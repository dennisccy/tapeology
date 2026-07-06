# Goal Session tape_to_profit_support_resistence — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-05T23:40:40Z

**Verdict:** CONTINUE
**Lesson:** The lean baseline ran only decompose -> develop(no-op) -> review; browser-qa and coherence-auditor never dispatched (empty `reports/qa/...-evidence/`, no `ui-test-results.md`, no `coherence.md`), so J-07's spec-required cockpit browser leg has no screenshot — acceptable ONLY because `git diff <snapshot>..HEAD -- apps/` was empty, making a frontend regression impossible; the sentinel was instead grounded on the zero-diff fact + a self-run equivalence suite (7/7) + config.py:1096 v1-only registry.
**Applies to:** any lean iter that actually changes `apps/frontend/` or cockpit/WebSocket code — it MUST produce real browser-qa screenshot evidence for J-07 (SIM-BUYER->buyer_control, SIM-SELLER->seller_control, /journal /studies /performance renders); zero-diff reasoning no longer covers it.

## iter-1 — 2026-07-06T03:40:00Z

**Verdict:** CONTINUE
**Lesson:** Two config gotchas surfaced building J-01. (1) `apps/backend/app/config.py` is vendor-name-forbidden **even in comments** — `tests/test_real_data_gate.py::test_engine_and_canonical_modules_reference_no_vendor` fails if "Alpaca" appears anywhere in the canonical/engine modules; vendor specifics stay confined to `providers/adapters/alpaca.py` (the dev self-caught this and reworded to "the configured market-data vendor"). (2) `config_fingerprint()` hashes **every** non-excluded `Config` dataclass field against a literal pinned hash (`4d665603569b9dbf`), so ANY new field silently moves the `default` fingerprint and breaks J-07 equivalence unless added to the `excluded` set — the iter-1 plan named only `bar_dir`, but all four new storage/validation fields (`bar_dir`, `bar_timeframes`, `bar_recency_delay_seconds`, `bar_rate_limit_per_minute`) had to be excluded.
**Applies to:** any iter touching `apps/backend/app/config.py` or `providers/adapters/` — especially J-02–J-06, which each add config-owned S/R / confluence / class-threshold / sizing fields: exclude every non-computational new field from `config_fingerprint` and keep vendor names out of config/engine modules, or the J-07 sentinel breaks.

## iter-2 — 2026-07-06T05:15:00Z

**Verdict:** CONTINUE
**Lesson:** The levels endpoint aliases a corrupt *sole* bar series for a symbol to `no_bar_series_for_symbol: true` (identical to "never recorded") — `compute_levels` reads only the healthy half of `BarStore.list()` and discards `integrity_errors`. Honest-empty (nothing fabricated) and out of J-02's scoped states, but the session anti-goal lists "corrupt file" among the failure modes that must surface a *distinct* state, and the corrupt case IS surfaced distinctly at its owner (`GET /research/bars`) — so it is a deferred seam, not a defect.
**Applies to:** J-03 (and any iter that consumes `compute_levels` / touches `apps/backend/app/research/levels.py`) — decide whether a corrupt sole series needs its own honest state at the levels endpoint before building on top of it.

## iter-3 — 2026-07-06T09:40:08Z

**Verdict:** CONTINUE
**Lesson:** The committed real PG bar fixture stores only TWO timeframes (1h, 1d), so it can NEVER produce a class-A confluence zone (class A needs >=3 distinct timeframes incl. a long-term member); its honest real output is [C,C,C,C,C,B]. Class-A reachability is proven only on the synthetic 3-timeframe `SYN-CONFLUENCE` fixture in `test_levels.py`. Any later journey consuming A/B/C classes that asserts class-A behaviour against the committed PG fixture will fail by construction — use the synthetic fixture (or record a real 3+-timeframe series) for class-A cases.
**Applies to:** any iter consuming J-03's A/B/C confluence classes — J-04 (`structure_tape` entries arming at classified levels) and J-05 (class-scaled stop/reward/size); any test asserting class-A on committed fixture data under `apps/backend/tests/test_levels*.py`.

## iter-4 — 2026-07-06T12:15:00Z

**Verdict:** CONTINUE
**Lesson:** `structure_tape` (iter-4) currently inherits its exits/fees/slippage/`dollars_per_r` **byte-identically from v1's dict** (verified: `strategy_definition('structure_tape')['exits'] == v1['exits']`) and shares v1's `_arm_trade`/`_close_trade`/`_synthetic_invalidation` math. J-05 will parameterize that shared exit/size arithmetic by A/B/C class — a subtle path where a class-scaling change can silently perturb v1/default and move the pinned `config_fingerprint 4d665603569b9dbf`. Separately, audit B1: the breakthrough arm (`backtests.py` `_structure_tape_arm`) is a **static price-position test** (`point.last > price` / `< price`, mirroring the frozen studies `_arm_setup_occurrences` precedent), not a fresh event-to-event cross — a sanctioned but *loose* structural anchor that will inflate breakthrough arm frequency relative to the tight 5-bps rejection band.
**Applies to:** J-05 (any iter changing `_arm_trade`/`_close_trade`/`_synthetic_invalidation` or adding class-scaled stop/reward/size — re-verify v1/default byte-identity + fingerprint AFTER the split); J-06 (honest edge measurement of structure_tape vs v1 must account for the loose breakthrough anchor before trusting any comparative edge number).

## iter-5 — 2026-07-06T15:15:00Z

**Verdict:** CONTINUE
**Lesson:** Two non-obvious properties of the J-05 class-scaled risk math that J-06's honest edge comparison must not silently break: (1) `_class_scaled_invalidation` (backtests.py) has a *level-relative-vs-entry-relative fallback* — a rejection entry can arm on either side of the level inside the proximity band, so a stop placed N bps beyond the *level* can land at/through the *entry* print; the code re-anchors to the same class-bps distance from the entry price in that case (proven by the SIM-ASKABS rejection-short fixture). (2) The DoD's "per train/hold-out split" is satisfied by *dataset provenance*, not a second in-report axis: one backtest runs over exactly one dataset carrying one frozen `split` tag, so `aggregates_by_class` is inherently scoped to that split — the cross-split comparison IS J-06, not a two-axis breakdown inside one report. Don't mistake the single-axis breakdown for an incomplete implementation.
**Applies to:** J-06 and any future iter touching `research/backtests.py` `_arm_trade`/`_exit_reason`/`_close_trade` or the edge-report/sweep train-vs-holdout comparison.
