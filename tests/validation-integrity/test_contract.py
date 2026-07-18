#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from check_validation_registry import run_fixture_inventory  # noqa: E402
from checker_execution_snapshot import create_execution_snapshot  # noqa: E402
from validation_registry import load_registry  # noqa: E402


class ValidationIntegrityContractTests(unittest.TestCase):
    def test_registered_source_bytes_are_committed_lf_and_private_execution_exact(self) -> None:
        registry = load_registry()
        source_rows = [
            ("checker", str(row["checker_id"]), row)
            for row in registry["checkers"]
        ] + [
            ("consumer", str(row["consumer_id"]), row)
            for row in registry["consumers"]
        ]
        paths = [str(row["source_path"]) for _kind, _source_id, row in source_rows]
        self.assertEqual(3, len(registry["consumers"]))
        self.assertEqual(len(paths), len(set(paths)), "registered source paths must be unique")

        attr_proc = subprocess.run(
            ["git", "check-attr", "-z", "eol", "--", *paths],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        attr_fields = attr_proc.stdout.split(b"\0")
        self.assertEqual(b"", attr_fields.pop())
        self.assertEqual(0, len(attr_fields) % 3)
        eol_attributes = {
            attr_fields[index].decode("utf-8"): attr_fields[index + 2].decode("utf-8")
            for index in range(0, len(attr_fields), 3)
        }

        tracked_proc = subprocess.run(
            ["git", "ls-files", "--eol", "-z", "--", *paths],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        tracked_eols: dict[str, tuple[str, str]] = {}
        for raw_record in tracked_proc.stdout.split(b"\0"):
            if not raw_record:
                continue
            metadata, path = raw_record.decode("utf-8").split("\t", 1)
            fields = metadata.split()
            tracked_eols[path] = (fields[0], fields[1])

        checker_plan = [row for kind, _source_id, row in source_rows if kind == "checker"]
        output_path = ROOT / "tests/validation-integrity/artifacts/output.md"
        problems: list[str] = []
        with tempfile.TemporaryDirectory(dir=ROOT / "tests/validation-integrity") as temp:
            execution = create_execution_snapshot(
                root=ROOT,
                destination=Path(temp) / "private-execution",
                plan=checker_plan,
                output_path=output_path,
            )
            manifest_by_path = {
                str(row["path"]): row for row in execution.manifest["files"]
            }
            for kind, source_id, row in source_rows:
                relative = str(row["source_path"])
                working_bytes = (ROOT / relative).read_bytes()
                working_sha256 = hashlib.sha256(working_bytes).hexdigest()
                prefix = f"{kind} {source_id} ({relative})"
                if eol_attributes.get(relative) != "lf":
                    problems.append(
                        f"{prefix}: git check-attr eol is {eol_attributes.get(relative)!r}, not 'lf'"
                    )
                if tracked_eols.get(relative) != ("i/lf", "w/lf"):
                    problems.append(
                        f"{prefix}: git index/worktree EOL is {tracked_eols.get(relative)!r}, not ('i/lf', 'w/lf')"
                    )
                if b"\r" in working_bytes:
                    problems.append(f"{prefix}: working bytes contain CR instead of exact LF")
                if row.get("source_sha256") != working_sha256:
                    problems.append(
                        f"{prefix}: registry SHA {row.get('source_sha256')} != working SHA {working_sha256}"
                    )
                if execution.files.get(relative) != working_bytes:
                    problems.append(f"{prefix}: private copy bytes differ from working bytes")
                private_path = execution.root / Path(relative)
                if not private_path.is_file() or private_path.read_bytes() != working_bytes:
                    problems.append(f"{prefix}: private readback bytes differ from working bytes")
                manifest_row = manifest_by_path.get(relative)
                if manifest_row is None or manifest_row.get("sha256") != working_sha256:
                    problems.append(f"{prefix}: private manifest SHA differs from working SHA")
                if kind == "checker":
                    try:
                        executable_bytes = execution.source_path(row).read_bytes()
                    except ValueError as exc:
                        problems.append(f"{prefix}: private executable rejected: {exc}")
                    else:
                        if executable_bytes != working_bytes:
                            problems.append(f"{prefix}: private executable bytes differ from working bytes")

        self.assertEqual([], problems, "\n" + "\n".join(problems))

    def test_inventory(self) -> None:
        inventory = json.loads((Path(__file__).parent / "inventory.json").read_text(encoding="utf-8"))
        problems, counts = run_fixture_inventory(Path(__file__).parent, inventory)
        self.assertEqual([], problems)
        self.assertEqual((2, 13), counts)

    def test_external_expectation_and_verdict(self) -> None:
        fixture_root = Path(__file__).parent / "valid"
        proc = subprocess.run(
            [sys.executable, "-B", str(TOOLS / "assert_expected_rejection.py"),
             "--expectation", str((fixture_root / "right-reason-stage04.verdict.expectation.json").relative_to(ROOT)),
             "--verdict", str((fixture_root / "right-reason-stage04.verdict.json").relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
