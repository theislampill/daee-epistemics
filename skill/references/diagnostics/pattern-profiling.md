> role: diagnostic-governance
> use when: a case instantiates a recurring cross-volume family, or the live burden is about standards of knowing, ontological categories, or noetic structure rather than first-order content alone
> do not use when: a narrow single-point reply does not benefit from surfacing a reusable pattern or claim-level distinction
> output: `claim_level`, `pattern_profile`, and the routing consequence they impose on module dispatch

# Pattern Profiling

Pattern profiling sits between local diagnosis and module dispatch. It does not replace
NS, DO, RT, deformation, or concealment analysis. It names the reusable higher-order
shape that keeps recurring across governed families so the operator can see whether the live burden
is first-order content, a meta-epistemic criterion fight, a meta-ontological category
fight, or a meta-noetic pattern in how the case is framed.

This file is the canonical owner for two governance fields:

- `claim_level`
- `pattern_profile`

`pattern-family-audit.md` remains the historical audit and regression document. This file
is the operational owner used by the live DSL/IR.

---

## Claim-Level Codes

Use one code for the governing level of the live pressure:

| Code | What it means | Route consequence |
|------|---------------|------------------|
| `first-order` | The live pressure is about the content claim itself | Route by the ordinary NS / DO / RT stack after upstream gates clear |
| `meta-epistemic` | The live pressure is about what counts as knowledge, proof, evidence, testimony, neutrality, or rational warrant | Clear the criterion, proof-method, or authority-order burden before first-order content |
| `meta-ontological` | The live pressure is about what categories may apply, what ontological distinctions are admissible, or whether a category-set has been installed as tribunal | Clear category, predication, definition, or perfection-criterion burdens before first-order content |
| `meta-noetic` | The live pressure is about the structure of recognition, suppression, deformation, concealment, or the conditions under which any content can land | Clear the noetic/register burden before content dispatch |
| `cross-level` | A first-order claim and a higher-order burden are simultaneously live and both must stay explicit | Keep both live in case-state and IR; sequence higher-order clearing first |

Rule: `claim_level` names the governing level, not every level present in the conversation.
If the case opens with first-order vocabulary but its force depends on a criterion, category,
or noetic-order claim, do not mark it `first-order`.

---

## Pattern-Profile Codes

Use `pattern_profile` when a recurring cross-volume family is doing real routing work.
Keep one primary profile. Carry secondary candidates in `Live alternatives`.

| Code | Name | Primary owner(s) |
|------|------|------------------|
| `PF-1` | Inherited framework / habituated belief | `seven-deformations.md`, `mixed-case-handling.md` |
| `PF-2` | Evidentialist demand / pre-inquiry criterion pressure | `foreign-premise-detection.md`, `V2-reconstituting-reason.md` |
| `PF-3` | Canon formation / text selection / authority certification | `V10-transmission-content-vetting.md`, `do-christian-extensions.md` DO-14, `revelation-transmission.md` RT-2 |
| `PF-4` | Transmission / preservation / authentication | `V10-transmission-content-vetting.md`, `revelation-transmission.md`, `hadith-authentication-epistemology.md` |
| `PF-5` | Doctrinal complexity / disagreement pressure | `mixed-case-handling.md` |
| `PF-6` | Christology / Trinity / Jesus-status pressure | `V12-tamanuc-exhaustion.md`, `do-christian-extensions.md` |
| `PF-7` | Comparative prophethood / why this revelation | `do-second-loop.md`, `prophecy-wahy-supremacy.md` |
| `PF-8` | Positive restoration / opening framing | `P1-fitrah-restoration.md`, `P4-maieutic.md` |
| `PF-9` | Self-refutation / performative incoherence | `M1-self-refutation.md`, `M1P-performative-self-refutation.md` |
| `PF-10` | Grief / existential pressure / evil register-hold | `M4-grief-register.md`, `mixed-case-handling.md` |
| `PF-11` | Muslim-internal crisis / authority fatigue / textual destabilization | `profiles/ns-8-muslim-internal-crisis.md`, `P5-already-believing.md`, `revelation-transmission.md` RT-4 |
| `PF-12` | Philosophical naturalism / scientistic filtering | `profiles/ns-1-naturalist.md`, `V2-reconstituting-reason.md`, `philosophical-usurpation.md` |

Do not treat `pattern_profile` as a substitute for `case_family`. `case_family` names the
live routed family; `pattern_profile` names the reusable cross-volume shape explaining why
that family is recurring in this form.

---

## Meta-Noetic Regularities

Pattern profiles cluster into a small reusable grammar. Surface this only when it clarifies
the case.

- `tribunal-installing` regularity: `PF-1`, `PF-2`, `PF-12`
- `authority-certification` regularity: `PF-3`, `PF-4`, `PF-7`, `PF-11`
- `register-hold / restoration-order` regularity: `PF-5`, `PF-8`, `PF-10`
- `coherence / predication / self-undermining` regularity: `PF-6`, `PF-9`

These regularities do not add new routing families. They show how a case's local burden
propagates upward into the repo's diagnostic grammar.

## Owner Exception: Imported Perfection / Non-Eventfulness

Do not create a new PF code merely because perfection, immutability, simplicity, or
non-eventfulness language appears. That burden is already owned by
`perfection-criterion-usurpation.md` when it functions as tribunal, by M9 when it is
carried through loaded terms, and by V8 / `sound-reason-epistemology.md` after the
upstream gate clears.

Emission rule: use `claim_level: meta-ontological`; use `pattern_profile: PF-6` only
when the case is specifically a Christian Trinity / perfection overlay. Otherwise emit
`pattern_profile: none` and route by the diagnostic owner.

---

## Emission Rules

Use this file to emit:

```text
Claim level: <first-order | meta-epistemic | meta-ontological | meta-noetic | cross-level>
Pattern profile: <PF-1 ... PF-12 | none>
```

Discipline:

1. If `claim_level` is not `first-order`, do not dispatch first-order DO / RT / profile content
   until the governing higher-order burden has been cleared.
2. Use `pattern_profile` only when it changes routing, sequencing, or owner selection.
3. Keep at most one primary profile. If two are genuinely live, carry the second in
   `Live alternatives` or `What remains live`.
4. If the case is too thin for a stable profile, omit `pattern_profile` rather than forcing one.
