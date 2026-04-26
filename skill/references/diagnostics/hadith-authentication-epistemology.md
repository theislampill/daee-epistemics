---
id: hadith-authentication-epistemology
module_class: diagnostic
canonical_path: skill/references/diagnostics/hadith-authentication-epistemology.md
contract_version: "0.2.3.0"
load_when:
  - ḥadīth corpus reliability or isnād criticism is live pressure
  - āḥād-vs-mutawātir epistemic-yield question active
  - grade-language rhetoric operative
routing_effects:
  - holds downstream doctrinal rebuttal until transmission burden is typed
  - prohibits RT-5 label
emits:
  - what_is_withheld_and_why
blocks:
  - downstream doctrinal release before ḥadīth burden typed
  - RT-5 inflation
companions:
  - V10-transmission-content-vetting
  - revelation-transmission
output_shapes:
  - pass-through
  - held-pending-upstream
layer_constraint: layer-b-governed
catalogue_registered: true
---

# Ḥadīth Authentication and Epistemic Yield

This file is the canonical owner for ḥadīth corpus transmission/authentication epistemology.
It exists to keep ḥadīth pressures from being blurred together with Qur'anic RT cases and to
stop downstream doctrinal rebuttal from being released before the transmission burden is typed.

This is not a full ʿulūm al-ḥadīth manual. It does not attempt to teach the whole history of
isnād criticism, every grading dispute, or every intra-madhhab debate. Its job is narrower:
distinguish the live burden, keep the routing honest, and state when provenance/authentication
must stay primary.

Runtime discipline:

- Keep `Claim-type: transmission`.
- Do not invent `RT-5`.
- Use `Case family` and `Matched modules` to surface the ḥadīth burden.
- Keep `RT marker: none` unless a separate Qur'anic RT-1..RT-4 pressure is also live.

## Standard Read

Use this compact read inside case-state or IR when the burden needs surfacing:

```text
[Ḥadīth Authentication Read]
- Burden family: <corpus skepticism | method skepticism | report-class / epistemic-yield | grade confusion | mixed>
- Pressure scope: <corpus | method | report-class | specific report | mixed>
- Live question:
- Route consequence:
- Hold / release rule:
- Prohibited move:
```

Use plain burden-family labels. Do not create a new runtime code family for them.

## Minimal-Pair Discriminator Set

| If the pressure is... | Then the family is... | Not this |
|-----------------------|-----------------------|----------|
| "Ḥadīth are late, political, unreliable, or unusable as a corpus" | `corpus skepticism` | not a specific report-class or grading question |
| "Isnād criticism, narrator grading, or jarḥ wa taʿdīl are circular, sectarian, or unhistorical" | `method skepticism` | not blanket corpus rejection and not yet a doctrine question |
| "If a report is āḥād, what certainty or doctrinal load can it bear?" | `report-class / epistemic-yield` | not global ḥadīth rejection |
| "This report is only ḥasan / not mutawātir / disputed, so the case collapses" | `grade confusion` unless the whole corpus is being attacked | not automatically corpus skepticism |
| "This ḥadīth is being used to defend or attack doctrine X" while its transmission status is still disputed | `mixed` | not a pure doctrinal objection yet |

The rule: type the ḥadīth burden before answering what the report or doctrine means.

## Burden Families

### 1. Corpus Skepticism

**Definition:** The live claim is that ḥadīth as a corpus are too late, too political, too
unreliable, or too structurally weak to be epistemically usable at all.

**Differentiator:** The attack is on the standing of the corpus, not merely on one grading
decision or one report-class.

**Routing consequence:**

- Treat the burden as `meta-epistemic` or `cross-level`, not as a first-order doctrinal dispute.
- Run V10 first so provenance, contents, and authority are not collapsed.
- If the pressure imports historical-critical method as a neutral tribunal, run
  `foreign-premise-detection.md`, then V2, before any downstream doctrinal release.
- If the case is believer-destabilization rather than external critique, pair this file with
  P5 or `mixed-case-handling.md`, but do not skip the corpus-level typing.

**Hold / release rule:** Hold all downstream doctrinal content until the live question stops
being "is the ḥadīth corpus epistemically usable at all?"

### 2. Method Skepticism

**Definition:** The live attack is on the authentication method itself: isnād evaluation,
jarḥ wa taʿdīl, narrator criticism, or historical verification norms.

**Differentiator:** The interlocutor is not yet arguing about what one report proves; they are
arguing that the method by which reliability is assessed is itself unsound, circular, or
sectarian.

**Routing consequence:**

- Keep the case at provenance/authentication level.
- Use V10 Step 1 as the primary gate: what kind of transmission mechanism is actually being
  criticized?
