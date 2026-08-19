# Goal Iteration 11 — The opaque research pool (r5), alone

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 11
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory, no exceptions). Iterations 3 and 8
  both asked for full and were demoted to lean by the deterministic budget arbiter, dropping the
  independent auditor lane both times; this iteration is scoped deliberately smaller than iter-9's
  vault build (three existing modules extended plus one test file, zero new modules) specifically
  to protect the auditor's ability to finish inside budget on the third attempt.
- Frontend Present: yes
- **Target journeys:** J-06, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed` shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure; the refusal is typed, tested, and fail-closed. *(critical)*
  - **Sealed exposure is family-level and single-shot — never a second draw.** No more than one evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels in every later export bundle; no perturbed re-submission resets it. *(critical)*
  - **A recorded tranche is one opaque research pool until its shards are exposed.** No served surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward, graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory" versus "sealed", nor a complete per-shard list of EITHER side while any pool member is unexposed; the registered universe is public by construction, so a complete list of one side identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable; identity becomes public only at real exposure or assignment. The governing test is the TR-2 inference trap: given the registered universe plus every public artifact, no still-unexposed vault-eligible shard is identifiable with certainty. *(critical — spec r5)*
  - **The 12 pre-existing tick symbol-days are permanently exploratory** — never sealed, never `historical_oos`, never relabeled. *(critical)*
  - **The vault secret never enters the repo, a log, a payload, or a screenshot** — only its sha256 commitment is ever recorded. *(critical)*

## GOAL

Close the r5 "opaque research pool" hole for real: neither the corpus-readiness page nor the
recorder's live progress view may show a name, a date, or an id for any pool member while it is
unexposed — on EITHER the exploratory or the sealed side — proven by a TR-2 rewritten into a
genuine deterministic inference trap, not merely re-labeled.

## BACKGROUND

The iter-10 evaluator ESCALATEd and named this exact work as the next round, scoped to one step,
under the full pipeline with the independent auditor: "the corpus page must stop listing
recordings one by one on EITHER side while any member of a batch is still unopened; the recording
progress view must show only totals, never a name, a date or an id; and the trap that guards this
must be rewritten so that it actively tries to work out which recordings are hidden and fails to."
Per the carried r5 owner ruling (`docs/rapid-validation-spec.md` header + §7.1 + §7.5 points 4/7/8
+ §9 TR-2 + §10 point 7, `docs/goal.md`'s matching J-06 step 3/5 and new critical anti-goal rail,
all dated 2026-08-18), this is settled design, not an open question — the only job left is to
build it. Depth is **full**, trigger 3 (mandatory: prior verdict ESCALATE) — no discretion here.

**What "settled design, not yet built" turned out to mean on inspection.** Reading the current
code before planning (not assuming from the prior eval's prose) surfaced two concrete gaps, both
now scoped into this iteration:

1. `GET /research/desk/micro/recorder/compute` serves `snapshot["progress"]["outcomes"]` — a raw
   list of per-chunk dicts carrying `symbol`, `date`, `start`, `end`, `dataset_id` — verbatim
   (`tick_recorder.py` `TickRecorderComputeManager.snapshot`/`_publish`; the route at
   `micro_routes.py:481-494` forwards `snap["progress"]` unchanged). This is a direct §7.1
   violation, not a hypothetical one. The run-log surface (`GET .../recorder/runs`, backed by
   `_run_log_entry`) is already aggregate-only and needs no change — only the LIVE progress path
   leaks.
2. `micro_readiness.build_readiness`'s per-shard withhold check (`vault.withheld_universe_by_dataset_id`)
   only flags a dataset that already carries an explicit vault shard-ledger row. A repo-wide grep
   confirms `seal_shard`/`assign_shard`/`expose_shard` have **zero production call sites** in
   `app/` — every hit is a docstring, an `__all__` entry, or the definition itself. So the actual
   hole r5 must close is not "opacity serving is wrong for tracked shards" (r3/r4 already handle
   that case) but "most future pool members would never be ledger-tracked at all," because
   nothing today wires the recorder to the vault. The instant a real recording under a registered
   universe finalizes a dataset, it becomes fully identifiable in `GET /research/datasets` and in
   readiness's `shards` list — the exact leak r5 exists to close — with zero code path standing in
   the way.

**The fix closes gap 2 structurally, not procedurally** (an interpretation call, logged in
`runs/goal-session-rapid-microscope/state/assumptions.md`'s iter-11 entry — read it before
building): the withhold predicate becomes UNIVERSE-RULE-driven rather than ledger-row-driven. A
dataset is withheld if it already fails today's ledger check (unchanged), OR if its (symbol,
date) matches a registered universe's `expected_recording_pairs()` (already exists,
`vault.py:427`) and its own `created_utc` is at or after that universe's `registered_at`. Because
this reads the REGISTERED RULE rather than which bookkeeping call happened to fire, it is
safe-by-construction the moment `register_universe` runs — a real recording stays opaque even
with zero additional recorder-to-vault wiring at finalize time. That wiring — and the still-undefined
mechanism by which an exploratory-track pool member (one that will never be HMAC-sealed) is ever
deliberately released to full visibility — is deliberately **not** built this iteration; §7.4 fully
specifies the family-bound `assigned → exposed` path, but no section of the spec names a trigger
for "exposed for exploratory use." Per T-1 ("ambiguous or unimplementable ⇒ DROP the procedure,
surface for owner ruling, never improvise"), that gap is left open rather than invented — see
NOTES. The `created_utc >= registered_at` guard exists specifically so a universe registered
LATER can never retroactively withhold one of the 12 permanently-exploratory legacy symbol-days
that happens to share a (symbol, date) with its rule.

**Two applicable lessons, both directly on point.** iter-9's lesson: "any surface publishing an
EXPECTED set beside a surface publishing the ACTUAL set is a subtraction oracle, and no amount of
field-level opacity in the new module can close it" — the exact mechanism this iteration closes
structurally rather than patching per-surface. iter-10(second)'s lesson: "prefer 'publish what the
exposure ledger already released' over 'list everything, then subtract the withheld'" — this
iteration's design generalizes that principle from "driven by what got explicitly released" to
"driven by what the registered rule says might still be pooled," which is the stronger, fail-safe
direction (over-withholding, never under-withholding).

**Zero-cost against the real store, matching r3/r4/r5's own pattern.** The real `.data` store has
zero registered vault universes today, so every change below is provably inert against it — same
"applied while zero shards are sealed, so nothing re-keys" shape every prior vault revision used.

## IN SCOPE

### Backend

- [ ] `vault.py`: a new function giving the SINGLE shared "is this dataset part of an unresolved
      registered-universe pool" predicate, combining (a) today's ledger-row check
      (`withheld_universe_by_dataset_id`, unchanged) with (b) a new universe-rule membership check
      per BACKGROUND above (`expected_recording_pairs()` × `created_utc >= registered_at`,
      resolved against `VaultUniverseLedger`'s own rows — add a `universe_ledger_for_dataset_dir`
      resolver mirroring the existing `shard_ledger_for_dataset_dir` pattern). `vault.py` stays
      store-agnostic (no `DatasetStore` import) — the function takes the caller's own
      `(dataset_id, symbol, session_date, created_utc)` tuples, not a store.
- [ ] `micro_snapshots.withheld_dataset_ids_for_store`/`exclude_withheld` reads the new predicate
      instead of the narrower ledger-only one. Every one of its 8 existing consumers
      (`scout.py`, `walkforward.py`, `micro_join.py` ×2, `edge_report.py`, `edge_report_cache.py`
      ×2, `pnl_scan.py`, `desk_screen.py`, `setups.py`) inherits the fix through this one choke
      point with **zero call-site changes** — do not touch any of those 9 files.
- [ ] `micro_readiness.build_readiness`'s per-shard loop (currently calls
      `vault.withheld_universe_by_dataset_id` directly, not through `exclude_withheld`) is
      updated to the same new predicate, so neither side is listed per-shard while any pool
      member of a registered universe is unresolved. `sealed_tranche`'s existing field name and
      shape (`shard_count`/`symbol_days`/`by_universe`) are UNCHANGED — only which datasets
      populate it broadens (see `blueprint.md`'s iter-11 note). The withhold check must run
      BEFORE `store.load_events` in the loop, exactly as today's ordering already does, so a
      newly-withheld pool member's events are never read (protects the "no exploratory read of a
      sealed shard" rail for this broader class too).
- [ ] `tick_recorder.py` (`TickRecorderComputeManager`) + `micro_routes.py`
      (`GET /research/desk/micro/recorder/compute`): the live `progress` body stops serving raw
      `outcomes`; it serves the aggregate-only shape named in spec §7.1 instead —
      `chunks_total`/`chunks_done` (already present), new `chunks_fetched`/`chunks_reused`/
      `chunks_unchanged`/`chunks_failed` (per-outcome-type counts, mirroring the already-compliant
      `_run_log_entry` shape), new `trades_total`/`quotes_total` (accumulated from each fetched
      chunk's `HistoricalWindow` at fetch time, never persisted per-chunk), `percent_complete`,
      and `elapsed_seconds`. No `symbol`, `date`, `dataset_id`, or any other per-chunk field
      anywhere in the response, at any point during a run. Add **no** operator-only bypass
      parameter, query flag, or header anywhere on this route — r5 explicitly forbids one.
      `GET .../recorder/runs` (`_run_log_entry`) is already compliant; do not change it.
- [ ] `test_vault.py`'s TR-2 suite is rewritten/widened into spec §9's deterministic
      inference-trap shape: register a fixture universe with a symbol/date rule the test knows
      completely; populate a fixture store with members some carrying explicit ledger rows
      (`sealed`/`assigned`/`exposed`) and some carrying none; expose a proper subset via the
      EXISTING family-bound `assign_shard`/`expose_shard` path; run the operator compute acts
      first (a fixture-scale snapshot build, Scout run, edge report, and PnL sweep, per spec §9's
      "cannot pass merely because the rig computed nothing"); then sweep every registered route,
      the recorder-progress path, and the `datasets` MCP tool, asserting that for every
      still-unexposed member at least 2 candidate identities remain consistent with everything
      served, and that no complete identity-labelled exploratory/sealed partition is derivable.
      Add a counter-test performing the PRE-fix subtraction attack (list `GET /research/datasets`'s
      served ids, compute the universe's full expected set, subtract) against the same fixture and
      assert it no longer isolates a unique unexposed identity — proving the assertion above is
      not vacuous.
- [ ] Extend `test_micro_readiness.py` and `test_tick_recorder.py` (or a new
      `test_micro_routes.py` case) for the new withhold/aggregate behavior described above. Full
      backend suite re-run after every edit.

### Frontend

None. The readiness, vault, and recorder-progress response SHAPES this iteration touches are
either unchanged (`sealed_tranche`, `shards` — same field names, same per-row shape, only
membership differs) or additive-inside-an-existing-object (`progress`'s new aggregate sub-fields
replace an object no `.tsx` file reads by name — the shipped `/desk` Microscope Readiness section
renders `readiness.shards`/`readiness.totals`, confirmed by direct inspection of
`apps/frontend/app/desk/page.tsx`, `lib/types.ts` — neither references `progress.outcomes` or
`sealed_tranche`). Zero `.tsx`/`.ts` files change. `Frontend Present: yes` above is declared solely
to keep the browser-qa regression lane running for J-01–J-05, J-07, and the J-10 sentinel (the
standing iter-4/iter-5 lesson: `Frontend Present: no` silently skips that whole lane even when a
spec names required-still-passing journeys).

### New user-facing capability

None this iteration. The already-shipped `/desk` Microscope Readiness section (J-01) keeps
rendering exactly as before against the real store, which has zero registered vault universes.

### New information displayed

None new to a user — see New user-facing capability above. New BACKEND-only aggregate fields are
listed under Data-contract additions below (sub-fields of the already-registered recorder-progress
row; inert today, nothing polls the recorder-compute route in production because no recording has
ever been triggered against the operator's real store).

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible to the operator. The real store's already-shipped `/desk` panels render
byte-identically before and after this iteration (zero registered universes today); the change is
entirely inside the research backend's withhold predicate, the recorder's live-progress shape,
and the trap suite that proves both.

### Blueprint conformance

No new page, no nav change. `micro_readiness.py`'s "Corpus readiness truth" row and
`tick_recorder.py`'s "Recorder job + tranche progress/runs" row are both ALREADY registered in
`blueprint.md`'s Data Contract (era baseline) — this iteration builds inside those already-reserved
owners. `blueprint.md` was edited this turn (additive only, no reapproval file needed): a new
"Recorder-progress aggregate sub-fields" table registers the new `progress.*` field names under
the already-registered recorder-progress row, and an iter-11 note documents `sealed_tranche`'s
semantic broadening (name and shape unchanged).

### Data-contract additions

New sub-fields of the ALREADY-registered "Recorder job + tranche progress/runs" row (owner
`tick_recorder.py`, served by `GET /research/desk/micro/recorder/compute`, no new endpoint):
`progress.chunks_fetched: int >= 0`, `progress.chunks_reused: int >= 0`,
`progress.chunks_unchanged: int >= 0`, `progress.chunks_failed: int >= 0`,
`progress.trades_total: int >= 0`, `progress.quotes_total: int >= 0`,
`progress.percent_complete: float, 0.0-100.0`, `progress.elapsed_seconds: float >= 0` — all
registered in `blueprint.md` this turn. No other new displayed value. `sealed_tranche` is NOT a
new value (already registered iter-10) — only its populated membership broadens; see `blueprint.md`'s
iter-11 note. Never introduce a second predicate for "is this dataset withheld" anywhere — the one
new `vault.py` function is the sole computing module for that question, consumed via
`micro_snapshots.exclude_withheld()`/`withheld_dataset_ids_for_store()` and directly by
`micro_readiness.build_readiness()`.

## OUT OF SCOPE

- **J-06 step 4** (the credentialed Alpaca starter tranche — an operator-attended act). Stays
  human-blocked: two of the three owner questions carried from iter-10 are still open (who
  decides a sealed shard's pass/fail verdict; whether a corrupted vault ledger fails closed or
  open) and this iteration does not depend on either being answered. No real vendor call, no
  write to the operator's real `.data/datasets` store.
- **The "exposed for exploratory use" release mechanism** — how/when a non-sealed pool member's
  real identity is ever deliberately published. Not specified anywhere in
  `docs/rapid-validation-spec.md` §7.1-§7.7 (unlike the family-bound `assigned → exposed` path,
  which §7.4 fully specifies); deliberately not invented here per T-1. This iteration's fix is
  safe WITHOUT it (a registered-but-unresolved pool member simply stays withheld indefinitely,
  which is conservative, never leaky) — but it is a genuine, open design gap that whichever
  iteration next scopes J-06 step 4 in detail must resolve before real exploratory-track tape is
  ever usable. Flagged here by name so it is not silently forgotten (see NOTES).
- **Wiring `tick_recorder._finalize_day`/`run_tick_recording` to call any `vault.py` function at
  record time.** Not needed for this iteration's safety property (the universe-rule-driven
  predicate closes the hole without it — see BACKGROUND) and not built. A future iteration MAY
  add it for auditability/UX reasons once the exploratory-release mechanism above is designed, but
  nothing here requires it.
- **TR-3** (accessor fence), **TR-17** (future-event availability), **TR-22** (exposure registry)
  — still-missing traps living in `micro_accessor.py`/`micro_observer.py`/`walkforward.py`
  (J-02/J-03/J-05 territory), not this iteration's files. Deferred again, exactly as iter-10 also
  deferred them, to a dedicated hardening round.
- **J-10 step 2's deterministic-rerun check** (byte-identical snapshot/screen/fold outputs on a
  re-run over unchanged stores) — never run this era; deferred alongside the traps above rather
  than bundled into an already-full-sized iteration.
- The two remaining owner questions carried from iter-10 (sealed-shard pass/fail authority; a
  corrupted vault ledger's fail-open-vs-closed behavior) and the one-quote-early depletion timing
  stamp (owner-owed since iteration 2) — human-owned, not this iteration's job to resolve.
- **J-08** (surface + MCP v6 bump, `/desk` UI sections) and **J-09** (pilot studies) — natural next
  journeys after J-06 progresses further, not this iteration.
- Any change to `referee_*` modules, the `v1` strategy, or the `default` profile — byte-identical,
  forbidden.
- Any change to `scout_ledger.compute_family_root_id`, `assign_shard`'s single-shot refusal logic,
  `verify_recording_batch`/`verify_universe_recording_batch` (TR-4), `_serialize_shard`'s existing
  per-stage reveal whitelist, or `recorder_split_for` — all reused verbatim, none modified. The
  vault and shard-ledger ROW SHAPES do not change (only a new, additive function reading them).
- A `desk_micro_readiness`/`desk_scout`/`desk_walkforward`/`desk_vault` MCP tool — J-08's four-tool
  delta, not this iteration's. MCP surface stays at 22 tools.
- Any `/desk` UI section, nav change, or `.tsx`/`lib/types.ts` edit — see Frontend above.

## DEFINITION OF DONE

- [ ] Readiness serves no per-shard row, on EITHER side, for any dataset that is part of a
      registered-but-unresolved vault universe's pool — proven on a fixture carrying BOTH
      ledger-tracked and non-ledger-tracked pool members.
- [ ] The new predicate is the single shared choke point consumed by `micro_snapshots.exclude_withheld`
      (hence its 8 existing corpus-wide enumerator consumers) and `micro_readiness.build_readiness`
      directly — no second implementation anywhere (coherence-auditor confirms).
- [ ] A dataset recorded before a universe's registration is never retroactively withheld by that
      universe's later rule, even if it shares a (symbol, date) with it.
- [ ] `GET /research/desk/micro/recorder/compute` serves aggregate-only progress at every point
      during a run — no symbol, date, dataset id, or other per-chunk field ever appears in the
      body — and no operator-bypass parameter exists anywhere on the route.
- [ ] TR-2 is rewritten into the deterministic inference-trap shape of spec §9 and is
      counter-tested to prove it would have FAILED against this iteration's pre-fix code.
- [ ] The "no exploratory read of a sealed shard" rail holds for the newly-withheld class too: the
      withhold check runs before any event load, proven directly (never inferred).
- [ ] Zero behavior change against the real `.data` store (byte-for-byte hash identical before and
      after this iteration's dev/test work; it has zero registered vault universes).
- [ ] Target journeys J-06 (advanced — status is the evaluator's call, not asserted here) and J-10
      (TR-2 strengthened; trap count unchanged at 19/22 since TR-2 was already counted) verified
      via browser-qa-agent and the backend test suite together.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-07 remain green (deterministic
      replay for the six with goldens on file; J-07 falls to the LLM lane per the recorded
      `golden-gaps` entry — expected, not a defect).
- [ ] No anti-goal violation introduced: the r5 opaque-pool rail holds under adversarial testing;
      the vault secret never appears in a log/payload/screenshot; the 12 legacy symbol-days are
      never withheld by the new predicate; all six `referee_*.py` modules stay byte-identical; the
      MCP surface stays at 22 tools; no `Config` field is added; `EXPECTED_TOOLS` unchanged.
- [ ] Full backend suite passes at a count ≥ 3,177 pass / 8 skip (iter-10's evaluator-verified
      count) and ≥ the era-open baseline, 0 regressions; `Config().config_fingerprint()` prints
      `08e471b10130e1e2` unchanged.
- [ ] The independent auditor (full-depth lane) runs against this diff; its findings are fixed
      within this iteration or explicitly carried forward by name in the dev handoff.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-11-dev.md`.

