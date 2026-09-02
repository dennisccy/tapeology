# Tapeology — Project Goal (Observation Contract v1 — one time-safe, provenance-complete tape observation, exposed)

> **OPERATIVE GOAL — v1, ratified 2026-09-02 after three adversarial revision rounds (READY TO COMMIT ERA-OPEN DOCS). Predecessor archived at [docs/goal-archive/goal-2026-09-02.md](goal-archive/goal-2026-09-02.md).**
>
> This chapter begins after **The Hypothesis Foundry** is formally closed (`GOAL_ACHIEVED` 2026-08-27,
> session `hypothesis-foundry`, `epoch:afd19e9c11a6534f`) and its closure artifacts plus the §0.8
> source-authoring laws are on `main`. Its epoch manifest, freeze set, trial ledger, reports and standing
> dispositions are immutable foundation. No research question is opened or reopened here.
>
> **Thesis.** Tapeology says *"this is what the tape observed."* It never says *"therefore trade."* This era
> exposes the EXISTING deterministic tape observation — the immutable `EngineSnapshot` the engine already
> builds once per tick — as one versioned, machine-readable artifact, **`TapeObservation`**, that an external
> composite-policy consumer can use without reconstructing, recomputing or guessing any Tapeology semantics.
> It is not a new tape engine, not a trading-signal goal, and not the consumer's implementation.
>
> **Core principle.** Tapeology distinguishes **market-event time**, **actual system availability time when
> measured**, and **artifact-generation time**, and never manufactures historical information availability
> that was not recorded. *Retrospective evidence establishes compatibility, not prospective proof.*
>
> **Deterministic-evidence rule.** No mandatory journey or test depends on Alpaca, the network, credentials
> or market hours. The binding contract is proven with Sim mode, committed fixtures and the deterministic
> provider harnesses; a real-provider smoke test is optional, environment-gated, and can never block
> `GOAL_ACHIEVED`.
>
> **No Goal-Proposer.** The framework goal-proposer was retired upstream (`3d0d07c2`); `docs/goal.md` is
> human-owned and never auto-extended. The journey set J-01…J-06 is finite and fixed.

---

## Vision

Tapeology already has a single-source-of-truth architecture: exactly one `EngineSnapshot` per tick owns
the ticker, scenario, logical timestamp, stream status, bid/ask/spread/last, per-window features, primary
window, tape state, confidence, observations, epoch anchor and delivery lag, and REST, WebSocket, the UI and
the read-only MCP surface all project from that one object. What is missing is an **external contract**:
today a consumer must combine the logical timestamp with an epoch anchor served on a different endpoint,
infer the feed basis from a scenario prefix, guess whether a snapshot is warm or stale, and has no
engine/config identity or integrity hash on any tape surface at all.

**Observation Contract v1** adds the smallest stable artifact that answers, for one symbol, from one
engine: *what was observed, at what market time, when (if ever) it was actually available, from which
feed and watch session, under which engine semantics and configuration, in which lifecycle state, and
which exact evidence object this is.* Every value is a verbatim projection of something the engine, the
watch manager or the configuration already owns. Nothing is recomputed, nothing is decided. The same
engine remains the single semantic producer for simulation, historical replay and live ingestion, and the
era proves that invariant under an identical valid event stream.

## Target Users

- **Primary:** the Tapeology owner/operator, who wants one canonical, versioned observation artifact whose
  time and provenance semantics are honest enough to be composed with other evidence later.
- **Secondary:** a future **external composite-policy consumer** (generic; it lives in its own repository;
  the dependency direction is consumer → Tapeology contract, never the reverse), which must obtain one
  observation through one read-only machine path and never reconstruct Tapeology semantics.
- **Tertiary:** a future scientific auditor who must be able to say which exact Tapeology evidence object a
  later evaluation consumed, and under which engine semantics, configuration and implementation source.

---

## Success Criteria

The era succeeds when all of the following are true:

1. **The era boundary is explicit and auditable.** The Hypothesis Foundry goal is archived byte-identically
   at `docs/goal-archive/goal-2026-09-02.md`; its session, epoch artifacts, ledgers and reports are
   unmodified; this era has its own goal, session id (`observation-contract`) and a dated opening note in
   `docs/research-directions.md`.
2. **One artifact, one producer.** `TapeObservation` (`schema_version = tape-observation-v1`,
   `provider = tapeology`) is a pure projection of `EngineSnapshot` plus manager-owned provenance. No tape
   feature, state, confidence, freshness or feed basis is recomputed outside the engine and the one existing
   feed-basis function; there is no second classifier, no second state engine.
3. **Three time concepts are distinct and tested.** `observed_at_utc` (market/event time of the latest
   processed quote or trade), `available_at_utc` (actual system availability when measured, else null) and
   `generated_at_utc` (artifact projection time) are three separate fields with pinned definitions.
4. **Historical availability is honestly unknown.** For historical and dataset replay `available_at_utc`
   is null and `availability_basis` is `historical_arrival_unknown`; event time is never copied into
   availability and the replay wall clock is never presented as historical availability.
5. **Live availability is measured, never derived.** On the live basis `available_at_utc` equals the
   manager-recorded settled wall-clock instant of the exact snapshot serialized; it is never
   `observed_at_utc + delivery_lag_seconds`.
6. **The observation read is atomic.** Snapshot, source/session descriptor and settled time come from one
   manager-controlled read that belongs to the same settled observation; the route never snapshots an
   engine.
7. **Feed basis is explicit and never pooled.** `source.data_feed ∈ {sim, iex, sip}` and
   `source.source_mode ∈ {sim, live, historical, dataset_replay}` are served verbatim from their single
   owners; no two bases are ever treated as equal.
8. **Session identity is present.** Every managed watch (sim, live, historical) carries a stable
   `source.session_id` and `source.session_started_at_utc`; dataset replay is identified by
   `dataset_id + dataset_checksum`. Session identity is provenance only and never enters engine computation.
9. **Lifecycle is honest.** `connecting`, `waiting`, `live`, `stale`, `paused`, `closed`, `failed` remain
   distinct; `tape_state` and `confidence` are never rewritten, suppressed or nulled because of lifecycle;
   Tapeology never returns READY, NO_TRADE, NO_VERDICT, `trade_allowed` or any equivalent.
10. **Semantic identity is separate from implementation provenance.** `engine_identity`
    (`engine_semantics_version`, `config_fingerprint`, `profile_id`, closed vocabularies) is the semantic
    identity; `implementation_provenance` (`engine_source_hash`, `source_revision`, `worktree_dirty`) is
    fail-closed provenance, disclosed honestly including dirty worktree state, and never claims a semantic
    change by itself.
11. **Prose is outside identity.** `observations[]` is explanatory metadata; a wording change never changes
    machine observation identity.
12. **Two hashes with normative roles.** `observation_hash` is the machine-observation equivalence
    identity; `artifact_hash` identifies the exact evidence artifact instance and is the reference a
    downstream consumer must record.
13. **Ingestion-path equivalence is proven under the narrow claim.** The same valid ordered event stream fed
    through the replay feeder and through the live feeder into the same frozen engine/configuration yields
    an identical machine-observation semantic set; the claim explicitly excludes equality between
    independently sourced IEX and SIP data.
14. **One read-only machine path.** `GET /tape/{ticker}/observation` (transport only) serves the artifact;
    its parsed JSON equals the builder's output field-for-field and value-for-value; the existing MCP
    `get_endpoint` proxies it byte-identically; a consumer needs nothing else.
15. **English canonical core.** Every new identifier, schema name, enum value, field name, test and
    persisted value is English-only ASCII.
16. **Deterministic evidence only.** No mandatory journey or test requires Alpaca, the network, credentials
    or market hours; an optional real-provider smoke test is environment-gated and non-blocking.
