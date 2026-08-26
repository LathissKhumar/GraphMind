import pytest
from pathlib import Path

sys_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(sys_path))

from src.router.zero_token import ZeroTokenAnswerGenerator


class TestZeroTokenAnswerGenerator:
    def test_answer_list_empty(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_list([], label="functions")
        assert "couldn't find any functions" in result["answer"]
        assert result["needs_rag"] is True

    def test_answer_list_single(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_list(["parse_file"], label="functions")
        assert "Found 1 function: parse_file." in result["answer"]
        assert result["needs_rag"] is False

    def test_answer_list_multiple(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_list(["parse_file", "load_repo"], label="functions")
        assert "Found 2 functions" in result["answer"]
        assert "parse_file" in result["answer"]
        assert "load_repo" in result["answer"]
        assert result["needs_rag"] is False

    def test_answer_list_label_plural(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_list(["item1", "item2"], label="items")
        assert "Found 2 items" in result["answer"]

    def test_answer_relationship_empty(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_relationship("function", "calls", [])
        assert "couldn't determine" in result["answer"]
        assert result["needs_rag"] is True

    def test_answer_relationship_single(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_relationship("main", "calls", ["helper"])
        assert "main calls helper." in result["answer"]
        assert result["needs_rag"] is False

    def test_answer_relationship_multiple(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_relationship("main", "calls", ["f1", "f2", "f3"])
        assert "main calls f1, f2, f3." in result["answer"]
        assert result["needs_rag"] is False

    def test_answer_existence_true(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_existence("parse_file", True)
        assert "Yes" in result["answer"]
        assert "parse_file exists" in result["answer"]
        assert result["needs_rag"] is False

    def test_answer_existence_false(self):
        gen = ZeroTokenAnswerGenerator()
        result = gen.answer_existence("unknown_func", False)
        assert "couldn't confirm" in result["answer"]
        assert result["needs_rag"] is True
