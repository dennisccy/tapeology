# Iteration State — referee

**After iteration:** 9 · **Date:** 2026-08-15 · **Verdict:** ESCALATE

## Journeys

8 passing (J-01..J-08) · 1 failing (J-09) · 1 partial (J-10) — 10 total. J-01..J-04 were
DEFERRED-BUDGET (kept prior status, sources unchanged); J-05/J-06 re-verified directly (their
sources changed); J-07's stale-capture flag cleared by a fresh screenshot.

## Active blockers

- **J-09, the only build work left** (dev): the two missing `/desk` Referee panels
  (Adjudications, Runs) + MCP 20→22 (`EXPECTED_TOOLS`); J-10 cannot close until it ships.
- **Open minor anti-goal** (dev): a certificate's candidate name is caller-declared and never
  checked against its evidence — `referee_adjudicate.py:521` / `referee_evidence.py:826` pool
  every backtest unfiltered. Unreachable today (no production caller passes
  `journal_store`/`certificate_mint`); close before the mint reaches `POST .../evaluate`.
- Human, non-blocking: iters 8+9 uncommitted; trendora :8255 not restarted.

## Last 2 verdicts

- iter 9: ESCALATE — J-08 interlock verified real (fail-closed, no bypass), but the planned full
  pass was demoted to lean a 3rd time and the evaluator itself had to find the scoping gap.
- iter 8: CONTINUE — J-07 shipped; audit caught the `projected_days_to_target` bug in-round.

## Do not redo

- **J-08 is DONE** (`pnl_scan.py:349` authorizes before the ledger write at `:367`;
  `certificate_store` required; TC-1..TC-7 cover all six refusal classes; no-bypass scan green).
- **Riders done:** S-6 `range_trade:short at_wall`; `family_id`/`family_q` backend-owned and
  served (closes iter-8 coherence F1); accrual/discovery context fix
  (`_signal_matches_hypothesis_cell`); `_PRICE_ARITHMETIC_FIELDS` covers `hyp.accrual.*`.
- **Settled** (`state/assumptions.md`, iter-9): strategy hypothesis `setup_id`/`side` are
  deliberately vestigial; TC-10's `insufficient_sample` = the record's `ci_cluster` sentinel.
- **Verified green this run:** suite 2,678 collected / 2,670 passed / 0 failed; pin
  `08e471b10130e1e2`; MCP 20 tools; store guard CLEAN (11,274 files unchanged).
- **Clean-ups, not new scope:** stale "unwired" docstring (`referee_adjudicate.py:6,1720`);
  `test_pnl_scan.py:1239` can-fail proof inspects a string, not the real scan; duplicate
  assertion `test_referee_registry.py:874`.
