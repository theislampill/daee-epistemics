# Recursive State Capsule (daee-state-capsule-v1)

Measurement-only reference for the typed multi-call state capsule contract
landed in Slice D (`460cd3f`, `b919e5`, `2d6bc17`). This document describes
the contract's shape and honesty invariants and how to validate/replay a
capsule sequence; it makes no interlocutor-uptake, semantic-faithfulness, or
release-provenance claim.

## What problem this solves

Before this slice, the only way for a recursive/multi-call model invocation
to "remember" state was to replay the full growing artifact (150-300KB) or
the full runtime (hundreds of thousands of est-tok) on every call. The typed
state capsule is the coined abstraction (the term "state capsule" had zero
matches repo-wide before this slice) that lets one model call instead receive
**kernel + capsule + selected shards**, where the capsule is a small,
structured, schema-validated hand-off.

Source of truth:

- Schema: `schema/state-capsule.schema.json` (draft-07,
  `additionalProperties: false`, 29 required fields).
- Semantic/replay checker: `tools/check_state_capsule.py`.
- Harness emission: `tools/run_staged_current_skill_smoke.py`
  (`build_state_capsule()`).
- Law text: `atomics/skill/references/rubrics/manual-contract-digest.md`,
  section "MULTI-CALL STATE CAPSULE LAW (daee-state-capsule-v1)".

## Multi-call recursion I/O

A capsule is written to `<run_dir>/state-capsules/capsule-NNN.json` after
every validated pipeline stage and again at Stage-07 completion. Each capsule
carries (non-exhaustive; see the schema for the full 29 required fields):

- `n_frame` (selected + held noetic-structure candidates),
- `live_registers` + `register_state` (both ASCII names and Unicode glyph
  aliases are legitimate; see `tools/register_axis_contract.py`
  `REGISTER_AXIS_ALIASES`),
- the full ledger: `B_LA`, `B_MRP`, `B_total`, `held_set_H`,
- `completed_acts` (DSL-separated act rows, `body_ref` as a bare ASCII join
  key -- never the public Unicode-decorated form),
- `last_mrp_resultant` / `route_result_type` / `terminal_states` /
  `field_diagnostics` (divergence/curl states),
- `transport` (`chat` | `file-retained`),
- `output_artifact_path` / `output_sha256` / `output_offset_bytes` (the
  append-offset triple used for replay),
- `cold_law_refs_used`, `shards_loaded` (the bridge field proving which cold
  law and which route shards this call actually consulted).

A model call receiving a capsule never receives the full prior artifact or
the full runtime; it receives the current capsule plus whatever the dispatch
index selects for this stage (see `docs/load-path-architecture.md`).

## Append/hash-offset protocol

The output artifact is append-only. Each capsule's `output_offset_bytes` is
the artifact's byte length as of that capsule, and `output_sha256` is the
SHA-256 of the artifact bytes at that offset. Across a replay sequence:

- `output_offset_bytes` is monotonic non-decreasing;
- the final capsule's `(output_offset_bytes, output_sha256)` must equal the
  real artifact's actual byte length and hash;
- `case_id` and `input_fingerprint` (`sha256:<64-hex>` of normalized D0
  input) stay constant across the whole sequence.

`check_state_capsule.py --replay <dir>` walks an ordered `capsule-NNN.json`
sequence plus the artifact and verifies this protocol, reporting the
earliest-failing capsule rather than only the last.

## PARTIAL/HOLD resume, including the single-call inline fallback

Two hosting shapes are governed:

1. **Multi-call hosts**: on `PARTIAL`/`hold_partial`, the next call resumes
   from the last written capsule. `next_required_action` must be non-empty
   (capped at 400 chars -- a short imperative, not a place to smuggle law or
   runtime prose back into per-call state).
