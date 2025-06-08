"""
Configuration settings for the LLM service.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (two levels up from this file)
project_root = Path(__file__).parent.parent.parent.parent

# Load environment variables from project root
load_dotenv(project_root / ".env")

# Model Configuration
MODEL_CONFIG: Dict[str, Any] = {
    "default_model": os.getenv("DEFAULT_LLM_MODEL", "meta-llama/Llama-3.2-1B-Instruct"),
    "default_temperature": float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
    "default_max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "1000")),
    "default_top_k": int(os.getenv("DEFAULT_TOP_K", "5")),
    "supported_models": os.getenv("SUPPORTED_MODELS", "meta-llama/Llama-3.2-1B-Instruct,meta-llama/Llama-3.2-3B-Instruct").split(",")
}

# Parameter Validation
def validate_parameters(temperature: float, max_tokens: int, top_k: int) -> None:
    """Validate model parameters."""
    if not 0 <= temperature <= 1:
        raise ValueError("Temperature must be between 0 and 1")
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if top_k <= 0:
        raise ValueError("top_k must be positive")

# System prompts for Llama models
SYSTEM_PROMPTS = {
    "llama": "You are a helpful financial AI assistant that answers questions based only on the provided context. Analyze the context carefully and provide detailed, accurate responses. If the answer cannot be found in the context, say \"Not found in context.\"",
    "default": "You are a helpful financial AI assistant that answers questions based only on the provided context. Analyze the context carefully and provide detailed, accurate responses. If the answer cannot be found in the context, say \"Not found in context.\""
}

# Model-specific prompt templates (Llama-focused)
PROMPT_TEMPLATES = {
    "llama": """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful financial AI assistant that answers questions based only on the provided context. Analyze the context carefully and provide detailed, accurate responses. If the answer cannot be found in the context, say "Not found in context."<|eot_id|><|start_header_id|>user<|end_header_id|>

Context:
{context}

Question: {query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

""",

    "default": """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful financial AI assistant that answers questions based only on the provided context. Analyze the context carefully and provide detailed, accurate responses. If the answer cannot be found in the context, say "Not found in context."<|eot_id|><|start_header_id|>user<|end_header_id|>

Context:
{context}

Question: {query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
}

def get_prompt_template(model_name: str) -> str:
    """Get the appropriate prompt template for a model (Llama-optimized)."""
    if "llama" in model_name.lower():
        return PROMPT_TEMPLATES["llama"]
    return PROMPT_TEMPLATES["default"]

def get_system_prompt(model_name: str) -> str:
    """Get the appropriate system prompt for a model (Llama-optimized)."""
    if "llama" in model_name.lower():
        return SYSTEM_PROMPTS["llama"]
    return SYSTEM_PROMPTS["default"]