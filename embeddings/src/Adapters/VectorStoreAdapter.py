'''
Parent class for each of the four vector database adapters.
'''
class VectorStoreAdapter:
    def add_embedding(self, vector: list[float], text: str, metadata: dict):
        raise NotImplementedError("This method must be implemented by subclasses.")