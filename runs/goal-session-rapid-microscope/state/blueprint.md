# App Blueprint — rapid-microscope

<!--
Coherence contract for the whole app. Drafted at baseline (iter-0) from docs/goal.md's
Product Shape + Must-have journeys + Key Capabilities. Auto-approved by default; the
coherence-auditor enforces it every iteration; the goal-decomposer keeps it current with
additive edits (new value rows, new pages under an existing nav section) as the era builds.
-->

## Information Architecture

**Layout shell:** persistent top nav + single main-content column per page; dark-only, dense,
terminal-grade (house style carried unchanged from Era B onward).

**Navigation skeleton** (unchanged this era — `app/meta.py` `UI_ROUTES` untouched):

```
Tapeology
├── Cockpit              /            live tape + chart
├── Structure            /structure   levels/zones, tradable map, S/R bands
└── Desk                 /desk
    ├── Playbook · Band Context · Cohorts          (Era B2, shipped — unchanged this era)
    ├── Referee: Registry · Adjudications · Runs    (Era 6, shipped — unchanged this era)
    └── Rapid Microscope (NEW this era, rendered BELOW the Referee sections, in this order):
        ├── Microscope Readiness   (J-01)
        ├── Scout Ledger           (J-04; J-09 pilot-study results render here too)
        ├── Walk-Forward           (J-05; J-09 pilot-study results render here too)
        └── Validation Vault       (J-06)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the persistent nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| Era transition + corpus readiness truth (J-01) | `/desk` → Microscope Readiness | Desk |
| Micro observer + snapshots (J-02) | keyless/automated; snapshot metadata surfaces via Microscope Readiness | Desk |
| Structure × flow join (J-03) | keyless/automated; joinable-corpus count surfaces via Microscope Readiness | Desk |
| Scout + candidate ledger (J-04) | `/desk` → Scout Ledger | Desk |
| Walk-forward engine + diagnostic run (J-05) | `/desk` → Walk-Forward | Desk |
| Recorder + Validation Vault (J-06) | `/desk` → Validation Vault | Desk |
| Graduation states (J-07) | keyless/automated; states surface via the Scout Ledger / Walk-Forward / Vault rows they attach to | Desk |
| Rapid-Microscope surface + MCP v6 (J-08) | `/desk` → all four new sections above | Desk |
| Pilot studies (J-09) | `/desk` → Scout Ledger / Walk-Forward (results render through J-08's sections, no new page) | Desk |
| Kept-product sentinel (J-10) | `/`, `/structure`, `/desk` (every existing section, unchanged) | Cockpit / Structure / Desk |

## Data Contract

Every value below is computed once, owned by one module, served by one endpoint; no page may
recompute or re-fetch it from anywhere else. **New rows this era** (transcribed verbatim from
`docs/goal.md` §Product Shape, the canonical statement):

| Value | Owner (module) | Serving endpoint |
|---|---|---|
| Corpus readiness truth (inventory, floors, exposure states) + joinable-corpus counts (iter-3/J-03 addition: `total`/`playbook_signal_count`/`band_touch_count`/`by_setup_id`, computed by new `app/research/micro_join.py`, called from `micro_readiness.py` — no second endpoint) | new `app/research/micro_readiness.py` (+ `micro_join.py` contributes the joinable-corpus computation only) | `GET /research/desk/micro/readiness` |
| Feature snapshot metadata + build progress/runs | new `app/research/micro_snapshots.py` (+ manager) | `GET /research/desk/micro/snapshots`, `POST/GET/POST-cancel /research/desk/micro/snapshots/compute`, `GET .../snapshots/runs` |
| Scout trials, kills, denominators, screens | new `app/research/scout_ledger.py` + `scout.py` | `GET /research/desk/micro/scout`, `POST/GET/POST-cancel /research/desk/micro/scout/compute`, `GET .../scout/runs` |
| Fold specs, folds, sequences, decay view | new `app/research/walkforward.py` + its ledger | `GET /research/desk/micro/walkforward`, `POST/GET/POST-cancel /research/desk/micro/walkforward/compute`, `GET .../walkforward/runs` |
| Vault shards, universes, exposure ledger | new `app/research/vault.py` | `GET /research/desk/micro/vault` |
| Recorder job + tranche progress/runs | new `app/research/tick_recorder.py` | `POST/GET/POST-cancel /research/desk/micro/recorder/compute`, `GET .../recorder/runs` |
| Graduation states + export bundles | new `app/research/micro_graduation.py` | `GET /research/desk/micro/graduation` |

**Disclosure sub-fields** (registered iter-10 — housekeeping only, no new owner, no new endpoint;
these three were already shipped by iter-9's r4 fix round and flagged WARN by iter-9's coherence
audit as "served across roughly nine endpoints but not yet rows in this table"):

| Sub-field | Type/shape | Owner (already-registered parent module) | Served by (existing endpoints) |
|---|---|---|---|
| `withheld_excluded` | `int >= 0` — a count only, never the withheld ids | each already-registered parent module (`scout.py`, `walkforward.py`, `micro_join.py`, `edge_report.py`, `edge_report_cache.py`, `pnl_scan.py`, `desk_screen.py`, `micro_snapshots.py`), all via the ONE shared predicate `vault.withheld_dataset_ids()` → `micro_snapshots.exclude_withheld()` | the GET/compute routes of the module in the same row |
| `sealed_withheld` | `int >= 0` | `datasets.py` (already-registered owner of the datasets listing) | `GET /research/datasets` |
| `sealed_tranche` | object aggregate (shard count, total symbol-days, per-universe totals — never a per-shard row, never a per-shard `exposure_state`) | `micro_readiness.py` (already-registered owner) | `GET /research/desk/micro/readiness` |

**Recorder-progress aggregate sub-fields** (registered iter-11 — r5 closure, sub-fields of the
ALREADY-registered "Recorder job + tranche progress/runs" row, no new owner, no new endpoint):

| Sub-field | Type/shape | Owner (already-registered parent module) | Served by (existing endpoint) |
|---|---|---|---|
| `progress.chunks_total` / `progress.chunks_done` | `int >= 0` each | `tick_recorder.py` (`TickRecorderComputeManager`) | `GET /research/desk/micro/recorder/compute` |
| `progress.chunks_fetched` / `progress.chunks_reused` / `progress.chunks_unchanged` / `progress.chunks_failed` | `int >= 0` each — per-outcome-type counts, never a per-chunk row | `tick_recorder.py` (`TickRecorderComputeManager`) | `GET /research/desk/micro/recorder/compute` |
| `progress.trades_total` / `progress.quotes_total` | `int >= 0` each — aggregate event counts, never per-chunk. **iter-12 note:** valid only after whole-ORIGINAL-pool release (r7 §7.1) — see the new bucket sub-fields below for the pre-release form this same surface serves while any pool member is unexposed | `tick_recorder.py` (`TickRecorderComputeManager`) | `GET /research/desk/micro/recorder/compute` |
| `progress.percent_complete` | `float, 0.0–100.0` | `tick_recorder.py` (`TickRecorderComputeManager`) | `GET /research/desk/micro/recorder/compute` |
| `progress.elapsed_seconds` | `float >= 0` | `tick_recorder.py` (`TickRecorderComputeManager`) | `GET /research/desk/micro/recorder/compute` |

**Universe rule-reveal sub-fields** (registered iter-12 — r7 §7.2 closure, sub-fields of the
ALREADY-registered "Vault shards, universes, exposure ledger" row, no new owner, no new endpoint):

| Sub-field | Type/shape | Owner (already-registered parent module) | Served by (existing endpoint) |
|---|---|---|---|
| `rule_commitment` | `str` — 64-hex-char `sha256(nonce ‖ canonical_rule)`; served in place of the plain `rule_hash` at the committed (pre-whole-pool-release) stage | `vault.py` (`register_universe`, `_serialize_universe`) | `GET /research/desk/micro/vault` |
| `commitment_nonce` | `str` — the high-entropy nonce, held privately with the registration row; served ONLY once a universe's revealed stage begins (whole-ORIGINAL-pool release — never merely "all ledger-tracked shards exposed") | `vault.py` (`register_universe`, `_serialize_universe`) | `GET /research/desk/micro/vault` |

**Recorder-progress volume sub-fields** (registered iter-12 — r7 §7.1 closure, sub-fields of the
ALREADY-registered "Recorder job + tranche progress/runs" row, no new owner, no new endpoint;
supersede the iter-11-registered `progress.trades_total`/`progress.quotes_total` at THIS surface
while the run's pool is unexposed — the exact int fields above stay valid only after whole-pool
release, a state this surface cannot reach before its own recording finishes, let alone before
assignment/exposure):

| Sub-field | Type/shape | Owner (already-registered parent module) | Served by (existing endpoint) |
|---|---|---|---|
| `progress.trades_total_bucket` / `progress.quotes_total_bucket` | `str` — a frozen, predeclared coarse label (order-of-magnitude or power-of-two range, e.g. `"1M-10M"`), never a rounded number, differencing-resistant across successive snapshots | `tick_recorder.py` (`TickRecorderComputeManager`) | `GET /research/desk/micro/recorder/compute` |

**Exposure-state value-space extension** (registered iter-12 — r6 §7.8 closure; widens the
ALREADY-registered `exposure_state` field of the "Vault shards, universes, exposure ledger" row; no
new owner, no new endpoint): the legal value set gains `exposure_unknown` beside the already-served
`sealed`/`assigned`/`exposed` — a shard whose freshness an unverifiable ledger recovery could not
prove, permanently ineligible for sealed-OOS use. Owner `vault.py`, served by
`GET /research/desk/micro/vault` exactly as the other three values already are.

**Unchanged owners** (this era reads them verbatim, never recomputes, never re-serves from a
second endpoint): datasets/replay → `datasets.py` (`DatasetStore.replay`; gains one additive
default-`None` `observer=` kwarg only, counter-tested byte-identical when absent); engine
features/side → the engine snapshot (`app/engine/features.py`); playbook records →
`desk_playbook.py`; band maps → `desk_playbook_context.BandMapResolver`; referee
registry/adjudications → the `referee_*` family (`referee_registry.py`,
`referee_adjudicate.py`, `referee_evidence.py`, `referee_null.py`, `referee_stats.py`,
`referee_routes.py`); every other value shipped by an earlier era exactly as its own contract
lists (full history in `docs/goal-archive/goal-2026-08-16.md` — not re-enumerated here).

**Canonical values (single source of truth):** a candidate's trial history (scout ledger); a
fold/sequence result and its evidence class (walkforward ledger); a shard's exposure state
(vault ledger); the corpus readiness floors (`micro_readiness`) — each computed once, served
from its one endpoint, read verbatim by UI/MCP/reports.

<!-- iter-3 note: the joinable-corpus field above is served ahead of its UI wiring, same accepted
     pattern iter-2's coherence audit approved for J-02's snapshot endpoints — the wiring iteration
     (J-08) is already named in the Information Architecture table above, so this is not an orphan
     feature. No nav-skeleton change this iteration; no reapproval file written. -->

<!-- iter-10 note: the "Disclosure sub-fields" table above is pure documentation catch-up (closing
     iter-9 coherence.md's WARN) — all three fields were already shipped by iter-9's r4 fix round;
     nothing about their code changed this iteration. No nav-skeleton change; no reapproval file
     written. J-07's own row in the main Data Contract table above (Graduation states + export
     bundles) was already registered at era baseline and is unchanged by this note — iter-10 builds
     that already-reserved owner verbatim. -->

<!-- iter-11 note (r5 closure): `sealed_tranche`'s KEEPS its already-registered name and shape
     (shard_count / symbol_days / by_universe — still never a per-shard row) — this note documents
     that its SEMANTICS broaden, not that its shape changes. Before this iteration, a dataset only
     counted toward `sealed_tranche` if it already carried an explicit vault shard-ledger row
     (`sealed`/`assigned`). Per the r5 owner ruling (`docs/rapid-validation-spec.md` §7.5 point 7 —
     "a newly recorded tranche is ONE OPAQUE RESEARCH POOL... no served id... may separate an
     unexposed exploratory shard from an unexposed sealed one"), a dataset now ALSO counts if its
     (symbol, date) matches a registered vault universe's expected recording set and it was
     recorded at-or-after that universe's registration — whether or not any shard-ledger row exists
     for it yet. This closes the structural gap where a pool member the recorder never explicitly
     sealed would otherwise be listed with full identity the moment it was recorded (zero
     `seal_shard`/`assign_shard`/`expose_shard` production call sites exist even after this
     iteration — see `runs/goal-session-rapid-microscope/state/assumptions.md`'s iter-11 entry for
     the full reasoning and the deliberately-deferred "exposed for exploratory use" mechanism this
     does NOT build). The new predicate is the SAME single choke point (`vault.py`, consumed via
     `micro_snapshots.exclude_withheld()`/`withheld_dataset_ids_for_store()` and directly by
     `micro_readiness.build_readiness()`) — no second implementation anywhere. Zero behavioural
     change against the real store, which has zero registered vault universes today. No
     nav-skeleton change; no reapproval file written. -->

<!-- iter-12 note (r6 §7.8 / r7 §7.2+§7.1 closure): the three sub-tables added this iteration
     (universe rule-reveal, recorder-progress volume buckets, exposure-state value-space extension)
     are the ONLY Data Contract change this round — all are sub-fields of already-registered rows
     (Vault shards/universes/exposure ledger; Recorder job + tranche progress/runs), served by
     their already-registered endpoints, owned by their already-registered modules. No new page, no
     new route, no new MCP tool, no nav-skeleton change; no reapproval file written. The
     `verify_chain()` fail-closed retrofit (r6 §7.8, TR-25) adds no displayed value at all -- it is
     a refusal behaviour, not a served field, so it has no Data Contract row of its own. Zero
     behavioural change against the real store: it still has no `micro_vault` directory (confirmed
     again this iteration), so no universe is registered, no shard is sealed, and the recorder's own
     progress surface has never yet served an exact `trades_total`/`quotes_total` pair for withheld
     data in production. The reveal-gate widening (`_fully_exposed_universe_ids` becoming
     pool-rule-aware rather than ledger-row-only) changes WHEN the existing revealed-stage fields
     become servable, not their shape -- no new row for that change either, matching this file's
     own iter-11-note precedent for semantics-broadening-without-shape-change edits. -->

<!-- iter-13 note: pure internal-correctness fix (vault.py's `recover_shard_ledger` recovery-path
     soundness + two documentation-only clarifications: `seal_shard`/`assign_shard`/`expose_shard`'s
     own-ledger-only gating scope, and a stale `micro_routes.py` docstring) — no Data Contract
     change. The corrected halt/union-marking behavior has no serving endpoint (0 production call
     sites, matching the iter-12 coherence audit's own precedent for `VaultRecoveryLedger`'s
     content: "no Data Contract row needed yet ... register it if/when a route or CLI ever surfaces
     it"). No new page, route, MCP tool, or nav-skeleton change; no reapproval file written. -->
