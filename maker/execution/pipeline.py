from __future__ import annotations
import asyncio
from typing import Mapping, Any, Dict, Optional, Set
from maker.config import ExecutionConfig
from maker.execution.resolve import resolve_value
from maker.execution.dag import build_step_maps, remaining_subplan
from maker.tools.runners import run_tool
from maker.types import ExecutionResult, ToolSpec, ExecutionFailure
from maker.planning.planner import MakerPlanner

class MakerToolPipeline:
    def __init__(self, registry: Mapping[str, ToolSpec]):
        self.registry = registry

    async def execute(self, plan: Mapping[str, Any], *, initial_context: Optional[Dict[str, Any]] = None, max_concurrency: int = 8) -> ExecutionResult:
        context: Dict[str, Any] = dict(initial_context or {})
        step_outputs: Dict[str, Any] = {}
        sem = asyncio.Semaphore(max_concurrency)
        steps_by_id, dependents, indegree = build_step_maps(plan)
        completed: Set[str] = set()
        ready = [step_id for step_id, deg in indegree.items() if deg == 0]

        async def run_one(step_id: str):
            step = steps_by_id[step_id]
            spec = self.registry[step["tool"]]
            resolved_input = resolve_value(step["input"], context)
            async with sem:
                output = await run_tool(spec, resolved_input)
            return step_id, output

        while ready:
            batch = list(ready)
            ready = []
            results = await asyncio.gather(*[run_one(step_id) for step_id in batch])
            for step_id, output in results:
                step = steps_by_id[step_id]
                step_outputs[step_id] = output
                alias = step.get("save_as")
                if alias:
                    context[alias] = output
                completed.add(step_id)
                for nxt in dependents[step_id]:
                    indegree[nxt] -= 1
                    if indegree[nxt] == 0:
                        ready.append(nxt)

        if len(completed) != len(steps_by_id):
            raise RuntimeError("Execution ended before all DAG steps completed")
        final = resolve_value(plan["final"], context)
        return ExecutionResult(plan=dict(plan), context=context, final=final, step_outputs=step_outputs, replans_used=0)

    async def execute_with_replanning(
        self,
        *,
        initial_plan: Mapping[str, Any],
        planner: MakerPlanner,
        user_prompt: str,
        exec_cfg: ExecutionConfig,
    ) -> ExecutionResult:
        current_plan = dict(initial_plan)
        context: Dict[str, Any] = {}
        step_outputs: Dict[str, Any] = {}
        replans_used = 0

        while True:
            try:
                sem = asyncio.Semaphore(exec_cfg.max_concurrency)
                steps_by_id, dependents, indegree = build_step_maps(current_plan)
                completed: Set[str] = set()
                ready = [step_id for step_id, deg in indegree.items() if deg == 0]

                async def run_one(step_id: str):
                    step = steps_by_id[step_id]
                    spec = self.registry[step["tool"]]
                    resolved_input = resolve_value(step["input"], context)
                    async with sem:
                        output = await run_tool(spec, resolved_input)
                    return step_id, output

                while ready:
                    batch = list(ready)
                    ready = []
                    try:
                        results = await asyncio.gather(*[run_one(step_id) for step_id in batch])
                    except Exception as e:
                        unfinished = set(steps_by_id) - completed
                        failed_id = batch[0]
                        failed_step = steps_by_id[failed_id]
                        failure = ExecutionFailure(
                            step_index=len(completed),
                            step_id=failed_id,
                            tool=failed_step["tool"],
                            error=str(e),
                            context=dict(context),
                            remaining_steps=remaining_subplan(current_plan, unfinished),
                        )
                        raise RuntimeError(failure) from e

                    for step_id, output in results:
                        step = steps_by_id[step_id]
                        step_outputs[step_id] = output
                        alias = step.get("save_as")
                        if alias:
                            context[alias] = output
                        completed.add(step_id)
                        for nxt in dependents[step_id]:
                            indegree[nxt] -= 1
                            if indegree[nxt] == 0:
                                ready.append(nxt)

                if len(completed) != len(steps_by_id):
                    raise RuntimeError("Execution ended before all DAG steps completed")
                final = resolve_value(current_plan["final"], context)
                return ExecutionResult(
                    plan=dict(current_plan),
                    context=context,
                    final=final,
                    step_outputs=step_outputs,
                    replans_used=replans_used,
                )

            except RuntimeError as e:
                if replans_used >= exec_cfg.max_replans:
                    raise
                failure = e.args[0]
                if not isinstance(failure, ExecutionFailure):
                    raise
                replan_result = await planner.replan(
                    user_prompt=user_prompt,
                    registry=self.registry,
                    failure=failure,
                )
                current_plan = replan_result.plan
                replans_used += 1
