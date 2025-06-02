"""
Prompt management module for the LLM service.

This module handles all aspects of prompt formatting, validation, and management.
"""

from typing import Dict, Optional, List
from .config import PROMPT_TEMPLATES, MODEL_CONFIG, SYSTEM_PROMPTS, get_system_prompt

class PromptManager:
    """Manages prompt formatting and validation for different models."""

    @staticmethod
    def format_prompt(query: str, context: List[str], model_name: str) -> str:
        """
        Format a query according to the model's requirements.

        Args:
            query: The raw user query
            context: List of context strings from the RAG system
            model_name: Name of the model to format for

        Returns:
            Formatted prompt string
        """
        template = PromptManager._get_template(model_name)
        system_prompt = get_system_prompt(model_name)

        # Combine context into a single string
        context_str = "\n".join(context) if context else "No relevant context found."

        return template.format(
            query=query,
            context=context_str,
            system_prompt=system_prompt
        )

    @staticmethod
    def _get_template(model_name: str) -> str:
        """Get the appropriate prompt template for a model."""
        if "instruct" in model_name.lower():
            return PROMPT_TEMPLATES["instruct"]
        elif "flan" in model_name.lower() or "t5" in model_name.lower():
            return PROMPT_TEMPLATES["flan-t5"]
        return PROMPT_TEMPLATES["default"]

    @staticmethod
    def validate_query(query: str) -> None:
        """
        Validate a query before processing.

        Args:
            query: The query to validate

        Raises:
            ValueError: If query is invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if len(query) > 1000:  # Reasonable limit for most models
            raise ValueError("Query exceeds maximum length of 1000 characters")

    @staticmethod
    def get_model_requirements(model_name: str) -> Dict:
        """
        Get the requirements and capabilities of a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dict containing model requirements and capabilities
        """
        return {
            "max_input_length": 512,  # Example value, should be model-specific
            "supports_streaming": "instruct" in model_name.lower(),
            "requires_system_prompt": "instruct" in model_name.lower(),
            "default_temperature": MODEL_CONFIG["default_temperature"],
            "default_max_tokens": MODEL_CONFIG["default_max_tokens"],
            "default_top_k": MODEL_CONFIG["default_top_k"]
        }

# Create a singleton instance
prompt_manager = PromptManager()