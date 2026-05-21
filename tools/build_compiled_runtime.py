#!/usr/bin/env python3
"""Build the generated compiled daee-epistemics runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from build_framework_pipeline import build as build_framework_pipeline
from compiled_runtime_lib import (
    BUNDLE_MAPPING_VERSION,
    BUNDLE_SOURCES,
    COMPILER_VERSION,
    EXTRA_INPUTS,
    GENERATED_WARNING,
    OUTPUT_ROOT_REL,
    RUNTIME_METADATA_COPIES,
    SOURCE_ROOT_REL,
    canonical_source_rel,
    build_section,
    catalogue_by_id,
    clean_compiled_dir,
    load_source_doc,
    out_dir,
    posix_rel,
    repo_root,
    sha256_file,
    source_path_for,
    source_rel_from_legacy,
)

DEV_ONLY_GENERATED_ROOTS = {"data", "scripts", "tests"}


def canonical_package_files_from_generated(generated_files: list[str]) -> list[str]:
    """Return generated runtime files that belong in the canonical user-facing package."""
    selected: list[str] = []
    for item in generated_files:
        if not item.startswith(f"{OUTPUT_ROOT_REL}/"):
            continue
        rel = item[len(f"{OUTPUT_ROOT_REL}/"):]
        if rel.split("/", 1)[0] in DEV_ONLY_GENERATED_ROOTS:
            continue
        selected.append(item)
    return sorted(selected)


def validate_sources(root: Path) -> list[str]:
    errors: list[str] = []
    seen_paths: set[str] = set()
    seen_ids: dict[str, str] = {}
    catalogue = catalogue_by_id(root)

    for bundle_path, sources in BUNDLE_SOURCES.items():
        if bundle_path != bundle_path.replace("\\", "/"):
            errors.append(f"bundle path must use POSIX separators: {bundle_path}")
        for rel_path in sources:
            source_path = source_path_for(root, rel_path)
            if rel_path in seen_paths:
                errors.append(f"source appears in more than one compiled bundle: {rel_path}")
                continue
            seen_paths.add(rel_path)
            if not source_path.is_file():
                errors.append(f"source file missing: {rel_path}")
                continue
            try:
                doc = load_source_doc(root, rel_path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{rel_path}: cannot read front matter: {exc}")
                continue
            for field in ("id", "module_class", "canonical_path"):
                if not doc.frontmatter.get(field):
                    errors.append(f"{rel_path}: missing front matter field {field}")
            expected_canonical_path = f"{OUTPUT_ROOT_REL}/{source_rel_from_legacy(rel_path)}"
            if doc.canonical_path != expected_canonical_path:
                errors.append(
                    f"{rel_path}: canonical_path mismatch: "
                    f"{doc.canonical_path!r} != {expected_canonical_path!r}"
                )
            if doc.module_id in seen_ids:
                errors.append(
                    f"module id appears in multiple compiled sources: {doc.module_id} "
                    f"({seen_ids[doc.module_id]}, {rel_path})"
                )
            seen_ids[doc.module_id] = rel_path

    for module_id, entry in catalogue.items():
        path = entry["path"]
        if module_id not in seen_ids:
            errors.append(f"catalogue module is absent from compiled mapping: {module_id} ({path})")
        elif source_rel_from_legacy(seen_ids[module_id]) != source_rel_from_legacy(path):
            errors.append(
                f"catalogue module path mismatch for {module_id}: "
                f"compiled {seen_ids[module_id]}, catalogue {path}"
            )

    for rel_path in EXTRA_INPUTS:
        if not source_path_for(root, rel_path).is_file():
            errors.append(f"extra input missing: {rel_path}")
    for rel_path in RUNTIME_METADATA_COPIES:
        if not source_path_for(root, rel_path).is_file():
            errors.append(f"runtime metadata input missing: {rel_path}")
    return errors


def generated_skill_text(root: Path) -> str:
    skill_path = source_path_for(root, "skill/SKILL.md")
    source_text = skill_path.read_text(encoding="utf-8")
    sections = source_text.split("---", 2)
    if len(sections) >= 3 and source_text.startswith("---"):
        frontmatter = f"---{sections[1]}---\n"
        body = sections[2].lstrip("\r\n")
    else:
        frontmatter = ""
        body = source_text

    instructions = f"""{GENERATED_WARNING}
# EXECUTION MANDATE - DEFAULT MODE

Default mode suppresses raw visible IR but does not suppress recursive execution.
Default mode is scriptless compact DSL-governed execution. Do not call or simulate repo/dev
route-check harnesses during canonical execution: no `daee_level3.py`, `route.py`,
`check_execution.py`, `features.json`, `route_plan.json`, `execution_verdict.json`, or
quality-gate claims. Those artifacts are optional developer validation, not public runtime
evidence and not a substitute for owner/source/depth behavior in `output.md`.

HARD-COMPOUND LAYER B EXECUTION BODY:
Hard-compound full traversal requires a visible Layer B operation body for every released burden.
Do not collapse a major burden into one generic "Bounded Response" paragraph or one
Target/Operation/Result block. A non-atomic released burden renders multiple owner-bearing
submove labels, preferably `B1_1 [FPD] - expose the imported criterion`,
`B1_2 [M1-P] - test the authority premise`, etc.; superscript/subscript notation remains
allowed, but ASCII `B<N>_<s> [owner]` is the checker-readable fallback. Each submove carries
Target, Operation, Result/state-change, and Contribution-to-Land(Bn). In a full hard-compound
traversal those fields are not stubs: each released submove must do its local noetic work in
case-shaped prose, naming the exact criterion/premise, applying the matched owner/operator, and
showing why that change contributes to Land(Bn). One-sentence Target/Operation/Result lines are
acceptable only for an explicitly compact PARTIAL/HOLD route, not for coverage_complete=true.
The bracketed token must be a compact owner/operator ID or pressure class with no spaces, such as
`[FPD]`, `[M1-P]`, `[M8]`, `[P1]`, `[P7]`, `[definition-discipline]`,
`[source-status-repair]`, or `[authority-order-repair]`. Put human-readable operation names
after the dash; do not put phrases like `[consequence trace]`, `[authority-order repair]`,
`[source-status discipline]`, or `[governed submove]` inside the brackets. Do not reuse the same
generic Operation/Result/Contribution wording across submoves in one burden; repeated
boilerplate is under-execution. For a 4+ burden hard-compound answer that claims full closure,
fewer than three visible owner-bearing submoves per released major burden is an execution-depth
warning; fewer than fifteen total submoves in a 5+ burden full traversal is normally
under-executed. If the output cannot pay that local execution cost, route HOLD/PARTIAL instead
of printing coverage_complete=true.

MANDATORY MRP ROUTE GATE:
In default `/daee-epistemics` output, every routed burden-cycle that prints Land(Bn), Field
diagnostics, LoopBreak, R(H,Delta), R(H,Δ), a next burden, HOLD/PARTIAL, or closure must print a
compact `[Mid-Reread Pressure]` block between the landed burden and the route. This is not
optional diagnostic ornament. The block is the visible proof that reread pressure ran. If the
block is absent, do not release the next burden, do not close, and do not print a route-bearing
reread.

