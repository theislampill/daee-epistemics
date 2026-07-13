# ANDON A12: Runtime-Footprint Salience and Load-Path Fidelity

Priority: P0/P1 runtime-contract and package-faithfulness fix  
Implementation target: PR #9 branch at planned head `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`  
PR attribution base: `56d023e910810e94f36b1e5e2623d568852bf28b`  
Current remote-main comparator: `c86b3c6673147b8802fe222373a165a37d4d24a8`  
v0.4.5.0 release-line baseline: `8c14e28fbcf440275f4d143a9b7cadc6148aa5a9`  
Regression status: `unproven`  
Plan status: implementation-ready for deterministic context-delivery tooling; model comparison remains owner-gated  
Scope: planning and future repo-local tests only; no model smoke, source mutation, package build, issue, commit, push, tag, release, or publication was performed for this plan

## Command Execution Contract

Unless a block explicitly says otherwise, execute it in a fresh PowerShell process after `Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch`. Treat multi-command blocks as ordered checklists, not as one success unit: run each positive native command, inspect `$LASTEXITCODE` immediately, and stop before the next command on nonzero. A later success may never mask an earlier failure. For an expected-negative probe, capture stdout/stderr and exit code immediately, then assert the exact exit, earliest stage, stable failure class, and absence of forbidden downstream artifacts. Commands naming files or flags this plan proposes are target contracts and become runnable only after the phase that adds them. Preserve the command, head/dirty state, output, and artifact hashes before proceeding. In this plan, `Smoke A` means the narrowest owner-level false-pass/red-green fixture command; `Smoke B` means the broader integration, freshness, package-shape, or composed-preflight command named later in the phases. Both must be green at the same source state before a closure claim, and neither may be replaced by a model run.

## Plain-Language Summary

PR #9 is trying to reduce how much runtime text is loaded at once without losing the laws needed to execute DAEE. The branch has real engineering for that goal: a smaller generated root, a cold-law digest and hash manifest, route shards, a dispatch index, prompt-budget instrumentation, state-capsule schemas, package profiles, and green deterministic checks.

The major abnormality is a missing join between **availability** and **delivery**:

- Current shard checks prove that shard files exist, are mapped, and are named by the dispatch index.
- Current cold-law checks prove that clauses exist, are hash-bound, and have hot pointers/checker mappings.
- Current package checks prove what ships.
- Current prompt checks prove prompt size arithmetic and that the whole runtime/prior output was not replayed.
- Current capsule checks prove capsule shape and replay invariants.

None of those checks currently proves that the capsule, selected shard bytes, or selected cold-law clause bytes entered a particular model call.

The mismatch is direct in the implementation:

1. The hot runtime law says each recursive execution call receives the kernel, current typed capsule, selected route shards, and a local excerpt.
2. `run_staged_current_skill_smoke.py` says capsule emission is a parallel observability artifact that never feeds prompt composition.
3. The harness passes `compact_state(previous_stages)` instead.
4. `shards_loaded` is filled from the stage ID at Stage07 and left empty earlier; it is not derived from prompt bytes.
5. `cold_law_refs_used` is always emitted as an empty list.
6. The prompt manifest records byte arithmetic but no package identity, capsule hash, selected shard hash, cold-clause hash, or exact prompt-component binding.

This plan repairs that join without restoring the huge eager-load path. It introduces a content-addressed call-context manifest, a pure runtime-context resolver, exact component-to-prompt binding, capsule/context parity, no-model package-only deterministic tests, and truthful evidence levels. It preserves the runtime budget and routes HOLD/PARTIAL when required law cannot be delivered. It never uses a fixed output length, burden count, submove count, or topic-specific answer bank.

## Evidence Boundary

### Confirmed repository geometry

Direct object inspection produced:

| Comparator | `skill/SKILL.md` bytes | root blob | `atomics/skill/SKILL.md` bytes | atomics blob |
| --- | ---: | --- | ---: | --- |
| v0.4.5.0 tag | 215,662 | `99496e4e361968e68c66cca8b0ef7dd0ad77d0bc` | 80,607 | `3b76ae3cd27b25d6726b9cc391e83ccc9000841a` |
| PR #9 base `56d023e910810e94f36b1e5e2623d568852bf28b` | 216,112 | `4a4ae5a238aa1d0d10f4910b69875fbc2c460723` | 80,607 | `3b76ae3cd27b25d6726b9cc391e83ccc9000841a` |
| PR #9 head `6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c` | 136,086 | `ef2dc8bbffb867f409030167142285eb0b5b5d44` | 96,303 | `01cee8c870e179956efd7b7feff58802aef92535` |
| remote `main` `c86b3c6673147b8802fe222373a165a37d4d24a8` | 215,662 | `99496e4e361968e68c66cca8b0ef7dd0ad77d0bc` | 80,607 | `3b76ae3cd27b25d6726b9cc391e83ccc9000841a` |

Confirmed interpretation:

- The generated hot root is materially smaller at PR head.
- Canonical atomics source is larger at PR head.
- v0.4.5.0 and current remote main have identical root and atomics blobs for these two files.
- PR base and v0.4.5.0/main share the atomics root but have different generated root blobs. That difference must be accounted for rather than assumed irrelevant.
- The local checkout is shallow, so local merge-base failure is inconclusive. Direct GitHub PR and compare metadata establish `main c86b3c6... -> PR8 head/PR9 base 56d023e... -> PR9 head 6987c9e...`.
- Code introduced by PR #9 must be attributed with `56d023e910810e94f36b1e5e2623d568852bf28b -> 6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c`.
- Release-line behavior may compare v0.4.5.0 with PR head under controlled package/runtime conditions, but that does not make the code diff causal.
- `a46e00f..6987c9e` currently contains 31 changed paths: 26 tests and five tools, with no `atomics/skill/**` or `skill/SKILL.md` change. Those late repairs are harness/checker evidence, not proof that the default packaged runtime behavior changed.

### Confirmed current controls

- `check_route_shard_selection.py --self-test` passed 43/43 planning-time checks.
- The live route-shard check passed and reported eight dispatch-index rows.
- `check_state_capsule.py --self-test` passed its embedded and fixture suite.
- `check_prompt_pack_budget.py --self-test` passed its six expectations.
- The branch-wide no-model preflight is green under its current 16-gate suite.
- `execution-mini` is the default package profile and includes the generated runtime, references, module map, build manifest, and cold-law manifest. It excludes repo-root tools/checkers.
- `audit-full` adds schema, tools, tests, and docs. It is non-default and cannot stand in for package-faithful model behavior or no-model package-only isolation.
- `check_cold_law_digest.py` proves static clause presence, source/cold-copy hash parity, checker mapping, CI wiring, hot pointer parity, advisory budget, allowlist, and reverse anchors.
- `check_route_shard_selection.py` proves static index, mapping, uniqueness, lockstep, selection-law text, and eager-list discipline.
- `check_prompt_pack_budget.py` explicitly says it does not know stage semantics. It validates byte/token arithmetic, two replay flags, a ceiling, and call-site instrumentation parity.
- `check_state_capsule.py` currently validates `cold_law_refs_used` and `shards_loaded` only as string arrays; it does not join them to prompt bytes.

### Confirmed implementation-contract mismatch

Runtime law in `atomics/skill/references/rubrics/manual-contract-digest.md` says:

```text
Each execution call receives the kernel, the current typed state capsule,
the selected route shard(s) for the next burden, and a local excerpt only.
```

Current harness source says:

```text
build_state_capsule() never mutates `stages` and never feeds into prompt composition.
```

Current `stage_prompt()` receives raw input plus `compact_state(previous_stages)`. It has no capsule argument and no selected-shard argument. Current `release_section_prompt()` likewise receives raw input and compact stage state, not the prior capsule.

Current capsule construction:

- sets `cold_law_refs_used` to `[]`;
- sets Stage01-06 `shards_loaded` to `[]`;
- sets Stage07 `shards_loaded` to two constant mandatory shard paths solely because `stage_id == stage-07-release-output`;
- labels the capsule an observability artifact.

This is a confirmed contract mismatch. It does **not** prove that PR #9 caused the captured thin output or that any particular model ignored a law.

### Confirmed wording overreach

