from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


DB_DIR = Path(".codegraphx")
DB_PATH = DB_DIR / "query_log.db"


@dataclass(frozen=True)
class QueryLogRecord:
    query: str
    tier: str
    tokens: int
    response_time_ms: float
    timestamp: str
    dollar_cost: float


class QueryLogger:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                tier TEXT NOT NULL,
                tokens INTEGER NOT NULL,
                response_time_ms REAL NOT NULL,
                timestamp TEXT NOT NULL,
                dollar_cost REAL NOT NULL
            )
            """
        )
        self.conn.commit()

    def log_query(
        self,
        query: str,
        tier: str,
        tokens: int,
        response_time_ms: float,
        dollar_cost: float,
        timestamp: Optional[str] = None,
    ) -> None:
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO query_log (query, tier, tokens, response_time_ms, timestamp, dollar_cost) VALUES (?, ?, ?, ?, ?, ?)",
            (query, tier, tokens, response_time_ms, ts, dollar_cost),
        )
        self.conn.commit()

    def get_metrics(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(tokens), 0), COALESCE(AVG(response_time_ms), 0), COALESCE(SUM(dollar_cost), 0) FROM query_log")
        total_queries, total_tokens, avg_response_time_ms, dollar_cost_saved = cursor.fetchone()

        cursor.execute("SELECT tier, COALESCE(SUM(tokens), 0) FROM query_log GROUP BY tier")
        tokens_by_tier = {tier: tokens for tier, tokens in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM query_log WHERE tokens <= 0")
        zero_token_queries = cursor.fetchone()[0] or 0
        savings_ratio = (zero_token_queries / total_queries) if total_queries else 0.0

        return {
            "total_queries": int(total_queries or 0),
            "total_tokens": int(total_tokens or 0),
            "tokens_by_tier": tokens_by_tier,
            "avg_response_time_ms": float(avg_response_time_ms or 0.0),
            "savings_percentage": round(float(savings_ratio or 0.0) * 100, 1),
            "dollar_cost_saved": float(dollar_cost_saved or 0.0),
        }


if __name__ == "__main__":
    logger = QueryLogger()
    logger.log_query("What functions call X?", "GRAPH_ONLY", 12, 3.5, 0.0)
    print(logger.get_metrics())
