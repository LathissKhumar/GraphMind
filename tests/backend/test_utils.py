from pathlib import Path
import tempfile
import shutil
import json
import random
from typing import Dict, Any, List


def create_temp_codebase(files: Dict[str, str]) -> Path:
    """Create a temporary directory with the given files.

    files: mapping of relative path -> content
    Returns Path to tempdir
    """
    tmp = Path(tempfile.mkdtemp(prefix="codebase_"))
    for rel, content in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp


def create_mock_llm_response(text: str = "Test response") -> Dict[str, Any]:
    return {"id": "mock-1", "object": "text_completion", "text": text}


def create_mock_embedding(dim: int = 384) -> List[float]:
    random.seed(0)
    return [random.random() for _ in range(dim)]


def validate_query_response(response: Dict[str, Any]) -> bool:
    # basic shape validation used by tests
    if not isinstance(response, dict):
        return False
    if "answer" not in response:
        return False
    if "source" in response and not isinstance(response["source"], str):
        return False
    return True


def calculate_token_estimate(text: str) -> int:
    # very rough: 4 chars per token
    if not text:
        return 0
    return max(1, len(text) // 4)


def _cleanup_temp(path: Path) -> None:
    try:
        shutil.rmtree(path)
    except Exception:
        pass
