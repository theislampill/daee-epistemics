---
id: diagnostic-render-contract
module_class: governance
canonical_path: skill/references/rubrics/diagnostic-render-contract.md
contract_version: "0.4.0.0"
load_when:
  - deciding how visibly structured the response should be across default, :dsl, and internal audit surfaces
catalogue_registered: false
---

# Diagnostic Render Contract

PACK-SPEC note: this file functions as a render contract owner. For future normative edits, use
`docs/spec-authoring-pack.md`; keep uppercase MUST / SHOULD / MAY intentional and backed by
examples or checks.

## Function

This file governs how visibly structured the output is. It runs after the output-release rubric has confirmed what may be released, and before the public response is shaped. It also requires an internal post-render gate before closure; visible gate fields are surface-specific. It does not replace routing, does not determine what is diagnosed, and does not determine what is eligible for release. Render shape follows diagnosis; it does not govern it. The default `/daee-epistemics` surface is the canonical compact DSL-governed runtime: readable bounded governed response with a mandatory noetic-field execution banner, compact DSL/IR header, hidden premises, per-released-operation Core Formulation, bounded operation, state/noetic re-read, one Restorative Response, and one final Closing Formulation. It is not prose-only mode. `/daee-epistemics:dsl` exposes expanded diagnostic/IR visibility; it is not the first place DSL governance appears. Internal/development audit render is retained for regression, pass-review, and architecture testing compatibility.

## Canonical Render Mode Syntax

```text
/daee-epistemics
/daee-epistemics:dsl
/daee-epistemics < C:\path\input.md > C:\path\output.md
```

- `/daee-epistemics` means the canonical compact DSL-governed surface: readable bounded governed prose plus a mandatory noetic-field execution banner, compact DSL/IR header, and state/noetic re-read. It exposes enough compiler trace to prevent clean essay surface-compliance failure while still prohibiting raw Diagnostic IR, full Case State, `matched_modules`, route ledger, and load ledger.
- `/daee-epistemics:dsl` means expanded diagnostic/IR visibility: compressed Diagnostic IR or Case State, live burden sequence, held routes, state re-read, and STOP / HOLD / RECURSE / PARTIAL.
- `/daee-epistemics < input.md > output.md` means canonical file-retained execution: read the case from `input.md`, write the full canonical compact DSL-governed answer to `output.md`, and keep the chat response to status only. This is not the optional script-capable route/check harness; it is the default runtime using a file output transport for hosts whose final-chat channel compresses hard cases.

`/daee-epistemics:audit` is deprecated as a public render mode. It is retained only as an internal/development compatibility surface for regression review, bundle/source-basis inspection, and procedural debugging. Default mode must not depend on `:audit` for governance visibility.

The former external recursive-audit prompt is deprecated as a normal invocation pattern. Its useful discipline is internalized into the skill; use `:dsl` when expanded diagnostic/IR visibility is desired.

**Core render invariant:** Full recursive-audit discipline runs in every surface. The surface determines how much diagnostic machinery is printed, not whether recursion occurs.

**Default Output Surface Invariant.** For plain `/daee-epistemics`, internal governance is
mandatory and default visibly prints the noetic-field execution banner as first visible content,
then the compact DSL/IR header and bounded governed response. Clarifying or missing-input replies
are still runtime outputs and must begin with the banner. Do not put prose, headings, apologies,
Markdown fences, or clarifying questions before it. The banner is a render obligation produced
from the same classification state as Layer A. The first visible surface must not collapse into
a bare `field:` line. It must show a governed execution signature such as compact box art or an
equivalent banner with `NOETIC FIELD EXECUTION` plus these fields:

```text
╔══════════════════════════════════════════════════════╗
║ daee-epistemics — NOETIC FIELD EXECUTION             ║
║ field: <LOCAL CLAIM | NAMED WORLDVIEW | SOURCE-AUTHENTICATION | MIXED NOETIC FIELD>
║ user task: <RESPOND | REFUTE | DIAGNOSE | EXPLAIN | SOURCE-AUTHENTICATION | OTHER>
║ external source request: <NONE EXPLICIT | IMPLICIT | EXPLICIT>
║ authority frame: <NONE DETECTED | LIVE>
║ state: <RECURSE | PARTIAL | COMPLETE>
╚══════════════════════════════════════════════════════╝
```

Print exactly one value for each field; never print the choice list or combine values with `|`.
The banner must distinguish the user's task from an external source request: `/daee-epistemics
refute:` renders `user task: REFUTE` even when `external source request: NONE EXPLICIT`.
Default release status is governed, not shallow or governance-hidden. When control-relevant,
it must include the burden-cycle, operative submove, pre-release route-gradient pressure `∇` in
Layer A's gate/release decision, `Δκ`, target-explicit `∇·` / `∇×` state in `R(H,Δ)`, any
licensed `LoopBreak(∇×T)`, closure-field status, and PARTIAL / RECURSE / COMPLETE decision needed to prevent false closure.
It should still avoid long explanatory formalism unless that explanation is needed for the
user-requested audit or formalism task.
Do not use SIMPLE, COMPACT, CANONICAL, HARD, or SOURCE-ORDER as banner categories or depth
licenses. External source request and authority frame are distinct: do not mark external source
request `IMPLICIT` merely because a worldview or authority frame is live. If a
source-authentication case supplies no actual text/reference, classify external source request as
`IMPLICIT`, authority frame as `LIVE`, user task as `SOURCE-AUTHENTICATION`, and state as
`PARTIAL`.
Field classification must not flatten named theological/worldview authority frames. If the input
is a local claim but it is governed by a named theological or worldview frame and the response
actively contrasts or restores through an Islamic restoration frame, render `field: MIXED NOETIC
FIELD` (or the repo-native mixed/named-worldview equivalent), not `LOCAL CLAIM`.

Layer A is the compact diagnostic/control surface: it identifies and licenses the live noetic
burden, source/noetic frame, held material, release decision, and current bounded operator. It
does not argue, prove itself indefinitely, or spawn another burden. Layer B is the governed
operation/release surface: it performs active TTP/operator submoves and releases only what is
needed to land the current burden. Layer A overgrowth and Layer B flattening are both render
failures.
Layer A may carry explicitly input-anchored held burdens, but it should not pre-list every
foreseeable downstream escape route before any burden has landed. Speculative downstream replies
belong to `MRP(ⁿB)` when `Land(ⁿB)` and `R(H,Δ)` make them live. A Layer A that prints the whole
refutation chain as an initial inventory without showing why each node is already input-anchored
has collapsed route-gradient reread into a static topology board.

Burden recursion is licensed by live noetic order, not topic availability. Layer A must identify
whether the live burden is first-order (surface claim), second-order (criterion, warrant,
proof-method, source-authority, testimony standard, moral tribunal, epistemic rule), or
higher-order/meta-noetic (source-worldview transfer, autonomy/desire as authority,
identity-protective discourse, grief/register, source-status inversion, noetic-frame collapse).
This is noetic governance, not formatting: it asks whether the noetic function is truth-directed
or deformed, whether the warrant-process is reliable or routed through an unreliable criterion,
and what the case treats as basic versus inferred. Hidden premises, source-rules, proof-methods,
and tribunals can function as foundations even when they are not named by the user.
If `R(H,Delta)` shows only another topic in the same order/function/source-frame, keep it as
Layer B submove or application. If a different order remains live, release the next burden-cycle
or explicitly HOLD/PARTIAL it.

```text
/daee-epistemics  = full recursive traversal operationally + mandatory noetic-field banner
                  + mandatory compact DSL/IR header + prose-first bounded governed response
                  + state/noetic re-read
                  + one Restorative Response + one final Closing Formulation
                  + no full ledger / no full IR dump
/daee-epistemics < input.md > output.md = same canonical surface written to file
                  + final chat reports file/status only
