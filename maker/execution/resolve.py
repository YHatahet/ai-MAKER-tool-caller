from __future__ import annotations
from typing import Any, Mapping

def _resolve_ref(ref: str, context: Mapping[str, Any]) -> Any:
    if not ref.startswith("$"):
        return ref
    path = ref[1:].split(".")
    value: Any = context
    for part in path:
        if isinstance(value, dict):
            value = value[part]
        else:
            raise ValueError(f"Cannot traverse '{part}' in reference '{ref}'")
    return value

def resolve_value(value: Any, context: Mapping[str, Any]) -> Any:
    if isinstance(value, str):
        if value.startswith("$") and " " not in value and value.count("$") == 1:
            return _resolve_ref(value, context)
        out = value
        start = 0
        while True:
            dollar = out.find("$", start)
            if dollar == -1:
                break
            end = dollar + 1
            while end < len(out) and (out[end].isalnum() or out[end] in "._"):
                end += 1
            ref = out[dollar:end]
            resolved = _resolve_ref(ref, context)
            out = out[:dollar] + str(resolved) + out[end:]
            start = dollar + len(str(resolved))
        return out
    if isinstance(value, list):
        return [resolve_value(v, context) for v in value]
    if isinstance(value, dict):
        return {k: resolve_value(v, context) for k, v in value.items()}
    return value
