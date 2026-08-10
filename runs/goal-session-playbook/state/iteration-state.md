# Iteration State — playbook

**After iteration:** 1 · **Date:** 2026-08-10 · **Verdict:** CONTINUE

## Journeys

1 passing (J-01) · 8 failing (J-02..J-09, unstarted) · 1 partial (J-10 sentinel — its "MCP = 20 tools" clause needs J-09) — 10 total

## Active blockers

- none human-owned. All dev work; J-02 (measurement) is the next link.
- Evidence debt: J-10's golden replay (`journey-scripts/J-10.json`) was NOT run in iter-1 — the
  browser lane self-skips on `Frontend Present: no`. Ask for it explicitly next iteration.
- Housekeeping: iter-1's 7 product files are still UNCOMMITTED (HEAD = iter-0 showcase commit).

## Last 2 verdicts

- iter 1: CONTINUE — J-01 verified passing (43 new tests, suite 1969/8, route probed live); audit
  found+fixed a fabricated-opening-range bug in-iteration; 8 journeys still unbuilt.
- iter 0: CONTINUE — verified-absent baseline; 9 journeys failing, kept product intact.

## Do not redo

- J-01 is DONE and verified — do not rebuild `desk_playbook_features.py` (8 primitives),
  `desk_playbook_detect.py` (open_high/low_break), or `desk_playbook.py` (spec §1 constants,
  parameters+signature, `PlaybookStore`, `compute_playbook`) + `GET /research/desk/playbook`.
- Fixed, do not re-fix: `opening_range`'s 5m fallback now filters to the 09:30–09:45 window
  (`desk_playbook_features.py:123`) + test at `tests/test_desk_playbook_features.py:117`.
- Floors re-verified in iter-1 — do not re-derive: suite **1969 pass / 8 skip**, fingerprint
  **`08e471b10130e1e2`**, MCP still **18** tools, nav = 3 routes, zero diff on `desk_forward.py`,
  `desk_screen*.py`, `setups.py`, `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py`, frontend.
- J-10 is `partial` BY DESIGN until J-09 — never plan an iteration to "fix" it; a `partial`
  sentinel will NOT auto-trip the regression halt: treat ANY kept-surface break as stop-and-review.

## Next target

- J-02 only (imported-rail measurement: `_measure_from`, `invalidation_breached`, seeded anchors,
  `desk_playbook_compute.py` trio + CLI, `desk_playbook_log.py`), **full** depth. Required-still-
  passing: J-10 — its replay MUST run. Carry in: 3 audit test gaps (T1/T3) + owner rulings on spec
  §1's `PLAYBOOK_OR_MIN_1M_BARS` row and §3.1's P4 rule (B3/B4).