/daee-epistemics:dsl    = full recursive traversal operationally + expanded formal Layer A / IR visibility
/daee-epistemics:audit  = deprecated internal/development audit compatibility only
```

**Named invariant:** Full recursion in every mode; compact DSL/IR header in default; full ledger only in internal/development audit.

Notation mirror: `ⁿB` names the n-th burden, `ⁿBᵢ` names the i-th operative submove inside
that burden-cycle, and `ⁿBᵢ[OPᵢ]` attaches the owner/operator. `nBi` is the plain-text
equivalent. `B1.s1` remains an accepted legacy/checker alias for `¹B₁` where needed. Default
prose may still say "Burden 1" and "operative submove"; public governed notation should use the
canonical burden/submove forms, while ASCII aliases belong in checker/dev-harness traces or
explicit machine-facing fallback fields.

Public canonical output should prefer `¹B`, `²B`, `¹B₁[FPD]`, `¹B₂[M1-P]`,
`²B₁[definition-discipline]`, `Land(¹B)`, `MRP(¹B)`, and `¹B → ²B`. Use `1B1`,
`1B2`, `2B1` or `B1`/`B2` only as ASCII fallback. `B1.s1` / `B<N>.s<M>` remains a
legacy/checker alias and should not be the primary public notation unless the output is explicitly
a checker/dev-harness trace.

Expanded formalism render boundary: full algebraic exposition belongs by default to
theory/specification docs, `:dsl` visibility, or internal audit surfaces. Default output must
print short formal governance markers when they are control-relevant to the current execution:
route-gradient `∇` markers in Layer A gate/release decision such as `∇ route: B2 pressure highest — B2 has highest dependency-reduction yield over held B3/B4`, `ΔⁿB`, `Δκ`,
target-explicit `∇·` / `∇×` markers in `R(H,Δ)` such as `∇·κ`, `∇×κ`, `∇·B`, or `∇×ξ`,
`LoopBreak(∇×T)` when a loop-breaker is licensed, `R(H,Δ)`, `R(H,Delta)`, PARTIAL,
RECURSE, or COMPLETE. Use `R(H,Δ)` as the formal notation and `R(H,Delta)` only as the
ASCII fallback.
`del-dot` and `del-cross` are ASCII aliases for `∇·` and `∇×`; when they appear in
default governed output they must be compact, target-explicit, and control-bound, not long
formalism exposition or separate operators.
The expanded formal reread is `R(H, ΔⁿB{♥,ξ,Ω,σ,μ}, Δκ)`; the expanded ASCII fallback is
`R(H, Delta-nB{heart,xi,Omega,sigma,mu}, Delta-kappa)`. Do not print
`IR(N,m,τ,σ,♥,ξ,Ω,μ,κ)` as a raw default header, do not conflate Delta with del/nabla, and
do not treat expanded notation as proof that a register or owner has executed.

Allowed default compact marker examples: `State: Δκ live; ∇·κ positive; ∇×κ unresolved;
R(H,Δ): RECURSE.` `Burden field: ΔⁿB landed; ∇·B positive over B3/B4; ∇×B unresolved
around compact-neutrality dependency.` `MRP(¹B): Route-gradient points to ²B generated-by
MRP(¹B) because Δ¹B exposed a translation tribunal not present in the initial inventory.`
Forbidden default exposition examples: `The antisymmetric Jacobian of the noetic field shows...`;
`The ∇× symbol proves the TTP executed.`

Anti-symbol-theater rule: visible notation must be backed by a local control effect. If a
render names `♥`, `ξ`, `Ω`, `μ`, `κ`, `Δκ`, plain `∇`, `∇·`, `∇×`,
`LoopBreak(∇×T)`, `R(H,Δ)`, `𝒞(Ψᴺ)`, `T_lang: Ψᴺ ⇢ Ψᴵ`, or
`N_fiṭrī ∧ ʿaql ṣarīḥ`, the same pass must show the burden, owner, hold/release decision,
reread, dependency pressure, loop-breaking, closure-field status, coupling boundary, or
restoration boundary that the symbol changed. Otherwise use ordinary prose and keep the notation
in the theory/spec layer.

Conditional LoopBreak render: do not require a decorative `LoopBreak:` line in every ordinary
output. When field diagnostics are rendered and `∇×T` was checked, the loopbreak surface must be
explicit: non-null cyclic pressure requires target, ground, `Δ` effect, reread, and resulting
hold/closure state; null cyclic pressure requires compact `LoopBreak: not needed`, `not licensed`,
or equivalent. If cyclic pressure was not checked, do not imply that a loopbreak occurred.

Reread witness floor: a visible `R(H,Δ)` / `R(H,Delta)` line must name actual reread content, not
only the symbol. Compact equivalents are acceptable, but the state/noetic re-read must recover
held set, live remainder, newly released or newly blocked routes, and next eligible
STOP/HOLD/PARTIAL/RECURSE/COMPLETE status when those surfaces govern release.

Initial burden enumeration gate: the `Initial burden set` used by the Closure/Reconstruction
Witness must be declared from the pre-release Layer A / Diagnostic IR burden enumeration before
terminal states are rendered. MRP-generated burdens discovered during `R(H,Δ)` are
`generated-by: MRP(ⁿB)` resultant nodes; they are not silently inserted into the original initial
set. If a later node was already in the initial set, classify the MRP route as
`held_burden_activation`; if it was not fully present until the post-landing reread, classify it as
`generated_burden_instantiation` and instantiate the node with Layer A, Layer B, owner-bearing
submoves, and Land/HOLD accounting. If the render cannot distinguish the initial set from newly
released or newly generated material, closure must be HOLD, PARTIAL, or RECURSE rather than
COMPLETE.
Generated-burden evidence must also name the route-gradient: what changed in `ΔⁿB`, which
`ξ`/`Ω`/concealment/dependency pressure now pulls the field toward the new node, why `∇·B` is
non-neutral or newly directed, and why `∇×κ` is not merely a loop unless LoopBreak is licensed.
The visible MRP block and the closure-witness `MRP resultants` ledger must agree on this lineage:
an already-initialized held node cannot be called generated in the ledger merely because MRP
authorized the route edge. A generated ledger entry requires a matching `[generated-by: MRP(ⁿB)]`
burden node and normal Layer A/B accounting.

Closure witness floor: `𝒞(Ψᴺ)` is agent/runtime-side closure only. When printed, it must identify
the agent execution-field decision or status (COMPLETE, STOP, HOLD, PARTIAL, or RECURSE) and must
not claim interlocutor acceptance, conversion, persuasion, guidance, or soul access.

Transfer-boundary witness floor: `T_lang: Ψᴺ ⇢ Ψᴵ` is a partial coupling relation at the public
output boundary, not an isomorphism, not a surjection, and not a guaranteed update operator on
the diagnosed interlocutor field. A render may show that the response preserves identity and
addresses the diagnosed burden; it may not claim uptake.

---

## Relation to Output-Release Rubric

The output-release rubric answers: *what may be released now, and in what order?*

This file answers: *how visibly structured should that release be?*

A response may pass the output-release rubric at the default compact surface or the expanded diagnostic/IR surface. The render contract selects the surface and governs the visible shape within that surface. It never determines what is eligible; it governs how eligible material appears.

---

## Render Surfaces

### Default Canonical Compact DSL-Governed Surface

**Use when:**
- The user invokes plain `/daee-epistemics` ? regardless of case complexity.
- The user did not invoke `:dsl`.
- The user did not explicitly request diagnostic trace, DSL output, lab-report render, source-basis trace, pass-review, or internal/development audit.

Case complexity alone does not trigger expanded `:dsl` visibility. A case with multiple live burdens and a plain `/daee-epistemics` invocation still uses the default compact DSL-governed surface. The full recursive traversal runs internally; only the visible machinery differs.

**Full recursion still required in the default compact surface:**
Recursive-audit discipline runs in every surface. Surface visibility determines how much diagnostic machinery is printed, not whether recursion occurs.
The same-response RECURSE trigger checklist still governs the default compact surface internally: if the current blocker cleared, another already-present burden remains live, and no stop/hold/gate/limit blocks it, the answer must continue through the next bounded prose move rather than rendering prose closure.

```text
claim being assessed
→ upstream criterion / tribunal / hidden premise
→ first-order content
→ higher-order burden
→ downstream entailments
→ adjacent already-present distortions
→ state re-read
→ STOP / HOLD / RECURSE / PARTIAL
```

This traversal must be visible through the mandatory compact DSL/IR header plus state-transition progression, not printed gate machinery. The response progresses through live burdens before final synthesis:

```text
bounded move
→ state re-read: what cleared
→ what remains live
→ next eligible burden
→ decision
→ next bounded move when internally licensed, or prose partial status when limits block it
```

If same-response recursion is internally licensed in the default compact surface, visible progression must include a short
prose state transition: what the prior move cleared, what remains live, why that live
burden was already present in the original input, and why the next bounded move is now
eligible. Bare essay headings such as "Move 1", "Move 2", or "Move 3" do not satisfy
RECURSE. They are section ordering unless the refreshed-state relation is stated.

TTP activation must also be operational, not merely named. Saying "the M1 move" or
"the M8 move" does not prove the TTP ran. The output must reflect the bounded operation
selected by the validated case-state / IR while avoiding a `matched_modules` ledger in
default mode.
Default render should exhaust the live structure made available by the user's input, not
minimize visible execution. Address as many input-anchored live burdens and materially active
submoves as release gates permit. Distinct active burdens, criteria, source/noetic frames,
theological targets, restoration vectors, and TTP/operator functions must not be merged into
a generic paragraph or a single all-purpose operation before burden accounting. If runtime, response, or
interaction limits prevent completion, mark the next live burden PARTIAL instead of closing.
Visible `Operation:` lines must begin with a closed operative verb from the existing
operator grammar: `split`, `distinguish`, `test against own grounds`, `disambiguate`,
`classify`, `audit`, `reclassify`, `narrow`, `expose`, `re-read`, `sequence`,
`refuse jurisdiction of`, or `clear`. Generic verbs such as `address`, `discuss`,
`explore`, `engage`, or `consider` are non-operative operation verbs.

### Release-Smoke Witness Capture Surface

**Use when:**
- The invocation or smoke runbook explicitly requests `release-smoke witness capture mode`.
- The output is a local package-bound release-gate smoke, not an ordinary user-facing chat reply.

**Rules:**
- Preserve the default governed answer; do not replace execution with a trace, route dump, or
  marker list.
- Make the witness surfaces literal and checker-readable because the purpose of this mode is
  release-gate capture from the final package.
- Required visible surfaces for `witness_required=true` cases:
  - noetic-field execution banner before all prose;
  - at least one literal `## Burden-Cycle N` section and a `State/noetic re-read` section
    with `What changed / cumulative-state delta:` and a prose `Release status:`;
  - compact Layer A with a non-empty `∇ route:` inside `gate/release decision`;
  - pre-release `initial burden set: [B1, ...]` before the closing witness;
  - target-explicit `Field diagnostics:` and `LoopBreak:` beside every released `R(H,Δ)` /
    `R(H,Delta)` state re-read;
  - `R(H,Δ):` / `R(H,Delta):` lines that state held material, live remainder or cleared field,
    newly released/blocked route where relevant, and STOP/HOLD/PARTIAL/RECURSE/COMPLETE status;
  - literal `## Closure/Reconstruction Witness` containing `Initial burden set`, `Terminal states`,
    `Burden dependency graph:`, `∇·B:`, `∇×κ:`, `𝒞(Ψᴺ):`, and `T_lang: Ψᴺ ⇢ Ψᴵ:`;
  - `Terminal states:` rendered as one parseable row per burden: `B1: cleared / <operator> /
    <target -> operation -> result or compact delta>`; do not put the burden title before the colon;
  - `∇·B:` rendered with a parseable leading status, for example `neutral / ...` or
    `non-neutral / <target-explicit status>`;
  - `∇×κ:` rendered with a parseable leading status, for example `null / ...`,
    `resolved / ...`, or `non-null / <target-explicit status>`;
  - `𝒞(Ψᴺ):` with explicit agent/runtime execution-field semantics and bounded closure status;
  - `T_lang: Ψᴺ ⇢ Ψᴵ:` with language-mediated partial-coupling boundary and no soul access,
    guaranteed uptake, or guidance-control claim;
  - literal `## Restorative Response` and `## Closing Formulation` after the closure witness.
- Hard/full closure must use those parseable field names exactly. Do not substitute
  a generic divergence-result field, a generic curl-result field, `remaining kappa`, standalone `coverage_complete=true`, or a
  prose-only closure license. In file-retained hard smokes, do not self-grant a size waiver:
  if the output remains near old compact-output size while claiming 5+ fully landed burdens,
  repeated MRP, graph accounting, closure, and restoration, continue expanding Layer B operations
  or route HOLD/PARTIAL with `coverage_complete=false`.
  Below the serious Andon band of roughly 60 KB, this is a hard gate: a 5+ burden full
  hard-compound answer must not self-close with `coverage_complete=true`. It must either continue
  expanding local Layer B work or write `coverage_complete=false` with HOLD/PARTIAL mass-boundary
  reason. Between roughly 60 KB and the calibrated 75 KB floor, closure requires external
  adjudicator waiver; the runtime itself should keep expanding or hold. For Smoke-6-shaped full
  traversal, target an approximate 80 KB safety margin before positive closure and spend the
  margin on reconstructible owner/submove, MRP-resultant, graph/field_witness, and closure-witness
  accounting rather than filler.
- Closure order is fixed. If final MRP emits `Route: STOP`, no further Layer B work,
  burden-local completion body, supplemental expansion, or submove block may appear after it.
  If more burden-local work is needed, render it before the final `Land(Bn)` and final stable
  MRP STOP, or route RECURSE/HOLD instead of STOP. Hard/full `Closure/Reconstruction Witness`
  must appear immediately after the final MRP record and before `Restorative Response` and
  `Closing Formulation`.
- Hard/full `Closure/Reconstruction Witness` must include an `MRP resultants:` ledger when MRP
  was invoked. Each line should identify the burden token, finding, graph/no-edge result, and
  route licensed by the MRP activation.
- This mode is evidence capture only. The witness block is not competence proof, not a truth
  meter, not public-release proof beyond the local package-bound smoke, and not a claim that every
  ordinary output always renders the full witness scaffold.

### Canonical File-Retained Execution

**Use when:**
- The invocation contains `< input-file`, `> output-file`, or an equivalent host-level
  instruction to read the case from a file and retain the governed answer in a file.
- The host/runtime's final-chat channel is likely to compress a hard, compound,
  deformed, or source-operative answer.

**Rules:**
- Read the case from the input file before diagnosis.
- Write the full canonical compact DSL-governed surface to the output file. The file
  contains the same default surface described above: compact Layer A, governed Layer B,
  burden-local operations, `Land(B)`, compact Delta/field diagnostics, `R(H,Delta)`,
  continuation/HOLD/PARTIAL/close, and restoration.
- Do not replace the file answer with a completion report. The final chat response
  only states the input file read, output file written, approximate length, and status:
  complete, HOLD, or PARTIAL. It must not add source links, sanity scans, checker notes,
  verification claims, or commentary.
- Do not invoke the optional script-capable route/check harness unless the user or
  maintainer explicitly asks for that harness. File-retained execution is scriptless
  canonical runtime with a different transport.
- Do not run repo checkers, route tools, smoke-artifact tools, or execution-fidelity
  checks as part of file-retained execution unless developer validation is explicitly
  requested. The final chat report may not add harness verdicts, `execution_fidelity`,
  route-plan claims, or source-audit commentary.
- If traversal cannot complete, write a PARTIAL answer to the output file and name
  the next live burden or blocked submove. Do not close thinly in the chat response.
- For hard or multi-burden file-retained answers, keep explicit `Land(Bn)` and
  `R(H,Delta)` attachment per released burden; do not replace them with a generic
  state paragraph.

Bash-style shells use `<` for input redirection and `>` for output redirection.
PowerShell supports `>` but stdin behavior differs. Because `/daee-epistemics` is
a skill invocation rather than a real shell command in every host, `< >` is
skill-level file-retained execution syntax where the host/agent supports file
reads/writes.