The current runtime addendum says a selected module's bundle section "counts as loaded" when the compiled map/routing table points to it and the runner has the generated skill surface. That proves availability and resolvability, not call-specific delivery. The distinction must be corrected.

The current capsule documentation says `cold_law_refs_used` and `shards_loaded` are bridge fields proving what the call actually consulted. Current code does not support that claim. Even after prompt binding, a system can prove delivery, not a model's unobservable internal attention. A model-returned consultation list is self-attestation and must remain labeled as such.

### Inferred

- Keeping closure/proof-tail vocabulary hot while detailed execution law is cold may increase the risk of formal-surface imitation when the required cold clause is not delivered in time.
- Harness-specific prompt scaffolding may compensate for package delivery defects and make harness-assisted runs look healthier than ordinary package invocation.
- Stage07 fragmentation without prior-segment/context binding may increase witness and owner-operation discontinuity.

### Unproven

- PR #9 caused a behavioral regression.
- The runtime-footprint design is inherently unsound.
- A smaller root necessarily causes thinner output.
- A particular model actually consulted or ignored a supplied component.
- Package membership implies host context injection.
- One host's skill-loading behavior represents another host.
- Any fixed output byte range, burden count, or submove count is correct.

## Abnormalities

### A12.1: Static reachability is presented as call-level load evidence

The static system answers:

```text
Does the file exist?
Is it mapped?
Does the hot root point to it?
Does the package ship it?
Is the selection law present?
```

The missing runtime question is:

```text
For call K, what exact kernel/capsule/shard/clause/local-excerpt bytes were delivered,
under what selection basis, from which package/build, and did the output record bind back to them?
```

### A12.2: State capsule is output observability, not call input

The current sequence is:

```text
compose prompt from raw input + compact prior stages
-> invoke model
-> validate stage response
-> write capsule after the call
```

The law requires:

```text
load prior validated capsule
-> resolve selected context from the package
-> bind exact context components into the call
-> invoke model
-> validate response and context acknowledgment
-> write updated capsule
```

Stage01 is a bootstrap exception: no prior stage capsule exists. It receives the kernel/intake context and emits capsule 001. Every later model call receives the previous validated capsule.

### A12.3: Stage07 shard claims are stage-derived, not prompt-derived

The current Stage07 capsule names the output-release and render-contract shards because the stage is 07. That is a declaration of what should have loaded, not evidence of what the prompt carried. The target must derive the list from a hash-bound call-context manifest whose component bytes are found in the exact prompt or independently attested by a host context receipt.

### A12.4: Prompt budget does not describe the effective runtime context

The current prompt manifest splits an already-composed prompt into known substrings and residual bytes. It has no component hash, package hash, capsule hash, shard list, or cold-clause list. It also treats runtime content delivered by a host outside the literal prompt as invisible.

The target must distinguish:

- transport frame bytes;
- host-attached skill context;
- explicitly embedded kernel/shard/clause bytes;
- capsule bytes;
- local excerpt bytes;
- prior output bytes, which remain forbidden except the bounded local excerpt;
- aggregate effective context budget.

### A12.5: Harness-assisted recovery is not package-faithful recovery

Late PR cycles changed tools and tests, especially the staged runner's prompts and normalization. Those changes can improve the controlled harness without changing canonical atomics or generated root. A release claim therefore needs a package-faithful lane in which the execution-mini package is the only runtime-law source and the runner supplies only generic transport/stage framing.

## Architectural Requirement

The formal chain remains:

```text
𝓝 ⊢ D₀
  → ⇝ Ψᴺ⟨N∈𝓝,m,τ,σ,♥,ξ,Ω,μ,κ,H⟩
  → IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)
  → ∇_route
  → ⁿB
  → {ⁿBᵢ[OPᵢ]}
  → Land(ⁿB)
  → ΔⁿB{♥,ξ,Ω,σ,μ}/Δκ
  → ∇·T/∇×T
  → LoopBreak(∇×T)
  → R(H,ΔⁿB{♥,ξ,Ω,σ,μ},Δκ)
  → 𝒞(Ψᴺ)
  → N_fiṭrī ∧ ʿaql ṣarīḥ
  → T_lang: Ψᴺ ⇢ Ψᴵ
```

Runtime compaction is valid only if each transition receives the law and prior state it needs when it becomes live. The architecture must support an unknown-at-design-time noetic structure and arbitrary runtime burden/submove topology. Shard selection may depend on validated structure, owner IDs, operations, registers, route state, and unresolved pressure. It must not depend on smoke case ID, topic label, a Torah-specific answer template, or a precomputed burden count.

The OSM paper is used only as a bounded engineering analogy: matching final output shape is weaker than preserving the route/state sequence. Here, package shape and final checker PASS are endpoint evidence. Call-context manifests and capsule transitions provide route evidence.

## Five Whys

1. **Why can a package contain the right law while a call lacks it?**  
   Package membership, module-map reachability, and dispatch-index text are static availability controls. No current call-context artifact binds selected package bytes to the prompt or host context for a particular call.

2. **Why is there no call-context binding?**  
   Prompt-pack instrumentation was intentionally additive observability over already-composed prompts, and capsule emission was intentionally implemented as a parallel artifact that never changed prompt composition.

3. **Why did the capsule remain parallel after the runtime law said calls receive it?**  
   The rollout separated schema/checker/emission work from transport integration. The docs and hot law advanced to the intended architecture while the runner remained at the measurement-only wave.

4. **Why can deterministic gates still pass?**  
   Each gate validates its own local contract: shard topology, cold-law hashes, capsule shape, prompt size, or package shape. None owns the cross-artifact join `package -> resolver -> prompt/context -> response -> next capsule`.

5. **Why did no owner close the cross-artifact join?**  
   Build/package availability, route selection, prompt instrumentation, capsule replay, and promotion evolved as separately green contracts; the release gate never required one content-addressed owner to prove `package component -> resolver selection -> actual call input -> response acknowledgment -> next capsule` for every dependent call.

Severity: runtime-footprint preservation is the engineering thesis of v0.4.6.0-wip. If compact law is merely available but not delivered, the system can preserve formal vocabulary while losing the operations needed to generate arbitrary noetic topology and reconstruct its trajectory.

**Actionable root owner/source:** the call-context transport and proof join between generated package artifacts and `tools/run_staged_current_skill_smoke.py`, with supporting schema/checkers in prompt-pack, state-capsule, route-shard, cold-law, and no-model package-only isolation surfaces.

This root does not establish a model regression. `regression_status` remains `unproven`.

## Hansei

### What worked

- Root compaction is measurable and reversible.
- Cold law is retained verbatim and hash-bound instead of deleted.
- Route shards preserve module homes and reject dead/unmapped shards.
- Stage07 mandatory output shards are explicitly named.
- The default execution package still ships omnibus owner bodies and route shards.
- Prompt-pack and capsule instrumentation create strong foundations for exact delivery evidence.
- The current no-model suite catches many static regressions.
- Documentation often states non-claims and package/host uncertainty honestly.

### What failed

- Architecture prose moved from "measurement" to "call receives" before transport did.
- `shards_loaded` was populated from expected stage policy, not observed prompt binding.
- `cold_law_refs_used` had no operational producer or binding.
- "Available through a map" was described as "loaded."
- The prompt manifest measured size but not component identity or source.
- Harness stage instructions became a second effective runtime law surface.
- Late harness repairs were easy to read as skill-runtime recovery even though canonical runtime source did not change.
- Earlier planning risked responding by re-inlining the full manual contract, which would abandon the footprint objective rather than solve delivery.

### Lesson

The runtime-footprint invariant is not:

```text
all laws are somewhere in the archive
```

It is:

```text
every live obligation has a content-addressed owner;
the resolver selects it from validated runtime state;
the call receives the exact bounded component;
the next state records delivery and declared use truthfully;
missing law routes HOLD/PARTIAL rather than fake Land;
and the public/witness trajectory reconstructs the same transitions.
```

## Evidence Vocabulary

The implementation must stop using one word, "loaded," for several states.

