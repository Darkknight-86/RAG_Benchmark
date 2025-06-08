#!/usr/bin/env python3
"""
Direct LLM Service Test
Tests the LLM service directly without going through API Gateway
"""

import sys
import os
sys.path.append('LLM/src')

from llm_manager import LLMManager
from config import MODEL_CONFIG
import traceback

def test_llm_direct():
    """Test LLM manager directly (Llama-only)"""
    print("🧪 Direct Llama Test Starting...")
    print(f"🔧 Default model: {MODEL_CONFIG['default_model']}")

    # Check environment
    hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
    if hf_token:
        print(f"🔑 HF Token present: {hf_token[:10]}...")
    else:
        print("⚠️ No HF Token found")

    try:
        # Initialize LLM Manager
        print("\n📝 Initializing LLM Manager...")
        llm_manager = LLMManager()

        # Test with Llama 3.2 1B
        print("\n🧪 Testing Llama 3.2 1B model...")
        response, latency, tokens = llm_manager.generate_response(
            prompt="What is Bitcoin?",
            model_name="meta-llama/Llama-3.2-1B-Instruct",
            max_tokens=2048,  # Maximum possible tokens
            temperature=0.7
        )
        print(f"✅ Llama Response: {response}")
        print(f"📊 Latency: {latency:.3f}s, Tokens: {tokens}")

        # Test with financial query
        print("\n🧪 Testing Llama with financial context...")
        financial_response, fin_latency, fin_tokens = llm_manager.generate_response(
            prompt="Explain cryptocurrency market volatility",
            model_name="meta-llama/Llama-3.2-1B-Instruct",
            max_tokens=1500,
            temperature=0.7
        )
        print(f"✅ Financial Response: {financial_response}")
        print(f"📊 Financial Latency: {fin_latency:.3f}s, Tokens: {fin_tokens}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"📋 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_direct()