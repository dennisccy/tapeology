# Phase goal-desk-iter-17 — UI Test Results

**Phase:** goal-desk-iter-17 (J-13 — every ranked row discloses the price its wall sits at)
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 11/11 tests passed (0 skipped). Plus 1/1 regression journey (J-06) passed via backend evidence.

All 8 P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-07, UT-J-06) PASS. UT-08/UT-09/UT-10 (P2/P3) PASS.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads, `band` header present | smoke | P1 | "Desk" heading visible, no error panel, ranked table's last header cell reads exactly `band`, no console errors | Navigated to `/desk`; "Desk" heading present; ranked table (`data-testid="desk-screen-rows-table"`) rendered; `document.querySelectorAll('th')` confirmed last cell text `band`; `get_console_messages` after a fresh navigate showed only the standard React DevTools info line, zero errors | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-01-result.png` |
| UT-02 | Header shows exactly 10 columns in order | smoke | P1 | Exactly 10 `<th>` cells: `symbol, side, class, distance, score, coverage, tick evidence, basis, history, band`, `band` last | `eval()` over the table's `th` elements returned exactly `["symbol","side","class","distance","score","coverage","tick evidence","basis","history","band"]`, length 10 | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-02-result.png` |
| UT-03 | Legacy rows show honest fallback text | happy-path | P1 | `BRK-B`/`LIN` `band` cells read exactly `close not recorded in this snapshot`; every other visible row also shows this fallback (spot-check ≥3 more) | `eval()` dumped all 63 ranked rows' `[data-testid="desk-row-band"]` text: every single one (including `BRK-B`, `LIN`, `DHR`, `HD`, `IBM`, ...) read exactly `close not recorded in this snapshot` — 0 exceptions | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-03-result.png` |
| UT-04 | Tooltip carries band/close segment after history | happy-path | P1 | Composite `title` attribute on the row's stretched drill-in anchor includes a close/band segment immediately after `history` and before the coverage segments; band `<td>` itself has no separate `title` | Read `tr[data-symbol="BRK-B"] a`'s `title` via `eval()`: exact string `"distance 0 bps · score 1787 · basis 2026-07-23T04:00:00.000000Z (5 d before as-of) · history 500 sessions from 2024-07-25T04:00:00.000000Z · close not recorded in this snapshot · 1h window last requested: ... · 4h ... · 1d ... · 1w ..."` — matches the plan's exact expected string; `[data-testid="desk-row-band"]`'s own `title` attribute confirmed `null` | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-04-result.png` |
| UT-05 | Populated in-band + out-of-band rows in one screenshot | happy-path | P1 | On a scoped rig, an in-band row's `band` cell reads `band <low>–<high> · close <val>` with `<val>` inside/at an edge of the range, and an out-of-band row's cell shows the same pattern with `<val>` outside the range — both legible together in one screenshot | Stood up a fixture-scoped rig (backend `:8392` / frontend `:3392`) with `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_BAR_INDEX_DB`/`TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR`/`TAPEOLOGY_DATASET_DIR` all pointed at a fresh temp copy of the real bar/universe stores (never `apps/backend/.data`; isolation independently verified via `/proc/<pid>/environ`); target screen store confirmed empty before compute (no collision, iter-10 lesson). Computed a NEW screen for `screen_date=2026-07-28` via `POST /research/desk/screen/compute`; all 63 rows came back carrying `reference_close` (9 in-band, 54 out-of-band). Navigated the real browser to the scoped frontend, confirmed `location.origin === "http://localhost:3392"` (iter-16 lesson) before treating the page as evidence: `BRK-B` (`distance 0.00 bps`) → `"band 488.50–490.85 · close 490.85"` (at the high edge, inside range); `LIN` (`distance 0.20 bps`) → `"band 506.33–509.61 · close 506.32"` (below the low edge, outside range). Both legible together in one screenshot | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-05-result.png` |
| UT-06 | Pre-existing columns unchanged for `BRK-B`/`LIN` | regression | P1 | `BRK-B`: side=support, class=Class A (nearest same-class band), distance=0.00 bps, score=1787.00, basis/history text unchanged; `LIN`: side=resistance, distance=0.20 bps, score=273.00, same basis/history; both rows' 4 coverage badges lit, no tick-evidence badge | `eval()` read all six pre-existing cells for both rows on the ambient store: values matched exactly (BRK-B support/Class A/0.00 bps/1787.00/basis 2026-07-23 · 5 d before as-of/history 500 sessions · from 2024-07-25; LIN resistance/Class A/0.20 bps/273.00/same basis+history); `data-has-bars="true"` on all 4 timeframe badges for both rows; no tick-evidence badge present for either | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-06-result.png` |
| UT-07 | Row drill-in + Screen History click-through still work | regression | P2 | Clicking the `BRK-B` row navigates to `/structure?symbol=BRK-B&asof=...`; clicking a Screen History row swaps the displayed snapshot in place (no navigation), highlights it, and its 10-column table (including `band`) renders correctly | Clicked `tr[data-symbol="BRK-B"]`: `location.href` became `http://localhost:3301/structure?symbol=BRK-B&asof=2026-07-28T23%3A59%3A59Z`, `<h1>` read "Structure", symbol field pre-filled `BRK-B` (screenshot). Navigated back to `/desk`, clicked the `screen-2026-06-22-3ecd45c062c7` Screen History row: `location.href` stayed `/desk` (in-place swap), that row's `data-selected="true"`, ranked table re-rendered with the same 10-column header ending in `band`, and its first row's band cell correctly showed the legacy fallback too | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-07-result.png` |
| UT-08 | Skip table intentionally has no `band` column | ux | P2 | Skip table header reads exactly `symbol, reason, coverage, tick evidence` (4 columns), no `band` column, not rendered as broken/missing | `eval()` over all `<table>` elements found the skip table (no `data-testid`) with exactly 4 `<th>` cells: `["symbol","reason","coverage","tick evidence"]` — confirmed via full-page screenshot showing "SKIPPED — NO BARS (38)" section rendering cleanly with 4 columns | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-08-result.png` |
| UT-09 | New copy carries no advice/prediction language | ux | P3 | Neither the fallback string nor the populated pattern contains "buy"/"sell"/"watch"/"opportunity"/"should"/"recommend"/"target" or similar | Programmatic scan of all 63 rendered `band` cell strings (post-navigate, fresh load) plus the UT-05 populated strings against the banned-word list: 0 matches found in either state | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-09-result.png` |
| UT-10 | Documented gap: no populated example on live store today | ux | P3 | No row anywhere on the live ambient store shows numeric band values; every row shows the exact fallback text (not blank/`undefined`/`NaN`) | `eval()` over all 63 ranked rows' `band` cells on the live ambient store: `nonFallbackCount: 0` — every single row reads exactly `"close not recorded in this snapshot"`, confirming this is an honest, complete, expected gap (independently proven populated via UT-05's scoped rig) | PASS | `reports/qa/goal-desk-iter-17-evidence/UT-10-result.png` |
| UT-J-06 | J-06 — MCP contract v3: 17 read-only tools (regression journey, goal.md) | regression | P1 | MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` byte-identical to their curl equivalents; `get_endpoint` proxies `/research/desk/screen` verbatim; MCP suite green | Journey is explicitly "Keyless; automated" in goal.md with no browser-observable acceptance surface (MCP protocol only). Ran `apps/backend/.venv/bin/python -m pytest tests/test_mcp_server.py -v`: **37 passed, 0 failed**, including the `EXPECTED_TOOLS` 17-tuple equality assertion (`tape_state, tape_features, tape_history, datasets, bars, levels, tradability, setups, backtests, strategies, edge_report, desk_universe, desk_screen, pnl_ledger, taxonomy, ui_route_map, get_endpoint`) and the byte-identity/honest-error clauses for every tool, including `desk_screen`. Separately confirmed live via `curl` against `:8301` that `GET /research/desk/screen` serves the real ambient `latest` snapshot (`screen-2026-07-28-ac07c9581a4f`, 63 rows) — the same response shape the `desk_screen` MCP tool proxies. (The configured `mcp__tapeology__desk_screen` tool call in this environment defaults to `localhost:8000`, not this dispatch's `:8301` rig, so live cross-tool invocation wasn't directly comparable here — the backend's own `test_mcp_server.py` is the authoritative byte-identity proof per J-06's acceptance text, matching the iter-16 precedent for this same journey.) | PASS | none (backend-automated; see Actual column) |

