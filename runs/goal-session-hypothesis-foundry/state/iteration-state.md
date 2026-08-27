# Iteration State — hypothesis-foundry

**After iteration:** 7 · **Date:** 2026-08-27 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01..J-07) · 1 failing (J-08) — 8 total. No status changed; nothing regressed.

## Active blockers

- **J-08 "The operator sees the final Foundry truth"** (owner: dev) — era's last journey, never
  targeted: final summary + drill-ins, the honest "no diagnostic survivor exists" line, the
  `withheld_excluded = 80` count J-06/J-07 leave CLI-only, the T-9/T-10/T-11 guards. No sealed file.
- **"No second real generation epoch"** (owner: HUMAN, blocking) — ratify or reject the discarded
  first real epoch. `reports/hypothesis-foundry/source-registry-audit.md:9-40`.
- **"Persistence stays scoped"** (owner: HUMAN, blocking) — a page-load GET writes a lock file; fix
  site `apps/backend/app/research/foundry_runner.py:197-201` is SEALED.
- Ledger: total=4 · resolved=2 · blocking=2 · non-blocking=0 · critical=0. Advisory only: sealed
  `run_hypothesis_foundry_real_exhaust.py:225` keeps a permanent, un-editable second
  `frozen_ready_total` formula (coherence = WARN) — worth an owner line in the closing record.

## Last 2 verdicts

- iter 7: ESCALATE — consolidation landed, seal held (59/59 hashes byte-identical); but QA certified
  "DoD ✓ Complete" while the browser lane never replayed TARGET J-07 — only the auditor caught it.
- iter 6: CONTINUE — J-07 passed and the first-read lock was written, but coherence FAILED on the
  duplicate `frozen_ready_total` computation, forcing this consolidation pass.

## Do not redo

- **`frozen_ready_total` consolidation is DONE** — `micro_routes.py:901-920` is the sole non-sealed
  owner; test `tests/test_run_hypothesis_foundry_real_exhaust.py:166-201`; iter-6 COHERENCE-FAIL
  retired. Do NOT chase the sealed CLI's copy — that needs breaking the era's seal.
- **Never edit a freeze-set file to make a check pass** (59 entries, verified byte-identical). Safe:
  `micro_routes.py`, `apps/backend/tests/**`, frontend. J-01..J-07 all re-verified this iteration
  (goldens 6/6 + J-07 1/1) — do not re-litigate them.
- **Capture rule:** screenshot Foundry subsections via `demo_runner --mode verify`, never the
  Chrome-MCP deep-scroll path — it reliably returns blank PNGs (4 identical blanks this iteration).
- **Replay the TARGET journey, not just the regression set**; "Frontend Present: no" never waives
  it. The equivalence test is a tautology (`families: []`) — the freeze-set guards, not the test.
