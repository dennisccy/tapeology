# The Rapid Microscope — closure audit + candidate-design owner memo

**Branch** `goal/rapid-microscope` · **HEAD** `144f8d30` · read-only audit.
No data recorded, released, probed or provisioned. No study re-run. No threshold changed.
No ledger rewritten. `config_fingerprint` `08e471b10130e1e2`.

---

# PART A — CLOSURE AUDIT

## RAPID MICROSCOPE CLOSURE VERDICT

# GOAL_CLOSEABLE

## WHY ZERO SURVIVORS IS ACCEPTABLE

The goal states the standard twice, in its own words:

> "**The era succeeds if it kills bad ideas honestly; it does NOT need to discover an edge.**"
> "Zero survivors is a passing grade."

The question is therefore not *did anything survive* but *were the kills honest*. Three properties
decide that, and all three hold against durable state:

**1. Every kill has a mechanical, ledgered reason.** 19 Scout rows, 13 distinct candidates, decisions
`killed_null` ×10, `killed_economic` ×6, `killed_insufficient_n` ×3. No free-text verdicts, no
judgment calls, no candidate abandoned without a row.

**2. Nothing was laundered.** Every one of the 19 rows is `historical_exposed_diagnostic`. Zero
`historical_oos` fold rows exist anywhere. The graduation ledger is **empty** — no candidate ever
left `exploratory`. There is no path by which a diagnostic result was upgraded.

**3. The gates were met, not lowered.** The final candidate (Study 2) cleared all three of Scout's
frozen sufficiency floors on real data — 14 ≥ 5 candidate, 5,599 ≥ 5 comparator, 2 ≥ 2 usable
sessions — and was then killed on the merits at p = 0.37. That is the difference between "we could
not look" and "we looked and it failed".

