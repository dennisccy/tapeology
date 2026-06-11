# goal-i_will_be_super_rich_with_my_loved_ones-iter-16 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-16
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

The segregated journal **Analytics** view (capability 31, J-59) as a second view within the existing
`/journal` page — NO new route, NO new nav entry (the blueprint-registered home). The thesis table stays
the DEFAULT view, so existing J-50/J-51 captures are unaffected. Plus the iter-15 carry-along: the
honest-absence copy split on `/journal/[id]`.

- **View toggle** on `/journal` — a two-tab segmented control (`Theses` | `Analytics`), `Theses` default.
  `role="tablist"`/`role="tab"` with `aria-selected`, hover/focus/active states per the design discipline.
  `data-testid="journal-view-toggle"`, `journal-view-theses`, `journal-view-analytics`.
- **`AnalyticsView`** (`components/AnalyticsView.tsx`) — renders `GET /research/analytics` **verbatim**
  (display rounding ONLY; no client-side arithmetic, no percentages):
  - one **partition block** per (`data_feed`, `config_fingerprint`) — feed chip + the FULL fingerprint (mono,
    `title=` full value). Two fingerprints render as two separate blocks (the never-pool guarantee, visible).
    `data-testid="analytics-partition"` with `data-feed`/`data-fingerprint`; `partition-feed`/`partition-fingerprint`.
  - per **group** (`setup_type` × `direction`): always-visible `n` (`group-n`) and `abandonment` bucket
    (`group-abandonment`, shown even when 0); the per-horizon ternary chips (`horizon-plus`/`horizon-minus`/
    `horizon-neither`) with a **separate** `horizon-truncated` chip and `horizon-spread-per-r` (median spread/R
    beside the +1R figure); `group-time-to-confirm` (honest absence copy when null); `group-tag-frequencies`
    (`tag-frequency` chips, user-confirmed only); and a **visually separate** `group-acted-trade` card
    (`acted-trade-absent` when none, else median realized R + median spread/R).
  - **insufficient-sample**: a group below the min shows `group-insufficient-sample` (the amber marker)
    WITH its `n` and the `< min` figure — never bare distributions.
  - states: loading skeleton (`analytics-loading`), error alert (`analytics-error`), honest empty
    (`analytics-empty`).
  - the honesty **framing line** (`analytics-framing`) is always shown — journaled measurements, never a
    profitability/edge/win-rate claim; R units only, never currency.
- **Carry-along** in `JournalDetailView.tsx` — the three honest-absence fallbacks (grades / excursions /
  execution checks) now split by resolved status via `isResolved()` + `absentCopy()`:
  - still-ACTIVE thesis (or any non-terminal status) => "Not yet …" copy;
  - RESOLVED thesis that predates the feature => "… predates that" copy.
  Each fallback carries `data-absence-cause="not_yet" | "predates"` for the QA captures.

## Files Changed

- `apps/frontend/lib/types.ts` -- Analytics/AnalyticsPartition/AnalyticsGroup/AnalyticsHorizonRow/AnalyticsActedTrade/AnalyticsResult + AnalyticsTaxonomy; `analytics?` on ResearchTaxonomy.
- `apps/frontend/lib/api.ts` -- `fetchAnalytics()` (honest empty vs explicit error).
- `apps/frontend/app/journal/page.tsx` -- the Theses/Analytics view toggle + lazy analytics load.
- `apps/frontend/components/AnalyticsView.tsx` -- NEW; the analytics view.
- `apps/frontend/components/JournalDetailView.tsx` -- `isResolved`/`absentCopy` + the three copy splits.

## Design System Adherence

- Dark instrument-panel surfaces (`slate-950/900/800`), mono numerics for every figure, restrained borders.
- Color semantics held: +1R emerald, −1R rose, neither/insufficient amber/slate, long emerald / short rose
  chips. No new effects; no currency symbol, equity curve, or win-rate-as-edge presentation anywhere.
- All copy (labels, captions, framing) comes from the taxonomy `analytics` block; the view hardcodes only a
  minimal fallback register for a pre-J-59 taxonomy so it never blocks render.
- Responsive: `flex-wrap` partition/group headers + horizon rows; single-column stacking on narrow.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` -> **clean, exit 0**.
- (`next lint` not configured in this repo — interactive prompt — so not a gate. `npm run build` deliberately
  not run per the shared-`.next` harness caution.)

## Known Issues / Notes for QA

- The analytics view fetches on open and re-fetches on each re-open. To see a populated view, start the
  backend against the persistent dev journal DB (`TAPEOLOGY_JOURNAL_DB=apps/backend/tapeology_journal.db`),
  which holds the multi-fingerprint substrate (4 partitions confirmed) for the partition-split assertion.
- Use full-page captures and scroll the asserted element into view — the analytics content sits below the
  toggle; sanity-check capture bytes (the ~6,303-byte blank-frame tooling defect persists per the lesson).
