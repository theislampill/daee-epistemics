#!/usr/bin/env python3
"""Pure helpers for DAEE validation registry and replay-verdict integrity."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import string
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from contract_validation import (
    PathCustodyError,
    SchemaDefinitionError,
    resolve_repo_path,
    validate_schema_subset,
)
from checker_execution_snapshot import execution_snapshot_sources

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_REL = Path("tools/validation-registry.json")
REGISTRY_PATH = ROOT / REGISTRY_REL
REGISTRY_SCHEMA_REL = Path("schema/validation-registry.schema.json")
VERDICT_SCHEMA_REL = Path("schema/checker-replay-verdict.schema.json")
EXPECTATION_SCHEMA_REL = Path("schema/negative-fixture-expectation.schema.json")
ARTIFACT_TYPES = (
    "output-md", "input-output-pair", "staged-handoff-record", "state-capsule-sequence",
    "prompt-context-manifest", "proof-sidecar-set", "retained-case-manifest",
    "captured-output-custody-manifest",
)
PROFILE_IDS = ("stage07-release", "captured-output-structural", "stage08-proof-surface", "promotion", "scorecard", "advisory")
REQUIRED_CONSUMER_CONTRACT = {
    "stage07-release-runner": (
        "tools/run_staged_current_skill_smoke.py",
        "stage07-release",
        "registry",
    ),
    "candidate-output-verifier": (
        "tools/verify_candidate_output.py",
        "captured-output-structural",
        "registry",
    ),
    "model-compliance-scorecard": (
        "tools/build_model_compliance_scorecard.py",
        "scorecard",
        "registry",
    ),
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_STATIC_FORMATTED_FRAGMENT_CHARS = 4096
MAX_STATIC_FRAGMENT_AST_DEPTH = 128
_LEGACY_PRIVATE_POLICY = re.compile(r"(?m)^\s*(BATTERY|DETECTORS|VALIDATORS)\s*(?::[^=]+)?=\s*\[")
_LEGACY_RELEASE_VALIDATOR_MARKER = "def run_release_" "validators("


@dataclass(frozen=True)
class Finding:
    failure_class: str
    message: str
    failure_subcode: str = "registry-integrity"


@dataclass(frozen=True)
class RegistrySnapshot:
    relative_path: str
    canonical_path: Path
    data: bytes
    sha256: str
    value: dict[str, Any]


def _safe(candidate: str | Path, *, root: Path = ROOT, must_exist: bool = False, expect_file: bool = False, expect_dir: bool = False) -> Path:
    return resolve_repo_path(root, candidate, must_exist=must_exist, expect_file=expect_file, expect_dir=expect_dir)


def _repo_relative(path: Path, *, root: Path = ROOT) -> Path:
    return path.resolve().relative_to(root.resolve())


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def strict_json_loads(text: str) -> Any:
    """Decode JSON while rejecting duplicate keys in every nested object."""

    return json.loads(text, object_pairs_hook=_strict_object)


def read_json(path: str | Path, *, root: Path = ROOT) -> Any:
    resolved = _safe(path, root=root, must_exist=True, expect_file=True)
    return strict_json_loads(resolved.read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash a path already resolved through the custody helper."""
    return sha256_bytes(path.read_bytes())


def hash_repo_file(path: str | Path, *, root: Path = ROOT) -> str:
    return sha256_file(_safe(path, root=root, must_exist=True, expect_file=True))


