"""Simple cost tracking without external dependencies"""
from datetime import datetime
from typing import Dict


class CostController:
    def __init__(self):
        self.daily_spend = 0.0
        self.daily_limit = 50.0
        self.token_count = 0

    async def check_and_degrade(self, task: Dict) -> Dict:
        """Basic cost control logic"""
        # Estimate cost (rough approximation)
        estimated_cost = self.token_count * 0.00002  # Rough GPT-3.5 pricing

        if self.daily_spend + estimated_cost > self.daily_limit * 0.9:
            print(
                f"⚠️ COST WARNING: Near daily limit (${self.daily_spend:.2f}/${self.daily_limit})"
            )
            task["max_tokens"] = 100  # Reduce token usage

        return task

    def log_usage(self, tokens: int, cost: float):
        """Track usage"""
        self.token_count += tokens
        self.daily_spend += cost
        print(f"💰 Usage: {tokens} tokens, ${cost:.4f} (Daily: ${self.daily_spend:.2f})")