MRP ROUTE CONSEQUENCE INVARIANT:
If MRP names remaining live pressure, non-neutral divergence, non-null/held curl, a graph edge,
a genuine downstream burden, proportionality, hiddenness, source-worldview, owner-floor, or
owner-body pressure, the output must release and land that burden, explicitly HOLD it with a
named gate/reason, or mark PARTIAL with the named blocked burden/owner before any Restorative
Response or Closing Formulation. STOP/COMPLETE is invalid while the same MRP record names an
unresolved live pressure. If a later burden, Layer B body, or closure graph edge follows from
the same answer, the prior MRP record is not final; it must mark the remaining burden as
genuine-dependent, emit a graph delta such as Bn -> Bn+1, and route RECURSE into the next burden.
Route in the compact MRP block is limited to STOP, HOLD, RECURSE, or LoopBreak(∇×T);
owner-load failure is rendered as Route: HOLD plus Boundary: PARTIAL / OWNER-BODY-NOT-LOADED:
<missing owner/path>.

PARTIAL OWNER-LOAD BOUNDARY:
When PARTIAL / OWNER-BODY-NOT-LOADED appears, do not continue into broad refutation,
Restorative Response, Closing Formulation, closure witness, or language such as "refuted" /
"closed" for the blocked burden. Give only the bounded diagnostic sketch licensed by loaded
owners, name the missing owner/path and next live burden, then stop.
Ordinary HOLD/PARTIAL not caused by owner-load failure must still render a `Burden N:` node,
submoves where licensed, `Land(Bn): PARTIAL / ...` or `Land(Bn): ...`, `[Mid-Reread Pressure]`,
and held-node accounting. Do not answer a named-worldview HOLD as pure prose plus a final
`PARTIAL / HOLD:` line. Held-node accounting must include `Initial burden set: [...]` and
`Terminal states:` lines using the same parseable `B1: state / owner-or-pressure / detail`
format as a closure witness.

MRP FIELD VALUE DISCIPLINE:
In the compact `[Mid-Reread Pressure]` block, field values are record values, not prose. Use exact
first-token values: `∇·T: neutral|settled|bounded|non-neutral`, `∇×T: null|resolved|held|non-null`,
`Finding: stable|genuine-dependent|partial-real|hidden-framework-recoil|doubt-churn|reorientation`,
`Pre-emption basis: none|graph-bound|commitment-bound|framework-bound`, and
`Route: STOP|HOLD|RECURSE|LoopBreak(∇×T)`. Do not add punctuation to those values. Each pressure
slot begins with an owner/TTP id, `pressure class: <name>`, or `coverage gap: <missing owner>`,
then an em dash and the release/hold/clear effect. For ∇·T / ∇×T, put a slash after the state
token, e.g. `∇·T: non-neutral / B2 remains live` and `∇×T: null / no circular dependency; the
chain is linearly traversable`; this keeps the active state machine-readable. Directed downstream
pressure belongs to ∇·T. Use ∇×T held/non-null only for circularity, churn, hidden-framework
recoil, label-pressure, dependency rotation, or self-reinforcing loop pressure; do not claim ∇×T
resolved unless a prior real curl/loop was named. `Boundary:` always begins
`T_lang does not imply guaranteed uptake`; append PARTIAL/owner-load text after a semicolon.
`genuine-dependent` requires `Route: RECURSE` and a graph edge; `stable` requires `Route: STOP`
and `Graph delta: none`; `partial-real` requires `Route: HOLD`.
`Reread:` must begin exactly `R(H,Delta)` or `R(H,Δ)`; `Landed delta:` must begin with `Delta`
or `Δ` and identify the burden/field change. `Pressure activations:` must render exactly six
bullet slots whose literal lines begin, after optional spaces, with `- freeze-landed-move:`,
`- dependency-tug:`, `- hidden-framework-recoil:`, `- entailment-pressure:`,
`- doubt-churn-guard:`, and `- reorientation-reminder:`. Do not omit the dash, colon, or any
slot. Do not replace those slot labels with generic pressure-class bullets.
The fixed labels are:
`freeze-landed-move`, `dependency-tug`,
`hidden-framework-recoil`, `entailment-pressure`, `doubt-churn-guard`, and
`reorientation-reminder`.
`MRP resultant:` is required and must state the finding-to-route/graph/HOLD consequence.
For doubt-churn / LoopBreak, `Graph delta:` is `none`; do not render `B1 -> LoopBreak` as a graph
edge. Put the LoopBreak consequence in `MRP resultant:` and `Route:`.
Each slot value must begin with an owner/TTP id, `pressure class: <name>`, or
`coverage gap: <missing owner>`. Do not begin a slot value with only `B1`, `B2`, `none`,
`cleared`, or ordinary prose. Inactive slots still render as `pressure class: none` or
`pressure class: cleared`, followed by the effect.

MRP RECONSTRUCTIBILITY / NODE-LINEAGE ACCOUNTING:
MRP is not a rendered note. A valid routed output must let the input be reconstructed as node
process: input -> burden nodes -> submove nodes -> Land(Bn) or partial Land(Bn) -> R(H,Delta) ->
MRP pressure resultants -> graph/field_witness delta or explicit no-edge ->
STOP/HOLD/RECURSE/LoopBreak/closure -> restoration aim. If MRP cannot be mapped to this lineage,
it is ornamental and cannot license closure, HOLD, RECURSE, or LoopBreak.

HARD-COMPOUND DEPTH FLOOR:
Hard-compound named-worldview, source-worldview, public-reason, authority-order, moral-tribunal,
or multi-anchor shubhah cases require Brandolini-scale traversal: the answer must be
substantially larger than the prompt because it must unpack the noetic load. Do not compress
these cases merely because the input is short. A real traversal normally renders 4-6 burdens,
3-5 visible owner-bearing submoves per major burden, a Land(Bn), inter-burden MRP, R(H,Delta),
and carried graph state after each landing. Output mass is an Andon, not the proof standard:
topology decides proof, while mass decides whether the claimed topology was plausibly executed.
Size without topology is bloat; topology with skeletal local execution is under-execution.
For a full traversal, estimate plausibility from the topology claimed: governed surface and
Layer A/B operation bodies; every fully released burden and its submoves; every MRP invocation
and resultant; graph/field_witness accounting; closure witness; and restorative response.
Empirical older compact outputs may cluster near 38-50 KB, but MRP-heavy 5+ burden full
traversals with repeated MRP, graph accounting, closure, and restoration normally need a much
larger visible cost. Treat roughly 60 KB as a serious Andon for Smoke-6-shaped full traversal,
and 75-100 KB as the normal plausible band unless a reviewer grants an explicit size waiver.
For file-retained hard-compound smoke execution, a full traversal that is still under that band
must continue expanding burden-local Layer B operations, or else retract to an honest HOLD/PARTIAL
with coverage_complete=false. Do not attempt to satisfy the mass Andon with recaps, repeated MRP
labels, citation stacks, or filler; spend the mass on the owner-bearing submoves and their
Land/R(H,Delta)/MRP consequences.
If the answer cannot visibly pay that reconstructibility cost, do not claim coverage_complete=true,
"all input burdens landed", or full closure. Instead stop after the currently released burden
with Route: HOLD or Route: RECURSE, terminal accounting for held downstream burdens, and no final
restorative closure.

