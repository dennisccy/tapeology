"""The multi-timeframe OHLC bar store (era-4 capability 1, J-01) — Data Contract row 38's ONE owner.

THIS MODULE is the only code that reads or writes bar-series files. A bar series is an IMMUTABLE
recording of one symbol's OHLC candle series over a UTC window at one timeframe (the
provider-neutral ``RawBar`` fields only — never a raw vendor payload) plus metadata (id, symbol,
timeframe, UTC window, feed, bar count, a content checksum, and a created timestamp). Files live
under the config-owned bar directory (``TAPEOLOGY_BAR_DIR`` override, ``config.bar_dir`` default —
gitignored via ``.data/``), one JSON file per bar series. This module explicitly MIRRORS
``research/datasets.py`` end to end (the spec's own directive): double checksum, verified on every
load, ``record`` as the only mutation, the same honest-failure taxonomy.

Disciplines (each an anti-goal or a J-01 acceptance clause):

  * **Explicit recording only.** Recording happens ONLY through ``BarStore.record``, called by the
    ``POST /research/bars`` route after a real Alpaca ``fetch_bars`` call. Nothing in the
    watch/stream path imports this module — the live cockpit's tape is never persisted here either
    (no ambient recording).
  * **Checksummed + re-verified on every content change (stat-keyed).** ``meta.checksum`` is a
    sha256 over the bar-series CONTENT (symbol + timeframe + feed + the ordered candles) computed
    at registration; a second whole-record checksum covers every metadata byte. era-fast_wall J-02:
    a module-level, stat-keyed (``path``, ``st_size``, ``st_mtime_ns``) cache serves an ALREADY
    fully-verified record with zero I/O while a file's stat is unchanged; ANY stat mismatch — the
    only way "unchanged" can be honestly claimed — re-runs the full verifier, recomputing BOTH
    checksums exactly as before caching existed. A corrupted or tampered file raises the explicit
    ``BarSeriesIntegrityError`` on that re-verify — never silence, never a fabricated series, and
    never cached (only a successful verify is ever published).
  * **Immutable — structurally.** No update/delete function exists anywhere in this module
    (immutability is structural, not policed). The only mutation is ``record``, and it REFUSES
    content that is already registered: re-recording the same series raises the 409-style
    ``BarSeriesAlreadyRegistered`` naming the existing series.
  * **Candles served embedded.** Unlike tick-level datasets (whose events are large and served only
    through a separate loader), a bar series is small by construction, so ``get``/``list`` embed the
    ordered OHLC candles directly on the served dict (the phase spec's explicit requirement) while
    the on-disk shape still separates ``meta`` from ``bars`` for the same checksum discipline. Three
    ADDITIVE projections exist for readers that do not want a whole series' candles at once:
    ``include_bars=False`` (metadata only, ``bars`` key omitted), ``candles(...)`` (a bounded,
    cursor-anchored slice of ONE series) and ``merged_candles(...)`` (the same slice over every
    recorded series for one symbol+timeframe, folded by timestamp). All go through the SAME verified
    load — projections of verified content, never a second, unverified read path.
  * **Honest failure states.** Unknown id -> ``BarSeriesNotFound``; an empty fetched window ->
    ``EmptyBarWindowError`` (nothing written, nothing fabricated); a candle with no finite price ->
    ``NonFiniteBarPriceError`` (era-desk-iter-4 audit B1 — the write-path rail that makes "a
    priceless bar can never reach disk" structural rather than a per-caller convention; the read
    side excludes any already-recorded priceless ROW from the merged view and reports it in
    ``integrity_errors``, never touching the append-only file).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..providers.adapters.base import RawBar
from .bar_verify_cache import BarVerifyCache


class BarSeriesNotFound(Exception):
    """No bar-series file exists for the requested id (the route maps this to a 404)."""


class BarSeriesIntegrityError(Exception):
    """A bar-series file failed its on-load verification — corrupted or tampered, surfaced
    explicitly (never silence, never a fabricated series)."""


class BarSeriesAlreadyRegistered(Exception):
    """The exact bar content (symbol + timeframe + feed + candles) is already registered. Bar
    series are immutable — there is no update/re-record path anywhere in this module."""

    def __init__(self, existing_id: str, existing_symbol: str, existing_timeframe: str) -> None:
        self.existing_id = existing_id
        self.existing_symbol = existing_symbol
        self.existing_timeframe = existing_timeframe
        super().__init__(
            f"this exact bar series is already registered as '{existing_id}' "
            f"({existing_symbol} {existing_timeframe}) — bar series are immutable and are never "
            f"re-recorded"
        )


class EmptyBarWindowError(Exception):
    """The fetched window contains no bars — an explicit refusal; nothing is written and nothing
    is fabricated."""


class NonFiniteBarPriceError(Exception):
    """A bar offered for recording carries a non-finite price (``NaN``/``inf``) in one of its OHLC
    fields — an explicit refusal at the ONE write path; nothing is written.

    A candle with no price is not a candle. Vendors emit such a row for a session that has not
    traded yet (pandas ``NaN`` in every price column), and ``float(nan)`` succeeds silently — so
    without this guard the append-only, checksummed store accepts a permanently priceless bar, and
    JSON round-trips it through the non-standard ``NaN`` token into every reader as ``null``
    (era-desk-iter-4 audit B1: that is how 60 series over 58 symbols were poisoned and how
    ``/structure``'s candlestick chart was taken down). The adapter that knows what the vendor meant
    drops the row first (``providers/adapters/yahoo.py::_is_priced_row``); THIS is the structural
    backstop that makes "a priceless bar can never reach disk" true for every write path, present
    and future."""


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace) — the SAME encoding ``research/datasets.py`` uses."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc(epoch: float) -> str:
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _bar_to_row(bar: RawBar) -> dict:
    """One stored candle row (``RawBar`` fields minus symbol/timeframe — the series-level ``meta``
    owns those; rows do not repeat them, mirroring ``datasets._event_to_row``)."""
    return {
        "ts": bar.epoch,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
    }


_PRICE_FIELDS = ("open", "high", "low", "close")


def _has_finite_prices(row: dict) -> bool:
    """Does ONE stored candle row carry a real, finite number in all four price fields?

    The single predicate behind both halves of the priceless-bar rail: ``record`` REFUSES a row that
    fails it (``NonFiniteBarPriceError`` — nothing reaches disk), and ``_merged_rows`` EXCLUDES a
    row that fails it from the merged view while reporting it in ``integrity_errors`` (the 60 series
    already on disk when the guard shipped — files never touched, since bar series are append-only
    and are never deleted, re-tagged, or content-perturbed)."""
    try:
        return all(math.isfinite(float(row[field])) for field in _PRICE_FIELDS)
    except (KeyError, TypeError, ValueError):
        return False


def _row_to_bar(symbol: str, timeframe: str, row: dict) -> RawBar:
    return RawBar(
        symbol, timeframe, row["ts"], row["open"], row["high"], row["low"], row["close"], row["volume"]
    )


def _content_checksum(symbol: str, timeframe: str, feed: str, rows: list[dict]) -> str:
    """The bar series' CONTENT identity: a sha256 over symbol + timeframe + feed + the ordered
    candle rows. Registration-time duplicate detection and the on-load verification both recompute
    exactly this."""
    return _sha256(_canonical({"symbol": symbol, "timeframe": timeframe, "feed": feed, "bars": rows}))


@dataclass(frozen=True)
class _LoadedBarSeries:
    """One verified load: the series' identity/stat metadata plus its stored candle rows."""

    meta: dict
    rows: list[dict]


# --- era-fast_wall J-02: the module-level stat-keyed verified-record cache ----------------------
# Mirrors ``setups.py``'s ``_SCAN_CACHE`` atomic-publish + read-local-reference-before-inspect
# discipline (see that module's own block comment for the full torn-read rationale), adapted from
# ONE remembered slot to a per-file dict: a module global, not an instance attribute, because
# ``BarStore`` is constructed fresh per FastAPI dependency call and has no natural long-lived
# instance to hang a cache off. Each entry is an immutable tuple ``(st_size, st_mtime_ns,
# _LoadedBarSeries)`` published via a SINGLE dict-key assignment — CPython's GIL makes that one
# bytecode op atomic, so a concurrent reader (``_VERIFIED_CACHE.get(path)``, read into a local
# ONCE before inspection) always observes either the complete prior entry or the complete new one,
# never a torn value. A concurrent miss on multiple threads only ever costs a redundant, harmless
# recompute (``_load`` is a pure function of the file's bytes) — never a corrupted cache.
#
# Key: the absolute file path (``str(Path)``) -- distinct roots (e.g. different ``tmp_path``
# test directories) can never collide. Value: ``(st_size, st_mtime_ns, _LoadedBarSeries)`` — ANY
# stat mismatch on a later read is treated as a miss and re-verifies in full; an integrity error
# is never cached (only a SUCCESSFUL ``_load`` result is ever published). See ``_cached_load``
# below for the ~2s racy-write guard that additionally refuses to publish a just-written file.
_VERIFIED_CACHE: dict[str, tuple[int, int, _LoadedBarSeries]] = {}

# The metadata-ONLY twin of ``_VERIFIED_CACHE``, same ``(path) -> (st_size, st_mtime_ns, value)``
# shape and same atomic-publish discipline, holding just a series' ``meta`` dict.
#
# Every whole-store scan (``list``, and ``_merged_rows``' "which files belong to this pair?" pass)
# needs ONLY metadata, and metadata is ~200 bytes against a series' megabytes of candles. Keeping
# the two tiers separate means such a scan neither parses nor retains the rows: on the live desk
# store that turns a cold scan's ~15s / ~1.5GB of retained rows into a single SQLite query, and
# leaves ``_VERIFIED_CACHE`` holding only the pairs an analytic reader actually folded.
_META_CACHE: dict[str, tuple[int, int, dict]] = {}

# A file whose mtime is within this many seconds of "now" (at read time) is never published to the
# cache — the guard against a same-granularity rewrite being served stale (two writes landing
# within one mtime-resolution tick could otherwise be indistinguishable by stat alone).
_RACY_WRITE_GUARD_SECONDS = 2.0


# The merged-view memo behind ``BarStore.merged_candles``: key = (symbol, timeframe, the exact set of
# contributing (series_id, content-checksum) pairs); value = (ascending merged rows, meta, the
# per-series priceless-row reports excluded from that fold). Same atomic single-key-assignment
# publish discipline as ``_VERIFIED_CACHE`` above. Because the key names every contributing series
# AND its content checksum, ANY change to the recorded set (a new fetch, a deleted file, a changed
# file) yields a different key -- a stale merge cannot be served. The priceless-row reports ride
# ALONG in the cached value (rather than being recomputed, or routed through the uncacheable
# ``errors`` set) so a pair holding one is memoized exactly like any other.
_MERGED_CACHE: dict[tuple, tuple[list[dict], dict, list[dict]]] = {}


# The typed twin of ``_MERGED_CACHE``, under the SAME key: the ``RawBar`` projection ``merged_bars``
# serves. ``_MERGED_CACHE`` memoizes the FOLD but not the per-row ``_row_to_bar`` construction, so
# every analytic read of an already-folded pair still rebuilt one ``RawBar`` per stored row (measured
# ~474k constructions per screened member, since a screen reads the same "1d" pair three times and
# each of six timeframes at least once). ``RawBar`` is a FROZEN dataclass, so the instances
# themselves are safe to share across callers; only the enclosing list is rebuilt per call, exactly
# as ``get``/``list`` hand out fresh containers over cached content.
_TYPED_MERGED_CACHE: dict[tuple, list[RawBar]] = {}


# The name-sorted file list of a store root, keyed by that DIRECTORY's own
# ``(st_mtime_ns, st_ctime_ns)``. A directory's mtime changes whenever an entry is created or
# removed, so an unchanged pair means the SET of files is unchanged — and this cache holds nothing
# else: each file is still stat'd and, on any stat change, re-verified in full on every read, so a
# file edited in place (which does NOT touch the directory's mtime) is caught exactly as before.
# What it removes is only the repeated readdir + Path construction + sort, which a screened member
# paid eight times over and a top-up walk 1,818 times.
#
# Measured on this filesystem: consecutive file creations never share a directory mtime (minimum
# observed gap ~12µs against nanosecond-resolution stamps), and ``record`` additionally evicts its
# own root explicitly, so an in-process write is never missed even if a clock were coarser.
_DIR_LISTING_CACHE: dict[str, tuple[int, int, list[tuple[Path, str]]]] = {}

# The pair-locating scan behind ``_merged_entry``, keyed by the same directory generation:
# ``{root: (dir_mtime_ns, dir_ctime_ns, [(path, meta)], errors)}``.
#
# Answering "which files belong to (symbol, timeframe)?" means knowing every file's symbol and
# timeframe, and re-establishing that from scratch cost a stat of the WHOLE store per merged read —
# 1.1M syscalls for a 72-pair top-up slice, ~40% of that walk. Since a file's identity can only
# change by rewriting it, and a bar series is append-only and immutable by construction, that
# mapping is stable for as long as the directory's own entry set is.
#
# This memo NEVER decides whether a served bar is trustworthy. Every file the fold actually reads
# still goes through ``_cached_load`` — a fresh stat, and a full re-verify on any change — so a
# corrupt or edited file in the pair being folded raises exactly as before. ``list`` deliberately
# does NOT use this memo: it is the store-wide read, so it re-stats every file and keeps reporting
# store-wide integrity errors first-hand.
_PAIR_SCAN_CACHE: dict[str, tuple[int, int, list[tuple[Path, dict]], list[dict]]] = {}


def _series_entries(root: Path) -> list[tuple[Path, str, os.stat_result]]:
    """Every recorded series file under ``root``, NAME-sorted, each paired with its cache key
    (``str(path)``) and a freshly read stat — the one enumeration ``list`` and ``_merged_entry``
    share.

    Replaces ``sorted(root.glob("*.json"))`` + a separate ``path.stat()`` per file. Both halves are
    equivalences, not approximations:

      * **Order.** ``Path.__lt__`` compares ``_parts_normcase`` tuples; for two files in the SAME
        directory every part but the last is equal, so the comparison reduces to the file name.
        Sorting the names as plain strings therefore yields the identical sequence — at a fraction
        of the cost (~62k tuple-materializing Path comparisons per call became 62k string
        comparisons). Order is observable: it fixes the sequence of the ``errors`` list both readers
        return.
      * **Stat.** The stat is handed to ``_cached_load`` rather than re-read there, removing one
        ``stat(2)`` per file per read while the cache's validity test stays byte-for-byte the same
        ``(st_size, st_mtime_ns)`` comparison against the same file. It is read through bare
        ``os.stat`` on the already-built path string rather than ``Path.stat`` — the same syscall,
        without ``pathlib``'s per-call re-parsing, which measured ~4x the cost of the syscall itself
        at this scale.

    The ``Path`` objects and their key strings are cached with the listing, since rebuilding 5,104
    of them per read cost more than the syscalls did. Every file is still stat'd on every call, so a
    file edited in place — which leaves the directory's own mtime untouched — is still caught.

    A file that vanishes between the scan and its load is simply not in this list (or raises its own
    explicit error on load), exactly as a glob taken a moment later would have behaved."""
    key = str(root)
    try:
        dir_st = os.stat(key)
    except OSError:
        _DIR_LISTING_CACHE.pop(key, None)
        return []

    cached = _DIR_LISTING_CACHE.get(key)  # read-local-reference-before-inspect
    if cached is not None and cached[0] == dir_st.st_mtime_ns and cached[1] == dir_st.st_ctime_ns:
        listing = cached[2]
    else:
        try:
            with os.scandir(root) as entries:
                names = sorted(
                    entry.name for entry in entries if entry.name.endswith(".json") and entry.is_file()
                )
        except OSError:
            return []
        listing = [(root / name, os.path.join(key, name)) for name in names]
        _DIR_LISTING_CACHE[key] = (dir_st.st_mtime_ns, dir_st.st_ctime_ns, listing)  # atomic rebind

    found: list[tuple[Path, str, os.stat_result]] = []
    for path, path_key in listing:
        try:
            found.append((path, path_key, os.stat(path_key)))
        except OSError:
            continue  # removed since the listing was taken — the same absence a fresh scan reports
    return found


def _slice_rows(
    rows: list[dict],
    *,
    before_ts: float | None,
    after_ts: float | None,
    limit: int,
) -> tuple[list[dict], bool, bool]:
    """The ONE implementation of the cursor/slice semantics both candle reads serve (per-series
    ``BarStore.candles`` and merged ``BarStore.merged_candles``) -- see ``candles``'s docstring for
    the cursor contract. ``rows`` is consumed in its given order and never reordered; returned rows
    are fresh per-row copies (a caller mutating them can never poison a cached record)."""
    if before_ts is not None and after_ts is not None:
        raise ValueError("pass at most one of before_ts / after_ts — they anchor opposite ends")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    if before_ts is not None:
        matching = [i for i, row in enumerate(rows) if row["ts"] <= before_ts]
        window = matching[-limit:]
    elif after_ts is not None:
        matching = [i for i, row in enumerate(rows) if row["ts"] >= after_ts]
        window = matching[:limit]
    else:
        window = list(range(len(rows)))[-limit:]

    if not window:
        return [], False, False
    first, last = window[0], window[-1]
    return [dict(rows[i]) for i in window], first > 0, last < len(rows) - 1


def release_row_caches() -> None:
    """Drop every cached CANDLE, keeping the cheap metadata tiers.

    The row-bearing caches are unbounded by design — a stat match must serve an already-verified
    record with zero I/O — which is right for a store read repeatedly and wrong for a SWEEP that
    touches each symbol once and never returns to it. A ~101-member screen retained every member's
    folds to the end and peaked at ~2.3GB; four such walks in worker processes exceeded the host's
    memory ceiling outright and the pool died mid-run.

    Releasing them is purely a memory decision and can never change an answer: the next read of an
    evicted pair re-verifies and re-folds it from the canonical file, producing the identical bytes.
    ``_META_CACHE`` and ``_DIR_LISTING_CACHE`` deliberately survive — they are small (metadata and
    file names, not candles) and they are what make that re-read cheap."""
    _VERIFIED_CACHE.clear()
    _MERGED_CACHE.clear()
    _TYPED_MERGED_CACHE.clear()


def _reset_verified_cache_for_tests() -> None:
    """Test-only: clears the module-level verified-record cache. Never called from any production
    code path — exists solely so tests (and the autouse ``conftest.py`` fixture) can guarantee no
    cross-test cache leakage (TC-12)."""
    _VERIFIED_CACHE.clear()
    _META_CACHE.clear()
    _MERGED_CACHE.clear()
    _TYPED_MERGED_CACHE.clear()
    _DIR_LISTING_CACHE.clear()
    _PAIR_SCAN_CACHE.clear()


class BarStore:
    """File-based store rooted at the config-owned bar directory — the ONE reader/writer.

    Construction is cheap (no I/O); the directory is created on the first ``record``. Every read
    path (``get`` / ``list`` / ``load_bars``) goes through the same verified ``_load`` via the
    stat-keyed cache (``_cached_load``, era-fast_wall J-02) — a stat match serves an already
    fully-verified record with zero I/O; ANY stat mismatch re-runs ``_load`` in full, recomputing
    both checksums with no bypass (the ``DatasetStore`` pattern)."""

    def __init__(self, root: str | Path, *, verify_cache_db_path: str | None = None) -> None:
        self._root = Path(root)
        # Opt-in, exactly like ``DatasetStore``'s durable index: a store constructed without a path
        # behaves precisely as it did before the cache existed (in-process caching only), so every
        # test that builds a bare ``BarStore(tmp_path)`` keeps its from-scratch verification.
        self._verify_cache_db_path = verify_cache_db_path
        self._verify_cache: BarVerifyCache | None = None
        self._verify_cache_lock = threading.Lock()

    def _durable_verify_cache(self) -> BarVerifyCache | None:
        if self._verify_cache_db_path is None:
            return None
        if self._verify_cache is None:
            # Guarded because a store is shared across the top-up walk's threads: without it two
            # of them would open two connections to the same DB and one would be silently dropped.
            with self._verify_cache_lock:
                if self._verify_cache is None and self._verify_cache_db_path is not None:
                    try:
                        self._verify_cache = BarVerifyCache(self._verify_cache_db_path)
                    except sqlite3.Error:
                        # A derived cache that cannot be opened is a missing optimisation, never a
                        # failed read: fall through to full verification, exactly as if no path
                        # had been given.
                        self._verify_cache_db_path = None
        return self._verify_cache

    @property
    def verify_cache_db_path(self) -> str | None:
        """The durable verify-cache path this store was constructed with, if any — read-only, and
        exposed so a caller that must rebuild an equivalent store somewhere else (a screen worker
        process, which cannot receive the store object itself) wires the same cache rather than
        starting cold."""
        return self._verify_cache_db_path

    @property
    def root(self) -> Path:
        """The resolved root directory this store reads/writes (era-fast_wall J-02, TC-11) —
        public and read-only; no prior public accessor existed for this (only the private
        ``self._root``). Exposed so a future sibling-path consumer (e.g. a durable cache rooted
        beside the bar directory) can derive its own path without reaching into a private
        attribute."""
        return self._root

    # --- verified load (the one loader; no unverified path exists) ------------------------------

    def _path(self, bar_series_id: str) -> Path:
        return self._root / f"{bar_series_id}.json"

    def _load(self, path: Path) -> _LoadedBarSeries:
        """Load ONE bar-series file, verifying BOTH checksums. Raises ``BarSeriesIntegrityError``
        for any parse/shape/checksum failure — explicit, distinct, never silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise BarSeriesIntegrityError(
                f"bar series file '{path.name}' is not parseable ({exc}) — corrupted or tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise BarSeriesIntegrityError(
                f"bar series file '{path.name}' does not carry the expected record shape — "
                f"corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise BarSeriesIntegrityError(
                f"bar series file '{path.name}' failed its integrity check (file checksum "
                f"mismatch) — the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        rows = record.get("bars")
        if not isinstance(meta, dict) or not isinstance(rows, list):
            raise BarSeriesIntegrityError(
                f"bar series file '{path.name}' does not carry the expected record shape — "
                f"corrupted or tampered"
            )
        recomputed = _content_checksum(meta.get("symbol"), meta.get("timeframe"), meta.get("feed"), rows)
        if recomputed != meta.get("checksum"):
            raise BarSeriesIntegrityError(
                f"bar series file '{path.name}' failed its integrity check (content checksum "
                f"mismatch) — the file was corrupted or tampered with"
            )
        return _LoadedBarSeries(meta=meta, rows=rows)

    def _verified_load(self, path: Path, st: os.stat_result, key: str) -> _LoadedBarSeries:
        """``_load``, but skipping the two checksum recomputations when the durable cache already
        vouches for this file's exact ``(size, mtime_ns)``.

        The skipped work is not the hashing — that is ~0.35s of a 14.3s cold whole-store verify. It
        is the two ``json.dumps(sort_keys=True)`` canonicalizations the checksums hash, ~10.3s of
        that 14.3s. So a remembered file still has to be read and parsed to obtain its candles, but
        it does not have to be re-serialized twice to re-prove something a prior process already
        proved about these very bytes.

        The shape checks are NOT skipped: a file must still present ``record``/``meta``/``bars`` of
        the right types, so a remembered row can never turn a malformed file into a served series.
        Only the two content proofs are elided, and only behind an exact stat match — the same
        condition under which the in-process tier already serves a record without re-reading it at
        all."""
        durable = self._durable_verify_cache()
        if durable is None:
            return self._load(path)  # the full verifier — unchanged, never bypassed
        try:
            remembered = durable.lookup(key, st.st_size, st.st_mtime_ns)
        except sqlite3.Error:
            remembered = None
        if remembered is None:
            return self._load(path)

        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise BarSeriesIntegrityError(
                f"bar series file '{path.name}' is not parseable ({exc}) — corrupted or tampered"
            ) from exc
        record = data.get("record") if isinstance(data, dict) else None
        meta = record.get("meta") if isinstance(record, dict) else None
        rows = record.get("bars") if isinstance(record, dict) else None
        if not isinstance(meta, dict) or not isinstance(rows, list):
            raise BarSeriesIntegrityError(
                f"bar series file '{path.name}' does not carry the expected record shape — "
                f"corrupted or tampered"
            )
        return _LoadedBarSeries(meta=meta, rows=rows)

    def _cached_load(self, path: Path, st: os.stat_result | None = None) -> _LoadedBarSeries:
        """era-fast_wall J-02 — the stat-keyed cache-or-verify wrapper around ``_load``, consulted
        by every reader (``get``/``list``/``load_bars``, via ``_load_by_id`` and ``list`` below).
        A stat match (``st_size`` AND ``st_mtime_ns`` both unchanged since the cached publish)
        serves the already-verified record with ZERO additional I/O; any mismatch — including a
        first-ever read — re-runs the full ``_load`` verifier unchanged. An integrity error is
        NEVER cached (only a successful ``_load`` result is ever published), so a corrupted file
        re-verifies — and re-fails — on every subsequent call until it is fixed. A file whose
        mtime is within ``_RACY_WRITE_GUARD_SECONDS`` of "now" is never published (nor served from
        a stale earlier publish, since the mismatch check already forces a fresh verify) — the
        guard against a same-mtime-granularity rewrite being served stale.

        ``st``, when given, is the stat a directory scan (``_series_entries``) already read for this
        exact path — the same ``(st_size, st_mtime_ns)`` values a ``path.stat()`` here would return,
        so passing it only avoids a duplicate syscall and never changes which branch is taken."""
        if st is None:
            try:
                st = path.stat()
            except OSError:
                # Let the real loader raise its own explicit, typed error for a vanished/unreadable
                # file — the identical failure this call would have hit uncached.
                return self._load(path)

        key = str(path)
        cached = _VERIFIED_CACHE.get(key)  # read-local-reference-before-inspect
        if cached is not None and cached[0] == st.st_size and cached[1] == st.st_mtime_ns:
            return cached[2]

        loaded = self._verified_load(path, st, key)

        now_ns = time.time_ns()
        if (now_ns - st.st_mtime_ns) >= _RACY_WRITE_GUARD_SECONDS * 1_000_000_000:
            _VERIFIED_CACHE[key] = (st.st_size, st.st_mtime_ns, loaded)  # single atomic rebind
            _META_CACHE[key] = (st.st_size, st.st_mtime_ns, loaded.meta)
        return loaded

    def _pair_scan(self) -> tuple[list[tuple[Path, dict]], list[dict]]:
        """``_scan_meta``, memoized for as long as the store's directory holds the same entries —
        the enumeration ``_merged_entry`` uses purely to decide WHICH files a pair is made of.

        See ``_PAIR_SCAN_CACHE`` for why this is safe: the answer is a question about file identity,
        which an append-only store only changes by adding or removing files, and every file the fold
        goes on to read is still stat'd and re-verified individually."""
        key = str(self._root)
        try:
            dir_st = os.stat(key)
        except OSError:
            _PAIR_SCAN_CACHE.pop(key, None)
            return [], []
        cached = _PAIR_SCAN_CACHE.get(key)  # read-local-reference-before-inspect
        if cached is not None and cached[0] == dir_st.st_mtime_ns and cached[1] == dir_st.st_ctime_ns:
            return cached[2], [dict(row) for row in cached[3]]
        found, errors = self._scan_meta()
        _PAIR_SCAN_CACHE[key] = (dir_st.st_mtime_ns, dir_st.st_ctime_ns, found, errors)
        return found, [dict(row) for row in errors]

    def _scan_meta(self) -> tuple[list[tuple[Path, dict]], list[dict]]:
        """Every healthy series' verified METADATA under this store's root, in the same name-sorted
        order ``_series_entries`` yields, plus the same explicit error row per file that failed
        verification — the ONE whole-store enumeration ``list`` and ``_merged_entry`` share.

        Three layers per file, checked in order and mirroring ``DatasetStore._cached_meta``: the
        in-process ``_META_CACHE`` (a stat match serves already-verified metadata with zero I/O);
        the OPTIONAL durable ``BarVerifyCache``, read ONCE for the whole directory rather than per
        file; and the full ``_load`` verifier for anything neither layer can vouch for at this exact
        ``(size, mtime_ns)``. An integrity error is never cached at any layer, so a corrupt file
        re-verifies — and re-fails — on every call. Freshly verified rows are published to the
        durable cache in ONE transaction at the end, subject to the same
        ``_RACY_WRITE_GUARD_SECONDS`` rule that governs the in-process tiers.

        Metadata is all either caller needs to decide WHICH series exist and which belong to a pair;
        candles are then loaded only for the files that survive that decision (``_merged_entry``) or
        when the caller explicitly asks for them (``list(include_bars=True)``)."""
        entries = _series_entries(self._root)
        # One slot per file, filled in place, so the directory's own order survives the two-pass
        # split below without a second sort.
        slots: list[tuple[Path, dict] | None] = [None] * len(entries)
        pending: list[tuple[int, Path, str, os.stat_result]] = []
        for position, (path, key, st) in enumerate(entries):
            cached = _META_CACHE.get(key)  # read-local-reference-before-inspect
            if cached is not None and cached[0] == st.st_size and cached[1] == st.st_mtime_ns:
                slots[position] = (path, cached[2])
            else:
                pending.append((position, path, key, st))
        if not pending:
            return [slot for slot in slots if slot is not None], []

        # The durable cache is consulted ONLY when the in-process tier could not answer for some
        # file — so a warm process issues no query at all, and a cold one issues exactly one for the
        # whole directory.
        remembered: dict[str, tuple[int, int, str]] = {}
        durable = self._durable_verify_cache()
        if durable is not None:
            try:
                remembered = durable.lookup_all()
            except sqlite3.Error:
                remembered = {}  # a derived cache is an optimisation; never a read failure

        errors: list[dict] = []
        publish: list[tuple[str, int, int, dict]] = []
        now_ns = time.time_ns()
        guard_ns = _RACY_WRITE_GUARD_SECONDS * 1_000_000_000
        for position, path, key, st in pending:
            row = remembered.get(key)
            if row is not None and row[0] == st.st_size and row[1] == st.st_mtime_ns:
                meta = json.loads(row[2])
                if (now_ns - st.st_mtime_ns) >= guard_ns:
                    _META_CACHE[key] = (st.st_size, st.st_mtime_ns, meta)  # single atomic rebind
                slots[position] = (path, meta)
                continue
            try:
                loaded = self._cached_load(path, st)  # the full verifier — never bypassed
            except BarSeriesIntegrityError as exc:
                errors.append({"position": position, "file": path.name, "error": str(exc)})
                continue
            slots[position] = (path, loaded.meta)
            if (now_ns - st.st_mtime_ns) >= guard_ns:
                publish.append((key, st.st_size, st.st_mtime_ns, loaded.meta))

        if durable is not None and publish:
            try:
                durable.insert_many(publish)
            except sqlite3.Error:
                pass  # remembering is best-effort; the next read simply re-verifies
        errors.sort(key=lambda row: row.pop("position"))  # directory order, as a single scan gave
        return [slot for slot in slots if slot is not None], errors

    def _load_by_id(self, bar_series_id: str) -> _LoadedBarSeries:
        path = self._path(bar_series_id)
        if not path.exists():
            raise BarSeriesNotFound(f"no bar series with id '{bar_series_id}'")
        return self._cached_load(path)

    # --- reads -----------------------------------------------------------------------------------

    def get(self, bar_series_id: str, *, include_bars: bool = True) -> dict:
        """One bar series' metadata WITH its ordered OHLC candles embedded (verified load) — bar
        series are small by construction, so (unlike tick datasets) the candles are served
        directly rather than through a separate accessor. ``BarSeriesNotFound`` for an unknown id.
        era-fast_wall J-02: ``bars`` is a fresh list of fresh per-row dict COPIES on every call
        (never the cached list/dicts themselves), so a caller mutating the returned structure can
        never poison a later cached read (TC-6).

        ``include_bars=False`` serves the SAME verified metadata with the ``bars`` key OMITTED
        (never an empty list — an absent key is the honest "not asked for", distinguishable from a
        series that genuinely holds no candles) and skips the per-row copying entirely. The
        verification path is identical; only the projection differs. The default is unchanged, so
        every pre-existing caller sees byte-identical output."""
        loaded = self._load_by_id(bar_series_id)
        if not include_bars:
            return {**loaded.meta}
        return {**loaded.meta, "bars": [dict(row) for row in loaded.rows]}

    def list(self, *, include_bars: bool = True) -> tuple[list[dict], list[dict]]:
        """Every bar series' metadata + candles (each file verified), oldest first, plus an
        EXPLICIT error row per file that failed verification — a corrupt file is surfaced, never
        silently hidden and never served as data. era-fast_wall J-02: routed through the same
        stat-keyed cache as ``get`` (per-row copies here too — see ``get``'s docstring).

        ``include_bars=False`` omits the ``bars`` key from every record (see ``get``'s docstring for
        the omit-vs-empty-list rationale) — the same verified records, minus the candle payload and
        minus the per-row copying. Every file is still verified; nothing is skipped or approximated.
        The default is unchanged, so a no-param call is byte-identical to before."""
        if not self._root.exists():
            return [], []
        found, errors = self._scan_meta()
        records: list[dict] = []
        if not include_bars:
            records = [{**meta} for _path, meta in found]
        else:
            # The candle payload was explicitly asked for, so every series is loaded in full —
            # through the same verified load, with the metadata scan above having already settled
            # which files are healthy.
            for path, _meta in found:
                try:
                    loaded = self._cached_load(path)
                except BarSeriesIntegrityError as exc:
                    errors.append({"file": path.name, "error": str(exc)})
                    continue
                records.append({**loaded.meta, "bars": [dict(row) for row in loaded.rows]})
        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
        return records, errors

    def candles(
        self,
        bar_series_id: str,
        *,
        before_ts: float | None = None,
        after_ts: float | None = None,
        limit: int,
    ) -> tuple[list[dict], bool, bool]:
        """A bounded SLICE of one series' stored candles (verified load), plus the two
        "more exist outside this slice" flags — the accessor a viewport-sized chart pages through
        instead of pulling a whole series.

        Cursor semantics (both INCLUSIVE, so a cursor taken from a returned row re-returns that row
        and the caller de-duplicates by ``ts`` — never an off-by-one hole in the middle of a chart):

          * ``before_ts`` -> the LAST ``limit`` rows with ``ts <= before_ts``.
          * ``after_ts``  -> the FIRST ``limit`` rows with ``ts >= after_ts``.
          * neither       -> the LAST ``limit`` rows (the newest window).

        Passing BOTH is a caller error (``ValueError``) — the two anchor opposite ends and combining
        them would silently pick one. Rows are returned in STORED ORDER, verbatim (fresh per-row
        copies, exactly as ``get``); this method sorts, re-bins, gap-fills and rounds nothing.
        ``has_more_before`` / ``has_more_after`` report whether a stored row exists strictly outside
        the returned slice on that side — the honest "you can keep scrolling" signal (both ``False``
        for an empty series, since there is nothing more in either direction)."""
        return _slice_rows(
            self._load_by_id(bar_series_id).rows,
            before_ts=before_ts,
            after_ts=after_ts,
            limit=limit,
        )

    def merged_candles(
        self,
        symbol: str,
        timeframe: str,
        *,
        before_ts: float | None = None,
        after_ts: float | None = None,
        limit: int,
    ) -> tuple[list[dict], bool, bool, dict]:
        """The SAME bounded slice as ``candles``, but over EVERY recorded series for one
        (symbol, timeframe) folded into a single ascending candle series.

        Why this exists: a symbol accumulates many overlapping recorded windows (fetching AAPL twice
        over different date ranges writes two immutable series — the store never mutates one). A
        chart paging ONE of them can only ever show that window's history, so zooming out honestly
        runs out of bars while a longer recording of the very same symbol/timeframe sits on disk.
        This read is the display view over all of them; it never merges ACROSS symbols or
        timeframes, and it never invents a candle that no recorded series holds.

        The fold is a ts-keyed map, so a timestamp recorded by several series appears exactly ONCE.
        Where recordings of the same timestamp differ, the row from the MOST RECENTLY CREATED series
        wins — the ``(created_utc, id)`` tie-break. This is the ONE authority rule for "two series,
        one (symbol, timeframe)": ``merged_bars`` below serves the analytic readers from this exact
        fold, so a chart and the lines drawn over it can never disagree about which recording is
        authoritative. Differences are common and mostly benign (Yahoo re-derives split/dividend-
        adjusted prices per fetch, so an older recording differs in the 7th significant digit; a
        bar fetched mid-session is later superseded by its completed self) — serving the newest
        recording is the only rule
        that keeps a completed bar from being overwritten by a stale partial one. The COUNT of such
        timestamps is reported in the returned meta (``revised_timestamps``) rather than resolved
        out of sight: the merge is a choice, and the caller is told how often it was made.

        Returns ``(rows, has_more_before, has_more_after, meta)`` where ``meta`` carries
        ``series_ids`` (every contributing series, oldest-created first), ``bar_count`` (the merged
        total available, not the slice length), ``revised_timestamps``, and ``integrity_errors``
        (a corrupt file is surfaced exactly as ``list`` surfaces it — never served as data, never
        silently dropped from the merge; a recorded row carrying no finite price is surfaced the
        same way and excluded from the fold — see ``_merged_rows``)."""
        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip()
        merged, meta = self._merged_rows(normalized_symbol, normalized_timeframe)
        rows, has_more_before, has_more_after = _slice_rows(
            merged, before_ts=before_ts, after_ts=after_ts, limit=limit
        )
        return rows, has_more_before, has_more_after, meta

    def _merged_rows(self, symbol: str, timeframe: str) -> tuple[list[dict], dict]:
        """The fold behind ``merged_candles`` — see ``_merged_entry``, which this projects."""
        _key, merged, meta = self._merged_entry(symbol, timeframe)
        return merged, meta

    def _merged_entry(self, symbol: str, timeframe: str) -> tuple[tuple | None, list[dict], dict]:
        """The memoized fold behind ``merged_candles``. Returns the ascending merged rows (the
        cached list itself — every caller slices + copies before serving) plus the meta describing
        how it was built.

        Memo key: the exact set of contributing series AND their content checksums, so recording a
        new series, deleting one, or any content change produces a different key — a stale merge is
        not representable. Published with the SAME single-assignment discipline as
        ``_VERIFIED_CACHE`` above (see that block comment for the torn-read rationale). Nothing is
        cached when a file fails verification, since the error set is part of the answer.

        PRICELESS ROWS (era-desk-iter-4 audit B1). A recorded row whose OHLC are not all finite
        numbers carries no price at all, so it is excluded from the fold and reported in
        ``integrity_errors`` — the same treatment, through the same registered channel, that a
        corrupt FILE already gets ("never served as data, never silently dropped"). Excluding the
        ROW rather than the whole file is deliberate: the 60 series that were recorded before
        ``record``'s finite guard existed each hold ONE priceless row beside hundreds of real ones,
        and quarantining whole files would silently change every band and level those real bars
        support (measured: AAPL's support side moves). The files themselves are never touched — bar
        series are append-only and are never deleted, re-tagged, or content-perturbed — so the
        exclusion lives here, on the read that every chart and every analytic consumer shares. The
        per-series report is part of the MEMOIZED value (not of ``errors``), so the fold stays
        memoized for the affected pairs exactly as before.

        Returns the memo KEY alongside the fold (``None`` when nothing was cacheable — an
        unverifiable file makes the error set part of the answer), so ``merged_bars`` can memoize
        its own typed projection under the very same key rather than inventing a second identity
        for the same content."""
        if not self._root.exists():
            return None, [], {"series_ids": [], "bar_count": 0, "revised_timestamps": 0, "integrity_errors": []}

        # Which files belong to this pair is a METADATA question, so it is answered from the
        # metadata scan; only the files that actually contribute are then loaded with their candles.
        # Every file in the store is still stat-checked and, on any stat change, re-verified in
        # full — so a corrupt file anywhere is surfaced in ``integrity_errors`` here exactly as it
        # always was, whether or not it belongs to the pair being folded.
        found, errors = self._pair_scan()
        contributing: list[_LoadedBarSeries] = []
        for path, meta in found:
            if meta.get("symbol") != symbol or meta.get("timeframe") != timeframe:
                continue
            try:
                loaded = self._cached_load(path)
            except BarSeriesIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
                continue
            contributing.append(loaded)

        # Oldest-created first, so the LAST writer into the ts map is the most recently created
        # series -- the documented winner for a timestamp several recordings hold.
        contributing.sort(key=lambda s: (s.meta.get("created_utc", ""), s.meta.get("id", "")))
        key = (symbol, timeframe, tuple((s.meta.get("id"), s.meta.get("checksum")) for s in contributing))
        cached = _MERGED_CACHE.get(key)  # read-local-reference-before-inspect
        if cached is not None and not errors:
            return key, cached[0], {**cached[1], "integrity_errors": [dict(e) for e in cached[2]]}

        by_ts: dict[float, dict] = {}
        revised: set[float] = set()
        priceless: list[dict] = []
        for loaded in contributing:
            dropped = 0
            for row in loaded.rows:
                if not _has_finite_prices(row):
                    dropped += 1  # a row with no price is not a candle -- see the docstring
                    continue
                ts = row["ts"]
                previous = by_ts.get(ts)
                if previous is not None and previous != row:
                    revised.add(ts)
                by_ts[ts] = row
            if dropped:
                priceless.append({
                    "file": f"{loaded.meta.get('id')}.json",
                    "error": (
                        f"{dropped} recorded row(s) carry a non-finite price (no OHLC value at "
                        f"all) — excluded from the merged {symbol} {timeframe} series; the file "
                        f"itself is unchanged (bar series are append-only)"
                    ),
                })
        merged = [by_ts[ts] for ts in sorted(by_ts)]
        meta = {
            "series_ids": [s.meta.get("id") for s in contributing],
            "bar_count": len(merged),
            "revised_timestamps": len(revised),
        }
        if not errors:
            _MERGED_CACHE[key] = (merged, meta, priceless)  # single atomic rebind
        return (
            key if not errors else None,
            merged,
            {**meta, "integrity_errors": errors + [dict(e) for e in priceless]},
        )

    def load_bars(self, bar_series_id: str) -> list[RawBar]:
        """The stored candle series as typed ``RawBar`` records (verified load, exact stored
        order) — the accessor a per-series reader (e.g. ``GET /research/bars/{id}``) uses."""
        loaded = self._load_by_id(bar_series_id)
        symbol = loaded.meta["symbol"]
        timeframe = loaded.meta["timeframe"]
        return [_row_to_bar(symbol, timeframe, row) for row in loaded.rows]

    def merged_bars(self, symbol: str, timeframe: str) -> list[RawBar]:
        """EVERY recorded series for one (symbol, timeframe) folded into a single ascending
        ``RawBar`` list — the typed twin of ``merged_candles``, and the accessor every ANALYTIC
        consumer reads (``research/levels.py``, ``research/tradability.py``,
        ``research/setups.py``).

        Why this exists: a symbol accumulates many overlapping recorded windows (a second fetch
        over a wider range, or the deep-history leg that asks a second vendor for the part a
        vendor cap left unfetched — each recording is immutable, so both stay on file). Reading
        only ONE of them makes an analysis a function of which window happened to be recorded
        last rather than of the symbol's actual history: a 1-bar recording created after a
        250-bar one would freeze every level and every as-of basis to that single bar, while the
        CHART — which has always read the merged view — drew the full history underneath. This
        accessor is what keeps the two answering from the same bars.

        The fold, its timestamp de-duplication, and the "most recently created recording wins a
        contested timestamp" rule are ``_merged_rows``' (see ``merged_candles``' docstring) —
        this is a typed projection of that already-memoized result, never a second fold. Because
        recordings of one pair can come from DIFFERENT feeds (Yahoo re-derives split/dividend-
        adjusted prices per fetch; Alpaca SIP is a different tape), a merged series can carry
        rows whose prices differ in the last significant digits from a neighbouring recording's;
        that is the same trade-off the merged chart read has always made, and the newest-wins
        rule is what keeps a completed bar from being overwritten by a stale partial one.

        Returns ``[]`` for a (symbol, timeframe) with no healthy recorded series — an honest
        absence, exactly as ``list()`` reports one (a corrupt file is skipped by the shared
        verified load, never served as data).

        The typed projection is memoized under the fold's OWN key (``_TYPED_MERGED_CACHE``), so a
        pair read repeatedly — as a screened member's "1d" is, three times per member — builds its
        ``RawBar`` records once instead of once per read. The returned LIST is always fresh, so a
        caller sorting or truncating it in place can never poison a later read; the ``RawBar``
        records inside it are frozen dataclasses and therefore safe to share."""
        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip()
        key, rows, _meta = self._merged_entry(normalized_symbol, normalized_timeframe)
        if key is not None:
            cached = _TYPED_MERGED_CACHE.get(key)  # read-local-reference-before-inspect
            if cached is not None:
                return list(cached)
        typed = [_row_to_bar(normalized_symbol, normalized_timeframe, row) for row in rows]
        if key is not None:
            _TYPED_MERGED_CACHE[key] = typed  # single atomic rebind
        return list(typed)

    # --- the one mutation: record/register --------------------------------------------------------

    def record(
        self,
        *,
        symbol: str,
        timeframe: str,
        window_start_utc: str,
        window_end_utc: str,
        feed: str,
        bars: list[RawBar],
        vendor_limit: str | None = None,
    ) -> dict:
        """Persist ONE new bar series (record + register in a single explicit action). Content
        already registered raises the 409-style ``BarSeriesAlreadyRegistered`` (there is no
        update/re-record path at all — immutability is structural).

        COVERAGE (never inferred by a reader): ``covered_start_utc``/``covered_end_utc`` are the
        first and last bar's own timestamps, and ``vendor_limit`` is the caller-supplied sentence
        naming any vendor cap that shortened the fetch (``None`` when the request was served in
        full). Without these a recording whose window says ``2026-01-01..2026-07-21`` but which
        holds only the last 30 days is indistinguishable from a complete one — precisely the
        confusion that made a clamped intraday fetch look like a broken one. They live in ``meta``
        (never in the checksummed CONTENT identity, which stays symbol+timeframe+feed+rows), so a
        pre-existing file simply lacks them and every reader treats them as optional."""
        if not bars:
            raise EmptyBarWindowError("no bars in the requested window — nothing was recorded")
        rows = [_bar_to_row(bar) for bar in bars]
        # The priceless-bar rail (era-desk-iter-4 audit B1): a candle with no finite price is not a
        # candle, and this store is append-only — so the refusal has to happen BEFORE the write,
        # never as a later repair. Checked here rather than in each caller so it holds for every
        # write path (the /research/bars route, the desk top-up job, the CLI warmers, and anything
        # added later); the offending timestamp is named so the operator can see which row the
        # vendor served empty.
        for row in rows:
            if not _has_finite_prices(row):
                raise NonFiniteBarPriceError(
                    f"{symbol} {timeframe}: the bar at ts {row['ts']} carries a non-finite price "
                    f"(open={row['open']!r} high={row['high']!r} low={row['low']!r} "
                    f"close={row['close']!r}) — a bar with no price is not a bar, so nothing was "
                    f"recorded"
                )
        checksum = _content_checksum(symbol, timeframe, feed, rows)
        # Registration-time duplicate scan over the HEALTHY registry — the exact same series
        # content is never recorded twice. ``include_bars=False``: the scan compares ONLY
        # ``meta["checksum"]``, so copying every stored candle of every series (3.25M rows on the
        # live store, ~0.6s per write) buys nothing — the verified metadata this projection serves
        # is the same verified metadata, minus a payload no line below reads.
        existing, _errors = self.list(include_bars=False)
        for meta in existing:
            if meta["checksum"] == checksum:
                raise BarSeriesAlreadyRegistered(meta["id"], meta["symbol"], meta["timeframe"])
        meta = {
            "id": uuid.uuid4().hex,
            "symbol": symbol,
            "timeframe": timeframe,
            "window_start_utc": window_start_utc,
            "window_end_utc": window_end_utc,
            "feed": feed,
            "bar_count": len(rows),
            "checksum": checksum,
            "created_utc": _iso_utc(datetime.now(timezone.utc).timestamp()),
            # min/max rather than rows[0]/rows[-1]: coverage is a fact about the CONTENT, and must
            # not silently depend on an adapter having sorted its rows.
            "covered_start_utc": _iso_utc(min(row["ts"] for row in rows)),
            "covered_end_utc": _iso_utc(max(row["ts"] for row in rows)),
            "vendor_limit": vendor_limit,
        }
        record = {"meta": meta, "bars": rows}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        # Written to a sibling temp file and renamed into place: ``os.replace`` is atomic within a
        # directory, so a concurrent reader — a parallel top-up thread, or a screen worker process
        # scanning the same store — observes the file either absent or complete, never as the
        # half-flushed prefix a plain ``write_text`` can expose. The temp name is prefixed so a
        # crash between write and rename leaves an obvious, ignorable artifact rather than
        # something ``_series_entries`` would mistake for a series (it matches ``*.json`` only
        # after the rename).
        final = self._path(meta["id"])
        staging = self._root / f".{meta['id']}.json.partial"
        staging.write_text(json.dumps(payload))
        os.replace(staging, final)
        # Belt-and-braces beside the directory mtime the rename just bumped: an explicit eviction
        # makes an in-process write visible to the very next read regardless of any clock's
        # resolution.
        _DIR_LISTING_CACHE.pop(str(self._root), None)
        _PAIR_SCAN_CACHE.pop(str(self._root), None)
        return {**meta, "bars": rows}
