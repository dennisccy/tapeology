# Iteration State — referee

**After iteration:** 1 · **Date:** 2026-08-14 · **Verdict:** CONTINUE

## Journeys

1 passing (J-01) · 8 failing (J-02..J-09 — Referee machinery still unbuilt) · 1 partial (J-10 sentinel: kept product green; its "3 Referee sections + 22 MCP tools" clauses wait on J-09) — 10 total

## Active blockers

- none — no credential, network, or human-owned blocker. J-02 is buildable today: keyless, backend-only, no new dependency.

## Last 2 verdicts

- iter 1: CONTINUE — J-01 passes: `GET /research/desk/referee/evidence` serves honest per-family readiness (screenshot `reports/qa/goal-referee-iter-1-evidence/UT-J-01-result.png`; evaluator re-ran the 15 new tests + 156 guard tests itself); kept product replayed green. Next target: J-02 alone, lean.
- iter 0: CONTINUE — honest baseline: 9 journeys fail (referee routes 404, no `referee_*.py`, MCP 20 tools); kept product walked green in a real browser.

## Do not redo

- J-01 is DONE and verified: `app/research/referee_evidence.py` + `referee_routes.py` + the route mounted in `main.py`; `tests/test_referee_evidence.py` (7) + `tests/test_referee_guards.py` (8) green. Extend it — never rebuild it; `REFEREE_FORMING_BAR_BASIS_CAVEAT` is the one caveat string J-06/J-08 must import verbatim.
- Suite floor: era-open 2,418 pass / 8 skip; now 2,433 pass / 8 skip — never fall below.
- Re-verified live in iter-1: fingerprint `08e471b10130e1e2`, MCP `EXPECTED_TOOLS` == 20, nav == 3 routes, store-scope guard CLEAN (11,274 files), zero diff to `desk_playbook*.py`/`desk_forward.py`/`levels.py`/`tradability.py`/`setups.py`/`pnl_scan.py`/`config.py`.
- `state/blueprint.md` is drafted and correct (3-route IA + the 7 Era-6 Data Contract rows) — build into it, do not re-draft.
- No golden replay script can exist for a backend-only journey (`demo_runner.py` is single-base-url); J-01 sits in `state/golden-gaps` by design — do not chase it, and expect the same for J-02..J-06/J-08.
- Do NOT plan an iteration whose goal is J-10; it rides every iteration as the required-still-passing sentinel and closes together with J-09.
- Open rider for whoever next touches the evidence endpoint (J-02): fold its two served `integrity_errors` keys into the documented response shape — served today, undocumented (reviewer NOTE + coherence advisory).
