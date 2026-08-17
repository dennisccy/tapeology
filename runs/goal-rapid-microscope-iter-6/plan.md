# goal-rapid-microscope-iter-6 Execution Plan

Session: `rapid-microscope` · Era: "The Rapid Microscope" · Target journeys: **J-05** (close two
wiring gaps), **J-10** (kept-product sentinel, first real run this era) · Required-still-passing:
J-01, J-02, J-03, J-04. Depth `full` (mandatory — prior verdict was `ESCALATE`).

Canonical sources (read from, never re-derived): phase spec
`docs/phases/goal-rapid-microscope-iter-6.md` (its own DEFINITION OF DONE / TC-1…TC-12 is the
source of truth; this plan condenses it, never replaces it); `docs/handoffs/goal-rapid-microscope-
iter-5-audit.md` findings B2 and B5 (the two gaps this iteration closes, with exact file:line
anchors, reproduced below); `docs/handoffs/goal-rapid-microscope-iter-5-dev.md` (what iter-5 already
shipped — do not re-derive).

## Alignment check

Tightly scoped to two named findings from iter-5's own audit, both of which map directly to
`docs/goal.md` rails: B5 (TR-15 unreachable) is Success Criterion #2 ("no leakage trap fails,
ever"); B2 (tick corpus never exposure-seeded) is a live latent breach path of the critical anti-goal
"the 12 pre-existing tick symbol-days are permanently exploratory — never... `historical_oos`". No
drift found — nothing here touches the frozen engine, referee modules, or any §1 spec constant.
Rebuilding or re-deriving iter-5's already-verified machinery is explicitly out of scope (binding
per iteration-state's "Do not redo").

