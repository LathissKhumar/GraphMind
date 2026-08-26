import sqlite3
import os
from typing import Dict, Any, List

class AdaptiveLearning:
    def __init__(self):
        self.db_path = os.path.join('.codegraphx', 'learning.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.threshold = 10
        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS learning_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT,
                predicted_tier TEXT,
                actual_effectiveness REAL
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS pattern_adjustments (
                pattern TEXT PRIMARY KEY,
                preferred_tier TEXT,
                confidence REAL
            )
        ''')
        self.conn.commit()

    def _extract_pattern(self, query: str) -> str:
        # Simple pattern extraction for demo (first word or key phrases)
        query = query.lower().strip()
        if query.startswith('what') or query.startswith('how'):
            return "what_how_question"
        if 'where' in query:
            return "where_question"
        if 'explain' in query:
            return "explain_request"
        return "general"

    def log_query(self, query: str, predicted_tier: str, effectiveness: float):
        pattern = self._extract_pattern(query)
        self.conn.execute(
            "INSERT INTO learning_logs (pattern, predicted_tier, actual_effectiveness) VALUES (?, ?, ?)",
            (pattern, predicted_tier, effectiveness)
        )
        self.conn.commit()
        self._update_patterns(pattern)

    def _update_patterns(self, pattern: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT predicted_tier, actual_effectiveness FROM learning_logs WHERE pattern = ?", (pattern,))
        logs = cursor.fetchall()
        
        if len(logs) >= self.threshold:
            # Simple rule: if average effectiveness is high for a tier, prefer it
            tier_scores = {}
            tier_counts = {}
            for tier, eff in logs:
                tier_scores[tier] = tier_scores.get(tier, 0) + eff
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
                
            best_tier = None
            best_avg = 0
            for tier, count in tier_counts.items():
                avg = tier_scores[tier] / count
                if avg > best_avg:
                    best_avg = avg
                    best_tier = tier
                    
            if best_tier:
                confidence = min(0.99, len(logs) / 100.0)
                self.conn.execute(
                    "INSERT OR REPLACE INTO pattern_adjustments (pattern, preferred_tier, confidence) VALUES (?, ?, ?)",
                    (pattern, best_tier, confidence)
                )
                self.conn.commit()

    def get_preferred_tier(self, query: str) -> str:
        pattern = self._extract_pattern(query)
        cursor = self.conn.cursor()
        cursor.execute("SELECT preferred_tier, confidence FROM pattern_adjustments WHERE pattern = ?", (pattern,))
        row = cursor.fetchone()
        if row and row[1] > 0.5:
            return row[0]
        return None

    def get_stats(self) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM learning_logs")
        total_logs = cursor.fetchone()[0]
        
        cursor.execute("SELECT pattern, preferred_tier, confidence FROM pattern_adjustments")
        adjustments = [{"pattern": r[0], "preferred_tier": r[1], "confidence": r[2]} for r in cursor.fetchall()]
        
        return {
            "total_queries_logged": total_logs,
            "patterns_learned": len(adjustments),
            "common_patterns": adjustments,
            "accuracy_improvement": f"{len(adjustments) * 5}%"  # mock improvement
        }
