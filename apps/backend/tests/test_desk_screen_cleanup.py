"""``desk_screen_cleanup.py`` -- the two operator cleanups over the recorded screens.

Everything here runs against planted, scoped stores under ``tmp_path`` (never
``apps/backend/.data``).

Mode 1 (the one-time migration to one snapshot per date): it removes exactly the superseded copies
and their orphaned forward records, and it REFUSES rather than discarding a richer snapshot.

Mode 2 (``--non-sessions``): it removes screens recorded for dates the daily bars on file show did
not trade, INCLUDING a date's last copy -- which mode 1 structurally cannot do -- and it fails open
on every date those bars cannot speak to.
"""

from __future__ import annotations

from datetime import datetime

from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.desk_forward import ForwardStore
from app.research.desk_screen import ScreenStore
from app.research.desk_screen_cleanup import (
    apply_cleanup,
    apply_non_session_cleanup,
    plan_cleanup,
    plan_non_session_cleanup,
)

FINGERPRINT = "08e471b10130e1e2"
UNIVERSE_ID = "universe-2026-07-25-49b33fa31680"


def _record_screen(store: ScreenStore, screen_date: str, *, bar="a" * 16, ranked=3, no_bars=0):
    return store.record(
        screen_date=screen_date,
        as_of=f"{screen_date}T23:59:59Z",
        universe_snapshot_id=UNIVERSE_ID,
        config_fingerprint=FINGERPRINT,
        bar_store_signature=bar,
        rows=[{"symbol": f"SYM{n}"} for n in range(ranked)],
        skipped=[{"symbol": f"XX{n}", "reason": "no_bars"} for n in range(no_bars)],
    )


def _record_forward(store: ForwardStore, screen_id: str, screen_date: str, *, signature="sig"):
    return store.record(
        screen_id=screen_id, screen_date=screen_date, as_of=f"{screen_date}T23:59:59Z",
        config_fingerprint=FINGERPRINT, forward_input_signature=signature, payload_version=1,
        parameters={}, register="registered", rows=[], summary={}, rows_with_touches=0,
        total_touches=0,
    )


def _stores(tmp_path):
    return ScreenStore(tmp_path / "screen"), ForwardStore(tmp_path / "forward")


def test_a_date_with_one_copy_is_not_in_the_plan(tmp_path):
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, "2026-07-27")

    plan = plan_cleanup(screen_store, forward_store)

    assert plan["dates"] == []
    assert plan["refused"] == []


def test_the_plan_keeps_the_newest_copy_and_names_its_orphaned_forward_records(tmp_path):
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, "2026-07-27", bar="a" * 16)
    _record_screen(screen_store, "2026-07-27", bar="b" * 16)
    records, _errors = screen_store.list()
    older, newer = records[0], records[-1]
    orphan = _record_forward(forward_store, older["id"], "2026-07-27")
    survivor = _record_forward(forward_store, newer["id"], "2026-07-27")

    plan = plan_cleanup(screen_store, forward_store)

    assert len(plan["dates"]) == 1
    entry = plan["dates"][0]
    assert entry["screen_date"] == "2026-07-27"
    assert entry["keep"]["id"] == newer["id"]
    assert [r["id"] for r in entry["remove"]] == [older["id"]]
    assert entry["forward_remove"] == [orphan["id"]]
    assert survivor["id"] not in entry["forward_remove"]


def test_a_dry_run_plan_writes_nothing(tmp_path):
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, "2026-07-27", bar="a" * 16)
    _record_screen(screen_store, "2026-07-27", bar="b" * 16)
    before = {p.name: p.read_bytes() for p in screen_store.root.glob("*.json")}

    plan_cleanup(screen_store, forward_store)

    assert {p.name: p.read_bytes() for p in screen_store.root.glob("*.json")} == before


def test_apply_collapses_every_date_and_removes_the_orphaned_forward_records(tmp_path):
    screen_store, forward_store = _stores(tmp_path)
    for screen_date in ("2026-07-27", "2026-07-28"):
        _record_screen(screen_store, screen_date, bar="a" * 16)
        _record_screen(screen_store, screen_date, bar="b" * 16)
    _record_screen(screen_store, "2026-07-29", bar="c" * 16)  # already single -- untouched
    records, _errors = screen_store.list()
    older_ids = [
        [r for r in records if r["screen_date"] == d][0]["id"] for d in ("2026-07-27", "2026-07-28")
    ]
    for screen_id in older_ids:
        _record_forward(forward_store, screen_id, screen_id[7:17])

    plan = plan_cleanup(screen_store, forward_store)
    result = apply_cleanup(screen_store, forward_store, plan)

    assert sorted(result["removed_screens"]) == sorted(older_ids)
    assert len(result["removed_forwards"]) == 2

    after, errors = screen_store.list()
    assert errors == []
    assert len(after) == 3
    assert sorted(r["screen_date"] for r in after) == ["2026-07-27", "2026-07-28", "2026-07-29"]
    forwards, _forward_errors = forward_store.list()
    assert forwards == []


