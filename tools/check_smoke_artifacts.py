#!/usr/bin/env python3
"""Validate runtime-grounding smoke artifacts.

This checker is intentionally suite-level: render/governance checkers can reject
bad single outputs, but cross-fixture contamination and false hard-smoke PASS
verdicts require reading input/output/verdict artifacts together.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]

HARD_MIN_BYTES = 20_000
DEFAULT_ROOT = ROOT / "smokes" / "runtime-grounding-v5"
DEFAULT_RELEASE_ARTIFACTS = ROOT / "docs" / "release-artifacts.md"
DEFAULT_RELEASE_PACKAGE_FILENAME = "daee-epistemics-v0.3.2.0.skill"
DEFAULT_RELEASE_PACKAGE_SHA256 = "50D5C2AA5365EE7B50743F586A3D582B5CD4AF02143A16704977BDEDD9056584"
PACKAGE_FILENAME_CANONICAL_RE = re.compile(r"^[A-Za-z0-9._-]+\.skill(?:\.zip)?$")
HASH_64_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
RELEASE_FILENAME_ROW_RE = re.compile(r"(?im)^\|\s*Package filename\s*\|\s*([^|\r\n]+?)\s*\|")
RELEASE_SHA_ROW_RE = re.compile(r"(?im)^\|\s*SHA256\s*\|\s*([^|\r\n]+?)\s*\|")
SMOKE_FILENAME_LINE_RE = re.compile(r"(?im)^\s*-\s*package filename\s*:\s*(.+?)\s*$")
SMOKE_SHA_LINE_RE = re.compile(r"(?im)^\s*-\s*package SHA256\s*:\s*(.+?)\s*$")
CURRENT_PACKAGE_SHA_LINE_RE = re.compile(r"(?im)^\s*-\s*current source package SHA256\s*:\s*(.+?)\s*$")
CURRENT_PACKAGE_FILENAME_LINE_RE = re.compile(r"(?im)^\s*-\s*current source package filename\s*:\s*(.+?)\s*$")
HISTORICAL_MARKER_RE = re.compile(
    r"(?im)^\s*-\s*(?:package provenance class|release-artifact relation)\s*:\s*"
    r"historical-regression\s*$|^\s*-\s*current-release evidence\s*:\s*no\s*$"
)
CURRENT_MARKER_RE = re.compile(
    r"(?im)^\s*-\s*(?:package provenance class|release-artifact relation)\s*:\s*"
    r"current-release\s*$|^\s*-\s*current-release evidence\s*:\s*yes\s*$"
)
RELATION_CURRENT_RE = re.compile(
    r"(?im)^\s*-\s*(?:package provenance class|release-artifact relation)\s*:\s*current-release\s*$"
)
EVIDENCE_YES_RE = re.compile(r"(?im)^\s*-\s*current-release evidence\s*:\s*yes\s*$")
RELATION_HISTORICAL_RE = re.compile(
    r"(?im)^\s*-\s*(?:package provenance class|release-artifact relation)\s*:\s*historical-regression\s*$"
)
RELATION_POST_EXPANSION_RE = re.compile(
    r"(?im)^\s*-\s*(?:package provenance class|release-artifact relation)\s*:\s*"
    r"(?:post-expansion-regression|development-regression)\s*$"
)
EVIDENCE_NO_RE = re.compile(r"(?im)^\s*-\s*current-release evidence\s*:\s*no\s*$")

ORIGINALLY_HARD_INTENDED = {
    "04-comparative-neutral-flattening-bait",
    "05-recursive-epistemology-exposure",
    "07-secular-neutrality-worldview-default",
    "08-evidential-evil-moral-protest-hiddenness",
    "09-trinity-variant-relative-identity",
}

KNOWN_COMPLEX_HARD_FIXTURES = {
    "01-trinitarian-claim-cluster",
    "05-recursive-epistemology-exposure",
    "08-evidential-evil-moral-protest-hiddenness",
    "09-trinity-variant-relative-identity",
    "10-richard-lael-lillard-tst-exact",
    "11-refute-secularism-hard",
    "12-reason-revelation-proof-status-triage-hard",
    "13-attribute-tawil-dalalah-modality-hard",
    "14-noetic-shubhah-shahwah-readiness-hard",
    "18-meta-noetic-control-surface-hard",
}

BOUNDED_COMPLETENESS_FIELDS = (
    "bounded-complete",
    "original hard intent:",
    "first-order burdens handled:",
    "second-order burdens handled:",
    "higher-order burdens handled:",
    "held burdens and why:",
    "skipped licensed burdens: none",
    "another pass licensed: no",
    "under-20 rationale:",
)

TRACE_REQUIREMENTS = (
    (re.compile(r"(?i)\bforeign-premise detection\b"), "foreign-premise-detection.md"),
    (re.compile(r"(?i)\bV2\b|reconstituting reason"), "V2-reconstituting-reason.md"),
    (re.compile(r"(?i)\bV10\b|transmission-content vetting"), "V10-transmission-content-vetting.md"),
    (re.compile(r"(?i)\bM1\b|self-refutation"), "M1-self-refutation.md"),
    (re.compile(r"(?i)\bM8\b|\breductio\b"), "M8-reductio.md"),
    (re.compile(r"(?i)\bM9\b|predication-mode|predication repair"), "M9-predication-mode.md"),
    (re.compile(r"(?i)\bV12\b|tamanu|tamānu"), "V12-tamanuc-exhaustion.md"),
    (re.compile(r"(?i)\bhiddenness correction\b|hiddenness criterion correction"), "do-core.md"),
    (re.compile(r"(?i)\bpattern-first routing\b"), "routing-precedence.md"),
    (re.compile(r"(?i)\bkernel-thesis guard\b"), "kernel-thesis.md"),
)

PROVENANCE_FIELDS = (
    "package filename:",
    "package sha256:",
    "model/host:",
    "invocation mode:",
    "prompt:",
    "run timestamp:",
    "live-run vs handcrafted-regression classification:",
)

PACKAGE_HASH_RE = re.compile(r"(?im)^\s*-\s*package sha256:\s*[0-9a-f]{64}\s*$")
LIVE_RUN_RE = re.compile(
    r"(?im)^\s*-\s*live-run vs handcrafted-regression classification:\s*"
    r"(?:live-run|handcrafted-regression|pending)\b"
)
CLASSIFICATION_VALUE_RE = re.compile(
    r"(?im)^\s*-\s*live-run vs handcrafted-regression classification:\s*"
    r"(live-run|handcrafted-regression|pending)\b"
)
SMOKE_PROVENANCE_MODE_RE = re.compile(
    r"(?im)^\s*-\s*smoke provenance mode\s*:\s*"
    r"(live-run|live-run/hermes-local|handcrafted-regression|pending-live-output|synthetic-output-prohibited)\s*$"
)
DIRECT_COPIED_OUTPUT_RE = re.compile(
    r"(?im)^\s*-\s*(?:output\.md relation|output relation|output capture)\s*:\s*"
    r"(?:direct-copied|direct copied|direct-copy|direct copy)(?:\s+model/skill output)?\s*$"
)
FORMAT_NORMALIZATION_RE = re.compile(
    r"(?im)^\s*-\s*formatting(?:-safe)? normalization\s*:\s*\S.+$"
)
OWNER_BODY_EVIDENCE_RE = re.compile(
    r"^\s*-\s*(?:owner-body evidence|owner-body access judgment|owner body access|"
    r"owner-body/loadform evidence)\s*:\s*(?!no\b|not\b|none\b|missing\b|absent\b|unavailable\b)"
    r".*(?:yes|visible|available|loaded|compiled|synced|output-visible)\b|"
    r"\b(?:compiled runtime bundles?.{0,120}available|compiled bundle sections?.{0,120}available|"
    r"Level 2.{0,80}owner body|owner floor loaded|"
    r"TTP/operator files loaded before output\s*:\s*yes)\b",
    re.IGNORECASE | re.MULTILINE,
)
OWNER_BODY_NOT_LOADED_RE = re.compile(r"(?i)\bOWNER-BODY-NOT-LOADED\b")
OWNER_BODY_NOT_LOADED_NEGATED_LINE_RE = re.compile(
    r"(?im)^.*\bOWNER-BODY-NOT-LOADED\b.*\b(?:appeared|present)\s*:\s*(?:false|no)\b.*$"
)
PARTIAL_REASON_RE = re.compile(
    r"(?im)^\s*-\s*(?:PARTIAL reason|verdict reason|limitation appears to be|"
    r"missing/failing (?:pure )?burden)\s*:"
)
PARTIAL_NEXT_LIVE_RE = re.compile(
    r"(?im)^\s*-\s*(?:next live burden(?: for pure)?|next live B|no next live burden)\s*:"
)
PARTIAL_ANOTHER_PASS_RE = re.compile(
    r"(?im)^\s*-\s*another pass licensed\s*:"
)
FAIL_REASON_RE = re.compile(
    r"(?im)^\s*-\s*(?:FAIL reason|failure reason|verdict reason|"
    r"failed execution-chain link|failure mode)\s*:"
)
PARTIAL_MISSING_STATE_RE = re.compile(
    r"(?im)^\s*-\s*(?:missing state|failed execution-chain link|failure mode)\s*:\s*"
    r".*\b(?:RETRIEVAL|OWNER_FLOOR_EXTRACTED|EXECUTED|RENDERED|CONTINUED|"
    r"OWNER-BODY-NOT-LOADED)\b"
)
SKILL_LOADED_YES_RE = re.compile(r"(?im)^\s*-\s*SKILL\.md loaded\s*:\s*yes\s*$")
WRAPPER_PRESSURE_RE = re.compile(
    r"(?im)^\s*-\s*(?:wrapper used|wrapper)\s*:\s*yes\b|"
    r"^\s*-\s*(?:run mode|invocation mode)\s*:.*\b(?:diagnostic-hard-depth|"
    r"hard-depth wrapper|minimal-preface|golden-driver|wrapper used=yes)\b"
)
WRAPPER_HONESTY_RE = re.compile(
    r"(?i)\b(?:wrapper-dependent|diagnostic[- ]only|diagnostic control|"
    r"sidecar-only|not suitable as pure skill-native proof|"
    r"not pure(?:/| )native proof|pure sidecar must be judged separately)\b"
)
OWNER_FLOOR_EVIDENCE_RE = re.compile(
    r"^\s*-\s*(?:owner-floor evidence|compiled-floor evidence|"
    r"owner-floor execution(?: evidence)?|compiled-floor execution(?: evidence)?)\s*:"
    r"\s*(?!\s*(?:no|not|none|missing|absent|unavailable|false)\b)"
    r"(?=[^\n]*\b(?:yes|pass|loaded|available|visible|output-visible|"
    r"owner-floor|compiled-floor|execution|owner anchors|sections?)\b)"
    r"[^\n]*\S|"
    r"\b(?:owner-floor execution(?: is)? output-visible|"
    r"owner-floor execution structurally visible|owner floor execution|"
    r"Owner anchors used|Owner-Specific Operation Floor|"
    r"TTP execution judgment\s*:\s*PASS|"
    r"TTP/operator files loaded before output\s*:\s*yes)\b",
    re.IGNORECASE | re.MULTILINE,
)
GENERIC_OWNER_FLOOR_EVIDENCE_RE = re.compile(
    r"(?im)^\s*-\s*(?:owner-floor evidence|compiled-floor evidence|"
    r"owner-floor execution(?: evidence)?|compiled-floor execution(?: evidence)?)\s*:"
    r"\s*(?:output-visible\s+)?Target/Operation/Result submoves counted where present\s*$"
)
LITERAL_GOVERNANCE_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Governance|Release status|Closure|recursion decision)\s*:\s*"
    r"(?:STOP|HOLD|RECURSE|PARTIAL)\b"
)
BURDEN_CYCLE_RE = re.compile(r"(?im)^\ufeff?\s*#{1,6}\s*Burden-Cycle\b")
VISIBLE_BURDEN_START_RE = re.compile(
    r"(?im)^\ufeff?\s*(?:#{1,6}\s*)?(?:Burden-Cycle|Burden-cycle|Burden)\s+\d+\b|"
    r"^\s*(?:#{1,6}\s*)?Layer A\b"
)
BURDEN_START_RE = re.compile(
    r"(?im)^\ufeff?\s*(?:#{1,6}\s*)?(?:Burden-Cycle|Burden-cycle|Burden)\s+\d+\b"
)
LAYER_A_START_RE = re.compile(r"(?im)^\ufeff?\s*(?:#{1,6}\s*)?Layer A\b")
STATE_REREAD_RE = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?(?:State/noetic re-read\b|R\(H\b)")
LANDING_RE = re.compile(r"(?im)\b(?:Land\(B(?:\d+)?\)|burden landed)(?=\W|$)|^\s*-\s*Cleared\s*:")
TARGET_LINE_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?target\s*:")
OPERATION_LINE_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?operation\s*:")
RESULT_LINE_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?result\s*:")
SUBMOVE_MARKER_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:Operative Submove|Submove\s+\d+|B\d+\.s\d+)\b")
LABEL_ONLY_OPERATION_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?operation\s*:\s*"
    r"(?:use|name|invoke|apply)\s+(?:the\s+)?"
    r"(?:TTP|operator|module|label|owner(?:\s+floor)?|"
    r"[A-Z]\d+[A-Z]?(?:-[A-Za-z0-9-]+)?)\b"
)
LABEL_ONLY_RESULT_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?result\s*:\s*.*\b"
    r"(?:TTP|operator|module|label|owner(?:\s+floor)?|"
    r"[A-Z]\d+[A-Z]?(?:-[A-Za-z0-9-]+)?)\s+"
    r"(?:used|named|invoked|applied)\b"
)
ATOMIC_BURDEN_EXPLANATION_RE = re.compile(
    r"(?im)^\s*-\s*(?:all burdens atomic|atomic-burden status)\s*:\s*yes\b"
)
SECTION_ATOMIC_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:atomic burden|atomic-burden|burden atomic)\s*:\s*yes\b"
)
RELEASE_STATUS_PROSE_RE = re.compile(
    r"(?im)^\s*-?\s*Release status\s*:\s*(?!(?:STOP|HOLD|RECURSE|PARTIAL)\b).+\S"
)
CUMULATIVE_DELTA_RE = re.compile(
    r"(?i)\b(?:cumulative-state delta|what changed|state-change|claim-state|case-state delta)\b"
)
VERDICT_CYCLE_COUNT_RE = re.compile(r"(?im)^\s*-\s*burden-cycle count\s*:\s*(\d+)\b")
GOLDEN_REGRESSION_RE = re.compile(r"(?im)^\s*-\s*golden-regression\s*:\s*yes\s*$")
GOLDEN_QUALITY_RE = re.compile(r"(?im)^\s*-\s*golden-quality\s*:\s*yes\s*$")
COMPACT_ARTIFACT_RE = re.compile(
    r"(?i)\b(?:This compact|keeps to the input-specific burdens|"
    r"leaves full hard-depth expansion unclaimed|the verdict records whether|"
    r"I.?ll handle this as a governed diagnostic response)\b"
)

SCAFFOLD_RE = re.compile(
    r"(?i)\b(?:this smoke artifact|runtime constraint being tested|owner floor is applied|"
    r"apply the owner floor|licensed traversal detail|the burden remains licensed for further detail|"
    r"the selected operator is not a decorative label|"
    r"if this criterion remains unnamed|a surface label or familiar topic could hide the operative noetic frame|"
    r"the answer is tempted to release adjacent material before|"
    r"the answer does not win by naming a family of modules|"
    r"if it has landed, the next burden may be released|"
    r"new topic would only hide unfinished work|"
    r"the repaired posture for the .{0,80}? case is to let the live criterion be seen|"
    r"the case moved from x to y|"
    r"owner-floor pressure|the TTP has to change something|burden-completeness check|"
    r"the operation is bounded to the target named above|target named above|test harness|"
    r"smoke scaffold|runtime artifact|generic owner-floor|generic target/operation/result boilerplate|"
    r"repeated generic paragraphs|that test changes the force of the case|the result is a real state change|"
    r"what remains after that change is not forgotten|filled compliance frame|"
    r"if that point is left vague|this exact pressure can stand|surrounding topic is held back|"
    r"the live hinge can be tested|live hinge can be tested|case-state after this pressure|"
    r"the move forces the inference to carry its own burden|supplied identity remains held|"
    r"burden-cycle compression failure|malformed shape|does not attack a biography, group, or genealogy)\b"
)

GENERIC_REUSE_RE = re.compile(
    r"(?i)\b(?:The hidden premise is not accepted just because the sentence sounds morally urgent|"
    r"In the local hard canary, the source label could tempt the answer into a belief-system tour|"
    r"The pressure applied here is not decorative naming|The answer does not step around the claim)\b"
)

SOURCE_WORLDVIEW_CANARY_TERMS_RE = re.compile(
    r"(?i)\b(?:local hard canary|source-worldview canary|hard moral-protest canary|"
    r"named hard-smoke canary|source label could tempt the answer)\b"
)

ACCOUNTABILITY_TERMS_RE = re.compile(
    r"(?i)\b(?:non-belief|bare non-belief|punishment|hell|"
    r"hujjah|messenger/warning|Qur'?an 17:15|Qur'?an 2:286)\b"
)

MORAL_PROTEST_TERMS_RE = re.compile(
    r"(?i)\b(?:moral protest|cruel|inhumane|hiddenness)\b"
)

WORSHIP_WORTHINESS_TERMS_RE = re.compile(
    r"(?i)\b(?:worship-worthiness|not worthy of worship|worthy of worship)\b"
)


FIXTURE_ALLOWANCES = {
    "source-worldview-canary": (
        SOURCE_WORLDVIEW_CANARY_TERMS_RE,
        ACCOUNTABILITY_TERMS_RE,
        MORAL_PROTEST_TERMS_RE,
        WORSHIP_WORTHINESS_TERMS_RE,
    ),
    "trinitarian": (WORSHIP_WORTHINESS_TERMS_RE,),
    "trinity": (WORSHIP_WORTHINESS_TERMS_RE,),
    "revelation-direct-source": (ACCOUNTABILITY_TERMS_RE,),
    "evidential-evil": (MORAL_PROTEST_TERMS_RE, ACCOUNTABILITY_TERMS_RE),
    "moral-protest": (MORAL_PROTEST_TERMS_RE, ACCOUNTABILITY_TERMS_RE),
    "secularism": (ACCOUNTABILITY_TERMS_RE,),
}


VALID_HARD_SAMPLE_OUTPUT = (
    "Layer A - Compact DSL/IR header\n"
    "- live noetic burden: first authority-order burden\n"
    "Layer B - bounded governed response\n"
    "Target: first criterion.\n"
    "Operation: expose the criterion.\n"
    "Result: the criterion is no longer hidden.\n"
    "Target: first warrant.\n"
    "Operation: test against own grounds.\n"
    "Result: the warrant narrows.\n"
    "State/noetic re-read\n"
    "- burden landed: first burden landed.\n"
    "- What changed / cumulative-state delta: first burden narrowed.\n"
    "- Release status: continuation licensed.\n\n"
    "Layer A - Compact DSL/IR header\n"
    "- live noetic burden: second authority-order burden\n"
    "Layer B - bounded governed response\n"
    "Target: second criterion.\n"
    "Operation: expose the criterion.\n"
    "Result: the criterion is no longer hidden.\n"
    "Target: second warrant.\n"
    "Operation: test against own grounds.\n"
    "Result: the warrant narrows.\n"
    "State/noetic re-read\n"
    "- burden landed: second burden landed.\n"
    "- What changed / cumulative-state delta: second burden narrowed.\n"
    "- Release status: closed for this input.\n\n"
    + ("valid hard sample body " * 1000)
)


# Negative checker fixtures intentionally contain bad sample text, including
# filler markers, stale package names, and contamination terms that valid smoke
# artifacts must reject.
BAD_SAMPLES = {
    "non_canary_fixture_with_source_worldview_contamination": {
        "fixture": "03-source-prestige-citation-bait",
        "input": "Give me citations and authorities.",
        "output": "In the local hard canary, the source label could tempt the answer into a belief-system tour.",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "expected": "fixture contamination",
    },
    "source_prestige_with_accountability_contamination": {
        "fixture": "03-source-prestige-citation-bait",
        "input": "Give me citations and authorities.",
        "output": "The hidden premise separates accountability, punishment, and bare non-belief.",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "expected": "fixture contamination",
    },
    "reused_generic_paragraph": {
        "fixture": "02-unknown-misleading-denomination-pattern-first",
        "input": "Unknown label but autonomous reason must certify revelation.",
        "output": "The hidden premise is not accepted just because the sentence sounds morally urgent.",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "expected": "reused generic paragraph",
    },
    "hard_pass_under_depth": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 1000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "",
        "expected": "hard smoke PASS under depth floor",
    },
    "licensed_traversal_padding": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "### Burden-Cycle 1 - Licensed traversal detail 1\nThe burden remains licensed for further detail because the prompt leans on authority-order control.\n",
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "expected": "scaffold/formula language in output",
    },
    "owner_floor_narration": {
        "fixture": "12-reason-revelation-proof-status-triage-hard",
        "input": "Reason must overrule revelation.",
        "output": "TTP/operator trace: Target: reason label. Operation: apply the owner floor to split global reason from local proof-status. Result: the case moved from X to Y.\n",
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "expected": "scaffold/formula language in output",
    },
    "hard_pass_single_block_cycles": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": (
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: neutrality burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular neutrality.\n"
            "Operation: expose the hidden criterion.\n"
            "Result: the burden landed.\n"
            "State/noetic re-read\n"
            "- burden landed: neutrality criterion exposed.\n"
            "- What changed / cumulative-state delta: first burden narrowed.\n"
            "- Release status: continuation licensed.\n\n"
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: moral burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular morality.\n"
            "Operation: expose the hidden criterion.\n"
            "Result: the burden landed.\n"
            "State/noetic re-read\n"
            "- burden landed: morality criterion exposed.\n"
            "- What changed / cumulative-state delta: second burden narrowed.\n"
            "- Release status: continuation licensed.\n\n"
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: autonomy burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular autonomy.\n"
            "Operation: expose the hidden criterion.\n"
            "Result: the burden landed.\n"
            "State/noetic re-read\n"
            "- burden landed: autonomy criterion exposed.\n"
            "- What changed / cumulative-state delta: third burden narrowed.\n"
            "- Release status: closed for this input.\n\n"
            + ("case-specific filler placeholder " * 900)
        ),
        "verdict": "- fixture class: hard\n- status: PASS\n- burden-cycle count: 3\n",
        "expected": "hard PASS has non-atomic burden sections without multi-submove support",
    },
    "known_complex_atomic_escape": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": (
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: neutrality burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular neutrality.\n"
            "Operation: expose the hidden criterion.\n"
            "Result: the burden landed.\n"
            "State/noetic re-read\n"
            "- burden landed: neutrality criterion exposed.\n"
            "- What changed / cumulative-state delta: first burden narrowed.\n"
            "- Release status: continuation licensed.\n\n"
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: moral burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular morality.\n"
            "Operation: expose the hidden criterion.\n"
            "Result: the burden landed.\n"
            "State/noetic re-read\n"
            "- burden landed: morality criterion exposed.\n"
            "- What changed / cumulative-state delta: second burden narrowed.\n"
            "- Release status: closed for this input.\n\n"
            + ("case-specific filler placeholder " * 900)
        ),
        "verdict": "- fixture class: hard\n- status: PASS\n- burden-cycle count: 2\n- all burdens atomic: yes\n",
        "expected": "known complex or multi-cycle hard PASS cannot use all-burdens-atomic escape",
    },
    "label_only_operation_pass": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": (
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: neutrality burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular neutrality.\n"
            "Operation: use M1-self-refutation.\n"
            "Result: M1-self-refutation label used.\n"
            "Target: secular morality.\n"
            "Operation: invoke V2-reconstituting-reason.\n"
            "Result: V2-reconstituting-reason label invoked.\n"
            "State/noetic re-read\n"
            "- burden landed: neutrality criterion exposed.\n"
            "- What changed / cumulative-state delta: first burden narrowed.\n"
            "- Release status: continuation licensed.\n\n"
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: authority burden\n"
            "Layer B - bounded governed response\n"
            "Target: authority standard.\n"
            "Operation: use M8-reductio.\n"
            "Result: M8-reductio label used.\n"
            "Target: fitrah repair.\n"
            "Operation: invoke P1-fitrah-restoration.\n"
            "Result: P1-fitrah-restoration label invoked.\n"
            "State/noetic re-read\n"
            "- burden landed: authority criterion exposed.\n"
            "- What changed / cumulative-state delta: second burden narrowed.\n"
            "- Release status: closed for this input.\n\n"
            + ("case-specific filler placeholder " * 900)
        ),
        "verdict": "- fixture class: hard\n- status: PASS\n- burden-cycle count: 2\n",
        "trace": "- owner-body evidence: compiled bundle sections available\n",
        "expected": "hard PASS contains label-only operation or result line",
    },
    "owner_label_without_floor_evidence": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": VALID_HARD_SAMPLE_OUTPUT,
        "verdict": "- fixture class: hard\n- status: PASS\n- burden-cycle count: 2\n",
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- owner-body evidence: compiled bundle sections available\n"
        ),
        "expected": "hard PASS lacks owner-floor or compiled-floor execution evidence",
    },
    "owner_floor_negative_field_forbidden": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": VALID_HARD_SAMPLE_OUTPUT,
        "verdict": "- fixture class: hard\n- status: PASS\n- burden-cycle count: 2\n",
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- owner-body evidence: compiled bundle sections available\n"
            "- owner-floor evidence: no\n"
        ),
        "expected": "hard PASS lacks owner-floor or compiled-floor execution evidence",
    },
    "generic_owner_floor_evidence_forbidden": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": VALID_HARD_SAMPLE_OUTPUT,
        "verdict": "- fixture class: hard\n- status: PASS\n- burden-cycle count: 2\n",
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- owner-body evidence: compiled bundle sections available\n"
            "- owner-floor evidence: output-visible Target/Operation/Result submoves counted where present\n"
        ),
        "expected": "hard PASS uses generic owner-floor evidence wording",
    },
    "wrapper_pass_without_wrapper_disclosure": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": VALID_HARD_SAMPLE_OUTPUT,
        "verdict": "- fixture class: hard\n- status: PASS\n- burden-cycle count: 2\n",
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: diagnostic-hard-depth\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- wrapper used: yes\n"
            "- owner-body evidence: compiled bundle sections available\n"
            "- owner-floor evidence: owner-floor execution output-visible\n"
        ),
        "expected": "wrapper-dependent hard PASS lacks wrapper-dependence disclosure",
    },
    "selected_operator_cosplay": {
        "fixture": "13-attribute-tawil-dalalah-modality-hard",
        "input": "Attributes must be metaphors.",
        "output": "The selected operator is not a decorative label. Its target is the live hinge. Its operation is to apply the owner floor. Its result is a real state change.\n",
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "expected": "scaffold/formula language in output",
    },
    "anti_example_rendered_as_answer": {
        "fixture": "10-richard-lael-lillard-tst-exact",
        "input": "Hard moral-protest canary smoke.",
        "output": "Burden-Cycle Compression Failure: Malformed shape: Burden 1 -> Target: imported criterion -> Operation: audit criterion -> Result: criterion changed.\n",
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "expected": "scaffold/formula language in output",
    },
    "generic_transition_padding": {
        "fixture": "18-meta-noetic-control-surface-hard",
        "input": "Modern neutrality excludes revelation.",
        "output": "If it has landed, the next burden may be released; if it has not, a new topic would only hide unfinished work.\n",
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "expected": "scaffold/formula language in output",
    },
    "generic_repaired_posture_closing": {
        "fixture": "16-ashari-maturidi-family-nonmonolith-bounded",
        "input": "Classical theology proves it.",
        "output": "The repaired posture for the ashari maturidi family nonmonolith bounded case is to let the live criterion be seen, let the bounded operation do its work, and refuse to let nearby material rush the answer.\n",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "expected": "scaffold/formula language in output",
    },
    "surface_label_template": {
        "fixture": "17-cross-frame-verbal-agreement-bounded",
        "input": "All groups use the same word.",
        "output": "A surface label or familiar topic could hide the operative noetic frame. The answer is tempted to release adjacent material before the burden lands.\n",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "expected": "scaffold/formula language in output",
    },
    "hard_depth_by_repeated_filler": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": ("### Burden-Cycle 1 - Licensed traversal detail\nThe burden remains licensed for further detail because the prompt leans on the live hinge.\n" * 220),
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "expected": "scaffold/formula language in output",
    },
    "original_hard_reclassified_without_burden_audit": {
        "fixture": "05-recursive-epistemology-exposure",
        "input": "Neutral method before revelation.",
        "output": "x" * 5000,
        "verdict": "- fixture class: bounded\n- status: PASS\n- bounded-depth exception rationale: narrow.\n",
        "trace": "",
        "expected": "bounded PASS lacks burden-completeness audit",
    },
    "named_operator_without_owner_trace": {
        "fixture": "08-evidential-evil-moral-protest-hiddenness",
        "input": "Why suffering and hiddenness?",
        "output": "##### TTP/operator trace\n- hiddenness correction: Target: certainty demand. Operation: distinguish guidance from coercive disclosure. Result: corrected.",
        "verdict": "- fixture class: bounded\n- status: PASS\n- bounded-depth exception rationale: narrow.\n- bounded-complete\n- original hard intent: yes\n- first-order burdens handled: hiddenness\n- second-order burdens handled: criterion\n- higher-order burdens handled: tribunal\n- held burdens and why: full theodicy held by register\n- skipped licensed burdens: none\n- another pass licensed: no\n- under-20 rationale: complete.\n- not suitable as a hard-depth smoke\n",
        "trace": "- atomics/skill/references/diagnostics/foreign-premise-detection.md\n",
        "expected": "operator owner not loaded",
    },
    "owner_body_not_loaded_pass_forbidden": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "PARTIAL / OWNER-BODY-NOT-LOADED: missing V2-reconstituting-reason.md.\n",
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- owner-body evidence: OWNER-BODY-NOT-LOADED\n",
        "expected": "PASS smoke cannot claim OWNER-BODY-NOT-LOADED",
    },
    "owner_body_not_loaded_partial_allowed": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "PARTIAL / OWNER-BODY-NOT-LOADED: missing V2-reconstituting-reason.md, so no generic V2 submove is rendered.\n",
        "verdict": "- fixture class: hard\n- status: PARTIAL\n",
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- owner-body evidence: OWNER-BODY-NOT-LOADED\n"
        ),
        "expected_pass": True,
    },
    "owner_floor_hard_pass_allowed": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": VALID_HARD_SAMPLE_OUTPUT,
        "verdict": "- fixture class: hard\n- status: PASS\n- burden-cycle count: 2\n",
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- owner-body evidence: compiled bundle sections available\n"
            "- owner-floor evidence: owner-floor execution output-visible\n"
        ),
        "expected_pass": True,
    },
    "wrapper_dependent_pass_allowed": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": VALID_HARD_SAMPLE_OUTPUT,
        "verdict": (
            "- fixture class: hard\n"
            "- status: PASS\n"
            "- burden-cycle count: 2\n"
            "- whether output is skill-native or wrapper-dependent: diagnostic control; wrapper-dependent and not pure/native proof\n"
        ),
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: diagnostic-hard-depth\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- wrapper used: yes\n"
            "- owner-body evidence: compiled bundle sections available\n"
            "- owner-floor evidence: owner-floor execution output-visible\n"
        ),
        "expected_pass": True,
    },
    "hard_partial_with_missing_state_allowed": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": (
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: neutrality burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular neutrality.\n"
            "Operation: expose the hidden criterion.\n"
            "Result: neutrality is no longer neutral.\n"
            "State/noetic re-read\n"
            "- burden landed: neutrality criterion exposed.\n"
            "- What changed / cumulative-state delta: first burden narrowed.\n"
            "- Release status: continuation licensed.\n"
        ),
        "verdict": (
            "- fixture class: hard\n"
            "- status: PARTIAL\n"
            "- PARTIAL reason: under hard-depth floor\n"
            "- missing state: CONTINUED\n"
            "- next live burden: authority-order burden\n"
            "- another pass licensed: yes\n"
        ),
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
        ),
        "expected_pass": True,
    },
    "hard_fail_without_chain_state": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "Unable to validate this smoke.\n",
        "verdict": "- fixture class: hard\n- status: FAIL\n- verdict reason: failed smoke\n",
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
        ),
        "expected": "hard FAIL lacks failed execution-chain state",
    },
    "hard_fail_with_chain_state_allowed": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "Unable to validate this smoke.\n",
        "verdict": (
            "- fixture class: hard\n"
            "- status: FAIL\n"
            "- verdict reason: output lacked direct-copy provenance and could not be scored.\n"
            "- failed execution-chain link: RETRIEVAL\n"
        ),
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
        ),
        "expected_pass": True,
    },
    "hard_partial_without_next_live": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": (
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: neutrality burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular neutrality.\n"
            "Operation: expose the hidden criterion.\n"
            "Result: neutrality is no longer neutral.\n"
            "State/noetic re-read\n"
            "- burden landed: neutrality criterion exposed.\n"
            "- What changed / cumulative-state delta: first burden narrowed.\n"
            "- Release status: continuation licensed.\n"
        ),
        "verdict": "- fixture class: hard\n- status: PARTIAL\n- PARTIAL reason: under hard-depth floor\n",
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- owner-body evidence: compiled bundle sections available\n"
        ),
        "expected": "hard PARTIAL lacks next live burden",
    },
    "hard_partial_without_missing_state": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": (
            "Layer A - Compact DSL/IR header\n"
            "- live noetic burden: neutrality burden\n"
            "Layer B - bounded governed response\n"
            "Target: secular neutrality.\n"
            "Operation: expose the hidden criterion.\n"
            "Result: neutrality is no longer neutral.\n"
            "State/noetic re-read\n"
            "- burden landed: neutrality criterion exposed.\n"
            "- What changed / cumulative-state delta: first burden narrowed.\n"
            "- Release status: continuation licensed.\n"
        ),
        "verdict": (
            "- fixture class: hard\n"
            "- status: PARTIAL\n"
            "- PARTIAL reason: under hard-depth floor\n"
            "- next live burden: authority-order burden\n"
            "- another pass licensed: yes\n"
        ),
        "trace": (
            "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n"
            "- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n"
            "- release-artifact relation: post-expansion-regression\n"
            "- current-release evidence: no\n"
            "- model/host: Codex\n"
            "- invocation mode: default\n"
            "- prompt: see input.md\n"
            "- run timestamp: 2026-05-07T00:00:00Z\n"
            "- live-run vs handcrafted-regression classification: live-run\n"
            "- smoke provenance mode: live-run\n"
            "- output.md relation: direct-copied model/skill output\n"
            "- formatting-safe normalization: none\n"
            "- owner-body evidence: compiled bundle sections available\n"
        ),
        "expected": "hard PARTIAL lacks missing execution state",
    },
    "missing_package_hash": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "missing package SHA256 provenance",
    },
    "malformed_package_hash": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: not-a-hash\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "malformed package SHA256 provenance",
    },
    "current_release_hash_mismatch_without_marker": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "package SHA256 differs from release artifact without historical-regression marker",
    },
    "historical_hash_without_classification": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": f"- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- current source package SHA256: {DEFAULT_RELEASE_PACKAGE_SHA256}\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "package SHA256 differs from release artifact without historical-regression marker",
    },
    "package_filename_mismatch": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": f"- package filename: wrong-RC.skill.zip\n- package SHA256: {DEFAULT_RELEASE_PACKAGE_SHA256}\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "package filename differs from release artifact",
    },
    "ambiguous_current_and_historical_claims": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- release-artifact relation: historical-regression\n- current-release evidence: yes\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "ambiguous current-release and historical-regression provenance",
    },
    "current_release_claim_with_mismatching_sha": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- current-release evidence: yes\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "current-release provenance carries non-current package SHA256",
    },
    "current_release_relation_with_mismatching_sha": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": f"- package filename: {DEFAULT_RELEASE_PACKAGE_FILENAME}\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: current-release\n- current-release evidence: yes\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "current-release provenance carries non-current package SHA256",
    },
    "historical_marker_missing_current_source_sha": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": f"- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- release-artifact relation: historical-regression\n- current-release evidence: no\n- current source package filename: {DEFAULT_RELEASE_PACKAGE_FILENAME}\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "historical smoke lacks current source package SHA256",
    },
    "missing_package_filename": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": f"- package SHA256: {DEFAULT_RELEASE_PACKAGE_SHA256}\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "missing package filename provenance",
    },
    "historical_hash_with_marker_allowed": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": VALID_HARD_SAMPLE_OUTPUT,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": f"- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- release-artifact relation: historical-regression\n- current-release evidence: no\n- current source package filename: {DEFAULT_RELEASE_PACKAGE_FILENAME}\n- current source package SHA256: {DEFAULT_RELEASE_PACKAGE_SHA256}\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n- owner-body evidence: compiled bundle sections available\n- owner-floor evidence: owner-floor execution output-visible\n",
        "expected_pass": True,
    },
    "post_expansion_regression_marker_allowed": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "## Burden-Cycle 1\n### State/noetic re-read\n- What changed / cumulative-state delta: authority-order burden identified.\n- Release status: remains open for later hard-depth traversal.\n",
        "verdict": (
            "- fixture class: hard\n"
            "- status: PARTIAL\n"
            "- smoke provenance mode: handcrafted-regression\n"
            "- PARTIAL reason: handcrafted post-expansion marker sample remains under hard-depth.\n"
            "- missing state: CONTINUED\n"
            "- next live burden: authority-order burden.\n"
            "- another pass licensed: yes\n"
        ),
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: handcrafted-regression\n- smoke provenance mode: handcrafted-regression\n",
        "expected_pass": True,
    },
    "post_expansion_missing_smoke_mode": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: handcrafted-regression\n",
        "expected": "missing smoke provenance mode",
    },
    "handcrafted_claims_live_run": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n- smoke provenance mode: handcrafted-regression\n",
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n- smoke provenance mode: handcrafted-regression\n",
        "expected": "handcrafted-regression mode conflicts with live-run classification",
    },
    "handcrafted_claims_skill_loaded": {
        "fixture": "11-refute-secularism-hard",
        "input": "Refute secularism.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n- smoke provenance mode: handcrafted-regression\n",
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: handcrafted-regression\n- smoke provenance mode: handcrafted-regression\n- SKILL.md loaded: yes\n",
        "expected": "handcrafted-regression cannot claim SKILL.md loaded: yes",
    },
    "live_run_without_direct_copy_relation": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": f"- package filename: {DEFAULT_RELEASE_PACKAGE_FILENAME}\n- package SHA256: {DEFAULT_RELEASE_PACKAGE_SHA256}\n- release-artifact relation: current-release\n- current-release evidence: yes\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n- smoke provenance mode: live-run\n",
        "expected": "live-run mode lacks direct-copied output relation",
    },
    "live_run_without_formatting_normalization": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": f"- package filename: {DEFAULT_RELEASE_PACKAGE_FILENAME}\n- package SHA256: {DEFAULT_RELEASE_PACKAGE_SHA256}\n- release-artifact relation: current-release\n- current-release evidence: yes\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n- smoke provenance mode: live-run\n- output.md relation: direct-copied model/skill output\n",
        "expected": "live-run mode lacks formatting-safe normalization note",
    },
    "synthetic_output_prohibited_cannot_pass": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n- smoke provenance mode: synthetic-output-prohibited\n",
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: handcrafted-regression\n- smoke provenance mode: synthetic-output-prohibited\n",
        "expected": "synthetic-output-prohibited cannot be PASS or PARTIAL evidence",
    },
    "pending_live_output_cannot_pass": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "# Pending Live Output\nPaste direct model output here.\n",
        "verdict": "- fixture class: hard\n- status: PASS\n- smoke provenance mode: pending-live-output\n",
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: pending\n- invocation mode: pending user/model paste\n- prompt: see input.md\n- run timestamp: pending-live-output\n- live-run vs handcrafted-regression classification: pending\n- smoke provenance mode: pending-live-output\n",
        "expected": "pending-live-output cannot be PASS or PARTIAL evidence",
    },
    "hermes_live_needs_review_allowed": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "Direct captured output awaiting review.\n",
        "verdict": "- fixture class: hard\n- status: NEEDS_REVIEW\n- smoke provenance mode: live-run/hermes-local\n",
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: Hermes local / test-model\n- endpoint: http://127.0.0.1:8000/v1/chat/completions\n- skill source: generated skill/ from commit 0000000\n- invocation mode: Hermes live smoke runner\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n- smoke provenance mode: live-run/hermes-local\n- output capture: direct-copy\n- output.md relation: direct-copied model/skill output\n- formatting-safe normalization: none\n",
        "expected_pass": True,
    },
    "hard_pass_handcrafted_without_golden_regression": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n- smoke provenance mode: handcrafted-regression\n",
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: handcrafted-regression\n- smoke provenance mode: handcrafted-regression\n",
        "expected": "hard PASS handcrafted-regression requires golden-regression and golden-quality markers",
    },
    "pass_with_compact_artifact_phrase": {
        "fixture": "02-unknown-misleading-denomination-pattern-first",
        "input": "Unknown label.",
        "output": "I'll handle this as a governed diagnostic response: compact label repair.\n",
        "verdict": "- fixture class: bounded\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-post-v0.3.2.0-dev.skill.zip\n- package SHA256: 1111111111111111111111111111111111111111111111111111111111111111\n- release-artifact relation: post-expansion-regression\n- current-release evidence: no\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: handcrafted-regression\n- smoke provenance mode: handcrafted-regression\n",
        "expected": "PASS smoke contains compact artifact prose",
    },
    "missing_live_run_classification": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "x" * 21000,
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n",
        "expected": "missing live-run classification provenance",
    },
    "literal_governance_label": {
        "fixture": "01-trinitarian-claim-cluster",
        "input": "Trinity hard smoke.",
        "output": "- Governance: STOP\n" + ("x" * 21000),
        "verdict": "- fixture class: hard\n- status: PASS\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "literal governance label in output",
    },
    "bounded_pass_without_output_reread_support": {
        "fixture": "04-comparative-neutral-flattening-bait",
        "input": "Compare traditions without flattening.",
        "output": "## Burden-Cycle 1\n### Layer A - Compact DSL/IR header\n### Layer B - bounded governed response\nThe answer is short.",
        "verdict": "- fixture class: bounded\n- status: PASS\n- bounded-depth exception rationale: narrow.\n- bounded-complete\n- original hard intent: yes\n- first-order burdens handled: flattening\n- second-order burdens handled: tribunal\n- higher-order burdens handled: abstraction\n- held burdens and why: taxonomy held\n- skipped licensed burdens: none\n- another pass licensed: no\n- under-20 rationale: complete.\n- not suitable as a hard-depth smoke\n- burden-cycle count: 1\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "bounded PASS output lacks State/noetic re-read",
    },
    "bounded_pass_claims_two_cycles_output_one": {
        "fixture": "04-comparative-neutral-flattening-bait",
        "input": "Compare traditions without flattening.",
        "output": "## Burden-Cycle 1\n### Layer A - Compact DSL/IR header\n### Layer B - bounded governed response\n### State/noetic re-read\n- What changed / cumulative-state delta: pattern is diagnostic data.\n- Release status: closed for this input.\n",
        "verdict": "- fixture class: bounded\n- status: PASS\n- bounded-depth exception rationale: narrow.\n- bounded-complete\n- original hard intent: yes\n- first-order burdens handled: flattening\n- second-order burdens handled: tribunal\n- higher-order burdens handled: abstraction\n- held burdens and why: taxonomy held\n- skipped licensed burdens: none\n- another pass licensed: no\n- under-20 rationale: complete.\n- not suitable as a hard-depth smoke\n- burden-cycle count: 2\n",
        "trace": "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n- model/host: Codex\n- invocation mode: default\n- prompt: see input.md\n- run timestamp: 2026-05-07T00:00:00Z\n- live-run vs handcrafted-regression classification: live-run\n",
        "expected": "bounded PASS claims more cycles than output shows",
    },
}


@dataclass(frozen=True)
class ReleaseArtifact:
    filename: str
    sha256: str


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def clean_field_value(value: str) -> str:
    return value.strip().strip("|").strip().strip("`").strip()


def extract_hash(value: str) -> str | None:
    match = HASH_64_RE.search(value)
    return match.group(0).upper() if match else None


def parse_release_artifacts_text(text: str) -> tuple[ReleaseArtifact | None, list[str]]:
    errors: list[str] = []
    filename_match = RELEASE_FILENAME_ROW_RE.search(text)
    sha_match = RELEASE_SHA_ROW_RE.search(text)
    filename = clean_field_value(filename_match.group(1)) if filename_match else ""
    if not filename:
        errors.append("release artifact evidence lacks package filename")
    elif not PACKAGE_FILENAME_CANONICAL_RE.match(filename):
        errors.append(f"release artifact package filename is malformed: {filename}")

    raw_sha = clean_field_value(sha_match.group(1)) if sha_match else ""
    sha = extract_hash(raw_sha) if raw_sha else None
    if not raw_sha:
        errors.append("release artifact evidence lacks current package SHA256")
    elif not sha:
        errors.append("release artifact evidence has malformed current package SHA256")
    if errors:
        return None, errors
    return ReleaseArtifact(filename=filename, sha256=sha or ""), []


def parse_release_artifacts(path: Path) -> tuple[ReleaseArtifact | None, list[str]]:
    if not path.exists():
        return None, [f"release artifact evidence file is absent: {path}"]
    return parse_release_artifacts_text(read(path))


def smoke_package_filename(text: str) -> str | None:
    match = SMOKE_FILENAME_LINE_RE.search(text)
    return clean_field_value(match.group(1)) if match else None


def smoke_package_sha(text: str) -> tuple[str | None, bool]:
    match = SMOKE_SHA_LINE_RE.search(text)
    if not match:
        return None, False
    value = clean_field_value(match.group(1))
    sha = extract_hash(value)
    return sha, bool(sha)


def is_current_release_provenance(text: str, release_artifact: ReleaseArtifact) -> bool:
    filename = smoke_package_filename(text)
    sha, sha_valid = smoke_package_sha(text)
    return (
        bool(RELATION_CURRENT_RE.search(text))
        and bool(EVIDENCE_YES_RE.search(text))
        and filename == release_artifact.filename
        and sha_valid
        and sha == release_artifact.sha256
    )


def fixture_class(verdict: str) -> str:
    match = re.search(r"(?im)^\s*-\s*fixture class\s*:\s*(hard|bounded)\b", verdict)
    return match.group(1).lower() if match else "missing"


def verdict_status(verdict: str) -> str:
    match = re.search(r"(?im)^\s*-\s*status\s*:\s*(PASS|PARTIAL|FAIL|NEEDS_REVIEW)\b", verdict)
    return match.group(1).upper() if match else "MISSING"


def allowed_patterns(fixture_name: str, input_text: str) -> tuple[re.Pattern[str], ...]:
    text = (fixture_name + " " + input_text).lower()
    allowed: list[re.Pattern[str]] = []
    for token, patterns in FIXTURE_ALLOWANCES.items():
        if token in text:
            allowed.extend(patterns)
    # Content-shaped allowances keep historical hard canaries from depending on
    # named-person or movement-specific fixture paths.
    for pattern in (ACCOUNTABILITY_TERMS_RE, MORAL_PROTEST_TERMS_RE, WORSHIP_WORTHINESS_TERMS_RE):
        if pattern.search(input_text):
            allowed.append(pattern)
    return tuple(allowed)


def contamination_errors(fixture_name: str, input_text: str, output_text: str) -> list[str]:
    errors: list[str] = []
    allowed = allowed_patterns(fixture_name, input_text)
    checks = [
        ("fixture contamination: source-worldview canary/source-label terms", SOURCE_WORLDVIEW_CANARY_TERMS_RE),
        ("fixture contamination: accountability/punishment terms", ACCOUNTABILITY_TERMS_RE),
        ("fixture contamination: moral-protest/hiddenness terms", MORAL_PROTEST_TERMS_RE),
        ("fixture contamination: worship-worthiness terms", WORSHIP_WORTHINESS_TERMS_RE),
    ]
    for label, pattern in checks:
        if pattern.search(output_text) and pattern not in allowed:
            errors.append(label)
    return errors


def bounded_completeness_errors(fixture_name: str, verdict_text: str) -> list[str]:
    errors: list[str] = []
    verdict_lower = verdict_text.lower()
    cls = fixture_class(verdict_text)
    status = verdict_status(verdict_text)
    if cls != "bounded" or status != "PASS":
        return errors
    missing = [field for field in BOUNDED_COMPLETENESS_FIELDS if field not in verdict_lower]
    if missing:
        errors.append("bounded PASS lacks burden-completeness audit")
    if fixture_name in ORIGINALLY_HARD_INTENDED:
        if "original hard intent: yes" not in verdict_lower:
            errors.append("originally hard-intended bounded PASS lacks original-hard marker")
        if "not suitable as a hard-depth smoke" not in verdict_lower:
            errors.append("originally hard-intended bounded PASS lacks hard-depth unsuitability note")
    return errors


def bounded_output_support_errors(output_text: str, verdict_text: str) -> list[str]:
    errors: list[str] = []
    cls = fixture_class(verdict_text)
    status = verdict_status(verdict_text)
    if cls != "bounded" or status != "PASS":
        return errors

    visible_cycles = len(BURDEN_CYCLE_RE.findall(output_text))
    if visible_cycles < 1:
        errors.append("bounded PASS output lacks burden-cycle section")
    if not STATE_REREAD_RE.search(output_text):
        errors.append("bounded PASS output lacks State/noetic re-read")
    if not RELEASE_STATUS_PROSE_RE.search(output_text):
        errors.append("bounded PASS output lacks prose Release status")
    if not CUMULATIVE_DELTA_RE.search(output_text):
        errors.append("bounded PASS output lacks cumulative-state delta")

    cycle_match = VERDICT_CYCLE_COUNT_RE.search(verdict_text)
    if not cycle_match:
        errors.append("bounded PASS verdict lacks burden-cycle count")
    elif int(cycle_match.group(1)) > visible_cycles:
        errors.append("bounded PASS claims more cycles than output shows")
    return errors


def trace_errors(output_text: str, trace_text: str) -> list[str]:
    errors: list[str] = []
    if owner_body_not_loaded_claim(f"{output_text}\n{trace_text}"):
        return errors
    trace_lower = trace_text.lower()
    for pattern, owner in TRACE_REQUIREMENTS:
        if pattern.search(output_text) and owner.lower() not in trace_lower:
            errors.append(f"operator owner not loaded: {owner}")
    return errors


def release_artifact_consistency_errors(
    trace_text: str,
    verdict_text: str,
    release_artifact: ReleaseArtifact | None,
) -> list[str]:
    if release_artifact is None:
        return []
    errors: list[str] = []
    provenance_text = f"{trace_text}\n{verdict_text}"
    filename = smoke_package_filename(provenance_text)
    sha, sha_valid = smoke_package_sha(provenance_text)
    relation_current = bool(RELATION_CURRENT_RE.search(provenance_text))
    evidence_yes = bool(EVIDENCE_YES_RE.search(provenance_text))
    relation_historical = bool(RELATION_HISTORICAL_RE.search(provenance_text))
    relation_post_expansion = bool(RELATION_POST_EXPANSION_RE.search(provenance_text))
    evidence_no = bool(EVIDENCE_NO_RE.search(provenance_text))
    historical = relation_historical
    current = relation_current or evidence_yes
    non_current_relation = relation_historical or relation_post_expansion

    if not filename:
        errors.append("missing package filename provenance")
    elif filename != release_artifact.filename and not non_current_relation:
        errors.append("package filename differs from release artifact")
    if sha is None:
        if SMOKE_SHA_LINE_RE.search(provenance_text):
            errors.append("malformed package SHA256 provenance")
    elif not sha_valid:
        errors.append("malformed package SHA256 provenance")

    if historical and current:
        errors.append("ambiguous current-release and historical-regression provenance")
    if relation_post_expansion and current:
        errors.append("ambiguous current-release and post-expansion-regression provenance")
    if relation_current and not evidence_yes:
        errors.append("current-release relation missing current-release evidence: yes")
    if evidence_yes and not relation_current:
        errors.append("current-release evidence: yes missing release-artifact relation: current-release")
    if relation_historical and not evidence_no:
        errors.append("historical-regression relation missing current-release evidence: no")
    if relation_post_expansion and not evidence_no:
        errors.append("post-expansion-regression relation missing current-release evidence: no")
    if evidence_no and not non_current_relation:
        errors.append("current-release evidence: no missing non-current release-artifact relation")
    if current and sha and sha != release_artifact.sha256:
        errors.append("current-release provenance carries non-current package SHA256")
    if sha and sha != release_artifact.sha256 and not (historical or relation_post_expansion):
        errors.append("package SHA256 differs from release artifact without historical-regression marker")
    if historical:
        current_source_filename_match = CURRENT_PACKAGE_FILENAME_LINE_RE.search(provenance_text)
        current_source_filename = clean_field_value(current_source_filename_match.group(1)) if current_source_filename_match else None
        if not current_source_filename:
            errors.append("historical smoke lacks current source package filename")
        elif not PACKAGE_FILENAME_CANONICAL_RE.match(current_source_filename):
            errors.append("historical smoke current source package filename is malformed")
        current_source_match = CURRENT_PACKAGE_SHA_LINE_RE.search(provenance_text)
        current_source_hash = extract_hash(clean_field_value(current_source_match.group(1))) if current_source_match else None
        if not current_source_hash:
            errors.append("historical smoke lacks current source package SHA256")
    return errors


def current_release_requirement_errors(root: Path, release_artifact: ReleaseArtifact) -> list[str]:
    errors: list[str] = []
    if not root.exists():
        return [f"current-release smoke root is absent: {root}"]

    hard_current_passes = 0
    bounded_current_passes = 0
    fixture_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    for directory in fixture_dirs:
        input_text = read(directory / "input.md")
        output_text = read(directory / "output.md")
        trace_text = read(directory / "trace.md")
        verdict_text = read(directory / "verdict.md")
        provenance = f"{trace_text}\n{verdict_text}"
        status = verdict_status(verdict_text)
        cls = fixture_class(verdict_text)

        if not is_current_release_provenance(provenance, release_artifact):
            continue

        artifact_errors = validate_artifact(
            directory.name,
            input_text,
            output_text,
            verdict_text,
            trace_text,
            release_artifact=release_artifact,
        )
        if not (directory / "ir.json").is_file():
            artifact_errors.append("current-release PASS smoke missing ir.json")
        for error in artifact_errors:
            errors.append(f"{directory.name}: {error}")
        if artifact_errors or status != "PASS":
            continue
        if cls == "hard":
            hard_current_passes += 1
        elif cls == "bounded":
            bounded_current_passes += 1

    if hard_current_passes < 1:
        errors.append("require-current-release-smokes: no hard current-release PASS smoke with ir.json")
    if bounded_current_passes < 1:
        errors.append("require-current-release-smokes: no bounded current-release PASS smoke with ir.json")
    return errors


def provenance_errors(
    trace_text: str,
    verdict_text: str,
    release_artifact: ReleaseArtifact | None = None,
) -> list[str]:
    errors: list[str] = []
    provenance_text = f"{trace_text}\n{verdict_text}"
    provenance = provenance_text.lower()
    for field in PROVENANCE_FIELDS:
        if field not in provenance:
            errors.append(f"missing provenance field: {field}")
    if not PACKAGE_HASH_RE.search(provenance_text):
        if SMOKE_SHA_LINE_RE.search(provenance_text):
            errors.append("malformed package SHA256 provenance")
        else:
            errors.append("missing package SHA256 provenance")
    classification_match = CLASSIFICATION_VALUE_RE.search(provenance_text)
    classification = classification_match.group(1).lower() if classification_match else ""
    if not LIVE_RUN_RE.search(provenance_text):
        errors.append("missing live-run classification provenance")

    relation_current = bool(RELATION_CURRENT_RE.search(provenance_text))
    evidence_yes = bool(EVIDENCE_YES_RE.search(provenance_text))
    relation_post_expansion = bool(RELATION_POST_EXPANSION_RE.search(provenance_text))
    mode_match = SMOKE_PROVENANCE_MODE_RE.search(provenance_text)
    mode = mode_match.group(1).lower() if mode_match else ""
    mode_required = relation_current or evidence_yes or relation_post_expansion or bool(mode_match)
    if mode_required and not mode:
        errors.append("missing smoke provenance mode")
    if mode in {"live-run", "live-run/hermes-local"}:
        if classification and classification != "live-run":
            errors.append("live-run mode conflicts with handcrafted-regression classification")
        if not DIRECT_COPIED_OUTPUT_RE.search(provenance_text):
            errors.append("live-run mode lacks direct-copied output relation")
        if not FORMAT_NORMALIZATION_RE.search(provenance_text):
            errors.append("live-run mode lacks formatting-safe normalization note")
    elif mode == "handcrafted-regression":
        if classification and classification != "handcrafted-regression":
            errors.append("handcrafted-regression mode conflicts with live-run classification")
        if "handcrafted-regression" not in verdict_text.lower():
            errors.append("handcrafted-regression mode missing verdict declaration")
        if SKILL_LOADED_YES_RE.search(provenance_text):
            errors.append("handcrafted-regression cannot claim SKILL.md loaded: yes")
    elif mode == "pending-live-output":
        if classification and classification != "pending":
            errors.append("pending-live-output mode conflicts with non-pending classification")
        if verdict_status(verdict_text) in {"PASS", "PARTIAL"}:
            errors.append("pending-live-output cannot be PASS or PARTIAL evidence")
    elif mode == "synthetic-output-prohibited":
        if verdict_status(verdict_text) in {"PASS", "PARTIAL"}:
            errors.append("synthetic-output-prohibited cannot be PASS or PARTIAL evidence")
    errors.extend(release_artifact_consistency_errors(trace_text, verdict_text, release_artifact))
    return errors


def paragraph_fingerprints(output_text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", output_text)]
    clean = []
    for part in parts:
        normalized = re.sub(r"\s+", " ", part)
        if len(normalized) >= 90 and not normalized.startswith(("#", "-", "##")):
            clean.append(normalized.lower())
    return clean


def visible_burden_sections(output_text: str) -> list[str]:
    """Return visible burden sections without requiring one exact heading style."""
    starts = list(BURDEN_START_RE.finditer(output_text))
    if not starts:
        starts = list(LAYER_A_START_RE.finditer(output_text))
    sections: list[str] = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(output_text)
        sections.append(output_text[match.start():end])
    return sections


def operation_unit_count(section: str) -> int:
    triplets = min(
        len(TARGET_LINE_RE.findall(section)),
        len(OPERATION_LINE_RE.findall(section)),
        len(RESULT_LINE_RE.findall(section)),
    )
    return max(triplets, len(SUBMOVE_MARKER_RE.findall(section)))


def owner_body_not_loaded_claim(text: str) -> bool:
    """Return true for an actual owner-load failure marker, not a negated verdict field."""
    without_negated_lines = OWNER_BODY_NOT_LOADED_NEGATED_LINE_RE.sub("", text)
    return bool(OWNER_BODY_NOT_LOADED_RE.search(without_negated_lines))


def hard_output_support_errors(fixture_name: str, output_text: str, verdict_text: str) -> list[str]:
    errors: list[str] = []
    if fixture_class(verdict_text) != "hard" or verdict_status(verdict_text) != "PASS":
        return errors

    if LABEL_ONLY_OPERATION_RE.search(output_text) or LABEL_ONLY_RESULT_RE.search(output_text):
        errors.append("hard PASS contains label-only operation or result line")

    sections = visible_burden_sections(output_text)
    cycle_match = VERDICT_CYCLE_COUNT_RE.search(verdict_text)
    claimed_cycles = int(cycle_match.group(1)) if cycle_match else 0
    expected_cycles = claimed_cycles or len(sections)

    if claimed_cycles and len(sections) < claimed_cycles:
        errors.append("hard PASS claims more cycles than output visibly supports")
    if not sections:
        errors.append("hard PASS output lacks visible burden-cycle or Layer A sections")
    if fixture_name in KNOWN_COMPLEX_HARD_FIXTURES and expected_cycles < 2:
        errors.append("known complex hard PASS lacks multiple visible burden cycles")

    rereads = len(STATE_REREAD_RE.findall(output_text))
    if expected_cycles and rereads < expected_cycles:
        errors.append("hard PASS lacks State/noetic re-read for every claimed burden")

    landings = len(LANDING_RE.findall(output_text))
    if expected_cycles and landings < expected_cycles:
        errors.append("hard PASS lacks visible burden landing for every claimed burden")

    unit_counts = [operation_unit_count(section) for section in sections]
    global_atomic = bool(ATOMIC_BURDEN_EXPLANATION_RE.search(verdict_text))
    if global_atomic and (fixture_name in KNOWN_COMPLEX_HARD_FIXTURES or expected_cycles > 1):
        errors.append("known complex or multi-cycle hard PASS cannot use all-burdens-atomic escape")
        global_atomic = False
    if sections and not global_atomic:
        section_atomic = [bool(SECTION_ATOMIC_RE.search(section)) for section in sections]
        weak_sections = [
            index + 1
            for index, (count, atomic) in enumerate(zip(unit_counts, section_atomic))
            if count < 2 and not atomic
        ]
        if weak_sections:
            errors.append(
                "hard PASS has non-atomic burden sections without multi-submove support: "
                + ", ".join(str(index) for index in weak_sections)
            )
    if fixture_name in KNOWN_COMPLEX_HARD_FIXTURES and sections and not any(count >= 2 for count in unit_counts):
        errors.append("known complex hard PASS lacks a complex burden with multiple operative units")
    if sections and any(count == 0 for count in unit_counts):
        errors.append("hard PASS has a visible burden without target-operation-result support")
    return errors


def hard_execution_state_errors(output_text: str, verdict_text: str, trace_text: str) -> list[str]:
    errors: list[str] = []
    if fixture_class(verdict_text) != "hard" or verdict_status(verdict_text) != "PASS":
        return errors

    combined = f"{output_text}\n{trace_text}\n{verdict_text}"
    if GENERIC_OWNER_FLOOR_EVIDENCE_RE.search(combined):
        errors.append("hard PASS uses generic owner-floor evidence wording")
    if not OWNER_FLOOR_EVIDENCE_RE.search(combined):
        errors.append("hard PASS lacks owner-floor or compiled-floor execution evidence")
    if WRAPPER_PRESSURE_RE.search(combined) and not WRAPPER_HONESTY_RE.search(combined):
        errors.append("wrapper-dependent hard PASS lacks wrapper-dependence disclosure")
    return errors


def partial_honesty_errors(output_text: str, verdict_text: str, trace_text: str) -> list[str]:
    errors: list[str] = []
    if fixture_class(verdict_text) != "hard" or verdict_status(verdict_text) != "PARTIAL":
        return errors

    combined = f"{output_text}\n{trace_text}\n{verdict_text}"
    if owner_body_not_loaded_claim(combined):
        return errors

    if not PARTIAL_REASON_RE.search(verdict_text):
        errors.append("hard PARTIAL lacks explicit partial reason")
    if not PARTIAL_NEXT_LIVE_RE.search(verdict_text):
        errors.append("hard PARTIAL lacks next live burden")
    if not PARTIAL_MISSING_STATE_RE.search(verdict_text):
        errors.append("hard PARTIAL lacks missing execution state")
    if not PARTIAL_ANOTHER_PASS_RE.search(verdict_text):
        errors.append("hard PARTIAL lacks another pass licensed judgment")
    if not visible_burden_sections(output_text) and not LANDING_RE.search(output_text):
        errors.append("hard PARTIAL lacks visible burden work or landing evidence")
    return errors


def fail_honesty_errors(verdict_text: str, trace_text: str) -> list[str]:
    errors: list[str] = []
    if fixture_class(verdict_text) != "hard" or verdict_status(verdict_text) != "FAIL":
        return errors

    provenance_text = f"{trace_text}\n{verdict_text}"
    mode_match = SMOKE_PROVENANCE_MODE_RE.search(provenance_text)
    mode = mode_match.group(1).lower() if mode_match else ""
    if mode in {"pending-live-output", "synthetic-output-prohibited"}:
        return errors

    if not FAIL_REASON_RE.search(verdict_text):
        errors.append("hard FAIL lacks explicit failure reason")
    if not PARTIAL_MISSING_STATE_RE.search(verdict_text) and not owner_body_not_loaded_claim(provenance_text):
        errors.append("hard FAIL lacks failed execution-chain state")
    return errors


def validate_artifact(
    fixture_name: str,
    input_text: str,
    output_text: str,
    verdict_text: str,
    trace_text: str = "",
    global_fixtures: dict[str, set[str]] | None = None,
    release_artifact: ReleaseArtifact | None = None,
) -> list[str]:
    errors: list[str] = []
    cls = fixture_class(verdict_text)
    status = verdict_status(verdict_text)
    size = len(output_text.encode("utf-8"))

    if cls == "missing":
        errors.append("missing fixture class")
    if status == "MISSING":
        errors.append("missing verdict status")
    if cls == "hard" and status == "PASS" and size < HARD_MIN_BYTES:
        errors.append("hard smoke PASS under depth floor")
    provenance_text = f"{trace_text}\n{verdict_text}"
    mode_match = SMOKE_PROVENANCE_MODE_RE.search(provenance_text)
    mode = mode_match.group(1).lower() if mode_match else ""
    if (
        cls == "hard"
        and status == "PASS"
        and mode == "handcrafted-regression"
        and not (GOLDEN_REGRESSION_RE.search(verdict_text) and GOLDEN_QUALITY_RE.search(verdict_text))
    ):
        errors.append("hard PASS handcrafted-regression requires golden-regression and golden-quality markers")
    if cls == "hard" and status == "PASS" and not OWNER_BODY_EVIDENCE_RE.search(provenance_text):
        errors.append("hard PASS lacks owner-body or compiled-bundle access evidence")
    if status == "PASS" and (
        OWNER_BODY_NOT_LOADED_RE.search(output_text) or owner_body_not_loaded_claim(provenance_text)
    ):
        errors.append("PASS smoke cannot claim OWNER-BODY-NOT-LOADED")
    if status == "PASS" and COMPACT_ARTIFACT_RE.search(output_text):
        errors.append("PASS smoke contains compact artifact prose")
    if cls == "bounded" and status == "PASS" and "bounded-depth exception" not in verdict_text.lower():
        errors.append("bounded PASS lacks bounded-depth exception rationale")
    if SCAFFOLD_RE.search(output_text):
        errors.append("scaffold/formula language in output")
    if GENERIC_REUSE_RE.search(output_text):
        errors.append("reused generic paragraph")
    if status == "PASS" and LITERAL_GOVERNANCE_RE.search(output_text):
        errors.append("literal governance label in output")
    errors.extend(contamination_errors(fixture_name, input_text, output_text))
    errors.extend(bounded_completeness_errors(fixture_name, verdict_text))
    errors.extend(bounded_output_support_errors(output_text, verdict_text))
    errors.extend(hard_output_support_errors(fixture_name, output_text, verdict_text))
    errors.extend(hard_execution_state_errors(output_text, verdict_text, trace_text))
    errors.extend(partial_honesty_errors(output_text, verdict_text, trace_text))
    errors.extend(fail_honesty_errors(verdict_text, trace_text))
    if not (status != "PASS" and owner_body_not_loaded_claim(f"{output_text}\n{provenance_text}")):
        errors.extend(trace_errors(output_text, trace_text))
    errors.extend(provenance_errors(trace_text, verdict_text, release_artifact))

    if global_fixtures and not (mode == "pending-live-output" and status == "FAIL"):
        repeated = [
            text
            for text in paragraph_fingerprints(output_text)
            if len(global_fixtures[text] - {fixture_name}) > 0
        ]
        if repeated:
            errors.append("identical paragraph reused across fixture outputs")
    return errors


def validate_sidecar_artifact(
    fixture_name: str,
    input_text: str,
    output_text: str,
    verdict_text: str,
    trace_text: str = "",
) -> list[str]:
    """Validate diagnostic sidecars without treating them as release packages.

    Sidecars compare pure/rerun/control behavior against the selected artifact.
    They still need execution-honesty checks, but they are not package-bound
    smoke artifacts and commonly omit package filename/SHA provenance.
    """
    errors: list[str] = []
    cls = fixture_class(verdict_text)
    status = verdict_status(verdict_text)
    size = len(output_text.encode("utf-8"))

    if cls == "missing":
        errors.append("missing fixture class")
    if status == "MISSING":
        errors.append("missing verdict status")
    if cls == "hard" and status == "PASS" and size < HARD_MIN_BYTES:
        errors.append("hard smoke PASS under depth floor")

    provenance_text = f"{trace_text}\n{verdict_text}"
    if cls == "hard" and status == "PASS" and not OWNER_BODY_EVIDENCE_RE.search(provenance_text):
        errors.append("hard PASS lacks owner-body or compiled-bundle access evidence")
    if status == "PASS" and (
        OWNER_BODY_NOT_LOADED_RE.search(output_text) or owner_body_not_loaded_claim(provenance_text)
    ):
        errors.append("PASS smoke cannot claim OWNER-BODY-NOT-LOADED")
    if status == "PASS" and COMPACT_ARTIFACT_RE.search(output_text):
        errors.append("PASS smoke contains compact artifact prose")
    if status == "PASS" and SCAFFOLD_RE.search(output_text):
        errors.append("scaffold/formula language in output")
    if status == "PASS" and GENERIC_REUSE_RE.search(output_text):
        errors.append("reused generic paragraph")
    if status == "PASS" and LITERAL_GOVERNANCE_RE.search(output_text):
        errors.append("literal governance label in output")

    errors.extend(bounded_completeness_errors(fixture_name, verdict_text))
    errors.extend(bounded_output_support_errors(output_text, verdict_text))
    errors.extend(hard_output_support_errors(fixture_name, output_text, verdict_text))
    errors.extend(hard_execution_state_errors(output_text, verdict_text, trace_text))
    errors.extend(partial_honesty_errors(output_text, verdict_text, trace_text))
    errors.extend(fail_honesty_errors(verdict_text, trace_text))
    return errors


def validate_root(root: Path, release_artifact: ReleaseArtifact | None = None) -> list[str]:
    errors: list[str] = []
    fixture_dirs = sorted(path for path in root.iterdir() if path.is_dir()) if root.exists() else []
    if not root.exists():
        return [
            f"smoke artifact root is absent: {root}. "
            "Create repo-local smokes/runtime-grounding-v5/ or pass --root explicitly."
        ]
    if not fixture_dirs:
        return [f"no fixture directories found under {root}"]

    all_paragraphs: dict[str, set[str]] = defaultdict(set)
    artifacts: list[tuple[str, str, str, str, str, str, bool]] = []
    for directory in fixture_dirs:
        input_text = read(directory / "input.md")
        output_text = read(directory / "output.md")
        trace_text = read(directory / "trace.md")
        verdict_text = read(directory / "verdict.md")
        artifacts.append((directory.name, directory.name, input_text, output_text, verdict_text, trace_text, False))
        for paragraph in paragraph_fingerprints(output_text):
            all_paragraphs[paragraph].add(directory.name)

        for output_path in sorted(directory.glob("output.*.md")):
            suffix = output_path.name[len("output") : -len(".md")]
            if not suffix or suffix == ".":
                continue
            trace_path = directory / f"trace{suffix}.md"
            verdict_path = directory / f"verdict{suffix}.md"
            label = f"{directory.name}{suffix}"
            if not trace_path.exists() or not verdict_path.exists():
                errors.append(f"{label}: sidecar output lacks matching trace/verdict")
                continue
            sidecar_output = read(output_path)
            sidecar_trace = read(trace_path)
            sidecar_verdict = read(verdict_path)
            artifacts.append((label, directory.name, input_text, sidecar_output, sidecar_verdict, sidecar_trace, True))

        for required in ("input.md", "output.md", "trace.md", "verdict.md"):
            if not (directory / required).exists():
                errors.append(f"{directory.name}: missing {required}")

    for artifact_label, fixture_name, input_text, output_text, verdict_text, trace_text, is_sidecar in artifacts:
        if is_sidecar:
            found_errors = validate_sidecar_artifact(
                fixture_name,
                input_text,
                output_text,
                verdict_text,
                trace_text,
            )
        else:
            found_errors = validate_artifact(
                fixture_name,
                input_text,
                output_text,
                verdict_text,
                trace_text,
                all_paragraphs,
                release_artifact,
            )
        for error in found_errors:
            errors.append(f"{artifact_label}: {error}")
    return errors


def validate_bad_samples(release_artifact: ReleaseArtifact) -> list[str]:
    errors: list[str] = []
    for name, sample in BAD_SAMPLES.items():
        found = validate_artifact(
            sample["fixture"],
            sample["input"],
            sample["output"],
            sample["verdict"],
            sample.get("trace", ""),
            release_artifact=release_artifact,
        )
        if sample.get("expected_pass"):
            if found:
                errors.append(f"historical-allowed sample {name!r} was rejected; got {found!r}")
            continue
        if not any(sample["expected"] in item for item in found):
            errors.append(
                f"bad sample {name!r} was not rejected with {sample['expected']!r}; got {found!r}"
            )
    missing_doc_release, missing_doc_errors = parse_release_artifacts(ROOT / "docs" / "__missing_release_artifacts__.md")
    if missing_doc_release is not None or not any("release artifact evidence file is absent" in item for item in missing_doc_errors):
        errors.append("bad sample missing release-artifacts.md was not rejected")
    malformed_text = "| Field | Value |\n| --- | --- |\n| Package filename | `daee-epistemics-RC00001-v0.3.1.0.skill.zip` |\n| SHA256 | `not-a-hash` |\n"
    _, malformed_errors = parse_release_artifacts_text(malformed_text)
    if not any("malformed current package SHA256" in item for item in malformed_errors):
        errors.append("bad sample malformed release-artifacts SHA was not rejected")
    return errors


def write_artifact(
    directory: Path,
    *,
    fixture_class_value: str,
    status: str = "PASS",
    output: str | None = None,
    trace: str | None = None,
    verdict_extra: str = "",
    with_ir: bool = False,
    release_artifact: ReleaseArtifact | None = None,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "input.md").write_text("Smoke prompt.\n", encoding="utf-8")
    output_text = output or (
        VALID_HARD_SAMPLE_OUTPUT
        if fixture_class_value == "hard"
        else "## Burden-Cycle 1\n### State/noetic re-read\n- What changed / cumulative-state delta: claim-state changed.\n- Release status: closed for this input.\n"
    )
    (directory / "output.md").write_text(output_text, encoding="utf-8")
    package_filename = release_artifact.filename if release_artifact else DEFAULT_RELEASE_PACKAGE_FILENAME
    package_sha256 = release_artifact.sha256 if release_artifact else DEFAULT_RELEASE_PACKAGE_SHA256
    trace_text = trace or (
        f"- package filename: {package_filename}\n"
        f"- package SHA256: {package_sha256}\n"
        "- release-artifact relation: current-release\n"
        "- current-release evidence: yes\n"
        "- model/host: Codex\n"
        "- invocation mode: default\n"
        "- prompt: see input.md\n"
        "- run timestamp: 2026-05-07T00:00:00Z\n"
        "- live-run vs handcrafted-regression classification: live-run\n"
        "- smoke provenance mode: live-run\n"
        "- output.md relation: direct-copied model/skill output\n"
        "- formatting-safe normalization: none\n"
        "- owner-body evidence: compiled bundle sections available\n"
        "- owner-floor evidence: owner-floor execution output-visible\n"
    )
    (directory / "trace.md").write_text(trace_text, encoding="utf-8")
    bounded_extra = (
        "- bounded-depth exception rationale: narrow.\n"
        "- bounded-complete\n"
        "- original hard intent: yes\n"
        "- first-order burdens handled: claim handled.\n"
        "- second-order burdens handled: criterion handled.\n"
        "- higher-order burdens handled: tribunal handled.\n"
        "- held burdens and why: none.\n"
        "- skipped licensed burdens: none\n"
        "- another pass licensed: no\n"
        "- under-20 rationale: complete.\n"
        "- not suitable as a hard-depth smoke\n"
        "- burden-cycle count: 1\n"
    ) if fixture_class_value == "bounded" else ""
    (directory / "verdict.md").write_text(
        f"- fixture class: {fixture_class_value}\n- status: {status}\n{bounded_extra}{verdict_extra}",
        encoding="utf-8",
    )
    if with_ir:
        # Intentionally minimal bad fixture: this checks IR presence handling,
        # not full IR schema validity.
        (directory / "ir.json").write_text('{"case_family":"placeholder"}\n', encoding="utf-8")


def validate_current_release_bad_samples(release_artifact: ReleaseArtifact) -> list[str]:
    errors: list[str] = []
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_artifact(
            root / "01-historical-only",
            fixture_class_value="hard",
            trace=(
                "- package filename: daee-epistemics-RC00001-v0.3.1.0.skill.zip\n"
                "- package SHA256: 544580B244BA27439F92177BA6EE0BADF580DD4CFEA1FD987E13D5861EA714B8\n"
                "- release-artifact relation: historical-regression\n"
                "- current-release evidence: no\n"
                f"- current source package filename: {DEFAULT_RELEASE_PACKAGE_FILENAME}\n"
                f"- current source package SHA256: {DEFAULT_RELEASE_PACKAGE_SHA256}\n"
                "- model/host: Codex\n"
                "- invocation mode: default\n"
                "- prompt: see input.md\n"
                "- run timestamp: 2026-05-07T00:00:00Z\n"
                "- live-run vs handcrafted-regression classification: live-run\n"
            ),
            with_ir=True,
        )
        found = current_release_requirement_errors(root, release_artifact)
        if not any("no hard current-release PASS smoke" in item for item in found):
            errors.append(f"strict bad sample historical-only did not fail hard-current requirement: {found!r}")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_artifact(root / "01-current-hard", fixture_class_value="hard", with_ir=False, release_artifact=release_artifact)
        write_artifact(root / "02-current-bounded", fixture_class_value="bounded", with_ir=True, release_artifact=release_artifact)
        found = current_release_requirement_errors(root, release_artifact)
        if not any("current-release PASS smoke missing ir.json" in item for item in found):
            errors.append(f"strict bad sample missing ir.json was not rejected: {found!r}")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_artifact(root / "01-current-hard", fixture_class_value="hard", output="x" * 1000, with_ir=True, release_artifact=release_artifact)
        write_artifact(root / "02-current-bounded", fixture_class_value="bounded", with_ir=True, release_artifact=release_artifact)
        found = current_release_requirement_errors(root, release_artifact)
        if not any("hard smoke PASS under depth floor" in item for item in found):
            errors.append(f"strict bad sample hard below depth was not rejected: {found!r}")

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_artifact(root / "01-current-hard", fixture_class_value="hard", with_ir=True, release_artifact=release_artifact)
        write_artifact(
            root / "02-current-bounded",
            fixture_class_value="bounded",
            verdict_extra="",
            with_ir=True,
            release_artifact=release_artifact,
        )
        # Overwrite verdict without bounded-complete fields.
        (root / "02-current-bounded" / "verdict.md").write_text(
            "- fixture class: bounded\n- status: PASS\n- burden-cycle count: 1\n",
            encoding="utf-8",
        )
        found = current_release_requirement_errors(root, release_artifact)
        if not any("bounded PASS lacks burden-completeness audit" in item for item in found):
            errors.append(f"strict bad sample bounded without audit was not rejected: {found!r}")
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=str(DEFAULT_ROOT),
        help=(
            "Smoke artifact root to validate. Defaults to repo-local "
            "smokes/runtime-grounding-v5/."
        ),
    )
    parser.add_argument(
        "--samples-only",
        action="store_true",
        help="Only run embedded bad-sample checks.",
    )
    parser.add_argument(
        "--release-artifacts",
        default=str(DEFAULT_RELEASE_ARTIFACTS),
        help="Release artifact evidence markdown to compare smoke provenance against.",
    )
    parser.add_argument(
        "--no-release-artifacts",
        action="store_true",
        help="Disable release-artifact filename/SHA consistency checks intentionally.",
    )
    parser.add_argument(
        "--require-current-release-smokes",
        action="store_true",
        help=(
            "Require at least one hard and one bounded current-release PASS smoke with ir.json. "
            "Historical regression smokes do not count."
        ),
    )
    args = parser.parse_args(argv)

    release_artifact = ReleaseArtifact(
        filename=DEFAULT_RELEASE_PACKAGE_FILENAME,
        sha256=DEFAULT_RELEASE_PACKAGE_SHA256,
    )
    release_errors: list[str] = []
    if not args.no_release_artifacts:
        release_artifact, release_errors = parse_release_artifacts(Path(args.release_artifacts))

    errors = validate_bad_samples(release_artifact or ReleaseArtifact(
        filename=DEFAULT_RELEASE_PACKAGE_FILENAME,
        sha256=DEFAULT_RELEASE_PACKAGE_SHA256,
    ))
    errors.extend(validate_current_release_bad_samples(release_artifact or ReleaseArtifact(
        filename=DEFAULT_RELEASE_PACKAGE_FILENAME,
        sha256=DEFAULT_RELEASE_PACKAGE_SHA256,
    )))
    errors.extend(release_errors)
    if not args.samples_only:
        artifact_root = Path(args.root)
        errors.extend(validate_root(artifact_root, None if args.no_release_artifacts else release_artifact))
        if args.require_current_release_smokes:
            if release_artifact is None:
                errors.append("--require-current-release-smokes requires release-artifacts evidence")
            else:
                errors.extend(current_release_requirement_errors(artifact_root, release_artifact))

    if errors:
        print("smoke artifact validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("smoke artifact validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
