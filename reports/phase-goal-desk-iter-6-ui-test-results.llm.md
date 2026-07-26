# Phase goal-desk-iter-6 — UI Test Results

**Phase:** goal-desk-iter-6
**Date:** 2026-07-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 15/15 tests passed (0 skipped) — all 12 UT-XX test-plan cases plus the 3 requested
goal-mode regression journeys (J-01, J-02, J-03). J-04 and J-07 were re-verified via deterministic
golden replay (not by this agent, per dispatch instructions) and are not re-tested here.

---

## Fixture-scoped data basis (cited by every claim below)

Per the phase spec's persistence-discipline note (iter-4/iter-5 lesson, carried forward), this
whole pass ran against a **fixture-scoped** FastAPI instance on port 8301, never the operator's
real ambient `apps/backend/.data/`:

- **Root:** `/var/tmp/iad.goal-desk-iter-6.822370/desk-iter6-fixture-qa/` — fresh temp root created
  by this agent (env vars `TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_BAR_DIR`,
  `TAPEOLOGY_DESK_SCREEN_DIR`, `TAPEOLOGY_DATASET_DIR`, `TAPEOLOGY_BAR_INDEX_DB`,
  `TAPEOLOGY_DATASET_INDEX_DB`, `TAPEOLOGY_JOURNAL_DB`, all under that root — the
  `qa_desk_iter5_fixture_scoped_backend.sh` pattern, extended with a seeded screen dir).
- **Screen fixtures:** verbatim byte-identical copies of the two REAL, already-recorded snapshots
  `apps/backend/.data/screen/screen-2026-06-22-3ecd45c062c7.json` and
  `screen-2026-07-25-e184a7dc2f86.json` (confirmed via `diff` before use).
- **Bar fixtures:** verbatim copies of all 84 real AAPL bar records (every timeframe/window this
  store held for AAPL) from `apps/backend/.data/bars/`, plus a rebuilt `bar_index.db` via
  `BarIndex.reindex()` over the seeded dir.
- **Universe fixture (for the J-01/J-02 regression checks only):** the committed
  `apps/backend/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json` (103 members),
  added mid-pass after UT-01–UT-12 (which need no universe data) so J-01/J-02's live acceptance
  clauses could be exercised against a genuinely populated snapshot.
- **Frontend:** `http://localhost:3301`, already pointed at `NEXT_PUBLIC_API_URL=http://localhost:8301`
  by the harness — no frontend change needed to hit the fixture-scoped backend.
- **Teardown:** confirmed via file listing + checksums that the operator's real
  `apps/backend/.data/` was byte-for-byte unchanged throughout (2 screen files, same mtimes; 355
  bar files, same count; 1 universe file, same mtime) — see TC-10 note below. The fixture-scoped
  backend was killed and a fresh, unscoped (ambient) backend restarted on :8301 at the end of this
  pass, confirmed serving the real `universe-2026-07-25-49b33fa31680` snapshot again.

