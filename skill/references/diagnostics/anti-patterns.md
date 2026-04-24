# Anti-Patterns

> role: self-audit
> use when: preparing, reviewing, or correcting a response path
> do not use when: the case is trivial and no diagnostic routing is being performed
> output: compact checks against misuse, forced fit, and rhetorical drift

## Core Anti-Patterns

The following entries expand the compressed table into full audit-grade entries. Each entry gives a one-line definition, a concrete positive example (the pattern appearing in output), a concrete negative example (correct behavior in the same case), and a self-audit question.

---

**Forced Fit**
*Definition:* Pushing an unfamiliar or mixed case into a familiar module because the module is ready to hand, rather than because the case has been confirmed as the module's proper domain.
*Pattern appearing in output:* An interlocutor makes one off-hand remark about evolution; the response immediately deploys NS-1 full profile and V2 as though naturalism were confirmed as the governing noetic structure.
*Correct behavior in the same case:* Mark the read provisional. Answer the specific claim made. State that NS-1 is a candidate but has not been confirmed; note what additional signals would confirm it.
*Self-audit question:* Have I confirmed the case family by multiple convergent signals, or did I choose this module because it is the first plausible match?
*Why it damages the skill:* Forced fit addresses the wrong case. The person receives a response optimized for a profile that is not theirs — correct in form, wrong in substance. The practitioner has the subjective experience of having engaged; the interlocutor has the experience of not being heard. The routing architecture exists precisely to prevent this: bypassing it with a plausible-first match converts the skill into a pattern-matching shortcut.
*Prevented by:* `V1-diagnostic.md` (full diagnostic pass before module selection); `noetic-reading-checklist.md` (multiple-convergent-signal requirement before NS code is assigned); `mixed-case-handling.md` (provisional status requirement when signals are thin).

---

**Recursive Overfitting**
*Definition:* Re-running the full diagnostic pass after every exchange move, even when no new differentiator has appeared, generating a cascade of diagnoses that substitutes for a clear intervention sequence.
*Pattern appearing in output:* After each exchange turn, a new case-state line is generated with slight revisions to the NS code and deformation read, none of which change the next move or the module selection.
*Correct behavior in the same case:* Re-run V1 and update the case-state only when a move has cleared an upstream barrier, the interlocutor has shifted register, or a new objection family has appeared. Otherwise hold the current read and proceed with the current module.
*Self-audit question:* What specifically changed that justifies a new diagnostic pass — has intervention order actually shifted?
*Why it damages the skill:* Each rediagnosis pass that changes nothing operationally replaces action with procedure. The engagement becomes a diagnostic exercise rather than a restorative one. The interlocutor experiences a practitioner who is elaborately analyzing rather than genuinely present. This is a form of gharaḍ in the practitioner — the diagnostic apparatus is being operated for its own sake rather than in service of restoration.
*Prevented by:* `mixed-case-handling.md` §Recursive Reassessment (reassess only when a move has cleared an upstream barrier or a new differentiator has appeared); `heuristics.md` rule 28 (case-state-justified coordination); the case-state schema's `Reassessment` field (should say "not warranted" unless conditions met).

---

**Cumulative Inflation**
*Definition:* Adding supporting modules, routes, and argument tracks beyond the case-state-justified coordination that still governs the case, inflating response weight without adding productive leverage.
*Pattern appearing in output:* V2 has been deployed but the framework has not yet visibly loosened; the response then also loads E1, E3, V6, and M3, adding convergent evidential content before the filter through which it will be evaluated has been changed.
*Correct behavior in the same case:* Deploy only V2. Wait for a differentiating signal before escalating. Escalate to E3 or V6 only when no single blocker still dominates and multiple routes add genuinely non-redundant warrant.
*Self-audit question:* Is the upstream blocker genuinely cleared, or am I loading additional modules into an unreconstituted filter?
*Why it damages the skill:* Every module loaded into an unreconstituted filter is absorbed through that filter and found wanting — which reinforces the filter's authority. The interlocutor's implicit conclusion after each failed argument is that the evidence confirms their criterion. Cumulative inflation therefore makes subsequent V2 application harder: the criterion has been reinforced by the failed attempts, not loosened.
*Prevented by:* `mixed-case-handling.md` §Cumulative-Case Escalation (escalate only when no single upstream blocker dominates); `anti-patterns.md` (self-referentially: Cumulative Inflation IS this anti-pattern — the check against it is the upstream-blocker-still-dominant question); SKILL.md Named Routing Constraint 3 (no content before register is cleared).

