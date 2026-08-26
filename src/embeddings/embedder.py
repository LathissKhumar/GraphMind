from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingCache:
    """Thread-safe LRU cache for embedding results."""

    def __init__(self, max_size: int = 500) -> None:
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def _make_key(self, text: str) -> str:
        """Hash long texts to save memory, use raw text for short ones."""
        if len(text) > 200:
            return "h:" + hashlib.sha256(text.encode()).hexdigest()[:16]
        return "r:" + text

    def get(self, text: str) -> Optional[list[float]]:
        key = self._make_key(text)
        with self._lock:
            if key in self._cache:
                self._hits += 1
                self._cache.move_to_end(key)
                return list(self._cache[key])  # return copy
            self._misses += 1
            return None

    def put(self, text: str, embedding: list[float]) -> None:
        key = self._make_key(text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = embedding
            else:
                self._cache[key] = embedding
                if len(self._cache) > self._max_size:
                    self._cache.popitem(last=False)

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "hit_rate": round(self._hits / max(1, total), 3),
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_size: int = 500):
        self.model_name: str = model_name
        self._model: Optional["SentenceTransformer"] = None
        self._dimension: Optional[int] = None
        self._cache = EmbeddingCache(max_size=cache_size)

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                test_embedding = self._model.encode("test")
                self._dimension = len(test_embedding)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required. Install: pip install sentence-transformers>=2.2.0"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load model {self.model_name}: {e}")

    def embed_text(self, text: str) -> list[float]:
        cached = self._cache.get(text)
        if cached is not None:
            return cached
        self._load_model()
        assert self._model is not None
        embedding = self._model.encode(text).tolist()
        self._cache.put(text, embedding)
        return embedding

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._load_model()
        assert self._model is not None

        results: list[Optional[list[float]]] = [None] * len(texts)
        misses: list[int] = []

        for i, text in enumerate(texts):
            cached = self._cache.get(text)
            if cached is not None:
                results[i] = cached
            else:
                misses.append(i)

        if misses:
            missed_texts = [texts[i] for i in misses]
            missed_embeddings = self._model.encode(missed_texts).tolist()
            for idx, embedding in zip(misses, missed_embeddings):
                results[idx] = embedding
                self._cache.put(texts[idx], embedding)

        return [r for r in results if r is not None]

    def dimension(self) -> int:
        if self._dimension is None:
            self._load_model()
        assert self._dimension is not None
        return self._dimension

    def cache_stats(self) -> dict:
        return self._cache.stats()

    def clear_cache(self) -> None:
        self._cache.clear()
