"""The durable stat-keyed meta-projection cache (``desk_meta_cache.py``) and the two desk stores'
use of it — ``test_bar_verify_cache.py``'s contract, applied to ``ScreenStore``/``ForwardStore``.

The no-params ``GET`` of each store re-read, re-parsed, re-canonicalized and re-hashed EVERY
recorded file just to serve a list of counts and pins — the bulk of the ~14s a ``/desk`` history
click cost. ``list_meta`` now serves that list from a stat-keyed row a prior verification already
proved.

What must stay true, and is pinned here: a hit is byte-identical to a from-scratch verify; ANY stat
change misses and re-verifies in full (so ordinary corruption is still caught and still surfaced);
an integrity error is NEVER remembered, so it is re-surfaced with the same text in the same position
on every single call; losing the DB loses nothing; a store built WITHOUT a cache path behaves
exactly as it did before this module existed; a cache that cannot be opened is a missing
optimisation rather than a failed read; and the cache never becomes load-bearing — it stores the
meta PROJECTION only, never ``rows``/``skipped``, and every response that serves snapshot CONTENT
(``latest``, ``?id=``, ``?date=``) still reads and verifies that file itself.

The two route goldens at the bottom are the whole point stated as a body: the served bytes of
``GET /research/desk/screen`` and ``GET /research/desk/forward`` are compared against the
expressions the routes used BEFORE the cache existed (a full ``store.list()``, ``len(record["rows"])``,
``max``/``records[-1]`` for ``latest``) — cold and warm.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path

import pytest

from app.config import CONFIG
from app.research.desk_forward import FORWARD_REGISTER, ForwardStore, forward_parameters
from app.research.desk_meta_cache import FORWARD_TABLE, SCREEN_TABLE, DeskMetaCache
from app.research.desk_screen import ScreenStore

UNIVERSE_SNAPSHOT_ID = "universe-2026-01-01-000000000000"

# Four consecutive recorded dates — enough that "exactly one file was re-verified" is a real
# statement rather than a coin flip, and few enough that every count below can be read by eye.
DATES = ("2026-07-24", "2026-07-25", "2026-07-26", "2026-07-27")


# --- planting helpers (test_desk_screen_diff.py's `_row`/`_plant` convention) ----------------------


def _row(symbol: str) -> dict:
    """A minimal ranked row. ``ScreenStore`` performs no row-shape validation, so a planted row
    never needs the full ``compute_screen`` shape — and this file reads only its LENGTH anyway (the
    meta projection replaces the whole list with its own count)."""
    return {"symbol": symbol, "side": "resistance", "band_class": "B", "distance_bps": 10.0}


def _skip(symbol: str) -> dict:
    return {"symbol": symbol, "skipped": True, "reason": "no_bars"}


def _forward_row(symbol: str) -> dict:
    """The forward mirror of ``_row`` — the bulk field ``ForwardStore._meta_projection`` drops."""
    return {"symbol": symbol, "side": "support", "reason": None, "touch_count": 1}


def _plant_screen(store: ScreenStore, screen_date: str, *, bar_store_signature: str = "a" * 16) -> dict:
    """One recorded snapshot for ``screen_date`` under this file's own fixed pins."""
    return store.record(
        screen_date=screen_date, as_of=f"{screen_date}T23:59:59Z",
        universe_snapshot_id=UNIVERSE_SNAPSHOT_ID,
        config_fingerprint=CONFIG.config_fingerprint(),
        bar_store_signature=bar_store_signature,
        rows=[_row("AAA"), _row("BBB")], skipped=[_skip("CCC")],
    )


def _plant_forward(store: ForwardStore, screen_date: str, *, signature: str = "sig-a") -> dict:
    """One recorded forward record measured against a synthetic screen id for ``screen_date``. The
    id carries that date because ``record`` refuses a pair that disagrees (a record is ADDRESSED by
    the date its screen id carries)."""
    return store.record(
        screen_id=f"screen-{screen_date}-{'0' * 12}", screen_date=screen_date,
        as_of=f"{screen_date}T23:59:59Z", config_fingerprint=CONFIG.config_fingerprint(),
        forward_input_signature=signature, payload_version=4, parameters=forward_parameters(),
        register=FORWARD_REGISTER, rows=[_forward_row("AAA"), _forward_row("BBB")],
        summary={"support": {"to_close": {"touches": {"n": 1}, "baseline": {"n": 1}}},
                 "resistance": {}},
        rows_with_touches=1, total_touches=1,
    )


