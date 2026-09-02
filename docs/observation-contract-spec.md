# Tapeology Observation Contract — `TapeObservation` v1

**Status:** frozen at era open (2026-09-02). Normative content lives in the Contract Constitution of
`docs/goal.md` (Observation Contract v1); this document is the consumer-facing copy. The implementing run
may add implementation notes below the line marked *Implementation notes*; it may not change any field
semantics, enum value, null rule, partition or hash law without a new schema version.

`schema_version = "tape-observation-v1"` · `provider = "tapeology"`

## 1. Purpose

`TapeObservation` is a versioned, machine-readable envelope around Tapeology's existing deterministic tape
observation — the immutable `EngineSnapshot` that the tape engine builds once per processed event. It lets
an external consumer answer, for one symbol from one engine:

- What did Tapeology observe? (`tape_state`, `confidence`, `warm`, `features`, `market`)
- For which symbol? (`ticker`)
- At what market time? (`observed_at_utc`)
- When was that observation actually available, if that was measured? (`available_at_utc`,
  `availability_basis`)
- From which feed, watch session or dataset? (`source`)
- Under which engine semantics, configuration and implementation? (`engine_identity`,
  `implementation_provenance`)
- In which lifecycle state? (`lifecycle`)
- Which exact evidence object is this? (`artifact_hash`), and which observation is it equivalent to?
  (`observation_hash`)

It carries observation, timing, provenance, lifecycle and integrity facts only. It never carries a
trading conclusion, a readiness verdict, a freshness judgment or any actionability.

## 2. The generic path

```
market/provider event
  → TapeEngine.process_event            (clock-free; the one semantic producer)
  → WatchManager stamps status/lag and records settled_at for THAT snapshot
  → atomic ManagedObservationRead {EngineSnapshot, SourceDescriptor, settled_at, end_reason}
  → pure build_tape_observation(...)     (no clock, no git, no engine access)
  → TapeObservation
  → GET /tape/{ticker}/observation       (transport only; nothing recomputed)
```

No field is recomputed by the route. The route owns transport only.

## 3. Shape (illustrative values)

```json
{
  "schema_version": "tape-observation-v1",
  "provider": "tapeology",
  "ticker": "SIM-BIDABS",
  "observed_at_utc": "2024-01-02T14:31:07.250000Z",
  "available_at_utc": null,
  "availability_basis": "simulated_not_applicable",
  "generated_at_utc": "2026-09-02T13:05:41.118204Z",
  "tape_state": "bid_absorption",
  "confidence": 0.71,
  "warm": true,
  "primary_window": "30s",
  "features": {"10s": {"...": 0.0}, "30s": {"...": 0.0}},
  "trade_event_count": 123,
  "market": {"bid": 149.01, "ask": 149.03, "spread": 0.02, "last": 149.02},
  "observations": ["human-readable explanatory text"],
  "lifecycle": {"stream_status": "live", "paused": false, "end_reason": null},
  "timing": {
    "logical_timestamp": 67.25,
    "epoch_anchor": 1704205800.0,
    "settled_at_utc": "2026-09-02T13:05:41.104913Z",
    "delivery_lag_seconds": 0.0
  },
  "source": {
    "source_mode": "sim",
    "data_feed": "sim",
    "scenario": "bid_absorption",
    "window_start_utc": null,
    "window_end_utc": null,
    "dataset_id": null,
    "dataset_checksum": null,
    "session_id": "6f1c…",
    "session_started_at_utc": "2026-09-02T13:04:59.000000Z"
  },
  "engine_identity": {
    "engine_semantics_version": "tape-engine-v1",
    "config_fingerprint": "08e471b10130e1e2",
    "profile_id": "default",
    "tape_state_vocabulary": ["buyer_control", "seller_control", "bid_absorption", "ask_absorption", "unclear"],
    "windows": ["10s", "30s", "60s", "180s", "300s"],
    "warmup_min_events": 40
  },
  "implementation_provenance": {
    "engine_source_hash": "…64 hex…",
    "source_revision": "…40 hex or null…",
    "worktree_dirty": false
  },
  "observation_hash": "…64 hex…",
  "artifact_hash": "…64 hex…"
}
```

