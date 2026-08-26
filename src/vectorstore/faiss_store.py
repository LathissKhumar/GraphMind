from __future__ import annotations
from typing import Any, TYPE_CHECKING
import pickle
import os
import threading

if TYPE_CHECKING:
    import numpy as np

_global_embedder: Any = None
_embedder_lock = threading.Lock()

def _get_embedder():
    global _global_embedder
    with _embedder_lock:
        if _global_embedder is None:
            from src.embeddings.embedder import Embedder
            _global_embedder = Embedder()
        return _global_embedder


class FAISSStore:
    def __init__(self, dimension: int = 384, index_path: str | None = None):
        self.dimension = dimension
        self.index: Any = None
        self.texts: list[str] = []
        self.metadata: list[dict[str, Any]] = []  # type: ignore
        # Thread-safe write lock for FAISS index mutations
        self._write_lock = threading.Lock()
        # attempt to load existing index if provided, otherwise create one
        if index_path and os.path.exists(index_path):
            self.load(index_path)
        else:
            import faiss
            # create index eagerly so callers can use it without None checks
            self.index = faiss.IndexFlatIP(dimension)  # type: ignore
    
    def add(self, texts: list[str], metadata: list[dict[str, Any]] | None = None) -> None:
        if not texts:
            return
            
        embedder = _get_embedder()
        vectors = embedder.embed_texts(texts)
        
        import numpy as np
        import faiss
        vectors_np = np.asarray(vectors, dtype=np.float32)
        faiss.normalize_L2(vectors_np)
        
        with self._write_lock:
            # Extend texts/metadata BEFORE index.add to maintain invariant:
            # len(self.texts) >= self.index.ntotal at all times.
            # This prevents search() from reading out-of-bounds during concurrent writes.
            self.texts.extend(texts)
            if metadata is None:
                metadata = [{} for _ in texts]
            self.metadata.extend(metadata)
            self.index.add(vectors_np)
    
    def add_batch(
        self,
        texts: list[str],
        vectors: np.ndarray | None = None,
        metadata: list[dict[str, Any]] | None = None
    ) -> int:
        """High-throughput batch addition, accepts raw texts or pre-computed vectors.
        
        Args:
            texts: List of text strings to store (required)
            vectors: Optional pre-computed numpy array of embeddings (batch size x dimension).
                     If None, texts will be embedded via the shared embedder.
            metadata: Optional list of metadata dicts for each text.
        
        Returns:
            Number of items added to the index.
        """
        if not texts:
            return 0
        
        import numpy as np
        import faiss
        
        if vectors is None:
            embedder = _get_embedder()
            vectors = embedder.embed_texts(texts)
            vectors_np = np.asarray(vectors, dtype=np.float32)
        else:
            vectors_np = np.asarray(vectors, dtype=np.float32)
            if vectors_np.shape[0] != len(texts):
                raise ValueError(
                    f"Vector count ({vectors_np.shape[0]}) does not match text count ({len(texts)})"
                )
        
        # In-place normalization for FAISS IndexFlatIP (cosine similarity)
        faiss.normalize_L2(vectors_np)  # type: ignore
        added_count = vectors_np.shape[0]
        
        with self._write_lock:
            # texts/metadata first, then index.add — invariant: len(texts) >= ntotal
            self.texts.extend(texts)
            if metadata is None:
                metadata = [{} for _ in texts]
            self.metadata.extend(metadata)
            self.index.add(vectors_np)  # type: ignore
        
        return added_count
    
    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        if getattr(self.index, "ntotal", 0) == 0:  # type: ignore
            return []
            
        import numpy as np
        import faiss
        # Optimized: use asarray and reshape instead of wrapping in list
        query_np = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(query_np)  # type: ignore
        
        distances, indices = self.index.search(query_np, top_k)  # type: ignore
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                break
            results.append({
                'text': self.texts[idx],
                'metadata': self.metadata[idx],
                'score': float(distances[0][i])
            })
        return results
    
    def search_batch(
        self,
        query_embeddings: list[list[float]],
        top_k: int = 5
    ) -> list[list[dict[str, Any]]]:
        """Batch search for multiple query embeddings, returns list of result lists."""
        if getattr(self.index, "ntotal", 0) == 0:  # type: ignore
            return [[] for _ in query_embeddings]
        
        import numpy as np
        import faiss
        queries_np = np.asarray(query_embeddings, dtype=np.float32)
        if queries_np.ndim != 2 or queries_np.shape[1] != self.dimension:
            raise ValueError(
                f"Query embeddings must have shape (n_queries, {self.dimension}), "
                f"got {queries_np.shape}"
            )
        # Normalize all queries in-place
        faiss.normalize_L2(queries_np)  # type: ignore
        
        # FAISS search supports multiple queries natively
        distances, indices = self.index.search(queries_np, top_k)  # type: ignore
        
        # Process results per query
        batch_results = []
        for q_idx in range(indices.shape[0]):
            query_results = []
            for i, idx in enumerate(indices[q_idx]):
                if idx == -1:
                    break
                query_results.append({
                    'text': self.texts[idx],
                    'metadata': self.metadata[idx],
                    'score': float(distances[q_idx][i])
                })
            batch_results.append(query_results)
        return batch_results
    
    def get_stats(self) -> dict[str, Any]:
        """Return index statistics for monitoring."""
        return {
            "index_size": int(getattr(self.index, "ntotal", 0)),
            "dimension": self.dimension,
            "texts_count": len(self.texts)
        }
    
    def save(self, path: str) -> None:
        import faiss
        if self.index is not None:
            faiss.write_index(self.index, path)  # type: ignore
        
        meta_path = f"{path}.meta"
        with open(meta_path, 'wb') as f:
            pickle.dump({'texts': self.texts, 'metadata': self.metadata}, f)
    
    def load(self, path: str) -> None:
        import faiss
        self.index = faiss.read_index(path)  # type: ignore
        # type: ignore[attr-defined]
        self.dimension = getattr(self.index, "d", self.dimension)
        
        meta_path = f"{path}.meta"
        if os.path.exists(meta_path):
            with open(meta_path, 'rb') as f:
                meta = pickle.load(f)
            self.texts = meta['texts']
            self.metadata = meta['metadata']
    
    def size(self) -> int:
        return int(getattr(self.index, "ntotal", 0))