Minimum substantive operation requirement: each rendered operation must apply the
owner-specific operation floor, not merely show the words Target/Operation/Result. The
operation must pressure a live premise, predicate, criterion, warrant, or branch; the result
must change burden-state; and the state/noetic re-read must show the cumulative-state delta.
If the section shape is present but the claim-state does not narrow, collapse, clear, hold,
or become partial, the output is rubric-schematic and must be rewritten before emission.
Hard/compound/deformed cases have a depth floor across their own noetic structure: moral
protest, imported criteria, accountability/hiddenness, source-worldview transfer,
higher-order reason or authority, testimony/transmission, predication/attribute pressure,
necessary-knowledge disputes, and grief/register holds all require owner-faithful pressure.
A non-PARTIAL answer must be rich enough to land each released burden, not merely short
enough to pass marker checks. When the user explicitly asks for sources, revealed texts must
be quoted or precisely cited as operative instruments and immediately explained; bare citation
labels are source-thin surface compliance. Golden-depth execution is not length for its own
sake; it is the amount of owner-floor, source-operative, restoration-directed work needed to
make the burden actually land.
Optional script-harness `pressure_dimensions` are an implementation analogue for this rule, not a default
public-output field. In scriptless compact-DSL render, the pressure dimensions remain internal:
the prose must execute them by narrowing the actual premise, criterion, warrant, source-frame,
theological predicate, testimony question, register-hold, or restoration vector. An output
fails hard-case render if it names an owner but omits that owner's pressure, uses generic
Target/Operation/Result verbs, cites sources without making them operate on the active burden,
reaches `Land(B)` without a changed claim-state, or performs restoration without tying it to
the landed burden.
For source-request hard cases, source operation must cover the routed source functions, not
just produce a source list. If hujjah, guidance/non-compulsion, fitrah/ayat, mercy/justice,
repentance/return, testimony, or predicate discipline are distinct pressure points, the render
must make the relevant text operate on each pressure point or mark the omitted pressure PARTIAL.
Final restoration is not a back door for omitted source functions. If mercy/justice,
Creator-right, repentance/return, testimony, predication, or another source-governed
pressure remains live after state re-read, it must appear as a burden-local operative
submove or licensed next burden before closure. A closing paragraph that merely invokes
mercy, guidance, worship, authenticity, or textual precision without showing what source
work changed the claim-state is source-thin surface compliance.
Structural attachment is part of this requirement: the right labels appearing somewhere is
not enough. `Owner-floor`, `Target`, `Operation`, `Result`, `Land(B)`, and `R(H,Delta)` must
remain locally attached to the burden step they govern. Grouped owner lines followed later by
grouped operation lines, or a final global state-read blob, is structural flattening even when
every marker appears. Each `ⁿBᵢ` / `nBi` must stay locally attached to its owner-floor
Target/Operation/Result, and `Land(ⁿB)` must summarize the cumulative state delta from the
submoves inside that burden.

**Minimum visible transition spine (mandatory in multi-burden default):**
A live burden is an input-anchored noetic-state burden, not merely a topic mentioned in the
prompt. topic transition != recursion; component tour != recursion. State re-read enumeration
of remaining input-anchored live burdens + one newly routed bounded pass = recursion.

In any multi-burden case the response must include a minimum visible transition spine. The
minimum permitted form is:
"That clears [X]. The remaining live issue already present in the input is [Y]. The next
bounded step is [Z]."

The transition spine must mark case-state re-read, not topical movement. Each transition must
show what the prior operator cleared, what input-anchored live burden state re-read identified
as remaining, and what the next bounded step is. If no transition marker appears when state
re-read identifies a remaining input-anchored live burden and licenses a newly routed bounded
pass, the output is clean essay surface-compliance failure and must be rewritten before emission. A multi-burden
default answer without transition spine is invalid even if it is clean, accurate, and
well-written. Minimum visible transition spine is required for multi-burden default output.
Topic-organized output without state re-read transitions fails governed traversal.

When state re-read names a remaining input-anchored burden and no named gate blocks it,
Restorative Response and Closing Formulation are not yet licensed. Continue with the next
bounded burden-cycle. If response limits prevent that continuation, mark PARTIAL with the
next live burden instead of closing rhetorically.
Missing per-burden Layer A -> governed Layer B -> state/noetic re-read is a scriptless compact-DSL
render failure whenever another input-anchored burden remains live and unblocked.

For this gate, "input-anchored" includes supporting premises and contrast rules already
present in the user's surface discourse, not only separate requested questions. A public/private
partition, source-status rule, translation demand, or moral/epistemic criterion named in the
input remains eligible for recheck after the upstream blocker lands.
If the state re-read enumerates such remaining burdens, the render may not say "only if
requested" and then close unless it also names the hold gate blocking release. "This needs its
own bounded pass" means continue with that pass or mark PARTIAL.

**Final closure in multi-burden default (mandatory):**
In multi-burden default responses, final closure must include a brief prose confirmation that
no further same-input eligible burden remains, or must mark HOLD/PARTIAL with reason.
Allowed: "At this point the live burdens in the original statement have been handled at the
level needed for this response."
Forbidden: literal governance labels such as "Recursion decision: STOP".

**Required compact DSL/IR header for default (minimum visible form):**

Each default burden-cycle must follow this structure. Layer B is prose-first; Layer A and
state/noetic re-read use compact entries. Default Layer A is fit-for-purpose but mandatory:
it prints only the compact DSL/IR header needed to make the current pass governable. This
Layer A block is the compact diagnostic frame for default mode; it is not raw Diagnostic IR.
The full-field compact header is a deliberate anti-surface-compliance failure tradeoff:
even outputs that become brief after diagnosis still show the minimum compiler trace needed
to prove governed execution without exposing raw IR. Brevity is licensed only after
diagnostic burden accounting.

```text
## Burden-Cycle N
### Layer A ? Compact DSL/IR header
- read status: [dominant | distributed | underdetermined]
- confidence: [strong | provisional | low]
- claim_level: [first-order | meta-epistemic | meta-ontological | meta-noetic | cross-level]
- pattern_profile: [PF overlay or none]
- reason-category: [1 | 2 | 3 | 4]
- Concealment mode: [clear | mode-? | compact anchored mode; never `None detected`]
- deformation: [primary/secondary deformation read or none/underdetermined]
- DO-orient: [truth-seek | identity-perf | autotelic | zann-mode | mixed]
- live noetic burden: [input-anchored noetic-state burden governing this pass]
- current bounded operator: [what the operator does, by function ? not a module label]
- held: [what remains held and why, or none]
- source-status/noetic-frame: [selected operative frame and any non-operative status]
- decisive missing differentiator: [only when required]
- gate/release decision: [compact release status; no raw `Recursion decision:` label]

### Layer B ? bounded governed response

#### Hidden Premises
[Compactly name the hidden premise(s), imported criterion, concealment/deformation, or warrant disorder that governs the released operation.]

#### Burden / Operation 1
##### Core Formulation
[Local operative formulation: governing deformation/concealment/deviation; the noetic/modal pattern by which it functions; and the restoration vector by which sound order is recovered.]

##### Bounded Response / operative submoves
[Execute only the selected bounded operator and justified submoves for this released burden. Not a general essay. No meta narration.]

#### TTP/operator trace
[Required when a named operator performs runtime work. Use local owner-ID-bearing submoves
such as `¹B₁ [FPD] - expose the imported tribunal`, then keep target -> operation -> result
visible in case-specific prose. Do not print repo/dev-harness lines such as `Owner-floor:`
or `B<N>.s<M>` in canonical public output. This is not external citation support and not a
`matched_modules` dump, bibliography parade, scholar/source parade, school-label context,
genealogy, external theorist support, or public-render prestige support.]
If a module-backed owner is structurally live, a generic label such as "Operative submove 1"
or a later trace list is insufficient. The owner ID must appear on the local operative submove
itself. A trace may summarize executed owners only after the local submoves have already
shown their owner IDs, targets, operations, and results.

### State/noetic re-read
- Cleared:                      [what this live burden cleared]
- ∇ route:                      [why this burden was selected before release, or why the next selected burden has highest dependency-reduction yield over held alternatives; omit only when no route ordering was control-relevant]
- Remaining input-anchored burdens: [enumerated from original input, not a topic list]
- Held routes rechecked:        [result after this pass]
- Field diagnostics:            [target-explicit `∇·` / `∇×` status; include null when it licenses closure, RECURSE, or PARTIAL]
- [Mid-Reread Pressure]:        [mandatory when this reread releases next burden, HOLD/PARTIAL, LoopBreak, or closure; include Target, Reread, Landed delta, Pressure activations, ∇·T, ∇×T, Route-gradient, Finding, MRP route result type, MRP resultant, Graph delta, Pre-emption basis, Route, Boundary]
- LoopBreak:                    [not needed / licensed with target + ground + Δ effect + reread / held with reason]
- Next bounded pass:            [prose reason if another bounded pass is licensed]
- Release status:               [prose closure/hold/partial/continuation status, plus compact `R(H,Δ): RECURSE/PARTIAL/COMPLETE` marker when control-relevant; no raw `Recursion decision:` field]

### Closure/Reconstruction Witness
[Required before final Restorative Response when closing a multi-burden, register-active,
named-worldview, source-authentication, mixed-field, authority-frame, or hard compound case.
Compact, not a full ledger. The heading and labels are literal default governed output; do not
rename this block `Closure audit`, do not shorten `Burden dependency graph:` to `burden graph`,
and do not move `𝒞(Ψᴺ)` / `T_lang: Ψᴺ ⇢ Ψᴵ` into prose-only closure.]
- N frames:                     [selected primary N and held/candidate N with reason]
- Registers:                    [operative ♥/ξ/Ω/σ/μ/κ summary or resolved/held state]
- Initial burden set:           [`[B1, B2, B3]`; every input-anchored burden admitted to the scoped witness]
- Terminal states:              [one line per initial burden: `B1: landed / <operator> / <target -> operation -> result or compact delta>`; the burden ID must come immediately before the colon; do not write `B1 <title>: <state>`; allowed states are `landed`, `discharged-as-derivative`, `held-with-reason`, `carried-PARTIAL`, `carried-RECURSE`, `cleared`]
- Burden dependency graph:      [parseable compact graph; `A → B` means B depends on A landing first, `A ∥ B` means parallel / independent at this level, exact `(root)` means no upstream dependency; node IDs must match terminal-state burden IDs and the graph must be reconstructible from the visible witness text alone; ASCII `A -> B` is a legacy transport fallback only, not the preferred notation. Put any root gloss outside the parentheses: `B1 (root) - authority-order` is valid; `B1 (root authority-order)` is invalid.]
- ∇·B:                          [`neutral / <target-explicit status>` or `non-neutral / <target-explicit status>`]
- ∇×κ:                          [`null / <target-explicit status>`, `resolved / <target-explicit status>`, or `non-null / <target-explicit status>`]
- `𝒞(Ψᴺ)`:                     [positive agent/runtime execution-field closure condition: landed/integrated/held burdens, bounded ∇·, resolved/held ∇×, reconstructible route, no hidden live pressure]
- `T_lang: Ψᴺ ⇢ Ψᴵ`:           [final response is language-mediated coupling attempt, not soul access, guaranteed uptake, or control of guidance]

Coverage proof rule: bare `R(H,Δ)` and a bare graph are insufficient. The witness must identify
held set / live remainder / terminal state accounting. `coverage_complete` means every burden in
`Initial burden set` appears exactly once in `Terminal states`. `collapse_positive` requires
`coverage_complete`, `∇·B: neutral`, and `∇×κ: null` or `resolved`. Coverage alone is not COMPLETE
closure. If any burden is `held-with-reason`, `carried-PARTIAL`, or `carried-RECURSE`, the closure
language must not overclaim COMPLETE unless it explains why that scoped field is terminal without
live outward pressure or unresolved curl.

Valid dependency-graph example:

```text
B1 (root)
B1 → B2
B1 → B3
B2 ∥ B3
B2 → B4
B3 → B4
```

Counterexamples: `B1 then maybe B2`, `B1/B2 related`, and `B2 after the first thing` are not
parseable dependency graphs because they do not expose roots, directed dependencies, or parallel
relations with burden IDs.

When the final `R(H,Δ)` exposes an apparent new burden, graph movement should be licensed by
`TTP-MRP-mid-reread-pressure` or an equivalent source-owned reread-pressure check. Default routed
output must show a compact `[Mid-Reread Pressure]` block for every burden-cycle route. Ordinary
compact output omits it only when no burden-cycle route, HOLD/PARTIAL, LoopBreak, next burden, or
closure is being released.
When MRP is shown, `∇·T` and `∇×T` are active reread gates: non-neutral `∇·T` needs HOLD/RECURSE
or bounded explanation, and non-null `∇×T` needs LoopBreak, STOP, HOLD, or graph-bound recursion.
For output control, `T` includes `B`, `κ/H`, held dependencies, registers, and downstream burden
pressure. If a state/noetic reread prints `∇×κ`, `∇×B`, remaining burden, still live pressure,
release next, HOLD, LoopBreak, blocked proof-stacking, hidden-framework recoil, doubt-churn, or a
pre-voiced downstream defense, it has invoked MRP and must show the compact block before routing.

### Restorative Response
[Required once in default output after the final state/noetic re-read. Bounded to what the released operation(s) actually landed. Do not promote it into a new burden-cycle. Do not release held downstream burdens. If state/noetic re-read licenses another same-input burden, continue first.]

### Closing Formulation
[Required once at the very end after Restorative Response. Synthesize what cleared, what remains held, and the final governed takeaway. Do not substitute for state/noetic re-read.]
```

