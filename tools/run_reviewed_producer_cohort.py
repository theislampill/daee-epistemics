#!/usr/bin/env python3
"""Canonical reviewed producer CLI; live execution requires the exact matrix child."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codex_live_producer_adapter import CodexLiveProducerAdapter
from reviewed_campaign_orchestrator import CampaignError, disabled_live_provider_message, run_producer_cohort


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--custody-root", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--provider", choices=("codex-live", "disabled"), default="disabled")
    parser.add_argument("--codex-executable", type=Path)
    parser.add_argument("--command-timeout-seconds", type=int, default=3600)
    args = parser.parse_args()
    # No CLI path accepts a fake adapter; fakes are dependency-injected by tests only.
    if args.provider != "codex-live":
        print(json.dumps(disabled_live_provider_message(), sort_keys=True))
        return 2
    if args.custody_root is None or args.authorization is None or args.codex_executable is None:
        print(json.dumps({"status": "FAIL", "error": "LIVE_PROVIDER_EXACT_CUSTODY_AUTHORIZATION_AND_EXECUTABLE_REQUIRED"}, sort_keys=True))
        return 1
    if args.command_timeout_seconds <= 0:
        print(json.dumps({"status": "FAIL", "error": "LIVE_PROVIDER_POSITIVE_TIMEOUT_REQUIRED"}, sort_keys=True))
        return 1
    try:
        adapter = CodexLiveProducerAdapter(
            custody_root=args.custody_root,
            codex_executable=args.codex_executable,
            command_timeout_seconds=args.command_timeout_seconds,
        )
        completion = run_producer_cohort(args.custody_root, args.authorization, adapter)
    except (CampaignError, OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(completion, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
