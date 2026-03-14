from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PlanningConfig:
    k: int = 2
    initial_parallel: int = 3
    max_samples: int = 25
    temperature_first: float = 0.0
    temperature_rest: float = 0.2
    max_tokens: int = 1400

    max_response_chars: int = 12000
    max_newlines: int = 220
    max_repeat_line_count: int = 6
    forbid_phrases_casefold: tuple[str, ...] = (
        "wait, maybe",
        "let's check again",
        "is there a mistake",
        "maybe the plan should",
    )

@dataclass(frozen=True)
class ExecutionConfig:
    max_replans: int = 2
    max_concurrency: int = 8
