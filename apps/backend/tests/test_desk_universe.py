"""The universe snapshot store + parser contract (Era B "The Desk", Key Capability 1, J-01) —
store-level discipline plus the stdlib-only HTML parser.

Mirrors ``tests/test_bars.py`` / ``tests/test_datasets.py`` (the plan's own explicit directive):
metadata correctness, structural immutability (no update/re-record path exists), verified loads
(checksum), the honest failure taxonomy, and the ``desk_universe_*`` ``config_fingerprint``
exclusions (the ``bar_dir``/``bar_timeframes`` precedent). Also covers the parser contract itself
(charset, bounds, table-shape, normalization) as small, independently testable pure functions —
the ``research/desk_universe.py`` module docstring's own discipline list.
"""

from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path

import pytest

from app.config import CONFIG, Config
import app.research.desk_universe as desk_universe
from app.research.desk_universe import (
    ParsedUniverse,
    UniverseAlreadyRegistered,
    UniverseIntegrityError,
    UniverseStore,
    UniverseValidationError,
    parse_constituents,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "universe"
VALID_HTML = (FIXTURE_DIR / "sp100_constituents.html").read_text()
CORRUPTED_HTML = (FIXTURE_DIR / "sp100_constituents_corrupted.html").read_text()
# "The fixture universe" (J-02–J-05's own naming) — the ONE committed, already-registered
# snapshot produced by running the real registration path against ``VALID_HTML`` once.
REGISTERED_SNAPSHOT_PATH = FIXTURE_DIR / "universe-2026-07-25-817cc184bbb3.json"

SOURCE_URL = "https://en.wikipedia.org/wiki/S%26P_100"


def _table_html(headers: list[str], rows: list[list[str]]) -> str:
    """A minimal, hand-built table for edge cases the two committed fixtures don't need to carry
    (no-symbol-column, out-of-bounds count, citation markers, column position) — deliberately
    NOT using the big realistic fixture for these, so each edge case stays a small, obviously
    correct table."""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f"<html><body><table><tr>{head}</tr>{body}</table></body></html>"


# --- parser contract: the valid, realistic fixture --------------------------------------------


def test_parse_constituents_extracts_the_normalized_sorted_deduped_membership():
    parsed = parse_constituents(VALID_HTML, min_members=90, max_members=110)
    assert isinstance(parsed, ParsedUniverse)
    assert len(parsed.members) == 103
    assert parsed.members == sorted(parsed.members)
    assert len(parsed.members) == len(set(parsed.members))  # no duplicates
    assert parsed.members[:3] == ["AAPL", "ABBV", "ABT"]


def test_parse_constituents_normalizes_dual_class_and_preserves_the_raw_form():
    parsed = parse_constituents(VALID_HTML, min_members=90, max_members=110)
    assert "BRK-B" in parsed.members
    assert "BRK.B" not in parsed.members  # never the un-normalized form
    assert parsed.raw_members["BRK-B"] == "BRK.B"  # T-2: raw form preserved in metadata


def test_parse_constituents_raw_form_is_identity_for_a_non_dual_class_ticker():
    parsed = parse_constituents(VALID_HTML, min_members=90, max_members=110)
    assert parsed.raw_members["AAPL"] == "AAPL"


def test_parse_constituents_finds_the_symbol_column_by_header_text_not_position():
    """The committed fixture already puts Symbol in column index 2 (No./Company/Symbol/Sector).
    This proves the SAME parser also works with Symbol in column 0 -- a header-name lookup, never
    a hardcoded index."""
    html = _table_html(["Symbol", "Company"], [["AAPL", "Apple Inc."], ["MSFT", "Microsoft"]])
    parsed = parse_constituents(html, min_members=1, max_members=5)
    assert parsed.members == ["AAPL", "MSFT"]


def test_parse_constituents_accepts_a_ticker_header_as_well_as_symbol():
    html = _table_html(["Ticker", "Company"], [["AAPL", "Apple Inc."]])
    parsed = parse_constituents(html, min_members=1, max_members=5)
    assert parsed.members == ["AAPL"]


def test_parse_constituents_strips_a_footnote_citation_marker():
    html = "<html><body><table><tr><th>Symbol</th></tr><tr><td>AAPL<sup>[1]</sup></td></tr></table></body></html>"
    parsed = parse_constituents(html, min_members=1, max_members=5)
    assert parsed.members == ["AAPL"]
    assert parsed.raw_members["AAPL"] == "AAPL"


def test_parse_constituents_skips_a_short_malformed_row_without_crashing():
    """A row too short to reach the Symbol column (e.g. a spanning footnote/notes row rendered as
    a single cell) is skipped -- not a ticker-charset failure, and never fabricated as an
    empty/partial ticker. Symbol is column INDEX 1 here so a single-cell row (index 0 only)
    genuinely falls short of it."""
    html = _table_html(
        ["No.", "Symbol", "Company"],
        [["1", "AAPL", "Apple Inc."], ["(a note spanning the whole row)"], ["2", "MSFT", "Microsoft"]],
    )
    parsed = parse_constituents(html, min_members=1, max_members=5)
    assert parsed.members == ["AAPL", "MSFT"]


# --- parser contract: honest failure states (T-1) -----------------------------------------------


def test_parse_constituents_rejects_a_charset_violating_ticker_and_names_it():
    with pytest.raises(UniverseValidationError) as excinfo:
        parse_constituents(CORRUPTED_HTML, min_members=90, max_members=110)
    assert "AVG1" in str(excinfo.value)
    assert "charset" in str(excinfo.value)


def test_parse_constituents_rejects_a_member_count_below_the_minimum():
    html = _table_html(["Symbol"], [["AAPL"], ["MSFT"], ["GOOG"]])
    with pytest.raises(UniverseValidationError) as excinfo:
        parse_constituents(html, min_members=90, max_members=110)
    assert "3" in str(excinfo.value) and "90" in str(excinfo.value)


def test_parse_constituents_rejects_a_member_count_above_the_maximum():
    # The real, valid fixture (103 members) against artificially tight bounds -- "well outside
    # 90-110" per the plan's own TC-4 wording, exercised from the OTHER direction.
    with pytest.raises(UniverseValidationError) as excinfo:
        parse_constituents(VALID_HTML, min_members=1, max_members=50)
    assert "103" in str(excinfo.value) and "50" in str(excinfo.value)


def test_parse_constituents_rejects_when_no_symbol_column_exists():
    html = _table_html(["No.", "Company", "Sector"], [["1", "Apple Inc.", "Tech"]])
    with pytest.raises(UniverseValidationError) as excinfo:
        parse_constituents(html, min_members=1, max_members=110)
    assert "Symbol" in str(excinfo.value)


def test_parse_constituents_rejects_a_table_with_zero_data_rows():
    html = _table_html(["Symbol", "Company"], [])
    with pytest.raises(UniverseValidationError) as excinfo:
        parse_constituents(html, min_members=1, max_members=110)
    assert "zero tickers" in str(excinfo.value)


def test_parse_constituents_rejects_garbage_html_with_no_table_at_all():
    with pytest.raises(UniverseValidationError):
        parse_constituents("<html><body><p>nothing here</p></body></html>", min_members=1, max_members=110)


# --- store: record/list, metadata correctness ---------------------------------------------------


def _record_fixture(store: UniverseStore, *, min_members: int = 90, max_members: int = 110) -> dict:
    parsed = parse_constituents(VALID_HTML, min_members=min_members, max_members=max_members)
    return store.record(
        members=parsed.members,
        raw_members=parsed.raw_members,
        source_url=SOURCE_URL,
        min_members=min_members,
        max_members=max_members,
    )


def test_record_stores_correct_metadata_and_a_12char_checksum(tmp_path):
    store = UniverseStore(tmp_path / "universe")
    meta = _record_fixture(store)

    assert meta["member_count"] == 103
    assert isinstance(meta["checksum"], str) and len(meta["checksum"]) == 12
    int(meta["checksum"], 16)  # hex, or this raises
    assert meta["id"] == f"universe-{meta['date']}-{meta['checksum']}"
    assert meta["created_utc"].endswith("Z")
    assert meta["members"] == sorted(meta["members"])
    assert "BRK-B" in meta["members"]
    # The snapshot landed as ONE file in the configured universe dir.
    assert len(list((tmp_path / "universe").glob("*.json"))) == 1


def test_record_embeds_the_exact_config_values_used_at_registration(tmp_path):
    """TC-10 at the store level (provenance duty): the three Path-A values used at THIS
    registration are embedded verbatim in the served/stored payload."""
    store = UniverseStore(tmp_path / "universe")
    meta = _record_fixture(store, min_members=77, max_members=200)

    assert meta["source_url"] == SOURCE_URL
    assert meta["min_members"] == 77
    assert meta["max_members"] == 200


def test_list_serves_the_stored_record_verbatim_oldest_first(tmp_path):
    store = UniverseStore(tmp_path / "universe")
    recorded = _record_fixture(store)

    records, errors = store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0] == recorded


