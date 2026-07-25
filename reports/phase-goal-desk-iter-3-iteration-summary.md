# Iteration Summary — goal-desk-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-25
**Iteration:** 3

## In plain words

**What you can do now:** Users can run a simulated tape-reading session on the home page and watch it settle into a read like "Buyer Control," complete with live moving price bars; switch to a real stock's historical chart and see support/resistance bands drawn over the candles; open the Structure page, pick a symbol and date, and see its key price levels mapped out; open a case study for a past price touch and see how it played out; and check the Edge Report section, which honestly says when a deeper study hasn't been run yet.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The system gained the actual daily-scan engine: given a date, it walks the roughly 100-company list, works out which stocks sit closest to one of their own interesting price levels, and saves one permanent, dated ranked list — a company with no price history on file is honestly marked "skipped" rather than guessed at. A saved scan can never be silently overwritten (a bug that allowed exactly that was caught and fixed this round). There's still no button or page to run or see this from yet.

**What's next:** Next we'll build the actual on-screen desk page — a screen where an operator can press "Run Screen" and watch the ranked results appear, with progress and a way to cancel.

## Headline

Backend 'screen' compute ships — deterministic, append-only, ranked rows (J-03 passing)

## Direction

**Signal:** improving
**Why:** J-03 (the append-only screen compute) moved failing → passing this iteration on 52 evaluator-executed acceptance checks, including a byte-for-byte cross-check against the live tradability route and cross-process determinism under two different `PYTHONHASHSEED` values. J-01/J-02/J-07's kept-product subset held steady (suite 1240 → 1299, fingerprint `08e471b10130e1e2` unchanged, zero diff on 12 frozen files), and the one in-iteration anti-goal risk (a silent snapshot overwrite) was found, fixed, and re-verified before this evaluation, so it counts as resolved rather than a live violation. Three straight iterations have each advanced exactly one journey (J-01 → J-02 → J-03), and J-04/J-05/J-06 are now fully unblocked, so direction is healthy.

**Trend (last 4 iters):**
- Newly passing this iter: J-03
- Newly passing in last 4 iters total: J-01, J-02, J-03
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: 1 (minor, found and fixed in-iteration at iter-3 — never landed in the shipped diff)
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** J-03 is genuinely delivered: I re-executed every one of `docs/goal.md`'s J-03 acceptance clauses myself — 52 checks through the REAL FastAPI app with all five stores scoped to a temp dir and the REAL committed fixtures seeded (103-member universe + real Yahoo AAPL/MSFT bars), zero network — and all 52 passed, including the byte-for-byte band cross-check against the live `GET /research/tradability`, an exact (not `approx`) `distance_bps` reproduction from the basis bar's own close, the identical-pin re-run leaving the one snapshot file's bytes AND mtime unchanged, and cross-process determinism under two different `PYTHONHASHSEED` values. My own full suite run is 1299 passed / 8 skipped / 0 failed with the pin live-printed as `08e471b10130e1e2` and zero diff on all 12 frozen owners plus every file under `apps/frontend/`. `coherence.md` is `COHERENCE-PASS`, so no structural veto. CONTINUE because J-04, J-05 and J-06 remain, every one is now unblocked, tractable and keyless — and because the auditor intercepted (and fixed, and I re-verified) a real append-only breach this iteration, which is exactly the class of defect the next iteration's spec must keep watching for.

## What was done

- Added a "screen" compute (backend + CLI): one pass over the universe as of a chosen date, ranking each member's closest tradable band (grade, distance from last close, score) into one dated list; a name with no bars on file is honestly reported "skipped" rather than guessed at.
- Made every screen run append-only and pinned to its exact inputs (date, universe snapshot, config fingerprint, bar-store state) — an identical re-run returns the same saved result rather than writing a second copy.
- Added live progress reporting and cancel for an in-flight screen run; only one run is allowed at a time (single-flight).
- Added a read endpoint listing past runs (lightweight summaries only) plus full lookup by date or "latest," never recomputed on read.
- Auditor found and fixed one real defect this iteration: a corrupted snapshot at the same key was being silently overwritten, erasing the tamper signal — now it refuses and reports the failure honestly, with two new regression tests, re-verified live by the evaluator.
- Suite grew from 1240 to 1299 passing tests (0 failed, 0 regressions); fingerprint pin `08e471b10130e1e2` confirmed unchanged; zero diff on all 12 frozen backend files and all of `apps/frontend`.
- Browser QA correctly skipped (backend-only, `Frontend Present: no`); the evaluator personally re-executed 52 acceptance checks through the real route handlers instead, including a byte-for-byte cross-check against the live tradability route.

