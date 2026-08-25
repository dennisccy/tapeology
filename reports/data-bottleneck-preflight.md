# Data-bottleneck preflight — read-only audit and acquisition plan

**Repo** `dennisccy/tapeology` · **Branch** `goal/rapid-microscope` · **HEAD** `e0136130e7ccfa7cb91556449587fd31274dd0dd`
**Spec revision in force** r13 · **`config_fingerprint`** `08e471b10130e1e2` (verified live)
**Status** PLANNING ONLY. No data fetched, no recorder run, no sealed shard opened / assigned / exposed,
no Scout or walk-forward run on new data, no ledger written, no threshold / geometry / floor changed.

Every number below was read from disk or computed from committed code. Where a fact could not be
learned without exposing withheld evidence, it is marked **cannot be learned safely in preflight**.

---

## Disclosure discipline applied to this document

Spec §7.2 forbids serving the registered universe's canonical `symbol_rule` / `date_rule` before
whole-pool release; §7.5 forbids exact per-shard or pool-level trade / quote / byte counts while any
member is unexposed. Accordingly this report:

- **does** name the eight panel symbols — §7.2.1(i) publishes the panel composition and the
  vault screen-provenance ledger publishes the resolved Tier-B names, so they are already public;
- **does not** enumerate the registered `date_rule`, and expresses every date-axis constraint as a
  *mechanical predicate* (§5) rather than a list;
- **does not** give per-shard or per-date volumes, and rounds pool-level storage figures.

One residual weak disclosure is unavoidable and is flagged rather than hidden: stating that the
recommended recording window is free of every barred date implies that all barred dates fall outside
it. Mitigation is in §6.

---

## 1. CURRENT STATE

### 1.1 Exposed tick corpus

Reproduced exactly as production computes it (`micro_snapshots.exclude_withheld` →
`vault.unresolved_pool_universe_by_dataset_id`), over `apps/backend/.data/datasets`:

| quantity | value |
|---|---|
| datasets in store | 98 |
| withheld (unresolved registered-universe pool) | 80 |
| **healthy exposed datasets** | **18** |
| integrity errors | **0** (`DatasetStore.list()` → `errors == []`) |
| distinct symbol-days | 12 |
| **distinct ET session dates** | **11** (2026-05-27 … 2026-07-13) |
| distinct symbols | 11 (AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, PG, SPY, TSLA) |
| bytes on disk | 0.92 GB |
| RTH minutes covered | 1 173.5 |
| **full-session equivalents** | **3.0089** (÷ 390 min) |
| exposure class | `historical_exposed_diagnostic`, permanently (§7.7) |
| snapshot availability | **18 / 18 current** — one `feature_source_hash` `d6945fdd…`, one `params_hash` `5d3f3094…`, one `config_fingerprint` `08e471b10130e1e2` |
| Scout-readable session count | **11** |

**The most important number here is 3.0089, not 11.** Every window is partial: seven are 08:30–11:00
ET (only 90 min of which fall inside RTH), one is 14:00–16:30 ET, one is 10:15–12:45 ET, and seven are
sub-10-minute PG probe windows on a single date. The corpus is eleven *dates* but three *sessions* of
actual regular-hours tape.

Label quality (`micro_readiness._label_quality`, computed live from the warm `fallback_frac` cache):

| field | value |
|---|---|
| `shards_measured` | 18 |
| `trade_weighted_fallback_frac` | **0.6171** |
| min / max | 0.2931 / 0.8252 |
| `shards_majority_inferred` (> 0.5) | **15 of 18** |
| `affected_families` | F-FLOW, F-RESPONSE |
| `unaffected_families` | F-LIQUIDITY |

62 % of aggressor labels in this corpus are *inferred by the tick test*, not determined by the quote
rule. That is a material caveat for F-FLOW / F-RESPONSE and says nothing about F-LIQUIDITY.

### 1.2 Readiness — the two floors

**60-session floor** (`micro_readiness.build_readiness` → `study_floors`):
`required_sessions = WF_TRAIN_MIN_SESSIONS(40) + WF_TEST_MIN_SESSIONS(20) = 60`;
`available_sessions = 11` → **`floor_unmet` for all three pilot studies**
(`range_wall_failed_aggression`, `delta_divergence_level_tests`, `capitulation_exhaustion`).

**105-session floor** (`walkforward.minimum_sessions_for_sufficient_folds(DIAGNOSTIC_GEOMETRY)`,
verified live = `105`). `run_tick_family_fold_request` was invoked against the real store during this
preflight — a read-only call that raises *before* `register_fold_spec` and therefore writes nothing.
Its verbatim answer:

```
TYPED REFUSAL: 11 < 105 -- refused (TR-15): this corpus cannot produce
WF_MIN_SUFFICIENT_FOLDS(3) folds under this geometry (this count excludes
80 withheld Validation-Vault shard(s), spec section 7.5 point 6)
```

This is goal.md's own acceptance sentence, met exactly, with the r4 withheld-disclosure suffix
attached. The persisted run log `.data/micro_walkforward/runs.jsonl` shows three earlier `failed`
runs whose message reads `0 < 105` and carries no disclosure suffix; that `0` is a scoped-fixture
artifact (an empty dataset dir), not the real-store answer — confirmed by the run above.

**A third gate exists and is currently unmet**: `REFEREE_TICK_GATE_SYMBOL_DAYS = 150`
(`referee_evidence.py:149`). `reports/j06-tranche/acceptance.json` records
`research_gate_150_symbol_days: {have: 80, target: 150, met: false}`.

### 1.3 Vault / recorded pools — aggregates only

| quantity | value |
|---|---|
| registered universes | **1** (`rapid-microscope-j06-starter`, registered 2026-08-21T16:04:59Z) |
| original pool size | **80 pairs** (8 panel symbols × 10 dates — the §7.2.1(i) published arithmetic) |
| recorded pool members | **80 / 80**, `full_session_pct: 100.0` |
| **sealed** | **21** |
| **assigned** | **0** |
| **exposed** | **0** |
| otherwise withheld (recorded, no shard-ledger row) | **59** |
| HMAC-selected total / recorded / sealed | 21 / 21 / 21 — `unsealed_selected_recorded: []` |
| distinct dates in pool | 10 |
| distinct symbols in pool | 8 |
| split distribution | holdout 13 / train 67 |
| all four vault chains | `verify_chain()` **ok** (universe, shard, screen-provenance, disclosure) |
| schema basis | `tick_recorder_v1_card_5_1_preservation_present` × 80 |
| `quote_size_unit` | `shares` × 80 |
| pool-level bytes | **order 10 GB** (coarse, per §7.5) |

**Incomplete universes**: none. Batch verification passed
(`tr4_batch_verification.ok: true`, `blocking_missing_pairs: {}`,
`unrecovered_disclosed_vendor_failures: []`).

**Collision state**: **1** — one legacy dataset occupies one registered pair. It was handled by
§7.2.2 *completion*, not substitution: the legacy dataset stays on disk, permanently exploratory,
excluded from the tranche (`legacy_collisions_counted_as_j06: 0`), and the recorder wrote a genuine
shard for the same pair. `legacy_datasets_untouched: 18`, `legacy_dataset_ids_with_shard_rows: 0`.

