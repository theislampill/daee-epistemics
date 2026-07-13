#!/usr/bin/env python3
"""Cold-review CLI boundary; live providers are deliberately fail-closed."""
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
    parser.parse_args()
    # Fakes are only dependency-injected by the test suite, never selected by CLI.
    print(json.dumps(disabled_live_provider_message(), sort_keys=True))
    return 2


if __name__ == "__main__":
    sys.exit(main())
