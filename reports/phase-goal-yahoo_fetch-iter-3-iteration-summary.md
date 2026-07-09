# Iteration Summary — goal-yahoo_fetch-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-09
**Iteration:** 3

## In plain words

**What you can do now:** You can already pick a stock on the Structure page to see its support-and-resistance price levels and zones, compare two trading strategies side by side with a "Champion" badge, watch a live simulated price tape, keep a trading journal, run replay research studies, and check an honest profit scorecard.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The app got quicker and smarter about reusing data it already has: asking for the same stock history twice no longer goes back out to Yahoo Finance — it's handed back instantly from what was already saved (proven live at 19 milliseconds), and saved data can now be searched by stock symbol and time window. If that internal search memory were ever lost, the app rebuilds it perfectly from the safely-saved data, losing nothing.

**What's next:** Next, the app will start computing real support-and-resistance price levels and zones from this real stock data, using the same tools it already trusts for that job, instead of only ever working on empty or simulated data.

## Headline

Fetching the same data twice no longer re-downloads it from Yahoo Finance.

## Direction

**Signal:** improving
**Why:** J-03 (the store-first SQLite bar index) moved from failing to passing this iteration on independently re-verified evidence — a repeat POST makes zero adapter calls, the additive `?symbol=&timeframe=` filter is index-backed, and `reindex()` rebuilds cleanly after DB loss — while J-01, J-02, and J-06 stayed green with zero regression (frozen files byte-identical, `config_fingerprint` unchanged, equivalence 22/22). This is the third consecutive iteration to move a journey from failing to passing with no regressions or anti-goal violations, so direction is healthy. Only J-04 and J-05 remain, and the evaluator's next-step recommendation targets J-04 (real levels on real Yahoo bars) next.

**Trend (last 4 iters):**
- Newly passing this iter: J-03
- Newly passing in last 4 iters total: J-01, J-02, J-03
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 1 of last 4

**Latest evaluator reasoning:** J-03 (quick reuse — store-first fetch backed by a derived SQLite `bar_index`) is newly passing, verified first-hand: the store-first coordinator serves a repeat `(symbol,timeframe,window)` POST from storage with zero adapter calls, the additive `?symbol=&timeframe=` GET filter is index-backed while the no-param GET stays a byte-identical `store.list()`, every served candle is checksum-verified through the frozen JSON `BarStore`, and `reindex()` rebuilds the index after DB loss. The required-still-passing foundation (J-01, J-02, J-06) is re-verified green by frozen byte-identity plus my own test / `config_fingerprint` / engine-equivalence re-run; J-04 and J-05 remain out-of-scope failing. Coherence is COHERENCE-PASS and no anti-goal is violated, so the loop continues toward J-04.

## What was done

- Added `apps/backend/app/research/bar_index.py` — a new derived, rebuildable SQLite index over the canonical JSON `BarStore` (metadata-only: `(symbol, timeframe, window)` → `series_id`/`checksum`/`bar_count`).
- Added a store-first coordinator to `POST /research/bars`: a repeat fetch of an already-stored window is now served instantly from storage with zero Yahoo Finance calls — verified live against real data at 19ms.
- Added an additive `?symbol=&timeframe=` filter to `GET /research/bars`; the no-param response stays byte-identical to before (proven by a dedicated diff test).
- Added `reindex()` — the index can rebuild itself from the permanent saved data after deletion/corruption, reproducing identical lookups.
- Added 14 new tests (10 index unit tests + 4 API tests); full suite now 1197 passed / 6 skipped / 0 failed (audit-confirmed), zero regressions; `config_fingerprint` unchanged (`4d665603569b9dbf`), engine equivalence 22/22.
- Re-verified J-01, J-02, J-06 stay green via frozen-file byte-identity plus an independent test/fingerprint/equivalence re-run.
- Verified 0 target journey(s) pass browser QA — lane SKIPPED (backend-only iteration, `Frontend Present: no`; no UI surface exists to test).

## What's left

- Journey J-04 (Real S/R levels and confluence zones on real Yahoo bars) failing.
- Journey J-05 (Fetch from the app — the Structure page fetch control with Yahoo Finance provenance) failing.
- No on-screen control exists yet to trigger a Yahoo fetch or use the new store-first/filter behavior — still deferred to J-05.
- Bar series recorded before this iteration are not auto-indexed; they need a one-time `reindex()` to become store-first/filterable (already run for the current environment; new fetches index automatically going forward).
- An explicit blank `?symbol=`/`?timeframe=` query silently bypasses the byte-identical no-param path (audit B2, non-blocking) — should be closed before/at J-05 when the Structure page becomes a real caller.
- The GET-filter's corrupted/deleted-indexed-series error branch is untested (audit T1, non-blocking) — the logic mirrors an already-tested POST path.
- `scripts/dev.sh` doesn't reliably kill the full frontend process tree on shutdown — a pre-existing gap, unrelated to this iteration's code.

