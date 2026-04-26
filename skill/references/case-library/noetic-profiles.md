---
id: noetic-profiles
module_class: case-library
canonical_path: skill/references/case-library/noetic-profiles.md
contract_version: "0.2.3.0"
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
