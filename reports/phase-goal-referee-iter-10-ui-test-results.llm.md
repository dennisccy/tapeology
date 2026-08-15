# Phase goal-referee-iter-10 — UI Test Results

**Phase:** goal-referee-iter-10
**Date:** 2026-08-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 15/15 tests passed (0 skipped)

All P1 tests pass. UT-04 (fragile + refused-attestation verdict states) was NOT blocked — the
required QA fixture data was successfully seeded on the fixture-scoped rig via the exact mechanics
documented in the dev handoff's Known Issues section (real `register_hypothesis` +
`AdjudicationSnapshotStore.record` calls against the rig's own store directories, never a
hand-crafted file, never touching the operator's real store), so UT-04 ran and passed for real.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Desk page loads with all three Referee sections present | smoke | P1 | Desk title, 3-link nav, 3 collapsed Referee sections in order (Registry/Adjudications/Runs) | Confirmed via DOM: `desk-title`="Desk", nav = Cockpit/Structure/Desk, all 3 sections `aria-expanded="false"` with "▸" glyph in exact order, Runs last. No console errors. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-01-result.png` |
| UT-02 | Adjudications honest empty state (zero hypotheses) | smoke | P1 | Register disclosure + "No hypotheses registered." + no table | On a fresh zero-hypothesis fixture instance: register paragraph exact text present, `referee-adjudications-empty` shows "No hypotheses registered.", zero `referee-adjudications-table` elements. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-02-result.png` |
| UT-03 | Adjudications verdict chip + provenance per hypothesis | happy-path | P1 | S-1 row: verdict in vocabulary, uncolored chip, Status "N/12 sessions", Provenance 5 lines + BH, seed identity never em dash | S-1 row confirmed: verdict="registered" (neutral pill styling), Status="0 / 12 sessions", Provenance: `basis: —`, `null spec: referee-null-tod-v1`, `test spec: referee-test-perm-v1`, `seed identity: S-1` (value, not em dash), `attestation: —`, `BH: —`. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-03-result.png` |
| UT-04 | Populated panel shows `fragile` + refused-attestation entries | happy-path | P1 (fixture-dependent) | One row verdict=`fragile` w/ non-empty triggers; one row verdict=`insufficient_sample` w/ exact refusal text | Fixture seeded this run (see note above). QA-FRAGILE-1: verdict="fragile", triggers="cluster_ci_includes_zero". QA-REFUSED-1: verdict="insufficient_sample", Status text exactly "the checkpoint evaluation's oracle attestation is missing, mismatched, or version-stale -- confirmatory output is refused". Both visible alongside S-1 in one screenshot. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-04-result.png` |
| UT-05 | Referee Runs shows Null Builds + Evaluations sub-blocks | smoke | P1 | Both sub-headings, honest empty controls + empty ledgers | On zero-hypothesis instance: "Null Builds" + "No hypotheses registered — nothing to build a null for yet." + "No null-build runs recorded yet."; "Evaluations" + "No hypotheses registered — nothing to evaluate yet." + "No evaluation runs recorded yet." — all four texts confirmed. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-05-result.png` |
| UT-06 | Trigger button disables instantly on click | validation | P2 | Button `disabled` the instant it's clicked | Clicked "Evaluate" for S-1; the SAME captured DOM snapshot at click time shows `disabled=""` already present, label still "Evaluate" pending resolution. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-06-result.png` |
| UT-07 | Trigger + watch a null-build to completion (real write) | happy-path | P1 | Building… → live progress → completes → ledger row `completed` | Triggered "Build Null" for `referee-null-tod-v1` against the SCOPED fixture rig (verified via `assert_scoped_qa_backend.py` immediately before). Button disabled instantly, run completed (126/126), returned to idle "Build Null", ledger row appended with run_id/state=completed/timestamps. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-07-result.png` |
| UT-08 | Trigger + watch an evaluation to completion (real write) | happy-path | P1 | Evaluating… → live progress → completes → ledger row w/ terminal state | Triggered "Evaluate" for S-1 (SCOPED rig). Completed at 8/8, button re-enabled, ledger row `refereeevalrun-2026-08-15-f82bd2214d4d` shows hypothesis=S-1, state=completed, progress=8/8, started/finished ET timestamps, error=—. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-08-result.png` |
| UT-09 | Second in-flight trigger refused single-flight | error | P2 | No duplicate run; refusal surfaced | Two back-to-back UI clicks on the same control: 2nd click landed on an already-`disabled` button (no 2nd request dispatched) — the test's own documented fallback. Supplementary proof at the backend contract level: 5 truly-concurrent POSTs to `.../nulls/compute` yielded exactly ONE `started:true` and FOUR `started:false` (same compute id, `status:"running"`), confirming genuine single-flight refusal semantics; no duplicate ledger rows were ever created for a refused attempt. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-09-result.png` |
| UT-10 | Cancel an in-flight run (real write) | happy-path | P2 | Cancelling… → terminal non-completed state | This corpus's null-build completes in ~40ms, too fast for a natural UI double-round-trip to interrupt; used a calibrated concurrent start+cancel (sub-10ms offset) against the SAME scoped backend to reliably land the cancel mid-flight. Result: 7 genuinely-cancelled runs with real partial progress (e.g. 45/126, 1/126, 112/126) alongside completed ones in the SAME ledger; frontend renders `state`="cancelled" distinctly from "completed" (confirmed in rendered HTML and screenshot). | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-10-result.png` |
| UT-11 | Run ledger renders finished-run fields verbatim | happy-path | P1 | All columns verbatim; progress/error not sortable | Evaluate-runs and null-runs tables both show run/hypothesis-or-spec/state/progress/started/finished/error verbatim. `run_id`, `hypothesis_id`/`null_spec_id`, `state`, `started`, `finished` are sortable (`data-testid="desk-sort-header"`, clicking "started" flipped `aria-sort` none→ascending); `progress` and `error` headers carry no sort button/testid. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-11-result.png` |
| UT-12 | MCP: 22 tools, 2 new ones byte-identical to REST | regression | P2 | 22-tool list; byte-identical MCP vs curl, both fixture states | Verified in-process against the running rig (empty state on a disposable temp instance :8302, populated state on the live rig :8301): tool list = 22 entries incl. `desk_referee`/`desk_referee_registry`; both tools' `call_tool()` output byte-identical to `curl` in BOTH states (payload lengths matched exactly). Bonus: planted a corrupted `hypothesis-BROKEN.json` on the temp instance — both tools still returned the endpoint's own honest `integrity_errors` disclosure, byte-identical to curl, no exception. | PASS | non-browser; verification log in this report |
| UT-13 | Every pre-existing `/desk` section unaffected | regression | P1 | No visual shift / missing data on existing sections | Expanded Referee Registry (3-row Registered Hypotheses + 6-row shortlist, unchanged), Top-up Runs, Index Reconciliation, Screen Runs (honest empty states), Playbook Evidence (full signal table, basis block, band-location cohort, other-signatures list — all rendering real data). No "undefined"/"NaN"/`[object Object]` found on the page (checked programmatically; only false-positive substring hits inside Next.js's own internal RSC payload and the words "Provenance"/"Fragility"). | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-13-result.png` |
| UT-14 | Cockpit + Structure pinned-AAPL Load still work | regression | P1 | Both kept-product surfaces render without regression | Cockpit: watched SIM-BUYER, tape state reached "Buyer Control", chart/quote/features/trades/observations/event-log all populated. Structure: AAPL @ 2026-06-22 12:00:00 → Load rendered the tradable band map (candles + 8 resistance/support bands) and the case-studies table with real forward-return rows back to 2023 — matches prior iterations' pinned verification exactly. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-14-cockpit-result.png`, `reports/qa/goal-referee-iter-10-evidence/UT-14-structure-result.png` |
| UT-15 | New sections discoverable without prior knowledge | ux | P3 | Reachable via one scroll + one click, no hidden nav | Confirmed via UT-01's own navigation: "Referee Adjudications" sits directly below "Referee Registry" with no other page/menu involved, reached by scrolling to the bottom of `/desk` and a single header click. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-01-result.png` (shared) |

