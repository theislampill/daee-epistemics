---
id: noetic-profiles
module_class: case-library
canonical_path: skill/references/case-library/noetic-profiles.md
contract_version: "0.4.0.0"
load_when:
  - redirect only — do not load for profile content; use individual profiles/ files
routing_effects:
  - routes to per-profile files in profiles/
output_shapes:
  - pass-through
catalogue_registered: true
---

> REDIRECT — this file has been replaced by individual per-profile files under `profiles/`
> Do not load this file for profile content. Load the matched profile file from the table below.

# Noetic Structure Profiles — Redirect

## Runtime field-accounting contract

- Activation/profile condition: redirect only — do not load for profile content; use individual profiles/ files.
- Field target: the candidate noetic-frame/profile pressure exposed by `noetic-profiles`; use profile signals as field conditions, not as a deterministic verdict. Activation cue: redirect only — do not load for profile content; use individual profiles/ files.
- Burden pressures usually exposed: profiles expose candidate burdens, likely route pressures, and held alternatives; they do not themselves exhaust the field or license content release.
- Δ effect: `ΔⁿB` may expose, split, or prioritize burdens; `Δκ` updates closure/dependency radius only after routed burden pressure lands.
- Possible ∇ reread: after profile pressure lands, check target-explicit residuals such as `∇·B` for unlanded profile burdens or `∇×κ` for circular route dependency; no ∇ marker is emitted without a target/control effect.
- R(H,Δ) obligation: after any profile-shaped burden lands, reread the whole live field: selected/held N, H, remaining burdens, alternate routes, unresolved registers, and closure pressure.
- Hold/release/closure effect: profile selection can prioritize, hold, or defer routes; it does not license STOP while input-anchored pressure remains unaccounted.
- Output boundary: `unspecified` with output shapes `pass-through`. Default render may show compact state markers when control-bound; long formalism stays audit/formalism-expanded.
- Negative constraints: do not treat a profile label as a verdict, motive proof, deterministic route, scalar summary, or substitute for owner/TTP execution; no ∇ as Δ replacement, no proof-by-symbol, and no Shannon/reconstruction-branding/∇ truth-or-warrant claim.
- Fixture/checker: Catalogue/frontmatter integrity is guarded by `tools/check_ttp_operator_contracts.py`; direct structural routing coverage remains a remediation item.


NS profiles are now individually owned files in `case-library/profiles/`. Each profile is a
distinct canonical unit with its own frontmatter, IR field, and load discipline. Load only the
matched file — never load multiple profile files simultaneously.

## Routing Table

| NS code | Profile | File |
|---------|---------|------|
| NS-1  | Naturalist | `profiles/ns-1-naturalist.md` |
| NS-2  | Agnostic Evidentialist | `profiles/ns-2-agnostic-evidentialist.md` |
| NS-3  | Deconverted (Post-Religious) | `profiles/ns-3-deconverted.md` |
| NS-4  | Secular Moral Realist | `profiles/ns-4-secular-moral-realist.md` |
| NS-5  | Habituated Atheist | `profiles/ns-5-habituated-atheist.md` |
| NS-6  | Kalāmic Evidentialist | `profiles/ns-6-kalamic-evidentialist.md` |
| NS-7  | Theistic Evidentialist | `profiles/ns-7-theistic-evidentialist.md` |
| NS-8  | Muslim-Internal Crisis (Compound) | `profiles/ns-8-muslim-internal-crisis.md` |
| NS-9  | Historical-Critical Skeptic | `profiles/ns-9-historical-critical-skeptic.md` |
| NS-10 | Māturīdī Evidentialist | `profiles/ns-10-maturidi-evidentialist.md` |
| NS-11 | Fideist / Reformed Basic-Belief | `profiles/ns-11-fideist-reformed.md` |
| NS-12 | Blank-Slate or Dual-Nature Fiṭrah | `profiles/ns-12-blank-slate-dual-fitrah.md` |

For the full directory index, minimal-pair discriminators, and load discipline, see
`case-library/profiles/INDEX.md`.
