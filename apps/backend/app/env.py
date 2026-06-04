"""Minimal stdlib ``.env`` loader — no dependency, no override (vendor-neutral).

Loads ``KEY=VALUE`` pairs from ``apps/backend/.env`` into ``os.environ`` ONLY for keys not
already set. "Load-if-missing" is what keeps callers in control: a value exported by the
shell, ``start-backend.sh``, CI, or a test's ``monkeypatch`` is never clobbered, so the test
suite stays hermetic while uvicorn and ``pytest`` both transparently see the operator's local
``.env`` without sourcing it by hand.

This module names no vendor and parses no secret-specific format — it just reads simple
``KEY=VALUE`` lines (``#`` comments and blanks skipped) and tolerates CRLF endings (values are
stripped). ``.env`` itself stays untracked; only ``.env.example`` (empty values) is committed.
"""

from __future__ import annotations

import os
from pathlib import Path

# apps/backend/.env  (this file is apps/backend/app/env.py)
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(path: Path = ENV_PATH) -> None:
    """Populate ``os.environ`` from ``path`` for keys that are not already set."""
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:  # never override an already-set var
            continue
        # Strip surrounding whitespace (handles CRLF) and optional matching quotes.
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = value
