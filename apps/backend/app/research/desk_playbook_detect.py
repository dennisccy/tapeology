"""The Playbook's detectors (Era B2). J-01 shipped the opening-range-break family
(``docs/playbook-detector-spec.md`` §3.1-3.2); J-04 added the continuation family --
``detect_jbe``/``detect_dbi`` (§3.3-3.4, one shared internal walk, direction-flipped) and
``detect_cup_handle`` (§3.6). J-05 added the climax family -- ``detect_capitulation`` (§3.5,
entry) and ``detect_euphoria`` (§3.5, the exact mirror UP, a MARKER only -- never a served
signal). J-06 (this iteration) adds the remaining three detectors -- ``detect_range_trade``
(§3.7, PROVISIONAL tier) and ``detect_double_top``/``detect_double_bottom`` (§3.8-3.9, the exact
mirror) -- each built purely out of ``desk_playbook_features.py``'s eight primitives plus the
``playbook_parameters()`` dict a caller hands in.

**J-06 design note -- range_trade's trigger grammar.** Spec §3.7 (and the iteration's own framing)
describes range_trade's bounce trigger as "the SAME reversal-bar grammar the capitulation bounce
already implements... one shared mechanism, not a second vague one". This module honors that at
the GRAMMAR level -- the identical local predicate (`bar.high > session_bars[t-1].high` / the
mirrored low check), scanned within `PLAYBOOK_BOUNCE_MAX_BARS` of an anchor, `T = high[t-1]` --
but does NOT literally route range_trade's trigger through `_find_climax_formation`: that
function's own arming precondition is a `vertical_move` formation with re-anchoring (a DIFFERENT
formation range_trade does not share -- range_trade arms via `zone_touches` of a tested-and-held
zone, never a vertical move), so forcing a shared call site would either bend
`_find_climax_formation` to a formation it was never built for or silently disable its own
re-anchoring for capitulation/euphoria. The reversal-bar predicate itself is small enough (one
comparison) that duplicating exactly that one line, under a shared name and cross-referenced
docstring, is the honest reading of "the same grammar" without risking J-05's own byte-identical
behavior for a J-06 formation it does not need.

**J-04's own primitives are all reused, none added.** ``consolidation_range`` (JBE/DBI's base,
shared with the module's own precedent of "shared geometry for JBE/DBI's base and cup-and-handle's
handle") and ``swing_pivots`` (cup-and-handle's rims) both already exist in
``desk_playbook_features.py`` from J-01/J-02 -- this iteration imports them, it does not extend
that file (expected zero diff, per the goal's own Constraints).

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

import statistics
from datetime import datetime, timezone

from ..providers.adapters.base import RawBar
from .desk_playbook_features import (
    consolidation_range,
    market_context,
    rth_session_slice,
    side_sign,
    swing_pivots,
    vertical_move,
    zone_touches,
)

__all__ = [
    "detect_opening_range_breaks",
    "detect_jbe",
    "detect_dbi",
    "detect_cup_handle",
    "detect_capitulation",
    "detect_euphoria",
    "detect_range_trade",
    "detect_double_top",
    "detect_double_bottom",
]


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

    sign = side_sign(side)
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


# --- J-04: the continuation family -- jbe (spec §3.3) / dbi (spec §3.4, the exact mirror) ---------
#
# ONE shared internal walk (``_find_one_continuation``), direction-parameterized by ``side`` --
# spec §3.4 states dbi IS jbe "exact mirror... same primitives, gates, and cap, direction-flipped",
# so a second, hand-flipped copy would be the second-implementation drift the whole codebase is
# built to avoid (the module's own ``side_sign``/``_market_block`` precedent). ``detect_jbe``/
# ``detect_dbi`` are the two thin, setup-id-naming callers a test or ``compute_playbook`` actually
# imports.


def _base_lows_ascending(base_bars: list[RawBar], side: str) -> bool:
    """The ADAPTATION "ascending-triangle" base-shape disclosure (spec §3.3): for a long base
    (jbe), are the LOWS non-decreasing bar to bar; for a short base (dbi, the mirror), are the
    HIGHS non-increasing -- one served field name (``base_lows_ascending``, per the goal's own
    Data-contract table), the direction-appropriate triangle check underneath."""
    if len(base_bars) < 2:
        return True
    if side == "long":
        return all(base_bars[i].low >= base_bars[i - 1].low for i in range(1, len(base_bars)))
    return all(base_bars[i].high <= base_bars[i - 1].high for i in range(1, len(base_bars)))


def _find_one_continuation(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
    side: str,
    setup_id: str,
    min_base_start: int,
    previous_jump_mbr: float | None,
) -> dict | None:
    """ONE ladder step: the first bar-by-bar-rolling ``(base, jump, trigger)`` formation found at
    or after ``min_base_start`` (the caller's own "a second base must start after the first
    trigger bar" cap discipline) -- ``None`` if no such formation ever forms and triggers before
    session close (spec §3.3 edge case: "a base still open at session close emits nothing").

    The base itself is RECOMPUTED at every candidate trigger bar ``t`` via
    ``consolidation_range(session_bars, t - 1, ...)`` -- the shared primitive's own "maximal
    window ending at ``end_idx``" contract rolls the base forward bar by bar exactly like the OR
    break's fixed-opening-range trigger scan rolls its OWN search forward, just over a dynamic
    (not session-fixed) base. Reusing the jump's own ``PLAYBOOK_JUMP_MIN_MOVE_MBR`` floor as an
    (undocumented but structural) safety net: any window wide enough to swallow part of the jump
    leg fails ``consolidation_range``'s own ``max_range`` gate before this function ever sees it,
    so the maximal-window search naturally lands on the tight base, never the jump-plus-base
    blend, without this function needing a second range check of its own."""
    mbr = baseline["mbr"]
    slot_medians = baseline["slot_volume_medians"]
    lookback = params["jump_lookback_bars"]
    min_bars = params["base_min_bars"]
    max_bars = params["base_max_bars"]
    max_range = params["base_max_range_mbr"] * mbr
    n = len(session_bars)

    for t in range(min_bars, n):
        base = consolidation_range(session_bars, t - 1, min_bars, max_bars, max_range)
        if base is None:
            continue
        start_idx, u, l = base
        if start_idx < min_base_start or start_idx - lookback < 0:
            continue

        base_range = u - l
        lookback_bars = session_bars[start_idx - lookback : start_idx]
        if side == "long":
            jump = u - min(bar.low for bar in lookback_bars)
        else:
            jump = max(bar.high for bar in lookback_bars) - l
        if jump < params["jump_min_mult"] * base_range or jump < params["jump_min_move_mbr"] * mbr:
            continue

        prior_bars = session_bars[:t]
        if side == "long":
            near_extreme_ok = u >= max(bar.high for bar in prior_bars) - params["near_extreme_mbr"] * mbr
        else:
            near_extreme_ok = l <= min(bar.low for bar in prior_bars) + params["near_extreme_mbr"] * mbr
        if not near_extreme_ok:
            continue

        base_bars = session_bars[start_idx:t]
        jump_rvols = [
            _rvol(bar, idx, slot_medians)
            for idx, bar in enumerate(lookback_bars, start=start_idx - lookback)
        ]
        known_jump_rvols = [r for r in jump_rvols if r is not None]
        if not known_jump_rvols:
            continue
        median_jump_rvol = statistics.median(known_jump_rvols)
        if median_jump_rvol < 1.0 or max(known_jump_rvols) < params["rvol_elevated"]:
            continue

        base_rvols = [_rvol(bar, idx, slot_medians) for idx, bar in enumerate(base_bars, start=start_idx)]
        known_base_rvols = [r for r in base_rvols if r is not None]
        if not known_base_rvols:
            continue
        if statistics.median(known_base_rvols) > params["vol_contrast_ratio"] * median_jump_rvol:
            continue

        bar_t = session_bars[t]
        triggers = bar_t.high > u if side == "long" else bar_t.low < l
        if not triggers:
            continue

        # --- formation armed AND triggered at t -- build the signal -----------------------------
        trigger_price = u if side == "long" else l
        if side == "long":
            entry = max(bar_t.open, trigger_price)
            entry_kind = "level" if bar_t.open < trigger_price else "gap_open"
            gapped_beyond_chase = bar_t.open > trigger_price * (1.0 + params["max_chase_frac"])
            invalidation_price = l - params["stop_pad_frac"] * base_range
        else:
            entry = min(bar_t.open, trigger_price)
            entry_kind = "level" if bar_t.open > trigger_price else "gap_open"
            gapped_beyond_chase = bar_t.open < trigger_price * (1.0 - params["max_chase_frac"])
            invalidation_price = u + params["stop_pad_frac"] * base_range

        jump_mbr = jump / mbr
        ladder_step_ratio = jump_mbr / previous_jump_mbr if previous_jump_mbr else None

        approach_start = max(0, t - params["approach_bars"])
        approach_indices = list(range(approach_start, t))
        approach_rvols = [_rvol(session_bars[i], i, slot_medians) for i in approach_indices]
        known_approach = [r for r in approach_rvols if r is not None]
        approach_rvol_max = max(known_approach) if known_approach else None
        rvol_trigger_bar = _rvol(bar_t, t, slot_medians)
        spike_verdict = _spike_into_trigger_verdict(
            session_bars, approach_indices, approach_rvols, trigger_price, side, mbr,
            params["rvol_surge"], params["near_extreme_mbr"],
        )
        spiky_approach = False
        if t - 1 >= 0:
            spiky_approach = vertical_move(
                session_bars, t - 1, 1, params["vertical_bar_mbr"] * mbr,
                "up" if side == "long" else "down",
            )
        if side == "long":
            zone_lo, zone_hi = trigger_price - params["near_extreme_mbr"] * mbr, trigger_price
        else:
            zone_lo, zone_hi = trigger_price, trigger_price + params["near_extreme_mbr"] * mbr
        attempt_count = len(zone_touches(session_bars[:t], zone_lo, zone_hi))
        market = _market_block(
            session_bars, t, index_bars, session_date, side, mbr, index_baseline, params,
        )

        return {
            "symbol": symbol,
            "setup_id": setup_id,
            "side": side,
            "trigger_ts": _iso(bar_t.epoch),
            "trigger_price": trigger_price,
            "entry": entry,
            "entry_kind": entry_kind,
            "price_low": l,
            "price_high": u,
            "invalidation_price": invalidation_price,
            "geometry": {
                "slots_to_break": t,
                "jump_mbr": jump_mbr,
                "base_range_mbr": base_range / mbr,
                "base_bars": t - start_idx,
                "base_flatline": (base_range / mbr) <= params["base_flatline_max_mbr"],
                "base_lows_ascending": _base_lows_ascending(base_bars, side),
                "ladder_step_ratio": ladder_step_ratio,
            },
            "volume": {
                "rvol_trigger_bar": rvol_trigger_bar,
                "approach_rvol_max": approach_rvol_max,
                "spike_into_trigger_verdict": spike_verdict,
                "spiky_approach": spiky_approach,
            },
            "market": market,
            "principles": ["P3", "P4"],
            "disclosures": {
                "gapped_beyond_chase": gapped_beyond_chase,
                "session_bar_count": len(session_bars),
                "attempt_count": attempt_count,
                "bars_to_close": len(session_bars) - 1 - t,
                "concurrent_signals": [],
                "euphoria_recent": False,
                "capitulation_recent": False,
            },
        }
    return None


def _continuation_signals(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
    side: str,
    setup_id: str,
) -> list[dict]:
    """Every ladder step of ONE continuation setup for this symbol-session, chronological order --
    up to ``PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION`` (spec §3.3: "every other detector caps at 1 --
    JBE/DBI's own cap is the ladder exception, shared by name with DBI since it is jbe's mirror,
    not a second cap). Each step's own search starts strictly after the PRIOR step's trigger bar
    (``min_base_start``) -- the exact ladder-cap mechanism this iteration is the first to actually
    exercise (see ``desk_playbook._baseline_seed``'s own ``firing_index`` discriminator, built
    ahead of need in J-03)."""
    if baseline["mbr"] == 0.0:
        return []
    signals: list[dict] = []
    min_base_start = 0
    previous_jump_mbr: float | None = None
    for _ in range(params["max_jbe_signals_per_session"]):
        found = _find_one_continuation(
            session_bars, baseline, symbol, session_date, index_bars, index_baseline, params,
            side, setup_id, min_base_start, previous_jump_mbr,
        )
        if found is None:
            break
        signals.append(found)
        min_base_start = found["geometry"]["slots_to_break"] + 1
        previous_jump_mbr = found["geometry"]["jump_mbr"]
    return signals


def detect_jbe(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
) -> list[dict]:
    """spec §3.3 -- jump-base-explosion, long only. Up to
    ``PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION`` ladder-step signals, chronological order (never a
    diagnostic -- a formation that never forms or never triggers is a legitimate "did not form"
    outcome, exactly like the OR-break pair's own ``(None, None)`` case)."""
    return _continuation_signals(
        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params,
        "long", "jbe",
    )


def detect_dbi(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
) -> list[dict]:
    """spec §3.4 -- drop-base-implosion, short only, the exact direction-flipped mirror of
    ``detect_jbe`` (same shared ``_continuation_signals`` walk, ``side="short"``)."""
    return _continuation_signals(
        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params,
        "short", "dbi",
    )


# --- J-04: cup_handle (spec §3.6, long only in v1) -------------------------------------------------


def detect_cup_handle(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
) -> dict | None:
    """spec §3.6 -- left/right rims via confirmed swing-high pivots, a cup between them, a handle
    after the right rim, trigger on the rim break. Searches every ``(left_rim, right_rim)`` pivot
    pair in chronological order and returns the FIRST one whose full formation (cup depth/duration/
    volume, handle retrace/duration/volume) validates AND triggers -- capped at 1 per
    symbol-session by construction (this function returns at most one signal, never a list).

    A handle retracing beyond ``PLAYBOOK_HANDLE_MAX_RETRACE_FRAC`` of cup depth, or one that runs
    longer than ``PLAYBOOK_HANDLE_MAX_DURATION_FRAC`` of the cup's own duration, voids ONLY this
    rim pair (spec §3.6 edge case: "voids the formation silently... may still fire as an
    independent hypothesis" under a different detector, or under a LATER rim pair here) -- it does
    not re-check a later bar for the SAME pair once the rim has already broken, since the breakout
    already happened and failed the gate at that exact bar.

    **Lookahead law, made concrete for a pivot-based detector.** ``swing_pivots`` runs once over
    the WHOLE ``session_bars`` it is handed, but a pivot's OWN price/index/``confirmed_at`` are a
    function only of its fixed local +/-lookback window -- truncating the array anywhere at or
    after a pivot's ``confirmed_at`` leaves that pivot unchanged (the property the generic
    truncation test proves). What this function must not do is USE a rim whose ``confirmed_at``
    falls ON OR AFTER the trigger bar -- spec §3.6: "Both rims pivot-confirmed strictly before
    ``t``". The trigger scan below therefore starts no earlier than
    ``right["confirmed_at"] + 1``, never merely ``handle_start + 1``."""
    mbr = baseline["mbr"]
    if mbr == 0.0:
        return None
    slot_medians = baseline["slot_volume_medians"]
    pivots = swing_pivots(session_bars, params["pivot_lookback_bars"])
    highs = sorted((p for p in pivots if p["kind"] == "high"), key=lambda p: p["index"])
    n = len(session_bars)

    for left_i, left in enumerate(highs):
        for right in highs[left_i + 1 :]:
            cup_bars_span = right["index"] - left["index"]
            if cup_bars_span < params["cup_min_bars"]:
                continue
            if abs(right["price"] - left["price"]) > params["rim_match_mbr"] * mbr:
                continue
            left_session_high = max(bar.high for bar in session_bars[: left["confirmed_at"] + 1])
            if left["price"] < left_session_high - params["near_extreme_mbr"] * mbr:
                continue
            right_session_high = max(bar.high for bar in session_bars[: right["confirmed_at"] + 1])
            if right["price"] < right_session_high - params["near_extreme_mbr"] * mbr:
                continue

            cup_window = session_bars[left["index"] + 1 : right["index"]]
            if not cup_window:
                continue
            cup_bottom_low = min(bar.low for bar in cup_window)
            depth = left["price"] - cup_bottom_low
            if depth < params["min_structure_depth_mbr"] * mbr:
                continue

            cup_bars_all = session_bars[left["index"] : right["index"] + 1]
            third = max(1, len(cup_bars_all) // 3)
            first_third, last_third = cup_bars_all[:third], cup_bars_all[-third:]
            middle_third = cup_bars_all[third : len(cup_bars_all) - third]
            if not middle_third:
                continue
            first_rvols = [
                _rvol(bar, left["index"] + i, slot_medians) for i, bar in enumerate(first_third)
            ]
            last_start = right["index"] - third + 1
            last_rvols = [_rvol(bar, last_start + i, slot_medians) for i, bar in enumerate(last_third)]
            middle_start = left["index"] + third
            middle_rvols = [
                _rvol(bar, middle_start + i, slot_medians) for i, bar in enumerate(middle_third)
            ]
            known_outer = [r for r in first_rvols + last_rvols if r is not None]
            known_middle = [r for r in middle_rvols if r is not None]
            if not known_outer or not known_middle:
                continue
            outer_median = statistics.median(known_outer)
            middle_median = statistics.median(known_middle)
            if middle_median > params["vol_contrast_ratio"] * outer_median:
                continue

            trigger_price = max(left["price"], right["price"])
            handle_start = right["index"] + 1
            # Both rims pivot-confirmed strictly before t (spec §3.6): the earliest legal trigger
            # candidate is the later of "at least 1 handle bar exists" and "the right rim's own
            # confirmation window has fully elapsed" -- confirming BOTH rims, since left's own
            # confirmed_at is always earlier (left.index < right.index).
            search_start = max(handle_start + 1, right["confirmed_at"] + 1)
            trigger_idx: int | None = None
            for t in range(search_start, n):
                if session_bars[t].high > trigger_price:
                    trigger_idx = t
                    break
            if trigger_idx is None:
                continue  # handle still open at session close -- spec §3.6 edge case, emits nothing

            handle_bars = session_bars[handle_start:trigger_idx]
            retrace_floor = right["price"] - params["handle_max_retrace_frac"] * depth
            handle_bottom = min(bar.low for bar in handle_bars)
            if handle_bottom < retrace_floor:
                continue  # handle retraced beyond 50% of cup depth -- voids silently
            handle_duration = len(handle_bars)
            if handle_duration > params["handle_max_duration_frac"] * cup_bars_span:
                continue
            handle_rvols = [_rvol(bar, handle_start + i, slot_medians) for i, bar in enumerate(handle_bars)]
            known_handle = [r for r in handle_rvols if r is not None]
            if not known_handle:
                continue
            handle_median = statistics.median(known_handle)
            if handle_median > params["vol_contrast_ratio"] * outer_median:
                continue

            # --- every gate passed -- build the signal ------------------------------------------
            trigger_bar = session_bars[trigger_idx]
            entry = max(trigger_bar.open, trigger_price)
            entry_kind = "level" if trigger_bar.open < trigger_price else "gap_open"
            gapped_beyond_chase = trigger_bar.open > trigger_price * (1.0 + params["max_chase_frac"])
            invalidation_price = handle_bottom - params["stop_pad_frac"] * (trigger_price - handle_bottom)

            approach_start = max(0, trigger_idx - params["approach_bars"])
            approach_indices = list(range(approach_start, trigger_idx))
            approach_rvols = [_rvol(session_bars[i], i, slot_medians) for i in approach_indices]
            known_approach = [r for r in approach_rvols if r is not None]
            approach_rvol_max = max(known_approach) if known_approach else None
            rvol_trigger_bar = _rvol(trigger_bar, trigger_idx, slot_medians)
            spike_verdict = _spike_into_trigger_verdict(
                session_bars, approach_indices, approach_rvols, trigger_price, "long", mbr,
                params["rvol_surge"], params["near_extreme_mbr"],
            )
            spiky_approach = False
            if trigger_idx - 1 >= 0:
                spiky_approach = vertical_move(
                    session_bars, trigger_idx - 1, 1, params["vertical_bar_mbr"] * mbr, "up",
                )
            zone_lo, zone_hi = trigger_price - params["near_extreme_mbr"] * mbr, trigger_price
            attempt_count = len(zone_touches(session_bars[:trigger_idx], zone_lo, zone_hi))
            market = _market_block(
                session_bars, trigger_idx, index_bars, session_date, "long", mbr, index_baseline, params,
            )
            handle_duration_frac = handle_duration / cup_bars_span

            return {
                "symbol": symbol,
                "setup_id": "cup_handle",
                "side": "long",
                "trigger_ts": _iso(trigger_bar.epoch),
                "trigger_price": trigger_price,
                "entry": entry,
                "entry_kind": entry_kind,
                "price_low": cup_bottom_low,
                "price_high": trigger_price,
                "invalidation_price": invalidation_price,
                "geometry": {
                    "slots_to_break": trigger_idx,
                    "cup_bars": cup_bars_span,
                    "cup_depth_mbr": depth / mbr,
                    "handle_retrace_frac": (right["price"] - handle_bottom) / depth,
                    "handle_duration_frac": handle_duration_frac,
                    "cup_optimal": cup_bars_span >= params["cup_optimal_bars"],
                    "handle_duration_desirable": handle_duration_frac <= params["handle_desirable_duration_frac"],
                    "cup_middle_third_rvol_median": middle_median,
                    "cup_outer_third_rvol_median": outer_median,
                    "handle_rvol_median": handle_median,
                },
                "volume": {
                    "rvol_trigger_bar": rvol_trigger_bar,
                    "approach_rvol_max": approach_rvol_max,
                    "spike_into_trigger_verdict": spike_verdict,
                    "spiky_approach": spiky_approach,
                },
                "market": market,
                "principles": ["P4", "P5-inverse"],
                "disclosures": {
                    "gapped_beyond_chase": gapped_beyond_chase,
                    "session_bar_count": len(session_bars),
                    "attempt_count": attempt_count,
                    "bars_to_close": len(session_bars) - 1 - trigger_idx,
                    "concurrent_signals": [],
                    "euphoria_recent": False,
                    "capitulation_recent": False,
                },
            }
    return None


# --- J-05: the climax family -- capitulation (spec §3.5, entry) + euphoria (spec §3.5, the exact
# mirror UP, a MARKER only) -------------------------------------------------------------------------
#
# ONE shared walk (``_find_climax_formation``), direction-parameterized by ``direction`` -- spec
# §3.5 states euphoria IS capitulation's "exact mirror UP... same constants", so a second,
# hand-flipped copy would be the second-implementation drift the module's own
# ``_continuation_signals``/``side_sign`` precedent already avoids for jbe/dbi.


def _rvol_series(session_bars: list[RawBar], slot_volume_medians: dict[int, float]) -> list[float | None]:
    """Every bar's own RVOL against its baseline slot median, in session order -- the parallel
    array ``vertical_move``'s ``require_volume`` clause needs (spec §0's ONE relative-volume
    definition, computed once per session rather than re-derived per candidate climax bar)."""
    return [_rvol(bar, idx, slot_volume_medians) for idx, bar in enumerate(session_bars)]


def _find_climax_formation(
    session_bars: list[RawBar],
    rvols: list[float | None],
    params: dict,
    mbr: float,
    direction: str,
) -> tuple[int, int, int] | None:
    """spec §3.5's shared vertical-move + reversal-bar grammar, direction-parameterized
    (``direction="down"`` powers ``detect_capitulation``, ``"up"`` powers ``detect_euphoria``).
    Returns ``(window_start, climax_idx, trigger_idx)`` for the FIRST candidate climax bar ``v``
    (a ``vertical_move`` formation ending at ``v``, with the ``require_volume`` clause) whose
    reversal-bar trigger fires within ``PLAYBOOK_BOUNCE_MAX_BARS`` of the bar's own (possibly
    re-anchored) climax -- ``None`` if no candidate anywhere in the session both forms and triggers
    (a later, independent formation may still succeed after an earlier one expires, mirroring
    ``detect_cup_handle``'s own "first (left_rim, right_rim) pair whose full formation validates
    AND triggers" search -- never just the first candidate encountered, whether or not it pans
    out).

    **Re-anchoring, made concrete.** ``leg_low``/``leg_high`` (``extreme`` below) is the running
    minimum low (``direction="down"``) or maximum high (``"up"``) through the bar STRICTLY BEFORE
    the candidate trigger bar ``t`` -- spec: "min low through ``t-1``". At every step, bar ``t-1``
    is checked against the running extreme BEFORE bar ``t`` is evaluated as a trigger candidate: a
    new extreme re-anchors the climax bar ``v`` to ``t-1`` itself (spec: "a new low after ``v``
    re-anchors ``v`` -- the panic still running"), which also resets the bounce-window clock (the
    window is measured from the CURRENT ``v``, not the original one) -- the panic continuing is
    never mistaken for the window expiring. The trigger predicate itself (``high > high[t-1]`` /
    the mirrored low check) always compares against the bar IMMEDIATELY before ``t``, never against
    the climax bar's own high/low -- spec: "first-strength reversal bar", a purely local fact."""
    window = params["vertical_window_bars"]
    k = params["vertical_move_mbr"] * mbr
    bounce_max = params["bounce_max_bars"]
    rvol_surge = params["rvol_surge"]
    n = len(session_bars)

    for v0 in range(window, n):
        if not vertical_move(
            session_bars, v0, window, k, direction,
            require_volume=True, rvol_surge=rvol_surge, rvols=rvols,
        ):
            continue
        window_start = v0 - window + 1
        extreme = session_bars[v0].low if direction == "down" else session_bars[v0].high
        cur_v = v0
        t = v0 + 1
        while t < n:
            prev = session_bars[t - 1]
            if t - 1 > cur_v:
                is_new_extreme = prev.low < extreme if direction == "down" else prev.high > extreme
                if is_new_extreme:
                    extreme = prev.low if direction == "down" else prev.high
                    cur_v = t - 1
            if (t - cur_v) > bounce_max:
                break
            bar = session_bars[t]
            reverses = (
                bar.high > session_bars[t - 1].high if direction == "down"
                else bar.low < session_bars[t - 1].low
            )
            if reverses:
                return window_start, cur_v, t
            t += 1
    return None


def detect_capitulation(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
) -> dict | None:
    """spec §3.5 -- capitulation entry, long only: a vertical decline (``vertical_move`` DOWN with
    the ``require_volume`` clause this iteration is the first to exercise) followed by the first
    bar within ``PLAYBOOK_BOUNCE_MAX_BARS`` of the (possibly re-anchored) climax bar whose high
    exceeds the PRIOR bar's own high (``T = high[t-1]`` -- fully known at ``t-1``; the crossing at
    ``t`` is the only bar-``t`` fact the trigger itself depends on). Capped at 1 per symbol-session
    by construction (this function returns at most one signal, mirroring ``detect_cup_handle``'s
    own single-return shape). Follows the SAME signal-assembly shape as
    ``detect_opening_range_breaks``/the continuation family (entry/entry_kind via the shared
    stop-through-fill convention, ``market`` via ``_market_block``, the shared volume/attempt-count
    disclosures) so it flows through ``desk_playbook._measure_signal`` unmodified."""
    mbr = baseline["mbr"]
    if mbr == 0.0:
        return None
    slot_medians = baseline["slot_volume_medians"]
    rvols = _rvol_series(session_bars, slot_medians)
    found = _find_climax_formation(session_bars, rvols, params, mbr, "down")
    if found is None:
        return None
    window_start, climax_idx, trigger_idx = found

    leg_low = session_bars[climax_idx].low
    trigger_price = session_bars[trigger_idx - 1].high
    trigger_bar = session_bars[trigger_idx]
    entry = max(trigger_bar.open, trigger_price)
    entry_kind = "level" if trigger_bar.open < trigger_price else "gap_open"
    gapped_beyond_chase = trigger_bar.open > trigger_price * (1.0 + params["max_chase_frac"])
    invalidation_price = leg_low - params["stop_pad_frac"] * (trigger_price - leg_low)

    # Disclosures spec §3.5 names by name -- `decline_bars` spans the WHOLE decline leg (the
    # original vertical-move window's own start through the possibly-re-anchored climax bar), so a
    # formation that re-anchors reports a LONGER decline than the raw `vertical_window_bars`
    # constant, never a fixed value (see the re-anchoring fixture in
    # test_desk_playbook_detect.py). `decline_mbr` is the net decline from the close right before
    # the vertical move began through to the eventual (possibly re-anchored) leg low -- the same
    # "how far did price actually fall" reading `vertical_move`'s own net-move check uses, extended
    # through any re-anchoring.
    decline_bars = climax_idx - window_start + 1
    decline_mbr = (session_bars[window_start - 1].close - leg_low) / mbr
    climax_rvol = rvols[climax_idx]
    bars_from_climax_to_trigger = trigger_idx - climax_idx

    approach_start = max(0, trigger_idx - params["approach_bars"])
    approach_indices = list(range(approach_start, trigger_idx))
    approach_rvols = [rvols[i] for i in approach_indices]
    known_approach = [r for r in approach_rvols if r is not None]
    approach_rvol_max = max(known_approach) if known_approach else None
    rvol_trigger_bar = rvols[trigger_idx]
    spike_verdict = _spike_into_trigger_verdict(
        session_bars, approach_indices, approach_rvols, trigger_price, "long", mbr,
        params["rvol_surge"], params["near_extreme_mbr"],
    )
    spiky_approach = False
    if trigger_idx - 1 >= 0:
        spiky_approach = vertical_move(
            session_bars, trigger_idx - 1, 1, params["vertical_bar_mbr"] * mbr, "up",
        )
    zone_lo, zone_hi = trigger_price - params["near_extreme_mbr"] * mbr, trigger_price
    attempt_count = len(zone_touches(session_bars[:trigger_idx], zone_lo, zone_hi))
    market = _market_block(
        session_bars, trigger_idx, index_bars, session_date, "long", mbr, index_baseline, params,
    )

    return {
        "symbol": symbol,
        "setup_id": "capitulation",
        "side": "long",
        "trigger_ts": _iso(trigger_bar.epoch),
        "trigger_price": trigger_price,
        "entry": entry,
        "entry_kind": entry_kind,
        "price_low": leg_low,
        "price_high": trigger_price,
        "invalidation_price": invalidation_price,
        "geometry": {
            "slots_to_break": trigger_idx,
            "decline_mbr": decline_mbr,
            "decline_bars": decline_bars,
            "climax_rvol": climax_rvol,
            "bars_from_climax_to_trigger": bars_from_climax_to_trigger,
        },
        "volume": {
            "rvol_trigger_bar": rvol_trigger_bar,
            "approach_rvol_max": approach_rvol_max,
            "spike_into_trigger_verdict": spike_verdict,
            "spiky_approach": spiky_approach,
        },
        "market": market,
        "principles": ["P1"],
        "disclosures": {
            "gapped_beyond_chase": gapped_beyond_chase,
            "session_bar_count": len(session_bars),
            "attempt_count": attempt_count,
            "bars_to_close": len(session_bars) - 1 - trigger_idx,
            "concurrent_signals": [],
            "euphoria_recent": False,
            "capitulation_recent": False,
        },
    }


def detect_euphoria(session_bars: list[RawBar], baseline: dict, params: dict) -> dict | None:
    """spec §3.5's euphoria marker -- the exact mirror UP of ``detect_capitulation``'s own
    vertical-move + reversal-bar grammar (``_find_climax_formation`` with ``direction="up"``: the
    SAME shared walk, never a second hand-flipped copy), same constants, same cap of 1 per
    symbol-session, but returning a MARKER event only: no side, no entry, no invalidation, no
    geometry, no ``setup_id`` -- structurally incapable of becoming a served signal row (there is
    no field here a caller could even append to ``signals``/``signal_pool``/``baseline_pool`` with).
    BOOK: an exit/avoid signal -- the authors do not short strong stocks on euphoria; the book's own
    instruction IS "do nothing but note it," which is exactly this function's return shape. Its
    only output is the firing's own trigger-bar index, consumed exclusively by
    ``desk_playbook._decorate_markers`` and discarded immediately afterward -- this function is
    never called anywhere near ``signals``/``signal_pool``/``baseline_pool`` construction."""
    mbr = baseline["mbr"]
    if mbr == 0.0:
        return None
    rvols = _rvol_series(session_bars, baseline["slot_volume_medians"])
    found = _find_climax_formation(session_bars, rvols, params, mbr, "up")
    if found is None:
        return None
    _window_start, _climax_idx, trigger_idx = found
    return {"trigger_idx": trigger_idx}


# === J-06: the range family -- range_trade (spec §3.7, PROVISIONAL) + double_top/double_bottom
# (spec §3.8-3.9, exact mirror; double_top described) ===============================================


def _zone_held(bars: list[RawBar], touches: list[int], extreme: str, hold_tol: float) -> bool:
    """spec §3.7's arming clause "each later touch extending the extreme by <=
    ``PLAYBOOK_RANGE_HOLD_TOL_MBR * MBR``" (the BOOK's "and hold"), read per-touch exactly as
    written: for every touch AFTER the first, the amount by which that touch pushes the running
    extreme further out must not exceed ``hold_tol``. ``touches`` are ``zone_touches`` indices
    (the FIRST bar of each touch group, full-exit re-arm semantics), so a touch's own extension is
    measured over its whole group -- the prefix extreme through the bar before the NEXT touch
    group starts (or the end of ``bars``) minus the prefix extreme established strictly before
    this group. Bars between two touch groups cannot set a new extreme: a bar extending the low
    below the running low necessarily overlaps the low zone ``[SL, SL + NEAR_EXTREME*MBR]`` (its
    low is <= the zone's own floor) and is therefore itself inside a touch group -- so the group
    boundaries account for every extension. A single touch never "holds" (the caller's >= 2 gate
    rejects it first); returns ``False`` for fewer than two touches. ``extreme`` names WHICH
    running extreme this zone owns (``"low"`` for the low zone, ``"high"`` for the high zone) --
    deliberately not a side, since spec §3.7 requires BOTH zones to hold before EITHER side arms."""
    if len(touches) < 2:
        return False
    for k in range(1, len(touches)):
        start = touches[k]
        end = touches[k + 1] if k + 1 < len(touches) else len(bars)
        if extreme == "low":
            before = min(bar.low for bar in bars[:start])
            through = min(bar.low for bar in bars[:end])
            extension = before - through
        else:
            before = max(bar.high for bar in bars[:start])
            through = max(bar.high for bar in bars[:end])
            extension = through - before
        if extension > hold_tol:
            return False
    return True


def _range_trade_side(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
    side: str,
) -> dict | None:
    """ONE side of spec §3.7 -- support-bounce (``side="long"``) or resistance-fade
    (``side="short"``, the exact mirror). Walks candidate arming-completion bars ``t`` forward
    through the session; at each, the session range so far (``SH``/``SL`` over
    ``session_bars[:t]``, prefix extremes -- entry-time legal by construction, the same "recompute
    at every candidate" shape ``_find_one_continuation``'s own ``near_extreme_ok`` check uses) must
    be ``>= PLAYBOOK_RANGE_MIN_WIDTH_MBR`` wide, and BOTH zones (``[SL, SL + NEAR_EXTREME*MBR]``
    low and ``[SH - NEAR_EXTREME*MBR, SH]`` high) must show ``>= 2`` touches EACH, each later touch
    holding its own extreme within ``RANGE_HOLD_TOL_MBR * MBR`` (``_zone_held``) -- spec §3.7's
    arming clause in full, the BOOK's "test the low AND high twice and hold"; a session that tests
    one extreme twice while touching the other once is the breakout-only case Ch 13 excludes and
    arms nothing. The armed side's own zone additionally supplies the COMPLETING touch: an arming
    attempt is evaluated only at the first ``t`` at which that side's most recent touch is ``t - 1``
    itself (so the same touch pair is never re-attempted on later, untouched bars). A formation
    whose trigger reference is degenerate (``T <= SL`` long / ``T >= SH`` short, where the spec's
    own invalidation arithmetic inverts) is voided fail-closed, per spec §3.7's Edge cases. From
    the completing touch ``b``, scans forward up to
    ``PLAYBOOK_BOUNCE_MAX_BARS`` for the reversal-bar grammar (module docstring: the SAME predicate
    ``_find_climax_formation``'s own bounce trigger uses, ``high > high[t-1]`` long / ``low <
    low[t-1]`` short), gated at every candidate bar by the arming description's own hold tolerance
    (``min(low[b..t-1]) >= SL - HOLD_TOL*MBR`` long, mirrored short) -- the FIRST bar where the
    hold check fails ends the scan for this arming attempt (spec's own edge case: a strict break
    beyond the zone by more than the tolerance dissolves range-mode), and the outer loop then tries
    the NEXT arming completion. Capped at 1 by construction (single return, first (arm, trigger)
    pair found chronologically -- the ``detect_cup_handle`` rim-pair-search precedent)."""
    mbr = baseline["mbr"]
    if mbr == 0.0:
        return None
    slot_medians = baseline["slot_volume_medians"]
    n = len(session_bars)
    min_width = params["range_min_width_mbr"] * mbr
    near_extreme = params["near_extreme_mbr"] * mbr
    hold_tol = params["range_hold_tol_mbr"] * mbr
    bounce_max = params["bounce_max_bars"]

    for t in range(2, n):
        bars_so_far = session_bars[:t]
        session_high = max(bar.high for bar in bars_so_far)
        session_low = min(bar.low for bar in bars_so_far)
        if session_high - session_low < min_width:
            continue
        low_touches = zone_touches(bars_so_far, session_low, session_low + near_extreme)
        high_touches = zone_touches(bars_so_far, session_high - near_extreme, session_high)
        # spec §3.7's arming gate, in full: the high zone AND the low zone EACH with >= 2 touches,
        # EACH later touch holding its extreme within `RANGE_HOLD_TOL_MBR * MBR`. Both zones, not
        # just the armed side's own: the BOOK rule is "test the low AND high twice and hold" -- a
        # session that tests one extreme twice while touching the other once is the breakout-only
        # case Ch 13 excludes, and never arms a range trade on either side.
        if len(low_touches) < 2 or len(high_touches) < 2:
            continue
        if not _zone_held(bars_so_far, low_touches, "low", hold_tol):
            continue
        if not _zone_held(bars_so_far, high_touches, "high", hold_tol):
            continue
        armed_touches = low_touches if side == "long" else high_touches
        b = armed_touches[-1]
        if b != t - 1:
            continue  # this exact touch pair already armed at an earlier `t` -- do not re-attempt

        floor_or_ceiling = session_low - hold_tol if side == "long" else session_high + hold_tol
        trigger_idx: int | None = None
        for t2 in range(b + 1, min(n, b + bounce_max + 1)):
            window = session_bars[b:t2]
            holds = (
                min(bar.low for bar in window) >= floor_or_ceiling if side == "long"
                else max(bar.high for bar in window) <= floor_or_ceiling
            )
            if not holds:
                break  # dissolved -- no later t2 in this window can hold either
            prev_bar, bar_t2 = session_bars[t2 - 1], session_bars[t2]
            reverses = bar_t2.high > prev_bar.high if side == "long" else bar_t2.low < prev_bar.low
            if reverses:
                trigger_idx = t2
                break
        if trigger_idx is None:
            continue

        # --- armed AND triggered -- build the signal ---------------------------------------------
        prev_bar = session_bars[trigger_idx - 1]
        trigger_bar = session_bars[trigger_idx]
        trigger_price = prev_bar.high if side == "long" else prev_bar.low
        # spec §3.7 Edge cases, "degenerate trigger reference" (the 2026-08-11 clarification): the
        # invalidation clause is arithmetic on `T - SL`, so it presupposes `T > SL` long / `T < SH`
        # short. The trigger scan tolerates the pre-trigger bars dipping to `SL - HOLD_TOL*MBR`, so
        # a reversal bar whose reference `high[t-1]` sits entirely BELOW the arming-time `SL` is
        # reachable -- and there the formula inverts (a long's invalidation lands above its own
        # entry, i.e. born-invalidated). Voided fail-closed; the walk continues to a later arming.
        degenerate = (
            trigger_price <= session_low if side == "long" else trigger_price >= session_high
        )
        if degenerate:
            continue
        if side == "long":
            entry = max(trigger_bar.open, trigger_price)
            entry_kind = "level" if trigger_bar.open < trigger_price else "gap_open"
            gapped_beyond_chase = trigger_bar.open > trigger_price * (1.0 + params["max_chase_frac"])
            invalidation_price = session_low - params["stop_pad_frac"] * (trigger_price - session_low)
        else:
            entry = min(trigger_bar.open, trigger_price)
            entry_kind = "level" if trigger_bar.open > trigger_price else "gap_open"
            gapped_beyond_chase = trigger_bar.open < trigger_price * (1.0 - params["max_chase_frac"])
            invalidation_price = session_high + params["stop_pad_frac"] * (session_high - trigger_price)

        # `crossed_midrange` (disclosure only, spec §3.7's own vague "BOOK midrange rule" --
        # this iteration's own named reading, per the goal's degeneracy-check requirement): did
        # price, ANYWHERE between the zone's first touch and the completing (armed) touch, cross to
        # the OPPOSITE side of the range midpoint -- a swing that visited the middle of the range,
        # not one that stayed compressed near one edge.
        midrange = (session_high + session_low) / 2.0
        between = session_bars[armed_touches[0] : b + 1]
        crossed_midrange = (
            any(bar.high >= midrange for bar in between) if side == "long"
            else any(bar.low <= midrange for bar in between)
        )
        # `absorption_bar_present` (spec §3.7): a zone TOUCH bar with RVOL >= RVOL_ELEVATED and its
        # own range <= RANGE_HOLD_TOL*MBR (P6 passive accumulation/distribution).
        absorption_bar_present = False
        for idx in armed_touches:
            candidate = session_bars[idx]
            rvol = _rvol(candidate, idx, slot_medians)
            if rvol is not None and rvol >= params["rvol_elevated"] and (candidate.high - candidate.low) <= hold_tol:
                absorption_bar_present = True
                break

        approach_start = max(0, trigger_idx - params["approach_bars"])
        approach_indices = list(range(approach_start, trigger_idx))
        approach_rvols = [_rvol(session_bars[i], i, slot_medians) for i in approach_indices]
        known_approach = [r for r in approach_rvols if r is not None]
        approach_rvol_max = max(known_approach) if known_approach else None
        rvol_trigger_bar = _rvol(trigger_bar, trigger_idx, slot_medians)
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
            zone_lo, zone_hi = trigger_price - near_extreme, trigger_price
        else:
            zone_lo, zone_hi = trigger_price, trigger_price + near_extreme
        attempt_count = len(zone_touches(session_bars[:trigger_idx], zone_lo, zone_hi))
        market = _market_block(
            session_bars, trigger_idx, index_bars, session_date, side, mbr, index_baseline, params,
        )
        # Principles (spec §3.7): P6 when the passive-accumulation/distribution absorption bar is
        # present; P5 ("decreasing-volume reversal") "at the high side" -- read literally as the
        # resistance-fade (short) side, the range's own high side.
        principles = (["P6"] if absorption_bar_present else []) + (["P5"] if side == "short" else [])

        return {
            "symbol": symbol,
            "setup_id": "range_trade",
            "side": side,
            "trigger_ts": _iso(trigger_bar.epoch),
            "trigger_price": trigger_price,
            "entry": entry,
            "entry_kind": entry_kind,
            "price_low": session_low,
            "price_high": session_high,
            "invalidation_price": invalidation_price,
            "geometry": {
                "slots_to_break": trigger_idx,
                "range_width_mbr": (session_high - session_low) / mbr,
                "low_zone_touches": len(low_touches),
                "high_zone_touches": len(high_touches),
                "crossed_midrange": crossed_midrange,
                "absorption_bar_present": absorption_bar_present,
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
                "concurrent_signals": [],
                "euphoria_recent": False,
                "capitulation_recent": False,
            },
        }
    return None


def detect_range_trade(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
) -> list[dict]:
    """spec §3.7 -- support-bounce long + resistance-fade short, checked INDEPENDENTLY (cap 1 per
    side per symbol-session, spec's own cap); returns 0, 1, or 2 signals, chronological order not
    guaranteed between sides (mirrors ``detect_jbe``/``detect_dbi`` being two independent calls,
    collapsed into one function here since both sides share ONE ``setup_id``)."""
    signals: list[dict] = []
    long_signal = _range_trade_side(
        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params, "long",
    )
    if long_signal is not None:
        signals.append(long_signal)
    short_signal = _range_trade_side(
        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params, "short",
    )
    if short_signal is not None:
        signals.append(short_signal)
    return signals


# --- J-06: double_top (spec §3.8) / double_bottom (spec §3.9, exact mirror; double_top described) -


def _find_double_extreme(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
    side: str,
) -> dict | None:
    """ONE shared walk for both mirrors: ``side="short"`` (``double_top``, two confirmed swing
    HIGHS, the valley break shorts) and ``side="long"`` (``double_bottom``, two confirmed swing
    LOWS, the peak break longs) -- spec §3.9: "mirror; double_top described". Searches every
    confirmed-pivot pair ``(p1, p2)`` in chronological order (the ``detect_cup_handle`` rim-pair-
    search precedent) and returns the FIRST pair whose full formation validates AND triggers --
    capped at 1 by construction. ``p2`` must be pivot-confirmed STRICTLY BEFORE the trigger bar
    (spec's pivot-confirmation-delay rule): a bar breaking the valley/peak BEFORE
    ``p2["confirmed_at"]`` fails this ENTIRE pair closed (never delays the trigger to search only
    after confirmation, which would silently misrepresent when the break actually happened -- TC-10)."""
    mbr = baseline["mbr"]
    if mbr == 0.0:
        return None
    slot_medians = baseline["slot_volume_medians"]
    pivot_kind = "high" if side == "short" else "low"
    pivots = swing_pivots(session_bars, params["pivot_lookback_bars"])
    candidates = sorted((p for p in pivots if p["kind"] == pivot_kind), key=lambda p: p["index"])
    n = len(session_bars)

    for i, p1 in enumerate(candidates):
        for p2 in candidates[i + 1 :]:
            if p2["index"] - p1["index"] < params["tops_min_separation_bars"]:
                continue
            if abs(p2["price"] - p1["price"]) > params["tops_match_mbr"] * mbr:
                continue

            # Both pivots near the session extreme AT THEIR OWN (already-confirmed) times -- the
            # `detect_cup_handle` "near_extreme_ok" pattern, direction-mirrored.
            p1_session_extreme = (
                max(bar.high for bar in session_bars[: p1["confirmed_at"] + 1]) if side == "short"
                else min(bar.low for bar in session_bars[: p1["confirmed_at"] + 1])
            )
            p2_session_extreme = (
                max(bar.high for bar in session_bars[: p2["confirmed_at"] + 1]) if side == "short"
                else min(bar.low for bar in session_bars[: p2["confirmed_at"] + 1])
            )
            if side == "short":
                if p1["price"] < p1_session_extreme - params["near_extreme_mbr"] * mbr:
                    continue
                if p2["price"] < p2_session_extreme - params["near_extreme_mbr"] * mbr:
                    continue
            else:
                if p1["price"] > p1_session_extreme + params["near_extreme_mbr"] * mbr:
                    continue
                if p2["price"] > p2_session_extreme + params["near_extreme_mbr"] * mbr:
                    continue

            between = session_bars[p1["index"] + 1 : p2["index"]]
            if not between:
                continue
            structure_price = (
                min(bar.low for bar in between) if side == "short"
                else max(bar.high for bar in between)
            )
            # Depth gated against the SHALLOWER of the two pivots (the conservative reading -- the
            # formation must clear the min-depth floor even in the worst case).
            shallower_pivot = min(p1["price"], p2["price"]) if side == "short" else max(p1["price"], p2["price"])
            depth = (shallower_pivot - structure_price) if side == "short" else (structure_price - shallower_pivot)
            if depth < params["min_structure_depth_mbr"] * mbr:
                continue

            # Fail-closed (TC-10): a bar between p2 itself and p2's OWN confirmation already
            # crossing the valley/peak means this pair is invalid -- never delay the trigger scan
            # past confirmation and silently claim a LATER bar as "the" break.
            collapse_window = session_bars[p2["index"] : p2["confirmed_at"] + 1]
            collapsed_before_confirmation = (
                any(bar.low < structure_price for bar in collapse_window) if side == "short"
                else any(bar.high > structure_price for bar in collapse_window)
            )
            if collapsed_before_confirmation:
                continue

            search_start = p2["confirmed_at"] + 1
            trigger_idx: int | None = None
            for t in range(search_start, n):
                crosses = (
                    session_bars[t].low < structure_price if side == "short"
                    else session_bars[t].high > structure_price
                )
                if crosses:
                    trigger_idx = t
                    break
            if trigger_idx is None:
                continue  # never breaks -- formation still open at session close

            # --- armed AND triggered -- build the signal ----------------------------------------
            # S = the FARTHER (worse-case) pivot -- max top for double_top, min bottom for
            # double_bottom -- so invalidation/nominal_risk use the FULL pattern height, "never
            # shrunk" (spec §3.9), never the shallower pivot the depth GATE above used.
            far_pivot = max(p1["price"], p2["price"]) if side == "short" else min(p1["price"], p2["price"])
            trigger_price = structure_price
            trigger_bar = session_bars[trigger_idx]
            if side == "short":
                entry = min(trigger_bar.open, trigger_price)
                entry_kind = "level" if trigger_bar.open > trigger_price else "gap_open"
                gapped_beyond_chase = trigger_bar.open < trigger_price * (1.0 - params["max_chase_frac"])
                invalidation_price = far_pivot + params["stop_pad_frac"] * (far_pivot - trigger_price)
            else:
                entry = max(trigger_bar.open, trigger_price)
                entry_kind = "level" if trigger_bar.open < trigger_price else "gap_open"
                gapped_beyond_chase = trigger_bar.open > trigger_price * (1.0 + params["max_chase_frac"])
                invalidation_price = far_pivot - params["stop_pad_frac"] * (trigger_price - far_pivot)

            p1_window = [idx for idx in (p1["index"] - 1, p1["index"], p1["index"] + 1) if 0 <= idx < n]
            p2_window = [idx for idx in (p2["index"] - 1, p2["index"], p2["index"] + 1) if 0 <= idx < n]
            p1_rvols = [
                r for r in (_rvol(session_bars[idx], idx, slot_medians) for idx in p1_window) if r is not None
            ]
            p2_rvols = [
                r for r in (_rvol(session_bars[idx], idx, slot_medians) for idx in p2_window) if r is not None
            ]
            p1_median_rvol = statistics.median(p1_rvols) if p1_rvols else None
            p2_median_rvol = statistics.median(p2_rvols) if p2_rvols else None
            second_top_rvol_vs_first = (
                p2_median_rvol / p1_median_rvol
                if p1_median_rvol is not None and p2_median_rvol is not None and p1_median_rvol != 0.0
                else None
            )

            approach_start = max(0, trigger_idx - params["approach_bars"])
            approach_indices = list(range(approach_start, trigger_idx))
            approach_rvols = [_rvol(session_bars[i], i, slot_medians) for i in approach_indices]
            known_approach = [r for r in approach_rvols if r is not None]
            approach_rvol_max = max(known_approach) if known_approach else None
            rvol_trigger_bar = _rvol(trigger_bar, trigger_idx, slot_medians)
            spike_verdict = _spike_into_trigger_verdict(
                session_bars, approach_indices, approach_rvols, trigger_price, side, mbr,
                params["rvol_surge"], params["near_extreme_mbr"],
            )
            spiky_approach = False
            if trigger_idx - 1 >= 0:
                spiky_approach = vertical_move(
                    session_bars, trigger_idx - 1, 1, params["vertical_bar_mbr"] * mbr,
                    "down" if side == "short" else "up",
                )
            if side == "short":
                zone_lo, zone_hi = trigger_price, trigger_price + params["near_extreme_mbr"] * mbr
            else:
                zone_lo, zone_hi = trigger_price - params["near_extreme_mbr"] * mbr, trigger_price
            attempt_count = len(zone_touches(session_bars[:trigger_idx], zone_lo, zone_hi))
            market = _market_block(
                session_bars, trigger_idx, index_bars, session_date, side, mbr, index_baseline, params,
            )

            return {
                "symbol": symbol,
                "setup_id": "double_top" if side == "short" else "double_bottom",
                "side": side,
                "trigger_ts": _iso(trigger_bar.epoch),
                "trigger_price": trigger_price,
                "entry": entry,
                "entry_kind": entry_kind,
                "price_low": structure_price if side == "short" else far_pivot,
                "price_high": far_pivot if side == "short" else structure_price,
                "invalidation_price": invalidation_price,
                "geometry": {
                    "slots_to_break": trigger_idx,
                    "tops_gap_mbr": abs(p2["price"] - p1["price"]) / mbr,
                    "tops_separation_bars": p2["index"] - p1["index"],
                    "valley_depth_mbr": depth / mbr,
                    "nominal_risk_mbr": (
                        (far_pivot - trigger_price) / mbr if side == "short"
                        else (trigger_price - far_pivot) / mbr
                    ),
                    "second_top_rvol_vs_first": second_top_rvol_vs_first,
                },
                "volume": {
                    "rvol_trigger_bar": rvol_trigger_bar,
                    "approach_rvol_max": approach_rvol_max,
                    "spike_into_trigger_verdict": spike_verdict,
                    "spiky_approach": spiky_approach,
                },
                "market": market,
                "principles": ["P5"],
                "disclosures": {
                    "gapped_beyond_chase": gapped_beyond_chase,
                    "session_bar_count": len(session_bars),
                    "attempt_count": attempt_count,
                    "bars_to_close": len(session_bars) - 1 - trigger_idx,
                    "concurrent_signals": [],
                    "euphoria_recent": False,
                    "capitulation_recent": False,
                },
            }
    return None


def detect_double_top(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
) -> dict | None:
    """spec §3.8 -- two confirmed swing-high pivots at (roughly) the same level, the valley break
    shorts. Capped at 1 per symbol-session by construction (single return, first validating-and-
    triggering pivot pair)."""
    return _find_double_extreme(
        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params, "short",
    )


def detect_double_bottom(
    session_bars: list[RawBar],
    baseline: dict,
    symbol: str,
    session_date: str,
    index_bars: list[RawBar],
    index_baseline: dict,
    params: dict,
) -> dict | None:
    """spec §3.9 -- the exact mirror of ``detect_double_top``: two confirmed swing-low pivots, the
    peak break longs."""
    return _find_double_extreme(
        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params, "long",
    )
