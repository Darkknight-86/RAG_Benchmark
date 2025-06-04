from langchain.docstore.document import Document
from nltk.tokenize import sent_tokenize
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
                 max_tokens=512,
                 token_overlap=50,
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

        self.max_tokens = max_tokens
        self.token_overlap = token_overlap
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_model)

    def chunk(self, documents):
        """
            Split and filter documents into LangChain-compatible Document chunks.

            Args:
                documents (List[str]): A list of raw document strings to be chunked.
            Returns:
                List[Document]: A list of LangChain Document objects, each under the token limit.
        """

        # Holds all final chunked Document objects
        chunks = []

        for doc_index, document in enumerate(documents):

            print(f"\n⏳ Processing document {doc_index} with {len(document)} characters")

            # Split document into sentences
            sentences = sent_tokenize(document)
            print(f"🟢 Tokenized into {len(sentences)} sentences")

            # Tokenize each sentence once and cache token lengths
            sentence_token_pairs = [
                (sentence,
                 len(self.tokenizer.encode(sentence, add_special_tokens=False))
                 ) for sentence in sentences
            ]
            print(f"🔢 Token lengths calculated for {len(sentence_token_pairs)} sentences")

            # Pointer to current sentence
            i = 0
            # Tracks chunks created
            chunk_index = 0

            while i < len(sentence_token_pairs):
                current_chunk = [] # Holds the sentences in the current chunk
                current_tokens = 0 # Tracks number of tokens in the current chunk
                start_index = i # Mark the start index of this chunk

                # Accumulate sentences into the current chunk until the max token limit is reached
                while i < len(sentence_token_pairs):
                    sentence, token_len = sentence_token_pairs[i]
                    if current_tokens + token_len > self.max_tokens:
                        break
                    current_chunk.append(sentence)
                    current_tokens += token_len
                    i += 1

                # If we have a valid chunk, package it into a Document with metadata
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    metadata = {
                        "source_index": doc_index,
                        "chunk_index": chunk_index,
                        "sentence_start_index": start_index,
                        "sentence_end_index": i - 1
                    }

                    chunks.append(Document(page_content=chunk_text, metadata=metadata))
                    print(f"✅ Created chunk {chunk_index} with {current_tokens} tokens")
                    chunk_index += 1

                    # Apply token-level overlap only if we actually advanced
                    if self.token_overlap > 0 and i < len(sentence_token_pairs):
                        if i > start_index:
                            # We moved forward, so it's safe to rewind
                            overlap_token_sum = 0
                            j = i - 1
                            while j >= 0 and overlap_token_sum < self.token_overlap:
                                overlap_token_sum += sentence_token_pairs[j][1]
                                j -= 1
                            new_i = max(j + 1, start_index + 1)
                            if new_i >= i:
                                i += 1  # Safety: ensure we move forward
                            else:
                                i = new_i
                        else:
                            # We didn’t advance (sentence too large), so force a skip
                            i += 1
        print(f"\n✅ Finished chunking. Total chunks created: {len(chunks)}")
        return chunks