## TESTING REQUIREMENTS

- Browser: no NEW user-facing surface this iteration. Required-still-passing regression sweep:
  J-01, J-02, J-03, J-04, J-05, J-07 (J-01–J-05 via stored golden replay scripts
  `runs/goal-session-rapid-microscope/journey-scripts/J-01.json` through `J-05.json`; J-07 via the
  LLM fallback lane, no golden on file — recorded in `state/golden-gaps`). Target-journey evidence:
  J-06 via `J-06.json`'s golden plus a fresh element capture of the shipped `/desk` Microscope
  Readiness shards table proving it is byte-identical against the real store (zero universes
  registered); J-10 via `J-10.json`'s sentinel walk.
- Unit/integration: `test_vault.py` (TR-2 rewritten to the inference-trap shape, plus the
  pre-fix-would-have-failed counter-test), `test_micro_readiness.py` (extended — the broadened
  withhold predicate, the `created_utc`-timing guard, the load-order guard), `test_tick_recorder.py`
  and/or `test_micro_routes.py` (extended — the aggregate-only progress shape, the no-bypass
  guard). Full backend suite re-run after every edit.
- Error cases: a dataset matching a registered universe's expected pairs but recorded BEFORE that
  universe existed is never withheld (never silently over-hidden); a still-running recorder job
  polled mid-flight never leaks a chunk's symbol/date/id even transiently; a corrupted or missing
  vault ledger at withhold-check time fails the SAME way `withheld_dataset_ids()` already does
  today (no behavior change to that path this iteration — the still-open corrupted-ledger question
  from iter-10 is not resolved here).