2. **Plain single-call hosts** (no multi-call recursion available): must
   either render the full output in one call, or emit a bounded governed
   `PARTIAL` that includes the full public skeleton **plus an inline fenced
   `daee-state-capsule-v1` resume block**. A prose-only waiver ("I'll
   continue later" with no capsule) is never acceptable for this case -- the
   law is explicit that the fenced capsule block is mandatory, not optional
   commentary.

## Validation and replay commands

```
python tools/check_state_capsule.py --capsule <path-to-capsule.json>
python tools/check_state_capsule.py --replay <run-dir-with-state-capsules/>
python tools/check_state_capsule.py --self-test
```

`--capsule` validates one instance's schema shape plus single-capsule
semantic invariants. `--replay` validates an ordered sequence against the
artifact for the cross-capsule invariants below. `--self-test` runs the
embedded + fixture suite (`tests/state-capsule-fixtures/`: 3 valid sequences
including multi-call-append and partial-hold-resume, 8+ invalid, each pinned
to its exact rejection reason).

The harness (`run_staged_current_skill_smoke.py`) writes capsules
**validate-then-write**: a capsule that fails validation is quarantined as
`capsule-NNN.invalid.json` and never persisted at the canonical name (a
negative self-test asserts this). At Stage-07 completion the harness also
runs a **hard full-sequence replay gate** over the real run directory and
`output.md` -- a replay failure raises `HarnessError`, because this is a run
integrity gate, not mere observability.

## Honesty invariants

These are the semantic checks `check_state_capsule.py` enforces beyond raw
schema shape:

- **Union**: `B_total == B_LA union B_MRP` (order-preserving, no duplicates)
  every capsule.
- **Never-shrink**: `B_LA` never shrinks across a replay sequence
  (anti-slimming at the capsule layer); `capsule-001`'s `B_LA` must already
  be a superset of the artifact's own "Initial burden set: [...]" ground
  truth, so never-shrinks is not vacuously true just because the sequence
  starts small.
- **MRP provenance**: entries only ever enter `B_MRP` with real MRP
  provenance (never predeclared as if generated); `B_MRP` and
  `completed_acts` are append-only across a sequence.
- **Coverage truth**: `coverage_complete: true` requires an empty
  `held_set_H` AND every burden in `B_total` present in `terminal_states`
  with a controlled closed-state token -- a whole-token grammar
  (`^(land|rejected|merged)\b(\(...\))?\+?$` plus the harness's own
  Stage-05 exact vocabulary: `landed`/`cleared`/`discharged-as-derivative`).
  Near-miss strings like `Landmark`, `landless`, `unmerged`, or
  `Land(B2): PARTIAL` do not classify as closed -- those are named canaries
  (`false-coverage-partial-suffix`, `closed-state-near-miss`).
- **Grammar-anchored ACT/Land parity**: the capsule's `completed_acts` are
  checked against the artifact's real ACT-row grammar lines with fenced code
  blocks stripped first, closing a substring-laundering path where a quoted,
  fenced, or negated token inside a code fence could otherwise satisfy the
  check without a real ACT row backing it (canary
  `act-only-in-code-fence`).
- **register_state fidelity**: every live register (alias-normalized; `N`,
  `m`, `H` are exempt because they are carried by dedicated fields, not
  `register_state`) must have a `register_state` entry.
- **Prose-smuggling bounds**: `next_required_action` maxLength 400,
  `notes` maxLength 1200; overall capsule size warns above 16KB and fails
  above 40KB (`FAIL_BYTES`) -- a capsule that large is smuggling prose back
  into what is supposed to be small per-call state.
- **Unicode correctness**: superscript digits used in `body_ref` are matched
  with an explicit character class, not a contiguous codepoint range
  assumption (a documented silent-match-nothing trap that was avoided during
  implementation).

## Boundary

`check_state_capsule.py` validates the capsule contract's shape and internal
consistency only. It does not certify interlocutor uptake, semantic
faithfulness, or release provenance, and it is not a substitute for the
harness emission wave that actually produces capsules at runtime.
