# Level 3 Onboarding

## Ordinary Codex Use

Install the `daee-epistemics.skill` package and invoke:

```text
/daee-epistemics <input>
```

When bundled scripts are available, Codex should use Level 3 by default for
every invocation:

```text
diagnose -> route -> validate/reconstruct -> execution_prompt -> check_execution
```

The user does not need to inspect `features.json`, `route_plan.json`, or other
internal artifacts during ordinary use.

## Scriptless Runtime Fallback

If a runtime cannot execute bundled Python scripts, the response must visibly
label fallback:

```text
Level 1/2 invocation - Level 3 wrapper unavailable in this runtime
```

This is not an error in the skill package; it is an invocation-boundary note.

## Maintainer Command

For local diagnostics:

```text
python skill/scripts/daee_level3.py --input <path> --out <run-dir>
```

For the fixture and stability suite:

```text
python skill/scripts/daee_level3.py --run-fixtures --simulate-output --repeat-stability 5
```

## Honest Claim

Level 3 gives deterministic routing given extracted features. It does not claim
deterministic feature extraction, because span-backed semantic features can vary
when a model-assisted extractor is used.

Level 3 validates route-plan reconstruction and checks whether output honors the
plan. It does not guarantee long-output success or remove transformer execution
ceilings such as the fixture 18 depth limit.

Level 3 is not a substitute for package-bound release smokes. Release smokes
must still show that the runtime actually executes the generated route plan.