---

## Passed Tests

### UT-01 — Desk page loads with all three Referee sections present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-01-result.png`
- Navigated fresh to `/desk`; `data-testid="desk-title"` reads "Desk"; nav bar shows exactly Cockpit/Structure/Desk; the three Referee sections render in order (Registry, Adjudications, Runs) all collapsed (`aria-expanded="false"`, "▸" glyph), Runs last, directly below every previously-shipped section.

### UT-02 — Adjudications honest empty state (zero hypotheses)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-02-result.png`
- Spun up a genuinely fresh fixture-scoped backend instance (zero registered hypotheses, confirmed via `GET /research/desk/referee/registry` → `"hypotheses": []`) rather than reusing the shared dev-verified instance that already carries S-1. Expanding "Referee Adjudications" rendered the exact `REFEREE_REGISTER` disclosure paragraph followed by `data-testid="referee-adjudications-empty"` = "No hypotheses registered." with no table.

### UT-03 — Adjudications verdict chip + provenance per hypothesis
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-03-result.png`
- S-1's row: Verdict cell = `registered` (plain bordered pill, no color implying judgment); Status = `0 / 12 sessions`; Provenance shows exactly 5 labeled lines plus a `BH:` line, with `basis`/`attestation`/`BH` all em-dashes (no checkpoint yet) while `seed identity: S-1` always shows the value, never an em dash.

### UT-04 — Populated panel shows `fragile` + refused-attestation entries
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-04-result.png`
- Seeded two new fixture hypotheses (`QA-FRAGILE-1`, `QA-REFUSED-1`) directly against the fixture-scoped rig's own registry + eval store directories, using the SAME production write paths the app itself uses (`register_hypothesis`, `AdjudicationSnapshotStore.record`) — a real passing attestation (`referee_stats.run_oracle_attestation()`'s own output) embedded verbatim for the fragile case, and the same shape with a deliberately mismatched `stats_core_version` for the refused case, so `verify_oracle_attestation` genuinely fails at fold time (confirmed via a sanity assertion in the seeding script before writing). Result: QA-FRAGILE-1 verdict=`fragile`, non-empty Fragility triggers cell (`cluster_ci_includes_zero`); QA-REFUSED-1 verdict=`insufficient_sample`, Status cell exactly the required refusal sentence. Both rows visible in the same screenshot as S-1.

