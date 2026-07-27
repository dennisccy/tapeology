"""The screen: pinned inputs, append-only snapshot, deterministic rank (Era B "The Desk", Key
Capability 3, J-03) -- the Data Contract's "Screen snapshots, rank rows, skip rows" row's ONE
owner, served by ``GET /research/desk/screen``.

THIS MODULE computes NOTHING about tradable structure itself -- it is a pure ORCHESTRATION lens
over three already-canonical owners: ``compute_tradability`` (``tradability.py:381`` -- bands,
class, quality score, verbatim), ``desk_coverage.get_desk_coverage`` (per-member coverage badge,
verbatim reuse -- also the source of ``bar_store_signature``, see below), and ``DatasetStore.list``
(tick-evidence presence, verbatim). Two new desk-owned values are computed HERE and only here:
``distance_bps`` (a plain arithmetic derivation from a band's own edge price and a reference close
this module resolves) and the cross-symbol rank order.

**The append-only store** (``ScreenStore``) mirrors ``desk_universe.UniverseStore``'s discipline
exactly: a checksum-verified load on every read, ``record`` as the only mutation, no update/delete
function anywhere (immutability is structural, not policed). UNLIKE the universe store (which dedups
on parsed CONTENT), a screen dedups on its own 5-pin KEY -- ``(screen_date, as_of,
universe_snapshot_id, config_fingerprint, bar_store_signature)`` -- because the key alone
deterministically determines the content (the row computation is a pure function of those five
pins), so keying on the pins is equivalent to keying on content while being resolvable BEFORE the
(potentially ~100-member) walk ever runs.

**``as_of`` translation (T-6, goal-desk-iter-3 NOTES).** ``as_of`` is a deterministic function of
the operator-given ``screen_date`` alone -- ``f"{screen_date}T23:59:59Z"`` -- reusing ``/structure``'s
own plain-date convention rather than inventing a new one. ``compute_tradability``'s basis
resolution is a CALENDAR-DATE comparison, so any ``as_of`` inside ``screen_date``'s own UTC day
resolves the identical prior-session basis -- never ``datetime.now()``.

**``bar_store_signature`` (T-4, TC-15).** A checksum over the sorted ``(symbol, timeframe,
latest_window_end_utc)`` tuples read ENTIRELY from ``desk_coverage.get_desk_coverage``'s own
per-member x per-timeframe output (already ``bar_index``-backed, already proven index-fast in J-02)
-- never a ``BarStore``/JSON-file re-hash (the era-5C 31.4s mistake T-4 exists to prevent).
``_bar_store_signature`` below takes the ALREADY-fetched coverage payload and touches no store at
all, so it is structurally incapable of issuing a ``BarStore`` call.

**Reference close price (TC-19).** ``compute_tradability``/``compute_levels`` serve no
``current_price``/close field (adding one would break their existing exact-dict-equality tests --
a "Frozen foundations" violation), so this module resolves it itself: the ONE daily bar in
``BarStore.merged_bars(symbol, "1d")`` whose OWN timestamp matches ``basis_as_of`` verbatim (a
value ``compute_tradability`` already returns) -- comparing via the SAME ISO-formatting function on
both sides (never parsing ``basis_as_of`` back to a float, which would risk a microsecond
round-trip mismatch). Never re-deriving WHICH bar is the basis; never touching ``tradability.py``'s
or ``levels.py``'s return shape.

**Best-band selection + cross-symbol rank (assumptions.md iter-3, entry 1).** Per symbol, the
"best" band minimizes ``(class rank A=3/B=2/C=1/null=0 -- DESCENDING preference, distance_bps
ascending, quality_score descending)``, iterating ``compute_tradability``'s own already-deterministic
served band order so an exact tie resolves identically every run (Python's ``min`` keeps the FIRST
of equal-key items). The SAME tuple, plus ``symbol`` ascending as the final tie-break, orders the
screen's final ``rows`` list (TC-14) -- one rule serves both jobs.

**Skip reasons -- exactly two, never conflated.** ``"no_bars"`` = ``compute_tradability``'s own
``no_bar_series_for_symbol: true``; ``"no_basis"`` = a daily series exists but no session resolves
(``basis_as_of: null``, ``bands: []``). Both honest, distinct absences -- a skip row's ``coverage``
still reflects whichever pinned timeframes genuinely have bars (never a fabricated all-false).

**Basis disclosure (goal-desk-iter-9, J-08).** Every RANKED row also carries ``basis_as_of``
(copied VERBATIM from ``result["basis_as_of"]`` -- the SAME value ``_resolve_reference_close``
already consumes to find the reference close, so this costs zero additional
``BarStore``/``compute_tradability`` work) and ``basis_age_days`` (a plain calendar-date
difference between that value and the row's own ``as_of``, mirroring ``_distance_bps``'s "plain
arithmetic derivation" style -- see ``_basis_age_days`` below). Skip rows never carry these fields
-- a skip row's own ``reason`` already means no basis resolved at all. A snapshot recorded BEFORE
this addition simply has ranked rows that OMIT these two keys entirely; ``ScreenStore`` performs no
row-shape validation or enrichment (a plain checksum-verified passthrough), so
``GET /research/desk/screen`` serves that absence VERBATIM -- never defaulted, never backfilled
(the append-only rail applies to row CONTENT, not just to the snapshot as a whole).

**No new ``Config`` field.** The screen store's directory resolves via ``resolve_desk_screen_dir``
below -- a bare ``TAPEOLOGY_DESK_SCREEN_DIR``-env-var-or-sibling-of-``desk_universe_dir_resolved()``
default (the ``edge_report_cache.resolve_cache_db_path`` pattern) -- never a ``desk_screen_dir``
``Config`` field. This keeps ``config_fingerprint()`` untouched this iteration.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..config import Config
from .bar_index import BarIndex
from .bars import BarStore
from .datasets import DatasetStore
from .desk_coverage import DESK_TOPUP_TIMEFRAMES, get_desk_coverage
from .desk_universe import UniverseStore
from .tradability import compute_tradability

# The two band sides `compute_tradability` serves. Only `RESISTANCE` is referenced by name below
# (`_distance_bps` treats anything else as the support case) -- no `SUPPORT` constant is defined
# since nothing in this module ever compares against it.
RESISTANCE = "resistance"

# Class rank for both the within-symbol "best band" selection and the cross-symbol final rank
# (assumptions.md iter-3 entry 1) -- a band with no inherited class ranks lowest, never highest
# (an honest absence is never preferred over a graded band).
_CLASS_RANK: dict[str | None, int] = {"A": 3, "B": 2, "C": 1, None: 0}

# The screen store's own env-var override (the ``TAPEOLOGY_DESK_UNIVERSE_DIR``/
# ``TAPEOLOGY_EDGE_REPORT_CACHE_DB`` pattern) -- see ``resolve_desk_screen_dir``.
_SCREEN_DIR_ENV = "TAPEOLOGY_DESK_SCREEN_DIR"


class ScreenIntegrityError(Exception):
    """An on-disk screen snapshot file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated snapshot)."""


class ScreenAlreadyRecorded(Exception):
    """A screen with this EXACT 5-pin key (``screen_date``, ``as_of``, ``universe_snapshot_id``,
    ``config_fingerprint``, ``bar_store_signature``) is already registered. Screen snapshots are
    immutable and append-only -- there is no update/re-record path anywhere in this module; a new
    run under the identical pins reuses the existing snapshot, never a second file."""

    def __init__(self, existing_id: str) -> None:
        self.existing_id = existing_id
        super().__init__(
            f"a screen with this exact key is already recorded as snapshot '{existing_id}' "
            f"-- screen snapshots are immutable and are never re-recorded"
        )


def resolve_desk_screen_dir(desk_universe_dir_resolved: str) -> str:
    """The screen store's directory: the ``TAPEOLOGY_DESK_SCREEN_DIR`` env var if set, else a file
    co-located as a SIBLING of the CALLER's own already-resolved universe directory (the
    ``edge_report_cache.resolve_cache_db_path`` pattern -- takes a plain string, never imports
    ``config.py``'s singleton, so the caller resolves its own universe directory first exactly as
    ``desk_routes.py`` already does). Deliberately NOT a ``desk_screen_dir`` Config field (see the
    module docstring) -- this is an operational storage-location knob, the Constraints' own
    explicit sanction for "worker counts, timeouts, store dirs"."""
    override = os.environ.get(_SCREEN_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "screen")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace) -- the SAME encoding ``research/desk_universe.py`` /
    ``research/bars.py`` hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _iso(epoch: float) -> str:
    """The SAME epoch -> ISO formatting ``tradability.py``'s own ``_iso`` uses -- kept as a local
    copy (this project's own convention: each module owns its tiny formatting helper rather than
    sharing one -- see ``bars.py._iso_utc``, ``desk_universe.py._iso_utc_now``) so a reference
    close is matched by comparing ISO strings on BOTH sides, never by parsing ``basis_as_of`` back
    to a float (which would risk a microsecond round-trip mismatch)."""
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def screen_as_of(screen_date: str) -> str:
    """T-6: ``as_of`` is a deterministic function of ``screen_date`` ALONE, never
    ``datetime.now()`` -- see the module docstring's "as_of translation" section."""
    return f"{screen_date}T23:59:59Z"