**The honest converse.** Zero survivors would NOT be a passing grade if the funnel had never been
able to pass anything. It could: `sequence_verdict` reaches a real verdict on a dense fixture
(r14.2's positive 105-date case), and `screen_candidate` returns `survive` on fixtures in r14.3's
case G. The machinery can say yes. It said no on this evidence.

## CORE SCIENTIFIC RAILS

All ten present, importable, and exercised by the green suite.

| Rail | Module | Evidence it is real, not declared |
|---|---|---|
| observer | `micro_observer.py` | prefix discipline; deferred constructs (`refill_consistent`, `quote_depletion`, `response_asymmetry`) with `available_at` ≠ measurement end |
| snapshot provenance | `micro_snapshots.py` | `feature_source_hash` over `micro_features`+`micro_observer` source bytes, re-checked on every load; 18/18 real metas current |
| Scout | `scout.py` | `screen_candidate` frozen ladder: α 0.05 · 2,000 block permutations · cells ≥5 · clusters ≥2 · top-1 ≤0.8 · econ floor · leave-one-session-out |
| exposure registry | `micro_accessor.py` | hash-chained, corpus-scoped; `log_exposure_once`; corpus-era rows structurally cannot mark a window exposed |
| walk-forward | `walkforward.py` | `build_folds`, `classify_evidence_class`, `fold_sufficiency_summary`, `sequence_verdict` refuses below floor |
| corpus identity | `micro_corpus.py` | bound eras, precommitted member sets, `corpus_manifest_hash` over `(dataset_id, checksum)` |
| recorder | `tick_recorder.py` | `RECORDER_SCHEMA_BASIS` distinguishes genuine recorder output from a legacy collision |
| Vault | `vault.py` | HMAC seal, surrogate ids, salted commitments, frozen release plan, deterministic decoy |
| graduation | `micro_graduation.py` | 4-state order; ledger empty (correct) |
| Referee isolation | `referee_*.py` | **6 of 6 byte-identical to `main`** (SHA-256 compared this audit) |

## REAL RESEARCH STATE

| | |
|---|---|
| Scout ledger | **19 rows**, 13 distinct candidates, 4 families, chain verifies |
| Real candidate decisions | `killed_null` 10 · `killed_economic` 6 · `killed_insufficient_n` 3 · **survive 0** |
| Study 2 | **KILLED** (`killed_null`, effect +0.487 bps, p 0.366, econ floor 1.526 bps, `econ_interesting` False) — row 18 |
| Studies 1 and 3 | `PARKED_PENDING_OWNER_SPEC` in `micro_readiness.PILOT_STUDY_STATUS`, each naming what is missing and the proxy it must not be screened as |
| Walk-forward | 7 rows: 1 `fold_spec`, 5 `fold_result`, 1 `mode_b_spec`; **0 `historical_oos`**; 3 insufficient / 2 sufficient |
| Sealed state | **21 shards, all `sealed`**; 0 ever assigned, 0 ever exposed, 0 `family_root_id` bound |
| Graduation | **0 rows** — nothing left `exploratory` |
| Exposure registry | 174 rows, all `record_kind: exposure`; 2 corpora (playbook 154, tick legacy 20); **no corpus-era row** — no fresh OOS corpus was ever registered |
| Release plan ledger | **0 rows** |
| Suite | 3,747 pass / 8 skip / 0 fail, against an era-open floor of 2,691/8 ("grows, never shrinks") |

## LEAKAGE / PROVENANCE

| Check | Result |
|---|---|
| All chains verify | Scout ✓ · walk-forward ✓ · vault shard/universe/incident/release-plan ✓ · exposure ✓ · graduation ✓ |
| No protected shard read | **0 of 19** Scout rows carry a sealed dataset id in `corpus_manifest`; `withheld_excluded = 80` on every row |
| Vault never opened | 0 shards assigned, 0 exposed — the sealed set has never been touched, so no single-shot was consumed |
| No evidence-class mixing | 19/19 Scout rows and 5/5 fold rows are `historical_exposed_diagnostic`; nothing emits `live_confirmatory` |
| No double OOS credit | 0 `historical_oos` rows exist; no `(sequence_id, fold_index)` appears twice |

## DATA ACQUISITION STATE

**No new 105-day campaign is scientifically justified, and that is a conclusion about candidates, not
about capacity.**

An OOS campaign is only meaningful for a *frozen Mode B hypothesis*. There is none, and there is no
candidate from which one could honestly be frozen:

- Study 2 is KILLED, with a positive effect against a bearish prediction. Freezing a short rule now
  would freeze the direction its own diagnostic just contradicted.
- Studies 1 and 3 are not yet specified mechanisms, so nothing about them is freezable.

Storage (`PROVISION_STORAGE`, ~1.19 TB projected) and tick retention before 2025-11-03 therefore
**stop being blockers and become dormant operational capabilities**. They were only ever blockers to
*acquisition*, and acquisition is not the constraint. They should not be spent, and they do not
prevent closing the era. The r14.2 operator acts (corpus era, release plan, release, probe,
`mode-b-predeclare`) are built, dry-by-default, and correctly unexecuted.

## DEFERRED ITEMS

**Intentionally deferred pilot mechanism work — NOT core defects:**

Studies 1 and 3, `PARKED_PENDING_OWNER_SPEC`. The goal's binding operator ruling reads:

> "if the era must shrink, defer in this order — UI/MCP polish first, then **up to two of the three
> pilot studies** — and NEVER weaken the observer, recorder/vault, Scout, walk-forward, provenance,
> or leakage-trap rails."

Exactly two of three are deferred, which is the maximum the ruling permits and precisely the item it
nominates as deferrable. Neither weakens a rail. Both are blocked on **owner specification**, not on
engineering: each needs a hypothesis stated before evidence, and inventing one now would be choosing
the mechanism after seeing Study 2's data.

**Actual unfinished scientific-core defects: NONE FOUND.**

I looked specifically for: a rail that exists in name only; a chain that does not verify; a candidate
with laundered evidence class; a sealed shard reached; a fold given OOS credit without a precommitted
spec; a served number whose denominator is unstated. None present.

**Two known limitations, neither a goal-level blocker, both already on the record:**

1. `register_screen_and_walkforward_check` re-extracts anchors — documented as fixture-affordable,
   not corpus-affordable. It is not on the Study 2 path and blocks nothing.
2. The r14.3 byte-identity proof covers 674 of 5,614 touch pairs (12%, GOOGL exhaustively), because
   the exhaustive oracle re-runs the path that could not finish in 90 minutes. Disclosed in
   `reports/r14-3-study2-scout-rail.md`.

## GOAL-LEVEL BLOCKERS

**None.** No cleanup work is manufactured here.

---

# PART B — CANDIDATE BOTTLENECK ANALYSIS

Rapid Microscope is now infrastructure. The binding constraint is candidate quality: the funnel can
falsify, and there is nothing worth feeding it.

**Analytical discipline held throughout.** The question answered below is *what hypothesis did we
mean before seeing more evidence*, never *what specification would survive*. Study 2's kill is used
nowhere: not to pick a window, threshold, feature, direction, context, horizon or comparison
population for either parked study.

## The structural fact that governs both studies

`scout._feature_membership` accepts **one scalar `feature_value`** under a `threshold` transform
(`ge|gt|le|lt`). There is no conjunction, no sequence and no multi-feature membership anywhere in
the screen. Both parked studies are conjunctions; Study 3 is an *ordered* conjunction.

This is not fatal, and the precedent is already built. Study 2 solved the same shape in r14.2/r14.3:
the extractor computes the mechanism's continuous coordinates, carries them on each anchor, and sets
`feature_value` to **one predeclared corner** of that space. The screen then runs unchanged. So the
machinery gap is a per-study extractor, not new screen infrastructure — but **the corner is the
hypothesis**, and defining it is exactly the owner ruling that cannot be delegated.

---

## STUDY 1 — RANGE-WALL FAILED AGGRESSION · UNSPECIFIED FIELDS

Declared: *"at band-map wall touches, does high aggression-into-the-wall with collapsing impact
efficiency and opposite-side `refill_consistent` replenishment precede rejection more than comparable
touches without that signature"*

| # | Field | Status | Notes |
|---|---|---|---|
| 1 | Anchor population | **ALREADY_FROZEN** | `structure_context_kind="band_touch"`; `enumerate_band_touches` — first touch, re-arm only on full exit, each band independently |
| 2 | Wall identity / side | **DERIVABLE_WITHOUT_NEW_RULING** | bands carry `side ∈ {support, resistance}`, encoded in `band_id`. "Into the wall" = buy into resistance, sell into support — follows mechanically |
| 3 | Wall-side coverage (both, or one) | **OWNER_RULING_REQUIRED** | symmetric two-sided study, or resistance-only. Changes the population and the outcome sign convention |
| 4 | Wall class filter (A/B/C, `quality_score`) | **OWNER_RULING_REQUIRED** | bands carry both; the spec does not restrict. Unrestricted is legal |
| 5 | What event establishes "aggression into the wall" | **OWNER_RULING_REQUIRED** + **NOT_IMPLEMENTED** | no frozen "aggression-into-wall" construct. Frozen ingredients: aggressor side (`buy\|sell`), `rolling_imbalance_{20t,100t,5000sh,50000sh}`, `same_side_run_length`, `volume_burst_{20t,100t}` |
| 6 | Is `failed_aggression_score` the representation or one component | **OWNER_RULING_REQUIRED** | **it already fuses two of the three conjuncts**: `dominant_side_volume_share × clamp(1 − \|delta_mid_bps\|/IMPACT_FLATNESS_SCALE_BPS, 0, 1)`. Using it collapses aggression and flatness into one scalar and hides which drove the result |
| 7 | "Collapsing impact efficiency" — level or trend | **OWNER_RULING_REQUIRED** | `impact_efficiency_{20t,100t}` (level) and `efficiency_trend_{20t,100t}` (trend) are both frozen. "Collapsing" reads more naturally as trend; the spec does not say |
| 8 | `refill_consistent` semantics | **ALREADY_FROZEN** | spec: displayed size restored at the same price within `REFILL_M_QUOTES`=20 same-side updates after executions against it; DEFERRED; `available_at` = M-th update or `unavailable`; boolean; the ONLY permitted label |
| 9 | What "opposite-side" means | **DERIVABLE_WITHOUT_NEW_RULING** (probably) | the observer registers refill on the side *executed against* (buy → `ask`), which **is** the aggressor's opposite side. The qualifier may be describing what the construct already does. Only a ruling is needed if the owner meant the *far* side |
| 10 | Co-occurrence vs ordered sequence | **OWNER_RULING_REQUIRED** | goal.md says "with … and …" and `scout.py`'s frozen comment says "at the SAME touch" — i.e. co-occurrence. **But `refill_consistent` is DEFERRED and cannot be known at the touch instant.** The declared co-occurrence is not observable at the declared anchor. This tension must be resolved explicitly |
| 11 | Measurement interval | **OWNER_RULING_REQUIRED** | 20t vs 100t variants exist for every relevant feature |
| 12 | `available_at` | **DERIVABLE_WITHOUT_NEW_RULING** | mechanically `resolve_outcome_start` = max conditioning `available_at` (spec §4/TR-17c). With refill included it is ≥ the M-th quote update. **Not an owner choice** |
| 13 | Comparator | **ALREADY_FROZEN** | Scout's comparator is the same anchor population where the threshold does not fire. **Not an owner choice** |
| 14 | Outcome horizon | **OWNER_RULING_REQUIRED**, bounded | `trades_20` or `trades_100` only — `_block_length_for_horizon` REFUSES shares/clock horizons outright |
| 15 | "Precedes rejection" → signed outcome | **OWNER_RULING_REQUIRED** | canonical outcome is `return_bps`. Rejection at resistance is negative, at support positive; a two-sided study needs an explicit sign convention |
| 16 | `sidedness` | **OWNER_RULING_REQUIRED** (deferred) | `None` is legal for exploratory Scout. A later Mode B freeze needs `long\|short`; a two-sided study must either sign-normalize or split into two candidates |

## STUDY 1 — OWNER-SPEC SKELETON

```
STUDY 1: range-wall failed aggression
  population:
    structure_context: band_touch                       [FROZEN]
    wall_sides:            ................  (resistance | support | both)
    wall_class_filter:     ................  (none | A | A+B | quality_score >= X)

  mechanism coordinates (continuous, kept multidimensional):
    C1 aggression_into_wall:
         feature:          ................  (rolling_imbalance_20t | ..._100t |
                                               same_side_run_length | volume_burst_20t | ...)
         signed toward wall by:  buy→resistance, sell→support        [DERIVABLE]
    C2 impact_response:
         feature:          ................  (impact_efficiency_20t | ..._100t |
                                               efficiency_trend_20t | ..._100t)
         "collapsing" =    ................  (low level | negative trend)
    C3 wall_replenishment:
         refill_consistent, side = the side executed against         [FROZEN, DEFERRED]
         opposite_side means:  ............  (side executed against | far side)

    decompose_failed_aggression_score:  ....  (yes: C1 and C2 separate
                                               | no: use the frozen product as one coordinate)

  conjunction:
    relation:              ................  (co-occurrence | ordered)
    refill timing:         ................  (REQUIRED — refill is deferred and cannot be
                                               known at the touch; choose: anchor at the
                                               refill resolution instant, OR drop C3 from the
                                               conjunction and report it descriptively)

  threshold variant (ONE predeclared corner of the coordinates above):
    corner:                ................

  outcome:
    horizon:               ................  (trades_20 | trades_100)      [bounded]
    rejection sign:        ................  (adverse-to-aggressor | raw signed return)
    sidedness:             None for discovery                              [FROZEN]
                           ................  for any later Mode B freeze

  available_at:  max(conditioning available_at)                            [DERIVABLE, not a choice]
  comparator:    same population, corner not met                           [FROZEN, not a choice]
```

---

## STUDY 3 — CAPITULATION EXHAUSTION · UNSPECIFIED FIELDS

Declared: *"do event-level exhaustion signatures (extreme sell aggression then collapsing negative
impact efficiency / replenishment) separate capitulation signals that snap back from those that do
not"*