## Next step

Target **J-04** — real S/R levels and confluence zones on real Yahoo bars. Feed the already-stored real Yahoo bars to the FROZEN era-4 `research/levels.py` and confirm `GET /research/levels?symbol=&as_of=` returns real, non-empty levels and A/B/C confluence zones; that REST and the MCP `levels` proxy agree byte-for-byte; no lookahead (as-of T uses only completed bars); and — the defining acceptance — that no second levels/zone computation path exists (single source of truth; the coherence-auditor stays clean; `levels.py` is read, never re-implemented). Keyless on a committed Yahoo fixture (backend-verifiable). Recommend **full** depth: J-04's acceptance is coherence-critical, so the coherence + audit lanes must run even though no frozen module is touched. Carry-forwards for J-05 (not J-04 blockers): close audit B2 (normalize a blank `?symbol=`/`?timeframe=` to `None`) before/at J-05; ensure any J-05 browser test that pre-seeds a fixture is indexed (via the store-first POST path or a one-off `reindex()`); and the orchestrator must finally provision reachable `:3301`/`:8301` + Chrome MCP before the J-05 pipeline run.

## Assumptions made

- iter-3 · goal-evaluator — Ambiguity: J-03's acceptance and the "fetching is explicit and store-first" anti-goal require that an already-stored window be served without re-hitting Yahoo, but the goal is silent on bar series recorded before this iteration (8 legacy series from iter-1/iter-2 are not auto-indexed). We chose: Scored J-03 passing, treating store-first as satisfied for every window recorded through the era-5 index-on-write flow, and treating pre-iter-3 legacy data as an explicit-migration concern (a one-off `reindex()`), not a violation. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the Era-5 constraints require the SQLite index to have a config-owned DB path while also requiring `config.py` to stay byte-identical — unclear which reading wins if a config field were added for the index DB. We chose: Plan the index DB path as config-owned by anchoring it to the existing config-owned `bar_dir_resolved()` (a co-located sibling DB file), with a `TAPEOLOGY_BAR_INDEX_DB` env override for hermetic tests, so `config.py` stays byte-identical and `config_fingerprint` stays `4d665603569b9dbf`. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: the iter-2 spec required the browser lane to re-verify J-01/J-06 and emit a screenshot, but the lane ran with no services reachable and produced none — the goal is silent on whether a required-still-passing journey may stay passing on non-browser evidence in that case. We chose: Kept J-01 and J-06 passing on backend/structural evidence (`config_fingerprint`, equivalence, and frozen-file byte-identity all re-run and green; J-01's core fetch re-run live; zero frontend bytes changed). Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: `docs/goal.md` enumerates exactly six era-5 Yahoo timeframes and names `8h`/`1mo` as unsupported, but is silent on `15m`, which is both a valid config entry and a yfinance-native interval. We chose: Treat `15m` as Yahoo-unsupported this era, alongside `8h`/`1mo`, following the goal's explicit six-timeframe enumeration rather than expanding scope to a seventh timeframe it never lists. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires both `GET /research/bars/{id}` and the MCP `bars` proxy to return the series byte-for-byte, but no Yahoo-specific MCP test was added — unclear whether a per-feed MCP proof is required or the generic proxy guarantee suffices. We chose: Scored J-01 passing, accepting the MCP half on the architectural byte-identity argument — the MCP layer has zero feed-awareness and already passes `response.text` verbatim, proven byte-identical by an existing unmodified test. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the spec named browser checks for J-05/J-06, but the lean baseline pipeline never ran the browser-qa lane — unclear whether an absent-capability journey may be scored without the browser leg the spec names. We chose: Scored J-05 failing and J-06 already_passing on code/test evidence instead — both provably supported by source inspection, the green suite, the config-fingerprint match, and an empty `apps/` diff. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-yahoo_fetch-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-yahoo_fetch-iter-3-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-yahoo_fetch-iter-3-review.md |
| Browser QA | SKIPPED | reports/phase-goal-yahoo_fetch-iter-3-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-yahoo_fetch-iter-3-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-yahoo_fetch-iter-3-user-visible-changes.md |
| What to click | — | reports/phase-goal-yahoo_fetch-iter-3-what-to-click.md |
| UI surface map | — | reports/phase-goal-yahoo_fetch-iter-3-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-yahoo_fetch-iter-3-ui-test-plan.md |
| QA | PASS | reports/qa/goal-yahoo_fetch-iter-3-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-yahoo_fetch-iter-3-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-yahoo_fetch-iter-3-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-yahoo_fetch/iter-3/eval.md |
| Journey history | — | runs/goal-session-yahoo_fetch/state/journey-history.json |
