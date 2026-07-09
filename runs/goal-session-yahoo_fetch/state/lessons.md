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