## 4. Fields and owners

Every field has exactly one owner and belongs to exactly one partition (§8). Nothing is recomputed.

| Field | Owner | Partition |
|---|---|---|
| `schema_version` | constant `tape-observation-v1` | semantic |
| `provider` | constant `tapeology` | semantic |
| `ticker` | `EngineSnapshot.ticker` | semantic |
| `observed_at_utc` | `EngineSnapshot.epoch_anchor + EngineSnapshot.timestamp` (§5) | semantic |
| `available_at_utc` | manager-recorded settled time per `availability_basis` (§5) | metadata |
| `availability_basis` | fixed by `source.source_mode` (§5) | metadata |
| `generated_at_utc` | route-supplied projection time (§5) | metadata |
| `tape_state` | `EngineSnapshot.tape_state` | semantic |
| `confidence` | `EngineSnapshot.confidence` | semantic |
| `warm` | `EngineSnapshot.warm` | semantic |
| `primary_window` | `EngineSnapshot.primary_window` | semantic |
| `features` | `EngineSnapshot.features` (window → feature name → value) | semantic |
| `trade_event_count` | `EngineSnapshot.event_count` — the existing trade-only counter, verbatim | semantic |
| `market.bid`, `market.ask`, `market.spread`, `market.last` | `EngineSnapshot.bid/ask/spread/last` | semantic |
| `observations[]` | `EngineSnapshot.observations` | explanatory |
| `lifecycle.stream_status` | `EngineSnapshot.stream_status` | metadata |
| `lifecycle.paused` | `EngineSnapshot.paused` | metadata |
| `lifecycle.end_reason` | `TapeEngine.end_reason` (via the atomic read) | metadata |
| `timing.logical_timestamp` | `EngineSnapshot.timestamp` | semantic |
| `timing.epoch_anchor` | `EngineSnapshot.epoch_anchor` | semantic |
| `timing.settled_at_utc` | `WatchManager` settled pair (§5) | metadata |
| `timing.delivery_lag_seconds` | `EngineSnapshot.delivery_lag_seconds` (telemetry) | metadata |
| `source.source_mode` | manager descriptor (validated watch mode; `sim` registry path; `dataset_replay` in-process) | metadata |
| `source.data_feed` | `data_feed_for_scenario` for watches; the immutable dataset manifest for `dataset_replay` | metadata |
| `source.scenario` | `EngineSnapshot.scenario` | metadata |
| `source.window_start_utc`, `source.window_end_utc` | manager descriptor: parsed UTC request window (historical), else null | metadata |
| `source.dataset_id`, `source.dataset_checksum` | dataset manifest (`dataset_replay`), else null | metadata |
| `source.session_id` | manager descriptor: stable id of the watch instance; null for `dataset_replay` | metadata |
| `source.session_started_at_utc` | manager descriptor: wall clock at watch creation; null for `dataset_replay` | metadata |
| `engine_identity.engine_semantics_version` | constant `tape-engine-v1` in `app/engine/tape_engine.py` | semantic |
| `engine_identity.config_fingerprint` | `Config.config_fingerprint()` | semantic |
| `engine_identity.profile_id` | manager descriptor (`default`) | semantic |
| `engine_identity.tape_state_vocabulary[]` | the classifier's closed state list | semantic |
| `engine_identity.windows[]` | `Config.windows` labels | semantic |
| `engine_identity.warmup_min_events` | `Config.warmup_min_events` | semantic |
| `implementation_provenance.engine_source_hash` | process-level resolver over the fixed `app/engine/*.py` tuple (§7) | metadata |
| `implementation_provenance.source_revision` | process-level git resolver (§7) | metadata |
| `implementation_provenance.worktree_dirty` | process-level git resolver (§7) | metadata |
| `observation_hash` | §8 | integrity |
| `artifact_hash` | §8 | integrity |