| Evidence level | Meaning | Machine-provable? | Permitted claim |
| --- | --- | --- | --- |
| `available` | File/clause exists in the bound package | Yes | Package availability only |
| `reachable` | Module/clause is mapped from an index/pointer | Yes | Static reachability only |
| `selected` | Pure resolver chose component for this call | Yes | Selection decision only |
| `delivered` | Exact component bytes/hash are bound to prompt or host context receipt | Yes | Context delivery only |
| `producer-declared-used` | Model response names a delivered component | Yes as self-attestation | Producer declaration, not cognition proof |
| `operation-bound` | Stage owner/operation and checker evidence require a module delivered for that operation | Yes structurally | Structural use/license evidence |
| `semantically-effective` | Law actually shaped correct reasoning | Not fully machine-decidable | Human/adversarial review only |

No tool may translate `available`, `reachable`, or `selected` directly into `delivered` or `used`.

## Target Contract 1: Runtime Call-Context Manifest

Add `schema/runtime-call-context.schema.json` with schema `daee-runtime-call-context-v1`.

One manifest is written **before** every model invocation. Required shape:

```json
{
  "schema": "daee-runtime-call-context-v1",
  "case_id": "gate88-secularism",
  "stage": "02",
  "call_index": 2,
  "runtime": {
    "delivery_mode": "explicit-prompt-components",
    "package_profile": "execution-mini",
    "package_sha256": "64-lowercase-hex",
    "build_manifest_sha256": "64-lowercase-hex",
    "skill_root_sha256": "64-lowercase-hex",
    "source_commit": "40-lowercase-hex"
  },
  "input": {
    "sha256": "64-lowercase-hex"
  },
  "state_capsule": {
    "bootstrap": false,
    "path": "state-capsules/capsule-001.json",
    "sha256": "64-lowercase-hex",
    "included": true
  },
  "selection": {
    "basis_kind": "stage-policy | owner-module-map | structural-trigger | mandatory-release",
    "basis_ids": ["stage-02-layer-a-diagnostic-ir"],
    "candidate_shards": ["references/runtime-diagnostic-core.md"],
    "selected_shards": ["references/runtime-diagnostic-core.md"],
    "status": "selected",
    "hold_reason": null
  },
  "components": [
    {
      "component_id": "state-capsule",
      "kind": "state-capsule",
      "source_path": "state-capsules/capsule-001.json",
      "sha256": "64-lowercase-hex",
      "byte_count": 1,
      "delivery": "prompt-bound",
      "prompt_start_byte": 1,
      "prompt_end_byte": 2
    }
  ],
  "cold_law_clauses_delivered": [],
  "prompt": {
    "path": "prompts/stage-02-layer-a-diagnostic-ir.prompt.md",
    "sha256": "64-lowercase-hex",
    "byte_count": 1,
    "transport_frame_est_tok": 1,
    "runtime_component_est_tok": 1,
    "effective_context_est_tok": 2
  },
  "non_claims": [
    "delivery does not prove internal model attention",
    "structural context fidelity is not semantic truth"
  ]
}
```

The sample values illustrate field types; tests use real nonzero byte counts and hashes. They are not output-mass thresholds.

### Delivery modes

Controlled modes:

```text
explicit-prompt-components
host-skill-context-receipt
unverified-host-ambient
```

- `explicit-prompt-components`: the harness embeds exact bytes with canonical component markers and can prove prompt offsets/hashes.
- `host-skill-context-receipt`: the host supplies a machine-readable receipt naming exact package/component hashes. This mode is owner/host integration work.
- `unverified-host-ambient`: the model may have skill context, but no receipt exists. This mode cannot satisfy promotion.

Claude's context-sterile no-tools lane cannot claim package delivery unless the required components are explicitly embedded. Merely naming `skill/SKILL.md` in the prompt is not delivery.

## Target Contract 2: Canonical Component Envelope

Explicitly delivered components use a deterministic envelope:

```text
----- BEGIN DAEE COMPONENT: component-id; sha256=64-lowercase-hex -----
exact component bytes
----- END DAEE COMPONENT: component-id -----
```

The context checker must:

1. Read the final prompt bytes.
2. Locate each envelope exactly once.
3. Hash the enclosed bytes.
4. Compare source path/hash/byte count with package or capsule source.
5. Verify recorded byte offsets.
6. Reject undeclared runtime-sized residual components.
7. Reject a manifest component not present in the prompt.
8. Reject prompt runtime components not present in the manifest.
9. Reject path traversal outside the extracted package/run directory.
10. Bind the prompt hash before model invocation.

This proves delivery. It does not prove internal attention.

## Target Contract 3: Pure Runtime-Context Resolver

Add `tools/runtime_context_resolver.py` as a pure resolver. Inputs:

- extracted `execution-mini` package root;
- stage ID;
- validated previous stage record;
- previous validated capsule, except Stage01 bootstrap;
- generated `compiled-module-map.json`;
- generated `cold-law-manifest.json`;
- dispatch index from generated `SKILL.md`;
- current output-mode/stage policy.

Forbidden resolver inputs:

- smoke case ID as a routing key;
- topic labels such as Torah, Qur'an, secularism, Khaybar, Trinity, or TST;
- expected burden/submove counts;
- expected conclusion or answer text;
- historical golden output text.

### Structural selection basis

The resolver may use:

- stage-specific mandatory context;
- selected/held noetic frames;
- live registers;
- route targets;
- owner IDs and operations;
- module IDs and source owners;
- unresolved route state;
- MRP result type;
- release mode;
- validated ambiguity state.

### Stage context table

| Stage | Prior capsule | Mandatory context | Conditional context | Failure behavior |
| --- | --- | --- | --- | --- |
| 01 intake | Bootstrap: none | Hot kernel/intake boundary and exact raw input | None | Fail intake; no downstream artifact |
| 02 diagnostic IR | Capsule 001 | Diagnostic core and compact IR law | IR-support/diagnostic shard only when structural trigger is live | HOLD/PARTIAL if required owner unavailable |
| 03 routing | Capsule 002 | `runtime-core-routing.md` | Pipeline/diagnostic/IR shard selected from validated Stage02 state | Ambiguous: select bounded candidates under existing cap or HOLD `route-ambiguous` |
| 04 ACT execution | Capsule 003 | Owner/module-map excerpt and operation contract | Exact owner omnibus section; `clause.execution-mandate-detail` when hard/manual depth is live | `cold-law-not-loaded` or owner-not-available; never fake Land |
| 05 MRP/reread | Capsule 004 | Recursion/MRP route law | Owner/dependency shard selected from Stage04/05 state | HOLD/PARTIAL/RECURSE as required |
| 06 witness/NAR | Capsule 005 | Witness/NAR and trajectory reconstruction law | IR-support or audit shard when reconstruction pressure is live | No closure if trajectory cannot reconstruct |
| 07 public release | Capsule 006 | `runtime-shard-output-release.md` and `runtime-shard-render-contract.md` | Proof-tail/order cold clauses and restoration shard only when structurally triggered | Release waits; no kernel-only rendering |
| 08 verifier | No model call | Registry/custody/checker context | Sidecar builders and replay tools external to execution-mini | Quarantine incomplete evidence |

The existing route-shard candidate cap is a context-footprint safeguard with an explicit HOLD/PARTIAL escape. It is not a burden or submove cardinality cap and must never truncate noetic topology.

### Owner module resolution

For M/P/V/E/F/DO/NS owners, resolve the original module ID through `compiled-module-map.json` to an exact omnibus section. Package co-location proves availability only. Delivery requires that exact section or bounded excerpt to appear as a manifest component.

For cold law, resolve the clause ID through `cold-law-manifest.json`, verify its anchored span hash, and deliver only the exact clause span required. Do not re-inline the entire manual contract.

## Target Contract 4: State Capsule Becomes Actual Handoff

Preserve `daee-state-capsule-v1` for legacy replay. Add a migration mode in the checker and runner rather than silently redefining historical captures.

Release-bearing new runs must satisfy:

1. Stage01 emits capsule 001 after validation.
2. Stage02 call manifest binds capsule 001 into the call.
3. Each later call binds the immediately preceding valid capsule.
4. A missing/invalid capsule prevents the call; it is not replaced by reconstructed prose.
5. The call-context manifest records delivered shards and clauses.
6. The response may emit `context_ack` naming the context-manifest hash and producer-declared-used components.
7. Declared-used components must be a subset of delivered components.
8. The next capsule's `shards_loaded` is derived from delivered shard components, not stage ID.
9. `cold_law_refs_used` is populated only from a validated producer declaration and remains explicitly self-attested.
10. Operation-bound checker evidence separately verifies that selected owners had their containing module section delivered.

