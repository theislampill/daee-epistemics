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

from check_model_smoke_escape_registry import (  # noqa: E402
    FIXTURE_ROOT,
    LIVE_REGISTRY,
    run_fixture_inventory,
    validate_for_candidate_maturity,
)


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

    def test_live_registry_owner_is_distinct_from_illustrative_fixtures(self) -> None:
        self.assertNotEqual((FIXTURE_ROOT / "registry.json").resolve(), LIVE_REGISTRY.resolve())
        registry = json.loads(LIVE_REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual("LIVE_EVIDENCE", registry.get("registry_role"))
        live_ids = {row["escape_id"] for row in registry["escapes"]}
        self.assertIn("escape-andon-182-pre-admission-diagnostic-001", live_ids)
        self.assertNotIn("escape-neutral-001", live_ids)
        self.assertEqual([], validate_for_candidate_maturity(registry))

    def test_live_registry_cannot_drop_required_escape_history(self) -> None:
        registry = json.loads(LIVE_REGISTRY.read_text(encoding="utf-8"))
        registry["escapes"] = []
        findings = validate_for_candidate_maturity(registry)
        self.assertTrue(findings)
        self.assertEqual("missing_live_escape_evidence", findings[0].failure_class)


if __name__ == "__main__":
    unittest.main()
