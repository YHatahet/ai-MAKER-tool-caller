from __future__ import annotations
import asyncio
import json
from typing import Mapping, Dict
from maker.config import PlanningConfig
from maker.llm.base import LLMClient
from maker.planning.redflags import red_flag_reason
from maker.planning.validate import extract_json_object, validate_plan
from maker.planning.canonicalize import canonical_plan_key
from maker.planning.voting import VoteState
from maker.types import CandidatePlan, PlanResult, VoteStats, Rejection, ToolSpec, ExecutionFailure

SYSTEM_PROMPT = """You are a planning microagent.
Create a minimal tool-use plan for the user's request.

Rules:
- Output ONLY a JSON object.
- Use only tools from the provided registry.
- Keep the plan as short as possible.
- Plans may be DAGs: use depends_on when a step depends on earlier step ids.
- Independent steps may be left without dependencies.
- Each step must have: id, tool, input
- Optionally include save_as and depends_on
- final must be a string reference like "$alias" or "$alias.field"
- Do not invent tools.
- Do not include explanations or markdown.
"""

REPLAN_SYSTEM_PROMPT = """You are a recovery planning microagent.
A prior tool-use plan failed during execution.

Your task:
- produce a NEW minimal tool-use plan to finish the user's request from the CURRENT context
- use only available tools
- do not repeat already completed work unless necessary
- output ONLY a JSON object
- plans may be DAGs using depends_on
- each step must have: id, tool, input
- final must be a string reference
"""

def registry_summary(registry: Mapping[str, ToolSpec]) -> str:
    parts = []
    for name, spec in registry.items():
        parts.append(
            f"- {name}: {spec.description}\n"
            f"  input_schema={json.dumps(spec.input_schema, sort_keys=True)}\n"
            f"  output_schema={json.dumps(spec.output_schema, sort_keys=True)}"
        )
    return "\n".join(parts)

class MakerPlanner:
    def __init__(self, *, client: LLMClient, model: str, cfg: PlanningConfig):
        self.client = client
        self.model = model
        self.cfg = cfg

    async def _vote_for_plan(self, *, system: str, user: str, registry: Mapping[str, ToolSpec]) -> PlanResult:
        vote = VoteState(self.cfg.k)
        stats = VoteStats()
        candidates_by_key: Dict[str, CandidatePlan] = {}
        pending: set[asyncio.Task] = set()
        winner: CandidatePlan | None = None

        async def one_sample(temp: float):
            raw = await self.client.sample(
                system=system,
                user=user,
                model=self.model,
                temperature=temp,
                max_tokens=self.cfg.max_tokens,
                meta={"kind": "plan"},
            )
            reason = red_flag_reason(raw.text, self.cfg)
            if reason:
                return Rejection(reason=reason, raw=raw)
            try:
                plan = extract_json_object(raw.text)
                validate_plan(plan, registry)
            except Exception:
                return Rejection(reason="invalid_plan", raw=raw)
            key = canonical_plan_key(plan)
            return CandidatePlan(plan=plan, key=key, raw=raw)

        temps = [self.cfg.temperature_first] + [self.cfg.temperature_rest] * max(0, self.cfg.initial_parallel - 1)
        for t in temps:
            pending.add(asyncio.create_task(one_sample(t)))

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for finished in done:
                stats.samples_total += 1
                res = finished.result()
                if isinstance(res, Rejection):
                    stats.rejected_samples += 1
                    stats.rejection_reasons[res.reason] = stats.rejection_reasons.get(res.reason, 0) + 1
                    continue
                stats.valid_samples += 1
                candidates_by_key.setdefault(res.key, res)
                decided_key = vote.add(res)
                stats.votes = dict(vote.counts)
                if decided_key is not None:
                    winner = candidates_by_key[decided_key]
                    for p in pending:
                        p.cancel()
                    pending.clear()
                    break
            if winner is not None:
                break
            if stats.samples_total < self.cfg.max_samples and len(pending) < self.cfg.initial_parallel:
                pending.add(asyncio.create_task(one_sample(self.cfg.temperature_rest)))

        if winner is None:
            if vote.counts:
                best_key = max(vote.counts.items(), key=lambda kv: kv[1])[0]
                winner = candidates_by_key[best_key]
            else:
                raise RuntimeError("Planner failed: no valid plans sampled")

        return PlanResult(plan=winner.plan, vote_stats=stats)

    async def plan(self, user_prompt: str, registry: Mapping[str, ToolSpec]) -> PlanResult:
        user = (
            "Available tools:\n"
            f"{registry_summary(registry)}\n\n"
            "User request:\n"
            f"{user_prompt}\n"
        )
        return await self._vote_for_plan(system=SYSTEM_PROMPT, user=user, registry=registry)

    async def replan(self, *, user_prompt: str, registry: Mapping[str, ToolSpec], failure: ExecutionFailure) -> PlanResult:
        user = (
            "Available tools:\n"
            f"{registry_summary(registry)}\n\n"
            "Original user request:\n"
            f"{user_prompt}\n\n"
            "Current context (JSON):\n"
            f"{json.dumps(failure.context, sort_keys=True)}\n\n"
            "Failed step:\n"
            f"{json.dumps({'step_index': failure.step_index, 'step_id': failure.step_id, 'tool': failure.tool}, sort_keys=True)}\n\n"
            "Error message:\n"
            f"{failure.error}\n\n"
            "Remaining unfinished steps from previous plan:\n"
            f"{json.dumps(failure.remaining_steps, sort_keys=True)}\n"
        )
        return await self._vote_for_plan(system=REPLAN_SYSTEM_PROMPT, user=user, registry=registry)
