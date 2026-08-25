# Rapid Microscope — measurement-semantics audit (unit + side)

**Date:** 2026-08-25 · **Branch:** `goal/rapid-microscope` · **Status:** audit complete, pre-fix

This audit was produced BEFORE any code change, per the operator's instruction. Every claim
below cites the line that establishes it.

---

## 1. What physical/unit meaning does `mid_outcome()["value"]` have today?

A **raw price difference in dollars** (quote currency), direction-signed:

```python
# micro_features.py:372
value = _signed(mid_at_horizon - mid_at_start, side)
```

`last_trade_outcome` (`micro_features.py:399`) is identical in kind. By contrast
`spread_bps()` (`micro_features.py:410-417`) is a genuine ratio:
`spread / mid * 10_000.0`.

So the module already contains **both** unit systems, one line apart, with no naming that
distinguishes them.

## 2. Where does it first become labelled as bps?

`scout.py:1045`:

```python
effect_bps, _per_session = _observed_effect(session_groups)
```

The rename happens **with no accompanying arithmetic**. It is then persisted under that name at
`scout.py:1253` (`screen_result["effect_bps"]`) and `scout.py:1109`
(`_bucket_effect`'s per-bucket `"effect_bps"`), and served verbatim by
`GET /research/desk/micro/scout`.

## 3. Is there any hidden normalization between the feature layer and Scout?

**No.** The full chain, verified line by line:

| Step | Site | Unit |
|---|---|---|
| outcome computed | `micro_features.py:372` | dollars |
| wrapped | `micro_join.py:299` `_build_outcome()["mid"]` | dollars |
| anchor built | `scout.py:443, 495, 611, 684` `outcome_value` | dollars |
| per-session delta | `scout.py:831` `cand.mean() - comp.mean()` | dollars |
| pooled effect | `scout.py:840-850` `_observed_effect` | dollars |
| **named** | `scout.py:1045` `effect_bps` | **still dollars** |
| **gated** | `scout.py:1249` `abs(effect_bps) >= econ_floor["floor_bps"]` | **dollars vs bps** |

Every intermediate step is a mean or a difference of dollar values. There is no division by
price anywhere in the path.

`floor_bps` on the right-hand side is genuine bps: `scout.py:1353`
`floor_bps = ECON_FLOOR_SPREAD_MULTIPLE * family_median_spread_bps`, where the median is taken
over `mf.spread_bps(...)` values (`scout.py:786`).

**The economic gate is dimensionally invalid.**

### 3b. Second, independent defect at the same site (not in the original brief)

`_observed_effect` averages session-cluster mean deltas **across symbols** — the live corpus
spans PG, AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, SPY, TSLA. A dollar move is not
comparable across price levels, so pooling dollar deltas across an ~$160–$600 price range is not
a meaningful estimator *regardless of what it is later compared against*. Converting the
outcome to a return fixes the estimator and the gate together.

## 4. Which Scout decisions depend on the magnitude?

| Decision | Site | Magnitude-dependent? |
|---|---|---|
| `killed_economic` | `scout.py:1296-1298` | **Yes — dimensionally invalid** |
| `killed_null` | `scout.py:1277` | Scale-free per se (block permutation), but contaminated by the cross-symbol dollar heterogeneity in §3b |
| `killed_direction` | `scout.py:1279` | Sign only |
| `killed_fragile` | `scout.py:1299` | Sign stability only |
| `killed_concentration` | `scout.py:1284` | Counts only |
| `killed_insufficient_n` | `scout.py:1270` | Counts only |

## 5. Which walk-forward rules depend on the magnitude?

`evaluate_survivor_rule` (`walkforward.py:661-705`):

- **condition 3** (`:676-682`) — `abs(pooled_effect) >= econ_floor["floor_bps"]`
- **condition 4** (`:647-658`) — `abs(f["effect"]) >= floor_bps`

Conditions 1, 2 and 5 are counts/signs and are unit-independent.

**The walk-forward effect is in a THIRD unit.** Its observation feed is
`walkforward.py:1236` `"value": horizon["return_pct"]`, and `desk_forward.py:40` states
plainly: *"`return_pct` values are PERCENT (x100)"* (computed at `desk_forward.py:539`).

So conditions 3 and 4 compare **percent against basis points** — a 100× error. It is currently
**dormant**, not benign: the only registered sequence carries `econ_floor: null`
(`walkforward.py:1292` registers `econ_floor=None`), so the comparison has never executed. Any
J-09 study that supplies Scout's floor to a fold sequence fires it.

## 6. Which sealed-evaluation rules depend on the magnitude?

`micro_sealed_evaluation.py:252-273` — `clears_economic_floor` =
`abs(summary["effect"]) >= econ_floor["floor_bps"]`, producing failure reason
`below_economic_floor` (`:154, :273`). `summary` comes from the same
`walkforward.summarize_fold_observations`, so it inherits the percent-vs-bps defect exactly.

## 7. Which persisted artifacts contain old-semantics values?

| Store | Contents | Classification |
|---|---|---|
| `.data/micro_scout/ledger.jsonl` | **6 real rows**, run `c7817e82`, 2026-08-25T14:07–14:16Z. `screen_result.effect_bps`, `.per_session_deltas_bps`, `.fallback_tercile[*].effect_bps`, `.best_of_n_disclosure.corrected_threshold_bps` — **all dollars**. `econ_floor.floor_bps` / `family_median_spread_bps` — genuine bps. | **Requires recomputation** |
| `.data/micro_walkforward/walkforward_ledger.jsonl` | 1 `fold_spec` + fold results for `seq-d39d20e47af24671`; effects in **percent**; `econ_floor: null` | **Retain, but version + label** — no economic comparison ever executed |
| `.data/micro_graduation/` | **Does not exist.** `GET .../graduation` → `{"families": [], "message": "No candidates ledgered."}` | Nothing to invalidate |
| sealed evaluations | **None on disk anywhere** | Nothing to invalidate |
| `.data/micro_vault/`, `.data/micro_exposure_registry/` | Shard/universe/exposure ledgers — carry no outcome magnitudes | Unaffected |

`.data/` is gitignored (`.gitignore:72`), so none of this is committed evidence.

## 8. Are real scientific results already persisted under the wrong semantics?

**Yes, but narrowly, and nothing laundered downstream.**

The 6 real Scout rows are genuine exploratory results. Two of them
(`quote_imbalance ≥0` / `≤0`) carry `decision = killed_economic` — decisions produced by the
dimensionally invalid comparison, and therefore **not scientifically valid as recorded**. The
other four died on `killed_null` (×3) or `killed_insufficient_n` (×1), neither of which touches
the floor; those verdicts are unaffected in kind, though their recorded effect magnitudes are
still mislabeled.

Nothing consumed them: graduation is empty, no sealed evaluation exists, no candidate ever
reached `walkforward_survivor`. **No claim escaped the funnel under the bad unit.**

---

## 9. Side / direction vocabulary

Two distinct vocabularies exist and they collide at exactly one site.

- **Aggressor side** `buy | sell` — `micro_observer.py:276, 291, 423, 425, 589, 593`
- **Candidate direction** `long | short` — `walkforward.py:642, 654`,
  `micro_sealed_evaluation.py:218`, and the frozen `desk_playbook_detect.py` /
  `backtests.py:1110`

The collision:

```python
# micro_features.py:348-351
def _signed(value, side):
    return -value if side == "sell" else value
```

```python
# scout.py:431 (and :599)
mj.outcome_row_at_single_horizon(..., side=sidedness)   # sidedness ∈ {long, short, None}
```

A candidate registered `sidedness="short"` reaches `_signed` as `"short"`, does **not** match
`"sell"`, and is silently returned unflipped. It would then meet `killed_direction`
(`scout.py:1279`, which requires `effect_bps > 0`) and a genuine short edge would be recorded as
a wrong-direction kill.

**This bug has never fired.** Every registered candidate carries `sidedness: None` —
`default_fixture_grid` (`scout.py:1580`) and all three pilot studies
(`scout.py:1652, 1665, 1677`). It is **latent, not corrupting**. `_signed` has exactly two
callers, both in `micro_features.py`; aggressor-signing of *features* is done separately and
correctly inside `micro_observer.py`.

---

## 10. The specification itself is contradictory

This is a spec defect propagated faithfully into code, not only an implementation slip.

- **§0 Units** (`docs/rapid-validation-spec.md:215`) — *"Returns/moves in percent or bps as named
  per field"*
- **§4 Outcomes** (`:423-424`) — *"forward **mid-price** move (quote mid at the horizon boundary
  minus mid at the outcome start)"* → **a dollar subtraction**
