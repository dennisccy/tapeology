"""Era 6 "The Referee" (J-01) — the readiness fold: the FIRST concrete Referee artifact, and the
one every later Referee journey (J-02 through J-09, per ``docs/goal.md``'s stated dependency
order) depends on existing first.

**What this module is, and is not.** This is the SIMPLEST possible slice of the eventual evidence
contract (``docs/goal.md`` Key Capability 1): honest per-family READINESS counts, never individual
observations. It answers "how much evidence already exists" — playbook-family occurrence/session
counts pooled at the CURRENT detector basis, plus strategy-family dataset/split/trade counts and
the honest tick-corpus-gate statement. It does NOT build the typed ``{evidence_family,
observation_id, anchor_ts, ...}`` contract (J-02), touch statistics of any kind (J-03), or write
anything — pure aggregation over records ``desk_playbook.py``/``store.py``/``datasets.py`` already
own, read through their own public APIs only. Zero re-implementation of anything Playbook or
strategy already computes.

**The two pooling halves — ``detector_basis`` vs. ``playbook_input_signature``.** A playbook
record's own ``playbook_input_signature`` hashes BOTH its parameters AND the bar-series checksums
it read, so it churns on every daily bar top-up (``desk_playbook.py``'s own module docstring, and
Build-anchors trap T-6 in ``docs/goal.md``) — pooling on it directly would almost never span more
than one date. ``detector_basis`` (Key Capability 1: ``sha256(canonical(record.parameters))[:16]``)
hashes ONLY the parameters half, so it stays stable across daily top-ups and moves only on a
genuine detector-constant revision — the identity this fold pools on. The "current" basis is that
SAME formula applied to a FRESH call of ``playbook_parameters()`` (so a test monkeypatching a
``PLAYBOOK_*`` constant genuinely moves it); a record whose own embedded parameters hash to a
DIFFERENT value is honestly excluded from ``signals_at_current_basis``/``per_setup_side`` (it still
counts toward ``records``/``distinct_sessions`` — the store's raw, unfiltered content) rather than
silently pooled into today's counts. Pooling also requires the record's own ``config_fingerprint``
to match the caller's live one (Key Capability 1's full pooling key is
``(detector_basis, config_fingerprint)``) — a no-op today (the fingerprint pin does not move this
era) but the honest formula regardless.

**Newest-record-per-date (T-6).** A ``session_date`` can carry several recorded versions (a bar
top-up or a detector revision each mint a new ``playbook_input_signature`` at the SAME date,
without touching the older file — ``PlaybookStore`` is append-only). Only the NEWEST version per
date (by ``(recorded_at, id)``, ``PlaybookStore.list()``'s own sort order) is eligible to pool into
``signals_at_current_basis``/``per_setup_side`` — an older, superseded version at the same date is
never double-counted.

**Strategy-family counts.** ``dataset_count``/``per_split_counts`` are a plain read of
``DatasetStore.list()``'s own metadata (never a second dataset walk); ``trade_count`` sums
``len(result.trades)`` over every recorded backtest report on file (``JournalStore.list_backtests``
at an effectively-unlimited cap — the SERVING-only ``Config.backtest_list_max`` the
``/research/backtests`` route uses for display would silently undercount an aggregate). A report
with no ``result`` yet (queued/running/failed/cancelled) contributes zero trades, not an error.

**The tick gate and the Card-6.4 caveat.** ``docs/research-directions.md``'s Part-1 prerequisite
table names Era 6's tick-corpus gate as "library >= ~150 symbol-days"; the era-6 opening note
(2026-08-14) records Card 5.2's real corpus at "~12 partial 2.5-hour windows" — nowhere near it.
Each registered ``DatasetStore`` entry is one tick-corpus unit toward that gate (every
``DatasetStore`` record IS tick/quote event data by construction — bars live in a wholly separate
store). ``REFEREE_FORMING_BAR_BASIS_CAVEAT`` is this iteration's FIRST authoring of the Card-6.4
forming-bar disclosure sentence (``docs/goal.md``'s NOTES: no verbatim text exists anywhere yet) —
the single source of truth later journeys (J-06, J-08) must read back verbatim rather than minting
a second version.

**The pinned J-01 response shape, restated (iteration-1 documentation rider).** ``GET
/research/desk/referee/evidence``'s body is ``{"playbook_occurrence": {...}, "strategy_trade":
{...}}``. Each block additionally carries an ``integrity_errors`` key (each store's own
``.list()``-surfaced ``errors`` return, verbatim) — part of the pinned response shape from J-01
onward: ``playbook_occurrence.integrity_errors`` and ``strategy_trade.integrity_errors`` are both
served on every response, empty lists on a healthy corpus, and a corrupted/unparseable store file
is surfaced there rather than crashing the endpoint or being silently dropped.

**J-02 — the typed observation contract, two families, one shape.** ``docs/referee-statistical-
spec.md`` §2 pins ONE observation record implemented ONCE, below, via the shared ``_observation``
builder: ``{evidence_family, observation_id, symbol, session_date, anchor_ts, side, measure_key,
value, cluster_key, provenance{detector_basis, config_fingerprint, context_algorithm_version,
source_record_id, basis_caveats}}``. Units: directional ``value``s are the rail's own side-signed
percent returns (``desk_forward._measure_from``'s ``sign`` already applied inside every recorded
``forward`` block); MDD ``value``s are unsigned, direction-named, ``<= 0``-clamped, with the
side→MDD binding ``long -> mdd_long_*``, ``short -> mdd_short_*``. Stated once, here; no adapter
below restates or varies it.

- **Playbook adapter** (``playbook_observations``): reuses ``current_playbook_detector_basis()``
  and ``_newest_per_session_date()`` verbatim (J-01) for the ``(detector_basis,
  config_fingerprint)`` pooling/dedup identity, then walks each newest-per-date record's own
  already-measured signals through ``_resolve_leaf`` into one observation per applicable
  ``DESK_FORWARD_MEASURE_KEYS`` entry — a truncated or structurally-unmeasurable
  (``reason``-non-null) leaf is counted as an exclusion, never a fabricated or fallback value
  (``desk_forward._collect_measures``'s own established exclusion rule, applied per-leaf here
  instead of pooled). ``context_algorithm_version`` is always ``None`` this iteration (zero
  dependency on ``desk_playbook_context`` — the import-ban guard proves it structurally) and
  ``basis_caveats`` is always ``[]`` (the Card-6.4 caveat names strategy-family evidence only).
  A per-file, stat-keyed ``RefereeObservationCache`` (see its own docstring) makes a warm read
  skip every file's own parse+checksum verification; deleting it changes latency only.
- **Strategy adapter** (``strategy_observations``): reads each recorded backtest report's own
  ``result`` block, which ALREADY carries its trades joined to dataset/strategy identity verbatim
  (``backtests.py``'s own ``"dataset": dataset_meta`` at record time) — no second ``DatasetStore``
  lookup, no re-join. One ``measure_key == "net_r"`` observation per trade; ``cluster_key`` = the
  dataset id; ``anchor_ts`` = ISO-8601 UTC of ``dataset.epoch_anchor + trade.entry.logical_ts``;
  ``session_date`` = the ET calendar date of that same instant (spec §2 — distinct from
  ``desk_sessions._session_date``, which is UTC-calendar and serves a different purpose); the
  recorded ``random_null`` trades (``backtests.py::_null_trades``) are adapted as a SEPARATE,
  labeled ``null_observations`` list, never merged into the primary trades; ``basis_caveats``
  always carries ``REFEREE_FORMING_BAR_BASIS_CAVEAT`` verbatim (the iter-1 rider). ``detector_basis``
  is always ``None`` for this family — a strategy trade has no detector, so the field the playbook
  family uses for its own pooling identity is an honest absence here, the identical pattern
  ``context_algorithm_version`` already uses when no context predicate is involved. Not cached —
  see ``RefereeObservationCache``'s own docstring for why.

Neither adapter writes to any pre-existing store (playbook/dataset/journal); both are pure reads
through each store's own public API, exactly as J-01's readiness fold already established.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
from .desk_forward import DESK_FORWARD_HORIZONS_MINUTES, DESK_FORWARD_MEASURE_KEYS
from .desk_playbook import PlaybookStore, playbook_parameters, resolve_desk_playbook_dir
from .store import JournalStore

__all__ = [
    "REFEREE_FORMING_BAR_BASIS_CAVEAT",
    "REFEREE_TICK_GATE_SYMBOL_DAYS",
    "REFEREE_SESSION_COMPLETE_ET",
    "current_playbook_detector_basis",
    "playbook_occurrence_readiness",
    "strategy_trade_readiness",
    "referee_evidence",
    # J-02: the typed evidence contract
    "RefereeObservationCache",
    "resolve_referee_obs_cache_db_path",
    "playbook_observations",
    "strategy_observations",
]

# The Era-6 tick-corpus readiness gate (docs/research-directions.md's Part-1 prerequisite table:
# "library >= ~150 symbol-days"; the era-6 opening note's Card-5.2 figure). A named module
# constant, never an inline magic number -- a READINESS floor reported honestly, never a detector
# gate and never a value any code path here iterates against outcomes.
REFEREE_TICK_GATE_SYMBOL_DAYS: int = 150

# The Card-6.4 forming-bar disclosure -- authored ONCE, here, for the first time this era
# (docs/goal.md's NOTES: no pinned verbatim text exists anywhere else). J-06/J-08 read this EXACT
# string back rather than minting a second version (single source of truth). Subject to
# tests/test_copy_discipline.py's lexicon (verified directly in this module's own test file, the
# PLAYBOOK_REGISTER/EVIDENCE_REGISTER precedent).
REFEREE_FORMING_BAR_BASIS_CAVEAT: str = (
    "strategy-family evidence is measured over bars read through levels._bars_as_of, which for "
    "intraday timeframes keeps a bar whenever epoch <= as_of -- admitting the still-forming bar, "
    "whose stored high/low/close can embed up to a full bar-length of information from after the "
    "as-of instant. The completed-bar fix (epoch + timeframe_seconds <= as_of) is deferred out of "
    "this era by operator decision (docs/research-directions.md Card 6.4 Part 1); until it lands, "
    "this caveat is carried on every strategy-family evidence record so no reader mistakes today's "
    "basis for a fully lookahead-clean one."
)

# An effectively-unlimited `list_backtests` cap for THIS aggregate fold -- distinct from the
# serving-only `Config.backtest_list_max` (100) the `/research/backtests` route uses for display.
# A readiness count must read every recorded report on file, never a display-sized sample.
_ALL_BACKTESTS_SCAN_LIMIT = 1_000_000

# spec Sec1's pre-registered completed-session constant: a record is confirmatory-eligible for a
# symbol only if that symbol's finest measurement series reaches this ET wall-clock time on the
# session date (partial mid-day records are exploratory-only). Era-wide, minted here since J-02 is
# the first consumer; a plain module constant, never a Config field.
REFEREE_SESSION_COMPLETE_ET: str = "15:55"

# The Referee's own ET zone constant -- the `desk_playbook_features.py` per-module idiom (each
# module that needs ET wall-clock resolution owns a private ZoneInfo constant rather than reaching
# into another module's private one; RTH/ET conversion is a one-line stdlib call, not logic worth
# a cross-module import for).
_ET_ZONE = ZoneInfo("America/New_York")

# The four rail horizon labels, in DESK_FORWARD_HORIZONS_MINUTES' own declared order -- derived,
# never spelled out a second time, so a rail horizon addition can never silently desync here.
_HORIZON_LABELS: tuple[str, ...] = tuple(label for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES)

# The observation cache's env override name and busy-timeout -- the `TAPEOLOGY_..._CACHE_DB`
# family (`bar_verify_cache`/`playbook_evidence_cache_db_path`) precedent verbatim.
_REFEREE_OBS_CACHE_DB_ENV = "TAPEOLOGY_REFEREE_OBS_CACHE_DB"
_REFEREE_OBS_CACHE_BUSY_TIMEOUT_MS = 5000
_REFEREE_PLAYBOOK_OBS_TABLE = "referee_playbook_observation_cache"

# The playbook per-file observation-projection cache schema version -- bumped whenever a cached
# projection's own shape gains fields a fold needs (the `desk_playbook_evidence._PROJECTION_
# VERSION` precedent). A row cached at an older version is an honest miss, never a partial hit.
_PLAYBOOK_OBS_PROJECTION_VERSION = 1


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding this module hashes -- the SAME encoding every other desk
    store hashes (``desk_playbook.py._canonical`` et al)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def current_playbook_detector_basis() -> str:
    """The pooling key's parameters-only half (docs/goal.md Key Capability 1):
    ``sha256(canonical(playbook_parameters()))[:16]``, read fresh at CALL TIME so a test
    monkeypatching a ``PLAYBOOK_*`` constant genuinely moves this value. Stable across daily bar
    top-ups (unlike ``playbook_input_signature``, which also hashes bar-series checksums) -- it
    moves only on a genuine detector-constant revision."""
    return _sha256(_canonical(playbook_parameters()))[:16]


def _record_detector_basis(record: dict) -> str:
    """The SAME formula applied to one already-recorded record's own embedded ``parameters`` --
    that record's own basis, whether or not it matches the CURRENT one."""
    return _sha256(_canonical(record["parameters"]))[:16]


