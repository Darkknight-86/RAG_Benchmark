"""
Prompt management module for the LLM service.

This module handles all aspects of prompt formatting, validation, and management.
"""

from typing import Dict, Optional, List
import logging
from config import PROMPT_TEMPLATES, MODEL_CONFIG, SYSTEM_PROMPTS, get_system_prompt

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
    def format_financial_prompt(query: str, context: str) -> str:
        """
        Format a financial-specific prompt with retrieved context.

        Args:
            query: Financial query from user
            context: Retrieved financial context from vector store

        Returns:
            Formatted financial prompt
        """
        financial_prompt = """Based on the financial data below, answer the question about price and performance.

Data: {context}

Question: {query}

Answer with specific prices and percentages from the data:"""

        return financial_prompt.format(context=context, query=query)

    @staticmethod
    def format_stock_analysis_prompt(ticker: str, context: str, query: str) -> str:
        """
        Format a prompt specifically for stock analysis.

        Args:
            ticker: Stock ticker symbol
            context: Financial data context
            query: Analysis request

        Returns:
            Formatted stock analysis prompt
        """
        analysis_prompt = """You are analyzing {ticker} based on real-time market data.

REAL-TIME DATA FOR {ticker}:
{context}

ANALYSIS REQUEST: {query}

Please provide a detailed analysis including:
1. Current price and recent changes
2. Volume trends if available
3. Any notable patterns in the data
4. Relevant context from the provided information

ANALYSIS:"""

        return analysis_prompt.format(ticker=ticker, context=context, query=query)

    @staticmethod
    def format_market_summary_prompt(context: str, query: str) -> str:
        """
        Format a prompt for market summary queries.

        Args:
            context: Market data context
            query: Market summary request

        Returns:
            Formatted market summary prompt
        """
        market_prompt = """You are providing a market summary based on real-time financial data.

MARKET DATA:
{context}

REQUEST: {query}

Please provide a comprehensive market summary including:
- Key market movements
- Notable stock performances
- Volume and trading activity
- Any significant trends or patterns

MARKET SUMMARY:"""

        return market_prompt.format(context=context, query=query)

    @staticmethod
    def _get_template(model_name: str) -> str:
        """Get the appropriate prompt template for a model (Llama-optimized)."""
        # All supported models are Llama-based now
        if "llama" in model_name.lower():
            return PROMPT_TEMPLATES["llama"]
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
        if len(query) > 12000:  # Increased limit for RAG context + user query
            raise ValueError("Query exceeds maximum length of 12000 characters")

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