Test-first contract — TC- scenarios:

- TC-1: given a registered fixture vault universe U (`symbol_rule=[SYM-A, SYM-B]`,
  `date_rule=[D1, D2]`, 4 expected pairs) and a fixture `DatasetStore` holding all 4 corresponding
  datasets recorded AFTER U's `registered_at`, with 2 of the 4 given an explicit vault
  shard-ledger row in state `sealed` and the other 2 given NO shard-ledger row at all, when
  `micro_readiness.build_readiness` is called, then none of the 4 datasets appears in the returned
  `shards` list, and `sealed_tranche` reports `shard_count: 4` for universe U.
- TC-2: given the same fixture, when `micro_snapshots.exclude_withheld` is called against the same
  store, then all 4 dataset ids are excluded from the kept list and the disclosed
  `withheld_excluded` count equals 4 (not 2), proving every existing corpus-wide enumerator
  inherits the fix through the one shared choke point with no per-caller change.
- TC-3: given the same fixture universe U, when one of its expected pairs is assigned to a family
  and exposed via the existing `assign_shard`/`expose_shard` path, and `build_readiness` is called
  again, then that one dataset's row appears in `shards` with full identity, and the remaining 3
  unresolved pairs still contribute zero per-shard rows and only the aggregate count, now
  `shard_count: 3`.
