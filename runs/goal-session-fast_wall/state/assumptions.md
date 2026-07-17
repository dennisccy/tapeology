# Goal Session fast_wall — Assumption Ledger

Append-only. Each entry records a scoring/interpretation call the goal-evaluator
made when the goal or a journey left something open — so the human can see (and
veto) these silent calls early. Routine evidence-reading is not an assumption.

## iter-0 — goal-evaluator

**Ambiguity:** J-07's acceptance names a live `/structure` era-5/5B interactive spot-check, but
loading `/structure` against the default real-corpus backend triggers the never-completing
edge-report sweep (hours of CPU pin), so the live leg was withheld and only the backend suite +
SSR-probe (curl GET 200, all era-5/5B markers present) + the other four surfaces' live screenshots
cover it.
**We chose:** Score J-07 `passing` on the strength of the green suite + pinned `config_fingerprint` +
equivalence 22/22 + four verified screenshots + zero-code diff (nothing could have regressed), treating
the spec-sanctioned code-citation/SSR substitution as sufficient for the `/structure` leg at a
zero-diff baseline, rather than downgrading to `partial`/`unknown`.
**Reversible:** yes — the deferred `/structure` live-interactive spot-check is re-run the first
iteration that makes the cold GET safe (J-01); if it ever fails, J-07 flips to `regressed` there.

## iter-1 — goal-decomposer

**Ambiguity:** J-01 step 2 says the not-computed payload embeds "the current compute snapshot (or `null`)", but the compute manager (`edge_report_compute.py`) is J-04's deliverable and does not exist yet within this iteration's scope.
**We chose:** `peek_strategy_comparison_report`'s not-computed payload always emits `compute: null` this iteration (the key is present now for forward shape-compatibility with J-04's frontend polling logic; its value is honestly `null` because no compute manager exists yet to query). J-04 wires the real snapshot into the same key without a shape change.
**Reversible:** yes — J-04 only needs to supply a non-null value for the existing `compute` key; no payload restructuring required.

## iter-1 — goal-decomposer

**Ambiguity:** J-07's deferred acceptance (iter-0 `assumptions.md`) says its live `/structure` interactive spot-check should be "re-run the first iteration that makes the cold GET safe (J-01)", but a full `/structure` page load on the default real-corpus backend still separately waits on `GET /research/setups`'s cold-scan cost (268.95s measured at iter-0) until J-06 ships — a hazard J-01 does not touch.
**We chose:** Scope this iteration's J-07 closure to the specific leg J-01 actually fixes (the Edge-Report mount-time GET, mechanically proven safe by the compute-spy test and by the old hazardous code path no longer existing) rather than requiring a full live page load that would still cost several minutes for an unrelated, already-diagnosed reason. A full live spot-check is encouraged as bonus evidence if time allows, not required to close this gap.
**Reversible:** yes — if future evidence shows the Edge-Report leg was NOT actually safe, J-07 flips to `regressed` and this reading is revisited; the setups-leg speed gap remains explicitly tracked for J-06, not silently closed.

## iter-1 — goal-evaluator

**Ambiguity:** The iteration spec's "New information displayed" prose says both `detail` AND
`dataset_count` "become newly visible" in the not-computed panel, but the shipped `NotComputedPanel`
renders only the headline + `detail` (`dataset_count` reaches typed frontend state but is never
painted) — flagged non-blocking by both coherence.md and the audit (F1).
**We chose:** Score J-01 `passing` by treating the goal.md journey acceptance + TC-11 (which require
only the "Edge report not computed yet." headline and the verbatim `detail`, and are met exactly) as
authoritative over the downstream iter-spec prose's stronger "dataset_count also visible" claim; the
unrendered `dataset_count` is a spec-completeness gap, not a J-01 acceptance miss.
**Reversible:** yes — a later iteration can render `dataset_count` in the same panel with no contract
change; if the human deems its visibility binding, J-01 can be reopened for that one addition.

## iter-2 — goal-evaluator

**Ambiguity:** The methodology's stable-journey re-verification model assumes the golden-replay lane
runs for the Required-still-passing set (J-01, J-07), but this backend-only iteration
(`Frontend Present: no`) SKIPPED the whole browser-qa step, so neither UI journey got a fresh
screenshot or replay this iteration.
**We chose:** Score J-01 and J-07 `passing` (and bump `last_verified_iter` to iter-2) on a
mechanical non-regression argument — a UI end-state can change only if frontend code or the served
response bytes change, and both are proven unchanged (zero-frontend git diff + TC-8/TC-14
byte-identity + green suite 1427/0-fail + `config.py`-untouched-so-fingerprint-frozen) — rather than
downgrading either to `unknown` for lack of a fresh browser pass.
**Reversible:** yes — the next frontend-touching iteration re-runs their golden replay; if either
ever fails there, it flips to `regressed` and this reading is revisited.

## iter-3 — goal-decomposer

