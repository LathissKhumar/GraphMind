import sqlite3
import os
import json
import time
from typing import Dict, Any, Optional

class PredictiveCache:
    def __init__(self):
        self.db_path = os.path.join('.codegraphx', 'cache.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.ttl = 3600  # 1 hour
        self.hits = 0
        self.misses = 0
        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                query_key TEXT PRIMARY KEY,
                answer TEXT,
                tier TEXT,
                tokens_used INTEGER,
                response_time REAL,
                timestamp REAL
            )
        ''')
        self.conn.commit()

    def _normalize_query(self, query: str) -> str:
        return query.strip().lower()

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        query_key = self._normalize_query(query)
        cursor = self.conn.cursor()
        cursor.execute("SELECT answer, tier, tokens_used, response_time, timestamp FROM queries WHERE query_key = ?", (query_key,))
        row = cursor.fetchone()
        
        if row:
            timestamp = row[4]
            if time.time() - timestamp <= self.ttl:
                self.hits += 1
                return {
                    "answer": row[0],
                    "tier": row[1],
                    "tokens_used": 0,  # 0 tokens for cached response
                    "response_time": row[3],
                    "timestamp": timestamp,
                    "cached": True
                }
            else:
                # Expired
                self.conn.execute("DELETE FROM queries WHERE query_key = ?", (query_key,))
                self.conn.commit()
                
        self.misses += 1
        return None

    def set(self, query: str, answer: str, tier: str, tokens_used: int, response_time: float):
        query_key = self._normalize_query(query)
        timestamp = time.time()
        self.conn.execute(
            "INSERT OR REPLACE INTO queries (query_key, answer, tier, tokens_used, response_time, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (query_key, answer, tier, tokens_used, response_time, timestamp)
        )
        self.conn.commit()

    def invalidate_all(self):
        self.conn.execute("DELETE FROM queries")
        self.conn.commit()
        
    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }
