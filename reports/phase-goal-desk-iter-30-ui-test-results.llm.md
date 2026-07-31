# Goal Iteration 30 — UI Test Results

**Phase:** goal-desk-iter-30
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-18 | Every screen run leaves an append-only record of what it attempted — and a re-run under identical pins says so before it walks | happy-path | P1 | On a freshly-provisioned scoped rig with zero prior screen-run records, `/desk` shows the honest `data-testid="desk-screen-runs-empty"` "No screen runs recorded yet." before any Run Screen click; on the ambient rig, a completed full-walk row shows `101 / 101` and a reused run's own table row states "no walk was performed"; golden replay holds | Scoped rig (backend :8302 `TAPEOLOGY_DESK_UNIVERSE_DIR`=fresh empty dir, frontend :3302) loaded `/desk` as the FIRST action — `GET /research/desk/screen/runs` returned `{"runs":[],"latest":null,"integrity_errors":[]}`, DOM confirmed `data-testid="desk-screen-runs-empty"` with exact text "No screen runs recorded yet.", 1440×900 viewport with no horizontal scroll (scrollWidth=clientWidth=1425). Ambient rig (:3301) regression-checked via DOM read: `desk-screen-runs-table` shows one `101 / 101` full-walk row (screen-2026-07-31-c169546856c7) and two reused rows reading "reused screen-2026-07-31-c169546856c7 — no walk was performed", same screen_id both times (no divergence). Updated golden script `runs/goal-session-desk/journey-scripts/J-18.json` to assert these stable table substrings instead of the prior date/id-pinned "latest run" text (closing iter-29 audit finding T1); replayed clean via `demo_runner.py --mode verify` against the ambient rig (PASS). Scoped rig torn down at end of dispatch. | PASS | `reports/qa/goal-desk-iter-30-evidence/J-18-empty-state.png` |

---

## Passed Tests

### UT-J-18 — Screen run ledger: honest empty state + append-only record + reuse disclosure
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-30-evidence/J-18-empty-state.png`

**What was verified (this iteration's headline deliverable — closing `runs/goal-session-desk/iter-29/eval-confirm.md`'s REJECT):**

1. **Scoped rig provisioned fresh, throwaway, never the operator's `.data`.** A second backend instance was started on `127.0.0.1:8302` with `TAPEOLOGY_DESK_UNIVERSE_DIR` pointed at a brand-new directory under this session's scratchpad (never populated, never the ambient `apps/backend/.data`); a second frontend was started on `127.0.0.1:3302` with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8302` and an isolated `NEXT_DIST_DIR` (the project's own `next.config.mjs` support for this, added precisely so a scoped build never clobbers the shared ambient `.next`). Confirmed via curl that `GET /research/desk/universe` and `GET /research/desk/screen/runs` on the scoped backend both returned genuinely empty payloads before any browser action.
2. **Empty-state screenshot captured as the FIRST browser action against the rig**, before any Run Screen click (the load-bearing ordering iter-29's own lesson required): viewport set to 1440×900, navigated to `http://127.0.0.1:3302/desk`. DOM `extract` showed the "SCREEN RUNS" section rendering "∅ / No screen runs recorded yet."; a targeted `eval` confirmed the exact node: `{"found":true,"text":"∅No screen runs recorded yet.","tag":"DIV"}` at `[data-testid="desk-screen-runs-empty"]`. `document.documentElement.scrollWidth === clientWidth === 1425` — no horizontal scroll. Screenshot saved and visually confirmed non-blank (full page renders: nav, Desk heading, "Desk screen not computed yet." panel, Top-up Runs/Index Reconciliation/Screen Runs sections all honestly empty).
3. **Regression check of the populated/reused states** (not re-captured as new screenshots per this iteration's explicit Out-of-Scope — verified via DOM read on the ambient `:3301` rig instead, using data left by real `Run Screen` clicks in prior iterations): `desk-screen-runs-table` contains one row with `101 / 101` (attempted/total) producing `screen-2026-07-31-c169546856c7`, and two further rows reading `reused screen-2026-07-31-c169546856c7 — no walk was performed` — both reused rows carry the identical `screen_id`, so no drift from the previously-captured evidence.
4. **Golden replay script hardened.** `runs/goal-session-desk/journey-scripts/J-18.json` previously pinned its assertions to a specific, mutable run/screen id embedded in the "latest run" detail block's text (iter-29 audit finding T1 — the very next real run anywhere would break it). Rewrote steps 2–3 to assert stable substrings (`"101 / 101"`, `"no walk was performed"`) against the append-only `desk-screen-runs-table` testid instead, which never disappear once written. Linted clean (`demo_runner.py --mode lint`) and replayed clean against the live ambient rig (`demo_runner.py --mode verify` → `PASS`, evidence `J-18-verify.png` in the temp verify dir used for this check).
5. **Rig torn down** at the end of this dispatch: both scoped processes killed, scoped ports (`8302`/`3302`) confirmed free, scratch directories removed. Ambient rig (`:3301`/`:8301`) reconfirmed healthy afterward (`200`/`404` on their respective root routes, as expected).

**Important observation (not a J-18 acceptance failure, flagged for the evaluator/auditor):** iter-30's own IN SCOPE section describes two additional code fixes this cycle — (a) suppressing the "Latest run" detail block's amber `desk-screen-run-latest-unreached` note and `desk-screen-run-latest-counts` line for a `state:"done" && reused:true` run, and (b) `failed_member = null` (not `members[0]`) when a run crashes before any member is attempted. Neither change is present in the working tree (`git diff` against HEAD shows zero changes to `desk_screen_compute.py`, `page.tsx`, or `test_desk_screen_compute.py`; `docs/handoffs/goal-desk-iter-30-dev.md` states "no code changes were planned or made"). I verified live against the ambient rig: the latest (reused) run's detail block still renders `data-testid="desk-screen-run-latest-unreached"` ("101 members not reached", amber) and `data-testid="desk-screen-run-latest-counts"` ("0 ranked · 0 skipped (no bars) · 0 skipped (no basis)") unconditionally — i.e. TC-2 from the iteration's own test-first contract does not currently hold. This does NOT affect my J-18 PASS verdict because J-18's own Acceptance line (as authored in `docs/goal.md`, unchanged by this iteration) requires only that "a reused run's own row states that no walk was performed" — which is true of the append-only table row and was verified above — and does not name the "latest run" detail block's amber note/counts framing. The golden script was written to assert only against the stable table, so it stays valid regardless of whether/when this framing gap is later closed.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01, J-02, J-03, J-04, J-06, J-07, J-09, J-10, J-12, J-16 were explicitly out of scope for this dispatch (deterministic golden replay covers them separately — see `reports/phase-goal-desk-iter-30-regression-replay-results.md`).

---

## Environment

- **Frontend URL (ambient, regression checks):** http://localhost:3301
- **Frontend URL (scoped rig, TC-1 capture):** http://127.0.0.1:3302 (backend http://127.0.0.1:8302, `TAPEOLOGY_DESK_UNIVERSE_DIR` scoped to a throwaway directory) — torn down at end of dispatch
- **Browser:** Chrome via MCP (CDP 127.0.0.1:9222, headless, pinned profile)
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-desk-iter-30-evidence/`
