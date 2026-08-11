# Iteration State — playbook

**After iteration:** 8 · **Date:** 2026-08-11 · **Verdict:** CONTINUE

## Journeys

8 passing (J-01..J-08) · 1 failing (J-09) · 1 partial (J-10) — 10 total

## Active blockers

- J-09 not built (dev): MCP is 18 tools, evaluator-counted; needs `desk_playbook` +
  `desk_playbook_evidence` in `_STATIC_PATHS` (`apps/backend/app/mcp/__init__.py:86`) → 20.
- J-10 cannot close until J-09 lands (its acceptance names "exactly 20 tools"); it also still owes
  the full kept-product browser walk (cockpit + /structure + every shipped /desk section).
- Store-scope guard is partial (dev): covers `browser-qa-phase.sh:250` + `goal-iter-lean.sh:350`
  only — the QA agent's own browser pass is ungated; a breach discloses but does not abort;
  `project-extensions/store-scope/store-scope.env:33` hardcodes the playbook rig repo-wide.
- Two owner rulings (human), untouched since iter-6: ratify/reject the §3.7 `range_trade`
  degenerate-trigger clarification; settle the three narrower-than-spec disclosures.

## Last 2 verdicts

- iter 8: CONTINUE — J-08 evidence table shipped and screenshot-verified; suite 2158 pass/8 skip,
  pin `08e471b10130e1e2`; the replay lane's real-store write was caught and closed by a real guard.
- iter 7: ESCALATE — J-07 shipped in a lean pass, so no auditor read the first mass-writer code.

## Do not redo

- J-08 evidence view is DONE: `desk_playbook_evidence.py` + `GET /research/desk/playbook/evidence`
  + the `/desk` Playbook Evidence section; pooling math hand-re-derived by the auditor (29 checks).
- All five iter-6/7 carry items are CLOSED: back-scan plan returns HTTP 200 on a half-typed date
  (write path refuses 422); `journey-scripts/J-05.json` asserts a real signal row;
  `journey-scripts/J-06.json` exists and replays green; the Range Trade re-capture is delivered
  (`evidence_makeup` cleared); the replay lane is scoped by the store-scope guard.
- The `EVIDENCE_REGISTER` baseline-cap wording is FIXED (`desk_playbook_evidence.py:98-110`) with a
  regression test the pre-fix text fails — do not reword it back.
- The three real records written at 14:45 (`.data/playbook/playbook-2026-06-2{2,3,4}-*.json`) and
  iter-6's `playbook-2026-08-07-84fcd116ebd7.json` STAY — deleting them breaches the append-only rail.
- Zero diff is maintained and verified for `desk_forward.py`, `desk_playbook_detect.py`,
  `desk_playbook.py`, `docs/playbook-detector-spec.md`, `docs/goal.md`, `config.py`, `meta.py`.