The schema descriptions and docs must say:

- `shards_loaded` means call-context-delivered shards under a bound manifest;
- `cold_law_refs_used` means producer-declared use of delivered clause IDs;
- neither field proves internal cognition;
- no value may be inferred solely from stage number.

Changing these meanings under v1 is incompatible with historical replay. Contribute the context-delivery fields to the packet's single shared `daee-state-capsule-v2` migration and retain v1 reader support only for legacy replay. Every new release-bearing run uses v2. Compatibility tests decide which v2 fields may be conditionally absent at bootstrap, but they do not decide the version or permit release-bearing v1. Do not create a load-path-specific v2, and do not allow mixed semantics.

## Target Contract 5: Prompt-Pack Manifest v2

Keep v1 reader support. Add `daee-prompt-pack-manifest-v2` with:

- prompt SHA-256;
- runtime package/build/root hashes;
- context-manifest path/hash;
- component path/hash/byte offsets;
- delivery mode;
- transport-frame bytes/tokens;
- runtime-component bytes/tokens;
- capsule bytes/tokens;
- local-excerpt bytes/tokens;
- effective-context total;
- `includes_full_runtime` and `includes_prior_full_output`;
- no-model structural non-claims.

The current 20,000-estimated-token prompt ceiling governs the transport frame that previously excluded host skill context. It must not be silently applied as if it described all delivered runtime components. V2 must validate two budgets separately:

1. transport-frame budget;
2. aggregate effective-context budget from `load-path-budget.config.json`.

These are input-context safety budgets. They are not output byte floors and do not constrain burden/submove cardinality. If required context exceeds the governed budget, route HOLD/PARTIAL with the exact unmet component. Do not truncate noetic topology or fake Land.

## Target Contract 6: Package-Faithful Versus Harness-Assisted Lanes

Define two explicit lanes:

### `package-faithful`

- Runtime law comes only from one hash-bound `execution-mini` package.
- Resolver reads generated package files, not `atomics/skill/**`.
- Runner supplies generic transport framing, exact raw input, previous capsule, selected package components, and local excerpt.
- Runner may validate or reject; it may not invent route topology, owner operations, resultants, graph edges, or closure.
- Normalization may repair transport syntax only when fully recorded and when raw versus normalized artifacts are retained.
- This is the only lane eligible for package-behavior promotion.

### `harness-assisted`

- Current rich prompt guidance and diagnostic normalization may remain for development.
- Every added instruction and repair is recorded in a harness assistance ledger.
- Results are labeled `harness-assisted` and cannot prove execution-mini default behavior.
- A law that repeatedly must be taught by the harness becomes a candidate canonical-runtime/context-delivery defect, not permanent hidden scaffolding.

No result may silently cross lanes.

## Exact Owner and Edit Map

### Canonical runtime source to modify

- `atomics/skill/references/rubrics/manual-contract-digest.md`
  - distinguish availability, reachability, selection, delivery, declared use, and operation binding;
  - correct the statement that map reachability plus runner surface "counts as loaded";
  - retain the multi-call capsule law hot;
  - require manifest-bound delivery or honest HOLD/PARTIAL.
- `atomics/skill/references/rubrics/non-droppable-manual-contract.md`
  - keep exact cold clauses and dispatch addendum in lockstep;
  - add no full-manual re-inline;
  - clarify cold-law delivery evidence.
- `atomics/skill/SKILL.md`
  - add only the compact invariant and pointer required by the compiler layout;
  - do not paste the full delivery protocol into every hot section.
- `atomics/skill/references/diagnostics/recursive-state-transitions.md`
  - define prior-capsule-to-next-call transition and HOLD/PARTIAL when context is unavailable.
- `atomics/skill/references/diagnostics/framework-pipeline.yaml`
  - map call-context manifest ownership if this control-plane schema accepts the artifact; do not turn it into runtime routing code.

### New source/checker surfaces

- `schema/runtime-call-context.schema.json`
- `tools/runtime_context_resolver.py`
- `tools/check_runtime_context_delivery.py`
- `tests/runtime-context-delivery/valid/bootstrap-stage01/`
- `tests/runtime-context-delivery/valid/stage02-prior-capsule-diagnostic-core/`
- `tests/runtime-context-delivery/valid/stage04-owner-module-section/`
- `tests/runtime-context-delivery/valid/stage04-cold-execution-clause/`
- `tests/runtime-context-delivery/valid/stage07-mandatory-release-shards/`
- `tests/runtime-context-delivery/valid/ambiguous-route-hold/`
- `tests/runtime-context-delivery/invalid/capsule-not-in-prompt/`
- `tests/runtime-context-delivery/invalid/shard-selected-not-delivered/`
- `tests/runtime-context-delivery/invalid/stage07-shards-stage-derived-only/`
- `tests/runtime-context-delivery/invalid/cold-clause-hash-mismatch/`
- `tests/runtime-context-delivery/invalid/declared-used-not-delivered/`
- `tests/runtime-context-delivery/invalid/package-path-escape/`
- `tests/runtime-context-delivery/invalid/case-id-routes-shard/`
- `tests/runtime-context-delivery/invalid/live-pressure-zero-candidate-without-hold/`
- `tests/runtime-context-delivery/invalid/ambiguous-over-cap-without-hold/`
- `tests/runtime-context-delivery/invalid/prompt-hash-drift/`
- `docs/runtime-context-delivery.md`

### Existing tooling to modify

- `tools/run_staged_current_skill_smoke.py`
  - add package-faithful mode;
  - resolve and bind call context before invocation;
  - feed prior capsule after Stage01;
  - derive capsule delivery fields from context manifest;
  - retain harness-assisted mode with explicit label;
  - hard-fail manifest emission in promotion-eligible mode.
- `tools/check_prompt_pack_budget.py`
  - support v2 and effective-context budgets;
  - verify component hashes/offsets and call-site parity structurally.
- `tools/check_state_capsule.py`
  - join capsule sequences to call-context manifests;
  - enforce previous capsule delivery and delivered/declared-use subset laws.
- `schema/state-capsule.schema.json`
  - clarify field semantics if v1-compatible; otherwise add a v2 schema and retain v1.
- `tools/check_route_shard_selection.py`
  - keep all current static checks;
  - add resolver parity, not model behavior claims.
- `tools/check_cold_law_digest.py`
  - keep static hash/pointer checks;
  - align wording so it does not claim call-level delivery.
- `tools/measure_load_path_budget.py`
  - consume v2 effective-context component classes for deterministic reports.
- `tools/load-path-budget.config.json`
  - add only measured component-class gates after implementation; never bank headroom.
- `tools/daee_dry_run_emulator.py`
  - generate no-model call-context manifests through Stage01-Stage08 fixtures.
- `tools/run_no_model_preflight.py`
  - add runtime-context delivery and no-model package-only isolation gates.
- `tools/run_local_ci.py` and `tools/ci_registry.json`
  - require resolver/context checker self-tests.
- `tools/build_package_shape_inventory.py`
  - preserve generated inventory but label host/package availability separately from delivery.

### Documentation to modify

- `docs/load-path-architecture.md`
- `docs/load-path-token-budget.md`
- `docs/recursive-state-capsule.md`
- `docs/source-vs-runtime-layout.md`
- `docs/compiled-runtime-tools.md`
- `docs/runtime-harness-onboarding.md`
- `docs/non-claims.md`
- `docs/proof-class-taxonomy.md`
- `docs/four-smoke-release-playbook.md`, generalized by the five-smoke plan

### Generated files not to hand-edit

- `skill/SKILL.md`
- `skill/compiled-module-map.json`
- `skill/build-manifest.json`
- `skill/cold-law-manifest.json`
- `skill/references/**`
- `docs/audits/package-shape-inventory.md` if regenerated by `tools/build_package_shape_inventory.py`
- generated docs/index surfaces

Regenerate from atomics/tool owners after source edits.

### Existing package surfaces to reuse without redesign

