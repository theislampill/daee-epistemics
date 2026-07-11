from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
FIXTURES = Path(__file__).resolve().parent


def upstream_source(path: Path) -> str:
    name = "empty.json" if path.name == "empty-input.json" else "alpha-beta.json" if path.name == "source-observation-disappears.json" else "unicode.json" if path.name == "utf8-crlf-quote-nesting.json" else "alpha.json"
    return json.loads((FIXTURES / "upstream" / name).read_text(encoding="utf-8"))["source_text"]


class InputPressureCoverageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = TOOLS / "input_observation_units.py"
        cls.validate = None
        if not path.exists():
            return
        spec = importlib.util.spec_from_file_location("input_observation_units", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        cls.validate = staticmethod(module.validate_input_pressure_record)

    def require_validator(self):
        self.assertIsNotNone(self.validate, "input_observation_units implementation missing")
        return self.validate

    def test_neighboring_valid_records_are_accepted(self) -> None:
        for path in sorted((FIXTURES / "valid").glob("*.json")):
            with self.subTest(path=path.name):
                self.assertEqual(self.require_validator()(json.loads(path.read_text(encoding="utf-8")), upstream_source_text=upstream_source(path)), [])

    def test_segmentation_preserves_crlf_unicode_and_nested_quote(self) -> None:
        module = sys.modules["input_observation_units"]
        source = 'alpha\r\n\r\nprefix “βeta” suffix'
        units = module.segment_observation_units(source)
        self.assertEqual([(item["source_start"], item["source_end"]) for item in units if item["parent_unit_id"] is None], [(0, 5), (9, 29)])
        quote = next(item for item in units if item["surface_kind"] == "quote")
        self.assertEqual(source[quote["source_start"]:quote["source_end"]], '“βeta”')
        self.assertEqual(quote["parent_unit_id"], "U2")

    def test_empty_segmentation_is_not_release_validity(self) -> None:
        module = sys.modules["input_observation_units"]
        self.assertEqual(module.segment_observation_units(""), [])
        record = json.loads((FIXTURES / "invalid" / "empty-input.json").read_text(encoding="utf-8"))
        self.assertEqual(self.require_validator()(record, upstream_source_text=upstream_source(FIXTURES / "invalid" / "empty-input.json"))[0]["failure_subcode"], "empty-input")

    def test_arbitrary_finite_wide_source_has_no_topology_limit(self) -> None:
        module = sys.modules["input_observation_units"]
        source = "\r\n\r\n".join(f"neutral unit {index}" for index in range(23))
        observations = module.segment_observation_units(source)
        observation_ids = [item["unit_id"] for item in observations]
        pressures = [{"pressure_id":f"P{index}","observation_unit_ids":[unit_id],"candidate_state_ids":["N1"],"pressure_function":f"bound transition {index}","register_axes":[],"status":"routed","burden_id":f"B{index}","decision_id":None,"basis":"The exact observation remains routed."} for index,unit_id in enumerate(observation_ids,1)]
        record = {"topology_contract":"input-pressure-v1","source_text":source,"offset_unit":"unicode-codepoint","observation_units":observations,"candidate_states":[{"state_id":"N1","observation_unit_ids":observation_ids,"frame":"neutral-frame","live_registers":[],"status":"selected","basis":"The bounded source licenses one operative frame.","merged_into":None}],"selection_status":"licensed","selected_n_frame":"neutral-frame","input_pressures":pressures,"burden_floor":[f"B{index}" for index in range(1,len(observations)+1)],"burden_origins":{f"B{index}":"B_LA" for index in range(1,len(observations)+1)},"burden_partition_decisions":[],"observation_dispositions":[],"input_coverage":{"all_observation_unit_ids":observation_ids,"pressure_bearing_unit_ids":observation_ids,"explicitly_disposed_unit_ids":[],"unaccounted_unit_ids":[]},"release_state":"OPEN"}
        self.assertEqual(self.require_validator()(record, upstream_source_text=source), [])

    def test_active_invalids_fail_for_pinned_reason(self) -> None:
        for expectation_path in sorted((FIXTURES / "invalid").glob("*.expectation.json")):
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            path = expectation_path.with_name(expectation["fixture"])
            findings = self.require_validator()(json.loads(path.read_text(encoding="utf-8")), upstream_source_text=upstream_source(path))
            with self.subTest(path=path.name):
                self.assertTrue(findings, "invalid fixture survived")
                self.assertEqual(findings[0]["failure_class"], expectation["expected_failure_class"])
                self.assertEqual(findings[0]["failure_subcode"], expectation["expected_failure_subcode"])


if __name__ == "__main__":
    unittest.main()
