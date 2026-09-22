package com.productorder.service;

import java.util.List;

import org.springframework.http.ResponseEntity;

import com.productorder.model.Product;
import com.productorder.model.RetryConfig;

public interface IOrderService {

	ResponseEntity<String> placeOrder(int productId);
	List<Product> viewAllProducts();
	RetryConfig getRetryConfig();

}
