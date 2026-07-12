# Goal Session yahoo_fetch — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-08T23:55:00Z

**Verdict:** CONTINUE
**Lesson:** The lean verify-only baseline pipeline ran decompose→develop→review only —
the browser-qa lane did NOT execute (`status.json browser_checks_run:false`, empty
`reports/qa/goal-yahoo_fetch-iter-0-evidence/`, no `ui-test-results.md`) and no
`coherence.md` was produced, even though the spec's TESTING REQUIREMENTS named browser
checks for J-05/J-06. Baseline statuses survived on code/test evidence, but any future
iteration that claims J-05 (or any browser-verifiable journey) `passing` MUST confirm the
browser lane actually ran and emitted a screenshot — a "passing" without one is unevidenced.
**Applies to:** any iter targeting J-05 or the `/structure` fetch control; any lean iteration
whose spec requests browser verification; the J-06 foundation sentinel once code starts changing.

## iter-1 — 2026-07-09T03:30:00Z

**Verdict:** CONTINUE
**Lesson:** A committed `feed="yahoo"` bar fixture must NOT be placed under `apps/backend/tests/fixtures/bars/` — the frozen `test_bars.py::test_committed_fixture_loads_through_the_real_store_path_keyless` runs `BarStore(FIXTURE_BAR_DIR).list()` over the WHOLE dir and blanket-asserts `meta["feed"] == CONFIG.historical_feed` ("sip") for every record, so a yahoo-feed file there breaks a frozen test. The dev correctly mirrored the pre-existing `tests/fixtures/alpaca/` precedent and used `tests/fixtures/yahoo/` instead. The bar-fetch vendor default is also confined to a NEW `get_bar_fetch_adapter()` on `POST /research/bars` only — never the shared `get_study_market_adapter()` or the global `get_adapter()` — because Yahoo is bars-only and would break studies/live/tick/search if the shared resolver were flipped.
**Applies to:** any J-02–J-05 iteration adding a Yahoo (`feed="yahoo"`) test fixture, and any future adapter that is not a full `MarketDataAdapter` (bars-only / ticks-only) being wired as a default — confine it to its capability's resolver, never the shared/global accessor.

## iter-2 — 2026-07-09T17:20:00Z

**Verdict:** CONTINUE
**Lesson:** The browser-qa lane silently no-op'd again (`ui-test-results.md` SKIPPED 0/10, evidence
dir empty) — this time on a FULL-depth iter, because neither frontend (:3301) nor backend (:8301)
was reachable (curl exit 7) when the lane ran, not because it was omitted. For a backend-only iter
whose required-still-passing journeys are UI journeys (J-01/J-06), the actual regression net was the
`git diff <snapshot> -- apps/frontend/` == empty invariant plus a live backend re-run of J-01's
keyless fetch and my own fingerprint/equivalence/byte-identity re-check of J-06 — the browser
screenshot the spec's DoD asked for was never the load-bearing evidence for those two journeys.
**Applies to:** J-05 specifically — it is the FIRST iter with genuinely new `/structure` UI, so its
browser lane MUST have both services started and Chrome MCP available or J-05 cannot be evidenced at
all (the zero-frontend-diff fallback that covered iter-2 will not exist once the fetch control lands).
The orchestrator should provision/verify reachable :3301/:8301 before the J-05 pipeline run.

## iter-3 — 2026-07-09T21:05:00Z

**Verdict:** CONTINUE
**Lesson:** The route-level semantics of a duplicate `POST /research/bars` CHANGED this iter: an
exact-repeat POST of the same `(symbol, timeframe, window)` now returns **200, served store-first**
(zero adapter calls), NOT the old **409**. The decomposer's spec asserted "no route-level test asserts
409 on a duplicate-window POST," but one existed (`test_duplicate_content_is_refused_409`); the dev
correctly transformed it into `test_duplicate_window_post_is_served_store_first_no_second_fetch`. The
FROZEN store-LEVEL content-duplicate 409 (a DIFFERENT window whose fetched content happens to match)
is untouched and still covered by `test_bars.py::test_rerecording_identical_content_is_refused`.
**Applies to:** any future iter touching `POST /research/bars` or bar-series duplicate/idempotence
semantics — "repeat window = 200 store-first" is now the route contract; do not "restore" a 409 there.
Directly relevant to J-05's `/structure` fetch-control test expectations.

