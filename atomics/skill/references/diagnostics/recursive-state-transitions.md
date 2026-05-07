---
id: recursive-state-transitions
module_class: governance
canonical_path: skill/references/diagnostics/recursive-state-transitions.md
contract_version: "0.3.1.0"
load_when:
  - after a bounded restorative move has landed
  - deciding STOP / HOLD / RECURSE / PARTIAL
  - auditing state re-read, held-route reassessment, or same-response recursion
routing_effects:
  - defines abstract STOP / HOLD / RECURSE / PARTIAL semantics
  - requires post-render re-entry before closure
  - blocks premature STOP while an eligible live burden remains
  - blocks recursive argument dumps and inherited module stacking
emits:
  - recursive_state_transition
  - post_render_gate
  - state_carry_partition
blocks:
  - premature STOP
  - held-as-never-answer
  - state-re-read-as-user-reply-only
  - recursive dump after one refresh
companions:
  - framework-pipeline
  - diagnostic-ir
  - routing-precedence
  - output-release
  - diagnostic-render-contract
  - P7-restoration-stops
catalogue_registered: false
verification_status: L_check
direct_read_verified: true
failure_conditions_present: true
ir_consequences_present: true
minimal_pairs_present: true
hold_release_rules_present: true
compiled_runtime_eligible: true
operator_pack_eligible: true
---

# Recursive State Transitions

This file is the canonical abstract owner for STOP / HOLD / RECURSE / PARTIAL
state-transition semantics. It governs post-render re-entry, no-premature-STOP discipline,
same-response recursion eligibility, PARTIAL vs STOP, and the state carry/reset/re-evaluation
partition after a bounded move.

## Authority Boundary

This file owns only abstract recursive state-transition semantics.

- `references/procedures/P7-restoration-stops.md` owns concrete stop instances.
- `references/diagnostics/diagnostic-ir.md` owns typed fields, schema carrier, and the
  `post_render_gate` record.
- `references/rubrics/output-release.md` owns release amount, release order, and hold/release
  discipline before render.
- `references/rubrics/diagnostic-render-contract.md` owns visible render mode.
- `references/diagnostics/routing-precedence.md` owns route order and suppression.
- `references/diagnostics/framework-pipeline.md` owns the pipeline audit surface and forbidden
  shortcut chart.

This file does not create routes, module activation rules, IR fields, source owners, or coverage
claims.

## Runtime Notation / Meta-Noetic Memetic Compression Layer

This notation is operative compression for existing runtime behavior, not decorative formalism.
It creates no IR fields, route IDs, PF codes, module owners, or schema keys.

Legend:
- `N` = noetic structure.
- `m` = memetic claim / criterion / authority-node.
- `τ` = tribunal / evaluative criterion.
- `σ` = source-status.
- `B` = live noetic burden.
- `s` = operative submove.
- `H` = held set.
- `R` = state/noetic re-read.
- `Δ` = state change.

Core runtime:

```text
Input -> IR(N,m,τ,σ) -> B -> {s1...sn} -> Land(B) -> R(H,Δ) -> STOP/HOLD/PARTIAL/RECURSE
```

Submove / recursion:

```text
sᵢ != Bᵢ
```

Gloss: an operative submove inside one burden is not a new burden-cycle.

Collapse:

```text
Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB
-> {facet1...facetn} ⊂ {s1...sn}
-> ¬RECURSE
```

Gloss: same tribunal, source-frame, and claim-cluster collapse into one burden-cycle unless
`R` licenses a genuinely new input-anchored `B`.

Source-status:

```text
σ ∈ {contrast, opponent-position, genealogy, historical note, held material, bounded comparison}
-> σ != operative warrant
```

Gloss: non-operative sources cannot become proof without explicit reclassification.

Noetic-frame non-equivalence:

```text
N_Ashʿarī != N_Māturīdī != N_Taymiyyan
```

Gloss: contradictory noetic frames are not co-valid operative supports; only the selected
operative `N` may warrant the move.

Held carry:

```text
H(n+1) = (Hn ∪ InputLive_n) - Released_n
```

Gloss: held material carries across cycles until released or resolved.

Re-read:

```text
Land(B) -> R
R required before STOP/RECURSE
```

Gloss: a burden must land before re-read; re-read must license closure or recursion.

## State Model

`STOP` is valid only after state re-read confirms that the current governing blocker has been
addressed, no eligible live burden already present in the original input remains live, no held route
became releasable after the move, and P7 permits stopping.

`HOLD` is valid only when remaining material exists but its release signal is absent because a
stop, register-hold, semantic gate, thin-basis rule, or other hard rail still blocks it.

`RECURSE` is required when another live distortion remains in the same input, or when a held route
becomes newly eligible after the current pass clears its blocker.

`PARTIAL` is required when token, tool, or interaction limits prevent completion while recursive
pressure remains. Do not emit a false STOP in that condition.

## TTP Entry / Exit Criteria

Recursion is auditable only when each TTP has entry criteria, operation criteria, and exit
criteria. These criteria are internal runtime checks; they do not create new routes, IR fields,
or visible default-mode template slots.

**TTP entry criteria:**

