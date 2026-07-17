# Phase goal-fast_wall-iter-5 — UX Regression Review

**Date:** 2026-07-17

**Verdict:** UX-REGRESSION-PASS

## New Capability Discoverability

There is no new capability to assess this iteration. `apps/frontend/` is git-confirmed
byte-identical to iter-4 (`git status --porcelain apps/frontend/` empty; dev handoff and both
`ui-surface-map.md`/`user-visible-changes.md` agree: "Frontend: none planned"). The plan itself
states the reason `Frontend Present: yes` is set at all: solely to force the UI Impact / UI Test
Design / Browser QA / UX Regression lanes to run against the EXISTING `/structure` button, not to
ship new frontend code.

What this iteration actually did on the UI side was **close a verification gap on an
already-shipped capability** (J-04's "Compute edge report" button, built in iter-4 but never
actually watched in a live browser due to two consecutive Chrome MCP failures). I re-checked its
discoverability directly against this iteration's own evidence:

| Capability | Shipped in | Navigation path this iteration re-confirmed | Clicks from home | Verdict |
|---|---|---|---|---|
| "Compute edge report" button / progress line / failed-state | iter-4 (code); iter-5 (first live verification) | `:3301/` (Cockpit) → click "Structure" nav link → scroll to "Edge Report" heading | 1 click + scroll | Discoverable — confirmed via `UT-09-discoverability.png`: the top nav bar (Cockpit / Journal / Studies / Performance / **Structure**) is visible with no login, and the Edge Report heading/button sit inline in a plain linear scroll (~1377px into a 2400px-tall viewport), not behind a tab or secondary menu |
| Button label / states | iter-4 | N/A (no new label) | — | Confirmed self-explanatory and unchanged: "Compute edge report" (idle) → "Computing…" (running, disabled) → "Retry compute" (failed) — verified byte-identical to iter-4's documented copy via `UT-01`, `UT-02`, `UT-06` |
| Visual feedback while running/failed | iter-4 | N/A | — | Progress line and red error line both confirmed rendering via `UT-02-during.png` and `UT-06-failed-compute-error.png` |

No label confusion: every string checked (headline, detail text, button labels, error text) is
byte-identical to what iter-4 shipped and what J-01/J-04's own spec text says.

