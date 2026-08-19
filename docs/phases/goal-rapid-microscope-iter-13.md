# Goal Iteration 13 — Close the vault recovery hole that can hide a destroyed shard as never-sealed

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 13
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — iteration 12's own verdict line was ESCALATE (not merely a prose
  recommendation), which per this session's iter-8 and iter-12 lessons is the sole mechanically
  binding grant of full depth; the arbiter cannot demote it.
- Frontend Present: yes
- **Target journeys:** J-06, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07
- **Anti-goal reminders:**
  - **No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed`
    shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded
    exposure; the refusal is typed, tested, and fail-closed. *(critical)*
  - **Sealed exposure is family-level and single-shot — never a second draw.** No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and
    travels in every later export bundle; no perturbed re-submission resets it. *(critical)*
  - **A recorded tranche is one opaque research pool until its shards are exposed.** No served
    surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
    graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory"
    versus "sealed", nor a complete per-shard list of EITHER side while any pool member is
    unexposed; the registered universe is public by construction, so a complete list of one side
    identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable;
    identity becomes public only at real exposure or assignment. The governing test is the TR-2
    inference trap: given the registered universe plus every public artifact, no still-unexposed
    vault-eligible shard is identifiable with certainty. *(critical — spec r5)*
  - **The vault secret never enters the repo, a log, a payload, or a screenshot** — only its
    sha256 commitment is ever recorded. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*

## GOAL

Make the vault's lawful-recovery promise actually true: a shard whose only ledger row was
destroyed can no longer silently reappear as an ordinary, never-sealed dataset — closing the one
open integrity hole standing between today's vault code and any real sealed tape.

## BACKGROUND

Iteration 12's own verdict line was `ESCALATE` — not merely a prose recommendation, which is
exactly the distinction iter-8's and iter-12's own lessons say the engine's arbiter honors — so
this is a genuine, unconditional Full trigger 3. Iteration 12 built and independently attacked
TR-25/TR-27/TR-28, but its own auditor pass then found a residual hole in TR-25's own recovery
primitive: `vault.recover_shard_ledger`'s "not proven complete" branch marks `exposure_unknown`
only for dataset ids visible in the surviving verified prefix. A shard whose ONLY row lived in the
destroyed suffix — reproduced end to end: seal `ds-1`/`ds-2`/`ds-3`, destroy `ds-3`'s row, attempt
recovery with nothing to reconstruct it — leaves the withheld set entirely and reads as an
ordinary never-sealed dataset, while `rewrite_from_recovery` still re-heals the tail anchor, so
`verify_chain()` reports clean afterward. This contradicts spec §7.8's own invariant verbatim
("unknown exposure history may NEVER be interpreted as 'never exposed'") and is this iteration's
sole must-close item — scored minor only because zero universes are registered, zero shards are
sealed, and the function has zero production call sites, but it must close before J-06 step 4.

This iteration is deliberately much narrower than iteration 12's: one fix plus two
documentation-only MINOR resolutions, nothing else. That respects "never bundle two risky
journeys" (J-08 stays iteration 14's turn, matching the iteration-11 and iteration-12 evaluators'
own sequencing) and directly answers the carried instruction to keep this round small enough that
the budget trimmer has no grounds to cut it a third time. Target selection follows the priority
rubric's unblocker rule (J-06's step 4 is blocked on exactly this fix) and smallest-spec-wins-ties
(one module, one bug family); J-10 is also a target because TR-25's own soundness is its step-1
acceptance item, even though fixing it does not move the era's 23-of-28 trap count — it corrects
the soundness of an already-counted entry rather than adding a new one.

Applying the session's own pairing lesson twice over. First, inside the fix itself:
`recover_shard_ledger`'s "halt when a row cannot be named at all" correction ships together with
its "mark the full named union, not just the surviving prefix" sibling in the same diff — fixing
the reported case while leaving the union-coverage gap narrow would repeat iteration 11's mistake
verbatim. Second, on the reviewer's separate open question (`vault.py:880`: `seal_shard`/
`assign_shard`/`expose_shard` gate `verify_chain()` on their own shard ledger only, not "both
ledgers" as the iteration-12 spec's IN SCOPE text literally said): this iteration resolves it by
DEFERRING the gate-widening and its not-yet-built universe-ledger recovery primitive TOGETHER,
rather than shipping a widened gate with no way to recover from what it would newly refuse — see
NOTES and the `state/assumptions.md` iter-13 entries for the full reasoning, including why making
it mandatory would force touching roughly 81 existing test call sites across ten unrelated files
for zero production-reachable benefit (zero call sites exist in `app/` for any of the three
functions today). The `micro_routes.py:491` stale docstring is folded in as the second cheap,
documentation-only MINOR. Anchors verified on the current tree (2026-08-19), re-locate by symbol
name: `vault.py` `recover_shard_ledger` :1447, its "not proven complete" branch :1481-1558,
`seal_shard`/`assign_shard`/`expose_shard` :880/941/971; `micro_routes.py`
`get_tick_recorder_compute` :481-505; TR-25's existing tests in `tests/test_vault.py` :1619-1786.

## IN SCOPE

### Backend

- [ ] `vault.py` `recover_shard_ledger`: when a reconstruction attempt cannot prove completeness
  AND at least one row the ledger's own durable tail anchor attests existed is not even NAMED by a
  dataset_id anywhere in the verified prefix plus the caller's `reconstructed_suffix` (a genuine
  row-count shortfall against the anchor's `row_count`, OR the anchor itself is missing/unreadable
  — both mean the true row count cannot be bounded), refuse to resume at all: do not call
  `rewrite_from_recovery`; the corrupted file on disk stays untouched, `verify_chain()` keeps
  reporting `ok: False` immediately afterward, and every dependent predicate keeps raising
  `VaultLedgerCorruptionError`. Still append an immutable incident row to `recovery_ledger`
  recording the attempt and the shortfall (spec §7.8's "or the whole tranche halts" disjunct —
  closes the iteration-12-found hole where an entirely-unnamed shard silently left the withheld
  set).
- [ ] `vault.py` `recover_shard_ledger`: when every anchor-attested row IS named (row counts match)
  but the hash-attested completeness check still fails (interior content mismatch, not a count
  shortfall), mark `exposure_unknown` for the UNION of dataset_ids appearing in BOTH the verified
  prefix and the caller's `reconstructed_suffix` — not the prefix alone as today — before resuming.
- [ ] `vault.py`: add a short docstring clarification to `seal_shard`/`assign_shard`/`expose_shard`
  stating that their corruption gating is deliberately scoped to their own shard ledger only
  (reasoning: zero production call sites, no read dependency on the universe ledger today — a
  `universe_id` is stored verbatim, never looked up — and no universe-ledger recovery primitive
  exists yet to pair with a widened gate). Resolves the iteration-12 reviewer's open scope question
  as a documented decision, not a code-behavior change.
- [ ] `micro_routes.py` `get_tick_recorder_compute`: correct the docstring's stale field list
  (`trades_total`/`quotes_total`) to name the fields `_progress_view` actually serves today
  (`trades_total_bucket`/`quotes_total_bucket` pre-release; the exact pair only after whole-
  ORIGINAL-pool release, per r7 §7.1 — already shipped in iteration 12, only the prose is stale).
- [ ] `tests/test_vault.py`: revise the three existing TC-5 tests
  (`test_tc5_an_unprovable_reconstruction_marks_affected_shards_exposure_unknown_permanently`,
  `test_tc5_a_wrong_nonempty_reconstruction_is_also_refused_never_treated_as_proven`,
  `test_tc5_a_shard_recovery_could_not_name_stays_protected_by_the_universe_rule_predicate`) to
  assert the corrected halt/union behavior — this is a deliberate correction of the function's own
  semantics, not a guard-test edit; none of the three is on the era's enumerated frozen-guard list.
  Add the exact three-shard reproduction from the evaluator's iteration-12 finding, an
  anchor-missing/unreadable variant, a re-recovery-after-halt test, and the seal/assign/expose
  own-ledger-only pinning test. See TC-1 through TC-7 below.

### Frontend

No new frontend code this iteration — the Validation Vault / Scout Ledger / Walk-Forward UI
sections remain J-08's unbuilt scope. The browser lane runs for **regression verification only**:
J-10's kept-product sentinel (every shipped surface, since this iteration touches code several of
them transitively read) and J-01's Microscope Readiness re-check (its `sealed_tranche` aggregate
routes through `vault.py`). No evidence retakes are pending this iteration (iteration 12 already
closed both flagged last round).

### New user-facing capability

None — this iteration hardens a recovery path that has zero production call sites; no new
control, page, or section.

### New information displayed

None. No served field, shape, or endpoint changes — the JSON `_progress_view` already serves is
unchanged (only its docstring prose was stale); `recover_shard_ledger`'s corrected return shape is
consumed by no route, CLI, or UI yet.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible. The only change in what the product can honestly claim is that a destroyed vault
record can no longer be silently forgotten by its own recovery tool.

### Blueprint conformance

No new pages, routes, or nav entries. This iteration adds one documentation-only note to
`blueprint.md` confirming no Data Contract row is needed (matching the iteration-12 coherence
audit's own precedent for `VaultRecoveryLedger`'s content). No nav-skeleton change; no
`blueprint.reapproval-requested` file.

### Data-contract additions

None. `recover_shard_ledger`'s corrected halt/union behavior has no serving endpoint (0
production call sites, matching the already-established precedent that this ledger's content
needs no Data Contract row "until a route or CLI ever surfaces it" — iteration-12
`coherence.md`). The `seal_shard`/`assign_shard`/`expose_shard` docstring clarification and the
`micro_routes.py` docstring fix touch no served field.

## OUT OF SCOPE

- **J-06 step 4** (the credentialed real Alpaca starter tranche recording) and **step 5**
  (readiness refresh over real tranche data). This iteration only removes the recovery-path
  blocker; the operator act itself is not attempted — no vendor call, no write to the operator's
  real `.data/datasets` store.
- **J-08** (the four new `/desk` sections + four new read-only MCP tools) and **J-09** (the pilot
  studies, which render through J-08's panels) — the next iteration's turn, per the
  iteration-11/iteration-12 evaluators' own sequencing; bundling either here would violate "never
  bundle two risky journeys".
- **TR-23 (r6 §8.1 `SEALED_PASS_RULE_V1` + new `micro_sealed_evaluation.py`)**, **TR-24 (r6 §8.2
  lineage-wide `proposed_confirmation_boundary`)**, and **TR-26 (r6 §3 `quote_depletion`
  revealing-quote fix + new `grid_version`)** — all ruled and plannable, all deliberately deferred:
  they touch `micro_graduation.py` and `micro_observer.py`/`micro_features.py`, distinct risk areas
  from this iteration's vault-only fix (same reasoning iteration 12 already recorded for excluding
  them).
- **Widening `seal_shard`/`assign_shard`/`expose_shard` to gate on BOTH ledgers as a mandatory
  check, plus a matching universe-ledger recovery primitive.** Deliberately deferred as a PAIR, not
  built as a half-measure — see BACKGROUND and `state/assumptions.md`'s iter-13 entries. Widening
  the gate alone, with no recovery primitive for the ledger it would newly refuse on, would
  introduce a new halt-with-no-recovery-path failure mode; doing so would also force updating
  roughly 81 existing test call sites across ten unrelated test files for zero
  production-reachable benefit.
- **The symbol/date case-sensitivity asymmetry in `_whole_pool_released_universe_ids`** (disclosed
  by the iteration-12 reviewer; fails safe only — a non-canonical-case-registered universe can
  never reach `REVEALED`, never an early leak). No action this iteration; carried forward
  unchanged.
- **Any new frontend code, page, or section.**
- **Evidence retakes.** None pending — iteration 12 already recaptured and closed the two flagged
  the round before (`iteration-state.md` Do-not-redo).
- **Editing any historical `docs/phases/goal-rapid-microscope-iter-*.md` phase spec.** Point-in-time
  records of what each iteration planned; never rewritten after the fact.

## DEFINITION OF DONE

- [ ] `recover_shard_ledger` refuses to resume (never rewrites the ledger) whenever it cannot NAME
  every anchor-attested row — closing the exact hole the iteration-12 evaluator found at
  `vault.py:1541` — TC-1, TC-2, TC-3, TC-4.
- [ ] `recover_shard_ledger`'s named-but-unverified branch marks the full union of prefix- and
  suffix-named dataset ids `exposure_unknown`, not the prefix alone — TC-5.
- [ ] The proven-complete recovery path is unchanged — TC-6.
- [ ] `seal_shard`/`assign_shard`/`expose_shard`'s own-ledger-only gating is documented as an
  intentional, pinned decision, resolving the iteration-12 reviewer's open scope question — TC-7.
- [ ] `micro_routes.py`'s stale recorder-progress docstring is corrected — TC-8.
- [ ] Required-still-passing journeys J-01 through J-05 and J-07 remain green — TC-10.
- [ ] J-10's kept-product sentinel renders as shipped and the trap-suite count is reconfirmed at 23
  of 28 (unchanged count; the TR-25 entry within it is now sound, not merely counted) — TC-11.
- [ ] No anti-goal violation introduced; the vault-ledger-integrity item on `iteration-state.md`'s
  blocker list closes.
- [ ] Unit tests pass; full suite count at or above 3212 collected / 3204 passed / 8 skipped / 0
  failed with 0 regressions; frozen rails (fingerprint `08e471b10130e1e2`, six `referee_*.py`
  hashes, MCP tool count 22, real `.data` store byte-unchanged) all unchanged — TC-9.
- [ ] J-06 remains appropriately partial — steps 4-5 are untouched by design; J-06 step 4 stays
  closed this iteration.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-13-dev.md` — TC-12.

