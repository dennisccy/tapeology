"""Extend the J-04/J-05/J-06/J-07 playbook browser-QA rig (``seed_playbook_iter7_backscan_
fixture.py``) with a well-populated Playbook Evidence corpus, for J-08's own browser-QA pass
(Era B2, goal-playbook-iter-8) -- TC-8 needs one cell with ``n >= 12`` legible beside a
``below_min_n``-tagged one in a single screenshot.

Reuses the iter-7 rig VERBATIM (calls its own ``main()`` -- never a second implementation of the
DECOR/RTAAA/DTAAA/BSCAN fixtures or their compute) and adds:

  * TWELVE new universe members, ``OHB01``..``OHB12`` -- each the SAME canonical
    open_high_break-firing session ``seed_playbook_iter7_backscan_fixture.py``'s own ``BSCAN``
    already uses (``_firing_session_bars``, imported verbatim), planted on a FRESH session date,
    2026-06-25 -- deliberately NOT 2026-06-22 (see "why a fresh date" below). ``compute_playbook``
    pools every member's signal for the SAME ``(setup_id, side)`` within one session-date walk, so
    12 members firing the identical setup on one date clears the evidence fold's
    ``(open_high_break, long, *)`` cells past the disclosure floor
    (``PLAYBOOK_MIN_N_DISCLOSURE = 12``) exactly -- the floor met, not padded. The 1h/4h measures
    for this SAME cell stay empty (the 6-bar OHB sessions truncate long before a 1h offset), so the
    SAME (setup_id, side) group shows a well-populated row (5m/to_close/mdd_*) directly beside a
    below_min_n one (1h/4h) -- exactly TC-8's own "one well populated cell and one below_min_n
    cell legible in a single screenshot" shape, with zero extra fixture work. Every OTHER setup
    (capitulation/range_trade/double_top/dbi/jbe/cup_handle) is below_min_n too, at n = 0 (no
    member fires them on 2026-06-25) -- an honest absence, not a fabricated thinness.
  * a NEW, sixteen-member universe snapshot (DECOR, RTAAA, DTAAA, BSCAN, OHB01..OHB12) --
    registration is append-only, so this is a genuinely new record, becoming the LATEST snapshot
    every route reads.
  * ONE fresh playbook compute + record for 2026-06-25 under this NEW (16-member) signature.

  **Why a fresh date (2026-06-25), never 2026-06-22.** The FIRST version of this script reused
  2026-06-22 for the evidence compute too -- but that recomputes AND RECORDS a NEW version for the
  SAME date the Backscan panel's own J-07 golden (``journey-scripts/J-07.json``) already asserts
  "3 missing at the current signature" over ``[2026-06-22, 2026-06-24]``. Recording 2026-06-22 under
  the (now current) 16-member signature would make it ``recorded_at_current_signature``, silently
  dropping J-07's own count to "2 missing" and breaking an ALREADY-PASSING golden as a side effect
  of an unrelated fixture addition -- exactly the kind of one-iteration-breaks-another regression
  this era's own append-only/no-second-implementation discipline exists to prevent. 2026-06-25 is
  outside the Backscan golden's own date range, so J-07's own three dates stay
  ``missing_at_current_signature`` at the 16-member signature, UNCHANGED, while the evidence corpus
  still gets a real, fresh, well-populated record to fold.

Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports the store
env vars first -- ALL FOUR playbook scoping vars, per the iter-6/iter-7 lesson):

    TAPEOLOGY_BAR_DIR=... TAPEOLOGY_DESK_UNIVERSE_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
    TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR=... TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR=... \\
    .venv/bin/python scripts/seed_playbook_iter8_evidence_fixture.py ROOT
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR.parent))

import seed_playbook_iter7_backscan_fixture as iter7_seed  # noqa: E402

from app.config import Config  # noqa: E402
from app.research.bars import BarStore  # noqa: E402
from app.research.desk_playbook import PlaybookStore, resolve_desk_playbook_dir  # noqa: E402
from app.research.desk_playbook_backscan import _assert_scoped  # noqa: E402
from app.research.desk_playbook_compute import run_playbook_and_record  # noqa: E402
from app.research.desk_universe import UniverseStore  # noqa: E402

_EVIDENCE_SESSION_DATE = "2026-06-25"  # a FRESH date -- outside J-07's own [06-22, 06-24] range
_OHB_MEMBERS = [f"OHB{i:02d}" for i in range(1, 13)]  # exactly 12 -- the disclosure floor, met


def main(root: Path) -> int:
    # Reuse the iter-7 rig VERBATIM first -- plants DECOR/RTAAA/DTAAA on 2026-06-22, BSCAN on
    # 2026-06-23/24 (unrecorded), registers the four-member universe, and records ONE real
    # playbook compute for 2026-06-22 at the three-member signature. Never a second implementation
    # of any of that.
    result = iter7_seed.main(root)
    if result != 0:
        return result

    config = Config()
    bar_dir = config.bar_dir_resolved()
    universe_dir = config.desk_universe_dir_resolved()
    playbook_dir = resolve_desk_playbook_dir(universe_dir)
    _assert_scoped(root)

    bar_store = BarStore(bar_dir)
    universe_store = UniverseStore(universe_dir)
    playbook_store = PlaybookStore(playbook_dir)

    # 2026-06-22 + 3 calendar days == 2026-06-25 -- the SAME "day offset in seconds" arithmetic
    # seed_playbook_iter7_backscan_fixture.py's own BSCAN dates use (both June, EDT, no DST
    # transition -- plain day arithmetic against E_OPEN resolves the same epoch a fresh ET
    # conversion would).
    e_open = iter7_seed.seed_playbook_fixture_rig.E_OPEN + 3 * 86_400.0
    for symbol in _OHB_MEMBERS:
        bars = iter7_seed._baseline_bars(symbol, e_open) + iter7_seed._firing_session_bars(symbol, e_open)
        bar_store.record(
            symbol=symbol, timeframe="5m",
            window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
            feed="test", bars=bars,
        )
        print(f"[seed-playbook-iter8-evidence] planted {symbol}: {len(bars)} 5m bars", file=sys.stderr)

    members = [
        *iter7_seed.seed_playbook_fixture_rig.MEMBERS, iter7_seed.BSCAN_SYMBOL, *_OHB_MEMBERS,
    ]
    universe_store.record(
        members=members, raw_members={m: m for m in members},
        source_url="fixture-rig-iter8", min_members=1, max_members=len(members),
    )
    print(f"[seed-playbook-iter8-evidence] universe snapshot: {members}", file=sys.stderr)

    record, reused = run_playbook_and_record(
        universe_store, bar_store, config, playbook_store, _EVIDENCE_SESSION_DATE,
    )
    if record is None:
        print("[seed-playbook-iter8-evidence] ERROR: compute produced no record", file=sys.stderr)
        return 1
    setup_counts: dict[str, int] = {}
    for s in record["signals"]:
        key = f"{s['setup_id']}:{s['side']}"
        setup_counts[key] = setup_counts.get(key, 0) + 1
    print(
        f"[seed-playbook-iter8-evidence] recorded {record['id']} (reused={reused}) "
        f"signature={record['playbook_input_signature']} signal_counts={setup_counts}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
