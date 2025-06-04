"""
Query module for the LLM service.

This module provides functions for processing queries using the LLM manager.
"""

from typing import Tuple, Dict
from rag.llm_manager import llm_manager
from rag.config import MODEL_CONFIG, validate_parameters
from rag.prompt_manager import prompt_manager
import logging

logger = logging.getLogger(__name__)

def process_query(
    user_query: str,
    model_name: str = None,
    temperature: float = MODEL_CONFIG["default_temperature"],
    max_tokens: int = MODEL_CONFIG["default_max_tokens"],
    top_k: int = MODEL_CONFIG["default_top_k"]
) -> Tuple[str, Dict]:
    """
    Process a query using the LLM manager.

    Args:
        user_query: The user's question
        model_name: Optional model name to use
        temperature: LLM temperature (0.0 to 1.0)
        max_tokens: Maximum tokens for response
        top_k: Number of top tokens to consider

    Returns:
        Tuple containing:
        - response_text: str
        - metrics: Dict with performance metrics
    """
    try:
        # Ensure model_name is set
        model_name = model_name or MODEL_CONFIG["default_model"]
        logger.info(f"Processing query with model: {model_name}")

        # Validate parameters
        validate_parameters(temperature, max_tokens, top_k)

        # Validate query using prompt manager
        prompt_manager.validate_query(user_query)

        # Get model requirements for metrics
        model_reqs = prompt_manager.get_model_requirements(model_name)

        # Generate response using LLM manager
        response_text, llm_latency, tokens_used = llm_manager.generate_response(
            prompt=user_query,
            model_name=model_name,  # Now we know this is always set
            temperature=temperature,
            max_tokens=max_tokens,
            top_k=top_k
        )

        # Build metrics
        metrics = {
            "vector_latency": 0.0,  # No vector search yet
            "llm_latency": llm_latency,
            "total_time": llm_latency,  # Total time is same as LLM latency for now
            "tokens_used": tokens_used,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_k": top_k,
            "model_requirements": model_reqs
        }

        return response_text, metrics

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        metrics = {
            "vector_latency": 0.0,
            "llm_latency": 0.0,
            "total_time": 0.0,
            "tokens_used": 0,
            "model_name": model_name or MODEL_CONFIG["default_model"],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_k": top_k,
            "error": str(e)
        }
        return f"Error: {str(e)}", metrics
