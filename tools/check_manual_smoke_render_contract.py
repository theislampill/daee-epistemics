#!/usr/bin/env python3
"""Validate manual/default hard-smoke render contract.

This checker is intentionally structural. It guards the v0.4.3.0 manual smoke
regression class where a readable theological answer drops the required public
execution banner, canonical burden notation, MRP route-result fields, generated
burden ledger, generated-by provenance, and Closing Formulation.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

from closure_witness_lib import (
    compare_visible_to_field_witness,
    extract_embedded_field_witness,
    extract_field_witness,
    field_witness_graph_errors,
    parse_closure_witness,
)
from delta_result_vocabulary import (
    delta_result_vocabulary_errors,
    owner_operation_vocabulary_errors,
    source_formal_delta_operation_errors,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SUP = "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079"
SUB = "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089"
SUP_DIGITS = str.maketrans(SUP, "0123456789")
SUB_DIGITS = str.maketrans(SUB, "0123456789")
ASCII_TO_SUP_DIGITS = str.maketrans("0123456789", SUP)
B_LEDGER = "\U0001d505"
WRONG_B_LEDGER = "\U0001d4d1"
WRONG_CLOSURE = "\U0001d4d2"
GENERIC_BURDEN_PLACEHOLDER_RE = re.compile(
    r"(?:[\u207f\u1d4f]B(?:[" + SUB + r"]+)?)"
    r"|(?:\bB[kn]\b|\bB[kn]\s*(?:->|\u2192)|(?:Land|MRP)\(\s*B[kn]\s*\)|Target:\s*B[kn]\b)"
)
SOURCE_OWNED_CONCEALMENT = (
    "iʿrāḍ",
    "irad",
    "i'rad",
    "juḥūd",
    "juhud",
    "inkār",
    "inkar",
    "istikbār",
    "istikbar",
    "nifāq",
    "nifaq",
    "mixed",
    "clarification",
    "shubhah",
    "shubha",
    "shakk",
    "rayb",
    "clear",
)
SOURCE_COMPONENT_TOKEN_RE = re.compile(
    r"(?i)\b(?:i['`]?rad|irad|juhud|inkar|istikbar|nifaq)\b|"
    r"iʿrāḍ|juḥūd|inkār|istikbār|nifāq"
)
CLARIFICATION_PRESSURE_RE = re.compile(
    r"(?i)\b(?:clarification\s+pressure|clarification\s*/\s*shubh?a?h|"
    r"shubh?a?h|shakk|rayb|rāyb|tawahhum|wasw[āa]s|doubt-pressure|doubt\s+pressure|"
    r"sincere\s+(?:uncertainty|clarification|inquiry)|ḥanīf\s+restoration|hanif\s+restoration)\b"
)
REFUSAL_SIGNAL_RE = re.compile(
    r"(?i)\b(?:refus|repudiat|recognition\s+pressure|outward\s+denial|"
    r"acknowledg(?:e|ment).*refus|pride|status\s+obstruction|volitional\s+alignment|"
    r"surface\s+acceptance\s+without\s+genuine|performative\s+agreement)\b"
)
CLARIFICATION_ROUTE_RE = re.compile(
    r"(?i)\b(?:route[sd]?\s+(?:toward|to|through)\s+clarification|"
    r"clarification\s+(?:route|path)|not\s+(?:functioning\s+as\s+)?refusal|"
    r"not\s+routed\s+to\s+refusal|not\s+(?:juḥūd|juhud|inkār|inkar|istikbār|istikbar|nifāq|nifaq)|"
    r"rather\s+than\s+(?:refusal|denial|obstinacy)|bounded\s+reassurance|"
    r"source[- ]order\s+repair|fiṭrah\s+anchoring|fitrah\s+anchoring|V9)\b"
)
BAD_CLARIFICATION_REFUSAL_ROUTE_RE = re.compile(
    r"(?i)\b(?:shubh?a?h|shakk|rayb|rāyb|clarification\s+pressure|sincere\s+uncertainty)"
    r"[^.\n;]*(?:route[sd]?\s+(?:to|into)|assigned\s+to|classified\s+as|read\s+as|folded\s+into)"
    r"[^.\n;]*(?:refusal|juḥūd|juhud|inkār|inkar|istikbār|istikbar|nifāq|nifaq)\b"
)
HIGH_LEVERAGE_HELD_ROUTE_RE = re.compile(
    r"(?i)\b(?:independent lordship|canon[- ]wide|textual criticism|epistemology of canon|"
    r"full Christology|source/proof-stack|source authority|proof[- ]stack|mystery shield|"
    r"worldview recoil|moral tribunal shift|authority-order|predication|source-worldview|"
    r"Christology|theology|hiddenness|metaphysics|epistemology|identity/worldview|"
    r"historical/transmission|transmission|source-authority|analogy[- ]stack|shubha|"
    r"shakk|rayb|moral protest|secular moral|source[- ]order|criterion)\b"
)
UNROUTED_HELD_ROUTE_RE = re.compile(
    r"(?i)\b(?:not released|unreleased|held beyond|beyond prompt|beyond bounded claim|"
    r"held outside scope|not worked)\b"
)
TERMINAL_CLOSURE_RE = re.compile(r"(?i)\b(?:STOP|closure|complete|collapse achieved|no remaining live problem)\b")
ROUTING_OR_BOUNDARY_PROOF_RE = re.compile(
    r"(?i)\b(?:held_burden_activation|generated_burden_instantiation|HOLD|PARTIAL|"
    r"coverage_complete\s*=\s*false|non[- ]load[- ]bearing|not load[- ]bearing|"
    r"not needed for (?:this|the) (?:scoped|bounded|local) claim|scope gate|"
    r"local closure only|partial closure)\b"
)
BAD_ROUTE_VALUE_RE = re.compile(
    r"(?im)^\s*Route\s*:\s*(?:RECURSE|STOP|HOLD|LoopBreak\(∇×T\))\s+(?:to|into|/|with|because|generated|closure)\b"
)
MRP_BLOCK_WITHOUT_TARGET_RE = re.compile(r"(?ims)^\s*\[Mid-Reread Pressure\]\s*\n(?!\s*Target\s*:)")
INLINE_REREAD_HEADING_RE = re.compile(
    r"(?im)^\s*R\(H,\s*(?:\u0394|Delta)\)\s*:\s*\[Mid-Reread Pressure\]\s*$"
)
HIGH_MASS_TERMS_RE = re.compile(
    r"(?i)\b(?:source[- ]worldview|worldview|proof[- ]stack|textual|canon|Christology|"
    r"independent lordship|hidden premise|dependency radius|source authority|authority-order|"
    r"predication|category|moral tribunal|worship[-_ ]worthiness|"
    r"divine[-_ ]hiddenness|hiddenness|source[-_ ]governance|chronology\+causality|chronology[-_ ]causality|"
    r"expose[-_ ]neutrality[-_ ]burden|neutrality[-_ ](?:burden|claim)|coercive guidance|"
    r"accountability|culpability|arbitrary command|command authority|mystery shield|"
    r"immunity|recoil|epistemology|self[- ]refutation|"
    r"performative contradiction|consequence trace|LoopBreak|proof[- ]carousel)\b"
)
LOW_MASS_LICENSE_RE = re.compile(
    r"(?i)\b(?:diagnostic state proves low mass|low[- ]mass license|low burden mass because|"
    r"few hidden premises|low dependency radius|no source/worldview load|no source-worldview load|"
    r"no predication/category repair|no proof-stack|no textual backstop|no MRP-detected recoil|"
    r"low closure risk)\b"
)
LOW_MASS_ASSERTION_RE = re.compile(
    r"(?i)\b(?:treated as low[- ]mass|low[- ]mass burden|low burden mass|"
    r"burden mass is low|bounded scope makes it low[- ]mass|local scope makes it low[- ]mass|"
    r"bounded/local scope removes|bounded scope removes|local scope removes)\b"
)
LABEL_LIKE_VALUE_RE = re.compile(
    r"(?i)^(?:dummy|label|named|name it|trace it|traced|identify it|identified|"
    r"expose|exposed|contributes?|lands?|landed|bounded|local|cleared|none|"
    r"the route is named|the pressure is named)\.?$"
)
RELATIONAL_PRESSURE_RE = re.compile(
    r"(?i)\b(?:identity|person|label|source|authority|criterion|reason|boundary|"
    r"model|mystery|proof|doctrine|worldview|frame)[- ]as[- ](?:warrant|criterion|"
    r"tribunal|immunity|proof|authority|source|court|support)\b"
)
PLACEHOLDER_OWNER_RE = re.compile(
    rf"(?im)^\s*(?:#{{1,6}}\s*)?(?:[{SUP}]+B|B\d+)(?:[{SUB}]+|[_\.]\d+)\s*"
    r"\[OP(?:[ᵢi])?\](?:\s*\[[^\]]+\])?"
)
OPERATION_MECHANISM_RE = re.compile(
    r"(?i)\b(?:hidden premise|escape route|smuggl|burden shift|proof[- ]stack|source[- ]order|"
    r"source authority|authority frame|scope gate|bounded claim|local claim|"
    r"expose[-_ ]neutrality[-_ ]burden|neutrality[-_ ](?:burden|claim)|total[- ]system|"
    r"whole[- ]system|exhaust|reopen|would require|unworked held route|non[- ]load[- ]bearing|"
    r"predicate|predication|category|monotheism[- ]counting|exclusive[- ]counting|"
    r"fatal[- ]harm(?:[- ]at[- ]t1)?|lexical[- ]equivalence|chronology[- ]completion|"
    r"chronology[- ]collapse|t1[- ]t2[- ]chronology[- ]collapse|"
    r"t1[- ]t2[- ]causation[- ]collapse|"
    r"attribute[- ]precision|claim[- ]context[- ]boundary|claim[-_ ]reconstruction[-_ ]pressure|definition[-_ ]boundary|"
    r"definition[- ]pressure|scope[- ]pressure|"
    r"moral[- ]intuition|ungrounded[- ]moral[- ]intuition|moral[- ]reaction|orphaned[- ]intuition|"
    r"dependency|criterion|immunity|recoil|framework|"
    r"broader material|held material|state change|delta|consequence|entailment|"
    r"self[- ]refutation|performative contradiction|internal contradiction|semantic|referent|"
    r"authority[- ]order|proof[- ]carousel|stop condition|closure boundary|circularity|"
    r"loop|restoration|fitrah|tawhid|positive orientation|guidance[- ]order|"
    r"guidance[- ]vs[- ]compulsion|source[- ]function|conveyance|warning|tawf[iī]q|"
    r"non[- ]coercive guidance)\b"
)
DO_ATTRIBUTE_CLAIM_PRECISION_TARGET_RE = re.compile(
    r"(?i)attribute[-_ ]claim[-_ ]precision"
)
OPERATION_ACTION_RE = re.compile(
    r"(?i)\b(?:expose|distinguish|distinguishes|distinguished|distinguishing|"
    r"block|blocks|blocked|blocking|repair|repairs|repaired|repairing|"
    r"trace|ground|test|split|splits|splitting|separate|separates|separated|separating|"
    r"prevent|audit|apply|tests?|act(?:s|ing)?\s+with\s+(?:M3|owner\s+family\s+M3)\s+on|integrate|integrates|integrated|integrating|"
    r"relocate|relocates|relocated|relocating|recognize|recognizes|recognized|recognizing|"
    r"identify|identification|reclassify|refuse|sequence|show why|demonstrate|bar|route|bind|isolate|"
    r"name|names|named|naming|define|anchor|anchors|anchored|anchoring|clarify|vet|reconstruct|dissolve|dissolves|dissolved|triage|prioritize|map|"
    r"type|types|typed|typing|calibrate|calibrates|calibrated|calibrating|"
    r"assume|assumes|assumed|assuming|follow|follows|followed|following|"
    r"shifts?|smuggl|reopen|supplies|explains|cannot retroactively|does not mean|"
    r"answered according|sort|bound|stop|break|restores?|return|orient|reorient|re-home|honor)\b"
)
OPERATION_SCOPE_RE = re.compile(
    r"(?i)\b(?:original (?:local )?claim|local (?:claim|argument|reply|refutation|closure)|"
    r"specific (?:reply|argument|claim)|bounded (?:claim|refutation|closure|answer)|"
    r"scoped (?:claim|closure)|total[- ]system|whole[- ]system|entire doctrine|"
    r"every (?:text|possible route|doctrine)|broader (?:system|framework|doctrine|material)|"
    r"proof[- ]stack claim|predicate|predication|identity claim|sender/sent|source[- ]order|"
    r"authority[- ]order|ontology|criterion|tribunal)\b"
)
OPERATION_TEST_RE = re.compile(
    r"(?i)\b(?:hidden premise|new premise|unargued|unstated|must be (?:stated|tested|carried)|"
    r"would require|requires (?:a )?(?:new burden|fixed|stable|criterion)|"
    r"reopen(?:ed|ing)?|reopen condition|admissible only if|cannot be smuggled|smuggled|"
    r"tests? which inference|which inference depends|would need its own burden|importing a new ontology|"
    r"must carry|must supply)\b"
)
OPERATION_FAILURE_RE = re.compile(
    r"(?i)\b(?:cannot (?:rescue|repair|retroactively|function)|not a rescue|does not (?:establish|license|derive)|"
    r"burden shift|burden shifting|proof[- ]carousel|evasion|not evidence|barred|blocked|fails because)\b"
)
STATE_CHANGE_RE = re.compile(
    r"(?i)\b(?:blocked|blocks|removed|removes|separated|separates|held|released|routed|"
    r"licensed|licenses|license|scoped STOP|reopen conditions|future distinct burdens|admissible|"
    r"barred|prevents|cannot rescue|requires a new burden|becomes a new burden|"
    r"scope[- ]boundary[- ]named|"
    r"exposed|demote|demotes|demoted|invalidated|withheld|narrowed|reoriented|converted|classified|sorted|sorts|"
    r"grounded|regrounded|re-grounded|"
    r"identified|identifies|defined|defines|stabilized|stabilizes|refused|denied|self[- ]undercut|loses|loss|severed|separated from|"
    r"criterion[- ]self[- ]failed|self[- ]failed|"
    r"(?:non|not)[- ]load[- ]bearing|lands|landed|cleared|state change|delta|undermined|"
    r"self[- ]undermining|invalidated|resolved|bounded|stopped|restored|restores|restoring|"
    r"returned|returning|returns|anchors?|anchored)\b"
)
PROOF_METHOD_CARRIER_RE = re.compile(
    r"(?is)\b(?:proof[- ]family|proof[- ]carrier|proof carrier|logic tree|"
    r"formal derivation|formal display|diagram|symbolic conflict|compression device|"
    r"proof[- ]route|route[- ]status|burden[- ]scope|tribunal[- ]status|burden[- ]function)\b"
)
PROOF_METHOD_DEPENDENCY_RE = re.compile(
    r"(?is)\b(?:premise[- ]set|premises?|predicate|definition|definitions?|"
    r"source sorting|source meanings?|entailment licensing|dependency|depends on|"
    r"earlier source|earlier .* semantic|faithful(?:ly)? preserve|supporting texts?|"
    r"proof eligibility|standard of proof|proof forum|burden role|burden[- ]function)\b"
)
PROOF_METHOD_STATE_RE = re.compile(
    r"(?is)\b(?:no longer treated as (?:a )?neutral proof|typed as a proof carrier|"
    r"does not independently establish|not self[- ]standing|prevents? the formal display from outranking|"
    r"cannot outrank|imports unresolved|packages? a contested premise[- ]set|"
    r"classif(?:y|ies|ied) .* compression device|loses the decisive distinctions?|"
    r"route[- ]status (?:is )?clarified|proof route is bounded|"
    r"tribunal[- ]function (?:is )?named|burden[- ]function (?:is )?named)\b"
)
PROOF_METHOD_ROUTE_STATUS_BODY_RE = re.compile(
    r"(?is)\b(?:proof forum|standard of proof|burden[- ]function|burden role|"
    r"tribunal[- ]function|proof eligibility|supporting texts?|premise/inference/conclusion scope)\b"
)
SOURCE_AUTHORITY_REPAIR_STATE_RE = re.compile(
    r"(?is)\b(?:authority[- ]order[- ]repaired|authority order is repaired)\b"
)
SOURCE_ORDER_REPAIR_STATE_RE = re.compile(
    r"(?is)\b(?:source[- ]order[- ]repaired|source order is repaired|"
    r"proof[- ]text[- ]hidden[- ]support[- ]blocked|hidden[- ]support[- ]blocked|"
    r"proof[- ]text[- ]sorted|source[- ]function[- ]bounded)\b"
)
SOURCE_AUTHORITY_REPAIR_EVIDENCE_RE = re.compile(
    r"(?is)\b(?:authority|rank|tribunal|judge|judging office|court|higher court|"
    r"source[- ]sovereignty|source authority|authority[- ]order|outrank|"
    r"approval standard|revelation .* judge|moral bench)\b"
)
SOURCE_ORDER_REPAIR_EVIDENCE_RE = re.compile(
    r"(?is)\b(?:source[- ]order|source lineage|quotation chain|quotation order|"
    r"quote(?:d|s)? order|inherited claim|inherited[- ]claim order|source priority|"
    r"source precedence|evidential dependency|dependency route|derivation order|"
    r"source chain|source function|testimony source|report source)\b"
)
SOURCE_REPAIR_NEGATED_EVIDENCE_RE = re.compile(
    r"(?is)\b(?:does not (?:sort|distinguish)|do not (?:sort|distinguish)|"
    r"does not perform (?:source|authority|ordering|repair|transition|operation|work)|"
    r"do not perform (?:source|authority|ordering|repair|transition|operation|work)|"
    r"never (?:sorts?|distinguishes?)|never performs (?:source|authority|ordering|repair|transition|operation|work)|"
    r"not\s+(?:actually\s+|really\s+|visibly\s+|explicitly\s+)?(?:sorts?|distinguishes?)\b|"
    r"only repeats?|merely repeats?|"
    r"generic repair language|label(?:s)? only|owner labels?)\b"
)
PUBLIC_ACT_RECORD_RE = re.compile(
    rf"(?m)^\s*\u27e6ACT\s+"
    rf"(?P<submove_ref>(?:[{SUP}]+B|B\d+)(?:[{SUB}]+|[_\.]\d+))"
    rf"\[(?P<owner>[A-Za-z][A-Za-z0-9_/\-]*)\.(?P<operation>[A-Za-z][A-Za-z0-9_.\-/]*)\]"
    rf"\s*::\s*\u03c0=(?P<pressure>[^\n]+?)"
    rf"\s*::\s*body_ref=(?P<body_ref>[^\s:]+)"
    rf"\s*::\s*\u0394=(?P<delta>[^:\s]+):(?P<delta_result>.+?)"
    rf"\s*::\s*(?P<land>Land\([^)\n]+\)\+?)\u27e7\s*$"
)
SOURCE_COMPACT_FORMAL_DELTAS = {
    "authority-order-repaired": "authority-order",
    "source-order-repaired": "source-order",
}
GENERIC_CONTRIBUTION_RE = re.compile(
    r"(?i)^\s*(?:it\s+)?(?:blocks?|preserves?|gives?|allows?|contributes?|lands?|makes?)\s+"
    r"(?:the\s+)?(?:move|burden|closure|target|direction|condition)\.?\s*$"
)
FIELD_LABEL_RE = re.compile(
    r"(?im)^\s*-?\s*(?:Target|Operation|What it does|Result(?:/state-change)?|Contribution-to-Land(?:\([^)]*\))?)\s*:"
)

OWNER_OPERATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "V1",
        re.compile(
            r"(?i)\b(?:diagnostic entry|diagnostic gate|case[- ]state|state[- ]read|"
            r"classif(?:y|ies|ication)|axis|pattern profile|triage|validated state)\b"
        ),
    ),
    (
        "V2",
        re.compile(
            r"(?i)\b(?:conception of reason|role of reason|sound reason|reconstitut\w+ reason|"
            r"reason is (?:not|more than)|reason[- ]role|rational faculty|type reason|"
            r"reason as (?:access|recognition|recognizer)|epistemic role|order of discovery|"
            r"order of reality|proof[- ]burden|burden[- ]order|warrant[- ]order|"
            r"claimant'?s? burden|must prove|stronger inference)\b"
        ),
    ),
    (
        "V3",
        re.compile(r"(?i)\b(?:regress|infinite regress|terminat\w+|grounding chain|non[- ]terminating)\b"),
    ),
    (
        "V4",
        re.compile(r"(?i)\b(?:contamination|contaminated|foreign frame|mixed source|imported standard)\b"),
    ),
    (
        "V5",
        re.compile(r"(?i)\b(?:signs?|ayat|direct(?:s|ing) attention|attention to|evidence in creation)\b"),
    ),
    (
        "V6",
        re.compile(r"(?i)\b(?:convergence|multi[- ]register|integrat(?:e|ion)|converging lines|registers? together)\b"),
    ),
    (
        "V7",
        re.compile(r"(?i)\b(?:taqlid|blind following|inherited authority|following without proof|deference structure)\b"),
    ),
    (
        "V8",
        re.compile(r"(?i)\b(?:bila kayf|bilā kayf|attribute discipline|without asking how|modality|kayf|divine attribute)\b"),
    ),
    (
        "V9",
        re.compile(r"(?i)\b(?:necessary knowledge|fitri knowledge|fiṭrī knowledge|lower[- ]order|destabiliz\w+|priority)\b"),
    ),
    (
        "V10",
        re.compile(r"(?i)\b(?:transmission|content vetting|isnad|isnād|matn|source chain|report standard|textual transmission)\b"),
    ),
    (
        "V11",
        re.compile(r"(?i)\b(?:taqlid|taḥqīq|tahqiq|transition to verification|recognition and transition|from deference)\b"),
    ),
    (
        "V12",
        re.compile(r"(?i)\b(?:tamanu|tamānu|divine plurality|independent lordship|multiple gods|logical exhaustion|plurality pressure)\b"),
    ),
    (
        "PATTERN_PROFILE",
        re.compile(
            r"(?i)\b(?:loaded[- ]label|label[- ]carrier|identity[- ]carrier|"
            r"worldview[- ]carrier|noetic[- ]carrier|carrier[- ]function|"
            r"proof[- ]packet|collapse[- ]radius|mutation[- ]after[- ]challenge|"
            r"pattern[- ]profile|compression[- ]carrier)\b"
        ),
    ),
    (
        "FPD",
        re.compile(
            r"(?i)\b(?:foreign premise|imported premise|imported criterion|hidden court|"
            r"foreign criterion|hidden premise|escape route|hidden support|smuggl\w*|"
            r"unargued criterion|criterion import|premise import|hidden criterion|"
            r"imported tribunal|imported court|impossible tribunal|total[- ]exhaustion tribunal)\b"
        ),
    ),
    (
        "M1-P",
        re.compile(
            r"(?i)\b(?:performative[- ]contradiction|act of (?:making|asserting)|presuppos\w+|"
            r"cannot ground its own assertion|speech[- ]act|claiming it requires|must already assume|"
            r"denies dependence while functioning)\b"
        ),
    ),
    (
        "M1",
        re.compile(
            r"(?i)\b(?:self[- ]refutation|self[- ]grounding|self[- ]authoriz\w+|"
            r"self[- ]enthronement|internal[- ]contradiction|own standard|"
            r"own rules?|unproved premise|unsupported premise|premise (?:must be )?established|"
            r"imported premise|loaded premise|disputed premise|inserted premise|"
            r"premise (?:is )?(?:imported|loaded|disputed|inserted|not established)|"
            r"checks whether .* (?:established|imported)|must prove|"
            r"assum(?:e|es|ed|ing) (?:the )?(?:very )?conclusion|begs? the question|"
            r"own (?:source[- ]appeal|textual|evidential|proof[- ]stack) standard|"
            r"own appeal to (?:scripture|the source|the text|evidence)|"
            r"circular (?:protection|appeal|source[- ]order|proof[- ]stack)|"
            r"proof[- ]stack becomes circular|cannot be falsified|pre[- ]controls?|"
            r"by its own rule|(?:cannot|can it|whether .* can) authorize its own verdict|"
            r"own verdict|collapses under its own)\b"
        ),
    ),
    (
        "M2",
        re.compile(r"(?i)\b(?:prior probability|probability prior|antecedent plausibility|prior plausibility)\b"),
    ),
    (
        "M3",
        re.compile(
            r"(?i)\b(?:orphaned intuition|ungrounded intuition|intuition without|moral intuition|"
            r"orphaned moral|ground is orphaned|grounded? intuition|intuition has a home|"
            r"moral deliverance|moral recognition|recognition remains honored|retained while its ground|"
            r"binding (?:moral )?judgments?|moral terms as more than|borrowed moral capital|"
            r"moral[- ]purpose|moral obligation|objective obligation|intrinsic dignity|"
            r"final human purpose|teleological intuitions?|inherited moral furniture|"
            r"preference can describe|convention can describe|utility can describe|"
            r"moral tribunal|standard of justice|verdict binding)\b"
        ),
    ),
    (
        "M4",
        re.compile(r"(?i)\b(?:grief register|grief|pain register|pastoral hold|wound|lament)\b"),
    ),
    (
        "M5",
        re.compile(r"(?i)\b(?:deformation triage|triage|deformation|sort(?:s|ing) the deformation|D[1-7])\b"),
    ),
    (
        "M6",
        re.compile(r"(?i)\b(?:excluded middle|either.*or|cannot be both|binary|middle option)\b"),
    ),
    (
        "M7",
        re.compile(
            r"(?i)\b(?:definition anchor|definition discipline|define|definition|defined term|"
            r"terms?|lexical|semantic anchor|meaning|relation|what .* means)\b"
        ),
    ),
    (
        "M8",
        re.compile(
            r"(?i)\b(?:consequence trace|if (?:the )?.*?(?:granted|holds|accepted)|what follows|"
            r"entails?|consequence|self[- ]undermining|vacuous|would make|leads to|"
            r"dependency trace|dependency[- ]trace|dependency chain|dependency edge|"
            r"dependency carrier|depends on|dependent on|borrowed .* capital|"
            r"non[- ]load[- ]bearing dependency)\b"
        ),
    ),
    (
        "M9",
        re.compile(
            r"(?i)\b(?:predication|predicate|category|referent|semantic|sense|attributive|"
            r"adverbial|identity|person/nature|mode of predication|category transfer)\b"
        ),
    ),
    (
        "DO_ATTRIBUTE",
        re.compile(
            r"(?i)\b(?:attribute[- ]precision|person/nature|attribute multiplicity|"
            r"divine attribute|model identification|composition|dependence|category confusion|"
            r"person-level|nature-level|multiplicity)\b"
        ),
    ),
    (
        "DO_CHRISTIAN",
        re.compile(
            r"(?i)\b(?:Christian theological pressure|Trinitarian model|Trinity model|"
            r"model[- ]identification|model[- ]shift|model[- ]pressure|"
            r"Trinitarian predication model|identity-style|social Trinitarian|"
            r"relative identity|mystery|person/nature|DO-1[1-4]|canon authority|"
            r"coherence burden|Christian overlay)\b"
        ),
    ),
    (
        "DO_SECOND_LOOP",
        re.compile(
            r"(?i)\b(?:DO[- ]second[- ]loop|hujjah|á¸¥ujjah|warning|record|"
            r"prophetic authority|moral protest|Great Pumpkin|cognitive science|"
            r"CSR|HADD|necessary-knowledge|accountability|guidance architecture|"
            r"family-local load floor)\b"
        ),
    ),
    (
        "PROOF_METHOD",
        re.compile(
            r"(?i)\b(?:proof[- ]method|proof grammar|proof family|method audit|"
            r"formal derivation|logic tree|inferential standard|what the proof establishes|"
            r"proof carrier|premise[- ]set|inference grammar|conclusion scope|"
            r"premise strength|invalid inference|proof[- ]overreach)\b"
        ),
    ),
    (
        "E1",
        re.compile(r"(?i)\b(?:broaden(?:ing)? evidence|wider evidence|evidence base|additional evidential register)\b"),
    ),
    (
        "E2",
        re.compile(r"(?i)\b(?:inferential criterion|criterion for inference|what would count|inference rule)\b"),
    ),
    (
        "E3",
        re.compile(r"(?i)\b(?:cumulative case|cumulative|combined evidence|convergent case)\b"),
    ),
    (
        "E4",
        re.compile(r"(?i)\b(?:cross[- ]cultural|across cultures|cultural check|cross[- ]tradition)\b"),
    ),
    (
        "F1",
        re.compile(r"(?i)\b(?:supra[- ]rational|anti[- ]rational|above reason|against reason)\b"),
    ),
    (
        "F2",
        re.compile(r"(?i)\b(?:volitional|will|desire|refusal|volition)\b"),
    ),
    (
        "F3",
        re.compile(r"(?i)\b(?:practice|epistemic access|access through practice|lived practice|practical access)\b"),
    ),
    (
        "R1",
        re.compile(r"(?i)\b(?:internalist criterion|internal criterion|from within|own criterion)\b"),
    ),
    (
        "R2",
        re.compile(r"(?i)\b(?:reminder|dhikr|recall|reorients? attention|already know)\b"),
    ),
    (
        "R3",
        re.compile(r"(?i)\b(?:warranted basic belief|basic belief|properly basic|warrant without inference)\b"),
    ),
    (
        "SOURCE",
        re.compile(
            r"(?i)\b(?:source[- ]status|source status|authority[- ]order|source authority|"
            r"source[- ]order|source lineage|source priority|evidential dependency|"
            r"inherited[- ]claim(?: order)?|quotation order|Qur'?anic source order|revealed source(?:s| order)?|"
            r"moral bench|external tribunal|final authority|higher court|"
            r"proof[- ]stack|broader proof[- ]texts?|hidden rescue|"
            r"source-correct(?:ed|ion)|revelation define|let revelation define|"
            r"source-use|source[- ]functions?|source[- ]function[- ][a-z-]+|source-prestige|source accumulation|proof[- ]text|"
            r"guidance[- ]order|guidance[- ]vs[- ]compulsion|guidance and compulsion|"
            r"revelation (?:guides|warns|clarifies|invites)|conveyance and warning|"
            r"outward clarification|inward granting|tawf[iī]q|warner|non[- ]coercive guidance|"
            r"citation|cited|override|overriding|governing source|text under dispute|"
            r"hidden support|unworked material|what source has authority|scoped closure|"
            r"doctrine[- ](?:shield|protection|prestige)|doctrinal (?:shield|protection|prestige|status)|"
            r"sacred doctrine|doctrine as (?:shield|protection)|"
            r"total[- ]system exhaustion|new text|new doctrine)\b"
        ),
    ),
    (
        "P2",
        re.compile(
            r"(?i)\b(?:objection mapping|maps? the objection|claim map|support map|"
            r"objection structure|claim[- ]reconstruction|objection[- ]topology|"
            r"structured claim|load[- ]bearing parts)\b"
        ),
    ),
    (
        "P3",
        re.compile(
            r"(?i)\b(?:reason/revelation|reason[- ]revelation|reason and revelation|"
            r"revelation tension|ʿaql|naql)\b"
        ),
    ),
    (
        "P4",
        re.compile(r"(?i)\b(?:maieutic|elicits?|questioning|draws out|asks the interlocutor)\b"),
    ),
    (
        "P5",
        re.compile(r"(?i)\b(?:already[- ]believing|internal repair|believer|within commitment|Muslim internal)\b"),
    ),
    (
        "P6",
        re.compile(
            r"(?i)\b(?:universal aqidah|universal ʿaqīdah|aqidah principle|creedal principle|"
            r"worldview[- ]binding|binding normativity|binding worldview|binds public reason|"
            r"public reason|moral authority|human purpose|final tribunal|chosen authority order)\b"
        ),
    ),
    (
        "P7",
        re.compile(
            r"(?i)\b(?:proof[- ]carousel|stop condition|STOP|HOLD|PARTIAL|scope boundary|"
            r"boundedness|bounded (?:closure|refutation|reply|answer|claim|exchange)|"
            r"local (?:closure|refutation|stop condition|reply)|scope gate|"
            r"total[- ]system exhaustion|reopen (?:condition|gate)|non[- ]load[- ]bearing|"
            r"held route|closure boundary|new burden territory)\b"
        ),
    ),
    (
        "LOOPBREAK",
        re.compile(
            r"(?i)\b(?:LoopBreak|loop break|circularity|circular structure|cycle|churn|"
            r"outside the loop|breaks? the loop)\b"
        ),
    ),
    (
        "P1",
        re.compile(
            r"(?i)\b(?:restoration|restore|positive orientation|sound orientation|fitrah|"
            r"tawhid|reorients?|returns? the field|restored source[- ]owned frame|"
            r"capacity, access|access, clarity|clear warning|honest (?:engagement|inquiry)|"
            r"humane criterion)\b"
        ),
    ),
    (
        "DOUBT_SKEPTICISM",
        re.compile(
            r"(?i)\b(?:doubt[- ]vs[- ]skepticism|normal doubt|skepticism as (?:ideology|methodology)|"
            r"skeptical methodology|evidence demand|absence of evidence|modal veto|"
            r"bare imagined possibility|alternative description|anomaly|background commitments|"
            r"burden[- ]of[- ]proof inversion|total possibility[- ]exhaustion|doubt function)\b"
        ),
    ),
)

GENERIC_OWNER_ACTIVATION_RE = re.compile(
    r"(?i)\b(?:validated state|matched owner|matched TTP|source[- ]owned|owner[- ]specific|"
    r"entry criteria|exit criteria|state change|burden[- ]local result|contribution to land|"
    r"route(?:d|s)? to Layer B|operation shape|operator function)\b"
)
SOURCE_EXECUTION_RE = re.compile(
    r"(?i)\b(?:revelation (?:guides|warns|clarifies|invites)|conveyance|warning|"
    r"outward clarification|inward granting|tawf[iī]q|non[- ]coercive|coercive|"
    r"compulsion|source[- ]function|source[- ]order filter|authority transfer|"
    r"who (?:gave|grants)|exclude revelation|source[- ]status (?:separated|sorted|repaired)|"
    r"exegetical warrant|textual warrant|proof[- ]stack|broader proof[- ]texts?|"
    r"hidden rescue|hidden authority|judge over the text|source[- ]order office|"
    r"non[- ]load[- ]bearing rescue material)\b"
)
DO_SECOND_LOOP_ACTION_RE = re.compile(
    r"(?is)\b(?:bound|bounds|bounded|narrow|narrows|narrowed|calibrate|calibrates|"
    r"calibrated|separate|separates|separated|sequence|sequenced|warn|warning|"
    r"guide|guidance|persuade|persuasion|coerce|coercion|compel|compelling)\b"
)
OWNER_NAME_ONLY_RE = re.compile(
    r"(?i)\b(?:"
    r"is named here|"
    r"named here,\s*so|"
    r"owner\s+is\s+named,\s*so\s+(?:the\s+)?"
    r"(?:proof\s+carrier|carrier|proof\s+packet|proof\s+route\s+status|"
    r"foreign-premise-detection\s+route|route)\s+is\s+handled|"
    r"(?:Land\([^)]*\):\s*)?(?:the\s+)?route\s+is\s+handled"
    r")\b"
)
V10_ACTION_RE = re.compile(
    r"(?is)\b(?:vets?|vetting|sorts?|sorted|orders?|ordered|bounds?|bounded|"
    r"constrains?|constrained|limits?|limited)\b"
)
V10_NEGATED_ACTION_RE = re.compile(
    r"(?is)\b(?:does\s+not|did\s+not|not|without)\s+(?:\w+\s+){0,4}"
    r"(?:vet|vets|vetting|sort|sorts|sorted|order|orders|ordered|"
    r"bound|bounds|bounded|constrain|constrains|constrained|limit|limits|limited)\b"
)
V10_PROVENANCE_RE = re.compile(
    r"(?is)\b(?:provenance|transmission|textual field|source pressure|source chain|"
    r"public materials|published tenets|public positions|public[- ]source)\b"
)
V10_CONTENT_RE = re.compile(
    r"(?is)\b(?:content|what they actually assert|content[- ]based|public claims|"
    r"belief[- ]system critique)\b"
)
V10_AUTHORITY_RE = re.compile(
    r"(?is)\b(?:authority|authority/status|status|standard|citation discipline|"
    r"source role|source function)\b"
)
V10_STATE_RE = re.compile(
    r"(?is)\b(?:sorted|bounded|ordered|constrained|limited|harmonization|"
    r"valid discharge|public materials|content[- ]based|private motive|identity proof)\b"
)
DOUBT_SINCERE_RE = re.compile(
    r"(?is)\b(?:sincere doubter?|sincere doubt|normal doubt|concrete doubt|"
    r"honest doubt|real doubt|doubt function|confused seeker|wounded protester|"
    r"person seeking clarity|real struggle|sincere uncertainty|honest question)\b"
)
DOUBT_METHOD_RE = re.compile(
    r"(?is)\b(?:skeptic(?:al|ism)?[- ]method|skeptical[- ]methodology|self[- ]sealing skeptic|"
    r"self[- ]sealing standards?|evidence[- ]demand tribunal|evidence bar|"
    r"self[- ]authored terms|final tribunal|burden inversion|proof[- ]demand)\b"
)
DOUBT_ACTION_RE = re.compile(
    r"(?is)\b(?:distinguish(?:es|ed|ing)?|separat(?:e|es|ed|ing)|expos(?:e|es|ed|ing)|"
    r"blocks?|no longer conflated)\b"
)


def v10_operation_performed(combined: str) -> bool:
    """Accept V10 only when provenance/content/authority are positively worked."""
    for match in V10_ACTION_RE.finditer(combined):
        prefix = combined[max(0, match.start() - 32) : match.start() + 96]
        window = combined[match.start() : match.start() + 900]
        if V10_NEGATED_ACTION_RE.search(prefix) or V10_NEGATED_ACTION_RE.search(window[:180]):
            continue
        if (
            V10_PROVENANCE_RE.search(window)
            and V10_CONTENT_RE.search(window)
            and V10_AUTHORITY_RE.search(window)
            and V10_STATE_RE.search(window)
        ):
            return True
    return False


def doubt_skepticism_operation_performed(combined: str) -> bool:
    return bool(
        DOUBT_SINCERE_RE.search(combined)
        and DOUBT_METHOD_RE.search(combined)
        and DOUBT_ACTION_RE.search(combined)
    )

OWNER_ROUTE_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:Matched owner/TTP route|Matched TTP route|"
    r"Owner/TTP route|Matched owners?|TTP route)\s*:\s*(?P<body>.+)$"
)
OWNER_ROUTE_TOKEN_RE = re.compile(
    r"(?i)(?:\[[A-Za-z][A-Za-z0-9_.\-/]*\]|\b(?:V(?:1[0-2]|[1-9])|M1-P|M[1-9]|"
    r"E[1-4]|F[1-3]|R[1-3]|P[1-7]|FPD|LoopBreak|source[- ]status|authority[- ]order|"
    r"definition[- ]discipline|transmission|testimony|restoration)\b)"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def generated_target(text: str) -> str:
    match = re.search(
        rf"(?P<target>(?:[{SUP}]+B|B\d+))\s*\[generated-by:\s*MRP\((?P<src>(?:[{SUP}]+B|B\d+))\)\]",
        text,
    )
    return match.group("target") if match else ""


def generated_source_for_target(text: str, target: str) -> str:
    match = re.search(
        rf"{re.escape(target)}\s*\[generated-by:\s*MRP\((?P<src>(?:[{SUP}]+B|B\d+))\)\]",
        text,
    )
    return match.group("src") if match else ""


def has_nonempty_b_mrp_ledger(text: str) -> bool:
    ledger_re = re.compile(
        rf"(?im)^\s*(?:[-*]\s*)?(?:{B_LEDGER}_MRP|B_MRP)\s*(?:\([^)]*\))?\s*=\s*(?P<body>.+)$"
    )
    for match in ledger_re.finditer(text):
        body = match.group("body").strip()
        if re.match(r"(?i)^(?:\{\s*\}|empty|none)\b", body):
            continue
        if re.search(rf"(?:[{SUP}]+B|B\d+)", body):
            return True
    return False


def count_complete_submoves(section: str, target: str) -> int:
    heading_re = re.compile(
        rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(target)}(?:[{SUB}]+|[_\.]\d+)\s*"
        rf"\[[A-Za-z][A-Za-z0-9/-]*\](?:\s*\([^)]*\))?\s*(?:[-\u2014:]).*$"
    )
    headings = list(heading_re.finditer(section))
    complete = 0
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        block = section[match.start() : end]
        if (
            re.search(r"(?im)^\s*-?\s*Target\s*:", block)
            and re.search(r"(?im)^\s*-?\s*Operation\s*:", block)
            and re.search(r"(?im)^\s*-?\s*Result(?:/state-change)?\s*:", block)
            and re.search(r"(?im)^\s*-?\s*Contribution-to-Land(?:\([^)]*\))?\s*:", block)
        ):
            complete += 1
    return complete


def split_mrp_blocks(text: str) -> list[str]:
    pieces = re.split(r"(?im)^\s*\[Mid-Reread Pressure\]\s*$", text)
    blocks: list[str] = []
    for piece in pieces[1:]:
        end = re.search(
            r"(?im)^\s*(?:#{1,6}\s*)?(?:Burden\s+\d+|Restorative Response|Closing Formulation|Closure/Reconstruction Witness|field_witness)\b",
            piece,
        )
        blocks.append(piece[: end.start()] if end else piece)
    return blocks


def held_route_false_closure_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    line_candidates = re.findall(r"(?im)^\s*(?:[-*]\s*)?R\(H,\s*(?:\u0394|Delta)\)\s*:\s*(.+)$", text)
    block_candidates = split_mrp_blocks(text)
    closure_tail = text[text.find("Closure/Reconstruction Witness") :] if "Closure/Reconstruction Witness" in text else ""
    candidates = line_candidates + block_candidates + ([closure_tail] if closure_tail else [])
    for candidate in candidates:
        if not candidate.strip():
            continue
        if (
            HIGH_LEVERAGE_HELD_ROUTE_RE.search(candidate)
            and UNROUTED_HELD_ROUTE_RE.search(candidate)
            and TERMINAL_CLOSURE_RE.search(candidate)
            and not ROUTING_OR_BOUNDARY_PROOF_RE.search(candidate)
        ):
            errors.append(
                f"{path}: R(H,Δ) detected a pertinent high-leverage held route, but output claimed STOP/collapse without working, generating, HOLD/PARTIAL-routing, or proving non-load-bearing status"
            )
            break
    if (
        HIGH_LEVERAGE_HELD_ROUTE_RE.search(text)
        and UNROUTED_HELD_ROUTE_RE.search(text)
        and re.search(r"(?im)^\s*Route\s*:\s*STOP\b", text)
        and re.search(r"(?i)\b(?:collapse achieved|coverage_complete\s*=\s*true|COMPLETE|no remaining live problem)\b", text)
        and not ROUTING_OR_BOUNDARY_PROOF_RE.search(text)
    ):
        errors.append(
            f"{path}: detected route is TTP-addressable and high-leverage, but output treats it as beyond prompt while claiming complete collapse"
        )
    return errors


def submove_heading_ref_pattern(target: str) -> str:
    target = str(target or "").strip()
    ascii_target = ""
    public_target = ""
    match = re.fullmatch(r"B([1-9][0-9]*)", target)
    if match:
        ascii_target = f"B{match.group(1)}"
        public_target = f"{match.group(1).translate(ASCII_TO_SUP_DIGITS)}B"
    else:
        match = re.fullmatch(rf"([{SUP}]+)B", target)
        if match:
            ascii_target = f"B{match.group(1).translate(SUP_DIGITS)}"
            public_target = target
    if not ascii_target:
        return re.escape(target)
    return rf"(?:{re.escape(ascii_target)}(?:[{SUB}]+|[_\.]\d+)|{re.escape(public_target)}(?:[{SUB}]+|[_\.]\d+))"


def submove_blocks(section: str, target: str) -> list[str]:
    ref_pattern = submove_heading_ref_pattern(target)
    heading_re = re.compile(
        rf"(?im)^\s*(?:#{{1,6}}\s*)?{ref_pattern}\s*"
        rf"\[[A-Za-z][A-Za-z0-9/-]*\](?:\s*\([^)]*\))?\s*(?:[-\u2014:]).*$"
    )
    headings = list(heading_re.finditer(section))
    blocks: list[str] = []
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        blocks.append(section[match.start() : end])
    return blocks


def canonical_submove_ref(value: str) -> str:
    text = str(value or "").strip()
    match = re.fullmatch(rf"([{SUP}]+)B([{SUB}]+)", text)
    if match:
        return f"B{match.group(1).translate(SUP_DIGITS)}_{match.group(2).translate(SUB_DIGITS)}"
    match = re.fullmatch(r"B([1-9][0-9]*)[_\.]([1-9][0-9]*)", text)
    if match:
        return f"B{match.group(1)}_{match.group(2)}"
    return text


def submove_block_ref(block: str) -> str:
    heading = next((line.strip() for line in block.splitlines() if line.strip()), "")
    match = re.search(
        rf"(?P<ref>(?:[{SUP}]+B|B\d+)(?:[{SUB}]+|[_\.]\d+))\s*\[",
        heading,
    )
    return match.group("ref") if match else ""


def submove_blocks_by_ref(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for target, _generated, section in burden_sections(text):
        for block in submove_blocks(section, target):
            ref = submove_block_ref(block)
            if ref:
                blocks.setdefault(canonical_submove_ref(ref), block)
    return blocks


def field_body(block: str, name: str) -> str:
    match = re.search(rf"(?im)^\s*-?\s*{re.escape(name)}\s*:\s*(?P<body>.+)$", block)
    return match.group("body").strip() if match else ""


def field_body_any(block: str, names: tuple[str, ...]) -> str:
    for name in names:
        value = field_body(block, name)
        if value:
            return value
    return ""


def submove_field_values(block: str) -> list[str]:
    values = [
        field_body(block, "Target"),
        field_body_any(block, ("Operation", "What it does")),
        field_body_any(block, ("Result", "Result/state-change")),
    ]
    contribution = re.search(
        r"(?im)^\s*-?\s*Contribution-to-Land(?:\([^)]*\))?\s*:\s*(?P<body>.+)$",
        block,
    )
    if contribution:
        values.append(contribution.group("body").strip())
    return [value for value in values if value]


def submove_operation_body(block: str) -> str:
    """Return prose body lines beyond the compact Target/Operation/Result fields.

    Compact decode fields (Target:/Operation:/Result:/Contribution-to-Land:) precede the
    ``TTP Operation Body:`` section and are captured in dedicated facets, so they are
    stripped here. But the local-proof capsule INSIDE that section uses sub-markers
    (BEFORE:/OPERATION:/AFTER:/DELTA:/LAND-LICENSE:) whose lines carry substantive prose.
    ``OPERATION:`` collides case-insensitively with the compact ``Operation:`` field
    label, so once we are inside the operation-body section we stop stripping field-label
    lines -- otherwise the capsule OPERATION prose (e.g. the hidden-rule exposure the NLA
    decode check looks for) would be dropped and the body would read as incomplete.
    """
    body_lines: list[str] = []
    in_operation_body = False
    for raw_line in block.splitlines()[1:]:
        line = raw_line.strip()
        if not line:
            if body_lines and body_lines[-1] != "":
                body_lines.append("")
            continue
        if re.match(rf"(?im)^\s*(?:#{{1,6}}\s*)?(?:[{SUP}]+B|B\d+)(?:[{SUB}]+|[_\.]\d+)\s*\[", line):
            continue
        if re.match(r"(?im)^\s*(?:TTP\s+)?Operation Body\s*:", line):
            # The capsule section is now open. A standalone marker line is dropped; an
            # inline "TTP Operation Body: BEFORE ..." keeps its trailing prose.
            in_operation_body = True
            if re.match(r"(?im)^\s*(?:TTP\s+)?Operation Body\s*:\s*$", line):
                continue
        if not in_operation_body and FIELD_LABEL_RE.match(line):
            continue
        if re.match(r"(?im)^\s*(?:#|Land\(|\[Mid-Reread Pressure\]|R\(H,)", line):
            continue
        body_lines.append(line)
    return "\n".join(body_lines).strip()


def paragraph_count(text: str) -> int:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text.strip()) if chunk.strip()]
    return len(chunks)


def section_after_heading(text: str, heading: str) -> str:
    match = re.search(rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(heading)}\s*$", text)
    if not match:
        return ""
    tail = text[match.end():]
    end = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:Restorative Response|Closing Formulation|Closure/Reconstruction Witness|field_witness|Legend)\s*$",
        tail,
    )
    return tail[: end.start()] if end else tail


def anchored_heading_position(text: str, heading: str) -> int:
    match = re.search(rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(heading)}\s*$", text)
    return match.start() if match else -1


PUBLIC_TAIL_LABEL_RE = re.compile(
    r"(?i)^\s*(?:response|restorative response|closing|closed|complete|done|answered|"
    r"refuted|summary|closure)\.?\s*$"
)
RESTORATIVE_ORDER_RE = re.compile(
    r"(?i)\b(?:restor(?:e|ed|es|ation)|reorient|return(?:s|ed)?|sound|fitrah|tawhid|"
    r"source[- ]owned|criterion|warrant|source order|orientation|bounded|scope|clarity|"
    r"proper order|proper home|exclusive predicate|sender/sent|model and the rule|principled rule)\b"
)
RESTORATIVE_RELIEF_RE = re.compile(
    r"(?i)\b(?:reliev(?:e|es|ed|ing)?|prevent(?:s|ed|ing)?|block(?:s|ed|ing)?|"
    r"bar(?:s|red|ring)?|clear(?:s|ed|ing)?|separat(?:e|es|ed|ing)?|"
    r"deformation|concealment|hidden|"
    r"pressure|proof[- ]stack|smuggl|burden|route|claim|fails?|does not answer|"
    r"false shape|error|autonom(?:y|ous)|orphan(?:ed|ing)|not self[- ]explaining|"
    r"no longer|cannot|refus(?:e|es|ed|ing)|demot(?:e|es|ed|ing)|not load[- ]bearing)\b"
)
RESTORATIVE_REMAINDER_RE = re.compile(
    r"(?i)\b(?:remain|held|scope|bounded|partial|reopen|generated|non[- ]load[- ]bearing|"
    r"what was proven|what failed|what remains|concrete defeater|determinate defeater|"
    r"strongest version|keep .* but|burden remains|give (?:the )?(?:model|rule)|"
    r"door open|if the real question|let the warrant stand)\b"
)
CLOSING_FAILURE_RE = re.compile(
    r"(?i)\b(?:fails?|failure|cannot|does not|blocked|barred|invalidated|undermined|"
    r"loses?|defeated|not evidence|cannot repair|collapse)\b"
)
CLOSING_ORIENTATION_RE = re.compile(
    r"(?i)\b(?:criterion|source|warrant|orientation|scope|bounded|local|ledger|Land|"
    r"generated|burden|route|proof|claim)\b"
)
CLOSING_BOUNDARY_RE = re.compile(
    r"(?i)\b(?:held|reopen|reopenable|new burden|scope|scoped|bounded|partial|non[- ]load[- ]bearing|"
    r"without pretending|does not exhaust|cannot repair|honest scope)\b"
)
CLOSING_ESTABLISHED_SLOT_RE = re.compile(
    r"(?im)^\s*(?:(?:#{1,6}\s*)?Established failure\s*$|(?:[-*]\s*)?Established failure\s*:\s*[^\n]*\S)"
)
CLOSING_RESTORED_SLOT_RE = re.compile(
    r"(?im)^\s*(?:(?:#{1,6}\s*)?Restored criterion/orientation\s*$|(?:[-*]\s*)?Restored criterion/orientation\s*:\s*[^\n]*\S)"
)
CLOSING_BOUNDARY_SLOT_RE = re.compile(
    r"(?im)^\s*(?:(?:#{1,6}\s*)?(?:Scoped boundary|Reopen boundary)\s*$|(?:[-*]\s*)?(?:Scoped boundary|Reopen boundary)\s*:\s*[^\n]*\S)"
)
COMPLIANCE_UPTAKE_RE = re.compile(
    r"(?i)\b(?:"
    r"interlocutor\s+(?:will|must|now)\s+(?:accept|concede|see|recognize|submit)|"
    r"(?:will|must|now)\s+(?:accept|concede|see|recognize|submit)\s+(?:the\s+)?(?:truth|claim|answer)|"
    r"has\s+no\s+choice\s+but\s+(?:to\s+)?(?:accept|concede|submit)|"
    r"this\s+resolves\s+(?:his|her|their|the)\s+doubt"
    r")\b"
)
# The bare concession phrase ("cannot deny/resist/avoid conceding") is FAIL-CLOSED: every
# occurrence flags (see compliance_side_success_present). The former logical-scope carve-out
# ("the argument/predicate cannot deny X unless built into P") was removed because its subject
# parser laundered self-asserted person concessions; such prose now over-flags (accepted), and
# no real fixture/smoke output emits it.
COMPLIANCE_CONCESSION_RE = re.compile(r"(?i)\bcannot\s+(?:deny|resist|avoid\s+conceding)\b")
# A governing prohibition/negation in the same clause turns an uptake phrase into
# an ANTI-uptake directive ("Do not promise that the interlocutor will accept ...",
# "must not claim that the audience will now accept ...") -- the safety-correct
# stance the guard exists to protect, which must NOT flag. This is a negative guard,
# not a person allowlist; direct affirmative uptake claims (no governing prohibition)
# still flag.
# A prohibition governs the uptake only when a negation is attached to a
# COMMITMENT verb (do not PROMISE / must not CLAIM that ...). Requiring the
# commitment verb keeps a litotes ("It is not SURPRISING that X will accept")
# or a contrastive affirmation ("not merely HOPE but demonstrate that X will
# accept") -- both direct uptake claims -- flagging.
UPTAKE_PROHIBITION_RE = re.compile(
    r"(?i)\b(?:not|never|n['’]t|no|refuse[sd]?|avoid(?:s|ed|ing)?|forbid(?:s|den|ding)?|"
    r"prohibit(?:s|ed|ing)?|disallow(?:s|ed|ing)?)\b"
    # A contrastive intensifier ("not merely/only/just claim ... BUT demonstrate")
    # is an affirmation of the uptake, not a prohibition -> do not treat as a guard.
    r"(?!\s+(?:merely|only|just|simply|solely|alone))"
    r"[^.!?;:\n]{0,30}?\b(?:promise|promising|claim|claiming|guarantee|guaranteeing|"
    r"assert|asserting|say|saying|state|stating|pretend|pretending|declare|declaring|"
    r"insist|insisting|ensure|ensuring|certify|certifying|warrant|warranting|"
    r"maintain|maintaining|suggest|suggesting|imply|implying|assume|assuming|"
    r"conclude|concluding|represent|representing)\b"
)
# NOTE: the report/disown-frame exemption (CONCESSION_REPORTING_FRAME_RE / CONCESSION_DISOWN_RE)
# and the logical-scope subject-head exemption (ARG_SUBJECT_TERMS + the subject-parser regexes
# CONCESSION_SUBJECT_MODIFIER_RE / CONCESSION_SUBORDINATE_LEAD_ONLY_RE / CONCESSION_LEADING_RE /
# CONCESSION_ARTICLE_RE + CONCESSION_LOGICAL_MARKER_RE) were REMOVED. Both laundered self-asserted
# uptake across adversarial-review rounds and regex could not close the class (see
# compliance_side_success_present). The concession path is fail-closed; do NOT re-add these.


def _clause_before(text: str, start: int) -> str:
    """Return the concession/uptake phrase's OWN clause, back to the last comma / semicolon /
    colon / sentence terminator OR clause-coordinating conjunction (and/but/yet/so/...). A
    governing prohibition ("do not promise that X will accept") stays attached only when it
    directly governs the uptake phrase; a prohibition on a DIFFERENT prior-clause subject
    joined by "and"/comma ("Do not overpromise, and the interlocutor will accept ...") is
    excluded so it cannot suppress a separately-asserted uptake claim."""
    lo = max(0, start - 160)
    segment = text[lo:start]
    boundary = None
    for match in re.finditer(
        r"[,;:\n.!?—–]|\s-\s|"
        r"\b(?:and|but|yet|so|therefore|thus|hence|nor|once|when|whenever|because|since|"
        r"after|before|while|whilst|although|though)\b",
        segment,
    ):
        boundary = match
    if boundary is not None:
        segment = segment[boundary.end() :]
    return segment


# NOTE: the quoted-concession EXEMPTION (CONCESSION_LEFT/RIGHT_QUOTE, _CONCESSION_CLAIM_NOUN,
# CONCESSION_ATTRIBUTION_RE, and _concession_quoted) was fully REMOVED. Four adversarial-review
# rounds each defeated it -- scare-quote, possessive/saying frame, temporal/subjunctive gate,
# and negated hypothesis -- because regex cannot reliably distinguish an entertained hypothesis
# from a self-assertion wrapped in quotes. Per the never-launder invariant (never suppress a
# self-asserted person-uptake concession; a rare genuine reported/hypothesized concession is an
# accepted conservative over-flag), no quote frame exempts a concession. Do NOT re-add a quote
# exemption. The report/disown-frame exemption (CONCESSION_REPORTING_FRAME_RE /
# CONCESSION_DISOWN_RE) was ALSO removed in a later round (it laundered across em-dash /
# subordinator / linking-verb connectors); those regexes are now unused. The only concession-
# path exemption left is a genuine logical-scope statement (argument/predicate subject + an
# explicit CONCESSION_LOGICAL_MARKER_RE marker) in compliance_side_success_present.
_REMOVED_CONCESSION_QUOTE_EXEMPTION = True  # marker; see compliance_side_success_present


def compliance_side_success_present(text: str) -> bool:
    """Detect compliance-side-success / guaranteed-uptake claims.

    Two paths:
      * UPTAKE ("the interlocutor will accept ...") flags UNLESS a governing anti-uptake
        prohibition ("do not promise/claim that X will accept ...") sits in the same clause
        (UPTAKE_PROHIBITION_RE) -- the safety-correct directive the output is allowed to emit.
      * CONCESSION ("cannot deny/resist/avoid conceding") is FAIL-CLOSED: every match flags.
        All concession exemptions (quote, report/disown, logical-scope subject-head) were
        removed after six adversarial-review rounds each laundered self-asserted uptake and
        regex could not close the class. A rare logical-scope "the argument cannot deny X
        unless built into P" is an ACCEPTED conservative over-flag; never-launder outranks
        logical-scope permissiveness (owner decision). No real fixture/smoke output contains a
        concession, so nothing real is over-flagged.
    """
    for match in COMPLIANCE_UPTAKE_RE.finditer(text):
        # A prohibition governing the uptake phrase in the same clause ("Do not
        # promise that the interlocutor will accept ...") is an anti-uptake
        # directive, not an uptake claim -> do not flag.
        clause_before = _clause_before(text, match.start())
        if UPTAKE_PROHIBITION_RE.search(clause_before):
            continue
        return True
    for _match in COMPLIANCE_CONCESSION_RE.finditer(text):
        # FAIL-CLOSED concession path (owner decision after six adversarial-review rounds):
        # every "cannot deny/resist/avoid conceding" concession flags. All three concession-
        # path exemption guards were removed because each was repeatedly laundered and regex
        # cannot close the class:
        #   * QUOTE exemption -- scare-quote, possessive/saying frame, temporal/subjunctive
        #     gate ("when one reads my proof ..."), negated hypothesis ("no need to imagine
        #     the claim is ...; it is fact").
        #   * REPORT/DISOWN exemption -- an unbounded set of connectors (em-dash, subordinators
        #     once/when/because, linking verbs means/proves/forces) carried the frame across a
        #     clause into a separately-asserted concession.
        #   * LOGICAL-SCOPE subject-head exemption -- compound coordination, appositives,
        #     nominative absolutes, missing commas, and prepositional/concessive adjuncts
        #     ("the skeptic near/despite/without the argument ... cannot deny ... unless P")
        #     inject an argument-term the parser mis-reads as the subject; a logical marker can
        #     always be co-supplied, so requiring one did not close the class. Regex cannot
        #     robustly identify the grammatical subject.
        # NO valid fixture or smoke output contains a "cannot deny/resist" concession (0 across
        # every valid fixture and smoke, including formal Khaybar), so this over-flags nothing
        # real; a rare logical-scope "the argument cannot deny X unless built into P" is an
        # ACCEPTED conservative over-flag. Never-launder outranks logical-scope permissiveness.
        # The anti-uptake DIRECTIVE guard on the uptake path above (UPTAKE_PROHIBITION_RE) is a
        # separate path and remains, protecting explicit "do not promise/claim uptake" prose.
        return True
    return False
INTERIOR_CERTIFICATION_RE = re.compile(
    r"(?i)\b(?:interlocutor|target|person|he|she|they)\s+(?:is|are)\s+"
    r"(?:insincere|lying|a\s+hypocrite|outside\s+(?:the\s+)?faith|k[aā]fir|mun[aā]fiq)\b|"
    r"\b(?:confirmed|certified)\s+(?:insincere|hypocrite|k[aā]fir|mun[aā]fiq|outside\s+(?:the\s+)?faith)\b"
)
FABRICATED_VALIDATION_VERDICT_RE = re.compile(
    r"^\s*(?:[-*]\s*)?"
    r"(?:validation|validator(?:\s+verdict)?|quality[- ]gate|checker|release_validation)"
    r"\s*:\s*(?:PASS|GREEN|OK|SUCCESS)\b|"
    r"\b(?:all|the)\s+(?:validators|quality[- ]gates|checks)\s+"
    r"(?:passed|pass|are\s+green)\b",
    re.IGNORECASE | re.MULTILINE,
)


def public_tail_label_like(body: str) -> bool:
    cleaned = re.sub(r"\s+", " ", body.strip(" .;:-")).strip()
    return not cleaned or bool(PUBLIC_TAIL_LABEL_RE.fullmatch(cleaned))


def public_tail_quality_errors(path: Path, text: str, hard_anchor_hits: int) -> list[str]:
    if hard_anchor_hits < 4:
        return []
    errors: list[str] = []
    restorative = section_after_heading(text, "Restorative Response")
    closing = section_after_heading(text, "Closing Formulation")
    if restorative:
        if public_tail_label_like(restorative) or not (
            RESTORATIVE_ORDER_RE.search(restorative)
            and RESTORATIVE_RELIEF_RE.search(restorative)
            and RESTORATIVE_REMAINDER_RE.search(restorative)
        ):
            errors.append(
                f"{path}: Restorative Response is not reconstructible for high-mass governed output; it must identify restored order/criterion, relieved pressure, and what remains held or scoped"
            )
    if closing:
        if public_tail_label_like(closing) or not (
            CLOSING_FAILURE_RE.search(closing)
            and CLOSING_ORIENTATION_RE.search(closing)
            and CLOSING_BOUNDARY_RE.search(closing)
        ):
            errors.append(
                f"{path}: Closing Formulation is not reconstructible for high-mass governed output; it must name the established failure, restored criterion/orientation, and scoped boundary or reopen condition"
            )
        missing_slots: list[str] = []
        if not CLOSING_ESTABLISHED_SLOT_RE.search(closing):
            missing_slots.append("Established failure")
        if not CLOSING_RESTORED_SLOT_RE.search(closing):
            missing_slots.append("Restored criterion/orientation")
        if not CLOSING_BOUNDARY_SLOT_RE.search(closing):
            missing_slots.append("Scoped boundary or Reopen boundary")
        if missing_slots:
            errors.append(
                f"{path}: Closing Formulation missing explicit high-mass slot(s): {', '.join(missing_slots)}"
            )
    return errors


def is_label_like_value(value: str) -> bool:
    cleaned = re.sub(r"\s+", " ", value.strip(" .;:-")).strip()
    words = re.findall(r"\b[\w'-]{3,}\b", cleaned)
    if len(words) <= 2:
        return True
    return bool(LABEL_LIKE_VALUE_RE.fullmatch(cleaned))


def has_substantive_operation_body(block: str) -> bool:
    body = submove_operation_body(block)
    if not body:
        return False
    words = re.findall(r"\b[\w'-]{4,}\b", body)
    if len(words) < 16 or sentence_count(body) < 2:
        return False
    return bool(
        OPERATION_ACTION_RE.search(body)
        or OPERATION_MECHANISM_RE.search(body)
        or STATE_CHANGE_RE.search(body)
    )


def is_label_like_submove(block: str) -> bool:
    values = submove_field_values(block)
    if len(values) < 3:
        return False
    label_like = sum(1 for value in values if is_label_like_value(value))
    substantive_words = re.findall(r"\b[\w'-]{4,}\b", " ".join(values))
    if has_substantive_operation_body(block):
        return False
    return label_like >= 3 or len(substantive_words) < 16


def sentence_count(value: str) -> int:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", value.strip()) if part.strip()]
    return len(parts) if parts else (1 if value.strip() else 0)


def submove_owner(block: str) -> str:
    heading = next((line.strip() for line in block.splitlines() if line.strip()), "")
    match = re.search(r"\[(?P<owner>[A-Za-z][A-Za-z0-9_.\-/]*)\]", heading)
    return match.group("owner") if match else ""


def owner_family(owner: str) -> str:
    normalized = owner.upper()
    if "DO-ATTRIBUTE" in normalized or "ATTRIBUTE-PRECISION" in normalized:
        return "DO_ATTRIBUTE"
    if "PROOF-METHOD" in normalized or "METHOD-AUDIT" in normalized:
        return "PROOF_METHOD"
    if re.match(r"^V10(?:\b|[-_/])", normalized):
        return "V10"
    if re.match(r"^V11(?:\b|[-_/])", normalized):
        return "V11"
    if re.match(r"^V12(?:\b|[-_/])", normalized):
        return "V12"
    if "PATTERN-PROFILING" in normalized or "PATTERN_PROFILE" in normalized:
        return "PATTERN_PROFILE"
    for code in ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9"):
        if re.match(rf"^{code}(?:\b|[-_/])", normalized):
            return code
    if re.match(r"^M1-P(?:\b|[-_/])", normalized):
        return "M1-P"
    if re.match(r"^M1(?:\b|[-_/])", normalized):
        return "M1"
    for code in ("M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"):
        if re.match(rf"^{code}(?:\b|[-_/])", normalized):
            return code
    for code in ("E1", "E2", "E3", "E4", "F1", "F2", "F3", "R1", "R2", "R3"):
        if re.match(rf"^{code}(?:\b|[-_/])", normalized):
            return code
    for code in ("P2", "P3", "P4", "P5", "P6", "P7"):
        if re.match(rf"^{code}(?:\b|[-_/])", normalized):
            return code
    if normalized.startswith("FPD") or "FOREIGN" in normalized or "PREMISE" in normalized:
        return "FPD"
    if "CHRISTIAN" in normalized:
        return "DO_CHRISTIAN"
    if "SECOND" in normalized and "LOOP" in normalized:
        return "DO_SECOND_LOOP"
    if "DOUBT" in normalized or "SKEPTIC" in normalized:
        return "DOUBT_SKEPTICISM"
    if normalized.startswith("PROOF-METHOD") or "PROOF-METHOD" in normalized or "PROOF_METHOD" in normalized:
        return "PROOF_METHOD"
    if "LOOP" in normalized:
        return "LOOPBREAK"
    if normalized.startswith("P1") or "RESTOR" in normalized:
        return "P1"
    if "DEFINITION" in normalized:
        return "M7"
    if "ATTRIBUTE" in normalized or "BILA" in normalized:
        return "V8"
    if "SOURCE" in normalized or "AUTHORITY" in normalized:
        return "SOURCE"
    if "BOUND" in normalized or "STOP" in normalized:
        return "P7"
    return ""


def owner_specific_operation_performed(owner: str, combined: str) -> bool:
    if OWNER_NAME_ONLY_RE.search(combined):
        return False
    family = owner_family(owner)
    if family == "V10":
        return v10_operation_performed(combined)
    if family == "DOUBT_SKEPTICISM":
        return doubt_skepticism_operation_performed(combined)
    if family:
        # Owner-operation keyword recognition is hyphen/space-invariant: the DSL writes
        # owner-operation deltas/targets as hyphenated slugs (e.g. "orphaned-intuition"),
        # while the OWNER_OPERATION_PATTERNS were authored with spaced bigrams (e.g.
        # "orphaned intuition"). This is pure orthography of the SAME owner concept (the
        # patterns already use [- ] equivalence in ~141 places); recognizing the canonical
        # hyphenated slug is a coverage fix, not a mass-gate change. Owner recognition is
        # one of ~8 conjunctive gates in is_operation_shaped_submove; the anti-label guard
        # (OWNER_NAME_ONLY_RE above) and the anti-slimming/mass gates are untouched, so a
        # thin/label-only slug block still fails.
        normalized = combined.replace("-", " ")
        return any(
            key == family and (pattern.search(combined) or pattern.search(normalized))
            for key, pattern in OWNER_OPERATION_PATTERNS
        )
    if not owner:
        return False
    return bool(
        GENERIC_OWNER_ACTIVATION_RE.search(combined)
        and OPERATION_ACTION_RE.search(combined)
        and STATE_CHANGE_RE.search(combined)
    )


def self_test_owner_specific_operation_patterns() -> list[str]:
    errors: list[str] = []
    if not compliance_side_success_present("The interlocutor will now accept the truth."):
        errors.append("self-test compliance-side success detector missed uptake claim")
    # Person-subject concession claims must still flag (negative guard must not
    # over-suppress); a positive person allowlist would miss these subjects.
    # Includes relative/appositive constructions where an argument load-word
    # sits immediately before "cannot" but the true subject is a person.
    for uptake in (
        "the skeptic cannot deny the evidence",
        "the audience cannot deny this once shown",
        "the reader cannot resist this conclusion",
        "The proponent of the argument cannot deny the evidence.",
        "One who accepts the premise cannot deny the conclusion.",
        "A skeptic who grants the premise cannot deny the consequence.",
        "The interlocutor who grants the proof cannot deny the result.",
        "The interlocutor who grants the proof cannot deny the result unless he recants.",
        # person subjects NOT in any hardcoded list, carried across a relative
        # clause that ends on an argument load-word before "cannot" (must flag;
        # the guard must not depend on a positive person allowlist).
        "The naysayer who grants the proof cannot deny the result unless the premise is built into P.",
        "The bystander who accepts the argument cannot deny the conclusion unless the premise entails it.",
        "The doubter who grants the formalization cannot deny the result unless the premise is built into P(x).",
        # person subject with a nonrestrictive appositive before "cannot" (must
        # flag; the appositive comma must not drop the person subject).
        "The skeptic, who has seen the proof, cannot deny the evidence.",
        "The interlocutor, given the argument, cannot deny the result unless he recants.",
        # person subject after a fronted subordinate clause with INTERNAL commas
        # (serial list / stacked clauses); the argument load-words inside the
        # fronted clause must not leak into the subject (must flag).
        "Although the argument, the proof, and the thesis were laid out, the reader cannot deny the result unless he lies.",
        "Because he studied it, although the argument is dense, the skeptic cannot deny the evidence.",
        "Because the premise, the objection, and the proof were addressed, the skeptic cannot deny the conclusion unless he recants.",
        # person subject whose appositive/absolute modifier contains a serial list
        # or is article-initial and ends on an argument term (must flag; the
        # front subject, not the modifier, governs "cannot").
        "The skeptic, who saw the proof, the objection, and the thesis, cannot deny the evidence.",
        "The reader, given the argument, the proof, and the premise, cannot deny the result.",
        "The skeptic, the objection notwithstanding, cannot deny the evidence.",
        # person concession clause joined by clause-joining punctuation to an
        # argument-word clause (must flag; the argument term is in a separate
        # clause, not the subject).
        "The proof is complete; the reader cannot deny it.",
        "The proof route becomes circular: the reader cannot deny the conclusion.",
        "The premise holds — the interlocutor cannot deny the conclusion.",
        # argument load-word as a bare attributive modifier before a person head
        # (must flag; the head, not the modifier, is the subject).
        "The reasoning interlocutor cannot deny the evidence.",
        # person subject with a comma-less participial reduced relative whose object
        # is an argument term (must flag; the person head, not the object, governs).
        "The reader granting the premise cannot deny it.",
        "Anyone accepting the proof cannot deny the conclusion.",
    ):
        if not compliance_side_success_present(uptake):
            errors.append(
                f"self-test compliance-side detector wrongly cleared person-subject uptake claim: {uptake!r}"
            )
    # ACCEPTED CONSERVATIVE OVER-FLAG (owner decision): logical-scope statements about what an
    # argument/predicate can exclude ("the argument cannot deny X unless built into P") now FLAG.
    # The guard-C logical-scope exemption was REMOVED after its subject parser laundered self-
    # asserted person concessions across six adversarial-review rounds (compound coordination,
    # appositives, nominative absolutes, missing commas, prepositional/concessive adjuncts). No
    # real fixture/smoke output emits such prose (0 "cannot deny/resist" concessions across every
    # valid fixture and smoke), so this over-flags nothing real; never-launder outranks logical-
    # scope permissiveness. These are kept here as regression canaries asserting they now flag.
    for logical_scope in (
        "But it cannot deny every attempted plot, every injury, or every later harm unless those exclusions are separately built into P.",
        "The formal tree cannot deny the weaker reading unless the stronger premise is built into P(x).",
        "The argument cannot deny successful mission-negating harm at t1 because it follows from P(t1).",
        # argument/predicate SUBJECT with an incidental person pronoun in a
        # leading subordinate clause (must NOT flag; the person term is not the
        # subject of "cannot").
        "Because they scoped P too broadly, the predicate cannot deny every case unless the exclusion is built into P.",
        "Since the proponent left P broad, it cannot deny every counterexample unless the exclusion is built into P.",
        "As the reader can check, the formula cannot deny any later martyrdom association unless it is built into P.",
        # argument/predicate subject with a nonrestrictive appositive before
        # "cannot" (must NOT flag; the subject head precedes the appositive comma).
        "The predicate, which we scoped to intentional mission-negating harm, cannot deny the weaker reading unless that exclusion is built into P.",
        "The argument, as formalized, cannot deny every attempted plot unless those exclusions are separately built into P.",
        # argument subject with a prepositional-phrase or irregular-participle
        # appositive (must NOT flag; the front argument subject governs "cannot").
        "The proposition, in its strongest form, cannot deny the counterexample unless it is built into P.",
        "The syllogism, taken in Barbara, cannot deny the case unless the premise entails it.",
        "The derivation, shown above, cannot deny the reading unless it follows from P(x).",
        # plural argument-subject heads (formerly logical-scope) now flag too.
        "Formal arguments cannot deny that overlap unless the identity is built into the predicate.",
        "These premises cannot deny the conclusion unless it follows from the antecedent.",
        # LATEST guard-C laundering cases (sixth review round: prepositional/concessive adjuncts
        # injected an argument-term the parser mis-read as the subject). With guard C removed
        # these self-asserted person concessions correctly flag.
        "The skeptic near the whole argument cannot deny the evidence unless it follows from P.",
        "The skeptic despite every objection cannot deny the evidence since it follows from P.",
        "The reader without a single counter-argument cannot resist the finding unless built into P.",
        "It cannot deny the conclusion unless that is built into the premise set.",
    ):
        if not compliance_side_success_present(logical_scope):
            errors.append(
                f"self-test: guard-C removed -> logical-scope/adjunct prose must now flag (accepted over-flag): {logical_scope!r}"
            )
    # Direct uptake / compliance-side-success claims must still flag ...
    for must_flag in (
        "The interlocutor will accept the answer.",
        "The audience will now recognize the truth.",
        "The person cannot resist the conclusion.",
        "The interlocutor has no choice but to accept.",
        # direct claims that merely CO-OCCUR with a register-native negation or
        # reporting/disown token in a separate clause must still flag (the guards
        # must be governance-scoped, not co-occurrence-scoped).
        "In the sense that matters, the skeptic cannot deny the evidence.",
        "The evidence rules out every alternative, so the skeptic cannot deny the conclusion.",
        "This argument blocks that escape route; the skeptic cannot deny the evidence.",
        "The claim is described as decisive; the skeptic cannot deny it.",
        "It is not surprising that the interlocutor will accept the answer.",
        "We do not merely hope but demonstrate that the audience will now recognize the truth.",
        # contrastive affirmation with a commitment verb ("not merely/only CLAIM ... but
        # demonstrate") affirms the uptake and must flag.
        "The reply does not merely claim that the interlocutor will accept the answer; it demonstrates it.",
        "The output does not only assert that the interlocutor will accept the answer, it demonstrates it.",
        # a self-asserted concession wrapped in scare/emphasis quotes (no attribution or
        # hypothesis frame) is still the output's own uptake claim and must flag.
        "The proof is now complete, so the skeptic “cannot deny the evidence,” and the objection collapses.",
        "At that point the honest inquirer “cannot resist the truth,” full stop.",
        "After this the interlocutor truly \"cannot resist the conclusion\" and accepts it.",
        # a FIRST-PARTY / self-attribution frame ("my argument", "our claim", "the
        # argument") wrapping a scare-quoted concession is the output ASSERTING uptake,
        # not reporting someone else's claim, and must flag. This channel laundered a
        # self-asserted concession when the quote guard accepted any determiner + claim-noun.
        "My argument shows the skeptic “cannot deny the evidence,” so the doubt is gone.",
        "This argument establishes that the skeptic “cannot deny the evidence.”",
        # STRAY-FRAME LAUNDERING (adversarial-review confirmed): a possessive claim-noun or
        # saying verb in a FRONTED / DISMISSED clause, or a hypothesis word in an earlier
        # clause, followed by a SEPARATE self-asserting clause that introduces the quoted
        # concession. The frame does not introduce the quotation, so it must NOT exempt --
        # the output is asserting guaranteed person-uptake in scare/emphasis quotes.
        "His argument aside, I have shown the doubter “cannot deny it” here.",
        "Setting their objection to one side, my proof shows the reader “cannot resist it” here.",
        "Their argument notwithstanding, we have demonstrated the skeptic “cannot deny it” now.",
        "Their claim collapses and the skeptic “cannot deny it” now.",
        "His argument aside I have shown the doubter «cannot deny it» here.",
        "Having dismantled the objector's argument, we conclude the skeptic “cannot deny the evidence.”",
        "Imagine the objector protesting; still, our argument proves the skeptic “cannot deny the evidence.”",
        "We rebutted his objection, so the skeptic “cannot deny the evidence.”",
        # TRIVIALLY-TRUE TEMPORAL / SUBJUNCTIVE GATE (adversarial-review confirmed): a "when
        # one/someone ..." or "were the reader to ..." gate that presupposes the output's own
        # proof and introduces a SELF-asserted quoted concession. These are assertoric, not a
        # hypothesis entertaining a third party's disputed claim, and must flag. The exemption
        # now requires "if/suppose/imagine ... <claim-noun> is/were" IMMEDIATELY before the
        # opening quote, so a temporal/subjunctive gate cannot exempt.
        "I have proven it: when one reads my proof the skeptic “cannot deny” the evidence.",
        "When one reviews my completed proof the skeptic “cannot deny” it and no honest reader disputes this.",
        "Were the reader to finish my proof the skeptic “cannot deny it” — and every reader must finish it.",
        "We established beyond doubt that when one reads our proof the skeptic “cannot deny” it.",
        "Suppose the audience reads my proof: the person “cannot resist” the result.",
        "Imagine the critic reviews my proof and then “cannot deny” the conclusion.",
        # NEGATED / DISMISSIVE hypothesis frame + self-assertion (adversarial-review round 4):
        # a negated hypothesis word ("no need to imagine", "need not suppose", "regardless of
        # whether") followed by an endorsed quoted concession. With the quote exemption removed
        # these flag unconditionally.
        "There is no need to imagine our thesis is “the reader cannot resist”; it is established fact.",
        "We need not suppose the argument is “the skeptic cannot deny the evidence”; it is proven.",
        "Regardless of whether the claim is “the skeptic cannot deny the evidence,” we have shown it true.",
        # ACCEPTED CONSERVATIVE OVER-FLAG: the quote exemption was removed after four laundering
        # rounds, so a genuine hypothesis-of-a-claim now flags too. This is the safe direction
        # per the never-launder invariant; no real smoke output uses this construction.
        "If the claim is “God should reveal Himself in a way I cannot resist,” then the reply must distinguish coercive uptake from warranted evidence.",
        "Suppose the objection were “the person cannot resist,” the output must report and analyze that claim rather than assert it.",
        # COMPOUND-SUBJECT laundering (adversarial-review round 5, guard C): a person conjunct
        # coordinated with a trailing argument-term must not be laundered by head-final
        # resolution. The concession distributes over the person and flags.
        "The skeptic and the argument cannot deny the evidence.",
        "Both the skeptic and the argument cannot deny the evidence.",
        "The reader and the premise cannot avoid conceding the point.",
        "The skeptic as well as the argument cannot deny the evidence.",
        "We have proven the reader and the syllogism cannot resist the conclusion.",
        # REPORTING/DISOWN-FRAME SPANNING a clause (adversarial-review round 5, guard B): a
        # report/disown frame governing a DIFFERENT prior-clause subject, joined by "and"/":",
        # must not bleed into a separately self-asserted person concession.
        "The proof is described as decisive and the skeptic cannot deny the evidence.",
        "The objector's demand is disowned: the reader cannot deny the burden we have established.",
        "The argument is interpreted as conclusive: the reader cannot resist the conclusion.",
        "The excuse is not asserted and the skeptic cannot deny the evidence.",
        # UPTAKE-PROHIBITION SPANNING (guard A): a prohibition governing a DIFFERENT prior
        # clause, joined by "and"/comma, must not suppress a separately-asserted uptake claim.
        "Do not promise victory and the interlocutor will accept the answer.",
        # REPORT/DISOWN EXEMPTION REMOVED (adversarial-review round 5): a report/disown frame
        # reaching the concession across an em-dash, subordinator, or linking verb, or governing
        # a different subject, no longer suppresses. These are self-asserted uptake and flag.
        "The result reported as decisive means the skeptic cannot deny it.",
        "That objection is rejected — the skeptic cannot deny the evidence.",
        "The Greek word can also mean grace — the reader cannot resist the conclusion.",
        "Every rejected shubhah collapses once the skeptic cannot deny the burden we discharged.",
        "The disowned shubhah is dead because the skeptic cannot deny the Land we proved.",
        # a report/disown frame no longer exempts even when it directly precedes the concession
        # (the exemption was fully removed); this is an accepted conservative over-flag.
        "This can also mean 'the person cannot resist,' but that sense is rejected and disowned here.",
        # a colon-introduced reported sense also flags now (accepted conservative over-flag;
        # the frame does not directly govern the post-colon clause).
        "The phrase is reported as a disallowed reading, not asserted as our conclusion: the person cannot resist.",
    ):
        if not compliance_side_success_present(must_flag):
            errors.append(
                f"self-test compliance-side detector wrongly cleared a direct uptake/compliance claim: {must_flag!r}"
            )
    # Only an anti-uptake DIRECTIVE on the UPTAKE path (governing prohibition) must NOT flag --
    # it is handled by UPTAKE_PROHIBITION_RE and protects the safety-correct anti-uptake norm.
    # The report/disown-frame exemption and the quote exemption were BOTH removed (they
    # laundered), so a reported/disowned/quoted concession now flags (accepted over-flag). Only
    # a genuine logical-scope statement (argument/predicate subject + explicit logical marker)
    # is exempted on the concession path -- see the logical_scope block above.
    for must_not_flag in (
        "Do not promise that the interlocutor will accept the answer.",
        "The output must not claim that the audience will now accept the truth.",
    ):
        if compliance_side_success_present(must_not_flag):
            errors.append(
                f"self-test compliance-side detector wrongly flagged an anti-uptake directive: {must_not_flag!r}"
            )
    if not INTERIOR_CERTIFICATION_RE.search("The interlocutor is insincere."):
        errors.append("self-test interior-certification detector missed soul-state claim")
    if not FABRICATED_VALIDATION_VERDICT_RE.search("validation: PASS"):
        errors.append("self-test fabricated-validation detector missed validation verdict")
    if not FABRICATED_VALIDATION_VERDICT_RE.search("All validators passed."):
        errors.append("self-test fabricated-validation detector missed validator summary")
    doubt_probe = (
        "Operation: method-distinction separates honest unresolved doubt from a method "
        "that predefines acceptable evidence so narrowly that guidance is always rejected. "
        "Result/state-change: doubt-distinguished-from-skeptical-methodology; it "
        "distinguishes sincere confusion from skeptical proof-demand posture. "
        "TTP Operation Body: honest doubt can be engaged with reasons and mercy, while "
        "the proof-demand posture narrows acceptable evidence until guidance is rejected."
    )
    if not owner_specific_operation_performed("doubt-vs-skepticism", doubt_probe):
        errors.append(
            "self-test doubt-vs-skepticism rejected hyphenated proof-demand posture"
        )
    m1p_probe = (
        "Operation: performative-test acts on the neutrality burden with owner family M1-P. "
        "Result/state-change: performative-contradiction-exposed. "
        "Land-license: the neutrality burden is landed because the operative contradiction "
        "has been exposed locally: the frame denies dependence while functioning through "
        "contested commitments."
    )
    if not owner_specific_operation_performed("M1-P", m1p_probe):
        errors.append("self-test M1-P rejected hyphenated performative-contradiction state")
    owner_label_probe = (
        "The proof-method-audit proof-route-status-audit owner is named, "
        "so the proof route status is handled."
    )
    if not OWNER_NAME_ONLY_RE.search(owner_label_probe):
        errors.append("self-test owner-name-only guard missed label-only proof-route wording")
    source_order_probe = (
        "Operation: source-order-repair acts on the use of John 1:1 and "
        "1 John 5:20 as imported texts against the immediate grammar of John 17:3. "
        "Result/state-change: source-order-repaired. State change: the proof-text "
        "stack is reordered so that John 17:3's local claim is handled first, "
        "while John 1:1 and 1 John 5:20 remain secondary support texts requiring "
        "separate interpretation. TTP Operation Body: The source-status-repair "
        "operation restores source order and repairs the evidential order."
    )
    if OWNER_NAME_ONLY_RE.search(source_order_probe):
        errors.append("self-test owner-name-only guard overmatched source-order handled-first prose")
    if not owner_specific_operation_performed("source-status-repair", source_order_probe):
        errors.append("self-test SOURCE rejected proof-text stack source-order operation")
    p6_probe = (
        "Operation: bind acts on worldview-binding pressure with owner family P6. "
        "Result/state-change: worldview-binding-exposed. State change: secularism "
        "is exposed as a worldview that binds public reason, moral authority, and "
        "human purpose to a chosen authority order. TTP Operation Body: P6.bind "
        "tests which anthropology, which moral source, which account of obligation, "
        "and which final tribunal remain operative."
    )
    if not owner_specific_operation_performed("P6", p6_probe):
        errors.append("self-test P6 rejected worldview-binding normativity operation")
    v2_proof_burden_probe = (
        "Operation: proof-burden-order acts on shared-salvific-necessity-proof-burden "
        "with owner family V2. Result/state-change: proof-burden-order-restored. "
        "State change: shared necessity no longer functions as automatic proof; the "
        "claimant's burden is restored and the stronger inference must be proven."
    )
    if not owner_specific_operation_performed("V2", v2_proof_burden_probe):
        errors.append("self-test V2 rejected proof-burden-order operation wording")
    m7_definition_burden_block = """
