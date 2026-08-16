# The Referee — canonical statistical specification (Era 6)

> **This document is the rulebook.** Every constant, eligibility rule, null definition, test
> procedure, weight, verdict rule, and oracle design for Era 6 is fixed HERE, before the code
> that implements it. Developers implement from this spec verbatim; a developer who finds a
> rule ambiguous or unimplementable DROPS the procedure from the iteration and surfaces it for
> an owner ruling — never improvises. A change to anything in this document is a **named
> revision** that re-keys future referee results beside old ones (new spec ids / parameter
> hashes), never an edit of recorded meaning. Nothing here is ever tuned from outcomes.
>
> Authored 2026-08-14 at the opening of Era 6, from the approved era plan (statistical design
> red-team-reviewed; the three blocker fixes — the single confirmatory checkpoint, the
> within-session label permutation as primary, and remaining-time-matched eligibility — are
> incorporated as law). Companion constitution: [`docs/goal.md`](goal.md).

---

## 0. Shared conventions

- **Units.** Directional measures are the rail's `return_pct` values: side-signed percent
  returns (long = raw, short = negated by `sign`), exactly as `desk_forward._measure_from`
  serves them. MDD measures are unsigned, direction-named, clamped ≤ 0, never sign-multiplied;
  the side→MDD binding is `long → mdd_long_*`, `short → mdd_short_*` (the rail's documented
  convention). These statements live ONCE in the observation contract
  (`referee_evidence.py`); adapters may not restate or vary them.
- **Sessions.** A Playbook cluster is a trading `session_date` (the record's own
  `"YYYY-MM-DD"` field). A strategy cluster is a registered dataset id. Clusters are never
  cross-applied between families.
- **Time of day.** ToD buckets are Card 6.5's, converted epoch → America/New_York with DST
  (trap T1): `open` 09:30–10:30, `mid` 10:30–15:00, `close` 15:00–16:00. Bucket membership is
  decided by the occurrence's trigger epoch (signals) or anchor bar epoch (nulls).
- **Determinism.** Every random draw uses `random.Random(stream)` with the pinned stream
  recipe (§1) and the hand-coded partial Fisher–Yates draw discipline (`_draw_anchor_indices`
  import or its exact idiom) — never `random.sample`, never a global RNG, never wall-clock.
  Persisted aggregate numbers use `math.fsum`-class stdlib accumulation, not
  platform/version-sensitive vectorized reductions. Identical inputs ⇒ byte-identical
  outputs, forever.
- **Read-side law.** Nothing in this spec writes to, re-keys, backfills, or reinterprets any
  existing record. All referee outputs are new append-only records or pure read-side folds.

## 1. Pre-registered constants (module constants in `referee_*.py`; NEVER `Config` fields)

