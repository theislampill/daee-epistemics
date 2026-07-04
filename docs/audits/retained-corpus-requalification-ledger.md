# Retained-Corpus Requalification Ledger

- Created: 2026-07-04 (Plan 05, on the committed Plan 18 keystone `62acd08`)
- Corpus: `tests/retained-proof-corpus/v0.4.3.0-schema-light/valid/sidecar-backed/` (24 cases)
- Evidence: smoke-proven 2026-07-04 — each row's `failing_probes` came from running the named checker with `--outputs <all 24 output.md>` and recording which case dirs it flagged.

## Anti-laundering rule (binding)

Old retained rows must NEVER back current-release claims. A release-notes or CHANGELOG
claim of the form "invariant X holds" may cite a retained corpus case id ONLY when
(a) that case's manifest rows explicitly cover the claimed invariant surface,
(b) the case's source build (`generated_skill_sha` / origin) is on the released line
being claimed, and (c) the case passes the current checker battery for that surface at
claim time. Cases marked `known_contract_drift` or `legacy_grandfathered` below fail one
or more current contracts and must never be averaged into "the corpus passes" or cited
for the invariant they fail. Regenerated artifacts are new evidence with a new proof
class, never substitutes for the original released artifact.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `current_bound_pass` | Passes all six current visible-output probes (act-surface, public-grouping, mid-reread, mrp-route, manual-render, concealment). Eligible to back current claims for its manifest-covered rows. |
| `legacy_grandfathered` | Passes today ONLY because of a dated, owner-approved exemption (OD-03/OD-03a concealment basis-qualifier grandfathering). Not a clean pass; the exemption is narrow and dated. |
| `known_contract_drift` | Fails ≥1 current advisory probe (named). Advisory-only (not a hard CI gate today); visible as past behavior under past contracts. Never cite for the failing invariant. |

Probe key: AS=`check_act_surface_syntax`, PG=`check_public_burden_grouping`,
MR=`check_mid_reread_pressure`, RI=`check_mrp_route_invariants`,
MRC=`check_manual_smoke_render_contract`, CM=`check_concealment_mode`.

## Case classification (24/24)

| Case id | Source SHA | Status | Failing probes | Note |
| --- | --- | --- | --- | --- |
| a9-science-source | 60A90DCA | current_bound_pass | — | |
| restoration-track | 60A90DCA | current_bound_pass | — | |
| c7-loopbreak | 60A90DCA | current_bound_pass | — | |
| fitrah-restoration-recoil | 60A90DCA | current_bound_pass | — | |
| authority-return-recoil | EE4EA581 | current_bound_pass | — | |
| uptake-guarantee-recoil | 60A90DCA | current_bound_pass | — | |
| worship-frame-recoil | 60A90DCA | current_bound_pass | — | |
| dad8-science-only-c8 | DAD8847A | current_bound_pass | — | manifest contract_notes present |
| staged-a9-science-source-proofbundle | EE9F8B52 | current_bound_pass | — | |
| cd9a-mixed-concealment | CD9A0141 | legacy_grandfathered | CM (exempted) | OD-03a dated exemption; d3 bound row |
| mixed-family-authority | 9C66D24F | legacy_grandfathered | CM (exempted) | OD-03 dated exemption; d3 bound row |
| academic-prestige-authority | 9C66D24F | legacy_grandfathered | CM (exempted) | OD-03 dated exemption; d3 bound row |
| therapy-moral-tribunal | 0DBEC1A2 | legacy_grandfathered | CM (exempted) | OD-03 dated exemption; d3 bound row |
| source-order-tlang | 60A90DCA | known_contract_drift | RI, MRC | |
| dad8-testimony-c8 | DAD8847A | known_contract_drift | MRC | SOURCE delta typed-transition (class F) |
| exact-secularism | BA6A7A6C | known_contract_drift | CM | basis-qualifier (advisory, not bound) |
| exact-trinitarian-j173 | BA6A7A6C | known_contract_drift | CM | basis-qualifier (advisory) |
| exact-tst-lillard | BA6A7A6C | known_contract_drift | CM | basis-qualifier (advisory) |
| trinitarian-j173-repair-v6 | 67213410 | known_contract_drift | CM | basis-qualifier (advisory; NOT grandfathered per OD-03a) |
| gate88-khaybar | 9DD3DF24 | known_contract_drift | MR, RI | v0.4.4.0 matrix case; pre-hardening |
| gate88-secularism | 9DD3DF24 | known_contract_drift | MR, RI, CM | v0.4.4.0 matrix case; pre-hardening |
| gate88-trinitarian-j173 | 9DD3DF24 | known_contract_drift | MR, RI, CM | v0.4.4.0 matrix case; pre-hardening |
| gate88-tst-lillard | 9DD3DF24 | known_contract_drift | MR, RI, CM | v0.4.4.0 matrix case; pre-hardening |
| staged-secularism-proofbundle-pilot-v17 | EE9F8B52 | known_contract_drift | AS, PG, MR, RI, CM | heaviest drift; the v0.4.5.0 hardening motivator |

Tally: 9 `current_bound_pass`, 4 `legacy_grandfathered`, 11 `known_contract_drift` = 24.

## What this licenses / does not license

- The 9 `current_bound_pass` cases may back current claims for their manifest-covered rows.
- The 4 `legacy_grandfathered` cases pass CI only via the dated OD-03/OD-03a concealment
  exemption; they must NOT be cited as clean concealment evidence.
- The 11 `known_contract_drift` cases are past-behavior evidence under past contracts. They
  remain in the corpus (no historical output mutated) and are visible, not silently upgraded.
- None of these is a semantic-correctness claim; all are structural/notation evidence
  (`SIDECAR_BACKED_STRUCTURAL`), input-fingerprint-bound.

## Next steps (not done in this pass — scoped for a focused follow-up)

1. **Advisory allowlist + wrapper checker** (Plan 05 Phase 4): `tests/retained-proof-corpus/advisory-allowlist.json`
   seeded from the `failing_probes` column above, and `tools/check_retained_corpus_advisory.py`
   that (a) fails on any non-allowlisted (case, checker) failure, (b) fails on any allowlisted
   pair that now passes (stale), (c) has a `--self-test`. Deferred because it shells out to six
   checkers with differing output formats and needs careful testing before it can be trusted as a gate.
2. **Class-F disposition** (`source-order-tlang`, `dad8-testimony-c8` MRC drift): confirm intended
   tightening vs regression (Plan 17 / OD-04) before allowlisting permanently.
3. **Smoke C promotion** (Plan 05 Phase 3): owner-gated, artifact-gated (requires the `.daee` outputs).
4. **Concealment advisory drift** (7 non-grandfathered CM cases): Plan 07 decision — leave as dated
   drift, or add basis qualifiers to those outputs (corpus-mutation, owner-gated).
