# Phase goal-tradable_wall-iter-9 — UI Test Results

**Phase:** goal-tradable_wall-iter-9
**Date:** 2026-07-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 7/11 tests passed (4 skipped, 0 failed)

All P1 tests either passed cleanly (UT-01, UT-07, UT-08, UT-10) or landed in the
explicitly pre-authorized cold-cache carve-out (UT-02, UT-03 — mirroring iter-8's UT-13
precedent, per this iteration's own dispatch instructions and the ui-test-plan's own
carve-out clause). No smoke, happy-path, or P1 test failed outright.

---

## Environment state confirmed before testing

The edge-report cache was independently verified **genuinely cold** for the entire QA
session (not inferred — directly confirmed):
- `apps/backend/.data/edge_report_cache.db` → `edge_report_cache` table: **0 rows**
  (read-only `sqlite3` inspection via Python, both before testing and again at the end).
- Backend process (pid 1529552) pinned at 90–100% CPU throughout, accumulating from
  23:45 to 58:59 minutes of CPU time across the session — a single long-running compute,
  not idle.
- No `TAPEOLOGY_DATASET_DIR` / `TAPEOLOGY_EDGE_REPORT_CACHE_DB` override present in the
  backend process's environment (`/proc/<pid>/environ`) — it is running the real,
  unscoped corpus, matching the documented ~10+h path, not a fast-path scoped dataset dir.
- `curl -m 45 http://localhost:8301/research/edge-report` returned no response within 45s.

