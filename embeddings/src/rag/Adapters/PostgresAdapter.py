from .VectorStoreAdapter import VectorStoreAdapter

class PostgresAdapter(VectorStoreAdapter):
    def add_embedding(self, vector, text, metadata):
        pass