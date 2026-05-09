---
id: anti-patterns
module_class: governance
canonical_path: skill/references/diagnostics/anti-patterns.md
contract_version: "0.3.2.0"
load_when:
  - preparing, reviewing, or correcting a response path
catalogue_registered: false
---

# Anti-Patterns

## Core Anti-Patterns

The following entries expand the compressed table into full audit-grade entries. Each entry gives a one-line definition, a concrete positive example (the pattern appearing in output), a concrete negative example (correct behavior in the same case), and a self-audit question.

---

**Forced Fit**
*Definition:* Pushing an unfamiliar or mixed case into a familiar module because the module is ready to hand, rather than because the case has been confirmed as the module's proper domain.
*Pattern appearing in output:* An interlocutor makes one off-hand remark about evolution; the response immediately deploys NS-1 full profile and V2 as though naturalism were confirmed as the governing noetic structure.
*Correct behavior in the same case:* Mark the read provisional. Answer the specific claim made. State that NS-1 is a candidate but has not been confirmed; note what additional signals would confirm it.
*Self-audit question:* Have I confirmed the case family by multiple convergent signals, or did I choose this module because it is the first plausible match?
*Prevented by:* `V1-diagnostic.md` (full diagnostic pass before module selection); `noetic-reading-checklist.md` (multiple-convergent-signal requirement before NS code is assigned); `mixed-case-handling.md` (provisional status requirement when signals are thin).

---

**Recursive Overfitting**
*Definition:* Re-running the full diagnostic pass after every exchange move, even when no new differentiator has appeared, generating a cascade of diagnoses that substitutes for a clear intervention sequence.
*Pattern appearing in output:* After each exchange turn, a new case-state line is generated with slight revisions to the NS code and deformation read, none of which change the next move or the module selection.
*Correct behavior in the same case:* Re-run V1 and update the case-state only when a move has cleared an upstream barrier, the interlocutor has shifted register, or a new objection family has appeared. Otherwise hold the current read and proceed with the current module.
*Self-audit question:* What specifically changed that justifies a new diagnostic pass — has intervention order actually shifted?
*Prevented by:* `mixed-case-handling.md` §Recursive Reassessment (reassess only when a move has cleared an upstream barrier or a new differentiator has appeared); `heuristics.md` rule 28 (case-state-justified coordination); the case-state schema's `Reassessment` field (should say "not warranted" unless conditions met).

---

**Cumulative Inflation**
*Definition:* Adding supporting modules, routes, and argument tracks beyond the case-state-justified coordination that still governs the case, inflating response weight without adding productive leverage.
*Pattern appearing in output:* V2 has been deployed but the framework has not yet visibly loosened; the response then also loads E1, E3, V6, and M3, adding convergent evidential content before the filter through which it will be evaluated has been changed.
*Correct behavior in the same case:* Deploy only V2. Wait for a differentiating signal before escalating. Escalate to E3 or V6 only when no single blocker still dominates and multiple routes add genuinely non-redundant warrant.
*Self-audit question:* Is the upstream blocker genuinely cleared, or am I loading additional modules into an unreconstituted filter?
*Prevented by:* `mixed-case-handling.md` §Cumulative-Case Escalation (escalate only when no single upstream blocker dominates); `anti-patterns.md` (self-referentially: Cumulative Inflation IS this anti-pattern — the check against it is the upstream-blocker-still-dominant question); SKILL.md Named Routing Constraint 3 (no content before register is cleared).

---

**False Landing / Premature Continuation**
*Definition:* Treating politeness, surprise, or a local concession as permission to keep chaining, instead of stopping the current pass and waiting for a refreshed-state basis.
*Pattern appearing in output:* After one consequence lands, the response immediately adds a second consequence, a positive reconstruction, and a reserve-route preview because the interlocutor said "I can see that." Or the response treats a new sentence in the same message as automatic permission to continue without testing whether it is actually a differentiating signal that reopens V1.
*Correct behavior in the same case:* Type the recognition strength, stop the current pass, and reassess. Continue only if a fresh differentiating signal has reopened V1, the restoration target remains unmet, and no stop, register-hold, or semantic gate remains live for the next move. Medium or strong recognition may justify a pause; weak signals do not license either celebration or renewed pressure.
*Self-audit question:* Am I continuing because the state actually refreshed, or because I do not want to leave a landed move alone?
*Prevented by:* `recursive-state-transitions.md` (canonical abstract owner of the STOP / HOLD / RECURSE / PARTIAL state model and recursive re-entry conditions); `P7-restoration-stops.md` Stop 2 (one-live-question stop and recognition ladder); `diagnostic-ir.md` acceptance-state fields (`alignment_state`, `recognition_strength`, `continuation_eligibility`, `post_render_gate`); `routing-precedence.md` Rule P-3 (boundary reset); `heuristics.md` rule 17 (pause and refresh before further release).

---

**Premature Closure Without Re-Entry**
*Definition:* Rendering one strong bounded move and stopping without refreshing case-state, rechecking held material, and recording the post-render STOP / HOLD / RECURSE / PARTIAL decision.
*Pattern appearing in output:* The response exposes an imported tribunal, clears a loaded term, or lands a transmission-source discipline point, then ends as though closure were automatic. It does not ask what remains live in the same input, does not recheck held routes, and does not name the next eligible pass or explicitly say none.
*Correct behavior in the same case:* After the bounded move, run the post-render gate: identify what cleared, what remains live, which held routes were rechecked, which routes became newly eligible, the next eligible pass, and the recursion decision. STOP only when no live distortion remains and no held route became eligible. HOLD blocked material. RECURSE into the next bounded pass when eligible. Use PARTIAL when limits prevent eligible continuation.
*Self-audit question:* Did I stop because the gate found nothing live and no newly eligible route, or because the first move felt complete?
*Prevented by:* `diagnostic-ir.md` `post_render_gate`; `output-release.md` Post-Render Re-Entry Gate; `diagnostic-render-contract.md` Post-Render Gate / Final Governance section; `P7-restoration-stops.md` post-render gate rule; `heuristics.md` rule 35.

---

**Inference Laundering**
*Definition:* Presenting a model-level synthesis or inference as if it were directly anchored in a loaded file, without marking the extension.
*Pattern appearing in output:* A response claims "the position on X is Y" where the loaded file only implies this through multi-step inference; the claim appears without an `[inference]` or `[synthesis]` marker.
*Correct behavior in the same case:* Mark the claim `[inference]` or `[synthesis]` and name the files being combined or the inferential step being made. Use `[anchored]` only for claims directly stated in the loaded file.
*Self-audit question:* Is this claim directly stated in the loaded file, or am I extending it — and have I marked the extension?
*Prevented by:* `inference-boundary.md` §Mandatory Pre-Release Check (every claim extending beyond loaded files must be marked); `case-state-schema.md` §Source Basis block (`[Source Basis]` forces explicit annotation of anchored vs. synthesized vs. inferred); `heuristics.md` rule 30 (mark where inference begins).

---

**Decorative Terminology**
*Definition:* Using Arabic or technical terms because they add scholarly register, not because they change routing, scope, or doctrinal precision in the current case.
*Pattern appearing in output:* A response to a simple evidentialist question loads iʿtiqādāt mawrūtha, ẓann, mushābara fāsida, and muʿānada all within one paragraph, where a single "the criterion itself is unexamined" would have done the routing work.
*Correct behavior in the same case:* Introduce a technical term only when it changes what move is required or when the concept it names is operationally distinct from what plain English would convey.
*Self-audit question:* Does this term change the routing or the doctrinal precision, or is it adding prestige to a point that plain language would state more clearly?
*Prevented by:* `heuristics.md` rule 15 (prefer simplicity; the sharpest move over the most elaborate); `seven-deformations.md` §Gharaḍ (vested interest applies to practitioners too — the vested interest here is scholarly self-presentation); `case-state-schema.md` §Compression Rule (surface only fields that improve governance, not transparency theater).

---