If the release status says another bounded pass is licensed, continue with Burden-Cycle N+1.
If closure, hold, or partial traversal is correct, state the reason in prose and use compact
state markers such as `R(H,Δ): RECURSE` when they prevent false closure. Do not print raw
`Recursion decision:` / `next_eligible_pass:` fields in default mode.

**Per-burden Layer A re-entry:** In hard, compound, or deformed cases, every released
burden after `R(H,Delta)` re-enters a compact Layer A before Layer B continues. This is a
state re-read, not a global reset. The new Layer A names what is now live, what landed,
what remains held/deferred, which bounded operator is current, and what gate/release decision
licenses the next burden. Without this re-entry, continuation has degraded into a queue rather
than governed diagnostic control.
Per-burden Layer A is a diagnostic re-entry, not a compression budget for the next Layer B.
It should enrich the accuracy of the next burden and must not reduce owner-floor execution,
theological substance, or restoration force.
In hard, compound, or deformed multi-burden output, a single opening Layer A plus prose
transitions is insufficient. Each released burden after `R(H,Delta)` must visibly reopen a
compact Layer A for that burden unless the answer marks PARTIAL before releasing it.
`R(H,Delta)` must decide whether the planned next burden remains licensed, is held/deferred,
is skipped because the prior burden changed the state, requires bounded reroute, or permits
closure. Do not render the next Layer B merely because it was plausible in the initial route.

**Layer A required default fields:** read status, confidence, claim_level,
pattern_profile, reason-category, `Concealment mode:`, deformation, DO-orient, live noetic
burden, current bounded operator (by function), held, source-status/noetic-frame, and
gate/release decision. `Decisive missing differentiator` is conditional:
include it when confidence is not `strong` or read status is not `dominant`, or when the
case is otherwise thin, mixed, distributed, or underdetermined. These fields are render-time
aliases of existing diagnostic state; they add no IR fields, routes, PF codes, or owners.
Do not omit the compact DSL/IR header in default mode.

When multiple deformations or modal pressures are active, Layer A names the compound rather
than flattening it into one module label. Preserve load-bearing distinctions among
desire-as-criterion, identity-stabilization, imported framework, concealment, register
mismatch, and pride/refusal signals when the input warrants them. A compact field can still
carry the case-specific diagnostic reading.
Do not render `concealment: None detected` or omit the concealment line in default Layer A when
the case is named-worldview, imported-framework, pseudo-neutral-tribunal, or identity-stabilized.
If the same Layer A marks
`D6`, imported-framework pressure, pseudo-neutral tribunal pressure, or identity-stabilization
as operative, `clear` is not licensed merely because the conclusion was stated openly. Use a
non-clear compact mode, `mode-?`, or an anchored phrase such as `surface-open /
framework-concealed` while holding stronger interior claims unless the evidence warrants them.
If a public worldview or identity marker supplies the criterion, authority-order, discourse
posture, or restoration vector, Layer A may mark it as structurally load-bearing while still
holding interior motive, culpability, sincerity, and soul-state. Source-status caution prevents
ad hominem verdicts; it does not make input-anchored worldview analysis optional.
The converse is also part of family fidelity: do not turn testimony, predication,
grief/register, kalamic proof-order, or another anchored family pressure into a generic
source-worldview frame when the input has not made that frame operative.

Current bounded operator is one live noetic burden/function: `B`, not a route chain,
module list, route itinerary, single operative submove, or lone `s`. Allowed examples: `imported moral tribunal /
worship-worthiness criterion burden`, `foundational epistemology warrant burden`, or
`source-status / identity-stabilization burden`. Forbidden examples: `FPD -> M1 -> DO-8 ->
M8 -> restoration`, `M1, M8, DO-8, restoration`, or `full route itinerary`. A route chain is
not a bounded operator. If imported criterion, hujjah/accountability, hiddenness-frame
correction, consequence tracing, or identity/source-status work all serve the same burden, they
remain separate `ⁿBᵢ` submoves inside that burden; if `R(H,Delta)` shows a new input-anchored
live burden, they become separate burden-cycles. The forbidden move is route-chain naming or
generic consolidation, not warranted distinct submoves.

**Submove-vs-recursion rule:** use `recursive-state-transitions.md` notation:
`Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`.
Gloss: Operative submoves do not become burden-cycles, but they also must not be merged into
one generic operation. `hujjah/accountability correction`, `guidance-as-coercive-proof
correction`, hiddenness, punishment/accountability, source-status, source-worldview,
consequence tracing, and identity-stabilization remain distinct `ⁿBᵢ` submoves whenever they
are active TTP/operator functions, even when they serve the same governing `B`. They become
separate burden-cycles only after the current gated operation lands and the state/noetic re-read
shows a genuinely new input-anchored live burden. Multi-burden does not mean multi-recursion by
default; one burden may still require several distinct submoves.

**Anti-overcollapse rule:** do not treat one broad indictment as one omnibus burden when the
input contains distinct live noetic functions. Same-burden collapse is valid only when the
same `τ`, source/noetic frame, claim cluster, and restoration vector remain operative. If
accountability compression, hiddenness/coercive-guidance pressure, punishment/mercy/justice
architecture, source-worldview consequence, predication, transmission/testimony, grief/register,
or family-local proof-method pressure has its own target/function/restoration vector, the
current burden must land and `R(H,Delta)` must release the next burden-cycle or explicitly
HOLD/PARTIAL it. Dense hard cases may be long; compactness removes padding, not live burdens.
First-order, second-order, and higher-order pressures must not be collapsed into one omnibus
burden when they remain live after `Land(B)`. A surface claim may land while its criterion,
proof-method, testimony standard, or source-authority remains governing; a criterion may land
while a source-worldview, authority-order, register, or noetic-frame inversion remains live.
The point is to repair noetic function: truth-directed operation, reliable warrant-process,
and sound foundational ordering. If a downstream claim rests on a corrupt basic criterion or
tribunal, the answer has not restored the structure merely by answering the surface proposition.
The request to respond, deal with a claim, bring sources, or dismantle a belief system does not
itself create a new practical burden. It requires source-operation inside the relevant burdens
and a final Restorative/Application Response. Practical handling becomes NewB only when the input
contains a distinct unresolved practitioner constraint such as register/HOLD, safety/adab
sequencing, testimony method, or source-status confusion.
Hard source-request cases must not compress distinct source functions into one citation stack.
If a burden uses sources for different functions, each material function needs local operation:
why that source is live for the burden, what premise/criterion/warrant it pressures, and what
state change it produces. A later source map may summarize; it cannot substitute for
burden-local source operation.

**TTP entry / exit visibility:** Default mode does not need to print an audit ledger, but the
answer must be visibly compatible with TTP entry and exit criteria. The current live burden
must have a bounded target; each operative submove must perform an operation and produce a
result; those results must feed a burden landing; and the next live burden transition must come from
state re-read. A response that names a TTP, then moves to a downstream topic without burden landing
and refresh, is invalid even if it is accurate.

Hard default output may expose `Operative Submove` labels under one burden; use the `ⁿBᵢ`
notation or its ASCII fallback for public canonical output. `B<N>.s<i>` labels are
legacy/checker aliases.
This is not a raw IR, route ledger, or load ledger when each submove is case-specific and
feeds `Land(B)` before `R(H,Δ)`. A complex `B` rendered as one generic
Target/Operation/Result block while necessary submoves remain implicit is hard-output
compression failure. A single block is sufficient only when diagnostic burden accounting
shows one live burden with one materially necessary submove.

Hard-output render-through template:

```text
Burden N: <name>
  Operative Submove ¹B₁:
    Target: <exact premise / criterion / predicate / warrant>
    Operation: <closed operative verb>
    Result: <changed claim-state>
  Operative Submove ¹B₂:
    Target: <exact premise / criterion / predicate / warrant>
    Operation: <closed operative verb>
    Result: <changed claim-state>
  [continue until all materially necessary s are rendered]
  Land(¹B): <cumulative state delta from ¹B₁...¹Bₙ>
  [Mid-Reread Pressure]
    Target: ¹B
    Reread: R(H,Δ)
    Landed delta: Δ¹B / Δκ from Land(¹B)
    Pressure activations:
    - freeze-landed-move: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - dependency-tug: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - hidden-framework-recoil: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - entailment-pressure: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - doubt-churn-guard: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - reorientation-reminder: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    ∇·T: <neutral/settled/bounded/non-neutral plus license>
    ∇×T: <null/resolved/held/non-null plus license>
    Route-gradient: <where ∇ now points: held burden / generated burden / hold / loopbreak / stop>
    Finding: <stable/genuine-dependent/partial-real/hidden-framework-recoil/doubt-churn/reorientation>
    MRP route result type: <held_burden_activation/generated_burden_instantiation/no_new_resultant/loopbreak/hold_partial>
    MRP resultant: <finding -> route/graph/hold consequence>
    Graph delta: <none or ⁿB → ⁿ⁺¹B>
    Pre-emption basis: <none/graph-bound/commitment-bound/framework-bound>
    Route: <STOP/HOLD/RECURSE/LoopBreak(∇×T)>
    Boundary: T_lang does not imply guaranteed uptake
  R(H,Δ): <held/released/next-live-burden decision licensed by the MRP block>
```

If this block names live pressure such as proportionality, hiddenness/coercive-guidance,
source-worldview, moral-grounding, owner-floor, owner-body, non-neutral divergence,
non-null/held curl, or a graph edge, STOP/COMPLETE and final response sections are blocked until
that pressure is released/landed, held with reason, or marked PARTIAL with the blocked
owner/burden.
MRP field values are parseable records: `Finding`, `Pre-emption basis`, and `Route` use one
exact template value with no prose or punctuation; `Boundary` begins `T_lang does not imply
guaranteed uptake`; pressure slots begin with an owner/TTP id, `pressure class:`, or
`coverage gap:`; `Graph delta` is `none` unless `Route: RECURSE`.

