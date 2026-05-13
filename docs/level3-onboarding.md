# Optional Route/Check Harness Onboarding

This file keeps the historical onboarding path for the optional script-capable
route/check harness formerly called Level 3. The harness is repo/dev/CI
machinery. It is not the canonical user-facing runtime and is not canonical
package content.

## Ordinary Skill Use

Install the canonical `daee-epistemics.skill` package and invoke:

```text
/daee-epistemics <input>
```

Default `/daee-epistemics` is the compact DSL-governed scriptless runtime. It
must not be described as prose-only fallback. `/daee-epistemics:dsl` is expanded
diagnostic/IR visibility, not the first place DSL governance appears.

When a host's final chat channel compresses hard cases, use canonical
file-retained execution where supported:

```text
/daee-epistemics < C:\path\input.md > C:\path\output.md
```

This is output transport for the same canonical runtime, not a prompt-engineered
harness run.

## Maintainer Harness Use

Use the optional route/check harness only when a maintainer explicitly wants
repo/dev validation:

```text
python skill/scripts/daee_level3.py --input <path> --out <run-dir>
```

For the repo/dev fixture and stability suite:

```text
python skill/scripts/daee_level3.py --run-fixtures --simulate-output --repeat-stability 5
```

The user does not need to inspect `features.json`, `route_plan.json`, or other
harness artifacts during ordinary skill use.

## Honest Claim Boundary

The optional route/check harness gives deterministic routing given extracted
features. It does not claim deterministic feature extraction, because
span-backed semantic features can vary when a model-assisted extractor is used.

The harness validates route-plan reconstruction and checks whether output honors
the plan. It does not guarantee long-output success, remove transformer
execution ceilings, prove scriptless behavioral recovery, or substitute for
package-bound release smokes.