1. Validated IR exists and names the current live burden.
2. Routing precedence selected one current bounded operator, not a route chain.
3. The TTP owner is justified by the current IR state or by refreshed state after a prior burden-cycle.
4. The TTP has a bounded target inside the active live noetic burden.
5. Output-release permits the operation now; otherwise the route is HOLD or PARTIAL.
6. No P7 stop, register-hold, semantic gate, thin-basis rule, or absent release signal blocks it.

**TTP operation criteria:**

1. The operation must do the owning TTP's work, not merely name the TTP label.
2. Operative submoves must preserve target -> operation -> result.
3. `Operation:` lines must begin with one of the closed operative verbs already used by
   the framework: `split`, `distinguish`, `test against own grounds`, `disambiguate`,
   `classify`, `audit`, `reclassify`, `narrow`, `expose`, `re-read`, `sequence`,
   `refuse jurisdiction of`, or `clear`. Generic verbs such as `address`, `discuss`,
   `explore`, `engage`, or `consider` are non-operative operation verbs and do not
   satisfy execution.
4. Multiple operative submoves may land one live noetic burden, but they remain internal until the burden landing.
5. A downstream TTP cannot inherit eligibility from the initial route read; it must be selected
   from the refreshed state after the prior bounded operation.

**Owner-specific operation floor:**

Generic `target -> operation -> result` syntax is not enough. The operation must apply the
owning file's minimum operation floor: the specific pressure dimensions, branch tests,
definition splits, or criterion tests required by that owner. A TTP named without its
owner-specific operation floor is label cosplay even when a Target/Operation/Result line
is present.

Default output must not narrate that an owner floor was applied. Phrases such as "owner
floor is applied", "owner-floor pressure", "the TTP has to change something",
"burden-completeness check", or "the operation is bounded to the target named above" are
test-harness proof, not TTP execution. If the public answer needs target -> operation ->
result, the terms must be filled with case-specific pressure and visible state change,
not compliance explanation.

Each TTP owner used in a burden-cycle must be able to answer:

1. Which owner rule or anchor made this TTP eligible?
2. Which exact premise, predicate, criterion, or warrant is the target?
3. Which owner-specific operation was performed?
4. What result changed the current burden-state?
5. Which remaining material is held, released, or newly eligible after the result?

**TTP exit criteria:**

1. The pass states or internally records the TTP result.
2. The burden landing is known: landed, held, partial, or failed to clear.
3. state re-read rechecks held routes and remaining same-input live burdens.
4. The next decision is STOP, HOLD, RECURSE, or PARTIAL.
5. Restoration synthesis or pastoral note appears only after this exit and refresh license it.

**Land(B) requirements:**

`Land(B)` is not a phrase in the output. The burden has landed only when:

1. every materially necessary submove for the released live burden has either been operated
   on, explicitly held by a gate, or marked PARTIAL with a concrete limit;
2. at least one owner-specific result changes the live burden's status, not merely its
   wording;
3. the cumulative-state delta is known: what the burden looked like before the operation,
   what changed after the operation, and why the next state is narrower, cleared, held, or
   partial;
4. no held route has been silently answered inside Layer B;
5. state re-read can identify STOP, HOLD, PARTIAL, or a licensed NewB from the changed
   burden-state.

A sentence such as "this burden lands" after generic prose is invalid unless the preceding
operation supplies the cumulative-state delta.

If entry criteria are missing, the TTP is not activated. If operation criteria are missing, the
TTP is label cosplay. If exit criteria are missing, recursion is unauditable and closure is
premature.

## Depth And Stop Guards

Depth is governed by live-burden traversal, not by how many arguments or headings can be written.
Each recursive depth increment requires:

```text
prior burden landing -> state re-read -> next input-anchored live burden -> new bounded operator
```

Depth guard rules:

- No recursive depth increase without a burden landing and state re-read.
- No repeated operator at the next depth unless refreshed state supplies a new bounded target.
- No downstream release from the initial itinerary; refreshed state must license every next pass.
- No total downstream dump after one refresh.
- No submove explosion: if a burden requires more than three major operative submoves, the
  runtime must run the submove saturation gate before releasing the fourth.
- If response, tool, or interaction limits prevent the next eligible burden, use PARTIAL with the
  concrete limit and the named next live burden.
- If the next live burden remains live but a release signal is absent, use HOLD with the blocker.
- STOP requires proof that no eligible same-input live burden remains, no held route became eligible,
  and P7 permits closure.

### Submove Saturation Gate

Before adding another major `s` inside the current `B`, ask whether the candidate submove
still shares all of the following with the active burden:

```text
same operative target-family
same tau / claim-level
same source/noetic frame
same claim cluster
same restoration vector
not already handled by a prior submove result
```

If the answer is yes, the submove may remain internal to `B` when it is materially necessary
for burden completeness. If the answer is no, do not keep expanding the submove list. Run
`Land(B) -> R` and let the re-read decide STOP, HOLD, PARTIAL, or NewB.

More than three major operative submoves inside one burden-cycle is allowed only when the
submove saturation gate records necessity and cohesion. Otherwise the fourth major move is
either a licensed NewB after re-read, held, or PARTIAL. Size, component availability, or a
desire for a fuller answer never licenses a fourth major submove by itself.

