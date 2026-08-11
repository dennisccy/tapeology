# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/research/desk_playbook.py b/apps/backend/app/research/desk_playbook.py
index 87afe8f..7544278 100644
--- a/apps/backend/app/research/desk_playbook.py
+++ b/apps/backend/app/research/desk_playbook.py
@@ -1,4 +1,4 @@
-"""The Playbook (Era B2 "The Playbook", J-01/J-02/J-04) -- the book's intraday setups
+"""The Playbook (Era B2 "The Playbook", J-01/J-02/J-04/J-05) -- the book's intraday setups
 (Graifer & Schumacher, *Techniques of Tape Reading*, 2004), detected on the desk's own recorded
 5m/1m bars and measured with the desk forward rail's own conventions. This module owns the
 pre-registered constant table, the parameters/signature recipe, the append-only store, and the
@@ -16,12 +16,13 @@ imports from ``setups.py`` or ``backtests.py``, and no field here is ever named
 
 **Detection then measurement, in one walk.** ``compute_playbook`` walks the desk universe's
 members and detects, per member, the opening-range-break pair (spec §3.1-3.2, J-01) beside the
-continuation family (``jbe``/``dbi``, spec §3.3-3.4, J-04) and ``cup_handle`` (spec §3.6, J-04),
-gated by the SAME "5m bars + sufficient baseline + a buildable opening range" absence checks J-01
-shipped -- every detected signal is measured in the same pass (forward returns,
-``invalidation_breached``, the seeded baseline, J-02) -- ``entry``/``entry_kind`` are decided at
-detection time (spec §0's stop-through fill convention is part of a signal's own GEOMETRY, not
-part of measuring what happened afterward).
+continuation family (``jbe``/``dbi``, spec §3.3-3.4, J-04), ``cup_handle`` (spec §3.6, J-04), and
+``capitulation`` (spec §3.5, J-05), gated by the SAME "5m bars + sufficient baseline + a buildable
+opening range" absence checks J-01 shipped -- every detected signal is measured in the same pass
+(forward returns, ``invalidation_breached``, the seeded baseline, J-02) -- ``entry``/``entry_kind``
+are decided at detection time (spec §0's stop-through fill convention is part of a signal's own
+GEOMETRY, not part of measuring what happened afterward). ``detect_euphoria`` (spec §3.5's marker,
+J-05) runs in the SAME per-member walk but is never measured -- see ``_decorate_markers``.
 
 **Parameters discipline (the ``desk_forward.forward_parameters`` pattern, applied at birth).**
 ``playbook_parameters()`` reads every constant below at CALL TIME (so a test monkeypatching one
@@ -63,7 +64,14 @@ from .desk_forward import (
     _draw_anchor_indices,
     _measure_from,
 )
-from .desk_playbook_detect import detect_cup_handle, detect_dbi, detect_jbe, detect_opening_range_breaks
+from .desk_playbook_detect import (
+    detect_capitulation,
+    detect_cup_handle,
+    detect_dbi,
+    detect_euphoria,
+    detect_jbe,
+    detect_opening_range_breaks,
+)
 from .desk_playbook_features import baselines, opening_range, rth_session_slice, side_sign
 from .desk_sessions import refuse_if_not_a_session
 
@@ -140,11 +148,15 @@ PLAYBOOK_BASE_FLATLINE_MAX_MBR: float = 1.0  # ADAPTATION -- spec §3.3 prose "b
 PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC: float = 0.25  # BOOK -- spec §1's HANDLE_MAX_DURATION_FRAC row: "25% desirable"
 
 # Companion structural constants (shape, not thresholds).
-# J-01 shipped ONLY the opening-range-break family; J-04 (this iteration) EXTENDS this tuple with
-# the continuation family (jbe/dbi/cup_handle) -- J-05/J-06 will extend it further as they land
-# their own detectors (each extension is a signature-moving, expected, visible change) -- declaring
-# a setup id here before its detector exists would claim a compute that does not happen.
-PLAYBOOK_SETUPS: tuple[str, ...] = ("open_high_break", "open_low_break", "jbe", "dbi", "cup_handle")
+# J-01 shipped ONLY the opening-range-break family; J-04 EXTENDED this tuple with the continuation
+# family (jbe/dbi/cup_handle); J-05 (this iteration) adds `capitulation` -- J-06 will extend it
+# further with the range family (each extension is a signature-moving, expected, visible change) --
+# declaring a setup id here before its detector exists would claim a compute that does not happen.
+# `"euphoria"` is DELIBERATELY never added here: spec §3.5 defines it as a marker only, never a
+# recorded setup -- see `_decorate_markers` below for what it does instead.
+PLAYBOOK_SETUPS: tuple[str, ...] = (
+    "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
+)
 PLAYBOOK_MARKET_SYMBOL: str = "SPY"
 # The rail's own baseline seed, echoed (not re-derived) -- the seed discipline itself is J-02's;
 # embedding the CONSTANT now is what makes a future rail-seed change re-key playbook records too.
@@ -157,8 +169,9 @@ PLAYBOOK_MIN_N_DISCLOSURE: int = 12  # evidence low-n tag (J-08) -- a disclosure
 # The visible honesty register carried by every playbook payload. Lint-checked via
 # test_copy_discipline.find_violations (the desk_forward.FORWARD_REGISTER precedent).
 PLAYBOOK_REGISTER = (
-    "pre-registered opening-range-break signals detected on the desk's own recorded 5m/1m bars — "
-    "every threshold is fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
+    "pre-registered opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, "
+    "and capitulation signals detected on the desk's own recorded 5m/1m bars — every threshold is "
+    "fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
     "A signal is a recorded observation, not advice: invalidation_price is the book's own "
     "structural level, disclosed as geometry, never a stop order, a size, or an account concept. "
     "Each signal's forward block is measured with the desk forward rail's own conventions — "
@@ -450,6 +463,38 @@ def _baseline_seed(session_date: str, symbol: str, setup_id: str, firing_index:
     return f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}{discriminator}"
 
 
+def _decorate_markers(
+    detected_signals: list[dict], euphoria_trigger_indices: list[int], params: dict
+) -> None:
+    """spec §3.5's marker-decoration pass, in place, for ONE member's already-assembled
+    ``detected_signals`` (any setup, including ``capitulation`` itself) -- sets
+    ``disclosures.euphoria_recent``/``capitulation_recent`` on every signal whose own trigger bar
+    (``geometry.slots_to_break``, the one field every setup family serves) falls STRICTLY AFTER a
+    same-symbol-session marker's own trigger bar and within ``PLAYBOOK_MARKER_DECAY_BARS`` bars of
+    it -- forward-only by construction (a marker never reaches back to decorate a signal that
+    already triggered before it fired; the only lookahead-clean reading of "sets ... on any signal
+    triggering within the decay window" -- see ``runs/goal-session-playbook/state/assumptions.md``
+    for why). A ``capitulation`` SIGNAL is itself a capitulation marker for every OTHER later signal
+    in the SAME walk (spec §3.5: "capitulation events symmetrically set capitulation_recent") but
+    never self-decorates its own firing -- the strict-after comparison already makes that
+    impossible (a signal's own trigger bar index is never strictly after itself), so no
+    special-case exclusion is needed. Decoration is same-symbol-session only by construction: the
+    caller hands this ONE member's own ``detected_signals`` and euphoria markers, never another
+    member's."""
+    decay = params["marker_decay_bars"]
+    capitulation_trigger_indices = [
+        signal["geometry"]["slots_to_break"]
+        for signal in detected_signals
+        if signal["setup_id"] == "capitulation"
+    ]
+    for signal in detected_signals:
+        own_trigger = signal["geometry"]["slots_to_break"]
+        if any(0 < own_trigger - marker <= decay for marker in euphoria_trigger_indices):
+            signal["disclosures"]["euphoria_recent"] = True
+        if any(0 < own_trigger - marker <= decay for marker in capitulation_trigger_indices):
+            signal["disclosures"]["capitulation_recent"] = True
+
+
 def compute_playbook(
     universe_store,
     bar_store,
@@ -460,17 +505,19 @@ def compute_playbook(
     should_abort: Callable[[], bool] | None = None,
 ) -> dict:
     """Detect AND measure every registered setup family (opening-range-break, J-01; the
-    continuation family ``jbe``/``dbi`` and ``cup_handle``, J-04) for EVERY member of the latest
-    registered universe snapshot, on ``session_date``'s own recorded bars, in the SAME walk --
-    returns everything ``PlaybookStore.record`` needs minus the store-assigned ``id``/
-    ``recorded_at`` (the ``compute_forward``/``compute_screen`` contract shape: a PURE compute,
-    never itself a store write).
+    continuation family ``jbe``/``dbi`` and ``cup_handle``, J-04; ``capitulation``, J-05) for EVERY
+    member of the latest registered universe snapshot, on ``session_date``'s own recorded bars, in
+    the SAME walk -- the ``euphoria`` marker (J-05) also runs per-member but decorates rather than
+    joining this list (see ``_decorate_markers``). Returns everything ``PlaybookStore.record``
+    needs minus the store-assigned ``id``/``recorded_at`` (the ``compute_forward``/
+    ``compute_screen`` contract shape: a PURE compute, never itself a store write).
 
     Session-honesty first: ``desk_sessions.refuse_if_not_a_session`` is checked before any bar is
     read for detection -- a non-session date raises ``PlaybookSessionRefused`` and NOTHING is
     walked. Per member: no 5m bars for the session, a thin/zero baseline, or no buildable opening
-    range are each a disclosed ``absences`` row (never a crash, never a guess) -- ALL FOUR
-    detector families share this one gate (a deliberate J-04 simplification: spec §3.1 scopes "no
+    range are each a disclosed ``absences`` row (never a crash, never a guess) -- ALL FIVE
+    detector families (plus the ``euphoria`` marker) share this one gate (a deliberate J-04
+    simplification: spec §3.1 scopes "no
     OR" absence to the OR-break family alone, but sharing the gate keeps J-01/J-02's own absence
     contract byte-unchanged, at the cost of also skipping jbe/dbi/cup_handle on the rare session
     with 5m coverage but no buildable opening range -- see the dev handoff). Everything else
@@ -600,6 +647,23 @@ def compute_playbook(
         if cup_signal is not None:
             detected_signals.append(cup_signal)
 
+        # J-05: capitulation joins the SAME per-member walk (spec §3.5), sharing the SAME "5m bars
+        # + sufficient baseline + a buildable opening range" absence gate as every other family.
+        # `euphoria` is a MARKER ONLY (§3.5's own "no side, no band, never measured" rule) -- its
+        # single trigger-bar index feeds `_decorate_markers` immediately below and is discarded
+        # afterward, never appended to `detected_signals`/`signals`/`signal_pool`/`baseline_pool`
+        # (TC-4's structural guarantee: there is no code path here that could).
+        capitulation_signal = detect_capitulation(
+            session_5m, baseline, symbol, session_date, index_bars, index_baseline, params
+        )
+        if capitulation_signal is not None:
+            detected_signals.append(capitulation_signal)
+        euphoria_marker = detect_euphoria(session_5m, baseline, params)
+        euphoria_trigger_indices = (
+            [euphoria_marker["trigger_idx"]] if euphoria_marker is not None else []
+        )
+        _decorate_markers(detected_signals, euphoria_trigger_indices, params)
+
         if detected_signals:
             session_1m = rth_session_slice(bars_1m, session_date)
             for signal in detected_signals:
diff --git a/apps/backend/app/research/desk_playbook_detect.py b/apps/backend/app/research/desk_playbook_detect.py
index 93696f7..1336fde 100644
--- a/apps/backend/app/research/desk_playbook_detect.py
+++ b/apps/backend/app/research/desk_playbook_detect.py
@@ -1,9 +1,12 @@
 """The Playbook's detectors (Era B2). J-01 shipped the opening-range-break family
-(``docs/playbook-detector-spec.md`` §3.1-3.2); J-04 (this iteration) adds the continuation family
--- ``detect_jbe``/``detect_dbi`` (§3.3-3.4, one shared internal walk, direction-flipped) and
-``detect_cup_handle`` (§3.6). J-05/J-06 add the remaining four detectors here, each built purely
-out of ``desk_playbook_features.py``'s eight primitives plus the ``playbook_parameters()`` dict a
-caller hands in.
+(``docs/playbook-detector-spec.md`` §3.1-3.2); J-04 added the continuation family --
+``detect_jbe``/``detect_dbi`` (§3.3-3.4, one shared internal walk, direction-flipped) and
+``detect_cup_handle`` (§3.6). J-05 (this iteration) adds the climax family --
+``detect_capitulation`` (§3.5, entry) and ``detect_euphoria`` (§3.5, the exact mirror UP, a
+MARKER only -- never a served signal). J-06 adds the remaining three detectors
+(``range_trade``/``double_top``/``double_bottom``), each built purely out of
+``desk_playbook_features.py``'s eight primitives plus the ``playbook_parameters()`` dict a caller
+hands in.
 
 **J-04's own primitives are all reused, none added.** ``consolidation_range`` (JBE/DBI's base,
 shared with the module's own precedent of "shared geometry for JBE/DBI's base and cup-and-handle's
@@ -55,6 +58,8 @@ __all__ = [
     "detect_jbe",
     "detect_dbi",
     "detect_cup_handle",
+    "detect_capitulation",
+    "detect_euphoria",
 ]
 
 
@@ -791,3 +796,215 @@ def detect_cup_handle(
                 },
             }
     return None
+
+
+# --- J-05: the climax family -- capitulation (spec §3.5, entry) + euphoria (spec §3.5, the exact
+# mirror UP, a MARKER only) -------------------------------------------------------------------------
+#
+# ONE shared walk (``_find_climax_formation``), direction-parameterized by ``direction`` -- spec
+# §3.5 states euphoria IS capitulation's "exact mirror UP... same constants", so a second,
+# hand-flipped copy would be the second-implementation drift the module's own
+# ``_continuation_signals``/``side_sign`` precedent already avoids for jbe/dbi.
+
+
+def _rvol_series(session_bars: list[RawBar], slot_volume_medians: dict[int, float]) -> list[float | None]:
+    """Every bar's own RVOL against its baseline slot median, in session order -- the parallel
+    array ``vertical_move``'s ``require_volume`` clause needs (spec §0's ONE relative-volume
+    definition, computed once per session rather than re-derived per candidate climax bar)."""
+    return [_rvol(bar, idx, slot_volume_medians) for idx, bar in enumerate(session_bars)]
+
+
+def _find_climax_formation(
+    session_bars: list[RawBar],
+    rvols: list[float | None],
+    params: dict,
+    mbr: float,
+    direction: str,
+) -> tuple[int, int, int] | None:
+    """spec §3.5's shared vertical-move + reversal-bar grammar, direction-parameterized
+    (``direction="down"`` powers ``detect_capitulation``, ``"up"`` powers ``detect_euphoria``).
+    Returns ``(window_start, climax_idx, trigger_idx)`` for the FIRST candidate climax bar ``v``
+    (a ``vertical_move`` formation ending at ``v``, with the ``require_volume`` clause) whose
+    reversal-bar trigger fires within ``PLAYBOOK_BOUNCE_MAX_BARS`` of the bar's own (possibly
+    re-anchored) climax -- ``None`` if no candidate anywhere in the session both forms and triggers
+    (a later, independent formation may still succeed after an earlier one expires, mirroring
+    ``detect_cup_handle``'s own "first (left_rim, right_rim) pair whose full formation validates
+    AND triggers" search -- never just the first candidate encountered, whether or not it pans
+    out).
+
+    **Re-anchoring, made concrete.** ``leg_low``/``leg_high`` (``extreme`` below) is the running
+    minimum low (``direction="down"``) or maximum high (``"up"``) through the bar STRICTLY BEFORE
+    the candidate trigger bar ``t`` -- spec: "min low through ``t-1``". At every step, bar ``t-1``
+    is checked against the running extreme BEFORE bar ``t`` is evaluated as a trigger candidate: a
+    new extreme re-anchors the climax bar ``v`` to ``t-1`` itself (spec: "a new low after ``v``
+    re-anchors ``v`` -- the panic still running"), which also resets the bounce-window clock (the
+    window is measured from the CURRENT ``v``, not the original one) -- the panic continuing is
+    never mistaken for the window expiring. The trigger predicate itself (``high > high[t-1]`` /
+    the mirrored low check) always compares against the bar IMMEDIATELY before ``t``, never against
+    the climax bar's own high/low -- spec: "first-strength reversal bar", a purely local fact."""
+    window = params["vertical_window_bars"]
+    k = params["vertical_move_mbr"] * mbr
+    bounce_max = params["bounce_max_bars"]
+    rvol_surge = params["rvol_surge"]
+    n = len(session_bars)
+
+    for v0 in range(window, n):
+        if not vertical_move(
+            session_bars, v0, window, k, direction,
+            require_volume=True, rvol_surge=rvol_surge, rvols=rvols,
+        ):
+            continue
+        window_start = v0 - window + 1
+        extreme = session_bars[v0].low if direction == "down" else session_bars[v0].high
+        cur_v = v0
+        t = v0 + 1
+        while t < n:
+            prev = session_bars[t - 1]
+            if t - 1 > cur_v:
+                is_new_extreme = prev.low < extreme if direction == "down" else prev.high > extreme
+                if is_new_extreme:
+                    extreme = prev.low if direction == "down" else prev.high
+                    cur_v = t - 1
+            if (t - cur_v) > bounce_max:
+                break
+            bar = session_bars[t]
+            reverses = (
+                bar.high > session_bars[t - 1].high if direction == "down"
+                else bar.low < session_bars[t - 1].low
+            )
+            if reverses:
+                return window_start, cur_v, t
+            t += 1
+    return None
+
+
+def detect_capitulation(
+    session_bars: list[RawBar],
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+) -> dict | None:
+    """spec §3.5 -- capitulation entry, long only: a vertical decline (``vertical_move`` DOWN with
+    the ``require_volume`` clause this iteration is the first to exercise) followed by the first
+    bar within ``PLAYBOOK_BOUNCE_MAX_BARS`` of the (possibly re-anchored) climax bar whose high
+    exceeds the PRIOR bar's own high (``T = high[t-1]`` -- fully known at ``t-1``; the crossing at
+    ``t`` is the only bar-``t`` fact the trigger itself depends on). Capped at 1 per symbol-session
+    by construction (this function returns at most one signal, mirroring ``detect_cup_handle``'s
+    own single-return shape). Follows the SAME signal-assembly shape as
+    ``detect_opening_range_breaks``/the continuation family (entry/entry_kind via the shared
+    stop-through-fill convention, ``market`` via ``_market_block``, the shared volume/attempt-count
+    disclosures) so it flows through ``desk_playbook._measure_signal`` unmodified."""
+    mbr = baseline["mbr"]
+    if mbr == 0.0:
+        return None
+    slot_medians = baseline["slot_volume_medians"]
+    rvols = _rvol_series(session_bars, slot_medians)
+    found = _find_climax_formation(session_bars, rvols, params, mbr, "down")
+    if found is None:
+        return None
+    window_start, climax_idx, trigger_idx = found
+
+    leg_low = session_bars[climax_idx].low
+    trigger_price = session_bars[trigger_idx - 1].high
+    trigger_bar = session_bars[trigger_idx]
+    entry = max(trigger_bar.open, trigger_price)
+    entry_kind = "level" if trigger_bar.open < trigger_price else "gap_open"
+    gapped_beyond_chase = trigger_bar.open > trigger_price * (1.0 + params["max_chase_frac"])
+    invalidation_price = leg_low - params["stop_pad_frac"] * (trigger_price - leg_low)
+
+    # Disclosures spec §3.5 names by name -- `decline_bars` spans the WHOLE decline leg (the
+    # original vertical-move window's own start through the possibly-re-anchored climax bar), so a
+    # formation that re-anchors reports a LONGER decline than the raw `vertical_window_bars`
+    # constant, never a fixed value (see the re-anchoring fixture in
+    # test_desk_playbook_detect.py). `decline_mbr` is the net decline from the close right before
+    # the vertical move began through to the eventual (possibly re-anchored) leg low -- the same
+    # "how far did price actually fall" reading `vertical_move`'s own net-move check uses, extended
+    # through any re-anchoring.
+    decline_bars = climax_idx - window_start + 1
+    decline_mbr = (session_bars[window_start - 1].close - leg_low) / mbr
+    climax_rvol = rvols[climax_idx]
+    bars_from_climax_to_trigger = trigger_idx - climax_idx
+
+    approach_start = max(0, trigger_idx - params["approach_bars"])
+    approach_indices = list(range(approach_start, trigger_idx))
+    approach_rvols = [rvols[i] for i in approach_indices]
+    known_approach = [r for r in approach_rvols if r is not None]
+    approach_rvol_max = max(known_approach) if known_approach else None
+    rvol_trigger_bar = rvols[trigger_idx]
+    spike_verdict = _spike_into_trigger_verdict(
+        session_bars, approach_indices, approach_rvols, trigger_price, "long", mbr,
+        params["rvol_surge"], params["near_extreme_mbr"],
+    )
+    spiky_approach = False
+    if trigger_idx - 1 >= 0:
+        spiky_approach = vertical_move(
+            session_bars, trigger_idx - 1, 1, params["vertical_bar_mbr"] * mbr, "up",
+        )
+    zone_lo, zone_hi = trigger_price - params["near_extreme_mbr"] * mbr, trigger_price
+    attempt_count = len(zone_touches(session_bars[:trigger_idx], zone_lo, zone_hi))
+    market = _market_block(
+        session_bars, trigger_idx, index_bars, session_date, "long", mbr, index_baseline, params,
+    )
+
+    return {
+        "symbol": symbol,
+        "setup_id": "capitulation",
+        "side": "long",
+        "trigger_ts": _iso(trigger_bar.epoch),
+        "trigger_price": trigger_price,
+        "entry": entry,
+        "entry_kind": entry_kind,
+        "price_low": leg_low,
+        "price_high": trigger_price,
+        "invalidation_price": invalidation_price,
+        "geometry": {
+            "slots_to_break": trigger_idx,
+            "decline_mbr": decline_mbr,
+            "decline_bars": decline_bars,
+            "climax_rvol": climax_rvol,
+            "bars_from_climax_to_trigger": bars_from_climax_to_trigger,
+        },
+        "volume": {
+            "rvol_trigger_bar": rvol_trigger_bar,
+            "approach_rvol_max": approach_rvol_max,
+            "spike_into_trigger_verdict": spike_verdict,
+            "spiky_approach": spiky_approach,
+        },
+        "market": market,
+        "principles": ["P1"],
+        "disclosures": {
+            "gapped_beyond_chase": gapped_beyond_chase,
+            "session_bar_count": len(session_bars),
+            "attempt_count": attempt_count,
+            "bars_to_close": len(session_bars) - 1 - trigger_idx,
+            "concurrent_signals": [],
+            "euphoria_recent": False,
+            "capitulation_recent": False,
+        },
+    }
+
+
+def detect_euphoria(session_bars: list[RawBar], baseline: dict, params: dict) -> dict | None:
+    """spec §3.5's euphoria marker -- the exact mirror UP of ``detect_capitulation``'s own
+    vertical-move + reversal-bar grammar (``_find_climax_formation`` with ``direction="up"``: the
+    SAME shared walk, never a second hand-flipped copy), same constants, same cap of 1 per
+    symbol-session, but returning a MARKER event only: no side, no entry, no invalidation, no
+    geometry, no ``setup_id`` -- structurally incapable of becoming a served signal row (there is
+    no field here a caller could even append to ``signals``/``signal_pool``/``baseline_pool`` with).
+    BOOK: an exit/avoid signal -- the authors do not short strong stocks on euphoria; the book's own
+    instruction IS "do nothing but note it," which is exactly this function's return shape. Its
+    only output is the firing's own trigger-bar index, consumed exclusively by
+    ``desk_playbook._decorate_markers`` and discarded immediately afterward -- this function is
+    never called anywhere near ``signals``/``signal_pool``/``baseline_pool`` construction."""
+    mbr = baseline["mbr"]
+    if mbr == 0.0:
+        return None
+    rvols = _rvol_series(session_bars, baseline["slot_volume_medians"])
+    found = _find_climax_formation(session_bars, rvols, params, mbr, "up")
+    if found is None:
+        return None
+    _window_start, _climax_idx, trigger_idx = found
+    return {"trigger_idx": trigger_idx}
diff --git a/apps/backend/tests/test_desk_playbook.py b/apps/backend/tests/test_desk_playbook.py
index fdd9a0e..addfe0b 100644
--- a/apps/backend/tests/test_desk_playbook.py
+++ b/apps/backend/tests/test_desk_playbook.py
@@ -1001,11 +1001,17 @@ def test_j04_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside
     pre_j04_sha = _sha256_file(pre_j04_path)
     assert pre_j04_meta["parameters"]["setups"] == ["open_high_break", "open_low_break"]
 
-    monkeypatch.undo()  # restore this iteration's real 5-setup PLAYBOOK_SETUPS
+    # goal-playbook-iter-5 (J-05) maintenance note: this restores the CURRENT `PLAYBOOK_SETUPS`,
+    # which iter-5 legitimately grew to 6 entries (`capitulation` joined) -- the assertion below is
+    # updated to match, exactly as this same test updated it from 2 to 5 entries when it was
+    # J-04's own new content. This is a live "what does PLAYBOOK_SETUPS currently say" assertion,
+    # not a frozen discipline guard, so it tracks the tuple's real value every iteration that
+    # legitimately extends it.
+    monkeypatch.undo()  # restore this iteration's real 6-setup PLAYBOOK_SETUPS
 
     current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
     assert current_result["parameters"]["setups"] == [
-        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle",
+        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
     ]
     assert current_result["playbook_input_signature"] != pre_j04_meta["playbook_input_signature"]
 
@@ -1030,3 +1036,213 @@ def test_j04_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside
         s for s in current_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
     ]
     assert pre_j04_or_signals == current_or_signals
+
+
+# === goal-playbook-iter-5 (J-05): the climax family wired into the real compute walk ==============
+
+
+def _plant_capitulation_session(bar_store: BarStore, symbol: str) -> None:
+    """The ``test_desk_playbook_detect.py`` canonical capitulation fixture, trimmed to 6 bars
+    (matching ``_plant_baseline_sessions``'s own 6-slot coverage) and planted through a real
+    ``BarStore``: a vertical decline into a climax bar (slot 3, RVOL surge) followed by a
+    first-strength reversal trigger at slot 4."""
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
+        _bar(symbol, "5m", E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),
+        _bar(symbol, "5m", E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
+        _bar(symbol, "5m", E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),
+        _bar(symbol, "5m", E_OPEN + 1200.0, 99.6, 101.5, 99.4, 101.0, 1000),
+        _bar(symbol, "5m", E_OPEN + 1500.0, 101.0, 101.3, 100.8, 101.1, 900),
+    ]
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def test_capitulation_wired_into_compute_playbook_is_measured_like_every_other_setup(
+    tmp_path, bar_store, universe_store,
+):
+    """Capitulation joins the SAME per-member walk as every other family: `PLAYBOOK_SETUPS` now
+    names it, and the recorded signal carries `forward`/`invalidation_breached` exactly like an
+    opening-range-break/jbe/dbi/cup_handle signal does (J-02's measurement pass, unmodified)."""
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_capitulation_session(bar_store, "AAA")
+    # THIN stays absent (thin baseline) -- reused from the fixture universe unmodified.
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    assert desk_playbook_module.PLAYBOOK_SETUPS[-1] == "capitulation"
+    assert result["parameters"]["setups"][-1] == "capitulation"
+    cap_signals = [s for s in result["signals"] if s["symbol"] == "AAA" and s["setup_id"] == "capitulation"]
+    assert len(cap_signals) == 1
+    signal = cap_signals[0]
+    assert "forward" in signal and signal["forward"] is not None
+    assert "invalidation_breached" in signal and signal["invalidation_breached"] is not None
+    assert result["summary"]["capitulation:long"]["to_close"]["signals"]["n"] == 1
+    assert result["baseline_anchors"]["capitulation:long"]
+
+
+def test_euphoria_marker_never_appears_in_any_signal_pool_or_summary_key(tmp_path, bar_store):
+    """TC-4: the structural guard, proven against a REAL firing (not just a source scan) -- a
+    session that fires ONLY the euphoria marker (the exact mirror-UP of the capitulation fixture
+    above) records zero signals for that symbol, and `"euphoria"` never appears anywhere in the
+    result: not as a `setup_id`, not as a `signal_pool`/`baseline_anchors`/`summary` key
+    component."""
+    universe_store = _register_universe(tmp_path, ["EUP1"])
+    _plant_baseline_sessions(bar_store, "EUP1")
+    bars_5m = [
+        _bar("EUP1", "5m", E_OPEN, 95.9, 96.1, 95.7, 96.0, 1000),
+        _bar("EUP1", "5m", E_OPEN + 300.0, 96.0, 97.6, 95.9, 97.5, 1000),
+        _bar("EUP1", "5m", E_OPEN + 600.0, 97.5, 99.1, 97.4, 99.0, 1200),
+        _bar("EUP1", "5m", E_OPEN + 900.0, 99.0, 100.7, 98.9, 100.5, 2500),
+        _bar("EUP1", "5m", E_OPEN + 1200.0, 100.4, 100.6, 98.5, 98.9, 1000),
+        _bar("EUP1", "5m", E_OPEN + 1500.0, 98.9, 99.1, 98.6, 99.0, 900),
+    ]
+    _plant(bar_store, "EUP1", "5m", bars_5m)
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    assert [s["symbol"] for s in result["signals"] if s["symbol"] == "EUP1"] == []
+    assert not any(s["setup_id"] == "euphoria" for s in result["signals"])
+    assert not any("euphoria" in key for key in result["summary"])
+    assert not any("euphoria" in key for key in result["baseline_anchors"])
+    assert not any(a.get("symbol") == "euphoria" for a in result["absences"])
+
+
+def _plant_decoration_baseline_sessions(bar_store: BarStore, symbol: str, slots: int = 9) -> None:
+    """9 slots (not the shared 6) -- the marker-decoration fixture below needs slots 0-8 for a
+    same-session euphoria marker (slot 4) followed by an independent, later capitulation firing
+    (slot 8), so it needs its own longer baseline planter (the `_plant_ladder_baseline_sessions`
+    precedent)."""
+    bars = []
+    for day in _BASELINE_DATES:
+        day_open = E_OPEN - (22 - int(day[-2:])) * 86_400.0
+        for slot in range(slots):
+            bars.append(_bar(symbol, "5m", day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
+    _plant(bar_store, symbol, "5m", bars)
+
+
+def test_a_later_capitulation_signal_is_decorated_euphoria_recent_by_an_earlier_marker(
+    tmp_path, bar_store,
+):
+    """TC-3: ONE session, real end-to-end -- an early euphoria mirror-formation (marker trigger at
+    slot 4) followed within `PLAYBOOK_MARKER_DECAY_BARS` (6) bars by an independent, LATER
+    capitulation formation (trigger at slot 8) -- the capitulation signal renders with
+    `disclosures.euphoria_recent == True`, and the signals table contains no `"euphoria"` row of
+    any kind."""
+    universe_store = _register_universe(tmp_path, ["DECOR"])
+    _plant_decoration_baseline_sessions(bar_store, "DECOR")
+    bars_5m = [
+        _bar("DECOR", "5m", E_OPEN, 95.9, 96.1, 95.7, 96.0, 1000),
+        _bar("DECOR", "5m", E_OPEN + 300.0, 96.0, 97.6, 95.9, 97.5, 1000),
+        _bar("DECOR", "5m", E_OPEN + 600.0, 97.5, 99.1, 97.4, 99.0, 1200),
+        _bar("DECOR", "5m", E_OPEN + 900.0, 99.0, 100.7, 98.9, 100.5, 2500),  # euphoria climax
+        _bar("DECOR", "5m", E_OPEN + 1200.0, 100.4, 100.6, 98.5, 98.9, 1000),  # euphoria trigger (slot 4)
+        _bar("DECOR", "5m", E_OPEN + 1500.0, 98.9, 99.0, 96.5, 97.0, 1000),
+        _bar("DECOR", "5m", E_OPEN + 1800.0, 97.0, 97.2, 95.0, 95.5, 1000),
+        _bar("DECOR", "5m", E_OPEN + 2100.0, 94.0, 94.2, 92.8, 93.5, 2600),  # capitulation climax
+        _bar("DECOR", "5m", E_OPEN + 2400.0, 93.0, 94.5, 93.0, 94.0, 1000),  # capitulation trigger (slot 8)
+    ]
+    _plant(bar_store, "DECOR", "5m", bars_5m)
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    assert not any(s["setup_id"] == "euphoria" for s in result["signals"])
+    cap_signals = [s for s in result["signals"] if s["setup_id"] == "capitulation"]
+    assert len(cap_signals) == 1
+    assert cap_signals[0]["geometry"]["slots_to_break"] == 8
+    assert cap_signals[0]["disclosures"]["euphoria_recent"] is True
+    assert cap_signals[0]["disclosures"]["capitulation_recent"] is False
+
+
+# --- TC-9 / TC-10: J-05's own setups-tuple re-key, mirroring the J-04 precedent above --------------
+
+
+def test_j05_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file(
+    tmp_path, bar_store, universe_store, monkeypatch,
+):
+    """Simulates 'a file already recorded under the pre-J-05, 5-setup parameters' by monkeypatching
+    `PLAYBOOK_SETUPS` down to its J-04-era value for ONE recording -- `_record_aaa`'s own 6-bar
+    session is too short for `capitulation` to ever fire regardless of which code computed it (its
+    own vertical-move window alone needs 4+ bars before any trigger), so this isolates exactly the
+    ONE thing this iteration changed for an already-recorded file's own inputs: the parameters
+    blob's `setups` list, and therefore the signature.
+
+    TC-9: the pre-J-05 file's own bytes on disk are UNCHANGED by a fresh, post-J-05 compute over
+    the identical inputs. TC-10: that fresh compute mints a genuinely NEW record (new signature,
+    new id) beside the old one -- re-keying, never rewriting -- and the OR-break signal's own
+    CONTENT (not its signature) is unaffected."""
+    monkeypatch.setattr(
+        desk_playbook_module, "PLAYBOOK_SETUPS",
+        ("open_high_break", "open_low_break", "jbe", "dbi", "cup_handle"),
+    )
+    pre_j05_store, pre_j05_meta = _record_aaa(tmp_path, bar_store, universe_store)
+    pre_j05_path = pre_j05_store._path(pre_j05_meta["id"])
+    pre_j05_sha = _sha256_file(pre_j05_path)
+    assert pre_j05_meta["parameters"]["setups"] == [
+        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle",
+    ]
+
+    monkeypatch.undo()  # restore this iteration's real 6-setup PLAYBOOK_SETUPS
+
+    current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert current_result["parameters"]["setups"] == [
+        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
+    ]
+    assert current_result["playbook_input_signature"] != pre_j05_meta["playbook_input_signature"]
+
+    current_meta = pre_j05_store.record(**current_result)
+    assert current_meta["id"] != pre_j05_meta["id"]
+
+    # TC-9: the pre-J-05 file is byte-identical, untouched by the second, differently-keyed write.
+    assert _sha256_file(pre_j05_path) == pre_j05_sha
+    assert pre_j05_store.get(pre_j05_meta["id"]) == pre_j05_meta
+
+    # TC-10: both versions are now recorded for this date; newest is the current-code one.
+    newest, versions = pre_j05_store.newest_for_date(SESSION_DATE)
+    assert versions == 2
+    assert newest["id"] == current_meta["id"]
+
+    # The OR-break signal's own CONTENT is unaffected by the new setups tuple joining the
+    # parameters blob -- zero behavior change to the families J-01 through J-04 already shipped.
+    pre_j05_or_signals = [
+        s for s in pre_j05_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
+    ]
+    current_or_signals = [
+        s for s in current_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
+    ]
+    assert pre_j05_or_signals == current_or_signals
+
+
+# --- TC-8: the widened PLAYBOOK_REGISTER pinned exactly, with a mandatory rationale paragraph ------
+#
+# goal-playbook-iter-5 (J-05): PLAYBOOK_REGISTER's opening clause widens from "opening-range-break
+# signals" to name every shipped setup family (open-range breaks, jump-base-explosion,
+# drop-base-implosion, cup-and-handle, capitulation) -- closing the OPEN minor anti-goal violation
+# iter-4's own evaluator/audit carried forward (the register/blurb text had silently drifted out of
+# sync with J-04's own continuation-family launch). This is a PINNED, exact-string assertion so the
+# NEXT widening (J-06, adding range_trade/double_top/double_bottom) fails LOUDLY here rather than
+# silently leaving the served register out of date again -- whoever adds a family must deliberately
+# re-derive this constant (and this rationale paragraph), never just extend `PLAYBOOK_SETUPS` in
+# isolation.
+_EXPECTED_PLAYBOOK_REGISTER = (
+    "pre-registered opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, "
+    "and capitulation signals detected on the desk's own recorded 5m/1m bars — every threshold is "
+    "fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
+    "A signal is a recorded observation, not advice: invalidation_price is the book's own "
+    "structural level, disclosed as geometry, never a stop order, a size, or an account concept. "
+    "Each signal's forward block is measured with the desk forward rail's own conventions — "
+    "trading-bar horizons, dual max drawdown, truncation honesty — anchored at the entry already "
+    "decided at detection time, never recomputed a second way; invalidation_breached discloses "
+    "whether price ever traded through that structural level, never an exit model; baseline_anchors "
+    "and summary compare every signal against the SAME math anchored at seeded random minutes of "
+    "the same session. A record computed before this measurement pass existed carries an honest "
+    "absence instead — no fills, no costs, and no probability, expectancy, edge, or significance "
+    "claim are made anywhere on this payload"
+)
+
+
+def test_playbook_register_pinned_text_names_every_shipped_setup_family():
+    """TC-8: the widened PLAYBOOK_REGISTER matches EXACTLY (see the rationale paragraph above) --
+    zero tolerance for a family being added to PLAYBOOK_SETUPS without this string being
+    deliberately re-derived alongside it."""
+    assert PLAYBOOK_REGISTER == _EXPECTED_PLAYBOOK_REGISTER
+    assert find_violations(PLAYBOOK_REGISTER) == []
diff --git a/apps/backend/tests/test_desk_playbook_detect.py b/apps/backend/tests/test_desk_playbook_detect.py
index 9cfa53f..93d0752 100644
--- a/apps/backend/tests/test_desk_playbook_detect.py
+++ b/apps/backend/tests/test_desk_playbook_detect.py
@@ -33,8 +33,10 @@ import pytest
 from app.providers.adapters.base import RawBar
 from app.research.desk_playbook import playbook_parameters
 from app.research.desk_playbook_detect import (
+    detect_capitulation,
     detect_cup_handle,
     detect_dbi,
+    detect_euphoria,
     detect_jbe,
     detect_opening_range_breaks,
 )
@@ -779,3 +781,236 @@ def test_cup_handle_mutating_a_bar_after_the_trigger_changes_nothing():
         mutated, _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
     )
     assert mutated_result == full
+
+
+# === J-05: the climax family -- capitulation (TC-1, TC-2, TC-6, TC-7) / euphoria marker (TC-3) ====
+#
+# A 4-bar reference-then-decline leg (slot 0 the pre-window close reference, slots 1-3 the
+# `PLAYBOOK_VERTICAL_WINDOW_BARS`-bar vertical decline itself, climax bar at slot 3 with the
+# volume surge `vertical_move`'s `require_volume` clause needs) followed by a trigger bar at slot 4
+# whose high exceeds slot 3's own high -- values hand-computed and cross-checked by direct
+# execution (this module's own convention, per the JBE/DBI/cup_handle fixtures above).
+
+_CAPITULATION_BASELINE = {
+    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(9)},
+}
+
+
+def _canonical_capitulation_bars(symbol: str = "CAP1") -> list[RawBar]:
+    """No re-anchoring: the climax bar (slot 3) already holds the session's lowest low, and slot
+    4's low never dips below it -- the re-anchoring fixture right below this one is the ONE that
+    exercises the "a new low after v re-anchors v" clause."""
+    return [
+        _bar(symbol, E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
+        _bar(symbol, E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),  # window start (slot 1)
+        _bar(symbol, E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
+        _bar(symbol, E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),  # climax (slot 3), RVOL surge
+        _bar(symbol, E_OPEN + 1200.0, 99.6, 101.5, 99.4, 101.0, 1000),  # trigger: breaks high[3]=101.1
+        _bar(symbol, E_OPEN + 1500.0, 101.0, 101.3, 100.8, 101.1, 900),
+        _bar(symbol, E_OPEN + 1800.0, 101.1, 101.4, 100.9, 101.2, 900),
+    ]
+
+
+def test_canonical_capitulation_matches_the_hand_computed_signal():
+    """TC-1: the canonical capitulation firing -- setup chip, side, and every geometry field
+    hand-verified (values confirmed by direct execution against the fixture)."""
+    signal = detect_capitulation(
+        _canonical_capitulation_bars(), _CAPITULATION_BASELINE, "CAP1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert signal is not None
+    assert signal["setup_id"] == "capitulation"
+    assert signal["side"] == "long"
+    assert signal["trigger_price"] == pytest.approx(101.1)
+    assert signal["entry"] == pytest.approx(101.1)
+    assert signal["entry_kind"] == "level"
+    assert signal["price_low"] == pytest.approx(99.3)
+    assert signal["price_high"] == pytest.approx(101.1)
+    assert signal["invalidation_price"] == pytest.approx(98.76)
+    geometry = signal["geometry"]
+    assert geometry["slots_to_break"] == 4
+    assert geometry["decline_mbr"] == pytest.approx(4.7)
+    assert geometry["decline_bars"] == 3
+    assert geometry["climax_rvol"] == pytest.approx(2.5)
+    assert geometry["bars_from_climax_to_trigger"] == 1
+    assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(1.0)
+    assert signal["volume"]["approach_rvol_max"] == pytest.approx(2.5)
+    assert signal["principles"] == ["P1"]
+    assert signal["disclosures"]["bars_to_close"] == 2
+    assert signal["disclosures"]["concurrent_signals"] == []
+    assert signal["disclosures"]["euphoria_recent"] is False
+    assert signal["disclosures"]["capitulation_recent"] is False
+
+
+def _reanchoring_capitulation_bars(symbol: str = "REANCH") -> list[RawBar]:
+    """TC-7: identical through the raw climax candidate at slot 3, but slot 4 makes a NEW, lower
+    low (98.5 < the raw climax's own 99.3) WITHOUT triggering -- the panic still running -- before
+    slot 5 finally triggers. `leg_low`/the disclosed `decline_*`/`climax_rvol` fields must reflect
+    the RE-ANCHORED slot-4 climax, never the original slot-3 one."""
+    return [
+        _bar(symbol, E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
+        _bar(symbol, E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),
+        _bar(symbol, E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
+        _bar(symbol, E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),  # raw climax candidate
+        _bar(symbol, E_OPEN + 1200.0, 99.4, 100.0, 98.5, 98.8, 1500),  # NEW low, no trigger yet
+        _bar(symbol, E_OPEN + 1500.0, 98.9, 100.6, 98.6, 100.2, 1000),  # trigger: breaks high[4]=100.0
+        _bar(symbol, E_OPEN + 1800.0, 100.2, 100.5, 100.0, 100.3, 900),
+    ]
+
+
+def test_capitulation_re_anchors_the_climax_bar_when_a_new_low_forms_before_any_trigger():
+    """TC-7: the re-anchored climax (slot 4, low=98.5) drives `leg_low`/`decline_bars`/
+    `decline_mbr`/`climax_rvol`/`trigger_price`/`invalidation_price` -- NOT the original slot-3
+    candidate's own values (which the canonical fixture above already proves as a contrast)."""
+    signal = detect_capitulation(
+        _reanchoring_capitulation_bars(), _CAPITULATION_BASELINE, "REANCH", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert signal is not None
+    geometry = signal["geometry"]
+    assert geometry["slots_to_break"] == 5  # trigger, not the (re-anchored) climax bar itself
+    assert signal["price_low"] == pytest.approx(98.5)  # re-anchored leg_low, not 99.3
+    assert geometry["decline_bars"] == 4  # extended by the re-anchoring, not the raw window's 3
+    assert geometry["decline_mbr"] == pytest.approx(5.5)
+    assert geometry["climax_rvol"] == pytest.approx(1.5)  # RVOL of the RE-ANCHORED bar (1500/1000)
+    assert geometry["bars_from_climax_to_trigger"] == 1
+    assert signal["trigger_price"] == pytest.approx(100.0)  # high[4], the re-anchored climax's high
+    assert signal["invalidation_price"] == pytest.approx(98.05)
+
+
+# --- TC-2: the near-miss fixture (meets the vertical-move/RVOL-surge gates, never reverses in the
+# window) paired with the gate-relaxed control -- proves the bounce-window gate SPECIFICALLY is
+# what rejects it (the iter-4 lesson: a "must not fire" fixture can pass for the wrong reason).
+
+
+def _capitulation_near_miss_bars(symbol: str = "NM1") -> list[RawBar]:
+    """The SAME climax formation as the canonical fixture (slots 0-3), but every subsequent bar's
+    high stays BELOW the immediately preceding bar's own high through slot 6 (`t - v > bounce_max`
+    at slot 7, so the walk expires before slot 7's own high -- which WOULD exceed slot 6's -- is
+    ever checked). Nothing else about the formation is disturbed."""
+    return [
+        _bar(symbol, E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
+        _bar(symbol, E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),
+        _bar(symbol, E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
+        _bar(symbol, E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),  # climax (slot 3), high=101.1
+        _bar(symbol, E_OPEN + 1200.0, 99.4, 101.0, 99.35, 99.6, 1000),  # high 101.0, not > 101.1
+        _bar(symbol, E_OPEN + 1500.0, 99.5, 100.9, 99.4, 99.7, 1000),  # high 100.9, not > 101.0
+        _bar(symbol, E_OPEN + 1800.0, 99.6, 100.8, 99.5, 99.8, 1000),  # high 100.8, not > 100.9
+        # slot 7: high 101.0 WOULD exceed slot 6's 100.8 -- but t-v=4 > bounce_max=3 by then.
+        _bar(symbol, E_OPEN + 2100.0, 99.7, 101.0, 99.55, 100.8, 1000),
+    ]
+
+
+def test_capitulation_near_miss_no_reversal_within_the_bounce_window_fires_no_signal():
+    """TC-2: the formation expires silently -- no signal, regardless of what a later bar's high
+    does. The control below relaxes ONLY `bounce_max_bars` and proves that gate, specifically, is
+    what rejected it (every other gate -- the vertical move, the RVOL surge -- already passed)."""
+    bars = _capitulation_near_miss_bars()
+    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(8)}}
+    signal = detect_capitulation(
+        bars, baseline, "NM1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert signal is None
+
+    relaxed = {**_PARAMS, "bounce_max_bars": 10}
+    relaxed_signal = detect_capitulation(
+        bars, baseline, "NM1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, relaxed,
+    )
+    assert relaxed_signal is not None
+    assert relaxed_signal["geometry"]["slots_to_break"] == 7
+    assert relaxed_signal["geometry"]["bars_from_climax_to_trigger"] == 4
+    assert relaxed_signal["geometry"]["bars_from_climax_to_trigger"] > _PARAMS["bounce_max_bars"]
+
+
+# --- TC-6 / TC-7: the truncate/mutate lookahead property test, for capitulation ------------------
+
+
+def test_capitulation_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields():
+    """TC-6: extends the generic truncation-invariance property (own direct test, mirroring
+    ``detect_cup_handle``'s own truncate/mutate pair, since ``detect_capitulation`` is a
+    single-return detector like ``detect_cup_handle`` rather than a list-returning one)."""
+    bars = _canonical_capitulation_bars()
+    full = detect_capitulation(
+        bars, _CAPITULATION_BASELINE, "CAP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert full is not None
+    trigger_idx = full["geometry"]["slots_to_break"]
+
+    truncated = detect_capitulation(
+        bars[: trigger_idx + 1], _CAPITULATION_BASELINE, "CAP1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert truncated is not None
+    assert truncated["trigger_price"] == full["trigger_price"]
+    assert truncated["invalidation_price"] == full["invalidation_price"]
+    assert truncated["geometry"] == full["geometry"]
+
+
+def test_capitulation_mutating_a_bar_after_the_trigger_changes_nothing():
+    """TC-7: mutation-invariance for capitulation."""
+    bars = _canonical_capitulation_bars()
+    full = detect_capitulation(
+        bars, _CAPITULATION_BASELINE, "CAP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert full is not None
+    trigger_idx = full["geometry"]["slots_to_break"]
+    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"
+
+    mutated = list(bars)
+    victim = mutated[trigger_idx + 1]
+    mutated[trigger_idx + 1] = RawBar(
+        victim.symbol, victim.timeframe, victim.epoch,
+        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
+    )
+    mutated_result = detect_capitulation(
+        mutated, _CAPITULATION_BASELINE, "CAP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert mutated_result == full
+
+
+# --- TC-3: detect_euphoria -- a marker event only, never a served signal shape ---------------------
+
+
+def _canonical_euphoria_bars(symbol: str = "EUP1") -> list[RawBar]:
+    """The exact mirror UP of ``_canonical_capitulation_bars``: a vertical RALLY into a climax bar
+    (slot 3), then a first-strength reversal DOWN at slot 4 (``low < low[3]``) -- the euphoria
+    marker's own trigger."""
+    return [
+        _bar(symbol, E_OPEN, 95.9, 96.1, 95.7, 96.0, 1000),
+        _bar(symbol, E_OPEN + 300.0, 96.0, 97.6, 95.9, 97.5, 1000),
+        _bar(symbol, E_OPEN + 600.0, 97.5, 99.1, 97.4, 99.0, 1200),
+        _bar(symbol, E_OPEN + 900.0, 99.0, 100.7, 98.9, 100.5, 2500),  # climax (slot 3)
+        _bar(symbol, E_OPEN + 1200.0, 100.4, 100.6, 98.5, 98.9, 1000),  # trigger: low < low[3]=98.9
+        _bar(symbol, E_OPEN + 1500.0, 98.9, 99.1, 98.6, 99.0, 900),
+    ]
+
+
+_EUPHORIA_BASELINE = {
+    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(6)},
+}
+
+
+def test_canonical_euphoria_fires_a_marker_event_only():
+    """TC-3: the euphoria marker's only output is its own trigger-bar index -- no side, no entry,
+    no invalidation, no geometry, no setup_id (structurally incapable of becoming a served signal
+    row)."""
+    marker = detect_euphoria(_canonical_euphoria_bars(), _EUPHORIA_BASELINE, _PARAMS)
+    assert marker == {"trigger_idx": 4}
+    assert set(marker.keys()) == {"trigger_idx"}
+
+
+def test_euphoria_near_miss_no_reversal_within_the_bounce_window_fires_no_marker():
+    """The mirrored error case: a euphoric rally that meets the vertical-move/RVOL-surge gates but
+    never produces a downside reversal bar within ``PLAYBOOK_BOUNCE_MAX_BARS`` emits no marker."""
+    bars = [
+        _bar("EUPNM", E_OPEN, 95.9, 96.1, 95.7, 96.0, 1000),
+        _bar("EUPNM", E_OPEN + 300.0, 96.0, 97.6, 95.9, 97.5, 1000),
+        _bar("EUPNM", E_OPEN + 600.0, 97.5, 99.1, 97.4, 99.0, 1200),
+        _bar("EUPNM", E_OPEN + 900.0, 99.0, 100.7, 98.9, 100.5, 2500),  # climax
+        _bar("EUPNM", E_OPEN + 1200.0, 100.4, 100.6, 98.95, 100.5, 1000),  # low not < 98.9
+        _bar("EUPNM", E_OPEN + 1500.0, 100.4, 100.5, 99.0, 100.3, 1000),  # low not < prior
+        _bar("EUPNM", E_OPEN + 1800.0, 100.2, 100.4, 99.1, 100.2, 1000),  # low not < prior
+    ]
+    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(7)}}
+    marker = detect_euphoria(bars, baseline, _PARAMS)
+    assert marker is None
diff --git a/apps/backend/tests/test_desk_playbook_guards.py b/apps/backend/tests/test_desk_playbook_guards.py
index eaa4378..68f018b 100644
--- a/apps/backend/tests/test_desk_playbook_guards.py
+++ b/apps/backend/tests/test_desk_playbook_guards.py
@@ -1,6 +1,10 @@
-"""goal-playbook-iter-4 (J-04) -- two new structural guards, source-introspection style (the
+"""goal-playbook-iter-4 (J-04) -- two structural guards, source-introspection style (the
 ``test_copy_discipline.py``/``test_desk_ui_guards.py`` pattern: read a module as TEXT, assert on
-substrings/regex; no runtime, no import-time side effects beyond reading the file).
+substrings/regex; no runtime, no import-time side effects beyond reading the file). Extended by
+goal-playbook-iter-5 (J-05) with two MORE guards -- this time behavioral rather than source-scan,
+since "does the euphoria marker ever leak into a served row" and "is marker decoration
+forward-only" are properties of DATA the decoration pass produces, not of code SHAPE a regex could
+usefully police.
 
 (a) TC-12 -- the no-threshold-sweep guard: no playbook module (``desk_playbook.py``,
     ``desk_playbook_detect.py``, ``desk_playbook_features.py``) contains a ``for``/comprehension
@@ -18,7 +22,11 @@ substrings/regex; no runtime, no import-time side effects beyond reading the fil
     single-source-of-truth discipline (the evidence view reads recorded playbook FILES, it must
     never let a detector reach into it).
 
-Both guards carry a seeded counter-test (the ``test_copy_discipline.py`` precedent: "a lint that
+(c) TC-5 -- the marker-decoration forward-only guard: ``desk_playbook._decorate_markers`` never
+    decorates a signal whose own trigger bar is AT OR BEFORE a marker's trigger bar, and a
+    ``capitulation`` signal never self-decorates its own firing.
+
+Every guard carries a seeded counter-test (the ``test_copy_discipline.py`` precedent: "a lint that
 can never fail proves nothing")."""
 
 from __future__ import annotations
@@ -29,6 +37,7 @@ import re
 from app.research import desk_playbook as desk_playbook_module
 from app.research import desk_playbook_detect as desk_playbook_detect_module
 from app.research import desk_playbook_features as desk_playbook_features_module
+from app.research.desk_playbook import _decorate_markers, playbook_parameters
 
 _PLAYBOOK_MODULES = (
     desk_playbook_module,
@@ -203,3 +212,93 @@ def test_desk_playbook_evidence_module_does_not_exist_yet():
         _repo_root() / "apps" / "backend" / "app" / "research" / "desk_playbook_evidence.py"
     )
     assert not evidence_path.exists()
+
+
+# --- (c) TC-5 -- the marker-decoration forward-only guard (goal-playbook-iter-5, J-05) -------------
+#
+# ``_decorate_markers`` operates on already-built signal dicts (``geometry.slots_to_break`` +
+# ``disclosures``), so this guard tests it DIRECTLY as a pure function -- no ``BarStore``, no real
+# detector firing needed to prove the property; ``test_desk_playbook.py``'s own
+# ``test_a_later_capitulation_signal_is_decorated_euphoria_recent_by_an_earlier_marker`` separately
+# proves the SAME property end to end through a real ``compute_playbook`` walk.
+
+_PARAMS = playbook_parameters()
+
+
+def _signal(setup_id: str, slots_to_break: int) -> dict:
+    return {
+        "setup_id": setup_id,
+        "geometry": {"slots_to_break": slots_to_break},
+        "disclosures": {"euphoria_recent": False, "capitulation_recent": False},
+    }
+
+
+def test_decorate_markers_sets_euphoria_recent_on_a_later_signal_within_the_decay_window():
+    """The baseline positive case: a marker at slot 7 decorates a signal triggering at slot 10 --
+    ``10 - 7 == 3 <= PLAYBOOK_MARKER_DECAY_BARS`` (6)."""
+    signals = [_signal("open_high_break", 10)]
+    _decorate_markers(signals, [7], _PARAMS)
+    assert signals[0]["disclosures"]["euphoria_recent"] is True
+    assert signals[0]["disclosures"]["capitulation_recent"] is False
+
+
+def test_decorate_markers_never_decorates_a_signal_that_triggered_at_or_before_the_marker():
+    """TC-5: the forward-only property, both edges -- a marker whose OWN trigger bar occurs AFTER
+    a candidate signal's trigger bar (in bar-index order) decorates NOTHING (the EARLIER signal
+    stays undecorated), and a marker at the EXACT same bar as a signal's own trigger (the
+    zero-distance edge) also does not decorate it -- ``euphoria_recent``/``capitulation_recent``
+    require the signal's trigger to be STRICTLY after the marker's, never merely at-or-after."""
+    earlier_signal = _signal("jbe", 5)
+    _decorate_markers([earlier_signal], [8], _PARAMS)  # marker AFTER the signal's own trigger
+    assert earlier_signal["disclosures"]["euphoria_recent"] is False
+
+    same_bar_signal = _signal("dbi", 6)
+    _decorate_markers([same_bar_signal], [6], _PARAMS)  # marker AT the signal's own trigger bar
+    assert same_bar_signal["disclosures"]["euphoria_recent"] is False
+
+
+def test_decorate_markers_beyond_the_decay_window_does_not_decorate():
+    """A marker more than ``PLAYBOOK_MARKER_DECAY_BARS`` bars before a later signal's trigger does
+    not decorate it either -- the window has a far edge, not just a near one. A signal exactly AT
+    the decay boundary (distance == decay) still IS decorated -- the window is inclusive on its
+    far edge, so this test also proves the boundary itself is not accidentally off-by-one."""
+    decay = _PARAMS["marker_decay_bars"]
+    marker = 10
+    at_boundary = _signal("cup_handle", marker + decay)
+    _decorate_markers([at_boundary], [marker], _PARAMS)
+    assert at_boundary["disclosures"]["euphoria_recent"] is True
+
+    beyond_boundary = _signal("cup_handle", marker + decay + 1)
+    _decorate_markers([beyond_boundary], [marker], _PARAMS)
+    assert beyond_boundary["disclosures"]["euphoria_recent"] is False
+
+
+def test_decorate_markers_capitulation_signal_decorates_later_signals_but_never_itself():
+    """spec §3.5: "capitulation events symmetrically set capitulation_recent" -- a recorded
+    ``capitulation`` signal is itself a marker for every OTHER later signal in the SAME walk, but
+    the strict-after comparison makes self-decoration structurally impossible (a signal's own
+    trigger bar index is never strictly after itself) -- no special-case exclusion needed, proven
+    here rather than merely asserted."""
+    capitulation_signal = _signal("capitulation", 4)
+    later_signal = _signal("jbe", 6)
+    signals = [capitulation_signal, later_signal]
+    _decorate_markers(signals, [], _PARAMS)  # no euphoria marker this walk
+    assert capitulation_signal["disclosures"]["capitulation_recent"] is False  # never self-decorates
+    assert later_signal["disclosures"]["capitulation_recent"] is True  # decorated by the earlier one
+
+
+def test_decorate_markers_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing. A deliberately WRONG
+    implementation (at-or-after instead of strictly-after) would decorate the same-bar case; this
+    test proves the counter-scenario itself is a real trigger for the assertion style above, not a
+    vacuous no-op."""
+    signal = _signal("open_low_break", 6)
+    # Manually simulate the WRONG (at-or-after) rule to confirm it WOULD decorate -- i.e. the
+    # correct, strict rule this module actually implements is doing real work, not passing by
+    # construction regardless of the comparison operator used.
+    marker = 6
+    wrongly_decorates = 0 <= signal["geometry"]["slots_to_break"] - marker <= _PARAMS["marker_decay_bars"]
+    assert wrongly_decorates is True
+    # ... yet the REAL function does not:
+    _decorate_markers([signal], [marker], _PARAMS)
+    assert signal["disclosures"]["euphoria_recent"] is False
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 0bfe310..69fdf7b 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -161,6 +161,10 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
 # own NEW `signal.geometry.*` numerics -- `PlaybookSignalDetail`'s two new setup-branches render
 # every one of these verbatim (base/jump geometry + ladder-step-ratio; cup/handle geometry + the
 # three RVOL medians), never a client-recomputed spread or ratio.
+# goal-playbook-iter-5 (J-05): extended AGAIN for capitulation's own NEW `signal.geometry.*`
+# numerics -- `PlaybookSignalDetail`'s capitulation branch renders `decline_mbr`/`climax_rvol`/
+# `bars_from_climax_to_trigger` verbatim (`decline_bars` is a plain bar count, like `base_bars`/
+# `cup_bars` before it, so it stays outside this price-arithmetic list by the same precedent).
 _PRICE_ARITHMETIC_FIELDS = (
     r"row\.(?:distance_bps|price_low|price_high|reference_close"
     r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
@@ -174,7 +178,7 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|signal\.(?:trigger_price|invalidation_price)"
     r"|geometry\.(?:jump_mbr|base_range_mbr|ladder_step_ratio|cup_depth_mbr|handle_retrace_frac"
     r"|handle_duration_frac|cup_middle_third_rvol_median|cup_outer_third_rvol_median"
-    r"|handle_rvol_median)"
+    r"|handle_rvol_median|decline_mbr|climax_rvol|bars_from_climax_to_trigger)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -298,6 +302,16 @@ def test_desk_page_price_arithmetic_guard_catches_continuation_and_cup_handle_fi
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_handle_rvol) is not None
 
 
+def test_desk_page_price_arithmetic_guard_catches_capitulation_field_arithmetic():
+    """goal-playbook-iter-5 (J-05) counter-test: the extended guard catches arithmetic on
+    capitulation's own NEW `geometry.*` bindings."""
+    seeded_decline = "const net = geometry.decline_mbr - geometry.climax_rvol;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_decline) is not None
+
+    seeded_bars = "const pace = geometry.bars_from_climax_to_trigger * 5;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bars) is not None
+
+
 # goal-playbook-iter-4 audit (F1): `base_lows_ascending` is ONE served field name carrying the
 # direction-appropriate triangle check underneath (non-decreasing LOWS for `jbe`, non-increasing
 # HIGHS for `dbi` -- see `desk_playbook_detect._base_lows_ascending`). The continuation geometry
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index d269c23..f45b5cf 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -4404,6 +4404,7 @@ function playbookSetupLabel(setupId: string): string {
   if (setupId === "jbe") return "Jump-Base Explosion";
   if (setupId === "dbi") return "Drop-Base Implosion";
   if (setupId === "cup_handle") return "Cup and Handle";
+  if (setupId === "capitulation") return "Capitulation";
   return setupId;
 }
 
@@ -4628,6 +4629,16 @@ function PlaybookSignalDetail({
           {fmt(geometry.handle_rvol_median)}
         </p>
       )}
+      {/* goal-playbook-iter-5 (J-05): capitulation's own geometry line -- the vertical decline's
+          magnitude/duration, the (possibly re-anchored) climax bar's RVOL, and how many bars the
+          first-strength reversal came after it, all rendered verbatim from the served payload. */}
+      {signal.setup_id === "capitulation" && (
+        <p data-testid="desk-playbook-signal-capitulation-geometry" className="mt-1 text-[11px] text-slate-500">
+          decline {fmt(geometry.decline_mbr)} MBR over {geometry.decline_bars} bar(s) · climax RVOL{" "}
+          {fmt(geometry.climax_rvol)} · reversal {geometry.bars_from_climax_to_trigger} bar(s) after
+          climax · broke at slot {geometry.slots_to_break}
+        </p>
+      )}
       <p className="mt-1 text-[11px] text-slate-500">
         volume: {volume.spike_into_trigger_verdict}
         {volume.rvol_trigger_bar !== null && ` · trigger RVOL ${fmt(volume.rvol_trigger_bar)}`}
@@ -4979,7 +4990,8 @@ function PlaybookRecordView({
       >
         <p className="text-sm font-medium text-amber-300">Playbook not computed for this session.</p>
         <p className="mt-1 text-xs text-amber-200/70">
-          Run Playbook detects and measures the opening-range-break family on{" "}
+          Run Playbook detects and measures the opening-range-break, jump-base-explosion,
+          drop-base-implosion, cup-and-handle, and capitulation families on{" "}
           {control.sessionDate}&apos;s own recorded bars — an explicit operator act, nothing runs on
           page load.
         </p>
@@ -5076,7 +5088,8 @@ function PlaybookSection({
   return (
     <div data-testid="desk-playbook-section" className="space-y-3">
       <p className="max-w-3xl text-sm text-slate-500">
-        The book&apos;s opening-range-break signals, detected on this session&apos;s own recorded
+        The book&apos;s opening-range-break, jump-base-explosion, drop-base-implosion,
+        cup-and-handle, and capitulation signals, detected on this session&apos;s own recorded
         5m/1m bars and measured with the desk forward rail&apos;s own conventions — read verbatim
         from GET /research/desk/playbook. Nothing here is recomputed in the browser.
       </p>
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 2fd6216..954a8e0 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1482,6 +1482,9 @@ export interface DeskForwardComputeSnapshot {
 // geometry shape on the SAME `signal.geometry` object (one owner, `desk_playbook_detect.py`, per
 // setup). `slots_to_break` is the one field every setup serves (it is what `_measure_signal`
 // anchors on) -- it stays required.
+// goal-playbook-iter-5 (J-05): `capitulation` adds its own four fields below the same way --
+// `euphoria` never appears here at all (it is a marker, never a served signal -- see
+// `DeskPlaybookDisclosures.euphoria_recent` for its only visible trace).
 export interface DeskPlaybookGeometry {
   slots_to_break: number;
   // open_high_break / open_low_break only (J-01)
@@ -1508,6 +1511,11 @@ export interface DeskPlaybookGeometry {
   cup_middle_third_rvol_median?: number;
   cup_outer_third_rvol_median?: number;
   handle_rvol_median?: number;
+  // capitulation only (J-05, spec §3.5)
+  decline_mbr?: number;
+  decline_bars?: number;
+  climax_rvol?: number;
+  bars_from_climax_to_trigger?: number;
 }
 
 export interface DeskPlaybookVolume {
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-playbook/telemetry.jsonl   | 7 +++++++
 runs/goal-session-playbook/trace/trace.jsonl | 1 +
 2 files changed, 8 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