**Disclosure (iter-5's capture-aids lesson):** for UT-11 only, the full-page screenshot capability
of this session's browser tool caps at 4320px height while `/desk`'s populated page is ~4662px
tall, cutting off the "Run Screen / Top-up" panel at the bottom. To capture it visually, the
Briefing and Skipped Members `<section>` elements were temporarily set to `display:none` via a
page-context `eval` (a pure client-side visual toggle, no data/state change) immediately before
that one screenshot, then the page was reloaded fresh before continuing. The pass/fail
determination for UT-11 was made from live DOM/HTML inspection (button presence + absence of a
`disabled` attribute), not from the screenshot.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, Desk heading + 4 panels visible, no console errors | Rendered correctly; "Desk" heading, Provenance/Briefing/Skipped Members/Screen History all visible; only the standard React DevTools info line in console | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-01-result.png` |
| UT-02 | `/structure` loads without errors, no params | smoke | P1 | Structure heading, Symbol/As-of empty, no console errors | Confirmed via live HTML: both inputs `value=""`, Load button disabled, `tradable-map-idle` shown, no errors | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-02-result.png` |
| UT-03 | Click history row renders exact snapshot | happy-path | P1 | Viewing banner + selected row + AAPL row (Class A, 0.34 bps, 298.02–300.1001) + Skipped(91)/ABBV; exactly one new GET, zero POST | All matched exactly; `data-selected="true"` on the clicked row; `performance` resource timing showed exactly one new request, `GET .../screen?date=2026-06-22`, no POST | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-03-result.png` |
| UT-04 | "Latest" reverts to newest screen | happy-path | P1 | Banner gone, latest rows restored, no row selected, zero new requests | Confirmed: banner gone, original 2026-07-25 rows byte-identical to pre-UT-03 state, both history rows `data-selected="false"`, `performance.getEntriesByType('resource')` empty after clearing | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-04-result.png` |
| UT-05 | Briefing row drills into `/structure` with prefill+auto-load | happy-path | P1 | URL `?symbol=AAPL&asof=2026-06-22T23:59:59Z`; fields prefilled; map already populated; band row `298.02–300.1001` | `location.href` matched exactly (URL-escaped colon); Symbol input `value="AAPL"`, As-of input `value="2026-06-22T23:59:59Z"`; `tradable-map-table` present without any Load click; bands list contains `resistance 298.02–300.1001 Class A 97 1610 round number` | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-05-result.png` |
| UT-06 | Skipped row also drills into `/structure` | happy-path | P1 | URL `?symbol=ABBV&asof=...`; honest no-bar-series empty state, no crash | Navigated to exactly that URL; Symbol="ABBV", As-of="2026-06-22T23:59:59Z"; `tradable-map-no-bar-series` shown ("No bar series recorded for ABBV."); no console errors, no blank page | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-06-result.png` |
| UT-07 | History click, no matching screen, UI unchanged | error | P2 | Briefing unchanged, amber note shown, no crash | Exercised the real `handleSelectHistoryScreen` code path end-to-end by intercepting `window.fetch` for the `date=2026-06-22` URL to return `{"screen": null}` (the real backend's own honest-no-match shape) and clicking that real row; Briefing's first row stayed TSLA (pre-click state, unchanged); exact text "No recorded screen matches 2026-06-22 — still showing the previously displayed screen." appeared; no console error | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-07-result.png` |
| UT-08 | `/structure?symbol=AAPL`, asof omitted — no partial prefill | validation | P2 | Both fields empty, idle state, after ≥2s wait | Live post-hydration check (after 2.5s): `{"symbol":"","asof":"","idle":true}` | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-08-result.png` |
| UT-09 | `/structure?asof=...`, symbol omitted — no partial prefill | validation | P2 | Both fields empty, idle state | Live check after 2.5s: `{"symbol":"","asof":"","idle":true}` | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-09-result.png` |
| UT-10 | Manual Load flow still works | regression | P1 | Load produces populated bands table (or honest empty), no crash/stuck | Typed AAPL + `2026-06-22T23:59:59Z`, clicked Load; `tradable-map-table` appeared with the same band set as UT-05 (chart + bands list); no console errors | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-10-result.png` |
| UT-11 | Run Screen / Top-up controls still render | regression | P2 | Both buttons visible + enabled; neither clicked | Confirmed via live HTML: `desk-run-screen-button` and `desk-topup-button` both present, no `disabled` attribute, labels unchanged ("Run Screen" / "Top-up"); neither was clicked | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-11-result.png` (see capture-aid disclosure above) |
| UT-12 | History/drill-in rows discoverable via hover | ux | P2 | Pointer cursor + background highlight on hover, both tables | History row: `getComputedStyle().cursor === "pointer"`, `el.matches(':hover') === true`, background changed to the hover class's color; Briefing row: covering `<a>` (stretched-link) shows `cursor: pointer` on hover, row background changed identically | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-12-result.png` |
| UT-J-01 | J-01 — Universe ingestion, honest states | regression (goal-mode) | P1 | Empty state before any snapshot; after registering a fixture, checksum + 90–110-bounded member count + normalized symbols (e.g. `BRK.B`→`BRK-B`), sorted | `GET /research/desk/universe` on the still-empty fixture root returned `{"snapshots":[],"latest":null,"integrity_errors":[]}`; after seeding the committed `universe-2026-07-25-817cc184bbb3.json` fixture (103 members, within 90–110), the GET listed it verbatim: checksum `817cc184bbb3`, `member_count: 103`, `source_url` = the documented Wikipedia S&P 100 URL, members alphabetically sorted, `BRK-B` present (no `BRK.B`) | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-J-01-empty-state.png`, `UT-J-01-populated.png` |
| UT-J-02 | J-02 — Coverage + top-up timeframe pin, truth table | regression (goal-mode) | P1 | Honest empty state before any universe snapshot; pinned timeframe set = exactly `1h/4h/1d/1w` (no 5m/1m); coverage truth-table reports bars-present only for the members the store actually holds | Before seeding: `GET /research/desk/coverage` returned `{"universe_snapshot_id":null,"timeframes":["1h","4h","1d","1w"],"members":[]}`. After seeding the universe fixture (same 103 members, only AAPL's bars present in this fixture root): the GET returned exactly 103 member entries, timeframe set unchanged (`1h/4h/1d/1w`, no 5m/1m), and exactly ONE symbol (`AAPL`) showed `has_bars:true` on any timeframe — the other 102 members (e.g. `ABBV`, `ABT`, `ACN`, `ADBE`, `AIG`, ...) all showed `has_bars:false` on every timeframe, a clean truth-table match to which bars this fixture root actually holds | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-J-02-empty-state.png`, `UT-J-02-populated.png` |
| UT-J-03 | J-03 — The screen: pinned inputs, rank order, byte-identical read | regression (goal-mode) | P1 | `GET /research/desk/screen?date=` serves the exact persisted snapshot verbatim; rows ranked band-class then distance asc; a row's band values match `GET /research/tradability` byte-for-byte for the same symbol/as-of | Fully exercised via UT-01/UT-03/UT-05 above: the `2026-06-22` snapshot read back AAPL's exact recorded fields (`band_class A`, `distance_bps 0.33523150389608725`, `price_low 298.02`, `price_high 300.1001`); the 10 displayed rows were monotonically non-decreasing in `distance_bps` (0.00, 0.00, 0.30, 0.31, 0.73, 1.62, 78.37, 95.54, 144.94, 148.08) — all Class A in this sample, matching the class-then-distance rank rule; AAPL's screen-row band (298.02–300.1001, class A, score 97.0) matched `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T23:59:59Z`'s own band list entry byte-for-byte (same price_low/price_high/class, `quality_score: 97.0` = `band_score: 97.0`). The compute-trigger idempotency clause ("same-pins re-run → honest already-recorded response") was intentionally NOT exercised live — POSTing to the compute endpoint is a write action explicitly out of scope for this browser pass (already unit-test-covered, confirmed green in the dev handoff / QA report) | PASS | `reports/qa/goal-desk-iter-6-evidence/UT-J-03-screen-verbatim.png` (plus UT-03/UT-05 evidence above) |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-01-result.png`
- Navigated to `/desk`; "Desk" heading (`data-testid="desk-title"` region) and all four panels
  (Provenance, Briefing, Skipped Members, Screen History) rendered; console showed only the
  standard React DevTools info line, no errors.

### UT-02 — `/structure` loads without errors, no params
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-02-result.png`
- Live HTML confirmed both the Symbol input and `structure-as-of-input` have `value=""` (the
  visible placeholder text is a `placeholder=` attribute, not a filled value); Load button has
  `disabled=""`; `tradable-map-idle` shown; no console errors.

### UT-03 — Click a Screen History row renders that exact snapshot
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-03-result.png`
- Clicked the `2026-06-22` history row; the "Viewing the recorded screen for 2026-06-22 — not the
  latest." banner appeared with a "Latest" button; the clicked row's `data-selected` flipped to
  `"true"`; Briefing's first row showed AAPL / resistance / Class A / 0.34 bps / score 97.00;
  Skipped Members showed "Skipped — no bars (91)" with ABBV first; `performance` resource timing
  showed exactly one new request (`GET /research/desk/screen?date=2026-06-22`) and no POST.
- Note: the FIRST screenshot taken immediately after the click still showed the pre-click (latest)
  data — a benign timing race between the auto-capture and the async fetch resolving, not a defect.
  A second screenshot taken after `await_element` on the viewing-banner testid showed the correct
  post-fetch state, which is what is recorded here.

### UT-04 — "Latest" control reverts to the newest screen
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-04-result.png`
- Clicked "Latest"; banner disappeared; Briefing table reverted to the original 2026-07-25 rows,
  byte-identical to the pre-UT-03 state (TSLA 0.00bps/217.00 first, etc.); neither history row
  showed `data-selected="true"`; `performance.getEntriesByType('resource')` was empty after being
  cleared immediately before the click, confirming zero new network requests.

### UT-05 — Click a Briefing row drills into `/structure` with prefill and auto-load
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-05-result.png`
- Verified the rendered anchor's `href` before clicking:
  `/structure?symbol=AAPL&asof=2026-06-22T23%3A59%3A59Z`. Clicked the AAPL row; `location.href`
  matched exactly after navigation. Symbol input `value="AAPL"`; As-of input
  `value="2026-06-22T23:59:59Z"`. `tradable-map-table` was already present (no Load click) with a
  chart and a bands list containing `resistance 298.02–300.1001 Class A 97 1610 round number`.

### UT-06 — Click a Skipped Members row also drills into `/structure`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-06-result.png`
- Clicked the ABBV skip row from the 2026-06-22 view; navigated to exactly
  `/structure?symbol=ABBV&asof=2026-06-22T23%3A59%3A59Z`; Symbol="ABBV", As-of exact match;
  `tradable-map-no-bar-series` shown ("No bar series recorded for ABBV."); no crash, no console
  error, no fabricated band.

### UT-07 — History click for a date with no matching screen leaves the UI unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-07-result.png`
- Rather than the devtools-fetch simulation the test plan offers as a fallback (which cannot itself
  exercise the frontend's own state-update code, since there is no rendered row for a genuinely
  nonexistent date), this ran the REAL `handleSelectHistoryScreen` code path end-to-end: intercepted
  `window.fetch` so a request for `?date=2026-06-22` returns `{"screen": null}` (the exact shape the
  real backend returns for a true no-match), then clicked the real, rendered `2026-06-22` row.
  Briefing's first row stayed TSLA (unchanged from before the click); the exact text "No recorded
  screen matches 2026-06-22 — still showing the previously displayed screen." appeared in
  `desk-history-fetch-error`; no JS console error. `window.fetch` was restored to the original
  immediately after.

### UT-08 — `/structure?symbol=AAPL` with `asof` omitted
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-08-result.png`
- After a 2.5s wait (ruling out a delayed auto-load), live DOM read: Symbol empty, As-of empty,
  `tradable-map-idle` shown.

### UT-09 — `/structure?asof=...` with `symbol` omitted
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-09-result.png`
- Same check after 2.5s: both fields empty, idle state — no partial prefill from either param alone.

### UT-10 — `/structure`'s manual Load flow still works unaided
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-10-result.png`
- Typed "AAPL", typed a known-good As-of (`2026-06-22T23:59:59Z`), clicked "Load"; the Tradable Map
  populated with the same band set seen via drill-in (UT-05); no console errors, no stuck-loading
  state — confirms the prefill addition did not disturb the pre-existing manual path.

### UT-11 — `/desk`'s Run Screen / Top-up controls still render
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-11-result.png` (capture-aid disclosed above)
- Live HTML confirmed both `desk-run-screen-button` ("Run Screen") and `desk-topup-button`
  ("Top-up") are present with no `disabled` attribute. Neither button was clicked, per the phase's
  explicit persistence-discipline instruction (Run Screen is a write action).

### UT-12 — Screen History and drill-in links are discoverable without instructions
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-12-result.png`
- Dispatched a real CDP hover over a history row: `getComputedStyle(el).cursor === "pointer"`,
  `el.matches(':hover') === true`, background changed to `rgba(15, 23, 42, 0.4)` (the
  `hover:bg-slate-900/40` class taking effect). Hovered a Briefing row: the row's own background
  changed identically on hover, and its covering stretched-link `<a>` reports `cursor: pointer` —
  both new interactions are discoverable within two hovers, no instructions needed.

### UT-J-01 — J-01: Universe ingestion — fetched, registered, honest (goal-mode regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-J-01-empty-state.png`,
`UT-J-01-populated.png`
- With the fixture root's universe dir genuinely empty, `GET /research/desk/universe` returned the
  honest empty payload `{"snapshots":[],"latest":null,"integrity_errors":[]}` (never a 404).
  Seeded the committed `apps/backend/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json`
  fixture (a verbatim copy, no re-registration) and re-checked live: the GET listed it with
  `checksum: "817cc184bbb3"`, `member_count: 103` (within the 90–110 bound), `source_url` the
  documented Wikipedia S&P 100 URL, members alphabetically sorted, and `BRK-B` present (confirming
  the `BRK.B → BRK-B` normalization survived to disk). Deeper parser-contract-level assertions
  (validation-failure honesty, re-registration no-op) are unit-test territory, already confirmed
  green in this iteration's backend suite run (1333 passed, 0 failed, fingerprint
  `08e471b10130e1e2` unchanged — per `docs/handoffs/goal-desk-iter-6-dev.md` and
  `reports/qa/goal-desk-iter-6-qa.md`).

### UT-J-02 — J-02: Coverage + explicit bar top-up over the universe (goal-mode regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-J-02-empty-state.png`,
`UT-J-02-populated.png`
- Before any universe snapshot existed, `GET /research/desk/coverage` returned the honest empty
  payload `{"universe_snapshot_id":null,"timeframes":["1h","4h","1d","1w"],"members":[]}` — already
  confirming the pinned timeframe set (exactly `1h/4h/1d/1w`, no `5m`/`1m`) even in the empty state.
  After seeding the same 103-member universe fixture (with only AAPL's real bars present in this
  fixture root's bar dir), the GET returned exactly 103 member entries with the SAME timeframe set,
  and a clean truth-table split: `AAPL` was the only symbol showing `has_bars:true` on any
  timeframe; all other 102 members (`ABBV`, `ABT`, `ACN`, `ADBE`, `AIG`, ...) showed `has_bars:false`
  on every timeframe — an exact live match to which bars this fixture root actually holds. The
  resumable-top-up-run acceptance clause (a POST-based, single-flight, store-first walk) was not
  triggered live (a write action, out of scope for this pass); it is unit-test-covered and
  confirmed green in the same suite run cited above.

### UT-J-03 — J-03: The screen — pinned inputs, append-only snapshot, deterministic rank (goal-mode regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-6-evidence/UT-J-03-screen-verbatim.png` (plus UT-01/UT-03/
UT-05 evidence above, which exercise the same endpoint from the UI side)
- `GET /research/desk/screen?date=2026-06-22` served the exact persisted snapshot verbatim (checked
  directly at the API level and via the UI in UT-03): AAPL's row matched the on-disk JSON
  field-for-field (`band_class A`, `distance_bps 0.33523150389608725`, `price_low 298.02`,
  `price_high 300.1001`). The 10 rendered rows' `distance_bps` values were monotonically
  non-decreasing (0.00, 0.00, 0.30, 0.31, 0.73, 1.62, 78.37, 95.54, 144.94, 148.08), consistent with
  the class-then-distance-ascending rank rule (all ten happened to be Class A in this sample).
  AAPL's screen-row band (298.02–300.1001, Class A, score 97.0) matched
  `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T23:59:59Z`'s own band-list entry
  byte-for-byte (UT-05). The same-pins-re-run/append-only-idempotency clause requires a POST to the
  compute endpoint — a write action explicitly out of scope for this browser pass (the exact reason
  `journey-scripts/J-04.json` was fixed this iteration); it is unit-test-covered and confirmed green
  in the same suite run cited above.

---

## Failed Tests

None.

---

## Skipped Tests

None. (J-04 and J-07 were re-verified via deterministic golden replay per the dispatch's
instruction and are intentionally not re-tested or re-listed by this agent.)

---

## Anti-goal / persistence-discipline confirmation (TC-10)

Before this pass began, the operator's real `apps/backend/.data/` held exactly 2 screen files
(`screen-2026-06-22-3ecd45c062c7.json`, mtime `2026-07-25 10:14`; `screen-2026-07-25-e184a7dc2f86.json`,
mtime `2026-07-25 12:45`), 355 bar files, and 1 universe file
(`universe-2026-07-25-49b33fa31680.json`, mtime `2026-07-25 04:58`). After the entire browser pass
(including the fixture-scoped backend's full lifecycle), the SAME directory shows the identical
file counts and identical mtimes on all three — confirmed via `ls -la` and checksums immediately
after tearing down the fixture-scoped backend. No write ever reached the ambient store: every
`TAPEOLOGY_*_DIR`/`*_DB` env var this pass set pointed at the throw-away root
`/var/tmp/iad.goal-desk-iter-6.822370/desk-iter6-fixture-qa/`, and derived caches
(`tradability_cache.db`, `setups_scan_cache.db`, `bar_index.db`) all resolve as siblings of the
INJECTED bar-store root (confirmed by reading `tradability_cache.py`/`setups_scan_cache.py`'s own
`resolve_*_path(str(store.root))` implementations), so they too landed inside the throw-away root,
never beside the real bars.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (fixture-scoped for the whole pass; ambient/unscoped
  instance restarted afterward — see "Fixture-scoped data basis" above)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-26
- **Evidence directory:** `reports/qa/goal-desk-iter-6-evidence/`