The convergence target is governed recursive sufficiency: the live same-input noetic structure has
been restored as far as the current gates permit. The target is not maximal topic coverage and not
shortest possible prose.

## Post-Render Re-Entry Gate

After every bounded restorative move, run state re-read before closure. The post-render gate asks:

1. What cleared this pass?
2. What remains live in the same input?
3. Which held routes were rechecked?
4. Did any held route become newly eligible?
5. What is the next eligible pass, or is it `none`?
6. Is the correct governance decision STOP, HOLD, RECURSE, or PARTIAL?

The gate is not a new routing pass. It is the enforcement point that keeps the validated IR live
after the response has made a bounded move.

## No Premature STOP

Core recursive traversal rule: no premature STOP while an eligible live burden remains.

An eligible live burden is a same-input distortion, held route, or downstream burden that was already
present in the original input and becomes releasable after the current blocker clears. STOP is
invalid merely because the first strong move landed. If another eligible live burden remains, choose
RECURSE for the next bounded pass or PARTIAL when limits prevent that pass.

STOP is valid only when state re-read confirms:

- the current blocker cleared,
- no eligible live burden already present in the original input remains live,
- no held route became releasable,
- continuing would be argument-stacking rather than governed traversal, and
- P7 permits stopping.

## Same-Response RECURSE

Same-response recursion is an internal state-transition, not a user-reply requirement. It is
required when the gate confirms this same-response RECURSE trigger checklist:

1. Current blocker cleared.
2. Another already-present burden remains live.
3. The next pass has a present release signal.
4. No P7 stop, register-hold, semantic gate, thin-basis rule, absent release signal, or limit
   blocks release.

When all four conditions hold, RECURSE is required in the same response. When the next pass is
eligible but limits prevent it, use PARTIAL. When the next pass remains live but its release signal
is absent, use HOLD. STOP is invalid.

**NewB license test:**

`NewB` is licensed only when state re-read can show all six facts:

1. the prior `B` landed through owner-specific operation, not merely through section shape;
2. the cumulative-state delta is explicit enough to show what changed;
3. the proposed next burden was already present in the original input, prior held material,
   or the collapse radius of the prior burden;
4. the proposed next burden differs from the prior `B` by target-family, claim-level,
   restoration vector, or governing noetic pressure;
5. the proposed next burden was not already answered as an operative submove;
6. release is not blocked by stop, register, semantic, thin-basis, source-use, or limit gates.

If any fact is missing, the next material is not NewB. It remains an operative submove,
HOLD, or PARTIAL.

Default Final-Output Preflight Gate must enforce this decision. It is not merely a
visible-format sanitizer. After the first bounded move, final-output preflight asks:

- what cleared?
- what remains live?
- was the remaining live burden already present in the original input?
- is it now eligible?
- is any stop/register/semantic/thin-basis gate blocking it?

If another eligible same-input live burden remains after the current blocker clears, default
output must either RECURSE into one bounded next pass with a prose state transition, or
mark PARTIAL if limits prevent doing so. It may not silently STOP. Silent STOP while
eligible burden remains is invalid. Clean prose without this state re-read and
STOP / HOLD / RECURSE / PARTIAL decision is still invalid.

This decision is not satisfied by a preplanned essay sequence. Headings such as "Step 1",
"Step 2", "Step 3", "Step 4", "Move 1", "Move 2", or "Move 3" do not show state re-read.
Same-response RECURSE requires: the
first bounded move landed, the state re-readed, the next live burden was already present in
the original input, the gate permits release, the next pass is bounded, and the next pass
refreshes state again before any further release.

## Hold And Release Semantics

Held means traversal-delayed, not response-delayed. Held also means traversal-delayed, not
permanently suppressed.

Holding downstream material is not a promise to wait for another user message. After a bounded
move lands, state re-read must recheck held routes. If a previously held route becomes eligible
and no stop or gate blocks it, it becomes the next bounded pass. If it remains blocked, HOLD is
valid and the blocker must be named.

## Recursion Discipline

Recursion is not argument dump. It is one live burden per burden-cycle: upstream before downstream, current-pass
modules only, state re-read after each move, and no total downstream release at one refresh.

No module stacking is permitted without a prose state-change transition. A visible response may
compress the audit surface, but internally it must still pass through a bounded move, state re-read,
and a renewed decision before releasing the next live burden.

Default mode may compress that transition into ordinary prose, but it may not hide it. A
valid default transition says what cleared, what remains live, why the next live burden is now
eligible, and why the next state is RECURSE rather than STOP, HOLD, or PARTIAL.

Default governed prose follows the mandatory compact DSL/IR header + Layer B + State/noetic
re-read burden-cycle shape in `diagnostic-render-contract.md`, then repeats only until governed
recursive sufficiency.

Default mode must not print literal state fields such as `Recursion decision:`,
`next_eligible_pass:`, `post_render_gate:`, or STOP / HOLD / RECURSE / PARTIAL as a visible
governance label. Literal state labels and post-render fields are for `:dsl`, internal/development audit,
pass-review, or diagnostic trace. Default RECURSE is valid only when the answer visibly
performs the transition and the one bounded next pass; naming the decision is not execution.