| Constant | Value | Meaning |
|---|---|---|
| `REFEREE_SEED` | `271828` | Root seed for every referee stream (distinct from the rail's 1729; namespaced streams make collision impossible, distinctness is hygiene) |
| `REFEREE_STREAM_RECIPE` | `f"{REFEREE_SEED}:{hypothesis_id}:{purpose}[:{session_date}[:{i}]]"` | The only stream constructor; `purpose` ∈ `{"null-draw","perm","flip","boot-occ","boot-cluster"}` |
| `REFEREE_B` | `10_000` | Randomization/bootstrap draw count (confirmatory) |
| `REFEREE_ENUMERATION_THRESHOLD` | `8_192` | Full enumeration when the randomization space is ≤ this; else `REFEREE_B` seeded draws |
| `REFEREE_CI_LEVEL` | `0.95` | Percentile bootstrap CI level (both clustering levels) |
| `REFEREE_DEFAULT_Q` | `0.10` | Default BH q; each family fixes its own q at registration and never after |
| `REFEREE_MIN_SESSIONS` | `12` | Minimum INFORMATIVE post-boundary sessions for a confirmatory evaluation |
| `REFEREE_MIN_OCCURRENCES` | `12` | Minimum eligible post-boundary occurrences (candidate group) |
| `REFEREE_MIN_CLUSTERS_FOR_CI` | `8` | Below this cluster count the clustered CI serves `insufficient_sample`, never a fabricated interval |
| `REFEREE_NULL_ANCHORS_PER_OCCURRENCE` | `4` | K seeded null anchors per eligible occurrence |
| `REFEREE_TOD_BUCKETS` | `(("open","09:30","10:30"),("mid","10:30","15:00"),("close","15:00","16:00"))` ET | Card 6.5's buckets, verbatim |
| `REFEREE_SESSION_COMPLETE_ET` | `"15:55"` | A record is a completed-session record for a symbol iff that symbol's finest measurement series reaches a bar whose epoch ≥ this ET time on the session date |
| `REFEREE_ORACLE_B` | `2_000` | Draw count inside oracle simulations (size/power estimation) |
| `REFEREE_ORACLE_REPLICATIONS` | `400` | Simulated datasets per oracle case |
| `REFEREE_ORACLE_BUDGET_SECONDS` | `120` | Hard runtime budget for the oracle suite (the `dense_replay_time_budget_seconds` precedent); a slower suite is a defect |
| `REFEREE_ORACLE_SIZE_TOLERANCE` | `0.5·α` … `1.5·α` empirical-rejection band at α = 0.05 | The calibration acceptance band (binomial noise at 400 replications is accounted for in the oracle tests' own math) |
| `REFEREE_GATE_VERSION` | `"referee-gate-v1"` | The gate basis pinned into certificates and adjudication snapshots |
| Null-spec ids | `"referee-null-tod-v1"`, `"referee-null-context-v1"` | §4; each id's signature hashes its full parameter blob |
| Test-spec id | `"referee-test-perm-v1"` | §3; hashes the test's full parameter blob (weights, sidedness handling, enumeration rule, p convention) |

Every constant above is read at call time by `referee_parameters()`, embedded verbatim in
every referee record, and hashed into that record's identity. A monkeypatched constant must
move the parameters AND the identity (counter-tested). Floors reuse philosophy: these are new
KINDS of floors (sessions/clusters), minted once here; the existing `pnl_min_sample_size`-class
floors keep their own owners.

## 2. The observation contract (implemented once, in `referee_evidence.py`)

```
{
  evidence_family: "playbook_occurrence" | "strategy_trade",
  observation_id:  str,          # pure function of (source_record_id, signal index / trade index)
  symbol:          str,
  session_date:    "YYYY-MM-DD", # playbook: the record's field; strategy: ET date of entry instant
  anchor_ts:       str,          # ISO-8601 UTC: trigger ts (playbook) / entry instant (strategy)
  side:            "long"|"short",
  measure_key:     str,          # one of the rail's 15 keys (playbook) / "net_r" (strategy)
  value:           float,        # units per §0
  cluster_key:     str,          # session_date (playbook) / dataset id (strategy)
  provenance: {
    detector_basis:            str,   # sha256(canonical(record.parameters))[:16]  (playbook)
    config_fingerprint:        str,
    context_algorithm_version: str|None,  # "playbook-band-context-v3" when a context predicate is involved
    source_record_id:          str,
    basis_caveats:             [str], # e.g. the Card-6.4 forming-bar caveat (strategy family)
  },
}
```

**Playbook pooling/dedup (the identity that survives daily top-ups):** observations pool at
`(detector_basis, config_fingerprint)`; for each `session_date`, exactly ONE record
contributes — the newest by `(recorded_at, id)` among records matching the pooled basis. A
genuine detector revision moves `detector_basis` and honestly splits the pool. Coverage
honesty: each pooled record carries its per-symbol coverage; when a newest record covers
fewer symbols than a superseded one for the same date, a served disclosure names it.

**`provenance.detector_basis` is `None` for every strategy-family observation, by design.** A
strategy trade has no detector: `detector_basis` is populated only for
`evidence_family: "playbook_occurrence"` (the pooling identity above) and is honestly `None` on
every `strategy_trade` observation — the same "`None` when inapplicable" convention
`context_algorithm_version` already uses. Standing for this era per the assumption ledger
(`state/assumptions.md`, iter-2/iter-3): a documentation clarification of the contract as
implemented, not a new field or a redefinition of any existing one.

**Completed-session rule:** a record is confirmatory-eligible for a symbol only if that
symbol's finest measurement series reaches `REFEREE_SESSION_COMPLETE_ET` (partial mid-day
records are exploratory-only; the session guard fails open by design, so this predicate is
the completeness gate).

**Exclusions are counts, never values:** a truncated primary-horizon leaf, an unmeasurable
leaf (`reason` non-null), or a zero-eligible-null occurrence is excluded from the pool and
counted in served exclusion fields. There is no fallback measure substitution, ever.

## 3. Estimands and tests

Three Playbook estimands; one strategy-family analog. Each hypothesis registers exactly ONE
primary `(measure_key, horizon)` chosen from the setup's economic semantics, and its
sidedness; every other measure/horizon is secondary/descriptive and carries no confirmatory
weight.

### 3.1 Estimand A — setup effect
"Do occurrences of setup S (side d) carry information beyond comparable times of the same
sessions?" Comparison: each eligible occurrence vs its ToD-matched null anchors
(`referee-null-tod-v1`, §4.1), paired within session.

Per informative session s (≥1 eligible occurrence with ≥1 eligible anchor):
`Δ_s = mean(occurrence values in s) − mean(anchor values in s)`.

### 3.2 Estimand B — context-associated difference within setup
Named honestly: this is ASSOCIATION, not a randomized increment (context labels are not
assigned at random; symbol-mix and time-of-day composition can confound; the hypothesis
record carries this statement). "Among occurrences of setup S (side d), do occurrences in
context cell C differ from same-setup occurrences outside C?"

Informative sessions = sessions containing BOTH groups (cell and complement, same setup+side,
eligible occurrences). Per informative session:
`Δ_s = mean(cell values in s) − mean(complement values in s)`.
One-group sessions contribute nothing and are counted out loud. Per-cell symbol composition
is served beside the result. Full (session × symbol) stratification is too sparse at this
corpus and is deliberately NOT claimed.

### 3.3 Estimand C — combined effect
"Are occurrences of setup S (side d) in context cell C better than chance at comparable times
AND comparable structure?" As estimand A, but against the context-matched null
(`referee-null-context-v1`, §4.2). Registration as C is REFUSED when the context predicate is
not evaluable at anchor bars from recorded data — register as A or B instead, never
approximate silently.

### 3.4 The primary test — within-session group-label permutation (`referee-test-perm-v1`)
Combined statistic over informative sessions:
`T = Σ_s w_s · Δ_s / Σ_s w_s`
with pre-registered precision weights:
- A/C: `w_s = n_s · K_s / (n_s + K_s)` where `n_s` = eligible occurrences, `K_s` = eligible
  anchors in session s (the harmonic form; equals `n_s·K/(K+1)`-proportional when anchors are
  full-K);
- B: `w_s = n1_s · n2_s / (n1_s + n2_s)`.

Null distribution: independently within each informative session, permute the group labels
among that session's pooled eligible observations, PRESERVING group sizes (seeded stream
`purpose="perm"`, per-session sub-streams); recompute `T*`. Draws: full enumeration when the
total space ≤ `REFEREE_ENUMERATION_THRESHOLD`, else `REFEREE_B` seeded draws.
`p = (1 + #{T* ≥ T}) / (B + 1)` for registered sidedness "greater" (mirrored for "less";
two-sided uses `|T*| ≥ |T|`). The `+1` convention keeps p super-uniform under H0
(Phipson–Smyth); the minimum attainable p (granularity) is served beside every p.

