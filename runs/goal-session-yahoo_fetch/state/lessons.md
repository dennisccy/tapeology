# Goal Session yahoo_fetch — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-08T23:55:00Z

**Verdict:** CONTINUE
**Lesson:** The lean verify-only baseline pipeline ran decompose→develop→review only —
the browser-qa lane did NOT execute (`status.json browser_checks_run:false`, empty
`reports/qa/goal-yahoo_fetch-iter-0-evidence/`, no `ui-test-results.md`) and no
`coherence.md` was produced, even though the spec's TESTING REQUIREMENTS named browser
checks for J-05/J-06. Baseline statuses survived on code/test evidence, but any future
iteration that claims J-05 (or any browser-verifiable journey) `passing` MUST confirm the
browser lane actually ran and emitted a screenshot — a "passing" without one is unevidenced.
**Applies to:** any iter targeting J-05 or the `/structure` fetch control; any lean iteration
whose spec requests browser verification; the J-06 foundation sentinel once code starts changing.

## iter-1 — 2026-07-09T03:30:00Z

**Verdict:** CONTINUE
**Lesson:** A committed `feed="yahoo"` bar fixture must NOT be placed under `apps/backend/tests/fixtures/bars/` — the frozen `test_bars.py::test_committed_fixture_loads_through_the_real_store_path_keyless` runs `BarStore(FIXTURE_BAR_DIR).list()` over the WHOLE dir and blanket-asserts `meta["feed"] == CONFIG.historical_feed` ("sip") for every record, so a yahoo-feed file there breaks a frozen test. The dev correctly mirrored the pre-existing `tests/fixtures/alpaca/` precedent and used `tests/fixtures/yahoo/` instead. The bar-fetch vendor default is also confined to a NEW `get_bar_fetch_adapter()` on `POST /research/bars` only — never the shared `get_study_market_adapter()` or the global `get_adapter()` — because Yahoo is bars-only and would break studies/live/tick/search if the shared resolver were flipped.
**Applies to:** any J-02–J-05 iteration adding a Yahoo (`feed="yahoo"`) test fixture, and any future adapter that is not a full `MarketDataAdapter` (bars-only / ticks-only) being wired as a default — confine it to its capability's resolver, never the shared/global accessor.

## iter-2 — 2026-07-09T17:20:00Z

**Verdict:** CONTINUE
**Lesson:** The browser-qa lane silently no-op'd again (`ui-test-results.md` SKIPPED 0/10, evidence
dir empty) — this time on a FULL-depth iter, because neither frontend (:3301) nor backend (:8301)
was reachable (curl exit 7) when the lane ran, not because it was omitted. For a backend-only iter
whose required-still-passing journeys are UI journeys (J-01/J-06), the actual regression net was the
`git diff <snapshot> -- apps/frontend/` == empty invariant plus a live backend re-run of J-01's
keyless fetch and my own fingerprint/equivalence/byte-identity re-check of J-06 — the browser
screenshot the spec's DoD asked for was never the load-bearing evidence for those two journeys.
**Applies to:** J-05 specifically — it is the FIRST iter with genuinely new `/structure` UI, so its
browser lane MUST have both services started and Chrome MCP available or J-05 cannot be evidenced at
all (the zero-frontend-diff fallback that covered iter-2 will not exist once the fetch control lands).
The orchestrator should provision/verify reachable :3301/:8301 before the J-05 pipeline run.

## iter-3 — 2026-07-09T21:05:00Z

**Verdict:** CONTINUE
**Lesson:** The route-level semantics of a duplicate `POST /research/bars` CHANGED this iter: an
exact-repeat POST of the same `(symbol, timeframe, window)` now returns **200, served store-first**
(zero adapter calls), NOT the old **409**. The decomposer's spec asserted "no route-level test asserts
409 on a duplicate-window POST," but one existed (`test_duplicate_content_is_refused_409`); the dev
correctly transformed it into `test_duplicate_window_post_is_served_store_first_no_second_fetch`. The
FROZEN store-LEVEL content-duplicate 409 (a DIFFERENT window whose fetched content happens to match)
is untouched and still covered by `test_bars.py::test_rerecording_identical_content_is_refused`.
**Applies to:** any future iter touching `POST /research/bars` or bar-series duplicate/idempotence
semantics — "repeat window = 200 store-first" is now the route contract; do not "restore" a 409 there.
Directly relevant to J-05's `/structure` fetch-control test expectations.

## iter-4 — 2026-07-10T00:50:13Z

**Verdict:** CONTINUE
**Lesson:** J-04 was a clean verify-and-lock (zero production diff) but it LOCKS IN a latent trap: frozen `compute_levels` (`levels.py:306`) selects a symbol's series by SYMBOL ALONE (feed-blind), and `_select_one_series_per_timeframe` (`levels.py:171-182`) dedups only WITHIN a (symbol, timeframe) pair — so across different timeframes it will pool a `feed="yahoo"` series and a `feed="sip"` series into one confluence cluster. The critical "never pooled across feeds" rail is currently satisfied ONLY because the keyless path gives a symbol a single feed; it is avoided-by-scoping, not enforced.
**Applies to:** any iter (J-05+) that lets a symbol accumulate more than one feed over overlapping timeframes, or any iter tempted to "fix" segregation inside `levels.py` — the fix MUST be a versioned feed-scoped path BESIDE frozen `levels.py` (fingerprint-locked; mutating it is itself a critical anti-goal), never an edit to it.
