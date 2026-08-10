"""The Playbook's detectors (Era B2, J-01: the opening-range-break family only --
``docs/playbook-detector-spec.md`` §3.1-3.2). J-04/J-05/J-06 add the remaining seven detectors
here, each built purely out of ``desk_playbook_features.py``'s eight primitives plus the
``playbook_parameters()`` dict a caller hands in.

**A THIRD "setup" vocabulary -- never conflate.** ``setups.py`` (the tick-touch scanner) and
``backtests.py`` (tape-arming occurrences) already use "setup" for two OTHER things; a playbook
signal is the book's own intraday pattern, a third, unrelated sense. This module never imports
from ``setups.py`` or ``backtests.py``, and no field here is ever named ``stop_loss`` -- the field
is ``invalidation_price``, a disclosed structural level, never an order concept.

**Constant-free by design, same as the primitives.** This module imports NOTHING from
``desk_playbook.py`` -- every threshold arrives as ``params`` (the caller's already-built
``playbook_parameters()`` dict). This is what keeps the import graph acyclic
(``desk_playbook.py`` -> this module -> ``desk_playbook_features.py`` -> ``desk_forward.py``,
never the reverse) AND makes "the parameters blob matches what the detector actually used" true
by construction: there is no second copy of a threshold anywhere for the two to drift apart on.

**Lookahead law.** ``detect_opening_range_breaks`` reads ``session_bars`` strictly through the
trigger bar for every GATING decision (the narrowness gate, the trigger crossing itself, the
volume-into-trigger discriminator, ``attempt_count``, market context) -- the trigger bar's own
close/volume/range are disclosures, never gates (spec §0). The one field that legitimately depends
on bars AFTER the trigger is ``bars_to_close`` (how much of the session remained) -- a descriptive
fact about the rest of the session, not a detection decision; the generic lookahead property test
(``tests/test_desk_playbook_detect.py``) asserts core detection fields (trigger_price,
invalidation_price, geometry) are truncation-invariant and the WHOLE signal is mutation-invariant
for any bar strictly after the trigger."""

from __future__ import annotations

from datetime import datetime, timezone

from ..providers.adapters.base import RawBar
from .desk_playbook_features import market_context, rth_session_slice, vertical_move, zone_touches

__all__ = ["detect_opening_range_breaks"]