**Higher-Order Vocabulary Theater**
*Definition:* Naming a case `meta-epistemic`, `meta-noetic`, `memetic`, or `PF-x` without distinguishing the actual higher-order burden, the deformation pattern, and the restoration target that routing must clear.
*Pattern appearing in output:* "This is a meta-noetic PF-2 / PF-12 problem" is announced, but the response never says whether the live pressure is criterion-import, naturalist filtering, aversion, or a blocked testimony-order question, and never types the restoration target beyond "respond to the framework."
*Correct behavior in the same case:* State the first-order claim if there is one, name the higher-order burden precisely, name the deformation or noetic pattern separately, and state the restoration target in the architecture's own grammar. Example: "First-order claim: revelation is under attack. Higher-order burden: meta-epistemic criterion import. Pattern: PF-2 inherited evidential pressure. Restoration target: sound reason / authentic-transmission order. So V2 or V10 clears first."
Emission means internal case-state / IR update for routing.
Internal NS/PF emission for routing means case-state / IR update, not visible default output.
Printing NS/PF codes or "meta-noetic memetics" without an IR/case-state/routing/hold-release consequence remains Higher-Order Vocabulary Theater.
*Self-audit question:* If I used higher-order vocabulary, have I said what it changes in routing and what layer is being restored, or did I only name the vocabulary?
*Prevented by:* `pattern-profiling.md` (claim-level and PF discipline), `noetic-reading-checklist.md` (higher-order assessment -> restoration hand-off), `case-state-schema.md` and `diagnostic-ir.md` (restoration-target typing), `heuristics.md` rule 29 (keep burden, pattern, and target distinct).

---

**Pattern-Print Theater**
*Definition:* Emitting a structural pattern print, load-bearing phrase, or background-topic shape without making it govern routing, suppression, release, or the next bounded move.
*Pattern appearing in output:* "This is a closed-canon veto / selective scriptural arbitrage pattern" appears in the analysis, but the response immediately lists prooftexts without typing whether authority, evidence, canon, interpretation, or identity wound is the live node.
*Correct behavior in the same case:* Use the optional IR fields only when they constrain action: name the load-bearing node, the intervention target, what is held, and which existing owner governs the next move.
*Self-audit question:* Did the pattern print change what I held, routed, or released, or did it only decorate the diagnosis?
*Prevented by:* `diagnostic-ir.md` optional structural framing field rules; `pattern-profiling.md` Structural Pattern Print Discipline; `routing-precedence.md` Rule S-8 and Rule P-1a.

---

**Identity Equilibrium Misread**
*Definition:* Either excluding identity from noetic diagnosis because it is protected/personal, or turning an identity marker into proof of motive, deformation, culpability, or the primary load-bearing node.
*Pattern appearing in output:* Under-reading: "identity is personal, so it cannot matter diagnostically." Over-reading: "because he is X, the argument is `hawa`," "his sexual identity is the criterion," "the identity layer is heavily load-bearing," "his identity is the framework through which every claim is processed," or "it is hawa dressed in moral reasoning."
*Correct behavior in the same case:* Treat identity as possibly modal/stabilizing inside the noetic equilibrium when the statement itself anchors that role, but mark source-status and keep the structure of the utterance primary. Say, for example: "The public identity-frame may stabilize the criterion or affect discourse orientation." Identity is a modal/stabilizing node, not the primary verdict-bearing load-bearer unless the statement itself makes it primary. Hawa/irad require source-status caution; do not assert them as default verdicts from identity or context alone.
*Self-audit question:* Is the identity role anchored, inferred, or speculative/held? Am I reading how the structure is stabilized, or am I making a verdict about the person?
*Prevented by:* `noetic-reading-checklist.md` source-status discipline; `discourse-orientation.md` Identity-marker caution; `diagnostic-ir.md` existing structural fields; `P7-restoration-stops.md` Stop 4.

---

**Argument-Bank / Citation-Dump Substitution**
*Definition:* Treating a background topic as permission to unload arguments, citations, prooftexts, or comparative-religion content before the live structural burden has been typed and routed.
*Pattern appearing in output:* A question about Torah-completeness receives a list of biblical prooftexts; a Sufi kashf claim receives a broad anti-Sufism polemic; an Arya Samaj critique receives verse-by-verse Qurʾān defense; an anatta question receives a generic Buddhism rebuttal. In each case, the authority rule, criterion, semantic blocker, or identity-continuity node remains unidentified.
*Correct behavior in the same case:* Use background material only to frame the case structurally, then route through existing owners and TTPs. Cite, quote, or release detailed content only if the refreshed IR state makes that the next bounded move and the source-use discipline permits it.
*Self-audit question:* Am I using background material to decide what must clear first, or am I using it as an answer bank?
*Prevented by:* `diagnostic-ir.md` framing notes; `routing-precedence.md` upstream-node priority; `V10-transmission-content-vetting.md` source-use discipline; `inference-boundary.md`; `coverage-scope.yaml` out-of-scope entries.

---

**Tradition-Label Routing**
*Definition:* Routing by the named tradition rather than by the structural pressure that is doing the work.
*Pattern appearing in output:* The response treats "Hindu" as if it already means Advaita, Arya Samaj, popular polytheism, or perennialism; treats "Buddhist" as if it already means materialism; treats "Sufism" as if it already means either heresy or spirituality; treats "Jewish" and "Christian" canon objections as identical.
*Correct behavior in the same case:* Type the structure first: external criterion as tribunal, nondual ontology, identity-continuity pressure, kashf-as-tribunal, authority wound, closed-canon veto, or source-use problem. Then route to the existing owner that governs that structure.
*Self-audit question:* Did I classify the live node, or did I let the tradition label choose the answer?
*Prevented by:* `pattern-profiling.md`; `diagnostic-ir.md` Structural Validation Notes; `coverage-scope.yaml` non-covered claim entries; `TODO.md` closed scope decisions.

---

**Abuse-Wound / Doctrine Collapse**
*Definition:* Treating a harmful historical, institutional, teacher, family, or community wound as though it were already a doctrinal argument, or treating a doctrinal authority-order claim as though pastoral acknowledgement alone resolves it.
*Pattern appearing in output:* A person says they were harmed by a teacher or institution, and the response defends the doctrine. Or a person says a shaykh's kashf outranks ḥadīth, and the response only empathizes with bad experiences without addressing the claimed authority inversion.
*Correct behavior in the same case:* Separate wound from tribunal. If wound is primary, route relational safety, NS-8, and P7 before content. If tribunal is primary, route FPD/usurpation/source-use discipline while keeping pastoral register humane.
*Self-audit question:* Am I answering a wound as doctrine, or answering a tribunal claim as if it were only a wound?
*Prevented by:* `mixed-case-handling.md` Authority Wound + Authority Tribunal playbook; `P7-restoration-stops.md`; `foreign-premise-detection.md`; `diagnostic-ir.md` framing notes.

---

**Tactic Over-Selection**
*Definition:* Loading many modules because several seem relevant to the topic, rather than selecting the case-state-justified coordination that changes the next differentiator.
*Pattern appearing in output:* A response to a single hiddenness objection loads V1, M5, DO-1, P2, P4, M2, M3, and F2 in sequence, providing the full apparatus when a single well-placed M2 or the grief-register check would have changed the next live issue.
*Correct behavior in the same case:* Identify the one or two modules that address the current live differentiator. Defer everything else until the first move has been made and a new differentiator appears.
*Self-audit question:* Is each module in this response changing the next live differentiator, or am I loading it because it might be relevant?
*Prevented by:* `heuristics.md` rule 28 (case-state-justified coordination); `mixed-case-handling.md` §Stopping Conditions (stop when next module would only restate the same point); `case-state-schema.md` §Matched modules field (list only the current-pass coordination — do not advertise unused modules); SKILL.md Named Routing Constraint 5 (no argument-stacking after landed move).

---