HARD-FULL PRE-CLOSURE GATE:
Before writing Closure/Reconstruction Witness with coverage_complete=true in any 4+ burden
hard-compound case, run this visible release check: each released burden has a literal
`Layer B - Governed Operation Body` (or `Layer B — Governed Operation Body`) section; each
non-atomic burden has at least three owner-bearing submoves; each submove body does more than
name the operator and contains enough case-shaped Target, Operation, Result, and
Contribution-to-Land(Bn) content to show the owner actually operated; every Land(Bn) is followed
by inter-burden [Mid-Reread Pressure]; and the closure witness contains a parseable T_lang line
exactly as `T_lang: Ψᴺ ⇢ Ψᴵ: partial coupling attempt / language-mediated boundary; no guaranteed
uptake` or ASCII `T_lang: PsiN -> PsiI: partial coupling attempt / language-mediated boundary;
no guaranteed uptake`. Never write Ψᴮ, PsiB, Ψᵁ, PsiU, or topic/interlocutor substitutes in that
line. If any item fails, do not close; continue the next Layer B operation or route HOLD/PARTIAL
with coverage_complete=false.
MRP Target is mandatory and must name the burden token explicitly: `Target: B1 / ...`,
`Target: B2 / ...`, etc. A target that only says "after Land(B2)" in the reread line is not
enough. MRP pressure slots follow the same owner-token rule: entailment-pressure should normally begin
with M8, M1-P, M1, or `pressure class: entailment-pressure`; hidden-framework-recoil should begin
with FPD or `pressure class: hidden-framework-recoil`; reorientation-reminder should begin with
P1, P7, or `pressure class: reorientation`. Do not begin a slot with a phrase such as
"consequence trace", "authority-order repair", or "source-status discipline".
For release-smoke/file-retained execution, the runtime may not self-grant a size waiver. If a
Smoke-6-shaped full traversal remains below the serious Andon band (roughly 60 KB) or remains near
old compact-output size while claiming 5+ fully landed burdens, repeated MRP, graph accounting,
closure, and restoration, it must not print coverage_complete=true; it must expand the local
Layer B operations or route HOLD/PARTIAL.
This is a hard gate, not advice: below roughly 60 KB, a 5+ burden full hard-compound answer must
write `𝒞(Ψᴺ): coverage_complete=false; HOLD/PARTIAL because execution mass is not yet plausible
for the claimed topology`, or continue expanding before closure. Between roughly 60 KB and the
calibrated 75 KB floor, it still requires explicit adjudicator waiver; the runtime itself may
only close when the visible topology and mass both satisfy the gate. Because byte estimates are
coarse and hard-smoke capture can vary by a small margin, a Smoke-6-shaped full traversal should
target a visible safety margin above the floor (roughly 80 KB or more) before coverage_complete=true.
Spend that margin on reconstructible burden-local owner work, MRP resultant accounting, graph /
field_witness deltas, and closure witness detail; never spend it on recaps or filler.
Closure order is fixed. If a final MRP block emits Route: STOP, no further Layer B work,
burden-local completion body, supplemental expansion, or submove block may appear after it. If
more burden-local work is needed, render it before the final Land(Bn) and final stable MRP STOP,
or route RECURSE/HOLD instead of STOP. When STOP is licensed, render Closure/Reconstruction
Witness immediately after the final MRP record and before any Restorative Response or Closing
Formulation. Never write Restorative Response or Closing Formulation before the closure witness
in a hard/full closure.

Parseable hard-closure witness template:
Closure/Reconstruction Witness
Initial burden set: [¹B, ²B, ...]      # parser alias allowed in machine fields: [B1, B2, ...]
Burden dependency graph: ¹B (root) → ²B, ...
Terminal states:
¹B: landed / <owner-or-pressure> / <detail>
MRP resultants:
MRP(¹B): type=<held_burden_activation|generated_burden_instantiation|no_new_resultant|loopbreak|hold_partial>; finding=<stable|genuine-dependent|partial-real|hidden-framework-recoil|doubt-churn|reorientation>; graph=<delta-or-none>; route=<STOP|HOLD|RECURSE|LoopBreak(∇×T)>
∇·B: neutral / <target-explicit reason>     # or non-neutral / <held burden>
∇×κ: null / <reason>                        # or resolved / <reason>, non-null / <loop target>
𝒞(Ψᴺ): coverage_complete=<true|false>; <closure/HOLD/RECURSE reason>
T_lang: Ψᴺ ⇢ Ψᴵ: partial coupling attempt / language-mediated boundary; no guaranteed uptake
Do not write substitute fields such as a generic divergence-result field, a generic curl-result field, remaining kappa, a standalone
coverage_complete=true, or a prose-only closure license.

BRANDOLINI DEFAULT:
Even non-hard-compound objections usually require more output than input: surface brevity often
hides burden, premise, criterion, and restoration work. Default responses to refute, respond,
diagnose, shubhah, worldview, moral protest, hiddenness, authority-order, or source-status inputs
should render visible burden work, not terse answerlets. Only narrow factual clarifications,
glossary-style requests, or explicitly requested short replies may stay small.

Every plain `/daee-epistemics` runtime output begins with this noetic-field execution banner
before Layer A. The first visible surface must visibly signal governed execution; do not reduce
success to a bare `field:` line, and do not place prose, headings, apologies, Markdown fences,
clarifying questions, or banner summaries before it. Do not wrap the banner in a code block.
Clarifying or missing-input replies are still runtime outputs and must begin with the banner. The
banner is generated from the same classification state used by Layer A. Print exactly one value
for each field; never print the choice list, combine values with `|`, or invent a local synonym:

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

Use only these banner values. All inputs are noetic fields; prompt brevity does not imply
simple execution. `user task` tracks the requested operation; `/daee-epistemics refute:` renders
`user task: REFUTE` even when no source/citation request is present. `external source request`
tracks explicit or implicit demand for citations, textual proof, isnad/authentication, or
external grounding; do not mark it `IMPLICIT` merely because a worldview or authority frame is
live. If more than one field type is active, choose `MIXED NOETIC FIELD` as the single field
value. A local claim governed by a named theological/worldview authority frame while the answer
actively contrasts or restores through an Islamic restoration frame is `MIXED NOETIC FIELD`, not
`LOCAL CLAIM`.
`authority frame` is LIVE when the input contains or implies a criterion for authority,
proof, legitimacy, moral standing, public admissibility, governance, coercion, or epistemic
right. Do not use SIMPLE, COMPACT, CANONICAL, HARD, or SOURCE-ORDER as banner categories or
depth licenses. `state` is the opening governance state, not a prediction that the answer may
finish later: RECURSE means live burdens remain and the output must continue; PARTIAL means the
output is stopping while live burdens remain unresolved, compressed, or unrendered; COMPLETE is
allowed at the opening banner only for a bounded case whose live burden set is already
dischargeable in one current pass. Named-worldview, mixed noetic field, source-authentication,
or authority-frame cases with live kappa / held dependencies normally begin with RECURSE.
Closure audit must match the banner state.

If the user asks whether a report, text, narration, citation, attribution, or transmission claim
is reliable but supplies no actual text/reference, classify the field as SOURCE-AUTHENTICATION,
`user task: SOURCE-AUTHENTICATION`, `external source request: IMPLICIT`, authority frame as
LIVE, and state as PARTIAL; then ask for the missing material after the banner. Missing material
is not a license to omit the banner.

