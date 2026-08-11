"""Extend the iter-8 evidence rig (``seed_playbook_iter8_evidence_fixture.py``) with everything the
REMAINING required goldens need, so ALL EIGHT required-still-passing journeys replay green against
ONE scoped backend.

WHY THIS EXISTS (goal-playbook-iter-8 audit, finding B2 + recommended next step 2). Iteration 8
made the replay lane's scoping a *launcher* and its own pipeline run ignored it, replaying against
the operator's ambient backend and writing three real playbook records + a back-scan ledger row.
Closing that hole with the framework's store-scope guard is only half the fix: with the guard armed,
every browser lane runs on the fixture rig, and five goldens (J-01, J-02, J-03, J-04, J-10) were
authored against scenarios only the operator's real store held. The audit's own words: *"Until then
no single backend exists on which all eight required journeys pass."* This layer builds that
backend.

What it adds on top of the iter-8 evidence rig (which itself reuses iter-7 -> iter-6 verbatim):

  * ``CALDR`` -- a member holding ONLY a daily (``1d``) series: one bar per WEEKDAY from
    2024-01-02 through 2026-08-14. ``desk_sessions`` derives "is this date a trading session"
    entirely from recorded daily bars over the first five members that hold them, and the rig had
    none at all -- so ``is_known_non_session`` could never answer True and the refusal J-01
    (2026-06-13, a Saturday) and J-03 (2024-01-06, a Saturday) assert was structurally unreachable.
    With this calendar both dates fall INSIDE the anchor's recorded span and outside its session
    set, which is exactly what ``non_session_refusal`` needs to say its one sentence. Weekends only:
    the rig models no holiday table (neither does the product -- see that module's opening
    paragraph), and no journey asserts one.

  * ``OLBRK`` / ``JBEXP`` / ``DBIMP`` -- the canonical open_low_break, jump-base-explosion and
    drop-base-implosion sessions, bar-for-bar from the committed detector goldens
    (``tests/test_desk_playbook_detect.py``), planted on 2026-08-07 with the rig's own ten flat
    baseline sessions. J-02 already asserts "Open-Low Break" on 2026-08-07 (its golden needs no
    edit); J-04's date moves from 2026-06-22 to this one, because 2026-06-22 cannot carry them: a
    record for that date at the CURRENT signature would flip J-07's own
    "3 missing at the current signature" assertion to 2 and break an already-passing golden.

  * every ``AAPL`` bar series COPIED VERBATIM from the operator's real store (read-only: the source
    files are opened for reading and never written, moved, or re-tagged). J-10 -- the kept-product
    sentinel -- loads ``/structure?symbol=AAPL&asof=2026-06-22...`` and asserts a real computed
    price. Levels are a pure function of the bars, so byte-identical bars reproduce the same
    numbers; substituting synthetic bars would have quietly turned the sentinel into a test of the
    fixture instead of a test of the kept product. Skipped with a loud note when the real store is
    absent (a fresh clone) -- the rest of the rig still seeds.

  * ONE new universe snapshot naming all nineteen members, then TWO fresh computes:
    2026-06-25 (the evidence corpus -- re-keyed, because the three new 5m members change
    ``playbook_input_signature`` and the evidence fold pools the DEFAULT signature only) and
    2026-08-07 (the new detector showcase). Both are append-only new versions beside the records the
    earlier layers wrote; nothing is rewritten (T-4).

  What it deliberately does NOT touch: 2026-06-22's own record (J-04/J-05/J-06 read it as
  ``newest_for_date``) and the 2026-06-22..24 back-scan window J-07 walks. Every addition lands on
  dates outside that window, for exactly the reason the iter-8 evidence seeder moved its own corpus
  to 2026-06-25.

Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports the store
env vars first):

    TAPEOLOGY_BAR_DIR=... TAPEOLOGY_DESK_UNIVERSE_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
    TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR=... TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR=... \\
    TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB=... .venv/bin/python scripts/seed_playbook_iter8_replay_rig.py ROOT
"""

from __future__ import annotations

import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR.parent))

import seed_playbook_iter8_evidence_fixture as iter8_seed  # noqa: E402

