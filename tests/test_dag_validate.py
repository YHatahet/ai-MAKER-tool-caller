import pytest
from maker.tools.registry import load_tool_registry
from maker.planning.validate import validate_plan

def test_validate_dag_ok():
    registry = load_tool_registry("examples/tools")
    plan = {
        "steps": [
            {"id": "a", "tool": "add_numbers", "input": {"a": 1, "b": 2}, "save_as": "x"},
            {"id": "b", "tool": "add_numbers", "input": {"a": 3, "b": 4}, "save_as": "y"},
            {"id": "c", "tool": "format_message", "depends_on": ["a", "b"], "input": {"message": "$x.sum + $y.sum"}, "save_as": "msg"}
        ],
        "final": "$msg.text"
    }
    validate_plan(plan, registry)

def test_validate_dag_cycle():
    registry = load_tool_registry("examples/tools")
    plan = {
        "steps": [
            {"id": "a", "tool": "add_numbers", "depends_on": ["b"], "input": {"a": 1, "b": 2}},
            {"id": "b", "tool": "add_numbers", "depends_on": ["a"], "input": {"a": 3, "b": 4}}
        ],
        "final": "$x"
    }
    with pytest.raises(ValueError):
        validate_plan(plan, registry)