# --- bar_store_signature (T-4, TC-15) ------------------------------------------------------------


def _bar_store_signature(coverage: dict) -> str:
    """T-4: a checksum over the sorted ``(symbol, timeframe, latest_window_end_utc)`` tuples,
    derived ENTIRELY from an ALREADY-FETCHED ``desk_coverage.get_desk_coverage`` payload -- this
    function receives no store reference of any kind, so it is structurally incapable of issuing a
    ``BarStore`` call (TC-15)."""
    tuples = sorted(
        (member["symbol"], timeframe, member["per_timeframe"][timeframe]["latest_window_end_utc"])
        for member in coverage["members"]
        for timeframe in DESK_TOPUP_TIMEFRAMES
    )
    return _sha256(_canonical(tuples))[:16]


def compute_bar_store_signature(universe_store: UniverseStore, bar_index: BarIndex) -> str:
    """The standalone accessor: fetches coverage (index-only, T-4) and derives the signature from
    it. Exposed separately from ``compute_screen`` so a caller (or a test) can resolve the 5-pin
    key's ``bar_store_signature`` component WITHOUT running the full per-member walk -- the SAME
    cheap-resolution property ``DeskTopupComputeManager.trigger`` already relies on for
    ``pairs_total`` (known synchronously, before any background work starts)."""
    return _bar_store_signature(get_desk_coverage(universe_store, bar_index))