**Disclosure incidents**: **1** — `j06-operator-report-pool-position-2026-08-22`, a
`non_sealed_pool_position` disclosure, `sealed_member_identity_disclosed: false`. Its consequence is
permanent: `vault.assign_shard` refuses that position for the lifetime of this vault directory, so it
can never receive sealed / blind / historical-OOS credit. TR-2 was re-run with the disclosure treated
as attacker-known: `no_identity_determinable_with_certainty: true`, 79 unknown positions vs 21
still-unexposed selected shards.

### 1.4 Sealed evidence is untouched — explicit confirmation

Every one of the 21 sealed shards has `exposure_state == "sealed"`, `assigned_at == null`,
`exposed_at == null`. No shard row was written, read-for-content, assigned, or exposed by this
preflight. `vault_shard_ledger.jsonl` is unchanged at 21 rows with an intact chain head. No sealed
snapshot row was read: the only snapshot reads performed were metadata (`*.meta.json`) on the 18
exposed shards.

### 1.5 Scout state

18 ledger rows = 6 candidates × 3 registration acts (two pre-r13, one post-r13 re-key).
The six live post-r13 candidates:

| candidate | family | decision |
|---|---|---|
| `cumulative_delta ge 0` | F-FLOW | `killed_null` |
| `cumulative_delta le 0` | F-FLOW | `killed_null` |
| `failed_aggression_score ge 0` | F-RESPONSE | `killed_insufficient_n` |
| `failed_aggression_score le 0` | F-RESPONSE | `killed_null` |
| `quote_imbalance ge 0` | F-LIQUIDITY | `killed_economic` |
| `quote_imbalance le 0` | F-LIQUIDITY | `killed_economic` |

All carry `sidedness: null` (unsided discovery), `structure_context: {"kind": "none"}`,
`outcome_unit: "return_bps"`, `evidence_class: "historical_exposed_diagnostic"`,
`withheld_excluded: 80`, `n_sessions_total: 11`. Econ floor `1.5262 bps`.
**0 survivors.** Variant budget: `variants_tried = 4` of `SCOUT_MAX_VARIANTS_PER_FAMILY = 24` in each
of the three families.

---

## 2. 60 VS 105 — the exact geometry

### 2.1 Where each number comes from

```
micro_readiness.py:102   WF_TRAIN_MIN_SESSIONS = 40
micro_readiness.py:103   WF_TEST_MIN_SESSIONS  = 20
walkforward.py:174       WF_MIN_SUFFICIENT_FOLDS = 3
walkforward.py:229       DIAGNOSTIC_GEOMETRY = {train 40, embargo 5, test 20, step 20}

walkforward.minimum_sessions_for_sufficient_folds(geometry):
    fold_one_span = train + embargo + test
    return fold_one_span + (WF_MIN_SUFFICIENT_FOLDS - 1) * step
  = (40 + 5 + 20) + 2 * 20 = 65 + 40 = 105        [verified live: 105]
```

### 2.2 What 60 permits — and does not

60 is **not** a fold-construction floor. It is the readiness table's floor
(`micro_readiness.build_readiness`: `required_sessions = 40 + 20`) and the session-count floor inside
`walkforward.scout_candidate_walkforward_floor_check`.

Under `DIAGNOSTIC_GEOMETRY`, `build_folds` at n=60 returns **zero folds** — verified:

| sessions | folds produced | validation sessions |
|---|---|---|
| 60 | **0** | 0 |
| 65 | 1 | 20 |
| 85 | 2 | 40 |
| 104 | 2 | 40 |
| **105** | **3** | **60** |
| 125 | 4 | 80 |
| 145 | 5 | 100 |

Minimum for *k* folds = `65 + 20·(k−1)`.

So clearing 60 permits exactly this: the readiness table flips from `floor_unmet` to `floor_met`, and
`scout_candidate_walkforward_floor_check` stops refusing on `oos_sessions`. It permits **no fold, no
sequence verdict, and no survivor state**. Clearing 65 permits one fold; a sequence with fewer than
`WF_MIN_SUFFICIENT_FOLDS` sufficient folds refuses a sequence-level verdict outright
(`walkforward.sequence_verdict`). **105 is the first count at which a `walkforward_survivor` verdict
is even reachable.**

For completeness and to close it off: an `embargo_sessions = 0` geometry would need only 100 sessions
for 3 folds, and §6.3 does say `E = 0` is a legitimate outcome when no cross-boundary dependency is
identified. Choosing E=0 *now*, after seeing that it would be convenient, would be a tuning act.
**This plan reuses `DIAGNOSTIC_GEOMETRY` verbatim so that no new geometry choice is introduced at
all**, and 105 therefore stands.

### 2.3 Can existing exposed sessions appear in training or validation windows?

The rule is `walkforward.classify_evidence_class` (spec §6.7), and it is mechanical:

```python
def classify_evidence_class(exposure_registry, *, corpus_id, window_sessions, registered_at):
    if not window_sessions:
        return EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    for session_date in window_sessions:
        if exposure_registry.is_exposed_before(corpus_id=corpus_id, window=session_date,
                                               instant=registered_at):
            return EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    return EVIDENCE_CLASS_HISTORICAL_OOS
```

Note what it does and does not consider. It classifies the **validation window only**; a training
window has no evidence class at all. And it is **corpus-scoped** — the same calendar date can be
exposed under one `corpus_id` and unexposed under another.

- **Training windows** — an exposed session may lawfully appear, in both Mode A and Mode B. Nothing
  reads the class of a training window; Mode A fits its rule there and Mode B does not read it.
  Scientifically it is also fine: fitting on already-seen data is what a training window *is for*.
- **Validation windows** — an exposed session in a Mode A or Mode B test window forces the whole fold
  to `historical_exposed_diagnostic`, which is worth **zero** graduation credit
  (`WF_SURVIVOR_RULE_V1` condition 1 requires every sufficient fold to be `historical_oos` **and**
  `rule_process`). A single exposed session anywhere in a 20-session test window poisons that fold.

**The hard fact this creates.** The exposure registry on disk currently holds **174 rows**, all
`surface: "r2_initialization"`, all stamped `2026-08-16T00:00:00.000000Z`:

- `playbook_setups_diagnostic_v1` — 154 windows, 2026-01-02 … 2026-08-13
- `tick_legacy_symbol_days_v1` — **20 windows, 2026-05-27 … 2026-08-12**

Those 20 windows are the union of the 11 exposed dates and the 10 registered-universe dates. The r2
seed excludes *sealed dataset ids*, but its unit is the **date**, not the dataset — and a sealed
shard's date is shared with unsealed siblings on the same date, so every pool date was seeded anyway.
`walkforward._tick_dataset_session_dates` documents exactly this and says why it is tolerable:

> "a date shared with an UNSEALED sibling still gets seeded via that sibling's own contribution … Do
> not read this filter as 'a sealed shard's window is provably unexposed' in general. That is
> acceptable only because these entries are scoped to `TICK_LEGACY_CORPUS_ID`, under which a sealed
> shard must never be evaluated at all (spec §7.7)."

