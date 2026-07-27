# Iteration State — desk

**After iteration:** 9 · **Date:** 2026-07-27 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-02 J-03 J-04 J-05 J-06 J-07) · 1 partial (J-08) · 0 failing · 0 unknown — 8 total

## Active blockers

- **J-08's screenshot clause UNMET (owner: dev/QA lane — NOT a human).** `docs/goal.md` J-08 needs one row `age ≤ 2 d` beside one `age ≥ 10 d` in ONE image; `goal-desk-iter-9-evidence/UT-03-fresh-vs-stale.png` shows 3 d vs 14 d. ZERO code change needed — evaluator-measured: compute `screen_date=2026-07-25` inside a throw-away `.data/` copy (`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`) → AAPL **1 d**, META/NFLX/NVDA **12 d**. A test plan may NEVER soften a number `docs/goal.md` states.
- Carried, not blocking: browser-QA wrote a real screen into the AMBIENT `.data/screen/` (`screen-2026-07-27-936543601e75.json`) against its own spec NOTES — scope EVERY lane, browser-QA included, and name the data root in the results report. Plus: `/structure` Case Studies scans on first load until an operator warms the scan.

## Last 2 verdicts

- iter 9: CONTINUE — J-08 built and honest (63/63 rows carry `basis_as_of`/`basis_age_days`, byte-identical to `compute_tradability` on the evaluator's own 6-symbol cross-check; legacy snapshots untouched by sha256+mtime; suite 1346/8/0; pin `08e471b10130e1e2`; COHERENCE-PASS) but ONE acceptance clause literally unmet.
- iter 8: GOAL_ACHIEVED — J-07 `partial → passing` on every clause; era B's seven human-authored journeys closed and two-key confirmed. J-08 was appended afterwards by the goal-proposer.

## Do not redo

- **J-01–J-07 DONE and clause-verified**, all re-verified passing again in iter-9 (six by golden replay, J-06 by its 17-tool contract). Do not re-derive internals or re-shoot pictures (`goal-desk-iter-8-evidence/`, `goal-desk-iter-9-evidence/J-0*-verify.png`).
- **J-08's implementation is DONE — change no product code.** `desk_screen.py` `_basis_age_days` + the two ranked-row keys, `/desk`'s basis column + honest "basis not recorded in this snapshot" fallback, the consolidated row-anchor tooltip, `types.ts`, five new tests: all verified. Only EVIDENCE is owed.
- **Proven this iteration, do not re-prove:** legacy snapshots byte-identical (sha256 `530bb4f6…`/`9c2fddf6…`, mtime 2026-07-25, 0/10 rows carry the new keys); zero diff on `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`/`config.py`/`meta.py`/`mcp/__init__.py`; `[NEW]` demo walkthrough exists.
- **R-1's eight files are IN INVENTORY and CLOSED** — never reopen, revert, or re-word that goal.md section.
- **Goldens settled:** `J-08.json` recorded + replay-proven (write-free; steps 3/6 need a LATEST screen carrying basis fields); `J-07.json` step 10 and `J-05.json`'s 4 s wait stay as-is; any golden edit must be disclosed.
- **Settled:** zero new `Config` field all era; suite floor now 1346 pass / 8 skip (1354 collected); pin `08e471b10130e1e2`; `UI_ROUTES` = 3; MCP = 17 tools; fixture-scoped rigs are the recipe for EVERY lane.