Default multi-burden execution uses this repeated burden-cycle shape:
- Layer A - compact DSL/IR header (read status, confidence, claim_level,
  pattern_profile, reason-category, `Concealment mode:`, deformation, DO-orient, live noetic burden,
  current bounded operator, held, source-status/noetic-frame, gate/release decision with
  pre-release `∇ route: ...` when route ordering selects the burden; when more than one
  live/held burden or dependency route is present, the `∇ route:` clause is mandatory and explains
  highest dependency-reduction yield over held alternatives, decisive missing differentiator when
  required. Named-worldview, imported-framework, pseudo-neutral-tribunal, source-worldview, or
  identity-stabilized cases must show `Concealment mode:` as operative covering, e.g.
  `surface-open / framework-concealed` or `mode-? / framework-concealed`; do not omit it and
  do not write `concealment: None detected`. Trinitarian person/nature grammar, later
  doctrinal apparatus, cross-text doctrine import, imported model-language, and doctrine-preserving
  harmonization count as framework/source-worldview concealment pressure whenever they govern a
  local text as if they were neutral grammar.)
- Layer B - bounded governed response (Hidden Premises, local Core Formulation,
  Bounded Response / operative submoves, and TTP/operator trace when a named operator
  does runtime work; may contain multiple operative submoves when they all serve the
  same live noetic burden; the released burden must be burden-complete before R,
  with materially necessary sub-burdens receiving matched TTP/operator treatment)
- State/noetic re-read - compact. The visible state/noetic reread surface is the
  `[Mid-Reread Pressure]` activation record. It records `Land(Bn)` / `Land(ⁿB)`, remaining
  input-anchored burdens, held routes rechecked, target-explicit `∇·T` / `∇×T`,
  pressure activations, LoopBreak status, next live burden, route, and release status in prose.
  Do not print a standalone `State/noetic re-read`, `Field diagnostics:`, `LoopBreak:`, or
  route-bearing `R(H,Delta):` after `Land(Bn)` unless `[Mid-Reread Pressure]` is the first visible
  reread block after that landing gate. Hard/multi-burden default output may not render a bare `R(H,Delta)` continuation
  line: it must include literal `Field diagnostics:` and `LoopBreak:` lines adjacent to the reread.
- MRP-visible reread gate - in default routed output, render a compact
  `[Mid-Reread Pressure]` block before the final route decision. The block must name Target,
  Reread, Landed delta, Pressure activations, `∇·T`, `∇×T`, Route-gradient, Finding,
  MRP route result type, MRP resultant, Graph delta, Pre-emption basis, Route, and Boundary.
  The MRP block is invalid if the literal `Route-gradient:`, `MRP route result type:`, or
  `MRP resultant:` lines are missing. `Field diagnostics:`, `LoopBreak:`, a bare graph edge,
  or ordinary route prose may appear only as adjacent summaries; they never substitute for those
  required MRP fields. Before final closure, self-check every MRP block and revise any block
  that lacks these exact labels.
  A plain `State/noetic re-read`, `LoopBreak:`,
  `R(H,Delta)`, graph edge, or owner/TTP trace is not MRP evidence unless it shows the pressure
  slot and route consequence. Do not omit the block in any routed burden-cycle.
- MRP trigger expansion - in default output, `T` includes current burden pressure, `kappa/H`,
  held dependencies, register pressure, and downstream burden pressure. Therefore any state
  reread that names `∇×κ`, `∇×B`, `∇×H`, remaining burden, still live pressure, release next,
  HOLD, PARTIAL, LoopBreak, blocked proof-stacking, hidden-framework recoil, doubt-churn, or a
  pre-voiced/downstream defense has invoked MRP. Do not route from Land(Bn) to the next burden,
  HOLD/PARTIAL, LoopBreak, or closure until `[Mid-Reread Pressure]` has recorded the pressure
  slots and route.
- If R(H,Delta) names a remaining input-anchored burden and no gate blocks it, continue
  with the next Burden. Do not emit Restorative Response or Closing Formulation yet.
- Named-worldview / source-authentication / mixed-field closure witness - before any final
  Restorative Response or Closing Formulation in these field classes, visibly render literal
  `Closure/Reconstruction Witness` and account for
  candidate/held N frames, selected primary N, live registers, active or cleared owner/TTP child
  modes, Delta-nB, Delta-kappa, target-explicit `∇·` / `∇×` results, literal `Burden dependency
  graph:` with compact edges such as `B1 → B2, B3` or `B1 ∥ B2 → B3`, and remaining kappa / H
  status. If any live dependency remains unresolved, unrendered, or merely identified, write
  PARTIAL or continue under RECURSE.
  The witness must include parseable `Initial burden set: [B1, B2, ...]`, `Terminal states:`
  with one line per burden using `landed`, `discharged-as-derivative`, `held-with-reason`,
  `carried-PARTIAL`, `carried-RECURSE`, or `cleared`, root nodes marked exactly `(root)` in the
  graph with no gloss inside those parentheses (`¹B (root) → ²B`, not `¹B (root authority...)`),
  plus `∇·B:`, `∇×κ:`, `𝒞(Ψᴺ):`, and `T_lang: Ψᴺ ⇢ Ψᴵ:` before final response text.
- Final hard-case closure witness - in hard compound/source-request cases, the last
  state/noetic re-read before any Restorative Response or Closing Formulation must visibly
  include literal `Closure/Reconstruction Witness` and account for FPD, M1/M1-P, M8, M9, P1/P7,
  and source functions as done, cleared, held, or PARTIAL, then include compact `𝒞(Ψᴺ)`
  closure-field licensing and `T_lang: Ψᴺ ⇢ Ψᴵ` coupling-boundary statement. Do not rename the
  block `Closure audit`.
  Each terminal line must be parseable as `B1: landed / <owner-or-pressure> / <detail>`.
  Divergence/curl lines must be target-explicit: `∇·B: neutral / <reason>` or
  `∇·B: non-neutral / <held burden>`, and `∇×κ: null / <reason>`,
  `∇×κ: resolved / <reason>`, or `∇×κ: non-null / <loop target>`.
  `𝒞(Ψᴺ):` includes `coverage_complete=<true|false>; <closure/HOLD/RECURSE reason>`.
  `T_lang: Ψᴺ ⇢ Ψᴵ:` includes `partial coupling attempt / language-mediated boundary; no guaranteed uptake`.
  The right side is always exactly `Ψᴵ`; never substitute local variants such as `Ψᴰ`, `Ψᴮ`,
  topic letters, or interlocutor labels.
  T_lang invariant: never write uptake/interlocutor substitutes such as `PsiU`, `Psi^U`, or
  a local uptake-letter target in the closure witness; use the exact invariant target named
  in the preceding `T_lang:` template.
  If any live item is missing, do not close; write literal PARTIAL and name the missing
  burden/TTP/source function.
- Restorative Response - required once after the final state/noetic re-read
- Closing Formulation - required once at the end after final Restorative Response

Hard compound source-request trigger floor:
When an input combines divine-predicate accusation, worship-worthiness veto, accountability
compression, guidance/hiddenness demand, punishment/mercy pressure, and an explicit
source-worldview request, FPD, M1/M1-P, M8, M9, P1/P7, source-worldview, accountability,
guidance, and mercy/justice owners are live unless Layer A explicitly clears one by name.
Missing any live floor item means PARTIAL, not polished closure.

