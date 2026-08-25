"""``micro_readiness.py`` -- Era "The Rapid Microscope" J-01: the corpus-truth surface.

THIS MODULE is the era's first served value (``docs/goal.md`` Key Capability 1, Data Contract
row "Corpus readiness truth"): an honest, served-from-disk statement of what tick evidence
actually exists today, and which of the three predeclared pilot-study floors it clears (none,
honestly). It never fabricates, never re-derives a value another store already owns, and never
computes at GET time beyond the one per-shard cost documented below.

**J-03 addition:** the SAME "Corpus readiness truth" Data Contract row (no new endpoint) now also
carries ``joinable_corpus`` -- how many recorded playbook signals fall inside a recorded tick
dataset's own window, with a ``by_setup_id`` breakdown, computed by ``micro_join.
joinable_corpus_counts`` (never a second, independently-valued copy of that count here). Read the
full rationale, including why ``band_touch_count`` is honestly zero this iteration, in
``micro_join.py``'s own module docstring.

**Reads verbatim, never re-derives.** Every shard's ``checksum``/``trade_count``/``quote_count``/
``data_feed``/``window_start_utc``/``window_end_utc`` is read straight off
``DatasetStore.list()``'s own already-checksum-verified metadata -- this module performs no
second parse of a dataset file's content and no second checksum. ``referee_tick_gate_symbol_days``
is imported verbatim from ``referee_evidence.REFEREE_TICK_GATE_SYMBOL_DAYS`` (150) -- never a
second hardcoded copy of the same gate (single-source-of-truth rail).

**Two genuinely NEW per-shard computations, both cheap except one:**

  * ``session_date``/``coverage_gaps``/``bytes`` -- cheap arithmetic over already-known window
    bounds (an ET conversion, an interval overlap against the fixed 09:30-16:00 RTH window, a
    ``stat()`` call) -- no event replay needed. Session dates are ET calendar dates
    (``docs/rapid-validation-spec.md`` §0: "A session is an ET RTH trading date"); this module
    owns a private ``ZoneInfo`` constant for that conversion, the SAME per-module idiom
    ``referee_evidence.py`` documents ("each module that needs ET wall-clock resolution owns a
    private ZoneInfo constant rather than reaching [into another module's private one]") --
    ``desk_sessions.py`` is the arbiter of WHICH dates are known trading sessions (spec §0), but
    its own ``_session_date`` is UTC-calendar and serves a different purpose (the exact
    distinction ``referee_evidence.py`` itself draws), so it offers no ET conversion to reuse.

  * ``fallback_frac`` -- THE one genuinely expensive per-shard computation: which fraction of a
    shard's trades were classified via the Lee-Ready tick-test FALLBACK (``aggressor.py``'s Stage
    2) rather than decided outright by the quote rule (Stage 1). ``classify_aggressor`` itself
    does not expose which stage fired, and Stage 2's resolved side depends on state
    (``prior_trade_price``/``last_tick_dir``) this metric does not need -- only WHETHER Stage 1
    decided does, and that depends on nothing but the trade's price and the quote in effect
    (``aggressor.py``'s own docstring, verbatim: "Stage 2 ... fires ONLY when stage 1 yields no
    decision: no quote in effect, OR the print is strictly between bid and ask"). ``_quote_rule_
    decides`` below mirrors exactly that documented precondition -- not a reimplementation of
    hidden branching, but the one public boolean ``classify_aggressor`` does not itself return --
    and ``tests/test_micro_readiness.py`` cross-validates it against ``classify_aggressor``'s own
    observable behavior (never merely against a second copy of the same formula). Cached keyed on
    the dataset's content ``checksum`` (``MicroReadinessCache``, below) -- the ``dataset_index.py``
    derived/rebuildable precedent: losing the cache loses nothing, the next GET rebuilds it -- so
    a repeat request never re-replays ~0.92 GB of tick events (T-8, "page-load GETs never
    compute").

**Corrupted files are surfaced, never dropped, never a crash.** ``DatasetStore.list()``'s own
``errors`` half is served verbatim as ``integrity_errors``; every OTHER, healthy shard still
appears in ``shards`` with every field populated, unaffected by the corrupted one.

**The three pilot-study floors read one shared, frozen geometry constant.** No study-specific
floor exists yet (J-09, the studies' own Scout registration, is eight iterations away) --
``runs/goal-session-rapid-microscope/state/assumptions.md`` (iter-1, goal-decomposer) already
records this as a reversible, gate-free reading: all three rows compare today's corpus-wide
distinct session-date count against the SAME frozen walk-forward fold-geometry floor
(``docs/rapid-validation-spec.md`` §1: ``WF_TRAIN_MIN_SESSIONS`` (40) + ``WF_TEST_MIN_SESSIONS``
(20) = 60). Neither constant is owned by any module yet -- ``walkforward.py`` (J-05) becomes the
canonical owner; this iteration transcribes the frozen spec values as the FIRST code
representation of them (a future J-05 dev should import these two names from here, or supersede
them, never mint a second, independently-valued copy)."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from ..providers.base import Event, QuoteEvent, TradeEvent
from .datasets import DatasetStore
from .micro_join import BAND_TOUCH_STATUS_NOT_ENUMERATED, joinable_corpus_counts
from .referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
from . import vault

if TYPE_CHECKING:  # pragma: no cover -- type-checking only, never a runtime import (no cycle risk)
    from .desk_playbook_context import BandMapResolver

__all__ = [
    "WF_TRAIN_MIN_SESSIONS",
    "WF_TEST_MIN_SESSIONS",
    "PILOT_STUDY_IDS",
    "SPLIT_PROVENANCE_HAND_ASSIGNED",
    "EXPOSURE_STATE_EXPLORATORY",
    "MicroReadinessCache",
    "resolve_micro_readiness_cache_db_path",
    "MicroBandTouchCache",
    "resolve_micro_band_touch_cache_db_path",
    "build_readiness",
]

# --- the frozen constants this iteration serves (see module docstring for provenance) ---------------

# docs/rapid-validation-spec.md §1 -- transcribed verbatim, not invented (see module docstring).
WF_TRAIN_MIN_SESSIONS = 40
WF_TEST_MIN_SESSIONS = 20

# The three studies goal.md J-09 predeclares, in its own stated priority order -- named here only
# for the floor-comparison table; registering their actual Scout specs is J-09's work.
PILOT_STUDY_IDS = (
    "range_wall_failed_aggression",
    "delta_divergence_level_tests",
    "capitulation_exhaustion",
)

SPLIT_PROVENANCE_HAND_ASSIGNED = "hand_assigned"
EXPOSURE_STATE_EXPLORATORY = "exploratory"

_FLOOR_NAME = "wf_fold_geometry"
_FLOOR_STATUS_MET = "floor_met"
_FLOOR_STATUS_UNMET = "floor_unmet"

# This module's own private ZoneInfo constant -- the referee_evidence.py per-module idiom (module
# docstring). RTH bounds are the spec's own "09:30-16:00 ET" (docs/rapid-validation-spec.md, and
# goal.md's Data-contract section, verbatim).
_ET_ZONE = ZoneInfo("America/New_York")
_RTH_OPEN = time(9, 30)
_RTH_CLOSE = time(16, 0)
_RTH_MINUTES_PER_SESSION = 390.0  # 16:00 - 09:30, the standard-session-equivalents denominator

# r13: the corpus must be judgeable by QUALITY, not only by count. `fallback_frac` is already
# served per shard; this is the aggregate an operator needs before reading any flow result -- an
# aggressor label produced by the tick test is an INFERENCE, not ground truth, and a flow effect
# measured mostly on inferences is weak evidence however large its sample.
#
# The threshold is a plain MAJORITY -- not a tuned number, and it GATES NOTHING. It answers one
# question: "on this shard, are most of the buy/sell labels determined by the quote rule, or
# guessed?" Nothing in the pipeline reads it; it is a disclosure only (the spec section 5.4
# fallback-tercile stratification remains the mechanism that actually stratifies a result).
_FALLBACK_FRAC_DISCLOSURE_THRESHOLD = 0.5


def _label_quality(shards: list[dict]) -> dict:
    """r13: the aggregate aggressor-label trustworthiness of the exploratory corpus, derived
    ENTIRELY from the per-shard ``fallback_frac``/``trade_count`` values already served above --
    no second source, no recomputation, no new I/O.

    ``trade_weighted_fallback_frac`` is the honest corpus-level figure: a 100-trade shard and a
    500,000-trade shard must not weigh the same. ``shards_majority_inferred`` counts shards whose
    labels are more guessed than determined. All of it is a DISCLOSURE -- nothing gates on it.
    Empty corpus answers ``None`` magnitudes, never a fabricated 0.0 that would read as perfect
    label quality."""
    measured = [s for s in shards if s.get("fallback_frac") is not None]
    total_trades = sum(s.get("trade_count") or 0 for s in measured)
    weighted = (
        sum((s["fallback_frac"] * (s.get("trade_count") or 0)) for s in measured) / total_trades
        if total_trades
        else None
    )
    fracs = [s["fallback_frac"] for s in measured]
    return {
        "shards_measured": len(measured),
        "trade_weighted_fallback_frac": round(weighted, 4) if weighted is not None else None,
        "min_fallback_frac": round(min(fracs), 4) if fracs else None,
        "max_fallback_frac": round(max(fracs), 4) if fracs else None,
        "majority_inferred_threshold": _FALLBACK_FRAC_DISCLOSURE_THRESHOLD,
        "shards_majority_inferred": sum(
            1 for f in fracs if f > _FALLBACK_FRAC_DISCLOSURE_THRESHOLD
        ),
        # r13 contract pass: the caveat is FEATURE-FAMILY-SCOPED, and the note now says so. The
        # code has always drawn this line (`scout.AGGRESSOR_DERIVED_FEATURES`: "F-FLOW and
        # F-RESPONSE are derived from the engine's aggressor SIDE classification; F-LIQUIDITY ...
        # is not -- it never reads `side` at all"), but this served sentence did not, and a reader
        # could take it as "the whole corpus is weak". It is not: a high fallback fraction says
        # nothing whatever about quote_imbalance, microprice or spread_change.
        "affected_families": ["F-FLOW", "F-RESPONSE"],
        "unaffected_families": ["F-LIQUIDITY"],
        "note": (
            "fallback_frac is the share of this corpus's aggressor (buy/sell) labels produced by "
            "the tick test rather than the quote rule -- an INFERENCE, never ground truth. It is a "
            "material caveat for the AGGRESSOR-DERIVED families only (F-FLOW, F-RESPONSE: "
            "cumulative delta, imbalance, runs, bursts, impact efficiency, failed aggression): a "
            "result from those measured largely on inferred labels is weak evidence however large "
            "its sample. It says NOTHING about F-LIQUIDITY (quote imbalance, microprice, spread "
            "change), which never reads the aggressor side at all, and it is not by itself "
            "evidence that the corpus as a whole is weak. A disclosure only: nothing gates on "
            "these numbers; the per-candidate fallback-tercile stratification is the mechanism "
            "that actually stratifies an aggressor-derived result."
        ),
    }


# --- session-date / RTH-coverage arithmetic (cheap; no event replay) --------------------------------


def _et_datetime(iso_utc: str) -> datetime:
    """A stored UTC ISO timestamp (``window_start_utc``/``window_end_utc``, possibly carrying
    fractional seconds), converted to this module's own ET zone."""
    parsed = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(_ET_ZONE)


