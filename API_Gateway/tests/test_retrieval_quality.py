#!/usr/bin/env python3
"""
Vector Database → LLM Quality Testing Script

Tests retrieval effectiveness and response quality for crypto queries.
Focus: Quality over speed - retrieval accuracy and response relevance.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
API_BASE = "http://localhost:8000"
TIMEOUT = 30

# Quality-focused test queries
RETRIEVAL_QUALITY_TESTS = [
    {
        "category": "Single Asset Deep Dive",
        "queries": [
            "What is the current price, volume, and trend of Bitcoin (BTC-USD)?",
            "Provide detailed analysis of Ethereum (ETH-USD) including price and market activity",
            "Give me comprehensive data on Solana (SOL-USD) performance today"
        ],
        "quality_checks": [
            "exact_ticker_match",
            "current_data",
            "multiple_metrics"
        ]
    },
    {
        "category": "Comparative Analysis",
        "queries": [
            "Compare Bitcoin vs Ethereum: prices, trends, and volume data",
            "Contrast the performance of Cardano (ADA) and Polygon (MATIC) with specific numbers",
            "How do major cryptos Bitcoin, Ethereum, and Solana compare right now?"
        ],
        "quality_checks": [
            "multiple_assets_retrieved",
            "comparative_format",
            "specific_data_points"
        ]
    },
    {
        "category": "Semantic Category Understanding",
        "queries": [
            "What are the current prices and trends of all DeFi tokens in the database?",
            "Show me the performance data for meme coins like DOGE, SHIB, and PEPE",
            "How are Layer 2 blockchain tokens performing: Arbitrum, Optimism, Polygon?"
        ],
        "quality_checks": [
            "category_recognition",
            "multiple_tokens",
            "ecosystem_understanding"
        ]
    }
]

def test_query_quality(query: str) -> Dict[str, Any]:
    """Test a single query and analyze retrieval/response quality."""
    print(f"\n🔍 Testing: {query[:60]}...")

    try:
        start_time = time.time()

        response = requests.post(
            f"{API_BASE}/api/query",
            json={"query": query, "top_k": 8},
            timeout=TIMEOUT
        )

        duration = time.time() - start_time

        if response.status_code != 200:
            return {
                "query": query,
                "success": False,
                "error": f"HTTP {response.status_code}",
                "duration": duration
            }

        data = response.json()

        # Analyze retrieval quality
        sources = data.get('sources', [])
        metrics = data.get('metrics', {})
        response_text = data.get('response', '')

        # Calculate quality scores
        retrieval_quality = analyze_retrieval_quality(sources, query)
        response_quality = analyze_response_quality(response_text, sources, query)

        return {
            "query": query,
            "success": True,
            "duration": duration,
            "retrieval_quality": retrieval_quality,
            "response_quality": response_quality,
            "metrics": {
                "vector_latency": metrics.get('vector_latency', 0),
                "llm_latency": metrics.get('llm_latency', 0),
                "tokens_used": metrics.get('tokens_used', 0)
            },
            "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
        }

    except Exception as e:
        return {
            "query": query,
            "success": False,
            "error": str(e),
            "duration": time.time() - start_time
        }

def analyze_retrieval_quality(sources: List[Dict], query: str) -> Dict[str, Any]:
    """Analyze the quality of vector database retrieval."""
    if not sources:
        return {
            "score": 0.0,
            "grade": "🔴 POOR",
            "documents_found": 0,
            "avg_relevance": 0.0,
            "high_quality_ratio": 0.0,
            "issues": ["No sources retrieved"]
        }

    # Calculate metrics
    relevance_scores = [source.get('score', 0) for source in sources]
    avg_relevance = sum(relevance_scores) / len(relevance_scores)
    high_quality_sources = len([s for s in relevance_scores if s > 0.7])
    high_quality_ratio = high_quality_sources / len(sources)

    # Check for crypto-specific quality indicators
    crypto_indicators = []
    crypto_terms = ['USD', 'BTC', 'ETH', 'price', 'volume', 'change', '$']

    for source in sources:
        content = source.get('content', '').upper()
        if any(term.upper() in content for term in crypto_terms):
            crypto_indicators.append(True)
        else:
            crypto_indicators.append(False)

    crypto_relevance = sum(crypto_indicators) / len(crypto_indicators) if crypto_indicators else 0

    # Determine overall quality grade
    if avg_relevance > 0.8 and high_quality_ratio > 0.6:
        grade = "🟢 EXCELLENT"
    elif avg_relevance > 0.6 and high_quality_ratio > 0.4:
        grade = "🟡 GOOD"
    else:
        grade = "🔴 POOR"

    # Identify issues
    issues = []
    if avg_relevance < 0.6:
        issues.append("Low average relevance")
    if len(sources) < 3:
        issues.append("Insufficient source count")
    if crypto_relevance < 0.5:
        issues.append("Limited crypto-specific data")

    return {
        "score": avg_relevance,
        "grade": grade,
        "documents_found": len(sources),
        "avg_relevance": avg_relevance,
        "high_quality_ratio": high_quality_ratio,
        "crypto_relevance": crypto_relevance,
        "issues": issues if issues else ["None identified"]
    }

def analyze_response_quality(response_text: str, sources: List[Dict], query: str) -> Dict[str, Any]:
    """Analyze the quality of LLM response based on retrieved context."""
    if not response_text:
        return {
            "score": 0.0,
            "grade": "❌ FAILED",
            "indicators": [],
            "issues": ["No response generated"]
        }

    response_upper = response_text.upper()

    # Quality indicators to check
    indicators = {
        "ticker_symbols": any(ticker in response_upper for ticker in ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'MATIC-USD']),
        "specific_prices": '$' in response_text and any(char.isdigit() for char in response_text),
        "percentage_changes": '%' in response_text,
        "trend_indicators": any(emoji in response_text for emoji in ['📈', '📉', '➡️']),
        "volume_data": 'VOLUME' in response_upper,
        "context_utilization": len(sources) > 0 and any(
            word in response_upper for source in sources
            for word in source.get('content', '').upper().split()[:10]
        ),
        "professional_formatting": any(term in response_upper for term in ['ANALYSIS', 'CURRENT', 'TRADING', 'MARKET']),
        "query_completeness": len([word for word in query.lower().split() if word in response_text.lower()]) > len(query.split()) * 0.5
    }

    # Calculate quality score
    quality_score = sum(indicators.values()) / len(indicators)

    # Determine grade
    if quality_score > 0.8:
        grade = "🎯 HIGH QUALITY"
    elif quality_score > 0.6:
        grade = "⚠️ MEDIUM QUALITY"
    else:
        grade = "❌ LOW QUALITY"

    # Identify missing elements
    issues = []
    if not indicators["ticker_symbols"]:
        issues.append("Missing ticker symbols")
    if not indicators["specific_prices"]:
        issues.append("No specific price data")
    if not indicators["context_utilization"]:
        issues.append("Poor context utilization")
    if not indicators["query_completeness"]:
        issues.append("Incomplete query coverage")

    return {
        "score": quality_score,
        "grade": grade,
        "indicators": [k for k, v in indicators.items() if v],
        "issues": issues if issues else ["None identified"]
    }

def run_quality_tests():
    """Run comprehensive retrieval quality tests."""
    print("🚀 Starting Vector Database → LLM Quality Testing")
    print("=" * 60)

    all_results = []
    category_scores = {}

    for test_category in RETRIEVAL_QUALITY_TESTS:
        category_name = test_category["category"]
        queries = test_category["queries"]

        print(f"\n📊 Testing Category: {category_name}")
        print("-" * 40)

        category_results = []

        for query in queries:
            result = test_query_quality(query)
            category_results.append(result)
            all_results.append(result)

            if result["success"]:
                print(f"✅ Retrieval: {result['retrieval_quality']['grade']}")
                print(f"   Response: {result['response_quality']['grade']}")
                print(f"   Duration: {result['duration']:.2f}s")
            else:
                print(f"❌ Failed: {result['error']}")

        # Calculate category averages
        successful_results = [r for r in category_results if r["success"]]
        if successful_results:
            avg_retrieval = sum(r["retrieval_quality"]["score"] for r in successful_results) / len(successful_results)
            avg_response = sum(r["response_quality"]["score"] for r in successful_results) / len(successful_results)
            category_scores[category_name] = {
                "retrieval_avg": avg_retrieval,
                "response_avg": avg_response,
                "success_rate": len(successful_results) / len(category_results)
            }

    # Generate summary report
    print("\n" + "=" * 60)
    print("📈 QUALITY TESTING SUMMARY")
    print("=" * 60)

    successful_tests = [r for r in all_results if r["success"]]
    total_tests = len(all_results)

    if successful_tests:
        overall_retrieval_avg = sum(r["retrieval_quality"]["score"] for r in successful_tests) / len(successful_tests)
        overall_response_avg = sum(r["response_quality"]["score"] for r in successful_tests) / len(successful_tests)

        print(f"📊 Overall Statistics:")
        print(f"   Success Rate: {len(successful_tests)}/{total_tests} ({len(successful_tests)/total_tests*100:.1f}%)")
        print(f"   Avg Retrieval Quality: {overall_retrieval_avg:.3f}")
        print(f"   Avg Response Quality: {overall_response_avg:.3f}")

        print(f"\n📋 Category Breakdown:")
        for category, scores in category_scores.items():
            print(f"   {category}:")
            print(f"     Retrieval: {scores['retrieval_avg']:.3f}")
            print(f"     Response: {scores['response_avg']:.3f}")
            print(f"     Success: {scores['success_rate']*100:.1f}%")

        # Quality assessment
        print(f"\n🎯 Quality Assessment:")
        if overall_retrieval_avg > 0.7 and overall_response_avg > 0.7:
            print("   🟢 EXCELLENT - VD retrieval and LLM responses are high quality")
        elif overall_retrieval_avg > 0.6 or overall_response_avg > 0.6:
            print("   🟡 GOOD - System shows promising retrieval and response quality")
        else:
            print("   🔴 NEEDS IMPROVEMENT - Focus on data quality and prompt engineering")

        # Recommendations
        print(f"\n💡 Recommendations:")
        low_retrieval_categories = [cat for cat, scores in category_scores.items() if scores['retrieval_avg'] < 0.6]
        low_response_categories = [cat for cat, scores in category_scores.items() if scores['response_avg'] < 0.6]

        if low_retrieval_categories:
            print(f"   📊 Improve VD search for: {', '.join(low_retrieval_categories)}")
        if low_response_categories:
            print(f"   🧠 Enhance LLM prompts for: {', '.join(low_response_categories)}")
        if not low_retrieval_categories and not low_response_categories:
            print("   🚀 System is performing well - consider expanding test coverage")

    else:
        print("❌ No successful tests - check system connectivity and data availability")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"quality_test_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": len(successful_tests),
                "overall_retrieval_avg": overall_retrieval_avg if successful_tests else 0,
                "overall_response_avg": overall_response_avg if successful_tests else 0,
                "category_scores": category_scores
            },
            "detailed_results": all_results
        }, f, indent=2)

    print(f"\n💾 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    run_quality_tests()