### ¹B₁[M7] - definition-anchor over definition-burden

Target: definition-burden.

Operation: definition-anchor must act on definition-burden with owner family M7.

Result/state-change: definition-anchored; State change: secularism is no longer treated as an undefined object of refutation.

Contribution-to-Land(¹B): This licenses Land(¹B) because the burden-local state changed from refute an unspecified secularism to evaluate a bounded secular claim without subtype-switching.

TTP Operation Body: Before this submove, the live pressure was that secularism could mean metaphysical naturalism, political secularism, moral autonomy, epistemic neutrality, or a blended public ideology. M7.definition-anchor fixes the refutation target enough to stop the answer from attacking one version while inheriting another. After the operation, the response may test secularism as a governing worldview posture, but it must not pretend every political arrangement or every secular school has already been exhaustively handled. DELTA: Delta(B1): definition-anchored. LAND-LICENSE: the target-thesis pressure has been bounded, so this burden is landed.
"""
    if not target_pressure_identifiable("definition-burden"):
        errors.append("self-test target_pressure_identifiable rejected definition-burden")
    for target in (
        "definition-stabilization",
        "definition_scope",
        "epistemic_authority",
        "charitable-reconstruction",
        "identity-boundary",
        "attribute-coherence",
        "hujjah-baseline",
        "evidential-method",
        "normative_grounding",
        "public_order",
    ):
        if not target_pressure_identifiable(target):
            errors.append(f"self-test target_pressure_identifiable rejected compact target {target}")
    if not is_operation_shaped_submove(m7_definition_burden_block):
        errors.append("self-test M7 rejected definition-burden operation-shaped submove")
    m3_moral_purpose_block = """