- **§5.5** (`:480`) — `econ_interesting = |effect_bps| ≥ ECON_FLOOR_SPREAD_MULTIPLE ×
  family_median_spread_bps` → **bps vs bps**

§4 and §5.5 are mutually inconsistent, and §4 violates §0. The implementation obeyed both
literally, which is how dollars came to be compared against basis points.

Because the defect originates in the canonical spec, the correction must be recorded as a
**named methodology revision**, not a silent rewrite.

---

## 11. Root cause (one sentence)

`docs/rapid-validation-spec.md` §4 defines the primary outcome as an absolute mid-price
*difference* while §5.5 gates it against a *ratio* floor expressed in basis points;
`micro_features.mid_outcome()` implements §4 literally, `scout.py` renames the result
`effect_bps` at `:1045` without converting it, and `scout.py:1249` compares the two — so the
economic-relevance gate has been evaluating **dollars ≥ basis points** since the module was
written, with a parallel **percent ≥ basis points** defect dormant in `walkforward.py:682` and
`micro_sealed_evaluation.py:257`.

---
---

# Part 2 — the correction (spec revision r13, 2026-08-25)

## 12. What changed

| File | Change | Why |
|---|---|---|
| `app/research/micro_features.py` | `mid_outcome`/`last_trade_outcome` now return `return_bps` (primary) + `delta_price` (diagnostic) + `unit`; the ambiguous `value` key is **removed**; `_signed` replaced by eager direction validation; added `BPS_UNIT`, `OUTCOME_UNIT`, `AGGRESSOR_SIDES`, `CANDIDATE_DIRECTIONS`, `UnknownSideVocabularyError`, `UnitMismatchError`, `aggressor_sign`, `direction_sign`, `direction_for_aggressor`, `require_bps_floor`, `clears_economic_floor` | The root cause. The outcome is now computed by `bps_move` — the correct primitive **this module already owned** and the outcome path simply never called |
| `app/research/micro_join.py` | `side=` → `direction=` through the outcome-row helpers | The parameter carries a candidate direction, never an aggressor side |
| `app/research/scout.py` | Reads `return_bps`; anchor key `outcome_value` → `outcome_bps`; `econ_interesting` via `clears_economic_floor`; `econ_floor` stamps `unit`; frozen `outcome` spec gains `unit`; `screen_result` gains `outcome_unit` | The gate now compares bps to bps, and the unit is frozen into the candidate identity |
| `app/research/walkforward.py` | `PCT_TO_BPS`/`observation_value_bps` convert the `return_pct` feed at its one boundary; fold summaries carry `unit`; survivor conditions 3 and 4 route through the unit-checked door | Closes the dormant percent-vs-bps 100× error |
| `app/research/micro_sealed_evaluation.py` | `clears_economic_floor` at the sealed gate | Same door, same semantics |
| `app/research/micro_readiness.py` | `totals` gains `distinct_symbols`, `distinct_sessions`, `label_quality` | Corpus growth must be judgeable by evidence QUALITY, not only count |
| `docs/rapid-validation-spec.md` | Revision **r13**; §0 Units and Side vocabularies; §4 outcome formula; §5.5 floor unit + the three-concept table; trap **TR-33** | The defect originated in the spec — the correction is recorded as a named revision, not a silent rewrite |
| `docs/goal.md` | r13 note in the era header | The journeys are the record of what was built and are not rewritten |
| `tests/test_micro_unit_semantics.py` | **New** — 31 guards | The tests that would have caught this immediately |

