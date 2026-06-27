import time
import argparse
from backend.services.ai_service import AIService

def benchmark_llm():
    print("\n--- Benchmarking LLM Generation (Phase 8) ---")
    query = "Explain the architecture of a production-grade RAG system in 3 paragraphs."
    
    # Mock context chunks
    context_chunks = [
        {
            "filename": "rag_architecture.md",
            "chunk_index": 0,
            "content": "A standard RAG system consists of a document ingestion pipeline, an embedding model, a vector database, and an LLM for generation."
        }
    ]
    
    start_time = time.perf_counter()
    answer, citations, metrics = AIService.generate_response(query, context_chunks)
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    
    print(f"Model Used: {metrics['model']}")
    print(f"Provider: {metrics['provider']}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Prompt Tokens: {metrics['prompt_tokens']}")
    print(f"Completion Tokens: {metrics['completion_tokens']}")
    print(f"Total Tokens: {metrics['total_tokens']}")
    
    if total_time > 0:
        throughput = metrics['completion_tokens'] / total_time
        print(f"Throughput: {throughput:.2f} completion tokens/sec")
    
    print("\nAnswer preview:")
    print(answer[:200] + "...")

def main():
    parser = argparse.ArgumentParser(description="Athenis Phase 8 LLM Benchmarks")
    parser.parse_args()
    
    print("Starting Phase 8 LLM Benchmarks...")
    benchmark_llm()

if __name__ == "__main__":
    main()
