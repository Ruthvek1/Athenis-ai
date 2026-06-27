import asyncio
import aiohttp
import time
import numpy as np
import json
import argparse

API_BASE_URL = "http://localhost:8000"

async def measure_request(session, url, method="GET", json_data=None):
    start = time.perf_counter()
    status = 0
    try:
        if method == "GET":
            async with session.get(url) as response:
                status = response.status
                await response.read()
        elif method == "POST":
            async with session.post(url, json=json_data) as response:
                status = response.status
                await response.read()
    except Exception as e:
        status = 0
    end = time.perf_counter()
    return end - start, status

async def benchmark_endpoint(name, url, method="GET", requests=100, concurrency=10):
    print(f"\n--- Benchmarking {name} ({method} {url}) ---")
    print(f"Requests: {requests}, Concurrency: {concurrency}")
    
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(requests):
            json_data = {"email": f"test_bench_{i}@example.com", "password": "password123"} if method == "POST" else None
            tasks.append(measure_request(session, url, method, json_data))
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
    latencies = [res[0] * 1000 for res in results] # in ms
    statuses = [res[1] for res in results]
    
    successes = statuses.count(200) + statuses.count(201)
    rate_limited = statuses.count(429)
    errors = len(statuses) - successes - rate_limited
    
    print(f"Total time: {total_time:.4f}s")
    print(f"Throughput: {requests / total_time:.2f} req/s")
    print(f"Successes: {successes} | Rate Limited (429): {rate_limited} | Errors: {errors}")
    
    if len(latencies) > 0:
        print(f"Min Latency: {np.min(latencies):.2f} ms")
        print(f"Max Latency: {np.max(latencies):.2f} ms")
        print(f"Mean Latency: {np.mean(latencies):.2f} ms")
        print(f"p50 Latency: {np.percentile(latencies, 50):.2f} ms")
        print(f"p90 Latency: {np.percentile(latencies, 90):.2f} ms")
        print(f"p99 Latency: {np.percentile(latencies, 99):.2f} ms")

async def main():
    parser = argparse.ArgumentParser(description="Athenis Phase 6 Benchmarks")
    parser.parse_args()
    
    print("Starting Phase 6 Benchmarks...")
    
    # 1. Baseline Health Check Throughput
    await benchmark_endpoint("Health Check", f"{API_BASE_URL}/health", requests=500, concurrency=50)
    
    # 2. Rate Limiter Test (Should hit 429s since limit is 10/min)
    await benchmark_endpoint("Rate Limited Auth", f"{API_BASE_URL}/api/v1/auth/register", method="POST", requests=20, concurrency=5)

if __name__ == "__main__":
    asyncio.run(main())