def _newest_per_session_date(records: list[dict]) -> dict[str, dict]:
    """One record per ``session_date`` -- the newest by ``(recorded_at, id)`` (T-6's pooling
    rule). ``records`` arrives ``(recorded_at, id)``-ascending (``PlaybookStore.list()``'s own
    sort), so simply overwriting a dict entry as each record is walked leaves the LAST-seen (=
    newest) record for every date -- no re-sort needed."""
    newest: dict[str, dict] = {}
    for record in records:
        newest[record["session_date"]] = record
    return newest


def playbook_occurrence_readiness(store: PlaybookStore, config_fingerprint: str) -> dict:
    """The ``playbook_occurrence`` block: ``records``/``distinct_sessions`` are the store's raw,
    UNFILTERED content (every file on disk, every date it spans); ``signals_at_current_basis`` and
    ``per_setup_side`` pool only the newest-per-date records whose own ``(detector_basis,
    config_fingerprint)`` match today's live values (T-6) -- a stale-basis record still counts
    toward the first two, never the last two. ``per_setup_side`` is SPARSE (only cells with at
    least one recorded signal), so a zero-corpus store serves ``[]``, never a padded zero-filled
    cross product."""
    records, errors = store.list()
    basis = current_playbook_detector_basis()
    newest_by_date = _newest_per_session_date(records)

    cells: dict[tuple[str, str], dict[str, object]] = {}
    signals_at_current_basis = 0
    for record in newest_by_date.values():
        if (
            _record_detector_basis(record) != basis
            or record["config_fingerprint"] != config_fingerprint
        ):
            continue
        session_date = record["session_date"]
        for signal in record["signals"]:
            signals_at_current_basis += 1
            key = (signal["setup_id"], signal["side"])
            cell = cells.setdefault(key, {"n": 0, "sessions": set()})
            cell["n"] += 1
            cell["sessions"].add(session_date)

    per_setup_side = [
        {"setup": setup, "side": side, "n": cell["n"], "n_sessions": len(cell["sessions"])}
        for (setup, side), cell in sorted(cells.items())
    ]

    return {
        "detector_basis": basis,
        "config_fingerprint": config_fingerprint,
        "records": len(records),
        "distinct_sessions": len(newest_by_date),
        "signals_at_current_basis": signals_at_current_basis,
        "per_setup_side": per_setup_side,
        "integrity_errors": errors,
    }