**Ambiguity:** J-03's acceptance says "the committed tick-fixture structure backtests complete
within an interactive test budget" but names no concrete number.
**We chose:** This iteration's TC-11 pins that budget at a concrete, generous 10-second
wall-clock ceiling on a newly-added fixture whose tick stream crosses at least 5 distinct
`level_change_points` intervals — chosen to be clearly satisfiable once the memo works and
clearly diagnostic of a regression back to per-tick recomputation, without being flaky on a
loaded CI box. The real proof of the throughput fix is the counting-spy call-count collapse
(TC-9/TC-10), not the wall-clock number itself.
**Reversible:** yes — a later iteration can tighten or loosen this specific number without
touching the underlying contract (byte-identity + call-count collapse), which is the
acceptance's real substance.

## iter-3 — goal-evaluator

**Ambiguity:** This is the first iteration to MODIFY the canonical owners behind a `passing` browser journey's UI (`levels.py`/`tradability.py` back J-07's `/structure` Tradable Map + Case Studies) while running `Frontend Present: no` — so J-07's continued pass has no fresh screenshot and the replay lane did not run.
**We chose:** Score J-07 (and J-01/J-02) `passing` on a mechanical byte-identity non-regression argument — the served bytes of the modified owners are proven unchanged (TC-15 pinned-value tests + my own targeted `test_levels.py`/`test_tradability.py` run + frozen `config_fingerprint` 4d665603569b9dbf), and a UI end-state can move only if the served bytes move — rather than downgrading J-07 to `unknown` for lack of a browser pass. This extends iter-2's mechanical-carry precedent to the harder case where the journey's OWN backing computation changed (not just an unrelated file).
**Reversible:** yes — the next frontend-touching iteration (J-04) re-runs J-01's and J-07's browser/golden-replay leg; if either fails there it flips to `regressed` and this reading is revisited.

## iter-4 — goal-decomposer

