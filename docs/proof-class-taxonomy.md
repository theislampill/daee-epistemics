# Proof Class Taxonomy

This repo uses several kinds of proof language. They are not interchangeable.
Use this file when writing release notes, audit ledgers, retained-corpus
manifests, or checker docstrings.

## Classes

| Class | What it proves | What it does not prove |
| --- | --- | --- |
| static-syntax | Required tokens, headings, field names, and parseable shapes are present. | The body performed the claimed operation. |
| structural-invariant | A visible output, record, or sidecar satisfies bounded route, MRP, graph, custody, and non-claim invariants. | Universal semantic correctness or model-only execution. |
| hash-integrity | A recorded artifact byte-for-byte matches its manifest, provenance, or retained binding. | That the artifact is true, complete, or freshly generated. |
| checker-replay | A named local checker was re-run against the bound artifact and passed. | Cross-host behavior, arbitrary-input behavior, or unenumerated semantic equivalence. |
| sidecar-backed-structural | Retained evidence is bound to sidecars, manifests, hashes, and replayable structural checks. | Semantic proof of the natural-language answer. |
| semantic-replay | Independent semantic equivalence across paraphrase, polarity, negation, and meaning-preserving rewrites. | Not currently implemented in this repo. |

## Current Boundary

The retained proof corpus classification is `SIDECAR_BACKED_STRUCTURAL`.
That means the corpus is a structural and custody evidence surface, not a
semantic proof surface.

`tools/check_nla_decode_semantic_faithfulness.py` is bounded to recoverable
owner, operation, pressure, delta/result, and Land facets from exact retained
text plus `field_witness`. Its name is historical. In current release prose,
describe it as "NLA decode facet recoverability" or "bounded NLA structural
faithfulness"; do not cite it as universal semantic grading.

Release notes may say a validator passed only when the validator was actually
run against the named artifact. Public governed output must not invent
`validation: PASS`, quality-gate, or validator-verdict lines.

## Claim classes

Beyond the proof MECHANISMS above, every claim in release notes, ledgers, and
docs carries a claim CLASS. These are not interchangeable; do not upgrade a claim
to a stronger class without the evidence that class requires.

| Claim class | Definition | Never licenses |
| --- | --- | --- |
| kernel-assumption | A thesis premise granted for engineering purposes (noetic structures as typed state, etc.). | It is a stated assumption, not a proven fact. |
| facet-recoverability | Owner/operation/pressure/delta/Land facets are recoverable from the exact retained text plus `field_witness`. | Semantic equivalence or meaning-correctness of the answer. |
| retained-replay | A named checker was re-run over a retained artifact and passed. | Fresh model execution, arbitrary-input behavior, or cross-host behavior. |
| package-proof | A built `.skill` artifact matches its manifest and provenance by hash and shape. | That the packaged runtime behaves correctly, or that the published asset matches. |
| release-proof | A published release's asset and provenance were verified by readback at the release boundary. | Ongoing consistency; a later force-move or replacement is a separate claim. |
| public-readback | A downloaded published artifact was re-verified against recorded hashes. | That the tagged source tree produced it, absent a rebuild. |
| analogy | A metaphor (Shannon channel, vector calculus) used as engineering framing. | Any literal mathematical or information-theoretic result. |
| target | A future or aspirational capability, explicitly labeled as not-yet-achieved. | Present capability. |
| non-claim | An explicitly disclaimed property (guaranteed uptake, interior-state certification, universal semantic grading, arbitrary-input correctness). | Anything — a non-claim is a prohibition, never evidence. |
| owner-decision | A judgment reserved for the maintainer (custody, release, rule-scoping). | Autonomous execution; a default recommendation is not an approval. |

Assignment rule: a release-notes or ledger sentence that uses a proof verb
(proves / guarantees / ensures / validated / verified) must be assignable to a
proof mechanism above AND a claim class here that its evidence actually supports.
When in doubt, use the weaker class.