- `execution-mini` remains the default package profile.
- `audit-full` remains audit-only and cannot satisfy package-faithful behavior evidence.
- Omnibus modules remain shipped but cold/owner-gated.
- The one-line eager substantive path and dispatch-index architecture remain.
- Stage07 mandatory release/render shards remain fixed post-gate loads.

## Required Fixture Lattice

### Valid

1. Stage01 bootstrap with no prior capsule and a hash-bound kernel/input component.
2. Stage02 receives capsule 001 and diagnostic core.
3. Stage03 receives capsule 002 and one unambiguous route shard.
4. Stage03 ambiguous structural triggers select multiple candidates within the current shard cap and record the basis.
5. Stage03 ambiguity beyond the context cap routes HOLD/PARTIAL without deleting candidate noetic states.
6. Stage04 owner operation resolves to the exact omnibus module section and selected route shard.
7. Stage04 hard/manual operation receives `clause.execution-mandate-detail` exact span.
8. Stage05 receives recursion/MRP context and previous capsule.
9. Stage06 receives witness/reconstruction context and previous capsule.
10. Stage07 receives both mandatory release shards regardless of topic.
11. Stage08 has no model call and validates all context manifests against capsules/prompts.
12. One no-model package-only synthetic run uses an extracted execution-mini tree with no atomics access.
13. One host-receipt fixture proves exact package component hashes without literal prompt embedding.
14. One low-context case remains compact because no conditional shard is live.
15. One high-topology neutral fixture selects context from runtime state without fixed burden/submove assumptions.

### Invalid

1. Stage02 omits capsule 001.
2. Capsule path exists but hash differs.
3. Shard is selected in the manifest but absent from prompt/receipt.
4. Shard path is in the prompt but source hash differs from package.
5. Stage07 capsule names mandatory shards but prompt contains neither.
6. Cold-law clause ID is declared used but not delivered.
7. Delivered clause bytes do not match manifest span hash.
8. Resolver reads `case_id` or a topic token to select a shard.
9. Live pressure has zero candidate owner/shard and no HOLD/PARTIAL.
10. Ambiguity exceeds the existing shard cap and silently chooses one.
11. Context manifest is emitted after the model call.
12. Prompt changes after manifest creation.
13. Package root changes after context resolution.
14. Harness-assisted run is labeled package-faithful.
15. Audit-full package is used to prove execution-mini behavior.
16. Full manual contract is re-inlined.
17. Prior full output is replayed instead of a local excerpt.
18. Missing context is repaired by inventing route/owner/graph data after the model response.

## Test-Driven Implementation Sequence

### Phase 0: Freeze branch and comparator truth

```powershell
$root = 'C:\Users\theis\Documents\Codex\2026-07-08\dae'
$repo = "$root\work\daee-v46-branch"
$v45 = "$root\work\daee-v45-tag"
$head = '6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c'
$base = '56d023e910810e94f36b1e5e2623d568852bf28b'
$main = 'c86b3c6673147b8802fe222373a165a37d4d24a8'
if ((git -C $repo rev-parse HEAD) -ne $head) { throw 'STALE PLAN: PR head drifted' }
if ((git -C $repo rev-parse origin/main) -ne $main) { throw 'STALE PLAN: origin/main drifted' }
if ((git -C $v45 rev-parse HEAD) -ne '8c14e28fbcf440275f4d143a9b7cadc6148aa5a9') { throw 'STALE PLAN: v45 checkout drifted' }
$repoStatus = git -C $repo status --short --branch --untracked-files=all
$v45Status = git -C $v45 status --short --branch --untracked-files=all
if (($repoStatus | Select-Object -Skip 1).Count -ne 0) { throw 'STOP: PR worktree dirty' }
if (($v45Status | Select-Object -Skip 1).Count -ne 0) { throw 'STOP: v45 worktree dirty' }
$shallow = git -C $repo rev-parse --is-shallow-repository
if ($LASTEXITCODE -ne 0) { throw 'cannot determine shallow-clone state' }
if ($shallow -ne 'true') { Write-Warning 'checkout is no longer shallow; refresh ancestry evidence instead of assuming drift' }
git -C $repo cat-file -e "$base^{commit}"
if ($LASTEXITCODE -ne 0) { throw 'PR base object unavailable' }
```

Expected: all assertions pass and shallow-clone state is recorded. GitHub PR #8/#9 metadata, captured separately in the comparator ledger, is the authoritative relationship evidence. A local merge-base result is never interpreted without first accounting for clone depth.

Record file sizes/blobs:

```powershell
$comparators = @(
  @{Name='v45'; Repo=$v45; Ref='HEAD'},
  @{Name='pr-base'; Repo=$repo; Ref=$base},
  @{Name='pr-head'; Repo=$repo; Ref=$head},
  @{Name='main'; Repo=$repo; Ref=$main}
)
$rows = foreach ($x in $comparators) {
  [pscustomobject]@{
    Name = $x.Name
    SkillBytes = [int](git -C $x.Repo cat-file -s "$($x.Ref):skill/SKILL.md")
    SkillBlob = git -C $x.Repo rev-parse "$($x.Ref):skill/SKILL.md"
    AtomicBytes = [int](git -C $x.Repo cat-file -s "$($x.Ref):atomics/skill/SKILL.md")
    AtomicBlob = git -C $x.Repo rev-parse "$($x.Ref):atomics/skill/SKILL.md"
  }
}
$rows | Format-Table -AutoSize
```

Expected planning baseline: values match the evidence table above. Drift triggers plan review, not automatic failure of the new branch.