**Frontend Present is declared `yes` even though this iteration's code diff is 100% backend.** This
is not a claim that new UI shipped — see the dedicated section below for the full rationale; the
short version: iter-4 and iter-5 both tried `Frontend Present: no`, and both times
`scripts/automation/browser-qa-phase.sh`'s `detect_frontend_in_plan` (confirmed by reading
`lib/common.sh:1502-1507`: a blind `grep -qi "frontend present: yes"`) short-circuited the ENTIRE
browser lane before `browser-qa-agent` ever dispatched — including the required-still-passing set
(J-01–J-04) and J-10's sentinel. iter-5's own plan tried threading the needle with an explicit
"MANDATORY browser regression" prose section under `Frontend Present: no`; the gate does not read
prose, only the literal string, so it still skipped everything (iter-5 audit finding E1, confirmed
live against `reports/phase-goal-rapid-microscope-iter-5-ui-test-results.md`: "SKIPPED —
Backend-only phase"). `Frontend Present: yes` here is the mechanical fix, not a UI claim.

## What to Build

Backend only (`apps/backend/app/research/`) — two wiring fixes plus their tests:

1. **Wire TR-15 into the one production fold-building call site.**
   `require_sufficient_sessions_for_folds` (confirmed at `walkforward.py:335` as of iter-5's audit;
   re-locate by symbol name, not line arithmetic — the audit's B1/B3 fixes shifted nearby lines)
   raises the typed `InsufficientSessionsForFoldsError` naming the exact shortfall, and is already
   proven by TC-20, but has zero callers in `app/`. `run_diagnostic_walkforward` (starts ~`walkforward
   .py:1010`) goes straight to its one `build_folds` call, which silently returns `[]` for a
   below-floor corpus instead of refusing (iter-5 audit B5: "the empty fold report standing in for
   the refusal that TR-15's own wording forbids"). Call `require_sufficient_sessions_for_folds`
   immediately before that `build_folds` call. Today's real corpus (155 sessions) stays far above the
   105-session floor, so this is defensive and must not change today's served result (TC-1).
2. **CLI catch for the new exception.** Give the CLI's `main()` a clean `except
   InsufficientSessionsForFoldsError` — print the typed message, exit non-zero, never an unhandled
   traceback (TC-4). Separately, verify (do not re-plumb) that `WalkForwardComputeManager.trigger`'s
   existing generic exception handler already resolves a raised exception from the compute route's
   worker to `{"state": "failed", "error": str(exc)}` (TC-3) — this is a read-and-confirm step, not a
   code change, unless the verification finds it does NOT already cover this case.
3. **Seed the §6.7 exposure registry for the legacy tick corpus.** The seeding mechanism already
   exists (`micro_accessor.py:169`, `initialize_r2_exposure_registry`; guard
   `has_any_exposure_entries`) but production only ever calls it for
   `PLAYBOOK_DIAGNOSTIC_CORPUS_ID` (`walkforward.py:1072`, iter-5 audit B2). Add a second seeding
   call, same pattern, same guard, for a NEW `corpus_id` distinct from
   `playbook_setups_diagnostic_v1` (naming is an implementation choice — log it in the dev handoff,
   don't invent it silently per T-1), covering every session window of every currently-registered
   tick dataset. Resolve the tick dataset list exactly the way `micro_readiness.py` already does
   (via `config.dataset_dir_resolved()`) — no second inventory mechanism, no hardcoded date list;
   today, "every registered tick dataset" and "the 12 legacy symbol-days" are the same 18-dataset/
   12-symbol-day set (J-06 hasn't landed), which is what makes seeding safe now (TC-5, TC-6).
4. **Trigger point discipline.** The new seeding call fires from the SAME operator-act entry point
   the playbook seeding already uses — inside `run_diagnostic_walkforward` — never from a GET route
   (era Non-Goal: "No scheduling"; T-8).
5. **Prove the two mechanisms stay separate (TC-7).** After the change, re-read
   `micro_readiness.py`'s served `exposure_state` per shard (real store) and confirm all 18 shards
   still read `exploratory`. The walk-forward-internal `ExposureRegistry` (used only to classify a
   future spec/window pair `historical_oos` vs `historical_exposed_diagnostic`) and the
   readiness-served vault `exposure_state` (`exploratory`/`hand_assigned`) are two different
   mechanisms and must never be conflated.
6. **Tests** (`apps/backend/tests/test_walkforward.py`, extended, not a new file):
   - TC-2: a fake session list below `minimum_sessions_for_sufficient_folds` (105), fed through the
     SAME production path `run_diagnostic_walkforward` uses (via the existing
     `_FakePlaybookStore`/`_FakeUniverseStore` doubles) raises `InsufficientSessionsForFoldsError` —
     proving the production path itself raises it, not just the standalone function TC-20 already
     covers.
   - TC-3: the compute route's worker raising the error resolves to
     `{"state": "failed", "error": "<exact shortfall message>"}`, never an unhandled 500.
   - TC-4: CLI integration test against a below-floor scoped fixture store — prints the typed
     message, non-zero exit, no traceback.
   - TC-5: first-seed test — a never-before-seeded registry gains one exposure entry per session
     window of every currently-registered tick dataset, under the new distinct `corpus_id`.
   - TC-6: idempotent-reseed test — running the same operator act a second time leaves the
     tick-corpus row count unchanged (mirrors the existing playbook `has_any_exposure_entries`
     guard).
   - TC-7: `micro_readiness.py` exposure_state re-check (all 18 shards still `exploratory`).
   - TC-1: the real 155-session corpus run stays byte-identical to iteration 5's recorded values (5
     folds, 100 validation sessions, sequence verdict refused "2 < 3") — proving the new TR-15 guard
     is silent on the path that already passes it.
7. **Dev handoff** at `docs/handoffs/goal-rapid-microscope-iter-6-dev.md` naming both fixes with
   their exact file:line locations (TC-12) — required even though the two changes are individually
   small; this is a DEFINITION OF DONE checkbox, not optional boilerplate.
8. **Full-suite and frozen-foundation re-checks**: `cd apps/backend && .venv/bin/python -m pytest
   tests/` (no redundant `-q` — iter-0 lesson, keeps the pass/skip/fail summary legible) ≥ 3033
   pass / 8 skip / 0 fail (iter-5's post-audit baseline); `Config().config_fingerprint()` prints
   `08e471b10130e1e2`; all 6 `referee_*.py` SHA-256 hashes match the iteration-0 baseline listing.

## Agents Required

- developer: yes -- implements items 1-8 above (the two wiring fixes in `walkforward.py`, the CLI
  catch, the exposure-seeding call, and the TC-1..TC-7 test additions to `test_walkforward.py`).
  Zero frontend files. Zero new `Config` field. Zero new route (both fixes wire into the EXISTING
  `run_diagnostic_walkforward` operator-act path and the existing CLI `main()`).

## Frontend Present

Frontend Present: yes

**Why, given zero frontend code changes this iteration:** see "Alignment check" above for the full
mechanical root-cause. In short — this flag is machine-read by `browser-qa-phase.sh` to decide
whether to dispatch `browser-qa-agent` at all; a `no` here has caused TWO consecutive iterations
(iter-4, iter-5) to silently skip the entire browser lane, including the required-still-passing
regression set, which iter-5's own audit named as an unclosed gap and the exact iteration-4 failure
repeating. This iteration's actual DEFINITION OF DONE requires "Browser-qa-agent is genuinely
dispatched this iteration (not N/A-stubbed)" as its own checkbox — declaring `no` here would make
that checkbox fail by construction and reproduce the bug this iteration exists to work around. The
durable fix (making `detect_frontend_in_plan` read the already-exported
`CHAIN_GOAL_TARGET_JOURNEYS` safeguard instead of gating on this one field) is framework-maintenance
work outside this agent's authority and outside `docs/goal.md`'s Key Capabilities — flagged, not
scheduled. Per the phase spec's own Escalation flag: if the browser lane still fails to dispatch
despite `yes`, that is a 3rd consecutive miss and should be escalated to a human/framework-maintenance
session rather than retried a 4th time with the same workaround.

## UI Evolution

- New user-facing capability: **none.** No new page, section, button, or served field. This is a
  backend correctness-and-evidence iteration.
- New information displayed: **none.** `GET /research/desk/micro/walkforward`'s response shape is
  unchanged; a below-floor fold request now fails closed with a typed message instead of silently
  returning an empty result, but no new field is added and no currently-served value changes.
- New user actions: **none.**
- UI surface changes: **none.**
- Navigation changes: **none.**
- What the browser pass actually verifies (regression, not new capability): the **Microscope
  Readiness** section on `/desk` (J-01's overdue element screenshot — a real, non-fabricated tick
  corpus panel: checksums, coverage gaps, fallback fractions, floor-unmet states) and the full
  13-step kept-product sentinel (`journey-scripts/J-10.json`, unmodified — cockpit `/` live tape +
  chart, `/structure` load + Tradable Map, every shipped `/desk` section including the 3 Referee
  sections). Both are pre-existing, already-shipped surfaces; this iteration adds no new element to
  either.

## Visual Requirements

Not applicable — no new component, layout, or visual state is introduced. If any styling is touched
it would be an unplanned regression, not a deliverable. The browser pass reuses the shipped
dark-only, dense, terminal-grade design as-is (no diff expected).

## Files to Create/Modify

- `apps/backend/app/research/walkforward.py` -- MODIFY: (a) call `require_sufficient_sessions_for_
  folds` immediately before `run_diagnostic_walkforward`'s `build_folds` call; (b) `main()` gains an
  `except InsufficientSessionsForFoldsError` printing the typed message and exiting non-zero; (c) a
  new tick-corpus exposure-seeding call (naming/placement is an implementation choice — log it),
  mirroring the existing playbook seed at `walkforward.py:1072`, guarded by `has_any_exposure_
  entries`, resolving the tick dataset list via `config.dataset_dir_resolved()` the same way
  `micro_readiness.py` does.
- `apps/backend/tests/test_walkforward.py` -- MODIFY: add TC-1 through TC-7 per "What to Build" §6
  above.
- `docs/handoffs/goal-rapid-microscope-iter-6-dev.md` -- NEW: dev handoff naming both fixes with
  exact file:line locations (TC-12).

Explicitly untouched (Do-Not-Redo / out of scope, per the phase spec's OUT OF SCOPE section): J-06
(`vault.py`/`tick_recorder.py` — a new credentialed pillar, not this iteration); J-07/J-09 (not
reachable yet); J-08's `/desk` rendering sections (Scout Ledger/Walk-Forward/Validation Vault UI —
separate, larger UI journey); the two human-owned rulings (`micro_observer.py:636/657` timing stamp;
per-dataset "variants tried" counting); the J-09 percent-vs-bps unit pin (iter-5 audit B6, due before
J-09); the J-08-parked copy/guard-list additions (iter-5 audit B6/B7); B4 (sequence identity vs.
§6.4's "any other spec-field change", iter-5 audit, spec-owner scope); any `.tsx`/frontend file; any
`Config` field; any `docs/rapid-validation-spec.md`, `docs/goal.md`, or `blueprint.md` edit;
`journey-scripts/J-10.json` (reused byte-unmodified).

## Key Test Scenarios

(Condensed from the phase spec's own TC-1…TC-12 — cross-reference there for exact wording.)

- **TC-1** — the real 155-session corpus run, after this change, calls `require_sufficient_sessions_
  for_folds` before `build_folds`, passes silently, and serves byte-identical values to iteration 5
  (5 folds, 100 validation sessions, verdict refused "2 < 3").
- **TC-2** — a below-105-session fake list through the real `run_diagnostic_walkforward` path raises
  `InsufficientSessionsForFoldsError` naming the shortfall; never a success dict with empty `rows`.
- **TC-3** — the compute route's worker raising that error resolves `GET .../compute` to
  `{"state": "failed", "error": "<message>"}`; never an unhandled 500.
- **TC-4** — the CLI against a below-floor fixture store prints the typed refusal and exits non-zero;
  never a Python traceback.
- **TC-5** — first diagnostic walk-forward operator act against the real (or scoped copy of the) tick
  `DatasetStore` gives `exposure_registry.jsonl` one entry per session window of every currently-
  registered tick dataset, under a `corpus_id` distinct from `playbook_setups_diagnostic_v1`.
- **TC-6** — a second run of the same operator act leaves the tick-corpus row count unchanged
  (idempotent).
- **TC-7** — `micro_readiness.py`'s served `exposure_state` per shard, re-read after this change:
  all 18 shards still `exploratory`.
- **TC-8** (browser) — after a clean `rm -rf apps/frontend/.next` rebuild (T-9), browser-qa-agent
  under `Frontend Present: yes` captures the Microscope Readiness section's element screenshot
  showing real tick-corpus data, and `reports/phase-goal-rapid-microscope-iter-6-ui-test-results.md`
  records a real, non-SKIPPED verdict — closing J-01's `evidence_makeup` flag.
- **TC-9** (browser) — the same pass runs `journey-scripts/J-10.json`'s 13-step sentinel UNMODIFIED;
  every step renders the same real data prior iterations recorded; green for the first time this era.
- **TC-10** — full suite ≥ 3033 pass / 0 fail; fingerprint `08e471b10130e1e2`; all 6 `referee_*.py`
  SHA-256 hashes match the iteration-0 baseline.
- **TC-11** — J-01/J-02/J-03/J-04's golden replay scripts run (now reachable since the lane
  dispatches) and go green, or the LLM browser-qa lane covers any journey without a golden on file.
- **TC-12** — `docs/handoffs/goal-rapid-microscope-iter-6-dev.md` exists and names both wiring fixes
  with exact file:line locations.

## Escalation watch (for the evaluator, not the developer)

If `browser-qa-agent` is STILL N/A-stubbed / not genuinely dispatched despite `Frontend Present: yes`
this time, that is a mechanical failure distinct from the one this iteration works around (a 3rd
consecutive miss) and the phase spec's own instruction is to escalate to a human/framework-maintenance
session rather than retry a 4th time with the same workaround.