def _corrupt(path: Path) -> None:
    """Tamper with a recorded file's CONTENT while leaving the ``file_checksum`` it was written
    with — the exact shape ``test_desk_screen.py``'s own corruption tests use, so the store's
    whole-record checksum verification fails on load (and the rewrite moves the file's stat, so a
    remembered row for it can never be hit again either)."""
    data = json.loads(path.read_text())
    data["record"]["meta"]["screen_date"] = "2099-12-31"
    path.write_text(json.dumps(data))


def _count_loads(monkeypatch, store_class) -> list[str]:
    """Instrument the store's OWN full verifier, so a cache hit is told from a re-verify by call
    count rather than by timing (``test_dataset_index.py``'s ``_counting_load`` instrumentation,
    generalised over the two stores). Returns the live list of file names loaded."""
    calls: list[str] = []
    real_load = store_class._load

    def _counting_load(self, path):
        calls.append(path.name)
        return real_load(self, path)

    monkeypatch.setattr(store_class, "_load", _counting_load)
    return calls


def _remembered(db: str, table: str) -> dict[str, dict]:
    """Every remembered row, read straight out of the DB file — introspection only, never a path
    any production read takes."""
    conn = sqlite3.connect(db)
    try:
        return {
            row[0]: json.loads(row[1])
            for row in conn.execute(f"SELECT path, meta_json FROM {table}")
        }
    finally:
        conn.close()


def _delete_db(db: str) -> None:
    Path(db).unlink()
    for suffix in ("-wal", "-shm"):
        Path(db + suffix).unlink(missing_ok=True)


@pytest.fixture
def screens(tmp_path) -> tuple[ScreenStore, str]:
    """Four recorded screens under a cache-backed store, plus the DB path they remember through —
    ``test_bar_verify_cache.py``'s ``store_with_cache`` shape.

    Nothing is aged first, deliberately: unlike the bar store's two tiers this cache carries no
    racy-write guard, because it can never put snapshot CONTENT in front of anyone (only counts and
    pins), so a file recorded and listed in the same instant is genuinely remembered."""
    db = str(tmp_path / "screen_meta_cache.db")
    store = ScreenStore(tmp_path / "screen", meta_cache_db_path=db)
    for day in DATES:
        _plant_screen(store, day)
    return store, db


@pytest.fixture
def forwards(tmp_path) -> tuple[ForwardStore, str]:
    """The ``screens`` fixture's forward twin — four recorded records, one per date, under their
    own separate DB (each store directory is independently relocatable, so each gets its own)."""
    db = str(tmp_path / "forward_meta_cache.db")
    store = ForwardStore(tmp_path / "forward", meta_cache_db_path=db)
    for day in DATES:
        _plant_forward(store, day)
    return store, db


# --- ScreenStore.list_meta: cold build, warm hit, stat change -------------------------------------


def test_the_first_screen_list_meta_verifies_every_file_and_remembers_it(screens, monkeypatch):
    """The cold build. Nothing is remembered yet, so every recorded file is verified in full
    exactly once — and every one of them lands in the DB, which is what the next read spends."""
    store, db = screens
    calls = _count_loads(monkeypatch, ScreenStore)

    records, errors = store.list_meta()

    assert errors == []
    assert len(records) == len(DATES)
    assert sorted(calls) == sorted(path.name for path in store.root.glob("*.json"))
    assert set(_remembered(db, SCREEN_TABLE)) == {str(p) for p in store.root.glob("*.json")}


