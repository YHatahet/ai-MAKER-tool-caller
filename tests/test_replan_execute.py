import asyncio
import json
from maker.config import PlanningConfig, ExecutionConfig
from maker.llm.mock_client import MockLLMClient
from maker.planning.planner import MakerPlanner
from maker.execution.pipeline import MakerToolPipeline
from maker.tools.registry import load_tool_registry

INITIAL_BAD = {
    "steps": [
        {"id": "s1", "tool": "add_numbers", "input": {"a": 12, "b": 30}, "save_as": "sum_result"},
        {"id": "s2", "tool": "fail_once_formatter", "depends_on": ["s1"], "input": {"message": "The answer is $sum_result.sum"}, "save_as": "final_msg"}
    ],
    "final": "$final_msg.text"
}

RECOVERY_GOOD = {
    "steps": [
        {"id": "r1", "tool": "format_message", "input": {"message": "The answer is forty-two"}, "save_as": "final_msg"}
    ],
    "final": "$final_msg.text"
}

def mock_fn(system, user, temperature, max_tokens, meta):
    if "recovery planning microagent" in system.lower():
        return json.dumps(RECOVERY_GOOD)
    return json.dumps(INITIAL_BAD)

def test_execute_with_replanning():
    registry = load_tool_registry("examples/tools")
    planner = MakerPlanner(
        client=MockLLMClient(mock_fn, seed=0),
        model="mock",
        cfg=PlanningConfig(k=1, initial_parallel=1, max_samples=3),
    )
    initial = asyncio.run(planner.plan("Add 12 and 30, then format a short answer.", registry))
    pipeline = MakerToolPipeline(registry)
    result = asyncio.run(
        pipeline.execute_with_replanning(
            initial_plan=initial.plan,
            planner=planner,
            user_prompt="Add 12 and 30, then format a short answer.",
            exec_cfg=ExecutionConfig(max_replans=2, max_concurrency=4),
        )
    )
    assert result.final == "The answer is forty-two"
    assert result.replans_used == 1
