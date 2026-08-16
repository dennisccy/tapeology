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

### 2.2 The prefix law (streaming-only state)
Snapshot row *i* is a pure function of events `1..i` (plus the engine snapshot after event *i*).
The writer flushes row *i* before consuming event *i+1*. **No whole-dataset normalizer, baseline,
calibration, or end-of-session statistic may enter any row.** Session-anchored accumulations
(cumulative delta) are legal because the anchor precedes every row. Event-time baselines use only
prior events. Enforced by the TR-1 prefix and tail-perturbation traps (§9).

### 2.3 Snapshot identity and verification
Snapshot key = `(dataset_id, dataset_checksum, MICRO_ALGO_VERSION, SNAPSHOT_FORMAT_VERSION,
feature_source_hash, config_fingerprint, params_hash)` where `feature_source_hash` =
sha256 over the feature-module bytes. The loader re-verifies `dataset_checksum`,
`config_fingerprint`, and `feature_source_hash` on every read and refuses on mismatch
(the `DatasetIntegrityError` discipline). Snapshots are derived, append-only, rebuildable, and
own nothing.

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

---

## 3. Feature families (Wave 1 — L1 only)

Per-row disclosures everywhere: `side_source`, and per-window `fallback_frac` (share of trades
classified by the tick test rather than the quote rule — measured 29–76% on the current corpus)
and `unknown_frac`. Any aggressor-derived quantity is served beside those two fractions.

- **F-FLOW** — per-print signed volume (engine side × size); session-anchored cumulative delta
  `CD_t = Σ_{i≤t, side_i≠unknown} sign(side_i)·size_i` (Card 9.1's formula verbatim; unknowns
  excluded and counted); rolling imbalance over event-time windows (last-N trades, last-X shares)
  beside the engine's clock windows; same-side run length at anchor; volume burst = window volume
  vs the median of the trailing event-time windows of the SAME session prefix.
- **F-RESPONSE** — impact efficiency = mid-price progress per aggressive share over a window;
  efficiency trend = current window efficiency minus the prior non-overlapping window's (the
  exhaustion signature: rising aggression with falling efficiency); failed aggression = the
  engine's `absorption_score` (reused) plus the continuous complement (dominant-side volume ×
  clamped impact flatness, unthresholded); response asymmetry = signed mid move in the K trades
  after buy-aggressive vs sell-aggressive prints, same window.