**Consequence: under `corpus_id = "tick_legacy_symbol_days_v1"`, every one of those 20 dates is
permanently `historical_exposed_diagnostic`. No walk-forward sequence run under that corpus id can
ever produce a survivor, no matter how many new sessions are added to it.** A new corpus era is not
an optimization here; it is structurally required, and it is the architecture the module already
documents.

---

## 3. WHAT COUNTS AS CLEAN OOS

Three classes, kept disjoint:

| class | definition | where it comes from |
|---|---|---|
| `historical_exposed_diagnostic` | some session of the validation window carries an exposure entry stamped before the spec's `registered_at`, **under that corpus id** | the 11 legacy dates, the 155-session playbook corpus, and any window a study has already served |
| `historical_oos` | no session of the validation window carries such an entry | a fresh corpus era whose windows have never been served |
| sealed vault shard | a `sealed → assigned → exposed` lifecycle member of a registered universe; single-shot, root-family-level | `vault.py`, evaluated by `micro_sealed_evaluation.py` under `SEALED_PASS_RULE_V1` |

Two mechanical facts that fix the boundaries:

1. **Scout output is never OOS.** `scout.py` sets `evidence_class = "historical_exposed_diagnostic"`
   *unconditionally* (`scout.py:1291`, docstring at `scout.py:63-69`). Discovery is by definition
   exposure. A Scout screen can only ever produce class-1 evidence.
2. **The sealed stage inherits the class it is handed.** `micro_sealed_evaluation` reads
   `evidence_class` and `process_label` off the `candidate_spec` it is given
   (`micro_sealed_evaluation.py:441`) and `SEALED_PASS_RULE_V1` condition 5 requires
   `historical_oos` + `rule_process`. A spec that reached the sealed stage carrying the Scout's own
   class fails condition 5. The class must come from the walk-forward stage.

So the ladder is strict: **Scout (always exposed) → walk-forward folds (class computed per window,
per corpus) → sealed shard (must already be `historical_oos` + `rule_process`).**

---

## 4. HISTORICAL BACKFILL VS WAITING FOR FUTURE DAYS

**Answer: yes — a lawful historical backfill produces genuine `historical_oos` evidence. We do not
need to wait 94 trading days.**

### 4.1 The proof, in code

`classify_evidence_class` (above) compares only two things: exposure-entry `logged_at` values and the
spec's `registered_at`. It never reads a calendar, never compares a session date against "today", and
never calls the wall clock. Grep of the entire classification path
(`walkforward.py`, `micro_accessor.py`, `micro_sealed_evaluation.py`) finds exactly three
`datetime.now` sites — all of them `_iso_utc_now()` helpers producing *default timestamps for rows
being written*, none of them in a predicate.

`ExposureRegistry.is_exposed_before` is likewise pure:

```python
for row in self._ledger.all_rows():
    if row["corpus_id"] == corpus_id and row["window"] == window and row["logged_at"] < instant:
        return True
return False
```

`micro_accessor.py`'s own docstring states the design intent directly: *"A registry for a genuinely
NEW corpus_id … starts EMPTY — nothing pre-marks a corpus this module has never heard of, so a spec
registered against a freshly-built synthetic corpus can legitimately classify `historical_oos`
(TC-21, TC-22)."*

Therefore: **freeze and register a rule today → fetch previously-unrecorded historical tick dates →
evaluate them → `historical_oos`**, provided those dates' tick outcomes were never inspectable under
that corpus id before registration. The registration instant, not the calendar, is the boundary.

### 4.2 The standing retrospective caveat (§7.7)

> "Retrospective sealed shards (past dates recorded fresh) carry the standing disclosed caveat that
> bar-level outcomes of their dates are public in the desk/playbook corpus; a
> **bar-reconstructibility diagnostic** … is REPORTED beside sealed evidence — it is a diagnostic
> only, **never a gate, never tunable, and never an authority**; independence is decided by the
> deterministic provenance/exposure rules above alone."

Concretely: the playbook bar corpus already covers 2026-01-02 … 2026-08-13, and the desk's daily-bar
calendar covers 2023-12-01 … 2026-08-13. A retrospective date's *bar-level* outcome (open/high/low/
close, daily return) is public even when its *tick* tape has never been served. The features this era
screens are microstructural — quote imbalance, cumulative delta, failed aggression, microprice,
spread change — none of which are reconstructible from a daily or hourly bar. But the honest position
is that a retrospective corpus is one notch weaker than a genuinely forward one, the diagnostic must
be reported beside every sealed verdict, and it must never be allowed to become a gate.

**Note this caveat applies equally to the 140-session window recommended below and to any other past
date. It is a property of retrospective recording, not of the particular window chosen.**

### 4.3 One real gap this exposes

`log_exposure` has **zero production call sites** other than `initialize_r2_exposure_registry` and the
origin-fenced `MicroAccessor` path — which, confirmed by grep of every `MicroAccessor(` construction
in `app/`, **no production caller constructs**. The registry is effectively write-once today.

That matters because `classify_evidence_class` has no `has_any_exposure_entries` guard (unlike
`scout_candidate_walkforward_floor_check`, which conservatively counts zero OOS sessions against an
unpopulated registry). Against an empty registry, `classify_evidence_class` returns `historical_oos`
for everything. For Mode A that is *defensible by construction* — the freeze order guarantees the test
window is read only after `spec_hash` is recorded, and `observations_in_sessions` asserts exactness —
but it means a **second** spec registered later could re-claim the same window as fresh.

**Wiring exposure logging into the new corpus's fold-observation reads is a required pre-registration
act, not a nicety.** It is listed in §14.

---

## 5. SAFE DATE SPACE

### 5.1 The barred set, as a mechanical predicate

A candidate recording date is barred iff **any** of:

1. it carries an exposure-registry entry under `tick_legacy_symbol_days_v1`
   (`ExposureRegistry.is_exposed_before(corpus_id=..., window=d, instant=<now>)`) — 20 such windows;
2. it is a member of `micro_tier_b_screen.SCREENING_EXPOSED_SESSIONS` — the five spread-screening
   sessions, already a frozen module constant and already enforced by
   `j06_operator._validate_panel_and_dates` via `tb.assert_no_exposed_session`. Their own artifact
   states it: *"SCREENING/EXPOSED observations — these sessions may never be used as J-06 sealed
   historical-OOS recording dates for any symbol screened here"*
   (`reports/tier-b-screen-r10/spread.json`);
3. it is not a recorded trading session under `desk_sessions.recorded_session_dates` (weekends,
   holidays, and dates with no daily bar are excluded for free — there is no hardcoded calendar).

Union of (1) and (2): **25 barred dates.**

The 30-session ADV screen (§7.2.1(e)) touched further dates, but it consumed *daily share volume*,
not tick data, and the spec bars only the five spread sessions. Those ADV dates are not barred; they
fall under the ordinary §7.7 bar-reconstructibility caveat like every other retrospective date.

### 5.2 The eligible space

Session calendar from `desk_sessions.recorded_session_dates` over the 101-symbol desk universe
(anchors AAPL, ABBV, ABT, ACN, ADBE): **676 sessions, 2023-12-01 … 2026-08-13**.

