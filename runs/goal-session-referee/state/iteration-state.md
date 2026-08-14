# Iteration State — referee

**After iteration:** 3 · **Date:** 2026-08-14 · **Verdict:** ESCALATE

## Journeys

2 passing (J-01 J-02) · 2 partial (J-03 J-10) · 6 failing (J-04..J-09) — 10 total

## Active blockers

- **J-03 over-confident p-value (dev-owned, small fix).** `referee_stats.py:424` derives
  `g2_sum = total - g1_sum` while `_t_statistic` (:454) builds `t_obs` from `math.fsum(group2)`;
  the ~1 ULP gap makes the OBSERVED grouping fail `_is_extreme` (:430), so the exact-enumeration
  branch returns `1/(N+1)` — below its own `2/(N+1)` floor. Evaluator-reproduced: 1.72% of 2v2,
  0.86% of 1v4, always on the most extreme results. No blast radius today; real at J-04/J-06/J-08.
- **Coverage gap:** no oracle case enters the enumeration branch (every generator uses S>=10
  sessions, space over 8,192); the one enumeration test (`tests/test_referee_stats.py:258`) uses
  binary-exact 5.0/1.0/2.0 and cannot fail this way.
- **Human-owned, outside this project:** trendora's `:8255` backend (stopped by iter-2's `pkill`)
  still needs a manual restart — command in `docs/handoffs/goal-referee-iter-2-dev.md`.

## Last 2 verdicts

- iter 3: ESCALATE — J-03's module, oracle suite and attestation are real and evaluator-verified
  (77 referee tests green in 81s; suite 2,495 pass / 8 skip; pin `08e471b10130e1e2`; 20 MCP tools;
  all 4 attestation tamper cases refused), but the evaluator reproduced the p-floor breach above,
  which dev, review and coherence all missed. Spec asked full; engine demoted to lean on budget,
  so audit/closure never ran, J-01/J-02 `DEFERRED-BUDGET`.
- iter 2: CONTINUE — J-02 evidence contract newly passing against hand-typed goldens; no regressions.

## Do not redo

- **J-01 and J-02 are DONE and verified** (`referee_evidence.py` + tests) — not re-targets.
- **All three iter-2 riders are closed:** `_signal_reaches_session_complete` and
  `resolve_referee_obs_cache_db_path` have real assertions; `detector_basis: None` for strategy
  observations is now in `docs/referee-statistical-spec.md` §2 (standing this era).
- **`referee_stats.py` exists and mostly works** — fix the enumeration branch + its oracle gap;
  do NOT rewrite the module or re-derive its constants from the spec.
- **Do not import `desk_forward` to "fix" the Fisher-Yates copy** — guard-tested anti-goal breach.
- **Never use `pkill -f` for dev-server cleanup** — exact-PID process-tree kills only.
