"""Desk forward returns v2 (forward-test era, touch-anchored) -- the pure computation and the
append-only store behind ``GET /research/desk/forward``.

**What one forward record IS.** For ONE recorded desk screen snapshot (``desk_screen.ScreenStore``,
the 5-pin append-only ledger), this module measures what recorded intraday price actually did at
each ranked row's OWN wall during **the screen date's own session** -- per row, per TOUCH of the
band:

  * **The window is the screen date's own session, and it is out-of-sample by construction.**
    ``compute_tradability``'s basis resolution (``tradability.py`` ``_resolve_basis``) filters
    daily bars to sessions STRICTLY BEFORE the requested date, and ``_PriorSessionBarView`` bounds
    every bar read to the prior session's close -- so the wall map a screen dated D ranks on is a
    function of data through D-1 only. D's own session never entered the map; its touches are a
    genuine forward test (exactly the map a chart marked up before D's open would show). A screen
    date with no session bars recorded (a weekend/holiday date from the range refresh, or bars
    not yet topped up) degrades to an honest row-level absence -- and a later compute records a
    NEW version once bars land (append-only versioning below).
  * **A touch** is a session bar whose ``[low, high]`` range overlaps the band's
    ``[price_low, price_high]`` -- the band taken VERBATIM from the screen row's own stored
    ``price_low``/``price_high`` (never recomputed) -- with the exit-required re-arm rule copied
    from ``setups.py``'s ``_touches`` (a band does not re-arm for a NEW touch until a later bar
    fully exits its range), capped at ``DESK_FORWARD_MAX_TOUCHES_PER_ROW`` per row with the
    beyond-cap count disclosed. Two honesty disclosures ride along: ``bars_fully_beyond_band``
    (session bars entirely on the wall's far side) and ``gap_through_before_first_touch`` -- a
    bar that gapped ENTIRELY beyond the band before any touch is NOT a touch under the overlap
    predicate, even though a resting limit at the edge would have filled; the register names
    this exclusion rather than silently extending the predicate.
  * **Entry per touch is a modeled limit fill at the band's near edge** (the same near-edge the
    briefing's ``distance_bps`` is measured to, ``desk_screen._distance_bps``): support ->
    ``min(bar.open, price_high)``; resistance -> ``max(bar.open, price_low)``. ``entry_kind`` is
    ``"open"`` when the bar opened at-or-through the edge (a resting limit fills at the open),
    else ``"edge"``.
  * **Horizons are trading-bar counts on the touch series** (``DESK_FORWARD_HORIZONS_MINUTES``:
    +1/+5/+60/+240 minutes = +1/+5/+60/+240 one-minute bars, or +1/+12/+48 five-minute bars; the
    "1m" label on a 5m series is an honest absence). A horizon reaching past the session's last
    bar is measured AT the last bar with ``truncated: true`` and ``effective_minutes`` (the
    ``setups.py`` truncation-honesty precedent) -- note ``effective_minutes`` counts
    bar-equivalents, not wall-clock (vendors omit no-trade minutes; extended-hours rows share
    the session's UTC date). ``to_close`` (the last session bar's close vs entry) owns the
    session-end story. ``return_pct`` values are PERCENT (x100), computed here -- the UI is
    guard-banned from arithmetic on served numbers.
  * **Every directional return is SIGNED TO THE ROW'S OWN SIDE** (the horizons and ``to_close``;
    ``DESK_FORWARD_RETURN_SIGN_CONVENTION``). A support wall's thesis is long, so its raw price
    move is served unchanged; a resistance wall's thesis is short, so its move is NEGATED. One
    reading rule holds on both sides: a POSITIVE number means price went the way the wall implied.
    The sign is applied identically to a row's touches and to its own baseline anchors, so the
    null it is compared against never drifts into the opposite space. The convention rides in
    ``parameters`` -- hashed into ``forward_input_signature`` -- so a record written under a
    different one re-keys and recomputes instead of being reused with its numbers re-read as if
    they were side-signed. The two MDDs are the deliberate exception (see ``_measure_from``).
  * **Max drawdown, long AND short, per touch** from the entry through the session close over
    ``session_bars[touch_index:]`` -- the touch bar's own full range included (a low printed
    moments before the touch within that same bar counts; the smear is disclosed here rather
    than smuggled out). Both clamped <= 0; a session that never traded below the entry is a REAL
    measured zero for the long side, not an absence.
  * **Averages (per row) pool UNTRUNCATED returns only** -- the ``setups.py`` precedent (its
    truncated forward values never enter the series) -- with ``n_truncated`` carried beside every
    cell so the exclusion is visible. ``to_close`` and the MDDs are never truncated.
  * **The baseline (the null).** Per row with >= 1 touch, the SAME math is anchored at seeded
    random session minutes: ``k = min(capped touch count, bars in session)`` anchor bars drawn by
    an explicitly-coded partial Fisher-Yates over ``rng.randrange`` (never ``random.sample`` --
    its internal algorithm is stdlib-owned and has shifted between CPython versions; this module
    owns its byte stream), ``rng = random.Random(f"{seed}:{screen_id}:{symbol}")`` -- a fresh
    per-row stream, so records are row-order- and cancel-independent and no global RNG state is
    ever touched. Anchor entry is that bar's CLOSE (the baseline measures drift at a random
    moment, not fill quality -- the asymmetry is stated in the register); anchors falling inside
    the band are KEPT (a random minute of the session is the correct null; ``anchors_in_band``
    is reported). The summary pools ALL touches vs ALL anchors per side x measure, so the table
    answers: did touching the wall beat any random minute of the same sessions?

Every payload carries ``FORWARD_REGISTER`` verbatim plus a ``parameters`` block embedding every
constant below (provenance duty -- there are ZERO new ``Config`` fields; the fingerprint pin is
untouched by construction).

**Determinism + the 2-pin key.** A forward record is a pure function of (the screen snapshot, the
1m/5m series on file for its ranked symbols, the config fingerprint, the parameters). That is
pinned as ``forward_input_signature`` -- sha256[:16] over the sorted ``(symbol, timeframe,
series_id, checksum)`` tuples of every series the compute could read (ranked symbols x
``DESK_FORWARD_TOUCH_TIMEFRAMES`` ONLY -- the coarse 1h/4h/1d/1w series are no longer read at
all), plus the fingerprint and the canonical parameters blob (a parameters change re-keys -- new
versions, correct provenance). ``ForwardStore`` is append-only under ``(screen_id,
forward_input_signature)``: identical inputs -> the recorded answer is reused; new fine bars
arriving -> a NEW record, older versions kept -- ``newest_for_screen`` serves the newest plus an
honest ``versions`` count.

**What this module never does.** It never issues a vendor fetch (fine bars arrive via the desk
top-up's own walk), never recomputes a band, never reads through ``routes.py``, and never writes
anything except through ``ForwardStore.record``."""

