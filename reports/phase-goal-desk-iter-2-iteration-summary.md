# Iteration Summary — goal-desk-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-25
**Iteration:** 2

## In plain words

**What you can do now:** Users can run a simulated tape-reading session on the home page and watch it settle into a read like "Buyer Control," complete with live moving price bars; switch to a real stock's historical chart and see support/resistance bands drawn over the candles; open the Structure page, pick a symbol and date, and see its key price levels mapped out; open a case study for a past price touch and see how it played out; and check the Edge Report section, which honestly says when a deeper study hasn't been run yet.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The system gained a second piece of plumbing for the Desk: it can now check which of the roughly 100 companies already have price history on file across four time windows (hourly, 4-hour, daily, weekly), and it can run a job that safely fills in whatever is missing — pausing and resuming cleanly without re-downloading anything it already has. There's still no button or page to trigger this from yet.

**What's next:** Next we'll build the actual daily scan — walking through the whole company list, ranking which stocks have the most interesting price levels right now, and keeping a permanent, dated record of each day's results.

## Headline

New backend-only bar coverage read and resumable, store-first bar top-up (J-02 passing)

## Direction

**Signal:** improving
**Why:** J-02 (coverage read + resumable bar top-up) moved failing → passing this iteration on evidence the evaluator personally re-ran through the real route handlers — the per-(symbol,timeframe) truth-table, store-first reuse, composite cancel-then-resume, and index-only 4.3ms latency all held, with the suite growing to 1240 passed/8 skipped and the fingerprint pin `08e471b10130e1e2` unchanged. Nothing regressed, the anti-goal scan stayed clean, and J-01/J-07's kept-product subset held steady on a widened 24-route byte-comparison, so J-03 (the screen compute) is now fully unblocked and targeted next at full depth.

**Trend (last 3 iters):**
- Newly passing this iter: J-02
- Newly passing in last 3 iters total: J-01, J-02
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** J-02 moves `failing → passing` on evidence I executed myself, not read: all four of its `docs/goal.md` acceptance clauses ran in-process through the REAL route handlers with the universe/bar/index dirs scoped to temp copies (zero network, real `.data/` mtimes byte-unchanged), plus my own full-suite run (1240 passed / 8 skipped / 0 failed) and a live pin print (`08e471b10130e1e2`). The diff is exactly the sanctioned inventory — two new production modules, one additive `BarIndex` method, four new routes on the existing desk router — with zero diff on `routes.py`, `config.py`, `main.py`, `meta.py`, `bars.py`, `levels.py`, `tradability.py`, `desk_universe.py`, `mcp/__init__.py`, and `docs/goal.md`. Coherence is `COHERENCE-PASS`, no anti-goal violation exists at any severity, and four documented gaps are carry-forwards for J-03/J-04 rather than acceptance failures. Four journeys (J-03–J-06) remain, all tractable and keyless — hence CONTINUE.

## What was done

- Added a bar-coverage read (`GET /research/desk/coverage`) reporting per-member × per-timeframe (`1h/4h/1d/1w`) bar presence and freshness, served instantly off the `bar_index` lookup table (no full-store re-hash) via a new additive `BarIndex.coverage()` accessor.
- Built `DeskTopupComputeManager`, a resumable, cancellable, single-flight bar top-up job that walks the universe's members through the existing `POST /research/bars` fetch-and-record path store-first — never re-fetching frozen series — with three new REST routes (`POST/GET/POST-cancel /research/desk/topup/compute`).
- Added a CLI warmer (`python -m app.research.desk_topup_compute`) so an operator can run a real, full top-up over the actual ~100-symbol universe from a terminal.
- Widened the kept-route byte-comparison regression capture from 14 to all 24 kept GET route templates, now run against a populated data dir (addressing audit finding T2 from iter-1) — zero deltas found.
- Added 41 new tests (unit + integration) plus a live, real-vendor Yahoo verification (AAPL × 4 timeframes: all fetched, then all reused on a same-day re-run) proving the orchestration genuinely drives the real vendor, not just fixtures.
- No new `Config` field was needed this iteration; fingerprint pin `08e471b10130e1e2` stayed unchanged; `routes.py`/`config.py`/`main.py` carry zero diff.
- Browser QA correctly skipped this iteration (backend-only, zero frontend files touched); J-02's four acceptance clauses were instead evidenced by the evaluator's own live REST calls re-executed personally against the real route handlers.

## What's left

