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
