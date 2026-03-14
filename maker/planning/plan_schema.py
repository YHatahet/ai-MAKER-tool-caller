PLAN_SCHEMA = {
    "type": "object",
    "required": ["steps", "final"],
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "tool", "input"],
                "properties": {
                    "id": {"type": "string"},
                    "tool": {"type": "string"},
                    "input": {"type": "object"},
                    "save_as": {"type": "string"},
                    "depends_on": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "final": {"type": "string"}
    }
}
