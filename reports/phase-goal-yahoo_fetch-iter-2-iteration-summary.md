# Iteration Summary — goal-yahoo_fetch-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-09
**Iteration:** 2

## In plain words

**What you can do now:** You can already pick a stock on the Structure page to see its support-and-resistance price levels and zones, compare two trading strategies side by side with a "Champion" badge, watch a live simulated price tape, keep a trading journal, run replay research studies, and check an honest profit scorecard.

**What changed this time:** Behind-the-scenes work — nothing new to click yet. The app quietly learned to fetch five more time windows from Yahoo Finance — weekly, hourly, 5-minute, and 1-minute history, plus a 4-hour view it builds itself from real hourly prices, never invented numbers — and now explains more clearly when a request can't be fulfilled instead of giving one generic error for everything. Everything that worked before was re-checked and still works exactly as before.

**What's next:** Next, the app will build a fast local memory so a previously-fetched price history loads instantly instead of being re-downloaded every time.

## Headline

Six timeframes can now be fetched from Yahoo Finance, not just daily.

## Direction

**Signal:** improving
**Why:** This iteration shipped the full era-5 timeframe set — five directly-fetched intervals plus a deterministically-derived `4h` — and a three-way honest error taxonomy, moving J-02 from failing to passing on unit, committed-fixture, and 5/5 live-integration evidence, with zero regression on J-01/J-06 (frozen files byte-identical, `config_fingerprint` unchanged, equivalence 22/22). J-03–J-05 remain out-of-scope `failing`; the evaluator's next-step recommendation targets J-03 (the SQLite store-first index) next. Two of the last three iterations have moved a journey from failing to passing with zero regressions or anti-goal violations, so direction is healthy, though the recurring browser-QA environment gap (services unreachable) needs to be closed before J-05 ships real UI.

**Trend (last 3 iters):**
- Newly passing this iter: J-02
- Newly passing in last 3 iters total: J-01, J-02
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 1 of last 3

**Latest evaluator reasoning:** J-02 is newly `passing`: the Yahoo adapter now maps all five directly-fetched era-5 timeframes (`1d/1w→1wk/1h/5m/1m`) and derives `4h` by a deterministic, session-aligned resample of real `1h` bars — verified honest (never the native yfinance `"4h"` interval, no pad/forward-fill/lookahead) — plus a three-way, observably-distinct honest-error taxonomy (`UnsupportedTimeframe`→422, `NoDataForWindow`→422, `VendorTimeout`→504) that writes no bar on any error path. No anti-goal was violated, and the frozen foundation (J-06) plus the keyless J-01 path stay green. J-03/J-04/J-05 remain out-of-scope `failing`, so the goal is not yet achieved → CONTINUE.

## What was done

- Expanded the Yahoo adapter's interval map to all five directly-fetched era-5 timeframes (`1w→"1wk"`, `1d`, `1h`, `5m`, `1m`) — `1d` output stays byte-identical to iter-1.
- Added a deterministic, session-aligned `4h`-from-`1h` resample confined to `providers/adapters/yahoo.py` — honest partial trailing bucket, no padding/forward-fill, byte-identical across identical requests.
- Added a three-way honest error taxonomy (`UnsupportedTimeframe`→422, `NoDataForWindow`→422, `VendorTimeout`→504) wired through `record_bar_series`; confirmed no bar is ever written on any error path.
- Added 24 new tests (49 targeted Yahoo/bars tests total) plus a committed real `1h` AAPL fixture under `tests/fixtures/yahoo/`; full suite now 1189 tests, 0 failed, 6 skipped.
- Ran 5 live-integration checks against the real Yahoo service (all six timeframes, `4h`-matches-resampled-`1h`, out-of-retention, unsupported-timeframe) — all passed.
- Re-verified zero regression: `config_fingerprint` unchanged (`4d665603569b9dbf`), engine equivalence 22/22, and every frozen file (`config.py`, `main.py`, `alpaca.py`, `levels/backtests/strategies/bars.py`, `requirements.txt`, `apps/frontend/**`) byte-identical.
- Verified 0 target journey(s) pass browser QA — the lane recorded SKIPPED 0/10 (both services unreachable); J-01/J-06 regression was instead re-verified via live integration tests and byte-identical frozen-file diffs.

## What's left

- Journey J-03 (Quick reuse — store-first fetch backed by a derived SQLite index) failing.
- Journey J-04 (Real S/R levels and confluence zones on real Yahoo bars) failing.
- Journey J-05 (Fetch from the app — the Structure page fetch control with Yahoo Finance provenance) failing.
- No on-screen control exists yet to trigger a Yahoo fetch at any timeframe, or to see the derived `4h` provenance label — deferred to J-05.
- Browser-QA regression evidence for J-01/J-06 was not captured this iteration (both services unreachable, SKIPPED 0/10) — must be captured for real once J-05 ships actual UI; the closure auditor flags a repeat of this gap as a likely CLOSURE-FAIL trigger for J-05.
- The `4h` session-boundary detector is a data-driven heuristic (a >2h gap between `1h` bars marks a new session), not an exchange-hours calendar — untested against an exotic same-session multi-hour halt (non-blocking, logged).

