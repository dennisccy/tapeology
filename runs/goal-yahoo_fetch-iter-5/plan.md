# goal-yahoo_fetch-iter-5 Execution Plan

Target journey: **J-05** — "Fetch from the app: the `/structure` Yahoo fetch control + 'Yahoo
Finance' provenance." This is the **last Must-have journey** in Era 5 — J-01/J-02/J-03/J-04/J-06
are all `passing` as of iter-4 (`runs/goal-session-yahoo_fetch/state/journey-history.json`), and
iter-4's audit was `PASS_WITH_GAPS` (documented, do-not-fix gaps only). If J-05 passes here, the
evaluator can consider `GOAL_ACHIEVED`.

Depth is **full** (backend + frontend + the first genuinely browser-verifiable UI in this era) —
confirmed correct; do not downgrade to lean.

## What to Build

**Backend (small, additive — confirmed against current source):**
1. Add `"yahoo": "Yahoo Finance"` to `FEED_BASIS_LABELS` in
   `apps/backend/app/research/taxonomy.py:36-40` (currently `sim`/`iex`/`sip` only).
   `taxonomy_payload()` builds `feed_basis.feeds` from this dict automatically — no route change.
   `config.py` is untouched; `config_fingerprint` stays `4d665603569b9dbf` (taxonomy copy isn't
   fingerprinted).
2. Fix **audit carry-forward B2** in `list_bar_series` (`apps/backend/app/research/routes.py`,
   `@router.get("/bars")`, ~line 1712-1729): today the `if symbol is None and timeframe is None:`
   short-circuit runs **before** the blank-string normalization two lines below it, so
   `GET /research/bars?symbol=` (empty string, not `None`) skips `store.list()` and falls into
   `index.list(symbol=None, timeframe=None)` instead — which misses any un-indexed legacy series.
   Fix: move `normalized_symbol = symbol.strip().upper() if symbol else None` /
   `normalized_timeframe = timeframe.strip() if timeframe else None` **above** the short-circuit
   and test `normalized_symbol is None and normalized_timeframe is None`. This is a 3-line reorder,
   not new logic — the real-filter path's behavior (case-insensitive symbol, stripped timeframe)
   is unchanged.
3. Update `test_research_api.py:154` — `test_taxonomy_serves_feed_basis_copy_canary` currently
   asserts `set(labels.keys()) == {"sim", "iex", "sip"}`; this must become
   `{"sim", "iex", "sip", "yahoo"}` with an added assertion `labels["yahoo"] == "Yahoo Finance"`.
   This is the **only** test in the repo that pins the exact label set (confirmed by grep across
   all files referencing `FEED_BASIS_LABELS`/`feed_basis`).
4. New backend unit test (`test_bars_api.py`, alongside the existing
   `test_symbol_and_timeframe_filter_returns_only_the_matching_series` /
   `test_no_param_get_is_byte_identical_to_a_direct_store_list_call`): seed a store with an
   **un-indexed** record (write directly via `store.record()`, skip `index.insert()`), then assert
   `GET /research/bars?symbol=` (blank) returns byte-identical JSON to `GET /research/bars`
   (no param) — proving B2 is actually closed, not just reordered without effect.

**Frontend (`apps/frontend/app/structure/page.tsx` + `lib/api.ts` + `FeedBasisBadge.tsx`):**
1. New POST client helper in `lib/api.ts`, modeled on `createStudy` (line 730) — same
   try/catch-with-`{ok,...}`/error-shaped-from-`data.detail` pattern already used by every mutating
   call in this file. Body `{symbol, timeframe, start, end}` → the route at `routes.py:1577
   record_bar_series` (which already handles store-first idempotence, 422/503/504/409). Returns
   `{ok:true, bar_series}` or `{ok:false, error, status}`.
2. New fetch-control section on `/structure`: symbol (reuse `<SymbolSearch>`), a timeframe
   `<select>` offering exactly the six era-5 Yahoo-supported values — `1w 1d 4h 1h 5m 1m`
   (`CONFIG.bar_timeframes` has 9 entries; `15m`/`8h`/`1mo` are Yahoo-unsupported per the iter-2
   assumption ledger — do not offer them here), start/end datetime inputs (ISO, mirroring the
   existing `structure-as-of-input` pattern), and a **"Fetch from Yahoo Finance"** button disabled
   until all four are set (mirrors the existing `canSubmit` pattern at line 774).
3. On submit: POST via the new helper, then render results by **reusing the existing Levels &
   Zones section verbatim** — the cleanest way to satisfy "reuse the existing ZoneRow/chart
   rendering, zero client recomputation" without a second render path (which the coherence-auditor
   would flag). Recommended wiring: on a successful POST, set `symbolInput`/`asOfInput` to the
   fetched symbol / window end, and invoke the existing `handleLoad()` — the already-built
   Levels & Zones section (chart + `ZoneRow` table) then populates from the real Yahoo data with
   no new rendering code. Add the provenance badge beside that section's chart, keyed off the
   fetched series' `feed` field.
