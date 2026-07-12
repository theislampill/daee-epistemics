#!/usr/bin/env python3
"""Validate the non-self-referential tracked A16 predecessor binding."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable

from source_provenance import self_test, validate_tracked_only


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tracked-only", action="store_true", help="validate tracked predecessor intent only")
    group.add_argument("--self-test", action="store_true", help="run the permanent mutation matrix")
    parser.add_argument("--explain", action="store_true", help="emit deterministic JSON for tracked-only mode")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        if args.explain:
            build_parser().error("--explain is only valid with --tracked-only")
        problems, valid_count, invalid_count = self_test()
        if problems:
            for problem in problems:
                print(f"FAIL: {problem}")
            print(f"source provenance self-test: FAIL ({len(problems)} problem(s))")
            return 1
        print(
            "source provenance self-test: PASS "
            f"({valid_count} valid predecessor HEAD without receipt, {invalid_count} invalid)"
        )
        return 0

    verdict, findings = validate_tracked_only()
    if findings:
        finding = findings[0]
        if args.explain:
            print(
                json.dumps(
                    {
                        "failure_class": finding.failure_class,
                        "message": finding.message,
                        "status": "TRACKED_SOURCE_BINDING_INVALID",
                        "terminal_claim": False,
                    },
                    sort_keys=True,
                )
            )
        else:
            print(f"source provenance tracked-only: FAIL [{finding.failure_class}]: {finding.message}")
        return 1
    if args.explain:
        print(json.dumps(verdict, sort_keys=True))
    else:
        print(
            "source provenance tracked-only: PASS "
            f"({verdict['binding_id']}; checkpoint {verdict['checkpoint_commit']}; receipt not validated)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
