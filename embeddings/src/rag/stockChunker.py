from langchain_core.documents import Document

class StockChunker:
    def chunk(self, text_list: list[str]) -> list[Document]:
        return [Document(page_content=text.strip()) for text in text_list if text.strip()]