4. Provenance badge: widen `FeedBasisBadge`'s `dataFeed` prop
   (currently `"sim"|"iex"|"sip"|null|undefined`, `components/FeedBasisBadge.tsx:29`) to also
   accept `"yahoo"` (or a bar-series feed string generally) — it already reads
   `feed_basis.feeds` from `GET /research/taxonomy` verbatim and falls back to the raw id, so no
   new fetch/logic is needed, only the type. **No hardcoded "Yahoo Finance" string anywhere in the
   frontend** — verified by `grep -r "Yahoo Finance" apps/frontend` (excluding `.next`) returning
   only the badge's data-driven render, never a literal.
5. Honest states: a symbol with no stored bars after fetch → reuse/mirror the existing
   `structure-no-bar-series` empty-state pattern (own testid); a POST error → fold the backend's
   own `detail` string (422 unsupported-timeframe / 422 no-data-for-window / 503 unavailable / 504
   vendor-timeout / 409 already-registered) into the existing `UnavailablePanel` degraded
   treatment — never a single generic "something went wrong" string, never silent.

**No frontend test runner exists in this repo** (`apps/frontend/package.json` has no `test`
script, no `.test.ts(x)` files anywhere) — this project verifies frontend behavior exclusively via
browser-qa (Chrome MCP), consistent with every prior iteration. Do not introduce a new test
framework for this iteration; the new POST helper's happy/error paths are verified by the browser
lane driving the real control, per Testing Requirements below.

## Agents Required

- backend-data: yes -- add the `"yahoo"` taxonomy label, fix B2 (blank-param normalization order)
  in `list_bar_series`, update the one test that pins the label set, add the B2 byte-identity
  test, run the full backend suite + engine equivalence, confirm `config_fingerprint` unchanged.
