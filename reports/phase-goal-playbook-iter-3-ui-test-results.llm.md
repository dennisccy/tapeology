# Phase goal-playbook-iter-3 — UI Test Results

**Phase:** goal-playbook-iter-3
**Date:** 2026-08-10
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped) — journey J-03, covering acceptance sub-checks TC-1..TC-6 from `docs/phases/goal-playbook-iter-3.md`. J-10 excluded per dispatch (verified separately by deterministic golden replay).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-03 | The Playbook lands on `/desk` | happy-path | P1 | Empty state + enabled Run Playbook; a fixture-scoped run renders the populated signals table with chips/disclosures/forward cells/provenance; an in-flight second trigger is refused (single-flight); a non-session date shows the refusal copy verbatim; a legacy (payload_version 1) record shows the literal absence string; every shipped `/desk` section renders exactly as shipped in the same pass | All six sub-states verified live against the real backend (fixture-scoped session dates within its recorded range): TC-1 empty state, TC-2 populated table (TXN open_low_break signal, full forward/invalidation/baseline detail, provenance line), TC-3 single-flight refusal surfaced ("Refused — a playbook compute is already running..."), TC-4 non-session refusal copy verbatim (`2024-01-06 is not a recorded trading session -- ...`), TC-5 legacy record shows `"measurement not recorded in this record"` in all three cells (forward/invalidation/baseline), TC-6 all 10 shipped `/desk` section headings present and rendering unchanged alongside the new Playbook Signals section | PASS | `reports/qa/goal-playbook-iter-3-evidence/J-03-TC1-empty-state.png`, `J-03-TC2-populated-table.png`, `J-03-TC3-single-flight-refusal.png`, `J-03-TC4-non-session-refusal.png`, `J-03-TC5-legacy-record-absence.png`, `J-03-TC6-shipped-sections-intact.png` |

---

## Passed Tests

### UT-J-03 — The Playbook lands on `/desk`
**Verdict:** PASS

**Evidence:** see six screenshots above, `reports/qa/goal-playbook-iter-3-evidence/J-03-TC*.png`

**Setup note:** The dispatched backend (`:8301`) is the project's normal fixture-scoped desk instance with real recorded bars spanning 2023-12-01 through 2026-08-07 (not a synthetic mini-fixture). To exercise every acceptance state without triggering any out-of-scope real-universe judgment call, the following session dates were used, each verified first via direct backend reads/computes before driving the browser:
- **2026-08-07** (the most recent recorded session — i.e. the blank-date default) — has a real, previously-uncomputed opening-range-break signal (TXN, `open_low_break`, short) once computed, used for TC-2.
- **2026-08-06** (recorded session, never computed) — used for TC-1 (empty state) and TC-3 (single-flight refusal, by triggering compute then firing a second trigger while the first was still `running`).
- **2024-01-06** (a Saturday that falls *within* the anchors' recorded span but carries no session) — used for TC-4; `refuse_if_not_a_session` correctly refuses it (a date after the recorded span, e.g. a real future Saturday, is NOT provably a non-session per the module's fail-open contract, so this in-span weekend was required to exercise the refusal path at all).
- **2026-08-04** — a legacy (`payload_version` 1) record was planted directly via `PlaybookStore.record(...)` (the same store class/directory the live route reads, using a placeholder `playbook_input_signature` so it collides with nothing) to exercise TC-5, since no `payload_version` 1 record exists anywhere in the current fixture data (the feature has only ever shipped version 2). This is read-only from the UI's perspective — the store's own `record()` API, called directly, the same way the unit test `test_j01_era_record_serves_verbatim_with_honest_absence_and_unchanged_sha` constructs its fixture.

**Steps and observations:**