17. **Guards are real.** Every guard added by this era is structural, proven non-vacuous, and ships a seeded
    counter-test proving it can fail.
18. **Foundation remains intact.** `config_fingerprint` stays `08e471b10130e1e2`; the `default` engine, the
    five tape states and thresholds, archived-era surfaces, the MCP contract (v8, 28 tools) and every
    existing determinism / observer / epoch-anchor / lifecycle / feed-basis / profile suite stay green and
    unweakened.

---

## Key Capabilities

1. **Observation contract spec** — the checked-in, consumer-facing `docs/observation-contract-spec.md`
   (field/owner table, time law, lifecycle table, partition, hash laws, canonical encoding, consumer path).
   Its normative content is this constitution; the run may add implementation notes, never change field
   semantics.
2. **`build_tape_observation`** — one public pure builder in `apps/backend/app/observation_contract.py`
   (reads no clock, no git, no engine internals) plus the frozen schema constants and both hash laws.
3. **Atomic managed observation read** — `WatchManager.get_observation_source(ticker)` returning the
   settled `EngineSnapshot`, its source/session descriptor, its settled wall-clock time and the engine's
   `end_reason` from one manager-held settled pair.
4. **Source/session descriptor** — manager-owned provenance recorded at watch creation (mode, scenario,
   window, session id, session start, profile id), with `data_feed` from the one existing feed-basis
   function.
5. **Implementation provenance resolver** — `engine_source_hash` over the fixed engine-module tuple plus
   process-level `source_revision` / `worktree_dirty`, resolved once per process.
6. **`GET /tape/{ticker}/observation`** — the transport-only route beside its `/tape/*` siblings, 404 on an
   unwatched ticker, proxied by the existing MCP `get_endpoint`.
7. **Deterministic proof suite** — projection, time-law, lifecycle/feed, ingestion-path equivalence and
   route tests on Sim mode, committed fixtures and the `HistoricalProvider` / `LiveProvider` harnesses with
   a controlled clock.
8. **Guard suite** — recompute guard, mutator-call-site guard, copy-discipline and compound-identifier ban,
   external-system reference guard, English-only guard, real-provider isolation guard, each with a seeded
   counter-test.

---

# Contract Constitution

Everything in this section is binding. Implementation may factor code differently, but it may not change
the meaning of any field, law, enum or partition below. If exact reuse of an existing engine or manager
value proves impossible without changing engine semantics, Goal Mode halts and reports
`CONTRACT_REVISION_REQUIRED`; it must not silently alter `app/engine/`.

## 1. The artifact and its owners

`TapeObservation` v1 carries only observation, timing, provenance, lifecycle and integrity facts. Every
field has exactly one owner and belongs to exactly one partition (§6).

| Field | Owner (never recomputed) | Partition |
|---|---|---|
| `schema_version` = `tape-observation-v1` | module constant | semantic |
| `provider` = `tapeology` | module constant | semantic |
| `ticker` | `EngineSnapshot.ticker` | semantic |
| `observed_at_utc` | projection of `EngineSnapshot.epoch_anchor + EngineSnapshot.timestamp` (§2) | semantic |
| `available_at_utc` | projection of the manager-recorded settled time per `availability_basis` (§2) | metadata |
| `availability_basis` | projection of `source.source_mode` (§2) | metadata |
| `generated_at_utc` | the route-supplied `now` (§2) | metadata |
| `tape_state` | `EngineSnapshot.tape_state` | semantic |
| `confidence` | `EngineSnapshot.confidence` | semantic |
| `warm` | `EngineSnapshot.warm` | semantic |
| `primary_window` | `EngineSnapshot.primary_window` | semantic |
| `features` (window → name → value) | `EngineSnapshot.features` | semantic |
| `trade_event_count` | `EngineSnapshot.event_count` (the existing trade-only counter, verbatim) | semantic |
| `market.bid`, `market.ask`, `market.spread`, `market.last` | `EngineSnapshot.bid/ask/spread/last` | semantic |
| `observations[]` | `EngineSnapshot.observations` | explanatory |
| `lifecycle.stream_status` | `EngineSnapshot.stream_status` | metadata |
| `lifecycle.paused` | `EngineSnapshot.paused` | metadata |
| `lifecycle.end_reason` | `TapeEngine.end_reason` (via the atomic read) | metadata |
| `timing.logical_timestamp` | `EngineSnapshot.timestamp` | semantic |
| `timing.epoch_anchor` | `EngineSnapshot.epoch_anchor` | semantic |
| `timing.settled_at_utc` | `WatchManager` settled pair (§2) | metadata |
| `timing.delivery_lag_seconds` | `EngineSnapshot.delivery_lag_seconds` (telemetry) | metadata |
| `source.source_mode` | manager descriptor: the validated `WatchRequest.mode`, `sim` for the registry path; `dataset_replay` for in-process dataset replay | metadata |
| `source.data_feed` | `feed_basis.data_feed_for_scenario` for watches; the immutable dataset manifest `data_feed` for `dataset_replay` | metadata |
| `source.scenario` | `EngineSnapshot.scenario` | metadata |
| `source.window_start_utc`, `source.window_end_utc` | manager descriptor: the parsed UTC request window (historical), else null | metadata |
| `source.dataset_id`, `source.dataset_checksum` | dataset manifest (`dataset_replay`), else null | metadata |
| `source.session_id` | manager descriptor: stable id of the watch instance; null for `dataset_replay` | metadata |
| `source.session_started_at_utc` | manager descriptor: wall clock at watch creation; null for `dataset_replay` | metadata |
| `engine_identity.engine_semantics_version` = `tape-engine-v1` | module constant in `app/engine/tape_engine.py` | semantic |
| `engine_identity.config_fingerprint` | `Config.config_fingerprint()` | semantic |
| `engine_identity.profile_id` | manager descriptor (`PROFILE_DEFAULT`; §3 refusal) | semantic |
| `engine_identity.tape_state_vocabulary[]` | the classifier's closed state list | semantic |
| `engine_identity.windows[]` | `Config.windows` labels | semantic |
| `engine_identity.warmup_min_events` | `Config.warmup_min_events` | semantic |
| `implementation_provenance.engine_source_hash` | process-level resolver over the fixed `app/engine/*.py` tuple (§6) | metadata |
| `implementation_provenance.source_revision` | process-level git resolver (§6) | metadata |
| `implementation_provenance.worktree_dirty` | process-level git resolver (§6) | metadata |
| `observation_hash` | projection (§6) | integrity |
| `artifact_hash` | projection (§6) | integrity |

Deliberately excluded: `recent_trades`, `event_log` (UI payloads served by `/tape/{ticker}/events`), and
any verdict, decision, readiness, freshness-acceptability or actionability field.

The generic path, which every iteration must preserve:

```
market/provider event
  → TapeEngine.process_event            (clock-free; the one semantic producer)
  → WatchManager stamps status/lag and records settled_at for THAT snapshot
  → atomic ManagedObservationRead {EngineSnapshot, SourceDescriptor, settled_at, end_reason}
  → pure build_tape_observation(...)     (no clock, no git, no engine access)
  → TapeObservation
  → GET /tape/{ticker}/observation       (transport only; nothing recomputed)
```

## 2. Time law — three concepts, honest nulls, atomic read

**`observed_at_utc`** is the UTC market/event timestamp of the latest processed event (quote or trade)
represented by this `EngineSnapshot`: `iso(epoch_anchor + timing.logical_timestamp)`. It is not "last trade
time", not "time the tape state last changed", and not "time the classification last changed". It is
**null** if and only if `epoch_anchor` is null OR the engine has processed no event, which the snapshot
exposes as `bid`, `ask` and `last` all null (`MarketState` never clears). `connecting` and `waiting` imply
null; `stale`, `closed` and `failed` with zero events are null; `paused` after events keeps the last
observation.

