# goal-rapid-microscope-iter-11 Execution Plan

Session: `rapid-microscope` · Era: "The Rapid Microscope" · Target journeys: **J-06** (step 3 of 5
only — deepening it, not completing 4/5), **J-10** (TR-2 widened to a deterministic inference
trap; trap count stays 19/22). Required-still-passing: **J-01, J-02, J-03, J-04, J-05, J-07**.
Depth `full` (mandatory — trigger 3, prior verdict `ESCALATE`, no discretion). This is the **third**
full-depth attempt at this class of work: iterations 3 and 8 both asked for full and were demoted
to lean by the deterministic budget arbiter before the independent auditor ever ran. The spec is
deliberately scoped to three EXISTING modules + their route file + test files — zero new modules,
zero new routes, zero new MCP tools, zero frontend files — specifically to protect the auditor's
slot this time.

Canonical sources (read from, never re-derived): phase spec
`docs/phases/goal-rapid-microscope-iter-11.md` (its own DEFINITION OF DONE / TC-1…TC-13 is the
source of truth; this plan condenses it, never replaces it); `docs/rapid-validation-spec.md` §7.1
(recorder progress, lines 478-490), §7.5 points 4/7/8 (the opaque-pool rule, lines 576-608), §9 TR-2
(the inference-trap definition, line 780); `docs/goal.md` J-06 step 3/5 (lines 552-598, byte-for-byte
consistent with the phase spec — confirmed by direct read, no drift); `docs/handoffs/
goal-rapid-microscope-iter-10-dev.md` (J-07 graduation, most recent shipped work — untouched this
iteration); `runs/goal-session-rapid-microscope/state/iteration-state.md` (the "Do not redo" list)
and `state/blueprint.md` (the iter-11 note documenting `sealed_tranche`'s semantic broadening — the
decomposer already edited this file this turn; no further edit needed from the developer).

## Alignment Check

Directly implements goal.md's critical anti-goal rail added this turn ("a recorded tranche is one
opaque research pool until its shards are exposed... no served surface may present a complete
per-shard list of EITHER side while any pool member is unexposed") and the matching J-06 step
3/5 text — both dated 2026-08-18, identical in substance to the phase spec's BACKGROUND. No drift
found. Two concrete code gaps ground the work (verified directly against the current tree, not
assumed from the prior evaluator's prose):

1. `tick_recorder.py`'s `TickRecorderComputeManager.snapshot()`/`_publish()` (confirmed at
   `tick_recorder.py:612,620-621,695,709-712`) carry a raw `progress.outcomes` list with per-chunk
   `symbol`/`date`/`dataset_id`, and `micro_routes.py`'s `GET /recorder/compute`
   (confirmed at `micro_routes.py:481-494`) forwards `snap["progress"]` verbatim — a live §7.1
   violation today, not hypothetical.
2. `micro_readiness.build_readiness` (confirmed at `micro_readiness.py:328`) calls
   `vault.withheld_universe_by_dataset_id` directly — a narrower, ledger-row-only check. A
   repo-wide grep confirms `seal_shard`/`assign_shard`/`expose_shard` have **zero production call
   sites** in `app/` today, so nothing wires the recorder to the vault at record time; the instant
   a real recording finalizes under a registered universe, it is fully identifiable in
   `GET /research/datasets` and readiness's `shards` list with zero code path standing in the way.