1. **TC-1 — empty state.** Navigated to `/desk`, entered `2026-08-06` in the Playbook Signals session-date input (`data-testid="desk-playbook-date-input"`). Observed: `"Playbook not computed for this session."` with an ENABLED `Run Playbook` button (`data-testid="desk-playbook-compute-button"`). Screenshot: `J-03-TC1-empty-state.png`.
2. **TC-2 — populated table.** With the date input blank (the default, which server-resolves to the most recent recorded session, 2026-08-07, already computed via a prior real compute against the live fixture backend), the section rendered: Record id `playbook-2026-08-07-fe29f0b6eb53`, Session date `2026-08-07`, Playbook input signature, Config fingerprint `08e471b10130e1e2`; a baseline-summary table (`open_low_break:short` signals row vs. baseline row, both signed consistently); a signals table row for `TXN` (setup chip "Open-Low Break", side chip "short", trigger 09:55:00 ET, trigger price 283.17, invalidation 286.48, entry "level") rendered in served order. Clicked the row (`data-testid="desk-playbook-signal-row"`) to expand `PlaybookSignalDetail`: geometry/volume/market/disclosure lines, a full forward-measurement table (1m/5m/1h/4h/close columns: exit, ret%, MDD L%, MDD S%), an invalidation-breached disclosure line (all horizons "not breached"), and a baseline-anchor-count note. Screenshot: `J-03-TC2-populated-table.png`.
3. **TC-3 — single-flight refusal.** With the date input at `2026-08-06`, fired the `Run Playbook` click handler twice back-to-back (both dispatched before the first trigger's response had a chance to disable the control — verified via the button's own `disabled` property still reading `false` immediately after both firings, i.e. this reproduces a genuine double-submit race, not just two well-spaced clicks that both land while idle). Observed: the compute entered `Computing…` with a live `0/101 member(s) walked` progress readout and a `Cancel` button, AND the surfaced message `"Refused — a playbook compute is already running. Wait for it to finish, then try again."` — the refusal is visibly rendered, not silently dropped or queued. Screenshot: `J-03-TC3-single-flight-refusal.png`.
4. **TC-4 — non-session refusal.** Entered `2024-01-06` (in-span Saturday) and clicked `Run Playbook`. Observed the refusal copy rendered verbatim, matching the backend's own `desk_sessions.non_session_refusal` sentence byte-for-byte: `"2024-01-06 is not a recorded trading session -- the daily bars on file for AAPL, ABBV, ABT, ACN, ADBE (2023-12-01 through 2026-08-07) record no session on that date. A screen for it would carry a map built from an earlier session and a forward measurement that is empty by construction."` No compute started (state stayed `"Playbook not computed for this session."`, no `Computing…`/progress indicator appeared). Screenshot: `J-03-TC4-non-session-refusal.png`.
5. **TC-5 — legacy-record absence literal.** Entered `2026-08-04` (the planted `payload_version` 1 fixture record). Observed the record-level banner `"This record predates measurement — measurement not recorded in this record for any of its signals; only detection fields are available."` and the signals table row for TXN (setup/side/trigger/invalidation fields all present, since those are J-01-era detection fields). Clicked the row to expand: the "forward measurement" block, "invalidation disclosure" block, and the baseline note ALL rendered the exact literal string `"measurement not recorded in this record"` — never blank, never a fabricated number. Screenshot: `J-03-TC5-legacy-record-absence.png`.
6. **TC-6 — shipped `/desk` sections unchanged in the same pass.** Reloaded `/desk` fresh and enumerated every `h2`/`h3` heading on the page: `Screen History`, `Forward Returns`, `Run Screen / Top-up / Reconcile Index / Deep Backfill`, `Briefing`, `Skipped Members`, `Top-up Runs`, `Index Reconciliation`, `Screen Runs`, `Screen Comparison`, `Provenance`, and — new, appended last — `Playbook Signals`. All ten shipped sections are present with no rename/removal; the Playbook Signals section lands strictly BELOW Provenance, additive only. A screenshot of the top of the page (Screen History calendar, Forward Returns touch table + baseline rows, the Run Screen/Top-up/Reconcile controls, and the start of the Briefing ranking table) shows these rendering exactly as the Era-B shipped baseline. Screenshot: `J-03-TC6-shipped-sections-intact.png`.

**Technique note (non-functional, for the record):** this `/desk` page is extremely tall (~37,000px with the Playbook section populated) and headless Chrome's viewport screenshot silently painted blank/black at any large `scrollTo`/`scrollIntoView` offset (confirmed reproducible at scrollY≈5,000 and beyond, and via `fullpage:true` capture, which also produced a truncated/stale image not reaching the tail sections) — this is a headless-Chrome rendering limitation on very tall pages, not a product defect. Worked around by temporarily setting `display:none` (via `eval`, never touching source) on the shipped `<section>` siblings above Playbook Signals for the duration of screenshot capture only, which collapses the document to a normal height so the target section renders in-viewport without any deep scroll. This is a capture-only aid; every functional interaction (typing, clicking, reading server responses) was exercised against the real, fully-rendered DOM.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01, J-02, and J-10 were intentionally excluded from this dispatch's scope (J-10 is verified separately via its stored golden replay script per the lean-mode dispatch instructions; J-01/J-02 are backend-only journeys with no browser-verification requirement of their own).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (confirmed alive via `GET /health` → `{"status":"ok"}` both before and after the run)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), attached to the pre-launched isolated headless instance on CDP port 9222
- **Test Date:** 2026-08-10
- **Evidence directory:** `reports/qa/goal-playbook-iter-3-evidence/`