### Phase 1: Preserve current static controls

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
python tools\check_route_shard_selection.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'route-shard self-test failed' }
python tools\check_route_shard_selection.py
if ($LASTEXITCODE -ne 0) { throw 'live route-shard check failed' }
python tools\check_cold_law_digest.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'cold-law self-test failed' }
python tools\check_cold_law_digest.py
if ($LASTEXITCODE -ne 0) { throw 'live cold-law check failed' }
python tools\check_state_capsule.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'state-capsule self-test failed' }
python tools\check_prompt_pack_budget.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'prompt-pack self-test failed' }
```

Expected: all exit `0`. These remain static/structural controls and must stay green throughout implementation.

### Phase 2: Add call-context schema and right-reason checker

1. Add schema and valid/invalid fixtures first.
2. Implement `check_runtime_context_delivery.py` with a pure validator.
3. Pin exact diagnostics for each invalid fixture.
4. Do not import the staged runner into the checker; keep composition and validation separable.

Commands:

```powershell
python tools\check_runtime_context_delivery.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'runtime-context self-test failed' }
python tools\check_runtime_context_delivery.py --fixtures tests\runtime-context-delivery
if ($LASTEXITCODE -ne 0) { throw 'runtime-context fixture lattice failed' }
```

Expected: exit `0`; every valid case passes and every invalid case fails for its pinned class.

Right-reason negative command:

```powershell
$case = 'tests\runtime-context-delivery\invalid\shard-selected-not-delivered\context-manifest.json'
$raw = python tools\check_runtime_context_delivery.py --manifest $case --explain
$code = $LASTEXITCODE
if ($code -ne 1) { throw "expected exit 1, got $code" }
$diag = $raw | ConvertFrom-Json
if ($diag.earliest_stage -ne '03') { throw "expected earliest stage 03, got $($diag.earliest_stage)" }
if ($diag.failure_class -ne 'selected-component-not-delivered') { throw "wrong class: $($diag.failure_class)" }
```

Expected diagnostic JSON:

```json
{
  "status": "fail",
  "failure_class": "selected-component-not-delivered",
  "earliest_stage": "03"
}
```

Rollback: remove schema/checker/fixtures together. Never retain a manifest claim with no validating consumer.

### Phase 3: Implement the pure resolver

1. Parse generated module map, dispatch index, cold-law manifest, and stage state.
2. Return a deterministic selection object without reading case ID/topic text.
3. Resolve owner modules to exact package sections.
4. Resolve cold clauses to exact anchored spans.
5. Return HOLD/PARTIAL status on missing or over-ambiguous context.
6. Unit-test aliases and owner-module homes.

Commands:

```powershell
python tools\runtime_context_resolver.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'runtime-context resolver self-test failed' }
python tools\check_route_shard_selection.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'resolver drifted from route-shard contract' }
python tools\check_cold_law_digest.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'resolver drifted from cold-law contract' }
```

Expected: all exit `0`.

Topic-independence mutation:

```powershell
python tools\check_runtime_context_delivery.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'case-id/topic routing negative fixture survived' }
```

The self-test must hold structural stage state constant while changing case ID/topic prose and prove the resolver output is unchanged.

### Phase 4: Compose and bind exact call context

1. Add deterministic component envelopes.
2. Build the context manifest before each call.
3. Hash the final prompt before invocation.
4. In package-faithful mode, manifest emission or validation failure aborts before model invocation.
5. Keep harness-assisted observability warnings only in the explicitly labeled non-promotion lane.
6. Retain prompt and context manifest as paired artifacts.

No-model commands:

```powershell
python tools\run_staged_current_skill_smoke.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'staged harness self-test failed after context composition' }
python tools\check_prompt_pack_budget.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'prompt-pack v2 self-test failed' }
python tools\check_runtime_context_delivery.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'context prompt-binding self-test failed' }
```

Expected: all exit `0`; self-tests prove context manifest precedes invocation and prompt hash drift is rejected.

### Phase 5: Make prior capsule an actual call input

1. Keep Stage01 bootstrap explicit.
2. After Stage01, load the previous canonical capsule, validate it, and bind it as a prompt component.
3. Remove full compact-stage replay only after capsule/local-excerpt parity proves no required state is lost.
4. During migration, if both are present, assert they agree; never let compact state silently override capsule state.
5. Derive next capsule `shards_loaded` from the call-context manifest.

Commands:

```powershell
python tools\check_state_capsule.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'capsule self-test failed' }
python tools\check_runtime_context_delivery.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'capsule/context join self-test failed' }
python tools\run_staged_current_skill_smoke.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'harness capsule-input self-test failed' }
```

Expected: all exit `0`.

Fixture replay command after CLI extension:

```powershell
python tools\check_state_capsule.py --replay tests\runtime-context-delivery\valid\stage02-prior-capsule-diagnostic-core\state-capsules --context-manifest tests\runtime-context-delivery\valid\stage02-prior-capsule-diagnostic-core\call-context-manifest.jsonl
if ($LASTEXITCODE -ne 0) { throw 'capsule/context replay failed' }
```

Negative replay:

```powershell
python tools\check_state_capsule.py --replay tests\runtime-context-delivery\invalid\capsule-not-in-prompt\state-capsules --context-manifest tests\runtime-context-delivery\invalid\capsule-not-in-prompt\call-context-manifest.jsonl
$code = $LASTEXITCODE
if ($code -ne 1) { throw "expected missing-capsule rejection exit 1, got $code" }
```

Canonical acceptance command:

```powershell
python tools\assert_expected_rejection.py --expectation tests\runtime-context-delivery\invalid\capsule-not-in-prompt\call-context-manifest.expectation.json --artifact-root auto
```

Expected: exit `0`; the helper pins the affected call stage, exact context-delivery class/subcode, downstream invalidation, and absence of dependent-call/promotion artifacts.

### Phase 6: Package-only deterministic isolation

This phase builds only a temporary local package after separate implementation authorization. It does not publish or install anything.

1. Rebuild generated runtime from atomics.
2. Verify freshness and package shape.
3. Build an execution-mini archive into a unique temp directory.
4. Extract it into an isolated directory.
5. Run the resolver/context composer with the extracted package as its only runtime root.
6. Deny access to atomics, repo docs, and audit-full tools as runtime-law sources.
7. Verify every selected component hash against archive bytes.

Exact future commands:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
if ((git status --short --untracked-files=all | Measure-Object).Count -ne 0) { throw 'package-only isolation test requires a clean worktree' }
python tools\build_compiled_runtime.py
if ($LASTEXITCODE -ne 0) { throw 'compiled runtime build failed' }
python tools\check_compiled_runtime_freshness.py
if ($LASTEXITCODE -ne 0) { throw 'compiled runtime freshness failed' }
git diff --quiet --
if ($LASTEXITCODE -ne 0) { throw 'runtime rebuild changed tracked files; commit/re-authorize before package isolation' }
git diff --cached --quiet --
if ($LASTEXITCODE -ne 0) { throw 'package-only isolation may not use staged changes' }
$unexpectedUntracked = @(git ls-files --others --exclude-standard)
if ($unexpectedUntracked.Count -ne 0) { throw "runtime rebuild created untracked repository files: $($unexpectedUntracked -join ', ')" }
python tools\check_package_shape.py
if ($LASTEXITCODE -ne 0) { throw 'package shape failed' }
$scratch = Join-Path ([System.IO.Path]::GetTempPath()) ("daee-package-faithful-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $scratch | Out-Null
$archive = Join-Path $scratch 'daee-epistemics-v0.4.6.0-wip-execution-mini.skill.zip'
$extract = Join-Path $scratch 'extracted'
python tools\package_skill.py --profile execution-mini $archive
if ($LASTEXITCODE -ne 0) { throw 'temporary execution-mini package build failed' }
python tools\check_skill_package_artifact.py --profile execution-mini $archive
if ($LASTEXITCODE -ne 0) { throw 'temporary execution-mini package shape failed' }
Expand-Archive -LiteralPath $archive -DestinationPath $extract -ErrorAction Stop
python tools\check_runtime_context_delivery.py --package-root $extract --package-only-self-test
if ($LASTEXITCODE -ne 0) { throw 'package-only context delivery self-test failed' }
```

Expected: all exit `0`; the package-only deterministic self-test reports no atomics/audit-full dependency and no network/model call. It is not a model-evidence lane.

This command sequence was not run during planning.

### Phase 7: Correct runtime and documentation claims

1. Replace "counts as loaded" with exact availability/delivery vocabulary.
2. Correct capsule docs to describe current and target waves truthfully.
3. Keep `check_cold_law_digest` claims static.
4. Document package-faithful and harness-assisted evidence separately.
5. Regenerate runtime and generated docs.

Commands:

```powershell
python tools\build_compiled_runtime.py
if ($LASTEXITCODE -ne 0) { throw 'runtime rebuild failed' }
python tools\check_compiled_runtime_freshness.py
if ($LASTEXITCODE -ne 0) { throw 'runtime freshness failed' }
python tools\check_cold_law_digest.py
if ($LASTEXITCODE -ne 0) { throw 'cold-law digest failed after wording correction' }
python tools\check_route_shard_selection.py
if ($LASTEXITCODE -ne 0) { throw 'route-shard lockstep failed after wording correction' }
python tools\check_docs_claim_boundaries.py
if ($LASTEXITCODE -ne 0) { throw 'docs claim-boundary check failed' }
```

Expected: all exit `0`; compiled root and cold copies are regenerated from canonical source.

### Phase 8: Layered comparison ledger

After implementation, create a machine-readable comparator report. It must keep four questions separate:

| Question | Comparator |
| --- | --- |
| What is in the inherited main layer? | current main `c86b3c6673147b8802fe222373a165a37d4d24a8` |
| What did PR #8 hardening add? | main `c86b3c6...` -> PR8 head/PR9 base `56d023e...` |
| What code did PR #9 introduce? | PR9 base `56d023e910810e94f36b1e5e2623d568852bf28b` -> PR9 head |
| Does release-line behavior differ? | controlled v0.4.5.0 package -> v0.4.6.0-wip package, under Plan 01 custody |

Exact code-attribution commands:

```powershell
$repo = 'C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch'
$base = '56d023e910810e94f36b1e5e2623d568852bf28b'
$head = '6987c9ebf1de45af700b1fa74b1ed25ec0beeb7c'
git -C $repo diff --stat $base $head
git -C $repo diff --name-status $base $head -- atomics skill schema tools docs tests
git -C $repo log --oneline --decorate $base..$head
```

Expected at planning baseline: 28 PR commits and the known runtime-footprint surfaces. Any new head requires a refreshed ledger.

Late-cycle surface assertion:

```powershell
$files = git -C $repo diff --name-only a46e00f $head
$atomics = @($files | Where-Object { $_ -like 'atomics/skill/*' })
$generatedRoot = @($files | Where-Object { $_ -eq 'skill/SKILL.md' })
if ($atomics.Count -ne 0 -or $generatedRoot.Count -ne 0) {
  throw 'late-cycle canonical-runtime surface changed; refresh harness-only inference'
}
```