## 13. Methodology change

| | Before | After (r13) |
|---|---|---|
| Primary outcome | `mid_h − mid_s` — **dollars**, key `value` | `(mid_h − mid_s) / mid_s × 10_000` — **basis points**, key `return_bps` |
| Raw dollar move | *was* the scientific quantity | `delta_price` — diagnostic only, never pooled or gated |
| Scout effect | dollars, named `effect_bps` | genuine bps |
| Walk-forward / sealed effect | percent (`return_pct`) | genuine bps |
| Economic gate | `dollars ≥ bps` | `bps ≥ bps`, both sides unit-proved |
| Unit declaration | none | on every outcome row, fold summary, floor, and screen result |

**No gate was weakened.** `ECON_FLOOR_SPREAD_MULTIPLE` stays `1.0`; `SCOUT_SCREEN_ALPHA` `0.05`;
`SCOUT_MIN_SESSION_CLUSTERS` `2`; `SCOUT_MIN_OBSERVATIONS_PER_CELL` `5`;
`SCOUT_MAX_TOP1_CONCENTRATION` `0.8`; `WF_MIN_SUFFICIENT_FOLDS` `3`; fold geometry 40/5/20/20;
`SEALED_MIN_OBSERVATIONS` `30`. Only the unit moved.

## 14. Side semantics

| | Before | After (r13) |
|---|---|---|
| Vocabulary | implicit, interchangeable | two closed, disjoint sets |
| Aggressor side | `buy`/`sell` (observer) | `AGGRESSOR_SIDES` — validated by `aggressor_sign` |
| Candidate direction | `long`/`short` (`sidedness`) — reached a helper that only knew `sell` | `CANDIDATE_DIRECTIONS` — validated by `direction_sign` |
| Unknown value | silently returned **+value** | raises `UnknownSideVocabularyError`, **before** any unmeasured/truncated short-circuit |
| Conversion | implicit and accidental | one named adapter, `direction_for_aggressor` |

## 15. Persisted-data impact

- **`.data/micro_scout/ledger.jsonl` — 12 rows, 6 distinct pre-r13 variants, 2 runs
  (`c7817e82` 14:07–14:16Z, `02720c6c` 15:01–15:12Z).** Every magnitude is dollars. The two
  `killed_economic` decisions are **void as economic judgements**. Rows are **retained** (the
  append-only rail) and **re-keyed**: the outcome unit joins the frozen spec, so r13 candidates
  compute different `candidate_id`s and can never be confused with their pre-r13 namesakes.
- **`.data/micro_walkforward/` — retained.** Effects are percent, `econ_floor: null`, so no
  economic comparison ever ran; the verdicts (`insufficient`, and the TR-15 floor refusals) are
  unaffected in kind. New rows carry `unit`.
- **`.data/micro_graduation/` — absent. No sealed evaluations exist.** Nothing to invalidate;
  nothing ever advanced on a bad magnitude.
- **`.data/micro_snapshots/` — rebuilt.** Editing `micro_features.py` moves
  `feature_source_hash` (it hashes module source bytes), so all 18 snapshots became an honest
  cache MISS. **Verified: rebuilt feature rows are byte-identical to the pre-r13 rows**
  (`309845c6…`, sha `f2078b71…`), `params_hash` unchanged (`5d3f3094…`), `config_fingerprint`
  still `08e471b10130e1e2`. r13 changed no feature value — only the outcome layer.
- **`.data/micro_vault/`, `.data/micro_exposure_registry/` — untouched.** No outcome magnitudes.
  **No sealed vault data was consumed at any point.**

---

# Part 3 — the real-corpus re-run under r13