from __future__ import annotations

import hashlib
import json
import os
import random
import statistics
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from .bars import BarStore

# The four intraday horizons, in minutes past the touch -- converted to bar counts on the touch
# series (1m: 1/5/60/240 bars; 5m: the "1m" label is an honest absence, then 1/12/48 bars). A
# plain structural constant, NOT a Config field (the DESK_TOPUP_TIMEFRAMES precedent); embedded
# verbatim in every recorded payload's `parameters` block.
DESK_FORWARD_HORIZONS_MINUTES: tuple[tuple[str, int], ...] = (
    ("1m", 1),
    ("5m", 5),
    ("1h", 60),
    ("4h", 240),
)

# The touch-detection ladder, finest first. Coarser than 5m, "the moment price touched" is
# fiction -- a row with neither series on the screen date reads as an honest absence instead.
DESK_FORWARD_TOUCH_TIMEFRAMES: tuple[str, ...] = ("1m", "5m")

# The per-row touch cap (with the exit-re-arm rule; the beyond-cap count is disclosed). Bounds a
# pathological band-hugging session without hiding that it was one.
DESK_FORWARD_MAX_TOUCHES_PER_ROW = 8

# The baseline RNG seed (the backtests null-baseline constant echoed). Per-row streams are keyed
# f"{seed}:{screen_id}:{symbol}" so no row's draw depends on any other row or on walk order.
DESK_FORWARD_BASELINE_SEED = 1729