- Journey J-03 (The screen — pinned inputs, append-only snapshot, deterministic rank) failing — now fully unblocked and the next target.
- Journey J-04 (The /desk briefing page) failing.
- Journey J-05 (Ledger history + drill-in to /structure) failing.
- Journey J-06 (MCP contract v3 — 17 read-only tools) failing — cannot fully land before J-03 ships.
- Journey J-07 (The kept product stands — regression sentinel) stays partial — kept-product half re-verified again (24/24 kept routes byte-identical, suite grew to 1240/8), but its own "nav = 3 routes" / "MCP = 17 tools" era-completion clauses remain unmet (2/15 today) until J-04/J-06 ship.
- Carried-forward gap: the "reused vs. fetched" vocabulary mislabels a benign "already on file" 409 as `"failed"` (audit B1) — a next-UTC-day re-run would surface ~100 weekly pairs this way, so J-03/J-04 must decide the vocabulary before rendering top-up progress.
- Carried-forward gap: `latest_window_end_utc` reads as the requested window end, not the actual last bar (audit B2) — J-04 must label it "window last requested," never "last bar."
- Carried-forward operational gap: `edge_report_cache._config_content_hash` still needs warming before J-04's browser pass (real-data `/research/setups` cold ~9–11 min), and `journey-scripts/J-07.json` step 8 still needs re-pointing off async text before the next browser-QA pass.

## Next step

Target J-03 alone (the screen — pinned inputs, append-only snapshot, deterministic rank) at full depth. It is `docs/goal.md`'s next link, now fully unblocked (J-02 hands it per-member × per-timeframe coverage, and the compute-manager pattern is proven in a second place), and it is the era's heaviest single remaining journey: a brand-new append-only persisted data kind, a second compute manager, a byte-identical-re-run determinism contract, five input pins, and a row-level byte-for-byte cross-check against `GET /research/tradability`. The spec must carry forward: the screen's `as_of` must derive from the requested screen date's session close, never `now()` (do not copy the top-up's sanctioned wall-clock fetch window); the bar-store signature pin must come from the durable index, never a JSON-store re-hash; decide the "nothing new to record" vocabulary (B1) and the freshness wording (B2) before any desk surface renders these values; and coverage truth is per-(symbol, timeframe), so a screen row with partial coverage must degrade honestly rather than assume full pinned-timeframe coverage.

## Assumptions made

- iter-2 · goal-evaluator — Ambiguity: J-02's acceptance is phrased per-member ("bars-present for exactly the members the era-open store holds... bars-missing for every other member"), but the shipped payload is per-(symbol, timeframe) — MSFT holds 1h/1d and no 1w/4h, so goal.md never says which reading wins. We chose: Score the clause satisfied by a per-(symbol, timeframe) truth-table reporting the index verbatim rather than requiring whole-member presence — strictly more honest and matching the journey's own step-1 wording. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's top-up derives its bar-fetch window from wall clock (`_fetch_window_now()`), and anti-goal 7 bars wall-clock use in "any research artifact" while build trap T-6 requires determinism, but neither text says whether a persisted fetch horizon counts. We chose: Read it as scoping to computed/served research values and snapshot keys, so a fetch horizon is a sanctioned operator-request parameter, not a violation — accepting that a later-UTC-day re-run always re-fetches (the source of audit gap B1), carried into J-03/J-04 with J-03's `as_of` stated as a hard "never `now()`" requirement. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: goal.md's T-4 requires coverage/freshness be "read from `bar_index` only," and the Frozen Foundations rail lists the JSON `BarStore` as byte-identical-forever, but neither states whether `bar_index.py`'s own public read API may be additively extended to expose its already-existing `window_end_utc` column. We chose: Permit a minimal, additive extension to `bar_index.py`'s public read surface — never a DB-schema change, never touching `.lookup()`/`.insert()`'s existing contract or any current caller's behavior. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the desk-era anti-goal says universe snapshots are "append-only... nothing is silently refetched, backfilled, recomputed in place, or rewritten," but audit finding B3 shows a corrupt (never-registered) snapshot FILE gets silently overwritten at the same path on re-recording identical membership, and the anti-goal doesn't say whether "snapshot" means the registered record or the file on disk. We chose: Read it as protecting the registered RECORD — a minor gap (a silent self-heal), not a violation, carried forward as a hardening item. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: goal.md's Constraints require a screenshot for every browser acceptance ("no screenshot ⇒ unknown, never passing"), but J-01's acceptance is tagged "(Keyless; automated...)" with no browser step, and nothing states the evidence class for a REST-only journey when the browser lane doesn't run. We chose: Treat live REST through the real route handlers, executed personally by the evaluator, as the screenshot equivalent for journeys whose acceptance carries no browser clause — applied again to J-02 this iteration. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-07 mixes kept-product behaviors checkable every iteration with two era-completion clauses ("nav = exactly three routes," "MCP = exactly 17 tools") that only become true once other journeys ship, and goal.md never states how to score J-07 mid-era. We chose: Score J-07 `partial` at baseline — kept half evidenced, era-completion half recorded as unmet — rather than `already_passing` on the kept half alone; a later kept-behavior break routes to REGRESSION via the "Frozen foundations" rail instead. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-2-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-2-review.md |
| Browser QA | SKIPPED | reports/phase-goal-desk-iter-2-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-desk-iter-2-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-desk-iter-2-user-visible-changes.md |
| What to click | — | reports/phase-goal-desk-iter-2-what-to-click.md |
| UI surface map | — | reports/phase-goal-desk-iter-2-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-desk-iter-2-ui-test-plan.md |
| QA | PASS | reports/qa/goal-desk-iter-2-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-desk-iter-2-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-desk-iter-2-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-2/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