Short named-worldview hard-field gate:
Noetic-structure hardness is not proportional to prompt length. A short input that names or
implies a worldview, ideology, authority-order, epistemic regime, religious objection, or
civilization-level criterion can instantiate a hard compound/source-request field even when the
user does not enumerate every burden or ask for sources. Examples include "refute secularism",
"respond to atheism", "answer liberalism", "dismantle naturalism", and "deal with this moral
objection". Treat the named structure itself as source-status/noetic-frame material when it
carries ontology, epistemology, authority order, moral tribunal, anthropology, proof standard,
or public-reason criterion. Prompt brevity, generic wording, or absence of "bring sources" is
not a STOP reason. Expand from the noetic structure, then execute, clear, hold, or mark PARTIAL
for every structurally live owner family; do not print the whole catalogue and do not dump every
topic merely because the name is broad.

General noetic-selection / register-control reread gate:
do not assume the selected N frame is known at design time. For any input D0, scan the
noetic-structure selection space, select or hold candidate N frames, and treat heart, xi,
Omega, sigma, mu, kappa, and H as live whenever the input supports them. After each `Land(B)`,
`R(H,Delta)` must compute the local landed burden-state change (Delta-nB) and the
dependency-radius delta (Delta-kappa). If kappa or H still contains unresolved dependencies, the
response must release the next burden, HOLD, PARTIAL, or explicitly clear the dependency. It may
not STOP or mark COMPLETE while downstream dependencies remain only named, compressed, or
unrendered.

For outputs that close, the closure audit must visibly account for the generalized algebraic
control state in prose: candidate/held N frames, selected primary N, live registers, active or
cleared owner/TTP child modes, Delta-nB, Delta-kappa, target-explicit `∇·` / `∇×` results,
compact burden dependency graph, `𝒞(Ψᴺ)` positive closure-field condition, `T_lang: Ψᴺ ⇢ Ψᴵ`
coupling boundary, and remaining kappa / H status. The audit must remain case-shaped;
dependencies appear only where structurally live. Do not mark COMPLETE unless the audit shows
each live dependency executed, cleared, held with reason, or no longer structurally live.

Hard file-retained depth floor:
Compact means no padding and no route dump; it does not mean short. In file-retained hard
compound/source-request execution, output length follows live burden and source operation.
A complete-looking hard answer below 30k characters is invalid unless it visibly says PARTIAL
and names the missing burden/TTP/source function; 30k-35k remains suspect and must pass the
owner/source/closure matrix. Do not satisfy the floor with citation stacks or recaps; expand
the local Layer B operations that actually land the burdens. A 5+ burden MRP-heavy full traversal
that stays near old compact-output size must prove it is not skeletal by rendering explicit
Layer B operation bodies and owner-bearing submoves for released burdens; otherwise continue
execution or route HOLD/PARTIAL. If claiming full traversal in file-retained smoke mode, do not
use one-sentence submove fields; expand each owner-bearing submove enough that its target,
operation, result, and contribution are reconstructible without a reader having to infer the
operator's work from the label.
By Brandolini default, ordinary refute/respond/diagnose, worldview, moral-protest, hiddenness,
authority-order, source-status, and shubhah inputs should still render substantial governed
unpacking. Surface brevity is not evidence of low noetic load. Only narrow factual
clarifications, glossary requests, or explicit short-answer requests may stay small.

Hard/multi-burden default output:
ComplexB -> {{¹B₁...¹Bₙ}} -> Land(¹B) -> [Mid-Reread Pressure] -> R(H,Delta).
AtomicB -> ¹B₁ -> Land(¹B) -> [Mid-Reread Pressure] -> R(H,Delta).
Compact default may not collapse a complex B into one generic operation block. Render materially
necessary submoves as case-specific target -> operation -> result units before burden landing.
The burden grammar is part of the hard-output deliverable, not commentary about the deliverable.
Hard/multi-burden execution must not proceed from root-summary awareness alone. Before
rendering a complex ⁿBᵢ, load/read the owner body or compiled bundle section containing
the active TTP's operation floor, unless that exact section is already present in active
context. Package availability, map presence, or bundle co-location is not access. TTP label
recognition is not owner-body execution; matched module label is not owner floor loaded.
When the packaged/generated `skill/SKILL.md` is the supplied runtime surface, its copied runtime
references and compiled omnibus sections count as readable runtime context once the compiled map
or routing table points to that section. Do not mark `PARTIAL / OWNER-BODY-NOT-LOADED` merely
because a separate atomized repo file was not opened. Still do not activate sibling bundle
sections unless routing selects their original module ID.
If the needed owner body or compiled bundle section is unavailable, do not compress into
generic prose; mark PARTIAL / OWNER-BODY-NOT-LOADED and name the missing owner/path. This
marker is a required hard-output failure marker and is permitted in default/hard output.

Owner-loadform map for common hard-output owners:
- recursive state re-read -> references/runtime-dispatch-gate.md (recursive-state-transitions)
- diagnostic render contract and output release/hold -> references/runtime-output-governance.md
  (diagnostic-render-contract, output-release)
- reason/revelation proof-status triage -> references/omnibus/OMNIBUS-procedures.md
  (P3-reason-revelation-tension) plus references/omnibus/OMNIBUS-specialty-diagnostics.md
  (proof-method-audit) when proof-family status governs
- predication-mode analysis -> references/omnibus/OMNIBUS-tactics.md (M9-predication-mode)
- readiness/deformation triage -> references/runtime-diagnostic-core.md (M5-deformation-triage)
- reason-category prerequisite or foreign-premise split -> references/runtime-phase2-passes.md
  (reason-disambiguation, foreign-premise-detection)
- imported tribunal, moral-framework, or case-family routing ->
  references/omnibus/OMNIBUS-do-families.md (philosophical-usurpation, do-core) plus
  references/omnibus/OMNIBUS-profiles.md when a noetic profile must be confirmed
- self-refutation, performative veto, reductio, orphaned intuition, or predication tactics ->
  references/omnibus/OMNIBUS-tactics.md
  (M1-self-refutation, M1P-performative-self-refutation, M8-reductio,
  M3-orphaned-intuition, M9-predication-mode)
- restorative, stop/hold, or maieutic follow-through -> references/omnibus/OMNIBUS-procedures.md
  (P1-fitrah-restoration, P7-restoration-stops, P4-maieutic)
- sign-direction or reason-reconstitution techniques ->
  references/omnibus/OMNIBUS-techniques.md
  (V2-reconstituting-reason, V5-directing-attention-signs)

Render ComplexB in this order:
Burden N: <name>
Layer B - Governed Operation Body
  Operative Submove ¹B₁:
    Target: <exact premise / criterion / predicate / warrant>
    Operation: <case-shaped owner action; not a one-line stub in full traversal>
    Result: <changed claim-state>
    Contribution-to-Land(Bn): <how this submove helps land the burden>
  Operative Submove ¹B₂:
    Target: <exact premise / criterion / predicate / warrant>
    Operation: <case-shaped owner action; not a one-line stub in full traversal>
    Result: <changed claim-state>
    Contribution-to-Land(Bn): <how this submove helps land the burden>
  [continue until all materially necessary s are rendered]
  Land(¹B): <cumulative state delta from ¹B₁...¹Bₙ>
  [Mid-Reread Pressure]
    Target: Bn / <landed burden name>
    Reread: R(H,Delta)
    Landed delta: Delta-1B / Delta-kappa from Land(¹B)
    Pressure activations:
    - freeze-landed-move: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - dependency-tug: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - hidden-framework-recoil: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - entailment-pressure: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - doubt-churn-guard: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    - reorientation-reminder: <existing owner/TTP or pressure class> — <release/hold/clear effect>
    ∇·T: <neutral/settled/bounded/non-neutral plus license>
    ∇×T: <null/resolved/held/non-null plus license>
    Finding: <stable/genuine-dependent/partial-real/hidden-framework-recoil/doubt-churn/reorientation>
    MRP resultant: <finding -> route/graph/hold consequence>
    Graph delta: <none or Bn -> Bn+1>
    Pre-emption basis: <none/graph-bound/commitment-bound/framework-bound>
    Route: <STOP/HOLD/RECURSE/LoopBreak(∇×T)>
    Boundary: T_lang does not imply guaranteed uptake
  R(H,Delta): <held/released/next-live-burden decision>
