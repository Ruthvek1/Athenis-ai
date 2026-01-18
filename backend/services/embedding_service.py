from typing import List
from backend.core.config import settings
import litellm
import time
from backend.core.observability import LLM_GENERATION_LATENCY, LLM_TOKEN_USAGE

# Ensure API keys are available to litellm
import os
if settings.GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

class EmbeddingService:
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        text = text.replace("\n", " ")
        model = settings.EMBEDDING_MODEL
        if model.startswith("gemini-"):
            model = f"gemini/{model}"
            
        start_time = time.time()
        try:
            response = litellm.embedding(
                model=model,
                input=[text]
            )
            
            # Record Token Usage
            if hasattr(response, 'usage'):
                LLM_TOKEN_USAGE.labels(model=model, token_type="total").inc(response.usage.total_tokens)
                
            return response.data[0]["embedding"]
        finally:
            latency = time.time() - start_time
            LLM_GENERATION_LATENCY.labels(model=model).observe(latency)
        
    @staticmethod
    def get_embeddings(texts: List[str]) -> List[List[float]]:
        texts = [t.replace("\n", " ") for t in texts]
        
        model = settings.EMBEDDING_MODEL
        if model.startswith("gemini-"):
            model = f"gemini/{model}"
        
        start_time = time.time()
        try:
            # We need to chunk the input array for litellm depending on the provider limits,
            # but for simplicity in this MVP we assume the batch size is already handled.
            response = litellm.embedding(
                model=model,
                input=texts
            )
            
            # Record Token Usage
            if hasattr(response, 'usage'):
                LLM_TOKEN_USAGE.labels(model=model, token_type="total").inc(response.usage.total_tokens)
            
            # Return embeddings in the same order
            return [data["embedding"] for data in response.data]
        finally:
            latency = time.time() - start_time
            LLM_GENERATION_LATENCY.labels(model=model).observe(latency)
