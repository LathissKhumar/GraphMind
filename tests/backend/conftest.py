import pytest
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def mock_codebase(tmp_path):
    (tmp_path / "main.py").write_text("""
def hello():
    return "hello"

class Foo:
    def bar(self):
        return "bar"
""")
    return tmp_path


# Expanded fixtures for Wave 1-5 testing
@pytest.fixture
def sample_code() -> str:
    return '''
import os
from typing import List

CONSTANT = 42

def add(a: int, b: int) -> int:
    """Return the sum of a and b"""
    return a + b

class Calculator:
    def __init__(self, values: List[int]):
        self.values = values

    def total(self) -> int:
        return sum(self.values)

def _helper(x):
    return x * 2
'''


@pytest.fixture
def sample_query_factoid() -> str:
    return "What does function add do?"


@pytest.fixture
def sample_query_relational() -> str:
    return "How are functions add and _helper related?"


@pytest.fixture
def sample_query_openended() -> str:
    return "Explain the authentication flow comprehensively"


@pytest.fixture
def mock_graph_nodes() -> List[Dict[str, Any]]:
    return [
        {"id": "n1", "type": "function", "name": "add", "loc": 3},
        {"id": "n2", "type": "class", "name": "Calculator", "loc": 8},
        {"id": "n3", "type": "variable", "name": "CONSTANT", "loc": 2},
    ]


@pytest.fixture
def mock_graph_edges() -> List[Dict[str, Any]]:
    return [
        {"source": "n1", "target": "n3", "type": "uses"},
        {"source": "n2", "target": "n1", "type": "calls"},
    ]


@pytest.fixture
def sample_answer_graph_only() -> str:
    return "GRAPH_ONLY: nodes=3 edges=2; add -> CONSTANT (uses); Calculator -> add (calls)"


@pytest.fixture
def sample_answer_graph_rag() -> str:
    return (
        "GRAPH_RAG: Based on graph nodes and retrieved docs: add sums two numbers; "
        "Calculator.total aggregates a list of ints using sum()."
    )


@pytest.fixture
def sample_answer_llm_full() -> str:
    return (
        "LLM_FULL: The function add(a, b) returns the arithmetic sum of its two arguments. "
        "Calculator.total returns the sum of the stored values. Authentication flow: ..."
    )


@pytest.fixture
def sample_ground_truth() -> Dict[str, str]:
    return {"question": "What does function add do?", "correct_answer": "Returns the sum of two numbers."}


@pytest.fixture
def mock_embedding_vector() -> List[float]:
    # deterministic 384-dim vector for tests
    return [float((i % 10) - 5) / 10.0 for i in range(384)]


@pytest.fixture
def sample_chunked_text() -> list:
    return [
        "def add(a, b): return a + b",
        "class Calculator: def total(self): return sum(self.values)",
        "CONSTANT = 42",
    ]


@pytest.fixture
def mock_judge_response():
    """Predefined judge response JSON string."""
    import json
    return json.dumps({
        "accuracy": 4,
        "completeness": 5,
        "relevance": 4,
        "conciseness": 5,
        "reasoning": "Accurate and complete answer"
    })
