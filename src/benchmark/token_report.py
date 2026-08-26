import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from .token_analyzer import get_token_report


class TokenReport:
    def __init__(self, scan_dir: Optional[str] = None) -> None:
        self.scan_dir: str = scan_dir or os.getcwd()
        self.report_data: Optional[Dict[str, Any]] = None
        self.reports_dir: Path = Path(".codegraphx/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self) -> Dict[str, Any]:
        self.report_data = get_token_report(self.scan_dir)
        return self.report_data

    def save_report(self, path: Optional[str] = None, fmt: str = "json") -> str:
        if not self.report_data:
            self.generate()
        out_path: Path
        if not path:
            out_path = self.reports_dir / f"token_report.{fmt}"
        else:
            out_path = Path(path)
        if fmt == "json":
            out_path.write_text(json.dumps(self.report_data or {}, indent=2))
        elif fmt == "markdown":
            md_content = self._to_markdown()
            out_path.write_text(md_content)
        return str(out_path)

    def _to_markdown(self) -> str:
        data = self.report_data or {"total_tokens": 0, "by_file_type": {}, "top_files": [], "token_density": 0.0}
        lines = [
            "# Token Analysis Report",
            f"**Scan Directory**: {self.scan_dir}",
            f"**Total Tokens**: {data['total_tokens']:,}",
            f"**Token Density**: {data['token_density']:.2f} tokens/file",
            "",
            "## Breakdown by File Type",
        ]
        for ext, tokens in sorted(data["by_file_type"].items(), key=lambda x: -x[1]):
            lines.append(f"- **{ext or 'no extension'}**: {tokens:,} tokens")
        lines += ["", "## Top 20 Files by Token Count"]
        for entry in data["top_files"][:20]:
            lines.append(f"- `{entry['path']}`: {entry['tokens']:,} tokens ({entry['type']})")
        return "\n".join(lines)