- frontend-ux: yes -- add the POST-bars client helper, the fetch-control section on `/structure`
  (symbol/timeframe/date-range/button), wire its result into the existing Levels & Zones render
  path, widen `FeedBasisBadge` for the `"yahoo"` feed, and the distinct honest states (empty /
  each POST error code).

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/research/taxonomy.py` -- add `"yahoo": "Yahoo Finance"` to `FEED_BASIS_LABELS`
  (line ~37-40).
- `apps/backend/app/research/routes.py` -- `list_bar_series` (~line 1712-1729): reorder blank-param
  normalization above the no-param short-circuit (B2 fix). No other route logic changes.
- `apps/backend/tests/test_research_api.py` -- update `test_taxonomy_serves_feed_basis_copy_canary`
  (line 154) to expect `{"sim", "iex", "sip", "yahoo"}` and assert the new label's exact value.
- `apps/backend/tests/test_bars_api.py` -- new test: un-indexed legacy record + blank `?symbol=` ==
  no-param, byte-identical (B2 proof). Existing `test_symbol_and_timeframe_filter_...` and
  `test_no_param_get_is_byte_identical_...` (lines ~193+) must stay green unmodified.
- `apps/frontend/lib/api.ts` -- new POST `/research/bars` helper, modeled on `createStudy` (line
  730) / the GET pattern in `fetchLevels`/`fetchBarSeriesList` (lines 887-931).
- `apps/frontend/app/structure/page.tsx` -- add the fetch-control section, its state + submit
  handler, and the provenance badge; reuse existing components (`SymbolSearch`, `StructureChart`,
  `ZoneRow`, `Panel`, `UnavailablePanel`, `EmptyState`, `LoadingPanel`) — do not duplicate render
  logic.
- `apps/frontend/components/FeedBasisBadge.tsx` -- widen the `dataFeed` prop type to admit
  `"yahoo"` (or the bar-series `feed` string generally); no change to its taxonomy-read logic.
- `docs/handoffs/goal-yahoo_fetch-iter-5-dev.md` -- new dev handoff.
- Expected **zero diff**: `apps/backend/app/research/levels.py`, `research/backtests.py`,
  `research/strategies.py`, `config.py` (fingerprint `4d665603569b9dbf`), `research/bars.py`,
  `research/bar_index.py`, `providers/adapters/` (Yahoo + Alpaca), the tape engine, the MCP layer
  (no new tool). Any touch to these must be justified as additive-only in the dev handoff.

## UI Evolution

- New user-facing capability: fetch real historical Yahoo bars for a chosen symbol / timeframe /
  date range directly from `/structure` (keyless, one click) and immediately see the computed
  S/R levels + A/B/C confluence zones on that real data.
- New information displayed: real Yahoo candles for the fetched window (previously only visible
  for symbols with data recorded some other way); a "Yahoo Finance" provenance badge beside the
  series.
- New user actions: symbol input (reused), a new timeframe selector, new start/end date-range
  inputs, and the **"Fetch from Yahoo Finance"** submit button — the one new explicit write action
  in the whole app.
- UI surface changes: a fetch-control section + provenance badge added to the existing
  `/structure` page. No new page/route.
- Navigation changes: none — `/structure` is already in the top bar (interlude era).

## Visual Requirements

- Component patterns: reuse `Panel` for the new fetch-control section header; reuse the existing
  `INPUT_CLASS` input styling and the established button classes (`border-slate-600 bg-slate-800`
  active state) for visual consistency with the Load/Run-comparison buttons already on this page;
  a native `<select>` for timeframe, matching the Comparison section's existing dataset `<select>`
  (line ~1137); reuse `UnavailablePanel`/`EmptyState`/`LoadingPanel` for every honest state —
  do not invent new empty/error components.
- Layout: single new `<section>` in the existing single-column `max-w-7xl` page layout, placed
  above or alongside the existing Levels & Zones "Load" form (both ultimately populate the same
  chart/zone-table render area).
- Key visual effects: none new — this is a functional addition to an already-shipped dark
  instrument-panel page (slate surfaces, amber honest-state treatment, font-mono numerics); do not
  restyle the page.
- States to handle: idle (fetch not yet submitted), fetching in-flight (disable the button,
  "Fetching…" label, matching the `comparisonRunning` precedent), success (chart + levels + zones +
  badge populate via the reused render path), no-stored-bars-after-fetch (distinct empty state),
  and one distinct-but-folded degraded message per POST error code (422/503/504/409) via
  `UnavailablePanel`.

## Key Test Scenarios

- `taxonomy.FEED_BASIS_LABELS["yahoo"] == "Yahoo Finance"`; `GET /research/taxonomy` serves
  `{"id":"yahoo","name":"Yahoo Finance"}` in `feed_basis.feeds`; the updated canary test passes.
- `GET /research/bars?symbol=` (blank, no timeframe) returns byte-identical JSON to
  `GET /research/bars` (no param) even when an un-indexed legacy series exists in the store (B2
  closed) — new test. The existing real-filter test (`?symbol=PG&timeframe=1d` etc.) and the
  existing no-param-byte-identity test both stay green, unmodified.
- Browser (J-05, HARD requirement — services + Chrome MCP must both be reachable; a "passing"
  without a real screenshot is `unknown`, per the spec's NOTES): pre-seed the two committed
  fixtures (`AAPL_1d_20260601_20260604.json`, `AAPL_1h_20260601_20260603.json` — already proven in
  iter-4 to yield 14 levels / 4 class-B zones incl. one cross-timeframe zone at score 12.0) through
  the real store-first POST path (or `reindex()`) so the click hits the index with **zero
  network**; then drive the fetch control with that exact `(AAPL, timeframe, start, end)` tuple
  and confirm: candles render, one level line per `levels[]` entry, the zone table matches
  `confluence_zones[]`, the badge reads "Yahoo Finance", and a symbol with no stored bars shows
  the distinct empty state.
- A duplicate-window POST (click again / pre-seeded window) returns **`200`, store-first** — not
  `409` (iter-3 lesson; do not regress this).
- Spot-check J-04 (levels/zones still render on `/structure`) and J-06 (`/`, `/journal`,
  `/studies`, `/performance` unaffected) did not regress while in the browser.
- Full backend suite green (iter-4 baseline: 1206 passed / 6 skipped / 0 failed, plus this
  iteration's new tests); engine equivalence 22/22; `config_fingerprint == 4d665603569b9dbf`;
  `git diff` empty on `levels.py`/`backtests.py`/`strategies.py`/`config.py`/`bars.py`/
  `bar_index.py`/`providers/adapters/`.
- `grep -r "Yahoo Finance" apps/frontend` (excluding `.next`) matches only the data-driven badge
  render, never a hardcoded literal.

## Out of Scope (do not act on this iteration)

- Enforcing mixed-feed segregation inside `compute_levels` (audit B1, carried forward from iter-4
  — `levels.py:306` selects a symbol's series by symbol alone, feed-blind). Frozen, fingerprint-
  locked; would require a versioned path beside it, never an edit. J-05's "honestly segregated"
  acceptance is met at the fetch/store/display layer on a single-feed fixture — see the iter-5
  assumption-ledger entry already logged in `runs/goal-session-yahoo_fetch/state/assumptions.md`.
- The live cache-miss Yahoo network fetch as a keyless browser assertion (integration-gated,
  `TAPEOLOGY_LIVE_INTEGRATION=1` only).
- Any change to `research/levels.py`, `research/backtests.py`, `research/strategies.py`,
  `config.py`, `research/bars.py`, `research/bar_index.py`, the tape engine, or the Alpaca adapter.
- Champion promotion or any write beyond the explicit bar fetch/store.
- A new MCP tool, a new route/page, `/datasets` library-management UI, the tick-tape recorder, the
  15-symbol panel.

No drift from `docs/goal.md` detected: this spec is a direct, tightly-scoped implementation of Key
Capability 5 ("Fetch-from-the-app on `/structure`") and Must-have journey J-05, verbatim, plus one
pre-flagged bug-fix (B2) explicitly named as J-05 pre-work in the iter-4 audit.
