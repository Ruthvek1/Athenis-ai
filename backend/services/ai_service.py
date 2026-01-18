from typing import List, Dict, Any, Generator, Optional
from backend.core.config import settings
import litellm
import json
import time
from backend.core.observability import LLM_GENERATION_LATENCY, LLM_TOKEN_USAGE

# Ensure API keys are available to litellm
import os
if settings.GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

class AIService:
    @staticmethod
    def _build_messages(query: str, context_chunks: List[Dict[str, Any]], chat_history: List[Dict[str, str]] = None, custom_system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        context_text = "\n\n".join([f"Source [{i+1}] ({chunk['filename']}):\n{chunk['content']}" for i, chunk in enumerate(context_chunks)])
        
        system_prompt = custom_system_prompt if custom_system_prompt else (
            "You are Athenis, an AI-powered RAG Knowledge Assistant. Use the provided context to answer the user's question. "
            "If the answer is not in the context, say you don't know based on the provided documents. Cite your sources clearly."
        )
        system_prompt += f"\n\nContext:\n{context_text}"
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            messages.extend(chat_history)
            
        messages.append({"role": "user", "content": query})
        return messages

    @staticmethod
    def generate_response(
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        chat_history: List[Dict[str, str]] = None,
        system_prompt: Optional[str] = None
    ) -> tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generates a non-streaming response using litellm with fallback routing.
        Returns generated text, citations, and metrics.
        """
        messages = AIService._build_messages(query, context_chunks, chat_history, custom_system_prompt=system_prompt)
        
        # Ensure litellm knows the provider
        primary_model = settings.LLM_MODEL
        if primary_model.startswith("gemini-"):
            primary_model = f"gemini/{primary_model}"
            
        # Models to attempt in order for automatic failover
        fallbacks = [primary_model, "gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro"]
        
        start_time = time.perf_counter()
        
        start_time_s = time.time()
        
        try:
            response = litellm.completion(
                model=fallbacks[0],
                messages=messages,
                fallbacks=fallbacks[1:] if len(fallbacks) > 1 else None
            )
            
            # Record Token Usage
            if hasattr(response, 'usage'):
                LLM_TOKEN_USAGE.labels(model=response.model, token_type="prompt").inc(response.usage.prompt_tokens)
                LLM_TOKEN_USAGE.labels(model=response.model, token_type="completion").inc(response.usage.completion_tokens)
                LLM_TOKEN_USAGE.labels(model=response.model, token_type="total").inc(response.usage.total_tokens)
                
            latency = (time.perf_counter() - start_time) * 1000
            
            metrics = {
                "model": response.model,
                "provider": response.model.split('/')[0] if '/' in response.model else "unknown",
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
                "latency_ms": latency
            }
            
            citations = [
                {
                    "id": i + 1,
                    "filename": chunk["filename"],
                    "chunk_index": chunk["chunk_index"],
                    "similarity_score": chunk.get("similarity_score")
                }
                for i, chunk in enumerate(context_chunks)
            ]
            
            return response.choices[0].message.content, citations, metrics
        finally:
            latency_s = time.time() - start_time_s
            # Note: response.model might not exist if exception thrown, so default to primary_model
            model_used = response.model if 'response' in locals() and hasattr(response, 'model') else primary_model
            LLM_GENERATION_LATENCY.labels(model=model_used).observe(latency_s)

    @staticmethod
    def generate_stream(
        query: str, 
        context_chunks: List[Dict[str, Any]], 
        chat_history: List[Dict[str, str]] = None,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generates a streaming response using litellm.
        """
        messages = AIService._build_messages(query, context_chunks, chat_history, custom_system_prompt=system_prompt)
        
        citations = [
            {
                "id": i + 1,
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
                "similarity_score": chunk.get("similarity_score")
            }
            for i, chunk in enumerate(context_chunks)
        ]
        
        # Prepend a special block for citations so the frontend can parse it
        yield json.dumps({"type": "citations", "data": citations}) + "\n\n"
        
        primary_model = settings.LLM_MODEL
        if primary_model.startswith("gemini-"):
            primary_model = f"gemini/{primary_model}"
            
        response = litellm.completion(
            model=primary_model,
            messages=messages,
            stream=True
        )
        
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield json.dumps({"type": "text", "data": content}) + "\n\n"