Expected at planned head: assertion passes. The result means only that this tail changed tools/tests, not that all 28 PR commits were harness-only.

Behavior comparison remains owner-gated and must use Plan 01's manifests. Until then:

```yaml
regression_status: unproven
runtime_footprint_amplifier: hypothesis
```

### Phase 9: Integrate deterministic preflight

```powershell
python tools\runtime_context_resolver.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'resolver self-test failed' }
python tools\check_runtime_context_delivery.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'context-delivery self-test failed' }
python tools\check_prompt_pack_budget.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'prompt-pack self-test failed' }
python tools\check_state_capsule.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'capsule self-test failed' }
python tools\check_route_shard_selection.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'route-shard self-test failed' }
python tools\check_cold_law_digest.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'cold-law self-test failed' }
python tools\measure_load_path_budget.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'load-path arithmetic self-test failed' }
python tools\measure_load_path_budget.py --enforce-ratchet --enforce
if ($LASTEXITCODE -ne 0) { throw 'load-path gates failed' }
python tools\run_staged_current_skill_smoke.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'staged harness self-test failed' }
python tools\run_no_model_preflight.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'preflight self-test failed' }
python tools\run_no_model_preflight.py
if ($LASTEXITCODE -ne 0) { throw 'composed no-model preflight failed' }
```

Expected: all exit `0`. No model is invoked.

## Stage01-Stage08 Load-Path Acceptance Map

### Stage01: Intake bootstrap

Owner inputs:

- exact raw input hash;
- generated hot kernel/intake contract;
- no prior capsule.

Required proof:

- call-context manifest exists before invocation;
- bootstrap is explicit;
- case ID is custody only;
- prompt/package hashes are bound.

STOP:

- resolver uses case ID or topic to route;
- package identity is unknown;
- call manifest is post-hoc.

### Stage02: Noetic state and Diagnostic IR

Owner inputs:

- capsule 001;
- diagnostic core;
- Plan 02 observation/pressure inventory contract;
- selected conditional diagnostic/IR support only when structurally live.

Required proof:

- capsule 001 exact bytes are delivered;
- diagnostic components are package-bound;
- candidate-state/pressure topology is not precomputed by smoke ID.

STOP:

- compact prior state substitutes for a missing capsule without an explicit migration parity record;
- input pressure is omitted and later reconstructed by the harness.

### Stage03: Route and owner gate

Owner inputs:

- capsule 002;
- core routing;
- validated Stage02 state;
- selected route shards/module map.

Required proof:

- selection basis IDs are structural;
- ambiguous candidates are preserved or HOLD/PARTIAL;
- no selected shard is absent from delivered context.

STOP:

- one candidate is silently chosen beyond the existing context cap;
- a live owner is declared unavailable without checking module-map resolution.

### Stage04: Burden execution and ACT

Owner inputs:

- capsule 003;
- exact owner module/omnibus section;
- exact operation contract;
- execution-mandate cold clause when required.

Required proof:

- each operation-bound owner maps to a delivered component;
- body-ref/operation evidence joins the selected module;
- missing law produces HOLD/PARTIAL, not a fabricated ACT/Land row.

STOP:

- the runner teaches owner-specific law not present in package components and calls the lane package-faithful;
- context budget pressure drops owner obligations.

### Stage05: MRP, reread, and recursion

Owner inputs:

- capsule 004;
- recursion/MRP contract;
- generated/held/pre-empted lifecycle state;
- dependency context.

Required proof:

- prior capsule is delivered;
- generated burdens remain Stage05-owned;
- next-burden shard/context requirement is recorded before RECURSE.

STOP:

- route topology is manufactured by a normalizer;
- no-new-resultant is accepted without the governing reread law being delivered.

### Stage06: Witness and NAR

Owner inputs:

- capsule 005;
- witness/reconstruction contract;
- exact owner/ACT/MRP trajectory refs.

Required proof:

- witness is built from delivered state and prior operations;
- no map availability is called consultation;
- field witness cannot close over context missing from the route.

STOP:

- a boolean or label substitutes for reconstructible witness state;
- closure is assembled from harness-only template law.

### Stage07: Public projection

Owner inputs:

- capsule 006;
- mandatory output-release shard;
- mandatory render-contract shard;
- applicable proof-tail/restoration cold clauses;
- bounded local prior excerpts only.

Required proof:

- both mandatory shard bytes are prompt/receipt-bound;
- Stage07 capsule derives `shards_loaded` from the context manifest;
- prompt pack does not replay full prior output;
- package-faithful and harness-assisted labels are explicit;
- Plan 11 release profile passes structurally.

STOP:

- Stage07 shard list is inferred solely from stage ID;
- kernel-only rendering proceeds;
- a section expansion uses fixed output mass as a proof substitute.

### Stage08: Verifier and custody

No model call occurs.

Required proof:

- all call-context manifests validate;
- capsule sequence and context manifests join one-to-one after Stage01;
- package/prompt/component hashes verify;
- Plan 11 promotion profile runs;
- Plan 01 custody is complete.

STOP:

- context manifest is missing;
- any required component is only `available/reachable`, not delivered;
- structural PASS is promoted to semantic truth or regression proof.

## Five-Smoke Integration

Required case IDs:

- `gate88-secularism`
- `gate88-khaybar`
- `gate88-trinitarian-j173`
- `gate88-tst-lillard`
- `gate88-torah-quran-source-authentication`

For each fresh authorized Stage01-Stage08 run:

1. Use one exact hash-bound execution-mini package per matrix lane.
2. Emit one call-context manifest before every Stage01-Stage07 model call.
3. Deliver the immediately prior capsule to Stage02-Stage07.
4. Resolve shards and owner modules from validated runtime state, never case ID.
5. Deliver mandatory Stage07 shards in every case.
6. Record package-faithful versus harness-assisted mode.
7. Preserve failed calls and manifests; no selective retry can overwrite them.
8. Pass Plan 11 promotion profile and Plan 02 topology adjudication separately.
9. Treat one failed case as a stopped matrix, not an average.
10. Keep structural PASS non-semantic.

The fifth source-authentication fixture contains only the exact owner-supplied prompt. It must not contain an expected shard list, burden count, submove count, output byte range, response outline, citation list, or theological conclusion. The runtime may legitimately select source-authentication owners because the input's diagnosed structure requires them; the fixture must not preselect them.

After owner-authorized runs exist under the fixed directory convention, verify context artifacts with:

```powershell
Set-Location C:\Users\theis\Documents\Codex\2026-07-08\dae\work\daee-v46-branch
$matrixRoot = '.daee\v0.4.6.0-wip-five-smoke\promotion-candidate-01'
$cases = @(
  'gate88-secularism',
  'gate88-khaybar',
  'gate88-trinitarian-j173',
  'gate88-tst-lillard',
  'gate88-torah-quran-source-authentication'
)
foreach ($case in $cases) {
  $run = Join-Path $matrixRoot $case
  if (-not (Test-Path -LiteralPath $run)) { throw "missing run: $run" }
  python tools\check_runtime_context_delivery.py --run-dir $run
  if ($LASTEXITCODE -ne 0) { throw "context delivery failed: $case" }
  python tools\check_state_capsule.py --replay (Join-Path $run 'state-capsules') --context-manifest (Join-Path $run 'call-context-manifest.jsonl') --artifact (Join-Path $run 'output.md')
  if ($LASTEXITCODE -ne 0) { throw "capsule/context replay failed: $case" }
  python tools\check_prompt_pack_budget.py --manifest (Join-Path $run 'prompt-pack-manifest.jsonl')
  if ($LASTEXITCODE -ne 0) { throw "prompt-pack budget failed: $case" }
}
```

This verification block does not authorize creating those runs.

## Rollback

- Preserve the current static shard/cold-law/package/capsule controls throughout migration.
- If call-context integration must be reverted, revert resolver, schema, prompt composition, capsule parity, and docs as one unit.
- A rollback returns the evidence status to `call-context-delivery: unverified`; it does not restore claims that static reachability proves load.
- Preserve generated context manifests and failed fixture outputs until triage completes.
- Never re-inline the full manual contract as an emergency workaround.
- Never remove package modules to meet context budgets; selection controls context, package shape preserves availability.
- If a required component exceeds budget, route HOLD/PARTIAL with the exact component and reopen condition.
- If a host cannot provide a context receipt, label it `unverified-host-ambient` and exclude it from promotion.
- If package-faithful model execution is blocked, harness-assisted testing may continue as development evidence, but it cannot close this ANDON.

