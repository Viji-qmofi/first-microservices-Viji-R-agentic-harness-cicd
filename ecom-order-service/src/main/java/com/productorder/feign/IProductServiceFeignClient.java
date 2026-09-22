package com.productorder.feign;

import java.util.List;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import com.productorder.model.Product;

// this is a declarative client
// this is the client for produt-service
// the implemantation will be created during the runtime
//this converst all jave calls to rest api calls
// the returened result will be deserialized
@FeignClient(name="product-service")
public interface IProductServiceFeignClient {
	
//	pass the complete url
//	 http://product-service/catalog-service/v1/products
	@GetMapping("/catalog-service/v1/products")
	List<Product> getAllProducts();
	
//	 http://product-service/catalog-service/v1/products/productId/1
	@GetMapping("/catalog-service/v1/products/productId/{productId}")
	Product getById(@PathVariable int productId);
}
