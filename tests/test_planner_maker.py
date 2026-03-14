import asyncio
import json
from maker.config import PlanningConfig
from maker.llm.mock_client import MockLLMClient
from maker.planning.planner import MakerPlanner
from maker.tools.registry import load_tool_registry

PLAN_A = {
    "steps": [
        {"id": "calc1", "tool": "add_numbers", "input": {"a": 12, "b": 30}, "save_as": "total"},
        {"id": "fmt", "tool": "format_message", "depends_on": ["calc1"], "input": {"message": "The answer is $total.sum"}, "save_as": "msg"}
    ],
    "final": "$msg.text"
}
PLAN_B = {
    "steps": [
        {"id": "x", "tool": "add_numbers", "input": {"b": 30, "a": 12}, "save_as": "sum_result"},
        {"id": "y", "tool": "format_message", "depends_on": ["x"], "input": {"message": "The answer is $sum_result.sum"}, "save_as": "final_msg"}
    ],
    "final": "$final_msg.text"
}

def mock_fn(system, user, temperature, max_tokens, meta):
    r = meta["rand"]
    if r < 0.2:
        return "Wait, maybe use some other tool"
    if r < 0.6:
        return json.dumps(PLAN_A)
    return json.dumps(PLAN_B)

def test_maker_planner_votes_on_semantic_equivalence():
    registry = load_tool_registry("examples/tools")
    planner = MakerPlanner(
        client=MockLLMClient(mock_fn, seed=0),
        model="mock",
        cfg=PlanningConfig(k=2, initial_parallel=3, max_samples=10),
    )
    out = asyncio.run(planner.plan("Add 12 and 30, then format a short answer.", registry))
    # Both semantically equivalent plans should collapse into one vote bucket
    assert len(out.vote_stats.votes) == 1
    assert out.plan["steps"][0]["tool"] == "add_numbers"
