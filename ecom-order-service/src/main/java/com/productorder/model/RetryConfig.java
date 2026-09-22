package com.productorder.model;

public class RetryConfig {

	private final int maxAttempts;
	private final long backoffMs;

	public RetryConfig(int maxAttempts, long backoffMs) {
		this.maxAttempts = maxAttempts;
		this.backoffMs = backoffMs;
	}

	public int getMaxAttempts() {
		return maxAttempts;
	}

	public long getBackoffMs() {
		return backoffMs;
	}

}
