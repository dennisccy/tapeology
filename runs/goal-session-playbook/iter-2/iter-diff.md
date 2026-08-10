# Iteration diff (bounded)

Files changed: 9. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_desk_playbook.py` (7 lines not shown)
- `apps/backend/app/research/desk_playbook_compute.py` (5 lines not shown)
- `apps/backend/tests/test_desk_playbook_compute.py` (36 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_playbook.py b/apps/backend/app/research/desk_playbook.py
index 97efd1b..7793897 100644
--- a/apps/backend/app/research/desk_playbook.py
+++ b/apps/backend/app/research/desk_playbook.py
@@ -44,14 +44,21 @@ from __future__ import annotations
 import hashlib
 import json
 import os
+import random
 from datetime import datetime, timezone
 from pathlib import Path
+from typing import Callable
 
 from .desk_forward import (
     DESK_FORWARD_BASELINE_SEED,
     DESK_FORWARD_HORIZONS_MINUTES,
     DESK_FORWARD_HORIZON_MEASURES,
+    DESK_FORWARD_MAX_TOUCHES_PER_ROW,
     DESK_FORWARD_MEASURE_KEYS,
+    _avg_cell,
+    _collect_measures,
+    _draw_anchor_indices,
+    _measure_from,
 )
 from .desk_playbook_detect import detect_opening_range_breaks
 from .desk_playbook_features import baselines, opening_range, rth_session_slice
@@ -144,9 +151,14 @@ PLAYBOOK_REGISTER = (
     "every threshold is fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
     "A signal is a recorded observation, not advice: invalidation_price is the book's own "
     "structural level, disclosed as geometry, never a stop order, a size, or an account concept. "
-    "This record does not yet carry a measurement — forward returns, invalidation-breach, and the "
-    "seeded random-anchor baseline are added by a later compute pass; no fills, no costs, and no "
-    "probability, expectancy, edge, or significance claim are made anywhere on this payload"
+    "Each signal's forward block is measured with the desk forward rail's own conventions — "
+    "trading-bar horizons, dual max drawdown, truncation honesty — anchored at the entry already "
+    "decided at detection time, never recomputed a second way; invalidation_breached discloses "
+    "whether price ever traded through that structural level, never an exit model; baseline_anchors "
+    "and summary compare every signal against the SAME math anchored at seeded random minutes of "
+    "the same session. A record computed before this measurement pass existed carries an honest "
+    "absence instead — no fills, no costs, and no probability, expectancy, edge, or significance "
+    "claim are made anywhere on this payload"
 )
 
 _PLAYBOOK_DIR_ENV = "TAPEOLOGY_DESK_PLAYBOOK_DIR"
@@ -249,6 +261,14 @@ def playbook_parameters() -> dict:
         "rail_horizons_minutes": [list(pair) for pair in DESK_FORWARD_HORIZONS_MINUTES],
         "rail_baseline_seed": DESK_FORWARD_BASELINE_SEED,
         "rail_horizon_measures": list(DESK_FORWARD_HORIZON_MEASURES),
+        # J-02: the rail's own per-row touch cap, reused verbatim (never re-derived) as the
+        # per-(setup_id, side) pooling cap on baseline_anchors/summary -- bounds a pathological
+        # many-symbols-firing-the-same-setup session exactly the way it already bounds a
+        # band-hugging one, without hiding that it was one (signals_beyond_cap discloses the rest).
+        # Embedding it here is also what re-keys every J-01-era (unmeasured) record: the SAME
+        # session_date and bar content under J-02's code now hashes a DIFFERENT parameters blob, so
+        # a fresh compute mints a genuinely NEW version instead of matching the old, unmeasured one.
+        "rail_max_touches_per_row": DESK_FORWARD_MAX_TOUCHES_PER_ROW,
     }
 
 
@@ -298,11 +318,121 @@ def _prior_session_close(bars_5m: list, session_date: str) -> float | None:
     return prior_bars[-1].close if prior_bars else None
 
 
-def compute_playbook(universe_store, bar_store, config_fingerprint: str, session_date: str) -> dict:
-    """Detect the opening-range-break family for EVERY member of the latest registered universe
-    snapshot, on ``session_date``'s own recorded bars -- returns everything ``PlaybookStore.record``
-    needs minus the store-assigned ``id``/``recorded_at`` (the ``compute_forward``/``compute_screen``
-    contract shape: a PURE compute, never itself a store write).
+def _measurement_anchor(
+    session_5m: list, session_1m: list, trigger_idx_5m: int, trigger_price: float
+) -> tuple[list, int, int]:
+    """Map ONE signal's already-detected 5m trigger bar to its OWN measurement anchor on the
+    finest series ITS OWN trigger window can actually supply -- spec Sec0's 5m->1m mapping: the
+    first 1m bar of the trigger bar's own ``[epoch, epoch+300)`` window whose ``[low, high]``
+    contains the trigger price ``T``, falling back to that window's first 1m bar. A gap spanning
+    the WHOLE window (no 1m bar inside it at all) degrades THIS signal to the 5m basis rather than
+    silently borrowing a bar from a neighboring 5m window -- ``_measure_from``'s own per-horizon
+    ``reason`` field (the ``minutes % tf_minutes`` mismatch) already discloses the coarser basis
+    honestly, so no new served field is needed for the degrade itself. A session carrying no 1m
+    bars at all degrades every one of its signals the same way, for free -- "session-level, not
+    per-signal" falls out of this rule rather than needing a separate pre-check.
+
+    Returns ``(measure_bars, anchor_index, tf_minutes)`` -- the SAME series/tf a baseline anchor
+    for this signal's own (symbol, setup_id) must also use, so the null lives in the same basis as
+    what it is the null for."""
+    trigger_bar_5m = session_5m[trigger_idx_5m]
+    if not session_1m:
+        return session_5m, trigger_idx_5m, 5
+    window_start = trigger_bar_5m.epoch
+    window_end = window_start + 300.0
+    window_1m = [
+        (idx, bar) for idx, bar in enumerate(session_1m) if window_start <= bar.epoch < window_end
+    ]
+    if not window_1m:
+        return session_5m, trigger_idx_5m, 5
+    for idx, bar in window_1m:
+        if bar.low <= trigger_price <= bar.high:
+            return session_1m, idx, 1
+    first_idx, _first_bar = window_1m[0]
+    return session_1m, first_idx, 1
+
+
+def _invalidation_breached(
+    measure_bars: list,
+    anchor_index: int,
+    invalidation_price: float,
+    side: str,
+    tf_minutes: int,
+    forward: dict,
+) -> dict:
+    """The same-pass, OUTSIDE-``_measure_from`` disclosure spec Sec0 requires (so the rail's own
+    served horizon shape never changes): did price ever trade through ``invalidation_price`` from
+    the anchor bar through the session close, and -- if so -- at what bar-equivalent minute offset
+    (``first_breach_minutes``: ONE session-wide fact, the same value on every horizon leaf that
+    reaches it -- never re-derived per horizon, never a guess). A horizon key is ``True`` when the
+    first breach falls AT OR BEFORE that horizon's own already-measured ``effective_minutes``
+    (reusing ``forward``'s own truncation-honest window -- never a second, independent walk); a
+    horizon this signal could not even measure at this tf (``reason`` set, ``effective_minutes``
+    null) is vacuously ``False`` -- it never observed anything. ``to_close`` spans the whole
+    remaining session by definition, so it is ``True`` exactly when any breach was ever observed at
+    all. Long: breached when a bar's low reaches the level (below entry); short: mirrored (high)."""
+    tail = measure_bars[anchor_index:]
+    first_breach_offset: int | None = None
+    for offset, bar in enumerate(tail):
+        breached = (
+            bar.low <= invalidation_price if side == "long" else bar.high >= invalidation_price
+        )
+        if breached:
+            first_breach_offset = offset
+            break
+    first_breach_minutes = (
+        first_breach_offset * tf_minutes if first_breach_offset is not None else None
+    )
+
+    result: dict = {}
+    for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES:
+        effective = forward["horizons"][label]["effective_minutes"]
+        result[label] = (
+            first_breach_minutes is not None
+            and effective is not None
+            and first_breach_minutes <= effective
+        )
+    result["to_close"] = first_breach_minutes is not None
+    result["first_breach_minutes"] = first_breach_minutes
+    return result
+
+
+def _measure_signal(signal: dict, session_5m: list, session_1m: list) -> tuple[dict, dict, list, int]:
+    """Measure ONE already-detected signal through the rail's own ``_measure_from`` -- THE call
+    site the convention-identity test compares against a direct ``desk_forward._measure_from`` call
+    with the identical arguments. Reuses the signal's own already-detected ``entry``/``entry_kind``
+    (spec Sec0's stop-through convention, decided at J-01 detection time) and ``trigger_price``
+    verbatim -- nothing here re-derives them a second way. Returns
+    ``(forward, invalidation_breached, measure_bars, tf_minutes)`` -- the last two so the caller's
+    baseline-anchor draw for this signal's (symbol, setup_id) measures on the SAME basis."""
+    trigger_idx_5m = signal["geometry"]["slots_to_break"]
+    measure_bars, anchor_index, tf_minutes = _measurement_anchor(
+        session_5m, session_1m, trigger_idx_5m, signal["trigger_price"]
+    )
+    sign = 1.0 if signal["side"] == "long" else -1.0
+    forward = _measure_from(
+        measure_bars, anchor_index, signal["entry"], signal["entry_kind"], tf_minutes, sign
+    )
+    breached = _invalidation_breached(
+        measure_bars, anchor_index, signal["invalidation_price"], signal["side"], tf_minutes, forward
+    )
+    return forward, breached, measure_bars, tf_minutes
+
+
+def compute_playbook(
+    universe_store,
+    bar_store,
+    config_fingerprint: str,
+    session_date: str,
+    *,
+    progress: Callable[[dict], None] | None = None,
+    should_abort: Callable[[], bool] | None = None,
+) -> dict:
+    """Detect AND measure the opening-range-break family for EVERY member of the latest registered
+    universe snapshot, on ``session_date``'s own recorded bars, in the SAME walk -- returns
+    everything ``PlaybookStore.record`` needs minus the store-assigned ``id``/``recorded_at`` (the
+    ``compute_forward``/``compute_screen`` contract shape: a PURE compute, never itself a store
+    write).
 
     Session-honesty first: ``desk_sessions.refuse_if_not_a_session`` is checked before any bar is
     read for detection (no separate compute-manager/route layer exists yet this iteration, so this
@@ -310,7 +440,21 @@ def compute_playbook(universe_store, bar_store, config_fingerprint: str, session
     is walked. Per member: no 5m bars for the session, a thin/zero baseline, or no buildable opening
     range are each a disclosed ``absences`` row (never a crash, never a guess); everything else
     reaches the detector, which may add a signal, an ``ambiguous_outside_bar`` diagnostic, or
-    neither (a legitimate "the setup did not form" outcome -- not an absence)."""
+    neither (a legitimate "the setup did not form" outcome -- not an absence).
+
+    J-02: every detected signal is measured in the SAME pass -- ``_measure_signal`` attaches
+    ``forward`` (the rail's own ``_measure_from`` shape, anchored on the finest series THIS
+    signal's own trigger window can supply) and ``invalidation_breached`` (computed OUTSIDE
+    ``_measure_from``, never touching its served shape). In-cap signals (per ``(setup_id, side)``,
+    capped at the rail's own ``DESK_FORWARD_MAX_TOUCHES_PER_ROW`` -- see ``playbook_parameters``)
+    also draw ONE seeded random-anchor baseline measurement each
+    (``f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}"``, a fresh per-
+    symbol-and-setup stream so pooling is walk-order-independent), pooled across every symbol
+    sharing that ``(setup_id, side)`` into the record's ``baseline_anchors``/``summary``; a pool
+    that exceeds the cap discloses the excess via ``signals_beyond_cap`` rather than silently
+    dropping it. ``progress``, if given, is called after EACH member with ``{"symbol": symbol}``
+    (whether it fired, was absent, or neither); a ``should_abort`` returning True stops the walk
+    early -- the CALLER must then discard the partial result (a cancelled walk is never recorded)."""
     universe_records, _universe_errors = universe_store.list()
     members = list(universe_records[-1]["members"]) if universe_records else []
 
@@ -331,14 +475,27 @@ def compute_playbook(universe_store, bar_store, config_fingerprint: str, session
     signals: list[dict] = []
     absences: list[dict] = []
     diagnostics: list[dict] = []
+    # Cross-symbol pools keyed "<setup_id>:<side>" -- the ONLY pooling boundary that makes sense
+    # this iteration, since a single symbol-session can carry at most ONE opening-range-break
+    # signal (the detector's own mutual-exclusion rule); a future multi-signal-per-session detector
+    # (J-04's JBE) pools into the SAME dict by construction, no rewrite needed.
+    signal_pool: dict[str, list[dict]] = {}
+    baseline_pool: dict[str, list[dict]] = {}
+    pool_counts: dict[str, int] = {}
+    pool_beyond_cap: dict[str, int] = {}
 
     for symbol in members:
+        if should_abort is not None and should_abort():
+            break
+
         bars_5m = bar_store.merged_bars(symbol, "5m")
         session_5m = rth_session_slice(bars_5m, session_date)
         if not session_5m:
             absences.append(
                 {"symbol": symbol, "reason": f"no 5m bars recorded for the {session_date} session"}
             )
+            if progress is not None:
+                progress({"symbol": symbol})
             continue
 
         baseline = baselines(
@@ -355,6 +512,8 @@ def compute_playbook(universe_store, bar_store, config_fingerprint: str, session
                     ),
                 }
             )
+            if progress is not None:
+                progress({"symbol": symbol})
             continue
 
         bars_1m = bar_store.merged_bars(symbol, "1m")
@@ -371,6 +530,8 @@ def compute_playbook(universe_store, bar_store, config_fingerprint: str, session
                     ),
                 }
             )
+            if progress is not None:
+                progress({"symbol": symbol})
             continue
 
         signal, diagnostic = detect_opening_range_breaks(
@@ -378,20 +539,69 @@ def compute_playbook(universe_store, bar_store, config_fingerprint: str, session
             params, _prior_session_close(bars_5m, session_date),
         )
         if signal is not None:
+            session_1m = rth_session_slice(bars_1m, session_date)
+            forward, breached, measure_bars, tf_minutes = _measure_signal(signal, session_5m, session_1m)
+            signal["forward"] = forward
+            signal["invalidation_breached"] = breached
             signals.append(signal)
+
+            pool_key = f"{signal['setup_id']}:{signal['side']}"
+            count_so_far = pool_counts.get(pool_key, 0)
+            pool_counts[pool_key] = count_so_far + 1
+            if count_so_far < DESK_FORWARD_MAX_TOUCHES_PER_ROW:
+                signal_pool.setdefault(pool_key, []).append(forward)
+                sign = 1.0 if signal["side"] == "long" else -1.0
+                rng = random.Random(
+                    f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{signal['setup_id']}"
+                )
+                k = min(1, len(measure_bars))  # this symbol's own capped signal count is <= 1
+                for anchor_idx in _draw_anchor_indices(rng, len(measure_bars), k):
+                    anchor_bar = measure_bars[anchor_idx]
+                    baseline_pool.setdefault(pool_key, []).append(
+                        _measure_from(
+                            measure_bars, anchor_idx, anchor_bar.close, "close", tf_minutes, sign
+                        )
+                    )
+            else:
+                pool_beyond_cap[pool_key] = pool_beyond_cap.get(pool_key, 0) + 1
         if diagnostic is not None:
             diagnostics.append(diagnostic)
+        if progress is not None:
+            progress({"symbol": symbol})
+
+    summary: dict[str, dict] = {}
+    for pool_key, pooled_signals in signal_pool.items():
+        signal_measures = _collect_measures(pooled_signals)
+        pooled_baseline = baseline_pool.get(pool_key, [])
+        baseline_measures = _collect_measures(pooled_baseline)
+        summary[pool_key] = {
+            key: {
+                "signals": _avg_cell(*signal_measures[key]),
+                "baseline": _avg_cell(*baseline_measures[key]),
+            }
+            for key in PLAYBOOK_SIGNAL_MEASURES
+        }
 
     return {
         "session_date": session_date,
         "config_fingerprint": config_fingerprint,
         "playbook_input_signature": signature,
-        "payload_version": 1,
+        # 2: every signal now carries `forward` + `invalidation_breached`, and the record gains
+        # `baseline_anchors`/`summary`/`signals_beyond_cap` (see the module + this function's own
+        # docstrings). The version DESCRIBES the shape; it is the new `rail_max_touches_per_row` key
+        # inside `parameters` (see `playbook_parameters`) that makes the change actually RE-KEY: a
+        # J-01-era record's own signature is untouched (its file is never rewritten), but a fresh
+        # compute over the SAME session_date/bar content now hashes a DIFFERENT parameters blob and
+        # so mints a genuinely new version rather than matching the old, unmeasured one.
+        "payload_version": 2,
         "parameters": params,
         "register": PLAYBOOK_REGISTER,
         "signals": signals,
         "absences": absences,
         "diagnostics": diagnostics,
+        "baseline_anchors": dict(baseline_pool),
+        "summary": summary,
+        "signals_beyond_cap": pool_beyond_cap,
     }
 
 
@@ -453,14 +663,22 @@ class PlaybookStore:
     @staticmethod
     def _registered(meta: dict) -> dict:
         """One verified ``meta`` in the shape every read of this store hands back: fresh copies of
-        the nested ``signals``/``absences``/``diagnostics`` lists (the ``ForwardStore``
-        per-list-copy discipline, so a caller mutating what it received can never poison a later
-        read)."""
+        the nested ``signals``/``absences``/``diagnostics``/``baseline_anchors``/``summary`` (the
+        ``ForwardStore`` per-list-copy discipline, so a caller mutating what it received can never
+        poison a later read). ``.get(..., default)`` on every J-02 field: a J-01-era record on disk
+        carries none of them -- TC-11's honest-absence contract -- and must keep reading back
+        verbatim rather than raising on a missing key."""
         return {
             **meta,
             "signals": [dict(s) for s in meta["signals"]],
             "absences": [dict(a) for a in meta["absences"]],
             "diagnostics": [dict(d) for d in meta.get("diagnostics", [])],
+            "baseline_anchors": {
+                key: [dict(m) for m in measures]
+                for key, measures in meta.get("baseline_anchors", {}).items()
+            },
+            "summary": {key: dict(value) for key, value in meta.get("summary", {}).items()},
+            "signals_beyond_cap": dict(meta.get("signals_beyond_cap", {})),
         }
 
     def list(self) -> tuple[list[dict], list[dict]]:
@@ -542,11 +760,17 @@ class PlaybookStore:
         signals: list[dict],
         absences: list[dict],
         diagnostics: list[dict],
+        baseline_anchors: dict[str, list[dict]] | None = None,
+        summary: dict[str, dict] | None = None,
+        signals_beyond_cap: dict[str, int] | None = None,
     ) -> dict:
         """Persist ONE new playbook record (append-only). An identical 2-pin key raises
         ``PlaybookAlreadyRecorded``; a file already at this key's own deterministic path but
         failing its integrity check raises ``PlaybookIntegrityError`` -- never a silent overwrite
-        (the ``ForwardStore.record`` refuse-loudly branch verbatim)."""
+        (the ``ForwardStore.record`` refuse-loudly branch verbatim). ``baseline_anchors``/
+        ``summary``/``signals_beyond_cap`` default to empty (J-02's measurement fields; a caller
+        planting a J-01-shaped, pre-measurement record -- e.g. a fixture for the "measurement not
+        recorded in this record" absence contract -- simply omits them)."""
         existing = self.find_by_key(session_date, playbook_input_signature)
         if existing is not None:
             raise PlaybookAlreadyRecorded(existing["id"])
@@ -571,6 +795,11 @@ class PlaybookStore:
             "signals": list(signals),
             "absences": list(absences),
             "diagnostics": list(diagnostics),
+            "baseline_anchors": {
+                key: list(measures) for key, measures in (baseline_anchors or {}).items()
+            },
+            "summary": {key: dict(value) for key, value in (summary or {}).items()},
+            "signals_beyond_cap": dict(signals_beyond_cap or {}),
         }
         record = {"meta": meta}
         payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 4d900b4..22cd5b0 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -123,7 +123,9 @@ from .desk_forward import ForwardStore, resolve_desk_forward_dir
 from .desk_forward_compute import DeskForwardComputeManager
 from .desk_forward_log import ForwardRunStore, resolve_desk_forward_log_dir
 from .desk_forward_pins import resolve_desk_forward_pins
-from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
+from .desk_playbook import PlaybookSessionRefused, PlaybookStore, resolve_desk_playbook_dir
+from .desk_playbook_compute import DeskPlaybookComputeManager
+from .desk_playbook_log import PlaybookRunStore, resolve_desk_playbook_log_dir
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
 from .desk_screen_diff import ScreenDiffSelfCompareError, compute_screen_diff
@@ -171,6 +173,10 @@ _desk_forward_compute_manager = DeskForwardComputeManager()
 # The deep fine-bar backfill compute manager — the SAME shape as its four siblings above.
 _desk_deep_backfill_manager = DeskDeepBackfillComputeManager()
 
+# The desk playbook compute manager (Era B2, J-02) — the SAME process-wide-singleton-behind-a-
+# dependency shape as its five siblings above.
+_desk_playbook_compute_manager = DeskPlaybookComputeManager()
+
 
 def get_universe_store() -> UniverseStore:
     """The universe store rooted at the config-owned directory (``TAPEOLOGY_DESK_UNIVERSE_DIR``
@@ -947,10 +953,14 @@ def get_desk_forward_pins(
     )
 
 
-# --- The Playbook (Era B2, J-01) — pre-registered, lookahead-clean intraday setups detected on the
-# desk's own recorded 5m/1m bars (docs/playbook-detector-spec.md). J-01 ships detection only (no
-# measurement, no compute-manager/trigger route, no CLI) plus this ONE read; see desk_playbook.py
-# for the computation, store, and parameters/signature recipe this route only serves verbatim. ----
+# --- The Playbook (Era B2) — pre-registered, lookahead-clean intraday setups detected on the
+# desk's own recorded 5m/1m bars (docs/playbook-detector-spec.md). J-01 shipped detection only (no
+# measurement, no compute-manager/trigger route, no CLI) plus the ONE read below; see
+# desk_playbook.py for the computation, store, and parameters/signature recipe this route only
+# serves verbatim. J-02 (this iteration) extends `compute_playbook` to MEASURE every signal in the
+# same walk (see desk_playbook.py's own docstring) and adds the compute trigger/poll/cancel trio +
+# the durable run ledger, below the GET route — mirrors the forward-returns trio exactly; see
+# desk_playbook_compute.py / desk_playbook_log.py. ---------------------------------------------------
 
 
 def get_playbook_store() -> PlaybookStore:
@@ -1021,6 +1031,121 @@ def get_playbook(
     }
 
 
+# --- The playbook compute (Era B2, J-02) — trigger/poll/cancel trio mirroring the forward-returns
+# trio exactly, plus ONE durable read mirroring `GET /research/desk/forward/runs`. See
+# `desk_playbook_compute.py` for the single-flight manager + `run_playbook_and_record` mechanics
+# and `desk_playbook_log.py` for the run ledger this wires up. ---------------------------------------
+
+
+def get_desk_playbook_compute_manager() -> DeskPlaybookComputeManager:
+    """The desk playbook compute manager — a FastAPI dependency (the
+    ``get_desk_forward_compute_manager`` pattern) so a test overrides it outright via
+    ``app.dependency_overrides`` for complete test-to-test isolation."""
+    return _desk_playbook_compute_manager
+
+
+def get_playbook_run_store() -> PlaybookRunStore:
+    """The durable playbook-run log store rooted at a bare env-var-or-sibling-of-the-universe-dir
+    default (zero new ``Config`` field — see ``desk_playbook_log.resolve_desk_playbook_log_dir``) —
+    the ``get_forward_run_store`` pattern. A FastAPI dependency so tests can point it at a temp dir
+    via the env var or override it outright."""
+    return PlaybookRunStore(resolve_desk_playbook_log_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+class PlaybookComputeRequest(BaseModel):
+    """Body for ``POST /research/desk/playbook/compute`` — ``session_date`` is REQUIRED (FastAPI
+    422s a missing/absent body before the route handler runs, the ``ForwardComputeRequest``/
+    ``ScreenComputeRequest`` convention); this endpoint never defaults to the current wall-clock
+    date (T-6) or to the latest recorded session."""
+
+    session_date: str
+
+
+@router.post("/playbook/compute")
+def trigger_desk_playbook_compute(
+    body: PlaybookComputeRequest,
+    universe_store: UniverseStore = Depends(get_universe_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+    manager: DeskPlaybookComputeManager = Depends(get_desk_playbook_compute_manager),
+    playbook_run_store: PlaybookRunStore = Depends(get_playbook_run_store),
+) -> dict:
+    """Start the single-flight desk playbook compute job for ``body.session_date``, or — if one is
+    already ``status`` in (``"running"``, ``"cancelling"``) — return it UNCHANGED
+    (``started: False``, never a second concurrent job). Returns
+    ``{"started": bool, "compute": <snapshot>}``; the walk runs on a background worker thread, off
+    this request, so this route returns immediately.
+
+    Refuses — 422, naming the non-session date, never starting a job or writing a ledger row — when
+    ``body.session_date`` is provably not a trading session (``desk_sessions.
+    refuse_if_not_a_session`` — the ``trigger_desk_screen_compute`` precedent). This is a PRE-check:
+    ``run_playbook_and_record`` carries the identical guard internally too (for the CLI path, which
+    has no route in front of it, and for the race), but reaching it from this route would mean a
+    job was already created and a "refused_non_session" ledger row already written for a date this
+    route could have refused for free."""
+    records, _errors = universe_store.list()
+    members = list(records[-1]["members"]) if records else []
+    refusal = refuse_if_not_a_session(body.session_date, bar_store, members)
+    if refusal is not None:
+        raise HTTPException(status_code=422, detail=refusal)
+    return manager.trigger(
+        body.session_date, universe_store, bar_store, CONFIG, playbook_store,
+        playbook_run_store=playbook_run_store,
+    )
+
+
+@router.get("/playbook/compute")
+def get_desk_playbook_compute(
+    manager: DeskPlaybookComputeManager = Depends(get_desk_playbook_compute_manager),
+) -> dict:
+    """The playbook compute job's current/last snapshot, served VERBATIM —
+    ``{"status", "session_date", "signals_done", "signals_total", "error"}``, ALWAYS a body (never
+    ``null``: ``status == "idle"`` before any compute has ever run this process). A plain read:
+    never triggers a compute as a side effect (GET-never-computes)."""
+    return manager.snapshot()
+
+
+@router.post("/playbook/compute/cancel")
+def cancel_desk_playbook_compute(
+    manager: DeskPlaybookComputeManager = Depends(get_desk_playbook_compute_manager),
+) -> dict:
+    """Cancel the in-flight desk playbook compute (cooperative — observed between members). ``409``
+    when idle (no job has ever run, or the last job already reached a terminal state) — mirrors
+    ``cancel_desk_forward_compute``'s own 409-when-terminal shape."""
+    snapshot = manager.snapshot()
+    if snapshot["status"] != "running":
+        raise HTTPException(status_code=409, detail="no desk playbook compute is currently running")
+    manager.cancel()
+    return {"cancelling": True}
+
+
+@router.get("/playbook/runs")
+def get_playbook_runs(
+    session_date: str | None = None, store: PlaybookRunStore = Depends(get_playbook_run_store)
+) -> dict:
+    """``{"runs": [...], "latest": <record>|null, "integrity_errors": [...]}`` — the durable log of
+    what every playbook compute attempted, surviving the compute manager's process-scoped snapshot
+    (see ``desk_playbook_log.py``). ``?session_date=`` narrows to one date's own runs (the
+    ``GET /research/desk/forward/runs?screen_id=`` convention), and then ``latest`` is that date's
+    newest run rather than the store's.
+
+    An explicit HTTP 200 honest-empty payload before any playbook run has ever reached a LOGGED
+    terminal state, never a 404. ``latest`` is the most recently STARTED run, verbatim from disk —
+    never recomputed on the GET. ``integrity_errors`` is ``store.list()``'s own ``errors`` return,
+    surfaced verbatim — a corrupted run-record file stays excluded from ``runs``/``latest`` either
+    way, never fabricated, never crashes this route. A cancelled attempt never appears here at all
+    (``desk_playbook_log.py``'s own terminal-excludes-cancelled contract) — its absence looks
+    identical to a run that never happened, by design."""
+    records, errors = store.list()
+    if session_date is not None:
+        records = [record for record in records if record.get("session_date") == session_date]
+    return {
+        "runs": records,
+        "latest": records[-1] if records else None,
+        "integrity_errors": errors,
+    }
+
+
 # --- Coverage-index reconciliation (J-10, goal-desk-iter-14) — a trigger/poll/cancel trio mirroring
 # the top-up compute trio exactly, plus ONE durable read mirroring ``GET /research/desk/topup/runs``.
 # See ``desk_index_reconcile.py`` for the classify/repair/record mechanics this only wires up. -------
diff --git a/apps/backend/tests/test_desk_playbook.py b/apps/backend/tests/test_desk_playbook.py
index d70fff1..ca62fff 100644
--- a/apps/backend/tests/test_desk_playbook.py
+++ b/apps/backend/tests/test_desk_playbook.py
@@ -25,12 +25,16 @@ from app.research import desk_playbook as desk_playbook_module
 from app.research import desk_playbook_detect as desk_playbook_detect_module
 from app.research import desk_playbook_features as desk_playbook_features_module
 from app.research.bars import BarStore
+from app.research.desk_forward import DESK_FORWARD_MAX_TOUCHES_PER_ROW, _measure_from
 from app.research.desk_playbook import (
     PLAYBOOK_REGISTER,
     PlaybookAlreadyRecorded,
     PlaybookIntegrityError,
     PlaybookSessionRefused,
     PlaybookStore,
+    _invalidation_breached,
+    _measure_signal,
+    _measurement_anchor,
     compute_playbook,
     compute_playbook_input_signature,
     playbook_parameters,
@@ -85,6 +89,80 @@ def _plant_firing_session(bar_store: BarStore, symbol: str) -> None:
     _plant(bar_store, symbol, "5m", bars_5m)
 
 
+def _plant_gap_open_firing_session(bar_store: BarStore, symbol: str) -> None:
+    """Same opening range as ``_plant_firing_session`` (or_high=101.0, 1m basis), but the trigger
+    bar OPENS at/beyond ``or_high`` -- ``entry_kind == "gap_open"`` (TC-3)."""
+    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 900.0, 101.2, 101.6, 101.1, 101.4, 1000),  # opens BEYOND 101.0
+        _bar(symbol, "5m", E_OPEN + 1200.0, 101.4, 101.6, 101.2, 101.3, 800),
+        _bar(symbol, "5m", E_OPEN + 1500.0, 101.3, 101.5, 101.0, 101.2, 800),
+    ]
+    _plant(bar_store, symbol, "1m", bars_1m)
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def _plant_full_1m_coverage_firing_session(bar_store: BarStore, symbol: str) -> None:
+    """Like ``_plant_firing_session``, but the 1m series extends THROUGH the trigger's own 5m
+    window (09:45-09:50), not just the opening range (09:30-09:45) -- exercises the "found a real
+    1m bar inside the trigger window" branch of ``_measurement_anchor`` (the non-degraded path)."""
+    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
+    # The trigger 5m bar's own window: 09:45:00 .. 09:50:00 (5 one-minute bars), one of which
+    # (100.9-101.3) actually contains T=101.0 in its [low, high].
+    bars_1m += [
+        _bar(symbol, "1m", E_OPEN + 900.0, 100.8, 100.95, 100.7, 100.9, 200),
+        _bar(symbol, "1m", E_OPEN + 960.0, 100.9, 101.3, 100.85, 101.2, 400),  # contains T=101.0
+        _bar(symbol, "1m", E_OPEN + 1020.0, 101.2, 101.4, 101.1, 101.3, 300),
+        _bar(symbol, "1m", E_OPEN + 1080.0, 101.3, 101.4, 101.2, 101.3, 300),
+        _bar(symbol, "1m", E_OPEN + 1140.0, 101.3, 101.4, 101.1, 101.1, 300),
+    ]
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 900.0, 100.8, 101.4, 100.7, 101.1, 1200),  # trigger: breaks 101.0
+        _bar(symbol, "5m", E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
+        _bar(symbol, "5m", E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
+    ]
+    _plant(bar_store, symbol, "1m", bars_1m)
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def _plant_5m_basis_firing_session(bar_store: BarStore, symbol: str) -> None:
+    """Fewer than ``PLAYBOOK_OR_MIN_1M_BARS`` (10) one-minute bars on file -> the opening range
+    degrades to the 5m basis -- closes audit T1's first gap as a ``compute_playbook``-LEVEL
+    fixture (real ``BarStore`` walk), not just a features/detector-level hand-built dict."""
+    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 100.6, 100.4, 100.5, 500) for i in range(5)]
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),  # trigger
+        _bar(symbol, "5m", E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
+        _bar(symbol, "5m", E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
+    ]
+    _plant(bar_store, symbol, "1m", bars_1m)
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def _plant_ambiguous_session(bar_store: BarStore, symbol: str) -> None:
+    """A single 5m bar strictly breaking BOTH opening-range sides, neither previously broken --
+    closes audit T1's second gap as a ``compute_playbook``-LEVEL fixture (real ``BarStore`` walk)."""
+    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 900.0, 100.5, 102.0, 99.0, 100.5, 1000),  # breaks BOTH sides
+        _bar(symbol, "5m", E_OPEN + 1200.0, 100.5, 100.8, 100.2, 100.6, 800),
+    ]
+    _plant(bar_store, symbol, "1m", bars_1m)
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
 def _register_universe(tmp_path, members: list[str]) -> UniverseStore:
     store = UniverseStore(tmp_path / "universe")
     store.record(
@@ -337,3 +415,304 @@ def test_no_served_signal_field_is_ever_named_stop_loss(bar_store, universe_stor
 
 def test_playbook_register_passes_copy_discipline():
     assert find_violations(PLAYBOOK_REGISTER) == []
+
+
+# --- J-02: measurement -- convention identity (TC-1) --------------------------------------------
+
+
+def test_measure_signal_and_measure_from_produce_byte_identical_leaves():
+    """A synthetic anchor measured through ``_measure_signal`` (the playbook's own call site) and
+    directly through ``desk_forward._measure_from`` with the identical resolved arguments produce
+    byte-identical horizons/to_close_pct/mdd leaves."""
+    session_5m = [
+        _bar("SYN", "5m", E_OPEN + i * 300.0, 100.0 + i * 0.1, 100.5 + i * 0.1, 99.5 + i * 0.1, 100.2 + i * 0.1)
+        for i in range(6)
+    ]
+    signal = {
+        "geometry": {"slots_to_break": 2},
+        "trigger_price": 100.7,
+        "side": "long",
+        "entry": 100.75,
+        "entry_kind": "level",
+        "invalidation_price": 99.0,
+    }
+    forward, breached, measure_bars, tf_minutes = _measure_signal(signal, session_5m, [])
+    assert measure_bars is session_5m and tf_minutes == 5
+
+    direct = _measure_from(session_5m, 2, 100.75, "level", 5, 1.0)
+    assert forward == direct
+    assert set(breached.keys()) == {"1m", "5m", "1h", "4h", "to_close", "first_breach_minutes"}
+
+
+# --- J-02: truncation + gap_open entry reuse (TC-2, TC-3) ----------------------------------------
+
+
+def test_truncated_horizon_reports_effective_minutes_and_last_bar_close(tmp_path, bar_store, universe_store):
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    forward = result["signals"][0]["forward"]
+    horizon_4h = forward["horizons"]["4h"]
+    assert horizon_4h["truncated"] is True
+    assert horizon_4h["effective_minutes"] < 240
+    assert horizon_4h["exit_price"] == forward["close_price"]
+
+
+def test_gap_open_entry_is_reused_verbatim_from_detection(tmp_path, bar_store):
+    universe_store = _register_universe(tmp_path, ["GAP"])
+    _plant_baseline_sessions(bar_store, "GAP")
+    _plant_gap_open_firing_session(bar_store, "GAP")
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    signal = result["signals"][0]
+    assert signal["entry_kind"] == "gap_open"
+    assert signal["forward"]["entry_price"] == signal["entry"]
+    assert signal["forward"]["entry_kind"] == signal["entry_kind"]
+
+
+# --- J-02: invalidation_breached (TC-4, TC-5, TC-6) -----------------------------------------------
+
+
+def test_invalidation_breach_at_a_horizon_boundary_bar():
+    bars = [_bar("INV", "1m", E_OPEN + i * 60.0, 100.0, 100.2, 99.9, 100.0) for i in range(7)]
+    bars[5] = _bar("INV", "1m", E_OPEN + 5 * 60.0, 100.0, 100.2, 98.0, 99.0)  # breach at offset 5
+    forward = _measure_from(bars, 0, 100.0, "level", 1, 1.0)
+    breached = _invalidation_breached(bars, 0, 99.0, "long", 1, forward)
+    assert breached["1m"] is False  # its own boundary (offset 1) is BEFORE the breach
+    assert breached["5m"] is True  # breach lands exactly on the 5m horizon's own boundary
+    assert breached["1h"] is True  # truncated (effective_minutes=6), but 5 <= 6
+    assert breached["4h"] is True
+    assert breached["to_close"] is True
+    assert breached["first_breach_minutes"] == 5
+
+
+def test_invalidation_breach_on_the_anchor_bar_itself():
+    bars = [_bar("INV", "1m", E_OPEN + i * 60.0, 100.0, 100.2, 99.9, 100.0) for i in range(5)]
+    bars[0] = _bar("INV", "1m", E_OPEN, 100.0, 100.2, 98.0, 99.5)  # breach at offset 0
+    forward = _measure_from(bars, 0, 100.0, "level", 1, 1.0)
+    breached = _invalidation_breached(bars, 0, 99.0, "long", 1, forward)
+    assert all(breached[label] for label in ("1m", "5m", "1h", "4h", "to_close"))
+    assert breached["first_breach_minutes"] == 0
+
+
+def test_invalidation_never_breached_reports_null_first_breach_minutes():
+    bars = [_bar("INV", "1m", E_OPEN + i * 60.0, 100.0, 100.2, 99.9, 100.0) for i in range(5)]
+    forward = _measure_from(bars, 0, 100.0, "level", 1, 1.0)
+    breached = _invalidation_breached(bars, 0, 90.0, "long", 1, forward)  # never trades that low
+    assert not any(breached[label] for label in ("1m", "5m", "1h", "4h", "to_close"))
+    assert breached["first_breach_minutes"] is None
+
+
+def test_invalidation_breach_mirrors_for_a_short_signal():
+    bars = [_bar("INVS", "1m", E_OPEN + i * 60.0, 100.0, 100.2, 99.9, 100.0) for i in range(3)]
+    bars[1] = _bar("INVS", "1m", E_OPEN + 60.0, 100.0, 101.5, 99.9, 101.0)  # breach at offset 1
+    forward = _measure_from(bars, 0, 100.0, "level", 1, -1.0)
+    breached = _invalidation_breached(bars, 0, 101.0, "short", 1, forward)
+    assert breached["1m"] is True and breached["first_breach_minutes"] == 1
+
+
+# --- J-02: baseline anchors -- determinism + cross-symbol independence (TC-7, TC-8) --------------
+
+
+def test_baseline_anchors_are_seeded_and_reproducible(tmp_path, bar_store, universe_store):
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    first = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    second = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert first["baseline_anchors"] == second["baseline_anchors"]
+    pool = first["baseline_anchors"]["open_high_break:long"]
+    assert len(pool) == 1  # k = min(this symbol's 1 signal, session bar count)
+    assert pool[0]["entry_kind"] == "close"
+
+
+def test_baseline_anchors_unchanged_by_an_unrelated_zero_signal_symbol(tmp_path, bar_store):
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    solo_universe = _register_universe(tmp_path, ["AAA"])
+    solo = compute_playbook(solo_universe, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    wider_universe = _register_universe(tmp_path, ["AAA", "ZZZ"])  # ZZZ: zero bars, zero signals
+    wider = compute_playbook(wider_universe, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    assert wider["baseline_anchors"]["open_high_break:long"] == solo["baseline_anchors"]["open_high_break:long"]
+
+
+# --- J-02: the pooling cap + beyond-cap disclosure (TC-9) -----------------------------------------
+
+
+def test_signals_beyond_the_pooling_cap_are_disclosed_and_excluded_from_the_pool(tmp_path, bar_store):
+    symbols = [f"SYM{i}" for i in range(DESK_FORWARD_MAX_TOUCHES_PER_ROW + 1)]  # 9 symbols, 1 over
+    universe_store = _register_universe(tmp_path, symbols)
+    for symbol in symbols:
+        _plant_baseline_sessions(bar_store, symbol)
+        _plant_firing_session(bar_store, symbol)
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    assert len(result["signals"]) == len(symbols)  # every symbol still gets a measured signal
+    pool_key = "open_high_break:long"
+    assert len(result["baseline_anchors"][pool_key]) == DESK_FORWARD_MAX_TOUCHES_PER_ROW
+    assert result["summary"][pool_key]["to_close"]["signals"]["n"] == DESK_FORWARD_MAX_TOUCHES_PER_ROW
+    assert result["signals_beyond_cap"] == {pool_key: len(symbols) - DESK_FORWARD_MAX_TOUCHES_PER_ROW}
+
+
+# --- J-02: embedded rail-constant liveness (TC-10) ------------------------------------------------
+
+
+def test_embedded_rail_baseline_seed_monkeypatch_moves_the_signature_and_mints_a_new_version(
+    tmp_path, bar_store, universe_store, monkeypatch
+):
+    store, first_meta = _record_aaa(tmp_path, bar_store, universe_store)
+    first_path = store._path(first_meta["id"])
+    before = _sha256_file(first_path)
+    original_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())
+
+    monkeypatch.setattr(desk_playbook_module, "DESK_FORWARD_BASELINE_SEED", 42)
+
+    moved_params = playbook_parameters()
+    assert moved_params["rail_baseline_seed"] == 42
+    moved_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())
+    assert moved_signature != original_signature
+
+    second_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert second_result["playbook_input_signature"] == moved_signature
+    second_meta = store.record(**second_result)  # does NOT raise -- a genuinely new key
+    assert second_meta["id"] != first_meta["id"]
+    assert _sha256_file(first_path) == before  # the original file is untouched
+
+
+# --- J-02: a J-01-era (pre-measurement) record serves verbatim (TC-11) ----------------------------
+
+
+def test_j01_era_record_serves_verbatim_with_honest_absence_and_unchanged_sha(tmp_path):
+    """A record written BEFORE this iteration's measurement pass existed (no ``forward`` key on its
+    signal, no ``baseline_anchors``/``summary``) reads back byte-unchanged through the route -- the
+    honest absence is that the signal simply carries no ``forward`` block, never a backfilled one."""
+    old_signal = {"symbol": "AAA", "setup_id": "open_high_break", "side": "long"}  # no `forward` key
+    store = PlaybookStore(tmp_path / "playbook")
+    meta = store.record(
+        session_date=SESSION_DATE,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature="pretend-j01-era-signature",
+        payload_version=1,
+        parameters=playbook_parameters(),
+        register="a pre-measurement J-01-era register string",
+        signals=[old_signal],
+        absences=[],
+        diagnostics=[],
+        # baseline_anchors / summary / signals_beyond_cap deliberately omitted -- the J-01 shape.
+    )
+    path = store._path(meta["id"])
+    before = _sha256_file(path)
+
+    reread = store.get(meta["id"])
+    assert reread["signals"] == [old_signal]
+    assert "forward" not in reread["signals"][0]
+    assert "invalidation_breached" not in reread["signals"][0]
+    assert reread["baseline_anchors"] == {}
+    assert reread["summary"] == {}
+    assert reread["signals_beyond_cap"] == {}
+    assert _sha256_file(path) == before  # reading never rewrites the file
+
+
+# --- J-02: audit T1 -- compute_playbook-LEVEL fixtures (TC-16, TC-17) -----------------------------
+
+
+def test_5m_basis_degrade_fires_a_signal_through_a_real_barstore_walk(tmp_path, bar_store):
+    universe_store = _register_universe(tmp_path, ["DEG"])
+    _plant_baseline_sessions(bar_store, "DEG")
+    _plant_5m_basis_firing_session(bar_store, "DEG")
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert len(result["signals"]) == 1
+    signal = result["signals"][0]
+    assert signal["geometry"]["opening_range_basis"] == "5m"
+    assert signal["forward"] is not None
+    assert signal["forward"]["horizons"]["5m"]["return_pct"] is not None
+
+
+def test_ambiguous_outside_bar_fires_no_signal_through_a_real_barstore_walk(tmp_path, bar_store):
+    universe_store = _register_universe(tmp_path, ["AMB"])
+    _plant_baseline_sessions(bar_store, "AMB")
+    _plant_ambiguous_session(bar_store, "AMB")
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert result["signals"] == []
+    assert [d["diagnostic"] for d in result["diagnostics"]] == ["ambiguous_outside_bar"]
+
+
+# --- J-02: the gapped-anchor-window degrade (TC-19) -----------------------------------------------
+
+
+def test_gapped_1m_window_at_the_trigger_bar_degrades_honestly_to_5m_basis(tmp_path, bar_store, universe_store):
+    """``_plant_firing_session``'s 1m series covers ONLY the opening range (09:30-09:45) -- the
+    trigger's own 5m window (09:45-09:50) has ZERO 1m bars. The measurement must degrade to the 5m
+    basis for THIS signal rather than borrow a bar from a neighboring window."""
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    forward = result["signals"][0]["forward"]
+    assert forward["horizons"]["1m"]["reason"] == "the 1m horizon is finer than the 5m touch series"
+    assert forward["horizons"]["5m"]["return_pct"] is not None  # measured on the 5m basis instead
+
+
+def test_a_real_1m_bar_inside_the_trigger_window_is_used_when_available(tmp_path, bar_store):
+    universe_store = _register_universe(tmp_path, ["FULL1M"])
+    _plant_baseline_sessions(bar_store, "FULL1M")
+    _plant_full_1m_coverage_firing_session(bar_store, "FULL1M")
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    forward = result["signals"][0]["forward"]
+    # measured on the genuine 1m basis this time -- the "1m" horizon IS resolvable.
+    assert forward["horizons"]["1m"]["reason"] is None
+    assert forward["horizons"]["1m"]["return_pct"] is not None
+
+
+def test_measurement_anchor_falls_back_to_the_windows_first_1m_bar_when_none_contains_t():
+    session_5m = [_bar("FB", "5m", E_OPEN + i * 300.0, 100.0, 100.5, 99.5, 100.2) for i in range(2)]
+    # Neither 1m bar's [low, high] contains T=105.0 -- falls back to the window's FIRST 1m bar.
+    session_1m = [
+        _bar("FB", "1m", E_OPEN + 300.0, 100.0, 100.3, 99.8, 100.1),
+        _bar("FB", "1m", E_OPEN + 360.0, 100.1, 100.4, 99.9, 100.2),
+    ]
+    measure_bars, anchor_index, tf_minutes = _measurement_anchor(session_5m, session_1m, 1, 105.0)
+    assert measure_bars is session_1m and tf_minutes == 1
+    assert measure_bars[anchor_index].epoch == E_OPEN + 300.0  # the window's first bar
+
+
+# --- J-02: audit B3/B4 doc-only spec catch-ups leave source constants byte-unchanged (TC-20) ------
+
+
+def test_b3_b4_spec_doc_catchups_leave_source_constants_byte_unchanged():
+    """audit B3/B4: two documentation-only edits to ``docs/playbook-detector-spec.md`` -- zero
+    code/value/behavior change. Asserts the spec doc now states both, AND that the exact source
+    lines they describe are byte-unchanged from before this iteration."""
+    import pathlib
+
+    repo_root = pathlib.Path(__file__).resolve().parents[3]
+    spec_text = (repo_root / "docs" / "playbook-detector-spec.md").read_text()
+    assert "PLAYBOOK_OR_MIN_1M_BARS" in spec_text
+    assert '`spike_into_trigger_verdict == "constructive"`' in spec_text
+
+    playbook_source = pathlib.Path(desk_playbook_module.__file__).read_text()
+    assert "PLAYBOOK_OR_MIN_1M_BARS: int = 10" in playbook_source
+
+    detect_source = pathlib.Path(desk_playbook_detect_module.__file__).read_text()
+    assert 'principles = ["P4"] if spike_verdict == "constructive" else []' in detect_source
+
+
+# --- J-02: progress + should_abort wiring ----------------------------------------------------------
+
+
+def test_compute_playbook_progress_and_should_abort_wiring(tmp_path, bar_store, universe_store):
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    seen: list[str] = []
+    result = compute_playbook(
+        universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE,
+        progress=lambda entry: seen.append(entry["symbol"]),
+    )
+    assert seen == ["AAA", "THIN"]  # every member, in walk order, regardless of outcome
... [diff_bound] apps/backend/tests/test_desk_playbook.py: 7 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_playbook_detect.py b/apps/backend/tests/test_desk_playbook_detect.py
index 9a6b404..ca6c9e3 100644
--- a/apps/backend/tests/test_desk_playbook_detect.py
+++ b/apps/backend/tests/test_desk_playbook_detect.py
@@ -214,6 +214,67 @@ def test_a_session_that_never_breaks_either_side_fires_nothing():
     assert diagnostic is None
 
 
+# --- audit T3: the detector's populated-SPY branches -------------------------------------------------
+# Every fixture above passes `index_bars=[]` -- only the no-SPY-bars null branch ever ran. These two
+# exercise a REAL, non-empty SPY 5m series: a trigger late enough in the session (slot 10) for
+# `market_context`'s lookback window (needs >= PLAYBOOK_MKT_LOOKBACK_BARS+1 == 7 prior SPY bars) to
+# resolve at all.
+
+
+def test_market_context_populated_spy_reports_a_supportive_direction():
+    """A clearly rising SPY beside a long trigger -- `direction` resolves non-null, and specifically
+    "supportive" (SPY moved > the neutral band, signed with the signal's own long side)."""
+    bars = [_bar("RS2", E_OPEN + i * 300.0, 100.1, 100.3, 100.0, 100.2, 500) for i in range(10)]
+    bars.append(_bar("RS2", E_OPEN + 10 * 300.0, 100.6, 101.2, 100.5, 101.0, 1000))  # slot 10: trigger
+
+    spy_bars = [
+        _bar(
+            "SPY", E_OPEN + i * 300.0,
+            400.0 + i * 0.3, 400.2 + i * 0.3, 399.9 + i * 0.3, 400.1 + i * 0.3, 500,
+        )
+        for i in range(10)
+    ]
+    or_result = {"high": 100.3, "low": 100.0, "width": 0.3, "basis": "1m", "bars_used": 15}
+    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 500 for i in range(11)}}
+    index_baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {}}
+
+    signal, diagnostic = detect_opening_range_breaks(
+        bars, or_result, baseline, "RS2", SESSION_DATE, spy_bars, index_baseline, _PARAMS, None,
+    )
+    assert diagnostic is None and signal is not None
+    assert signal["market"]["direction"] == "supportive"
+    assert signal["market"]["market_move_mbr"] == pytest.approx(1.8)
+    assert signal["market"]["reason"] is None
+
+
+def test_market_context_relative_strength_strong_when_stock_high_and_spy_low():
+    """The stock closing near its own session-high-so-far while SPY closes near ITS OWN
+    session-low-so-far -- `relative_strength_strong: True` for a long (spec Sec0)."""
+    bars = [_bar("RS1", E_OPEN + i * 300.0, 100.1, 100.3, 100.0, 100.2, 500) for i in range(9)]
+    bars.append(_bar("RS1", E_OPEN + 9 * 300.0, 100.3, 100.5, 100.1, 100.45, 500))  # near its own high
+    bars.append(_bar("RS1", E_OPEN + 10 * 300.0, 100.6, 101.2, 100.5, 101.0, 1000))  # slot 10: trigger
+
+    spy_bars = [
+        _bar(
+            "SPY", E_OPEN + i * 300.0,
+            400.3 - i * 0.1, 400.5 - i * 0.1, 400.1 - i * 0.1, 400.2 - i * 0.1, 500,
+        )
+        for i in range(9)
+    ]
+    spy_bars.append(_bar("SPY", E_OPEN + 9 * 300.0, 399.4, 399.6, 399.0, 399.05, 500))  # near its own low
+
+    or_result = {"high": 100.3, "low": 100.0, "width": 0.3, "basis": "1m", "bars_used": 15}
+    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 500 for i in range(11)}}
+    index_baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {}}
+
+    signal, diagnostic = detect_opening_range_breaks(
+        bars, or_result, baseline, "RS1", SESSION_DATE, spy_bars, index_baseline, _PARAMS, None,
+    )
+    assert diagnostic is None and signal is not None
+    assert signal["market"]["direction"] is not None  # a real, populated-SPY market block
+    assert signal["market"]["relative_strength_strong"] is True
+
+
 # --- TC-6: the generic lookahead property test -----------------------------------------------------
 #
 # Registered fixtures, each ``(session_bars, or_result, baseline, symbol, index_bars,
diff --git a/docs/playbook-detector-spec.md b/docs/playbook-detector-spec.md
index 0414a6f..9934916 100644
--- a/docs/playbook-detector-spec.md
+++ b/docs/playbook-detector-spec.md
@@ -132,6 +132,7 @@ continuation, P5 decreasing-volume reversal, P6 passive accumulation/distributio
 | `PLAYBOOK_MAX_CHASE_FRAC` | 0.002 | BOOK — 3–5c chase on ~$20 ≈ 0.2% |
 | `PLAYBOOK_STOP_PAD_FRAC` | 0.30 | BOOK — 20–40% stop padding; midpoint |
 | `PLAYBOOK_OR_MINUTES` | 15 | BOOK — opening range = first 15–20 min; lower endpoint |
+| `PLAYBOOK_OR_MIN_1M_BARS` | 10 | ADAPTATION — §2 primitive 2's own floor: fewer than 10 of the 15 one-minute bars on file degrades the opening range to the 5m basis (J-01 audit B3: named in code from birth, tabulated here) |
 | `PLAYBOOK_NARROW_OR_MAX_MBR` | 3.0 | ADAPTATION — relative form of the ≤25c narrow range |
 | `PLAYBOOK_JUMP_MIN_MULT` | 1.5 | BOOK — jump ≥ 1.5–2× base; stated minimum |
 | `PLAYBOOK_JUMP_MIN_MOVE_MBR` | 3.0 | ADAPTATION — floor so tiny/tiny can't satisfy the ratio |
@@ -216,8 +217,10 @@ cases. Side/band/entry/measurement always follow §0.
 - **Invalidation.** Long: `S = or_low`, `invalidation = or_low − 0.30·(or_high − or_low)`
   (BOOK structure + BOOK pad). Short mirrored.
 - **Disclosures.** `or_width_mbr`, `or_bars_used`, `opening_range_basis`,
-  `open_vs_prior_close_pct` (gap context), `slots_to_break`. Principles: P4 when pre-break
-  pullbacks were shallow and dry, else structural-only.
+  `open_vs_prior_close_pct` (gap context), `slots_to_break`. Principles: `["P4"]` exactly when
+  `spike_into_trigger_verdict == "constructive"` (§0's already-defined discriminator — pre-break
+  pullbacks were shallow and dry); `[]` (structural-only) otherwise (J-01 audit B4: this mechanical
+  reading is the pre-registered rule, matching `desk_playbook_detect.py`'s implementation verbatim).
 - **Edge cases.** `gap_open` triggers at slot 3 are common on trend opens —
   `gapped_beyond_chase` does the honesty work. No 1m and no 5m OR ⇒ silent symbol-session
   (disclosed absence).
diff --git a/apps/backend/app/research/desk_playbook_compute.py b/apps/backend/app/research/desk_playbook_compute.py
new file mode 100644
index 0000000..aa61cb1
--- /dev/null
+++ b/apps/backend/app/research/desk_playbook_compute.py
@@ -0,0 +1,399 @@
+"""Desk playbook compute (Era B2, J-02) -- the single-flight, cancellable, progress-reporting
+background job around ``desk_playbook.compute_playbook`` (the SOLE detect+measure walker; this
+module computes nothing about signals or measurements itself), plus a CLI warmer that drives the
+SAME run-and-record function synchronously, in-process, for a REQUIRED ``--session-date``.
+
+Mirrors ``desk_forward_compute.DeskForwardComputeManager``/``run_forward_and_record`` verbatim in
+shape: one in-flight job slot (``self._snapshot``), an in-memory process-scoped progress snapshot,
+cooperative cancel, an atomic snapshot publish under a lock (a fresh dict rebound in ONE assignment,
+never mutated in place). Job state is process-scoped bookkeeping -- honestly lost on restart, never
+a research value.
+
+**Reuse, not a recompute.** ``run_playbook_and_record`` resolves the run's 2-pin key BEFORE any
+walk, using only metadata reads (``compute_playbook_input_signature`` is
+``list(include_bars=False)``-only, the same cheap-pre-check discipline ``compute_forward_input_
+signature`` follows): a ``PlaybookStore.find_by_key`` hit short-circuits immediately with
+``reused=True`` and ZERO ``merged_bars`` reads. A miss runs the full detect+measure walk; a
+cancelled (partial) walk is NEVER recorded.
+
+**Session honesty, twice, on purpose.** The HTTP route (``desk_routes.trigger_desk_playbook_
+compute``) pre-checks ``desk_sessions.refuse_if_not_a_session`` BEFORE ever calling
+``DeskPlaybookComputeManager.trigger`` -- a bad ``session_date`` never creates a job or a ledger row
+by that path (the ``trigger_desk_screen_compute`` precedent). ``run_playbook_and_record`` ALSO
+checks it directly (not merely relying on ``compute_playbook``'s own internal check), for the CLI
+path -- which carries no separate pre-check layer -- and for the rare race between the route's
+check and the walk's start; this second check DOES log an honest ``"refused_non_session"`` ledger
+row, since the CLI has no earlier gate to make that outcome invisible.
+
+**Cancellation leaves no trace, deliberately -- both here AND in the ledger.** Unlike
+``desk_forward_compute``'s manager (whose snapshot settles on a distinct ``"cancelled"`` state),
+this manager's ``status`` enum (``idle``/``running``/``cancelling``/``done``/``error``) has no
+sixth value for a completed cancel: once the walk observes the cancel and stops, the snapshot
+reverts to the SAME idle shape it started from, and ``desk_playbook_log.py``'s writer is never
+called for it either (see that module's docstring). A cancelled playbook run is treated as though
+it never happened, everywhere it is visible -- not merely absent from the durable store (true of
+every compute path in this codebase) but absent from the ephemeral progress view too.
+
+**Store-only.** The compute reads the frozen ``BarStore``/``UniverseStore`` exactly as they stand
+-- it never issues a vendor fetch, never triggers a universe refresh. The CLI below resolves the
+real store singletons via ``routes.py``'s accessors (the same legal one-way edge
+``desk_forward_compute``'s own CLI already uses), which is also why the manager lives as a
+module-level singleton in ``desk_routes.py``, never on ``ResearchRegistry``.
+
+**The durable run log.** ``PlaybookStore`` records only SUCCESSFUL measurements, so on its own it
+cannot distinguish a session whose playbook never ran from one that ran and found nothing to
+record. ``desk_playbook_log.PlaybookRunStore`` is the durable counterpart (the
+``desk_forward_log``/``desk_topup_log`` discipline), written once from inside
+``run_playbook_and_record`` below for every TERMINAL outcome except a cancel. It is OPTIONAL at
+every call site (``playbook_run_store=None`` skips it), so the compute path is unchanged for
+callers that do not pass one."""
+
+from __future__ import annotations
+
+import argparse
+import sys
+import threading
+import uuid
+from datetime import datetime, timezone
+from typing import Callable
+
+from ..config import CONFIG, Config
+from .bars import BarStore
+from .desk_playbook import (
+    PlaybookAlreadyRecorded,
+    PlaybookSessionRefused,
+    PlaybookStore,
+    compute_playbook,
+    compute_playbook_input_signature,
+    resolve_desk_playbook_dir,
+)
+from .desk_playbook_log import (
+    PlaybookRunStore,
+    record_playbook_run,
+    resolve_desk_playbook_log_dir,
+)
+from .desk_sessions import refuse_if_not_a_session
+from .desk_universe import UniverseStore
+from .routes import get_bar_store
+
+__all__ = ["DeskPlaybookComputeManager", "run_playbook_and_record"]
+
+_IDLE_SNAPSHOT: dict = {
+    "status": "idle", "session_date": None, "signals_done": 0, "signals_total": 0, "error": None,
+}
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def run_playbook_and_record(
+    universe_store: UniverseStore,
+    bar_store: BarStore,
+    config: Config,
+    playbook_store: PlaybookStore,
+    session_date: str,
+    *,
+    progress: Callable[[dict], None] | None = None,
+    should_abort: Callable[[], bool] | None = None,
+    playbook_run_store: PlaybookRunStore | None = None,
+) -> tuple[dict | None, bool]:
+    """Detect+measure ONE session (``compute_playbook`` -- the sole walker) and persist it,
+    append-only. Returns ``(record, reused)``:
+
+      * a provably non-session ``session_date`` raises ``PlaybookSessionRefused`` (belt-and-braces
+        -- the route pre-checks and 422s before ever reaching here for the HTTP path; this is the
+        rail for the CLI path and for the race);
+      * an identical 2-pin key already recorded returns the EXISTING record with
+        ``(record, True)`` -- resolved BEFORE the walk, zero bar reads;
+      * a cancelled (partial) walk is NEVER recorded -- returns ``(None, False)``;
+      * a freshly persisted record returns ``(record, False)``; the record-time
+        ``PlaybookAlreadyRecorded`` race resolves to the existing record with ``(record, True)``.
+
+    If ``playbook_run_store`` is given, this function ALSO persists exactly one durable run record
+    (``desk_playbook_log.record_playbook_run``) at its own terminal outcome -- EXCEPT for a cancel,
+    which is never logged at all (module docstring). ``playbook_run_store=None`` (the default)
+    skips logging entirely, so every existing caller/test keeps working unmodified."""
+    started_at = _iso_utc_now()
+    config_fingerprint = config.config_fingerprint()
+
+    # Written EXACTLY ONCE per run -- structurally, not by convention (the `run_forward_and_record`
+    # B1 latch verbatim): without this, a terminal write that itself raises would be caught by the
+    # outer `except` below and re-entered as a SECOND, fabricated "failed" record.
+    logged = False
+
+    def _log(
+        *, outcome: str, signals_recorded: int, playbook_input_signature: str | None,
+        playbook_id: str | None, error: str | None,
+    ) -> None:
+        nonlocal logged
+        if playbook_run_store is None or logged:
+            return
+        logged = True
+        record_playbook_run(
+            playbook_run_store,
+            session_date=session_date,
+            config_fingerprint=config_fingerprint,
+            playbook_input_signature=playbook_input_signature,
+            started_at=started_at,
+            finished_at=_iso_utc_now(),
+            outcome=outcome,
+            signals_recorded=signals_recorded,
+            playbook_id=playbook_id,
+            error=error,
+        )
+
+    universe_records, _errors = universe_store.list()
+    members = list(universe_records[-1]["members"]) if universe_records else []
+
+    refusal = refuse_if_not_a_session(session_date, bar_store, members)
+    if refusal is not None:
+        _log(
+            outcome="refused_non_session", signals_recorded=0, playbook_input_signature=None,
+            playbook_id=None, error=refusal,
+        )
+        raise PlaybookSessionRefused(refusal)
+
+    try:
+        signature = compute_playbook_input_signature(bar_store, members, config_fingerprint)
+        existing = playbook_store.find_by_key(session_date, signature)
+        if existing is not None:
+            # A reuse is a real attempt with its own timestamps, and its counts are the ones the
+            # walk it short-circuited produced -- never zeroes, which would read as an empty result.
+            _log(
+                outcome="reused", signals_recorded=len(existing["signals"]),
+                playbook_input_signature=signature, playbook_id=existing["id"], error=None,
+            )
+            return existing, True
+
+        result = compute_playbook(
+            universe_store, bar_store, config_fingerprint, session_date,
+            progress=progress, should_abort=should_abort,
+        )
+        if should_abort is not None and should_abort():
+            # Nothing is persisted AND nothing is logged -- a cancelled playbook run leaves no
+            # trace anywhere (module docstring), unlike the forward-returns ledger's "cancelled"
+            # row.
+            return None, False
+
+        try:
+            recorded = playbook_store.record(**result)
+        except PlaybookAlreadyRecorded as exc:
+            raced = playbook_store.find_by_key(session_date, result["playbook_input_signature"])
+            assert raced is not None and raced["id"] == exc.existing_id
+            _log(
+                outcome="reused", signals_recorded=len(raced["signals"]),
+                playbook_input_signature=result["playbook_input_signature"],
+                playbook_id=raced["id"], error=None,
+            )
+            return raced, True
+    except PlaybookSessionRefused as exc:
+        # The rare race: bars/universe changed between the up-front check above and the walk's own
+        # internal one inside `compute_playbook`.
+        _log(
+            outcome="refused_non_session", signals_recorded=0, playbook_input_signature=None,
+            playbook_id=None, error=str(exc),
+        )
+        raise
+    except Exception as exc:  # noqa: BLE001 -- logged, then re-raised VERBATIM, never swallowed
+        _log(
+            outcome="failed", signals_recorded=0, playbook_input_signature=None,
+            playbook_id=None, error=str(exc),
+        )
+        raise
+
+    _log(
+        outcome="recorded", signals_recorded=len(recorded["signals"]),
+        playbook_input_signature=recorded["playbook_input_signature"],
+        playbook_id=recorded["id"], error=None,
+    )
+    return recorded, False
+
+
+class DeskPlaybookComputeManager:
+    """Owns the SINGLE in-flight (or last-terminal) desk playbook compute job. Construct with no
+    arguments -- every ``trigger()`` call takes its stores/config explicitly (the
+    ``DeskForwardComputeManager`` per-call-injection precedent)."""
+
+    def __init__(self) -> None:
+        self._lock = threading.Lock()
+        self._snapshot: dict | None = None
+        self._job_id: str | None = None
+        self._cancel_event: threading.Event | None = None
+        self._thread: threading.Thread | None = None
+
+    def snapshot(self) -> dict:
+        """The current/last job's snapshot -- ``{"status", "session_date", "signals_done",
+        "signals_total", "error"}``, ALWAYS a real dict (never ``None``): before any job has ever
+        run this process, ``status == "idle"``. A caller-safe copy, never a shared mutable
+        reference."""
+        current = self._snapshot
+        return dict(current) if current is not None else dict(_IDLE_SNAPSHOT)
+
+    def trigger(
+        self,
+        session_date: str,
+        universe_store: UniverseStore,
+        bar_store: BarStore,
+        config: Config,
+        playbook_store: PlaybookStore,
+        playbook_run_store: PlaybookRunStore | None = None,
+    ) -> dict:
+        """Start a NEW playbook compute job for ``session_date``, or -- if one is already
+        ``status`` in (``"running"``, ``"cancelling"``) -- return it UNCHANGED (``started: False``,
+        single-flight, process-wide -- never per-``session_date``). Once the current job is
+        terminal, the NEXT call always starts a genuinely new job. Never blocks -- the walk runs on
+        a dedicated worker thread. Callers are expected to have ALREADY refused a non-session date
+        (the route's own pre-check) -- this method does not repeat that check itself; a bad date
+        still resolves honestly (``status: "error"``) via ``run_playbook_and_record``'s own guard."""
+        with self._lock:
+            current = self._snapshot
+            if current is not None and current["status"] in ("running", "cancelling"):
+                return {"started": False, "compute": dict(current)}
+
+            # signals_total resolved synchronously, before any background work starts (the
+            # rows_total/members_total precedent) -- the universe's own member count, the upper
+            # bound on how many symbols this walk will visit.
+            universe_records, _errors = universe_store.list()
+            signals_total = len(universe_records[-1]["members"]) if universe_records else 0
+
+            job_id = uuid.uuid4().hex
+            self._job_id = job_id
+            cancel_event = threading.Event()
+            self._cancel_event = cancel_event
+            snapshot = {
+                "status": "running", "session_date": session_date,
+                "signals_done": 0, "signals_total": signals_total, "error": None,
+            }
+            self._snapshot = snapshot
+
+        def _publish(_entry: dict) -> None:
+            with self._lock:
+                if self._job_id != job_id:
+                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
+                current = self._snapshot
+                if current is None:
+                    return
+                self._snapshot = {**current, "signals_done": current["signals_done"] + 1}
+
+        def _work() -> None:
+            try:
+                run_playbook_and_record(
+                    universe_store, bar_store, config, playbook_store, session_date,
+                    progress=_publish, should_abort=cancel_event.is_set,
+                    playbook_run_store=playbook_run_store,
+                )
+            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
+                self._resolve_error(job_id, str(exc))
+                return
+            if cancel_event.is_set():
+                self._resolve_cancelled(job_id)
+            else:
+                self._resolve_done(job_id)
+
+        thread = threading.Thread(target=_work, name=f"desk-playbook-compute:{job_id}", daemon=True)
+        with self._lock:
+            self._thread = thread
+        thread.start()
+        return {"started": True, "compute": dict(snapshot)}
+
+    def _resolve_done(self, job_id: str) -> None:
+        with self._lock:
+            current = self._snapshot
+            if current is None or self._job_id != job_id:
+                return  # superseded -- never resolve a job that is no longer the current one
+            self._snapshot = {**current, "status": "done", "error": None}
+
+    def _resolve_error(self, job_id: str, error: str) -> None:
+        with self._lock:
+            current = self._snapshot
+            if current is None or self._job_id != job_id:
+                return
+            self._snapshot = {**current, "status": "error", "error": error}
+
+    def _resolve_cancelled(self, job_id: str) -> None:
+        """A completed cancel leaves NO trace (module docstring): the snapshot reverts to the same
+        idle shape it started from, rather than a distinct terminal state nothing was recorded
+        under."""
+        with self._lock:
+            if self._job_id != job_id:
+                return
+            self._snapshot = dict(_IDLE_SNAPSHOT)
+
+    def cancel(self) -> None:
+        """Signal cooperative cancellation for the in-flight job -- flips the visible ``status`` to
+        ``"cancelling"`` immediately (distinct from a walk still unaware of the request), a
+        harmless no-op if idle (the ROUTE is the one that rejects an idle cancel with a 409)."""
+        with self._lock:
+            cancel_event = self._cancel_event
+            current = self._snapshot
+            if current is not None and current["status"] == "running":
+                self._snapshot = {**current, "status": "cancelling"}
+        if cancel_event is not None:
+            cancel_event.set()
+
+    def join_all(self, timeout: float = 30.0) -> None:
+        """Wait for the in-flight job thread, if any (test/shutdown hygiene)."""
+        with self._lock:
+            thread = self._thread
+        if thread is not None:
+            thread.join(timeout=timeout)
+
+
+# --- The CLI warmer --------------------------------------------------------------------------------
+
+
+def _cli_progress_printer() -> Callable[[dict], None]:
+    def _print(entry: dict) -> None:
+        print(f"  walked {entry['symbol']}", flush=True)
+
+    return _print
+
+
+def main() -> int:
+    """The CLI entry: ``python -m app.research.desk_playbook_compute --session-date <yyyy-MM-dd>``.
+    Runs the playbook detect+measure walk to completion against the operator's real universe/bar/
+    playbook dirs, publishing to the SAME durable playbook store ``GET /research/desk/playbook``
+    serves. ``--session-date`` is REQUIRED and never defaults to the current wall-clock date (T-6)."""
+    parser = argparse.ArgumentParser(
+        description="Desk playbook CLI warmer -- detect the opening-range-break family and measure "
+        "every signal with the desk forward rail's own conventions (horizons, dual max drawdown, "
+        "truncation honesty, the seeded random-anchor baseline) for ONE recorded session, and "
+        "persist the result append-only to the SAME durable playbook store "
+        "GET /research/desk/playbook serves."
+    )
+    parser.add_argument(
+        "--session-date", required=True,
+        help="the recorded trading session date (yyyy-MM-dd) to detect and measure -- REQUIRED; "
+        "never defaults to the current date.",
+    )
+    args = parser.parse_args()
+
+    config = CONFIG
+    universe_store = UniverseStore(config.desk_universe_dir_resolved())
+    bar_store = get_bar_store()
+    playbook_store = PlaybookStore(resolve_desk_playbook_dir(config.desk_universe_dir_resolved()))
+    playbook_run_store = PlaybookRunStore(
+        resolve_desk_playbook_log_dir(config.desk_universe_dir_resolved())
+    )
+
+    try:
+        recorded, reused = run_playbook_and_record(
+            universe_store, bar_store, config, playbook_store, args.session_date,
+            progress=_cli_progress_printer(), playbook_run_store=playbook_run_store,
+        )
+    except PlaybookSessionRefused as exc:
+        print(str(exc), file=sys.stderr)
+        return 1
+
+    assert recorded is not None  # no cancel path exists in the CLI
+    print(
+        f"playbook compute complete for {args.session_date}: {len(recorded['signals'])} signal(s), "
+        f"{len(recorded['absences'])} absence(s) -- record {recorded['id']} "
+        f"({'reused existing' if reused else 'newly recorded'})."
+    )
... [diff_bound] apps/backend/app/research/desk_playbook_compute.py: 5 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/desk_playbook_log.py b/apps/backend/app/research/desk_playbook_log.py
new file mode 100644
index 0000000..2375dee
--- /dev/null
+++ b/apps/backend/app/research/desk_playbook_log.py
@@ -0,0 +1,239 @@
+"""The playbook run log (Era B2, J-02) -- an append-only, checksummed record of what every desk
+PLAYBOOK compute run attempted, surviving past the next run superseding
+``DeskPlaybookComputeManager``'s in-flight/last-terminal snapshot (``desk_playbook_compute.py``'s
+job state is process-scoped and honestly lost on restart, exactly like its forward-returns
+sibling). Mirrors ``desk_forward_log.py``/``desk_topup_log.py``'s discipline: a checksum-verified
+load on every read (``PlaybookRunIntegrityError`` on any mismatch, never silence, never a
+fabricated record), ``record()`` the only mutation, no update/delete function anywhere, and NO
+content-based deduplication -- every terminal run is its own genuinely distinct event.
+
+**Terminal-state-only, and "terminal" EXCLUDES cancelled (the one deliberate divergence from
+``desk_forward_log.py``, matching ``desk_topup_log.py``'s OBSERVED behaviour instead).** A run
+whose PROCESS ends before this module's writer is ever called (a crash, ``kill -9``, a power loss)
+leaves NO record -- there is no "pending"/"partial" file ever written, because ``record()`` is the
+ONLY write path here and it is called at most once, at the very end of a run's lifecycle. An
+OPERATOR-cancelled run leaves NO record EITHER: unlike the forward-returns ledger (which logs a
+``"cancelled"`` state), ``run_playbook_and_record`` (``desk_playbook_compute.py``) simply never
+calls this module's writer when the walk observed a cancel -- unmeasured, partial work is not a
+reportable attempt outcome for the playbook, it is exactly as if the run had not happened. The four
+``outcome`` values below (``recorded``/``reused``/``refused_non_session``/``failed``) are therefore
+the COMPLETE terminal-state set; there is no fifth.
+
+**Records the RUN only -- zero diff to what a playbook record itself records.**
+``desk_playbook.py``'s ``PlaybookStore`` stays the sole owner of playbook records/signals/the 2-pin
+key; this module never reads or writes a playbook record file, never re-derives a pin, and never
+duplicates ``signals``/``absences``/``diagnostics`` content -- only a COUNT of what a successful
+run measured, the same "attempt-level summary, not content" split every sibling run-log draws.
+
+**Storage dir -- no new ``Config`` field.** ``resolve_desk_playbook_log_dir`` mirrors
+``resolve_desk_forward_log_dir`` exactly: a bare ``TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`` env-var
+override, else a directory co-located as a SIBLING of the caller's own already-resolved universe
+directory -- an operational storage-location knob, never a value that shapes a served result, so
+``config_fingerprint()`` stays untouched."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+import uuid
+from pathlib import Path
+
+__all__ = [
+    "PlaybookRunIntegrityError",
+    "PlaybookRunStore",
+    "record_playbook_run",
+    "resolve_desk_playbook_log_dir",
+]
+
+# The store's own env-var override (the ``TAPEOLOGY_DESK_FORWARD_LOG_DIR`` pattern) -- see
+# ``resolve_desk_playbook_log_dir``.
+_PLAYBOOK_LOG_DIR_ENV = "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR"
+
+# The COMPLETE terminal-outcome set (the module docstring's "terminal excludes cancelled" rule) --
+# matches the Data Contract's own ``outcome`` enum exactly. Never "cancelled": a cancelled run
+# writes no row at all (the caller, ``run_playbook_and_record``, simply never calls ``record()``
+# for one).
+_TERMINAL_OUTCOMES = ("recorded", "reused", "refused_non_session", "failed")
+
+
+class PlaybookRunIntegrityError(Exception):
+    """An on-disk run-record file failed its checksum verification on load -- corrupted or
+    tampered, surfaced explicitly (never silence, never a fabricated record)."""
+
+
+def resolve_desk_playbook_log_dir(desk_universe_dir_resolved: str) -> str:
+    """The playbook run log's directory: the ``TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`` env var if set,
+    else a directory co-located as a SIBLING of the CALLER's own already-resolved universe
+    directory (the ``resolve_desk_forward_log_dir`` pattern verbatim). Deliberately NOT a
+    ``desk_playbook_log_dir`` ``Config`` field (see the module docstring) -- this keeps
+    ``config_fingerprint()`` untouched."""
+    override = os.environ.get(_PLAYBOOK_LOG_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "playbook_runs")
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding every checksum in this module hashes (stable across
+    processes: sorted keys, no whitespace) -- the SAME encoding ``desk_forward_log.py``/
+    ``desk_playbook.py`` hash."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+class PlaybookRunStore:
+    """File-based store rooted at the resolved playbook-run-log directory -- the ONE
+    reader/writer. Mirrors ``desk_forward_log.ForwardRunStore``'s load/checksum discipline exactly;
+    like it, ``record`` performs no content-keyed dedup -- every call always persists a genuinely
+    new file."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    @property
+    def root(self) -> Path:
+        return self._root
+
+    def _path(self, run_id: str) -> Path:
+        return self._root / f"{run_id}.json"
+
+    def _load(self, path: Path) -> dict:
+        """Load ONE run-record file, verifying its whole-record checksum. Raises
+        ``PlaybookRunIntegrityError`` for any parse/shape/checksum failure -- explicit, never
+        silent."""
+        try:
+            data = json.loads(path.read_text())
+        except (OSError, ValueError) as exc:
+            raise PlaybookRunIntegrityError(
+                f"playbook run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
+                f"tampered"
+            ) from exc
+        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
+            raise PlaybookRunIntegrityError(
+                f"playbook run record file '{path.name}' does not carry the expected record shape "
+                f"-- corrupted or tampered"
+            )
+        record = data["record"]
+        if _sha256(_canonical(record)) != data["file_checksum"]:
+            raise PlaybookRunIntegrityError(
+                f"playbook run record file '{path.name}' failed its integrity check (checksum "
+                f"mismatch) -- the file was corrupted or tampered with"
+            )
+        meta = record.get("meta")
+        if not isinstance(meta, dict):
+            raise PlaybookRunIntegrityError(
+                f"playbook run record file '{path.name}' does not carry the expected record shape "
+                f"-- corrupted or tampered"
+            )
+        return meta
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        """Every registered run's full content (each file verified), oldest-started first, plus an
+        EXPLICIT error row per file that failed verification -- a corrupt file is surfaced, never
+        silently hidden and never served as data. A store whose directory was never created (no run
+        has ever been recorded) returns ``([], [])`` -- the honest-empty case."""
+        if not self._root.exists():
+            return [], []
+        records: list[dict] = []
+        errors: list[dict] = []
+        for path in sorted(self._root.glob("*.json")):
+            try:
+                records.append(dict(self._load(path)))
+            except PlaybookRunIntegrityError as exc:
+                errors.append({"file": path.name, "error": str(exc)})
+        records.sort(key=lambda meta: (meta.get("started_at", ""), meta.get("run_id", "")))
+        return records, errors
+
+    def list_for_session(self, session_date: str) -> list[dict]:
+        """Every recorded run FOR one session date, oldest-started first -- a plain filter over
+        ``list()``'s verified records (integrity errors stay excluded there, never re-surfaced as
+        data here)."""
+        records, _errors = self.list()
+        return [record for record in records if record.get("session_date") == session_date]
+
+    def record(
+        self,
+        *,
+        session_date: str,
+        config_fingerprint: str,
+        playbook_input_signature: str | None,
+        started_at: str,
+        finished_at: str,
+        outcome: str,
+        signals_recorded: int,
+        playbook_id: str | None,
+        error: str | None,
+    ) -> dict:
+        """Persist ONE new playbook-run record (record + register in a single explicit action) --
+        ALWAYS a genuinely new file: no content-keyed dedup exists in this store (see the module
+        docstring), so a second call with identical field values still appends a second, distinct
+        record.
+
+        ``signals_recorded`` is the count of signals the resulting record HOLDS (its own recorded
+        or already-recorded-and-reused count, never a partial-walk count -- a cancelled/interrupted
+        run never reaches this call at all)."""
+        if outcome not in _TERMINAL_OUTCOMES:
+            raise ValueError(
+                f"invalid terminal outcome {outcome!r} -- must be one of {_TERMINAL_OUTCOMES}"
+            )
+        date = started_at[:10]  # started_at is always an ISO-8601 UTC string -- a YYYY-MM-DD prefix
+        run_id = f"playbookrun-{date}-{uuid.uuid4().hex[:12]}"
+        # A path collision is astronomically unlikely (a random 12-hex-char suffix), but this store
+        # never silently overwrites an existing file regardless of cause -- mirrors
+        # ForwardRunStore.record's identical defensive re-roll instead of a blind write.
+        while self._path(run_id).exists():
+            run_id = f"playbookrun-{date}-{uuid.uuid4().hex[:12]}"
+        meta = {
+            "run_id": run_id,
+            "session_date": session_date,
+            "config_fingerprint": config_fingerprint,
+            "playbook_input_signature": playbook_input_signature,
+            "started_at": started_at,
+            "finished_at": finished_at,
+            "outcome": outcome,
+            "signals_recorded": signals_recorded,
+            "playbook_id": playbook_id,
+            "error": error,
+        }
+        record = {"meta": meta}
+        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
+        self._root.mkdir(parents=True, exist_ok=True)
+        self._path(run_id).write_text(json.dumps(payload))
+        return dict(meta)
+
+
+def record_playbook_run(
+    store: PlaybookRunStore,
+    *,
+    session_date: str,
+    config_fingerprint: str,
+    playbook_input_signature: str | None,
+    started_at: str,
+    finished_at: str,
+    outcome: str,
+    signals_recorded: int,
+    playbook_id: str | None,
+    error: str | None,
+) -> dict:
+    """THE single shared writer -- called AT MOST once per run, at a run's terminal state (and
+    never at all for a cancel -- see the module docstring), from inside ``run_playbook_and_record``
+    (``desk_playbook_compute.py``) -- the ONE shared entry point both
+    ``DeskPlaybookComputeManager``'s worker and the CLI's ``main()`` call -- and nothing else. A
+    thin, explicit free function over ``PlaybookRunStore.record`` (rather than the call site
+    invoking the method directly) so a future reader grepping for ``record_playbook_run`` finds the
+    one call site (the ``record_forward_run``/``record_topup_run`` precedent)."""
+    return store.record(
+        session_date=session_date,
+        config_fingerprint=config_fingerprint,
+        playbook_input_signature=playbook_input_signature,
+        started_at=started_at,
+        finished_at=finished_at,
+        outcome=outcome,
+        signals_recorded=signals_recorded,
+        playbook_id=playbook_id,
+        error=error,
+    )
diff --git a/apps/backend/tests/test_desk_playbook_compute.py b/apps/backend/tests/test_desk_playbook_compute.py
new file mode 100644
index 0000000..d428b19
--- /dev/null
+++ b/apps/backend/tests/test_desk_playbook_compute.py
@@ -0,0 +1,430 @@
+"""``desk_playbook_compute.py`` (Era B2, J-02) — ``run_playbook_and_record``'s reuse/cancel/
+session-refusal/ledger-write discipline, ``DeskPlaybookComputeManager``'s single-flight + cancel
+mechanics, the CLI warmer, and the compute/runs routes end to end. Mirrors the manager/route/CLI
+sections of ``test_desk_forward.py`` in shape; ``test_desk_playbook_log.py`` covers the ledger
+store module in isolation.
+
+Reuses ``test_desk_playbook``'s own bar/universe fixture helpers (the ``from test_copy_discipline
+import find_violations`` cross-file-import precedent already established there) rather than
+duplicating them."""
+
+from __future__ import annotations
+
+import sys
+import threading
+import time
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app
+from app.research import desk_playbook_compute
+from app.research.bars import BarStore
+from app.research.desk_playbook import (
+    PlaybookSessionRefused,
+    PlaybookStore,
+    compute_playbook_input_signature,
+    resolve_desk_playbook_dir,
+)
+from app.research.desk_playbook_compute import DeskPlaybookComputeManager, run_playbook_and_record
+from app.research.desk_playbook_log import PlaybookRunStore, resolve_desk_playbook_log_dir
+from app.research.desk_routes import get_desk_playbook_compute_manager
+from app.research.desk_sessions import non_session_refusal, session_evidence
+from app.research.desk_universe import UniverseStore
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+from test_desk_playbook import (
+    E_OPEN,
+    SESSION_DATE,
+    _bar,
+    _plant,
+    _plant_baseline_sessions,
+    _plant_firing_session,
+    _register_universe,
+)
+
+
+@pytest.fixture
+def env(tmp_path):
+    bar_store = BarStore(tmp_path / "bars")
+    universe_store = _register_universe(tmp_path, ["AAA"])
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    return bar_store, universe_store, playbook_store
+
+
+def _wait_for_terminal(manager: DeskPlaybookComputeManager, timeout: float = 5.0) -> dict:
+    deadline = time.monotonic() + timeout
+    while time.monotonic() < deadline:
+        snap = manager.snapshot()
+        if snap["status"] not in ("running", "cancelling"):
+            return snap
+        time.sleep(0.01)
+    raise AssertionError("playbook compute never reached a terminal state")
+
+
+# --- run_playbook_and_record: reuse / cancel / session refusal / ledger (TC-12, TC-13) -----------
+
+
+def test_a_fresh_run_records_and_logs_exactly_one_row(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    run_store = PlaybookRunStore(tmp_path / "playbook_runs")
+
+    record, reused = run_playbook_and_record(
+        universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE, playbook_run_store=run_store,
+    )
+
+    assert reused is False and len(record["signals"]) == 1
+    rows, errors = run_store.list()
+    assert errors == [] and len(rows) == 1
+    assert rows[0]["outcome"] == "recorded"
+    assert rows[0]["playbook_id"] == record["id"]
+    assert rows[0]["playbook_input_signature"] == record["playbook_input_signature"]
+    assert rows[0]["signals_recorded"] == 1
+    assert rows[0]["error"] is None
+
+
+def test_a_reused_run_records_a_second_row_carrying_the_existing_records_counts(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    run_store = PlaybookRunStore(tmp_path / "playbook_runs")
+    first, _ = run_playbook_and_record(
+        universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE, playbook_run_store=run_store,
+    )
+
+    second, reused = run_playbook_and_record(
+        universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE, playbook_run_store=run_store,
+    )
+
+    assert reused is True and second["id"] == first["id"]
+    rows = run_store.list_for_session(SESSION_DATE)
+    assert len(rows) == 2  # a reuse is its own real attempt, never folded into the first
+    assert rows[1]["outcome"] == "reused"
+    assert rows[1]["playbook_id"] == first["id"]
+    assert rows[1]["signals_recorded"] == rows[0]["signals_recorded"] == 1
+
+
+def test_a_cancelled_walk_leaves_no_store_file_and_no_ledger_row(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    run_store = PlaybookRunStore(tmp_path / "playbook_runs")
+
+    record, _reused = run_playbook_and_record(
+        universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE,
+        should_abort=lambda: True, playbook_run_store=run_store,
+    )
+
+    assert record is None
+    assert playbook_store.list() == ([], [])  # a partial walk is never recorded
+    assert run_store.list() == ([], [])  # ...and never logged either (unlike the forward ledger)
+
+
+def test_a_non_session_date_is_refused_and_logs_a_refused_row(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    for day in ("2026-06-19", "2026-06-20", "2026-06-22"):
+        from datetime import datetime
+        epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
+        _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", epoch, 100.0, 101.0, 99.0, 100.0)])
+    run_store = PlaybookRunStore(tmp_path / "playbook_runs")
+
+    with pytest.raises(PlaybookSessionRefused) as exc_info:
+        run_playbook_and_record(
+            universe_store, bar_store, CONFIG, playbook_store, "2026-06-21",
+            playbook_run_store=run_store,
+        )
+
+    evidence = session_evidence(bar_store, ["AAA"])
+    assert str(exc_info.value) == non_session_refusal("2026-06-21", evidence)
+    assert playbook_store.list() == ([], [])
+    rows, _errors = run_store.list()
+    assert len(rows) == 1
+    assert rows[0]["outcome"] == "refused_non_session"
+    assert rows[0]["playbook_id"] is None
+
+
+def test_a_failing_walk_records_a_failed_row_and_re_raises(tmp_path, env, monkeypatch):
+    bar_store, universe_store, playbook_store = env
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    run_store = PlaybookRunStore(tmp_path / "playbook_runs")
+
+    def _boom(*_args, **_kwargs):
+        raise RuntimeError("the bar store went away mid-walk")
+
+    monkeypatch.setattr(desk_playbook_compute, "compute_playbook", _boom)
+
+    with pytest.raises(RuntimeError, match="went away mid-walk"):
+        run_playbook_and_record(
+            universe_store, bar_store, CONFIG, playbook_store, SESSION_DATE,
+            playbook_run_store=run_store,
+        )
+
+    rows, _errors = run_store.list()
+    assert len(rows) == 1
+    assert rows[0]["outcome"] == "failed"
+    assert rows[0]["error"] == "the bar store went away mid-walk"
+    assert rows[0]["playbook_id"] is None
+
+
+# --- the manager: single-flight + cancel (TC-13, TC-15) --------------------------------------------
+
+
+def test_manager_single_flight_second_trigger_returns_the_same_job(env, monkeypatch):
+    bar_store, universe_store, playbook_store = env
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+
+    started = threading.Event()
+    release = threading.Event()
+
+    def _blocking_compute(universe_store_arg, bar_store_arg, fp, session_date_arg, *, progress=None, should_abort=None):
+        started.set()
+        release.wait(timeout=5)
+        from app.research.desk_playbook import compute_playbook as _real
+        return _real(universe_store_arg, bar_store_arg, fp, session_date_arg)
+
+    monkeypatch.setattr(desk_playbook_compute, "compute_playbook", _blocking_compute)
+    manager = DeskPlaybookComputeManager()
+    first = manager.trigger(SESSION_DATE, universe_store, bar_store, CONFIG, playbook_store)
+    assert first["started"] is True
+    assert started.wait(timeout=5)
+
+    second = manager.trigger(SESSION_DATE, universe_store, bar_store, CONFIG, playbook_store)
+    assert second["started"] is False
+    assert second["compute"]["session_date"] == first["compute"]["session_date"] == SESSION_DATE
+
+    release.set()
+    snap = _wait_for_terminal(manager)
+    assert snap["status"] == "done"
+    assert snap["signals_total"] == 1  # one universe member
+    manager.join_all(timeout=5)
+
+
+def test_manager_cancel_mid_walk_records_nothing_and_reverts_to_idle(env, monkeypatch):
+    bar_store, universe_store, playbook_store = env
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+
+    entered = threading.Event()
+    release = threading.Event()
+    from app.research.desk_playbook import compute_playbook as real_compute
+
+    def _pausing_compute(universe_store_arg, bar_store_arg, fp, session_date_arg, *, progress=None, should_abort=None):
+        entered.set()
+        release.wait(timeout=5)
+        return real_compute(
+            universe_store_arg, bar_store_arg, fp, session_date_arg,
+            progress=progress, should_abort=should_abort,
+        )
+
+    monkeypatch.setattr(desk_playbook_compute, "compute_playbook", _pausing_compute)
+    manager = DeskPlaybookComputeManager()
+    manager.trigger(SESSION_DATE, universe_store, bar_store, CONFIG, playbook_store)
+    assert entered.wait(timeout=5)
+
+    manager.cancel()
+    cancelling_snap = manager.snapshot()
+    assert cancelling_snap["status"] == "cancelling"
+
+    release.set()
+    snap = _wait_for_terminal(manager)
+    # a completed cancel leaves NO distinct terminal marker -- it reverts to the idle shape
+    assert snap == {
+        "status": "idle", "session_date": None, "signals_done": 0, "signals_total": 0, "error": None,
+    }
+    assert playbook_store.list() == ([], [])
+    manager.join_all(timeout=5)
+
+
+def test_manager_snapshot_is_idle_before_any_job_has_ever_run():
+    manager = DeskPlaybookComputeManager()
+    assert manager.snapshot() == {
+        "status": "idle", "session_date": None, "signals_done": 0, "signals_total": 0, "error": None,
+    }
+
+
+# --- the routes --------------------------------------------------------------------------------------
+
+
+@pytest.fixture
+def route_ctx(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(store, CONFIG)
+    set_registry(registry)
+    fresh_manager = DeskPlaybookComputeManager()
+    app.dependency_overrides[get_desk_playbook_compute_manager] = lambda: fresh_manager
+    with TestClient(app) as client:
+        yield client, fresh_manager, tmp_path
+    fresh_manager.join_all(timeout=5.0)
+    set_registry(None)
+    app.dependency_overrides.pop(get_desk_playbook_compute_manager, None)
+    store.close()
+
+
+def test_routes_honest_idle_and_idle_cancel_409(route_ctx):
+    client, _manager, _tmp = route_ctx
+    idle = client.get("/research/desk/playbook/compute")
+    assert idle.status_code == 200
+    assert idle.json() == {
+        "status": "idle", "session_date": None, "signals_done": 0, "signals_total": 0, "error": None,
+    }
+
+    idle_cancel = client.post("/research/desk/playbook/compute/cancel")
+    assert idle_cancel.status_code == 409
+
+    runs = client.get("/research/desk/playbook/runs")
+    assert runs.status_code == 200
+    assert runs.json() == {"runs": [], "latest": None, "integrity_errors": []}
+
+
+def test_trigger_refuses_a_non_session_date_before_starting_a_job(route_ctx):
+    client, manager, tmp = route_ctx
+    bar_store = BarStore(tmp / "bars")
+    for day in ("2026-06-19", "2026-06-20", "2026-06-22"):
+        from datetime import datetime
+        epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
+        _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", epoch, 100.0, 101.0, 99.0, 100.0)])
+    universe_store = UniverseStore(tmp / "universe")
+    universe_store.record(
+        members=["AAA"], raw_members={"AAA": "AAA"}, source_url="test", min_members=1, max_members=10,
+    )
+
+    response = client.post("/research/desk/playbook/compute", json={"session_date": "2026-06-21"})
+    assert response.status_code == 422
+    assert "not a recorded trading session" in response.json()["detail"]
+    assert manager.snapshot()["status"] == "idle"  # no job was ever created
+
+    runs = client.get("/research/desk/playbook/runs").json()
+    assert runs == {"runs": [], "latest": None, "integrity_errors": []}  # -- and no ledger row
+
+
+def test_route_compute_runs_to_done_and_the_runs_route_records_it(route_ctx):
+    client, manager, tmp = route_ctx
+    bar_store = BarStore(tmp / "bars")
+    universe_store = UniverseStore(tmp / "universe")
+    universe_store.record(
+        members=["AAA"], raw_members={"AAA": "AAA"}, source_url="test", min_members=1, max_members=10,
+    )
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+
+    trigger = client.post("/research/desk/playbook/compute", json={"session_date": SESSION_DATE})
+    assert trigger.status_code == 200
+    body = trigger.json()
+    assert body["started"] is True
+    assert body["compute"]["signals_total"] == 1
+
+    snap = _wait_for_terminal(manager)
+    assert snap["status"] == "done"
+
+    served = client.get("/research/desk/playbook", params={"date": SESSION_DATE})
+    payload = served.json()
+    assert payload["versions"] == 1
+    record = payload["playbook"]
+    assert len(record["signals"]) == 1
+    assert record["signals"][0]["forward"] is not None
+
+    runs = client.get("/research/desk/playbook/runs").json()
+    assert len(runs["runs"]) == 1
+    row = runs["runs"][0]
+    assert row["outcome"] == "recorded"
+    assert row["playbook_id"] == record["id"]
+    assert runs["latest"]["run_id"] == row["run_id"]
+
+    narrowed = client.get("/research/desk/playbook/runs", params={"session_date": SESSION_DATE}).json()
+    assert [r["run_id"] for r in narrowed["runs"]] == [row["run_id"]]
+    other = client.get("/research/desk/playbook/runs", params={"session_date": "2099-01-01"}).json()
+    assert other == {"runs": [], "latest": None, "integrity_errors": []}
+
+
+def test_a_second_trigger_while_running_is_refused_single_flight(route_ctx, monkeypatch):
+    client, manager, tmp = route_ctx
+    bar_store = BarStore(tmp / "bars")
+    universe_store = UniverseStore(tmp / "universe")
+    universe_store.record(
+        members=["AAA"], raw_members={"AAA": "AAA"}, source_url="test", min_members=1, max_members=10,
+    )
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+
+    started = threading.Event()
+    release = threading.Event()
+
+    def _blocking_compute(universe_store_arg, bar_store_arg, fp, session_date_arg, *, progress=None, should_abort=None):
+        started.set()
+        release.wait(timeout=5)
+        from app.research.desk_playbook import compute_playbook as _real
+        return _real(universe_store_arg, bar_store_arg, fp, session_date_arg)
+
+    monkeypatch.setattr(desk_playbook_compute, "compute_playbook", _blocking_compute)
+
+    first = client.post("/research/desk/playbook/compute", json={"session_date": SESSION_DATE})
+    assert first.json()["started"] is True
+    assert started.wait(timeout=5)
+
+    second = client.post("/research/desk/playbook/compute", json={"session_date": SESSION_DATE})
+    assert second.json()["started"] is False
+
+    cancel = client.post("/research/desk/playbook/compute/cancel")
+    assert cancel.status_code == 200
+
+    release.set()
+    _wait_for_terminal(manager)
+    manager.join_all(timeout=5)
+
+
+# --- the CLI (TC-14) ---------------------------------------------------------------------------------
+
+
+def test_cli_records_a_real_signature_matched_record_and_a_non_session_date_exits_1(tmp_path, monkeypatch):
+    """The CLI drives the SAME shared ``run_playbook_and_record`` entry point the API route's
+    background worker calls (this module's own docstring) -- there is no second code path for it
+    to diverge onto. This proves the CLI-triggered record is genuinely real (right shape, right
+    signature) and that its non-session refusal exits 1, naming the date."""
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
... [diff_bound] apps/backend/tests/test_desk_playbook_compute.py: 36 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_playbook_log.py b/apps/backend/tests/test_desk_playbook_log.py
new file mode 100644
index 0000000..7494d99
--- /dev/null
+++ b/apps/backend/tests/test_desk_playbook_log.py
@@ -0,0 +1,280 @@
+"""``desk_playbook_log.py`` (Era B2, J-02) — the playbook-run log's store discipline: checksum
+verification, structural append-only-ness (no update/delete path, no content dedup — every call to
+``record`` is a genuinely new file), the interrupted-run-leaves-no-record guarantee, the
+per-session read, and the directory-resolution seam. Mirrors ``test_desk_forward_log.py``'s own
+store-level test shape, with ONE deliberate divergence: this store's terminal-outcome set has no
+``"cancelled"`` value at all (a cancelled playbook run leaves no row — see the module docstring).
+
+The shared-writer contract itself (proving ``record_playbook_run`` is called from inside
+``run_playbook_and_record``, the ONE entry point both ``DeskPlaybookComputeManager`` and the CLI
+call) is exercised end to end in ``test_desk_playbook_compute.py`` — this file covers the store
+module in isolation."""
+
+from __future__ import annotations
+
+import json
+
+import pytest
+
+from app.research.desk_playbook_log import (
+    PlaybookRunIntegrityError,
+    PlaybookRunStore,
+    record_playbook_run,
+    resolve_desk_playbook_log_dir,
+)
+
+
+def _record_sample(
+    store: PlaybookRunStore,
+    *,
+    outcome: str = "recorded",
+    started_at: str = "2026-08-10T22:37:02.000000Z",
+    finished_at: str = "2026-08-10T22:37:26.000000Z",
+    session_date: str = "2026-06-22",
+    config_fingerprint: str = "08e471b10130e1e2",
+    playbook_input_signature: str | None = "3ba0e5c0c85b7555",
+    signals_recorded: int = 1,
+    playbook_id: str | None = "playbook-2026-06-22-eccfa5dff487",
+    error: str | None = None,
+) -> dict:
+    return record_playbook_run(
+        store,
+        session_date=session_date,
+        config_fingerprint=config_fingerprint,
+        playbook_input_signature=playbook_input_signature,
+        started_at=started_at,
+        finished_at=finished_at,
+        outcome=outcome,
+        signals_recorded=signals_recorded,
+        playbook_id=playbook_id,
+        error=error,
+    )
+
+
+# --- record: shape + provenance ------------------------------------------------------------------
+
+
+def test_record_stores_every_field_verbatim(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    meta = _record_sample(store)
+
+    assert meta["run_id"].startswith("playbookrun-2026-08-10-")
+    assert meta["session_date"] == "2026-06-22"
+    assert meta["config_fingerprint"] == "08e471b10130e1e2"
+    assert meta["playbook_input_signature"] == "3ba0e5c0c85b7555"
+    assert meta["started_at"] == "2026-08-10T22:37:02.000000Z"
+    assert meta["finished_at"] == "2026-08-10T22:37:26.000000Z"
+    assert meta["outcome"] == "recorded"
+    assert meta["signals_recorded"] == 1
+    assert meta["playbook_id"] == "playbook-2026-06-22-eccfa5dff487"
+    assert meta["error"] is None
+
+
+def test_the_run_id_takes_its_date_from_when_the_run_started_not_the_session_date(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    meta = _record_sample(store, session_date="2025-01-01", started_at="2026-08-10T22:37:02Z")
+    assert meta["run_id"].startswith("playbookrun-2026-08-10-")
+
+
+def test_record_rejects_a_non_terminal_outcome(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    with pytest.raises(ValueError, match="invalid terminal outcome"):
+        _record_sample(store, outcome="running")
+
+
+def test_record_rejects_cancelled_as_an_outcome(tmp_path):
+    """The one deliberate divergence from the forward-returns ledger: a cancelled playbook run is
+    never logged at all (the CALLER never invokes this writer for one), so ``"cancelled"`` is not
+    even a valid value on this store — a caller attempting it is a programming error, not a real
+    terminal state to represent."""
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    with pytest.raises(ValueError, match="invalid terminal outcome"):
+        _record_sample(store, outcome="cancelled")
+
+
+def test_a_failed_run_carries_its_error_verbatim_and_names_no_record(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    meta = _record_sample(
+        store, outcome="failed", playbook_id=None, error="the bar store went away mid-walk",
+        signals_recorded=0,
+    )
+    assert meta["outcome"] == "failed"
+    assert meta["error"] == "the bar store went away mid-walk"
+    assert meta["playbook_id"] is None
+
+
+def test_a_refused_non_session_run_carries_the_refusal_sentence_and_names_no_record(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    meta = _record_sample(
+        store, outcome="refused_non_session", playbook_id=None, signals_recorded=0,
+        playbook_input_signature=None, error="2026-06-21 is not a recorded trading session -- ...",
+    )
+    assert meta["outcome"] == "refused_non_session"
+    assert meta["playbook_id"] is None
+    assert meta["playbook_input_signature"] is None
+    assert "not a recorded trading session" in meta["error"]
+
+
+def test_a_reused_run_reports_the_existing_records_own_signal_count(tmp_path):
+    """A reuse short-circuits the walk but is NOT an empty measurement: the count it reports is the
+    one the walk it skipped produced, never a misleading zero."""
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    meta = _record_sample(store, outcome="reused", signals_recorded=3)
+    assert meta["outcome"] == "reused"
+    assert meta["signals_recorded"] == 3
+    assert meta["playbook_id"] == "playbook-2026-06-22-eccfa5dff487"
+
+
+# --- list / list_for_session -----------------------------------------------------------------------
+
+
+def test_list_serves_the_stored_record_verbatim(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    meta = _record_sample(store)
+    records, errors = store.list()
+    assert errors == []
+    assert records == [meta]
+
+
+def test_store_survives_a_reload_from_disk(tmp_path):
+    root = tmp_path / "playbook_runs"
+    meta = _record_sample(PlaybookRunStore(root))
+    records, errors = PlaybookRunStore(root).list()
+    assert errors == []
+    assert records == [meta]
+
+
+def test_list_on_a_directory_that_was_never_created_is_honestly_empty(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    assert store.list() == ([], [])
+
+
+def test_list_for_session_filters_to_one_date_oldest_first(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    older = _record_sample(store, started_at="2026-08-10T22:00:00Z")
+    newer = _record_sample(store, started_at="2026-08-10T23:00:00Z", outcome="reused")
+    _record_sample(store, session_date="2026-06-19")
+
+    for_session = store.list_for_session("2026-06-22")
+    assert [record["run_id"] for record in for_session] == [older["run_id"], newer["run_id"]]
+
+
+def test_list_for_session_on_an_unknown_date_is_honestly_empty(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    _record_sample(store)
+    assert store.list_for_session("2099-01-01") == []
+
+
+# --- append-only: every call to record is a genuinely NEW file, never a dedup/update ---------------
+
+
+def test_two_calls_with_identical_field_values_still_append_two_distinct_records(tmp_path):
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    first = _record_sample(store)
+    second = _record_sample(store)
+    assert first["run_id"] != second["run_id"]
+    records, errors = store.list()
+    assert errors == []
+    assert {r["run_id"] for r in records} == {first["run_id"], second["run_id"]}
+
+
+def test_a_second_run_appends_without_touching_the_first_files_bytes_on_disk(tmp_path):
+    root = tmp_path / "playbook_runs"
+    store = PlaybookRunStore(root)
+    first = _record_sample(store, started_at="2026-08-10T22:00:00Z")
+    first_path = root / f"{first['run_id']}.json"
+    first_bytes_before = first_path.read_bytes()
+
+    second = _record_sample(store, started_at="2026-08-10T23:00:00Z", outcome="reused")
+
+    assert first_path.read_bytes() == first_bytes_before  # byte-unchanged
+    records, errors = store.list()
+    assert errors == []
+    assert [record["run_id"] for record in records] == [first["run_id"], second["run_id"]]
+
+
+def test_playbook_run_store_has_no_update_or_delete_method():
+    """Structural immutability: the only mutation on this class is ``record``."""
+    public_methods = {name for name in dir(PlaybookRunStore) if not name.startswith("_")}
+    assert public_methods == {"root", "list", "list_for_session", "record"}
+
+
+# --- interrupted/cancelled-run honesty: BOTH leave zero record --------------------------------------
+
+
+def test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched(tmp_path):
+    """Stands in for a crash AND for a cooperative cancel alike — both never call
+    ``record_playbook_run`` (the module docstring's terminal-excludes-cancelled contract) — the
+    store gains zero new file either way."""
+    store = PlaybookRunStore(tmp_path / "playbook_runs")
+    # ... the walk would happen here in a real run; the process ends (or the walk is cancelled)
+    # before this line runs: record_playbook_run(store, ...)
+    records, errors = store.list()
+    assert records == []
+    assert errors == []
+    assert not (tmp_path / "playbook_runs").exists()
+
+
+# --- integrity: a corrupted file is explicit, never silent ----------------------------------------
+
+
+def test_corrupted_run_record_file_surfaces_explicitly_in_list_errors(tmp_path):
+    root = tmp_path / "playbook_runs"
+    store = PlaybookRunStore(root)
+    _record_sample(store)
+    path = next(root.glob("*.json"))
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["signals_recorded"] = 999  # tamper -- file_checksum now disagrees
+    path.write_text(json.dumps(data))
+
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1
+    assert path.name == errors[0]["file"]
+    assert "integrity" in errors[0]["error"]
+
+
+def test_load_raises_playbook_run_integrity_error_for_unparseable_json(tmp_path):
+    root = tmp_path / "playbook_runs"
+    root.mkdir(parents=True)
+    (root / "playbookrun-2026-01-01-deadbeef0000.json").write_text("{not json")
+
+    records, errors = PlaybookRunStore(root).list()
+    assert records == []
+    assert len(errors) == 1
+
+
+def test_corrupted_file_does_not_block_other_valid_records_from_listing(tmp_path):
+    root = tmp_path / "playbook_runs"
+    store = PlaybookRunStore(root)
+    good = _record_sample(store)
+    (root / "playbookrun-2026-01-01-deadbeef0000.json").write_text("{not json")
+
+    records, errors = store.list()
+    assert len(records) == 1 and records[0]["run_id"] == good["run_id"]
+    assert len(errors) == 1
+
+
+def test_load_raises_playbook_run_integrity_error_directly_for_a_missing_meta_shape(tmp_path):
+    root = tmp_path / "playbook_runs"
+    root.mkdir(parents=True)
+    path = root / "playbookrun-2026-01-01-deadbeef0000.json"
+    path.write_text(json.dumps({"unexpected": "shape"}))
+
+    store = PlaybookRunStore(root)
+    with pytest.raises(PlaybookRunIntegrityError):
+        store._load(path)  # noqa: SLF001 -- direct unit test of the private loader's own raise
+
+
+# --- resolve_desk_playbook_log_dir -- zero new Config field ------------------------------------------
+
+
+def test_resolve_desk_playbook_log_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
+    monkeypatch.delenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", raising=False)
+    resolved = resolve_desk_playbook_log_dir("/some/root/.data/universe")
+    assert resolved == "/some/root/.data/playbook_runs"
+
+
+def test_resolve_desk_playbook_log_dir_env_override(monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", "/tmp/custom-playbook-log-dir")
+    assert resolve_desk_playbook_log_dir("/some/root/.data/universe") == "/tmp/custom-playbook-log-dir"
```