def _tick_gate_state(measured_symbol_days: int) -> tuple[bool, str]:
    """Whether the Era-6 tick-corpus gate is met, plus the honest sentence naming the gate and the
    measured shortfall (or surplus) -- pure arithmetic over an already-counted value, never a
    second count and never a threshold this (or any) code path iterates against outcomes."""
    met = measured_symbol_days >= REFEREE_TICK_GATE_SYMBOL_DAYS
    gate_clause = (
        f"the Era-6 tick-corpus gate (>= {REFEREE_TICK_GATE_SYMBOL_DAYS} symbol-days, "
        f"docs/research-directions.md Card 5.2) "
    )
    if met:
        return True, gate_clause + (
            f"is met: {measured_symbol_days} tick dataset(s) are registered today."
        )
    shortfall = REFEREE_TICK_GATE_SYMBOL_DAYS - measured_symbol_days
    return False, gate_clause + (
        f"is unmet: {measured_symbol_days} tick dataset(s) are registered today, {shortfall} "
        f"short of the gate."
    )


def strategy_trade_readiness(dataset_store: DatasetStore, journal_store: JournalStore) -> dict:
    """The ``strategy_trade`` block: dataset/split/trade counts read straight off
    ``DatasetStore``/``JournalStore``'s own public reads (zero recomputation of anything
    ``backtests.py`` already owns), plus the honest tick-gate statement and the Card-6.4 basis
    caveat."""
    datasets, dataset_errors = dataset_store.list()
    per_split_counts = {SPLIT_TRAIN: 0, SPLIT_HOLDOUT: 0}
    for meta in datasets:
        split = meta.get("split")
        if split in per_split_counts:
            per_split_counts[split] += 1

    backtests = journal_store.list_backtests(limit=_ALL_BACKTESTS_SCAN_LIMIT)
    trade_count = sum(
        len(record.payload.get("result", {}).get("trades", [])) for record in backtests
    )

    tick_gate_met, tick_gate_statement = _tick_gate_state(len(datasets))

    return {
        "dataset_count": len(datasets),
        "per_split_counts": per_split_counts,
        "trade_count": trade_count,
        "tick_gate_met": tick_gate_met,
        "tick_gate_statement": tick_gate_statement,
        "basis_caveats": [REFEREE_FORMING_BAR_BASIS_CAVEAT],
        "integrity_errors": dataset_errors,
    }


