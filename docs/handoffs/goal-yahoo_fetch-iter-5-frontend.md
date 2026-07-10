# goal-yahoo_fetch-iter-5 Frontend Handoff

**Phase:** goal-yahoo_fetch-iter-5
**Date:** 2026-07-10
**Agent:** developer
**Status:** complete

## What Was Built

`/structure` gains its **one new explicit write action** — a "Fetch from Yahoo Finance" control —
above the pre-existing read-only Levels & Zones "Load" form. No new page, no new route, no nav
change (`/structure` was already in the top bar from the structure-UI interlude).

- **Fetch-control section** (`apps/frontend/app/structure/page.tsx`): a `Panel` titled "Fetch from
  Yahoo Finance" containing:
  - **Symbol** — the existing `<SymbolSearch>` component, reused verbatim (same debounced
    `/symbols/search` suggestions dropdown as the Load form).
  - **Timeframe** — a native `<select>` offering exactly the six era-5 Yahoo-supported values
    (`1w 1d 4h 1h 5m 1m`), matching the existing Comparison section's dataset `<select>` styling.
    `15m`/`8h`/`1mo` (valid backend `bar_timeframes` entries the Yahoo adapter itself does not map)
    are deliberately not offered — a display choice, not a second validation authority; an
    out-of-set value would still 422 server-side either way.
  - **Start / End (UTC, ISO-8601)** — two text inputs mirroring the existing
    `structure-as-of-input` pattern.
  - **"Fetch from Yahoo Finance"** button — disabled until all four fields are set (mirrors the
    existing `canSubmit` pattern), shows "Fetching…" while in flight.
- **Submit behavior**: POSTs `{symbol, timeframe, start, end}` to `/research/bars` via the new
  `recordBarSeries()` helper. On success, it seeds the pre-existing Load form's
  `symbolInput`/`asOfInput` state from the response (`bar_series.symbol` /
  `bar_series.window_end_utc`) and calls the ALREADY-BUILT `handleLoad()` — so the existing Levels
  & Zones section (chart + level lines + `ZoneRow` confluence table) renders the real fetched data
  with **zero new rendering code**. A manual re-submit of the original Load form afterward simply
  repeats the same read, never a second write.
- **Provenance badge**: `FeedBasisBadge` (previously cockpit-only, keyed off a live-watch
  snapshot's `data_feed`) now also renders beside the Structure chart, keyed off the charted bar
  series' own `feed` field. Its `dataFeed` prop was widened from the narrow union
  `"sim"|"iex"|"sip"|null|undefined` to `string|null|undefined` so it accepts `"yahoo"` (and any
  future feed id) through the exact same taxonomy-lookup rendering logic — no new component, no new
  fetch, no hardcoded label.
- **Honest states**: a POST failure renders the backend's own 422 (unsupported timeframe / no data
  for window) / 503 (adapter unavailable) / 504 (vendor timeout) / 409 (content-duplicate) `detail`
  string verbatim through the page's existing `UnavailablePanel` component — never a single generic
  message. A fetched symbol with no stored bars falls through to the pre-existing, already-tested
  `structure-no-bar-series` empty state (own testid) — no new empty-state component needed, since
  the fetch simply feeds bars into the same J-04 state machine that already handles this case.

## Files Changed

- `apps/frontend/lib/api.ts` -- new `recordBarSeries(params)` async function (`+41` lines),
  modeled on the existing `createStudy` POST pattern in the same file: on `res.ok` returns
  `{ok:true, bar_series, status}`; otherwise attempts to read `data.detail` from the JSON body and
  returns `{ok:false, status, error}}`; a network-level failure returns
  `{ok:false, error:"Backend unreachable — is the API running?"}`.
- `apps/frontend/lib/types.ts` -- new `RecordBarSeriesResult` interface (`+12` lines) describing
  the helper's return shape.
