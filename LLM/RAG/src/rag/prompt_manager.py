"""
Prompt management module for the LLM service.

This module handles all aspects of prompt formatting, validation, and management.
"""

from typing import Dict, Optional, List
import logging
from .config import PROMPT_TEMPLATES, MODEL_CONFIG, SYSTEM_PROMPTS, get_system_prompt

logger = logging.getLogger(__name__)

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
        logger.info(f"Formatting prompt for model: {model_name}")

        template = PromptManager._get_template(model_name)
        system_prompt = get_system_prompt(model_name)

        # Combine context into a single string, handle empty context
        context_str = "\n".join(context) if context else "No relevant context found."

        try:
            formatted_prompt = template.format(
                query=query,
                context=context_str,
                system_prompt=system_prompt
            )
            logger.debug(f"Formatted prompt: {formatted_prompt[:100]}...")  # Log first 100 chars
            return formatted_prompt
        except KeyError as e:
            logger.error(f"Error formatting prompt: {str(e)}")
            raise ValueError(f"Error formatting prompt: {str(e)}")

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
        logger.info(f"Getting requirements for model: {model_name}")
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