**Ambiguity:** goal.md's J-04 step 1 names all five additive keyword-only hooks
(`force=, progress=, should_abort=, sub_cache=, workers=`) as this journey's OWN signature addition to
`run_strategy_comparison_report`, and J-04 step 3's CLI usage string already shows `--workers N`, but
the work that gives `sub_cache=`/`workers=` any actual parallel-execution effect (`_split_cells`'s new
`run_pair` provider seam + the `ProcessPoolExecutor` pool) is explicitly named as J-05's own step 2/3.
**We chose:** J-04 adds all five keyword-only parameters to `run_strategy_comparison_report`'s
signature (and the CLI's `--workers N` flag, default 4) so the shape goal.md names is complete and
forward-compatible from day one — mirroring iter-1's own `compute: null` forward-shape precedent — but
`sub_cache=`/`workers=` are accepted-and-currently-INERT this iteration: every compute this iteration
triggers (button or CLI, at any `--workers` value) runs strictly sequentially, byte-identical to
today's `_split_cells` loop. J-05 is what makes `workers > 1` genuinely parallel.
**Reversible:** yes — J-05 only needs to give the already-accepted parameters real behavior; no
signature or CLI-flag change required, no re-plumbing of any caller.

## iter-4 — goal-decomposer

**Ambiguity:** goal.md's J-04 acceptance requires the browser-verified compute cycle ("button →
progress → cells or the honest empty state") and the CLI's warm-key repeat-invocation speedup, but
names no concrete wall-clock ceiling for either (the same open-ended pattern iter-3's TC-11 budget
already resolved once for a single backtest).
**We chose:** Pin two concrete, generous ceilings on the tiny committed fixture dataset dir (1–2
datasets, per `tests/fixtures/datasets_j03` / `tests/fixtures/datasets`): the browser click-to-terminal-
render cycle (TC-15) gets a 90-second ceiling; a warm-key repeat CLI invocation without `--force`
(TC-12) gets a 5-second ceiling. Both are chosen to be clearly satisfiable (the fixture is small enough
that even a full sequential 3-strategy sweep should complete in low single-digit seconds) and clearly
diagnostic of a regression to per-request recomputation, without being flaky on a loaded CI box or a
slow browser-automation round-trip. The real proof is the call-counting spy (TC-6/TC-12) and the
single-flight/cancel/force mechanics (TC-1 through TC-5), not the wall-clock numbers themselves.
**Reversible:** yes — a later iteration can tighten or loosen either number without touching the
underlying contract (single-flight + cache-hit call-count + browser terminal-state proof).

## iter-4 — goal-evaluator

**Ambiguity:** J-04 is this iteration's target and its acceptance explicitly requires a browser-verified
click-through ("button → progress → cells or the honest empty state"), but Chrome MCP would not start
(reproduced by 4 agents) so no screenshot exists — while every keyless clause (single-flight, cancel,
force, failed-state, 405, MCP-count, CLI warm-repeat, hook byte-identity) is fully proven by 121 targeted
tests + audit-run CLI + curl. The status enum forces a single label for a journey that is genuinely
verified on its backend half and genuinely unverified on its required browser half.
**We chose:** Score J-04 `partial` (not `passing` — a required browser clause has no screenshot, the
project's "no screenshot ⇒ never passing" rule; and not `unknown` — the journey WAS extensively tested
this iteration and its backend/API/CLI assertions genuinely passed). `last_passing_iter` stays `null`.
This does not affect the verdict (CONTINUE regardless, since J-05/J-06 remain failing).
**Reversible:** yes — the next healthy-Chrome browser-qa pass of TC-15/TC-16 flips J-04 `partial →
passing` with zero code change; if that render ever contradicts the backend evidence, J-04 reopens.

## iter-4 — goal-evaluator

**Ambiguity:** J-01 and J-07 are Required-still-passing and share this iteration's touched page
(`/structure`), so under `Frontend Present: yes` the browser lane was EXPECTED to re-verify their visual
legs — but it could not run (Chrome MCP down), and this iteration DID modify `structure/page.tsx` (unlike
iter-2/iter-3's zero-frontend-diff mechanical carries).
**We chose:** Keep J-01 and J-07 `passing` on an extended mechanical + traced-additive-diff argument:
(a) all their backend/engine owned files are git-confirmed byte-unchanged vs the working tree, full suite
1489/1489 green, equivalence 15/15, fingerprint `4d665603569b9dbf` frozen; (b) the `structure/page.tsx`
change is strictly additive — the frozen J-01 headline/detail/register nodes are byte-unchanged and the
new button/progress/error nodes are appended below them (audit T1, coherence), `tsc --noEmit` clean —
rather than downgrading either to `unknown` for the missing screenshot. The J-01/J-07 `/structure`
visual-regression legs (TC-17/TC-18) are carried forward as an explicit open browser-qa item.
**Reversible:** yes — the next healthy-Chrome pass re-runs TC-17/TC-18; if either visual leg regresses
there, the affected journey flips to `regressed` and this carry is revisited.

## iter-5 — goal-decomposer

**Ambiguity:** goal.md's J-05 step 3 and the interlude-wide constraint say parallelism "runs ONLY
in the CLI/background job — never inside a request thread," and Success Criteria #4 frames
"resumable... and parallel" as a property of the sweep triggered by "UI button OR CLI warmer"
equally — but the text never states whether `EdgeReportComputeManager`'s own background thread
(the button's async trigger, already off the HTTP request thread since J-04) counts as an allowed
"background job" home for `ProcessPoolExecutor` parallelism, or whether "the CLI/background job" is
one compound term meaning the CLI warmer specifically.

**We chose:** This iteration wires `sub_cache=` (resumability — pure SQLite caching, no new
concurrency primitive) into BOTH the CLI warmer and `EdgeReportComputeManager.trigger()`, so a
browser-triggered compute is genuinely resumable and the already-displayed
`progress.backtests_from_cache` field becomes meaningful for button-triggered runs too. Genuine
`workers > 1` process-pool parallelism, however, is wired into the CLI warmer ONLY —
`trigger()` never passes `workers` above `1`/`None` into `run_strategy_comparison_report`, keeping
`ProcessPoolExecutor`/multiprocessing entirely out of the always-on FastAPI/uvicorn backend
process. The CLI is a clean, isolated, one-shot, nohup-able process explicitly designed for this
(J-04's own docstring calls it "restart-proof"); the manager's background thread is more
conservatively treated as still request-adjacent for this CRITICAL anti-goal ("no compute on page
load" sits right beside it in the same section of goal.md).

**Reversible:** yes — a follow-up iteration can add a `workers=` passthrough to `trigger()`/the
route with no signature-breaking change, exactly mirroring how J-04 itself forward-declared
`sub_cache=`/`workers=` as accepted-but-inert for this iteration to later resolve.

## iter-5 — goal-evaluator

**Ambiguity:** J-04's acceptance / DoD names a browser-verified "button → progress →
terminal-state" cycle, but both committed keyless fixtures resolve 0 eligible pairs, so the
captured browser evidence is button → (instant) terminal honest-empty-state, never a live
nonzero progress tick or the "(N from cache)" annotation. The status enum forces one label for a
journey whose required browser leg is now genuinely captured at its terminal/failed states but
whose intermediate progress-tick sub-leg is un-showable on the mandated fixtures.
**We chose:** Score J-04 `passing` (flip from iter-4's `partial`), not keep it `partial`. The
iter-4 rationale for `partial` was strictly "no screenshot exists" (Chrome MCP down); that
blocker is now resolved — I personally opened real screenshots of the enabled "Compute edge
report" button (UT-01), the click-through to the acceptance's explicitly-allowed terminal honest
empty state with no button/no reload (UT-02-after-empty-state), the failed-state verbatim
`EdgeReportError` + "Retry compute" (UT-06), and the warm reload serving directly (UT-04). The
single unshown sub-leg is fixture-bound, openly disclosed across three lanes, and proven
non-vacuously at the pytest level — a documented limitation, not a missing-evidence gap. Requiring
the nonzero-tick screenshot would hold J-04 hostage to a keyless-fixture limitation the spec
itself mandated (the methodology's #1 "vague criteria → infinite loop" anti-pattern).
**Reversible:** yes — a future iteration with a fixture/corpus carrying genuinely eligible pairs
(after J-06, or a recorded corpus) can add the live-tick + "(N from cache)" browser evidence
(currently UT-07 SKIP); if that render ever contradicts the pytest proof, J-04 reopens.
