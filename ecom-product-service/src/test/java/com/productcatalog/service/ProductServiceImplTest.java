package com.productcatalog.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.productcatalog.model.Product;
import com.productcatalog.util.ProductRepo;

@ExtendWith(MockitoExtension.class)
class ProductServiceImplTest {

	@Mock
	private ProductRepo repo;

	private ProductServiceImpl productService;

	private List<Product> products;

	@BeforeEach
	void setUp() {
		productService = new ProductServiceImpl(repo);
		products = Arrays.asList(
				new Product("Mobile", 1, "Samsung", "Electronics"),
				new Product("Lapptop", 2, "Dell", "Electronics"),
				new Product("Football", 3, "Nike", "Sports"),
				new Product("Shoes", 4, "Nike", "Sports"),
				new Product("Pen", 5, "classmate", "Stationary"));
	}

	@Test
	void getAll_returnsAllProductsFromRepo() {
		when(repo.showProducts()).thenReturn(products);

		List<Product> result = productService.getAll();

		assertThat(result).isEqualTo(products);
	}

	@Test
	void getById_returnsMatchingProduct_whenProductExists() {
		when(repo.showProducts()).thenReturn(products);

		Product result = productService.getById(3);

		assertThat(result).isNotNull();
		assertThat(result.getProductName()).isEqualTo("Football");
		assertThat(result.getBrand()).isEqualTo("Nike");
	}

	@Test
	void getById_returnsNull_whenProductDoesNotExist() {
		when(repo.showProducts()).thenReturn(products);

		Product result = productService.getById(999);

		assertThat(result).isNull();
	}

	@Test
	void getById_returnsNull_whenRepoIsEmpty() {
		when(repo.showProducts()).thenReturn(Collections.emptyList());

		Product result = productService.getById(1);

		assertThat(result).isNull();
	}

	@Test
	void getByCategory_returnsMatchingProducts_caseInsensitive() {
		when(repo.showProducts()).thenReturn(products);

		List<Product> result = productService.getByCategory("electronics");

		assertThat(result).hasSize(2)
				.extracting(Product::getProductName)
				.containsExactlyInAnyOrder("Mobile", "Lapptop");
	}

	@Test
	void getByCategory_returnsMatchingProducts_exactCase() {
		when(repo.showProducts()).thenReturn(products);

		List<Product> result = productService.getByCategory("Sports");

		assertThat(result).hasSize(2)
				.extracting(Product::getProductName)
				.containsExactlyInAnyOrder("Football", "Shoes");
	}

	@Test
	void getByCategory_returnsEmptyList_whenNoCategoryMatches() {
		when(repo.showProducts()).thenReturn(products);

		List<Product> result = productService.getByCategory("Toys");

		assertThat(result).isEmpty();
	}
}
