import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from src.llm.client import LLMClient
from src.llm.prompts import build_graph_rag_prompt, build_llm_full_prompt

class TestLLMClient:
    def test_client_initialization(self):
        client = LLMClient()
        assert client is not None

    def test_client_has_default_models(self):
        client = LLMClient()
        assert hasattr(client, 'models')

    def test_client_has_timeout(self):
        client = LLMClient()
        assert hasattr(client, 'timeout')

class TestPromptTemplates:
    def test_build_graph_rag_prompt(self):
        prompt = build_graph_rag_prompt("What is X?", "context data")
        assert isinstance(prompt, str)
        assert "What is X?" in prompt

    def test_build_llm_full_prompt(self):
        prompt = build_llm_full_prompt("What is X?", "context data")
        assert isinstance(prompt, str)
        assert "What is X?" in prompt