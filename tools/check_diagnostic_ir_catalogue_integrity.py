#!/usr/bin/env python3
"""Compatibility entrypoint for Diagnostic IR catalogue/source-basis checks.

The implementation lives in check_ir_instance_integrity.py. This alias remains
so older verification command lists that named catalogue integrity still run the
same schema-adjacent/custom IR fixture validator.
"""

from __future__ import annotations

import sys

from check_ir_instance_integrity import main


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
