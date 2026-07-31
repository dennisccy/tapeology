# Iteration State — desk

**After iteration:** 36 · **Date:** 2026-07-31 · **Verdict:** GOAL_ACHIEVED

## Journeys

21 passing (J-01..J-21) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` · 0 `pending_infra` · 2 `evidence_makeup` (J-20 + J-21, films only) — 21 total; all 21 `spec_hash` values re-derived from `docs/goal.md` and matching; no `journeys-changed.md`; 4 historical anti-goal items all `resolved`, none new; scan CLEAN; coherence COHERENCE-PASS.

## Active blockers

- **none blocking.** Two owed ARTIFACTS, not product faults: the `[NEW]`-flagged demo-narrator walkthroughs for J-20 and J-21 were never recorded — the engine dispatched `depth=lean` against specs asking `Depth: full` on iters 32/33/35/36, so no demo-narrator has run since iter-34 (`reports/demo/goal-desk-iter-35/` and `-iter-36/` do not exist). They ride a `Depth: evidence` pass as passengers; NEVER the reason for a build run.
- Awaiting the second-key confirm only. If it REJECTS, the follow-ups below are the candidate work — nothing else is open.

## Last 2 verdicts

- iter 36: GOAL_ACHIEVED — J-21's screen-pin disclosure landed and was proven three ways by the evaluator personally: three per-state screenshots opened at 1440×900 (match / differ / empty); today's signature re-derived read-only over `.data` (`2ce14e8f252966f7`, carried by none of the 12 recorded screens, 101 pinned members); and the match state re-created from scratch over the committed fixtures, reproducing the screenshot's exact snapshot id `screen-2026-06-22-09cf660a4125`, signature `64c954949e3cf681` and 1-ranked/102-skipped counts, plus the planted-row flip and the byte-identical repeat. Suite 1559 pass/8 skip/0 fail, pin `08e471b10130e1e2`, MCP 17, replay 9/9 with ZERO script edits, nothing under `.data` newer than the run's start.
- iter 35: GOAL_ACHIEVED — J-20's screen-comparison disclosure landed; confirmed by the second key (`iter-35/eval-confirm.md` = CONFIRM_ACHIEVED, which also ruled a missing film "not a product gap").

## Do not redo

- **J-21 is DONE, front to back**: `apps/backend/app/research/desk_screen_pins.py` (sole owner), `GET /research/desk/screen/pins` (`desk_routes.py`, sole endpoint, `screen_date` required → 422), `DeskProvenancePins` + `TodayScreenPinsNote` in `app/desk/page.tsx` (own `desk-provenance-pins-*` / `desk-run-screen-pins-*` testid namespace), `tests/test_desk_screen_pins.py` (8 tests), `journey-scripts/J-21.json` (stable testids only). Do not rebuild, re-own, re-path or move any of it.
- **J-20 and J-19 stay DONE** (owners, endpoints, sections, guard tests, repointed scripts). Do not re-point `J-17.json`/`J-19.json`/`J-20.json`/`J-21.json`.
- **Do NOT click Top-up or Run Screen, and do NOT stand up a scoped rig without need**: the ambient store is untouched (1163 bar series, 1 universe, 12 screens, 3 screen-run, 2 top-up, 2 reconciliation records, all checksums green) and already shows J-21's differ state naturally.
- **Do NOT run a capture-only BUILD iteration** and do not re-verify J-01..J-21 as an iteration goal. Presentation facts on non-gating lanes (replay verify frames sharing one md5 — same in iters 34/35; deep-scroll captures returning black → crops) are accepted tooling behaviour, not product faults.
- Zero diff stays law: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `desk_screen_compute.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `desk_topup_compute.py`, `meta.py`, `mcp/__init__.py`, both charts, the guard test files; pin `08e471b10130e1e2`; 17 MCP tools; zero new `Config` fields. `test_desk_ui_guards.py` reads `journey-scripts/J-13.json`+`J-14.json` — archiving that folder breaks the suite.
- **Follow-ups, explicitly never an iteration goal on their own:** (1) the two owed films; (2) the provenance pin sentence is easy to misread when an OLD screen from history is displayed (it describes today's pins, not that screen); (3) the dev's "a non-null `recorded` can only name the displayed snapshot" reasoning is looser than the code guarantees — printed copy is honest, but naming the compared snapshot explicitly would close it; (4) `DeskProvenancePins` has no separate no-universe branch (would print "walk 0 members" in a state that cannot occur today). Plus iters 34/35's earlier owner-optional notes ("ranked rows are identical" wording; unknown-id `base_resolution`), all still non-blocking.