# --- best-band selection + distance_bps (assumptions.md iter-3, entry 1) -------------------------


def _distance_bps(band: dict, close: float) -> float:
    """``abs(edge_price - close) / close * 10000``, where ``edge_price`` is the near edge to price
    -- ``price_low`` for a resistance band (support from below), ``price_high`` for a support band
    (resistance from above). Correct by construction: ``compute_tradability``'s own side split
    already guarantees ``price_low``/``price_high`` are the closest member on the relevant side."""
    edge_price = band["price_low"] if band["side"] == RESISTANCE else band["price_high"]
    return abs(edge_price - close) / close * 10_000.0


def _select_best_band(bands: list[dict], close: float) -> dict:
    """The symbol's single "best" band: minimizes ``(class rank DESCENDING preference, distance_bps
    ascending, quality_score descending)`` over ``bands`` in ``compute_tradability``'s own served
    order -- ``min`` returns the FIRST of any exactly-tied items, so a tie resolves identically
    every run without a second, invented tie-break."""

    def key(band: dict) -> tuple[int, float, float]:
        return (-_CLASS_RANK[band["class"]], _distance_bps(band, close), -band["quality_score"])

    return min(bands, key=key)


def _row_rank_key(row: dict) -> tuple[int, float, float, str]:
    """The FINAL cross-symbol ``rows`` order (TC-14): the identical selection tuple above, plus
    ``symbol`` ascending as the final tie-break."""
    return (-_CLASS_RANK[row["band_class"]], row["distance_bps"], -row["band_score"], row["symbol"])