## TESTING REQUIREMENTS

- Browser: J-10 (kept-product sentinel — `/`, `/structure`, `/desk` including every shipped
  section: Playbook/Band Context/Cohorts, Referee Registry/Adjudications/Runs, and the four
  already-shipped Rapid-Microscope sections' unchanged appearance — browser-verified via the
  store-scoped rig); J-01 (Microscope Readiness section re-check, since its `sealed_tranche`
  aggregate transitively reads the code this iteration touches). J-06 and J-07 have no NEW browser
  acceptance this iteration (J-06's own UI ships at J-08; J-07's servable surface and golden
  coverage are unchanged, per Do-not-redo).
- Unit/integration: every Backend IN SCOPE item above, plus the TC- scenarios below.
- Error cases: a shard-ledger recovery attempt that cannot NAME every anchor-attested row (a real
  row-count shortfall, or an unreadable anchor) must refuse to resume rather than silently omitting
  the unnamed shard from `exposure_unknown`; a recovery attempt whose named rows fail the
  hash-attested completeness check must mark every named dataset (prefix- and suffix-named alike)
  `exposure_unknown`, never a subset; a corrupted universe ledger must not change what
  `seal_shard`/`assign_shard`/`expose_shard` write (pinned, documented, unchanged behavior).

Test-first contract:

