#!/usr/bin/env python3
"""Validate daee-prompt-pack-manifest-v1 JSONL lines against a token budget.

This is a cheap, stdlib-only budget gate over the additive prompt-pack
manifest lines emitted by tools/run_staged_current_skill_smoke.py. It does
not run a model and does not know anything about stage semantics; it only
checks the manifest shape, internal byte/token arithmetic, and the two
observability flags (includes_full_runtime, includes_prior_full_output)
plus a total-token ceiling.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
SMOKE_HARNESS_PATH = ROOT / "tools" / "run_staged_current_skill_smoke.py"


SCHEMA = "daee-prompt-pack-manifest-v1"
REQUIRED_KEYS = (
    "schema",
    "case_id",
    "stage",
    "call_index",
    "components",
    "total_bytes",
    "total_est_tok",
    "includes_full_runtime",
    "includes_prior_full_output",
)
DEFAULT_CEILING = 20_000


class BudgetViolation(Exception):
    """A single manifest line failed validation."""


def _case_label(record: dict[str, Any]) -> str:
    case_id = record.get("case_id", "<missing case_id>")
    stage = record.get("stage", "<missing stage>")
    call_index = record.get("call_index", "<missing call_index>")
    return f"case_id={case_id!r} stage={stage!r} call_index={call_index!r}"


def validate_record(record: dict[str, Any], ceiling: int) -> None:
    if not isinstance(record, dict):
        raise BudgetViolation("manifest line is not a JSON object")

    if record.get("schema") != SCHEMA:
        raise BudgetViolation(
            f"{_case_label(record)}: schema mismatch (expected {SCHEMA!r}, got {record.get('schema')!r})"
        )

    missing = [key for key in REQUIRED_KEYS if key not in record]
    if missing:
        raise BudgetViolation(f"{_case_label(record)}: missing required key(s): {', '.join(missing)}")

    components = record["components"]
    if not isinstance(components, list) or not components:
        raise BudgetViolation(f"{_case_label(record)}: components must be a non-empty list")

    components_bytes_sum = 0
    for component in components:
        if not isinstance(component, dict) or "name" not in component or "bytes" not in component or "est_tok" not in component:
            raise BudgetViolation(f"{_case_label(record)}: malformed component entry: {component!r}")
        comp_bytes = component["bytes"]
        comp_tok = component["est_tok"]
        if not isinstance(comp_bytes, int) or comp_bytes < 0:
            raise BudgetViolation(f"{_case_label(record)}: component {component.get('name')!r} has invalid bytes {comp_bytes!r}")
        if comp_tok != comp_bytes // 4:
            raise BudgetViolation(
                f"{_case_label(record)}: component {component.get('name')!r} est_tok {comp_tok} != bytes//4 ({comp_bytes // 4})"
            )
        components_bytes_sum += comp_bytes

    total_bytes = record["total_bytes"]
    if not isinstance(total_bytes, int) or total_bytes < 0:
        raise BudgetViolation(f"{_case_label(record)}: total_bytes is not a non-negative int: {total_bytes!r}")
    if components_bytes_sum != total_bytes:
        raise BudgetViolation(
            f"{_case_label(record)}: components sum {components_bytes_sum} != total_bytes {total_bytes}"
        )

    total_est_tok = record["total_est_tok"]
    if total_est_tok != total_bytes // 4:
        raise BudgetViolation(
            f"{_case_label(record)}: total_est_tok {total_est_tok} != total_bytes//4 ({total_bytes // 4})"
        )

    if record["includes_full_runtime"] is not False:
        raise BudgetViolation(f"{_case_label(record)}: includes_full_runtime is not false")

    if record["includes_prior_full_output"] is not False:
        raise BudgetViolation(f"{_case_label(record)}: includes_prior_full_output is not false")

    if total_est_tok > ceiling:
        raise BudgetViolation(
            f"{_case_label(record)}: total_est_tok {total_est_tok} exceeds ceiling {ceiling}"
        )


def check_manifest_file(path: Path, ceiling: int) -> int:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"ERROR: cannot read {path}: {exc}")
        return 1

    checked = 0
    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"prompt pack budget check: FAIL ({path}:{lineno}: invalid JSON: {exc})")
            return 1
        try:
            validate_record(record, ceiling)
        except BudgetViolation as exc:
            print(f"prompt pack budget check: FAIL ({path}:{lineno}: {exc})")
            return 1
        checked += 1

    print(f"prompt pack budget check: PASS ({checked} manifest line(s) checked, ceiling={ceiling})")
    return 0


# --- self-test fixtures (no filesystem dependency) --------------------------


def _fixture_record(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema": SCHEMA,
        "case_id": "self-test-case",
        "stage": "stage-01",
        "call_index": 1,
        "components": [
            {"name": "raw_input_text", "bytes": 40, "est_tok": 10},
            {"name": "previous_stages_json", "bytes": 20, "est_tok": 5},
            {"name": "frame_and_residual", "bytes": 140, "est_tok": 35},
        ],
        "total_bytes": 200,
        "total_est_tok": 50,
        "includes_full_runtime": False,
        "includes_prior_full_output": False,
    }
    base.update(overrides)
    return base


def _run_self_test_case(label: str, record: dict[str, Any], ceiling: int, expect_pass: bool) -> bool:
    try:
        validate_record(record, ceiling)
        passed = True
        reason = ""
    except BudgetViolation as exc:
        passed = False
        reason = str(exc)
    ok = passed == expect_pass
    status = "PASS" if ok else "FAIL"
    detail = "" if not reason else f" ({reason})"
    print(f"[{status}] {label}: expected {'pass' if expect_pass else 'fail'}, got {'pass' if passed else 'fail'}{detail}")
    return ok


# --- FIX 6: static call-site parity (structural instrumentation coverage) --
#
# The manifest checker above only ever sees synthetic fixtures or whatever
# manifest lines a real run happened to produce; it has no way to notice a
# NEW invoke_model() call site in tools/run_staged_current_skill_smoke.py
# that was never wired up to emit_prompt_pack_manifest(). This performs a
# cheap, purely textual structural check on that file's source instead, as a
# floor guarantee that every model-invocation call site has a paired
# manifest-emission call site.
#
# Method (documented per FIX 6's requirement): count line-start-anchored
# occurrences of "invoke_model(" and "emit_prompt_pack_manifest(" via a
# regex that requires the match to begin a logical call expression -- i.e.
# preceded only by leading whitespace, an assignment target, "return ", or
# the start of an expression statement, NEVER preceded by "def " (which
# would match the function's own definition line) and never occurring
# inside a quoted string literal starting at that same position (approximated
# by requiring the token NOT be immediately preceded by a quote character,
# which is sufficient to exclude the common "quoted example" case without a
# full tokenizer; this is a deliberately cheap heuristic, not a parser).
_CALL_SITE_RE_TEMPLATE = r"(?<!def )(?<!['\"])\b{name}\("


def _count_call_sites(source: str, function_name: str) -> int:
    pattern = re.compile(_CALL_SITE_RE_TEMPLATE.format(name=re.escape(function_name)))
    return len(pattern.findall(source))


def check_call_site_parity(smoke_harness_path: Path) -> tuple[bool, str]:
    """Return (ok, message) for the invoke_model / emit_prompt_pack_manifest parity check.

    Every model invocation (invoke_model call site) must have a paired
    manifest emission (emit_prompt_pack_manifest call site): the count of
    emit_prompt_pack_manifest call sites must be >= the count of invoke_model
    call sites. A mismatch means a new (or newly discovered) invoke_model
    call site was added without instrumenting it -- the fix is to add the
    missing emit_prompt_pack_manifest() call at that site, not to loosen this
    check.
    """
    try:
        source = smoke_harness_path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"cannot read {smoke_harness_path}: {exc}"

    invoke_model_count = _count_call_sites(source, "invoke_model")
    emit_manifest_count = _count_call_sites(source, "emit_prompt_pack_manifest")

    if emit_manifest_count < invoke_model_count:
        return False, (
            f"call-site parity FAIL: {invoke_model_count} invoke_model( call site(s) but only "
            f"{emit_manifest_count} emit_prompt_pack_manifest( call site(s)) in {smoke_harness_path}. "
            "Every model invocation must be paired with a manifest emission -- instrument the new "
            "invoke_model( call site with an emit_prompt_pack_manifest(...) call immediately before it."
        )

    return True, (
        f"call-site parity OK: {emit_manifest_count} emit_prompt_pack_manifest( call site(s) >= "
        f"{invoke_model_count} invoke_model( call site(s)) in {smoke_harness_path}"
    )


def run_self_test() -> int:
    results = []

    valid = _fixture_record()
    results.append(_run_self_test_case("valid manifest line passes", valid, DEFAULT_CEILING, expect_pass=True))

    full_runtime = _fixture_record(includes_full_runtime=True)
    results.append(
        _run_self_test_case("includes_full_runtime=true fails", full_runtime, DEFAULT_CEILING, expect_pass=False)
    )

    prior_output = _fixture_record(includes_prior_full_output=True)
    results.append(
        _run_self_test_case(
            "includes_prior_full_output=true fails", prior_output, DEFAULT_CEILING, expect_pass=False
        )
    )

    sum_mismatch = _fixture_record(total_bytes=999)
    results.append(_run_self_test_case("component sum mismatch fails", sum_mismatch, DEFAULT_CEILING, expect_pass=False))

    over_ceiling = _fixture_record(
        components=[
            {"name": "raw_input_text", "bytes": 400_000, "est_tok": 100_000},
            {"name": "frame_and_residual", "bytes": 0, "est_tok": 0},
        ],
        total_bytes=400_000,
        total_est_tok=100_000,
    )
    results.append(_run_self_test_case("over-ceiling total_est_tok fails", over_ceiling, DEFAULT_CEILING, expect_pass=False))

    parity_ok, parity_message = check_call_site_parity(SMOKE_HARNESS_PATH)
    status = "PASS" if parity_ok else "FAIL"
    print(f"[{status}] invoke_model / emit_prompt_pack_manifest call-site parity: {parity_message}")
    results.append(parity_ok)

    if all(results):
        print(f"check_prompt_pack_budget self-test: PASS ({len(results)}/{len(results)} expectations met)")
        return 0
    print(f"check_prompt_pack_budget self-test: FAIL ({sum(results)}/{len(results)} expectations met)")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="Path to a prompt-pack-manifest.jsonl file to validate.")
    parser.add_argument("--ceiling", type=int, default=DEFAULT_CEILING, help="Max allowed total_est_tok per line.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in fixture-based expectations.")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    if args.manifest is None:
        parser.error("--manifest is required unless --self-test is used")

    if not args.manifest.exists():
        print(f"ERROR: manifest not found: {args.manifest}")
        return 1

    return check_manifest_file(args.manifest, args.ceiling)


if __name__ == "__main__":
    raise SystemExit(main())