def test_store_survives_a_reload_from_disk(tmp_path):
    root = tmp_path / "universe"
    recorded = _record_fixture(UniverseStore(root))

    reloaded = UniverseStore(root)
    records, errors = reloaded.list()
    assert errors == []
    assert records == [recorded]


# --- immutability (409-style refusal; no update/re-record path exists) --------------------------


def test_rerecording_identical_membership_is_refused(tmp_path):
    store = UniverseStore(tmp_path / "universe")
    first = _record_fixture(store)

    with pytest.raises(UniverseAlreadyRegistered) as excinfo:
        _record_fixture(store)
    assert excinfo.value.existing_id == first["id"]
    assert len(list((tmp_path / "universe").glob("*.json"))) == 1  # no second file


def test_rerecording_identical_membership_leaves_the_file_byte_unchanged(tmp_path):
    universe_dir = tmp_path / "universe"
    store = UniverseStore(universe_dir)
    _record_fixture(store)
    path = next(universe_dir.glob("*.json"))
    before = path.read_bytes()

    with pytest.raises(UniverseAlreadyRegistered):
        _record_fixture(store)
    assert path.read_bytes() == before


def test_a_different_membership_registers_a_second_distinct_snapshot(tmp_path):
    store = UniverseStore(tmp_path / "universe")
    first = store.record(
        members=["AAPL", "MSFT"], raw_members={"AAPL": "AAPL", "MSFT": "MSFT"},
        source_url=SOURCE_URL, min_members=1, max_members=5,
    )
    second = store.record(
        members=["AAPL", "GOOG"], raw_members={"AAPL": "AAPL", "GOOG": "GOOG"},
        source_url=SOURCE_URL, min_members=1, max_members=5,
    )
    assert first["id"] != second["id"]
    assert first["checksum"] != second["checksum"]
    records, errors = store.list()
    assert errors == []
    assert {r["id"] for r in records} == {first["id"], second["id"]}