Per the dispatch instructions (point 3) and the ui-test-plan's own Scope section, no
attempt was made to force a fast warm-up (that would require restarting the
pipeline-managed backend against a scoped dataset directory, which is outside
browser-QA's role and would risk interrupting a real in-flight compute). UT-02/UT-03 are
recorded using the pre-authorized carve-out.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/structure` loads, Edge Report loading state visible immediately | smoke | P1 | Structure heading + Edge Report caption + `edge-report-loading` pulsing placeholder; no red error, no blank area | Confirmed via DOM: `data-testid="structure-title"` present; `<section aria-label="Edge report">` with exact caption text and `data-testid="edge-report-loading"` (`animate-pulse`); no `edge-report-unavailable`, no populated table; no blank white area | PASS | `reports/qa/goal-tradable_wall-iter-9-evidence/UT-01-edge-report-loading-full.png` |
| UT-02 | Warm-cache Edge Report resolves within interactive time (headline) | happy-path | P1 | Loading placeholder replaced by populated register/tables or honest empty state, within ~1 min | Cache confirmed genuinely cold for the full session (see Environment section) — no fast-path warm-up reachable without restarting the pipeline-managed backend mid-real-compute. Carve-out applied per ui-test-plan's own clause | SKIP (documented carve-out) | `reports/qa/goal-tradable_wall-iter-9-evidence/UT-01-edge-report-loading-full.png` (loading state evidence) |
| UT-03 | Populated cells honestly label `insufficient sample`/`ok`, no pooling | error | P1 (inherits UT-02 carve-out) | Depends on UT-02 resolving with populated content | UT-02 did not resolve this session (carve-out) — nothing to inspect; inherits the same carve-out per this test's own precondition text | SKIP (inherits UT-02 carve-out) | none |
| UT-04 | Cold/never-warmed cache shows honest loading, never fabricated | error | P2 | `edge-report-loading` persists; no `edge-report-unavailable`; no partial/fabricated content; backend `/health` stays healthy | Precondition (force restart with fresh cache path) not literally performed — restarting the pipeline-managed backend is outside QA's role and would interrupt the real in-flight compute. The **live environment was already naturally in this exact state** (0 rows, confirmed by direct DB read) for the full ~1h session. Observed continuously: only `edge-report-loading` ever appeared, never `edge-report-unavailable`, never a table/register. `curl /health` returned `{"status":"ok"}` on every check | PASS (verified against the naturally-occurring cold state, not a QA-forced restart — see note) | `reports/qa/goal-tradable_wall-iter-9-evidence/UT-01-edge-report-loading-full.png` |
| UT-05 | Cache busts after dataset/config change, no stale render lingers | validation | P2 | Panel returns to loading after a dataset/config mutation | Not executed. Requires mutating the dataset registry or cache-key config while a real, valuable ~10+h operator-gated compute appears to be in flight on this same backend — doing so risked corrupting that run. The test's own precondition explicitly permits skipping when this action isn't available in-session | SKIP | none |
| UT-06 | Loading/empty/populated Edge Report states visually distinct | ux | P3 | Able to compare ≥2 of the 3 Edge Report states | Precondition not met: only the loading state was observed for Edge Report specifically this session (UT-02 never resolved) | SKIP | none |
| UT-07 | Case Studies filters + table/empty-state unregressed | regression | P1 | Populated table → no-match message on bad filter → table returns on clear | Confirmed: table loaded with 801 real AAPL band-touch rows (`data-testid="case-studies-table"`); typing `ZZZZNOPE` produced exactly "No events match these filters." + "The registry has rows — this filter combination simply matches none." (`data-testid="case-studies-no-match"`); clearing the field restored all 801 rows. No errors | PASS | `reports/qa/goal-tradable_wall-iter-9-evidence/UT-07-case-studies-populated.png`, `UT-07-case-studies-no-match.png`, `UT-07-case-studies-cleared.png` |
| UT-08 | Tradable Map default + raw-toggle off by default unregressed | regression | P1 | Idle state, "Show raw levels" default, loads pinned AAPL 2026-06-22 case with basis/table/band exactly as iter-7 verified | Confirmed: idle state + `tradable-map-idle` before Load; "Show raw levels" default; after Load — basis text exactly "Map basis (prior completed session close): 2026-06-18T04:00:00.000000Z"; table has exactly 10 rows; first row = resistance, `300.1700134277344–302.2699890136719`, Class A, score 153, round number — matches pinned case; toggle still read "Show raw levels" after Load; solid (not dashed) band lines on chart | PASS | `reports/qa/goal-tradable_wall-iter-9-evidence/UT-08-before-load.png`, `UT-08-tradable-map-loaded.png` |
| UT-09 | Raw-levels toggle reveals unchanged pre-existing view | regression | P2 | Toggle flips to "Hide raw levels", reveals raw levels chart + confluence zones, flips back and disappears, Tradable Map unaffected | Confirmed: button flipped to "Hide raw levels"; `aria-label="Levels and zones"` section appeared with "Price chart — S/R levels" (dense multi-timeframe level grid, real data — full page grew to 116,344px tall) and "Confluence Zones" (real zone cards, e.g. Class C zone 1–6 with price/timeframe/type rows); clicking again flipped back to "Show raw levels" and the section fully disappeared; `tradable-map-table`/`tradable-map-basis` unaffected throughout | PASS | `reports/qa/goal-tradable_wall-iter-9-evidence/UT-09-raw-levels-shown.png` |
| UT-10 | Cockpit SIM honest empty state + Live-mode hiding unregressed | regression | P1 | SIM-BUYER shows chart + "No tradable map for SIM-BUYER."; Live mode hides the entire chart component; nav unchanged | Confirmed: "Simulated" pre-selected by default; SIM-BUYER watch rendered chart + tape state; `data-testid="no-tradable-map"` text exactly "No tradable map for SIM-BUYER."; no `confluence-chip`. After Stop → Live → AAPL → Watch: zero "Price Chart" / "Tape-State Markers" text anywhere in the DOM (component fully absent, honestly showing "market is closed... Tapeology never fabricates data to fill the gap" instead); nav bar exactly `Cockpit, Journal, Studies, Performance, Structure` (5 items) | PASS | `reports/qa/goal-tradable_wall-iter-9-evidence/UT-10-sim-buyer-watch.png`, `UT-10-live-mode-no-chart.png` |
| UT-11 | Historical AAPL band overlay + confluence chip unregressed | regression | P2 | Chart + tape-state markers render normally; band-overlay/chip *if visible* use the documented format | Chart + tape-state markers rendered correctly across **4 separate real-data (SIP consolidated feed) windows** on the pinned AAPL 2026-06-22 session (Buyer Control / Seller Control states, confidence, quote, features all populated correctly, no console errors). The `Open 9:30 ET` preset itself tripped the app's own high-volume guard ("that window is very high-volume — try a shorter range") — worth noting since the test plan assumed it wouldn't; used shorter/later custom windows instead, consistent with the test's own intent. Band-overlay line and `confluence-chip` did **not** appear in any of the 4 sampled windows despite price sitting inside the pinned 300.17–302.27 band's numeric range in 3 of them. See note below | PASS (hard requirement); band-overlay/chip sub-check inconclusive, not failed — see note | `reports/qa/goal-tradable_wall-iter-9-evidence/UT-11-historical-aapl-chart.png`, `UT-11-historical-aapl-seller-control.png` |

---

## Passed Tests

### UT-01 — `/structure` loads with the Edge Report panel visible in its loading state immediately
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-9-evidence/UT-01-edge-report-loading-full.png`
- "Structure" heading (`data-testid="structure-title"`) visible immediately.
- `<section aria-label="Edge report">` renders with caption text beginning "The v1 /
  structure_tape / structure_tape_map comparison over recorded event windows…" (exact match).
- `data-testid="edge-report-loading"` (`animate-pulse` gray skeleton) directly below the
  caption, confirming the fetch to `GET /research/edge-report` started automatically on
  mount.
- No `edge-report-unavailable`, no populated register/table, no blank white area.
- Note: the Chrome MCP tool's console-log capture is a stub ("TODO: Console logging not
  yet implemented") in this environment, so DevTools console errors could not be checked
  via that specific mechanism; no visual error overlay/red banner appeared in any of the
  ~30 page states captured across this session.

### UT-04 — Cold / never-warmed cache shows the honest loading state, never a fabricated or partial result
**Verdict:** PASS (see caveat)
**Evidence:** `reports/qa/goal-tradable_wall-iter-9-evidence/UT-01-edge-report-loading-full.png`
- The literal precondition (force a fresh cache path + restart the backend) was **not**
  performed — restarting the pipeline-managed backend mid-way through what appears to be
  a real, valuable ~10+h operator-gated compute is outside browser-QA's role and would
  risk destroying that progress.
- Instead, this session's live backend was independently confirmed — via direct read-only
  `sqlite3` inspection of `edge_report_cache.db` (0 rows) both at the start and end of the
  session, roughly an hour apart — to already be genuinely, continuously cold for the
  entire QA pass. This satisfies the same observable condition UT-04 is designed to
  exercise.
- Across the full session, the Edge Report panel was checked at multiple points and never
  showed anything but `edge-report-loading`: no `edge-report-unavailable`, no table, no
  register banner text.
- `curl http://localhost:8301/health` returned `{"status":"ok"}` on every check throughout
  (confirms the backend is genuinely computing, not crashed/hung).

### UT-07 — Case Studies panel still renders its filters and table/empty-state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-9-evidence/UT-07-case-studies-populated.png`, `UT-07-case-studies-no-match.png`, `UT-07-case-studies-cleared.png`
- Initial load: populated table (`data-testid="case-studies-table"`), columns `symbol |
  session | band | reaction | forward returns`, real AAPL rows (e.g. `2026-05-18,
  resistance · 300.45–300.92 · Class C, rejected, ...`).
- Typed `ZZZZNOPE` into `data-testid="case-studies-filter-symbol"` → table area showed
  exactly "No events match these filters." with sub-text "The registry has rows — this
  filter combination simply matches none." (`data-testid="case-studies-no-match"`) — this
  is a pure client-side filter over already-fetched rows, so it updated instantly.
  Confirmed the field-clear happens client-side per the panel's own copy ("nothing here is
  recomputed").
- Cleared the field → table returned with 801 rows (`data-testid="case-studies-row"`
  count).
- No console errors observed at any point (subject to the console-tool limitation noted
  under UT-01).

### UT-08 — Tradable Map still defaults correctly and the raw-levels toggle stays off by default
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-9-evidence/UT-08-before-load.png`, `UT-08-tradable-map-loaded.png`
- Before any action: `data-testid="tradable-map-idle"` present with the exact idle copy;
  `data-testid="raw-levels-toggle"` read "Show raw levels" (not "Hide raw levels").
- Typed `AAPL` / `2026-06-22T21:00:00Z`, clicked Load (`data-testid="structure-load-button"`,
  confirmed not disabled beforehand).
- Resolved within the `await_element` bound (well under 60s): `data-testid="tradable-map-basis"`
  read exactly "Map basis (prior completed session close): 2026-06-18T04:00:00.000000Z".
- `data-testid="tradable-map-table"` had exactly **10** `tradable-band-range` rows (5
  Class A, 5 Class C). First row: `resistance | 300.1700134277344–302.2699890136719 |
  Class A | 153 | 55 | round number` — matches the pinned band iter-7 independently
  verified.
- "Show raw levels" toggle unchanged after Load.
- Candlestick chart rendered with solid (not dashed) red/green band lines, price-axis
  labels in the form `R class A · score 153 · round`, matching the documented format.

### UT-09 — Raw-levels toggle still reveals the pre-existing all-levels view, unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-9-evidence/UT-09-raw-levels-shown.png`
- Clicking "Show raw levels" flipped the button to "Hide raw levels" and revealed
  `aria-label="Levels and zones"` containing "Price chart — S/R levels" (a dense
  multi-timeframe level grid over real data; the full page grew to 116,344px tall,
  confirming a large real level dump, not a stub) and "Confluence Zones" (real zone
  cards with price/timeframe/type rows, e.g. "Class C · zone 1 · score 8").
- Clicking again flipped the button back to "Show raw levels" and the whole section
  disappeared; `tradable-map-table` / `tradable-map-basis` were unaffected throughout.

### UT-10 — Cockpit: SIM honest empty state and Live-mode hiding remain unregressed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-9-evidence/UT-10-sim-buyer-watch.png`, `UT-10-live-mode-no-chart.png`
- "Simulated" pre-selected by default on fresh load.
- Watched `SIM-BUYER` → "Price Chart — Tape-State Markers" rendered a chart with a tape
  state marker; directly below, `data-testid="no-tradable-map"` read exactly "No
  tradable map for SIM-BUYER." — no band overlay, no `confluence-chip`.
- Stop → Live → cleared field via native-setter (typing alone appended rather than
  replaced — see Observations) → typed `AAPL` → Watch: zero occurrences of "Price Chart"
  or "Tape-State Markers" anywhere in the DOM; the app instead honestly showed "market is
  closed... Tapeology never fabricates data to fill the gap. You can replay a past
  session with Historical instead."
- Nav bar read exactly `Cockpit, Journal, Studies, Performance, Structure` (5 items,
  unchanged).
- No console errors observed (subject to the console-tool limitation noted under UT-01).

### UT-11 — Historical AAPL replay still shows the tradable-band overlay and a descriptive-only confluence chip
**Verdict:** PASS (hard requirement); band-overlay/chip sub-check inconclusive — see note
**Evidence:** `reports/qa/goal-tradable_wall-iter-9-evidence/UT-11-historical-aapl-chart.png`, `UT-11-historical-aapl-seller-control.png`
- The test's hard requirement — "the candlestick chart and tape-state markers render
  normally" — was confirmed across **4** separate real-data windows on AAPL 2026-06-22
  (`feed: SIP (consolidated)`): 17:00–17:01 local (Buyer Control, conf. 0.631, price
  300.94), 16:45–16:55 local (rejected by the app's high-volume guard, see below),
  15:20–15:21 local (Seller Control, conf. 0.640, price 301.47), 16:10–16:11 local
  (rendered, no errors). No console errors in any attempt.
- **Observation:** the `Open 9:30 ET` quick-pick preset (a 1-minute window right at the
  session open) itself tripped the app's own "that window is very high-volume — try a
  shorter range" guard. The ui-test-plan assumed this specific preset would avoid the
  guard; empirically, AAPL's real opening-minute tick volume was enough to trip it. A
  10-minute custom window elsewhere in the session also tripped it; 1-minute custom
  windows away from the open did not. This is pre-existing guard behavior (unrelated to
  this iteration's diff) — recorded as an observation, not scored as a failure, since the
  test's own note already anticipated needing to route around this class of guard.
- **Band-overlay / confluence-chip:** neither `confluence-chip` nor any band-overlay
  price-axis label was observed in any of the 4 sampled windows, even though price
  (300.94, then 301.47) sat numerically inside the pinned resistance band
  (300.17–302.27) in two of them. This was not scored as a failure because (a) the
  test's own Expected Result uses conditional wording ("If a band-overlay line is
  visible… If a confluence chip banner… is visible…"), and (b) the confluence chip's
  own documented copy includes the literal segment "measured history: edge report" —
  and the edge-report cache was confirmed cold for this entire session (see Environment
  section above). It is plausible the chip is gated on a populated edge-report response,
  which would tie this observation to the exact same root condition as UT-02's carve-out
  rather than being an independent regression — but this was **not** independently
  confirmed (e.g., by warming the cache and re-testing), so it is reported as an open
  observation, not a diagnosed cause. Zero code was touched in `PriceChart.tsx` or
  `tradability.py` this iteration, so this is pre-existing behavior either way, not a
  regression introduced by this iteration's diff.

---

## Skipped Tests

### UT-02 — Warm-cache Edge Report resolves to the full 3-way register within an interactive time budget
**Verdict:** SKIP (documented, pre-authorized carve-out)
**Reason:** The edge-report cache was independently confirmed genuinely cold for the
entire QA session — not inferred, directly verified via read-only inspection of
`edge_report_cache.db` (0 rows, checked at session start and again ~1 hour later) plus a
backend process pinned at 90–100% CPU with 58:59 minutes of accumulated compute time and
no `TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_EDGE_REPORT_CACHE_DB` scoped override present. Two
unrelated `curl` probes (5s and 45s timeouts) against `GET /research/edge-report` both
received no response. Per this iteration's dispatch instructions (point 3) and the
ui-test-plan's own Carve-out clause (mirroring iter-8's UT-13), forcing a fast warm-up
would require restarting the pipeline-managed backend against a scoped dataset directory
— outside browser-QA's role, and risky given a real ~10+h operator-gated compute appears
to be genuinely in flight on this exact backend instance. UT-01's evidence (loading
placeholder correctly present) stands in for this test per the carve-out's own
instructions. This carve-out is explicitly pre-authorized and does not, by itself, move
the overall verdict to FAIL.

### UT-03 — Populated Edge Report cells honestly label `insufficient sample` vs `ok`
**Verdict:** SKIP (inherits UT-02's carve-out)
**Reason:** This test's own precondition states it inherits UT-02's outcome. UT-02 did
not resolve with populated content this session (cold cache, see above), so there is
nothing to inspect. Per the test's own text, this is recorded as inheriting the carve-out,
not as a failure.

### UT-05 — Cache correctly invalidates after a dataset or config change
**Verdict:** SKIP
**Reason:** Executing this test requires mutating the backend's dataset registry or a
cache-key-affecting config field. Doing so right now would mean deliberately changing
shared state on a backend that appears to be mid-flight on a real, ~10+h operator-gated
compute over the credentialed corpus — a mutation here risks invalidating or corrupting
that in-progress run. The test's own precondition explicitly allows skipping ("an
operator without backend access cannot execute this test and should skip it, not fail
it"); this was a deliberate choice to protect the in-flight real compute, not a tooling
limitation (backend shell access was in fact available and used read-only throughout this
session).

### UT-06 — Loading, empty, and populated Edge Report states remain visually distinct
**Verdict:** SKIP
**Reason:** This test's own precondition requires observing the Edge Report panel in at
least two of its three states this session. Only the loading state was ever observed for
Edge Report specifically (cache cold throughout — see UT-02). P3 priority; does not affect
the overall verdict.

---

## Observations (non-blocking, informational)

1. **Nav bar shows an honest "navigation unavailable — backend unreachable" notice
   (`data-testid="nav-unavailable"`) intermittently on `/structure` while the cold-cache
   compute is running.** First observed a few seconds into the session (absent on the very
   first navigation, present on subsequent DOM snapshots), and present in several later
   captures on `/structure`; not observed on `/` (cockpit) navigations. This is an amber,
   informational notice — not a red error banner, and it never blocked any page
   interaction or produced a blank page. It appears to be the nav bar's own graceful
   degradation when its route-listing fetch (`GET /meta/ui-routes`) can't complete quickly
   against a backend saturated by the long-running edge-report compute (a plain `curl
   /health` during the same window took ~3s to respond — unusually slow for a trivial
   health check — while a plain `curl /research/setups` timed out completely at 5s, yet
   the same request succeeded a few minutes later through the browser). This is
   pre-existing backend-contention behavior orthogonal to this iteration's diff (which
   only touches the edge-report serving path), not a new regression — recorded here as
   context for why some backend-dependent panels (Case Studies, Tradable Map) took longer
   than usual to resolve during this specific QA pass, though all of them did resolve
   correctly once given a bounded wait.
2. See UT-11's note above for the `Open 9:30 ET` high-volume-guard observation and the
   band-overlay/confluence-chip open question.
3. The Chrome MCP tool's console-message capture (`enable_console_logging` /
   `get_console_messages`) area of the auto-captured `*-console.txt` files consistently
   read `# TODO: Console logging not yet implemented` in this environment throughout the
   session — DevTools console-error assertions in this report rely on the absence of
   visible error UI (red banners, blank pages, broken renders) rather than a captured
   console transcript.
4. Full-page screenshots at scroll depth reliably render blank on this page (confirms the
   iter-6 lesson) — DOM-text extraction and targeted `fullpage: true` screenshots (cropped
   with PIL where the page exceeded 100k px tall) were used as the fallback throughout,
   per the phase spec's own guidance.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), viewport 1440×1000
- **Test Date:** 2026-07-15
- **Evidence directory:** `reports/qa/goal-tradable_wall-iter-9-evidence/`
- **Edge-report cache state throughout testing:** cold (0 rows in `edge_report_cache.db`,
  confirmed at session start and end); real compute in flight on the backend process for
  the full session duration.