## What's left

- Journey J-04 (the `/desk` briefing page) failing — now fully unblocked, targeted next.
- Journey J-05 (ledger history + drill-in to `/structure`) failing — depends on J-04.
- Journey J-06 (MCP contract v3 — 17 read-only tools) failing — needs J-04's data-contract decisions carried in first.
- Journey J-07 (kept-product sentinel) stays partial — kept half re-verified again, but its own "nav = 3 routes" / "MCP = 17 tools" clauses remain unmet at 2/15 until J-04/J-06 ship.
- Human product decision needed: a symbol's headline row currently shows its nearest same-class band, not necessarily its strongest — needs a call before J-04 renders these rows.
- The compute surface has no "already recorded" signal yet — needed before a future "Run Screen" button can honestly say "nothing new was written."
- Known limitation: the first symbol in a real screen run is slow (cold cache); a full ~100-symbol run has not been timed end to end.
- Known limitation: no CLI filter to screen just one or a few symbols yet.

## Next step

Target J-04 alone (the `/desk` briefing page) at full depth — the era's first frontend iteration: a new page, the first `UI_ROUTES` change (2 → 3, a blueprint IA change the coherence gate must re-audit), compute-button wiring with live progress/cancel, new desk copy under the copy-discipline lint, and four browser screenshots. The spec must carry: (1) the B10 human call — the "best band" rule ranks nearest band over strongest, so AAPL's headline row is a score-57 band while the era's own pinned 300–302.4 wall (score 123.0) goes unmentioned — either the chip copy says "nearest same-class band" or the selection rule gets respecced before J-04 renders it; (2) an honest reuse signal (`reused: bool` + `screen_id`) so "Run Screen" can say "nothing new was written"; (3) label coverage and bar-store-signature fields as "window last requested," never "last bar"; (4) still-open browser-pass prerequisites — a fixture-scoped backend, warming the caches stranded by an earlier config move, re-pointing a flaky replay assertion off async text, and rebuilding the frontend's `.next` cache; (5) three one-line hygiene items (scope a dataset-dir env var in route tests, refuse rather than record an empty screen with no universe, and port the new corrupt-file guard into the universe store); and (6) do not re-verify J-03's internals next iteration — suite + pin + zero-diff is sufficient.

## Assumptions made

