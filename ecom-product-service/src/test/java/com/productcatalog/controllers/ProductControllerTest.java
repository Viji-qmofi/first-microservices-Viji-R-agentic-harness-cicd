package com.productcatalog.controllers;

import static org.hamcrest.Matchers.hasSize;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.productcatalog.model.Product;
import com.productcatalog.service.IProductService;

@WebMvcTest(ProductController.class)
class ProductControllerTest {

	@Autowired
	private MockMvc mockMvc;

	@MockitoBean
	private IProductService productService;

	@Test
	void viewProducts_returnsAllProductsAsJson() throws Exception {
		List<Product> products = Arrays.asList(
				new Product("Mobile", 1, "Samsung", "Electronics"),
				new Product("Football", 3, "Nike", "Sports"));
		when(productService.getAll()).thenReturn(products);

		mockMvc.perform(get("/catalog-service/v1/products"))
				.andExpect(status().isOk())
				.andExpect(content().contentType(MediaType.APPLICATION_JSON))
				.andExpect(jsonPath("$", hasSize(2)))
				.andExpect(jsonPath("$[0].productId").value(1))
				.andExpect(jsonPath("$[0].productName").value("Mobile"))
				.andExpect(jsonPath("$[1].productId").value(3));
	}

	@Test
	void viewProducts_returnsEmptyList_whenNoProductsExist() throws Exception {
		when(productService.getAll()).thenReturn(Collections.emptyList());

		mockMvc.perform(get("/catalog-service/v1/products"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$", hasSize(0)));
	}

	@Test
	void getProductById_returnsProduct_whenFound() throws Exception {
		Product product = new Product("Mobile", 1, "Samsung", "Electronics");
		when(productService.getById(1)).thenReturn(product);

		mockMvc.perform(get("/catalog-service/v1/products/productId/1"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.productId").value(1))
				.andExpect(jsonPath("$.productName").value("Mobile"))
				.andExpect(jsonPath("$.brand").value("Samsung"))
				.andExpect(jsonPath("$.category").value("Electronics"));
	}

	@Test
	void getProductById_returnsEmptyBody_whenProductNotFound() throws Exception {
		when(productService.getById(anyInt())).thenReturn(null);

		mockMvc.perform(get("/catalog-service/v1/products/productId/999"))
				.andExpect(status().isOk())
				.andExpect(content().string(""));
	}

	@Test
	void getProductByCategory_returnsMatchingProducts() throws Exception {
		List<Product> sportsProducts = Arrays.asList(
				new Product("Football", 3, "Nike", "Sports"),
				new Product("Shoes", 4, "Nike", "Sports"));
		when(productService.getByCategory("Sports")).thenReturn(sportsProducts);

		mockMvc.perform(get("/catalog-service/v1/products/category/Sports"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$", hasSize(2)))
				.andExpect(jsonPath("$[0].productName").value("Football"))
				.andExpect(jsonPath("$[1].productName").value("Shoes"));
	}

	@Test
	void getProductByCategory_returnsEmptyList_whenNoMatch() throws Exception {
		when(productService.getByCategory(anyString())).thenReturn(Collections.emptyList());

		mockMvc.perform(get("/catalog-service/v1/products/category/Toys"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$", hasSize(0)));
	}
}