- TC-1: given a shard ledger sealing three shards (d-1, d-2, d-3, in that order) with a valid tail
  anchor recording `row_count=3`, when d-3's own row is destroyed (tail-truncated) and
  `recover_shard_ledger` is invoked with an empty `reconstructed_suffix`, then the outcome reports
  `resumed: False`, `rewrite_from_recovery` is never invoked (the ledger's own `verify_chain()`
  still reports `ok: False` immediately after the call), and d-3 does not appear in any
  `exposure_unknown` row or any other row anywhere.
- TC-2: given a shard ledger whose own durable tail-anchor file (not its content rows) is itself
  missing or unreadable, when `recover_shard_ledger` is invoked with any `reconstructed_suffix`,
  then the attempt is treated the same as TC-1's named shortfall (never as trivially "proven
  complete"), and it also refuses to resume.
- TC-3: given the halted outcome from TC-1, when `currently_sealed_dataset_ids`,
  `withheld_dataset_ids`, `unresolved_pool_universe_by_dataset_id`, and `build_vault_state` are
  each called afterward, then every one of them raises `VaultLedgerCorruptionError` rather than
  returning a result that omits d-3.
- TC-4: given the still-corrupted ledger left behind by TC-1's halted attempt, when
  `recover_shard_ledger` is invoked a second time with the caller's own byte-correct reconstruction
  of d-3's lost row, then the reconstruction proves complete, all three shards report `sealed`
  exactly as before the corruption, and `recovery_ledger.all_rows()` shows both the earlier halted
  attempt and the later completed one on permanent record.
