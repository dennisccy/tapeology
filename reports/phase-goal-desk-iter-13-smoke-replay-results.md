# Regression Replay — goal-desk-iter-13

**Phase:** goal-desk-iter-13
**Date:** 2026-07-28
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-13-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-13-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-13-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-13-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-13-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-13-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-13-evidence/J-08-verify.png |

J-06 (MCP contract) has no browser surface — re-confirmed separately via `test_mcp_server.py`'s
existing 17-tool contract; see `docs/handoffs/goal-desk-iter-13-dev.md`.

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-28
- **`--timeout-ms`:** 30000 (raised from the runner's 15000 default — see the J-07 note below)

## Scoped data root (TC-3/TC-5 disclosure requirement)

This replay ran against a SCOPED throwaway copy of `apps/backend/.data/`, never the ambient store.
Absolute path:

```
/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/desk-iter13-scoped-qa
```

Seeded fresh this iteration (distinct from `desk-iter9-scoped-qa` / `desk-iter10-scoped-qa` /
`desk-iter11-scoped-qa` / `desk-iter12-scoped-qa` / `desk-iter12-scoped-qa-empty`) via
`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301` — a full `cp -a` of the
ambient tree at this iteration's start. Backend served on `:8301`, frontend on `:3301` pointed at it
(`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301`). Both processes were booted BEFORE any top-up
run was recorded into the rig (this iteration's load-bearing ordering fix) and are left running
after this dispatch for any downstream lane that wants to independently reload the live rig. See
`docs/handoffs/goal-desk-iter-13-dev.md` for the full provenance, the 3 recorded checkpoint top-up
runs, and the ambient-store zero-write proof.

None of J-01/J-02/J-03/J-04/J-05/J-07/J-08's own golden steps click a Run Screen/Top-up/Compute
control (verified by inspecting each script before this replay) — J-05 and J-07 click
navigation/watch/load controls that are existing KEPT-surface behavior, not desk-compute triggers,
so replaying them against the scoped rig carries no anti-goal risk either way.

## Note — UT-J-07 transient timing flake

The first pass (all 7 journeys together, `--timeout-ms 30000`) reported `UT-J-07` FAIL: step 04
("Watch" click → expect "Buyer Control") did not see that text appear in time. `J-07.json` carries
its own `default_timeout_ms: 15000` and no per-step override on step 4, so the script's own embedded
default governs that step's wait regardless of the CLI `--timeout-ms` value — this iteration's
`--timeout-ms 30000` did not change step 4's effective budget, unlike iteration 12's own note, which
assumed the CLI flag always won; empirically it does not for a step that inherits the script's own
`default_timeout_ms`. This is a pre-existing golden-script property, not something this iteration
touched (zero diff to `journey-scripts/J-07.json`).

Before re-running, the SIM-BUYER watch left running by the failed attempt was stopped explicitly
(`DELETE /watch/SIM-BUYER` → `{"ticker":"SIM-BUYER","status":"stopped"}`) — the iteration-12
"leftover feeder task" lesson, applied proactively rather than discovered after the fact. A
single-journey re-run of J-07 alone then passed immediately on the first retry, and the full
7-journey set was re-run together end to end (0 failed) — the table and verdict above are that
clean, all-7-together run (the SIM-BUYER watch it started was stopped again afterward).

SIM-BUYER's warm-up-to-classification latency is a property of the simulated tape engine's own
real-time tick cadence, unrelated to any desk/top-up code path this iteration touched (zero product
diff). Disclosed per the "no silent retry" honesty norm — this is a timing observation on an
existing kept-surface journey, not a finding that changes the PASS verdict above.
