package com.productorder.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.server.ResponseStatusException;

import com.productorder.feign.IProductServiceFeignClient;
import com.productorder.model.Product;
import com.productorder.model.RetryConfig;

import ch.qos.logback.classic.Level;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.read.ListAppender;

import feign.FeignException;
import feign.Request;
import feign.Response;
import feign.RetryableException;

@ExtendWith(MockitoExtension.class)
class OrderServiceImplTest {

	@Mock
	private IProductServiceFeignClient feignClient;

	private OrderServiceImpl orderService;

	private List<Long> recordedSleeps;

	private Logger orderServiceLogger;
	private ListAppender<ILoggingEvent> listAppender;

	@BeforeEach
	void setUpOrderService() {
		recordedSleeps = new ArrayList<>();
		orderService = new OrderServiceImpl(feignClient, recordedSleeps::add);
	}

	@BeforeEach
	void setUpLogAppender() {
		orderServiceLogger = (Logger) LoggerFactory.getLogger(OrderServiceImpl.class);
		listAppender = new ListAppender<>();
		listAppender.start();
		orderServiceLogger.addAppender(listAppender);
	}

	@AfterEach
	void tearDownLogAppender() {
		orderServiceLogger.detachAppender(listAppender);
	}

	@Test
	void placeOrder_returnsConfirmation_whenProductExists() {
		Product product = new Product("Mobile", 1, "Samsung", "Electronics");
		when(feignClient.getById(1)).thenReturn(product);

		ResponseEntity<String> result = orderService.placeOrder(1);

		assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
		assertThat(result.getBody()).isEqualTo("Order placed successfully for Mobile");
	}

