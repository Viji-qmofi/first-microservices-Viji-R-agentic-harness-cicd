package com.productcatalog.util;

import java.util.Arrays;
import java.util.List;

import org.springframework.stereotype.Component;

import com.productcatalog.model.Product;

// fake DB
@Component
public class ProductRepo {
	
	public List<Product> showProducts(){
		return Arrays.asList(
				 new Product("Mobile", 1, "Samsung", "Electronics"),
				  new Product("Lapptop", 2, "Dell", "Electronics"),
				  new Product("Football", 3, "Nike", "Sports"),
				  new Product("Shoes", 4, "Nike", "Sports"),
				  new Product("Pen", 5, "classmate", "Stationary"));
				
	}

}
