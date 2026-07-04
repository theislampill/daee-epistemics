# daee-epistemics

This package is the canonical scriptless compact DSL-governed runtime for:

```text
/daee-epistemics [case]
```

Default use is not prose-only. DSL/IR-governed structure is integral to the
skill's anti-drift, routing, burden-accounting, and restoration discipline; any
anti-hallucination benefit is a design hypothesis unless measured. The default surface should expose compact diagnostic state, governed
Layer B operation, burden-local landing, state/noetic reread, and
STOP/HOLD/PARTIAL/RECURSE discipline without requiring the user to supply a
separate meta-prompt.

`/daee-epistemics:dsl` is the expanded diagnostic/IR visibility mode. It exposes
more machinery, but it is not the first place DSL governance appears.

When a host's final chat channel compresses hard outputs, use file-retained
execution where supported by the host or agent:

```text
/daee-epistemics < input.md > output.md
```

The `< input.md` / `> output.md` convention is skill-level file-retained
execution syntax, not a guarantee about every shell's native stdin behavior. The
full governed answer belongs in the output file; the chat response should only
report the input file, output file, approximate length, and completion status.

The optional script-capable route/check harness is repo/dev/CI machinery, not
canonical package content and not the public identity of the skill. Simulated
route/check output is structural harness evidence only; it is not behavioral
smoke proof and does not prove scriptless shrinkage recovery.

Canonical package roots:

```text
SKILL.md
README.md
references/
compiled-module-map.json
build-manifest.json
```

The canonical package excludes `data/`, `scripts/`, `tests/`, local run
artifacts, `.daee/`, smokes, route/check outputs, and repository tooling.
