"""Extend the J-04/J-05/J-06 playbook browser-QA rig (``seed_playbook_fixture_rig.py``) with TWO
additional recorded session dates, for the Backscan panel's own browser-QA pass (Era B2, J-07).

Reuses the iter-6 rig VERBATIM (calls its own ``main()`` -- never a second implementation of the
DECOR/RTAAA/DTAAA fixtures or their compute) and adds:

  * a fourth universe member, ``BSCAN`` -- a plain canonical open_high_break firing session (the
    ``_plant_firing_session`` shape ``test_desk_playbook.py`` hand-computes), planted on TWO new
    dates, 2026-06-23 and 2026-06-24, each with its own 10 prior baseline sessions;
  * a NEW, fourth universe snapshot naming all four members (DECOR, RTAAA, DTAAA, BSCAN) -- universe
    registration is append-only, so this is a genuinely new record, never an edit of iter-6's own
    three-member one, and it becomes the LATEST snapshot every route reads.

Deliberately leaves BSCAN's two new dates UNRECORDED in the playbook store -- the whole point of
this rig is a Backscan panel with something genuine left to walk. A plan preview over
[2026-06-22, 2026-06-24] shows all THREE dates as ``missing_at_current_signature``, including
2026-06-22 (iter-6's own rig already recorded a playbook for it, under a THREE-member universe) --
registering the fourth member here changes ``playbook_input_signature`` (it hashes
``members ∪ {SPY}``), so the OLD three-member record no longer matches the CURRENT signature and is
honestly reported missing (T-4, "re-key, never rewrite": a membership change is exactly the kind of
input change this discipline exists to catch). A real "Run Backscan" click in the browser therefore
has genuine, non-trivial work to do on all three dates and a real, non-trivial result to screenshot
-- the OLD three-member record is untouched on disk (append-only; a fresh, four-member version is
minted beside it, never over it).

Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports the store
env vars first -- ALL FOUR playbook scoping vars, per this session's own iter-6 lesson):

    TAPEOLOGY_BAR_DIR=... TAPEOLOGY_DESK_UNIVERSE_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
    TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR=... TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR=... \\
    .venv/bin/python scripts/seed_playbook_iter7_backscan_fixture.py ROOT
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR.parent))

import seed_playbook_fixture_rig  # noqa: E402

from app.config import Config  # noqa: E402
from app.providers.adapters.base import RawBar  # noqa: E402
from app.research.bars import BarStore  # noqa: E402
from app.research.desk_playbook import resolve_desk_playbook_dir  # noqa: E402
from app.research.desk_playbook_backscan import _assert_scoped  # noqa: E402
from app.research.desk_universe import UniverseStore  # noqa: E402

BSCAN_SYMBOL = "BSCAN"
BSCAN_DATES = ("2026-06-23", "2026-06-24")
_E_OPEN_BY_DATE = {
    # 2026-06-22T13:30:00Z (== 09:30 ET) is the iter-6 rig's own E_OPEN; the two new dates are one
    # and two calendar days later -- the SAME "day offset in seconds" arithmetic
    # ``test_desk_playbook.py``'s own ``_plant_baseline_sessions`` uses.
    "2026-06-23": 1782135000.0 + 86_400.0,
    "2026-06-24": 1782135000.0 + 2 * 86_400.0,
}
_BASELINE_DAYS = 10


def _bar(symbol: str, epoch: float, o: float, h: float, low: float, c: float, v: int) -> RawBar:
    return RawBar(symbol, "5m", epoch, float(o), float(h), float(low), float(c), int(v))


def _firing_session_bars(symbol: str, day_open: float) -> list[RawBar]:
    """The canonical open_high_break session (``test_desk_playbook.py``'s ``_plant_firing_session``
    shape, hand-copied so the rig and the goldens can never drift): a narrow opening range and a
    slot-3 trigger that breaks only the high side -- fires exactly one signal."""
    return [
        _bar(symbol, day_open, 100.5, 100.9, 100.1, 100.6, 500),
        _bar(symbol, day_open + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, day_open + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, day_open + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),
        _bar(symbol, day_open + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
        _bar(symbol, day_open + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
    ]


def _baseline_bars(symbol: str, day_open: float) -> list[RawBar]:
    """10 prior RTH 5m sessions, identical flat bars -> MBR = 1.0 and a full slot-volume-median
    vector (the ``_baseline_bars`` recipe ``seed_playbook_fixture_rig.py`` itself uses)."""
    bars: list[RawBar] = []
    for day in range(_BASELINE_DAYS):
        prior_open = day_open - (day + 1) * 86_400.0
        for slot in range(6):
            bars.append(_bar(symbol, prior_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
    return bars


def main(root: Path) -> int:
    # Reuse the iter-6 rig VERBATIM first -- plants DECOR/RTAAA/DTAAA on 2026-06-22, registers the
    # three-member universe, and records ONE real playbook compute for that date. Never a second
    # implementation of any of that.
    result = seed_playbook_fixture_rig.main(root)
    if result != 0:
        return result

    config = Config()
    bar_dir = config.bar_dir_resolved()
    universe_dir = config.desk_universe_dir_resolved()
    playbook_dir = resolve_desk_playbook_dir(universe_dir)
    _assert_scoped(root)

    bar_store = BarStore(bar_dir)
    universe_store = UniverseStore(universe_dir)

    for day, day_open in _E_OPEN_BY_DATE.items():
        bars = _baseline_bars(BSCAN_SYMBOL, day_open) + _firing_session_bars(BSCAN_SYMBOL, day_open)
        bar_store.record(
            symbol=BSCAN_SYMBOL, timeframe="5m",
            window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
            feed="test", bars=bars,
        )
        print(f"[seed-playbook-iter7-backscan] planted {BSCAN_SYMBOL} {day}: {len(bars)} 5m bars", file=sys.stderr)

    members = [*seed_playbook_fixture_rig.MEMBERS, BSCAN_SYMBOL]
    universe_store.record(
        members=members, raw_members={m: m for m in members},
        source_url="fixture-rig-iter7", min_members=1, max_members=len(members),
    )
    print(f"[seed-playbook-iter7-backscan] universe snapshot: {members}", file=sys.stderr)
    print(
        f"[seed-playbook-iter7-backscan] {BSCAN_SYMBOL} left UNRECORDED on {list(BSCAN_DATES)}; "
        "2026-06-22's own three-member record now sits at a different playbook_input_signature "
        "(the fourth member re-keys it) -- a real Run Backscan click over "
        f"[2026-06-22, 2026-06-24] has genuine work to do on all three dates (playbook_dir={playbook_dir})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