from app.config import Config  # noqa: E402
from app.providers.adapters.base import RawBar  # noqa: E402
from app.research.bars import BarStore  # noqa: E402
from app.research.desk_playbook import PlaybookStore, resolve_desk_playbook_dir  # noqa: E402
from app.research.desk_playbook_backscan import _assert_scoped  # noqa: E402
from app.research.desk_playbook_compute import run_playbook_and_record  # noqa: E402
from app.research.desk_universe import UniverseStore  # noqa: E402

# The detector showcase date: a Friday, OUTSIDE J-07's [2026-06-22, 2026-06-24] back-scan window and
# outside the evidence date (2026-06-25), and already the date J-02's stored golden types in.
DETECTOR_SESSION_DATE = "2026-08-07"
_DETECTOR_E_OPEN = 1786109400.0  # 2026-08-07T13:30:00Z == 09:30 ET (verified by direct conversion)

# The session-evidence calendar. Starts before J-03's asserted 2024-01-06 and ends after every
# fixture session date, so every date any golden types falls INSIDE the anchor's recorded span --
# the bound `is_known_non_session` requires before it will call anything a non-session.
CALENDAR_SYMBOL = "CALDR"
CALENDAR_FROM = "2024-01-02"
CALENDAR_THROUGH = "2026-08-14"
_CALENDAR_BAR_SECONDS = 48_600.0  # 13:30:00Z within the day -- same UTC date as the session

# Kept-product symbols copied verbatim from the real store for J-10's /structure step.
KEPT_SYMBOLS = ("AAPL",)

_BASELINE_DAYS = 10


def _bar(symbol: str, epoch: float, o: float, h: float, low: float, c: float, v: int,
         timeframe: str = "5m") -> RawBar:
    return RawBar(symbol, timeframe, epoch, float(o), float(h), float(low), float(c), int(v))