- TC-5: given a two-shard ledger (d-1, d-2) whose tail is truncated, when `recover_shard_ledger` is
  invoked with a `reconstructed_suffix` that names d-2 with a row count matching the anchor but
  content that fails the hash-attested completeness check, then the outcome resumes
  (`resumed: True`, `ok: False`) and marks BOTH d-1 and d-2 `exposure_unknown` — not d-1 alone.
- TC-6: given a shard ledger's tail is truncated and then fully, byte-exactly reconstructed from a
  hash-attested trusted source, when `recover_shard_ledger` runs, then it resumes exactly as
  before this iteration's changes (`ok: True`, exact prior exposure state reported) — an explicit
  regression pin on the one path this iteration does not alter.
- TC-7: given `seal_shard`, `assign_shard`, and `expose_shard`'s own docstrings, when a reader
  inspects them, then each states that corruption-gating covers only its own shard ledger by
  design; and given the universe ledger's tail is truncated while the shard ledger stays intact,
  when each of the three functions is called, then all three still succeed exactly as before this
  iteration — a pinning test proving the documented scope matches the shipped behavior.
- TC-8: given `micro_routes.py`'s `get_tick_recorder_compute` docstring, when it is inspected after
  this iteration, then it names `trades_total_bucket`/`quotes_total_bucket` (the fields actually
  served pre-release) and no longer names the bare `trades_total`/`quotes_total` pair as if
  unconditionally served.
