"""Document chunking, embeddings, Chroma storage, and retrieval."""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from enterprise_knowledge_assistant.config import Settings
from enterprise_knowledge_assistant.demo_components import HashEmbeddings


class RAGService:
    """Build and query the local Chroma knowledge index."""

    def __init__(self, settings: Settings, demo_mode: bool = False):
        self.settings = settings
        self.demo_mode = demo_mode
        self.vector_store: Chroma | None = None

    def _embedding_model(self):
        if self.demo_mode:
            return HashEmbeddings()
        return OllamaEmbeddings(model=self.settings.embedding_model)

    def build_index(self, source_documents: dict[str, str]) -> int:
        """Chunk MCP-loaded documents and store their embeddings in Chroma."""

        documents = [
            Document(page_content=text, metadata={"source": filename})
            for filename, text in source_documents.items()
        ]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        chunks = splitter.split_documents(documents)

        # Reset only this application's collection. Removing the whole Chroma
        # directory can fail on Windows when OneDrive or antivirus holds a file.
        existing_store = Chroma(
            collection_name="enterprise_knowledge",
            embedding_function=self._embedding_model(),
            persist_directory=str(self.settings.chroma_dir),
        )
        try:
            existing_store.delete_collection()
        except ValueError:
            pass

        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self._embedding_model(),
            collection_name="enterprise_knowledge",
            persist_directory=str(self.settings.chroma_dir),
        )
        return len(chunks)

    def retrieve(self, question: str, k: int | None = None) -> list[Document]:
        """Return the most relevant knowledge chunks."""

        if self.vector_store is None:
            raise RuntimeError("The knowledge index has not been built.")
        return self.vector_store.similarity_search(
            question,
            k=k or self.settings.retrieval_k,
        )