---

**False Landing / Premature Continuation**
*Definition:* Treating politeness, surprise, or a local concession as permission to keep chaining, instead of stopping the current pass and waiting for a refreshed-state basis.
*Pattern appearing in output:* After one consequence lands, the response immediately adds a second consequence, a positive reconstruction, and a reserve-route preview because the interlocutor said "I can see that." Or the response treats a new sentence in the same message as automatic permission to continue without testing whether it is actually a differentiating signal that reopens V1.
*Correct behavior in the same case:* Type the recognition strength, stop the current pass, and reassess. Continue only if a fresh differentiating signal has reopened V1, the restoration target remains unmet, and no stop, register-hold, or semantic gate remains live for the next move. Medium or strong recognition may justify a pause; weak signals do not license either celebration or renewed pressure.
*Self-audit question:* Am I continuing because the state actually refreshed, or because I do not want to leave a landed move alone?
*Why it damages the skill:* It turns selective recursion into debate momentum. The practitioner mistakes movement for permission and converts restoration into chain-dumping. This is precisely how a selective state machine decays into a sophisticated answer bank: the live state stops governing once the first move feels successful.
*Prevented by:* `framework-pipeline.md §Recursive State-Transition View` (canonical owner of the STOP / PAUSE / RECURSE state model and recursive re-entry conditions); `P7-restoration-stops.md` Stop 2 (one-live-question stop and recognition ladder); `diagnostic-ir.md` acceptance-state fields (`alignment_state`, `recognition_strength`, `continuation_eligibility`); `routing-precedence.md` Rule P-3 (boundary reset); `heuristics.md` rule 17 (pause and refresh before further release).

---

**Inference Laundering**
*Definition:* Presenting a model-level synthesis or inference as if it were directly anchored in a loaded file, without marking the extension.
*Pattern appearing in output:* A response claims "the position on X is Y" where the loaded file only implies this through multi-step inference; the claim appears without an `[inference]` or `[synthesis]` marker.
*Correct behavior in the same case:* Mark the claim `[inference]` or `[synthesis]` and name the files being combined or the inferential step being made. Use `[anchored]` only for claims directly stated in the loaded file.
*Self-audit question:* Is this claim directly stated in the loaded file, or am I extending it — and have I marked the extension?
*Why it damages the skill:* Inference laundering corrupts the audit trail. The reader cannot distinguish what the skill actually says from what the model is adding on the skill's behalf. Over time, inference laundering expands the skill's apparent positions beyond what its files actually support, and the expanded positions cannot be audited or corrected because they are not clearly attributed. The inference-boundary discipline exists to prevent exactly this.
*Prevented by:* `inference-boundary.md` §Mandatory Pre-Release Check (every claim extending beyond loaded files must be marked); `case-state-schema.md` §Source Basis block (`[Source Basis]` forces explicit annotation of anchored vs. synthesized vs. inferred); `heuristics.md` rule 30 (mark where inference begins).

---

**Decorative Terminology**
*Definition:* Using Arabic or technical terms because they add scholarly register, not because they change routing, scope, or doctrinal precision in the current case.
*Pattern appearing in output:* A response to a simple evidentialist question loads iʿtiqādāt mawrūtha, ẓann, mushābara fāsida, and muʿānada all within one paragraph, where a single "the criterion itself is unexamined" would have done the routing work.
*Correct behavior in the same case:* Introduce a technical term only when it changes what move is required or when the concept it names is operationally distinct from what plain English would convey.
*Self-audit question:* Does this term change the routing or the doctrinal precision, or is it adding prestige to a point that plain language would state more clearly?
*Why it damages the skill:* Decorative terminology signals erudition while reducing precision. The interlocutor encounters a response that is harder to engage because the governing point is obscured under technical vocabulary. In the practitioner, it is a form of gharaḍ — using the skill's register for identity-presentation rather than for the interlocutor's benefit.
*Prevented by:* `heuristics.md` rule 15 (prefer simplicity; the sharpest move over the most elaborate); `seven-deformations.md` §Gharaḍ (vested interest applies to practitioners too — the vested interest here is scholarly self-presentation); `case-state-schema.md` §Compression Rule (surface only fields that improve governance, not transparency theater).

---