# --- reference close price (TC-19) ----------------------------------------------------------------


def _resolve_reference_close(store: BarStore, symbol: str, basis_as_of: str) -> float:
    """The ONE daily bar in ``store.merged_bars(symbol, "1d")`` whose own timestamp -- formatted
    through the SAME ``_iso`` function ``tradability.py`` uses -- matches ``basis_as_of`` verbatim.
    Never re-derives WHICH bar is the basis (that stays ``compute_tradability``'s exclusive
    decision); never touches ``tradability.py``'s or ``levels.py``'s return shape.

    Structurally this bar always exists: ``basis_as_of`` is itself derived from a bar
    ``compute_tradability`` read via this EXACT accessor (``tradability.py``'s own
    ``_select_daily_series`` calls ``BarStore.merged_bars(symbol, "1d")``), and the store is
    immutable between the two reads within one screen computation -- a missing match is an
    unreachable internal-invariant failure, surfaced loudly (never a fabricated close)."""
    for bar in store.merged_bars(symbol, "1d"):
        if _iso(bar.epoch) == basis_as_of:
            return bar.close
    raise RuntimeError(
        f"internal invariant violated: no daily bar for {symbol!r} matches basis_as_of "
        f"{basis_as_of!r} -- compute_tradability's own basis bar must always be present in "
        f"merged_bars(symbol, '1d')"
    )


# --- basis disclosure (goal-desk-iter-9, J-08) -----------------------------------------------------


def _basis_age_days(basis_as_of: str, as_of: str) -> int:
    """``basis_age_days``: a plain calendar-date difference between ``basis_as_of`` (a ranked row's
    own reference session -- ``compute_tradability``'s own already-resolved value, zero new read)
    and ``as_of`` (the screen's own as-of) -- the ``_distance_bps`` precedent's "plain arithmetic
    derivation" style, never a second bar read. Calendar DATES, not a raw hour delta:
    ``basis_as_of`` carries the prior session's own bar-timestamp time-of-day (e.g. ``04:00:00``
    UTC) while ``as_of`` is always ``screen_as_of``'s fixed ``23:59:59Z`` -- comparing the raw
    instants would inflate the count by a fraction of a day for every symbol, so both sides are
    reduced to a UTC calendar date first, the SAME ``.replace("Z", "+00:00")`` parsing style
    ``_epoch`` above already uses."""
    basis_date = datetime.fromisoformat(basis_as_of.replace("Z", "+00:00")).date()
    as_of_date = datetime.fromisoformat(as_of.replace("Z", "+00:00")).date()
    return (as_of_date - basis_date).days


# --- the row computation (the SOLE walker; the manager and the CLI both call this) ----------------


