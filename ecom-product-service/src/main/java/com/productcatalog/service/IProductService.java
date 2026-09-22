package com.productcatalog.service;

import java.util.List;

import com.productcatalog.model.Product;

public interface IProductService {
	
	List<Product> getAll();
	Product getById(int productId);
	List<Product> getByCategory(String category);
	

}