def _iso(epoch: float) -> str:
    """The per-module tiny-helper convention (``desk_screen.py._iso``, ``desk_forward.py._iso``):
    epoch -> ISO, so every served timestamp is formatted identically wherever it is read."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _rvol(bar: RawBar, slot: int, slot_volume_medians: dict[int, float]) -> float | None:
    """One bar's RVOL against its own baseline slot median -- spec §0's ONE relative-volume
    definition; null (never a guess) when the slot has no median (too few baseline sessions)."""
    median = slot_volume_medians.get(slot)
    if not median:
        return None
    return bar.volume / median


def _spike_into_trigger_verdict(
    session_bars: list[RawBar],
    approach_indices: list[int],
    approach_rvols: list[float | None],
    trigger_price: float,
    side: str,
    mbr: float,
    rvol_surge: float,
    near_extreme_mbr: float,
) -> str:
    """spec §0's volume-into-trigger discriminator, defined once and shared by every detector.
    Disclosure only, never a gate."""
    for idx, rvol in zip(approach_indices, approach_rvols):
        if rvol is None or rvol < rvol_surge:
            continue
        bar = session_bars[idx]
        if side == "long":
            near_level = abs(bar.high - trigger_price) <= near_extreme_mbr * mbr
            failed_to_close_beyond = bar.close <= trigger_price
        else:
            near_level = abs(bar.low - trigger_price) <= near_extreme_mbr * mbr
            failed_to_close_beyond = bar.close >= trigger_price
        if near_level and failed_to_close_beyond:
            return "exhausted_spike"
    known = [r for r in approach_rvols if r is not None]
    if known and all(r < rvol_surge for r in known) and known == sorted(known):
        return "constructive"
    return "neutral"


def _relative_strength_strong(
    session_bars: list[RawBar],
    trigger_idx: int,
    mbr: float,
    spy_prior_bars: list[RawBar],
    side: str,
    near_extreme_mbr: float,
    index_mbr: float | None,
) -> bool:
    """spec §0: the stock's last pre-trigger close within ``near_extreme_mbr`` of its own
    session-high-so-far while SPY's last close is within the same tolerance (index-MBR) of ITS
    session-low-so-far -- mirrored for shorts. ``False`` (never a guess) when either MBR is
    unavailable or SPY carries no prior bars."""
    if mbr == 0.0 or not index_mbr or not spy_prior_bars:
        return False
    stock_close = session_bars[trigger_idx - 1].close
    prior_stock_bars = session_bars[:trigger_idx]
    stock_high = max(bar.high for bar in prior_stock_bars)
    stock_low = min(bar.low for bar in prior_stock_bars)
    spy_close = spy_prior_bars[-1].close
    spy_high = max(bar.high for bar in spy_prior_bars)
    spy_low = min(bar.low for bar in spy_prior_bars)
    if side == "long":
        return (
            abs(stock_close - stock_high) <= near_extreme_mbr * mbr
            and abs(spy_close - spy_low) <= near_extreme_mbr * index_mbr
        )
    return (
        abs(stock_close - stock_low) <= near_extreme_mbr * mbr
        and abs(spy_close - spy_high) <= near_extreme_mbr * index_mbr
    )


def _market_block(
    session_bars: list[RawBar],
    trigger_idx: int,
    index_bars: list[RawBar],
    session_date: str,
    side: str,
    mbr: float,
    index_baseline: dict,
    params: dict,
) -> dict:
    """spec §0's market-context disclosure block -- never a gate. Null ``direction``/
    ``market_move_mbr`` (with an honest ``reason``) when SPY has no bars for the session, when
    there are not yet ``mkt_lookback_bars`` prior SPY bars this early in the session, or when
    SPY's own baseline MBR is unavailable to normalize the move."""
    trigger_epoch = session_bars[trigger_idx].epoch
    index_mbr = index_baseline.get("mbr") or None
    mkt = market_context(index_bars, session_date, trigger_epoch, params["mkt_lookback_bars"])
    spy_session_bars = rth_session_slice(index_bars, session_date)
    spy_prior_bars = [bar for bar in spy_session_bars if bar.epoch < trigger_epoch]

    if mkt is None:
        reason = (
            "no SPY bars recorded for the session"
            if not spy_session_bars
            else "fewer than the market lookback window's worth of SPY bars before the trigger"
        )
        return {
            "direction": None, "market_move_mbr": None, "book_would_skip_market": False,
            "relative_strength_strong": False, "source": "SPY", "reason": reason,
        }
    if index_mbr is None:
        return {
            "direction": None, "market_move_mbr": None, "book_would_skip_market": False,
            "relative_strength_strong": _relative_strength_strong(
                session_bars, trigger_idx, mbr, spy_prior_bars, side,
                params["near_extreme_mbr"], index_mbr,
            ),
            "source": "SPY",
            "reason": "SPY's own baseline MBR is unavailable -- cannot normalize the market move",
        }

    sign = 1.0 if side == "long" else -1.0
    move_mbr = mkt["move"] / index_mbr
    signed = sign * move_mbr
    band = params["mkt_neutral_band_mbr"]
    if signed > band:
        direction = "supportive"
    elif signed < -band:
        direction = "against"
    else:
        direction = "neutral"
    return {
        "direction": direction,
        "market_move_mbr": move_mbr,
        "book_would_skip_market": direction == "against",
        "relative_strength_strong": _relative_strength_strong(
            session_bars, trigger_idx, mbr, spy_prior_bars, side, params["near_extreme_mbr"], index_mbr
        ),
        "source": "SPY",
        "reason": None,
    }