def test_a_second_screen_store_on_the_same_db_serves_identical_rows_with_zero_loads(
    screens, monkeypatch
):
    """The whole point: a cold process (a brand new store instance, warm DB) must serve exactly what
    the from-scratch verify served — key order included, since a REST response built from a
    remembered row has to be byte-identical to one built from a fresh verify."""
    store, db = screens
    cold_records, cold_errors = store.list_meta()
    assert len(cold_records) == len(DATES), "the comparison would be vacuous over an empty listing"

    calls = _count_loads(monkeypatch, ScreenStore)
    warm_records, warm_errors = ScreenStore(store.root, meta_cache_db_path=db).list_meta()

    assert calls == [], "a remembered row must cost ZERO calls to the full verifier"
    assert warm_errors == cold_errors == []
    assert json.dumps(warm_records) == json.dumps(cold_records)  # key order too, not just equality


def test_touching_one_screen_file_re_verifies_exactly_that_file(screens, monkeypatch):
    """The lookup key is the file's own ``(path, size, mtime_ns)``, so ANY stat difference is an
    honest miss — and ONLY that file's. The re-verified row is then remembered under its new stat,
    so the miss is paid once rather than on every later call."""
    store, db = screens
    expected, _errors = store.list_meta()

    victim = sorted(store.root.glob("*.json"))[1]
    past = time.time() - 60
    os.utime(victim, (past, past))

    calls = _count_loads(monkeypatch, ScreenStore)
    records, errors = ScreenStore(store.root, meta_cache_db_path=db).list_meta()

    assert calls == [victim.name]
    assert errors == []
    assert json.dumps(records) == json.dumps(expected)

    calls.clear()
    assert json.dumps(ScreenStore(store.root, meta_cache_db_path=db).list_meta()[0]) == json.dumps(expected)
    assert calls == [], "the re-verified file must be remembered under its new stat"


# --- ScreenStore.list_meta: integrity errors are never remembered ---------------------------------


def test_a_corrupt_screen_is_never_remembered_and_is_re_surfaced_on_every_call(screens, monkeypatch):
    """An integrity error is never cached, at any layer. The corrupt file is re-verified and
    re-reported on every single call — with the same text, in the same position as an uncached walk
    produces — and no row for it ever reaches the DB, so no later read can serve it as healthy."""
    store, db = screens
    victim = sorted(store.root.glob("*.json"))[0]
    _corrupt(victim)

    uncached = ScreenStore(store.root)  # the from-scratch walk, for comparison
    expected_records, expected_errors = uncached.list_meta()

    records, errors = store.list_meta()
    assert len(records) == len(DATES) - 1
    assert json.dumps(records) == json.dumps(expected_records)
    assert json.dumps(errors) == json.dumps(expected_errors)
    assert [e["file"] for e in errors] == [victim.name]
    assert json.dumps(errors) == json.dumps(store.list()[1]), (
        "list_meta's error channel must stay identical to list()'s — same text, same position"
    )
    assert str(victim) not in _remembered(db, SCREEN_TABLE)

    calls = _count_loads(monkeypatch, ScreenStore)
    for _ in range(2):
        again_records, again_errors = ScreenStore(store.root, meta_cache_db_path=db).list_meta()
        assert json.dumps(again_records) == json.dumps(expected_records)
        assert json.dumps(again_errors) == json.dumps(expected_errors)
    assert calls == [victim.name, victim.name], "the damage must be re-verified every single call"


def test_a_screen_tampered_after_being_remembered_still_fails_loudly(screens):
    """The cache's honesty guarantee across a restart: ordinary tampering changes the file's size
    and mtime, so the remembered row cannot be hit — the file is re-verified, fails, and is surfaced
    as an error rather than served from a row that was proven before the damage."""
    store, db = screens
    store.list_meta()  # populate: every file remembered as healthy

    victim = sorted(store.root.glob("*.json"))[2]
    remembered_id = _remembered(db, SCREEN_TABLE)[str(victim)]["id"]
    _corrupt(victim)

    records, errors = ScreenStore(store.root, meta_cache_db_path=db).list_meta()

    assert [e["file"] for e in errors] == [victim.name]
    assert remembered_id not in {record["id"] for record in records}
    assert len(records) == len(DATES) - 1


