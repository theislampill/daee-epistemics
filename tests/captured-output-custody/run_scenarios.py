from __future__ import annotations
import json,sys,tempfile
from pathlib import Path
from _support import apply_fault,build_base_bundle

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;TOOLS=ROOT/"tools";sys.path.insert(0,str(TOOLS))
from contract_validation import validate_schema_subset
from check_captured_output_manifest import validate_capture_manifest,validate_comparison_manifest
from check_topology_review import validate_topology_review
from check_cold_comprehensiveness_review import validate_cold_review
from check_review_incident_report import validate_incident_report
VALIDATORS={"capture":validate_capture_manifest,"comparison":validate_comparison_manifest,"topology":validate_topology_review,"cold":validate_cold_review,"incident":validate_incident_report}

def main()->int:
 expectation_schema=json.loads((ROOT/"schema/negative-fixture-expectation.schema.json").read_text(encoding="utf-8"));problems=[];rows=[]
 for scenario_path in sorted((HERE/"invalid").glob("*/scenario.json")):
  scenario=json.loads(scenario_path.read_text(encoding="utf-8"));expectation=json.loads(scenario_path.with_name("scenario.expectation.json").read_text(encoding="utf-8"));schema_issues=validate_schema_subset(expectation,expectation_schema)
  with tempfile.TemporaryDirectory(prefix="daee-a01-direct-") as temp:
   root=Path(temp);paths=build_base_bundle(root);kind=apply_fault(root,scenario["fault"]);artifact=paths["capture" if kind=="capture" else kind];findings=VALIDATORS[kind](artifact,root)
   if schema_issues or not findings:problems.append(f"{scenario['fault']}: expectation invalid or artifact survived");continue
   first=findings[0];actual=(first.failure_class,first.failure_subcode,first.earliest_stage,list(first.downstream_invalidated));expected=(expectation["expected_failure_class"],expectation["expected_failure_subcode"],expectation["expected_earliest_stage"],expectation["expected_downstream_invalidated"])
   rendered=f"{first.failure_class} {first.failure_subcode} {first.message}".lower()
   if actual!=expected or any(marker.lower() not in rendered for marker in expectation["required_diagnostic_markers"]):problems.append(f"{scenario['fault']}: wrong reason {actual!r}");continue
   if any((root/path).exists() for path in expectation["forbidden_artifacts"]):problems.append(f"{scenario['fault']}: forbidden artifact exists");continue
   rows.append({"fault":scenario["fault"],"checker":expectation["expected_checker_id"],"earliest_stage":first.earliest_stage,"failure_class":first.failure_class,"failure_subcode":first.failure_subcode,"downstream_invalidated":list(first.downstream_invalidated),"forbidden_artifacts_absent":True})
 for row in rows:print(json.dumps(row,sort_keys=True))
 print(json.dumps({"status":"PASS" if not problems else "FAIL","valid_scenario_families":len(list((HERE/"valid").glob("*/scenario.json"))),"invalid_right_reason":len(rows),"problems":problems},sort_keys=True))
 return 0 if not problems else 1
if __name__=="__main__":raise SystemExit(main())