| # | Field | Status | Notes |
|---|---|---|---|
| 1 | Anchor population | **ALREADY_FROZEN** | `structure_context_kind="playbook_signal"`, `setup_id="capitulation"`, joined at `trigger_ts` via `join_playbook_signal` |
| 2 | Signal = context or mechanism | **DERIVABLE_WITHOUT_NEW_RULING** | "separate capitulation signals that snap back from those that do not" makes the signal the POPULATION and the exhaustion signature the discriminator. The alternative reading (signal geometry participates) exists but is not what the sentence says |
| 3 | What makes sell aggression "extreme" | **OWNER_RULING_REQUIRED** + **NOT_IMPLEMENTED** | no sell-SIGNED aggression feature is frozen. The current proxy `failed_aggression_score` uses `dominant_side_volume_share` — **direction-agnostic**, so it fires on buy climaxes too. Frozen ingredients exist (aggressor side is `buy\|sell`; `rolling_imbalance_*` is signed) but a sell-specific extremity measure must be named |
| 4 | The "THEN" relation | **OWNER_RULING_REQUIRED** + **NOT_IMPLEMENTED** | no ordered-sequence machinery exists in the screen or the extractor vocabulary. Both the semantics and the plumbing are absent |
| 5 | Allowed lag between aggression and exhaustion | **OWNER_RULING_REQUIRED** | nothing frozen. The spec has no conditioning-lag vocabulary at all; `HORIZON_KEYS` are outcome spans, not lags |
| 6 | Impact-efficiency condition | **OWNER_RULING_REQUIRED** | `impact_efficiency_*` is signed bps per 1,000 aggressive shares. For sell aggression it is negative; "collapsing negative efficiency" = magnitude shrinking toward zero. Level vs `efficiency_trend_*` is unstated |
| 7 | Replenishment's role | **OWNER_RULING_REQUIRED** | the declaration writes "collapsing negative impact efficiency **/** replenishment". The slash is genuinely ambiguous: alternative, conjunct, or gloss |
| 8 | Continuous-first representation | **OWNER_RULING_REQUIRED** | required by goal.md; the coordinates are proposed below but the owner must adopt them |
| 9 | `available_at` | **DERIVABLE_WITHOUT_NEW_RULING** | max conditioning `available_at`, and ≥ the playbook `trigger_ts`. **Not an owner choice** |
| 10 | Comparator | **ALREADY_FROZEN** | same population, corner not met. Note the population is capitulation signals only — materially smaller n than Studies 1–2 |
| 11 | Horizon | **OWNER_RULING_REQUIRED**, bounded | `trades_20` or `trades_100` only |
| 12 | Short/long semantic expectation | **OWNER_RULING_REQUIRED** | the frozen detector carries `side: "long"` (snap-back), and "snap back" is a positive return — so LONG is the natural reading. But the declaration says "separate", not which direction the signature predicts. Whether exhaustion predicts snap-back (long) or continuation (short) is a genuine hypothesis choice |

