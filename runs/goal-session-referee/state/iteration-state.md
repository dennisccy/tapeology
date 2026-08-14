# Iteration State — referee

**After iteration:** 2 · **Date:** 2026-08-14 · **Verdict:** CONTINUE

## Journeys

2 passing (J-01, J-02) · 7 failing (J-03..J-09 — Referee machinery still unbuilt) · 1 partial (J-10 sentinel: kept product green; its "3 Referee sections + 22 MCP tools" clauses wait on J-09) — 10 total

## Active blockers

- none inside this project — J-03 is buildable today: keyless, backend-only, no new dependency.
- OUTSIDE this project, human-owned: trendora's backend on `:8255` was killed by iter-2's pattern-based `pkill` and is still down; restart command is in `docs/handoffs/goal-referee-iter-2-dev.md`. Does not block tapeology.

## Last 2 verdicts

- iter 2: CONTINUE — J-02 passes: one typed observation record for both evidence families in `referee_evidence.py` + a rebuildable cache; evaluator ran the 28 referee tests and the full suite itself (2,446 pass / 8 skip) and read the hand-computed goldens line by line; kept product replayed green. Next target: J-03 alone, FULL depth.
- iter 1: CONTINUE — J-01 passes: `GET /research/desk/referee/evidence` serves honest per-family readiness (screenshot + 15 tests re-run by the evaluator); kept product replayed green.

## Do not redo

- J-01 and J-02 are DONE and verified in `app/research/referee_evidence.py`: the readiness fold, `current_playbook_detector_basis()`, `_newest_per_session_date()`, the typed observation contract (`_observation`, `playbook_observations`, `strategy_observations`), `RefereeObservationCache`, `REFEREE_SESSION_COMPLETE_ET`. EXTEND, never rebuild; import these — J-03..J-09 must not re-derive the observation shape. `REFEREE_FORMING_BAR_BASIS_CAVEAT` stays the one caveat string J-06/J-08 read verbatim.
- Both iter-1 riders are CLOSED: `integrity_errors` is documented in the pinned response shape, and the strategy adapter reuses the caveat constant by identity. Do not re-open.
- Suite floor: now 2,446 pass / 8 skip (era-open 2,418) — never fall below.
- Re-verified in iter-2: fingerprint `08e471b10130e1e2`, MCP `EXPECTED_TOOLS` == 20, nav == 3 routes, store-scope guard CLEAN (11,274 files), zero diff to `desk_playbook*.py`/`desk_forward.py`/`levels.py`/`tradability.py`/`setups.py`/`pnl_scan.py`/`config.py`/`main.py`.
- Backend-only journeys get a `not_yet` golden stub (see `journey-scripts/J-01.json`, `J-02.json`) — replay SKIPs them safely. `state/golden-gaps` is gone by design; do not chase replay coverage for J-03..J-06/J-08, and do NOT plan an iteration whose goal is J-10 (it rides along every iteration and closes with J-09).
- `state/blueprint.md` is drafted and correct — build into it, do not re-draft.
- Three riders for whoever builds J-03 (carry along; none is an iteration of its own): test `session_completeness` (zero assertions today, a gap-blind estimate J-06 will lean on); test `resolve_referee_obs_cache_db_path` (exported, never called); get an owner ruling or a spec revision for `detector_basis: None` on strategy observations before J-06 assumes the field is populated.
- Dev-server cleanup MUST use exact-PID process-tree kills only — never `pkill -f`; iter-2 killed an unrelated project's backend that way.
