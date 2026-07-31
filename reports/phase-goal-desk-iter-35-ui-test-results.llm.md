# Goal-Desk Iteration 35 — UI Test Results

**Phase:** goal-desk-iter-35
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Note: this is a goal-mode LEAN dispatch — only J-20 was in scope for live browser
verification this run. J-03, J-04, J-05, J-06, J-07, J-12, J-13, J-14, J-16, J-18 are the
required-still-passing journeys and were verified separately by the deterministic golden
replay (see `reports/phase-goal-desk-iter-35-regression-replay-results.md` — 10/10 passed,
0 skipped, replayed 2026-07-31), per the dispatch instruction not to re-drive them here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-20 | Every recorded screen states how it differs from the screen recorded before it | smoke | P1 | `/desk` renders a new read-only "Screen Comparison" section for the currently-displayed screen, showing (a) the identical state for the latest-vs-prior pair, (b) a churned state (≥1 row rank-moved ≥20 places, ≥1 side change) when an older churned pair is selected, and (c) an honest "no earlier recorded screen" state on the ledger's oldest snapshot — all legible at 1440×900 with no horizontal scroll and the ranked briefing table unchanged from J-16 | All three states rendered exactly as specified, confirmed via both DOM extraction and full-page screenshots (see Passed Tests below for exact text/values) | PASS | see per-state screenshots below |

---

## Passed Tests

### UT-J-20 — Every recorded screen states how it differs from the screen recorded before it
**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-desk-iter-35-evidence/J-20-identical-state.png`
- `reports/qa/goal-desk-iter-35-evidence/J-20-churned-state.png`
- `reports/qa/goal-desk-iter-35-evidence/J-20-no-earlier-state.png`

Steps executed (Chrome MCP, viewport 1440×900, against the running ambient rig
`http://localhost:3301` / `http://localhost:8301`):

1. Navigated to `/desk`. Confirmed no horizontal scroll at 1440×900
   (`document.documentElement.scrollWidth === clientWidth === 1425`, i.e. exactly the
   viewport minus scrollbar — the ranked briefing table renders unchanged from J-16, all
   100 rows with their existing rank/symbol/side/class/distance/score/coverage/tick-evidence/
   basis/history/band/opposite/levels columns intact).
2. **Identical state (default view):** the default-displayed screen is
   `screen-2026-07-31-c169546856c7` (latest); its default-resolved base is
   `screen-2026-07-30-bad6387963ef` — exactly the pair goal.md itself names for this
   example. The new "Screen Comparison" section (rendered last on the page, after the
   ranked table and Top-up Runs/Index Reconciliation/Screen Runs) showed: "This screen"
   `id screen-2026-07-31-c169546856c7`, "Compared against" `id screen-2026-07-30-bad6387963ef`,
   both bar-store signatures `ae2c740d1a70c9c7` (equal), the counts line
   `rows compared 100 · rank changed 0 · side changed 0 · entered 0 · left 0`, and the honest
   line "The compared snapshots' ranked rows are identical." — byte-identical to what
   `GET /research/desk/screen/compare?id=screen-2026-07-31-c169546856c7` serves (cross-checked
   via curl before the browser pass). Screenshot: `J-20-identical-state.png`.
3. **Churned state:** clicked the Screen History row for `screen-2026-07-25-bd0b37ebc426`
   (`tr[data-screen-id="screen-2026-07-25-bd0b37ebc426"]`). Its default-resolved base came
   back as `screen-2026-07-20-ca185294a384` — exactly goal.md's named churned pair. The
   comparison section updated to show `rows compared 100 · rank changed 95 · side changed 12
   · entered 0 · left 0` and a capped table ("showing 20 of 100 rows") with rows whose ranks
   moved far more than 20 places (e.g. PEP rank 2 vs 64 = -62, DHR rank 6 vs 72 = -66, TMUS
   rank 10 vs 71 = -61) and rows whose side differs between the two recordings (e.g. UPS
   support vs resistance, DHR support vs resistance, HONA support vs resistance) — satisfying
   both the "≥1 row rank moved by ≥20 places" and "≥1 row's side differs" acceptance clauses.
   Screenshot: `J-20-churned-state.png`.
4. **No-earlier-recorded-screen state:** clicked the Screen History row for the ledger's
   oldest snapshot `screen-2026-06-22-3ecd45c062c7`
   (`tr[data-screen-id="screen-2026-06-22-3ecd45c062c7"]`). The comparison section showed only
   "This screen" meta (`id screen-2026-06-22-3ecd45c062c7`) and the honest line "No earlier
   recorded screen exists to compare against." — no counts line, no table, matching the
   backend's `base: null` / `base_resolution: "none_earlier"` response for that id (cross-checked
   via curl). Screenshot: `J-20-no-earlier-state.png`.
5. Backend cross-check (curl, before the browser pass) confirmed all three
   `GET /research/desk/screen/compare` responses match the UI exactly, including
   `base_resolution` values (`default_prior_date` / `default_prior_date` / `none_earlier`).

**Note on evidence capture:** a direct viewport `screenshot` action taken after scrolling
past roughly Y≈900px on this tall page came back as a single solid-color (2,6,23) blank
frame — a known browser-tool rendering quirk on deep-scrolled pages in this environment,
already documented in `docs/handoffs/goal-desk-iter-34-dev.md`. Worked around exactly as
that prior iteration did: took a `fullpage: true` capture (confirmed non-blank, 13,000+
distinct colors) and cropped the Screen Comparison section's own bounding-rect region out
with PIL. All three evidence PNGs above are real renders (verified non-blank, distinct
md5sums, opened and visually inspected before citing them here).

---

## Failed Tests

None.

---

## Skipped Tests

None. J-03/J-04/J-05/J-06/J-07/J-12/J-13/J-14/J-16/J-18 were explicitly out of scope for
this dispatch (deterministic replay covers them — see note above), not skipped due to any
failure or unavailability.

---

## Golden Replay Script

Wrote `runs/goal-session-desk/journey-scripts/J-20.json` (schema_version 1). Deliberately
tests only the structural presence of the Screen Comparison section on the default view plus
the no-earlier-screen branch on the ledger's permanently-oldest snapshot
(`screen-2026-06-22-3ecd45c062c7`) — per this iteration's own lesson ("assert stable
substrings, never a specific run's exact counts/dates"), the identical/churned pair named in
goal.md will stop being "the default view" the moment a new real screen run lands, so pinning
those ids/counts would make the next ambient `Run Screen` click a false regression (the same
trap iter-30's audit caught in `J-18.json`). Linted clean
(`python3 scripts/automation/lib/demo_runner.py --mode lint`) and replayed green end-to-end
against the live rig via `--mode verify` before being finalized.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, CDP 127.0.0.1:9222), viewport 1440×900
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-desk-iter-35-evidence/`
