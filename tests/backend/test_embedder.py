import pytest
from pathlib import Path
import numpy as np
import sys
from unittest.mock import MagicMock, patch
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.embeddings.embedder import Embedder


class TestEmbedder:
    def test_init_default(self):
        embedder = Embedder()
        assert embedder.model_name == "all-MiniLM-L6-v2"
        assert embedder._model is None
        assert embedder._dimension is None

    def test_init_custom_model(self):
        embedder = Embedder(model_name="custom-model")
        assert embedder.model_name == "custom-model"

    def test_embed_text(self):
        embedder = Embedder()
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        embedder._model = mock_model
        result = embedder.embed_text("test text")
        assert isinstance(result, list)
        assert len(result) == 3
        mock_model.encode.assert_called_once_with("test text")

    def test_embed_texts(self):
        embedder = Embedder()
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        embedder._model = mock_model
        result = embedder.embed_texts(["text1", "text2"])
        assert isinstance(result, list)
        assert len(result) == 2
        assert len(result[0]) == 2
        mock_model.encode.assert_called_once_with(["text1", "text2"])

    def test_dimension(self):
        embedder = Embedder()
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        embedder._model = mock_model
        embedder._dimension = 3
        dim = embedder.dimension()
        assert dim == 3
        assert embedder._dimension == 3

    def test_embed_text_no_sentence_transformers(self):
        with patch('builtins.__import__', side_effect=ImportError("No module")):
            embedder = Embedder()
            with pytest.raises(ImportError, match="sentence-transformers"):
                embedder.embed_text("test")

    def test_embed_text_calls_load_model(self):
        embedder = Embedder()
        embedder._model = None
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1])
        with patch.object(Embedder, '_load_model') as mock_load:
            embedder._model = mock_model
            embedder.embed_text("test")
            mock_load.assert_called_once()

    def test_embed_texts_calls_load_model(self):
        embedder = Embedder()
        embedder._model = None
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1]])
        with patch.object(Embedder, '_load_model') as mock_load:
            embedder._model = mock_model
            embedder.embed_texts(["test"])
            mock_load.assert_called_once()
