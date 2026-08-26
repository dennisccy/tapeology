# r14.3 — Study 2's decision belongs to the Scout rail, and the one real diagnostic

**Branch** `goal/rapid-microscope` · **base HEAD** `7245fbba` · **spec revision** r14.3
· `config_fingerprint` `08e471b10130e1e2` (frozen, untouched)

No data was recorded, released, probed or provisioned. No sealed shard was touched. No Mode B rule
was frozen. One real Scout row was appended — the Study 2 diagnostic this task exists to perform.

---

## ROOT CAUSE

Both concerns in the brief are confirmed in code, at
`apps/backend/app/research/micro_study2_diagnostic.py` as of `7245fbba`:

| Line | What it did |
|------|-------------|
| 63 | `MIN_ANCHORS_FOR_AN_ESTIMATE = 30`, lifted from `walkforward.WF_FOLD_MIN_OBSERVATIONS` |
| 231 | `if len(usable) < 30 or fired["n_sessions"] == 0: INSUFFICIENT` |
| 242 | `separation` computed… |
| 244–258 | …and never read. The verdict branched on `effect`, the **fired cell's own raw mean**. |

The single root cause behind both: **Study 2 was given a decision rail of its own** when the project
already had exactly one frozen discovery rail, and every part of the new one was weaker than the part
it shadowed.

## WHY THE OLD DIAGNOSTIC COULD FALSELY PROMOTE

**Two independent routes, and the second is the dangerous one.**

*Route 1 — a floor that measured the wrong population.* The 30-anchor floor counted ALL usable
anchors, then let the decision through on `fired["n_sessions"] == 0` being false. Thirty usable
anchors of which exactly one fired, in one session, cleared both. One observation decided.

*Route 2 — market drift read as mechanism.* Judging the fired cell alone cannot distinguish "this
mechanism is bearish" from "everything was falling". The brief's own counterexample, now a test: a
fired cell at −2 bps against a comparator at −8 bps is **+6 bps worse** than the alternative, and the
old rail called it PROMISING because −2 < 0.

**The sharpest evidence is r14.2's own "PROMISING" fixture.** It was forty anchors, every one of them
firing, **with no comparator cell in existence** — `n_comparator == 0` — scored PROMISING because
40 ≥ 30 and the fired mean was −9 bps. There was nothing to compare −9 against. That fixture is
retained as a test, now asserting `INSUFFICIENT`.

## SCOUT RAIL REUSE

The decision is now read off `scout.screen_candidate` over the same anchors. Nothing was duplicated:
no second sample floor, p-value, null, concentration rule, fragility rule or economic gate exists in
this module. `MIN_ANCHORS_FOR_AN_ESTIMATE` was deleted outright, and a test pins its absence.

```
killed_insufficient_n   -> INSUFFICIENT     (we could not look)
any other kill          -> KILLED           (we looked and it failed; the list is open by design)
survive + effect_bps<0  -> PROMISING_FOR_MODE_B_FREEZE, proposed_direction = short
survive + effect_bps>=0 -> KILLED           (Card 9.1 is bearish; contradicted by its own evidence)
```

Two deliberate asymmetries. **Every path out of a non-`survive` decision leads to INSUFFICIENT or
KILLED** — PROMISING is reachable only through Scout's full ladder and then only with the right
sign. And **`short` is the only direction this module can express**: a surviving positive effect is
killed, never re-read as a long hypothesis, because reversing a stated mechanism after seeing
discovery data is the post-hoc freedom the funnel exists to remove.

The economic gate is the spec's own `econ_floor` object (family median spread × `ECON_FLOOR_SPREAD_MULTIPLE`),
passed to `screen_candidate`. The free-floating `econ_floor_bps` parameter is gone.

## CONTINUOUS-FIRST INVARIANT

`continuous_report` is computed first, from the same anchors, and carries **no verdict field at all**
— a test asserts `outcome`, `proposed_direction` and `scout_decision` are all unreachable from it.
Another asserts the continuous half is byte-identical across a surviving and a killed screen of the
same anchors.

Renames that matter: `conditional_outcome` → `conditional_raw_return`, and its magnitude
`effect_bps` → `raw_return_bps`. `effect_bps` is Scout's decision statistic; a one-cell raw mean
under the same field name is exactly how drift gets mistaken for a mechanism. The report exposes
`mechanism_raw_return_bps`, `comparator_raw_return_bps` and `descriptive_separation_bps`, each
labelled descriptive in-band.

`descriptive_separation_bps` is retained but is **not** the decision statistic: it differences two
cell means over *different session sets*, whereas Scout's `effect_bps` is the mean of per-session
paired deltas over sessions carrying *both* cells. They can disagree in sign; when they do, Scout is
right.

## TESTS

