### 1. Create venv, then run:
`pip install -e .`


# MAKER Tools Pipeline v8

This version adds **semantic plan canonicalization** for stronger MAKER voting.

## Why this matters
Two planner samples can be functionally identical but differ in superficial ways:
- step ids (`calc1` vs `step_a`)
- aliases (`total` vs `sum_result`)
- dependency list ordering
- harmless field ordering in JSON

Without canonicalization, MAKER voting treats those as different plans.
With canonicalization, they collapse to the **same vote bucket** if they are structurally equivalent.

## What gets canonicalized
- step ids → `s1`, `s2`, ...
- `save_as` aliases → `a1`, `a2`, ...
- `depends_on` references updated accordingly
- `$alias.field` references rewritten
- steps are normalized in topological order
- dependency lists are sorted

## Result
The planner now votes on a **canonical semantic key**, not the raw JSON string.

This usually improves convergence when the model produces equivalent plans with minor naming differences.
