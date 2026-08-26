from __future__ import annotations

from typing import Optional, Dict, Any, List

from src.evaluation.judge import LLMJudge
from src.evaluation.ground_truth import GroundTruthStore
from src.evaluation.semantic_metrics import SemanticMetrics
from src.evaluation.bertscore_evaluator import BERTScoreEvaluator
from src.evaluation.rescaler import rescale_bertscore_f1, score_to_label


class PipelineEvaluator:
    def __init__(self, judge: Optional[LLMJudge] = None, ground_truth: Optional[GroundTruthStore] = None, semantic_metrics: Optional[SemanticMetrics] = None):
        self.judge = judge or LLMJudge()
        self.ground_truth = ground_truth or GroundTruthStore()
        self.semantic_metrics = semantic_metrics or SemanticMetrics()

    def evaluate_query(self, question: str, answer: str, tier: str) -> Dict[str, Any]:
        """Evaluate a single query result."""
        ground_truth = self.ground_truth.get(question)
        if not ground_truth:
            return {
                "question": question,
                "answer": answer,
                "tier": tier,
                "error": "No ground truth found for question",
                "scores": None,
                "pass": False
            }

        scores = self.judge.evaluate(question, ground_truth, answer)
        passed = self.judge.is_pass(scores)
        return {
            "question": question,
            "answer": answer,
            "tier": tier,
            "ground_truth": ground_truth,
            "scores": scores,
            "pass": passed
        }

    def evaluate_pipeline(self, queries: List[Dict], pipeline_name: str) -> Dict[str, Any]:
        """Evaluate all queries for a single pipeline."""
        per_query = []
        for query in queries:
            question = query.get("question")
            answer = query.get("answer")
            if not question or answer is None:
                per_query.append({
                    "error": "Missing question or answer in query",
                    "question": question,
                    "answer": answer,
                    "scores": None,
                    "pass": False
                })
                continue

            result = self.evaluate_query(question, answer, pipeline_name)
            per_query.append(result)

        # Calculate aggregate stats
        total = len(per_query)
        pass_count = sum(1 for r in per_query if r.get("pass", False) and not r.get("error"))
        score_sums = {"accuracy": 0, "completeness": 0, "relevance": 0, "conciseness": 0}
        valid_results = [r for r in per_query if r.get("scores")]

        for r in valid_results:
            scores = r["scores"]
            for key in score_sums:
                score_sums[key] += scores[key]

        avg_scores = {}
        if valid_results:
            for key in score_sums:
                avg_scores[key] = score_sums[key] / len(valid_results)

        pass_rate = pass_count / total if total > 0 else 0.0

        return {
            pipeline_name: {
                "pass_rate": pass_rate,
                "avg_scores": avg_scores,
                "total_evaluated": total,
                "pass_count": pass_count,
                "per_query_results": per_query
            }
        }

    def evaluate_semantic(self, candidates: List[str], references: List[str]) -> List[Dict[str, Any]]:
        return self.semantic_metrics.evaluate_batch(candidates, references)

    def compute_bert_score(self, candidate: str, reference: str) -> Dict[str, Any]:
        evaluator = BERTScoreEvaluator()
        raw_f1 = evaluator.compute_single(candidate, reference)
        rescaled = rescale_bertscore_f1(raw_f1)
        return {
            'raw_f1': raw_f1,
            'rescaled_score': rescaled,
            'label': score_to_label(rescaled)
        }

    def compare_pipelines(self, evaluations: Dict[str, Any]) -> Dict[str, Any]:
        comparison = {
            "pipelines": {},
            "best_pipeline": None,
            "highest_pass_rate": 0.0
        }

        for pipeline, stats in evaluations.items():
            pipeline_summary = {
                "pass_rate": stats.get("pass_rate", 0.0),
                "avg_scores": stats.get("avg_scores", {}),
                "total_evaluated": stats.get("total_evaluated", 0)
            }
            comparison["pipelines"][pipeline] = pipeline_summary

            if pipeline_summary["pass_rate"] > comparison["highest_pass_rate"]:
                comparison["highest_pass_rate"] = pipeline_summary["pass_rate"]
                comparison["best_pipeline"] = pipeline

        return comparison