## STUDY 3 — OWNER-SPEC SKELETON

```
STUDY 3: capitulation exhaustion
  population:
    structure_context: playbook_signal, setup_id="capitulation"    [FROZEN]
    signal role:       conditioning context                        [DERIVABLE]

  mechanism coordinates (continuous, kept multidimensional):
    C1 sell_aggression_extremity:
         feature:          ................  (must be SELL-SIGNED; the current proxy is not)
         window:           ................  (20t | 100t | 5000sh | 50000sh)
    C2 impact_efficiency_collapse:
         feature:          ................  (impact_efficiency_20t | ..._100t |
                                               efficiency_trend_20t | ..._100t)
         "collapse" =      ................  (|efficiency| shrinking | trend sign flip)
    C3 replenishment (role unresolved):
         refill_consistent                                          [FROZEN, DEFERRED]
         role:             ................  (required conjunct | alternative to C2 |
                                               descriptive only)

  ordering:
    relation:              ................  (C1 strictly before C2 | co-occurrence)
    max_lag:               ................  (REQUIRED if ordered; no frozen vocabulary exists —
                                               state units: trades | shares | seconds)
    measurement anchor:    ................  (at C2's resolution instant | at trigger_ts)

  threshold variant (ONE predeclared corner):
    corner:                ................

  outcome:
    horizon:               ................  (trades_20 | trades_100)      [bounded]
    hypothesis direction:  ................  (exhaustion → snap back (long)
                                               | exhaustion → continuation (short))
    sidedness:             None for discovery                              [FROZEN]

  available_at:  max(conditioning available_at), >= trigger_ts             [DERIVABLE, not a choice]
  comparator:    capitulation signals where the corner is not met          [FROZEN, not a choice]
```

