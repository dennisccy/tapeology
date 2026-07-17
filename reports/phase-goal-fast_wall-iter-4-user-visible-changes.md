# Phase goal-fast_wall-iter-4 — User-Visible Changes

**Phase:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now click a **"Compute edge report"** button on the `/structure` page's Edge Report
  section to start the first-ever real edge-report compute directly from the browser — previously
  the only way to warm this up was an out-of-band script/REPL call with no in-page path forward.
- Users can now watch the compute job's progress live on the page — a line showing
  `{backtests done} / {backtests total} backtests` (with a "(N from cache)" annotation once a
  future iteration adds per-pair caching) updates every ~700ms while the job runs, with no page
  reload.
- Users can now see the finished report render automatically in place the instant the job
  completes — the same report table/cells `/structure` already showed for a pre-warmed report,
  now actually reachable from a cold page without leaving it.
- Users can now see an honest, verbatim failure message in place if the compute job fails partway
  (e.g., a corrupted data file) — a specific red error line, not a generic "something went wrong."
- Users can now retry a failed compute by clicking the same button, which relabels itself
  "Retry compute" and re-enables once a job reaches the failed state.
- Users can now reload or land on `/structure` while a compute is mid-flight, or after it already
  finished or failed, and immediately see the matching state (running progress / finished report /
  failed error) without needing to click anything first — the page resumes rather than resetting
  to idle.
- Operators can now also run the SAME compute unattended from a terminal —
  `python -m app.research.edge_report_compute [--workers N] [--force] [--out report.json]` — which
  prints its own progress and publishes to the identical shared cache the button reads from. This
  is a command-line capability, not a browser UI element; there is no button or page that exposes
  it.

---

## What Changed in the Visible UI

- The `/structure` page's Edge Report section's "not computed" panel (`edge-report-not-computed`)
  now shows a **"Compute edge report"** button directly beneath the existing headline/detail text.
  The button's label changes with the job's state: **"Compute edge report"** (idle, enabled) →
  **"Computing…"** (running, disabled) → **"Retry compute"** (failed, re-enabled).
- While a job is running, a new progress line appears inside the same panel, reading
  `{backtests_done} / {backtests_total} backtests`.
- If the job fails, a new red line appears inside the same panel showing the backend's exact error
  string (e.g., an integrity-verification failure message) verbatim.
- If the button's own click (the POST that starts the job) fails — for example the backend is
  unreachable at click time — a separate red line appears showing that failure (distinct from a
  job that started and then failed on the server).
- No new page was added, no new panel, and no navigation entry changed — the entire visible change
  is confined to the existing not-computed panel on the existing Edge Report section.

---

## What Old Behavior Changed

None. This iteration is purely additive:
- The static "Edge report not computed yet." headline and detail text render byte-for-byte the
  same as before on a page that has never had a compute run — only the new button/progress/error
  elements are added beneath it.
- The already-existing finished-report display (the report table, cells, and surviving-strategy
  section) is unchanged — this iteration adds a new way to *reach* that display, not a new way of
  *showing* it.
- No previously-working `/structure` flow (Tradable Map, Case Studies, Registry, Comparison
  sections) had its rendering touched.

---

## Not Visible Yet

- **Cancelling a running compute has no button.** The backend route
  (`POST /research/edge-report/compute/cancel`) is implemented and tested, and the frontend
  function `cancelEdgeReportCompute()` exists in `lib/api.ts`, but no UI control calls it — an
  operator cannot stop an in-flight compute from the browser this iteration.
- **The "(N from cache)" progress annotation will never actually appear yet.** The field exists in
  the progress line's code path, but there is no per-pair sub-cache until a future iteration (goal
  dependency order calls it J-05), so `backtests_from_cache` is always `0` and the annotation never
  renders in practice.
- **Forcing a fresh recompute over an already-warm result has no UI control.** The backend route
  and the CLI's `--force` flag both support it, but the browser button always sends `force: false`
  — there is no "recompute anyway" option on the page.
- **This iteration's actual browser click-through was not captured with a screenshot.** The
  automated browser tool could not start in the developer's session, so the button/progress/failed
  states above were verified via direct HTTP calls against a real running backend, a strict
  TypeScript build, and a server-rendered HTML check — not an actual visual click-through. The
  underlying behavior is documented as strongly evidenced but not yet visually confirmed; this is a
  verification gap to close, not a known product gap.
