import asyncio
import time
import argparse
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.services.retrieval_service import RetrievalService
from backend.services.embedding_service import EmbeddingService
import numpy as np

def benchmark_search(db: Session, query: str, top_k: int, search_type: str, iterations: int = 100):
    print(f"\n--- Benchmarking {search_type} Search ---")
    latencies = []
    
    # Warmup
    if search_type == "Vector":
        RetrievalService.search_vector(db, query, top_k)
    elif search_type == "Keyword":
        RetrievalService.search_keyword(db, query, top_k)
    elif search_type == "Hybrid":
        RetrievalService.search_similar_chunks(db, query, top_k)
        
    for _ in range(iterations):
        start = time.perf_counter()
        if search_type == "Vector":
            RetrievalService.search_vector(db, query, top_k)
        elif search_type == "Keyword":
            RetrievalService.search_keyword(db, query, top_k)
        elif search_type == "Hybrid":
            RetrievalService.search_similar_chunks(db, query, top_k)
        end = time.perf_counter()
        latencies.append((end - start) * 1000) # ms
        
    print(f"Iterations: {iterations}")
    print(f"Min Latency: {np.min(latencies):.2f} ms")
    print(f"Max Latency: {np.max(latencies):.2f} ms")
    print(f"Mean Latency: {np.mean(latencies):.2f} ms")
    print(f"p50 Latency: {np.percentile(latencies, 50):.2f} ms")
    print(f"p90 Latency: {np.percentile(latencies, 90):.2f} ms")
    print(f"p99 Latency: {np.percentile(latencies, 99):.2f} ms")

def main():
    parser = argparse.ArgumentParser(description="Athenis Phase 7 Retrieval Benchmarks")
    parser.parse_args()
    
    print("Starting Phase 7 Retrieval Benchmarks...")
    db = SessionLocal()
    
    test_query = "What is the architecture of Athenis?"
    top_k = 5
    iterations = 5
    
    try:
        benchmark_search(db, test_query, top_k, "Vector", iterations)
        benchmark_search(db, test_query, top_k, "Keyword", iterations)
        benchmark_search(db, test_query, top_k, "Hybrid", iterations)
    finally:
        db.close()

if __name__ == "__main__":
    main()
