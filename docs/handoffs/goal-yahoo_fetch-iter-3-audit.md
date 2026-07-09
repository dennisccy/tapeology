# goal-yahoo_fetch-iter-3 Audit Report

**Date:** 2026-07-09
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-03's store-first mechanism is genuinely and correctly implemented, not merely wired. I traced
the unhappy paths of every dev claim: the lookup key `(symbol, body.timeframe, body.start,
body.end)` provably matches the insert key because `store.record` persists `body.start`/`body.end`
**verbatim** into `meta["window_start_utc"]`/`["window_end_utc"]` (`bars.py:247-248`) and the route
passes them verbatim (`routes.py:1688-1689`) — so a repeat POST really does hit in production, and
every hit is re-checksum-verified through the frozen `BarStore` before it is served. I independently
re-ran the full suite (exit 0: **1197 passed / 6 skipped / 0 failed**, a +14 delta that matches the
14 new tests exactly), the targeted+equivalence subset (70/70), and confirmed
`config_fingerprint == 4d665603569b9dbf` by direct execution. The goal is achieved; three documented
GAP-level limitations (empty-string query param, un-indexed legacy series, one untested error
branch) are real but acceptable and none compromise the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (not fixed): `get_bar_index()` opens a fresh sqlite3 connection per request with no `close()`**
`routes.py:1546-1557` constructs a new `BarIndex` (new `sqlite3.connect` + PRAGMA + `CREATE TABLE
IF NOT EXISTS`) on every `POST`/`GET /research/bars`, unlike the codebase's other sqlite3 store
(`JournalStore`, a lifespan singleton that is explicitly closed at shutdown). Verified this is not a
leak under CPython: `BarIndex` holds the only reference to `self._conn`, so at end of request the
`index` dependency is dropped, refcount hits zero, and `sqlite3.Connection`'s finalizer closes the
handle (WAL checkpoint on close). Functionally correct for a low-frequency metadata cache; a minor
cleanliness/perf cost only. Matches the reviewer's MINOR. Not fixed — a `close()`/registry refactor
is scope creep for J-03 and touches no acceptance criterion.

**B2 — GAP (not fixed): an explicit empty-string `?symbol=` / `?timeframe=` bypasses the byte-identical path**
`routes.py:1724` gates the verbatim `store.list()` path on `symbol is None and timeframe is None`.
An explicit `?symbol=` sends `symbol=""` (not `None`), so the request falls into the index-filtered
branch; `normalized_symbol` then becomes `None` (`routes.py:1728`, the `if symbol` guard), so
`index.list(None, None)` returns **all indexed** entries — which can under-represent un-indexed
legacy series (see B3). No in-scope caller triggers this: the MCP `bars` tool declares
`inputSchema=_object_schema({})` (no params, `mcp/__init__.py:188`) and `Frontend Present: no`. It
does not fabricate — it under-represents. Becomes relevant at J-05 (UI). Disclosed in the review
(NOTE) and dev handoff. The DoD scopes byte-identity to the *no-param* call, which
`test_no_param_get_is_byte_identical_to_a_direct_store_list_call` proves — so this is a documented
limitation, not a DoD violation. A one-line fix (normalize blank → `None` before the guard) exists
if J-05 needs it; not applied here to avoid scope creep on a path with no in-scope caller.

**B3 — GAP (not fixed): bar series recorded before iter-3 are not auto-indexed**
The index only grows additively via `index.insert(meta)` after a store-first `POST`
(`routes.py:1700`); "any background/ambient re-indexing or polling" is explicitly OUT OF SCOPE
(plan + anti-goal "Persistence stays scoped"). Consequence I traced: for a legacy window already on
disk but absent from the index, a repeat `POST` **misses** the index, runs a real Yahoo fetch, then
`store.record` raises `BarSeriesAlreadyRegistered` → **409** — i.e. the anti-goal "an already-stored
window is served from storage without re-hitting Yahoo" does not hold for pre-iter-3 data until a
one-time `reindex()`. For data recorded within this era's own flow (indexed on write) store-first
works fully, which is exactly what the DoD's acceptance test exercises. Dev disclosed this, ran a
one-off `reindex()` against the real `.data/`, and left it in a correct state. Acceptable migration
gap; an auto-reindex hook would itself brush the "no ambient re-indexing" boundary. Not fixed.

### Frontend Findings

None — `Frontend Present: no`; no `apps/frontend/**` change. `user-visible-changes` report correctly
states "Backend-only phase … No user-visible changes" (no misleading "shipped to UI" claim).

### Test Findings

**T1 — GAP (not fixed): the GET-filter's corrupted/deleted-indexed-series error branch is untested**
`routes.py:1735-1743` catches `BarSeriesNotFound`/`BarSeriesIntegrityError` from `store.get(...)` in
the filter path and surfaces them in `integrity_errors`. Correct by inspection (it mirrors the
POST self-heal and never fabricates), but has no dedicated test — the analogous POST path
(`test_store_first_hit_pointing_at_a_corrupted_series_self_heals_via_a_refetch`) and the no-param
corrupt-file path (`test_corrupted_bar_series_file_surfaces_explicitly_on_detail_and_list`) are both
tested, this filter-path variant is not. Matches the reviewer's MINOR. Documented rather than
fixed: the branch is demonstrably correct and mirrors two already-tested paths; adding the test is a
nice-to-have, not a correctness gate.

