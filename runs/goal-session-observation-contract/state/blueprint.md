# App Blueprint — observation-contract

<!--
Written at iter-0 (baseline). This era is additive, docs/backend-only, on top of the product left
by prior eras: Cockpit `/` + Structure `/structure` + Desk `/desk` (config fingerprint
`08e471b10130e1e2`, MCP contract v8 / 28 tools). Per `docs/goal.md` Product Shape: "Existing product
routes remain unchanged... No page, panel, link or component is added or modified." This era's ONLY
new surface is a served-JSON machine path — there is no new UI page, panel or nav entry to plan.

Confirmed at baseline time by direct repo inspection:
- Era-transition paperwork is ALREADY DONE: `docs/goal-archive/goal-2026-09-02.md`,
  `docs/observation-contract-spec.md` (the frozen consumer-facing copy of the Contract
  Constitution) and a dated opening note in `docs/research-directions.md` all exist and are
  committed (HEAD `2f3d2b32 docs(observation-contract): open Observation Contract v1 era`).
- Entirely UNBUILT: `apps/backend/app/observation_contract.py` does not exist; no
  `/tape/{ticker}/observation` route is registered in `apps/backend/app/main.py` (its `/tape/*`
  siblings — `/state`, `/features`, `/events`, `/summary`, `/history` — exist, `/observation` does
  not); `WatchManager.get_observation_source` is not defined in `apps/backend/app/watch_manager.py`;
  no `tests/test_tape_observation_*.py` module exists.
- `apps/frontend/app/{page.tsx,structure/page.tsx,desk/page.tsx}` (Cockpit, Structure, Desk) all
  exist and are UNCHANGED by this era — this era touches zero frontend files.
-->

## Information Architecture

**Layout shell:** persistent top nav bar + main content area (unchanged this era).

**Navigation skeleton** (current state; this era adds NO nav entry, NO page, NO panel):

```
Tapeology
├── Cockpit      /             live/sim/historical tape watch — UNCHANGED this era; used only to
│                               start/pause/resume/stop a Sim watch so its observation exists to read
├── Structure    /structure    UNCHANGED this era (regression-checked only, J-06)
└── Desk         /desk         UNCHANGED this era (regression-checked only, J-06)

Machine-only surface (no nav entry — reached by URL / MCP, never a UI control):
└── GET /tape/{ticker}/observation   NEW this era — the sole TapeObservation v1 read path
```

**Feature / journey homes** (each is the served-JSON machine path, not a page; J-01..J-05 use the
Cockpit only to start/control a Sim watch before reading the artifact by URL):

| Feature / journey | Canonical home | Nav section |
|---|---|---|
| J-01 Pure projection: identity, provenance, integrity | `GET /tape/{ticker}/observation` (planned) | machine path only — Cockpit `/` used only to start the watch |
| J-02 Three honest time concepts, atomic read | `GET /tape/{ticker}/observation` (planned) | machine path only |
| J-03 Lifecycle, feed basis, session identity | `GET /tape/{ticker}/observation` (planned) + existing Cockpit Watch/Pause/Resume/Stop controls (unchanged) | machine path + Cockpit (controls only, no new Cockpit UI) |
| J-04 Ingestion-path equivalence (replay vs. live) | `GET /tape/{ticker}/observation` (planned) + in-process test harness (no UI) | machine path only |
| J-05 One read-only machine path (route + MCP parity) | `GET /tape/{ticker}/observation` (planned) + existing MCP `get_endpoint` proxy (unchanged, byte-identical) | machine path + MCP |
| J-06 Guards + regression sentinel | N/A — cross-cutting; confirms `/`, `/structure`, `/desk` render with zero new panel/link/control | Cockpit / Structure / Desk (unchanged, verified only) |

No page is introduced anywhere in this era; every journey's home is the single new machine-readable
route, reached directly by URL in the browser-qa no-screenshot rail (per `docs/goal.md`: "Every
journey has a Sim-mode browser step on the served JSON").

## Data Contract

Single canonical REST owner for the entire artifact, per `docs/goal.md` Product Shape:
`GET /tape/{ticker}/observation`. It projects, through one pure builder, values whose single owners
are pinned field-by-field in the Contract Constitution §1 of `docs/goal.md` (mirrored consumer-facing
in `docs/observation-contract-spec.md`) — that table is the exact per-field authority; this row is a
condensed index into it, not a second copy. No other endpoint, page or tool may compute or serve any
`TapeObservation` field.

| Value / entity (partition, §6) | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Machine observation semantics — `schema_version`, `provider`, `ticker`, `tape_state`, `confidence`, `warm`, `primary_window`, `features`, `trade_event_count`, `market.*`, `observed_at_utc`, `timing.logical_timestamp`, `timing.epoch_anchor`, `engine_identity.*` | `EngineSnapshot` (existing engine, unchanged, the one semantic producer) projected verbatim by `build_tape_observation` in `apps/backend/app/observation_contract.py` (iter-1: builder module built in-process; not yet served) | `GET /tape/{ticker}/observation` (planned — route lands iter-5) | drives `observation_hash`; zero recomputation — no second classifier/feature/confidence path |
| Provenance / source / lifecycle metadata — `available_at_utc`, `availability_basis`, `generated_at_utc`, `timing.settled_at_utc`, `timing.delivery_lag_seconds`, `lifecycle.*`, `source.*`, `implementation_provenance.*` | `WatchManager.get_observation_source(ticker)` atomic settled-pair read in `apps/backend/app/watch_manager.py` (iter-2: settled snapshot + `settled_at_utc` + `end_reason` built in-process from one manager-held atomic pair; source/session descriptor fields still iter-3) + `build_tape_observation` | `GET /tape/{ticker}/observation` (planned — route lands iter-5) | `data_feed` from the one existing `data_feed_for_scenario`; `source_revision`/`worktree_dirty` resolved once per process, never per request |
| Explanatory metadata — `observations[]` | `EngineSnapshot.observations` (existing engine, unchanged) | `GET /tape/{ticker}/observation` (planned) | prose only; never machine identity |
| Integrity — `observation_hash`, `artifact_hash` | `build_tape_observation` hash laws over the §6 canonical encoding (iter-1: built in-process; not yet served) | `GET /tape/{ticker}/observation` (planned — route lands iter-5) | `observation_hash` = machine-observation equivalence identity; `artifact_hash` = exact evidence-instance identity |

No row was implemented at baseline — the entire table was `(planned)`. Iter-1 built the machine-observation-semantics and integrity rows' computing module (`build_tape_observation`, the schema/partition
constants and both hash laws) in-process, per `docs/goal.md`'s Binding Execution Order step 1. Iter-2
built the atomic-settled-pair half of the provenance/source/lifecycle-metadata row's computing module
(`WatchManager.get_observation_source`: settled snapshot + `settled_at_utc` + `end_reason` from one
manager-held atomic read) — none of the four rows are SERVED yet (no route exists — that is step 5).
Subsequent iterations build the remaining rows incrementally (descriptor/lifecycle/provenance →
ingestion-path equivalence → route → guards/sentinel). No shared canonical value outside this one
endpoint is introduced by this era; every existing Cockpit/Structure/Desk Data Contract value from prior
eras is unread, unchanged foundation here.