**Higher-Order Vocabulary Theater**
*Definition:* Naming a case `meta-epistemic`, `meta-noetic`, `memetic`, or `PF-x` without distinguishing the actual higher-order burden, the deformation pattern, and the restoration target that routing must clear.
*Pattern appearing in output:* "This is a meta-noetic PF-2 / PF-12 problem" is announced, but the response never says whether the live pressure is criterion-import, naturalist filtering, aversion, or a blocked testimony-order question, and never types the restoration target beyond "respond to the framework."
*Correct behavior in the same case:* State the first-order claim if there is one, name the higher-order burden precisely, name the deformation or noetic pattern separately, and state the restoration target in the architecture's own grammar. Example: "First-order claim: revelation is under attack. Higher-order burden: meta-epistemic criterion import. Pattern: PF-2 inherited evidential pressure. Restoration target: sound reason / authentic-transmission order. So V2 or V10 clears first."
*Self-audit question:* If I used higher-order vocabulary, have I said what it changes in routing and what layer is being restored, or did I only name the vocabulary?
*Why it damages the skill:* It makes the architecture sound sophisticated while hiding the actual work. The interlocutor hears labels; the operator never commits to whether the burden is about content, criterion, category, noetic condition, or the restoration layer. Higher-order language is then used as prestige-register compression rather than as auditable routing discipline.
*Prevented by:* `pattern-profiling.md` (claim-level and PF discipline), `noetic-reading-checklist.md` (higher-order assessment -> restoration hand-off), `case-state-schema.md` and `diagnostic-ir.md` (restoration-target typing), `heuristics.md` rule 29 (keep burden, pattern, and target distinct).

---

**Tactic Over-Selection**
*Definition:* Loading many modules because several seem relevant to the topic, rather than selecting the case-state-justified coordination that changes the next differentiator.
*Pattern appearing in output:* A response to a single hiddenness objection loads V1, M5, DO-1, P2, P4, M2, M3, and F2 in sequence, providing the full apparatus when a single well-placed M2 or the grief-register check would have changed the next live issue.
*Correct behavior in the same case:* Identify the one or two modules that address the current live differentiator. Defer everything else until the first move has been made and a new differentiator appears.
*Self-audit question:* Is each module in this response changing the next live differentiator, or am I loading it because it might be relevant?
*Why it damages the skill:* Module proliferation masks the actual diagnostic precision the skill is designed to produce. A response advertising nine modules suggests the practitioner does not know which coordination is actually needed. More practically: every additional module is a new surface for the interlocutor to deflect to, multiplying the number of available exits from the main engagement. The case-state-justified coordination is also the hardest to deflect.
*Prevented by:* `heuristics.md` rule 28 (case-state-justified coordination); `mixed-case-handling.md` §Stopping Conditions (stop when next module would only restate the same point); `case-state-schema.md` §Matched modules field (list only the current-pass coordination — do not advertise unused modules); SKILL.md Named Routing Constraint 5 (no argument-stacking after landed move).

---

**Rhetorical Overreach**
*Definition:* Attributing motive, concealment mode, or discourse orientation to the interlocutor without sufficient evidential basis, presenting inference as diagnosis.
*Pattern appearing in output:* From a single sentence expressing frustration with a ruling, the response concludes "this is juḥūd combined with gharaḍ" and names the interlocutor's resistance as culpable denial.
*Correct behavior in the same case:* Mark the read provisional. State what signals would confirm or disconfirm the candidate mode. Respond to the established claim-type only; do not name a concealment mode without multiple convergent signals.
*Self-audit question:* Do I have multiple convergent signals supporting this characterization, or am I extrapolating from a single data point?
*Why it damages the skill:* Naming a concealment mode without evidential basis is itself a form of the juḥūd diagnosis applied without warrant — the practitioner has attributed culpable resistance where it is not confirmed. This harms the engagement directly (the interlocutor experiences a misjudgment) and corrupts the practitioner's subsequent reads (subsequent moves are now calibrated to a mode that was never confirmed).
*Prevented by:* `modes-of-concealment.md` (iʿrāḍ vs. juḥūd boundary and juḥūd vs. inkār boundary require multiple convergent signals); `mixed-case-handling.md` §Insufficient-Basis Conditions (do not claim a settled read of concealment mode when evidence is thin); `heuristics.md` rule 5 (distinguish register before naming a mode); SKILL.md Named Routing Constraint 4 (no confident family-lock from thin basis).

---

