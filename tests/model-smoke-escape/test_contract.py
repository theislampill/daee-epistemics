#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from check_model_smoke_escape_registry import run_fixture_inventory  # noqa: E402


class ModelSmokeEscapeContractTests(unittest.TestCase):
    def test_inventory(self) -> None:
        inventory = json.loads((Path(__file__).parent / "inventory.json").read_text(encoding="utf-8"))
        problems, counts = run_fixture_inventory(Path(__file__).parent, inventory)
        self.assertEqual([], problems)
        self.assertEqual((5, 12), counts)

    def test_tracked_registry_is_illustrative_and_cannot_self_declare_maturity(self) -> None:
        registry = json.loads((Path(__file__).parent / "registry.json").read_text(encoding="utf-8"))
        self.assertEqual("ILLUSTRATIVE_FIXTURE", registry.get("registry_role"))
        self.assertNotIn("candidate_maturity_status", registry)


if __name__ == "__main__":
    unittest.main()
