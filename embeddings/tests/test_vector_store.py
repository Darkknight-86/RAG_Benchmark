#!/usr/bin/env python3
"""
Test script to demonstrate ClickHouse vector store functionality with LangChain documents.
"""

from uuid import uuid4
from langchain_core.documents import Document

# Import your adapter
from src.rag.Adapters.ClickHouseAdapter import ClickHouseAdapter

def test_vector_store():
    """Test the ClickHouse vector store with sample documents."""

    # Initialize the adapter
    print("Initializing ClickHouse adapter...")
    vector_store = ClickHouseAdapter()

    # Create sample documents as specified by the user
    document_1 = Document(
        page_content="I had chocolate chip pancakes and scrambled eggs for breakfast this morning.",
        metadata={"source": "tweet"},
    )

    document_2 = Document(
        page_content="The weather forecast for tomorrow is cloudy and overcast, with a high of 62 degrees.",
        metadata={"source": "news"},
    )

    document_3 = Document(
        page_content="Building an exciting new project with LangChain - come check it out!",
        metadata={"source": "tweet"},
    )

    document_4 = Document(
        page_content="Robbers broke into the city bank and stole $1 million in cash.",
        metadata={"source": "news"},
    )

    document_5 = Document(
        page_content="Wow! That was an amazing movie. I can't wait to see it again.",
        metadata={"source": "tweet"},
    )

    document_6 = Document(
        page_content="Is the new iPhone worth the price? Read this review to find out.",
        metadata={"source": "website"},
    )

    document_7 = Document(
        page_content="The top 10 soccer players in the world right now.",
        metadata={"source": "website"},
    )

    document_8 = Document(
        page_content="LangGraph is the best framework for building stateful, agentic applications!",
        metadata={"source": "tweet"},
    )

    document_9 = Document(
        page_content="The stock market is down 500 points today due to fears of a recession.",
        metadata={"source": "news"},
    )

    document_10 = Document(
        page_content="I have a bad feeling I am going to get deleted :(",
        metadata={"source": "tweet"},
    )

    documents = [
        document_1,
        document_2,
        document_3,
        document_4,
        document_5,
        document_6,
        document_7,
        document_8,
        document_9,
        document_10,
    ]

    # Generate UUIDs for the documents
    uuids = [str(uuid4()) for _ in range(len(documents))]

    # Add documents to vector store
    print(f"\nAdding {len(documents)} documents to vector store...")
    successful_ids = vector_store.add_documents(documents=documents, ids=uuids)
    print(f"Successfully added {len(successful_ids)} documents")

    # Test similarity search
    print("\n=== Testing Similarity Search ===")
    results = vector_store.similarity_search(
        "LangChain provides abstractions to make working with LLMs easy", k=2
    )
    print(f"Found {len(results)} results:")
    for i, res in enumerate(results):
        print(f"{i+1}. {res.page_content} [{res.metadata}]")

    # Test similarity search with score
    print("\n=== Testing Similarity Search with Score ===")
    results = vector_store.similarity_search_with_score("Will it be hot tomorrow?", k=1)
    for res, score in results:
        print(f"* [SIM={score:.3f}] {res.page_content} [{res.metadata}]")

    # Test filtering (note: this would require custom filtering implementation)
    print("\n=== Testing Search for Tweets ===")
    tweet_results = vector_store.similarity_search(
        "What did I eat for breakfast?", k=4
    )
    print(f"Found {len(tweet_results)} results:")
    for res in tweet_results:
        if res.metadata.get("source") == "tweet":
            print(f"* {res.page_content} [{res.metadata}]")

    # Test deletion
    print(f"\n=== Testing Document Deletion ===")
    if successful_ids:
        last_id = successful_ids[-1]
        print(f"Deleting document with ID: {last_id}")
        success = vector_store.delete(ids=[last_id])
        if success:
            print("✅ Document deleted successfully")
        else:
            print("❌ Failed to delete document")

    # Verify final state
    print("\n=== Final Verification ===")
    vector_store.verify_data_insertion()
    vector_store.get_table_stats()

if __name__ == "__main__":
    test_vector_store()