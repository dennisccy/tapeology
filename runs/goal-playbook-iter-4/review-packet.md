# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 8. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/desk_playbook_detect.py` (107 lines not shown)
- `apps/backend/tests/test_desk_playbook_detect.py` (16 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_playbook.py b/apps/backend/app/research/desk_playbook.py
index 62d8c69..87afe8f 100644
--- a/apps/backend/app/research/desk_playbook.py
+++ b/apps/backend/app/research/desk_playbook.py
@@ -1,4 +1,4 @@
-"""The Playbook (Era B2 "The Playbook", J-01/J-02) -- the book's intraday setups
+"""The Playbook (Era B2 "The Playbook", J-01/J-02/J-04) -- the book's intraday setups
 (Graifer & Schumacher, *Techniques of Tape Reading*, 2004), detected on the desk's own recorded
 5m/1m bars and measured with the desk forward rail's own conventions. This module owns the
 pre-registered constant table, the parameters/signature recipe, the append-only store, and the
@@ -14,11 +14,14 @@ break, a jump-base-explosion, ...) -- a third, unrelated sense of the word. This
 imports from ``setups.py`` or ``backtests.py``, and no field here is ever named ``stop_loss``
 (the field is ``invalidation_price`` -- a disclosed structural level, never an order concept).
 