def _fmt_et(value: datetime) -> str:
    return value.strftime("%H:%M")


def _rth_overlap(start_et: datetime, end_et: datetime, session_date: date) -> tuple[float, list[str]]:
    """Minutes of ``[start_et, end_et)`` covered by ``session_date``'s 09:30-16:00 ET RTH window,
    plus the honest coverage-gap sentence(s) -- ``[]`` when the window fully covers RTH end to
    end; a single whole-session gap when the window does not overlap RTH at all."""
    rth_open = datetime.combine(session_date, _RTH_OPEN, tzinfo=_ET_ZONE)
    rth_close = datetime.combine(session_date, _RTH_CLOSE, tzinfo=_ET_ZONE)
    overlap_start = max(start_et, rth_open)
    overlap_end = min(end_et, rth_close)
    if overlap_start >= overlap_end:
        return 0.0, [f"{_fmt_et(rth_open)}–{_fmt_et(rth_close)} ET not covered"]
    minutes = (overlap_end - overlap_start).total_seconds() / 60.0
    gaps: list[str] = []
    if overlap_start > rth_open:
        gaps.append(f"{_fmt_et(rth_open)}–{_fmt_et(overlap_start)} ET not covered")
    if overlap_end < rth_close:
        gaps.append(f"{_fmt_et(overlap_end)}–{_fmt_et(rth_close)} ET not covered")
    return minutes, gaps


