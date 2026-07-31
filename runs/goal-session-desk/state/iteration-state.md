# Iteration State — desk

**After iteration:** 32 · **Date:** 2026-07-31 · **Verdict:** GOAL_ACHIEVED (first key)

## Journeys

19 passing (J-01..J-19) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` · 0 `pending_infra` · 1 `evidence_makeup` (J-19, its `[NEW]` walkthrough was never recorded — lean depth sent no demo lane) — 19 total; all 19 `spec_hash` values re-derived from `docs/goal.md` and matching.

## Active blockers

- **none blocking.** All four recorded anti-goal items stay `resolved`; nothing new opened. Scan CLEAN, coherence COHERENCE-PASS.
- **Two golden-script repairs owed (dev), BEFORE any further replay.** This iteration's spec-sanctioned real top-up (`topup-2026-07-31-8fb5c9a1f737`) displaced the run the `/desk` latest-run panel shows, so `journey-scripts/J-17.json` is STALE — it pins "0 reused · 390 fetched · 0 unchanged · 14 failed", "window basis not recorded in this run", and the `desk-topup-run-latest-failed` block, which no longer MOUNTS at 0 failed. J-17's feature is intact and photographed (`UT-J-19-result.png` line 3). `journey-scripts/J-19.json` repeats the iter-29 `J-18.json` mistake: pinned to today's counts/dates ("101 pairs reach it", "(303)", "AAPL 4h — 2026-07-30").
- Coupling to watch: `test_desk_ui_guards.py` reads `journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 32: GOAL_ACHIEVED — J-19 built and proven, not claimed: evaluator opened `UT-J-19-result.png` (reach line + "Pairs recorded earlier (303)" + a strictly-earlier "AAPL 1w — 2026-07-27", one frame, no h-scroll), then swept ALL 404 outcome entries in the frozen run record against `BarStore.merged_bars` — 0 mismatches (294 later / 101 equal / 9 null→set / 0 backwards). Suite 1514 pass / 8 skip / 0 fail, `08e471b10130e1e2`, 17 MCP tools, append-only proven (bar files 759→1163, ZERO pre-existing files touched, all 20 records verify their own SHA-256).
- iter 31: GOAL_ACHIEVED — the two dropped honesty fixes landed and were verified in frame; both polluted build files reverted byte-for-byte; confirmed by the second key.

## Do not redo

- **J-19 is BUILT and verified**: `store_frozen_through_after` from a second `_pair_window` call in `run_topup`, the optional field in `lib/types.ts`, and `topupLibraryReach` + the reach line / earlier-pairs list inside `LatestTopupRunDetail` (`apps/frontend/app/desk/page.tsx`). Do not rebuild, revert, or re-verify it as an iteration goal.
- **Do NOT run a capture-only iteration.** J-19's missing `[NEW]` walkthrough is picture debt only — it rides any future run as a passenger, never as its reason. All other captures are DONE (iter-29/30/31 J-18 set, iter-31 film with distinct md5s). Do NOT re-verify J-01..J-18 as an iteration goal.
- **Owner-optional, never a new iteration**: iter-31's B1 / F1 / T3 / demo scroll-anchor, plus iter-32's two wording notes — the earlier-pairs list renders all 303 rows rather than a short selection, and 202 of them print the same DAY as the "newest" line because the comparison uses the exact hour while the page prints `.slice(0,10)`.
- J-16 layout is DONE and measured (`table-fixed` + 13-col `<colgroup>`). No 14th column, no width re-tuning; `band `/`opposite ` in-cell prefixes MUST stay. Never script a `click` inside a `/desk` ranked/skipped row — the stretched `absolute inset-0` anchor blocks it; use `expect`-only. Demo/replay scripts stay READ-ONLY over the ambient store.
- Zero diff stays law: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `research/routes.py`, `desk_topup_log.py`, `meta.py`, `mcp/__init__.py`, both charts, the three guard test files; pin `08e471b10130e1e2`; 17 MCP tools; zero new `Config` fields. Accepted non-defect: replay-frame duplication (tooling).
