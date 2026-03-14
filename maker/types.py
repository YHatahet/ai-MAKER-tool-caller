from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Dict, List

JsonDict = Dict[str, Any]

@dataclass(frozen=True)
class RawResponse:
    text: str
    model: str
    temperature: float
    max_tokens: int
    meta: Mapping[str, Any] | None = None

@dataclass(frozen=True)
class Rejection:
    reason: str
    raw: RawResponse

@dataclass(frozen=True)
class CandidatePlan:
    plan: JsonDict
    key: str
    raw: RawResponse

@dataclass
class VoteStats:
    samples_total: int = 0
    valid_samples: int = 0
    rejected_samples: int = 0
    rejection_reasons: Dict[str, int] = None
    votes: Dict[str, int] = None

    def __post_init__(self):
        if self.rejection_reasons is None:
            self.rejection_reasons = {}
        if self.votes is None:
            self.votes = {}

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    runner: JsonDict
    input_schema: JsonDict
    output_schema: JsonDict
    tool_dir: str

@dataclass(frozen=True)
class PlanResult:
    plan: JsonDict
    vote_stats: VoteStats

@dataclass(frozen=True)
class ExecutionResult:
    plan: JsonDict
    context: JsonDict
    final: Any
    step_outputs: JsonDict
    replans_used: int = 0

@dataclass(frozen=True)
class ExecutionFailure:
    step_index: int
    step_id: str
    tool: str
    error: str
    context: JsonDict
    remaining_steps: List[JsonDict]
