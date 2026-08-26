import pytest
from pathlib import Path
import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.vectorstore.faiss_store import FAISSStore


class TestFAISSStore:
    def test_init_default(self):
        store = FAISSStore()
        assert store.dimension == 384
        assert store.index is not None
        assert store.size() == 0

    def test_init_custom_dimension(self):
        store = FAISSStore(dimension=128)
        assert store.dimension == 128

    def test_init_with_nonexistent_path(self, tmp_path):
        path = str(tmp_path / "nonexistent" / "index.bin")
        store = FAISSStore(index_path=path)
        assert store.size() == 0

    def test_add_single_text(self):
        store = FAISSStore()
        store.add(["test text"])
        assert store.size() == 1
        assert len(store.texts) == 1
        assert len(store.metadata) == 1

    def test_add_multiple_texts(self):
        store = FAISSStore()
        texts = ["text one", "text two", "text three"]
        store.add(texts)
        assert store.size() == 3
        assert len(store.texts) == 3

    def test_add_with_metadata(self):
        store = FAISSStore()
        texts = ["text one"]
        metadata = [{"source": "test.py"}]
        store.add(texts, metadata)
        assert store.metadata[0]["source"] == "test.py"

    def test_add_empty_list(self):
        store = FAISSStore()
        store.add([])
        assert store.size() == 0

    def test_add_default_metadata(self):
        store = FAISSStore()
        store.add(["text"])
        assert store.metadata[0] == {}

    def test_search(self):
        store = FAISSStore()
        store.add(["text one", "text two"])
        query_emb = [0.1] * 384
        results = store.search(query_emb, top_k=2)
        assert len(results) <= 2
        if results:
            assert "text" in results[0]
            assert "score" in results[0]

    def test_search_empty_store(self):
        store = FAISSStore()
        query_emb = [0.1] * 384
        results = store.search(query_emb, top_k=5)
        assert results == []

    def test_search_top_k(self):
        store = FAISSStore()
        store.add(["text one", "text two", "text three"])
        query_emb = [0.1] * 384
        results = store.search(query_emb, top_k=2)
        assert len(results) <= 2

    def test_search_returns_metadata(self):
        store = FAISSStore()
        store.add(["test"], [{"source": "file.py"}])
        query_emb = [0.1] * 384
        results = store.search(query_emb, top_k=1)
        if results:
            assert "metadata" in results[0]
            assert results[0]["metadata"]["source"] == "file.py"

    def test_save_and_load(self, tmp_path):
        store = FAISSStore()
        store.add(["text one", "text two"])
        path = str(tmp_path / "index.bin")
        store.save(path)
        assert Path(path).exists()
        assert Path(path + ".meta").exists()

    def test_load_existing(self, tmp_path):
        store = FAISSStore()
        store.add(["text one", "text two"])
        path = str(tmp_path / "index.bin")
        store.save(path)
        new_store = FAISSStore(index_path=path)
        assert new_store.size() == 2
        assert len(new_store.texts) == 2

    def test_size_empty(self):
        store = FAISSStore()
        assert store.size() == 0

    def test_size_after_add(self):
        store = FAISSStore()
        store.add(["text"])
        assert store.size() == 1