---

## CONTINUOUS-FIRST REPRESENTATIONS

**The existing frozen features already form the natural coordinates for both studies.** No new
composite is needed, and none should be invented.

**Study 1 — three coordinates, kept three-dimensional:**
```
C1  aggression into the wall      (F-FLOW, signed toward the wall side)
C2  impact response               (F-RESPONSE: impact_efficiency_* or efficiency_trend_*)
C3  wall replenishment            (F-LIQUIDITY: refill_consistent, boolean, deferred)
```
The threshold variant is one predeclared corner of that space, exactly as
`bearish_divergence` is the corner `price_extension_bps > 0 ∧ delta_weakening_multiple ≥ 1`.

> **The one live composite risk, and it is pre-existing.** `failed_aggression_score` is
> `dominant_side_volume_share × flatness` — it *already* multiplies C1 and C2 into a single scalar.
> It is mechanism-defined, not fitted, so it is not banned. But adopting it as *the* representation
> re-creates precisely the defect r14.2 corrected in Study 2: a fused scalar cannot show which
> conjunct carried the result, and a study whose stated mechanism is a three-part conjunction cannot
> be falsified through a two-part product. **This is the single most consequential ruling in Study 1.**

**Study 3 — two coordinates plus a relation:**
```
C1  sell-signed aggression extremity   (F-FLOW; NOT the direction-agnostic current proxy)
C2  impact-efficiency collapse         (F-RESPONSE; efficiency_trend_* is the natural "collapse" axis)
[C3 refill_consistent — role unresolved]
```
The **"THEN" relation is not a coordinate**. It is an ordering constraint on when C1 and C2 are
measured, and it cannot be flattened into a scalar without destroying the mechanism. Keep it as a
constraint on the anchor construction, not as a dimension.