### Minimum Visible Transition Spine

Default mode suppresses raw visible IR but does not suppress recursive execution.

**Formal terminology:** Use final runtime terms, not debugging shorthand.
- Live noetic burden: the input-anchored claim, criterion, structural pressure, or noetic feature currently being cleared.
- Operative submove: a TTP operation inside the current live noetic burden.
- Burden-cycle: one Layer A -> Layer B -> state re-read traversal of a live noetic burden.
- Burden landed: the current live noetic burden has produced a result sufficient for re-reading state.
- Next live burden: another input-anchored burden licensed after re-read.
- State re-read / noetic re-read: the post-burden reassessment after the current burden lands.

A live noetic burden is not a topic count. Use the canonical invariant:
`Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`.
Gloss: the current `B` may require several `s` before `Land(B)`; recursion waits for `R`.
Anchor wording: the current live noetic burden may require several operative submoves.
Operative submoves are not burden-cycles. Live-burden boundary is set by the noetic burden being
cleared, not by the count of TTP names or visible headings.
Burden completeness rule: once `B` is released, materially necessary sub-burdens inside that
same `B` must receive matched TTP/operator treatment before `R`. Do not answer only the headline
objection, skip internal sub-burdens, replace routed execution with generic prose, or jump to a
broad conclusion. `R` may then expose deeper governing epistemology as `NewB`, first-order
repairs, held higher-order rebuttals, or STOP/HOLD/PARTIAL/RECURSE; `NewB` is not licensed until
the released `B` and its necessary `s` have actually been operated on.

In moral-protest / hiddenness / worship-worthiness cases, Imported-criterion testing,
hujjah/accountability correction, punishment narrowing, guidance-as-coercive-proof correction,
TST/source-worldview source-status discipline, and identity-stabilization caution are `s` when
they serve the same imported-tribunal `B`. They become later burden-cycles only if `R` licenses a
genuinely new input-anchored `B`.

Multi-burden does not mean multi-recursion by default. The model must not split topical components
into new burden-cycles merely because they name hiddenness, punishment, source-status,
source-worldview, or identity-stabilization.
Forbidden failure name: topical components split into burden-cycles.
Short form: hiddenness/punishment/source-status can be operative submoves under one burden.
Bad split pattern: imported tribunal / hiddenness / punishment / TST source-worldview.

Recursion begins only when `Land(B) -> R` licenses a new input-anchored live burden that remains
after the submoves have done their work. If the facet has already been handled as `s`, it cannot
be promoted into the next cycle just to create serial depth.
Anchor wording: Recursion begins only when the current gated operation lands.
Equivalent legacy wording: Recursion begins only after that burden lands, the state is re-read,
and another input-anchored burden is licensed.

A route chain is not a bounded operator. `FPD -> M1 -> DO-8 -> M8 -> restoration` is a route itinerary,
not a current live noetic burden. Current bounded operator names one burden-level function such as
`imported moral tribunal / worship-worthiness criterion burden`. Smaller phrases such as
`hujjah/accountability correction` or `guidance-as-coercive-proof correction` are operative
submoves when they merely test or narrow that same burden.
hujjah/accountability correction can be operative submove. guidance-as-coercive-proof correction can be operative submove.

**Recursion defined (for default mode):**
```text
topic transition != recursion
component tour   != recursion
burden landed -> state re-read -> next input-anchored live burden -> next burden-cycle
```

State re-read enumeration of remaining input-anchored live burdens plus one newly routed bounded pass per refresh = recursion. A TTP's visible execution spine is:
target -> operation -> result -> state re-read.

A recursive response must:
1. Land the governing live noetic burden in the current burden-cycle.
2. Run state re-read / noetic re-read.
3. Enumerate remaining already-present live burdens from the original input.
4. Route one bounded live burden per burden-cycle; a burden may contain multiple operative submoves.
5. After each burden-cycle, re-read state again and enumerate remaining burdens.
6. STOP only after proving no input-anchored eligible burden remains, or remaining burdens are
   HELD with release conditions, or limits force PARTIAL with the next live burden named.

The transition spine must mark state re-read, not topical movement. Each transition must show:
(1) what the prior burden landed, including operative submove results, (2) what input-anchored
live burden the noetic re-read identified as remaining, and (3) what the next burden-level
function is. If no transition marker appears when re-read licenses another input-anchored live
burden, the output is clean essay cosplay and must be rewritten before emission.

Valid internal progression for the first live burden:
"The same tribunal test has three operative submoves. First, the secular moral criterion has to
justify its authority. Second, the accusation that Islam punishes mere non-belief has to be
narrowed through hujjah/accountability. Third, hiddenness has to be corrected where it assumes
coercive individualized proof. These submoves serve one burden: whether the imported criterion
has authority to declare God unworthy of worship."

Valid transition to a new burden:
"That burden has landed: The imported criterion no longer governs as judge; the imported
tribunal no longer stands as an unquestioned judge over divine action. What remains live
is a different noetic aspect: the foundational epistemology by which moral and evidential
standards claim authority at all. That is the next live burden."

