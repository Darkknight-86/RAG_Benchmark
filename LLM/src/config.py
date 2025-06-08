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

# System prompts for different models
SYSTEM_PROMPTS = {
    "flan-t5": "You are an assistant that answers questions based only on the provided context. Do not use any external knowledge. If the answer cannot be found in the context, say \"Not found in context.\"",
    "instruct": "You are an assistant that answers questions based only on the provided context. Do not use any external knowledge. If the answer cannot be found in the context, say \"Not found in context.\" Always cite your sources when possible.",
    "default": "You are an assistant that answers questions based only on the provided context. Do not use any external knowledge. If the answer cannot be found in the context, say \"Not found in context.\""
}

# Model-specific prompt templates
PROMPT_TEMPLATES = {
    "flan-t5": """Instruction: Using only the information in the context provided, respond to the question below.
Do not include any outside knowledge or assumptions. If the answer cannot be found in the context, say "Not found in context."

Context:
{context}

Question:
{query}

Answer:""",

    "instruct": """<s>[INST] <<SYS>>
{system_prompt}
<</SYS>>

Instruction: Using only the information in the context provided, respond to the question below.
Do not include any outside knowledge or assumptions. If the answer cannot be found in the context, say "Not found in context."

Context:
{context}

Question:
{query} [/INST]""",

    "default": """Instruction: Using only the information in the context provided, respond to the question below.
Do not include any outside knowledge or assumptions. If the answer cannot be found in the context, say "Not found in context."

Context:
{context}

Question:
{query}

Answer:"""
}

def get_prompt_template(model_name: str) -> str:
    """Get the appropriate prompt template for a model."""
    if "instruct" in model_name.lower():
        return PROMPT_TEMPLATES["instruct"]
    elif "flan" in model_name.lower() or "t5" in model_name.lower():
        return PROMPT_TEMPLATES["flan-t5"]
    return PROMPT_TEMPLATES["default"]

def get_system_prompt(model_name: str) -> str:
    """Get the appropriate system prompt for a model."""
    if "instruct" in model_name.lower():
        return SYSTEM_PROMPTS["instruct"]
    elif "flan" in model_name.lower() or "t5" in model_name.lower():
        return SYSTEM_PROMPTS["flan-t5"]
    return SYSTEM_PROMPTS["default"]