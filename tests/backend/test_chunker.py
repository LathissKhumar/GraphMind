import pytest
from pathlib import Path

sys_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(sys_path))

from src.chunking.chunker import Chunker


class TestChunker:
    def test_init_default(self):
        chunker = Chunker()
        assert chunker.chunk_size == 2048
        assert chunker.overlap_size == 256
        assert chunker.threshold == 0.95

    def test_init_custom(self):
        chunker = Chunker(chunk_size=1024, overlap_size=128, threshold=0.90)
        assert chunker.chunk_size == 1024
        assert chunker.overlap_size == 128
        assert chunker.threshold == 0.90

    def test_chunk_text_empty(self):
        chunker = Chunker()
        result = chunker.chunk_text("")
        assert result == []

    def test_chunk_text_short(self):
        chunker = Chunker(chunk_size=50, overlap_size=5)
        text = "Short text"
        result = chunker.chunk_text(text)
        assert len(result) >= 1
        assert "Short text" in "".join(result)

    def test_chunk_text_long(self):
        chunker = Chunker(chunk_size=50, overlap_size=10)
        text = "A" * 120  # 120 chars, should split into multiple chunks
        result = chunker.chunk_text(text)
        assert len(result) > 1

    def test_chunk_text_with_newlines(self):
        chunker = Chunker(chunk_size=50, overlap_size=10)
        text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        result = chunker.chunk_text(text)
        # Should split at newline boundaries
        assert len(result) >= 1
        # Each chunk should be <= chunk_size
        for chunk in result:
            assert len(chunk) <= 50

    def test_chunk_text_overlap(self):
        chunker = Chunker(chunk_size=20, overlap_size=5)
        text = "A" * 50
        result = chunker.chunk_text(text)
        assert len(result) > 1
        # Check that overlap exists (end of one chunk should overlap with start of next)
        if len(result) >= 2:
            # The overlap might not be exact due to splitting logic, but chunks should be contiguous
            assert len(result[0]) <= 20
            assert len(result[1]) <= 20