Invalid default-mode recursion shapes:
- "Step 1 / Step 2 / Step 3" as fake recursion.
- "Move 1 / Move 2 / Move 3" as fake recursion.
- "Pass 1 / Pass 2 / Pass 3" used for FPD, M1, DO-8, M8, or restoration fragments inside one burden.
- "Pass 1 / Pass 2 / Pass 3" used for imported criterion, hujjah/accountability, and
  guidance-as-coercive-proof corrections that all serve the same imported-tribunal burden.
- "Burden 1 / Burden 2 / Burden 3 / Burden 4" used for imported tribunal, hiddenness,
  punishment, and TST/source-worldview without a state/noetic re-read proving that each is a
  new live burden rather than a subordinate submove under the same tribunal burden.
- `Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration`.
- silently stopping after criterion correction when another eligible live burden remains.
- restoration synthesis or pastoral note before the active burden lands and state is re-read.

TTP labels do not satisfy execution. A valid default burden-cycle must show the bounded target,
operation performed, result of the operation, and burden landing before any next burden-cycle.
In short:

```text
live noetic burden -> operative submove(s): target -> operation -> result -> burden landed -> state re-read
```

State re-read follows the burden landing, not each route label in a preplanned itinerary. If the
same imported tribunal remains the live target, FPD, M1, DO-8, M8, hujjah/accountability
correction, guidance-as-coercive-proof correction, and identity/source-status clarification remain
operative submoves under the first live burden. They are not burden-cycles until state re-read
licenses a new input-anchored noetic aspect.
TTPs execute across refreshed case-states, not as a one-time itinerary from the initial read.
The initial case-state selects only the current bounded operator. Once that operator lands,
state re-read re-evaluates upstream/downstream, higher-order/first-order, and held material
already present in the same input. The next TTP, if any, must be selected from that refreshed
state. Eligible same-input burdens must be traversed or marked PARTIAL; untriggered future
contingencies stay held with a release condition.

Length is governed by burden-cycle live-burden traversal: bounded pass, state re-read, next
eligible same-input burden, bounded pass, refresh again, then STOP, HOLD, RECURSE, or PARTIAL.
Do not compress default output into premature STOP merely to keep it short.
PARTIAL requires concrete limit reason: name the live burden and the response/tool/interaction
limit preventing traversal. A bare PARTIAL label is not a release decision.

Positive target: governed recursive sufficiency. Recursion continues until the live same-input
noetic structure has been restored as far as the input and release gates permit: case-state read,
governing live burden, bounded TTP operation, result, state re-read, then the next eligible live
burden or HOLD/PARTIAL/STOP.

This is the recursive-state form of `anti-patterns.md` Route Cosplay Failure: visible
recursion label != recursive traversal; pass-by-pass state re-read = recursive traversal.
It is also the recursive-state guard against Clean Essay Cosplay: every pass must show a
transition before the next bounded operator starts.

Compact audit shape when recursion must be visible in `:dsl`, internal/development audit, pass-review, or
diagnostic trace:

```text
Live noetic burden:
Why already present:
Released module(s):
Bounded move:
state re-read:
Governance: STOP / HOLD / RECURSE / PARTIAL
```

## Grounded Noetic Re-Read Shape

State re-read / noetic re-read is not satisfied by field-shape alone. The block must be
grounded in the preceding burden-cycle. This file owns the auditability rules.

The minimum grounded noetic re-read shape, when no canonical block already governs the
render, is:

```text
Noetic re-read:
- burden landed:
- still live:
- held:
- recursion decision:
- next licensed live burden:
```

This shape introduces no new IR fields. It is a render-time rephrasing of the existing
post-render gate fields (`cleared_this_pass`, `remaining_live_distortions`,
`held_routes_rechecked`, `recursion_decision`, `next_eligible_pass`).

**Field-grounding rules (mandatory; checker-enforced):**

1. `burden landed` must be traceable to the immediately preceding burden-cycle's burden
   result. A `burden landed: yes` claim that follows no operative submove producing a
   `target -> operation -> result` chain is a formatted but ungrounded noetic re-read and
   must be rejected. The Layer B above the re-read must contain at least one operative
   submove whose result feeds the burden landing.
2. `still live` must enumerate items already present in the original input, in held
   material from prior burden-cycles, or in a load-bearing dependency whose support
   collapsed when this burden landed. A `still live` entry that introduces material not
   anchored in those sources is unanchored introduction; the entry is invalid.
3. `held` must name material that was already named as held in a prior Layer A or whose
   release signal is currently absent. Treating a previously released item as held is
   regression and must be rejected.
4. `recursion decision` (`STOP | HOLD | RECURSE | PARTIAL`) must be consistent with
   `burden landed`, `still live`, and `held`:
   - `STOP` requires `still live: none` (or all entries explicitly held with absent
     release signal) and no held route newly eligible.
   - `HOLD` requires at least one named blocker for each remaining `still live` item.
   - `RECURSE` requires at least one item in `still live` for which release is now
     permitted.
   - `PARTIAL` requires a concrete limit reason and a named next licensed live burden.
