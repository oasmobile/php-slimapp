#!/usr/bin/env python3
"""Deterministic local tooling for Mars Development Flow."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from mdf_core.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