## iter-4 — 2026-07-10T00:50:13Z

**Verdict:** CONTINUE
**Lesson:** J-04 was a clean verify-and-lock (zero production diff) but it LOCKS IN a latent trap: frozen `compute_levels` (`levels.py:306`) selects a symbol's series by SYMBOL ALONE (feed-blind), and `_select_one_series_per_timeframe` (`levels.py:171-182`) dedups only WITHIN a (symbol, timeframe) pair — so across different timeframes it will pool a `feed="yahoo"` series and a `feed="sip"` series into one confluence cluster. The critical "never pooled across feeds" rail is currently satisfied ONLY because the keyless path gives a symbol a single feed; it is avoided-by-scoping, not enforced.
**Applies to:** any iter (J-05+) that lets a symbol accumulate more than one feed over overlapping timeframes, or any iter tempted to "fix" segregation inside `levels.py` — the fix MUST be a versioned feed-scoped path BESIDE frozen `levels.py` (fingerprint-locked; mutating it is itself a critical anti-goal), never an edit to it.

## iter-5 — 2026-07-10T23:35:00Z

**Verdict:** CONTINUE
**Lesson:** A UI journey can pass every functional check yet fail phase-closure on pure artifact plumbing: `browser-qa-phase.sh` deliberately writes NO stub when signal-killed (SIGKILL/SIGTERM, per anti-patterns #20), so a quota-throttle interruption leaves `ui-test-results.md` entirely absent → CLOSURE-FAIL even though the QA agent independently captured a real Chrome-MCP browser pass + screenshots under `reports/qa/.../-evidence/`. Also: the deterministic GOAL_ACHIEVED gate (goal-gates.sh:126) greps the FULL-diff `scan-report.md` for `**Result:** CRITICAL` — so vendored `incredible_auto_dev/**` judgment-test fixtures (deliberately-planted fake secrets) will block certification unless that framework churn is kept OUT of the evaluated `snapshot..HEAD`. And an interaction defect (F1: `SymbolSearch` auto-opening its dropdown on a programmatic `value` set) can occlude the headline element in the very "proof" screenshots — a badge verified in the DOM is not a badge captured in a screenshot.
**Applies to:** any iter whose final evidence is browser-side (esp. the last Must-have UI journey before a GOAL_ACHIEVED attempt); any session doing an `incredible_auto_dev` subtree sync mid-goal-run; any `/structure` change that seeds `SymbolSearch`'s value programmatically.

## iter-6 — 2026-07-11T03:05:00Z

**Verdict:** CONTINUE
**Lesson:** A spec/docs file that QUOTES a live secret-scanner trigger token verbatim becomes the
trip-wire it warns about. iter-5's scan CRITICAL came from vendored `incredible_auto_dev/**` judgment
fixtures; the iter-6 pre-flight correctly moved those out — but the iter-6 spec's own NOTES paragraph,
explaining the risk, wrote `AKIAIOSFODNN7EXAMPLE` (AWS's public example key) inline, and the
deterministic full-diff scan (`lib/scan_diff.py`, which includes `docs/phases/*.md`) then flagged the
spec file itself. All six journeys passed and `git diff -- apps/` was empty, yet `goal-gates.sh:126`
still blocks GOAL_ACHIEVED on that one line. Non-product scan hygiene — not product code — was the last
mile to done, twice in a row from different sources.
**Applies to:** any iteration approaching a GOAL_ACHIEVED attempt (verify `scan-report.md` has no
`**Result:** CRITICAL` and, if it does, confirm the match is product source vs. a docs/framework
placeholder before scoring); any spec/handoff author documenting scanner behavior (describe trigger
tokens, never paste them verbatim into a file that lands in the evaluated diff).

## iter-7 — 2026-07-11T09:35:00Z

**Verdict:** CONTINUE
**Lesson:** A secret-scanner that scans the pipeline's OWN generated diff-bookkeeping is self-referentially recursive: `goal_gate_build_diff_artifacts` folds the UNTRACKED `runs/**/iter-diff.md` + `scan-report.md` into `$full_diff`, and those artifacts quote `scan_diff.py`'s self-test fake-secret fixtures — so the scan re-flags them and COMPOUNDS each regeneration (iter-7 went 1→3+ criticals, the scan-report even flagging its own prior findings). Worse, the "reconstruct-the-diff-and-scan-it-yourself → CLEAN" verification is UNRELIABLE here because it races the pipeline's final artifact regeneration: dev, reviewer, AND coherence all reported false-CLEAN (08:39–08:50) while the canonical `scan-report.md` regenerated at 09:05 said CRITICAL. Only reading the FINAL canonical `scan-report.md` that `goal-gates.sh` consumes is trustworthy. Durable fix is STRUCTURAL (exclude the scanner's own generated artifacts from the scan scope) + self-test hygiene (build generic-secret fixtures by concatenation, not literals); an allowlist entry cannot fix it (the generic `secret-assignment` path is not allowlist-covered).
**Applies to:** any GOAL_ACHIEVED / clean-scan attempt; any iter touching `incredible_auto_dev/scripts/automation/lib/scan_diff.py`, `goal-gates.sh` diff-building, or the `runs/**` diff-artifact scan scope — and any evaluator adjudicating a scan-report CLEAN claim (re-derive from the FINAL artifact, distrust early reconstructions).

## iter-7 (re-run) — 2026-07-12T21:27:40Z

**Verdict:** CONTINUE
**Lesson:** The deterministic regression-replay (`demo_runner.py`) text-matcher gives FALSE NEGATIVES on strings that live only inside a `<select><option>` or an async-loaded list row — J-06 step 3 (`/studies` expect "Absorption reversal") FAILED while `J-06-verify.png` plainly shows the text rendered twice. That single `| FAIL |` cell blocks the deterministic achievement gate (`goal_gate.py results`, rc=1 on `\|\s*FAIL\s*\|`) even when the journey genuinely passes and the evaluator has proven it via screenshot — so a substantively-complete goal still can't certify. Two takeaways: (1) regression-sentinel golden scripts must assert on STATICALLY-rendered, always-present headings/labels (not `<option>` text or async rows); (2) the evaluator MUST open the failing-step screenshot before honoring a replay FAIL — the screenshot outranks the replay verdict.
**Applies to:** any goal-mode iteration whose GOAL_ACHIEVED depends on a clean `ui-test-results.md`; any `journey-scripts/*.json` golden replay whose `expect.text` targets dropdown/`<option>`/async-list content; certification/declare-victory passes where a pipeline artifact (not the product) is the last blocker.

## iter-7 (re-run) — 2026-07-12T21:27:40Z — scan-hygiene resolution

**Verdict:** CONTINUE
**Lesson:** The scan-recursion CRITICAL that blocked this session for two iterations was cured ONLY by the PATH-based fix (`CHAIN_SCAN_BOOKKEEPING_EXCLUDES` excluding `runs reports docs/handoffs docs/phases` from both the tracked diff and the untracked enumeration in `goal_gate_build_diff_artifacts`) — the earlier VALUE-based allowlist made it worse (1->3 compounding criticals). Confirmed durable by independently reconstructing the gate's evaluated diff and re-running `scan_diff.py` (CLEAN, 0 untracked scanned) rather than trusting the canonical report's prose. The distinction is path (generated bookkeeping vs product source), never value.
**Applies to:** any future scan-hygiene / secret-scan false-positive blocker in goal mode; anyone tempted to allowlist a token value instead of excluding the generated-artifact path.