Run: `python -m app.research.scout --grid default`, same 18-shard exploratory corpus, 11
sessions, all 18 snapshots rebuilt first. Ledger `.data/micro_scout/ledger.jsonl`: 12 pre-r13
rows retained + 6 new r13 rows appended (nothing deleted, nothing rewritten).

| candidate | pre-r13 effect (dollars, mislabelled `effect_bps`) | r13 `effect_bps` | `floor_bps` | r13 `p_screen` | pre-r13 decision | r13 decision | changed |
|---|---|---|---|---|---|---|---|
| `cumulative_delta ≥ 0` | +0.0000268 | **−0.0191** | 1.5262 | 0.8136 | `killed_null` | `killed_null` | no |
| `cumulative_delta ≤ 0` | +0.0000236 | **+0.0203** | 1.5262 | 0.8021 | `killed_null` | `killed_null` | no |
| `failed_aggression_score ≥ 0` | — | — | 1.5262 | — | `killed_insufficient_n` | `killed_insufficient_n` | no |
| `failed_aggression_score ≤ 0` | +0.001568 | **+0.0340** | 1.5262 | 0.7141 | `killed_null` | `killed_null` | no |
| `quote_imbalance ≥ 0` | +0.004236 | **+0.1462** | 1.5262 | 0.00050 | `killed_economic` | `killed_economic` | no |
| `quote_imbalance ≤ 0` | −0.004716 | **−0.1499** | 1.5262 | 0.00050 | `killed_economic` | `killed_economic` | no |

**Zero survivors, as before. No decision changed. No survivor was manufactured.** Every r13 row
is re-keyed (`cand-e5dcfa15…` → `cand-48bc98d6…`, etc.) — no collision with any pre-r13 row.

## 16. What the re-run actually proves

**(a) The old numbers were not recoverable by rescaling.** The old/new ratio is *not* constant:
0.0014, 0.0012, 0.046, 0.029, 0.031. Dividing by each anchor's own price is not a global rescale,
so no correction factor could have rehabilitated the persisted rows. **Recomputation was
mandatory; reinterpretation was impossible.** This is the strongest justification for re-keying
rather than relabelling.

**(b) The pre-r13 estimator was incoherent, not merely mis-scaled.** `cumulative_delta ≥ 0` and
`cumulative_delta ≤ 0` split the same anchors into complementary candidate/comparator cells, so a
valid contrast MUST return near-mirror effects. Pre-r13 both read **positive**
(+0.0000268 and +0.0000236) — structurally impossible for a genuine contrast. Under r13 they read
**−0.0191 and +0.0203**, proper mirror images. The dollar pooling had destroyed the sign, not just
the scale. Nothing in the old ledger's magnitudes should be read as evidence of anything.

**(c) `p_screen` moved materially** (0.9925 → 0.8136; 0.9955 → 0.8021; 0.4563 → 0.7141) because
the statistic itself changed. `quote_imbalance` stayed at 0.00050 — the permutation floor
(1/2001), i.e. the effect is beyond every one of 2,000 block permutations either way.

**(d) The `quote_imbalance` conclusion survives, now honestly.** The corrected effect is ~34×
larger than the mislabelled figure — and still **10.4× below** the spread floor (0.146 vs 1.526
bps). The kill stands, but it now rests on a comparison that means something: a statistically
unambiguous effect (p at the permutation floor, ~2.3M vs ~1.5M observations, 11/11 sessions) whose
magnitude is an order of magnitude too small to clear the quoted-spread cost proxy.

## 17. Scientific interpretation — what may now safely be concluded

1. **The measurement layer is now trustworthy, and it was not before.** Every `*_bps` magnitude
   reaching a gate is proved to be basis points at the Scout, walk-forward and sealed stages.
2. **No conclusion of this era ever depended on the defect.** Graduation is empty, no sealed
   evaluation exists, no candidate ever advanced. The two void `killed_economic` decisions have
   been superseded by valid ones that reach the same verdict.
3. **On the exploratory corpus, none of the six reference candidates is economically
   interesting.** That is a statement about a 12-symbol-day, 11-session, 3.0-session-equivalent
   corpus — a screening result, not a finding about markets.

   **Corrected in the contract pass:** an earlier draft of this line attached the "29–83%
   tick-test inferences" caveat to all six candidates. That overgeneralized. `fallback_frac`
   measures aggressor-label quality, and only the **aggressor-derived** families read that label
   (`scout.AGGRESSOR_DERIVED_FEATURES`). So it is a material caveat for `cumulative_delta` and
   `failed_aggression_score` (F-FLOW / F-RESPONSE) — four of the six trials — and **not** for
   `quote_imbalance`, which is F-LIQUIDITY and never reads `side` at all. The `quote_imbalance`
   result (p at the permutation floor, 0.146 bps against a 1.526 bps floor) does not inherit the
   label-quality caveat; it is limited by corpus SIZE, not by aggressor inference.