This template is the visible hard-output form for `ComplexB`; it is not a full procedural
audit, raw IR dump, or route ledger when the fields are case-specific and serve the same
live burden. `AtomicB` may render one submove only when the burden has one target, one
operation, and no distinct internal predicates, criteria, source-status forks, or release gates.
For hard smoke or hard default execution, visible submoves must be backed by owner-body access:
root summary recognition, module-label memory, or `matched_modules` naming is not enough.
Before rendering a complex `ⁿBᵢ`, the active TTP owner body or compiled bundle section
containing its operation floor must be loaded/read, unless that exact section is already present
in active context. Package availability, map presence, or bundle co-location is not access, and
trace/verdict evidence must not overclaim beyond that access. If the owner body or compiled bundle section cannot be
loaded or identified, the hard output must mark `PARTIAL / OWNER-BODY-NOT-LOADED` with
the missing owner/path rather than rendering a generic Target/Operation/Result block. This marker
is a required hard-output failure marker and is permitted in default/hard output.
When generated `skill/SKILL.md` is the supplied runtime surface, copied runtime references and
compiled omnibus sections count as readable runtime context once the compiled map or routing
table points to that selected `MODULE_ID`. Do not mark owner-body failure merely because a
separate atomized source file was not opened. Sibling bundle sections remain inactive unless
routing selects their original module ID.
After this marker, do not render closure witness, Restorative Response, Closing Formulation, or
broad "refuted"/"closed" language for the blocked burden. In MRP, owner-load failure uses
`Route: HOLD` and `Boundary: PARTIAL / OWNER-BODY-NOT-LOADED: <missing owner/path>`.

**Layer B governed-response shape (mandatory):** Default Layer B must visibly contain Hidden
Premises and one Core Formulation for each released live noetic burden / governed operation.
Core Formulation is local to the released operation: it is a compact operative formulation
identifying how sound/innate reason has been deformed, concealed, or deviated from; the
modality/pattern by which the unsoundness operates; and the restoration vector by which the
noetic structure is resolved or returned toward sound order. It is not a summary, conclusion,
bibliography, or rhetorical flourish. The bounded response / operative submoves execute that Core Formulation.
Missing Core Formulation or essay-only Layer B is a render failure.

Restorative Response is required once in default output after the final state/noetic re-read. It is bounded
to what the current operation(s) actually landed; it is not optional, not pastoral expansion, not
a new burden-cycle by default, and not a license to release held downstream burdens. It identifies
what order is restored, what criterion/source/warrant is returned to its proper place, what
deformation or concealment is relieved, and what remains held if not yet restorable.

Closing Formulation is required once at the very end, after Restorative Response. It synthesizes
what was cleared, what remains held, and the final governed takeaway. Do not require Closing
Formulation inside each burden. Do not let Closing Formulation substitute for state/noetic re-read.
Do not make every burden self-close rhetorically. Closing before state/noetic re-read is a render
failure.

Non-trivial operators require a compact TTP/operator trace when that trace helps audit execution;
this is not a `matched_modules` dump and does not authorize public source, scholar, school,
genealogy, bibliography, or external-theorist support.

**TTP/operator invocation trace:** Do not confuse source-citation discipline with
TTP/operator trace discipline. Default output avoids scholar/source/citation parade, but when
a TTP/operator actually performs the work it must be explicitly identified in the governed
operation or bounded response with the owner ID where the owner has one. Prefer compact local
labels such as `¹B₁ [FPD]`, `¹B₂ [M1]`, `¹B₃ [M9]`, or `²B₁ [P1]`; use ASCII fallback
`1B1`, `1B2`, `1B3`, or `2B1` only when Unicode is unsupported. This is not a route ledger; it is local operator attachment.
This includes reductio, tamanu, criterion-reversal, tribunal-detection, predication repair,
authority-order repair, and any other named operator.
No invisible TTP execution; no generic prose replacing named operator use; no argument-bank dump
under an unnamed TTP; no TTP name used decoratively without target -> operation -> result; no
source citation substituted for TTP invocation; and no TTP invocation substituted for
Qurʾān/Sunnah/Salaf citation when revealed textual support is actually used.

**Burden-complete operator routing:** within the released live burden, matched
TTPs/operators must address materially necessary sub-burdens before `R`. Do not answer only
the headline objection, skip internal sub-burdens, substitute generic prose for routed
execution, or jump straight to a broad conclusion. `R` may expose a deeper governing
epistemology as `NewB`, first-order repairs, held higher-order rebuttals, or STOP/HOLD/
PARTIAL/RECURSE, but `NewB` is not licensed until the current burden and its necessary
sub-burdens have actually been operated on.

**Bounded release cohesion gate:** Layer B may release more than three major operative submoves
inside one governing burden when those submoves are materially necessary to land that burden
and remain cohesive under the submove saturation gate. More than three major moves is a recheck
trigger, not a cap: ask whether the next submove shares the same target-family, claim-level,
source/noetic frame, claim cluster, and restoration vector. If it does, release it as its own
distinct target -> operation -> result. If it does not, the current burden must land and state
must be re-read before more material is released. This gate is never a consolidation license:
active TTP/operator functions remain distinct submoves or later burden-cycles, and if limits
prevent that distinction the result is PARTIAL, not a merged generic operation.

**Rubric-skeleton failure:** A default answer fails even when every heading is present if it:
- asserts "this burden lands" without owner-specific operation and cumulative-state delta;
- repeats the rubric vocabulary while giving generic prose instead of operative pressure;
- treats TTP names as decorative labels rather than operations;
- makes a state/noetic re-read that only restates cleared/held/decision without saying what changed;
- starts a new burden-cycle without passing the NewB license test;
- builds size by repeating runtime-proof or compliance language rather than executing the burden.

**Scaffold-language failure:** Default output fails if it explains the smoke/test harness,
owner-floor compliance, or runtime proof instead of answering the case. Forbidden default
phrases include "this smoke artifact", "runtime constraint being tested", "owner floor is
applied", "owner-floor pressure", "the TTP has to change something",
"burden-completeness check", "the operation is bounded to the target named above", or any
generic paragraph about target / operation / result whose function is to prove compliance
rather than perform the operation. Those belong in trace/verdict artifacts only.
Also forbidden in canonical scriptless output: "execute queued owner", "execute first-live
owner", "validation passed", `smoke_kind`, `validation_fidelity`, `execution_fidelity`,
`route_plan`, `features.json`, `check_execution`, or any repo/dev harness proof claim.
Use human-facing owner-ID submove labels instead, such as `¹B₁ [FPD] - expose the imported
tribunal`; do not render dev-harness status. Do not use literal `Owner-floor:` lines or
`B<N>.s<M>` legacy/checker markers as preferred canonical public notation; use `¹B₁`,
`¹B₂`, `²B₁`, or ASCII fallback `1B1`, `1B2`, `2B1` only when Unicode is unsupported.
Likewise, repeated formula paragraphs such as "That test changes the force of the case",
"The result is a real state change", or other reusable test/result boilerplate fail default
render even if the surrounding nouns are case-specific. Operation prose must be live
case-pressure, not a fill-in compliance frame.
Reusable hinge/load-bearing boilerplate also fails default render. Phrases such as
"load-bearing point", "if that point is left vague", "this exact pressure can stand",
"surrounding topic is held back", "the live hinge can be tested", "case-state after
this pressure", or "the move forces the inference to carry its own burden" describe
proof-of-execution, not the case itself. They belong, if at all, in `trace.md` or
`verdict.md`, never in user-facing default output.

**Fixture/case contamination failure:** Default output must not import case-specific
language from another fixture, example, or smoke family. Named source-worldview
hard-smoke frames, quoted hard-smoke phrases, accountability/punishment/hell
language, source-status biography language, or moral-protest/hiddenness language
may appear only when the current input and validated IR release that burden-family.
Cross-fixture prose reuse is a render failure even when headings and operator trace
are present.

**Artifact separation:** default output is the user-facing runtime result. It is not the trace
file and not the verdict file. Runtime proof, loaded-file proof, checker proof, smoke execution
metadata, and fixture audit text belong in trace/verdict artifacts or internal/development audit,
not in default Layer A or Layer B.

**Layer A / Layer B release check:** Layer A is diagnostic control, not an answer bank. Layer B
is the permitted bounded response, not a place to unload all held material named in Layer A.
If Layer A lists a held route and Layer B answers it before state re-read licenses it, the render
has become Layer A/B smuggling. Rewrite as one bounded live burden, then refresh.
Held-route semantic leakage is the stricter form of this failure: a noun phrase listed
in `held` or `Held routes` cannot appear in Layer B as an answered topical commitment
unless a preceding state/noetic re-read explicitly released it with `Released: <item>`,
`Released routes: <item>`, or `Newly released routes: <item>`.

**Layer A must not show:** full Diagnostic IR, full Case State, source_basis,
matched_modules, load ledger, route itinerary (e.g., Next: FPD → M1 → M8), NS codes in
field-printout form (unless the NS code is the governing issue), or broad concealment /
deformation verdict dumps without anchoring signal. The compact `Concealment mode:`
and lowercase `deformation:` fields above are permitted only as bounded DSL/IR anchors, not as
expanded interior-certification ledgers.

**Default compact DSL/IR header:** The Layer A block above is the compact visible
diagnostic compiler trace. It is the default compact diagnostic frame, not the full
internal/audit diagnostic record. The default header restricts visible fields to the
required field set; everything else remains internal. It must surface enough governing
diagnostic fact for the current pass to be auditable as compiler traversal rather than essay.

**Compact state re-read:** The state re-read block above is compact. It must enumerate
remaining input-anchored burdens, not merely state a governance decision. A line such as
"Governance: STOP" is forbidden in default output and is not a valid state re-read. The
default must show that no input-anchored eligible burden remains, or name the burden and
the prose reason for a hold or partial close.

**Single-Pass Layer A/B Surface-Compliance Failure:** A response that prints Layer A + Layer B + state re-read
exactly once and then stops ? without proving no eligible input-anchored live burden remains,
or without continuing when state re-read licenses another bounded pass. This is a recursion failure, not a
structured response. The burden-cycle shape is not satisfied by printing it once. It must be
repeated for each eligible input-anchored live burden until governed recursive sufficiency.

**Internal requirements still apply even when not visible:**
- Case-state resolved internally.
- Governing burden identified internally.
- Upstream blocker cleared or named.
- Downstream held if unresolved.
- Output-release rubric passed.
- STOP / HOLD / RECURSE / PARTIAL decision made.
- Post-render gate run before ending.
- Default compact DSL/IR header, Hidden Premises, per-operation Core Formulation,
  bounded operation, state/noetic re-read, one Restorative Response, and one final
  Closing Formulation rendered; literal final-governance
  fields remain internal unless `:dsl`, internal/development audit, pass-review, or diagnostic
  trace was requested.

**Default Final-Output Preflight Gate (mandatory):**
Before emitting any default canonical compact `/daee-epistemics` answer, scan the proposed final
response. This is a final-output gate, not a render preference. If the proposed response
contains any prohibited scaffolding, route plan, or meta-composition prefix, the response is
invalid and must be rewritten before output as clean governed prose.

The Default Final-Output Preflight Gate is not merely a visible-format sanitizer. It also
checks pipeline validity: internal diagnosis -> validated IR -> routed operator selection
-> output-release rubric -> diagnostic-render-contract -> state re-read -> post-render
gate -> STOP / HOLD / RECURSE / PARTIAL decision. Output-release decides what may be
released; diagnostic-render-contract decides how it appears; the preflight gate enforces both
at the last mile. If the answer is clean prose but was produced by topical essay
sequencing, it is invalid and must be rewritten.

Use `recursive-state-transitions.md` for the canonical default transition skeleton and
no-premature-STOP recursion rules.

Pipeline-validity check for the default compact surface:
- V1 / diagnosis ran before answer.
- Phase 2 passes ran where triggered.
- Diagnostic IR formed internally before routing.
- Routing came from validated IR.
- TTP selected as operator, not prose label.
- Output-release rubric applied before visible render.
- Render contract applied before final prose.
- state re-readed after the bounded move.
- Post-render gate run before closure.
- STOP / HOLD / RECURSE / PARTIAL decision made before ending.

Preflight recursion check: after the first bounded move, ask what cleared, what remains
live, whether the remaining live burden was already present in the original input, whether it is
now eligible, and whether any stop/register/semantic/thin-basis gate blocks it. If another
eligible same-input live burden remains after the current blocker clears, default output must
continue with one bounded next pass using a prose state transition, or render partial
release-status prose if limits prevent doing so. It may not silently close.