- If the objection imports a foreign tribunal, surface `tribunal-installation` or
  `transmission-demotion` rather than answering as if the method had already lost standing.
- Do not let the date of a later collection stand in for the date of the transmitted content.

**Hold / release rule:** Hold specific-report debate and doctrinal rebuttal until the method
question has been named as method-level rather than smuggled in as a conclusion.

### 3. Report-Class / Epistemic-Yield Questions

**Definition:** The live issue is not whether ḥadīth exist or whether the method works, but
what level of epistemic force a report-class carries, especially āḥād vs mutawātir.

**Differentiator:** The interlocutor is asking about certainty-grade, evidentiary yield, or
what kind of doctrinal or practical load a class of reports can bear.

**Routing consequence:**

- Keep the question at certainty-grade level before moving to doctrine.
- Distinguish "not mutawātir" from "epistemically worthless."
- Distinguish a question about what yields ḍarūrī certainty from a claim that anything below
  that threshold is unusable.
- Load `sound-reason-epistemology.md` only if the interlocutor is truly pressing certainty-grade
  or the structure of necessary vs inferential knowledge. Do not ambient-load it.

**Hold / release rule:** Release downstream doctrinal content only after naming whether the
dispute is about certainty, sufficiency for action, or the specific doctrinal load being claimed.

### 4. Grade Confusion

**Definition:** Grade-language is being used rhetorically rather than analytically:
`ṣaḥīḥ`, `ḥasan`, `ḍaʿīf`, `not mutawātir`, or "disputed" is being treated as if all lower
statuses collapse into one undifferentiated failure.

**Differentiator:** The pressure usually targets one report or one clip, but then tries to
generalize from grading language to corpus collapse or doctrinal collapse.

**Routing consequence:**

- First determine whether the case is about one report, one class of reports, or the corpus.
- Keep `ṣaḥīḥ`, `ḥasan`, and `ḍaʿīf` distinct; keep "not mutawātir" distinct from "worthless."
- If the report is only being used as a rhetorical destabilizer, route through the grading
  confusion first rather than jumping to doctrine.

**Hold / release rule:** Hold doctrinal use of the report until the grading term has been
typed and its actual epistemic consequence stated.

## Downstream Release Discipline

When ḥadīth-authentication pressure and downstream doctrine co-occur, sequence in this order:

1. Type the burden family: corpus, method, report-class, grade confusion, or mixed.
2. Run V10 provenance -> contents -> authority.
3. If an imported tribunal is live, run FPD/V2 before transmission content.
4. If the live question is epistemic-yield, resolve that layer before doctrine.
5. Only then release the downstream doctrinal file, prophecy file, or believer-strengthening move.

Examples:

- Global ḥadīth rejection + doctrinal objection -> corpus skepticism first, doctrine held.
- "Jarḥ wa taʿdīl is circular" + one troubling ḥadīth -> method skepticism first, specific report second.
- "This belief rests on āḥād reports" -> epistemic-yield question first, then the claimed doctrinal load.
- "This report is only ḥasan" + Muslim panic -> grade confusion first, then P5 or the matched doctrinal clarification.

## Prohibited Moves

- Do not force ḥadīth-authentication pressure into RT-1..RT-4 or invent `RT-5`.
- Do not answer a corpus-level or method-level burden by citing one doctrinally useful report.
- Do not treat the late compilation date of a collection as the origination date of the transmitted content.
- Do not collapse "not mutawātir" into "therefore unusable."
- Do not answer a specific report-class question as if the whole corpus had been rejected.
- Do not release downstream doctrinal defense before the provenance/authentication burden has been typed.

## Failure Tests

This file has not governed the response if any of the following occur:

- The reply moves to doctrine before stating whether the live ḥadīth burden is corpus, method,
  report-class, or grade confusion.
- A challenge to isnād or jarḥ wa taʿdīl is answered as if it were already a settled attack on
  the entire corpus.
- "Not mutawātir" is treated as equivalent to "epistemically worthless."
- A weak or disputed report is used to collapse the whole ḥadīth corpus without the response
  naming that leap.
- Qur'anic RT material is imported as though ḥadīth transmission and Qur'anic transmission were
  one undifferentiated architecture.

## Connection to Existing Owners

- V10 remains the structural provenance -> contents -> authority technique.
- `revelation-transmission.md` remains the RT-1..RT-4 owner for Qur'anic/scriptural text-history
  cases and believer-destabilization in that family.
- `foreign-premise-detection.md` and V2 govern imported historical-critical or rationalist
  tribunals when they are functioning upstream of the ḥadīth challenge.
- `prophecy-wahy-supremacy.md` may become live only after the transmission burden is typed, when
  the real issue is authority-order demotion rather than one report's status.