Deliberately excluded: `recent_trades`, `event_log` (served by `/tape/{ticker}/events`), and any verdict,
decision, readiness, freshness-acceptability or actionability field.

## 5. Time semantics — three distinct concepts

Tapeology distinguishes **market-event time**, **actual system availability time when measured**, and
**artifact-generation time**. It never manufactures historical information availability that was not
recorded.

### `observed_at_utc` — market-event time

The UTC market/event timestamp of the latest processed event (quote or trade) represented by this
`EngineSnapshot`: `iso(epoch_anchor + timing.logical_timestamp)`. It is not "last trade time" and not the
time the tape state last changed. It is **null** if and only if `timing.epoch_anchor` is null or the
engine has processed no event (`market.bid`, `market.ask` and `market.last` all null). `connecting` and
`waiting` imply null; `stale`, `closed` and `failed` with zero events are null; `paused` after events keeps
the last observation.

### `timing.settled_at_utc` — measured processing-settled time

The wall-clock instant, recorded by the watch manager, at which THIS snapshot became settled and externally
readable (after the event was processed and the status and delivery-lag fields were stamped). Recorded in
every managed mode (sim, live, historical); null for in-process dataset replay. A lifecycle-only change
(stale flip, pause, resume, close, fail) carries the previous settled time forward. The engine never reads
it.

### `available_at_utc` — actual availability when measured, else null

Never derived from event time and never `observed_at_utc + delivery_lag_seconds`.

| `source.source_mode` | `availability_basis` | `available_at_utc` |
|---|---|---|
| `live` | `live_settled_wall_clock` | `= timing.settled_at_utc` (null until the first settled event) |
| `historical`, `dataset_replay` | `historical_arrival_unknown` | null — original vendor-arrival, receive, processing and external-availability times were never recorded |
| `sim` | `simulated_not_applicable` | null — the synthetic clock (`epoch_anchor = 2024-01-02T14:30:00Z`) carries no market information |

The live value is a measurement; under vendor clock skew it may precede `observed_at_utc`, and the
contract does not clamp. No ordering between `available_at_utc` and `generated_at_utc` is asserted.

### `generated_at_utc` — artifact-generation time

The wall clock at which this artifact projection was generated. It is distinct from both of the above and
is excluded from `observation_hash` (§8).

### `timing.delivery_lag_seconds` — telemetry only

The feeder's existing measurement (live: wall clock minus `epoch_anchor + logical_timestamp`, clamped at
zero; paced replay: backlog against the pacing schedule). It is provenance, never a source of truth for
availability.

### Atomic-read invariant

`timing.settled_at_utc` belongs to the exact `EngineSnapshot` serialized in the same artifact. The watch
manager holds one immutable settled pair per ticker and serves snapshot, source descriptor and settled time
from that pair in one read; the route never snapshots the engine.

### Instant format

Every instant is ISO-8601 UTC with microseconds and a `Z` suffix, produced by
`datetime.fromtimestamp(x, timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")`.

### Composed-validation note (binding disclosure)

Historical `TapeObservation` artifacts can support deterministic composed replay using `observed_at_utc`,
the declared event ordering and the frozen engine semantics/configuration. That establishes retrospective
event-time compatibility under the declared replay assumptions. **It does not prove that an equivalent
observation would have been externally available at exactly the historical market-event timestamp in a
prospective live system.** The limitation is machine-visible (`availability_basis =
historical_arrival_unknown`, `available_at_utc = null`) and is never patched with an assumed latency.
Retrospective evidence establishes compatibility, not prospective proof. A future dataset with actual
recorded receive timestamps may support a stronger availability basis in a later schema version.

## 6. Source, feed and session provenance

