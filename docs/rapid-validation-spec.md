# The Rapid-Validation Spec — microstructure candidates, chronological validation, and the vault

> **This file is the single source of the Rapid Microscope era's methodology: every constant,
> contract, fold rule, sealing rule, ledger schema, graduation gate, and trap test is fixed here
> BEFORE the code that uses it.** Developers implement from this spec verbatim; a developer who
> finds a rule ambiguous or unimplementable DROPS the procedure from the iteration and surfaces it
> for an owner ruling — never improvises. A change to anything here is a **named revision** that
> re-keys future results beside old ones (new spec ids / parameter hashes), never an edit of
> recorded meaning. Nothing here is ever tuned from outcomes. The Referee's own spec
> (`docs/referee-statistical-spec.md`) is untouched and outranks this file wherever both speak
> about confirmatory claims.
>
> **Revision r2 (2026-08-16, pre-implementation).** A narrow named revision applied BEFORE any
> artifact was recorded under r1 — so nothing re-keys; r1 never produced a record. r2 adds: the
> availability law (`anchor_at` / `observed_through` / `available_at`, §0/§2.2); the dataset
> schema-basis + quote-size-unit contract (§2.6, superseding Card 5.1's universal "round lots"
> pin — Alpaca CTA/UTP displayed quote sizes are SHARES from 2025-11-03); the Card-5.1
> data-preservation prerequisite on the recorder (§7.1); every remaining Wave-1 degree of
> freedom frozen as a §1 constant (refill M, response K, burst baseline, depletion window,
> impact-flatness formula, divergence trailing window + δ); mid-only primary outcomes with a
> separate last-trade sensitivity basis (§4); `family_root_id` lineage for single-shot sealed
> evidence (§5.1/§7.4); opaque pre-exposure vault metadata (§7.5); the deterministic exposure
> registry + human/agent rules for `historical_oos` (§6.7); `rule_process` vs
> `operator_process` sequence labels (§6.8); frozen clustering semantics and the explicit
> `WF_SURVIVOR_RULE_V1` (§6.2/§6.6); and traps TR-17–TR-22 (§9).
>
> **Revision r3 (2026-08-18, owner ruling — sealed-shard join resistance).** A narrow named
> revision applied while ZERO shards are sealed, so nothing re-keys and no recorded verdict
> moves. The iteration-9 audit proved r2's §7.5 opacity is defeated in one hop: the served
> `shard_id` was the `DatasetStore` dataset id, so `GET /research/datasets/{id}` (and the
> `datasets` MCP tool, `get_endpoint`, and `micro_readiness`'s per-shard rows) returned the
> sealed shard's symbol, window and event counts. r2 already REQUIRED an "opaque `shard_id`",
> so that part was a compliance gap, not a spec gap — but r2 also MANDATED serving the
> `checksum commitment`, which is itself an equally good join key against the public dataset
> record. Resolving that tension is a genuine methodological change, hence this revision.
> r3 replaces §7.5's identity rules (surrogate ids, salted pre-exposure commitment, explicit
> refusal on the pre-existing dataset surfaces) and widens TR-2 from a field-whitelist sweep to
> a join-resistance sweep. Owner ruling recorded 2026-08-18; the alternatives considered and
> rejected were a separate sealed store path (strongest, largest build) and accepting the leak
> with a documented caveat (cheapest, materially weaker vault).
>
> **Revision r4 (2026-08-18, owner ruling — corpus enumerators honour the seal).** Applied while
> ZERO shards are sealed, so no recorded report or ledger row changes. The iteration-9 re-audit
> proved r3's refusals are route-scoped and therefore bypassable: `edge_report._all_datasets`
> and `pnl_scan._split_datasets` each enumerate the WHOLE store through their own
> `DatasetStore.list()` and drive `BacktestJobManager` directly, so a corpus-wide report would
> read a sealed shard's events and republish its id, raw checksum and outcome aggregates through
> `GET /research/backtests` and the append-only PnL ledger. r4 adds §7.5 point 6: enumerators
> EXCLUDE withheld shards and DISCLOSE the exclusion. This is a derivation, not a free choice —
> goal.md's critical rail already says event data and outcome aggregates of a sealed shard are
> "refused everywhere… fail-closed", and both call sites already carry the honesty convention
> that "a partial report is a misleading report", which forbids the silent variant. Rejected:
> aborting a whole sweep whenever any sealed shard exists (renders the edge report unusable the
> moment the vault holds anything) and accepting the bypass (re-opens exactly what r3 closed).

---

## 0. Shared conventions

- **Units.** Returns/moves in percent or bps as named per field; side-signed where a hypothesis
  side exists (positive = the thesis direction), stated per field. Shares are integer counts.
- **Sessions.** A session is an ET RTH trading date (`session_date`); the desk's session-honesty
  module (`desk_sessions.py`) is the arbiter of what counts as a session.
- **Determinism.** Every random draw uses `random.Random` streams under the recipe
  `f"{MICRO_SEED}:{scope_id}:{purpose}[:{fold_or_origin}[:{i}]]"` — no global RNG, no wall-clock,
  no unseeded randomness in any persisted artifact. Identical inputs reproduce byte-identical
  outputs.
- **Read-side law.** Every module this spec governs READS the frozen product (engine, detectors,
  band context, referee) and never feeds back into any of it. The engine-derived aggressor side
  and window features are consumed from the replay snapshot — never recomputed.
- **The availability law (r2).** Every feature value carries three instants: `anchor_at` (the
  event/moment the value describes), `observed_through` (the last event consumed to compute it),
  and `available_at` = the instant of `observed_through` (never earlier than `anchor_at`). A
  prefix feature has `observed_through = anchor_at`. A deferred construct — anything requiring
  later observations, e.g. `refill_consistent` (needs `REFILL_M_QUOTES` subsequent quotes) or
  response-over-K-trades (needs `RESPONSE_K_TRADES` subsequent trades) — becomes available only
  when those observations exist: it is written at its `observed_through` row, referencing its
  `anchor_at`, and is `unavailable` (counted, never guessed) when the session ends first.
  **Outcomes for a conditioned anchor begin at or after the conditioning feature set's maximum
  `available_at`** — never at `anchor_at` when the condition looks later. TR-17 enforces all of
  this deterministically.