def referee_evidence(
    *,
    playbook_store: PlaybookStore,
    dataset_store: DatasetStore,
    journal_store: JournalStore,
    config_fingerprint: str,
) -> dict:
    """The whole ``GET /research/desk/referee/evidence`` body (J-01) -- per-family readiness, a
    pure aggregation over already-recorded ``PlaybookStore``/``DatasetStore``/``JournalStore``
    records. Never 404/500 on an empty corpus (an honest all-zero shape at HTTP 200 — the desk
    router's established never-404-on-absence convention)."""
    return {
        "playbook_occurrence": playbook_occurrence_readiness(playbook_store, config_fingerprint),
        "strategy_trade": strategy_trade_readiness(dataset_store, journal_store),
    }


# === J-02: the typed evidence contract — two families, one observation shape ========================
#
# Nothing below this line is wired into `referee_evidence()`/`GET /research/desk/referee/evidence`
# — J-01's already-served response shape stays byte-identical (OUT OF SCOPE). This section adds a
# standalone contract later journeys (J-04/J-05/J-06) import directly; J-02 itself serves no route
# (goal.md's own `(Keyless; automated.)` tag — its acceptance is the hermetic fixture suite).


def _iso(epoch: float) -> str:
    """The per-module tiny-helper convention (``desk_forward.py._iso`` / ``desk_screen.py._iso``):
    epoch -> ISO, so every served timestamp is formatted identically wherever it is read."""
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _epoch_from_iso(iso: str) -> float:
    """The inverse of ``_iso`` -- ``desk_forward._epoch``'s own idiom, copied fresh."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _et_session_date(epoch: float) -> str:
    """The ET calendar date ``epoch`` falls on, ``yyyy-MM-dd`` -- DST-correct by construction
    (``zoneinfo`` resolves the UTC offset from the instant given, never a fixed offset). Spec
    §2: a strategy observation's ``session_date`` is the ET date of its own entry instant --
    distinct from ``desk_sessions._session_date``, which is UTC-calendar-date and serves session
    detection, a different concept for a different purpose."""
    return datetime.fromtimestamp(epoch, tz=_ET_ZONE).date().isoformat()


def _session_complete_epoch(session_date: str) -> float:
    """The UTC epoch ``REFEREE_SESSION_COMPLETE_ET`` (ET wall-clock) resolves to on
    ``session_date`` -- ``desk_playbook_features._et_epoch``'s own idiom, copied fresh (a
    one-line zoneinfo combine is not worth a cross-module import for)."""
    hour, minute = (int(part) for part in REFEREE_SESSION_COMPLETE_ET.split(":"))
    day = date.fromisoformat(session_date)
    return datetime.combine(day, time(hour, minute), tzinfo=_ET_ZONE).timestamp()


def _observation(
    *,
    evidence_family: str,
    observation_id: str,
    symbol: str | None,
    session_date: str,
    anchor_ts: str,
    side: str,
    measure_key: str,
    value: float,
    cluster_key: str | None,
    detector_basis: str | None,
    config_fingerprint: str | None,
    context_algorithm_version: str | None,
    source_record_id: str,
    basis_caveats: list[str],
) -> dict:
    """ONE typed observation record -- ``docs/referee-statistical-spec.md`` §2's shape,
    implemented ONCE, here, for both families (``docs/goal.md`` Key Capability 1). See the module
    docstring's own J-02 section for the units/side->MDD binding stated once."""
    return {
        "evidence_family": evidence_family,
        "observation_id": observation_id,
        "symbol": symbol,
        "session_date": session_date,
        "anchor_ts": anchor_ts,
        "side": side,
        "measure_key": measure_key,
        "value": value,
        "cluster_key": cluster_key,
        "provenance": {
            "detector_basis": detector_basis,
            "config_fingerprint": config_fingerprint,
            "context_algorithm_version": context_algorithm_version,
            "source_record_id": source_record_id,
            "basis_caveats": list(basis_caveats),
        },
    }