**`timing.settled_at_utc`** is the manager-recorded wall-clock instant at which THIS snapshot became
settled and externally readable: stamped by the feeder after `process_event`, the status write and the
delivery-lag write, in every managed mode (sim, live, historical); null for in-process dataset replay. A
lifecycle-only rebuild (stale flip, pause, resume, close, fail) carries the previous settled time forward
— no new event, same availability. The engine never reads it.

**`available_at_utc`** is actual system availability time when measured, else null. It is never derived
from event time and never `observed_at_utc + delivery_lag_seconds`. By `availability_basis`, fixed by
`source.source_mode`:

| `source_mode` | `availability_basis` | `available_at_utc` |
|---|---|---|
| `live` | `live_settled_wall_clock` | `= timing.settled_at_utc` (null until the first settled event) |
| `historical`, `dataset_replay` | `historical_arrival_unknown` | null — original vendor-arrival, receive, processing and external-availability times were never recorded |
| `sim` | `simulated_not_applicable` | null — the synthetic clock (`epoch_anchor = 2024-01-02T14:30:00Z`) carries no market information; `settled_at_utc` is still recorded as telemetry |

The live value is a measurement: under vendor clock skew it MAY precede `observed_at_utc`; the contract
does not clamp (clamping would manufacture). No `available_at_utc ≤ generated_at_utc` relation is
asserted either.

**`generated_at_utc`** is the wall clock at which this artifact projection was generated (the route passes
`now`; the builder reads no clock).

**`timing.delivery_lag_seconds`** is the existing feeder telemetry, verbatim (live: `wall − (anchor + ts)`
clamped at zero; paced replay: backlog against the pacing schedule). It may be cross-checked against the
timestamps on a controlled clock; it is never a source of truth for availability.

**Atomic-read invariant.** `timing.settled_at_utc` belongs to the exact `EngineSnapshot` serialized in the
same `TapeObservation`. `WatchManager` holds, per ticker, one immutable settled pair
`(EngineSnapshot, settled_at_epoch)` written in a single assignment by one helper after every processed
event and after every lifecycle-only mutation; `get_observation_source(ticker)` returns that pair with the
source descriptor and `end_reason` and never snapshots the engine at read time. A deterministic
interleaving test proves that an event N+1 processed but not yet settled cannot be paired with settled
time N (nor the reverse), and that a naive `(engine.snapshot(), settled_at)` read would mis-pair.

**Pinned ISO function.** Every UTC instant uses
`datetime.fromtimestamp(x, timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")`
— the repository's existing stamp format — never a hand-formatted string.

**Composed-validation note (binding disclosure).** Historical `TapeObservation` artifacts can support
deterministic composed replay using `observed_at_utc` + the declared event ordering + the frozen engine
semantics/config, establishing retrospective event-time compatibility under the declared replay
assumptions. They do not prove that an equivalent observation would have been externally available at
exactly the historical market-event timestamp in a prospective live system. This limitation is
machine-visible (`historical_arrival_unknown` + null availability). It is never "fixed" with an assumed
latency. A future dataset that records actual receive timestamps may support a stronger basis in a later
schema version.

## 3. Source, feed and session provenance

- `source.source_mode` is recorded by the manager from the validated watch request (`sim`, `live`,
  `historical`) or set to `sim` by the sim registry path; in-process dataset replay passes
  `dataset_replay`. It is never re-derived by a second scenario-prefix parser.
- `source.data_feed` comes from the one existing `data_feed_for_scenario(scenario, config)` for watches
  (`live ` → `iex`, `historical ` → `sip`, else `sim`) and from the immutable dataset manifest for
  `dataset_replay`. A guard asserts the two owners agree on every committed fixture dataset.
- `sim`, `iex` and `sip` are never pooled, equated or silently converted. REST serves `sim`, `live` and
  `historical` watches only; `dataset_replay` exists for in-process callers (tests, future replay
  consumers) through the same builder.
- `window_start_utc` / `window_end_utc` are the parsed UTC request window of a historical watch (the
  progressive chunks share it); null otherwise. They are request identity, distinct from the observed
  extent.
- `session_id` is a stable identifier of the watch instance that produced the observation (an existing
  per-watch identifier if one exists, else a uuid4 minted at watch creation); `session_started_at_utc` is
  the manager wall clock at watch creation. Two watches of the same ticker have different session ids.
  For `dataset_replay` both are null: the path is fully identified by `dataset_id + dataset_checksum`.
- Session identity is provenance only. Nothing under `app/engine/` may reference it (AST guard).
- `engine_identity.profile_id` is `PROFILE_DEFAULT` from the descriptor. The builder refuses (raises)
  when `profile_id` is `default` but `config.config_fingerprint()` differs from the process `CONFIG`
  fingerprint; it never invents a profile string.

## 4. Lifecycle honesty

| `lifecycle.stream_status` | How it arises | What the artifact shows | A consumer may conclude |
|---|---|---|---|
| `connecting` | engine constructed, stream not yet open | `observed_at_utc`, `available_at_utc` null | not yet observing |
| `waiting` | stream open, no event yet | null times | healthy but waiting |
| `live` | at least one event processed and no gap flagged | times per basis; `warm` as-is | healthy current observation |
| `stale` | live watchdog saw no event for `stale_gap_seconds` (live basis only; possible with zero events) | last observation retained; its times unchanged, or null with zero events | stale observation |
| `paused` | operator pause through the manager | last observation retained; `settled_at_utc` unchanged | paused |
| `closed` | natural end (`end_reason = stream_closed`) or cancel/switch (`end_reason` null) | last observation retained | closed stream |
| `failed` | feeder exception | last observation retained (null times with zero events); `end_reason` null in v1 | failed feed |
| watch stopped | `stop()` removes the engine | REST answers 404; `watch_stopped` is observable in-process only | not watched |

`stale` never occurs on the `historical`, `dataset_replay` or `sim` bases — replay freshness is not a
Tapeology concept. The artifact never rewrites, suppresses or nulls `tape_state` or `confidence` on any
status; the consumer receives both `tape_state` and `lifecycle` and decides usability under its own policy.

## 5. Ingestion-path equivalence under an identical valid event stream

> When the exact same valid ordered event stream is fed through different ingestion mechanisms into the
> same frozen engine semantics and configuration/profile, the resulting machine-observation semantic set
> (§6) — and therefore `observation_hash` — is identical. Only provenance/source/lifecycle metadata may
> differ.

A **valid ordered event stream** has non-decreasing epochs; at equal epoch every quote precedes every
trade; relative order within a kind is preserved (the order `HistoricalProvider` emits and the live-socket
merge fixture builds). For out-of-order input the live path's monotonic clamp and the replay path's global
sort may legitimately differ, and no equivalence is claimed.

The mechanisms compared are the replay feeder (`_replay_events`) and the live feeder (`_feed_live` over
`LiveProvider`), on the committed PG SIP fixture and one seeded sim scenario, with per-tick capture.

**Explicit non-claim.** This invariant does not assert semantic equality between independently sourced
IEX and SIP market data, which may contain different events. Feed bases are never pooled. If any ingestion
path produces semantic divergence on identical ordered input, that is a blocking finding to report — never
excluded by widening the metadata partition.

## 6. Identity — semantic vs implementation; partition; hash laws

**Semantic identity** (`engine_identity`): `engine_semantics_version` (`tape-engine-v1`, a module constant
in `app/engine/tape_engine.py`, bumped only by an owner act when classifier, feature, aggressor or warm-up
semantics change — the existing pinned/golden/profile/determinism tests are the tripwires; no automated
inference), `config_fingerprint`, `profile_id`, `tape_state_vocabulary`, `windows`, `warmup_min_events`.

