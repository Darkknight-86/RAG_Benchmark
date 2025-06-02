from .VectorStoreAdapter import VectorStoreAdapter

class CassandraAdapter(VectorStoreAdapter):
    def add_embedding(self, vector, text, metadata):
        pass