def canonical_sha256(value: Any) -> str:
    return sha256_bytes((json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8"))


def rel(path: Path, *, root: Path = ROOT) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _schema_subcode(keyword: str) -> str:
    return {
        "required": "required-field",
        "additionalProperties": "additional-property",
        "uniqueItems": "unique-items",
    }.get(keyword, f"schema-{keyword.lower()}")


def schema_findings(document: Any, schema_path: str | Path, *, root: Path = ROOT) -> list[Finding]:
    try:
        schema = read_json(schema_path, root=root)
        issues = validate_schema_subset(document, schema)
    except (PathCustodyError, SchemaDefinitionError, json.JSONDecodeError, OSError, ValueError) as exc:
        return [Finding("schema_definition", str(exc), "schema-definition")]
    return [Finding("schema_contract", f"{issue.path}: [{issue.keyword}] {issue.message}", _schema_subcode(issue.keyword)) for issue in issues]


def load_registry(path: str | Path = REGISTRY_REL, *, root: Path = ROOT) -> dict[str, Any]:
    value = read_json(path, root=root)
    if not isinstance(value, dict):
        raise ValueError("validation registry root must be an object")
    problems = schema_findings(value, REGISTRY_SCHEMA_REL, root=root)
    if problems:
        raise ValueError(problems[0].message)
    return value


def snapshot_registry(path: str | Path = REGISTRY_REL, *, root: Path = ROOT) -> RegistrySnapshot:
    """Read, hash, parse, and semantically validate one frozen registry byte object."""

    resolved = _safe(path, root=root, must_exist=True, expect_file=True)
    data = resolved.read_bytes()
    try:
        value = strict_json_loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"validation registry is not canonical UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("validation registry root must be an object")
    findings = validate_registry(value, root=root, scan_repo=False)
    if findings:
        first = findings[0]
        raise ValueError(
            "validation registry rejected "
            f"[{first.failure_class}/{first.failure_subcode}] {first.message}"
        )
    return RegistrySnapshot(
        relative_path=resolved.relative_to(root.resolve()).as_posix(),
        canonical_path=resolved,
        data=data,
        sha256=sha256_bytes(data),
        value=value,
    )


def registry_hash(path: str | Path = REGISTRY_REL, *, root: Path = ROOT) -> str:
    return hash_repo_file(path, root=root)


def _unique_index(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if value in result:
            raise ValueError(f"duplicate {key}: {value}")
        result[value] = row
    return result


def checker_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _unique_index((row for row in registry.get("checkers", []) if isinstance(row, dict)), "checker_id")


def profile_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _unique_index((row for row in registry.get("profiles", []) if isinstance(row, dict)), "profile_id")


def diagnostic_adapter_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _unique_index(
        (row for row in registry.get("diagnostic_adapters", []) if isinstance(row, dict)),
        "adapter_id",
    )


def profile_invocations(
    registry: dict[str, Any],
    profile_id: str,
    *,
    bindings: dict[str, str] | None = None,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    """Project one profile's ordered invocations with canonical checker identity.

    Registry arguments are argv templates, never shell fragments.  The only
    current placeholder is ``{output}``; callers may request an unresolved
    projection by omitting ``bindings``.
    """

    registry_findings = validate_registry(registry, root=root, scan_repo=False)
    if registry_findings:
        first = registry_findings[0]
        raise ValueError(
            "validation registry rejected "
            f"[{first.failure_class}/{first.failure_subcode}] {first.message}"
        )
    profile = profile_map(registry).get(profile_id)
    if profile is None:
        raise ValueError(f"unknown validation profile {profile_id}")
    checkers = checker_map(registry)
    projected: list[dict[str, Any]] = []
    formatter = string.Formatter()
    for raw in profile.get("invocations", []):
        row = copy.deepcopy(raw)
        arguments: list[str] = []
        for template in row.get("arguments", []):
            fields = [field for _literal, field, _spec, _conversion in formatter.parse(template) if field]
            unknown = sorted(set(fields) - {"output"})
            if unknown:
                raise ValueError(f"{profile_id}/{row.get('result_key')}: unknown argument placeholder(s) {unknown}")
            if bindings is None:
                arguments.append(template)
                continue
            missing = sorted(set(fields) - set(bindings))
            if missing:
                raise ValueError(f"{profile_id}/{row.get('result_key')}: missing argument binding(s) {missing}")
            arguments.append(template.format_map(bindings))
        row["arguments"] = arguments
        if row.get("invocation_kind") == "checker":
            checker_id = str(row.get("checker_id") or "")
            checker = checkers.get(checker_id)
            if checker is None:
                raise ValueError(f"{profile_id}/{row.get('result_key')}: unknown checker {checker_id}")
            source = _safe(checker["source_path"], root=root, must_exist=True, expect_file=True)
            if sha256_file(source) != checker["source_sha256"]:
                raise ValueError(f"{profile_id}/{row.get('result_key')}: checker source hash drift for {checker_id}")
            row["source_path"] = str(checker["source_path"])
            row["source_sha256"] = str(checker["source_sha256"])
            row["runtime_resources"] = [
                str(value) for value in checker.get("runtime_resources", [])
            ]
        projected.append(row)
    return projected


def discover_output_tools(root: Path = ROOT) -> set[str]:
    found: set[str] = set()
    for path in sorted((root / "tools").glob("check_*.py")):
        resolved = _safe(path.relative_to(root), root=root, must_exist=True, expect_file=True)
        text = resolved.read_text(encoding="utf-8", errors="replace")
        if "--outputs" in text:
            found.add(path.relative_to(root).as_posix())
    return found


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _literal_string(node.left)
        right = _literal_string(node.right)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                return None
            parts.append(value.value)
        return "".join(parts)
    return None


def _parse_python_source(text: str, path: Path) -> ast.AST | None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            warnings.simplefilter("ignore", SyntaxWarning)
            return ast.parse(text, filename=str(path))
    except SyntaxError:
        return None


def _strings_in(node: ast.AST) -> list[str]:
    literal = _literal_string(node)
    if literal is not None:
        return [literal]
    values: list[str] = []
    for child in ast.iter_child_nodes(node):
        values.extend(_strings_in(child))
    return values


def _known_checker_names(registry: dict[str, Any] | None) -> dict[str, str]:
    known: dict[str, str] = {}
    if registry is None:
        return known
    for checker in registry.get("checkers", []):
        if not isinstance(checker, dict):
            continue
        checker_id = str(checker.get("checker_id", ""))
        candidates = [
            checker.get("checker_id", ""),
            Path(str(checker.get("source_path", ""))).stem,
            *checker.get("aliases", []),
            *checker.get("deprecated_aliases", []),
        ]
        for value in candidates:
            if value:
                known[str(value).strip().lower().replace("-", "_")] = checker_id
    return known


def _checker_identity(value: str, known: dict[str, str]) -> str | None:
    candidate = value.strip().replace("\\", "/")
    if not candidate or any(character.isspace() for character in candidate):
        return None
    leaf = candidate.rsplit("/", 1)[-1]
    if leaf.lower().endswith(".py"):
        leaf = leaf[:-3]
    normalized = leaf.lower().replace("-", "_")
    return known.get(normalized)


def _checker_identities(node: ast.AST, known: dict[str, str]) -> set[str]:
    return {
        identity
        for value in _strings_in(node)
        if (identity := _checker_identity(value, known)) is not None
    }


def _resolved_checker_identities(
    node: ast.AST | None,
    known: dict[str, str],
    buckets: dict[str, set[str]],
) -> set[str]:
    if node is None:
        return set()
    if isinstance(node, ast.Name):
        return set(buckets.get(node.id, set()))
    literal = _literal_string(node)
    if literal is not None:
        identity = _checker_identity(literal, known)
        return {identity} if identity is not None else set()
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _resolved_checker_identities(node.left, known, buckets) | _resolved_checker_identities(
            node.right, known, buckets
        )
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return set().union(
            *(_resolved_checker_identities(child, known, buckets) for child in node.elts)
        )
    if isinstance(node, ast.Dict):
        return set().union(
            *(
                _resolved_checker_identities(child, known, buckets)
                for child in [*node.keys, *node.values]
                if child is not None
            )
        )
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "tuple", "set", "enumerate"}
    ):
        return set().union(
            *(_resolved_checker_identities(child, known, buckets) for child in node.args)
        )
    if isinstance(node, ast.Subscript):
        return _resolved_checker_identities(node.value, known, buckets)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "copy"
        and not node.args
    ):
        return _resolved_checker_identities(node.func.value, known, buckets)
    return set()


def _assignment_values(tree: ast.AST) -> dict[str, list[ast.AST]]:
    values: dict[str, list[ast.AST]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if node.value is None:
                continue
            for target in targets:
                if isinstance(target, ast.Name):
                    values.setdefault(target.id, []).append(node.value)
    return values


_PROCESS_METHODS = {"run", "Popen", "call", "check_call", "check_output"}


def _process_bindings(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Resolve bounded subprocess module/call aliases used by this source."""

    direct_names = {"run_process", "require_command_success"}
    module_names = {"subprocess"}
    assignments: list[tuple[str, ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    module_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                if alias.name in _PROCESS_METHODS:
                    direct_names.add(alias.asname or alias.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            assignments.extend(
                (target.id, node.value) for target in targets if isinstance(target, ast.Name)
            )

    for _pass in range(max(1, len(assignments))):
        changed = False
        for name, value in assignments:
            recognized = isinstance(value, ast.Name) and value.id in direct_names
            recognized = recognized or (
                isinstance(value, ast.Attribute)
                and value.attr in _PROCESS_METHODS
                and isinstance(value.value, ast.Name)
                and value.value.id in module_names
            )
            if recognized and name not in direct_names:
                direct_names.add(name)
                changed = True
        if not changed:
            break
    return direct_names, module_names


def _process_command(
    node: ast.Call,
    process_call_names: set[str],
    process_module_names: set[str],
) -> ast.AST | None:
    func = node.func
    process_call = (
        isinstance(func, ast.Attribute)
        and func.attr in _PROCESS_METHODS
        and isinstance(func.value, ast.Name)
        and func.value.id in process_module_names
    ) or (isinstance(func, ast.Name) and func.id in process_call_names)
    if not process_call:
        return None
    if node.args:
        return node.args[0]
    return next((keyword.value for keyword in node.keywords if keyword.arg == "args"), None)


def _resolve_simple_alias(
    node: ast.AST,
    assignments: dict[str, list[ast.AST]],
    seen: set[str] | None = None,
) -> ast.AST:
    seen = set() if seen is None else set(seen)
    if isinstance(node, ast.Name) and node.id in assignments and node.id not in seen:
        values = assignments[node.id]
        if len(values) != 1:
            return node
        seen.add(node.id)
        return _resolve_simple_alias(values[0], assignments, seen)
    return node


def _merge_string_fragments(
    fragments: Iterable[str | ast.AST],
    *,
    max_static_chars: int = MAX_STATIC_FORMATTED_FRAGMENT_CHARS,
) -> tuple[str | ast.AST, ...]:
    max_static_chars = max(0, min(max_static_chars, MAX_STATIC_FORMATTED_FRAGMENT_CHARS))
    merged: list[str | ast.AST] = []
    pending: list[str] = []
    static_chars = 0

    def flush_pending() -> None:
        if not pending:
            return
        merged.append(pending[0] if len(pending) == 1 else "".join(pending))
        pending.clear()

    for fragment in fragments:
        if isinstance(fragment, str):
            if not fragment:
                continue
            if len(fragment) > max_static_chars - static_chars:
                flush_pending()
                merged.append(ast.Constant(fragment))
                static_chars = max_static_chars
                continue
            pending.append(fragment)
            static_chars += len(fragment)
        else:
            flush_pending()
            merged.append(fragment)
    flush_pending()
    return tuple(merged)


def _format_static_string(
    value: str,
    conversion: int,
    format_spec: str,
    *,
    max_chars: int = MAX_STATIC_FORMATTED_FRAGMENT_CHARS,
) -> str | None:
    max_chars = max(0, min(max_chars, MAX_STATIC_FORMATTED_FRAGMENT_CHARS))
    if max_chars == 0:
        return None
    if conversion not in {-1, ord("s"), ord("r"), ord("a")}:
        return None
    bound = str(max_chars)
    for match in re.finditer(r"[0-9]+", format_spec):
        digits = match.group(0).lstrip("0") or "0"
        if len(digits) > len(bound) or len(digits) == len(bound) and digits > bound:
            return None
    source_limit = max_chars
    if conversion in {ord("r"), ord("a")}:
        source_limit = max(0, (max_chars - 2) // 10)
    if len(value) > source_limit:
        return None
    try:
        if conversion == ord("s"):
            converted = str(value)
        elif conversion == ord("r"):
            converted = repr(value)
        elif conversion == ord("a"):
            converted = ascii(value)
        else:
            converted = value
        if len(converted) > max_chars:
            return None
        rendered = format(converted, format_spec)
    except (MemoryError, OverflowError, TypeError, ValueError):
        return None
    return rendered if len(rendered) <= max_chars else None


def _string_concatenation_fragments(
    node: ast.AST,
    assignments: dict[str, list[ast.AST]],
    seen: set[str] | None = None,
    *,
    allow_dynamic_leaf: bool = False,
    max_static_chars: int = MAX_STATIC_FORMATTED_FRAGMENT_CHARS,
    remaining_depth: int = MAX_STATIC_FRAGMENT_AST_DEPTH,
) -> tuple[str | ast.AST, ...] | None:
    """Resolve the bounded concatenation forms whose leading bytes are knowable."""

    seen = set() if seen is None else set(seen)
    if remaining_depth <= 0:
        return (node,) if allow_dynamic_leaf else None
    max_static_chars = max(0, min(max_static_chars, MAX_STATIC_FORMATTED_FRAGMENT_CHARS))
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _merge_string_fragments((node.value,), max_static_chars=max_static_chars)
    if isinstance(node, ast.Name) and node.id in assignments and node.id not in seen:
        values = assignments[node.id]
        if len(values) == 1:
            seen.add(node.id)
            return _string_concatenation_fragments(
                values[0],
                assignments,
                seen,
                allow_dynamic_leaf=allow_dynamic_leaf,
                max_static_chars=max_static_chars,
                remaining_depth=remaining_depth - 1,
            )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _string_concatenation_fragments(
            node.left,
            assignments,
            seen,
            allow_dynamic_leaf=True,
            max_static_chars=max_static_chars,
            remaining_depth=remaining_depth - 1,
        )
        left_static_chars = sum(
            len(fragment) for fragment in left or () if isinstance(fragment, str)
        )
        left_exhausted = any(
            isinstance(fragment, ast.Constant) and isinstance(fragment.value, str)
            for fragment in left or ()
        )
        remaining = 0 if left_exhausted else max_static_chars - left_static_chars
        right = _string_concatenation_fragments(
            node.right,
            assignments,
            seen,
            allow_dynamic_leaf=True,
            max_static_chars=remaining,
            remaining_depth=remaining_depth - 1,
        )
        if left is not None and right is not None:
            return _merge_string_fragments(
                (*left, *right), max_static_chars=max_static_chars
            )
    if isinstance(node, ast.JoinedStr):
        fragments: list[str | ast.AST] = []
        remaining = max_static_chars
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                bounded = _merge_string_fragments(
                    (value.value,), max_static_chars=remaining
                )
                fragments.extend(bounded)
                if any(
                    isinstance(fragment, ast.Constant) and isinstance(fragment.value, str)
                    for fragment in bounded
                ):
                    remaining = 0
                else:
                    remaining -= sum(
                        len(fragment) for fragment in bounded if isinstance(fragment, str)
                    )
                continue
            if isinstance(value, ast.FormattedValue):
                resolved = _string_concatenation_fragments(
                    value.value,
                    assignments,
                    seen,
                    allow_dynamic_leaf=True,
                    max_static_chars=remaining,
                    remaining_depth=remaining_depth - 1,
                )
                resolved_static_chars = sum(
                    len(fragment) for fragment in resolved or () if isinstance(fragment, str)
                )
                resolved_exhausted = any(
                    isinstance(fragment, ast.Constant) and isinstance(fragment.value, str)
                    for fragment in resolved or ()
                )
                remaining = (
                    0 if resolved_exhausted else remaining - resolved_static_chars
                )
                format_spec = ""
                if value.format_spec is not None:
                    spec_fragments = _string_concatenation_fragments(
                        value.format_spec,
                        assignments,
                        seen,
                        max_static_chars=remaining,
                        remaining_depth=remaining_depth - 1,
                    )
                    spec_static_chars = sum(
                        len(fragment)
                        for fragment in spec_fragments or ()
                        if isinstance(fragment, str)
                    )
                    spec_exhausted = any(
                        isinstance(fragment, ast.Constant) and isinstance(fragment.value, str)
                        for fragment in spec_fragments or ()
                    )
                    remaining = (
                        0 if spec_exhausted else remaining - spec_static_chars
                    )
                    if spec_fragments is None or any(
                        not isinstance(fragment, str) for fragment in spec_fragments
                    ):
                        fragments.append(value)
                        continue
                    format_spec = "".join(spec_fragments)
                if resolved is not None and all(
                    isinstance(fragment, str) for fragment in resolved
                ):
                    rendered = _format_static_string(
                        "".join(resolved),
                        value.conversion,
                        format_spec,
                        max_chars=remaining,
                    )
                    if rendered is not None:
                        fragments.append(rendered)
                        remaining -= len(rendered)
                        continue
                fragments.append(value)
                continue
            return (node,) if allow_dynamic_leaf else None
        return _merge_string_fragments(
            fragments, max_static_chars=max_static_chars
        )
    return (node,) if allow_dynamic_leaf else None


def _static_string_value(
    node: ast.AST,
    assignments: dict[str, list[ast.AST]],
) -> str | None:
    fragments = _string_concatenation_fragments(node, assignments)
    if fragments is None or any(not isinstance(fragment, str) for fragment in fragments):
        return None
    return "".join(fragments)


def _fragments_expression(fragments: tuple[str | ast.AST, ...]) -> ast.AST:
    nodes = [ast.Constant(fragment) if isinstance(fragment, str) else fragment for fragment in fragments]
    expression = nodes[0]
    for node in nodes[1:]:
        expression = ast.BinOp(expression, ast.Add(), node)
    return expression


def _python_launcher_kind(
    node: ast.AST,
    assignments: dict[str, list[ast.AST]],
) -> str:
    resolved = _resolve_simple_alias(node, assignments)
    if (
        isinstance(resolved, ast.Attribute)
        and resolved.attr == "executable"
        and isinstance(resolved.value, ast.Name)
        and resolved.value.id == "sys"
    ):
        return "python"
    literal = _static_string_value(node, assignments)
    if literal is None:
        return "unresolved"
    leaf = literal.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if leaf in {"py", "py.exe"}:
        return "py"
    if re.fullmatch(
        r"(?:pythonw?(?:\d+(?:\.\d+)*t?)?|pypy(?:\d+(?:\.\d+)*)?)(?:\.exe)?",
        leaf,
    ):
        return "python"
    return "non-python"


def _attached_option_payload(
    node: ast.AST,
    prefix: str,
    assignments: dict[str, list[ast.AST]],
) -> ast.AST | None:
    fragments = _string_concatenation_fragments(node, assignments)
    if not fragments or not isinstance(fragments[0], str):
        return None
    head, *remaining = fragments
    if not head.startswith(prefix):
        return None
    payload = _merge_string_fragments((head[len(prefix) :], *remaining))
    return _fragments_expression(payload) if payload else None


def _python_script_position(
    argv: list[ast.AST],
    launcher_kind: str,
    assignments: dict[str, list[ast.AST]],
) -> tuple[ast.AST | None, str, tuple[ast.AST, ...]]:
    flag_only = {
        "-B", "-d", "-E", "-i", "-I", "-P", "-q", "-R", "-s", "-S", "-u", "-v", "-x",
        "--debug", "--dont-write-bytecode", "--ignore-environment", "--inspect", "--isolated",
        "--no-site", "--no-user-site", "--optimize", "--quiet", "--safe-path", "--unbuffered",
        "--verbose",
    }
    terminal = {"-h", "--help", "-V", "--version"}
    consumes_value = {"-W", "-X", "--check-hash-based-pycs"}
    index = 1
    while index < len(argv):
        expression = argv[index]
        attached_command = _attached_option_payload(expression, "-c", assignments)
        if attached_command is not None:
            return None, "none", ()
        attached_module = _attached_option_payload(expression, "-m", assignments)
        if attached_module is not None:
            return attached_module, "module", ()
        token = _static_string_value(expression, assignments)
        if token is None:
            fragments = _string_concatenation_fragments(expression, assignments)
            if (
                fragments
                and isinstance(fragments[0], str)
                and not fragments[0].startswith("-")
            ):
                return expression, "script", ()
            return None, "none", tuple(argv[index:])
        if launcher_kind == "py" and (
            re.fullmatch(r"-\d+(?:\.\d+)*(?:-\d+)?", token)
            or re.fullmatch(r"-V:.+", token, flags=re.IGNORECASE)
        ):
            index += 1
            continue
        if launcher_kind == "py" and token in {"-0", "-0p", "--list", "--list-paths"}:
            return None, "none", ()
        if token == "--":
            return (argv[index + 1], "script", ()) if index + 1 < len(argv) else (None, "none", ())
        if token == "-c":
            return None, "none", ()
        if token == "-m":
            return (argv[index + 1], "module", ()) if index + 1 < len(argv) else (None, "none", ())
        if token == "-":
            return None, "none", ()
        if token in terminal:
            return None, "none", ()
        if token in consumes_value:
            if index + 1 >= len(argv):
                return None, "none", ()
            index += 2
            continue
        if (
            token in flag_only
            or re.fullmatch(r"-(?:b+|O+|q+|v+)", token)
            or (token.startswith("-W") and token != "-W")
            or (token.startswith("-X") and token != "-X")
            or token.startswith("--check-hash-based-pycs=")
        ):
            index += 1
            continue
        if token.startswith("-"):
            return None, "none", tuple(argv[index:])
        return expression, "script", ()
    return None, "none", ()


def _command_script_expression(
    node: ast.AST,
    assignments: dict[str, list[ast.AST]],
    seen: set[str] | None = None,
) -> tuple[ast.AST | None, str, tuple[ast.AST, ...]]:
    seen = set() if seen is None else set(seen)
    if isinstance(node, ast.Name) and node.id in assignments and node.id not in seen:
        seen.add(node.id)
        values = assignments[node.id]
        if len(values) == 1:
            return _command_script_expression(values[0], assignments, seen)
        return None, "none", (node,)
    if isinstance(node, (ast.List, ast.Tuple)):
        if not node.elts:
            return None, "none", ()
        launcher_kind = _python_launcher_kind(node.elts[0], assignments)
        if launcher_kind in {"python", "py"}:
            return _python_script_position(list(node.elts), launcher_kind, assignments)
        if launcher_kind == "non-python":
            return None, "none", ()
        return None, "none", tuple(node.elts)
    return node, "script", ()


def _module_checker_identity(value: str, known: dict[str, str]) -> str | None:
    candidate = value.strip().replace("\\", "/")
    if not candidate or any(character.isspace() for character in candidate):
        return None
    leaf = candidate.rsplit("/", 1)[-1]
    if leaf.lower().endswith(".py"):
        leaf = leaf[:-3]
    elif "." in leaf:
        leaf = leaf.rsplit(".", 1)[-1]
    return known.get(leaf.lower().replace("-", "_"))


def _identity_preserving_concatenation_child(
    node: ast.AST,
    assignments: dict[str, list[ast.AST]],
) -> ast.AST | None:
    fragments = _string_concatenation_fragments(node, assignments)
    if fragments is None or len(fragments) != 1 or isinstance(fragments[0], str):
        return None
    return fragments[0]


def _resolved_module_checker_identities(
    node: ast.AST | None,
    known: dict[str, str],
    buckets: dict[str, set[str]],
    assignments: dict[str, list[ast.AST]],
    seen: set[str] | None = None,
) -> set[str]:
    if node is None:
        return set()
    seen = set() if seen is None else set(seen)
    if isinstance(node, ast.Name):
        identities = set(buckets.get(node.id, set()))
        if node.id in assignments and node.id not in seen:
            seen.add(node.id)
            for value in assignments[node.id]:
                identities.update(
                    _resolved_module_checker_identities(value, known, buckets, assignments, seen)
                )
        return identities
    literal = _static_string_value(node, assignments)
    if literal is not None:
        identity = _module_checker_identity(literal, known)
        return {identity} if identity is not None else set()
    if isinstance(node, ast.Subscript):
        return _resolved_module_checker_identities(node.value, known, buckets, assignments, seen)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return set().union(
            *(
                _resolved_module_checker_identities(child, known, buckets, assignments, seen)
                for child in node.elts
            )
        )
    if (
        isinstance(node, ast.JoinedStr)
        or isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
    ):
        child = _identity_preserving_concatenation_child(node, assignments)
        return _resolved_module_checker_identities(
            child, known, buckets, assignments, seen
        )
    if isinstance(node, ast.FormattedValue):
        format_spec = "" if node.format_spec is None else _static_string_value(
            node.format_spec, assignments
        )
        if node.conversion not in {-1, ord("s")} or format_spec not in {"", "s"}:
            return set()
        return _resolved_module_checker_identities(
            node.value, known, buckets, assignments, seen
        )
    return set()


def _unresolved_module_checker_identities(
    node: ast.AST | None,
    known: dict[str, str],
    buckets: dict[str, set[str]],
    assignments: dict[str, list[ast.AST]],
    seen_nodes: set[int] | None = None,
    seen_names: set[str] | None = None,
) -> set[str]:
    """Inspect one unresolved Python argv candidate without normalizing it."""

    if node is None:
        return set()
    seen_nodes = set() if seen_nodes is None else seen_nodes
    seen_names = set() if seen_names is None else seen_names
    marker = id(node)
    if marker in seen_nodes:
        return set()
    seen_nodes.add(marker)
    if isinstance(node, ast.Name):
        identities = set(buckets.get(node.id, set()))
        if node.id in assignments and node.id not in seen_names:
            seen_names.add(node.id)
            for value in assignments[node.id]:
                identities.update(
                    _unresolved_module_checker_identities(
                        value,
                        known,
                        buckets,
                        assignments,
                        seen_nodes,
                        seen_names,
                    )
                )
        return identities
    literal = _literal_string(node)
    if literal is not None:
        identity = _module_checker_identity(literal, known)
        return {identity} if identity is not None else set()
    identities: set[str] = set()
    for child in ast.iter_child_nodes(node):
        identities.update(
            _unresolved_module_checker_identities(
                child,
                known,
                buckets,
                assignments,
                seen_nodes,
                seen_names,
            )
        )
    return identities


def _expression_is_collection_derived(
    node: ast.AST,
    buckets: dict[str, set[str]],
    assignments: dict[str, list[ast.AST]],
    dynamic_names: set[str],
    seen: set[str] | None = None,
) -> bool:
    seen = set() if seen is None else set(seen)
    if isinstance(node, ast.Name):
        if node.id in dynamic_names:
            return True
        if node.id in assignments and node.id not in seen:
            seen.add(node.id)
            return any(
                _expression_is_collection_derived(value, buckets, assignments, dynamic_names, seen)
                for value in assignments[node.id]
            )
        return False
    if isinstance(node, ast.Subscript):
        return bool(_resolved_checker_identities(node.value, {}, buckets))
    return any(
        isinstance(child, ast.Name) and child.id in dynamic_names
        for child in ast.walk(node)
    )


def _module_expression_is_collection_derived(
    node: ast.AST,
    known: dict[str, str],
    buckets: dict[str, set[str]],
    assignments: dict[str, list[ast.AST]],
    dynamic_names: set[str],
    seen: set[str] | None = None,
) -> bool:
    seen = set() if seen is None else set(seen)
    if isinstance(node, ast.Name):
        if node.id in dynamic_names:
            return True
        if node.id in assignments and node.id not in seen:
            seen.add(node.id)
            return any(
                _module_expression_is_collection_derived(
                    value, known, buckets, assignments, dynamic_names, seen
                )
                for value in assignments[node.id]
            )
        return False
    if isinstance(node, ast.Subscript):
        return bool(
            _resolved_module_checker_identities(node.value, known, buckets, assignments)
        )
    if isinstance(node, ast.FormattedValue):
        format_spec = "" if node.format_spec is None else _static_string_value(
            node.format_spec, assignments
        )
        if node.conversion not in {-1, ord("s")} or format_spec not in {"", "s"}:
            return False
        return _module_expression_is_collection_derived(
            node.value, known, buckets, assignments, dynamic_names, seen
        )
    if (
        isinstance(node, ast.JoinedStr)
        or isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
    ):
        child = _identity_preserving_concatenation_child(node, assignments)
        return child is not None and _module_expression_is_collection_derived(
            child, known, buckets, assignments, dynamic_names, seen
        )
    return False


def _unresolved_module_expression_is_collection_derived(
    node: ast.AST,
    known: dict[str, str],
    buckets: dict[str, set[str]],
    assignments: dict[str, list[ast.AST]],
    dynamic_names: set[str],
    seen: set[str] | None = None,
    memo: dict[tuple[Any, ...], bool] | None = None,
) -> bool:
    seen = set() if seen is None else set(seen)
    node_key: tuple[str, Any] = (
        ("name", node.id) if isinstance(node, ast.Name) else ("node", id(node))
    )
    cache_key = (node_key, frozenset(seen), frozenset(dynamic_names))
    if memo is not None and cache_key in memo:
        return memo[cache_key]
    if isinstance(node, ast.Name):
        if node.id in dynamic_names:
            result = True
        elif node.id in assignments and node.id not in seen:
            seen.add(node.id)
            result = any(
                _unresolved_module_expression_is_collection_derived(
                    value, known, buckets, assignments, dynamic_names, seen, memo
                )
                for value in assignments[node.id]
            )
        else:
            result = False
    elif isinstance(node, ast.Subscript):
        result = bool(
            _resolved_module_checker_identities(node.value, known, buckets, assignments)
        )
    else:
        result = any(
            _unresolved_module_expression_is_collection_derived(
                child, known, buckets, assignments, dynamic_names, seen, memo
            )
            for child in ast.iter_child_nodes(node)
        )
    if memo is not None:
        memo[cache_key] = result
    return result


def _expression_uses_dynamic_name(node: ast.AST, dynamic_names: set[str]) -> bool:
    return any(
        isinstance(child, ast.Name) and child.id in dynamic_names
        for child in ast.walk(node)
    )


def _call_executes_collection(
    call: ast.Call,
    known: dict[str, str],
    buckets: dict[str, set[str]],
    assignments: dict[str, list[ast.AST]],
    dynamic_names: set[str],
    process_call_names: set[str],
    process_module_names: set[str],
    module_derived_memo: dict[tuple[Any, ...], bool] | None = None,
) -> bool:
    command = _process_command(call, process_call_names, process_module_names)
    if command is None:
        return False
    script, script_kind, unresolved = _command_script_expression(command, assignments)
    if script is not None:
        if script_kind == "module":
            identities = _resolved_module_checker_identities(
                script, known, buckets, assignments
            )
            derived = _module_expression_is_collection_derived(
                script, known, buckets, assignments, dynamic_names
            )
        else:
            identities = _resolved_checker_identities(script, known, buckets)
            derived = _expression_is_collection_derived(
                script, buckets, assignments, dynamic_names
            )
        if derived and (identities or _expression_uses_dynamic_name(script, dynamic_names)):
            return True
    for candidate in unresolved:
        script_identities = _resolved_checker_identities(candidate, known, buckets)
        uses_dynamic_name = _expression_uses_dynamic_name(candidate, dynamic_names)
        script_derived = bool(script_identities or uses_dynamic_name) and _expression_is_collection_derived(
            candidate, buckets, assignments, dynamic_names
        )
        module_identities = _unresolved_module_checker_identities(
            candidate, known, buckets, assignments
        )
        module_derived = bool(module_identities or uses_dynamic_name) and (
            _unresolved_module_expression_is_collection_derived(
                candidate,
                known,
                buckets,
                assignments,
                dynamic_names,
                memo=module_derived_memo,
            )
        )
        if (
            script_derived
            and (script_identities or uses_dynamic_name)
        ) or (
            module_derived
            and (module_identities or uses_dynamic_name)
        ):
            return True
    return False


def _loop_executes_collection(
    node: ast.For,
    known: dict[str, str],
    buckets: dict[str, set[str]],
    assignments: dict[str, list[ast.AST]],
    process_call_names: set[str],
    process_module_names: set[str],
    module_derived_memo: dict[tuple[Any, ...], bool] | None = None,
) -> bool:
    if not (
        _resolved_checker_identities(node.iter, known, buckets)
        or _resolved_module_checker_identities(node.iter, known, buckets, assignments)
    ):
        return False
    target = node.target
    if (
        isinstance(node.iter, ast.Call)
        and isinstance(node.iter.func, ast.Name)
        and node.iter.func.id == "enumerate"
        and isinstance(target, (ast.Tuple, ast.List))
        and len(target.elts) >= 2
    ):
        target = target.elts[1]
    dynamic_names = {item.id for item in ast.walk(target) if isinstance(item, ast.Name)}
    if not dynamic_names:
        return False
    local_assignments = _assignment_values(node)
    merged_assignments = {name: list(values) for name, values in assignments.items()}
    for name, values in local_assignments.items():
        merged_assignments.setdefault(name, []).extend(values)
    for _pass in range(max(1, len(local_assignments))):
        before = set(dynamic_names)
        for name, values in local_assignments.items():
            if any(
                any(isinstance(child, ast.Name) and child.id in dynamic_names for child in ast.walk(value))
                for value in values
            ):
                dynamic_names.add(name)
        if before == dynamic_names:
            break
    return any(
        _call_executes_collection(
            call,
            known,
            buckets,
            merged_assignments,
            dynamic_names,
            process_call_names,
            process_module_names,
            module_derived_memo,
        )
        for call in (item for item in ast.walk(node) if isinstance(item, ast.Call))
    )


def _comprehension_executes_collection(
    node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
    known: dict[str, str],
    buckets: dict[str, set[str]],
    assignments: dict[str, list[ast.AST]],
    process_call_names: set[str],
    process_module_names: set[str],
    module_derived_memo: dict[tuple[Any, ...], bool] | None = None,
) -> bool:
    dynamic_names: set[str] = set()
    for generator in node.generators:
        iter_is_collection_derived = bool(
            _resolved_checker_identities(generator.iter, known, buckets)
            or _resolved_module_checker_identities(generator.iter, known, buckets, assignments)
            or _expression_is_collection_derived(
                generator.iter,
                buckets,
                assignments,
                dynamic_names,
            )
            or _module_expression_is_collection_derived(
                generator.iter,
                known,
                buckets,
                assignments,
                dynamic_names,
            )
        )
        if not iter_is_collection_derived:
            continue
        dynamic_names.update(
            item.id for item in ast.walk(generator.target) if isinstance(item, ast.Name)
        )
    if not dynamic_names:
        return False
    return any(
        _call_executes_collection(
            call,
            known,
            buckets,
            assignments,
            dynamic_names,
            process_call_names,
            process_module_names,
            module_derived_memo,
        )
        for call in (item for item in ast.walk(node) if isinstance(item, ast.Call))
    )


def _assembled_policy_detected(tree: ast.AST, known: dict[str, str]) -> bool:
    buckets: dict[str, set[str]] = {}
    nodes = list(ast.walk(tree))
    operations: list[tuple[tuple[str, ...], tuple[ast.AST, ...]]] = []
    for node in nodes:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = tuple(target.id for target in targets if isinstance(target, ast.Name))
            if names and node.value is not None:
                operations.append((names, (node.value,)))
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            operations.append(((node.target.id,), (node.value,)))
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr in {"append", "extend"}
        ):
            operations.append(((node.func.value.id,), tuple(node.args)))

    dependents: dict[str, set[int]] = defaultdict(set)
    for index, (_targets, values) in enumerate(operations):
        for value in values:
            for child in ast.walk(value):
                if isinstance(child, ast.Name):
                    dependents[child.id].add(index)
    pending = deque(range(len(operations)))
    queued = set(pending)
    while pending:
        index = pending.popleft()
        queued.discard(index)
        targets, values = operations[index]
        identities = set().union(
            *(_resolved_checker_identities(value, known, buckets) for value in values)
        ) if values else set()
        changed_names: list[str] = []
        for name in targets:
            before = set(buckets.get(name, set()))
            buckets.setdefault(name, set()).update(identities)
            if before != buckets[name]:
                changed_names.append(name)
        for name in changed_names:
            for dependent in dependents.get(name, set()):
                if dependent not in queued:
                    pending.append(dependent)
                    queued.add(dependent)
    declarative_policy_names = {"battery", "detectors", "validators", "checks_to_run", "selection", "policy"}
    if any(
        (
            name.lower() in declarative_policy_names
            or name.lower().endswith(("_battery", "_detectors", "_validators", "_projection"))
        )
        and len(identities) >= 2
        for name, identities in buckets.items()
    ):
        return True
    assignments = _assignment_values(tree)
    process_call_names, process_module_names = _process_bindings(tree)
    module_derived_memo: dict[tuple[Any, ...], bool] = {}
    for node in nodes:
        if isinstance(node, ast.For):
            identities = _resolved_checker_identities(node.iter, known, buckets)
            module_identities = _resolved_module_checker_identities(
                node.iter, known, buckets, assignments
            )
            if (identities or module_identities) and _loop_executes_collection(
                node,
                known,
                buckets,
                assignments,
                process_call_names,
                process_module_names,
                module_derived_memo,
            ):
                return True
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            if _comprehension_executes_collection(
                node,
                known,
                buckets,
                assignments,
                process_call_names,
                process_module_names,
                module_derived_memo,
            ):
                return True
    if any(
        _call_executes_collection(
            node,
            known,
            buckets,
            assignments,
            set(),
            process_call_names,
            process_module_names,
            module_derived_memo,
        )
        for node in nodes
        if isinstance(node, ast.Call)
    ):
        return True
    return False


def _source_has_private_policy(path: Path, registry: dict[str, Any] | None = None) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = _parse_python_source(text, path)
    except RecursionError:
        return True
    if tree is None:
        return False
    known = _known_checker_names(registry)
    try:
        return _assembled_policy_detected(tree, known)
    except RecursionError:
        return True


def _discoverable_profile_policy(tree: ast.AST, registry: dict[str, Any]) -> bool:
    try:
        return _assembled_policy_detected(tree, _known_checker_names(registry))
    except RecursionError:
        return True


def _uses_registry_projection(
    tree: ast.AST,
    expected_profile_id: str | None = None,
) -> bool:
    """Return whether source calls the canonical projection for the bound profile.

    Discovery callers may omit ``expected_profile_id``. Registered-consumer
    validation supplies it so importing the helper, calling a different profile,
    or merely mentioning the API cannot satisfy custody.
    """

    direct_names: set[str] = set()
    module_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "validation_registry":
            for alias in node.names:
                if alias.name == "profile_invocations":
                    direct_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "validation_registry":
                    module_names.add(alias.asname or alias.name)
    assignments = _assignment_values(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        is_projection_call = isinstance(node.func, ast.Name) and node.func.id in direct_names
        is_projection_call = is_projection_call or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "profile_invocations"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in module_names
        )
        if not is_projection_call:
            continue
        if expected_profile_id is None:
            return True
        profile_node = node.args[1] if len(node.args) >= 2 else next(
            (keyword.value for keyword in node.keywords if keyword.arg == "profile_id"),
            None,
        )
        if profile_node is not None and _static_string_value(profile_node, assignments) == expected_profile_id:
            return True
    return False


def _source_uses_profile_projection(path: Path, profile_id: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = _parse_python_source(text, path)
    except RecursionError:
        return False
    if tree is None:
        return False
    try:
        return _uses_registry_projection(tree, profile_id)
    except RecursionError:
        return False


def discover_validation_consumers(root: Path = ROOT, registry: dict[str, Any] | None = None) -> set[str]:
    found: set[str] = set()
    registered_checker_paths = {
        str(row.get("source_path"))
        for row in (registry or {}).get("checkers", [])
        if isinstance(row, dict)
    }
    for path in sorted((root / "tools").glob("*.py")):
        resolved = _safe(path.relative_to(root), root=root, must_exist=True, expect_file=True)
        relative = path.relative_to(root).as_posix()
        text = resolved.read_text(encoding="utf-8", errors="replace")
        legacy_list = bool(_LEGACY_PRIVATE_POLICY.search(text))
        release_validator_marker = _LEGACY_RELEASE_VALIDATOR_MARKER in text
        try:
            tree = _parse_python_source(text, resolved)
        except RecursionError:
            found.add(relative)
            continue
        registry_derived = tree is not None and _uses_registry_projection(tree)
        if legacy_list or (release_validator_marker and not registry_derived) or (
            registry is not None
            and relative not in registered_checker_paths
            and tree is not None
            and _discoverable_profile_policy(tree, registry)
        ):
            found.add(relative)
    return found


def _path_finding(exc: PathCustodyError, context: str) -> Finding:
    if exc.subcode in {"missing-path", "not-file"}:
        return Finding("nonexistent_checker_tool" if "checker" in context else "unregistered_consumer", f"{context}: {exc}", "missing-tool" if "checker" in context else "missing-consumer")
    return Finding("path_custody", f"{context}: {exc}", exc.subcode)


def validate_registry(registry: Any, *, root: Path = ROOT, scan_repo: bool = True) -> list[Finding]:
    schema_errors = schema_findings(registry, REGISTRY_SCHEMA_REL, root=root)
    if schema_errors:
        return schema_errors
    assert isinstance(registry, dict)
    findings: list[Finding] = []
    if tuple(registry["artifact_types"]) != ARTIFACT_TYPES:
        findings.append(Finding("artifact_type_contract", "artifact_types must be the canonical ordered eight", "artifact-types"))
    checkers = registry["checkers"]
    ids = [str(row["checker_id"]) for row in checkers]
    if len(ids) != len(set(ids)):
        return [Finding("duplicate_checker_id", "checker IDs must be unique", "checker-id")]
    aliases: dict[str, str] = {}
    deprecated: dict[str, str] = {}
    for row in checkers:
        checker_id = str(row["checker_id"])
        try:
            source = _safe(row["source_path"], root=root, must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            return [_path_finding(exc, f"checker {checker_id}")]
        if sha256_file(source) != row["source_sha256"]:
            findings.append(Finding("checker_source_hash_drift", f"{checker_id}: source hash drift for {row['source_path']}", "tool-hash-drift"))
        for resource in row.get("runtime_resources", []):
            try:
                _safe(resource, root=root, must_exist=True)
            except PathCustodyError as exc:
                findings.append(
                    Finding(
                        "checker_runtime_resource_invalid",
                        f"{checker_id}: runtime resource {resource}: {exc}",
                        "runtime-resource",
                    )
                )
        if not set(row["artifact_applicability"]).issubset(ARTIFACT_TYPES):
            findings.append(Finding("unknown_artifact_type", f"{checker_id}: unknown artifact applicability", "artifact-applicability"))
        for alias in row.get("aliases", []):
            if alias in aliases or alias in ids or alias in deprecated:
                return [Finding("duplicate_checker_alias", f"duplicate or colliding alias {alias}", "checker-alias")]
            aliases[str(alias)] = checker_id
        for alias in row.get("deprecated_aliases", []):
            if alias in deprecated or alias in aliases or alias in ids:
                return [Finding("duplicate_checker_alias", f"duplicate or colliding deprecated alias {alias}", "checker-alias")]
            deprecated[str(alias)] = checker_id
    by_id = checker_map(registry)
    adapter_ids: set[str] = set()
    adapter_checker_counts: dict[str, int] = {}
    for adapter in registry["diagnostic_adapters"]:
        adapter_id = str(adapter["adapter_id"])
        if adapter_id in adapter_ids:
            findings.append(Finding("duplicate_diagnostic_adapter", f"duplicate diagnostic adapter {adapter_id}", "diagnostic-adapter"))
        adapter_ids.add(adapter_id)
        checker_ids = [str(value) for value in adapter["checker_ids"]]
        if len(checker_ids) != 1:
            findings.append(
                Finding(
                    "diagnostic_adapter_not_checker_specific",
                    f"{adapter_id}: each structural diagnostic adapter must own exactly one checker",
                    "diagnostic-adapter",
                )
            )
        unknown = sorted(set(checker_ids) - set(by_id))
        if unknown:
            findings.append(Finding("unknown_checker_id", f"{adapter_id}: unknown checker(s) {unknown}", "unknown-checker"))
        for checker_id in checker_ids:
            adapter_checker_counts[checker_id] = adapter_checker_counts.get(checker_id, 0) + 1
    profiles = registry["profiles"]
    pids = [str(row["profile_id"]) for row in profiles]
    if len(pids) != len(set(pids)):
        return [Finding("duplicate_profile_id", "profile IDs must be unique", "profile-id")]
    if tuple(pids) != PROFILE_IDS:
        findings.append(Finding("profile_contract", "profiles must be the canonical ordered six", "profiles"))
    consumer_profile_ids = {
        str(row["profile_id"])
        for row in registry["consumers"]
        if isinstance(row, dict)
    }
    required_output_checker_ids = {
        str(row["checker_id"])
        for row in checkers
        if row["requirement_status"] == "required" and "output-md" in row["artifact_applicability"]
    }
    for profile in profiles:
        pid = str(profile["profile_id"])
        requirement_ids = [str(row["checker_id"]) for row in profile["requirements"]]
        required_requirement_ids = {
            str(row["checker_id"])
            for row in profile["requirements"]
            if row["required"]
        }
        executable_consumer_profile = (
            pid in consumer_profile_ids
            and profile["missing_prerequisite_behavior"] not in {"projection-only", "advisory-only"}
        )
        if len(requirement_ids) != len(set(requirement_ids)):
            findings.append(Finding("duplicate_profile_requirement", f"{pid}: checker requirement IDs must be unique", "profile-requirement"))
        if not set(profile["artifact_types"]).issubset(ARTIFACT_TYPES):
            findings.append(Finding("unknown_artifact_type", f"{pid}: unknown profile artifact type", "artifact-applicability"))
        for requirement in profile["requirements"]:
            cid = str(requirement["checker_id"])
            if cid in deprecated:
                findings.append(Finding("deprecated_checker_alias", f"{pid}: deprecated checker alias {cid}", "deprecated-alias"))
            elif cid not in by_id:
                findings.append(Finding("unknown_checker_id", f"{pid}: unknown checker {cid}", "unknown-checker"))
            elif requirement["required"] and by_id[cid]["requirement_status"] == "inapplicable":
                findings.append(Finding("profile_required_not_run", f"{pid}: required checker {cid} is inapplicable", "required-not-run"))
            elif (
                requirement["required"]
                and (executable_consumer_profile or bool(profile["invocations"]))
                and not (
                set(by_id[cid]["artifact_applicability"]) & set(profile["artifact_types"])
                )
            ):
                findings.append(Finding("profile_invocation_inapplicable", f"{pid}: required checker {cid} is not applicable to the profile artifact types", "artifact-applicability"))
        if executable_consumer_profile and "output-md" in profile["artifact_types"]:
            missing_output_requirements = sorted(required_output_checker_ids - required_requirement_ids)
            if missing_output_requirements:
                findings.append(
                    Finding(
                        "profile_required_not_run",
                        f"{pid}: required output checker requirement(s) missing {missing_output_requirements}",
                        "required-not-run",
                    )
                )
            missing_adapter_checkers = sorted(
                checker_id
                for checker_id in required_requirement_ids
                if adapter_checker_counts.get(checker_id, 0) == 0
            )
            if missing_adapter_checkers:
                findings.append(
                    Finding(
                        "missing_diagnostic_adapter",
                        f"{pid}: checker(s) lack a registered structural diagnostic adapter {missing_adapter_checkers}",
                        "diagnostic-adapter",
                    )
                )
            duplicate_adapter_checkers = sorted(
                checker_id
                for checker_id in required_requirement_ids
                if adapter_checker_counts.get(checker_id, 0) > 1
            )
            if duplicate_adapter_checkers:
                findings.append(
                    Finding(
                        "duplicate_diagnostic_adapter_coverage",
                        f"{pid}: checker(s) have ambiguous structural diagnostic adapters {duplicate_adapter_checkers}",
                        "diagnostic-adapter",
                    )
                )
        invocations = profile["invocations"]
        if executable_consumer_profile and not invocations:
            findings.append(
                Finding(
                    "profile_required_not_run",
                    f"{pid}: consumer-bound executable profile must have an exact non-empty invocation plan",
                    "required-not-run",
                )
            )
        result_keys = [str(row["result_key"]) for row in invocations]
        if len(result_keys) != len(set(result_keys)):
            findings.append(Finding("duplicate_profile_invocation", f"{pid}: invocation result keys must be unique", "profile-invocation"))
        invoked_checkers: list[str] = []
        formatter = string.Formatter()
        for invocation in invocations:
            result_key = str(invocation["result_key"])
            kind = str(invocation["invocation_kind"])
            checker_id = invocation.get("checker_id")
            adapter_id = invocation.get("adapter_id")
            if kind == "checker":
                if not isinstance(checker_id, str) or adapter_id is not None:
                    findings.append(Finding("profile_invocation_contract", f"{pid}/{result_key}: checker invocation requires checker_id and null adapter_id", "profile-invocation"))
                elif checker_id not in by_id:
                    findings.append(Finding("unknown_checker_id", f"{pid}/{result_key}: unknown checker {checker_id}", "unknown-checker"))
                elif checker_id not in required_requirement_ids:
                    findings.append(Finding("profile_invocation_unrequired", f"{pid}/{result_key}: invoked checker {checker_id} is not a required profile checker", "profile-invocation"))
                elif not (
                    set(by_id[checker_id]["artifact_applicability"])
                    & set(profile["artifact_types"])
                ):
                    findings.append(Finding("profile_invocation_inapplicable", f"{pid}/{result_key}: invoked checker {checker_id} is not applicable to the profile artifact types", "artifact-applicability"))
                else:
                    invoked_checkers.append(checker_id)
            elif kind == "in-process-adapter":
                if checker_id is not None or not isinstance(adapter_id, str) or not adapter_id:
                    findings.append(Finding("profile_invocation_contract", f"{pid}/{result_key}: adapter invocation requires adapter_id and null checker_id", "profile-invocation"))
            for argument in invocation["arguments"]:
                try:
                    fields = [field for _literal, field, _spec, _conversion in formatter.parse(argument) if field]
                except ValueError as exc:
                    findings.append(Finding("profile_invocation_argument", f"{pid}/{result_key}: malformed argument template: {exc}", "profile-argument"))
                    continue
                unknown_fields = sorted(set(fields) - {"output"})
                if unknown_fields:
                    findings.append(Finding("profile_invocation_argument", f"{pid}/{result_key}: unknown argument placeholders {unknown_fields}", "profile-argument"))
        if len(invoked_checkers) != len(set(invoked_checkers)):
            findings.append(Finding("duplicate_profile_invocation", f"{pid}: checker invocations must be unique", "profile-invocation"))
        if invocations or executable_consumer_profile:
            missing_required = sorted(
                checker_id
                for checker_id in required_requirement_ids
                if checker_id not in invoked_checkers
            )
            if missing_required:
                findings.append(Finding("profile_required_not_run", f"{pid}: required invocation(s) missing {missing_required}", "required-not-run"))
    consumers = registry["consumers"]
    consumer_ids = [str(row["consumer_id"]) for row in consumers]
    if len(consumer_ids) != len(set(consumer_ids)):
        return [Finding("duplicate_consumer_id", "consumer IDs must be unique", "consumer-id")]
    for consumer in consumers:
        try:
            _safe(consumer["source_path"], root=root, must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            finding = _path_finding(exc, f"consumer {consumer['consumer_id']}")
            if finding.failure_class == "nonexistent_checker_tool":
                finding = Finding("unregistered_consumer", finding.message, "missing-consumer")
            return [finding]
    actual_consumer_contract = {
        str(row["consumer_id"]): (
            str(row["source_path"]),
            str(row["profile_id"]),
            str(row["policy_source"]),
        )
        for row in consumers
    }
    if actual_consumer_contract != REQUIRED_CONSUMER_CONTRACT:
        return [
            Finding(
                "consumer_set_mismatch",
                "consumers must exactly match the canonical Stage07, candidate, and scorecard tuples",
                "consumer-set",
            )
        ]
    registered_consumer_paths: set[str] = set()
    resolved_consumer_paths: set[str] = set()
    for consumer in consumers:
        try:
            path = _safe(consumer["source_path"], root=root, must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            finding = _path_finding(exc, f"consumer {consumer['consumer_id']}")
            if finding.failure_class == "nonexistent_checker_tool":
                finding = Finding("unregistered_consumer", finding.message, "missing-consumer")
            return [finding]
        registered_consumer_paths.add(str(consumer["source_path"]))
        resolved_key = str(path.resolve()).casefold()
        if resolved_key in resolved_consumer_paths:
            findings.append(
                Finding(
                    "duplicate_consumer_source",
                    f"{consumer['consumer_id']}: consumer source path is already registered: {consumer['source_path']}",
                    "consumer-source",
                )
            )
        resolved_consumer_paths.add(resolved_key)
        if consumer["profile_id"] not in pids:
            findings.append(Finding("unknown_profile", f"{consumer['consumer_id']}: unknown profile {consumer['profile_id']}", "unknown-profile"))
        if sha256_file(path) != consumer["source_sha256"]:
            findings.append(
                Finding(
                    "consumer_source_hash_drift",
                    f"{consumer['consumer_id']}: source hash drift for {consumer['source_path']}",
                    "consumer-source-hash",
                )
            )
        if not _source_uses_profile_projection(path, str(consumer["profile_id"])):
            findings.append(
                Finding(
                    "consumer_profile_projection_missing",
                    f"{consumer['consumer_id']}: source does not call profile_invocations for bound profile {consumer['profile_id']}",
                    "consumer-profile-projection",
                )
            )
        if consumer["policy_source"] != "registry" or (scan_repo and _source_has_private_policy(path, registry)):
            findings.append(Finding("private_consumer_battery", f"{consumer['consumer_id']}: private checker policy remains in {consumer['source_path']}", "private-battery"))
    if scan_repo:
        registered_paths = {str(row["source_path"]) for row in checkers}
        for missing in sorted(discover_output_tools(root) - registered_paths):
            findings.append(Finding("unregistered_output_checker", f"output-capable checker is unregistered: {missing}", "unregistered-output-checker"))
        for missing in sorted(discover_validation_consumers(root, registry) - registered_consumer_paths):
            findings.append(Finding("unregistered_consumer", f"validation consumer is unregistered: {missing}", "unregistered-consumer"))
    return findings


def _result_tuple_finding(row: dict[str, Any]) -> Finding | None:
    cid = str(row["checker_id"])
    status, category = row["execution_status"], row["exit_category"]
    exit_code, diag = row["exit_code"], row["diagnostic"]
    flags = (row["timeout"], row["crash"], row["usage_error"], row["malformed_diagnostic"])
    expectation = row["expectation_status"]
    if category == "accepted":
        valid = status == "completed" and exit_code == 0 and not any(flags) and diag is None and expectation == "ACCEPTED"
        return None if valid else Finding("result_tuple_invalid", f"{cid}: accepted requires completed/exit-0/no flags/no diagnostic/ACCEPTED", "result-tuple")
    if category == "structural-rejection":
        valid = status == "completed" and exit_code == 1 and not any(flags) and isinstance(diag, dict) and expectation in {"REJECTED_EXPECTED", "REJECTED_WRONG_REASON"}
        return None if valid else Finding("malformed_diagnostic", f"{cid}: structural rejection requires completed/exit-1/exact diagnostic", "malformed-diagnostic")
    if category == "usage-error":
        valid = status == "completed" and exit_code == 2 and flags == (False, False, True, False) and diag is None and expectation == "INDETERMINATE"
        return None if valid else Finding("usage_error_not_rejection", f"{cid}: usage tuple is malformed", "usage-error")
    if category == "timeout":
        valid = status == "timeout" and exit_code is None and flags == (True, False, False, False) and diag is None and expectation == "INDETERMINATE"
        return None if valid else Finding("infrastructure_not_rejection", f"{cid}: timeout tuple is malformed", "timeout")
    if category == "crash":
        valid = status == "crashed" and isinstance(exit_code, int) and exit_code != 0 and flags == (False, True, False, False) and diag is None and expectation == "INDETERMINATE"
        return None if valid else Finding("infrastructure_not_rejection", f"{cid}: crash tuple is malformed", "crash")
    if category == "malformed-diagnostic":
        valid = status == "completed" and exit_code == 1 and flags == (False, False, False, True) and diag is None and expectation == "INDETERMINATE"
        return None if valid else Finding("malformed_diagnostic", f"{cid}: malformed-diagnostic tuple is invalid", "malformed-diagnostic")
    if category == "unavailable":
        valid = status == "unavailable" and exit_code is None and flags == (False, False, False, False) and diag is None and expectation == "INDETERMINATE"
        return None if valid else Finding("infrastructure_not_rejection", f"{cid}: unavailable tuple is malformed", "unavailable")
    if category == "not-run":
        return Finding("profile_required_not_run", f"{cid}: checker did not run", "required-not-run")
    return Finding("result_tuple_invalid", f"{cid}: unknown result tuple", "result-tuple")


def _aggregate_status(verdict: dict[str, Any], profile: dict[str, Any], results: list[dict[str, Any]]) -> str:
    by_id = {str(row["checker_id"]): row for row in results}
    required = [str(row["checker_id"]) for row in profile["requirements"] if row["required"]]
    if any(cid not in by_id or by_id[cid]["execution_status"] == "not-run" for cid in required):
        return "QUARANTINED_INCOMPLETE_EVIDENCE"
    if not results:
        return "NOT_RUN"
    fallback: str | None = None
    for row in results:
        category = str(row["exit_category"])
        if category == "accepted":
            continue
        if category == "structural-rejection":
            if row["expectation_status"] == "REJECTED_EXPECTED":
                return "FAIL_STRUCTURAL"
            fallback = "QUARANTINED_INCOMPLETE_EVIDENCE"
            continue
        if category in {"usage-error", "timeout", "crash", "malformed-diagnostic", "unavailable"}:
            return "INFRASTRUCTURE_ERROR"
        fallback = "QUARANTINED_INCOMPLETE_EVIDENCE"
    if fallback is not None:
        return fallback
    if all(by_id[cid]["exit_category"] == "accepted" for cid in required):
        return "PASS_STRUCTURAL"
    return "QUARANTINED_INCOMPLETE_EVIDENCE"


def _execution_snapshot_findings(
    verdict: dict[str, Any],
    registry: dict[str, Any],
    profile: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    root: Path,
    verify_files: bool,
) -> list[Finding]:
    snapshot = verdict.get("execution_snapshot")
    if verdict["selected_profile"] == "captured-output-structural" and not isinstance(snapshot, dict):
        return [
            Finding(
                "execution_snapshot_missing",
                "captured-output replay requires a complete checker execution snapshot",
                "execution-snapshot",
            )
        ]
    if snapshot is None:
        return []
    assert isinstance(snapshot, dict)
    files = snapshot["files"]
    if snapshot["file_count"] != len(files):
        return [Finding("execution_snapshot_count_mismatch", "execution snapshot file_count drifted", "execution-snapshot-count")]
    paths = [str(row["path"]) for row in files]
    if len(paths) != len(set(paths)):
        return [Finding("execution_snapshot_duplicate_path", "execution snapshot paths must be unique", "execution-snapshot-path")]
    if paths != sorted(paths):
        return [Finding("execution_snapshot_order_mismatch", "execution snapshot paths must use canonical sorted order", "execution-snapshot-order")]
    if snapshot["sha256"] != canonical_sha256(files):
        return [Finding("execution_snapshot_digest_mismatch", "execution snapshot manifest digest drifted", "execution-snapshot-digest")]
    try:
        plan = profile_invocations(registry, str(profile["profile_id"]), root=root)
        expected_sources = execution_snapshot_sources(root=root, plan=plan)
    except (OSError, ValueError, PathCustodyError) as exc:
        return [Finding("execution_snapshot_source_error", str(exc), "execution-snapshot-source")]
    expected_paths = set(expected_sources)
    observed_paths = set(paths)
    if observed_paths != expected_paths:
        missing = sorted(expected_paths - observed_paths)
        extra = sorted(observed_paths - expected_paths)
        return [
            Finding(
                "execution_snapshot_incomplete",
                f"execution snapshot path set drifted; missing={missing[:5]} extra={extra[:5]}",
                "execution-snapshot-path-set",
            )
        ]
    manifest_by_path = {str(row["path"]): row for row in files}
    for relative, source in expected_sources.items():
        row = manifest_by_path[relative]
        if verify_files:
            data = source.read_bytes()
            if row["bytes"] != len(data) or row["sha256"] != sha256_bytes(data):
                return [
                    Finding(
                        "execution_snapshot_file_drift",
                        f"execution snapshot identity drifted for {relative}",
                        "execution-snapshot-file",
                    )
                ]
    for result in results:
        tool_path = str(result["tool_path"])
        manifest_row = manifest_by_path.get(tool_path)
        if manifest_row is None or manifest_row["sha256"] != result["tool_sha256"]:
            return [
                Finding(
                    "execution_snapshot_checker_unbound",
                    f"checker result is not bound to execution snapshot: {tool_path}",
                    "execution-snapshot-checker",
                )
            ]
    return []


def validate_verdict(verdict: Any, registry: dict[str, Any], *, root: Path = ROOT, verify_files: bool = True) -> list[Finding]:
    schema_errors = schema_findings(verdict, VERDICT_SCHEMA_REL, root=root)
    if schema_errors:
        return schema_errors
    assert isinstance(verdict, dict)
    registry_errors = validate_registry(registry, root=root, scan_repo=False)
    if registry_errors:
        return registry_errors
    try:
        registry_path = _safe(verdict["registry_path"], root=root, must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        return [Finding("path_custody", f"registry_path: {exc}", "registry-path")]
    try:
        referenced_registry = strict_json_loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [Finding("malformed_registry", str(exc), "registry-json")]
    if referenced_registry != registry:
        return [Finding("registry_object_path_mismatch", "referenced registry bytes are not the registry object used for validation", "registry-object-split")]
    if verdict["registry_sha256"] != sha256_file(registry_path):
        return [Finding("registry_hash_drift", "verdict registry hash does not match referenced registry bytes", "registry-hash-drift")]
    profiles = profile_map(registry)
    profile = profiles.get(str(verdict["selected_profile"]))
    if not profile:
        return [Finding("unknown_profile", f"unknown selected profile {verdict['selected_profile']}", "unknown-profile")]
    artifacts = verdict["artifacts"]
    roles = [str(row["role"]) for row in artifacts]
    paths = [str(row["path"]) for row in artifacts]
    if len(roles) != len(set(roles)):
        return [Finding("duplicate_artifact_role", "artifact roles must be unique", "artifact-role")]
    if len(paths) != len(set(paths)):
        return [Finding("duplicate_artifact_path", "artifact paths must be unique", "artifact-path")]
    if roles.count("input") != 1 or roles.count("output") != 1:
        return [Finding("artifact_role_contract", "verdict requires exactly one input and one output artifact", "input-output-role")]
    for row in artifacts:
        if row["artifact_type"] not in ARTIFACT_TYPES:
            return [Finding("unknown_artifact_type", f"artifact {row['role']}: unknown type {row['artifact_type']}", "artifact-applicability")]
        try:
            path = _safe(row["path"], root=root, must_exist=verify_files, expect_file=verify_files)
        except PathCustodyError as exc:
            return [Finding("path_custody", f"artifact {row['role']}: {exc}", "artifact-path")]
        if verify_files and sha256_file(path) != row["sha256"]:
            failure_class = "verdict_output_hash_drift" if row["role"] == "output" else "artifact_hash_drift"
            return [Finding(failure_class, f"bound artifact drift: {row['path']}", "artifact-hash-drift")]
    results = verdict["checker_results"]
    result_ids = [str(row["checker_id"]) for row in results]
    if len(result_ids) != len(set(result_ids)):
        return [Finding("duplicate_checker_result", "checker-result IDs must be unique", "checker-result-id")]
    if verdict["selected_profile"] == "captured-output-structural":
        expected_result_ids = [
            str(requirement["checker_id"])
            for requirement in profile["requirements"]
            if requirement["required"]
        ]
        missing_result_ids = [checker_id for checker_id in expected_result_ids if checker_id not in result_ids]
        if missing_result_ids:
            return [
                Finding(
                    "profile_required_not_run",
                    f"required checker result(s) missing {missing_result_ids}",
                    "required-not-run",
                )
            ]
        if result_ids != expected_result_ids:
            return [
                Finding(
                    "profile_result_not_exact",
                    "captured-output checker results must exactly match required profile order",
                    "checker-result-profile",
                )
            ]
    snapshot_findings = _execution_snapshot_findings(
        verdict,
        registry,
        profile,
        results,
        root=root,
        verify_files=verify_files,
    )
    if snapshot_findings:
        return snapshot_findings
    cmap = checker_map(registry)
    adapters = diagnostic_adapter_map(registry)
    findings: list[Finding] = []
    for row in results:
        cid = str(row["checker_id"])
        checker = cmap.get(cid)
        if checker is None:
            return [Finding("unknown_checker_id", f"verdict references unknown checker {cid}", "unknown-checker")]
        try:
            tool_path = _safe(row["tool_path"], root=root, must_exist=True, expect_file=True)
        except PathCustodyError as exc:
            return [Finding("path_custody", f"checker result {cid}: {exc}", "checker-source-path")]
        if row["tool_path"] != checker["source_path"] or row["tool_sha256"] != checker["source_sha256"] or sha256_file(tool_path) != row["tool_sha256"]:
            return [Finding("checker_source_hash_drift", f"{cid}: verdict tool identity drift", "tool-hash-drift")]
        adapter_id = row.get("diagnostic_adapter_id")
        if row["exit_category"] == "structural-rejection":
            adapter = adapters.get(str(adapter_id)) if isinstance(adapter_id, str) else None
            if (
                verdict["selected_profile"] == "captured-output-structural"
                and (
                    adapter is None
                    or cid not in adapter["checker_ids"]
                    or not isinstance(row["diagnostic"], dict)
                    or any(
                        str(marker) not in str(row["diagnostic"].get("message", ""))
                        for marker in adapter["required_markers"]
                    )
                )
            ):
                return [Finding("malformed_diagnostic", f"{cid}: structural rejection lacks the registered diagnostic adapter", "diagnostic-adapter")]
        elif adapter_id is not None:
            return [Finding("result_tuple_invalid", f"{cid}: diagnostic adapter is allowed only for structural rejection", "diagnostic-adapter")]
        bound_rows = [
            artifact for artifact in artifacts
            if artifact["sha256"] == row["artifact_sha256"] and artifact["artifact_type"] == row["artifact_type"]
        ]
        if len(bound_rows) != 1:
            return [Finding("checker_artifact_hash_drift", f"{cid}: result artifact hash/type is not bound", "checker-artifact-hash")]
        bound = bound_rows[0]
        if row["artifact_type"] not in checker["artifact_applicability"]:
            return [Finding("checker_artifact_inapplicable", f"{cid}: artifact type {row['artifact_type']} is not applicable", "artifact-applicability")]
        if row["artifact_type"] not in profile["artifact_types"]:
            return [Finding("profile_artifact_inapplicable", f"{cid}: artifact type {row['artifact_type']} is outside profile {profile['profile_id']}", "profile-artifact")]
        tuple_finding = _result_tuple_finding(row)
        if tuple_finding is not None:
            findings.append(tuple_finding)
        if row["exit_category"] in {"accepted", "structural-rejection"} and row["exit_category"] not in checker["accepted_exit_categories"]:
            findings.append(Finding("exit_category_not_registered", f"{cid}: category {row['exit_category']} is not accepted by registry", "exit-category"))
        readback_paths = [str(item["path"]) for item in row["forbidden_artifact_readback"]]
        if len(readback_paths) != len(set(readback_paths)):
            return [Finding("duplicate_forbidden_readback_path", f"{cid}: forbidden readback paths must be unique", "forbidden-readback-path")]
        for item in row["forbidden_artifact_readback"]:
            try:
                path = _safe(item["path"], root=root, must_exist=False)
            except PathCustodyError as exc:
                return [Finding("path_custody", f"forbidden artifact {item['path']}: {exc}", "forbidden-artifact-path")]
            actual_exists = path.exists()
            if bool(item["exists"]) != actual_exists:
                return [Finding("forbidden_artifact_readback_mismatch", f"{cid}: recorded readback differs for {item['path']}", "forbidden-readback")]
            if actual_exists:
                return [Finding("forbidden_artifact_exists", f"{cid}: forbidden downstream artifact exists: {item['path']}", "forbidden-artifact")]
    if findings:
        return findings
    by_result = {str(row["checker_id"]): row for row in results}
    for requirement in profile["requirements"]:
        if requirement["required"] and (requirement["checker_id"] not in by_result or by_result[requirement["checker_id"]]["execution_status"] == "not-run"):
            return [Finding("profile_required_not_run", f"required checker {requirement['checker_id']} did not run", "required-not-run")]
    recomputed = _aggregate_status(verdict, profile, results)
    if verdict["aggregate_status"] != recomputed:
        return [Finding("aggregate_status_mismatch", f"declared {verdict['aggregate_status']} but recomputed {recomputed}", "aggregate-status")]
    rejections = [row for row in results if row["exit_category"] == "structural-rejection" and row["expectation_status"] == "REJECTED_EXPECTED"]
    if recomputed == "FAIL_STRUCTURAL":
        if verdict["mutation_fault_id"] is not None and (
            len(rejections) != 1
            or verdict["mutation_fault_id"] != rejections[0]["diagnostic"]["failure_subcode"]
        ):
            return [Finding("different_active_fault", "FAIL_STRUCTURAL mutation identity must equal the sole expected rejection subcode", "active-fault-mismatch")]
    elif verdict["mutation_fault_id"] is not None:
        return [Finding("mutation_fault_status_mismatch", "mutation_fault_id is allowed only for one expected structural rejection", "mutation-fault")]
    nonclaims = " ".join(verdict["structural_non_claims"]).lower()
    if not all(token in nonclaims for token in ("structural", "semantic", "model")):
        return [Finding("structural_non_claims_missing", "verdict must disclaim semantic and model proof", "non-claims")]
    return findings


def materialize_fixture(path: str | Path, *, root: Path = ROOT, _seen: set[str] | None = None) -> dict[str, Any]:
    resolved = _safe(path, root=root, must_exist=True, expect_file=True)
    relative = _repo_relative(resolved, root=root)
    seen = set() if _seen is None else set(_seen)
    key = relative.as_posix()
    if key in seen:
        raise ValueError(f"mutation base cycle at {key}")
    seen.add(key)
    raw = strict_json_loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("fixture_schema") != "daee-validation-integrity-mutation-v1":
        return raw
    base_value = raw.get("base")
    if not isinstance(base_value, str) or not base_value:
        raise ValueError("mutation base must be a non-empty relative path")
    try:
        base = _safe(relative.parent / Path(base_value), root=root, must_exist=True, expect_file=True)
    except PathCustodyError as exc:
        raise PathCustodyError(f"mutation base: {exc}", subcode="mutation-base") from exc
    value = copy.deepcopy(materialize_fixture(_repo_relative(base, root=root), root=root, _seen=seen))
    for operation in raw.get("operations", []):
        parts = [part.replace("~1", "/").replace("~0", "~") for part in str(operation["path"]).strip("/").split("/") if part]
        if not parts:
            raise ValueError("mutation operation path must not be empty")
        cursor: Any = value
        for part in parts[:-1]:
            cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
        key_part = parts[-1]
        if operation["op"] == "set":
            if isinstance(cursor, list):
                cursor[int(key_part)] = operation.get("value")
            else:
                cursor[key_part] = operation.get("value")
        elif operation["op"] == "delete":
            if isinstance(cursor, list):
                del cursor[int(key_part)]
            else:
                cursor.pop(key_part, None)
        else:
            raise ValueError(f"unsupported fixture operation {operation['op']}")
    return value


def hydrate_fixture(value: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    value = copy.deepcopy(value)
    registry_value = value.get("registry_path", REGISTRY_REL.as_posix())
    reg_path = _safe(registry_value, root=root, must_exist=True, expect_file=True)
    if value.get("registry_sha256") == "AUTO":
        value["registry_sha256"] = sha256_file(reg_path)
    for row in value.get("artifacts", []):
        path = _safe(row.get("path", ""), root=root, must_exist=True, expect_file=True)
        if row.get("sha256") == "AUTO":
            row["sha256"] = sha256_file(path)
    roles = [str(row.get("role")) for row in value.get("artifacts", [])]
    if len(roles) != len(set(roles)):
        raise ValueError("cannot hydrate duplicate artifact roles")
    artifact_map = {str(row["role"]): row for row in value.get("artifacts", [])}
    cmap = checker_map(load_registry(_repo_relative(reg_path, root=root), root=root))
    for row in value.get("checker_results", []):
        checker = cmap.get(str(row.get("checker_id")), {})
        if row.get("tool_sha256") == "AUTO":
            row["tool_sha256"] = checker.get("source_sha256", "0" * 64)
        if row.get("artifact_sha256") == "AUTO":
            row["artifact_sha256"] = artifact_map.get("output", {}).get("sha256", "0" * 64)
    return value


def scan_anti_bank(paths: Iterable[Path], *, root: Path = ROOT) -> list[str]:
    banned_terms = [
        "gate" + "88-", "expected" + "_answer", "expected" + "_topology",
        "maximum" + "_cycles", "maximum" + "_invocations", "fixed" + "_burden",
        "fixed" + "_submove", "fixed" + "_byte", "stop" + "-after-n",
    ]
    problems: list[str] = []
    for path in paths:
        resolved = _safe(path, root=root, must_exist=True, expect_file=True)
        text = resolved.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower().replace("-", "_").replace(" ", "_")
        match = next((term for term in banned_terms if term.replace("-", "_") in lowered), None)
        if match:
            problems.append(f"{rel(resolved, root=root)}: prohibited answer/quota policy token {match!r}")
    return problems


def _self_test() -> int:
    registry = load_registry()
    findings = validate_registry(registry, root=ROOT, scan_repo=False)
    if findings:
        for finding in findings:
            print(f"FAIL: [{finding.failure_class}/{finding.failure_subcode}] {finding.message}")
        return 1
    print(json.dumps({"artifact_types": len(ARTIFACT_TYPES), "checkers": len(registry["checkers"]), "profiles": len(registry["profiles"]), "status": "PASS"}, sort_keys=True))
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.error("only --self-test is supported; use check_validation_registry.py for validation")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
