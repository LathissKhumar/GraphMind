import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from src.evaluation.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_PROMPT_TEMPLATE
from src.llm.github_models_client import GitHubModelsClient

logger = logging.getLogger(__name__)


class LLMJudge:
    """LLM-as-a-Judge evaluator using GitHub Models (free tier)."""

    def __init__(self, model: str = "openai/gpt-4o-mini") -> None:
        self.model = model
        self.client = GitHubModelsClient()

    def evaluate(self, question: str, ground_truth: str, candidate_answer: str) -> Dict[str, Any]:
        """Evaluate a single answer against ground truth.

        Args:
            question: The original question
            ground_truth: The correct answer
            candidate_answer: The answer to evaluate

        Returns:
            Dict with accuracy, completeness, relevance, conciseness scores and reasoning
        """
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            question=question,
            ground_truth=ground_truth,
            candidate_answer=candidate_answer
        )

        try:
            response = self.client.generate(prompt, JUDGE_SYSTEM_PROMPT, model=self.model)

            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                scores = json.loads(json_str)

                required_keys = {"accuracy", "completeness", "relevance", "conciseness", "reasoning"}
                if not required_keys.issubset(scores.keys()):
                    missing = required_keys - scores.keys()
                    logger.warning(f"Missing keys in judge response: {missing}")
                    return self._get_default_scores()

                for key in ["accuracy", "completeness", "relevance", "conciseness"]:
                    if isinstance(scores[key], str):
                        try:
                            scores[key] = int(scores[key])
                        except ValueError:
                            scores[key] = 3
                    elif not isinstance(scores[key], int):
                        scores[key] = 3

                return scores
            else:
                logger.warning("No JSON found in judge response")
                return self._get_default_scores()

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse judge response JSON: {e}")
            return self._get_default_scores()
        except Exception as e:
            logger.error(f"Error in judge evaluation: {e}")
            return self._get_default_scores()

    def is_pass(self, scores: Dict[str, Any], threshold: float = 3.0) -> bool:
        """Determine if scores meet the pass threshold.

        Args:
            scores: Dictionary with accuracy, completeness, relevance, conciseness scores
            threshold: Minimum average score to pass

        Returns:
            True if average score >= threshold
        """
        try:
            numeric_scores = [
                scores["accuracy"],
                scores["completeness"],
                scores["relevance"],
                scores["conciseness"]
            ]
            avg_score = sum(numeric_scores) / len(numeric_scores)
            return avg_score >= threshold
        except (KeyError, TypeError):
            return False

    def batch_evaluate(self, evaluations: List[Dict[str, Any]], max_workers: int = 4) -> Dict[str, Any]:
        """Evaluate multiple queries in parallel and return aggregate statistics.

        Args:
            evaluations: List of dicts with question, ground_truth, candidate_answer
            max_workers: Max parallel LLM calls (default 4)

        Returns:
            Dict with pass_rate, avg_scores, and per_result breakdown
        """
        results: list[Dict[str, Any]] = []
        total_passed = 0

        def _evaluate_one(item: Dict[str, Any]) -> Dict[str, Any]:
            scores = self.evaluate(
                item["question"],
                item["ground_truth"],
                item["candidate_answer"]
            )
            return {
                "question": item["question"],
                "scores": scores,
                "passed": self.is_pass(scores)
            }

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_evaluate_one, item): item for item in evaluations}
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        total_passed = sum(1 for r in results if r.get("passed", False))
        pass_rate = total_passed / len(evaluations) if evaluations else 0.0

        avg_scores = {
            "accuracy": 0.0,
            "completeness": 0.0,
            "relevance": 0.0,
            "conciseness": 0.0
        }

        if results:
            for result in results:
                scores = result["scores"]
                avg_scores["accuracy"] += scores["accuracy"]
                avg_scores["completeness"] += scores["completeness"]
                avg_scores["relevance"] += scores["relevance"]
                avg_scores["conciseness"] += scores["conciseness"]

            for key in avg_scores:
                avg_scores[key] /= len(results)

        return {
            "pass_rate": pass_rate,
            "avg_scores": avg_scores,
            "total_evaluated": len(evaluations),
            "per_result": results
        }

    def _get_default_scores(self) -> Dict[str, Any]:
        """Return default scores when judge fails to respond properly."""
        return {
            "accuracy": 3,
            "completeness": 3,
            "relevance": 3,
            "conciseness": 3,
            "reasoning": "Failed to parse judge response - using default scores"
        }