`tests/test_micro_r14_3_study2_scout_rail.py` — **21 tests**, covering the brief's A–I in full.

Two are worth singling out:

**Case D (concentration)** initially proved nothing — the fixture died at `killed_null` before ever
reaching the concentration gate. It now asserts the null gate is *cleared* first.

**Case F (fragility)** took real work, and the reason is a genuine property of the rail: most
"fragile-looking" shapes are caught by the block-permutation null first, because an outlier large
enough to flip the sign also widens that session's own rotated null. Reaching the fragility gate
requires a session whose candidate cell is a small *contiguous* block inside a large session, so
rotation moves it onto comparator outcomes and the null stays tight while the observed delta stays
extreme. The test now asserts all three earlier gates passed (p < α, concentration ≤ ceiling,
`econ_interesting`) before `killed_fragile`.

Four r14.2 tests that pinned the retired rail were replaced by a documented pointer block plus the
re-targeted no-comparator test described above.

### The performance work the real run required, and its proof

The first real run was killed at **90 minutes** with no result. Profiling the corpus found the cause:
**5,614 touch pairs**, 96% of them inside AMZN (3,325) and AMD (2,094), each a ~280k-row dataset —
and `_extract_divergence_anchors` rescanned the whole dataset **four times per pair**
(`feature_row_at_trigger` rebuilding the trade-row list, the price-history filter, the
baseline-volume windows, and a linear `trade_rows.index()`).

Four hoists, all cost-only: `anchor_at` is ascending on all 18 real datasets (verified), so each
scan became a binary-searched contiguous slice. Summation **order** is preserved deliberately — a
prefix-sum table would be faster still but not bit-identical, and `divergence_delta_threshold` feeds
a `<=` comparison in Card 9.1, so the result must be bit-identical rather than close.
`trade_rows.index()` is replaced by the already-known bisect position, valid because `trade_index` is
strictly increasing on every dataset (verified), so no two rows compare equal.

**Proof, on real data:**

| dataset | pairs | sampled | verified anchors | new (all pairs) | old (sample only) | mismatches |
|---|---|---|---|---|---|---|
| AMZN | 3,325 | 240 | 239 | 68.1 s | 314.2 s | **0** |
| GOOGL | 195 | **195 (all)** | 195 | 7.7 s | 168.9 s | **0** |
| AMD | 2,094 | 240 | 240 | 42.0 s | 278.9 s | **0** |

**674 anchors verified byte-identical, 0 mismatches**, GOOGL exhaustively. The r14.2 arithmetic was
transcribed verbatim as the oracle and sampled at an even stride across each whole session.

**Stated honestly:** this is 12% of pairs, not 100%. The full old-vs-new comparison was started and
abandoned after 30 minutes — it re-runs the very code path that could not finish in 90 minutes. The
314 s for 240 AMZN pairs extrapolates to ~73 minutes for that one dataset, which is exactly the
original timeout. Sampling plus the two verified structural invariants is the proof that was
achievable; a reader wanting exhaustive coverage should run `scratchpad/equiv.py` unattended.

## FULL SUITE

**3,747 passed · 8 skipped · 0 failed** (3,755 collected), run twice: once before the performance
work and once after, with **identical counts** — the optimization changed no test outcome.
Delta from r14.2's 3,729 passing is +21 new − 3 retired from the r14.2 file = net +18.

**Frontend `tsc --noEmit`: exit 0.**

## REAL LEDGER STATE BEFORE RUN

Verified immediately before the commit, and again after:

| ledger | before | after |
|---|---|---|
| Scout | 18 rows, **0 divergence rows** | 19 rows, **1** divergence row |
| Vault shard | 21, all `sealed` | 21, all `sealed` |
| Vault release plan | 0 | 0 |
| Exposure registry | 174, all `record_kind: exposure` | 174 |
| Walk-forward | 7 (1 spec, 5 results, 1 `mode_b_spec`) | 7 |

All chains verify. The 90-minute killed run wrote **nothing** — the ledger append is the last step.

**Preconditions, all fail-closed and all verified:** no pre-existing Study 2 row · 18 snapshot metas,
**0 stale** under the live `feature_source_hash` · 98 datasets registered, **18 in manifest, 80
withheld excluded** · 21 sealed rows, **0 sealed ids in the manifest** · 11 session dates, **0 not
marked exposed** under `tick_legacy_symbol_days_v1` · `historical_exposed_diagnostic`.

---

## REAL STUDY 2 CONTINUOUS RESULT

**Corpus:** 18 datasets · 11 session dates · 11 symbols · 80 withheld excluded · 0 sealed ·
`historical_exposed_diagnostic`.

**But the anchors come from only 3 of those 18 datasets.** Fifteen have **zero band touches**, so
Study 2's paired-touch mechanism is undefined on them. The evidence is AMZN 2026-06-26, AMD
2026-07-06 and GOOGL 2026-07-13.

