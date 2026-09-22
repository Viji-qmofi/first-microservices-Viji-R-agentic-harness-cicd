package com.productorder.controllers;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoMoreInteractions;
import static org.mockito.Mockito.when;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.server.ResponseStatusException;

import com.productorder.model.Product;
import com.productorder.model.RetryConfig;
import com.productorder.service.IOrderService;

@ExtendWith(MockitoExtension.class)
class OrderControllerTest {

	@Mock
	private IOrderService mockService;

	@Test
	void placeOrder_delegatesToConstructorSuppliedService_whenCalled() {
		OrderController controller = new OrderController(mockService);
		ResponseEntity<String> expected = ResponseEntity.ok("Order placed successfully for Mobile");
		when(mockService.placeOrder(7)).thenReturn(expected);

		ResponseEntity<String> result = controller.placeOrder(7);

		assertThat(result).isSameAs(expected);
		assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
		assertThat(result.getBody()).isEqualTo("Order placed successfully for Mobile");
		verify(mockService, times(1)).placeOrder(7);
		verifyNoMoreInteractions(mockService);
	}

	@Test
	void viewProducts_delegatesToConstructorSuppliedService_whenCalled() {
		OrderController controller = new OrderController(mockService);
		List<Product> products = List.of(new Product("Mobile", 1, "Samsung", "Electronics"));
		when(mockService.viewAllProducts()).thenReturn(products);

		List<Product> result = controller.viewProducts();

		assertThat(result).isEqualTo(products);
		verify(mockService, times(1)).viewAllProducts();
		verifyNoMoreInteractions(mockService);
	}

	@Test
	void placeOrder_propagatesException_whenServiceThrows() {
		OrderController controller = new OrderController(mockService);
		ResponseStatusException thrown = new ResponseStatusException(HttpStatus.NOT_FOUND, "Product with id 404 not found");
		when(mockService.placeOrder(404)).thenThrow(thrown);

		assertThatThrownBy(() -> controller.placeOrder(404)).isSameAs(thrown);

		verify(mockService, times(1)).placeOrder(404);
	}

	@Test
	void getRetryConfig_delegatesToConstructorSuppliedService_whenCalled() {
		OrderController controller = new OrderController(mockService);
		RetryConfig expected = new RetryConfig(3, 200);
		when(mockService.getRetryConfig()).thenReturn(expected);

		RetryConfig result = controller.getRetryConfig();

		assertThat(result).isSameAs(expected);
		verify(mockService, times(1)).getRetryConfig();
		verifyNoMoreInteractions(mockService);
	}

}
