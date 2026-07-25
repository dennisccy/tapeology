"""The S&P 100 universe snapshot store (Era B "The Desk", Key Capability 1, J-01) — the Product
Shape's "Universe snapshots + membership" row's ONE owner.

THIS MODULE is the only code that fetches, parses, or persists universe-membership data. A
universe snapshot is an IMMUTABLE recording of one fetch's validated, normalized S&P 100
membership (the sorted ticker list, the raw-form mapping for normalized entries, and the exact
Path-A Config values used at registration) plus metadata (id, date, a content checksum, and a
created timestamp). Files live under the config-owned universe directory
(``TAPEOLOGY_DESK_UNIVERSE_DIR`` override, ``config.desk_universe_dir`` default — gitignored via
``.data/``), one JSON file per snapshot. This module deliberately MIRRORS ``research/bars.py`` /
``research/datasets.py`` (the plan's own explicit directive): a checksum-wrapped record verified
on every load, ``record`` as the only mutation, the same honest-failure taxonomy — WITHOUT those
modules' later stat-keyed performance cache (era-fast_wall J-02), since a universe snapshot is a
handful of KB and this is the capability's first iteration (no measured cost to amortize yet).

Disciplines (each an anti-goal or a J-01 acceptance clause):

  * **Membership is never a signal.** This module selects WHAT the desk screens; nothing here
    computes, ranks, or scores anything. Callers pass membership straight through.
  * **Honest parsing, never a guess.** ``parse_constituents`` validates ticker charset
    (``[A-Z.-]{1,6}``), member-count bounds, and the table shape itself; ANY failure raises the
    specific, honest ``UniverseValidationError`` — never a partial or guessed list (T-1). Yahoo's
    dash convention (``BRK.B -> BRK-B``) is applied at parse time; the raw form is retained (T-2).
  * **Immutable — structurally.** No update/delete function exists anywhere in this module
    (immutability is structural, not policed). The only mutation is ``UniverseStore.record``, and
    it REFUSES content already registered: re-recording the same membership raises the 409-style
    ``UniverseAlreadyRegistered`` naming the existing snapshot.
  * **Store separation (T-3).** This module never imports ``research/datasets.py``'s registration
    surface or ``DatasetStore`` — a universe snapshot is never written through, or registered as,
    a dataset (proven by a source-introspection guard in ``tests/test_desk_universe.py``).
  * **Honest failure states.** A vendor-fetch failure (network/non-200) raises the distinct
    ``UniverseFetchError`` — never a cached or fabricated fallback page; a corrupted or tampered
    on-disk file raises ``UniverseIntegrityError`` on load — never silence, never a fabricated
    snapshot.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

# The Yahoo-style ticker charset (goal.md Key Capability 1 / plan T-1): after normalization every
# member must match this — a bare, honest gate with no per-symbol allowlist to keep in sync.
_TICKER_RE = re.compile(r"^[A-Z.-]{1,6}$")

# A Wikipedia footnote citation marker (e.g. "AAPL[1]") that can land inside a table cell's text
# when a ``<sup class="reference">`` tag sits next to the real content — stripped defensively so a
# genuine footnote reference on the Symbol column is never mistaken for part of the ticker itself.
_CITATION_RE = re.compile(r"\[\s*\d+\s*\]")

# Header cell text (case-insensitive, exact match after stripping) this parser accepts as "this
# column holds the ticker" — covers the Wikipedia S&P 100/500 "Symbol" convention plus the more
# generic "Ticker" heading some constituent tables use instead.
_SYMBOL_HEADER_NAMES = ("symbol", "ticker")

# The vendor-fetch User-Agent (era-B J-01, verified live against the real Wikimedia edge). NOT a
# Config field — it shapes no served value, only whether the fetch itself succeeds (the
# ``bar_recency_delay_seconds``/vendor-mechanics precedent). Wikimedia's documented User-Agent
# policy (meta.wikimedia.org/wiki/User-Agent_policy) requires a self-identifying bot string
# carrying a project reference; a generic/uninformative UA is rejected with an honest HTTP 403
# ("Please respect our robot policy") — confirmed live: the SAME request succeeds once the UA
# carries a URL-shaped token and fails without one, independent of every other header. This
# project has no public home page, so the identifying URL uses the IANA-reserved ``.invalid`` TLD
# (RFC 2606 — explicitly never a real, resolvable domain) rather than fabricate one.
_FETCH_USER_AGENT = (
    "TapeologyDeskBot/1.0 (+http://example.invalid/tapeology; research tool, operator-run, "
    "non-commercial)"
)


class UniverseFetchError(Exception):
    """The vendor HTTP fetch itself failed (network error, timeout, or a non-200 response) —
    honest and explicit; never a cached or fabricated fallback page (T-1)."""


class UniverseValidationError(Exception):
    """The fetched page failed parsing or validation: no recognizable constituents table, a
    ticker outside the ``[A-Z.-]{1,6}`` charset, or a member count outside the configured
    ``[min_members, max_members]`` bounds. Always specific and honest — never a partial or
    guessed list (T-1)."""


class UniverseIntegrityError(Exception):
    """An on-disk snapshot file failed its checksum verification on load — corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated snapshot)."""


class UniverseAlreadyRegistered(Exception):
    """The exact membership content is already registered under an existing snapshot. Universe
    snapshots are immutable — there is no update/re-record path anywhere in this module."""

    def __init__(self, existing_id: str) -> None:
        self.existing_id = existing_id
        super().__init__(
            f"this exact universe membership is already registered as snapshot '{existing_id}' "
            f"— universe snapshots are immutable and are never re-recorded"
        )


@dataclass(frozen=True)
class ParsedUniverse:
    """One successfully validated parse: the normalized, deduped, sorted ticker list plus the
    normalized -> raw form mapping (T-2 provenance) for EVERY member (identical to the normalized
    form when normalization was a no-op)."""

    members: list[str]
    raw_members: dict[str, str]


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace) — the SAME encoding ``research/bars.py`` /
    ``research/datasets.py`` hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _content_checksum12(members: list[str]) -> str:
    """The snapshot's CONTENT identity: the first 12 hex chars of a sha256 over the normalized
    membership list alone (never the raw HTML, the source URL, or any provenance field) — the
    same 12-character form embedded in the filename (``universe-<date>-<checksum12>.json``) and
    served as ``meta["checksum"]``. Registration-time duplicate detection and the filename both
    use exactly this value, so two fetches that parse to the identical membership are recognized
    as the same content regardless of when or from what raw page they were fetched."""
    return _sha256(_canonical({"members": list(members)}))[:12]


# --- fetch (the vendor seam) -----------------------------------------------------------------------


def fetch_constituents_html(source_url: str, *, timeout: float) -> str:
    """The REAL vendor call: a plain, keyless GET against the documented public source (mirrors
    the Yahoo adapter's keyless, credential-free contract — no signup, no API key). Raises the
    explicit ``UniverseFetchError`` for any transport failure or non-200 response — never a
    cached or fabricated fallback page (T-1). Lazy ``httpx`` import mirrors the adapters' own
    lazy-SDK-import discipline (this function is the only code path that pays its cost)."""
    import httpx

    try:
        response = httpx.get(
            source_url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": _FETCH_USER_AGENT},
        )
    except httpx.HTTPError as exc:
        raise UniverseFetchError(f"could not reach '{source_url}': {exc}") from exc
    if response.status_code != 200:
        raise UniverseFetchError(
            f"'{source_url}' returned HTTP {response.status_code} — refusing to parse an error page"
        )
    return response.text


# --- parse (stdlib-only; no lxml/html5lib/beautifulsoup4/pandas.read_html) -------------------------


class _TableExtractor(HTMLParser):
    """Extracts every top-level ``<table>`` on the page as a list of rows, each row a list of
    cell text strings (``<td>``/``<th>`` treated uniformly, so a header row of ``<th>`` cells and
    a data row of ``<td>`` cells both come out as plain text rows). A table NESTED inside another
    table's cell contributes nothing to either table (``_table_depth`` guards every row/cell
    event to depth 1) — the real Wikipedia constituents table is not nested, and this keeps the
    extractor a simple, honest reflection of stdlib-only parsing rather than a general HTML-table
    library. All text nodes encountered while inside a cell are concatenated (so a ticker wrapped
    in ``<a href="...">AAPL</a>`` — the real Wikipedia markup — is read correctly) and only
    stripped once, at cell-close, so incidental inter-tag whitespace collapses naturally."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table_depth = 0
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._current_table = []
        elif tag == "tr" and self._table_depth == 1 and self._current_table is not None:
            self._current_row = []
        elif tag in ("td", "th") and self._table_depth == 1 and self._current_row is not None:
            self._current_cell = []
            self._in_cell = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._in_cell:
            assert self._current_row is not None and self._current_cell is not None
            self._current_row.append("".join(self._current_cell).strip())
            self._current_cell = None
            self._in_cell = False
        elif tag == "tr" and self._table_depth == 1 and self._current_row is not None:
            assert self._current_table is not None
            if self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table":
            if self._table_depth == 1 and self._current_table is not None:
                self.tables.append(self._current_table)
                self._current_table = None
            self._table_depth = max(0, self._table_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            assert self._current_cell is not None
            self._current_cell.append(data)


def _extract_tables(html: str) -> list[list[list[str]]]:
    parser = _TableExtractor()
    parser.feed(html)
    return parser.tables


def _find_symbol_column(tables: list[list[list[str]]]) -> tuple[list[list[str]], int] | None:
    """The first table (document order) whose header row names a Symbol/Ticker column — never a
    hardcoded column index, so a harmless reordering of the real page's columns cannot silently
    misread a different field as the ticker. Returns ``(data_rows, symbol_column_index)`` or
    ``None`` if no table has a recognizable column (an honest table-shape failure, T-1)."""
    for table in tables:
        if not table:
            continue
        header = [cell.strip().lower() for cell in table[0]]
        for name in _SYMBOL_HEADER_NAMES:
            if name in header:
                return table[1:], header.index(name)
    return None


def parse_constituents(html: str, *, min_members: int, max_members: int) -> ParsedUniverse:
    """Parse, validate, and normalize a constituents page's raw HTML into a ``ParsedUniverse``.
    Stdlib-only (``html.parser.HTMLParser`` — no ``lxml``/``html5lib``/``beautifulsoup4``/
    ``pandas.read_html``, none of which are declared dependencies of this project).

    Every failure is a distinct, honest ``UniverseValidationError`` naming the specific problem —
    never a partial or guessed list (T-1):
      * no table carries a recognizable Symbol/Ticker column (the page structure changed);
      * the table yields zero tickers;
      * ANY raw ticker fails the ``[A-Z.-]{1,6}`` charset check after normalization (the WHOLE
        fetch is refused, never a per-row skip that would silently shrink the list);
      * the final (deduped) member count falls outside ``[min_members, max_members]``.

    Normalization (T-2): Yahoo's dash convention is applied to every raw ticker
    (``BRK.B -> BRK-B``, ``BF.B -> BF-B``) before the charset check and before dedup — the raw
    form (as it appeared on the page) is retained per normalized ticker in ``raw_members``.
    """
    tables = _extract_tables(html)
    found = _find_symbol_column(tables)
    if found is None:
        raise UniverseValidationError(
            "could not find a constituents table with a 'Symbol' (or 'Ticker') column — the "
            "page structure may have changed"
        )
    rows, symbol_col = found

    raw_tickers: list[str] = []
    for row in rows:
        if symbol_col >= len(row):
            continue  # a short/malformed row (e.g. a spanning footnote row) — not a ticker itself
        raw = _CITATION_RE.sub("", row[symbol_col]).strip()
        if raw:
            raw_tickers.append(raw)

    if not raw_tickers:
        raise UniverseValidationError(
            "the constituents table yielded zero tickers — refusing an empty list"
        )

    normalized_to_raw: dict[str, str] = {}
    for raw in raw_tickers:
        normalized = raw.replace(".", "-").upper()
        if not _TICKER_RE.match(normalized):
            raise UniverseValidationError(
                f"ticker '{raw}' (normalized '{normalized}') fails the charset check "
                f"[A-Z.-]{{1,6}} — refusing the whole fetch, never a partial list"
            )
        normalized_to_raw.setdefault(normalized, raw)

    member_count = len(normalized_to_raw)
    if not (min_members <= member_count <= max_members):
        raise UniverseValidationError(
            f"parsed {member_count} members, outside the expected [{min_members}, {max_members}] "
            f"range — refusing a suspiciously sized list"
        )

    members = sorted(normalized_to_raw)
    return ParsedUniverse(members=members, raw_members=normalized_to_raw)


# --- the store (frozen JSON, one file per snapshot, structurally immutable) ------------------------


class UniverseStore:
    """File-based store rooted at the config-owned universe directory — the ONE reader/writer.

    Construction is cheap (no I/O); the directory is created on the first ``record``. Mirrors
    ``bars.py``/``datasets.py``: every load verifies a whole-record checksum
    (``UniverseIntegrityError`` on any mismatch); the only mutation, ``record``, refuses content
    already registered (``UniverseAlreadyRegistered``)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, snapshot_id: str) -> Path:
        return self._root / f"{snapshot_id}.json"

    def _load(self, path: Path) -> dict:
        """Load ONE snapshot file, verifying its whole-record checksum. Raises
        ``UniverseIntegrityError`` for any parse/shape/checksum failure — explicit, never
        silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise UniverseIntegrityError(
                f"universe snapshot file '{path.name}' is not parseable ({exc}) — corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise UniverseIntegrityError(
                f"universe snapshot file '{path.name}' does not carry the expected record shape "
                f"— corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise UniverseIntegrityError(
                f"universe snapshot file '{path.name}' failed its integrity check (checksum "
                f"mismatch) — the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise UniverseIntegrityError(
                f"universe snapshot file '{path.name}' does not carry the expected record shape "
                f"— corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered snapshot's metadata + membership (each file verified), oldest first,
        plus an EXPLICIT error row per file that failed verification — a corrupt file is
        surfaced, never silently hidden and never served as data. Fresh copies of the nested
        ``members``/``raw_members`` fields on every call, so a caller mutating a returned record
        can never poison a later read (the ``bars.py`` per-row-copy discipline)."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                meta = self._load(path)
                records.append(
                    {**meta, "members": list(meta["members"]), "raw_members": dict(meta["raw_members"])}
                )
            except UniverseIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
        return records, errors

    def record(
        self,
        *,
        members: list[str],
        raw_members: dict[str, str],
        source_url: str,
        min_members: int,
        max_members: int,
    ) -> dict:
        """Persist ONE new universe snapshot (record + register in a single explicit action).
        Content already registered raises the 409-style ``UniverseAlreadyRegistered`` (there is
        no update/re-record path at all — immutability is structural). ``source_url``,
        ``min_members``, ``max_members`` are the exact Path-A Config values used at THIS
        registration, embedded verbatim into the stored/served payload (provenance duty)."""
        checksum = _content_checksum12(members)
        existing, _errors = self.list()
        for meta in existing:
            if meta["checksum"] == checksum:
                raise UniverseAlreadyRegistered(meta["id"])

        date = datetime.now(timezone.utc).date().isoformat()
        snapshot_id = f"universe-{date}-{checksum}"
        meta = {
            "id": snapshot_id,
            "date": date,
            "checksum": checksum,
            "member_count": len(members),
            "source_url": source_url,
            "min_members": min_members,
            "max_members": max_members,
            "created_utc": _iso_utc_now(),
            "members": list(members),
            "raw_members": dict(raw_members),
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(snapshot_id).write_text(json.dumps(payload))
        return dict(meta)