- iter-3 · goal-evaluator — Ambiguity: Anti-goal 7 bars wall-clock use in "any research artifact" and T-6 scopes progress timestamps to compute-manager state, yet the screen snapshot's registered shape includes `created_utc`, filled from `datetime.now(timezone.utc)`. We chose: Read `created_utc` as registration metadata rather than a research value or progress timestamp — excluded from the 5-pin key and the snapshot-id checksum, with identical pins still reproducing byte-identical `rows`/`skipped` across two fresh interpreters; not an anti-goal violation. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-03 step 4 requires the honest "Desk screen not computed yet." payload before any run, but that literal string is also `docs/goal.md`'s Design-Direction copy example and J-04's own browser acceptance clause — nothing states whether the JSON payload itself must carry the sentence. We chose: Score the clause satisfied by an honest-empty JSON payload (`{"screens": [], "latest": null, ...}`, HTTP 200, never 404) and treat the literal sentence as UI copy owned by J-04, now carried as a hard requirement in J-04's spec. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: `docs/goal.md`'s Constraints sanction both Path-A `Config` fields and bare env-var "operational knobs" for store directories, and both patterns are already live in this codebase, so a new screen-snapshot store's directory could honestly go either way. We chose: Treat the screen store's directory as an operational-knob env var (`TAPEOLOGY_DESK_SCREEN_DIR`-or-sibling-default), not a new `Config` field — adds zero further `config_fingerprint`/`_config_content_hash` debt and matches the carried "do not redo" lesson. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: `distance_bps` needs a reference close price, but neither `compute_tradability` nor `compute_levels` serve one, and adding one would break existing exact-dict-equality assertions in the frozen `tradability.py` tests. We chose: `desk_screen.py` resolves the reference close itself via a plain, existing `BarStore` read of the one daily bar dated at `basis_as_of` — never re-deriving which bar is the basis, never touching either frozen module's return shape. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: `docs/goal.md` states a rank tuple for ordering the screen's final rows, but `compute_tradability` returns a list of bands per symbol with no existing method to select a single "best" one, so it's unclear whether within-symbol band selection should reuse that same tuple. We chose: Apply the identical tuple (class rank desc, distance asc, quality_score desc) twice — first to pick each symbol's own "best" band, then across symbols (plus symbol asc) for row order — rather than inventing a second selection rule. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's acceptance is phrased per-member ("bars-present for exactly the members the era-open store holds"), but the shipped payload is per-`(symbol, timeframe)`, since MSFT holds `1h`/`1d` and no `1w`/`4h`. We chose: Score the clause satisfied by a per-`(symbol, timeframe)` truth-table reporting the index verbatim, strictly more honest than requiring whole-member presence; J-03/J-04 were told partial coverage must degrade honestly. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's top-up derives its bar-fetch window from wall clock, and anti-goal 7 bars wall-clock use in "any research artifact" while T-6 requires determinism, but neither text says whether a persisted fetch horizon counts. We chose: Read it as a sanctioned operator-request parameter, not a violation — accepting a later-UTC-day re-run always re-fetches (the source of audit gap B1) — and required J-03's own `as_of` to never use `now()`, so this reading cannot creep into the screen's determinism contract. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: T-4 requires coverage/freshness be "read from `bar_index` only," and the Frozen Foundations rail lists the JSON `BarStore` as byte-identical-forever, but neither states whether `bar_index.py`'s own public read API may be additively extended. We chose: Permit a minimal, additive extension exposing the existing `window_end_utc` column — never a DB-schema change, never touching existing callers' behavior. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the desk-era anti-goal says universe snapshots are append-only and never rewritten, but audit finding B3 showed a corrupt snapshot file gets silently overwritten at the same path on re-recording identical membership, and the anti-goal doesn't say whether "snapshot" means the registered record or the file on disk. We chose: Read it as protecting the registered record — a minor gap (a silent self-heal), not a violation — carried forward as a hardening item (now fixed for the sibling `ScreenStore` this iteration; `UniverseStore`'s own copy of the gap is still open). Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: `docs/goal.md`'s Constraints require a screenshot for every browser acceptance clause, but J-01's acceptance is tagged "(Keyless; automated)" with no browser step, and nothing states the evidence class for a REST-only journey when the browser lane doesn't run. We chose: Treat live REST through the real route handlers, personally executed by the evaluator, as the screenshot equivalent for journeys whose acceptance carries no browser clause — the same rule applied again to J-02 and J-03. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-07 mixes kept-product behaviors checkable every iteration with two era-completion clauses ("nav = exactly three routes," "MCP = exactly 17 tools") that only become true once other journeys ship, and `docs/goal.md` never states how to score J-07 mid-era. We chose: Score J-07 `partial` at baseline — kept half evidenced, era-completion half recorded as unmet — rather than `already_passing` on the kept half alone; a later kept-behavior break routes to REGRESSION via the "Frozen foundations" rail instead. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-3-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-3-review.md |
| Browser QA | SKIPPED | reports/phase-goal-desk-iter-3-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-desk-iter-3-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-desk-iter-3-user-visible-changes.md |
| What to click | — | reports/phase-goal-desk-iter-3-what-to-click.md |
| UI surface map | — | reports/phase-goal-desk-iter-3-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-desk-iter-3-ui-test-plan.md |
| QA | PASS | reports/qa/goal-desk-iter-3-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-desk-iter-3-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-desk-iter-3-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-3/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
