# lessons.md — archive

Entries moved out of `lessons.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-07-27T20:07:55Z: moved 6 entries (keep-iters=5) -->

## iter-0 — 2026-07-25T03:25:01+01:00

**Verdict:** CONTINUE
**Lesson:** The new J-07 golden (`runs/goal-session-desk/journey-scripts/J-07.json`) step 8 asserts
the text `300.11` — a post-Load, cache-warmth-dependent async value — on the 15 s default timeout,
which is the exact shape of assertion that cost a full iteration in the `yahoo_fetch` era (headless
matcher misses async-rendered list text). Re-point it at a statically-rendered `/structure` shell
string (or widen its timeout) BEFORE the replay lane guards J-07; if replay FAILs step 8 while the
LLM lane passes, the merged results file wins and it is a golden false negative, not a regression.
**Applies to:** any iteration where J-07 rides the deterministic replay lane, and every new golden
script written this era.

## iter-0 — 2026-07-25T03:25:01+01:00

**Verdict:** CONTINUE
**Lesson:** On a freshly-started scoped browser-QA backend, the first
`GET /research/setups?symbol=AAPL` took ~9–11 min at ~96% CPU (warm re-call: 0.84 s) — the
`/structure` Case Studies skeleton is honest, not hung, but any browser pass that clicks a Case
Study needs the cache warmed first or a wait budget far past the usual per-command timeout.
**Applies to:** every browser-QA dispatch against `.data/scoped_browser_qa`; and read it as live
precedent when building J-02's "coverage GET is index-read fast, never re-hashes the store"
requirement (T-4).

## iter-1 — 2026-07-25T06:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** The era's Path-A protocol only protects `config_fingerprint()` — there is a SECOND,
unnamed whole-config hash, `edge_report_cache._config_content_hash` (`apps/backend/app/research/edge_report_cache.py:165-169`),
which hashes `dataclasses.asdict(config)` with NO exclusion set and keys four durable caches
(`setups_scan_cache`, `tradability_cache`, `edge_report_cache`, `edge_report_backtest_cache`). Adding
the four `desk_universe_*` fields moved it to `dc0271c15a26…` (I confirmed the change myself), so
every pre-diff cache row is unreachable: the real-data `GET /research/setups` is cold again (~9–11 min
first call) and `/structure` Load is back to ~21.6 s. Served values are unaffected (no desk field is
read outside `config.py` + the two desk modules), so this is pure latency — but it re-arms exactly the
false-negative trap that has burned prior browser passes.
**Applies to:** every era-B iteration that adds ANY `Config` field (i.e. most of them), and
unconditionally to whichever iteration next dispatches browser QA (expected J-04): warm
`/research/setups` and `/structure` Load on the real data dir first, and budget for the cold call.

## iter-2 — 2026-07-25T08:24:13+01:00

**Verdict:** CONTINUE
**Lesson:** J-02's delivered truth-table test used synthetic `AAA…EEE` symbols, so goal.md's LITERAL
clause ("bars-present for exactly the members the era-open store holds (AAPL/AMD/MSFT)" over the
fixture universe) was asserted by no test — and when I ran it directly against
`tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json` + the real `bar_index`, it passed but
revealed the goal text's own hidden assumption is wrong: MSFT holds `1h`/`1d` rows but **no** `1w`/`4h`,
so era-open coverage is per-`(symbol, timeframe)`, not per-member. Any consumer that treats "this
symbol has bars" as "the whole pinned timeframe set is present" will silently mis-serve MSFT.
**Applies to:** J-03's screen rows and J-04's coverage badges (any code consuming
`GET /research/desk/coverage`); and generally — when a spec's acceptance names concrete real symbols,
execute it against those symbols rather than accepting a synthetic-fixture stand-in as equivalent.

## iter-3 — 2026-07-25T11:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** Two sibling append-only stores in this era now disagree on the SAME failure mode: the
audit made `ScreenStore.record` refuse (`ScreenIntegrityError`) when the 5-pin key's own
deterministic path already holds a checksum-failed file (`desk_screen.py:467-473`, verified live),
while `UniverseStore.record` still `write_text()`s straight over it (`desk_universe.py:418`, iter-1's
audit B3 gap). The general trap: when a store's file path is a pure function of its dedup key, the
"look up by key → not found → write" sequence silently overwrites any file the loader withheld for
failing verification — so every content-addressed store in this codebase needs an explicit
`path.exists()` guard, not just a key lookup.
**Applies to:** any iteration touching `desk_universe.py`, `desk_screen.py`, or adding a new
checksum-verified append-only store (a `record()` whose filename derives from its dedup key)

## iter-3 — 2026-07-25T11:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** A QA report's numbers can silently come from a DIFFERENT data basis than the acceptance
clause names: `reports/qa/goal-desk-iter-3-qa.md` TC-01 records AAPL as `class A, distance_bps 0.335,
band_score 97.0` "verified against the committed fixture universe", but that run was against the real
ambient 101-member `.data/` store — the committed fixture universe + fixture bars actually yield
`class C, 2.348 bps, score 57.0` (my run, and the auditor's independent probe). The same report also
carried a fabricated single-flight "queue" mechanism the auditor had to correct in place. Never carry
a QA numeric into a golden or a spec without re-deriving it against the named data basis.
**Applies to:** any iteration whose spec quotes measured values from a QA/dev report, and any golden
or fixture assertion authored from one