The one genuinely new *runtime behavior* this iteration adds — the progress line's "(N from
cache)" clause finally being able to show a non-zero N on a **resumed** compute — reuses the exact
UI element iter-4 already shipped (`data-testid="edge-report-compute-progress"`); no new element,
no new label. Browser QA could not exercise the N>0 case live (UT-07, SKIPPED) because neither
committed fixture (`datasets_j03`, `apps/backend/tests/fixtures/datasets`) has any eligible pair to
resume — this is a fixture limitation, not a UI gap: the annotation's code path was reviewed and
shipped in iter-4, and its cache-hit-counting logic has authoritative non-vacuous proof at the
pytest level (TC-6/TC-8/TC-10/TC-11, part of the iteration's green 1517-test suite). This is
reported as a verification note below, not a discoverability flag.

## Regression Risk

Frontend code carries **zero** regression surface this iteration (byte-identical file tree). The
risk instead runs through shared **backend** plumbing this iteration modified
(`edge_report.py`, `edge_report_compute.py`, `routes.py`) that prior UI-visible journeys read
through:

| Shared component | Prior feature it serves | This iteration's change | Risk level | Verified how |
|---|---|---|---|---|
| `edge_report.py` / `edge_report_compute.py` (`_split_cells`, `run_strategy_comparison_report`, `EdgeReportComputeManager.trigger()`) | J-04's "Compute edge report" button (iter-4) — the on-page click→progress→result cycle | Added `run_pair=None` seam, `sub_cache=None` param, cache-hit counting; `trigger()` now threads a real `sub_cache` | High risk in theory (central to J-04's workflow) — mitigated by construction: `run_pair=None`/`sub_cache=None` defaults are byte-identical to the pre-J-05 code path (proven by TC-13), and TC-12 guards that `trigger()` never passes `workers>1`. Browser-verified: `UT-02` (happy path) and `UT-06` (failed-state) both PASS, rendering identically to iter-4's documented behavior | Live browser (`UT-02`, `UT-06`), pytest byte-identity (TC-4, TC-13) |
| `routes.py` (`trigger_edge_report_compute`) | J-04's `POST /research/edge-report/compute` route the button calls | New `get_edge_report_backtest_cache()` dependency injected; route path/request/response shape unchanged | Medium (route wiring, not route shape) | Live browser (`UT-02`), curl lifecycle in dev handoff, TC-13 |
| `edge_report.py`'s `_ProgressReporter` | J-04's progress line (`backtests_from_cache` field, displayed since iter-4 but dead) | Gains `note_cache_hit()` | Low — additive, only activates on a cache hit; cold-run behavior (all current fixtures) unaffected, confirmed absent in `UT-01`/`UT-02` | Live browser (`UT-01`, `UT-02`) |
| `levels.py` / `tradability.py` / `backtests.py` | J-03's arm memo; Tradable Map (`/research/tradability`) | **Git-confirmed byte-unchanged** this iteration — consumed at greater volume by new process-pool workers, never modified | Low by construction (no file touched) | `git diff --stat` (dev handoff), full suite green including `test_levels.py`/`test_tradability.py`/`test_backtests.py` source-introspection guards |
| `bars.py` / `datasets.py` / `dataset_index.py` | J-02's store caching; Tradable Map's bar-series read path | **Git-confirmed byte-unchanged** | Low by construction | `git diff --stat`; live browser exercised the read path (`UT-05`: symbol=PG on Tradable Map correctly returned the honest "No bar series recorded" state, no crash) |
| `/structure` page shell (Tradable Map, Case Studies, Fetch-from-Yahoo, Registry, Comparison sections) | tradable_wall (era 5B) and yahoo_fetch (era 5) — prior UI-shipped sections sitting beside the Edge Report panel on the same page | Zero code diff; re-verified as regression sentinels because they share the page with the modified backend plumbing | Low, confirmed intact | `UT-05` (all 6 headings present, no crash, no blank section — `UT-05-top-tradable-case-studies.png`, `UT-05-registry-comparison.png`), `UT-08` (standard-instance scroll, `UT-08-standard-structure-top.png`/`-bottom.png`) — I opened both images directly and confirm all sections render with the same dark/terminal-dense visual language and the same section order as prior iterations |
| Cockpit / Journal / Studies / Performance (SIM-BUYER/SIM-SELLER, replay studies, PnL register) | Foundational journeys predating this interlude (J-07 regression sentinel) | Not touched by this iteration's diff at all | Low | `UT-J-07`: full 9-step golden-script walkthrough manually re-executed and PASSED (SIM-BUYER → `buyer_control`; SIM-SELLER → `seller_control`; journal, studies, performance all correct) |

**One data point worth surfacing, correctly resolved by the phase itself:** the automated
deterministic-replay lane (`phase-goal-fast_wall-iter-5-regression-replay-results.md`) reported a
FAIL for `UT-J-07` ("step 03 expected 'buyer_control' did not appear"). I opened its own evidence
screenshot (`reports/qa/goal-fast_wall-iter-5-evidence/J-07-verify.png`) directly: it shows "Backend
unreachable — is the API running?" and "navigation unavailable — backend unreachable" — i.e., the
backend was genuinely down at that check, not a rendering regression. This matches the merged
report's own reconciliation and the "Notable Finding #1" explanation (a self-inflicted `.next`
build-cache collision from running two `next dev` processes against the same directory during this
QA session, unrelated to any product code change). I independently opened the manual
re-verification screenshot (`J-07-sim-buyer.png`) and confirm it shows a fully working cockpit —
tape state "Unclear" warming up correctly under scenario `buyer_control`, feed `Simulated`, live
quote/features/trades all populated. The FAIL was correctly identified as an infra false-negative,
not a product regression, and both the replay-results file and merged results file already carry
this reconciliation note. I flag this only as a **process note**, not a UX regression: a second QA
lane running two dev servers against one shared `.next/` cache is a recurring hazard worth avoiding
in future sessions, but it did not ship in the diff and does not affect real users.

## UI vs Backend Parity