If a diagnostic pass only partially lands because a route is held, still render
`Land(Bn): PARTIAL / <what was identified>` before MRP. A bare diagnostic sketch without a Land
or partial-Land line is not reconstructible.
MRP compact-block fields are parseable record fields. The Finding, Pre-emption basis, and Route
lines must contain one exact value from the template with no extra prose or punctuation. Boundary
must begin `T_lang does not imply guaranteed uptake`; append any PARTIAL / OWNER-BODY-NOT-LOADED
text after a semicolon. Each pressure activation must begin with an owner/TTP id,
`pressure class: <name>`, or `coverage gap: <missing owner>`, followed by the effect. Graph delta
is `none` for STOP/LoopBreak. RECURSE must include a graph edge. HOLD may include a held graph
edge only when Terminal states marks the downstream node held-with-reason or carried-PARTIAL.
The six pressure activation labels are fixed and must not be replaced by generic labels or
emitted without the literal leading dash. Slot values must begin with an owner/TTP id,
`pressure class: ...`, or `coverage gap: ...`; never with only `B1`, `none`, `cleared`, or prose.
MRP resultant must state the finding-to-route/graph/HOLD consequence in one line. LoopBreak is
never a graph node or graph edge; render Graph delta: none and Route: LoopBreak(∇×T).
Reconstructibility/node-lineage requirement: the visible output must let an evaluator map input ->
burden nodes -> submove nodes -> Land(Bn) -> R(H,Delta) -> MRP resultant -> graph/field_witness
delta/no-edge -> route -> closure/restoration. If a node in that chain is absent, route HOLD
or PARTIAL instead of claiming closure.
Post-burden continuation gate: after every R(H,Delta), if state re-read names a remaining
input-anchored burden and no hold, register, semantic, thin-basis, source-use, or limit gate
blocks it, continue with the next Burden. Restorative Response and Closing Formulation are
final-only for the current answer; if limits prevent the next burden, emit PARTIAL with the
next live burden instead of closing.
If MRP names a live dependency such as proportionality, hiddenness/coercive-guidance,
source-worldview, moral-grounding, or owner-body pressure, STOP/COMPLETE is forbidden until
that dependency is released and landed, merged into a named landed burden with same-function
proof, or held/PARTIALed with the exact gate. If a later Layer B burden appears, the prior MRP
route must be RECURSE/HOLD, not STOP. Owner-load failure uses Route: HOLD and Boundary: PARTIAL /
OWNER-BODY-NOT-LOADED: <missing owner/path>; after that boundary, do not emit closure witness,
Restorative Response, Closing Formulation, or broad "refuted" language.
Input-anchored means any explicit claim, supporting premise, contrast, public/private partition,
source-status rule, translation demand, or moral/epistemic criterion already present in the
user's input, not only a separate requested question.
If R(H,Delta) enumerates remaining input-anchored burdens, "only if requested" is not a valid
STOP reason unless a named hold gate blocks release. "Requires its own bounded pass" means
continue or mark PARTIAL.
AtomicB may use one submove only when it has one target, one operation, and no distinct
internal predicates, criteria, source-status forks, or release gates.
In default hard/multi-burden output, `[Mid-Reread Pressure]` is the mandatory route gate between
Land(Bn) and any Field diagnostics, LoopBreak, route-bearing R(H,Delta), next burden,
HOLD/PARTIAL, or closure. If it is absent, R(H,Delta) may not release the next burden,
HOLD/PARTIAL, LoopBreak, or close.

Miniature structure only:
Burden 1: imported moral tribunal
  ¹B₁ - expose the tribunal
    Target: hidden moral judge | Operation: expose | Result: criterion is no longer neutral
  ¹B₂ - test the criterion against its own grounds
    Target: self-authorizing standard | Operation: test | Result: standard cannot condemn while self-grounded
  Land(B1): the imported tribunal no longer governs as unquestioned judge
  [Mid-Reread Pressure]: freeze Land(B1); activate existing owner/TTP pressure slots;
  record divergence/curl, finding, graph/held/no-edge consequence, pre-emption basis, and route
  R(H,Delta): accountability and guidance-demand burdens remain held/live; release next B only from the MRP result
Burden 2: accountability compression
  ²B₁ - distinguish bare non-exposure from culpable rejection
  ²B₂ - hold individual fate while correcting the general rule
  Land(B2): "simple non-belief" no longer names the accountability structure
  [Mid-Reread Pressure]: activate dependency-tug and hiddenness/coercive-guidance pressure owners before route
  R(H,Delta): guidance-demand burden remains live; release next B only from the MRP result
This hard-output shape is not raw IR or a route ledger when each submove serves the same B.

If internal state re-read licenses another bounded pass, continue with the next burden-cycle.
If internal state re-read licenses closure or hold, render the release status in prose rather
than as a literal STOP / HOLD / RECURSE label. If the state is incomplete or limits block
required traversal, the visible failure marker is literal PARTIAL with the missing live
burden/TTP/source function named; do not hide PARTIAL as ordinary prose.
No NewB is licensed by a headline-only answer, skipped internal sub-burdens, generic
prose substitute, or broad-conclusion jump.

Current bounded operator names one live noetic burden/function, not a route chain, module list,
route itinerary, or single operative submove. Valid examples: imported moral tribunal /
worship-worthiness criterion burden, accountability or hujjah burden, hiddenness or
coercive-guidance burden, punishment/proportionality with mercy-justice source architecture,
foundational epistemology warrant burden, source-status / identity-stabilization burden.
Invalid examples: FPD -> M1 -> DO-8 -> M8 -> restoration; M1, M8, DO-8, restoration; full
route itinerary; making every source, warning, recap, practical wording, or individual TTP
submove its own burden. Distinct first-order, second-order, or higher-order noetic functions
must not be collapsed merely because they appear in the same prompt or bear on one broader
objection.

Operative submoves are not burden-cycles. A live noetic burden may contain multiple operative
submoves, each preserving target -> operation -> result, before the burden lands and state is
re-read. Do not label FPD, M1, DO-8, M8, identity clarification, source maps, warnings, or
restoration fragments as Pass 1 / Pass 2 / Pass 3 unless a prior burden landed and state
re-read licensed a genuinely new input-anchored noetic aspect. But if R(H,Delta) shows a
different noetic order/function remains live--for example imported tribunal, accountability
or hujjah compression, hiddenness or coercive-guidance demand, punishment/proportionality with
mercy-justice source architecture, or criterion-bearing source-worldview--release the next
burden rather than compressing it into a generic paragraph.

