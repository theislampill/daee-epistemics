#!/usr/bin/env python3
"""Contract tests for canonical atomics Markdown byte integrity."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import check_stub_integrity as integrity  # noqa: E402
import run_local_ci  # noqa: E402


FIXTURES = Path(__file__).resolve().parent / "fixtures"
DIAGNOSTIC_IR_REL = "atomics/skill/references/diagnostics/diagnostic-ir.md"


class CanonicalMarkdownIntegrityTests(unittest.TestCase):
    def validate(self, raw: bytes, rel: str = DIAGNOSTIC_IR_REL) -> list[str]:
        return integrity.markdown_source_errors(raw, rel)

    def test_intact_diagnostic_ir_fixture_passes(self) -> None:
        raw = (FIXTURES / "valid/diagnostic-ir-intact.md").read_bytes()
        self.assertEqual([], self.validate(raw))

    def test_historical_simple_mate_truncation_fails_closed(self) -> None:
        raw = (FIXTURES / "invalid/diagnostic-ir-historical-truncation.md").read_bytes()
        errors = self.validate(raw)
        self.assertTrue(any("historical truncation boundary" in error for error in errors))
        self.assertTrue(any("unclosed fenced block" in error for error in errors))
        self.assertTrue(any("terminal Failure Tests" in error for error in errors))
        self.assertFalse(any("final LF" in error for error in errors))

    def test_relocated_close_cannot_swallow_terminal_headings(self) -> None:
        raw = (FIXTURES / "invalid/diagnostic-ir-relocated-close.md").read_bytes()
        errors = self.validate(raw)
        self.assertFalse(any("unclosed fenced block" in error for error in errors))
        self.assertTrue(any("outside fenced blocks" in error for error in errors))

    def test_invalid_utf8_fails_before_text_validation(self) -> None:
        raw = (FIXTURES / "valid/diagnostic-ir-intact.md").read_bytes() + b"\xff\n"
        errors = self.validate(raw)
        self.assertTrue(any("strict UTF-8" in error for error in errors))

    def test_missing_deliberate_final_lf_fails(self) -> None:
        raw = (FIXTURES / "valid/diagnostic-ir-intact.md").read_bytes().rstrip(b"\n")
        errors = self.validate(raw)
        self.assertTrue(any("final LF" in error for error in errors))

    def test_commonmark_fence_requires_matching_character_and_sufficient_length(self) -> None:
        raw = b"---\nid: x\nmodule_class: x\ncanonical_path: x\n---\n\n````text\n```\n"
        errors = self.validate(raw, "atomics/skill/references/diagnostics/example.md")
        self.assertTrue(any("unclosed fenced block" in error for error in errors))

    def test_live_source_gate_precedes_every_generator_and_package_check(self) -> None:
        commands = run_local_ci.COMMANDS
        self_test_index = commands.index("python tools/check_stub_integrity.py --self-test")
        live_index = commands.index("python tools/check_stub_integrity.py")
        protected_indexes = [
            index
            for index, command in enumerate(commands)
            if "build_compiled_runtime.py" in command
            or "build_framework_pipeline.py" in command
            or "check_package_shape.py" in command
            or "build_package" in command
        ]
        self.assertLess(self_test_index, live_index)
        self.assertTrue(protected_indexes)
        self.assertLess(live_index, min(protected_indexes))


if __name__ == "__main__":
    unittest.main()
