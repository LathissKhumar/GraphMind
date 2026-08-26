from __future__ import annotations

import json
import os
import difflib
from typing import Optional, Dict


class GroundTruthStore:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or ".codegraphx/ground_truth.json"
        self.data: Dict[str, str] = {}
        if os.path.exists(self.data_path):
            self.load_json(self.data_path)

    def add(self, question: str, answer: str) -> None:
        self.data[question] = answer

    def get(self, question: str) -> Optional[str]:
        if question in self.data:
            return self.data[question]
        matches = difflib.get_close_matches(
            question, self.data.keys(), n=1, cutoff=0.6
        )
        if matches:
            return self.data[matches[0]]
        return None

    def load_json(self, path: str) -> None:
        if not os.path.exists(path):
            return
        with open(path, 'r') as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                self.data.update(loaded)

    def save_json(self, path: str) -> None:
        with open(path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def size(self) -> int:
        return len(self.data)
