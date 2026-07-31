# goal-desk-iter-35 Frontend Handoff

**Phase:** goal-desk-iter-35
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

A new, read-only **"Screen Comparison"** section on `/desk` (J-20) — discloses how the currently
DISPLAYED screen differs from the screen recorded immediately before it. No new control, no
recompute trigger; a plain page-load/id-change GET only.

- **Placement**: rendered as the LAST section on the page — after the ranked briefing table
  (inside `DeskPopulatedScreen`, far above) and after the existing Top-up Runs / Index
  Reconciliation / Screen Runs sections. This is a deliberate build-time choice (logged in the
  page's own leading comment for the new block): placing it immediately after Briefing (between it
  and Skipped Members) would risk an existing golden's first-visible-match text search resolving
  into the new section's own symbol/side/distance text instead of its real target inside the
  ranked table. Placing it dead last removes that risk entirely — every other section's own
  occurrence of any shared substring resolves first.
- **Wiring**: a new `useEffect` in `DeskPage`, keyed on `displayedSnapshot?.id` (the SAME
  snapshot the Provenance/Briefing sections above already render — whichever screen is currently
  on screen, whether that's `latest` or a selected history entry), calls the new
  `fetchDeskScreenCompare(id)`. Only renders at all once a screen exists (`latest !== null`) —
  there is nothing to compare against a screen that has never been computed.
- **States rendered**:
  - Loading (mirrors `LoadingPanel`).
  - Unavailable (fetch failed, OR the id somehow didn't resolve — folded into the same
    "unavailable" rendering, since this page never requests a comparison for anything other than
    the screen it is already displaying).
  - No earlier recorded screen (`base === null`): "No earlier recorded screen exists to compare
    against." — no table, no counts line.
  - Identical (`identical === true`): both snapshots' own meta + "The compared snapshots' ranked
    rows are identical." — no table.
  - Churned (`identical === false`, base exists): both snapshots' own meta, a descriptive counts
    line ("rows compared N · rank changed N · side changed N · entered N · left N"), and a capped
    table (first 20 of the compare snapshot's own ranked rows, honest "showing N of M" line above
    it when truncated) showing symbol / status / rank(this) / rank(base) / rank change /
    side(this) / side(base) / distance(this) / distance(base) — a null field (only reachable on
    an "entered"/"left" row, since side/distance have carried no legacy-absence case since J-03's
    very first shipment) renders "not recorded in the compared/base snapshot" rather than a bare
    dash, naming WHICH snapshot has no row for that symbol.
- **Deliberately excluded from the table**: `band_class`/`basis_as_of` — the spec's own literal
  wording for the table names only "rank/side/distance"; both fields still ride the fetched API
  payload (used for `identical`'s own field-by-field equality check) but are not rendered as extra
  columns, keeping the new table minimal and matching the "no new ranked-table column" discipline
  for the EXISTING ranked table.
- **Testid namespace**: every new testid lives under `desk-screen-compare-*`
  (`desk-screen-compare-section`, `-meta-compare`/`-meta-base` (+ `-id`/`-dates`/`-signature`
  children), `-no-earlier`, `-counts`, `-identical`, `-table`, `-cap-note`, `-rows-empty`, `-row`
  (+ `-symbol`/`-status`/`-compare-rank`/`-base-rank`/`-rank-change`/`-compare-side`/`-base-side`/
  `-compare-distance`/`-base-distance` children)) — never reuses `data-screen-id`,
  `desk-history-row`, `desk-screen-row`, or any `desk-row-*` testid (a new backend source-guard
  test, `test_desk_screen_compare_ui_guard.py`, proves this structurally, plus that the section's
  own JSX call site renders after `<DeskRowsTable`'s).

No new ranked-table column, no change to the existing ranked table's rendering or markup — J-16's
measured width contract is untouched (`test_desk_ui_guards.py` passes unmodified, confirmed via
`git diff` showing zero changes to that file).

## Files Changed

- `apps/frontend/app/desk/page.tsx` — new components `ScreenCompareMeta`, `ScreenCompareRowView`,
  `ScreenCompareTable`, `ScreenComparisonSection`, `SCREEN_COMPARE_ROWS_DISPLAY_CAP` constant;
  new `screenCompareResult` state + its own `useEffect`; new `<section aria-label="Screen
  Comparison">` rendered last, gated on `latest !== null`.
- `apps/frontend/lib/types.ts` — `DeskScreenCompareSnapshotMeta`, `DeskScreenCompareRow`,
  `DeskScreenCompareCounts`, `DeskScreenCompareResult`.
- `apps/frontend/lib/api.ts` — `fetchDeskScreenCompare(id)`, mirrors `fetchDeskScreenById`'s
  `{ok, data, error}` shape byte-for-byte; a 200 body with `data.compare === null` (unresolved id)
  is folded into `ok: true`, never surfaced as a client-side failure.

## Visual / UX notes

- Reuses the page's existing dark/dense styling verbatim: `LABEL_CELL`/`NUMERIC_CELL`/
  `HEADER_CELL`/`HEADER_CELL_LEFT` (the SAME constants the Top-up Runs/Index Reconciliation/Screen
  Runs tables already use — not the ranked table's own tighter `ROW_*` variants, since this new
  table is not part of the reflow-sensitive ranked briefing), `Panel` wrapper, `LoadingPanel`/
  `UnavailablePanel`/`EmptyState` helpers. No new color, badge, glow, or effect introduced.
- No arrow, colour, or ordering-by-size-of-change anywhere — `rank_change` renders as a plain
  signed integer (or `0`), never styled to imply a direction is good/bad (goal.md's own "never
  gives a direction a valence" Non-Goal).
- Copy is entirely descriptive measurement (counts, ranks, distances, dates) — verified against
  the copy-discipline lint (`test_copy_discipline.py` passes unmodified; the lint's own
  frontend-literal walk covers `apps/frontend/app` automatically, no new exemption needed).
- Verified compiling/type-checking cleanly: `npm run build` → zero type errors, `/desk` route
  entry present in the build output (10.3 kB, up from the pre-iteration size).
- **Not yet browser-verified** — this handoff covers implementation + the `npm run build`
  type-check + a live backend smoke check of the new endpoint only. No screenshot was taken this
  iteration (that is the browser-qa-agent's lane, per the pipeline's own division of labor); per
  T-10, this journey is `unknown`, never `passing`, until a screenshot exists.

## Known Issues

- No golden replay script exists for J-20 yet (`journey-scripts/J-20.json` is authored by the
  browser-qa-agent downstream of this handoff, using stable substrings/testid-existence checks per
  the J-18/J-19 hardening precedent named in the spec).
- The `[NEW]`-flagged demo-narrator walkthrough has not been recorded — a separate pipeline step,
  expected to run against the now-shipped page over the ambient ledger's identical-state and
  churned-state pairs.
- All three states (identical / churned / no-earlier-screen) are exercised by the backend test
  suite (`test_desk_screen_diff.py`) over planted synthetic snapshots, but none has yet been
  captured live against the real ambient ledger's own named pairs
  (`screen-2026-07-31-c169546856c7` vs `screen-2026-07-30-bad6387963ef` for identical;
  `screen-2026-07-25-bd0b37ebc426` vs `screen-2026-07-20-ca185294a384` for churned;
  `screen-2026-06-22-3ecd45c062c7` for no-earlier) — that live capture is the browser-qa-agent's
  job.