# The measure keys every averages/summary block carries, in serving order: the four horizon
# labels, then the session-end mark, then the two adverse excursions.
DESK_FORWARD_MEASURE_KEYS: tuple[str, ...] = (
    "1m", "5m", "1h", "4h", "to_close", "mdd_long", "mdd_short",
)

# The sign convention every directional return (the horizons and ``to_close``) is served in.
# ``side_relative``: support keeps the raw price move (its thesis is long), resistance is NEGATED
# (its thesis is short) -- so a POSITIVE number always means the wall worked, on either side, and
# a row's touches and its own baseline anchors live in the same signed space. Read at call time by
# ``forward_parameters`` so it rides in the payload AND in the input signature: a record written
# under a different convention re-keys instead of being silently reused (the 2-pin reuse rule
# compares signatures, and the numbers under it would otherwise be read as if side-signed).
# The two MDDs are deliberately NOT re-signed -- see ``_measure_from``.
DESK_FORWARD_RETURN_SIGN_CONVENTION = "side_relative"

# The visible honesty register carried by EVERY forward payload. Lint-checked in tests via
# test_copy_discipline.find_violations.
FORWARD_REGISTER = (
    "price moves after intraday touches of each ranked wall, signed to the row's own side — a "
    "support wall reads long and a resistance wall reads short, so a positive number always means "
    "price went the way the wall implied; the two max drawdowns are not signed and stay in "
    "absolute price direction. Entry is a modeled limit fill at the band edge (the bar's open "
    "when it opened through), no fees and no exits modeled; bars gapping entirely beyond the band "
    "are disclosed, not counted as touches; the baseline is the same math on the same sign, "
    "anchored at seeded random minutes of the same session and measured from those bars' closes "
    "— descriptive only, not a strategy result"
)

_FORWARD_DIR_ENV = "TAPEOLOGY_DESK_FORWARD_DIR"


