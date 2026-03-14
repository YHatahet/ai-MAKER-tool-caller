from maker.planning.canonicalize import canonicalize_plan, canonical_plan_key

def test_semantically_equivalent_plans_share_key():
    p1 = {
        "steps": [
            {"id": "calc1", "tool": "add_numbers", "input": {"a": 12, "b": 30}, "save_as": "total"},
            {"id": "fmt", "tool": "format_message", "depends_on": ["calc1"], "input": {"message": "The answer is $total.sum"}, "save_as": "msg"}
        ],
        "final": "$msg.text"
    }
    p2 = {
        "steps": [
            {"id": "x", "tool": "add_numbers", "input": {"b": 30, "a": 12}, "save_as": "sum_result"},
            {"id": "y", "tool": "format_message", "depends_on": ["x"], "input": {"message": "The answer is $sum_result.sum"}, "save_as": "final_msg"}
        ],
        "final": "$final_msg.text"
    }
    assert canonical_plan_key(p1) == canonical_plan_key(p2)

def test_canonicalize_dag_dependency_sorting():
    plan = {
        "steps": [
            {"id": "b", "tool": "add_numbers", "input": {"a": 3, "b": 4}, "save_as": "y"},
            {"id": "a", "tool": "add_numbers", "input": {"a": 1, "b": 2}, "save_as": "x"},
            {"id": "c", "tool": "format_message", "depends_on": ["b", "a"], "input": {"message": "A=$x.sum B=$y.sum"}, "save_as": "m"}
        ],
        "final": "$m.text"
    }
    canon = canonicalize_plan(plan)
    assert canon["steps"][2]["depends_on"] == ["s1", "s2"]
