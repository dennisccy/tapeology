"""The §0.4 Path B epoch-bump retirement gate (goal.md I-9 / J-04 acceptance).

The founding ``config_fingerprint`` literal ``4d665603569b9dbf`` was RETIRED in this journey (The
Clean Slate iter-4): 23 orphaned journal-era ``Config`` fields were deleted, 8 now-orphaned
exclusion-set entries were pruned, and ``pnl_founding_enhancement_id`` / ``_title`` were bumped —
so ``Config().config_fingerprint()`` now mints a NEW pin (T-3: exactly ONE commit ever touches the
13 pin-assertion sites, and this is that commit). This gate proves the old pin is not merely
unasserted but genuinely GONE from every live source file — no forgotten fixture, comment, or
straggler assertion still names it.

Scope is exactly ``apps/`` (the SAME ``REPO_APPS = parents[2]`` root ``test_no_execution_path.py``
uses), which naturally satisfies the T-11 exemption: ``reports/**``, ``runs/**``, and
``docs/goal-archive/**`` all live OUTSIDE ``apps/`` and are read-only history this gate never
walks or judges. Mirrors that file's ``_SKIP_DIRS`` / ``_SOURCE_SUFFIXES`` convention (build
products, dependencies, and committed fixture DATA are out of scope for a source-vocabulary scan;
goal.md's I-9 already independently verifies no committed fixture JSON embeds the stamp).
"""

from __future__ import annotations

from pathlib import Path

# apps/backend/tests/<this file> -> parents[2] is the apps/ tree root (test_no_execution_path.py
# precedent, reused verbatim).
REPO_APPS = Path(__file__).resolve().parents[2]

_SKIP_DIRS = {".venv", "node_modules", ".next", "__pycache__", ".data", ".pytest_cache", "fixtures"}
_SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js"}

RETIRED_FINGERPRINT = "4d665603569b9dbf"

# This gate itself names the retired literal as data (the test_no_execution_path.py SELF-exemption
# precedent) — it is scanning/policing code, not a candidate for its own scan.
SELF = "backend/tests/test_fingerprint_epoch_retirement.py"


def _source_files() -> list[Path]:
    files = []
    for path in sorted(REPO_APPS.rglob("*")):
        if not path.is_file() or path.suffix not in _SOURCE_SUFFIXES:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def _rel(path: Path) -> str:
    return path.relative_to(REPO_APPS).as_posix()


def test_scan_is_not_vacuous():
    files = _source_files()
    rels = {_rel(p) for p in files}
    # A path bug must never silently pass an empty scan: the sweep sees the real tree.
    assert len(files) > 100
    assert "backend/app/config.py" in rels
    assert "backend/tests/test_backtests.py" in rels  # one of the 13 former pin-assertion sites
    assert any(r.startswith("frontend/") for r in rels)


def test_retired_fingerprint_literal_appears_in_zero_files_under_apps():
    offenders: list[str] = []
    for path in _source_files():
        rel = _rel(path)
        if rel == SELF:
            continue
        if RETIRED_FINGERPRINT in path.read_text(errors="ignore"):
            offenders.append(rel)
    assert offenders == [], (
        f"the retired epoch pin {RETIRED_FINGERPRINT!r} still appears in: {offenders} — the "
        "§0.4 Path B bump (T-3) must move every live reference in the SAME commit"
    )


def test_current_fingerprint_has_genuinely_moved():
    # Belt-and-suspenders: the live-computed pin itself is not the retired literal (proves the
    # scan above isn't vacuously passing because Config itself still mints the old value).
    from app.config import Config

    assert Config().config_fingerprint() != RETIRED_FINGERPRINT
