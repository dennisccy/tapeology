"""The historical tape dataset store (era-3 capability 1, J-02) — Data Contract row 30's ONE owner.

THIS MODULE is the only code that reads or writes dataset files. A dataset is an IMMUTABLE
recording of one historical trade/quote stream: the provider-neutral engine events
(``TradeEvent`` / ``QuoteEvent`` fields — never raw vendor payloads) plus metadata (id, symbol,
UTC window, ``data_feed``, event counts, content checksum, the frozen ``train | holdout`` split
tag, the epoch anchor, and a created timestamp). Files live under the config-owned dataset
directory (``TAPEOLOGY_DATASET_DIR`` override, ``config.dataset_dir`` default — gitignored via
``.data/``), one JSON file per dataset.

Disciplines (each an anti-goal or a J-02 acceptance clause):

  * **Explicit recording only.** Recording is a research ACTION through ``record_from_source``
    (the same source resolution studies use: the committed keyless reference window, or an
    arbitrary window through the EXISTING adapter fetch seam). Nothing in the watch/stream path
    imports this module — the live cockpit's tape is never persisted (no ambient recording).
  * **Checksummed + verified on EVERY load.** ``meta.checksum`` is a sha256 over the tape
    CONTENT (symbol + feed + anchor + events) computed at registration; a second whole-record
    checksum covers every metadata byte INCLUDING the split tag. Both are recomputed on every
    load — a corrupted or tampered file (even a hand-edited split) raises the explicit
    ``DatasetIntegrityError``, never silence, never a fabricated dataset.
  * **The split tag is frozen at registration — structurally.** No update/re-tag/delete function
    exists anywhere in this module (immutability is structural, not policed). The only mutation
    is ``record``, and it REFUSES content that is already registered: re-recording the same tape
    under a different split (the re-tag attempt) — or the same split — raises the 409-style
    ``DatasetAlreadyRegistered`` naming the existing dataset and its frozen tag.
  * **Byte-identical replay.** ``DatasetStore.replay`` replays a stored dataset UNPACED through
    a FRESH ``TapeEngine`` (the studies-runner pattern), yielding snapshots byte-identical to
    replaying the original source stream, deterministic across re-runs. Consumed by tests now
    and by J-03's backtester next — there is no REST replay endpoint (Product Shape lists none).
  * **Honest failure states.** Unknown id -> ``DatasetNotFound``; an empty requested window ->
    ``EmptyWindowError`` (nothing written); an unavailable reference fixture ->
    ``DatasetRecordError``. Every error is distinct and explicit.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from ..config import Config
from ..engine.snapshot import EngineSnapshot
from ..engine.tape_engine import TapeEngine
from ..providers.adapters.base import HistoricalWindow
from ..providers.base import Event, QuoteEvent, Side, TradeEvent
from ..providers.historical import HistoricalProvider
from .feed_basis import data_feed_for_scenario

# The dataset source vocabulary REUSES the studies module's source-resolution names (one owner
# per literal — never a second copy), and the reference loader below reuses its one committed
# fixture loader. Datasets are HISTORICAL tape: the committed keyless reference window, or an
# arbitrary real window through the EXISTING adapter fetch seam. A seeded sim stream reproduces
# on demand, so ``sim`` is deliberately NOT a dataset source kind.
from .studies import SOURCE_HISTORICAL, SOURCE_REFERENCE
from .studies import _load_reference_window as _load_reference

# The frozen split vocabulary (assigned at registration, immutable forever after).
SPLIT_TRAIN = "train"
SPLIT_HOLDOUT = "holdout"
VALID_SPLITS = frozenset({SPLIT_TRAIN, SPLIT_HOLDOUT})

VALID_SOURCE_KINDS = frozenset({SOURCE_REFERENCE, SOURCE_HISTORICAL})

# Stored event-row type tags (one explicit copy each).
_ROW_TRADE = "trade"
_ROW_QUOTE = "quote"


class DatasetNotFound(Exception):
    """No dataset file exists for the requested id (the route maps this to a 404)."""


class DatasetIntegrityError(Exception):
    """A dataset file failed its on-load verification — corrupted or tampered, surfaced
    explicitly (never silence, never a fabricated dataset)."""


class DatasetAlreadyRegistered(Exception):
    """The exact tape content is already registered. Split tags are frozen at registration, so
    re-recording it — under ANY split — is the 409-style re-tag refusal."""

    def __init__(self, existing_id: str, existing_split: str, requested_split: str) -> None:
        self.existing_id = existing_id
        self.existing_split = existing_split
        self.requested_split = requested_split
        if requested_split != existing_split:
            detail = (
                f"this exact tape is already registered as dataset '{existing_id}' with split "
                f"'{existing_split}' — split tags are frozen at registration, so re-tagging it "
                f"'{requested_split}' is refused"
            )
        else:
            detail = (
                f"this exact tape is already registered as dataset '{existing_id}' (split "
                f"'{existing_split}' — frozen at registration); datasets are immutable and are "
                f"never re-recorded"
            )
        super().__init__(detail)


class EmptyWindowError(Exception):
    """The requested window contains no events — an explicit refusal; nothing is written and
    nothing is fabricated."""


class DatasetRecordError(Exception):
    """A record request could not be served (e.g. the committed reference window is
    unavailable) — explicit, never fixture-substituted."""


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc(epoch: float) -> str:
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _event_to_row(event: Event) -> dict:
    """One provider-neutral stored row per engine event (TradeEvent/QuoteEvent fields only —
    never a vendor payload). The dataset-level ``symbol`` owns the ticker; rows do not repeat it."""
    if isinstance(event, TradeEvent):
        return {
            "type": _ROW_TRADE,
            "ts": event.timestamp,
            "price": event.price,
            "size": event.size,
            "side": event.side.value,
        }
    return {
        "type": _ROW_QUOTE,
        "ts": event.timestamp,
        "bid": event.bid,
        "ask": event.ask,
        "bid_size": event.bid_size,
        "ask_size": event.ask_size,
    }


def _row_to_event(symbol: str, row: dict) -> Event:
    if row["type"] == _ROW_TRADE:
        return TradeEvent(symbol, row["ts"], row["price"], row["size"], Side(row["side"]))
    if row["type"] == _ROW_QUOTE:
        return QuoteEvent(symbol, row["ts"], row["bid"], row["ask"], row["bid_size"], row["ask_size"])
    raise DatasetIntegrityError(f"unknown stored event type {row.get('type')!r}")


def _content_checksum(symbol: str, data_feed: str, epoch_anchor: float | None, rows: list[dict]) -> str:
    """The dataset's CONTENT identity: a sha256 over the tape itself (symbol + feed + anchor +
    the ordered event rows). Registration-time duplicate detection and the on-load verification
    both recompute exactly this."""
    return _sha256(
        _canonical(
            {"symbol": symbol, "data_feed": data_feed, "epoch_anchor": epoch_anchor, "events": rows}
        )
    )


@dataclass(frozen=True)
class _LoadedDataset:
    """One verified load: the served metadata plus the stored event rows."""

    meta: dict
    rows: list[dict]


class DatasetStore:
    """File-based store rooted at the config-owned dataset directory — the ONE reader/writer.

    Construction is cheap (no I/O); the directory is created on the first ``record``. Every read
    path (``get`` / ``list`` / ``load_events`` / ``replay``) goes through the same verified
    ``_load`` — the checksum is recomputed on EVERY load, with no bypass."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    # --- verified load (the one loader; no unverified path exists) ------------------------------

    def _path(self, dataset_id: str) -> Path:
        return self._root / f"{dataset_id}.json"

    def _load(self, path: Path) -> _LoadedDataset:
        """Load ONE dataset file, verifying BOTH checksums. Raises ``DatasetIntegrityError`` for
        any parse/shape/checksum failure — explicit, distinct, never silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise DatasetIntegrityError(
                f"dataset file '{path.name}' is not parseable ({exc}) — corrupted or tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise DatasetIntegrityError(
                f"dataset file '{path.name}' does not carry the expected record shape — "
                f"corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise DatasetIntegrityError(
                f"dataset file '{path.name}' failed its integrity check (file checksum "
                f"mismatch) — the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        rows = record.get("events")
        if not isinstance(meta, dict) or not isinstance(rows, list):
            raise DatasetIntegrityError(
                f"dataset file '{path.name}' does not carry the expected record shape — "
                f"corrupted or tampered"
            )
        recomputed = _content_checksum(
            meta.get("symbol"), meta.get("data_feed"), meta.get("epoch_anchor"), rows
        )
        if recomputed != meta.get("checksum"):
            raise DatasetIntegrityError(
                f"dataset file '{path.name}' failed its integrity check (content checksum "
                f"mismatch) — the file was corrupted or tampered with"
            )
        return _LoadedDataset(meta=meta, rows=rows)

    def _load_by_id(self, dataset_id: str) -> _LoadedDataset:
        path = self._path(dataset_id)
        if not path.exists():
            raise DatasetNotFound(f"no dataset with id '{dataset_id}'")
        return self._load(path)

    # --- reads -----------------------------------------------------------------------------------

    def get(self, dataset_id: str) -> dict:
        """One dataset's metadata (verified load). ``DatasetNotFound`` for an unknown id."""
        return dict(self._load_by_id(dataset_id).meta)

    def list(self) -> tuple[list[dict], list[dict]]:
        """All datasets' metadata (each file verified), oldest first, plus an EXPLICIT error row
        per file that failed verification — a corrupt file is surfaced, never silently hidden and
        never served as data."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                records.append(dict(self._load(path).meta))
            except DatasetIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
        return records, errors

    def load_events(self, dataset_id: str) -> list[Event]:
        """The stored event stream as engine events (verified load, exact stored order)."""
        loaded = self._load_by_id(dataset_id)
        symbol = loaded.meta["symbol"]
        return [_row_to_event(symbol, row) for row in loaded.rows]

    def replay(self, dataset_id: str, config: Config) -> Iterator[EngineSnapshot]:
        """Replay the stored dataset UNPACED through a FRESH ``TapeEngine`` (the studies-runner
        pattern), yielding every per-event snapshot. Deterministic: the stored stream, the stored
        source descriptor, and the stored epoch anchor fully determine the output — re-runs are
        byte-identical, and both match replaying the original source stream."""
        loaded = self._load_by_id(dataset_id)
        meta = loaded.meta
        engine = TapeEngine(
            meta["symbol"], meta["source"], config, epoch_anchor=meta["epoch_anchor"]
        )
        for row in loaded.rows:
            yield engine.process_event(_row_to_event(meta["symbol"], row))

    # --- the one mutation: record/register --------------------------------------------------------

    def record(
        self,
        *,
        symbol: str,
        source: str,
        source_kind: str,
        source_id: str,
        split: str,
        window_start_utc: str,
        window_end_utc: str,
        data_feed: str,
        epoch_anchor: float | None,
        events: list[Event],
    ) -> dict:
        """Persist ONE new dataset (record + register in a single explicit action). The split tag
        is assigned HERE and frozen: content already registered under any split raises the
        409-style ``DatasetAlreadyRegistered`` (there is no update/re-tag/delete path at all)."""
        if split not in VALID_SPLITS:
            raise ValueError(f"unknown split {split!r} — expected one of {sorted(VALID_SPLITS)}")
        if not events:
            raise EmptyWindowError("no events in the requested window — nothing was recorded")
        rows = [_event_to_row(event) for event in events]
        checksum = _content_checksum(symbol, data_feed, epoch_anchor, rows)
        # Registration-time duplicate scan over the HEALTHY registry: the same content under a
        # different split is a re-tag attempt; under the same split it is an immutable re-record.
        existing, _errors = self.list()
        for meta in existing:
            if meta["checksum"] == checksum:
                raise DatasetAlreadyRegistered(meta["id"], meta["split"], split)
        trade_count = sum(1 for row in rows if row["type"] == _ROW_TRADE)
        meta = {
            "id": uuid.uuid4().hex,
            "symbol": symbol,
            "window_start_utc": window_start_utc,
            "window_end_utc": window_end_utc,
            "data_feed": data_feed,
            "event_counts": {
                "trades": trade_count,
                "quotes": len(rows) - trade_count,
                "total": len(rows),
            },
            "checksum": checksum,
            "split": split,
            "source": source,
            "source_kind": source_kind,
            "source_id": source_id,
            "epoch_anchor": epoch_anchor,
            "created_utc": _iso_utc(datetime.now(timezone.utc).timestamp()),
        }
        record = {"meta": meta, "events": rows}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(meta["id"]).write_text(json.dumps(payload))
        return dict(meta)


# --- source resolution + record (the explicit research action) ------------------------------------


def _slice_window(window: HistoricalWindow, start_epoch: float | None, end_epoch: float | None) -> HistoricalWindow:
    """The half-open ``[start, end)`` epoch slice of a source window — pure selection of REAL
    records (nothing fabricated, dropped beyond the bounds, or reordered)."""
    if start_epoch is None and end_epoch is None:
        return window

    def _keep(epoch: float) -> bool:
        if start_epoch is not None and epoch < start_epoch:
            return False
        if end_epoch is not None and epoch >= end_epoch:
            return False
        return True

    return HistoricalWindow(
        window.symbol,
        tuple(t for t in window.trades if _keep(t.epoch)),
        tuple(q for q in window.quotes if _keep(q.epoch)),
    )


def record_from_source(
    store: DatasetStore,
    *,
    source_kind: str,
    source_id: str = "",
    split: str,
    start: str | None = None,
    end: str | None = None,
    config: Config,
    historical_fetch: Callable[[], HistoricalWindow] | None = None,
) -> dict:
    """Record + register ONE dataset from a historical source (the explicit research action).

    Source resolution mirrors the studies runner: ``reference`` loads the committed keyless PG
    SIP fixture (optionally sliced to ``[start, end)``); ``historical`` calls the injected
    ``historical_fetch`` built on the EXISTING neutral adapter seam (credentials / no-data /
    timeouts surface that seam's explicit errors — never fabricated, never fixture-substituted).
    The stream is materialised through the SAME ``HistoricalProvider`` the watch and studies
    paths replay, so the stored events ARE the source stream, byte for byte."""
    if source_kind == SOURCE_REFERENCE:
        window = _load_reference()
        if window is None or (not window.trades and not window.quotes):
            raise DatasetRecordError("the committed reference window is unavailable")
    elif source_kind == SOURCE_HISTORICAL:
        if historical_fetch is None:
            raise DatasetRecordError("no historical fetch available for this record request")
        window = historical_fetch()  # existing seam errors propagate explicitly
    else:
        raise ValueError(f"unknown source_kind {source_kind!r}")

    start_epoch = parse_utc_epoch(start) if start is not None else None
    end_epoch = parse_utc_epoch(end) if end is not None else None
    sliced = _slice_window(window, start_epoch, end_epoch)
    if not sliced.trades and not sliced.quotes:
        raise EmptyWindowError("no events in the requested window — nothing was recorded")

    scenario = f"historical {sliced.symbol} dataset"
    provider = HistoricalProvider(sliced.symbol, sliced, scenario)
    events = list(provider.stream())
    epochs = [t.epoch for t in sliced.trades] + [q.epoch for q in sliced.quotes]
    window_start = start if start is not None else _iso_utc(min(epochs))
    window_end = end if end is not None else _iso_utc(max(epochs))
    return store.record(
        symbol=sliced.symbol,
        source=scenario,
        source_kind=source_kind,
        source_id=source_id,
        split=split,
        window_start_utc=window_start,
        window_end_utc=window_end,
        data_feed=data_feed_for_scenario(scenario, config),
        epoch_anchor=provider.epoch_anchor,
        events=events,
    )


def parse_utc_epoch(value: str) -> float:
    """ISO-8601 (``Z`` accepted) -> UTC epoch seconds; a naive value is taken as UTC (the studies
    window-parse convention). Raises ``ValueError`` for a malformed value (the route maps it to
    an explicit 422)."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()