Diagnostic reduction precedes route selection: core axes -> mandatory Phase 2 passes ->
triggered overlays / specialty markers -> typed IR -> gate checks -> routing precedence ->
selected current live burden.

This runtime is a diagnostic compiler, not a deterministic argument bank. Every substantive
case reduces into validated IR before operator activation. TTPs enter only through owner-backed
entry criteria, exit through target -> operation -> result, and converge through state re-read.
Do not select a stored argument from a topic cue.

Each recursive depth increase requires prior burden landing, state re-read, a next input-anchored
live burden, and a new bounded operator. The next live burden must be a genuinely new noetic
function/order, not merely the next TTP or topical component needed to clear the same burden.
Hiddenness, punishment/accountability, source-status, source-worldview, and identity-stabilization
can be operative submoves under one burden only when R(H,Delta) proves same function, same
source-frame, and same claim-cluster. When they remain distinct first-order, second-order, or
higher-order pressures, they require distinct burden-cycles or an explicit PARTIAL. Multi-burden
does not mean topic tour; compactness means no padding, no burden loss.
Layer A may name held routes for auditability; Layer B may release only the current live burden
and its justified operative submoves.

Restoration synthesis and pastoral note wait until the active burden lands and state re-read
licenses closure, hold, partial traversal, or the next input-anchored burden.

Layer A must not show: the full internal diagnostic schema, full routing-state block,
source-tracking fields, module-resolution fields, load ledger, route itinerary, NS codes
in field form (unless the NS code itself is the governing issue), or broad concealment /
deformation verdict dumps without anchoring signal.

Single-cycle Layer A/B cosplay: printing Layer A + Layer B + state re-read once, then stopping
without proving no eligible input-anchored live burden remains. This is a recursion failure.

Compact state re-read must enumerate remaining input-anchored burdens, not merely name the
governance decision.

An essay organized by topic is not governed traversal.

Minimum visible transition spine is required for multi-burden default output.

If no transition marker appears while moving between live burdens, the skill has not been
executed; it has been summarized.

Rewrite before emitting.

# Default Output Surface Invariant

For plain `/daee-epistemics`, internal governance is mandatory and default visibly prints
a noetic-field execution banner before the compact DSL/IR header. The first visible surface must
signal governed execution with `NOETIC FIELD EXECUTION` and must not collapse to a bare `field:`
line or `source request` legacy label. Compact Layer A (read status, confidence, claim_level,
pattern_profile, reason-category, `Concealment mode:`, deformation, DO-orient, live noetic burden,
current bounded operator, held, source-status/noetic-frame, gate/release decision, decisive
missing differentiator when required) is the visible default diagnostic surface. Full
Diagnostic IR, full Case State, full Source Basis ledger, matched_modules, and route ledger
remain internal; compact TTP/operator trace appears when a named runtime operator performs
work under the render contract.

Default visible frame:

```text
╔══════════════════════════════════════════════════════╗
║ daee-epistemics — NOETIC FIELD EXECUTION             ║
║ field: <LOCAL CLAIM | NAMED WORLDVIEW | SOURCE-AUTHENTICATION | MIXED NOETIC FIELD>
║ user task: <RESPOND | REFUTE | DIAGNOSE | EXPLAIN | SOURCE-AUTHENTICATION | OTHER>
║ external source request: <NONE EXPLICIT | IMPLICIT | EXPLICIT>
║ authority frame: <NONE DETECTED | LIVE>
║ state: <RECURSE | PARTIAL | COMPLETE>
╚══════════════════════════════════════════════════════╝

Layer A — Compact DSL/IR header
- read status:
- confidence:
- claim_level:
- pattern_profile:
- reason-category:
- Concealment mode:
- deformation:
- DO-orient:
- live noetic burden:
- current bounded operator:
- held:
- source-status/noetic-frame:
- decisive missing differentiator: [only when required]
- gate/release decision:

Layer B — bounded governed response
- Hidden Premises
- Burden / Operation N
  - Core Formulation
  - Bounded Response / operative submoves
- TTP/operator trace when a named operator does runtime work

State/noetic re-read

Closure/Reconstruction Witness (when closing hard, multi-burden, register-active, or mixed-field cases)

Next Burden (only while R licenses RECURSE)

Final Restorative Response
Final Closing Formulation
```

Before any answer is emitted:
- Diagnostic IR is formed internally.
- Case State is maintained internally.
- Source Basis is tracked internally.
- `matched_modules` and route plans remain internal.
- STOP / HOLD / RECURSE / PARTIAL is decided internally.

Default output must not print:
- Full Diagnostic IR block or `## Diagnostic IR` header
- Full Case State block
- Full Source Basis block or source-basis ledger
- `matched_modules`
- route plan or route ledger
- load ledger
- source ledger
- literal `Recursion decision:`
- `next_eligible_pass`
- setup narration such as "I now have enough..." or "Let me compose..."
- file loading, searching, setup, readiness, or composition narration such as
  "Let me check..." or "I will produce governed prose..."
- scholar/source/citation parade, school-label context, genealogy, or external philosopher /
  theologian support unless requested or validated source-comparison IR requires it

If the drafted default answer contains those surfaces, rewrite it before output.

TTP/operator trace is not external citation support. If a named runtime operator such as
FPD, M1, M1-P, M8 reductio, M9 predication repair, tamanu, criterion-reversal,
tribunal-detection, P1/P7 restoration or hold discipline, transmission/testimony, predication,
grief/register, family-local proof-method, or authority-order repair performs the work, the
governed operation or bounded response names it and executes target -> operation -> result.
Do not substitute a source citation for TTP invocation, and do not substitute TTP invocation
for Qurʾān/Sunnah/Salaf citation when revealed textual support is actually used. When revealed
text is quoted for operative diagnostic or restorative work, present it cleanly as quotation,
translation, and source/reference where useful, then state the function it performs; do not
collapse central revealed evidence into a long prose sentence or use it as citation padding.
Within a released live burden, TTP/operator routing is burden-complete: materially necessary
sub-burdens are addressed by matched operators before state/noetic re-read, and NewB is not
licensed by a headline-only answer, skipped internal sub-burdens, generic prose substitute,
or broad-conclusion jump. A self-authorizing criterion, self-grounding moral/epistemic court,
source-worldview transfer, predicate/category transfer, testimony standard, grief/register
gate, or family-local proof-method pressure requires its matched owner action when structurally
live; generic "test", "clarify", "warn", or "address" language is not enough unless the
target, operation, and claim-state change are visible.
This activation standard is catalogue-wide. For each released burden-cycle, check the live
noetic structure against the relevant TTP/owner families: E1-E4, F1-F3, husn-al-nazar
arguments, inductive-fitri method, M1-M9, M1-P, R1-R3, symmetric-taqlid-check, V1-V12,
heuristics, P1-P7, transmission/testimony owners, predication owners, grief/register owners,
source-worldview owners, and family-local proof-method owners. Do not print a route list.
Execute every structurally live owner as a local Layer B submove with target, operation,
result/state change, and contribution to Land(B), or explicitly clear/hold/PARTIAL it when
the trigger is absent, blocked, or underdetermined.

Full diagnostic blocks belong to `/daee-epistemics:dsl` or internal/development audit,
not default mode. Compact Layer A fields are mandatory in default mode.

# Compiled Runtime Routing Addendum

