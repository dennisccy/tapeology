# Iteration State — playbook

**After iteration:** 9 · **Date:** 2026-08-11 · **Verdict:** STALLED

## Journeys

10 passing (J-01..J-10) · 0 failing · 0 unknown — 10 total. Era build complete; the halt is for two
owner rulings, not a product gap.

## Active blockers

- **Owner ruling 1 (human):** ratify or reject the developer-authored `range_trade` "degenerate
  trigger reference" clause — `docs/playbook-detector-spec.md` §3.7. Rejecting = drop `range_trade`
  from `PLAYBOOK_SETUPS` (changes what J-06 ships).
- **Owner ruling 2 (human):** settle three narrower-than-spec readings (crossed-midrange
  disclosure, double-top pair choice, 1.5x jump-to-base gate + cup rim constant) — all disclosed,
  all fail-closed.
- **Test-asset defect (dev):** `runs/goal-session-playbook/journey-scripts/J-10.json` step 6 now
  asserts the fixture-dependent hash `9597251432bd9e75` (was "Forward Returns"); the same value was
  `9803f6881e8f86b3` earlier in this iteration. Re-point it at a static kept-surface string.
- **Environment (dev):** `:8301` left on the scoped fixture rig, not the operator's real backend.

## Last 2 verdicts

- iter 9: STALLED — J-09 + J-10 landed (20 MCP tools; full kept-product walk); every unblock path
  left is an owner-only ruling open since iter 6.
- iter 8: CONTINUE — J-08 evidence view landed; store-scope guard built after a replay-lane breach.

## Do not redo

- **J-09 MCP contract v4 — DONE.** 20 tools live, `desk_playbook`/`desk_playbook_evidence` in
  `_STATIC_PATHS` (`apps/backend/app/mcp/__init__.py`); `EXPECTED_TOOLS`=20 + byte-identity tests
  (empty/populated/`?date=`) in `apps/backend/tests/test_mcp_server.py`.
- **J-10 kept-product walk — DONE.** 8 screenshots in `reports/qa/goal-playbook-iter-9-evidence/`;
  evaluator re-derived kept-route byte-identity + inventory from `git diff ed87dca..HEAD`.
- **Store-scope hardening — DONE (all 3):** abort-on-breach at both call sites, `qa-phase.sh` gated,
  `store-scope.env` project-identity guard. Closes the iter-8 open item.
- **Evidence signature line — DONE** (`app/desk/page.tsx`); **`J-08.json` golden — RECORDED**.
- **Zero-diff files stay zero-diff:** `desk_forward.py`, `desk_playbook*.py`,
  `docs/playbook-detector-spec.md`, `docs/goal.md`, `config.py`, `meta.py`. Pin `08e471b10130e1e2`.
