# Phase goal-fast_wall-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-fast_wall-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- **Do not use the standard `http://localhost:3301` instance for this check.** This phase adds a
  real "Compute edge report" button that starts a genuine background job. On the standard instance
  that job would sweep the project's full real corpus (18 datasets) — slow and unnecessary just to
  confirm the feature works. Use a small, disposable SCOPED instance instead:

  **Terminal 1** (from the repo root, `/home/dennis-chan/Git/tapeology`):
  ```bash
  SCOPED_DIR=$(mktemp -d)
  mkdir -p "$SCOPED_DIR/bars"
  cp -r apps/backend/tests/fixtures/datasets_j03 "$SCOPED_DIR/datasets"
  cd apps/backend && source .venv/bin/activate
  TAPEOLOGY_DATASET_DIR="$SCOPED_DIR/datasets" TAPEOLOGY_BAR_DIR="$SCOPED_DIR/bars" \
  TAPEOLOGY_JOURNAL_DB="$SCOPED_DIR/journal.db" TAPEOLOGY_EDGE_REPORT_CACHE_DB="$SCOPED_DIR/edge_report_cache.db" \
  uvicorn main:app --host 0.0.0.0 --port 8391
  ```

  **Terminal 2:**
  ```bash
  cd apps/frontend && NEXT_PUBLIC_API_URL=http://localhost:8391 npx next dev -p 3391
  ```
- No login is required (this app has no authentication).
- Wait for both terminals to print their "ready"/"ready on" lines before starting Step 1.

---

## Verification Steps

1. Open `http://localhost:3391/structure` in your browser
   - **Expect:** The page loads with the heading "Structure" visible; no blank page or error screen.

2. Scroll down past "Tradable Map" and "Case Studies" to the **"Edge Report"** panel
   - **Expect:** An amber box reading "Edge report not computed yet." with a button labeled
     **"Compute edge report"** underneath it.

3. Click the **"Compute edge report"** button
   - **Expect:** The button immediately relabels to **"Computing…"** and greys out (you can no
     longer click it); a small line appears below it reading something like "0 / 0 backtests".

4. Wait up to 90 seconds without clicking anything else
   - **Expect:** The panel changes on its own — either a small report section appears (with a short
     amber disclaimer line at the top), or the panel now reads **"No edge-report cells yet."** Both
     outcomes are correct — on this test dataset, the second one is expected and typically appears in
     under a second.
   - **What "broken" looks like:** the button stays stuck on "Computing…" for the full 90 seconds
     with no change, or the page shows a raw error / crash instead of either outcome above.

5. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The exact same finished view from Step 4 reappears immediately. It does **not**
     reset back to the "Compute edge report" button — this proves the result was actually saved, not
     just held in the browser tab.

6. Scroll back to the top and slowly scroll all the way through the rest of the page
   - **Expect:** The "Tradable Map", "Case Studies", "Registry", and "Comparison" sections all still
     show their normal content (or their own pre-existing empty/unavailable messages) — nothing looks
     broken, missing, or different because of this change.

---

## What "Working Correctly" Looks Like

- Clicking "Compute edge report" produces a visible, immediate reaction (button greys out, a
  progress line appears) and, within 90 seconds, a real result appears in the same spot — never a
  frozen page or a silent failure.
- Refreshing the page after the result appears keeps showing that same result — the work was not
  lost by reloading.
- Every other part of the `/structure` page looks exactly as it did before this phase.

## Common Issues

- **Blank page / connection refused at `localhost:3391`**: the scoped frontend (Terminal 2) is not
  running yet, or is still starting up — wait a few seconds and reload.
- **Button click does nothing at all**: check that the scoped backend (Terminal 1) is running at
  `http://localhost:8391` — try `curl http://localhost:8391/research/edge-report` in a third
  terminal; it should return JSON, not a connection error.
- **The page seems to hang for minutes with high CPU usage**: stop it (Ctrl+C both terminals) and
  confirm you are on `localhost:3391`, not `localhost:3301` — the standard instance's much larger
  real dataset corpus is not meant for this quick check.
- **Panel never leaves "Computing…"**: this would be the one genuine regression to flag — the phase
  spec guarantees the job reaches an end state within 90 seconds on this small test dataset.
