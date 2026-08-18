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