def detect_opening_range_breaks(
    session_bars: list[RawBar],
    or_result: dict,
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
    prior_close: float | None,
) -> tuple[dict | None, dict | None]:
    """spec §3.1 (``open_high_break``) / §3.2 (``open_low_break``) -- one shared implementation
    (the two are an exact mirror, sharing all formation/trigger/invalidation logic; only ONE of
    the pair can ever fire per symbol-session, so a single walk deciding "which side, if either,
    breaks first" is the natural -- and only sound -- shape). Returns ``(signal, diagnostic)``:
    at most one is non-``None``. ``diagnostic`` is set only for the ``ambiguous_outside_bar`` case
    (spec: a bar strictly breaking BOTH opening-range sides with neither previously broken).
    A narrow-opening-range gate failure or a session that never breaks either side is a legitimate
    "the setup did not form" outcome -- ``(None, None)``, never an absence (the caller's
    ``absences`` list is reserved for DATA-quality gaps, not formation misses)."""
    mbr = baseline["mbr"]
    or_high, or_low = or_result["high"], or_result["low"]
    if or_result["width"] > params["narrow_or_max_mbr"] * mbr:
        return None, None

    first_eligible_slot = params["or_minutes"] // 5
    trigger_idx: int | None = None
    side: str | None = None
    for idx in range(first_eligible_slot, len(session_bars)):
        bar = session_bars[idx]
        breaks_high = bar.high > or_high
        breaks_low = bar.low < or_low
        if breaks_high and breaks_low:
            return None, {
                "symbol": symbol, "diagnostic": "ambiguous_outside_bar", "at_utc": _iso(bar.epoch),
            }
        if breaks_high:
            trigger_idx, side = idx, "long"
            break
        if breaks_low:
            trigger_idx, side = idx, "short"
            break

    if trigger_idx is None:
        return None, None

    trigger_bar = session_bars[trigger_idx]
    trigger_price = or_high if side == "long" else or_low
    or_width = or_high - or_low

    if side == "long":
        entry = max(trigger_bar.open, trigger_price)
        entry_kind = "level" if trigger_bar.open < trigger_price else "gap_open"
        gapped_beyond_chase = trigger_bar.open > trigger_price * (1.0 + params["max_chase_frac"])
        invalidation_price = or_low - params["stop_pad_frac"] * or_width
    else:
        entry = min(trigger_bar.open, trigger_price)
        entry_kind = "level" if trigger_bar.open > trigger_price else "gap_open"
        gapped_beyond_chase = trigger_bar.open < trigger_price * (1.0 - params["max_chase_frac"])
        invalidation_price = or_high + params["stop_pad_frac"] * or_width

    approach_start = max(0, trigger_idx - params["approach_bars"])
    approach_indices = list(range(approach_start, trigger_idx))
    approach_rvols = [_rvol(session_bars[i], i, baseline["slot_volume_medians"]) for i in approach_indices]
    known_rvols = [r for r in approach_rvols if r is not None]
    approach_rvol_max = max(known_rvols) if known_rvols else None
    rvol_trigger_bar = _rvol(trigger_bar, trigger_idx, baseline["slot_volume_medians"])

    spike_verdict = _spike_into_trigger_verdict(
        session_bars, approach_indices, approach_rvols, trigger_price, side, mbr,
        params["rvol_surge"], params["near_extreme_mbr"],
    )

    spiky_approach = False
    if trigger_idx - 1 >= 0:
        spiky_approach = vertical_move(
            session_bars, trigger_idx - 1, 1, params["vertical_bar_mbr"] * mbr,
            "up" if side == "long" else "down",
        )

    if side == "long":
        zone_lo, zone_hi = trigger_price - params["near_extreme_mbr"] * mbr, trigger_price
    else:
        zone_lo, zone_hi = trigger_price, trigger_price + params["near_extreme_mbr"] * mbr
    attempt_count = len(zone_touches(session_bars[first_eligible_slot:trigger_idx], zone_lo, zone_hi))

    market = _market_block(
        session_bars, trigger_idx, index_bars, session_date, side, mbr, index_baseline, params
    )

    open_vs_prior_close_pct = (
        (session_bars[0].open - prior_close) / prior_close * 100.0 if prior_close else None
    )

    principles = ["P4"] if spike_verdict == "constructive" else []

    signal = {
        "symbol": symbol,
        "setup_id": "open_high_break" if side == "long" else "open_low_break",
        "side": side,
        "trigger_ts": _iso(trigger_bar.epoch),
        "trigger_price": trigger_price,
        "entry": entry,
        "entry_kind": entry_kind,
        "price_low": or_low,
        "price_high": or_high,
        "invalidation_price": invalidation_price,
        "geometry": {
            "or_high": or_high,
            "or_low": or_low,
            "or_width_mbr": or_result["width"] / mbr,
            "or_bars_used": or_result["bars_used"],
            "opening_range_basis": or_result["basis"],
            "slots_to_break": trigger_idx,
            "open_vs_prior_close_pct": open_vs_prior_close_pct,
        },
        "volume": {
            "rvol_trigger_bar": rvol_trigger_bar,
            "approach_rvol_max": approach_rvol_max,
            "spike_into_trigger_verdict": spike_verdict,
            "spiky_approach": spiky_approach,
        },
        "market": market,
        "principles": principles,
        "disclosures": {
            "gapped_beyond_chase": gapped_beyond_chase,
            "session_bar_count": len(session_bars),
            "attempt_count": attempt_count,
            "bars_to_close": len(session_bars) - 1 - trigger_idx,
            # No other detector family exists yet this iteration (the OR-break pair is mutually
            # exclusive with itself -- at most one signal per symbol-session) and no
            # euphoria/capitulation marker detector exists yet either (J-05) -- both fields are
            # wired for real cross-detector reads starting J-04/J-05; honestly empty until then.
            "concurrent_signals": [],
            "euphoria_recent": False,
            "capitulation_recent": False,
        },
    }
    return signal, None
