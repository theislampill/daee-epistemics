# Execution Spine Map (skill-as-code pipeline index)

> A **pointer map**, not a restatement and not a runtime rewrite. It indexes how
> the repo *already* implements the North-Star skill-as-code pipeline, so the
> Stage 01–08 contract and its skill↔harness↔checker wiring can be understood
> without reverse-engineering the harness. It changes no runtime behavior and
> adds no runtime content. Source-of-truth stays in the files this map points to;
> where they disagree with this map, **they win**.

## Tier split

- **Tier 0 — in-skill runtime self-check (model-readable).** Already present in the
  compiled runtime: the `## EXECUTION SPINE` section of `skill/SKILL.md`
  (source: `atomics/skill/SKILL.md`) plus
  `references/diagnostics/recursive-state-transitions.md`. This is the execution
  contract a model sees when `/daee-epistemics` runs. This map does **not**
  duplicate it into a new runtime file (that would grow the load-path budget and
  fight the 80k root guard).
- **Tier 1 — repo no-model verification.** The Python harness, standalone
  checkers, fixtures, and hashes; requires a checkout. Green today:
  `run_local_ci: PASS`.
- **Tier 2 — model smoke / release verification.** External, owner-gated,
  artifact-gated, or spend-gated (four-smoke matrix, release provenance, Pages).
  Out of local scope.

## Execution-spine step map (North-Star thesis chain)

Each row is one step of `surface observation → hidden noetic state → owner/TTP
operation → register-axis transition → controlled delta → MRP/NAR/field_witness
mirror → public proof scaffold → sidecar eligibility`, mapped to its Tier-0 owner
(skill), Tier-1 harness stage/function, and the checker family that verifies it.

| Step (thesis chain) | Stage | Tier-0 owner (skill / runtime reference) | Tier-1 harness | Tier-1 checker family |
| --- | --- | --- | --- | --- |
| surface observation / intake | 01 | `SKILL.md` Layer A intake; `references/diagnostics/diagnostic-ir.md` | stage-01 custody in `run_staged_current_skill_smoke.py` | `check_staged_runtime_handshake` (stage01) |
| hidden noetic state (build case state) | 02 | `SKILL.md` `## EXECUTION SPINE` IR(N,m,τ,σ…); `recursive-state-transitions.md` | `normalize_stage02_diagnostic_fields`; burden-floor/details | `check_ir_instance_integrity`, `check_staged_runtime_handshake` |
| owner/TTP operation (route/owner gate → execute) | 03–04 | `SKILL.md` `## EXECUTION SPINE`; `diagnostic-ir.md`; `delta-result-vocabulary.json` | `normalize_stage03_*`, `normalize_stage04_*` | `check_ttp_operator_contracts`, `check_mrp_generated_burden`, `check_owner_contract_parity` |
| register-axis transition | 04 | register tuple `⟨N,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩`; `delta_result_vocabulary.py` | `normalize_stage04_act_fields` / `_act_row_details` | `check_mrp_generated_burden` |
| controlled delta | 04–05 | `delta-result-vocabulary.json` (compact delta = projection, not proof) | `normalize_stage05_*` | `check_mrp_generated_burden` |
| MRP / NAR / field_witness mirror | 05–06 | `SKILL.md` `## EXECUTION SPINE` MRP visibility contract | `normalize_stage05_mrp_fields`, `normalize_stage06_nar_object` / `_witness_nar_fields` | `check_mid_reread_pressure`, `check_mrp_route_invariants`, `check_ir_instance_integrity`, `check_field_witness_binding`, `check_field_witness_convergence` |
| decide STOP / HOLD / RECURSE / PARTIAL | 05–07 | `recursive-state-transitions.md` | stage-05/07 route decision | `check_mrp_route_invariants`, `check_formal_reread_state_semantics` |
| public proof scaffold / visible render | 07 | `references/rubrics/output-release.md`; `diagnostic-render-contract.md` | `normalize_stage07_generated_terminal_accounting` | `check_manual_smoke_render_contract`, `check_tlang_response_closure`, `check_public_burden_grouping`, `check_act_surface_syntax` |
| preserve internal state for audit | 06–08 | `field_witness` contract; `schema/field-witness.schema.json` | stage-06/08 witness + sidecars | `check_field_witness_binding`, `check_retained_proof_corpus` |
| sidecar eligibility (only when licensed) | 08 | sidecar licensing after Stage-07 pass | stage-08 `proof_sidecars` | `check_staged_runtime_handshake` (stage08 path integrity), `check_retained_proof_corpus`, `check_graph_completeness` |

## Skill ↔ harness vocabulary

| Concept | Skill (Tier 0) term | Harness (Tier 1) term |
| --- | --- | --- |
| state | IR(N,m,τ,σ,♥,ξ,Ω,μ,κ,H; Bᵢ) / case state | stage record (`stage_map`) |
| result | Δ / delta_result, Land/HOLD/PARTIAL/RECURSE | stage `status` (pass/held/partial/fail) |
| attempt | a governed pass over the burden field | a smoke run over a captured output |
| artifact | `output.md`, `field_witness` | staged record, `staged-smoke.hashes.json`, sidecars |
| verifier | output-release / post-render checks | `check_*` families above |
| guardrail | non-claims, scope boundary, size guard | `HarnessError`, metacompliance pins |
| stop reason | STOP / HOLD / RECURSE / PARTIAL basis | terminal-state / `route_result_type` |
| handoff | `R(H,Δ)` after each burden | stage N output typed as stage N+1 input |
| visible render | public projection (`output.md`) | Stage-07 public-projection validation |

## Normalizer classification (one facet, not a policy layer)

The harness applies normalizers to a captured output before judging it (see
`docs/model-compliance-scorecard.md` for the failure-shape → detector map). By
effect on meaning:

- **lossless-parse** (benign): punctuation / shape / alias canonicalization —
  e.g. `normalize_stage05_diagnostic_punctuation`, `normalize_string_list`,
  `normalize_stage04_burden_ids`.
- **cli-alias / helper** (benign): field-name aliasing and detail-to-canonical
  derivation — e.g. `normalize_stage02_diagnostic_fields`,
  `normalize_activation_map`.
- **route-state-repair** (semantics-adjacent — the audit concern): repairs to
  route/terminal state — e.g. `normalize_stage03_route_targets`,
  `normalize_stage05_held_route_gradient_identity`, `normalize_stage05_mrp_fields`.
  A route-state repair can turn a non-conformant raw output into a passing one; a
  verdict that does not report the repair can mask a weaker model's output. Making
  those firings visible in the verdict/hash record is the (larger, owner-gated)
  Plan 15 normalizer-transparency refactor of the ~15.9k-line harness; this map
  only classifies them.

## What this map is not

- Not a second execution spine in the root skill (the root is at the size guard;
  the Tier-0 spine already exists in the runtime).
- Not a runtime behavior change, not a harness or skill rewrite, not Python in the
  skill, not a new policy/safety layer.
- Not a source of truth: every row points to the file that owns the contract.
