"""
Complete RAG pipeline for financial queries.
Handles retrieval from ClickHouse and generation with LLM.
"""

import time
from typing import List, Dict, Any, Optional
from connect_db import get_vector_db
from llm_manager import LLMManager
from prompt_manager import PromptManager
from config import MODEL_CONFIG


class RAGPipeline:
    """
    Complete RAG pipeline for financial queries.
    Handles retrieval from ClickHouse and generation with LLM.
    """

    def __init__(self):
        self.vector_store = get_vector_db()
        self.llm_manager = LLMManager()
        self.prompt_manager = PromptManager()

        if not self.vector_store:
            raise RuntimeError("Failed to connect to vector store")

        print("🚀 RAG Pipeline initialized successfully")

    async def query(
        self,
        query: str,
        top_k: int = 5,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 200
    ) -> Dict[str, Any]:
        """
        Process a RAG query end-to-end.

        Args:
            query: Natural language query
            top_k: Number of relevant documents to retrieve
            model_name: LLM model to use (optional)
            temperature: LLM temperature parameter
            max_tokens: Maximum tokens for response

        Returns:
            Dictionary with answer, sources, and metrics
        """
        start_time = time.time()

        try:
            # Step 1: Enhanced Vector Retrieval with debugging
            print(f"🔍 Searching for: {query[:50]}...")
            retrieval_start = time.time()

            # Try multiple search strategies for crypto/financial queries
            retrieved_docs = []
            search_strategies = []

            # Strategy 1: Standard similarity search
            try:
                docs = self.vector_store.similarity_search_with_score(query, k=top_k)
                retrieved_docs.extend(docs)
                search_strategies.append(f"similarity_search: {len(docs)} docs")
            except Exception as e:
                print(f"⚠️ Standard similarity search failed: {e}")
                search_strategies.append("similarity_search: failed")

            # Strategy 2: Enhanced crypto search with expanded coverage
            crypto_terms = [
                "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", "solana", "sol",
                "cardano", "ada", "ripple", "xrp", "dogecoin", "doge", "avalanche", "avax",
                "polkadot", "dot", "chainlink", "link", "polygon", "matic", "litecoin", "ltc",
                "binance", "bnb", "tether", "usdt", "shiba", "shib", "near", "uniswap", "uni",
                "cosmos", "atom", "filecoin", "fil", "tron", "trx", "aave", "maker", "mkr",
                "pepe", "floki", "bonk", "stellar", "xlm", "algorand", "algo", "hedera", "hbar",
                "sandbox", "sand", "decentraland", "mana", "chiliz", "chz", "dai", "arbitrum",
                "optimism", "aptos", "apt", "sui", "injective", "inj", "celestia", "tia"
            ]

            if any(term in query.lower() for term in crypto_terms):
                try:
                    if hasattr(self.vector_store, 'client'):
                        crypto_results = self.vector_store.client.query(
                            """
                            SELECT chunk, price, change_percent, volume, security, timestamp
                            FROM rag_chunks_v2
                            WHERE security LIKE '%-USD'
                              AND security NOT LIKE '%=X'
                            ORDER BY timestamp DESC
                            LIMIT 15
                            """
                        )

                        for row in crypto_results.result_rows:
                            from langchain_core.documents import Document
                            crypto_name = row[4].replace('-USD', '').replace('USD', '')
                            indicator = "📈" if float(row[2]) > 0 else "📉" if float(row[2]) < 0 else "➡️"
                            doc = Document(
                                page_content=f"""
                                    {crypto_name} Cryptocurrency Analysis:
                                    - Current Price: ${row[1]:.4f}
                                    - 24h Change: {row[2]:.2f}% {indicator}
                                    - Trading Volume: {row[3]:,}
                                    - Last Updated: {row[5]}
                                    - Market Status: Active Trading (24/7)
                                    - Asset Type: Cryptocurrency
                                """.strip(),
                                metadata={
                                    "security": row[4],
                                    "price": row[1],
                                    "change_percent": row[2],
                                    "volume": row[3],
                                    "timestamp": row[5],
                                    "asset_type": "cryptocurrency"
                                }
                            )
                            retrieved_docs.append((doc, 0.9))

                        search_strategies.append(
                            f"crypto_enhanced: {len(crypto_results.result_rows)} docs"
                        )
                except Exception as e:
                    print(f"⚠️ Enhanced crypto search failed: {e}")
                    search_strategies.append("crypto_enhanced: failed")

            # Strategy 3: Fallback with broader search
            if not retrieved_docs:
                try:
                    broad_results = self.vector_store.client.query(
                        """
                        SELECT chunk, security, timestamp
                        FROM rag_chunks_v2
                        ORDER BY timestamp DESC
                        LIMIT 5
                        """
                    )
                    for row in broad_results.result_rows:
                        from langchain_core.documents import Document
                        doc = Document(
                            page_content=f"Recent financial data for {row[1]}: {row[0]}",
                            metadata={"security": row[1], "timestamp": row[2]}
                        )
                        retrieved_docs.append((doc, 0.6))
                    search_strategies.append(
                        f"broad_search: {len(broad_results.result_rows)} docs"
                    )
                except Exception as e:
                    print(f"⚠️ Broad search failed: {e}")
                    search_strategies.append("broad_search: failed")

            retrieval_time = time.time() - retrieval_start
            print(f"📊 Search strategies used: {', '.join(search_strategies)}")
            print(f"📄 Total documents found: {len(retrieved_docs)}")

            # Retrieval quality assessment
            retrieval_quality = {}
            if retrieved_docs:
                avg_rel = sum(score for _, score in retrieved_docs) / len(retrieved_docs)
                high_q = [d for d, s in retrieved_docs if s > 0.7]
                print("📈 Retrieval Quality Assessment:")
                print(f"  - Average relevance: {avg_rel:.3f}")
                print(f"  - High-quality docs: {len(high_q)}/{len(retrieved_docs)}")

                # Store retrieval quality metrics for response
                retrieval_quality = {
                    "docs_found": len(retrieved_docs),
                    "avg_relevance": avg_rel,
                    "high_quality_docs": len(high_q),
                    "high_quality_ratio": len(high_q) / len(retrieved_docs)
                }
            else:
                retrieval_quality = {
                    "docs_found": 0,
                    "avg_relevance": 0.0,
                    "high_quality_docs": 0,
                    "high_quality_ratio": 0.0
                }

            # Parse search strategies for structured metrics
            search_metrics = {}
            for strategy in search_strategies:
                if ":" in strategy:
                    strategy_name, strategy_result = strategy.split(":", 1)
                    strategy_name = strategy_name.strip()
                    if "docs" in strategy_result:
                        # Extract number of docs found
                        docs_count = strategy_result.strip().split()[0]
                        try:
                            search_metrics[strategy_name] = int(docs_count)
                        except:
                            search_metrics[strategy_name] = strategy_result.strip()
                    else:
                        search_metrics[strategy_name] = strategy_result.strip()

            if not retrieved_docs:
                return {
                    "answer": (
                        f"No relevant data. Strategies: {', '.join(search_strategies)}."
                    ),
                    "sources": [],
                    "metrics": {
                        "vector_latency": retrieval_time,
                        "llm_latency": 0.0,
                        "total_time": time.time() - start_time,
                        "tokens_used": 0,
                        "model_name": model_name or MODEL_CONFIG["default_model"],
                        "search_strategies": search_strategies,
                        "search_metrics": search_metrics,
                        "retrieval_quality": retrieval_quality
                    }
                }

            # Prepare context with length management
            context_parts = []
            total_length = 0
            max_context_length = 3000  # Conservative limit for prompt + context

            for doc, score in retrieved_docs:
                content = doc.page_content
                if total_length + len(content) < max_context_length:
                    context_parts.append(content)
                    total_length += len(content)
                else:
                    # Truncate the last document to fit
                    remaining_space = max_context_length - total_length
                    if remaining_space > 100:  # Only add if meaningful space left
                        context_parts.append(content[:remaining_space] + "...")
                    break

            context = "\n\n".join(context_parts)
            sources = [
                {
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "score": float(score),
                    "metadata": dict(doc.metadata)
                }
                for doc, score in retrieved_docs
            ]

            # Generate response
            print("🧠 Generating LLM response...")
            llm_start = time.time()
            prompt = self.prompt_manager.format_financial_prompt(query, context)
            response_text, _, tokens = self.llm_manager.generate_response(
                prompt=prompt,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            llm_time = time.time() - llm_start
            total_time = time.time() - start_time

            print(f"✅ Completed in {total_time:.3f}s")
            return {
                "answer": response_text,
                "sources": sources,
                "metrics": {
                    "vector_latency": retrieval_time,
                    "llm_latency": llm_time,
                    "total_time": total_time,
                    "tokens_used": tokens,
                    "model_name": model_name or MODEL_CONFIG["default_model"],
                    "search_strategies": search_strategies,
                    "search_metrics": search_metrics,
                    "retrieval_quality": retrieval_quality
                }
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "answer": f"Error: {e}",
                "sources": [],
                "metrics": {
                    "vector_latency": 0.0,
                    "llm_latency": 0.0,
                    "total_time": time.time() - start_time,
                    "tokens_used": 0,
                    "model_name": model_name or MODEL_CONFIG["default_model"],
                    "search_strategies": [],
                    "search_metrics": {},
                    "retrieval_quality": {
                        "docs_found": 0,
                        "avg_relevance": 0.0,
                        "high_quality_docs": 0,
                        "high_quality_ratio": 0.0
                    },
                    "error": str(e)
                }
            }

    def get_financial_context(self, query: str, ticker: Optional[str] = None) -> List[Dict]:
        """Get financial-specific context"""
        try:
            if ticker:
                print(f"💰 Getting context for ticker: {ticker}")
                results = self.vector_store.client.query(
                    f"""
                    SELECT chunk, price, change_percent, volume, timestamp,
                           cosineDistance(embedding,
                               {self.vector_store.embedding_model.encode([query])[0].tolist()})
                      AS distance
                    FROM rag_chunks_v2
                    WHERE security = '{ticker}'
                    ORDER BY distance ASC
                    LIMIT 10
                    """
                )
                return [
                    {
                        "content": r[0],
                        "price": float(r[1]),
                        "change_percent": float(r[2]),
                        "volume": int(r[3]),
                        "timestamp": r[4],
                        "score": 1.0 - r[5]
                    }
                    for r in results.result_rows
                ]
            else:
                docs = self.vector_store.similarity_search_with_score(query, k=10)
                return [
                    {
                        "content": d.page_content,
                        "score": s,
                        "metadata": d.metadata
                    }
                    for d, s in docs
                ]
        except Exception as e:
            print(f"❌ Context error: {e}")
            return []

    def get_health_status(self) -> Dict[str, Any]:
        """Health status of pipeline components"""
        status = {
            "vector_store": "unknown",
            "llm_manager": "unknown",
            "overall": "unknown"
        }

        # Test vector store
        try:
            self.vector_store.similarity_search("test", k=1)
            status["vector_store"] = "healthy"
        except:
            status["vector_store"] = "unhealthy"

        # Test LLM manager
        try:
            # Basic health check for LLM manager
            status["llm_manager"] = "healthy" if self.llm_manager else "unhealthy"
        except:
            status["llm_manager"] = "unhealthy"

        # Overall status
        if all(s == "healthy" for s in [status["vector_store"], status["llm_manager"]]):
            status["overall"] = "healthy"
        else:
            status["overall"] = "unhealthy"

        return status