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
    ``EmptyBarWindowError`` (nothing written, nothing fabricated).
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..providers.adapters.base import RawBar


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

# A file whose mtime is within this many seconds of "now" (at read time) is never published to the
# cache — the guard against a same-granularity rewrite being served stale (two writes landing
# within one mtime-resolution tick could otherwise be indistinguishable by stat alone).
_RACY_WRITE_GUARD_SECONDS = 2.0


# The merged-view memo behind ``BarStore.merged_candles``: key = (symbol, timeframe, the exact set of
# contributing (series_id, content-checksum) pairs); value = (ascending merged rows, meta). Same
# atomic single-key-assignment publish discipline as ``_VERIFIED_CACHE`` above. Because the key
# names every contributing series AND its content checksum, ANY change to the recorded set (a new
# fetch, a deleted file, a changed file) yields a different key -- a stale merge cannot be served.
_MERGED_CACHE: dict[tuple, tuple[list[dict], dict]] = {}


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


def _reset_verified_cache_for_tests() -> None:
    """Test-only: clears the module-level verified-record cache. Never called from any production
    code path — exists solely so tests (and the autouse ``conftest.py`` fixture) can guarantee no
    cross-test cache leakage (TC-12)."""
    _VERIFIED_CACHE.clear()
    _MERGED_CACHE.clear()


class BarStore:
    """File-based store rooted at the config-owned bar directory — the ONE reader/writer.

    Construction is cheap (no I/O); the directory is created on the first ``record``. Every read
    path (``get`` / ``list`` / ``load_bars``) goes through the same verified ``_load`` via the
    stat-keyed cache (``_cached_load``, era-fast_wall J-02) — a stat match serves an already
    fully-verified record with zero I/O; ANY stat mismatch re-runs ``_load`` in full, recomputing
    both checksums with no bypass (the ``DatasetStore`` pattern)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

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

    def _cached_load(self, path: Path) -> _LoadedBarSeries:
        """era-fast_wall J-02 — the stat-keyed cache-or-verify wrapper around ``_load``, consulted
        by every reader (``get``/``list``/``load_bars``, via ``_load_by_id`` and ``list`` below).
        A stat match (``st_size`` AND ``st_mtime_ns`` both unchanged since the cached publish)
        serves the already-verified record with ZERO additional I/O; any mismatch — including a
        first-ever read — re-runs the full ``_load`` verifier unchanged. An integrity error is
        NEVER cached (only a successful ``_load`` result is ever published), so a corrupted file
        re-verifies — and re-fails — on every subsequent call until it is fixed. A file whose
        mtime is within ``_RACY_WRITE_GUARD_SECONDS`` of "now" is never published (nor served from
        a stale earlier publish, since the mismatch check already forces a fresh verify) — the
        guard against a same-mtime-granularity rewrite being served stale."""
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

        loaded = self._load(path)  # the full verifier — unchanged, never bypassed

        now_ns = time.time_ns()
        if (now_ns - st.st_mtime_ns) >= _RACY_WRITE_GUARD_SECONDS * 1_000_000_000:
            _VERIFIED_CACHE[key] = (st.st_size, st.st_mtime_ns, loaded)  # single atomic rebind
        return loaded

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
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                loaded = self._cached_load(path)
                if include_bars:
                    records.append({**loaded.meta, "bars": [dict(row) for row in loaded.rows]})
                else:
                    records.append({**loaded.meta})
            except BarSeriesIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
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
        silently dropped from the merge)."""
        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip()
        merged, meta = self._merged_rows(normalized_symbol, normalized_timeframe)
        rows, has_more_before, has_more_after = _slice_rows(
            merged, before_ts=before_ts, after_ts=after_ts, limit=limit
        )
        return rows, has_more_before, has_more_after, meta

    def _merged_rows(self, symbol: str, timeframe: str) -> tuple[list[dict], dict]:
        """The memoized fold behind ``merged_candles``. Returns the ascending merged rows (the
        cached list itself — every caller slices + copies before serving) plus the meta describing
        how it was built.

        Memo key: the exact set of contributing series AND their content checksums, so recording a
        new series, deleting one, or any content change produces a different key — a stale merge is
        not representable. Published with the SAME single-assignment discipline as
        ``_VERIFIED_CACHE`` above (see that block comment for the torn-read rationale). Nothing is
        cached when a file fails verification, since the error set is part of the answer."""
        if not self._root.exists():
            return [], {"series_ids": [], "bar_count": 0, "revised_timestamps": 0, "integrity_errors": []}

        contributing: list[_LoadedBarSeries] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                loaded = self._cached_load(path)
            except BarSeriesIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
                continue
            if loaded.meta.get("symbol") == symbol and loaded.meta.get("timeframe") == timeframe:
                contributing.append(loaded)

        # Oldest-created first, so the LAST writer into the ts map is the most recently created
        # series -- the documented winner for a timestamp several recordings hold.
        contributing.sort(key=lambda s: (s.meta.get("created_utc", ""), s.meta.get("id", "")))
        key = (symbol, timeframe, tuple((s.meta.get("id"), s.meta.get("checksum")) for s in contributing))
        cached = _MERGED_CACHE.get(key)  # read-local-reference-before-inspect
        if cached is not None and not errors:
            return cached[0], {**cached[1], "integrity_errors": []}

        by_ts: dict[float, dict] = {}
        revised: set[float] = set()
        for loaded in contributing:
            for row in loaded.rows:
                ts = row["ts"]
                previous = by_ts.get(ts)
                if previous is not None and previous != row:
                    revised.add(ts)
                by_ts[ts] = row
        merged = [by_ts[ts] for ts in sorted(by_ts)]
        meta = {
            "series_ids": [s.meta.get("id") for s in contributing],
            "bar_count": len(merged),
            "revised_timestamps": len(revised),
        }
        if not errors:
            _MERGED_CACHE[key] = (merged, meta)  # single atomic rebind
        return merged, {**meta, "integrity_errors": errors}

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
        verified load, never served as data)."""
        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip()
        rows, _meta = self._merged_rows(normalized_symbol, normalized_timeframe)
        return [_row_to_bar(normalized_symbol, normalized_timeframe, row) for row in rows]

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
        checksum = _content_checksum(symbol, timeframe, feed, rows)
        # Registration-time duplicate scan over the HEALTHY registry — the exact same series
        # content is never recorded twice.
        existing, _errors = self.list()
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
        self._path(meta["id"]).write_text(json.dumps(payload))
        return {**meta, "bars": rows}