# --- ScreenStore.list_meta: the cache is derived, opt-in, and never load-bearing -------------------


def test_deleting_the_screen_cache_loses_nothing_and_repopulates(screens, monkeypatch):
    """Deleting the DB loses nothing: the next read misses, re-verifies every file in full, serves
    byte-identical rows, and repopulates itself on the way past."""
    store, db = screens
    expected, _errors = store.list_meta()

    _delete_db(db)
    assert not Path(db).exists()

    calls = _count_loads(monkeypatch, ScreenStore)
    rebuilt = ScreenStore(store.root, meta_cache_db_path=db)
    records, errors = rebuilt.list_meta()

    assert errors == []
    assert json.dumps(records) == json.dumps(expected)
    assert len(calls) == len(DATES), "each file must be fully re-verified exactly once"
    assert Path(db).exists()

    calls.clear()
    assert json.dumps(ScreenStore(store.root, meta_cache_db_path=db).list_meta()[0]) == json.dumps(expected)
    assert calls == [], "the repopulated cache must serve the next read with zero reads too"


def test_a_screen_store_without_a_cache_path_touches_no_database(tmp_path, monkeypatch):
    """Opt-in, exactly like ``BarStore``'s durable verify cache — a bare ``ScreenStore(root)`` keeps
    its from-scratch verification on every call and writes nothing beside the screen directory."""
    store = ScreenStore(tmp_path / "screen")
    for day in DATES:
        _plant_screen(store, day)

    calls = _count_loads(monkeypatch, ScreenStore)
    first, _errors = store.list_meta()
    second, _errors = store.list_meta()

    assert json.dumps(first) == json.dumps(second)
    assert len(calls) == 2 * len(DATES), "every call re-verifies every file when no path was given"
    assert list(tmp_path.glob("*.db")) == []


def test_an_unopenable_screen_cache_degrades_to_full_verification(tmp_path):
    """A derived cache that cannot be opened is a missing optimisation, never a failed read
    (``BarStore._durable_verify_cache``'s rule verbatim) — here the path is a DIRECTORY, so
    ``sqlite3.connect`` raises and the store simply keeps verifying in full."""
    store = ScreenStore(tmp_path / "screen", meta_cache_db_path=str(tmp_path / "screen"))
    for day in DATES:
        _plant_screen(store, day)

    records, errors = store.list_meta()
    assert errors == []
    assert json.dumps(records) == json.dumps(ScreenStore(store.root).list_meta()[0])
    # And it stays degraded rather than retrying (and raising) on the next call.
    assert json.dumps(store.list_meta()[0]) == json.dumps(records)


def test_the_screen_cache_holds_metadata_only_never_rows_or_skipped(screens):
    """The 439MB-of-rows-never-cached discipline ``dataset_index.py`` documents, narrowed further
    here: only the meta PROJECTION is remembered, so the two per-member arrays that dwarf a snapshot
    can never reach this DB — and no cache can therefore put unverified snapshot CONTENT in front of
    a caller."""
    store, db = screens
    store.list_meta()

    stored = _remembered(db, SCREEN_TABLE)
    assert stored, "the cache never populated"
    for meta in stored.values():
        assert "rows" not in meta
        assert "skipped" not in meta
        assert meta["counts"] == {"rows": 2, "skipped": 1}
        assert {"id", "screen_date", "as_of", "bar_store_signature", "created_utc"} <= set(meta)


# --- ForwardStore.list_meta: the same contract, its own store and its own DB -----------------------


def test_the_first_forward_list_meta_verifies_every_file_and_remembers_it(forwards, monkeypatch):
    forward_store, db = forwards
    calls = _count_loads(monkeypatch, ForwardStore)

    records, errors = forward_store.list_meta()

    assert errors == []
    assert len(records) == len(DATES)
    assert sorted(calls) == sorted(path.name for path in forward_store.root.glob("*.json"))
    assert set(_remembered(db, FORWARD_TABLE)) == {
        str(p) for p in forward_store.root.glob("*.json")
    }