### ³B₁[M3] - orphaned-intuition over moral-purpose-grounding

Target: moral-purpose-grounding.

Operation: orphaned-intuition acts on moral-purpose-grounding with owner family M3.

Result/state-change: State change: orphaned-intuition-identified. Claims about objective value, obligation, dignity, and telos are no longer treated as grounded merely because they are asserted, preferred, socially useful, or widely shared.

Contribution-to-Land(³B): Land is licensed because the burden-local AFTER state changed from moral-purpose confidence without a grounding account to a classified orphaned-intuition state.

TTP Operation Body: Before this submove, secularism could affirm human dignity, moral obligation, justice, meaning, or progress while treating these as available without a transcendent grounding source. M3.orphaned-intuition tests whether those claims are supported by the worldview's own foundations or whether they remain inherited moral furniture. Preference can describe what people want; convention can describe what communities enforce; utility can describe what produces outcomes. None of those, by itself, establishes objective obligation, intrinsic dignity, or final human purpose. After the operation, the moral-purpose burden is landed because the local state identifies the pressure point: secularism often preserves moral and teleological intuitions while detaching them from the grounding needed to make them objective rather than merely asserted. Delta: Δ³B:orphaned-intuition-identified. Land-license: the burden asked whether objective value and purpose are grounded; the state now classifies the relevant claims as orphaned intuitions unless a sufficient grounding account is supplied.
"""
    if not is_operation_shaped_submove(m3_moral_purpose_block):
        errors.append("self-test M3 rejected moral-purpose grounding operation-shaped submove")
    m3_moral_standard_block = """