**Diagnosis Collapse**
*Definition:* Replying to the surface content of a question before classifying the noetic structure, deformation, and discourse orientation — skipping V1 and loading content that may be addressed to the wrong register.
*Pattern appearing in output:* An interlocutor asks about theodicy and the response immediately deploys DO-2 probabilistic analysis without checking whether the presenting register is grief (M4) or intellectual (shubhah), and without establishing that the discourse orientation is truth-seeking.
*Correct behavior in the same case:* Run V1 first. Identify the claim-type, the concealment mode, the deformation, and the discourse orientation before selecting any content module. Diagnose before rebutting.
*Self-audit question:* Have I run V1 and confirmed the noetic structure, deformation, and discourse orientation before loading content?
*Why it damages the skill:* Content deployed without diagnostic routing is calibrated to the wrong register by default. The skill's discriminating power — its ability to send different responses to different cases — is entirely dependent on the diagnostic gate. Bypassing V1 collapses all cases into the one the practitioner expects, converting a precision instrument into a generic apologetics dispatcher.
*Prevented by:* `V1-diagnostic.md` (the diagnostic gate itself); SKILL.md Named Routing Constraint 1 (no content module before V1 has been run); `heuristics.md` rule 2 (start with V1); `framework-pipeline.md` (forbidden shortcut path: intake → direct doctrinal rebuttal).

---

**Excerpt Over-Read**
*Definition:* Assigning a confident NS code, deformation type, or concealment mode from a conversation excerpt that is too thin to support the assignment — without marking the read provisional or naming what differentiating signal would resolve the ambiguity.
*Pattern appearing in output:* A three-sentence excerpt in which someone asks "isn't it arrogant to think your religion is right?" is diagnosed as NS-5 (habituated atheist) with primary deformation hawā and concealment mode istikbār. A confident [Diagnostic IR] block is emitted and the matched modules are loaded.
*Correct behavior in the same case:* Mark read status as `underdetermined`. List the competing NS candidates (NS-5, NS-2, or possibly NS-4). Answer the specific claim made — the arrogance charge — without assigning a governing read to the whole case. State: "Differentiating signal: whether this is a held position (NS-5 candidate), a principled criterion objection (NS-2 candidate), or a moral-parity argument (NS-4 candidate) — cannot be distinguished from this excerpt alone."
*Self-audit question:* Is my NS/deformation/concealment diagnosis supported by multiple convergent signals from this excerpt, or by the most plausible surface reading of a single sentence?
*Why it damages the skill:* An excerpt-mode over-read produces a response optimized for a wrongly diagnosed profile. The person receives a response precisely calibrated to a noetic structure they may not have. Because excerpts are often culled for review rather than produced in live dialogue, the practitioner has no feedback loop to correct the wrong diagnosis. Each module loaded on the wrong diagnosis reinforces the wrong treatment frame.
*Prevented by:* `P7-restoration-stops.md` Stop 4 (underdetermined-case stop — "do not assign a deformation or concealment code without sufficient signal"); `mixed-case-handling.md` §Insufficient-Basis Conditions; `noetic-reading-checklist.md` multiple-convergent-signal requirement; SKILL.md Named Routing Constraint 4 ("no confident family-lock from thin basis").

---

**Register-Hold Bypass**
*Definition:* Deploying a matched content module when the concealment × orientation matrix in `case-state-schema.md` specifies that the current register requires a hold — loading doctrinal or case-library content into a cell that says "relational only," "held pending register shift," or equivalent.
*Pattern appearing in output:* Concealment is confirmed as iʿrāḍ (aversion) and discourse orientation is identity-performance. The matrix cell for this pair says "Iʿrāḍ compounded by identity performance hardens under argument. Relational only; no doctrinal module." The response nonetheless loads DO-1 (divine hiddenness rebuttal) and deploys probabilistic analysis of sincere non-belief.
*Correct behavior in the same case:* Confirm the matrix cell before loading any content module. When the cell specifies relational-only, invitational, or character-as-evidence: deploy exactly that. Include in the case-state: "Register-hold: iʿrāḍ + identity-performance. Deployable on shift to: truth-seek orientation or concealment clearing." Hold the matched DO module until the register shifts.
*Self-audit question:* Did I check the concealment × orientation matrix cell before loading any content module? Does the cell I confirmed permit full apparatus deployment, or does it specify a hold?
*Why it damages the skill:* Content deployed into a register-hold cell is filtered through the very barrier the register-hold exists to address. iʿrāḍ + identity-performance hardens under argument specifically because argument is experienced as pressure, and pressure reinforces the aversion-identity compound. Every argument deployed into this cell is metabolized as further confirmation of the interlocutor's identity position — the skill's precision is converted into a precision instrument for reinforcing the barrier.
*Prevented by:* `case-state-schema.md` §Concealment × Orientation Routing Matrix (explicit cell-level rules); `diagnostic-ir.md` Gate Check 6 ("confirm the concealment × orientation matrix cell shows content is deployable now"); SKILL.md Named Routing Constraint 3 ("no content-before-register"); `P7-restoration-stops.md` Stop 1 (Content-Withholding Stop — the hard-rail version of the same constraint).

