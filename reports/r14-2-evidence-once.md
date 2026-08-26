# r14.2 — physical evidence may earn OOS credit exactly once

**Branch** `goal/rapid-microscope` · **base HEAD** `6205d998` · **spec revision** r14.2
· `config_fingerprint` `08e471b10130e1e2` (frozen, untouched)

No market data was fetched, recorded, probed, released, assigned, exposed or inspected. No real
universe, corpus or candidate was registered. No sealed shard was touched. Every fixture below
builds its own universe under its own secret in `tmp_path`.

---

## ROOT CAUSES

All four gaps named in the brief were confirmed against the code before anything was changed. None
was disproved; one carried a nuance worth stating, and one of the brief's premises about §5 *was*
partly disproved (below).

| # | Gap | Confirmed where | Why it was reachable |
|---|-----|-----------------|----------------------|
| 1 | A universe could found many corpus eras | `micro_accessor.register_fresh_corpus_era` keyed its conflict check on `corpus_id` alone | r14.1 enforced `corpus_id → one universe` and simply never asked the inverse question. Nothing in the registry indexed by `universe_id`. |
| 2 | Release made data inspectable without recording exposure | `vault.release_unselected_dataset` had no `exposure_registry` parameter at all | Release was modelled as a *vault lifecycle* transition. It is also an *evidence* transition, and only the vault half was implemented. |
| 3 | Many datasets could occupy one registered position | `micro_corpus.eligible_oos_members` appended every matching record; `release_unselected_dataset` checked `_latest_shard_row(ledger, dataset_id)` | Both were keyed on **dataset id**, which is unique by construction. Neither ever asked whether the *position* was already taken. |
| 4 | 105 was read as a sufficiency floor | `walkforward.minimum_sessions_for_sufficient_folds`; the r14.1 proof test; `micro_readiness.survivor_min_session_dates` | The **function's own name** asserted sufficiency while computing constructibility, and that name propagated into a served API field and the desk UI. |

**The common shape.** Three of the four are the same mistake: an identity was checked on the key
that is unique *by construction* (`corpus_id`, `dataset_id`) rather than on the thing that is
actually scarce (the universe, the registered position). The fourth is a naming error that became a
scientific claim by being served.

### The nuance on gap 4

The r14.1 test `test_a_105_date_bound_corpus_produces_three_folds_...` asserted, at its step 4,
`len({m["session_date"] for m in test_members}) >= wf.WF_FOLD_MIN_SIGNAL_SESSIONS`. That compares a
**dataset-date count** against a floor whose name and meaning are **signal sessions** — sessions in
which qualifying observations actually occurred. It reads as a sufficiency check and is not one.
The test's other claims were sound; this one line overstated them.

### What was disproved

The brief states that `register_mode_b_spec()` is an in-memory constructor and asks whether *any*
durable predeclaration exists. The constructor claim is correct, but durable machinery **did**
already exist and was already in production use:

```
app/research/walkforward_ledger.py:235  record_mode_b_predeclaration()   # hash-chained mode_b_spec row
app/research/walkforward.py:1657        called by run_diagnostic_walkforward()
apps/backend/.data/micro_walkforward/walkforward_ledger.jsonl  # 1 real mode_b_spec row on disk
```

So the gap is narrower than stated, and also worse in one respect than stated:

* **Narrower** — a durable, hash-chained, idempotent predeclaration row already existed.
* **Worse** — its dedupe matched on `(sequence_id, spec_hash)`, so a **changed** spec did not match,
  fell through, and appended a *second* predeclaration for the same sequence. The ledger could hold
  two contradictory promises for one `(corpus_id, rule_id)`, each with its own `registered_at`, and
  a reader was free to cite whichever suited the result.

What genuinely did not exist is an operator path for a **real tick** campaign: the only production
caller predeclares one hardcoded *playbook-bar* rule.

---

## UNIVERSE/CORPUS UNIQUENESS

`micro_accessor.corpus_era_record_for_universe` is the new inverse index, read from the durable
hash-chained registry. `register_fresh_corpus_era` now refuses with
`UniverseAlreadyBoundToCorpusError` when a *different* `corpus_id` would draw on an
already-bound universe.