-**Detection only, this iteration.** ``compute_playbook`` walks the desk universe's members and
-detects the opening-range-break family (spec §3.1-3.2); trigger-anchored measurement (forward
-returns, ``invalidation_breached``, the seeded baseline) is J-02 -- ``entry``/``entry_kind`` are
-computed now (spec §0's stop-through fill convention is part of a signal's own GEOMETRY, decided
-at the trigger bar, not part of measuring what happened afterward).
+**Detection then measurement, in one walk.** ``compute_playbook`` walks the desk universe's
+members and detects, per member, the opening-range-break pair (spec §3.1-3.2, J-01) beside the
+continuation family (``jbe``/``dbi``, spec §3.3-3.4, J-04) and ``cup_handle`` (spec §3.6, J-04),
+gated by the SAME "5m bars + sufficient baseline + a buildable opening range" absence checks J-01
+shipped -- every detected signal is measured in the same pass (forward returns,
+``invalidation_breached``, the seeded baseline, J-02) -- ``entry``/``entry_kind`` are decided at
+detection time (spec §0's stop-through fill convention is part of a signal's own GEOMETRY, not
+part of measuring what happened afterward).
 
 **Parameters discipline (the ``desk_forward.forward_parameters`` pattern, applied at birth).**
 ``playbook_parameters()`` reads every constant below at CALL TIME (so a test monkeypatching one
@@ -60,7 +63,7 @@ from .desk_forward import (
     _draw_anchor_indices,
     _measure_from,
 )
-from .desk_playbook_detect import detect_opening_range_breaks
+from .desk_playbook_detect import detect_cup_handle, detect_dbi, detect_jbe, detect_opening_range_breaks
 from .desk_playbook_features import baselines, opening_range, rth_session_slice, side_sign
 from .desk_sessions import refuse_if_not_a_session
 
@@ -129,12 +132,19 @@ PLAYBOOK_MKT_NEUTRAL_BAND_MBR: float = 1.0  # ADAPTATION -- neutral band, index-
 PLAYBOOK_MARKER_DECAY_BARS: int = 6  # ADAPTATION -- euphoria/capitulation marker decorates 30 min
 PLAYBOOK_APPROACH_BARS: int = 3  # ADAPTATION -- volume-into-trigger window
 PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION: int = 2  # ADAPTATION -- ladder steps
+# J-04: two more prose-only spec thresholds promoted to named constants, the
+# `PLAYBOOK_OR_MIN_1M_BARS` precedent (a value stated in the spec's OWN prose but not originally
+# given its own §1 row) -- both are now tabulated in docs/playbook-detector-spec.md §1 too, flagged
+# in the dev handoff for the same owner ruling on whether the promotion reads right.
+PLAYBOOK_BASE_FLATLINE_MAX_MBR: float = 1.0  # ADAPTATION -- spec §3.3 prose "base range <= 1.0 MBR"
+PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC: float = 0.25  # BOOK -- spec §1's HANDLE_MAX_DURATION_FRAC row: "25% desirable"
 
 # Companion structural constants (shape, not thresholds).
-# This iteration implements ONLY the opening-range-break family; J-04/J-05/J-06 EXTEND this tuple
-# as they land their own detectors (a signature-moving, expected, visible change) -- declaring a
-# setup id here before its detector exists would claim a compute that does not happen.
-PLAYBOOK_SETUPS: tuple[str, ...] = ("open_high_break", "open_low_break")
+# J-01 shipped ONLY the opening-range-break family; J-04 (this iteration) EXTENDS this tuple with
+# the continuation family (jbe/dbi/cup_handle) -- J-05/J-06 will extend it further as they land
+# their own detectors (each extension is a signature-moving, expected, visible change) -- declaring
+# a setup id here before its detector exists would claim a compute that does not happen.
+PLAYBOOK_SETUPS: tuple[str, ...] = ("open_high_break", "open_low_break", "jbe", "dbi", "cup_handle")
 PLAYBOOK_MARKET_SYMBOL: str = "SPY"
 # The rail's own baseline seed, echoed (not re-derived) -- the seed discipline itself is J-02's;
 # embedding the CONSTANT now is what makes a future rail-seed change re-key playbook records too.
@@ -255,6 +265,8 @@ def playbook_parameters() -> dict:
         "marker_decay_bars": PLAYBOOK_MARKER_DECAY_BARS,
         "approach_bars": PLAYBOOK_APPROACH_BARS,
         "max_jbe_signals_per_session": PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION,
+        "base_flatline_max_mbr": PLAYBOOK_BASE_FLATLINE_MAX_MBR,
+        "handle_desirable_duration_frac": PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC,
         # The measurement rail's own shape constants, echoed verbatim (embedded at birth, per the
         # module docstring) -- a FUTURE desk_forward.py change re-keys playbook records instead of
         # silently reinterpreting them, even though J-01 measures nothing itself.
@@ -447,19 +459,25 @@ def compute_playbook(
     progress: Callable[[dict], None] | None = None,
     should_abort: Callable[[], bool] | None = None,
 ) -> dict:
-    """Detect AND measure the opening-range-break family for EVERY member of the latest registered
-    universe snapshot, on ``session_date``'s own recorded bars, in the SAME walk -- returns
-    everything ``PlaybookStore.record`` needs minus the store-assigned ``id``/``recorded_at`` (the
-    ``compute_forward``/``compute_screen`` contract shape: a PURE compute, never itself a store
-    write).
+    """Detect AND measure every registered setup family (opening-range-break, J-01; the
+    continuation family ``jbe``/``dbi`` and ``cup_handle``, J-04) for EVERY member of the latest
+    registered universe snapshot, on ``session_date``'s own recorded bars, in the SAME walk --
+    returns everything ``PlaybookStore.record`` needs minus the store-assigned ``id``/
+    ``recorded_at`` (the ``compute_forward``/``compute_screen`` contract shape: a PURE compute,
+    never itself a store write).
 
     Session-honesty first: ``desk_sessions.refuse_if_not_a_session`` is checked before any bar is
-    read for detection (no separate compute-manager/route layer exists yet this iteration, so this
-    function plays that role) -- a non-session date raises ``PlaybookSessionRefused`` and NOTHING
-    is walked. Per member: no 5m bars for the session, a thin/zero baseline, or no buildable opening
-    range are each a disclosed ``absences`` row (never a crash, never a guess); everything else
-    reaches the detector, which may add a signal, an ``ambiguous_outside_bar`` diagnostic, or
-    neither (a legitimate "the setup did not form" outcome -- not an absence).
+    read for detection -- a non-session date raises ``PlaybookSessionRefused`` and NOTHING is
+    walked. Per member: no 5m bars for the session, a thin/zero baseline, or no buildable opening
+    range are each a disclosed ``absences`` row (never a crash, never a guess) -- ALL FOUR
+    detector families share this one gate (a deliberate J-04 simplification: spec §3.1 scopes "no
+    OR" absence to the OR-break family alone, but sharing the gate keeps J-01/J-02's own absence
+    contract byte-unchanged, at the cost of also skipping jbe/dbi/cup_handle on the rare session
+    with 5m coverage but no buildable opening range -- see the dev handoff). Everything else
+    reaches the detectors, each of which may add zero, one, or (jbe/dbi's own ladder) up to
+    ``PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION`` signals, plus (OR-break only) an
+    ``ambiguous_outside_bar`` diagnostic -- a formation that never forms or never triggers is a
+    legitimate "the setup did not form" outcome, not an absence.
 
     J-02: every detected signal is measured in the SAME pass -- ``_measure_signal`` attaches
     ``forward`` (the rail's own ``_measure_from`` shape, anchored on the finest series THIS
@@ -563,35 +581,57 @@ def compute_playbook(
             session_5m, or_result, baseline, symbol, session_date, index_bars, index_baseline,
             params, _prior_session_close(bars_5m, session_date),
         )
-        if signal is not None:
+        # J-04: the continuation family (jbe/dbi, each up to a 2-step ladder) and cup_handle (at
+        # most 1) detect on the SAME `session_5m`/baseline this symbol already resolved for the
+        # OR-break pair -- they run beside it, gated by the SAME "a valid opening range exists"
+        # branch (a deliberate, documented simplification: spec §3.1's "no OR" absence is scoped
+        # to the OR-break family alone, but sharing the gate here keeps the absence contract
+        # exactly as J-01/J-02 shipped it -- zero risk to their own behavior; see the dev handoff).
+        detected_signals: list[dict] = [signal] if signal is not None else []
+        detected_signals.extend(
+            detect_jbe(session_5m, baseline, symbol, session_date, index_bars, index_baseline, params)
+        )
+        detected_signals.extend(
+            detect_dbi(session_5m, baseline, symbol, session_date, index_bars, index_baseline, params)
+        )
+        cup_signal = detect_cup_handle(
+            session_5m, baseline, symbol, session_date, index_bars, index_baseline, params
+        )
+        if cup_signal is not None:
+            detected_signals.append(cup_signal)
+
+        if detected_signals:
             session_1m = rth_session_slice(bars_1m, session_date)
-            forward, breached, measure_bars, tf_minutes = _measure_signal(signal, session_5m, session_1m)
-            signal["forward"] = forward
-            signal["invalidation_breached"] = breached
-            signals.append(signal)
-
-            pool_key = f"{signal['setup_id']}:{signal['side']}"
-            count_so_far = pool_counts.get(pool_key, 0)
-            pool_counts[pool_key] = count_so_far + 1
-            if count_so_far < DESK_FORWARD_MAX_TOUCHES_PER_ROW:
-                signal_pool.setdefault(pool_key, []).append(forward)
-                sign = side_sign(signal["side"])
-                firing_key = f"{symbol}:{signal['setup_id']}"
-                firing_index = firing_counts.get(firing_key, 0)
-                firing_counts[firing_key] = firing_index + 1
-                rng = random.Random(
-                    _baseline_seed(session_date, symbol, signal["setup_id"], firing_index)
+            for signal in detected_signals:
+                forward, breached, measure_bars, tf_minutes = _measure_signal(
+                    signal, session_5m, session_1m
                 )
-                k = min(1, len(measure_bars))  # this symbol's own capped signal count is <= 1
-                for anchor_idx in _draw_anchor_indices(rng, len(measure_bars), k):
-                    anchor_bar = measure_bars[anchor_idx]
-                    baseline_pool.setdefault(pool_key, []).append(
-                        _measure_from(
-                            measure_bars, anchor_idx, anchor_bar.close, "close", tf_minutes, sign
-                        )
+                signal["forward"] = forward
+                signal["invalidation_breached"] = breached
+                signals.append(signal)
+
+                pool_key = f"{signal['setup_id']}:{signal['side']}"
+                count_so_far = pool_counts.get(pool_key, 0)
+                pool_counts[pool_key] = count_so_far + 1
+                if count_so_far < DESK_FORWARD_MAX_TOUCHES_PER_ROW:
+                    signal_pool.setdefault(pool_key, []).append(forward)
+                    sign = side_sign(signal["side"])
+                    firing_key = f"{symbol}:{signal['setup_id']}"
+                    firing_index = firing_counts.get(firing_key, 0)
+                    firing_counts[firing_key] = firing_index + 1
+                    rng = random.Random(
+                        _baseline_seed(session_date, symbol, signal["setup_id"], firing_index)
                     )
-            else:
-                pool_beyond_cap[pool_key] = pool_beyond_cap.get(pool_key, 0) + 1
+                    k = min(1, len(measure_bars))  # every signal draws exactly one baseline anchor
+                    for anchor_idx in _draw_anchor_indices(rng, len(measure_bars), k):
+                        anchor_bar = measure_bars[anchor_idx]
+                        baseline_pool.setdefault(pool_key, []).append(
+                            _measure_from(
+                                measure_bars, anchor_idx, anchor_bar.close, "close", tf_minutes, sign
+                            )
+                        )
+                else:
+                    pool_beyond_cap[pool_key] = pool_beyond_cap.get(pool_key, 0) + 1
         if diagnostic is not None:
             diagnostics.append(diagnostic)
         if progress is not None:
diff --git a/apps/backend/app/research/desk_playbook_detect.py b/apps/backend/app/research/desk_playbook_detect.py
index 178d453..93696f7 100644
--- a/apps/backend/app/research/desk_playbook_detect.py
+++ b/apps/backend/app/research/desk_playbook_detect.py
@@ -1,7 +1,15 @@
-"""The Playbook's detectors (Era B2, J-01: the opening-range-break family only --
-``docs/playbook-detector-spec.md`` §3.1-3.2). J-04/J-05/J-06 add the remaining seven detectors
-here, each built purely out of ``desk_playbook_features.py``'s eight primitives plus the
-``playbook_parameters()`` dict a caller hands in.
+"""The Playbook's detectors (Era B2). J-01 shipped the opening-range-break family
+(``docs/playbook-detector-spec.md`` §3.1-3.2); J-04 (this iteration) adds the continuation family
+-- ``detect_jbe``/``detect_dbi`` (§3.3-3.4, one shared internal walk, direction-flipped) and
+``detect_cup_handle`` (§3.6). J-05/J-06 add the remaining four detectors here, each built purely
+out of ``desk_playbook_features.py``'s eight primitives plus the ``playbook_parameters()`` dict a
+caller hands in.
+
+**J-04's own primitives are all reused, none added.** ``consolidation_range`` (JBE/DBI's base,
+shared with the module's own precedent of "shared geometry for JBE/DBI's base and cup-and-handle's
+handle") and ``swing_pivots`` (cup-and-handle's rims) both already exist in
+``desk_playbook_features.py`` from J-01/J-02 -- this iteration imports them, it does not extend
+that file (expected zero diff, per the goal's own Constraints).
 
 **A THIRD "setup" vocabulary -- never conflate.** ``setups.py`` (the tick-touch scanner) and
 ``backtests.py`` (tape-arming occurrences) already use "setup" for two OTHER things; a playbook
@@ -28,18 +36,26 @@ for any bar strictly after the trigger."""
 
 from __future__ import annotations
 
+import statistics
 from datetime import datetime, timezone
 
 from ..providers.adapters.base import RawBar
 from .desk_playbook_features import (
+    consolidation_range,
     market_context,
     rth_session_slice,
     side_sign,
+    swing_pivots,
     vertical_move,
     zone_touches,
 )
 
-__all__ = ["detect_opening_range_breaks"]
+__all__ = [
+    "detect_opening_range_breaks",
+    "detect_jbe",
+    "detect_dbi",
+    "detect_cup_handle",
+]
 
 
 def _iso(epoch: float) -> str:
@@ -324,3 +340,454 @@ def detect_opening_range_breaks(
         },
     }
     return signal, None
+
+
+# --- J-04: the continuation family -- jbe (spec §3.3) / dbi (spec §3.4, the exact mirror) ---------
+#
+# ONE shared internal walk (``_find_one_continuation``), direction-parameterized by ``side`` --
+# spec §3.4 states dbi IS jbe "exact mirror... same primitives, gates, and cap, direction-flipped",
+# so a second, hand-flipped copy would be the second-implementation drift the whole codebase is
+# built to avoid (the module's own ``side_sign``/``_market_block`` precedent). ``detect_jbe``/
+# ``detect_dbi`` are the two thin, setup-id-naming callers a test or ``compute_playbook`` actually
+# imports.
+
+
+def _base_lows_ascending(base_bars: list[RawBar], side: str) -> bool:
+    """The ADAPTATION "ascending-triangle" base-shape disclosure (spec §3.3): for a long base
+    (jbe), are the LOWS non-decreasing bar to bar; for a short base (dbi, the mirror), are the
+    HIGHS non-increasing -- one served field name (``base_lows_ascending``, per the goal's own
+    Data-contract table), the direction-appropriate triangle check underneath."""
+    if len(base_bars) < 2:
+        return True
+    if side == "long":
+        return all(base_bars[i].low >= base_bars[i - 1].low for i in range(1, len(base_bars)))
+    return all(base_bars[i].high <= base_bars[i - 1].high for i in range(1, len(base_bars)))
+
+
+def _find_one_continuation(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+    side: str,
+    setup_id: str,
+    min_base_start: int,
+    previous_jump_mbr: float | None,
+) -> dict | None:
+    """ONE ladder step: the first bar-by-bar-rolling ``(base, jump, trigger)`` formation found at
+    or after ``min_base_start`` (the caller's own "a second base must start after the first
+    trigger bar" cap discipline) -- ``None`` if no such formation ever forms and triggers before
+    session close (spec §3.3 edge case: "a base still open at session close emits nothing").
+
+    The base itself is RECOMPUTED at every candidate trigger bar ``t`` via
+    ``consolidation_range(session_bars, t - 1, ...)`` -- the shared primitive's own "maximal
+    window ending at ``end_idx``" contract rolls the base forward bar by bar exactly like the OR
+    break's fixed-opening-range trigger scan rolls its OWN search forward, just over a dynamic
+    (not session-fixed) base. Reusing the jump's own ``PLAYBOOK_JUMP_MIN_MOVE_MBR`` floor as an
+    (undocumented but structural) safety net: any window wide enough to swallow part of the jump
+    leg fails ``consolidation_range``'s own ``max_range`` gate before this function ever sees it,
+    so the maximal-window search naturally lands on the tight base, never the jump-plus-base
+    blend, without this function needing a second range check of its own."""
+    mbr = baseline["mbr"]
+    slot_medians = baseline["slot_volume_medians"]
+    lookback = params["jump_lookback_bars"]
+    min_bars = params["base_min_bars"]
+    max_bars = params["base_max_bars"]
+    max_range = params["base_max_range_mbr"] * mbr
+    n = len(session_bars)
+
+    for t in range(min_bars, n):
+        base = consolidation_range(session_bars, t - 1, min_bars, max_bars, max_range)
+        if base is None:
+            continue
+        start_idx, u, l = base
+        if start_idx < min_base_start or start_idx - lookback < 0:
+            continue
+
+        base_range = u - l
+        lookback_bars = session_bars[start_idx - lookback : start_idx]
+        if side == "long":
+            jump = u - min(bar.low for bar in lookback_bars)
+        else:
+            jump = max(bar.high for bar in lookback_bars) - l
+        if jump < params["jump_min_mult"] * base_range or jump < params["jump_min_move_mbr"] * mbr:
+            continue
+
+        prior_bars = session_bars[:t]
+        if side == "long":
+            near_extreme_ok = u >= max(bar.high for bar in prior_bars) - params["near_extreme_mbr"] * mbr
+        else:
+            near_extreme_ok = l <= min(bar.low for bar in prior_bars) + params["near_extreme_mbr"] * mbr
+        if not near_extreme_ok:
+            continue
+
+        base_bars = session_bars[start_idx:t]
+        jump_rvols = [
+            _rvol(bar, idx, slot_medians)
+            for idx, bar in enumerate(lookback_bars, start=start_idx - lookback)
+        ]
+        known_jump_rvols = [r for r in jump_rvols if r is not None]
+        if not known_jump_rvols:
+            continue
+        median_jump_rvol = statistics.median(known_jump_rvols)
+        if median_jump_rvol < 1.0 or max(known_jump_rvols) < params["rvol_elevated"]:
+            continue
+
+        base_rvols = [_rvol(bar, idx, slot_medians) for idx, bar in enumerate(base_bars, start=start_idx)]
+        known_base_rvols = [r for r in base_rvols if r is not None]
+        if not known_base_rvols:
+            continue
+        if statistics.median(known_base_rvols) > params["vol_contrast_ratio"] * median_jump_rvol:
+            continue
+
+        bar_t = session_bars[t]
+        triggers = bar_t.high > u if side == "long" else bar_t.low < l
+        if not triggers:
+            continue
+
+        # --- formation armed AND triggered at t -- build the signal -----------------------------
+        trigger_price = u if side == "long" else l
+        if side == "long":
+            entry = max(bar_t.open, trigger_price)
+            entry_kind = "level" if bar_t.open < trigger_price else "gap_open"
+            gapped_beyond_chase = bar_t.open > trigger_price * (1.0 + params["max_chase_frac"])
+            invalidation_price = l - params["stop_pad_frac"] * base_range
+        else:
+            entry = min(bar_t.open, trigger_price)
+            entry_kind = "level" if bar_t.open > trigger_price else "gap_open"
+            gapped_beyond_chase = bar_t.open < trigger_price * (1.0 - params["max_chase_frac"])
+            invalidation_price = u + params["stop_pad_frac"] * base_range
+
+        jump_mbr = jump / mbr
+        ladder_step_ratio = jump_mbr / previous_jump_mbr if previous_jump_mbr else None
+
+        approach_start = max(0, t - params["approach_bars"])
+        approach_indices = list(range(approach_start, t))
+        approach_rvols = [_rvol(session_bars[i], i, slot_medians) for i in approach_indices]
+        known_approach = [r for r in approach_rvols if r is not None]
+        approach_rvol_max = max(known_approach) if known_approach else None
+        rvol_trigger_bar = _rvol(bar_t, t, slot_medians)
+        spike_verdict = _spike_into_trigger_verdict(
+            session_bars, approach_indices, approach_rvols, trigger_price, side, mbr,
+            params["rvol_surge"], params["near_extreme_mbr"],
+        )
+        spiky_approach = False
+        if t - 1 >= 0:
+            spiky_approach = vertical_move(
+                session_bars, t - 1, 1, params["vertical_bar_mbr"] * mbr,
+                "up" if side == "long" else "down",
+            )
+        if side == "long":
+            zone_lo, zone_hi = trigger_price - params["near_extreme_mbr"] * mbr, trigger_price
+        else:
+            zone_lo, zone_hi = trigger_price, trigger_price + params["near_extreme_mbr"] * mbr
+        attempt_count = len(zone_touches(session_bars[:t], zone_lo, zone_hi))
+        market = _market_block(
+            session_bars, t, index_bars, session_date, side, mbr, index_baseline, params,
+        )
+
+        return {
+            "symbol": symbol,
+            "setup_id": setup_id,
+            "side": side,
+            "trigger_ts": _iso(bar_t.epoch),
+            "trigger_price": trigger_price,
+            "entry": entry,
+            "entry_kind": entry_kind,
+            "price_low": l,
+            "price_high": u,
+            "invalidation_price": invalidation_price,
+            "geometry": {
+                "slots_to_break": t,
+                "jump_mbr": jump_mbr,
+                "base_range_mbr": base_range / mbr,
+                "base_bars": t - start_idx,
+                "base_flatline": (base_range / mbr) <= params["base_flatline_max_mbr"],
+                "base_lows_ascending": _base_lows_ascending(base_bars, side),
+                "ladder_step_ratio": ladder_step_ratio,
+            },
+            "volume": {
+                "rvol_trigger_bar": rvol_trigger_bar,
+                "approach_rvol_max": approach_rvol_max,
+                "spike_into_trigger_verdict": spike_verdict,
+                "spiky_approach": spiky_approach,
+            },
+            "market": market,
+            "principles": ["P3", "P4"],
+            "disclosures": {
+                "gapped_beyond_chase": gapped_beyond_chase,
+                "session_bar_count": len(session_bars),
+                "attempt_count": attempt_count,
+                "bars_to_close": len(session_bars) - 1 - t,
+                "concurrent_signals": [],
+                "euphoria_recent": False,
+                "capitulation_recent": False,
+            },
+        }
+    return None
+
+
+def _continuation_signals(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+    side: str,
+    setup_id: str,
+) -> list[dict]:
+    """Every ladder step of ONE continuation setup for this symbol-session, chronological order --
+    up to ``PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION`` (spec §3.3: "every other detector caps at 1 --
+    JBE/DBI's own cap is the ladder exception, shared by name with DBI since it is jbe's mirror,
+    not a second cap). Each step's own search starts strictly after the PRIOR step's trigger bar
+    (``min_base_start``) -- the exact ladder-cap mechanism this iteration is the first to actually
+    exercise (see ``desk_playbook._baseline_seed``'s own ``firing_index`` discriminator, built
+    ahead of need in J-03)."""
+    if baseline["mbr"] == 0.0:
+        return []
+    signals: list[dict] = []
+    min_base_start = 0
+    previous_jump_mbr: float | None = None
+    for _ in range(params["max_jbe_signals_per_session"]):
+        found = _find_one_continuation(
+            session_bars, baseline, symbol, session_date, index_bars, index_baseline, params,
+            side, setup_id, min_base_start, previous_jump_mbr,
+        )
+        if found is None:
+            break
+        signals.append(found)
+        min_base_start = found["geometry"]["slots_to_break"] + 1
+        previous_jump_mbr = found["geometry"]["jump_mbr"]
+    return signals
+
+
+def detect_jbe(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+) -> list[dict]:
+    """spec §3.3 -- jump-base-explosion, long only. Up to
+    ``PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION`` ladder-step signals, chronological order (never a
+    diagnostic -- a formation that never forms or never triggers is a legitimate "did not form"
+    outcome, exactly like the OR-break pair's own ``(None, None)`` case)."""
+    return _continuation_signals(
+        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params,
+        "long", "jbe",
+    )
+
+
+def detect_dbi(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+) -> list[dict]:
+    """spec §3.4 -- drop-base-implosion, short only, the exact direction-flipped mirror of
+    ``detect_jbe`` (same shared ``_continuation_signals`` walk, ``side="short"``)."""
+    return _continuation_signals(
+        session_bars, baseline, symbol, session_date, index_bars, index_baseline, params,
+        "short", "dbi",
+    )
+
+
+# --- J-04: cup_handle (spec §3.6, long only in v1) -------------------------------------------------
+
+
+def detect_cup_handle(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+) -> dict | None:
+    """spec §3.6 -- left/right rims via confirmed swing-high pivots, a cup between them, a handle
+    after the right rim, trigger on the rim break. Searches every ``(left_rim, right_rim)`` pivot
+    pair in chronological order and returns the FIRST one whose full formation (cup depth/duration/
+    volume, handle retrace/duration/volume) validates AND triggers -- capped at 1 per
+    symbol-session by construction (this function returns at most one signal, never a list).
+
+    A handle retracing beyond ``PLAYBOOK_HANDLE_MAX_RETRACE_FRAC`` of cup depth, or one that runs
+    longer than ``PLAYBOOK_HANDLE_MAX_DURATION_FRAC`` of the cup's own duration, voids ONLY this
+    rim pair (spec §3.6 edge case: "voids the formation silently... may still fire as an
+    independent hypothesis" under a different detector, or under a LATER rim pair here) -- it does
+    not re-check a later bar for the SAME pair once the rim has already broken, since the breakout
+    already happened and failed the gate at that exact bar.
+
+    **Lookahead law, made concrete for a pivot-based detector.** ``swing_pivots`` runs once over
+    the WHOLE ``session_bars`` it is handed, but a pivot's OWN price/index/``confirmed_at`` are a
+    function only of its fixed local +/-lookback window -- truncating the array anywhere at or
+    after a pivot's ``confirmed_at`` leaves that pivot unchanged (the property the generic
+    truncation test proves). What this function must not do is USE a rim whose ``confirmed_at``
+    falls ON OR AFTER the trigger bar -- spec §3.6: "Both rims pivot-confirmed strictly before
+    ``t``". The trigger scan below therefore starts no earlier than
+    ``right["confirmed_at"] + 1``, never merely ``handle_start + 1``."""
+    mbr = baseline["mbr"]
+    if mbr == 0.0:
+        return None
+    slot_medians = baseline["slot_volume_medians"]
+    pivots = swing_pivots(session_bars, params["pivot_lookback_bars"])
+    highs = sorted((p for p in pivots if p["kind"] == "high"), key=lambda p: p["index"])
+    n = len(session_bars)
+
+    for left_i, left in enumerate(highs):
+        for right in highs[left_i + 1 :]:
+            cup_bars_span = right["index"] - left["index"]
+            if cup_bars_span < params["cup_min_bars"]:
+                continue
+            if abs(right["price"] - left["price"]) > params["rim_match_mbr"] * mbr:
+                continue
+            left_session_high = max(bar.high for bar in session_bars[: left["confirmed_at"] + 1])
+            if left["price"] < left_session_high - params["near_extreme_mbr"] * mbr:
+                continue
+            right_session_high = max(bar.high for bar in session_bars[: right["confirmed_at"] + 1])
+            if right["price"] < right_session_high - params["near_extreme_mbr"] * mbr:
+                continue
+
+            cup_window = session_bars[left["index"] + 1 : right["index"]]
+            if not cup_window:
+                continue
+            cup_bottom_low = min(bar.low for bar in cup_window)
+            depth = left["price"] - cup_bottom_low
+            if depth < params["min_structure_depth_mbr"] * mbr:
+                continue
+
+            cup_bars_all = session_bars[left["index"] : right["index"] + 1]
+            third = max(1, len(cup_bars_all) // 3)
+            first_third, last_third = cup_bars_all[:third], cup_bars_all[-third:]
+            middle_third = cup_bars_all[third : len(cup_bars_all) - third]
+            if not middle_third:
+                continue
+            first_rvols = [
+                _rvol(bar, left["index"] + i, slot_medians) for i, bar in enumerate(first_third)
+            ]
+            last_start = right["index"] - third + 1
+            last_rvols = [_rvol(bar, last_start + i, slot_medians) for i, bar in enumerate(last_third)]
+            middle_start = left["index"] + third
+            middle_rvols = [
+                _rvol(bar, middle_start + i, slot_medians) for i, bar in enumerate(middle_third)
+            ]
+            known_outer = [r for r in first_rvols + last_rvols if r is not None]
+            known_middle = [r for r in middle_rvols if r is not None]
+            if not known_outer or not known_middle:
+                continue
... [diff_bound] apps/backend/app/research/desk_playbook_detect.py: 107 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_playbook.py b/apps/backend/tests/test_desk_playbook.py
index 2c4de3d..fdd9a0e 100644
--- a/apps/backend/tests/test_desk_playbook.py
+++ b/apps/backend/tests/test_desk_playbook.py
@@ -896,3 +896,137 @@ def test_compute_playbook_progress_and_should_abort_wiring(tmp_path, bar_store,
         should_abort=lambda: True,
     )
     assert aborted["signals"] == [] and aborted["absences"] == []
+
+
+# === goal-playbook-iter-4 (J-04): the continuation family wired into the real compute walk ========
+
+
+def _plant_ladder_baseline_sessions(bar_store: BarStore, symbol: str) -> None:
+    """10 prior RTH 5m sessions, 22 bars each (matching the ladder fixture's OWN session length --
+    ``_plant_baseline_sessions``'s shared 6-bar-per-day helper would leave ``slot_volume_medians``
+    covering only slots 0-5, starving every base/trigger bar at slot >= 6 of an RVOL -- every
+    continuation-family volume gate is fail-closed on a missing median, so this iteration needs its
+    own, longer baseline planter rather than widening the shared one every other playbook test
+    already depends on)."""
+    bars = []
+    for day in _BASELINE_DATES:
+        day_open = E_OPEN - (22 - int(day[-2:])) * 86_400.0
+        for slot in range(22):
+            bars.append(_bar(symbol, "5m", day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
+    _plant(bar_store, symbol, "5m", bars)
+
+
+def _plant_ladder_jbe_session(bar_store: BarStore, symbol: str) -> None:
+    """A real ``BarStore``-backed session where the SAME ``(symbol, "jbe")`` pair fires TWICE --
+    the ``test_desk_playbook_detect.py`` ladder fixture, planted as 5m bars only (the opening
+    range degrades to its own 5m basis, honestly, per the shared absence gate this iteration's
+    continuation detectors ride on -- see ``compute_playbook``'s own docstring)."""
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN, 98.4, 98.5, 98.0, 98.3, 1200),
+        _bar(symbol, "5m", E_OPEN + 300.0, 98.3, 98.4, 98.1, 98.3, 1200),
+        _bar(symbol, "5m", E_OPEN + 600.0, 98.3, 98.4, 98.05, 98.3, 1200),
+        _bar(symbol, "5m", E_OPEN + 900.0, 98.3, 98.45, 98.2, 98.3, 1200),
+        _bar(symbol, "5m", E_OPEN + 1200.0, 98.3, 98.4, 98.15, 98.3, 1200),
+        _bar(symbol, "5m", E_OPEN + 1500.0, 98.3, 98.5, 98.3, 98.4, 3000),
+        _bar(symbol, "5m", E_OPEN + 1800.0, 103.5, 103.8, 103.2, 103.6, 400),
+        _bar(symbol, "5m", E_OPEN + 2100.0, 103.6, 104.0, 103.3, 103.7, 500),
+        _bar(symbol, "5m", E_OPEN + 2400.0, 103.7, 103.9, 103.4, 103.8, 450),
+        _bar(symbol, "5m", E_OPEN + 2700.0, 103.9, 104.8, 103.8, 104.5, 1500),  # step 1 trigger
+        _bar(symbol, "5m", E_OPEN + 3000.0, 104.5, 104.6, 104.3, 104.4, 1200),
+        _bar(symbol, "5m", E_OPEN + 3300.0, 104.4, 104.5, 104.2, 104.3, 1200),
+        _bar(symbol, "5m", E_OPEN + 3600.0, 104.3, 104.4, 104.1, 104.2, 1200),
+        _bar(symbol, "5m", E_OPEN + 3900.0, 104.2, 104.3, 104.0, 104.1, 1200),
+        _bar(symbol, "5m", E_OPEN + 4200.0, 104.1, 104.2, 103.9, 104.0, 1200),
+        _bar(symbol, "5m", E_OPEN + 4500.0, 104.0, 104.3, 103.9, 104.2, 3000),
+        _bar(symbol, "5m", E_OPEN + 4800.0, 107.5, 107.8, 107.2, 107.6, 400),
+        _bar(symbol, "5m", E_OPEN + 5100.0, 107.6, 108.0, 107.3, 107.7, 500),
+        _bar(symbol, "5m", E_OPEN + 5400.0, 107.7, 107.9, 107.4, 107.8, 450),
+        _bar(symbol, "5m", E_OPEN + 5700.0, 107.9, 108.8, 107.8, 108.5, 1500),  # step 2 trigger
+        _bar(symbol, "5m", E_OPEN + 6000.0, 108.5, 108.7, 108.3, 108.6, 900),
+        _bar(symbol, "5m", E_OPEN + 6300.0, 108.6, 108.8, 108.4, 108.7, 900),
+    ]
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def test_real_two_firing_jbe_fixture_draws_independent_baseline_anchors_via_compute_playbook(
+    tmp_path, bar_store,
+):
+    """TC-8: the FIRST real exercise of the iter-3 seed-collision fix on an actual multi-fire
+    signal (not just the synthetic fixture `test_two_firings_of_the_same_symbol_setup_pair_draw_
+    independent_non_colliding_anchors` already proves the machinery with) -- two `jbe` signals
+    fire for the SAME symbol in one session, and their baseline draws land on different anchor
+    bars because `firing_index` genuinely increments 0 -> 1 across them."""
+    universe_store = _register_universe(tmp_path, ["LADDER"])
+    _plant_ladder_baseline_sessions(bar_store, "LADDER")
+    _plant_ladder_jbe_session(bar_store, "LADDER")
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    jbe_signals = [s for s in result["signals"] if s["setup_id"] == "jbe"]
+    assert len(jbe_signals) == 2
+    assert jbe_signals[0]["geometry"]["slots_to_break"] < jbe_signals[1]["geometry"]["slots_to_break"]
+    assert jbe_signals[0]["geometry"]["ladder_step_ratio"] is None
+    assert jbe_signals[1]["geometry"]["ladder_step_ratio"] is not None
+
+    pool = result["baseline_anchors"]["jbe:long"]
+    assert len(pool) == 2  # both firings' own draws pooled -- neither one silently dropped
+    assert pool[0]["at_utc"] != pool[1]["at_utc"]  # independent, non-colliding anchor bars
+
+    # Determinism: a second, fresh compute over the identical inputs reproduces byte-identically.
+    second = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert second["baseline_anchors"]["jbe:long"] == pool
+
+
+# --- TC-9 / TC-10: the new setups tuple re-keys, it never rewrites -----------------------------
+
+
+def test_j04_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file(
+    tmp_path, bar_store, universe_store, monkeypatch,
+):
+    """Simulates 'a file already recorded under the J-01/J-02/J-03-era, 2-setup parameters' by
+    monkeypatching `PLAYBOOK_SETUPS` down to its pre-J-04 value for ONE recording (the
+    `_record_aaa` fixture's own 6-bar session is too short for `jbe`/`dbi`/`cup_handle` to ever
+    fire regardless of which code computed it -- see `_find_one_continuation`'s own
+    `jump_lookback_bars` floor -- so this monkeypatch isolates exactly the ONE thing this
+    iteration actually changed for an already-recorded file's own inputs: the parameters blob's
+    `setups` list, and therefore the signature).
+
+    TC-9: the pre-J-04 file's own bytes on disk are UNCHANGED by a fresh, post-J-04 compute over
+    the identical inputs. TC-10: that fresh compute mints a genuinely NEW record (new signature,
+    new id) beside the old one -- re-keying, never rewriting -- and the OR-break signal's own
+    CONTENT (not its signature) is unaffected."""
+    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_SETUPS", ("open_high_break", "open_low_break"))
+    pre_j04_store, pre_j04_meta = _record_aaa(tmp_path, bar_store, universe_store)
+    pre_j04_path = pre_j04_store._path(pre_j04_meta["id"])
+    pre_j04_sha = _sha256_file(pre_j04_path)
+    assert pre_j04_meta["parameters"]["setups"] == ["open_high_break", "open_low_break"]
+
+    monkeypatch.undo()  # restore this iteration's real 5-setup PLAYBOOK_SETUPS
+
+    current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert current_result["parameters"]["setups"] == [
+        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle",
+    ]
+    assert current_result["playbook_input_signature"] != pre_j04_meta["playbook_input_signature"]
+
+    current_meta = pre_j04_store.record(**current_result)
+    assert current_meta["id"] != pre_j04_meta["id"]
+
+    # TC-9: the pre-J-04 file is byte-identical, untouched by the second, differently-keyed write.
+    assert _sha256_file(pre_j04_path) == pre_j04_sha
+    assert pre_j04_store.get(pre_j04_meta["id"]) == pre_j04_meta
+
+    # TC-10: both versions are now recorded for this date; newest is the current-code one.
+    newest, versions = pre_j04_store.newest_for_date(SESSION_DATE)
+    assert versions == 2
+    assert newest["id"] == current_meta["id"]
+
+    # The OR-break signal's own CONTENT is unaffected by the new setups tuple joining the
+    # parameters blob -- zero behavior change to the family J-01/J-02/J-03 already shipped.
+    pre_j04_or_signals = [
+        s for s in pre_j04_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
+    ]
+    current_or_signals = [
+        s for s in current_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
+    ]
+    assert pre_j04_or_signals == current_or_signals
diff --git a/apps/backend/tests/test_desk_playbook_detect.py b/apps/backend/tests/test_desk_playbook_detect.py
index ca6c9e3..d99e850 100644
--- a/apps/backend/tests/test_desk_playbook_detect.py
+++ b/apps/backend/tests/test_desk_playbook_detect.py
@@ -5,11 +5,24 @@ both-sides ambiguous outside bar (TC-5), and the generic lookahead property test
 so J-04/J-05/J-06 extend ``_LOOKAHEAD_FIXTURES`` with their own detectors' fixtures without
 touching the property test's own body.
 
-``detect_opening_range_breaks`` is tested directly as a pure function of bars + a hand-built
-``or_result``/``baseline`` dict -- ``desk_playbook_features.py``'s primitives that would normally
-produce those dicts are already covered by ``test_desk_playbook_features.py``; this file is
-detector logic only. ``test_desk_playbook.py`` separately proves the full bar-store-backed walk
-(``compute_playbook``) wires the primitives into the detector correctly."""
+**J-04 addendum.** ``detect_jbe``/``detect_dbi`` (spec §3.3-3.4) and ``detect_cup_handle`` (spec
+§3.6) take a DIFFERENT call signature than ``detect_opening_range_breaks`` (no ``or_result``, no
+``prior_close`` -- neither setup reads the opening range) -- extending the literal
+``_LOOKAHEAD_FIXTURES`` list/test body below (which is hard-wired to
+``detect_opening_range_breaks``'s own signature) would mean either a lossy tuple shape or touching
+that test's own body, and TC-11/T-11 require the OR-break family's own tests to stay
+byte-unmodified. This file instead adds a SECOND, otherwise-identical two-assertion harness
+(``_CONTINUATION_LOOKAHEAD_FIXTURES`` for jbe/dbi, plus one direct pair of truncate/mutate tests
+for ``cup_handle``) proving the SAME truncation-invariance + mutation-invariance property TC-6/TC-7
+require, for every new detector's own canonical fixture -- the OR-break harness above is not
+touched.
+
+``detect_opening_range_breaks``/``detect_jbe``/``detect_dbi``/``detect_cup_handle`` are all tested
+directly as pure functions of bars + hand-built ``baseline``/``index_baseline`` dicts --
+``desk_playbook_features.py``'s primitives that would normally produce those dicts are already
+covered by ``test_desk_playbook_features.py``; this file is detector logic only.
+``test_desk_playbook.py`` separately proves the full bar-store-backed walk (``compute_playbook``)
+wires the primitives into every detector correctly."""
 
 from __future__ import annotations
 
@@ -19,7 +32,12 @@ import pytest
 
 from app.providers.adapters.base import RawBar
 from app.research.desk_playbook import playbook_parameters
-from app.research.desk_playbook_detect import detect_opening_range_breaks
+from app.research.desk_playbook_detect import (
+    detect_cup_handle,
+    detect_dbi,
+    detect_jbe,
+    detect_opening_range_breaks,
+)
 
 SESSION_DATE = "2026-06-22"
 E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET
@@ -342,3 +360,367 @@ def test_mutating_a_bar_after_the_trigger_changes_nothing(
     )
     assert mutated_diagnostic is None
     assert mutated_signal == original_signal
+
+
+# === J-04: the continuation family -- jbe (TC-1, TC-4) / dbi (TC-2, TC-5) =========================
+#
+# A tight, hand-computed base+jump: 6 flat lookback bars (slots 0-5, deliberate volume surge on the
+# LAST one) then a 3-bar base (slots 6-8, tight range, dry volume) then a trigger at slot 9. Every
+# earlier candidate trigger bar the detector's own rolling search visits is deliberately unable to
+# find a qualifying (base, jump) pair -- either the base window it finds swallows part of the
+# lookback leg (range too wide) or there aren't yet enough bars before the candidate base start for
+# a full jump-lookback window -- so slot 9 is the unique, deterministic firing point (verified by
+# direct execution, not just by inspection).
+
+_CONTINUATION_BASELINE = {
+    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(12)},
+}
+
+
+def _canonical_jbe_bars(symbol: str = "JBE1") -> list[RawBar]:
+    return [
+        _bar(symbol, E_OPEN, 98.4, 98.5, 98.0, 98.3, 1200),
+        _bar(symbol, E_OPEN + 300.0, 98.3, 98.4, 98.1, 98.3, 1200),
+        _bar(symbol, E_OPEN + 600.0, 98.3, 98.4, 98.05, 98.3, 1200),
+        _bar(symbol, E_OPEN + 900.0, 98.3, 98.45, 98.2, 98.3, 1200),
+        _bar(symbol, E_OPEN + 1200.0, 98.3, 98.4, 98.15, 98.3, 1200),
+        _bar(symbol, E_OPEN + 1500.0, 98.3, 98.5, 98.3, 98.4, 3000),  # lookback volume surge
+        _bar(symbol, E_OPEN + 1800.0, 103.5, 103.8, 103.2, 103.6, 400),  # base bar 1
+        _bar(symbol, E_OPEN + 2100.0, 103.6, 104.0, 103.3, 103.7, 500),  # base bar 2
+        _bar(symbol, E_OPEN + 2400.0, 103.7, 103.9, 103.4, 103.8, 450),  # base bar 3
+        _bar(symbol, E_OPEN + 2700.0, 103.9, 104.8, 103.8, 104.5, 1500),  # trigger: breaks U=104.0
+        _bar(symbol, E_OPEN + 3000.0, 104.5, 104.7, 104.3, 104.6, 900),
+        _bar(symbol, E_OPEN + 3300.0, 104.6, 104.8, 104.4, 104.7, 900),
+    ]
+
+
+def _canonical_dbi_bars(symbol: str = "DBI1") -> list[RawBar]:
+    """The exact mirror of ``_canonical_jbe_bars``: a high lookback, a tight base near a LOWER
+    level, and a trigger breaking DOWN through the base's own low."""
+    return [
+        _bar(symbol, E_OPEN, 109.6, 110.0, 109.5, 109.7, 1200),
+        _bar(symbol, E_OPEN + 300.0, 109.7, 109.9, 109.6, 109.7, 1200),
+        _bar(symbol, E_OPEN + 600.0, 109.7, 109.95, 109.6, 109.7, 1200),
+        _bar(symbol, E_OPEN + 900.0, 109.7, 109.8, 109.55, 109.7, 1200),
+        _bar(symbol, E_OPEN + 1200.0, 109.7, 109.85, 109.6, 109.7, 1200),
+        _bar(symbol, E_OPEN + 1500.0, 109.6, 109.7, 109.5, 109.6, 3000),  # lookback volume surge
+        _bar(symbol, E_OPEN + 1800.0, 104.5, 104.8, 104.2, 104.4, 400),  # base bar 1
+        _bar(symbol, E_OPEN + 2100.0, 104.4, 104.7, 104.0, 104.3, 500),  # base bar 2
+        _bar(symbol, E_OPEN + 2400.0, 104.3, 104.6, 104.1, 104.2, 450),  # base bar 3
+        _bar(symbol, E_OPEN + 2700.0, 104.1, 104.2, 103.2, 103.5, 1500),  # trigger: breaks L=104.0
+        _bar(symbol, E_OPEN + 3000.0, 103.5, 103.7, 103.3, 103.4, 900),
+        _bar(symbol, E_OPEN + 3300.0, 103.4, 103.6, 103.2, 103.3, 900),
+    ]
+
+
+def test_canonical_jbe_matches_the_hand_computed_signal():
+    """TC-1: the canonical JBE firing -- setup chip, side, and every geometry field hand-verified
+    (values confirmed by direct execution against the fixture, per the module-level note above)."""
+    results = detect_jbe(
+        _canonical_jbe_bars(), _CONTINUATION_BASELINE, "JBE1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(results) == 1
+    signal = results[0]
+    assert signal["setup_id"] == "jbe"
+    assert signal["side"] == "long"
+    assert signal["trigger_price"] == 104.0
+    assert signal["entry"] == 104.0
+    assert signal["entry_kind"] == "level"
+    assert signal["price_low"] == pytest.approx(103.2)
+    assert signal["price_high"] == 104.0
+    assert signal["invalidation_price"] == pytest.approx(102.96)
+    geometry = signal["geometry"]
+    assert geometry["slots_to_break"] == 9
+    assert geometry["jump_mbr"] == pytest.approx(6.0)
+    assert geometry["base_range_mbr"] == pytest.approx(0.8)
+    assert geometry["base_bars"] == 3
+    assert geometry["base_flatline"] is True
+    assert geometry["base_lows_ascending"] is True
+    assert geometry["ladder_step_ratio"] is None
+    assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(1.5)
+    assert signal["principles"] == ["P3", "P4"]
+    assert signal["disclosures"]["bars_to_close"] == 2
+    assert signal["disclosures"]["concurrent_signals"] == []
+
+
+def test_canonical_dbi_mirrors_the_jbe_fixture():
+    """TC-2: the exact mirror -- short side, invalidation ABOVE the base, geometry magnitudes
+    identical to the JBE canonical (same shape, direction-flipped)."""
+    results = detect_dbi(
+        _canonical_dbi_bars(), _CONTINUATION_BASELINE, "DBI1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(results) == 1
+    signal = results[0]
+    assert signal["setup_id"] == "dbi"
+    assert signal["side"] == "short"
+    assert signal["trigger_price"] == 104.0
+    assert signal["entry"] == 104.0
+    assert signal["entry_kind"] == "level"
+    assert signal["invalidation_price"] == pytest.approx(105.04)
+    geometry = signal["geometry"]
+    assert geometry["slots_to_break"] == 9
+    assert geometry["jump_mbr"] == pytest.approx(6.0)
+    assert geometry["base_range_mbr"] == pytest.approx(0.8)
+    assert geometry["base_bars"] == 3
+    assert geometry["base_flatline"] is True
+    assert geometry["base_lows_ascending"] is True  # mirrored meaning: base HIGHS non-increasing
+    assert geometry["ladder_step_ratio"] is None
+    assert signal["principles"] == ["P3", "P4"]
+
+
+def test_jbe_near_miss_jump_too_small_fires_no_signal():
+    """TC-4: the SAME base/trigger shape, but the lookback window sits close enough to the base
+    that the jump fails BOTH the ``jump_min_mult`` and ``jump_min_move_mbr`` gates."""
+    bars = [
+        _bar("JBENM", E_OPEN, 98.9, 99.0, 98.5, 98.8, 1200),
+        _bar("JBENM", E_OPEN + 300.0, 98.8, 98.9, 98.6, 98.8, 1200),
+        _bar("JBENM", E_OPEN + 600.0, 98.8, 98.9, 98.55, 98.8, 1200),
+        _bar("JBENM", E_OPEN + 900.0, 98.8, 98.95, 98.7, 98.8, 1200),
+        _bar("JBENM", E_OPEN + 1200.0, 98.8, 98.9, 98.65, 98.8, 1200),
+        _bar("JBENM", E_OPEN + 1500.0, 98.8, 99.0, 98.8, 98.9, 3000),
+        _bar("JBENM", E_OPEN + 1800.0, 99.5, 99.8, 99.2, 99.6, 400),
+        _bar("JBENM", E_OPEN + 2100.0, 99.6, 100.0, 99.3, 99.7, 500),
+        _bar("JBENM", E_OPEN + 2400.0, 99.7, 99.9, 99.4, 99.8, 450),
+        _bar("JBENM", E_OPEN + 2700.0, 99.9, 100.8, 99.8, 100.5, 1500),  # would break 100.0
+        _bar("JBENM", E_OPEN + 3000.0, 100.5, 100.7, 100.3, 100.6, 900),
+        _bar("JBENM", E_OPEN + 3300.0, 100.6, 100.8, 100.4, 100.7, 900),
+    ]
+    results = detect_jbe(
+        bars, _CONTINUATION_BASELINE, "JBENM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert results == []
+
+
+def test_dbi_near_miss_mirrors_the_jbe_near_miss():
+    """TC-5: the mirrored gate failure -- jump too small on the short side."""
+    bars = [
+        _bar("DBINM", E_OPEN, 100.6, 100.9, 100.5, 100.7, 1200),
+        _bar("DBINM", E_OPEN + 300.0, 100.7, 100.9, 100.55, 100.7, 1200),
+        _bar("DBINM", E_OPEN + 600.0, 100.7, 100.85, 100.6, 100.7, 1200),
+        _bar("DBINM", E_OPEN + 900.0, 100.7, 100.9, 100.6, 100.7, 1200),
+        _bar("DBINM", E_OPEN + 1200.0, 100.7, 100.85, 100.6, 100.7, 1200),
+        _bar("DBINM", E_OPEN + 1500.0, 100.6, 100.7, 100.5, 100.6, 3000),
+        _bar("DBINM", E_OPEN + 1800.0, 100.0, 100.3, 99.7, 99.9, 400),
+        _bar("DBINM", E_OPEN + 2100.0, 99.9, 100.1, 99.6, 99.8, 500),
+        _bar("DBINM", E_OPEN + 2400.0, 99.8, 100.0, 99.65, 99.9, 450),
+        _bar("DBINM", E_OPEN + 2700.0, 99.7, 99.8, 98.9, 99.2, 1500),  # would break 99.6
+        _bar("DBINM", E_OPEN + 3000.0, 99.2, 99.4, 99.0, 99.1, 900),
+        _bar("DBINM", E_OPEN + 3300.0, 99.1, 99.3, 98.9, 99.0, 900),
+    ]
+    results = detect_dbi(
+        bars, _CONTINUATION_BASELINE, "DBINM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert results == []
+
+
+def test_jbe_ladder_two_firings_draw_independent_bases_and_disclose_the_step_ratio():
+    """TC-8 (detector level): a second, independent base+jump+trigger AFTER the first trigger bar
+    fires a second ``jbe`` signal, capped at
+    ``PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION`` (2) -- ``ladder_step_ratio`` is null on the first
+    firing and the (second jump / first jump) ratio on the second. ``test_desk_playbook.py`` proves
+    the SAME two-firing shape draws independent, non-colliding baseline anchors through the full
+    ``compute_playbook`` walk."""
+    bars = _canonical_jbe_bars("LADDER")[:10]  # step 1 only, through its own trigger bar (index 9)
+    bars += [
+        _bar("LADDER", E_OPEN + 3000.0, 104.5, 104.6, 104.3, 104.4, 1200),
+        _bar("LADDER", E_OPEN + 3300.0, 104.4, 104.5, 104.2, 104.3, 1200),
+        _bar("LADDER", E_OPEN + 3600.0, 104.3, 104.4, 104.1, 104.2, 1200),
+        _bar("LADDER", E_OPEN + 3900.0, 104.2, 104.3, 104.0, 104.1, 1200),
+        _bar("LADDER", E_OPEN + 4200.0, 104.1, 104.2, 103.9, 104.0, 1200),
+        _bar("LADDER", E_OPEN + 4500.0, 104.0, 104.3, 103.9, 104.2, 3000),  # step-2 lookback surge
+        _bar("LADDER", E_OPEN + 4800.0, 107.5, 107.8, 107.2, 107.6, 400),
+        _bar("LADDER", E_OPEN + 5100.0, 107.6, 108.0, 107.3, 107.7, 500),
+        _bar("LADDER", E_OPEN + 5400.0, 107.7, 107.9, 107.4, 107.8, 450),
+        _bar("LADDER", E_OPEN + 5700.0, 107.9, 108.8, 107.8, 108.5, 1500),  # step 2 trigger
+        _bar("LADDER", E_OPEN + 6000.0, 108.5, 108.7, 108.3, 108.6, 900),
+        _bar("LADDER", E_OPEN + 6300.0, 108.6, 108.8, 108.4, 108.7, 900),
+    ]
+    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(22)}}
+    results = detect_jbe(bars, baseline, "LADDER", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
+    assert len(results) == 2
+    step1, step2 = results
+    assert step1["geometry"]["slots_to_break"] == 9
+    assert step1["geometry"]["ladder_step_ratio"] is None
+    assert step2["geometry"]["slots_to_break"] == 19
+    # a genuinely SECOND base -- starts strictly after step 1's own trigger bar
+    assert step2["geometry"]["slots_to_break"] > step1["geometry"]["slots_to_break"]
+    assert step2["geometry"]["ladder_step_ratio"] == pytest.approx(
+        step2["geometry"]["jump_mbr"] / step1["geometry"]["jump_mbr"]
+    )
+
+
+# --- J-04: the continuation family's own truncate/mutate lookahead property test (TC-7) ----------
+
+_CONTINUATION_LOOKAHEAD_FIXTURES = [
+    (detect_jbe, _canonical_jbe_bars(), "JBE1"),
+    (detect_dbi, _canonical_dbi_bars(), "DBI1"),
+]
+
+
+@pytest.mark.parametrize("detect_fn, bars, symbol", _CONTINUATION_LOOKAHEAD_FIXTURES)
+def test_continuation_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields(
+    detect_fn, bars, symbol
+):
+    full = detect_fn(bars, _CONTINUATION_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
+    assert len(full) == 1
+    trigger_idx = full[0]["geometry"]["slots_to_break"]
+
+    truncated = detect_fn(
+        bars[: trigger_idx + 1], _CONTINUATION_BASELINE, symbol, SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(truncated) == 1
+    assert truncated[0]["trigger_price"] == full[0]["trigger_price"]
+    assert truncated[0]["invalidation_price"] == full[0]["invalidation_price"]
+    assert truncated[0]["geometry"] == full[0]["geometry"]
+
+
+@pytest.mark.parametrize("detect_fn, bars, symbol", _CONTINUATION_LOOKAHEAD_FIXTURES)
+def test_continuation_mutating_a_bar_after_the_trigger_changes_nothing(detect_fn, bars, symbol):
+    full = detect_fn(bars, _CONTINUATION_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
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
+        mutated, _CONTINUATION_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert mutated_result == full
+
+
+# === J-04: cup_handle (TC-3, TC-6) =================================================================
+
+
+def _canonical_cup_handle_bars(symbol: str = "CUP1", handle_ohlcv=None) -> list[RawBar]:
+    """Left rim (slot 3) -- decline to a cup bottom (slot 9, low=105.0) -- right rim (slot 15,
+    matching the left rim exactly) -- a 3-bar handle (slots 16-18, the pivot's own confirmation
+    window) -- trigger at slot 19 (the first bar legally allowed to use the confirmed right rim)."""
+    if handle_ohlcv is None:
+        handle_ohlcv = [
+            (109.6, 109.3, 108.0, 108.5, 400),
+            (108.5, 109.0, 107.8, 108.2, 400),
+            (108.2, 109.4, 108.0, 108.9, 400),
+        ]
+    bars = [
+        _bar(symbol, E_OPEN, 106.5, 107.0, 106.0, 106.8, 500),
+        _bar(symbol, E_OPEN + 300.0, 106.8, 108.0, 106.5, 107.5, 500),
+        _bar(symbol, E_OPEN + 600.0, 107.5, 109.0, 107.0, 108.5, 500),
+        _bar(symbol, E_OPEN + 900.0, 108.5, 110.0, 108.0, 109.5, 1000),  # LEFT RIM
+        _bar(symbol, E_OPEN + 1200.0, 109.5, 109.0, 108.0, 108.5, 1000),
+        _bar(symbol, E_OPEN + 1500.0, 108.5, 108.0, 107.0, 107.5, 1000),
+        _bar(symbol, E_OPEN + 1800.0, 107.5, 107.5, 106.5, 107.0, 1000),
+        _bar(symbol, E_OPEN + 2100.0, 107.0, 106.5, 106.0, 106.2, 300),
+        _bar(symbol, E_OPEN + 2400.0, 106.2, 106.0, 105.5, 105.8, 300),
+        _bar(symbol, E_OPEN + 2700.0, 105.8, 105.5, 105.0, 105.2, 300),  # cup bottom low=105.0
+        _bar(symbol, E_OPEN + 3000.0, 105.2, 106.0, 105.1, 105.8, 300),
+        _bar(symbol, E_OPEN + 3300.0, 105.8, 107.0, 105.5, 106.8, 300),
+        _bar(symbol, E_OPEN + 3600.0, 106.8, 108.0, 106.5, 107.8, 1000),
+        _bar(symbol, E_OPEN + 3900.0, 107.8, 109.0, 107.5, 108.8, 1000),
+        _bar(symbol, E_OPEN + 4200.0, 108.8, 109.5, 108.5, 109.2, 1000),
+        _bar(symbol, E_OPEN + 4500.0, 109.2, 110.0, 108.8, 109.6, 1000),  # RIGHT RIM
+    ]
+    for i, (o, h, l, c, v) in enumerate(handle_ohlcv, start=16):
+        bars.append(_bar(symbol, E_OPEN + i * 300.0, o, h, l, c, v))
+    next_i = 16 + len(handle_ohlcv)
+    bars.append(_bar(symbol, E_OPEN + next_i * 300.0, 108.9, 110.5, 108.7, 110.2, 1500))  # trigger
+    bars.append(_bar(symbol, E_OPEN + (next_i + 1) * 300.0, 110.2, 110.4, 109.9, 110.1, 900))
+    bars.append(_bar(symbol, E_OPEN + (next_i + 2) * 300.0, 110.1, 110.3, 109.8, 110.0, 900))
+    return bars
+
+
+_CUP_HANDLE_BASELINE = {
+    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(25)},
+}
+
+
+def test_canonical_cup_handle_matches_the_hand_computed_signal():
+    """TC-3: the canonical cup-and-handle firing -- rims, cup depth/duration, handle retrace/
+    duration, and the three RVOL medians hand-verified (values confirmed by direct execution)."""
+    signal = detect_cup_handle(
+        _canonical_cup_handle_bars(), _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert signal is not None
+    assert signal["setup_id"] == "cup_handle"
+    assert signal["side"] == "long"
+    assert signal["trigger_price"] == 110.0
+    assert signal["entry"] == 110.0
+    assert signal["entry_kind"] == "level"
+    assert signal["price_low"] == pytest.approx(105.0)
+    assert signal["invalidation_price"] == pytest.approx(107.14)
+    geometry = signal["geometry"]
+    assert geometry["slots_to_break"] == 19
+    assert geometry["cup_bars"] == 12
+    assert geometry["cup_depth_mbr"] == pytest.approx(5.0)
+    assert geometry["handle_retrace_frac"] == pytest.approx(0.44)
+    assert geometry["handle_duration_frac"] == pytest.approx(0.25)
+    assert geometry["cup_optimal"] is True
+    assert geometry["handle_duration_desirable"] is True
+    assert geometry["cup_middle_third_rvol_median"] == pytest.approx(0.3)
+    assert geometry["cup_outer_third_rvol_median"] == pytest.approx(1.0)
+    assert geometry["handle_rvol_median"] == pytest.approx(0.4)
+    assert signal["principles"] == ["P4", "P5-inverse"]
+
+
+def test_cup_handle_near_miss_handle_retrace_beyond_50pct_fires_no_signal():
+    """TC-6: the SAME cup, but the handle dips well past 50% of cup depth before the rim ever
+    breaks -- voids silently even though a later bar still crosses the rim price."""
+    near_miss_handle = [
+        (109.6, 109.0, 105.5, 106.0, 400),  # retrace to 105.5 -- 90% of a 5.0 cup depth
+        (106.0, 106.5, 105.6, 106.2, 400),
+        (106.2, 106.8, 106.0, 106.5, 400),
+    ]
+    bars = _canonical_cup_handle_bars("CUPNM", handle_ohlcv=near_miss_handle)
+    signal = detect_cup_handle(
+        bars, _CUP_HANDLE_BASELINE, "CUPNM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert signal is None
+
+
+def test_cup_handle_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields():
+    """TC-7: the same truncation-invariance property, for ``cup_handle``."""
+    bars = _canonical_cup_handle_bars()
+    full = detect_cup_handle(
+        bars, _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert full is not None
+    trigger_idx = full["geometry"]["slots_to_break"]
+
+    truncated = detect_cup_handle(
+        bars[: trigger_idx + 1], _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert truncated is not None
+    assert truncated["trigger_price"] == full["trigger_price"]
+    assert truncated["invalidation_price"] == full["invalidation_price"]
+    assert truncated["geometry"] == full["geometry"]
+
+
+def test_cup_handle_mutating_a_bar_after_the_trigger_changes_nothing():
+    """TC-7: mutation-invariance for ``cup_handle``."""
+    bars = _canonical_cup_handle_bars()
+    full = detect_cup_handle(
... [diff_bound] apps/backend/tests/test_desk_playbook_detect.py: 16 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 619b179..5f2b4b0 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -157,6 +157,10 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
 # values are already reached through the EXISTING `touchRow.*`/`touchValue.*`/`avgCell.*` bindings
 # this guard already covers -- see test_desk_page_price_arithmetic_guard_catches_playbook_field_
 # arithmetic below for the counter-test proving both the new and the reused bindings are caught.
+# goal-playbook-iter-4 (J-04): extended AGAIN for the continuation family (jbe/dbi) and cup_handle's
+# own NEW `signal.geometry.*` numerics -- `PlaybookSignalDetail`'s two new setup-branches render
+# every one of these verbatim (base/jump geometry + ladder-step-ratio; cup/handle geometry + the
+# three RVOL medians), never a client-recomputed spread or ratio.
 _PRICE_ARITHMETIC_FIELDS = (
     r"row\.(?:distance_bps|price_low|price_high|reference_close"
     r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
@@ -168,6 +172,9 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|avgCell\.(?:mean_pct|median_pct)"
     r"|summaryCell\.(?:mean_pct|median_pct)"
     r"|signal\.(?:trigger_price|invalidation_price)"
+    r"|geometry\.(?:jump_mbr|base_range_mbr|ladder_step_ratio|cup_depth_mbr|handle_retrace_frac"
+    r"|handle_duration_frac|cup_middle_third_rvol_median|cup_outer_third_rvol_median"
+    r"|handle_rvol_median)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -270,6 +277,27 @@ def test_desk_page_price_arithmetic_guard_catches_playbook_field_arithmetic():
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline) is not None
 
 
+def test_desk_page_price_arithmetic_guard_catches_continuation_and_cup_handle_field_arithmetic():
+    """goal-playbook-iter-4 (J-04) counter-test: the extended guard catches arithmetic on the
+    continuation family's (jbe/dbi) and cup_handle's own NEW `geometry.*` bindings."""
+    seeded_jbe = "const net = geometry.jump_mbr - geometry.base_range_mbr;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_jbe) is not None
+
+    seeded_ladder = "const decay = geometry.ladder_step_ratio * 2;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_ladder) is not None
+
+    seeded_cup = "const drop = geometry.cup_depth_mbr - geometry.handle_retrace_frac;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_cup) is not None
+
+    seeded_rvol_contrast = (
+        "const contrast = geometry.cup_middle_third_rvol_median / geometry.cup_outer_third_rvol_median;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_rvol_contrast) is not None
+
+    seeded_handle_rvol = "const dry = geometry.handle_rvol_median - geometry.cup_outer_third_rvol_median;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_handle_rvol) is not None
+
+
 # goal-desk-iter-24 (J-16) TC-7 (a): the ranked table's own reflow adds a `rank` cell rendering
 # each row's own 1-based position in the served `rows` array (the `.map` index) -- this guard
 # proves the page never sorts, reverses, or re-slices `rows` to produce that position (or any
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 014b049..60a4238 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -4401,6 +4401,9 @@ const PLAYBOOK_LEGACY_ABSENCE = "measurement not recorded in this record";
 function playbookSetupLabel(setupId: string): string {
   if (setupId === "open_high_break") return "Open-High Break";
   if (setupId === "open_low_break") return "Open-Low Break";
+  if (setupId === "jbe") return "Jump-Base Explosion";
+  if (setupId === "dbi") return "Drop-Base Implosion";
+  if (setupId === "cup_handle") return "Cup and Handle";
   return setupId;
 }
 
@@ -4579,13 +4582,45 @@ function PlaybookSignalDetail({
           {fmt(signal.invalidation_price)}
         </span>
       </p>
-      <p className="mt-1 text-[11px] text-slate-500">
-        opening range {fmt(geometry.or_low)}–{fmt(geometry.or_high)} ({geometry.opening_range_basis}{" "}
-        basis, {geometry.or_bars_used} bars) · width {fmt(geometry.or_width_mbr)} MBR · broke at
-        slot {geometry.slots_to_break}
-        {geometry.open_vs_prior_close_pct !== null &&
-          ` · open vs prior close ${fmt(geometry.open_vs_prior_close_pct)}%`}
-      </p>
+      {/* goal-playbook-iter-4 (J-04): the ONE geometry object now varies its own fields by
+          setup_id -- open_high_break/open_low_break's own line (J-01, unchanged); jbe/dbi's own
+          line and cup_handle's own line are the two new branches below. Every value rendered
+          verbatim from the already-served payload, never derived client-side (T-9's own guard,
+          extended in test_desk_ui_guards.py). */}
+      {(signal.setup_id === "open_high_break" || signal.setup_id === "open_low_break") && (
+        <p className="mt-1 text-[11px] text-slate-500">
+          opening range {fmt(geometry.or_low)}–{fmt(geometry.or_high)} ({geometry.opening_range_basis}{" "}
+          basis, {geometry.or_bars_used} bars) · width {fmt(geometry.or_width_mbr)} MBR · broke at
+          slot {geometry.slots_to_break}
+          {geometry.open_vs_prior_close_pct !== null && geometry.open_vs_prior_close_pct !== undefined &&
+            ` · open vs prior close ${fmt(geometry.open_vs_prior_close_pct)}%`}
+        </p>
+      )}
+      {(signal.setup_id === "jbe" || signal.setup_id === "dbi") && (
+        <p data-testid="desk-playbook-signal-continuation-geometry" className="mt-1 text-[11px] text-slate-500">
+          base {fmt(geometry.base_range_mbr)} MBR wide ({geometry.base_bars} bars) · jump{" "}
+          {fmt(geometry.jump_mbr)} MBR · broke at slot {geometry.slots_to_break}
+          {geometry.base_flatline && " · flatline base"}
+          {geometry.base_lows_ascending && " · ascending base"}
+          {geometry.ladder_step_ratio !== null && geometry.ladder_step_ratio !== undefined &&
+            ` · ladder step ratio ${fmt(geometry.ladder_step_ratio)}`}
+        </p>
+      )}
+      {signal.setup_id === "cup_handle" && (
+        <p data-testid="desk-playbook-signal-cup-handle-geometry" className="mt-1 text-[11px] text-slate-500">
+          cup {geometry.cup_bars} bars · depth {fmt(geometry.cup_depth_mbr)} MBR · handle retrace{" "}
+          {fmt(geometry.handle_retrace_frac)} · handle duration {fmt(geometry.handle_duration_frac)} of
+          cup · broke at slot {geometry.slots_to_break}
+          {geometry.cup_optimal && " · optimal cup length"}
+          {geometry.handle_duration_desirable && " · desirable handle length"}
+          {" · RVOL cup mid "}
+          {fmt(geometry.cup_middle_third_rvol_median)}
+          {" / cup outer "}
+          {fmt(geometry.cup_outer_third_rvol_median)}
+          {" / handle "}
+          {fmt(geometry.handle_rvol_median)}
+        </p>
+      )}
       <p className="mt-1 text-[11px] text-slate-500">
         volume: {volume.spike_into_trigger_verdict}
         {volume.rvol_trigger_bar !== null && ` · trigger RVOL ${fmt(volume.rvol_trigger_bar)}`}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index d10da5c..2fd6216 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1477,14 +1477,37 @@ export interface DeskForwardComputeSnapshot {
 // every playbook signal through the SAME `desk_forward._measure_from` the forward rail's own
 // touches/anchors are measured through, so the shape is byte-identical by construction. ------------
 
+// goal-playbook-iter-4 (J-04): `open_high_break`/`open_low_break`'s own geometry fields become
+// OPTIONAL here -- the JBE/DBI and cup_handle setups this iteration adds serve a DIFFERENT
+// geometry shape on the SAME `signal.geometry` object (one owner, `desk_playbook_detect.py`, per
+// setup). `slots_to_break` is the one field every setup serves (it is what `_measure_signal`
+// anchors on) -- it stays required.
 export interface DeskPlaybookGeometry {
-  or_high: number;
-  or_low: number;
-  or_width_mbr: number;
-  or_bars_used: number;
-  opening_range_basis: "1m" | "5m";
   slots_to_break: number;
-  open_vs_prior_close_pct: number | null;
+  // open_high_break / open_low_break only (J-01)
+  or_high?: number;
+  or_low?: number;
+  or_width_mbr?: number;
+  or_bars_used?: number;
+  opening_range_basis?: "1m" | "5m";
+  open_vs_prior_close_pct?: number | null;
+  // jbe / dbi only (J-04, spec §3.3-3.4)
+  jump_mbr?: number;
+  base_range_mbr?: number;
+  base_bars?: number;
+  base_flatline?: boolean;
+  base_lows_ascending?: boolean;
+  ladder_step_ratio?: number | null;
+  // cup_handle only (J-04, spec §3.6)
+  cup_bars?: number;
+  cup_depth_mbr?: number;
+  handle_retrace_frac?: number;
+  handle_duration_frac?: number;
+  cup_optimal?: boolean;
+  handle_duration_desirable?: boolean;
+  cup_middle_third_rvol_median?: number;
+  cup_outer_third_rvol_median?: number;
+  handle_rvol_median?: number;
 }
 
 export interface DeskPlaybookVolume {
diff --git a/docs/playbook-detector-spec.md b/docs/playbook-detector-spec.md
index 9934916..d672583 100644
--- a/docs/playbook-detector-spec.md
+++ b/docs/playbook-detector-spec.md
@@ -106,6 +106,17 @@ tolerance (index-MBR) of its session low — mirrored for shorts. No SPY bars fo
 - `neutral` — otherwise.
 Disclosure only, never a gate.
 
+**Provenance ("the parameters hash").** Every served playbook payload already carries
+`playbook_input_signature` (the sha256[:16] over the recorded series' `(symbol, timeframe, id,
+checksum)` tuples, `config_fingerprint`, and the canonical `parameters` blob — see §1's closing
+paragraph) beside `config_fingerprint` and the verbatim `parameters` object itself. Together these
+three already-served fields ARE the goal's own "parameters hash" line — the signature is a hash
+*of* the parameters (among other inputs), and the parameters themselves are served alongside it in
+full, so nothing is hidden and nothing is re-derivable-but-undisclosed. This is a documentation-only
+ruling, not a new field: no source constant moves and no payload key is added or renamed by it (J-04
+carries this ruling forward from the iteration that raised it, mirroring the `PLAYBOOK_OR_MIN_1M_BARS`
+prose-to-table promotion pattern below).
+
 **Shared disclosure block on every signal:** `rvol_trigger_bar` (post-hoc),
 `approach_rvol_max`, `spike_into_trigger_verdict` (the discriminator), `spiky_approach`
 (single-bar vertical into the level), the market block, `attempt_count` at `T` (pre-trigger
@@ -140,12 +151,14 @@ continuation, P5 decreasing-volume reversal, P6 passive accumulation/distributio
 | `PLAYBOOK_BASE_MIN_BARS` | 3 | ADAPTATION — book gives no consolidation duration |
 | `PLAYBOOK_BASE_MAX_BARS` | 12 | ADAPTATION — 60-min cap; beyond it the "base" is the day's range |
 | `PLAYBOOK_BASE_MAX_RANGE_MBR` | 2.0 | ADAPTATION — relative form of the ≤25c narrow base |
+| `PLAYBOOK_BASE_FLATLINE_MAX_MBR` | 1.0 | ADAPTATION — §3.3/§3.4's own prose ("base range ≤ 1.0 MBR — the flatline-at-the-high variation") named as a constant (J-04, the `PLAYBOOK_OR_MIN_1M_BARS` precedent) |
 | `PLAYBOOK_NEAR_EXTREME_MBR` | 1.0 | ADAPTATION — mechanical "near the high/low" |
 | `PLAYBOOK_PIVOT_LOOKBACK_BARS` | 3 | ADAPTATION — 5m intraday N for the strict-pivot rule |
 | `PLAYBOOK_CUP_MIN_BARS` | 6 | BOOK — cup ≥ 30 min |
 | `PLAYBOOK_CUP_OPTIMAL_BARS` | 12 | BOOK — ≥ 1 h optimal (disclosure only) |
 | `PLAYBOOK_HANDLE_MAX_RETRACE_FRAC` | 0.5 | BOOK — handle ≤ 50% of cup depth |
 | `PLAYBOOK_HANDLE_MAX_DURATION_FRAC` | 0.30 | BOOK — handle ≤ 30% of cup duration (25% desirable → disclosure) |
+| `PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC` | 0.25 | BOOK — this row's own "25% desirable" parenthetical, named as a constant (J-04, the `PLAYBOOK_OR_MIN_1M_BARS` precedent) so `handle_duration_desirable` reads through `playbook_parameters()` like every other threshold |
 | `PLAYBOOK_RIM_MATCH_MBR` | 1.0 | ADAPTATION — "cup edges at the day's high" tolerance |
 | `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR` | 2.0 | ADAPTATION — min cup depth AND min valley depth |
 | `PLAYBOOK_VERTICAL_WINDOW_BARS` | 3 | ADAPTATION — "near-vertical" window (15 min) |
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-playbook-index.html        | 11 ++--
 runs/goal-session-playbook/.engine.lock/boot_id |  2 +-
 runs/goal-session-playbook/.engine.lock/epoch   |  2 +-
 runs/goal-session-playbook/.engine.lock/pid     |  2 +-
 runs/goal-session-playbook/dispatch/.pump-alive |  4 +-
 runs/goal-session-playbook/engine.pid           |  2 +-
 runs/goal-session-playbook/session.json         |  6 +-
 runs/goal-session-playbook/summary.md           | 82 +++++++++++++++++++------
 runs/goal-session-playbook/telemetry.jsonl      | 29 +++++++++
 runs/goal-session-playbook/trace/trace.jsonl    |  2 +
 10 files changed, 110 insertions(+), 32 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
