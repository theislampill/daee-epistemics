---
id: E1-broadening-evidence
module_class: tactic
canonical_path: skill/references/tactics/E1-broadening-evidence.md
contract_version: "0.4.0.0"
load_when:
  - interlocutor insists "there is no evidence" for God's existence
  - evidential scope needs widening beyond empirical-only criterion
blocks:
  - run doubt-vs-skepticism first when interlocutor's rule is "belief requires evidence, absence is disproof" — E1 inside an uncleared evidentialist framework is absorbed
companions:
  - doubt-vs-skepticism
  - V5-directing-attention-signs
  - E3-cumulative-case
output_shapes:
  - bounded-single-pass
layer_constraint: layer-b-permitted
catalogue_registered: true
verification_status: L_check
direct_read_verified: true
failure_conditions_present: true
ir_consequences_present: true
minimal_pairs_present: true
hold_release_rules_present: true
compiled_runtime_eligible: true
operator_pack_eligible: true
---

# E1 — Broadening the Evidential Scope

## Runtime operator contract

- Activation: interlocutor insists "there is no evidence" for God's existence.
- Field target: the live burden or submove pressure that made tactic `E1-broadening-evidence` eligible; activation cue: interlocutor insists "there is no evidence" for God's existence.
- Burden/submove form: tactic `ⁿBᵢ[OPᵢ]`: target -> operation -> result; the result contributes to `Land(ⁿB)` only when live for the current burden.
- Δ effect: `ΔⁿB` is the local target/operation/result transition; `Δκ` changes only if the operation affects closure, dependency radius, or held routes.
- Possible ∇ reread: after the tactic lands, check target-explicit `∇·B` for remaining burden pressure or `∇×ξ`/`∇×κ` for circular criterion/dependency pressure when relevant.
- R(H,Δ) obligation: after this owner acts, reread H, remaining burdens, alternate routes, register pressure, dependency loops, and closure state before STOP/RECURSE/PARTIAL.
- Hold/release/closure effect: release only the bounded result that has landed; hold, integrate, discharge as derivative, or carry forward unresolved pressure with reason.
- Output boundary: `layer-b-permitted` with output shapes `bounded-single-pass`. Default render may show compact state markers when control-bound; long formalism stays audit/formalism-expanded.
- Negative constraints: no argument-bank drift, no scalar closure, no deterministic route freezing, no indiscriminate TTP spraying, no ∇ as Δ replacement, no proof-by-symbol, and no Shannon/reconstruction-branding/∇ truth-or-warrant claim.
- Fixture/checker: Direct routing fixtures cover this owner (1); `tools/check_routing_parity.py`, `tools/check_ttp_operator_contracts.py`, and compiled-runtime freshness must remain green.


**Register:** Evidentialist
**Deploy when:** The interlocutor insists "there is no evidence" for God's existence.

Do not contest this on their narrow terms. Redirect to the full evidential field they have not counted:

- **Signs (āyāt):** Sensory, cosmological, scriptural — each a direct *indication* of the divine, not a syllogistic premise. The sign activates the fiṭrah; it does not supply a premise for an inference. See `references/techniques/V5-directing-attention-signs.md` for the critical distinction between indication and argument.
- **Arguments (dalāʾil):** Inferential, analogical, demonstrative — these belong to the ḥusn al-naẓar register and are secondary instruments for impaired fiṭrah.
- **Reliable testimony (khabar):** Transmitted from those who have observed or investigated what we cannot directly access. The reliability of the chain is the criterion. See `references/sound-reason-epistemology.md` §4 for the tawātur account.
- **Direct inner experience (wājid):** The felt sense of moral obligation, beauty, awe, recognition arising in genuine attentiveness. Inner states count as ḥiss — they are not less real for being interior.
- **Spiritual awareness (ilhām):** Direct experiential evidence in states of inner clarity.

**The key move:** The question is not whether God-belief survives a narrow evidential standard but whether that standard is adequate to the full structure of human knowledge. An interlocutor who counts only replicable empirical experiment is already relying on the other channels constantly — for knowledge of other minds, of the past, of mathematical objects, of logical axioms. Show this inconsistency before arguing for any specific sign.

## Precedence Rule — E1 vs. doubt-vs-skepticism

E1 broadens the evidential scope that the interlocutor will count. `doubt-vs-skepticism.md`
challenges whether evidence is the default epistemic requirement at all. The two are
distinct moves and the wrong order produces a predictable misfire:

- **Run `doubt-vs-skepticism.md` first** when the interlocutor's operative rule is "every
  belief requires evidence, and absence of evidence is disproof." The framework is the
  problem; broadening the evidential menu (E1) inside that framework still concedes that
  evidence is what settles the question.
- **Run E1 first** when the interlocutor accepts that some beliefs are warranted
  non-inferentially but holds that theistic belief is not among them, or when the
  interlocutor's stated standard is actually narrower than their practice and the
  inconsistency is the fastest move to land.
- **Do not run both in the same turn.** E1 deployed on top of an uncleared
  evidentialist framework is absorbed as "more candidate evidence" — the framework
  filters each of the E1 channels as "not the right kind." The framework must be
  cleared first (doubt-vs-skepticism + E2 + M1-P) or E1 must find a narrower foothold
  (the inconsistency between standard and practice) that does the framework-clearing
  incidentally.

For NS-1 (Naturalist) and NS-6 (Kalāmic Evidentialist): framework-clearing precedes
E1. For NS-2 (Agnostic Evidentialist) when the interlocutor has already conceded
non-inferential warrant in other domains: E1 can be the direct move. For NS-7
(Theistic Evidentialist): neither is the right move — the interlocutor already
accepts theism; V9 (necessary-knowledge priority) is what relocates warrant.

**Connection:** When the interlocutor acknowledges the broader evidential scope, move to E3 (cumulative case) or V5 (directing attention to signs).
