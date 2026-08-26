import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(sys_path))

from src.benchmark.token_analyzer import count_tokens, count_dataset_tokens, verify_2m_threshold, get_token_report


class TestTokenAnalyzer:
    def test_count_tokens_valid_file(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("hello world")
        
        with patch("src.benchmark.token_analyzer._counter") as mock_counter:
            mock_counter.count_tokens.return_value = 2
            result = count_tokens(str(test_file))
            assert result == 2
            mock_counter.count_tokens.assert_called_once_with("hello world")

    def test_count_tokens_nonexistent_file(self):
        result = count_tokens("/nonexistent/file.py")
        assert result == 0

    def test_count_tokens_unicode_error(self, tmp_path):
        test_file = tmp_path / "test.py"
        # Write some binary content that will cause UnicodeDecodeError
        test_file.write_bytes(b"\xff\xfe\x00\x00")
        
        result = count_tokens(str(test_file))
        assert result == 0

    def test_count_dataset_tokens(self, tmp_path):
        # Create test files
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.py").write_text("print('world')")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("git config")
        
        with patch("src.benchmark.token_analyzer.count_tokens", return_value=10):
            result = count_dataset_tokens(str(tmp_path))
            assert result == 20  # 10 per file * 2 files

    def test_verify_2m_threshold_true(self):
        with patch("src.benchmark.token_analyzer.count_dataset_tokens", return_value=3_000_000):
            result = verify_2m_threshold("/some/dir")
            assert result is True

    def test_verify_2m_threshold_false(self):
        with patch("src.benchmark.token_analyzer.count_dataset_tokens", return_value=1_000_000):
            result = verify_2m_threshold("/some/dir")
            assert result is False

    def test_verify_2m_threshold_default_dir(self):
        with patch("src.benchmark.token_analyzer.count_dataset_tokens", return_value=3_000_000):
            with patch("os.getcwd", return_value="/current/dir"):
                result = verify_2m_threshold()
                assert result is True

    def test_get_token_report(self, tmp_path):
        with patch("src.benchmark.token_analyzer.count_tokens") as mock_count:
            mock_count.side_effect = [10, 20, 0]  # file1, file2, file3 (0 = skip)
            
            with patch("os.walk") as mock_walk:
                mock_walk.return_value = [
                    (str(tmp_path), [], ["file1.py", "file2.py", "file3.py"])
                ]
                
                result = get_token_report(str(tmp_path))
                assert result["total_tokens"] == 30
                assert "by_file_type" in result
                assert ".py" in result["by_file_type"]
                assert len(result["top_files"]) <= 50