## STOP / ANDON Conditions

Stop and write a terminal record if:

- a runtime call after Stage01 does not receive the previous validated capsule;
- selected shard or cold-clause bytes are absent from the bound prompt/receipt;
- `shards_loaded` is inferred from stage ID rather than context evidence;
- `cold_law_refs_used` names an undelivered clause;
- docs or reports call availability/reachability "consultation";
- package membership is treated as context injection proof;
- harness-only instructions or normalizers are represented as package behavior;
- audit-full is used to prove execution-mini behavior;
- resolver logic keys on smoke case ID, topic, expected burden/submove count, or answer outline;
- missing context causes silent topology loss, owner loss, or fake Land instead of HOLD/PARTIAL;
- the full manual contract or full prior output is replayed to bypass selection;
- context budget changes bank headroom without current measurement;
- main/head tree comparison is described as a causal Git diff;
- PR-base attribution and v45 behavior comparison are conflated;
- structural context delivery is described as semantic truth or actual model attention;
- `regression_status` is advanced without Plan 01 controlled evidence;
- a model smoke, package publication, issue, commit, push, tag, release, or external publication is attempted without separate authorization.

Terminal record:

```yaml
status: BLOCKED | PARTIAL | UNVERIFIED
andon_class: context-not-delivered | capsule-not-transported | shard-selection | cold-law-binding | package-parity | harness-contamination | budget | claim-overreach
case_id: case-or-fixture
stage: "01" | "02" | "03" | "04" | "05" | "06" | "07" | "08"
call_index: integer-or-null
delivery_mode: explicit-prompt-components | host-skill-context-receipt | unverified-host-ambient
package_sha256: hash-or-null
context_manifest_sha256: hash-or-null
prompt_sha256: hash-or-null
prior_capsule_sha256: hash-or-null
selected_components: component-ids
delivered_components: component-ids
missing_components: component-ids
failing_command: exact-command
owner_source: file-and-function
next_action: one-concrete-action
preserved_artifacts: paths-and-hashes
regression_status: unproven
```

`BLOCKED`, `PARTIAL`, and `AUDIT_COMPLETE` are mutually exclusive terminal claims for one active abnormality.

## Adversarial Review Applied

The proposed delivery design was attacked against the present code and footprint objective. These attacks changed the final plan.

| Adversarial attack | Failure in a weaker design | Adopted countermeasure | Proof fixture/gate |
| --- | --- | --- | --- |
| Prompt inclusion does not prove model attention | A manifest could overclaim cognition | Separate delivered, producer-declared-used, operation-bound, and semantically-effective evidence | `declared-used-not-delivered` plus non-claim schema tests |
| Package membership does not prove context delivery | An archive can be complete while a host injects nothing | Require explicit component binding or a hash-bound host receipt | `shard-selected-not-delivered` fixture |
| Host receipts can be self-attested or opaque | A label saying "skill loaded" is not component evidence | Receipt must identify package and component hashes; otherwise mode is `unverified-host-ambient` | Invalid host-receipt fixture in context checker |
| A resolver can become a hidden argument bank | Case IDs or topic words could select expected law/owners | Forbid topic/case inputs and run metamorphic case-ID/topic mutations with fixed stage state | `case-id-routes-shard` fixture |
| A stage policy can fabricate selection evidence | Stage07 currently fills shard names from stage ID | Derive delivered fields from the pre-call manifest and exact prompt/receipt; stage policy only supplies mandatory candidates | `stage07-shards-stage-derived-only` fixture |
| Feeding both compact state and capsule can create two truths | One can silently override the other | Migration parity gate; disagreement stops; remove compact replay only after proof | Capsule/compact-state mismatch fixture |
| Explicit components can rebuild the 300k eager path | Delivery repair could abandon the footprint goal | Resolve exact shard/clause/module section; keep aggregate budget and HOLD/PARTIAL escape | Full-runtime-reinline and over-budget fixtures |
| A shard cap can become a noetic-topology cap | Context limit could silently discard burdens or candidate states | Cap applies only to co-loaded context; preserve topology and route HOLD/PARTIAL when unresolved | Ambiguous-over-cap-without-hold fixture |
| Harness instructions can still substitute for package law | A package-only label could hide a rich second runtime in the runner | Separate package-faithful and harness-assisted lanes; context manifest classifies every component source | Harness-labeled-package-faithful fixture |
| An external resolver has repo access during package tests | It could read atomics and make the package appear sufficient | Extract execution-mini into isolation and enforce package-root-only runtime reads | Package-only self-test with denied atomics paths |
| Main versus PR head can be presented as one causal change | The verified stack contains an inherited-main layer, a PR8 hardening layer, and a PR9 runtime-footprint layer | Use PR9 base/head for PR9 code attribution; preserve intermediate lineage cells for behavior; use v45/head only as a confounded release-line comparison | Comparator ledger plus GitHub PR8/PR9 relationship assertions |
| More context can be mistaken for better output | Input context budget can become an answer-length quota | Keep context budgets separate from output mass; no output byte/count gate | Docs claim-boundary and no-output-quota scan |
| Five smoke cases can become five argument banks | Fixture-specific expected shards/topologies could leak | Store exact input only; derive context from stage state; metamorphic topic independence | Fifth-fixture metadata audit |

Rejected countermeasures:

- Re-inline the full manual contract into the hot root.
- Replay the full prior output on every call.
- Remove owner modules from the package to make it smaller.
- Treat static hash parity as proof of call delivery.
- Treat a model's component acknowledgment as proof of internal reasoning.
- Use the Torah/Qur'an case ID to preselect source modules or response structure.
- Solve thin output with fixed byte, burden, or submove floors.
- Claim PR #9 regression from root-size correlation.

## Definition of Done

- Static shard, cold-law, package, prompt-budget, and capsule tests remain green.
- Every Stage01-Stage07 model call has a pre-invocation call-context manifest.
- Every Stage02-Stage07 call receives the immediately previous validated capsule.
- Selected package components are content-addressed and bound to prompt bytes or a valid host receipt.
- `shards_loaded` is derived from delivered context, not stage identity.
- Declared cold-law use is a subset of delivered clauses and is labeled self-attestation.
- Resolver inputs are structural and topic/case-ID independent.
- Missing or over-ambiguous context routes HOLD/PARTIAL without truncating noetic topology.
- Stage07 always receives both mandatory release shards.
- Package-faithful and harness-assisted lanes cannot be confused in artifacts or scorecards.
- Execution-mini package-only deterministic isolation passes without atomics/audit-full runtime dependencies; package-faithful model evidence remains a separate A13/A14 gate.
- Prompt-pack v2 reports effective context faithfully and preserves current budget ratchets.
- No full-manual re-inline and no prior-full-output replay occurs.
- Documentation distinguishes availability, reachability, selection, delivery, declared use, operation binding, and semantic effectiveness.
- PR9 attribution uses PR9 base/head; GitHub's main-to-PR8-to-PR9 stack remains explicit; v45 behavior comparison remains separately custody-controlled.
- All five fresh authorized smokes eventually pass Stage01-Stage08 with valid context/capsule joins.
- Structural PASS does not claim semantic truth, model attention, uptake, provenance beyond bound artifacts, or regression causality.
- `regression_status` remains `unproven` until controlled comparison evidence exists.

## Confidence

Confirmed capsule/prompt mismatch: **HIGH; directly present in current source.**  
Static availability-versus-delivery gap: **HIGH; directly present in current check scopes.**  
Call-context manifest, resolver, and package-only deterministic test plan: **YES, implementation-ready.**  
State-capsule migration: **implementation-ready; v1 is legacy replay only and v2 is mandatory for new release-bearing runs. Field optionality is mechanically decided in Phase 5.**  
Package-faithful live model behavior: **OWNER/ARTIFACT gated; no run authorized or performed.**  
Runtime-footprint amplifier as cause of thin output: **UNPROVEN hypothesis.**  
PR #9 regression causality: **UNPROVEN.**
