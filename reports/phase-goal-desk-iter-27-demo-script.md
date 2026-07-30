# Demo Script — goal-desk-iter-27

**Mode:** record
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the desk screen

- **Narration:** The desk screen shows your ranked briefing at the top, and below it sits a record of every bar top-up run you've executed. Let's look at how the system captures exactly what it asked from the vendor.
- **Action:** Navigate to /desk
- **Point out:** The page loads with the desk briefing table visible. Scroll down to find the Top-up Runs section showing the history of all top-up executions.
- **Screenshot:** reports/demo/goal-desk-iter-27/step-01.png

### Step 02 — See the top-up run summary  [NEW]

- **Narration:** Each top-up run is recorded with four outcome counts: how many bars were reused from the frozen store, how many the system fetched fresh, how many the vendor had unchanged since we last asked, and how many pairs failed to fetch.
- **Action:** Expect {'testid': 'desk-topup-run-latest-counts'}
- **Point out:** The Top-up Runs section shows a summary line: '0 reused · 6 fetched · 2 unchanged · 4 failed'. These four numbers tell you the exact outcome of the run — which pairs the system could reuse, which it had to fetch, which came back unchanged, and which failed.
- **Screenshot:** reports/demo/goal-desk-iter-27/step-02.png

### Step 03 — Understand what the system asked for  [NEW]

- **Narration:** For each pair, the system chose a window to ask from the vendor: either a tail window (only the bars since the frozen store's last update) or the full lookback window (all bars from the configured lookback start to today). This line shows you which strategy was used for how many pairs.
- **Action:** Expect {'testid': 'desk-topup-run-latest-window-basis'}
- **Point out:** Below the outcome counts, you see: '2 pairs asked for a tail window · 10 pairs asked for the full lookback window'. This means for just 2 pairs, the system could ask for only the new bars. For the other 10, it had to ask for the full span.
- **Screenshot:** reports/demo/goal-desk-iter-27/step-03.png

### Step 04 — Examine a failed pair's requested window  [NEW]

- **Narration:** When a pair fails, the system records exactly what window it asked for. This lets you see whether the vendor was asked for a narrow tail (from the last known bar forward) or the full lookback (from your configured start date forward).
- **Action:** Expect {'testid': 'desk-topup-run-failed-pair-requested-window'}
- **Point out:** In the Failed pairs table, look at one of the ZZZINVALIDXYZ rows. You can see a column showing the exact requested window: for example, 'requested 2024-07-30 → 2026-07-30'. This is the window the system asked the vendor to fill.
- **Screenshot:** reports/demo/goal-desk-iter-27/step-04.png

### Step 05 — Review the full top-up record  [NEW]

- **Narration:** The top-up record is append-only. Every time you run a top-up, it creates a new entry with its own counts and window disclosures. Nothing is changed or recomputed in place — you always see an honest record of what the system asked the vendor to provide.
- **Action:** Expect {'testid': 'desk-topup-run-latest-counts'}
- **Point out:** The Top-up Runs section lists this and any prior runs you've executed. Each row shows the date, the four outcome counts, the window basis split, and for any failed pairs, exactly what window was requested. The entire briefing above remains unchanged — it is always pinned to a specific universe snapshot date.
- **Screenshot:** reports/demo/goal-desk-iter-27/step-05.png