- TC-4: given a dataset recorded with `created_utc` BEFORE a universe U2's `registered_at`, whose
  (symbol, date) happens to also be one of U2's expected pairs, when the new predicate evaluates
  it, then it is NOT withheld — proving a pre-existing (e.g. permanently-exploratory legacy)
  dataset is never retroactively hidden by a later universe registration naming the same
  symbol-day.
- TC-5: given the real, current `.data` store with zero registered vault universes, when the new
  predicate runs against it, then its output is byte-identical (empty) to today's
  `withheld_dataset_ids()` output, and a hash of the real store taken before and after this
  iteration's dev/test work is identical.
- TC-6: given a tick-recorder compute job planned over 3 chunks spanning 2 symbol-days, when
  `GET /research/desk/micro/recorder/compute` is polled mid-run and again after it reaches a
  terminal state, then neither response body contains any planned chunk's `symbol` or `date`
  string value, nor any `dataset_id`, anywhere in the JSON — only `chunks_total`, `chunks_done`,
  the four per-outcome-type counts, `trades_total`, `quotes_total`, `percent_complete`, and
  `elapsed_seconds`.
- TC-7: given the recorder-progress route's request handling, when it is inspected for any query
  parameter, header, or role claim that would return per-chunk identity, then none exists.
- TC-8: given a fixture pool recorded under a registered universe whose symbol/date rule the test
  fixture knows completely, with a proper subset of members exposed via the existing family-bound
  path and the rest left unresolved (some with ledger rows, some without), when the widened TR-2
  sweep runs the operator compute acts first (a fixture-scale snapshot build, Scout run, edge
  report, and PnL sweep) and then collects every value any registered route, the recorder-progress
  path, and the `datasets` MCP tool serve, then for every still-unexposed member at least 2
  candidate identities remain consistent with everything served, and no complete
  identity-labelled exploratory/sealed partition is derivable.