	@Test
	void placeOrder_throwsBadRequest_whenProductIdIsZero() {
		assertThatThrownBy(() -> orderService.placeOrder(0))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
					assertThat(rse.getReason()).isEqualTo("productId must be a positive integer");
				});

		verifyNoInteractions(feignClient);
	}

	@Test
	void placeOrder_throwsBadRequest_whenProductIdIsNegative() {
		assertThatThrownBy(() -> orderService.placeOrder(-1))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
					assertThat(rse.getReason()).isEqualTo("productId must be a positive integer");
				});

		verifyNoInteractions(feignClient);
	}

	@Test
	void placeOrder_throwsBadRequest_whenProductIdIsIntegerMinValue() {
		assertThatThrownBy(() -> orderService.placeOrder(Integer.MIN_VALUE))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
					assertThat(rse.getReason()).isEqualTo("productId must be a positive integer");
				});

		verifyNoInteractions(feignClient);
	}

	@Test
	void placeOrder_logsNothing_whenProductIdIsInvalid() {
		assertThatThrownBy(() -> orderService.placeOrder(-1)).isInstanceOf(ResponseStatusException.class);

		assertThat(listAppender.list).isEmpty();
		verifyNoInteractions(feignClient);
	}

	@Test
	void placeOrder_succeedsAfterRetries_whenProductServiceUnreachableTwiceThenSucceeds() {
		Product product = new Product("Mobile", 1, "Samsung", "Electronics");
		when(feignClient.getById(1))
				.thenThrow(unreachableException("/catalog-service/v1/products/productId/1"))
				.thenThrow(unreachableException("/catalog-service/v1/products/productId/1"))
				.thenReturn(product);

		ResponseEntity<String> result = orderService.placeOrder(1);

		assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
		assertThat(result.getBody()).isEqualTo("Order placed successfully for Mobile");
		verify(feignClient, times(3)).getById(1);
		assertThat(recordedSleeps).isEqualTo(List.of(200L, 200L));
	}

	@Test
	void placeOrder_throwsNotFound_whenProductDoesNotExist() {
		when(feignClient.getById(999)).thenThrow(notFoundException(999));

		assertThatThrownBy(() -> orderService.placeOrder(999))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
					assertThat(rse.getReason()).isEqualTo("Product with id 999 not found");
				});

		verify(feignClient, times(1)).getById(999);
	}

	@Test
	void placeOrder_throwsBadGateway_whenProductServiceReturns500() {
		when(feignClient.getById(1)).thenThrow(generalFeignException());

		assertThatThrownBy(() -> orderService.placeOrder(1))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_GATEWAY);
					assertThat(rse.getReason()).isEqualTo("Product service returned an error, please try again later");
					assertThat(rse.getReason()).doesNotContain("/catalog-service/v1/products/productId/1");
				});

		verify(feignClient, times(1)).getById(1);
	}

	@Test
	void placeOrder_throwsServiceUnavailable_whenProductServiceUnreachable() {
		when(feignClient.getById(1))
				.thenThrow(unreachableException("/catalog-service/v1/products/productId/1"));

		assertThatThrownBy(() -> orderService.placeOrder(1))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
					assertThat(rse.getReason()).isEqualTo("Product service is currently unreachable, please try again later");
					assertThat(rse.getReason()).doesNotContain("connection timed out");
				});

		verify(feignClient, times(3)).getById(1);
		assertThat(recordedSleeps).isEqualTo(List.of(200L, 200L));
	}

	@Test
	void placeOrder_throwsInternalServerError_whenProductServiceReturnsOther4xx() {
		when(feignClient.getById(1)).thenThrow(badRequestException());

		assertThatThrownBy(() -> orderService.placeOrder(1))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
					assertThat(rse.getReason()).isEqualTo("Unable to process request due to an internal error");
					assertThat(rse.getReason()).doesNotContain("/catalog-service/v1/products/productId/1");
				});

		verify(feignClient, times(1)).getById(1);
	}

	@Test
	void placeOrder_throwsBadGateway_whenProductServiceReturnsGenuine503_notMistakenForUnreachable() {
		// A real downstream response with status 503 (feign.FeignException.ServiceUnavailable)
		// must NOT be treated the same as a RetryableException (truly unreachable). It should
		// fall through the generic FeignException 5xx branch -> 502, not the 503 unreachable branch.
		when(feignClient.getById(1)).thenThrow(errorStatus(503, "/catalog-service/v1/products/productId/1"));

		assertThatThrownBy(() -> orderService.placeOrder(1))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_GATEWAY);
					assertThat(rse.getReason()).isEqualTo("Product service returned an error, please try again later");
				});

		verify(feignClient, times(1)).getById(1);
	}

	@Test
	void placeOrder_throwsInternalServerError_atStatus499LowerBoundary() {
		when(feignClient.getById(1)).thenThrow(errorStatus(499, "/catalog-service/v1/products/productId/1"));

		assertThatThrownBy(() -> orderService.placeOrder(1))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
					assertThat(rse.getReason()).isEqualTo("Unable to process request due to an internal error");
				});

		verify(feignClient, times(1)).getById(1);
	}

	@Test
	void placeOrder_throwsBadGateway_atStatus599UpperBoundary() {
		when(feignClient.getById(1)).thenThrow(errorStatus(599, "/catalog-service/v1/products/productId/1"));

		assertThatThrownBy(() -> orderService.placeOrder(1))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_GATEWAY);
					assertThat(rse.getReason()).isEqualTo("Product service returned an error, please try again later");
				});

		verify(feignClient, times(1)).getById(1);
	}

	@Test
	void placeOrder_throwsInternalServerError_whenStatusUndetermined() {
		// Feign can surface status -1 when it cannot determine a real HTTP status. This falls
		// through the ">=500 && <600" check to the generic "other 4xx" branch by default.
		when(feignClient.getById(1)).thenThrow(errorStatus(-1, "/catalog-service/v1/products/productId/1"));

		assertThatThrownBy(() -> orderService.placeOrder(1))
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
					assertThat(rse.getReason()).isEqualTo("Unable to process request due to an internal error");
				});

		verify(feignClient, times(1)).getById(1);
	}

	@Test
	void placeOrder_logsWarn_whenProductServiceUnreachable() {
		when(feignClient.getById(42))
				.thenThrow(unreachableException("/catalog-service/v1/products/productId/42"));

		assertThatThrownBy(() -> orderService.placeOrder(42)).isInstanceOf(ResponseStatusException.class);

		assertThat(listAppender.list).hasSize(1);
		ILoggingEvent event = listAppender.list.get(0);
		assertThat(event.getLevel()).isEqualTo(Level.WARN);
		assertThat(event.getFormattedMessage()).contains("getById").contains("42").contains("unreachable");
		assertThat(recordedSleeps).isEqualTo(List.of(200L, 200L));
	}

	@Test
	void placeOrder_logsError_whenProductServiceReturnsServerError() {
		when(feignClient.getById(42)).thenThrow(errorStatus(500, "/catalog-service/v1/products/productId/42"));

		assertThatThrownBy(() -> orderService.placeOrder(42)).isInstanceOf(ResponseStatusException.class);

		assertThat(listAppender.list).hasSize(1);
		ILoggingEvent event = listAppender.list.get(0);
		assertThat(event.getLevel()).isEqualTo(Level.ERROR);
		assertThat(event.getFormattedMessage()).contains("getById").contains("42").contains("500");

		verify(feignClient, times(1)).getById(42);
	}

	@Test
	void placeOrder_logsError_whenProductServiceReturnsOther4xx() {
		when(feignClient.getById(42)).thenThrow(errorStatus(400, "/catalog-service/v1/products/productId/42"));

		assertThatThrownBy(() -> orderService.placeOrder(42)).isInstanceOf(ResponseStatusException.class);

		assertThat(listAppender.list).hasSize(1);
		ILoggingEvent event = listAppender.list.get(0);
		assertThat(event.getLevel()).isEqualTo(Level.ERROR);
		assertThat(event.getFormattedMessage()).contains("getById").contains("42").contains("400");

		verify(feignClient, times(1)).getById(42);
	}

	@Test
	void viewAllProducts_returnsList_whenProductServiceSucceeds() {
		List<Product> products = List.of(new Product("Mobile", 1, "Samsung", "Electronics"));
		when(feignClient.getAllProducts()).thenReturn(products);

		List<Product> result = orderService.viewAllProducts();

		assertThat(result).isEqualTo(products);
	}

	@Test
	void viewAllProducts_succeedsAfterRetries_whenProductServiceUnreachableTwiceThenSucceeds() {
		List<Product> products = List.of(new Product("Mobile", 1, "Samsung", "Electronics"));
		when(feignClient.getAllProducts())
				.thenThrow(unreachableException("/catalog-service/v1/products"))
				.thenThrow(unreachableException("/catalog-service/v1/products"))
				.thenReturn(products);

		List<Product> result = orderService.viewAllProducts();

		assertThat(result).isEqualTo(products);
		verify(feignClient, times(3)).getAllProducts();
		assertThat(recordedSleeps).isEqualTo(List.of(200L, 200L));
	}

	@Test
	void viewAllProducts_throwsServiceUnavailable_whenProductServiceUnreachable() {
		when(feignClient.getAllProducts())
				.thenThrow(unreachableException("/catalog-service/v1/products"));

		assertThatThrownBy(() -> orderService.viewAllProducts())
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
					assertThat(rse.getReason()).isEqualTo("Product service is currently unreachable, please try again later");
					assertThat(rse.getReason()).doesNotContain("connection timed out");
				});

		verify(feignClient, times(3)).getAllProducts();
		assertThat(recordedSleeps).isEqualTo(List.of(200L, 200L));
	}

	@Test
	void viewAllProducts_throwsBadGateway_whenProductServiceReturns500() {
		when(feignClient.getAllProducts()).thenThrow(errorStatusForGetAllProducts(500));

		assertThatThrownBy(() -> orderService.viewAllProducts())
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_GATEWAY);
					assertThat(rse.getReason()).isEqualTo("Product service returned an error, please try again later");
					assertThat(rse.getReason()).doesNotContain("/catalog-service/v1/products");
				});

		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void viewAllProducts_throwsInternalServerError_whenProductServiceReturnsOther4xx() {
		when(feignClient.getAllProducts()).thenThrow(errorStatusForGetAllProducts(400));

		assertThatThrownBy(() -> orderService.viewAllProducts())
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
					assertThat(rse.getReason()).isEqualTo("Unable to process request due to an internal error");
					assertThat(rse.getReason()).doesNotContain("/catalog-service/v1/products");
				});

		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void viewAllProducts_throwsInternalServerError_whenProductServiceReturns404() {
		// Unlike placeOrder(), viewAllProducts() has no FeignException.NotFound-specific catch,
		// so a 404 here must fall through the generic FeignException branch and map to 500 --
		// NOT 404. This documents that asymmetry between the two methods' catch structures.
		when(feignClient.getAllProducts()).thenThrow(errorStatusForGetAllProducts(404));

		assertThatThrownBy(() -> orderService.viewAllProducts())
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
					assertThat(rse.getStatusCode()).isNotEqualTo(HttpStatus.NOT_FOUND);
					assertThat(rse.getReason()).isEqualTo("Unable to process request due to an internal error");
				});

		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void viewAllProducts_throwsBadGateway_whenProductServiceReturnsGenuine503_notMistakenForUnreachable() {
		// A real downstream response with status 503 must NOT be treated the same as a
		// RetryableException (truly unreachable). It should fall through the generic
		// FeignException 5xx branch -> 502, not the 503 unreachable branch.
		when(feignClient.getAllProducts()).thenThrow(errorStatusForGetAllProducts(503));

		assertThatThrownBy(() -> orderService.viewAllProducts())
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_GATEWAY);
					assertThat(rse.getReason()).isEqualTo("Product service returned an error, please try again later");
				});

		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void viewAllProducts_throwsInternalServerError_atStatus499LowerBoundary() {
		when(feignClient.getAllProducts()).thenThrow(errorStatusForGetAllProducts(499));

		assertThatThrownBy(() -> orderService.viewAllProducts())
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
					assertThat(rse.getReason()).isEqualTo("Unable to process request due to an internal error");
				});

		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void viewAllProducts_throwsBadGateway_atStatus599UpperBoundary() {
		when(feignClient.getAllProducts()).thenThrow(errorStatusForGetAllProducts(599));

		assertThatThrownBy(() -> orderService.viewAllProducts())
				.isInstanceOf(ResponseStatusException.class)
				.satisfies(ex -> {
					ResponseStatusException rse = (ResponseStatusException) ex;
					assertThat(rse.getStatusCode()).isEqualTo(HttpStatus.BAD_GATEWAY);
					assertThat(rse.getReason()).isEqualTo("Product service returned an error, please try again later");
				});

		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void viewAllProducts_logsWarn_whenProductServiceUnreachable() {
		when(feignClient.getAllProducts())
				.thenThrow(unreachableException("/catalog-service/v1/products"));

		assertThatThrownBy(() -> orderService.viewAllProducts()).isInstanceOf(ResponseStatusException.class);

		assertThat(listAppender.list).hasSize(1);
		ILoggingEvent event = listAppender.list.get(0);
		assertThat(event.getLevel()).isEqualTo(Level.WARN);
		assertThat(event.getFormattedMessage()).contains("getAllProducts").contains("unreachable");
		assertThat(recordedSleeps).isEqualTo(List.of(200L, 200L));
	}

	@Test
	void viewAllProducts_logsError_whenProductServiceReturnsServerError() {
		when(feignClient.getAllProducts()).thenThrow(errorStatusForGetAllProducts(500));

		assertThatThrownBy(() -> orderService.viewAllProducts()).isInstanceOf(ResponseStatusException.class);

		assertThat(listAppender.list).hasSize(1);
		ILoggingEvent event = listAppender.list.get(0);
		assertThat(event.getLevel()).isEqualTo(Level.ERROR);
		assertThat(event.getFormattedMessage()).contains("getAllProducts").contains("500");

		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void viewAllProducts_logsError_whenProductServiceReturnsOther4xx() {
		when(feignClient.getAllProducts()).thenThrow(errorStatusForGetAllProducts(400));

		assertThatThrownBy(() -> orderService.viewAllProducts()).isInstanceOf(ResponseStatusException.class);

		assertThat(listAppender.list).hasSize(1);
		ILoggingEvent event = listAppender.list.get(0);
		assertThat(event.getLevel()).isEqualTo(Level.ERROR);
		assertThat(event.getFormattedMessage()).contains("getAllProducts").contains("400");

		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void placeOrder_usesConstructorSuppliedClient_whenBuiltExplicitly() {
		OrderServiceImpl service = new OrderServiceImpl(feignClient);
		Product product = new Product("Mobile", 1, "Samsung", "Electronics");
		when(feignClient.getById(1)).thenReturn(product);

		ResponseEntity<String> result = service.placeOrder(1);

		assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
		assertThat(result.getBody()).isEqualTo("Order placed successfully for Mobile");
		verify(feignClient, times(1)).getById(1);
	}

	@Test
	void viewAllProducts_usesConstructorSuppliedClient_whenBuiltExplicitly() {
		OrderServiceImpl service = new OrderServiceImpl(feignClient);
		List<Product> products = List.of(new Product("Mobile", 1, "Samsung", "Electronics"));
		when(feignClient.getAllProducts()).thenReturn(products);

		List<Product> result = service.viewAllProducts();

		assertThat(result).isEqualTo(products);
		verify(feignClient, times(1)).getAllProducts();
	}

	@Test
	void placeOrder_reachesOnlyOwnClient_whenTwoInstancesBuiltWithDistinctClients() {
		IProductServiceFeignClient clientA = mock(IProductServiceFeignClient.class);
		IProductServiceFeignClient clientB = mock(IProductServiceFeignClient.class);
		OrderServiceImpl serviceA = new OrderServiceImpl(clientA);
		OrderServiceImpl serviceB = new OrderServiceImpl(clientB);
		when(clientA.getById(1)).thenReturn(new Product("Mobile", 1, "Samsung", "Electronics"));
		when(clientB.getById(2)).thenReturn(new Product("Laptop", 2, "Dell", "Electronics"));

		assertThat(serviceA.placeOrder(1).getBody()).isEqualTo("Order placed successfully for Mobile");
		verify(clientA, times(1)).getById(1);
		verifyNoInteractions(clientB);

		assertThat(serviceB.placeOrder(2).getBody()).isEqualTo("Order placed successfully for Laptop");
		verify(clientB, times(1)).getById(2);
		verify(clientA, times(1)).getById(1);
	}

	private FeignException notFoundException(int productId) {
		return errorStatus(404, "/catalog-service/v1/products/productId/" + productId);
	}

	private FeignException generalFeignException() {
		return errorStatus(500, "/catalog-service/v1/products/productId/1");
	}

	private FeignException badRequestException() {
		return errorStatus(400, "/catalog-service/v1/products/productId/1");
	}

	private FeignException errorStatus(int status, String url) {
		Request request = Request.create(Request.HttpMethod.GET, url,
				Collections.emptyMap(), null, StandardCharsets.UTF_8, null);
		Response response = Response.builder()
				.status(status)
				.reason("error")
				.request(request)
				.headers(Collections.emptyMap())
				.build();
		return FeignException.errorStatus("IProductServiceFeignClient#getById(int)", response);
	}

	private FeignException errorStatusForGetAllProducts(int status) {
		Request request = Request.create(Request.HttpMethod.GET, "/catalog-service/v1/products",
				Collections.emptyMap(), null, StandardCharsets.UTF_8, null);
		Response response = Response.builder()
				.status(status)
				.reason("error")
				.request(request)
				.headers(Collections.emptyMap())
				.build();
		return FeignException.errorStatus("IProductServiceFeignClient#getAllProducts()", response);
	}

	private RetryableException unreachableException(String url) {
		Request request = Request.create(Request.HttpMethod.GET, url,
				Collections.emptyMap(), null, StandardCharsets.UTF_8, null);
		return new RetryableException(-1, "connection timed out", Request.HttpMethod.GET, (Long) null, request);
	}

	@Test
	void getRetryConfig_returnsApprovedConstants_whenCalled() {
		RetryConfig config = orderService.getRetryConfig();

		assertThat(config.getMaxAttempts()).isEqualTo(3);
		assertThat(config.getBackoffMs()).isEqualTo(200L);
		verifyNoInteractions(feignClient);
	}

}
