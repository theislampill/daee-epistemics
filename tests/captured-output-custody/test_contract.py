from __future__ import annotations

import importlib.util
import errno
import os
import json
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from _support import apply_fault, build_base_bundle, make_valid_retry


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

MODULES = {
    "capture": ("check_captured_output_manifest", "validate_capture_manifest"),
    "comparison": ("check_captured_output_manifest", "validate_comparison_manifest"),
    "topology": ("check_topology_review", "validate_topology_review"),
    "cold": ("check_cold_comprehensiveness_review", "validate_cold_review"),
    "incident": ("check_review_incident_report", "validate_incident_report"),
}


def load_validator(kind: str):
    module_name, function_name = MODULES[kind]
    path = TOOLS / f"{module_name}.py"
    if not path.exists():
        return lambda *_args, **_kwargs: []
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, function_name)


class CustodyContractTests(unittest.TestCase):
    def test_malformed_nested_shapes_return_findings_without_crashing(self) -> None:
        from _support import load_json, write_json
        cases=(("capture","capture","structural_replay",lambda value:value.update({"structural_replay":{"checker_results":"not-an-array"}})),("topology","topology","schema_contract",lambda value:value.update({"artifacts":[]})))
        for name,key,expected_class,mutate in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory(prefix="daee-a01-shape-") as temp:
                root=Path(temp);paths=build_base_bundle(root);value=load_json(paths[key]);mutate(value);write_json(root,paths[key].name,value)
                try:findings=load_validator(key)(paths[key],root)
                except (KeyError,TypeError) as exc:self.fail(f"validator crashed instead of returning Finding: {exc!r}")
                self.assertTrue(findings);self.assertEqual(findings[0].failure_class,expected_class)

    def test_stage_identity_order_and_topology_aliases_reject(self) -> None:
        from _support import artifact, load_json, write_json
        cold_validator=load_validator("cold");topology_validator=load_validator("topology")
        with tempfile.TemporaryDirectory(prefix="daee-a01-stage-duplicate-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["cold"]);value["stage_records"][1]=value["stage_records"][0];write_json(root,"cold-review.json",value);findings=cold_validator(paths["cold"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"duplicate-stage-evidence")
        with tempfile.TemporaryDirectory(prefix="daee-a01-stage-alias-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["topology"]);value["artifacts"]["stage04"]=value["artifacts"]["stage02"];write_json(root,"topology-review.json",value);findings=topology_validator(paths["topology"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"topology-stage-alias")
        with tempfile.TemporaryDirectory(prefix="daee-a01-reviewer-drift-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["topology"]);value["reviewer"]["identity_or_accountable_role"]="independent-reviewer-x";write_json(root,"topology-review.json",value);findings=topology_validator(paths["topology"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"reviewer-identity-drift")

    def test_package_checker_verifier_and_authorization_identity_drift_reject(self) -> None:
        from _support import artifact, load_json, write_json, write_text
        capture_validator=load_validator("capture");cold_validator=load_validator("cold")
        with tempfile.TemporaryDirectory(prefix="daee-a01-package-swap-") as temp:
            root=Path(temp);paths=build_base_bundle(root);old=(root/"package.skill").read_bytes();write_text(root,"package-substitute.skill","X"*len(old));value=load_json(paths["capture"]);value["runtime"]["package"]=artifact(root,"package-substitute.skill");write_json(root,"capture-manifest.json",value);findings=capture_validator(paths["capture"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"package-build-binding")
        with tempfile.TemporaryDirectory(prefix="daee-a01-checker-source-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["capture"]);value["structural_replay"]["checker_results"][0]["checker_source_sha256"]="0"*64;write_json(root,"capture-manifest.json",value);findings=capture_validator(paths["capture"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"checker-source-binding")
        with tempfile.TemporaryDirectory(prefix="daee-a01-auth-drift-") as temp:
            root=Path(temp);paths=build_base_bundle(root);auth=load_json(root/"review-authorization-1.json");auth["case_id"]="other-case";write_json(root,"foreign-auth.json",auth);value=load_json(paths["cold"]);value["review_authorization"]=artifact(root,"foreign-auth.json");write_json(root,"cold-review.json",value);findings=cold_validator(paths["cold"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"review-authorization-binding")

    def test_second_human_and_review_ids_are_distinct_and_unique(self) -> None:
        from _support import artifact, load_json, write_json
        validator=load_validator("topology")
        with tempfile.TemporaryDirectory(prefix="daee-a01-second-identity-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["topology"]);value["reviewer"]["relationship_to_producer"]="patch-owner";value["owner_adjudication"]["patch_owner_involved"]=True;proof=load_json(root/"second-review.json");proof["reviewer_identity_or_accountable_role"]=value["reviewer"]["identity_or_accountable_role"];write_json(root,"second-review.json",proof);value["second_independent_review"]={"required":True,"reason":"patch-owner-reversal","review":artifact(root,"second-review.json")};write_json(root,"topology-review.json",value);findings=validator(paths["topology"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"second-reviewer-not-distinct")
        with tempfile.TemporaryDirectory(prefix="daee-a01-finding-id-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["topology"]);value["findings"].append(dict(value["findings"][0]));write_json(root,"topology-review.json",value);findings=validator(paths["topology"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"duplicate-human-finding")

    def test_retry_proofs_and_comparison_replicates_are_nonempty_and_nonreused(self) -> None:
        from _support import artifact, load_json, write_json
        cold_validator=load_validator("cold");comparison_validator=load_validator("comparison")
        with tempfile.TemporaryDirectory(prefix="daee-a01-tautology-") as temp:
            root=Path(temp);build_base_bundle(root);retry=make_valid_retry(root,"packet_insufficiency");delta=load_json(root/"packet-delta.json");delta["added_refs"]=[];delta["removed_refs"]=[];write_json(root,"packet-delta.json",delta);packet=load_json(root/"packet-rebuilt/manifest.json");packet["packet_delta"]=artifact(root,"packet-delta.json");write_json(root,"packet-rebuilt/manifest.json",packet);review=load_json(retry);review["packet"]=artifact(root,"packet-rebuilt/manifest.json");write_json(root,"cold-review-retry.json",review);findings=cold_validator(retry,root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"packet-delta-empty")
        with tempfile.TemporaryDirectory(prefix="daee-a01-pair-reuse-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["comparison"]);value["pairings"].append({**value["pairings"][0],"pair_id":"pair-2"});value["regression_status"]="replicated-candidate";write_json(root,"comparison.json",value);findings=comparison_validator(paths["comparison"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"pair-reuse")
        with tempfile.TemporaryDirectory(prefix="daee-a01-not-observed-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["comparison"]);value["regression_status"]="not-observed";write_json(root,"comparison.json",value);findings=comparison_validator(paths["comparison"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"not-observed-direction")

    def test_verified_snapshot_bytes_survive_same_length_path_swaps(self) -> None:
        import build_captured_output_verdict as verdict_builder
        import check_captured_output_manifest as custody
        from _support import load_json, write_json
        with tempfile.TemporaryDirectory(prefix="daee-a01-snapshot-verdict-") as temp:
            root=Path(temp);paths=build_base_bundle(root);original=load_json(paths["capture"]);replacement=dict(original);replacement["capture_id"]="capture-evil";self.assertEqual(len(json.dumps(original,sort_keys=True)),len(json.dumps(replacement,sort_keys=True)))
            original_validate=verdict_builder.validate_capture_manifest
            def validate_then_swap(source,custody_root):
                result=original_validate(source,custody_root);write_json(root,"capture-manifest.json",replacement);return result
            with mock.patch.object(verdict_builder,"validate_capture_manifest",validate_then_swap):data=verdict_builder.build(paths["capture"],root,"capture")
            self.assertEqual(data["capture_id"],"capture-head")
        with tempfile.TemporaryDirectory(prefix="daee-a01-snapshot-comparison-") as temp:
            root=Path(temp);paths=build_base_bundle(root);original=load_json(paths["comparison"]);replacement=dict(original);replacement["comparison_id"]="comparison-omega";self.assertEqual(len(json.dumps(original,sort_keys=True)),len(json.dumps(replacement,sort_keys=True)))
            original_validate=verdict_builder.validate_comparison_manifest
            def validate_comparison_then_swap(source,custody_root):
                result=original_validate(source,custody_root);write_json(root,"comparison.json",replacement);return result
            with mock.patch.object(verdict_builder,"validate_comparison_manifest",validate_comparison_then_swap):data=verdict_builder.build(paths["comparison"],root,"comparison")
            self.assertEqual(data["comparison_id"],"comparison-alpha")
        with tempfile.TemporaryDirectory(prefix="daee-a01-snapshot-nested-") as temp:
            root=Path(temp);paths=build_base_bundle(root);original_verify=custody.verify_artifact;swapped=[]
            def verify_then_swap(ref,custody_root,label):
                verified=original_verify(ref,custody_root,label)
                if "topology_review" in label:write_json(root,"topology-review.json",{"same":"length-placeholder"});swapped.append(label)
                return verified
            with mock.patch.object(custody,"verify_artifact",verify_then_swap):findings=custody.validate_capture_manifest(paths["capture"],root)
            self.assertEqual(findings,[]);self.assertTrue(swapped)
        import check_cold_comprehensiveness_review as cold_module
        with tempfile.TemporaryDirectory(prefix="daee-a01-snapshot-incident-") as temp:
            root=Path(temp);build_base_bundle(root);retry=make_valid_retry(root,"reviewer_transport");original_verify=cold_module.verify_artifact;swapped=[]
            def incident_then_swap(ref,custody_root,label):
                verified=original_verify(ref,custody_root,label)
                if label=="owner-incident":write_json(root,"incident-retry.json",{"same":"length-placeholder"});swapped.append(label)
                return verified
            with mock.patch.object(cold_module,"verify_artifact",incident_then_swap):findings=cold_module.validate_cold_review(retry,root)
            self.assertEqual(findings,[]);self.assertTrue(swapped)

    def test_verdict_publication_race_preserves_competitor_and_fault_boundary_is_explicit(self) -> None:
        import build_captured_output_verdict as module
        import check_captured_output_manifest as custody
        from _support import build_base_bundle
        with tempfile.TemporaryDirectory(prefix="daee-a01-verdict-race-") as temp:
            root=Path(temp);build_base_bundle(root);target=root/"verdict.json";competitor=b'competitor-bytes\n';real_publish=module.atomic_publish_bytes
            def race_publish(path,data):
                path.write_bytes(competitor);return real_publish(path,data)
            with mock.patch.object(module,"atomic_publish_bytes",race_publish):
                old=sys.argv;sys.argv=["build_captured_output_verdict.py","--capture","capture-manifest.json","--custody-root",str(root),"--out","verdict.json"]
                try:code=module.main()
                finally:sys.argv=old
            self.assertEqual(code,1);self.assertEqual(target.read_bytes(),competitor)
        for boundary in ("after-stage-write","after-stage-verify","after-publish"):
            with self.subTest(boundary=boundary),tempfile.TemporaryDirectory(prefix="daee-a01-verdict-fault-") as temp:
                root=Path(temp);target=root/"verdict.json"
                with self.assertRaises(custody.PublicationError):custody.atomic_publish_bytes(target,b'complete\n',fault_at=boundary)
                if boundary=="after-publish":self.assertEqual(target.read_bytes(),b'complete\n')
                else:self.assertFalse(target.exists())
                self.assertFalse(any(root.glob(".*.stage-*")))

    def test_packet_publication_cleans_prepublish_and_preserves_visible_final(self) -> None:
        import build_cold_review_packet as module
        import check_captured_output_manifest as custody
        from _support import artifact, build_base_bundle, write_json
        with tempfile.TemporaryDirectory(prefix="daee-a01-packet-fault-") as temp:
            root=Path(temp);build_base_bundle(root);spec={"packet_id":"atomic","protocol_id":"protocol-alpha","case_id":"case-alpha","cycle_id":"cycle-alpha","retry_mode":"initial","input":artifact(root,"input.txt"),"output":artifact(root,"output.md"),"purpose":"Cold reconstruction.","public_rubric":"Reconstruct before grading.","stage_records":[artifact(root,f"stages/stage-{n:02d}.json") for n in range(1,9)],"witness_refs":[artifact(root,"witness.json")],"audit_refs":[artifact(root,"audit.json")],"body_refs":[artifact(root,"body.json")],"review_authorization":artifact(root,"review-authorization-1.json"),"anti_answer_bank_proof":artifact(root,"anti-bank.json")};write_json(root,"atomic-spec.json",spec)
            for boundary in ("after-stage-file-0","after-stage-file-1","after-stage-write","after-stage-verify","after-publish"):
                with self.subTest(boundary=boundary):
                    with self.assertRaisesRegex(ValueError,"injected publication failure"):module.build(root/"atomic-spec.json",root,"packet-final",fault_at=boundary)
                    if boundary=="after-publish":
                        self.assertTrue((root/"packet-final"/"manifest.json").is_file());shutil.rmtree(root/"packet-final")
                    else:self.assertFalse((root/"packet-final").exists())
                    self.assertFalse(any(root.glob(".*.stage-*")))
            competitor=root/"packet-final";competitor.mkdir();(competitor/"owner.txt").write_bytes(b'competitor')
            with self.assertRaisesRegex(ValueError,"target already exists"):module.build(root/"atomic-spec.json",root,"packet-final")
            self.assertEqual((competitor/"owner.txt").read_bytes(),b'competitor');self.assertFalse(any(root.glob(".*.stage-*")))

    def test_publication_cleanup_preserves_swapped_competitors(self) -> None:
        import check_captured_output_manifest as custody
        with tempfile.TemporaryDirectory(prefix="daee-a01-file-swap-") as temp:
            root=Path(temp);target=root/"verdict.json";competitor=b'competitor-bytes\n';original_read=Path.read_bytes;swapped=[]
            def swap_file_before_final_cas(path):
                if path==target and not swapped:
                    path.unlink();path.write_bytes(competitor);swapped.append(True)
                return original_read(path)
            with mock.patch.object(Path,"read_bytes",swap_file_before_final_cas):
                with self.assertRaisesRegex(ValueError,"changed during final CAS"):
                    custody.atomic_publish_bytes(target,b'publisher-bytes\n')
            self.assertEqual(target.read_bytes(),competitor);self.assertFalse(any(root.glob(".*.stage-*")))
        with tempfile.TemporaryDirectory(prefix="daee-a01-directory-swap-") as temp:
            root=Path(temp);target=root/"packet-final";competitor=b'competitor-manifest\n';original_read=Path.read_bytes;swapped=[]
            def swap_directory_before_final_cas(path):
                if path==target/"manifest.json" and not swapped:
                    shutil.rmtree(target);target.mkdir();(target/"manifest.json").write_bytes(competitor);(target/"owner.txt").write_bytes(b'competitor-owner\n');swapped.append(True)
                return original_read(path)
            with mock.patch.object(Path,"read_bytes",swap_directory_before_final_cas):
                with self.assertRaisesRegex(ValueError,"changed during final CAS"):
                    custody.atomic_publish_directory(target,{"manifest.json":b'publisher-manifest\n'})
            self.assertEqual((target/"manifest.json").read_bytes(),competitor);self.assertEqual((target/"owner.txt").read_bytes(),b'competitor-owner\n');self.assertFalse(any(root.glob(".*.stage-*")))

    def test_empty_directory_competitor_is_never_replaced_even_with_posix_rename_semantics(self) -> None:
        import check_captured_output_manifest as custody
        with tempfile.TemporaryDirectory(prefix="daee-a01-empty-competitor-") as temp:
            root=Path(temp);target=root/"packet-final";target.mkdir();before=target.stat();original_rename=Path.rename
            def posix_replace_empty_directory(source,destination):
                destination.rmdir()
                return original_rename(source,destination)
            with mock.patch.object(Path,"rename",posix_replace_empty_directory):
                with self.assertRaisesRegex(ValueError,"target already exists"):custody.atomic_publish_directory(target,{"manifest.json":b'complete\n'})
            after=target.stat()
            self.assertEqual((after.st_dev,after.st_ino,after.st_ctime_ns),(before.st_dev,before.st_ino,before.st_ctime_ns))
            self.assertEqual(list(target.iterdir()),[]);self.assertFalse(any(root.glob(".*.stage-*")))

    def test_directory_noreplace_platform_dispatch_and_fail_closed_errors(self) -> None:
        import check_captured_output_manifest as custody
        primitive=getattr(custody,"_rename_directory_noreplace",None)
        self.assertTrue(callable(primitive),"atomic directory no-replace primitive is required")
        if primitive is None:return
        source=Path("source");target=Path("target")
        with mock.patch.object(custody.os,"name","nt"),mock.patch.object(custody,"_rename_directory_noreplace_windows") as windows:
            primitive(source,target);windows.assert_called_once_with(source,target)
        with mock.patch.object(custody.os,"name","posix"),mock.patch.object(custody.sys,"platform","linux"),mock.patch.object(custody,"_rename_directory_noreplace_linux") as linux:
            primitive(source,target);linux.assert_called_once_with(source,target)
        with mock.patch.object(custody.os,"name","posix"),mock.patch.object(custody.sys,"platform","darwin"):
            with self.assertRaisesRegex(ValueError,"unsupported platform"):primitive(source,target)
        successful_linux=mock.Mock(return_value=0)
        custody._rename_directory_noreplace_linux(source,target,renameat2=successful_linux)
        linux_args=successful_linux.call_args.args
        self.assertEqual((linux_args[0],linux_args[2],linux_args[4]),(-100,-100,1))
        self.assertEqual((linux_args[1],linux_args[3]),(os.fsencode(source),os.fsencode(target)))
        for error,marker in ((errno.EEXIST,"target already exists"),(errno.ENOSYS,"unavailable")):
            with self.subTest(error=error):
                fake=mock.Mock(return_value=-1)
                with mock.patch.object(custody.ctypes,"get_errno",return_value=error):
                    with self.assertRaisesRegex(ValueError,marker):custody._rename_directory_noreplace_linux(source,target,renameat2=fake)
        rename=mock.Mock(side_effect=OSError(errno.EEXIST,"exists"))
        with self.assertRaisesRegex(ValueError,"target already exists"):custody._rename_directory_noreplace_windows(source,target,rename=rename)
        with tempfile.TemporaryDirectory(prefix="daee-a01-unsupported-publish-") as temp:
            root=Path(temp);unsupported_target=root/"packet-final"
            with mock.patch.object(custody.os,"name","posix"),mock.patch.object(custody.sys,"platform","darwin"):
                with self.assertRaisesRegex(ValueError,"unsupported platform"):custody.atomic_publish_directory(unsupported_target,{"manifest.json":b'complete\n'})
            self.assertFalse(unsupported_target.exists());self.assertFalse(any(root.glob(".*.stage-*")))
    def test_root_cross_object_probes_reject_for_pinned_reasons(self) -> None:
        import copy
        from _support import artifact, load_json, write_json
        probes = []
        def arbitrary_topology(root, paths):
            write_json(root,"topology-review.json",{"not":"a review"});value=load_json(paths["capture"]);value["topology_review"]=artifact(root,"topology-review.json");write_json(root,"capture-manifest.json",value);return "capture",paths["capture"]
        probes.append(("arbitrary topology",arbitrary_topology,"cross_object","topology-review-invalid"))
        def empty_checker(root, paths):
            value=load_json(paths["capture"]);value["structural_replay"]["checker_results"]=[{}];write_json(root,"capture-manifest.json",value);return "capture",paths["capture"]
        probes.append(("empty checker row",empty_checker,"structural_replay","checker-row-shape"))
        def initial_identity(root, paths):
            initial=load_json(root/"initial-assessment.json");initial.update({"case_id":"other-case","cycle_id":"other-cycle"});write_json(root,"initial-assessment.json",initial);review=load_json(paths["topology"]);review["initial_assessment"]=artifact(root,"initial-assessment.json");review["cold_review_disclosure"]["initial_assessment_sha256_at_disclosure"]=review["initial_assessment"]["sha256"];write_json(root,"topology-review.json",review);return "topology",paths["topology"]
        probes.append(("initial identity",initial_identity,"review_binding","initial-identity-mismatch"))
        def arbitrary_cold(root, paths):
            write_json(root,"cold-review.json",{"case_id":"other-case","cycle_id":"other-cycle","findings":[{"finding_id":"cold-finding-1","severity":"material"}]});review=load_json(paths["topology"]);review["cold_review_disclosure"]["cold_review"]=artifact(root,"cold-review.json");write_json(root,"topology-review.json",review);return "topology",paths["topology"]
        probes.append(("arbitrary cold",arbitrary_cold,"cross_object","cold-review-invalid"))
        def duplicate_cold(root, paths):
            cold=load_json(root/"cold-review.json");cold["findings"].append(copy.deepcopy(cold["findings"][0]));write_json(root,"cold-review.json",cold);review=load_json(paths["topology"]);review["cold_review_disclosure"]["cold_review"]=artifact(root,"cold-review.json");write_json(root,"topology-review.json",review);return "topology",paths["topology"]
        probes.append(("duplicate cold finding",duplicate_cold,"review_set","duplicate-cold-finding"))
        def arbitrary_incident(root, paths):
            retry=make_valid_retry(root,"reviewer_transport");write_json(root,"incident-retry.json",{"not":"an incident"});value=load_json(retry);value["invalid_classification"]["owner_incident_report"]=artifact(root,"incident-retry.json");write_json(root,"cold-review-retry.json",value);return "cold",retry
        probes.append(("arbitrary incident",arbitrary_incident,"retry_lineage","incident-semantic-invalid"))
        def pass_pass_candidate(root, paths):
            value=load_json(paths["comparison"]);value["regression_status"]="candidate-observed";write_json(root,"comparison.json",value);return "comparison",paths["comparison"]
        probes.append(("PASS/PASS candidate",pass_pass_candidate,"claim_overreach","candidate-status-without-direction"))
        for name,mutate,expected_class,expected_subcode in probes:
            with self.subTest(probe=name), tempfile.TemporaryDirectory(prefix="daee-a01-root-probe-") as temp:
                root=Path(temp);paths=build_base_bundle(root);kind,path=mutate(root,paths);findings=load_validator(kind)(path,root)
                self.assertTrue(findings,f"root probe survived: {name}")
                self.assertEqual((findings[0].failure_class,findings[0].failure_subcode),(expected_class,expected_subcode))

    def test_neighboring_duplicate_ids_and_answer_key_markers_reject(self) -> None:
        from _support import load_json, write_json, artifact
        comparison_validator=load_validator("comparison")
        for mutation,subcode in ((lambda value:value["cells"][3]["captures"].append(value["cells"][3]["captures"][0]),"duplicate-capture-id"),(lambda value:value["pairings"].append(dict(value["pairings"][0])),"duplicate-pair-id")):
            with self.subTest(subcode=subcode), tempfile.TemporaryDirectory(prefix="daee-a01-id-") as temp:
                root=Path(temp);paths=build_base_bundle(root);value=load_json(paths["comparison"]);mutation(value);write_json(root,"comparison.json",value);findings=comparison_validator(paths["comparison"],root)
                self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,subcode)
        if str(TOOLS) not in sys.path:sys.path.insert(0,str(TOOLS))
        from build_cold_review_packet import build
        with tempfile.TemporaryDirectory(prefix="daee-a01-marker-") as temp:
            root=Path(temp);build_base_bundle(root);spec={"packet_id":"marker","protocol_id":"protocol-alpha","case_id":"case-alpha","cycle_id":"cycle-alpha","retry_mode":"initial","input":artifact(root,"input.txt"),"output":artifact(root,"output.md"),"purpose":"Use this golden conclusion when grading.","public_rubric":"Reconstruct before grading.","stage_records":[artifact(root,f"stages/stage-{n:02d}.json") for n in range(1,9)],"witness_refs":[artifact(root,"witness.json")],"audit_refs":[artifact(root,"audit.json")],"body_refs":[artifact(root,"body.json")],"review_authorization":artifact(root,"review-authorization-1.json"),"anti_answer_bank_proof":artifact(root,"anti-bank.json")};write_json(root,"marker-spec.json",spec)
            with self.assertRaisesRegex(ValueError,"answer-bank"):build(root/"marker-spec.json",root,"marker-out")

    def test_candidate_observed_accepts_one_admissible_base_pass_head_fail_pair(self) -> None:
        from _support import artifact, load_json, write_json
        validator=load_validator("comparison")
        with tempfile.TemporaryDirectory(prefix="daee-a01-direction-") as temp:
            root=Path(temp);paths=build_base_bundle(root);capture=load_json(paths["capture"]);row=capture["structural_replay"]["checker_results"][0];row.update({"exit_code":1,"first_failure":True});capture["structural_replay"].update({"aggregate_status":"FAIL","first_failed_checker":row["checker_id"]});verdict=load_json(root/"verifier-verdict.json");verdict.update({"aggregate_status":"FAIL","first_failed_checker":row["checker_id"]});verdict["checker_results"][0].update({"exit_code":1,"first_failure":True});write_json(root,"verifier-verdict-head.json",verdict);capture["structural_replay"]["verdict"]=artifact(root,"verifier-verdict-head.json");write_json(root,"capture-manifest.json",capture);comparison=load_json(paths["comparison"]);comparison["cells"][3]["captures"][0]=artifact(root,"capture-manifest.json");comparison["regression_status"]="candidate-observed";write_json(root,"comparison.json",comparison)
            self.assertEqual(validator(paths["comparison"],root),[])

    def test_nested_proof_cohort_and_selection_neighbors_reject(self) -> None:
        from _support import artifact, load_json, write_json
        cold_validator=load_validator("cold")
        with tempfile.TemporaryDirectory(prefix="daee-a01-proof-") as temp:
            root=Path(temp);build_base_bundle(root);retry=make_valid_retry(root,"packet_insufficiency")
            write_json(root,"packet-delta.json",{"not":"a delta"});packet=load_json(root/"packet-rebuilt/manifest.json");packet["packet_delta"]=artifact(root,"packet-delta.json");write_json(root,"packet-rebuilt/manifest.json",packet);review=load_json(retry);review["packet"]=artifact(root,"packet-rebuilt/manifest.json");write_json(root,"cold-review-retry.json",review)
            findings=cold_validator(retry,root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"packet-delta-shape")
        proof_cases=(("predecessor_packet","predecessor-binding"),("builder_red_green_proof","builder-proof-shape"),("anti_answer_bank_proof","anti-bank-shape"),("review_authorization","authorization-shape"))
        for field,subcode in proof_cases:
            with self.subTest(nested_proof=field), tempfile.TemporaryDirectory(prefix="daee-a01-nested-proof-") as temp:
                root=Path(temp);build_base_bundle(root);retry=make_valid_retry(root,"packet_insufficiency");write_json(root,"arbitrary-proof.json",{"not":"evidence"});packet=load_json(root/"packet-rebuilt/manifest.json");packet[field]=artifact(root,"arbitrary-proof.json");write_json(root,"packet-rebuilt/manifest.json",packet);review=load_json(retry);review["packet"]=artifact(root,"packet-rebuilt/manifest.json");write_json(root,"cold-review-retry.json",review);findings=cold_validator(retry,root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,subcode)
        for variant,mutate,subcode in (("empty",lambda value:value.update({"case_ids":[]}),"empty-cohort"),("duplicate",lambda value:value.update({"case_ids":["case-alpha","case-alpha"]}),"duplicate-cohort-case"),("protocol-drift",lambda value:value.update({"protocol_id":"other-protocol"}),"cohort-manifest-binding")):
            with self.subTest(cohort=variant), tempfile.TemporaryDirectory(prefix="daee-a01-cohort-negative-") as temp:
                root=Path(temp);paths=build_base_bundle(root);cohort=load_json(root/"cohort-manifest.json");mutate(cohort);write_json(root,"cohort-manifest.json",cohort);review=load_json(paths["cold"]);review["protocol_replay"]["cohort_manifest"]=artifact(root,"cohort-manifest.json");write_json(root,"cold-review.json",review);findings=cold_validator(paths["cold"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,subcode)
        with tempfile.TemporaryDirectory(prefix="daee-a01-lineage-gap-") as temp:
            root=Path(temp);build_base_bundle(root);retry=make_valid_retry(root,"reviewer_transport");review=load_json(retry);review["attempt_index"]=3;write_json(root,"cold-review-retry.json",review);findings=cold_validator(retry,root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"attempt-lineage-cardinality")
        with tempfile.TemporaryDirectory(prefix="daee-a01-prior-selected-") as temp:
            root=Path(temp);build_base_bundle(root);retry=make_valid_retry(root,"reviewer_transport");prior=load_json(root/"cold-review-predecessor.json");prior["selection"]["selected_for_final"]=True;write_json(root,"cold-review-predecessor.json",prior);review=load_json(retry);new_ref=artifact(root,"cold-review-predecessor.json");review["attempt_lineage"]=[new_ref];review["predecessor_review_attempt"]=new_ref;write_json(root,"cold-review-retry.json",review);findings=cold_validator(retry,root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"prior-attempt-selected")
        with tempfile.TemporaryDirectory(prefix="daee-a01-latest-selection-") as temp:
            root=Path(temp);paths=build_base_bundle(root);review=load_json(paths["cold"]);review["selection"]["selected_for_final"]=False;write_json(root,"cold-review.json",review);findings=cold_validator(paths["cold"],root);self.assertTrue(findings);self.assertEqual(findings[0].failure_subcode,"latest-valid-not-selected")
    def test_all_six_schema_definitions_use_the_shared_supported_subset(self) -> None:
        if str(TOOLS) not in sys.path:
            sys.path.insert(0, str(TOOLS))
        from contract_validation import validate_schema_definition
        names = (
            "captured-output-manifest.schema.json", "captured-output-comparison.schema.json",
            "topology-review.schema.json", "topology-initial-assessment.schema.json",
            "cold-comprehensiveness-review.schema.json", "review-incident-report.schema.json",
        )
        for name in names:
            with self.subTest(schema=name):
                validate_schema_definition(json.loads((ROOT / "schema" / name).read_text(encoding="utf-8")))

    def test_path_custody_rejects_absolute_drive_unc_parent_and_symlink_escape(self) -> None:
        validator = load_validator("capture")
        with tempfile.TemporaryDirectory(prefix="daee-a01-path-") as temp:
            root = Path(temp); paths = build_base_bundle(root)
            original = json.loads(paths["capture"].read_text(encoding="utf-8"))
            probes = (("../escape", "path-traversal"), ("C:\\outside\\input.txt", "absolute-path"), ("\\\\server\\share\\input.txt", "absolute-path"), (str((root / "input.txt").resolve()), "absolute-path"))
            for candidate, subcode in probes:
                value = json.loads(json.dumps(original)); value["input"]["path"] = candidate
                paths["capture"].write_text(json.dumps(value), encoding="utf-8")
                findings = validator(paths["capture"], root)
                self.assertTrue(findings); self.assertEqual(findings[0].failure_subcode, subcode)
            outside = root.parent / f"{root.name}-outside.txt"; outside.write_text("outside", encoding="utf-8")
            link = root / "escape-link.txt"
            try:
                os.symlink(outside, link)
            except OSError:
                return
            value = json.loads(json.dumps(original)); value["input"] = {"path":"escape-link.txt","sha256":"0"*64,"byte_count":7}
            paths["capture"].write_text(json.dumps(value), encoding="utf-8")
            findings = validator(paths["capture"], root)
            self.assertTrue(findings); self.assertEqual(findings[0].failure_subcode, "symlink-escape")
            outside.unlink(missing_ok=True)

    def test_packet_builder_is_hash_bound_mutation_sensitive_and_anti_bank(self) -> None:
        if str(TOOLS) not in sys.path: sys.path.insert(0, str(TOOLS))
        from build_cold_review_packet import build
        from _support import artifact, write_json
        with tempfile.TemporaryDirectory(prefix="daee-a01-packet-") as temp:
            root=Path(temp);build_base_bundle(root)
            spec={"packet_id":"built-1","protocol_id":"protocol-alpha","case_id":"case-alpha","cycle_id":"cycle-alpha","retry_mode":"initial","input":artifact(root,"input.txt"),"output":artifact(root,"output.md"),"purpose":"Cold reconstruction and artifact review.","public_rubric":"Reconstruct before grading.","stage_records":[artifact(root,f"stages/stage-{n:02d}.json") for n in range(1,9)],"witness_refs":[artifact(root,"witness.json")],"audit_refs":[artifact(root,"audit.json")],"body_refs":[artifact(root,"body.json")],"review_authorization":artifact(root,"review-authorization-1.json"),"anti_answer_bank_proof":artifact(root,"anti-bank.json")}
            write_json(root,"packet-spec.json",spec);manifest,payload=build(root/"packet-spec.json",root,"built")
            first=__import__("hashlib").sha256(manifest.read_bytes()).hexdigest();payload_value=json.loads(payload.read_text(encoding="utf-8"))
            self.assertEqual(payload_value["output"]["content_utf8"],(root/"output.md").read_text(encoding="utf-8"))
            spec["body_refs"].append(artifact(root,"audit.json"));spec["packet_id"]="built-2";write_json(root,"packet-spec-2.json",spec);manifest2,_=build(root/"packet-spec-2.json",root,"built-2")
            self.assertNotEqual(first,__import__("hashlib").sha256(manifest2.read_bytes()).hexdigest())
            spec["expected_answer"]="forbidden";write_json(root,"packet-spec-bad.json",spec)
            with self.assertRaisesRegex(ValueError,"anti-answer-bank"): build(root/"packet-spec-bad.json",root,"built-bad")

    def test_same_packet_and_rebuilt_packet_retry_lineage_are_valid(self) -> None:
        validator=load_validator("cold")
        for cause in ("reviewer_transport","packet_insufficiency"):
            with self.subTest(cause=cause), tempfile.TemporaryDirectory(prefix="daee-a01-retry-") as temp:
                root=Path(temp);build_base_bundle(root);path=make_valid_retry(root,cause)
                self.assertEqual(validator(path,root),[])

    def test_shared_protocol_change_accepts_only_exact_full_cohort_replay(self) -> None:
        from _support import artifact, write_json
        validator=load_validator("cold")
        with tempfile.TemporaryDirectory(prefix="daee-a01-cohort-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=json.loads(paths["cold"].read_text(encoding="utf-8"))
            value["protocol_replay"]={"change_scope":"shared","cohort_manifest":artifact(root,"cohort-manifest.json"),"repeated_case_ids":["case-beta","case-alpha"]};write_json(root,"cold-review.json",value)
            self.assertEqual(validator(paths["cold"],root),[])

    def test_patch_owner_pass_requires_hash_valid_affirming_independent_review(self) -> None:
        from _support import artifact, write_json
        validator=load_validator("topology")
        with tempfile.TemporaryDirectory(prefix="daee-a01-second-") as temp:
            root=Path(temp);paths=build_base_bundle(root);value=json.loads(paths["topology"].read_text(encoding="utf-8"))
            value["reviewer"]["relationship_to_producer"]="patch-owner";value["owner_adjudication"]["patch_owner_involved"]=True
            value["second_independent_review"]={"required":True,"reason":"patch-owner-reversal","review":artifact(root,"second-review.json")};write_json(root,"topology-review.json",value)
            self.assertEqual(validator(paths["topology"],root),[])

    def test_valid_base_bundle_passes_every_validator(self) -> None:
        with tempfile.TemporaryDirectory(prefix="daee-a01-valid-") as temp:
            root = Path(temp)
            paths = build_base_bundle(root)
            for kind in MODULES:
                with self.subTest(kind=kind):
                    validator = load_validator(kind)
                    artifact = paths["capture" if kind == "capture" else kind]
                    self.assertEqual(validator(artifact, root), [])

    def test_every_single_fault_rejects_for_canonical_right_reason(self) -> None:
        scenarios = sorted((HERE / "invalid").glob("*/scenario.json"))
        self.assertGreaterEqual(len(scenarios), 19)
        for scenario_path in scenarios:
            scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
            expectation_path = scenario_path.with_name("scenario.expectation.json")
            expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
            self.assertEqual(scenario["schema"], "daee-a01-synthetic-scenario-v1")
            self.assertEqual(list(scenario), ["schema", "fault"])
            self.assertEqual(expectation["schema"], "daee-negative-fixture-expectation-v1")
            self.assertEqual(expectation["fixture"], "scenario.json")
            with self.subTest(fault=scenario["fault"]), tempfile.TemporaryDirectory(prefix="daee-a01-invalid-") as temp:
                root = Path(temp)
                paths = build_base_bundle(root)
                kind = apply_fault(root, scenario["fault"])
                artifact = paths["capture" if kind == "capture" else kind]
                findings = load_validator(kind)(artifact, root)
                self.assertTrue(findings, f"invalid artifact survived: {scenario['fault']}")
                first = findings[0]
                self.assertEqual(first.failure_class, expectation["expected_failure_class"])
                self.assertEqual(first.failure_subcode, expectation["expected_failure_subcode"])
                self.assertEqual(first.earliest_stage, expectation["expected_earliest_stage"])
                self.assertEqual(list(first.downstream_invalidated), expectation["expected_downstream_invalidated"])


if __name__ == "__main__":
    unittest.main()