**Rhetorical Overreach**
*Definition:* Attributing motive, concealment mode, or discourse orientation to the interlocutor without sufficient evidential basis, presenting inference as diagnosis.
*Pattern appearing in output:* From a single sentence expressing frustration with a ruling, the response concludes "this is juḥūd combined with gharaḍ" and names the interlocutor's resistance as culpable denial.
*Correct behavior in the same case:* Mark the read provisional. State what signals would confirm or disconfirm the candidate mode. Respond to the established claim-type only; do not name a concealment mode without multiple convergent signals.
*Self-audit question:* Do I have multiple convergent signals supporting this characterization, or am I extrapolating from a single data point?
*Prevented by:* `modes-of-concealment.md` (iʿrāḍ vs. juḥūd boundary and juḥūd vs. inkār boundary require multiple convergent signals); `mixed-case-handling.md` §Insufficient-Basis Conditions (do not claim a settled read of concealment mode when evidence is thin); `heuristics.md` rule 5 (distinguish register before naming a mode); SKILL.md Named Routing Constraint 4 (no confident family-lock from thin basis).

---

**Diagnosis Collapse**
*Definition:* Replying to the surface content of a question before classifying the noetic structure, deformation, and discourse orientation — skipping V1 and loading content that may be addressed to the wrong register.
*Pattern appearing in output:* An interlocutor asks about theodicy and the response immediately deploys DO-2 probabilistic analysis without checking whether the presenting register is grief (M4) or intellectual (shubhah), and without establishing that the discourse orientation is truth-seeking.
*Correct behavior in the same case:* Run V1 first. Identify the claim-type, the concealment mode, the deformation, and the discourse orientation before selecting any content module. Diagnose before rebutting.
*Self-audit question:* Have I run V1 and confirmed the noetic structure, deformation, and discourse orientation before loading content?
*Prevented by:* `V1-diagnostic.md` (the diagnostic gate itself); SKILL.md Named Routing Constraint 1 (no content module before V1 has been run); `heuristics.md` rule 2 (start with V1); `framework-pipeline.md` (forbidden shortcut path: intake → direct doctrinal rebuttal).

---

**Excerpt Over-Read**
*Definition:* Assigning a confident NS code, deformation type, or concealment mode from a conversation excerpt that is too thin to support the assignment — without marking the read provisional or naming what differentiating signal would resolve the ambiguity.
*Pattern appearing in output:* A three-sentence excerpt in which someone asks "isn't it arrogant to think your religion is right?" is diagnosed as NS-5 (habituated atheist) with primary deformation hawā and concealment mode istikbār. A confident [Diagnostic IR] block is emitted and the matched modules are loaded.
*Correct behavior in the same case:* Mark read status as `underdetermined`. List the competing NS candidates (NS-5, NS-2, or possibly NS-4). Answer the specific claim made — the arrogance charge — without assigning a governing read to the whole case. State: "Differentiating signal: whether this is a held position (NS-5 candidate), a principled criterion objection (NS-2 candidate), or a moral-parity argument (NS-4 candidate) — cannot be distinguished from this excerpt alone."
*Self-audit question:* Is my NS/deformation/concealment diagnosis supported by multiple convergent signals from this excerpt, or by the most plausible surface reading of a single sentence?
*Prevented by:* `P7-restoration-stops.md` Stop 4 (underdetermined-case stop — "do not assign a deformation or concealment code without sufficient signal"); `mixed-case-handling.md` §Insufficient-Basis Conditions; `noetic-reading-checklist.md` multiple-convergent-signal requirement; SKILL.md Named Routing Constraint 4 ("no confident family-lock from thin basis").

---

**Register-Hold Bypass**
*Definition:* Deploying a matched content module when the concealment × orientation matrix in `case-state-schema.md` specifies that the current register requires a hold — loading doctrinal or case-library content into a cell that says "relational only," "held pending register shift," or equivalent.
*Pattern appearing in output:* Concealment is confirmed as iʿrāḍ (aversion) and discourse orientation is identity-performance. The matrix cell for this pair says "Iʿrāḍ compounded by identity performance hardens under argument. Relational only; no doctrinal module." The response nonetheless loads DO-1 (divine hiddenness rebuttal) and deploys probabilistic analysis of sincere non-belief.
*Correct behavior in the same case:* Confirm the matrix cell before loading any content module. When the cell specifies relational-only, invitational, or character-as-evidence: deploy exactly that. Include in the case-state: "Register-hold: iʿrāḍ + identity-performance. Deployable on shift to: truth-seek orientation or concealment clearing." Hold the matched DO module until the register shifts.
*Self-audit question:* Did I check the concealment × orientation matrix cell before loading any content module? Does the cell I confirmed permit full apparatus deployment, or does it specify a hold?
*Prevented by:* `case-state-schema.md` §Concealment × Orientation Routing Matrix (explicit cell-level rules); `diagnostic-ir.md` Gate Check 6 ("confirm the concealment × orientation matrix cell shows content is deployable now"); SKILL.md Named Routing Constraint 3 ("no content-before-register"); `P7-restoration-stops.md` Stop 1 (Content-Withholding Stop — the hard-rail version of the same constraint).

---

**Restoration-First Default**
*Definition:* Loading P1 (fiṭrah-restoration) or P4 (maieutic) as the opening move when the case carries a live epistemic question — evidentialist demand, canon or authority confusion, doctrinal complexity structured as argument — that requires the matched content module before any restoration framing.
*Pattern appearing in output:* An interlocutor with an inherited-tradition background asks "which Bible is authoritative, and how would anyone know?" The response immediately frames the question as a fiṭrah-recognition opportunity, invites reflection on creation, and omits the canon-authority analysis the interlocutor actually asked about. Or: an interlocutor with an evidentialist criterion objection receives P4 maieutic prompts about inner recognition before V2 has loosened the criterion that is doing the governing work.
*Correct behavior in the same case:* Run V1 and foreign-premise detection (FPD). Identify the live epistemic question and the matched content module. Deploy the matched module first — DO-14 for canon-selection, DO-10 for ḍarūrī criterion attacks, V2 for inherited evidentialist criteria, V10 for transmission pressure. Restoration framing may accompany the engagement later (once the epistemic question has been met) but never substitutes for the matched module.
*Self-audit question:* Does this case carry a live epistemic question (evidentialist demand, canon/authority confusion, doctrinal-complexity-as-argument), and if so have I deployed the matched content module before loading any restoration frame?
*Prevented by:* `mixed-case-handling.md` Playbook (v) §Critical correction to the "restoration-first" failure mode (the localized correction this anti-pattern generalizes); `P7-restoration-stops.md` Stop 1 (Content-Withholding Stop — the inverse guard, preventing content when register requires hold; restoration-first is the other-direction failure, preventing content when content is what is required); `kernel-thesis.md` Commitment 4 (restoration works through matched content, not around it); `heuristics.md` rule 12 exception clause (restoration framing supports but does not substitute epistemic content when epistemic demand is present); SKILL.md Named Routing Constraint 1 (no content module before V1 has been run — the read from V1 is what separates restoration-need from epistemic-need).

---

---

**Semantic Gate Bypass**
*Definition:* Releasing doctrinal or attribute content while an upstream semantic blocker is still live - recontented prophetic discourse, evacuated prophetic discourse, or an unresolved loaded negative theological term.
*Pattern appearing in output:* The response answers "God is not a body" or "bilā kayf solves it" before clarifying what "body," "direction," "composition," or the prophetic-language claim is actually being made to mean.
*Correct behavior in the same case:* Clear the semantic blocker first. If prophetic discourse is being redirected or evacuated, run the prophetic-discourse-neutralization pass. If the case is built on loaded anti-attribute vocabulary, run M9's lexical-ontological split before doctrinal release.
*Self-audit question:* Have I restored meaning before releasing doctrine, or did I answer a semantically unstable question as if it were already well formed?
*Prevented by:* `prophetic-discourse-neutralization.md`; `M9-predication-mode.md`; `routing-precedence.md` Rule S-6; `diagnostic-ir.md` semantic-discipline gate.

---