---

## Passed Tests

### UT-01 — `/desk` loads, `band` header present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-01-result.png`
- "Desk" heading visible; ranked table's rightmost header cell reads exactly `band`; console clean (only a React DevTools info line) on a fresh navigate.

### UT-02 — Header shows exactly 10 columns in order
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-02-result.png`
- `document.querySelectorAll('th')` over the ranked table returned exactly `symbol, side, class, distance, score, coverage, tick evidence, basis, history, band`, in that order, `band` last.

### UT-03 — Every currently-recorded ranked row shows the honest fallback
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-03-result.png`
- All 63 ranked rows (not just the 5 spot-checked) read exactly `close not recorded in this snapshot` in their `band` cell — `BRK-B` and `LIN` both confirmed among them.

### UT-04 — Composite tooltip carries the band/close segment
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-04-result.png`
- `BRK-B`'s drill-in anchor `title` attribute matched the plan's exact expected string byte-for-byte, with the close/band segment positioned immediately after `history` and before the coverage segments; the `band` `<td>` itself carries no separate `title`.

### UT-05 — Populated in-band + out-of-band rows, one screenshot
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-05-result.png`
- Fixture-scoped rig (backend `:8392`, isolated `TAPEOLOGY_*` dirs copied from the real ambient bar/universe stores, never touching `apps/backend/.data`) computed a genuinely NEW screen for `2026-07-28`. `BRK-B` came back in-band (`band 488.50–490.85 · close 490.85`) and `LIN` out-of-band (`band 506.33–509.61 · close 506.32`), both legible together in one screenshot on the scoped frontend (`:3392`, origin independently verified).

