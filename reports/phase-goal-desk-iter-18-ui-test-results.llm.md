# Phase goal-desk-iter-18 — UI Test Results

**Phase:** goal-desk-iter-18 (J-14 — every ranked row discloses the nearest wall on the OTHER side
of price)
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 11/11 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads, `opposite` header present as 11th column | smoke | P1 | 11 header cells ending in `opposite`, heading "Desk" visible, no error panel, no console errors | Headers read exactly `symbol, side, class, distance, score, coverage, tick evidence, basis, history, band, opposite`; only an informational React DevTools console message, no errors | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-01-result.png` |
| UT-02 | Legacy rows show honest fallback text | happy-path | P1 | `BRK-B`/`CRM`/`ISRG`/`CMCSA` and other rows' `opposite` cell reads exactly `opposite wall not recorded in this snapshot` | All 63 ranked rows on the live `screen-2026-07-28-ac07c9581a4f` snapshot (including the four named) read exactly that fallback string, verified via DOM eval over the whole table | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-02-result.png` |
| UT-03 | Populated near (≤25bps) + far (>1000bps) rows in one screenshot | happy-path | P1 | One row's `opposite` cell ≤25.00 bps, another's >1,000.00 bps, both legible together | On a fixture-scoped rig (backend :8395/frontend :3395, real Yahoo-fetched BRK-B/CRM/ISRG/CMCSA + fixture AAPL/MSFT bars) a freshly computed screen produced `CMCSA`/`CRM` at 0.00 bps and `AAPL` at 1208.73 bps, both legible in one full-page screenshot; page origin independently confirmed to be `http://localhost:3395` (the rig's own base URL) before treating the capture as evidence | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-03-result.png` |
| UT-04 | Legacy tooltip carries `bands by class not recorded` line | happy-path | P1 | `BRK-B` row's composite tooltip title includes `bands by class not recorded in this snapshot` immediately after the band/close segment, before coverage segments; no separate title on the opposite `<td>` | Anchor `title` attribute matched byte-for-byte, segment positioned as expected; `desk-row-opposite` cell's own `title` attribute is `null` | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-04-result.png` |
| UT-05 | Populated tooltip carries full-precision `bands_by_class` line | happy-path | P1 | Tooltip's last pre-coverage segment reads `bands by class A <n> · B <n> · C <n> · unclassified <n>`, counts sum to the symbol's total band count | Scoped-rig `MSFT` row tooltip read `bands by class A 0 · B 0 · C 10 · unclassified 0` (sum 10, matches `bands_by_class` total); `CMCSA` read `A 0 · B 0 · C 5 · unclassified 1` (sum 6, matches) | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-05-result.png` |
| UT-06 | Populated row with unclassified opposite band renders "unclassified" | happy-path | P2 | Cell reads `opposite <side> unclassified <low>–<high> · <n> bps`, never blank or literal `"null"` | `CMCSA` row read `opposite support unclassified 22.08–22.13 · 0.00 bps`; `CRM` row read `opposite support unclassified 151.78–151.78 · 0.00 bps` — both real members of the same scoped-rig screen | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-06-result.png` |
| UT-07 | Pre-existing columns unchanged; skip table unaffected | regression | P1 | `BRK-B`/`CRM`'s other cells unchanged from pre-iteration values; skip table header stays 4 columns, no `opposite`/`band` column | All 7 named `BRK-B`/`CRM` cell values matched exactly (side/class/distance/score/basis/history/band); skip table header read exactly `symbol, reason, coverage, tick evidence` | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-02-result.png` (row cell values captured in the same session; see notes) |
| UT-08 | Row drill-in + Screen History click-through still work | regression | P2 | Clicking `BRK-B` row navigates to `/structure?symbol=BRK-B&asof=...`; clicking a Screen History row swaps in place (no navigation), highlights via `data-selected`, renders 11-column table | Click navigated to `http://localhost:3301/structure?symbol=BRK-B&asof=2026-07-28T23%3A59%3A59Z`; clicking the `2026-06-22` history row kept URL at `/desk`, set `data-selected="true"` on that row only, table still had 11 headers and correct fallback opposite cell | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-08-result.png` |
| UT-09 | New column discoverable with zero extra clicks | ux | P2 | 1 click from home to `/desk`; `opposite` header/column visible after the same horizontal scroll every column past `coverage` already required | Navigated home → clicked "Desk" nav link → landed on `/desk` with heading "Desk"; `opposite` header text confirmed present after horizontal scroll, no extra control needed | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-09-result.png` |
| UT-10 | New copy carries no advice/prediction language | ux | P3 | None of the fallback/populated copy strings contain advice/imperative/prediction words | Re-checked all captured strings (`opposite wall not recorded in this snapshot`, `no band on the other side`, `bands by class not recorded in this snapshot`, the populated `opposite <side> <class> ...` / `bands by class A <n> · B <n> · C <n> · unclassified <n>` patterns) — none contain "buy/sell/watch/opportunity/should/recommend/target" or similar; agrees with `test_copy_discipline.py` (30 passed, unmodified, per dev handoff) | PASS | `reports/qa/goal-desk-iter-18-evidence/UT-10-result.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools (regression journey) | regression | P1 | MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` outputs byte-identical to curl equivalents; `get_endpoint` proxies `/research/desk/screen` verbatim; MCP suite green | `len(TOOL_NAMES)` = 17 (confirmed by direct import); in-process MCP tool calls (`TAPEOLOGY_API_BASE=http://localhost:8301`) for `desk_screen`, `desk_universe`, and `get_endpoint(/research/desk/screen)` diffed byte-identical against `curl http://localhost:8301/research/desk/{screen,universe}`; `pytest tests/test_mcp_server.py` — 38 passed, including `test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim` run in isolation | PASS | none (non-browser journey; verified via MCP tool calls + curl diff + pytest, see notes) |

---

## Passed Tests

### UT-01 — `/desk` loads, `opposite` header present as 11th column
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`; `document.querySelector('[data-testid="desk-screen-rows-table"]')` header cells read `["symbol","side","class","distance","score","coverage","tick evidence","basis","history","band","opposite"]` — exactly 11, `opposite` last. Console showed only an informational React DevTools message, no errors.

### UT-02 — Every currently-recorded ranked row shows the honest fallback
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-02-result.png`
- Batch DOM eval over all 63 `tbody tr` rows on the live `screen-2026-07-28-ac07c9581a4f` snapshot: every row's `[data-testid="desk-row-opposite"]` cell text is exactly `opposite wall not recorded in this snapshot`, including the four named symbols (`BRK-B`, `CRM`, `ISRG`, `CMCSA`) and every other visible row (spot-check requirement exceeded — all rows checked, not just 3).

### UT-03 — Populated near/far opposite rows in one screenshot
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-03-result.png`
- Set up a fixture-scoped backend on an isolated port (`:8395`), env-scoped to a fresh temp rig (`TAPEOLOGY_JOURNAL_DB`/`TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_BAR_INDEX_DB`/`TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR` all under `$TMPDIR/scoped-rig-desk18`, never `apps/backend/.data`), seeded with the committed 103-member fixture universe, the committed AAPL/MSFT daily bar fixtures, and four REAL keyless-Yahoo-fetched symbols (`BRK-B`, `CRM`, `ISRG`, `CMCSA`, 2026-01-01..2026-06-26 daily). Confirmed the target screen dir was empty before computing (no collision, iter-10 lesson). Triggered `POST /research/desk/screen/compute {"screen_date":"2026-06-22"}` — completed immediately (`state: done`, `reused: false`). A dedicated scoped frontend (a hardlink-copied `apps/frontend` tree at `$TMPDIR/scoped-frontend-desk18`, never touching the ambient `next dev` process — iter-17 lesson) was started on `:3395` with `NEXT_PUBLIC_API_URL=http://localhost:8395`.
- Before treating any capture as evidence, confirmed `window.location.origin === "http://localhost:3395"` (the rig's own base URL, iter-16 lesson) and that the rendered symbols (`MSFT, ISRG, AAPL, BRK-B, CMCSA, CRM`) matched the scoped backend's own computed screen, not the ambient one.
- `opposite` cells read: `MSFT` 487.04 bps, `ISRG` 986.28 bps, `AAPL` **1208.73 bps** (far, >1,000), `BRK-B` 27.17 bps, `CMCSA` **0.00 bps** (near, ≤25), `CRM` **0.00 bps** (near, ≤25) — a full-page screenshot shows all six rows' `opposite` cells simultaneously, legible.
- Backend and frontend processes for this scoped rig were cleanly killed after evidence capture; the ambient `:8301`/`:3301` pair was confirmed still healthy afterward.

### UT-04 — Legacy tooltip carries the `bands by class not recorded` line
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-04-result.png`
- `BRK-B` row anchor `title` attribute read exactly: `distance 0 bps · score 1787 · basis 2026-07-23T04:00:00.000000Z (5 d before as-of) · history 500 sessions from 2024-07-25T04:00:00.000000Z · band 488.5–490.8500061035156 · close not recorded in this snapshot · bands by class not recorded in this snapshot · 1h window last requested: 2026-07-25T00:00:00Z · 4h window last requested: 2026-07-25T00:00:00Z · 1d window last requested: 2026-07-25T00:00:00Z · 1w window last requested: 2026-07-25T00:00:00Z` — the new segment sits immediately after band/close and before coverage, matching source order. `desk-row-opposite` cell's own `title` attribute is `null` (F2 lesson honored — one composite anchor tooltip only).

### UT-05 — Populated tooltip carries the full-precision `bands_by_class` line
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-05-result.png`
- Scoped-rig `MSFT` row tooltip: `... band 378.91–379.40 · close 379.40 · bands by class A 0 · B 0 · C 10 · unclassified 0 · 1h window last requested: never · ...` (sum 10, matches its `bands_by_class` total confirmed independently via the compute output). `CMCSA` read `bands by class A 0 · B 0 · C 5 · unclassified 1` (sum 6, matches). Position confirmed identical to the fallback line's position in UT-04.

### UT-06 — Unclassified opposite band renders the literal word "unclassified"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-06-result.png`
- `CMCSA` row: `opposite support unclassified 22.08–22.13 · 0.00 bps`. `CRM` row: `opposite support unclassified 151.78–151.78 · 0.00 bps`. Both real rows of the same scoped-rig screen used for UT-03; both bands genuinely exist on the other side (non-null price range) but carry `band_class: null` server-side — a distinct, correctly-rendered state from the "no band on the other side" case.

### UT-07 — Pre-existing columns unchanged; skip table unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-02-result.png`
- `BRK-B`: `side=support`, `class="Class A" + "nearest same-class band"` caption, `distance=0.00 bps`, `score=1787.00`, `basis="basis 2026-07-23 · 5 d before as-of"`, `history="history 500 sessions · from 2024-07-25"`, `band="band 488.50–490.85 · close not recorded in this snapshot"` — all byte-identical to the pre-iteration shape.
- `CRM`: same basis/history; `score=63.00`; `band="band 156.25–156.93 · close not recorded in this snapshot"`.
- Skip table (`Skipped — no bars`) header read exactly `symbol, reason, coverage, tick evidence` — 4 columns, no `opposite` or `band` column, correct per spec (skipped members were never ranked).

### UT-08 — Row drill-in and Screen History click-through still work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-08-result.png`
- Clicking the `BRK-B` row navigated to `http://localhost:3301/structure?symbol=BRK-B&asof=2026-07-28T23%3A59%3A59Z` (confirmed via `window.location.href`).
- Back on `/desk`, clicking the `2026-06-22` Screen History row kept the URL at `/desk` (no navigation), set `data-selected="true"` on exactly that row (all others `false`), and the ranked table re-rendered with 11 headers and the correct legacy `opposite` fallback for that older snapshot too.

### UT-09 — New column discoverable with zero extra clicks
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-09-result.png`
- From `http://localhost:3301`, clicked the "Desk" nav link (`data-testid="nav-link"`) — landed on `/desk` (1 click), heading "Desk" visible. After the same horizontal scroll every column past `coverage` already required (pre-existing behavior), the `opposite` header cell text read exactly `"opposite"` — plain, lower-case, consistent with existing headers.

### UT-10 — New copy carries no advice/prediction language
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-18-evidence/UT-10-result.png`
- Reviewed all captured fallback strings (`opposite wall not recorded in this snapshot`, `no band on the other side` per plan.md's own contract text, `bands by class not recorded in this snapshot`) and populated patterns (`opposite <side> <class> <low>–<high> · <n> bps`, `bands by class A <n> · B <n> · C <n> · unclassified <n>`) actually rendered on-page this run — none contain "buy/sell/watch/opportunity/should/recommend/target" or similar advice/imperative/prediction language. Consistent with `test_copy_discipline.py` passing unmodified (per dev handoff, 30 passed).

### UT-J-06 — MCP contract v3 — 17 read-only tools (regression journey)
**Verdict:** PASS
**Evidence:** none (non-browser MCP/backend journey — see notes below)
- This session's configured `mcp__tapeology__*` tools point at `http://localhost:8000` by default (`TAPEOLOGY_API_BASE` unset), which has no service running in this pipeline (the ambient backend for this iteration is `:8301`) — both `mcp__tapeology__desk_screen` and `mcp__tapeology__desk_universe` correctly and honestly errored (`ConnectError... no cached or fabricated data is served`) rather than serving anything fabricated. This is expected/correct MCP behavior, not a product defect, and does not indicate a J-06 regression.
- To verify J-06's actual acceptance, ran the MCP tool functions in-process with `TAPEOLOGY_API_BASE=http://localhost:8301` (the real running ambient backend) via `app.mcp.call_tool`, and diffed the results against direct `curl http://localhost:8301/research/desk/{screen,universe}`:
  - `desk_screen` tool output — **byte-identical** to `curl .../research/desk/screen` (`json.tool`-normalized diff: no output).
  - `desk_universe` tool output — **byte-identical** to `curl .../research/desk/universe`.
  - `get_endpoint(/research/desk/screen)` output — **byte-identical** to `curl .../research/desk/screen`.
  - `len(app.mcp.TOOL_NAMES)` == **17** (confirmed by direct import: `backtests, bars, datasets, desk_screen, desk_universe, edge_report, get_endpoint, levels, pnl_ledger, setups, strategies, tape_features, tape_history, tape_state, taxonomy, tradability, ui_route_map`).
  - `cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -v` — **38 passed**, 0 failed, including `test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim` (re-run in isolation, 1 passed) which proves the two new J-14 fields flow through the MCP proxy byte-identically on populated fixture data.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden Replay Scripts

- `runs/goal-session-desk/journey-scripts/J-14.json` written (lints clean via `demo_runner.py --mode lint`). Pinned to the permanent legacy screen `screen-2026-06-22-3ecd45c062c7` (the era's earliest recorded screen, forever a legacy row under the append-only rail) for future-proof stability — mirrors the J-13 precedent exactly, since the scoped-rig populated evidence (UT-03/05/06) used a one-off temp rig that will not exist at future replay time.
- No golden script was written for J-06: it is a non-browser MCP/backend contract journey (tool count + byte-identity + pytest suite) with no dedicated UI surface to drive with `goto`/`click`/`fill` — best-effort per the agent instructions, so it is skipped and falls back to the LLM/manual verification lane next time.

---

## Environment

- **Frontend URL:** http://localhost:3301 (ambient); http://localhost:3395 (fixture-scoped rig, torn down after UT-03/05/06 evidence capture)
- **Backend URL:** http://localhost:8301 (ambient); http://localhost:8395 (fixture-scoped rig, torn down after evidence capture)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-29
- **Evidence directory:** `reports/qa/goal-desk-iter-18-evidence/`