Validity: exact (conditional on the realized observations) under within-session
exchangeability of labels — which is precisely the H0 the constructed null encodes (A/C) or
the no-context-information H0 (B) — for ANY group-size ratio and ANY skew. This is the reason
it is primary and the session-level sign-flip is not (§6 case iii demonstrates the sign-flip's
finite-sample mis-sizing for unequal groups under skew).

### 3.5 Robustness disclosures (never the decision)
Computed and served beside every confirmatory result; feeding only the `fragile` verdict:
1. session-level sign-flip on `{Δ_s}` (the cluster-coarse view; `purpose="flip"`),
2. the equal-session-weight variant of T (`w_s = 1` — the fat-session defense reading),
3. the entry-basis sensitivity (§4.3),
4. occurrence-level AND session-clustered percentile bootstrap CIs (§3.6).

### 3.6 Uncertainty
Percentile bootstrap at `REFEREE_CI_LEVEL`, seeded:
- occurrence-level (`purpose="boot-occ"`): resample eligible occurrences' paired per-
  occurrence differences (A/C: occurrence value − mean of its own anchors; B: not defined at
  occurrence level — occurrence-level CI is over the cell-vs-complement pooled difference)
  with replacement;
- session-clustered (`purpose="boot-cluster"`): resample informative sessions with
  replacement; a drawn session carries ALL its observations; the statistic is T.