- **F-LIQUIDITY** — spread level (engine) and spread change (window mean minus prior window's);
  quote imbalance `(bid_size − ask_size)/(bid_size + ask_size)`; microprice
  `(ask·bid_size + bid·ask_size)/(bid_size + ask_size)`; quote depletion (drawdown of same-side
  displayed size across consecutive quotes at an unchanged price); replenishment
  (`refill_consistent`: displayed size restored at the same price within the next M quotes after
  executions against it — **the ONLY permitted label**; "iceberg", "institutional", "spoof" and
  any intent language are banned); execution-vs-replenishment ratio (executed volume at a price /
  displayed-size restoration at that price, windowed).

Quote sizes reach the observer on `QuoteEvent` rows — they are dropped only inside the engine's
`FeatureEngine`, which this spec does not touch.

---

## 4. Outcomes (the closed set)

For an anchor event: forward **mid-price** move (quote mid at the horizon boundary minus mid at
anchor; last-trade fallback only when no quote exists on either end, disclosed per row) at every
horizon in §1's three horizon families; session-truncated with truncation flagged and truncated
rows excluded from averages (the playbook rail's honesty rule); side-signed when a hypothesis side
exists. Quoted spread at anchor (bps) is served beside every outcome as the cost-proxy column —
never netted into the outcome silently. No sub-second horizon exists anywhere.

---

## 5. The Scout and the exploratory candidate ledger (`scout.py`, `scout_ledger.py`)

### 5.1 Candidate spec (frozen at ledger append)
`{candidate_id, family_id, feature: {name, transform, params}, structure_context: {kind:
"playbook_signal"|"band_touch"|"none", …frozen references}, outcome: {horizon_key, sidedness},
fitting_rule?: <a named rule string, §6.4>, econ_floor: {multiple, family_median_spread_bps,
floor_bps, proxy_sentence}, corpus_manifest: [dataset/record ids + checksums], grid_version,
registered_at, spec_hash}`.

### 5.2 The ledger
Hash-chained append-only JSONL (the `desk_playbook_log.py` pattern): every evaluated variant —
including every kill — is one permanent row carrying its result summary, `decision:
survive|<KILL_REASONS>`, `reason` (closed vocabulary), `notes`, and the family's running
`variants_tried` (the union-N denominator across all grid versions). Rows are never rewritten;
`superseded` rows point at their successor. Tamper = chain-verification failure (TR-11).

### 5.3 Screening procedure (descriptive, never confirmatory)
Cluster unit = `session_date` (tick family: symbol-day until ≥2 symbols/date median, then
session_date). Effect = mean of session-cluster mean deltas (candidate cell vs its comparator).
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
geometry_hash}`. Fold boundaries fall ONLY on session-date boundaries. Step ≥ test span (pooled
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

**The diagnostic acceptance run**: the 155-session playbook bar corpus (the 2025-06 orphan
excluded, disclosed), `DIAGNOSTIC_GEOMETRY`, a small predeclared set of already-frozen playbook
setup definitions, producing 5 folds / 100 validation sessions — every output labeled
`historical_exposed_diagnostic`, worth zero graduation credit, and never re-run with tuned
parameters.

---

## 7. The recorder and the Validation Vault (`tick_recorder.py`, `vault.py`)

### 7.1 The recorder job (Card 5.2, brought forward)
Chunked fetch via the adapter's `iter_historical_chunks` (900s sub-windows), throttled at
`RECORDER_PAGE_BUDGET_PER_MINUTE`, per-chunk checkpointing, resumable and idempotent (an
already-recorded window is answered store-first), single-flight job manager + CLI (the
deep-backfill precedent), operator-gated and credentialed; every recording lands through the
existing `DatasetStore.record` unchanged (append-only, checksummed, split frozen at
registration). Paired bar backfill (the existing `desk_deep_backfill` CLI) runs for the same
symbol-days so band context joins. Recording failure modes (vendor timeout, partial window,
credential absence) are per-chunk `failed` outcomes with detail — never a raise, never a
fabricated row.

### 7.2 Pre-registered recording universes
A recording batch is legal only under a UNIVERSE registered before any fetch: `{universe_id,
symbol_rule (the explicit panel list), date_rule (an explicit date range or rule), registered_at,
rule_hash}` — appended to the vault ledger first. The recorded batch must be the rule's complete
output net of disclosed vendor failures; a verifier recomputes the expected set and refuses
cherry-picked batches (TR-4).

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
timestamps; no transition back; deletion impossible. Assignment binds ONE candidate FAMILY to the
shard; **sealed exposure is family-level and single-shot** — a second spec from the same family
can never treat the same shard as fresh, and a failed sealed verdict is a permanent family fact
carried in every later export bundle (TR-12).

### 7.5 Sealed metadata minimization
While sealed, a shard serves only: symbol, date range, feed, coarse size bucket (order of
magnitude), checksum commitment, universe id, exposure state. Exact event counts, bytes, and any
feature/outcome aggregate are withheld until exposure (TR-2 sweeps every registered route,
closing the `get_endpoint` path structurally). Recorder run logs commit counts by hash while the
shard is sealed.

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
2. `walkforward_survivor` — a constant-rule sequence with ≥ `WF_MIN_SUFFICIENT_FOLDS` sufficient
   folds of class `historical_oos`, sign-consistent per the sequence report, above its economic
   floor, and no voiding event. Diagnostic-class folds contribute nothing.
3. `sealed_survivor` — additionally passed its single-shot family-level sealed-shard evaluation
   (§7.4) under a spec frozen before assignment.
4. `referee_handoff_ready` — the export bundle exists and validates: frozen spec hash; the
   COMPLETE exposure provenance (every ledger trial including kills, every fold, every shard
   touched, every failure); proposed confirmation boundary; family/multiplicity metadata
   (union-N, sibling candidates). **This state does NOT imply the current Referee can register
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
| TR-2 sealed sweep | Every registered route + MCP tool serves only §7.5 metadata (or refusal) for a sealed shard |
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
| TR-16 end-to-end oracles | A synthetic known-null corpus survives nothing end-to-end (Scout + folds); a synthetic planted-effect corpus is recovered with the planted sign and magnitude within tolerance; byte-identical rerun |

Plus the standing suite: engine golden trace + observer equivalence + frozen-default profile,
fingerprint pin `08e471b10130e1e2`, referee modules byte-untouched, no-execution scan, copy
discipline, MCP contract, replay-script static sweep.

---

## 10. Stated assumptions and limits (served, not hidden)

1. L1 only: trades (epoch, price, size) + top-of-book quotes. Trade conditions/exchange were
   dropped at the vendor boundary and are unrecoverable for existing datasets; condition-aware
   studies (Card 9.10) stay blocked until a future re-recorded data family.
2. Aggressor labels are inferred (quote rule → tick test); 29–76% of current-corpus labels are
   tick-test inferences. Every aggressor-derived statistic carries `fallback_frac` and the
   tercile stratification; no label is ever treated as ground truth.
3. Quoted spread is a research cost proxy — no fill model, no queue model, no impact model is
   claimed anywhere in this era.
4. The current tick corpus (12 symbol-days) supports plumbing and clearly-labeled exploratory
   diagnostics only; every readiness payload says which floors are unmet.
5. Retrospective sealed shards conceal L1 micro detail only; bar-level outcomes of their dates
   are public. The reconstructibility diagnostic reports this; provenance rules, not the
   diagnostic, decide admissibility.
6. Nothing in this era emits `live_confirmatory` evidence; the Referee remains the only source
   of confirmatory claims, unchanged.