# --- the playbook adapter ----------------------------------------------------------------------------


def _resolve_leaf(measure_key: str, forward: dict) -> tuple[float | None, bool]:
    """``(value, excluded)`` for ONE of ``DESK_FORWARD_MEASURE_KEYS``' 15 keys, read off one
    already-measured signal's own ``forward`` block (never re-measured). The four horizon labels
    and their own ``mdd_long_*``/``mdd_short_*`` siblings share that horizon's own
    ``reason``/``truncated`` flags -- ``desk_forward._measure_from`` measures a horizon's return
    AND both its drawdowns over the IDENTICAL window, so all three are excluded together. The
    session-end trio (``to_close``, ``mdd_long``, ``mdd_short``) is measured through session close
    and is never excluded -- ``desk_forward._collect_measures``'s own "the session-end trio pools
    every event" rule, applied per-leaf here instead of pooled. ``excluded`` means "no fallback
    value, ever" (spec §2) -- the caller counts the exclusion and emits no observation for it."""
    if measure_key == "to_close":
        return forward["to_close_pct"], False
    if measure_key == "mdd_long":
        return forward["mdd_long_pct"], False
    if measure_key == "mdd_short":
        return forward["mdd_short_pct"], False
    if measure_key in _HORIZON_LABELS:
        horizon = forward["horizons"][measure_key]
        excluded = horizon["reason"] is not None or horizon["truncated"]
        return (None if excluded else horizon["return_pct"]), excluded
    for prefix, field in (("mdd_long_", "mdd_long_pct"), ("mdd_short_", "mdd_short_pct")):
        if measure_key.startswith(prefix) and measure_key[len(prefix) :] in _HORIZON_LABELS:
            horizon = forward["horizons"][measure_key[len(prefix) :]]
            excluded = horizon["reason"] is not None or horizon["truncated"]
            return (None if excluded else horizon[field]), excluded
    raise ValueError(f"unknown DESK_FORWARD_MEASURE_KEYS entry {measure_key!r}")


def _signal_reaches_session_complete(signal: dict, session_date: str) -> bool:
    """Best-effort per-signal completeness check (spec §2's completed-session rule): whether this
    signal's own finest measurement series reaches ``REFEREE_SESSION_COMPLETE_ET`` on
    ``session_date``, estimated from the signal's own already-recorded ``forward`` block
    (``at_utc`` + ``minutes_to_close``, in bar-count-equivalent minutes -- ``_measure_from``'s own
    documented unit for that field). **Known limitation, disclosed rather than hidden:** this
    reading is blind to any intra-session bar gap between the signal's own anchor and the
    session's actual last recorded bar (bar-count-equivalent minutes under-count true elapsed
    wall-clock time whenever the finest series has a gap), so it is carried as a DISCLOSURE this
    iteration, never a gate -- J-02 emits every applicable observation regardless of this flag;
    only a later journey's confirmatory-eligibility fold (J-06) may ever filter on it."""
    forward = signal.get("forward")
    if forward is None:
        return False
    anchor_epoch = _epoch_from_iso(forward["at_utc"])
    last_bar_epoch = anchor_epoch + forward["minutes_to_close"] * 60.0
    return last_bar_epoch >= _session_complete_epoch(session_date)


