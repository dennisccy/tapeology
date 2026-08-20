# goal-rapid-microscope-iter-21 Dev Handoff

**Phase:** goal-rapid-microscope-iter-21
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

J-09's shared foundation (structure-context-conditioned anchor extraction plus a real band-touch
enumerator), all three predeclared pilot-study specs frozen in source in goal.md's stated priority
order, and the delta-divergence-at-level-tests candidate taken through a genuine screen + walk-forward
floor check on a committed hermetic fixture, rendered through the already-shipped Scout Ledger
section.

- **`micro_join.enumerate_band_touches(dataset_meta, dataset_store, resolver)`** (new) — the
  band-touch enumeration primitive goal.md names. Resolves the band map ONCE per dataset, at the
  dataset's own window start (a recorded RTH window never spans an ET midnight); an unresolvable
  map is an honest empty list. Reads the dataset's RAW event stream
  (`DatasetStore.load_events` — an existing, already-sanctioned store reader, the same call
  `micro_readiness.py`'s own `fallback_frac` fold already makes) rather than a built snapshot, so
  band-touch enumeration never requires a snapshot to already exist, and the expensive event load
  only happens AFTER the (cheap, durable-cache-backed) band map resolves — the common case today
  (no operator-warmed tradability map for most symbol/dates) pays only the resolver lookup. A
  touch mirrors `setups.py`'s own `_touches` "first touch, re-arm only once fully exited" rule,
  applied to a trade price against `[price_low, price_high]` instead of a bar range; each band
  arms/disarms independently. `_band_id(band)` is a stable identifier from a band's own
  `(side, price_low, price_high)` — never `quality_score`/`class`/`members`.
- **`micro_join.joinable_corpus_counts(...)` gains an optional, keyword-only `resolver` param**
  (default `None`) — omitted, `band_touch_count` stays the pre-J-09 `not_enumerated` sentinel
  (byte-identical to every existing caller); given, `band_touch_count` becomes the real
  `{"status": "enumerated", "count": <int>}`, summed via `enumerate_band_touches` over the SAME
  withheld-excluded dataset list `playbook_signal_count` already reads (a sealed shard's events
  are never read for either count).
- **`micro_readiness.build_readiness(...)` gains an optional `resolver` param**, threaded straight
  through to `joinable_corpus_counts` (only when `playbook_store` is also given).
- **`GET /research/desk/micro/readiness` now ALWAYS constructs a `BandMapResolver`** (the
  established `desk_routes.py` `GET .../playbook/{id}/context` construction call, verbatim —
  `compute=False`, GET-never-computes) from the existing `routes.get_bar_store` dependency, so
  `joinable_corpus.band_touch_count` is materialized to a real int on the LIVE route from this
  iteration forward.
- **`scout.extract_anchors` now dispatches on `structure_context_kind`** — `"none"` (unchanged
  original body), `"band_touch"` (new: enumerates touches via `micro_join.enumerate_band_touches`,
  joins each via `micro_join.join_band_touch` — reuses the SAME join primitive J-03 already
  proved), `"playbook_signal"` (new: reads recorded signals via a `playbook_store`, optionally
  narrowed by a new `setup_id` kwarg, joins each via `micro_join.join_playbook_signal`).
  `ScoutUnsupportedStructureContextError` now fires only for a value genuinely outside the closed
  `STRUCTURE_CONTEXT_KINDS` set (there is none today — all three are wired). `resolver`/
  `playbook_store` are required-when-relevant kwargs; omitting the wrong one raises a clear
  `ValueError`, not an opaque `AttributeError`.
- **`scout._extract_divergence_anchors`** — the delta-divergence feature's dedicated PAIRED-touch
  path (dispatched automatically inside the `"band_touch"` branch when
  `feature_name == "divergence_at_level_bearish"`): for every pair of CONSECUTIVE touches
  (tau1 < tau2) of the SAME band within one dataset, reuses `micro_features.divergence_at_level`
  VERBATIM over that pair's own `cumulative_delta` readings (read straight off the two touches'
  own snapshot rows, never recomputed) plus a trailing `(anchor_at, mid)` price history and the
  session-prefix baseline trade-volume windows this iteration's own `_windowed_trade_volumes`
  helper builds (new plumbing — the formula itself was already 100% pre-coded in
  `micro_features.py`; only its inputs were unbuilt, per the phase spec's own BACKGROUND).
  `feature_value` is `1.0`/`0.0` for `bearish_divergence` True/False (never a third fabricated
  state), reusing the EXISTING threshold-transform membership check rather than inventing a
  "boolean" transform kind.
- **`scout.pilot_study_candidate_grid(dataset_store, grid_version=1)`** (new) — the three
  predeclared pilot-study candidate-registration requests, keyed by
  `PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION` / `PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS` /
  `PILOT_STUDY_CAPITULATION_EXHAUSTION`, in goal.md's stated priority order, each with fully
  constructed `feature`/`structure_context`/`outcome`/`econ_floor` fields. Study 1 = `band_touch` +
  `failed_aggression_score` (its real screen's `refill_consistent` co-occurrence disclosure is
  named as future work — a joint two-feature condition the current single-feature threshold
  membership check does not express yet). Study 2 = `band_touch` +
  `divergence_at_level_bearish`. Study 3 = `playbook_signal` + `failed_aggression_score` +
  `setup_id="capitulation"`.
- **`scout.build_candidate_spec_fields`/`register_and_screen_candidate` gain an optional
  `setup_id` kwarg** — lands in `structure_context` ONLY when given (Study 3's own frozen field);
  every pre-J-09 spec (`setup_id` omitted) keeps a byte-identical `structure_context` shape.
- **`scout.register_screen_and_walkforward_check(...)`** (new) — screens ONE candidate
  (`register_and_screen_candidate`, unmodified), THEN runs its walk-forward floor check
  (`walkforward.scout_candidate_walkforward_floor_check`) and appends the resulting decision as a
  SECOND ledger row under the SAME `candidate_id` (the `scout_ledger.py` append-only "a later
  stage's outcome is a new row, never an edit" precedent). Never calls `evaluate_mode_b_fold`
  (source-level guard-tested).
- **`walkforward.scout_candidate_walkforward_floor_check(...)`** (new) — whether a Scout
  candidate's own anchor corpus clears the floor for ONE walk-forward fold before any fold is ever
  evaluated. Only sessions NOT already exposed before the candidate's own `registered_at` count
  toward the floor; an exposure registry with NO entries at all for the corpus is read
  conservatively as "nothing proven" (zero OOS sessions), never the opposite — an uninitialized
  registry's `is_exposed_before` always answers `False`, which would otherwise let an
  already-published legacy corpus masquerade as fresh out-of-sample evidence. Reuses
  `summarize_fold_observations`'s own `WF_FOLD_MIN_OBSERVATIONS`/`WF_FOLD_MIN_SIGNAL_SESSIONS`
  floors verbatim plus a session-count floor (`WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS`).
- **`POST /research/desk/micro/scout/compute` gains an additive, optional JSON body**
  (`{"grid": "delta_divergence_pilot"}`) — omitted (or no body at all, every pre-J-09 caller),
  behavior is byte-identical (the unchanged default reference grid).
  `scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT` selects a ONE-ELEMENT grid — the SAME frozen
  delta-divergence request `pilot_study_candidate_grid` carries, with a `BandMapResolver`
  (constructed from the existing `routes.get_bar_store` dependency) attached. Studies 1 and 3 are
  structurally UNREACHABLE through this selector, the CLI, or the manager — no other pilot-grid
  value exists anywhere in the wiring. `scout.py`'s CLI (`python -m app.research.scout`) gained
  the mirrored `--grid {default,delta_divergence_pilot}` flag.
- **New guard/source-scan test** (`tests/test_micro_no_referee_evidence_guard.py`) — proves zero
  `micro_*.py`/`scout*.py`/`walkforward*.py`/`vault.py` module imports or calls
  `referee_evidence.strategy_trade_readiness`/`referee_evidence.referee_evidence` (both defined in
  `referee_evidence.py`), as either a direct name import or a module-qualified attribute call.
  Correctly distinguishes the banned shapes from the EXISTING legitimate
  `from .referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS` import `micro_readiness.py`
  already makes (a counter-test proves the scan never flags it).
- **Frontend: Scout Ledger row rendering fix** (`apps/frontend/app/desk/page.tsx`) — the Feature
  cell now shows `structure_context.kind` inline (e.g. `divergence_at_level_bearish / threshold
  (band_touch)`) whenever it is not `"none"`; a `"none"`-kind row (every shipped J-04 default-grid
  row) renders byte-identical text to before this iteration. No new column/heading (T-11) — the
  addition lives inside the EXISTING Feature `<td>`. `lib/types.ts`'s `ScoutTrialRow.
  structure_context` widened to `{ kind: string; setup_id?: string }` (additive, matching the
  backend's new optional field).
- **Frontend: Microscope Readiness — `joinable_corpus.band_touch_count` now rendered** — one new
  row ("Joinable corpus — band touches") in the existing Sealed Tranche table, showing the real
  materialized int or the honest `"not enumerated"` string. `lib/types.ts` already carried the
  correct type for this field (its own comment named this "a future J-09 home" — this iteration
  is that home); only the render was missing.
- **`J-10.json` restored** — steps 9-10 (`desk-section-expand-playbookEvidence` → "Built from
  signature:"; `desk-playbook-date-input` fill "2026-06-22" → "recorded signals, none hidden")
  reinstated at positions 9-10, with the iter-16-added
  microReadiness/scoutLedger/walkForward/validationVault steps renumbered to follow (now steps
  11-14), then refereeRegistry/refereeAdjudications/refereeRuns (15-17). The iter-16 changes to
  `structure-as-of-input` ("16:00:00") and `validationVault`'s expected text
  ("iter18-qa-universe") were kept, NOT reverted (per the plan's own instruction). Both restored
  strings verified still present verbatim in the current frontend source
  (`grep` against `apps/frontend/app/desk/page.tsx`) before finalizing.

## Files Changed

- `apps/backend/app/research/micro_join.py` — new `enumerate_band_touches`/`_band_id`;
  `joinable_corpus_counts` gains optional `resolver`; `BAND_TOUCH_STATUS_ENUMERATED` constant.
- `apps/backend/app/research/micro_readiness.py` — `build_readiness` gains optional `resolver`,
  threaded to `joinable_corpus_counts`.
- `apps/backend/app/research/micro_routes.py` — `GET /readiness` always constructs a
  `BandMapResolver`; `POST /scout/compute` gains the additive `grid`-selector body param.
- `apps/backend/app/research/scout.py` — `extract_anchors` dispatch
  (`_extract_none_anchors`/`_extract_band_touch_anchors`/`_extract_divergence_anchors`/
  `_extract_playbook_signal_anchors`), `_windowed_trade_volumes`, `_signal_in_dataset_window`,
  `_outcome_at_horizon`, `pilot_study_candidate_grid`, `register_screen_and_walkforward_check`,
  `GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`, `setup_id` threaded through
  `build_candidate_spec_fields`/`register_and_screen_candidate`, `ScoutComputeManager.trigger`'s
  `grid_selector`/`resolver` params, CLI `--grid` flag, `divergence_at_level_bearish` added to
  `FEATURE_FAMILY_OF` (F-FLOW).
- `apps/backend/app/research/walkforward.py` — new `scout_candidate_walkforward_floor_check`.
- `apps/backend/tests/test_micro_join.py` — TC-3 (band-touch enumerator oracle, 3 tests + a
  two-independent-bands test), TC-9 (`joinable_corpus_counts` materialization, 3 tests).
- `apps/backend/tests/test_micro_readiness.py` — `client`/`scout_client`-style fixture gains a
  `bar_store` override (needed once the readiness route always constructs a resolver);
  TC-15/route-level tests updated for the materialized `band_touch_count` shape.
- `apps/backend/tests/test_scout.py` — TC-1/TC-2 (`extract_anchors` band_touch/playbook_signal),
  TC-4 (pilot grid shape + 3 distinct `family_root_id`s), TC-5 (delta-divergence full screen on a
  hand-derived oracle fixture), TC-6 (walk-forward floor check + ledger recording), TC-7 (Studies
  1/3 frozen but never screened), plus route-level tests for the additive grid-selector body.
- `apps/backend/tests/test_walkforward.py` — direct unit tests for
  `scout_candidate_walkforward_floor_check` (fresh registry, exposed-session exclusion, a genuine
  sufficient case, the never-calls-evaluate_mode_b_fold source guard).
- `apps/backend/tests/test_micro_no_referee_evidence_guard.py` (new) — TC-10.
- `apps/frontend/app/desk/page.tsx` — Scout Ledger Feature cell renders `structure_context.kind`
  inline.
- `apps/frontend/lib/types.ts` — `ScoutTrialRow.structure_context` widened additively.
- `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` — steps 9-10 restored,
  renumbered.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **3,314 passed, 8 skipped, 0 failed, 0 errors, 644.04s (0:10:44)** — comfortably above the
DoD's `>= 3,281` floor (iter-19's own recorded baseline), 0 regressions, 8 skips matching the
established baseline exactly. This is the FINAL run, against the complete diff (including the
readiness-route "band touches" row and the TC-9 route-level test, both added after an earlier,
intermediate full run of 3,311 passed had already confirmed the rest of the diff clean).

New/changed modules run in isolation, all green before the full run:
- `tests/test_micro_join.py` — 44 passed
- `tests/test_micro_readiness.py` — 198 passed
- `tests/test_scout.py` — 69 passed (67 + 2 new grid-selector route tests)
- `tests/test_walkforward.py` — 74 passed (70 + 4 new TC-6 unit tests)
- `tests/test_micro_no_referee_evidence_guard.py` — 4 passed

`Config().config_fingerprint()` == `08e471b10130e1e2` (unchanged — zero new `Config` fields, per
`git status` confirming no `app/config.py` diff). Zero `referee_*.py` files touched (`git status`
confirms).

Frontend: `rm -rf apps/frontend/.next && npm run build` — clean build, `Compiled successfully`,
type-check passed, all three routes (`/`, `/desk`, `/structure`) prerendered.

## Known Issues

- **Studies 1 and 3 (range-wall failed aggression, capitulation exhaustion) are explicitly
  deferred this iteration** — frozen-in-source in `scout.pilot_study_candidate_grid`, fully
  constructed and unit-tested for shape (TC-4), but NOT passed through
  `register_and_screen_candidate` (TC-7 proves this negative directly). Per Success Criteria's own
  scope-pressure order ("up to two of the three pilot studies are deferrable"). Study 1's own real
  screen additionally needs a joint two-feature (`failed_aggression_score` +
  `refill_consistent`) co-occurrence condition that today's single-feature threshold membership
  check does not express — named as future work in the pilot grid's own comment, not built here.
- **The r5 §10.7 UI-caveat half stays dropped** (per the phase spec's own NOTES) — only the
  guard/source-scan half (TC-10) is in scope; `referee_evidence.py` is byte-frozen this era and
  has zero live UI/API consumers to attach a caveat sentence to.
- **UT-10's element-capture re-take was NOT performed by this developer pass** — the underlying
  markup (`data-testid="scout-ledger-unavailable"`, `UnavailablePanel`) is unchanged by this
  iteration's diff, so the existing `window.fetch`-override technique should still work
  unmodified; the actual browser screenshot capture is left to the browser-qa-agent's own pass
  (this iteration touches `apps/frontend/app/desk/page.tsx` near, but not inside, this specific
  panel's render path — confirmed via source read).
- **The walk-forward floor-check row's `screen_result` field is `null`** in the Scout Ledger's
  collapsed JSON detail (honest — there is no statistical screen for this row, it is a SEPARATE
  ledger entry recording the walk-forward eligibility decision under the same `candidate_id`).
  This reads slightly oddly in the UI (a `null` value where a screen's disclosures usually sit)
  but is never fabricated; a future iteration could give this row's own dedicated rendering if
  desired.
- **Verified live against the real production backend** (`scripts/dev.sh`, port 8301, the real
  `.data/` corpus): `GET /research/desk/micro/readiness` returns HTTP 200 with
  `joinable_corpus.band_touch_count == {"status": "enumerated", "count": 8247}` — a genuine,
  non-zero, real count (at least one of the 18 registered tick datasets' own symbol/date already
  has an operator-warmed tradability map on disk, so the enumerator's expensive path genuinely ran
  against real tick data and completed without error). The dev handoff's own earlier prediction of
  a "likely zero" was a reasonable guess made before this live check and is corrected here by the
  actual observed result.
- Out of scope, confirmed untouched: any recorder/vault real-tape work, any `referee_*` module,
  any engine change, any threshold/constant not already pinned in spec §1, a UI trigger button for
  the pilot grid (CLI/manager-only this iteration, matching the "operator act, not goal-mode act"
  framing).
- **Pre-existing `scripts/dev.sh` bug found during pre-handoff service-startup verification (NOT
  caused by this iteration's diff -- the script itself is untouched).** Sending `SIGINT` to the
  `dev.sh` process (the documented Ctrl+C stop path) correctly stops the backend (uvicorn) and the
  `npm exec next dev` wrapper, but the actual `node .../next dev` grandchild process survives as an
  orphan (reparented to PID 1, still bound to :3301) — `dev.sh`'s own trap only signals
  `$BACKEND_PID $FRONTEND_PID` (the direct children), never the `npm exec` shim's own child.
  Verified live: started the servers, sent `SIGINT` to the `dev.sh` PID, confirmed via `ps` that
  the Next.js `node` process was still running and the port still bound; killed it manually,
  confirmed a second `bash scripts/dev.sh` start then succeeds cleanly with no port conflict (the
  script's own leading `lsof`/`fuser` port-clearing loop recovers from the orphan on the NEXT
  start, just not on stop). This is a genuine, reproducible gap in the shared dev-launch script,
  outside this iteration's own file scope (`scripts/dev.sh` is not part of this diff and the plan
  names no reason to touch it) — reported here for visibility rather than fixed, per "Do NOT touch
  code outside your task scope."

---

## Addendum — full backend suite result (final, definitive)

```
3314 passed, 8 skipped, 2 warnings in 644.04s (0:10:44)
```

0 failed, 0 errors, exit code 0. The 2 warnings are the same pre-existing library deprecation
notices every prior iteration's own suite carries (`httpx`-via-`starlette.testclient`,
`websockets.legacy`), unrelated to this iteration's changes. `Config().config_fingerprint()`
re-verified == `08e471b10130e1e2` after this run.
