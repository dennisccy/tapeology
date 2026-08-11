"""Seed the J-04/J-05/J-06 playbook browser-QA rig into a SCOPED root (never .data/).

Every bar value below is copied verbatim from the committed goldens
(``tests/test_desk_playbook_detect.py`` / ``tests/test_desk_playbook.py``) so the rig a browser
pass photographs and the fixtures the unit tests hand-compute can never drift. Nothing here
re-derives a number, and nothing here writes outside the root it is given.

Planted for session 2026-06-22:

* ``DECOR`` -- the euphoria-marker-then-capitulation session (J-05: a capitulation signal whose
  disclosures carry ``euphoria_recent``);
* ``RTAAA`` -- the canonical TWO-SIDED armed range (J-06 ``range_trade`` long: both zones tested
  twice and held, spec §3.7's full arming clause);
* ``DTAAA`` -- the canonical double top (J-06 ``double_top`` short, valley-break trigger).

Usage (normally through ``qa_playbook_iter6_fixture_scoped_backend.sh``, which exports the store
env vars first):

    TAPEOLOGY_BAR_DIR=... TAPEOLOGY_DESK_UNIVERSE_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
    TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR=... .venv/bin/python scripts/seed_playbook_fixture_rig.py ROOT
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Config  # noqa: E402
from app.providers.adapters.base import RawBar  # noqa: E402
from app.research.bars import BarStore  # noqa: E402
from app.research.desk_playbook import PlaybookStore, resolve_desk_playbook_dir  # noqa: E402
from app.research.desk_playbook_compute import run_playbook_and_record  # noqa: E402
from app.research.desk_universe import UniverseStore  # noqa: E402

SESSION_DATE = "2026-06-22"
E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET
BASELINE_DAYS = 10


def _bar(symbol: str, slot_epoch: float, o: float, h: float, low: float, c: float, v: int) -> RawBar:
    return RawBar(symbol, "5m", slot_epoch, float(o), float(h), float(low), float(c), int(v))


def _baseline_bars(symbol: str, slots: int) -> list[RawBar]:
    """10 prior RTH sessions, identical flat bars -> MBR = 1.0 and a full slot-volume-median
    vector (the ``_plant_baseline_sessions`` recipe the goldens use)."""
    bars: list[RawBar] = []
    for day in range(BASELINE_DAYS):
        day_open = E_OPEN - (day + 1) * 86_400.0
        for slot in range(slots):
            bars.append(_bar(symbol, day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
    return bars


def _decor_session(symbol: str) -> list[RawBar]:
    """Euphoria marker (trigger slot 4) then an independent capitulation (trigger slot 8)."""
    rows = [
        (95.9, 96.1, 95.7, 96.0, 1000),
        (96.0, 97.6, 95.9, 97.5, 1000),
        (97.5, 99.1, 97.4, 99.0, 1200),
        (99.0, 100.7, 98.9, 100.5, 2500),
        (100.4, 100.6, 98.5, 98.9, 1000),
        (98.9, 99.0, 96.5, 97.0, 1000),
        (97.0, 97.2, 95.0, 95.5, 1000),
        (94.0, 94.2, 92.8, 93.5, 2600),
        (93.0, 94.5, 93.0, 94.0, 1000),
    ]
    return [_bar(symbol, E_OPEN + i * 300.0, *row) for i, row in enumerate(rows)]


def _range_trade_session(symbol: str) -> list[RawBar]:
    """The canonical two-sided armed range: high touches at slots 0/4, low touches at slots 2/6
    (each held within RANGE_HOLD_TOL), reversal-bar trigger at slot 7."""
    rows = [
        (104.0, 105.0, 103.5, 104.5, 1000),
        (103.9, 103.9, 101.5, 101.8, 1000),
        (101.8, 102.0, 100.0, 100.4, 1000),
        (101.6, 103.0, 101.5, 102.8, 1000),
        (102.8, 104.8, 102.5, 104.4, 1000),
        (103.4, 103.5, 102.0, 102.4, 1000),
        (102.4, 102.6, 100.4, 100.7, 1000),
        (101.0, 103.5, 100.6, 103.2, 2000),
        (103.2, 103.4, 102.9, 103.1, 1000),
        (103.1, 103.3, 102.8, 103.0, 1000),
    ]
    return [_bar(symbol, E_OPEN + i * 300.0, *row) for i, row in enumerate(rows)]


def _double_top_session(symbol: str) -> list[RawBar]:
    """The canonical double top: P1 high 110.0 (slot 3), P2 high 110.3 (slot 13), valley low 97.0
    (slot 8), valley-break trigger at slot 18."""
    rows = [
        (104, 105, 104, 104.5, 1000),
        (104.5, 106, 104, 105.5, 1000),
        (105.5, 107, 105, 106.5, 1000),
        (106.5, 110, 106, 109, 1000),
        (109, 108, 107, 107.5, 1000),
        (107.5, 105, 104, 104.5, 1000),
        (104.5, 102, 101, 101.5, 1000),
        (101.5, 100, 99, 99.5, 1000),
        (99.5, 98, 97, 97.5, 1000),
        (97.5, 99, 97.2, 98.5, 1000),
        (98.5, 101, 98, 100.5, 1000),
        (100.5, 104, 100, 103.5, 1000),
        (103.5, 107, 103, 106.5, 1000),
        (106.5, 110.3, 106, 109.5, 1000),
        (109.5, 108, 107, 107.5, 1000),
        (107.5, 106, 105, 105.5, 1000),
        (105.5, 104, 103, 103.5, 1000),
        (103.5, 103.8, 102, 102.5, 1000),
        (102.5, 103, 96.0, 96.5, 2000),
        (96.5, 97, 96, 96.8, 1000),
    ]
    return [_bar(symbol, E_OPEN + i * 300.0, *row) for i, row in enumerate(rows)]


MEMBERS = {
    "DECOR": (_decor_session, 9),
    "RTAAA": (_range_trade_session, 10),
    "DTAAA": (_double_top_session, 20),
}


def _assert_scoped(root: Path, **dirs: str) -> None:
    """Refuse to plant anything unless EVERY resolved store directory lives under ``root`` and
    outside the repo's ``.data/``. Learned the hard way during the iter-6 fix pass: reading
    ``config.bar_dir`` (the raw default field) instead of ``config.bar_dir_resolved()`` (the env
    override) silently planted three synthetic fixture bar series and a 3-member universe
    snapshot into the operator's REAL store. A seeder that can reach ``.data/`` at all is a
    loaded gun -- this guard makes the failure loud and harmless instead of silent and durable."""
    root_resolved = root.resolve()
    problems = []
    for name, value in dirs.items():
        path = Path(value).resolve()
        if ".data" in path.parts:
            problems.append(f"{name}={path} is inside a .data/ store")
        elif root_resolved not in path.parents and path != root_resolved:
            problems.append(f"{name}={path} is outside the seed root {root_resolved}")
    if problems:
        raise SystemExit(
            "[seed-playbook-rig] REFUSING to seed -- store directories are not scoped:\n  "
            + "\n  ".join(problems)
            + "\nExport TAPEOLOGY_BAR_DIR / TAPEOLOGY_DESK_UNIVERSE_DIR / "
              "TAPEOLOGY_DESK_PLAYBOOK_DIR / TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR (all four) at the "
              "seed root first -- qa_playbook_iter6_fixture_scoped_backend.sh does it for you."
        )


def main(root: Path) -> int:
    config = Config()
    # `*_resolved()`, never the raw `config.<dir>` fields: only the resolved accessors read the
    # TAPEOLOGY_* env overrides. The raw fields always point at the operator's real .data/ store.
    bar_dir = config.bar_dir_resolved()
    universe_dir = config.desk_universe_dir_resolved()
    playbook_dir = resolve_desk_playbook_dir(universe_dir)
    _assert_scoped(root, bar_dir=bar_dir, universe_dir=universe_dir, playbook_dir=playbook_dir)

    bar_store = BarStore(bar_dir)
    universe_store = UniverseStore(universe_dir)
    playbook_store = PlaybookStore(playbook_dir)

    for symbol, (builder, slots) in MEMBERS.items():
        bars = _baseline_bars(symbol, slots) + builder(symbol)
        bar_store.record(
            symbol=symbol, timeframe="5m",
            window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
            feed="test", bars=bars,
        )
        print(f"[seed-playbook-rig] planted {symbol}: {len(bars)} 5m bars", file=sys.stderr)

    universe_store.record(
        members=list(MEMBERS), raw_members={m: m for m in MEMBERS},
        source_url="fixture-rig", min_members=1, max_members=len(MEMBERS),
    )
    print(f"[seed-playbook-rig] universe snapshot: {list(MEMBERS)}", file=sys.stderr)

    record, reused = run_playbook_and_record(
        universe_store, bar_store, config, playbook_store, SESSION_DATE,
    )
    if record is None:
        print("[seed-playbook-rig] ERROR: compute produced no record", file=sys.stderr)
        return 1
    fired = sorted({(s["symbol"], s["setup_id"], s["side"]) for s in record["signals"]})
    print(
        f"[seed-playbook-rig] recorded {record['id']} (reused={reused}) "
        f"signature={record['playbook_input_signature']} signals={fired}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
