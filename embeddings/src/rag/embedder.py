from sentence_transformers import SentenceTransformer

class SpecterEmbedder:
    """
        Wrapper for allenai/specter2_base embedding model using sentence-transformers.

        This embedder is optimized for scientific document chunks, returning 768-dimensional
        dense vectors suitable for semantic search and retrieval.
    """

    def __init__(self, model_name="allenai/specter2_base", normalize=True):
        """
            Initialize the embedder with the given model.

            Args:
                model_name (str): Hugging Face model name.
                normalize (bool): Whether to normalize embeddings (cos similarity).
        """

        self.model = SentenceTransformer(model_name)
        self.normalize = normalize

    def embed(self, texts):
        """
            Embed a list of texts.

            Args:
                texts (List[str]): List of document chunks or queries.

            Returns:
                List[List[float]]: List of 768-dimensional embedding vectors.
        """

        return self.model.encode(texts, convert_to_tensor=False, normalize_embeddings=self.normalize)