#!/usr/bin/env python3
"""Validate generated skill/ package shape against build-manifest.json."""

from __future__ import annotations

import sys

from compiled_runtime_lib import fail_with_errors, repo_root
from package_shape import validate_skill_tree


def main() -> int:
    return fail_with_errors("package shape", validate_skill_tree(repo_root()))


if __name__ == "__main__":
    sys.exit(main())