| | |
|---|---|
| paired-touch anchors | **5,613** |
| defined / undefined coordinates | **5,613 / 0** |
| session dates *with anchors* | **3** (of 11 in the corpus) |
| symbols *with anchors* | **3** (of 11) |

`price_extension_bps` — min −44.22 · p10 0.0 · median **0.0** · p90 0.0 · max 53.47 · mean 0.088
`delta_weakening_multiple` — min −33.77 · p10 −0.045 · median **0.0** · p90 0.051 · max 8.91 · mean −0.036

**Quadrants:** `both` **14** · `extension_only` 199 · `weakening_only` 52 · `neither` **5,348** ·
`undefined` 0.

Card 9.1 fires on **14 of 5,613 anchors — 0.25%**. Both coordinate medians are exactly 0.0: at the
typical consecutive touch of the same band, price does not extend and cumulative delta does not
weaken. The mechanism is rare in this tape, and that is the single most important number here.

## REAL STUDY 2 SCOUT RESULT

**Cells:** `n_candidate` **14** · `n_comparator` **5,599** · `n_sessions_total` 3 ·
`n_usable_sessions` **2**

The frozen sufficiency floors were **met, not bypassed**: 14 ≥ 5, 5,599 ≥ 5, 2 ≥ 2. Scout actually
computed the screen.

| statistic | value |
|---|---|
| **`effect_bps` (the decision statistic)** | **+0.4872** |
| `p_screen` | **0.3663** (α = 0.05) |
| concentration | top1 session 0.643 · top1 symbol 0.643 |
| `econ_floor` | 1.5262 bps (family median spread × 1.0) |
| `econ_interesting` | **False** |
| fragility | not reached — killed earlier |
| **Scout decision** | **`killed_null`** |

Per-session deltas: `2026-06-26` **−0.397**, `2026-07-06` **+1.372`. **The two usable sessions
disagree in sign.** With only two clusters and opposite signs, p = 0.37 is the honest answer.

**Descriptive only:** mechanism raw return **+0.617 bps** · comparator raw return **+0.061 bps** ·
descriptive separation **+0.556 bps**.

Note the descriptive and decision statistics agree here, and both point the wrong way: the fired
cell's own raw return is **positive**, for an explicitly bearish mechanism. This candidate had three
independent ways to die and took the first one.

## FINAL OUTCOME

# KILLED

`proposed_direction`: **None**. No Mode B rule was frozen, and none should be.

Study 2 dies cheaply, having spent no fresh evidence. Three independent reasons, any one sufficient:

1. **`killed_null`** — p = 0.37 against α = 0.05. The two usable sessions disagree in sign.
2. **Wrong direction** — `effect_bps` is **+0.49**, and the fired cell's own raw return is **+0.62**.
   Card 9.1 predicts bearish. Even had it been significant, the surviving-positive branch kills it.
3. **Economically negligible** — |+0.49| is well under the 1.53 bps floor; `econ_interesting: False`.

**No gate was lowered or bypassed to reach this.** All three of Scout's frozen sufficiency floors
were cleared on real data; the candidate was screened and failed on the merits.

## NEXT OWNER DECISION

**Do not record an OOS campaign for Study 2.** That was the entire purpose of running this
diagnostic first, and it cost nothing but compute — no storage, no retention risk, no released
member, no burned window.

Study 2 was the **only** pilot classified `FULL_MECHANISM_READY`. Studies 1 and 3 remain
`PARKED_PENDING_OWNER_SPEC` and were not touched. So all three pilots are now closed to recording,
and the era has **no candidate that justifies the expensive path**.

Three things the owner should weigh, and only the owner can:

**The corpus, not just the candidate, may be the limit.** Fifteen of eighteen datasets produced zero
band touches. Two usable session clusters is the bare minimum the screen accepts. A `killed_null` on
n=2 clusters is a weak refutation of the mechanism even though it is a correct refusal — it says
*this tape cannot support the claim*, not *the claim is false*. What it does establish is that the
**exposed legacy corpus cannot answer Study 2**, which is a fact about the evidence available today.

**The sign, though, is not a sample-size problem.** Both the decision statistic and the raw cell mean
are positive for a mechanism predicted to be bearish. That is a substantive strike against Card 9.1
as stated, independent of power.

**A larger corpus would be a new question, not a retry.** Re-running Study 2 on fresh tape after
seeing this result is exactly the post-hoc freedom the funnel forbids — a new campaign needs a Mode B
rule frozen *before* the evidence exists, and freezing a *short* rule now would be freezing a
direction this diagnostic just contradicted.

**Nothing further was done.** Per the brief: no Mode B freeze, no retention probe, no storage, no
universe, no corpus, no release plan, no release, no recording, no sealed shard.