Below `REFEREE_MIN_CLUSTERS_FOR_CI` informative sessions the clustered CI serves
`insufficient_sample`. CIs are descriptive companions; no CI is ever a p-value (the era's
anti-goal), and MDE ≈ `z_{1−α} · sd*(T) / 1` from the clustered resamples is served as the
power disclosure.

### 3.7 Strategy-family analog
Cluster = dataset. Per dataset d with ≥1 candidate trade:
`Δ_d = mean(candidate net_r in d) − mean(recorded random_null net_r in d)`; the same
permutation frame within dataset; the same floors read over datasets. At today's corpus the
expected honest outcome is `insufficient_sample`; the adapter serves the Card-6.4
`basis_caveats` and the null-design disclosure (the recorded null is 100 uniform-random
entries, not count/ToD-matched — stated, not hidden).

## 4. Matched nulls

### 4.1 `referee-null-tod-v1` — the time-of-day-matched null
For each eligible occurrence (primary-horizon leaf complete):
- Anchor population: bars of the SAME symbol's SAME measurement series (`measure_bars`, same
  `tf_minutes`) in the SAME session, whose ET time falls in the occurrence's ToD bucket,
  EXCLUDING the trigger/anchor bar of the occurrence itself.
- **Remaining-time matching:** for fixed horizons (1m/5m/1h/4h), an anchor bar is eligible
  only if ≥ horizon minutes of session remain at it (mirroring the occurrence's own
  completeness). For `to_close` primaries, eligibility is the ToD bucket alone and the mean
  |exposure difference| (minutes-to-close) is a served disclosure.
- Draw: `min(K, eligible)` anchors WITHOUT replacement, seeded stream
  (`purpose="null-draw"`, per-occurrence sub-stream); shortfall disclosed; zero eligible ⇒
  the occurrence is excluded and counted.
- Measurement: the imported `desk_forward._measure_from` at the anchor bar, `entry = anchor
  bar close`, `entry_kind = "close"`, the SIGNAL's side sign — identical conventions,
  identical series, identical truncation semantics.
- Overlap disclosure: mean fraction of each anchor's primary-horizon window overlapping its
  paired occurrence's window (the same-session power-cost made visible). No exclusion radius
  beyond the trigger bar itself (decided; the disclosure replaces it).

### 4.2 `referee-null-context-v1` — the context/time-matched null
As 4.1, plus: the anchor bar's price must satisfy the SAME backing-bucket predicate the
hypothesis registers (e.g. `at_wall`: distance from the anchor bar's close to the wall behind,
side-relative, ≤ 70 bps inclusive — evaluated through the existing `BandMapResolver` over the
RECORDED band map for `(symbol, basis_day)`, the context layer's own machinery); `room_r` at
the anchor borrows the paired occurrence's risk distance (the shipped
`risk_source="paired_signal"` convention). Per-cell anchor eligibility rates are served; a
cell whose anchors cannot be found is an exclusion disclosure, never a substitution.

