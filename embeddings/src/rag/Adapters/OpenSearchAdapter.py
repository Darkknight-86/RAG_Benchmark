from .VectorStoreAdapter import VectorStoreAdapter

class OpenSearchAdapter(VectorStoreAdapter):
    def add_embedding(self, vector, text, metadata):
        pass