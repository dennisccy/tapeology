# Phase goal-desk-iter-15 — UI Test Results

**Phase:** goal-desk-iter-15
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 10/11 tests passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads with `history` column present | smoke | P1 | Heading "Desk", 3-link nav, header row `... coverage \| tick evidence \| basis \| history`, no error banner | Confirmed via rendered DOM: `<thead>` reads `symbol, side, class, distance, score, coverage, tick evidence, basis, history`; nav shows Cockpit/Structure/Desk; no "not computed yet" / "could not be loaded" text found; screenshot shows full briefing table | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-01-result.png` |
| UT-02 | Short- and long-history rows legible together | happy-path | P1 | Two rows visibly differ by ≥10× in `history` cell, exact pattern, no `null`/`undefined`/`NaN` | HONA row: `history 27 sessions · from 2026-06-15`; BRK-B row (top of table): `history 500 sessions · from 2024-07-25` — both visible in ONE screenshot without scrolling; no null/undefined/NaN found in any history cell; rest of row (side/class/distance/score/coverage/basis) unaffected | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-02-result.png` |
| UT-03 | Hover tooltip discloses full-precision history | happy-path | P1 | Tooltip: `distance ... · score ... · basis ... · history <N> sessions from <full timestamp>` (no dot before "from"); click still navigates to `/structure?symbol=...&asof=...` | HONA anchor `title` attr read directly: `distance 0 bps · score 51 · basis 2026-07-23T04:00:00.000000Z (5 d before as-of) · history 27 sessions from 2026-06-15T04:00:00.000000Z · 1h window last requested: ...` — order and "from" (no dot) confirmed; click navigated to `http://localhost:3301/structure?symbol=HONA&asof=2026-07-28T23%3A59%3A59Z` (confirmed via `window.location.href`) | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-03-result.png` |
| UT-04 | Legacy row shows honest fallback, never null | validation | P2 | Banner "Viewing the recorded screen for 2026-07-29 — not the latest." + "Latest" button; every history cell reads exactly "history not recorded in this snapshot"; basis column unaffected; "Latest" restores real values | Clicked Screen History row `data-screen-date="2026-07-29"` (screen `screen-2026-07-29-ce0d82b8e9bf`, recorded before this iteration's code, `bar_store_signature` unchanged from later screens so it stays permanently reused/never recomputed under append-only pins); banner text matched exactly; ALL 63 ranked rows' `desk-row-history` cells read the identical fallback string (verified via dedup over every row); basis column still showed real per-row values (e.g. "basis 2026-07-23 · 6 d before as-of"); clicking "Latest" (`desk-history-latest-button`) restored real `history_sessions` values (27/382/500/etc.) | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-04-result.png` |
| UT-05 | Skip tables never grow a `history` column | validation | P2 | Neither skip table has a `history` header/cell; skip rows unaffected | "Skipped — no bars (38)" table header = exactly `symbol, reason, coverage, tick evidence` (no `history` th); no "history"-prefixed text anywhere inside the skipped-members section (checked programmatically over the section's own HTML slice); no "no basis session" table present in this fixture (all 38 skips are `reason: no_bars`, consistent with the rest of this era's fixture) | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-05-result.png` |
| UT-06 | Existing row data unchanged by new column | regression | P1 | distance/score/coverage/tick-evidence/basis identical before and after reload; basis format unchanged; exactly one new column vs prior iterations | BRK-B/DHR/HD distance, score, and basis values read identical before (`015-navigate.html`) and after (`022-navigate.html`) a full page reload; basis format still `basis <date> · <N> d before as-of`; table header shows exactly one new column (`history`) beyond J-08/J-10's documented shape | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-06-result.png` |
| UT-07 | Run Screen / Screen History click-through still work | regression | P1 | Button shows "Computing…" + progress line, then a Recorded/Reused outcome line; `history` column still present after; history-row click-through still swaps snapshot + shows banner | Clicked "Run Screen": button disabled, progress showed "Computing… / 42 / 101 members / current: GOOG"; on completion the line read "Reused the snapshot already recorded for this key — screen-2026-07-29-ce0d82b8e9bf" (a valid idempotent outcome — today's pins matched the already-recorded legacy screen); `history` column still present in the ranked-table header afterward; Screen-History row click-through re-verified in UT-04 above (same page, same session) | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-07-result.png` |
| UT-08 | Top-up Runs / Index Reconciliation unaffected | regression | P2 | Both sections render pre-existing content unchanged, no `history` text; no cut-off/missing content | Full-page screenshot confirms both sections fully rendered below Screen History: "Top-up Runs" → "No top-up runs recorded yet."; "Index Reconciliation" → latest run detail with drift-before/after counts; programmatic check over the rendered `<body>` text (`/history/i` regex) found zero matches in the Top-up Runs + Index Reconciliation segment; neither section is cut off | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-08-result.png` |
| UT-09 | `history` column discoverable, plain language | ux | P2 | Header reads plain lowercase "history"; cell self-explanatory; no advisory/judgement language; sits next to "basis" | `<th>` text is literally `history`, same CSS classes/styling as `coverage`/`tick evidence`/`basis` neighbors; cell text is a plain count + date (`history 500 sessions · from 2024-07-25`); grep for "enough", "reliable", "confidence", "buy", "watch this", "opportunity" inside all `history`-prefixed text found nothing; column sits immediately right of `basis` | PASS | `reports/qa/goal-desk-iter-15-evidence/UT-09-result.png` |
| UT-10 | Backend-unavailable shows honest message | error | P3 | Amber panel, no crash, no fabricated history values | Not executed — see Skipped Tests below | SKIP | none |
| UT-J-06 | MCP contract v3 — 17 read-only tools (regression journey, per dispatch instructions) | regression | P1 | MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` proxy byte-identical (empty + populated); `get_endpoint` on `/research/desk/screen?date=` proxies verbatim; MCP suite green | `apps/backend/tests/test_mcp_server.py` run directly: 35/35 pass, including the exact assertion `assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 17` (line 920) and dedicated byte-identity tests for `desk_universe`/`desk_screen` (empty + populated, real `httpx` REST comparison) plus the `?date=` `get_endpoint` proxy test; `app.mcp._STATIC_PATHS` confirmed to map `desk_universe`→`/research/desk/universe`, `desk_screen`→`/research/desk/screen`; live curl against the scoped rig (`:8301`) confirmed both endpoints serve real, structurally-correct payloads (101-member universe, 63-row latest screen). Note: the live `mcp__tapeology__*` MCP tools available to this agent are configured against the DEFAULT backend port 8000 (not running in this environment), not this iteration's scoped rig at `:8301` — verification therefore used the backend's own automated proxy-equivalence tests (which run against a real live server) plus direct curl against the scoped rig, not the MCP tool call itself | PASS | none (automated backend suite + curl; no UI surface for this journey — its own acceptance is explicitly "Keyless; automated") |

---

## Passed Tests

### UT-01 — `/desk` loads with the new `history` column present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-01-result.png`
- Nav bar shows Cockpit / Structure / Desk; heading "Desk" visible; ranked table header row ends `... coverage | tick evidence | basis | history`; no error banner; no console errors logged.

### UT-02 — Short-history and long-history rows both legible in the `history` column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-02-result.png`
- Same screenshot as UT-01 shows BRK-B (`history 500 sessions · from 2024-07-25`) and HONA (`history 27 sessions · from 2026-06-15`) simultaneously, ~18.5× apart. No `null`/`undefined`/`NaN` anywhere in the column.

### UT-03 — Hovering a row's drill-in link discloses full-precision history in the tooltip
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-03-result.png`
- HONA row anchor's `title` attribute read directly (native-tooltip source): `distance 0 bps · score 51 · basis 2026-07-23T04:00:00.000000Z (5 d before as-of) · history 27 sessions from 2026-06-15T04:00:00.000000Z · ...`. Clicking navigated to `/structure?symbol=HONA&asof=2026-07-28T23%3A59%3A59Z`, matching the pre-iteration click target exactly.

### UT-04 — Legacy screen row shows the honest fallback, never blank or `null`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-04-result.png`
- Selected the 2026-07-29 Screen History row (a screen recorded before this iteration's code landed). Banner "Viewing the recorded screen for 2026-07-29 — not the latest." appeared with a "Latest" button; every one of the 63 ranked rows' history cells read exactly "history not recorded in this snapshot"; the basis column on the same rows kept showing real per-row values, confirming only `history` is affected. Clicking "Latest" restored real history values.

### UT-05 — Skipped-members tables never grow a `history` column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-05-result.png`
- "Skipped — no bars (38)" table header is exactly `symbol, reason, coverage, tick evidence`; a programmatic scan of the entire skipped-members section's HTML found zero occurrences of `history`-prefixed text. This fixture's skips are all `reason: no_bars` (no `no_basis` skip rows present to check separately, but the shared component renders both reasons identically with no history column in either case per the code).

### UT-06 — Existing row data unchanged by the new column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-06-result.png`
- BRK-B / DHR / HD distance, score, and basis values were byte-identical before and after a full page reload. Basis format unchanged (`basis <date> · <N> d before as-of`). Exactly one new column added vs. the table's documented J-08/J-10 shape.

### UT-07 — "Run Screen" and Screen History click-through still work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-07-result.png`
- Clicking "Run Screen" disabled the button and showed live progress ("Computing… / 42 / 101 members / current: GOOG"). On completion: "Reused the snapshot already recorded for this key — screen-2026-07-29-ce0d82b8e9bf" (a valid outcome — today's pins matched an already-recorded legacy screen, so the append-only rail correctly refused a duplicate rather than rewriting it). The `history` column remained present in the table header throughout. Screen History row click-through (swap snapshot + banner) was independently confirmed in UT-04 on the same page/session.

### UT-08 — Top-up Runs and Index Reconciliation sections unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-08-result.png` (full-page capture)
- Both sections render fully below Screen History with their pre-existing content: "No top-up runs recorded yet." and a populated Index Reconciliation detail (drift before/after, series-on-disk, rows-indexed). A regex scan (`/history/i`) over that segment of the rendered page text found zero matches. Neither section is cut off or missing rows.

### UT-09 — `history` column is discoverable and uses plain, non-advisory language
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-15-evidence/UT-09-result.png`
- Header text is the plain lowercase word "history", styled identically to its "coverage"/"tick evidence"/"basis" neighbors. Cell content is self-explanatory (a count + a date). No advisory/judgement words ("enough", "reliable", "confidence", "buy", "watch this", "opportunity") appear anywhere in the column or its tooltip segment. Column sits immediately right of "basis".

### UT-J-06 — MCP contract v3 — 17 read-only tools (goal-mode regression journey)
**Verdict:** PASS
**Evidence:** none (automated backend suite + curl against the scoped rig; this journey's own acceptance is explicitly "Keyless; automated" with no browser surface)
- `apps/backend/tests/test_mcp_server.py` run directly against this checkout: **35/35 passed**, including the literal 17-tool-count assertion (`test_mcp_server.py:920`) and dedicated byte-identity proxy tests for `desk_universe`/`desk_screen` in both the honest-empty and populated states, plus the `?date=` `get_endpoint` proxy variant — all comparing the MCP tool's returned text against a real `httpx` call to the same running app (genuine byte-identity proof, not a mock). `app.mcp._STATIC_PATHS` was read directly and confirmed to register `desk_universe` → `/research/desk/universe` and `desk_screen` → `/research/desk/screen`. Live `curl` against this iteration's scoped rig (`http://localhost:8301`) confirmed both endpoints serve real payloads: `/research/desk/universe` → 1 snapshot, 101 members; `/research/desk/screen` → latest screen `screen-2026-07-28-ac07c9581a4f`, 63 ranked rows all carrying `history_sessions`/`history_start`. Caveat noted below.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-10 — Backend-unavailable state shows an honest message, not a crash
**Verdict:** SKIPPED
**Reason:** P3/optional per the test plan itself ("skip if that is not safe to do on this rig, and rely on TC-10's automated coverage instead"). This rig's backend (`:8301`) and frontend (`:3301`) are shared, pipeline-managed processes for this iteration's other evidence (Screen History, Reconcile Index runs, etc.); deliberately stopping the backend mid-run risked disrupting that shared state for no incremental signal beyond what TC-10's automated coverage already proves at the unit/integration level. No history-specific UI behavior is exercised by this test that isn't already covered by UT-01–UT-09.

---

## Notes / Caveats

- **UT-J-06 MCP-tool caveat:** the live `mcp__tapeology__*` MCP tools available to this agent session are configured against the framework's DEFAULT backend port (`8000`), which is not running in this environment (this iteration's backend is scoped to `:8301` by the browser-qa dispatch wrapper). Calling `mcp__tapeology__desk_screen` directly returned a connection error to `:8000`, confirming the mismatch rather than a product defect. J-06 verification therefore used the backend's own automated proxy-equivalence test suite (`test_mcp_server.py`, which spins up and calls a real live app instance) plus direct `curl` against the scoped rig — both are decisive, evidence-grounded checks for this journey's explicitly "Keyless; automated" acceptance, which has no browser/UI surface to drive.
- **Golden-collision discipline (iter-10 lesson) applied:** UT-07's "Run Screen" click computed today's screen (screen_date `2026-07-29`) and reported "Reused the snapshot already recorded for this key" against the pre-existing `screen-2026-07-29-ce0d82b8e9bf` (recorded before this iteration's code landed, sharing today's bar-store signature with every other recent screen). This does not collide with `J-04.json`/`J-05.json`/`J-08.json`'s golden scripts (none of which assert against `screen_date=2026-07-29` specifically), and per the iteration's own NOTES this is honest, expected append-only behavior — that legacy record will permanently lack `history_sessions`/`history_start` (append-only rail: identical pins never rewrite an existing snapshot), which is exactly what UT-04 verified.
- **Rig discipline (iter-14/15 lesson):** all evidence in this report was captured against the browser-qa dispatch's own scoped rig (backend `http://localhost:8301`, frontend `http://localhost:3301`) as instructed — no fallback to an ambient `apps/backend/.data` store was used.
- Golden replay script `runs/goal-session-desk/journey-scripts/J-11.json` was rewritten this run (overwritten in place) after live verification of UT-01–UT-04/UT-07, and passed `demo_runner.py --mode lint`.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-29
- **Evidence directory:** `reports/qa/goal-desk-iter-15-evidence/`