**Explicitly not proposed anywhere above:** weighted composites, fitted weights, z-score mixtures,
optimized cut-points, or any grid sweep.

## OWNER DECISION TABLE

| Field | Why it matters | Current status | Legal options under existing spec/code | What the owner must decide |
|---|---|---|---|---|
| **S1 · decompose `failed_aggression_score`** | It already fuses 2 of 3 conjuncts; fused, the study cannot show which conjunct acted | OWNER_RULING_REQUIRED | (a) separate C1/C2 coordinates; (b) keep the frozen product as one coordinate | Whether Study 1's mechanism is a 3-part conjunction or a 2-part product |
| **S1 · refill timing vs co-occurrence** | `refill_consistent` is DEFERRED; the declared "same touch" co-occurrence is **not observable at the touch** | OWNER_RULING_REQUIRED | (a) anchor at the refill resolution instant; (b) drop C3 from the conjunction, report descriptively; (c) redefine the anchor | How a deferred construct can be part of an instantaneous conjunction |
| **S1 · wall-side coverage** | Sets population and outcome sign | OWNER_RULING_REQUIRED | resistance-only · support-only · both | Whether Study 1 is one hypothesis or two |
| **S1 · wall class filter** | Bands carry class A/B/C and `quality_score` | OWNER_RULING_REQUIRED | none · A · A+B · score threshold | Whether wall quality is part of the hypothesis |
| **S1/S3 · aggression feature + window** | No "aggression" construct is frozen; several candidates are | OWNER_RULING_REQUIRED | `rolling_imbalance_{20t,100t,5000sh,50000sh}` · `same_side_run_length` · `volume_burst_{20t,100t}` | Which frozen feature *is* the mechanism's aggression term |
| **S1/S3 · "collapsing" = level or trend** | Both families are frozen; they are different claims | OWNER_RULING_REQUIRED | `impact_efficiency_*` (level) · `efficiency_trend_*` (trend) | Whether "collapse" means low or falling |
| **S3 · sell-signed extremity** | The current proxy is direction-agnostic and fires on buy climaxes | OWNER_RULING_REQUIRED + NOT_IMPLEMENTED | any signed F-FLOW feature restricted to sell aggression | What makes sell aggression "extreme" |
| **S3 · the "THEN" relation** | The ordering *is* the mechanism | OWNER_RULING_REQUIRED + NOT_IMPLEMENTED | strict ordering with a max lag · co-occurrence | What "then" means, and in what units |
| **S3 · max lag** | No frozen lag vocabulary exists anywhere | OWNER_RULING_REQUIRED | trades · shares · seconds, value unstated | The permitted separation between C1 and C2 |
| **S3 · replenishment role** | The declaration's "/" is genuinely ambiguous | OWNER_RULING_REQUIRED | required conjunct · alternative to C2 · descriptive only | Whether replenishment is part of the claim |
| **S3 · hypothesis direction** | Determines what a positive result would mean | OWNER_RULING_REQUIRED | snap-back (long) · continuation (short) | Which way exhaustion is predicted to resolve |
| **S1/S3 · outcome horizon** | Sets the permutation block length | OWNER_RULING_REQUIRED, **bounded** | `trades_20` · `trades_100` **only** — shares/clock are REFUSED by `_block_length_for_horizon` | Which of the two trade-count horizons |
| ~~available_at~~ | — | **DERIVABLE** | `max(conditioning available_at)` (§4/TR-17c) | **Not an owner choice** — it follows mechanically |
| ~~comparator~~ | — | **FROZEN** | same population, corner not met | **Not an owner choice** |
| ~~`refill_consistent` semantics~~ | — | **FROZEN** | `REFILL_M_QUOTES`=20, deferred, boolean, sole permitted label | **Not an owner choice** |
| ~~wall side identification~~ | — | **DERIVABLE** | buy→resistance, sell→support | **Not an owner choice** |
| ~~discovery `sidedness`~~ | — | **FROZEN** | `None` for exploratory Scout | **Not an owner choice** at discovery |