- TC-9: given the era's frozen rails, when the full backend suite runs after this iteration's
  changes, then the collected/passed/skipped/failed counts are at or above 3212/3204/8/0 with 0
  regressions, `Config().config_fingerprint()` still prints `08e471b10130e1e2`, all six
  `referee_*.py` SHA-256 hashes are unchanged from iteration 0, the MCP tool count stays the
  22-tuple, and the real `.data` store stays byte-unchanged (18 datasets, still no `micro_vault`
  directory).
- TC-10: given J-01 through J-05 and J-07's stored golden replay scripts (or the LLM browser-qa
  fallback where a golden is genuinely infeasible, per J-07's disclosed gap), when they replay
  against this iteration's code, then all six remain `passing` with zero regressions.
- TC-11: given J-10's kept-product sentinel (cockpit `/` live tape and chart, `/structure` load and
  Tradable Map, every shipped `/desk` section including the three Referee sections and the four
  already-shipped Rapid-Microscope sections), when the browser-qa lane runs this iteration via the
  store-scoped rig, then every kept surface's screenshot matches its already-established shipped
  appearance, and the era's trap-suite count is confirmed still at 23 of 28.
- TC-12: given the iteration completes, when `docs/handoffs/goal-rapid-microscope-iter-13-dev.md`
  is checked, then it exists on disk.

## NOTES

- **Lesson applied (iter-12):** "always probe the entity whose ONLY record was destroyed, and
  always re-run the integrity check AFTER the repair to see whether the repair erased the
  evidence." TC-1 through TC-4 do exactly this against the exact three-shard reproduction the
  evaluator ran.
- **Lesson applied (iter-11, pairing):** widening one side of a paired mechanism re-opens the leak
  through the twin left narrow. Applied twice this iteration — see BACKGROUND — both inside the
  `recover_shard_ledger` fix itself (halt-widening ships with union-widening) and in the decision
  NOT to widen the `seal_shard`/`assign_shard`/`expose_shard` gate without its recovery-primitive
  twin.
- Two `state/assumptions.md` entries recorded this iteration (`## iter-13 — goal-decomposer`,
  twice): the halt-vs-mark dividing line for `recover_shard_ledger`, and the seal/assign/expose
  own-ledger-only decision. Read them for the full reasoning behind both calls.
- Revising the three named existing TC-5 tests in `tests/test_vault.py` is INTENDED, not a
  guard-test edit — they assert the OLD (buggy) behavior of the exact function this iteration is
  tasked with correcting. None of the three is on the era's enumerated frozen-guard list
  (`EXPECTED_TOOLS`, `_PRICE_ARITHMETIC_FIELDS`, etc., per `docs/goal.md`'s own Constraints section).
- J-06 step 4 (real Alpaca tape) stays closed regardless of this fix landing — no vendor call, no
  operator act, no write to the real `.data/datasets` store this iteration.
- If anything here proves genuinely ambiguous against `docs/rapid-validation-spec.md`'s text once
  the developer is in the code, the project's own rule applies: drop, disclose, and surface for an
  owner ruling rather than improvise (T-1) — do not repeat the iteration-10 pattern where an
  unspecified TC pressure produced an invented rule.
