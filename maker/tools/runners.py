from __future__ import annotations
import asyncio
import importlib.util
import json
import os
from typing import Any, Mapping
from maker.llm.http_json import post_json, get_json
from maker.schema.simple_jsonschema import validate_json
from maker.types import ToolSpec

def _load_python_callable(file_path: str, func_name: str):
    spec = importlib.util.spec_from_file_location("maker_dynamic_tool", file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load python tool from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, func_name)

async def run_tool(spec: ToolSpec, tool_input: Mapping[str, Any]) -> Mapping[str, Any]:
    validate_json(tool_input, spec.input_schema)
    runner_type = spec.runner["type"]

    if runner_type == "python":
        entry = spec.runner["entrypoint"]
        file_name, func_name = entry.split(":")
        file_path = os.path.join(spec.tool_dir, file_name)
        fn = _load_python_callable(file_path, func_name)
        if asyncio.iscoroutinefunction(fn):
            output = await fn(dict(tool_input))
        else:
            output = await asyncio.to_thread(fn, dict(tool_input))
    elif runner_type == "cli":
        cmd = spec.runner["command"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=spec.tool_dir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(json.dumps(tool_input).encode("utf-8"))
        if proc.returncode != 0:
            raise RuntimeError(f"CLI tool {spec.name} failed: {stderr.decode('utf-8', errors='replace')}")
        output = json.loads(stdout.decode("utf-8"))
    elif runner_type == "http":
        method = spec.runner.get("method", "POST").upper()
        url = spec.runner["url"]
        headers = spec.runner.get("headers", {})
        if method == "POST":
            output = await post_json(url, tool_input, headers)
        elif method == "GET":
            if tool_input:
                raise ValueError("GET http runner currently expects empty tool_input or a wrapper endpoint.")
            output = await get_json(url, headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    else:
        raise ValueError(f"Unsupported runner type: {runner_type}")

    validate_json(output, spec.output_schema)
    return output