**Implementation provenance** (`implementation_provenance`), resolved once per process, never per request:

- `engine_source_hash` — sha256 over the source bytes of a fixed tuple of `app/engine/*.py` modules in a
  fixed order (a test asserts the tuple equals the sorted module set so nothing is silently omitted). It
  changes on comment edits and is unaffected by git state. **`engine_source_hash` identifies exact
  implementation source and is fail-closed provenance. A changed source hash does not by itself claim that
  the tape semantics changed.**
- `source_revision` — the commit hash (`git rev-parse HEAD`) or null.
- `worktree_dirty` — `true` / `false` / `null` under the declared dirty-state check
  `git status --porcelain --untracked-files=no -- apps/backend/app` (tracked backend source only, so run
  and doc artifacts neither mask code drift nor cry wolf). Clean: `(abc123, false)` — the process started
  from `abc123` and the checked source was clean. Dirty: `(abc123, true)` — HEAD was `abc123` but the
  running implementation includes uncommitted changes; `engine_source_hash` is the exact engine-source
  provenance. Git unavailable: `(null, null)` — never invented.

**Partition** (leaf paths; a test asserts the four groups cover the schema exactly once):

- **Machine observation semantics** (→ `observation_hash`): `schema_version`, `provider`, `ticker`,
  `tape_state`, `confidence`, `warm`, `primary_window`, `features`, `trade_event_count`, `market.bid`,
  `market.ask`, `market.spread`, `market.last`, `observed_at_utc`, `timing.logical_timestamp`,
  `timing.epoch_anchor`, `engine_identity.*`.
- **Provenance / source / lifecycle metadata**: `available_at_utc`, `availability_basis`,
  `generated_at_utc`, `timing.settled_at_utc`, `timing.delivery_lag_seconds`, `lifecycle.*`, `source.*`,
  `implementation_provenance.*`.
- **Explanatory metadata**: `observations[]` — human-readable prose for understanding, audit and
  debugging; never machine identity; no `reason_codes[]` is invented this era.
- **Integrity**: `observation_hash`, `artifact_hash`.

**Canonical encoding**: `json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")`, then
sha256 hex — the repository's existing idiom. Serialization order never changes either hash.

**`observation_hash`** = sha256(canonical encoding of the machine-observation semantic set). It is a
**machine-observation equivalence identity**: two artifacts may share it across different watch sessions,
generation times, source metadata and implementation source hashes, provided their declared semantic set
is identical. It is NOT the unique identifier of the exact evidence object another system consumed.

**`artifact_hash`** = sha256(canonical encoding of the whole artifact minus `artifact_hash`). It
**identifies the exact `TapeObservation` evidence artifact instance** — provenance, source/session/lifecycle
metadata, explanatory text, implementation provenance (including `worktree_dirty`) and generation time
under the declared canonical encoding. It is intentionally non-reproducible across projections. **A
downstream consumer recording "which exact Tapeology evidence object did this evaluation use?" references
`artifact_hash`, not only `observation_hash`.**

The name `content_hash` is not used in this contract (elsewhere it means reproducible research content).

## 7. The consumer path

- `GET /tape/{ticker}/observation` is the one canonical read-only machine path. It answers 404 for an
  unwatched ticker exactly like its `/tape/*` siblings, and 200 with the v1 artifact otherwise.
- The route owns transport only: it consumes `manager.get_observation_source(ticker)` and calls
  `build_tape_observation` with `now`; it calls no engine method and recomputes no field.
- **Builder/route equivalence is semantic JSON equality**: the route's parsed JSON object is
  field-for-field and value-for-value equal to the builder's output for the same atomic read and the same
  `now`. HTTP key order is not part of the contract; byte canonicalization lives only in the hash law, and
  both hashes are recomputable from the served JSON.
- The existing MCP `get_endpoint` tool proxies the route byte-identically (its existing contract); no new
  named MCP tool is added and the MCP contract stays at v8 / 28 tools.
- A GET never starts a watch, a computation, a git call or a recording.
- A consumer never scrapes UI text, combines endpoints, derives timestamps, recalculates freshness,
  recomputes confidence or tape state, or infers feed basis. It records `artifact_hash` to reference the
  exact evidence it consumed.

## 8. English canonical core

All new contract identifiers, schema names, enum values, field names, tests and canonical persisted values
are English-only ASCII. Non-English text may exist only in UI/localized display or raw source evidence,
neither of which this era touches. A guard scans schema keys, enum values and module identifiers (not
free-text labels such as the existing historical scenario string, which carries an en dash).

## 9. Provider ownership

Tapeology owns: tape state, confidence, features, the timing facts it can honestly know, feed/source/session
provenance, lifecycle, observation identity and artifact identity.

The external consumer owns: whether an observation satisfies its composite policy, whether the observation's
freshness is acceptable for that policy, whether its policy remains pending, and whether its complete
system returns READY, NO_TRADE or NO_VERDICT. Tapeology does not know those concepts and never returns
them or any equivalent (`trade_allowed`, verdicts, readiness).

## 10. Refusals — what this era does NOT do

No logic of the form `if tape_state == bid_absorption: trade = true`. No candidate matching against an
external screener, no external playbook logic, no position sizing, no stop calculation, no portfolio risk,
no READY / NO_TRADE / NO_VERDICT, no composite-policy promotion, no "validated edge" claims, no autonomous
alerts, no broker execution. No import of, or path reference to, any external consumer system. No second
representation of a value the engine already owns. No recomputation of any tape feature, state, confidence
or freshness outside the engine.

---

## Non-Goals

- Discovering, mining or proving profitability of any tape condition; the economic value of an observable
  is a property of the consumer's frozen composite policy, not of this contract.
- Redesigning the tape classifier, tuning thresholds, inventing a new tape feature, or bumping the
  classifier version for style.
- Any new Foundry epoch, source revision, research primitive, OOS acquisition, Vault, graduation or Referee
  act (§0.8 law 5 is not applicable: this is an operator pivot outside the catalog and no research
  primitive is built).
- A CLI, a WebSocket embedding, a listing endpoint, a named MCP tool, or any new UI surface.
- Fixing the live provider's dropped preservation fields (`conditions/exchange/tape/trade_id`); the
  engine never reads them.
- Modelling, guessing or reconstructing historical arrival latency or receive time.
- Machine-readable `reason_codes[]`; semantic-version inference automation; additional live-session
  business logic beyond provenance.
- The external consumer's implementation, in this or any other repository.

---

## Constraints

- Current foundation is the completed Hypothesis Foundry stack on latest `main`; every Foundry artifact,
  ledger and disposition stays byte-identical.
- `config_fingerprint` remains `08e471b10130e1e2`; this era adds zero `Config` fields (module constants
  only, e.g. `ENGINE_SEMANTICS_VERSION`, `OBSERVATION_SCHEMA_VERSION`).
- `app/engine/` stays free of wall-clock reads, randomness, git access and session identity.
- Mandatory evidence is deterministic and local: Sim mode on the local backend, the committed fixtures
  (`tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json`, `tests/fixtures/datasets_j03/`), and the
  `HistoricalProvider` / `LiveProvider` / `FakeAdapter` harnesses with a monkeypatched clock in
  `watch_manager`. A real-provider smoke test may exist only as an environment-gated optional integration
  test (skipped unless `TAPEOLOGY_REAL_PROVIDER_SMOKE=1` and credentials resolve); it is never journey
  acceptance and can never block `GOAL_ACHIEVED`. Production Alpaca support is untouched.
- Process-level implementation provenance (`source_revision`, `worktree_dirty`) is resolved once at
  process start; no git call per request.
- The MCP contract stays at v8 / 28 tools; the existing no-write, no-app-import and byte-identity guards
  are extended, never weakened.
