from __future__ import annotations
import json
import os
from typing import Dict
from maker.types import ToolSpec

def load_tool_registry(tools_dir: str) -> Dict[str, ToolSpec]:
    registry: Dict[str, ToolSpec] = {}
    for name in sorted(os.listdir(tools_dir)):
        tool_dir = os.path.join(tools_dir, name)
        if not os.path.isdir(tool_dir):
            continue
        manifest_path = os.path.join(tool_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            continue
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        spec = ToolSpec(
            name=manifest["name"],
            description=manifest["description"],
            runner=manifest["runner"],
            input_schema=manifest["input_schema"],
            output_schema=manifest["output_schema"],
            tool_dir=tool_dir,
        )
        registry[spec.name] = spec
    return registry