class ForwardIntegrityError(Exception):
    """An on-disk forward record file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


class ForwardAlreadyRecorded(Exception):
    """A forward record with this EXACT 2-pin key (``screen_id``, ``forward_input_signature``) is
    already registered. Forward records are immutable and append-only -- a re-run over identical
    inputs reuses the existing record, never a second file."""

    def __init__(self, existing_id: str) -> None:
        self.existing_id = existing_id
        super().__init__(
            f"a forward record with this exact key is already recorded as '{existing_id}' "
            f"-- forward records are immutable and are never re-recorded"
        )


class ForwardScreenNotFound(Exception):
    """The named screen snapshot does not exist in the screen store -- there is nothing to measure
    forward from. Raised by the run-and-record caller, surfaced as an explicit refusal."""


def resolve_desk_forward_dir(desk_universe_dir_resolved: str) -> str:
    """The forward store's directory: the ``TAPEOLOGY_DESK_FORWARD_DIR`` env var if set, else a
    ``forward`` SIBLING of the caller's own already-resolved universe directory -- the
    ``resolve_desk_screen_dir`` pattern verbatim. Deliberately NOT a Config field (see the module
    docstring)."""
    override = os.environ.get(_FORWARD_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "forward")


def forward_parameters() -> dict:
    """The parameters block embedded verbatim in every recorded payload AND hashed into the input
    signature -- ONE builder so the two can never drift. Reads the module constants at call time
    (so a test monkeypatching a constant genuinely moves both the payload and the key -- the
    liveness counter-test's hook)."""
    return {
        "horizons_minutes": [list(pair) for pair in DESK_FORWARD_HORIZONS_MINUTES],
        "max_touches_per_row": DESK_FORWARD_MAX_TOUCHES_PER_ROW,
        "baseline_seed": DESK_FORWARD_BASELINE_SEED,
        "touch_timeframes": list(DESK_FORWARD_TOUCH_TIMEFRAMES),
        "return_sign_convention": DESK_FORWARD_RETURN_SIGN_CONVENTION,
    }


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes -- the SAME encoding
    ``desk_screen.py``/``desk_universe.py`` hash."""
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
    """The per-module tiny-helper convention (``desk_screen.py._iso``): epoch -> ISO, so every
    served timestamp is formatted identically wherever it is read."""
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _session_date(epoch: float) -> date:
    """A bar's UTC calendar date -- the ``setups.py._session_date`` session-grouping rule verbatim.
    Extended-hours rows carry the same date as their session and are deliberately included."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).date()


_TF_MINUTES: dict[str, int] = {"1m": 1, "5m": 5}


def compute_forward_input_signature(
    bar_store: BarStore, symbols: list[str], config_fingerprint: str
) -> str:
    """The forward record's own input pin: sha256[:16] over the sorted ``(symbol, timeframe,
    series_id, checksum)`` tuples of every recorded series the compute could possibly read
    (ranked symbols x the TOUCH ladder timeframes ONLY -- the ``setups.py._store_signature``
    style), plus the config fingerprint and the canonical parameters blob. Metadata-only:
    ``list(include_bars=False)`` reads no candle payloads, so resolving the pin costs no bar
    reads (the J-18 cheap-pre-check property). A corrupt series file is withheld by ``list`` and
    unreadable by ``merged_bars`` alike, so it cannot flap the key. Coarse (1h/4h/1d/1w) series
    are structurally invisible here -- recording them can never re-key a forward record."""
    records, _errors = bar_store.list(include_bars=False)
    wanted = set(symbols)
    tuples = sorted(
        (record["symbol"], record["timeframe"], record["id"], record["checksum"])
        for record in records
        if record["symbol"] in wanted and record["timeframe"] in DESK_FORWARD_TOUCH_TIMEFRAMES
    )
    return _sha256(_canonical([tuples, config_fingerprint, forward_parameters()]))[:16]


# --- touch detection (the setups.py semantics, copied locally with attribution) --------------------


def _touch_scan(
    session_bars: list, price_low: float, price_high: float, side: str, cap: int
) -> tuple[list[int], int, int, bool]:
    """Local copy of ``setups.py._touches``'s overlap + exit-re-arm semantics (setups.py is a
    frozen-era module; the per-module tiny-helper convention applies), extended with the cap and
    the two gap disclosures. Returns ``(touch_indices[:cap], total_touch_count,
    bars_fully_beyond_band, gap_through_before_first_touch)``.

      * a touch: ``bar.low <= price_high and bar.high >= price_low`` while armed; re-arms only
        once a later bar FULLY exits the band's range;
      * ``bars_fully_beyond_band``: bars entirely on the wall's FAR side (support: ``high <
        price_low``; resistance: ``low > price_high``) -- price got through without the overlap
        predicate firing on that bar;
      * ``gap_through_before_first_touch``: any such far-side bar occurred BEFORE the first
        counted touch (or at all, when no touch was ever counted) -- the case where a resting
        limit at the edge would have filled but no touch is recorded (the register names this
        exclusion)."""
    indices: list[int] = []
    total = 0
    beyond = 0
    first_touch_index: int | None = None
    gap_before_first = False
    armed = True
    for index, bar in enumerate(session_bars):
        inside = bar.low <= price_high and bar.high >= price_low
        fully_beyond = (bar.high < price_low) if side == "support" else (bar.low > price_high)
        if fully_beyond:
            beyond += 1
            if first_touch_index is None:
                gap_before_first = True
        if inside and armed:
            total += 1
            if first_touch_index is None:
                first_touch_index = index
            if len(indices) < cap:
                indices.append(index)
            armed = False
        elif not inside:
            armed = True
    return indices, total, beyond, gap_before_first


def _draw_anchor_indices(rng: random.Random, population: int, k: int) -> list[int]:
    """``k`` distinct indices from ``range(population)`` via an explicitly-coded partial
    Fisher-Yates over ``rng.randrange`` -- this module OWNS its byte stream (``random.sample``'s
    internal algorithm choice is stdlib-owned and has shifted between CPython versions, which
    would silently re-key first-time computes across interpreter upgrades)."""
    pool = list(range(population))
    for i in range(k):
        j = rng.randrange(i, population)
        pool[i], pool[j] = pool[j], pool[i]
    return sorted(pool[:k])


# --- per-anchor measurement (shared by touches and baseline anchors) -------------------------------


def _side_sign(side: str) -> float:
    """The row's directional multiplier under ``DESK_FORWARD_RETURN_SIGN_CONVENTION``: a support
    wall's thesis is long (``+1``, the raw price move), a resistance wall's is short (``-1``). Any
    other value is treated as long -- a screen row carrying an unrecognised side still measures,
    it simply is not negated (an honest degrade, never a crash mid-walk)."""
    return -1.0 if side == "resistance" else 1.0


def _measure_from(
    session_bars: list,
    index: int,
    entry: float,
    entry_kind: str,
    tf_minutes: int,
    sign: float,
) -> dict:
    """One anchored measurement -- the SHARED shape for a touch and a baseline anchor (one
    client-side binding). Horizons are bar-count offsets on the touch series; a target past the
    session's last bar is measured AT the last bar with ``truncated: true`` and
    ``effective_minutes`` (bar-equivalent minutes, not wall clock). ``to_close`` and both MDDs
    are measured through the session close over ``session_bars[index:]`` -- the anchor bar's own
    full range included (the pre-anchor smear the module docstring discloses).

    ``sign`` (the caller's ``_side_sign(row_side)``) multiplies every DIRECTIONAL return -- the
    horizons and ``to_close`` -- so the served number reads against the row's own thesis. It is
    applied identically to a touch and to a baseline anchor, so the null stays like-for-like.

    The two MDDs are NOT multiplied: they name their own direction (``mdd_long`` is always the
    worst move BELOW the entry, ``mdd_short`` always the worst move ABOVE it) and both stay
    clamped ``<= 0`` on either side. Signing them would collapse two independent facts into one
    and erase which way price actually travelled; the row's own adverse excursion is simply the
    one matching its thesis (support -> ``mdd_long``, resistance -> ``mdd_short``)."""
    last = len(session_bars) - 1
    horizons: dict[str, dict] = {}
    for label, minutes in DESK_FORWARD_HORIZONS_MINUTES:
        if minutes % tf_minutes != 0:
            horizons[label] = {
                "return_pct": None,
                "truncated": False,
                "effective_minutes": None,
                "reason": f"the {label} horizon is finer than the {tf_minutes}m touch series",
            }
            continue
        offset = minutes // tf_minutes
        target = index + offset
        if target > last:
            measured_at = last
            truncated = True
            effective_minutes = (last - index) * tf_minutes
        else:
            measured_at = target
            truncated = False
            effective_minutes = minutes
        horizons[label] = {
            "return_pct": sign * (session_bars[measured_at].close - entry) / entry * 100.0,
            "truncated": truncated,
            "effective_minutes": effective_minutes,
            "reason": None,
        }

    tail = session_bars[index:]
    lows = [bar.low for bar in tail]
    highs = [bar.high for bar in tail]
    return {
        "at_utc": _iso(session_bars[index].epoch),
        "entry_price": entry,
        "entry_kind": entry_kind,
        "horizons": horizons,
        "to_close_pct": sign * (session_bars[last].close - entry) / entry * 100.0,
        "minutes_to_close": (last - index) * tf_minutes,
        "mdd_long_pct": min(0.0, (min(lows) - entry) / entry * 100.0),
        "mdd_short_pct": min(0.0, (entry - max(highs)) / entry * 100.0),
    }


# --- averaging / pooling ---------------------------------------------------------------------------


def _avg_cell(values: list[float], n_truncated: int) -> dict:
    """One averages/summary cell -- plain ``statistics`` over the pooled values; nulls at
    ``n == 0`` (an honest absence, never a fabricated 0.0). ``n_truncated`` counts the
    measurements EXCLUDED from the pool as truncated (the setups precedent: a truncated forward
    value never enters the series -- it stays served per-touch with its flag)."""
    if not values:
        return {"n": 0, "mean_pct": None, "median_pct": None, "n_truncated": n_truncated}
    return {
        "n": len(values),
        "mean_pct": statistics.mean(values),
        "median_pct": statistics.median(values),
        "n_truncated": n_truncated,
    }


def _collect_measures(events: list[dict]) -> dict[str, tuple[list[float], int]]:
    """Per measure key: (pooled untruncated values, truncated-count) over one list of
    touch-shaped events."""
    pools: dict[str, tuple[list[float], int]] = {}
    for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES:
        values: list[float] = []
        truncated = 0
        for event in events:
            measure = event["horizons"][label]
            if measure["return_pct"] is None:
                continue
            if measure["truncated"]:
                truncated += 1
            else:
                values.append(measure["return_pct"])
        pools[label] = (values, truncated)
    pools["to_close"] = ([event["to_close_pct"] for event in events], 0)
    pools["mdd_long"] = ([event["mdd_long_pct"] for event in events], 0)
    pools["mdd_short"] = ([event["mdd_short_pct"] for event in events], 0)
    return pools


def _averages_block(events: list[dict]) -> dict:
    return {
        key: _avg_cell(values, truncated)
        for key, (values, truncated) in _collect_measures(events).items()
    }


# --- the compute walker ----------------------------------------------------------------------------


def compute_forward(
    screen: dict,
    bar_store: BarStore,
    config_fingerprint: str,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> dict:
    """Measure ONE recorded screen's ranked rows at their walls -- the sole walker (the
    ``compute_screen`` contract shape: returns everything ``ForwardStore.record`` needs minus the
    store-assigned ``id``/``created_utc``). Walks ``screen["rows"]`` in their stored (ranked)
    order; ``progress``, if given, is called after EACH row with ``{"symbol": symbol}``; a
    ``should_abort`` returning True stops the walk early -- the CALLER must then discard the
    partial result (a cancelled walk is never recorded)."""
    screen_date = screen["screen_date"]
    as_of_epoch = _epoch(screen["as_of"])
    window_date = date.fromisoformat(screen_date)
    symbols = [row["symbol"] for row in screen["rows"]]
    signature = compute_forward_input_signature(bar_store, symbols, config_fingerprint)

    out_rows: list[dict] = []
    touch_pool: dict[str, list[dict]] = {"support": [], "resistance": []}
    anchor_pool: dict[str, list[dict]] = {"support": [], "resistance": []}

    for row in screen["rows"]:
        if should_abort is not None and should_abort():
            break
        symbol = row["symbol"]
        side = row["side"]
        price_low = row.get("price_low")
        price_high = row.get("price_high")

        def _absent_row(reason: str) -> dict:
            return {
                "symbol": symbol,
                "side": side,
                "band_class": row.get("band_class"),
                "band_price_low": price_low,
                "band_price_high": price_high,
                "reason": reason,
                "touch_basis": None,
                "touch_count": 0,
                "touches_beyond_cap": 0,
                "bars_fully_beyond_band": 0,
                "gap_through_before_first_touch": False,
                "anchors_in_band": 0,
                "touches": [],
                "baseline_anchors": [],
                "averages": _averages_block([]),
            }

        if price_low is None or price_high is None:
            out_rows.append(
                _absent_row(
                    "screen row carries no band price range — nothing to measure touches against"
                )
            )
            if progress is not None:
                progress({"symbol": symbol})
            continue

        # The screen date's OWN session, from the finest ladder timeframe holding bars on that
        # date. The `epoch <= as_of` guard is belt-and-braces: as_of is the date's last second,
        # so only a sub-second pathological bar could exceed it -- it must never be read.
        session_bars: list = []
        touch_timeframe: str | None = None
        for tf in DESK_FORWARD_TOUCH_TIMEFRAMES:
            candidate = [
                bar
                for bar in bar_store.merged_bars(symbol, tf)
                if _session_date(bar.epoch) == window_date and bar.epoch <= as_of_epoch
            ]
            if candidate:
                session_bars = candidate
                touch_timeframe = tf
                break
        if touch_timeframe is None:
            out_rows.append(
                _absent_row(
                    f"no 1m or 5m bars recorded for the {screen_date} session — touches cannot "
                    "be measured (top up the fine timeframes, then compute again)"
                )
            )
            if progress is not None:
                progress({"symbol": symbol})
            continue

        tf_minutes = _TF_MINUTES[touch_timeframe]
        touch_indices, total_touches, beyond, gap_before_first = _touch_scan(
            session_bars, price_low, price_high, side, DESK_FORWARD_MAX_TOUCHES_PER_ROW
        )

        # One sign for the row, shared by its touches and its own baseline anchors below — the
        # null must live in the same signed space as what it is the null for.
        sign = _side_sign(side)

        touches: list[dict] = []
        for index in touch_indices:
            bar = session_bars[index]
            if side == "support":
                entry = min(bar.open, price_high)
                entry_kind = "open" if bar.open < price_high else "edge"
            else:
                entry = max(bar.open, price_low)
                entry_kind = "open" if bar.open > price_low else "edge"
            touches.append(_measure_from(session_bars, index, entry, entry_kind, tf_minutes, sign))

        # The baseline: k seeded random anchor bars, matched to the CAPPED touch count.
        baseline_anchors: list[dict] = []
        anchors_in_band = 0
        if touches:
            rng = random.Random(f"{DESK_FORWARD_BASELINE_SEED}:{screen['id']}:{symbol}")
            k = min(len(touches), len(session_bars))
            for index in _draw_anchor_indices(rng, len(session_bars), k):
                bar = session_bars[index]
                if bar.low <= price_high and bar.high >= price_low:
                    anchors_in_band += 1
                baseline_anchors.append(
                    _measure_from(session_bars, index, bar.close, "close", tf_minutes, sign)
                )

        out_rows.append(
            {
                "symbol": symbol,
                "side": side,
                "band_class": row.get("band_class"),
                "band_price_low": price_low,
                "band_price_high": price_high,
                "reason": None,
                "touch_basis": {
                    "timeframe": touch_timeframe,
                    "session_date": screen_date,
                    "bars_in_session": len(session_bars),
                },
                "touch_count": len(touches),
                "touches_beyond_cap": max(0, total_touches - len(touches)),
                "bars_fully_beyond_band": beyond,
                "gap_through_before_first_touch": gap_before_first,
                "anchors_in_band": anchors_in_band,
                "touches": touches,
                "baseline_anchors": baseline_anchors,
                "averages": _averages_block(touches),
            }
        )
        touch_pool[side].extend(touches)
        anchor_pool[side].extend(baseline_anchors)
        if progress is not None:
            progress({"symbol": symbol})

    summary: dict[str, dict] = {}
    for side in ("support", "resistance"):
        touch_measures = _collect_measures(touch_pool[side])
        anchor_measures = _collect_measures(anchor_pool[side])
        summary[side] = {
            key: {
                "touches": _avg_cell(*touch_measures[key]),
                "baseline": _avg_cell(*anchor_measures[key]),
            }
            for key in DESK_FORWARD_MEASURE_KEYS
        }

    return {
        "screen_id": screen["id"],
        "screen_date": screen_date,
        "as_of": screen["as_of"],
        "config_fingerprint": config_fingerprint,
        "forward_input_signature": signature,
        "payload_version": 3,
        "parameters": forward_parameters(),
        "register": FORWARD_REGISTER,
        "rows": out_rows,
        "summary": summary,
        "rows_with_touches": sum(1 for r in out_rows if r["touch_count"] > 0),
        "total_touches": sum(r["touch_count"] for r in out_rows),
    }


class ForwardStore:
    """File-based store rooted at the forward directory -- the ONE reader/writer. Mirrors
    ``desk_screen.ScreenStore``'s discipline exactly: every load verifies a whole-record checksum
    (``ForwardIntegrityError`` on any mismatch); the only mutation, ``record``, refuses an
    identical 2-pin key (``ForwardAlreadyRecorded``, never a second file for the same key); no
    update/delete function exists anywhere. New fine bars arriving later move the input
    signature, so a re-compute records a NEW version and every older one is kept."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, forward_id: str) -> Path:
        return self._root / f"{forward_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise ForwardIntegrityError(
                f"forward record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise ForwardIntegrityError(
                f"forward record file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise ForwardIntegrityError(
                f"forward record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise ForwardIntegrityError(
                f"forward record file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every recorded forward record (each file verified), oldest first, plus an EXPLICIT
        error row per file that failed verification. Fresh copies of the nested ``rows`` list on
        every call (the ``ScreenStore.list`` per-row-copy discipline)."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                meta = self._load(path)
                records.append({**meta, "rows": [dict(r) for r in meta["rows"]]})
            except ForwardIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
        return records, errors

    def find_by_key(self, screen_id: str, forward_input_signature: str) -> dict | None:
        """The already-recorded forward record matching this EXACT 2-pin key, or ``None`` -- the
        append-only dedup lookup ``record`` itself uses, also usable standalone by a caller that
        wants to check before paying for a walk."""
        records, _errors = self.list()
        key = (screen_id, forward_input_signature)
        for record in records:
            if (record["screen_id"], record["forward_input_signature"]) == key:
                return record
        return None

    def newest_for_screen(self, screen_id: str) -> tuple[dict | None, int]:
        """The NEWEST recorded forward record for one screen, plus an honest count of every
        version ever recorded for it (``list`` is already ``(created_utc, id)``-sorted, so the
        last match is the newest)."""
        records, _errors = self.list()
        matching = [record for record in records if record["screen_id"] == screen_id]
        if not matching:
            return None, 0
        return matching[-1], len(matching)

    def record(
        self,
        *,
        screen_id: str,
        screen_date: str,
        as_of: str,
        config_fingerprint: str,
        forward_input_signature: str,
        payload_version: int,
        parameters: dict,
        register: str,
        rows: list[dict],
        summary: dict,
        rows_with_touches: int,
        total_touches: int,
    ) -> dict:
        """Persist ONE new forward record (append-only). An identical 2-pin key raises
        ``ForwardAlreadyRecorded``; a file already at this key's own deterministic path but
        failing its integrity check raises ``ForwardIntegrityError`` -- never a silent overwrite
        (the ``ScreenStore.record`` refuse-loudly branch verbatim)."""
        existing = self.find_by_key(screen_id, forward_input_signature)
        if existing is not None:
            raise ForwardAlreadyRecorded(existing["id"])

        checksum = _sha256(_canonical([screen_id, forward_input_signature]))[:12]
        forward_id = f"forward-{screen_date}-{checksum}"
        if self._path(forward_id).exists():
            raise ForwardIntegrityError(
                f"forward record file '{self._path(forward_id).name}' already exists on disk but "
                f"failed its integrity check -- refusing to overwrite it (forward records are "
                f"append-only and are never rewritten). Move or remove the damaged file "
                f"explicitly before re-recording this key."
            )
        meta = {
            "id": forward_id,
            "screen_id": screen_id,
            "screen_date": screen_date,
            "as_of": as_of,
            "config_fingerprint": config_fingerprint,
            "forward_input_signature": forward_input_signature,
            "payload_version": payload_version,
            "parameters": dict(parameters),
            "register": register,
            "created_utc": _iso_utc_now(),
            "rows": list(rows),
            "summary": dict(summary),
            "rows_with_touches": rows_with_touches,
            "total_touches": total_touches,
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(forward_id).write_text(json.dumps(payload))
        return dict(meta)
