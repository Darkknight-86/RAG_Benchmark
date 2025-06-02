"""
Configuration settings for the LLM service.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model Configuration
MODEL_CONFIG: Dict[str, Any] = {
    "default_model": os.getenv("DEFAULT_LLM_MODEL", "google/flan-t5-small"),
    "default_temperature": float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
    "default_max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", "200")),
    "default_top_k": int(os.getenv("DEFAULT_TOP_K", "5")),
    "supported_models": os.getenv("SUPPORTED_MODELS", "google/flan-t5-small,google/flan-t5-base,google/flan-t5-large").split(",")
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

# Model-specific prompt templates
PROMPT_TEMPLATES = {
    "flan-t5": "Question: {query}\nAnswer:",
    "instruct": "<s>[INST] {query} [/INST]",
    "default": "{query}"
}

def get_prompt_template(model_name: str) -> str:
    """Get the appropriate prompt template for a model."""
    if "instruct" in model_name.lower():
        return PROMPT_TEMPLATES["instruct"]
    elif "flan" in model_name.lower() or "t5" in model_name.lower():
        return PROMPT_TEMPLATES["flan-t5"]
    return PROMPT_TEMPLATES["default"]