# --- integrity: a corrupted file is explicit, never silent --------------------------------------


def test_corrupted_snapshot_file_surfaces_explicitly_in_list_errors(tmp_path):
    universe_dir = tmp_path / "universe"
    store = UniverseStore(universe_dir)
    _record_fixture(store)
    path = next(universe_dir.glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["member_count"] = 999  # tamper -- file_checksum now disagrees
    path.write_text(json.dumps(data))

    records, errors = store.list()
    assert records == []
    assert len(errors) == 1
    assert path.name == errors[0]["file"]
    assert "integrity" in errors[0]["error"]


def test_load_raises_universe_integrity_error_for_unparseable_json(tmp_path):
    universe_dir = tmp_path / "universe"
    universe_dir.mkdir(parents=True)
    (universe_dir / "universe-2026-01-01-deadbeef0000.json").write_text("{not json")

    store = UniverseStore(universe_dir)
    records, errors = store.list()
    assert records == []
    assert len(errors) == 1


# --- T-3 guard: the universe store never routes through the dataset store -----------------------


def test_desk_universe_module_never_imports_the_dataset_store_surface():
    """Grep-based (source-introspection) guard, mirroring ``test_backtests.py``'s
    ``inspect.getsource`` precedent: ``desk_universe.py`` must never import
    ``research/datasets.py``'s registration surface or ``DatasetStore`` (T-3) -- zero hits.
    Checked against only the ACTUAL import statements (not the whole module source), since the
    module's own docstring honestly names ``DatasetStore`` in prose while explaining this exact
    discipline -- a whole-source substring scan would false-positive on its own documentation."""
    src = inspect.getsource(desk_universe)
    import_lines = "\n".join(
        line for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    )
    forbidden = ("DatasetStore", "record_from_source", "datasets")
    for pattern in forbidden:
        assert pattern not in import_lines, f"desk_universe.py must never import {pattern!r} (T-3)"


# --- Path-A Config discipline: exclusion set, stability, counter-test, resolver -----------------


def test_desk_universe_fields_are_excluded_from_config_fingerprint():
    base = CONFIG.config_fingerprint()
    changed = Config(
        desk_universe_source_url="https://example.invalid/other-source",
        desk_universe_min_members=1,
        desk_universe_max_members=1000,
        desk_universe_dir="/tmp/somewhere-else",
    ).config_fingerprint()
    assert changed == base
    # Ground truth: the era-open pin (docs/goal.md). If this ever moves, every archived-era record
    # has silently drifted -- the strongest guard against that.
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
    assert Config().config_fingerprint() == "08e471b10130e1e2"


def test_desk_universe_min_members_counter_test_changes_the_new_path_output():
    """TC-9: raising ``desk_universe_min_members`` above the fixture's actual member count (103)
    refuses the SAME valid fixture -- proving the field is genuinely live-wired into the parser's
    output, independent of (and without moving) the fingerprint."""
    with pytest.raises(UniverseValidationError):
        parse_constituents(VALID_HTML, min_members=200, max_members=300)
    # The fixture parses fine again at the real default bounds -- isolating the counter-test's
    # effect to the overridden bounds alone.
    parsed = parse_constituents(VALID_HTML, min_members=90, max_members=110)
    assert len(parsed.members) == 103


def test_desk_universe_dir_resolved_env_override(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DESK_UNIVERSE_DIR", raising=False)
    default = Config()
    assert default.desk_universe_dir_resolved() == default.desk_universe_dir

    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", "/tmp/custom-universe-dir")
    assert default.desk_universe_dir_resolved() == "/tmp/custom-universe-dir"


# --- the committed fixture snapshot: "the fixture universe" J-02-J-05 will reuse by name --------


def test_the_committed_fixture_snapshot_is_a_valid_already_registered_universe():
    """A direct load of the COMMITTED registered-snapshot JSON (produced once by running the real
    registration path against ``VALID_HTML`` -- see the module docstring / plan) — proves it is
    exactly what a fresh ``store.record`` against the fixture HTML would produce, so future
    iterations (J-02-J-05) can drop this file into a temp universe dir and call it
    "the fixture universe" without re-running a fetch."""
    assert REGISTERED_SNAPSHOT_PATH.exists(), "the committed fixture snapshot is missing"
    data = json.loads(REGISTERED_SNAPSHOT_PATH.read_text())
    meta = data["record"]["meta"]
    assert meta["member_count"] == 103
    assert 90 <= meta["member_count"] <= 110
    assert "BRK-B" in meta["members"]
    assert meta["source_url"] == SOURCE_URL


def test_the_committed_fixture_snapshot_loads_cleanly_through_the_store(tmp_path):
    universe_dir = tmp_path / "universe"
    universe_dir.mkdir()
    shutil.copy(REGISTERED_SNAPSHOT_PATH, universe_dir / REGISTERED_SNAPSHOT_PATH.name)

    store = UniverseStore(universe_dir)
    records, errors = store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["member_count"] == 103
