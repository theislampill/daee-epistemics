# Validation registry and promotion boundary

Status: bounded A11 control-plane and validation-consumer migration. This
document does not claim Phase 3 completion, candidate maturity, model behavior,
five-smoke readiness, or release readiness.

## Canonical owners

`tools/validation-registry.json` is the single registry for checker identity,
source hashes, accepted exit categories, artifact applicability, requirement
status, the registered plain-output diagnostic adapter, and the six honest profiles. Profiles also own ordered invocation
projections: result key, checker or in-process-adapter kind, checker/adapter
identity, and argv templates. `schema/validation-registry.schema.json` defines
the public shape. `tools/validation_registry.py` owns pure parsing, hashing,
profile projection, registry integrity, verdict integrity, private-policy
detection, and anti-bank helpers.
`tools/contract_validation.py` is the shared fail-closed JSON-Schema subset
validator and repository path-custody resolver. All external paths remain
repository-relative: absolute, drive-qualified, UNC, parent-traversal, and
resolved symlink/reparse escapes are rejected before a file is read.

The canonical artifact types are:

- `output-md`
- `input-output-pair`
- `staged-handoff-record`
- `state-capsule-sequence`
- `prompt-context-manifest`
- `proof-sidecar-set`
- `retained-case-manifest`
- `captured-output-custody-manifest`

The profiles are `stage07-release`, `captured-output-structural`,
`stage08-proof-surface`, `promotion`, `scorecard`, and `advisory`. Missing a
required row hard-fails or quarantines according to the profile; it never
becomes a neutral `NOT_RUN`. The scorecard profile is a projection of existing
verdicts and must not execute a second detector battery.

Every registry-backed executable consumer profile is semantically validated
before projection. Its checker invocations must be non-empty and contain each
required, artifact-applicable checker exactly once; empty, deleted, duplicate,
optional-only, unknown, and inapplicable invocations fail closed. Every
consumer-bound `output-md` profile covers every checker classified as required
for that artifact. The captured-output profile additionally retains its
explicit mode-specific concealment check.

## Replay verdict

`schema/checker-replay-verdict.schema.json` separates launch/completion,
execution status, exit category/code, timeout, crash, usage error, malformed
diagnostic, exact diagnostic ID/stage/class/subcode, stdout/stderr hashes,
artifact/tool/registry hashes, downstream invalidation, forbidden-artifact
readback, and the accepted/rejected expectation status.

Only `completed + accepted` satisfies a required positive check. Only
`completed + structural-rejection` with exact expected stage, class, subcode,
downstream set, diagnostic markers, active fault, and absent forbidden
artifacts satisfies a negative right-reason check. Exit `1` alone is never
mutation success.

The candidate verifier emits this canonical schema directly. It requires
repository-relative input and output custody, freezes every source in the exact
`captured-output-structural` profile before the first launch, and executes each
helper-owned private source snapshot against the private output snapshot. The
child hashes the source byte object before compiling that same object while
presenting the canonical checker path as `__file__`, `argv[0]`, and the sibling
import root. Canonical input/output, registry, checker sources, and private
snapshots are read back before returning. This binds the registered main checker
sources; sibling modules and repository resources retain their canonical live
semantics and are not claimed as transitively snapshotted. Exit `1` becomes
structural rejection
only through its unique registered checker-specific diagnostic adapter when the
checker's owned failure marker is present in non-empty, non-traceback output.
Timeout, spawn failure, signal/crash, usage exit, arbitrary exit-1 text, and
malformed diagnostics remain explicit infrastructure evidence. `--json-out`
publishes only validated bytes with atomic no-replace semantics. Once a final
path becomes externally visible, a later readback ambiguity fails closed and
preserves that path for custody inspection; cleanup never deletes a possibly
swapped competitor by pathname.

Candidate replay retains every ordered checker result. Its aggregate follows
the first decisive non-accepted result: an earlier genuine
`structural-rejection + REJECTED_EXPECTED` remains structural failure even if a
later checker has infrastructure trouble, while earlier infrastructure remains
infrastructure error. A wrong-reason rejection never shields later
infrastructure.

`tools/assert_expected_rejection.py` consumes an external expectation and
verdict. It does not invoke a model, network, or process tree. It rejects
unknown checkers, wrong-reason diagnostics, usage/infrastructure outcomes,
malformed JSON, hash drift, downstream mismatch, forbidden artifacts, and
active-fault mismatch.

Schema validation precedes semantic validation. Duplicate checker-result IDs,
artifact roles/paths, forbidden readbacks, registry IDs/aliases/profiles, and
consumer IDs are rejected before any index is built, so no dictionary
projection can silently collapse evidence. The registry bytes named by a
verdict must hash to and decode as the same registry object used to validate
that verdict.

## Model-smoke escapes

`schema/model-smoke-escape.schema.json` and
`tools/check_model_smoke_escape_registry.py` implement the Plan 21 D19-D20
boundary:

- Open `YES` and every `UNKNOWN` block maturity; a deterministically detectable
  escape can be closed only with red/green, neighboring-valid, exact
  right-reason, and registry evidence.
- `NO` is scoped to hashes, protocol, defect signature, and IR/artifact
  boundary; it records the missing neutral observable, anti-answer-bank basis,
  strongest compensating observability, and recheck predicates.
- `REASSESSMENT_DUE` is append-only and remains `NO -> NO`.
- `NO -> UNKNOWN` requires the accountable owner, a distinct independent
  reviewer, materially new evidence, a named current question, and a bounded
  resolution date.
