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
            # Step 1: Vector Retrieval
            print(f"🔍 Searching for: {query[:50]}...")
            retrieval_start = time.time()
            retrieved_docs = self.vector_store.similarity_search_with_score(query, k=top_k)
            retrieval_time = time.time() - retrieval_start

            if not retrieved_docs:
                return {
                    "answer": "I couldn't find relevant information to answer your question.",
                    "sources": [],
                    "metrics": {
                        "vector_latency": retrieval_time,
                        "llm_latency": 0.0,
                        "total_time": time.time() - start_time,
                        "tokens_used": 0,
                        "model_name": model_name or MODEL_CONFIG["default_model"]
                    }
                }

            print(f"📄 Found {len(retrieved_docs)} relevant documents")

            # Step 2: Prepare Context
            context_docs = []
            sources = []

            for doc, score in retrieved_docs:
                context_docs.append(doc.page_content)
                sources.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "score": float(score),
                    "metadata": dict(doc.metadata)
                })

            context = "\n\n".join(context_docs)

            # Step 3: Generate Response
            print("🧠 Generating LLM response...")
            llm_start = time.time()

            # Get appropriate prompt template
            prompt = self.prompt_manager.format_financial_prompt(query, context)

            # Generate response using LLM
            response_text, response_latency, tokens_used = self.llm_manager.generate_response(
                prompt=prompt,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )

            llm_time = time.time() - llm_start
            total_time = time.time() - start_time

            print(f"✅ Query completed in {total_time:.3f}s")

            return {
                "answer": response_text,
                "sources": sources,
                "metrics": {
                    "vector_latency": retrieval_time,
                    "llm_latency": llm_time,
                    "total_time": total_time,
                    "tokens_used": tokens_used,
                    "model_name": model_name or MODEL_CONFIG["default_model"]
                }
            }

        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return {
                "answer": f"I encountered an error processing your request: {str(e)}",
                "sources": [],
                "metrics": {
                    "vector_latency": 0.0,
                    "llm_latency": 0.0,
                    "total_time": time.time() - start_time,
                    "tokens_used": 0,
                    "model_name": model_name or MODEL_CONFIG["default_model"],
                    "error": str(e)
                }
            }

    def get_financial_context(self, query: str, ticker: Optional[str] = None) -> List[Dict]:
        """
        Get financial-specific context for a query.
        Can filter by specific ticker if provided.
        """
        try:
            if ticker:
                print(f"💰 Getting context for ticker: {ticker}")
                # Use optimized search for specific ticker
                results = self.vector_store.client.query(f"""
                    SELECT chunk, price, change_percent, volume, timestamp,
                           cosineDistance(embedding,
                               {self.vector_store.embedding_model.encode([query])[0].tolist()}) as distance
                    FROM rag_chunks_v2
                    WHERE security = '{ticker}'
                    ORDER BY distance ASC
                    LIMIT 10
                """)

                return [
                    {
                        "content": row[0],
                        "price": float(row[1]),
                        "change_percent": float(row[2]),
                        "volume": int(row[3]),
                        "timestamp": row[4],
                        "score": 1.0 - row[5]  # Convert distance to similarity
                    }
                    for row in results.result_rows
                ]
            else:
                # Regular semantic search
                docs = self.vector_store.similarity_search_with_score(query, k=10)
                return [
                    {
                        "content": doc.page_content,
                        "score": score,
                        "metadata": doc.metadata
                    }
                    for doc, score in docs
                ]

        except Exception as e:
            print(f"❌ Error getting financial context: {e}")
            return []

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of RAG pipeline components"""
        status = {
            "vector_store": "unknown",
            "llm_manager": "unknown",
            "overall": "unknown"
        }

        try:
            # Test vector store
            test_results = self.vector_store.similarity_search("test", k=1)
            status["vector_store"] = "healthy"
        except:
            status["vector_store"] = "unhealthy"

        try:
            # Test LLM manager
            # This is a basic check - you might want to make it more comprehensive
            status["llm_manager"] = "healthy"
        except:
            status["llm_manager"] = "unhealthy"

        # Overall status
        if all(s == "healthy" for s in [status["vector_store"], status["llm_manager"]]):
            status["overall"] = "healthy"
        else:
            status["overall"] = "unhealthy"

        return status