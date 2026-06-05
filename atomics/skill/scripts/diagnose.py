#!/usr/bin/env python3
"""Extract Level 3 covered-scope features with input-span justification.

Mechanical features are regex/parser based. The interpretive slots are
represented as LLM-assisted feature classes, but this local runtime uses bounded
span-backed heuristics so CI can run without network or model access. A future
LLM extractor may replace these heuristics only if it preserves span,
confidence, and ambiguous-fallback discipline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from level3_lib import LEVEL3_VERSION, default_skill_root, find_spans, sha256_text, write_json


MECHANICAL_PATTERNS: dict[str, list[str]] = {
    "term.trinity": [r"\btrinit(?:y|arian)\b", r"\bthree\s+persons?\b"],
    "term.father_son_spirit": [
        r"\bfather\b.{0,120}\bson\b",
        r"\bson\b.{0,120}\bfather\b",
        r"\bfather\b.{0,120}\b(?:holy\s+)?spirit\b",
        r"\b(?:holy\s+)?spirit\b.{0,120}\bfather\b",
        r"\bson\b.{0,120}\b(?:holy\s+)?spirit\b",
        r"\b(?:holy\s+)?spirit\b.{0,120}\bson\b",
        r"\bholy\s+spirit\b",
    ],
    "feature.person_nature_predication_relation": [
        r"\b(?:one|single|shared)\b.{0,120}\b(?:nature|essence|substance)\b.{0,120}\bthree\s+persons?\b",
        r"\bthree\s+persons?\b.{0,120}\b(?:one|single|shared)\b.{0,120}\b(?:nature|essence|substance)\b",
        r"\bpredicate\b.{0,120}\b(?:person|nature|category|identity)\b",
        r"\b(?:person|nature|category|identity)\b.{0,120}\bpredicate\b",
    ],
    "term.attribute": [r"\battribute\b", r"\battributes\b", r"\bpredicate\b", r"\bpredication\b"],
    "term.god": [r"\bgod\b", r"\bdivine\b", r"\bcreator\b"],
    "term.secularism": [r"\bsecularism\b", r"\bsecularist\b", r"\bnaturalism\b", r"\batheism\b"],
    "term.shubhah": [r"\bshubhah\b", r"\bdoubt\b", r"\bobjection\b"],
    "term.necessary_knowledge": [r"\bnecessary\s+knowledge\b", r"\bself[- ]evident\b", r"\bbedrock\b"],
    "term.kalam": [r"\bkalam\b", r"\bspeculative\s+theolog(?:y|ical)\b"],
    "term.zahir_tawil": [r"\bzahir\b", r"\btawil\b", r"\bta'wil\b"],
    "term.majaz_haqiqah": [r"\bmajaz\b", r"\bhaqiqah\b", r"\bhaqiqi\b"],
    "term.reason_roles": [
        r"\bsound\s+reason\b",
        r"\breason\s+as\s+(?:tribunal|judge)\b",
        r"\bspeculative\s+inference\b",
        r"\bimported\s+criterion\b",
        r"\bfitri\s+recognition\b",
        r"\bdaruri\b",
        r"\bnazari\b",
    ],
    "feature.quoted_assertion": [r"\"[^\"]+\"", r"'[^']+'"],
    "feature.negation_protest": [r"\bnever\s+worship\b", r"\bwould\s+not\s+worship\b", r"\bcannot\b", r"\bcan't\b"],
    "feature.worldview_refutation_request": [r"\brefute\b", r"\bdismantle\b", r"\brespond\s+to\b"],
    "feature.authority_claim": [r"\bauthority\b", r"\bultimate\s+judge\b", r"\bverdict\b", r"\btribunal\b"],
    "feature.proof_status_pressure": [
        r"\bwarrant(?:ed)?\b",
        r"\bjustif(?:y|ied|ication)\b",
        r"\bproof[- ]status\b",
        r"\beviden(?:ce|tial)\s+(?:burden|status|warrant|criterion)\b",
        r"\brational(?:ly)?\s+(?:warranted|justified|required)\b",
    ],
    "feature.moral_tribunal": [
        r"\bnever\s+worship\b",
        r"\bmorally\s+(?:unacceptable|wrong|cruel)\b",
        r"\bmore\s+humane\b",
        r"\bcruel\b",
        r"\bpunish(?:es|ment|ing)?\b",
    ],
    "feature.hiddenness_punishment_cluster": [r"\bhiddenness\b", r"\bnot\s+shown\s+enough\b", r"\bpunish(?:es|ment|ing)?\b"],
    "feature.accountability_compression": [
        r"\bnon[- ]belief\b",
        r"\bsimple\s+fact\s+of\s+non[- ]belief\b",
        r"\beternal\s+lake\s+of\s+fire\b",
        r"\bburn(?:ed|ing)?\s+forever\b",
        r"\bhell\b",
    ],
    "feature.coercive_guidance_demand": [
        r"\bknows\s+what\s+it\s+would\s+take\s+to\s+convince\b",
        r"\bconvince\s+every\s+single\s+person\b",
        r"\bhides?\s+himself\b",
        r"\bnot\s+shown\s+enough\b",
    ],
    "feature.opponent_worldview_frame": [
        r"\bfollower\s+of\s+[^.\n,]+",
        r"\bmember\s+of\s+[^.\n,]+",
        r"\badherent\s+of\s+[^.\n,]+",
        r"\bfrom\s+(?:within\s+)?(?:the\s+)?[^.\n,]+(?:framework|worldview|tradition|movement)\b",
        r"\bworldview\b",
        r"\bbelief\s+system\b",
        r"\bsource[- ]worldview\b",
        r"\bopponent(?:'s)?\s+(?:framework|worldview|position)\b",
        r"\bsecular\s+humanis[mt]\b",
        r"\bliberal\s+humanis[mt]\b",
    ],
    "feature.mercy_worthiness_protest": [
        r"\binhumane\b",
        r"\bnot\s+kind\b",
        r"\bnot\s+generous\b",
        r"\bnot\s+(?:a\s+)?God\s+worthy\s+of\s+worship\b",
        r"\bworthy\s+of\s+worship\b",
        r"\bmore\s+humane\b",
    ],
    "feature.source_substantiation_request": [
        r"\bbring\s+sources\b",
        r"\bsubstantiate\b",
        r"\bdismantle\b",
    ],
    "feature.grief_keyword": [
        r"\bgrief\b",
        r"\bwound\b",
        r"\btrauma\b",
        r"\bfamily\s+(?:wound|trauma|harm|grief|death|died|loss)\b",
        r"\b(?:lost|loss\s+of|death\s+of)\s+(?:my\s+|a\s+|the\s+)?family\b",
        r"\bdied\b",
        r"\bhurt\b",
    ],
    "feature.attribute_resemblance": [
        r"\bresemble\b",
        r"\bsimilar\s+to\s+creatures?\b",
        r"\blike\s+creatures?\b",
        r"\bmushabara\s+fasida\b",
        r"\bfalse\s+resemblance\b",
    ],
    "feature.deformation_cleared": [
        r"\bafter\s+(?:clearing|the\s+deformation\s+is\s+cleared)\b",
        r"\bdeformation\s+(?:cleared|removed)\b",
    ],
    "feature.deformation_signal": [r"\bdeformation\b", r"\bconcealment\b", r"\bfalse\s+resemblance\b"],
}


def add_feature(
    collection: list[dict[str, Any]],
    feature_ids: set[str],
    feature_id: str,
    spans: list[dict[str, Any]],
    *,
    source: str,
    confidence: float = 1.0,
    classification: str | None = None,
) -> None:
    if not spans:
        return
    feature_ids.add(feature_id)
    item: dict[str, Any] = {
        "id": feature_id,
        "source": source,
        "confidence": confidence,
        "spans": spans,
    }
    if classification is not None:
        item["classification"] = classification
    collection.append(item)


def extract(text: str, skill_root: Path) -> dict[str, Any]:
    del skill_root  # Keep CLI signature aligned with the other Level 3 commands.
    mechanical: list[dict[str, Any]] = []
    assisted: list[dict[str, Any]] = []
    feature_ids: set[str] = set()

    span_cache: dict[str, list[dict[str, Any]]] = {}
    for feature_id, patterns in MECHANICAL_PATTERNS.items():
        spans = find_spans(text, feature_id, patterns, "mechanical")
        span_cache[feature_id] = spans
        add_feature(mechanical, feature_ids, feature_id, spans, source="mechanical")

    # Derived mechanical features.
    predication_spans: list[dict[str, Any]] = []
    if span_cache["term.trinity"] and (span_cache["term.father_son_spirit"] or span_cache["term.attribute"]):
        predication_spans.extend(span_cache["term.trinity"] + span_cache["term.father_son_spirit"] + span_cache["term.attribute"])
    predication_spans.extend(span_cache["feature.person_nature_predication_relation"])
    if predication_spans:
        spans = predication_spans
        add_feature(mechanical, feature_ids, "feature.predication_confusion", spans, source="mechanical")

    if span_cache["feature.attribute_resemblance"]:
        add_feature(mechanical, feature_ids, "feature.false_resemblance", span_cache["feature.attribute_resemblance"], source="mechanical")

    if span_cache["feature.moral_tribunal"]:
        add_feature(mechanical, feature_ids, "span.imported_criterion", span_cache["feature.moral_tribunal"], source="mechanical")

    if span_cache["feature.grief_keyword"]:
        add_feature(mechanical, feature_ids, "span.register", span_cache["feature.grief_keyword"], source="mechanical")

    criterion_spans = (
        span_cache["feature.negation_protest"]
        + span_cache["feature.authority_claim"]
        + span_cache["feature.proof_status_pressure"]
        + span_cache["feature.accountability_compression"]
        + span_cache["feature.coercive_guidance_demand"]
        + span_cache["feature.mercy_worthiness_protest"]
        + span_cache["term.reason_roles"]
    )
    theological_topic_spans = (
        span_cache["term.god"]
        + span_cache["term.secularism"]
        + span_cache["feature.quoted_assertion"]
        + span_cache["term.kalam"]
        + span_cache["term.zahir_tawil"]
        + span_cache["term.majaz_haqiqah"]
    )
    source_request_spans = span_cache["feature.source_substantiation_request"]
    worldview_context_spans = span_cache["feature.opponent_worldview_frame"]
    add_feature(mechanical, feature_ids, "feature.reason_repair_pressure", criterion_spans, source="mechanical", confidence=0.9)
    add_feature(mechanical, feature_ids, "feature.theological_topic_context", theological_topic_spans, source="mechanical", confidence=0.7)
    add_feature(mechanical, feature_ids, "feature.source_request", source_request_spans, source="mechanical", confidence=0.8)
    add_feature(mechanical, feature_ids, "feature.worldview_context_marker", worldview_context_spans, source="mechanical", confidence=0.75)
    if criterion_spans and worldview_context_spans:
        add_feature(
            mechanical,
            feature_ids,
            "feature.criterion_bearing_source_worldview",
            (criterion_spans + worldview_context_spans)[:8],
            source="mechanical",
            confidence=0.84,
        )
    if span_cache["feature.authority_claim"] or span_cache["feature.moral_tribunal"]:
        add_feature(
            mechanical,
            feature_ids,
            "feature.imported_tribunal_pressure",
            span_cache["feature.authority_claim"] + span_cache["feature.moral_tribunal"],
            source="mechanical",
            confidence=0.84,
        )

    shubhah_spans = span_cache["term.shubhah"] + span_cache["term.necessary_knowledge"]
    if span_cache["term.necessary_knowledge"] and (span_cache["term.shubhah"] or span_cache["feature.deformation_cleared"]):
        add_feature(mechanical, feature_ids, "feature.necessary_knowledge_shubhah", shubhah_spans, source="mechanical")

    # Span-backed interpretive slots. Low-confidence slots become ambiguous and
    # are not added as router features.
    grief_spans = span_cache["feature.grief_keyword"]
    if grief_spans:
        add_feature(
            assisted,
            feature_ids,
            "feature.grief_register",
            grief_spans,
            source="llm_assisted_span_heuristic",
            confidence=0.86,
            classification="grief",
        )
    else:
        assisted.append({
            "id": "register_classification",
            "classification": "argument_or_unknown",
            "confidence": 0.51,
            "spans": [],
            "accepted_by_router": False,
            "reason_code": "ambiguous",
            "reason": "No register span; ambiguous fallback.",
        })

    imported_spans = span_cache["feature.moral_tribunal"] + span_cache["feature.authority_claim"]
    if imported_spans:
        add_feature(
            assisted,
            feature_ids,
            "feature.imported_criterion",
            imported_spans,
            source="llm_assisted_span_heuristic",
            confidence=0.82,
            classification="imported_criterion",
        )
    else:
        assisted.append({
            "id": "imported_criterion_detection",
            "classification": "ambiguous",
            "confidence": 0.45,
            "spans": [],
            "accepted_by_router": False,
            "reason_code": "insufficient-evidence",
            "reason": "No imported-criterion span.",
        })

    if span_cache["feature.attribute_resemblance"] or span_cache["feature.deformation_signal"]:
        spans = span_cache["feature.attribute_resemblance"] + span_cache["feature.deformation_signal"]
        add_feature(
            assisted,
            feature_ids,
            "feature.concealment_false_resemblance",
            spans,
            source="llm_assisted_span_heuristic",
            confidence=0.8,
            classification="false_resemblance",
        )

    orientation_spans = criterion_spans + theological_topic_spans + source_request_spans + worldview_context_spans + imported_spans + grief_spans
    if orientation_spans:
        if grief_spans:
            classification = "register-first"
        elif imported_spans:
            classification = "criterion-first"
        else:
            classification = "argument"
        assisted.append({
            "id": "discourse_orientation",
            "classification": classification,
            "confidence": 0.76,
            "spans": orientation_spans[:5],
            "accepted_by_router": False,
        })

    if "feature.grief_register" in feature_ids:
        sequence = "register-hold-first"
        spans = grief_spans
    elif "feature.imported_criterion" in feature_ids:
        sequence = "imported-criterion-first"
        spans = imported_spans
    elif "feature.false_resemblance" in feature_ids:
        sequence = "deformation-first"
        spans = span_cache["feature.attribute_resemblance"]
    elif "feature.necessary_knowledge_shubhah" in feature_ids:
        sequence = "necessary-knowledge-first"
        spans = shubhah_spans
    elif "feature.predication_confusion" in feature_ids:
        sequence = "predication-first"
        spans = span_cache["term.trinity"] + span_cache["term.father_son_spirit"] + span_cache["feature.person_nature_predication_relation"]
    else:
        sequence = "ambiguous"
        spans = []
    assisted.append({
        "id": "mixed_case_sequencing",
        "classification": sequence,
        "confidence": 0.78 if spans else 0.4,
        "spans": spans[:5],
        "accepted_by_router": False,
    })

    return {
        "level3_version": LEVEL3_VERSION,
        "extractor": "diagnose.py",
        "extractor_mode": "mechanical plus span-backed interpretive slots",
        "input_sha256": sha256_text(text),
        "mechanical": mechanical,
        "llm_assisted": assisted,
        "feature_ids": sorted(feature_ids),
        "feature_extraction_limits": [
            "Semantic feature extraction can vary by model in non-heuristic deployments.",
            "The router accepts only features with input-span support.",
            "Low-confidence interpretive slots fall back to ambiguous and do not route.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract Level 3 route features.")
    parser.add_argument("--input", required=True, help="Input text file.")
    parser.add_argument("--output", help="features.json path.")
    parser.add_argument("--skill-root", default=str(default_skill_root()), help="Skill package root.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"diagnose: input missing: {input_path}", file=sys.stderr)
        return 2
    payload = extract(input_path.read_text(encoding="utf-8"), Path(args.skill_root))
    if args.output:
        write_json(Path(args.output), payload)
    else:
        print(__import__("json").dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