### 4.3 The entry-basis sensitivity (pre-registered, mechanical)
Occurrences enter at detector-decided `entry`/`entry_kind`; anchors enter at bar close. The
registered estimand wording is therefore "differs from a ToD-matched close-anchored
baseline". The sensitivity: re-measure each occurrence close-anchored at its trigger bar
through the same rail (read-side, at evaluation time; detectors untouched) and recompute T.
A sign flip of T under this sensitivity triggers `fragile` mechanically.

### 4.4 Persistence
Null sets are recorded append-only (`TAPEOLOGY_DESK_REFEREE_NULL_DIR`), keyed
`(playbook record id, null-spec signature)`, embedding the null parameters verbatim, with a
run ledger and compute manager/CLI. GETs serve recorded nulls or honest absence; they never
compute.

## 5. Registry, boundary, checkpoint, and BH

- **Family record** (immutable): `family_id`, `q`, the COMPLETE planned candidate list
  (hypothesis ids), `registered_at`. The BH denominator m = the planned count, forever.
- **Hypothesis record** (immutable): identity + estimand + setup/side + context predicate +
  primary `(measure, horizon)` + sidedness + null-spec id + test-spec id + `detector_basis` +
  `context_algorithm_version` (when contextual) + `confirmation_start_boundary` +
  `target_sessions` + floors + `origin: "historical-exploration"` + `family_id`.
- **Boundary:** `confirmation_start_boundary` = the ET calendar date of `registered_at`
  (UTC → America/New_York); confirmation admits only observations with `session_date`
  STRICTLY after it. The boundary is on `session_date`, never `recorded_at` — a
  deep-backfilled record for an older session date recorded after registration can NEVER
  enter confirmation (counter-tested).
- **Withdrawal:** permitted only while no post-boundary evaluation of the hypothesis exists;
  afterwards the hypothesis remains in m and folds as p = 1 if never evaluated.
- **The single confirmatory checkpoint:** the FIRST evaluation of a hypothesis at which
  post-boundary informative sessions ≥ `target_sessions` (on completed-session records) is
  its confirmatory evaluation. Its family-level BH adjudication is recorded as an append-only
  ADJUDICATION SNAPSHOT — the citable verdict. Earlier evaluations serve
  `pending_forward_confirmation` (accrual math, NO confirmatory p). Later evaluations are
  labeled `monitoring` and can never change the snapshot. A replication is a NEW registered
  hypothesis. This closes optional stopping; there is no interim-look schedule in v1.
- **BH within a family** (at its registered q, over the family's checkpoint p-values, m =
  planned): sort ascending, `k* = max{k : p_(k) ≤ (k/m)·q}`, corroboration for ranks ≤ k*.
  Benjamini–Yekutieli adjusted values are served beside BH as a dependence-robustness
  disclosure; BH is the registered decision rule. The `REFEREE_REGISTER` states that
  family-wise q does not compound across families — running many families over time erodes
  global FDR, and only the registry's full history makes that auditable.
- **Verdicts** (each a pure function of recorded facts):
  `exploratory` (basis not registered) · `registered` (boundary set, zero post-boundary
  informative sessions) · `pending_forward_confirmation` (0 < accrued < target) ·
  `insufficient_sample` (floors unmet at checkpoint, or `REFEREE_MIN_CLUSTERS_FOR_CI` unmet)
  · `fragile` (BH pass BUT: BY fail, OR any §3.5/§4.3 sensitivity flips T's sign, OR the
  clustered CI includes 0) · `no_evidence` (checkpoint ran; null not rejected under BH) ·
  `corroborated` (BH pass + no fragility trigger + floors met) · `killed` (a registered kill
  condition met) · `basis_retired` (disclosure: the pinned `detector_basis` is no longer
  produced by the live corpus). "Survivor" is never used — that word belongs to `pnl_scan`'s
  holdout measurement concept.

