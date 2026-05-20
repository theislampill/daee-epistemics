#!/usr/bin/env python3
"""Validate local release package provenance without network access."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


HASH_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$")
ROOT = Path(__file__).resolve().parents[1]


FIELD_ALIASES = {
    "package_sha256": ("package_sha256", "asset_sha256", "zip_sha256"),
    "package_size": ("package_size", "asset_size", "zip_size"),
    "entry_count": ("package_entry_count", "entry_count"),
    "build_manifest_sha256": (
        "build_manifest_sha256",
        "manifest_sha256",
        "build_manifest_hash",
    ),
    "compiled_module_map_sha256": (
        "compiled_module_map_sha256",
        "compiled_map_sha256",
        "compiled_module_map_hash",
    ),
}


def read_json(path: Path, errors: list[str]) -> dict[str, object]:
    if not path.exists():
        errors.append(f"provenance file is absent: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: provenance payload must be a JSON object")
        return {}
    return value


def sha256(path: Path, errors: list[str], label: str) -> str | None:
    if not path.exists():
        errors.append(f"{label} is absent: {path}")
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git_output(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def gh_json(args: list[str]) -> dict[str, object] | None:
    if shutil.which("gh") is None:
        return None
    try:
        text = subprocess.check_output(["gh", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def run_check(label: str, command: list[str]) -> list[str]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        return [f"{label}: command unavailable: {exc}"]
    if completed.returncode == 0:
        return []
    output = completed.stdout.strip()
    detail = f": {output}" if output else ""
    return [f"{label}: FAIL{detail}"]


def release_mojibake_paths(
    release_body: Path | None, manifest_out: Path | None, provenance_path: Path | None
) -> list[str]:
    paths = [
        "AGENTS.md",
        "README.md",
        "docs/package-smoke-readiness.md",
        "docs/release-artifacts.md",
        "docs/v0.4.3.0-release-log.md",
        "docs/v0.4.3.0-release-notes.md",
        "docs/audits",
        "docs/releases",
        "atomics/skill/references",
        "docs/index.html",
        "docs/daee-epistemics-pipeline.html",
    ]
    build_dir = ROOT / "build"
    if build_dir.exists():
        paths.extend(str(path.relative_to(ROOT)) for path in build_dir.glob("*release-body*.md"))
    for path in (release_body, manifest_out, provenance_path):
        if path is not None:
            paths.append(str(path))

    unique: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def run_mojibake_preflight(
    release_body: Path | None, manifest_out: Path | None, provenance_path: Path | None
) -> list[str]:
    command = [
        sys.executable,
        "tools/check_mojibake.py",
        *release_mojibake_paths(release_body, manifest_out, provenance_path),
    ]
    return run_check("release-facing mojibake scan", command)


def run_generated_surface_preflight() -> list[str]:
    errors: list[str] = []
    checks = [
        ("compiled runtime freshness", [sys.executable, "tools/check_compiled_runtime_freshness.py"]),
        ("docs index freshness", [sys.executable, "tools/build_docs_index.py", "--check"]),
        ("docs index interactions", [sys.executable, "tools/check_docs_index_interactions.py"]),
    ]
    for label, command in checks:
        errors.extend(run_check(label, command))
    return errors


def run_package_artifact_preflight(version: str, artifact: Path) -> list[str]:
    return run_check(
        "package artifact shape/leakage",
        [sys.executable, "tools/check_skill_package_artifact.py", str(artifact), "--expect-version", version],
    )


def provenance_field(
    payload: dict[str, object], canonical: str, errors: list[str], required: bool = True
) -> object | None:
    for name in FIELD_ALIASES.get(canonical, (canonical,)):
        if name in payload:
            return payload[name]
    if required:
        aliases = ", ".join(FIELD_ALIASES.get(canonical, (canonical,)))
        errors.append(f"provenance missing required field: {aliases}")
    return None


def normalize_hash(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    match = HASH_RE.search(value)
    return match.group(0).upper() if match else None


def normalize_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value.replace(",", ""))
        return int(match.group(0)) if match else None
    return None


def zip_entry_count(path: Path, errors: list[str]) -> int | None:
    if not path.exists():
        errors.append(f"package file is absent: {path}")
        return None
    try:
        with ZipFile(path) as zf:
            return len(zf.namelist())
    except BadZipFile:
        errors.append(f"package is not a readable .skill/.zip archive: {path}")
        return None


def clean_table_value(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_markdown_tables(path: Path, errors: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        errors.append(f"release artifacts document is absent: {path}")
        return []
    tables: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = TABLE_ROW_RE.match(line)
        if not match:
            if current:
                tables.append(current)
                current = {}
            continue
        key = clean_table_value(match.group(1)).lower()
        value = clean_table_value(match.group(2))
        if key in {"field", "---"} or set(key) <= {"-"}:
            continue
        current[key] = value
    if current:
        tables.append(current)
    return tables


def check_required_fields(payload: dict[str, object], errors: list[str]) -> None:
    for field in ("version", "contract_version", "source_commit"):
        if not payload.get(field):
            errors.append(f"provenance missing required field: {field}")
    if payload.get("raw_atomics_packaged") is not False:
        errors.append("provenance must record raw_atomics_packaged: false")
    if payload.get("forbidden_roots_absent") is not True:
        errors.append("provenance must record forbidden_roots_absent: true")
    for field in FIELD_ALIASES:
        provenance_field(payload, field, errors)


def compare_hash(label: str, actual: str | None, expected: object, errors: list[str]) -> None:
    if actual is None:
        return
    if expected is None:
        return
    expected_hash = normalize_hash(expected)
    if expected_hash is None:
        errors.append(f"provenance {label} is not a SHA256 hash")
        return
    if actual != expected_hash:
        errors.append(f"{label} mismatch: actual {actual}, provenance {expected_hash}")


def compare_int(label: str, actual: int | None, expected: object, errors: list[str]) -> None:
    if actual is None:
        return
    if expected is None:
        return
    expected_int = normalize_int(expected)
    if expected_int is None:
        errors.append(f"provenance {label} is not an integer")
        return
    if actual != expected_int:
        errors.append(f"{label} mismatch: actual {actual}, provenance {expected_int}")


def check_release_artifacts_doc(
    path: Path, package_path: Path, package_sha: str, payload: dict[str, object], errors: list[str]
) -> None:
    tables = parse_markdown_tables(path, errors)
    if not tables:
        return
    package_name = package_path.name
    alternate_name = package_name[:-4] if package_name.endswith(".zip") else f"{package_name}.zip"
    matching = [
        table for table in tables
        if table.get("package filename") in {package_name, alternate_name}
        or table.get("local zip build") in {package_name, alternate_name, str(package_path)}
    ]
    if not matching:
        print(f"release artifacts note: no table for {package_name}; contradiction check skipped")
        return
    table = matching[0]
    doc_sha = normalize_hash(table.get("sha256"))
    if doc_sha and doc_sha != package_sha:
        errors.append(f"{path}: SHA256 contradicts package/provenance: {doc_sha} != {package_sha}")
    doc_size = normalize_int(table.get("size"))
    package_size = normalize_int(provenance_field(payload, "package_size", errors, required=False))
    if doc_size is not None and package_size is not None and doc_size != package_size:
        errors.append(f"{path}: size contradicts provenance: {doc_size} != {package_size}")
    doc_entries = normalize_int(table.get("entries"))
    entry_count = normalize_int(provenance_field(payload, "entry_count", errors, required=False))
    if doc_entries is not None and entry_count is not None and doc_entries != entry_count:
        errors.append(f"{path}: entry count contradicts provenance: {doc_entries} != {entry_count}")
    doc_manifest = normalize_hash(table.get("generated runtime manifest sha256"))
    prov_manifest = normalize_hash(
        provenance_field(payload, "build_manifest_sha256", errors, required=False)
    )
    if doc_manifest and prov_manifest and doc_manifest != prov_manifest:
        errors.append(f"{path}: build-manifest SHA256 contradicts provenance")


def check_smoke_root(root: Path, package_sha: str, errors: list[str]) -> None:
    if not root.exists():
        errors.append(f"smoke root is absent: {root}")
        return
    found_hashes: set[str] = set()
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            found_hashes.update(match.group(0).upper() for match in HASH_RE.finditer(text))
    if not found_hashes:
        errors.append(f"{root}: no package SHA256 evidence found")
    elif package_sha not in found_hashes:
        errors.append(f"{root}: smoke package SHA does not match provenance/package SHA256")


def conventional_provenance_path(version: str) -> Path:
    return Path(f"build/daee-epistemics-{version}.provenance.json")


def release_manifest_path(version: str) -> Path:
    return Path("docs/releases") / f"{version}-provenance.json"


def package_summary(path: Path, errors: list[str]) -> dict[str, object]:
    package_sha = sha256(path, errors, "package artifact")
    entry_count = zip_entry_count(path, errors)
    return {
        "artifact_name": path.name,
        "artifact_sha256": package_sha or "",
        "artifact_size": path.stat().st_size if path.exists() else 0,
        "entry_count": entry_count or 0,
    }


def source_commit_from_provenance(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    value = payload.get("source_commit") if isinstance(payload, dict) else None
    return value if isinstance(value, str) else ""


def remote_tag_target(tag: str) -> str:
    line = git_output(["ls-remote", "--tags", "origin", f"refs/tags/{tag}^{{}}"])
    if not line:
        line = git_output(["ls-remote", "--tags", "origin", f"refs/tags/{tag}"])
    if not line:
        return ""
    return line.split()[0]


def build_release_manifest(
    version: str,
    artifact: Path,
    release_body: Path | None,
    provenance_path: Path | None,
    proof_commands: list[str] | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    summary = package_summary(artifact, errors)
    head = git_output(["rev-parse", "HEAD"]) or ""
    local_tag = git_output(["rev-parse", f"{version}^{{}}"]) or git_output(["rev-parse", version]) or ""
    remote_tag = remote_tag_target(version)
    package_built_from = source_commit_from_provenance(provenance_path or conventional_provenance_path(version))
    release = gh_json([
        "release",
        "view",
        version,
        "--json",
        "name,tagName,publishedAt,assets,url,isPrerelease",
    ])
    return {
        "version": version,
        "source_commit": head,
        "tag": version,
        "tag_target": local_tag,
        "remote_tag_target": remote_tag,
        "github_release": release or {},
        "artifact_name": summary["artifact_name"],
        "artifact_sha256": summary["artifact_sha256"],
        "artifact_size": summary["artifact_size"],
        "artifact_entries": summary["entry_count"],
        "package_built_from": package_built_from or head,
        "release_body_file": str(release_body) if release_body else "",
        "proof_commands": proof_commands or [],
        "proof_outputs_summary": {
            "package_artifact": "computed from actual artifact",
            "tag_alignment": "checked when local/remote tag exists",
            "github_release": "checked when gh release view is available",
        },
        "caveats": [
            "raw smoke outputs are local evidence, not release assets",
            "cross-host/paraphrase proof is not claimed",
            "T_lang does not imply guaranteed uptake",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_manifest(path: Path, manifest: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_release_body(path: Path, manifest: dict[str, object]) -> None:
    version = str(manifest["version"])
    artifact_name = str(manifest["artifact_name"])
    artifact_sha = str(manifest["artifact_sha256"])
    artifact_size = int(manifest["artifact_size"])
    source_commit = str(manifest["source_commit"])
    lines = [
        f"# {version} - Closure Reconstructibility + Mid-Reread Pressure",
        "",
        "## Summary",
        "",
        "v0.4.3.0 makes daee-epistemics more reconstructible and operational at reread/closure time.",
        "It includes closure-witness graph accounting, machine-readable `field_witness`, local",
        "visualizer/checker fixtures, and Mid-Reread Pressure as a behaviorally smoke-proven",
        "reread-time TTP.",
        "",
        "## Behavioral Proof",
        "",
        "- Repair14 hard-compound Smoke 6 is the decisive Codex-hosted exact-file behavioral MRP proof.",
        "- v0.4.2.0 remains a strong governed baseline but lacks explicit MRP as a named reread-pressure TTP.",
        "- The later secularism exact-file smoke proves generic route/curl/field generalization only,",
        "  not a fresh full reconstructibility proof.",
        "- Raw smoke outputs are local evidence and are not release assets.",
        "",
        "## Release Fixes Included",
        "",
        "- closure witness dependency graph and `field_witness` validation;",
        "- Trinitarian MRP route/curl hotfix;",
        "- generic MRP route/curl invariant checker and fixtures;",
        "- mojibake guard/fix for parseable governance notation;",
        "- package-bound artifact validation.",
        "",
        "## Artifact",
        "",
        f"- `{artifact_name}`",
        f"- size: `{artifact_size}` bytes",
        f"- SHA256: `{artifact_sha}`",
        f"- source commit: `{source_commit}`",
        "",
        "## Caveats",
        "",
        "- Not a cross-host/paraphrase proof.",
        "- Not a claim of guaranteed uptake from `T_lang`.",
        "- Raw smoke outputs are local evidence, not release assets.",
        "- Repeated schema language / bloat cleanup remains future work.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def check_release_body(path: Path, manifest: dict[str, object], errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"release body is absent: {path}")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    required = {
        "version": str(manifest["version"]),
        "artifact name": str(manifest["artifact_name"]),
        "artifact SHA256": str(manifest["artifact_sha256"]),
        "source commit": str(manifest["source_commit"]),
        "Repair14 proof boundary": "Repair14",
        "route/curl caveat": "route/curl",
        "raw smoke boundary": "Raw smoke outputs are local evidence",
    }
    for label, token in required.items():
        if token and token not in text:
            errors.append(f"{path}: release body missing {label}: {token}")


def check_release_download_metadata(manifest: dict[str, object], errors: list[str]) -> None:
    path = ROOT / "docs" / "index" / "release-download.json"
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return
    if not isinstance(payload, dict):
        errors.append(f"{path.relative_to(ROOT)}: expected JSON object")
        return

    artifact_name = str(manifest["artifact_name"])
    if payload.get("primary_skill_asset_name") != artifact_name:
        errors.append(
            f"docs/index/release-download.json: primary asset mismatch: "
            f"{payload.get('primary_skill_asset_name')} != {artifact_name}"
        )
    expected_size = int(manifest["artifact_size"])
    if int(payload.get("primary_skill_asset_size") or 0) != expected_size:
        errors.append(
            f"docs/index/release-download.json: asset size mismatch: "
            f"{payload.get('primary_skill_asset_size')} != {expected_size}"
        )
    expected_digest = f"sha256:{str(manifest['artifact_sha256']).lower()}"
    if str(payload.get("primary_skill_asset_digest") or "").lower() != expected_digest:
        errors.append("docs/index/release-download.json: asset digest mismatch")
    if str(payload.get("sha256") or "").upper() != str(manifest["artifact_sha256"]).upper():
        errors.append("docs/index/release-download.json: SHA256 mismatch")


def check_github_release_assets(version: str, manifest: dict[str, object], errors: list[str]) -> None:
    release = manifest.get("github_release")
    if not isinstance(release, dict) or not release:
        return
    if release.get("tagName") != version:
        errors.append(f"GitHub Release tag mismatch: {release.get('tagName')} != {version}")
    assets = release.get("assets")
    if not isinstance(assets, list):
        return
    expected_name = str(manifest["artifact_name"])
    expected_sha = str(manifest["artifact_sha256"]).lower()
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        if name != expected_name:
            continue
        digest = str(asset.get("digest") or "").lower().replace("sha256:", "")
        size = asset.get("size")
        if digest and digest != expected_sha:
            errors.append(f"GitHub Release asset digest mismatch for {expected_name}: {digest} != {expected_sha}")
        if isinstance(size, int) and size != int(manifest["artifact_size"]):
            errors.append(f"GitHub Release asset size mismatch for {expected_name}: {size} != {manifest['artifact_size']}")
        return
    errors.append(f"GitHub Release missing expected artifact asset: {expected_name}")


def check_release_preflight(
    version: str,
    artifact: Path,
    release_body: Path | None,
    provenance_path: Path | None,
    manifest_out: Path | None,
    release_artifacts: Path | None,
    write_body: Path | None,
) -> int:
    errors: list[str] = []
    manifest = build_release_manifest(version, artifact, release_body, provenance_path)
    if manifest_out:
        write_manifest(manifest_out, manifest)
    if write_body:
        write_release_body(write_body, manifest)
        release_body = write_body

    if not manifest["artifact_sha256"]:
        errors.append(f"artifact SHA256 could not be computed: {artifact}")
    source_commit = str(manifest["source_commit"])
    package_built_from = str(manifest["package_built_from"])
    if package_built_from and package_built_from != source_commit:
        errors.append(f"artifact/provenance source mismatch: {package_built_from} != HEAD {source_commit}")
    for label, value in (
        ("local tag", str(manifest["tag_target"])),
        ("remote tag", str(manifest["remote_tag_target"])),
    ):
        if value and value != source_commit:
            errors.append(f"{label} target differs from source commit: {value} != {source_commit}")
    if str(manifest["tag_target"]) and str(manifest["remote_tag_target"]):
        if str(manifest["tag_target"]) != str(manifest["remote_tag_target"]):
            errors.append("local tag target differs from remote tag target")
    if release_body:
        check_release_body(release_body, manifest, errors)
    if release_artifacts:
        fake_payload = {
            "package_sha256": manifest["artifact_sha256"],
            "package_size": manifest["artifact_size"],
            "entry_count": manifest["artifact_entries"],
            "build_manifest_sha256": "",
            "compiled_module_map_sha256": "",
        }
        check_release_artifacts_doc(release_artifacts, artifact, str(manifest["artifact_sha256"]), fake_payload, errors)
    check_release_download_metadata(manifest, errors)
    errors.extend(run_mojibake_preflight(release_body, manifest_out, provenance_path))
    errors.extend(run_generated_surface_preflight())
    errors.extend(run_package_artifact_preflight(version, artifact))
    check_github_release_assets(version, manifest, errors)

    if errors:
        print("release provenance preflight: FAIL")
        for error in errors:
            print(f"- {error}")
        if manifest_out:
            print(f"- manifest written: {manifest_out}")
        return 1
    print("release provenance preflight: PASS")
    print(f"- version: {version}")
    print(f"- source commit: {source_commit}")
    print(f"- artifact: {artifact}")
    print(f"- artifact SHA256: {manifest['artifact_sha256']}")
    print(f"- artifact size: {manifest['artifact_size']}")
    if manifest_out:
        print(f"- manifest written: {manifest_out}")
    if write_body:
        print(f"- release body written: {write_body}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--package", dest="package_path", type=Path)
    parser.add_argument("--manifest", default=Path("skill/build-manifest.json"), type=Path)
    parser.add_argument("--compiled-map", default=Path("skill/compiled-module-map.json"), type=Path)
    parser.add_argument("--release-artifacts", type=Path)
    parser.add_argument("--smoke-root", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--release-body", type=Path)
    parser.add_argument("--write-manifest", nargs="?", const="__default__")
    parser.add_argument("--write-release-body", type=Path)
    args = parser.parse_args(argv)

    if args.version or args.artifact:
        if not args.version or not args.artifact:
            parser.error("--version and --artifact must be supplied together for release preflight")
        manifest_out: Path | None = None
        if args.write_manifest:
            manifest_out = release_manifest_path(args.version) if args.write_manifest == "__default__" else Path(args.write_manifest)
        return check_release_preflight(
            args.version,
            args.artifact,
            args.release_body,
            args.provenance,
            manifest_out,
            args.release_artifacts,
            args.write_release_body,
        )

    if args.provenance is None or args.package_path is None:
        parser.error("either --version/--artifact or --provenance/--package is required")

    errors: list[str] = []
    payload = read_json(args.provenance, errors)
    if payload:
        check_required_fields(payload, errors)

    package_sha = sha256(args.package_path, errors, "package")
    package_size = args.package_path.stat().st_size if args.package_path.exists() else None
    entry_count = zip_entry_count(args.package_path, errors)
    manifest_sha = sha256(args.manifest, errors, "build manifest")
    compiled_map_sha = sha256(args.compiled_map, errors, "compiled module map")

    if payload:
        compare_hash(
            "package SHA256",
            package_sha,
            provenance_field(payload, "package_sha256", errors, required=False),
            errors,
        )
        compare_int(
            "package size",
            package_size,
            provenance_field(payload, "package_size", errors, required=False),
            errors,
        )
        compare_int(
            "entry count",
            entry_count,
            provenance_field(payload, "entry_count", errors, required=False),
            errors,
        )
        compare_hash(
            "build-manifest SHA256",
            manifest_sha,
            provenance_field(payload, "build_manifest_sha256", errors, required=False),
            errors,
        )
        compare_hash(
            "compiled-module-map SHA256",
            compiled_map_sha,
            provenance_field(payload, "compiled_module_map_sha256", errors, required=False),
            errors,
        )

    if args.release_artifacts and package_sha and payload:
        check_release_artifacts_doc(args.release_artifacts, args.package_path, package_sha, payload, errors)
    if args.smoke_root and package_sha:
        check_smoke_root(args.smoke_root, package_sha, errors)

    if errors:
        print("release provenance check: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("release provenance check: PASS")
    print(f"- package: {args.package_path}")
    print(f"- package SHA256: {package_sha}")
    print(f"- package size: {package_size}")
    print(f"- package entries: {entry_count}")
    print(f"- build-manifest SHA256: {manifest_sha}")
    print(f"- compiled-module-map SHA256: {compiled_map_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