### UT-06 — Pre-existing columns unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-06-result.png`
- All six pre-existing cells for `BRK-B` and `LIN` (side, class, distance, score, basis, history) plus coverage/tick-evidence match their known values exactly; the `band` column is a pure append.

### UT-07 — Row drill-in + Screen History click-through
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-07-result.png`
- `BRK-B` row click navigated to `/structure?symbol=BRK-B&asof=2026-07-28T23%3A59%3A59Z`; Screen History row click swapped the displayed snapshot in place (no navigation) with the new 10-column table rendering correctly for that older snapshot too.

### UT-08 — Skip table has no `band` column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-08-result.png`
- Skip table header reads exactly `symbol, reason, coverage, tick evidence` (4 columns) — correctly absent, not broken.

### UT-09 — New copy carries no advice/prediction language
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-09-result.png`
- Programmatic scan of both the fallback and populated copy strings found zero banned words.

### UT-10 — Documented gap confirmed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-17-evidence/UT-10-result.png`
- 0 of 63 rows on the live ambient store show a populated band value — an honest, complete, expected gap (not a defect), independently proven populated via UT-05.

### UT-J-06 — MCP contract v3: 17 read-only tools (regression journey from docs/goal.md)
**Verdict:** PASS
**Evidence:** none (backend-automated evidence — see Actual column in Results Table)
- `pytest tests/test_mcp_server.py -v` → 37 passed, 0 failed, confirming the 17-tool `EXPECTED_TOOLS` contract and every tool's byte-identity/honest-error clauses (including `desk_screen`/`desk_universe`). Live curl cross-check against `:8301` confirmed `GET /research/desk/screen` serves the real ambient snapshot the MCP tool proxies.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Incident During This Run (fully remediated, no impact on recorded verdicts)