- Iteration depth: lean by default with `Frontend Present: no` (browser QA still runs and screenshots the
  served JSON); if the engine escalates an iteration to full depth, the iteration spec sets
  `Frontend Present: yes` with the served JSON page as the browser surface and answers the UI-evolution
  audit "no user-facing capability introduced". No frontend file changes this era.
- Ingestion-path test knobs: replay leg with `speed_cell=[inf]` and `WatchManager(CONFIG, pace=0.0)`,
  live leg over `LiveProvider(ticker, _aiter(records), "live TICKER")`, waits of at least 30 s, per-tick
  capture through `add_observer`.
- Goal Mode host-guard CPU/thread/memory confinement remains mandatory.
- Recommended launch: `/goal observation-contract --max-iter 40`; hitting the cap is resumable and is not a
  verdict.

---

## Design Direction

- Visual style: **no visual change this era.** The cockpit (`/`), `/structure` and `/desk` render exactly
  as before; the only new surface is served JSON.
- Mood: contract document / instrument calibration record, not a signal dashboard.
- No copy anywhere in the served artifact implies urgency, prediction, confidence beyond the served value,
  or a trading action.

---

## Product Shape

### Navigation / information architecture

Existing product routes remain unchanged: `/` Cockpit, `/structure`, `/desk`. No page, panel, link or
component is added or modified.

### Canonical REST owner

`GET /tape/{ticker}/observation` — the only home of `TapeObservation`. It projects, through
`build_tape_observation`, values whose single owners are named in Constitution §1. No other endpoint, page
or tool computes any of these values.

### Canonical values (single source of truth)

- every field of `TapeObservation` v1, pinned to its owner in Constitution §1;
- the three time concepts and the `availability_basis` enum (§2);
- `source.*` provenance and session identity (§3);
- the lifecycle table (§4);
- `engine_identity.*` and `implementation_provenance.*` (§6);
- `observation_hash` and `artifact_hash` (§6).

The pre-existing cockpit chart arithmetic `epoch_anchor + logical_ts` in `PriceChart.tsx` is display-only
and unchanged; the artifact is the canonical external owner of absolute observation time.

### MCP

No new tool. The existing read-only `get_endpoint` proxy reaches `/tape/{ticker}/observation` byte-identically.

---

## Must-have user journeys

Six fixed journeys. Every journey has a Sim-mode browser step on the served JSON (the no-screenshot rail)
and deterministic test steps that name the exact pytest command; each test module ships at least one
seeded counter-test (named `test_counterexample_*`) proving its guards can fail. Sim tickers are
`SIM-BUYER`, `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`, `SIM-SHIFT`, `SIM-REVERSAL`.