---

**Restoration-First Default**
*Definition:* Loading P1 (fiṭrah-restoration) or P4 (maieutic) as the opening move when the case carries a live epistemic question — evidentialist demand, canon or authority confusion, doctrinal complexity structured as argument — that requires the matched content module before any restoration framing.
*Pattern appearing in output:* An interlocutor with an inherited-tradition background asks "which Bible is authoritative, and how would anyone know?" The response immediately frames the question as a fiṭrah-recognition opportunity, invites reflection on creation, and omits the canon-authority analysis the interlocutor actually asked about. Or: an interlocutor with an evidentialist criterion objection receives P4 maieutic prompts about inner recognition before V2 has loosened the criterion that is doing the governing work.
*Correct behavior in the same case:* Run V1 and foreign-premise detection (FPD). Identify the live epistemic question and the matched content module. Deploy the matched module first — DO-14 for canon-selection, DO-10 for ḍarūrī criterion attacks, V2 for inherited evidentialist criteria, V10 for transmission pressure. Restoration framing may accompany the engagement later (once the epistemic question has been met) but never substitutes for the matched module.
*Self-audit question:* Does this case carry a live epistemic question (evidentialist demand, canon/authority confusion, doctrinal-complexity-as-argument), and if so have I deployed the matched content module before loading any restoration frame?
*Why it damages the skill:* Defaulting to restoration when argument is required produces a preachy or exhortatory response that leaves the interlocutor's actual question unanswered. The practitioner has the subjective experience of having offered something gentle and principled; the interlocutor experiences being addressed at a register they did not ask for and not at the one they did. Across repeated cases, this converts the skill's epistemic-comparative architecture into an invitational register — the specific regression `mixed-case-handling.md` playbook (v) was written to prevent. Generalized, this anti-pattern protects cases beyond playbook (v) (including NS-3, NS-11, and NS-12 profiles) where the localized playbook guard does not fire.
*Prevented by:* `mixed-case-handling.md` Playbook (v) §Critical correction to the "restoration-first" failure mode (the localized correction this anti-pattern generalizes); `P7-restoration-stops.md` Stop 1 (Content-Withholding Stop — the inverse guard, preventing content when register requires hold; restoration-first is the other-direction failure, preventing content when content is what is required); `kernel-thesis.md` Commitment 4 (restoration works through matched content, not around it); `heuristics.md` rule 12 exception clause (restoration framing supports but does not substitute epistemic content when epistemic demand is present); SKILL.md Named Routing Constraint 1 (no content module before V1 has been run — the read from V1 is what separates restoration-need from epistemic-need).

---

---

**Semantic Gate Bypass**
*Definition:* Releasing doctrinal or attribute content while an upstream semantic blocker is still live - recontented prophetic discourse, evacuated prophetic discourse, or an unresolved loaded negative theological term.
*Pattern appearing in output:* The response answers "God is not a body" or "bilā kayf solves it" before clarifying what "body," "direction," "composition," or the prophetic-language claim is actually being made to mean.
*Correct behavior in the same case:* Clear the semantic blocker first. If prophetic discourse is being redirected or evacuated, run the prophetic-discourse-neutralization pass. If the case is built on loaded anti-attribute vocabulary, run M9's lexical-ontological split before doctrinal release.
*Self-audit question:* Have I restored meaning before releasing doctrine, or did I answer a semantically unstable question as if it were already well formed?
*Why it damages the skill:* It lets the objectioner's hidden semantics govern the exchange. The practitioner appears to answer the claim while actually accepting the opponent's terms, so the same semantic trap simply regenerates downstream objections.
*Prevented by:* `prophetic-discourse-neutralization.md`; `M9-predication-mode.md`; `routing-precedence.md` Rule S-6; `diagnostic-ir.md` semantic-discipline gate.