# --- fallback_frac: the one expensive per-shard computation, plus its checksum-keyed cache ----------


def _quote_rule_decides(trade: TradeEvent, quote: QuoteEvent | None) -> bool:
    """Whether ``aggressor.classify_aggressor``'s Stage 1 (the quote rule) decides this trade --
    mirrors that function's own documented precondition verbatim (module docstring); the ONLY
    factor is the trade's price against the quote in effect, independent of any prior-trade
    state. ``False`` means Stage 2 (the Lee-Ready tick-test fallback) fires."""
    return quote is not None and (trade.price >= quote.ask or trade.price <= quote.bid)


def _compute_fallback_frac(events: list[Event]) -> float:
    """The fraction of a shard's trades classified via the Stage-2 fallback rather than the
    Stage-1 quote rule -- a single linear scan carrying forward the most recently seen quote (the
    ONLY state ``_quote_rule_decides`` reads), exactly the state ``TapeEngine.process_event``
    itself carries at the instant it classifies a trade (module docstring). A shard with zero
    trades reads ``0.0`` (never a division by zero, never fabricated)."""
    current_quote: QuoteEvent | None = None
    total_trades = 0
    fallback_trades = 0
    for event in events:
        if isinstance(event, QuoteEvent):
            current_quote = event
            continue
        total_trades += 1
        if not _quote_rule_decides(event, current_quote):
            fallback_trades += 1
    if total_trades == 0:
        return 0.0
    return fallback_trades / total_trades


