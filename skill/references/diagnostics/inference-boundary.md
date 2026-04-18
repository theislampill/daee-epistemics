# Inference Boundary Markers

> role: diagnostic-governance
> use when: the response draws on more than one file, extends the file content, or risks overclaiming
> do not use when: every material claim is directly grounded and no metadiscursive marking is needed
> output: source-status labels that separate anchored skill content from model-added reasoning

This file governs the difference between what the repository says, what multiple files jointly
support, what the model is inferring, and what remains speculative.
Use this file as the canonical source-status legend whenever a response crosses file boundaries.
The short legend is mirrored in `skill/SKILL.md` §V and can be surfaced there without treating this
file as a separate topic module.

## Marker Set

- `[anchored]` Directly grounded in a loaded file or in the explicit governing thesis of the skill.
- `[synthesis]` Drawn by combining multiple loaded files without adding a new thesis.
- `[inference]` A model-level inference extending beyond what the loaded files explicitly state.
- `[speculative]` A tentative extension, hypothesis, or extrapolation that should not govern the case unless confirmed.

## Source Status vs. Source Weight

Source status and source weight are not the same thing.

- **Status** asks how a claim relates to the loaded material: anchored, synthesized, inferred, or speculative.
- **Weight** asks what kind of material is carrying the claim: core theory/case architecture,
  research-grade study, narrower argumentative resource, or light operational/instructional aid.

Do not let a lower-weight source inherit the status of a higher-weight one merely because both are
loaded.

## Source-Weight Discipline

- Core theoretical files, case files, and research-grade studies may anchor substantive doctrinal
  or epistemic claims when they are actually loaded.
- Narrower argumentative resources, edited collections, or translated discussions may anchor a
  specific distinction or formulation, but they should not by themselves silently reset the whole
  architecture.
- Course decks, lecture notes, and operational notes may anchor sequencing, examples, reminders, or
  quick distinctions; they should not by themselves settle doctrine or override higher-weight
  material.

## Rules

- Do not present `[inference]` or `[speculative]` material as though it were `[anchored]`.
- If a key move depends on `[synthesis]`, name the files or distinctions being joined.
- If a key move depends on materials with different weights, name that difference instead of
  flattening them into one evidentiary class.
- If a response depends materially on `[inference]`, state what evidence would confirm or weaken it.
- Reserve `[speculative]` for rare cases where the extension is useful enough to expose openly.
- If most of the case read would need `[inference]`, shrink the claim or mark the diagnosis underdetermined.

## Default Priority

Prefer this order when building a response:

1. `[anchored]`
2. `[synthesis]`
3. `[inference]`
4. `[speculative]`

The further down the list a claim sits, the more proportion, tentativeness, and explicit marking it requires.

---

## Usage Examples by Marker

### `[anchored]`

**With correct marker:**
"The fiṭrah's deliverance of the Creator is ḍarūrī, not iktisābī — inferential argument is a legitimate restorative or remedial route, but it is not the universal precondition of warranted belief. [anchored — sound-reason-epistemology.md §2]"

**Without the marker (showing the problem):**
"The fiṭrah's deliverance of the Creator is ḍarūrī." — Stated as if obvious, without indicating it is directly grounded in the file. The reader cannot distinguish this from an inference the model is making on the file's behalf.

**Why the marker matters:** `[anchored]` tells the reader that the claim is directly stated in a loaded file and can be audited against it. Without the marker, anchored claims become invisible — indistinguishable from synthesis or inference, and the response loses auditability.

---

### `[synthesis]`

**With correct marker:**
"The combination of V2 (framework-clearing) and V9 (necessary-knowledge priority) means that when a criterion is contaminated, the correct order is: loosen the criterion first, then show that the fiṭrī deliverable it was excluding is ḍarūrī. [synthesis — V2 + V9 + sound-reason-epistemology.md §1]"

**Without the marker (showing the problem):**
"V2 and V9 together establish that you must loosen the criterion before engaging the fiṭrī deliverable." — Presented as a single file's doctrine when it is actually the result of combining two files. A reader checking one file will not find this claim, and the response appears to overclaim the source.

**Why the marker matters:** `[synthesis]` identifies where cross-file combination is doing work. It distinguishes a claim derived from multiple loaded files from a claim directly anchored in one — preventing accidental overclaiming of any single file's content.

---

### `[inference]`

**With correct marker:**
"Given the interlocutor's pattern of objection-regeneration after each dissolved objection, the governing deformation is likely hawā rather than genuine shubhah — though this read would need confirmation from a follow-up exchange. [inference — extending M5's pattern-criteria to this specific case]"

**Without the marker (showing the problem):**
"The governing deformation here is hawā." — Stated as if diagnosed from the files, when it is actually a model-level extension. The reader cannot tell whether this is anchored in the diagnostic files or extended from them, and the confidence level is inflated.

**Why the marker matters:** `[inference]` signals that the claim extends beyond what the files explicitly state. It allows the reader to calibrate confidence, know where the model has gone beyond its sources, and know what evidence would confirm or weaken the claim.

---

### `[speculative]`

**With correct marker:**
"It is possible that the interlocutor's framework-clearing would require multiple exchanges before loosening — the ʿāda may be operating alongside the iʿtiqādāt mawrūtha, which would mean V2 alone is insufficient and V5 would need to follow at close interval. [speculative — this extension is not derivable from the current excerpt alone]"

**Without the marker (showing the problem):**
"V2 alone is insufficient here; V5 will also need to be deployed." — Stated as if confirmed, when the basis is a plausible extension that has not been verified by any signal from the interlocutor. The response may route to a module the case does not yet warrant.

**Why the marker matters:** `[speculative]` prevents a tentative hypothesis from governing a response as if it were a confirmed read. It keeps the response proportioned to the actual basis and signals that the extension should not drive module selection unless confirmed.

---

## Mandatory Pre-Release Check

Before finalizing any response, confirm:

1. Every claim that extends beyond the loaded files is marked — `[inference]` or `[speculative]` as appropriate.
2. No synthesis claim is presented as anchored — if the claim combines two or more files, it carries `[synthesis]`, not `[anchored]`.
3. No inference is presented as synthesis — if the claim goes beyond what the loaded files jointly state, it is `[inference]`, not `[synthesis]`.
4. Every speculative extension is explicitly flagged as such and is not allowed to govern module selection or diagnosis unless confirmed by additional signals.

---

## Integration with [Source Basis] Block

The `[Source Basis]` block in `case-state-schema.md` requires source-weight annotation when unlike source types are joined. The inference-boundary markers feed directly into that block: a claim marked `[inference]` must be listed as inference-weight in `[Source Basis]`, not as anchored. A claim marked `[synthesis]` must name the files being combined. The markers in the response body and the weight annotations in `[Source Basis]` must be consistent — they are two surfaces of the same audit trail.