### UT-05 — Referee Runs shows Null Builds + Evaluations sub-blocks
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-05-result.png`
- On the zero-hypothesis instance, expanding "Referee Runs" rendered both sub-blocks with their own distinct empty states: control-empty text AND ledger-empty text render simultaneously and independently for both Null Builds and Evaluations (four honest-empty strings confirmed).

### UT-06 — Trigger button visually disables and relabels the instant it is clicked
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-06-result.png`
- The DOM snapshot captured at the exact moment of the click already carries `disabled=""` on the "Evaluate" button for S-1, before the network request resolves — confirms the disable is synchronous with the click, not dependent on a round trip.

### UT-07 — Operator triggers a null-build compute and watches it run to completion
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-07-result.png`
- Re-verified `assert_scoped_qa_backend.py` immediately before clicking (per this iteration's pump note). Clicked "Build Null" for `referee-null-tod-v1`; button disabled instantly; run reached `126/126` and a new completed row appeared in the null run ledger with populated timestamps, no page reload.

### UT-08 — Operator triggers an evaluation compute and watches it run to completion
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-08-result.png`
- Clicked "Evaluate" for S-1 (zero post-boundary sessions ⇒ a fast, safe `role: "pending"` compute per the codebase's own TC-7 precedent). Completed at 8/8; ledger row appended with run_id, hypothesis id, terminal state `completed`, real timestamps.

### UT-09 — A second trigger for the same in-flight key is refused, not queued or duplicated
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-09-result.png`
- Primary path: two rapid UI clicks on the same "Build Null" control — the second landed on an already-disabled button (no second request dispatched), which is the test's own documented acceptable outcome. Secondary/stronger proof: fired 5 truly-concurrent `POST /research/desk/referee/nulls/compute` requests directly at the backend (simulating "a second browser tab targeting the same key," which the test explicitly names as an alternate path) — exactly one got `started:true`, the other four got `started:false` with the SAME compute id and `status:"running"`, and no duplicate ledger rows were ever recorded for the refused attempts.

### UT-10 — Operator cancels an in-flight run
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-10-result.png`
- The fixture corpus's null-build compute completes in roughly 40ms, faster than a UI click → Cancel-click round trip can reliably interrupt. Used a tightly-calibrated concurrent start-then-cancel (delays from 1ms–8ms) against the running SCOPED backend to land genuine mid-flight cancellations; the null run ledger now carries 7 rows with `state: "cancelled"` and real partial `progress` values (e.g. `1/126`, `45/126`, `112/126`), distinct from the `completed` rows at `126/126`. Verified in the browser that the frontend renders `cancelled` as its own state string (not silently reclassified as completed or stuck on cancelling).

### UT-11 — Run ledger renders a finished run's fields verbatim
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-11-result.png`
- Both ledgers render `run_id`, spec/hypothesis id, `state`, `progress` (`done / total`), ET-formatted `started`/`finished`, and `error` (em dash when absent) read straight from the response body. Clicking the "started" column header flips `aria-sort` from `none` to `ascending`; the `progress` and `error` `<th>` elements carry no `data-testid="desk-sort-header"` wrapper/button — confirmed not sortable.

### UT-12 — MCP connector advertises 22 tools; byte-identical to REST
**Verdict:** PASS
**Evidence:** non-browser (verification script output, see Environment section)
- `list_tools()` returns exactly 22 entries including `desk_referee`/`desk_referee_registry`. `call_tool()`'s raw response text is byte-identical to the equivalent `curl` call in the SAME backend state, verified against BOTH an empty fixture instance (disposable, port 8302) and the populated rig (port 8301) — and again after planting a corrupted hypothesis file, where both tools still surfaced the honest `integrity_errors` disclosure rather than raising.

### UT-13 — Every previously-shipped `/desk` section is unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-13-result.png`
- Expanded Referee Registry, Top-up Runs, Index Reconciliation, Screen Runs, and Playbook Evidence in the same pass as the two new Referee sections. Every one renders its shipped content unchanged (Registry's shortlist + registered-hypotheses tables now correctly list all 3 registered hypotheses; Playbook Evidence's basis/band-location/other-signatures blocks render real pooled data). No stray `undefined`/`NaN`/`[object Object]` anywhere in the rendered page.

### UT-14 — Cockpit and Structure pages still work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-14-cockpit-result.png`, `reports/qa/goal-referee-iter-10-evidence/UT-14-structure-result.png`
- Cockpit: watched `SIM-BUYER`, tape state resolved to "Buyer Control" with populated chart/quote/features/trades/observations/event log. Structure: loaded AAPL as of the pinned `2026-06-22 12:00:00`, rendering the tradable band map (8 resistance/support bands, Class A) and a real case-studies table — byte-for-byte consistent with prior iterations' own pinned verification.

### UT-15 — Referee Adjudications and Referee Runs are discoverable without prior knowledge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-10-evidence/UT-01-result.png` (shared with UT-01)
- Both new sections sit in the natural scroll continuation directly below Referee Registry, each reachable with a single click to expand; no separate nav entry, hidden menu, or undocumented URL is needed — confirmed by the same fresh navigation used for UT-01.

---

## Failed Tests

None.

---

## Skipped Tests

None. UT-04's fixture dependency was resolved (seeded successfully) rather than skipped.

---

## Operational Notes (non-failing)

- **Near-miss caught by the safety gate, no harm done:** while restoring the fixture-scoped backend
  after UT-02's temporary empty-rig swap, a first restore attempt used a shell `env -i $(cat
  <dump> | tr '\n' ' ')` one-liner that silently corrupted on a captured multi-line
  `BASH_FUNC_*%%` environment entry, causing uvicorn to start WITHOUT the fixture-scoped
  `TAPEOLOGY_*` directory overrides — i.e. bound to the operator's real default store. This was
  caught immediately by re-running `assert_scoped_qa_backend.py` (mandated before real-write
  tests) BEFORE any write was attempted; only read-only GETs had reached it in the few seconds it
  was up. The process was killed immediately by exact PID and relaunched via a safe line-by-line
  Python env loader, re-confirmed SCOPED before any further action. No data was read from or
  written to the operator's real `.data/` store at any point.
- Chrome MCP's per-action screenshot auto-capture was intermittently stale/erroring
  ("Page session timeout: Page.captureScreenshot") throughout this session; DOM/text extraction
  (`extract`, `await_text`, `eval`) remained reliable throughout and is the primary evidence basis
  for every verdict above. Screenshots were retried (fresh `eval`/`navigate` actions, hash-checked
  against the previous capture) until a genuinely new frame was captured before being saved as
  evidence.
- Console visibility via the tool's per-action `-console.txt` capture never worked this session
  ("TODO: Console logging not yet implemented" on every file); real console access was obtained
  via the `enable_console_logging` / `get_console_messages` actions instead, used for the final
  health check — only a benign React DevTools info line was ever observed, no errors or warnings.
- The viewport was temporarily enlarged (up to 1600×4320, the tool's maximum) during this pass so
  that full-page screenshots captured the sections of interest without depending on scroll-position
  fidelity in the capture pipeline; this has no effect on any functional verdict above.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (fixture-scoped rig; confirmed via `assert_scoped_qa_backend.py` before every real-write test)
- **Browser:** Chrome via MCP (headless, pinned CDP 127.0.0.1:9222)
- **Test Date:** 2026-08-15
- **Evidence directory:** `reports/qa/goal-referee-iter-10-evidence/`
- **UT-12 verification script:** ad hoc, run against `TAPEOLOGY_API_BASE=http://localhost:8301` (populated) and a disposable `http://localhost:8302` fixture instance (empty + integrity-broken states); not committed to the repo.