# Mirrors every sibling durable cache's identical brief writer-contention tolerance
# (tradability_cache.py/dataset_index.py's own constant).
_BUSY_TIMEOUT_MS = 5000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS micro_fallback_frac_cache (
    checksum       TEXT PRIMARY KEY,
    fallback_frac  REAL NOT NULL,
    created_utc    TEXT NOT NULL
)
"""

# Deliberately its own env var, distinct from every sibling durable cache's (Constraints:
# "storage dirs are env-var-or-sibling defaults -- the TAPEOLOGY_MICRO_* family").
_CACHE_DB_ENV = "TAPEOLOGY_MICRO_READINESS_CACHE_DB"


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def resolve_micro_readiness_cache_db_path(dataset_dir: str) -> str:
    """The cache DB path resolution policy -- the ``resolve_tradability_cache_db_path`` env-else-
    sibling shape: ``TAPEOLOGY_MICRO_READINESS_CACHE_DB`` if set, else ``micro_readiness_cache.db``
    co-located as a SIBLING of the caller's dataset-store directory (e.g. ``.data/datasets`` ->
    ``.data/micro_readiness_cache.db``)."""
    override = os.environ.get(_CACHE_DB_ENV)
    if override:
        return override
    return str(Path(dataset_dir).parent / "micro_readiness_cache.db")


class MicroReadinessCache:
    """One durable SQLite row per dataset content ``checksum`` -> its ``fallback_frac`` --
    ``TradabilityCache``'s "rebuildable result only, owns nothing" contract (see that module's own
    docstring for the full discipline), applied to a single-float value instead of a whole map. A
    miss NEVER computes -- ``lookup`` has no ``compute_fn``, mechanically incapable of running the
    replay; a corrupted/unreadable DB is a full miss, never a crash; a ``publish`` failure is
    swallowed, never propagated -- the caller is still holding its own freshly-computed value."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(_SCHEMA)
            finally:
                conn.close()
        except sqlite3.Error:
            pass  # self-heals: every subsequent lookup/publish independently re-attempts

    @property
    def db_path(self) -> str:
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        """A FRESH, short-lived connection per call (the ``TradabilityCache._connect`` precedent)."""
        conn = sqlite3.connect(
            self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0
        )
        conn.row_factory = sqlite3.Row
        if self._db_path != ":memory:":
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        return conn

    def lookup(self, checksum: str) -> float | None:
        try:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT fallback_frac FROM micro_fallback_frac_cache WHERE checksum=?",
                    (checksum,),
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            return None
        return None if row is None else float(row["fallback_frac"])

    def publish(self, checksum: str, fallback_frac: float) -> None:
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO micro_fallback_frac_cache "
                        "(checksum, fallback_frac, created_utc) VALUES (?,?,?)",
                        (checksum, fallback_frac, _iso_utc_now()),
                    )
            finally:
                conn.close()
        except sqlite3.Error:
            pass


