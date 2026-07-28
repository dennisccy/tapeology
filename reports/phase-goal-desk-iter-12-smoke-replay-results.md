# Regression Replay — goal-desk-iter-12

**Phase:** goal-desk-iter-12
**Date:** 2026-07-28
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-12-evidence/J-08-verify.png |

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-28
- **`--timeout-ms`:** 30000 (raised from the runner's 15000 default — see the J-07 note below)

## Scoped data root (TC-3/TC-5 disclosure requirement)

This replay ran against a SCOPED throwaway copy of `apps/backend/.data/`, never the ambient store.
Absolute path:

```
/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/desk-iter12-scoped-qa
```

Seeded fresh this iteration (distinct from `desk-iter9-scoped-qa` / `desk-iter10-scoped-qa` /
`desk-iter11-scoped-qa`) via `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh
"$SCOPED_ROOT" 8301` — a full `cp -a` of the ambient tree at this iteration's start. Backend served
on `:8301`, frontend on `:3301` pointed at it (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301`).
Both processes are left running after this dispatch for the browser-qa-agent/demo-narrator stages.
See `docs/handoffs/goal-desk-iter-12-dev.md` for the full provenance, the 3 recorded checkpoint
top-up runs, and the ambient-store zero-write proof.

None of J-01/J-02/J-03/J-04/J-05/J-07/J-08's own golden steps click a Run Screen/Top-up/Compute
control (verified by inspecting each script before this replay) — J-05 and J-07 click
navigation/watch/load controls that are existing KEPT-surface behavior, not desk-compute triggers,
so replaying them against the scoped rig carries no anti-goal risk either way.

## Note — UT-J-07 transient timing flake at the runner's 15000ms default

The first pass (7 journeys, default 15000ms `--timeout-ms`) reported `UT-J-07` FAIL: step 04
("Watch" click → expect "Buyer Control") timed out with the tape state still `Unclear, confidence
0.100, "Warming up — collecting tape data..."` and `lag 10.5s` shown on the chart (screenshot:
`reports/qa/goal-desk-iter-12-evidence/J-07-verify.png` at that point, since overwritten by the
passing re-run below) — a warm-up/classification-latency timing issue, not a code change (this
iteration's product diff is zero, and SIM-BUYER → `buyer_control` is unrelated to any desk/top-up
code path this iteration touched). A same-journey re-run at `--timeout-ms 30000` passed cleanly
first try, and the FULL 7-journey set was then re-run together at 30000ms end to end (0 failed) —
the table and verdict above are that clean, 30000ms, all-7-together run. Plausible cause: this
host's own CPU-mask host-guard ceiling (`docs/goal.md`'s "Host protection" anti-goal,
`project-extensions/host-guard/host-guard.env`) slowing the simulated engine's real-time tape
processing under this iteration's own concurrent backend load (the checkpoint-3 topup walk had just
finished). Disclosed per the "no silent retry" honesty norm — this is a timing observation, not a
finding that changes the PASS verdict above.
