# Phase goal-playbook-iter-8 — User-Visible Changes

**Phase:** goal-playbook-iter-8
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now scroll to a new **Playbook Evidence** panel at the bottom of `/desk` (below the
  existing Backscan panel) and see, per setup family (open-high break, jump-base explosion,
  drop-base implosion, cup-and-handle, capitulation, range trade, double top/bottom) and side
  (long/short), how many recorded signals fired and what their forward-return and max-drawdown
  distributions (median, p25, p75, mean) look like against the pooled seeded baseline.
- Users can now spot statistically thin cells at a glance via an amber **"low n"** badge in the
  table's Flag column — the numbers are still shown next to the badge, never hidden.
- Users can now see, in a second table titled **"Invalidation breaches"** directly below the main
  cells table, how many recorded signals breached their invalidation level per setup/side/horizon
  (breached count out of total count).
- Any script, MCP client, or curl user can now call `GET /research/desk/playbook/evidence` directly
  to retrieve this same data as JSON — including an optional `?signature=` parameter to inspect a
  non-default recorded signature's own date list and created span (this parameter itself has no UI
  control; see "Not Visible Yet" below).
- Operators typing a half-finished date (e.g. `2026-06-2`) into the Backscan panel's "Backscan from
  day" or "Backscan to day" boxes no longer risk the plan preview hitting a raw backend error — it
  now returns the same honest "0 dates planned" response the already-handled inverted-range case
  produces.

---

## What Changed in the Visible UI

- `/desk` gains a new bordered panel headed **"Playbook Evidence"**, rendered directly below the
  shipped Backscan panel and above nothing else (it is now the last section on the page). No new
  route was added — this is a scroll-down section, not a new page.
- The new panel opens with a plain-language disclosure paragraph (the `register` text) stating what
  was measured, what the baseline is, and that nothing here is a probability, expectancy, or advice
  claim.
- Below that: a dense table (setup × side × measure — 270 rows) with 3 identity columns, 6 "Signal"
  columns (n, truncated, median, p25, p75, mean), 5 "Baseline" columns (n, median, p25, p75, mean),
  and 1 "Flag" column showing the "low n" badge on thin cells.
- Below the cells table: the **"Invalidation breaches"** table (setup × side × horizon — 90 rows)
  with Breached/Total count columns.
- When the fixture store holds a recorded signature other than the current default, an **"Other
  signatures (listed, never pooled)"** list appears showing each signature string, how many dates it
  covers, and its created-date span — visually separate from the main cells table, never folded in.
- No navigation change: the top nav bar still reads Cockpit / Structure / Desk exactly as before;
  there is no new nav entry for Evidence since it lives inside the existing `/desk` page.

---

## What Old Behavior Changed

- **Backscan plan preview**: previously, an incompletely-typed date in the "Backscan from day" /
  "Backscan to day" boxes (e.g. `2026-06-2` mid-keystroke) could make the backend return a raw HTTP
  500 (the on-screen panel already tolerated a failed fetch gracefully, so this was not visible as a
  crash to the operator, only as an error in network traffic/logs). Now the same incomplete date
  returns a clean "0 dates planned · 0 missing at the current signature." response — no functional
  change an operator would notice at the screen, but the underlying response is now honest instead
  of erroring.

---

## Not Visible Yet

- The evidence endpoint's `?signature=` query parameter (inspect a specific non-default signature's
  own `dates`/`created_span` without pooling it) exists in the API but has no UI control anywhere on
  `/desk` — there is no dropdown, input, or link that lets an operator choose a signature to inspect.
  The only signature-related information visible in the UI is the automatically-rendered "Other
  signatures" list, which shows the same fields but for every non-default signature at once, not
  interactively.