- `apps/frontend/components/FeedBasisBadge.tsx` -- widened the `dataFeed` prop type
  (`+11/-3` lines, doc comment + type signature only — the component's render logic is untouched).
- `apps/frontend/app/structure/page.tsx` -- `+181/-9` lines: the new section, four new pieces of
  state (`fetchSymbolInput`, `fetchTimeframeInput`, `fetchStartInput`, `fetchEndInput`,
  `fetchSubmitting`, `fetchError`), the `handleFetchYahoo`/`handleFetchSubmit` handlers, the
  `YAHOO_TIMEFRAMES` constant, the `canFetch` gate, and the badge insertion point inside the
  existing chart panel; updated page-level doc comments (now "J-01 + J-02 + J-03 + J-05", nine
  canonical endpoints instead of eight).

No other frontend file was touched. No new component file was added — everything reuses
`Panel`, `SymbolSearch`, `StructureChart`, `ZoneRow`, `UnavailablePanel`, `EmptyState`,
`LoadingPanel`, and the page's local `INPUT_CLASS` styling constant.

## Visual / UX confirmation

Confirmed live via Chrome MCP against the real running app (backend `:8301`, frontend `:3301`,
`npx tsc --noEmit` clean beforehand):

- The new panel sits above the Load form in the existing single-column `max-w-7xl` layout,
  identical visual language to the rest of the page (slate surfaces, uppercase field labels,
  `border-slate-600 bg-slate-800` button styling matching Load/Run-comparison, disabled-state
  opacity). No restyling of the page, no new visual effects introduced.
- With all four fields empty, the button renders visibly disabled.
- Filling `symbol=AAPL, timeframe=1d, start=2026-06-01T00:00:00Z, end=2026-07-09T23:59:59Z`
  (an already-stored, already-indexed window from a prior iteration) and clicking the button
  produced a `200` (store-first, not `409`), and within roughly a second the Levels & Zones
  section repopulated with: a real 5m candle series (2028 bars), real level lines drawn on the
  chart (`5m swing-pivot`, `1d prior-period-extreme`, `1h swing-pivot`, etc. at their real prices),
  a real confluence-zones table (`Class A · zone 1 · score 32`, five real cross-timeframe members
  at `273.75` spanning `1d/1h/1w/4h/5m`), and — directly above the chart — the provenance badge
  reading **"feed Yahoo Finance"**, sourced from `GET /research/taxonomy`.
- One minor, harmless UX note: because `handleFetchYahoo` also sets `symbolInput` (the pre-existing
  Load form's own symbol field) on success, `SymbolSearch`'s own debounced suggestions dropdown can
  briefly auto-open on that field after a successful fetch (since the field's value changed
  programmatically, not by a user keystroke). It does not block or corrupt anything — clicking
  elsewhere dismisses it — but it is a small side effect of reusing the Load form's state as the
  seed for the read path, worth a look if a future iteration wants to suppress it (e.g. by not
  re-triggering the search effect on a programmatic value change).

## Tests

No frontend test runner exists in this repo (`apps/frontend/package.json` has no `test` script, no
`.test.ts(x)` files anywhere) — unchanged from every prior iteration. Frontend correctness was
verified via:
1. `npx tsc --noEmit -p tsconfig.json` — exit 0, zero type errors, including the new
   `React.FormEvent` handler (same no-explicit-`React`-import precedent already used three other
   places in this exact file plus two other components) and the `recordBarSeries`/`FeedBasisBadge`
   wiring.
2. The live browser walkthrough described above.
3. `grep -rn "Yahoo Finance" apps/frontend` (excl. `.next`) — 9 hits, all either code comments or
   the fetch-control's own product-mandated UI copy (button/title/prose/aria-label); zero hits
   inside `FeedBasisBadge.tsx` itself. See the dev handoff's "A note on the 'no hardcoded Yahoo
   Finance' check" section for the reasoning on why the button/title copy is expected, sanctioned,
   verbatim-from-goal.md text and not a violation of the provenance-badge anti-hardcode rule.

## Known Issues

- The `SymbolSearch` dropdown auto-open side effect on the Load form's symbol field after a
  successful fetch (described above) — cosmetic, non-blocking, not fixed this iteration (not in
  the plan's scope; noted for visibility).
- The browser-qa-agent should seed the plan's two specific narrow committed fixtures
  (`AAPL_1d_20260601_20260604.json`, `AAPL_1h_20260601_20260603.json`) via the store-first POST
  path or `reindex()` if it wants to reproduce the exact iter-4-confirmed "14 levels / 4 zones /
  score 12.0" result; my own live check above used broader, already-indexed real dev data instead
  (a valid proof of the same mechanism, not the identical fixture).