def _baseline_bars(symbol: str, day_open: float, slots: int) -> list[RawBar]:
    """The rig's own ten-flat-sessions baseline recipe (MBR = 1.0, slot volume median 1000),
    parameterized by BOTH the session open and the slot count -- the two existing copies each fix
    one of them (``seed_playbook_fixture_rig._baseline_bars`` fixes the open,
    ``seed_playbook_iter7_backscan_fixture._baseline_bars`` fixes the slot count at 6) and the
    twelve-slot continuation fixtures need both to vary. Same numbers, no third recipe."""
    bars: list[RawBar] = []
    for day in range(_BASELINE_DAYS):
        prior_open = day_open - (day + 1) * 86_400.0
        for slot in range(slots):
            bars.append(_bar(symbol, prior_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
    return bars


def _open_low_break_bars(symbol: str, day_open: float) -> list[RawBar]:
    """``tests/test_desk_playbook_detect.py::test_open_low_break_mirrors_the_high_side``'s own
    fixture, bar for bar: a narrow opening range and a slot-3 trigger that breaks only the LOW side
    (fires exactly one ``open_low_break`` short)."""
    rows = [
        (100.5, 100.9, 100.1, 100.4, 500),
        (100.4, 100.9, 100.1, 100.4, 500),
        (100.4, 100.9, 100.1, 100.4, 500),
        (100.2, 100.3, 99.5, 99.8, 1000),   # trigger: breaks the 100.1 opening-range low
        (99.8, 99.9, 99.6, 99.7, 800),
        (99.7, 99.8, 99.5, 99.6, 800),
    ]
    return [_bar(symbol, day_open + i * 300.0, *row) for i, row in enumerate(rows)]


def _jbe_bars(symbol: str, day_open: float) -> list[RawBar]:
    """``_canonical_jbe_bars`` verbatim: a high-volume lookback, a three-bar tight base, and a
    trigger breaking UP through the base high."""
    rows = [
        (98.4, 98.5, 98.0, 98.3, 1200),
        (98.3, 98.4, 98.1, 98.3, 1200),
        (98.3, 98.4, 98.05, 98.3, 1200),
        (98.3, 98.45, 98.2, 98.3, 1200),
        (98.3, 98.4, 98.15, 98.3, 1200),
        (98.3, 98.5, 98.3, 98.4, 3000),     # lookback volume surge
        (103.5, 103.8, 103.2, 103.6, 400),  # base bar 1
        (103.6, 104.0, 103.3, 103.7, 500),  # base bar 2
        (103.7, 103.9, 103.4, 103.8, 450),  # base bar 3
        (103.9, 104.8, 103.8, 104.5, 1500), # trigger: breaks U=104.0
        (104.5, 104.7, 104.3, 104.6, 900),
        (104.6, 104.8, 104.4, 104.7, 900),
    ]
    return [_bar(symbol, day_open + i * 300.0, *row) for i, row in enumerate(rows)]


def _dbi_bars(symbol: str, day_open: float) -> list[RawBar]:
    """``_canonical_dbi_bars`` verbatim: the exact mirror of the JBE fixture."""
    rows = [
        (109.6, 110.0, 109.5, 109.7, 1200),
        (109.7, 109.9, 109.6, 109.7, 1200),
        (109.7, 109.95, 109.6, 109.7, 1200),
        (109.7, 109.8, 109.55, 109.7, 1200),
        (109.7, 109.85, 109.6, 109.7, 1200),
        (109.6, 109.7, 109.5, 109.6, 3000),  # lookback volume surge
        (104.5, 104.8, 104.2, 104.4, 400),   # base bar 1
        (104.4, 104.7, 104.0, 104.3, 500),   # base bar 2
        (104.3, 104.6, 104.1, 104.2, 450),   # base bar 3
        (104.1, 104.2, 103.2, 103.5, 1500),  # trigger: breaks L=104.0
        (103.5, 103.7, 103.3, 103.4, 900),
        (103.4, 103.6, 103.2, 103.3, 900),
    ]
    return [_bar(symbol, day_open + i * 300.0, *row) for i, row in enumerate(rows)]


DETECTOR_MEMBERS = {
    "OLBRK": (_open_low_break_bars, 6),
    "JBEXP": (_jbe_bars, 12),
    "DBIMP": (_dbi_bars, 12),
}


def _calendar_bars(symbol: str) -> list[RawBar]:
    """One daily bar per WEEKDAY across the calendar span -- the rig's session evidence.

    Flat, unremarkable values: nothing reads these bars for price, only for the FACT that a session
    was recorded on that date (``desk_sessions`` derives its whole answer from a daily bar's
    existence). Weekends are absent, which is what makes 2024-01-06 and 2026-06-13 provable
    non-sessions rather than merely unrecorded ones."""
    bars: list[RawBar] = []
    day = date.fromisoformat(CALENDAR_FROM)
    last = date.fromisoformat(CALENDAR_THROUGH)
    while day <= last:
        if day.weekday() < 5:
            epoch = (
                (day - date(1970, 1, 1)).days * 86_400.0 + _CALENDAR_BAR_SECONDS
            )
            bars.append(_bar(symbol, epoch, 100.0, 101.0, 99.0, 100.0, 1_000_000, timeframe="1d"))
        day += timedelta(days=1)
    return bars


def _copy_kept_symbol_series(scoped_bar_dir: Path, real_bar_dir: Path) -> int:
    """Copy every recorded series for ``KEPT_SYMBOLS`` from the operator's real bar store into the
    scoped one, file for file.

    READ-ONLY on the source, by construction: the real directory is listed and its JSON files are
    opened for reading; nothing is written, renamed, or deleted there (the immutable-data rail
    applies to a QA rig exactly as it applies to the product). The destination is the scoped root,
    which ``_assert_scoped`` has already proven is not a ``.data`` store.

    Byte-identical copies matter: J-10 asserts a REAL computed price from the kept ``/structure``
    surface, and levels/zones are a pure function of the bars. Synthetic substitutes would turn the
    kept-product sentinel into a test of the fixture."""
    if not real_bar_dir.exists():
        print(
            f"[seed-playbook-iter8-replay] NOTE: no real bar store at {real_bar_dir} -- kept-symbol "
            f"series ({', '.join(KEPT_SYMBOLS)}) NOT copied; J-10's /structure step cannot pass on "
            "this rig.",
            file=sys.stderr,
        )
        return 0
    if real_bar_dir.resolve() == scoped_bar_dir.resolve():
        raise SystemExit("[seed-playbook-iter8-replay] REFUSING: scoped bar dir IS the real bar dir")
    records, _errors = BarStore(real_bar_dir).list(include_bars=False)
    copied = 0
    for record in records:
        if record["symbol"] not in KEPT_SYMBOLS:
            continue
        source = real_bar_dir / f"{record['id']}.json"
        if not source.exists():
            continue
        shutil.copy2(source, scoped_bar_dir / source.name)
        copied += 1
    print(
        f"[seed-playbook-iter8-replay] copied {copied} kept-symbol series verbatim from the real "
        f"store (read-only): {', '.join(KEPT_SYMBOLS)}",
        file=sys.stderr,
    )
    return copied


def main(root: Path) -> int:
    # Reuse the iter-8 evidence rig VERBATIM first (which reuses iter-7, which reuses iter-6):
    # DECOR/RTAAA/DTAAA on 2026-06-22, BSCAN on 2026-06-23/24 (unrecorded), OHB01..OHB12 on
    # 2026-06-25, and the sixteen-member universe + evidence compute.
    result = iter8_seed.main(root)
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

    # 1. The session calendar (J-01 / J-03's refusals).
    calendar = _calendar_bars(CALENDAR_SYMBOL)
    bar_store.record(
        symbol=CALENDAR_SYMBOL, timeframe="1d",
        window_start_utc=f"{CALENDAR_FROM}T00:00:00Z", window_end_utc=f"{CALENDAR_THROUGH}T23:59:59Z",
        feed="test", bars=calendar,
    )
    print(
        f"[seed-playbook-iter8-replay] planted {CALENDAR_SYMBOL}: {len(calendar)} daily bars "
        f"({CALENDAR_FROM}..{CALENDAR_THROUGH}, weekdays only)",
        file=sys.stderr,
    )

    # 2. The detector showcase session (J-02's Open-Low Break, J-04's JBE + DBI).
    for symbol, (builder, slots) in DETECTOR_MEMBERS.items():
        bars = _baseline_bars(symbol, _DETECTOR_E_OPEN, slots) + builder(symbol, _DETECTOR_E_OPEN)
        bar_store.record(
            symbol=symbol, timeframe="5m",
            window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
            feed="test", bars=bars,
        )
        print(f"[seed-playbook-iter8-replay] planted {symbol}: {len(bars)} 5m bars", file=sys.stderr)

    # 3. Kept-product bars for J-10's /structure step (verbatim copies, real store read-only).
    _copy_kept_symbol_series(Path(bar_dir), Path(config.bar_dir))

    # 4. ONE new snapshot naming every member, then the two computes it re-keys.
    members = [
        *iter8_seed.iter7_seed.seed_playbook_fixture_rig.MEMBERS,
        iter8_seed.iter7_seed.BSCAN_SYMBOL,
        *iter8_seed._OHB_MEMBERS,
        CALENDAR_SYMBOL,
        *DETECTOR_MEMBERS,
    ]
    universe_store.record(
        members=members, raw_members={m: m for m in members},
        source_url="fixture-rig-iter8-replay", min_members=1, max_members=len(members),
    )
    print(f"[seed-playbook-iter8-replay] universe snapshot: {members}", file=sys.stderr)

    # The evidence corpus must be re-recorded at the NEW signature: three new members hold 5m
    # series, so `compute_playbook_input_signature` moves, and the evidence fold pools the DEFAULT
    # signature only. Append-only -- the sixteen-member version stays on disk untouched beside it.
    for session_date in (iter8_seed._EVIDENCE_SESSION_DATE, DETECTOR_SESSION_DATE):
        record, reused = run_playbook_and_record(
            universe_store, bar_store, config, playbook_store, session_date,
        )
        if record is None:
            print(
                f"[seed-playbook-iter8-replay] ERROR: compute produced no record for {session_date}",
                file=sys.stderr,
            )
            return 1
        counts: dict[str, int] = {}
        for signal in record["signals"]:
            key = f"{signal['setup_id']}:{signal['side']}"
            counts[key] = counts.get(key, 0) + 1
        print(
            f"[seed-playbook-iter8-replay] recorded {record['id']} for {session_date} "
            f"(reused={reused}) signature={record['playbook_input_signature']} signal_counts={counts}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