**Process note (not a code finding):** the DoD lists "coherence returns COHERENCE-PASS," but the
formal coherence-auditor report for iter-3 has not been produced yet (only iter-1/iter-2 exist under
`runs/goal-session-yahoo_fetch/`; that gate runs downstream in the goal loop). I assessed the
coherence-relevant anti-goals directly from the diff and found no violation — see §3.

---

## 3. Domain Assessment

The core domain question for J-03 is whether the SQLite index stays a **derived cache that owns
nothing** while the JSON `BarStore` remains the single source of truth. Traced against the code and
the critical anti-goals:

- **Index owns nothing / never a source of truth.** `bar_index.py` stores metadata only
  (`series_id`, `checksum`, `bar_count` keyed by the tuple). A hit is served **only** via
  `store.get(hit.series_id)` (`routes.py:1638`), which recomputes both checksums on load
  (`bars.py:158-175`); the index's own `checksum` column is never trusted to serve a candle. Loss is
  harmless: `reindex()` drops + repopulates from `BarStore.list()`'s healthy records and reproduces
  identical lookups (`test_reindex_after_deleting_the_db_file_reproduces_identical_lookups`, passing).
  Verified — anti-goal satisfied.
- **No fabrication.** A hit whose backing file was deleted/corrupted since indexing raises inside
  `store.get`, is caught, and falls through to a real re-fetch rather than serving stale/partial data
  (`routes.py:1639-1644`); proven end-to-end by
  `test_store_first_hit_pointing_at_a_corrupted_series_self_heals_via_a_refetch` (asserts a NEW id,
  `fetch_bars_calls == 2`, and the orphan still surfaced in `integrity_errors`). Verified.
- **No re-tag/pool of `feed="yahoo"` with `sip`.** The hit serves the stored series verbatim; feed
  is never rewritten. `reindex` and `insert` copy `meta` fields, never re-derive feed. Verified.
- **Single source of truth / byte-identical no-param path.** The no-param branch is a verbatim
  `store.list()` return (`routes.py:1724-1726`), proven byte-identical by a direct-diff test; the
  MCP proxy stays param-less. No contract value is recomputed — the filter serves the existing
  bar-series value owned by `BarStore`. Verified.
- **Frozen foundations byte-identical.** `git status` confirms only `routes.py` and
  `test_bars_api.py` are modified; `config.py`, `bars.py`, `store.py`, `levels.py`, `strategies.py`,
  `backtests.py`, the tape engine, and both adapters are untouched. `config_fingerprint` reproduced
  as `4d665603569b9dbf`. The store-level content-duplicate 409 stays covered by the unmodified
  `test_bars.py::test_rerecording_identical_content_is_refused` (confirmed present, passing). The
  moved `symbol` normalization is defined exactly once and changes no existing consumer's input
  (fetch/record already received the normalized symbol pre-J-03), which is why all 12 pre-existing
  `test_bars_api.py` tests pass unmodified. Verified.

The domain logic is correct and honest. The store-first path cannot serve unverified data by
construction, and every failure mode is explicit (miss → fetch; corrupt/missing hit → fetch;
un-fetchable → the existing 4xx/5xx taxonomy).

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found. All findings are GAP/OBSERVATION level, where a fix
would be scope creep (the auditor's rule is to document, not fix, these). The implementation was
verified faithful to the spec by direct execution and code tracing.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

**Proceed to the goal-mode evaluator / next iteration (J-04).** J-03 is complete and verified:
store-first serves a repeat window from storage with zero adapter calls, the additive
`?symbol=&timeframe=` filter is index-backed, the no-param path is byte-identical, `reindex()` is a
faithful rebuild, the fingerprint is unchanged, and the full suite is green (exit 0; 1197 passed / 6
skipped / 0 failed; +14 new tests matching the delta exactly) with no frozen file touched.

Carry-forward for later iterations (not J-03 blockers):
- **B2** (normalize blank `?symbol=`/`?timeframe=` → `None`) should be closed **before or as part of
  J-05**, when the `/structure` UI becomes a real caller that could submit empty form fields.
- **B3**: an operator upgrading a real deployment must run a one-time `reindex()` so pre-iter-3 data
  becomes store-first/filterable; if J-04+ ever needs legacy data served store-first, decide then
  whether an explicit (non-ambient) reindex trigger is in scope.
- **T1**: add the GET-filter corrupt-series test opportunistically in a future bars-touching
  iteration.
- Ensure the downstream **coherence-auditor** step runs for iter-3 (its report is not yet present);
  my independent read is COHERENCE-PASS-equivalent.
