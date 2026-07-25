# Iteration diff (bounded)

Files changed: 11. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/desk_universe.py` (25 lines not shown)
- `apps/backend/tests/fixtures/universe/sp100_constituents.html` (246 lines not shown)
- `apps/backend/tests/fixtures/universe/sp100_constituents_corrupted.html` (246 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index e533e70..0a56b18 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1101,6 +1101,38 @@ class Config:
         default_factory=lambda: {"A": 2.0, "B": 1.0, "C": 0.5}
     )
 
+    # --- Era B "The Desk": UNIVERSE INGESTION (Key Capability 1, J-01) --------------------------
+    # Every field below governs ONLY the brand-new universe-snapshot capability (fetch, parse,
+    # validate, register S&P 100 membership) — none of them are read by the tape engine, a
+    # backtest, a study, or the PnL ledger, so they take Path A: each one lands in the
+    # ``config_fingerprint`` exclusion set below (the ``bar_timeframes``/``bar_dir`` precedent),
+    # with a stability test proving the pin is unchanged and a counter-test proving the field
+    # genuinely shapes the NEW path's output (``tests/test_desk_universe.py``). Namespaced
+    # ``desk_universe_*`` so it never collides with the unrelated ``sr_*`` / ``structure_tape_*`` /
+    # ``setups_*`` research families above.
+    #
+    # SOURCE URL: the ONE documented public constituents source (goal.md Key Capability 1 — "one
+    # documented source URL as a Path-A Config field"). A pure validation/fetch-target value — it
+    # selects WHERE to fetch from, never what a fetched member list contains (membership is never a
+    # signal, per the desk-era anti-goals), so it cannot affect any persisted research value.
+    desk_universe_source_url: str = "https://en.wikipedia.org/wiki/S%26P_100"
+    # MEMBER-COUNT BOUNDS: the sanity window a parsed membership list must fall inside (goal.md's
+    # "count sanity 90-110") — a page that returns far too few or far too many rows almost
+    # certainly means the table shape changed underneath the parser, so refusing outside this
+    # window is the honest failure T-1 requires (never a partial or guessed list). Defaults measured
+    # against the real S&P 100 index, which — because of dual-class share lines (e.g. GOOG/GOOGL) —
+    # legitimately runs a few names past 100.
+    desk_universe_min_members: int = 90
+    desk_universe_max_members: int = 110
+    # STORAGE DIRECTORY: where the universe store persists frozen, checksummed snapshot JSON files
+    # (one file per registered snapshot) — mirrors ``bar_dir``/``dataset_dir`` exactly (the
+    # era-4/era-3 capability-1 precedent). ONLY a default here — the operator overrides it with the
+    # ``TAPEOLOGY_DESK_UNIVERSE_DIR`` env var (read in ``desk_universe_dir_resolved`` below, the
+    # ``bar_dir_resolved`` pattern) and tests point it at a temp dir the same way. Package-anchored
+    # (``apps/backend/.data/universe/``, covered by the repo's ``.data/`` gitignore entry) so it
+    # resolves identically whatever the process cwd is.
+    desk_universe_dir: str = str(Path(__file__).resolve().parents[1] / ".data" / "universe")
+
     def profile_definition(self, profile_id: str) -> dict | None:
         """The config-owned descriptor for ``profile_id`` (Data Contract row 33) — the
         ``strategy_definition`` pattern applied to profiles: THIS method is the ONE place that
@@ -1309,6 +1341,13 @@ class Config:
         code change, while tests point it at a temp dir via the env var."""
         return os.environ.get("TAPEOLOGY_BAR_DIR", self.bar_dir)
 
+    def desk_universe_dir_resolved(self) -> str:
+        """The effective universe-store directory: the ``TAPEOLOGY_DESK_UNIVERSE_DIR`` env var if
+        set, else the package-anchored config default (the ``bar_dir_resolved`` pattern, era-B
+        J-01). Read at store-construction time so an operator can point the universe store at a
+        real location without code change, while tests point it at a temp dir via the env var."""
+        return os.environ.get("TAPEOLOGY_DESK_UNIVERSE_DIR", self.desk_universe_dir)
+
     def config_fingerprint(self) -> str:
         """A stable hash over the ENTIRE frozen config (capability 28 / honesty stamps).
 
@@ -1512,6 +1551,23 @@ class Config:
             "structure_tape_stop_bps_by_class",
             "structure_tape_reward_r_multiple_by_class",
             "structure_tape_size_multiple_by_class",
+            # Era B "The Desk" universe ingestion (Key Capability 1, J-01): the SAME
+            # ``bar_timeframes``/``bar_dir`` "brand-new, unrelated capability" rationale directly
+            # above -- the universe subsystem (fetch source, member-count sanity bounds, storage
+            # directory) is a SEPARATE, additive capability that selects WHICH symbols the desk
+            # screens; it never enters the tape engine, a backtest, a study, or the PnL ledger (the
+            # desk-era anti-goal "membership is never a signal"), so none of these three fields can
+            # affect any persisted research value. Two journals identical in every FINGERPRINTED
+            # threshold but configured with a different universe source URL, member-count bounds,
+            # or storage directory MUST share a fingerprint (else every temp-dir test of this
+            # brand-new capability would mint a different fingerprint and falsely fragment the
+            # tape/backtest/PnL pools those OTHER thresholds exist to protect). Pinned by a
+            # fingerprint-stability test + the real-threshold counter-test in
+            # ``tests/test_desk_universe.py``.
+            "desk_universe_source_url",
+            "desk_universe_min_members",
+            "desk_universe_max_members",
+            "desk_universe_dir",
         }
         payload = {k: v for k, v in asdict(self).items() if k not in excluded}
         encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index c95d1e5..cbeb917 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -39,6 +39,7 @@ from .providers.adapters.base import (
 )
 from .providers.historical import HistoricalProvider
 from .providers.live import LiveProvider
+from .research.desk_routes import router as desk_router
 from .research.routes import (
     ResearchRegistry,
     get_registry_or_none,
@@ -196,6 +197,10 @@ app.add_middleware(
 # router; the engine snapshot endpoints above are untouched.
 app.include_router(research_router)
 
+# Era B "The Desk" (J-01): the universe-ingestion namespace, under the SAME /research prefix but
+# its own module (routes.py is already large) — mounted separately, alongside research_router.
+app.include_router(desk_router)
+
 # The meta namespace (Data Contract row 35, J-01): the canonical UI route map. The rendered nav
 # and the MCP ``ui_route_map`` tool read it — never a hand-maintained duplicate list.
 app.include_router(meta_router)
diff --git a/apps/backend/pyproject.toml b/apps/backend/pyproject.toml
index f52272c..d8844b2 100644
--- a/apps/backend/pyproject.toml
+++ b/apps/backend/pyproject.toml
@@ -8,5 +8,5 @@ requires-python = ">=3.12"
 testpaths = ["tests"]
 addopts = "-q"
 markers = [
-    "integration: hits the REAL Alpaca live socket (operator/gated; needs credentials + market hours + TAPEOLOGY_LIVE_INTEGRATION=1). Skipped by default.",
+    "integration: hits a REAL external system -- Alpaca live socket/recording, Yahoo Finance, or Wikipedia (operator/gated; TAPEOLOGY_LIVE_INTEGRATION=1, some also need credentials + market hours). Skipped by default.",
 ]
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
new file mode 100644
index 0000000..9cde5d0
--- /dev/null
+++ b/apps/backend/app/research/desk_routes.py
@@ -0,0 +1,103 @@
+"""``/research/desk/*`` — Era B "The Desk" (J-01): universe ingestion.
+
+THIS is the first desk-era route module: two routes over the new universe subsystem
+(``desk_universe.py``) — ``POST /research/desk/universe/fetch`` (the explicit operator research
+action: fetch -> parse -> validate -> register) and ``GET /research/desk/universe`` (snapshot
+list + latest membership, honestly empty before any registration — never 404). Kept as its own
+module (mirroring the plan's stated preference) rather than folding into ``routes.py``, which is
+already large; mounted separately in ``app/main.py``.
+
+The fetch is a single synchronous vendor call, so — unlike the longer-running J-02/J-03 top-up and
+screen runs — it needs no compute-manager (that pattern lands with those later journeys)."""
+
+from __future__ import annotations
+
+from typing import Callable
+
+from fastapi import APIRouter, Depends, HTTPException
+
+from ..config import CONFIG
+from .desk_universe import (
+    UniverseAlreadyRegistered,
+    UniverseFetchError,
+    UniverseStore,
+    UniverseValidationError,
+    fetch_constituents_html,
+    parse_constituents,
+)
+
+router = APIRouter(prefix="/research/desk", tags=["desk"])
+
+
+def get_universe_store() -> UniverseStore:
+    """The universe store rooted at the config-owned directory (``TAPEOLOGY_DESK_UNIVERSE_DIR``
+    override, package-anchored default) — the ``get_bar_store``/``get_dataset_store`` pattern. A
+    FastAPI dependency so tests can point it at a temp dir via the env var or override it
+    outright."""
+    return UniverseStore(CONFIG.desk_universe_dir_resolved())
+
+
+def get_universe_fetcher() -> Callable[[str], str]:
+    """The universe-page HTML fetch — a FastAPI dependency so a hermetic test overrides it
+    outright via ``app.dependency_overrides`` (the ``get_bar_store``/``get_dataset_store`` seam)
+    and injects fixture HTML with ZERO network calls. The default is the real keyless HTTP GET
+    (``fetch_constituents_html``) bound to the existing vendor-call budget
+    (``CONFIG.vendor_http_timeout_seconds`` — the same deadline every adapter already honors)."""
+
+    def _fetch(source_url: str) -> str:
+        return fetch_constituents_html(source_url, timeout=CONFIG.vendor_http_timeout_seconds)
+
+    return _fetch
+
+
+@router.post("/universe/fetch")
+def fetch_universe(
+    store: UniverseStore = Depends(get_universe_store),
+    fetcher: Callable[[str], str] = Depends(get_universe_fetcher),
+) -> dict:
+    """Fetch -> parse -> validate -> register ONE new universe snapshot — the explicit operator
+    research action; nothing here runs on a schedule or a page load. Three honest, distinct
+    failure states (mirrors the ``POST /research/bars`` taxonomy):
+      * the vendor fetch itself fails (unreachable / non-200) -> 503, naming the source
+        (``UniverseFetchError`` — never a fabricated or cached fallback page);
+      * a parse/charset/bounds failure -> 422, naming the specific problem
+        (``UniverseValidationError`` — T-1, never a partial or guessed list);
+      * content identical to an already-registered snapshot -> 409, naming the existing snapshot
+        (``UniverseAlreadyRegistered`` — snapshots are immutable, never rewritten)."""
+    source_url = CONFIG.desk_universe_source_url
+    try:
+        html = fetcher(source_url)
+    except UniverseFetchError as exc:
+        raise HTTPException(status_code=503, detail=str(exc))
+
+    try:
+        parsed = parse_constituents(
+            html,
+            min_members=CONFIG.desk_universe_min_members,
+            max_members=CONFIG.desk_universe_max_members,
+        )
+    except UniverseValidationError as exc:
+        raise HTTPException(status_code=422, detail=str(exc))
+
+    try:
+        meta = store.record(
+            members=parsed.members,
+            raw_members=parsed.raw_members,
+            source_url=source_url,
+            min_members=CONFIG.desk_universe_min_members,
+            max_members=CONFIG.desk_universe_max_members,
+        )
+    except UniverseAlreadyRegistered as exc:
+        raise HTTPException(status_code=409, detail=str(exc))
+    return {"universe": meta}
+
+
+@router.get("/universe")
+def get_universe(store: UniverseStore = Depends(get_universe_store)) -> dict:
+    """Snapshot list + latest membership, verbatim (checksum-verified on load). An explicit HTTP
+    200 EMPTY payload before any registration — never a 404 (the ``GET /research/bars`` /
+    ``GET /research/datasets`` no-data convention). ``latest`` is the most recently created
+    snapshot (``None`` before any registration) — never recomputed, always the stored record."""
+    records, errors = store.list()
+    latest = records[-1] if records else None
+    return {"snapshots": records, "latest": latest, "integrity_errors": errors}
diff --git a/apps/backend/app/research/desk_universe.py b/apps/backend/app/research/desk_universe.py
new file mode 100644
index 0000000..a2efbd0
--- /dev/null
+++ b/apps/backend/app/research/desk_universe.py
@@ -0,0 +1,419 @@
+"""The S&P 100 universe snapshot store (Era B "The Desk", Key Capability 1, J-01) — the Product
+Shape's "Universe snapshots + membership" row's ONE owner.
+
+THIS MODULE is the only code that fetches, parses, or persists universe-membership data. A
+universe snapshot is an IMMUTABLE recording of one fetch's validated, normalized S&P 100
+membership (the sorted ticker list, the raw-form mapping for normalized entries, and the exact
+Path-A Config values used at registration) plus metadata (id, date, a content checksum, and a
+created timestamp). Files live under the config-owned universe directory
+(``TAPEOLOGY_DESK_UNIVERSE_DIR`` override, ``config.desk_universe_dir`` default — gitignored via
+``.data/``), one JSON file per snapshot. This module deliberately MIRRORS ``research/bars.py`` /
+``research/datasets.py`` (the plan's own explicit directive): a checksum-wrapped record verified
+on every load, ``record`` as the only mutation, the same honest-failure taxonomy — WITHOUT those
+modules' later stat-keyed performance cache (era-fast_wall J-02), since a universe snapshot is a
+handful of KB and this is the capability's first iteration (no measured cost to amortize yet).
+
+Disciplines (each an anti-goal or a J-01 acceptance clause):
+
+  * **Membership is never a signal.** This module selects WHAT the desk screens; nothing here
+    computes, ranks, or scores anything. Callers pass membership straight through.
+  * **Honest parsing, never a guess.** ``parse_constituents`` validates ticker charset
+    (``[A-Z.-]{1,6}``), member-count bounds, and the table shape itself; ANY failure raises the
+    specific, honest ``UniverseValidationError`` — never a partial or guessed list (T-1). Yahoo's
+    dash convention (``BRK.B -> BRK-B``) is applied at parse time; the raw form is retained (T-2).
+  * **Immutable — structurally.** No update/delete function exists anywhere in this module
+    (immutability is structural, not policed). The only mutation is ``UniverseStore.record``, and
+    it REFUSES content already registered: re-recording the same membership raises the 409-style
+    ``UniverseAlreadyRegistered`` naming the existing snapshot.
+  * **Store separation (T-3).** This module never imports ``research/datasets.py``'s registration
+    surface or ``DatasetStore`` — a universe snapshot is never written through, or registered as,
+    a dataset (proven by a source-introspection guard in ``tests/test_desk_universe.py``).
+  * **Honest failure states.** A vendor-fetch failure (network/non-200) raises the distinct
+    ``UniverseFetchError`` — never a cached or fabricated fallback page; a corrupted or tampered
+    on-disk file raises ``UniverseIntegrityError`` on load — never silence, never a fabricated
+    snapshot.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import re
+from dataclasses import dataclass
+from datetime import datetime, timezone
+from html.parser import HTMLParser
+from pathlib import Path
+
+# The Yahoo-style ticker charset (goal.md Key Capability 1 / plan T-1): after normalization every
+# member must match this — a bare, honest gate with no per-symbol allowlist to keep in sync.
+_TICKER_RE = re.compile(r"^[A-Z.-]{1,6}$")
+
+# A Wikipedia footnote citation marker (e.g. "AAPL[1]") that can land inside a table cell's text
+# when a ``<sup class="reference">`` tag sits next to the real content — stripped defensively so a
+# genuine footnote reference on the Symbol column is never mistaken for part of the ticker itself.
+_CITATION_RE = re.compile(r"\[\s*\d+\s*\]")
+
+# Header cell text (case-insensitive, exact match after stripping) this parser accepts as "this
+# column holds the ticker" — covers the Wikipedia S&P 100/500 "Symbol" convention plus the more
+# generic "Ticker" heading some constituent tables use instead.
+_SYMBOL_HEADER_NAMES = ("symbol", "ticker")
+
+# The vendor-fetch User-Agent (era-B J-01, verified live against the real Wikimedia edge). NOT a
+# Config field — it shapes no served value, only whether the fetch itself succeeds (the
+# ``bar_recency_delay_seconds``/vendor-mechanics precedent). Wikimedia's documented User-Agent
+# policy (meta.wikimedia.org/wiki/User-Agent_policy) requires a self-identifying bot string
+# carrying a project reference; a generic/uninformative UA is rejected with an honest HTTP 403
+# ("Please respect our robot policy") — confirmed live: the SAME request succeeds once the UA
+# carries a URL-shaped token and fails without one, independent of every other header. This
+# project has no public home page, so the identifying URL uses the IANA-reserved ``.invalid`` TLD
+# (RFC 2606 — explicitly never a real, resolvable domain) rather than fabricate one.
+_FETCH_USER_AGENT = (
+    "TapeologyDeskBot/1.0 (+http://example.invalid/tapeology; research tool, operator-run, "
+    "non-commercial)"
+)
+
+
+class UniverseFetchError(Exception):
+    """The vendor HTTP fetch itself failed (network error, timeout, or a non-200 response) —
+    honest and explicit; never a cached or fabricated fallback page (T-1)."""
+
+
+class UniverseValidationError(Exception):
+    """The fetched page failed parsing or validation: no recognizable constituents table, a
+    ticker outside the ``[A-Z.-]{1,6}`` charset, or a member count outside the configured
+    ``[min_members, max_members]`` bounds. Always specific and honest — never a partial or
+    guessed list (T-1)."""
+
+
+class UniverseIntegrityError(Exception):
+    """An on-disk snapshot file failed its checksum verification on load — corrupted or
+    tampered, surfaced explicitly (never silence, never a fabricated snapshot)."""
+
+
+class UniverseAlreadyRegistered(Exception):
+    """The exact membership content is already registered under an existing snapshot. Universe
+    snapshots are immutable — there is no update/re-record path anywhere in this module."""
+
+    def __init__(self, existing_id: str) -> None:
+        self.existing_id = existing_id
+        super().__init__(
+            f"this exact universe membership is already registered as snapshot '{existing_id}' "
+            f"— universe snapshots are immutable and are never re-recorded"
+        )
+
+
+@dataclass(frozen=True)
+class ParsedUniverse:
+    """One successfully validated parse: the normalized, deduped, sorted ticker list plus the
+    normalized -> raw form mapping (T-2 provenance) for EVERY member (identical to the normalized
+    form when normalization was a no-op)."""
+
+    members: list[str]
+    raw_members: dict[str, str]
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding every checksum in this module hashes (stable across
+    processes: sorted keys, no whitespace) — the SAME encoding ``research/bars.py`` /
+    ``research/datasets.py`` hash."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return (
+        datetime.now(timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _content_checksum12(members: list[str]) -> str:
+    """The snapshot's CONTENT identity: the first 12 hex chars of a sha256 over the normalized
+    membership list alone (never the raw HTML, the source URL, or any provenance field) — the
+    same 12-character form embedded in the filename (``universe-<date>-<checksum12>.json``) and
+    served as ``meta["checksum"]``. Registration-time duplicate detection and the filename both
+    use exactly this value, so two fetches that parse to the identical membership are recognized
+    as the same content regardless of when or from what raw page they were fetched."""
+    return _sha256(_canonical({"members": list(members)}))[:12]
+
+
+# --- fetch (the vendor seam) -----------------------------------------------------------------------
+
+
+def fetch_constituents_html(source_url: str, *, timeout: float) -> str:
+    """The REAL vendor call: a plain, keyless GET against the documented public source (mirrors
+    the Yahoo adapter's keyless, credential-free contract — no signup, no API key). Raises the
+    explicit ``UniverseFetchError`` for any transport failure or non-200 response — never a
+    cached or fabricated fallback page (T-1). Lazy ``httpx`` import mirrors the adapters' own
+    lazy-SDK-import discipline (this function is the only code path that pays its cost)."""
+    import httpx
+
+    try:
+        response = httpx.get(
+            source_url,
+            timeout=timeout,
+            follow_redirects=True,
+            headers={"User-Agent": _FETCH_USER_AGENT},
+        )
+    except httpx.HTTPError as exc:
+        raise UniverseFetchError(f"could not reach '{source_url}': {exc}") from exc
+    if response.status_code != 200:
+        raise UniverseFetchError(
+            f"'{source_url}' returned HTTP {response.status_code} — refusing to parse an error page"
+        )
+    return response.text
+
+
+# --- parse (stdlib-only; no lxml/html5lib/beautifulsoup4/pandas.read_html) -------------------------
+
+
+class _TableExtractor(HTMLParser):
+    """Extracts every top-level ``<table>`` on the page as a list of rows, each row a list of
+    cell text strings (``<td>``/``<th>`` treated uniformly, so a header row of ``<th>`` cells and
+    a data row of ``<td>`` cells both come out as plain text rows). A table NESTED inside another
+    table's cell contributes nothing to either table (``_table_depth`` guards every row/cell
+    event to depth 1) — the real Wikipedia constituents table is not nested, and this keeps the
+    extractor a simple, honest reflection of stdlib-only parsing rather than a general HTML-table
+    library. All text nodes encountered while inside a cell are concatenated (so a ticker wrapped
+    in ``<a href="...">AAPL</a>`` — the real Wikipedia markup — is read correctly) and only
+    stripped once, at cell-close, so incidental inter-tag whitespace collapses naturally."""
+
+    def __init__(self) -> None:
+        super().__init__(convert_charrefs=True)
+        self.tables: list[list[list[str]]] = []
+        self._table_depth = 0
+        self._current_table: list[list[str]] | None = None
+        self._current_row: list[str] | None = None
+        self._current_cell: list[str] | None = None
+        self._in_cell = False
+
+    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
+        if tag == "table":
+            self._table_depth += 1
+            if self._table_depth == 1:
+                self._current_table = []
+        elif tag == "tr" and self._table_depth == 1 and self._current_table is not None:
+            self._current_row = []
+        elif tag in ("td", "th") and self._table_depth == 1 and self._current_row is not None:
+            self._current_cell = []
+            self._in_cell = True
+
+    def handle_endtag(self, tag: str) -> None:
+        if tag in ("td", "th") and self._in_cell:
+            assert self._current_row is not None and self._current_cell is not None
+            self._current_row.append("".join(self._current_cell).strip())
+            self._current_cell = None
+            self._in_cell = False
+        elif tag == "tr" and self._table_depth == 1 and self._current_row is not None:
+            assert self._current_table is not None
+            if self._current_row:
+                self._current_table.append(self._current_row)
+            self._current_row = None
+        elif tag == "table":
+            if self._table_depth == 1 and self._current_table is not None:
+                self.tables.append(self._current_table)
+                self._current_table = None
+            self._table_depth = max(0, self._table_depth - 1)
+
+    def handle_data(self, data: str) -> None:
+        if self._in_cell:
+            assert self._current_cell is not None
+            self._current_cell.append(data)
+
+
+def _extract_tables(html: str) -> list[list[list[str]]]:
+    parser = _TableExtractor()
+    parser.feed(html)
+    return parser.tables
+
+
+def _find_symbol_column(tables: list[list[list[str]]]) -> tuple[list[list[str]], int] | None:
+    """The first table (document order) whose header row names a Symbol/Ticker column — never a
+    hardcoded column index, so a harmless reordering of the real page's columns cannot silently
+    misread a different field as the ticker. Returns ``(data_rows, symbol_column_index)`` or
+    ``None`` if no table has a recognizable column (an honest table-shape failure, T-1)."""
+    for table in tables:
+        if not table:
+            continue
+        header = [cell.strip().lower() for cell in table[0]]
+        for name in _SYMBOL_HEADER_NAMES:
+            if name in header:
+                return table[1:], header.index(name)
+    return None
+
+
+def parse_constituents(html: str, *, min_members: int, max_members: int) -> ParsedUniverse:
+    """Parse, validate, and normalize a constituents page's raw HTML into a ``ParsedUniverse``.
+    Stdlib-only (``html.parser.HTMLParser`` — no ``lxml``/``html5lib``/``beautifulsoup4``/
+    ``pandas.read_html``, none of which are declared dependencies of this project).
+
+    Every failure is a distinct, honest ``UniverseValidationError`` naming the specific problem —
+    never a partial or guessed list (T-1):
+      * no table carries a recognizable Symbol/Ticker column (the page structure changed);
+      * the table yields zero tickers;
+      * ANY raw ticker fails the ``[A-Z.-]{1,6}`` charset check after normalization (the WHOLE
+        fetch is refused, never a per-row skip that would silently shrink the list);
+      * the final (deduped) member count falls outside ``[min_members, max_members]``.
+
+    Normalization (T-2): Yahoo's dash convention is applied to every raw ticker
+    (``BRK.B -> BRK-B``, ``BF.B -> BF-B``) before the charset check and before dedup — the raw
+    form (as it appeared on the page) is retained per normalized ticker in ``raw_members``.
+    """
+    tables = _extract_tables(html)
+    found = _find_symbol_column(tables)
+    if found is None:
+        raise UniverseValidationError(
+            "could not find a constituents table with a 'Symbol' (or 'Ticker') column — the "
+            "page structure may have changed"
+        )
+    rows, symbol_col = found
+
+    raw_tickers: list[str] = []
+    for row in rows:
+        if symbol_col >= len(row):
+            continue  # a short/malformed row (e.g. a spanning footnote row) — not a ticker itself
+        raw = _CITATION_RE.sub("", row[symbol_col]).strip()
+        if raw:
+            raw_tickers.append(raw)
+
+    if not raw_tickers:
+        raise UniverseValidationError(
+            "the constituents table yielded zero tickers — refusing an empty list"
+        )
+
+    normalized_to_raw: dict[str, str] = {}
+    for raw in raw_tickers:
+        normalized = raw.replace(".", "-").upper()
+        if not _TICKER_RE.match(normalized):
+            raise UniverseValidationError(
+                f"ticker '{raw}' (normalized '{normalized}') fails the charset check "
+                f"[A-Z.-]{{1,6}} — refusing the whole fetch, never a partial list"
+            )
+        normalized_to_raw.setdefault(normalized, raw)
+
+    member_count = len(normalized_to_raw)
+    if not (min_members <= member_count <= max_members):
+        raise UniverseValidationError(
+            f"parsed {member_count} members, outside the expected [{min_members}, {max_members}] "
+            f"range — refusing a suspiciously sized list"
+        )
+
+    members = sorted(normalized_to_raw)
+    return ParsedUniverse(members=members, raw_members=normalized_to_raw)
+
+
+# --- the store (frozen JSON, one file per snapshot, structurally immutable) ------------------------
+
+
+class UniverseStore:
+    """File-based store rooted at the config-owned universe directory — the ONE reader/writer.
+
+    Construction is cheap (no I/O); the directory is created on the first ``record``. Mirrors
+    ``bars.py``/``datasets.py``: every load verifies a whole-record checksum
+    (``UniverseIntegrityError`` on any mismatch); the only mutation, ``record``, refuses content
+    already registered (``UniverseAlreadyRegistered``)."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    @property
+    def root(self) -> Path:
+        return self._root
+
+    def _path(self, snapshot_id: str) -> Path:
+        return self._root / f"{snapshot_id}.json"
+
+    def _load(self, path: Path) -> dict:
+        """Load ONE snapshot file, verifying its whole-record checksum. Raises
+        ``UniverseIntegrityError`` for any parse/shape/checksum failure — explicit, never
+        silent."""
+        try:
+            data = json.loads(path.read_text())
+        except (OSError, ValueError) as exc:
+            raise UniverseIntegrityError(
+                f"universe snapshot file '{path.name}' is not parseable ({exc}) — corrupted or "
+                f"tampered"
+            ) from exc
+        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
+            raise UniverseIntegrityError(
+                f"universe snapshot file '{path.name}' does not carry the expected record shape "
+                f"— corrupted or tampered"
+            )
+        record = data["record"]
+        if _sha256(_canonical(record)) != data["file_checksum"]:
+            raise UniverseIntegrityError(
+                f"universe snapshot file '{path.name}' failed its integrity check (checksum "
+                f"mismatch) — the file was corrupted or tampered with"
+            )
+        meta = record.get("meta")
+        if not isinstance(meta, dict):
+            raise UniverseIntegrityError(
+                f"universe snapshot file '{path.name}' does not carry the expected record shape "
+                f"— corrupted or tampered"
+            )
+        return meta
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        """Every registered snapshot's metadata + membership (each file verified), oldest first,
+        plus an EXPLICIT error row per file that failed verification — a corrupt file is
+        surfaced, never silently hidden and never served as data. Fresh copies of the nested
+        ``members``/``raw_members`` fields on every call, so a caller mutating a returned record
+        can never poison a later read (the ``bars.py`` per-row-copy discipline)."""
+        if not self._root.exists():
+            return [], []
+        records: list[dict] = []
+        errors: list[dict] = []
+        for path in sorted(self._root.glob("*.json")):
+            try:
+                meta = self._load(path)
+                records.append(
+                    {**meta, "members": list(meta["members"]), "raw_members": dict(meta["raw_members"])}
+                )
+            except UniverseIntegrityError as exc:
+                errors.append({"file": path.name, "error": str(exc)})
+        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
+        return records, errors
+
+    def record(
+        self,
+        *,
+        members: list[str],
+        raw_members: dict[str, str],
+        source_url: str,
+        min_members: int,
+        max_members: int,
+    ) -> dict:
+        """Persist ONE new universe snapshot (record + register in a single explicit action).
+        Content already registered raises the 409-style ``UniverseAlreadyRegistered`` (there is
+        no update/re-record path at all — immutability is structural). ``source_url``,
+        ``min_members``, ``max_members`` are the exact Path-A Config values used at THIS
+        registration, embedded verbatim into the stored/served payload (provenance duty)."""
... [diff_bound] apps/backend/app/research/desk_universe.py: 25 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/fixtures/universe/sp100_constituents.html b/apps/backend/tests/fixtures/universe/sp100_constituents.html
new file mode 100644
index 0000000..da9b9aa
--- /dev/null
+++ b/apps/backend/tests/fixtures/universe/sp100_constituents.html
@@ -0,0 +1,640 @@
+<!DOCTYPE html>
+<html lang="en">
+<head><meta charset="UTF-8"><title>S&amp;P 100 - Wikipedia</title></head>
+<body>
+<div id="mw-content-text">
+<h2><span class="mw-headline" id="Components">Components</span></h2>
+<p>The S&amp;P 100 component stocks are (fixture, not a live capture):</p>
+<table class="wikitable sortable" id="constituents">
+  <thead>
+    <tr>
+      <th>No.</th>
+      <th>Company</th>
+      <th>Symbol</th>
+      <th>GICS Sector</th>
+    </tr>
+  </thead>
+  <tbody>
+    <tr>
+      <td>1</td>
+      <td><a href="/wiki/Apple_Inc." title="Apple Inc.">Apple Inc.</a></td>
+      <td><a href="/wiki/AAPL" class="external text">AAPL</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>2</td>
+      <td><a href="/wiki/AbbVie_Inc." title="AbbVie Inc.">AbbVie Inc.</a></td>
+      <td><a href="/wiki/ABBV" class="external text">ABBV</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>3</td>
+      <td><a href="/wiki/Abbott_Laboratories" title="Abbott Laboratories">Abbott Laboratories</a></td>
+      <td><a href="/wiki/ABT" class="external text">ABT</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>4</td>
+      <td><a href="/wiki/Accenture_plc" title="Accenture plc">Accenture plc</a></td>
+      <td><a href="/wiki/ACN" class="external text">ACN</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>5</td>
+      <td><a href="/wiki/Adobe_Inc." title="Adobe Inc.">Adobe Inc.</a></td>
+      <td><a href="/wiki/ADBE" class="external text">ADBE</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>6</td>
+      <td><a href="/wiki/American_International_Group" title="American International Group">American International Group</a></td>
+      <td><a href="/wiki/AIG" class="external text">AIG</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>7</td>
+      <td><a href="/wiki/Advanced_Micro_Devices" title="Advanced Micro Devices">Advanced Micro Devices</a></td>
+      <td><a href="/wiki/AMD" class="external text">AMD</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>8</td>
+      <td><a href="/wiki/Amgen_Inc." title="Amgen Inc.">Amgen Inc.</a></td>
+      <td><a href="/wiki/AMGN" class="external text">AMGN</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>9</td>
+      <td><a href="/wiki/American_Tower_Corporation" title="American Tower Corporation">American Tower Corporation</a></td>
+      <td><a href="/wiki/AMT" class="external text">AMT</a></td>
+      <td>Real Estate</td>
+    </tr>
+    <tr>
+      <td>10</td>
+      <td><a href="/wiki/Amazon.com_Inc." title="Amazon.com Inc.">Amazon.com Inc.</a></td>
+      <td><a href="/wiki/AMZN" class="external text">AMZN</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>11</td>
+      <td><a href="/wiki/Broadcom_Inc." title="Broadcom Inc.">Broadcom Inc.</a></td>
+      <td><a href="/wiki/AVGO" class="external text">AVGO</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>12</td>
+      <td><a href="/wiki/American_Express_Company" title="American Express Company">American Express Company</a></td>
+      <td><a href="/wiki/AXP" class="external text">AXP</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>13</td>
+      <td><a href="/wiki/The_Boeing_Company" title="The Boeing Company">The Boeing Company</a></td>
+      <td><a href="/wiki/BA" class="external text">BA</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>14</td>
+      <td><a href="/wiki/Bank_of_America_Corp" title="Bank of America Corp">Bank of America Corp</a></td>
+      <td><a href="/wiki/BAC" class="external text">BAC</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>15</td>
+      <td><a href="/wiki/The_Bank_of_New_York_Mellon" title="The Bank of New York Mellon">The Bank of New York Mellon</a></td>
+      <td><a href="/wiki/BK" class="external text">BK</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>16</td>
+      <td><a href="/wiki/Booking_Holdings_Inc." title="Booking Holdings Inc.">Booking Holdings Inc.</a></td>
+      <td><a href="/wiki/BKNG" class="external text">BKNG</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>17</td>
+      <td><a href="/wiki/BlackRock_Inc." title="BlackRock Inc.">BlackRock Inc.</a></td>
+      <td><a href="/wiki/BLK" class="external text">BLK</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>18</td>
+      <td><a href="/wiki/Bristol-Myers_Squibb" title="Bristol-Myers Squibb">Bristol-Myers Squibb</a></td>
+      <td><a href="/wiki/BMY" class="external text">BMY</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>19</td>
+      <td><a href="/wiki/Berkshire_Hathaway" title="Berkshire Hathaway">Berkshire Hathaway</a></td>
+      <td><a href="/wiki/BRK.B" class="external text">BRK.B</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>20</td>
+      <td><a href="/wiki/Citigroup_Inc." title="Citigroup Inc.">Citigroup Inc.</a></td>
+      <td><a href="/wiki/C" class="external text">C</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>21</td>
+      <td><a href="/wiki/Caterpillar_Inc." title="Caterpillar Inc.">Caterpillar Inc.</a></td>
+      <td><a href="/wiki/CAT" class="external text">CAT</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>22</td>
+      <td><a href="/wiki/Charter_Communications" title="Charter Communications">Charter Communications</a></td>
+      <td><a href="/wiki/CHTR" class="external text">CHTR</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>23</td>
+      <td><a href="/wiki/Colgate-Palmolive_Company" title="Colgate-Palmolive Company">Colgate-Palmolive Company</a></td>
+      <td><a href="/wiki/CL" class="external text">CL</a></td>
+      <td>Consumer Staples</td>
+    </tr>
+    <tr>
+      <td>24</td>
+      <td><a href="/wiki/Comcast_Corporation" title="Comcast Corporation">Comcast Corporation</a></td>
+      <td><a href="/wiki/CMCSA" class="external text">CMCSA</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>25</td>
+      <td><a href="/wiki/Capital_One_Financial" title="Capital One Financial">Capital One Financial</a></td>
+      <td><a href="/wiki/COF" class="external text">COF</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>26</td>
+      <td><a href="/wiki/ConocoPhillips" title="ConocoPhillips">ConocoPhillips</a></td>
+      <td><a href="/wiki/COP" class="external text">COP</a></td>
+      <td>Energy</td>
+    </tr>
+    <tr>
+      <td>27</td>
+      <td><a href="/wiki/Costco_Wholesale_Corp" title="Costco Wholesale Corp">Costco Wholesale Corp</a></td>
+      <td><a href="/wiki/COST" class="external text">COST</a></td>
+      <td>Consumer Staples</td>
+    </tr>
+    <tr>
+      <td>28</td>
+      <td><a href="/wiki/Salesforce_Inc." title="Salesforce Inc.">Salesforce Inc.</a></td>
+      <td><a href="/wiki/CRM" class="external text">CRM</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>29</td>
+      <td><a href="/wiki/Cisco_Systems_Inc." title="Cisco Systems Inc.">Cisco Systems Inc.</a></td>
+      <td><a href="/wiki/CSCO" class="external text">CSCO</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>30</td>
+      <td><a href="/wiki/CVS_Health_Corporation" title="CVS Health Corporation">CVS Health Corporation</a></td>
+      <td><a href="/wiki/CVS" class="external text">CVS</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>31</td>
+      <td><a href="/wiki/Chevron_Corporation" title="Chevron Corporation">Chevron Corporation</a></td>
+      <td><a href="/wiki/CVX" class="external text">CVX</a></td>
+      <td>Energy</td>
+    </tr>
+    <tr>
+      <td>32</td>
+      <td><a href="/wiki/Deere_%26_Company" title="Deere & Company">Deere & Company</a></td>
+      <td><a href="/wiki/DE" class="external text">DE</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>33</td>
+      <td><a href="/wiki/Danaher_Corporation" title="Danaher Corporation">Danaher Corporation</a></td>
+      <td><a href="/wiki/DHR" class="external text">DHR</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>34</td>
+      <td><a href="/wiki/The_Walt_Disney_Company" title="The Walt Disney Company">The Walt Disney Company</a></td>
+      <td><a href="/wiki/DIS" class="external text">DIS</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>35</td>
+      <td><a href="/wiki/Dow_Inc." title="Dow Inc.">Dow Inc.</a></td>
+      <td><a href="/wiki/DOW" class="external text">DOW</a></td>
+      <td>Materials</td>
+    </tr>
+    <tr>
+      <td>36</td>
+      <td><a href="/wiki/Duke_Energy_Corporation" title="Duke Energy Corporation">Duke Energy Corporation</a></td>
+      <td><a href="/wiki/DUK" class="external text">DUK</a></td>
+      <td>Utilities</td>
+    </tr>
+    <tr>
+      <td>37</td>
+      <td><a href="/wiki/Emerson_Electric_Co." title="Emerson Electric Co.">Emerson Electric Co.</a></td>
+      <td><a href="/wiki/EMR" class="external text">EMR</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>38</td>
+      <td><a href="/wiki/Ford_Motor_Company" title="Ford Motor Company">Ford Motor Company</a></td>
+      <td><a href="/wiki/F" class="external text">F</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>39</td>
+      <td><a href="/wiki/FedEx_Corporation" title="FedEx Corporation">FedEx Corporation</a></td>
+      <td><a href="/wiki/FDX" class="external text">FDX</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>40</td>
+      <td><a href="/wiki/General_Dynamics_Corp" title="General Dynamics Corp">General Dynamics Corp</a></td>
+      <td><a href="/wiki/GD" class="external text">GD</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>41</td>
+      <td><a href="/wiki/General_Electric_Company" title="General Electric Company">General Electric Company</a></td>
+      <td><a href="/wiki/GE" class="external text">GE</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>42</td>
+      <td><a href="/wiki/Gilead_Sciences_Inc." title="Gilead Sciences Inc.">Gilead Sciences Inc.</a></td>
+      <td><a href="/wiki/GILD" class="external text">GILD</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>43</td>
+      <td><a href="/wiki/General_Motors_Company" title="General Motors Company">General Motors Company</a></td>
+      <td><a href="/wiki/GM" class="external text">GM</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>44</td>
+      <td><a href="/wiki/Alphabet_Inc._(Class_C)" title="Alphabet Inc. (Class C)">Alphabet Inc. (Class C)</a></td>
+      <td><a href="/wiki/GOOG" class="external text">GOOG</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>45</td>
+      <td><a href="/wiki/Alphabet_Inc._(Class_A)" title="Alphabet Inc. (Class A)">Alphabet Inc. (Class A)</a></td>
+      <td><a href="/wiki/GOOGL" class="external text">GOOGL</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>46</td>
+      <td><a href="/wiki/The_Goldman_Sachs_Group" title="The Goldman Sachs Group">The Goldman Sachs Group</a></td>
+      <td><a href="/wiki/GS" class="external text">GS</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>47</td>
+      <td><a href="/wiki/The_Home_Depot_Inc." title="The Home Depot Inc.">The Home Depot Inc.</a></td>
+      <td><a href="/wiki/HD" class="external text">HD</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>48</td>
+      <td><a href="/wiki/Honeywell_International" title="Honeywell International">Honeywell International</a></td>
+      <td><a href="/wiki/HON" class="external text">HON</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>49</td>
+      <td><a href="/wiki/International_Business_Machines" title="International Business Machines">International Business Machines</a></td>
+      <td><a href="/wiki/IBM" class="external text">IBM</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>50</td>
+      <td><a href="/wiki/Intel_Corporation" title="Intel Corporation">Intel Corporation</a></td>
+      <td><a href="/wiki/INTC" class="external text">INTC</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>51</td>
+      <td><a href="/wiki/Intuit_Inc." title="Intuit Inc.">Intuit Inc.</a></td>
+      <td><a href="/wiki/INTU" class="external text">INTU</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>52</td>
+      <td><a href="/wiki/Intuitive_Surgical_Inc." title="Intuitive Surgical Inc.">Intuitive Surgical Inc.</a></td>
+      <td><a href="/wiki/ISRG" class="external text">ISRG</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>53</td>
+      <td><a href="/wiki/Johnson_%26_Johnson" title="Johnson & Johnson">Johnson & Johnson</a></td>
+      <td><a href="/wiki/JNJ" class="external text">JNJ</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>54</td>
+      <td><a href="/wiki/JPMorgan_Chase_%26_Co." title="JPMorgan Chase & Co.">JPMorgan Chase & Co.</a></td>
+      <td><a href="/wiki/JPM" class="external text">JPM</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>55</td>
+      <td><a href="/wiki/The_Kraft_Heinz_Company" title="The Kraft Heinz Company">The Kraft Heinz Company</a></td>
+      <td><a href="/wiki/KHC" class="external text">KHC</a></td>
+      <td>Consumer Staples</td>
+    </tr>
+    <tr>
+      <td>56</td>
+      <td><a href="/wiki/The_Coca-Cola_Company" title="The Coca-Cola Company">The Coca-Cola Company</a></td>
+      <td><a href="/wiki/KO" class="external text">KO</a></td>
+      <td>Consumer Staples</td>
+    </tr>
+    <tr>
+      <td>57</td>
+      <td><a href="/wiki/Linde_plc" title="Linde plc">Linde plc</a></td>
+      <td><a href="/wiki/LIN" class="external text">LIN</a></td>
+      <td>Materials</td>
+    </tr>
+    <tr>
+      <td>58</td>
+      <td><a href="/wiki/Eli_Lilly_and_Company" title="Eli Lilly and Company">Eli Lilly and Company</a></td>
+      <td><a href="/wiki/LLY" class="external text">LLY</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>59</td>
+      <td><a href="/wiki/Lockheed_Martin_Corp" title="Lockheed Martin Corp">Lockheed Martin Corp</a></td>
+      <td><a href="/wiki/LMT" class="external text">LMT</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>60</td>
+      <td><a href="/wiki/Lowe's_Companies_Inc." title="Lowe's Companies Inc.">Lowe's Companies Inc.</a></td>
+      <td><a href="/wiki/LOW" class="external text">LOW</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>61</td>
+      <td><a href="/wiki/Mastercard_Incorporated" title="Mastercard Incorporated">Mastercard Incorporated</a></td>
+      <td><a href="/wiki/MA" class="external text">MA</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>62</td>
+      <td><a href="/wiki/McDonald's_Corporation" title="McDonald's Corporation">McDonald's Corporation</a></td>
+      <td><a href="/wiki/MCD" class="external text">MCD</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>63</td>
+      <td><a href="/wiki/Mondelez_International" title="Mondelez International">Mondelez International</a></td>
+      <td><a href="/wiki/MDLZ" class="external text">MDLZ</a></td>
+      <td>Consumer Staples</td>
... [diff_bound] apps/backend/tests/fixtures/universe/sp100_constituents.html: 246 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/fixtures/universe/sp100_constituents_corrupted.html b/apps/backend/tests/fixtures/universe/sp100_constituents_corrupted.html
new file mode 100644
index 0000000..7dcfe8d
--- /dev/null
+++ b/apps/backend/tests/fixtures/universe/sp100_constituents_corrupted.html
@@ -0,0 +1,640 @@
+<!DOCTYPE html>
+<html lang="en">
+<head><meta charset="UTF-8"><title>S&amp;P 100 - Wikipedia</title></head>
+<body>
+<div id="mw-content-text">
+<h2><span class="mw-headline" id="Components">Components</span></h2>
+<p>The S&amp;P 100 component stocks are (fixture, not a live capture):</p>
+<table class="wikitable sortable" id="constituents">
+  <thead>
+    <tr>
+      <th>No.</th>
+      <th>Company</th>
+      <th>Symbol</th>
+      <th>GICS Sector</th>
+    </tr>
+  </thead>
+  <tbody>
+    <tr>
+      <td>1</td>
+      <td><a href="/wiki/Apple_Inc." title="Apple Inc.">Apple Inc.</a></td>
+      <td><a href="/wiki/AAPL" class="external text">AAPL</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>2</td>
+      <td><a href="/wiki/AbbVie_Inc." title="AbbVie Inc.">AbbVie Inc.</a></td>
+      <td><a href="/wiki/ABBV" class="external text">ABBV</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>3</td>
+      <td><a href="/wiki/Abbott_Laboratories" title="Abbott Laboratories">Abbott Laboratories</a></td>
+      <td><a href="/wiki/ABT" class="external text">ABT</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>4</td>
+      <td><a href="/wiki/Accenture_plc" title="Accenture plc">Accenture plc</a></td>
+      <td><a href="/wiki/ACN" class="external text">ACN</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>5</td>
+      <td><a href="/wiki/Adobe_Inc." title="Adobe Inc.">Adobe Inc.</a></td>
+      <td><a href="/wiki/ADBE" class="external text">ADBE</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>6</td>
+      <td><a href="/wiki/American_International_Group" title="American International Group">American International Group</a></td>
+      <td><a href="/wiki/AIG" class="external text">AIG</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>7</td>
+      <td><a href="/wiki/Advanced_Micro_Devices" title="Advanced Micro Devices">Advanced Micro Devices</a></td>
+      <td><a href="/wiki/AMD" class="external text">AMD</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>8</td>
+      <td><a href="/wiki/Amgen_Inc." title="Amgen Inc.">Amgen Inc.</a></td>
+      <td><a href="/wiki/AMGN" class="external text">AMGN</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>9</td>
+      <td><a href="/wiki/American_Tower_Corporation" title="American Tower Corporation">American Tower Corporation</a></td>
+      <td><a href="/wiki/AMT" class="external text">AMT</a></td>
+      <td>Real Estate</td>
+    </tr>
+    <tr>
+      <td>10</td>
+      <td><a href="/wiki/Amazon.com_Inc." title="Amazon.com Inc.">Amazon.com Inc.</a></td>
+      <td><a href="/wiki/AMZN" class="external text">AMZN</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>11</td>
+      <td><a href="/wiki/Broadcom_Inc." title="Broadcom Inc.">Broadcom Inc.</a></td>
+      <td><a href="/wiki/AVG1" class="external text">AVG1</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>12</td>
+      <td><a href="/wiki/American_Express_Company" title="American Express Company">American Express Company</a></td>
+      <td><a href="/wiki/AXP" class="external text">AXP</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>13</td>
+      <td><a href="/wiki/The_Boeing_Company" title="The Boeing Company">The Boeing Company</a></td>
+      <td><a href="/wiki/BA" class="external text">BA</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>14</td>
+      <td><a href="/wiki/Bank_of_America_Corp" title="Bank of America Corp">Bank of America Corp</a></td>
+      <td><a href="/wiki/BAC" class="external text">BAC</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>15</td>
+      <td><a href="/wiki/The_Bank_of_New_York_Mellon" title="The Bank of New York Mellon">The Bank of New York Mellon</a></td>
+      <td><a href="/wiki/BK" class="external text">BK</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>16</td>
+      <td><a href="/wiki/Booking_Holdings_Inc." title="Booking Holdings Inc.">Booking Holdings Inc.</a></td>
+      <td><a href="/wiki/BKNG" class="external text">BKNG</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>17</td>
+      <td><a href="/wiki/BlackRock_Inc." title="BlackRock Inc.">BlackRock Inc.</a></td>
+      <td><a href="/wiki/BLK" class="external text">BLK</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>18</td>
+      <td><a href="/wiki/Bristol-Myers_Squibb" title="Bristol-Myers Squibb">Bristol-Myers Squibb</a></td>
+      <td><a href="/wiki/BMY" class="external text">BMY</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>19</td>
+      <td><a href="/wiki/Berkshire_Hathaway" title="Berkshire Hathaway">Berkshire Hathaway</a></td>
+      <td><a href="/wiki/BRK.B" class="external text">BRK.B</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>20</td>
+      <td><a href="/wiki/Citigroup_Inc." title="Citigroup Inc.">Citigroup Inc.</a></td>
+      <td><a href="/wiki/C" class="external text">C</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>21</td>
+      <td><a href="/wiki/Caterpillar_Inc." title="Caterpillar Inc.">Caterpillar Inc.</a></td>
+      <td><a href="/wiki/CAT" class="external text">CAT</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>22</td>
+      <td><a href="/wiki/Charter_Communications" title="Charter Communications">Charter Communications</a></td>
+      <td><a href="/wiki/CHTR" class="external text">CHTR</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>23</td>
+      <td><a href="/wiki/Colgate-Palmolive_Company" title="Colgate-Palmolive Company">Colgate-Palmolive Company</a></td>
+      <td><a href="/wiki/CL" class="external text">CL</a></td>
+      <td>Consumer Staples</td>
+    </tr>
+    <tr>
+      <td>24</td>
+      <td><a href="/wiki/Comcast_Corporation" title="Comcast Corporation">Comcast Corporation</a></td>
+      <td><a href="/wiki/CMCSA" class="external text">CMCSA</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>25</td>
+      <td><a href="/wiki/Capital_One_Financial" title="Capital One Financial">Capital One Financial</a></td>
+      <td><a href="/wiki/COF" class="external text">COF</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>26</td>
+      <td><a href="/wiki/ConocoPhillips" title="ConocoPhillips">ConocoPhillips</a></td>
+      <td><a href="/wiki/COP" class="external text">COP</a></td>
+      <td>Energy</td>
+    </tr>
+    <tr>
+      <td>27</td>
+      <td><a href="/wiki/Costco_Wholesale_Corp" title="Costco Wholesale Corp">Costco Wholesale Corp</a></td>
+      <td><a href="/wiki/COST" class="external text">COST</a></td>
+      <td>Consumer Staples</td>
+    </tr>
+    <tr>
+      <td>28</td>
+      <td><a href="/wiki/Salesforce_Inc." title="Salesforce Inc.">Salesforce Inc.</a></td>
+      <td><a href="/wiki/CRM" class="external text">CRM</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>29</td>
+      <td><a href="/wiki/Cisco_Systems_Inc." title="Cisco Systems Inc.">Cisco Systems Inc.</a></td>
+      <td><a href="/wiki/CSCO" class="external text">CSCO</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>30</td>
+      <td><a href="/wiki/CVS_Health_Corporation" title="CVS Health Corporation">CVS Health Corporation</a></td>
+      <td><a href="/wiki/CVS" class="external text">CVS</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>31</td>
+      <td><a href="/wiki/Chevron_Corporation" title="Chevron Corporation">Chevron Corporation</a></td>
+      <td><a href="/wiki/CVX" class="external text">CVX</a></td>
+      <td>Energy</td>
+    </tr>
+    <tr>
+      <td>32</td>
+      <td><a href="/wiki/Deere_%26_Company" title="Deere & Company">Deere & Company</a></td>
+      <td><a href="/wiki/DE" class="external text">DE</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>33</td>
+      <td><a href="/wiki/Danaher_Corporation" title="Danaher Corporation">Danaher Corporation</a></td>
+      <td><a href="/wiki/DHR" class="external text">DHR</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>34</td>
+      <td><a href="/wiki/The_Walt_Disney_Company" title="The Walt Disney Company">The Walt Disney Company</a></td>
+      <td><a href="/wiki/DIS" class="external text">DIS</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>35</td>
+      <td><a href="/wiki/Dow_Inc." title="Dow Inc.">Dow Inc.</a></td>
+      <td><a href="/wiki/DOW" class="external text">DOW</a></td>
+      <td>Materials</td>
+    </tr>
+    <tr>
+      <td>36</td>
+      <td><a href="/wiki/Duke_Energy_Corporation" title="Duke Energy Corporation">Duke Energy Corporation</a></td>
+      <td><a href="/wiki/DUK" class="external text">DUK</a></td>
+      <td>Utilities</td>
+    </tr>
+    <tr>
+      <td>37</td>
+      <td><a href="/wiki/Emerson_Electric_Co." title="Emerson Electric Co.">Emerson Electric Co.</a></td>
+      <td><a href="/wiki/EMR" class="external text">EMR</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>38</td>
+      <td><a href="/wiki/Ford_Motor_Company" title="Ford Motor Company">Ford Motor Company</a></td>
+      <td><a href="/wiki/F" class="external text">F</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>39</td>
+      <td><a href="/wiki/FedEx_Corporation" title="FedEx Corporation">FedEx Corporation</a></td>
+      <td><a href="/wiki/FDX" class="external text">FDX</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>40</td>
+      <td><a href="/wiki/General_Dynamics_Corp" title="General Dynamics Corp">General Dynamics Corp</a></td>
+      <td><a href="/wiki/GD" class="external text">GD</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>41</td>
+      <td><a href="/wiki/General_Electric_Company" title="General Electric Company">General Electric Company</a></td>
+      <td><a href="/wiki/GE" class="external text">GE</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>42</td>
+      <td><a href="/wiki/Gilead_Sciences_Inc." title="Gilead Sciences Inc.">Gilead Sciences Inc.</a></td>
+      <td><a href="/wiki/GILD" class="external text">GILD</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>43</td>
+      <td><a href="/wiki/General_Motors_Company" title="General Motors Company">General Motors Company</a></td>
+      <td><a href="/wiki/GM" class="external text">GM</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>44</td>
+      <td><a href="/wiki/Alphabet_Inc._(Class_C)" title="Alphabet Inc. (Class C)">Alphabet Inc. (Class C)</a></td>
+      <td><a href="/wiki/GOOG" class="external text">GOOG</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>45</td>
+      <td><a href="/wiki/Alphabet_Inc._(Class_A)" title="Alphabet Inc. (Class A)">Alphabet Inc. (Class A)</a></td>
+      <td><a href="/wiki/GOOGL" class="external text">GOOGL</a></td>
+      <td>Communication Services</td>
+    </tr>
+    <tr>
+      <td>46</td>
+      <td><a href="/wiki/The_Goldman_Sachs_Group" title="The Goldman Sachs Group">The Goldman Sachs Group</a></td>
+      <td><a href="/wiki/GS" class="external text">GS</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>47</td>
+      <td><a href="/wiki/The_Home_Depot_Inc." title="The Home Depot Inc.">The Home Depot Inc.</a></td>
+      <td><a href="/wiki/HD" class="external text">HD</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>48</td>
+      <td><a href="/wiki/Honeywell_International" title="Honeywell International">Honeywell International</a></td>
+      <td><a href="/wiki/HON" class="external text">HON</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>49</td>
+      <td><a href="/wiki/International_Business_Machines" title="International Business Machines">International Business Machines</a></td>
+      <td><a href="/wiki/IBM" class="external text">IBM</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>50</td>
+      <td><a href="/wiki/Intel_Corporation" title="Intel Corporation">Intel Corporation</a></td>
+      <td><a href="/wiki/INTC" class="external text">INTC</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>51</td>
+      <td><a href="/wiki/Intuit_Inc." title="Intuit Inc.">Intuit Inc.</a></td>
+      <td><a href="/wiki/INTU" class="external text">INTU</a></td>
+      <td>Information Technology</td>
+    </tr>
+    <tr>
+      <td>52</td>
+      <td><a href="/wiki/Intuitive_Surgical_Inc." title="Intuitive Surgical Inc.">Intuitive Surgical Inc.</a></td>
+      <td><a href="/wiki/ISRG" class="external text">ISRG</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>53</td>
+      <td><a href="/wiki/Johnson_%26_Johnson" title="Johnson & Johnson">Johnson & Johnson</a></td>
+      <td><a href="/wiki/JNJ" class="external text">JNJ</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>54</td>
+      <td><a href="/wiki/JPMorgan_Chase_%26_Co." title="JPMorgan Chase & Co.">JPMorgan Chase & Co.</a></td>
+      <td><a href="/wiki/JPM" class="external text">JPM</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>55</td>
+      <td><a href="/wiki/The_Kraft_Heinz_Company" title="The Kraft Heinz Company">The Kraft Heinz Company</a></td>
+      <td><a href="/wiki/KHC" class="external text">KHC</a></td>
+      <td>Consumer Staples</td>
+    </tr>
+    <tr>
+      <td>56</td>
+      <td><a href="/wiki/The_Coca-Cola_Company" title="The Coca-Cola Company">The Coca-Cola Company</a></td>
+      <td><a href="/wiki/KO" class="external text">KO</a></td>
+      <td>Consumer Staples</td>
+    </tr>
+    <tr>
+      <td>57</td>
+      <td><a href="/wiki/Linde_plc" title="Linde plc">Linde plc</a></td>
+      <td><a href="/wiki/LIN" class="external text">LIN</a></td>
+      <td>Materials</td>
+    </tr>
+    <tr>
+      <td>58</td>
+      <td><a href="/wiki/Eli_Lilly_and_Company" title="Eli Lilly and Company">Eli Lilly and Company</a></td>
+      <td><a href="/wiki/LLY" class="external text">LLY</a></td>
+      <td>Health Care</td>
+    </tr>
+    <tr>
+      <td>59</td>
+      <td><a href="/wiki/Lockheed_Martin_Corp" title="Lockheed Martin Corp">Lockheed Martin Corp</a></td>
+      <td><a href="/wiki/LMT" class="external text">LMT</a></td>
+      <td>Industrials</td>
+    </tr>
+    <tr>
+      <td>60</td>
+      <td><a href="/wiki/Lowe's_Companies_Inc." title="Lowe's Companies Inc.">Lowe's Companies Inc.</a></td>
+      <td><a href="/wiki/LOW" class="external text">LOW</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>61</td>
+      <td><a href="/wiki/Mastercard_Incorporated" title="Mastercard Incorporated">Mastercard Incorporated</a></td>
+      <td><a href="/wiki/MA" class="external text">MA</a></td>
+      <td>Financials</td>
+    </tr>
+    <tr>
+      <td>62</td>
+      <td><a href="/wiki/McDonald's_Corporation" title="McDonald's Corporation">McDonald's Corporation</a></td>
+      <td><a href="/wiki/MCD" class="external text">MCD</a></td>
+      <td>Consumer Discretionary</td>
+    </tr>
+    <tr>
+      <td>63</td>
+      <td><a href="/wiki/Mondelez_International" title="Mondelez International">Mondelez International</a></td>
+      <td><a href="/wiki/MDLZ" class="external text">MDLZ</a></td>
+      <td>Consumer Staples</td>
... [diff_bound] apps/backend/tests/fixtures/universe/sp100_constituents_corrupted.html: 246 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json b/apps/backend/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json
new file mode 100644
index 0000000..12d47c5
--- /dev/null
+++ b/apps/backend/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json
@@ -0,0 +1 @@
+{"file_checksum": "4326602aa1f684895dd07503102b226bb540de9ad8289a1f3ffdb12e7f19cfe8", "record": {"meta": {"id": "universe-2026-07-25-817cc184bbb3", "date": "2026-07-25", "checksum": "817cc184bbb3", "member_count": 103, "source_url": "https://en.wikipedia.org/wiki/S%26P_100", "min_members": 90, "max_members": 110, "created_utc": "2026-07-25T03:17:52.011336Z", "members": ["AAPL", "ABBV", "ABT", "ACN", "ADBE", "AIG", "AMD", "AMGN", "AMT", "AMZN", "AVGO", "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "BRK-B", "C", "CAT", "CHTR", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS", "CVX", "DE", "DHR", "DIS", "DOW", "DUK", "EMR", "F", "FDX", "GD", "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON", "IBM", "INTC", "INTU", "ISRG", "JNJ", "JPM", "KHC", "KO", "LIN", "LLY", "LMT", "LOW", "MA", "MCD", "MDLZ", "MDT", "MET", "META", "MMM", "MO", "MRK", "MS", "MSFT", "NEE", "NFLX", "NKE", "NOW", "NVDA", "ORCL", "PEP", "PFE", "PG", "PM", "PYPL", "QCOM", "RTX", "SBUX", "SCHW", "SO", "SPG", "T", "TGT", "TMO", "TMUS", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC", "WMT", "XOM"], "raw_members": {"AAPL": "AAPL", "ABBV": "ABBV", "ABT": "ABT", "ACN": "ACN", "ADBE": "ADBE", "AIG": "AIG", "AMD": "AMD", "AMGN": "AMGN", "AMT": "AMT", "AMZN": "AMZN", "AVGO": "AVGO", "AXP": "AXP", "BA": "BA", "BAC": "BAC", "BK": "BK", "BKNG": "BKNG", "BLK": "BLK", "BMY": "BMY", "BRK-B": "BRK.B", "C": "C", "CAT": "CAT", "CHTR": "CHTR", "CL": "CL", "CMCSA": "CMCSA", "COF": "COF", "COP": "COP", "COST": "COST", "CRM": "CRM", "CSCO": "CSCO", "CVS": "CVS", "CVX": "CVX", "DE": "DE", "DHR": "DHR", "DIS": "DIS", "DOW": "DOW", "DUK": "DUK", "EMR": "EMR", "F": "F", "FDX": "FDX", "GD": "GD", "GE": "GE", "GILD": "GILD", "GM": "GM", "GOOG": "GOOG", "GOOGL": "GOOGL", "GS": "GS", "HD": "HD", "HON": "HON", "IBM": "IBM", "INTC": "INTC", "INTU": "INTU", "ISRG": "ISRG", "JNJ": "JNJ", "JPM": "JPM", "KHC": "KHC", "KO": "KO", "LIN": "LIN", "LLY": "LLY", "LMT": "LMT", "LOW": "LOW", "MA": "MA", "MCD": "MCD", "MDLZ": "MDLZ", "MDT": "MDT", "MET": "MET", "META": "META", "MMM": "MMM", "MO": "MO", "MRK": "MRK", "MS": "MS", "MSFT": "MSFT", "NEE": "NEE", "NFLX": "NFLX", "NKE": "NKE", "NOW": "NOW", "NVDA": "NVDA", "ORCL": "ORCL", "PEP": "PEP", "PFE": "PFE", "PG": "PG", "PM": "PM", "PYPL": "PYPL", "QCOM": "QCOM", "RTX": "RTX", "SBUX": "SBUX", "SCHW": "SCHW", "SO": "SO", "SPG": "SPG", "T": "T", "TGT": "TGT", "TMO": "TMO", "TMUS": "TMUS", "TSLA": "TSLA", "TXN": "TXN", "UNH": "UNH", "UNP": "UNP", "UPS": "UPS", "USB": "USB", "V": "V", "VZ": "VZ", "WFC": "WFC", "WMT": "WMT", "XOM": "XOM"}}}}
\ No newline at end of file
diff --git a/apps/backend/tests/test_desk_universe.py b/apps/backend/tests/test_desk_universe.py
new file mode 100644
index 0000000..a8ec0fc
--- /dev/null
+++ b/apps/backend/tests/test_desk_universe.py
@@ -0,0 +1,374 @@
+"""The universe snapshot store + parser contract (Era B "The Desk", Key Capability 1, J-01) —
+store-level discipline plus the stdlib-only HTML parser.
+
+Mirrors ``tests/test_bars.py`` / ``tests/test_datasets.py`` (the plan's own explicit directive):
+metadata correctness, structural immutability (no update/re-record path exists), verified loads
+(checksum), the honest failure taxonomy, and the ``desk_universe_*`` ``config_fingerprint``
+exclusions (the ``bar_dir``/``bar_timeframes`` precedent). Also covers the parser contract itself
+(charset, bounds, table-shape, normalization) as small, independently testable pure functions —
+the ``research/desk_universe.py`` module docstring's own discipline list.
+"""
+
+from __future__ import annotations
+
+import inspect
+import json
+import shutil
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG, Config
+import app.research.desk_universe as desk_universe
+from app.research.desk_universe import (
+    ParsedUniverse,
+    UniverseAlreadyRegistered,
+    UniverseIntegrityError,
+    UniverseStore,
+    UniverseValidationError,
+    parse_constituents,
+)
+
+FIXTURE_DIR = Path(__file__).parent / "fixtures" / "universe"
+VALID_HTML = (FIXTURE_DIR / "sp100_constituents.html").read_text()
+CORRUPTED_HTML = (FIXTURE_DIR / "sp100_constituents_corrupted.html").read_text()
+# "The fixture universe" (J-02–J-05's own naming) — the ONE committed, already-registered
+# snapshot produced by running the real registration path against ``VALID_HTML`` once.
+REGISTERED_SNAPSHOT_PATH = FIXTURE_DIR / "universe-2026-07-25-817cc184bbb3.json"
+
+SOURCE_URL = "https://en.wikipedia.org/wiki/S%26P_100"
+
+
+def _table_html(headers: list[str], rows: list[list[str]]) -> str:
+    """A minimal, hand-built table for edge cases the two committed fixtures don't need to carry
+    (no-symbol-column, out-of-bounds count, citation markers, column position) — deliberately
+    NOT using the big realistic fixture for these, so each edge case stays a small, obviously
+    correct table."""
+    head = "".join(f"<th>{h}</th>" for h in headers)
+    body = "".join(
+        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
+    )
+    return f"<html><body><table><tr>{head}</tr>{body}</table></body></html>"
+
+
+# --- parser contract: the valid, realistic fixture --------------------------------------------
+
+
+def test_parse_constituents_extracts_the_normalized_sorted_deduped_membership():
+    parsed = parse_constituents(VALID_HTML, min_members=90, max_members=110)
+    assert isinstance(parsed, ParsedUniverse)
+    assert len(parsed.members) == 103
+    assert parsed.members == sorted(parsed.members)
+    assert len(parsed.members) == len(set(parsed.members))  # no duplicates
+    assert parsed.members[:3] == ["AAPL", "ABBV", "ABT"]
+
+
+def test_parse_constituents_normalizes_dual_class_and_preserves_the_raw_form():
+    parsed = parse_constituents(VALID_HTML, min_members=90, max_members=110)
+    assert "BRK-B" in parsed.members
+    assert "BRK.B" not in parsed.members  # never the un-normalized form
+    assert parsed.raw_members["BRK-B"] == "BRK.B"  # T-2: raw form preserved in metadata
+
+
+def test_parse_constituents_raw_form_is_identity_for_a_non_dual_class_ticker():
+    parsed = parse_constituents(VALID_HTML, min_members=90, max_members=110)
+    assert parsed.raw_members["AAPL"] == "AAPL"
+
+
+def test_parse_constituents_finds_the_symbol_column_by_header_text_not_position():
+    """The committed fixture already puts Symbol in column index 2 (No./Company/Symbol/Sector).
+    This proves the SAME parser also works with Symbol in column 0 -- a header-name lookup, never
+    a hardcoded index."""
+    html = _table_html(["Symbol", "Company"], [["AAPL", "Apple Inc."], ["MSFT", "Microsoft"]])
+    parsed = parse_constituents(html, min_members=1, max_members=5)
+    assert parsed.members == ["AAPL", "MSFT"]
+
+
+def test_parse_constituents_accepts_a_ticker_header_as_well_as_symbol():
+    html = _table_html(["Ticker", "Company"], [["AAPL", "Apple Inc."]])
+    parsed = parse_constituents(html, min_members=1, max_members=5)
+    assert parsed.members == ["AAPL"]
+
+
+def test_parse_constituents_strips_a_footnote_citation_marker():
+    html = "<html><body><table><tr><th>Symbol</th></tr><tr><td>AAPL<sup>[1]</sup></td></tr></table></body></html>"
+    parsed = parse_constituents(html, min_members=1, max_members=5)
+    assert parsed.members == ["AAPL"]
+    assert parsed.raw_members["AAPL"] == "AAPL"
+
+
+def test_parse_constituents_skips_a_short_malformed_row_without_crashing():
+    """A row too short to reach the Symbol column (e.g. a spanning footnote/notes row rendered as
+    a single cell) is skipped -- not a ticker-charset failure, and never fabricated as an
+    empty/partial ticker. Symbol is column INDEX 1 here so a single-cell row (index 0 only)
+    genuinely falls short of it."""
+    html = _table_html(
+        ["No.", "Symbol", "Company"],
+        [["1", "AAPL", "Apple Inc."], ["(a note spanning the whole row)"], ["2", "MSFT", "Microsoft"]],
+    )
+    parsed = parse_constituents(html, min_members=1, max_members=5)
+    assert parsed.members == ["AAPL", "MSFT"]
+
+
+# --- parser contract: honest failure states (T-1) -----------------------------------------------
+
+
+def test_parse_constituents_rejects_a_charset_violating_ticker_and_names_it():
+    with pytest.raises(UniverseValidationError) as excinfo:
+        parse_constituents(CORRUPTED_HTML, min_members=90, max_members=110)
+    assert "AVG1" in str(excinfo.value)
+    assert "charset" in str(excinfo.value)
+
+
+def test_parse_constituents_rejects_a_member_count_below_the_minimum():
+    html = _table_html(["Symbol"], [["AAPL"], ["MSFT"], ["GOOG"]])
+    with pytest.raises(UniverseValidationError) as excinfo:
+        parse_constituents(html, min_members=90, max_members=110)
+    assert "3" in str(excinfo.value) and "90" in str(excinfo.value)
+
+
+def test_parse_constituents_rejects_a_member_count_above_the_maximum():
+    # The real, valid fixture (103 members) against artificially tight bounds -- "well outside
+    # 90-110" per the plan's own TC-4 wording, exercised from the OTHER direction.
+    with pytest.raises(UniverseValidationError) as excinfo:
+        parse_constituents(VALID_HTML, min_members=1, max_members=50)
+    assert "103" in str(excinfo.value) and "50" in str(excinfo.value)
+
+
+def test_parse_constituents_rejects_when_no_symbol_column_exists():
+    html = _table_html(["No.", "Company", "Sector"], [["1", "Apple Inc.", "Tech"]])
+    with pytest.raises(UniverseValidationError) as excinfo:
+        parse_constituents(html, min_members=1, max_members=110)
+    assert "Symbol" in str(excinfo.value)
+
+
+def test_parse_constituents_rejects_a_table_with_zero_data_rows():
+    html = _table_html(["Symbol", "Company"], [])
+    with pytest.raises(UniverseValidationError) as excinfo:
+        parse_constituents(html, min_members=1, max_members=110)
+    assert "zero tickers" in str(excinfo.value)
+
+
+def test_parse_constituents_rejects_garbage_html_with_no_table_at_all():
+    with pytest.raises(UniverseValidationError):
+        parse_constituents("<html><body><p>nothing here</p></body></html>", min_members=1, max_members=110)
+
+
+# --- store: record/list, metadata correctness ---------------------------------------------------
+
+
+def _record_fixture(store: UniverseStore, *, min_members: int = 90, max_members: int = 110) -> dict:
+    parsed = parse_constituents(VALID_HTML, min_members=min_members, max_members=max_members)
+    return store.record(
+        members=parsed.members,
+        raw_members=parsed.raw_members,
+        source_url=SOURCE_URL,
+        min_members=min_members,
+        max_members=max_members,
+    )
+
+
+def test_record_stores_correct_metadata_and_a_12char_checksum(tmp_path):
+    store = UniverseStore(tmp_path / "universe")
+    meta = _record_fixture(store)
+
+    assert meta["member_count"] == 103
+    assert isinstance(meta["checksum"], str) and len(meta["checksum"]) == 12
+    int(meta["checksum"], 16)  # hex, or this raises
+    assert meta["id"] == f"universe-{meta['date']}-{meta['checksum']}"
+    assert meta["created_utc"].endswith("Z")
+    assert meta["members"] == sorted(meta["members"])
+    assert "BRK-B" in meta["members"]
+    # The snapshot landed as ONE file in the configured universe dir.
+    assert len(list((tmp_path / "universe").glob("*.json"))) == 1
+
+
+def test_record_embeds_the_exact_config_values_used_at_registration(tmp_path):
+    """TC-10 at the store level (provenance duty): the three Path-A values used at THIS
+    registration are embedded verbatim in the served/stored payload."""
+    store = UniverseStore(tmp_path / "universe")
+    meta = _record_fixture(store, min_members=77, max_members=200)
+
+    assert meta["source_url"] == SOURCE_URL
+    assert meta["min_members"] == 77
+    assert meta["max_members"] == 200
+
+
+def test_list_serves_the_stored_record_verbatim_oldest_first(tmp_path):
+    store = UniverseStore(tmp_path / "universe")
+    recorded = _record_fixture(store)
+
+    records, errors = store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0] == recorded
+
+
+def test_store_survives_a_reload_from_disk(tmp_path):
+    root = tmp_path / "universe"
+    recorded = _record_fixture(UniverseStore(root))
+
+    reloaded = UniverseStore(root)
+    records, errors = reloaded.list()
+    assert errors == []
+    assert records == [recorded]
+
+
+# --- immutability (409-style refusal; no update/re-record path exists) --------------------------
+
+
+def test_rerecording_identical_membership_is_refused(tmp_path):
+    store = UniverseStore(tmp_path / "universe")
+    first = _record_fixture(store)
+
+    with pytest.raises(UniverseAlreadyRegistered) as excinfo:
+        _record_fixture(store)
+    assert excinfo.value.existing_id == first["id"]
+    assert len(list((tmp_path / "universe").glob("*.json"))) == 1  # no second file
+
+
+def test_rerecording_identical_membership_leaves_the_file_byte_unchanged(tmp_path):
+    universe_dir = tmp_path / "universe"
+    store = UniverseStore(universe_dir)
+    _record_fixture(store)
+    path = next(universe_dir.glob("*.json"))
+    before = path.read_bytes()
+
+    with pytest.raises(UniverseAlreadyRegistered):
+        _record_fixture(store)
+    assert path.read_bytes() == before
+
+
+def test_a_different_membership_registers_a_second_distinct_snapshot(tmp_path):
+    store = UniverseStore(tmp_path / "universe")
+    first = store.record(
+        members=["AAPL", "MSFT"], raw_members={"AAPL": "AAPL", "MSFT": "MSFT"},
+        source_url=SOURCE_URL, min_members=1, max_members=5,
+    )
+    second = store.record(
+        members=["AAPL", "GOOG"], raw_members={"AAPL": "AAPL", "GOOG": "GOOG"},
+        source_url=SOURCE_URL, min_members=1, max_members=5,
+    )
+    assert first["id"] != second["id"]
+    assert first["checksum"] != second["checksum"]
+    records, errors = store.list()
+    assert errors == []
+    assert {r["id"] for r in records} == {first["id"], second["id"]}
+
+
+# --- integrity: a corrupted file is explicit, never silent --------------------------------------
+
+
+def test_corrupted_snapshot_file_surfaces_explicitly_in_list_errors(tmp_path):
+    universe_dir = tmp_path / "universe"
+    store = UniverseStore(universe_dir)
+    _record_fixture(store)
+    path = next(universe_dir.glob("*.json"))
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["member_count"] = 999  # tamper -- file_checksum now disagrees
+    path.write_text(json.dumps(data))
+
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1
+    assert path.name == errors[0]["file"]
+    assert "integrity" in errors[0]["error"]
+
+
+def test_load_raises_universe_integrity_error_for_unparseable_json(tmp_path):
+    universe_dir = tmp_path / "universe"
+    universe_dir.mkdir(parents=True)
+    (universe_dir / "universe-2026-01-01-deadbeef0000.json").write_text("{not json")
+
+    store = UniverseStore(universe_dir)
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1
+
+
+# --- T-3 guard: the universe store never routes through the dataset store -----------------------
+
+
+def test_desk_universe_module_never_imports_the_dataset_store_surface():
+    """Grep-based (source-introspection) guard, mirroring ``test_backtests.py``'s
+    ``inspect.getsource`` precedent: ``desk_universe.py`` must never import
+    ``research/datasets.py``'s registration surface or ``DatasetStore`` (T-3) -- zero hits.
+    Checked against only the ACTUAL import statements (not the whole module source), since the
+    module's own docstring honestly names ``DatasetStore`` in prose while explaining this exact
+    discipline -- a whole-source substring scan would false-positive on its own documentation."""
+    src = inspect.getsource(desk_universe)
+    import_lines = "\n".join(
+        line for line in src.splitlines() if line.strip().startswith(("import ", "from "))
+    )
+    forbidden = ("DatasetStore", "record_from_source", "datasets")
+    for pattern in forbidden:
+        assert pattern not in import_lines, f"desk_universe.py must never import {pattern!r} (T-3)"
+
+
+# --- Path-A Config discipline: exclusion set, stability, counter-test, resolver -----------------
+
+
+def test_desk_universe_fields_are_excluded_from_config_fingerprint():
+    base = CONFIG.config_fingerprint()
+    changed = Config(
+        desk_universe_source_url="https://example.invalid/other-source",
+        desk_universe_min_members=1,
+        desk_universe_max_members=1000,
+        desk_universe_dir="/tmp/somewhere-else",
+    ).config_fingerprint()
+    assert changed == base
+    # Ground truth: the era-open pin (docs/goal.md). If this ever moves, every archived-era record
+    # has silently drifted -- the strongest guard against that.
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
+    assert Config().config_fingerprint() == "08e471b10130e1e2"
+
+
+def test_desk_universe_min_members_counter_test_changes_the_new_path_output():
+    """TC-9: raising ``desk_universe_min_members`` above the fixture's actual member count (103)
+    refuses the SAME valid fixture -- proving the field is genuinely live-wired into the parser's
+    output, independent of (and without moving) the fingerprint."""
+    with pytest.raises(UniverseValidationError):
+        parse_constituents(VALID_HTML, min_members=200, max_members=300)
+    # The fixture parses fine again at the real default bounds -- isolating the counter-test's
+    # effect to the overridden bounds alone.
+    parsed = parse_constituents(VALID_HTML, min_members=90, max_members=110)
+    assert len(parsed.members) == 103
+
+
+def test_desk_universe_dir_resolved_env_override(monkeypatch):
+    monkeypatch.delenv("TAPEOLOGY_DESK_UNIVERSE_DIR", raising=False)
+    default = Config()
+    assert default.desk_universe_dir_resolved() == default.desk_universe_dir
+
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", "/tmp/custom-universe-dir")
+    assert default.desk_universe_dir_resolved() == "/tmp/custom-universe-dir"
+
+
+# --- the committed fixture snapshot: "the fixture universe" J-02-J-05 will reuse by name --------
+
+
+def test_the_committed_fixture_snapshot_is_a_valid_already_registered_universe():
+    """A direct load of the COMMITTED registered-snapshot JSON (produced once by running the real
+    registration path against ``VALID_HTML`` -- see the module docstring / plan) — proves it is
+    exactly what a fresh ``store.record`` against the fixture HTML would produce, so future
+    iterations (J-02-J-05) can drop this file into a temp universe dir and call it
+    "the fixture universe" without re-running a fetch."""
+    assert REGISTERED_SNAPSHOT_PATH.exists(), "the committed fixture snapshot is missing"
+    data = json.loads(REGISTERED_SNAPSHOT_PATH.read_text())
+    meta = data["record"]["meta"]
+    assert meta["member_count"] == 103
+    assert 90 <= meta["member_count"] <= 110
+    assert "BRK-B" in meta["members"]
+    assert meta["source_url"] == SOURCE_URL
+
+
+def test_the_committed_fixture_snapshot_loads_cleanly_through_the_store(tmp_path):
+    universe_dir = tmp_path / "universe"
+    universe_dir.mkdir()
+    shutil.copy(REGISTERED_SNAPSHOT_PATH, universe_dir / REGISTERED_SNAPSHOT_PATH.name)
+
+    store = UniverseStore(universe_dir)
+    records, errors = store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0]["member_count"] == 103
diff --git a/apps/backend/tests/test_desk_universe_api.py b/apps/backend/tests/test_desk_universe_api.py
new file mode 100644
index 0000000..225e438
--- /dev/null
+++ b/apps/backend/tests/test_desk_universe_api.py
@@ -0,0 +1,246 @@
+"""The ``/research/desk/universe*`` endpoints (Era B "The Desk", J-01) — fetch/register, list.
+
+Exactly TWO routes exist (the plan's Product Shape): ``POST /research/desk/universe/fetch`` (the
+explicit operator research action — fetch -> parse -> validate -> register; recording is never
+ambient) and ``GET /research/desk/universe`` (snapshot list + latest membership; an explicit HTTP
+200 empty payload before any registration — never 404). Four states per the plan's Key Test
+Scenarios: empty / registered / corrupted-input / duplicate-input. Mirrors
+``test_bars_api.py``/``test_datasets_api.py``'s fixture-injection conventions, using
+``app.dependency_overrides`` on ``get_universe_fetcher`` (the ``get_market_adapter``/
+``FakeAdapter`` seam) so every test here makes ZERO real network calls.
+"""
+
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG, Config
+from app.main import app, manager
+import app.research.desk_routes as desk_routes
+from app.research.desk_routes import get_universe_fetcher, get_universe_store
+from app.research.desk_universe import UniverseFetchError
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+
+FIXTURE_DIR = Path(__file__).parent / "fixtures" / "universe"
+VALID_HTML = (FIXTURE_DIR / "sp100_constituents.html").read_text()
+CORRUPTED_HTML = (FIXTURE_DIR / "sp100_constituents_corrupted.html").read_text()
+
+SOURCE_URL = "https://en.wikipedia.org/wiki/S%26P_100"
+
+
+@pytest.fixture
+def ctx(tmp_path, monkeypatch):
+    universe_dir = tmp_path / "universe"
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(universe_dir))
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(store, CONFIG)
+    set_registry(registry)
+    with TestClient(app) as client:
+        yield client, universe_dir
+    for ticker in list(manager._engines.keys()):
+        manager.stop(ticker)
+    set_registry(None)
+    app.dependency_overrides.pop(get_universe_fetcher, None)
+    store.close()
+
+
+def _inject_fetcher(html: str = VALID_HTML, *, raises: Exception | None = None) -> list[str]:
+    """Overrides the universe-page HTML fetch with a scripted response — the
+    ``get_market_adapter``/``FakeAdapter`` seam, adapted for a single-callable dependency. Returns
+    the list of source URLs the route actually requested (so a test can assert it was called)."""
+    calls: list[str] = []
+
+    def _fake_fetch(source_url: str) -> str:
+        calls.append(source_url)
+        if raises is not None:
+            raise raises
+        return html
+
+    app.dependency_overrides[get_universe_fetcher] = lambda: _fake_fetch
+    return calls
+
+
+# --- empty state (TC-1) ---------------------------------------------------------------------------
+
+
+def test_get_with_no_snapshot_is_an_honest_empty_200(ctx):
+    client, _universe_dir = ctx
+    r = client.get("/research/desk/universe")
+    assert r.status_code == 200
+    body = r.json()
+    assert body == {"snapshots": [], "latest": None, "integrity_errors": []}
+
+
+# --- valid registration (TC-2, TC-3, TC-6) ----------------------------------------------------
+
+
+def test_post_fetch_registers_a_valid_snapshot(ctx):
+    client, universe_dir = ctx
+    _inject_fetcher(VALID_HTML)
+
+    r = client.post("/research/desk/universe/fetch")
+    assert r.status_code == 200
+    meta = r.json()["universe"]
+    assert len(meta["checksum"]) == 12
+    assert 90 <= meta["member_count"] <= 110
+    assert meta["members"] == sorted(meta["members"])
+    assert "BRK-B" in meta["members"]
+    assert "BRK.B" not in meta["members"]
+    assert meta["raw_members"]["BRK-B"] == "BRK.B"
+    assert len(list(universe_dir.glob("*.json"))) == 1
+
+
+def test_get_after_registration_lists_the_snapshot_and_serves_it_as_latest(ctx):
+    client, _universe_dir = ctx
+    _inject_fetcher(VALID_HTML)
+    posted = client.post("/research/desk/universe/fetch").json()["universe"]
+
+    r = client.get("/research/desk/universe")
+    assert r.status_code == 200
+    body = r.json()
+    assert body["integrity_errors"] == []
+    assert [row["id"] for row in body["snapshots"]] == [posted["id"]]
+    assert body["snapshots"][0] == posted  # the stored row, verbatim -- no recompute at read
+    assert body["latest"] == posted
+
+
+def test_post_fetch_only_calls_the_vendor_once_for_the_configured_source_url(ctx):
+    client, _universe_dir = ctx
+    calls = _inject_fetcher(VALID_HTML)
+    client.post("/research/desk/universe/fetch")
+    assert calls == [CONFIG.desk_universe_source_url]
+
+
+# --- corrupted input (TC-4) ---------------------------------------------------------------------
+
+
+def test_post_fetch_with_a_charset_violating_ticker_is_an_explicit_422(ctx):
+    client, universe_dir = ctx
+    _inject_fetcher(CORRUPTED_HTML)
+
+    r = client.post("/research/desk/universe/fetch")
+    assert r.status_code == 422
+    assert "charset" in r.json()["detail"]
+
+    listed = client.get("/research/desk/universe").json()
+    assert listed == {"snapshots": [], "latest": None, "integrity_errors": []}
+    assert not universe_dir.exists() or list(universe_dir.glob("*.json")) == []
+
+
+def test_post_fetch_with_an_out_of_bounds_count_is_an_explicit_422(ctx):
+    client, universe_dir = ctx
+    tiny_html = (
+        "<html><body><table><tr><th>Symbol</th></tr>"
+        "<tr><td>AAPL</td></tr><tr><td>MSFT</td></tr></table></body></html>"
+    )
+    _inject_fetcher(tiny_html)
+
+    r = client.post("/research/desk/universe/fetch")
+    assert r.status_code == 422
+    assert "2" in r.json()["detail"]
+    assert not universe_dir.exists() or list(universe_dir.glob("*.json")) == []
+
+
+def test_post_fetch_when_the_vendor_is_unreachable_is_an_explicit_503(ctx):
+    client, universe_dir = ctx
+    _inject_fetcher(raises=UniverseFetchError("could not reach the source"))
+
+    r = client.post("/research/desk/universe/fetch")
+    assert r.status_code == 503
+    assert "could not reach" in r.json()["detail"]
+    assert not universe_dir.exists() or list(universe_dir.glob("*.json")) == []
+
+
+# --- duplicate content (TC-5) ---------------------------------------------------------------------
+
+
+def test_post_fetch_of_identical_already_registered_content_is_a_409(ctx):
+    client, universe_dir = ctx
+    _inject_fetcher(VALID_HTML)
+    first = client.post("/research/desk/universe/fetch")
+    assert first.status_code == 200
+    original = first.json()["universe"]
+    path = next(universe_dir.glob("*.json"))
+    before = path.read_bytes()
+
+    duplicate = client.post("/research/desk/universe/fetch")
+    assert duplicate.status_code == 409
+    assert original["id"] in duplicate.json()["detail"]
+    assert path.read_bytes() == before  # byte-unchanged -- never a rewrite
+    assert len(list(universe_dir.glob("*.json"))) == 1  # no second file
+
+
+# --- provenance (TC-10): the exact Path-A values used at registration are embedded --------------
+
+
+def test_registered_snapshot_embeds_the_exact_config_values_used(ctx):
+    client, _universe_dir = ctx
+    _inject_fetcher(VALID_HTML)
+    meta = client.post("/research/desk/universe/fetch").json()["universe"]
+
+    assert meta["source_url"] == CONFIG.desk_universe_source_url
+    assert meta["min_members"] == CONFIG.desk_universe_min_members
+    assert meta["max_members"] == CONFIG.desk_universe_max_members
+
+    get_body = client.get("/research/desk/universe").json()
+    assert get_body["latest"]["source_url"] == CONFIG.desk_universe_source_url
+    assert get_body["latest"]["min_members"] == CONFIG.desk_universe_min_members
+    assert get_body["latest"]["max_members"] == CONFIG.desk_universe_max_members
+
+
+# --- Path-A counter-test at the route level (TC-9): live-wired end to end -----------------------
+
+
+def test_route_level_counter_test_raising_min_members_refuses_the_same_valid_fixture(ctx, monkeypatch):
+    """TC-9, exercised end to end through the ROUTE (not just the pure parser): overriding
+    ``desk_universe_min_members`` above the fixture's real member count (103) refuses the SAME
+    valid fixture — proving the field is genuinely live-wired into this new path, while
+    ``Config().config_fingerprint()`` (asserted separately in ``test_desk_universe.py``) stays
+    unaffected."""
+    client, universe_dir = ctx
+    _inject_fetcher(VALID_HTML)
+    monkeypatch.setattr(desk_routes, "CONFIG", Config(desk_universe_min_members=200))
+
+    r = client.post("/research/desk/universe/fetch")
+    assert r.status_code == 422
+    assert "outside the expected" in r.json()["detail"]
+    assert not universe_dir.exists() or list(universe_dir.glob("*.json")) == []
+
+
+# --- dependency resolvers: direct, hermetic proofs (the get_bar_store/get_bar_index precedent) --
+
+
+def test_get_universe_store_resolves_to_the_configured_dir_by_default(ctx):
+    _client, universe_dir = ctx
+    store = get_universe_store()
+    assert store.root == universe_dir
+
+
+def test_get_universe_fetcher_default_is_the_real_keyless_fetch(ctx):
+    """A direct, hermetic proof of the resolver itself (the
+    ``test_bar_fetch_adapter_resolver_defaults_to_yahoo_with_no_override`` pattern): with NO
+    ``dependency_overrides`` on ``get_universe_fetcher``, calling it returns the REAL
+    ``fetch_constituents_html``-backed callable (never a test double) — proven by identity of the
+    wrapped function's origin, not by making a real network call."""
+    _client, _universe_dir = ctx
+    app.dependency_overrides.pop(get_universe_fetcher, None)  # ensure no leftover override
+    fetch = get_universe_fetcher()
+    assert callable(fetch)
+    assert fetch.__module__ == desk_routes.__name__
+
+
+# --- honest 4xx naming the specific validation failure (not a generic message) -------------------
+
+
+def test_no_symbol_column_failure_names_the_specific_problem(ctx):
+    client, _universe_dir = ctx
+    no_symbol_html = "<html><body><table><tr><th>No.</th><th>Company</th></tr><tr><td>1</td><td>Apple</td></tr></table></body></html>"
+    _inject_fetcher(no_symbol_html)
+
+    r = client.post("/research/desk/universe/fetch")
+    assert r.status_code == 422
+    assert "Symbol" in r.json()["detail"]
diff --git a/apps/backend/tests/test_desk_universe_live_integration.py b/apps/backend/tests/test_desk_universe_live_integration.py
new file mode 100644
index 0000000..74187e8
--- /dev/null
+++ b/apps/backend/tests/test_desk_universe_live_integration.py
@@ -0,0 +1,55 @@
+"""Operator/gated REAL Wikipedia S&P 100 constituents fetch (Era B "The Desk", J-01) —
+out-of-loop, not hermetic.
+
+Per `.claude/core.md` (External Integration Testing) the hermetic suite alone is NOT sufficient
+evidence the real integration works. This is the runnable proof that ``fetch_constituents_html``
++ ``parse_constituents`` genuinely reach the live Wikipedia page and produce a valid, in-bounds
+S&P 100 membership snapshot — keyless (no credentials) and with no market-hours gate (a static
+reference page, not a live feed). GATED behind an explicit opt-in so it is SKIPPED in the
+autonomous loop by default and never makes a network call by accident (mirrors
+``test_yahoo_live_integration.py``'s / ``test_live_integration.py``'s existing
+``TAPEOLOGY_LIVE_INTEGRATION`` gate — the SAME shared env var, since this is the SAME class of
+operator-run real-external-system check, just against a third vendor).
+
+Run it (operator, any time — no credentials needed):
+
+    TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_desk_universe_live_integration.py -v -s
+"""
+
+from __future__ import annotations
+
+import os
+
+import pytest
+
+from app.config import CONFIG
+from app.research.desk_universe import fetch_constituents_html, parse_constituents
+
+pytestmark = pytest.mark.integration
+
+
+def _skip_unless_live_integration() -> None:
+    if os.environ.get("TAPEOLOGY_LIVE_INTEGRATION") != "1":
+        pytest.skip(
+            "gated: set TAPEOLOGY_LIVE_INTEGRATION=1 to run the real Wikipedia fetch check"
+        )
+
+
+def test_real_wikipedia_fetch_parses_a_valid_sp100_snapshot():
+    _skip_unless_live_integration()
+
+    html = fetch_constituents_html(CONFIG.desk_universe_source_url, timeout=15.0)
+    parsed = parse_constituents(
+        html,
+        min_members=CONFIG.desk_universe_min_members,
+        max_members=CONFIG.desk_universe_max_members,
+    )
+
+    assert CONFIG.desk_universe_min_members <= len(parsed.members) <= CONFIG.desk_universe_max_members
+    for member in parsed.members:
+        assert 1 <= len(member) <= 6
+    assert parsed.members == sorted(parsed.members)
+    assert len(parsed.members) == len(set(parsed.members))
+    # A durable, long-standing large-cap constituent — a sanity check that this is genuinely the
+    # S&P 100 table and not some other page content.
+    assert "AAPL" in parsed.members
```
