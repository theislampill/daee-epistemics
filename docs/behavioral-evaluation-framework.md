# Behavioral Evaluation Framework

This document separates current repo proof from future behavioral proof. It governs future smoke,
live-output, and evaluation design without requiring canned model answers.

## Seven Layers

| Layer | Evidence question | Current repo evidence | Not proven by marker presence |
| --- | --- | --- | --- |
| 1. Structural compliance | Do source files, generated runtime, package shape, and IR fixtures satisfy static contracts? | Static build/checker suite. | Route correctness or live behavior. |
| 2. Render compliance | Does output expose the required governed surfaces when that render mode is in scope? | Render checker and live witness checker. | That the selected route is correct. |
| 3. Route correctness | Was the selected route the right route for the live burden rather than a plausible label? | Routing fixtures and strict parity partially test this. | Competence from printing `∇ route:`. |
| 4. State transformation | Did the operator actually change burden/dependency/register state? | Owner contracts and `post_render_gate`/optional `field_witness` can trace this. | Competence from printing `Δ`, `R(H,Δ)`, or owner names. |
| 5. Reconstruction fidelity | Can an auditor reconstruct why the output followed from input, IR, owners, and held routes? | IR integrity, source-basis checks, reconstruction fixtures. | Live host replay or generalization. |
| 6. Behavioral generalization | Does the runtime hold under paraphrase, adversarial probes, false-route pressure, and host/model variation? | Not yet proven for the pre-public v0.4.2.0 candidate. | Any single fixture or exact expected answer. |
| 7. Interlocutor-facing usefulness | Does the response help the interlocutor without overclaiming acceptance, guidance, or uptake? | Not yet live-output proven. | `T_lang` or `𝒞(Ψᴺ)` markers. |

## Design Rules

- Marker presence is structural/render evidence only, not proof of route correctness,
  state transformation, behavioral competence, or interlocutor uptake.
- Smoke suites should use real package-bound outputs for release proof and should avoid fixed
  expected model prose.
- Small positive/negative fixtures may test checkers, parsers, schemas, and anti-theater rules;
  they must not become canned model answers.
- Future behavioral evaluation should include route-pressure probes, held-set rereads,
  false-route controls, paraphrases, adversarial near-misses, host/model variation, and scoring
  rubrics that reward reconstruction fidelity rather than exact wording.
- The current pre-public v0.4.2.0 candidate can claim source/build/checker discipline and local package-shape proof,
  but not public release provenance, current-release smoke proof, live-output behavioral proof, or
  full formal noetic-field calculus proof.
