from typing import List, Tuple
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LocalRAG:
    """Tiny TF-IDF retriever over a local glossary (no external API)."""

    def __init__(self, glossary_path: str | Path, ngram_range=(1, 2)):
        self.terms: List[str] = []
        self.passages: List[str] = []
        self.vectorizer = TfidfVectorizer(ngram_range=ngram_range, stop_words="english")
        self._fit(glossary_path)

    def _fit(self, path: str | Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        # data is list of {"term": "...", "definition": "..."}
        self.terms = [d["term"] for d in data]
        self.passages = [d["definition"] for d in data]
        self.doc_matrix = self.vectorizer.fit_transform(self.passages)

    def retrieve(self, query: str, k: int = 2) -> List[Tuple[str, str]]:
        if not query or not query.strip():
            return []
        q = self.vectorizer.transform([query])
        sims = cosine_similarity(q, self.doc_matrix)[0]
        idxs = sims.argsort()[::-1][:k]
        return [(self.terms[i], self.passages[i]) for i in idxs]

    def answer(self, query: str, k: int = 2) -> str:
        hits = self.retrieve(query, k=k)
        if not hits:
            return "Please ask a term-specific question, e.g., 'What is deductible?'"
        # Concatenate top passages
        return " ".join([h[1] for h in hits])
