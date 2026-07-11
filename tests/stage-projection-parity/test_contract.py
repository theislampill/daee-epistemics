#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

try:
    import stage_projection_contract as contract
    import check_stage_projection_parity as checker
except ImportError as exc:  # expected RED before implementation
    print(f"stage-projection-parity contract RED: missing implementation surface: {exc}")
    raise SystemExit(1)


class StageProjectionParityContractTests(unittest.TestCase):
    def test_lossless_projection_passes(self) -> None:
        path = Path(__file__).parent / "valid" / "lossless-stage06-stage07.json"
        payload = checker.load_fixture_payload(path)
        self.assertEqual(contract.projection_diagnostics(payload), [])

    def test_historical_shorthand_is_labeled_and_non_release(self) -> None:
        path = Path(__file__).parent / "valid" / "historical-stage06-local-shorthand.json"
        result = checker.validate_fixture(path)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["compatibility"], "historical-stage06-local")

    def test_every_invalid_matches_same_stem_expectation(self) -> None:
        errors, counts = checker.run_fixture_suite(Path(__file__).parent)
        self.assertEqual(errors, [], "\n".join(errors))
        self.assertGreaterEqual(counts["invalid"], 8)
        for expectation_path in (Path(__file__).parent / "invalid").glob("*.expectation.json"):
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            self.assertEqual(expectation_path.name, Path(expectation["fixture"]).stem + ".expectation.json")


if __name__ == "__main__":
    unittest.main()
