# Iteration Summary — goal-fast_wall-iter-4

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-17
**Iteration:** 4

## In plain words

**What you can do now:** You can open the cockpit and watch simulated buyer/seller tape scenarios settle, save your trade thinking to a journal and review it later, browse replay studies, and check a performance ledger of simulated results. On the structure page, the price-level map and case studies are always safe to open, and if the deeper price-comparison report hasn't been calculated yet, the page says so plainly instead of hanging. There's now also a button on that page that lets you start that calculation yourself and watch it work.

**What changed this time:** You can now click "Compute edge report" on the structure page to kick off the full price-comparison calculation directly — watch a progress count tick up, see the finished report appear in place, or see an honest error message if something goes wrong, all without leaving the page or reloading. Everything behind the button was tested and works correctly; the only thing still missing is an actual recorded on-screen check of someone clicking it, which a testing-tool hiccup prevented capturing this round.

**What's next:** Next we'll confirm that on-screen click works with a real recorded check, then make the calculation able to run across multiple processor cores at once so the very first full run finishes in minutes instead of never completing.

## Headline

A "Compute edge report" button now exists on /structure.

## Direction

**Signal:** holding
**Why:** J-04's operator-run compute (single-flight manager, five additive hooks, three REST routes, CLI warmer, and the `/structure` button/poll panel) is fully built and strongly proven at the backend/API/CLI level (121 targeted tests, an audit-run CLI, a full curl lifecycle check), but its required browser click-through (TC-15/TC-16) has no screenshot — Chrome MCP failed to start, reproduced independently by four agents — so J-04 scores `partial`, not `passing`, and the phase closure verdict is CLOSURE-FAIL. No journey newly passed and none regressed this iteration (the J-07 golden-replay FAIL is a screenshot-proven backend-unreachable infra artifact, not a product regression). J-05 and J-06 remain untouched by design, so the session holds at four journeys fully passing plus one strongly-evidenced-but-unconfirmed partial, pending a clean browser session.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-07 (iter-0), J-01 (iter-1), J-02 (iter-2), J-03 (iter-3)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** "J-04's operator-run compute (single-flight/cancel/force/progress `EdgeReportComputeManager`, five additive keyword-only hooks, three REST subpaths, CLI warmer, and the `/structure` button/poll panel) is built and strongly proven at the backend/API/CLI level (121 targeted tests green, audit ran the CLI end-to-end, curl exercised the full trigger→running→done/failed lifecycle) — but its required browser click-through (TC-15/TC-16) has no screenshot: Chrome MCP failed to start this session, reproduced first-hand by four independent agents (dev, QA, audit, browser-qa). Per this project's own 'no screenshot ⇒ never passing' discipline, J-04 is `partial` (backend acceptance met; browser leg unverified), not `passing`. No regression and no anti-goal violation: the golden-replay UT-J-07 FAIL is a backend-unreachable infrastructure artifact (screenshot-proven), every frozen/pinned file is byte-unchanged, fingerprint `4d665603569b9dbf` frozen, MCP tool count 18, scan CLEAN, coherence PASS."

## What was done

- Built `EdgeReportComputeManager` — a single-flight, cancellable, progress-reporting background compute job (new `apps/backend/app/research/edge_report_compute.py`), wired to a "Compute edge report" button on `/structure` with live progress polling and a finished/failed render.
- Added five additive keyword-only hooks (`force`, `progress`, `should_abort`, `sub_cache`, `workers`) to `run_strategy_comparison_report` — byte-identical to the pre-J-04 path when unused (TC-14a) and genuinely wired, not decorative, when `should_abort` fires (TC-14b).
- Added three new REST routes (`POST`/`GET /research/edge-report/compute`, `POST .../cancel`) plus a CLI warmer (`python -m app.research.edge_report_compute --workers N [--force] [--out report.json]`) sharing the same cache the button reads from; zero new MCP tool (still 18).
- Confirmed single-flight (a second trigger while running returns the same job), clean cancel (no partial report is ever published), and verbatim failed-state error surfacing — proven by 121 targeted tests plus an audit-run CLI and a full curl-based lifecycle check against a real scoped backend.
- Full backend suite: 1482 passed / 7 skipped / 0 failed (42 net-new tests); `config_fingerprint` unchanged at `4d665603569b9dbf`; zero diff on every frozen-foundation file (`levels.py`, `tradability.py`, `backtests.py`, `bars.py`, `datasets.py`, `dataset_index.py`, `edge_report_cache.py` method bodies, `mcp/__init__.py`, `config.py`).
- Verified 0 target journeys pass browser QA this iteration — Chrome MCP failed to start (reproduced independently by the developer, QA/browser-qa, the audit, and ux-regression), so J-04's required browser click-through (TC-15/TC-16) has no screenshot and the journey scores `partial`, not `passing`.

