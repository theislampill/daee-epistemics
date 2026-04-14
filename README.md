# daee-epistemics

A modular LLM skill for epistemic operations and noetic analysis: a cognitive-security framework for classifying discourse, diagnosing orientation, deformation, and concealment, and routing engagements through matched tactics, techniques, procedures, and case modules.

This repository is organized as a GitHub landing page plus a self-contained skill package under [`skill/`](skill/). The package is grounded in an Islamic account of sound reason, the *fiṭrah* (the innate normative disposition toward truth and recognition of God), and revelation. It is designed to examine the condition of the *qalb* (heart-mind) and the *ʿaql* (intellect or reason) before replying to doubts, objections, and worldview conflicts. Its governing aim is not to manufacture novelty or simply accumulate clever refutations, but to restore sound cognition so that foundational knowledge, inference, testimony, signs, and revelation are encountered in their proper order.

## Table of Contents

- [Core Thesis](#core-thesis)
- [Why This Framing Fits the Repository](#why-this-framing-fits-the-repository)
- [What the Skill Protects](#what-the-skill-protects)
- [Threat Model](#threat-model)
- [Repository Architecture](#repository-architecture)
- [Install / Package for Claude](#install--package-for-claude)
- [Terminology Note](#terminology-note)

## Core Thesis

> `daee-epistemics` is best understood as an epistemic SOC: a structured system for identifying, classifying, and remediating epistemic distortion affecting the human heart-mind.

The point of that analogy is architectural, not ornamental. A Security Operations Center does not begin by deploying countermeasures blindly; it begins with intake, triage, classification, root-cause analysis, and response selection. This repository applies a comparable logic to theological and philosophical engagement. It treats an objection not merely as a proposition to rebut, but as an event arising within a wider *noetic structure* (the underlying structure of how a person knows, trusts, reasons, and proportions belief).

Not a storehouse of arguments; this is a cognitive-security and diagnostic-response framework for epistemic compromise. Its aim is restorative: to clear occlusion, reorder cognition, and return the person to sound perception of truth rather than to construct belief from nothing.

## Why This Framing Fits the Repository

The repository begins with diagnosis before rebuttal. [`skill/SKILL.md`](skill/SKILL.md) instructs the practitioner to identify input type, epistemological position, mode of concealment, deformation, and discourse orientation before selecting any deeper module. That posture is the opposite of generic polemics, which often move straight to proposition-level refutation.

This matters because the framework treats falsehood as more than a bad conclusion. It also tracks compromised process: inherited priors presented as neutral defaults, malformed evidential standards, grief operating as epistemic fog, socially reinforced habits of discourse, and volitional resistance masquerading as pure rationality. A formally correct argument can fail if it is given to the wrong kind of case.

For that reason, the repository routes engagements by condition, not only by topic. In some cases the appropriate move is inferential; in others it is classificatory, clarificatory, or *maieutic* (a method of drawing out latent recognition rather than supplying wholly new content). The underlying assumption is that truth is often already signified but occluded, displaced, or misread.

## What the Skill Protects

The protected asset is not "belief" in a thin or merely verbal sense. The framework is concerned with the integrity of the human epistemic constitution as rightly ordered toward truth: the *fiṭrah*, sound *ʿaql*, and the right relationship among foundational knowledge, inferential knowledge, testimony, signs, and revelation.

That is why the repository is restorative rather than novelty-producing. It assumes that sound reason and authentic revelation agree, and that many objections become persuasive only after the noetic environment has already been disordered. The work, then, is to identify that disorder and respond at the right depth.

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

In this model, an objection may be intellectually formulated while still arising from a compromised epistemic process. That is why the repository repeatedly distinguishes deformations, concealment modes, and discourse orientation before recommending a response.

## Repository Architecture

The repository operationalizes the thesis through a layered structure:

| Path | Role |
|------|------|
| [`skill/SKILL.md`](skill/SKILL.md) | Governing protocol and routing logic. Defines activation conditions, epistemological standpoint, diagnostic protocol, and response format. |
| [`skill/references/diagnostics/`](skill/references/diagnostics/) | Classifies the epistemic condition before argument: noetic reading, deformations, concealment modes, discourse orientation, and related diagnostic lenses. |
| [`skill/references/tactics/`](skill/references/tactics/) | Context-triggered maneuvers for live objection patterns and argumentative behaviors. |
| [`skill/references/techniques/`](skill/references/techniques/) | Reusable diagnostic and restorative methods that can be applied across multiple kinds of case. |
| [`skill/references/procedures/`](skill/references/procedures/) | Ordered multi-stage workflows for recurring engagement classes, including cases that require sustained restoration rather than a single reply. |
| [`skill/references/case-library/`](skill/references/case-library/) | Playbooks for recurring noetic profiles and doctrinal objection families. |
| [`skill/references/terminology.md`](skill/references/terminology.md) | Glossary of Arabic and technical vocabulary used across the framework. |
| [`skill/references/sound-reason-epistemology.md`](skill/references/sound-reason-epistemology.md) | Fuller theoretical account for cases requiring heavier philosophical treatment. |

Read behaviorally as well as structurally, the architecture works like this: diagnose the noetic structure, identify the primary deformation, classify concealment and discourse orientation, and only then select the relevant tactic, technique, procedure, or case module. [`skill/references/techniques/heuristics.md`](skill/references/techniques/heuristics.md) functions as the analyst-discipline layer governing how the framework is used.

## Install / Package for Claude

The distributable artifact for this repository is `daee-epistemics.skill`. Its archive root must contain `SKILL.md` and `references/` directly. Do not zip the whole repo root, and do not produce a bundle whose top level is `skill/`.

From this repo:

1. Clone or download the repository.
2. Run one of the packaging commands below from the repo root.
3. Upload `daee-epistemics.skill` in Claude.ai via Settings > Skills or the [Claude Skills](https://claude.ai/customize/skills) page.

PowerShell:

```powershell
Compress-Archive -Path .\skill\* -DestinationPath .\daee-epistemics.zip -Force
Move-Item .\daee-epistemics.zip .\daee-epistemics.skill -Force
```

Bash:

```bash
(cd skill && zip -r ../daee-epistemics.skill .)
```

If you open `daee-epistemics.skill`, you should see `SKILL.md` and `references/` at the top level of the archive.

Claude-first installation flow:

1. Package the skill from this repository.
2. Open Claude.ai and go to Settings > Skills, or open [Claude Skills](https://claude.ai/customize/skills).
3. Upload `daee-epistemics.skill`.
4. Enable the skill and test it with a query that should trigger epistemic diagnosis or objection handling.

The same `.skill` bundle may also work in other agent platforms that support the open skill format, but the upload steps outside Claude may differ.

## Terminology Note

The repository uses Arabic and philosophical vocabulary because the framework itself is articulated in those terms. This README defines key terms on first use so that newcomers do not need prior training in Islamic theology or philosophy to follow the argument. For fuller definitions, see [`skill/references/terminology.md`](skill/references/terminology.md).

Readers unfamiliar with the vocabulary should treat these terms as named components of the framework, not as insider shibboleths. The repository's own method requires clarity before response, and that applies to terminology as well.
