#!/usr/bin/env python3
"""Execute one static Python script/module under the Branch 10 sanitized profile."""
from __future__ import annotations

import os
import runpy
import sys
import sysconfig
from pathlib import Path
from typing import NoReturn


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
ALLOWED_MODULES = {"py_compile"}
REMOVED_ENVIRONMENT_NAMES_ATTRIBUTE = "_daee_sanitized_python_removed_environment_names"


def _fail(message: str) -> NoReturn:
    raise SystemExit(f"sanitized Python bootstrap: {message}")


def _append_once(paths: list[str], value: str | None) -> None:
    if value:
        resolved = str(Path(value).resolve())
        key = os.path.normcase(resolved)
        if key not in {os.path.normcase(path) for path in paths}:
            paths.append(resolved)


def _sysconfig_root(value: object, role: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"invalid sysconfig path for {role}: non-empty string required")
    path = Path(value)
    if not path.is_absolute():
        _fail(f"invalid sysconfig path for {role}: absolute path required")
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        _fail(f"invalid sysconfig path for {role}: {exc}")
    if resolved.exists() and not resolved.is_dir():
        _fail(f"invalid sysconfig path for {role}: existing path is not a directory")
    return str(resolved)


def _install_import_roots(script_parent: Path | None) -> None:
    configured: list[str] = []
    _append_once(configured, str(ROOT))
    _append_once(configured, str(TOOLS))
    if script_parent is not None:
        _append_once(configured, str(script_parent))
    paths = sysconfig.get_paths()
    if not isinstance(paths, dict):
        _fail("invalid sysconfig paths: mapping required")
    for role in ("stdlib", "platstdlib"):
        _append_once(configured, _sysconfig_root(paths.get(role), f"system {role}"))
    for role in ("purelib", "platlib"):
        _append_once(configured, _sysconfig_root(paths.get(role), f"system {role}"))
    # Local Branch 10 verification may install requirements-ci.txt into the
    # interpreter's user scheme. Add those roots directly, without importing
    # site, calling addsitedir, or processing any .pth file. Under -I -S the
    # user scheme cannot influence interpreter startup; it becomes reachable
    # only after the bootstrap has removed Python environment variables and
    # verified that no startup customization module ran.
    user_scheme = "nt_user" if os.name == "nt" else "posix_user"
    if user_scheme in sysconfig.get_scheme_names():
        for role in ("purelib", "platlib"):
            _append_once(
                configured,
                _sysconfig_root(
                    sysconfig.get_path(role, scheme=user_scheme),
                    f"{user_scheme} {role}",
                ),
            )
    for inherited in sys.path:
        if inherited:
            _append_once(configured, inherited)
    sys.path[:] = configured


def _remove_inherited_python_environment() -> list[str]:
    removed_environment_names = sorted(
        [
            key
            for key in os.environ
            if key.upper().startswith("PYTHON") or key.upper() == "__PYVENV_LAUNCHER__"
        ],
        key=lambda key: (key.upper(), key),
    )
    for key in removed_environment_names:
        del os.environ[key]
    return removed_environment_names


def main() -> int:
    if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        _fail("requires exact -I -S -B startup flags")
    if "sitecustomize" in sys.modules or "usercustomize" in sys.modules:
        _fail("startup customization module was imported")
    removed_environment_names = _remove_inherited_python_environment()
    setattr(sys, REMOVED_ENVIRONMENT_NAMES_ATTRIBUTE, tuple(removed_environment_names))
    if any(
        key.upper().startswith("PYTHON") or key.upper() == "__PYVENV_LAUNCHER__"
        for key in os.environ
    ):
        _fail("inherited Python environment deletion was incomplete")
    if len(sys.argv) < 3 or sys.argv[1] not in {"--script", "--module"}:
        _fail("requires one explicit --script or --module target")
    mode, target, *arguments = sys.argv[1:]
    if mode == "--script":
        script = Path(target)
        if not script.is_absolute():
            script = ROOT / script
        script = script.resolve()
        if script.suffix != ".py" or not script.is_file():
            _fail(f"static script target is not an existing .py file: {target}")
        _install_import_roots(script.parent)
        if "sitecustomize" in sys.modules or "usercustomize" in sys.modules:
            _fail("startup customization module was imported")
        sys.argv = [str(script), *arguments]
        runpy.run_path(str(script), run_name="__main__")
        return 0
    if target not in ALLOWED_MODULES:
        _fail(f"unsupported static module target: {target}")
    _install_import_roots(None)
    if "sitecustomize" in sys.modules or "usercustomize" in sys.modules:
        _fail("startup customization module was imported")
    sys.argv = [target, *arguments]
    runpy.run_module(target, run_name="__main__", alter_sys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
