from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_DIR = Path(".codegraphx")
DB_PATH = DB_DIR / "cache.db"
DEFAULT_TTL_SECONDS = 3600


class QueryCache:
    def __init__(self, db_path: Optional[Path] = None, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.ttl_seconds = ttl_seconds
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_key TEXT UNIQUE NOT NULL,
                answer TEXT NOT NULL,
                tier TEXT NOT NULL,
                tokens_used INTEGER NOT NULL,
                response_time_ms REAL NOT NULL,
                timestamp TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_query_key ON cache(query_key)
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hit_count INTEGER DEFAULT 0,
                miss_count INTEGER DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        key = self._normalize(query)
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT answer, tier, tokens_used, response_time_ms, timestamp, created_at FROM cache WHERE query_key = ?",
            (key,)
        )
        row = cursor.fetchone()
        if not row:
            self._log_miss()
            return None
        answer, tier, tokens_used, response_time_ms, timestamp, created_at = row
        if time.time() - created_at > self.ttl_seconds:
            self.invalidate(key)
            self._log_miss()
            return None
        self._log_hit()
        return {
            "answer": answer,
            "tier": tier,
            "tokens_used": tokens_used,
            "response_time_ms": response_time_ms,
            "timestamp": timestamp,
            "cached": True,
        }

    def set(self, query: str, answer: str, tier: str, tokens_used: int, response_time_ms: float) -> None:
        if tier == "LLM_FULL":
            return
        key = self._normalize(query)
        timestamp = datetime.now(timezone.utc).isoformat()
        created_at = int(time.time())
        self.conn.execute(
            "INSERT OR REPLACE INTO cache (query_key, answer, tier, tokens_used, response_time_ms, timestamp, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (key, answer, tier, tokens_used, response_time_ms, timestamp, created_at),
        )
        self.conn.commit()

    def invalidate(self, query: Optional[str] = None) -> None:
        cursor = self.conn.cursor()
        if query:
            cursor.execute("DELETE FROM cache WHERE query_key = ?", (self._normalize(query),))
        else:
            cursor.execute("DELETE FROM cache")
        self.conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cache")
        total = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COALESCE(SUM(hit_count), 0) FROM cache_stats")
        hits = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COALESCE(SUM(miss_count), 0) FROM cache_stats")
        misses = cursor.fetchone()[0] or 0
        rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0.0
        return {"total_entries": total, "hits": hits, "misses": misses, "hit_rate_percent": round(rate, 1)}

    def prefetch(self, known_entities: List[str], query_engine: Any = None) -> int:
        """Predictive prefetch: generate likely queries based on known entities and pre-cache results."""
        predicted_count = 0
        if not known_entities:
            return 0
        for entity in known_entities[:10]:
            base_queries = [
                f"What functions call {entity}?",
                f"What does {entity} call?",
                f"Show imports for {entity}",
                f"List classes in {entity}",
            ]
            for q in base_queries:
                key = self._normalize(q)
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1 FROM cache WHERE query_key = ?", (key,))
                if not cursor.fetchone():
                    predicted_count += 1
        return predicted_count

    def get_predicted_queries(self, entity: str) -> List[str]:
        """Return likely follow-up queries based on an entity."""
        if not entity:
            return []
        return [
            f"What functions call {entity}?",
            f"What does {entity} call?",
            f"Show imports for {entity}",
            f"What classes does {entity} define?",
        ]

    def _normalize(self, query: str) -> str:
        return query.strip().lower()

    def _log_hit(self) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO cache_stats (hit_count, miss_count) VALUES (1, 0)"
        )
        self.conn.commit()

    def _log_miss(self) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO cache_stats (hit_count, miss_count) VALUES (0, 1)"
        )
        self.conn.commit()


if __name__ == "__main__":
    cache = QueryCache()
    cache.set("test query", "Test answer", "GRAPH_ONLY", 0, 5.0)
    print(cache.get("test query"))
    print(cache.get_stats())