5. `next licensed live burden` must be anchored in `still live`, in held material whose
   release signal has now appeared, or in the original input. It must not appear from
   nowhere. If `recursion decision` is `STOP` or `HOLD`, this field is `none` or names
   what would be released on a future refresh.
6. A new burden-cycle may begin only after a noetic re-read whose `burden landed` is
   grounded by rule 1 and whose `next licensed live burden` is grounded by rule 5.
   Beginning a new burden-cycle from a re-read block alone, without a prior operative
   result, is invalid.
7. `state delta` / cumulative-state delta must be known even when not printed as a raw
   field in default mode: the response must show what changed, what narrowed, and why the
   next burden is different from the burden just landed. A re-read that merely repeats
   "cleared / held / decision" without a changed claim-state is rubric-schematic and invalid.

**Failure conditions:**

- `burden landed: yes` asserted without an operative-submove `target -> operation -> result`
  in the immediately preceding Layer B.
- `still live` lists a topic not present in the original input, prior held material, or the
  preceding burden-cycle's collapse radius.
- `next licensed live burden` is asserted but `still live` does not contain it and held
  material does not contain it.
- `recursion decision: STOP` while `still live` is non-empty without explicit HOLD reasons.
- `recursion decision: RECURSE` while `still live` is empty.
- A new burden-cycle begins after a re-read whose `burden landed` is asserted but not
  produced through an auditable operative submove.
- A new burden-cycle begins after the prior re-read fails the NewB license test.
- A burden-cycle exceeds three major operative submoves without the submove saturation gate.
- A TTP is named and paired with generic prose but does not satisfy the owner-specific
  operation floor.
- A noetic re-read provides a decision but no cumulative-state delta.

These conditions are auditable by source review; the checker enforces a representative
subset of them on structural fixtures.

The grounded shape is render-mode-agnostic. Default mode renders the same content under
`State/noetic re-read` without raw post-render gate fields. `:dsl` / internal/development
audit may surface the field block. In every mode, the grounding rules apply.

## Source-Status & Noetic-Frame Non-Equivalence Discipline

This section is canonical for source-status discipline and noetic-frame non-equivalence.
It governs how sources are used inside burden-cycles. It introduces no new routes, IR
fields, or module owners; it formalizes existing requirements.

**Thesis-protection rule.** The framework must not treat contradictory theological or
noetic structures as equally acceptable operative frames. Umbrella terms such as
`classical theology`, `classical theologies`, `classical Islamic theology`,
`the classical tradition`, `mainstream kalam`, or `Ashari/Maturidi tradition` must not
be used to flatten Ashʿarī, Māturīdī, Atharī, Taymiyyan, kalāmic, falsafah-inflected, or
generic "classical Islamic theology" frames into one unified operative authority. This
rule applies inter-school (across Ashʿarī / Māturīdī / Atharī / Taymiyyan / falsafah)
and intra-school (treating a named school as internally uniform on a school-sensitive or
disputed claim).

**Source-status taxonomy.** Every source used in a burden-cycle is marked with one of
the following statuses; a source may appear in only one status per burden-cycle:

```text
operative support     - the source is being used as warrant for the operative conclusion
contrast              - the source is named to mark a differing noetic structure
opponent-position     - the source is named as the position being engaged
historical note       - the source is named as historical or genealogical context
genealogy             - the source is named as the genealogy of a dispute
held material         - the source is named as held by routing/release governance
bounded comparison    - the source is named under an explicit bounded comparison
```

**Source-status non-equivalence rule.** A source marked as `contrast`, `opponent-position`,
`historical note`, `genealogy`, `held material`, or `bounded comparison` must not be used
as `operative support` in the same burden-cycle unless explicitly reclassified with a
named justification: a sentence stating the reclassification, the reason, and why the
selected operative noetic frame is preserved. Cross-frame prestige stacking (citing
contradictory schools side-by-side as one authority) is forbidden in every mode.

**Default public-render source restriction.** In default output, school, author, citation,
genealogy, external philosopher, theologian, framework, or contextual-source references are
not public-render material unless the user explicitly asks for them or validated IR
specifically requires source-comparison. Default citation allowance is restricted to Qur'an,
Sunnah, and sound narrations from the Salaf; if any of these are used, each must be directly
referenced through an external source. Do not use al-Ghazali, Ash'ari, Maturidi, Christian
philosophers, external theorists, or any named scholar/school as public-render support in
default mode.

**Method-source non-branding rule.** The framework is not publicly framed as belonging to,
deriving from, or being branded under a named scholar, named school, newly coined methodology,
new creed, new aqidah, or new noetics. Public/default framing remains sound noetic diagnosis
-> detection of deformation/concealment/criterion import -> restoration of proper
warrant/order and proper cognitive function in a congenial epistemic milieu. Methodological
consonance may be preserved internally without source-branding.

**Operative-frame selection rule.** Each burden-cycle proceeds from one selected
operative noetic frame. Other frames may be named only under non-operative statuses.
The selected frame must be visibly identified when source-status discrimination would
otherwise be ambiguous; phrases such as `the classical tradition agrees` or
`Islamic tradition says` are forbidden when the claim is school-sensitive or disputed.