Restricted to the homogeneous `quote_size_unit = "shares"` era
(`ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE = "2025-11-03"`): **195 sessions**, of which **175 are unbarred**.

Contiguous unbarred runs inside that era:

| length | span |
|---|---|
| **140** | **2025-11-03 → 2026-05-26** |
| 4 | 2026-06-03 → 2026-06-08 |
| 4 | 2026-06-11 → 2026-06-16 |
| 4 | 2026-07-16 → 2026-07-21 |
| 4 | 2026-07-23 → 2026-07-28 |
| 4 | 2026-07-30 → 2026-08-04 |
| 4 | 2026-08-06 → 2026-08-11 |
| 3 | 2026-05-28 → 2026-06-01 |

**One contiguous run of 140 unbarred sessions exists, entirely inside the shares-unit era, and it
alone clears 105 with 35 sessions to spare.** Every other run is 4 sessions or fewer. There is no
second candidate range worth discussing.

### 5.3 Two early closes inside it

Detected objectively from AAPL 1-minute RTH bar counts (median 390 across the window):

| date | RTH 1m bars | reading |
|---|---|---|
| 2025-11-28 | 310 | early close (13:00 ET) |
| 2025-12-24 | 282 | early close (13:00 ET) |

These are not vendor failures — they are structurally short sessions. `j06_operator._full_session`
requires a ≥ 6.4 h recorded window, and `is_genuine_j06_dataset` gates on it, so an early close would
either fail the genuineness predicate or pass on nominal span while carrying ~3.5 h of real tape.
Excluding them is a **calendar rule, decided before any outcome is read**, in the same class as the
quote-size-unit preference. It is not an outcome-selection act.

**Clean window after exclusion: 138 sessions.**

Month distribution: 2025-11 ×18, 2025-12 ×21, 2026-01 ×20, 2026-02 ×19, 2026-03 ×22, 2026-04 ×21,
2026-05 ×17. No month dominates; calendar span 204 days (29.1 weeks) ≫ the §7.6 six-week minimum.

### 5.4 Collisions with already-recorded data

Zero. The 98 datasets on disk span 2026-05-27 … 2026-08-12 — every one of them falls **after**
2026-05-26. The recommended window collides with nothing, so §7.2.2's `legacy_dataset_collision`
condition cannot arise for any pair in it.

### 5.5 What cannot be learned safely in preflight

**Whether Alpaca serves SIP tick data back to 2025-11-03.** The only tick recordings that exist span
2026-05 … 2026-08; the bar store proves *bar* availability back to 2023-12 but that is a different
endpoint and a different retention policy. This must be settled by one cheap probe before the window
is committed — see §15 step 0, which probes on an **already-burned** date so it costs nothing.

---

## 6. RECOMMENDED CORPUS ARCHITECTURE

### The choice

**Option B — a dedicated fresh corpus era of ≥105 previously-unexposed session dates, under a new
`corpus_id`, containing both its own discovery block and its own OOS block.**

Not Option A (105 total including existing exposed discovery sessions).

### Why

1. **Option A is mechanically dead, not merely inelegant.** All 11 exposed dates carry exposure
   entries under `tick_legacy_symbol_days_v1` stamped 2026-08-16. Any fold whose 20-session test
   window touches one is `historical_exposed_diagnostic` and worth zero credit. Mixing them in buys
   training-window depth we do not need and risks poisoning validation windows we do.
2. **Class mixing is refused anyway.** `WF_SURVIVOR_RULE_V1` condition 1 requires *every* sufficient
   fold to be `historical_oos`; TR-5 refuses class-mixing in one pooled number. A corpus that mixes
   classes cannot produce a pooled verdict, only a refusal.
3. **Auditability.** With a dedicated corpus id, the question "is this window clean?" reduces to a
   single ledger query against one corpus id whose entire history is one era long. With a mixed
   corpus it becomes a per-window argument about which of 20 legacy entries applies. The user's own
   criterion — *least vulnerable to accidental class mixing* — decides this on its own.
4. **The code already assumes it.** `walkforward._tick_dataset_session_dates` explicitly justifies
   the legacy corpus's date-granularity leak on the grounds that "a sealed shard must never be
   evaluated at all" under that corpus id. Sealed evaluation under a different corpus id is the
   documented design, not a workaround.

### Why the new corpus must contain a discovery block too

`scout_candidate_walkforward_floor_check` counts **zero** OOS sessions when
`has_any_exposure_entries(registry, corpus_id)` is false — a deliberate fail-closed default. A
*pure*-OOS corpus would therefore always read as insufficient at that preflight boundary even though
`classify_evidence_class` would happily classify its folds as OOS. Splitting the new era into a
discovery block (marked exposed at the moment it is first read) and an OOS block (never marked) makes
both functions behave correctly and produces the honest record besides.

### The shape

```
corpus_id: rapid-microscope-tick-oos-v1          (new; TICK_LEGACY_CORPUS_ID untouched)
geometry:  DIAGNOSTIC_GEOMETRY verbatim           (train 40 / embargo 5 / test 20 / step 20)
           — reused, not re-chosen, so no new geometry degree of freedom is introduced
clustering_unit: session_date                     (§6.2, frozen for both families)

  block D  discovery   — exposed at first read, class-1 forever, feeds Scout and Mode A fitting
  block O  OOS         — never served before its spec freezes, class-2 eligible
  vault    a NEW universe registered over block O's dates, HMAC-sealed as usual, class-3
```

Blocks D and O are the same corpus era, so one fold spec and one geometry hash cover both; the
per-window exposure registry does the separating, exactly as §6.7 designs it. **The existing
`rapid-microscope-j06-starter` vault and its 21 sealed shards are left exactly as they are.**

---

## 7. RECOMMENDED DATE RULE

```
date_rule = every recorded trading session d such that
    2025-11-03 <= d <= 2026-05-26                       (homogeneous shares quote-size era)
    and d in desk_sessions.recorded_session_dates(...)  (no calendar table; holidays free)
    and not exposure_registry.is_exposed_before(
            corpus_id="tick_legacy_symbol_days_v1", window=d, instant=<registration>)
    and d not in micro_tier_b_screen.SCREENING_EXPOSED_SESSIONS
    and d not in {"2025-11-28", "2025-12-24"}           (early closes; calendar rule, pre-registered)
  -> 138 sessions
```

Each clause is mechanical, evaluated before any outcome is read, and reuses an existing owner. No
clause selects on realised data of any kind.

**Ordering within the era**: block D takes the **earliest** sessions and block O the **latest**, so
the chronology runs discovery → validation and never the reverse. Concretely: D = the first 33, O =
the last 105. Both blocks are contiguous and the split index is fixed before recording begins.

**Disclosure note.** Publishing this window's bounds implies that all 25 barred dates fall outside it.
That is a weak negative disclosure about the withheld date axis. It is partially unavoidable (the 11
exposed dates are already public in the served Scout `per_session_deltas_bps`, and the five screening
dates are a public module constant). **Recommendation: keep the concrete 138-date list operator-
private until the new universe is registered**, and register from the predicate above rather than
from a committed list.

---

## 8. RECOMMENDED SYMBOL RULE