- **J-01: The artifact is a pure projection with semantic identity, provenance and integrity**
  - Steps:
    1. Visit `/`. In the `Data source` group select `Simulated`, type `SIM-BIDABS` into the `Ticker`
       field, press `Watch`, and wait until the status dot reads `live`.
    2. Open `/tape/SIM-BIDABS/observation` (served JSON). Confirm the body contains
       `"schema_version": "tape-observation-v1"`, `"provider": "tapeology"`, `"ticker": "SIM-BIDABS"`, and
       the keys `tape_state`, `confidence`, `warm`, `primary_window`, `features`, `trade_event_count`,
       `market`, `observations`, `lifecycle`, `timing`, `source`, `engine_identity`,
       `implementation_provenance`, `observation_hash`, `artifact_hash`.
    3. Confirm `engine_identity.engine_semantics_version` is `tape-engine-v1`,
       `engine_identity.config_fingerprint` is `08e471b10130e1e2`, `engine_identity.profile_id` is
       `default`, `source.session_id` is non-empty, `source.session_started_at_utc` is an ISO-8601 UTC
       instant ending in `Z`, and `implementation_provenance` shows a 64-hex `engine_source_hash`, a
       `source_revision` (40-hex or null) and a `worktree_dirty` (true, false or null).
    4. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_projection.py -q`
       and record the `N passed` summary line (0 failed). The module contains, each as a named test: the
       sentinel-mutation projection (a snapshot with patched `tape_state`, `confidence` and `features` is
       echoed verbatim); the AST recompute guard (the module imports no classifier or feature computation
       and references no threshold); `trade_event_count == snapshot.event_count` with no re-count; both
       hashes recomputable from the §6 encoding; key-order permutation changes neither hash;
       `observation_hash` changes when `engine_semantics_version`, `config_fingerprint` or `profile_id`
       changes and does not change when `engine_source_hash`, `worktree_dirty`, `observations[]` wording,
       `generated_at_utc`, `session_id` or `settled_at_utc` changes; `artifact_hash` changes for each of
       those; clean, dirty and git-unavailable provenance triples are distinct while `engine_source_hash`
       is identical across them; the provenance resolver runs once per process and the route makes no git
       call; the engine-source module tuple equals the sorted set of `app/engine/*.py`; the profile
       refusal; the four-group partition covers every leaf path exactly once; the schema constants equal
       the field table of `docs/observation-contract-spec.md`; and a doc-lint asserting the spec states that
       exact downstream evidence references use `artifact_hash`.
    5. Confirm the module's `test_counterexample_*` tests prove the recompute guard, the partition test and
       the hash-law tests can fail.
  - Acceptance: the served JSON at `/tape/SIM-BIDABS/observation` shows `"schema_version": "tape-observation-v1"`,
    `engine_semantics_version` `tape-engine-v1`, `config_fingerprint` `08e471b10130e1e2`, a non-empty
    `source.session_id`, a 64-hex `observation_hash` and a 64-hex `artifact_hash`; every served field traces
    to exactly one owner in Constitution §1; and `tests/test_tape_observation_projection.py` passes with 0
    failures and its `test_counterexample_*` tests present.

- **J-02: Market-event time, measured availability and generation time are three distinct, honest instants, read atomically**
  - Steps:
    1. Visit `/`. In the `Data source` group select `Simulated`, type `SIM-BIDABS` into the `Ticker`
       field, press `Watch`, and wait until the status dot reads `live`.
       Open `/tape/SIM-BIDABS/observation`. Confirm
       `observed_at_utc` starts with `2024-01-02T14:3` (the synthetic anchor clock), `available_at_utc` is
       `null`, `availability_basis` is `simulated_not_applicable`, and both `timing.settled_at_utc` and
       `generated_at_utc` carry today's date — three separate fields, two of them on a different day from
       the market-event time.
    2. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_time.py -q` and
       record the `N passed` summary line (0 failed). The module contains, each as a named test, without
       any network call: `observed_at_utc` equals the latest processed event (a quote-only prefix, then a
       trade) for the sim provider, for `HistoricalProvider` over the committed PG fixture, for
       `DatasetStore.replay` over a committed `datasets_j03` fixture, and for `LiveProvider` over the
       merged fixture records; both null clauses (`epoch_anchor` null; no event processed); historical and
       `dataset_replay` artifacts always carry `available_at_utc = null` and
       `availability_basis = historical_arrival_unknown`, with `test_counterexample_*` failing when event
       time is copied into `available_at_utc`; on the live basis `available_at_utc == timing.settled_at_utc`
       from the manager-recorded monkeypatched clock, with `test_counterexample_*` failing when the builder
       derives `observed + delivery_lag`; `settled − observed` agrees with `delivery_lag_seconds` on the
       controlled clock (telemetry check only); the atomic-read interleaving test (event N settled, event
       N+1 processed without settling: the read still pairs snapshot N with settled N; after settling N+1
       it pairs N+1 with settled N+1; a naive `(engine.snapshot(), settled_at)` read is shown to mis-pair);
       a source scan proving `app/engine/` contains no `time.time`, `datetime.now`, `utcnow`, `random` or
       git access; `availability_basis` is exhaustive per `source_mode`; the pinned ISO function
       round-trips to the microsecond; two `DatasetStore.replay` reruns yield identical `observation_hash`
       at every tick.
    3. Confirm the module's `test_counterexample_*` tests are present and pass.
  - Acceptance: the served JSON shows `observed_at_utc` beginning `2024-01-02T14:3`, `"available_at_utc": null`,
    `"availability_basis": "simulated_not_applicable"`, and `timing.settled_at_utc` and `generated_at_utc` on
    today's date; and `tests/test_tape_observation_time.py` passes with 0 failures, with every §2 law and the
    interleaving test present as named tests.

- **J-03: Lifecycle, feed basis and session identity stay honest**
  - Steps:
    1. Visit `/`. In the `Data source` group select `Simulated`, type `SIM-BIDABS` into the `Ticker`
       field, press `Watch`, and wait until the status dot reads `live`.
       Open `/tape/SIM-BIDABS/observation` and confirm `lifecycle.stream_status` is `live` and
       `lifecycle.paused` is `false`; note `source.session_id` and `timing.settled_at_utc`.
    2. On `/` press the `Pause watching` control, reload the observation JSON, and confirm
       `lifecycle.stream_status` is `paused`, `lifecycle.paused` is `true`, `tape_state` is unchanged from
       step 1, and `timing.settled_at_utc` is unchanged from step 1.
    3. Press `Resume watching`, reload, and confirm `lifecycle.stream_status` is `live` again.
    4. Press `Stop watching`, reload `/tape/SIM-BIDABS/observation`, and confirm the response is a 404 body.
    5. On `/` press `Watch` again for `SIM-BIDABS` (`Simulated`), wait for `live`, reload the observation JSON,
       and confirm `source.session_id`
       differs from the value noted in step 1 while `source.source_mode` is `sim` and `source.data_feed` is
       `sim`.
    6. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_lifecycle_feed.py -q`
       and record the `N passed` summary line (0 failed). The module contains, each as a named test: a
       table-driven pass over all seven statuses using the existing lifecycle harness (plus `paused`,
       natural `closed` with `end_reason = stream_closed`, in-process `watch_stopped`, `failed` with
       `end_reason = null`, and live `waiting`/`stale` with zero events yielding null times); `tape_state`
       and `confidence` are never nulled or rewritten on any status; the live basis via `LiveProvider`
       yields `data_feed = iex` and `availability_basis = live_settled_wall_clock`, the historical fixture
       yields `sip` and `historical_arrival_unknown`, sim yields `sim` and `simulated_not_applicable`, and no
       two bases are ever equal; dataset feed-owner agreement on every committed fixture dataset;
       `source_mode` recorded from the validated request with no second scenario-prefix parser (AST);
       session identity present and stable within a watch, different across two watches of the same
       ticker, and absent from `app/engine/` (AST); no actionability field or token anywhere in the
       artifact.
    7. Confirm the module's `test_counterexample_*` tests are present and pass.
  - Acceptance: the served JSON shows `lifecycle.stream_status` moving `live` → `paused` → `live` with
    `tape_state` and `timing.settled_at_utc` unchanged across the pause, `/tape/SIM-BIDABS/observation`
    answers 404 after `Stop watching`, the re-watch shows a different `source.session_id`; and
    `tests/test_tape_observation_lifecycle_feed.py` passes with 0 failures, so from the artifact alone a
    consumer can tell healthy-waiting, healthy-current, stale, failed and closed apart and no feed basis is
    pooled or equated.

- **J-04: Ingestion-path equivalence under an identical valid event stream**
  - Steps:
    1. Visit `/`. In the `Data source` group select `Simulated`, type `SIM-BIDABS` into the `Ticker`
       field, press `Watch`, and wait until the status dot reads `live`.
       Press `Pause watching`, then open `/tape/SIM-BIDABS/observation` twice (two reloads). Confirm
       `observation_hash` is identical across the
       two loads while `generated_at_utc` and `artifact_hash` differ — the equivalence identity versus the
       exact evidence identity, visibly.
    2. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_path_equivalence.py -q`
       and record the `N passed` summary line (0 failed). The module feeds the committed PG SIP fixture and
       one seeded sim scenario, each as a valid ordered event stream, through `_replay_events` and through
       `_feed_live` over `LiveProvider`, capturing every tick through `add_observer`; at every captured tick
       and at end the machine-observation semantic set and `observation_hash` are identical, while the two
       legs carry different `source.source_mode`, `source.data_feed` and session metadata and the assertion
       excludes exactly the metadata partition; a mutation proof (`test_counterexample_*`) shows the
       comparator can fail; the module docstring states the IEX-versus-SIP non-claim of Constitution §5
       verbatim.
    3. Confirm no semantic divergence was excluded by widening the metadata partition (the partition
       constants are unchanged from J-01).
  - Acceptance: two reloads of the paused `/tape/SIM-BIDABS/observation` show the same `observation_hash`
    and different `generated_at_utc` and `artifact_hash` values; `tests/test_tape_observation_path_equivalence.py`
    passes with 0 failures on both fixtures with its mutation counter-test present; and no semantic
    divergence was hidden by widening the metadata partition.

- **J-05: One read-only machine path**
  - Steps:
    1. Visit `/`. In the `Data source` group select `Simulated`, type `SIM-BIDABS` into the `Ticker`
       field, press `Watch`, and wait until the status dot reads `live`.
       Open `/tape/SIM-BIDABS/observation` and confirm the JSON renders with
       `"schema_version": "tape-observation-v1"`.
    2. Open `/tape/ZZZZ/observation` and confirm a 404 body (the same shape as `/tape/ZZZZ/state`).
    3. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_route.py -q` and
       record the `N passed` summary line (0 failed). The module contains, each as a named test: the route
       consumes `manager.get_observation_source(ticker)` and calls no `TapeEngine` method (AST); with
       `now` frozen, the route's parsed JSON is field-for-field and value-for-value equal to
       `build_tape_observation` for the same atomic read; `observation_hash` and `artifact_hash` are
       recomputable from the served JSON via the §6 encoding; the MCP `get_endpoint` response bytes equal
       the REST response bytes against a real uvicorn subprocess; the MCP no-write, no-app-import and
       28-tool pins are unchanged; a GET starts no watch, computation, git call or recording (manager and
       resolver call counts unchanged across 100 requests).
    4. Confirm the module's `test_counterexample_*` tests are present and pass.
  - Acceptance: `/tape/SIM-BIDABS/observation` renders the JSON with `"schema_version": "tape-observation-v1"`,
    `/tape/ZZZZ/observation` renders a 404 body, and `tests/test_tape_observation_route.py` passes with 0
    failures — a consumer obtains the canonical artifact from this one GET (or the existing `get_endpoint`
    proxy) with nothing else to combine, derive or recompute.

- **J-06: Guards and the regression sentinel**
  - Steps:
    1. Visit `/`. In the `Data source` group select `Simulated`, type `SIM-BIDABS` into the `Ticker`
       field, press `Watch`, and wait until the status dot reads `live`.
       Confirm `/tape/SIM-BIDABS/observation` serves the JSON. Then visit `/structure` and `/desk`; confirm
       each of the three pages loads with no new panel, link or control.
    2. Confirm `docs/goal-archive/goal-2026-09-02.md`, the dated opening note in
       `docs/research-directions.md`, and `docs/observation-contract-spec.md` exist, and that the spec's
       field table equals the schema constants (the J-01 parity test).
    3. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_guards.py -q` and
       record the `N passed` summary line (0 failed). The module contains, each non-vacuous with a
       `test_counterexample_*`: the copy-discipline lexicon (`find_violations`) plus a compound-identifier
       ban (`should_trade`, `trade_signal`, `entry_price`, `stop_loss`, `position_size`, `trade_allowed`,
       `READY`, `NO_TRADE`, `NO_VERDICT`, `PENDING_CONDITION`, `composite_policy`) over the observation
       module, its tests and a served artifact, with comments and docstrings stripped and a `SELF`
       exclusion; the external-system reference guard (`workstation`, `trendora`, `tensteps` absent,
       case-insensitively, under `apps/` and in `docs/observation-contract-spec.md`, with `docs/goal.md`,
       `docs/phases/`, `docs/goal-archive/` and `project-extensions/host-guard/` excluded explicitly); the
       English-only guard over schema keys, enum values and module identifiers; the real-provider isolation
       guard (no test module named `test_tape_observation_*` reaches `AlpacaAdapter` except the
       environment-gated smoke, which is skipped by default and whose failure cannot fail the suite); the
       mutator-call-site guard (every `TapeEngine` mutator call under `app/` lives in `watch_manager.py`
       methods that re-settle, or in `DatasetStore.replay`).
    4. Run the full backend suite `cd apps/backend && .venv/bin/python -m pytest tests/ -q` and the
       frontend compile `cd apps/frontend && npx tsc --noEmit`; record pass/skip/fail counts and the
       `tsc` error count (0). Confirm `config_fingerprint` is `08e471b10130e1e2`, the MCP contract is v8 /
       28 tools, and the existing classifier, profile-equivalence, determinism, observer-equivalence,
       epoch-anchor, stream-lifecycle, feed-basis and MCP suites are unchanged in content and green.
  - Acceptance: `/`, `/structure` and `/desk` render with no new panel, link or control;
    `tests/test_tape_observation_guards.py` and the full backend suite pass with 0 failures and `tsc` reports
    0 errors; `config_fingerprint` reads `08e471b10130e1e2`; the three era-open artifacts exist; and no
    mandatory step contacted an external service.

---

## Anti-goals

### Immutable project rails (`docs/research-directions.md` §0.3, verbatim)

1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
   trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
   tier-1 guard; new research code adds matching guard tests, never weakens them.)
2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
   fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
   imperative trading cues.
3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
   states and thresholds, and archived-era behavior stay byte-identical. New work is additive and
   versioned beside them, never a mutation of them.
4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
   through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
   labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
   feeds/fingerprints to manufacture a survivor.
5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
   (See the forming-bar rule in card 6.4.)
6. **Single source of truth** — each shared value is computed once, owned by one canonical
   endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
   violations.
7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
   requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
   research artifact.
8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
   MCP surface can change state.
9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never
   re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
10. **Persistence stays scoped** — no ambient recording of live streams; recording is an explicit,
    logged act.

### Source-authoring laws (`docs/research-directions.md` §0.8, verbatim; law 5 is not applicable to this era — an operator pivot outside the catalog that builds no research primitive)

1. **Hypothesis vs modifier.** A statement of the form "feature X adds confirm/veto
   information" is NOT a standalone directional hypothesis unless it explicitly names (a) the
   host setup / eligible population, (b) the relevant side or context, and (c) the directional
   return thesis. Otherwise it is a modifier / atlas / filter object. A future author may
   promote it ONLY through a new forward source revision that supplies all three. Never infer
   the missing host thesis.
2. **Representation fidelity.** A source formula may be represented by implementation code only
   when the two are formula-equivalent under the ratified methodology, or when an explicit named
   forward supersession exists. Monotonic similarity, signed/unsigned convenience, and "it is
   the feature we happen to have built" are NOT implicit supersession.
3. **Qualitative threshold fidelity.** There is no universal qualitative-word → quantile rule,
   and none may be invented. A load-bearing threshold is legal only if it is source-defined, an
   existing frozen constant, an exact frozen named construct, a true natural semantic boundary,
   or a newly owner-ratified value. Otherwise the source blocks. A generic quantile protocol is
   specifically forbidden: it would silently overwrite source-defined constants (Card 9.4's
   `z ≥ 4`, Card 9.5's `ratio ≥ 1.5`) while manufacturing values where the source states none
   (Study 1's "high", Study 3's "extreme").
4. **Proxy lineage.** A historical partial proxy is immutable provenance. A fully specified
   mechanism is a NEW forward `source_id` with scoped supersession. Never "lift" a proxy into a
   full mechanism and never screen a proxy under the full mechanism's name.
5. **Engineering on demand.** Do not build a research primitive because a blocked source might
   one day use it. Engineering is justified only when at least one forward source is otherwise
   scientifically complete AND that primitive is its remaining blocker. Corollary: a shared
   primitive serving several blocked sources is still not justified if every one of them is
   blocked on something else as well.
6. **Prerequisite fidelity.** When a source names another card or spec as the provider of a
   load-bearing construct, that prerequisite must ACTUALLY define the construct referenced.
   Conceptual similarity, a matching baseline window, or a shared name is insufficient. If the
   named prerequisite does not define the referenced construct, **block** — never invent or
   extend it to fit. Note the two distinct failure modes: a prerequisite that is *unbuilt*
   (Card 9.2 → Card 8.2), and a prerequisite that is *built-or-buildable but supplies a
   different construct* (Card 9.4 → Card 5.5, below). Both block; only the first is fixed by
   building it.

### Era-specific anti-goals (checkable)

- No logic of the form `if tape_state == X: trade = True`; no field, token or copy that reads as a trading
  action, readiness or verdict (READY, NO_TRADE, NO_VERDICT, `trade_allowed`, PENDING_CONDITION or any
  equivalent) anywhere in the artifact, the module, its tests or the spec's served surface.
- No candidate matching against an external screener, no external playbook logic, no position sizing, no
  stop calculation, no portfolio risk, no composite-policy promotion, no "validated edge" claim, no
  autonomous alert, no broker execution.
- No second state engine, no second classifier, no change to the tape classifier, its thresholds, its five
  states, or the feature set; no new tape feature; no strategy mining; no change to any Foundry artifact or
  science.
- No consumer-specific business logic; no import of, or path reference to, Workstation, Trendora or
  TenSteps under `apps/` or in `docs/observation-contract-spec.md` (guard-enforced; `docs/goal.md`,
  `docs/phases/`, `docs/goal-archive/` and `project-extensions/host-guard/` are excluded from the scan).
- No non-English identifier, schema name, enum value, field name, test name or persisted value in the
  contract.
- No recomputation of any tape feature, state, confidence, freshness or feed basis outside the engine and
  the one existing `data_feed_for_scenario`; no second scenario-prefix parser.
- No `available_at_utc` that is not a manager-measured settled instant; no `observed_at + delivery_lag`
  reconstruction; no availability before the underlying event or state existed.
- No latency modelling, no guessed vendor latency constant, no historical receive-time reconstruction.
- No pooling, equating or silent conversion between `sim`, `iex` and `sip`.
- No route that snapshots an engine for the observation; the atomic manager read is the only source.
- No invented git provenance: `source_revision` and `worktree_dirty` are null when unavailable, never
  guessed; no git call per request.
- No `content_hash` field; no `reason_codes[]`; no semantic-version inference automation.
- No mandatory journey or test that requires Alpaca, the network, credentials or market hours.
- No new UI page, panel, link, component or frontend file change; no new `Config` field; no named MCP
  tool; no CLI; no WebSocket embedding; no listing endpoint.
- No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`,
  `test_copy_discipline.py`, `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`,
  `test_mcp_server.py`, `test_stream_lifecycle.py`, `test_observer_equivalence.py` and
  `test_epoch_anchor.py` stay green and unedited except for additive registrations.

### Goal-Mode / automation anti-goals

- No Goal Mode workaround that edits, deletes, skips or xfails a guard merely to pass a journey.
- No browser proof based on a fabricated state presented as real; fixture and real views must be visibly
  distinguished.
- No weakening or bypass of `project-extensions/host-guard/host-guard.env`; Goal Mode pauses
  `AWAITING_HOST_GUARD` if confinement cannot be established.
- No post-`GOAL_ACHIEVED` proposer or `AUTO:journeys` self-extension (the proposer is retired upstream).
- Anti-goal violations use the existing Goal Mode violation state/disposition machinery; they are never
  dismissed in prose.

---

# Binding Execution Order

Goal Mode may decompose implementation work, but this partial order is mandatory:

1. **Constants, builder and hash laws.** `ENGINE_SEMANTICS_VERSION`, schema constants, the partition
   constants, `build_tape_observation`, `observation_hash` / `artifact_hash`, the projection tests (J-01).
2. **Time law, settled clock and atomic read.** Manager-recorded settled pair, `get_observation_source`,
   the three time fields, `availability_basis`, the interleaving test, the engine clock-free scan (J-02).
3. **Descriptor, lifecycle and provenance.** Source/session descriptor, feed-owner agreement, lifecycle
   table tests, process-level `source_revision` / `worktree_dirty` (J-03, J-01 provenance tests).
4. **Ingestion-path equivalence.** Replay leg versus live leg on both fixtures with per-tick capture (J-04).
5. **Route and machine path.** `GET /tape/{ticker}/observation`, JSON/value equality, `get_endpoint`
   byte-identity, MCP pins (J-05).
6. **Guards and sentinel.** Copy/compound ban, external-system reference, English-only, real-provider
   isolation, mutator-call-site guards; full suite; era-open artifact checks (J-06).

A route that reads an engine directly, an `available_at_utc` derived from event time, or a semantic
divergence hidden by widening the metadata partition is a critical anti-goal violation, not an iteration
opportunity.

---

# Required Trap Coverage

Deterministic tests must cover at least the following (journey in brackets):

1. Artifact is a pure projection of engine-owned facts (sentinel mutation echoed verbatim) [J-01].
2. No feature, state, confidence or freshness is recomputed (AST guard + counter-test) [J-01].
3. `trade_event_count` equals the engine-owned trade count without re-counting [J-01].
4. Both hashes recomputable from the documented canonical encoding; key order changes neither [J-01].
5. `observation_hash` changes with `engine_semantics_version`, `config_fingerprint`, `profile_id` [J-01].
6. `observation_hash` unchanged by `engine_source_hash`, `worktree_dirty`, `observations[]` wording,
   `generated_at_utc`, session fields, `settled_at_utc` [J-01, J-04].
7. `artifact_hash` changes with each of the metadata changes in item 6 [J-01, J-04].
8. Engine semantic version exposed separately from the exact source hash [J-01].
9. Clean, dirty and git-unavailable provenance are distinct; `engine_source_hash` identical across them
   [J-01].
10. Provenance resolved once per process; no git call per request [J-01, J-05].
11. Engine-source module tuple equals the sorted `app/engine/*.py` set [J-01].
12. Profile refusal when `default` is claimed under a non-default fingerprint [J-01].
13. Four-group partition covers every leaf path exactly once [J-01].
14. Schema constants equal the spec's field table; spec states the `artifact_hash` reference rule [J-01].
15. `observed_at_utc` equals the latest processed quote-or-trade time in sim, historical fixture, dataset
    replay and `LiveProvider` contexts [J-02].
16. Both null clauses for `observed_at_utc` [J-02].
17. Historical and dataset replay: `available_at_utc = null`, `historical_arrival_unknown`; counter-test
    fails on event-time copying [J-02].
18. Live: `available_at_utc == settled_at_utc` from the manager clock; counter-test fails on
    `observed + lag` derivation [J-02].
19. `settled − observed` agrees with `delivery_lag_seconds` on a controlled clock (telemetry only) [J-02].
20. Atomic read: forced interleaving cannot pair snapshot N+1 with settled N or the reverse; naive read
    shown to mis-pair [J-02].
21. `app/engine/` contains no wall-clock, randomness, git or session-identity reference [J-02, J-03].
22. `availability_basis` exhaustive per `source_mode` [J-02].
23. Pinned ISO function round-trips to the microsecond [J-02].
24. Two dataset-replay reruns yield identical `observation_hash` at every tick [J-02].
25. All seven statuses (plus `paused`, both close reasons, `failed` with null `end_reason`, live
    `waiting`/`stale` with zero events) distinguishable from the artifact alone [J-03].
26. `tape_state` / `confidence` never nulled or rewritten on any status [J-03].
27. Feed bases `sim` / `iex` / `sip` explicit per context and never equal [J-03].
28. Dataset manifest `data_feed` agrees with `data_feed_for_scenario` on committed fixtures [J-03].
29. `source_mode` from the validated request; no second scenario-prefix parser [J-03].
30. Session identity present, stable within a watch, different across watches; provenance only [J-03].
31. No actionability field or token in the artifact [J-03, J-06].
32. Identical valid ordered stream through replay and live feeders → identical semantic set and
    `observation_hash` at every captured tick; metadata legs differ [J-04].
33. The equivalence test's docstring and the spec carry the IEX-versus-SIP non-claim [J-04].
34. Mutation proof: the equivalence comparator can fail [J-04].
35. Route consumes the atomic read and calls no engine method [J-05].
36. Builder output and REST parsed JSON are field/value equal under frozen `now` [J-05].
37. MCP `get_endpoint` bytes equal REST bytes; MCP pins (v8 / 28 tools, no-write, no-app-import)
    unchanged [J-05].
38. A GET starts no watch, computation, git call or recording [J-05].
39. 404 parity with sibling `/tape/*` routes [J-05].
40. Copy-discipline lexicon and compound-identifier ban, non-vacuous with counter-test [J-06].
41. External-system reference guard, non-vacuous with counter-test and explicit exclusions [J-06].
42. English-only guard over schema keys, enum values and identifiers [J-06].
43. No mandatory observation test reaches a real provider; the optional smoke is gated and cannot fail the
    suite [J-06].
44. Every engine-mutator call site under `app/` re-settles through the manager or is the unserved dataset
    replay [J-06].
45. Full suite, `tsc`, fingerprint pin, MCP contract and every existing classifier / profile /
    determinism / observer / epoch-anchor / lifecycle / feed-basis suite unchanged and green [J-06].

---

# Completion / Honest Stop

The Goal Mode evaluator may declare `GOAL_ACHIEVED` when J-01…J-06 pass on deterministic, local evidence
and:

- no era-open artifact is missing (`docs/goal-archive/goal-2026-09-02.md`, the dated opening note,
  `docs/observation-contract-spec.md`) and the spec's field table shows 0 differences from the schema constants;
- every field of `TapeObservation` v1 traces to its single owner and the partition test passes;
- no historical or dataset-replay artifact carries a non-null `available_at_utc`, no live artifact carries an
  `available_at_utc` other than its own settled instant, and no read pairs a snapshot with another
  observation's settled time;
- ingestion-path equivalence holds on both fixtures with no widened metadata partition;
- `config_fingerprint` is `08e471b10130e1e2`, the MCP contract is v8 / 28 tools, and no existing guard was
  weakened;
- no anti-goal violation is open (0 open dispositions);
- no mandatory evidence depended on Alpaca, the network, credentials or market hours.

There is no research ending to grade. The contract either exposes what Tapeology already knows with honest
time and provenance semantics, or it does not.

---

# Post-Era Owner Boundary

After a successful run the only planned follow-on is external to this repository: the composite-policy
consumer reads `GET /tape/{ticker}/observation`, records `artifact_hash` for every observation it evaluates,
and decides usability under its own policy. That consumer may not ask Tapeology to add readiness, verdicts,
freshness acceptability or actionability. A later Tapeology schema version (for example one carrying
recorded receive timestamps and a stronger availability basis) is a new named contract revision, never a
silent change to `tape-observation-v1`.