The fix is structural (a universe-RULE-driven predicate, safe the instant `register_universe`
runs) rather than procedural (wiring the recorder to call the vault at finalize time) — this is
the decomposer's own logged interpretation call, already recorded in `runs/
goal-session-rapid-microscope/state/assumptions.md`'s iter-11 entry. Do not re-derive it; build
against it. Zero cost against the real `.data` store (zero registered vault universes today, so
every change below is provably inert against it, matching every prior vault revision's own
"applied while zero shards are sealed" shape).

## What to Build

1. **`vault.py`** — one new shared predicate: "is this dataset part of an unresolved
   registered-universe pool," combining (a) today's ledger-row check
   (`withheld_universe_by_dataset_id`, unchanged) with (b) a new universe-rule membership check
   (`expected_recording_pairs()` × `created_utc >= registered_at`, resolved against
   `VaultUniverseLedger`'s rows via a new `universe_ledger_for_dataset_dir` resolver mirroring the
   existing `shard_ledger_for_dataset_dir` pattern verbatim). Store-agnostic — takes the caller's
   own `(dataset_id, symbol, session_date, created_utc)` tuples, never a `DatasetStore` import.
   The `created_utc >= registered_at` guard is what stops a universe registered LATER from
   retroactively withholding a pre-existing (e.g. one of the 12 permanently-exploratory legacy)
   symbol-day that happens to share a (symbol, date).
2. **`micro_snapshots.py`** — `withheld_dataset_ids_for_store`/`exclude_withheld` read the new
   predicate instead of the narrower ledger-only one. This is the ONE choke point; its 8 existing
   consumers (`scout.py`, `walkforward.py`, `micro_join.py` ×2, `edge_report.py`,
   `edge_report_cache.py` ×2, `pnl_scan.py`, `desk_screen.py`, `setups.py`) inherit the fix for
   free — **zero call-site changes in any of those 9 files.**
3. **`micro_readiness.py`** — `build_readiness`'s per-shard loop switches from the direct
   `vault.withheld_universe_by_dataset_id` call to the same new predicate. `sealed_tranche`'s
   field name and shape (`shard_count`/`symbol_days`/`by_universe`) are UNCHANGED — only which
   datasets populate it broadens. The withhold check must keep running BEFORE `store.load_events`
   (currently at `micro_readiness.py:368`), exactly as today's ordering already does.
4. **`tick_recorder.py` + `micro_routes.py`** — the live `progress` body stops serving raw
   `outcomes`; it serves aggregate-only fields instead: `chunks_total`/`chunks_done` (already
   present), new `chunks_fetched`/`chunks_reused`/`chunks_unchanged`/`chunks_failed` (reuse the
   per-outcome-type counting logic already written once for the run-log entry at
   `tick_recorder.py:638-641` — do not write a second copy), new `trades_total`/`quotes_total`
   (accumulated from each fetched chunk's `HistoricalWindow` at fetch time, never persisted
   per-chunk), `percent_complete`, `elapsed_seconds`. No `symbol`, `date`, `dataset_id`, or any
   other per-chunk field anywhere in the body, at any point during a run. **No operator-only
   bypass** anywhere on this route — r5 explicitly forbids one. `GET .../recorder/runs`
   (`_run_log_entry`) is already compliant; do not touch it.
5. **`test_vault.py`** — rewrite/widen the TR-2 suite into spec §9's deterministic inference-trap
   shape (register a fixture universe with a fully-known rule; populate a fixture store with some
   members ledger-tracked, some not; expose a proper subset via the existing
   `assign_shard`/`expose_shard` path; run the operator compute acts first — snapshot build, Scout
   run, edge report, PnL sweep — so the trap cannot pass merely because the rig computed nothing;
   sweep every route + recorder-progress + the `datasets` MCP tool; assert ≥2 candidate identities
   remain for every unexposed member and no complete identity-labelled partition is derivable).
   Add the counter-test proving the PRE-fix subtraction attack (list `GET /research/datasets`,
   compute the universe's expected set, subtract) would have isolated a unique identity before
   this iteration's fix — proving the main assertion is not vacuous.
6. **`test_micro_readiness.py` + `test_tick_recorder.py`/new `test_micro_routes.py`** — extended
   for the new withhold/aggregate behavior (see Key Test Scenarios below). Full backend suite
   re-run after every edit.

**Scope guardrail (do not widen).** Explicitly OUT OF SCOPE this iteration, per the phase spec —
do not let any of these creep in: J-06 step 4 (credentialed Alpaca recording — still human-blocked,
two owner questions open); the "exposed for exploratory use" release mechanism (genuinely
unspecified anywhere in the spec — leave it open per T-1, do not invent it); wiring
`tick_recorder._finalize_day`/`run_tick_recording` to call `vault.py` at record time (not needed —
the universe-rule predicate is safe without it); TR-3/TR-17/TR-22; J-10 step 2's deterministic-rerun
check; the two remaining owner questions (sealed-verdict authority, corrupted-ledger fail-open-vs-
closed) and the one-quote-early depletion stamp; J-08/J-09; any edit to `referee_*.py`, the `v1`
strategy, the `default` profile, `scout_ledger.compute_family_root_id`, `assign_shard`'s
single-shot refusal, `verify_recording_batch`/`verify_universe_recording_batch`, `_serialize_shard`,
or `recorder_split_for`; any MCP tool or `.tsx`/`lib/types.ts` edit. If the universe-rule predicate
proves insufficient for any fixture scenario the auditor constructs, DROP and escalate rather than
layering a second ad hoc predicate on top — never two implementations of "is this withheld."

## Agents Required

- **backend-data: yes** — all six items above are backend-only: one new predicate + one new
  resolver in an existing module, a choke-point read-through in another existing module, a
  per-shard-loop swap in a third, a progress-shape rewrite across two files, and three test files
  extended/added.
- **frontend-ux: no** — zero `.tsx`/`.ts` files change this iteration. The response SHAPES this
  touches are either unchanged (`sealed_tranche` — same field names, same per-row shape, only
  membership differs) or additive-inside-an-existing-object that no `.tsx` file reads by name
  (confirmed by the decomposer's direct inspection of `apps/frontend/app/desk/page.tsx` and
  `lib/types.ts` — neither references `progress.outcomes` or `sealed_tranche`).

## Frontend Present: yes

Read literally as a plain line for the browser-qa grep. This is the standing mechanical trigger
(iter-5 through iter-9 precedent, restated in nearly every dev handoff since) that keeps
`browser-qa-phase.sh`'s ENTIRE browser lane alive — including the required-still-passing
regression set (J-01–J-05, J-07) and the J-10 kept-product sentinel — none of which this
iteration touches in `.tsx`, but all of which must still be re-verified on-screen via the
store-scoped rig. The standing iter-4/iter-5 lesson is that `Frontend Present: no` silently skips
that whole lane even when a spec names required-still-passing journeys. There is no new or
changed UI surface in this diff — see UI Evolution below.

## Files to Create/Modify

- `apps/backend/app/research/vault.py` — add `universe_ledger_for_dataset_dir(dataset_dir_resolved)`
  (mirrors `shard_ledger_for_dataset_dir` at `vault.py:314-320`, wrapping
  `VaultUniverseLedger(resolve_vault_dir(...))`); add the new shared pool-unresolved predicate,
  combining `withheld_universe_by_dataset_id` (`vault.py:715`, unchanged) with a new check against
  `expected_recording_pairs()` (`vault.py:427`) over `VaultUniverseLedger.all_rows()`. Stays
  store-agnostic (no `DatasetStore` import) per the module's own existing discipline.
- `apps/backend/app/research/micro_snapshots.py` — `withheld_dataset_ids_for_store` (`:99`) and
  `exclude_withheld` (`:118`) switch from `vault.withheld_dataset_ids(vault.
  shard_ledger_for_dataset_dir(...))` to the new predicate, supplying each store record's id,
  symbol, date, and `created_utc`. No change needed in any of its 8 downstream consumers.
- `apps/backend/app/research/micro_readiness.py` — `build_readiness` (`:292`), the per-shard loop
  at/after `:328` (`withheld_universe_by_id = vault.withheld_universe_by_dataset_id(...)`) switches
  to the new predicate; `sealed_tranche` construction (`~:447`) and the `shards` list (`~:461`)
  keep their existing shape; the load-order guard vs. `store.load_events` (`:368`) must hold.
- `apps/backend/app/research/tick_recorder.py` — `TickRecorderComputeManager.snapshot()` (`:663`)
  and `_publish()` (`:702`), plus the idle-default progress shape (`:612`) and the
  outcomes-carrying re-serialization (`:620-621`), stop carrying/exposing raw `outcomes`; add the
  aggregate counters (reuse the counting logic already written for the run-log entry at
  `:638-641`) plus `trades_total`/`quotes_total`/`percent_complete`/`elapsed_seconds`.
- `apps/backend/app/research/micro_routes.py` — `GET /recorder/compute` (`:481-494`) forwards
  `snap["progress"]` verbatim; once `tick_recorder.py`'s own `snapshot()` is aggregate-only this
  route needs no logic change, but confirm no operator-bypass parameter/header ever gets added
  here, and update the route's docstring/route-inventory comment to reflect the new contract.
- `apps/backend/tests/test_vault.py` (existing, 1236 lines) — TR-2 rewritten to the inference-trap
  shape + the pre-fix-would-have-failed counter-test (TC-8/TC-9).
- `apps/backend/tests/test_micro_readiness.py` (existing, 588 lines) — extended for TC-1, TC-3,
  TC-4, TC-10 (mixed ledger-tracked/untracked pool withholding; the `created_utc`-timing guard;
  the load-before-check ordering guard).
- `apps/backend/tests/test_tick_recorder.py` (existing, 843 lines) and/or a new
  `apps/backend/tests/test_micro_routes.py` — extended/added for TC-6 (aggregate-only progress,
  no per-chunk field ever appears, mid-run and terminal) and TC-7 (no bypass parameter/header/role
  exists anywhere on the route).
- `docs/handoffs/goal-rapid-microscope-iter-11-dev.md` — dev handoff (required deliverable),
  naming the two disclosed-ambiguity guardrails above explicitly if either was touched.

No edit needed to `runs/goal-session-rapid-microscope/state/blueprint.md` — the decomposer already
added the iter-11 note documenting `sealed_tranche`'s semantic broadening this turn (confirmed by
direct read). No edit to any `referee_*.py`, `scout_ledger.py` (only its `compute_family_root_id`/
`distinct_variant_count` read verbatim elsewhere, not touched here), `walkforward.py`, or any
`.tsx`/`.ts` file.

## UI Evolution

- New user-facing capability: None. The already-shipped `/desk` Microscope Readiness section
  (J-01) keeps rendering exactly as before against the real store (zero registered vault
  universes today).
- New information displayed: None to a user. New fields are backend-only aggregate sub-fields of
  the already-registered recorder-progress row (`progress.chunks_fetched/reused/unchanged/failed`,
  `progress.trades_total/quotes_total`, `progress.percent_complete`, `progress.elapsed_seconds`) —
  inert today since nothing polls the recorder-compute route in production (no recording has ever
  been triggered against the operator's real store).
- New user actions: None.
- UI surface changes: None.
- Navigation changes: none.

## Visual Requirements

- Component patterns: N/A — no new/changed UI surface this iteration.
- Layout: N/A — existing `/desk` layout unchanged.
- Key visual effects: N/A.
- States to handle: regression-only. The existing Microscope Readiness table's populated/empty
  states must render byte-identically to before this diff, since the real store has zero
  registered vault universes (nothing newly withheld to display differently).

## Key Test Scenarios

Full TC-1…TC-13 detail lives in the phase spec — read it directly rather than re-deriving from
this summary.

- **Predicate mechanics (TC-1..TC-4, `test_vault.py`/`test_micro_readiness.py`)**: a
  registered-but-unresolved pool's members (mixed ledger-tracked/untracked) produce zero per-shard
  rows on either side and a correct aggregate `shard_count`; `exclude_withheld`'s
  `withheld_excluded` count reflects the SAME broadened membership (proving the one-choke-point
  claim); assigning/exposing one pool member reveals exactly that one row, leaving the rest
  aggregate-only; a dataset recorded BEFORE a universe's registration sharing its (symbol, date)
  is never retroactively withheld.
- **Real-store inertness (TC-5)**: the new predicate's output against the real `.data` store is
  byte-identical (empty) to today's `withheld_dataset_ids()`; a hash of the real store taken
  before/after this iteration's work is identical.
- **Recorder progress (TC-6/TC-7, `test_tick_recorder.py`/`test_micro_routes.py`)**: polled
  mid-run and at terminal state, the response body never contains a planned chunk's `symbol`,
  `date`, or `dataset_id` anywhere in the JSON — only the aggregate fields; no query parameter,
  header, or role claim on the route ever returns per-chunk identity.
- **TR-2 rewrite (TC-8/TC-9, `test_vault.py`)**: the widened inference-trap sweep (operator
  compute acts run first, then every route + recorder-progress + `datasets` MCP tool collected)
  leaves ≥2 candidate identities for every still-unexposed member; the counter-test proves the
  pre-fix subtraction attack WOULD have isolated a unique identity before this fix.
- **Load-order guard (TC-10)**: `store.load_events` is never called for a withheld shard during
  `build_readiness`'s `fallback_frac` walk — proven directly, never inferred.
- **Regression + frozen foundations (TC-11)**: full suite ≥ 3,177 pass / 8 skip, 0 failures;
  `config_fingerprint()` → `08e471b10130e1e2`; all six `referee_*.py` SHA-256 hashes byte-identical
  to the iteration-0 baseline; `EXPECTED_TOOLS` still the unchanged 22-tuple.
- **Browser (TC-12, store-scoped rig `:8301`/`:3301`)**: J-01–J-05 + J-07 replay green (J-01–J-05
  via stored golden scripts, J-07 via the LLM fallback lane per `state/golden-gaps`); J-06 evidence
  = a fresh element capture of the shipped `/desk` Microscope Readiness shards table proving it is
  byte-identical against the real (zero-universe) store; J-10 evidence = `J-10.json`'s full
  kept-product sentinel walk.
- **Independent auditor (TC-13)**: full-depth lane MUST run against this diff — the entire reason
  this iteration is scoped this small. Findings fixed in-iteration or explicitly carried forward
  by name in the dev handoff, never silently dropped. This class of work (ledger/withhold-predicate
  correctness) is exactly where prior full audits have caught real integrity faults — weight the
  single-choke-point claim (item 2 above) and the load-order guard (TC-10) first, since those are
  the two places a second, divergent implementation would silently reopen the leak.

## Error Cases (from the spec, do not skip)

A dataset matching a registered universe's expected pairs but recorded BEFORE that universe
existed is never withheld (never silently over-hidden — TC-4). A still-running recorder job polled
mid-flight never leaks a chunk's symbol/date/id even transiently (TC-6). A corrupted or missing
vault ledger at withhold-check time fails the SAME way `withheld_dataset_ids()` already does today
— no behavior change to that path this iteration; the still-open corrupted-ledger owner question
from iter-10 is not resolved here.
