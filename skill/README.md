# daee-epistemics Level 3 Execution

This skill package supports two invocation paths.

Default direct skill use remains Level 1/2 only for runtimes that cannot execute
bundled scripts. When scripts are available, `/daee-epistemics [input]` should
use Level 3 by default for every case:

```text
python scripts/daee_level3.py --input <input.md> --out <run-dir>
```

The wrapper emits:
- `features.json`
- `route_plan.json`
- `validation.json`
- `reconstruction.json`
- `execution_prompt.md` when validation/reconstruction pass, or
  `execution_blocked.md` when route generation is blocked.

If `execution_blocked.md` appears, return its visible PARTIAL/block note and do
not execute an ordinary answer. After the model answers from `execution_prompt.md`,
validate the answer:

```text
python scripts/check_execution.py --route <run-dir>/route_plan.json --output <run-dir>/output.md
```

If `check_execution.py` returns `partial` or `fail`, the user-facing answer
keeps the output but adds a visible banner:

```text
PARTIAL - Level 3 execution check: <specific defect>
```

If bundled scripts cannot run in the current runtime, the answer must visibly
say:

```text
Level 1/2 invocation - Level 3 wrapper unavailable in this runtime
```

Maintainer fixture command:

```text
python scripts/daee_level3.py --run-fixtures --simulate-output --repeat-stability 5
```

Honest claim boundary:
- Routing is deterministic given extracted features.
- Feature extraction includes span-backed interpretive slots and can still vary
  when a model-assisted extractor is used.
- Level 3 does not eliminate transformer execution ceilings.
- Users invoking the skill without the wrapper receive Level 1/2 behavior.
