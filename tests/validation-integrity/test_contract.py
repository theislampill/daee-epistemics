#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from check_validation_registry import run_fixture_inventory  # noqa: E402


class ValidationIntegrityContractTests(unittest.TestCase):
    def test_inventory(self) -> None:
        inventory = json.loads((Path(__file__).parent / "inventory.json").read_text(encoding="utf-8"))
        problems, counts = run_fixture_inventory(Path(__file__).parent, inventory)
        self.assertEqual([], problems)
        self.assertEqual((2, 13), counts)

    def test_external_expectation_and_verdict(self) -> None:
        fixture_root = Path(__file__).parent / "valid"
        proc = subprocess.run(
            [sys.executable, str(TOOLS / "assert_expected_rejection.py"),
             "--expectation", str((fixture_root / "right-reason-stage04.verdict.expectation.json").relative_to(ROOT)),
             "--verdict", str((fixture_root / "right-reason-stage04.verdict.json").relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