Preflight NewB check: a next burden-cycle is valid only if the prior burden landed through
owner-specific operation, cumulative-state delta is visible, the proposed next burden was
already input-anchored or held, the proposed next burden differs materially from the prior
burden by live target/function/restoration vector, and no gate blocks release. Otherwise the
material remains a submove, HOLD, or PARTIAL.
Do not promote application packaging into a burden-cycle: source maps, concise response
wording, "how to answer" sections, do/don't boundaries, warnings, and recaps usually belong
inside the current Layer B or final Restorative/Application Response unless `R(H,Delta)` proves
a genuinely new unresolved noetic function. Source-worldview, worship-worthiness,
transmission/testimony, predication, hiddenness, grief/register, kalam/falsafah proof-method,
and similar family pressures may become distinct burdens only when they remain input-anchored
and unresolved after the previous burden lands.
Do not overcollapse them into a first omnibus burden when they carry distinct input-anchored
targets/functions; release the next burden after `Land(B) -> R(H,Delta)` or mark HOLD/PARTIAL.
Do not promote "how to answer," source-map, or concise-response material into a late burden just
because the user asked for an answer; attach it to the relevant Layer B or final response unless
it carries its own unresolved practitioner constraint.
Do not stack several verses or reports under one generic "source deployment" paragraph when
they perform different burden functions. Separate the source operations locally before `Land(B)`.

Do not flatten active operators while preventing false burden proliferation. Same-burden
collapse means active TTP/operator submoves stay locally attached under Layer B; it does not
license one generic paragraph. Each materially active operator submove must show why that
operator is live for the current burden, its target, its operation, its result/state change,
and how that result contributes to `Land(B)`. Use the matched owner/TTP where structurally
warranted: FPD for imported tribunals, M1/M1P for self-grounding or self-defeating criteria,
M8 for unacceptable consequences on a worldview's own grounds, M9/predication discipline for
divine-predicate errors, V2 for reason-role repair, P1/P7 for restoration and stop discipline,
and the relevant transmission, predication, register-hold, or family-local owner where active.

For the canonical valid default-mode transition example and invalid Step/Move contrast,
use `recursive-state-transitions.md`.

TTP labels do not satisfy execution. TTPs are surgical interventions, not essay sections.
A default answer may briefly name an operation/module
label if helpful, but the operation must be visible: bounded target, operation performed,
result of the operation, and state re-read before any next operator.

Layer A contrast pairs:
- Permitted default prose: "The objection imports a moral tribunal that has not justified its
  authority."
- Permitted default compact Layer A fields: `- claim_level:`, `- reason-category:`,
  `- live noetic burden: imported moral criterion`, and `- gate/release decision:`.
- Banned default field printouts: `Foreign premise: detected`, `Concealment: iʿrāḍ primary`,
  `Deformation: hawā primary`, `NS-4/NS-5`, and `Recursion decision: RECURSE`.

Rule: prose diagnostic fact is allowed; field-style printout is not default output.
"Field-style printout" in this rule refers to the full IR / Case-State field set and verdict
dumps ? not the compact Layer A DSL/IR header. The compact Layer A header is the explicitly
permitted exception: it may show read status, confidence, claim_level, pattern_profile,
reason-category, `Concealment mode:`, deformation, DO-orient, live noetic burden, current bounded
operator, held, source-status/noetic-frame, decisive missing differentiator when required,
and gate/release decision. Layer A must not show the forbidden set above.

Default final-output failure tokens include:
- "Now I have enough", "I now have enough", or "I now have sufficient".
- "Let me compose", "Let me write", "Let me craft", or
  "Let me construct the diagnostic IR".
- "Let me check", "Let me also quickly check", or "I will produce governed prose".
- `## Diagnostic IR`, `[Diagnostic IR]`, `Case State:`, a full IR/case-state field block,
  `matched_modules`, `source_basis`, load ledger, route ledger, planned route list, or
  a visible route plan such as `Next: FPD -> ...`.
- Strong interior-classification verdict dumps such as `Concealment: iʿrāḍ primary`,
  `Deformation: hawā primary`, or `NS-4/NS-5 compound` unless the user invoked `:dsl`
  or the task is internal/development audit. The compact Layer A fields are allowed only
  as bounded DSL/IR anchors.
- A bibliography, "Primary Sources Referenced", external research-style source list, or
  source-basis ledger in default mode unless sources/citations were requested.
- Bare "Step 1 / Step 2 / Step 3 / Step 4" or "Move 1 / Move 2 / Move 3" sequencing
  when offered as recursion.
- `Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration`, or any variant where a
  route itinerary is printed as the bounded operator.
- "Smoke runtime note", "Runtime grounding detail", "Skill invocation proof",
  "loaded before output", "proof of loaded files", or other audit/proof boilerplate in
  default output. Output artifact is not trace artifact; output.md != trace.md != verdict.md.
- "Pass 1 / Pass 2 / Pass 3" headings for FPD, M1, DO-8, M8, identity clarification, or
  restoration fragments that are merely operative submoves under one burden.
- "Pass 1 / Pass 2 / Pass 3" headings for imported criterion, hujjah/accountability, and
  guidance-as-coercive-proof corrections when `R(H,Delta)` has not first proved whether they
  are same-function submoves or distinct input-anchored noetic burdens.
- Restoration synthesis or pastoral note before the active burden landing and state re-read.

Rewrite-before-output rule: replace the failed surface with compact prose that names only
the governing diagnostic fact needed for the answer. A valid default opening may say: "This
objection has three layers: an imported moral criterion, a hiddenness claim, and a
punishment/accountability claim. The criterion has to be tested first, because otherwise
the answer would let the objection judge revelation by a standard it has not justified."
Then continue with bounded prose. Do not print the IR, case state, matched route, or route
plan.

**Must not:**
- Print meta-composition prefixes or close variants such as "Now I have enough...",
  "Now I have enough to compose...", "I now have enough...",
  "I now have sufficient...", "I now have sufficient grounding...",
  "Let me compose...", "Let me write...", "Let me write it...",
  "Let me craft...", or "I'll now compose...".
- Print "Let me construct the diagnostic IR" or equivalent narration of internal setup.
- Pretend diagnosis was unnecessary.
- Release downstream content before upstream blockers clear.
- Hide held material when the user needs to know why the answer is bounded.
- Treat state re-read as only waiting for a user response.
- Close with STOP before the post-render gate has rechecked held material.
- Stop after the first good move when the original input contains another eligible live burden.
- Print the `[Diagnostic IR]` code-fenced block or any `## Diagnostic IR` section header.
- Print any header equivalent to `## Diagnostic IR (Internal - Governing the Response)`.
- Print `Case State:` or a full `[Case State]` block with all IR fields populated.
- Print `matched_modules` or route-owner ledger lines.
- Print `source_basis`, route ledger, planned route list, or a visible route plan such as
  `Next: FPD -> ...`.
- Print strong interior-classification verdict dumps such as `Concealment: iʿrāḍ primary`,
  `Deformation: hawā primary`, or `NS-4/NS-5 compound` unless the user invoked `:dsl`
  or the task is internal/development audit. In default prose, prefer:
  "The public identity-frame may stabilize the objection's moral criterion, but that is not
  a claim to know the person's inner motive."
- Print a Load Ledger or bundle resolution table.
- Print a Render Permission Check or source-basis printout.
- Print a bibliography, "Primary Sources Referenced", external research-style source
  list, or source-basis ledger unless the user explicitly requested citations/sources
  or the task is internal/development audit or research.
- Print the full procedural audit template or any code-fenced IR listing. The compact
  hard-output render-through template above is allowed when it renders case-specific
  submoves under the same live burden.
- Print smoke/runtime proof boilerplate, loaded-file proof, checker proof, or verdict
  material inside default output.
- Apply expanded diagnostic or internal-audit render shape solely because the case has multiple live burdens.

---

### Expanded Diagnostic / IR Surface (`:dsl`)

**Use when (invocation gating required ? secondary conditions alone do not trigger expanded diagnostic visibility):**
- The user invokes `/daee-epistemics:dsl`. **This is the gating condition.**
- OR the user explicitly asks for expanded diagnostic output, DSL/IR render, or lab-report format.

Plain `/daee-epistemics` never triggers expanded diagnostic visibility, regardless of case complexity, number of live burdens, or whether diagnostic transparency would be useful. If the invocation is plain, the default compact DSL-governed surface applies. Full recursion still runs; only the visible machinery differs.

Secondary conditions (apply only when the gating condition above is met):
- The case has multiple live burdens.
- Diagnostic transparency materially helps.
- The answer must show what is governing first.
- Downstream material is held.
- Recursive traversal needs to be visible.
- The response needs to distinguish anchored, inferred, and speculative material.
- The user is testing whether the skill routed correctly.

**Recommended visible shape:**

```md
## Compact DSL / IR
- Read status:
- Confidence:
- Live noetic burden:
- Current bounded operator:
- Held:
- Decisive missing differentiator:
- Selected IR fields:

## Source Basis
- Anchored:
- Synthesis:
- Inference:
- Speculative / held:

## Release Check
- Cleared before release:
- Held downstream:
- Why this much is released:

## Restorative Response
<bounded answer>

## Post-Render Gate
- Cleared this pass:
- Remaining live distortions:
- Held routes rechecked:
- Newly released routes:
- Next eligible pass:
- Recursion decision: STOP | HOLD | RECURSE | PARTIAL
```

**Rules:**
- Do not require every bullet if not materially governed.
- Use original module IDs for any visible `matched_modules`; never use omnibus filenames as matched modules.
- Do not expose PF codes or matched module names unless they help the user trace a compact IR decision.
- Do not let the diagnostic section become a broad procedural audit.
- Do not release downstream content merely because it is named in a section header.
- Do not treat compact diagnostic render as permission to dump all internal machinery.
- Do not include the full verbose load ledger; that belongs only to internal/development audit when useful.
- Do not treat the Post-Render Gate section as merely waiting for user response. State whether same-response recursion is required, blocked, partial, or complete and why.
- If recursive traversal is visible, use one live burden per burden-cycle: Live noetic burden, Why already present, Released module(s), Bounded move, state re-read, and Governance. Recursion is not argument dump.

---

### Internal/Development Audit Surface

**Use only when:**
- The task is internal/development audit, regression review, or procedural debugging.
- The user invokes `/daee-epistemics:audit` in that internal/development context.
- The user asks for pass-review.
- The user asks for regression testing.
- The user asks for source-basis trace.
- The user asks whether the skill routed correctly.
- The task is a patch report or architecture test rather than answering an ordinary interlocutor.

`/daee-epistemics:audit` is not a public-facing render mode for ordinary interlocutor
answers. If invoked for ordinary response work, treat it as deprecated and prefer `:dsl`
for expanded diagnostic/IR visibility or default mode for governed response.

**Full shape:**

```md
# Output ? <Burden-Cycle Number or "Initial daee-epistemics Response">

## Source Case
<input.md reference>

## [Case State]
- Case family:
- Claim-type:
- Claim level:
- Reason-category:
- Foreign-premise status:
- Upstream findings:
- Primary upstream issue:
- Pattern profile:
- Primary deformation:
- Routing gate:
- Read status:
- Live alternatives:
- Reassessment:
- Convergence requirement:
- Discourse orientation:
- Concealment mode:
- Register-hold:
- Deployable on shift to:
- Matched modules:
- Sequencing rationale:
- Restoration target:
- Confidence:
- Decisive missing differentiator:

## [Source Basis]
- [anchored]:
- [synthesis]:
- [inference]:
- [speculative]:
- Source type / weight:
- Restoration source:

## [Restoration Trace]
- Governing misread risk:
- What was withheld and why:
- What correction was applied:
- Route that became permissible after correction:
- What remains live or unresolved:

## [Restorative Response]
<Bounded public response. If Layer B is held, mark that clearly without releasing what remains held.>

## [Core Formulation]
<Only include when the objection, shubhah, or criterion structure needs explicit unpacking.>

## [Engagement Register]
<Only include when concealment mode, discourse orientation, register-hold, or Layer B / Layer A split materially governs deployment.>

## [Pastoral/Relational Note]
<Only include when non-intellectual conditions materially govern follow-through.>

## [Post-Render Gate]
<Required before closure; full detail is visible in internal/development audit.>

## Closing Formulation
<Sharp restorative closing.>

## Pass Tag
<pass-X or initial-daee-run>

## Pass-Scoped Revision Notes
<current-pass only; for audit/pass-review, not ordinary runtime.>
```

