# goal-i_will_be_super_rich_with_my_loved_ones-iter-18 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built

- **Studies nav entry enabled** (`components/NavBar.tsx`): the pre-registered disabled `/studies` item
  flips to enabled now its page exists. This is the ONLY cockpit-adjacent pixel change (the J-68 sentinel
  allowance) — the cockpit grid itself is untouched.
- **New `/studies` page** (`app/studies/page.tsx`): create, monitor, cancel, re-run, and read
  deterministic replay studies. The page does NO business logic — it POSTs the create form, polls a
  running job's status (queued → running → done), and renders the runner's persisted results VERBATIM
  (display rounding only). Loading / empty / error states all handled. Two-column on wide (form + job
  list left, results right); single column on narrow.
- **`StudyCreateForm`**: source picker (reference-window quick-pick labeled as the committed PG SIP
  fixture / seeded sim scenario / arbitrary symbol + past window), setup × direction, and a level input
  shown ONLY for the two level setups with the hindsight warning. The arbitrary-window source reuses the
  existing `SymbolSearch`, the `dd-MM-yyyy` custom date input + the shared row-12 local-window resolver,
  and US-session quick-picks — no second timezone path.
- **`StudyList`**: every study most-recent-first with its status badge + progress and a Cancel control
  while queued/running. Status colors stay within the existing semantics — slate (queued/cancelled),
  amber (running), rose (failed), and a NEUTRAL slate for `done` (never a green "success" that reads as
  an edge). Selecting a row opens its results.
- **`StudyResultsView`**: the setup occurrence distribution rendered SIDE-BY-SIDE with the seeded
  random-arm-time null baseline, per-horizon ternary outcomes (`+1R` / `−1R` / `neither` + a SEPARATE
  truncated chip, never folded in), the occurrence rows (arm time, verdict reached, R basis), the
  honesty stamps (feed + the FULL config fingerprint + the recorded seed), the hindsight label +
  caption where applicable, n + the insufficient-sample marker, the occurrence-R definition note, the
  measurement framing, the "Descriptive only — not trading advice" disclaimer, and a "Re-run identical"
  button. A failed study shows its explicit error; a cancelled study is marked PARTIAL; a queued/running
  study shows its OWN explicit absence sentence.

## Copy / labels

All labels, captions, framing, status names, and per-status absence sentences come from
`GET /research/taxonomy → studies` (the frontend hardcodes none). A pre-J-60 taxonomy payload falls back
to a minimal local register so the page never blocks render.

## Design system adherence

Dark slate-950 cockpit palette, slate-900/60 panels with slate-800 borders, font-mono for ALL numerics
(arm times, R bases, fingerprints, counts), the existing green/red/amber semantics (emerald for +1R, rose
for −1R, amber for truncated/running/hindsight). Every interactive element has hover / focus / active
states. Consistent with `/journal` (Panel-style surfaces, the `AnalyticsView` horizon-row convention).

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: clean — type-check + compile pass; `/studies` route builds at 7.1 kB.

## Known Issues

- The page polls every 700 ms while any study is queued/running and stops when everything is terminal.
  This is adequate for the in-process job timings (~1–3 s); a future iteration could move to a WS/SSE push
  if studies grow much longer.
- The "Full RTH" quick-pick on the historical-window create form reuses the cockpit's ET-session preset
  helper; the long-window fetch then follows the same progressive-fetch path the watch uses.
