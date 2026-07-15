# Iteration Summary — goal-tradable_wall-iter-9

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-15
**Iteration:** 9

## In plain words

**What you can do now:** You can watch simulated or real historical stock price action with live buy-and-sell-pressure readings, keep a trading journal, and run replay research studies. On the Structure page you can fetch real price history for a stock with one click, see a short list of at most ten price zones that actually matter for a stock (instead of a wall of thousands of lines), and open a real pinned Apple example to see exactly how price reacted at that zone. Those same important zones also show up on the live cockpit chart, with a plain-language note when the reading agrees. There's also an honest profit-comparison report — though it's still slow to load the very first time someone lets it finish computing.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team built machinery so the profit-comparison report will remember its answer and load in seconds on every future visit (even after restarting the app) once someone lets it finish computing one time — but that first long computation, and the resulting fast page, hasn't actually happened or been seen working yet.

**What's next:** A short follow-up pass to make that fast, remembered answer actually show up on screen, using a quick practice run instead of the full multi-hour one — which should be the last piece needed before this feature is fully done.

## Headline

Built a rebuildable Edge Report cache; browser-observed warm render still not achieved (3rd iter).

## Direction

**Signal:** holding
**Why:** J-08's cache machinery (determinism, concurrency, restart durability, byte-identity) is built and independently verified — the failing→partial move is real progress — but DoD item 1 (a browser-observed warm-cache render) still wasn't captured because the pipeline backend was mid-flight on the real ~10h corpus compute, so J-08 stays short of a full pass for the third straight iteration (iter-6/8/9). J-01–J-07 all re-verified green with zero regressions and no anti-goal violation, so the seven-journey foundation holds steady while the loop needs one more lean pass to close the render gap.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-03, J-05, J-06
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5 (iter-5)

**Latest evaluator reasoning:** J-08's rebuildable, checksum-keyed edge-report result cache is genuinely built and correct — I ran the load-bearing determinism/concurrency/warm-serve/no-pool tests myself (all green), independently recomputed `config_fingerprint == 4d665603569b9dbf`, and confirmed every frozen foundation + all of `apps/frontend/` + the committed `reports/pnl/pnl-history.md` are ABSENT from the diff. But J-08 is **partial, not passing**: its DoD item 1 (a browser-observed warm-cache Edge Report render), the iteration's own lessons-applied instruction ("the warm-cache render must be observed in a real browser, not left to a loading carve-out"), and the decomposer's keyless-core passing bar all require the warm render — and the crux screenshot (UT-01) shows only the loading skeleton; UT-02/UT-03/UT-06 were SKIPPED because the pipeline backend ran against the real corpus with a genuine cold ~10h compute in flight.

## What was done

- Built `EdgeReportCache`, a two-layer rebuildable, checksum-keyed result cache (durable SQLite + in-process fast path) around the Edge Report's ~10+h backtest sweep, keyed on dataset checksums + strategy registry + `config_fingerprint` + a justified, tested 4th whole-config-content hash.
- Wired `GET /research/edge-report` and its MCP proxy to serve through the cache via a thin `cache=None` dispatcher; `edge_report.py`'s actual computation is untouched (renamed only), so a cache miss still recomputes byte-identically.
- Added keyless PnL-history append machinery (`append_strategy_comparison_row`, CLI `--append-report` flags) so a completed 3-way comparison can eventually be recorded to `reports/pnl/pnl-history.md`, never pooling train/holdout or feeds.
- Added 44 net-new backend tests — determinism/byte-identity, a 16-thread concurrency/torn-read guard, six-way cache-key-busting, restart durability, MCP byte-identity; full suite now 1392 passed / 7 skipped / 0 failed.
- Caught and fixed a real bug during implementation: the stored cache blob was serialized sorted, silently breaking response byte-order versus a fresh compute; added a dedicated regression test.
- Re-verified J-01–J-07 unregressed via frozen-file diff-absence, an independently-recomputed `config_fingerprint`, and fresh browser QA (UT-07/08/09/10/11).
- Verified 0 target journey(s) pass browser QA this iteration (J-08 stayed partial): browser QA opened 7/11 UI checks PASS overall, but the crux warm-render check (UT-02) stayed in a documented, independently-verified cold-cache carve-out.

## What's left

