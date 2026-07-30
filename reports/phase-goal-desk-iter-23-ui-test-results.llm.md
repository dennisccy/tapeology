# Phase goal-desk-iter-23 — UI Test Results

**Phase:** goal-desk-iter-23
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass; all P1 tests pass. UT-07 (P2, ux) failed but
     does not gate the verdict per the pass criteria. -->

**Overall:** 8/9 tests passed (0 skipped) — plus 2 additional goal-mode regression journeys
(J-06, J-09) both PASS.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Ranked table (`desk-screen-rows-table`) present, header includes `levels` after `opposite`, no errors | Page loaded cleanly; table present with 100 ranked rows; header row confirmed via DOM to end `...band, opposite, levels`; no error boundary/blank screen | PASS | `reports/qa/goal-desk-iter-23-evidence/UT-01-result.png` |
| UT-02 | `levels` header visible beside `band`/`opposite` | smoke | P1 | Header order `...band, opposite, levels`, `levels` is last column | `eval` over `thead th` returned exactly `["symbol","side","class","distance","score","coverage","tick evidence","basis","history","band","opposite","levels"]` — `levels` last, nothing to its right | PASS | `reports/qa/goal-desk-iter-23-evidence/UT-04-legacy-scrolled.png` (header row visible) |
| UT-03 | Populated row shows tally + round-number badge | happy-path | P1 | Cell reads `<N> levels · <tf> <n> ...`, per-tf sum == N; badge present iff `band_round_number` true | Ran a NEW screen (`screen-2026-07-30-bad6387963ef`, via "Run Screen" for 2026-07-30, a date not previously recorded). BRK-B: `155 levels · 1d 68 · 1h 57 · 1w 11 · 4h 19` (68+57+11+19=155 ✓). AMT: `5 levels · 1d 3 · 1h 1 · 4h 1` (3+1+1=5 ✓). ORCL: `2 levels · 1h 1 · 1d 1` (✓). MA: `121 levels · 1d 58 · 1h 41 · 1w 8 · 4h 14` **round number** badge present (58+41+8+14=121 ✓); confirmed via `data-testid="tradable-band-round-number"` element found with text "round number". Rows without `band_round_number` show no badge. | PASS | `reports/qa/goal-desk-iter-23-evidence/UT-03-populated-levels-badge.png` (shows ≥100-level row, two ≤5-level rows, and the round-number badge all in one frame), `UT-03-populated-levels.png` |
| UT-04 | Legacy screen renders honest absence copy | error | P1 | Every row's `levels` cell reads exactly "composition not recorded in this snapshot"; no badge | Selected the ambient legacy screen `screen-2026-07-20-ca185294a384` (recorded before this iteration). All 100 visible ranked rows' `levels` cells read exactly "composition not recorded in this snapshot"; no round-number badge anywhere | PASS | `reports/qa/goal-desk-iter-23-evidence/UT-04-legacy-scrolled.png` |
| UT-05 | Pre-existing columns unaffected | regression | P1 | symbol/side/class/distance/score/coverage/tick-evidence/basis/history/band/opposite all render as before, unaffected by the new column | On the legacy screen, first row (BRK-B): `support`, `Class A / nearest same-class band`, `0.00 bps`, `1763.00`, coverage badges `1h 4h 1d 1w`, `basis 2026-07-17 · 3 d before as-of`, `history 496 sessions · from 2024-07-25`, `band 488.50–490.91 · close 490.91`, `opposite resistance A 490.97–494.39 · 1.22 bps` — all correctly formatted, positions unchanged, unaffected by the new `levels` column | PASS | `reports/qa/goal-desk-iter-23-evidence/UT-07-fail.png` (left columns), `UT-04-legacy-scrolled.png` (right columns) |
| UT-06 | Symbol tooltip unchanged (no new line) | ux | P2 | Tooltip does not mention `band_member_count`/`band_round_number`/`band_member_timeframes`/`levels`/"round number"; existing content unchanged | Read the `title` attribute of the drill-in anchor under `desk-row-symbol` via DOM: `"distance 0 bps · score 1763 · basis ... · band ... · bands by class A 10 · B 0 · C 0 · unclassified 0 · 1h window last requested: ... "` — none of the five forbidden strings present; content matches the established J-14 `bands_by_class`-precision tooltip pattern | PASS | Verified via DOM `title` attribute read-out (no native-tooltip screenshot needed — this test's acceptance is content-absence, not a photographed UI; the T-10a headed rig is reserved for acceptance lines that require photographing native browser chrome) |
| UT-07 | `levels` column discoverable without scroll at ≥1440px | ux | P2 | `levels` header + a populated/legacy-absent cell visible without horizontal scroll at 1440px width | At 1440px viewport, the ranked table's own content width is 1795px inside a 1214px-wide scrollable container (`overflow-x: auto`); the `levels` header's right edge sits at x≈1901, far outside the 1214px visible area. The table already required horizontal scroll to reach `opposite` before this column was even added — `levels` inherits that pre-existing condition and is NOT visible without scrolling at 1440px | **FAIL** | `reports/qa/goal-desk-iter-23-evidence/UT-07-fail.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression (goal-mode) | — | MCP server advertises exactly 17 tools incl. `desk_universe`/`desk_screen`; `get_endpoint` allowlist reaches `/research/desk/screen`; suite green | Backend-only journey, no UI surface (confirmed via ui-surface-map: 0 UI impact). Verified via code + live endpoint checks: `app/mcp/__init__.py` registers exactly 17 tools by name (`tape_state, tape_features, tape_history, datasets, bars, levels, tradability, setups, backtests, strategies, edge_report, desk_universe, desk_screen, pnl_ledger, taxonomy, ui_route_map, get_endpoint`), matching the 17 `mcp__tapeology__*` tools visible in this session's own tool roster; `desk_universe`→`/research/desk/universe`, `desk_screen`→`/research/desk/screen` confirmed in `_STATIC_PATHS`; both endpoints respond HTTP 200 with valid JSON; `get_endpoint`'s allowlist `("/tape/", "/research/", "/meta/")` reaches both new paths. `tests/test_mcp_server.py` (38 tests) and `tests/test_desk_screen.py` (78 tests) both 100% green via project venv | PASS | Verified via `apps/backend/app/mcp/__init__.py` inspection + `curl` against the running backend + `pytest` run (no browser UI exists for this journey) |
| UT-J-09 | Every top-up run leaves an append-only record | regression (goal-mode, flagged) | — | Top-up Runs section on `/desk`: honest-empty before any run, or a real recorded run's stats/failed-pair detail legible after one | The stored golden script (`J-09.json`) FAILED replay because it asserted the honest-EMPTY text "No top-up runs recorded yet.", but the ambient store now holds a REAL top-up run (`topup-2026-07-29-5de907c83fc4`, recorded between iter-11 and iter-23) — exactly the environmental-drift scenario the golden's own notes predicted. Re-executed live: `/desk`'s "Top-up Runs" table shows the run (date, id, state `done`, `404 / 404` attempted, universe snapshot); the "LATEST RUN" detail panel shows `state: done`, `404 of 404 pairs attempted`, `0 reused · 390 fetched · 14 failed`, and all 14 failed pairs' verbatim detail text (e.g. "no data for AAPL 1h in the requested window ... Yahoo Finance serves 1h bars only for the last 730 days..."), legible and correctly rendered. This is a stale-golden false-negative, not a product regression — golden REPAIRED (see below) | PASS | `reports/qa/goal-desk-iter-23-evidence/UT-J-09-topup-runs.png` (full page at reduced zoom to avoid a headless-screenshot scrollY rendering glitch — see Notes), cropped close-ups `UT-J-09-topup-runs-crop3.png` / `-crop4.png` |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-23-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`; `desk-screen-rows-table` present with 100 ranked rows + 1 skipped-member row; provenance panel rendered; header row confirmed (via DOM query) to end `...band, opposite, levels`. No blank screen, no error boundary.

### UT-02 — `levels` header visible beside `band`/`opposite`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-23-evidence/UT-04-legacy-scrolled.png`
- `Array.from(thead th).map(t => t.textContent)` returned `[..., "band", "opposite", "levels"]` — `levels` is the last header cell, nothing follows it.

### UT-03 — Populated row shows the wall-composition tally and round-number badge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-23-evidence/UT-03-populated-levels-badge.png`, `UT-03-populated-levels.png`
- Clicked "Run Screen" (`desk-run-screen-button`) for 2026-07-30 (a screen_date not previously recorded); waited ~4 minutes for the 101-member compute to finish (polled `GET /research/desk/screen/compute`). Resulting screen `screen-2026-07-30-bad6387963ef` has `band_member_count` on all 100 ranked rows, ranging 1–4,014, with 16 rows carrying `band_round_number: true`.
- Verified pattern + sum invariant on multiple rows (BRK-B 155=68+57+11+19, AMZN 144=52+57+16+15+4, MDLZ 53=12+34+6+1, MA 121=58+41+8+14) and confirmed the "round number" badge (`tradable-band-round-number`) appears only on MA's cell among the visible rows, never on rows with `band_round_number: false`.

### UT-04 — Legacy screen renders the honest absence copy
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-23-evidence/UT-04-legacy-scrolled.png`
- The ambient "latest" screen at test start, `screen-2026-07-20-ca185294a384` (`created_utc` 2026-07-29, i.e. recorded before this iteration's deploy), showed "composition not recorded in this snapshot" in every one of its 100 rows' `levels` cells, with no round-number badge anywhere.

### UT-05 — Pre-existing `/desk` columns are unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-23-evidence/UT-07-fail.png` + `UT-04-legacy-scrolled.png` (together span the full row)
- All nine pre-existing cells (symbol, side, class, distance, score, coverage, tick evidence, basis, history, band, opposite) render with unchanged content, format, and position on both the legacy and newly-populated screens.

### UT-06 — Symbol-cell tooltip is unchanged
**Verdict:** PASS
**Evidence:** DOM `title`-attribute read-out (see Notes)
- The drill-in anchor's `title` attribute contains distance/score/basis/history/band/bands-by-class/window-last-requested detail exactly as before this iteration — none of `band_member_count`, `band_round_number`, `band_member_timeframes`, `levels`, or "round number" appear.

---

## Failed Tests

### UT-07 — `levels` column discoverable without scrolling past the fold
**Verdict:** FAIL
**Failure:** At a 1440px-wide viewport (the test's own minimum), the ranked table requires horizontal scrolling to reach the `levels` column. The table's own rendered width is 1795px inside a `overflow-x: auto` container whose visible width is only 1214px (`main`'s max-width caps content well below the 1440px viewport). The `levels` header's right edge sits at x≈1901 — entirely outside the visible 1214px window. This condition already existed for the `opposite` column before this iteration (verbose cell content like `opposite resistance A 490.97–494.39 · 1.22 bps` already overflowed); `levels` simply inherits it as the new rightmost column.
**Evidence:** `reports/qa/goal-desk-iter-23-evidence/UT-07-fail.png`

**Steps taken:**
1. Set viewport to 1440×900, navigated to `http://localhost:3301/desk`.
2. Measured the ranked table's container: `parentWidth`/`clientWidth` = 1214px, `scrollWidth` = 1795px, `overflowX: auto`.
3. Measured the `levels` header cell's bounding rect: `left` ≈ 1658, `right` ≈ 1901 (both far past the 1214px visible edge).
4. Screenshotted the unscrolled state — table visibly cuts off after the `band` column; `opposite` and `levels` are both off-screen.

**Expected:** `levels` header + at least one cell visible without horizontal scroll at ≥1440px.
**Actual:** Requires horizontal scroll; not visible without scrolling. (P2/ux — does not gate the overall verdict per pass criteria; pre-existing condition inherited by the new column, not a regression this iteration introduced to a previously-fitting layout.)

---

## Skipped Tests

None.

---

## Additional Goal-Mode Regression Journeys

### UT-J-06 — MCP contract v3 — 17 read-only tools
**Verdict:** PASS
**Evidence:** code inspection (`apps/backend/app/mcp/__init__.py`) + live `curl` + `pytest`
- This journey has zero UI surface (confirmed in the phase's ui-surface-map: 0 frontend files touched for J-06 as of prior iterations). Verified instead via:
  - `app/mcp/__init__.py`: exactly 17 `name="..."` tool registrations (`tape_state, tape_features, tape_history, datasets, bars, levels, tradability, setups, backtests, strategies, edge_report, desk_universe, desk_screen, pnl_ledger, taxonomy, ui_route_map, get_endpoint`) — matches this session's own 17-tool `mcp__tapeology__*` roster exactly.
  - `_STATIC_PATHS` maps `desk_universe`→`/research/desk/universe`, `desk_screen`→`/research/desk/screen`; both endpoints return HTTP 200 with valid JSON when curled directly against the running backend (`localhost:8301`).
  - `get_endpoint`'s `ALLOWED_GET_PREFIXES = ("/tape/", "/research/", "/meta/")` reaches both new paths (both start with `/research/`).
  - `apps/backend/tests/test_mcp_server.py` (38 tests) and `apps/backend/tests/test_desk_screen.py` (78 tests) both pass 100% via the project's `.venv`.

### UT-J-09 — Every top-up run leaves an append-only record of what it attempted
**Verdict:** PASS (stale-golden false-negative repaired)
**Evidence:** `reports/qa/goal-desk-iter-23-evidence/UT-J-09-topup-runs.png` (+ crops)
- The replay lane flagged this journey as a possible regression. Root cause: the stored `J-09.json` golden asserted the honest-EMPTY state ("No top-up runs recorded yet."), which was true when the golden was recorded at iter-11 but is no longer true — a real top-up run (`topup-2026-07-29-5de907c83fc4`) has since landed on the ambient `apps/backend/.data/` store (state `done`, 404/404 pairs attempted, 0 reused · 390 fetched · 14 failed). The golden's OWN notes explicitly predicted this exact scenario and said to update the expected text rather than treat it as a regression.
- Re-executed live: navigated to `/desk`, confirmed the "Top-up Runs" section renders the real run in its table (date, run id, state, attempted/total, universe snapshot) and the "LATEST RUN" detail panel renders `state: done`, `404 of 404 pairs attempted`, `0 reused · 390 fetched · 14 failed`, and all 14 failed pairs with their verbatim vendor-error detail legible (e.g. "no data for AAPL 1h in the requested window 2024-07-29T00:00:00+00:00..2026-07-30T00:00:00+00:00 — Yahoo Finance serves 1h bars only for the last 730 days..."). No crash, no missing section, no stale/blank state.
- **Golden repaired:** `runs/goal-session-desk/journey-scripts/J-09.json` updated — step 2's expected text changed from `"No top-up runs recorded yet."` to `"404 of 404 pairs attempted"` (the current ambient store's real rendered value), with notes documenting the environmental-drift rationale. Linted clean (`demo_runner.py --mode lint`).

---

## Notes — headless screenshot rendering glitch (tooling, not product)

During UT-J-09 evidence capture, the Chrome MCP headless screenshot action reliably returned a
solid-color blank image whenever the page was vertically scrolled (`window.scrollY > 0`) at a
normal viewport height (900–4320px), regardless of viewport width, whether native `scroll` or
`window.scrollTo`/`scrollIntoView` was used, or whether sticky/fixed-position elements were
neutralized first. DOM-level checks (`elementFromPoint`, `getBoundingClientRect`, `textContent`)
consistently confirmed the correct content WAS present and laid out correctly at these scroll
positions — only the pixel screenshot capture was affected. Screenshots taken at `scrollY = 0`
were reliably correct at any viewport size. Workaround used: temporarily set
`document.body.style.zoom` low enough that the full page fit within the 4320px viewport-height cap
at `scrollY = 0`, screenshot, then crop/upscale the region of interest with PIL. This is recorded
here as a tooling limitation for future iterations' awareness, not a product defect — confirmed via
the DOM cross-checks and via `UT-03-populated-levels-badge.png`, which used the same workaround
successfully without needing any deep scroll.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, CDP port 9222)
- **Test Date:** 2026-07-30
- **Evidence directory:** `reports/qa/goal-desk-iter-23-evidence/`
- **Screen snapshots referenced:** `screen-2026-07-20-ca185294a384` (legacy, pre-iteration), `screen-2026-07-30-bad6387963ef` (newly computed this session, populated)