# --- the band-touch count cache (iter-26): the SAME durable-cache contract as MicroReadinessCache
# above, applied to `micro_join.enumerate_band_touches`'s per-dataset touch count instead of
# `fallback_frac` -- that walk over every record's own event stream is the ~22s-and-growing
# uncached cost `joinable_corpus_counts` pays on every warm GET once a resolver is supplied
# (`micro_join.py`'s own `enumerate_band_touches` docstring: "the expensive event load"). Keyed on
# the COMPOSITE `(dataset checksum, resolver.map_key(symbol, window_start_epoch))` -- never the
# checksum alone -- because a dataset's own bytes never change (immutability, rail 9) but the BAND
# MAP a resolver serves for it can (a re-warmed tradability cache under a new store signature), and
# a stale hit under the old map would silently under/over-count touches against bands that no
# longer describe that basis day. Deliberately its own env var, distinct from every sibling durable
# cache's (the `MicroReadinessCache` docstring above: "the TAPEOLOGY_MICRO_* family").
_BAND_TOUCH_CACHE_DB_ENV = "TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB"

_BAND_TOUCH_SCHEMA = """
CREATE TABLE IF NOT EXISTS micro_band_touch_cache (
    checksum     TEXT NOT NULL,
    map_key      TEXT NOT NULL,
    touch_count  INTEGER NOT NULL,
    created_utc  TEXT NOT NULL,
    PRIMARY KEY (checksum, map_key)
)
"""


def resolve_micro_band_touch_cache_db_path(dataset_dir: str) -> str:
    """The band-touch cache DB path resolution policy -- the IDENTICAL env-else-sibling shape
    ``resolve_micro_readiness_cache_db_path`` above uses, under its own env var:
    ``TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB`` if set, else ``micro_band_touch_cache.db`` co-located as
    a SIBLING of the caller's dataset-store directory."""
    override = os.environ.get(_BAND_TOUCH_CACHE_DB_ENV)
    if override:
        return override
    return str(Path(dataset_dir).parent / "micro_band_touch_cache.db")


