# daee-epistemics

This repo is a landing page plus the packaged `skill/` tree. The skill itself is the source of truth; the README stays compact so the routing and governance text lives in one place.

## Before You Use This Tool

The diagnostic faculty is subject to the same taxonomy it applies. The skill identifies seven deformations of the fiṭrah — iʿtiqādāt mawrūtha, mushābara fāsida, hawā, ẓann, taqlīd, ʿāda, gharaḍ, and shubhah — in interlocutors. A practitioner's diagnostic reads are only as reliable as the health of the practitioner's own noetic structure. A practitioner operating under hawā (will dug in), gharaḍ (something at stake), or iʿtiqādāt mawrūtha (invisible inherited filters) will produce reads contaminated by those deformations — and will execute every downstream tactic on the basis of those reads. The procedure does not fix a deformed faculty; it inherits its condition.

The tool is ordered toward restoration, not performance. The standpoint stated in §I — removal of occlusion, not construction of novelty; the task of reminder and restoration, not of winning — applies to the practitioner first. Using this tool as a debating instrument, a credential, or a means of forcing verbal concession is itself a deformation: gharaḍ or hawā operating in the practitioner rather than in the interlocutor. The character note in §I is not decorative. "The absence of defensiveness, the quality of genuine listening" are epistemically constitutive — they are part of what makes the engagement reach where argument cannot, especially where doubt is entangled with damaged trust or bad religious experience.

The symmetric check applies inward before outward. `references/tactics/symmetric-taqlid-check.md` exists for a reason: an atheism absorbed from one's intellectual environment without genuine investigation is taqlīd, and so is a theism held by convention without genuine examination. Before deploying V7 against an interlocutor's assumed-by-default skepticism, the practitioner should have applied the same check to their own positions. The practitioner who holds their own commitments by taqlīd rather than taḥqīq has no standing to press the outward check. This is not a one-time gate — it is a standing discipline, because iʿtiqādāt mawrūtha can reestablish itself and ʿāda deepens with time.

The tool can assist getting there. The skill's diagnostic vocabulary — deformation types, discourse orientation, noetic structure across the nine analytical dimensions — is available for self-application. A practitioner who suspects their own reads are contaminated can run the noetic reading checklist and the seven deformations taxonomy on themselves, not only on interlocutors. Dimension 8 (discourse orientation) is especially apt: determine whether your own engagement is ordered toward truth and warrant, or toward identity-performance or vested outcome. This is a feature of the architecture, not an afterthought — the same instruments that produce a structured diagnostic of an interlocutor's noetic structure can produce one of the practitioner's own.

## Start Here

- `skill/SKILL.md`: canonical entry point for the skill, including routing, diagnostics, and response structure
- `skill/references/`: diagnostics, tactics, techniques, procedures, case libraries, and terminology
- `skill/references/techniques/heuristics.md`: always-active analyst discipline and background routing rules
- `skill/references/terminology.md`: glossary for Arabic and technical vocabulary

## Package Shape

The distributable artifact is `daee-epistemics.skill`. Its archive root must contain `SKILL.md` and `references/` directly. Do not package the repository root or preserve the `skill/` folder name inside the final bundle.

## Install / Package for Claude

From any folder, open a terminal and run one of the following. The command clones the repo into a temporary folder, builds `daee-epistemics.skill`, and removes the temporary clone so the folder you opened ends with only `daee-epistemics.skill`.

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

## Terminology

The skill uses Arabic and philosophical vocabulary, but the README does not repeat the definitions. For the operational glossary, read `skill/references/terminology.md`.