**Field discipline for internal/development audit:**
- `[Restorative Response]` is bounded, not exhaustive. If Layer B is held, it is held ? not previewed under another heading.
- `[Core Formulation]` is conditional on whether the argument structure requires explicit unpacking.
- `[Engagement Register]` is conditional on whether concealment mode or orientation materially governs.
- `[Pastoral/Relational Note]` is conditional on whether non-intellectual conditions are operative.
- `[Post-Render Gate]` is mandatory in internal/development audit and is derived from `post_render_gate`, not improvised after writing the answer.
- Pass-Scoped Revision Notes are for audit/pass-review only ? not ordinary runtime.
- Runtime/bundle ledger, when shown, must resolve atomized paths through `compiled-module-map.json`; do not describe missing atomized files as literal runtime load targets.

---

## Field Discipline

**When to surface PF codes / pattern_profile:** Only when the overlay changes routing, owner selection, hold/release behavior, or load floor ? not as a label for the visible topic.

**When to surface matched module names / IDs:** Only in internal/development audit, or in `:dsl` when the user needs to trace which module governed a routing decision. Do not turn this into a route ledger.

**When to surface backbone predicates:** Only when a backbone predicate emission (C, T, O, or K group) materially changed the routing gate or suppression rule in this pass.

**When to suppress raw internal fields:** Default governed response suppresses raw diagnostic machinery, but it must still print the compact DSL/IR header, state/noetic re-read, and control-relevant formal state markers. Literal field labels such as `Recursion decision:`, `next_eligible_pass:`, and `post_render_gate:` belong to `:dsl`, internal/development audit, pass-review, or diagnostic trace. Compact target-explicit markers such as `R(H,Δ): RECURSE`, `Δκ live`, `∇·κ positive/live`, `∇×κ unresolved`, `∇·B positive`, or `∇×ξ unresolved` may appear by default only when they govern release, recursion, or closure.

---

## Source Basis Discipline

Use the standard markers from `references/diagnostics/inference-boundary.md`:

| Marker | When |
|--------|------|
| `[anchored]` | Directly grounded in a loaded file or governing thesis |
| `[synthesis]` | Combining multiple loaded files without adding a new thesis |
| `[inference]` | Model-level extension beyond what the files explicitly state |
| `[speculative]` | Tentative extension that should not govern unless confirmed |

In `:dsl`, surface the Source Basis section only when the reply combines files, depends on synthesis, or uses model-level inference. In default compact render, inference marking is still required internally but need not appear in the visible output unless the claim is materially extension-dependent.

---

## Restoration Trace Discipline

`[Restoration Trace]` appears in internal/development audit render and may appear in `:dsl` when the trace materially explains why only this much was released. It must record:

1. What governed the case.
2. What was withheld and why.
3. What correction was applied.
4. What route became permissible after correction.
5. What remains live or unresolved.

It does not appear in default compact render and should not appear in `:dsl` unless the held/released distinction is the primary diagnostic question.

---

## Layer B and Held Material

**Layer B held means actually held.** Not previewed. Not named as held and then summarized. Not answered under a different heading (see `anti-patterns.md ?Held-but-Answered Contradiction`).

In an expanded diagnostic/IR render, held material may be named in the `Downstream held` field of the Case State section and in the `Held downstream` field of the Release Check section. These fields name what is held; they do not summarize or preview the held content.

In an internal/development audit render, the `[Restorative Response]` must mark held Layer B deployment explicitly: "Layer B: held ? [reason]." The content does not appear.

---

## Post-Render Gate / Final Governance Section

This section is mandatory in the governing state after every bounded restorative move. `:dsl` and
internal/development audit may surface the full gate when recursion, state re-read, or the
continuation decision materially governs the visible answer. Default compact render does not print the raw gate
or literal field labels; it prints `State/noetic re-read` plus compact content. When the
continuation decision materially governs a default answer, render it as a state transition:
what cleared, what remains live, why that burden was already present, why it is now eligible, and
the one bounded next pass. A compact marker such as `R(H,Δ): RECURSE` is allowed when it names
the actual closure decision; raw gate-field dumps remain disallowed.

Internally, and visibly in `:dsl`, internal/development audit, pass-review, or diagnostic trace, it must answer:
- **Cleared this pass:** What did the bounded move actually clear?
- **Remaining live distortions:** What pressure remains live in the same input?
- **Held routes rechecked:** Which held routes were tested after refresh?
- **Newly released routes:** Did any held route become newly eligible?
- **Next eligible pass:** What is the next bounded pass, or is there none?
- **Recursion decision:** STOP, HOLD, RECURSE, or PARTIAL.

Decision rules:
- **STOP** is valid only if no live distortion remains, no eligible live burden remains, and no held route has become eligible.
- **HOLD** is valid only if remaining material exists but its release signal is absent from the input.
- **RECURSE** is required if another live distortion remains in the same input or a held route becomes eligible.
- **PARTIAL** is required if token, tool, or interaction limits prevent completion while recursive pressure remains.

**Do not:**
- Treat this section as merely "I will continue in the next reply." State whether same-response recursion is permitted or blocked, and why.
- Emit STOP without this section or its compact final-governance equivalent.
- Use PARTIAL as an excuse to dump a queue. It names the next eligible pass that limits prevented.

---

## Prohibited Render Moves

1. **Render before diagnosis:** Do not populate template sections alongside answer-generation. Sections must be derived from a prior validated IR.
2. **Template-driven routing:** Do not let the presence of template fields determine what is diagnosed.
3. **Downstream-smuggling via section:** Do not release held content by naming it in a section header and then filling the section.
4. **Machinery dump as diagnostic transparency:** Diagnostic transparency means showing the governing fields ? not every possible field.
5. **Internal audit as default:** Internal/development audit render is not the default format. It applies only for regression, pass-review, source-basis trace, architecture testing, or procedural debugging.
6. **Codex patch-report format as runtime output:** Patch-report structure (files inspected, implementation verdict, changelog) is not a runtime response format.
7. **Suppressing expanded diagnostic visibility when requested:** If the user invoked `/daee-epistemics:dsl` or explicitly asked for expanded diagnostic/IR output, withholding `:dsl` structure without a clear reason harms routing legibility.
8. **Hiding refreshed-state decision:** If a governing blocker was cleared in this pass and a downstream burden remains live, the response must show the refreshed-state decision ? not silently hold the downstream material as though the blocker had not cleared.
9. **Premature closure without re-entry:** Do not render one strong move and close without running the post-render gate, rechecking held routes, and internally deciding STOP, HOLD, RECURSE, or PARTIAL.
10. **Printing the IR schema as the response:** Do not print the `[Diagnostic IR]` code-fenced block or a `## Diagnostic IR` section header in the public response in default mode. The Full IR Schema in `diagnostic-ir.md` is the internal state object for the dispatch gate - not a printout template. Discipline is universal; printout is mode-specific. Recursive-audit discipline applies in every mode; the full audit printout belongs only to internal/development audit. In default mode, literal governance fields such as `Recursion decision:` and `next_eligible_pass:` are prohibited; use the compact DSL/IR header, state/noetic re-read, and control-bound state markers instead.
11. **Meta-composition leakage:** Do not show private drafting phrases such as "Now I have enough...", "Now I have enough to compose...", "I now have enough...", "I now have sufficient...", "I now have sufficient grounding...", "Let me compose...", "Let me write...", "Let me write it...", "Let me craft...", or "I'll now compose..." in any runtime answer. Those are composition notes, not skill output.
12. **Stacking without transition:** If same-response recursion is required, the answer must include a prose state-change transition: what landed, what changed, and why the next bounded move is now eligible. Simply placing another module section after the first is not governed recursion.
13. **Essay headings as fake recursion:** "Move 1 / Move 2 / Move 3" headings do not satisfy RECURSE unless the response shows state re-read between passes and explains why the next already-present burden is eligible.
14. **Default source-list dump:** In default compact render, do not end with a bibliography, "Primary Sources Referenced", source-basis ledger, or external research-style source list unless the user requested sources or the task is internal/development audit or research. Short form: no source/bibliography dump in default mode unless requested. Integrate essential references compactly in prose instead.
15. **Route Surface-Compliance Failure Failure:** Do not print route machinery as proof of compliance. In default mode, Diagnostic IR, Case State, `matched_modules`, literal `Recursion decision:`, and TTP labels do not substitute for target -> operation -> result -> state re-read.
16. **One-time TTP itinerary:** Do not apply TTPs only once against the initial case-state and then answer every detected topic. TTPs execute across refreshed case-states: after each bounded operator lands, the refreshed state determines whether an already-present same-input burden is eligible, held, partial, or closed. Eligible same-input burdens must be traversed or marked PARTIAL; untriggered future contingencies stay held with a release condition.
17. **Premature compression:** Do not shorten default output by skipping an eligible same-input burden. The failure is essay sprawl without refresh, not governed recursive sufficiency.
18. **Wrong optimization target:** Do not optimize for short output or long output. Optimize the render for governed recursive sufficiency: compact DSL/IR header plus bounded prose in default mode, expanded pass trace in `:dsl`, full ledger only in internal/development audit. Compact does not mean thin: governance rejects padding, dumping, and sprawl, but it does not authorize diagnostic impoverishment. Layer A stays compact but load-bearing; Layer B stays burden-complete, case-specific, owner-floor faithful, and restoration-directed. `ⁿBᵢ` / `Land(ⁿB)` / `R` structure is additive to noetic depth, not a substitute for active deformations, live criterion structure, identity/source-status implications, or necessary theological/restorative force. Per-burden Layer A must not shorten Layer B; each active TTP/operator function must remain a distinct submove with target -> operation -> result. In hard scriptless compact-DSL cases, the failure mode to avoid is the smallest compliant-looking response; the target is enough rendered substance for every released burden to land, with as many input-anchored burdens and active submoves addressed as the release gates permit.
    Hard noetic cases may therefore produce extensive output when the live burden requires it. A 20-25kb answer that closes while live burdens remain unlanded is still a failure; a 30-80kb answer can be correct when it is source-operative, TTP-complete, and not padded. If response/runtime limits prevent traversal, mark PARTIAL with the next live burden or blocked submove rather than closing thinly.
