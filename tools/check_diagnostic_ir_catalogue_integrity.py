#!/usr/bin/env python3
"""Compatibility entrypoint for Diagnostic IR catalogue/source-basis checks."""

from __future__ import annotations

import sys

from check_ir_instance_integrity import main


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
