import asyncio
from maker.execution.pipeline import MakerToolPipeline
from maker.tools.registry import load_tool_registry

def test_pipeline_execute_dag():
    registry = load_tool_registry("examples/tools")
    pipeline = MakerToolPipeline(registry)
    plan = {
        "steps": [
            {"id": "s1", "tool": "add_numbers", "input": {"a": 12, "b": 30}, "save_as": "sum_a"},
            {"id": "s2", "tool": "add_numbers", "input": {"a": 7, "b": 8}, "save_as": "sum_b"},
            {"id": "s3", "tool": "format_message", "depends_on": ["s1", "s2"], "input": {"message": "A=$sum_a.sum, B=$sum_b.sum"}, "save_as": "final_msg"}
        ],
        "final": "$final_msg.text"
    }
    result = asyncio.run(pipeline.execute(plan, max_concurrency=4))
    assert result.final == "A=42, B=15"