def test_a_second_forward_store_on_the_same_db_serves_identical_rows_with_zero_loads(
    forwards, monkeypatch
):
    forward_store, db = forwards
    cold_records, cold_errors = forward_store.list_meta()
    assert len(cold_records) == len(DATES), "the comparison would be vacuous over an empty listing"

    calls = _count_loads(monkeypatch, ForwardStore)
    warm_records, warm_errors = ForwardStore(forward_store.root, meta_cache_db_path=db).list_meta()

    assert calls == []
    assert warm_errors == cold_errors == []
    assert json.dumps(warm_records) == json.dumps(cold_records)


def test_touching_one_forward_file_re_verifies_exactly_that_file(forwards, monkeypatch):
    forward_store, db = forwards
    expected, _errors = forward_store.list_meta()

    victim = sorted(forward_store.root.glob("*.json"))[2]
    past = time.time() - 60
    os.utime(victim, (past, past))

    calls = _count_loads(monkeypatch, ForwardStore)
    records, errors = ForwardStore(forward_store.root, meta_cache_db_path=db).list_meta()

    assert calls == [victim.name]
    assert errors == []
    assert json.dumps(records) == json.dumps(expected)


def test_a_corrupt_forward_record_is_never_remembered_and_is_re_surfaced_on_every_call(
    forwards, monkeypatch
):
    """``ScreenStore``'s integrity contract, verbatim, on the forward store."""
    forward_store, db = forwards
    victim = sorted(forward_store.root.glob("*.json"))[0]
    _corrupt(victim)

    expected_records, expected_errors = ForwardStore(forward_store.root).list_meta()

    records, errors = forward_store.list_meta()
    assert len(records) == len(DATES) - 1
    assert json.dumps(records) == json.dumps(expected_records)
    assert json.dumps(errors) == json.dumps(expected_errors)
    assert [e["file"] for e in errors] == [victim.name]
    assert json.dumps(errors) == json.dumps(forward_store.list()[1])
    assert str(victim) not in _remembered(db, FORWARD_TABLE)

    calls = _count_loads(monkeypatch, ForwardStore)
    for _ in range(2):
        assert json.dumps(
            ForwardStore(forward_store.root, meta_cache_db_path=db).list_meta()[1]
        ) == json.dumps(expected_errors)
    assert calls == [victim.name, victim.name]


def test_deleting_the_forward_cache_loses_nothing_and_repopulates(forwards, monkeypatch):
    forward_store, db = forwards
    expected, _errors = forward_store.list_meta()

    _delete_db(db)

    calls = _count_loads(monkeypatch, ForwardStore)
    records, errors = ForwardStore(forward_store.root, meta_cache_db_path=db).list_meta()

    assert errors == []
    assert json.dumps(records) == json.dumps(expected)
    assert len(calls) == len(DATES)
    assert Path(db).exists()


def test_a_forward_store_without_a_cache_path_touches_no_database(tmp_path, monkeypatch):
    forward_store = ForwardStore(tmp_path / "forward")
    for day in DATES:
        _plant_forward(forward_store, day)

    calls = _count_loads(monkeypatch, ForwardStore)
    first, _errors = forward_store.list_meta()
    second, _errors = forward_store.list_meta()

    assert json.dumps(first) == json.dumps(second)
    assert len(calls) == 2 * len(DATES)
    assert list(tmp_path.glob("*.db")) == []


def test_an_unopenable_forward_cache_degrades_to_full_verification(tmp_path):
    forward_store = ForwardStore(tmp_path / "forward", meta_cache_db_path=str(tmp_path / "forward"))
    for day in DATES:
        _plant_forward(forward_store, day)

    records, errors = forward_store.list_meta()
    assert errors == []
    assert json.dumps(records) == json.dumps(ForwardStore(forward_store.root).list_meta()[0])


