from __future__ import annotations
import argparse
import asyncio
import json

from maker.config import PlanningConfig, ExecutionConfig
from maker.execution.pipeline import MakerToolPipeline
from maker.llm.factory import create_client
from maker.planning.planner import MakerPlanner
from maker.tools.registry import load_tool_registry

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--tools-dir", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--max-replans", type=int, default=2)
    ap.add_argument("--max-concurrency", type=int, default=8)
    args = ap.parse_args()

    registry = load_tool_registry(args.tools_dir)
    client = create_client(args.provider, base_url=args.base_url, api_key=args.api_key)
    planner = MakerPlanner(
        client=client,
        model=args.model,
        cfg=PlanningConfig(k=args.k, initial_parallel=args.parallel),
    )
    plan_result = await planner.plan(args.prompt, registry)
    pipeline = MakerToolPipeline(registry)
    execution = await pipeline.execute_with_replanning(
        initial_plan=plan_result.plan,
        planner=planner,
        user_prompt=args.prompt,
        exec_cfg=ExecutionConfig(max_replans=args.max_replans, max_concurrency=args.max_concurrency),
    )

    print("=== PLAN ===")
    print(json.dumps(plan_result.plan, indent=2))
    print("\n=== FINAL ===")
    print(json.dumps(execution.final, indent=2) if isinstance(execution.final, (dict, list)) else execution.final)
    print("\n=== REPLANS USED ===")
    print(execution.replans_used)

if __name__ == "__main__":
    asyncio.run(main())
