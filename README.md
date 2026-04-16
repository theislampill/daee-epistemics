# daee-epistemics

`daee-epistemics` is a modular LLM skill for epistemic operations and noetic analysis: a cognitive-security framework for classifying discourse, diagnosing orientation, deformation, and concealment, and routing engagements through matched tactics, techniques, procedures, and case modules.

This repository is organized as a GitHub landing page plus a self-contained skill package under [`skill/`](skill/). 
The package is grounded in the coherence and convergence of a common sense account of sound reason, the *fiṭrah* (the innate normative disposition toward truth), and revelation. 
It is designed to examine the condition of the *qalb* (heart-mind) and the *ʿaql* (intellect or reason) before replying to doubts, objections, and worldview conflicts. 
Its governing aim is not to manufacture novelty or simply accumulate clever refutations, but to restore sound cognition so that foundational knowledge, inference, testimony, signs, and revelation are encountered in their proper order.

## Table of Contents
- [Before You Use This Skill](#before-you-use-this-skill)
- [Terminology Note](#terminology-note)
- [Core Thesis](#core-thesis)
- [Why This Framing Fits the Repository](#why-this-framing-fits-the-repository)
- [What the Skill Protects](#what-the-skill-protects)
- [Threat Model](#threat-model)
- [Repository Architecture](#repository-architecture)
- [Operational Governance](#operational-governance)
- [Corpus Integration](#corpus-integration)
- [Install / Package for Claude](#install--package-for-claude)

## Before You Use This Skill
The skill needs a practitioner whose own *fiṭrah* is in reasonable health.

Obstacles to clear:
- *bidʿī ʿaqlī* (contaminated rationality)
- *bidʿī naqlī* (corrupted transmission)

The diagnostic faculty is subject to the same taxonomy it applies. 

The skill identifies in interlocutors seven deformations of the *fiṭrah* — 
- *iʿtiqādāt mawrūtha* (inherited beliefs)
- *hawā* (whim, preconceived bias, or stubbornly clinging to personal opinion in the face of countervailing evidence)
- *ẓann* (conjecture)
- *taqlīd* (blind imitation)
- *ʿāda* (unreflective habit)
- *gharaḍ* (ulterior motive or vested interest)
- *shubhah* (doubt or misgivings)

A practitioner's diagnostic reads are only as reliable as the health of the practitioner's own noetic structure. 
A practitioner operating under *hawā* (will dug in), *gharaḍ* (something at stake), or *iʿtiqādāt mawrūtha* (invisible inherited filters) will produce reads contaminated by those deformations — and will execute every downstream tactic on the basis of those reads. The procedure does not fix a deformed faculty; it inherits its condition.

The skill is ordered toward restoration, not performance. 
The standpoint stated in §I — removal of occlusion, not construction of novelty; the task of reminder and restoration, not of winning — applies to the practitioner first. 
Using this skill as a debating instrument, a credential, or a means of forcing verbal concession is itself a deformation: *gharaḍ* or *hawā* operating in the practitioner rather than in the interlocutor.
The character note in §I is not decorative. 
"The absence of defensiveness, the quality of genuine listening" are epistemically constitutive — they are part of what makes the engagement reach where argument cannot, especially where doubt is entangled with damaged trust or bad religious experience.

The symmetric check applies inward before outward. 
`references/tactics/symmetric-taqlid-check.md` exists for a reason: an atheism absorbed from one's intellectual environment without genuine investigation is *taqlīd*, and so is a theism held by convention without genuine examination. Before deploying V7 against an interlocutor's assumed-by-default skepticism, the practitioner should have applied the same check to their own positions. The practitioner who holds their own commitments by *taqlīd* rather than *taḥqīq* has no standing to press the outward check. 
This is not a one-time gate — it is a standing discipline, because *iʿtiqādāt mawrūtha* can reestablish itself and *ʿāda* deepens with time.

The tool can assist getting there. 
The skill's diagnostic vocabulary — Deformation Types, Discourse Orientation, Noetic Structure across the nine analytical dimensions — is available for self-application. A practitioner who suspects their own reads are contaminated can run the noetic reading checklist and the seven deformations taxonomy on themselves, not only on interlocutors. 
Dimension 8 (discourse orientation) is especially apt: determine whether your own engagement is ordered toward truth and warrant, or toward identity-performance or vested outcome. This is a feature of the architecture, not an afterthought — the same instruments that produce a structured diagnostic of an interlocutor's noetic structure can produce one of the practitioner's own.

## Terminology Note

The repository uses Arabic and philosophical vocabulary because the framework itself is articulated in those terms. 
For fuller definitions, see [`references/terminology.md`](skill/references/terminology.md).

Readers unfamiliar with the vocabulary should treat these terms as named components of the framework. 
The repository's own method requires clarity before response, and that applies to terminology as well.

## Core Thesis

> `daee-epistemics` is best understood as an epistemic SOC: 
a structured system for identifying, classifying, and remediating epistemic distortion affecting the heart-mind.

The point of that analogy is architectural, not ornamental. 

A Security Operations Center does not begin by deploying countermeasures blindly; it initiates:
* intake
* triage
* classification
* root-cause analysis
* response selection. 

This repository applies a comparable logic to theological and philosophical engagement. 
It treats an objection not merely as a proposition to rebut, but as an event arising within a wider *noetic structure* (the underlying structure of how a person knows, trusts, reasons, and proportions belief).

Not a storehouse of arguments; this is a cognitive-security and diagnostic-response framework for epistemic compromise. 
Its aim is restorative: to clear occlusion, reorder cognition, and return the person to sound perception of truth rather than to construct belief from nothing.

## Why This Framing Fits the Repository

The repository begins with diagnosis before rebuttal. 
[`SKILL.md`](skill/SKILL.md) instructs the practitioner to identify input type, epistemological position, mode of concealment, deformation, and discourse orientation before selecting any deeper module. 
That posture is the opposite of generic polemics, which often move straight to proposition-level refutation.

This matters because the framework treats falsehood as more than a bad conclusion. 
It also tracks compromised process: 
* inherited priors presented as neutral defaults
* malformed evidential standards
* grief operating as epistemic fog
* socially reinforced habits of discourse
* volitional resistance masquerading as pure rationality. 

A formally correct argument can fail if it is given to the wrong kind of case.

For that reason, the repository routes engagements by condition, not only by topic. 
In some cases the appropriate move is inferential; in others it is classificatory, clarificatory, or *maieutic* (a method of drawing out latent recognition rather than supplying wholly new content). 
The underlying assumption is that truth is often already signified but occluded, displaced, or misread.

## What the Skill Protects

The protected asset is not "belief" in a thin or merely verbal sense. 
The framework is concerned with the integrity of epistemic constitution as rightly ordered toward truth: 
* the *fiṭrah*
* sound *ʿaql*
* the right relationship among foundational knowledge
* inferential knowledge
* testimony
* signs
* revelation.

That is why the repository is restorative rather than novelty-producing. 
It assumes that sound reason and authentic revelation agree, and that many objections become persuasive only after the noetic environment has already been disordered. 
The work, then, is to identify that disorder and respond at the right depth.

## Threat Model

The framework's threat model includes more than explicit disbelief. It also includes conditions that deform inquiry upstream:

- inherited background assumptions posing as neutrality
- *taqlīd* (unexamined imitation) and socially inherited defaults
- malformed evidential standards that treat one narrow criterion as the whole of rationality
- category mistakes, equivocation, and false contrasts
- grief, injury, or moral protest functioning as epistemic fog
- identity-protective habits of discourse
- volitional resistance and vested interest
- pseudo-rational criteria that parasitize genuine rational norms

In this model, an objection may be intellectually formulated while still arising from a compromised epistemic process. 
That is why the repository repeatedly distinguishes deformations, concealment modes, and discourse orientation before recommending a response.

## Repository Architecture

The repository operationalizes the thesis through a layered structure:

| Path | Role |
|------|------|
| [`SKILL.md`](skill/SKILL.md) | Governing protocol and routing logic. Defines activation conditions, epistemological standpoint, diagnostic protocol, and response format. |
| [`references/diagnostics/`](skill/references/diagnostics/) | Classifies the epistemic condition before argument: noetic reading, deformations, concealment modes, discourse orientation, and related diagnostic lenses. |
| [`references/tactics/`](skill/references/tactics/) | Context-triggered maneuvers for live objection patterns and argumentative behaviors. |
| [`references/techniques/`](skill/references/techniques/) | Reusable diagnostic and restorative methods that can be applied across multiple kinds of case. |
| [`references/procedures/`](skill/references/procedures/) | Ordered multi-stage workflows for recurring engagement classes, including cases that require sustained restoration rather than a single reply. |
| [`references/case-library/`](skill/references/case-library/) | Playbooks for recurring noetic profiles and doctrinal objection families. |
| [`references/terminology.md`](skill/references/terminology.md) | Glossary of Arabic and technical vocabulary used across the framework. |
| [`references/sound-reason-epistemology.md`](skill/references/sound-reason-epistemology.md) | Fuller theoretical account for cases requiring heavier philosophical treatment. |
| [`references/diagnostics/case-state-schema.md`](skill/references/diagnostics/case-state-schema.md) | Compact metadiscursive output form for surfacing case type, module choice, confidence, and restoration target without chain-of-thought dumping. |
| [`references/diagnostics/inference-boundary.md`](skill/references/diagnostics/inference-boundary.md) | Standard markers for separating file-grounded claims, cross-file synthesis, model inference, and speculative extension. |
| [`references/diagnostics/mixed-case-handling.md`](skill/references/diagnostics/mixed-case-handling.md) | Rules for underdetermined diagnoses, mixed cases, and insufficient-basis conditions. |
| [`references/diagnostics/anti-patterns.md`](skill/references/diagnostics/anti-patterns.md) | Self-audit checks against diagnosis collapse, forced fit, tactic over-selection, decorative terminology, and rhetorical overreach. |

Read behaviorally as well as structurally, the architecture works like this: 
Diagnose the Noetic Structure, 
Identify the Primary Deformation, 
Classify Concealment and Discourse Orientation, 
and only then select the relevant Tactic, Technique, Procedure, or Case Module. 
[`references/techniques/heuristics.md`](skill/references/techniques/heuristics.md) functions as the analyst-discipline layer governing how the framework is used.

## Operational Governance

The repository is not only a content store. It carries an explicit governance layer that makes its routing state inspectable:

- a compact case-state schema for naming what kind of case is being read, which module subset is being selected, why, with what confidence
- an inference-boundary legend separating direct file content from cross-file synthesis, model inference, and speculative extension
- mixed-case and insufficient-basis rules to keep the model from overclassifying thin or ambiguous cases
- an anti-pattern sheet to catch diagnosis collapse, forced fit, tactic over-selection, decorative terminology, and rhetorical overreach before they harden into output

This matters because the repository's thesis is restorative, not merely polemical. 
The framework should make it easy for a model to say, succinctly, "this is the kind of case I think this is, this is why I am taking this path, this is how sure I am, and this is where I am inferring beyond the file set."

## Corpus Integration

New source material should be integrated only when it improves routing, restoration, scope control, or terminology discipline. 

The goal is not to accumulate study notes. 

The goal is to extract durable distinctions and convert them into reusable architecture: new Case Modules, tighter Tactic or Technique criteria, clarified Glossary entries, sharper confidence rules, or better routing boundaries. 

If a source does not alter how the skill classifies, sequences, or restores, it should usually not be imported.

## Install / Package for Claude

The distributable artifact for this repository is `daee-epistemics.skill`. 
Its archive root must contain `SKILL.md` and `references/` directly. 
Do not zip the whole repo root, and do not produce a bundle whose top level is `skill/`.

From any folder, open a terminal and paste one of the following. The command will clone the repo into a temporary subfolder, build `daee-epistemics.skill`, and remove the temporary clone so the folder you opened ends with only `daee-epistemics.skill`.

PowerShell:

```powershell
$repo = "https://github.com/theislampill/daee-epistemics.git"
$tmp = "daee-epistemics-src"
$tmpSkill = "daee-epistemics.tmp.skill"
$outSkill = "daee-epistemics.skill"

if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
if (Test-Path $tmpSkill) { Remove-Item $tmpSkill -Force }

git clone $repo $tmp
Compress-Archive -Path ".\$tmp\skill\*" -DestinationPath ".\$tmpSkill.zip" -Force
Move-Item ".\$tmpSkill.zip" ".\$tmpSkill" -Force
Move-Item ".\$tmpSkill" ".\$outSkill" -Force
Remove-Item $tmp -Recurse -Force
```

Bash:

```bash
repo="https://github.com/theislampill/daee-epistemics.git"
tmp="daee-epistemics-src"
tmp_skill="daee-epistemics.tmp.skill"
out_skill="daee-epistemics.skill"

rm -rf "$tmp" "$tmp_skill"
git clone "$repo" "$tmp" &&
(cd "$tmp/skill" && zip -r "../../$tmp_skill" .) &&
mv -f "$tmp_skill" "$out_skill" &&
rm -rf "$tmp"
```

If you open `daee-epistemics.skill`, you should see `SKILL.md` and `references/` at the top level of the archive.

Claude-first installation flow:

1. Package the skill from this repository.
2. Open Claude.ai and go to Settings > Skills, or open [Claude Skills](https://claude.ai/customize/skills).
3. Upload `daee-epistemics.skill`.
4. Enable the skill and test it with a query that should trigger epistemic diagnosis or objection handling.

The same `.skill` bundle may also work in other agent platforms that support the open skill format, but the upload steps outside Claude may differ.