**Cited-agreement rule.** When agreement across frames is asserted, the response must
mark whether the agreement is substantive (the structural conclusion holds in each frame
on each frame's own grounds) or merely verbal/surface-level (the words coincide while
the operative grounding differs). Verbal agreement is not operative support.

**Failure conditions:**

- An umbrella term flattens contradictory schools into one authority.
- A contrast-marked source is then used as operative warrant in the same burden-cycle
  without explicit reclassification.
- A burden-cycle cites Ashʿarī or kalāmic authorities as operative support for a
  Taymiyyan / Atharī operative conclusion (or vice versa) without source-status marking.
- A response asserts `the classical tradition agrees` for a school-sensitive claim.
- A response asserts agreement across frames without marking substantive vs. verbal.
- Identity-frame is treated as operative support for a content claim without
  source-status caution.

**Operative-warrant sentence convention.** When any non-operative source (`contrast`,
`opponent-position`, `historical note`, `genealogy`, `held material`, `bounded comparison`)
is named in `:dsl`, internal/development audit, pass-review, diagnostic trace, or an
IR-required source-comparison render, that rendered source-status block must include one
prose sentence in this minimum shape:

```text
Operative warrant: [selected operative noetic frame]; the [contrast | opponent-position
| historical | genealogy | held | bounded-comparison] source above does not contribute
to this warrant; specifically, [named element from the non-operative frame] is not used
as a premise here.
```

The final clause is the specific non-premise clause. This adds no new IR field. It converts the implicit operative dependence into an
explicit claim that can be audited. A burden-cycle that names a non-operative source
without this sentence is at risk of source-status label-emission without substantive
discrimination: the label emits compliance while the operative reasoning silently relies
on the contrast frame's content. The convention is normally not public default material; it is expected
in `:dsl` / internal/development audit, and is the canonical disambiguator when a reviewer needs to verify
that the contrast was held to its named status.

**Allowed shapes:**

- `Source-status: operative support. The selected operative frame is X; the conclusion
  holds inside that frame.`
- `Source-status: contrast only. This Ashʿarī formulation is named only to mark a
  differing noetic structure. It is not used as warrant for the operative conclusion.`
- `Source-status: historical note. Some later kalāmic treatments frame the issue
  differently; this is not the operative authority for this burden-cycle.`
- `Source-status: bounded comparison. The Māturīdī and Taymiyyan framings agree
  verbally that X, but the operative grounding differs; the operative warrant in this
  burden-cycle is the selected frame only.`
- `Operative warrant: selected Atharī predication frame; the contrast source above does
  not contribute to this warrant; specifically, the later kalāmic formulation is not
  used as a premise here.`

**Forbidden shapes:**

- `Classical Islamic theologies, including Ashʿarī, Māturīdī, and Taymiyyan approaches,
  all provide acceptable ways to ground the answer.`
- `The classical theological tradition, from al-Juwaynī and al-Ghazālī to Ibn Taymiyyah
  and Ibn al-Qayyim, agrees that ...`
- `Ashʿarī theology teaches X` when the point is internally disputed within Ashʿarī or
  is school-sensitive across kalāmic and Atharī frames.
- `Māturīdī theology teaches X` under the same conditions.
- `Islamic tradition says X` where the claim is school-sensitive and structurally
  disputed.
- A list of sources hides disagreement behind breadth.
- `Ashʿarī, Māturīdī, and Taymiyyan approaches are all classically acceptable theological
  routes here.`
- A contrast-marked source is named, then immediately used as evidence for the operative
  conclusion in the next sentence under the same burden-cycle.
- `This is the daee-epistemics method of [named scholar/school]`, `a new aqidah/noetics`,
  or any authority-by-association method branding.
- Default output uses al-Ghazali, Ash'ari, Maturidi, Christian philosophers, external
  theorists, genealogy, or school-label context as support without explicit user request
  or validated source-comparison IR.

These failures are not citation-style errors. They are thesis-protection failures: the
skill's diagnostic compiler must discriminate noetic structures, not flatten them.

## State Carry / Reset / Re-Evaluation Table

This is the canonical State Carry Table for the abstract refresh operation.

| State component | Carry rule |
|----------------|------------|
| NS code, deformation, concealment mode, DO-orient | Carried: stable diagnostic read persists until a fresh differentiating signal changes it |
| Restoration target | Carried if still unmet; updated if the landed move partially resolved it |
| Alignment state, Recognition strength | Carried as progress state; these do not reset merely because a pass ended |
| What remains live | Carried as the live input to the next V1 opening |
| Held routes / What is withheld and why | Carried across burden-cycles as a coherent set; never silently dropped |
| Matched modules | Reset: re-derived from refreshed state; not inherited from the prior pass |
| Layer B content | Reset: re-derived from refreshed state |
| Next move | Reset: one live move only; never a queue |
| Continuation eligibility | Re-evaluated fresh from the refreshed state; not inherited from the prior pass |

**Held-routes carry rule (cross-cycle).** Burden-cycle N's Layer A `Held routes` field
must be derivable from:

