#!/usr/bin/env python3
"""Narrow, fail-closed Codex CLI adapter for the governed producer cohort.

The adapter never treats process start as provider acceptance.  It retains exact
prompt/output/JSONL bytes, keeps the access credential in child-process memory,
and stops at immutable raw capture for separately governed structural review.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed, wait
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

from artifact_tree import tree_sha256
from check_captured_output_manifest import PublicationError, atomic_publish_bytes
from credential_residue_scan_contract import (
    CredentialResidueError,
    MANAGED_AUTH_MARKER_FAMILIES as _MANAGED_AUTH_MARKER_FAMILIES,
    MANAGED_AUTH_SCAN_MODE as _MANAGED_AUTH_SCAN_MODE,
    ManagedCredentialScanAmbiguousError,
    PASS_V3_SCHEMA as _MANAGED_AUTH_SCAN_SCHEMA,
    SAFE_CARRIER_ROLES as _SAFE_CARRIER_ROLES,
    classify_managed_auth_bytes as _classify_managed_auth_bytes,
)
from runtime_call_context_adapter import prepare_runtime_call
from runtime_context_resolver import EMPTY_VALIDATED_STATE


ROOT = Path(__file__).resolve().parents[1]


CANONICAL_EXEC_FLAGS = ["--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "-C", "-s", "-m", "-c", "--output-last-message", "-"]
_DEDICATED_AGENT_IDENTITY_ENV = "DEDICATED_AGENT_IDENTITY_ENV"
_MANAGED_AUTH_HOME = "CLI_MANAGED_AUTH_HOME"
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_OWNERSHIP_WITNESS_NAME = ".daee-owned-directory-v1"
_OWNERSHIP_WITNESS_BYTE_COUNT = 32
_OBSERVATION_QUIESCENCE_SECONDS = 20.0
_PRODUCER_OBSERVATION_PROTOCOL = "concurrent-five-shared-deadline-v1"
_OPTION_DECLARATION_RE = re.compile(
    r"^\s*(?P<short>-[A-Za-z0-9])?"
    r"(?:(?:,\s*)?(?P<long>--[a-z0-9][a-z0-9-]*))?"
    r"(?:\s+(?:<[^>\r\n]+>|\[[^\]\r\n]+\]))?"
    r"(?:\s{2,}.*)?$"
)


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _CREATE_SUSPENDED = 0x00000004
    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS = 1
    _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
    _TH32CS_SNAPTHREAD = 0x00000004
    _THREAD_SUSPEND_RESUME = 0x0002
    _INVALID_DWORD = 0xFFFFFFFF
    _ERROR_NO_MORE_FILES = 18

    class _JobObjectBasicAccountingInformation(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    class _JobObjectBasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class _JobObjectExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _JobObjectBasicLimitInformation),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class _ThreadEntry32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ThreadID", wintypes.DWORD),
            ("th32OwnerProcessID", wintypes.DWORD),
            ("tpBasePri", wintypes.LONG),
            ("tpDeltaPri", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
        ]

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    _kernel32.SetInformationJobObject.restype = wintypes.BOOL
    _kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    _kernel32.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    _kernel32.IsProcessInJob.restype = wintypes.BOOL
    _kernel32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    _kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _kernel32.TerminateJobObject.restype = wintypes.BOOL
    _kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _kernel32.TerminateProcess.restype = wintypes.BOOL
    _kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _kernel32.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ThreadEntry32)]
    _kernel32.Thread32First.restype = wintypes.BOOL
    _kernel32.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ThreadEntry32)]
    _kernel32.Thread32Next.restype = wintypes.BOOL
    _kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.OpenThread.restype = wintypes.HANDLE
    _kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    _kernel32.ResumeThread.restype = wintypes.DWORD
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL

    def _resume_only_suspended_thread(process: subprocess.Popen[bytes]) -> None:
        snapshot = _kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPTHREAD, 0)
        if int(snapshot) == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        thread_ids: list[int] = []
        try:
            entry = _ThreadEntry32()
            entry.dwSize = ctypes.sizeof(entry)
            present = bool(_kernel32.Thread32First(snapshot, ctypes.byref(entry)))
            if not present and ctypes.get_last_error() != _ERROR_NO_MORE_FILES:
                raise ctypes.WinError(ctypes.get_last_error())
            while present:
                if int(entry.th32OwnerProcessID) == process.pid:
                    thread_ids.append(int(entry.th32ThreadID))
                entry.dwSize = ctypes.sizeof(entry)
                present = bool(_kernel32.Thread32Next(snapshot, ctypes.byref(entry)))
                if not present and ctypes.get_last_error() != _ERROR_NO_MORE_FILES:
                    raise ctypes.WinError(ctypes.get_last_error())
        finally:
            if not _kernel32.CloseHandle(snapshot):
                raise ctypes.WinError(ctypes.get_last_error())
        if len(thread_ids) != 1:
            raise RuntimeError(
                f"suspended Windows launch exposed {len(thread_ids)} threads; exactly one required"
            )
        thread = _kernel32.OpenThread(_THREAD_SUSPEND_RESUME, False, thread_ids[0])
        if not thread:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            previous_count = int(_kernel32.ResumeThread(thread))
            if previous_count == _INVALID_DWORD:
                raise ctypes.WinError(ctypes.get_last_error())
            if previous_count != 1:
                raise RuntimeError(
                    f"suspended Windows launch had unexpected suspend count {previous_count}"
                )
        finally:
            if not _kernel32.CloseHandle(thread):
                raise ctypes.WinError(ctypes.get_last_error())

    class _WindowsJobCustody:
        """Kernel-owned process-tree custody, never reconstructed from process ancestry."""

        def __init__(self) -> None:
            handle = _kernel32.CreateJobObjectW(None, None)
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            self.handle: int | None = int(handle)
            limits = _JobObjectExtendedLimitInformation()
            limits.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not _kernel32.SetInformationJobObject(
                wintypes.HANDLE(self.handle),
                _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
                ctypes.byref(limits),
                ctypes.sizeof(limits),
            ):
                error = ctypes.get_last_error()
                self.close()
                raise ctypes.WinError(error)

        def _handle(self) -> wintypes.HANDLE:
            if self.handle is None:
                raise RuntimeError("Windows Job Object custody handle is closed")
            return wintypes.HANDLE(self.handle)

        def assign_verify_resume(self, process: subprocess.Popen[bytes]) -> None:
            process_handle = wintypes.HANDLE(int(process._handle))
            if not _kernel32.AssignProcessToJobObject(self._handle(), process_handle):
                raise ctypes.WinError(ctypes.get_last_error())
            assigned = wintypes.BOOL()
            if not _kernel32.IsProcessInJob(process_handle, self._handle(), ctypes.byref(assigned)):
                raise ctypes.WinError(ctypes.get_last_error())
            if not assigned.value:
                raise RuntimeError("Windows Job Object assignment verification failed")
            _resume_only_suspended_thread(process)

        def active_processes(self) -> int:
            info = _JobObjectBasicAccountingInformation()
            returned = wintypes.DWORD()
            if not _kernel32.QueryInformationJobObject(
                self._handle(),
                _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS,
                ctypes.byref(info),
                ctypes.sizeof(info),
                ctypes.byref(returned),
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            return int(info.ActiveProcesses)

        def terminate(self, exit_code: int) -> None:
            if not _kernel32.TerminateJobObject(self._handle(), exit_code):
                raise ctypes.WinError(ctypes.get_last_error())

        def close(self) -> None:
            handle = self.handle
            if handle is None:
                return
            self.handle = None
            if not _kernel32.CloseHandle(wintypes.HANDLE(handle)):
                raise ctypes.WinError(ctypes.get_last_error())


class IsolationCleanupError(RuntimeError):
    pass


class DirectoryIdentity(NamedTuple):
    directory_device: int
    directory_inode: int
    witness_device: int
    witness_inode: int
    witness_ctime_ns: int
    witness_byte_count: int
    witness_sha256: str


class WrittenFileIdentity(NamedTuple):
    device: int
    inode: int
    ctime_ns: int
    byte_count: int
    sha256: str


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _strict_json_event(line: bytes) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value

    def reject_nonfinite(constant: str) -> object:
        raise ValueError(f"non-finite JSON number is forbidden: {constant}")

    try:
        value = json.loads(
            line,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"Codex JSONL event stream invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("Codex JSONL event must be an object")
    return value


def _complete_jsonl_prefix(raw: bytes) -> tuple[bytes, list[dict[str, Any]]]:
    final_newline = raw.rfind(b"\n")
    if final_newline < 0:
        return b"", []
    prefix = raw[: final_newline + 1]
    lines = prefix.splitlines()
    if any(not line.strip() for line in lines):
        raise RuntimeError("Codex JSONL event stream contains a blank record")
    return prefix, [_strict_json_event(line) for line in lines]


def _write_once(path: Path, data: bytes) -> WrittenFileIdentity:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        if handle.write(data) != len(data):
            raise OSError("short create-once write")
        handle.flush()
        os.fsync(handle.fileno())
        observed = os.fstat(handle.fileno())
        if not stat.S_ISREG(observed.st_mode) or observed.st_size != len(data):
            raise OSError("create-once write identity unavailable")
        return WrittenFileIdentity(
            observed.st_dev,
            observed.st_ino,
            observed.st_ctime_ns,
            observed.st_size,
            hashlib.sha256(data).hexdigest(),
        )


def _is_reparse(path: Path) -> bool:
    observed = path.lstat()
    return path.is_symlink() or bool(getattr(observed, "st_file_attributes", 0) & _REPARSE_POINT)


def _lstat_optional(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _regular_directory_stat(path: Path, label: str) -> os.stat_result:
    observed = _lstat_optional(path)
    if observed is None:
        raise IsolationCleanupError(f"{label}: creation identity unavailable")
    if (
        not stat.S_ISDIR(observed.st_mode)
        or stat.S_ISLNK(observed.st_mode)
        or bool(getattr(observed, "st_file_attributes", 0) & _REPARSE_POINT)
    ):
        raise IsolationCleanupError(f"{label}: regular non-reparse directory required")
    return observed


def _ownership_witness_identity(path: Path, label: str) -> tuple[int, int, int, int, str]:
    before = _lstat_optional(path)
    if before is None:
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} ownership witness is missing"
        )
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or bool(getattr(before, "st_file_attributes", 0) & _REPARSE_POINT)
        or before.st_size != _OWNERSHIP_WITNESS_BYTE_COUNT
    ):
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} ownership witness is not the exact regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} ownership witness could not be opened"
        ) from exc
    try:
        opened = os.fstat(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_ctime_ns,
            before.st_size,
        )
        opened_identity = (
            opened.st_dev,
            opened.st_ino,
            opened.st_ctime_ns,
            opened.st_size,
        )
        if not stat.S_ISREG(opened.st_mode) or opened_identity != before_identity:
            raise IsolationCleanupError(
                f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} ownership witness changed before readback"
            )
        raw = bytearray()
        while len(raw) <= _OWNERSHIP_WITNESS_BYTE_COUNT:
            chunk = os.read(descriptor, _OWNERSHIP_WITNESS_BYTE_COUNT + 1 - len(raw))
            if not chunk:
                break
            raw.extend(chunk)
    finally:
        os.close(descriptor)
    if len(raw) != _OWNERSHIP_WITNESS_BYTE_COUNT:
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} ownership witness byte count changed"
        )
    after = _lstat_optional(path)
    if after is None or (
        after.st_dev,
        after.st_ino,
        after.st_ctime_ns,
        after.st_size,
    ) != before_identity or (
        not stat.S_ISREG(after.st_mode)
        or stat.S_ISLNK(after.st_mode)
        or bool(getattr(after, "st_file_attributes", 0) & _REPARSE_POINT)
    ):
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} ownership witness changed during readback"
        )
    return (
        before.st_dev,
        before.st_ino,
        before.st_ctime_ns,
        len(raw),
        hashlib.sha256(raw).hexdigest(),
    )


def _regular_directory_identity(path: Path, label: str) -> DirectoryIdentity:
    observed = _regular_directory_stat(path, label)
    witness = _ownership_witness_identity(path / _OWNERSHIP_WITNESS_NAME, label)
    return DirectoryIdentity(observed.st_dev, observed.st_ino, *witness)


def _create_owned_directory(path: Path, label: str, *, parents: bool) -> DirectoryIdentity:
    path.mkdir(parents=parents, exist_ok=False)
    created = _regular_directory_stat(path, label)
    witness_path = path / _OWNERSHIP_WITNESS_NAME
    witness_raw = secrets.token_bytes(_OWNERSHIP_WITNESS_BYTE_COUNT)
    try:
        created_witness = _write_once(witness_path, witness_raw)
        identity = _regular_directory_identity(path, label)
        if (identity.directory_device, identity.directory_inode) != (
            created.st_dev,
            created.st_ino,
        ):
            raise IsolationCleanupError(f"{label}: parent identity changed during witness creation")
        if tuple(identity[2:]) != tuple(created_witness):
            raise IsolationCleanupError(
                f"{label}: ownership witness changed after exclusive creation"
            )
        return identity
    except BaseException as exc:
        residue = "; unverified creation residue retained" if _lstat_optional(path) is not None else ""
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CREATION_IDENTITY_UNAVAILABLE: {label}{residue}"
        ) from exc


def _require_owned_directory(
    path: Path,
    expected: DirectoryIdentity,
    label: str,
) -> os.stat_result | None:
    observed = _lstat_optional(path)
    if observed is None:
        return None
    if (
        not stat.S_ISDIR(observed.st_mode)
        or stat.S_ISLNK(observed.st_mode)
        or bool(getattr(observed, "st_file_attributes", 0) & _REPARSE_POINT)
    ):
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} is not a regular non-reparse directory"
        )
    actual = (observed.st_dev, observed.st_ino)
    if actual != (expected.directory_device, expected.directory_inode):
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} creation identity changed"
        )
    witness = _ownership_witness_identity(path / _OWNERSHIP_WITNESS_NAME, label)
    if witness != (
        expected.witness_device,
        expected.witness_inode,
        expected.witness_ctime_ns,
        expected.witness_byte_count,
        expected.witness_sha256,
    ):
        raise IsolationCleanupError(
            f"OWNED_ISOLATION_CLEANUP_UNSAFE: {label} ownership witness changed"
        )
    return observed


def _ref(base: Path, path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "path": path.relative_to(base).as_posix(),
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _safe_join(root: Path, relative: object, label: str, *, file: bool = False) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or relative.startswith("/"):
        raise ValueError(f"{label}: portable relative path required")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise ValueError(f"{label}: portable relative path required")
    target = Path(os.path.abspath(root.joinpath(*parts)))
    try:
        target.relative_to(Path(os.path.abspath(root)))
    except ValueError as exc:
        raise ValueError(f"{label}: path escapes custody root") from exc
    current = Path(os.path.abspath(root))
    if current.exists() and _is_reparse(current):
        raise ValueError(f"{label}: custody root is symlink/reparse")
    for part in parts:
        current = current / part
        if current.exists() and _is_reparse(current):
            raise ValueError(f"{label}: symlink/reparse component")
    if file and not target.is_file():
        raise ValueError(f"{label}: file unavailable")
    return target


def _retain_content_addressed(base: Path, data: bytes, suffix: str) -> Path:
    digest = hashlib.sha256(data).hexdigest()
    path = base / f"{digest}{suffix}"
    base.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("content-addressed retention collision")
    else:
        try:
            atomic_publish_bytes(path, data)
        except PublicationError as exc:
            if not path.is_file() or path.read_bytes() != data:
                raise ValueError("content-addressed retention collision") from exc
    for stage in base.glob(f".{path.name}.stage-*"):
        try:
            stage.lstat()
        except FileNotFoundError:
            continue
        if not stage.is_file() or stage.is_symlink():
            raise ValueError("unsafe content-addressed retention stage residue")
        stage.unlink()
    if path.read_bytes() != data or _sha256(path) != digest:
        raise ValueError("content-addressed retention readback drift")
    return path


class _DiagnosticRetentionFailure(RuntimeError):
    def __init__(self, role: str, cause: BaseException) -> None:
        super().__init__(f"pre-admission diagnostic retention failed for {role}")
        self.role = role
        self.error_class = type(cause).__name__


def _parse_codex_exec_option_identities(help_text: str) -> set[str]:
    if not isinstance(help_text, str):
        raise TypeError("Codex help text must be text")
    candidates: list[tuple[str, re.Match[str]]] = []
    in_options = False
    for line in help_text.splitlines():
        if line.strip() == "Options:":
            in_options = True
            continue
        if not in_options:
            continue
        if line and not line[0].isspace():
            break
        match = _OPTION_DECLARATION_RE.fullmatch(line)
        if match is None:
            continue
        if match.group("short") is not None or match.group("long") is not None:
            candidates.append((line, match))
    layouts = {
        (len(line) - len(line.lstrip()), line.index(match.group("long")))
        for line, match in candidates
        if match.group("short") is not None and match.group("long") is not None
    }
    if len(layouts) != 1:
        return set()
    short_column, long_column = next(iter(layouts))
    options: set[str] = set()
    for line, match in candidates:
        short = match.group("short")
        long = match.group("long")
        indentation = len(line) - len(line.lstrip())
        if short is not None and indentation == short_column:
            options.add(short)
            if long is not None and line.index(long) == long_column:
                options.add(long)
        elif short is None and long is not None and line.index(long) == long_column:
            options.add(long)
    return options


def _file_contains_any(path: Path, patterns: tuple[bytes, ...]) -> bool:
    overlap = max(len(pattern) for pattern in patterns) - 1
    retained = b""
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            combined = retained + chunk
            if any(pattern in combined for pattern in patterns):
                return True
            retained = combined[-overlap:] if overlap else b""
    return False


def _scan_private_worker_for_credential(worker_root: Path, credential: str) -> dict[str, int]:
    if not isinstance(credential, str) or not credential:
        raise RuntimeError("access credential unavailable for residue readback")
    patterns = tuple(
        dict.fromkeys(
            (
                credential.encode("utf-8"),
                credential.encode("utf-16-le"),
                credential.encode("utf-16-be"),
            )
        )
    )
    if not worker_root.is_dir() or _is_reparse(worker_root):
        raise RuntimeError("private worker root unavailable or reparse during credential readback")
    files = 0
    byte_count = 0
    pending = [worker_root]
    while pending:
        directory = pending.pop()
        if _is_reparse(directory):
            raise RuntimeError("private worker credential readback encountered reparse custody")
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                if _is_reparse(path):
                    raise RuntimeError("private worker credential readback encountered reparse custody")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files += 1
                    byte_count += entry.stat(follow_symlinks=False).st_size
                    if _file_contains_any(path, patterns):
                        raise CredentialResidueError("access credential residue detected")
                else:
                    raise RuntimeError("private worker credential readback encountered unsupported entry")
    return {"scanned_file_count": files, "scanned_byte_count": byte_count}


def _scan_private_worker_for_structural_credential_markers(
    worker_root: Path,
) -> dict[str, object]:
    if not worker_root.is_dir() or _is_reparse(worker_root):
        raise RuntimeError("private worker root unavailable or reparse during credential readback")
    files = 0
    byte_count = 0
    structural_families: set[str] = set()
    pending = [worker_root]
    while pending:
        directory = pending.pop()
        if _is_reparse(directory):
            raise RuntimeError("private worker credential readback encountered reparse custody")
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                if _is_reparse(path):
                    raise RuntimeError("private worker credential readback encountered reparse custody")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files += 1
                    byte_count += entry.stat(follow_symlinks=False).st_size
                    classification = _classify_managed_auth_bytes(path.read_bytes())
                    structural_families.update(
                        classification["observed_structure_families"]
                    )
                else:
                    raise RuntimeError("private worker credential readback encountered unsupported entry")
    return {
        "scanned_file_count": files,
        "scanned_byte_count": byte_count,
        "semantic_classification": (
            "EXPECTED_TRANSPORT_STRUCTURE"
            if structural_families
            else "NO_CREDENTIAL_MARKERS"
        ),
        "observed_structure_families": list(
            family
            for family in _MANAGED_AUTH_MARKER_FAMILIES
            if family in structural_families
        ),
    }


def _copy_tree_exact(source: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(destination)
    for path in [source, *source.rglob("*")]:
        if path.is_symlink():
            raise ValueError(f"candidate package contains symlink/reparse entry: {path}")
    shutil.copytree(source, destination, copy_function=shutil.copyfile)


class SubprocessCodexHost:
    """Real process host.  Tests inject a no-network host with the same surface."""

    def __init__(self) -> None:
        self._windows_jobs: dict[subprocess.Popen[bytes], Any] = {}
        self._windows_released: set[subprocess.Popen[bytes]] = set()
        self._windows_custody_failures: dict[subprocess.Popen[bytes], str] = {}

    def _start_owned_process(
        self,
        command: list[str],
        **popen_kwargs: Any,
    ) -> subprocess.Popen[bytes]:
        if os.name != "nt":
            return subprocess.Popen(command, start_new_session=True, **popen_kwargs)

        job = _WindowsJobCustody()
        process: subprocess.Popen[bytes] | None = None
        try:
            creationflags = int(popen_kwargs.pop("creationflags", 0))
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | _CREATE_SUSPENDED
            process = subprocess.Popen(
                command,
                creationflags=creationflags,
                start_new_session=False,
                **popen_kwargs,
            )
            job.assign_verify_resume(process)
        except BaseException as exc:
            cleanup_errors: list[str] = []
            if process is not None:
                try:
                    if process.poll() is None and not _kernel32.TerminateProcess(
                        wintypes.HANDLE(int(process._handle)), 127
                    ):
                        cleanup_errors.append(str(ctypes.WinError(ctypes.get_last_error())))
                except BaseException as cleanup_exc:
                    cleanup_errors.append(str(cleanup_exc))
            try:
                job.close()
            except BaseException as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
            if process is not None:
                try:
                    process.wait(timeout=20)
                except BaseException as cleanup_exc:
                    cleanup_errors.append(str(cleanup_exc))
            suffix = f"; cleanup failures: {'; '.join(cleanup_errors)}" if cleanup_errors else ""
            raise RuntimeError(f"Windows Job Object launch custody failed closed{suffix}") from exc
        self._windows_jobs[process] = job
        return process

    def _run_probe_command(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        process: subprocess.Popen[bytes] | None = None
        with tempfile.TemporaryFile(dir=cwd) as stdout, tempfile.TemporaryFile(dir=cwd) as stderr:
            try:
                process = self._start_owned_process(
                    command,
                    cwd=cwd,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                )
                returncode = process.wait(timeout=timeout)
            finally:
                if process is not None:
                    self.terminate_tree(process)
                    if not self.verify_tree_stopped(process):
                        raise RuntimeError("capability probe process custody did not terminate")
            stdout.seek(0)
            stderr.seek(0)
            return subprocess.CompletedProcess(
                command,
                returncode,
                stdout.read().decode("utf-8"),
                stderr.read().decode("utf-8"),
            )

    def probe(
        self,
        executable: Path,
        *,
        credential_carrier_available: bool,
    ) -> dict[str, object]:
        if type(credential_carrier_available) is not bool:
            raise TypeError("credential carrier availability must be Boolean")
        safe_env = {
            key: value
            for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATH")
            if (value := os.environ.get(key))
        }
        with tempfile.TemporaryDirectory(prefix="daee-codex-capability-") as temp:
            private = Path(temp)
            private_cache = private / "cache"
            private_temp = private / "temp"
            private_local = private / "appdata/local"
            private_roaming = private / "appdata/roaming"
            for directory in (private_cache, private_temp, private_local, private_roaming):
                directory.mkdir(parents=True, exist_ok=True)
            safe_env.update(
                {
                    "HOME": temp,
                    "USERPROFILE": temp,
                    "CODEX_HOME": temp,
                    "TEMP": str(private_temp),
                    "TMP": str(private_temp),
                    "LOCALAPPDATA": str(private_local),
                    "APPDATA": str(private_roaming),
                    "XDG_CACHE_HOME": str(private_cache),
                }
            )
            version = self._run_probe_command(
                [str(executable), "--version"],
                cwd=private,
                env=safe_env,
                timeout=30,
            )
            if version.returncode != 0:
                raise RuntimeError("Codex version probe failed")
            catalog = self._run_probe_command(
                [str(executable), "debug", "models", "--bundled"],
                cwd=private,
                env=safe_env,
                timeout=60,
            )
            if catalog.returncode != 0:
                raise RuntimeError("Codex structured model catalog probe failed")
            try:
                catalog_value = json.loads(catalog.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Codex model catalog is not structured JSON") from exc
            rows = catalog_value if isinstance(catalog_value, list) else catalog_value.get("models") if isinstance(catalog_value, dict) else None
            if not isinstance(rows, list):
                raise RuntimeError("Codex structured model catalog has no exact model rows")
            matches = [row for row in rows if isinstance(row, dict) and row.get("slug") == "gpt-5.5"]
            if len(matches) != 1:
                raise RuntimeError("Codex structured model catalog lacks one exact gpt-5.5 row")
            efforts = matches[0].get("supported_reasoning_efforts")
            if efforts is None:
                levels = matches[0].get("supported_reasoning_levels")
                if not isinstance(levels, list) or any(
                    not isinstance(item, dict) or not isinstance(item.get("effort"), str)
                    for item in levels
                ):
                    raise RuntimeError("Codex structured model row has invalid reasoning levels")
                efforts = [item["effort"] for item in levels]
            if not isinstance(efforts, list) or "high" not in efforts or any(not isinstance(item, str) for item in efforts):
                raise RuntimeError("Codex structured model row does not support high reasoning")
            exec_help = self._run_probe_command(
                [str(executable), "exec", "--help"], cwd=private, env=safe_env, timeout=30,
            )
            required_options = set(CANONICAL_EXEC_FLAGS) - {"-"}
            parsed_options = _parse_codex_exec_option_identities(exec_help.stdout)
            if exec_help.returncode != 0 or not required_options.issubset(parsed_options):
                raise RuntimeError("Codex canonical exec flags unavailable")
            return {
                "version": version.stdout.strip(),
                "executable_sha256": _sha256(executable),
                "catalog_row": {"slug": "gpt-5.5", "supported_reasoning_efforts": efforts},
                "canonical_exec_flags": list(CANONICAL_EXEC_FLAGS),
                "credential_carrier_available": credential_carrier_available,
            }

    def start(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        prompt_path: Path,
        event_log_path: Path,
        stderr_path: Path,
        output_path: Path,
        worker: str,
    ) -> subprocess.Popen[bytes]:
        del output_path, worker
        event_log_path.parent.mkdir(parents=True, exist_ok=True)
        with prompt_path.open("rb") as prompt, event_log_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            return self._start_owned_process(
                command,
                cwd=cwd,
                env=env,
                stdin=prompt,
                stdout=stdout,
                stderr=stderr,
            )

    def terminate_tree(self, process: subprocess.Popen[bytes]) -> None:
        if os.name == "nt":
            if process in self._windows_released:
                return
            previous_failure = self._windows_custody_failures.get(process)
            if previous_failure is not None:
                raise RuntimeError(f"Windows Job Object custody previously failed: {previous_failure}")
            job = self._windows_jobs.get(process)
            if job is None:
                raise RuntimeError("Windows Job Object custody unavailable; ancestry fallback is forbidden")
            try:
                if job.active_processes() > 0:
                    job.terminate(137)
                deadline = time.monotonic() + 20.0
                while job.active_processes() > 0:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Windows Job Object remained active after termination")
                    time.sleep(0.01)
                process.wait(timeout=max(0.1, deadline - time.monotonic()))
                job.close()
            except BaseException as exc:
                cleanup_errors: list[str] = []
                try:
                    job.close()
                except BaseException as cleanup_exc:
                    cleanup_errors.append(str(cleanup_exc))
                self._windows_jobs.pop(process, None)
                failure = str(exc)
                if cleanup_errors:
                    failure += f"; close failures: {'; '.join(cleanup_errors)}"
                self._windows_custody_failures[process] = failure
                raise RuntimeError(f"Windows Job Object teardown failed closed: {failure}") from exc
            self._windows_jobs.pop(process, None)
            self._windows_released.add(process)
            return
        else:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                process.kill()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=20)

    def verify_tree_stopped(self, process: subprocess.Popen[bytes]) -> bool:
        if os.name == "nt":
            if process in self._windows_released:
                return True
            previous_failure = self._windows_custody_failures.get(process)
            if previous_failure is not None:
                raise RuntimeError(f"Windows Job Object custody previously failed: {previous_failure}")
            job = self._windows_jobs.get(process)
            if job is None:
                raise RuntimeError("Windows Job Object custody unavailable; ancestry fallback is forbidden")
            try:
                active_processes = job.active_processes()
            except BaseException as exc:
                cleanup_errors: list[str] = []
                try:
                    job.terminate(137)
                except BaseException as cleanup_exc:
                    cleanup_errors.append(f"terminate: {cleanup_exc}")
                try:
                    job.close()
                except BaseException as cleanup_exc:
                    cleanup_errors.append(f"close: {cleanup_exc}")
                self._windows_jobs.pop(process, None)
                failure = str(exc)
                if cleanup_errors:
                    failure += f"; cleanup failures: {'; '.join(cleanup_errors)}"
                self._windows_custody_failures[process] = failure
                raise RuntimeError(
                    f"Windows Job Object status verification failed closed: {failure}"
                ) from exc
            if active_processes != 0:
                return False
            try:
                job.close()
            except BaseException as exc:
                self._windows_jobs.pop(process, None)
                self._windows_custody_failures[process] = str(exc)
                raise RuntimeError(f"Windows Job Object close verification failed: {exc}") from exc
            self._windows_jobs.pop(process, None)
            self._windows_released.add(process)
            return True
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        return False


class CodexLiveProducerAdapter:
    def __init__(
        self,
        *,
        custody_root: Path,
        codex_executable: Path,
        access_token: str | None = None,
        host: Any | None = None,
        command_timeout_seconds: int = 3600,
    ) -> None:
        if (
            not isinstance(command_timeout_seconds, int)
            or isinstance(command_timeout_seconds, bool)
            or command_timeout_seconds < 1
        ):
            raise ValueError("positive integer command timeout required")
        self.root = Path(os.path.abspath(custody_root))
        self.executable = Path(os.path.abspath(codex_executable))
        self._access_token = access_token
        self._credential: str | None = None
        self._credential_transport_mode: str | None = None
        self._managed_auth_home: Path | None = None
        self.host = host or SubprocessCodexHost()
        self.timeout = command_timeout_seconds
        self._capability: dict[str, object] | None = None
        self._prepared: dict[str, dict[str, Any]] = {}
        self._handles: dict[str, dict[str, Any]] = {}
        self._ordered_cases: list[str] = []
        self._isolated_root_owner: tuple[Path, DirectoryIdentity] | None = None
        self._owned_workers: dict[Path, DirectoryIdentity] = {}
        self._cohort_deadline_monotonic: float | None = None

    def configured_command_timeout_seconds(self) -> int:
        return self.timeout

    def _remove_owned_worker_path(self, path: Path, identity: DirectoryIdentity) -> None:
        recorded = self._owned_workers.get(path)
        if recorded is None:
            if _lstat_optional(path) is None:
                return
            raise IsolationCleanupError(
                f"OWNED_ISOLATION_CLEANUP_UNSAFE: {path.name} has no invocation ownership record"
            )
        if recorded != identity:
            raise IsolationCleanupError(
                f"OWNED_ISOLATION_CLEANUP_UNSAFE: {path.name} ownership record drift"
            )
        observed = _require_owned_directory(path, identity, path.name)
        if observed is None:
            self._owned_workers.pop(path, None)
            return
        try:
            shutil.rmtree(path)
        except OSError as exc:
            raise IsolationCleanupError(
                f"OWNED_ISOLATION_CLEANUP_INCOMPLETE: {path.name} removal failed"
            ) from exc
        if _lstat_optional(path) is not None:
            raise IsolationCleanupError(
                f"OWNED_ISOLATION_CLEANUP_INCOMPLETE: {path.name} still exists after removal"
            )
        self._owned_workers.pop(path, None)

    def _remove_owned_worker(self, row: dict[str, Any]) -> None:
        path = row.get("worker_root")
        identity = row.get("worker_identity")
        if not isinstance(path, Path) or not isinstance(identity, DirectoryIdentity):
            raise IsolationCleanupError(
                "OWNED_ISOLATION_CLEANUP_UNSAFE: worker creation identity unavailable"
            )
        self._remove_owned_worker_path(path, identity)

    def _remove_owned_root_if_ready(self) -> None:
        if self._owned_workers or self._isolated_root_owner is None:
            return
        path, identity = self._isolated_root_owner
        observed = _require_owned_directory(path, identity, "isolation root")
        if observed is None:
            self._isolated_root_owner = None
            return
        witness_path = path / _OWNERSHIP_WITNESS_NAME
        try:
            entries = list(path.iterdir())
        except OSError as exc:
            raise IsolationCleanupError(
                "OWNED_ISOLATION_CLEANUP_INCOMPLETE: isolation root inventory failed"
            ) from exc
        if entries != [witness_path]:
            raise IsolationCleanupError(
                "OWNED_ISOLATION_CLEANUP_UNSAFE: isolation root contains non-witness entries"
            )
        _require_owned_directory(path, identity, "isolation root")
        try:
            witness_path.unlink()
        except OSError as exc:
            raise IsolationCleanupError(
                "OWNED_ISOLATION_CLEANUP_INCOMPLETE: isolation root ownership witness removal failed"
            ) from exc
        if _lstat_optional(witness_path) is not None:
            raise IsolationCleanupError(
                "OWNED_ISOLATION_CLEANUP_INCOMPLETE: isolation root ownership witness still exists"
            )
        current = _regular_directory_stat(path, "isolation root")
        if (current.st_dev, current.st_ino) != (
            identity.directory_device,
            identity.directory_inode,
        ):
            raise IsolationCleanupError(
                "OWNED_ISOLATION_CLEANUP_UNSAFE: isolation root changed before final removal"
            )
        try:
            path.rmdir()
        except OSError as exc:
            try:
                current = _regular_directory_stat(path, "isolation root")
                if (current.st_dev, current.st_ino) != (
                    identity.directory_device,
                    identity.directory_inode,
                ):
                    raise IsolationCleanupError(
                        "OWNED_ISOLATION_CLEANUP_UNSAFE: isolation root changed after final removal failure"
                    )
                if list(path.iterdir()):
                    raise IsolationCleanupError(
                        "OWNED_ISOLATION_CLEANUP_UNSAFE: isolation root changed after ownership witness removal"
                    )
                created_witness = _write_once(
                    witness_path,
                    secrets.token_bytes(_OWNERSHIP_WITNESS_BYTE_COUNT),
                )
                witness = _ownership_witness_identity(
                    witness_path,
                    "isolation root",
                )
                if witness != tuple(created_witness):
                    raise IsolationCleanupError(
                        "OWNED_ISOLATION_CLEANUP_UNSAFE: renewed isolation root ownership witness changed before adoption"
                    )
                replacement = DirectoryIdentity(
                    current.st_dev,
                    current.st_ino,
                    *witness,
                )
                if (replacement.directory_device, replacement.directory_inode) != (
                    identity.directory_device,
                    identity.directory_inode,
                ):
                    raise IsolationCleanupError(
                        "OWNED_ISOLATION_CLEANUP_UNSAFE: isolation root changed during ownership witness recovery"
                    )
                self._isolated_root_owner = (path, replacement)
            except BaseException as recovery_exc:
                raise IsolationCleanupError(
                    "OWNED_ISOLATION_CLEANUP_INCOMPLETE: isolation root ownership witness recovery failed closed"
                ) from recovery_exc
            raise IsolationCleanupError(
                "OWNED_ISOLATION_CLEANUP_INCOMPLETE: isolation root is not empty or could not be removed"
            ) from exc
        if _lstat_optional(path) is not None:
            raise IsolationCleanupError(
                "OWNED_ISOLATION_CLEANUP_INCOMPLETE: isolation root still exists after removal"
            )
        self._isolated_root_owner = None

    def _cleanup_isolation_custody(self) -> None:
        errors: list[str] = []
        for path, identity in reversed(list(self._owned_workers.items())):
            try:
                self._remove_owned_worker_path(path, identity)
            except IsolationCleanupError as exc:
                errors.append(str(exc))
        if not self._owned_workers:
            try:
                self._remove_owned_root_if_ready()
            except IsolationCleanupError as exc:
                errors.append(str(exc))
        if errors:
            raise IsolationCleanupError("; ".join(errors))

    def _token(self) -> str:
        token = self._access_token or os.environ.get("CODEX_ACCESS_TOKEN")
        if token:
            if self._credential_transport_mode not in {
                None,
                _DEDICATED_AGENT_IDENTITY_ENV,
            }:
                raise RuntimeError("Codex credential transport mode changed during cohort")
            self._credential_transport_mode = _DEDICATED_AGENT_IDENTITY_ENV
            self._credential = token
            return token
        raise RuntimeError("dedicated Codex Agent Identity credential unavailable")

    def _managed_auth_home_if_available(self) -> Path | None:
        auth = Path.home() / ".codex/auth.json"
        observed = _lstat_optional(auth)
        auth_home = auth.parent
        home_observed = _lstat_optional(auth_home)
        if not (
            observed is not None
            and stat.S_ISREG(observed.st_mode)
            and not stat.S_ISLNK(observed.st_mode)
            and not bool(getattr(observed, "st_file_attributes", 0) & _REPARSE_POINT)
            and observed.st_size > 0
            and home_observed is not None
            and stat.S_ISDIR(home_observed.st_mode)
            and not stat.S_ISLNK(home_observed.st_mode)
            and not bool(getattr(home_observed, "st_file_attributes", 0) & _REPARSE_POINT)
        ):
            return None
        for component in (auth_home, *auth_home.parents):
            component_observed = _lstat_optional(component)
            if (
                component_observed is None
                or not stat.S_ISDIR(component_observed.st_mode)
                or stat.S_ISLNK(component_observed.st_mode)
                or bool(
                    getattr(component_observed, "st_file_attributes", 0)
                    & _REPARSE_POINT
                )
            ):
                return None
        return Path(os.path.abspath(auth_home))

    def _credential_transport(self) -> tuple[str, str | Path]:
        if (
            isinstance(self._access_token, str)
            and bool(self._access_token)
        ) or "CODEX_ACCESS_TOKEN" in os.environ:
            mode = _DEDICATED_AGENT_IDENTITY_ENV
            transport: str | Path = self._token()
        else:
            auth_home = self._managed_auth_home_if_available()
            if auth_home is None:
                raise RuntimeError("Codex managed auth carrier unavailable")
            if self._managed_auth_home not in {None, auth_home}:
                raise RuntimeError("Codex managed auth home changed during cohort")
            mode = _MANAGED_AUTH_HOME
            transport = auth_home
            self._managed_auth_home = auth_home
        if self._credential_transport_mode not in {None, mode}:
            raise RuntimeError("Codex credential transport mode changed during cohort")
        self._credential_transport_mode = mode
        return mode, transport

    def _credential_carrier_available(self) -> bool:
        if isinstance(self._access_token, str) and bool(self._access_token):
            return True
        if "CODEX_ACCESS_TOKEN" in os.environ:
            return True
        return self._managed_auth_home_if_available() is not None

    def capability(self) -> dict[str, object]:
        probe = self.host.probe(
            self.executable,
            credential_carrier_available=self._credential_carrier_available(),
        )
        required = {
            "version",
            "executable_sha256",
            "catalog_row",
            "canonical_exec_flags",
            "credential_carrier_available",
        }
        if not isinstance(probe, dict) or set(probe) != required:
            raise RuntimeError("Codex capability probe shape invalid")
        catalog_row = probe["catalog_row"]
        if (
            not isinstance(catalog_row, dict)
            or set(catalog_row) != {"slug", "supported_reasoning_efforts"}
            or catalog_row.get("slug") != "gpt-5.5"
            or not isinstance(catalog_row.get("supported_reasoning_efforts"), list)
            or "high" not in catalog_row["supported_reasoning_efforts"]
            or probe["canonical_exec_flags"] != CANONICAL_EXEC_FLAGS
            or probe["credential_carrier_available"] is not True
        ):
            raise RuntimeError("Codex capability probe contract invalid")
        self._capability = {
            "schema": "reviewed-campaign-provider-capability-v1",
            "adapter_kind": "codex-live",
            "adapter_version": "codex-live-v1",
            "host_application_version": probe["version"],
            "codex_executable_sha256": probe["executable_sha256"],
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "test_only": False,
            "paid_provider_reachable": True,
            "live_execution_authorized": True,
        }
        return dict(self._capability)

    def prepare(self, auth: dict[str, Any], bindings: dict[str, Any], *, allow_test_fixture: bool = False) -> None:
        if self._capability is None:
            raise RuntimeError("capability must be established before preparation")
        if allow_test_fixture:
            if (
                self._capability.get("adapter_kind") != "codex-scripted-test-no-provider"
                or self._capability.get("test_only") is not True
                or self._capability.get("paid_provider_reachable") is not False
                or self._capability.get("live_execution_authorized") is not False
            ):
                raise RuntimeError("paid live adapter cannot use test fixtures")
        elif (
            self._capability.get("adapter_kind") != "codex-live"
            or self._capability.get("test_only") is not False
            or self._capability.get("paid_provider_reachable") is not True
            or self._capability.get("live_execution_authorized") is not True
        ):
            raise RuntimeError("test-only adapter cannot prepare production execution")
        if self._isolated_root_owner is not None or self._owned_workers or self._prepared:
            raise RuntimeError("live producer adapter already owns prepared isolation custody")
        package_root = _safe_join(self.root, auth["candidate_package_root"], "candidate_package_root")
        if not package_root.is_dir():
            raise ValueError("candidate package root unavailable")
        registry = bindings["registry"]
        cases = registry.get("cases")
        if not isinstance(cases, list) or len(cases) != 5:
            raise ValueError("exact canonical five-case registry required")
        expected_rows = auth["case_inputs"]
        actual_rows = [
            {
                "case_id": row.get("case_id"),
                "input_sha256": str(row.get("raw_sha256")).lower(),
            }
            for row in cases
        ]
        if actual_rows != expected_rows:
            raise ValueError("authorization case/input identity drift")
        output_contracts = bindings.get("producer_output_contracts")
        if not isinstance(output_contracts, dict) or list(output_contracts) != [row.get("case_id") for row in cases]:
            raise ValueError("exact ordered producer output contracts required")
        provider_settings = auth.get("provider_settings", {})
        if provider_settings.get("observation_protocol") != _PRODUCER_OBSERVATION_PROTOCOL:
            raise ValueError("authorization-bound concurrent observation protocol required")
        context_limit = provider_settings.get("effective_context_limit_bytes")
        if not isinstance(context_limit, int) or isinstance(context_limit, bool) or context_limit < 1:
            raise ValueError("positive authorization-bound effective context limit required")
        command_timeout_seconds = provider_settings.get("command_timeout_seconds")
        if (
            not isinstance(command_timeout_seconds, int)
            or isinstance(command_timeout_seconds, bool)
            or command_timeout_seconds < 1
            or command_timeout_seconds != self.timeout
        ):
            raise ValueError("live command timeout differs from authorization")
        authorization_window = auth.get("authorization_window")
        launch_not_after = (
            authorization_window.get("launch_not_after")
            if isinstance(authorization_window, dict)
            else None
        )
        if not isinstance(launch_not_after, str):
            raise ValueError("absolute cohort launch deadline unavailable")
        try:
            cohort_deadline = datetime.fromisoformat(launch_not_after.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("absolute cohort launch deadline invalid") from exc
        if cohort_deadline.tzinfo is None:
            raise ValueError("absolute cohort launch deadline must be timezone-aware")
        cohort_remaining = (cohort_deadline.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds()
        if cohort_remaining <= 0:
            raise ValueError("absolute cohort launch deadline elapsed")
        self._cohort_deadline_monotonic = time.monotonic() + cohort_remaining
        isolated_root = _safe_join(self.root, auth["isolated_root_prefix"], "isolated_root_prefix")
        prompt_root = _safe_join(self.root, auth["prompt_retention_root"], "prompt_retention_root")
        output_root = _safe_join(self.root, auth["output_retention_root"], "output_retention_root")
        provider_root = _safe_join(self.root, auth["provider_receipt_root"], "provider_receipt_root")
        capture_root = _safe_join(self.root, auth["structural_evidence_root"], "structural_evidence_root")
        source_tree_sha256 = tree_sha256(package_root)
        if not allow_test_fixture and source_tree_sha256 != auth["package_tree_sha256"]:
            raise ValueError("candidate package tree differs from authorization")
        self._ordered_cases = []
        try:
            isolated_identity = _create_owned_directory(
                isolated_root,
                "isolation root",
                parents=True,
            )
            self._isolated_root_owner = (isolated_root, isolated_identity)
            for index, row in enumerate(cases, 1):
                case_id = str(row["case_id"])
                worker_root = _safe_join(self.root, f"{auth['isolated_root_prefix']}/producer-{index:02d}", "worker_root")
                home = worker_root / "home"
                workspace = worker_root / "workspace"
                run_root = worker_root / "run"
                cache = worker_root / "cache"
                sqlite_home = worker_root / "sqlite"
                temp = worker_root / "temp"
                local_appdata = worker_root / "appdata/local"
                roaming_appdata = worker_root / "appdata/roaming"
                worker_identity = _create_owned_directory(
                    worker_root,
                    f"producer-{index:02d}",
                    parents=False,
                )
                self._owned_workers[worker_root] = worker_identity
                for directory in (home, run_root, cache, sqlite_home, temp, local_appdata, roaming_appdata):
                    directory.mkdir(parents=True, exist_ok=False)
                _copy_tree_exact(package_root, workspace)
                if tree_sha256(workspace) != source_tree_sha256:
                    raise ValueError("private candidate package copy drift")
                input_path = _safe_join(self.root, row["input_path"], f"input_{index}", file=True)
                raw_input = input_path.read_bytes()
                if (
                    len(raw_input) != row.get("raw_bytes")
                    or hashlib.sha256(raw_input).hexdigest() != str(row.get("raw_sha256")).lower()
                ):
                    raise ValueError(f"canonical input drift: {case_id}")
                private_input = run_root / "raw-input.bin"
                _write_once(private_input, raw_input)
                prepared_call = prepare_runtime_call(
                    package_root=workspace,
                    repo_root=ROOT,
                    run_dir=run_root,
                    call_index=1,
                    case_id=case_id,
                    stage="01-08",
                    raw_input_path=private_input,
                    previous_capsule_path=None,
                    harness_prompt=None,
                    validated_state=copy.deepcopy(EMPTY_VALIDATED_STATE),
                    source_commit=auth["source_commit"],
                    effective_context_limit=context_limit,
                    candidate_cap=16,
                    single_call_output_contract=output_contracts[case_id],
                )
                prompt_path = _retain_content_addressed(
                    prompt_root,
                    prepared_call.prompt_path.read_bytes(),
                    ".prompt.md",
                )
                retained_input = _retain_content_addressed(capture_root, raw_input, ".input.bin")
                retained_context = _retain_content_addressed(
                    capture_root,
                    prepared_call.context_path.read_bytes(),
                    ".runtime-context.json",
                )
                retained_parity = _retain_content_addressed(
                    capture_root,
                    prepared_call.parity_path.read_bytes(),
                    ".package-harness-parity.json",
                )
                capture_bindings = {
                    "raw_input": _ref(self.root, retained_input),
                    "exact_prompt": _ref(self.root, prompt_path),
                    "composite_runtime_context": _ref(self.root, retained_context),
                    "package_harness_parity": _ref(self.root, retained_parity),
                }
                self._prepared[case_id] = {
                    "case_id": case_id, "worker": f"producer-{index:02d}", "worker_root": worker_root, "home": home,
                    "worker_identity": worker_identity,
                    "workspace": workspace, "run_root": run_root, "cache": cache, "sqlite_home": sqlite_home, "temp": temp,
                    "local_appdata": local_appdata, "roaming_appdata": roaming_appdata,
                    "prompt": prompt_path, "input": retained_input, "output_root": output_root,
                    "provider_root": provider_root, "capture_root": capture_root,
                    "runtime_context": retained_context, "package_harness_parity": retained_parity,
                    "capture_bindings": capture_bindings,
                    "single_call_output_contract": copy.deepcopy(output_contracts[case_id]),
                    "candidate_id": auth["candidate_id"], "source_commit": auth["source_commit"],
                    "package_sha256": auth["package_sha256"],
                    "package_tree_sha256": auth["package_tree_sha256"],
                    "command_timeout_seconds": command_timeout_seconds,
                    "state": "NOT_SUBMITTED", "result": None, "started_at": None,
                    "ended_at": None, "host_invocation_id": None,
                    "launch_deadline_monotonic": None,
                    "credential_scan_status": "PENDING", "credential_scan_evidence": None,
                    "pre_admission_diagnostic": None,
                    "terminal_cause": None,
                    "terminal_failure_kind": None,
                    "terminal_host_returncode": None,
                    "outcome_unknown_diagnostic": None,
                }
                self._ordered_cases.append(case_id)
        except BaseException as exc:
            cleanup_error: IsolationCleanupError | None = None
            try:
                self._cleanup_isolation_custody()
            except IsolationCleanupError as caught:
                cleanup_error = caught
            self._prepared.clear()
            self._ordered_cases.clear()
            if cleanup_error is not None:
                raise IsolationCleanupError(
                    f"OWNED_ISOLATION_CLEANUP_FAILED_CLOSED: {cleanup_error}"
                ) from exc
            raise

    def _start_pending(self, execution_custody: dict[str, object]) -> tuple[str, dict[str, Any]]:
        case_id = str(execution_custody.get("case_id"))
        prepared = self._prepared.get(case_id)
        if prepared is None:
            raise RuntimeError("unprepared live producer case")
        if prepared.get("state") != "NOT_SUBMITTED":
            raise RuntimeError("live producer case was already submitted")
        if execution_custody.get("model") != "gpt-5.5" or execution_custody.get("reasoning_effort") != "high":
            raise RuntimeError("live model identity drift")
        if (
            execution_custody.get("single_call_output_contract") != prepared["single_call_output_contract"]
            or execution_custody.get("capture_bindings") != prepared["capture_bindings"]
        ):
            raise RuntimeError("live pre-dispatch capture binding drift")
        provider_settings = execution_custody.get("provider_settings")
        command_timeout_seconds = (
            provider_settings.get("command_timeout_seconds")
            if isinstance(provider_settings, dict)
            else None
        )
        if (
            not isinstance(command_timeout_seconds, int)
            or isinstance(command_timeout_seconds, bool)
            or command_timeout_seconds < 1
            or command_timeout_seconds != prepared.get("command_timeout_seconds")
            or command_timeout_seconds != self.timeout
        ):
            raise RuntimeError("live command timeout custody drift")
        if (
            provider_settings.get("observation_protocol") != _PRODUCER_OBSERVATION_PROTOCOL
            or not isinstance(execution_custody.get("usage_reservation_sha256"), str)
            or re.fullmatch(r"[a-f0-9]{64}", execution_custody["usage_reservation_sha256"]) is None
        ):
            raise RuntimeError("live usage reservation or observation protocol custody drift")
        custody_path = _retain_content_addressed(
            prepared["capture_root"],
            _canonical(execution_custody),
            ".execution-custody.json",
        )
        custody_ref = _ref(self.root, custody_path)
        run_root = prepared["run_root"]
        output = run_root / "raw-output.md"
        events = run_root / "codex-events.jsonl"
        stderr = run_root / "codex-stderr.txt"
        command = [
            str(self.executable), "exec", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "-C", str(prepared["workspace"]), "-s", "read-only", "-m", "gpt-5.5",
            "-c", 'model_reasoning_effort="high"', "-c", 'approval_policy="never"',
            "-c", "shell_environment_policy.inherit=none", "-c", 'cli_auth_credentials_store="file"',
            "--output-last-message", str(output), "-",
        ]
        credential_transport_mode, credential_transport = self._credential_transport()
        env = {
            key: value
            for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH")
            if (value := os.environ.get(key))
        }
        private_home = prepared["home"].as_posix()
        env.update(
            {
                "HOME": private_home,
                "USERPROFILE": private_home,
                "CODEX_HOME": (
                    str(credential_transport)
                    if credential_transport_mode == _MANAGED_AUTH_HOME
                    else private_home
                ),
                "CODEX_SQLITE_HOME": prepared["sqlite_home"].as_posix(),
                "TEMP": prepared["temp"].as_posix(),
                "TMP": prepared["temp"].as_posix(),
                "LOCALAPPDATA": prepared["local_appdata"].as_posix(),
                "APPDATA": prepared["roaming_appdata"].as_posix(),
                "XDG_CACHE_HOME": prepared["cache"].as_posix(),
            }
        )
        if credential_transport_mode == _DEDICATED_AGENT_IDENTITY_ENV:
            env["CODEX_ACCESS_TOKEN"] = str(credential_transport)
        started_at = _utc_now()
        started_monotonic = time.monotonic()
        launch_deadline = started_monotonic + float(command_timeout_seconds)
        if self._cohort_deadline_monotonic is not None:
            launch_deadline = min(launch_deadline, self._cohort_deadline_monotonic)
        if launch_deadline <= started_monotonic:
            raise RuntimeError("absolute cohort launch deadline elapsed before dispatch")
        prepared.update(
            {
                "state": "SUBMITTING",
                "started_at": started_at,
                "launch_deadline_monotonic": launch_deadline,
            }
        )
        attempt_row: dict[str, Any] = {
            **prepared,
            "process": None,
            "events": events,
            "stderr": stderr,
            "output": output,
            "started_at": started_at,
            "launch_deadline_monotonic": launch_deadline,
            "execution_custody_sha256": hashlib.sha256(_canonical(execution_custody)).hexdigest(),
            "execution_custody": custody_ref,
            "case_id": case_id,
            "event_bytes_seen": b"",
            "in_flight_admission": None,
            "admission_thread_id": None,
        }
        try:
            process = self.host.start(
                command, cwd=prepared["workspace"], env=env, prompt_path=prepared["prompt"],
                event_log_path=events, stderr_path=stderr, output_path=output, worker=prepared["worker"],
            )
        except BaseException as exc:
            process = getattr(exc, "process", None)
            if process is None:
                self._fail_pre_admission(
                    attempt_row,
                    failure_kind="HOST_START_FAILED_BEFORE_PROCESS_IDENTITY",
                    host_returncode=None,
                )
            else:
                handle = f"codex-host:{process.pid}:{case_id}"
                attempt_row.update({"process": process, "host_invocation_id": handle})
                self._handles[handle] = attempt_row
                self._fail_pre_admission(
                    attempt_row,
                    failure_kind="HOST_START_FAILED_AFTER_PROCESS_CREATION",
                    host_returncode=process.poll(),
                )
            raise
        handle = f"codex-host:{process.pid}:{case_id}"
        prepared.update({"state": "PENDING_STRUCTURED_ADMISSION", "host_invocation_id": handle})
        attempt_row.update(
            {
                "state": "PENDING_STRUCTURED_ADMISSION",
                "process": process,
                "host_invocation_id": handle,
            }
        )
        self._handles[handle] = attempt_row
        return handle, self._handles[handle]

    def _advance_structured_admission(self, row: dict[str, Any]) -> tuple[str, bytes] | None:
        try:
            raw = row["events"].read_bytes()
        except OSError as exc:
            raise RuntimeError("Codex structured in-flight admission carrier unavailable") from exc
        previous = row.get("event_bytes_seen")
        if not isinstance(previous, bytes) or not raw.startswith(previous):
            raise RuntimeError("Codex structured in-flight admission carrier changed non-append-only")
        row["event_bytes_seen"] = raw
        prefix, events = _complete_jsonl_prefix(raw)
        thread_rows = [event for event in events if event.get("type") == "thread.started"]
        if len(thread_rows) > 1:
            raise RuntimeError("Codex structured in-flight admission identity is ambiguous")
        if thread_rows:
            thread_index = next(
                index for index, event in enumerate(events)
                if event.get("type") == "thread.started"
            )
            if any(
                event.get("type") in {
                    "turn.started", "turn.completed", "turn.failed", "error",
                }
                for event in events[:thread_index]
            ):
                raise RuntimeError(
                    "Codex turn or terminal event preceded structured in-flight admission"
                )
        if any(event.get("type") in {"turn.failed", "error"} for event in events):
            raise RuntimeError("Codex failure event preceded structured in-flight admission")
        if any(event.get("type") == "turn.completed" for event in events):
            raise RuntimeError("Codex terminal event preceded structured in-flight admission")
        if not thread_rows:
            return None
        thread_id = thread_rows[0].get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            raise RuntimeError("Codex structured in-flight admission identity is invalid")
        return thread_id, prefix

    @staticmethod
    def _optional_carrier_bytes(path: Path, label: str) -> tuple[bool, bytes]:
        observed = _lstat_optional(path)
        if observed is None:
            return False, b""
        if (
            not stat.S_ISREG(observed.st_mode)
            or stat.S_ISLNK(observed.st_mode)
            or bool(getattr(observed, "st_file_attributes", 0) & _REPARSE_POINT)
        ):
            raise RuntimeError(f"{label} must be a regular non-reparse file")
        try:
            return True, path.read_bytes()
        except OSError as exc:
            raise RuntimeError(f"{label} readback failed") from exc

    @staticmethod
    def _terminal_carrier_specs(row: dict[str, Any]) -> tuple[tuple[str, Path | None, str], ...]:
        prefix = "pre-admission" if row.get("state") == "DISPATCH_UNKNOWN" else "outcome-unknown"
        return (
            ("raw_event_log", row.get("events"), f".{prefix}.events.jsonl"),
            ("stderr", row.get("stderr"), f".{prefix}.stderr.txt"),
            ("raw_output", row.get("output"), f".{prefix}.output.md"),
        )

    def _retain_safe_terminal_carriers_before_purge(
        self,
        row: dict[str, Any],
    ) -> dict[str, str]:
        existing = row.get("safe_terminal_carrier_custody")
        if existing is not None:
            if (
                not isinstance(existing, dict)
                or set(existing) != {"outcomes", "references"}
                or not isinstance(existing.get("outcomes"), dict)
                or set(existing["outcomes"]) != set(_SAFE_CARRIER_ROLES)
                or not isinstance(existing.get("references"), dict)
            ):
                raise RuntimeError("safe terminal carrier custody changed before replay")
            return copy.deepcopy(existing["outcomes"])
        outcomes: dict[str, str] = {}
        references: dict[str, dict[str, object]] = {}
        for role, path, suffix in self._terminal_carrier_specs(row):
            present = False
            raw = b""
            safe = False
            try:
                if not isinstance(path, Path):
                    raise RuntimeError(f"{role} path unavailable")
                present, raw = self._optional_carrier_bytes(
                    path,
                    f"secret-safe pre-purge {role}",
                )
                if present:
                    _classify_managed_auth_bytes(raw)
                safe = True
            except BaseException:
                outcomes[role] = "UNSAFE_OR_UNPROVEN"
                raw = b""
            if safe:
                outcomes[role] = (
                    "RETAINED_SECRET_SAFE" if present else "SOURCE_ABSENT"
                )
            try:
                retained_path = _retain_content_addressed(
                    row["provider_root"],
                    raw,
                    suffix,
                )
            except BaseException:
                if safe:
                    outcomes[role] = "PUBLICATION_FAILED"
                continue
            references[role] = _ref(self.root, retained_path)
        custody = {"outcomes": outcomes, "references": references}
        row["safe_terminal_carrier_custody"] = copy.deepcopy(custody)
        prepared = self._prepared.get(row["case_id"])
        if prepared is not None:
            prepared["safe_terminal_carrier_custody"] = copy.deepcopy(custody)
        return outcomes

    @staticmethod
    def _safe_carrier_disposition(row: dict[str, Any]) -> str:
        custody = row.get("safe_terminal_carrier_custody")
        if not isinstance(custody, dict) or not isinstance(custody.get("outcomes"), dict):
            return "PURGED_UNRETAINED"
        outcomes = custody["outcomes"]
        if set(outcomes) != set(_SAFE_CARRIER_ROLES):
            return "PURGED_UNRETAINED"
        values = list(outcomes.values())
        if all(value in {"RETAINED_SECRET_SAFE", "SOURCE_ABSENT"} for value in values):
            return "SAFE_RETAINED_BEFORE_PURGE"
        if any(value == "RETAINED_SECRET_SAFE" for value in values):
            return "PARTIAL_SAFE_RETENTION_BEFORE_PURGE"
        return "PURGED_UNRETAINED"

    def _retained_safe_carrier(
        self,
        row: dict[str, Any],
        role: str,
        suffix: str,
    ) -> tuple[bool, dict[str, object]]:
        custody = row.get("safe_terminal_carrier_custody")
        outcome = None
        reference = None
        if isinstance(custody, dict):
            outcomes = custody.get("outcomes")
            references = custody.get("references")
            if isinstance(outcomes, dict):
                outcome = outcomes.get(role)
            if isinstance(references, dict):
                reference = references.get(role)
        if isinstance(reference, dict):
            path = _safe_join(
                self.root,
                reference.get("path"),
                f"secret-safe retained {role}",
                file=True,
            )
            if _ref(self.root, path) != reference or not path.name.endswith(suffix):
                raise RuntimeError(f"secret-safe retained {role} identity changed")
        else:
            path = _retain_content_addressed(row["provider_root"], b"", suffix)
            reference = _ref(self.root, path)
        return outcome == "RETAINED_SECRET_SAFE", copy.deepcopy(reference)

    def _retain_pre_admission_diagnostic(
        self,
        row: dict[str, Any],
        *,
        failure_kind: str,
        host_returncode: int | None,
        credential_scan: dict[str, object] | None,
        carrier_disposition: str,
        cleanup_residual_witness: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if not isinstance(failure_kind, str) or not failure_kind:
            raise RuntimeError("pre-admission diagnostic failure kind unavailable")
        if host_returncode is not None and (
            not isinstance(host_returncode, int) or isinstance(host_returncode, bool)
        ):
            raise RuntimeError("pre-admission diagnostic host return code invalid")
        if carrier_disposition not in {
            "RETAINED",
            "SAFE_RETAINED_BEFORE_PURGE",
            "PARTIAL_SAFE_RETENTION_BEFORE_PURGE",
            "PURGED_UNRETAINED",
            "UNAVAILABLE",
        }:
            raise RuntimeError("pre-admission carrier disposition unavailable")
        source_presence: dict[str, bool] = {}
        retained: dict[str, dict[str, object]] = {}
        for role, path, suffix in (
            ("raw_event_log", row.get("events"), ".pre-admission.events.jsonl"),
            ("stderr", row.get("stderr"), ".pre-admission.stderr.txt"),
            ("raw_output", row.get("output"), ".pre-admission.output.md"),
        ):
            if carrier_disposition == "RETAINED":
                if not isinstance(path, Path):
                    raise RuntimeError(f"pre-admission {role} path unavailable")
                present, raw = self._optional_carrier_bytes(path, f"pre-admission {role}")
                try:
                    retained_path = _retain_content_addressed(row["provider_root"], raw, suffix)
                except BaseException as exc:
                    raise _DiagnosticRetentionFailure(role, exc) from exc
                reference = _ref(self.root, retained_path)
            elif carrier_disposition == "UNAVAILABLE":
                present, raw = False, b""
                try:
                    retained_path = _retain_content_addressed(row["provider_root"], raw, suffix)
                except BaseException as exc:
                    raise _DiagnosticRetentionFailure(role, exc) from exc
                reference = _ref(self.root, retained_path)
            else:
                present, reference = self._retained_safe_carrier(
                    row,
                    role,
                    suffix,
                )
            source_presence[role] = present
            retained[role] = reference
        execution_custody = row.get("execution_custody")
        execution_custody_sha256 = row.get("execution_custody_sha256")
        if (
            not isinstance(execution_custody, dict)
            or set(execution_custody) != {"path", "byte_count", "sha256"}
            or not isinstance(execution_custody_sha256, str)
            or execution_custody.get("sha256") != execution_custody_sha256
        ):
            raise RuntimeError("pre-admission execution custody unavailable")
        diagnostic = {
            "schema": (
                "reviewed-campaign-pre-admission-diagnostic-v2"
                if isinstance(row.get("safe_terminal_carrier_custody"), dict)
                else "reviewed-campaign-pre-admission-diagnostic-v1"
            ),
            "status": "PRE_ADMISSION_DIAGNOSTIC_RETAINED",
            "failure_kind": failure_kind,
            "candidate_id": row["candidate_id"],
            "source_commit": row["source_commit"],
            "package_sha256": row["package_sha256"],
            "package_tree_sha256": row["package_tree_sha256"],
            "case_id": row["case_id"],
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "dispatch_classification": "DISPATCH_UNKNOWN",
            "admission_status": "NOT_ADMITTED",
            "provider_invocation_proven": False,
            "host_returncode": host_returncode,
            "host_returncode_status": "RECORDED" if host_returncode is not None else "UNAVAILABLE",
            "host_invocation_id": row.get("host_invocation_id"),
            "started_at": row.get("started_at"),
            "ended_at": row.get("ended_at"),
            "carrier_disposition": carrier_disposition,
            "source_presence": source_presence,
            **retained,
            "credential_residue_scan": copy.deepcopy(credential_scan),
            **(
                {"cleanup_residual_witness": copy.deepcopy(cleanup_residual_witness)}
                if cleanup_residual_witness is not None
                else {}
            ),
            "execution_custody_sha256": execution_custody_sha256,
            "execution_custody": copy.deepcopy(execution_custody),
            "captured_at": _utc_now(),
        }
        try:
            diagnostic_path = _retain_content_addressed(
                row["provider_root"],
                _canonical(diagnostic),
                ".pre-admission-diagnostic.json",
            )
        except BaseException as exc:
            raise _DiagnosticRetentionFailure("diagnostic", exc) from exc
        return _ref(self.root, diagnostic_path)

    def _retain_pre_admission_retention_failure(
        self,
        row: dict[str, Any],
        *,
        original_failure_kind: str,
        host_returncode: int | None,
        credential_scan: dict[str, object],
        retention_failure: _DiagnosticRetentionFailure,
    ) -> dict[str, object]:
        retained: dict[str, dict[str, object]] = {}
        for role, suffix in (
            ("raw_event_log", ".pre-admission.events.jsonl"),
            ("stderr", ".pre-admission.stderr.txt"),
            ("raw_output", ".pre-admission.output.md"),
        ):
            retained_path = _retain_content_addressed(row["provider_root"], b"", suffix)
            retained[role] = _ref(self.root, retained_path)
        diagnostic = {
            "schema": "reviewed-campaign-pre-admission-diagnostic-v1",
            "status": "PRE_ADMISSION_DIAGNOSTIC_RETENTION_FAILED_CLOSED",
            "failure_kind": original_failure_kind,
            "candidate_id": row["candidate_id"],
            "source_commit": row["source_commit"],
            "package_sha256": row["package_sha256"],
            "package_tree_sha256": row["package_tree_sha256"],
            "case_id": row["case_id"],
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "dispatch_classification": "DISPATCH_UNKNOWN",
            "admission_status": "NOT_ADMITTED",
            "provider_invocation_proven": False,
            "host_returncode": host_returncode,
            "host_returncode_status": "RECORDED" if host_returncode is not None else "UNAVAILABLE",
            "host_invocation_id": row.get("host_invocation_id"),
            "started_at": row.get("started_at"),
            "ended_at": row.get("ended_at"),
            "carrier_disposition": "RETENTION_FAILED",
            "source_presence": {
                "raw_event_log": False,
                "stderr": False,
                "raw_output": False,
            },
            **retained,
            "credential_residue_scan": copy.deepcopy(credential_scan),
            "execution_custody_sha256": row["execution_custody_sha256"],
            "execution_custody": copy.deepcopy(row["execution_custody"]),
            "captured_at": _utc_now(),
            "retention_failure": {
                "schema": "reviewed-campaign-diagnostic-retention-failure-v1",
                "status": "FAILED_CLOSED",
                "failed_role": retention_failure.role,
                "error_class": retention_failure.error_class,
                "retained_original_carriers": False,
            },
        }
        diagnostic_path = _retain_content_addressed(
            row["provider_root"],
            _canonical(diagnostic),
            ".pre-admission-diagnostic.json",
        )
        return _ref(self.root, diagnostic_path)

    def _retain_cleanup_residual_witness(
        self,
        row: dict[str, Any],
        *,
        failure_kind: str,
        residual_kind: str,
    ) -> dict[str, object]:
        execution_custody_sha256 = row.get("execution_custody_sha256")
        if (
            not isinstance(execution_custody_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", execution_custody_sha256) is None
        ):
            raise RuntimeError("cleanup residual execution custody unavailable")
        witness = {
            "schema": "reviewed-campaign-cleanup-residual-witness-v1",
            "status": "CLEANUP_INCOMPLETE",
            "failure_kind": failure_kind,
            "residual_kind": residual_kind,
            "case_id": row["case_id"],
            "worker": row["worker"],
            "execution_custody_sha256": execution_custody_sha256,
            "retained_original_carriers": False,
        }
        witness_path = _retain_content_addressed(
            row["provider_root"],
            _canonical(witness),
            ".cleanup-residual-witness.json",
        )
        return _ref(self.root, witness_path)

    def _fail_pre_admission(
        self,
        row: dict[str, Any],
        *,
        failure_kind: str,
        host_returncode: int | None,
    ) -> None:
        self._mark_dispatch_unknown(row)
        process = row.get("process")
        if process is not None:
            try:
                self._teardown_process(process)
            except BaseException as exc:
                cleanup_failure_kind = "PROCESS_TEARDOWN_UNVERIFIED"
                witness = self._retain_cleanup_residual_witness(
                    row,
                    failure_kind=cleanup_failure_kind,
                    residual_kind="PROCESS_GENERATION",
                )
                diagnostic = self._retain_pre_admission_diagnostic(
                    row,
                    failure_kind=cleanup_failure_kind,
                    host_returncode=host_returncode,
                    credential_scan=None,
                    carrier_disposition="UNAVAILABLE",
                    cleanup_residual_witness=witness,
                )
                row["pre_admission_diagnostic"] = diagnostic
                self._prepared[row["case_id"]]["pre_admission_diagnostic"] = copy.deepcopy(
                    diagnostic
                )
                self._record_terminal_cause(row, exc)
                raise RuntimeError("pre-admission process teardown remains unverified") from exc
        credential_error: BaseException | None = None
        carrier_disposition = "RETAINED"
        try:
            credential_scan = self._credential_readback(row)
        except BaseException as exc:
            credential_scan = row.get("credential_scan_evidence")
            if row.get("credential_scan_status") != "PURGED" or not isinstance(
                credential_scan,
                dict,
            ):
                cleanup_failure_kind = "CREDENTIAL_SCAN_AND_PURGE_FAILED"
                witness = self._retain_cleanup_residual_witness(
                    row,
                    failure_kind=cleanup_failure_kind,
                    residual_kind="OWNED_WORKER",
                )
                diagnostic = self._retain_pre_admission_diagnostic(
                    row,
                    failure_kind=cleanup_failure_kind,
                    host_returncode=host_returncode,
                    credential_scan=None,
                    carrier_disposition="UNAVAILABLE",
                    cleanup_residual_witness=witness,
                )
                row["pre_admission_diagnostic"] = diagnostic
                self._prepared[row["case_id"]]["pre_admission_diagnostic"] = copy.deepcopy(
                    diagnostic
                )
                self._record_terminal_cause(row, exc)
                raise RuntimeError("pre-admission credential scan and purge failed closed") from exc
            credential_error = exc
            carrier_disposition = self._safe_carrier_disposition(row)
        try:
            diagnostic = self._retain_pre_admission_diagnostic(
                row,
                failure_kind=failure_kind,
                host_returncode=host_returncode,
                credential_scan=credential_scan,
                carrier_disposition=carrier_disposition,
            )
        except _DiagnosticRetentionFailure as exc:
            if carrier_disposition != "RETAINED":
                raise
            diagnostic = self._retain_pre_admission_retention_failure(
                row,
                original_failure_kind=failure_kind,
                host_returncode=host_returncode,
                credential_scan=credential_scan,
                retention_failure=exc,
            )
            row["pre_admission_diagnostic"] = diagnostic
            self._prepared[row["case_id"]]["pre_admission_diagnostic"] = copy.deepcopy(
                diagnostic
            )
            self._record_terminal_cause(row, exc)
            raise RuntimeError("pre-admission diagnostic retention failed closed") from exc
        row["pre_admission_diagnostic"] = diagnostic
        self._prepared[row["case_id"]]["pre_admission_diagnostic"] = copy.deepcopy(diagnostic)
        if credential_error is not None:
            raise credential_error

    def _await_structured_admission(
        self,
        handle: str,
        row: dict[str, Any],
    ) -> dict[str, object]:
        while True:
            try:
                early_returncode = row["process"].poll()
            except BaseException as exc:
                self._fail_pre_admission(
                    row,
                    failure_kind="ADMISSION_LIVENESS_CHECK_FAILED",
                    host_returncode=None,
                )
                raise RuntimeError("Codex structured in-flight admission liveness check failed closed") from exc
            if early_returncode is not None:
                self._fail_pre_admission(
                    row,
                    failure_kind="HOST_EXITED_BEFORE_ADMISSION",
                    host_returncode=early_returncode,
                )
                raise RuntimeError(
                    f"Codex producer host exited before adapter in-flight admission ({early_returncode})"
                )
            try:
                admission = self._advance_structured_admission(row)
            except BaseException:
                self._fail_pre_admission(
                    row,
                    failure_kind="STRUCTURED_ADMISSION_INVALID",
                    host_returncode=row["process"].poll(),
                )
                raise
            if admission is not None:
                thread_id, admitted_prefix = admission
                after_parse_returncode = row["process"].poll()
                if after_parse_returncode is not None:
                    self._fail_pre_admission(
                        row,
                        failure_kind="HOST_EXITED_DURING_ADMISSION",
                        host_returncode=after_parse_returncode,
                    )
                    raise RuntimeError("Codex producer host exited before structured in-flight admission")
                try:
                    _classify_managed_auth_bytes(admitted_prefix)
                except BaseException:
                    self._fail_pre_admission(
                        row,
                        failure_kind="ADMISSION_EVIDENCE_UNSAFE_OR_UNPROVEN",
                        host_returncode=row["process"].poll(),
                    )
                    raise
                try:
                    retained_admission = _retain_content_addressed(
                        row["provider_root"],
                        admitted_prefix,
                        ".in-flight-admission.events.jsonl",
                    )
                except BaseException:
                    self._fail_pre_admission(
                        row,
                        failure_kind="ADMISSION_EVIDENCE_RETENTION_FAILED",
                        host_returncode=row["process"].poll(),
                    )
                    raise
                admission_ref = _ref(self.root, retained_admission)
                row.update(
                    {
                        "state": "ADAPTER_IN_FLIGHT",
                        "host_invocation_id": handle,
                        "in_flight_admission": admission_ref,
                        "admission_thread_id": thread_id,
                    }
                )
                self._prepared[row["case_id"]].update(
                    {
                        "state": "ADAPTER_IN_FLIGHT",
                        "host_invocation_id": handle,
                        "in_flight_admission": copy.deepcopy(admission_ref),
                        "admission_thread_id": thread_id,
                    }
                )
                return {
                    "handle_id": handle,
                    "execution_custody_sha256": row["execution_custody_sha256"],
                    "accepted": None,
                    "in_flight": True,
                    "acknowledgment_origin": "ADAPTER_IN_FLIGHT",
                    "started_at": row["started_at"],
                    "host_invocation_id": handle,
                }
            deadline = row.get("launch_deadline_monotonic")
            if not isinstance(deadline, (int, float)) or isinstance(deadline, bool):
                self._fail_pre_admission(
                    row,
                    failure_kind="ADMISSION_DEADLINE_UNAVAILABLE",
                    host_returncode=row["process"].poll(),
                )
                raise RuntimeError("Codex structured in-flight admission deadline unavailable")
            remaining = float(deadline) - time.monotonic()
            if remaining <= 0:
                self._fail_pre_admission(
                    row,
                    failure_kind="ADMISSION_TIMEOUT",
                    host_returncode=row["process"].poll(),
                )
                raise RuntimeError("Codex structured in-flight admission timed out")
            time.sleep(min(0.05, remaining))

    def submit(self, execution_custody: dict[str, object]) -> dict[str, object]:
        handle, row = self._start_pending(execution_custody)
        return self._await_structured_admission(handle, row)

    def submit_tail(
        self,
        execution_custodies: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        if not isinstance(execution_custodies, list) or len(execution_custodies) != 4:
            raise RuntimeError("exact four-case producer tail required")
        pending = [self._start_pending(execution_custody) for execution_custody in execution_custodies]
        return [self._await_structured_admission(handle, row) for handle, row in pending]

    @staticmethod
    def _wait_for_terminal_process(row: dict[str, Any]) -> int:
        deadline = row.get("launch_deadline_monotonic")
        if not isinstance(deadline, (int, float)) or isinstance(deadline, bool):
            raise RuntimeError("Codex producer launch deadline unavailable")
        remaining = float(deadline) - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired("Codex producer command", 0)
        return row["process"].wait(timeout=remaining)

    def observe_many(
        self,
        handles: list[str],
        execution_custodies: list[dict[str, object]],
    ) -> tuple[list[dict[str, object] | None], BaseException | None]:
        """Observe the canonical five concurrently, with coordinator-only mutation."""
        if (
            not isinstance(handles, list)
            or not isinstance(execution_custodies, list)
            or len(handles) != 5
            or len(execution_custodies) != 5
            or len(set(handles)) != 5
        ):
            raise RuntimeError("exact five unique live producer observations required")
        rows: list[dict[str, Any]] = []
        for index, (handle, custody) in enumerate(zip(handles, execution_custodies), 1):
            row = self._handles.get(handle)
            if row is None or custody.get("case_id") != self._ordered_cases[index - 1] or row.get("case_id") != custody.get("case_id"):
                raise RuntimeError("live producer observation handle/case order drift")
            provider_settings = custody.get("provider_settings")
            if not isinstance(provider_settings, dict) or provider_settings.get("observation_protocol") != _PRODUCER_OBSERVATION_PROTOCOL:
                raise RuntimeError("live producer concurrent observation protocol drift")
            expected_custody = hashlib.sha256(_canonical(custody)).hexdigest()
            if row.get("execution_custody_sha256") != expected_custody:
                raise RuntimeError("live producer observation custody drift")
            rows.append(row)

        results: list[dict[str, object] | None] = [None] * 5
        first_error: BaseException | None = None
        processed: set[int] = set()
        executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="daee-producer-observe")
        futures: dict[Future[int], int] = {}
        try:
            try:
                for index, row in enumerate(rows):
                    futures[executor.submit(self._wait_for_terminal_process, row)] = index
            except BaseException as exc:
                first_error = exc
                for row in rows:
                    self._record_terminal_cause(row, exc)
                for future in futures:
                    future.cancel()

            if first_error is None:
                for future in as_completed(futures):
                    index = futures[future]
                    processed.add(index)
                    try:
                        returncode = future.result()
                        if returncode != 0:
                            raise RuntimeError(f"Codex producer command exited {returncode}")
                        results[index] = self._observe_terminal(
                            handles[index],
                            execution_custodies[index],
                            terminal_returncode=returncode,
                        )
                    except BaseException as exc:
                        self._record_terminal_cause(rows[index], exc)
                        first_error = exc
                        break

            if first_error is None:
                executor.shutdown(wait=True, cancel_futures=False)
                return results, None

            teardown_errors: list[str] = []
            for row in rows:
                try:
                    self._teardown_process(row["process"])
                except BaseException as exc:
                    teardown_errors.append(str(exc))
            _done, not_done = wait(futures, timeout=_OBSERVATION_QUIESCENCE_SECONDS)
            if not_done:
                teardown_errors.append("observer tasks did not quiesce within the governed teardown bound")
            for future, index in futures.items():
                if index in processed or not future.done():
                    continue
                processed.add(index)
                try:
                    returncode = future.result()
                    if returncode == 0:
                        results[index] = self._observe_terminal(
                            handles[index],
                            execution_custodies[index],
                            terminal_returncode=returncode,
                        )
                    else:
                        raise RuntimeError(f"Codex producer command exited {returncode}")
                except BaseException as exc:
                    self._record_terminal_cause(rows[index], exc)

            for index, row in enumerate(rows):
                if results[index] is None and row.get("state") != "COMPLETED":
                    try:
                        if row.get("state") == "ADAPTER_IN_FLIGHT":
                            self._mark_outcome_unknown(row)
                        self._credential_readback(row)
                    except BaseException as exc:
                        self._record_terminal_cause(row, exc)
                        teardown_errors.append(str(exc))
                    if row.get("state") == "OUTCOME_UNKNOWN":
                        try:
                            self._ensure_outcome_unknown_diagnostic(row)
                        except BaseException as exc:
                            teardown_errors.append(str(exc))
                try:
                    self._remove_owned_worker(row)
                except BaseException as exc:
                    teardown_errors.append(str(exc))
            try:
                self._remove_owned_root_if_ready()
            except BaseException as exc:
                teardown_errors.append(str(exc))
            if teardown_errors:
                first_error = RuntimeError(
                    f"{first_error}; concurrent observation teardown failed: {'; '.join(teardown_errors)}"
                )
            return results, first_error
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def observe(self, handle: str, execution_custody: dict[str, object]) -> dict[str, object]:
        return self._observe_terminal(
            handle,
            execution_custody,
            terminal_returncode=None,
        )

    def _observe_terminal(
        self,
        handle: str,
        execution_custody: dict[str, object],
        *,
        terminal_returncode: int | None,
    ) -> dict[str, object]:
        row = self._handles.get(handle)
        if row is None:
            raise RuntimeError("unknown live producer handle")
        try:
            if terminal_returncode is None:
                deadline = row.get("launch_deadline_monotonic")
                if not isinstance(deadline, (int, float)) or isinstance(deadline, bool):
                    raise RuntimeError("Codex producer launch deadline unavailable")
                remaining = float(deadline) - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired("Codex producer command", 0)
                returncode = row["process"].wait(timeout=remaining)
            else:
                if (
                    not isinstance(terminal_returncode, int)
                    or isinstance(terminal_returncode, bool)
                    or row["process"].poll() != terminal_returncode
                ):
                    raise RuntimeError("Codex producer terminal wait readback drift")
                returncode = terminal_returncode
            if returncode != 0:
                raise RuntimeError(f"Codex producer command exited {returncode}")
            self._teardown_process(row["process"])
            credential_scan = self._credential_readback(row)
            events_raw = row["events"].read_bytes()
            prior_events = row.get("event_bytes_seen")
            if not isinstance(prior_events, bytes) or not events_raw.startswith(prior_events):
                raise RuntimeError("Codex JSONL event stream changed non-append-only after admission")
            complete_events_raw, parsed = _complete_jsonl_prefix(events_raw)
            if complete_events_raw != events_raw:
                raise RuntimeError("Codex JSONL event stream has an incomplete terminal record")
            thread_ids = [event.get("thread_id") for event in parsed if event.get("type") == "thread.started"]
            completed = [event for event in parsed if event.get("type") == "turn.completed"]
            failed = [event for event in parsed if event.get("type") in {"turn.failed", "error"}]
            if len(thread_ids) != 1 or not isinstance(thread_ids[0], str) or not thread_ids[0] or len(completed) != 1 or failed:
                raise RuntimeError("Codex completion identity unavailable or contradictory")
            admission_ref = row.get("in_flight_admission")
            if not isinstance(admission_ref, dict) or set(admission_ref) != {"path", "byte_count", "sha256"}:
                raise RuntimeError("Codex structured in-flight admission evidence unavailable")
            admission_path = _safe_join(self.root, admission_ref["path"], "in_flight_admission", file=True)
            admission_raw = admission_path.read_bytes()
            if (
                len(admission_raw) != admission_ref.get("byte_count")
                or hashlib.sha256(admission_raw).hexdigest() != admission_ref.get("sha256")
                or not events_raw.startswith(admission_raw)
                or row.get("admission_thread_id") != thread_ids[0]
            ):
                raise RuntimeError("Codex structured in-flight admission evidence drift")
            output = row["output"].read_bytes()
            if not output:
                raise RuntimeError("Codex raw output is empty")
            usage = completed[0].get("usage")
            if not isinstance(usage, dict):
                raise RuntimeError("Codex token usage unavailable")
            input_tokens = usage.get("input_tokens")
            cached_tokens = usage.get("cached_input_tokens")
            output_tokens = usage.get("output_tokens")
            token_values = (input_tokens, cached_tokens, output_tokens)
            if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in token_values):
                raise RuntimeError("Codex token usage invalid")
            if cached_tokens > input_tokens:
                raise RuntimeError("Codex cached token usage exceeds input usage")
            expected_custody = hashlib.sha256(_canonical(execution_custody)).hexdigest()
            if row["execution_custody_sha256"] != expected_custody:
                raise RuntimeError("execution custody changed before observation")
            retained_output = _retain_content_addressed(row["output_root"], output, ".output.md")
            retained_events = _retain_content_addressed(row["provider_root"], events_raw, ".events.jsonl")
            retained_stderr = _retain_content_addressed(row["provider_root"], row["stderr"].read_bytes(), ".stderr.txt")
            exact_usage = {
                "status": "RECORDED", "input_tokens": input_tokens,
                "cached_input_tokens": cached_tokens, "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }
            exact_cost = {
                "unit": "usd", "value": "unknown", "status": "UNAVAILABLE",
                "reason": "provider-cost-not-present-in-retained-jsonl",
                "source": "codex-cli-jsonl-v1",
            }
            ended_at = _utc_now()
            capture = {
                "schema": "reviewed-campaign-live-capture-v1",
                "status": "CAPTURED",
                "candidate_id": row["candidate_id"],
                "source_commit": row["source_commit"],
                "package_sha256": row["package_sha256"],
                "package_tree_sha256": row["package_tree_sha256"],
                "case_id": execution_custody["case_id"],
                "prompt": _ref(self.root, row["prompt"]),
                "raw_input": _ref(self.root, row["input"]),
                "runtime_context": _ref(self.root, row["runtime_context"]),
                "package_harness_parity": _ref(self.root, row["package_harness_parity"]),
                "raw_output": _ref(self.root, retained_output),
                "raw_event_log": _ref(self.root, retained_events),
                "in_flight_admission": copy.deepcopy(admission_ref),
                "stderr": _ref(self.root, retained_stderr),
                "credential_residue_scan": credential_scan,
                "execution_custody_sha256": expected_custody,
                "execution_custody": copy.deepcopy(row["execution_custody"]),
                "completion_identity": {
                    "provider_call_id": f"codex-thread:{thread_ids[0]}",
                    "host_invocation_id": handle,
                    "started_at": row["started_at"],
                    "ended_at": ended_at,
                },
                "usage": exact_usage,
                "cost": exact_cost,
                "structural_status": "UNVERIFIED",
                "stage01_stage08_evidence": None,
            }
            capture_path = _retain_content_addressed(row["capture_root"], _canonical(capture), ".capture.json")
            result = {
                "content_utf8": output.decode("utf-8"),
                "capture_status": "CAPTURED",
                "capture_evidence": _ref(self.root, capture_path),
                "provider_call_id": f"codex-thread:{thread_ids[0]}",
                "execution_custody_sha256": expected_custody,
                "usage": exact_usage,
                "cost": exact_cost,
                "started_at": row["started_at"],
                "ended_at": ended_at,
                "host_invocation_id": handle,
                "accepted": None,
                "in_flight": False,
                "acknowledgment_origin": "ADAPTER_IN_FLIGHT",
                "raw_event_log": _ref(self.root, retained_events),
                "raw_output": _ref(self.root, retained_output),
                "stderr": _ref(self.root, retained_stderr),
                "prompt": _ref(self.root, row["prompt"]),
                "credential_residue_scan": credential_scan,
                "execution_custody": copy.deepcopy(row["execution_custody"]),
            }
            row.update(
                {"state": "COMPLETED", "ended_at": result["ended_at"], "result": result}
            )
            self._prepared[row["case_id"]].update(
                {"state": "COMPLETED", "ended_at": result["ended_at"], "result": result}
            )
            self._remove_owned_worker(row)
            self._remove_owned_root_if_ready()
        except subprocess.TimeoutExpired as exc:
            if row.get("state") != "COMPLETED":
                self._mark_outcome_unknown(row)
            self._record_terminal_cause(row, exc)
            self._teardown_process(row["process"])
            self._credential_readback(row)
            raise RuntimeError("Codex producer command timed out") from exc
        except BaseException as exc:
            if row.get("state") != "COMPLETED":
                self._mark_outcome_unknown(row)
            self._record_terminal_cause(row, exc)
            self._teardown_process(row["process"])
            self._credential_readback(row)
            raise
        return result

    def execution_bindings(self) -> dict[str, dict[str, object]]:
        if list(self._prepared) != self._ordered_cases:
            raise RuntimeError("prepared capture binding order is unavailable")
        return {
            case_id: copy.deepcopy(self._prepared[case_id]["capture_bindings"])
            for case_id in self._ordered_cases
        }

    def _mark_dispatch_unknown(self, row: dict[str, Any]) -> None:
        ended_at = _utc_now()
        row.update({"state": "DISPATCH_UNKNOWN", "ended_at": ended_at})
        self._prepared[row["case_id"]].update({"state": "DISPATCH_UNKNOWN", "ended_at": ended_at})

    def _mark_outcome_unknown(self, row: dict[str, Any]) -> None:
        prepared = self._prepared[row["case_id"]]
        if row.get("state") == "COMPLETED" or prepared.get("state") == "COMPLETED":
            raise RuntimeError("completed live producer result cannot be downgraded")
        ended_at = _utc_now()
        row.update({"state": "OUTCOME_UNKNOWN", "ended_at": ended_at})
        prepared.update({"state": "OUTCOME_UNKNOWN", "ended_at": ended_at})

    def _record_terminal_cause(self, row: dict[str, Any], error: BaseException) -> None:
        if row.get("terminal_cause") is not None:
            return
        cause = str(error) or type(error).__name__
        current: BaseException | None = error
        chain: list[BaseException] = []
        while current is not None and current not in chain:
            chain.append(current)
            next_error = current.__cause__ or current.__context__
            current = next_error if isinstance(next_error, BaseException) else None
        if any(isinstance(item, KeyboardInterrupt) for item in chain):
            failure_kind = "OBSERVATION_INTERRUPTED"
        elif any(isinstance(item, subprocess.TimeoutExpired) for item in chain):
            failure_kind = "HOST_TIMEOUT"
        elif any(isinstance(item, CredentialResidueError) for item in chain):
            failure_kind = "CREDENTIAL_RESIDUE"
        elif any(
            isinstance(item, ManagedCredentialScanAmbiguousError) for item in chain
        ):
            failure_kind = "CREDENTIAL_SCAN_AMBIGUOUS"
        elif "event stream" in cause or "completion identity" in cause:
            failure_kind = "TERMINAL_EVENT_STREAM_INVALID"
        else:
            process = row.get("process")
            try:
                returncode = process.poll() if process is not None else None
            except BaseException:
                returncode = None
            failure_kind = (
                "HOST_EXITED_NONZERO"
                if isinstance(returncode, int) and returncode != 0
                else "OBSERVATION_FAILED"
            )
        process = row.get("process")
        try:
            host_returncode = process.poll() if process is not None else None
        except BaseException:
            host_returncode = None
        row["terminal_cause"] = cause
        row["terminal_failure_kind"] = failure_kind
        row["terminal_host_returncode"] = host_returncode
        prepared = self._prepared.get(row["case_id"])
        if prepared is not None:
            prepared["terminal_cause"] = cause
            prepared["terminal_failure_kind"] = failure_kind
            prepared["terminal_host_returncode"] = host_returncode

    def _ensure_outcome_unknown_diagnostic(self, row: dict[str, Any]) -> dict[str, object]:
        retained = row.get("outcome_unknown_diagnostic")
        if retained is not None:
            if not isinstance(retained, dict):
                raise RuntimeError("outcome-unknown diagnostic reference invalid")
            return retained
        if row.get("state") != "OUTCOME_UNKNOWN":
            raise RuntimeError("outcome-unknown diagnostic requires exact terminal state")
        failure_kind = row.get("terminal_failure_kind")
        if not isinstance(failure_kind, str) or not failure_kind:
            raise RuntimeError("outcome-unknown failure kind unavailable")
        credential_scan = row.get("credential_scan_evidence")
        credential_status = row.get("credential_scan_status")
        if credential_status == "PASS":
            carrier_disposition = "RETAINED"
        elif credential_status in {"PURGED", "PURGE_INCOMPLETE"}:
            carrier_disposition = self._safe_carrier_disposition(row)
        else:
            raise RuntimeError("outcome-unknown credential scan evidence unavailable")
        if not isinstance(credential_scan, dict):
            raise RuntimeError("outcome-unknown credential scan reference invalid")
        source_presence: dict[str, bool] = {}
        carriers: dict[str, dict[str, object]] = {}
        for role, path, suffix in (
            ("raw_event_log", row.get("events"), ".outcome-unknown.events.jsonl"),
            ("stderr", row.get("stderr"), ".outcome-unknown.stderr.txt"),
            ("raw_output", row.get("output"), ".outcome-unknown.output.md"),
        ):
            if credential_status == "PASS":
                if not isinstance(path, Path):
                    raise RuntimeError(f"outcome-unknown {role} path unavailable")
                present, raw = self._optional_carrier_bytes(path, f"outcome-unknown {role}")
                retained_path = _retain_content_addressed(row["provider_root"], raw, suffix)
                reference = _ref(self.root, retained_path)
            else:
                present, reference = self._retained_safe_carrier(
                    row,
                    role,
                    suffix,
                )
            source_presence[role] = present
            carriers[role] = reference
        admission = row.get("in_flight_admission")
        execution_custody = row.get("execution_custody")
        execution_custody_sha256 = row.get("execution_custody_sha256")
        if (
            not isinstance(admission, dict)
            or set(admission) != {"path", "byte_count", "sha256"}
            or not isinstance(execution_custody, dict)
            or set(execution_custody) != {"path", "byte_count", "sha256"}
            or not isinstance(execution_custody_sha256, str)
            or execution_custody.get("sha256") != execution_custody_sha256
        ):
            raise RuntimeError("outcome-unknown admission or execution custody unavailable")
        host_returncode = row.get("terminal_host_returncode")
        diagnostic = {
            "schema": (
                "reviewed-campaign-outcome-unknown-diagnostic-v2"
                if isinstance(row.get("safe_terminal_carrier_custody"), dict)
                else "reviewed-campaign-outcome-unknown-diagnostic-v1"
            ),
            "status": "OUTCOME_UNKNOWN_DIAGNOSTIC_RETAINED",
            "failure_kind": failure_kind,
            "candidate_id": row["candidate_id"],
            "source_commit": row["source_commit"],
            "package_sha256": row["package_sha256"],
            "package_tree_sha256": row["package_tree_sha256"],
            "case_id": row["case_id"],
            "model": "gpt-5.5",
            "reasoning_effort": "high",
            "dispatch_classification": "OUTCOME_UNKNOWN",
            "admission_status": "ADMITTED",
            "provider_invocation_proven": False,
            "host_returncode": host_returncode,
            "host_returncode_status": (
                "RECORDED" if host_returncode is not None else "UNAVAILABLE"
            ),
            "host_invocation_id": row.get("host_invocation_id"),
            "started_at": row.get("started_at"),
            "ended_at": row.get("ended_at"),
            "carrier_disposition": carrier_disposition,
            "source_presence": source_presence,
            "in_flight_admission": copy.deepcopy(admission),
            **carriers,
            "credential_residue_scan": copy.deepcopy(credential_scan),
            "execution_custody_sha256": execution_custody_sha256,
            "execution_custody": copy.deepcopy(execution_custody),
            "captured_at": _utc_now(),
        }
        diagnostic_path = _retain_content_addressed(
            row["provider_root"],
            _canonical(diagnostic),
            ".outcome-unknown-diagnostic.json",
        )
        retained = _ref(self.root, diagnostic_path)
        row["outcome_unknown_diagnostic"] = retained
        prepared = self._prepared.get(row["case_id"])
        if prepared is not None:
            prepared["outcome_unknown_diagnostic"] = copy.deepcopy(retained)
        return retained

    def _teardown_process(self, process: Any) -> None:
        if not self.host.verify_tree_stopped(process):
            self.host.terminate_tree(process)
        if not self.host.verify_tree_stopped(process):
            raise RuntimeError(f"owned Codex process tree remains active: {process.pid}")

    def _credential_readback(self, row: dict[str, Any]) -> dict[str, object]:
        status = row.get("credential_scan_status")
        retained = row.get("credential_scan_evidence")
        if status in {"PASS", "PURGED", "PURGE_INCOMPLETE"}:
            if not isinstance(retained, dict):
                raise RuntimeError("credential residue readback evidence unavailable")
            return retained
        if status != "PENDING" or self._credential_transport_mode not in {
            _DEDICATED_AGENT_IDENTITY_ENV,
            _MANAGED_AUTH_HOME,
        }:
            raise RuntimeError("credential residue readback unavailable")
        try:
            if self._credential_transport_mode == _DEDICATED_AGENT_IDENTITY_ENV:
                if not isinstance(self._credential, str) or not self._credential:
                    raise RuntimeError("dedicated credential unavailable for residue readback")
                inventory = _scan_private_worker_for_credential(row["worker_root"], self._credential)
            else:
                if self._credential is not None:
                    raise RuntimeError("managed auth credential value entered adapter custody")
                inventory = _scan_private_worker_for_structural_credential_markers(
                    row["worker_root"]
                )
        except BaseException as exc:
            safe_carrier_outcomes: dict[str, str] | None = None
            if self._credential_transport_mode == _MANAGED_AUTH_HOME:
                try:
                    safe_carrier_outcomes = (
                        self._retain_safe_terminal_carriers_before_purge(row)
                    )
                except BaseException:
                    safe_carrier_outcomes = {
                        role: "UNSAFE_OR_UNPROVEN" for role in _SAFE_CARRIER_ROLES
                    }
                    row["safe_terminal_carrier_custody"] = {
                        "outcomes": copy.deepcopy(safe_carrier_outcomes),
                        "references": {},
                    }
            cleanup_error: IsolationCleanupError | None = None
            try:
                self._remove_owned_worker(row)
                self._remove_owned_root_if_ready()
            except IsolationCleanupError as cleanup_exc:
                cleanup_error = cleanup_exc
            worker_purged = _lstat_optional(row["worker_root"]) is None
            if not worker_purged and cleanup_error is None:
                cleanup_error = IsolationCleanupError(
                    "OWNED_WORKER_CLEANUP_FAILED_CLOSED: worker still exists"
                )
            if self._credential_transport_mode == _MANAGED_AUTH_HOME:
                if isinstance(exc, CredentialResidueError):
                    failure_class = "CREDENTIAL_RESIDUE"
                    semantic_classification = "CREDENTIAL_VALUE_RESIDUE"
                elif isinstance(exc, ManagedCredentialScanAmbiguousError):
                    failure_class = "AMBIGUOUS_SCAN_RESULT"
                    semantic_classification = "AMBIGUOUS_OR_UNAVAILABLE"
                else:
                    failure_class = "SCAN_UNAVAILABLE"
                    semantic_classification = "AMBIGUOUS_OR_UNAVAILABLE"
                marker_families = list(
                    getattr(exc, "marker_families", ())
                    if failure_class != "SCAN_UNAVAILABLE"
                    else ()
                )
                failure = {
                    "schema": _MANAGED_AUTH_SCAN_SCHEMA,
                    "status": "FAIL_CLOSED",
                    "worker": row["worker"],
                    "scan_mode": _MANAGED_AUTH_SCAN_MODE,
                    "credential_value_loaded_by_adapter": False,
                    "failure_class": failure_class,
                    "semantic_classification": semantic_classification,
                    "observed_marker_families": marker_families,
                    "safe_carrier_outcomes": safe_carrier_outcomes,
                    "cleanup_status": (
                        "OWNED_WORKER_PURGED"
                        if worker_purged
                        else "OWNED_WORKER_PURGE_INCOMPLETE"
                    ),
                    "completed_at": _utc_now(),
                }
            else:
                failure = {
                    "schema": "reviewed-campaign-credential-residue-scan-v1",
                    "status": "FAIL_CLOSED",
                    "worker": row["worker"],
                    "failure_class": (
                        "CREDENTIAL_RESIDUE"
                        if isinstance(exc, CredentialResidueError)
                        else "SCAN_UNAVAILABLE"
                    ),
                    "cleanup_status": (
                        "OWNED_WORKER_PURGED"
                        if worker_purged
                        else "OWNED_WORKER_PURGE_INCOMPLETE"
                    ),
                    "completed_at": _utc_now(),
                }
            evidence_path = _retain_content_addressed(row["provider_root"], _canonical(failure), ".credential-scan.json")
            evidence = _ref(self.root, evidence_path)
            scan_status = "PURGED" if worker_purged else "PURGE_INCOMPLETE"
            row.update({"credential_scan_status": scan_status, "credential_scan_evidence": evidence})
            prepared = self._prepared.get(row["case_id"])
            if prepared is not None:
                prepared.update({"credential_scan_status": scan_status, "credential_scan_evidence": evidence})
            if cleanup_error is not None:
                raise RuntimeError(
                    f"OWNED_WORKER_CLEANUP_FAILED_CLOSED: {cleanup_error}"
                ) from exc
            if isinstance(exc, CredentialResidueError):
                raise RuntimeError("access credential residue detected; owned worker custody purged") from exc
            if isinstance(exc, ManagedCredentialScanAmbiguousError):
                raise RuntimeError(
                    "managed credential scan ambiguous; owned worker custody purged"
                ) from exc
            raise RuntimeError("access credential residue scan failed closed; owned worker custody purged") from exc
        success = {
            "schema": (
                _MANAGED_AUTH_SCAN_SCHEMA
                if self._credential_transport_mode == _MANAGED_AUTH_HOME
                else "reviewed-campaign-credential-residue-scan-v1"
            ),
            "status": "PASS",
            "worker": row["worker"],
            **inventory,
            "encoding_forms_checked": ["utf-8", "utf-16-le", "utf-16-be"],
            "completed_at": _utc_now(),
        }
        if self._credential_transport_mode == _MANAGED_AUTH_HOME:
            success.update(
                {
                    "scan_mode": _MANAGED_AUTH_SCAN_MODE,
                    "credential_value_loaded_by_adapter": False,
                    "marker_families_checked": list(_MANAGED_AUTH_MARKER_FAMILIES),
                }
            )
        evidence_path = _retain_content_addressed(row["provider_root"], _canonical(success), ".credential-scan.json")
        evidence = _ref(self.root, evidence_path)
        row.update({"credential_scan_status": "PASS", "credential_scan_evidence": evidence})
        prepared = self._prepared.get(row["case_id"])
        if prepared is not None:
            prepared.update({"credential_scan_status": "PASS", "credential_scan_evidence": evidence})
        return evidence

    def attempt_states(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for case_id in self._ordered_cases:
            prepared = self._prepared[case_id]
            rows.append(
                {
                    "case_id": case_id,
                    "state": prepared["state"],
                    "started_at": prepared["started_at"],
                    "ended_at": prepared["ended_at"],
                    "host_invocation_id": prepared["host_invocation_id"],
                    "result": prepared["result"],
                    "pre_admission_diagnostic": copy.deepcopy(
                        prepared["pre_admission_diagnostic"]
                    ),
                    "terminal_cause": prepared.get("terminal_cause"),
                    "terminal_failure_kind": prepared.get("terminal_failure_kind"),
                    "terminal_host_returncode": prepared.get("terminal_host_returncode"),
                    "outcome_unknown_diagnostic": copy.deepcopy(
                        prepared.get("outcome_unknown_diagnostic")
                    ),
                }
            )
        return rows

    def abort_all(self) -> None:
        errors: list[str] = []
        handled_workers: set[Path] = set()
        for row in self._handles.values():
            handled_workers.add(row["worker_root"])
            try:
                if row["state"] in {"SUBMITTING", "PENDING_STRUCTURED_ADMISSION"}:
                    self._fail_pre_admission(
                        row,
                        failure_kind="ABORTED_BEFORE_ADMISSION",
                        host_returncode=row["process"].poll(),
                    )
                else:
                    if row["state"] == "ADAPTER_IN_FLIGHT":
                        self._record_terminal_cause(
                            row,
                            RuntimeError("cohort aborted before terminal observation"),
                        )
                    self._teardown_process(row["process"])
                if row["state"] == "ADAPTER_IN_FLIGHT":
                    self._mark_outcome_unknown(row)
                if row["state"] != "DISPATCH_UNKNOWN":
                    self._credential_readback(row)
                if row["state"] == "OUTCOME_UNKNOWN":
                    self._ensure_outcome_unknown_diagnostic(row)
                self._remove_owned_worker(row)
            except Exception as exc:
                errors.append(str(exc))
        for row in self._prepared.values():
            if row["worker_root"] in handled_workers:
                continue
            try:
                self._remove_owned_worker(row)
            except IsolationCleanupError as exc:
                errors.append(str(exc))
        try:
            self._remove_owned_root_if_ready()
        except IsolationCleanupError as exc:
            errors.append(str(exc))
        if errors:
            raise RuntimeError("; ".join(errors))
