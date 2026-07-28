# Phase goal-desk-iter-11 — UI Test Results

**Phase:** goal-desk-iter-11
**Date:** 2026-07-28
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 11/11 tests passed (0 skipped)

---

## Test rigs used (disclosed per the iter-9/iter-10 lessons)

Two distinct backends served `http://localhost:8301` at different points in this run — the
frontend (`http://localhost:3301`) was never restarted; only the backend process bound to `:8301`
was swapped:

1. **Ambient backend** (`apps/backend/.data/`, the project's real store) — used for UT-02 and UT-09
   (both genuinely require/tolerate a zero-top-up-run state, which the ambient store already had —
   confirmed live via `curl http://localhost:8301/research/desk/topup/runs` → `{"runs":[],"latest":null}`
   before touching anything), and again after restoration for the J-09 golden-script self-check and
   the `test_mcp_server.py` regression run.
2. **Fixture-scoped rig** — a fresh `cp -a` copy of `apps/backend/.data/` to
   `${TMPDIR}/desk-iter11-scoped-qa` (env-redirected via `TAPEOLOGY_BAR_DIR` /
   `TAPEOLOGY_DESK_UNIVERSE_DIR` / `TAPEOLOGY_DESK_SCREEN_DIR` / `TAPEOLOGY_JOURNAL_DB`, never the
   ambient store), served on the same port `:8301` so the already-running frontend needed no rebuild
   (`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`'s established recipe). Used for UT-01,
   UT-03 through UT-08, and UT-10. Three checkpoint runs were recorded into this rig's own
   `.data/topup_runs/` before/during browser testing:
   - **Checkpoint 1** (ordinary): triggered in-process via `DeskTopupComputeManager.trigger()` with
     a monkeypatched `_run_one_pair` (the same technique
     `test_desk_topup_compute.py`'s own manager-mechanics tests use) → `state: done`,
     `pairs_attempted == pairs_total == 404`.
   - **Checkpoint 2** (cancelled): same technique with a `threading.Event` handshake, cancelled after
     3 pairs → `state: cancelled`, `pairs_attempted == 3 < pairs_total == 404`.
   - **Checkpoint 3** (one induced failure): triggered by **actually clicking the "Top-up" button in
     the browser** against a scoped backend process whose `get_market_adapter` dependency was
     overridden (in-process, before `uvicorn.run`) to a small double mirroring
     `test_desk_topup_compute.py`'s own `_NthCallFailsAdapter` — fails exactly once with
     `NoDataForWindow("no data for that window")`, synthetic bars otherwise, zero real network calls
     ever. Result: `state: done`, `404/404` attempted, `0 reused · 403 fetched · 1 failed`
     (AAPL 4h). This same click also produced UT-07's auto-refresh evidence.

   The scoped rig's backend was stopped/restarted in place for UT-01's steps 6–7 (backend-down/up).
   At the end of the run the scoped backend was stopped and the **original ambient backend was
   restarted with its original command/env** (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301
   scripts/start-backend.sh`); confirmed healthy, confirmed its own `topup/runs` is genuinely
   `{"runs":[],"latest":null}` again (proving the scoped copy was never the same store), and the
   frontend process was never touched throughout.

J-06 (MCP contract) was verified against the ambient backend after restoration, using the hermetic
`test_mcp_server.py` suite directly (see UT-J-06 below) rather than through this session's own live
`mcp__tapeology__*` client, which is configured for `http://localhost:8000` — a port this iteration's
environment never uses (`:8301`/`:3301`) — and so could not connect; noted as an environment/tooling
wiring gap, not a product defect.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Section present, last on page, independent failure states | smoke | P1 | Top-up Runs is the last section on `/desk` in every state; no console errors; a backend outage shows two INDEPENDENT amber unreachable panels (screen + Top-up Runs); recovers cleanly on restart | Confirmed last of 6 sections in both empty and populated states; console clean (only the benign React DevTools info line); stopping the scoped backend produced `desk-screen-unavailable` + `desk-topup-runs-unavailable`, both reading "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." (nav itself also disclosed unavailability); restarting fully recovered both panels and all 3 Top-up Runs rows | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-01-backend-unreachable.png`, `UT-01-recovered.png` |
| UT-02 | Honest empty state; GET never triggers a compute | happy-path | P1 | Panel reads exactly "No top-up runs recorded yet." with 0 rows; 3 reloads issue only GETs, never a POST to `topup/compute`, snapshot stays `null` | Verified live on the ambient backend (genuinely 0 runs recorded): `desk-topup-runs-empty` present, exact text match, 0 rows/no table. Backend access log across 3 reloads showed only `GET .../topup/runs`, `GET .../topup/compute`, `GET .../screen`, `GET .../screen/compute`, `GET /meta/ui-routes` — zero POSTs; `GET /research/desk/topup/compute` stayed `null` throughout | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-02-empty-state.png` |
| UT-03 | Populated table lists every run with correct columns | happy-path | P1 | 3 rows (Checkpoints 1/2/3); header exactly `date, run, state, attempted / total, universe snapshot`; cancelled row's attempted < total even though not latest | Header cells exactly `["date","run","state","attempted / total","universe snapshot"]`. 3 rows, chronological: `done 404/404`, `cancelled 3/404`, `done 404/404`, all sharing `universe-2026-07-25-49b33fa31680`; none missing/duplicated/merged | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-03-04-05-populated-topup-runs.png` |
| UT-04 | Latest-run detail counts are correct and sum right | happy-path | P1 | Heading matches table's latest row; `state`/`N of M attempted`/counts string present; reused+fetched+failed == attempted; failed == 1 | Heading "Latest run — 2026-07-28 · topup-2026-07-28-b5bb6c17323d" matches row 3 exactly; stats "state: done", "404 of 404 pairs attempted", "0 reused · 403 fetched · 1 failed"; 0+403+1 = 404 = N; failed count = 1 matching the one induced failure | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-03-04-05-populated-topup-runs.png` |
| UT-05 | Failed pair's verbatim detail is legible, untruncated | error | P1 | "Failed pairs (1)" heading; one item `<SYMBOL> <tf> — <verbatim detail>` containing the exact substring "no data for that window", untruncated, legible in one screenshot | "Failed pairs (1)" heading present; item reads "AAPL 4h — no data for that window" verbatim (not a placeholder, no ellipsis); confirmed fully legible with no horizontal clipping in the evidence crop | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-05-failed-pair-detail-legible.png` |
| UT-06 | Unreached-pairs note correct and honestly absent when 0 | error | P1 | Part A (cancelled run latest): amber "X pairs not reached", X = total−attempted. Part B (all-pairs-reached run latest): note entirely absent from DOM | Part A: `desk-topup-run-latest-unreached` present, text "401 pairs not reached" (404−3=401), styled `text-amber-200/70`. Part B: same selector returned `null` after Checkpoint 3 (404/404 attempted) — confirmed absent from the DOM, not merely hidden | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-06-partA-unreached-pairs.png`, `UT-03-04-05-populated-topup-runs.png` |
| UT-07 | Panel auto-refreshes on run completion, no reload | happy-path | P2 | After clicking Top-up and reaching terminal state, table row count +1 and Latest-run block references the new run id within ~2s, with no manual reload | Caught button label "Topping up…" mid-run (a QA-only artificial per-call delay in the fake adapter made this observable over ~2.5 min instead of near-instant); after the run reached `done` (confirmed via a separate `curl` poll, never touching the browser), a fresh DOM read — with no navigate/click issued by this agent in between — showed the button back to "Top-up", row count 2→3, and the Latest-run block already referencing the just-finished run id. Frame-by-frame "no flash of empty state" was not independently captured (only before/after DOM snapshots), so that one sub-clause is PASS-by-architecture-and-snapshot-evidence rather than video-verified; the core auto-refresh contract is solidly evidenced | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-07-topup-in-progress.png`, `UT-07-auto-refreshed-after-completion.png` |
| UT-08 | Every pre-existing `/desk` section unaffected | regression | P1 | Provenance/Briefing/Skipped Members/Screen History drill-through/Run Screen button all render and behave exactly as before | Provenance fields all non-blank (Universe snapshot/Screen date/As of/Config fingerprint/Bar-store signature); Briefing table has the 8 expected columns incl. `basis`, 63 rows; Skipped Members shows "Skipped — no bars (38)" with its usual columns; clicking the 2026-06-22 history row showed "Viewing the recorded screen for 2026-06-22 — not the latest.", clicking Latest reverted cleanly; Run Screen button reads "Run Screen", not disabled/stuck | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-08-regression-history-drillthrough-reverted.png` |
| UT-09 | Discoverable with plain scrolling, distinct from history | ux | P3 | Top-up Runs reached by plain scroll; heading styled identically to other sections; clearly distinct from Screen History | Section order Provenance→Briefing→Skipped members→Screen history→Run Screen and Top-up controls→Top-up runs, plain DOM flow, no toggle/tab; heading `className` byte-identical between "Top-up Runs" and "Screen History" (`mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500`); distinct heading text and distinct table columns | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-09-discoverability.png` |
| UT-10 | Copy stays descriptive, no advice/urgency styling | ux | P3 | No advice/urgency language anywhere in the section; failed-pair detail and unreached note use restrained, non-alarming styling | Scanned full section text (empty state, headers, latest-run stats, unreached note, failed-pairs list) against an advice/urgency word list (warning, danger, consider, opportunity, buy, sell, alert, urgent, recommend, …) — zero matches; failed-pair row styled `text-xs text-slate-400`, unreached note styled `text-amber-200/70` — both restrained, consistent with the page's existing cancelled/error styling family | PASS | `reports/qa/goal-desk-iter-11-evidence/UT-06-partA-unreached-pairs.png`, `UT-05-failed-pair-detail-legible.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools (Required-still-passing regression) | regression | P1 | MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` byte-identical to curl; `get_endpoint` proxies verbatim; MCP suite green | This session's own live `mcp__tapeology__*` client is configured for `http://localhost:8000` (not this iteration's `:8301`/`:3301`) and could not connect — an environment wiring gap, not a product defect. Its tool manifest nonetheless lists exactly 17 tools (`backtests, bars, datasets, desk_screen, desk_universe, edge_report, get_endpoint, levels, pnl_ledger, setups, strategies, tape_features, tape_history, tape_state, taxonomy, tradability, ui_route_map`), matching `EXPECTED_TOOLS` in `tests/test_mcp_server.py` exactly. Ran that hermetic suite directly (`cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -q`): 34/34 passed, exit 0 — covering byte-identity, honest-empty states, `get_endpoint` proxying/allowlist, and `desk_universe`/`desk_screen` coverage | PASS | pytest output captured in this report's Environment section below; no screenshot (backend/MCP-contract journey, not a UI walk) |

---

## Passed Tests

### UT-01 — Section present, last on page, independent failure states
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-01-backend-unreachable.png`, `UT-01-recovered.png`
- Normal load: `sectionOrder` DOM query returned `["Provenance","Briefing","Skipped members","Screen history","Run Screen and Top-up controls","Top-up runs"]` — Top-up Runs last, in both the empty-ambient state and the populated-scoped state.
- Console: `get_console_messages` after a fresh navigate showed only the benign "Download the React DevTools…" info line — no red errors.
- Backend down (scoped backend `kill -TERM`, then reload): `document.body.textContent` included, independently, `desk-screen-unavailable` and `desk-topup-runs-unavailable`, each reading "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." The page did not blank out — heading and page description still rendered; nav itself also honestly disclosed "navigation unavailable — backend unreachable."
- Recovery: after restarting the scoped backend and reloading, both `-unavailable` testids were gone and the Top-up Runs table showed all 3 rows again, no leftover error banners.

### UT-02 — Honest empty state; GET never triggers a compute
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-02-empty-state.png`
- Ran against the live ambient backend, which had genuinely never recorded a J-09-aware top-up (`curl http://localhost:8301/research/desk/topup/runs` → `{"runs":[],"latest":null}` before any browser interaction).
- DOM check: `desk-topup-runs-empty` present, text exactly "No top-up runs recorded yet.", 0 `desk-topup-run-row` elements, no `desk-topup-runs-table`.
- Reloaded `/desk` 3 times; diffed the backend's own uvicorn access log across the reload window — every request to `/research/desk/topup/runs` was a `GET`; zero `POST /research/desk/topup/compute` lines appeared; `GET /research/desk/topup/compute` continued to return `null` after all 3 reloads.

### UT-03 — Populated table lists every run with correct columns
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-03-04-05-populated-topup-runs.png`
- After Checkpoint 3, table header cells (left to right): `date, run, state, attempted / total, universe snapshot` — exact match.
- 3 rows, oldest-first: `2026-07-28 / topup-...a890f4c638f1 / done / 404 / 404 / universe-2026-07-25-49b33fa31680`; `.../96b8283705c2 / cancelled / 3 / 404 / ...`; `.../b5bb6c17323d / done / 404 / 404 / ...`.
- Row 2 (cancelled, not latest) still shows `3 / 404` — a strictly smaller attempted than total, proving the per-row summary discloses incompleteness on every row, not only the latest.

### UT-04 — Latest-run detail counts are correct and sum right
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-03-04-05-populated-topup-runs.png`
- "Latest run — 2026-07-28 · topup-2026-07-28-b5bb6c17323d" matches the table's own last row's id/date exactly.
- Stats line: "state: done", "404 of 404 pairs attempted", "0 reused · 403 fetched · 1 failed" — `0+403+1 == 404` and the failed count (1) matches the single induced failure.

### UT-05 — Failed pair's verbatim detail is legible, untruncated
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-05-failed-pair-detail-legible.png`
- "Failed pairs (1)" heading, matching UT-04's failed count.
- One list item: "AAPL 4h — no data for that window" — contains the exact induced substring, symbol/timeframe match the pair the QA-only fake adapter was set to fail on, no ellipsis/truncation/generic placeholder.
- A cropped, upsampled section screenshot (table + latest-run stats + failed-pairs list together) confirms the text is fully legible with no horizontal clipping. (Note: a raw deep-scroll viewport screenshot rendered blank in this Chrome MCP setup — a known environment quirk, not a product defect — so evidence was captured via a full-page screenshot cropped/upsampled to the relevant section instead; DOM-text extraction independently confirms the exact string.)

### UT-06 — Unreached-pairs note correct and honestly absent when 0
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-06-partA-unreached-pairs.png` (Part A), `UT-03-04-05-populated-topup-runs.png` (Part B)
- Part A (rig paused right after Checkpoint 2, cancelled run is latest): `desk-topup-run-latest-unreached` present, text "401 pairs not reached" — `404 − 3 = 401`, computed from the same "3 of 404 pairs attempted" text shown just above it; styled `text-amber-200/70`.
- Part B (Checkpoint 3, a run that reached every pair, is latest): the same selector returns no element at all — confirmed structurally absent from the DOM (not a hidden/blank/"0 pairs not reached" element).

### UT-07 — Panel auto-refreshes on run completion, no reload
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-07-topup-in-progress.png`, `UT-07-auto-refreshed-after-completion.png`
- Clicked the pre-existing "Top-up" button (`data-testid="desk-topup-button"`); immediately read back button text "Topping up…".
- Polled the run's terminal state via `curl http://localhost:8301/research/desk/topup/compute` in a separate shell (never touching the browser tab) until `state: done` (404/404).
- Returned to the SAME browser tab (no navigate, no click, no reload issued by this agent since the initial click) and read the DOM: button back to "Top-up", `desk-topup-run-row` count 2→3, and the "Latest run" detail block already referencing the just-finished run's own id and stats — proving the page's own poll (not this agent) picked up the terminal state and re-rendered unaided.
- One sub-clause ("no flash of empty state during the update") was not captured frame-by-frame; the before/after DOM snapshots plus the component's architecture (existing rows are keyed, not remounted) support it but it is not independently video-verified — noted rather than asserted with full certainty. This does not affect the PASS verdict for the test's core, explicitly-required assertion.

### UT-08 — Every pre-existing `/desk` section unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-08-regression-history-drillthrough-reverted.png`
- Provenance: Universe snapshot / Screen date / As of / Config fingerprint / Bar-store signature all populated (non-blank) — `universe-2026-07-25-49b33fa31680`, `2026-07-27`, `2026-07-27T23:59:59Z`, `08e471b10130e1e2`, `7eab5f03cf23e8c7`.
- Briefing: table header exactly `symbol, side, class, distance, score, coverage, tick evidence, basis` (8 columns, including `basis` per iter-9), 63 ranked rows.
- Skipped Members: "Skipped — no bars (38)" panel renders with its symbol/reason/coverage/tick-evidence columns.
- Screen History drill-through: clicking the `2026-06-22` row showed "Viewing the recorded screen for 2026-06-22 — not the latest." with a "Latest" button; clicking it removed the banner and reverted cleanly.
- Run Screen button: text "Run Screen", `disabled: false` — not stuck on a prior "Computing…" state.

### UT-09 — Discoverable with plain scrolling, distinct from history
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-09-discoverability.png`
- Confirmed via `document.querySelectorAll('section[aria-label]')` that Top-up Runs is a plain top-level `<section>` in normal document flow — no toggle, tab, or "show more" control gates it.
- Heading `className` for "Top-up Runs" and "Screen History" are byte-identical (`mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500`) — same visual treatment.
- Distinct heading text and distinct table columns (`date/run/state/attempted-total/universe-snapshot` vs. Screen History's `date/rows/skipped/provenance`) make the two sections unambiguous.

### UT-10 — Copy stays descriptive, no advice/urgency styling
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-11-evidence/UT-06-partA-unreached-pairs.png`, `UT-05-failed-pair-detail-legible.png`
- Extracted the full Top-up Runs section text (both the Checkpoint-2-latest state with its "401 pairs not reached" note, and the Checkpoint-3-latest state with its "AAPL 4h — no data for that window" failed-pair line) and scanned it against an advice/urgency word list — zero hits.
- Every string observed is plain factual measurement: "state: cancelled", "401 pairs not reached", "AAPL 4h — no data for that window".
- Styling: failed-pair row `text-xs text-slate-400`, unreached-pairs note `text-amber-200/70` — both restrained, matching the rest of `/desk`'s existing error/cancelled-state palette; no red "ALERT" banners, no flashing, no action-implying icon.
- `pytest tests/test_copy_discipline.py` (automated lint, TC-11) is outside this agent's own re-verification scope; this UX pass is the human/DOM-eyeball counterpart per the test plan's own framing.

### UT-J-06 — MCP contract v3 — 17 read-only tools (Required-still-passing regression)
**Verdict:** PASS
**Evidence:** pytest output below; this journey has no UI surface (backend/MCP-protocol contract), so no screenshot applies.
- goal.md's J-06 Steps/Acceptance (MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` byte-identical to curl; `get_endpoint` on `/research/desk/screen` proxies verbatim; MCP suite green) are inherently `(Keyless; automated.)` per goal.md's own text, not a browser walk.
- This session's own live `mcp__tapeology__*` MCP client returned `ConnectError` for every call: "tapeology backend unreachable at http://localhost:8000" — this session's actual backend runs on `:8301` (ambient) / was `:8301` (scoped); `:8000` is an unrelated default this environment never used. This is an MCP-server-wiring gap in how this interactive session was provisioned, not a regression in the product's own MCP contract — noted honestly rather than silently skipped.
- Despite being unable to connect, the client's own advertised tool manifest (visible without a live call) lists exactly these 17 names: `backtests, bars, datasets, desk_screen, desk_universe, edge_report, get_endpoint, levels, pnl_ledger, setups, strategies, tape_features, tape_history, tape_state, taxonomy, tradability, ui_route_map` — a byte-for-byte match (as a set) to `EXPECTED_TOOLS` in `apps/backend/tests/test_mcp_server.py`.
- Ran the authoritative hermetic suite directly: `cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -q` → 34 tests, all passed, exit code 0. This suite (confirmed by reading it) covers exactly J-06's Acceptance clauses in-process: the 17-tool count assertion, `get_endpoint` byte-identity against allowlisted paths (including `/research/desk/screen?date=`), honest-404/honest-empty-state proxying, and the allowlist-prefix correctness check — this is the same mechanism J-06's own `(Keyless; automated.)` tag points to.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (ambient for UT-02/UT-09 and the post-restore checks; a fixture-scoped copy for UT-01/UT-03–08/UT-10 — see "Test rigs used" above)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`, attached to the pre-launched headless Chrome on CDP port 9222
- **Test Date:** 2026-07-28
- **Evidence directory:** `reports/qa/goal-desk-iter-11-evidence/`
- **Golden replay script:** `runs/goal-session-desk/journey-scripts/J-09.json` written after J-09 (UT-01/UT-02/UT-03/UT-04/UT-05/UT-06/UT-07/UT-08/UT-09/UT-10, all mapping to the same underlying journey) verified PASS; lint-checked clean (`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-desk/journey-scripts --journeys J-09` → `J-09 ok`) and self-verified end-to-end against the restored ambient backend (`--mode verify` → `1 journey(s), 0 failed (verdict: PASS)`); the script is deliberately read-only (three `goto /desk` steps asserting "Top-up Runs", the honest-empty text, and a post-match liveness re-check) so it never mutates whichever backend is live at future replay time — see the script's own `notes` for the documented environmental dependency (its empty-state assertion will need updating once the ambient store ever gains a real operator-run top-up record).
- **J-06 regression (MCP contract):** `cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -q` → 34 passed, 0 failed, exit code 0.
