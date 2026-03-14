from __future__ import annotations
from typing import Dict, Optional
from maker.types import CandidatePlan

class VoteState:
    def __init__(self, k: int):
        self.k = k
        self.counts: Dict[str, int] = {}

    def add(self, cand: CandidatePlan) -> Optional[str]:
        self.counts[cand.key] = self.counts.get(cand.key, 0) + 1
        winner_key, winner_votes = max(self.counts.items(), key=lambda kv: kv[1])
        max_other = 0
        for key, value in self.counts.items():
            if key != winner_key and value > max_other:
                max_other = value
        if winner_votes >= max_other + self.k:
            return winner_key
        return None