| Backend capability (this iteration) | UI exposure | Assessment |
|---|---|---|
| `EdgeReportBacktestCache` (durable per-pair resumability) wired into `EdgeReportComputeManager.trigger()` | Inherited invisibly by the existing "Compute edge report" button — a resumed compute now finishes faster and the already-shipped "(N from cache)" annotation can show N>0 | Appropriate: this is a robustness/performance change to an existing action, not a new capability requiring a new element. The existing UI already has the display hook (`backtests_from_cache`, shipped iter-4); reusing it rather than adding a new one is correct, not a gap |
| `ProcessPoolExecutor` multi-process parallel sweep (`--workers N`) | CLI-only (`python -m app.research.edge_report_compute --workers N`); explicitly NOT wired into the button path | **Intentionally backend-only, correctly documented** — this is a named, reasoned, reversible scope decision (`runs/goal-session-fast_wall/state/assumptions.md`'s iter-5 entry, plan's "Scope Decision Already Logged" section, goal.md's own NOTES: "process-pool execution is CLI-only this iteration... Reversible with no signature-breaking change later"), driven by a real constraint (keeping multiprocessing out of the always-on FastAPI/uvicorn process). `user-visible-changes.md`'s "Not Visible Yet" section states this plainly for a human reader. This matches the "intentionally backend-only for this phase — acceptable" carve-out; no parity gap to flag |
| `get_edge_report_backtest_cache()` routes.py dependency | None — internal wiring only, no new route/response field | Correct: purely an implementation-detail change, nothing for a user to see |

Carried-forward (not new this iteration, not worsened, already transparently documented since
iter-4): no Cancel button for a running compute (`POST /research/edge-report/compute/cancel` exists
server-side, no UI caller) and no Force-recompute UI control (button always sends `force: false`).
Both are unchanged pre-existing gaps outside this iteration's scope, honestly disclosed in
`user-visible-changes.md`'s "Not Visible Yet" section rather than silently dropped. Not flagged
against this iteration.

## Flags

### Hidden Capabilities
None. No new capability shipped this iteration to hide.

### Undiscoverable Capabilities
None. The one capability under re-verification this iteration (the Edge Report compute cycle) was
directly confirmed reachable in 1 click + scroll from the home page (`UT-09`).

### Potential Regressions
None confirmed. All shared-component risk (see Regression Risk table above) was proactively
mitigated by default-preserving signatures plus byte-identity tests (TC-4, TC-13) and independently
verified through a live, multi-section browser pass (`UT-01` through `UT-09`, `UT-J-01`, `UT-J-04`,
`UT-J-07`) — all PASS. The one lane that reported a FAIL (`UT-J-07` via the deterministic replay
script) was checked against its own screenshot and confirmed to be a transient
backend-unreachable infra artifact, not a rendering or behavior regression, matching the project's
own established iter-4 lesson for this exact class of false-negative.

### Visual Consistency
Zero frontend diff this iteration — there is no new page or new visual element to check against
DESIGN SYSTEM tokens. I opened `UT-08-standard-structure-top.png`, `UT-09-discoverability.png`, and
`UT-06-failed-compute-error.png` directly: all sections (Tradable Map, Case Studies, Edge Report,
Fetch from Yahoo Finance, Registry) render in the same dark slate/amber/red terminal-dense visual
language established in prior iterations (era-4 structure_ui through era-5B tradable_wall) — same
panel borders, same amber degraded-state container for the not-computed/failed panel, same button
styling. No arbitrary values or new effects observed, consistent with the plan's explicit "no new
visual language" Design Direction for this iteration.

## Recommendation

No action required. This iteration correctly matched its own stated scope: zero new frontend
surface for zero new user-facing capability, the existing "Compute edge report" capability's
discoverability was actively re-confirmed (not just assumed) via a live browser pass, and every
shared-component regression risk introduced by the backend diff was both structurally mitigated
(byte-identity-preserving default parameters) and empirically verified against a running browser
across all `/structure` sections plus the cross-page J-07 sentinel.

One non-blocking note for a future iteration, not this one: when J-06 or a later iteration finally
produces a fixture/scenario with eligible resumable pairs, add a browser-QA case that actually
exercises the "(N from cache)" N>0 render (currently UT-07 SKIP) so this becomes visually confirmed
rather than resting solely on pytest-level proof.