While setting up UT-05's fixture-scoped rig, a **second `next dev -p 3392` process was started from the same `apps/frontend` source directory** as the ambient frontend (`:3301`). Both `next dev` dev-server processes share the same `apps/frontend/.next` build-cache directory on disk — starting the second process caused Next.js to recompile shared chunks, and the AMBIENT frontend (`:3301`) began serving JS bundled with the SCOPED backend's `NEXT_PUBLIC_API_URL` (`:8392`) baked in. This was caught immediately (a `BRK-B` row on `:3301` unexpectedly showed populated `reference_close` values that did not match a direct `curl` to the ambient `:8301` backend, which correctly still showed 0/63 populated rows).

**Verified no data was affected:** the ambient backend (`:8301`) and its on-disk `apps/backend/.data/screen/screen-2026-07-28-ac07c9581a4f.json` file were never written to by any action in this dispatch (only `GET`s and one `POST` to the separate scoped `:8392` process) — file mtime and content confirmed unchanged throughout.

**Remediation:** stopped the scoped frontend process, SIGTERM'd the ambient frontend process tree, cleared the poisoned `apps/frontend/.next` directory, and restarted the ambient frontend fresh with its correct `NEXT_PUBLIC_API_URL=http://localhost:8301`. Re-verified via `eval()` that `:3301` correctly resumed serving the honest fallback text for `BRK-B`/`LIN` before continuing with UT-06 onward. **UT-01 through UT-04's evidence was captured BEFORE this incident began** (verified clean); **UT-05's evidence is from the correctly-isolated scoped origin** (`:3392`, independently origin-checked, unaffected by the ambient-side symptom); **UT-06 through UT-10 were captured AFTER remediation was confirmed** (re-verified 0/63 populated on the ambient store). No recorded PASS in this report rests on contaminated evidence.

**Lesson for downstream lanes (demo-narrator or any future scoped-rig work on this project):** never run a second `next dev` from `apps/frontend` while the ambient one is running — they share `.next` and will cross-contaminate which backend the ambient page serves from. If a scoped frontend is needed, either (a) reuse this run's evidence instead of re-deriving it, (b) stop the ambient frontend first and restart it afterward (as done here), or (c) copy the whole `apps/frontend` source tree to an isolated directory before running `next dev` there.

---

## Golden Replay Scripts

- `runs/goal-session-desk/journey-scripts/J-13.json` written after J-13's underlying UI behavior (UT-01/02/03/04/06/07 header+fallback+tooltip+regression behavior) verified PASS. Pinned to the PERMANENT legacy state (`screen-2026-06-22-3ecd45c062c7`, the era's earliest recorded screen, guaranteed stable forever under the append-only rail) rather than the one-off scoped-rig populated state, since that scoped rig's data will not exist at future replay time. Read-only (the click only drives `GET /research/desk/screen?id=`, never a write path); lints clean via `demo_runner.py --mode lint`.
- No golden written for J-06 (UT-J-06): goal.md marks J-06 explicitly "Keyless; automated" with no browser-observable acceptance surface — best-effort skip per the golden-script policy, matching the iter-16 precedent for this same journey (which also had no golden).

---

## Environment

- **Frontend URL:** http://localhost:3301 (ambient rig; confirmed healthy and correctly isolated at the end of this run — see Incident note above)
- **Backend URL:** http://localhost:8301 (ambient rig, real `apps/backend/.data` store, never written to by this dispatch)
- **Scoped rig (UT-05 evidence):** backend `:8392` left running (harmless, isolated Python process, no shared build cache) for the downstream demo-narrator lane to reuse if useful — screen `screen-2026-07-28-ac07c9581a4f` with `reference_close` populated on all 63 rows is available at `GET http://localhost:8392/research/desk/screen`. Scoped data root: `/home/dennis-chan/.cache/iad/iad.goal-desk-iter-17.3302867/desk-iter17-scoped-qa`. The scoped frontend (`:3392`) was stopped and NOT left running (see Incident note — do not start a second `next dev` from `apps/frontend` alongside the ambient one).
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (CDP `:9222`, single dedicated tab, origin-checked before every evidence capture per the iter-16 lesson)
- **Test Date:** 2026-07-29
- **Evidence directory:** `reports/qa/goal-desk-iter-17-evidence/`
