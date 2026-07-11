# Runtime Context Delivery Foundation

Status: deterministic A12/A13 foundation. This document does not claim staged-runner integration, model behavior, semantic truth, or release readiness.

## Purpose

DAEE distinguishes package availability from call delivery and declared use:

1. `available`: bytes exist in the bound package.
2. `reachable`: a generated map or manifest points to those bytes.
3. `selected`: the pure resolver chose bounded components from validated stage state.
4. `delivered`: exact bytes are bound to the prompt or to an independently verifiable host receipt.
5. `producer-declared-used`: the producer named a delivered component; this is self-attestation, not proof of cognition.
6. `operation-bound`: a checker joins a delivered owner/law component to the operation it governs.

No lower evidence level implies a higher one. Missing, ambiguous, or over-budget required context routes `HOLD` or `PARTIAL`; it never licenses guessed routing, silent candidate loss, fabricated Land, or `COMPLETE`.

## Owned artifacts

- `schema/runtime-call-context.schema.json` defines `daee-runtime-call-context-v1`.
- `tools/runtime_context_resolver.py` reads only a supplied generated package root and returns deterministic byte slices selected from stage policy and validated state.
- `tools/check_runtime_context_delivery.py` independently validates schema shape, package identity, component slices, prompt envelopes and offsets, capsule continuity, structural selection, host receipts, delivery/use subsets, proof mode, and context-budget status.
- `tools/producer-contract-registry.json` binds model-visible staged-harness clauses to canonical atomics owners, generated package owners, prompt projections, checker source hashes, normalizer classes, and proof classes.
- `tools/check_producer_checker_parity.py` rejects checker-only semantic law, missing package owners, semantic normalizer invention, ambiguous ownership, prompt-projection drift, and case/topic selection taint.
- `schema/package-harness-parity.schema.json` and `tools/check_package_harness_parity.py` bind package/build/cold-law/module/context/prompt/checker/normalizer bytes and classify evidence as `package-faithful`, `harness-assisted`, or `unverified-host-ambient`.

## Resolver boundary

The resolver is a pure standard-library module. It performs no process, network, model, repository write, atomics read, or audit-full fallback. All package paths are resolved with symlink-aware root containment. Stage 01 requires an exact hash-bound raw-input transport component; Stage 02 through Stage 07 require the exact previous validated capsule. Selection may use stage policy, route state, owner/module IDs, operations, live registers, MRP state, release mode, and validated ambiguity. It does not use case ID, case name, topic, expected topology, expected answer, burden count, or output-size targets.

Owner modules resolve through `compiled-module-map.json` to the exact `## RUNTIME MODULE: <id>` section in the shipped omnibus file. Cold clauses resolve through `cold-law-manifest.json` and its canonical LF-joined, no-trailing-newline span hash. The resolver never re-inlines the full manual contract or imposes a semantic byte floor.

Transport custody is not semantic context. In particular, a Stage 04 prior capsule does not satisfy live pressure by itself: live pressure with no resolved owner/module, operation-bearing route shard, or cold-law component returns `HOLD` with `live-pressure-without-semantic-context`. The exact raw-input bytes remain a Stage 01 transport requirement; Stage 02–07 preserve input identity/hash while transporting the immediately prior validated capsule and stage-selected context.

## Delivery proof

Explicit components use this envelope:

```text
----- BEGIN DAEE COMPONENT: component-id; sha256=<64 lowercase hex> -----
<exact bytes>
----- END DAEE COMPONENT: component-id -----
```

The delivery checker recomputes source-slice, prompt, package-tree, generated-root, and manifest hashes. It reruns selection from the bound package, stage, validated state, capsule/raw-input transport, and candidate cap; declared candidate and selected sets must exactly match that result. Each mandatory component must be present, and each prompt-bound envelope must appear exactly once at the recorded byte offsets with no undeclared component envelope. A host receipt must independently bind the exact package and component hashes; an opaque or self-attested “skill loaded” claim is `unverified-host-ambient`. Package membership alone is never delivery proof.

