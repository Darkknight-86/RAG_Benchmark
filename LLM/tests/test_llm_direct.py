#!/usr/bin/env python3
"""
Direct LLM Service Test - Complex Query Stress Test
Tests the LLM service with demanding, nuanced queries to evaluate float16 performance
"""

import sys
import os
import time
import psutil
sys.path.append('../src')

from llm_manager import LLMManager
from config import MODEL_CONFIG
import traceback

def monitor_system_resources():
    """Monitor CPU and memory usage"""
    process = psutil.Process()
    return {
        "cpu_percent": process.cpu_percent(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "system_cpu": psutil.cpu_percent(interval=1)
    }

def test_complex_llm_queries():
    """Test LLM manager with complex, nuanced queries"""
    print("🧪 Complex LLM Query Stress Test Starting...")
    print(f"🔧 Default model: {MODEL_CONFIG['default_model']}")
    print(f"💾 Using float16 for reduced CPU load")

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

        # Complex test queries that require nuanced reasoning
        complex_queries = [
            {
                "name": "Multi-Factor Financial Analysis",
                "query": """Analyze the complex relationship between cryptocurrency market volatility,
                traditional stock market performance, and macroeconomic factors like inflation rates and
                Federal Reserve policy changes. Consider how institutional adoption of Bitcoin affects
                portfolio diversification strategies for both retail and institutional investors.
                Discuss the implications of regulatory uncertainty across different jurisdictions and
                how this impacts long-term investment thesis for digital assets versus traditional safe havens like gold.""",
                "max_tokens": 1200,  # Increased for better quality responses
                "temperature": 0.8
            },
            {
                "name": "Technical Market Analysis with Context",
                "query": """Given the current market environment where we're seeing divergent monetary policies
                between the Federal Reserve, European Central Bank, and Bank of Japan, analyze how this creates
                arbitrage opportunities in currency markets while simultaneously affecting commodity prices,
                particularly energy and precious metals. Factor in geopolitical tensions, supply chain disruptions,
                and the transition to renewable energy. How should sophisticated investors position themselves
                considering these interconnected variables, and what are the risk management implications for
                different asset classes over the next 12-18 months?""",
                "max_tokens": 1400,  # Increased for better quality responses
                "temperature": 0.7
            },
            {
                "name": "ESG Investment Strategy Analysis",
                "query": """Evaluate the paradox in ESG (Environmental, Social, Governance) investing where
                companies with strong ESG scores may sometimes underperform financially in the short term,
                while also considering the long-term value creation potential. Analyze how carbon pricing
                mechanisms, regulatory changes around climate disclosure, and shifting consumer preferences
                are reshaping industry valuations. Discuss the methodological challenges in ESG scoring,
                the risk of greenwashing, and how institutional investors can develop robust frameworks
                for authentic sustainable investing that balances fiduciary duty with environmental impact.
                Consider the role of activist investing and shareholder engagement in driving corporate change.""",
                "max_tokens": 1300,  # Increased for better quality responses
                "temperature": 0.6
            }
        ]

        # Run complex queries and monitor performance
        for i, test_case in enumerate(complex_queries, 1):
            print(f"\n{'='*80}")
            print(f"🔥 TEST {i}: {test_case['name']}")
            print(f"📊 Query Length: {len(test_case['query'])} characters")
            print(f"🎯 Max Tokens: {test_case['max_tokens']}")
            print(f"{'='*80}")

            # Monitor resources before
            resources_before = monitor_system_resources()
            print(f"📈 CPU Before: {resources_before['system_cpu']:.1f}% | Memory: {resources_before['memory_mb']:.1f}MB")

            # Run the complex query
            start_time = time.time()
            try:
                response, latency, tokens = llm_manager.generate_response(
                    prompt=test_case['query'],
                    model_name="meta-llama/Llama-3.2-1B-Instruct",
                    max_tokens=test_case['max_tokens'],
                    temperature=test_case['temperature']
                )

                # Monitor resources after
                resources_after = monitor_system_resources()
                total_time = time.time() - start_time

                print(f"✅ COMPLETED SUCCESSFULLY")
                print(f"📊 Performance Metrics:")
                print(f"   ⏱️  Total Time: {total_time:.3f}s")
                print(f"   🧠 LLM Latency: {latency:.3f}s")
                print(f"   🎯 Tokens Generated: {tokens}")
                print(f"   ⚡ Tokens/Second: {tokens/latency:.1f}")
                print(f"   📈 CPU Peak: {resources_after['system_cpu']:.1f}%")
                print(f"   💾 Memory Used: {resources_after['memory_mb']:.1f}MB")

                print(f"\n📝 RESPONSE PREVIEW:")
                print(f"   {response[:200]}...")
                if len(response) > 200:
                    print(f"   [Response truncated - Total length: {len(response)} characters]")

                # Calculate performance score
                performance_score = (tokens / latency) / resources_after['system_cpu']
                print(f"⭐ Performance Score (tokens/sec/cpu%): {performance_score:.2f}")

            except Exception as e:
                print(f"❌ ERROR in {test_case['name']}: {e}")
                print("📋 Error details:")
                traceback.print_exc()

            # Rest between tests
            if i < len(complex_queries):
                print(f"\n⏸️  Resting 5 seconds before next test...")
                time.sleep(5)

        # Summary test with concurrent complexity
        print(f"\n{'='*80}")
        print(f"🚀 FINAL STRESS TEST: Multi-Part Complex Analysis")
        print(f"{'='*80}")

        mega_complex_query = """
        Conduct a comprehensive analysis addressing multiple interconnected aspects:

        1. MARKET STRUCTURE ANALYSIS: Examine how high-frequency trading and algorithmic trading have
           fundamentally altered market microstructure, particularly during periods of extreme volatility.
           Consider the role of market makers, the impact on price discovery, and liquidity provision.

        2. BEHAVIORAL FINANCE PERSPECTIVE: Analyze how cognitive biases, herd mentality, and social media
           influence modern market dynamics. Discuss the implications of retail investor behavior during
           market stress events and how this differs from institutional responses.

        3. SYSTEMIC RISK ASSESSMENT: Evaluate interconnectedness risks in the current financial system,
           including counterparty risk, concentration risk, and the potential for contagion across
           different asset classes and geographic regions.

        4. REGULATORY ARBITRAGE AND COMPLIANCE: Examine how varying regulatory frameworks across
           jurisdictions create arbitrage opportunities while also introducing compliance complexities
           for global financial institutions.

        5. TECHNOLOGICAL DISRUPTION IMPACT: Assess how fintech innovations, blockchain technology,
           and central bank digital currencies (CBDCs) are reshaping traditional banking and
           payment systems.

        Synthesize these elements into actionable investment insights considering both opportunities
        and risk mitigation strategies for the next 2-3 years.
        """

        resources_before = monitor_system_resources()
        print(f"📈 System Status Before Mega Test:")
        print(f"   CPU: {resources_before['system_cpu']:.1f}% | Memory: {resources_before['memory_mb']:.1f}MB")

        start_time = time.time()
        try:
            response, latency, tokens = llm_manager.generate_response(
                prompt=mega_complex_query,
                model_name="meta-llama/Llama-3.2-1B-Instruct",
                max_tokens=1800,  # Increased for comprehensive analysis
                temperature=0.75
            )

            resources_after = monitor_system_resources()
            total_time = time.time() - start_time

            print(f"🎉 MEGA TEST COMPLETED!")
            print(f"📊 Final Performance Metrics:")
            print(f"   ⏱️  Total Processing Time: {total_time:.3f}s")
            print(f"   🧠 Model Inference Time: {latency:.3f}s")
            print(f"   🎯 Total Tokens: {tokens}")
            print(f"   ⚡ Processing Speed: {tokens/latency:.1f} tokens/sec")
            print(f"   💻 Peak CPU Usage: {resources_after['system_cpu']:.1f}%")
            print(f"   💾 Peak Memory: {resources_after['memory_mb']:.1f}MB")

            # Performance assessment
            if latency < 30 and resources_after['system_cpu'] < 90:
                print(f"✅ EXCELLENT: float16 optimization working well!")
            elif latency < 60 and resources_after['system_cpu'] < 95:
                print(f"🟡 GOOD: Acceptable performance with float16")
            else:
                print(f"🔴 NEEDS OPTIMIZATION: Consider further optimizations")

            print(f"\n📝 MEGA RESPONSE SAMPLE:")
            print(f"   {response[:300]}...")
            print(f"   [Full response: {len(response)} characters]")

        except Exception as e:
            print(f"❌ MEGA TEST FAILED: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Overall Test Failed: {e}")
        print(f"📋 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Complex LLM Stress Test with float16 optimization...")
    test_complex_llm_queries()
    print("🏁 Complex LLM Stress Test Complete!")