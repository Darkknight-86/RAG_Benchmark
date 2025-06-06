#!/usr/bin/env python3
"""
Simple script to download the sentence transformer model
"""

import os
from sentence_transformers import SentenceTransformer

def download_model():
    print("Downloading sentence-transformers/all-MiniLM-L6-v2...")
    print("This may take a few minutes on first download...")

    try:
        # This will download and cache the model
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✅ Model downloaded successfully!")

        # Test the model
        test_text = ["Hello world", "This is a test"]
        embeddings = model.encode(test_text)
        print(f"✅ Model test successful! Generated embeddings with shape: {embeddings.shape}")

    except Exception as e:
        print(f"❌ Download failed: {e}")
        print("\nTrying alternative approach...")

        # Alternative: try with explicit cache directory
        cache_dir = os.path.expanduser("~/.cache/sentence_transformers")
        os.makedirs(cache_dir, exist_ok=True)

        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder=cache_dir)
        print("✅ Model downloaded with explicit cache!")

if __name__ == "__main__":
    download_model()