- `source.source_mode ∈ {sim, live, historical, dataset_replay}` — recorded from the validated watch
  request (or set by the sim registry path); `dataset_replay` exists for in-process callers and is not
  served by REST in v1.
- `source.data_feed ∈ {sim, iex, sip}` — from the one existing feed-basis function for watches
  (`live ` → `iex`, `historical ` → `sip`, else `sim`) and from the immutable dataset manifest for
  `dataset_replay`. Bases are never pooled, equated or converted.
- `source.window_start_utc` / `source.window_end_utc` — the parsed UTC request window of a historical
  watch (request identity, distinct from the observed extent); null otherwise.
- `source.dataset_id` / `source.dataset_checksum` — dataset identity for `dataset_replay`; null otherwise.
- `source.session_id` / `source.session_started_at_utc` — the watch instance that produced the
  observation and when it started. A Tapeology snapshot is path-dependent (it reflects every event
  consumed since the watch began), so two observations for the same symbol at the same market time from
  different sessions are different evidence. Null for `dataset_replay`, whose path is fully identified by
  `dataset_id + dataset_checksum`. Session identity is provenance only and never enters engine
  computation.

## 7. Engine identity vs implementation provenance

**`engine_identity`** is the semantic identity of the producer:

- `engine_semantics_version` — `tape-engine-v1`. It changes only by an explicit owner act when classifier,
  feature, aggressor or warm-up semantics change.
- `config_fingerprint` — the configuration identity (`08e471b10130e1e2` at era open).
- `profile_id` — `default` (the frozen legacy profile that every watch runs).
- `tape_state_vocabulary`, `windows`, `warmup_min_events` — readable closed vocabularies derived from the
  same configuration.

**`implementation_provenance`** is exact implementation provenance, resolved once per process:

- `engine_source_hash` — sha256 over the source bytes of a fixed tuple of engine modules. **It identifies
  exact implementation source and is fail-closed provenance. A changed source hash does not by itself claim
  that the tape semantics changed** (a comment-only edit changes it).
- `source_revision` — the git commit hash the process started from, or null when unavailable.
- `worktree_dirty` — `true`, `false` or `null` under the declared dirty-state check (tracked files under
  `apps/backend/app`): `(abc123, false)` means the process started from commit `abc123` with the checked
  source clean; `(abc123, true)` means HEAD was `abc123` but the running implementation includes
  uncommitted changes — `engine_source_hash` is then the exact engine-source provenance; `(null, null)`
  means git/source identity was unavailable. Nothing is invented.

## 8. Partition, canonical encoding and the two hashes

**Partition** (leaf paths):

- **Machine observation semantics** → `observation_hash`: `schema_version`, `provider`, `ticker`,
  `tape_state`, `confidence`, `warm`, `primary_window`, `features`, `trade_event_count`, `market.bid`,
  `market.ask`, `market.spread`, `market.last`, `observed_at_utc`, `timing.logical_timestamp`,
  `timing.epoch_anchor`, `engine_identity.*`.
- **Provenance / source / lifecycle metadata**: `available_at_utc`, `availability_basis`,
  `generated_at_utc`, `timing.settled_at_utc`, `timing.delivery_lag_seconds`, `lifecycle.*`, `source.*`,
  `implementation_provenance.*`.
- **Explanatory metadata**: `observations[]` — human-readable prose for understanding, audit and
  debugging. A wording change never changes machine identity. Policies must not depend on it.
- **Integrity**: `observation_hash`, `artifact_hash`.

**Canonical encoding**: `json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")`, then
sha256 hex. Serialization order never changes either hash.

**`observation_hash`** = sha256(canonical encoding of the machine-observation semantic set). It is a
**machine-observation equivalence identity**. Two artifacts may share an `observation_hash` even if they
came from different watch sessions, different generation times, different source metadata or different
implementation source hashes, provided their declared semantic set is identical. It is not the unique
identifier of the exact evidence object another system consumed.