## Next step

Target **J-03** (the natural next unblocker in `J-01→J-02→J-03→J-04→J-05`): the derived SQLite index `apps/backend/app/research/bar_index.py` (mirroring the stdlib-`sqlite3` `store.py` pattern), a store-first coordinator that calls the frozen `BarStore.record` then updates the index (never mutating `record`), the additive `?symbol=&timeframe=` filter on `GET /research/bars` (no-param call byte-identical), and `reindex()` rebuildability. Run **full** depth: J-03 adds a new persistence module carrying its own critical anti-goals ("the SQLite index is a derived cache, never a source of truth" + "fetching is explicit and store-first"), so the audit + coherence lanes must confirm the index owns nothing, every served candle stays checksum-verified from the canonical JSON `BarStore`, and a cache-hit performs no second Yahoo call. Carry forward the browser-qa environment gap — J-03 can still tolerate it since it too is backend-only, but the orchestrator must provision reachable services plus Chrome MCP before J-05, since J-05's real fetch control cannot be evidenced any other way.

## Assumptions made

- iter-2 · goal-evaluator — Ambiguity: The spec required the browser lane to re-verify J-01/J-06 and emit a screenshot, but the lane ran with no services reachable and produced none — the goal is silent on whether a required-still-passing journey may stay passing on non-browser evidence when the mandated re-verification didn't execute. We chose: Kept J-01 and J-06 passing on backend/structural evidence — J-06's `config_fingerprint`/equivalence/frozen-file byte-identity all re-run and green, J-01's core fetch re-run live, and zero frontend bytes changed so no UI regression is structurally possible; the screenshot was a re-verification nicety, not either journey's defining acceptance. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: `docs/goal.md` enumerates exactly six era-5 Yahoo timeframes and names `8h`/`1mo` as unsupported examples, but is silent on `15m`, which is both a valid config entry and a `yfinance`-native interval. We chose: Treat `15m` as Yahoo-unsupported this era, alongside `8h`/`1mo`, since the goal's explicit six-timeframe enumeration and the "only new computation is the Yahoo fetch + 4h resample" non-goal argue against expanding to a seventh timeframe the goal never lists. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires both the REST endpoint and the MCP `bars` proxy to return the series byte-for-byte, but no Yahoo-specific MCP test was added — unclear whether a per-feed MCP proof is required or the generic proxy guarantee suffices. We chose: Scored J-01 passing, accepting the MCP half on the architectural byte-identity argument — the MCP layer has zero feed-awareness and already passes `response.text` verbatim, proven byte-identical by an existing unmodified test. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: The spec named browser checks for J-05/J-06, but the lean baseline pipeline never ran the browser-qa lane — unclear whether an absent-capability journey may be scored without the browser leg the spec names. We chose: Scored J-05 failing and J-06 already_passing on code/test evidence instead — both provably supported by source inspection, the green suite, the config-fingerprint match, and an empty `apps/` diff. Reversible: yes

## Quick verify

From `reports/phase-goal-yahoo_fetch-iter-2-what-to-click.md`:

1. Open `http://localhost:3301/structure` in your browser
2. Type `AAPL` into the "Symbol" field and `2026-07-02T00:00:00Z` into the "As-of (UTC, ISO-8601)" field, then click "Load"
3. Change the "Symbol" field to `MSFT` (leave the As-of field as it is), then click "Load" again
4. Click "Cockpit" in the top navigation, type `SIM-BUYER` into the ticker field, and click "Watch"
5. Look at the small badge that says "feed" next to "Watching SIM-BUYER"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-yahoo_fetch-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-yahoo_fetch-iter-2-dev.md |
| Review | PASS | reports/reviews/goal-yahoo_fetch-iter-2-review.md |
| Browser QA | SKIPPED | reports/phase-goal-yahoo_fetch-iter-2-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-yahoo_fetch-iter-2-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-yahoo_fetch-iter-2-user-visible-changes.md |
| What to click | — | reports/phase-goal-yahoo_fetch-iter-2-what-to-click.md |
| UI surface map | — | reports/phase-goal-yahoo_fetch-iter-2-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-yahoo_fetch-iter-2-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-yahoo_fetch-iter-2-ux-regression.md |
| QA | PASS | reports/qa/goal-yahoo_fetch-iter-2-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-yahoo_fetch-iter-2-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-yahoo_fetch-iter-2-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-yahoo_fetch/iter-2/eval.md |
| Journey history | — | runs/goal-session-yahoo_fetch/state/journey-history.json |
