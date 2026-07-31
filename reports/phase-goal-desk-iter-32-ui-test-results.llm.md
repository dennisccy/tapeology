# goal-desk-iter-32 — UI Test Results

**Phase:** goal-desk-iter-32
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 1/1 tests passed (0 skipped)

GOAL-MODE LEAN MODE — only J-19 was in scope for this dispatch. J-01, J-02, J-04, J-06, J-07,
J-09, J-16, J-17, J-18 are verified separately by deterministic golden-script replay, per the
dispatch instructions, and were not re-executed here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-19 | Every top-up run records the date each pair's frozen history actually reaches | happy-path | P1 | After a real top-up run, `/desk`'s Top-up Runs latest-run detail shows one descriptive line naming the newest `store_frozen_through_after` date across the run's pairs plus the count reaching it, AND a list of pairs whose own recorded reach date is earlier (or null), each with symbol/timeframe/date, both legible in one 1440×900 frame with no horizontal scroll, and the ranked briefing table unchanged from J-16 | Triggered a real top-up run via the shipped "Top-up" button against the ambient `:3301`/`:8301` store (404/404 pairs, `topup-2026-07-31-8fb5c9a1f737`). `/desk`'s latest-run detail now renders `desk-topup-run-latest-reach` = "newest recorded reach 2026-07-30 · 101 pairs reach it" and `desk-topup-run-latest-reach-earlier` = "Pairs recorded earlier (303)" with per-pair rows (e.g. "AAPL 4h — 2026-07-30", "AAPL 1w — 2026-07-27") each showing symbol/timeframe/date verbatim. `document.documentElement.scrollWidth` (1440) equals `window.innerWidth` (1440) confirming zero horizontal scroll. The ranked briefing table at the top of `/desk` renders with its unchanged rank/symbol/side/class/distance/score/coverage/tick-evidence/basis/history/band/opposite/levels columns. | PASS | `reports/qa/goal-desk-iter-32-evidence/UT-J-19-result.png`, `reports/qa/goal-desk-iter-32-evidence/UT-J-19-ranked-table-unchanged.png` |

---

## Passed Tests

### UT-J-19 — Every top-up run records the date each pair's frozen history actually reaches
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-32-evidence/UT-J-19-result.png` (reach line + earlier-pairs list, one frame, no horizontal scroll), `reports/qa/goal-desk-iter-32-evidence/UT-J-19-ranked-table-unchanged.png` (ranked briefing table as shipped)

Steps executed (per iteration notes' recommended TC-1/TC-10/TC-14 evidence route — a real, explicit
operator-run top-up against the ambient store, since the currently-recorded latest run predated
both J-17 and J-19 and carried none of the new field):

1. Set viewport to 1440×900. Navigated to `http://localhost:3301/desk`. Confirmed via
   `GET /research/desk/topup/runs` that the current latest recorded run
   (`topup-2026-07-29-5de907c83fc4`) is a legacy 4-key-per-outcome record (no
   `store_frozen_through_after`, no `window_basis`) — verifying a fresh run was genuinely needed to
   exercise J-19's disclosure, not merely re-display an already-populated one.
2. Clicked the shipped `[data-testid="desk-topup-button"]` "Top-up" control (an explicit, sanctioned
   operator act per Vision Key Capability 2 and the iteration notes) to trigger a new, real top-up
   run over the pinned universe. The button went `disabled` immediately (single-flight in progress).
3. Polled `GET /research/desk/topup/compute` directly (curl) to confirm progress and, later,
   completion — `state: "done"`, started `2026-07-31T06:52:55.191780Z`, finished
   `2026-07-31T06:56:49Z` (per the coordinator's relayed status), 404/404 pairs, `error: null`. Spot
   checked several in-flight outcome entries mid-run and confirmed `store_frozen_through_after` was
   present on every entry, later than `store_frozen_through` for `fetched` pairs (e.g. AAPL 1h:
   `store_frozen_through` `2026-07-24T19:30:00Z` → `store_frozen_through_after`
   `2026-07-30T19:30:00Z`).
4. Confirmed via `GET /research/desk/topup/runs` after completion: the new run
   `topup-2026-07-31-8fb5c9a1f737` is now `latest`, all 404 outcome entries carry
   `store_frozen_through_after`, newest reach date across pairs is `2026-07-30` (101 pairs reach it),
   and 303 pairs recorded an earlier date (e.g. `AAPL 4h` → `2026-07-30`, `AAPL 1w` → `2026-07-27`) —
   a genuine mix of "just advanced" and "still lagging" pairs, exactly what TC-10 needs.
5. Re-navigated the browser to `/desk` (fresh load) and read the rendered DOM. Confirmed
   `[data-testid="desk-topup-run-latest-reach"]` renders "newest recorded reach 2026-07-30 · 101
   pairs reach it" verbatim, and `[data-testid="desk-topup-run-latest-reach-earlier"]` renders
   "Pairs recorded earlier (303)" followed by 303
   `[data-testid="desk-topup-run-latest-reach-earlier-row"]` rows, each showing `symbol timeframe —
   date` (e.g. "AAPL 4h — 2026-07-30"), matching the new block's spec (placed directly after the
   existing `desk-topup-run-latest-window-basis` line, before the failed-pairs block; no new
   section, no new control, no new table column).