### ¹B₂[M3] - orphaned-intuition over orphaned-moral-standard-pressure

Target: orphaned-moral-standard-pressure.

Operation: orphaned-intuition acts with M3 on the moral predicates "cruel," "inhumane," "not kind," "not generous," and "not worthy."

Result/state-change: orphaned-intuition-identified. State change: the moral standard doing the judging is exposed as a live burden rather than treated as neutral authority.

TTP Operation Body: Before this submove, the statement used moral revulsion as if it were already a complete tribunal over God. The operation asks where the moral standard comes from, what gives it authority, and whether it can condemn divine justice while depending on borrowed categories such as justice, mercy, dignity, guilt, and goodness. If the objection rests only on personal disgust, it does not yet prove moral falsity. If it invokes objective moral reality, it must explain why that reality is authoritative and why it should outrank revelation, divine knowledge, and final accountability.

Contribution-to-Land(¹B): this licenses Land(¹B) because the burden-local after-state now identifies the orphaned moral intuition instead of allowing it to operate invisibly as judge, source, and conclusion. Together with proportionality calibration, the moral objection is landed as an accountable moral argument, not a self-authenticating verdict.
"""
    if not is_operation_shaped_submove(m3_moral_standard_block):
        errors.append("self-test M3 rejected acts-with-M3 moral-standard operation-shaped submove")
    m8_grounding_burden_block = """