- **Evidence classes** (stamped on every served study/fold/screen output; the era's spine):

| Class | Definition | Maximum claim it can carry |
|---|---|---|
| `historical_exposed_diagnostic` | Computed over a corpus whose outcomes were inspectable before the evaluated spec was frozen (today: the whole playbook bar corpus; the 12 legacy tick symbol-days) | Machinery works; temporal-stability DIAGNOSTICS. Zero graduation credit, zero gate satisfaction, never confirmation. |
| `historical_oos` | Spec frozen and registered FIRST, then evaluated on data whose relevant outcomes were not inspectable at freeze time (clean-horizon folds; sealed vault shards) | "Historically repeated out of sample under a frozen spec." Eligible for graduation gates. |
| `live_confirmatory` | Genuinely new sessions after a Referee registration boundary | The Referee's territory exclusively; this era's machinery never emits it. |

  Classes never mix in one pooled statistic; every payload carries `evidence_class` verbatim.

---

## 1. Pre-registered constants (module constants in `micro_*.py`; NEVER `Config` fields)

| Constant | Value | Meaning |
|---|---|---|
| `MICRO_SEED` | `314159` | Root seed for every stream in this family |
| `MICRO_ALGO_VERSION` | `1` | Bumps only as a named revision |
| `SNAPSHOT_FORMAT_VERSION` | `"micro-snapshot-v1"` | The snapshot representation chosen by the §2.4 benchmark; a representation change is a new version, old snapshots stay readable-or-refused, never rewritten |
| `MICRO_HORIZON_TRADES` | `(20, 100)` | Event-time outcome horizons (trades after anchor) |
| `MICRO_HORIZON_SHARES` | `(5_000, 50_000)` | Volume-time outcome horizons (shares after anchor) |
| `MICRO_HORIZON_CLOCK_SECONDS` | `(30, 60, 300)` | Clock outcome horizons; **no sub-second horizon exists** (DO-NOT #1) |
| `SCOUT_BLOCK_PERMUTATIONS` | `2_000` | Draws for the §5.3 screening null |
| `SCOUT_SCREEN_ALPHA` | `0.05` | Descriptive screening level for kill/advance ranking — never a confirmatory claim |
| `SCOUT_MAX_VARIANTS_PER_FAMILY` | `24` | Hard grid bound per (family, corpus), counted over the UNION of all grid versions ever run there |
| `ECON_FLOOR_SPREAD_MULTIPLE` | `1.0` | The §5.5 economic-relevance floor = this multiple × the family's median quoted spread (bps) at its discovery anchors. **A research cost PROXY, not an execution or tradability model** — served with that sentence |
| `WF_TRAIN_MIN_SESSIONS` | `40` | Fold-geometry floor |
| `WF_TEST_MIN_SESSIONS` | `20` | Fold-geometry floor |
| `WF_MIN_SUFFICIENT_FOLDS` | `3` | Below this, sequence-level refusal |
| `WF_FOLD_MIN_SIGNAL_SESSIONS` | `8` | Per-fold floor: validation sessions carrying ≥1 observation |
| `WF_FOLD_MIN_OBSERVATIONS` | `30` | Per-fold floor |
| `WF_FOLD_MIN_SYMBOLS` | `2` | Per-fold floor whenever symbol breadth is claimed |
| `DIAGNOSTIC_GEOMETRY` | `train=40, embargo=5, test=20, step=20` | Pinned geometry of the ONE playbook-corpus diagnostic acceptance run (§6.6). The `embargo=5` here is that run's predeclared choice, not a universal law — see §6.3 |
| `VAULT_SEAL_HEX_BELOW` | `4` | Seal iff the last hex digit of the §7.3 HMAC < 4 (≈25% of a universe) |
| `TRANCHE_MINIMUMS` | §7.6 table | The starter-tranche diversity floors |
| `RECORDER_PAGE_BUDGET_PER_MINUTE` | `200` | Tick-fetch throttle (the bar path's discipline, applied to the tick path at last) |
| `KILL_REASONS` | `("killed_null", "killed_direction", "killed_insufficient_n", "killed_concentration", "killed_economic", "killed_fragile", "superseded")` | The CLOSED kill vocabulary; free-text goes in `notes`, never in `reason` |
| `MICRO_FEATURE_WINDOW_TRADES` | `(20, 100)` | Event-time FEATURE windows (deliberately separate constants from the outcome horizons) |
| `MICRO_FEATURE_WINDOW_SHARES` | `(5_000, 50_000)` | Volume-time feature windows |
| `REFILL_M_QUOTES` | `20` | `refill_consistent` observation window: same-side quote updates after the execution; `available_at` = the M-th update; session-end first ⇒ `unavailable` |
| `RESPONSE_K_TRADES` | `20` | Response-asymmetry window: trades after the print; `available_at` = the K-th trade |
| `BURST_BASELINE_TRAILING_WINDOWS` | `20` | Burst baseline = median of this many prior non-overlapping same-length windows in the SAME session prefix; fewer than `5` ⇒ burst undefined (counted) |
| `DEPLETION_WINDOW_QUOTES` | `20` | Quote-depletion observation bound: consecutive same-side quote updates at an unchanged price; ends at a price change or the bound; `available_at` = window end |
| `IMPACT_FLATNESS_SCALE_BPS` | `5.0` | The frozen flatness scale: `flatness = clamp(1 − |Δmid_bps| / 5.0, 0, 1)`; `failed_aggression_score = dominant_side_volume_share × flatness` per feature window |
| `DIVERGENCE_TRAILING_SECONDS` | `120.0` | Divergence-at-level price/volume window: TRAILING `[τ − 120s, τ]`, as-of the touch — supersedes Card 9.1's symmetric "window around the touch"; `available_at` = τ |
| `DIVERGENCE_DELTA_VOLUME_FRACTION` | `0.25` | Card 9.1's δ fraction, frozen HERE as a module constant (never a Config field): `δ = 0.25 × median trailing-120s volume` over the session-prefix baseline windows |
| `QUOTE_SIZE_UNITS` | `("shares", "round_lots", "unverified")` | The dataset-level size-unit vocabulary (§2.6) |
| `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` | `"2025-11-03"` | Vendor-documented rule the recorder stamps from: Alpaca CTA/UTP displayed quote sizes are SHARES for windows on/after this date, ROUND LOTS before it; re-verify against vendor docs at recording time and record the verification |
| `WF_SURVIVOR_SIGN_CONSISTENCY` | `0.7` | The §6.6 survivor rule's fold-sign agreement floor |

Every value above was chosen on 2026-08-16, before any outcome was read — arbitrary-but-frozen;
a change to any of them is a named revision, never a tuning act.

Every record embeds the constants it used verbatim (`micro_parameters()` — the desk pattern) and
keys on their hash; a monkeypatched constant must move the parameters hash AND the result identity
(counter-tested).

---

## 2. The observer contract (`micro_observer.py` + `micro_snapshots.py`)

### 2.1 Attachment
`DatasetStore.replay(dataset_id, config)` gains an additive, default-`None` `observer=` kwarg that
calls the engine's existing `TapeEngine.add_observer` seam before the event loop. `observer=None`
is byte-identical to today (the engine's observer-equivalence test already proves snapshots are
unaffected; a counter-test pins the kwarg default). **No second replay implementation exists.**

### 2.2 The prefix law (streaming-only state) + availability (r2)
Snapshot row *i* is a pure function of events `1..i` (plus the engine snapshot after event *i*).
The writer flushes row *i* before consuming event *i+1*. **No whole-dataset normalizer, baseline,
calibration, or end-of-session statistic may enter any row.** Session-anchored accumulations
(cumulative delta) are legal because the anchor precedes every row. Event-time baselines use only
prior events. Deferred constructs (§0 availability law) are written at their `observed_through`
row referencing their `anchor_at` — never attached retroactively to an earlier row. Enforced by
the TR-1 prefix/tail traps and the TR-17 availability trap (§9).

### 2.3 Snapshot identity and verification
Snapshot key = `(dataset_id, dataset_checksum, MICRO_ALGO_VERSION, SNAPSHOT_FORMAT_VERSION,
feature_source_hash, config_fingerprint, params_hash)` where `feature_source_hash` =
sha256 over the feature-module bytes. The loader re-verifies `dataset_checksum`,
`config_fingerprint`, and `feature_source_hash` on every read and refuses on mismatch
(the `DatasetIntegrityError` discipline). Snapshots are derived, append-only, rebuildable, and
own nothing. Every persisted feature value carries `anchor_at`, `observed_through`, and
`available_at` (§0); prefix features may encode the three compactly, deferred features never.

### 2.4 Granularity is decided by measurement, not assumption
Before any snapshot format is frozen, J-02 runs a benchmark on ≥2 real datasets including the
largest (NVDA `72ca8bc0`, 1.97M events): candidate representations (per-event rows; per-event
sampled-at-anchors; fixed-stride event blocks) are measured for bytes-on-disk amplification vs
the raw dataset, one-pass build time, and anchor-query latency. The chosen representation and the
measured numbers are recorded in the J-02 handoff and pinned as `SNAPSHOT_FORMAT_VERSION`.
Per-event rows are NOT presumed — the raw corpus is already ~1 GB and the tranche corpus will be
multiples of that.

### 2.5 Reuse table (compute nothing twice)
Read from the engine snapshot, never re-derived: aggressor side (+ its `side_source`: `quote_rule`
| `tick_test` | `carried` | `unknown`), the five-window features (`aggressive_*`,
`net_aggressive_volume`, `buy/sell_price_impact`, `average_spread`, `absorption_score`,
`bid/ask_refresh_score`, `reference_price`), tape state, bid/ask/spread/last. New research
features (§3) are additive representations the engine does not compute.

### 2.6 The dataset schema-basis + size-unit contract (r2)
Every NEWLY recorded dataset carries two manifest fields, stamped at record time:
- `schema_basis` — the event-row schema version, including whether the optional Card-5.1
  preservation fields (§7.1) are present;
- `quote_size_unit` ∈ `QUOTE_SIZE_UNITS` — stamped from the dated vendor rule
  (`ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`: Alpaca CTA/UTP displayed quote sizes are SHARES for
  windows on/after 2025-11-03, ROUND LOTS before; the recorder records the rule text + the
  verification note beside the stamp).

Every LEGACY dataset (all 18 on disk) is `quote_size_unit: "unverified"` until a recorded,
auditable verification act says otherwise — never a silent relabel. **The old universal "SIP
quote sizes are round lots" pin (Card 5.1 / trap T12) is superseded by this per-dataset
contract.**

Consequences, fail-closed: features that compare quote sizes only to quote sizes within one
dataset (quote imbalance, microprice) are unit-invariant and always legal; **any cross-basis
feature relating trade SHARES to displayed liquidity — execution-vs-replenishment, any
share-denominated depletion/replenishment magnitude, any trade-share/displayed-size ratio — is
REFUSED with a typed error unless the dataset's `quote_size_unit` is verified**, and any pooled
statistic across datasets of mixed units is refused outright (TR-18). Unit normalization exists
only as a recorded verification act (a named, auditable manifest annotation), never as silent
arithmetic in a feature path.

---

## 3. Feature families (Wave 1 — L1 only)

Per-row disclosures everywhere: `side_source`, and per-window `fallback_frac` (share of trades
classified by the tick test rather than the quote rule — measured 29–76% on the current corpus)
and `unknown_frac`. Any aggressor-derived quantity is served beside those two fractions.

- **F-FLOW** — per-print signed volume (engine side × size); session-anchored cumulative delta
  `CD_t = Σ_{i≤t, side_i≠unknown} sign(side_i)·size_i` (Card 9.1's accumulator verbatim;
  unknowns excluded and counted); rolling imbalance over the `MICRO_FEATURE_WINDOW_TRADES` /
  `MICRO_FEATURE_WINDOW_SHARES` event-time windows beside the engine's clock windows; same-side
  run length at anchor (consecutive prints with the same engine side; `unknown` breaks the run;
  the anchor print counts); volume burst = window volume ÷ the median of the prior
  `BURST_BASELINE_TRAILING_WINDOWS` non-overlapping same-length windows of the SAME session
  prefix (fewer than 5 ⇒ undefined, counted). **Divergence-at-level (Card 9.1, amended r2)**:
  at consecutive touches τ1 < τ2 of the same recorded band, bearish divergence iff
  `price_extreme(τ2) > price_extreme(τ1)` AND `CD(τ2) ≤ CD(τ1) − δ`, where `price_extreme(τ)`
  = the max/min mid over the TRAILING window `[τ − DIVERGENCE_TRAILING_SECONDS, τ]` (as-of,
  never symmetric) and `δ = DIVERGENCE_DELTA_VOLUME_FRACTION × median trailing-120s volume`
  over the same session-prefix baseline windows; `available_at = τ`. Prefix features all carry
  `available_at = anchor_at`.
- **F-RESPONSE** — impact efficiency = signed mid move (bps, aggressor-signed) per 1,000
  aggressive shares over a feature window; efficiency trend = current window efficiency minus
  the prior non-overlapping same-length window's (the exhaustion signature: rising aggression
  with falling efficiency); failed aggression = the engine's `absorption_score` (reused)
  plus the continuous complement, pinned as
  `failed_aggression_score = dominant_side_volume_share × clamp(1 − |Δmid_bps| /
  IMPACT_FLATNESS_SCALE_BPS, 0, 1)` (dominant share = max(buy, sell) ÷ directional volume,
  0.0 when none); **response asymmetry** = the signed mid move over the `RESPONSE_K_TRADES`
  trades after a buy-aggressive vs a sell-aggressive print — a DEFERRED construct:
  `observed_through` = the K-th subsequent trade, `available_at` there, `unavailable` when the
  session ends first.
- **F-LIQUIDITY** — spread level (engine) and spread change (feature-window mean minus the
  prior non-overlapping same-length window's); quote imbalance
  `(bid_size − ask_size)/(bid_size + ask_size)` and microprice
  `(ask·bid_size + bid·ask_size)/(bid_size + ask_size)` — both instantaneous at the in-effect
  NBBO and as feature-window means, and both unit-invariant WITHIN a dataset (legal at any
  `quote_size_unit`); quote depletion = the drawdown of same-side displayed size across
  consecutive quote updates at an unchanged price, observed over at most
  `DEPLETION_WINDOW_QUOTES` updates (ends at a price change or the bound; a DEFERRED
  construct, `available_at` = window end); replenishment (`refill_consistent`: displayed size
  restored at the same price within the next `REFILL_M_QUOTES` same-side quote updates after
  executions against it — a DEFERRED construct, `available_at` = the M-th update or
  `unavailable`; **the ONLY permitted label** — "iceberg", "institutional", "spoof" and any
  intent language are banned); execution-vs-replenishment ratio (executed trade volume at a
  price ÷ displayed-size restoration there, windowed) — **CROSS-BASIS: refused unless the
  dataset's `quote_size_unit` is verified (§2.6)**, as is any share-denominated
  depletion/replenishment magnitude.

Quote sizes reach the observer on `QuoteEvent` rows — they are dropped only inside the engine's
`FeatureEngine`, which this spec does not touch.

---

## 4. Outcomes (the closed set)

For an anchor event: forward **mid-price** move (quote mid at the horizon boundary minus mid at
the outcome start) at every horizon in §1's three horizon families; session-truncated with
truncation flagged and truncated rows excluded from averages (the playbook rail's honesty rule);
side-signed when a hypothesis side exists. **Mid is the ONLY primary basis (r2)**: a row lacking
a quote mid at either end is `unmeasured` — excluded and counted, never silently measured off
the last trade. A separately named `last_trade_basis` outcome column MAY be served beside the
primary as a sensitivity reading; it is never pooled with, substituted for, or averaged into
the mid-basis primary. **Outcome start = the conditioning feature set's maximum `available_at`**
(= `anchor_at` when every conditioning feature is prefix; strictly later for deferred
constructs) — TR-17(c) enforces it. Quoted spread at the outcome start (bps) is served beside
every outcome as the cost-proxy column — never netted into the outcome silently. No sub-second
horizon exists anywhere.

---

## 5. The Scout and the exploratory candidate ledger (`scout.py`, `scout_ledger.py`)

### 5.1 Candidate spec (frozen at ledger append)
`{candidate_id, family_id, family_root_id, feature: {name, transform, params},
structure_context: {kind: "playbook_signal"|"band_touch"|"none", …frozen references},
outcome: {horizon_key, sidedness}, fitting_rule?: <a named rule string, §6.4>, econ_floor:
{multiple, family_median_spread_bps, floor_bps, proxy_sentence}, corpus_manifest:
[dataset/record ids + checksums], grid_version, registered_at, spec_hash}`.

**`family_root_id` (r2) is COMPUTED, never declared**:
`sha256(canonical(feature_family_name, structure_context_kind, outcome_horizon_family))[:16]`.
Every renamed, re-parameterized, or derived family with the same triple computes the SAME root —
so the single-shot sealed-exposure key (§7.4) cannot be reset by renaming, and every export
bundle's lineage is canonical (TR-20).

### 5.2 The ledger
Hash-chained append-only JSONL (the `desk_playbook_log.py` pattern): every evaluated variant —
including every kill — is one permanent row carrying its result summary, `decision:
survive|<KILL_REASONS>`, `reason` (closed vocabulary), `notes`, and the family's running
`variants_tried` (the union-N denominator across all grid versions). Rows are never rewritten;
`superseded` rows point at their successor. Tamper = chain-verification failure (TR-11).

### 5.3 Screening procedure (descriptive, never confirmatory)
Cluster unit = `session_date` for BOTH families, always — **frozen, corpus-size-invariant
(r2)**; symbol-day breadth is a served disclosure beside it, never an alternative clustering.
Effect = mean of session-cluster mean deltas (candidate cell vs its comparator).
Null = **within-session circular block permutation** with block length ≥ the label span in events
of the longest horizon evaluated (computed per session, ceiling) — a plain row shuffle is BANNED
(anti-conservative under overlapping labels; TR-8 calibration trap pins pass-rate ≤ 1.5× nominal
alpha on an autocorrelated null fixture). Clock-horizon effects additionally use non-overlapping
anchor subsampling (every anchor at least one horizon apart within a session, seeded selection).
`p_screen` at `SCOUT_SCREEN_ALPHA` ranks kills/advances; it is served with the label
`descriptive screen — not a confirmatory p-value`.

### 5.4 Mandatory disclosures per screened candidate
Session/symbol concentration (top-1 session share, top-1 symbol share); ToD-bucket slices
(open/mid/close — the referee's buckets, reused); fallback-tercile stratification for any
aggressor-derived feature (effect within low/mid/high `fallback_frac` terciles); the family's
best-of-N expected-max-under-null line (N = union variants tried; a DISCLOSURE, never a decision
rule); `evidence_class` of the corpus screened.

### 5.5 Economic relevance (separate column, never a merged verdict)
`econ_interesting = |effect_bps| ≥ ECON_FLOOR_SPREAD_MULTIPLE × family_median_spread_bps`,
computed from the discovery anchors' quoted spreads, with the formula and inputs frozen in the
candidate spec BEFORE any outcome is read (registration-ordering enforced, TR-9). Served beside —
never multiplied into — the statistical screen, always with the proxy sentence: *quoted spread is
a research cost proxy, not a full execution or tradability model*.

---

## 6. The chronological walk-forward engine (`walkforward.py`, `micro_accessor.py`)

### 6.1 The accessor is the only door
`micro_accessor.py` is the sole legal reader of snapshot, ledger-input, and vault event data
(import-ban guard; TR-3). It is constructed with an `origin` (a session date) and refuses — with
a typed error, never an empty result — any read beyond it; sealed shards are invisible to it
except as §7.5 metadata.

### 6.2 Fold spec (frozen per corpus-era, before fold 1)
`{corpus_id, corpus_manifest_hash, geometry: {train_sessions, test_sessions, step_sessions,
embargo_sessions, embargo_derivation}, clustering_unit, floors (§1), registered_at,
geometry_hash}`. `clustering_unit` is frozen at registration and is `session_date` for both
families (§5.3's r2 rule — no corpus-size-dependent switching, ever). Fold boundaries fall ONLY
on session-date boundaries. Step ≥ test span (pooled
statistics over overlapping validation windows are refused). **Changing geometry after fold 1
voids every survivor state of that corpus-era** (recorded as a voiding event; TR-13).

### 6.3 Purge and embargo
Labels are session-truncated (§4), so no label crosses a session-date fold boundary — **purge is
exact by construction** and asserted, not assumed (TR-6). The embargo is **derived per fold-spec
from actual cross-boundary dependencies**, deterministically, and the derivation is recorded in
`embargo_derivation`: if session-truncated labels + prefix-only features + session-date boundaries
leave no identified cross-boundary dependency, **E=0 is a legitimate outcome**; a nonzero E must
name the dependency it covers (e.g. multi-session feature memory, known regime autocorrelation).
The diagnostic acceptance run pins E=5 as ITS predeclared choice only.

### 6.4 Mode A — rolling-origin discovery
At each origin T: candidate generation, ranking, and threshold FITTING run only through the
origin-T accessor. **The frozen spec identity is the fitting RULE** — e.g.
`training_quantile(0.90)` — never the fold's realized numeric value; realized fitted values are
recorded as fold provenance. Only a RULE change (or any other spec-field change) starts a new
constant-rule sequence; per-origin refits under the same rule do NOT (TR-14 pins both directions).
Fitting rules are functionals of DATA only, never of the candidate pool (pool-invariance trap
TR-10). The validation window is revealed only after the spec hash is recorded; freeze order is
in the fold ledger.

### 6.5 Mode B — fixed hypothesis
A human-authored spec is registered (ledger row, spec hash, timestamp) FIRST; evaluation then
runs on later windows and/or assigned vault shards. Evaluation of a spec against data whose
outcomes were inspectable before its registration is auto-classed `historical_exposed_diagnostic`.

### 6.6 Reporting: the temporal-stability (decay) view
Per constant-rule sequence: per-fold effect, n, sessions, sign, ToD-regime slices, symbol breadth,
and the recent-vs-older consistency line. Pooling across sequences is refused. Every fold and
sequence carries its `evidence_class`; class-mixing in one pooled number is refused (TR-5).
Below-floor folds report `insufficient`; a sequence with < `WF_MIN_SUFFICIENT_FOLDS` sufficient
folds refuses a sequence-level verdict. The tick family refuses fold construction outright until
its corpus clears the §1 floors (TR-15 pins the refusal at today's 11 sessions).

**The explicit survivor rule — `WF_SURVIVOR_RULE_V1` (r2, frozen):** a constant-rule sequence
qualifies as `walkforward_survivor` iff ALL of:
1. ≥ `WF_MIN_SUFFICIENT_FOLDS` sufficient folds, every one of class `historical_oos` and
   process label `rule_process` (§6.8);
2. fold-sign agreement with the registered sidedness ≥ `WF_SURVIVOR_SIGN_CONSISTENCY` over the
   sufficient folds (a zero or opposite-sign fold counts against);
3. the pooled session-clustered effect lies in the registered direction with magnitude ≥ the
   family's pre-registered economic floor (§5.5);
4. no sufficient fold passes the §5.3 screen in the OPPOSITE direction;
5. zero voiding events on the corpus-era.
Anything less is not a survivor — there is no discretionary override.

**The diagnostic acceptance run**: the 155-session playbook bar corpus (the 2025-06 orphan
excluded, disclosed), `DIAGNOSTIC_GEOMETRY`, a small predeclared set of already-frozen playbook
setup definitions, producing 5 folds / 100 validation sessions — every output labeled
`historical_exposed_diagnostic`, worth zero graduation credit, and never re-run with tuned
parameters.

### 6.7 The exposure registry — the deterministic `historical_oos` rule (r2)
A corpus-scoped, hash-chained **exposure registry** records every serving of a window's outcome
data: any GET/report/study/screen/fold that returned outcome aggregates or rows for (corpus,
session-window) appends an exposure entry (surface, window, timestamp). The class rule is then
mechanical: a (spec, validation-window) pair is `historical_oos` **iff** the window has NO
exposure entry timestamped before the spec's `registered_at` AND the shard(s) covering it were
not `exposed` before that instant. At r2 the registry is honestly initialized: every window of
the playbook bar corpus and of the 12 legacy tick symbol-days is pre-marked exposed (their
aggregates have been served for months). **Human/agent rule**: authors — human or agent — read
research data only through served, registry-logged surfaces; the accessor is the only door and
direct file/sqlite reads are guard-banned (TR-3), so there is no unlogged read path. A spec
registered after any logged serving of its validation window is auto-classed
`historical_exposed_diagnostic` (TR-22) — the rule needs no judgment about who remembers what.

### 6.8 Process labels: candidate-rule vs proposer-process evidence (r2)
Every sequence carries a process label. `rule_process`: every generation, ranking, and fitting
step inside the walk-forward was the frozen algorithmic rule — no human/proposer choice
intervened after the first reveal. `operator_process`: a human or proposer selection step
occurred after any fold reveal (choosing among Mode-A outputs, re-ordering, re-prioritizing).
`operator_process` sequences are diagnostic-grade for graduation — they may inform NEW
registrations but never satisfy `WF_SURVIVOR_RULE_V1` (TR-21). An operator selection logged
BEFORE the first reveal (a registered shortlist) keeps `rule_process` for the sequences it
selected, because nothing revealed informed it.

---

## 7. The recorder and the Validation Vault (`tick_recorder.py`, `vault.py`)

### 7.1 The recorder job (Card 5.2, brought forward)
Chunked fetch via the adapter's `iter_historical_chunks` (900s sub-windows), throttled at
`RECORDER_PAGE_BUDGET_PER_MINUTE`, per-chunk checkpointing, resumable and idempotent (an
already-recorded window is answered store-first), single-flight job manager + CLI (the
deep-backfill precedent), operator-gated and credentialed; every recording lands through the
existing `DatasetStore.record` unchanged in discipline (append-only, checksummed, split frozen
at registration). Paired bar backfill (the existing `desk_deep_backfill` CLI) runs for the same
symbol-days so band context joins. Recording failure modes (vendor timeout, partial window,
credential absence) are per-chunk `failed` outcomes with detail — never a raise, never a
fabricated row.

**The Card-5.1 data-preservation prerequisite (r2) — a HARD gate before any bulk recording.**
Before the recorder may record ANY universe (starter tranche included), the event schema ships
the preservation fields: optional `conditions: list[str]` and `exchange: str` on
`RawTrade`/`TradeEvent` and the dataset trade rows, and the vendor-supplied quote
conditions/venue equivalents on `RawQuote`/`QuoteEvent` and quote rows where the feed provides
them — plus any other immutable vendor identifiers the SDK response carries (tape, trade id)
as optional row fields. Optional means: absent-key backward compatibility — every EXISTING
dataset and committed fixture loads byte-identically and its checksum still verifies; the
frozen engine ignores the new fields entirely (the equivalence and golden-trace tests pass
byte-unmodified); the fields exist for research consumers and future data families (Card 9.10's
condition dependency starts accruing on new recordings). The recorder structurally asserts the
schema basis (fields present + `quote_size_unit` stamping per §2.6) before its first fetch and
refuses otherwise (TR-19). Whatever is recorded first is what the corpus keeps forever — the
store is immutable, so preservation precedes volume.

### 7.2 Pre-registered recording universes
A recording batch is legal only under a UNIVERSE registered before any fetch: `{universe_id,
symbol_rule (the explicit panel list), date_rule (an explicit date range or rule), registered_at,
rule_hash}` — appended to the vault ledger first. The recorded batch must be the rule's complete
output net of disclosed vendor failures; a verifier recomputes the expected set and refuses
cherry-picked batches (TR-4).

**The Tier-B resolution order (preflight correction 2026-08-16 — a contract clarification, not
a methodology change).** Card 5.2's Tier-B mid-cap names are PROVISIONAL; its screening
CRITERIA are the contract and are re-evaluated at recording time. The mandatory order, which a
weak executor may not reinterpret:
1. evaluate the frozen Card-5.2 Tier-B screening criteria;
2. record, in the vault ledger: the screening criteria/spec hash, the screen's as-of
   timestamp, the input/provenance basis, the COMPLETE screening output, and the resolved
   Tier-B symbol list;
3. freeze that resolved list;
4. use the resolved list — and nothing else — as the Tier-B portion of `symbol_rule`;
5. register the recording universe;
6. record the vault-secret commitment and compute the opaque HMAC seal assignment (§7.3);
7. only then begin vendor fetches.
After universe registration: **no Tier-B re-screen, no substitution because a symbol is
inconvenient, no replacement from vendor availability or observed data** — a vendor failure is
a DISCLOSED per-chunk/per-symbol failure in the batch report, never a silent swap. The current
provisional names are never hard-coded as permanently valid; only the resolved, recorded list
of step 2 is.

### 7.3 Split vs seal — two independent assignments
- **Split** (train/holdout tag, Card 5.2's published rule, unchanged): `holdout` iff the last hex
  digit of `sha256(f"{symbol}:{YYYY-MM-DD}")` ∈ {0,1,2}.
- **Seal** (vault membership, NEW and opaque): sealed iff the last hex digit of
  `HMAC-SHA256(vault_secret, f"{symbol}:{YYYY-MM-DD}")` < `VAULT_SEAL_HEX_BELOW`. The secret
  lives OUTSIDE the repo at the path named by `TAPEOLOGY_VAULT_SECRET_FILE`, is never committed,
  logged, or served; its commitment `sha256(vault_secret)` is recorded in the universe
  registration, so assignment is auditable after reveal while sealed membership cannot be
  inferred from public information before exposure. Losing the secret orphans assignment audit —
  the commitment row says so; the shards themselves stay sealed.

### 7.4 Shard lifecycle (one-way)
`sealed → assigned → exposed`, recorded in a hash-chained append-only exposure ledger with
timestamps; no transition back; deletion impossible. Assignment binds ONE candidate family LINE
to the shard, keyed on the COMPUTED `family_root_id` (§5.1) — **sealed exposure is
root-family-level and single-shot**: a renamed or re-parameterized family computes the same
root and can never treat the same shard as fresh, and a failed sealed verdict is a permanent
root-family fact carried in every later export bundle (TR-12, TR-20).

### 7.5 Sealed metadata minimization — OPAQUE pre-exposure (r3)
While sealed, a shard serves only: a surrogate `shard_id`, its `universe_id`, a coarse size
bucket (order of magnitude), a **salted** commitment, `sealed_at`, and the exposure state.
**Symbol and date range are NOT served pre-exposure** — they would let bar-level public
outcomes (desk/playbook, served for every date) be looked up against sealed membership; both
are revealed at ASSIGNMENT and recorded in the exposure ledger. Exact event counts, bytes, and
any feature/outcome aggregate are withheld until exposure.

**Join resistance is the actual requirement (r3).** Field-level minimization is not enough: a
served value that merely *identifies* the shard on another surface leaks everything that
surface serves. Therefore:

1. **Surrogate identity.** The served `shard_id` is a vault-minted opaque token bearing no
   derivable relation to the `DatasetStore` dataset id (not the id, not a hash of it, not a
   prefix). The surrogate → dataset-id mapping lives only in the sealed-side ledger and is
   revealed at assignment.
2. **Salted commitment.** The pre-exposure commitment is `HMAC(vault_secret, content_checksum)`
   — not the raw `content_checksum`, which is served publicly per dataset and would join
   directly. The raw checksum is revealed at exposure, at which point the salted commitment can
   be re-derived and verified against it, preserving auditability.
3. **Refusal on the pre-existing surfaces.** `GET /research/datasets` / `/research/datasets/{id}`,
   the `datasets` MCP tool, and any `get_endpoint` path resolving to them REFUSE a sealed
   dataset id with a typed refusal until its exposure is recorded. The refusal states only that
   the id is sealed — never symbol, window, counts, or universe.
4. **Readiness serves sealed-tranche AGGREGATES only** (shard count, total symbol-days,
   per-universe totals) — never a per-shard row, never a per-shard `exposure_state`.
5. Recorder run logs commit per-shard identity and counts by hash while sealed.
6. **Corpus enumerators honour the seal (r4).** A refusal wired only into a route is bypassed by
   any module that enumerates the store itself. Therefore every corpus-wide enumerator —
   `edge_report._all_datasets`, `pnl_scan._split_datasets`, the Scout's corpus manifest, the
   snapshot builder and its compute manager, and any future sibling — EXCLUDES withheld shards
   (state ≠ `exposed`) at its single `DatasetStore.list()` choke point, and **DISCLOSES the
   exclusion**: a `withheld_excluded` count (never the ids) travels into the report body and
   into any append-only row the run writes. Silent exclusion is forbidden — these call sites
   already hold that "a partial report is a misleading report", and the era's denominator rail
   forbids a corpus that shrinks without saying so. A run whose entire eligible corpus is
   withheld reports that honestly rather than emitting an empty-but-shaped result.

No pre-exposure field may equal, contain, or be derivable from any field the public surfaces
serve for the same shard, and no exploratory statistic may be computed from one. TR-2 proves
this by construction, not by whitelist review — and it exercises the operator compute acts
(snapshot build, Scout run, edge report, PnL sweep) BEFORE sweeping, so it cannot pass merely
because the rig computed nothing.

### 7.6 The starter tranche (this era's recording acceptance)
Minimums (all must hold): ≥30 symbol-days; ≥8 distinct Card-5.2-panel symbols including `PG`,
≥3 Tier-B mid-caps, ≥1 Tier-C ETF; ≥10 distinct trading dates spanning ≥6 calendar weeks; no
single date >20% and no single symbol >25% of the tranche's symbol-days; ≥60% full-session
windows (Card 5.2's 09:30–11:00 + 15:00–16:00 ET fallback windows allowed for the remainder,
window provenance recorded). Per-shard completeness reporting: feed, trade/quote counts (hash-
committed while sealed), coverage gaps, classification readiness (`fallback_frac`), checksum,
exposure state. **The ~150-symbol-day research-readiness gate is neither lowered nor satisfied by
this tranche** — readiness reporting states per-study whether its predeclared floor is met, and
any claim below floor fails closed.

### 7.7 The legacy corpus
The 12 pre-existing tick symbol-days (18 datasets) are **permanently exploratory** — never
sealed, never `historical_oos`, regardless of whether an individual file happens never to have
been analyzed. Retrospective sealed shards (past dates recorded fresh) carry the standing
disclosed caveat that bar-level outcomes of their dates are public in the desk/playbook corpus;
a **bar-reconstructibility diagnostic** (a fixed regression recipe of each feature family on
same-session bar features, computed on exploratory data) is REPORTED beside sealed evidence —
it is a diagnostic only, **never a gate, never tunable, and never an authority**; independence is
decided by the deterministic provenance/exposure rules above alone.

---

## 8. Graduation (`micro_graduation.py`)

States, strictly ordered; every transition is an append-only ledger event with full provenance:

1. `exploratory` — any ledgered candidate. Claims: descriptive only.
2. `walkforward_survivor` — a constant-rule sequence satisfying `WF_SURVIVOR_RULE_V1` (§6.6)
   in full: sufficient `historical_oos` + `rule_process` folds, the sign-agreement floor, the
   economic floor in the registered direction, no opposite-direction fold pass, no voiding
   event. Diagnostic-class and `operator_process` folds contribute nothing.
3. `sealed_survivor` — additionally passed its single-shot root-family-level sealed-shard
   evaluation (§7.4, keyed on `family_root_id`) under a spec frozen before assignment.
4. `referee_handoff_ready` — the export bundle exists and validates: frozen spec hash;
   `family_root_id` lineage; the COMPLETE exposure provenance (every ledger trial including
   kills, every fold with its evidence class AND process label, every shard touched, every
   failure); proposed confirmation boundary; family/multiplicity metadata (union-N, sibling
   candidates, prior sealed verdicts of the root family). **This state does NOT imply the current Referee can register
   or adjudicate the candidate**: a flow-context predicate requires a FUTURE named revision of
   `docs/referee-statistical-spec.md`; where a candidate maps onto the existing referee
   vocabulary (setup × side × existing context predicates × existing measures), the bundle is
   registrable through the existing operator act unchanged. The Referee's modules are
   byte-untouched this era either way.

No state ever moves backward except by a voiding event (§6.2), which is itself permanent history.

---

## 9. The trap suite (all deterministic, all in CI)

| Trap | Asserts |
|---|---|
| TR-1 prefix/tail | Truncated-dataset snapshot rows byte-identical to the full run's prefix (3 cut points incl. i=1); appending one tail event changes no prior row |
| TR-2 sealed sweep (r3: join-resistance) | Every registered route + MCP tool serves only §7.5 metadata (or a typed refusal) for a sealed shard — AND the sweep is adversarial, not a whitelist review: seal a fixture shard, collect every value any surface serves for it pre-exposure, and assert none equals, contains, or derives the dataset id, raw `content_checksum`, symbol, window, or event counts. Explicitly includes `/research/datasets{,/{id}}`, the `datasets` MCP tool, `get_endpoint`, and `micro_readiness` (which must expose no per-shard row at all) |
| TR-3 accessor fence | Origin-T accessor refuses reads > T with a typed error; corpus aggregates exclude > T exactly; import-ban: only `micro_accessor` opens snapshot/vault data paths |
| TR-4 cherry-pick refusal | A recording batch ≠ its universe rule's computed set (net of disclosed failures) is refused |
| TR-5 class mixing | Pooling `historical_exposed_diagnostic` with `historical_oos` rows in one statistic is refused; diagnostic folds contribute zero to graduation |
| TR-6 purge exactness | A planted label crossing a fold boundary fails the build; session-truncation asserted per fold |
| TR-7 stale identity | Snapshot cache MISSES on a changed fingerprint-relevant config field and on a mutated feature-module byte (source-hash) |
| TR-8 screening calibration | On an autocorrelated known-null fixture (200 seeds), screen pass-rate ≤ 1.5 × `SCOUT_SCREEN_ALPHA`; the banned plain row-shuffle demonstrably fails this fixture (counter-test) |
| TR-9 econ-floor ordering | A candidate whose econ-floor inputs were read before its spec registration is refused; the floor formula hash predates the first outcome read |
| TR-10 pool invariance | Adding 100 null candidates at an origin changes no prior candidate's fitted threshold or pass/fail |
| TR-11 ledger integrity | Union-N spans grid versions (v1 N=40 + v2 N=25 ⇒ disclosure N=65); in-place edit of row k breaks chain verification at k |
| TR-12 sealed single-shot | Second evaluation attempt of the same family on the same shard is refused; the failed verdict appears in the family's later export bundle |
| TR-13 geometry freeze | A second geometry on the same corpus is refused without a voiding event; the voiding event clears every survivor state of that corpus-era |
| TR-14 rule identity | A per-origin refit under an unchanged fitting rule does NOT start a new sequence; changing the rule string DOES |
| TR-15 tick refusal | The fold engine pointed at the 18-dataset corpus returns the typed floor-refusal naming the failed minima — never an empty fold report |
| TR-16 end-to-end oracles | A synthetic known-null corpus survives nothing end-to-end (Scout + folds); a synthetic planted-effect corpus is recovered with the planted sign and magnitude within tolerance (mid-basis primary); byte-identical rerun |
| TR-17 future-event availability | (a) every row with `observed_through` after `anchor_at` has `available_at` = the `observed_through` instant; (b) truncating a dataset at T reproduces byte-identically exactly the rows with `available_at` ≤ T — none later; (c) a planted outcome starting before its conditioning set's max `available_at` is refused by the outcome join |
| TR-18 units gate | A fixture with `quote_size_unit: "unverified"` (and a mixed-unit pool) refuses every cross-basis feature with a typed error; the verified twin serves them; no silent normalization path exists (source-scan) |
| TR-19 preservation prerequisite | The recorder refuses to start any universe recording unless the row schema carries the Card-5.1 preservation fields and the §2.6 stamping; a freshly captured fixture round-trips conditions/exchange; every legacy fixture loads byte-identically with its checksum verifying |
| TR-20 root lineage | A re-registered family with the same (feature family, context kind, outcome family) triple COMPUTES the same `family_root_id` (the rename attack is refused at the sealed door); a genuinely different triple computes a different root |
| TR-21 process label | A sequence containing a logged operator selection after any fold reveal is `operator_process` and is refused at `walkforward_survivor`; a pre-reveal registered shortlist keeps `rule_process` |
| TR-22 exposure registry | A spec registered after a logged serving of its validation window is auto-classed `historical_exposed_diagnostic`; the registry's r2 initialization marks every playbook-corpus and legacy-tick window exposed |

Plus the standing suite: engine golden trace + observer equivalence + frozen-default profile,
fingerprint pin `08e471b10130e1e2`, referee modules byte-untouched, no-execution scan, copy
discipline, MCP contract, replay-script static sweep.

---

## 10. Stated assumptions and limits (served, not hidden)

1. L1 only: trades + top-of-book quotes. For the LEGACY datasets, trade conditions/exchange
   were dropped at the vendor boundary and are unrecoverable; from this era's recorder on, the
   Card-5.1 preservation fields (§7.1) carry them on every NEW recording — so condition-aware
   studies (Card 9.10) remain blocked on the legacy corpus but their data prerequisite accrues
   going forward. Auction/average-price/TRF prints in legacy data still masquerade as ordinary
   prints; served as a standing caveat on legacy-corpus flow statistics.
2. Aggressor labels are inferred (quote rule → tick test); 29–76% of current-corpus labels are
   tick-test inferences. Every aggressor-derived statistic carries `fallback_frac` and the
   tercile stratification; no label is ever treated as ground truth.
2b. Displayed quote sizes have a DATED unit basis (§2.6): Alpaca CTA/UTP moved to shares on
   2025-11-03; earlier windows are round lots; every legacy dataset is `unverified` until a
   recorded verification. No cross-basis liquidity arithmetic exists outside verified units.
3. Quoted spread is a research cost proxy — no fill model, no queue model, no impact model is
   claimed anywhere in this era.
4. The current tick corpus (12 symbol-days) supports plumbing and clearly-labeled exploratory
   diagnostics only; every readiness payload says which floors are unmet.
5. Retrospective sealed shards conceal L1 micro detail only; bar-level outcomes of their dates
   are public. The reconstructibility diagnostic reports this; provenance rules, not the
   diagnostic, decide admissibility.
6. Nothing in this era emits `live_confirmatory` evidence; the Referee remains the only source
   of confirmatory claims, unchanged.