## What's left

- Journey J-04 (The operator-run compute — button, background job, CLI warmer) scored `partial` — backend/API/CLI fully proven, but its required browser click-through has no screenshot (Chrome MCP failed to start).
- Journey J-05 (The sweep becomes resumable and parallel — durable pair results + process pool) failing — not yet built; depends on this iteration's manager/hook plumbing.
- Journey J-06 (Restarts stop hurting — the durable setups scan cache) failing — not yet built; unrelated to J-04's plumbing.
- Closure blocker: this iteration's sole target journey has no browser-executed verification anywhere in the pipeline — Definition of Done item #1 / TC-15 / TC-16 unmet; phase closure verdict is CLOSURE-FAIL until a real screenshot exists.
- Cancelling a running compute has no UI button — the backend route and frontend function both exist and are tested, but nothing on `/structure` calls it yet (deliberately out of scope this iteration).
- Forcing a fresh recompute over an already-warm result has no UI control — only reachable via the CLI's `--force` flag or a direct API call.
- The "(N from cache)" progress annotation will never actually appear yet — the field exists but there's no per-pair sub-cache until J-05 ships.

## Next step

Retry Chrome MCP in a fresh session, then re-run browser-qa for J-04 (TC-15/TC-16) plus the J-01/J-07 `/structure` visual-regression legs (TC-17/TC-18) against the SCOPED fixture backend (ports 8391/3391, `TAPEOLOGY_DATASET_DIR` pointed at `apps/backend/tests/fixtures/datasets_j03`, cold cache — never the default `.data/datasets` corpus) — a single passing screenshot flips J-04 from `partial` to `passing` with zero new code. Then build J-05 ("resumable + parallel sweep": `EdgeReportBacktestCache`, the `_split_cells` `run_pair` provider seam, a `spawn`-context `ProcessPoolExecutor`), next per the dependency order, giving the accepted-but-inert `sub_cache=`/`workers=` hooks their real effect; full depth is warranted since J-05 touches the same functions J-04 just did, over frozen foundations. If Chrome MCP still will not start, escalate the environmental blocker to the operator — it is degrading verification of every browser-verifiable journey.

## Assumptions made