The call manifest separates `delivery_status`, `usage_status`, and `proof_mode`. Package/harness parity derives supplements from validated call-context components and requires that set to equal the parity record exactly. Record classification, context `proof_mode`, and runtime `evidence_lane` must agree. Harness supplements force `harness-assisted` classification and cannot be omitted or relabeled package-bound.

Parity proof kind is also joined to the validated transport mechanism: `explicit-prompt-components` requires `exact-component-binding`, while `host-skill-context-receipt` requires `exact-host-receipt`. A parity label alone cannot upgrade or substitute the delivery evidence established by the runtime-context checker.

## Producer/checker parity

Every registered canonical semantic clause has one stable ID, one atomics anchor, one generated package anchor, exact hashes, a resolver-produced prompt component, a checker owner, a normalizer classification, allowed structural selection inputs, and a proof class. The checker inventories the four actual model prompt roots, every local helper transitively reachable from them, and referenced top-level stage-contract bindings. It binds root source/literal hashes, transitive source/literal hashes, and exact clause-marker visibility per prompt surface; an anchor found only in tests, comments outside the prompt closure, or another non-prompt helper is not delivery. Section projections bind the resolver's exact section slice, not the containing bundle hash. A checker-enforced semantic obligation must be visible before the producer call. Post-producer checks are allowed only when explicitly non-semantic or custody-only.

Package/harness records are recursively schema-closed. `execution-mini` is the only accepted package profile, artifact kinds are unique, and package/run/repository artifacts are pinned to their canonical scope and owner path. A prompt or other run artifact cannot impersonate checker or normalizer custody even when its self-declared hash is internally consistent. Local A11 expectation mirrors are also closed to unknown normative fields.

Producer/checker scenario fixtures use the closed `daee-producer-checker-scenario-v1` identity. Scenario schema, identity, validity flag, and the validity-specific `kind` or `mutation` field are checked before mutation dispatch, so a malformed fixture cannot satisfy the lattice through an unrelated failure.

Normalizers may perform lossless spelling, grammar, or mirror canonicalization. They may not invent or change routes, burdens, owners, operations, Land, delta, dependency edges, terminal states, closure, or answer meaning.

## Commands

```powershell
python tools\runtime_context_resolver.py --self-test
python tools\check_runtime_context_delivery.py --self-test
python tools\check_runtime_context_delivery.py --fixtures tests\runtime-context-delivery
python tools\check_producer_checker_parity.py --self-test
python tools\check_producer_checker_parity.py --registry tools\producer-contract-registry.json
python tools\check_package_harness_parity.py --self-test
```

Default self-tests write only to unique operating-system temporary directories. They do not mutate the repository or invoke a model, process runner, or network client.

## Current integration boundary

This foundation intentionally does not edit `tools/run_staged_current_skill_smoke.py`, state-capsule v2 owners, prompt-pack owners, route/cold-law/package owners, preflight, CI, or generated runtime. Until those owners consume these contracts, the current staged harness remains an expected integration RED for package-faithful call-context delivery: it still composes calls from compact prior state, emits capsules after calls, and lacks pre-invocation `daee-runtime-call-context-v1` manifests.

Required future integration delta:

1. Before each Stage 01–07 invocation, the staged runner must call the resolver against one extracted `execution-mini` root, render exact component envelopes, validate the manifest, and abort before invocation on failure.
2. Stage 02–07 must consume the immediately previous validated state-capsule v2 hash; capsule delivery/use fields must derive from the call manifest rather than stage identity.
3. Prompt-pack v2, state-capsule v2, route-shard, cold-law, package-shape, load-budget, dry-run, preflight, CI, and staged-runner owners must join these new hashes without creating duplicate authorities.
4. The runner must render registered clauses from package components, retain raw producer records, apply only lossless adapters, and classify any extra semantic guidance as `harness-assisted`.
5. Candidate maturity and promotion must require package-only isolation plus package/harness parity records from the exact immutable candidate.

No package build, generated rebuild, model call, release, publication, commit, or push is authorized by this document.