```text
Held(N) = (Held(N-1)) ∪ (input-anchored burdens not yet released) − (items released by Burden N-1)
```

New material introduced in Burden N's `Held routes` must be anchored in the original
input or in a load-bearing collapse-radius dependency that became visible when Burden
N-1 landed; it must not appear from nowhere. An item silently dropped from Burden N's
`Held routes` (without an explicit release event in Burden N-1's state re-read) is
held-material amnesia: the recursion has lost state, and the meta-noetic memetics
claim that the DSL/IR tracks live noetic state across the conversation is broken for
this trace.

A held noun phrase must also stay held semantically. If Layer A / compact `held` names
`full punishment doctrine`, `hiddenness`, `source-status`, or any other held item, Layer B
must not answer that item as topical commitment until a preceding state/noetic re-read
explicitly releases it with `Released: <item>`, `Released routes: <item>`, or
`Newly released routes: <item>`. Naming a held item as still held, withheld, or contrast
is permitted. Answering it without an explicit release marker is held-route semantic
leakage.

Failure conditions:

- Held item in Burden N-1 disappears from Burden N's Layer A without an explicit
  release event in Burden N-1's `Cleared` / `Newly released routes`.
- Held item named in Layer A or compact `held` appears in Layer B as an answered topical
  commitment before `Released: <item>` or an equivalent release marker appears in a
  preceding state/noetic re-read.
- Burden N's `Held routes` introduces material not anchored in the original input,
  prior held material, or the preceding collapse radius.
- A multi-burden response (≥ 2 burden-cycles) whose `Held routes` field is empty in
  every Layer A while the original input contained multiple input-anchored burdens.

## Failure Tests

- Failure condition: STOP is declared before state re-read names `next_eligible_pass: none`.
- Failure condition: a held route becomes eligible, but the response treats it as permanently
  suppressed.
- Failure condition: same-response RECURSE is refused solely because the user has not sent a new
  reply.
- Failure condition: default output prints `Recursion decision: RECURSE` or `next_eligible_pass:`
  as visible compliance instead of performing the prose transition and next bounded pass.
- Failure condition: "Move 1 / Move 2 / Move 3" headings replace state re-read and prose
  state transition.
- Failure condition: route legs are mislabeled as burden-cycles: FPD as Pass 1, M1 as Pass 2,
  DO-8 as Pass 3, M8 as Pass 4, or restoration as Pass 5 while Burden 1 has not landed.
- Failure condition: the current bounded operator is a route chain rather than one burden-level
  function.
- Failure condition: a TTP label is named in prose but the bounded operator is not actually
  selected, executed, and refreshed before downstream release.
- Failure condition: restoration synthesis or pastoral note appears before the active burden landing
  and state re-read.
- Failure condition: PARTIAL is collapsed into STOP when limits prevent an eligible next pass.
- Failure condition: multiple downstream arguments are dumped at one refresh instead of moving one
  live burden at a time.
- Failure condition: Component-Tour Cosplay — the response covers all topics detected at initial
  read without state re-read between passes, without enumerating remaining input-anchored live
  burdens after each pass, and without routing one bounded live burden per burden-cycle. Covering all
  topics is not recursion. A response that covers all topics in one essay still fails recursion.
  input-anchored eligibility after refresh ≠ topic presence in the prompt.

Minimal pair: a governed same-response recursion follows a landed move plus refresh plus renewed
permission; an argument dump accumulates downstream content without refreshed governance.

- Failure condition: ungrounded noetic re-read — a `Noetic re-read` block whose
  `burden landed` is asserted but the immediately preceding Layer B contains no operative
  submove with `target -> operation -> result` chain feeding the burden landing.
- Failure condition: noetic-equivalence prestige stack — Ashʿarī, Māturīdī, Atharī,
  Taymiyyan, kalāmic, or falsafah-inflected sources cited as one unified operative
  authority for a school-sensitive claim.
- Failure condition: classical-theology umbrella — `classical theology`,
  `classical theologies`, `classical Islamic theology`, `the classical tradition`,
  `mainstream kalam`, or `Ashari/Maturidi tradition` used as if it named one operative
  frame across contradictory schools.
- Failure condition: contrast-as-operative-support — a source first marked `contrast`,
  `opponent-position`, `historical note`, `genealogy`, or `held material` is then used
  as operative warrant in the same burden-cycle without explicit reclassification.
- Failure condition: held-route semantic leakage — Layer A names material as held, then
  Layer B answers that material as topical commitment before a preceding state/noetic
  re-read explicitly releases it.
- Failure condition: non-operative operation verb — an `Operation:` line begins with
  generic prose such as `address`, `discuss`, `explore`, `engage`, or `consider` rather
  than one of the closed operative verbs.
- Failure condition: intra-school flattening — a school is named as internally uniform
  (`Ashʿarī theology teaches X`, `Māturīdī theology teaches X`) on a claim that is
  internally disputed or school-sensitive without that qualification appearing.
- Failure condition: verbal-agreement smuggling — agreement across frames is asserted
  without marking whether the agreement is substantive or only verbal/surface-level,
  and the asserted agreement is then used as operative support.
