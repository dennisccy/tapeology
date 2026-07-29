# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 22/22 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-08-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-09-verify.png |
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-10-verify.png |
| UT-J-11 | Every ranked briefing row states how much completed history its wall was measured over | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-11-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-12-verify.png |
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

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29


---

## Auditor addendum (2026-07-29, `docs/handoffs/goal-desk-iter-17-audit.md`)

1. **UT-J-11 / UT-J-12 were added by the audit lane, not by the iteration's own browser-QA run.**
   The phase spec's `Required-still-passing journeys:` line wraps onto a second physical line, and
   `replay_lane_spec_journeys` (`scripts/automation/lib/replay-lane.sh:70`) parses only `head -1`,
   so `J-11`/`J-12` were silently dropped from `REQUIRED_JOURNEYS` and reached neither lane — the
   file previously read "20/20 journeys passed" while two required journeys had no verifier. The
   auditor ran `demo_runner.py --mode verify --journeys J-11,J-12` against the same
   `http://localhost:3301` rig (rc 0, both PASS, evidence `J-11-verify.png`/`J-12-verify.png`,
   raw artifact `reports/phase-goal-desk-iter-17-regression-replay-results-audit.md`) and re-merged.
   Neither journey is regressed; the gap was in verification coverage, not in the product.
2. **UT-03 / UT-04 / UT-10's exact-string expectation is superseded.** Audit finding F1 changed the
   legacy-row `band` cell from `close not recorded in this snapshot` to
   `band <low>–<high> · close not recorded in this snapshot` (goal.md J-13 requires legacy rows to
   render "their OWN recorded band range plus the honest ... state"). Re-verified live in a real
   browser at `location.origin === "http://localhost:3301"`: all 63 rows now read e.g.
   `band 488.50–490.85 · close not recorded in this snapshot`, the band `<td>` still carries no
   per-cell `title`, and the composite tooltip carries the full-precision range. Evidence:
   `AUDIT-F1-legacy-band-range.png`, `AUDIT-F1-legacy-band-range-scrolled.png`. The J-13 golden
   asserts the fallback as a SUBSTRING, so it still replays PASS (re-run post-fix together with
   J-04/J-08/J-11/J-12: 5/5 PASS).
