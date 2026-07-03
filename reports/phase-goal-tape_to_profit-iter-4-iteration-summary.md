# Iteration Summary — goal-tape_to_profit-iter-4

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-03
**Iteration:** 4

## In plain words

**What you can do now:** Type in a stock ticker (or use a built-in demo ticker) and watch Tapeology read live trade-by-trade activity, showing moment to moment whether buyers or sellers are in control. Write trading ideas into a journal and revisit them later, and run replay studies against past market activity. The product can permanently store slices of historical market data — checked for tampering on every read and locked forever as "practice" or "final exam" data once saved — and it can run a defined trading strategy against that saved data to get back an honest report on whether the strategy would have made or lost money, always shown next to a fair random-guessing comparison. Other software tools, including AI assistants, can connect directly to read all of this information.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The product started keeping a permanent scoreboard: a tamper-proof record of the honest profit-or-loss result for the current trading strategy on both the practice and final-exam data, including its very first ("founding") entry, readable identically no matter which tool asks for it. There's still no screen in the app to view it, though — that's the next step.

**What's next:** Next, the product will get a Performance page in the app itself, so this permanent scoreboard becomes something you can actually look at, alongside a summary of the current best-performing strategy.

## Headline

J-04 ships: append-only PnL ledger with the founding baseline row (MCP's last honest-404 tool goes live)

## Direction

**Signal:** improving
**Why:** J-04 (append-only PnL ledger with the founding baseline row) moved from failing to passing this iteration, independently cross-checked by the evaluator against three separate evidence captures — the J-02 dataset ids/checksums, the J-03 backtest aggregates, and the committed `pnl-history.md` render — that all matched byte-for-byte. J-01, J-02, J-03, and J-08 all re-verified passing with explicit evidence rows and zero anti-goal violations or regressions. Four of the last five iterations (all but the iter-0 baseline check) have each landed exactly one newly-passing journey, and the evaluator's next-step recommendation (J-05, the `/performance` page) is already unblocked with all the data it needs now live.

**Trend (last 5 iters):**
- Newly passing this iter: J-04
- Newly passing in last 5 iters total: J-01 (iter-1), J-02 (iter-2), J-03 (iter-3), J-04 (iter-4)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5 (iteration 0, baseline verification)

**Latest evaluator reasoning:** J-04 verified passing on multi-surface evidence: iter-0 404 → live 200 with the founding row (explicit `baseline: null`, candidate net R+$ per split, n=1 both splits labeled insufficient sample, full provenance, register verbatim); POST/DELETE → 405; the row's aggregates equal the independent J-03 re-run capture EXACTLY and its dataset ids + checksums appear verbatim in the J-02 datasets-list capture; committed `reports/pnl/pnl-history.md` shows identical numbers; MCP `pnl_ledger` byte-identity tested (last tool out of honest-404). Evaluator independently confirmed the `app/mcp/__init__.py` diff is two documentation strings only and the only UPDATE SQL is schema_version bookkeeping. Suite 983 passed / 1 skipped, equivalence 7/7, replay lane 2/2 (J-01, J-08), COHERENCE-PASS.

## What was done

- Added the append-only `pnl_ledger` table via a versioned v8→v9 journal migration (proven against a new committed old-schema fixture), with no update/delete methods and explicit duplicate-enhancement-id refusal
- Built the one writer module (`app/research/pnl_ledger.py`) that composes ledger rows from verbatim row-31 backtest aggregates — never recomputing R, $, or trade count
- Added a keyless, idempotent founding-baseline seeding CLI (`python -m app.research.pnl_baseline`) that runs one backtest per fixture split and appends the founding row with the baseline side explicitly null, never fabricated zeros
- Exposed `GET /research/pnl/ledger` (the last remaining honest 404 in the API) plus a byte-level-no-op markdown render committed at `reports/pnl/pnl-history.md`
- Flipped the MCP `pnl_ledger` tool from honest 404 to live data with a two-string documentation-only diff to `app/mcp/__init__.py`, retiring the now-empty honest-404 test premise
- Grew the backend suite from 952 collected (951 passed/1 skipped) to 984 collected (983 passed/1 skipped); engine equivalence suite still 7/7
- Verified 1 target journey (J-04) passes browser QA, plus re-verified the 4 required-still-passing journeys (J-01, J-02, J-03, J-08) all pass (5/5 in the merged UI test results)

## What's left

- Journey J-05 (The /performance page reports PnL per enhancement honestly) failing — next target
- Journey J-06 (Indicator profiles are versioned; the default stays byte-identical) failing
- Journey J-07 (The candidate sweep survives hold-out or says so honestly) failing
- Known limitation: the `pnl_baseline` / `pnl_history` module CLIs resolve the journal DB via `TAPEOLOGY_JOURNAL_DB` or a cwd-relative default — must run from `apps/backend/` or set the env var (documented, not a defect)
- J-07 planning heads-up: the fixture windows arm exactly n=1 trade per split (below the configured minimum of 5) — the sweep's promotion-gate test design needs deliberate handling on the current fixtures

## Next step

Target J-05 (the `/performance` page) at lean depth — the first frontend iteration of the era, continuing the J-02 → J-03 → J-04 → J-05 chain; all the data it needs is now live. Scope: a fourth top-level page rendering `GET /research/pnl/ledger` rows verbatim (no client-side recomputation; every $ beside its R and n; register visible; train/hold-out separate; insufficient-sample labels exercised by the real n=1 founding row), a champion summary per the blueprint, and a Performance nav entry rendered from `/meta/ui-routes` (adding `/performance` to the route map — this changes the J-01 nav assertion and likely requires updating the stored golden expectations for the 3-link nav). The browser lane must verify the nav on every page and that displayed values equal the API values. After J-05: J-06 (profiles), then J-07 (sweep) — noting the fixture windows arm only n=1 per split, below the configured minimum of 5, so J-07's promotion-gate test design needs deliberate handling.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tape_to_profit-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-tape_to_profit-iter-4-dev.md |
| Review | PASS | reports/reviews/goal-tape_to_profit-iter-4-review.md |
| Browser QA | PASS | reports/phase-goal-tape_to_profit-iter-4-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-tape_to_profit/iter-4/eval.md |
| Journey history | — | runs/goal-session-tape_to_profit/state/journey-history.json |
