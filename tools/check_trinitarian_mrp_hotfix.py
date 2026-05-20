#!/usr/bin/env python3
"""Case wrapper for the Trinitarian RC2 hotfix fixtures.

The runtime invariant logic lives in check_mrp_route_invariants.py so the route/curl rules are
not limited to this case family.
"""

from __future__ import annotations

from pathlib import Path

from check_mrp_route_invariants import run_cli


def main() -> int:
    return run_cli(
        default_root=Path("tests/trinitarian-mrp-hotfix"),
        description=__doc__,
    )


if __name__ == "__main__":
    raise SystemExit(main())
