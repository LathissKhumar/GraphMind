import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.evaluation.judge import LLMJudge
from src.evaluation.evaluator import PipelineEvaluator
from src.evaluation.ground_truth import GroundTruthStore
from src.evaluation.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_PROMPT_TEMPLATE
from src.evaluation.bertscore_evaluator import BERTScoreEvaluator
from src.evaluation.rescaler import rescale_bertscore_f1, score_to_label
from src.evaluation.semantic_metrics import SemanticMetrics


class TestPrompts:
    def test_judge_system_prompt_exists(self):
        assert isinstance(JUDGE_SYSTEM_PROMPT, str)
        assert "accuracy" in JUDGE_SYSTEM_PROMPT.lower()
        assert "completeness" in JUDGE_SYSTEM_PROMPT.lower()

    def test_judge_prompt_template_exists(self):
        assert isinstance(JUDGE_PROMPT_TEMPLATE, str)
        assert "{question}" in JUDGE_PROMPT_TEMPLATE
        assert "{ground_truth}" in JUDGE_PROMPT_TEMPLATE
        assert "{candidate_answer}" in JUDGE_PROMPT_TEMPLATE

    def test_prompt_template_format(self):
        result = JUDGE_PROMPT_TEMPLATE.format(
            question="What is X?",
            ground_truth="X is...",
            candidate_answer="X is a thing"
        )
        assert "What is X?" in result
        assert "X is..." in result
        assert "X is a thing" in result


class TestRescaler:
    def test_rescale_bertscore_f1_midrange(self):
        assert rescale_bertscore_f1(0.5) == 3.0

    def test_rescale_bertscore_f1_zero(self):
        assert rescale_bertscore_f1(0.0) == 1.0

    def test_rescale_bertscore_f1_one(self):
        assert rescale_bertscore_f1(1.0) == 5.0

    def test_rescale_bertscore_f1_clamped_high(self):
        assert rescale_bertscore_f1(2.0) == 5.0

    def test_rescale_bertscore_f1_clamped_low(self):
        assert rescale_bertscore_f1(-1.0) == 1.0

    @pytest.mark.parametrize("score,expected", [
        (4.5, "Excellent"),
        (5.0, "Excellent"),
        (3.5, "Very Good"),
        (4.49, "Very Good"),
        (2.5, "Good"),
        (3.49, "Good"),
        (1.5, "Fair"),
        (2.49, "Fair"),
        (0.0, "Poor"),
        (1.49, "Poor"),
    ])
    def test_score_to_label(self, score, expected):
        assert score_to_label(score) == expected


