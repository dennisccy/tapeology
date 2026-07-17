# Phase goal-fast_wall-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-fast_wall-iter-6
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start: what to expect

This phase changes **nothing about how any page looks.** If you compare `/structure` side-by-side
with the last check (iter-5), you should see zero differences anywhere — that is correct, not a sign
something failed. What actually changed is entirely invisible in the browser: the "Case Studies"
panel's underlying scan now saves its result to disk, so it survives a backend restart instead of
re-running from scratch every time the server restarts. On the small test dataset used below, that
scan was already instant either way, so even the speed difference will not be visible here — only on
the real, populated corpus, after a real restart, would anyone actually notice a difference (minutes
of waiting avoided).

---

## Prerequisites

- **Do not use the standard `http://localhost:3301` instance for this check.** If its backend has
  never scanned Case Studies for the current settings, simply loading `/structure` there can trigger
  a genuine multi-minute scan over the real 18-dataset corpus — the exact slow-load hazard this "Fast
  Wall" work exists to fix. Use a small, disposable SCOPED instance instead:

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
  TAPEOLOGY_SETUPS_CACHE_DB="$SCOPED_DIR/setups_scan_cache.db" \
  uvicorn main:app --host 0.0.0.0 --port 8391
  ```
  (The last env var, `TAPEOLOGY_SETUPS_CACHE_DB`, is new this phase — it keeps this iteration's new
  cache file scoped to this disposable directory too.)

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

2. Wait 10 seconds without clicking anything, then look at every panel on the page
   - **Expect:** No panel is stuck showing a loading spinner or placeholder — every section
     (Tradable Map, Case Studies, Edge Report, Registry, Comparison) has finished loading into its
     normal or honest-empty state.

3. Scroll down to the **"Case Studies"** panel
   - **Expect:** It reads **"No band-touch events scanned yet."** — this is the correct, expected
     message for this test dataset, not a bug.

4. Scroll down to the **"Edge Report"** panel — do **not** click its button
   - **Expect:** An amber box reads "Edge report not computed yet." with a button labeled "Compute
     edge report" underneath — identical to every prior check.

5. Keep scrolling to the **"Registry"** panel
   - **Expect:** A "Champion" block appears, followed by three strategy cards. Nothing here looks
     different from before.

6. Keep scrolling to the **"Comparison"** panel at the bottom
   - **Expect:** A dataset dropdown is visible with at least one option in it ("Choose a dataset…"
     plus one entry). Nothing here looks different from before either.

7. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The exact same content from Steps 2–6 reappears immediately — no crash, no
     different text, no stuck loading spinner.

---

## What "Working Correctly" Looks Like

- Every part of `/structure` looks exactly as it did in the last check — no new buttons, no new
  labels, no layout changes, no stuck loading spinners.
- The "Case Studies" panel shows its honest "No band-touch events scanned yet." message promptly, not
  after a long wait.
- Refreshing the page never resets anything to a broken or different state.

## Common Issues

- **Blank page / connection refused at `localhost:3391`**: the scoped frontend (Terminal 2) is not
  running yet, or is still starting up — wait a few seconds and reload.
- **A panel stays stuck loading for more than 10 seconds**: this would be the one genuine regression
  to flag for this phase — every section on this small test dataset should finish loading almost
  immediately.
- **You notice zero visual differences anywhere**: that is the expected, correct result for this
  phase — see "Before you start" above. Do not treat "looks identical to before" as a failure.
- **The standard `localhost:3301` instance seems to hang with high CPU when you load `/structure`**:
  stop it and use the scoped instance above instead — this can happen if that instance's backend has
  never scanned Case Studies before for the current settings.
