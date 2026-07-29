# Demo Script — goal-desk-iter-16

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page  [NEW]

- **Narration:** The Desk page opens on the most recently RECORDED screen snapshot. The Provenance panel at the top now names exactly which recording is on screen — its own snapshot id and the time it was recorded — followed by a note explaining that 'most recently recorded' is not the same thing as 'the latest screen date'.
- **Action:** Navigate to /desk
- **Point out:** Under Provenance, the first two rows are new this iteration: 'Snapshot id' and 'Recorded at'. Below the panel's rows, the note reads 'This is the most recently recorded screen (by recorded-at time), not necessarily the latest screen date — an earlier same-date recording can still exist and be opened from Screen History below.'
- **Screenshot:** reports/demo/goal-desk-iter-16/step-01.png

### Step 02 — Open the EARLIER of the two same-date recordings from Screen History  [NEW]

- **Narration:** The Screen History table lists every recorded snapshot and now carries a 'recorded' column. Two rows share the same trading date, 2026-07-27, but were recorded a day apart. Before this iteration the page looked those rows up by DATE, so clicking either one could only ever open the newer of the two — the earlier recording was listed but unreachable. Each row is now addressed by its own snapshot id, so clicking the earlier row opens that exact recording.
- **Action:** Click "tr[data-screen-id='screen-2026-07-27-936543601e75']"
- **Point out:** This frame is the Screen History table. The two 2026-07-27 rows show different 'recorded' values: 2026-07-27T21:42:14.636275Z and 2026-07-28T21:30:16.111871Z. After the click only the earlier row carries the selected highlight; the 'Viewing the recorded screen for 2026-07-27 — not the latest.' banner it raises sits at the top of the page, visible in the next frame.
- **Screenshot:** reports/demo/goal-desk-iter-16/step-02.png

### Step 03 — Provenance names the earlier recording by id and recorded-at time  [NEW]

- **Narration:** Scrolling back up to Provenance, the panel has swapped to the earlier recording's own identity. This is what makes two same-date snapshots tellable apart on screen: the date alone no longer identifies what you are reading.
- **Action:** Click "[data-testid='desk-provenance']"
- **Point out:** 'Snapshot id' now reads screen-2026-07-27-936543601e75 and 'Recorded at' reads 2026-07-27T21:42:14.636275Z, while 'Screen date' still reads 2026-07-27. The 'most recently recorded' note is gone — this is not the latest recording.
- **Screenshot:** reports/demo/goal-desk-iter-16/step-03.png

### Step 04 — Open the LATER same-date recording  [NEW]

- **Narration:** Now the sibling row — the same trading date, recorded a day later. It is a genuinely different snapshot: it was recorded after a coverage repair, so its rows carry different bar-coverage badges than the recording opened a moment ago.
- **Action:** Click "tr[data-screen-id='screen-2026-07-27-3ad3c57aa6ba']"
- **Point out:** This frame is again the Screen History table: the highlight has moved to the second 2026-07-27 row — the same date, a different recording. The Provenance panel it swapped in sits at the top of the page and is shown in the next frame.
- **Screenshot:** reports/demo/goal-desk-iter-16/step-04.png

### Step 05 — Provenance updates to the later recording's own identity  [NEW]

- **Narration:** Same trading date, different recording, different provenance. Every value shown here is read verbatim from the snapshot that is on screen — nothing is recomputed in the browser.
- **Action:** Click "[data-testid='desk-provenance']"
- **Point out:** 'Snapshot id' now reads screen-2026-07-27-3ad3c57aa6ba and 'Recorded at' reads 2026-07-28T21:30:16.111871Z — one day later than the recording shown in step 3, for the same 2026-07-27 screen date.
- **Screenshot:** reports/demo/goal-desk-iter-16/step-05.png

### Step 06 — Return to the most recently recorded snapshot  [NEW]

- **Narration:** The banner's 'Latest' button returns the page to the most recently recorded snapshot — by recorded-at time, not by screen date. The default-view note reappears to say so explicitly.
- **Action:** Click "[data-testid='desk-history-latest-button']"
- **Point out:** The banner disappears, the Provenance rows revert to the newest recording, and the note returns: 'This is the most recently recorded screen (by recorded-at time), not necessarily the latest screen date...'.
- **Screenshot:** reports/demo/goal-desk-iter-16/step-06.png

### Step 07 — A ledger discloses its own file-integrity error  [NEW]

- **Narration:** The Top-up Runs and Index Reconciliation ledgers used to read their store's verification errors and throw them away. They now disclose them the same way the screen and universe reads already did. This walkthrough runs against a scoped COPY of the ledger directories with one deliberately corrupted record file planted in each — the real store is never written to — so the disclosure is visible on screen instead of only in a test.
- **Action:** Click "[data-testid='desk-topup-runs-integrity-errors']"
- **Point out:** Under Top-up Runs, an amber line reads '1 file failed an integrity check and is excluded: topup-2026-07-28-audit0corrupt.json'. The Index Reconciliation section below carries the equivalent line for its own corrupted file, and both corrupted records stay excluded from their tables — named, never repaired, never deleted.
- **Screenshot:** reports/demo/goal-desk-iter-16/step-07.png
