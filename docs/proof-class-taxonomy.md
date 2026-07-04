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