def test_the_forward_cache_holds_the_summary_but_never_the_rows(forwards):
    """This store's bulk field is ``rows`` ALONE: ``summary`` is a handful of scalars the list route
    already serves, so dropping it would change the served body — it is kept, and the per-member
    array is the only thing left on disk."""
    forward_store, db = forwards
    forward_store.list_meta()

    stored = _remembered(db, FORWARD_TABLE)
    assert stored, "the cache never populated"
    for meta in stored.values():
        assert "rows" not in meta
        assert meta["counts"] == {"rows": 2}
        assert meta["summary"] == {
            "support": {"to_close": {"touches": {"n": 1}, "baseline": {"n": 1}}},
            "resistance": {},
        }
        assert {"id", "screen_id", "forward_input_signature", "created_utc"} <= set(meta)


# --- DeskMetaCache on its own: the exact stat-keyed lookup contract --------------------------------


def test_lookup_is_an_exact_stat_match(tmp_path):
    """ANY stat difference (a genuine content change, or simply no row yet) is an honest miss,
    never a stale or approximate hit."""
    cache = DeskMetaCache(str(tmp_path / "meta.db"), SCREEN_TABLE)
    cache.insert("/x/a.json", 100, 500, {"id": "a"})

    assert cache.lookup("/x/a.json", 100, 500) == {"id": "a"}
    assert cache.lookup("/x/a.json", 101, 500) is None  # size differs
    assert cache.lookup("/x/a.json", 100, 501) is None  # mtime differs
    assert cache.lookup("/x/b.json", 100, 500) is None  # a different file entirely
    assert cache.lookup_all() == {"/x/a.json": (100, 500, '{"id": "a"}')}


def test_insert_replaces_a_superseded_row(tmp_path):
    """The self-heal shape: re-inserting under the IDENTICAL path (a legitimately changed file, new
    size/mtime) overwrites rather than duplicating or erroring."""
    cache = DeskMetaCache(str(tmp_path / "meta.db"), SCREEN_TABLE)
    cache.insert("/x/a.json", 100, 500, {"id": "a"})
    cache.insert("/x/a.json", 120, 900, {"id": "a", "counts": {"rows": 7, "skipped": 0}})

    assert cache.lookup("/x/a.json", 100, 500) is None  # the OLD stat no longer matches
    assert cache.lookup("/x/a.json", 120, 900) == {"id": "a", "counts": {"rows": 7, "skipped": 0}}
    assert len(cache.lookup_all()) == 1


def test_meta_json_is_stored_without_sort_keys_preserving_insertion_order(tmp_path):
    """The ``dataset_index.py``/``bar_verify_cache.py`` byte-identity discipline: a cache-served row
    must reproduce the EXACT key order a fresh disk verify produces, never an alphabetized one —
    otherwise a warm REST/MCP response could byte-differ from a cold one despite identical content."""
    cache = DeskMetaCache(str(tmp_path / "meta.db"), SCREEN_TABLE)
    cache.insert("/p.json", 1, 1, {"zeta": 1, "alpha": 2, "middle": 3})

    assert cache.lookup_all()["/p.json"][2] == '{"zeta": 1, "alpha": 2, "middle": 3}'


def test_prune_missing_forgets_only_the_rows_whose_files_are_gone(tmp_path):
    """Pure housekeeping: a row for a removed file is already unreachable (its path is never looked
    up again), so this only stops a cleanup's worth of removed snapshots being remembered forever —
    and it must never drop a row for a file that is still there."""
    cache = DeskMetaCache(str(tmp_path / "meta.db"), SCREEN_TABLE)
    cache.insert("/x/a.json", 100, 500, {"id": "a"})
    cache.insert("/x/b.json", 200, 600, {"id": "b"})

    assert cache.prune_missing({"/x/a.json"}) == 1
    assert cache.lookup("/x/a.json", 100, 500) == {"id": "a"}
    assert cache.lookup("/x/b.json", 200, 600) is None
    assert cache.prune_missing({"/x/a.json"}) == 0  # idempotent — nothing left to forget


