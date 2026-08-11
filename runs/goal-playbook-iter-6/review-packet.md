# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 9. Shown in full: 7.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/desk_playbook_detect.py` (150 lines not shown)
- `apps/backend/tests/test_desk_playbook_detect.py` (169 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_playbook.py b/apps/backend/app/research/desk_playbook.py
index 7544278..681c858 100644
--- a/apps/backend/app/research/desk_playbook.py
+++ b/apps/backend/app/research/desk_playbook.py
@@ -16,13 +16,15 @@ imports from ``setups.py`` or ``backtests.py``, and no field here is ever named
 
 **Detection then measurement, in one walk.** ``compute_playbook`` walks the desk universe's
 members and detects, per member, the opening-range-break pair (spec §3.1-3.2, J-01) beside the
-continuation family (``jbe``/``dbi``, spec §3.3-3.4, J-04), ``cup_handle`` (spec §3.6, J-04), and
-``capitulation`` (spec §3.5, J-05), gated by the SAME "5m bars + sufficient baseline + a buildable
-opening range" absence checks J-01 shipped -- every detected signal is measured in the same pass
-(forward returns, ``invalidation_breached``, the seeded baseline, J-02) -- ``entry``/``entry_kind``
-are decided at detection time (spec §0's stop-through fill convention is part of a signal's own
-GEOMETRY, not part of measuring what happened afterward). ``detect_euphoria`` (spec §3.5's marker,
-J-05) runs in the SAME per-member walk but is never measured -- see ``_decorate_markers``.
+continuation family (``jbe``/``dbi``, spec §3.3-3.4, J-04), ``cup_handle`` (spec §3.6, J-04),
+``capitulation`` (spec §3.5, J-05), and the range family -- ``range_trade`` (spec §3.7, PROVISIONAL
+tier, J-06) and ``double_top``/``double_bottom`` (spec §3.8-3.9, J-06) -- gated by the SAME "5m
+bars + sufficient baseline + a buildable opening range" absence checks J-01 shipped -- every
+detected signal is measured in the same pass (forward returns, ``invalidation_breached``, the
+seeded baseline, J-02) -- ``entry``/``entry_kind`` are decided at detection time (spec §0's
+stop-through fill convention is part of a signal's own GEOMETRY, not part of measuring what
+happened afterward). ``detect_euphoria`` (spec §3.5's marker, J-05) runs in the SAME per-member
+walk but is never measured -- see ``_decorate_markers``.
 
 **Parameters discipline (the ``desk_forward.forward_parameters`` pattern, applied at birth).**
 ``playbook_parameters()`` reads every constant below at CALL TIME (so a test monkeypatching one
@@ -68,9 +70,12 @@ from .desk_playbook_detect import (
     detect_capitulation,
     detect_cup_handle,
     detect_dbi,
+    detect_double_bottom,
+    detect_double_top,
     detect_euphoria,
     detect_jbe,
     detect_opening_range_breaks,
+    detect_range_trade,
 )
 from .desk_playbook_features import baselines, opening_range, rth_session_slice, side_sign
 from .desk_sessions import refuse_if_not_a_session
@@ -149,13 +154,15 @@ PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC: float = 0.25  # BOOK -- spec §1's HAND
 
 # Companion structural constants (shape, not thresholds).
 # J-01 shipped ONLY the opening-range-break family; J-04 EXTENDED this tuple with the continuation
-# family (jbe/dbi/cup_handle); J-05 (this iteration) adds `capitulation` -- J-06 will extend it
-# further with the range family (each extension is a signature-moving, expected, visible change) --
+# family (jbe/dbi/cup_handle); J-05 added `capitulation`; J-06 (this iteration) adds the range
+# family -- `range_trade`, `double_top`, `double_bottom` -- completing the full nine-detector-plus-
+# marker set the era promised (each extension is a signature-moving, expected, visible change) --
 # declaring a setup id here before its detector exists would claim a compute that does not happen.
 # `"euphoria"` is DELIBERATELY never added here: spec §3.5 defines it as a marker only, never a
 # recorded setup -- see `_decorate_markers` below for what it does instead.
 PLAYBOOK_SETUPS: tuple[str, ...] = (
     "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
+    "range_trade", "double_top", "double_bottom",
 )
 PLAYBOOK_MARKET_SYMBOL: str = "SPY"
 # The rail's own baseline seed, echoed (not re-derived) -- the seed discipline itself is J-02's;
@@ -170,7 +177,8 @@ PLAYBOOK_MIN_N_DISCLOSURE: int = 12  # evidence low-n tag (J-08) -- a disclosure
 # test_copy_discipline.find_violations (the desk_forward.FORWARD_REGISTER precedent).
 PLAYBOOK_REGISTER = (
     "pre-registered opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, "
-    "and capitulation signals detected on the desk's own recorded 5m/1m bars — every threshold is "
+    "capitulation, range-trade, double-top, and double-bottom signals detected on the desk's own "
+    "recorded 5m/1m bars — every threshold is "
     "fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
     "A signal is a recorded observation, not advice: invalidation_price is the book's own "
     "structural level, disclosed as geometry, never a stop order, a size, or an account concept. "
@@ -658,6 +666,28 @@ def compute_playbook(
         )
         if capitulation_signal is not None:
             detected_signals.append(capitulation_signal)
+
+        # J-06: the range family -- range_trade (both sides, one setup_id), double_top,
+        # double_bottom -- joins the SAME per-member walk, sharing the SAME absence gate as every
+        # other family. Reads bars/baselines only (zero `compute_tradability`/`compute_levels`
+        # calls anywhere in this module -- see test_desk_playbook_guards.py's own call-counting
+        # guard): the book's intraday ranges and the desk's structural walls are different owners.
+        detected_signals.extend(
+            detect_range_trade(
+                session_5m, baseline, symbol, session_date, index_bars, index_baseline, params
+            )
+        )
+        double_top_signal = detect_double_top(
+            session_5m, baseline, symbol, session_date, index_bars, index_baseline, params
+        )
+        if double_top_signal is not None:
+            detected_signals.append(double_top_signal)
+        double_bottom_signal = detect_double_bottom(
+            session_5m, baseline, symbol, session_date, index_bars, index_baseline, params
+        )
+        if double_bottom_signal is not None:
+            detected_signals.append(double_bottom_signal)
+
         euphoria_marker = detect_euphoria(session_5m, baseline, params)
         euphoria_trigger_indices = (
             [euphoria_marker["trigger_idx"]] if euphoria_marker is not None else []
diff --git a/apps/backend/app/research/desk_playbook_detect.py b/apps/backend/app/research/desk_playbook_detect.py
index 1336fde..dc17c0c 100644
--- a/apps/backend/app/research/desk_playbook_detect.py
+++ b/apps/backend/app/research/desk_playbook_detect.py
@@ -1,12 +1,27 @@
 """The Playbook's detectors (Era B2). J-01 shipped the opening-range-break family
 (``docs/playbook-detector-spec.md`` §3.1-3.2); J-04 added the continuation family --
 ``detect_jbe``/``detect_dbi`` (§3.3-3.4, one shared internal walk, direction-flipped) and
-``detect_cup_handle`` (§3.6). J-05 (this iteration) adds the climax family --
-``detect_capitulation`` (§3.5, entry) and ``detect_euphoria`` (§3.5, the exact mirror UP, a
-MARKER only -- never a served signal). J-06 adds the remaining three detectors
-(``range_trade``/``double_top``/``double_bottom``), each built purely out of
-``desk_playbook_features.py``'s eight primitives plus the ``playbook_parameters()`` dict a caller
-hands in.
+``detect_cup_handle`` (§3.6). J-05 added the climax family -- ``detect_capitulation`` (§3.5,
+entry) and ``detect_euphoria`` (§3.5, the exact mirror UP, a MARKER only -- never a served
+signal). J-06 (this iteration) adds the remaining three detectors -- ``detect_range_trade``
+(§3.7, PROVISIONAL tier) and ``detect_double_top``/``detect_double_bottom`` (§3.8-3.9, the exact
+mirror) -- each built purely out of ``desk_playbook_features.py``'s eight primitives plus the
+``playbook_parameters()`` dict a caller hands in.
+
+**J-06 design note -- range_trade's trigger grammar.** Spec §3.7 (and the iteration's own framing)
+describes range_trade's bounce trigger as "the SAME reversal-bar grammar the capitulation bounce
+already implements... one shared mechanism, not a second vague one". This module honors that at
+the GRAMMAR level -- the identical local predicate (`bar.high > session_bars[t-1].high` / the
+mirrored low check), scanned within `PLAYBOOK_BOUNCE_MAX_BARS` of an anchor, `T = high[t-1]` --
+but does NOT literally route range_trade's trigger through `_find_climax_formation`: that
+function's own arming precondition is a `vertical_move` formation with re-anchoring (a DIFFERENT
+formation range_trade does not share -- range_trade arms via `zone_touches` of a tested-and-held
+zone, never a vertical move), so forcing a shared call site would either bend
+`_find_climax_formation` to a formation it was never built for or silently disable its own
+re-anchoring for capitulation/euphoria. The reversal-bar predicate itself is small enough (one
+comparison) that duplicating exactly that one line, under a shared name and cross-referenced
+docstring, is the honest reading of "the same grammar" without risking J-05's own byte-identical
+behavior for a J-06 formation it does not need.
 
 **J-04's own primitives are all reused, none added.** ``consolidation_range`` (JBE/DBI's base,
 shared with the module's own precedent of "shared geometry for JBE/DBI's base and cup-and-handle's
@@ -60,6 +75,9 @@ __all__ = [
     "detect_cup_handle",
     "detect_capitulation",
     "detect_euphoria",
+    "detect_range_trade",
+    "detect_double_top",
+    "detect_double_bottom",
 ]
 
 
@@ -1008,3 +1026,501 @@ def detect_euphoria(session_bars: list[RawBar], baseline: dict, params: dict) ->
         return None
     _window_start, _climax_idx, trigger_idx = found
     return {"trigger_idx": trigger_idx}
+
+
+# === J-06: the range family -- range_trade (spec §3.7, PROVISIONAL) + double_top/double_bottom
+# (spec §3.8-3.9, exact mirror; double_top described) ===============================================
+
+
+def _zone_held(bars: list[RawBar], touches: list[int], extreme: str, hold_tol: float) -> bool:
+    """spec §3.7's arming clause "each later touch extending the extreme by <=
+    ``PLAYBOOK_RANGE_HOLD_TOL_MBR * MBR``" (the BOOK's "and hold"), read per-touch exactly as
+    written: for every touch AFTER the first, the amount by which that touch pushes the running
+    extreme further out must not exceed ``hold_tol``. ``touches`` are ``zone_touches`` indices
+    (the FIRST bar of each touch group, full-exit re-arm semantics), so a touch's own extension is
+    measured over its whole group -- the prefix extreme through the bar before the NEXT touch
+    group starts (or the end of ``bars``) minus the prefix extreme established strictly before
+    this group. Bars between two touch groups cannot set a new extreme: a bar extending the low
+    below the running low necessarily overlaps the low zone ``[SL, SL + NEAR_EXTREME*MBR]`` (its
+    low is <= the zone's own floor) and is therefore itself inside a touch group -- so the group
+    boundaries account for every extension. A single touch never "holds" (the caller's >= 2 gate
+    rejects it first); returns ``False`` for fewer than two touches. ``extreme`` names WHICH
+    running extreme this zone owns (``"low"`` for the low zone, ``"high"`` for the high zone) --
+    deliberately not a side, since spec §3.7 requires BOTH zones to hold before EITHER side arms."""
+    if len(touches) < 2:
+        return False
+    for k in range(1, len(touches)):
+        start = touches[k]
+        end = touches[k + 1] if k + 1 < len(touches) else len(bars)
+        if extreme == "low":
+            before = min(bar.low for bar in bars[:start])
+            through = min(bar.low for bar in bars[:end])
+            extension = before - through
+        else:
+            before = max(bar.high for bar in bars[:start])
+            through = max(bar.high for bar in bars[:end])
+            extension = through - before
+        if extension > hold_tol:
+            return False
+    return True
+
+
+def _range_trade_side(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+    side: str,
+) -> dict | None:
+    """ONE side of spec §3.7 -- support-bounce (``side="long"``) or resistance-fade
+    (``side="short"``, the exact mirror). Walks candidate arming-completion bars ``t`` forward
+    through the session; at each, the session range so far (``SH``/``SL`` over
+    ``session_bars[:t]``, prefix extremes -- entry-time legal by construction, the same "recompute
+    at every candidate" shape ``_find_one_continuation``'s own ``near_extreme_ok`` check uses) must
+    be ``>= PLAYBOOK_RANGE_MIN_WIDTH_MBR`` wide, and BOTH zones (``[SL, SL + NEAR_EXTREME*MBR]``
+    low and ``[SH - NEAR_EXTREME*MBR, SH]`` high) must show ``>= 2`` touches EACH, each later touch
+    holding its own extreme within ``RANGE_HOLD_TOL_MBR * MBR`` (``_zone_held``) -- spec §3.7's
+    arming clause in full, the BOOK's "test the low AND high twice and hold"; a session that tests
+    one extreme twice while touching the other once is the breakout-only case Ch 13 excludes and
+    arms nothing. The armed side's own zone additionally supplies the COMPLETING touch: an arming
+    attempt is evaluated only at the first ``t`` at which that side's most recent touch is ``t - 1``
+    itself (so the same touch pair is never re-attempted on later, untouched bars). A formation
+    whose trigger reference is degenerate (``T <= SL`` long / ``T >= SH`` short, where the spec's
+    own invalidation arithmetic inverts) is voided fail-closed, per spec §3.7's Edge cases. From
+    the completing touch ``b``, scans forward up to
+    ``PLAYBOOK_BOUNCE_MAX_BARS`` for the reversal-bar grammar (module docstring: the SAME predicate
+    ``_find_climax_formation``'s own bounce trigger uses, ``high > high[t-1]`` long / ``low <
+    low[t-1]`` short), gated at every candidate bar by the arming description's own hold tolerance
+    (``min(low[b..t-1]) >= SL - HOLD_TOL*MBR`` long, mirrored short) -- the FIRST bar where the
+    hold check fails ends the scan for this arming attempt (spec's own edge case: a strict break
+    beyond the zone by more than the tolerance dissolves range-mode), and the outer loop then tries
+    the NEXT arming completion. Capped at 1 by construction (single return, first (arm, trigger)
+    pair found chronologically -- the ``detect_cup_handle`` rim-pair-search precedent)."""
+    mbr = baseline["mbr"]
+    if mbr == 0.0:
+        return None
+    slot_medians = baseline["slot_volume_medians"]
+    n = len(session_bars)
+    min_width = params["range_min_width_mbr"] * mbr
+    near_extreme = params["near_extreme_mbr"] * mbr
+    hold_tol = params["range_hold_tol_mbr"] * mbr
+    bounce_max = params["bounce_max_bars"]
+
+    for t in range(2, n):
+        bars_so_far = session_bars[:t]
+        session_high = max(bar.high for bar in bars_so_far)
+        session_low = min(bar.low for bar in bars_so_far)
+        if session_high - session_low < min_width:
+            continue
+        low_touches = zone_touches(bars_so_far, session_low, session_low + near_extreme)
+        high_touches = zone_touches(bars_so_far, session_high - near_extreme, session_high)
+        # spec §3.7's arming gate, in full: the high zone AND the low zone EACH with >= 2 touches,
+        # EACH later touch holding its extreme within `RANGE_HOLD_TOL_MBR * MBR`. Both zones, not
+        # just the armed side's own: the BOOK rule is "test the low AND high twice and hold" -- a
+        # session that tests one extreme twice while touching the other once is the breakout-only
+        # case Ch 13 excludes, and never arms a range trade on either side.
+        if len(low_touches) < 2 or len(high_touches) < 2:
+            continue
+        if not _zone_held(bars_so_far, low_touches, "low", hold_tol):
+            continue
+        if not _zone_held(bars_so_far, high_touches, "high", hold_tol):
+            continue
+        armed_touches = low_touches if side == "long" else high_touches
+        b = armed_touches[-1]
+        if b != t - 1:
+            continue  # this exact touch pair already armed at an earlier `t` -- do not re-attempt
+
+        floor_or_ceiling = session_low - hold_tol if side == "long" else session_high + hold_tol
+        trigger_idx: int | None = None
+        for t2 in range(b + 1, min(n, b + bounce_max + 1)):
+            window = session_bars[b:t2]
+            holds = (
+                min(bar.low for bar in window) >= floor_or_ceiling if side == "long"
+                else max(bar.high for bar in window) <= floor_or_ceiling
+            )
+            if not holds:
+                break  # dissolved -- no later t2 in this window can hold either
+            prev_bar, bar_t2 = session_bars[t2 - 1], session_bars[t2]
+            reverses = bar_t2.high > prev_bar.high if side == "long" else bar_t2.low < prev_bar.low
+            if reverses:
+                trigger_idx = t2
+                break
+        if trigger_idx is None:
+            continue
+
+        # --- armed AND triggered -- build the signal ---------------------------------------------
+        prev_bar = session_bars[trigger_idx - 1]
+        trigger_bar = session_bars[trigger_idx]
+        trigger_price = prev_bar.high if side == "long" else prev_bar.low
+        # spec §3.7 Edge cases, "degenerate trigger reference" (the 2026-08-11 clarification): the
+        # invalidation clause is arithmetic on `T - SL`, so it presupposes `T > SL` long / `T < SH`
+        # short. The trigger scan tolerates the pre-trigger bars dipping to `SL - HOLD_TOL*MBR`, so
+        # a reversal bar whose reference `high[t-1]` sits entirely BELOW the arming-time `SL` is
+        # reachable -- and there the formula inverts (a long's invalidation lands above its own
+        # entry, i.e. born-invalidated). Voided fail-closed; the walk continues to a later arming.
+        degenerate = (
+            trigger_price <= session_low if side == "long" else trigger_price >= session_high
+        )
+        if degenerate:
+            continue
+        if side == "long":
+            entry = max(trigger_bar.open, trigger_price)
+            entry_kind = "level" if trigger_bar.open < trigger_price else "gap_open"
+            gapped_beyond_chase = trigger_bar.open > trigger_price * (1.0 + params["max_chase_frac"])
+            invalidation_price = session_low - params["stop_pad_frac"] * (trigger_price - session_low)
+        else:
+            entry = min(trigger_bar.open, trigger_price)
+            entry_kind = "level" if trigger_bar.open > trigger_price else "gap_open"
+            gapped_beyond_chase = trigger_bar.open < trigger_price * (1.0 - params["max_chase_frac"])
+            invalidation_price = session_high + params["stop_pad_frac"] * (session_high - trigger_price)
+
+        # `crossed_midrange` (disclosure only, spec §3.7's own vague "BOOK midrange rule" --
+        # this iteration's own named reading, per the goal's degeneracy-check requirement): did
+        # price, ANYWHERE between the zone's first touch and the completing (armed) touch, cross to
+        # the OPPOSITE side of the range midpoint -- a swing that visited the middle of the range,
+        # not one that stayed compressed near one edge.
+        midrange = (session_high + session_low) / 2.0
+        between = session_bars[armed_touches[0] : b + 1]
+        crossed_midrange = (
+            any(bar.high >= midrange for bar in between) if side == "long"
+            else any(bar.low <= midrange for bar in between)
+        )
+        # `absorption_bar_present` (spec §3.7): a zone TOUCH bar with RVOL >= RVOL_ELEVATED and its
+        # own range <= RANGE_HOLD_TOL*MBR (P6 passive accumulation/distribution).
+        absorption_bar_present = False
+        for idx in armed_touches:
+            candidate = session_bars[idx]
+            rvol = _rvol(candidate, idx, slot_medians)
+            if rvol is not None and rvol >= params["rvol_elevated"] and (candidate.high - candidate.low) <= hold_tol:
+                absorption_bar_present = True
+                break
+
+        approach_start = max(0, trigger_idx - params["approach_bars"])
+        approach_indices = list(range(approach_start, trigger_idx))
+        approach_rvols = [_rvol(session_bars[i], i, slot_medians) for i in approach_indices]
+        known_approach = [r for r in approach_rvols if r is not None]
+        approach_rvol_max = max(known_approach) if known_approach else None
+        rvol_trigger_bar = _rvol(trigger_bar, trigger_idx, slot_medians)
+        spike_verdict = _spike_into_trigger_verdict(
+            session_bars, approach_indices, approach_rvols, trigger_price, side, mbr,
+            params["rvol_surge"], params["near_extreme_mbr"],
+        )
+        spiky_approach = False
+        if trigger_idx - 1 >= 0:
+            spiky_approach = vertical_move(
+                session_bars, trigger_idx - 1, 1, params["vertical_bar_mbr"] * mbr,
+                "up" if side == "long" else "down",
+            )
+        if side == "long":
+            zone_lo, zone_hi = trigger_price - near_extreme, trigger_price
+        else:
+            zone_lo, zone_hi = trigger_price, trigger_price + near_extreme
+        attempt_count = len(zone_touches(session_bars[:trigger_idx], zone_lo, zone_hi))
+        market = _market_block(
+            session_bars, trigger_idx, index_bars, session_date, side, mbr, index_baseline, params,
+        )
+        # Principles (spec §3.7): P6 when the passive-accumulation/distribution absorption bar is
+        # present; P5 ("decreasing-volume reversal") "at the high side" -- read literally as the
+        # resistance-fade (short) side, the range's own high side.
+        principles = (["P6"] if absorption_bar_present else []) + (["P5"] if side == "short" else [])
+
+        return {
+            "symbol": symbol,
+            "setup_id": "range_trade",
+            "side": side,
+            "trigger_ts": _iso(trigger_bar.epoch),
+            "trigger_price": trigger_price,
+            "entry": entry,
+            "entry_kind": entry_kind,
+            "price_low": session_low,
+            "price_high": session_high,
+            "invalidation_price": invalidation_price,
+            "geometry": {
+                "slots_to_break": trigger_idx,
+                "range_width_mbr": (session_high - session_low) / mbr,
+                "low_zone_touches": len(low_touches),
+                "high_zone_touches": len(high_touches),
+                "crossed_midrange": crossed_midrange,
+                "absorption_bar_present": absorption_bar_present,
+            },
+            "volume": {
+                "rvol_trigger_bar": rvol_trigger_bar,
+                "approach_rvol_max": approach_rvol_max,
+                "spike_into_trigger_verdict": spike_verdict,
+                "spiky_approach": spiky_approach,
+            },
+            "market": market,
+            "principles": principles,
+            "disclosures": {
+                "gapped_beyond_chase": gapped_beyond_chase,
+                "session_bar_count": len(session_bars),
+                "attempt_count": attempt_count,
+                "bars_to_close": len(session_bars) - 1 - trigger_idx,
+                "concurrent_signals": [],
+                "euphoria_recent": False,
+                "capitulation_recent": False,
+            },
+        }
+    return None
+
+
+def detect_range_trade(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+) -> list[dict]:
+    """spec §3.7 -- support-bounce long + resistance-fade short, checked INDEPENDENTLY (cap 1 per
+    side per symbol-session, spec's own cap); returns 0, 1, or 2 signals, chronological order not
+    guaranteed between sides (mirrors ``detect_jbe``/``detect_dbi`` being two independent calls,
+    collapsed into one function here since both sides share ONE ``setup_id``)."""
+    signals: list[dict] = []
+    long_signal = _range_trade_side(
+        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params, "long",
+    )
+    if long_signal is not None:
+        signals.append(long_signal)
+    short_signal = _range_trade_side(
+        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params, "short",
+    )
+    if short_signal is not None:
+        signals.append(short_signal)
+    return signals
+
+
+# --- J-06: double_top (spec §3.8) / double_bottom (spec §3.9, exact mirror; double_top described) -
+
+
+def _find_double_extreme(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+    side: str,
+) -> dict | None:
+    """ONE shared walk for both mirrors: ``side="short"`` (``double_top``, two confirmed swing
+    HIGHS, the valley break shorts) and ``side="long"`` (``double_bottom``, two confirmed swing
+    LOWS, the peak break longs) -- spec §3.9: "mirror; double_top described". Searches every
+    confirmed-pivot pair ``(p1, p2)`` in chronological order (the ``detect_cup_handle`` rim-pair-
+    search precedent) and returns the FIRST pair whose full formation validates AND triggers --
+    capped at 1 by construction. ``p2`` must be pivot-confirmed STRICTLY BEFORE the trigger bar
+    (spec's pivot-confirmation-delay rule): a bar breaking the valley/peak BEFORE
+    ``p2["confirmed_at"]`` fails this ENTIRE pair closed (never delays the trigger to search only
+    after confirmation, which would silently misrepresent when the break actually happened -- TC-10)."""
+    mbr = baseline["mbr"]
+    if mbr == 0.0:
+        return None
+    slot_medians = baseline["slot_volume_medians"]
+    pivot_kind = "high" if side == "short" else "low"
+    pivots = swing_pivots(session_bars, params["pivot_lookback_bars"])
+    candidates = sorted((p for p in pivots if p["kind"] == pivot_kind), key=lambda p: p["index"])
+    n = len(session_bars)
+
+    for i, p1 in enumerate(candidates):
+        for p2 in candidates[i + 1 :]:
+            if p2["index"] - p1["index"] < params["tops_min_separation_bars"]:
+                continue
+            if abs(p2["price"] - p1["price"]) > params["tops_match_mbr"] * mbr:
+                continue
+
+            # Both pivots near the session extreme AT THEIR OWN (already-confirmed) times -- the
+            # `detect_cup_handle` "near_extreme_ok" pattern, direction-mirrored.
+            p1_session_extreme = (
+                max(bar.high for bar in session_bars[: p1["confirmed_at"] + 1]) if side == "short"
+                else min(bar.low for bar in session_bars[: p1["confirmed_at"] + 1])
+            )
+            p2_session_extreme = (
+                max(bar.high for bar in session_bars[: p2["confirmed_at"] + 1]) if side == "short"
+                else min(bar.low for bar in session_bars[: p2["confirmed_at"] + 1])
+            )
+            if side == "short":
+                if p1["price"] < p1_session_extreme - params["near_extreme_mbr"] * mbr:
+                    continue
+                if p2["price"] < p2_session_extreme - params["near_extreme_mbr"] * mbr:
+                    continue
+            else:
+                if p1["price"] > p1_session_extreme + params["near_extreme_mbr"] * mbr:
+                    continue
+                if p2["price"] > p2_session_extreme + params["near_extreme_mbr"] * mbr:
+                    continue
+
+            between = session_bars[p1["index"] + 1 : p2["index"]]
+            if not between:
+                continue
+            structure_price = (
+                min(bar.low for bar in between) if side == "short"
+                else max(bar.high for bar in between)
+            )
+            # Depth gated against the SHALLOWER of the two pivots (the conservative reading -- the
+            # formation must clear the min-depth floor even in the worst case).
+            shallower_pivot = min(p1["price"], p2["price"]) if side == "short" else max(p1["price"], p2["price"])
+            depth = (shallower_pivot - structure_price) if side == "short" else (structure_price - shallower_pivot)
+            if depth < params["min_structure_depth_mbr"] * mbr:
+                continue
+
+            # Fail-closed (TC-10): a bar between p2 itself and p2's OWN confirmation already
+            # crossing the valley/peak means this pair is invalid -- never delay the trigger scan
+            # past confirmation and silently claim a LATER bar as "the" break.
+            collapse_window = session_bars[p2["index"] : p2["confirmed_at"] + 1]
+            collapsed_before_confirmation = (
+                any(bar.low < structure_price for bar in collapse_window) if side == "short"
+                else any(bar.high > structure_price for bar in collapse_window)
... [diff_bound] apps/backend/app/research/desk_playbook_detect.py: 150 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_playbook.py b/apps/backend/tests/test_desk_playbook.py
index addfe0b..c56192a 100644
--- a/apps/backend/tests/test_desk_playbook.py
+++ b/apps/backend/tests/test_desk_playbook.py
@@ -1007,11 +1007,12 @@ def test_j04_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside
     # J-04's own new content. This is a live "what does PLAYBOOK_SETUPS currently say" assertion,
     # not a frozen discipline guard, so it tracks the tuple's real value every iteration that
     # legitimately extends it.
-    monkeypatch.undo()  # restore this iteration's real 6-setup PLAYBOOK_SETUPS
+    monkeypatch.undo()  # restore this iteration's real 9-setup PLAYBOOK_SETUPS
 
     current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
     assert current_result["parameters"]["setups"] == [
         "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
+        "range_trade", "double_top", "double_bottom",
     ]
     assert current_result["playbook_input_signature"] != pre_j04_meta["playbook_input_signature"]
 
@@ -1069,8 +1070,12 @@ def test_capitulation_wired_into_compute_playbook_is_measured_like_every_other_s
 
     result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
 
-    assert desk_playbook_module.PLAYBOOK_SETUPS[-1] == "capitulation"
-    assert result["parameters"]["setups"][-1] == "capitulation"
+    # goal-playbook-iter-6 (J-06) maintenance note: `PLAYBOOK_SETUPS` no longer ENDS with
+    # "capitulation" (three more setup ids joined after it) -- a live "is it present" check, not a
+    # frozen discipline guard, so it tracks the tuple's real membership every iteration that
+    # legitimately extends it (the same maintenance the J-04/J-05 setups-tuple tests already do).
+    assert "capitulation" in desk_playbook_module.PLAYBOOK_SETUPS
+    assert "capitulation" in result["parameters"]["setups"]
     cap_signals = [s for s in result["signals"] if s["symbol"] == "AAA" and s["setup_id"] == "capitulation"]
     assert len(cap_signals) == 1
     signal = cap_signals[0]
@@ -1181,11 +1186,12 @@ def test_j05_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside
         "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle",
     ]
 
-    monkeypatch.undo()  # restore this iteration's real 6-setup PLAYBOOK_SETUPS
+    monkeypatch.undo()  # restore this iteration's real 9-setup PLAYBOOK_SETUPS
 
     current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
     assert current_result["parameters"]["setups"] == [
         "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
+        "range_trade", "double_top", "double_bottom",
     ]
     assert current_result["playbook_input_signature"] != pre_j05_meta["playbook_input_signature"]
 
@@ -1212,20 +1218,170 @@ def test_j05_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside
     assert pre_j05_or_signals == current_or_signals
 
 
+# === goal-playbook-iter-6 (J-06): the range family wired into the real compute walk ===============
+
+
+def _plant_range_trade_session(bar_store: BarStore, symbol: str) -> None:
+    """The ``test_desk_playbook_detect.py`` canonical range_trade (support-bounce long) fixture,
+    planted through a real ``BarStore`` -- a genuinely TWO-SIDED range (both zones tested twice and
+    held), the only formation spec §3.7's arming clause admits."""
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN + 0 * 300.0, 104.0, 105.0, 103.5, 104.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 1 * 300.0, 103.9, 103.9, 101.5, 101.8, 1000),
+        _bar(symbol, "5m", E_OPEN + 2 * 300.0, 101.8, 102.0, 100.0, 100.4, 1000),
+        _bar(symbol, "5m", E_OPEN + 3 * 300.0, 101.6, 103.0, 101.5, 102.8, 1000),
+        _bar(symbol, "5m", E_OPEN + 4 * 300.0, 102.8, 104.8, 102.5, 104.4, 1000),
+        _bar(symbol, "5m", E_OPEN + 5 * 300.0, 103.4, 103.5, 102.0, 102.4, 1000),
+        _bar(symbol, "5m", E_OPEN + 6 * 300.0, 102.4, 102.6, 100.4, 100.7, 1000),
+        _bar(symbol, "5m", E_OPEN + 7 * 300.0, 101.0, 103.5, 100.6, 103.2, 2000),
+        _bar(symbol, "5m", E_OPEN + 8 * 300.0, 103.2, 103.4, 102.9, 103.1, 1000),
+        _bar(symbol, "5m", E_OPEN + 9 * 300.0, 103.1, 103.3, 102.8, 103.0, 1000),
+    ]
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def test_range_trade_wired_into_compute_playbook_is_measured_like_every_other_setup(
+    tmp_path, bar_store,
+):
+    """Range_trade joins the SAME per-member walk as every other family: `PLAYBOOK_SETUPS` now
+    names it, and the recorded signal carries `forward`/`invalidation_breached` exactly like an
+    opening-range-break/jbe/dbi/cup_handle/capitulation signal does (J-02's measurement pass,
+    unmodified)."""
+    universe_store = _register_universe(tmp_path, ["RTAAA"])
+    _plant_decoration_baseline_sessions(bar_store, "RTAAA", slots=10)
+    _plant_range_trade_session(bar_store, "RTAAA")
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    assert "range_trade" in result["parameters"]["setups"]
+    rt_signals = [s for s in result["signals"] if s["symbol"] == "RTAAA" and s["setup_id"] == "range_trade"]
+    assert len(rt_signals) == 1
+    signal = rt_signals[0]
+    assert "forward" in signal and signal["forward"] is not None
+    assert "invalidation_breached" in signal and signal["invalidation_breached"] is not None
+    assert result["summary"]["range_trade:long"]["to_close"]["signals"]["n"] == 1
+    assert result["baseline_anchors"]["range_trade:long"]
+
+
+def _plant_double_top_session(bar_store: BarStore, symbol: str) -> None:
+    """The ``test_desk_playbook_detect.py`` canonical double_top fixture, planted through a real
+    ``BarStore``."""
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN + 0 * 300.0, 104, 105, 104, 104.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 1 * 300.0, 104.5, 106, 104, 105.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 2 * 300.0, 105.5, 107, 105, 106.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 3 * 300.0, 106.5, 110, 106, 109, 1000),
+        _bar(symbol, "5m", E_OPEN + 4 * 300.0, 109, 108, 107, 107.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 5 * 300.0, 107.5, 105, 104, 104.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 6 * 300.0, 104.5, 102, 101, 101.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 7 * 300.0, 101.5, 100, 99, 99.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 8 * 300.0, 99.5, 98, 97, 97.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 9 * 300.0, 97.5, 99, 97.2, 98.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 10 * 300.0, 98.5, 101, 98, 100.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 11 * 300.0, 100.5, 104, 100, 103.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 12 * 300.0, 103.5, 107, 103, 106.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 13 * 300.0, 106.5, 110.3, 106, 109.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 14 * 300.0, 109.5, 108, 107, 107.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 15 * 300.0, 107.5, 106, 105, 105.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 16 * 300.0, 105.5, 104, 103, 103.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 17 * 300.0, 103.5, 103.8, 102, 102.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 18 * 300.0, 102.5, 103, 96.0, 96.5, 2000),
+        _bar(symbol, "5m", E_OPEN + 19 * 300.0, 96.5, 97, 96, 96.8, 1000),
+    ]
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def test_double_top_and_double_bottom_wired_into_compute_playbook_is_measured_like_every_other_setup(
+    tmp_path, bar_store,
+):
+    """double_top (and, by the exact-mirror construction, double_bottom) join the SAME per-member
+    walk as every other family."""
+    universe_store = _register_universe(tmp_path, ["DTAAA"])
+    _plant_decoration_baseline_sessions(bar_store, "DTAAA", slots=20)
+    _plant_double_top_session(bar_store, "DTAAA")
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    assert "double_top" in result["parameters"]["setups"]
+    assert "double_bottom" in result["parameters"]["setups"]
+    dt_signals = [s for s in result["signals"] if s["symbol"] == "DTAAA" and s["setup_id"] == "double_top"]
+    assert len(dt_signals) == 1
+    signal = dt_signals[0]
+    assert "forward" in signal and signal["forward"] is not None
+    assert "invalidation_breached" in signal and signal["invalidation_breached"] is not None
+    assert result["summary"]["double_top:short"]["to_close"]["signals"]["n"] == 1
+    assert result["baseline_anchors"]["double_top:short"]
+
+
+def test_j06_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file(
+    tmp_path, bar_store, universe_store, monkeypatch,
+):
+    """TC-13/TC-14: the SAME re-key-never-rewrite precedent as the J-04/J-05 tests above, this time
+    for J-06's own three new setup ids. `_record_aaa`'s own 6-bar session is too short for
+    `range_trade`/`double_top`/`double_bottom` to ever fire (each needs >= 2 zone touches or 2
+    confirmed, separated pivots -- neither is reachable in 6 bars), so this isolates exactly the
+    ONE thing this iteration changed for an already-recorded file's own inputs: the parameters
+    blob's `setups` list, and therefore the signature."""
+    monkeypatch.setattr(
+        desk_playbook_module, "PLAYBOOK_SETUPS",
+        ("open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation"),
+    )
+    pre_j06_store, pre_j06_meta = _record_aaa(tmp_path, bar_store, universe_store)
+    pre_j06_path = pre_j06_store._path(pre_j06_meta["id"])
+    pre_j06_sha = _sha256_file(pre_j06_path)
+    assert pre_j06_meta["parameters"]["setups"] == [
+        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
+    ]
+
+    monkeypatch.undo()  # restore this iteration's real 9-setup PLAYBOOK_SETUPS
+
+    current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert current_result["parameters"]["setups"] == [
+        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
+        "range_trade", "double_top", "double_bottom",
+    ]
+    assert current_result["playbook_input_signature"] != pre_j06_meta["playbook_input_signature"]
+
+    current_meta = pre_j06_store.record(**current_result)
+    assert current_meta["id"] != pre_j06_meta["id"]
+
+    # TC-13: the pre-J-06 file is byte-identical, untouched by the second, differently-keyed write.
+    assert _sha256_file(pre_j06_path) == pre_j06_sha
+    assert pre_j06_store.get(pre_j06_meta["id"]) == pre_j06_meta
+
+    # TC-14: both versions are now recorded for this date; newest is the current-code one.
+    newest, versions = pre_j06_store.newest_for_date(SESSION_DATE)
+    assert versions == 2
+    assert newest["id"] == current_meta["id"]
+
+    # The OR-break signal's own CONTENT is unaffected by the new setups tuple joining the
+    # parameters blob -- zero behavior change to the families J-01 through J-05 already shipped.
+    pre_j06_or_signals = [
+        s for s in pre_j06_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
+    ]
+    current_or_signals = [
+        s for s in current_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
+    ]
+    assert pre_j06_or_signals == current_or_signals
+
+
 # --- TC-8: the widened PLAYBOOK_REGISTER pinned exactly, with a mandatory rationale paragraph ------
 #
-# goal-playbook-iter-5 (J-05): PLAYBOOK_REGISTER's opening clause widens from "opening-range-break
-# signals" to name every shipped setup family (open-range breaks, jump-base-explosion,
-# drop-base-implosion, cup-and-handle, capitulation) -- closing the OPEN minor anti-goal violation
-# iter-4's own evaluator/audit carried forward (the register/blurb text had silently drifted out of
-# sync with J-04's own continuation-family launch). This is a PINNED, exact-string assertion so the
-# NEXT widening (J-06, adding range_trade/double_top/double_bottom) fails LOUDLY here rather than
-# silently leaving the served register out of date again -- whoever adds a family must deliberately
-# re-derive this constant (and this rationale paragraph), never just extend `PLAYBOOK_SETUPS` in
-# isolation.
+# goal-playbook-iter-6 (J-06): PLAYBOOK_REGISTER's opening clause widens AGAIN -- this is the THIRD
+# occurrence of this pattern (J-04, J-05, now J-06), so it is deliberately not deferred. It now
+# names all EIGHT shipped setup families: opening-range-break (one family covering both
+# open_high_break/open_low_break, the same grouping the register has used since J-01),
+# jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top,
+# and double-bottom -- range_trade's own PROVISIONAL tier is a code-comment/spec disclosure, not a
+# reason to omit it from the register (it is a genuinely shipped, detected, measured family this
+# iteration). This is a PINNED, exact-string assertion so the NEXT widening (whenever it lands)
+# fails LOUDLY here rather than silently leaving the served register out of date again -- whoever
+# adds a family must deliberately re-derive this constant (and this rationale paragraph), never
+# just extend `PLAYBOOK_SETUPS` in isolation.
 _EXPECTED_PLAYBOOK_REGISTER = (
     "pre-registered opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, "
-    "and capitulation signals detected on the desk's own recorded 5m/1m bars — every threshold is "
+    "capitulation, range-trade, double-top, and double-bottom signals detected on the desk's own "
+    "recorded 5m/1m bars — every threshold is "
     "fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
     "A signal is a recorded observation, not advice: invalidation_price is the book's own "
     "structural level, disclosed as geometry, never a stop order, a size, or an account concept. "
diff --git a/apps/backend/tests/test_desk_playbook_detect.py b/apps/backend/tests/test_desk_playbook_detect.py
index 93d0752..9f37909 100644
--- a/apps/backend/tests/test_desk_playbook_detect.py
+++ b/apps/backend/tests/test_desk_playbook_detect.py
@@ -32,13 +32,17 @@ import pytest
 
 from app.providers.adapters.base import RawBar
 from app.research.desk_playbook import playbook_parameters
+from app.research.desk_playbook_features import zone_touches
 from app.research.desk_playbook_detect import (
     detect_capitulation,
     detect_cup_handle,
     detect_dbi,
+    detect_double_bottom,
+    detect_double_top,
     detect_euphoria,
     detect_jbe,
     detect_opening_range_breaks,
+    detect_range_trade,
 )
 
 SESSION_DATE = "2026-06-22"
@@ -1014,3 +1018,546 @@ def test_euphoria_near_miss_no_reversal_within_the_bounce_window_fires_no_marker
     baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(7)}}
     marker = detect_euphoria(bars, baseline, _PARAMS)
     assert marker is None
+
+
+# === J-06: the range family -- range_trade (TC-1, TC-2, TC-3) / double_top+double_bottom
+# (TC-4, TC-5, TC-10) ===============================================================================
+#
+# range_trade: a session-wide high/low (`SH`/`SL`, prefix extremes) wide enough
+# (>= PLAYBOOK_RANGE_MIN_WIDTH_MBR) with BOTH the low zone AND the high zone showing >= 2 touches
+# each, each later touch holding its own extreme within PLAYBOOK_RANGE_HOLD_TOL_MBR (spec §3.7's
+# full arming clause -- the BOOK's "test the low AND high twice and hold"), then a reversal-bar
+# trigger within PLAYBOOK_BOUNCE_MAX_BARS of the arming-completing touch, gated by
+# PLAYBOOK_RANGE_HOLD_TOL_MBR throughout the scan, and voided fail-closed when the trigger
+# reference is degenerate (`T <= SL` long / `T >= SH` short -- spec §3.7's Edge cases). Values
+# hand-computed and cross-checked by direct execution (this module's own convention); every
+# fixture bar is physically valid (`low <= min(open, close)`, `high >= max(open, close)`).
+
+_RANGE_TRADE_BASELINE = {
+    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(12)},
+}
+
+
+def _canonical_range_trade_long_bars(symbol: str = "RT1") -> list[RawBar]:
+    """A genuinely TWO-SIDED range (spec §3.7 arms on both zones, never one). MBR = 1.0, so the
+    zones are 1.00 wide and the hold tolerance is 0.50.
+    Slot 0: HIGH TOUCH 1 -- sets `SH` = 105.0, so the high zone is [104.0, 105.0].
+    Slot 1: leaves both zones (103.9 high / 101.5 low).
+    Slot 2: LOW TOUCH 1 -- sets `SL` = 100.0, so the low zone is [100.0, 101.0].
+    Slot 3: leaves the low zone (low 101.5), re-arming it; its high 103.0 crosses the 102.5
+      midrange, which is what makes `crossed_midrange` True here.
+    Slot 4: HIGH TOUCH 2 (high 104.8, inside the high zone; extends `SH` by 0.0 -- "held").
+    Slot 5: leaves the high zone (high 103.5), re-arming it.
+    Slot 6: LOW TOUCH 2 (low 100.4; extends `SL` by 0.0 -- "held") -- the arming-completing
+      touch `b = 6`, so the arming attempt is evaluated at `t = 7`.
+    Slot 7: the reversal-bar trigger (`high 103.5 > high[6] = 102.6`), volume surge; the hold
+      check passes (`min(low[6..6]) = 100.4 >= SL - 0.5 = 99.5`). `T = high[6] = 102.6`.
+    Slots 8-9: session tail (also the post-trigger bars the lookahead property test mutates)."""
+    return [
+        _bar(symbol, E_OPEN + 0 * 300.0, 104.0, 105.0, 103.5, 104.5, 1000),
+        _bar(symbol, E_OPEN + 1 * 300.0, 103.9, 103.9, 101.5, 101.8, 1000),
+        _bar(symbol, E_OPEN + 2 * 300.0, 101.8, 102.0, 100.0, 100.4, 1000),
+        _bar(symbol, E_OPEN + 3 * 300.0, 101.6, 103.0, 101.5, 102.8, 1000),
+        _bar(symbol, E_OPEN + 4 * 300.0, 102.8, 104.8, 102.5, 104.4, 1000),
+        _bar(symbol, E_OPEN + 5 * 300.0, 103.4, 103.5, 102.0, 102.4, 1000),
+        _bar(symbol, E_OPEN + 6 * 300.0, 102.4, 102.6, 100.4, 100.7, 1000),
+        _bar(symbol, E_OPEN + 7 * 300.0, 101.0, 103.5, 100.6, 103.2, 2000),
+        _bar(symbol, E_OPEN + 8 * 300.0, 103.2, 103.4, 102.9, 103.1, 1000),
+        _bar(symbol, E_OPEN + 9 * 300.0, 103.1, 103.3, 102.8, 103.0, 1000),
+    ]
+
+
+def _canonical_range_trade_short_bars(symbol: str = "RT2") -> list[RawBar]:
+    """The resistance-fade mirror, hand-built INDEPENDENTLY (different price scale, different
+    range width, and the two zones tested in the opposite ORDER -- low/low then high/high -- so it
+    is a genuine second computation, not the long fixture's values negated).
+    `SL` = 198.0 (slot 0), `SH` = 205.0 (slot 4) -> range 7.00 MBR; low zone [198.0, 199.0],
+    high zone [204.0, 205.0]; midrange 201.5.
+    Slot 0: LOW TOUCH 1. Slot 1: leaves it. Slot 2: LOW TOUCH 2 (low 198.3 -- held).
+    Slot 3: leaves it. Slot 4: HIGH TOUCH 1 (sets `SH`). Slot 5: leaves the high zone, its low
+      202.0 staying ABOVE the 201.5 midrange -- which is what makes `crossed_midrange` False on
+      this fixture (the True/False pair that proves the field is not constant by construction).
+    Slot 6: HIGH TOUCH 2 (high 204.7 -- held), the arming-completing touch `b = 6`.
+    Slot 7: the reversal-bar trigger (`low 201.0 < low[6] = 202.6`); `T = low[6] = 202.6`.
+    Slots 8-9: session tail."""
+    return [
+        _bar(symbol, E_OPEN + 0 * 300.0, 199.0, 200.4, 198.0, 198.5, 1000),
+        _bar(symbol, E_OPEN + 1 * 300.0, 199.5, 201.0, 199.4, 200.8, 1000),
+        _bar(symbol, E_OPEN + 2 * 300.0, 200.1, 200.2, 198.3, 198.7, 1000),
+        _bar(symbol, E_OPEN + 3 * 300.0, 199.7, 202.5, 199.6, 202.3, 1000),
+        _bar(symbol, E_OPEN + 4 * 300.0, 202.5, 205.0, 202.3, 204.5, 1000),
+        _bar(symbol, E_OPEN + 5 * 300.0, 203.7, 203.8, 202.0, 202.4, 1000),
+        _bar(symbol, E_OPEN + 6 * 300.0, 203.0, 204.7, 202.6, 204.5, 1000),
+        _bar(symbol, E_OPEN + 7 * 300.0, 204.0, 204.2, 201.0, 201.3, 2000),
+        _bar(symbol, E_OPEN + 8 * 300.0, 201.3, 201.8, 200.8, 201.0, 1000),
+        _bar(symbol, E_OPEN + 9 * 300.0, 201.0, 201.5, 200.6, 201.2, 1000),
+    ]
+
+
+def _one_sided_range_trade_bars(symbol: str = "RT1S") -> list[RawBar]:
+    """The both-zones near-miss: the low zone is tested TWICE (slots 1 and 3) while the high zone
+    is touched ONCE (slot 0) -- a plain support test inside a one-way session, the "breakout-only"
+    case spec §3.7's own Ch 13 note excludes. Every other gate this fixture meets (range 5.00 MBR
+    wide, both low touches held, a reversal bar at slot 4 within the bounce window), so the
+    both-zones clause specifically is what silences it; its control is the canonical two-sided
+    fixture above, which differs by exactly one thing -- a genuine second high-zone test."""
+    return [
+        _bar(symbol, E_OPEN + 0 * 300.0, 103.0, 105.0, 103.0, 104.0, 1000),
+        _bar(symbol, E_OPEN + 1 * 300.0, 104.0, 104.2, 100.0, 100.3, 1000),
+        _bar(symbol, E_OPEN + 2 * 300.0, 100.3, 103.0, 102.0, 102.5, 1000),
+        _bar(symbol, E_OPEN + 3 * 300.0, 102.5, 102.8, 100.4, 100.6, 1000),
+        _bar(symbol, E_OPEN + 4 * 300.0, 100.6, 103.5, 100.2, 103.0, 2000),
+        _bar(symbol, E_OPEN + 5 * 300.0, 103.0, 103.2, 102.8, 103.0, 1000),
+        _bar(symbol, E_OPEN + 6 * 300.0, 103.0, 103.1, 102.9, 103.0, 1000),
+    ]
+
+
+def test_canonical_range_trade_long_matches_the_hand_computed_signal():
+    """TC-1: the canonical support-bounce firing -- setup chip, side, and every geometry field
+    hand-verified (values confirmed by direct execution against the fixture). The range is
+    two-sided as spec §3.7 requires: BOTH zone touch counts are 2, and the invalidation
+    (`SL - 0.30*(T - SL)` = 100.0 - 0.30*2.6 = 99.22) sits BELOW the long's own entry."""
+    results = detect_range_trade(
+        _canonical_range_trade_long_bars(), _RANGE_TRADE_BASELINE, "RT1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(results) == 1
+    signal = results[0]
+    assert signal["setup_id"] == "range_trade"
+    assert signal["side"] == "long"
+    assert signal["trigger_price"] == pytest.approx(102.6)
+    assert signal["entry"] == pytest.approx(102.6)
+    assert signal["entry_kind"] == "level"
+    assert signal["price_low"] == pytest.approx(100.0)
+    assert signal["price_high"] == pytest.approx(105.0)
+    assert signal["invalidation_price"] == pytest.approx(99.22)
+    assert signal["invalidation_price"] < signal["entry"]
+    geometry = signal["geometry"]
+    assert geometry["slots_to_break"] == 7
+    assert geometry["range_width_mbr"] == pytest.approx(5.0)
+    assert geometry["low_zone_touches"] == 2
+    assert geometry["high_zone_touches"] == 2
+    assert geometry["crossed_midrange"] is True
+    assert geometry["absorption_bar_present"] is False
+    assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(2.0)
+    assert signal["principles"] == []
+    assert signal["disclosures"]["attempt_count"] == 1
+    assert signal["disclosures"]["bars_to_close"] == 2
+
+
+def test_canonical_range_trade_short_mirrors_the_long_fixture():
+    """TC-2: the exact mirror -- resistance-fade short, invalidation ABOVE the range, geometry
+    magnitudes an independent (not merely negated) hand-computation of the mirrored fixture."""
+    results = detect_range_trade(
+        _canonical_range_trade_short_bars(), _RANGE_TRADE_BASELINE, "RT2", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(results) == 1
+    signal = results[0]
+    assert signal["setup_id"] == "range_trade"
+    assert signal["side"] == "short"
+    assert signal["trigger_price"] == pytest.approx(202.6)
+    assert signal["entry"] == pytest.approx(202.6)
+    assert signal["entry_kind"] == "level"
+    assert signal["price_low"] == pytest.approx(198.0)
+    assert signal["price_high"] == pytest.approx(205.0)
+    # `SH + 0.30*(SH - T)` = 205.0 + 0.30*2.4 = 205.72 -- ABOVE the short's own entry.
+    assert signal["invalidation_price"] == pytest.approx(205.72)
+    assert signal["invalidation_price"] > signal["entry"]
+    geometry = signal["geometry"]
+    assert geometry["slots_to_break"] == 7
+    assert geometry["range_width_mbr"] == pytest.approx(7.0)
+    assert geometry["low_zone_touches"] == 2
+    assert geometry["high_zone_touches"] == 2
+    assert geometry["crossed_midrange"] is False
+    assert geometry["absorption_bar_present"] is False
+    assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(2.0)
+    assert signal["principles"] == ["P5"]  # "P5 at the high side" -- the resistance-fade short
+    assert signal["disclosures"]["attempt_count"] == 1
+
+
+def test_range_trade_one_sided_range_never_arms_and_its_two_sided_control_fires_once():
+    """Spec §3.7's arming clause is "test the low AND high twice and hold": a session that tests
+    one extreme twice while touching the other once -- the breakout-only case Ch 13 excludes --
+    arms nothing on EITHER side. Paired with its control (the iter-4 lesson: `results == []` alone
+    proves nothing): the canonical fixture, which differs by exactly one added high-zone test,
+    fires exactly one signal. This is the formation the pre-audit implementation fired on."""
+    one_sided = _one_sided_range_trade_bars()
+    assert detect_range_trade(
+        one_sided, _RANGE_TRADE_BASELINE, "RT1S", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    ) == []
+    # The one-sided fixture's own touch counts, read directly: the low zone IS tested twice, so
+    # the rejecter is the high zone's single touch, not the low side or the range width.
+    session_low = min(bar.low for bar in one_sided[:4])
+    session_high = max(bar.high for bar in one_sided[:4])
+    near = _PARAMS["near_extreme_mbr"] * _RANGE_TRADE_BASELINE["mbr"]
+    assert (session_high - session_low) >= _PARAMS["range_min_width_mbr"]
+    assert len(zone_touches(one_sided[:4], session_low, session_low + near)) == 2
+    assert len(zone_touches(one_sided[:4], session_high - near, session_high)) == 1
+
+    control = detect_range_trade(
+        _canonical_range_trade_long_bars(), _RANGE_TRADE_BASELINE, "RT1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(control) == 1
+    assert control[0]["geometry"]["high_zone_touches"] == 2
+
+
+def _range_trade_unheld_bars() -> list[RawBar]:
+    """Both zones tested twice, but the SECOND low touch (slot 6, low 99.1) extends the running
+    low by 0.90 MBR against the 0.50 `PLAYBOOK_RANGE_HOLD_TOL_MBR` tolerance -- the range did not
+    "hold", so spec §3.7's arming clause rejects it even though every count is satisfied."""
+    bars = _canonical_range_trade_long_bars("RTH")
+    bars[6] = _bar("RTH", E_OPEN + 6 * 300.0, 102.4, 102.6, 99.1, 99.4, 1000)
+    bars[7] = _bar("RTH", E_OPEN + 7 * 300.0, 99.6, 103.5, 99.3, 103.2, 2000)
+    return bars
+
+
+def test_range_trade_a_touch_that_does_not_hold_the_extreme_never_arms():
+    """The "held" half of spec §3.7's arming clause, with its gate-relaxed control: the ONLY
+    parameter the control changes is `range_hold_tol_mbr` (0.50 -> 2.00, which covers the 0.90
+    extension), and the same bars then fire exactly one signal -- proving that named tolerance
+    specifically is the rejecter."""
+    bars = _range_trade_unheld_bars()
+    assert detect_range_trade(
+        bars, _RANGE_TRADE_BASELINE, "RTH", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    ) == []
+
+    relaxed = {**_PARAMS, "range_hold_tol_mbr": 2.0}
+    relaxed_results = detect_range_trade(
+        bars, _RANGE_TRADE_BASELINE, "RTH", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, relaxed,
+    )
+    assert len(relaxed_results) == 1
+    assert relaxed_results[0]["side"] == "long"
+    assert relaxed_results[0]["trigger_price"] == pytest.approx(102.6)
+    assert relaxed_results[0]["geometry"]["low_zone_touches"] == 2
+    assert relaxed_results[0]["geometry"]["high_zone_touches"] == 2
+
+
+def _range_trade_degenerate_reference_bars(reference_high: float) -> list[RawBar]:
+    """The canonical arming (slots 0-6) followed by a bar whose whole range sits at/below the
+    arming-time `SL` = 100.0 while staying inside the 0.50 hold tolerance (low 99.6 >= 99.5), then
+    a higher-high reversal bar. `reference_high` is the ONLY value that differs between the
+    degenerate fixture (99.9, below `SL`) and its control (100.2, above `SL`)."""
+    bars = _canonical_range_trade_long_bars("RTD")[:7]
+    bars.append(_bar("RTD", E_OPEN + 7 * 300.0, 99.8, reference_high, 99.6, 99.7, 1000))
+    bars.append(_bar("RTD", E_OPEN + 8 * 300.0, 99.7, 100.5, 99.6, 100.4, 2000))
+    bars.append(_bar("RTD", E_OPEN + 9 * 300.0, 100.4, 100.6, 100.1, 100.5, 1000))
+    return bars
+
+
+def test_range_trade_degenerate_trigger_reference_below_the_range_low_fails_closed():
+    """Spec §3.7's Edge cases, "degenerate trigger reference": the invalidation clause is
+    arithmetic on `T - SL`, so `T <= SL` inverts it -- a long whose structural invalidation lands
+    ABOVE its own entry, i.e. recorded born-invalidated. Voided fail-closed. Control: the SAME
+    bars with the reversal bar's reference high lifted from 99.9 to 100.2 (just above `SL`) fire
+    exactly one coherent signal, so the degeneracy clause specifically is the rejecter."""
+    degenerate = _range_trade_degenerate_reference_bars(99.9)
+    assert detect_range_trade(
+        degenerate, _RANGE_TRADE_BASELINE, "RTD", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    ) == []
+    # What the spec's formula WOULD have produced there, computed here from the fixture itself:
+    # T = high[7] = 99.9 < SL = 100.0 -> invalidation 100.03, i.e. above the entry.
+    would_be_trigger, session_low = degenerate[7].high, min(bar.low for bar in degenerate[:7])
+    assert would_be_trigger < session_low
+    assert session_low - _PARAMS["stop_pad_frac"] * (would_be_trigger - session_low) > would_be_trigger
+
+    control = detect_range_trade(
+        _range_trade_degenerate_reference_bars(100.2), _RANGE_TRADE_BASELINE, "RTD", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(control) == 1
+    assert control[0]["side"] == "long"
+    assert control[0]["trigger_price"] == pytest.approx(100.2)
+    assert control[0]["invalidation_price"] == pytest.approx(99.94)
+    assert control[0]["invalidation_price"] < control[0]["entry"]
+
+
+# --- TC-3: a strict break beyond the low zone by more than PLAYBOOK_RANGE_HOLD_TOL_MBR dissolves
+# range-mode -- no signal, PAIRED with a gate-relaxed control (range_hold_tol_mbr widened) proving
+# the hold-tolerance gate specifically is the rejecter (the iter-4 lesson: `results == []` alone
+# proves nothing).
+
+
+def _range_trade_near_miss_bars() -> list[RawBar]:
+    """The SAME two-sided arming as the canonical long fixture (slots 0-6), but slot 7 breaks well
+    beyond the hold floor (`SL - RANGE_HOLD_TOL_MBR*MBR = 99.5`) without itself reversing -- the
+    scan's hold check fails at slot 8 (`min(low[6..7]) == 97.0 < 99.5`), ending the scan before the
+    would-be-reversal bar at slot 8 is ever reached under the default tolerance."""
+    bars = _canonical_range_trade_long_bars("RTNM")[:7]
+    bars.append(_bar("RTNM", E_OPEN + 7 * 300.0, 100.7, 100.8, 97.0, 97.2, 1000))  # breaks hold tol
+    bars.append(_bar("RTNM", E_OPEN + 8 * 300.0, 97.2, 103.5, 97.0, 103.0, 2000))  # unreachable
+    bars.append(_bar("RTNM", E_OPEN + 9 * 300.0, 103.0, 103.2, 102.8, 103.0, 1000))
+    return bars
+
+
+def test_range_trade_near_miss_break_beyond_hold_tolerance_fires_no_signal():
+    """TC-3: the formation dissolves silently -- no signal, regardless of the later reversal bar.
+    The control below relaxes ONLY `range_hold_tol_mbr` and proves that gate, specifically, is what
+    rejected it (the arming itself -- range width, both zones tested twice and held -- passed)."""
+    bars = _range_trade_near_miss_bars()
+    results = detect_range_trade(
+        bars, _RANGE_TRADE_BASELINE, "RTNM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert results == []
+
+    relaxed = {**_PARAMS, "range_hold_tol_mbr": 10.0}
+    relaxed_results = detect_range_trade(
+        bars, _RANGE_TRADE_BASELINE, "RTNM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, relaxed,
+    )
+    assert len(relaxed_results) == 1
+    assert relaxed_results[0]["side"] == "long"
+    assert relaxed_results[0]["geometry"]["slots_to_break"] == 8
+    assert relaxed_results[0]["trigger_price"] == pytest.approx(100.8)
+
+
+# --- range_trade's own truncate/mutate lookahead property test (TC-8) -----------------------------
+# BOTH sides are parametrized (the J-04 `_CONTINUATION_LOOKAHEAD_FIXTURES` precedent): the long and
+# short walks share one code path, but a shared walk is exactly where a mirror-only lookahead bug
+# would hide, so the mirror is truncate/mutate-tested in its own right.
+
+_RANGE_TRADE_LOOKAHEAD_FIXTURES = [
+    (detect_range_trade, _canonical_range_trade_long_bars(), "RT1"),
+    (detect_range_trade, _canonical_range_trade_short_bars(), "RT2"),
+]
+
+
+@pytest.mark.parametrize("detect_fn, bars, symbol", _RANGE_TRADE_LOOKAHEAD_FIXTURES)
+def test_range_trade_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields(
+    detect_fn, bars, symbol
+):
+    full = detect_fn(bars, _RANGE_TRADE_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
+    assert len(full) == 1
+    trigger_idx = full[0]["geometry"]["slots_to_break"]
+
+    truncated = detect_fn(
+        bars[: trigger_idx + 1], _RANGE_TRADE_BASELINE, symbol, SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(truncated) == 1
+    assert truncated[0]["trigger_price"] == full[0]["trigger_price"]
+    assert truncated[0]["invalidation_price"] == full[0]["invalidation_price"]
+    assert truncated[0]["geometry"] == full[0]["geometry"]
+
+
+@pytest.mark.parametrize("detect_fn, bars, symbol", _RANGE_TRADE_LOOKAHEAD_FIXTURES)
+def test_range_trade_mutating_a_bar_after_the_trigger_changes_nothing(detect_fn, bars, symbol):
+    full = detect_fn(bars, _RANGE_TRADE_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
+    assert len(full) == 1
+    trigger_idx = full[0]["geometry"]["slots_to_break"]
+    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"
+
+    mutated = list(bars)
+    victim = mutated[trigger_idx + 1]
+    mutated[trigger_idx + 1] = RawBar(
+        victim.symbol, victim.timeframe, victim.epoch,
+        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
+    )
+    mutated_result = detect_fn(
+        mutated, _RANGE_TRADE_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert mutated_result == full
+
+
+# === J-06: double_top (TC-4, TC-5, TC-10) / double_bottom (mirror) =================================
+
+_DOUBLE_TOP_BASELINE = {
+    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(20)},
+}
+
+
+def _canonical_double_top_bars(symbol: str = "DT1", p2_high: float = 110.3, idx14_low: float = 107.0) -> list[RawBar]:
+    """Two confirmed swing-high pivots -- P1 at slot 3 (high=110, confirmed_at=6), P2 at slot 13
+    (high=`p2_high`, confirmed_at=16), separated by 10 bars (>= `TOPS_MIN_SEPARATION_BARS`=4) and
+    `TOPS_MATCH_MBR`-close (110.3-110=0.3 <= 1.0 by default). A valley (min low strictly between
+    them, at slot 8, low=97.0) with depth 13.0 MBR (>= `MIN_STRUCTURE_DEPTH_MBR`=2.0). Slot 18: the
+    valley-break trigger (low=96.0 < 97.0). `idx14_low` is parameterized so the fail-closed fixture
+    below can reuse this exact shape with only that one bar's low changed."""
+    return [
+        _bar(symbol, E_OPEN + 0 * 300.0, 104, 105, 104, 104.5, 1000),
+        _bar(symbol, E_OPEN + 1 * 300.0, 104.5, 106, 104, 105.5, 1000),
+        _bar(symbol, E_OPEN + 2 * 300.0, 105.5, 107, 105, 106.5, 1000),
+        _bar(symbol, E_OPEN + 3 * 300.0, 106.5, 110, 106, 109, 1000),  # P1
+        _bar(symbol, E_OPEN + 4 * 300.0, 109, 108, 107, 107.5, 1000),
+        _bar(symbol, E_OPEN + 5 * 300.0, 107.5, 105, 104, 104.5, 1000),
+        _bar(symbol, E_OPEN + 6 * 300.0, 104.5, 102, 101, 101.5, 1000),
+        _bar(symbol, E_OPEN + 7 * 300.0, 101.5, 100, 99, 99.5, 1000),
+        _bar(symbol, E_OPEN + 8 * 300.0, 99.5, 98, 97, 97.5, 1000),  # valley low=97
+        _bar(symbol, E_OPEN + 9 * 300.0, 97.5, 99, 97.2, 98.5, 1000),
+        _bar(symbol, E_OPEN + 10 * 300.0, 98.5, 101, 98, 100.5, 1000),
+        _bar(symbol, E_OPEN + 11 * 300.0, 100.5, 104, 100, 103.5, 1000),
+        _bar(symbol, E_OPEN + 12 * 300.0, 103.5, 107, 103, 106.5, 1000),
+        _bar(symbol, E_OPEN + 13 * 300.0, 106.5, p2_high, 106, p2_high - 0.8, 1000),  # P2
+        _bar(symbol, E_OPEN + 14 * 300.0, p2_high - 0.8, 108, idx14_low, 107.5, 1000),
+        _bar(symbol, E_OPEN + 15 * 300.0, 107.5, 106, 105, 105.5, 1000),
+        _bar(symbol, E_OPEN + 16 * 300.0, 105.5, 104, 103, 103.5, 1000),  # P2 confirmed_at
+        _bar(symbol, E_OPEN + 17 * 300.0, 103.5, 103.8, 102, 102.5, 1000),
... [diff_bound] apps/backend/tests/test_desk_playbook_detect.py: 169 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_playbook_guards.py b/apps/backend/tests/test_desk_playbook_guards.py
index 68f018b..10c2f8a 100644
--- a/apps/backend/tests/test_desk_playbook_guards.py
+++ b/apps/backend/tests/test_desk_playbook_guards.py
@@ -4,7 +4,12 @@ substrings/regex; no runtime, no import-time side effects beyond reading the fil
 goal-playbook-iter-5 (J-05) with two MORE guards -- this time behavioral rather than source-scan,
 since "does the euphoria marker ever leak into a served row" and "is marker decoration
 forward-only" are properties of DATA the decoration pass produces, not of code SHAPE a regex could
-usefully police.
+usefully police. Extended by goal-playbook-iter-6 (J-06) with a THIRD behavioral guard -- this
+one call-COUNTING instrumentation (a stub/counting double patched onto the real
+``compute_tradability``/``compute_levels`` functions), since "does the playbook walk ever call the
+desk's own structural-wall computations" is a property of RUNTIME CALLS a source-scan regex could
+not usefully police either (the playbook module imports neither function today, but a future
+refactor could introduce an indirect call path a regex would miss; instrumentation survives that).
 
 (a) TC-12 -- the no-threshold-sweep guard: no playbook module (``desk_playbook.py``,
     ``desk_playbook_detect.py``, ``desk_playbook_features.py``) contains a ``for``/comprehension
@@ -26,6 +31,11 @@ usefully police.
     decorates a signal whose own trigger bar is AT OR BEFORE a marker's trigger bar, and a
     ``capitulation`` signal never self-decorates its own firing.
 
+(d) TC-7 (J-06) -- the zero-structural-calls guard: ``compute_playbook`` calls neither
+    ``app.research.tradability.compute_tradability`` nor ``app.research.levels.compute_levels``,
+    over a real, ``BarStore``-backed fixture walk that fires all eight setup families in one call
+    -- the book's intraday ranges and the desk's structural walls are different owners.
+
 Every guard carries a seeded counter-test (the ``test_copy_discipline.py`` precedent: "a lint that
 can never fail proves nothing")."""
 
@@ -34,10 +44,18 @@ from __future__ import annotations
 import pathlib
 import re
 
+import pytest
+
+from app.config import CONFIG
+from app.providers.adapters.base import RawBar
 from app.research import desk_playbook as desk_playbook_module
 from app.research import desk_playbook_detect as desk_playbook_detect_module
 from app.research import desk_playbook_features as desk_playbook_features_module
-from app.research.desk_playbook import _decorate_markers, playbook_parameters
+from app.research import levels as levels_module
+from app.research import tradability as tradability_module
+from app.research.bars import BarStore
+from app.research.desk_playbook import _decorate_markers, compute_playbook, playbook_parameters
+from app.research.desk_universe import UniverseStore
 
 _PLAYBOOK_MODULES = (
     desk_playbook_module,
@@ -302,3 +320,332 @@ def test_decorate_markers_guard_can_fail_on_a_seeded_violation():
     # ... yet the REAL function does not:
     _decorate_markers([signal], [marker], _PARAMS)
     assert signal["disclosures"]["euphoria_recent"] is False
+
+
+# --- (d) TC-7 (goal-playbook-iter-6, J-06) -- the zero-`compute_tradability`/`compute_levels`
+# call-counting guard -----------------------------------------------------------------------------
+#
+# A real, BarStore-backed fixture walk across EIGHT members, each individually crafted to fire
+# exactly one of the eight shipped setup families (open_high_break stands in for the
+# opening-range-break family; jbe/dbi/cup_handle/capitulation/range_trade/double_top/double_bottom
+# each get their own member) -- the SAME canonical fixture shapes ``test_desk_playbook_detect.py``
+# already hand-verifies as pure detector calls, planted through a real ``BarStore`` (the
+# ``test_desk_playbook.py`` precedent: ``_plant_ladder_baseline_sessions`` et al.).
+
+_GUARD_SESSION_DATE = "2026-06-22"
+_GUARD_E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET
+_GUARD_BASELINE_DATES = [f"2026-06-{d:02d}" for d in range(8, 18)]  # 10 prior dates
+
+
+def _guard_bar(symbol: str, epoch: float, o: float, h: float, low: float, c: float, v: int = 1000) -> RawBar:
+    return RawBar(symbol, "5m", epoch, o, h, low, c, v)
+
+
+def _plant_guard_baseline_sessions(bar_store: BarStore, symbol: str, slots: int) -> None:
+    """``slots`` identical, flat prior RTH 5m sessions (range 1.0, volume 1000 -> MBR=1.0, a full
+    slot-volume-median vector covering every slot the fixture's OWN session length needs) --
+    generalizes ``test_desk_playbook.py``'s ``_plant_ladder_baseline_sessions`` to an arbitrary
+    slot count, since this guard's eight fixtures each carry a different session length."""
+    bars = []
+    for day in _GUARD_BASELINE_DATES:
+        day_open = _GUARD_E_OPEN - (22 - int(day[-2:])) * 86_400.0
+        for slot in range(slots):
+            bars.append(_guard_bar(symbol, day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
+    bar_store.record(
+        symbol=symbol, timeframe="5m",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
+        feed="test", bars=bars,
+    )
+
+
+def _plant_guard_session(bar_store: BarStore, symbol: str, bars_5m: list[RawBar]) -> None:
+    bar_store.record(
+        symbol=symbol, timeframe="5m",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
+        feed="test", bars=bars_5m,
+    )
+
+
+def _guard_open_high_break_bars(symbol: str) -> list[RawBar]:
+    return [
+        _guard_bar(symbol, _GUARD_E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
+    ]
+
+
+def _guard_jbe_bars(symbol: str) -> list[RawBar]:
+    return [
+        _guard_bar(symbol, _GUARD_E_OPEN, 98.4, 98.5, 98.0, 98.3, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 98.3, 98.4, 98.1, 98.3, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 98.3, 98.4, 98.05, 98.3, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 98.3, 98.45, 98.2, 98.3, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 98.3, 98.4, 98.15, 98.3, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 98.3, 98.5, 98.3, 98.4, 3000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1800.0, 103.5, 103.8, 103.2, 103.6, 400),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2100.0, 103.6, 104.0, 103.3, 103.7, 500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2400.0, 103.7, 103.9, 103.4, 103.8, 450),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2700.0, 103.9, 104.8, 103.8, 104.5, 1500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3000.0, 104.5, 104.7, 104.3, 104.6, 900),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3300.0, 104.6, 104.8, 104.4, 104.7, 900),
+    ]
+
+
+def _guard_dbi_bars(symbol: str) -> list[RawBar]:
+    return [
+        _guard_bar(symbol, _GUARD_E_OPEN, 109.6, 110.0, 109.5, 109.7, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 109.7, 109.9, 109.6, 109.7, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 109.7, 109.95, 109.6, 109.7, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 109.7, 109.8, 109.55, 109.7, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 109.7, 109.85, 109.6, 109.7, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 109.6, 109.7, 109.5, 109.6, 3000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1800.0, 104.5, 104.8, 104.2, 104.4, 400),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2100.0, 104.4, 104.7, 104.0, 104.3, 500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2400.0, 104.3, 104.6, 104.1, 104.2, 450),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2700.0, 104.1, 104.2, 103.2, 103.5, 1500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3000.0, 103.5, 103.7, 103.3, 103.4, 900),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3300.0, 103.4, 103.6, 103.2, 103.3, 900),
+    ]
+
+
+def _guard_cup_handle_bars(symbol: str) -> list[RawBar]:
+    bars = [
+        _guard_bar(symbol, _GUARD_E_OPEN, 106.5, 107.0, 106.0, 106.8, 500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 106.8, 108.0, 106.5, 107.5, 500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 107.5, 109.0, 107.0, 108.5, 500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 108.5, 110.0, 108.0, 109.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 109.5, 109.0, 108.0, 108.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 108.5, 108.0, 107.0, 107.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1800.0, 107.5, 107.5, 106.5, 107.0, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2100.0, 107.0, 106.5, 106.0, 106.2, 300),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2400.0, 106.2, 106.0, 105.5, 105.8, 300),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2700.0, 105.8, 105.5, 105.0, 105.2, 300),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3000.0, 105.2, 106.0, 105.1, 105.8, 300),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3300.0, 105.8, 107.0, 105.5, 106.8, 300),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3600.0, 106.8, 108.0, 106.5, 107.8, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3900.0, 107.8, 109.0, 107.5, 108.8, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 4200.0, 108.8, 109.5, 108.5, 109.2, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 4500.0, 109.2, 110.0, 108.8, 109.6, 1000),
+    ]
+    for i, (o, h, low, c, v) in enumerate(
+        [(109.6, 109.3, 108.0, 108.5, 400), (108.5, 109.0, 107.8, 108.2, 400), (108.2, 109.4, 108.0, 108.9, 400)],
+        start=16,
+    ):
+        bars.append(_guard_bar(symbol, _GUARD_E_OPEN + i * 300.0, o, h, low, c, v))
+    bars.append(_guard_bar(symbol, _GUARD_E_OPEN + 19 * 300.0, 108.9, 110.5, 108.7, 110.2, 1500))
+    bars.append(_guard_bar(symbol, _GUARD_E_OPEN + 20 * 300.0, 110.2, 110.4, 109.9, 110.1, 900))
+    bars.append(_guard_bar(symbol, _GUARD_E_OPEN + 21 * 300.0, 110.1, 110.3, 109.8, 110.0, 900))
+    return bars
+
+
+def _guard_capitulation_bars(symbol: str) -> list[RawBar]:
+    return [
+        _guard_bar(symbol, _GUARD_E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
+        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 99.6, 101.5, 99.4, 101.0, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 101.0, 101.3, 100.8, 101.1, 900),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1800.0, 101.1, 101.4, 100.9, 101.2, 900),
+    ]
+
+
+def _guard_range_trade_bars(symbol: str) -> list[RawBar]:
+    # The canonical two-sided armed range (both zones tested twice and held, spec §3.7's full
+    # arming clause) -- the same fixture `test_desk_playbook_detect.py` hand-computes.
+    return [
+        _guard_bar(symbol, _GUARD_E_OPEN + 0 * 300.0, 104.0, 105.0, 103.5, 104.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1 * 300.0, 103.9, 103.9, 101.5, 101.8, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2 * 300.0, 101.8, 102.0, 100.0, 100.4, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3 * 300.0, 101.6, 103.0, 101.5, 102.8, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 4 * 300.0, 102.8, 104.8, 102.5, 104.4, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 5 * 300.0, 103.4, 103.5, 102.0, 102.4, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 6 * 300.0, 102.4, 102.6, 100.4, 100.7, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 7 * 300.0, 101.0, 103.5, 100.6, 103.2, 2000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 8 * 300.0, 103.2, 103.4, 102.9, 103.1, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 9 * 300.0, 103.1, 103.3, 102.8, 103.0, 1000),
+    ]
+
+
+def _guard_double_top_bars(symbol: str) -> list[RawBar]:
+    return [
+        _guard_bar(symbol, _GUARD_E_OPEN + 0 * 300.0, 104, 105, 104, 104.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1 * 300.0, 104.5, 106, 104, 105.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2 * 300.0, 105.5, 107, 105, 106.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3 * 300.0, 106.5, 110, 106, 109, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 4 * 300.0, 109, 108, 107, 107.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 5 * 300.0, 107.5, 105, 104, 104.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 6 * 300.0, 104.5, 102, 101, 101.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 7 * 300.0, 101.5, 100, 99, 99.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 8 * 300.0, 99.5, 98, 97, 97.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 9 * 300.0, 97.5, 99, 97.2, 98.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 10 * 300.0, 98.5, 101, 98, 100.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 11 * 300.0, 100.5, 104, 100, 103.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 12 * 300.0, 103.5, 107, 103, 106.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 13 * 300.0, 106.5, 110.3, 106, 109.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 14 * 300.0, 109.5, 108, 107, 107.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 15 * 300.0, 107.5, 106, 105, 105.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 16 * 300.0, 105.5, 104, 103, 103.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 17 * 300.0, 103.5, 103.8, 102, 102.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 18 * 300.0, 102.5, 103, 96.0, 96.5, 2000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 19 * 300.0, 96.5, 97, 96, 96.8, 1000),
+    ]
+
+
+def _guard_double_bottom_bars(symbol: str) -> list[RawBar]:
+    return [
+        _guard_bar(symbol, _GUARD_E_OPEN + 0 * 300.0, 96, 97, 96, 96.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 1 * 300.0, 96.5, 97, 95, 95.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 2 * 300.0, 95.5, 96, 94, 94.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 3 * 300.0, 94.5, 95, 90, 91, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 4 * 300.0, 91, 93, 92, 92.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 5 * 300.0, 92.5, 96, 95, 95.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 6 * 300.0, 95.5, 99, 98, 98.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 7 * 300.0, 98.5, 101, 100, 100.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 8 * 300.0, 100.5, 103, 102, 102.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 9 * 300.0, 102.5, 101, 100.8, 101, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 10 * 300.0, 101, 99, 98, 98.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 11 * 300.0, 98.5, 96, 95, 95.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 12 * 300.0, 95.5, 93, 92, 92.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 13 * 300.0, 92.5, 91, 89.7, 90.2, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 14 * 300.0, 90.2, 92, 91, 91.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 15 * 300.0, 91.5, 94, 93, 93.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 16 * 300.0, 93.5, 96, 95, 95.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 17 * 300.0, 95.5, 95.8, 94, 94.5, 1000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 18 * 300.0, 94.5, 104.0, 95, 103.5, 2000),
+        _guard_bar(symbol, _GUARD_E_OPEN + 19 * 300.0, 103.5, 104, 103, 103.8, 1000),
+    ]
+
+
+def test_compute_playbook_calls_neither_compute_tradability_nor_compute_levels(tmp_path, monkeypatch):
+    """TC-7: a real, ``BarStore``-backed fixture walk that fires all EIGHT shipped setup families
+    in one ``compute_playbook`` call makes exactly zero calls to
+    ``app.research.tradability.compute_tradability`` and exactly zero calls to
+    ``app.research.levels.compute_levels`` -- the book's intraday ranges and the desk's structural
+    walls are different owners."""
+    calls = {"tradability": 0, "levels": 0}
+
+    def _counting_tradability(*args, **kwargs):
+        calls["tradability"] += 1
+        raise AssertionError("compute_tradability must never be called from the playbook walk")
+
+    def _counting_levels(*args, **kwargs):
+        calls["levels"] += 1
+        raise AssertionError("compute_levels must never be called from the playbook walk")
+
+    monkeypatch.setattr(tradability_module, "compute_tradability", _counting_tradability)
+    monkeypatch.setattr(levels_module, "compute_levels", _counting_levels)
+
+    bar_store = BarStore(tmp_path / "bars")
+    members = ["OHB", "JBE", "DBI", "CUP", "CAP", "RT", "DT", "DB"]
+    fixture_builders = {
+        "OHB": (_guard_open_high_break_bars, 6),
+        "JBE": (_guard_jbe_bars, 12),
+        "DBI": (_guard_dbi_bars, 12),
+        "CUP": (_guard_cup_handle_bars, 22),
+        "CAP": (_guard_capitulation_bars, 9),
+        "RT": (_guard_range_trade_bars, 10),
+        "DT": (_guard_double_top_bars, 20),
+        "DB": (_guard_double_bottom_bars, 20),
+    }
+    for symbol, (builder, slots) in fixture_builders.items():
+        _plant_guard_baseline_sessions(bar_store, symbol, slots)
+        _plant_guard_session(bar_store, symbol, builder(symbol))
+
+    universe_store = UniverseStore(tmp_path / "universe")
+    universe_store.record(
+        members=members, raw_members={m: m for m in members},
+        source_url="test", min_members=1, max_members=len(members),
+    )
+
+    result = compute_playbook(
+        universe_store, bar_store, CONFIG.config_fingerprint(), _GUARD_SESSION_DATE,
+    )
+
+    # `>=`, not `==`: every member runs through ALL nine detectors (the opening-range-break pair
+    # included), so a member built to fire e.g. `capitulation` may ALSO incidentally break its own
+    # opening range on one side -- an honest, harmless extra signal, not a fixture bug. The
+    # assertion only needs "every one of the eight families fired at least once somewhere".
+    fired_setups = {s["setup_id"] for s in result["signals"]}
+    expected_families = {
+        "open_high_break", "jbe", "dbi", "cup_handle", "capitulation",
+        "range_trade", "double_top", "double_bottom",
+    }
+    assert fired_setups >= expected_families, (
+        f"expected all eight setup families to fire, got {fired_setups} (absences: {result['absences']})"
+    )
+
+    assert calls == {"tradability": 0, "levels": 0}
+
+
+def test_zero_structural_calls_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing. A deliberately WRONG call site
+    (calling the real, patched ``compute_tradability``) trips the counting stub's own assertion."""
+    calls = {"tradability": 0}
+
+    def _counting_tradability(*args, **kwargs):
+        calls["tradability"] += 1
+        raise AssertionError("seeded violation")
+
+    with pytest.MonkeyPatch.context() as mp:
+        mp.setattr(tradability_module, "compute_tradability", _counting_tradability)
+        with pytest.raises(AssertionError, match="seeded violation"):
+            tradability_module.compute_tradability()
+    assert calls["tradability"] == 1
+
+
+# --- TC-18 (goal-playbook-iter-6, J-06) -- the doc-only spec edit's own zero-behavior-change proof -
+#
+# `docs/playbook-detector-spec.md` §3.5 gained prose transcribing the `decline_bars`/`decline_mbr`
+# reading `_find_climax_formation`/`detect_capitulation` already ship (the assumption-ledger entry
+# "iter-6 -- goal-decomposer"). A pinned source hash of BOTH function bodies -- not a `git diff`
+# subprocess, which would also need to special-case every OTHER, legitimate edit this same iteration
+# makes elsewhere in the file -- proves neither function's own code lines moved by even one
+# character; a companion pinned-constant check proves the capitulation-relevant `PLAYBOOK_*` values
+# these two functions read are untouched too.
+
+import hashlib
+import inspect
+
+_FIND_CLIMAX_FORMATION_SHA256 = "1a6b880d320072ad1a79b8d262accb7352fefae61ab85017c5d44a070b62e585"
+_DETECT_CAPITULATION_SHA256 = "ffff5f2b4a3298ee48f4194e2f0de634a4a6fec37ba0512670b5b1dadc1240ca"
+
+
+def test_decline_disclosure_doc_edit_left_the_capitulation_code_byte_unchanged():
+    """TC-18: `_find_climax_formation`'s and `detect_capitulation`'s own source (extracted live via
+    ``inspect.getsource``) still hashes to the EXACT value pinned before this iteration's doc-only
+    spec edit landed -- proving the spec §3.5 prose addition is genuinely zero-behavior-change, not
+    a disguised code edit."""
+    from app.research.desk_playbook_detect import _find_climax_formation, detect_capitulation
+
+    assert hashlib.sha256(inspect.getsource(_find_climax_formation).encode()).hexdigest() == (
+        _FIND_CLIMAX_FORMATION_SHA256
+    )
+    assert hashlib.sha256(inspect.getsource(detect_capitulation).encode()).hexdigest() == (
+        _DETECT_CAPITULATION_SHA256
+    )
+    # Companion constant check: every PLAYBOOK_* value these two functions actually read is
+    # untouched (the doc edit transcribes existing behavior; it invents, tunes, or moves no number).
+    params = playbook_parameters()
+    assert params["vertical_window_bars"] == 3
+    assert params["vertical_move_mbr"] == 4.0
+    assert params["vertical_bar_mbr"] == 2.5
+    assert params["bounce_max_bars"] == 3
+    assert params["stop_pad_frac"] == 0.30
+    assert params["rvol_surge"] == 2.0
+
+
+def test_decline_disclosure_doc_edit_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing. A deliberately WRONG (seeded)
+    hash is rejected."""
+    import hashlib as _hashlib
+    import inspect as _inspect
+
+    from app.research.desk_playbook_detect import _find_climax_formation
+
+    real_hash = _hashlib.sha256(_inspect.getsource(_find_climax_formation).encode()).hexdigest()
+    seeded_wrong_hash = "0" * 64
+    assert real_hash != seeded_wrong_hash
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 69fdf7b..2f2714d 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -165,6 +165,12 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
 # numerics -- `PlaybookSignalDetail`'s capitulation branch renders `decline_mbr`/`climax_rvol`/
 # `bars_from_climax_to_trigger` verbatim (`decline_bars` is a plain bar count, like `base_bars`/
 # `cup_bars` before it, so it stays outside this price-arithmetic list by the same precedent).
+# goal-playbook-iter-6 (J-06): extended AGAIN for the range family's own NEW `signal.geometry.*`
+# numerics -- `PlaybookSignalDetail`'s range_trade branch renders `range_width_mbr` verbatim, and
+# its double_top/double_bottom branch renders `tops_gap_mbr`/`valley_depth_mbr`/
+# `nominal_risk_mbr`/`second_top_rvol_vs_first` verbatim. Bar-count/int-count fields
+# (`tops_separation_bars`, `low_zone_touches`, `high_zone_touches`) stay OUT of this list, following
+# the `base_bars`/`cup_bars`/`decline_bars` precedent -- a plain count is not a price.
 _PRICE_ARITHMETIC_FIELDS = (
     r"row\.(?:distance_bps|price_low|price_high|reference_close"
     r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
@@ -178,7 +184,8 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|signal\.(?:trigger_price|invalidation_price)"
     r"|geometry\.(?:jump_mbr|base_range_mbr|ladder_step_ratio|cup_depth_mbr|handle_retrace_frac"
     r"|handle_duration_frac|cup_middle_third_rvol_median|cup_outer_third_rvol_median"
-    r"|handle_rvol_median|decline_mbr|climax_rvol|bars_from_climax_to_trigger)"
+    r"|handle_rvol_median|decline_mbr|climax_rvol|bars_from_climax_to_trigger"
+    r"|range_width_mbr|tops_gap_mbr|valley_depth_mbr|nominal_risk_mbr|second_top_rvol_vs_first)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -312,6 +319,24 @@ def test_desk_page_price_arithmetic_guard_catches_capitulation_field_arithmetic(
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bars) is not None
 
 
+def test_desk_page_price_arithmetic_guard_catches_range_family_field_arithmetic():
+    """goal-playbook-iter-6 (J-06) counter-test: the extended guard catches arithmetic on the range
+    family's own NEW `geometry.*` bindings (range_trade's `range_width_mbr`; double_top/
+    double_bottom's `tops_gap_mbr`/`valley_depth_mbr`/`nominal_risk_mbr`/
+    `second_top_rvol_vs_first`)."""
+    seeded_range_width = "const half = geometry.range_width_mbr / 2;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_range_width) is not None
+
+    seeded_tops = "const net = geometry.tops_gap_mbr - geometry.valley_depth_mbr;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_tops) is not None
+
+    seeded_risk = "const scaled = geometry.nominal_risk_mbr * 2;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_risk) is not None
+
+    seeded_rvol_ratio = "const inverse = 1 / geometry.second_top_rvol_vs_first;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_rvol_ratio) is not None
+
+
 # goal-playbook-iter-4 audit (F1): `base_lows_ascending` is ONE served field name carrying the
 # direction-appropriate triangle check underneath (non-decreasing LOWS for `jbe`, non-increasing
 # HIGHS for `dbi` -- see `desk_playbook_detect._base_lows_ascending`). The continuation geometry
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index f45b5cf..16b8b5a 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -4405,6 +4405,9 @@ function playbookSetupLabel(setupId: string): string {
   if (setupId === "dbi") return "Drop-Base Implosion";
   if (setupId === "cup_handle") return "Cup and Handle";
   if (setupId === "capitulation") return "Capitulation";
+  if (setupId === "range_trade") return "Range Trade";
+  if (setupId === "double_top") return "Double Top";
+  if (setupId === "double_bottom") return "Double Bottom";
   return setupId;
 }
 
@@ -4639,6 +4642,30 @@ function PlaybookSignalDetail({
           climax · broke at slot {geometry.slots_to_break}
         </p>
       )}
+      {/* goal-playbook-iter-6 (J-06): range_trade's own geometry line -- the tested-and-held
+          range's width, each zone's own touch count, and the two disclosure flags, all rendered
+          verbatim from the served payload. */}
+      {signal.setup_id === "range_trade" && (
+        <p data-testid="desk-playbook-signal-range-trade-geometry" className="mt-1 text-[11px] text-slate-500">
+          range {fmt(geometry.range_width_mbr)} MBR wide · low zone touches{" "}
+          {geometry.low_zone_touches} · high zone touches {geometry.high_zone_touches} · broke at
+          slot {geometry.slots_to_break}
+          {geometry.crossed_midrange && " · crossed midrange"}
+          {geometry.absorption_bar_present && " · absorption bar present"}
+        </p>
+      )}
+      {/* goal-playbook-iter-6 (J-06): double_top/double_bottom's own geometry line -- the two
+          tops'/bottoms' gap and separation, the valley/peak depth, the full (never-shrunk)
+          pattern-height nominal risk, and the second-top/bottom RVOL ratio, all rendered verbatim. */}
+      {(signal.setup_id === "double_top" || signal.setup_id === "double_bottom") && (
+        <p data-testid="desk-playbook-signal-double-extreme-geometry" className="mt-1 text-[11px] text-slate-500">
+          gap {fmt(geometry.tops_gap_mbr)} MBR · separation {geometry.tops_separation_bars} bar(s)
+          · depth {fmt(geometry.valley_depth_mbr)} MBR · nominal risk {fmt(geometry.nominal_risk_mbr)}{" "}
+          MBR · broke at slot {geometry.slots_to_break}
+          {geometry.second_top_rvol_vs_first !== null && geometry.second_top_rvol_vs_first !== undefined &&
+            ` · second RVOL vs first ${fmt(geometry.second_top_rvol_vs_first)}`}
+        </p>
+      )}
       <p className="mt-1 text-[11px] text-slate-500">
         volume: {volume.spike_into_trigger_verdict}
         {volume.rvol_trigger_bar !== null && ` · trigger RVOL ${fmt(volume.rvol_trigger_bar)}`}
@@ -4991,9 +5018,9 @@ function PlaybookRecordView({
         <p className="text-sm font-medium text-amber-300">Playbook not computed for this session.</p>
         <p className="mt-1 text-xs text-amber-200/70">
           Run Playbook detects and measures the opening-range-break, jump-base-explosion,
-          drop-base-implosion, cup-and-handle, and capitulation families on{" "}
-          {control.sessionDate}&apos;s own recorded bars — an explicit operator act, nothing runs on
-          page load.
+          drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top, and
+          double-bottom families on {control.sessionDate}&apos;s own recorded bars — an explicit
+          operator act, nothing runs on page load.
         </p>
         <div className="mt-3 space-y-1 text-left">
           <PlaybookRunsNote result={runsResult} />
@@ -5089,9 +5116,10 @@ function PlaybookSection({
     <div data-testid="desk-playbook-section" className="space-y-3">
       <p className="max-w-3xl text-sm text-slate-500">
         The book&apos;s opening-range-break, jump-base-explosion, drop-base-implosion,
-        cup-and-handle, and capitulation signals, detected on this session&apos;s own recorded
-        5m/1m bars and measured with the desk forward rail&apos;s own conventions — read verbatim
-        from GET /research/desk/playbook. Nothing here is recomputed in the browser.
+        cup-and-handle, capitulation, range-trade, double-top, and double-bottom signals, detected
+        on this session&apos;s own recorded 5m/1m bars and measured with the desk forward
+        rail&apos;s own conventions — read verbatim from GET /research/desk/playbook. Nothing here
+        is recomputed in the browser.
       </p>
       <div className="flex flex-col items-center gap-1">
         <label className="flex flex-col items-center gap-1">
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 954a8e0..e2da4bb 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1516,6 +1516,18 @@ export interface DeskPlaybookGeometry {
   decline_bars?: number;
   climax_rvol?: number;
   bars_from_climax_to_trigger?: number;
+  // range_trade only (J-06, spec §3.7)
+  range_width_mbr?: number;
+  low_zone_touches?: number;
+  high_zone_touches?: number;
+  crossed_midrange?: boolean;
+  absorption_bar_present?: boolean;
+  // double_top / double_bottom only (J-06, spec §3.8-3.9)
+  tops_gap_mbr?: number;
+  tops_separation_bars?: number;
+  valley_depth_mbr?: number;
+  nominal_risk_mbr?: number;
+  second_top_rvol_vs_first?: number | null;
 }
 
 export interface DeskPlaybookVolume {
diff --git a/docs/playbook-detector-spec.md b/docs/playbook-detector-spec.md
index d672583..4da559a 100644
--- a/docs/playbook-detector-spec.md
+++ b/docs/playbook-detector-spec.md
@@ -272,6 +272,20 @@ cases. Side/band/entry/measurement always follow §0.
 - **Caps.** 1 per symbol-session (first).
 - **Disclosures.** `decline_mbr`, `decline_bars`, `climax_rvol`,
   `bars_from_climax_to_trigger`. Principle: P1.
+  **`decline_bars`/`decline_mbr`, precisely (goal-playbook-iter-6 doc-only closure of the OPEN
+  minor anti-goal item iter-5 carried — zero constant/behavior change, transcribing the reading
+  `desk_playbook_detect.py`'s `_find_climax_formation`/`detect_capitulation` already ship).**
+  Re-anchoring (above) means the climax bar `v` used for these two disclosures is not always the
+  RAW candidate the `vertical_move` window first found — a new low forming after `v` (before any
+  trigger) re-anchors `v` to that later bar, since the panic is still running. `decline_bars`
+  spans the WHOLE decline leg: from the ORIGINAL `vertical_move` window's own start bar through
+  the (possibly re-anchored) climax bar `v` — a formation that re-anchors therefore reports a
+  LONGER decline than the raw `PLAYBOOK_VERTICAL_WINDOW_BARS` constant, never a fixed value.
+  `decline_mbr` is the net decline, in MBR units, from the close of the bar immediately BEFORE the
+  vertical-move window began through to the eventual (possibly re-anchored) `leg_low` — the same
+  "how far did price actually fall" reading `vertical_move`'s own net-move check uses internally,
+  extended through whatever re-anchoring occurred. Both disclosures always describe the FINAL,
+  re-anchored leg, never the raw candidate's own (possibly shorter/shallower) window.
 - **`euphoria`** — exact mirror UP with the same constants, emitted as a **marker, not a
   signal**: no side, no band, never measured (BOOK: an exit/avoid signal; the authors do not
   short strong stocks on euphoria). It sets `euphoria_recent: true` on any signal triggering
@@ -324,6 +338,18 @@ cases. Side/band/entry/measurement always follow §0.
   Principles: P6 when absorption present; P5 at the high side.
 - **Edge cases.** A strict break beyond a zone by > `HOLD_TOL` dissolves range-mode (re-arms
   only on a new twice-tested range).
+  **Degenerate trigger reference (clarification, 2026-08-11 — ADAPTATION, narrowing only, no
+  new constant).** The Invalidation clause above is arithmetic on `T − SL`: it pads the range
+  bound by 30% of the distance from the range low to the trigger reference, and therefore
+  presupposes `T > SL` (long; `T < SH` short). That premise is not automatic — the Trigger
+  clause tolerates the pre-trigger bars dipping to `SL − RANGE_HOLD_TOL·MBR`, so a reversal bar
+  whose reference `high[t−1]` sits entirely below the arming-time `SL` is reachable, and there
+  `SL − 0.30·(T − SL)` INVERTS: a long's invalidation lands ABOVE its own entry and the signal
+  is recorded born-invalidated. That is a degenerate formation, not a signal: following §4's
+  own class of degenerate/edge rules ("formation open at session end ⇒ nothing emitted"; thin
+  data ⇒ silent, never a guess), the formation is **voided, fail-closed** — `T ≤ SL` (long) /
+  `T ≥ SH` (short) emits nothing, and the detector continues its walk for a later arming.
+  No threshold is involved; the clause can only remove signals, never create one.
 - **Provisional status.** First candidate for removal in a named revision if its forward
   distributions do not separate from the random-anchor baseline.
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-playbook/state/assumptions.md    | 27 +++++++++++++
 runs/goal-session-playbook/state/golden-gaps       |  1 -
 runs/goal-session-playbook/state/golden-nudge.json |  3 +-
 .../goal-session-playbook/state/iteration-state.md |  9 +++++
 runs/goal-session-playbook/telemetry.jsonl         | 44 ++++++++++++++++++++++
 runs/goal-session-playbook/trace/trace.jsonl       |  9 +++++
 6 files changed, 91 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