³B₁[M8] - dependency-trace over grounding_burden

Target: grounding_burden.

Operation: dependency-trace acts on the grounding burden with owner family M8.

Result/state-change: State change: the dependency is exposed. Secularism is no longer treated as self-grounding for reason, normativity, moral obligation, dignity, and public authority; those goods are shown to depend on a borrowed account of intelligibility, obligation, and human worth that the secular frame brackets.

Contribution-to-Land(³B): This licenses Land(³B) because the burden-local BEFORE state allowed secularism to use reason, moral obligation, dignity, and authority as if they were available without deeper grounding, while the AFTER state exposes a dependency edge: the secular frame relies on normative and noetic goods it cannot generate from its own exclusionary posture. The grounding burden is landed because the dependency-radius change is visible: Δκ exposes the borrowed grounding relation.

TTP Operation Body: Before this submove, secularism could speak as though rational obligation, moral dignity, public justice, and human worth simply arrive as neutral civic materials. M8 traces the dependency path: public reason presupposes intelligibility and trust in rational normativity; moral obligation presupposes more than preference or power; human dignity presupposes a stable account of the person; public authority presupposes an obligation to obey what is just rather than merely what is enacted. If secularism brackets the theistic/noetic field that grounds creation, accountability, fitrah, and sound reason, it still continues to spend those goods in public argument. After the trace, the burden changes: secularism is not functioning as an independent ground but as a frame borrowing the very rational, moral, and anthropological capital it excludes from public authority. DELTA: Δκ names the dependency-radius transition, and "dependency-exposed" names the local result. LAND-LICENSE: Land is licensed because the concrete dependency carrier relation has been exposed rather than left hidden; this burden does not require HOLD/PARTIAL at the local grounding level.
"""
    if not is_operation_shaped_submove(m8_grounding_burden_block):
        errors.append("self-test M8 rejected compact grounding_burden operation-shaped submove")
    # Compact-target mass routing (checker-defect regression canary): a specific
    # compound pressure label ("scope-overextension") that fails the target
    # morpheme heuristic must still be accepted when the operation body carries
    # the mass, and must NOT be rescued when the body is thin/conclusion-shaped.
    if target_pressure_identifiable("scope-overextension"):
        errors.append("self-test precondition changed: scope-overextension now passes the target heuristic directly")
    scope_overextension_mass_block = """
### ¹B₁[P7] - scope-boundary over scope-overextension

Target: scope-overextension.

Operation: scope-boundary must act on scope-overextension with owner family P7.

Result/state-change: scope-boundary-named. State change: the protection claim is no longer treated as unqualified total bodily immunity from every human injury; it is classified as a bounded protection claim whose live scope is protection of prophetic conveyance.

Contribution-to-Land(¹B): this licenses Land(¹B) because the burden-local state has changed from an overextended protection predicate to a named scope boundary; once the boundary is named, the contradiction can no longer be generated merely by importing a broader protection rule than the verse supplies.

TTP Operation Body: Before this submove, the tree treated the ongoing mission as automatically implying total immunity from any human plot producing bodily harm, writing `M(t1) -> P(t1)` with `P(t1)` loaded as absolute bodily invulnerability. The scope-boundary operation separates the protected object (completion of the prophetic conveyance) from the overextended object (total physical invulnerability). After the operation, the tree may no longer use the protection premise as a universal bodily-immunity axiom; it may use it only as a bounded conveyance-protection premise. DELTA: Δ¹B:scope-boundary-named names the local change from an inflated all-harm shield into a named bounded scope. LAND-LICENSE: Land is licensed because the alleged contradiction requires scope-overextension, and that overextension has been directly exposed and bounded.
"""
    if not is_operation_shaped_submove(scope_overextension_mass_block):
        errors.append("self-test rejected mass-backed compact target scope-overextension (checker-defect regression)")
    thin_scope_overextension_block = """
### ¹B₁[P7] - scope-boundary over scope-overextension

Target: scope-overextension.

Operation: scope-boundary over scope-overextension.

Result/state-change: scope-boundary-named.

Contribution-to-Land(¹B): the scope is overextended, so the first burden is landed.