---

**Ghost-Load**
*Definition:* Listing a module in `matched_modules` and loading its governing file, but writing output that does not demonstrably use that file — no `source_basis` entry with `source_kind: "module"` links any output claim or routing decision back to it.
*Pattern appearing in output:* A DO-12 case loads M9-predication-mode.md and lists M9 in `matched_modules`, but the `[Source Basis]` block contains no entry with `source_kind: module, module_id: M9`. The predication analysis in the response is plausible and consistent with M9 but is not traceable to it.
*Correct behavior in the same case:* After loading M9, record at least one `source_basis` entry: `source_kind: "module"`, `module_id: "M9"`, `basis_type: "anchored"` or `"inference"`, and `claim` naming the specific output claim or routing fork M9 governed. If M9 governed only a routing decision (e.g., "run count-noun analysis before Trinitarian overlay"), name that decision as the claim.
*Self-audit question:* For each entry in `matched_modules`, does a `source_basis` entry with `source_kind: module` and matching `module_id` exist? If not, either add it or move the module to `What is withheld and why`.
*Why it damages the skill:* Ghost-loading makes the activation record unfalsifiable. A module appears active but leaves no audit trail; the load-floor patch (Rule 13) enforced that files are loaded, but ghost-loading defeats that guarantee by leaving no evidence the loading constrained the output. Over many passes, `matched_modules` becomes a plausible-sounding decoration rather than a governance record. The practitioner can list a module to appear thorough while writing output that ignores its governing constraints — inverting the purpose of case-state-justified coordination.
*Prevented by:* `SKILL.md` Rule 14 (source_basis entry required for every matched_modules entry); `diagnostic-ir.md` §Current-pass activation rule ghost-load prohibition bullet; `diagnostic-ir.schema.json` §source_basis allOf constraint (module_id required when source_kind is "module").

---

**Transcendence Default / Abstraction-as-Cure**
*Definition:* Responding to a specific attribute, coherence, or predication objection by invoking divine transcendence, bilā kayf, or mystery language as the primary move — before the semantic splitting, predication-mode analysis, and analytical distinction work the objection actually requires.
*Pattern appearing in output:* An interlocutor asks whether God's knowledge of particulars implies dependence on them. The response deploys bilā kayf and transcendence language immediately without first running M9 on the loaded term "dependence," distinguishing ontological from logical dependence, or engaging the composition / dependence distinction the objection requires. The interlocutor's specific confusion is unaddressed; the same objection regenerates downstream.
*Correct behavior in the same case:* Run M9 on the loaded term first. Distinguish ontological dependence (implying incompleteness) from logical distinction (not implying dependence). After the specific analytical work is done, bilā kayf may anchor the result — as a genuine doctrinal anchor after the problem is identified, not as a shortcut around identifying it.
*Self-audit question:* Am I deploying transcendence or bilā kayf because the specific analytical work has been completed and this is its honest conclusion, or am I using it to bypass the work the objection actually requires?
*Why it damages the skill:* Transcendence-as-default appears to honor divine greatness while leaving the specific confusion intact. The interlocutor's objection regenerates because its underlying predication structure was never examined. Repeated use trains the practitioner to treat bilā kayf as an escape hatch, inverting its function: V8-bilā kayf is an anchor for a claim after its predication has been stabilized, not a response to a question whose predication structure is unexamined. The do-attribute-precision.md route order (M9 → definition-discipline → attribute-precision → V8) exists precisely to prevent this premature deployment.
*Prevented by:* `V8-bila-kayf-anchor.md` (bilā kayf anchors after semantic and predication work, not instead of it); `M9-predication-mode.md` Function 4 (semantic split required before yes/no answer on a loaded term); `do-attribute-precision.md` §Three-Layer Owner Distinction (route order M9 → definition-discipline → attribute-precision → V8); `routing-precedence.md` Rule S-6 (semantic gate must clear before doctrinal release).

---

