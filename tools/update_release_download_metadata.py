"""Refresh docs/index release-download metadata from GitHub Release assets.

The generated docs/index page uses a static metadata file instead of calling
the GitHub API from the browser. Local runs fall back to the latest-release page
when gh/auth/network are unavailable; release/docs-publish automation can pass
--require-github to make lookup failures hard failures.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "theislampill/daee-epistemics"
DEFAULT_OUTPUT = ROOT / "docs" / "index" / "release-download.json"
RELEASE_ARTIFACTS = ROOT / "docs" / "release-artifacts.md"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_sha_from_docs() -> str:
    if not RELEASE_ARTIFACTS.exists():
        return ""
    text = RELEASE_ARTIFACTS.read_text(encoding="utf-8")
    match = re.search(r"\|\s*SHA256\s*\|\s*`([A-Fa-f0-9]{64})`", text)
    return match.group(1).upper() if match else ""


def release_download_url(repo: str, tag: str, asset_name: str) -> str:
    return f"https://github.com/{repo}/releases/download/{tag}/{asset_name}"


def select_asset(assets: list[dict[str, Any]], suffix: str, stable_name: str = "") -> dict[str, Any] | None:
    if stable_name:
        for asset in assets:
            if asset.get("name") == stable_name:
                return asset
    candidates = [
        asset
        for asset in assets
        if isinstance(asset.get("name"), str)
        and asset["name"].endswith(suffix)
        and not asset["name"].endswith(f"{suffix}.zip")
    ]
    return sorted(candidates, key=lambda asset: asset["name"])[0] if candidates else None


def asset_sha(asset: dict[str, Any] | None) -> str:
    if not asset:
        return ""
    digest = asset.get("digest")
    if isinstance(digest, str):
        match = re.fullmatch(r"sha256:([A-Fa-f0-9]{64})", digest.strip())
        if match:
            return match.group(1).upper()
    return ""


def run_gh_release_view(repo: str, tag: str | None) -> dict[str, Any]:
    command = [
        "gh",
        "release",
        "view",
        "--repo",
        repo,
        "--json",
        "tagName,name,url,isDraft,isPrerelease,assets,publishedAt",
    ]
    if tag:
        command.insert(3, tag)
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip() or "gh release view failed"
        raise RuntimeError(detail)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gh release view returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("gh release view returned a non-object payload")
    return payload


def fallback_metadata(repo: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "fallback-latest-release-page",
        "source": "fallback",
        "generated_at": now_utc(),
        "repo": repo,
        "latest_tag": "",
        "release_title": "Latest GitHub Release",
        "release_url": f"https://github.com/{repo}/releases/latest",
        "download_kind": "latest_release_page",
        "primary_skill_asset_name": "",
        "primary_skill_asset_browser_download_url": "",
        "provenance_asset_name": "",
        "provenance_asset_browser_download_url": "",
        "sha256": parse_sha_from_docs(),
        "fallback_url": f"https://github.com/{repo}/releases/latest",
        "lookup_error": reason,
        "non_claim": "Release metadata powers a navigation link only; it is not runtime proof, smoke proof, or a public raw-smoke artifact.",
    }


def build_metadata(repo: str, tag: str | None) -> dict[str, Any]:
    release = run_gh_release_view(repo, tag)
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise RuntimeError("release JSON did not include an assets list")

    release_tag = str(release.get("tagName") or "")
    primary = select_asset(assets, ".skill", "daee-epistemics.skill")
    provenance = select_asset(assets, ".provenance.json", "daee-epistemics.provenance.json")
    docs_sha = parse_sha_from_docs()
    primary_sha = asset_sha(primary) or docs_sha
    direct_url = ""
    if primary and release_tag:
        direct_url = str(primary.get("url") or "") or release_download_url(repo, release_tag, str(primary["name"]))

    download_kind = "direct_asset" if direct_url else "latest_release_page"
    fallback_url = f"https://github.com/{repo}/releases/latest"
    provenance_url = ""
    if provenance and release_tag:
        provenance_url = str(provenance.get("url") or "") or release_download_url(repo, release_tag, str(provenance["name"]))

    return {
        "schema_version": 1,
        "status": "generated-release-download-metadata",
        "source": "GitHub Release metadata via gh release view",
        "generated_at": now_utc(),
        "repo": repo,
        "latest_tag": release_tag,
        "release_title": str(release.get("name") or release_tag or "Latest GitHub Release"),
        "release_url": str(release.get("url") or fallback_url),
        "published_at": str(release.get("publishedAt") or ""),
        "is_draft": bool(release.get("isDraft")),
        "is_prerelease": bool(release.get("isPrerelease")),
        "download_kind": download_kind,
        "primary_skill_asset_name": str(primary.get("name") if primary else ""),
        "primary_skill_asset_browser_download_url": direct_url,
        "primary_skill_asset_size": int(primary.get("size") or 0) if primary else 0,
        "primary_skill_asset_digest": str(primary.get("digest") or "") if primary else "",
        "provenance_asset_name": str(provenance.get("name") if provenance else ""),
        "provenance_asset_browser_download_url": provenance_url,
        "provenance_asset_digest": str(provenance.get("digest") or "") if provenance else "",
        "sha256": primary_sha,
        "fallback_url": fallback_url,
        "non_claim": "Release metadata powers a navigation link only; it is not runtime proof, smoke proof, or a public raw-smoke artifact.",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {rel(path)} ({payload.get('download_kind')})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"GitHub owner/repo (default: {DEFAULT_REPO})")
    parser.add_argument("--tag", default=None, help="Release tag to inspect; omit to use gh's latest release")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Output JSON path (default: {rel(DEFAULT_OUTPUT)})")
    parser.add_argument(
        "--require-github",
        action="store_true",
        help="Fail instead of writing fallback metadata when gh release lookup fails.",
    )
    args = parser.parse_args(argv)

    output = args.output if args.output.is_absolute() else ROOT / args.output
    try:
        payload = build_metadata(args.repo, args.tag)
    except Exception as exc:  # noqa: BLE001 - surfaced as CLI diagnostic/fallback.
        if args.require_github:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        payload = fallback_metadata(args.repo, str(exc))
        print(f"WARNING: {exc}; writing latest-release fallback metadata", file=sys.stderr)
    write_json(output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
