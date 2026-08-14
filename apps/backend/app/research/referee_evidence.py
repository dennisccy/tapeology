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
"""

from __future__ import annotations

import hashlib
import json

from .datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
from .desk_playbook import PlaybookStore, playbook_parameters
from .store import JournalStore

__all__ = [
    "REFEREE_FORMING_BAR_BASIS_CAVEAT",
    "REFEREE_TICK_GATE_SYMBOL_DAYS",
    "current_playbook_detector_basis",
    "playbook_occurrence_readiness",
    "strategy_trade_readiness",
    "referee_evidence",
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
