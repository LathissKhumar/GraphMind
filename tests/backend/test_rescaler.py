import pytest
from src.evaluation.rescaler import rescale_bertscore_f1, score_to_label
from src.evaluation.semantic_metrics import SemanticMetrics


class TestRescaler:
    def test_rescale_value_at_min(self):
        result = rescale_bertscore_f1(0.0)
        assert result == 1.0

    def test_rescale_value_at_max(self):
        result = rescale_bertscore_f1(1.0)
        assert result == 5.0

    def test_rescale_value_at_mid(self):
        result = rescale_bertscore_f1(0.5)
        assert result == 3.0

    def test_rescale_value_at_quarter(self):
        result = rescale_bertscore_f1(0.25)
        assert result == 2.0

    def test_rescale_value_at_three_quarter(self):
        result = rescale_bertscore_f1(0.75)
        assert result == 4.0


class TestScoreLabel:
    def test_label_for_fail(self):
        assert score_to_label(1.0) == "Poor"
        assert score_to_label(1.4) == "Poor"

    def test_label_for_poor(self):
        assert score_to_label(1.5) == "Fair"

    def test_label_for_acceptable(self):
        assert score_to_label(2.5) == "Good"

    def test_label_for_good(self):
        assert score_to_label(3.5) == "Very Good"

    def test_label_for_excellent(self):
        assert score_to_label(4.5) == "Excellent"
        assert score_to_label(5.0) == "Excellent"