- J-08 (edge-report result cache) is `partial`: the browser-observed warm-cache Edge Report render (DoD item 1) hasn't been captured in 3 straight iterations (iter-6/8/9) — the cache machinery is built and verified, only the observed render is missing, and it is agent-achievable with a scoped keyless dataset dir.
- The real ~10+h compute over the 11 credentialed `sip` datasets has not been triggered — an explicit operator-gated action, needed before the Edge Report shows real populated numbers end to end.
- The real PnL-history append (recording the first genuine 3-way comparison to `reports/pnl/pnl-history.md`) hasn't happened yet — the append machinery is built and tested, but the committed file is still untouched.
- Even after a future real append, `/structure` has no render path yet for the new `strategy_comparison` ledger-row type — the page currently only looks up a single `founding` row.
- UT-11's band-overlay/confluence-chip did not appear in any of 4 sampled historical AAPL windows despite price sitting inside the pinned band twice — open, non-blocking observation, plausibly tied to the cold edge-report cache but not confirmed.
- Pre-existing `scripts/dev.sh` process-cleanup gap (uvicorn/`next-server` child processes survive a plain stop) — documented since iter-8, still not fixed.

## Next step

LEAN iteration to close the single missing DoD element — the browser-observed warm-cache render for J-08 (no new product code expected; the render path is unchanged, already-verified J-05 code). Provision a scoped keyless dataset dir (`TAPEOLOGY_DATASET_DIR` + `TAPEOLOGY_EDGE_REPORT_CACHE_DB`, e.g. the committed fixture or a couple of reference datasets that resolve to classified scan events) so `GET /research/edge-report` warms in seconds, then have browser-QA open a screenshot of the resolved `/structure` Edge Report section (populated cells or the honest all-`insufficient_sample`/empty state) within an interactive budget — closing UT-02/UT-03/UT-06 and DoD item 1, which flips J-08 partial to passing and yields GOAL_ACHIEVED (subject to the deterministic gate + two-key confirm). Fold in the two coherence-WARN advisories while here: register `pnl_ledger.py`/`pnl_history.py` in `blueprint.md`'s owners table, and rename the `pnl-history.md` 3-way table's `side` column to `band side`. The first real ~10h corpus warm and its real PnL-history append remain an operator-gated carry that does not block J-08 passing.

## Assumptions made