class MicroBandTouchCache:
    """One durable SQLite row per ``(dataset checksum, resolver.map_key(symbol,
    window_start_epoch))`` composite key -> its enumerated band-touch COUNT --
    ``MicroReadinessCache``'s own contract (this module's docstring, above class), applied to a
    per-record touch count instead of a per-shard ``fallback_frac``. A miss NEVER computes --
    ``lookup`` has no ``compute_fn``; a corrupted/unreadable DB is a full miss, never a crash; a
    ``publish`` failure is swallowed, never propagated -- the caller is still holding its own
    freshly-computed count. Publishes ONLY a resolved count, never a placeholder (goal.md IN SCOPE
    item 1)."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(_BAND_TOUCH_SCHEMA)
            finally:
                conn.close()
        except sqlite3.Error:
            pass  # self-heals: every subsequent lookup/publish independently re-attempts

    @property
    def db_path(self) -> str:
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        """A FRESH, short-lived connection per call (the ``MicroReadinessCache._connect``/
        ``TradabilityCache._connect`` precedent)."""
        conn = sqlite3.connect(
            self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0
        )
        conn.row_factory = sqlite3.Row
        if self._db_path != ":memory:":
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        return conn

    def lookup(self, checksum: str, map_key: str) -> int | None:
        try:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT touch_count FROM micro_band_touch_cache WHERE checksum=? AND map_key=?",
                    (checksum, map_key),
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            return None
        return None if row is None else int(row["touch_count"])

    def publish(self, checksum: str, map_key: str, touch_count: int) -> None:
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO micro_band_touch_cache "
                        "(checksum, map_key, touch_count, created_utc) VALUES (?,?,?,?)",
                        (checksum, map_key, touch_count, _iso_utc_now()),
                    )
            finally:
                conn.close()
        except sqlite3.Error:
            pass


# --- the whole readiness aggregation -----------------------------------------------------------------


def build_readiness(
    store: DatasetStore,
    cache: MicroReadinessCache,
    *,
    dataset_dir: str,
    playbook_store=None,
    resolver: "BandMapResolver | None" = None,
    band_touch_cache: "MicroBandTouchCache | None" = None,
) -> dict:
    """The whole ``GET /research/desk/micro/readiness`` body -- a pure aggregation over
    ``DatasetStore.list()``'s already-verified records (module docstring). Deterministic and
    byte-reproducible: an unchanged store + a warm cache yields a byte-identical response on
    every call (TC-7) -- nothing here reads the wall clock into the served shape (the cache's own
    ``created_utc`` never leaves the cache).

    ``playbook_store`` (J-03, ``desk_playbook.PlaybookStore``) is OPTIONAL and defaults to
    ``None`` -- callers that do not pass one (every pre-J-03 test in this file) get the honest
    ``joinable_corpus`` zero rather than an error, since "no playbook evidence was even checked"
    is a true statement in that case, never a fabricated one.

    ``resolver`` (J-09, ``desk_playbook_context.BandMapResolver``) is likewise OPTIONAL, defaulting
    to ``None`` -- passed straight through to ``micro_join.joinable_corpus_counts`` (never
    constructed here; this module owns no ``BarStore``/``Config`` wiring of its own -- the caller,
    ``micro_routes.py``, already holds both). Omitting it (every pre-J-09 test) keeps
    ``band_touch_count`` at its honest ``not_enumerated`` sentinel; supplying one materializes the
    real enumerated int (``micro_join.py``'s own docstring). Only consulted when ``playbook_store``
    is also given -- the ``playbook_store is None`` branch below already answers "nothing was
    checked" honestly for BOTH counts at once, never a mixed state.

    ``band_touch_cache`` (iter-26, ``MicroBandTouchCache`` above) is likewise OPTIONAL, passed
    straight through to ``micro_join.joinable_corpus_counts`` -- omitting it (every pre-iter-26
    caller) keeps today's uncached per-record ``enumerate_band_touches`` walk byte-identical;
    supplying one only changes warm-path LATENCY, never the served ``band_touch_count`` value
    (goal.md IN SCOPE item 1).

    **Sealed-tranche AGGREGATES only (iter-9, spec section 7.5 point 4, r3; widened iteration 11,
    point 7, r5).** A dataset that is part of an UNRESOLVED registered-universe pool gets NO
    per-shard row and NO per-shard ``exposure_state`` here -- its row would carry the symbol,
    session date and exact trade/quote counts section 7.5 withholds, and the iter-9 audit's
    finding B1 demonstrated this table doing exactly that for a ledger-tracked sealed shard.
    Iteration 11 widens WHICH datasets that covers: membership is no longer only "carries an
    explicit vault shard-ledger row" but "is caught by ``vault.
    unresolved_pool_universe_by_dataset_id``" (that function's own docstring has the full
    reasoning) -- because a repo-wide grep at authoring finds zero production call sites of
    ``seal_shard``, so a real recording finalized under a registered universe would otherwise
    carry NO ledger row at all and be fully identifiable here, the exact leak point 7 exists to
    close. Such a shard is counted instead in ``sealed_tranche`` (shard count, distinct
    symbol-days, per-universe totals -- section 7.5's own enumerated aggregate list) and is
    excluded from ``totals``/``study_floors``, since withheld evidence is by construction not
    available to any study. The exclusion also means this fold never LOADS a withheld shard's
    events, so the ``fallback_frac`` walk below can never become an exploratory read of withheld
    tape (the era's *(critical)* anti-goal) -- the withhold check still runs BEFORE
    ``store.load_events`` below, exactly as before (TC-10). The vault is read through the SAME
    ``vault.shard_ledger_for_dataset_dir(dataset_dir)``/``vault.universe_ledger_for_dataset_dir(
    dataset_dir)`` resolution every other consumer uses -- one vault location, never a second.
    With nothing sealed and no universe registered, ``sealed_tranche`` is an all-zero row and
    every other value in this payload is byte-identical to its pre-iter-9 self (proven inert
    against the real corpus, which has zero registered universes today).

    Membership is the VAULT's answer, never re-derived here; the arithmetic over it is this
    module's own, exactly as it already is for ``totals`` (the ``joinable_corpus`` precedent, where
    ``micro_join`` owns the count and this module owns nothing but its placement). ``sealed_tranche``
    counts the withheld shards PRESENT IN THIS STORE -- a vault ledger row naming a dataset that no
    longer sits in ``dataset_dir`` contributes nothing here, since this payload's whole subject is
    what evidence exists on this disk."""
    records, errors = store.list()
    root = Path(dataset_dir)
    # Pure metadata arithmetic (no event replay -- `window_start_utc` is already-verified
    # manifest data from `store.list()` above): computed for EVERY record, including ones that
    # turn out withheld, because the iteration-11 pool predicate needs each record's own
    # (symbol, session_date, created_utc) to test against a registered universe's rule (spec
    # section 7.5 point 7, r5). This does not touch `store.load_events` -- the load-order guard
    # (TC-10) is about EVENT reads, which stay confined to the kept branch below exactly as
    # before.
    start_et_by_id: dict[str, datetime] = {
        meta["id"]: _et_datetime(meta["window_start_utc"]) for meta in records
    }
    withheld_universe_by_id = vault.unresolved_pool_universe_by_dataset_id(
        vault.shard_ledger_for_dataset_dir(dataset_dir),
        vault.universe_ledger_for_dataset_dir(dataset_dir),
        [
            (
                meta["id"],
                meta["symbol"],
                start_et_by_id[meta["id"]].date().isoformat(),
                meta.get("created_utc", ""),
            )
            for meta in records
        ],
    )

    shards: list[dict] = []
    symbol_days: set[tuple[str, str]] = set()
    session_dates: set[str] = set()
    rth_minutes_total = 0.0
    sealed_symbol_days: set[tuple[str, str]] = set()
    sealed_shard_count = 0
    sealed_symbol_days_by_universe: dict[str, set[tuple[str, str]]] = {}
    sealed_shard_count_by_universe: dict[str, int] = {}

    for meta in records:
        if meta["id"] in withheld_universe_by_id:
            # Section 7.5 point 4/7: aggregates only. Computed from the store's own metadata
            # SERVER-side and never served per shard -- the payload below carries counts, never a
            # symbol, a date, or an id.
            universe_id = withheld_universe_by_id[meta["id"]]
            symbol_day = (meta["symbol"], start_et_by_id[meta["id"]].date().isoformat())
            sealed_shard_count += 1
            sealed_symbol_days.add(symbol_day)
            sealed_shard_count_by_universe[universe_id] = (
                sealed_shard_count_by_universe.get(universe_id, 0) + 1
            )
            sealed_symbol_days_by_universe.setdefault(universe_id, set()).add(symbol_day)
            continue

        start_et = start_et_by_id[meta["id"]]
        end_et = _et_datetime(meta["window_end_utc"])
        session_date = start_et.date()
        session_date_str = session_date.isoformat()
        minutes, gaps = _rth_overlap(start_et, end_et, session_date)
        rth_minutes_total += minutes
        symbol_days.add((meta["symbol"], session_date_str))
        session_dates.add(session_date_str)

        checksum = meta["checksum"]
        fallback_frac = cache.lookup(checksum)
        if fallback_frac is None:
            events = store.load_events(meta["id"])
            fallback_frac = _compute_fallback_frac(events)
            cache.publish(checksum, fallback_frac)

        try:
            shard_bytes = (root / f"{meta['id']}.json").stat().st_size
        except OSError:
            # Honest zero on a file removed between store.list()'s own verify and this stat --
            # never a crash, and store.list() already proved the metadata itself is trustworthy.
            shard_bytes = 0

        shards.append(
            {
                "dataset_id": meta["id"],
                "symbol": meta["symbol"],
                "session_date": session_date_str,
                "data_feed": meta["data_feed"],
                "window_start_utc": meta["window_start_utc"],
                "window_end_utc": meta["window_end_utc"],
                "trade_count": meta["event_counts"]["trades"],
                "quote_count": meta["event_counts"]["quotes"],
                "bytes": shard_bytes,
                "coverage_gaps": gaps,
                "fallback_frac": fallback_frac,
                "checksum": checksum,
                "split_provenance": SPLIT_PROVENANCE_HAND_ASSIGNED,
                "exposure_state": EXPOSURE_STATE_EXPLORATORY,
            }
        )

    available_sessions = len(session_dates)
    required_sessions = WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS
    floor_status = _FLOOR_STATUS_MET if available_sessions >= required_sessions else _FLOOR_STATUS_UNMET
    study_floors = [
        {
            "study_id": study_id,
            "floor_name": _FLOOR_NAME,
            "required_sessions": required_sessions,
            "available_sessions": available_sessions,
            "status": floor_status,
        }
        for study_id in PILOT_STUDY_IDS
    ]

    totals = {
        "distinct_symbol_days": len(symbol_days),
        # The EXPLORATORY inventory: `shards` above, one row each. A sealed shard is deliberately
        # absent from both (spec section 7.5 point 4) -- it is neither available evidence nor a
        # servable row -- and is counted in `sealed_tranche` below instead.
        "distinct_datasets": len(shards),
        "rth_minutes_covered": round(rth_minutes_total, 2),
        "session_equivalents": round(rth_minutes_total / _RTH_MINUTES_PER_SESSION, 4),
        "referee_tick_gate_symbol_days": REFEREE_TICK_GATE_SYMBOL_DAYS,
        # r13: breadth and label quality, so corpus GROWTH can be judged by what the evidence is
        # worth and not only by how much of it there is. Every input is already served per shard
        # above -- this aggregates, it never introduces a second computation of anything.
        "distinct_symbols": len({s["symbol"] for s in shards}),
        "distinct_sessions": len(session_dates),
        "label_quality": _label_quality(shards),
    }

    # J-03: honestly zero (never computed) when no playbook_store is given at all -- a true
    # statement ("no playbook evidence was even checked"), never a fabricated count. When one IS
    # given, the count is owned entirely by micro_join.joinable_corpus_counts (never re-derived
    # here -- module docstring). iter-4 passenger fix: this fallback shape now mirrors
    # joinable_corpus_counts's own typed band_touch_count ("not enumerated", never a bare 0) and
    # its playbook_integrity_errors key -- `[]` here is the SAME "nothing was checked, so nothing
    # is known to be corrupt" convention every other empty/unbuilt store in this codebase reports
    # (DatasetStore.list()/PlaybookStore.list() both answer `[]` on an absent store, never a
    # fabricated warning).
    if playbook_store is None:
        joinable_corpus = {
            "total": 0,
            "playbook_signal_count": 0,
            "band_touch_count": {"status": BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None},
            "by_setup_id": {},
            "playbook_integrity_errors": [],
            # Spec section 7.5 point 6 (r4): a run that enumerated nothing excluded nothing --
            # a true statement about THIS fallback, not a copy of the real count (which only
            # `joinable_corpus_counts` below is entitled to compute).
            "withheld_excluded": 0,
        }
    else:
        joinable_corpus = joinable_corpus_counts(
            store, playbook_store, resolver=resolver, band_touch_cache=band_touch_cache
        )

    sealed_tranche = {
        "shard_count": sealed_shard_count,
        "symbol_days": len(sealed_symbol_days),
        "by_universe": {
            universe_id: {
                "shard_count": sealed_shard_count_by_universe[universe_id],
                "symbol_days": len(sealed_symbol_days_by_universe[universe_id]),
            }
            for universe_id in sorted(sealed_shard_count_by_universe)
        },
    }

    return {
        "totals": totals,
        "shards": shards,
        "study_floors": study_floors,
        "integrity_errors": errors,
        "joinable_corpus": joinable_corpus,
        "sealed_tranche": sealed_tranche,
    }
