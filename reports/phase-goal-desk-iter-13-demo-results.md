# Demo Results — goal-desk-iter-13

**Demo Verdict:** RECORDED_WITH_NOTES
**Date:** 2026-07-28
**Frontend URL:** http://localhost:3301
**Iteration:** 13

## Captured Steps

| Step | Title | Journey | New | Screenshot |
|------|-------|---------|-----|------------|
| 01 | Open the Desk page | J-04 |  | reports/demo/goal-desk-iter-13/step-01.png |
| 02 | See the Desk before any top-up has run | J-09 | yes | reports/demo/goal-desk-iter-13/step-02.png |
| 03 | See every top-up run saved for good | J-09 | yes | reports/demo/goal-desk-iter-13/step-03.png |
| 04 | See exactly how each run went | J-09 | yes | reports/demo/goal-desk-iter-13/step-04.png |
| 05 | See the exact reason a pair failed | J-09 | yes | reports/demo/goal-desk-iter-13/step-05.png |
| 06 | Look back at a past scan | J-05 |  | reports/demo/goal-desk-iter-13/step-06.png |
| 07 | Jump from a ranked stock into its chart | J-05 |  | reports/demo/goal-desk-iter-13/step-07.png |
| 11 | Watch the tape settle into a read | J-07 |  | reports/demo/goal-desk-iter-13/step-11.png |
| 15 | Load its key price levels | J-07 |  | reports/demo/goal-desk-iter-13/step-15.png |

## Soft notes

- Step 02 — static frame, not a live capture from this record pass: the honest-empty Top-up Runs state is a one-way door on an append-only store, so it was captured on this same scoped rig's live, already-booted /desk page at 2026-07-28T17:02Z (before the first checkpoint run was written at 17:03:23Z) and spliced in here by the iteration-13 audit. Source: reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-topup-section.png. Steps 01 and 03-15 are live frames from the 2026-07-28 19:22 record pass against the same rig.
- Re-running demo_runner.py --mode record against this script would overwrite step-02.png with a populated frame — the empty state cannot be re-driven live on this rig.

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (record)
- **Demo mode:** record

## Scoped data root (TC-5 disclosure requirement)

Every frame in this walkthrough — the static step-02 empty state and the live
step-01/03-15 frames — was served by the SAME scoped throwaway copy of
`apps/backend/.data/`, never the ambient store. Absolute path:

```
/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/desk-iter13-scoped-qa
```

Seeded fresh this iteration via
`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301`; backend on
`:8301`, frontend on `:3301` pointed at it. The three checkpoint top-up runs the
populated frames show (`topup-2026-07-28-bad54d19fb21` done 404/404,
`topup-2026-07-28-a45eb8397844` cancelled 3/404, `topup-2026-07-28-c4de94d71e04` done
404/404 with 0 reused / 403 fetched / 1 failed) live in that root's
`.data/topup_runs/`. See `docs/handoffs/goal-desk-iter-13-dev.md` for full provenance
and the ambient-store zero-write proof.