- TC-9: given that same fixture, when the pre-fix subtraction attack is attempted (list every id
  `GET /research/datasets` serves, compute universe U's full expected set, subtract), then the
  result no longer isolates any unique unexposed identity — a counter-test proving TR-2 would have
  FAILED before this iteration's fix.
- TC-10: given a freshly recorded fixture shard whose event data is part of an unresolved pool,
  when `build_readiness`'s `fallback_frac` computation runs, then `store.load_events` is never
  called for that shard's dataset id — the withhold check short-circuits before any event read.
- TC-11: given the full backend test suite and the six `referee_*.py` SHA-256 hashes recorded at
  iteration 0, when they are re-run/re-hashed after this iteration's diff, then all six hashes are
  byte-identical, `Config().config_fingerprint()` still prints `08e471b10130e1e2`,
  `test_mcp_server.py`'s `EXPECTED_TOOLS` is still the unchanged 22-tuple, and the suite passes at
  a count ≥ 3,177 pass / 8 skip with 0 failures.
- TC-12: given required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-07 and target
  journeys J-06, J-10, when the browser-qa lane runs, then each replays deterministically green
  via its stored golden script (J-07 via the LLM fallback lane), with a screenshot/element-capture
  of the shipped `/desk` Microscope Readiness shards table shown unchanged against the real store,
  and the J-10 sentinel's full kept-product walk on record.
- TC-13: given this iteration's diff, when the independent auditor (full-depth lane) reviews it,
  then its findings are either fixed within this same iteration or explicitly carried forward by
  name in the dev handoff — never silently dropped.

## NOTES

- **The exploratory-track exposure mechanism is a genuine open design gap, not an oversight.**
  Recorded in `runs/goal-session-rapid-microscope/state/assumptions.md`'s iter-11 entry: no
  section of `docs/rapid-validation-spec.md` names how or when a non-sealed pool member's real
  identity is ever deliberately published (unlike the fully-specified family-bound
  `assigned → exposed` path). This iteration's fix is safe without it — an unresolved pool member
  simply stays withheld indefinitely — but whichever iteration next scopes J-06 step 4 in detail
  needs to design it (and very possibly ask the owner, given the one-way, immutable stakes once
  real tape flows). Do not let it get lost.
- **Scope-protection is deliberate, mirroring iter-9's own note.** This spec touches three
  existing modules (`vault.py`, `micro_readiness.py`, `tick_recorder.py`) plus their route file
  and test files — zero new modules, zero new routes, zero new MCP tools, zero frontend files.
  Two prior full-depth attempts (iterations 3 and 8) were demoted to lean by the budget arbiter
  before the auditor ever ran; keep this iteration from growing to absorb TR-3/17/22, the
  deterministic-rerun check, or the exploratory-release mechanism above — all explicitly deferred.
- **Process note (standing, from the operator):** never use pattern-based process kills
  (`pkill -f` / `killall`) for uvicorn, next, node, chrome, or python — other projects share this
  host. Kill only exact PIDs you started and recorded.
- The vault secret (`TAPEOLOGY_VAULT_SECRET_FILE` at `~/.config/tapeology/vault-secret`) is not
  touched this iteration (no sealing act occurs against the real store), but the standing rule
  stands regardless: never read, log, print, or serve it — only its sha256 commitment may ever be
  recorded.
- Spec revisions r2 through r5 (`docs/rapid-validation-spec.md`) are SETTLED owner rulings — do
  not re-litigate; build against the current spec text as read this iteration.
- One assumption-ledger entry was logged for this iteration's central design call (the
  universe-rule-driven predicate, and the deliberate non-invention of the exploratory-release
  mechanism) — see `runs/goal-session-rapid-microscope/state/assumptions.md`'s iter-11 entry.
- Escalation flag: if the developer finds the universe-rule-driven predicate insufficient for any
  reason discovered during implementation (e.g. a fixture scenario the auditor constructs that it
  does not actually cover), DROP and escalate rather than layering a second, ad hoc predicate on
  top — per this era's own T-1 discipline and the standing "single source of truth" rail on the
  withhold question specifically.
