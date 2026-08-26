from __future__ import annotations

from typing import Any, Dict, List


class ZeroTokenAnswerGenerator:
    def answer_list(self, items: List[str], label: str = "items") -> Dict[str, Any]:
        if not items:
            return {
                "answer": f"I couldn't find any {label} in the graph.",
                "needs_rag": True,
            }
        if len(items) == 1:
            return {
                "answer": f"Found 1 {label[:-1] if label.endswith('s') else label}: {items[0]}.",
                "needs_rag": False,
            }
        joined = ", ".join(items)
        return {
            "answer": f"Found {len(items)} {label}: {joined}.",
            "needs_rag": False,
        }

    def answer_relationship(self, subject: str, relation: str, targets: List[str]) -> Dict[str, Any]:
        if not targets:
            return {
                "answer": f"I couldn't determine what {subject} {relation} from the graph.",
                "needs_rag": True,
            }
        if len(targets) == 1:
            return {
                "answer": f"{subject} {relation} {targets[0]}.",
                "needs_rag": False,
            }
        return {
            "answer": f"{subject} {relation} {', '.join(targets)}.",
            "needs_rag": False,
        }

    def answer_existence(self, entity: str, exists: bool) -> Dict[str, Any]:
        if exists:
            return {
                "answer": f"Yes — {entity} exists in the graph.",
                "needs_rag": False,
            }
        return {
            "answer": f"I couldn't confirm whether {entity} exists from the graph alone.",
            "needs_rag": True,
        }


if __name__ == "__main__":
    generator = ZeroTokenAnswerGenerator()
    print(generator.answer_list(["parse_file", "load_repo"], label="functions"))