```
symbol_rule = ["PG", "AAPL", "MSFT", "NVDA", "AG", "LYFT", "WULF", "SPY"]     (8 symbols, unchanged)
```

### The four separate requirements, kept separate

| requirement | source | value |
|---|---|---|
| **per-fold breadth** | `WF_FOLD_MIN_SYMBOLS` (`walkforward.py:223`) | **2** |
| **recorder / universe** | §7.2 — `symbol_rule` is "the explicit panel list"; no count minimum | none |
| **starter-tranche minimum** | §7.6 | **≥8** Card-5.2-panel symbols incl. `PG`, ≥3 Tier-B, ≥1 Tier-C ETF |
| **concentration** | §7.6 | no single symbol > 25 % and no single date > 20 % of tranche symbol-days → Cartesian ⇒ ≥4 symbols, ≥5 dates |
| **scientific robustness** | §5.4 disclosures, §5.3 concentration | a 2-symbol panel makes `top1_symbol_share ≥ 0.5`, which `SCOUT_MAX_TOP1_CONCENTRATION` would kill outright |

### Is a smaller follow-on universe legally supported?

**No.** I looked for the contract that would permit it and it does not exist:

- §7.6 is titled *"The starter tranche (**this era's recording acceptance**)"*. The parenthetical
  scopes it to the era, not to the first batch. Nothing in §7 distinguishes a first universe from a
  later one for acceptance purposes.
- §7.2.1(i) fixes the panel by construction: *"the J-06 minimum legal starter panel is exactly eight
  symbols, following the existing frozen Tier-A/Tier-C ordering so no post-screen human selection
  remains: `PG`, `AAPL`, `MSFT`, `NVDA`, the three resolved Tier-B names, and `SPY`."*
- §7.2.1(j) screen-once discipline forbids re-running the Tier-B screen. The resolved list
  `[AG, LYFT, WULF]` is frozen in the vault screen-provenance ledger (`rapid-microscope-tier-b-r11`,
  cutoff 2026-08-21T12:06Z, resolution artifact `fb89c5a2…`). It is neither re-screenable nor
  substitutable — *"no Tier-B re-screen, no substitution because a symbol is inconvenient, no
  replacement from vendor availability or observed data."*

So the panel is the same eight, not because 8 is convenient but because the spec names those exact
eight slots and forbids re-deriving them. `WF_FOLD_MIN_SYMBOLS == 2` is a per-fold floor and is not a
licence to record two symbols. No widening beyond the Card-5.2 panel either.

**One real consequence to plan for**: AG, LYFT and WULF currently have **zero 1d and 1h bars**, and
SPY has zero 1h bars over the target window. Paired bar backfill must run for those four symbols over
the whole 138-session window before band-context joins will work.

| symbol | 1d over 138 target sessions | 1h |
|---|---|---|
| PG, AAPL, MSFT, NVDA | 140 / 140 | 140 / 140 |
| SPY | 140 / 140 | **0 / 140** |
| AG, LYFT, WULF | **0 / 140** | **0 / 140** |

---

## 9. MATHEMATICAL MINIMUM

**105 distinct session dates in block O**, derived above from
`minimum_sessions_for_sufficient_folds(DIAGNOSTIC_GEOMETRY) = (40+5+20) + 2·20`, verified live.

Plus, to make block D usable and the registry non-empty: **≥1 discovery session**, and in practice
≥60 if a Scout re-screen on the new corpus is wanted (the readiness floor). 105 + 33 = 138 is what the
window supplies.

Not lowered, not renegotiated. `WF_MIN_SUFFICIENT_FOLDS`, `WF_TRAIN_MIN_SESSIONS`,
`WF_TEST_MIN_SESSIONS`, the per-fold floors, the econ floor, and `DIAGNOSTIC_GEOMETRY` are all
untouched by this plan.

---

## 10. OPERATIONAL TARGET

**138 sessions** — the whole clean window: **33 discovery + 105 OOS.**

### The buffer reasoning, from non-outcome evidence only

Fold count is a **step function** of session count: 105 → 3 folds, 125 → 4, 145 → 5. Any target in
[105, 124] buys **zero additional folds**. Its entire value is tolerance against *losing* sessions.
So the honest question is only: how many sessions can we expect to lose?

Recorder run history, from `reports/j06-tranche/recording-runs.json` (5 runs, terminal reporting,
which §7.2 requires to carry the disclosed failure list):

| run | pairs attempted | fresh attempts | recorded | failed | elapsed |
|---|---|---|---|---|---|
| 1 | 21 | 21 | 19 | 2 | 1 784.6 s |
| 2 | 80 | 60 | 54 | 6 | 7 104.9 s |
| 3 | 80 | 6 | 4 | 2 | 677.9 s |
| 4 | 80 | 2 | 2 | 0 | 233.1 s |
| 5 | 80 | 1 | 1 | 0 | 180.0 s |

- Transient per-symbol-day failure rate: **10 / 90 fresh attempts = 11.1 %**
- Terminal, unrecovered failures after ≤ 3 resume passes: **0 / 80 symbol-days**
- `unrecovered_disclosed_vendor_failures: []`, `blocking_missing_pairs: {}`
- 2 080 / 2 080 chunks checkpointed; `dataset_list_errors: 0`; `full_session_pct: 100.0`

**A session is lost to the corpus only if every symbol on that date fails terminally.** Observed
terminal rate is 0/80 with a checkpointed, resumable recorder. So the objective failure-driven buffer
is **~0 sessions**, and inventing a percentage buffer on top of a 0 % observed terminal rate would be
fabrication.

The buffer that *is* justified comes from known structural losses, not from failure guessing:

| source | sessions |
|---|---|
| mathematical minimum for block O | 105 |
| discovery block D (needed for a non-empty registry and any Scout re-screen) | 33 |
| **operational target** | **138** |
| headroom above the minimum | 33 sessions of tolerance |

If the availability probe (§5.5) shows the vendor's tick retention starts later than 2025-11-03, the
window shortens from the left and the discovery block absorbs the loss first, down to a hard floor of
105 for block O. **Below 105 in block O the plan stops rather than shrinks** — see §17.

---

## 11. ESTIMATED STORAGE

Basis: the 80 recorded full-RTH symbol-sessions of the existing tranche — the only full-session
evidence that exists. Figures are rounded per §7.5.

**Per full symbol-session (6.5 h RTH, 8-symbol panel mix):**

| statistic | tape on disk | snapshot |
|---|---|---|
| median | ~170 MB | — |
| mean | ~330 MB | ~1 080 MB |
| p90 | ~860 MB | — |
| min / max | ~26 MB / ~1 530 MB | — |

Snapshots are **one row per trade** at **~1 672 bytes/row** (verified: 3 815 933 snapshot rows vs
3 815 915 trades across the 18 exposed shards; 6.38 GB / 3.82 M rows). Full-session snapshot : tape
byte ratio is **~3.25×**.

**Projections, 8-symbol panel:**