**Order matters and is deliberate.** The `corpus_id` lookup runs first; an idempotent replay returns
before the inverse check is ever reached, so re-registering an era is never refused for being bound
to the universe it *is* the binding of. Only a genuinely new `corpus_id` reaches the inverse check.

**The refusal holds with zero exposure rows** — the exploit is the fresh *namespace*, not the rows
already in it. A first era that has never been spent is just as binding as one that has.

Proven by `test_a_second_corpus_id_on_the_same_universe_refuses` (A),
`test_b_the_refusal_holds_when_the_first_era_has_zero_exposure_rows` (B),
`test_c_the_exact_same_binding_is_idempotent` (C — and asserts the **first** `registered_at`
survives a later replay), `test_d_the_same_corpus_id_under_a_changed_universe_identity_still_refuses`
(D — r14.1's `ConflictingCorpusEraError` is still reached),
`test_the_inverse_index_is_read_from_the_durable_ledger_not_process_state`, and
`test_a_different_universe_may_still_found_its_own_era` (the refusal is narrow).

---

## RELEASE AS EXPOSURE

`vault.release_unselected_dataset` now takes an `exposure_registry`, **resolves** its `corpus_id`
from the universe's own era (never from an operator argument — `UnboundReleaseCorpusError` if none),
and appends the exposure row **before** the shard row.

The two appends span independent hash-chained ledgers and cannot be made atomic. The order is chosen
for which failure is survivable:

| Order | Crash between the appends | Verdict |
|-------|---------------------------|---------|
| exposure → shard *(chosen)* | window burned, dataset still withheld | evidence destroyed — acceptable |
| shard → exposure | servable data with no exposure fact | unfalsifiable contamination — never |

Dedupe is per `(corpus_id, session window)` and only against a row **already stamped at or before**
the release instant (`micro_accessor.log_exposure_once`). A row stamped *later* would leave a gap a
spec could be frozen into, so it does not discharge the obligation.

The full lifecycle the brief specifies now holds by timestamps alone, with no special-casing in
`classify_evidence_class`:

```
spec frozen T1  →  release + exposure T2 > T1  →  window reads historical_oos
                →  later spec T3 > T2          →  same window reads historical_exposed_diagnostic
```

Proven by `test_release_precommits_the_exposure_before_the_dataset_is_servable`,
`test_no_released_dataset_is_servable_before_its_exposure_entry_exists` (a registry that refuses to
append leaves the dataset withheld — proved by **order**, not by inspection after the fact),
`test_a_crash_after_the_exposure_append_burns_the_evidence`,
`test_a_spec_frozen_before_the_release_may_still_receive_oos` (A),
`test_a_spec_frozen_after_the_release_sees_diagnostic` (B),
`test_a_release_under_a_universe_with_no_bound_corpus_refuses` (E),
`test_release_exposure_is_deduped_per_corpus_and_session_window` (F), and
`test_a_later_exposure_row_does_not_discharge_an_earlier_release`.

---

## DUPLICATE POSITION RULE

Enforced at both boundaries, and **fails closed** at each:

* **Membership** — `micro_corpus.eligible_oos_members` raises `DuplicateCorpusPositionError`
  (a subclass of `CorpusMembershipError`, so existing handlers keep working and cannot mistake it
  for an empty corpus). Checked *after* the class filters — a duplicate that is not even a member is
  not this corpus's problem — and *before* anything is returned.
* **Release** — `vault.release_unselected_dataset` raises `DuplicateReleasedPositionError`, indexed
  by `vault.released_positions`.

**No supersession rule was invented.** Latest / earliest / largest / first would each be a
methodology decision about which recording of a session is *the* recording. None is frozen in the
spec, so both paths refuse and a human resolves the duplicate on the record.

**One deliberate scope note.** `released_positions` indexes only rows that actually carry a
`symbol`/`session_date`. A `sealed` row records both as `None` on purpose (§7.5's opaque
projection — `vault.seal_shard` writes the nulls explicitly, and all 21 real sealed rows carry them).
That is not a hole: a sealed position is HMAC-selected, the frozen plan never marks it releasable,
and the release path refuses it earlier and for a stronger reason.

Proven by `test_two_genuine_datasets_at_one_registered_pair_refuse_membership` (A),
`test_a_second_dataset_at_an_already_released_pair_refuses_release` (B),
`test_a_duplicate_can_never_double_the_observation_count` (C), and
`test_the_manifest_positions_are_unique_by_symbol_and_session_date` (D).

---

## 105 CONSTRUCTIBLE VS SUFFICIENT

State it exactly, as the brief requires:

> **105 = the minimum distinct session dates required for 3 constructible folds under
> `DIAGNOSTIC_GEOMETRY`.**
>
> **105 does NOT guarantee a walk-forward survivor is reachable on a sparse candidate.**

No floor, no geometry and no threshold moved. `WF_FOLD_MIN_OBSERVATIONS`(30),
`WF_FOLD_MIN_SIGNAL_SESSIONS`(8), `WF_FOLD_MIN_SYMBOLS`(2) and 105 are all unchanged in value.

What changed is naming and reporting:

| Before | After |
|--------|-------|
| `minimum_sessions_for_sufficient_folds` | `minimum_sessions_for_constructible_folds` (old name retained as a **documented deprecated alias** — its name was itself the confusion) |
| fold counts conflated | `fold_sufficiency_summary` → `constructible_fold_count`, `sufficient_fold_count`, `insufficient_fold_count`, `meets_sequence_floor`, per-fold `shortfalls` |
| served `survivor_min_session_dates` / `survivor_status` | `constructible_folds_min_session_dates` / `constructible_folds_status` served beside them; **old keys retained at identical values** for wire compatibility |
| `FLOOR_BASIS_NOTE` promised "can a walkforward_survivor verdict be reached" | corrected; new `SUFFICIENCY_NOTE` served on every floor row and states the misnomer explicitly |
| desk UI column "Survivor needs" / "Survivor" | "3 folds need" / "3 folds buildable"; caption now states the observation floors |

**The two hermetic tests the brief requires:**

* **Negative** — `test_the_negative_case_105_dates_with_a_sparse_candidate_yields_no_sufficient_folds`.
  105 dates, two anchors per fold on one symbol. `build_folds` → **3 constructible**;
  `summarize_fold_observations` → **0 sufficient**, each naming all three failed floors;
  `sequence_verdict` → `refused: True`, `n_sufficient_folds: 0`.
* **Positive** — `test_the_positive_case_105_dates_with_dense_observations_can_reach_three_sufficient_folds`.
  105 dates, 10 sessions × 4 symbols per fold. **3 constructible, 3 sufficient**, every row
  `historical_oos` (the spec was predeclared before any window was exposed), and the sequence verdict
  reaches a real result rather than a floor refusal.

No real market data is used by either.

---

## REAL MODE B PREDECLARATION

The audit result is in **ROOT CAUSES → What was disproved**: durable predeclaration existed;
conflicting replay did not refuse; and no real-tick operator path existed.

Both holes are closed:

* `walkforward_ledger.record_mode_b_predeclaration` now raises
  `ConflictingModeBPredeclarationError` when the same `sequence_id` arrives under a different
  `spec_hash`. A byte-identical replay stays idempotent and still returns the **first**
  `registered_at`. A changed hypothesis needs a new `rule_id`.
* `walkforward.register_mode_b_spec` refuses `sidedness=None` (`UnsidedModeBSpecError`). Unsided
  stays legal at the Scout boundary — an exploratory candidate is a *question* — but a fixed
  hypothesis that passes its own test in either direction falsifies nothing.
* New operator stage `python -m scripts.j06_operator mode-b-predeclare --corpus-id ID --rule-id ID
  --sidedness long|short [--econ-floor-bps N] [--commit]`. **Dry by default**, like every other real
  act; the dry run reports the exact `spec_hash` it would freeze. Requires a bound corpus era.
  Freezes `corpus_id`/`rule_id`/`sidedness`/`econ_floor`, records `spec_hash`/`registered_at`,
  append-only, refuses conflicting replay.

**Safety check on the real ledger.** The live walk-forward ledger holds exactly **one** `mode_b_spec`
row (`seq-d39d20e47af24671`, spec_hash `3dea2e952321…`, corpus `playbook_setups_diagnostic_v1`), so
the new refusal cannot retroactively break an existing sequence. No real candidate was registered.

Proven by `test_a_mode_b_predeclaration_is_a_hash_chained_row_written_before_any_release`,
`test_an_identical_mode_b_replay_is_idempotent`, `test_a_conflicting_mode_b_replay_refuses`,
`test_an_unsided_mode_b_spec_refuses`, and the three `stage_mode_b_predeclare` tests.

---

## STUDY 1 STATUS

**`range_wall_failed_aggression` → `PARKED_PENDING_OWNER_SPEC`.** Recorded in code at
`micro_readiness.PILOT_STUDY_STATUS`, not only in prose.

The stated mechanism is a three-part conjunction: high aggression into the wall · collapsing impact
efficiency · **opposite-side `refill_consistent` replenishment**. `failed_aggression_score` covers the
first two as one composite; the refill co-occurrence is genuinely unbuilt, and `scout.py`'s own
frozen comment says so. Nothing was invented. The entry carries an explicit
`do_not: "screen the failed_aggression_score proxy under this mechanism's name"`.

## STUDY 3 STATUS

**`capitulation_exhaustion` → `PARKED_PENDING_OWNER_SPEC`.** Same mechanism.

The stated mechanism is an ordered **sequence** — extreme *sell* aggression, **then** collapsing
negative impact efficiency / replenishment. What exists is a single direction-agnostic
`failed_aggression_score` threshold at a `capitulation` signal: no then-sequence, no replenishment
term, not sell-specific.

**Neither gap is a coding task.** Each needs the owner to *specify* the missing mechanism — what
counts as "then", over what window, with what replenishment measure. Inventing that specification
now would be choosing the hypothesis after seeing the tape, which is the exact failure this funnel
exists to prevent.

---

## STUDY 2 CONTINUOUS REPRESENTATION

`micro_features.divergence_at_level` now returns Card 9.1's own two conjuncts as two independent,
mechanism-preserving coordinates:

```
price_extension_bps      = (price_extreme_τ2 − price_extreme_τ1) / price_extreme_τ1 × 10 000
delta_weakening_multiple = (cum_delta_τ1 − cum_delta_τ2) / delta_volume_fraction_threshold
```

**No weighted composite, no z-score, no fitted weights, no new threshold, no tuning.** The axes *are*
the mechanism. `available_at` remains `τ2`. Card 9.1's semantics are unchanged.

Each returns `None` explicitly when undefined rather than imputing a value:

* `price_extension_bps` — no positive basis to divide by (`price_extreme_τ1 ≤ 0` or missing).
* `delta_weakening_multiple` — the threshold is `None` (fewer than 5 baseline windows) **or** `0.0`
  (≥5 windows whose median volume is zero — thin tape, not a bug). Zero is not a positive measured
  denominator, so this is `None` rather than infinity or a divide-by-zero.

The coordinates are also carried through `scout._extract_divergence_anchors` onto each anchor. That
addition is **purely additive**: `screen_candidate` reads named keys (`feature_value`,
`session_date`, `symbol`, `outcome_bps`) and never hashes or enumerates the anchor dict, so no
ledgered or served value moves.

## STUDY 2 BOOLEAN EQUIVALENCE

```
price_extension_bps > 0
  ⟺ (p₂ − p₁)/p₁ × 10 000 > 0        [p₁ > 0, so the divisor is sign-preserving]
  ⟺ p₂ > p₁                           ← Card 9.1's price conjunct, exactly

delta_weakening_multiple ≥ 1
  ⟺ (cd₁ − cd₂)/δ ≥ 1                 [δ > 0, so the inequality direction is preserved]
  ⟺ cd₁ − cd₂ ≥ δ
  ⟺ cd₂ ≤ cd₁ − δ                     ← Card 9.1's delta conjunct, exactly
```

Recorded in code as `micro_features.DIVERGENCE_CONTINUOUS_EQUIVALENCE`, next to the function that
must keep satisfying it. Verified empirically on **5 305** randomized defined-domain cases plus
hand-derived oracles.

**The one disclosed asymmetry.** When `δ == 0.0` the **boolean stays defined** (it reduces to
`cd₂ ≤ cd₁`) while the continuous multiple is undefined. Card 9.1's semantics are frozen and were
**not** changed, so the equivalence is stated over the domain where both coordinates are defined, and
`micro_study2_diagnostic` drops those anchors honestly into an `undefined` count rather than imputing
a value onto the very axis origin the boolean tests against.

Hand oracles: `100.00 → 100.50` is `+50` bps; `δ = 0.25 × median([100]×5) = 25.0` and a `1000 → 0`
delta fall is `40.0` threshold-widths; exactly one threshold-width is `1.0` and is **inclusive**,
matching Card 9.1's `≤`.

**Study 2 discovery contract (§8).** `app/research/micro_study2_diagnostic.py` is capability only —
it was **not run**. It takes already-extracted anchors rather than a corpus, so it reads no store,
opens no dataset and cannot reach a sealed shard even by accident. It reports n anchors / n session
dates / n symbols, both coordinate distributions (with `n_undefined` counted separately), the four
quadrants of the two predeclared axis origins, and the canonical forward `return_bps` conditional on
the mechanism — aggregated as a **mean of session-cluster means**, never a flat pooled mean, and with
every outcome's unit *proven* before averaging. `EVIDENCE_CLASS` and `GRADUATION_CREDIT` are stamped
in-band on every report. There is no threshold sweep and no candidate ranking.

---

## TESTS

New file `apps/backend/tests/test_micro_r14_2_evidence_once.py` — **50 tests**, all passing:

| Group | n | Covers |
|-------|---|--------|
| §1 universe/corpus uniqueness | 6 | A, B, C, D + durability + narrowness |
| §2 release as exposure | 8 | precommit, non-servability, crash, OOS/diagnostic, unbound, dedupe, later-row |
| §3 duplicate position | 4 | A, B, C, D |
| §4 105 semantics | 4 | constructible boundary (105 → 3, 104 → 2), negative, positive, reporting contract |
| §5 Mode B predeclaration | 4 + 3 | durable/idempotent/conflicting/unsided + the operator stage |
| §7 Study 2 continuous | 10 | hand oracles, undefined denominators, equivalence (5 parametrized), `available_at`, no-lookahead, identity |
| §8 discovery contract | 8 | insufficient / killed ×2 / promising, quadrants, undefined, cluster mean, unit refusal |
| §6 parking | 3 | studies 1 & 3 parked, study 2 continuous-first, floors no longer claim a survivor |

**Two pre-existing test defects were fixed in passing**, both in `test_micro_r14_1_partial_pool_oos.py`:

1. `test_missing_snapshots_for_expected_members_fail_closed` asserted the window was *unexposed*
   after a fail-closed read. Under r14.2 the release itself burns the window, so that assertion no
   longer isolates what the test is about. Re-targeted to what it actually means: the refused read
   appends **no row of its own**.
2. The `operator` fixture saved-and-restored `j06_operator`'s module globals, so it faithfully
   restored whatever a test in *another file* had left behind. `test_the_starter_tranches_...` then
   failed purely on file order. **This reproduces on the unmodified baseline** (`git stash`; run both
   r14 files together with `-p no:randomly`) — it is a latent isolation bug, not a regression from
   this change. The fixture now **resets** to the starter defaults on entry.

---

## REAL LEDGER INVARIANTS

Verified after all changes, against the operator's real `.data` ledgers. Nothing was written.

| Ledger | State | Chain |
|--------|-------|-------|
| Scout | 18 rows | verifies |
| Vault shard | 21 rows, **all `sealed`** | verifies |
| Vault universe | 1 row, `rule_commitment`/`commitment_nonce` unchanged | verifies |
| Vault release plan | **0 rows** (no real plan committed) | verifies |
| Exposure registry | 174 rows, **all `record_kind: exposure`** — zero corpus-era rows, i.e. no real corpus era was registered | verifies |
| Walk-forward | 7 rows (1 `fold_spec`, 5 `fold_result`, **1** `mode_b_spec`) | verifies |

`config_fingerprint` `08e471b10130e1e2` — unchanged.

## FULL SUITE

**3 729 passed · 8 skipped · 0 failed · 0 errors** (3 737 collected). Delta from the r14.1 baseline
of 3 687 is exactly **+50**, the new file, so no pre-existing test changed outcome.

### One real-corpus test failed on the FIRST run, and why that is expected

`test_micro_join.py::test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_point`
failed once with `no_covering_snapshot` before passing on re-run. This is not flakiness and not a
defect — it is the provenance discipline doing its job, and it is a real operational consequence of
this change that anyone repeating the work should expect:

`micro_snapshots.feature_source_hash()` is a sha256 over the **source bytes** of
`micro_features.py` **and** `micro_observer.py`, recomputed fresh on every load. Adding the two
continuous coordinates to `divergence_at_level` therefore changed that hash, which **correctly
invalidated all 18 built snapshots of the real corpus at once**. The one test that asserts a real
on-disk snapshot is *currently valid* is the one test that must fail until the corpus is rebuilt.

Confirmed rather than assumed:

* the failure reproduces at the **unmodified base HEAD** (`git stash`; same assertion, same value);
* the 18 real snapshot metas were rebuilt by the suite itself between `09:59:16Z` and `10:07:14Z`
  and now **all 18 carry the live `feature_source_hash`** (`04ccce88…`);
* the test passes on re-run with the cache coherent.

**Consequence to carry forward:** any future edit to `micro_features.py` or `micro_observer.py` —
including a purely additive one — invalidates the entire real snapshot corpus and forces a rebuild.
That is strictly conservative (it can only turn a would-be cache hit into an honest miss) and is the
behaviour the spec asks for, but it means the first suite run after such an edit is expected to fail
this one test.

## FRONTEND TSC

`npx tsc --noEmit` → exit **0**.

---

## REMAINING BLOCKERS

Unchanged from r14.1 except where noted. **It is still not safe to record.**

1. **Storage is unresolved.** `PROVISION_STORAGE` was the r14 decision and nothing has been
   provisioned: ~1.19 TB projected at 105 dates against ~116 GB free.
2. **Tick retention before 2025-11-03 is unverified.** The retention probe is a deliberate,
   permanent burn of one session date and has not been run.
3. **No Mode B rule is freezable for any real study.** Study 2 is now mechanism-complete *and*
   continuous-first, but its direction is still unfrozen — and freezing it before the exposed
   diagnostic runs would be choosing a hypothesis with no evidence at all.
4. **Studies 1 and 3 are `PARKED_PENDING_OWNER_SPEC`** and cannot be screened as their stated
   mechanisms until the owner specifies what is missing. *(Newly formalized in r14.2.)*
5. **No real corpus era, release plan or universe exists for an OOS campaign.** The four r14.1
   operator acts plus the new `mode-b-predeclare` stage are all still unexecuted, by instruction.

Storage being provisioned would close (1) and leave (2)–(5) standing.

---

## NEXT SCIENTIFIC ACT

**Not recording.**

> Run the Study 2 continuous paired-touch diagnostic on the **already-exposed legacy tick corpus
> only**, and report `INSUFFICIENT` / `KILLED` / `PROMISING_FOR_MODE_B_FREEZE`.

That act is cheap, spends no fresh evidence, and is the only one of the three outcomes-gates that can
justify the expensive path. It answers the question that actually governs everything downstream:
**does the exposed corpus produce enough paired-touch anchors to estimate anything at all?**

* `INSUFFICIENT` → the exposed corpus cannot answer it. Nothing is claimed in either direction, and
  the recording decision must rest on something other than a promising discovery number.
* `KILLED` → Study 2 dies cheaply, having spent nothing. This is a good outcome.
* `PROMISING_FOR_MODE_B_FREEZE` → **only then** freeze a `long|short` Mode B rule via
  `mode-b-predeclare --commit`, and only after that consider the retention probe, storage and an OOS
  campaign.

It was **not performed in this task.** The capability exists; running it is a separate, explicit
instruction.

**Do not read a promising diagnostic as evidence of edge.** Every window it can read was exposed
before any rule could have been frozen against it, so its result is permanently
`historical_exposed_diagnostic` and can never graduate. It buys permission to go looking under
falsifiable conditions — nothing more.