**Ghost-Load**
*Definition:* Listing a module in `matched_modules` and loading its governing file, but writing output that does not demonstrably use that file — no `source_basis` entry with `source_kind: "module"` links any output claim or routing decision back to it.
*Pattern appearing in output:* A DO-12 case loads M9-predication-mode.md and lists M9 in `matched_modules`, but the `[Source Basis]` block contains no entry with `source_kind: module, module_id: M9`. The predication analysis in the response is plausible and consistent with M9 but is not traceable to it.
*Correct behavior in the same case:* After loading M9, record at least one `source_basis` entry: `source_kind: "module"`, `module_id: "M9"`, `basis_type: "anchored"` or `"inference"`, and `claim` naming the specific output claim or routing fork M9 governed. If M9 governed only a routing decision (e.g., "run count-noun analysis before Trinitarian overlay"), name that decision as the claim.
*Self-audit question:* For each entry in `matched_modules`, does a `source_basis` entry with `source_kind: module` and matching `module_id` exist? If not, either add it or move the module to `What is withheld and why`.
*Prevented by:* `SKILL.md` Rule 14 (source_basis entry required for every matched_modules entry); `diagnostic-ir.md` §Current-pass activation rule ghost-load prohibition bullet; `diagnostic-ir.schema.json` §source_basis allOf constraint (module_id required when source_kind is "module").

---

**Transcendence Default / Abstraction-as-Cure**
*Definition:* Responding to a specific attribute, coherence, or predication objection by invoking divine transcendence, bilā kayf, or mystery language as the primary move — before the semantic splitting, predication-mode analysis, and analytical distinction work the objection actually requires.
*Pattern appearing in output:* An interlocutor asks whether God's knowledge of particulars implies dependence on them. The response deploys bilā kayf and transcendence language immediately without first running M9 on the loaded term "dependence," distinguishing ontological from logical dependence, or engaging the composition / dependence distinction the objection requires. The interlocutor's specific confusion is unaddressed; the same objection regenerates downstream.
*Correct behavior in the same case:* Run M9 on the loaded term first. Distinguish ontological dependence (implying incompleteness) from logical distinction (not implying dependence). After the specific analytical work is done, bilā kayf may anchor the result — as a genuine doctrinal anchor after the problem is identified, not as a shortcut around identifying it.
*Self-audit question:* Am I deploying transcendence or bilā kayf because the specific analytical work has been completed and this is its honest conclusion, or am I using it to bypass the work the objection actually requires?
*Prevented by:* `V8-bila-kayf-anchor.md` (bilā kayf anchors after semantic and predication work, not instead of it); `M9-predication-mode.md` Function 4 (semantic split required before yes/no answer on a loaded term); `do-attribute-precision.md` §Three-Layer Owner Distinction (route order M9 → definition-discipline → attribute-precision → V8); `routing-precedence.md` Rule S-6 (semantic gate must clear before doctrinal release).

---

**Held-but-Answered Contradiction**
*Definition:* Declaring that a downstream issue is held by register, semantic, or stop governance, then effectively answering it in the same pass under a different heading or as part of the "bounded answer."
*Pattern appearing in output:* A response states "composition/dependence pressure governs first; downstream coherence question is held." The response then proceeds to answer whether the doctrine is coherent in the [Restorative Response] section, under the label "preliminary clarification."
*Correct behavior in the same case:* If composition/dependence governs first, the coherence answer stays held. It may be named as downstream but not answered. After the governing move clears, refresh state; if the coherence question remains live, it becomes the next bounded pass.
*Self-audit question:* Did I name something as held and then answer it under a different label in the same pass?
*Prevented by:* `references/rubrics/output-release.md` §4 (held material actually held); `routing-precedence.md` Rule P-1 (upstream-blocker priority); `SKILL.md` Rule 8 (no held-as-never-answer — but also no held-while-answering).

---

