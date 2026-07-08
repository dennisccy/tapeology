# goal-lint report — docs/goal.md

Run: 2026-07-09 · deterministic exit: 1 · semantic findings: 2

## Deterministic lint (goal_lint.py)

```
[goal-lint] WARN aspirational-anti-goal line 362: anti-goal "** is honestly derived.** It is a pure, deterministic resample of real  bars, unit-tested for OHLC" has no checkable condition — phrase it as a veto rule (prohibition or measurable bound)
[goal-lint] WARN aspirational-anti-goal line 377: anti-goal "**Dependency discipline.**  is pinned in  (confined to ) and" has no checkable condition — phrase it as a veto rule (prohibition or measurable bound)
[goal-lint] docs/goal.md: 0 error(s), 2 warning(s) — advisory: lint never blocks the engine (CHAIN_GOAL_LINT=false to silence)
```

Note: both warnings are **false positives from inline-`code`-span stripping** — the linter deletes the backticked
tokens (`` `4h` ``/`` `1h` `` on 362; `` `yfinance` ``/`` `requirements.txt` ``/`` `adapters/yahoo.py` `` on 377)
and then only sees the descriptive lead, missing the real veto clauses that follow ("never presented as a
vendor-native fetch and never fabricated"; "no unpinned/dynamic install, no other new runtime dependency").
Both anti-goals ARE checkable as written. If you want a clean lint run, reorder each to lead with the
prohibition (paste-ready versions in the Summary).

## Semantic findings

### Not independently runnable — line 266 (J-04)

> 1. With real Yahoo bars stored for a symbol, call `GET /research/levels?symbol=<S>&as_of=<ISO-T>` and

- **Problem:** J-04 opens by assuming bars are already stored (from J-01/J-02) but gives itself no setup step; from a fresh checkout its only stored bars are the committed fixture, and that dependency lives only in the evidence tag — so a reviewer or a fresh run could hit an empty `levels` result and misjudge the journey as failing.
- **Suggested rewrite:** `1. Given the committed Yahoo fixture from J-01 (present in `tests/fixtures/bars/`), or after fetching bars via J-01's flow, call `GET /research/levels?symbol=<the fixture's symbol>&as_of=<an ISO-T inside the fixture window>` and`

### Steps require guessing (concrete input value) — line 280 (J-05)

> 1. On `/structure`, add a fetch control — symbol (reuse `SymbolSearch`) + timeframe + date range + a

- **Problem:** J-05 is the one browser-verified journey, but neither its steps nor its acceptance name the concrete symbol / timeframe / date-range to enter — and the "pre-seeded committed fixture" it must match is only created later in J-01. A browser-qa agent would have to invent inputs, and inventing a symbol not in the fixture forces a live network fetch (defeating the "keyless, store-first, no network" verification).
- **Suggested rewrite:** append to step 2 (or the Acceptance): `enter the exact symbol, timeframe, and date range that J-01 committed as the Yahoo fixture (e.g. `AAPL` / `1d` / <fixture window>, recorded in the fixture's README) so the click is a store-first hit with no network; assert the candles for that symbol and the A/B/C zone table render and the provenance badge reads "Yahoo Finance".`

## Summary

Strong contract overall: values are consistently pinned in the Data Contract (`feed="yahoo"`, levels/zones,
the index-owns-nothing rule), success criteria are all measurable, and the external-network surface is
well-bounded (explicit + store-first + honest-error + pinned dep). Both deterministic warnings are linter
code-stripping artifacts, not real gaps. **Highest-impact fix:** name the concrete fixture symbol/timeframe/
window in J-04 and J-05 (findings above) — they are the two journeys that lean on the committed fixture as
implicit shared setup, and pinning the inputs is what makes the browser + levels checks runnable without
guessing. Calibration note (not a defect): J-01–J-04 are backend/research journeys observable via REST/MCP/
automated tests, not the browser — correct for this project and consistent with prior eras; only J-05 (and the
J-06 spot-check) are browser-visible. Optional lint-silencer rewrites: line 362 → `- **4h bars are never
fabricated or presented as vendor-native.** They are a pure, deterministic resample of real 1h bars,
unit-tested for OHLC aggregation and bucket alignment. *(critical)*`; line 377 → `- **No unpinned or extra
dependencies.** yfinance is pinned in requirements.txt (confined to adapters/yahoo.py) and added to the
install-security-policy allowlist; no other new runtime dependency. *(critical)*`