**`artifact_hash`** = sha256(canonical encoding of the whole artifact with `artifact_hash` removed). It
**identifies the exact `TapeObservation` evidence artifact instance**, including its provenance,
source/session/lifecycle metadata, explanatory text, implementation provenance and generation time under
the declared canonical encoding. It is intentionally different on every projection.

**Evidence-identity rule.** An external consumer that needs to record *which exact Tapeology evidence
object an evaluation used* references `artifact_hash`, not only `observation_hash`.

Recomputation recipe: parse the served JSON; drop `artifact_hash`; canonical-encode and hash → must equal
the served `artifact_hash`. Then select the semantic leaf paths listed above; canonical-encode and hash →
must equal the served `observation_hash`.

## 9. Lifecycle honesty

| `lifecycle.stream_status` | Meaning | Times | A consumer may conclude |
|---|---|---|---|
| `connecting` | engine constructed, stream not yet open | null | not yet observing |
| `waiting` | stream open, no event yet | null | healthy but waiting |
| `live` | at least one event processed, no gap flagged | per basis | healthy current observation |
| `stale` | live watchdog saw no event for the configured gap (live basis only; possible with zero events) | unchanged (or null with zero events) | stale observation |
| `paused` | operator pause | unchanged | paused |
| `closed` | natural end (`end_reason = stream_closed`) or cancel/switch (`end_reason` null) | unchanged | closed stream |
| `failed` | feeder exception (`end_reason` null in v1) | unchanged (or null with zero events) | failed feed |
| watch stopped | the watch was removed | REST answers 404 | not watched |

`stale` never occurs on the historical, dataset-replay or sim bases. The artifact never rewrites,
suppresses or nulls `tape_state` or `confidence` because of lifecycle status. The consumer receives both
`tape_state` and `lifecycle` and decides usability under its own policy.

## 10. Ingestion-path equivalence under an identical valid event stream

When the exact same valid ordered event stream is fed through different ingestion mechanisms (the replay
feeder and the live feeder) into the same frozen engine semantics and configuration/profile, the resulting
machine-observation semantic set — and therefore `observation_hash` — is identical. Only provenance, source
and lifecycle metadata may differ.

A valid ordered event stream has non-decreasing epochs; at equal epoch every quote precedes every trade;
relative order within a kind is preserved.

**This does not assert semantic equality between independently sourced IEX and SIP market data**, which
may contain different events. Feed bases are never pooled.

## 11. The consumer path

- `GET /tape/{ticker}/observation` — 200 with the artifact for a watched ticker; 404 for an unwatched
  ticker (like every other `/tape/*` route).
- The route's parsed JSON is field-for-field and value-for-value equal to the builder's output for the
  same atomic read and projection time. HTTP key order is not part of the contract; both hashes are
  recomputable from the served JSON with the recipe in §8.
- The read-only MCP `get_endpoint` tool proxies the route byte-identically.
- A GET never starts a watch, a computation, a git call or a recording.
- A consumer never scrapes UI text, combines endpoints, derives timestamps, recalculates freshness,
  recomputes confidence or tape state, or infers feed basis.

## 12. Provider ownership

Tapeology owns: tape state, confidence, features, the timing facts it can honestly know, feed/source/session
provenance, lifecycle, observation identity and artifact identity.

The external consumer owns: whether an observation satisfies its composite policy, whether the
observation's freshness is acceptable for that policy, whether its policy remains pending, and whether its
complete system returns READY, NO_TRADE or NO_VERDICT. Tapeology does not know those concepts and never
returns them or any equivalent.

## 13. Canonical core language

All identifiers, schema names, enum values, field names and persisted values in this contract are
English-only ASCII.

## 14. Versioning

`tape-observation-v1` is frozen. Any change to a field's meaning, an enum value, a null rule, the
partition or a hash law is a new `schema_version`, never a silent change. A later version may add a
stronger availability basis when actual receive timestamps are recorded.

---

*Implementation notes* (the implementing run may append below this line; nothing above changes).
