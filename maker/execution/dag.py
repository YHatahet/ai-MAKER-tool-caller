from __future__ import annotations
from typing import Dict, List, Mapping, Any, Set

def build_step_maps(plan: Mapping[str, Any]) -> tuple[Dict[str, dict], Dict[str, List[str]], Dict[str, int]]:
    steps_by_id = {step["id"]: dict(step) for step in plan["steps"]}
    dependents: Dict[str, List[str]] = {step_id: [] for step_id in steps_by_id}
    indegree: Dict[str, int] = {step_id: 0 for step_id in steps_by_id}
    for step in plan["steps"]:
        for dep in step.get("depends_on", []):
            dependents[dep].append(step["id"])
            indegree[step["id"]] += 1
    return steps_by_id, dependents, indegree

def remaining_subplan(plan: Mapping[str, Any], unfinished_ids: Set[str]) -> List[dict]:
    return [dict(step) for step in plan["steps"] if step["id"] in unfinished_ids]
