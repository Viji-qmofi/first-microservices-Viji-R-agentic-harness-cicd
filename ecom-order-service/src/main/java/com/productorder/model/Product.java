package com.productorder.model;


public class Product {

	private String productName;
	private Integer productId;
	private String brand;
	private String category;
	public Product() {
		super();
		// TODO Auto-generated constructor stub
	}
	
	public Product(String productName, Integer productId, String brand, String category) {
		super();
		this.productName = productName;
		this.productId = productId;
		this.brand = brand;
		this.category = category;
	}

	public String getProductName() {
		return productName;
	}

	public void setProductName(String productName) {
		this.productName = productName;
	}

	public Integer getProductId() {
		return productId;
	}

	public void setProductId(Integer productId) {
		this.productId = productId;
	}

	public String getBrand() {
		return brand;
	}

	public void setBrand(String brand) {
		this.brand = brand;
	}

	public String getCategory() {
		return category;
	}

	public void setCategory(String category) {
		this.category = category;
	}

	@Override
	public String toString() {
		return "Product [productName=" + productName + ", productId=" + productId + ", brand=" + brand + ", category="
				+ category + ", getProductName()=" + getProductName() + ", getProductId()=" + getProductId()
				+ ", getBrand()=" + getBrand() + ", getCategory()=" + getCategory() + ", getClass()=" + getClass()
				+ ", hashCode()=" + hashCode() + ", toString()=" + super.toString() + "]";
	}
	
	
//	
	
}