| sessions | symbol-days | chunks | tape | snapshots | **total steady state** | transient checkpoints |
|---|---|---|---|---|---|---|
| **105** (minimum) | 840 | 21 840 | ~280 GB | ~910 GB | **~1.19 TB** | ~250 GB |
| 125 | 1 000 | 26 000 | ~330 GB | ~1 080 GB | ~1.41 TB | ~290 GB |
| **138** (target) | 1 104 | 28 704 | ~370 GB | ~1 190 GB | **~1.56 TB** | ~320 GB |

**Available disk today: 116 GB on `/` (286 G total, 156 G used). The repo already holds 63 GB, of
which `.data` is 60 GB.**

**This is the binding constraint of the entire plan — a ~10× shortfall at the mathematical minimum,
before the operational target is even considered.** It is not a rounding risk; it decides whether the
plan is executable.

Three levers, in order of honesty:

1. **Provision storage.** ~1.6 TB working / ~1.2 TB steady. Cleanest, changes no contract.
2. **A snapshot v2 anchor projection.** Snapshots are a *derived, rebuildable* cache keyed on
   `(dataset_checksum, params_hash, feature_source_hash, config_fingerprint)`; the walk-forward needs
   only `{session_date, symbol, value}` per anchor, and Scout's `structure_context: "none"` anchor set
   is candidate-independent. A columnar anchor projection at ~64 B/anchor instead of ~1 672 B/row
   would cut ~910 GB to ~35 GB. Measured: the `deferred` array alone is 31 % of current snapshot
   bytes. **This is a `SNAPSHOT_FORMAT_VERSION` change and therefore a named revision — not designed
   here, and not to be improvised inside the acquisition.**