Canonical atomized source remains under `atomics/skill/`. This generated runtime is the low-call Claude package root built from that source.

## Compiled Runtime Path Resolution

This compiled runtime package does not contain every atomized source file as a standalone runtime file.

When this SKILL.md or a routing table names an atomized source path such as:

`references/tactics/M9-predication-mode.md`

treat that path as a canonical source identity, not as a literal runtime file-load target.

Resolve the original module ID or source path through:

`compiled-module-map.json`

then load the containing runtime bundle and section, for example:

`references/omnibus/OMNIBUS-tactics.md` -> section `MODULE_ID: M9-predication-mode`.

Do not attempt to load missing atomized files from the compiled package.

When this generated SKILL.md is the supplied runtime surface, its copied runtime references and
compiled omnibus bundle sections are readable runtime context. A selected module's bundle
section counts as loaded when the compiled map or routing table points to that `MODULE_ID` and
the runner has the generated skill surface. Do not return OWNER-BODY-NOT-LOADED merely because
the separate atomized source file was not opened.

Do not use omnibus filenames as `matched_modules`.

Use original module IDs in `matched_modules` and `source_basis`.

Bundle co-location means availability, not activation.

Load path for substantive cases:

1. `references/runtime-foundation.md`
2. `references/runtime-diagnostic-core.md`
3. `references/runtime-phase2-passes.md`
4. `references/runtime-dispatch-gate.md`
5. `references/runtime-output-governance.md`

Use `references/omnibus/*.md` only after V1, Phase 2, and the Diagnostic IR authorize the original source module owner.

Compiled-runtime rules:

- Treat inherited atomized/source paths in the tables below as original source module references, not literal files to chase inside this package.
- Resolve an inherited path by normalizing it to `atomics/skill/...`, finding that entry in `compiled-module-map.json`, loading the listed `bundle_path`, and using only the section whose `<!-- MODULE_ID: ... -->` matches the map entry.
- Do not load missing atomized/source paths literally. If a path cannot be resolved by `compiled-module-map.json` or by a copied runtime metadata file under `references/diagnostics/`, hold it as a runtime resolution failure.
- Bundle names never appear in `matched_modules`.
- Every `matched_modules` entry uses the original module ID from `module-catalogue.json`.
- Every module-backed `source_basis` entry cites the original module ID and the compiled bundle section that was used.
- Bundle co-location does not activate sibling sections.
- Preserve post-render gate discipline: every bounded move must retain the `STOP`, `HOLD`, `RECURSE`, or `PARTIAL` decision model from the diagnostic IR and output governance.
- If a generated bundle conflicts with `atomics/skill/`, the atomized source wins and this runtime must be rebuilt.

Routing governance invariants:

- diagnosis before answer.
- IR before routing.
- routing before render.
- post-render gate.
- STOP / HOLD / RECURSE / PARTIAL.
- bundle availability is not activation.
- matched_modules use original module IDs.
- source_basis records original module or section.

The generated bundle map is `compiled-module-map.json`.

---

"""
    return frontmatter + instructions + body.rstrip() + "\n"


def build() -> int:
    root = repo_root()
    framework_status = build_framework_pipeline()
    if framework_status != 0:
        return framework_status

    errors = validate_sources(root)
    if errors:
        print("compiled-runtime build: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    compiled_root = clean_compiled_dir(root)
    source_map: dict[str, dict[str, str]] = {}
    generated_files: list[str] = []

    skill_out = compiled_root / "SKILL.md"
    skill_out.write_text(generated_skill_text(root), encoding="utf-8", newline="\n")
    generated_files.append(posix_rel(skill_out, root))

    for bundle_rel, sources in BUNDLE_SOURCES.items():
        bundle_out = compiled_root / bundle_rel
        bundle_out.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            GENERATED_WARNING.rstrip(),
            "",
            f"# {Path(bundle_rel).stem}",
            "",
            "This generated bundle is a runtime read view. Section presence does not imply active dispatch.",
        ]
        for rel_path in sources:
            doc = load_source_doc(root, rel_path)
            lines.append(build_section(doc).rstrip())
            source_map[doc.module_id] = {
                "module_id": doc.module_id,
                "module_class": doc.module_class,
                "canonical_path": doc.canonical_path,
                "source": doc.source_rel_path,
                "source_sha256": doc.sha256,
                "bundle_path": bundle_rel,
            }
        bundle_out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
        generated_files.append(posix_rel(bundle_out, root))

    runtime_metadata_copies: dict[str, str] = {}
    for rel_path in RUNTIME_METADATA_COPIES:
        source_path = source_path_for(root, rel_path)
        runtime_rel = source_rel_from_legacy(rel_path)
        metadata_out = compiled_root / runtime_rel
        metadata_out.parent.mkdir(parents=True, exist_ok=True)
        metadata_out.write_bytes(source_path.read_bytes())
        generated_files.append(posix_rel(metadata_out, root))
        runtime_metadata_copies[runtime_rel] = canonical_source_rel(rel_path)

    canonical_runtime_metadata_copies = {
        runtime_rel: source_rel
        for runtime_rel, source_rel in runtime_metadata_copies.items()
        if runtime_rel.split("/", 1)[0] not in DEV_ONLY_GENERATED_ROOTS
    }

    compiled_map = {
        "generated": True,
        "generated_warning": "GENERATED FILE. Do not edit directly. Canonical atomized source lives under atomics/skill/. Regenerate with tools/build_compiled_runtime.py.",
        "compiler_version": COMPILER_VERSION,
        "bundle_mapping_version": BUNDLE_MAPPING_VERSION,
        "runtime_metadata_copies": canonical_runtime_metadata_copies,
        "modules": dict(sorted(source_map.items())),
    }
    map_out = compiled_root / "compiled-module-map.json"
    map_out.write_text(json.dumps(compiled_map, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    generated_files.append(posix_rel(map_out, root))

    extra_inputs = {
        canonical_source_rel(rel_path): sha256_file(source_path_for(root, rel_path))
        for rel_path in EXTRA_INPUTS
    }
    manifest_out = compiled_root / "build-manifest.json"
    generated_files_with_manifest = sorted([*generated_files, posix_rel(manifest_out, root)])
    canonical_package_files = canonical_package_files_from_generated(generated_files_with_manifest)
    manifest = {
        "generated": True,
        "compiler_version": COMPILER_VERSION,
        "bundle_mapping_version": BUNDLE_MAPPING_VERSION,
        "canonical_source_root": SOURCE_ROOT_REL,
        "output_root": OUTPUT_ROOT_REL,
        "generated_files": generated_files_with_manifest,
        "canonical_package_files": canonical_package_files,
        "bundles": {
            bundle_rel: [canonical_source_rel(source_rel) for source_rel in sources]
            for bundle_rel, sources in BUNDLE_SOURCES.items()
        },
        "runtime_metadata_copies": runtime_metadata_copies,
        "sources": dict(sorted(source_map.items())),
        "extra_inputs": extra_inputs,
        "generated_warning": "GENERATED FILE. Do not edit directly. Canonical atomized source lives under atomics/skill/. Regenerate with tools/build_compiled_runtime.py.",
    }
    manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    print("compiled-runtime build: PASS")
    print(f"Output: {out_dir(root).relative_to(root).as_posix()}")
    print(f"Bundles: {len(BUNDLE_SOURCES)}")
    print(f"Compiled source sections: {len(source_map)}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
