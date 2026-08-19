# Demo Script — goal-rapid-microscope-iter-15

**Mode:** record
**Date:** 2026-08-19
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page is the command center for research tracking. All sections start collapsed — click to expand them.
- **Action:** Navigate to /desk
- **Point out:** Four collapsed section headers: Microscope Readiness, Scout Ledger, Walk-Forward, and Validation Vault.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-15/step-01.png

### Step 02 — Expand Microscope Readiness to see the Sealed Tranche block  [NEW]

- **Narration:** The Microscope Readiness section now shows a new Sealed Tranche block. It tracks recordings deliberately held back from research as aggregate counts only — never revealing which specific shards are withheld.
- **Action:** Click the "Microscope Readiness" button
- **Point out:** A new block titled "Sealed Tranche (Aggregate Only)" appears below the existing Corpus Totals table. It shows three counts: Sealed shard count, Sealed symbol-days, and Joinable corpus — withheld (excluded), all reading zero because nothing has been sealed yet. The empty state "No sealed shards recorded." confirms the honest state.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-15/step-02.png

### Step 03 — Expand Walk-Forward to see recorded sequences

- **Narration:** Walk-Forward sequences represent candidate ideas tested forward through time rather than on data they were fitted to. Expanding a sequence's detail no longer triggers console errors — a React hydration issue was fixed this iteration.
- **Action:** Click the "Walk-Forward" button
- **Point out:** The Walk-Forward section expands showing a real recorded sequence. Notice the "Sequence verdict:" line with a detail toggle that can be opened without console errors.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-15/step-03.png

### Step 04 — Expand Scout Ledger to see the screening record  [NEW]

- **Narration:** Scout Ledger is the permanent record of every candidate idea screened, including killed ones — the denominator that stops results being cherry-picked. Each family now shows its family_root_id in the header (though the real ledger is empty today).
- **Action:** Click the "Scout Ledger" button
- **Point out:** Scout Ledger expands cleanly showing "No candidates ledgered." — the honest state, since nothing has been screened yet. The family-header format now includes (root family_root_id) for tracking lineage.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-15/step-04.png

### Step 05 — Expand Validation Vault to see the sealed data reserve

- **Narration:** The Validation Vault is sealed data reserved to test a finished idea against — it's deliberately read-only with no interactive controls, protecting its integrity.
- **Action:** Click the "Validation Vault" button
- **Point out:** Validation Vault expands to show "No shards recorded." and "No universes registered." — the honest empty state. The section has no buttons or editable fields, by design.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-15/step-05.png

### Step 06 — Navigate to Structure to confirm it's unaffected

- **Narration:** The Structure page shows the tradable map and comparison tools. This iteration's changes were confined to Desk — Structure continues working exactly as before.
- **Action:** Navigate to /structure
- **Point out:** The Tradable Map table is present with the comparison dropdown visible. No error banner appears.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-15/step-06.png

### Step 07 — Return to Cockpit and watch the live chart

- **Narration:** The Cockpit is the live trading watchlist with real-time tape and historical chart. This iteration had no changes here — the chart, tape, and quote live data remain unchanged.
- **Action:** Navigate to /
- **Point out:** The live chart renders with the ticker field ready. You can type SIM-BUYER to see simulated tape and candlesticks update live.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-15/step-07.png

### Step 08 — Type SIM-BUYER in the ticker field and watch

- **Narration:** Simulated mode lets you follow a mock buyer without real credentials. The chart and tape update live to show realistic order flow.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The chart shows candles and volume; the tape displays live orders; the Tape State shows "Buyer Control". This confirms the Cockpit's core surface is working.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-15/step-08.png

## Full tour (text only)

### Step 09 — Click Watch to start the live feed

- **Narration:** Clicking Watch connects to the live data stream and begins showing real-time (or simulated) order flow and pricing.
- **Action:** Click the "Watch" button
- **Point out:** The chart updates and the tape shows live events. Quote and Trade panels populate with current data.