- iter-9 · goal-evaluator — Ambiguity: Is the browser-observed warm-cache Edge Report render a REQUIRED, agent-achievable element of J-08's passing bar, or is it substantively covered by route-level warm-serve proof? We chose: REQUIRED and unmet — J-08 stays partial (CONTINUE), since the only Edge Report screenshot (UT-01) showed the loading state and the render is agent-achievable keyless, not an operator carry. Reversible: yes — a human accepting route-level tests as sufficient evidence can flip J-08 to passing, yielding GOAL_ACHIEVED on --resume.
- iter-9 · goal-decomposer — Ambiguity: Does J-08 pass on its keyless core, or does it require the operator's full ~10+h real compute AND the real pnl-history append before passing? We chose: the keyless-core reading (mirrors iter-4's J-04 decision) — cache machinery + determinism + concurrency + byte-identity + the warm-cache render + append machinery, all keyless; the real compute and its ledger append are the operator-gated carry. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: Does GOAL_ACHIEVED require the populated Edge Report cells to be rendered/observed, given the ~10+h compute never finished this session? We chose: acceptable to declare GOAL_ACHIEVED without observing populated cells — populated cells are not a journey acceptance criterion and an empty/all-insufficient_sample report is an explicitly valid outcome. Reversible: yes — a human requiring the observed render could reverse to CONTINUE.
- iter-8 · goal-decomposer — Ambiguity: Does J-03's feed-honesty acceptance require an `iex` stamp specifically, or the feed stamped verbatim from whatever tier the adapter returns (here `sip`)? We chose: the verbatim-stamp reading — `iex` was only an illustrative free-tier example; the operator's paid SIP tier is honest and richer, not a violation. Reversible: yes.
- iter-7 · goal-evaluator — Ambiguity: (a) does J-06 require the credentialed tick-recording replay, or is the keyless overlay+chip+empty-state core sufficient; (b) with J-03 still partial and zero agent-buildable work left, is STALLED the right verdict? We chose: (a) J-06 passes on its keyless core; (b) STALLED, not GOAL_ACHIEVED/CONTINUE — every J-03 unblock path is operator-owned. Reversible: yes.
- iter-7 · goal-decomposer — Ambiguity: Does J-06's "labels... never hardcoded" require a backend change to add a served label field, or is reading the served rejection/breakthrough mapping plus the served tape-state token enough? We chose: no-backend-change reading — the served mapping IS the vocabulary; no new served label field added. Reversible: yes.
- iter-6 · goal-evaluator — Ambiguity: Is J-05 fully passing with an honest empty tape-timeline state on the pinned case, or only partial until J-03 populates it? We chose: passing — the acceptance text explicitly conditions the tape timeline on "once J-03 ran," and the honest empty-state is a sanctioned pass condition. Reversible: yes.
- iter-6 · goal-decomposer — Ambiguity: Does "/structure decluttered" require removing the era-5 Registry/Comparison sections, or only moving the raw-levels rendering behind a toggle? We chose: the non-regressing reading — only raw levels move behind an off-by-default toggle; Registry/Comparison stay intact below the new Tradable Map. Reversible: yes.
- iter-5 · goal-decomposer — Ambiguity: How should a touch event whose reaction is computed from a truncated sub-horizon (the audit-B1 boundary case) be presented — disclosed, suppressed, or excluded? We chose: additive disclosure — keep the existing reaction/forward_returns and additionally carry an effective-horizon + boundary flag for honest UI rendering. Reversible: yes.
- iter-4 · goal-evaluator — Ambiguity: Does J-04's keyless run need to produce a POPULATED all-insufficient_sample report, or is a vacuously-empty `cells: []` report on the literal fixture sufficient (with a synthetic-panel test proving the populated shape)? We chose: empty-is-valid — J-04 passes on its keyless core; the goal explicitly names an empty/all-insufficient_sample report a valid, publishable outcome. Reversible: yes.
- iter-4 · goal-decomposer — Ambiguity: Can J-04 be scored passing on the keyless committed-fixture run alone, or does it require the credentialed >=10-window recorded data? We chose: the keyless reading — a correct, gate-honoring, all-insufficient_sample report over the committed fixture is J-04's passing core; credentialed enrichment is an operator-gated carry. Reversible: yes.
- iter-3 · goal-evaluator — Ambiguity: Does J-03's ">=10 datasets exist"/"shows the timeline" require durable persistence in the canonical store plus the specific pinned-AAPL drill-in, or is a demonstrated-but-ephemeral recording run enough? We chose: the stricter reading — the credentialed headline is met only when datasets persist in the canonical store AND the pinned-AAPL drill-in is demonstrated end-to-end; under this bar J-03 = partial. Reversible: yes.

## Quick verify

From `reports/phase-goal-tradable_wall-iter-9-what-to-click.md`:

1. Open `http://localhost:3301/structure` in your browser.
2. Scroll down past the "Tradable Map" and "Case Studies" panels to the panel titled "Edge Report".
3. If step 2 showed the already-resolved outcome, refresh this page (press F5) and watch the "Edge Report" panel again.
4. Scroll back to the top of the page. Type `AAPL` into the "Symbol" field, type `2026-06-22T21:00:00Z` into the "As-of (UTC, ISO-8601)" field, then click the "Load" button.
5. Look at the button just below the Tradable Map panel.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tradable_wall-iter-9.md |
| Dev handoff | — | docs/handoffs/goal-tradable_wall-iter-9-dev.md |
| Review | PASS | reports/reviews/goal-tradable_wall-iter-9-review.md |
| Browser QA | PASS | reports/phase-goal-tradable_wall-iter-9-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-tradable_wall-iter-9-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-tradable_wall-iter-9-user-visible-changes.md |
| What to click | — | reports/phase-goal-tradable_wall-iter-9-what-to-click.md |
| UI surface map | — | reports/phase-goal-tradable_wall-iter-9-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-tradable_wall-iter-9-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-tradable_wall-iter-9-ux-regression.md |
| QA | PASS | reports/qa/goal-tradable_wall-iter-9-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-tradable_wall-iter-9-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-tradable_wall-iter-9-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-tradable_wall/iter-9/eval.md |
| Journey history | — | runs/goal-session-tradable_wall/state/journey-history.json |
