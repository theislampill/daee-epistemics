# Field-Witness and Artifact Binding Map

> Plan 03, Phase 0 deliverable. Read-only inventory of every surface that a
> `field_witness` binding system must cover, its single owner file, how it is
> validated today, whether its bytes are hashed today, and the binding gap.
> This document is an orientation map, not a proof: it makes no claim that any
> listed artifact is semantically correct, freshly generated, or released.
> Evidence classes follow `docs/proof-class-taxonomy.md`.

## Scope and method

Anchors below were read in the `codex/hardening-all-20260703` worktree and
re-verified against the working tree on 2026-07-04. Line citations name the
file and the construct; they are stable references, not a promise that the
line number never moves. Key sets come from `tools/check_ir_instance_integrity.py`
(`FIELD_WITNESS_KEYS` at line 46, `FIELD_WITNESS_OPTIONAL_KEYS` at line 59, and
the nested `FIELD_WITNESS_*` sets that follow). Certificate shape comes from
`schema/collapse-certificate.schema.json`. Hash behavior comes from
`tools/check_retained_proof_corpus.py`.

## Surface map

"Hashed today" means the bytes or a canonical projection of this surface are
recomputed and compared to a recorded digest by a wired checker. "Structural
only" means a checker validates shape/keys but does not bind bytes.

| # | Surface | Owner file (single source) | Validated by today | Hashed today | Binding gap |
| --- | --- | --- | --- | --- | --- |
| 1 | Visible governed output (`output.md`) | retained case `output.md` (immutable once retained) | `check_retained_proof_corpus.py` recomputes `hashes.output` | Yes (sha256, EOL-normalized) | None on bytes; no binding to the ACT/NAR content that describes it |
| 2 | ACT rows (visible ACT surface) | `atomics/skill/SKILL.md` (ACT surface spec) | `check_act_surface_syntax.py` (`--outputs`) | No (structural only) | ACT-row set not bound to `field_witness.owner_activations[]` |
| 3 | `activation_record` | `atomics/skill/SKILL.md` prose + `check_ir_instance_integrity.py` | `check_ir_instance_integrity.py` key-set validation | No (structural only) | Not projected to a hash; not cross-bound to ACT rows |
| 4 | `field_witness.owner_activations[]` | `check_ir_instance_integrity.py` (`FIELD_WITNESS_KEYS`, line 46) | `check_ir_instance_integrity.py`; tolerant parse in `closure_witness_lib.py` (`extract_field_witness`, ~541-566) | No (structural only) | No published schema artifact; Python key-set is the only master |
| 5 | `owner_activation_ordering` | `check_ir_instance_integrity.py` (`FIELD_WITNESS_OPTIONAL_KEYS`, line 59) + `check_owner_activation_ordering.py` | ordering validator (worktree-only path) | No (structural only) | Optional key; no ordering-hash projection |
| 6 | `normalized_activation_record` | `check_ir_instance_integrity.py` (`FIELD_WITNESS_OPTIONAL_KEYS`, line 59) | `check_ir_instance_integrity.py` | No (structural only) | Optional; no canonical-JSON hash |
| 7 | NAR rows (`field_witness` NAR block) | `check_ir_instance_integrity.py` (`FIELD_WITNESS_NAR_KEYS` / `FIELD_WITNESS_NAR_ROW_KEYS`, lines 67-76) | `check_ir_instance_integrity.py`; `check_nla_decode_semantic_faithfulness.py` decode path | No (structural only) | NAR not bound to ACT / owner / delta / terminal projections |
| 8 | Sidecar manifest rows | `tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/manifest.json` | `check_retained_proof_corpus.py` | Referenced artifacts hashed; manifest bytes not self-hashed | No `binding_status` field; all 24 cases classified `SIDECAR_BACKED_STRUCTURAL` |
| 9 | `hashes` entries (`input`, `output`, `collapse_certificate`, `grapher_html`, b5 sidecar) | manifest `hashes` block per case | `check_retained_proof_corpus.py` recomputes each from bytes | Yes (sha256, EOL-normalized) | Verifies file bytes only, not that content cross-agrees |
| 10 | Certificate fields | `schema/collapse-certificate.schema.json` | `check_collapse_certificate_schema.py` (format); `check_retained_proof_corpus.py` recomputes `input_fingerprint` from input bytes | `input_fingerprint` recomputed; **no `output_fingerprint` exists anywhere** | Output-side binding absent — see Finding F1 |
| 11 | `origin` records | manifest `origin` (points into `.daee/`) | none from a clone (`.daee/` is git-ignored) | No | Unverifiable from a clone — see Finding F3 |
| 12 | Body refs to source owner files | `atomics/skill/references/**` (tactics, techniques, procedures, rubrics, diagnostics) | referenced structurally by checkers; not resolved to a hashed operation body | No | No `body_ref_hashes` binding a ref to its source-owned operation body |

Every surface above has a single owner file; none require an OWNER-DECISION to
name the owner. Owner decisions that *do* arise (certificate schema rev, NFC
canonicalization, `binding_status` assignment, `.daee` origin custody) are
tracked in Plan 03 Section 13 and routed through Plan 19, not resolved here.

## Findings

- **F1 — Shared-certificate false-pass (output-side binding absent).** 24 retained
  collapse certificates, 22 unique by content: two byte-identical pairs bind two
  different outputs each because certificate binding is input-side only.
  Verified pairs (2026-07-04):
  - `gate88-secularism` == `staged-secularism-proofbundle-pilot-v17`
  - `a9-science-source` == `staged-a9-science-source-proofbundle`
  The check-time `input_fingerprint` recompute passes both members of each pair
  because they share input bytes and differ only in output. No `output_fingerprint`
  field exists in `schema/collapse-certificate.schema.json` or in any `tools/*.py`
  (grep 2026-07-04: zero occurrences). Closing this is Plan 03 Phase 5 (owner-gated).
- **F2 — Format-only shas.** `generated_skill_sha` is checked for shape, not
  recomputed against a present skill build; a well-formed but wrong 64-hex value
  passes. Historical skill builds are not retained, so the honest status is
  `legacy_unbound`, never a silent pass.
- **F3 — Origin unverifiability.** Manifest `origin` values point into `.daee/`,
  which is git-ignored (`git check-ignore .daee` succeeds) and absent from a
  clone. No `origin_sha256` is recorded at promotion today; origin is
  local-custody evidence, not proof the run occurred as described.
- **F4 — Documented-evidence pointer (C.5 class).** Coverage rests on a pointer
  to `docs/audits/v0.4.3.0-open-work-ledger.md` whose content is not
  machine-verified. This is a non-claim class weaker than checker-replay and must
  not be upgraded until Plan 05 requalifies it.

## What this map does not establish

- It does not prove any `field_witness`, ACT row, or NAR is faithful to the
  output — surfaces 2-7 are structural-only today.
- It does not add, change, or enforce any binding. Phases 1-5 of Plan 03 do
  that; this is the read-plus-one-doc precondition for them.
- It makes no claim about branch protection, release assets, or Pages state.