def _playbook_file_projection(record: dict) -> dict:
    """Extract ONE already-verified playbook record's own candidate observations -- independent
    of pooling (newest-per-date / current-basis selection happens in the caller, across every
    file's own projection -- the ``desk_playbook_evidence._file_projection`` split). Nothing here
    re-measures anything: every ``value`` is read off the record's own already-recorded
    ``signal["forward"]`` block via ``_resolve_leaf``. A signal recorded before the (era-B2)
    forward-measurement pass existed carries no ``forward`` block at all -- excluded from this
    projection entirely (the same "predates measurement" absence ``PlaybookStore._registered``
    itself reads back verbatim), never fabricated, never a crash."""
    basis = _record_detector_basis(record)
    observations: list[dict] = []
    excluded_leaves = 0
    symbols_with_signals: set[str] = set()
    complete_by_symbol: dict[str, bool] = {}
    for index, signal in enumerate(record["signals"]):
        forward = signal.get("forward")
        if forward is None:
            continue
        symbol = signal["symbol"]
        symbols_with_signals.add(symbol)
        if _signal_reaches_session_complete(signal, record["session_date"]):
            complete_by_symbol[symbol] = True
        else:
            complete_by_symbol.setdefault(symbol, False)
        for measure_key in DESK_FORWARD_MEASURE_KEYS:
            value, excluded = _resolve_leaf(measure_key, forward)
            if excluded:
                excluded_leaves += 1
                continue
            observations.append(
                _observation(
                    evidence_family="playbook_occurrence",
                    observation_id=f"playbook:{record['id']}:{index}:{measure_key}",
                    symbol=symbol,
                    session_date=record["session_date"],
                    anchor_ts=signal["trigger_ts"],
                    side=signal["side"],
                    measure_key=measure_key,
                    value=value,
                    cluster_key=record["session_date"],
                    detector_basis=basis,
                    config_fingerprint=record["config_fingerprint"],
                    context_algorithm_version=None,
                    source_record_id=record["id"],
                    basis_caveats=[],
                )
            )
    return {
        "projection_version": _PLAYBOOK_OBS_PROJECTION_VERSION,
        "id": record["id"],
        "session_date": record["session_date"],
        "recorded_at": record["recorded_at"],
        "record_detector_basis": basis,
        "config_fingerprint": record["config_fingerprint"],
        "symbol_coverage": len(symbols_with_signals),
        "symbol_completeness": complete_by_symbol,
        "excluded_leaves": excluded_leaves,
        "observations": observations,
    }


