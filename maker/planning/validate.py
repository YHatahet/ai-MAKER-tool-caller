from __future__ import annotations
import json
from typing import Any, Mapping
from maker.schema.simple_jsonschema import validate_json
from maker.planning.plan_schema import PLAN_SCHEMA
from maker.types import ToolSpec

def extract_json_object(text: str) -> Mapping[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found")
    return json.loads(text[start:end + 1])

def _validate_dag(plan: Mapping[str, Any]) -> None:
    ids = [step["id"] for step in plan["steps"]]
    id_set = set(ids)
    edges = {step_id: [] for step_id in ids}
    for step in plan["steps"]:
        deps = step.get("depends_on", [])
        for dep in deps:
            if dep not in id_set:
                raise ValueError(f"Unknown dependency '{dep}' in step {step['id']}")
            edges[dep].append(step["id"])

    indegree = {step_id: 0 for step_id in ids}
    for step in plan["steps"]:
        for dep in step.get("depends_on", []):
            indegree[step["id"]] += 1

    queue = [step_id for step_id, deg in indegree.items() if deg == 0]
    seen = 0
    while queue:
        cur = queue.pop(0)
        seen += 1
        for nxt in edges[cur]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if seen != len(ids):
        raise ValueError("Plan dependencies contain a cycle")

def validate_plan(plan: Mapping[str, Any], registry: Mapping[str, ToolSpec]) -> None:
    validate_json(plan, PLAN_SCHEMA)
    seen_ids = set()
    seen_aliases = set()
    for step in plan["steps"]:
        step_id = step["id"]
        if step_id in seen_ids:
            raise ValueError(f"Duplicate step id: {step_id}")
        seen_ids.add(step_id)
        tool = step["tool"]
        if tool not in registry:
            raise ValueError(f"Unknown tool '{tool}' in step {step_id}")
        save_as = step.get("save_as")
        if save_as:
            if save_as in seen_aliases:
                raise ValueError(f"Duplicate save_as alias: {save_as}")
            seen_aliases.add(save_as)
    if not isinstance(plan["final"], str):
        raise ValueError("'final' must be a string reference")
    _validate_dag(plan)