def test_a_date_whose_newest_copy_is_thinner_is_refused_not_collapsed(tmp_path):
    """The safety valve: the newest copy resolved FEWER members than an older one, so collapsing
    would discard the richer snapshot. Refused and reported -- never silently applied."""
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, "2026-07-27", bar="a" * 16, ranked=100)
    _record_screen(screen_store, "2026-07-27", bar="b" * 16, ranked=63, no_bars=38)

    plan = plan_cleanup(screen_store, forward_store)

    assert plan["dates"] == []
    assert len(plan["refused"]) == 1
    assert plan["refused"][0]["keep_resolved"] == 63

    apply_cleanup(screen_store, forward_store, plan)
    records, _errors = screen_store.list()
    assert len(records) == 2  # both copies still on disk


def test_a_refused_date_never_blocks_the_others(tmp_path):
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, "2026-07-27", bar="a" * 16, ranked=100)
    _record_screen(screen_store, "2026-07-27", bar="b" * 16, ranked=63, no_bars=38)
    _record_screen(screen_store, "2026-07-28", bar="a" * 16, ranked=63, no_bars=38)
    _record_screen(screen_store, "2026-07-28", bar="b" * 16, ranked=100)

    plan = plan_cleanup(screen_store, forward_store)
    apply_cleanup(screen_store, forward_store, plan)

    records, _errors = screen_store.list()
    by_date: dict[str, int] = {}
    for record in records:
        by_date[record["screen_date"]] = by_date.get(record["screen_date"], 0) + 1
    assert by_date == {"2026-07-27": 2, "2026-07-28": 1}


def test_a_no_basis_skip_counts_toward_a_copy_being_as_rich(tmp_path):
    """The plan uses the SAME resolved-member accounting the decision rule does, so a snapshot full
    of honest ``no_basis`` skips is not mistaken for a thin one and does not trip the valve."""
    screen_store, forward_store = _stores(tmp_path)
    screen_store.record(
        screen_date="2026-07-27", as_of="2026-07-27T23:59:59Z",
        universe_snapshot_id=UNIVERSE_ID, config_fingerprint=FINGERPRINT,
        bar_store_signature="a" * 16,
        rows=[{"symbol": "AAA"}],
        skipped=[{"symbol": "BBB", "reason": "no_basis"}, {"symbol": "CCC", "reason": "no_basis"}],
    )
    _record_screen(screen_store, "2026-07-27", bar="b" * 16, ranked=3)

    plan = plan_cleanup(screen_store, forward_store)

    assert plan["refused"] == []
    assert len(plan["dates"]) == 1


# ==================================================================================================
# Mode 2: --non-sessions. The desk chain used to enumerate raw CALENDAR days, so weekends, US market
# holidays and dates that had not happened yet were screened exactly like real sessions -- ~280 of
# the 939 snapshots on disk on 2026-08-08, each carrying an all-absent forward record. The chain and
# both compute entry points now refuse those dates; this mode is for what they already left behind.
# ==================================================================================================

# Mon 2026-06-01 .. Fri 2026-06-05, then the weekend, then the Monday after. Nothing below asserts a
# weekday NAME -- the derivation never needs to know one.
SESSIONS = ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05", "2026-06-08"]
SATURDAY = "2026-06-06"
SUNDAY = "2026-06-07"


def _bar_store_with_sessions(tmp_path, days=SESSIONS, symbol="AAA") -> BarStore:
    bar_store = BarStore(tmp_path / "bars")
    if days:
        bar_store.record(
            symbol=symbol, timeframe="1d",
            window_start_utc=f"{days[0]}T00:00:00Z", window_end_utc=f"{days[-1]}T23:59:59Z",
            feed="yahoo",
            bars=[
                RawBar(
                    symbol, "1d",
                    datetime.fromisoformat(f"{day}T14:30:00+00:00").timestamp(),
                    10.0, 11.0, 9.0, 10.5, 1000,
                )
                for day in days
            ],
        )
    return bar_store


