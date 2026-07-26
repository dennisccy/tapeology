# Phase goal-desk-iter-4 — User-Visible Changes

**Phase:** goal-desk-iter-4
**Date:** 2026-07-25
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Open a new third page, **`/desk`**, via the "Desk" link that now appears in the top navigation
  bar on every page — this is the operator's daily briefing, previously reachable only by scanning
  `/structure` one symbol at a time.
- Click **"Run Screen"** on `/desk` to compute today's ranked screen over the registered universe,
  watch it progress live ("N / M members" with a pulsing indicator and the symbol currently being
  processed), and cancel it mid-run.
- Click **"Top-up"** on `/desk` — the first-ever on-screen control for the bar-fetching job that,
  until this iteration, only had a command-line/API trigger — with the same live progress ("N / M
  pairs", the last symbol/timeframe/outcome) and a cancel control.
- Once a screen has run, read a ranked briefing table: each symbol's side (support/resistance),
  band class ("Class A/B/C" with a "nearest same-class band" caption), distance in bps, band
  score, a badge per bar timeframe the symbol actually has coverage for, and a tick-evidence badge
  where applicable — all in the screen's own ranked row order.
- See exactly which universe members were screened but not ranked, split into two honestly labeled
  groups — "Skipped — no bars (N)" and "Skipped — no basis session (N)" — each shown only when it
  has members.
- See a screen's full paper trail in one place: the universe snapshot id + date, the `as_of`
  timestamp, the app's config fingerprint, and "Window last requested" bar freshness — enough to
  tell any two screens apart or confirm they're identical.
- See a read-only history list of every past screen run (date, row/skipped counts, provenance
  summary) directly on `/desk`, without leaving the page.

---

## What Changed in the Visible UI

- The top navigation bar — present on every page (Cockpit, Structure, and now Desk) — gained a
  third link, "Desk," rendered automatically from the backend's route list; Cockpit's and
  Structure's own page content is unchanged.
- A new page renders at `/desk`. Before any screen has ever been computed, it shows the exact text
  **"Desk screen not computed yet."** with an enabled "Run Screen" button and an enabled "Top-up"
  button.
- Once a screen exists, `/desk` shows four stacked panels in order — Provenance, Briefing (ranked
  rows), Skipped Members, Screen History — followed by a footer "Run Screen / Top-up" control
  panel, matching the dense single-column layout already used on `/structure`.
- Clicking "Run Screen" or "Top-up" disables that button for the duration of the run (it relabels
  to "Computing…" / "Topping up…") and shows a live progress line with a small pulsing dot; a
  "Cancel" button appears alongside it while running.
- If "Run Screen" is clicked before any universe has ever been registered, `/desk` now shows an
  inline red error message under the button instead of silently starting a job.
- If the backend becomes unreachable while a compute's progress is being polled, `/desk` keeps
  showing the last progress line it knew about rather than blanking the panel or fabricating a
  status.

---

## What Old Behavior Changed

- **`POST /research/desk/screen/compute`** (the screen-compute trigger endpoint, already reachable
  outside the UI since a prior iteration): previously, calling it with no universe snapshot
  registered would start a job and persist a permanent, empty screen snapshot. It now refuses
  immediately (HTTP 4xx, naming the missing universe) and persists nothing. This changes behavior
  for any existing caller of that endpoint, not only the new "Run Screen" button.
- The job snapshot served by **`GET`/`POST /research/desk/screen/compute`** (an endpoint that
  already existed and was already callable outside the UI) now carries two additional fields,
  `reused` and `screen_id`, alongside its prior fields — purely additive, no existing field's shape
  changed.

---

## Not Visible Yet

- The new `reused`/`screen_id` values on the screen-compute snapshot — which would tell an
  operator whether a "Run Screen" click found an already-recorded screen versus created a brand
  new one — are returned by the API and present in the frontend's type definitions, but `/desk`
  does not display either value anywhere on screen this iteration.
- Each briefing row's underlying `price_low`/`price_high` band-boundary prices are present in the
  API response and the frontend's type contract, but the `/desk` table does not render them — only
  the distance-in-bps and band-score values are shown.
- The corrupted-file integrity guard added to universe-snapshot recording (refuses to silently
  overwrite a damaged file on disk) has no UI trigger point at all: registering/fetching a universe
  remains a CLI/API-only action this iteration — there is no "Fetch Universe" button anywhere in
  the product.
- Clicking into a past entry in the Screen History list to see that day's own rows, and jumping
  from a ranked symbol straight to its chart on `/structure`, are both explicitly deferred to the
  next iteration — this iteration's history list shows date, counts, and provenance only, with no
  click interaction.
