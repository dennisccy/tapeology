# Iteration State — desk

**After iteration:** 1 · **Date:** 2026-07-25 · **Verdict:** CONTINUE

## Journeys

1 passing (J-01) · 5 failing (J-02 J-03 J-04 J-05 J-06) · 1 partial (J-07) — 7 total

## Active blockers

- None human-owned; none blocking J-02. Two dev-owned carried risks: (1)
  `edge_report_cache._config_content_hash` (`app/research/edge_report_cache.py:165-169`) is a SECOND
  whole-config hash with NO exclusion set, keying the setups/tradability/edge-report/backtest caches.
  The 4 new `desk_universe_*` fields changed it → all pre-diff rows stranded: real-data
  `GET /research/setups` cold (~9–11 min), `/structure` Load ~21.6 s. EVERY future `Config` field
  re-does this — set the policy in the spec, and warm both before J-04's browser pass.
- (2) `apps/backend/.data/universe/universe-2026-07-25-49b33fa31680.json` pre-populates the prod dir,
  so an identical LIVE POST now returns 409 instead of registering.

## Last 2 verdicts

- iter 1: CONTINUE — J-01 `passing` on the evaluator's OWN run through the real routes (empty /
  registered / corrupted-422 / duplicate-409), suite 1210p/8s/0f, pin `08e471b10130e1e2` unchanged
  incl. under a Path-A field override, 14/14 kept routes byte-identical, COHERENCE-PASS.
- iter 0: CONTINUE — verify-only baseline, zero source diff; J-01–J-06 failing, J-07 partial.

## Do not redo

- **J-01 is DONE and independently verified** — vendor seam, stdlib parser, append-only checksummed
  `UniverseStore`, both `/research/desk/universe` routes, 4 Path-A Config fields (exclusion, stability
  + counter tests, provenance), 42 tests — `desk_universe.py`/`desk_routes.py`; no index owed.
- **"The fixture universe" exists** — `tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json`
  (103 members, checksum re-verified) + `sp100_constituents.html` / `..._corrupted.html`; reuse by name.
- **Live Wikipedia fetch already proven** (101 real members, `BRK.B→BRK-B`); Wikimedia demands a
  URL-shaped User-Agent (`desk_universe.py:70`). Do not re-litigate the vendor or gate on it.
- **J-07 stays `partial` BY DECISION** until nav = 3 routes (J-04) and MCP = 17 tools (J-06) — see
  `state/assumptions.md`; iter-0 browser walk stands; suite floor now 1210p/8s; the pin must not move.
- **`blueprint.md` is drafted** (`state/blueprint.md`) and matched verbatim; extend, do not redraft.
- **Next target settled: J-02 alone, at `full` depth** (coverage from `bar_index` + resumable top-up;
  first desk compute manager). Carry-forward list in `runs/goal-session-desk/iter-1/eval.md`.