**Held-but-Answered Contradiction**
*Definition:* Declaring that a downstream issue is held by register, semantic, or stop governance, then effectively answering it in the same pass under a different heading or as part of the "bounded answer."
*Pattern appearing in output:* A response states "composition/dependence pressure governs first; downstream coherence question is held." The response then proceeds to answer whether the doctrine is coherent in the [Restorative Response] section, under the label "preliminary clarification."
*Correct behavior in the same case:* If composition/dependence governs first, the coherence answer stays held. It may be named as downstream but not answered. After the governing move clears, refresh state; if the coherence question remains live, it becomes the next bounded pass.
*Self-audit question:* Did I name something as held and then answer it under a different label in the same pass?
*Why it damages the skill:* It defeats hold discipline entirely while appearing to respect it. The interlocutor receives the downstream content without the upstream clearing that makes it meaningful, and the routing trace becomes fraudulent: held is recorded but not respected.
*Prevented by:* `references/rubrics/output-release.md` §4 (held material actually held); `routing-precedence.md` Rule P-1 (upstream-blocker priority); `SKILL.md` Rule 8 (no held-as-never-answer — but also no held-while-answering).

---

**Held-as-Never-Answer**
*Definition:* Treating a hold at the current traversal point as permanent suppression — never reassessing the held material after the governing blocker is cleared, and never releasing it even when the refreshed case-state would permit it.
*Pattern appearing in output:* Upstream blocker X is addressed. The response ends. Downstream material Y was correctly held during X's pass, but no reassessment is performed. If the interlocutor asks Y directly, the response still treats Y as held without checking whether X's clearing removed the basis for the hold.
*Correct behavior in the same case:* After X clears, refresh state. If Y remains live and no stop, register-hold, or semantic gate now blocks it, release the bounded Y move. If Y no longer governs (because X's clearing dissolved it), compress or drop it explicitly.
*Self-audit question:* Is any material I am holding still actually blocked by a live gate, or am I continuing to hold it by inertia after the governing blocker was cleared?
*Why it damages the skill:* It converts the holding discipline into a content-suppression mechanism. The interlocutor is denied downstream content that is now legitimately releasable, and the practitioner treats "held" as equivalent to "forbidden" rather than "traversal-delayed."
*Prevented by:* `references/rubrics/output-release.md` §4 (held material reassessed after refresh); `P7-restoration-stops.md` (stops govern current pass, not all future passes); `framework-pipeline.md §Recursive State-Transition View` (RECURSE is licensed after refresh when target remains unmet).

---

**State-Refresh-as-User-Reply-Only**
*Definition:* Treating state refresh as an operation that can only happen when the interlocutor sends a new message — never allowing same-response recursion even when the current pass itself has cleared the governing blocker and the next live burden is now visible.
*Pattern appearing in output:* An imported tribunal is named and refused within the response. The response correctly identifies that the downstream positive reconstruction is now eligible, but says "I will address this in my next reply after you respond." The interlocutor's next message only repeats the question; no new signal was needed.
*Correct behavior in the same case:* Tribunal refusal clears the upstream blocker. Refresh state internally. If the downstream reconstruction remains live and no stop/hold/gate blocks it, release the bounded next move within the same response. Do not manufacture a dependency on a new user turn.
*Self-audit question:* Am I waiting for a user reply because a stop, register-hold, or semantic gate genuinely requires one — or because I am modeling refresh as only conversational turn-taking?
*Why it damages the skill:* It introduces artificial latency into restoration. Cases where one response could complete a full restoration sequence are fractured into multiple turns, each requiring the interlocutor to re-engage. This is a form of false passivity that can feel like epistemic caution while actually suppressing legitimate continuation.
*Prevented by:* `references/rubrics/output-release.md` §7 (same-response recursion bounded but permitted); `SKILL.md` Rule 15 (state refresh may occur inside the same response); `P7-restoration-stops.md` (stops govern deployment; not requiring external reply before every bounded next move).

---

**Recursive Dump**
*Definition:* Treating the permission for governed recursive traversal as license to release every downstream burden, argument, and module at the moment of a single state refresh — answering all detected issues simultaneously without ordered traversal.
*Pattern appearing in output:* An interlocutor asks about divine direction. A loaded spatial term governs. It is cleared. The response then immediately releases: attribute content, composition analysis, bilā kayf anchor, philosophical-usurpation framing, and a cosmological argument — because all were detected as downstream during the initial diagnostic pass.
*Correct behavior in the same case:* Clear the loaded spatial term. Refresh state. Identify whether composition/dependence pressure remains live and now governs. If yes, release only that bounded move. Refresh again. Each door is opened in order, not simultaneously.
*Self-audit question:* Am I releasing all detected downstream items at once, or am I moving door-by-door with a state refresh before each release?
*Why it damages the skill:* It converts governed recursion into an argument dump. The interlocutor receives a treatise when they asked a question. The successive-door discipline — the primary virtue of the recursive state model — is lost. Same-response recursion is permitted only as a bounded next pass, not as total downstream release.
*Prevented by:* `references/rubrics/output-release.md` §5 (recursive traversal discipline: 7-step ordered process); `framework-pipeline.md §Recursive State-Transition View` (RECURSE is governed re-entry, not autonomous looping); `P7-restoration-stops.md` Stop 2 (boundary reset after landing).

---

**Fixed Full-Field Template Materialization**
*Definition:* Printing every section of the full diagnostic template in every response by default — regardless of whether each section is materially needed for the current case — because the template structure has become the practitioner's routine output format.
*Pattern appearing in output:* A simple loaded-term question receives a response with [Case State] (all fields), [Source Basis] (all four lines), [Restoration Trace], [Restorative Response], [Core Formulation], [Engagement Register], [Pastoral/Relational Note], [Refresh / Stop / Hold / Recurse] — all populated, because the practitioner applies Level 3 audit render by default.
*Correct behavior in the same case:* A loaded-term question whose governing burden is clear, whose interlocutor is truth-seeking, and whose required move is semantic disaggregation → Level 1 or Level 2 render. Surface only the materially governing fields. The full template is reserved for audit, pass-review, and explicitly diagnostic tasks.
*Self-audit question:* Is each section I am including materially governing this response, or am I filling it in because the template expects it?
*Why it damages the skill:* It inverts the purpose of the render contract. Diagnostic structure should appear when it serves the case; making it default inverts this, turning every ordinary response into an audit report. The interlocutor encounters bureaucratic structure rather than a response calibrated to their question. It also trains the practitioner to confuse structural completeness with diagnostic rigor.
*Prevented by:* `references/rubrics/diagnostic-render-contract.md` §Render Levels (Level 3 is not default); `references/rubrics/output-release.md` §9 (rubric is not a mandatory full-field template); `SKILL.md §V` (surfaced-mode policy: ordinary mode compresses inactive fields).

---

**Template-Driven Routing**
*Definition:* Allowing the visible render format or the sections that appear in a template to determine what is diagnosed or routed — substituting a structurally complete template for an actually validated IR.
*Pattern appearing in output:* A response fills in every field of the Level 3 render template, including [Case State], [Matched Modules], and [Source Basis], as part of the response-generation process rather than as the output of a prior validated diagnostic pass. The fields are populated by reasoning backward from the answer — what modules would make this response look well-formed? — rather than forward from the diagnostic pass.
*Correct behavior in the same case:* Diagnostic IR is formed and validated before any render template is populated. The render template is populated from the validated IR, not constructed in parallel with it. If the IR was not formed, the template sections are fabricated rather than derived.
*Self-audit question:* Did my render template sections emerge from a validated IR, or did I construct them alongside writing the answer?
*Why it damages the skill:* This is the render-side complement to IR fabrication. A templated response can look like a correctly diagnosed response while the actual diagnostic gate was bypassed. The governance record is structurally present but causally reversed — the template shaped the routing rather than the routing shaping the template. This re-introduces the exact failure mode that Rule 10 (IR retrospective documentation) prohibits, at the render level.
*Prevented by:* `SKILL.md §V` Rule 7 (governance blocks rendered from validated IR, not improvised); `diagnostic-ir.md` §How the IR Prevents Cosmetic Compliance; `references/rubrics/diagnostic-render-contract.md` §Prohibited Render Moves; `framework-pipeline.md` forbidden shortcut: "[IR formed retrospectively] → [counts as gate pass]".

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
- Am I continuing because the state actually refreshed, or because I do not want to leave a landed move alone?
- For each entry in `matched_modules`, does a `source_basis` entry with `source_kind: module` name what it governed?
- Am I invoking transcendence or bilā kayf because the specific analytical work is done, or as a substitute for it?
- Did I say something was held and then answer it anyway under a different label?
- After the governing blocker cleared, did I reassess held downstream material or treat it as permanently suppressed?
- Am I waiting for a user reply when internal state refresh already permits the next bounded pass?
- Am I releasing all detected downstream burdens at once, or moving door-by-door with state refresh between each?
- Am I printing a full audit template when the case only requires a compact or ordinary response?
