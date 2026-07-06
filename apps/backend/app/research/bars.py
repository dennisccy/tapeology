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
  * **Checksummed + verified on EVERY load.** ``meta.checksum`` is a sha256 over the bar-series
    CONTENT (symbol + timeframe + feed + the ordered candles) computed at registration; a second
    whole-record checksum covers every metadata byte. Both are recomputed on every load — a
    corrupted or tampered file raises the explicit ``BarSeriesIntegrityError``, never silence,
    never a fabricated series.
  * **Immutable — structurally.** No update/delete function exists anywhere in this module
    (immutability is structural, not policed). The only mutation is ``record``, and it REFUSES
    content that is already registered: re-recording the same series raises the 409-style
    ``BarSeriesAlreadyRegistered`` naming the existing series.
  * **Candles served embedded.** Unlike tick-level datasets (whose events are large and served only
    through a separate loader), a bar series is small by construction, so ``get``/``list`` embed the
    ordered OHLC candles directly on the served dict (the phase spec's explicit requirement) while
    the on-disk shape still separates ``meta`` from ``bars`` for the same checksum discipline.
  * **Honest failure states.** Unknown id -> ``BarSeriesNotFound``; an empty fetched window ->
    ``EmptyBarWindowError`` (nothing written, nothing fabricated).
"""

from __future__ import annotations

import hashlib
import json
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


class BarStore:
    """File-based store rooted at the config-owned bar directory — the ONE reader/writer.

    Construction is cheap (no I/O); the directory is created on the first ``record``. Every read
    path (``get`` / ``list`` / ``load_bars``) goes through the same verified ``_load`` — the
    checksum is recomputed on EVERY load, with no bypass (the ``DatasetStore`` pattern)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

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

    def _load_by_id(self, bar_series_id: str) -> _LoadedBarSeries:
        path = self._path(bar_series_id)
        if not path.exists():
            raise BarSeriesNotFound(f"no bar series with id '{bar_series_id}'")
        return self._load(path)

    # --- reads -----------------------------------------------------------------------------------

    def get(self, bar_series_id: str) -> dict:
        """One bar series' metadata WITH its ordered OHLC candles embedded (verified load) — bar
        series are small by construction, so (unlike tick datasets) the candles are served
        directly rather than through a separate accessor. ``BarSeriesNotFound`` for an unknown id."""
        loaded = self._load_by_id(bar_series_id)
        return {**loaded.meta, "bars": list(loaded.rows)}

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every bar series' metadata + candles (each file verified), oldest first, plus an
        EXPLICIT error row per file that failed verification — a corrupt file is surfaced, never
        silently hidden and never served as data."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                loaded = self._load(path)
                records.append({**loaded.meta, "bars": list(loaded.rows)})
            except BarSeriesIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
        return records, errors

    def load_bars(self, bar_series_id: str) -> list[RawBar]:
        """The stored candle series as typed ``RawBar`` records (verified load, exact stored
        order) — the accessor a later level-detection consumer reads."""
        loaded = self._load_by_id(bar_series_id)
        symbol = loaded.meta["symbol"]
        timeframe = loaded.meta["timeframe"]
        return [_row_to_bar(symbol, timeframe, row) for row in loaded.rows]

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
    ) -> dict:
        """Persist ONE new bar series (record + register in a single explicit action). Content
        already registered raises the 409-style ``BarSeriesAlreadyRegistered`` (there is no
        update/re-record path at all — immutability is structural)."""
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
        }
        record = {"meta": meta, "bars": rows}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(meta["id"]).write_text(json.dumps(payload))
        return {**meta, "bars": rows}