def test_the_non_session_plan_names_a_bracketed_date_and_its_forward_records(tmp_path):
    screen_store, forward_store = _stores(tmp_path)
    saturday = _record_screen(screen_store, SATURDAY)
    _record_screen(screen_store, "2026-06-05")
    doomed = _record_forward(forward_store, saturday["id"], SATURDAY)

    plan = plan_non_session_cleanup(
        screen_store, forward_store, _bar_store_with_sessions(tmp_path), ["AAA"]
    )

    assert [entry["screen_date"] for entry in plan["dates"]] == [SATURDAY]
    assert [r["id"] for r in plan["dates"][0]["remove"]] == [saturday["id"]]
    assert plan["dates"][0]["forward_remove"] == [doomed["id"]]
    # The plan states what it rests on, so a dry run is readable without a second lookup.
    assert plan["evidence"]["anchor_symbols"] == ["AAA"]
    assert plan["evidence"]["through"] == "2026-06-08"


def test_a_recorded_session_is_never_in_the_non_session_plan(tmp_path):
    screen_store, forward_store = _stores(tmp_path)
    for day in SESSIONS:
        _record_screen(screen_store, day)

    plan = plan_non_session_cleanup(
        screen_store, forward_store, _bar_store_with_sessions(tmp_path), ["AAA"]
    )

    assert plan["dates"] == []


def test_a_date_past_the_last_recorded_daily_bar_is_left_alone(tmp_path):
    """Daily bars cannot prove anything about a session nobody has recorded yet, and a dry run that
    silently proposed deleting next Monday would be exactly the surprise this module avoids."""
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, "2026-06-09")
    _record_screen(screen_store, "2099-01-01")

    plan = plan_non_session_cleanup(
        screen_store, forward_store, _bar_store_with_sessions(tmp_path), ["AAA"]
    )

    assert plan["dates"] == []


def test_with_no_daily_bars_recorded_nothing_is_proposed(tmp_path):
    """The fail-open rail: an empty bar store must never read as 'no date ever traded'."""
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, SATURDAY)

    plan = plan_non_session_cleanup(
        screen_store, forward_store, _bar_store_with_sessions(tmp_path, days=[]), ["AAA"]
    )

    assert plan["dates"] == []
    assert plan["evidence"]["anchor_symbols"] == []


def test_applying_removes_a_dates_LAST_copy_which_the_supersede_path_cannot(tmp_path):
    """The whole reason mode 2 needs its own removal path: `prune_superseded` keeps a date's newest
    copy by definition, and there is no correct snapshot for a Saturday to be superseded BY."""
    screen_store, forward_store = _stores(tmp_path)
    saturday = _record_screen(screen_store, SATURDAY)
    sunday = _record_screen(screen_store, SUNDAY)
    kept = _record_screen(screen_store, "2026-06-05")
    doomed_forward = _record_forward(forward_store, saturday["id"], SATURDAY)
    kept_forward = _record_forward(forward_store, kept["id"], "2026-06-05")

    plan = plan_non_session_cleanup(
        screen_store, forward_store, _bar_store_with_sessions(tmp_path), ["AAA"]
    )
    result = apply_non_session_cleanup(screen_store, forward_store, plan)

    assert sorted(result["removed_screens"]) == sorted([saturday["id"], sunday["id"]])
    assert result["removed_forwards"] == [doomed_forward["id"]]

    records, errors = screen_store.list()
    assert errors == []
    assert [r["screen_date"] for r in records] == ["2026-06-05"]
    forwards, _forward_errors = forward_store.list()
    assert [f["id"] for f in forwards] == [kept_forward["id"]]


def test_the_non_session_apply_is_idempotent(tmp_path):
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, SATURDAY)
    bar_store = _bar_store_with_sessions(tmp_path)

    first = plan_non_session_cleanup(screen_store, forward_store, bar_store, ["AAA"])
    apply_non_session_cleanup(screen_store, forward_store, first)
    second = plan_non_session_cleanup(screen_store, forward_store, bar_store, ["AAA"])

    assert second["dates"] == []
    assert apply_non_session_cleanup(screen_store, forward_store, second) == {
        "removed_screens": [], "removed_forwards": []
    }


def test_the_two_modes_stay_separate(tmp_path):
    """Folding them would make one --apply capable of both. A date with duplicate copies that IS a
    session belongs only to mode 1; a non-session belongs only to mode 2."""
    screen_store, forward_store = _stores(tmp_path)
    _record_screen(screen_store, "2026-06-05", bar="a" * 16)
    _record_screen(screen_store, "2026-06-05", bar="b" * 16)
    _record_screen(screen_store, SATURDAY)
    bar_store = _bar_store_with_sessions(tmp_path)

    duplicates = plan_cleanup(screen_store, forward_store)
    non_sessions = plan_non_session_cleanup(screen_store, forward_store, bar_store, ["AAA"])

    assert [entry["screen_date"] for entry in duplicates["dates"]] == ["2026-06-05"]
    assert [entry["screen_date"] for entry in non_sessions["dates"]] == [SATURDAY]