class RefereeObservationCache:
    """The durable, stat-keyed per-file cache behind the playbook adapter's observation
    projections -- ``desk_playbook_evidence.PlaybookEvidenceCache``'s contract, copied fresh (the
    identical "a fresh small class, not a shared import, because the cached SHAPE differs"
    reasoning that module gives for not reusing ``desk_meta_cache.DeskMetaCache`` either). Owns
    nothing: a row only ever remembers one already-verified playbook file's own already-built
    candidate observations, keyed by that file's exact ``(path, size, mtime_ns)``. No
    update/delete method exists anywhere on this class (structural): ``insert`` is
    ``INSERT OR REPLACE``, idempotent under the identical key a legitimately re-verified file
    would produce. Deleting the DB file changes only how many files must be re-read through
    ``PlaybookStore.get`` to reproduce the IDENTICAL result -- never the served content (TC-2).

    **The strategy family is deliberately NOT cached through this class, or any other.** Unlike
    ``PlaybookStore``'s per-file JSON store (no metadata-only listing exists, so every
    ``store.list()`` call re-parses and re-verifies every file on disk -- the exact cost
    ``desk_meta_cache.py``'s own docstring motivates this whole class family against),
    ``JournalStore`` is a single indexed SQLite table and ``DatasetStore`` already carries its own
    optional index accelerator (``index_db_path``) -- neither exposes a metadata-only projection
    cheaper than the read itself, so a cache here could only ever cost as much as what it claims
    to save. ``strategy_observations`` reads fresh every call, exactly as J-01's own
    ``strategy_trade_readiness`` already does, uncached, today."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # One connection, several threads (FastAPI's sync-route threadpool) -- the
        # `desk_meta_cache.py`/`desk_playbook_evidence.py` serialization, for the identical reason.
        self._lock = threading.Lock()
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(f"PRAGMA busy_timeout={_REFEREE_OBS_CACHE_BUSY_TIMEOUT_MS}")
        with self._lock, self._conn:
            self._conn.execute(
                f"CREATE TABLE IF NOT EXISTS {_REFEREE_PLAYBOOK_OBS_TABLE} ("
                "    path            TEXT PRIMARY KEY,"
                "    size            INTEGER NOT NULL,"
                "    mtime_ns        INTEGER NOT NULL,"
                "    projection_json TEXT NOT NULL)"
            )

    @property
    def db_path(self) -> str:
        return self._db_path

    def lookup(self, path: str, size: int, mtime_ns: int) -> dict | None:
        """An exact ``(path, size, mtime_ns)`` match -- ANY stat difference (a genuine content
        change, a moved file, or simply no row yet) is an honest miss, never a stale hit."""
        with self._lock:
            row = self._conn.execute(
                f"SELECT size, mtime_ns, projection_json FROM {_REFEREE_PLAYBOOK_OBS_TABLE} "
                "WHERE path=?",
                (path,),
            ).fetchone()
        if row is None or row["size"] != size or row["mtime_ns"] != mtime_ns:
            return None
        return json.loads(row["projection_json"])

    def insert(self, path: str, size: int, mtime_ns: int, projection: dict) -> None:
        """Additively remember ONE already-extracted file projection. ``json.dumps`` WITHOUT
        ``sort_keys`` -- a cache hit must reproduce the EXACT key order a fresh extraction would
        (the ``desk_meta_cache.py`` byte-identity precedent), so a served result never differs
        between a cold and a warm read (TC-2)."""
        with self._lock, self._conn:
            self._conn.execute(
                f"INSERT OR REPLACE INTO {_REFEREE_PLAYBOOK_OBS_TABLE} "
                "(path, size, mtime_ns, projection_json) VALUES (?,?,?,?)",
                (path, size, mtime_ns, json.dumps(projection)),
            )


def resolve_referee_obs_cache_db_path(desk_universe_dir_resolved: str) -> str:
    """The resolved durable observation-cache path: the ``TAPEOLOGY_REFEREE_OBS_CACHE_DB`` env
    var if set, else a file co-located as a SIBLING of the playbook directory
    (``playbook_evidence_cache_db_path``'s resolver verbatim, one level up since this module has
    no dependency on ``desk_routes.py``). A derived path, never a ``Config`` field, so
    ``config_fingerprint`` stays frozen."""
    override = os.environ.get(_REFEREE_OBS_CACHE_DB_ENV)
    if override:
        return override
    playbook_dir = resolve_desk_playbook_dir(desk_universe_dir_resolved)
    return os.path.join(os.path.dirname(playbook_dir), "referee_obs_cache.db")


def _playbook_observation_projections(
    store: PlaybookStore, cache: RefereeObservationCache | None
) -> list[dict]:
    """Every recorded playbook file's own observation projection, oldest-path-first -- a cache
    hit skips that file's own parse+checksum verification entirely; a cache miss reads it through
    ``PlaybookStore.get`` (the store's own public, verified reader -- zero re-implementation of
    its checksum/corruption handling) and remembers the freshly extracted projection for next
    time. A file that fails verification (``PlaybookStore.get`` returns ``None``) is silently
    excluded from this fold (``PlaybookStore.list()``'s own ``integrity_errors`` already surfaces
    a corrupted file explicitly elsewhere; this fold does not duplicate that disclosure, it simply
    never crashes and never fabricates a projection for a file it could not verify) -- the
    ``desk_playbook_evidence._projections_by_signature`` pattern verbatim."""
    if not store.root.exists():
        return []
    projections: list[dict] = []
    for path in sorted(store.root.glob("*.json")):
        try:
            stat = path.stat()
        except OSError:
            continue
        key = str(path)
        cached = cache.lookup(key, stat.st_size, stat.st_mtime_ns) if cache is not None else None
        if cached is not None and cached.get("projection_version") == _PLAYBOOK_OBS_PROJECTION_VERSION:
            projections.append(cached)
            continue
        record = store.get(path.stem)
        if record is None:
            continue
        projection = _playbook_file_projection(record)
        if cache is not None:
            cache.insert(key, stat.st_size, stat.st_mtime_ns, projection)
        projections.append(projection)
    return projections


def playbook_observations(
    store: PlaybookStore,
    config_fingerprint: str,
    *,
    cache: RefereeObservationCache | None = None,
) -> dict:
    """The playbook-family adapter (J-02, spec §2): every newest-per-``session_date`` record
    whose own ``(detector_basis, config_fingerprint)`` matches today's LIVE values (T-6 —
    ``current_playbook_detector_basis()``/``_newest_per_session_date()`` reused verbatim from
    J-01, never reimplemented) contributes its own already-built candidate observations; a
    stale-basis or superseded record contributes none. Returns::

        {
          "observations": [...],                 # spec §2 shape, both families' union type
          "excluded_leaves": int,                 # truncated/unmeasurable leaves, counted not valued
          "coverage_by_date": [{"session_date", "symbol_count"}, ...],
          "coverage_shrink_disclosures": [
              {"session_date", "newest_record_id", "newest_symbol_count",
               "superseded_record_id", "superseded_symbol_count"}, ...
          ],                                       # T-6: a newest record covering FEWER symbols
                                                     # than the one it superseded, named honestly
          "session_completeness": [{"session_date", "symbol", "complete"}, ...],
          "detector_basis": str,                  # the LIVE basis this call pooled against
          "config_fingerprint": str,
        }
    """
    live_basis = current_playbook_detector_basis()
    projections = _playbook_observation_projections(store, cache)
    # `PlaybookStore.list()`'s own sort order — `_newest_per_session_date` relies on it (its own
    # docstring: "records arrives (recorded_at, id)-ascending ... so simply overwriting a dict
    # entry ... leaves the LAST-seen (= newest) record"). The cache may return files in glob order,
    # so this call re-establishes it explicitly rather than trusting glob's own ordering.
    projections.sort(key=lambda p: (p["recorded_at"], p["id"]))
    newest_by_date = _newest_per_session_date(projections)  # REUSED verbatim (J-01, T-6)

    by_date: dict[str, list[dict]] = {}
    for projection in projections:
        by_date.setdefault(projection["session_date"], []).append(projection)

    observations: list[dict] = []
    excluded_leaves = 0
    coverage_by_date: list[dict] = []
    coverage_shrink_disclosures: list[dict] = []
    session_completeness: list[dict] = []

    for session_date in sorted(newest_by_date):
        newest = newest_by_date[session_date]
        if (
            newest["record_detector_basis"] != live_basis
            or newest["config_fingerprint"] != config_fingerprint
        ):
            continue
        observations.extend(newest["observations"])
        excluded_leaves += newest["excluded_leaves"]
        coverage_by_date.append(
            {"session_date": session_date, "symbol_count": newest["symbol_coverage"]}
        )
        for symbol, complete in newest["symbol_completeness"].items():
            session_completeness.append(
                {"session_date": session_date, "symbol": symbol, "complete": complete}
            )
        versions = by_date[session_date]
        if len(versions) >= 2:
            superseded = versions[-2]  # the record this date's newest one directly replaced
            if newest["symbol_coverage"] < superseded["symbol_coverage"]:
                coverage_shrink_disclosures.append(
                    {
                        "session_date": session_date,
                        "newest_record_id": newest["id"],
                        "newest_symbol_count": newest["symbol_coverage"],
                        "superseded_record_id": superseded["id"],
                        "superseded_symbol_count": superseded["symbol_coverage"],
                    }
                )

    return {
        "observations": observations,
        "excluded_leaves": excluded_leaves,
        "coverage_by_date": coverage_by_date,
        "coverage_shrink_disclosures": coverage_shrink_disclosures,
        "session_completeness": session_completeness,
        "detector_basis": live_basis,
        "config_fingerprint": config_fingerprint,
    }


# --- the strategy adapter ----------------------------------------------------------------------------


def _strategy_observation(
    *,
    backtest_id: str,
    index: int,
    kind: str,
    trade: dict,
    dataset: dict,
    config_fingerprint: str | None,
) -> dict:
    entry = trade["entry"]
    epoch_anchor = dataset.get("epoch_anchor") or 0.0
    anchor_epoch = epoch_anchor + entry["logical_ts"]
    return _observation(
        evidence_family="strategy_trade",
        observation_id=f"strategy:{backtest_id}:{kind}:{index}",
        symbol=dataset.get("symbol"),
        session_date=_et_session_date(anchor_epoch),
        anchor_ts=_iso(anchor_epoch),
        side=trade["direction"],
        measure_key="net_r",
        value=trade["net_r"],
        cluster_key=dataset.get("id"),
        detector_basis=None,
        config_fingerprint=config_fingerprint,
        context_algorithm_version=None,
        source_record_id=backtest_id,
        basis_caveats=[REFEREE_FORMING_BAR_BASIS_CAVEAT],
    )


def strategy_observations(journal_store: JournalStore) -> dict:
    """The strategy-family adapter (J-02, spec §2): every recorded backtest report's own
    ``result`` block already carries its trades joined to dataset/strategy identity VERBATIM
    (``backtests.py``'s own result-block construction, ``"dataset": dataset_meta`` stored at
    record time) -- so this reads ONLY ``JournalStore.list_backtests``, never a second
    ``DatasetStore`` lookup (the join already happened once; re-joining would be a second
    implementation of something ``backtests.py`` already owns). Not cached -- see
    ``RefereeObservationCache``'s own docstring for why. A report missing its ``dataset`` block
    entirely (never produced by the shipped runner, read defensively anyway) contributes zero
    observations rather than emitting one with a fabricated identity. Returns
    ``{"observations": [...], "null_observations": [...]}`` -- the recorded ``random_null`` trades
    kept as a SEPARATE, labeled set, never merged into the primary trades (TC-8)."""
    backtests = journal_store.list_backtests(limit=_ALL_BACKTESTS_SCAN_LIMIT)
    observations: list[dict] = []
    null_observations: list[dict] = []
    for record in backtests:
        result = record.payload.get("result") or {}
        if not result:
            continue
        dataset = result.get("dataset") or {}
        if not dataset:
            continue
        config_fingerprint = result.get("config_fingerprint")
        for index, trade in enumerate(result.get("trades", [])):
            observations.append(
                _strategy_observation(
                    backtest_id=record.id,
                    index=index,
                    kind="trade",
                    trade=trade,
                    dataset=dataset,
                    config_fingerprint=config_fingerprint,
                )
            )
        null_trades = (result.get("null_baseline") or {}).get("trades", [])
        for index, trade in enumerate(null_trades):
            null_observations.append(
                _strategy_observation(
                    backtest_id=record.id,
                    index=index,
                    kind="null",
                    trade=trade,
                    dataset=dataset,
                    config_fingerprint=config_fingerprint,
                )
            )
    return {"observations": observations, "null_observations": null_observations}