19. **Clean Essay Surface-Compliance Failure:** Every pass must show a transition before the next bounded operator starts. Multiple topical sections without state re-read transitions, hidden premises listed without operator result, doctrine dumped after criterion correction, or a pastoral close added without final state re-read are default-mode failures.
20. **Identity over-certification:** In default mode, "the public identity-frame may stabilize the criterion or affect discourse orientation" is permitted when grounded. Unsafe default verdicts include "the identity layer is heavily load-bearing," "his identity is the framework through which every claim is processed," "it is hawā," or "it is iʿrāḍ," unless independently grounded and source-status marked. When an identity/source-status marker is live and input-anchored, do not leave it as a diagnostic orphan: feed it into the restoration vector or practitioner instruction while keeping interior motive, sincerity, culpability, and soul-state speculative or held. Do not misread motive caution as a ban on source-worldview analysis when the input itself makes that worldview criterion-bearing.
21. **Route-chain bounded operator:** Do not render `Current bounded operator` as `FPD -> M1 -> DO-8 -> M8 -> restoration`, `M1, M8, DO-8, restoration`, or any module itinerary. The field names one burden-level function selected after diagnostic reduction and routing precedence.
22. **Route-chain recursion surface-compliance failure:** Do not turn route legs into `Pass 1`, `Pass 2`, and `Pass 3`. Those are operative submoves unless a prior burden landed, state re-read ran, and the next input-anchored burden was licensed.
23. **Restoration before state re-read:** Do not append restoration synthesis or pastoral note before the active burden has landed and state re-read licenses closure, HOLD, PARTIAL, or the next live burden.
24. **Noetic-frame equivalence stack:** Use the canonical notation in `references/diagnostics/recursive-state-transitions.md`: `N_AT` aliases count once; `N_Ashʿarī[*]` and `N_Māturīdī[*]` are family labels, not automatic operative `N`; `family label != operative N`; `shared vocabulary != shared warrant`; `σ_context != σ_warrant`. Do not flatten rival frames under umbrella terms (`classical theology`, `the classical tradition`, `mainstream kalām`, `Ashʿarī/Māturīdī tradition`) when the claim is school-sensitive or disputed.
25. **Contrast-source-as-operative-support:** Do not name a source as `contrast`, `opponent-position`, `historical note`, `genealogy`, `held material`, or `bounded comparison` and then use the same source as operative warrant in the same burden-cycle without explicit reclassification.
26. **Ungrounded noetic re-read:** Do not render a `state re-read` / `noetic re-read` whose `burden landed` is asserted without an immediately preceding operative submove with `target -> operation -> result`, or whose `still live` / `next licensed live burden` is not anchored in the original input, prior held material, or the preceding collapse radius. Field-grounding rules are in `references/diagnostics/recursive-state-transitions.md ?Grounded Noetic Re-Read Shape`.
27. **Method-source branding:** Do not publicly frame daee-epistemics as a named-school methodology, new creed, new ʿaqīdah, new noetics, named-scholar method, or authority-by-association project. Default/public framing is sound noetic diagnosis -> detection of deformation/concealment/criterion import -> restoration of proper warrant/order and proper cognitive function in a congenial epistemic milieu.
28. **Default source/citation restriction:** In default output, school, author, citation, genealogy, external philosopher, theologian, or framework references are not public-render material unless the user explicitly asks for them or validated IR specifically requires source-comparison. Default citation allowance is restricted to Qurʾān, Sunnah, and sound narrations from the Salaf, and any such use must be directly referenced through an external source. Use revealed evidence as an operative diagnostic or restorative instrument where it names the mechanism; do not append it as decorative substantiation or citation padding. When a Qurʾānic or ḥadīth text is quoted because it is doing operative work, prefer a clean blockquote shape: Arabic when useful, translation, source/reference, then a sentence explaining the diagnostic or restorative operation it performs. Do not collapse a central revealed text into a long prose sentence. In operative source-status fields, reserve `Islamic scholar` and `Islamic scholarship` for Salafī/Atharī-aligned scholarship; use specific source-status labels for kalām, falsafah, or later speculative-theological figures. Analyzing an input-anchored worldview frame as the source of a criterion is not source parade when it is tied to the burden's target -> operation -> result.

---

## Grounded Noetic Re-Read Render Shape

For default-mode prose, the canonical state re-read transition is:
"That landed [X]. What remains live is [Y]. What is held is [Z]. The next licensed live
burden is [W]." ? where each clause is grounded as defined in
`references/diagnostics/recursive-state-transitions.md ?Grounded Noetic Re-Read Shape`.

For `:dsl` / internal-development audit / pass-review / diagnostic-trace, the compact field block is:

```text
Noetic re-read:
- burden landed:
- still live:
- held:
- recursion decision:
- next licensed live burden:
```

Field-grounding rules apply in every mode. Printing the field block does not satisfy
the grounding rules. The compact state re-read fields used in the default Layer B
burden-cycle shape (`Cleared`, `Remaining input-anchored burdens`, `Held routes
rechecked`, `Next bounded pass`, `Governance`) are equivalent surface forms; they map to
the same grounded shape and are subject to the same grounding rules.

**Source-status discipline in render:** use `recursive-state-transitions.md` notation:
`N_AT := N_Atharī ≡ N_Taymiyyan ≡ N_Salafī ≡ N_Wahhābī`; `N_Ashʿarī[*]` and
`N_Māturīdī[*]` are family labels, not automatic operative `N`; `σ_context != σ_warrant`.
Gloss: each burden-cycle renders one operative noetic frame; `N_AT` aliases are not multiple
warrants, family labels are not operative support, and contradictory frames may appear only
under non-operative source-status. Render shapes such as "the classical tradition agrees"
or "Islamic tradition says" are forbidden in default mode when school-sensitive or disputed.
Default output normally does not render non-operative `σ` sources at all. School, author,
genealogy, external philosopher/theologian, framework, or contextual-source references are held
unless explicitly requested by the user or required by validated source-comparison IR. When an
internal/development, `:dsl`, pass-review, or IR-required source-comparison render names
non-operative `σ`, include the `Operative warrant:` sentence and the specific non-premise clause:
the non-operative source does not contribute to the warrant; specifically, the named
contrast/opponent/history/genealogy/held/comparison element is not used as a premise here.

---

## Default-Mode Worked Example

**Input.** "If God really has eternal knowledge, power, and will, doesn't that make God
composed of distinct attributes? And if composed, then dependent on parts, like everything
else?"

### Layer A ? Compact DSL/IR header
- read status: dominant
- confidence: strong
- claim_level: meta-ontological
- pattern_profile: none
- reason-category: 2
- Concealment mode: clear
- deformation: category pressure / none primary certified
- DO-orient: truth-seek
- live noetic burden: composition / dependence pressure on divine attributes
- current bounded operator: lexical / category discipline on "composition" and "dependence"
- held: full attribute exposition; source-comparison held
- source-status/noetic-frame: no public source-context release; selected operative frame internal
- gate/release decision: release bounded lexical/category correction; hold full exposition

### Layer B ? bounded governed response
#### Hidden Premises
- Conceptual distinction is being treated as separable composition.
- "Depends on" is being used across senses without warrant.

#### Burden / Operation 1
##### Core Formulation
The deformation is a category-pressure move: real predication is collapsed into separable
part-composition, then dependence is imported through that collapse. The restoration vector
is lexical/category discipline: keep conceptual distinction, separable composition, and
ontological dependence in their proper order.

##### Bounded Response / operative submoves
¹B₁ [M9] - separate composition from conceptual distinction. Target: "composition." Operation: split separable parts from conceptual
distinction. Result: distinguishing knowledge from power does not entail separable parts.

¹B₂ [M9] - test dependence equivocation. Target: conceptual distinction -> ontological dependence. Operation:
test whether "depends on" is being used in one sense. Result: the equivocation is exposed.

##### TTP/operator trace
Trace: M9 predication-mode work is already local in ¹B₁ and ¹B₂; this trace summarizes, not substitutes for, execution.

### State/noetic re-read
- Cleared: composition / dependence pressure dissolved through the lexical and category split.
- ∇ route: this burden was selected because the composition-dependence hinge carried the highest
  dependency-reduction yield; broader attribute exposition remained held.
- Remaining input-anchored burdens: none in this prompt.
- Held routes rechecked: full attribute exposition and source-comparison remain held.
- Initial burden set: [B1] declared before terminal-state accounting.
- Field diagnostics: ∇·B: neutral after category split; ∇×κ: null.
- LoopBreak: not needed.
- Release status: closed for this input; no same-input eligible burden remains after the category correction.

### Closure/Reconstruction Witness
- N frames: selected operative frame held to lexical/category discipline; source-comparison frame held.
- Registers: Ω cleared for composition/dependence predicate; κ bounded; H contains only held exposition.
- Initial burden set: [B1]
- Terminal states:
  B1: landed / M9 / composition-dependence predicate split through ¹B₁/¹B₂
- Burden dependency graph: B1 (root).
- ∇·B: neutral
- ∇×κ: null
- `𝒞(Ψᴺ)`: positive; burden landed, residual pressure bounded, no loop remains live.
- `T_lang: Ψᴺ ⇢ Ψᴵ`: final wording is a coupling attempt toward the diagnosed objection field, not guaranteed uptake.

### Restorative Response
The restored order is that real predication does not become dependency merely by being
conceptually distinguishable. The live pressure has been narrowed to its category mistake.

### Closing Formulation
What cleared is the composition-dependence inference; what remains held is broader attribute
exposition. The governed takeaway is that the objection no longer follows from the terms it used.

## Default-Mode Worked Example - Boundary Discipline

**Input.** "This worldview's compassion/autonomy criterion is more humane than a God
who hides himself, condemns people to hell, and demands worship."

### Burden-Cycle 1
#### Layer A - Compact DSL/IR header
- live noetic burden: imported moral tribunal / worship-worthiness criterion.
- current bounded operator: tribunal authority test, not a route chain.
- active owner families: FPD for the imported criterion; M1/M1P if the criterion
  self-authorizes or exempts itself; M8 if its own frame defeats the verdict; M9 if
  cruelty, humanity, or worthiness language transfers creaturely predicates onto Allah.
- held until `R(H,Delta)`: accountability/hujjah, hiddenness/coercive-guidance,
  punishment/mercy/justice, source-worldview consequence, and interior motive.
- gate/release decision: release the tribunal burden; do not answer downstream material
  as final restoration before this burden lands.

#### Layer B - governed operation/release surface
- ¹B₁ [FPD] - expose the imported tribunal. Target: the imported compassion/autonomy tribunal. Operation: expose
  its claimed authority over divine action. Result: it cannot remain an unquestioned court.
- ¹B₂ [M1/M1-P] - test self-grounding or performed veto, when live. Target: a self-authorizing moral veto or worship-withholding
  criterion. Operation: apply the criterion to its own authority claim or performed veto.
  Result: the criterion must justify itself or lose tribunal status.
- ¹B₃ [M8] - trace the consequence, when live. Target: the opponent's own moral-source frame. Operation: trace
  what that frame can warrant on its own terms. Result: consequence pressure narrows or
  defeats the verdict it tried to impose.
- ¹B₄ [M9] - repair predicate mode, when live. Target: human moral-predicate transfer such as cruel, inhumane, or
  unworthy. Operation: repair predicate mode before doctrinal release. Result: creaturely
  limitation and sentiment no longer function as the measure of divine action.

#### Land(B) -> R(H,Delta)
`Land(B)`: the imported tribunal no longer governs the case as an untested judge.
`R(H,Delta)`: re-read the input. Field diagnostics: `∇·B` positive if downstream burdens remain;
`∇×κ` null unless a circular dependency is still detected. If accountability/hujjah, hiddenness/coercive guidance,
punishment/mercy/justice, source-worldview consequence, testimony, predication, grief/register,
or family-local proof-method pressure remains as a distinct target/function/restoration vector,
release the next burden-cycle, HOLD/PARTIAL it with reason, or mark a runtime limit. Keep it
inside Burden 1 only when the state re-read proves same target-family, claim-level,
source/noetic frame, claim cluster, and restoration vector.

### Boundary Lesson
This example does not teach "all hiddenness/accountability/punishment material belongs under
Burden 1." It teaches the gate. Same-burden consolidation preserves active owner/TTP submoves
inside Layer B; it does not collapse distinct noetic functions into a single umbrella burden.
Hard compound source-request cases often require several burden-cycles before final
Restorative/Application Response. Practical wording, source maps, and final warning usually
package already-landed burdens unless `R(H,Delta)` proves a new noetic burden.

---

## Related Files

| File | Relation |
|------|----------|
| `references/rubrics/output-release.md` | Governs what may be released before this file governs how it appears |
| `references/diagnostics/framework-pipeline.md` | Operative pipeline audit surface; bounded render sits here in the architecture |
| `references/diagnostics/recursive-state-transitions.md` | Canonical abstract owner for the post-render STOP / HOLD / RECURSE / PARTIAL decision |
| `references/diagnostics/case-state-schema.md` | `[Case State]`, `[Source Basis]`, `[Restoration Trace]` block schemas |
| `references/diagnostics/diagnostic-ir.md` | Internal Diagnostic IR and dispatch gate; default render derives from it but does not print it raw |
| `references/diagnostics/anti-patterns.md` | Failure examples for render surface-compliance failure, raw machinery leakage, and noetic-frame/source-status violations |
