from typing import Dict, Any

class BudgetController:
    def __init__(self, initial_limit: int = 10000):
        self.budget_limit = initial_limit
        self.budget_used = 0
        self.total_tokens_without_graphmind = 0
        self.cost_per_token = 0.00001 # roughly $10 per 1M tokens as an example

    def set_budget(self, limit: int):
        self.budget_limit = limit

    def add_usage(self, tokens: int, estimated_full_tokens: int = None):
        self.budget_used += tokens
        if estimated_full_tokens is None:
            estimated_full_tokens = tokens * 4 # Assume we saved some
        self.total_tokens_without_graphmind += estimated_full_tokens

    def get_status(self) -> Dict[str, Any]:
        remaining = max(0, self.budget_limit - self.budget_used)
        savings = self.total_tokens_without_graphmind - self.budget_used
        
        savings_percentage = 0
        if self.total_tokens_without_graphmind > 0:
            savings_percentage = (savings / self.total_tokens_without_graphmind) * 100
            
        dollar_cost = self.budget_used * self.cost_per_token
        saved_dollars = savings * self.cost_per_token
        
        return {
            "budget_limit": self.budget_limit,
            "budget_used": self.budget_used,
            "budget_remaining": remaining,
            "savings_percentage": round(savings_percentage, 2),
            "dollar_cost": round(dollar_cost, 4),
            "saved_dollars": round(saved_dollars, 4)
        }

    def get_forced_tier(self) -> str:
        """Return forced routing tier based on budget remaining."""
        if self.budget_limit <= 0:
            return "GRAPH_ONLY"
            
        remaining_ratio = (self.budget_limit - self.budget_used) / self.budget_limit
        
        if remaining_ratio < 0.10:
            return "GRAPH_ONLY"
        elif remaining_ratio < 0.25:
            return "GRAPH_RAG"
            
        return None  # No forced downgrade