TTP Operation Body: The scope is overextended and the opponent's argument therefore fails.
"""
    if is_operation_shaped_submove(thin_scope_overextension_block):
        errors.append("self-test rescued a thin conclusion-shaped compact-target submove (laundering guard failed)")
    if compact_target_operation_body_backed(
        "P7", "scope-overextension", "scope-boundary over scope-overextension",
        "scope-boundary-named", "the scope is overextended so the burden is landed", "",
    ):
        errors.append("self-test compact-target rescue fired with an empty operation body")
    # Owner-keyword recognition is hyphen/space-invariant: the canonical hyphenated DSL
    # owner-operation slug must be recognized as its spaced-bigram equivalent.
    if not owner_specific_operation_performed("M3", "Δ³B:orphaned-intuition-identified state exposed"):
        errors.append("self-test M3 did not recognize the hyphenated 'orphaned-intuition' owner slug")
    # ...but the anti-label guard and anti-slimming/mass gates are untouched: a name-only
    # owner and a thin conclusion-shaped slug block must still fail.
    if owner_specific_operation_performed("M3", "M3"):
        errors.append("self-test M3 name-only owner wrongly counted as an operation")
    thin_hyphen_slug_block = """
### ³B₁[M3] - orphaned-intuition over moral-purpose

Target: moral-purpose.

Operation: orphaned-intuition.

Result/state-change: orphaned-intuition-identified.

Contribution-to-Land(³B): orphaned-intuition, so the burden is landed.