def compute_screen(
    universe_store: UniverseStore,
    bar_store: BarStore,
    bar_index: BarIndex,
    dataset_store: DatasetStore,
    config: Config,
    screen_date: str,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> dict:
    """Walk the LATEST universe snapshot's members, as of ``screen_date``'s session close,
    computing one ranked row (or an honest skip) per member via the canonical owners
    (``compute_tradability``, ``desk_coverage.get_desk_coverage``, ``DatasetStore.list``). Returns
    the full snapshot content MINUS the store-assigned ``id``/``created_utc`` (``ScreenStore.record``
    assigns those): ``{screen_date, as_of, universe_snapshot_id, config_fingerprint,
    bar_store_signature, rows, skipped}``. Each RANKED row additionally carries ``basis_as_of``/
    ``basis_age_days`` (goal-desk-iter-9, J-08 -- see the module docstring's "Basis disclosure"
    section); skip rows never carry them.

    ``progress``, if given, is called after EACH member with ``{"symbol": symbol}`` (the caller
    tracks its own done/total counters -- the ``desk_topup_compute.run_topup`` precedent).
    ``should_abort``, if given and it returns ``True`` before a member starts, stops the walk early
    -- ``rows``/``skipped`` are simply shorter than the full member list; a cooperative stop, never
    a raise. No universe snapshot registered yet -> an honest empty walk (``universe_snapshot_id``
    is ``None``, both lists empty) -- never an error."""
    as_of = screen_as_of(screen_date)
    as_of_epoch = _epoch(as_of)

    universe_records, _universe_errors = universe_store.list()
    universe_snapshot_id = universe_records[-1]["id"] if universe_records else None
    members = list(universe_records[-1]["members"]) if universe_records else []

    coverage_payload = get_desk_coverage(universe_store, bar_index)
    coverage_by_symbol = {m["symbol"]: m["per_timeframe"] for m in coverage_payload["members"]}
    bar_store_signature = _bar_store_signature(coverage_payload)

    dataset_records, _dataset_errors = dataset_store.list()
    tick_symbols = {meta["symbol"] for meta in dataset_records}

    config_fingerprint = config.config_fingerprint()

    rows: list[dict] = []
    skipped: list[dict] = []
    for symbol in members:
        if should_abort is not None and should_abort():
            break
        coverage = coverage_by_symbol[symbol]
        tick_evidence = symbol in tick_symbols
        result = compute_tradability(bar_store, symbol, as_of_epoch, config)

        if result["no_bar_series_for_symbol"]:
            skipped.append(
                {"symbol": symbol, "skipped": True, "reason": "no_bars",
                 "coverage": coverage, "tick_evidence": tick_evidence}
            )
        elif result["basis_as_of"] is None:
            skipped.append(
                {"symbol": symbol, "skipped": True, "reason": "no_basis",
                 "coverage": coverage, "tick_evidence": tick_evidence}
            )
        else:
            close = _resolve_reference_close(bar_store, symbol, result["basis_as_of"])
            best = _select_best_band(result["bands"], close)
            rows.append(
                {
                    "symbol": symbol,
                    "side": best["side"],
                    "band_class": best["class"],
                    "distance_bps": _distance_bps(best, close),
                    "band_score": best["quality_score"],
                    "price_low": best["price_low"],
                    "price_high": best["price_high"],
                    "coverage": coverage,
                    "tick_evidence": tick_evidence,
                    "basis_as_of": result["basis_as_of"],
                    "basis_age_days": _basis_age_days(result["basis_as_of"], as_of),
                }
            )

        if progress is not None:
            progress({"symbol": symbol})

    rows.sort(key=_row_rank_key)
    # `skipped` is already symbol-ascending by construction (walked in `members`' own sorted
    # order, per `desk_universe.UniverseStore.record`'s `sorted(normalized_to_raw)` -- never
    # reordered here, so no redundant second sort is needed.

    return {
        "screen_date": screen_date,
        "as_of": as_of,
        "universe_snapshot_id": universe_snapshot_id,
        "config_fingerprint": config_fingerprint,
        "bar_store_signature": bar_store_signature,
        "rows": rows,
        "skipped": skipped,
    }


# --- the store (frozen JSON, one file per snapshot, structurally immutable) ----------------------


class ScreenStore:
    """File-based store rooted at the config-owned screen directory -- the ONE reader/writer.
    Mirrors ``desk_universe.UniverseStore``'s discipline exactly: every load verifies a
    whole-record checksum (``ScreenIntegrityError`` on any mismatch); the only mutation,
    ``record``, refuses an identical 5-pin key (``ScreenAlreadyRecorded``, never a second file for
    the same key); no update/delete function exists anywhere."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, screen_id: str) -> Path:
        return self._root / f"{screen_id}.json"

    def _load(self, path: Path) -> dict:
        """Load ONE snapshot file, verifying its whole-record checksum. Raises
        ``ScreenIntegrityError`` for any parse/shape/checksum failure -- explicit, never silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise ScreenIntegrityError(
                f"screen snapshot file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise ScreenIntegrityError(
                f"screen snapshot file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise ScreenIntegrityError(
                f"screen snapshot file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise ScreenIntegrityError(
                f"screen snapshot file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered screen's full content (each file verified), oldest first, plus an
        EXPLICIT error row per file that failed verification -- a corrupt file is surfaced, never
        silently hidden and never served as data. Fresh copies of the nested ``rows``/``skipped``
        lists on every call (the ``desk_universe.UniverseStore.list`` per-row-copy discipline), so
        a caller mutating a returned record can never poison a later read."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                meta = self._load(path)
                records.append(
                    {**meta, "rows": [dict(r) for r in meta["rows"]], "skipped": [dict(s) for s in meta["skipped"]]}
                )
            except ScreenIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
        return records, errors

    def find_by_key(
        self, screen_date: str, as_of: str, universe_snapshot_id: str | None,
        config_fingerprint: str, bar_store_signature: str,
    ) -> dict | None:
        """The already-recorded snapshot matching this EXACT 5-pin key, or ``None`` -- the
        append-only dedup lookup ``record`` itself uses, also usable standalone by a caller that
        wants to check before paying for a walk."""
        records, _errors = self.list()
        key = (screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature)
        for record in records:
            record_key = (
                record["screen_date"], record["as_of"], record["universe_snapshot_id"],
                record["config_fingerprint"], record["bar_store_signature"],
            )
            if record_key == key:
                return record
        return None

    def record(
        self,
        *,
        screen_date: str,
        as_of: str,
        universe_snapshot_id: str | None,
        config_fingerprint: str,
        bar_store_signature: str,
        rows: list[dict],
        skipped: list[dict],
    ) -> dict:
        """Persist ONE new screen snapshot (record + register in a single explicit action). A
        snapshot already registered under this EXACT 5-pin key raises the 409-style
        ``ScreenAlreadyRecorded`` (there is no update/re-record path at all -- immutability is
        structural). A file already sitting at this key's own deterministic path but failing its
        integrity check raises ``ScreenIntegrityError`` -- never a silent overwrite (see below)."""
        existing = self.find_by_key(
            screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature
        )
        if existing is not None:
            raise ScreenAlreadyRecorded(existing["id"])

        checksum = _sha256(
            _canonical([screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature])
        )[:12]
        screen_id = f"screen-{screen_date}-{checksum}"
        # A file already at this key's own path, with `find_by_key` reporting no match, means
        # exactly one thing: that file failed its integrity check (`list` surfaces it in
        # `integrity_errors` and withholds it from `records`), because the path is a pure function
        # of the 5-pin key we just searched by. Writing here would SILENTLY overwrite a
        # corrupted/tampered snapshot and erase the very integrity error the store had been
        # honestly surfacing -- both a rewrite ("snapshots are append-only ... never rewritten")
        # and a silence. Refuse loudly instead; a human decides what happens to the damaged file.
        if self._path(screen_id).exists():
            raise ScreenIntegrityError(
                f"screen snapshot file '{self._path(screen_id).name}' already exists on disk but "
                f"failed its integrity check -- refusing to overwrite it (screen snapshots are "
                f"append-only and are never rewritten). Move or remove the damaged file "
                f"explicitly before re-recording this key."
            )
        meta = {
            "id": screen_id,
            "screen_date": screen_date,
            "as_of": as_of,
            "universe_snapshot_id": universe_snapshot_id,
            "config_fingerprint": config_fingerprint,
            "bar_store_signature": bar_store_signature,
            "created_utc": _iso_utc_now(),
            "rows": list(rows),
            "skipped": list(skipped),
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(screen_id).write_text(json.dumps(payload))
        return dict(meta)
