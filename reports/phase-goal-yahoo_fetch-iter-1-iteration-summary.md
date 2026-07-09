# Iteration Summary — goal-yahoo_fetch-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-09
**Iteration:** 1

## In plain words

**What you can do now:** You can already pick a stock on the Structure page to see its support-and-resistance price levels and zones, compare two trading strategies side by side with a "Champion" badge, watch a live simulated price tape, keep a trading journal, run replay research studies, and check an honest profit scorecard.

**What changed this time:** Behind-the-scenes work — nothing new to click yet. The app quietly gained the ability to pull real daily stock prices from Yahoo Finance for free, with no account needed, and to save that history permanently and safely. Everything that already worked was re-checked and still behaves exactly as before, including a careful check that the new data source never shows up in the wrong place.

**What's next:** Next, the app will learn to fetch more time windows — weekly, hourly, and a derived 4-hour view — from Yahoo Finance, honestly, on the way to a real "Fetch from Yahoo Finance" button on the Structure page.

## Headline

Keyless Yahoo Finance daily bar adapter ships as the default bar-fetch vendor (API/MCP-only, no UI yet)

## Direction

**Signal:** improving
**Why:** Iteration 1 shipped the keyless Yahoo Finance daily bar adapter and made it the default bar-fetch vendor, moving J-01 from failing to passing with zero regression on J-06 (independently re-verified: `config_fingerprint` unchanged, 22/22 equivalence tests, and a browser-confirmed feed badge that still reads "Simulated"). J-02–J-05 remain failing but are explicitly out of scope this round (not attempted-and-failed); the evaluator's next-step recommendation targets J-02 (the full timeframe set + honest 4h resample) next.

**Trend (last 2 iters):**
- Newly passing this iter: J-01
- Newly passing in last 2 iters total: J-01
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 1 of last 2 (iter-0, the verify-only baseline)

**Latest evaluator reasoning:** The keyless Yahoo daily-bar adapter plus the bar-fetch vendor default landed and J-01 is now `passing` on convergent evidence: a real `POST /research/bars` (AAPL) returns HTTP 200 with `feed="yahoo"`, `bar_count=24`, real bars, which render on `/structure` as a genuine AAPL candlestick chart (~$270–320, high-precision prices — not fabricated round numbers) with S/R lines and 28 Class-C zones. The crux anti-goal ("Yahoo default must not break the Alpaca path") is cleanly met — `main.py` has zero diff, the new default is confined to `get_bar_fetch_adapter()` on `POST /research/bars`, and the live/simulated feed badge still reads "Simulated" (UT-06). J-06 foundation sentinel stays green; J-02–J-05 remain `failing` (out of scope this iteration, not attempted-and-failed), so this is not GOAL_ACHIEVED — progress was made, so CONTINUE.

## What was done

- Added `YahooAdapter` (`apps/backend/app/providers/adapters/yahoo.py`) — keyless, bars-only, `name="yahoo"`, `"1d"`-only interval mapping, honest empty-tuple on an unmapped timeframe or empty vendor response (no fabricated bars).
- Added a bar-fetch-only resolver (`get_bar_fetch_adapter()` in `research/routes.py`) that defaults `POST /research/bars` to Yahoo, while the live accessor `get_adapter()` and the studies accessor `get_study_market_adapter()` stay byte-identical and untouched.
- Sourced the `feed="yahoo"` stamp from the adapter itself (single owner); Alpaca-served fetches keep the pre-existing `"sip"` stamp unchanged.
- Pinned `yfinance==1.5.1` in `requirements.txt` (confined-to-adapter comment) and added it to the `python.allowlist` in `config/install-security-policy.json`; the supply-chain install gate returned ALLOW.
- Added 18 new tests (14 adapter unit tests, 3 route/store tests, 1 gated live-integration test) plus a committed real Yahoo fixture; full suite now 1163 passed / 2 skipped, `config_fingerprint` unchanged (`4d665603569b9dbf`), and the two equivalence suites (22/22) stayed byte-identical.
- Ran a real, live, keyless Yahoo daily fetch for AAPL under the `integration` marker (`TAPEOLOGY_LIVE_INTEGRATION=1`) — passed.
- Verified 2 target journey(s) pass browser QA (J-01, J-06) — 14/14 UI tests passed, including the two named crux-risk regression checks (UT-06 feed badge, UT-07 Structure render) and the exploratory UT-14 proof that a live Yahoo fetch reaches the Structure chart.

