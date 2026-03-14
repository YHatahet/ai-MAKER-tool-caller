from __future__ import annotations
import json
from typing import Any, Dict, List, Mapping, Tuple

def _topological_order(plan: Mapping[str, Any]) -> List[dict]:
    steps = [dict(step) for step in plan["steps"]]
    steps_by_id = {step["id"]: step for step in steps}
    indegree = {step["id"]: len(step.get("depends_on", [])) for step in steps}
    dependents = {step["id"]: [] for step in steps}
    for step in steps:
        for dep in step.get("depends_on", []):
            dependents[dep].append(step["id"])

    ready = sorted([sid for sid, deg in indegree.items() if deg == 0], key=lambda sid: (steps_by_id[sid]["tool"], sid))
    ordered: List[dict] = []
    while ready:
        sid = ready.pop(0)
        ordered.append(steps_by_id[sid])
        for nxt in sorted(dependents[sid]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
                ready.sort(key=lambda x: (steps_by_id[x]["tool"], x))
    return ordered

def _rewrite_refs_in_str(text: str, alias_map: Mapping[str, str]) -> str:
    out = text
    for old_alias, new_alias in sorted(alias_map.items(), key=lambda kv: len(kv[0]), reverse=True):
        out = out.replace(f"${old_alias}.", f"${new_alias}.")
        if out == f"${old_alias}":
            out = f"${new_alias}"
    return out

def _rewrite_value(value: Any, alias_map: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return _rewrite_refs_in_str(value, alias_map)
    if isinstance(value, list):
        return [_rewrite_value(v, alias_map) for v in value]
    if isinstance(value, dict):
        return {k: _rewrite_value(v, alias_map) for k, v in sorted(value.items())}
    return value

def canonicalize_plan(plan: Mapping[str, Any]) -> Mapping[str, Any]:
    ordered = _topological_order(plan)

    step_id_map: Dict[str, str] = {}
    alias_map: Dict[str, str] = {}

    for idx, step in enumerate(ordered, start=1):
        step_id_map[step["id"]] = f"s{idx}"

    alias_idx = 1
    for step in ordered:
        save_as = step.get("save_as")
        if save_as:
            alias_map[save_as] = f"a{alias_idx}"
            alias_idx += 1

    canon_steps = []
    for step in ordered:
        canon = {
            "id": step_id_map[step["id"]],
            "tool": step["tool"],
            "input": _rewrite_value(step["input"], alias_map),
        }
        deps = step.get("depends_on", [])
        if deps:
            canon["depends_on"] = sorted(step_id_map[d] for d in deps)
        if step.get("save_as"):
            canon["save_as"] = alias_map[step["save_as"]]
        canon_steps.append(canon)

    canon_final = _rewrite_value(plan["final"], alias_map)
    return {"steps": canon_steps, "final": canon_final}

def canonical_plan_key(plan: Mapping[str, Any]) -> str:
    canon = canonicalize_plan(plan)
    return json.dumps(canon, sort_keys=True, separators=(",", ":"))