3. **Wave-and-discard.** Keep the tape (~280 GB), build snapshots per wave, extract observations,
   delete the snapshot. Peak ≈ tape + one wave. Still exceeds 116 GB, so it only helps *after* lever 1
   is partially applied. Caveat: `extract_anchors` treats a missing snapshot as an **honest skip, not
   an error** (`scout.py`: *"a dataset with no currently-valid snapshot is an honest skip, not a
   fabricated row"*), so a discarded snapshot silently shrinks the corpus. Any wave scheme needs an
   explicit completeness assertion.

The checkpoint store (~250–320 GB peak) is transient and deletable after each day finalizes, but it
must fit *concurrently* with the tape during recording.

---

## 12. ESTIMATED RECORDING COST / THROUGHPUT

Measured from the existing tranche — 2 080 checkpoint files and 5 terminal run records:

| quantity | value | source |
|---|---|---|
| chunk size | 900 s (`RECORDER_CHUNK_SECONDS`) | module constant |
| chunks per symbol-day | **26** (6.5 h RTH ÷ 900 s) | `plan_recorder_chunks`; 2 080 = 80 × 26 exactly |
| throttle | `RECORDER_PAGE_BUDGET_PER_MINUTE = 200` → ≥0.3 s between vendor calls | module constant |
| **observed seconds per chunk** | **4.80 s** | 9 980.5 s total elapsed ÷ 2 080 chunks |
| **observed seconds per symbol-day** | **~125 s** | 9 980.5 s ÷ 80 |
| observed active wall-clock, 80 symbol-days | **2.77 h** | sum of `elapsed_seconds` |
| checkpoint size | ~11 MB/chunk mean (median ~5 MB, p90 ~32 MB) | checkpoint store |
| transient failure rate | 11.1 % of fresh attempts | run records |
| terminal failure rate | **0 %** | `unrecovered_disclosed_vendor_failures: []` |

**Projected vendor fetch time:**

| sessions | symbol-days | chunks | active fetch |
|---|---|---|---|
| 105 | 840 | 21 840 | **~29 h** |
| 138 | 1 104 | 28 704 | **~38 h** |

Plus, downstream and separately measured:

- **Snapshot build**: 18 datasets / 3.82 M trades in **7.1 min** ≈ **9 000 trades/s**. At 138 × 8
  symbol-days and ~646 k trades/symbol-day mean, that is **~713 M trades ≈ 22 h** of single-process
  snapshot build.
- **Scout screen**: 6 candidates over 11 sessions / 18 datasets took **8.9–10.5 min**. Scaling is
  roughly linear in anchors; a 6-candidate screen over 138 sessions × 8 symbols is on the order of
  **days**, not minutes, and will need the parallel-sweep treatment era 5C applied to the edge report.
- **Paired bar backfill** for AG, LYFT, WULF (1d + 1h, full history) and SPY (1h): not yet estimated;
  the existing tranche's pairing was 24 outcomes over 80 symbol-days in a few minutes, but that was
  10 dates, not 138.

**One scaling landmine, quantified.** `DatasetStore.list()` re-verifies both checksums for every file
unless the caller passes `index_db_path` — and **only `routes.py:296` does**. Every CLI and module-
level `DatasetStore(dir)` construction (including
`walkforward.run_tick_family_fold_request` and `run_diagnostic_walkforward`'s tick seed) gets the
un-indexed path. Measured today at 27.5 GB on disk:

| construction | `store.list()` |
|---|---|
| `DatasetStore(dir, index_db_path=...)` | **0.00 s** (98 records, 0 errors) |
| `DatasetStore(dir)` | **> 600 s** (timed out) |

At ~370 GB the un-indexed path becomes hours per call — and `run_tick_family_fold_request` calls
`store.list()` **twice** on an un-indexed store (once directly, once inside
`_tick_dataset_session_dates`), so it pays the bill twice per invocation. Confirmed empirically during
this preflight: invoking that function against the real store had not returned after 35 minutes at
today's 27.5 GB. The dataset index is currently 100 % warm (98/98 rows stat-match disk). **Wiring
`index_db_path` into the CLI/module construction sites is a prerequisite, not a nice-to-have** — but note it is a *performance* change only and must be proven
byte-identical, since the index is written only from values the full verifier already produced.

---

## 13. DISCOVERY / OOS / VAULT SEPARATION

### The recommended path: **B, with the discovery block folded into the same corpus era**

Chosen on leakage discipline, not on survivor likelihood.

**Why not PATH A** (grow an exposed discovery corpus → re-run Scout → freeze survivors → then collect
a *separate* OOS corpus):

- It requires **two** recordings, roughly doubling a storage bill that is already the binding
  constraint (~2.4 TB at the minimum).
- Every discovery session it records is burned to class-1 forever, and none of that evidence can ever
  contribute a fold.
- It buys nothing PATH B does not already give: Mode A's rolling-origin design *is* discovery inside
  the training windows.

**Why PATH B**, precisely (§6.4): *"At each origin T: candidate generation, ranking, and threshold
FITTING run only through the origin-T accessor. The frozen spec identity is the fitting RULE … The
validation window is revealed only after the spec hash is recorded; freeze order is in the fold
ledger."* `register_mode_a_origin` implements exactly that order, verified in source:

```
validate_candidate_direction  →  parse_fitting_rule  →  train read  →  unit check  →  fit
  →  compute_spec_hash / spec_hash_recorded_at  →  test read  →  unit check
  →  classify_evidence_class  →  summarize  →  append_fold_result
```

So discovery happens *inside* the training windows of the same corpus, and the validation windows stay
unexposed until after the spec freezes. One recording, correct classes, and no separate discovery
corpus to burn.

### Evidence class carried by each window, per path

| | PATH A | **PATH B (recommended)** |
|---|---|---|
| discovery corpus / block D | `historical_exposed_diagnostic` — permanently | `historical_exposed_diagnostic` — permanently |
| Scout screens run on it | `historical_exposed_diagnostic` (hardcoded, `scout.py:1291`) | same |
| Mode A **train** windows | n/a | no class — training windows are unclassified by design |
| Mode A / Mode B **test** windows | `historical_oos` **only if** every session is unexposed under the new corpus id at the spec's `registered_at` | `historical_oos` by construction of the freeze order + a clean corpus id |
| sealed shards | `historical_oos` + `rule_process` required by `SEALED_PASS_RULE_V1` cond. 5 | same |

### What to do about the zero current survivors

Nothing, deliberately. All six real Scout candidates are unsided (`sidedness: null`) exploratory
screens on a 3-session-equivalent corpus; three died at the null, one at n, two at the economic floor.
Their information value for PATH B is that **F-LIQUIDITY is the family that reached the econ floor at
all** (`quote_imbalance` measured 0.1462 bps against a 1.5262 bps floor — it lost, but it lost on
magnitude rather than on the null) and that F-FLOW/F-RESPONSE evidence is the part most damaged by the
0.62 fallback fraction. That is context for what to predeclare, not a result.

`SCOUT_MAX_VARIANTS_PER_FAMILY` budget note: `family_id` is `feature__contextkind__horizon` and is
**not** corpus-scoped, while `candidate_id` **is** (the `corpus_manifest` is inside `spec_hash`). So
re-screening the same thresholds on the new corpus mints new variants that count against the same
24-per-family cap. Current usage is 4/24 in each of three families. A re-screen takes each to 8/24.
Budget it; do not discover it at registration time.

### Vault separation

The new era registers **its own universe** over block O's dates, with its own nonce, its own
`rule_commitment`, its own vault-secret commitment and its own HMAC assignment. The existing
`rapid-microscope-j06-starter` universe, its 21 sealed shards, its screen provenance and its one
disclosure incident are **not touched, not re-registered, not re-sealed and not exposed**.

---

## 14. LABEL-QUALITY POLICY

**Does any pre-existing spec rule allow excluding a session on `fallback_frac`? No.**

Every consumer of `fallback_frac` in the codebase, enumerated:

| site | use |
|---|---|
| `micro_readiness._compute_fallback_frac` / cache | computes and caches the per-shard value |
| `micro_readiness` per-shard row | serves it |
| `micro_readiness._label_quality` | aggregates it — `_FALLBACK_FRAC_DISCLOSURE_THRESHOLD = 0.5` is used **only** to count `shards_majority_inferred` |
| `scout._fallback_tercile_slices` | stratifies a screened result into low/mid/high terciles |

Zero filters, zero thresholds that drop a session, zero gates. The code says so in its own words:
*"All of it is a DISCLOSURE — nothing gates on it"* and *"The threshold is a plain MAJORITY — not a
tuned number, and it GATES NOTHING."* Spec §5.4 agrees and adds the family scoping.

**Therefore, stated plainly as the policy for this acquisition:**

> **We record the registered universe completely and report `fallback_frac`. We do not cherry-pick
> low-fallback sessions afterward.**

No new threshold is created. The family distinction stands unchanged:

- **F-FLOW / F-RESPONSE** (cumulative delta, imbalance, runs, bursts, impact efficiency, failed
  aggression) read the engine's aggressor side classification — aggressor-label fallback is a
  **material caveat**, and the per-candidate fallback-tercile stratification is the mechanism that
  handles it.
- **F-LIQUIDITY** (quote imbalance, microprice, spread change) never reads `side` at all — a high
  corpus-wide `fallback_frac` is **not** evidence that an F-LIQUIDITY result, or the corpus as a
  whole, is weak.

The 0.6171 trade-weighted figure on the current corpus is a fact to report beside every F-FLOW /
F-RESPONSE result, not a reason to select dates.

---

## 15. PRE-REGISTRATION ACTS REQUIRED

Ordered. Each must complete before the next begins; several are code changes that must land and be
proven byte-identical **before** anything is registered.

**Code, before registration:**

1. **Wire exposure logging into the new corpus's observation reads** (§4.3). Today `log_exposure` has
   no production call site; `classify_evidence_class` has no `has_any_exposure_entries` guard, so an
   unpopulated registry grants `historical_oos` to everything. Without this the OOS claim rests on
   freeze-order alone and a second spec could re-claim the same window.
2. **Build the tick observations reader.** None exists — the only readers are
   `walkforward.playbook_observations` and `referee_evidence.playbook_observations`, both bar-corpus.
   It is a thin adapter (`extract_anchors` already returns `session_date`, `symbol`, `outcome_bps`)
   producing `{session_date, symbol, value, value_unit: "return_bps"}`, but it must exist and be
   unit-proved before a fold can be evaluated on tick data.
3. **Parameterize the corpus id and the operator bridge.** `walkforward.run_tick_family_fold_request`
   is hardcoded to `TICK_LEGACY_CORPUS_ID`; `scripts/j06_operator.py` hardcodes `UNIVERSE_ID`,
   `SYMBOL_RULE` and `DATE_RULE`. A second era needs these as parameters, with the legacy constants
   left byte-unchanged.
4. **Wire `index_db_path` into CLI/module `DatasetStore` constructions** (§12). Performance only;
   must be proven byte-identical.
5. **Resolve the storage decision** (§11) — provision, or land a snapshot v2 named revision, or
   design an explicit wave-and-discard with a completeness assertion. **Do not start recording until
   this is settled.** A recording that dies at 70 % on ENOSPC leaves a half-corpus that cannot be
   registered as complete under §7.2's "complete output net of disclosed vendor failures".

**Registration acts, in order:**

6. **Fold spec** for `rapid-microscope-tick-oos-v1`: `DIAGNOSTIC_GEOMETRY` verbatim,
   `clustering_unit: "session_date"`, floors from §1, `corpus_manifest_hash` over the frozen 138-date
   list — registered *before* fold 1, per §6.2.
7. **Block D / block O split**, frozen with the fold spec. Predeclared, not chosen after any read.
8. **Predeclared candidate set**: either the Mode A fitting rules (`training_quantile(q)` — the only
   family `parse_fitting_rule` accepts) or the three pilot studies
   (`pilot_study_candidate_grid` is already wired in `scout.py` for all three
   `structure_context.kind` values). Registered before block O is touched.
9. **New recording universe** over block O's dates: reuse the frozen Tier-B resolution
   (`rapid-microscope-tier-b-r11`, artifact `fb89c5a2…`) — **no re-screen**, per §7.2.1(j) — new
   nonce, new `rule_commitment`, new vault-secret commitment, new HMAC assignment.
10. **Paired bar backfill** for AG, LYFT, WULF (1d + 1h) and SPY (1h) over the window, so band-context
    joins resolve.

---

## 16. EXACT OPERATOR COMMAND SEQUENCE

Nothing below has been run. Steps 1–5 of §15 must land first.

```bash
cd /home/dennis-chan/Git/tapeology/apps/backend

# ── 0. AVAILABILITY PROBE — costs nothing, settles §5.5 ────────────────────────────────
#    Probe on an ALREADY-BURNED screening date so no clean date is touched.
#    One symbol, one 900 s chunk. Confirms Alpaca SIP tick retention reaches 2025-11.
.venv/bin/python -m scripts.<probe> --symbol PG --date 2026-08-14 --chunks 1   # burned date
.venv/bin/python -m scripts.<probe> --symbol PG --date 2025-11-03 --chunks 1   # earliest target
#    STOP if the second returns empty or 4xx — re-derive the window from actual retention.

# ── 1. Freeze the date list from the predicate (operator-private) ──────────────────────
.venv/bin/python -m scripts.<new_operator> dates --from 2025-11-03 --through 2026-05-26

# ── 2. Register the fold spec + block split, BEFORE any recording ──────────────────────
.venv/bin/python -m scripts.<new_operator> foldspec --corpus rapid-microscope-tick-oos-v1

# ── 3. Predeclare the candidate rules (ledgered, before any outcome read) ──────────────
.venv/bin/python -m scripts.<new_operator> predeclare

# ── 4. Register the new universe over block O (reuses the frozen Tier-B resolution) ────
.venv/bin/python -m scripts.<new_operator> register
.venv/bin/python -m scripts.<new_operator> preflight

# ── 5. Record — resumable; expect ~38 h active, ~11 % transient failures, retry to zero ─
.venv/bin/python -m scripts.<new_operator> record          # re-run until failed == 0
.venv/bin/python -m scripts.<new_operator> verify          # TR-4 batch acceptance

# ── 6. Paired bar backfill for the four symbols missing 1d/1h over the window ──────────
.venv/bin/python -m app.research.desk_deep_backfill --symbols AG,LYFT,WULF,SPY \
    --from 2025-11-03 --through 2026-05-26 --timeframes 1d,1h

# ── 7. Snapshots (the ~22 h step; storage decision from §11 must already be applied) ────
.venv/bin/python -m app.research.micro_snapshots --build

# ── 8. Readiness — expect study_floors floor_met and session_equivalents ≈ 138 ──────────
curl -s localhost:8301/research/desk/micro/readiness | jq '.totals, .study_floors'

# ── 9. Discovery on block D only, then folds on block O ────────────────────────────────
.venv/bin/python -m app.research.scout --grid pilot --corpus rapid-microscope-tick-oos-v1 --block D
.venv/bin/python -m app.research.walkforward --corpus rapid-microscope-tick-oos-v1
```

`<probe>` and `<new_operator>` are the code items from §15 steps 1–3; they do not exist yet. The
`--block` / `--corpus` flags likewise do not exist yet. **This sequence is a specification for the
next step, not a runnable script today.**

---

## 17. RISKS

| # | risk | severity | evidence | mitigation |
|---|---|---|---|---|
| R1 | **~1.19 TB needed at the minimum; 116 GB free** | **blocking** | measured, §11 | settle §15 step 5 before recording; do not start a recording that cannot complete |
| R2 | **Alpaca tick retention may not reach 2025-11-03** | high | unverifiable in preflight, §5.5 | §16 step 0 probe on a burned date, before anything is registered |
| R3 | **`historical_oos` currently granted by an empty registry** | high | `log_exposure` has no production call site, §4.3 | §15 step 1; without it the OOS claim rests on freeze-order alone |
| R4 | Un-indexed `store.list()` re-verifies the whole corpus | high | 0.00 s indexed vs >600 s un-indexed at 27.5 GB | §15 step 4; byte-identical proof required |
| R5 | No tick observations reader exists | high | grep, §15 step 2 | build it; unit-prove it |
| R6 | AG/LYFT/WULF have no 1d/1h bars; SPY no 1h | medium | measured, §8 | §16 step 6 before any band-context join |
| R7 | Snapshot build ~22 h single-process; Scout screen scales to days | medium | 9 000 trades/s measured | parallelize as era 5C did for the edge report; budget the time |
| R8 | Publishing the window bounds weakly discloses the withheld date axis | medium | §6 disclosure note | keep the concrete date list operator-private; register from the predicate |
| R9 | Variant budget: re-screen takes each family 4/24 → 8/24 | low | `corpus_manifest` inside `spec_hash`, §13 | budget the grid before registering |
| R10 | Retrospective corpus carries the §7.7 bar-reconstructibility caveat | low, standing | §4.2 | report the diagnostic beside every sealed verdict; never let it gate |
| R11 | A discarded snapshot silently shrinks the corpus | low unless lever 3 is used | `extract_anchors` treats a missing snapshot as an honest skip | explicit completeness assertion in any wave scheme |
| R12 | Label quality on the new corpus may match the current 0.62 fallback | medium, scientific | measured, §1.1 | report it; **do not** select dates on it (§14). F-LIQUIDITY is unaffected |

---

## 18. STOP CONDITIONS

Halt and escalate rather than adapt, in every one of these:

1. **Block O cannot reach 105 unbarred sessions** — from vendor retention, a new exposure entry, or
   any other cause. Do not lower the floor, do not shorten the geometry, do not reuse an exposed date.
2. **Storage cannot be provisioned and no lawful storage lever lands.** Do not start a recording that
   cannot finish; a partial pool cannot be registered as complete under §7.2.
3. **The availability probe returns short retention.** Re-derive the window from actual retention and
   re-run this preflight's §5 — do not slide the window into barred dates.
4. **Any vault chain fails `verify_chain()`.** §7.8 is absolute: fail closed, halt all vault work, and
   recover only against pre-existing trusted commitments. Row-count equality never authorizes
   recovery.
5. **A `legacy_dataset_collision` appears at a registered pair.** Repair by completion into the same
   universe with the original nonce — never substitution, never a second universe.
6. **A pool-position disclosure occurs.** Record the incident in the disclosure ledger, re-run TR-2
   with the disclosure treated as attacker-known, and never disclose a second position to balance it.
7. **Terminal vendor failures leave any registered pair without a genuine shard.** Disclose per §7.2.2
   with run evidence; never derive `disclosed_failures` by subtracting recorded from expected.
8. **Any temptation to re-screen Tier-B, substitute a symbol, or widen the panel.** §7.2.1(j): STOP.
9. **Any proposal to exclude a session on realised `fallback_frac`, or on any realised outcome.** §14:
   that is a selection degree of freedom this era has not predeclared.

---

## 19. NEXT IMPLEMENTATION / OPERATOR STEP

**One decision, then one probe. Nothing else should start.**

1. **Operator decision — storage (R1).** Provision ~1.6 TB, or authorize a snapshot v2 named revision,
   or authorize a wave-and-discard design. This decision gates everything downstream and is not mine
   to make.
2. **Then the availability probe (R2)**, on the already-burned date `2026-08-14` first and
   `2025-11-03` second. One symbol, one chunk each. It costs one burned date that is already
   permanently barred, and it settles whether the 138-session window exists at all.

Only after both: §15 code items 1–4, then registration.

**Nothing in this plan lowers a floor, changes a geometry, alters the economic floor, re-screens
Tier-B, touches the sealed vault, or relabels existing evidence.**