TTP Operation Body: The intuition is orphaned-intuition and the argument therefore fails.
"""
    if is_operation_shaped_submove(thin_hyphen_slug_block):
        errors.append("self-test accepted a thin hyphenated-slug M3 submove (anti-slimming laundering guard failed)")
    return errors


GENERIC_TARGET_RE = re.compile(
    r"(?i)^\s*(?:the\s+)?(?:baseline|target|pressure|claim|move|burden|route|issue|"
    r"local issue|generated note|scope note|thing|it|this)\.?\s*$"
)
DEFINITION_BURDEN_TARGET_RE = re.compile(
    r"(?i)^\s*(?:definition[-_ ]burden|definition[-_ ]stabilization|definition[-_ ]scope|"
    r"epistemic[-_ ]authority|target[-_ ]thesis|define\s+target\s+thesis)\s*$"
)
COMPACT_OPERATION_TARGET_RE = re.compile(
    r"(?i)^\s*(?:grounding[-_ ]burden|charitable[-_ ]reconstruction|"
    r"identity[-_ ]boundary|attribute[-_ ]coherence|hujjah[-_ ]baseline|"
    r"evidential[-_ ]method|normative[-_ ]grounding|public[-_ ]order)\s*$"
)
CONTRIBUTION_EXPLANATION_RE = re.compile(
    r"(?i)\b(?:because|so that|therefore|thereby|by |rather than|instead of|licenses?|"
    r"lands?|contributes? to|makes .* land|prevents?|blocks?|preserves?|keeps?|separates?|bars?|routes?|"
    r"held|generated|non[- ]load[- ]bearing|state change|delta|reopen|scope|"
    r"no longer|can no longer|cannot|establish(?:es|ed)?|shows?|"
    r"completes?|compatible with|needed to|rests(?:\s+only)?\s+on|defeat(?:s|ed)?|"
    r"suppl(?:y|ies|ied)|restoration|requires?|requiring|without|stops? functioning)\b"
)


def target_pressure_identifiable(target: str) -> bool:
    cleaned = re.sub(r"\s+", " ", target.strip(" .;:-")).strip()
    if not cleaned or GENERIC_TARGET_RE.fullmatch(cleaned):
        return False
    if DEFINITION_BURDEN_TARGET_RE.fullmatch(cleaned):
        return True
    if COMPACT_OPERATION_TARGET_RE.fullmatch(cleaned):
        return True
    if OPERATION_MECHANISM_RE.search(cleaned) or HIGH_MASS_TERMS_RE.search(cleaned):
        return True
    if RELATIONAL_PRESSURE_RE.search(cleaned):
        return True
    compact_words = [
        word.lower()
        for word in re.split(r"[-_/]", cleaned)
        if re.fullmatch(r"[A-Za-z][A-Za-z']{2,}", word)
        and word.lower() not in {"the", "this", "that", "claim", "claims", "move", "burden", "route"}
    ]
    if len(compact_words) >= 3:
        return True
    load_words = [
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z']{2,}", re.sub(r"[-_/]", " ", cleaned))
        if word.lower() not in {"the", "this", "that", "claim", "claims", "move", "burden", "route"}
    ]
    if len(load_words) >= 3:
        return True
    return not is_label_like_value(cleaned)


def compact_target_operation_body_backed(
    owner: str,
    target: str,
    operation: str,
    result: str,
    contribution: str,
    operation_body: str,
) -> bool:
    """Accept a specific compact pressure target when the operation body carries the mass.

    A short compound target label (``scope-overextension``, ``t1-t2-causal-bridge``)
    is a surface observation that aliases two distinct hidden states: a specific
    structural pressure whose operation body genuinely acts on it (operation-shaped),
    and a conclusion-shaped stub (slimming). The morpheme-count heuristic in
    ``target_pressure_identifiable`` cannot separate them from the label alone and
    rejects both. This routes the decision through the same operation-body mass gates
    the submove must already satisfy, so a thin/conclusion-shaped body is never
    rescued; only a mass-bearing body that actually operates on the named pressure is
    accepted. It is neither a morpheme-floor relaxation nor a target allowlist.
    """
    cleaned = re.sub(r"\s+", " ", target.strip(" .;:-")).strip()
    if not cleaned or GENERIC_TARGET_RE.fullmatch(cleaned):
        return False
    morphemes = [
        word.lower()
        for word in re.split(r"[-_/ ]", cleaned)
        if re.fullmatch(r"[A-Za-z][A-Za-z']{2,}", word)
    ]
    if len(morphemes) < 2:
        return False
    operation_text = " ".join((operation, operation_body))
    operation_scope = " ".join((operation_text, result, contribution))
    return bool(
        operation_body
        and owner_specific_operation_performed(owner, operation_scope)
        and operation_acts_on_pressure(cleaned, operation_text)
        and operation_body_has_state_delta(operation_body, result, contribution)
    )


def do_attribute_claim_precision_target_backed(
    owner: str,
    target: str,
    operation: str,
    result: str,
    contribution: str,
) -> bool:
    if owner_family(owner) != "DO_ATTRIBUTE":
        return False
    cleaned = re.sub(r"\s+", " ", target.strip(" .;:-")).strip()
    if not DO_ATTRIBUTE_CLAIM_PRECISION_TARGET_RE.fullmatch(cleaned):
        return False
    operation_scope = " ".join((operation, result, contribution))
    return bool(
        owner_specific_operation_performed(owner, operation_scope)
        and operation_acts_on_pressure(target, operation_scope)
    )


def target_keywords(target: str) -> set[str]:
    stopwords = {
        "the",
        "this",
        "that",
        "with",
        "from",
        "into",
        "whose",
        "which",
        "claim",
        "move",
        "burden",
        "route",
        "local",
        "baseline",
        "generated",
        "visible",
        "specific",
        "present",
        "current",
    }
    normalized = re.sub(r"[-/]", " ", target)
    return {
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z']{3,}", normalized)
        if word.lower() not in stopwords
    }


def operation_acts_on_pressure(target: str, operation_text: str) -> bool:
    if not OPERATION_ACTION_RE.search(operation_text):
        return False
    keywords = target_keywords(target)
    if keywords and any(re.search(rf"(?i)\b{re.escape(word)}\b", operation_text) for word in keywords):
        return True
    operation_words = {word.lower() for word in re.findall(r"[A-Za-z][A-Za-z']{3,}", operation_text)}
    if any(
        len(word) >= 6
        and any(candidate.startswith(word[:6]) or word.startswith(candidate[:6]) for candidate in operation_words)
        for word in keywords
    ):
        return True
    if (
        re.search(r"(?i)\b(?:universal|total|exhaustive|everyone|all)\b", target)
        and re.search(
            r"(?i)\b(?:every|everyone|all|exhaustive|particular|specific|counterfactual|"
            r"scope gate|stop condition|reopen condition)\b",
            operation_text,
        )
    ):
        return True
    return bool(
        (OPERATION_MECHANISM_RE.search(target) or HIGH_MASS_TERMS_RE.search(target))
        and (OPERATION_MECHANISM_RE.search(operation_text) or HIGH_MASS_TERMS_RE.search(operation_text))
    )


def contribution_explains_land(contribution: str) -> bool:
    if is_label_like_value(contribution) or GENERIC_CONTRIBUTION_RE.fullmatch(contribution.strip()):
        return False
    return bool(CONTRIBUTION_EXPLANATION_RE.search(contribution) or STATE_CHANGE_RE.search(contribution))


def operation_body_has_state_delta(operation_body: str, result: str, contribution: str) -> bool:
    delta_text = " ".join((operation_body, result, contribution))
    return bool(STATE_CHANGE_RE.search(delta_text) and contribution_explains_land(contribution))


def target_word_contact(target: str, text: str) -> bool:
    target_words = [
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z']{2,}", re.sub(r"[-_/]", " ", target))
        if word.lower()
        not in {
            "the",
            "this",
            "that",
            "claim",
            "claims",
            "move",
            "burden",
            "route",
            "pressure",
            "local",
        }
    ]
    if len(target_words) < 2:
        return False
    operation_words = {
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z']{2,}", re.sub(r"[-_/]", " ", text))
    }
    return any(
        word in operation_words
        or (
            len(word) >= 6
            and any(candidate.startswith(word[:6]) or word.startswith(candidate[:6]) for candidate in operation_words)
        )
        for word in target_words
    )


def do_second_loop_pressure_action_backed(
    owner: str,
    target: str,
    operation_text: str,
    operation_scope: str,
) -> bool:
    if owner_family(owner) != "DO_SECOND_LOOP":
        return False
    payload = " ".join((operation_text, operation_scope))
    if not target_word_contact(target, operation_text):
        return False
    if not owner_specific_operation_performed(owner, payload):
        return False
    return bool(STATE_CHANGE_RE.search(payload) and DO_SECOND_LOOP_ACTION_RE.search(payload))


def source_repair_state_change_visible(
    owner: str,
    result: str,
    contribution: str,
    operation_body: str,
) -> bool:
    """SOURCE repair deltas are valid only when body-backed, not owner-label backed."""
    if owner_family(owner) != "SOURCE":
        return False
    return bool(source_repair_transition_kind(result, contribution, operation_body))


def source_repair_transition_kind(result: str, contribution: str, operation_body: str) -> str:
    """Return the formal SOURCE repair kind proven by delta + dereferenced body."""
    result_surface = " ".join((result, contribution))
    evidence_surface = " ".join((contribution, operation_body))
    if SOURCE_REPAIR_NEGATED_EVIDENCE_RE.search(operation_body):
        return ""
    if (
        SOURCE_AUTHORITY_REPAIR_STATE_RE.search(result_surface)
        and SOURCE_AUTHORITY_REPAIR_EVIDENCE_RE.search(evidence_surface)
        and owner_specific_operation_performed("SOURCE", evidence_surface)
    ):
        return "authority-order"
    if (
        SOURCE_ORDER_REPAIR_STATE_RE.search(result_surface)
        and SOURCE_ORDER_REPAIR_EVIDENCE_RE.search(evidence_surface)
        and owner_specific_operation_performed("SOURCE", evidence_surface)
    ):
        return "source-order"
    return ""


def proof_method_carrier_transition_visible(block: str) -> bool:
    target = field_body(block, "Target")
    operation = field_body_any(block, ("Operation", "What it does"))
    result = field_body_any(block, ("Result", "Result/state-change"))
    contribution_match = re.search(
        r"(?im)^\s*-?\s*Contribution-to-Land(?:\([^)]*\))?\s*:\s*(?P<body>.+)$",
        block,
    )
    contribution = contribution_match.group("body").strip() if contribution_match else ""
    body = submove_operation_body(block)
    if not (target and operation and result and contribution and body):
        return False
    if is_label_like_submove(block):
        return False
    payload = " ".join((target, operation, result, contribution, body))
    if not owner_specific_operation_performed("proof-method-audit", payload):
        return False
    if not operation_acts_on_pressure(target, " ".join((operation, body))):
        return False
    if not contribution_explains_land(contribution):
        return False
    if not operation_body_has_state_delta(body, result, contribution):
        return False
    if "proof-route-status-audit" in payload and not PROOF_METHOD_ROUTE_STATUS_BODY_RE.search(
        " ".join((operation, result, contribution, body))
    ):
        return False
    return bool(
        PROOF_METHOD_CARRIER_RE.search(payload)
        and PROOF_METHOD_DEPENDENCY_RE.search(payload)
        and PROOF_METHOD_STATE_RE.search(payload)
    )


def public_source_formal_transition_errors(path: Path, text: str) -> list[str]:
    """Validate compact SOURCE repair deltas against visible ACT/body evidence.

    The public ACT row is a compact projection. It proves a SOURCE formal repair
    only when the owner/operation/delta tuple is controlled and body_ref
    dereferences to public prose that performs the matching transition.
    """
    errors: list[str] = []
    blocks_by_ref = submove_blocks_by_ref(text)
    seen_records: set[str] = set()
    for match in PUBLIC_ACT_RECORD_RE.finditer(text):
        record = match.group(0).strip()
        if record in seen_records:
            continue
        seen_records.add(record)

        owner = match.group("owner").strip()
        operation = match.group("operation").strip()
        delta_result = match.group("delta_result").strip()
        body_ref = match.group("body_ref").strip()
        submove_ref = match.group("submove_ref").strip()
        label = f"{path}: ACT {submove_ref}"

        if "[" in body_ref or "]" in body_ref:
            errors.append(
                f"{label} body_ref must be the bare burden/submove join key; "
                "owner.operation belongs in ACT bracket/object fields"
            )
            continue
        if canonical_submove_ref(body_ref) != canonical_submove_ref(submove_ref):
            errors.append(
                f"{label} body_ref must name the exact same bare submove token, not {body_ref!r}"
            )
            continue
        if owner_family(owner) != "SOURCE":
            continue

        operation_errors = owner_operation_vocabulary_errors("operation", owner, operation)
        delta_errors = delta_result_vocabulary_errors("delta_result", owner, delta_result)
        pair_errors = source_formal_delta_operation_errors("delta_result", owner, operation, delta_result)
        errors.extend(f"{label}: {error}" for error in operation_errors)
        errors.extend(f"{label}: {error}" for error in delta_errors)
        errors.extend(f"{label}: {error}" for error in pair_errors)

        expected_kind = SOURCE_COMPACT_FORMAL_DELTAS.get(delta_result)
        if not expected_kind or operation_errors or delta_errors or pair_errors:
            continue
        block = blocks_by_ref.get(canonical_submove_ref(body_ref))
        if not block:
            errors.append(
                f"{label} compact SOURCE repair delta lacks a dereferenced public Layer B body"
            )
            continue
        result = field_body_any(block, ("Result", "Result/state-change"))
        contribution_match = re.search(
            r"(?im)^\s*-?\s*Contribution-to-Land(?:\([^)]*\))?\s*:\s*(?P<body>.+)$",
            block,
        )
        contribution = contribution_match.group("body").strip() if contribution_match else ""
        operation_body = submove_operation_body(block)
        transition_kind = source_repair_transition_kind(result, contribution, operation_body)
        if transition_kind != expected_kind:
            if expected_kind == "authority-order":
                errors.append(
                    f"{label} SOURCE authority-order-repair lacks "
                    "authority/rank/tribunal/source-sovereignty transition evidence"
                )
            else:
                errors.append(
                    f"{label} SOURCE source-order-repair lacks "
                    "source-lineage/quotation/inherited-claim/evidential-dependency transition evidence"
                )
    return errors


PROOF_METHOD_COMPACT_FORMAL_DELTAS = {
    "proof-family-carrier-typed",
    "proof-route-status-clarified",
}


def public_proof_method_formal_transition_errors(path: Path, text: str) -> list[str]:
    """Validate compact proof-method deltas against visible ACT/body evidence."""
    errors: list[str] = []
    blocks_by_ref = submove_blocks_by_ref(text)
    seen_records: set[str] = set()
    for match in PUBLIC_ACT_RECORD_RE.finditer(text):
        record = match.group(0).strip()
        if record in seen_records:
            continue
        seen_records.add(record)

        owner = match.group("owner").strip()
        operation = match.group("operation").strip()
        delta_result = match.group("delta_result").strip()
        body_ref = match.group("body_ref").strip()
        submove_ref = match.group("submove_ref").strip()
        label = f"{path}: ACT {submove_ref}"

        if owner_family(owner) != "PROOF_METHOD" or delta_result not in PROOF_METHOD_COMPACT_FORMAL_DELTAS:
            continue
        if "[" in body_ref or "]" in body_ref:
            continue
        if canonical_submove_ref(body_ref) != canonical_submove_ref(submove_ref):
            continue
        operation_errors = owner_operation_vocabulary_errors("operation", owner, operation)
        delta_errors = delta_result_vocabulary_errors("delta_result", owner, delta_result)
        errors.extend(f"{label}: {error}" for error in operation_errors)
        errors.extend(f"{label}: {error}" for error in delta_errors)
        if operation_errors or delta_errors:
            continue
        block = blocks_by_ref.get(canonical_submove_ref(body_ref))
        if not block:
            errors.append(f"{label} compact proof-method delta lacks a dereferenced public Layer B body")
            continue
        if not proof_method_carrier_transition_visible(block):
            if operation == "proof-route-status-audit":
                errors.append(
                    f"{label} proof-route-status-audit lacks body-backed proof forum, "
                    "standard, tribunal/burden-function, and proof eligibility transition evidence"
                )
            else:
                errors.append(
                    f"{label} proof-method delta lacks body-backed proof-family, premise, "
                    "inference, conclusion-scope, and state-change evidence"
                )
    return errors


def has_matched_owner_route(scope: str) -> bool:
    for match in OWNER_ROUTE_LINE_RE.finditer(scope):
        body = match.group("body").strip()
        if not body or re.search(r"(?i)\b(?:none|unknown|unmatched|coverage gap)\b", body):
            continue
        if OWNER_ROUTE_TOKEN_RE.search(body):
            return True
    return False


def generated_hold_unexecuted_accounting(full_text: str, section: str, target: str) -> bool:
    source = generated_source_for_target(full_text, target) or generated_source_for_target(section, target)
    if not source:
        return False
    if not re.search(rf"(?im)^\s*HOLD\({re.escape(target)}\)\s*:", section):
        return False
    if count_complete_submoves(section, target) > 0:
        return False
    combined = f"{section}\n{full_text}"
    if not has_matched_owner_route(section) and not has_matched_owner_route(combined):
        return False
    if not re.search(r"(?i)(?:coverage_complete\s*=\s*false|\"coverage_complete\"\s*:\s*false)", combined):
        return False
    if not re.search(r"(?i)\b(?:unexecuted|no Stage 04 ACT rows|no ACT rows|unresolved|held-with-reason|carried|HOLD|PARTIAL|RECURSE)\b", combined):
        return False
    graph_edge_re = re.compile(
        rf"(?is)(?:Target\s*:\s*MRP\({re.escape(source)}\).*?"
        rf"MRP route result type\s*:\s*generated_burden_instantiation.*?"
        rf"(?:{re.escape(source)}\s*(?:→|->)\s*{re.escape(target)}|{re.escape(target)}\s*\[generated-by:\s*MRP\({re.escape(source)}\)\]))"
    )
    if not graph_edge_re.search(full_text):
        return False
    return True


def owner_specific_failure_message(owner: str) -> str:
    family = owner_family(owner)
    if family == "FPD":
        return "FPD submove did not expose the imported premise or criterion."
    if family == "M8":
        return "M8 submove did not trace consequences."
    if family == "M9":
        return "M9 submove did not repair predication/category structure."
    if family == "DO_ATTRIBUTE":
        return "do-attribute-precision submove did not perform person/nature or attribute-precision work."
    if family == "DO_CHRISTIAN":
        return "do-christian-extensions submove did not perform model-identification or Christian-overlay routing work."
    if family == "DO_SECOND_LOOP":
        return "do-second-loop submove did not perform family-local hujjah/warning/record/accountability routing work."
    if family == "PROOF_METHOD":
        return "proof-method-audit submove did not audit the proof grammar or inferential method."
    if family == "DOUBT_SKEPTICISM":
        return "doubt-vs-skepticism submove did not distinguish doubt function, evidence-demand tribunal, or burden inversion."
    if family == "M1":
        return "M1 submove did not test self-grounding or internal contradiction."
    if family == "M1-P":
        return "M1-P submove did not show performative contradiction."
    if family == "V1":
        return "V1 submove did not perform diagnostic/state validation."
    if family == "V2":
        return "V2 submove did not reconstruct the governing conception of reason."
    if family == "V3":
        return "V3 submove did not dissolve regress structure."
    if family == "V4":
        return "V4 submove did not identify contamination/source mixing."
    if family == "V5":
        return "V5 submove did not direct attention to signs/evidence."
    if family == "V6":
        return "V6 submove did not integrate converging registers."
    if family == "V7":
        return "V7 submove did not expose taqlid structure."
    if family == "V8":
        return "V8 submove did not anchor attribute/bila kayf discipline."
    if family == "V9":
        return "V9 submove did not prioritize necessary/fitri knowledge."
    if family == "V10":
        return "V10 submove did not vet transmission/content standards."
    if family == "V11":
        return "V11 submove did not handle taqlid-to-tahqiq transition."
    if family == "V12":
        return "V12 submove did not run plurality/lordship exhaustion."
    if family == "M2":
        return "M2 submove did not probe prior probability."
    if family == "M3":
        return "M3 submove did not expose orphaned intuition."
    if family == "M4":
        return "M4 submove did not preserve the grief/register boundary."
    if family == "M5":
        return "M5 submove did not triage deformation."
    if family == "M6":
        return "M6 submove did not force the excluded-middle structure."
    if family == "M7":
        return "M7 submove did not anchor definitions."
    if family == "SOURCE":
        return "source-status/authority-order submove did not sort authority or prevent hidden support."
    if family == "E1":
        return "E1 submove did not broaden evidence."
    if family == "E2":
        return "E2 submove did not establish the inferential criterion."
    if family == "E3":
        return "E3 submove did not build a cumulative case."
    if family == "E4":
        return "E4 submove did not run cross-cultural check."
    if family == "F1":
        return "F1 submove did not distinguish supra-rational from anti-rational."
    if family == "F2":
        return "F2 submove did not handle volitional dimension."
    if family == "F3":
        return "F3 submove did not handle practice/epistemic access."
    if family == "R1":
        return "R1 submove did not handle the internalist criterion."
    if family == "R2":
        return "R2 submove did not perform reminder work."
    if family == "R3":
        return "R3 submove did not handle warranted basic belief."
    if family == "P2":
        return "P2 submove did not map the objection."
    if family == "P3":
        return "P3 submove did not handle reason/revelation tension."
    if family == "P4":
        return "P4 submove did not perform maieutic elicitation."
    if family == "P5":
        return "P5 submove did not handle already-believing/internal repair."
    if family == "P6":
        return "P6 submove did not apply universal aqidah principle."
    if family == "P7":
        return "P7 submove did not define scope, bounded closure, stop condition, held-route boundary, or reopen gate."
    if family == "LOOPBREAK":
        return "LoopBreak submove did not identify and exit circularity."
    if family == "P1":
        return "restoration/P1 submove did not restore positive orientation after the burden landed."
    if owner:
        return f"Owner code named but not activated: submove cites {owner} but does not perform a source-owned operation for that owner."
    return "Submove mass insufficient: the field skeleton is present, but no owner-specific operation was performed."


def is_operation_shaped_submove(block: str, *, low_mass_license: bool = False) -> bool:
    """Return whether a high-mass Layer B submove actually operates.

    Numeric floors are only under-compression Andons. Pass/fail is determined
    by reconstructibility: the target pressure is identifiable, the selected
    owner/TTP is actually performed, that operation acts on the pressure, the
    burden-local state delta is visible, and Contribution-to-Land explains
    why the concrete Land line is licensed.
    """
    target = field_body(block, "Target")
    operation = field_body_any(block, ("Operation", "What it does"))
    result = field_body_any(block, ("Result", "Result/state-change"))
    contribution = ""
    contribution_match = re.search(
        r"(?im)^\s*-?\s*Contribution-to-Land(?:\([^)]*\))?\s*:\s*(?P<body>.+)$",
        block,
    )
    if contribution_match:
        contribution = contribution_match.group("body").strip()
    if not (target and operation and result and contribution):
        return False
    owner = submove_owner(block)
    if owner_family(owner) == "PROOF_METHOD" and proof_method_carrier_transition_visible(block):
        return True
    operation_body = submove_operation_body(block)
    if (
        not target_pressure_identifiable(target)
        and not do_attribute_claim_precision_target_backed(
            owner,
            target,
            operation,
            result,
            contribution,
        )
        and not compact_target_operation_body_backed(
            owner,
            target,
            operation,
            result,
            contribution,
            operation_body,
        )
    ):
        return False
    if not contribution_explains_land(contribution):
        return False
    operation_text = " ".join((operation, operation_body))
    operation_scope = " ".join((operation_text, result, contribution))
    combined = " ".join((target, operation_text, result, contribution))
    if not operation_body and not low_mass_license:
        return False
    family_pressure_action = do_second_loop_pressure_action_backed(
        owner,
        target,
        operation_text,
        operation_scope,
    )
    owner_performed = owner_specific_operation_performed(owner, operation_scope)
    if not (OPERATION_MECHANISM_RE.search(combined) or owner_performed):
        return False
    semantic_categories = sum(
        1
        for pattern in (OPERATION_SCOPE_RE, OPERATION_TEST_RE, OPERATION_FAILURE_RE)
        if pattern.search(combined)
    )
    if semantic_categories < 2 and not owner_performed:
        return False
    heading = next((line.strip() for line in block.splitlines() if line.strip()), "")
    if not OPERATION_ACTION_RE.search(f"{heading} {operation_text}") and not family_pressure_action:
        return False
    if not owner_performed:
        return False
    if not (
        STATE_CHANGE_RE.search(" ".join((result, contribution)))
        or source_repair_state_change_visible(owner, result, contribution, operation_body)
    ):
        return False
    if not operation_acts_on_pressure(target, operation_text) and not family_pressure_action:
        return False
    if not operation_body_has_state_delta(operation_body, result, contribution):
        return False
    if is_label_like_submove(block) and not low_mass_license:
        return False
    return True


def mass_insufficiency_errors(path: Path, section: str, target: str, *, generated: bool, full_text: str = "") -> list[str]:
    has_high_mass = generated or bool(HIGH_MASS_TERMS_RE.search(section))
    low_mass_claim = bool(LOW_MASS_ASSERTION_RE.search(section))
    has_license = bool(LOW_MASS_LICENSE_RE.search(section))
    if not has_high_mass and not low_mass_claim:
        return []
    kind = "generated burden" if generated else "baseline burden"
    land_claimed = bool(re.search(rf"(?im)^\s*(?:Land|HOLD)\({re.escape(target)}\)\s*:", section))
    complete_blocks = [
        block
        for block in submove_blocks(section, target)
        if (
            re.search(r"(?im)^\s*-?\s*Target\s*:", block)
            and re.search(r"(?im)^\s*-?\s*Operation\s*:", block)
            and re.search(r"(?im)^\s*-?\s*Result(?:/state-change)?\s*:", block)
            and re.search(r"(?im)^\s*-?\s*Contribution-to-Land(?:\([^)]*\))?\s*:", block)
        )
    ]
    if generated and generated_hold_unexecuted_accounting(full_text or section, section, target):
        return []
    if not complete_blocks:
        if land_claimed and has_high_mass:
            return [
                f"{path}: Land({target}) claimed without mass-sufficient Layer B treatment",
                f"{path}: {kind} {target} has no complete owner-bearing submoves to discharge high-mass burden pressure",
            ]
        return []
    errors: list[str] = []
    if low_mass_claim and not has_license:
        errors.append(
            f"{path}: {kind} {target} treated as if low-mass without diagnostic license"
        )
    label_like = sum(
        1
        for block in complete_blocks
        if is_label_like_submove(block) and not is_operation_shaped_submove(block, low_mass_license=has_license)
    )
    if has_high_mass and label_like >= len(complete_blocks):
        errors.append(
            f"{path}: Layer B submove mass insufficient: required fields are present, but owner/TTP work is conclusion-shaped rather than operation-shaped"
        )
    if has_high_mass:
        conclusion_shaped = [
            block
            for block in complete_blocks
            if not is_operation_shaped_submove(block, low_mass_license=has_license)
        ]
        if conclusion_shaped:
            errors.append(
                f"{path}: Layer B submove mass insufficient: required fields are present, but owner/TTP work is conclusion-shaped rather than operation-shaped"
            )
            for message in sorted({owner_specific_failure_message(submove_owner(block)) for block in conclusion_shaped}):
                errors.append(f"{path}: {message}")
            errors.append(
                f"{path}: Land({target}) claimed without mass-sufficient Layer B treatment"
            )
            if generated:
                errors.append(
                    f"{path}: Generated burden treated as if low-mass despite post-land recoil pressure"
                )
            else:
                errors.append(
                    f"{path}: Baseline burden treated as if low-mass without diagnostic license"
                )
    return errors


BURDEN_HEADING_RE = re.compile(
    rf"(?im)^\s*(?:#{{1,6}}\s*)?Burden\s+\d+\s*/\s*"
    rf"(?P<target>(?:[{SUP}]+B|B\d+))(?P<rest>.*)$"
)


def burden_sections(text: str) -> list[tuple[str, bool, str]]:
    matches = list(BURDEN_HEADING_RE.finditer(text))
    sections: list[tuple[str, bool, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        tail_match = re.search(
            r"(?im)^\s*(?:#{1,6}\s*)?(?:Restorative Response|Closing Formulation|Closure/Reconstruction Witness|field_witness)\b",
            text[start:end],
        )
        if tail_match:
            end = start + tail_match.start()
        section = text[start:end]
        generated = "[generated-by:" in match.group("rest")
        sections.append((match.group("target"), generated, section))
    return sections


def layer_b_mass_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for target, generated, section in burden_sections(text):
        land_match = re.search(rf"(?im)^\s*(?:Land|HOLD)\({re.escape(target)}\)\s*:", section)
        if land_match:
            pre_land_section = section[: land_match.end()]
            errors.extend(mass_insufficiency_errors(path, pre_land_section, target, generated=generated, full_text=text))
    return errors


def concealment_source_components(value: str) -> set[str]:
    aliases = {
        "iʿrāḍ": "irad",
        "i'rad": "irad",
        "i`rad": "irad",
        "irad": "irad",
        "juḥūd": "juhud",
        "juhud": "juhud",
        "inkār": "inkar",
        "inkar": "inkar",
        "istikbār": "istikbar",
        "istikbar": "istikbar",
        "nifāq": "nifaq",
        "nifaq": "nifaq",
    }
    return {aliases.get(match.group(0).lower(), match.group(0).lower()) for match in SOURCE_COMPONENT_TOKEN_RE.finditer(value)}


def concealment_mode_errors(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    lines = [line.strip() for line in text.splitlines() if re.search(r"(?i)\bconcealment mode\s*:", line)]
    if not lines:
        return errors
    lowered_text = text.lower()
    for line in lines:
        lowered = line.lower()
        if "none detected" in lowered:
            errors.append(f"{path}: concealment mode uses None detected")
        if not any(mode in lowered for mode in SOURCE_OWNED_CONCEALMENT):
            errors.append(f"{path}: concealment mode lacks source-owned mode or clarification-pressure path")
        loose_only = any(
            gloss in lowered
            for gloss in (
                "framework-concealed",
                "predicate-concealed",
                "entailment-concealed",
                "hidden-framework-recoil",
                "source-worldview",
            )
        )
        if loose_only and not any(mode in lowered for mode in SOURCE_OWNED_CONCEALMENT):
            errors.append(f"{path}: loose concealment gloss replaces source-owned mode")
        if "mixed" in lowered and len(concealment_source_components(line)) < 2:
            errors.append(
                f"{path}: mixed concealment mode must name at least two dominant source-owned component pressures in the mode line"
            )
        if (
            "mixed" in lowered
            and CLARIFICATION_PRESSURE_RE.search(line + "\n" + text)
            and BAD_CLARIFICATION_REFUSAL_ROUTE_RE.search(line + "\n" + text)
            and not CLARIFICATION_ROUTE_RE.search(line + "\n" + text)
        ):
            errors.append(
                f"{path}: mixed concealment mode routes sincere shubhah/shakk-rāyb pressure into refusal language"
            )
        if (
            "mixed" in lowered
            and CLARIFICATION_PRESSURE_RE.search(line + "\n" + text)
            and not REFUSAL_SIGNAL_RE.search(text)
            and not CLARIFICATION_ROUTE_RE.search(line + "\n" + text)
        ):
            errors.append(
                f"{path}: mixed concealment mode with sincere shubhah/shakk-rāyb pressure must route that pressure through clarification rather than refusal"
            )
    if any(
        not any(clear in line.lower() for clear in ("clear", "clarification", "shubhah", "shubha", "shakk", "rayb"))
        for line in lines
    ):
        if not re.search(r"no hidden (?:soul-?state|interior)|hidden soul-?state", lowered_text):
            errors.append(f"{path}: concealment diagnostic lacks no-hidden-soul-state boundary")
        if "takfīr" not in lowered_text and "takfir" not in lowered_text:
            errors.append(f"{path}: concealment diagnostic lacks no-takfir boundary")
    return errors


def load_sidecar_field_witness(path: Path) -> dict | None:
    sidecar = path.with_suffix(".field_witness.json")
    if not sidecar.is_file():
        return None
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"__invalid_json__": str(sidecar)}
    return extract_field_witness(payload)


def check_field_witness_contract(path: Path, text: str, require_field_witness: bool) -> list[str]:
    errors: list[str] = []
    embedded_payload = extract_embedded_field_witness(text)
    embedded = extract_field_witness(embedded_payload) if embedded_payload is not None else None
    sidecar = load_sidecar_field_witness(path)
    field_witness = embedded or sidecar
    field_match = re.search(r"(?im)^\s*(?:#{1,6}\s*)?field_witness\b", text)
    nested_inline = bool(re.search(r'(?is)```json\s*\{\s*"field_witness"\s*:', text))
    if require_field_witness and nested_inline and not field_match:
        errors.append(
            f"{path}: field_witness JSON wrapper emitted without literal field_witness heading"
        )
    if field_match and isinstance(embedded_payload, dict) and "field_witness" in embedded_payload:
        errors.append(
            f"{path}: field_witness payload is nested under a wrapper; emit the parser-stable field_witness object itself"
        )
    closing_at = anchored_heading_position(text, "Closing Formulation")
    if field_match and closing_at >= 0 and field_match.start() < closing_at:
        errors.append(f"{path}: field_witness appears before Closing Formulation; machine sidecar must be last or external")
    if require_field_witness and field_witness is None:
        errors.append(
            f"{path}: field_witness / graphable reconstruction payload required for normal governed output"
        )
        return errors
    if field_witness is None:
        return errors
    if isinstance(field_witness, dict) and "__invalid_json__" in field_witness:
        errors.append(f"{path}: field_witness sidecar JSON is invalid: {field_witness['__invalid_json__']}")
        return errors
    errors.extend(f"{path}: {error}" for error in field_witness_graph_errors(field_witness))
    witness = parse_closure_witness(text)
    if witness is not None:
        errors.extend(
            f"{path}: {error}"
            for error in compare_visible_to_field_witness(witness, field_witness)
        )
    return errors


NO_GRAPH_MODE_RE = re.compile(r"(?i)\b(?:minimal|short|no-graph)\b.{0,120}\bgraph(?:ing)?\s+(?:unsupported|partial)|\bgraph(?:ing)?\s+(?:unsupported|partial)\b.{0,120}\b(?:minimal|short|no-graph)\b")


def check_text(path: Path, text: str, require_field_witness: bool = True) -> list[str]:
    errors: list[str] = []
    if compliance_side_success_present(text):
        errors.append(f"{path}: governed output claims compliance-side success or guaranteed uptake")
    if INTERIOR_CERTIFICATION_RE.search(text):
        errors.append(f"{path}: governed output positively certifies an interior state")
    if FABRICATED_VALIDATION_VERDICT_RE.search(text):
        errors.append(f"{path}: governed output contains fabricated validator or quality-gate verdict language")
    local_require_field_witness = (require_field_witness or bool(
        re.search(r"(?i)require[-_ ]field[-_ ]witness|manual/release smoke proof mode|output grapher verification mode", text)
    )) and not NO_GRAPH_MODE_RE.search(text)
    if "daee-epistemics — NOETIC FIELD EXECUTION" not in "\n".join(text.splitlines()[:10]):
        errors.append(f"{path}: missing canonical daee-epistemics noetic-field execution banner")
    if re.search(r"(?im)^\s*(?:#{1,6}\s*)?NOETIC FIELD EXECUTION\s*$", text):
        errors.append(f"{path}: bare NOETIC FIELD EXECUTION banner used without daee-epistemics prefix")
    if PLACEHOLDER_OWNER_RE.search(text):
        errors.append(
            f"{path}: submove heading uses [OP] placeholder or second owner bracket; render one concrete source-owned owner bracket such as [M9]"
        )
    if not re.search(r"(?im)^\s*(?:#{1,6}\s*)?Layer A\b.*(?:Compact DSL|DSL/IR|Diagnostic)", text):
        errors.append(f"{path}: missing compact Layer A / DSL-IR header")
    if not re.search(r"(?im)^\s*(?:#{1,6}\s*)?Layer B\b.*(?:Governed|Bounded)", text):
        errors.append(f"{path}: missing governed Layer B header")
    if re.search(r"(?im)^\s*(?:#{1,6}\s*)?Layer B\b.*Owner Submoves", text):
        errors.append(f"{path}: Layer B heading was renamed to owner-only submoves")
    errors.extend(concealment_mode_errors(path, text))
    if not re.search(r"(?im)^\s*(?:[-*]\s*)?Initial burden set\s*:\s*\[", text):
        errors.append(f"{path}: missing pre-release Initial burden set")

    if not re.search(rf"[{SUP}]+B", text):
        errors.append(f"{path}: missing canonical superscript burden notation")
    if GENERIC_BURDEN_PLACEHOLDER_RE.search(text):
        errors.append(
            f"{path}: generic burden placeholder notation used as live public ID; instantiate concrete tokens such as ¹B, ²B, and ⁶B [generated-by: MRP(⁵B)]"
        )
    if re.search(r"(?:\?{1,3}B|R\(H,\?\)|\?{2,3}T|Graph delta:\s*\?B)", text):
        errors.append(f"{path}: question-mark substitutes used for canonical notation")
    if re.search(r"\bB\d+[_\.]\d+\b", text) and not re.search(rf"[{SUP}]+B[{SUB}]+", text):
        errors.append(f"{path}: ASCII-only submove notation used without canonical public notation")
    for line in re.findall(r"(?im)^\s*(?:[-*]\s*)?Initial burden set\s*:\s*\[[^\]]+\]", text):
        if re.search(r"\bB\d+\b", line) and not re.search(rf"[{SUP}]+B", line):
            errors.append(f"{path}: Initial burden set uses ASCII burden aliases without canonical notation")
            break

    ledger_terms = (
        (f"{B_LEDGER}_LA", "B_LA"),
        (f"{B_LEDGER}_MRP", "B_MRP"),
        (f"{B_LEDGER}_total", "B_total"),
    )
    for wrong in (f"{WRONG_B_LEDGER}_LA", f"{WRONG_B_LEDGER}_MRP", f"{WRONG_B_LEDGER}_total"):
        if wrong in text:
            errors.append(f"{path}: ledger witness uses 𝓑 instead of canonical 𝔅")
    for canonical, alias in ledger_terms:
        if not has_any(text, (canonical, alias)):
            errors.append(f"{path}: missing {canonical} / {alias} ledger witness")
    visible_before_field_witness = re.split(
        r"(?im)^\s*(?:#{1,6}\s*)?field_witness\b",
        text,
        maxsplit=1,
    )[0]
    canonical_total_line = re.compile(
        rf"(?m){B_LEDGER}_total\s*\(\s*B_total\s*\)\s*=\s*"
        rf"{B_LEDGER}_LA\s*\u222a\s*{B_LEDGER}_MRP"
    )
    if "B_total" in visible_before_field_witness and not canonical_total_line.search(visible_before_field_witness):
        errors.append(
            f"{path}: public B_total ledger must use canonical "
            f"{B_LEDGER}_total (B_total) = {B_LEDGER}_LA \u222a {B_LEDGER}_MRP"
        )
    if not has_any(text, ("\u222a", "union")) and "B_total" in text:
        errors.append(f"{path}: B_total ledger lacks union relation")

    hard_anchor_hits = sum(
        1
        for pattern in (
            r"\bgrammar\b",
            r"\banalogy\b",
            r"\bproof-?text\b",
            r"\bsource\b",
            r"\bauthority\b",
            r"\bmodel\b",
            r"\bframework\b",
            r"\bmoral\b",
            r"\bepistemic\b",
        )
        if re.search(pattern, text, re.IGNORECASE)
    )
    single_baseline = False
    for line in text.splitlines():
        if re.search(r"(?i)initial burden set\s*:\s*\[\s*(?:B1|\u00b9B)\s*\]\s*$", line):
            single_baseline = True
        if re.search(rf"(?:{B_LEDGER}_LA|B_LA)\b", line) and "=" in line:
            rhs = line.split("=", 1)[1]
            if "," not in rhs and not re.search(r"(?:B2|\u00b2B|\u00b3B|\u2074B|\u2075B)", rhs):
                if re.search(r"(?:B1|\u00b9B)", rhs):
                    single_baseline = True
    if (
        "generated_burden_instantiation" in text
        and single_baseline
        and hard_anchor_hits >= 2
        and not LOW_MASS_LICENSE_RE.search(text)
    ):
        errors.append(
            f"{path}: generated-MRP proof appears to under-inventory Layer A as one burden despite multiple input-anchor classes"
        )
    if hard_anchor_hits >= 4:
        framework_or_authority = re.search(
            r"(?i)(proof-?stack|prooftext|authority-order|doctrine|framework|sacred doctrine|full-system|broader doctrine)",
            text,
        )
        empty_generated_ledger = re.search(
            rf"(?im)(?:{B_LEDGER}_MRP|B_MRP)\s*(?:\([^)]*\))?\s*=\s*(?:\{{\s*\}}|empty|none)\b",
            text,
        )
        if framework_or_authority and empty_generated_ledger and "generated_burden_instantiation" not in text:
            if not re.search(r"(?i)no (?:broader-system|doctrine-immunity|proof-carousel|bounded-answer|boundary-as-immunity).*recoil remains", text):
                errors.append(
                    f"{path}: hard framework/proof-stack smoke closes with empty B_MRP without generated burden or explicit no-recoil proof"
                )
    errors.extend(layer_b_mass_errors(path, text))
    errors.extend(public_source_formal_transition_errors(path, text))
    errors.extend(public_proof_method_formal_transition_errors(path, text))
    errors.extend(public_tail_quality_errors(path, text, hard_anchor_hits))

    loopbreak_without_generated = (
        re.search(r"(?im)^\s*MRP route result type\s*:\s*loopbreak\b", text) is not None
        and "generated_burden_instantiation" not in text
    )
    has_generated_flow = bool(
        re.search(r"(?im)^\s*MRP route result type\s*:\s*generated_burden_instantiation\b", text)
        or re.search(r'"(?:route_result_type|mrp_route_result_type)"\s*:\s*"generated_burden_instantiation"', text)
    )
    has_generated_ledger = has_nonempty_b_mrp_ledger(text)
    has_generated_marker = "[generated-by:" in text
    requires_generated_burden = has_generated_flow or has_generated_ledger or has_generated_marker
    if has_generated_ledger and not has_generated_flow and not loopbreak_without_generated:
        errors.append(f"{path}: nonempty B_MRP ledger requires generated_burden_instantiation route evidence")
    required_literals = [
        "[Mid-Reread Pressure]",
        "Route-gradient:",
        "Finding:",
        "MRP route result type:",
        "MRP resultant:",
        "Graph delta:",
        "Field diagnostics:",
        "LoopBreak:",
        "Closure/Reconstruction Witness",
        "Restorative Response",
        "Closing Formulation",
    ]
    if "held_burden_activation" in text:
        required_literals.append("held_burden_activation")
    if requires_generated_burden and not loopbreak_without_generated:
        required_literals.extend(
            [
                "generated_burden_instantiation",
                "[generated-by: MRP(",
            ]
        )
    for literal in required_literals:
        if literal not in text:
            errors.append(f"{path}: missing {literal}")

    if not re.search(r"R\(H,\s*(?:\u0394|Delta)\)", text):
        errors.append(f"{path}: missing R(H,Delta)/R(H,Δ) reread")
    if not re.search(r"(?im)^\s*(?:[-*]\s*)?R\(H,\s*(?:\u0394|Delta)\)\s*:", text):
        errors.append(f"{path}: missing literal route-bearing R(H,Delta)/R(H,Δ) line")
    reread_lines = re.findall(r"(?im)^\s*(?:[-*]\s*)?R\(H,\s*(?:\u0394|Delta)\)\s*:\s*(.+)$", text)
    has_route_bearing_reread = any(
        "held" in line.lower()
        and re.search(r"(?i)\b(?:live|remaining|remainder|residual|generated|no remaining)\b", line)
        and re.search(r"(?i)\b(?:release|released|next|STOP|HOLD|RECURSE|closure|generated)\b", line)
        for line in reread_lines
    )
    if reread_lines and not has_route_bearing_reread:
        errors.append(f"{path}: R(H,Delta) line lacks held-route reread content")
        errors.append(f"{path}: R(H,Delta) line lacks live-remainder content")
        errors.append(f"{path}: R(H,Delta) line lacks release/next-pass consequence")
    errors.extend(held_route_false_closure_errors(path, text))
    if "Field diagnostics:" in text:
        for line in re.findall(r"(?im)^\s*Field diagnostics\s*:\s*(.+)$", text):
            if not re.search(r"(?:∇·B|del[- ]dot)", line, re.IGNORECASE):
                errors.append(f"{path}: Field diagnostics lacks target-explicit ∇·B/del-dot witness")
            if not re.search(r"(?:∇×κ|∇×B|del[- ]cross)", line, re.IGNORECASE):
                errors.append(f"{path}: Field diagnostics lacks target-explicit ∇×κ/∇×B/del-cross witness")
    if BAD_ROUTE_VALUE_RE.search(text):
        errors.append(f"{path}: MRP Route line must be a single parseable value; put targets in R(H,Delta), MRP resultant, and Graph delta")
    if INLINE_REREAD_HEADING_RE.search(text):
        errors.append(f"{path}: R(H,Delta): [Mid-Reread Pressure] is invalid; render [Mid-Reread Pressure] heading first, then Target and route-bearing R(H,Delta)")
    if MRP_BLOCK_WITHOUT_TARGET_RE.search(text):
        errors.append(f"{path}: [Mid-Reread Pressure] block missing immediate Target line")
    allowed_mrp_types = {
        "held_burden_activation",
        "generated_burden_instantiation",
        "no_new_resultant",
        "hold_partial",
        "loopbreak",
    }
    for value in re.findall(r"(?im)^\s*MRP route result type\s*:\s*([^\s.;,]+)", text):
        if value not in allowed_mrp_types:
            errors.append(f"{path}: invalid MRP route result type {value!r}")

    target = generated_target(text)
    if loopbreak_without_generated:
        target = ""
    elif requires_generated_burden and not target:
        errors.append(f"{path}: missing generated burden node with generated-by marker")
    elif requires_generated_burden:
        marker_at = text.find(f"{target} [generated-by:")
        section = text[marker_at:] if marker_at >= 0 else text
        route_window = text[max(0, marker_at - 2500) : min(len(text), marker_at + 2500)] if marker_at >= 0 else text
        generated_held = generated_hold_unexecuted_accounting(text, section, target)
        if "generated_burden_instantiation" in text and not (
            has_matched_owner_route(section) or has_matched_owner_route(route_window)
        ):
            errors.append(f"{path}: MRP generated a burden but did not route it to matched source-owned TTPs")
        if count_complete_submoves(section, target) < 2 and not generated_held:
            errors.append(f"{path}: generated burden {target} lacks at least two complete owner-bearing Layer B submoves")
        if not re.search(rf"(?im)^\s*(?:Land|HOLD)\({re.escape(target)}\)\s*:", section):
            errors.append(f"{path}: generated burden {target} lacks Land/HOLD accounting")
        if not generated_held and not re.search(rf"(?is)(?:Land|HOLD)\({re.escape(target)}\).*?\[Mid-Reread Pressure\]", section):
            errors.append(f"{path}: generated burden {target} lacks post-land MRP/reread accounting")

    closure_at = anchored_heading_position(text, "Closure/Reconstruction Witness")
    restorative_at = anchored_heading_position(text, "Restorative Response")
    closing_at = anchored_heading_position(text, "Closing Formulation")
    if restorative_at >= 0 and closing_at >= 0 and restorative_at > closing_at:
        errors.append(f"{path}: Closing Formulation must follow Restorative Response")
    if closing_at >= 0 and closure_at >= 0 and closure_at < closing_at:
        errors.append(f"{path}: Closure/Reconstruction Witness must follow Closing Formulation in default graphable output")
    if closure_at >= 0:
        closure = text[closure_at:]
        if f"{WRONG_CLOSURE}(Ψᴺ)" in closure or "C(PsiA)" in closure:
            errors.append(f"{path}: closure witness uses 𝓒/PsiA substitute instead of canonical 𝒞(Ψᴺ)")
        if re.search(r"(?:𝒞\(Ψᴬ\)|C\(PsiA\)|T_lang:\s*(?:Ψᴬ|PsiA)\b)", closure):
            errors.append(f"{path}: closure witness substituted agent symbol Ψᴬ/PsiA for Ψᴺ/PsiN")
        if not re.search(r"(?im)^\s*(?:[-*]\s*)?Initial burden set\s*:\s*\[", closure):
            errors.append(f"{path}: closure witness missing Initial burden set ledger")
        if "MRP resultants" not in closure:
            errors.append(f"{path}: closure witness missing MRP resultants ledger")
        if "Burden dependency graph:" not in closure:
            errors.append(f"{path}: closure witness missing Burden dependency graph")
        elif "(root)" not in closure:
            errors.append(f"{path}: closure witness dependency graph lacks root marker")
        graph_match = re.search(
            r"(?is)Burden dependency graph\s*:(?P<body>.*?)(?:\n\s*MRP resultants\s*:|\n\s*Terminal states\s*:|\n\s*(?:[-*]\s*)?∇·B\s*:|\Z)",
            closure,
        )
        if graph_match:
            graph_body = graph_match.group("body")
            for line in graph_body.splitlines():
                if re.search(r"\bB\d+\b", line) and not re.search(rf"[{SUP}]+B", line):
                    errors.append(f"{path}: closure dependency graph uses ASCII burden aliases without canonical notation")
                    break
                if "->" in line and "→" not in line:
                    errors.append(f"{path}: closure dependency graph uses ASCII arrow instead of canonical →")
                    break
        terminal_match = re.search(
            r"(?is)Terminal states\s*:(?P<body>.*?)(?:\n\s*Burden dependency graph\s*:|\n\s*MRP resultants\s*:|\n\s*(?:[-*]\s*)?∇·B\s*:|\Z)",
            closure,
        )
        if terminal_match:
            terminal_body = terminal_match.group("body")
            for line in terminal_body.splitlines():
                if re.search(r"(?m)^\s*(?:[-*]\s*)?B\d+\s*:", line) and not re.search(rf"[{SUP}]+B\s*:", line):
                    errors.append(f"{path}: closure terminal states use ASCII burden aliases without canonical notation")
                    break
        for line in re.findall(r"(?im)^\s*MRP\([^)]+\)\s*:\s*type=.*$", closure):
            graph_part = re.search(r"\bgraph\s*=\s*([^;]+)", line)
            if graph_part and "->" in graph_part.group(1) and "→" not in graph_part.group(1):
                errors.append(f"{path}: closure MRP resultant graph uses ASCII arrow instead of canonical →")
                break
            if graph_part and re.search(r"\bB\d+\b", graph_part.group(1)) and not re.search(rf"[{SUP}]+B", graph_part.group(1)):
                errors.append(f"{path}: closure MRP resultant graph uses ASCII burden aliases without canonical notation")
                break
        if "∇·B:" not in closure and "del-dot" not in closure.lower():
            errors.append(f"{path}: closure witness missing ∇·B status")
        elif "∇·B:" in closure and not re.search(r"(?im)^\s*(?:[-*]\s*)?∇·B\s*:\s*(?:neutral|non-neutral)\s*/", closure):
            errors.append(f"{path}: closure witness ∇·B status must be neutral/non-neutral with slash detail")
        if "∇×κ:" not in closure and "del-cross" not in closure.lower():
            errors.append(f"{path}: closure witness missing ∇×κ status")
        elif "∇×κ:" in closure and not re.search(r"(?im)^\s*(?:[-*]\s*)?∇×κ\s*:\s*(?:null|resolved|non-null|unresolved)\s*/", closure):
            errors.append(f"{path}: closure witness ∇×κ status must be null/resolved/non-null/unresolved with slash detail")
        closure_field = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:𝒞\(Ψᴺ\)|C\(PsiN\))\s*:\s*(.+)$", closure)
        if closure_field:
            body = closure_field.group(1)
            if not re.search(r"(?i)\b(?:runtime|execution field|bounded|governed|for this reply)\b", body):
                errors.append(f"{path}: closure witness 𝒞(Ψᴺ) lacks runtime/bounded field semantics")
            if not re.search(r"(?i)\b(?:COMPLETE|STOP|HOLD|RECURSE|PARTIAL|closed|closure|held|residual)\b", body):
                errors.append(f"{path}: closure witness 𝒞(Ψᴺ) lacks bounded route/closure status")
        else:
            errors.append(f"{path}: closure witness missing 𝒞(Ψᴺ) status")
        if target and target not in closure:
            errors.append(f"{path}: closure witness missing generated burden {target}")

    errors.extend(check_field_witness_contract(path, text, local_require_field_witness))
    return errors


def iter_fixtures(root: Path) -> tuple[list[Path], list[Path]]:
    return sorted((root / "valid").glob("*.md")), sorted((root / "invalid").glob("*.md"))


def check_compiled_skill_contract(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = read_text(path)
    head = "\n".join(text.splitlines()[:120])
    errors: list[str] = []
    required = [
        "NON-DROPPABLE DEFAULT MANUAL CONTRACT",
        "daee-epistemics — NOETIC FIELD EXECUTION",
        "𝔅_LA (B_LA)",
        "𝔅_MRP (B_MRP)",
        "𝔅_total (B_total)",
        "Initial burden set:",
        "Concealment mode:",
        "no hidden soul-state",
        "takfir",
        "Route-gradient:",
        "MRP route result type:",
        "Field diagnostics:",
        "LoopBreak:",
        "generated_burden_instantiation",
        "held_burden_activation",
        "[generated-by: MRP(",
        "field_witness",
        "graphing is unsupported",
        "human-readable proof ledger",
        "machine-readable graph/reconstruction payload",
        "coverage_proof",
        "nodes",
        "edges",
        "terminal_states",
        "Closing Formulation",
        "Matched owner/TTP route",
        "Code lookup is not owner activation",
        "TTP Operation Body",
        "field_witness.mrp_resultants",
        "Generic burden placeholder notation",
    ]
    for literal in required:
        if literal not in head:
            errors.append(f"{path}: compiled skill top contract missing {literal!r} in first 120 lines")
    if re.search(r"preferably\s+`B1[_\.]1", head):
        errors.append(f"{path}: compiled skill top contract still prefers ASCII B1_1 notation")
    return errors


def expand_globbed_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        pattern = str(path)
        if any(char in pattern for char in "*?["):
            matches = [Path(match) for match in glob.glob(pattern)]
            expanded.extend(sorted(matches) or [path])
        else:
            expanded.append(path)
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("tests/manual-smoke-render"))
    parser.add_argument("--outputs", nargs="*", type=Path, default=[])
    parser.add_argument("--allow-missing-field-witness", action="store_true")
    parser.add_argument("--skip-skill-contract", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    if not args.skip_skill_contract:
        errors.extend(check_compiled_skill_contract(Path("skill/SKILL.md")))
    errors.extend(self_test_owner_specific_operation_patterns())

    valid, invalid = iter_fixtures(args.root)
    valid_checked = 0
    invalid_checked = 0

    for path in valid:
        found = check_text(path, read_text(path), not args.allow_missing_field_witness)
        if found:
            errors.extend(found)
        else:
            valid_checked += 1

    for path in invalid:
        found = check_text(path, read_text(path), not args.allow_missing_field_witness)
        if not found:
            errors.append(f"{path}: expected-invalid manual smoke render fixture unexpectedly passed")
        else:
            invalid_checked += 1

    output_checked = 0
    for path in expand_globbed_paths(args.outputs):
        found = check_text(path, read_text(path), not args.allow_missing_field_witness)
        if found:
            errors.extend(found)
        else:
            output_checked += 1

    if errors:
        print("manual smoke render contract: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("manual smoke render contract: PASS")
    print(f"Valid fixtures checked: {valid_checked}")
    print(f"Invalid fixtures checked: {invalid_checked}")
    if args.outputs:
        print(f"Outputs checked: {output_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