- Renewed scoped `NO` requires updated evidence and compensating control.
- A paid successor after `NO` additionally requires five Whys, Hansei, a
  credible owner-source countermeasure, deterministic green, and independent
  concurrence, with usage and authorization drift explicitly resolved.
- Numeric calls avoided require a receipt for an actually blocked planned
  invocation. Otherwise the value is `unknown`.

No campaign cycle/call ceiling, case route, expected answer, expected topology,
fixed burden/submove count, or fixed byte rule belongs in these controls.

## Current integration boundary

The registry classifies every currently discovered `check_*.py` tool that
advertises `--outputs`. The three shared consumers now derive policy from their
registered profile:

- `tools/run_staged_current_skill_smoke.py` executes the exact ordered Stage 07
  projection. Its visible-output and MRP record-surface checks remain two
  explicit in-process adapters; checker failures still abort at the first
  failing invocation. MRP record-surface parity retains checkpoint precedence
  immediately after mid-reread pressure. Stage 07 and retained Stage 08 records
  bind the selected profile, canonical registry path/SHA, and exact result
  order. The required ACT-surface checker runs last, preserving the relative
  precedence of every checkpoint-era Stage 07 check.
- `tools/verify_candidate_output.py` executes the captured-output profile and
  returns a canonical ordered replay verdict bound to registry, checker source,
  input/output artifacts, stdout, and stderr hashes.
- `tools/build_model_compliance_scorecard.py` projects existing validated replay
  verdicts from a manifest only after independently loading the immutable
  canonical five-case input registry and matching its exact ordered IDs plus
  each case's input path/hash custody tuple. The manifest cannot authorize a
  subset or relabel one canonical input as another. The scorecard profile has an empty
  invocation projection. Readback reprojects every row from frozen evidence and
  reloads the same canonical authority; JSON and Markdown publish together as
  one no-replace directory transaction. It never executes a detector or claims
  that the authoritative five-smoke campaign ran.

All three consumer rows use `policy_source: registry`, have unique resolved
source paths, and must contain a real `profile_invocations` call statically bound
to the row's exact profile even during registrations-only validation. The live
check additionally requires zero private consumer policies. AST-based detection
catches renamed, concatenated, nested, sliced, copied, enumerated, incrementally
assembled, directly looped or comprehended, indexed, keyword-command, and
command-variable checker collections only when checker data reaches an imported,
aliased, or canonical subprocess command/script position.
Non-executing labels and argument-only `echo` uses remain clean. Discovery
retains the legacy policy anchors and also
recognizes unregistered clones of executable profile policy; comments cannot
impersonate a real registry projection import/call. Synthetic negative fixtures
retain that rejection path. `--registrations-only` remains a bounded diagnostic
and is not a substitute for the full live check.

The command-position pass resolves bounded unambiguous executable and option
aliases, recognizes `sys.executable`, Windows `py` selectors, and
common/versioned Python launcher paths (including official free-threaded
`python3.13t` and path-qualified `.exe` forms), then parses interpreter options
before
selecting a script. Options that consume a value consume it. Exact and attached
`-c` are terminal; exact and attached `-m` bind only their module slot, where a
qualified dotted name is normalized only to an exact registered checker
identity. Neither mode shifts a later argument into script position. Any
unresolved pre-script token or starred expansion preserves itself and the full
remaining argv as fail-closed candidates. Bounded static-fragment evaluation
covers constants, unambiguous single-assignment alias chains, `+`, and f-string
fields whose leading prefix is statically resolvable. Static formatted fragments
share one 4,096-character expression budget across adjacent f-string fields and
`+` concatenations. A numeric width or precision component above the remaining
budget is rejected before built-in formatting; budget exhaustion, formatting
exceptions, and allocation failure preserve the remaining AST as unresolved
instead of expanding or merging it. Static fragment traversal is also capped at
128 AST edges; deeper structure is retained as unresolved, and a residual
parser/evaluator recursion failure at the policy-scan boundary fails closed.
A separately known leading `-c` or `-m` prefix remains authoritative even when
its payload is unresolved.
`.format`, percent formatting, and `join` remain intentionally unresolved;
known or unresolved Python launchers inspect those candidate expressions fail
closed. Known non-Python executables remain clean and are never globally
scanned for checker-like later arguments.

## Negative-expectation migration

`schema/negative-fixture-expectation.schema.json` now requires
`expected_failure_subcode`. Thirty-seven pre-existing sidecars lacked that
field. Each payload was executed through its owning checker first; because
those legacy checkers expose one stable machine diagnostic code as
`failure_class`, the matching emitted code was copied to the subcode field.
No generic placeholder was introduced. Every currently active sidecar has an
exact stage, class, subcode, downstream invalidation set, and forbidden
artifact set.

## Deterministic commands

```powershell
python -B tools/validation_registry.py --self-test
python -B tools/contract_validation.py --self-test
python -B tools/check_validation_registry.py --self-test
python -B tools/check_validation_registry.py --registrations-only
python -B tools/check_validation_registry.py
python -B tools/verify_candidate_output.py --self-test
python -B tools/verify_candidate_output.py --profile captured-output-structural --input <input.txt> --output <output.md> --verdict-id <case-id> --json-out <verdict.json>
python -B tools/build_model_compliance_scorecard.py --self-test
python -B tools/build_model_compliance_scorecard.py --case-manifest <case-manifest.json> --out-dir <fresh-scorecard-directory>
python -B tools/assert_expected_rejection.py --self-test
python -B tools/check_model_smoke_escape_registry.py --self-test
python -B tools/check_model_smoke_escape_registry.py
```
