# goal-desk-iter-24 — UI Test Results

**Phase:** goal-desk-iter-24
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Scope note: per the goal-mode LEAN dispatch, this run tests ONLY J-16. J-01–J-05, J-07–J-14 are
covered separately by deterministic golden replay (13 stored scripts) and are not re-driven here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression-fix | P1 | At a 1440×900 viewport, no horizontal scroll (`scrollWidth<=clientWidth`), one screenshot shows rank/symbol/side/class/distance/score/coverage/tick-evidence/basis/history/band/opposite/levels for the top row; 4 coverage badges on one line, row height ≤60px; first 8 ranked rows legible with rank 1–8 in served order; legacy snapshot honest-absence strings intact; skipped-members table still groups honestly | `table.scrollWidth` 1214px === container `clientWidth` 1214px (doc-level 1425===1425) — zero horizontal scroll, closing iter-23's UT-07 FAIL (was 1795/1214); all 12 disclosures + new `rank` cell legible in one screenshot of row 1 (BRK-B); coverage badges share one top y-coordinate on every row checked (4/4, one line); row height: first 8 rows all 57px, full-table 98/100 rows ≤60px (2 rows — positions 24 & 80 — measure 63px, a disclosed 3px residual); rank cells read 1,2,3,4,5,6,7,8 in order on rows 1–8; legacy snapshot `screen-2026-06-22-3ecd45c062c7` renders all 5 honest-absence strings verbatim; Skipped Members table still groups "SKIPPED — NO BASIS SESSION (1)" honestly; SHA-256 listing of `.data/{screen,universe,topup_runs,index_reconcile_runs}` identical before/after (zero write) | PASS | `reports/qa/goal-desk-iter-24-evidence/J-16-viewport.png` (+ `J-16-eight-rows-crop.png`, `J-16-legacy-snapshot.png`, `J-16-skipped-table.png`) |

---

## Passed Tests

### UT-J-16 — The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll

**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-24-evidence/J-16-viewport.png`, `J-16-eight-rows-crop.png`, `J-16-legacy-snapshot.png`, `J-16-skipped-table.png`

**Preconditions:** Frontend `:3301` and backend `:8301` up (both curl 200). Latest recorded screen
already populated (`screen-2026-07-30-bad6387963ef`, 100 ranked / 1 skipped — no new Run Screen
triggered, per the iteration's explicit OUT OF SCOPE). Chrome MCP attached to the pinned `:9222`
headless profile.

**Steps executed (Chrome MCP, viewport set to 1440×900):**

1. Navigated to `http://localhost:3301/desk`, waited for `BRK-B` (top row) to render.
2. **TC-1/TC-2 (screenshot + DOM measurement):** Screenshot at 1440×900 shows row 1's rank (1),
   symbol (BRK-B), side (support), class chip (Class A), distance chip (0.00 bps), score
   (1673.00), coverage badges (1h/4h/1d/1w on one line), tick-evidence (absent, correctly — false
   for this row), basis (`2026-07-27 · 3 d before as-of`), history (`502 sessions · from
   2024-07-25`), band (`band 495.45–497.18 · close 497.18`), opposite (`opposite resistance A
   497.20–500.67 · 0.40 bps`), levels (`155 · 1d 68 · 1h 57 · 1w 11 · 4h 19`) — all legible at once,
   no truncation. DOM `eval`: `table[data-testid="desk-screen-rows-table"].scrollWidth` = 1214,
   its `overflow-x-auto` ancestor's `clientWidth` = 1214 (equal — zero horizontal scrollbar);
   `document.documentElement.scrollWidth` 1425 === `clientWidth` 1425 (no page-level horizontal
   scroll either). This is iter-23's UT-07 measurement (1795px inside 1214px, FAIL) turned PASS,
   quoted the same way.
3. **TC-3 (badge line + row height):** `eval` over rows 1–3: all 4 `desk-coverage-badge` elements
   per row share one `top` y-coordinate (one line, not four). Row-height sweep over all 100 ranked
   rows: first 8 rows uniformly 57px (well under the 60px target); full-table min 56.5px / max
   63px; exactly 2 of 100 rows (ranked positions 24 and 80) measure 63px — matches the dev
   handoff's disclosed residual exactly (round-number badge's own 22px height landing on a 3rd
   line for those two rows only). The reviewer already judged this a non-blocking NOTE; 98/100
   rows and all of the acceptance-required rows 1–8 meet ≤60px.
4. **TC-4 (first 8 rows legible with rank order):** Row 8's bottom (1006px) exceeds the 900px
   viewport, so a full-page screenshot was taken and cropped to y=0–1050 to show rows 1–8 in one
   image (`J-16-eight-rows-crop.png`). `rank` cells on rows 1–8 read `1, 2, 3, 4, 5, 6, 7, 8` in
   that exact served order (`eval`-confirmed), each row's full row of disclosures legible.
5. **TC-5 (legacy snapshot + skipped table):** Located the 2026-06-22 Screen History row
   (`data-screen-id="screen-2026-06-22-3ecd45c062c7"`, the pre-J-15 legacy snapshot), clicked it,
   confirmed via `eval`/`document.body.innerText` search that all five honest-absence strings
   render verbatim: "basis not recorded in this snapshot", "history not recorded in this
   snapshot", "close not recorded in this snapshot" (inside `band 298.02–300.10 · close not
   recorded in this snapshot`), "opposite wall not recorded in this snapshot", "composition not
   recorded in this snapshot". Screenshot captured (`J-16-legacy-snapshot.png`). Returned to
   Latest; the Skipped Members table on the latest screen still groups honestly — "SKIPPED — NO
   BASIS SESSION (1)" with symbol `NOW`, reason `no basis` (`J-16-skipped-table.png`, cropped from
   the earlier full-page capture).
6. **TC-12 (zero-write check):** SHA-256 listing of every file under
   `apps/backend/.data/{screen,universe,topup_runs,index_reconcile_runs}` taken immediately before
   and immediately after this entire QA pass — byte-identical (`diff` empty). This pass triggered
   no Run Screen / top-up / reconcile — only navigation and Screen History row selection (a plain
   `GET /research/desk/screen?id=...` read).

**No anti-goal or regression concern observed:** rank column renders the served order verbatim
(no client-side sort observed across the 100-row sweep); class/distance render as bordered chips
with unchanged text; every value read matched what `GET /research/desk/screen` serves (spot-checked
BRK-B row 1 and the legacy snapshot's raw JSON payload structure via the earlier `curl` probe).

**Golden replay script:** written to
`runs/goal-session-desk/journey-scripts/J-16.json` (7 steps: load `/desk`, assert the ranked table
and a rank cell render, assert `BRK-B` real content, click the legacy Screen History row, assert
its honest-absence string, return to `/desk`). Lint-checked
(`demo_runner.py --mode lint` → `J-16 ok`) **and** independently replayed end-to-end
(`demo_runner.py --mode verify --journeys J-16` → `1 journey(s), 0 failed (verdict: PASS)`,
evidence `J-16-verify.png`) — not merely linted.

---

## Failed Tests

None.

---

## Skipped Tests

None — J-01–J-05, J-07–J-14 were explicitly excluded from this run's scope (deterministic replay
covers them separately per the dispatch) rather than skipped for cause.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome (headless, CDP `:9222`, pinned profile) via
  `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Viewport:** 1440×900
- **Test Date:** 2026-07-30
- **Latest screen tested:** `screen-2026-07-30-bad6387963ef` (100 ranked rows / 1 skipped)
- **Legacy snapshot tested:** `screen-2026-06-22-3ecd45c062c7` (pre-J-15)
