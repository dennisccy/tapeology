# Iteration 3 — Coherence Audit

**Iteration:** goal-yahoo_fetch-iter-3
**Date:** 2026-07-09
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration (J-03) implements exactly one Data Contract row that was already registered in
`blueprint.md` from the baseline draft — the "Store-first lookup `(symbol,timeframe,window) →
series_id`" row, owner `research/bar_index.py`, served by `GET /research/bars?symbol=&timeframe=`.
No new value is introduced; every other registered row is untouched (`bars.py`, `levels.py`,
`backtests.py`, `strategies.py`, `pnl_ledger.py`, `datasets`, `taxonomy.py`, `meta.py` — none
appear in the diff).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Store-first lookup `(symbol,timeframe,window) → series_id` | OK | `apps/backend/app/research/bar_index.py:64-171` — new `BarIndex` class, metadata-only schema (`symbol, timeframe, window_start_utc, window_end_utc, series_id, checksum, bar_count`); no candle data stored |
| Bar series + checksums (candles) | OK | `apps/backend/app/research/routes.py:1636-1638` (store-first hit resolves via `store.get(hit.series_id)`, the canonical checksum-verified read — not served from the index); `routes.py:1685-1692` (`store.record(...)` call is unchanged, still the sole write path) |
| `GET /research/bars` no-param path | OK — byte-identical | `routes.py:1724-1726`: `if symbol is None and timeframe is None: records, errors = store.list(); return {...}` — identical to the pre-iteration body, index never consulted. Asserted by new test `test_no_param_get_is_byte_identical_to_a_direct_store_list_call` (`test_bars_api.py:325-343`), which diffs the route response against a direct `BarStore(...).list()` call |
| `GET /research/bars?symbol=&timeframe=` filtered path | OK | `routes.py:1728-1745`: filters via `index.list(...)` then resolves **every** hit through `store.get(hit.series_id)` (never returns index-only data); corrupt/missing hits surface in `integrity_errors`, never fabricated. Sort key `(created_utc, id)` matches `BarStore.list()`'s own sort (`bars.py:207`) — same ordering as the canonical source |
| `feed="yahoo"` provenance | OK — untouched | `routes.py:1682` (`feed = adapter.name if isinstance(adapter, YahooAdapter) else ...`) is unchanged context, not part of this diff's edited lines |
| `config_fingerprint` (`4d665603569b9dbf`) | OK | `apps/backend/app/config.py` does not appear anywhere in the diff; `bar_index.py` takes a bare DI'd path string and never imports/reads `CONFIG` (confirmed by grep — zero `CONFIG`/`config_fingerprint` references in the file) |

No duplicate computation found: `BarIndex` never independently derives a checksum, bar count, or
candle — every field it stores is copied verbatim from the `meta` dict `store.record()` already
returned (`bar_index.py:107-119`, `_params_from_meta` at `:161-171`), and every read path resolves
back through `store.get()`/`store.list()` before serving. This is squarely the blueprint's own
description of the row ("OWNS NOTHING... a cache, never a source of truth") implemented as
specified — not a re-derivation of an existing value, so not even a borderline A5 case.

## Information Architecture check

`Frontend Present: no` for this iteration, confirmed by `reports/phase-goal-yahoo_fetch-iter-3-ui-surface-map.md`
("N/A — Backend-only phase... No UI surfaces affected.") and independently by the diff itself: no
file under `apps/frontend/` is touched, and no route/page/nav file (`NavBar.tsx`, router config,
`meta.py` `UI_ROUTES`) appears in the diff. The additive `?symbol=&timeframe=` query params are a
filter on the existing `GET /research/bars` endpoint, not a new route — there is no new
page/feature for the IA table to evaluate this iteration.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new frontend surface this iteration) | OK — nothing to check | `reports/phase-goal-yahoo_fetch-iter-3-ui-surface-map.md:3`; diff contains no `apps/frontend/*` or nav/router changes |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md`'s bar-store bullet was updated this iteration to replace the stale "Only the daily
  timeframe is available through this free path today" sentence (carried forward as a non-blocking
  advisory in the iter-2 and iter-3 spec notes) with accurate multi-timeframe / 4h-resample /
  two-distinct-error-messages text. This resolves the previously carried advisory rather than
  introducing a new one — noted for completeness, not a violation.
- J-03 adds no user-facing surface for the store-first behavior (by design — the payoff lands in
  J-05's `/structure` fetch control). Nothing to flag: the blueprint's IA table already assigns
  J-03 to the existing `/structure` home with no new route, and this iteration's backend-only scope
  matches that exactly.