def test_the_two_tables_are_independent_and_an_unknown_one_is_refused(tmp_path):
    """``table`` is fixed per instance by the store that constructs it, from a FIXED set — nothing
    can interpolate an arbitrary identifier into the schema, and two stores sharing a DB file would
    still never read each other's rows."""
    db = str(tmp_path / "meta.db")
    screen_cache = DeskMetaCache(db, SCREEN_TABLE)
    forward_cache = DeskMetaCache(db, FORWARD_TABLE)
    screen_cache.insert("/x/a.json", 100, 500, {"id": "a"})

    assert screen_cache.table == SCREEN_TABLE and forward_cache.table == FORWARD_TABLE
    assert screen_cache.db_path == db
    assert forward_cache.lookup("/x/a.json", 100, 500) is None
    assert forward_cache.lookup_all() == {}

    with pytest.raises(ValueError):
        DeskMetaCache(db, "some_other_table")


def test_concurrent_list_meta_calls_share_one_connection_without_misusing_it(tmp_path):
    """FastAPI serves these sync routes from a threadpool, so two requests can repopulate ONE
    store's cache at the same moment. Two threads entering ``with self._conn`` interleave a BEGIN
    with a COMMIT and SQLite answers "bad parameter or other API misuse", so every statement runs
    behind one lock — proven here on the COLD path (where every thread both reads and inserts)
    rather than on the trivial all-hits one. Mirrors ``test_edge_report_cache.py``'s own
    barrier-based concurrency test exactly."""
    db = str(tmp_path / "screen_meta_cache.db")
    store = ScreenStore(tmp_path / "screen", meta_cache_db_path=db)
    for day in DATES:
        _plant_screen(store, day)

    thread_count = 8
    results: list[str | None] = [None] * thread_count
    errors: list[BaseException] = []
    start_barrier = threading.Barrier(thread_count)

    def _call(index: int) -> None:
        start_barrier.wait()  # every thread reaches list_meta at roughly the same instant
        try:
            records, integrity_errors = store.list_meta()
            assert integrity_errors == []
            results[index] = json.dumps(records)
        except BaseException as exc:  # pragma: no cover -- failure path only
            errors.append(exc)

    threads = [threading.Thread(target=_call, args=(i,)) for i in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30.0)

    assert errors == [], f"a concurrent list_meta raised (never a crash, never an API misuse): {errors}"
    assert all(result is not None for result in results)
    assert len(set(results)) == 1, "every concurrent reader must see the identical listing"


# --- the served goldens: the two no-params GET bodies, cold and warm -------------------------------


