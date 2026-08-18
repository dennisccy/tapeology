# Phase goal-rapid-microscope-iter-7 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-7
**Date:** 2026-08-18
**Written by:** ui-impact-analyst

---

**Reading this map:** this iteration's diff touches zero frontend files (`git status` confirms
exactly 8 changed files, all under `apps/backend/`: 6 source + 2 test — 0 `.tsx`/`.ts`/`.css`).
Every row below is a **pre-existing, unmodified surface** the browser-QA lane must re-verify only
because `Frontend Present: yes` forces the browser lane to dispatch — not because this iteration
changed any of them. There is no new UI surface to map; inventing one would misrepresent the diff.
Two groups of rows exist for two different reasons:

1. **J-01's Microscope Readiness section** — this iteration's J-06 step 1 work modifies
   `apps/backend/app/research/datasets.py`, the exact module the readiness endpoint's data flows
   through (row serialization/deserialization). No new field is served and no manifest shape changed
   for any existing call site, so the section must render byte-identically to before — this is the
   narrowest, highest-stakes regression check in this iteration's browser pass.
2. **J-10's kept-product sentinel** — `journey-scripts/J-10.json`'s 13-step walk (cockpit →
   `/structure` → several `/desk` sections), reused byte-unmodified this iteration. The rows below
   decompose its 13 steps by surface. None of the code these steps exercise (cockpit tape rendering,
   `/structure`'s bar/level engine, the Playbook/Referee sections) is anywhere in this iteration's
   diff — the Alpaca trade/quote provider changes are upstream of tick-dataset *recording* only, a
   different pipeline from the Yahoo/BarStore path `/structure` reads and from the already-recorded
   data the Playbook/Referee sections read.

J-02, J-03, and J-04 (the other required-still-passing journeys) have **no dedicated UI element of
their own** — independently confirmed by reading `apps/frontend/app/desk/page.tsx` directly (not
just trusting the prior iteration's report): the page's `DeskCollapsibleSection` type lists exactly
10 sections (`topupRuns`, `indexReconciliation`, `screenRuns`, `screenComparison`, `provenance`,
`playbookEvidence`, `refereeRegistry`, `refereeAdjudications`, `refereeRuns`, `microReadiness`) —
no `scoutLedger`, `walkforward`, or `vault` section exists in the current build. That UI is J-08
scope (`journey-history.json`: J-08 status `failing`, unbuilt). **Note:** this iteration's own plan
(`runs/goal-rapid-microscope-iter-7/plan.md`, Key Test Scenarios, TC-12) and phase spec name "the
Scout Ledger section (J-04) on `/desk`" as something to re-verify — that section does not exist in
the shipped product; the row below (whole-page load) is the correct substitute, matching how the
iteration-6 map handled the same absence for J-02/J-03/J-04.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Microscope Readiness section (`data-testid="micro-readiness-section"`, collapsible id `microReadiness`) | Regression check (unmodified this iteration) | This iteration's J-06 step 1 diff touches `datasets.py`'s row/manifest serialization — the exact code this section's data flows through — but adds no new served field and stamps `schema_basis`/`quote_size_unit` only when a caller supplies them (no caller does yet), so the endpoint and section must render byte-identically to before | Navigate to `/desk`, click the section header `data-testid="desk-section-expand-microReadiness"` to expand it, and verify: (1) the "Corpus Totals" table (`data-testid="micro-readiness-totals-table"`) shows "Distinct symbol-days" = **1** and "Distinct datasets" = **2** — this store-scoped QA rig seeds exactly 2 committed fixture datasets (`tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json`, `.../d9f9dbe04fb24a7caccc53f0c6805412.json`), never the real store's 12/18, and asserting those larger numbers against this rig is what made iteration 6's equivalent check fail spuriously (`docs/handoffs/goal-rapid-microscope-iter-6-audit.md` finding E3) — do not repeat that; (2) the "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"`) lists exactly **2** rows (`data-testid="micro-readiness-shard-rows"`), both with Symbol = `PG` and Session date = `2026-06-09`, both rows' Split provenance column = `hand_assigned` and Exposure state column = `exploratory`; (3) the shard table still has exactly 12 columns (Symbol, Session date, Feed, Window (ET), Trades, Quotes, Bytes, Coverage gaps, Fallback frac, Checksum, Split provenance, Exposure state) — no new column for `conditions`/`exchange`/`tape`/`trade_id`/`schema_basis`/`quote_size_unit`, confirming J-06 step 1's new fields are not surfaced in the UI yet |
| `/desk` | Whole-page load across all 10 sections; confirms no "Scout Ledger" section exists (J-02/J-03/J-04) | Regression check (unmodified this iteration) | J-02 ("micro observer"), J-03 ("structure × flow join"), and J-04 ("Scout and the ledger") remain backend/CLI/endpoint-only journeys with no browser element of their own; this iteration's plan/spec name a "Scout Ledger section" that does not exist in the current build (confirmed via source: `DeskCollapsibleSection` lists 10 sections, none named `scoutLedger`) | Navigate to `/desk`, verify the "Playbook Signals" panel heading renders, scroll through all 10 sections top to bottom confirming none is blank/broken and no error banner appears anywhere, and confirm the browser console shows no unhandled exception |
| `/` (cockpit) | Ticker watch panel | Regression check (unmodified this iteration; J-10 steps 1–3) | Part of J-10's 13-step kept-product sentinel (`journey-scripts/J-10.json`, byte-unmodified); this iteration's Alpaca provider changes touch only historical tick-dataset *recording*, a different code path from the cockpit's live-tape rendering | Navigate to `/`, verify the text "No ticker watched" appears, type `SIM-BUYER` into the field labeled "Ticker", click the "Watch" button, and verify the text "Buyer Control" appears |
| `/structure` | Tradable Map load | Regression check (unmodified this iteration; J-10 steps 4–7) | Same J-10 sentinel; `/structure` reads the Yahoo/BarStore bar pipeline, entirely separate from the Alpaca trade/quote provider fields this iteration adds | Navigate to `/structure`, verify the text "Tradable Map" appears, type `AAPL` into the field labeled "Structure symbol", type `2026-06-22 17:00:00` into the field with `data-testid="structure-as-of-input"`, click the element with `data-testid="structure-load-button"`, and verify the text "300.11–302.2" appears |
| `/desk` | Playbook Evidence section | Regression check (unmodified this iteration; J-10 steps 8–10) | Same J-10 sentinel; reads already-recorded playbook signal data, unrelated to this iteration's tick/dataset diff | Navigate to `/desk`, verify the "Playbook Signals" heading appears, click `data-testid="desk-section-expand-playbookEvidence"`, verify the text "Built from signature:" appears, type `2026-06-22` into the field with `data-testid="desk-playbook-date-input"`, and verify the text "recorded signals, none hidden" appears |
| `/desk` | Referee Registry section | Regression check (unmodified this iteration; J-10 step 11) | Same J-10 sentinel | Click `data-testid="desk-section-expand-refereeRegistry"` and verify the text "config fingerprint 08e471b10130e1e2" appears — the same frozen fingerprint this iteration's own backend check (TC-4/TC-10, `Config().config_fingerprint()`) independently re-verifies |
| `/desk` | Referee Adjudications section + Referee Runs section | Regression check (unmodified this iteration; J-10 steps 12–13) | Same J-10 sentinel | Click `data-testid="desk-section-expand-refereeAdjudications"` and verify the text "No hypotheses registered" appears; click `data-testid="desk-section-expand-refereeRuns"` and verify the text "No evaluation runs recorded yet." appears |

<!-- Change Type is "Regression check" throughout — no row above reflects a code change; every row exists because Frontend Present: yes forces the browser lane to genuinely exercise the kept product this iteration. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/providers/adapters/base.py` — `RawTrade` gains optional `conditions`,
  `exchange`, `tape`, `trade_id`; `RawQuote` gains optional `conditions`, `tape`, `bid_exchange`,
  `ask_exchange` — no UI surface affected (no endpoint serves these values).
- `apps/backend/app/providers/base.py` — `TradeEvent`/`QuoteEvent` gain the matching optional
  fields — no UI surface affected.
- `apps/backend/app/providers/historical.py` — both construction sites thread the new fields
  through when present — no UI surface affected.
- `apps/backend/app/providers/adapters/alpaca.py` — two new helpers (`_venue_str`,
  `_conditions_list`) populate the new fields from the real Alpaca SDK response at the two
  historical construction sites (and, trivially, the live-stream site) — no UI surface affected;
  this code path is never invoked from a UI-triggered request.
- `apps/backend/app/research/datasets.py` — `_event_to_row`/`_row_to_event` carry the 8 new fields
  present-only; `record()`/`record_from_source()` gain optional `schema_basis`/`quote_size_unit`
  keyword parameters — no UI surface affected; no existing call site supplies them, so the
  Microscope Readiness endpoint's served shape is unchanged (see the regression row above).
- `apps/backend/app/research/walkforward.py` — new `run_tick_family_fold_request()` function plus a
  new CLI `--family tick_legacy` flag on `main()` — operator/CLI-only, no UI surface affected;
  `POST /walkforward/compute`'s route-level family parameter is explicitly deferred (no UI/MCP
  consumer needs it yet, per the plan's assumption ledger).
- `apps/backend/tests/test_datasets.py`, `apps/backend/tests/test_walkforward.py` — test files, no
  UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 8 (6 source files + 2 test files)
- **Pre-existing surfaces requiring regression re-verification this iteration:** 7 rows above
  (Microscope Readiness section, `/desk` whole-page load, cockpit ticker watch, `/structure`
  Tradable Map, Playbook Evidence section, Referee Registry section, Referee Adjudications +
  Referee Runs sections)