## What's left

- Journey J-02 (The full timeframe set, including honestly-resampled 4h) failing.
- Journey J-03 (Quick reuse — store-first fetch backed by a derived SQLite index) failing.
- Journey J-04 (Real S/R levels and confluence zones on real Yahoo bars) failing.
- Journey J-05 (Fetch from the app — the Structure page fetch control with Yahoo Finance provenance) failing.
- No on-screen control exists yet to trigger a Yahoo fetch — deferred to J-05.
- `feed: "yahoo"` has no human-readable label anywhere in the UI yet.
- Only the daily timeframe is mapped; other timeframes return a generic empty-window error rather than a specific "not supported yet" message (J-02 scope).
- No production-reachable way to request an Alpaca bar fetch through `POST /research/bars` (test-injection only) — documented, non-blocking gap (audit finding B1).

## Next step

Iteration 2 targets **J-02** — the full timeframe set (`1w/1d/4h/1h/5m/1m`) with the deterministic `4h` resample-from-`1h` (open=first/high=max/low=min/close=last/volume=sum, session-aligned, honest partial trailing bucket) and the out-of-retention / unsupported-timeframe honest-neutral-error taxonomy. Run **full** depth: the `4h` resampler is the era's single named new backend computation and carries its own critical anti-goal ("`4h` is honestly derived") plus the "no fabricated bars" rail, so the audit + coherence lanes must run (coherence should confirm the derived-`4h` value stays single-owner and honestly labelled). Carry forward the fixture-location lesson: a `feed="yahoo"` fixture must live under `apps/backend/tests/fixtures/yahoo/`, never `tests/fixtures/bars/` (a frozen test blanket-asserts `feed=="sip"` over that whole dir).

## Assumptions made

- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires both `GET /research/bars/{id}` and the MCP `bars` proxy to return the series byte-for-byte, but no Yahoo-specific MCP test was added — the goal text doesn't say whether a per-feed MCP proof is required or the generic proxy guarantee suffices. We chose: Scored J-01 passing, accepting the MCP half on the architectural byte-identity argument — the MCP layer has zero feed-awareness and passes `response.text` verbatim, already proven byte-identical by an existing, unmodified test. A Yahoo-specific duplicate would be redundant coverage, not new defense. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: The spec's TESTING REQUIREMENTS named browser checks for J-05 and J-06, but the lean baseline pipeline never ran the browser-qa lane (no screenshots, no `ui-test-results.md`); the spec doesn't say whether an absent-capability journey may be scored without the browser leg it names. We chose: Scored J-05 failing and J-06 already_passing on code/test evidence instead — both provably supported by source inspection, the green suite, the `config_fingerprint` match, and an empty `apps/` diff; a browser screenshot would only re-show the same absence/unchanged surfaces. Reversible: yes

## Quick verify

From `reports/phase-goal-yahoo_fetch-iter-1-what-to-click.md`:

1. Open `http://localhost:3301/` in your browser.
2. Click into the field with placeholder text "Ticker e.g. SIM-BUYER" and type `SIM-BUYER`, then click the "Watch" button next to it.
3. Look at the small badge that says "feed" next to the "Watching SIM-BUYER" text near the top of the page.
4. Click "Stop" (next to "Watching SIM-BUYER"), then click "Structure" in the top navigation bar.
5. Type `AAPL` into the "Symbol" field and `2026-06-05T00:00:00Z` into the "As-of (UTC, ISO-8601)" field, then click "Load".

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-yahoo_fetch-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-yahoo_fetch-iter-1-dev.md |
| Review | PASS | reports/reviews/goal-yahoo_fetch-iter-1-review.md |
| Browser QA | PASS | reports/phase-goal-yahoo_fetch-iter-1-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-yahoo_fetch-iter-1-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-yahoo_fetch-iter-1-user-visible-changes.md |
| What to click | — | reports/phase-goal-yahoo_fetch-iter-1-what-to-click.md |
| UI surface map | — | reports/phase-goal-yahoo_fetch-iter-1-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-yahoo_fetch-iter-1-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-yahoo_fetch-iter-1-ux-regression.md |
| QA | PASS | reports/qa/goal-yahoo_fetch-iter-1-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-yahoo_fetch-iter-1-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-yahoo_fetch-iter-1-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-yahoo_fetch/iter-1/eval.md |
| Journey history | — | runs/goal-session-yahoo_fetch/state/journey-history.json |