@pytest.fixture
def desk_route_ctx(tmp_path, monkeypatch):
    """A live-routed screen + forward pair scoped entirely under ``tmp_path`` (never
    ``apps/backend/.data``) — ``test_desk_screen.py``'s ``screen_route_ctx`` and
    ``test_desk_forward.py``'s ``route_ctx`` wiring, combined. Both meta-cache DBs resolve to
    siblings of their own store directory, so they land under ``tmp_path`` for free."""
    from fastapi.testclient import TestClient

    from app.main import app, get_market_adapter, manager as ws_manager
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    monkeypatch.setenv("TAPEOLOGY_DESK_FORWARD_DIR", str(tmp_path / "forward"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    with TestClient(app) as client:
        yield client, tmp_path
    for ticker in list(ws_manager._engines.keys()):
        ws_manager.stop(ticker)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


def _old_screen_body(root: Path) -> dict:
    """``GET /research/desk/screen``'s no-params body, rebuilt from the expressions the route used
    BEFORE this cache existed: a full ``store.list()``, counts taken as ``len(record["rows"])`` /
    ``len(record["skipped"])`` off the materialised arrays, and ``latest`` chosen by ``max`` over
    ``(screen_date, created_utc, id)``. This is the golden the change must not move."""
    records, errors = ScreenStore(root).list()
    return {
        "screens": [
            {
                "id": r["id"],
                "screen_date": r["screen_date"],
                "as_of": r["as_of"],
                "universe_snapshot_id": r["universe_snapshot_id"],
                "config_fingerprint": r["config_fingerprint"],
                "bar_store_signature": r["bar_store_signature"],
                "created_utc": r["created_utc"],
                "counts": {"rows": len(r["rows"]), "skipped": len(r["skipped"])},
            }
            for r in records
        ],
        "latest": (
            max(records, key=lambda r: (r["screen_date"], r.get("created_utc", ""), r["id"]))
            if records
            else None
        ),
        "integrity_errors": errors,
    }


def _old_forward_body(root: Path) -> dict:
    """``GET /research/desk/forward``'s no-params body under the pre-cache expressions — same
    contract as ``_old_screen_body``, with this route's own ``records[-1]`` ``latest`` (the newest
    RECORDING, deliberately not the screen route's date-first ordering)."""
    records, errors = ForwardStore(root).list()
    return {
        "forwards": [
            {
                "id": r["id"],
                "screen_id": r["screen_id"],
                "screen_date": r["screen_date"],
                "as_of": r["as_of"],
                "config_fingerprint": r["config_fingerprint"],
                "forward_input_signature": r["forward_input_signature"],
                "payload_version": r["payload_version"],
                "parameters": r["parameters"],
                "created_utc": r["created_utc"],
                "counts": {
                    "rows": len(r["rows"]),
                    "rows_with_touches": r["rows_with_touches"],
                    "total_touches": r["total_touches"],
                },
            }
            for r in records
        ],
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }


def test_the_no_params_screen_route_serves_the_pre_cache_body_cold_and_warm(
    desk_route_ctx, monkeypatch
):
    """The served bytes are the contract. A corrupt file is planted alongside the healthy ones so
    the golden covers all three channels at once — the meta-only list, the fully-verified ``latest``,
    and ``integrity_errors``."""
    client, tmp_path = desk_route_ctx
    screen_dir = tmp_path / "screen"
    store = ScreenStore(screen_dir)
    for day in DATES:
        _plant_screen(store, day)
    victim = sorted(screen_dir.glob("*.json"))[0]
    _corrupt(victim)

    expected = _old_screen_body(screen_dir)
    assert len(expected["screens"]) == len(DATES) - 1
    assert [e["file"] for e in expected["integrity_errors"]] == [victim.name]

    cold = client.get("/research/desk/screen")
    assert cold.status_code == 200
    assert json.dumps(cold.json()) == json.dumps(expected)

    calls = _count_loads(monkeypatch, ScreenStore)
    warm = client.get("/research/desk/screen")
    assert json.dumps(warm.json()) == json.dumps(expected)
    # Every LISTED row came from a remembered projection. The only files opened are `latest`'s own
    # (snapshot CONTENT is never served from a remembered row) and the corrupt one (never
    # remembered, so re-verified and re-reported on every request).
    assert sorted(calls) == sorted([f"{expected['latest']['id']}.json", victim.name])
    assert (tmp_path / "screen_meta_cache.db").exists()


def test_the_no_params_forward_route_serves_the_pre_cache_body_cold_and_warm(
    desk_route_ctx, monkeypatch
):
    """``GET /research/desk/forward``'s own golden — same three channels, this route's own
    ``latest`` rule (the newest RECORDING) and its own meta projection (``summary`` kept, the rows
    array replaced by its count)."""
    client, tmp_path = desk_route_ctx
    forward_dir = tmp_path / "forward"
    store = ForwardStore(forward_dir)
    for day in DATES:
        _plant_forward(store, day)
    victim = sorted(forward_dir.glob("*.json"))[0]
    _corrupt(victim)

    expected = _old_forward_body(forward_dir)
    assert len(expected["forwards"]) == len(DATES) - 1
    assert [e["file"] for e in expected["integrity_errors"]] == [victim.name]

    cold = client.get("/research/desk/forward")
    assert cold.status_code == 200
    assert json.dumps(cold.json()) == json.dumps(expected)

    calls = _count_loads(monkeypatch, ForwardStore)
    warm = client.get("/research/desk/forward")
    assert json.dumps(warm.json()) == json.dumps(expected)
    assert sorted(calls) == sorted([f"{expected['latest']['id']}.json", victim.name])
    assert (tmp_path / "forward_meta_cache.db").exists()