- iter-4 · goal-evaluator — Ambiguity: J-01 and J-07 are Required-still-passing and share this iteration's touched page (`/structure`); under `Frontend Present: yes` the browser lane was expected to re-verify their visual legs but could not run (Chrome MCP down), and this iteration did modify `structure/page.tsx` (unlike prior zero-frontend-diff carries). We chose: keep J-01 and J-07 `passing` on an extended mechanical + traced-additive-diff argument — backend/engine owned files are byte-unchanged, full suite green, equivalence 15/15, fingerprint frozen, and the `structure/page.tsx` change is strictly additive (frozen J-01 nodes byte-unchanged, new nodes appended below, `tsc --noEmit` clean) — rather than downgrading to `unknown`; the J-01/J-07 visual-regression legs carry forward as an explicit open browser-qa item. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-04 is this iteration's target and its acceptance explicitly requires a browser-verified click-through, but Chrome MCP would not start (reproduced by 4 agents) so no screenshot exists, while every keyless clause is fully proven by 121 targeted tests plus audit-run CLI and curl. We chose: score J-04 `partial` (not `passing` — no screenshot; not `unknown` — extensively tested and its backend/API/CLI assertions genuinely passed); `last_passing_iter` stays `null`; does not change the verdict (CONTINUE regardless). Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: goal.md's J-04 acceptance requires the browser-verified compute cycle and the CLI's warm-key repeat-invocation speedup but names no concrete wall-clock ceiling for either. We chose: pin two generous ceilings on the tiny committed fixture — 90 seconds for the browser click-to-terminal-render cycle (TC-15), 5 seconds for a warm-key repeat CLI invocation without `--force` (TC-12); the real proof is the call-counting spy and single-flight/cancel/force mechanics, not the wall-clock numbers. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: goal.md names all five keyword-only hooks as J-04's own signature addition (the CLI usage string already shows `--workers N`), but the work that gives `sub_cache=`/`workers=` any actual parallel-execution effect is explicitly named as J-05's own step. We chose: J-04 adds all five keyword-only parameters (and the CLI's `--workers N` flag, default 4) so the shape goal.md names is complete from day one, but `sub_cache=`/`workers=` are accepted-and-currently-inert this iteration — every compute runs strictly sequentially; J-05 is what makes `workers > 1` genuinely parallel. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: this was the first iteration to modify the canonical owners behind a passing browser journey's UI (`levels.py`/`tradability.py` back J-07's `/structure` sections) while running `Frontend Present: no`, so J-07's continued pass had no fresh screenshot or replay. We chose: score J-07 (and J-01/J-02) `passing` on a mechanical byte-identity non-regression argument — served bytes of the modified owners proven unchanged — rather than downgrading to `unknown`, extending the mechanical-carry precedent to the harder case where the journey's own backing computation changed. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: J-03's acceptance says the committed tick-fixture structure backtests complete "within an interactive test budget" but names no concrete number. We chose: pin TC-11 at a generous 10-second wall-clock ceiling on a fixture crossing at least 5 distinct `level_change_points` intervals; the real proof of the throughput fix is the counting-spy call-count collapse, not the wall-clock number. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: the stable-journey re-verification model assumes the golden-replay lane runs for J-01/J-07, but that backend-only iteration (`Frontend Present: no`) skipped browser-qa entirely, so neither got a fresh screenshot. We chose: score J-01 and J-07 `passing` on a mechanical non-regression argument — a UI end-state can change only if frontend code or served response bytes change, and both were proven unchanged — rather than downgrading to `unknown`. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the iteration spec's prose said both `detail` AND `dataset_count` "become newly visible" in the not-computed panel, but the shipped panel renders only the headline + `detail` (`dataset_count` reaches typed state but is never painted). We chose: score J-01 `passing` by treating the goal.md acceptance + TC-11 (headline + verbatim `detail` only) as authoritative over the stronger iteration-spec prose; the unrendered `dataset_count` is a spec-completeness gap, not an acceptance miss. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: J-07's deferred acceptance said its live `/structure` spot-check should re-run "the first iteration that makes the cold GET safe (J-01)", but a full page load still separately waits on `GET /research/setups`'s cold-scan cost until J-06 ships. We chose: scope J-07's closure to the specific Edge-Report leg J-01 actually fixes, not the full page load which still separately waits on the untouched setups cost. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: J-01 step 2 said the not-computed payload embeds "the current compute snapshot (or `null`)", but the compute manager is J-04's deliverable and didn't exist yet in that iteration's scope. We chose: `peek_strategy_comparison_report`'s not-computed payload always emitted `compute: null` that iteration, for forward shape-compatibility with J-04's polling logic; J-04 wires the real snapshot into the same key without a shape change. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-07's acceptance names a live `/structure` interactive spot-check, but loading `/structure` against the default real-corpus backend triggers the never-completing edge-report sweep, so the live leg was withheld. We chose: score J-07 `passing` on the strength of the green suite, pinned fingerprint, equivalence 22/22, and four verified screenshots, treating the spec-sanctioned code-citation/SSR substitution as sufficient rather than downgrading. Reversible: yes

## Quick verify

From `reports/phase-goal-fast_wall-iter-4-what-to-click.md`:

1. Open `http://localhost:3391/structure` in your browser
2. Scroll down past "Tradable Map" and "Case Studies" to the "Edge Report" panel
3. Click the "Compute edge report" button
4. Wait up to 90 seconds without clicking anything else
5. Refresh the page (press F5 or Cmd+R)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-fast_wall-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-fast_wall-iter-4-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-fast_wall-iter-4-review.md |
| Browser QA | SKIPPED | reports/phase-goal-fast_wall-iter-4-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-fast_wall-iter-4-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-fast_wall-iter-4-user-visible-changes.md |
| What to click | — | reports/phase-goal-fast_wall-iter-4-what-to-click.md |
| UI surface map | — | reports/phase-goal-fast_wall-iter-4-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-fast_wall-iter-4-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-fast_wall-iter-4-ux-regression.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-fast_wall-iter-4-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-fast_wall-iter-4-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-fast_wall-iter-4-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-fast_wall/iter-4/eval.md |
| Journey history | — | runs/goal-session-fast_wall/state/journey-history.json |