**Held-as-Never-Answer**
*Definition:* Treating a hold at the current traversal point as permanent suppression — never reassessing the held material after the governing blocker is cleared, and never releasing it even when the refreshed case-state would permit it.
*Pattern appearing in output:* Upstream blocker X is addressed. The response ends. Downstream material Y was correctly held during X's pass, but no reassessment is performed. If the interlocutor asks Y directly, the response still treats Y as held without checking whether X's clearing removed the basis for the hold.
*Correct behavior in the same case:* After X clears, refresh state. If Y remains live and no stop, register-hold, or semantic gate now blocks it, release the bounded Y move. If Y no longer governs (because X's clearing dissolved it), compress or drop it explicitly.
*Self-audit question:* Is any material I am holding still actually blocked by a live gate, or am I continuing to hold it by inertia after the governing blocker was cleared?
*Prevented by:* `references/rubrics/output-release.md` §4 (held material reassessed after refresh); `P7-restoration-stops.md` (stops govern current pass, not all future passes); `recursive-state-transitions.md` (RECURSE is licensed after refresh when target remains unmet).

---

**State-Re-Read-as-User-Reply-Only**
*Definition:* Treating state re-read as an operation that can only happen when the interlocutor sends a new message — never allowing same-response recursion even when the current pass itself has cleared the governing blocker and the next live burden is now visible.
*Pattern appearing in output:* An imported tribunal is named and refused within the response. The response correctly identifies that the downstream positive reconstruction is now eligible, but says "I will address this in my next reply after you respond." The interlocutor's next message only repeats the question; no new signal was needed.
*Correct behavior in the same case:* Tribunal refusal clears the upstream blocker. Refresh state internally. If the downstream reconstruction remains live and no stop/hold/gate blocks it, release the bounded next move within the same response. Do not manufacture a dependency on a new user turn.
*Self-audit question:* Am I waiting for a user reply because a stop, register-hold, or semantic gate genuinely requires one — or because I am modeling refresh as only conversational turn-taking?
*Prevented by:* `references/rubrics/output-release.md` §7 (same-response recursion bounded but permitted); `SKILL.md` Rule 15 (state re-read may occur inside the same response); `P7-restoration-stops.md` (stops govern deployment; not requiring external reply before every bounded next move).

---

**Recursive Dump**
*Definition:* Treating the permission for governed recursive traversal as license to release every downstream burden, argument, and module at the moment of a single state re-read — answering all detected issues simultaneously without ordered traversal.
*Pattern appearing in output:* An interlocutor asks about divine direction. A loaded spatial term governs. It is cleared. The response then immediately releases: attribute content, composition analysis, bilā kayf anchor, philosophical-usurpation framing, and a cosmological argument — because all were detected as downstream during the initial diagnostic pass.
*Correct behavior in the same case:* Clear the loaded spatial term. Refresh state. Identify whether composition/dependence pressure remains live and now governs. If yes, release only that bounded move. Refresh again. Each live burden is traversed in order, not simultaneously.
*Self-audit question:* Am I releasing all detected downstream items at once, or am I moving burden-cycle by burden-cycle with a state re-read before each release?
*Prevented by:* `references/rubrics/output-release.md` §5 (recursive traversal discipline: 7-step ordered process); `recursive-state-transitions.md` (RECURSE is governed re-entry, not autonomous looping); `P7-restoration-stops.md` Stop 2 (boundary reset after landing).

---

**Essay-Sequence Recursion**
*Definition:* Replacing governed same-response recursion with essay headings such as "Move 1", "Move 2", "Move 3", or "Move 4" while never showing a refreshed-state transition.
*Pattern appearing in output:* FPD is named, then hiddenness, accountability, hell, mercy, and pastoral synthesis are each placed under a numbered "move" heading. No transition says what cleared, what remains live, why the next live burden was already present, or why RECURSE rather than STOP/HOLD/PARTIAL governs.
*Correct behavior in the same case:* If the imported criterion clears, state the transition in ordinary prose and release only the next bounded eligible burden. If no burden is eligible, STOP or HOLD. If limits prevent the next pass, PARTIAL.
*Self-audit question:* Could each "move" be justified from state re-read, or am I outlining an essay?
*Prevented by:* `recursive-state-transitions.md`; `output-release.md`; `diagnostic-render-contract.md`.

---

**Clean Essay Cosplay / Clean Essay Failure**
*Definition:* The answer avoids visible IR / Case State / route ledger, but still proceeds as a topical essay itinerary. It fails `B -> {s1...sn} -> Land(B) -> R -> Decision`: no bounded operator result, state re-read, live-burden eligibility, or licensed STOP/HOLD/RECURSE/PARTIAL. A multi-burden default answer without a minimum visible transition spine is invalid even if clean, accurate, and well-written.
*Pattern appearing in output:* The answer has no `## Diagnostic IR`, no `Case State:`, and no visible ledger, but it moves from criterion language into hiddenness, hell, accountability, consequence tracing, mercy, and pastoral synthesis without showing state re-read, release gating, or STOP / HOLD / RECURSE / PARTIAL discipline.
*Bad signs:* multiple topical sections without state re-read transitions; hidden premises listed but no operator result; criterion addressed, then doctrine dumped; pastoral close added without final state re-read; "governed prose" claimed but not executed; topical organization passed off as governed traversal; multi-burden response without a visible minimum transition spine between live burdens.
*Correct behavior in the same case:* Every pass shows the runtime spine: `Input -> IR(N,m,τ,σ) -> B -> {s1...sn} -> Land(B) -> R(H,Δ) -> STOP/HOLD/PARTIAL/RECURSE`. Gloss: if another eligible live burden remains, recurse through one bounded next pass with a prose transition or mark PARTIAL if limits prevent it.
*Self-audit question:* Is this clean prose the surface of a governed pipeline, or only a well-written topical essay?
*Prevented by:* `framework-pipeline.md` pipeline validity; `diagnostic-ir.md` internal-state-before-routing rule; `output-release.md` release gate; `diagnostic-render-contract.md` Default Final-Output Preflight Gate; `recursive-state-transitions.md` state re-read and no-premature-STOP rule.

---

**Component-Tour Cosplay**
*Definition:* The answer treats facets as burden-cycles even when `Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`. It may discuss imported criterion, non-belief, hiddenness, punishment, identity, and pastoral response, but never proves STOP/HOLD/PARTIAL through state re-read.
*Pattern appearing in output:* A complex prompt with moral protest, hiddenness, and accountability is answered with a well-structured essay that covers each topic because it was detected, not because `R` licensed it as the next input-anchored `B`. topic transition ≠ recursion. component tour ≠ recursion.
*Bad signs:* all topics addressed without state re-read transitions between passes; no enumeration of remaining input-anchored live burdens after any bounded pass; the response covers the same topics regardless of whether a prior bounded operator actually landed; final STOP is asserted without proving no input-anchored eligible burden remains.
*Correct behavior in the same case:* `B -> {s1...sn} -> Land(B) -> R -> Decision`. Gloss: after Burden-Cycle 1 lands the governing blocker, enumerate remaining already-present live burdens; STOP only after none remains, otherwise HOLD/PARTIAL/RECURSE with the named next pass.
*Self-audit question:* Is each section driven by a state re-read that enumerated remaining input-anchored live burdens, or was the response planned as a topical itinerary from the initial read?
*Prevented by:* `recursive-state-transitions.md` (input-anchored live-burden rule, one bounded live burden per burden-cycle, Component-Tour failure test); `output-release.md` (state re-read enumeration requirement); `diagnostic-render-contract.md` (minimum visible transition spine).

---

**Single-Pass Layer A/B Cosplay**
*Definition:* The response prints the compact Layer A + Layer B + state re-read burden-cycle shape exactly once and then stops — without proving no eligible input-anchored live burden remains, or without continuing when state re-read = RECURSE. The structured form is present but the multi-pass recursion discipline is not executed. Printing the shape once does not satisfy multi-burden governance.
*Pattern appearing in output:* A complex prompt receives Pass 1 with compact Layer A, a bounded prose Layer B, and a state re-read block. The state re-read says "Governance: STOP" or names a second live burden, but the response closes without running Pass 2. The compact structure makes the response look governed while bypassing the recursive re-entry requirement.
*Bad signs:* state re-read lists remaining input-anchored burdens but governance = STOP without proving they are held/partialed; compact Layer A is printed but the second eligible burden named in it is never addressed; state re-read block present but "Remaining input-anchored burdens" field is empty when the original input had multiple burdens.
*Correct behavior in the same case:* After Pass 1 state re-read = RECURSE, continue with Pass 2 Layer A (updated governing burden), Pass 2 Layer B, Pass 2 state re-read. Continue until governance = STOP / HOLD / PARTIAL with demonstrated reason. Each pass uses a fresh Layer A derived from the refreshed state, not a copy of Pass 1.
*Self-audit question:* Did I print the burden-cycle shape and then perform governed recursive re-entry, or did I print the shape and then stop as if printing it were the same as executing it?
*Prevented by:* `recursive-state-transitions.md` (no premature STOP, RECURSE when eligible burden remains); `diagnostic-render-contract.md` compact Layer A → Layer B → state re-read burden-cycle shape and Single-Pass Layer A/B Cosplay invalidity.

Source-status correction: a single public identity statement is not differentiating signal
for hawā or iʿrāḍ. Keep concealment / deformation at anchored or inference level unless
the noetic-state source-status rules supply input evidence for a verdict.

---

**TTP Name-Dropping**
*Definition:* Naming a TTP label in prose without selecting and executing the operator from validated case-state / IR.
*Pattern appearing in output:* The answer says "the M1 move" or "the M8 move" but the paragraph behaves like generic worldview critique, not a bounded source-backed operation with state re-read after it lands.
*Correct behavior in the same case:* Select the TTP from the validated IR, state or imply the bounded target, perform the operation, refresh state, and release a downstream TTP only if it becomes the next eligible pass.
*Self-audit question:* Did the TTP perform its specific operation, or did I only name its label?
*Prevented by:* `diagnostic-ir.md` source-basis rules; `output-release.md` TTP execution rule; `framework-pipeline.md` forbidden shortcut.

---

**Owner-Body Not Loaded Compression**
*Definition:* Rendering a hard or complex burden from root SKILL recognition, TTP label memory, or `matched_modules` naming without loading or having access to the active owner body / compiled bundle section.
*Pattern appearing in output:* The response names `V2`, `M9`, `P3`, or another owner label, then emits a broad Target/Operation/Result block that could fit many cases and never demonstrates the owner-specific operation floor.
*Correct behavior in the same case:* Load or consult the selected owner body / compiled bundle section, render owner-specific `B.s<i>` submoves, then `Land(B)` and `R(H,Delta)`. If the owner body cannot be loaded or identified, mark `PARTIAL / OWNER-BODY-NOT-LOADED` with the missing owner/path.
*Self-audit question:* Am I executing the owner body, or substituting root-summary recognition for Level 2 owner access?
*Prevented by:* `SKILL.md` owner-loadform map; `recursive-state-transitions.md` TTP entry criteria; `diagnostic-render-contract.md` hard-output render-through template; `output-release.md` owner-loadform gate.

---

**Diagnostic-Reduction Bypass**
*Definition:* Jumping from input/global Layer A to a selected route, module list, doctrinal answer, or restoration frame before completing the diagnostic reduction sequence: core axes -> mandatory Phase 2 passes -> overlays/specialty markers -> Diagnostic IR -> gate checks -> routing precedence.
*Pattern appearing in output:* The answer reads the case, names `FPD -> M1 -> DO-8 -> M8 -> restoration`, and begins answering from that itinerary without showing or internally preserving the required Phase 2 pass emissions/clearances.
*Bad signs:* no reason-category result; FPD used as a label rather than pass output; prophetic-discourse-neutralization and arabic-backbone-predicates silently skipped; IR formed retrospectively; routing precedence inferred from the route chain rather than applied before it.
*Correct behavior in the same case:* Complete diagnostic reduction first. Only after the IR and gate checks pass may routing precedence select the current live burden.
*Self-audit question:* Did I form a route itinerary before the diagnostic reduction was complete?
*Prevented by:* `SKILL.md` diagnostic-reduction order; `diagnostic-ir.md` gate protocol; `framework-pipeline.md` pipeline validity.

---

**Denomination-First / Source-Label Routing**
*Definition:* Routing by a named denomination, school, author, genealogy, source label, or topic before the diagnostic IR identifies the live deformation, concealment, criterion, tribunal, predication, authority-order, warrant, `claim_level`, and `pattern_profile`.
*Pattern appearing in output:* "This is an Ashari/Maturidi/Christian/naturalist objection, so here is the standard argument set," followed by denomination-specific apologetics, scholar/source stacks, or proof lists.
*Correct behavior in the same case:* `Pattern(deformation/concealment/unsoundness) > denomination/source-label`. A named framework may be recorded internally as source-status context, but it is not public-render material by default, not operative warrant, and not a route license. Route through the matched TTP/operator selected by the IR.
*Self-audit question:* Did the route come from the live noetic pattern, or from the label attached to the person, source, school, or topic?
*Prevented by:* `routing-precedence.md` Rule P-1a; `diagnostic-ir.md` runtime compiler contract; `recursive-state-transitions.md` source-status discipline; `output-release.md` source-status release check.

---

**Route-Chain Collapse**
*Definition:* Compressing diagnostic reduction and dispatch into a short route itinerary such as `FPD -> M1 -> DO-8 -> M8 -> restoration`, then treating that itinerary as the current bounded operator.
*Pattern appearing in output:* `Current bounded operator: FPD -> M1 -> DO-8 -> M8 -> restoration`.
*Bad signs:* Layer A prints a route chain; the bounded operator is a list of modules; route legs are used as the answer outline; restoration appears as a route leg rather than a post-refresh release.
*Correct behavior in the same case:* Current bounded operator names one burden-level function: `imported-criterion tribunal test`, `worship-worthiness criterion test`, or `hujjah/accountability correction`.
*Self-audit question:* Is the current bounded operator one function, or a compressed route?
*Prevented by:* `diagnostic-render-contract.md` Layer A field limits; `recursive-state-transitions.md` route-chain guard; `routing-precedence.md` current-burden rule.

---

**Route-Chain Recursion Cosplay**
*Definition:* Turning route legs into numbered `Pass` sections even though they are operative submoves under the same live burden.
*Pattern appearing in output:* Pass 1 is FPD, Pass 2 is M1, Pass 3 is DO-8, Pass 4 is M8, and Pass 5 is restoration, with no Burden-1 state re-read licensing Burden 2.
*Bad signs:* every "pass" is part of the imported moral tribunal / worship-worthiness criterion test; no burden landing; no state re-read before the next pass heading; route labels substituted for live-burden eligibility.
*Correct behavior in the same case:* `sᵢ != Bᵢ`; keep all operative submoves needed to land Burden 1 inside Burden 1. A burden-cycle begins only after Burden 1 lands, state re-read runs, and the next input-anchored burden is licensed.
*Self-audit question:* Did a burden land before this pass heading, or did I simply rename an operative submove?
*Prevented by:* `recursive-state-transitions.md` live-burden rule; `output-release.md` same-response recursion checklist; `diagnostic-render-contract.md` prohibited render moves.

---

**Operative-Submove Burden Split**
*Definition:* Splitting a single live noetic burden into several burden-cycles because its operative submoves have different names.
*Expected checker violation:* operative submoves split into recursive burden-cycles.
*Pattern appearing in output:* Pass 1 is `imported-criterion tribunal test`, Pass 2 is `hujjah/accountability correction`, and Pass 3 is `guidance-as-coercive-proof correction`, even though all three operations are clearing Burden 1: the imported tribunal judging divine worship-worthiness.
*Bad signs:* the "next pass" is only the next sub-operation required by the same tribunal test; hujjah/accountability corrects the tribunal's accusation rather than opening a new burden; hiddenness correction narrows the same worship-worthiness complaint; state re-read appears between operative submoves instead of after the whole burden landing.
*Correct behavior in the same case:* `Sameτ ∧ SameSourceFrame ∧ SameClaimCluster ∧ ¬NewB -> facets ⊂ {s1...sn} -> ¬RECURSE`. Gloss: use one Burden 1, preserve target -> operation -> result for each `s`, then land the burden and run state re-read. Burden 2 begins only if a genuinely new noetic aspect remains eligible.
*Self-audit question:* Am I crossing into a new live noetic burden, or did I only finish one operative submove inside the same burden?
*Prevented by:* `recursive-state-transitions.md` live-burden boundary rule; `diagnostic-render-contract.md` current bounded operator rule; `output-release.md` Layer A / Layer B release checks.

---

**Burden-Cycle Compression Failure**
*Definition:* A hard output names a complex `B` but renders it as one broad Target/Operation/Result block, then moves to `R`, leaving materially necessary submoves implicit.
*Malformed shape:* `Burden 1: imported tribunal -> Target: imported criterion -> Operation: audit criterion -> Result: criterion changed -> state/noetic re-read`.
*Bad signs:* distinct hidden premises, criteria, predicates, source-status forks, or release gates are mentioned but never rendered as `B1.s1`, `B1.s2`, etc.; `Land(B)` merely restates the broad conclusion; `R(H,Δ)` releases the next burden without showing the cumulative delta produced by submoves.
*Correct behavior in the same case:* Render materially necessary submoves first, then `Land(B)`, then `R(H,Δ)`. A single Target/Operation/Result block is valid only for a genuinely atomic burden.
*Prevented by:* `SKILL.md` execution spine; `diagnostic-render-contract.md` hard-output render-through template; `recursive-state-transitions.md` B-complexity test.

---

**Shallow Live-Burden Execution**
*Definition:* Naming correct TTPs inside a live burden without executing them deeply enough to land the burden.
*Pattern appearing in output:* Hidden premises are listed, M1 is named, DO-8 is mentioned, and M8 consequences are gestured at, but no operative submove preserves target -> operation -> result and no burden landing is stated before state re-read.
*Bad signs:* FPD as enumeration only; M1 self-refutation explained rather than performed; M8 consequences listed without a result; hujjah/accountability correction becomes broad doctrinal presentation; restoration closes the section before the burden landing is known.
*Correct behavior in the same case:* Each TTP inside the live burden has a bounded target, performs its operation, produces a result, and feeds a burden landing. Then run state re-read.
*Self-audit question:* Did the TTP actually change the burden state, or did I merely mention it?
*Prevented by:* `output-release.md` TTP activation rule; `recursive-state-transitions.md` live burden -> operative submove -> burden landing rule.

---

**Deterministic Argument Bank**
*Definition:* Treating the skill as a prewritten answer selector rather than a runtime-verifiable diagnostic compiler.
*Pattern appearing in output:* The response recognizes a topic family, chooses a familiar rebuttal, and delivers a linear argument without reducing the input into validated IR, selecting one current live burden, or refreshing state after the TTP result.
*Bad signs:* topic cue -> argument; no validated IR; no TTP entry criteria; no exit result; no held-route recheck; no STOP / HOLD / RECURSE / PARTIAL decision; every prompt in the same family receives the same answer shape.
*Correct behavior in the same case:* The input reduces into IR, routing precedence selects a burden-level function, the TTP enters with owner-backed target and release permission, the operation produces a result, and state re-read decides whether another same-input burden is eligible.
*Self-audit question:* Did the input compile into governed state, or did I pick a known argument?
*Prevented by:* `diagnostic-ir.md` Runtime Diagnostic Compiler Contract; `routing-precedence.md` TTP entry rule; `recursive-state-transitions.md` TTP entry / exit criteria.

---

**Unguarded TTP Recursion**
*Definition:* Continuing through TTPs without checking entry criteria, exit criteria, or refreshed-state eligibility at each depth.
*Pattern appearing in output:* After one route leg lands, the response proceeds into M8, DO-8, restoration, or pastoral synthesis because those were listed in the initial route read, not because state re-read selected them.
*Bad signs:* downstream TTP inherits eligibility from the initial itinerary; repeated operator with no new bounded target; no burden landing; no depth guard; no concrete HOLD or PARTIAL when release is blocked.
*Correct behavior in the same case:* Each depth increment requires prior burden landing -> state re-read -> next input-anchored live burden -> new bounded operator. If limits block the next eligible burden, mark PARTIAL with the concrete limit; if release signal is absent, HOLD.
*Self-audit question:* Did this next TTP pass entry criteria from refreshed state?
*Prevented by:* `recursive-state-transitions.md` TTP entry / exit criteria and Depth And Stop Guards; `output-release.md` Layer A / Layer B release checks.

---

**Layer A/B Smuggling**
*Definition:* Naming held downstream content in Layer A and then answering it in Layer B before state re-read licenses release.
*Pattern appearing in output:* Layer A lists hiddenness, punishment, worship-worthiness, and criterion import as live burdens; Layer B then answers all of them in one essay while calling the response bounded.
*Bad signs:* held routes are listed but not held; Layer B releases downstream doctrine before active burden landing; state re-read appears after the answer has already unloaded the held material; pastoral synthesis appears before refresh.
*Correct behavior in the same case:* Layer A names live/held material for auditability. Layer B releases only the current bounded operation. state re-read then decides whether the next held route is eligible, held, partial, or stopped.
*Self-audit question:* Did Layer B answer something Layer A marked as held?
*Prevented by:* `output-release.md` Layer A / Layer B release checks; `diagnostic-render-contract.md` Layer A / Layer B release check.

---

**Depth Drift**
*Definition:* Recursive traversal continues or stops based on prose momentum rather than controlled state transitions.
*Pattern appearing in output:* The answer keeps adding sections because more topics are nearby, or it stops because the first move was rhetorically strong, without proving convergence through state re-read.
*Bad signs:* no depth guard; no proof that no eligible same-input live burden remains; no HOLD/PARTIAL reason; repeated TTP at the next depth without refreshed warrant; topic coverage replaces noetic-state progress.
*Correct behavior in the same case:* Depth advances only when a prior burden landing and state re-read license a next input-anchored burden. STOP requires proof of no eligible burden; HOLD and PARTIAL require concrete reasons.
*Self-audit question:* Is the next depth licensed by refreshed state, or by topic momentum?
*Prevented by:* `recursive-state-transitions.md` Depth And Stop Guards; `framework-pipeline.md` generated recursion loop; `output-release.md` governed recursive sufficiency rule.

---

## Route Cosplay Failure

*Definition:* The response names the skill machinery instead of executing it.

*Bad signs:*
- Prints Diagnostic IR as proof of compliance.
- Prints Case State instead of rendering from it.
- Names `Recursion decision: RECURSE` but does not perform state re-read plus one bounded next pass.
- Names M1, M8, M9, or another TTP without target -> operation -> result -> state re-read.
- Uses `matched_modules` as public proof of routing.
- Turns probable module order into an essay itinerary.
- Guesses structure from topic cues such as moral protest, hiddenness, hell, a named source-worldview frame, or secular humanism.
- Applies TTPs only once against the initial case-state, then stops or dumps every detected topic.
- Compresses the default answer to avoid recursion even though eligible same-input burdens remain.

*Correct behavior:*
- IR remains internal in default mode.
- TTP operation is visible through bounded prose.
- Recursion appears as a prose transition and next bounded pass.
- Visible recursion label != recursive traversal; pass-by-pass state re-read = recursive traversal.
- TTPs execute across refreshed case-states, not from an initial essay itinerary.
- Eligible same-input burdens are traversed or marked PARTIAL; future contingencies stay held.
- Length is governed by governed recursive sufficiency, not essay sprawl or compression.
- Module labels may appear briefly only when useful, but labels do not substitute for execution.
- In `:dsl`, a compact pass trace may show live burden, operation, result, refresh, and decision.
- In internal/development audit compatibility, a full pass ledger is allowed.

*Self-audit question:* Am I performing the route, or only naming the route so the answer looks governed?


*Prevented by:* `diagnostic-ir.md` internal-gate rule; `recursive-state-transitions.md` same-response recursion rule; `output-release.md` TTP execution rule; `diagnostic-render-contract.md` default render contract.

---

**Fixed Full-Field Template Materialization**
*Definition:* Printing every section of the full diagnostic template in every response by default — regardless of whether each section is materially needed for the current case — because the template structure has become the practitioner's routine output format.
*Pattern appearing in output:* A simple loaded-term question receives a response with [Case State] (all fields), [Source Basis] (all four lines), [Restoration Trace], [Restorative Response], [Core Formulation], [Engagement Register], [Pastoral/Relational Note], [Post-Render Gate] — all populated, because the practitioner applies Level 3 audit render by default.
*Correct behavior in the same case:* Clear, truth-seeking loaded-term case requiring semantic disaggregation → Level 1 or Level 2 render. Surface only governing fields; reserve the full template for internal/development audit compatibility, pass-review, or explicit diagnostic tasks.
*Self-audit question:* Is each section I am including materially governing this response, or am I filling it in because the template expects it?
*Prevented by:* `references/rubrics/diagnostic-render-contract.md` §Render Levels (Level 3 is not default); `references/rubrics/output-release.md` §9 (rubric is not a mandatory full-field template); `SKILL.md §V` (surfaced-mode policy: ordinary mode compresses inactive fields).

---

**Template-Driven Routing**
*Definition:* Allowing the visible render format or the sections that appear in a template to determine what is diagnosed or routed — substituting a structurally complete template for an actually validated IR.
*Pattern appearing in output:* A response fills in every field of the Level 3 render template, including [Case State], [Matched Modules], and [Source Basis], as part of the response-generation process rather than as the output of a prior validated diagnostic pass. The fields are populated by reasoning backward from the answer — what modules would make this response look well-formed? — rather than forward from the diagnostic pass.
*Correct behavior in the same case:* Diagnostic IR is formed and validated before any render template is populated. The render template is populated from the validated IR, not constructed in parallel with it. If the IR was not formed, the template sections are fabricated rather than derived.
*Self-audit question:* Did my render template sections emerge from a validated IR, or did I construct them alongside writing the answer?
*Prevented by:* `SKILL.md §V` Rule 7 (governance blocks rendered from validated IR, not improvised); `diagnostic-ir.md` §How the IR Prevents Cosmetic Compliance; `references/rubrics/diagnostic-render-contract.md` §Prohibited Render Moves; `framework-pipeline.md` forbidden shortcut: "[IR formed retrospectively] → [counts as gate pass]".

---

**Noetic-Frame Equivalence Stack**
*Definition:* Violating `N_AT`, `N_Ashʿarī[*]`, `N_Māturīdī[*]`, or `σ_context != σ_warrant` discipline by treating rival or family-level frames as peer-valid operative supports in one burden-cycle.
*Pattern appearing in output:* "The whole classical tradition agrees that ...", "multiple school approaches are all classically acceptable theological routes here," or "Atharī, Taymiyyan, Salafī, and Wahhābī aqidah are four independent authorities."
*Bad signs:* `N_AT` aliases counted as separate warrants; contradictory authorities cited side-by-side as one unified support; the operative frame is not identified; verbal agreement is treated as substantive without marking; intra-school disputes are hidden by breadth.
*Correct behavior in the same case:* Select one operative `N`; `N_AT` aliases count once; `N_Ashʿarī[*]` and `N_Māturīdī[*]` require the live predicate/warrant/criterion/authority-order; other frames are only `σ` = contrast / opponent-position / historical note / genealogy / held / bounded comparison. If agreement across frames is asserted, mark substantive vs. verbal/surface-level.
*Self-audit question:* Did I select one operative noetic frame, or did I stack contradictory schools as one authority?
*Prevented by:* `recursive-state-transitions.md` §Source-Status & Noetic-Frame Non-Equivalence Discipline; `routing-precedence.md` Rule S-9 and Rule P-8.

---

**Classical-Theology Umbrella**
*Definition:* Using umbrella terms such as `classical theology`, `classical theologies`, `classical Islamic theology`, `the classical tradition`, `mainstream kalam`, or `Ashari/Maturidi tradition` as if contradictory `N` frames named one operative authority.
*Pattern appearing in output:* "Classical Islamic theologies, including Ashʿarī, Māturīdī, and Taymiyyan approaches, all provide acceptable ways to ground the answer."
*Bad signs:* an umbrella term is asserted as the warrant; contradictory frames are flattened; school-sensitive claims are not marked as disputed; the operative frame is not identified.
*Correct behavior in the same case:* Replace the umbrella with selected operative `N`; if contrast is useful, mark other schools under non-operative `σ` only.
*Self-audit question:* Did the umbrella hide a school-sensitive disagreement?
*Prevented by:* `recursive-state-transitions.md` §Source-Status & Noetic-Frame Non-Equivalence Discipline; `routing-precedence.md` Rule S-9.

---

**Contrast-Source-as-Operative-Support**
*Definition:* Violating `σ != operative warrant` by naming a source under non-operative status (`contrast`, `opponent-position`, `historical note`, `genealogy`, `held material`) and then using it as operative warrant in the same burden-cycle without explicit reclassification.
*Pattern appearing in output:* "Source-status: contrast only. A rival formulation is mentioned only as contrast. Therefore, the operative answer is established by that contrast source together with the selected frame."
*Bad signs:* the same source carries two statuses in one burden-cycle; reclassification is not justified; the operative conclusion depends on the contrast source.
*Correct behavior in the same case:* Keep the source in non-operative `σ`, or reclassify explicitly with a named reason and a sentence preserving the selected operative frame.
*Self-audit question:* Did I name a source as contrast and then use it as warrant in the same burden-cycle?
*Prevented by:* `recursive-state-transitions.md` §Source-Status & Noetic-Frame Non-Equivalence Discipline; `routing-precedence.md` Rule P-8.

---

**Intra-School Flattening**
*Definition:* Treating a named school (Ashʿarī, Māturīdī, Atharī, Taymiyyan, falsafah) as internally uniform on a claim that is internally disputed within the school or school-sensitive across schools, without marking the claim as disputed.
*Pattern appearing in output:* "Ashʿarī theology teaches X" or "Māturīdī theology teaches X" stated as settled when the claim is internally contested.
*Bad signs:* a school is named as one voice on a disputed claim; internal disagreement is hidden; the claim is school-sensitive but presented as uniformly held.
*Correct behavior in the same case:* Mark the claim as disputed within the school, or identify which strand within the school holds it, or use the claim only under contrast / historical-note status.
*Self-audit question:* Is this a settled school position, or am I flattening intra-school disagreement?
*Prevented by:* `recursive-state-transitions.md` §Source-Status & Noetic-Frame Non-Equivalence Discipline; `routing-precedence.md` Rule S-9.

---

**Verbal-Agreement Smuggling**
*Definition:* Asserting agreement across contradictory `N` frames without marking substantive vs. verbal/surface-level agreement, then using the asserted agreement as operative support.
*Pattern appearing in output:* "All schools agree that God is one" used as the operative warrant when the agreement is verbal but the operative grounding (tawḥīd al-rubūbiyyah / tawḥīd al-asmāʾ wa-l-ṣifāt / tawḥīd al-ulūhiyyah, or kalām nafsī vs. ḥudūth/khalq formulations) differs across frames.
*Bad signs:* shared vocabulary is treated as shared warrant; the difference in operative grounding is not stated; the asserted agreement carries the conclusion.
*Correct behavior in the same case:* Mark agreement as substantive or verbal; if verbal, do not use it as operative support. State the operative warrant inside selected `N`.
*Self-audit question:* Is the agreement I am citing substantive across frames, or only a coincidence of words?
*Prevented by:* `recursive-state-transitions.md` §Source-Status & Noetic-Frame Non-Equivalence Discipline.

---

**Ungrounded Noetic Re-Read**
*Definition:* Printing `R` without grounded `Land(B)`: a `Noetic re-read` block whose `burden landed` lacks an immediately preceding `target -> operation -> result`, or whose `still live` / `next licensed live burden` is not anchored in original input, prior held material, or the preceding burden-cycle.
*Pattern appearing in output:* "Noetic re-read: burden landed: yes; still live: hiddenness, punishment; held: none; recursion decision: continue; next licensed live burden: hiddenness." — appearing after a Layer B that merely asserts "The tribunal has been addressed" without an operative submove.
*Bad signs:* `burden landed: yes` follows no operative result; `still live` introduces material not present in the input or held; `next licensed live burden` appears from nowhere; a new burden-cycle begins from a re-read block alone.
*Correct behavior in the same case:* `B -> {s1...sn} -> Land(B) -> R(H,Δ)`. Gloss: produce burden landing through auditable `s`; anchor `still live` in original input, prior held material, or collapse radius; anchor `next licensed live burden` in `still live` or held material.
*Self-audit question:* Does my noetic re-read block's `burden landed` trace to an actual operation, or did I print the shape and call it grounded?
*Prevented by:* `recursive-state-transitions.md` §Grounded Noetic Re-Read Shape (field-grounding rules 1–6).

---

## Quick Self-Audit

- Have I diagnosed before rebutting?
- Am I using a term because it distinguishes, or because it sounds weighty?
- Am I forcing this case into a preferred module?
- Is the discourse orientation established or only guessed?
- Have I preserved restoration over rhetorical win?
- Have I marked where inference begins?
- If this is a conversation excerpt, have I confirmed multiple convergent signals before assigning a confident NS code?
- Did I confirm the concealment × orientation matrix cell shows the register is open before loading any content module?
- Does this case carry a live epistemic question, and if so have I deployed the matched content module before loading any restoration frame?
- If I used higher-order vocabulary, did I distinguish burden, pattern, and restoration target rather than just naming them?
- If I used a structural pattern print, did it change routing, hold/release, or the next bounded move?
- Am I using a background topic as an answer bank instead of as framing intelligence?
- Did I route by tradition label, or did I identify the live structural node first?
- Did I separate an abuse or authority wound from a doctrinal or tribunal claim?
- Am I continuing because the state actually refreshed, or because I do not want to leave a landed move alone?
- Did I run the post-render gate before STOP, recheck held routes, and name the next eligible pass or `none`?
- For each entry in `matched_modules`, does a `source_basis` entry with `source_kind: module` name what it governed?
- Am I invoking transcendence or bilā kayf because the specific analytical work is done, or as a substitute for it?
- Did I say something was held and then answer it anyway under a different label?
- After the governing blocker cleared, did I reassess held downstream material or treat it as permanently suppressed?
- Am I waiting for a user reply when internal state re-read already permits the next bounded pass?
- Am I releasing all detected downstream burdens at once, or moving burden-cycle by burden-cycle with state re-read between each?
- Am I printing a full audit template when the case only requires a compact or ordinary response?
- Did diagnostic reduction finish before I formed any route itinerary?
- Is the current bounded operator one burden-level function, not a route chain?
- Are the numbered passes true post-refresh burdens, or merely operative submoves?
- Did I split imported criterion, hujjah/accountability, and hiddenness-frame correction into
  fake recursive burden-cycles when they are all serving the same tribunal burden?
- Did each TTP inside the active burden preserve target -> operation -> result before burden landing and state re-read?
- Did this input compile into validated IR, or did I select a deterministic argument-bank answer?
- Did every TTP pass entry criteria and exit criteria before the next depth?
- Did Layer B answer anything Layer A marked as held?
- Is recursion depth licensed by state re-read, or by prose momentum?
- Did I select one operative noetic frame, or did I stack contradictory schools as one authority?
- Is any source carrying two source-status labels in this burden-cycle without explicit reclassification?
- Does my noetic re-read block trace `burden landed` to an actual operative submove `target -> operation -> result`?
