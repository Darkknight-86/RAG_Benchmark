from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from transformers import AutoTokenizer

class SpecterChunker:
    """
        Hybrid chunker for scientific documents using both character-aware and token-aware strategies.

        This class first splits documents using LangChain's RecursiveCharacterTextSplitter
        to preserve natural boundaries (e.g., paragraphs), then ensures each chunk fits within
        the token limits of the embedding model (e.g., specter2_base's 512-token max).

        Attributes:
            chunk_size (int): Max number of characters per chunk (for initial split).
            chunk_overlap (int): Number of characters to overlap between chunks.
            max_tokens (int): Token limit per chunk (based on the embedding model's capacity).
            tokenizer_model (str): The Hugging Face model name to use for tokenization.
    """

    def __init__(self,
                 chunk_size=1000,
                 chunk_overlap=200,
                 max_tokens=512,
                 tokenizer_model="allenai/specter2_base"
    ):
        """
            Initialize the chunker with character-level and token-level constraints.

            Args:
                chunk_size (int): Initial chunk size in characters.
                chunk_overlap (int): Overlap between character-based chunks.
                max_tokens (int): Max token count allowed per chunk.
                tokenizer_model (str): Tokenizer model name (must be Hugging Face-compatible).
        """

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.max_tokens = max_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_model)

    def chunk(self, documents):
        """
            Split and filter documents into LangChain-compatible Document chunks.

            Args:
                documents (List[str]): A list of raw document strings to be chunked.
            Returns:
                List[Document]: A list of LangChain Document objects, each under the token limit.
        """

        chunks = []

        for document in documents:
            initial_chunks = self.splitter.create_documents([document])

            for chunk in initial_chunks:
                tokens = self.tokenizer.encode(chunk.page_content, add_special_tokens=False)

                if len(tokens) <= self.max_tokens:
                    chunks.append(chunk)
                else:
                    trimmed_tokens = tokens[:self.max_tokens]
                    trimmed_text = self.tokenizer.decode(trimmed_tokens)
                    chunks.append(Document(page_content=trimmed_text, metadata=chunk.metadata))

        return chunks


