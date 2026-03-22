"""
rag_system.py - система поиска по базе знаний (RAG)
Использует sentence-transformers для векторизации текста и FAISS для поиска
"""

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


class RAGSystem:
    """
    RAG (Retrieval-Augmented Generation) - система поиска релевантных
    фрагментов из базы знаний по тексту запроса.
    """

    def __init__(self, kb_path="knowledge_base.txt"):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.vectorstore = None
        self._load_knowledge_base(kb_path)

    def _load_knowledge_base(self, kb_path: str):
        """Загрузка и индексация базы знаний."""
        if not os.path.exists(kb_path):
            print(f"[RAG] Файл базы знаний не найден: {kb_path}")
            return

        loader = TextLoader(kb_path, encoding="utf-8")
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "],
        )
        chunks = splitter.split_documents(documents)

        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        print(f"[RAG] База знаний загружена: {len(chunks)} фрагментов")

    def query(self, question: str, k: int = 3) -> str | None:
        """
        Поиск наиболее релевантных фрагментов по запросу.

        Args:
            question: текст запроса
            k: количество фрагментов для извлечения

        Returns:
            Объединённый текст найденных фрагментов или None
        """
        if not self.vectorstore:
            return None

        docs = self.vectorstore.similarity_search(question, k=k)
        if not docs:
            return None

        result = "\n\n".join([doc.page_content for doc in docs])
        return result
