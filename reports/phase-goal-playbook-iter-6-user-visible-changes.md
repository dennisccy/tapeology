# Phase goal-playbook-iter-6 — User-Visible Changes

**Phase:** goal-playbook-iter-6
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On `/desk`, after running the Playbook for a session (the same "Session date" input + "Run
  Playbook" button already shipped in J-03), the operator can now see up to three additional setup
  types fire in the Playbook Signals table, each with its own row and its own setup chip:
  - **"Range Trade"** (`range_trade`) — a support-bounce (long side) when price tests and holds a
    well-tested low zone twice and reverses up, or a resistance-fade (short side) when price tests
    and holds a well-tested high zone twice and reverses down. Same served `setup_id`, two possible
    `side` values.
  - **"Double Top"** (`double_top`, short side) — two roughly-equal swing highs followed by a break
    through the valley between them.
  - **"Double Bottom"** (`double_bottom`, long side) — the exact mirror: two roughly-equal swing
    lows followed by a break through the peak between them.
- Users can now click a "Range Trade" signal row (same click-to-expand row interaction already
  shipped) and see a new geometry disclosure line beneath the trigger/invalidation line, showing:
  the tested range's width in MBR, how many times the low zone was touched, how many times the high
  zone was touched, the breakout slot, an optional "crossed midrange" note (price swung through the
  middle of the range on its way to the signal), and an optional "absorption bar present" note (a
  slow, high-volume bar sat right at the tested edge).
- Users can now click a "Double Top" or "Double Bottom" signal row and see its own geometry
  disclosure line: the gap between the two tops/bottoms in MBR, how many bars separated them, the
  depth of the valley/peak between them in MBR, the "nominal risk" (the full, never-shrunk pattern
  height in MBR, measured from the worse of the two pivots), the breakout slot, and — when
  available — a "second RVOL vs first" ratio comparing volume around the second top/bottom to
  volume around the first.
- Every already-shipped disclosure on that same expanded row — the forward-measurement table, the
  invalidation-breach note, the baseline-pool note, the volume/market/approach-attempt lines — still
  renders for these new setup types, unchanged, beside the new geometry line (the same "what
  happened afterward" math already used for every other setup family).
- The Playbook's own summary text — both the "not computed yet" amber panel and the populated
  section's own intro paragraph on `/desk` — now names all eight setup families (opening-range-break,
  jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top,
  double-bottom) instead of five, visible on every visit to the Playbook Signals section regardless
  of whether a range-trade or double-top/bottom signal has ever fired.

---

## What Changed in the Visible UI

- The Playbook Signals table's "setup" column (chip cell, both in the row and in the expanded
  detail panel) can now show three additional chip labels: "Range Trade", "Double Top", "Double
  Bottom" — using the exact same chip styling every other setup chip already uses
  (`playbookSetupLabel()` in `apps/frontend/app/desk/page.tsx`). No new column, no new table.
- The expandable per-signal detail panel (`PlaybookSignalDetail`) gained two new conditional lines
  that render only for the matching setup type: one `range_trade`-only geometry line
  (`data-testid="desk-playbook-signal-range-trade-geometry"`) and one shared
  `double_top`/`double_bottom` geometry line (`data-testid="desk-playbook-signal-double-extreme-geometry"`).
  Every other already-shipped geometry line (opening-range, jbe/dbi, cup-and-handle, capitulation)
  is unaffected — the render is gated by `signal.setup_id`, so exactly one geometry line shows per
  signal.
- Two static copy spots on `/desk` were widened: the amber "Playbook not computed for this
  session." empty-state sub-text, and the Playbook Signals section's own intro paragraph (both are
  plain text in the page component, not served data) — both now list all eight family names instead
  of five.
- The amber "register" footer note at the bottom of a computed Playbook record
  (`data-testid="desk-playbook-register"`) is served verbatim from the record itself
  (`PLAYBOOK_REGISTER`), and the backend's copy of that string was also widened to name all eight
  families — see "What Old Behavior Changed" below for why this one does NOT change retroactively
  for already-recorded sessions.
- No new page, no new route, no new navigation link, no new button, and no new input field. The
  session-date input and "Run Playbook" / poll / cancel controls are pixel-for-pixel the same
  controls already shipped.

---

## What Old Behavior Changed

- **None for the five already-shipped setup families themselves.** Opening-range-break,
  jump-base-explosion, drop-base-implosion, cup-and-handle, and capitulation signals render with
  identical wording and values to before this iteration (confirmed by the developer's own
  byte-identical-file proof over existing fixture inputs and this iteration's regression tests).
- **The Playbook Signals summary copy changed for every operator, immediately, on both `/desk`
  copy spots** — the "not computed yet" panel and the section's own intro paragraph read
  differently starting the moment this iteration's frontend build is live, regardless of which
  session date is being viewed.
- **The "register" footer note does NOT change retroactively for already-recorded sessions.**
  Because playbook records are append-only and never rewritten, the `register` text an operator
  sees at the bottom of a computed record is whatever text was true when THAT record was computed
  — a session recorded before this iteration still shows the old five-family register wording until
  it is re-computed (which mints a new record, since `PLAYBOOK_SETUPS` growing to nine entries also
  moves `playbook_input_signature`). Only newly-run "Run Playbook" computes after this iteration
  produce records with the widened eight-family register text.

---

## Not Visible Yet

- The back-scan (J-07, a resumable sweep of every recorded session) has not been run. This
  iteration's own dev-time verification of `range_trade`/`double_top`/`double_bottom` stayed
  fixture-scoped only — nothing in the operator's real recorded universe has been checked yet for a
  genuine firing, so on an arbitrary real session date the operator may see zero new-family signals
  even where the pattern might eventually be found once J-07 sweeps the real data.
- The evidence view (J-08, pooled distribution stats per setup/side/horizon) does not exist; there
  is no UI or API surface yet for "how did range-trade or double-top signals do across every
  recorded session."
- The Playbook (all nine setup types, old and new) still has no MCP surface at all — MCP stays at
  exactly 18 read-only tools this iteration (J-09, "MCP contract v4," is out of scope, and
  `apps/backend/app/mcp/__init__.py` has zero diff). An operator using Claude+MCP cannot read any
  playbook signal today; only the browser at `/desk` and direct REST calls to
  `GET /research/desk/playbook` expose it.
- `range_trade` is explicitly shipped as the PROVISIONAL-tier, "first draft" detector of the nine
  per the book's own spec — its two supporting disclosure notes (`crossed_midrange`,
  `absorption_bar_present`) reflect this developer's own documented, degeneracy-checked reading of
  vague book prose, not a formula the canonical spec itself pins down. No UI change results from
  this — it renders exactly like every other geometry line — but an operator reading the
  disclosures should know this one detector's supporting notes carry more judgment latitude than
  the other eight.
- Two orphaned run-ledger rows on the operator's real (non-fixture) store were investigated this
  iteration (see the dev handoff's "Known Issues") but left in place, unfixed, by design — the
  store exposes no delete/rewrite method. They have no visible effect on any `/desk` page a user
  looks at; they were surfaced here only for completeness since they were part of this iteration's
  own investigation, not because any UI shows them.
