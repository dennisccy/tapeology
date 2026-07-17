# Phase goal-fast_wall-iter-5 — What to Click (Operator Verification Guide)

**Phase:** goal-fast_wall-iter-5
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start: what to expect

This phase changes **nothing about how the page looks**. If you compare it side-by-side with the
last check, you should see zero differences — that is correct, not a sign something failed. What
actually changed is invisible: the "Compute edge report" button's live browser behavior was finally
confirmed with real screenshots (it was built earlier but never actually watched running in a
browser), and re-triggering a killed compute now skips work it already finished. None of that shows
up as a new button, new label, or new page.

---

## Prerequisites

- **Do not use the standard `http://localhost:3301` instance for the compute-button steps below
  (Steps 1–5).** Clicking "Compute edge report" there sweeps the project's full real corpus (18
  datasets) — slow and unnecessary just to confirm the feature works. Use a small, disposable
  SCOPED instance instead:

  **Terminal 1** (from the repo root, `/home/dennis-chan/Git/tapeology`):
  ```bash
  SCOPED_DIR=$(mktemp -d)
  mkdir -p "$SCOPED_DIR/bars"
  cp -r apps/backend/tests/fixtures/datasets_j03 "$SCOPED_DIR/datasets"
  cd apps/backend && source .venv/bin/activate
  TAPEOLOGY_DATASET_DIR="$SCOPED_DIR/datasets" TAPEOLOGY_BAR_DIR="$SCOPED_DIR/bars" \
  TAPEOLOGY_JOURNAL_DB="$SCOPED_DIR/journal.db" \
  TAPEOLOGY_EDGE_REPORT_CACHE_DB="$SCOPED_DIR/edge_report_cache.db" \
  TAPEOLOGY_EDGE_SWEEP_CACHE_DB="$SCOPED_DIR/edge_report_backtests.db" \
  uvicorn main:app --host 0.0.0.0 --port 8391
  ```
  (The last env var, `TAPEOLOGY_EDGE_SWEEP_CACHE_DB`, is new this phase — it keeps the new
  resumability cache scoped to this disposable directory too.)

  **Terminal 2:**
  ```bash
  cd apps/frontend && NEXT_PUBLIC_API_URL=http://localhost:8391 npx next dev -p 3391
  ```
- No login is required (this app has no authentication).
- Wait for both terminals to print their "ready"/"ready on" lines before starting Step 1.

---

## Verification Steps

1. Open `http://localhost:3391/structure` in your browser
   - **Expect:** The page loads with the heading "Structure" visible; no blank page or error
     screen. Scroll down past "Tradable Map" and "Case Studies" to the **"Edge Report"** panel — an
     amber box reads "Edge report not computed yet." with a button labeled **"Compute edge
     report"** underneath it.

2. Click the **"Compute edge report"** button
   - **Expect:** The button immediately relabels to **"Computing…"** and greys out (you can no
     longer click it); a small line appears below it reading "0 / 0 backtests".

3. Wait up to 90 seconds without clicking anything else
   - **Expect:** The panel changes on its own to read **"No edge-report cells yet."** — this is the
     expected, correct outcome for this test dataset and typically appears in under a second. (A
     small report table appearing instead is also correct, just less likely on this test data.)
   - **What "broken" looks like:** the button stays stuck on "Computing…" for the full 90 seconds
     with no change, or the page shows a raw error / crash instead.

4. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The exact same "No edge-report cells yet." view from Step 3 reappears immediately.
     It does **not** reset back to the "Compute edge report" button — this proves the result was
     actually saved, not just held in the browser tab.

5. Scroll back to the top and slowly scroll all the way through the rest of the page
   - **Expect:** The "Tradable Map", "Case Studies", "Fetch from Yahoo Finance", "Registry", and
     "Comparison" sections all still show their normal content — nothing looks broken, missing, or
     different because of this change.

6. Open a new tab and go to `http://localhost:3301/structure` (the normal instance) — **do not
   click "Compute edge report" here**
   - **Expect:** The page loads normally too, with the same six section headings in the same order
     as Step 5. This just confirms the everyday instance wasn't broken by this phase either.

---

## What "Working Correctly" Looks Like

- Clicking "Compute edge report" produces a visible, immediate reaction (button greys out, a
  progress line appears) and, within 90 seconds, a real result appears in the same spot — never a
  frozen page or a silent failure.
- Refreshing the page after the result appears keeps showing that same result — the work was not
  lost by reloading.
- Every part of the `/structure` page — on both the scoped test instance and the everyday instance
  — looks exactly as it did before this phase. No new buttons, no new labels, no layout changes.

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
  guarantees the job reaches an end state within 90 seconds on this small test dataset.
- **You notice zero visual differences anywhere**: that is the expected, correct result for this
  phase — nothing in the frontend changed. Do not treat "looks identical to before" as a failure.