## 6. Oracles and the fail-closed attestation

The oracle suite (seeded; `REFEREE_ORACLE_REPLICATIONS` datasets/case; `REFEREE_ORACLE_B`
draws inside each; total ≤ `REFEREE_ORACLE_BUDGET_SECONDS`) is the acceptance for the
statistics core. Cases:

1. **Size, iid skewed:** lognormal-shifted-to-zero-mean occurrence values, n_s=1, K=4 —
   empirical rejection at α=0.05 within the tolerance band.
2. **Size, heavy-tailed:** Student-t(3)-generated values — same band.
3. **The two demonstrated failures (must fail, by design):**
   (a) an UNCLUSTERED pooled-label permutation foil on a session-clustered null (shared
   per-session regime shifts) over-rejects (> the band's ceiling);
   (b) the session-level SIGN-FLIP variant on the skewed n_s=1/K=3 one-sided case mis-sizes
   while the within-session label permutation holds size. These two cases are the recorded
   evidence for why the primary test is what it is.
4. **Power:** a +0.5·sd location shift at S = 40 informative sessions — rejection rate
   reported and pinned as a golden (a stated power, not a gate).
5. **BH sweep:** 20 known-null + 1 known-positive candidates, m = 21 — across seeds, BH at
   q=0.10 admits ≈ the positive only (the false-admission rate stays within its binomial
   band).
6. **CI coverage:** clustered percentile CI covers the true session-mean effect at ≈ 95%
   within tolerance at S = 40; the S = 6 case correctly serves `insufficient_sample` instead
   of an interval.

**Attestation:** `run_oracle_attestation()` executes a pinned known-answer subset (fixed
seeds, fixed tiny datasets, exact expected p/CI digests with stated tolerances) and returns
`{passed, expected, actual, tolerance, stats_core_version}`. Every evaluation record embeds
its attestation. The adjudication fold VERIFIES the attestation (presence + match + version)
and refuses confirmatory output with honest served copy when it fails — fail closed, but
never Monte Carlo at GET time.

## 7. The starter family (PROPOSED shortlist — the operator approves 2–3 at the J-07 act)

Constraints (operator ruling 2026-08-14): 2–3 hypotheses, operator-approved through the REAL
registration act, never auto-baked or special-cased; `origin: "historical-exploration"` on
every one (the atlas was inspected before these questions were written down); prefer covering
all three estimands; exactly one semantically-chosen primary per hypothesis (never
performance-picked, never blanket-`1h`); confirmation strictly post-boundary; zero
`corroborated` at era end is the expected honest state.

| # | Estimand | Candidate | Corpus at authoring (n / sessions, current basis) | Proposed primary + semantic rationale |
|---|---|---|---|---|
| S-1 | A | `capitulation:long` vs ToD-matched null | 473 / 71 | `5m` return — the book's capitulation claim is the immediate reflexive snapback off climax exhaustion; minutes-scale, not session-scale |
| S-2 | A | `jbe:long` vs ToD-matched null | 164 / 44 | `1h` return — jump-base-explosion claims continuation of an established leg; the follow-through hour after the base resolves |
| S-3 | A | `double_top:short` vs ToD-matched null | 771 / 105 | `to_close` return — a completed reversal structure claims the session's trend has turned; always measurable by construction |
| S-4 | B | `range_trade` (registered per side) `at_wall` vs other same-setup contexts | subset of 469+459 / ~80 (live cell counts served at registration) | `1h` return — a range bounce plays out over the traverse toward the opposite boundary; `to_close` would contaminate with post-breakout regimes |
| S-5 | C | `range_trade:long` + `at_wall` vs context/ToD-matched null | subset served at registration | `1h` return — the combined claim: a wall-backed bounce is better than chance at that time and place |

Deliberately not proposed: `open_high_break`/`open_low_break` (26 and 18 occurrences — below
any honest floor), `cup_handle` (n = 1), a fourth A on `dbi:short` (kept for a future
family). The registration surface serves LIVE readiness (n, informative sessions, accrual
rate, projected days to `target_sessions`) beside each candidate; the operator picks with the
sample reality in view.

## 8. The promotion certificate and interlock

- **Certificate record** (append-only, in the registry): pins `{candidate (strategy_id,
  profile), champion identity at scan time, train dataset (id, checksum, split), holdout
  dataset (id, checksum, split), config_fingerprint, REFEREE_GATE_VERSION + referee
  parameters hash, family_id + hypothesis_id, gate results (calibrated p, BH pass at the
  family q, CI, floors)}`. Mintable only through the real evaluation rail — never by hand,
  never by fixture paths in production code.
- **`authorize_promotion`** runs inside `pnl_scan._promote` BEFORE any write (the
  ledger-row-first / champion-pointer-second order is unchanged after authorization). Fail
  closed, with distinct honest refusals: no certificate · stale (ANY pin differs from the
  live scan's own report values) · wrong candidate · mismatched datasets/fingerprint ·
  failed gates · malformed/unverifiable (store integrity failure). No `--force`, no skip
  flag, no env override, no default-allow mode (source-scan guard-tested). A Playbook
  hypothesis certificate can never satisfy a strategy promotion (the candidate pins make
  this structural).
- Survivor labelling and every report stay as shipped measurement concepts:
  `survivor: true` with `promotion_eligible: false` (+ the refusal reason) is an honest,
  expected state for the rest of this era.

## 9. Stated assumptions and limits (served, not hidden)

1. **Same-session matching is conservative under H1:** anchors share the session's realized
   drift, which under a true effect partially contains the effect itself — a power cost, paid
   for exchangeability. The overlap disclosure (§4.1) quantifies it.
2. **Estimand B is observational:** context labels are not randomized; symbol-mix and ToD
   composition can confound; B verdicts are association statements, worded so.
3. **Exchangeability is within-session:** the permutation conditions on each session's
   realized values; cross-session dependence enters only through the session-level statistic
   and the clustered CI — the reason both are mandatory.
4. **The corpus is coverage-heterogeneous** (median 4 symbols/date at authoring, 38
   full-universe dates): precision weights lean on fat sessions; the equal-weight sensitivity
   discloses when that matters.
5. **Discrete p-values** make BH conservative at small S; the granularity floor is served.
6. **The strategy family's recorded null is unmatched** (uniform-random, fixed 100); its
   adjudications say so, and Card 6.6's matched nulls remain future work gated on the tick
   library.
7. **The forming-bar caveat (Card 6.4)** applies to structure/strategy-family measurement
   bases and is stamped as `basis_caveats`; it does not touch Playbook context (recorded
   band maps) or these tests' validity.
8. **(2026-08-16 addendum, goal-referee-iter-12, J-11) The accrual projection is a read-side
   planning disclosure, not a statistical procedure.** The starter-family shortlist's shipped
   `accrual_rate_sessions_per_day`/`projected_days_to_target` divide a candidate's recorded
   sessions by the corpus's raw CALENDAR-day span (`corpus_span_days`), which can silently
   include stretches with zero recorded trading sessions — a multi-month recording gap inflates
   that projected wait. This addendum adds a second basis measured in RECORDED sessions instead
   of calendar days (`accrual_basis`'s `recorded_sessions_in_span`/
   `pooled_sessions_at_current_basis`/longest zero-session stretch, plus each candidate's own
   `informative_sessions_per_pooled_session`/`projected_pooled_sessions_to_target`), served SIDE
   BY SIDE with the calendar-day pair — neither basis ever replaces the other. Both bases are
   pure read-side arithmetic over already-recorded facts: neither feeds any null, test statistic,
   p-value, BH denominator, verdict, or gate, and neither is a `referee_parameters()` entry — the
   spec's estimands, tests, and verdict rules (Sec3-Sec5) are unchanged by this addendum.