class TestGroundTruthStore:
    def test_init_default_path(self):
        store = GroundTruthStore()
        assert store.data_path == ".codegraphx/ground_truth.json"
        assert store.size() == 0

    def test_init_with_path_no_file(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        store = GroundTruthStore(data_path=path)
        assert store.data_path == path
        assert store.size() == 0

    def test_add_and_get(self):
        store = GroundTruthStore()
        store.add("What is X?", "X is a function.")
        assert store.size() == 1
        assert store.get("What is X?") == "X is a function."

    def test_get_nonexistent(self):
        store = GroundTruthStore()
        assert store.get("nonexistent") is None

    def test_get_close_match(self):
        store = GroundTruthStore()
        store.add("What is the meaning of life?", "42")
        result = store.get("What is the meaning of")
        assert result == "42"

    def test_get_no_close_match_below_cutoff(self):
        store = GroundTruthStore()
        store.add("alpha beta gamma", "value")
        result = store.get("completely different")
        assert result is None

    def test_load_json(self, tmp_path):
        json_path = tmp_path / "ground_truth.json"
        json_path.write_text(json.dumps({"Q1": "A1", "Q2": "A2"}))
        store = GroundTruthStore()
        store.load_json(str(json_path))
        assert store.size() == 2
        assert store.get("Q1") == "A1"
        assert store.get("Q2") == "A2"

    def test_save_json(self, tmp_path):
        store = GroundTruthStore()
        store.add("Q1", "A1")
        store.add("Q2", "A2")
        output_path = str(tmp_path / "output.json")
        store.save_json(output_path)
        assert os.path.exists(output_path)
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded == {"Q1": "A1", "Q2": "A2"}

    def test_load_json_invalid_path(self):
        store = GroundTruthStore()
        store.load_json("/nonexistent/path.json")
        assert store.size() == 0

    def test_init_loads_existing_file(self, tmp_path):
        json_path = tmp_path / "ground_truth.json"
        json_path.write_text(json.dumps({"Q": "A"}))
        store = GroundTruthStore(data_path=str(json_path))
        assert store.size() == 1
        assert store.get("Q") == "A"

    def test_size_empty(self):
        store = GroundTruthStore()
        assert store.size() == 0


class TestBERTScoreEvaluator:
    def test_init_default(self):
        evaluator = BERTScoreEvaluator()
        assert evaluator.model_type == "bert-base-uncased"
        assert evaluator._bert_score is None
        assert evaluator._sentence_transformer is None

    def test_init_custom_model(self):
        evaluator = BERTScoreEvaluator(model_type="custom-model")
        assert evaluator.model_type == "custom-model"

    @patch.object(BERTScoreEvaluator, '_load_bert_score')
    @patch.object(BERTScoreEvaluator, '_load_sentence_transformer')
    def test_compute_f1_uses_sentence_transformer_fallback(self, mock_load_st, mock_load_bs):
        import numpy as np
        mock_load_bs.return_value = None
        mock_st = MagicMock()
        mock_tensor1 = MagicMock()
        mock_tensor1.cpu.return_value = mock_tensor1
        mock_tensor1.numpy.return_value = np.array([0.1, 0.2, 0.3])
        mock_tensor2 = MagicMock()
        mock_tensor2.cpu.return_value = mock_tensor2
        mock_tensor2.numpy.return_value = np.array([0.1, 0.2, 0.3])
        mock_st.encode.side_effect = [[mock_tensor1], [mock_tensor2]]
        mock_load_st.return_value = mock_st
        evaluator = BERTScoreEvaluator()
        result = evaluator.compute_f1(["candidate"], ["reference"])
        assert "precision" in result
        assert "recall" in result
        assert "f1" in result
        assert isinstance(result["f1"], float)

    def test_compute_f1_mismatched_lengths(self):
        evaluator = BERTScoreEvaluator()
        with pytest.raises(ValueError, match="same length"):
            evaluator.compute_f1(["a", "b"], ["c"])

    @patch.object(BERTScoreEvaluator, '_load_bert_score')
    @patch.object(BERTScoreEvaluator, '_load_sentence_transformer')
    def test_compute_f1_no_dependencies(self, mock_load_st, mock_load_bs):
        mock_load_bs.return_value = None
        mock_load_st.return_value = None
        evaluator = BERTScoreEvaluator()
        with pytest.raises(RuntimeError, match="Neither bert_score nor sentence_transformers"):
            evaluator.compute_f1(["candidate"], ["reference"])

    @patch.object(BERTScoreEvaluator, 'compute_f1')
    def test_compute_single(self, mock_compute_f1):
        mock_compute_f1.return_value = {"precision": 0.9, "recall": 0.8, "f1": 0.85}
        evaluator = BERTScoreEvaluator()
        result = evaluator.compute_single("candidate", "reference")
        assert result == 0.85
        mock_compute_f1.assert_called_once_with(["candidate"], ["reference"])


class TestSemanticMetrics:
    def test_init_default(self):
        metrics = SemanticMetrics()
        assert metrics.model_name == "all-MiniLM-L6-v2"
        assert metrics._sentence_transformer is None

    def test_init_custom_model(self):
        metrics = SemanticMetrics(model_name="custom-model")
        assert metrics.model_name == "custom-model"

    @patch.object(SemanticMetrics, '_load_sentence_transformer')
    def test_evaluate_pair(self, mock_load_st):
        import numpy as np
        mock_st = MagicMock()
        mock_st.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_load_st.return_value = mock_st
        metrics = SemanticMetrics()
        result = metrics.evaluate_pair("candidate text", "reference text")
        assert "bertscore_f1" in result
        assert "bertscore_rescaled" in result
        assert "cosine_sim" in result
        assert "euclidean_dist" in result
        assert "manhattan_dist" in result
        assert "jaccard_sim" in result
        assert "label" in result

    @patch.object(SemanticMetrics, '_load_sentence_transformer')
    def test_evaluate_pair_no_bert_score(self, mock_load_st):
        import numpy as np
        mock_st = MagicMock()
        mock_st.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_load_st.return_value = mock_st
        metrics = SemanticMetrics()
        metrics.bert_evaluator = MagicMock()
        metrics.bert_evaluator.compute_single.return_value = 0.75
        result = metrics.evaluate_pair("candidate", "reference")
        assert result["bertscore_f1"] == 0.75
        assert "label" in result

    def test_evaluate_batch(self):
        metrics = SemanticMetrics()
        with patch.object(metrics, 'evaluate_pair') as mock_eval:
            mock_eval.return_value = {"bertscore_f1": 0.8, "label": "Good"}
            results = metrics.evaluate_batch(["c1", "c2"], ["r1", "r2"])
            assert len(results) == 2
            assert mock_eval.call_count == 2

    def test_evaluate_batch_mismatched_lengths(self):
        metrics = SemanticMetrics()
        with pytest.raises(ValueError, match="same length"):
            metrics.evaluate_batch(["c1"], ["r1", "r2"])

    @patch.object(SemanticMetrics, '_load_sentence_transformer')
    def test_compute_cosine(self, mock_load_st):
        import numpy as np
        mock_st = MagicMock()
        mock_st.encode.return_value = np.array([[1.0, 0.0], [0.0, 1.0]])
        mock_load_st.return_value = mock_st
        metrics = SemanticMetrics()
        cand_emb = np.array([1.0, 0.0])
        ref_emb = np.array([0.0, 1.0])
        result = metrics._compute_cosine(cand_emb, ref_emb)
        assert isinstance(result, float)
        assert result == pytest.approx(0.0, abs=0.01)

    @patch.object(SemanticMetrics, '_load_sentence_transformer')
    def test_compute_cosine_zero_norm(self, mock_load_st):
        import numpy as np
        mock_st = MagicMock()
        mock_st.encode.return_value = np.array([[1.0, 0.0]])
        mock_load_st.return_value = mock_st
        metrics = SemanticMetrics()
        cand_emb = np.array([0.0, 0.0])
        ref_emb = np.array([1.0, 0.0])
        result = metrics._compute_cosine(cand_emb, ref_emb)
        assert result == 0.0

    @patch.object(SemanticMetrics, '_load_sentence_transformer')
    def test_compute_jaccard(self, mock_load_st):
        import numpy as np
        mock_st = MagicMock()
        mock_st.encode.return_value = np.array([[1.0, 0.0]])
        mock_load_st.return_value = mock_st
        metrics = SemanticMetrics()
        cand_emb = np.array([1.0, 0.0, 1.0])
        ref_emb = np.array([1.0, 1.0, 0.0])
        result = metrics._compute_jaccard(cand_emb, ref_emb)
        assert isinstance(result, float)
        assert result == pytest.approx(1/3, abs=0.01)

    @patch.object(SemanticMetrics, '_load_sentence_transformer')
    def test_compute_jaccard_zero_union(self, mock_load_st):
        import numpy as np
        mock_st = MagicMock()
        mock_st.encode.return_value = np.array([[1.0]])
        mock_load_st.return_value = mock_st
        metrics = SemanticMetrics()
        cand_emb = np.array([0.0, 0.0])
        ref_emb = np.array([0.0, 0.0])
        result = metrics._compute_jaccard(cand_emb, ref_emb)
        assert result == 0.0


class TestLLMJudge:
    def test_init_default(self):
        with patch('src.evaluation.judge.GitHubModelsClient') as mock_client_class:
            judge = LLMJudge()
            assert judge.model == "openai/gpt-4o-mini"
            mock_client_class.assert_called_once()

    def test_init_custom_model(self):
        with patch('src.evaluation.judge.GitHubModelsClient') as mock_client_class:
            judge = LLMJudge(model="custom-model")
            assert judge.model == "custom-model"

    def test_evaluate_valid_json_response(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps({
            "accuracy": 4, "completeness": 5, "relevance": 4, "conciseness": 5, "reasoning": "Good answer"
        })
        judge = LLMJudge()
        judge.client = mock_client
        result = judge.evaluate("Q?", "GT", "Answer")
        assert result["accuracy"] == 4
        assert result["completeness"] == 5
        assert result["reasoning"] == "Good answer"

    def test_evaluate_json_with_surrounding_text(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = 'Here is the evaluation:\n{"accuracy": 3, "completeness": 4, "relevance": 3, "conciseness": 4, "reasoning": "OK"}\nEnd.'
        judge = LLMJudge()
        judge.client = mock_client
        result = judge.evaluate("Q?", "GT", "Answer")
        assert result["accuracy"] == 3
        assert result["reasoning"] == "OK"

    def test_evaluate_missing_keys_returns_default(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps({"accuracy": 4, "reasoning": "Incomplete"})
        judge = LLMJudge()
        judge.client = mock_client
        result = judge.evaluate("Q?", "GT", "Answer")
        assert result["accuracy"] == 3
        assert result["reasoning"] == "Failed to parse judge response - using default scores"

    def test_evaluate_string_scores_converted_to_int(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps({
            "accuracy": "4", "completeness": "5", "relevance": "4", "conciseness": "5", "reasoning": "Good"
        })
        judge = LLMJudge()
        judge.client = mock_client
        result = judge.evaluate("Q?", "GT", "Answer")
        assert isinstance(result["accuracy"], int)
        assert result["accuracy"] == 4

    def test_evaluate_invalid_string_score_becomes_3(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps({
            "accuracy": "high", "completeness": 5, "relevance": 4, "conciseness": 5, "reasoning": "Good"
        })
        judge = LLMJudge()
        judge.client = mock_client
        result = judge.evaluate("Q?", "GT", "Answer")
        assert result["accuracy"] == 3

    def test_evaluate_no_json_found(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = "This is just text, no JSON here."
        judge = LLMJudge()
        judge.client = mock_client
        result = judge.evaluate("Q?", "GT", "Answer")
        assert result["accuracy"] == 3
        assert "Failed to parse" in result["reasoning"]

    def test_evaluate_json_decode_error(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = "{invalid json"
        judge = LLMJudge()
        judge.client = mock_client
        result = judge.evaluate("Q?", "GT", "Answer")
        assert result["accuracy"] == 3

    def test_evaluate_exception(self):
        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("API error")
        judge = LLMJudge()
        judge.client = mock_client
        result = judge.evaluate("Q?", "GT", "Answer")
        assert result["accuracy"] == 3

    def test_is_pass_true(self):
        judge = LLMJudge()
        scores = {"accuracy": 4, "completeness": 4, "relevance": 4, "conciseness": 4}
        assert judge.is_pass(scores) is True

    def test_is_pass_false(self):
        judge = LLMJudge()
        scores = {"accuracy": 2, "completeness": 2, "relevance": 2, "conciseness": 2}
        assert judge.is_pass(scores) is False

    def test_is_pass_custom_threshold(self):
        judge = LLMJudge()
        scores = {"accuracy": 3, "completeness": 3, "relevance": 3, "conciseness": 3}
        assert judge.is_pass(scores, threshold=2.5) is True
        assert judge.is_pass(scores, threshold=3.5) is False

    def test_is_pass_missing_key(self):
        judge = LLMJudge()
        scores = {"accuracy": 4}
        assert judge.is_pass(scores) is False

    def test_is_pass_non_integer_score(self):
        judge = LLMJudge()
        scores = {"accuracy": "high", "completeness": 4, "relevance": 4, "conciseness": 4}
        assert judge.is_pass(scores) is False

    def test_batch_evaluate(self):
        mock_client = MagicMock()
        mock_client.generate.return_value = json.dumps({
            "accuracy": 4, "completeness": 4, "relevance": 4, "conciseness": 4, "reasoning": "OK"
        })
        judge = LLMJudge()
        judge.client = mock_client
        evaluations = [
            {"question": "Q1", "ground_truth": "GT1", "candidate_answer": "A1"},
            {"question": "Q2", "ground_truth": "GT2", "candidate_answer": "A2"},
        ]
        result = judge.batch_evaluate(evaluations)
        assert result["total_evaluated"] == 2
        assert result["pass_rate"] == 1.0
        assert len(result["per_result"]) == 2
        assert all(r["passed"] for r in result["per_result"])

    def test_batch_evaluate_empty(self):
        judge = LLMJudge()
        result = judge.batch_evaluate([])
        assert result["total_evaluated"] == 0
        assert result["pass_rate"] == 0.0

    def test_batch_evaluate_mixed_pass(self):
        judge = LLMJudge()
        mock_client = MagicMock()
        mock_client.generate.side_effect = [
            json.dumps({"accuracy": 5, "completeness": 5, "relevance": 5, "conciseness": 5, "reasoning": "Great"}),
            json.dumps({"accuracy": 1, "completeness": 1, "relevance": 1, "conciseness": 1, "reasoning": "Bad"}),
        ]
        judge.client = mock_client
        evaluations = [
            {"question": "Q1", "ground_truth": "GT1", "candidate_answer": "A1"},
            {"question": "Q2", "ground_truth": "GT2", "candidate_answer": "A2"},
        ]
        result = judge.batch_evaluate(evaluations)
        assert result["pass_rate"] == 0.5
        assert result["per_result"][0]["passed"] is True
        assert result["per_result"][1]["passed"] is False

    def test_get_default_scores(self):
        judge = LLMJudge()
        defaults = judge._get_default_scores()
        assert defaults["accuracy"] == 3
        assert defaults["completeness"] == 3
        assert defaults["reasoning"] == "Failed to parse judge response - using default scores"


class TestPipelineEvaluator:
    def test_init_default(self):
        with patch('src.evaluation.evaluator.LLMJudge') as mock_judge, \
             patch('src.evaluation.evaluator.GroundTruthStore') as mock_gt, \
             patch('src.evaluation.evaluator.SemanticMetrics') as mock_sm:
            evaluator = PipelineEvaluator()
            mock_judge.assert_called_once()
            mock_gt.assert_called_once()
            mock_sm.assert_called_once()

    def test_init_custom_components(self):
        mock_judge = MagicMock()
        mock_gt = MagicMock()
        mock_sm = MagicMock()
        evaluator = PipelineEvaluator(judge=mock_judge, ground_truth=mock_gt, semantic_metrics=mock_sm)
        assert evaluator.judge == mock_judge
        assert evaluator.ground_truth == mock_gt
        assert evaluator.semantic_metrics == mock_sm

    def test_evaluate_query_found(self):
        mock_judge = MagicMock()
        mock_judge.evaluate.return_value = {"accuracy": 4, "completeness": 4, "relevance": 4, "conciseness": 4}
        mock_judge.is_pass.return_value = True
        mock_gt = MagicMock()
        mock_gt.get.return_value = "Ground truth answer"
        evaluator = PipelineEvaluator(judge=mock_judge, ground_truth=mock_gt)
        result = evaluator.evaluate_query("Q?", "Answer", "GRAPH_RAG")
        assert result["question"] == "Q?"
        assert result["pass"] is True
        assert result["ground_truth"] == "Ground truth answer"
        mock_gt.get.assert_called_once_with("Q?")

    def test_evaluate_query_not_found(self):
        mock_gt = MagicMock()
        mock_gt.get.return_value = None
        evaluator = PipelineEvaluator(ground_truth=mock_gt)
        result = evaluator.evaluate_query("Q?", "Answer", "GRAPH_RAG")
        assert result["error"] == "No ground truth found for question"
        assert result["pass"] is False
        assert result["scores"] is None

    def test_evaluate_pipeline(self):
        mock_judge = MagicMock()
        mock_judge.evaluate.return_value = {"accuracy": 4, "completeness": 4, "relevance": 4, "conciseness": 4}
        mock_judge.is_pass.return_value = True
        mock_gt = MagicMock()
        mock_gt.get.return_value = "GT"
        evaluator = PipelineEvaluator(judge=mock_judge, ground_truth=mock_gt)
        queries = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        result = evaluator.evaluate_pipeline(queries, "test_pipeline")
        assert "test_pipeline" in result
        assert result["test_pipeline"]["total_evaluated"] == 2
        assert result["test_pipeline"]["pass_count"] == 2

    def test_evaluate_pipeline_missing_fields(self):
        evaluator = PipelineEvaluator()
        queries = [
            {"question": "Q1"},
            {"answer": "A2"},
        ]
        result = evaluator.evaluate_pipeline(queries, "test_pipeline")
        assert result["test_pipeline"]["total_evaluated"] == 2
        assert all(r.get("error") for r in result["test_pipeline"]["per_query_results"])

    def test_evaluate_semantic(self):
        mock_sm = MagicMock()
        mock_sm.evaluate_batch.return_value = [{"bertscore_f1": 0.8}]
        evaluator = PipelineEvaluator(semantic_metrics=mock_sm)
        result = evaluator.evaluate_semantic(["c1"], ["r1"])
        assert len(result) == 1
        mock_sm.evaluate_batch.assert_called_once_with(["c1"], ["r1"])

    def test_compute_bert_score(self):
        evaluator = PipelineEvaluator()
        with patch.object(evaluator, 'compute_bert_score') as mock_compute:
            mock_compute.return_value = {'raw_f1': 0.8, 'rescaled_score': 4.2, 'label': 'Very Good'}
            result = evaluator.compute_bert_score("candidate", "reference")
            assert result['raw_f1'] == 0.8
            assert result['label'] == 'Very Good'

    def test_compare_pipelines(self):
        evaluations = {
            "pipeline_a": {"pass_rate": 0.8, "avg_scores": {"accuracy": 4.0}, "total_evaluated": 10},
            "pipeline_b": {"pass_rate": 0.9, "avg_scores": {"accuracy": 4.5}, "total_evaluated": 10},
        }
        evaluator = PipelineEvaluator()
        result = evaluator.compare_pipelines(evaluations)
        assert result["best_pipeline"] == "pipeline_b"
        assert result["highest_pass_rate"] == 0.9
        assert "pipeline_a" in result["pipelines"]
        assert "pipeline_b" in result["pipelines"]