## NEXT ERA OPTIONS

Stated as scientific commitments, not expected returns. I am not ranking B against C.

**A. Close Rapid Microscope and stop research here.**
Commits to: the funnel as a finished, dormant instrument. The era's claim becomes *we built something
that can falsify microstructure hypotheses honestly, and it falsified everything we had.* No new
hypothesis is owed. The vault's 21 sealed shards stay sealed and their single shots stay unspent —
which keeps them available indefinitely. The risk accepted is that infrastructure with no live
research programme decays: `feature_source_hash` invalidations, snapshot rebuilds and dependency
drift accumulate silently against a suite nobody is running for a purpose.

**B. Close, then open a candidate-design era beginning with Study 1.**
Commits to: **specifying a three-part conjunction, and resolving how a DEFERRED construct
participates in an instantaneous one.** That second problem is the substantive one and it is
general — it recurs for any mechanism involving replenishment or depletion. Study 1 also inherits a
population that demonstrably exists in the corpus (band touches were found in 3 of 18 datasets) and
a decomposition question with a clear precedent in Study 2's r14.2 correction.

**C. Close, then open a candidate-design era beginning with Study 3.**
Commits to: **building ordered-sequence machinery that does not exist anywhere in the funnel today,
and naming a sell-signed aggression measure that is not currently a frozen feature.** Both are new
vocabulary, not new parameters. Study 3 also commits to the smallest population of the three
(capitulation signals only), which raises the risk of `killed_insufficient_n` before any mechanism is
tested — a real cost, since a study that cannot reach a verdict teaches less than one that fails.

## RECOMMENDED IMMEDIATE PROCEDURAL STEP

**Close The Rapid Microscope era first, as a zero-survivor success, before any new research begins.**

The audit shows `GOAL_CLOSEABLE` with no goal-level blockers. Closing now, rather than after a new
study is specified, matters procedurally for one reason: the era's record is currently clean and
self-contained — 13 candidates, 13 kills, zero laundered results, an untouched vault, an empty
graduation ledger. Opening candidate-design work *inside* this era would mix a new hypothesis's
history into a closed falsification record and make the zero-survivor claim harder to audit later.

I am deliberately **not** recommending Study 1 over Study 3, or either over stopping. That choice
turns on which scientific commitment the owner wants to make (B's deferred-construct problem vs C's
ordered-sequence vocabulary), and on whether there is appetite for a new hypothesis at all — none of
which follows from anything in the code or the ledgers.
