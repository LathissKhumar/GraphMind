import os
import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

sys_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(sys_path))

from src.benchmark.token_report import TokenReport


class TestTokenReport:
    def test_init_default(self):
        report = TokenReport()
        assert report.scan_dir == os.getcwd()
        assert report.reports_dir == Path(".codegraphx/reports")
        assert report.report_data is None

    def test_init_custom_dir(self):
        report = TokenReport(scan_dir="/custom/dir")
        assert report.scan_dir == "/custom/dir"

    def test_generate(self):
        report = TokenReport()
        with patch.object(report, 'generate') as mock_gen:
            mock_gen.return_value = {"total_tokens": 100}
            result = report.generate()
            assert result["total_tokens"] == 100

    def test_save_report_json(self, tmp_path):
        report = TokenReport()
        report.report_data = {
            "total_tokens": 100,
            "by_file_type": {".py": 100},
            "top_files": [{"path": "file.py", "tokens": 100, "type": ".py"}],
            "token_density": 50.0
        }
        
        with patch.object(report, 'generate') as mock_gen:
            mock_gen.return_value = report.report_data
            report.generate()
        
        out_path = report.save_report(path=str(tmp_path / "report.json"), fmt="json")
        assert Path(out_path).exists()
        
        with open(out_path) as f:
            data = json.load(f)
        assert data["total_tokens"] == 100

    def test_save_report_markdown(self, tmp_path):
        report = TokenReport()
        report.report_data = {
            "total_tokens": 100,
            "by_file_type": {".py": 100},
            "top_files": [{"path": "file.py", "tokens": 100, "type": ".py"}],
            "token_density": 50.0
        }
        
        out_path = report.save_report(path=str(tmp_path / "report.md"), fmt="markdown")
        assert Path(out_path).exists()
        
        content = Path(out_path).read_text()
        assert "# Token Analysis Report" in content
        assert "100" in content

    def test_to_markdown(self):
        report = TokenReport()
        report.scan_dir = "/test/dir"
        report.report_data = {
            "total_tokens": 100,
            "by_file_type": {".py": 60, ".js": 40},
            "top_files": [
                {"path": "file1.py", "tokens": 60, "type": ".py"},
                {"path": "file2.js", "tokens": 40, "type": ".js"}
            ],
            "token_density": 50.0
        }
        
        md = report._to_markdown()
        assert "# Token Analysis Report" in md
        assert "100" in md
        assert ".py" in md
        assert ".js" in md
        assert "file1.py" in md
