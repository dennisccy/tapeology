# Iteration State — playbook

**After iteration:** 7 · **Date:** 2026-08-11 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01..J-07) · 2 failing (J-08 J-09) · 1 partial (J-10 — needs J-09's 20 MCP tools) — 10 total

## Active blockers

- **Depth arbiter (engine):** spec asked `full`, engine ran `lean` — 3rd time this session; no
  auditor read J-07, the first mass-writer into the operator's store. Next iteration MUST be `full`.
- **Replay lane scoping (dev):** the golden-replay lane runs against the ambient unscoped `:8301`
  backend (the operator's real `.data/`), and `journey-scripts/J-01.json` + `J-03.json` click Run
  Playbook. Nothing was written this run (verified); the hole is structural.
- **J-06 (dev):** no golden script → DEFERRED-BUDGET this run, will keep being skipped; also still
  owes its Range Trade row re-capture (`evidence_makeup`).
- **Owner rulings, 4 open (human):** the developer-authored §3.7 degenerate-trigger clause in
  `docs/playbook-detector-spec.md`, plus 3 narrower-than-spec disclosures (`crossed_midrange`,
  `double_top` pair choice, 1.5x jump-to-base / cup rim).
- **Defect (dev):** `GET .../playbook/backscan/plan` 500s on a half-typed date (`_planned_dates`
  raises `ValueError`); the panel refetches on every keystroke.

## Last 2 verdicts

- iter 7: ESCALATE — J-07 back-scan shipped + browser-verified, real store untouched, suite 2130/8
  skip, pin `08e471b10130e1e2`; planned-full ran lean, so J-08's pooling math needs the auditor.
- iter 6: CONTINUE — J-06 range family passed; three minor anti-goal items opened, two since closed.

## Do not redo

- J-07 is DONE: `apps/backend/app/research/desk_playbook_backscan.py` (plan/walker/manager/ledger +
  `_assert_scoped`), 3 routes in `desk_routes.py`, the `/desk` Backscan panel, `J-07.json` golden.
- Short-side `range_trade` mirror test (TC-12) DONE in `tests/test_desk_playbook_detect.py`, zero
  diff to `desk_playbook_detect.py` — do not re-open the detector for it.
- Backscan guard censuses re-derived: `_EXPECTED_EFFECT_COUNT = 19`, `_EXPECTED_INTERVAL_COUNT = 7`, `_TRIGGER_CALLS` +2, `_PRICE_ARITHMETIC_FIELDS` extended.
- Scoped rig exists (extend, never rewrite): `scripts/qa_playbook_iter7_fixture_scoped_backend.sh`.
- Keep the zero diff: `desk_forward.py`, `desk_playbook*.py` (except the new backscan module),
  `config.py`, `levels.py`, `bars.py`, `setups.py`, `mcp/__init__.py`; pin `08e471b10130e1e2`.
- Do NOT delete the iter-6 accidental record `.data/playbook/playbook-2026-08-07-84fcd116ebd7.json`.
