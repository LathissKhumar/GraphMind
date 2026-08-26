import os
from pathlib import Path
from typing import Optional, Dict, List, Any

from src.router.token_counter import TokenCounter

_counter = TokenCounter()

def count_tokens(file_path: str) -> int:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return 0
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return 0
    return _counter.count_tokens(text)

def count_dataset_tokens(directory: str) -> int:
    total = 0
    skip_dirs = {".git", ".codegraphx", "__pycache__", "node_modules", "venv", ".venv", "env"}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for file in files:
            total += count_tokens(os.path.join(root, file))
    return total

def verify_2m_threshold(directory: Optional[str] = None) -> bool:
    if directory is None:
        directory = os.getcwd()
    total = count_dataset_tokens(directory)
    return total > 2_000_000

def get_token_report(directory: Optional[str] = None) -> Dict[str, Any]:
    if directory is None:
        directory = os.getcwd()
    report: Dict[str, Any] = {
        "total_tokens": 0,
        "by_file_type": {},
        "top_files": [],
        "token_density": 0.0,
    }
    skip_dirs = {".git", ".codegraphx", "__pycache__", "node_modules", "venv", ".venv", "env"}
    file_entries: List[Dict[str, Any]] = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for file in files:
            file_path = os.path.join(root, file)
            ext = Path(file_path).suffix.lower() or "unknown"
            tokens = count_tokens(file_path)
            if tokens == 0:
                continue
            report["total_tokens"] = report["total_tokens"] + tokens
            current = report["by_file_type"].get(ext, 0)
            report["by_file_type"][ext] = current + tokens
            file_entries.append({"path": file_path, "tokens": tokens, "type": ext})
    file_entries.sort(key=lambda x: x["tokens"], reverse=True)
    report["top_files"] = file_entries[:50]
    if file_entries:
        report["token_density"] = report["total_tokens"] / len(file_entries)
    return report
