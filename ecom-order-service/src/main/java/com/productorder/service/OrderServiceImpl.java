package com.productorder.service;

import java.util.List;
import java.util.function.LongConsumer;
import java.util.function.Supplier;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import com.productorder.feign.IProductServiceFeignClient;
import com.productorder.model.Product;
import com.productorder.model.RetryConfig;

import feign.FeignException;
import feign.RetryableException;

@Service
public class OrderServiceImpl implements IOrderService{

	private static final Logger logger = LoggerFactory.getLogger(OrderServiceImpl.class);

	// 1 initial call + 2 retries; human-approved exact value, not to be changed.
	private static final int MAX_ATTEMPTS = 3;
	// Fixed delay between attempts, no exponential growth or jitter; human-approved exact value.
	private static final long RETRY_BACKOFF_MS = 200;

	private final IProductServiceFeignClient feignClient;
	// Backoff seam: production uses a real Thread.sleep; tests inject a recording no-op so retry tests
	// do not pay the real delay.
	private final LongConsumer sleeper;

	@Autowired
	public OrderServiceImpl(IProductServiceFeignClient feignClient) {
		this(feignClient, OrderServiceImpl::sleepMillis);
	}

	// Package-private: only for tests in the same package.
	OrderServiceImpl(IProductServiceFeignClient feignClient, LongConsumer sleeper) {
		this.feignClient = feignClient;
		this.sleeper = sleeper;
	}

	// A LongConsumer cannot throw the checked InterruptedException, so restore the interrupt flag here;
	// callWithRetry checks the flag after each sleep and stops retrying if it is set.
	private static void sleepMillis(long millis) {
		try {
			Thread.sleep(millis);
		} catch (InterruptedException interruptedEx) {
			Thread.currentThread().interrupt();
		}
	}

	// Manual bounded retry loop for feign.RetryableException (true "service unreachable" case: no HTTP
	// response received at all). Implemented here rather than via a Feign Retryer bean/config because the
	// test suite mocks IProductServiceFeignClient directly with Mockito, which bypasses Feign's own
	// SynchronousMethodHandler/Retryer machinery entirely -- a Retryer-SPI-based fix would never be
	// exercised by those tests. No logging occurs inside this loop: the single WARN log for an exhausted
	// retry sequence must continue to fire exactly once, from the caller's existing
	// catch (RetryableException ex) block, only after retries are exhausted. FeignException.NotFound and
	// general FeignException are not RetryableException subtypes, so they propagate out on the very first
	// attempt, unretried.
	private <T> T callWithRetry(Supplier<T> feignCall) {
		RetryableException lastException = null;
		for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
			try {
				return feignCall.get();
			} catch (RetryableException ex) {
				lastException = ex;
				if (attempt < MAX_ATTEMPTS) {
					sleeper.accept(RETRY_BACKOFF_MS);
					if (Thread.currentThread().isInterrupted()) {
						break;
					}
				}
			}
		}
		throw lastException;
	}

	@Override
	public ResponseEntity<String> placeOrder(int productId) {
		// Client error raised before any downstream call: an invalid productId never reaches
		// product-service, so no Feign call and no retry backoff occur. Fixed generic reason, not logged.
		if (productId <= 0) {
			throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
					"productId must be a positive integer");
		}
		// check if the product by id is available if yes place order
		//	else cancel the order
		Product product;
		try {
			product = callWithRetry(() -> feignClient.getById(productId));
		} catch (FeignException.NotFound ex) {
			throw new ResponseStatusException(HttpStatus.NOT_FOUND,
					"Product with id "+productId+" not found");
		// RetryableException is a subtype of FeignException thrown only when no HTTP response was received
		// at all (connection refused, timeout, DNS failure) -- the true "service unreachable" case. It is
		// caught before the broader FeignException below because it is a more specific subtype (general/broad
		// catches must come last in Java). Logged at WARN, not ERROR, since this is treated as an expected,
		// self-resolving operational condition rather than a bug, and maps to 503 (Product service is
		// currently unreachable).
		} catch (RetryableException ex) {
			logger.warn("IProductServiceFeignClient#getById unreachable for productId {}: {}",
					productId, ex.getMessage());
			throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
					"Product service is currently unreachable, please try again later");
		// This branch only fires when a real HTTP response was received from the downstream service (not the
		// unreachable case above, and not the 404 NotFound case handled earlier) -- e.g. a genuine 4xx
		// (400/401) or 5xx from product-service. Logged at ERROR with the actual status code, since this may
		// indicate a real bug or contract violation, not a transient outage. Status is mapped by range:
		// 5xx -> 502 (Bad Gateway), other non-404 4xx -> 500, and the downstream response body/detail is
		// deliberately not echoed to the caller.
		} catch (FeignException ex) {
			logger.error("IProductServiceFeignClient#getById failed for productId {}, status {}: {}",
					productId, ex.status(), ex.getMessage());
			if (ex.status() >= 500 && ex.status() < 600) {
				throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
						"Product service returned an error, please try again later");
			}
			throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR,
					"Unable to process request due to an internal error");
		}

		return ResponseEntity.ok("Order placed successfully for "+product.getProductName());
	}

	@Override
	public List<Product> viewAllProducts() {
		try {
			return callWithRetry(() -> feignClient.getAllProducts());
		// Same RetryableException-before-FeignException distinction as placeOrder() above; see the comments
		// there for the full explanation (no NotFound case here since this call returns a list, not a single
		// resource).
		} catch (RetryableException ex) {
			logger.warn("IProductServiceFeignClient#getAllProducts unreachable: {}", ex.getMessage());
			throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
					"Product service is currently unreachable, please try again later");
		} catch (FeignException ex) {
			logger.error("IProductServiceFeignClient#getAllProducts failed, status {}: {}",
					ex.status(), ex.getMessage());
			if (ex.status() >= 500 && ex.status() < 600) {
				throw new ResponseStatusException(HttpStatus.BAD_GATEWAY,
						"Product service returned an error, please try again later");
			}
			throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR,
					"Unable to process request due to an internal error");
		}
	}

	// Read-only view of the retry constants above; no Feign call and no logging.
	@Override
	public RetryConfig getRetryConfig() {
		return new RetryConfig(MAX_ATTEMPTS, RETRY_BACKOFF_MS);
	}

}