4. **Nothing here is a profitability claim, and `econ_interesting` is not one either.** Clearing
   the spread proxy is necessary and very far from sufficient; profitability needs an execution
   model this era does not build (§5.5's three-concept table).

## 18. Remaining blocker (unchanged by r13 — and deliberately so)

`GET /research/desk/micro/walkforward` still refuses with **`0 < 105`**: the geometry needs
40 train + 5 embargo + 20 test + 2×20 step = 105 sessions for `WF_MIN_SUFFICIENT_FOLDS`, and the
exploratory corpus has **11**. All three pilot studies read `floor_unmet` (60 required, 11
available). 80 sealed vault symbol-days exist and were **not touched** — they are OOS reserve, not
discovery data. No geometry, floor, or threshold was relaxed to make anything run.

The bottleneck is exposed sessions: **11 of 105**. That is the next problem, and it is now safe
to attack, because growth will be measured in a unit that means something.

---

## 19. Acceptance criteria — verified

| Criterion | Evidence |
|---|---|
| Every value called bps is demonstrably basis points | `test_micro_unit_semantics.py` (31 guards), propagation tests at all three stages |
| Scout economic floor compares bps vs bps | `scout.py` → `mf.clears_economic_floor` → `require_bps_floor` |
| Walk-forward fold + pooled effects use the canonical unit | `PCT_TO_BPS` at the feed; `unit` on every fold summary |
| Sealed evaluation uses the same unit | `micro_sealed_evaluation.py:257` through the same door |
| long/short cannot silently conflict with buy/sell | disjoint vocabularies, separate validators, one adapter |
| Unknown side values fail loudly | `UnknownSideVocabularyError`, raised **before** unmeasured/truncated short-circuits |
| Price-scale invariance tests pass | 3 tests incl. 4 parametrised rescale factors |
| Economic-floor regression tests pass | 5 bps vs 2 bps → interesting; 1 bps vs 2 bps → `killed_economic` |
| Spec documents the corrected convention | r13 + §0 + §4 + §5.5 + TR-33 |
| Old evidence cannot be mistaken for new | outcome `unit` is a frozen spec field → all 6 candidates **re-keyed**; unitless floors refused |
| Real corpus recomputed | run over 18 rebuilt snapshots, 6 r13 rows appended |
| Before/after table for all six | §Part 3 |
| No sealed vault data consumed | `withheld_excluded: 80` on every grid; vault ledgers untouched |
| No statistical or sample gate weakened | §13 — every constant unchanged |
| All relevant existing tests pass | **3543 passed, 8 skipped, 0 failed** (`PYTEST_EXIT=0`); frontend `tsc --noEmit` exit 0 |
| Era invariants intact | 0 `referee_*` modules changed · 0 `Config` fields · fingerprint `08e471b10130e1e2` · `params_hash` `5d3f3094…` unchanged · rebuilt feature rows byte-identical |

**Not verified in a browser:** the one-word `/desk` header change (`Effect` → `Effect (bps)`).
It is a static label with no golden-replay or guard-test dependency, and `tsc --noEmit` passes,
but no screenshot was taken — so by the era's own T-10 rule it is `unknown`, not `passing`.

---
---

# Part 4 — r13 completion (2026-08-25): sign applied once, units proved

A review after the r13 landing found three places where r13's own semantics were not yet carried
through. All are corrected under the **same revision** — no methodology, constant, threshold, or
gate changed — so a new revision number would misrepresent a completion as a change.

## 20. Root cause A — direction was applied TWICE

r13 made the canonical outcome direction-signed at the outcome. But two downstream stages
re-derived an expected sign from `sidedness`, applying a **second** direction interpretation to an
already-signed value:

| site | pre-completion |
|---|---|
| `walkforward._pooled_sign_agreement` | `expected = "positive" if sidedness == "long" else "negative"` |
| `walkforward._opposite_direction_eligible_fold_exists` | `opposite = "negative" if sidedness == "long" else "positive"` |
| `walkforward.evaluate_survivor_rule` cond. 3 | `(pooled_effect > 0) == (expected_sign == "positive")` |
| `micro_sealed_evaluation._expected_sign` | `"positive" if sidedness == "long" else "negative"` |

**The source proves the value arrives already signed.** `desk_forward.py:42-46`: *"Every
directional return is SIGNED TO THE ROW'S OWN SIDE... a POSITIVE number means price went the way
the wall implied."* `walkforward.playbook_observations` restates it and forbids exactly what the
predicate below it did: *"already side-relative signed... **never a second, independent sign
derivation**."* The module contradicted its own documented contract.

**Consequence:** a genuinely successful SHORT candidate arrives POSITIVE, was compared against an
expected "negative", and would have been refused as wrong-direction — at both the walk-forward and
sealed stages. **Latent, never fired:** every registered candidate and sequence to date is `long`
or unsided, where the two readings coincide.

**Scout was already correct** (`scout.py:1285` requires `effect_bps > 0` regardless of
`sidedness`) — which is why the inconsistency mattered: two stages of one pipeline disagreed.

**The spec needed no rule change.** §6.6 condition 3 says the effect must lie *"in the registered
direction"*; §8.1 condition 2 says the same. Neither says "negative if short". In canonical signed
space, "in the registered direction" **is** positive. Only the operationalization was wrong.

## 21. Root cause B — legacy walk-forward rows could be read as bps

The persisted ledger holds fold 3 = `0.019176` and fold 4 = `-0.007731`, both **percent**, with no
`unit` key. `list_walkforward_sequences` served those rows verbatim and `decay_view` copied the
magnitude while dropping any unit — and the r13 commit had labelled the UI column
**`Effect (bps)`**. That combination would have displayed 0.019 percent (≈1.9 bps) as 0.019 bps: a
100× mislabel of persisted evidence, introduced by the r13 commit itself.

**Fix — disclose, never convert.** A row with no `unit` key predates the contract and is served
with the explicit historical token `legacy_percent` (deliberately distinct from both `percent` and
`return_bps`: it states the unit AND that it was established from the pre-r13 convention rather
than declared by the writer). The stored magnitude is served verbatim. The ledger on disk is
untouched. `decay_view` now carries the unit per row, and the UI prints each row's own unit in its
own column instead of a hardcoded header. A sequence whose sufficient folds carry a non-canonical
unit **refuses a verdict** rather than pooling percent into basis points.

## 22. Root cause C — the effect unit was trusted, not proved

r13 proved the *floor's* unit (`require_bps_floor`) but took the *effect* on trust because a
variable was named `effect_bps`. A name is not a proof.

`require_return_bps_effect(value, unit)` now gates: every economic-floor comparison (both sides),
every pooled fold effect, every fold observation before averaging (missing, unknown, legacy **and
mixed** units all refuse), and every sealed observation at its own boundary — before a verdict is
derived and before the single shot is consumed.

## 23. Canonical sign convention (stated once, in spec §0)

`raw market return → direction signing (exactly one application) → canonical return_bps`

| raw move | direction | canonical `return_bps` | reading |
|---|---|---|---|
| up | `long` | **positive** | thesis worked |
| down | `long` | **negative** | thesis failed |
| down | `short` | **positive** | thesis worked |
| up | `short` | **negative** | thesis failed |

No downstream layer re-inverts on `long` vs `short`. `sidedness` stays recorded, served and
vocabulary-checked — it is never a second sign derivation.

## 24. Side validation — every public scientific boundary

| boundary | protection |
|---|---|
| `scout.register_and_screen_candidate` | validated first, before corpus read, spread floor, spec freeze, ledger write |
| `scout.build_candidate_spec_fields` | validated before the direction can be frozen into a spec |
| `scout.extract_anchors` | validated before any corpus or outcome read |
| `scout.screen_candidate` | validated before any screening arithmetic |
| `walkforward.register_mode_b_spec` | validated at registration |
| `walkforward.evaluate_survivor_rule` | validated before the predicate runs |
| `walkforward.sequence_verdict` | protected via its delegation to `evaluate_survivor_rule` — its refusal paths perform no scientific computation, so there is nothing to protect there |
| `micro_sealed_evaluation._expected_sign` | validated on every sealed verdict |
| `micro_features.mid_outcome` / `last_trade_outcome` | validated eagerly, before unmeasured/truncated short-circuits |

`None` remains legal everywhere (a genuine unsided exploratory candidate). `buy`, `sell`, `SHORT`,
`Long`, `positive`, `negative`, `flat`, `""` all raise.

**Ten test fixtures registered `sidedness="buy"`** and expected a normal result. That contract was
invalid after r13 and is corrected to `"long"`, not preserved.

## 25. Unit validation — where every magnitude is proved

| stage | what is proved | how |
|---|---|---|
| Scout economic gate | effect **and** floor | `clears_economic_floor(effect, mf.OUTCOME_UNIT, econ_floor)` |
| Walk-forward observation feed | every observation before averaging | `require_canonical_observation_units` inside `summarize_fold_observations` — missing, unknown, legacy and **mixed** all refuse |
| Walk-forward pooled effect | every eligible fold before pooling | `require_return_bps_effect(f["effect"], f["unit"])` |
| Walk-forward condition 3 | pooled effect **and** floor | `clears_economic_floor(pooled_effect, WF_OBSERVATION_UNIT, econ_floor)` |
| Walk-forward condition 4 | each opposing fold's magnitude | `require_return_bps_effect` before the floor comparison |
| Sealed evaluation input | caller-supplied observations, at its own boundary | `wf.require_canonical_observation_units(observations)` — before the verdict, before the single shot is consumed |
| Sealed condition 3 | recomputed effect **and** floor | `clears_economic_floor(summary["effect"], summary["unit"], econ_floor)` |
| Sequence verdict | every sufficient fold's unit | refuses the verdict outright if any is non-canonical |

## 26. Browser verification (acceptance criterion 22)

A scoped rig (`scripts/seed_micro_walkforward_unit_disclosure_fixture.py`, fixture root outside the
real store) seeds ONE sequence carrying BOTH conventions, then serves it on an isolated backend
(`:8399`) and frontend (`:3399`). Screenshot:
`reports/browser-qa/r13-completion-walkforward-unit-disclosure.png`.

The `/desk` Walk-Forward fold table renders:

| Fold | Status | Effect | Unit |
|---|---|---|---|
| 0 | sufficient | `0.019176079727258294` | `legacy_percent` |
| 1 | sufficient | `25` | `return_bps` |

The column header is `Effect` + `Unit` — it names no unit itself, because no single header can be
truthful for both rows. The legacy magnitude is displayed **verbatim**, never ×100. The sequence
verdict reads `refused — 2 < 3 sufficient folds`. No vault shard was consumed; the real store was
not written to; the operator's own `:8301` backend was left running untouched.

## 27. Real corpus — no re-run required, and proved rather than assumed

The mandate's own condition is *"re-run only if code changes touch Scout scientific semantics."*
They do not, and that is demonstrated, not asserted:

- **The frozen candidate identity is unchanged.** Re-deriving all six specs from the persisted
  ledger rows reproduces byte-identical `candidate_id`, `spec_hash` and `econ_floor` for every one.
  Nothing entering a candidate's scientific identity moved.
- **The Scout diff is exactly two things:** four `validate_candidate_direction(sidedness)` calls
  (which pass for `sidedness: None`, what all six candidates carry), and a unit argument added to
  the same `clears_economic_floor` comparison — same magnitudes, same `>=`, plus an assertion that
  passes. `_observed_effect`, anchor extraction, the block-permutation null and the kill ladder are
  untouched.

A re-run would append six rows with identical ids and identical decisions: evaluations, not
information. **The six r13 decisions therefore stand unchanged** — `killed_null` ×3,
`killed_insufficient_n` ×1, `killed_economic` ×2, zero survivors.

An interrupted re-run had already completed the snapshot rebuild before it was stopped; all 18
snapshots verify fresh against the current `feature_source_hash`, and the ledger is unchanged at 18
rows (12 pre-r13 + 6 r13) — the kill landed before any candidate was screened, so no partial
scientific row exists.

## 28. Verification

| check | result |
|---|---|
| Full backend suite | **3583 passed, 8 skipped, 0 failed** (`PYTEST_EXIT=0`) |
| Frontend `tsc --noEmit` | exit 0 |
| Browser (legacy + r13 fixtures) | screenshot on record, §26 |
| Frozen candidate specs | byte-identical for all six |
| Snapshots | 18/18 fresh; feature rows unaffected by this change |

## 29. Invariants — nothing weakened

`ECON_FLOOR_SPREAD_MULTIPLE` 1.0 · `SCOUT_SCREEN_ALPHA` 0.05 · `SCOUT_BLOCK_PERMUTATIONS` 2000 ·
`SCOUT_MIN_SESSION_CLUSTERS` 2 · `SCOUT_MIN_OBSERVATIONS_PER_CELL` 5 ·
`SCOUT_MAX_TOP1_CONCENTRATION` 0.8 · `SCOUT_MAX_VARIANTS_PER_FAMILY` 24 ·
`WF_MIN_SUFFICIENT_FOLDS` 3 · fold geometry 40/5/20/20 · embargo 5 · `SEALED_MIN_OBSERVATIONS` 30 ·
`config_fingerprint` `08e471b10130e1e2` · zero `Config` fields · zero `referee_*` modules changed ·
zero PnL logic changed · no feature meaning changed · no candidate family or pilot study added ·
no append-only ledger rewritten · no pre-r13 evidence deleted · **no sealed vault data consumed**.

The 105-session walk-forward requirement is untouched: `GET .../walkforward` still refuses
`0 < 105`, and all three pilot studies still read `floor_unmet` (60 required, 11 available).

## 30. Two defects of my own, found and corrected

1. **`Effect (bps)` column header** (introduced by the r13 commit) would have displayed the
   persisted `0.019176` **percent** as bps — a 100× mislabel of real evidence. Replaced by a
   per-row served unit.
2. **TR-33 collision**: r12's vault ruling already owned TR-33; the r13 commit added a second
   TR-33. Renumbered to TR-34, with TR-35 added for the completion traps.

---
---

# Part 5 — r13 contract pass (2026-08-25): fail-closed boundaries + direction freeze

Four remaining gaps. Three were real as described; one was **partly disproved** and only its
genuine half was fixed. No constant, threshold, geometry or gate changed.

## 31. Root cause A — Mode A fitted before it validated

`register_mode_a_origin` never called `validate_candidate_direction`, and `sidedness` is one of
`spec_fields` — so an invalid vocabulary would be hashed into `spec_hash` and written to a
permanent ledger row. Worse, `fit_training_quantile([o["value"] for o in train_observations], q)`
consumed the training values before any unit check; only the TEST observations were validated, and
only at the end via `summarize_fold_observations`.

**Call order, before → after:**

| before | after |
|---|---|
| `parse_fitting_rule` | **`validate_candidate_direction(sidedness)`** |
| `train_observations_provider()` | `parse_fitting_rule` |
| `fit_training_quantile(...)` | `train_observations_provider()` |
| freeze `spec_hash` | **`require_canonical_observation_units(train)`** |
| `test_observations_provider()` | `fit_training_quantile(...)` |
| `summarize_fold_observations(test)` | freeze `spec_hash` |
| | `test_observations_provider()` |
| | **`require_canonical_observation_units(test)`** |
| | `summarize_fold_observations(test)` |

The freeze-order guarantee is untouched: both new checks sit strictly inside the training half, so
train → fit → freeze → reveal still holds (proved by an ordering test).

## 32. Root cause B — the sealed evaluator failed too late

Invalid direction and non-canonical units *did* fail — but at `:425` and `:419`, after
`build_vault_state` (`:375`) and **`accessor.read_snapshot_rows` (`:406`)** had already read
protected shard data. Both facts are knowable from the call arguments alone.

**Validated now, before any shard read** (in order): `family_root_id` present → spec completeness
(`spec_hash`/`sidedness`/`registered_at`) → no caller `floors` override → recorded rule hash matches
→ **`validate_candidate_direction(sidedness)`** → **`require_canonical_observation_units(observations)`**
→ *then* `build_vault_state` → assignment/exposure/family binding → `read_snapshot_rows`.

No vault identity, rule-hash, assignment or exposure check was weakened; all still run on every
call that gets past that point. Proved with a spy accessor asserting `reads == []`.

## 33. Root cause C — Scout asserted its own unit provenance

Anchors carried `outcome_bps` with **no unit**, and `screen_candidate` passed `mf.OUTCOME_UNIT` to
the gate as a literal — so the provenance existed only because the consumer claimed it, and the
key's *name* proved nothing about its contents.

**Anchor schema now** (all four extraction paths):

```python
{"dataset_id", "symbol", "session_date", "anchor_at", "trade_index",
 "feature_value", "outcome_bps": outcome["mid"]["return_bps"],
 "outcome_unit": outcome["mid"]["unit"],      # read OFF the outcome row
 "tod_bucket", "fallback_frac"}
```

`require_canonical_anchor_units(anchors)` runs in `screen_candidate` before any pooling,
permutation or gate; the economic gate then reads `anchors[0]["outcome_unit"]` — the proved value —
never a module literal. Missing, unknown, percent, legacy and MIXED all refuse.

## 34. Root cause D — direction freeze: two thirds of this concern was already handled

**Disproved, with evidence — no fix made:**

- *Sealed credit for an unsided candidate.* Already impossible:
  `if not (spec_hash and sidedness and spec_registered_at): raise` — `sidedness=None` is falsy and
  the sealed evaluation is refused for spec incompleteness.
- *Post-hoc direction selection earning OOS credit.* Already impossible: `sidedness` is part of the
  frozen `spec_fields`, so changing it re-keys `spec_hash` and stamps a new `registered_at`; then
  `classify_evidence_class` returns `historical_exposed_diagnostic` iff any window in the fold was
  exposed before that instant. A direction chosen after seeing the window yields diagnostic
  evidence, which earns zero graduation credit. Proved against the **real** exposure registry, not
  a fabricated OOS.

**Real, and fixed:** `sequence_verdict` granted `walkforward_survivor` to a sequence carrying
`sidedness=None` (verified empirically before the fix). It now refuses. That is the correct and
only place — `micro_graduation.evaluate_walkforward_survivor_transition` delegates the entire
predicate to `sequence_verdict` and converts a refusal into a refused transition, so it is the
single door to survivor credit.

**Ordering note:** the gate is checked *after* the sufficient-folds floor. With zero ledgered folds
the sidedness read off those rows is *unknown*, not "unsided", and `0 < 3 sufficient folds` is the
honest answer there.

**The contract:** `exposed Scout diagnostic → choose long|short from discovery evidence only →
freeze in the registered spec → ONLY THEN reveal/evaluate OOS windows → sealed after that`.
Choosing the direction from Scout's exposed sign **is allowed** — Scout is discovery evidence — and
Scout itself stays legally unsided.

## 35. Root cause E — an overgeneralized label-quality caveat (documentation only)

The **code was already family-aware**: `scout.AGGRESSOR_DERIVED_FEATURES` carries the comment
*"F-FLOW and F-RESPONSE are derived from the engine's aggressor SIDE classification; F-LIQUIDITY
(quote imbalance, microprice, spread change) is not — it never reads `side` at all."* No formula
was touched.

What overgeneralized was my own wording — the readiness `label_quality.note` and §17 of this
report attached the 29–83% fallback caveat to the whole corpus and all six candidates.

| aggressor-derived (caveat applies) | not aggressor-derived (caveat does NOT apply) |
|---|---|
| F-FLOW: `cumulative_delta`, `rolling_imbalance_*`, `same_side_run_length`, `volume_burst_*`, `divergence_at_level_bearish` | F-LIQUIDITY: `quote_imbalance`, `microprice`, `spread_change_*` |
| F-RESPONSE: `failed_aggression_score`, `absorption_score`, `impact_efficiency_*`, `efficiency_trend_*` | |

So of the six real trials, the caveat bears on four (`cumulative_delta` ×2,
`failed_aggression_score` ×2) and **not** on `quote_imbalance` ×2. The `quote_imbalance` result is
limited by corpus **size**, not by aggressor inference. Readiness now serves `affected_families` /
`unaffected_families` beside the note. The disclosure was made narrower and more accurate — never
removed or weakened.

## 36. Real corpus — no re-run, proved again

All six frozen candidate specs still recompute **byte-identical** `candidate_id` and `spec_hash`.
The production Scout numerical path for valid canonical anchors is unchanged: anchors gained a unit
FIELD, the gate reads that field instead of a literal of the same value, and the direction
validators pass for `sidedness: None`. `_observed_effect`, the block-permutation null and the kill
ladder are untouched. The ledger stands at 18 rows; the six decisions are unchanged
(3× `killed_null`, 1× `killed_insufficient_n`, 2× `killed_economic`, zero survivors). No redundant
rows appended.

## 37. Verification

Full backend suite **3613 passed / 8 skipped / 0 failed** (`PYTEST_EXIT=0`); frontend
`tsc --noEmit` exit 0. Invariants: no threshold, alpha, permutation count, concentration ceiling,
sample floor, floor multiple, fold geometry, embargo, variant cap, feature formula, aggressor
classifier, Referee module or PnL logic changed; `config_fingerprint` `08e471b10130e1e2`; exposure
registry semantics unchanged; no append-only ledger rewritten; no sealed vault data consumed.
