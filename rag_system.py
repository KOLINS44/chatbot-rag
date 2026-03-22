"""
rag_system.py - система поиска по базе знаний (RAG)
Использует TF-IDF векторизацию и косинусное сходство для поиска
"""

import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class RAGSystem:
    """
    RAG (Retrieval-Augmented Generation) - система поиска релевантных
    фрагментов из базы знаний по тексту запроса.
    Использует TF-IDF векторизацию и косинусное сходство.
    """

    def __init__(self, kb_path="knowledge_base.txt"):
        self.chunks = []
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            max_features=5000,
        )
        self.tfidf_matrix = None
        self._load_knowledge_base(kb_path)

    def _load_knowledge_base(self, kb_path: str):
        """Загрузка и индексация базы знаний."""
        if not os.path.exists(kb_path):
            print(f"[RAG] Файл базы знаний не найден: {kb_path}")
            return

        with open(kb_path, "r", encoding="utf-8") as f:
            text = f.read()

        raw_chunks = [c.strip() for c in text.split("\n\n") if c.strip()]

        self.chunks = []
        for chunk in raw_chunks:
            if len(chunk) > 600:
                sentences = re.split(r"(?<=[.!?])\s+", chunk)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) < 600:
                        current += " " + sent
                    else:
                        if current.strip():
                            self.chunks.append(current.strip())
                        current = sent
                if current.strip():
                    self.chunks.append(current.strip())
            else:
                self.chunks.append(chunk)

        self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
        print(f"[RAG] База знаний загружена: {len(self.chunks)} фрагментов")

    def query(self, question: str, k: int = 3) -> str | None:
        if not self.chunks or self.tfidf_matrix is None:
            return None

        query_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = scores.argsort()[::-1][:k]

        results = [self.chunks[i] for i in top_indices if scores[i] > 0.01]
        if not results:
            return None

        return "\n\n".join(results)