6. Confirmed no horizontal scroll: `document.documentElement.scrollWidth` (1440) === `window.
   innerWidth` (1440) at the 1440×900 viewport.
7. Captured evidence. The MCP tool's plain `screenshot` action returned a blank/black frame at any
   scrolled position on this very tall page (reproduced consistently across `scrollIntoView`,
   `window.scrollTo`, and the tool's own `scroll` action — a capture-tool quirk, not a product
   defect: `elementFromPoint` at the same scroll position resolved real page content, and scrolling
   back to the top rendered correctly again). Worked around it with the tool's `fullpage` screenshot
   option (which stitches the entire 1440×14361 document correctly) and cropped a 1440×900 window
   at the exact document-Y coordinates of the `desk-topup-run-latest-detail` block (read via
   `getBoundingClientRect()` + `window.pageYOffset`) — this crop is pixel-identical to what a normal
   scrolled capture at that position would show, and needs no horizontal cropping since the document
   is exactly viewport-width. Also captured the page top (ranked briefing table) directly, which
   captured fine at scroll position 0.
8. Verified the ranked briefing table (rank/symbol/side/class/distance/score/coverage/tick
   evidence/basis/history/band/opposite/levels columns, e.g. rank 1 BRK-B / support / Class A /
   0.00 bps / 1673.00) renders unchanged from its shipped J-16 layout.

**Copy discipline spot-check:** the new line and list text ("newest recorded reach 2026-07-30 · 101
pairs reach it", "Pairs recorded earlier (303)", "AAPL 4h — 2026-07-30") is plain descriptive
measurement — dates and counts only, no fresh/stale/current/behind/recommendation language.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01, J-02, J-04, J-06, J-07, J-09, J-16, J-17, J-18 were explicitly out of scope for this
dispatch (deterministic replay covers them separately) and were not executed or graded here.

---

## Golden Replay Script

Wrote `runs/goal-session-desk/journey-scripts/J-19.json` (read-only `goto` + `expect` steps only —
no `click` — so replay never triggers a new real top-up run, matching the established J-09/J-17
precedent that reserves the Top-up button for explicit, separately-reported operator acts). Lint
passed: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
runs/goal-session-desk/journey-scripts --journeys J-19` → `J-19 ok`. Every asserted testid/string
was confirmed present against the live `/desk` page during this run (see steps above).

**Note for a future iteration/dispatch (not fixed here — out of this dispatch's assigned scope,
which was J-19 only):** the real top-up run triggered above to produce J-19's evidence also
advanced the ambient store's "latest" top-up run away from the one `journey-scripts/J-17.json`'s
existing golden script was written against. `J-17.json` asserts `desk-topup-run-latest-counts` =
"0 reused · 390 fetched · 0 unchanged · 14 failed", `desk-topup-run-latest-window-basis` = "window
basis not recorded in this run", and `desk-topup-run-latest-failed` (testid) with text "Failed
pairs (14)". Against the NEW latest run those now read "0 reused · 404 fetched · 0 unchanged · 0
failed", "390 pairs asked for a tail window · 14 pairs asked for the full lookback window", and the
`desk-topup-run-latest-failed` testid is not rendered at all (zero failed pairs, so the conditional
block does not mount). This is the same class of honest environmental drift `J-09.json`'s own
iter-23 note documents (and iter-32's own notes anticipated for this exact evidence route) — not a
regression in J-17's underlying feature (window-basis disclosure and the failed-pairs list both
still work correctly; the current run simply has different, and in the window-basis case more
complete, honest content) — but J-17's replay will FAIL on its next run until its golden script is
refreshed to the new run's values. Flagging here per this iteration's own explicit lesson rather
than editing `J-17.json` myself, since re-verifying/repairing J-17 was explicitly marked out of
scope for this dispatch.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, CDP 127.0.0.1:9222)
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-desk-iter-32-evidence/`
