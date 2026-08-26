from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.benchmark.runner import BenchmarkResult


class BenchmarkStore:
    def __init__(self, results_dir: str = "results") -> None:
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, benchmark_result: BenchmarkResult) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"benchmark_{date_str}.json"
        filepath = self.results_dir / filename
        existing = []
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing.append(asdict(benchmark_result))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        return str(filepath)

    def load_results(self, date_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        all_results = []
        for json_file in self.results_dir.glob("benchmark_*.json"):
            if date_range:
                file_date = json_file.stem.split("_")[1]
                if "start" in date_range and file_date < date_range["start"]:
                    continue
                if "end" in date_range and file_date > date_range["end"]:
                    continue
            with open(json_file, "r", encoding="utf-8") as f:
                file_results = json.load(f)
                all_results.extend(file_results)
        return all_results

    def get_best_pipeline(self) -> Dict[str, Any]:
        results = self.load_results()
        tier_stats = {
            "GRAPH_ONLY": {"wins": 0, "total": 0, "success_rate": 0.0},
            "GRAPH_RAG": {"wins": 0, "total": 0, "success_rate": 0.0},
            "LLM_FULL": {"wins": 0, "total": 0, "success_rate": 0.0},
        }
        for result in results:
            run_tier = result.get("run_tier")
            if run_tier not in tier_stats:
                continue
            tier_stats[run_tier]["total"] += 1
            if result.get("success", False):
                tier_stats[run_tier]["wins"] += 1
        for tier in tier_stats:
            total = tier_stats[tier]["total"]
            wins = tier_stats[tier]["wins"]
            tier_stats[tier]["success_rate"] = round(wins / total * 100, 2) if total > 0 else 0.0
        best_tier = max(tier_stats.items(), key=lambda x: x[1]["wins"])[0]
        return {
            "best_tier": best_tier,
            "stats": tier_stats,
            "total_queries": len(results),
        }
