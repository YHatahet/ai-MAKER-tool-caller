from __future__ import annotations
from typing import Any, Mapping

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}

def validate_json(data: Any, schema: Mapping[str, Any], path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type is not None:
        py_type = _TYPE_MAP[expected_type]
        if expected_type == "integer":
            ok = isinstance(data, int) and not isinstance(data, bool)
        elif expected_type == "number":
            ok = isinstance(data, (int, float)) and not isinstance(data, bool)
        else:
            ok = isinstance(data, py_type)
        if not ok:
            raise ValueError(f"{path}: expected {expected_type}, got {type(data).__name__}")

    if expected_type == "object":
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                raise ValueError(f"{path}: missing required key '{key}'")
        for key, value in data.items():
            if key in props:
                validate_json(value, props[key], f"{path}.{key}")

    if expected_type == "array":
        item_schema = schema.get("items")
        if item_schema is not None:
            for idx, item in enumerate(data):
                validate_json(item, item_schema, f"{path}[{idx}]")

    enum_vals = schema.get("enum")
    if enum_vals is not None and data not in enum_vals:
        raise ValueError(f"{path}: value {data!r} not in enum {enum_vals}")
