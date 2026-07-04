# Field-Witness Canonicalization & Binding Envelope Spec

> Plan 03, Phase 2 deliverable (spec only). Makes explicit the byte
> canonicalization the retained-proof corpus already uses, and specifies the
> (FUTURE) binding-envelope shape. This is a reference spec: the envelope
> generation, the recomputing binding checker, retained `binding_status`
> assignment, and the certificate `output_fingerprint` rev are Plan 03 Phases 3-5
> and are **artifact-gated / owner-gated**, not built here. No historical retained
> output is mutated by this document.

## `daee-canon-eol-v1` — byte canonicalization (implemented)

This is the de facto canonicalization already applied by
`tools/check_retained_proof_corpus.py` (`sha256_artifact_bytes`, verified
2026-07-04). It is documented here so the contract lives outside the code too:

1. If the bytes contain **no** `\x00` (i.e. text): replace `\r\n` → `\n`, then
   `\r` → `\n` (normalize line endings).
2. Otherwise (binary — a NUL byte is present): hash the **raw** bytes unchanged.
3. Hash with SHA-256; emit the digest as **uppercase** hex.

Explicitly **not** part of `daee-canon-eol-v1`:
- No trailing-newline insertion or trimming.
- No Unicode NFC/NFKC normalization (that would be a different version,
  `daee-canon-v2`, and would invalidate every recorded hash — owner-gated).

A portability self-test (`hash_portability_errors`) already asserts that a
CRLF/LF text twin hashes **equal** and a NUL-containing twin hashes **different**.

## Canonical-JSON projection hashing (spec, for envelope hashes)

Projection hashes (`act_rows_hash`, `nar_hash`, `owner_activation_ordering_hash`)
are specified as: `json.dumps(obj, sort_keys=True, ensure_ascii=False,
separators=(",", ":"))` → encode UTF-8 → SHA-256 → uppercase hex. Sorted keys and
tight separators make the projection order-insensitive and whitespace-stable.

## Binding envelope `field-witness-artifact-binding-v1` (FUTURE)

The envelope binds output-side artifacts together (today only input-side binding
exists — see `docs/audits/field-witness-binding-map.md`, finding F1). Shape:

```json
{
  "schema_version": "field-witness-artifact-binding-v1",
  "canonicalization": "daee-canon-eol-v1",
  "source_commit": "<40-hex>",
  "output_sha256": "<64-hex>",
  "sidecar_sha256": "<64-hex>",
  "origin_sha256": "<64-hex or null>",
  "act_rows_hash": "<64-hex>",
  "nar_hash": "<64-hex>",
  "owner_activation_ordering_hash": "<64-hex or null>",
  "proof_class": "sidecar-backed-structural",
  "binding_status": "current_bound | legacy_unbound | known_contract_drift",
  "non_claims": ["hash binding does not prove semantic correctness or fresh generation"]
}
```

## What is already covered vs gated

- **Covered (implemented + CI-validated):** `daee-canon-eol-v1` output-byte
  hashing and its portability self-test (`check_retained_proof_corpus`); the
  field-witness top-level key contract (`check_field_witness_binding` +
  `schema/field-witness.schema.json`).
- **ARTIFACT-GATED:** generating a `field-witness-artifact-binding-v1` envelope
  per retained case (the envelope artifact does not exist yet) and the checker
  that recomputes `act_rows_hash` / `nar_hash` from projections.
- **OWNER-GATED:** retained `binding_status` assignment (an evidentiary claim over
  24 legacy cases) and the collapse-certificate `output_fingerprint` rev (Phase 5;
  it changes a tracked schema and interacts with 24 retained v1 certs).

## Must-not-claim

- Hash-integrity binding does not prove semantic correctness, faithful generation,
  interlocutor uptake, or cross-host behavior.
- A regenerated envelope/sidecar/certificate never impersonates a released asset.
