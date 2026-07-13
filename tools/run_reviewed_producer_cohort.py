#!/usr/bin/env python3
"""Producer CLI boundary; live providers are deliberately fail-closed."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reviewed_campaign_orchestrator import disabled_live_provider_message


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--custody-root", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--provider", choices=("codex-live", "disabled"), default="disabled")
    args = parser.parse_args()
    # No CLI path accepts a fake adapter; fakes are dependency-injected by tests only.
    print(json.dumps(disabled_live_provider_message(), sort_keys=True))
    return 2


if __name__ == "__main__":
    sys.exit(main())
