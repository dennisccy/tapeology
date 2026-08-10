# Iteration diff (bounded)

Files changed: 7. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/desk_playbook.py` (185 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 87daa2a..4d900b4 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -123,6 +123,7 @@ from .desk_forward import ForwardStore, resolve_desk_forward_dir
 from .desk_forward_compute import DeskForwardComputeManager
 from .desk_forward_log import ForwardRunStore, resolve_desk_forward_log_dir
 from .desk_forward_pins import resolve_desk_forward_pins
+from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
 from .desk_screen_diff import ScreenDiffSelfCompareError, compute_screen_diff
@@ -946,6 +947,80 @@ def get_desk_forward_pins(
     )
 
 
+# --- The Playbook (Era B2, J-01) — pre-registered, lookahead-clean intraday setups detected on the
+# desk's own recorded 5m/1m bars (docs/playbook-detector-spec.md). J-01 ships detection only (no
+# measurement, no compute-manager/trigger route, no CLI) plus this ONE read; see desk_playbook.py
+# for the computation, store, and parameters/signature recipe this route only serves verbatim. ----
+
+
+def get_playbook_store() -> PlaybookStore:
+    """The playbook store rooted at a bare env-var-or-sibling-of-the-universe-dir default (zero new
+    ``Config`` field — see ``desk_playbook.resolve_desk_playbook_dir``) — the ``get_forward_store``
+    pattern. A FastAPI dependency so tests can point it at a temp dir via the env var or override
+    it outright."""
+    return PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def _playbook_meta_only(record: dict) -> dict:
+    """The lightweight projection the bulk list serves — id/pins/parameters/counts only, never the
+    full ``signals``/``absences``/``diagnostics`` lists (the ``_forward_meta_only`` convention)."""
+    return {
+        "id": record["id"],
+        "session_date": record["session_date"],
+        "config_fingerprint": record["config_fingerprint"],
+        "playbook_input_signature": record["playbook_input_signature"],
+        "payload_version": record["payload_version"],
+        "parameters": record["parameters"],
+        "recorded_at": record["recorded_at"],
+        "counts": {
+            "signals": len(record["signals"]),
+            "absences": len(record["absences"]),
+            "diagnostics": len(record["diagnostics"]),
+        },
+    }
+
+
+@router.get("/playbook")
+def get_playbook(
+    date: str | None = None, id: str | None = None, store: PlaybookStore = Depends(get_playbook_store)
+) -> dict:
+    """Three shapes, selected by ``?date=``/``?id=`` (the ``GET /research/desk/screen`` convention):
+
+      * neither given: ``{"playbooks": [...meta-only...], "latest": <full record>|null,
+        "integrity_errors": [...]}`` — an explicit HTTP 200 honest-empty payload
+        (``{"playbooks": [], "latest": null, "integrity_errors": []}``) before any playbook has
+        ever been computed, never a 404. ``latest`` is the most recently RECORDED playbook (a
+        playbook, like a forward measurement and unlike a screen, is an ATTEMPT that can carry
+        several versions per date as parameters change — ``desk_forward``'s ``latest`` convention,
+        not ``desk_screen``'s date-first one).
+      * ``date=YYYY-MM-DD`` (``id`` absent): ``{"playbook": <newest record for that date>|null,
+        "versions": <how many records that date has ever accumulated>}`` — a plain read, never
+        recomputed on the GET; an unknown date is an honest ``null``/``0`` at HTTP 200.
+      * ``id=<record id>`` (``date`` absent): ``{"playbook": <that exact persisted record>|null}``
+        — the only way to reach an EARLIER same-date recording once a later one exists (``?date=``
+        always resolves to the newest match); an unknown id is an honest ``null``, never a 404.
+      * ``id`` and ``date`` both given: an honest 4xx refusal — never a silent precedence rule.
+
+    A plain read: writes nothing, triggers nothing, recomputes nothing (GET-never-computes) — this
+    route takes no ``BarStore``/``UniverseStore``/compute-manager dependency at all, so it is
+    structurally incapable of triggering ``compute_playbook``."""
+    if id is not None and date is not None:
+        raise HTTPException(
+            status_code=422, detail="only one of `id` or `date` may be supplied, not both"
+        )
+    if id is not None:
+        return {"playbook": store.get(id)}
+    if date is not None:
+        newest, versions = store.newest_for_date(date)
+        return {"playbook": newest, "versions": versions}
+    records, errors = store.list()
+    return {
+        "playbooks": [_playbook_meta_only(r) for r in records],
+        "latest": records[-1] if records else None,
+        "integrity_errors": errors,
+    }
+
+
 # --- Coverage-index reconciliation (J-10, goal-desk-iter-14) — a trigger/poll/cancel trio mirroring
 # the top-up compute trio exactly, plus ONE durable read mirroring ``GET /research/desk/topup/runs``.
 # See ``desk_index_reconcile.py`` for the classify/repair/record mechanics this only wires up. -------
diff --git a/apps/backend/app/research/desk_playbook.py b/apps/backend/app/research/desk_playbook.py
new file mode 100644
index 0000000..97efd1b
--- /dev/null
+++ b/apps/backend/app/research/desk_playbook.py
@@ -0,0 +1,579 @@
+"""The Playbook (Era B2 "The Playbook", J-01/J-02) -- the book's intraday setups
+(Graifer & Schumacher, *Techniques of Tape Reading*, 2004), detected on the desk's own recorded
+5m/1m bars and measured with the desk forward rail's own conventions. This module owns the
+pre-registered constant table, the parameters/signature recipe, the append-only store, and the
+per-session compute walker; ``app/research/desk_playbook_features.py`` owns the shared primitives
+and ``app/research/desk_playbook_detect.py`` owns the detectors themselves -- see
+``docs/playbook-detector-spec.md`` for the canonical rule set every constant/detector here
+implements verbatim.
+
+**A THIRD "setup" vocabulary -- never conflate.** ``setups.py`` (the tick-touch-of-a-structural-
+level scanner) and ``backtests.py`` (tape-arming occurrences under a strategy profile) ALREADY use
+"setup" for two OTHER things. A playbook signal is the book's intraday PATTERN (an opening-range
+break, a jump-base-explosion, ...) -- a third, unrelated sense of the word. This module never
+imports from ``setups.py`` or ``backtests.py``, and no field here is ever named ``stop_loss``
+(the field is ``invalidation_price`` -- a disclosed structural level, never an order concept).
+
+**Detection only, this iteration.** ``compute_playbook`` walks the desk universe's members and
+detects the opening-range-break family (spec §3.1-3.2); trigger-anchored measurement (forward
+returns, ``invalidation_breached``, the seeded baseline) is J-02 -- ``entry``/``entry_kind`` are
+computed now (spec §0's stop-through fill convention is part of a signal's own GEOMETRY, decided
+at the trigger bar, not part of measuring what happened afterward).
+
+**Parameters discipline (the ``desk_forward.forward_parameters`` pattern, applied at birth).**
+``playbook_parameters()`` reads every constant below at CALL TIME (so a test monkeypatching one
+genuinely moves both the served blob and the signature) and embeds the measurement rail's own
+horizon/seed/measure-shape constants verbatim -- a FUTURE change to ``desk_forward.py`` would
+re-key every playbook record instead of silently reinterpreting it, even though this iteration
+does no measurement at all. ``compute_playbook_input_signature`` mirrors
+``desk_forward.compute_forward_input_signature`` exactly: sha256[:16] over the sorted
+``(symbol, timeframe, series_id, checksum)`` tuples of every series the compute could read
+(members union {SPY}, the two fine timeframes only) plus the config fingerprint plus the
+parameters blob.
+
+**Store discipline (the ``desk_forward.ForwardStore`` pattern).** ``PlaybookStore`` is a 2-pin
+(``session_date``, ``playbook_input_signature``) append-only file store: every load verifies a
+whole-record checksum, an identical key is refused (never silently reused as a second file), a
+corrupt file is surfaced loudly and never overwritten, and -- structurally, by never being written
+-- there is no update or delete method anywhere on this class. A changed constant re-keys and
+mints a NEW version; every older recorded file stays byte-identical forever.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+from datetime import datetime, timezone
+from pathlib import Path
+
+from .desk_forward import (
+    DESK_FORWARD_BASELINE_SEED,
+    DESK_FORWARD_HORIZONS_MINUTES,
+    DESK_FORWARD_HORIZON_MEASURES,
+    DESK_FORWARD_MEASURE_KEYS,
+)
+from .desk_playbook_detect import detect_opening_range_breaks
+from .desk_playbook_features import baselines, opening_range, rth_session_slice
+from .desk_sessions import refuse_if_not_a_session
+
+__all__ = [
+    "PLAYBOOK_SETUPS",
+    "PLAYBOOK_MARKET_SYMBOL",
+    "PLAYBOOK_REGISTER",
+    "PlaybookIntegrityError",
+    "PlaybookAlreadyRecorded",
+    "PlaybookSessionRefused",
+    "PlaybookStore",
+    "resolve_desk_playbook_dir",
+    "playbook_parameters",
+    "compute_playbook_input_signature",
+    "compute_playbook",
+]
+
+# --- Pre-registered constants (docs/playbook-detector-spec.md §1 -- the COMPLETE tunable surface,
+# transcribed verbatim; nothing else exists). Every one is embedded in `playbook_parameters()` and
+# hashed into the input signature, whether or not a detector built so far actually reads it -- the
+# table is declared whole (T-1: "no threshold exists outside the spec"), detectors are built
+# incrementally. BOOK = the book's own stated number; ADAPTATION = a single named choice where the
+# book is vague (rationale in the spec doc; not re-derived here). ------------------------------------
+
+PLAYBOOK_BASELINE_SESSIONS: int = 20  # ADAPTATION -- Card 5.5's RVOL convention
+PLAYBOOK_MIN_BASELINE_SESSIONS: int = 10  # ADAPTATION -- minimum honest median
+PLAYBOOK_RVOL_SURGE: float = 2.0  # ADAPTATION -- book's "volume surge" unquantified
+PLAYBOOK_RVOL_ELEVATED: float = 1.5  # ADAPTATION -- Card 5.5 high-RVOL bucket boundary
+PLAYBOOK_RVOL_DRYUP: float = 0.7  # ADAPTATION -- Card 5.5 low-RVOL bucket boundary
+PLAYBOOK_VOL_CONTRAST_RATIO: float = 0.6  # ADAPTATION -- mechanical "dries on pullback" ratio
+PLAYBOOK_MAX_CHASE_FRAC: float = 0.002  # BOOK -- 3-5c chase on ~$20 approx 0.2%
+PLAYBOOK_STOP_PAD_FRAC: float = 0.30  # BOOK -- 20-40% stop padding; midpoint
+PLAYBOOK_OR_MINUTES: int = 15  # BOOK -- opening range = first 15-20 min; lower endpoint
+# ADAPTATION, not tabulated in the spec's own §1 table -- stated in §2 primitive 2's prose ONLY
+# ("fewer than 10 of the 15 one-minute bars on file -> fall back"). Named here rather than left an
+# inline literal so it still passes through `playbook_parameters()`/the signature like every other
+# threshold; flagged in the dev handoff for an owner ruling on whether §1 should gain this row.
+PLAYBOOK_OR_MIN_1M_BARS: int = 10
+PLAYBOOK_NARROW_OR_MAX_MBR: float = 3.0  # ADAPTATION -- relative form of the <=25c narrow range
+PLAYBOOK_JUMP_MIN_MULT: float = 1.5  # BOOK -- jump >= 1.5-2x base; stated minimum
+PLAYBOOK_JUMP_MIN_MOVE_MBR: float = 3.0  # ADAPTATION -- floor so tiny/tiny can't satisfy the ratio
+PLAYBOOK_JUMP_LOOKBACK_BARS: int = 6  # ADAPTATION -- jump low read from the 30 min before the base
+PLAYBOOK_BASE_MIN_BARS: int = 3  # ADAPTATION -- book gives no consolidation duration
+PLAYBOOK_BASE_MAX_BARS: int = 12  # ADAPTATION -- 60-min cap
+PLAYBOOK_BASE_MAX_RANGE_MBR: float = 2.0  # ADAPTATION -- relative form of the <=25c narrow base
+PLAYBOOK_NEAR_EXTREME_MBR: float = 1.0  # ADAPTATION -- mechanical "near the high/low"
+PLAYBOOK_PIVOT_LOOKBACK_BARS: int = 3  # ADAPTATION -- 5m intraday N for the strict-pivot rule
+PLAYBOOK_CUP_MIN_BARS: int = 6  # BOOK -- cup >= 30 min
+PLAYBOOK_CUP_OPTIMAL_BARS: int = 12  # BOOK -- >= 1h optimal (disclosure only)
+PLAYBOOK_HANDLE_MAX_RETRACE_FRAC: float = 0.5  # BOOK -- handle <= 50% of cup depth
+PLAYBOOK_HANDLE_MAX_DURATION_FRAC: float = 0.30  # BOOK -- handle <= 30% of cup duration
+PLAYBOOK_RIM_MATCH_MBR: float = 1.0  # ADAPTATION -- "cup edges at the day's high" tolerance
+PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR: float = 2.0  # ADAPTATION -- min cup depth AND min valley depth
+PLAYBOOK_VERTICAL_WINDOW_BARS: int = 3  # ADAPTATION -- "near-vertical" window (15 min)
+PLAYBOOK_VERTICAL_MOVE_MBR: float = 4.0  # ADAPTATION -- net move for capitulation/euphoria
+PLAYBOOK_VERTICAL_BAR_MBR: float = 2.5  # ADAPTATION -- single-bar spike (spiky-approach flag)
+PLAYBOOK_BOUNCE_MAX_BARS: int = 3  # ADAPTATION -- reversal confirmation must come fast
+PLAYBOOK_RANGE_MIN_WIDTH_MBR: float = 4.0  # ADAPTATION -- narrower = breakout-only per Ch 13
+PLAYBOOK_RANGE_HOLD_TOL_MBR: float = 0.5  # ADAPTATION -- "held" tolerance; absorption-bar max range
+PLAYBOOK_TOPS_MATCH_MBR: float = 1.0  # ADAPTATION -- two tops "at the same level"
+PLAYBOOK_TOPS_MIN_SEPARATION_BARS: int = 4  # ADAPTATION -- tops >= 20 min apart
+PLAYBOOK_LADDER_HEALTHY_LOW: float = 0.50  # BOOK -- ladder step 50-75% of prior step (disclosure)
+PLAYBOOK_LADDER_HEALTHY_HIGH: float = 0.75  # BOOK -- ladder step 50-75% of prior step (disclosure)
+PLAYBOOK_MKT_LOOKBACK_BARS: int = 6  # ADAPTATION -- 30-min index-direction window
+PLAYBOOK_MKT_NEUTRAL_BAND_MBR: float = 1.0  # ADAPTATION -- neutral band, index-MBR units
+PLAYBOOK_MARKER_DECAY_BARS: int = 6  # ADAPTATION -- euphoria/capitulation marker decorates 30 min
+PLAYBOOK_APPROACH_BARS: int = 3  # ADAPTATION -- volume-into-trigger window
+PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION: int = 2  # ADAPTATION -- ladder steps
+
+# Companion structural constants (shape, not thresholds).
+# This iteration implements ONLY the opening-range-break family; J-04/J-05/J-06 EXTEND this tuple
+# as they land their own detectors (a signature-moving, expected, visible change) -- declaring a
+# setup id here before its detector exists would claim a compute that does not happen.
+PLAYBOOK_SETUPS: tuple[str, ...] = ("open_high_break", "open_low_break")
+PLAYBOOK_MARKET_SYMBOL: str = "SPY"
+# The rail's own baseline seed, echoed (not re-derived) -- the seed discipline itself is J-02's;
+# embedding the CONSTANT now is what makes a future rail-seed change re-key playbook records too.
+PLAYBOOK_BASELINE_SEED: int = DESK_FORWARD_BASELINE_SEED
+PLAYBOOK_RETURN_SIGN_CONVENTION: str = "side_relative"
+# The rail's own measure-key shape, echoed verbatim (J-02 measures playbook signals through it).
+PLAYBOOK_SIGNAL_MEASURES: tuple[str, ...] = DESK_FORWARD_MEASURE_KEYS
+PLAYBOOK_MIN_N_DISCLOSURE: int = 12  # evidence low-n tag (J-08) -- a disclosure floor, never a gate
+
+# The visible honesty register carried by every playbook payload. Lint-checked via
+# test_copy_discipline.find_violations (the desk_forward.FORWARD_REGISTER precedent).
+PLAYBOOK_REGISTER = (
+    "pre-registered opening-range-break signals detected on the desk's own recorded 5m/1m bars — "
+    "every threshold is fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
+    "A signal is a recorded observation, not advice: invalidation_price is the book's own "
+    "structural level, disclosed as geometry, never a stop order, a size, or an account concept. "
+    "This record does not yet carry a measurement — forward returns, invalidation-breach, and the "
+    "seeded random-anchor baseline are added by a later compute pass; no fills, no costs, and no "
+    "probability, expectancy, edge, or significance claim are made anywhere on this payload"
+)
+
+_PLAYBOOK_DIR_ENV = "TAPEOLOGY_DESK_PLAYBOOK_DIR"
+_PLAYBOOK_SIGNATURE_TIMEFRAMES: tuple[str, ...] = ("1m", "5m")
+
+
+class PlaybookIntegrityError(Exception):
+    """An on-disk playbook record file failed its checksum verification on load -- corrupted or
+    tampered, surfaced explicitly (never silence, never a fabricated record)."""
+
+
+class PlaybookAlreadyRecorded(Exception):
+    """A playbook record with this EXACT 2-pin key (``session_date``, ``playbook_input_signature``)
+    is already registered. Playbook records are immutable and append-only -- a re-run over
+    identical inputs reuses the existing record, never a second file."""
+
+    def __init__(self, existing_id: str) -> None:
+        self.existing_id = existing_id
+        super().__init__(
+            f"a playbook record with this exact key is already recorded as '{existing_id}' -- "
+            f"playbook records are immutable and are never re-recorded"
+        )
+
+
+class PlaybookSessionRefused(Exception):
+    """``session_date`` is provably not a recorded trading session
+    (``desk_sessions.refuse_if_not_a_session``'s sentence) -- nothing to detect, and
+    ``compute_playbook`` writes nothing (mirrors ``ForwardScreenNotFound``: a whole-computation
+    refusal, raised before any walk starts)."""
+
+
+def resolve_desk_playbook_dir(desk_universe_dir_resolved: str) -> str:
+    """The playbook store's directory: ``TAPEOLOGY_DESK_PLAYBOOK_DIR`` if set, else a ``playbook``
+    SIBLING of the caller's own already-resolved universe directory -- the
+    ``resolve_desk_forward_dir`` pattern verbatim. Deliberately NOT a ``Config`` field."""
+    override = os.environ.get(_PLAYBOOK_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "playbook")
+
+
+def playbook_parameters() -> dict:
+    """The parameters block embedded verbatim in every recorded payload AND hashed into the input
+    signature -- ONE builder so the two can never drift (the ``desk_forward.forward_parameters``
+    pattern). Reads every module constant at CALL TIME, so a test monkeypatching one genuinely
+    moves both the payload and the key. This is also the ONLY dict a detector ever reads playbook
+    thresholds from (``desk_playbook_detect.py`` takes no constant import of its own) -- so "the
+    parameters blob matches what the detector actually used" holds by construction, not by
+    coincidence."""
+    return {
+        "setups": list(PLAYBOOK_SETUPS),
+        "market_symbol": PLAYBOOK_MARKET_SYMBOL,
+        "baseline_seed": PLAYBOOK_BASELINE_SEED,
+        "return_sign_convention": PLAYBOOK_RETURN_SIGN_CONVENTION,
+        "signal_measures": list(PLAYBOOK_SIGNAL_MEASURES),
+        "min_n_disclosure": PLAYBOOK_MIN_N_DISCLOSURE,
+        "baseline_sessions": PLAYBOOK_BASELINE_SESSIONS,
+        "min_baseline_sessions": PLAYBOOK_MIN_BASELINE_SESSIONS,
+        "rvol_surge": PLAYBOOK_RVOL_SURGE,
+        "rvol_elevated": PLAYBOOK_RVOL_ELEVATED,
+        "rvol_dryup": PLAYBOOK_RVOL_DRYUP,
+        "vol_contrast_ratio": PLAYBOOK_VOL_CONTRAST_RATIO,
+        "max_chase_frac": PLAYBOOK_MAX_CHASE_FRAC,
+        "stop_pad_frac": PLAYBOOK_STOP_PAD_FRAC,
+        "or_minutes": PLAYBOOK_OR_MINUTES,
+        "or_min_1m_bars": PLAYBOOK_OR_MIN_1M_BARS,
+        "narrow_or_max_mbr": PLAYBOOK_NARROW_OR_MAX_MBR,
+        "jump_min_mult": PLAYBOOK_JUMP_MIN_MULT,
+        "jump_min_move_mbr": PLAYBOOK_JUMP_MIN_MOVE_MBR,
+        "jump_lookback_bars": PLAYBOOK_JUMP_LOOKBACK_BARS,
+        "base_min_bars": PLAYBOOK_BASE_MIN_BARS,
+        "base_max_bars": PLAYBOOK_BASE_MAX_BARS,
+        "base_max_range_mbr": PLAYBOOK_BASE_MAX_RANGE_MBR,
+        "near_extreme_mbr": PLAYBOOK_NEAR_EXTREME_MBR,
+        "pivot_lookback_bars": PLAYBOOK_PIVOT_LOOKBACK_BARS,
+        "cup_min_bars": PLAYBOOK_CUP_MIN_BARS,
+        "cup_optimal_bars": PLAYBOOK_CUP_OPTIMAL_BARS,
+        "handle_max_retrace_frac": PLAYBOOK_HANDLE_MAX_RETRACE_FRAC,
+        "handle_max_duration_frac": PLAYBOOK_HANDLE_MAX_DURATION_FRAC,
+        "rim_match_mbr": PLAYBOOK_RIM_MATCH_MBR,
+        "min_structure_depth_mbr": PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR,
+        "vertical_window_bars": PLAYBOOK_VERTICAL_WINDOW_BARS,
+        "vertical_move_mbr": PLAYBOOK_VERTICAL_MOVE_MBR,
+        "vertical_bar_mbr": PLAYBOOK_VERTICAL_BAR_MBR,
+        "bounce_max_bars": PLAYBOOK_BOUNCE_MAX_BARS,
+        "range_min_width_mbr": PLAYBOOK_RANGE_MIN_WIDTH_MBR,
+        "range_hold_tol_mbr": PLAYBOOK_RANGE_HOLD_TOL_MBR,
+        "tops_match_mbr": PLAYBOOK_TOPS_MATCH_MBR,
+        "tops_min_separation_bars": PLAYBOOK_TOPS_MIN_SEPARATION_BARS,
+        "ladder_healthy_low": PLAYBOOK_LADDER_HEALTHY_LOW,
+        "ladder_healthy_high": PLAYBOOK_LADDER_HEALTHY_HIGH,
+        "mkt_lookback_bars": PLAYBOOK_MKT_LOOKBACK_BARS,
+        "mkt_neutral_band_mbr": PLAYBOOK_MKT_NEUTRAL_BAND_MBR,
+        "marker_decay_bars": PLAYBOOK_MARKER_DECAY_BARS,
+        "approach_bars": PLAYBOOK_APPROACH_BARS,
+        "max_jbe_signals_per_session": PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION,
+        # The measurement rail's own shape constants, echoed verbatim (embedded at birth, per the
+        # module docstring) -- a FUTURE desk_forward.py change re-keys playbook records instead of
+        # silently reinterpreting them, even though J-01 measures nothing itself.
+        "rail_horizons_minutes": [list(pair) for pair in DESK_FORWARD_HORIZONS_MINUTES],
+        "rail_baseline_seed": DESK_FORWARD_BASELINE_SEED,
+        "rail_horizon_measures": list(DESK_FORWARD_HORIZON_MEASURES),
+    }
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding every checksum in this module hashes -- the SAME encoding
+    every other desk store hashes (``desk_forward.py._canonical`` et al)."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def compute_playbook_input_signature(bar_store, members: list[str], config_fingerprint: str) -> str:
+    """The playbook record's own input pin: sha256[:16] over the sorted ``(symbol, timeframe,
+    series_id, checksum)`` tuples of every recorded series the compute could possibly read
+    (``members`` union ``{SPY}``, the two fine timeframes ONLY), plus the config fingerprint and
+    the canonical parameters blob -- ``desk_forward.compute_forward_input_signature``'s recipe
+    verbatim. Metadata-only (``list(include_bars=False)``): resolving the pin costs no bar reads."""
+    records, _errors = bar_store.list(include_bars=False)
+    wanted = set(members) | {PLAYBOOK_MARKET_SYMBOL}
+    tuples = sorted(
+        (record["symbol"], record["timeframe"], record["id"], record["checksum"])
+        for record in records
+        if record["symbol"] in wanted and record["timeframe"] in _PLAYBOOK_SIGNATURE_TIMEFRAMES
+    )
+    return _sha256(_canonical([tuples, config_fingerprint, playbook_parameters()]))[:16]
+
+
+def _prior_session_close(bars_5m: list, session_date: str) -> float | None:
+    """The most recent PRIOR RTH session's own last 5m close, for ``geometry.
+    open_vs_prior_close_pct``'s gap-context disclosure -- ``None`` (never a guess) when no earlier
+    session is on file. A small, self-contained scan (distinct from ``baselines()``'s own prior-
+    dates walk -- that one pools MANY sessions for a median; this one only ever needs the single
+    most recent one)."""
+    all_dates = sorted(
+        {datetime.fromtimestamp(bar.epoch, tz=timezone.utc).date().isoformat() for bar in bars_5m}
+    )
+    priors = [d for d in all_dates if d < session_date]
+    if not priors:
+        return None
+    prior_bars = rth_session_slice(bars_5m, priors[-1])
+    return prior_bars[-1].close if prior_bars else None
+
+
+def compute_playbook(universe_store, bar_store, config_fingerprint: str, session_date: str) -> dict:
+    """Detect the opening-range-break family for EVERY member of the latest registered universe
+    snapshot, on ``session_date``'s own recorded bars -- returns everything ``PlaybookStore.record``
+    needs minus the store-assigned ``id``/``recorded_at`` (the ``compute_forward``/``compute_screen``
+    contract shape: a PURE compute, never itself a store write).
+
+    Session-honesty first: ``desk_sessions.refuse_if_not_a_session`` is checked before any bar is
+    read for detection (no separate compute-manager/route layer exists yet this iteration, so this
+    function plays that role) -- a non-session date raises ``PlaybookSessionRefused`` and NOTHING
+    is walked. Per member: no 5m bars for the session, a thin/zero baseline, or no buildable opening
+    range are each a disclosed ``absences`` row (never a crash, never a guess); everything else
+    reaches the detector, which may add a signal, an ``ambiguous_outside_bar`` diagnostic, or
+    neither (a legitimate "the setup did not form" outcome -- not an absence)."""
+    universe_records, _universe_errors = universe_store.list()
+    members = list(universe_records[-1]["members"]) if universe_records else []
+
+    refusal = refuse_if_not_a_session(session_date, bar_store, members)
+    if refusal is not None:
+        raise PlaybookSessionRefused(refusal)
+
+    params = playbook_parameters()
+    signature = compute_playbook_input_signature(bar_store, members, config_fingerprint)
+    index_bars = bar_store.merged_bars(PLAYBOOK_MARKET_SYMBOL, "5m")
+    # SPY's own baseline MBR normalizes `market_move` into MBR units (spec §0) -- resolved ONCE
+    # (it does not vary per member), not re-baselined inside every member's detector call.
+    index_baseline = baselines(
+        bar_store, PLAYBOOK_MARKET_SYMBOL, session_date,
+        PLAYBOOK_BASELINE_SESSIONS, PLAYBOOK_MIN_BASELINE_SESSIONS,
+    )
+
+    signals: list[dict] = []
+    absences: list[dict] = []
+    diagnostics: list[dict] = []
+
+    for symbol in members:
+        bars_5m = bar_store.merged_bars(symbol, "5m")
+        session_5m = rth_session_slice(bars_5m, session_date)
+        if not session_5m:
+            absences.append(
+                {"symbol": symbol, "reason": f"no 5m bars recorded for the {session_date} session"}
+            )
+            continue
+
+        baseline = baselines(
+            bar_store, symbol, session_date,
+            PLAYBOOK_BASELINE_SESSIONS, PLAYBOOK_MIN_BASELINE_SESSIONS,
+        )
+        if baseline["sessions"] < PLAYBOOK_MIN_BASELINE_SESSIONS or baseline["mbr"] == 0.0:
+            absences.append(
+                {
+                    "symbol": symbol,
+                    "reason": (
+                        f"fewer than {PLAYBOOK_MIN_BASELINE_SESSIONS} prior sessions on file or "
+                        f"MBR == 0 for {symbol} -- baseline too thin to detect against"
+                    ),
+                }
+            )
+            continue
+
+        bars_1m = bar_store.merged_bars(symbol, "1m")
+        or_result = opening_range(
+            bars_1m, bars_5m, session_date, PLAYBOOK_OR_MINUTES, PLAYBOOK_OR_MIN_1M_BARS
+        )
+        if or_result is None:
+            absences.append(
+                {
+                    "symbol": symbol,
+                    "reason": (
+                        "no opening range could be built -- neither 1m nor 5m bars cover the "
+                        "first 15 minutes of the session"
+                    ),
+                }
+            )
+            continue
+
+        signal, diagnostic = detect_opening_range_breaks(
+            session_5m, or_result, baseline, symbol, session_date, index_bars, index_baseline,
+            params, _prior_session_close(bars_5m, session_date),
+        )
+        if signal is not None:
+            signals.append(signal)
+        if diagnostic is not None:
+            diagnostics.append(diagnostic)
+
+    return {
+        "session_date": session_date,
+        "config_fingerprint": config_fingerprint,
+        "playbook_input_signature": signature,
+        "payload_version": 1,
+        "parameters": params,
+        "register": PLAYBOOK_REGISTER,
+        "signals": signals,
+        "absences": absences,
+        "diagnostics": diagnostics,
... [diff_bound] apps/backend/app/research/desk_playbook.py: 185 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/desk_playbook_detect.py b/apps/backend/app/research/desk_playbook_detect.py
new file mode 100644
index 0000000..f2e7535
--- /dev/null
+++ b/apps/backend/app/research/desk_playbook_detect.py
@@ -0,0 +1,320 @@
+"""The Playbook's detectors (Era B2, J-01: the opening-range-break family only --
+``docs/playbook-detector-spec.md`` §3.1-3.2). J-04/J-05/J-06 add the remaining seven detectors
+here, each built purely out of ``desk_playbook_features.py``'s eight primitives plus the
+``playbook_parameters()`` dict a caller hands in.
+
+**A THIRD "setup" vocabulary -- never conflate.** ``setups.py`` (the tick-touch scanner) and
+``backtests.py`` (tape-arming occurrences) already use "setup" for two OTHER things; a playbook
+signal is the book's own intraday pattern, a third, unrelated sense. This module never imports
+from ``setups.py`` or ``backtests.py``, and no field here is ever named ``stop_loss`` -- the field
+is ``invalidation_price``, a disclosed structural level, never an order concept.
+
+**Constant-free by design, same as the primitives.** This module imports NOTHING from
+``desk_playbook.py`` -- every threshold arrives as ``params`` (the caller's already-built
+``playbook_parameters()`` dict). This is what keeps the import graph acyclic
+(``desk_playbook.py`` -> this module -> ``desk_playbook_features.py`` -> ``desk_forward.py``,
+never the reverse) AND makes "the parameters blob matches what the detector actually used" true
+by construction: there is no second copy of a threshold anywhere for the two to drift apart on.
+
+**Lookahead law.** ``detect_opening_range_breaks`` reads ``session_bars`` strictly through the
+trigger bar for every GATING decision (the narrowness gate, the trigger crossing itself, the
+volume-into-trigger discriminator, ``attempt_count``, market context) -- the trigger bar's own
+close/volume/range are disclosures, never gates (spec §0). The one field that legitimately depends
+on bars AFTER the trigger is ``bars_to_close`` (how much of the session remained) -- a descriptive
+fact about the rest of the session, not a detection decision; the generic lookahead property test
+(``tests/test_desk_playbook_detect.py``) asserts core detection fields (trigger_price,
+invalidation_price, geometry) are truncation-invariant and the WHOLE signal is mutation-invariant
+for any bar strictly after the trigger."""
+
+from __future__ import annotations
+
+from datetime import datetime, timezone
+
+from ..providers.adapters.base import RawBar
+from .desk_playbook_features import market_context, rth_session_slice, vertical_move, zone_touches
+
+__all__ = ["detect_opening_range_breaks"]
+
+
+def _iso(epoch: float) -> str:
+    """The per-module tiny-helper convention (``desk_screen.py._iso``, ``desk_forward.py._iso``):
+    epoch -> ISO, so every served timestamp is formatted identically wherever it is read."""
+    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="microseconds").replace(
+        "+00:00", "Z"
+    )
+
+
+def _rvol(bar: RawBar, slot: int, slot_volume_medians: dict[int, float]) -> float | None:
+    """One bar's RVOL against its own baseline slot median -- spec §0's ONE relative-volume
+    definition; null (never a guess) when the slot has no median (too few baseline sessions)."""
+    median = slot_volume_medians.get(slot)
+    if not median:
+        return None
+    return bar.volume / median
+
+
+def _spike_into_trigger_verdict(
+    session_bars: list[RawBar],
+    approach_indices: list[int],
+    approach_rvols: list[float | None],
+    trigger_price: float,
+    side: str,
+    mbr: float,
+    rvol_surge: float,
+    near_extreme_mbr: float,
+) -> str:
+    """spec §0's volume-into-trigger discriminator, defined once and shared by every detector.
+    Disclosure only, never a gate."""
+    for idx, rvol in zip(approach_indices, approach_rvols):
+        if rvol is None or rvol < rvol_surge:
+            continue
+        bar = session_bars[idx]
+        if side == "long":
+            near_level = abs(bar.high - trigger_price) <= near_extreme_mbr * mbr
+            failed_to_close_beyond = bar.close <= trigger_price
+        else:
+            near_level = abs(bar.low - trigger_price) <= near_extreme_mbr * mbr
+            failed_to_close_beyond = bar.close >= trigger_price
+        if near_level and failed_to_close_beyond:
+            return "exhausted_spike"
+    known = [r for r in approach_rvols if r is not None]
+    if known and all(r < rvol_surge for r in known) and known == sorted(known):
+        return "constructive"
+    return "neutral"
+
+
+def _relative_strength_strong(
+    session_bars: list[RawBar],
+    trigger_idx: int,
+    mbr: float,
+    spy_prior_bars: list[RawBar],
+    side: str,
+    near_extreme_mbr: float,
+    index_mbr: float | None,
+) -> bool:
+    """spec §0: the stock's last pre-trigger close within ``near_extreme_mbr`` of its own
+    session-high-so-far while SPY's last close is within the same tolerance (index-MBR) of ITS
+    session-low-so-far -- mirrored for shorts. ``False`` (never a guess) when either MBR is
+    unavailable or SPY carries no prior bars."""
+    if mbr == 0.0 or not index_mbr or not spy_prior_bars:
+        return False
+    stock_close = session_bars[trigger_idx - 1].close
+    prior_stock_bars = session_bars[:trigger_idx]
+    stock_high = max(bar.high for bar in prior_stock_bars)
+    stock_low = min(bar.low for bar in prior_stock_bars)
+    spy_close = spy_prior_bars[-1].close
+    spy_high = max(bar.high for bar in spy_prior_bars)
+    spy_low = min(bar.low for bar in spy_prior_bars)
+    if side == "long":
+        return (
+            abs(stock_close - stock_high) <= near_extreme_mbr * mbr
+            and abs(spy_close - spy_low) <= near_extreme_mbr * index_mbr
+        )
+    return (
+        abs(stock_close - stock_low) <= near_extreme_mbr * mbr
+        and abs(spy_close - spy_high) <= near_extreme_mbr * index_mbr
+    )
+
+
+def _market_block(
+    session_bars: list[RawBar],
+    trigger_idx: int,
+    index_bars: list[RawBar],
+    session_date: str,
+    side: str,
+    mbr: float,
+    index_baseline: dict,
+    params: dict,
+) -> dict:
+    """spec §0's market-context disclosure block -- never a gate. Null ``direction``/
+    ``market_move_mbr`` (with an honest ``reason``) when SPY has no bars for the session, when
+    there are not yet ``mkt_lookback_bars`` prior SPY bars this early in the session, or when
+    SPY's own baseline MBR is unavailable to normalize the move."""
+    trigger_epoch = session_bars[trigger_idx].epoch
+    index_mbr = index_baseline.get("mbr") or None
+    mkt = market_context(index_bars, session_date, trigger_epoch, params["mkt_lookback_bars"])
+    spy_session_bars = rth_session_slice(index_bars, session_date)
+    spy_prior_bars = [bar for bar in spy_session_bars if bar.epoch < trigger_epoch]
+
+    if mkt is None:
+        reason = (
+            "no SPY bars recorded for the session"
+            if not spy_session_bars
+            else "fewer than the market lookback window's worth of SPY bars before the trigger"
+        )
+        return {
+            "direction": None, "market_move_mbr": None, "book_would_skip_market": False,
+            "relative_strength_strong": False, "source": "SPY", "reason": reason,
+        }
+    if index_mbr is None:
+        return {
+            "direction": None, "market_move_mbr": None, "book_would_skip_market": False,
+            "relative_strength_strong": _relative_strength_strong(
+                session_bars, trigger_idx, mbr, spy_prior_bars, side,
+                params["near_extreme_mbr"], index_mbr,
+            ),
+            "source": "SPY",
+            "reason": "SPY's own baseline MBR is unavailable -- cannot normalize the market move",
+        }
+
+    sign = 1.0 if side == "long" else -1.0
+    move_mbr = mkt["move"] / index_mbr
+    signed = sign * move_mbr
+    band = params["mkt_neutral_band_mbr"]
+    if signed > band:
+        direction = "supportive"
+    elif signed < -band:
+        direction = "against"
+    else:
+        direction = "neutral"
+    return {
+        "direction": direction,
+        "market_move_mbr": move_mbr,
+        "book_would_skip_market": direction == "against",
+        "relative_strength_strong": _relative_strength_strong(
+            session_bars, trigger_idx, mbr, spy_prior_bars, side, params["near_extreme_mbr"], index_mbr
+        ),
+        "source": "SPY",
+        "reason": None,
+    }
+
+
+def detect_opening_range_breaks(
+    session_bars: list[RawBar],
+    or_result: dict,
+    baseline: dict,
+    symbol: str,
+    session_date: str,
+    index_bars: list[RawBar],
+    index_baseline: dict,
+    params: dict,
+    prior_close: float | None,
+) -> tuple[dict | None, dict | None]:
+    """spec §3.1 (``open_high_break``) / §3.2 (``open_low_break``) -- one shared implementation
+    (the two are an exact mirror, sharing all formation/trigger/invalidation logic; only ONE of
+    the pair can ever fire per symbol-session, so a single walk deciding "which side, if either,
+    breaks first" is the natural -- and only sound -- shape). Returns ``(signal, diagnostic)``:
+    at most one is non-``None``. ``diagnostic`` is set only for the ``ambiguous_outside_bar`` case
+    (spec: a bar strictly breaking BOTH opening-range sides with neither previously broken).
+    A narrow-opening-range gate failure or a session that never breaks either side is a legitimate
+    "the setup did not form" outcome -- ``(None, None)``, never an absence (the caller's
+    ``absences`` list is reserved for DATA-quality gaps, not formation misses)."""
+    mbr = baseline["mbr"]
+    or_high, or_low = or_result["high"], or_result["low"]
+    if or_result["width"] > params["narrow_or_max_mbr"] * mbr:
+        return None, None
+
+    first_eligible_slot = params["or_minutes"] // 5
+    trigger_idx: int | None = None
+    side: str | None = None
+    for idx in range(first_eligible_slot, len(session_bars)):
+        bar = session_bars[idx]
+        breaks_high = bar.high > or_high
+        breaks_low = bar.low < or_low
+        if breaks_high and breaks_low:
+            return None, {
+                "symbol": symbol, "diagnostic": "ambiguous_outside_bar", "at_utc": _iso(bar.epoch),
+            }
+        if breaks_high:
+            trigger_idx, side = idx, "long"
+            break
+        if breaks_low:
+            trigger_idx, side = idx, "short"
+            break
+
+    if trigger_idx is None:
+        return None, None
+
+    trigger_bar = session_bars[trigger_idx]
+    trigger_price = or_high if side == "long" else or_low
+    or_width = or_high - or_low
+
+    if side == "long":
+        entry = max(trigger_bar.open, trigger_price)
+        entry_kind = "level" if trigger_bar.open < trigger_price else "gap_open"
+        gapped_beyond_chase = trigger_bar.open > trigger_price * (1.0 + params["max_chase_frac"])
+        invalidation_price = or_low - params["stop_pad_frac"] * or_width
+    else:
+        entry = min(trigger_bar.open, trigger_price)
+        entry_kind = "level" if trigger_bar.open > trigger_price else "gap_open"
+        gapped_beyond_chase = trigger_bar.open < trigger_price * (1.0 - params["max_chase_frac"])
+        invalidation_price = or_high + params["stop_pad_frac"] * or_width
+
+    approach_start = max(0, trigger_idx - params["approach_bars"])
+    approach_indices = list(range(approach_start, trigger_idx))
+    approach_rvols = [_rvol(session_bars[i], i, baseline["slot_volume_medians"]) for i in approach_indices]
+    known_rvols = [r for r in approach_rvols if r is not None]
+    approach_rvol_max = max(known_rvols) if known_rvols else None
+    rvol_trigger_bar = _rvol(trigger_bar, trigger_idx, baseline["slot_volume_medians"])
+
+    spike_verdict = _spike_into_trigger_verdict(
+        session_bars, approach_indices, approach_rvols, trigger_price, side, mbr,
+        params["rvol_surge"], params["near_extreme_mbr"],
+    )
+
+    spiky_approach = False
+    if trigger_idx - 1 >= 0:
+        spiky_approach = vertical_move(
+            session_bars, trigger_idx - 1, 1, params["vertical_bar_mbr"] * mbr,
+            "up" if side == "long" else "down",
+        )
+
+    if side == "long":
+        zone_lo, zone_hi = trigger_price - params["near_extreme_mbr"] * mbr, trigger_price
+    else:
+        zone_lo, zone_hi = trigger_price, trigger_price + params["near_extreme_mbr"] * mbr
+    attempt_count = len(zone_touches(session_bars[first_eligible_slot:trigger_idx], zone_lo, zone_hi))
+
+    market = _market_block(
+        session_bars, trigger_idx, index_bars, session_date, side, mbr, index_baseline, params
+    )
+
+    open_vs_prior_close_pct = (
+        (session_bars[0].open - prior_close) / prior_close * 100.0 if prior_close else None
+    )
+
+    principles = ["P4"] if spike_verdict == "constructive" else []
+
+    signal = {
+        "symbol": symbol,
+        "setup_id": "open_high_break" if side == "long" else "open_low_break",
+        "side": side,
+        "trigger_ts": _iso(trigger_bar.epoch),
+        "trigger_price": trigger_price,
+        "entry": entry,
+        "entry_kind": entry_kind,
+        "price_low": or_low,
+        "price_high": or_high,
+        "invalidation_price": invalidation_price,
+        "geometry": {
+            "or_high": or_high,
+            "or_low": or_low,
+            "or_width_mbr": or_result["width"] / mbr,
+            "or_bars_used": or_result["bars_used"],
+            "opening_range_basis": or_result["basis"],
+            "slots_to_break": trigger_idx,
+            "open_vs_prior_close_pct": open_vs_prior_close_pct,
+        },
+        "volume": {
+            "rvol_trigger_bar": rvol_trigger_bar,
+            "approach_rvol_max": approach_rvol_max,
+            "spike_into_trigger_verdict": spike_verdict,
+            "spiky_approach": spiky_approach,
+        },
+        "market": market,
+        "principles": principles,
+        "disclosures": {
+            "gapped_beyond_chase": gapped_beyond_chase,
+            "session_bar_count": len(session_bars),
+            "attempt_count": attempt_count,
+            "bars_to_close": len(session_bars) - 1 - trigger_idx,
+            # No other detector family exists yet this iteration (the OR-break pair is mutually
+            # exclusive with itself -- at most one signal per symbol-session) and no
+            # euphoria/capitulation marker detector exists yet either (J-05) -- both fields are
+            # wired for real cross-detector reads starting J-04/J-05; honestly empty until then.
+            "concurrent_signals": [],
+            "euphoria_recent": False,
+            "capitulation_recent": False,
+        },
+    }
+    return signal, None
diff --git a/apps/backend/app/research/desk_playbook_features.py b/apps/backend/app/research/desk_playbook_features.py
new file mode 100644
index 0000000..368e012
--- /dev/null
+++ b/apps/backend/app/research/desk_playbook_features.py
@@ -0,0 +1,296 @@
+"""The Playbook's shared primitives (Era B2, J-01) -- ``docs/playbook-detector-spec.md`` §2's eight
+functions, and NOTHING else in this module. Every detector (``desk_playbook_detect.py``, this
+iteration and every later one) is built entirely out of these eight calls; a detector that needs a
+ninth building block is a spec gap, not a reason to add one here quietly.
+
+**Constant-free by design.** This module takes every threshold as a PARAMETER (``PLAYBOOK_*``
+values live in ``desk_playbook.py``, the constants owner) -- so it never imports from
+``desk_playbook.py`` and the dependency graph has no cycle: ``desk_playbook.py`` and
+``desk_playbook_detect.py`` both import primitives FROM here, never the reverse.
+
+**RTH is derived properly, not by a fixed UTC offset.** ``09:30``/``16:00`` are ET WALL-CLOCK
+times; converting them to a UTC epoch for one session date must account for EST/EDT, so this module
+resolves them via ``zoneinfo.ZoneInfo("America/New_York")`` (stdlib, Python 3.12) rather than a
+hardcoded offset -- a fixture dated in June (EDT, UTC-4) and one dated in January (EST, UTC-5)
+resolve to the correct epoch either way (verified against ``test_desk_forward.py``'s own
+``E_OPEN = 1782135000.0`` == "2026-06-22T13:30:00Z" == 09:30 ET that day).
+
+**Session-window extraction is attributed, not re-derived.** ``rth_session_slice`` imports
+``desk_forward._session_slice`` for the day-narrowing step (the SAME bisect-based technique the
+measurement rail uses to avoid a full-history scan on a ~360k-row 1m series) and applies the RTH
+filter on top -- zero diff to ``desk_forward.py``, per T-8 ("the rail is imported, not forked").
+
+**Every bar-index IS the slot.** ``rth_session_slice``'s returned list is ascending and RTH-only,
+so a bar's position in that list already IS "index in the RTH 5m sequence" (spec §0's ``slot(bar)``)
+-- no separate slot field is attached to the (frozen, immutable) ``RawBar`` records themselves.
+"""
+
+from __future__ import annotations
+
+import statistics
+from bisect import bisect_left
+from datetime import date, datetime, time, timezone
+from operator import attrgetter
+from zoneinfo import ZoneInfo
+
+from ..providers.adapters.base import RawBar
+from .desk_forward import _session_slice
+
+__all__ = [
+    "rth_session_slice",
+    "opening_range",
+    "baselines",
+    "swing_pivots",
+    "consolidation_range",
+    "vertical_move",
+    "zone_touches",
+    "market_context",
+]
+
+# Regular trading hours, ET wall-clock -- a market-structure fact, not a tunable (the
+# ``desk_sessions.DESK_SESSION_ANCHOR_TIMEFRAME`` precedent: a plain structural constant, never a
+# ``Config`` field, never in the playbook's own tunable-constants table).
+_ET_ZONE = ZoneInfo("America/New_York")
+_RTH_START = time(9, 30)
+_RTH_END = time(16, 0)
+
+
+def _et_epoch(session_date: str, wall_time: time) -> float:
+    """The UTC epoch ``wall_time`` (ET) resolves to on ``session_date`` -- DST-correct by
+    construction (``zoneinfo`` resolves the UTC offset from the local wall-clock instant given,
+    never a fixed offset)."""
+    day = date.fromisoformat(session_date)
+    return datetime.combine(day, wall_time, tzinfo=_ET_ZONE).timestamp()
+
+
+def rth_session_slice(bars: list[RawBar], session_date: str) -> list[RawBar]:
+    """The session's own regular-trading-hours bars (ET 09:30 <= open < 16:00), ascending by
+    epoch -- a bar's INDEX in this list is its slot (0..77 on a full day; fewer on a half-day,
+    disclosed by callers as ``session_bar_count``).
+
+    Two steps: ``desk_forward._session_slice`` narrows to the UTC calendar date (imported, not
+    forked -- the SAME bisect technique that keeps a full-history read out of every call); the RTH
+    hour filter then narrows the (already tiny, ~1 day's worth) result further. Bars outside RTH on
+    the same UTC calendar date (pre/post-market, if ever recorded) are excluded -- the detection
+    series is RTH-only per spec §0."""
+    if not bars:
+        return []
+    window_date = date.fromisoformat(session_date)
+    rth_start = _et_epoch(session_date, _RTH_START)
+    rth_end = _et_epoch(session_date, _RTH_END)
+    # `_session_slice`'s as_of bound is inclusive; one second past RTH close is comfortably inside
+    # the UTC calendar day and still excludes nothing this module wants -- the RTH filter below is
+    # the actual right boundary (strict `< rth_end`).
+    day_bars = _session_slice(bars, window_date, rth_end + 1.0)
+    epoch_of = attrgetter("epoch")
+    start_idx = bisect_left(day_bars, rth_start, key=epoch_of)
+    return [bar for bar in day_bars[start_idx:] if bar.epoch < rth_end]
+
+
+def opening_range(
+    bars_1m: list[RawBar],
+    bars_5m: list[RawBar],
+    session_date: str,
+    or_minutes: int,
+    min_1m_bars: int,
+) -> dict | None:
+    """``{"high", "low", "width", "basis": "1m"|"5m", "bars_used"}`` over ET
+    ``09:30 .. 09:30+or_minutes``. At least ``min_1m_bars`` of the (up to) ``or_minutes`` one-minute
+    bars on file -> the 1m basis, built from whichever of those bars actually exist; fewer -> the
+    5m basis, the first ``or_minutes // 5`` five-minute bars (spec §2 primitive 2: "fall back to
+    the first 3 five-minute bars" -- derived from ``or_minutes``, not a second hardcoded ``3``);
+    neither on file -> ``None`` (fail-closed, disclosed by the caller as an absence).
+
+    BOTH bases read the SAME ``09:30 .. 09:30+or_minutes`` epoch window, never "whatever the
+    series happens to start with": a session whose early 5m bars are missing has no opening range
+    at all, and saying so is the whole point of the null. Taking ``session_5m[:3]`` positionally
+    would hand a session starting at 09:40 an "opening range" built from its 09:40/09:45/09:50
+    bars, disclosed as ``basis: "5m"`` exactly like a genuine one -- a fabricated value where the
+    honest answer is an absence (spec §0's fail-closed discipline; §3.1's "No 1m and no 5m OR =>
+    silent symbol-session (disclosed absence)")."""
+    window_end = _et_epoch(session_date, _RTH_START) + or_minutes * 60.0
+
+    session_1m = rth_session_slice(bars_1m, session_date)
+    one_min_window = [bar for bar in session_1m if bar.epoch < window_end]
+    if len(one_min_window) >= min_1m_bars:
+        highs = [bar.high for bar in one_min_window]
+        lows = [bar.low for bar in one_min_window]
+        high, low = max(highs), min(lows)
+        return {"high": high, "low": low, "width": high - low, "basis": "1m", "bars_used": len(one_min_window)}
+
+    five_min_bars_needed = or_minutes // 5
+    session_5m = rth_session_slice(bars_5m, session_date)
+    first_bars = [bar for bar in session_5m if bar.epoch < window_end][:five_min_bars_needed]
+    if len(first_bars) >= five_min_bars_needed:
+        highs = [bar.high for bar in first_bars]
+        lows = [bar.low for bar in first_bars]
+        high, low = max(highs), min(lows)
+        return {
+            "high": high, "low": low, "width": high - low, "basis": "5m",
+            "bars_used": len(first_bars),
+        }
+    return None
+
+
+def baselines(bar_store, symbol: str, session_date: str, baseline_sessions: int, min_baseline_sessions: int) -> dict:
+    """``{"mbr", "sessions", "slot_volume_medians"}`` over the ``baseline_sessions`` RTH 5m
+    sessions STRICTLY BEFORE ``session_date`` (entry-time legal by construction -- prior sessions
+    only). ``mbr`` = median(high - low) over every RTH 5m bar of those sessions (0.0 if none);
+    ``sessions`` = how many prior sessions were actually found (< ``min_baseline_sessions`` is the
+    caller's fail-closed signal, per spec §0); ``slot_volume_medians`` = ``{slot: median volume}``,
+    a slot present ONLY when at least ``min_baseline_sessions`` prior sessions recorded that slot
+    (spec §0's RVOL denominator rule -- fewer observations and RVOL at that slot is null, never a
+    thin median). The only baseline builder (spec §2 primitive 3): every RVOL and MBR in the
+    playbook reads through this."""
+    bars_5m = bar_store.merged_bars(symbol, "5m")
+    if not bars_5m:
+        return {"mbr": 0.0, "sessions": 0, "slot_volume_medians": {}}
+    all_dates = sorted({datetime.fromtimestamp(bar.epoch, tz=timezone.utc).date().isoformat() for bar in bars_5m})
+    prior_dates = [d for d in all_dates if d < session_date][-baseline_sessions:]
+
+    ranges: list[float] = []
+    slot_volumes: dict[int, list[int]] = {}
+    for prior_date in prior_dates:
+        for slot, bar in enumerate(rth_session_slice(bars_5m, prior_date)):
+            ranges.append(bar.high - bar.low)
+            slot_volumes.setdefault(slot, []).append(bar.volume)
+
+    slot_medians = {
+        slot: statistics.median(volumes)
+        for slot, volumes in slot_volumes.items()
+        if len(volumes) >= min_baseline_sessions
+    }
+    return {
+        "mbr": statistics.median(ranges) if ranges else 0.0,
+        "sessions": len(prior_dates),
+        "slot_volume_medians": slot_medians,
+    }
+
+
+def swing_pivots(bars: list[RawBar], lookback: int) -> list[dict]:
+    """Every STRICT +/-``lookback``-neighbour extreme in ``bars`` -- ``{"index", "kind": "high"|
+    "low", "price", "confirmed_at"}``, ``confirmed_at = index + lookback`` (the first index at
+    which the pivot is knowable without lookahead: once bars through ``confirmed_at`` are visible).
+    Mirrors ``levels._swing_pivots``' rule (``levels.py:325``) -- strictly greater/less than EVERY
+    neighbour on BOTH sides, a tie is never a pivot, a centre needs ``lookback`` bars visible on
+    each side to be checked at all -- but returns high/low SEPARATELY (``levels._swing_pivots``
+    folds both into one ``SWING_PIVOT`` level type, which loses the direction this primitive's
+    callers need: cup-and-handle needs swing HIGHS specifically, double-bottom needs swing LOWS).
+    A plain O(n * lookback) loop -- one session is at most ~78 bars, so the vectorized apparatus
+    ``levels.py`` needs for a multi-year history buys nothing here."""
+    pivots: list[dict] = []
+    n = len(bars)
+    for i in range(lookback, n - lookback):
+        left = bars[i - lookback : i]
+        right = bars[i + 1 : i + 1 + lookback]
+        high = bars[i].high
+        low = bars[i].low
+        if all(high > b.high for b in left) and all(high > b.high for b in right):
+            pivots.append({"index": i, "kind": "high", "price": high, "confirmed_at": i + lookback})
+        if all(low < b.low for b in left) and all(low < b.low for b in right):
+            pivots.append({"index": i, "kind": "low", "price": low, "confirmed_at": i + lookback})
+    return pivots
+
+
+def consolidation_range(
+    bars: list[RawBar], end_idx: int, min_bars: int, max_bars: int, max_range: float
+) -> tuple[int, float, float] | None:
+    """The MAXIMAL window ending at ``end_idx`` (length in ``[min_bars, max_bars]``) whose
+    ``max(high) - min(low) <= max_range`` -- ``(start_idx, U, L)``, or ``None`` if even the
+    shortest window fails. A wider window's range can only grow (never shrink), so checking lengths
+    from ``max_bars`` down finds the maximal qualifying window in one pass. Shared geometry for
+    JBE/DBI's base and cup-and-handle's handle (both J-04)."""
+    for length in range(max_bars, min_bars - 1, -1):
+        start_idx = end_idx - length + 1
+        if start_idx < 0:
+            continue
+        window = bars[start_idx : end_idx + 1]
+        u = max(bar.high for bar in window)
+        l = min(bar.low for bar in window)
+        if u - l <= max_range:
+            return start_idx, u, l
+    return None
+
+
+def vertical_move(
+    bars: list[RawBar],
+    end_idx: int,
+    n: int,
+    k: float,
+    direction: str,
+    *,
+    require_volume: bool = False,
+    rvol_surge: float | None = None,
+    rvols: list[float | None] | None = None,
+) -> bool:
+    """Did ``bars`` make a vertical move INTO ``end_idx``: net close-to-close move over the last
+    ``n`` bars >= ``k`` (an ALREADY MBR-scaled absolute threshold -- this primitive takes no MBR
+    itself, keeping it a plain bars-in utility) in ``direction`` ("up"/"down"), with at least
+    ``n - 1`` of the ``n`` closes themselves moving that way. ``require_volume`` (only capitulation/
+    euphoria, J-05, ever sets it) additionally needs the caller's own precomputed ``rvols`` (a list
+    parallel to ``bars``) to show the LAST bar's RVOL >= ``rvol_surge`` and >= the FIRST bar's RVOL
+    (rising) -- ``False`` whenever RVOL is unavailable (fail-closed, never a guess). Powers
+    capitulation/euphoria's climax leg (J-05) and, with ``n=1`` and no volume clause, the
+    spiky-approach flag (this iteration)."""
+    start_idx = end_idx - n + 1
+    if start_idx < 1 or end_idx >= len(bars) or start_idx > end_idx:
+        return False
+    sign = 1.0 if direction == "up" else -1.0
+    net_move = sign * (bars[end_idx].close - bars[start_idx - 1].close)
+    if net_move < k:
+        return False
+    closes_with = sum(
+        1 for i in range(start_idx, end_idx + 1) if sign * (bars[i].close - bars[i - 1].close) > 0
+    )
+    if closes_with < n - 1:
+        return False
+    if require_volume:
+        if rvols is None or rvol_surge is None:
+            return False
+        last_rvol, first_rvol = rvols[end_idx], rvols[start_idx]
+        if last_rvol is None or first_rvol is None:
+            return False
+        if last_rvol < rvol_surge or last_rvol < first_rvol:
+            return False
+    return True
+
+
+def zone_touches(bars: list[RawBar], lo: float, hi: float) -> list[int]:
+    """Indices of ``bars`` touching ``[lo, hi]`` -- overlap (``bar.low <= hi and bar.high >= lo``)
+    + full-exit re-arm semantics (attribution: ``desk_forward._touch_scan``, this module's own
+    tiny local mirror rather than an import -- ``zone_touches`` has no side/cap/beyond-cap
+    disclosure, the touch-scan concept narrowed to what the formation primitives need). Powers
+    attempt counts, tested-twice-and-held range arming, and second-top support touches."""
+    indices: list[int] = []
+    armed = True
+    for i, bar in enumerate(bars):
+        inside = bar.low <= hi and bar.high >= lo
+        if inside and armed:
+            indices.append(i)
+            armed = False
+        elif not inside:
+            armed = True
+    return indices
+
+
+def market_context(
+    index_bars: list[RawBar], session_date: str, before_epoch: float, lookback_bars: int
+) -> dict | None:
+    """The index's own mechanical facts as of strictly before ``before_epoch`` (the trigger bar's
+    own epoch, so the index's in-progress bar is never read): ``{"move": index close[t-1] - index
+    close[t-1-lookback_bars], "close_before": index close[t-1], "bars_available"}``. ``None`` when
+    fewer than ``lookback_bars + 1`` of the session's RTH index bars are on file before
+    ``before_epoch`` -- covers BOTH "no index bars for the session at all" (an empty ``index_bars``
+    list session-slices to ``[]``) and "too early in the session for the lookback window yet"
+    uniformly; the caller distinguishes the two for its own disclosure reason. Direction/alignment/
+    MBR-normalization are NOT computed here (this primitive has no MBR access by design) -- the
+    detector combines this with its own signal's side and the index's own ``baselines()`` MBR."""
+    session_bars = rth_session_slice(index_bars, session_date)
+    prior = [bar for bar in session_bars if bar.epoch < before_epoch]
+    if len(prior) < lookback_bars + 1:
+        return None
+    return {
+        "move": prior[-1].close - prior[-1 - lookback_bars].close,
+        "close_before": prior[-1].close,
+        "bars_available": len(prior),
+    }
diff --git a/apps/backend/tests/test_desk_playbook.py b/apps/backend/tests/test_desk_playbook.py
new file mode 100644
index 0000000..d70fff1
--- /dev/null
+++ b/apps/backend/tests/test_desk_playbook.py
@@ -0,0 +1,339 @@
+"""``desk_playbook.py`` -- constants/parameters/signature liveness, ``PlaybookStore`` append-only
+discipline, ``compute_playbook``'s session-refusal and per-symbol absence wiring, and
+``GET /research/desk/playbook`` (Era B2, J-01). Also the whole-package structural guards (TC-15:
+no ``setups``/``backtests`` import, no ``stop_loss`` field anywhere in a served signal) and the
+copy-discipline lint (TC-16) that close out this iteration's test-first contract.
+
+``test_desk_playbook_features.py`` covers the eight primitives in isolation and
+``test_desk_playbook_detect.py`` covers the detector as a pure function of hand-built bars/dicts;
+this file is the only one that plants real bars through a real ``BarStore`` and drives the full
+``compute_playbook`` walk end to end."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+from datetime import datetime
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app
+from app.providers.adapters.base import RawBar
+from app.research import desk_playbook as desk_playbook_module
+from app.research import desk_playbook_detect as desk_playbook_detect_module
+from app.research import desk_playbook_features as desk_playbook_features_module
+from app.research.bars import BarStore
+from app.research.desk_playbook import (
+    PLAYBOOK_REGISTER,
+    PlaybookAlreadyRecorded,
+    PlaybookIntegrityError,
+    PlaybookSessionRefused,
+    PlaybookStore,
+    compute_playbook,
+    compute_playbook_input_signature,
+    playbook_parameters,
+)
+from app.research.desk_sessions import non_session_refusal, session_evidence
+from app.research.desk_universe import UniverseStore
+from test_copy_discipline import find_violations
+
+SESSION_DATE = "2026-06-22"
+E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET
+_BASELINE_DATES = [f"2026-06-{d:02d}" for d in range(8, 18)]  # 10 prior dates < SESSION_DATE
+
+
+def _bar(symbol: str, timeframe: str, epoch: float, o: float, h: float, low: float, c: float, v: int = 1000) -> RawBar:
+    return RawBar(symbol, timeframe, epoch, o, h, low, c, v)
+
+
+def _plant(bar_store: BarStore, symbol: str, timeframe: str, bars: list[RawBar]) -> None:
+    bar_store.record(
+        symbol=symbol, timeframe=timeframe,
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
+        feed="test", bars=bars,
+    )
+
+
+def _plant_baseline_sessions(bar_store: BarStore, symbol: str, dates: list[str] = _BASELINE_DATES) -> None:
+    """10 prior RTH 5m sessions, 6 bars each, all identical (range 1.0, volume 1000) -> MBR=1.0,
+    a full slot-volume-median vector. All dates are in June (EDT, no DST transition), so plain
+    day arithmetic against E_OPEN resolves the SAME epoch a fresh ET conversion would."""
+    bars = []
+    for day in dates:
+        day_open = E_OPEN - (22 - int(day[-2:])) * 86_400.0
+        for slot in range(6):
+            bars.append(_bar(symbol, "5m", day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
+    _plant(bar_store, symbol, "5m", bars)
+
+
+def _plant_firing_session(bar_store: BarStore, symbol: str) -> None:
+    """The canonical open_high_break session (test_desk_playbook_detect.py's hand-computed
+    fixture, planted through a real BarStore this time): a narrow, 1m-basis opening range and a
+    slot-3 trigger that breaks only the high side."""
+    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
+    bars_5m = [
+        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, "5m", E_OPEN + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),
+        _bar(symbol, "5m", E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
+        _bar(symbol, "5m", E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
+    ]
+    _plant(bar_store, symbol, "1m", bars_1m)
+    _plant(bar_store, symbol, "5m", bars_5m)
+
+
+def _register_universe(tmp_path, members: list[str]) -> UniverseStore:
+    store = UniverseStore(tmp_path / "universe")
+    store.record(
+        members=members, raw_members={m: m for m in members},
+        source_url="test", min_members=1, max_members=10,
+    )
+    return store
+
+
+@pytest.fixture
+def bar_store(tmp_path) -> BarStore:
+    return BarStore(tmp_path / "bars")
+
+
+@pytest.fixture
+def universe_store(tmp_path) -> UniverseStore:
+    return _register_universe(tmp_path, ["AAA", "THIN"])
+
+
+def _sha256_file(path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+# --- compute_playbook: session refusal (TC-7) -----------------------------------------------------
+
+
+def test_compute_playbook_refuses_a_known_non_session_date(tmp_path, bar_store):
+    universe_store = _register_universe(tmp_path, ["AAA"])
+    # Daily bars bracket 06-21 without recording it -- a provable non-session gap.
+    for day in ("2026-06-19", "2026-06-20", "2026-06-22"):
+        epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
+        _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", epoch, 100.0, 101.0, 99.0, 100.0)])
+
+    with pytest.raises(PlaybookSessionRefused) as exc_info:
+        compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), "2026-06-21")
+
+    evidence = session_evidence(bar_store, ["AAA"])
+    assert str(exc_info.value) == non_session_refusal("2026-06-21", evidence)
+
+    store = PlaybookStore(tmp_path / "playbook")
+    assert store.list() == ([], [])  # nothing was ever written
+
+
+# --- compute_playbook: per-symbol absences (TC-8) and a real firing signal ------------------------
+
+
+def test_compute_playbook_records_a_thin_baseline_absence_beside_a_firing_signal(tmp_path, bar_store, universe_store):
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    _plant_baseline_sessions(bar_store, "THIN", _BASELINE_DATES[:3])  # only 3 -- below the floor
+    _plant_firing_session(bar_store, "THIN")  # has session bars, but the baseline gate fires first
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    assert [s["symbol"] for s in result["signals"]] == ["AAA"]
+    assert result["signals"][0]["setup_id"] == "open_high_break"
+    absence_symbols = {a["symbol"] for a in result["absences"]}
+    assert absence_symbols == {"THIN"}
+    assert "baseline too thin" in result["absences"][0]["reason"]
+    assert result["diagnostics"] == []
+    assert result["session_date"] == SESSION_DATE
+    assert result["parameters"] == playbook_parameters()
+    assert result["register"] == PLAYBOOK_REGISTER
+
+
+def test_compute_playbook_records_a_no_bars_absence(tmp_path, bar_store):
+    universe_store = _register_universe(tmp_path, ["NOBARS"])
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert result["signals"] == []
+    assert result["absences"] == [
+        {"symbol": "NOBARS", "reason": f"no 5m bars recorded for the {SESSION_DATE} session"}
+    ]
+
+
+# --- PlaybookStore: append-only discipline (TC-9, TC-11) --------------------------------------------
+
+
+def _record_aaa(tmp_path, bar_store, universe_store) -> tuple[PlaybookStore, dict]:
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    store = PlaybookStore(tmp_path / "playbook")
+    meta = store.record(**result)
+    return store, meta
+
+
+def test_duplicate_key_raises_and_leaves_the_recorded_file_byte_identical(tmp_path, bar_store, universe_store):
+    store, meta = _record_aaa(tmp_path, bar_store, universe_store)
+    path = store._path(meta["id"])
+    before = _sha256_file(path)
+
+    duplicate_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    with pytest.raises(PlaybookAlreadyRecorded) as exc_info:
+        store.record(**duplicate_result)
+    assert meta["id"] in str(exc_info.value)
+    assert _sha256_file(path) == before
+
+
+def test_playbook_store_has_no_update_or_delete_method():
+    assert not hasattr(PlaybookStore, "update")
+    assert not hasattr(PlaybookStore, "delete")
+
+
+def test_corrupt_file_checksum_is_surfaced_and_disk_is_untouched(tmp_path, bar_store, universe_store):
+    store, meta = _record_aaa(tmp_path, bar_store, universe_store)
+    path = store._path(meta["id"])
+    original_bytes = path.read_bytes()
+
+    tampered = json.loads(original_bytes)
+    tampered["record"]["meta"]["signals"] = []  # payload changed; file_checksum now stale
+    path.write_text(json.dumps(tampered))
+
+    with pytest.raises(PlaybookIntegrityError) as exc_info:
+        store._load(path)
+    assert path.name in str(exc_info.value)
+
+    # `list()` withholds the corrupted file into `errors` rather than raising through the walk.
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1 and errors[0]["file"] == path.name
+
+    # The tamper itself is the only mutation; the store never rewrote it on either read attempt.
+    assert path.read_bytes() == json.dumps(tampered).encode()
+
+
+# --- parameters / signature liveness (TC-10) ---------------------------------------------------------
+
+
+def test_monkeypatched_constant_moves_parameters_and_signature_and_mints_a_new_version(
+    tmp_path, bar_store, universe_store, monkeypatch
+):
+    store, first_meta = _record_aaa(tmp_path, bar_store, universe_store)
+    original_params = playbook_parameters()
+    original_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())
+
+    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_NARROW_OR_MAX_MBR", 999.0)
+
+    moved_params = playbook_parameters()
+    moved_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())
+    assert moved_params != original_params
+    assert moved_params["narrow_or_max_mbr"] == 999.0
+    assert moved_signature != original_signature
+
+    second_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert second_result["playbook_input_signature"] == moved_signature
+    second_meta = store.record(**second_result)  # does NOT raise -- a genuinely new key
+    assert second_meta["id"] != first_meta["id"]
+
+    newest, versions = store.newest_for_date(SESSION_DATE)
+    assert versions == 2
+    assert newest["id"] == second_meta["id"]
+    # The original file is untouched by the second, differently-keyed write.
+    assert store.get(first_meta["id"]) == first_meta
+
+
+def test_compute_playbook_input_signature_is_deterministic(bar_store):
+    _plant_baseline_sessions(bar_store, "AAA")
+    fp = CONFIG.config_fingerprint()
+    first = compute_playbook_input_signature(bar_store, ["AAA"], fp)
+    second = compute_playbook_input_signature(bar_store, ["AAA"], fp)
+    assert first == second
+    different_members = compute_playbook_input_signature(bar_store, ["AAA", "ZZZ"], fp)
+    assert different_members == first  # ZZZ has no recorded series -- contributes no tuples
+
+
+# --- GET /research/desk/playbook (TC-1, TC-12) -------------------------------------------------------
+
+
+@pytest.fixture
+def playbook_client(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
+    return TestClient(app), tmp_path
+
+
+def test_get_playbook_honest_empty(playbook_client):
+    client, _tmp_path = playbook_client
+    response = client.get("/research/desk/playbook")
+    assert response.status_code == 200
+    assert response.json() == {"playbooks": [], "latest": None, "integrity_errors": []}
+
+
+def test_get_playbook_date_and_id_are_verbatim_reads(tmp_path, bar_store, monkeypatch):
+    # A single-member universe (unlike the shared `universe_store` fixture's ["AAA", "THIN"]) so
+    # this route-focused test's `counts` assertion isn't coupled to another test's absence fixture.
+    solo_universe = _register_universe(tmp_path, ["AAA"])
+    _, meta = _record_aaa(tmp_path, bar_store, solo_universe)
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
+    client = TestClient(app)
+
+    by_date = client.get("/research/desk/playbook", params={"date": SESSION_DATE})
+    assert by_date.status_code == 200
+    body = by_date.json()
+    assert body["versions"] == 1
+    assert body["playbook"]["signals"] == meta["signals"]
+    assert body["playbook"]["id"] == meta["id"]
+
+    by_id = client.get("/research/desk/playbook", params={"id": meta["id"]})
+    assert by_id.status_code == 200
+    assert by_id.json() == {"playbook": meta}
+
+    unknown_date = client.get("/research/desk/playbook", params={"date": "2099-01-01"})
+    assert unknown_date.json() == {"playbook": None, "versions": 0}
+
+    unknown_id = client.get("/research/desk/playbook", params={"id": "playbook-nope"})
+    assert unknown_id.json() == {"playbook": None}
+
+    both = client.get("/research/desk/playbook", params={"date": SESSION_DATE, "id": meta["id"]})
+    assert both.status_code == 422
+
+    bulk = client.get("/research/desk/playbook")
+    assert bulk.status_code == 200
+    bulk_body = bulk.json()
+    assert bulk_body["latest"] == meta
+    assert len(bulk_body["playbooks"]) == 1
+    assert bulk_body["playbooks"][0]["id"] == meta["id"]
+    assert bulk_body["playbooks"][0]["counts"] == {"signals": 1, "absences": 0, "diagnostics": 0}
+    assert "signals" not in bulk_body["playbooks"][0]  # meta-only -- the bulk field is never served
+
+
+# --- structural guards (TC-15) and copy discipline (TC-16) -------------------------------------------
+
+
+def test_neither_playbook_module_imports_setups_or_backtests():
+    for module in (
+        desk_playbook_module, desk_playbook_detect_module, desk_playbook_features_module,
+    ):
+        source = open(module.__file__, encoding="utf-8").read()
+        assert "import setups" not in source and "from .setups" not in source
+        assert "import backtests" not in source and "from .backtests" not in source
+
+
+def test_no_served_signal_field_is_ever_named_stop_loss(bar_store, universe_store):
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+
+    def _flatten_keys(obj):
+        if isinstance(obj, dict):
+            for key, value in obj.items():
+                yield key
+                yield from _flatten_keys(value)
+        elif isinstance(obj, list):
+            for item in obj:
+                yield from _flatten_keys(item)
+
+    keys = set(_flatten_keys(result))
+    assert "stop_loss" not in keys
+    assert "invalidation_price" in keys
+
+
+def test_playbook_register_passes_copy_discipline():
+    assert find_violations(PLAYBOOK_REGISTER) == []
diff --git a/apps/backend/tests/test_desk_playbook_detect.py b/apps/backend/tests/test_desk_playbook_detect.py
new file mode 100644
index 0000000..9a6b404
--- /dev/null
+++ b/apps/backend/tests/test_desk_playbook_detect.py
@@ -0,0 +1,283 @@
+"""``desk_playbook_detect.py`` -- the opening-range-break detector pair (Era B2, J-01,
+``docs/playbook-detector-spec.md`` §3.1-3.2): fixture goldens for the canonical firing case (TC-2),
+the wide-OR near-miss (TC-3), the 1m->5m opening-range degrade on a firing signal (TC-4), the
+both-sides ambiguous outside bar (TC-5), and the generic lookahead property test (TC-6) -- built
+so J-04/J-05/J-06 extend ``_LOOKAHEAD_FIXTURES`` with their own detectors' fixtures without
+touching the property test's own body.
+
+``detect_opening_range_breaks`` is tested directly as a pure function of bars + a hand-built
+``or_result``/``baseline`` dict -- ``desk_playbook_features.py``'s primitives that would normally
+produce those dicts are already covered by ``test_desk_playbook_features.py``; this file is
+detector logic only. ``test_desk_playbook.py`` separately proves the full bar-store-backed walk
+(``compute_playbook``) wires the primitives into the detector correctly."""
+
+from __future__ import annotations
+
+from datetime import datetime, timezone
+
+import pytest
+
+from app.providers.adapters.base import RawBar
+from app.research.desk_playbook import playbook_parameters
+from app.research.desk_playbook_detect import detect_opening_range_breaks
+
+SESSION_DATE = "2026-06-22"
+E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET
+
+
+def _iso(epoch: float) -> str:
+    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="microseconds").replace(
+        "+00:00", "Z"
+    )
+
+
+def _bar(symbol: str, epoch: float, o: float, h: float, low: float, c: float, v: int = 1000) -> RawBar:
+    return RawBar(symbol, "5m", epoch, o, h, low, c, v)
+
+
+_EMPTY_INDEX_BASELINE = {"mbr": 0.0, "sessions": 0, "slot_volume_medians": {}}
+_NO_SPY_MARKET = {
+    "direction": None, "market_move_mbr": None, "book_would_skip_market": False,
+    "relative_strength_strong": False, "source": "SPY", "reason": "no SPY bars recorded for the session",
+}
+
+
+def _canonical_session_bars(symbol: str) -> list[RawBar]:
+    """Slots 0-2: unremarkable pre-trigger bars (flat close, RVOL 0.5 vs the 1000-median baseline
+    below -- deliberately non-decreasing and never surging, so the volume-into-trigger verdict is
+    "constructive"). Slot 3: the trigger -- opens on the near side of or_high=101.0 ("level" entry,
+    no chase gap), breaks only the high side. Slots 4-5: session tail (bars_to_close)."""
+    return [
+        _bar(symbol, E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar(symbol, E_OPEN + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),  # trigger: breaks 101.0 high
+        _bar(symbol, E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
+        _bar(symbol, E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
+    ]
+
+
+_CANONICAL_OR = {"high": 101.0, "low": 100.0, "width": 1.0, "basis": "1m", "bars_used": 15}
+_CANONICAL_BASELINE = {
+    "mbr": 1.0, "sessions": 10,
+    "slot_volume_medians": {0: 1000, 1: 1000, 2: 1000, 3: 1000, 4: 1000, 5: 1000},
+}
+_PARAMS = playbook_parameters()
+
+
+def _detect_canonical(symbol: str = "OHB1", *, session_bars=None):
+    bars = session_bars if session_bars is not None else _canonical_session_bars(symbol)
+    return detect_opening_range_breaks(
+        bars, _CANONICAL_OR, _CANONICAL_BASELINE, symbol, SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS, 100.0,
+    )
+
+
+# --- TC-2: the canonical firing fixture, every field hand-computed -------------------------------
+
+
+def test_canonical_open_high_break_matches_the_hand_computed_signal():
+    signal, diagnostic = _detect_canonical()
+    assert diagnostic is None
+    assert signal == {
+        "symbol": "OHB1",
+        "setup_id": "open_high_break",
+        "side": "long",
+        "trigger_ts": _iso(E_OPEN + 900.0),
+        "trigger_price": 101.0,
+        "entry": 101.0,
+        "entry_kind": "level",
+        "price_low": 100.0,
+        "price_high": 101.0,
+        "invalidation_price": pytest.approx(99.7),
+        "geometry": {
+            "or_high": 101.0,
+            "or_low": 100.0,
+            "or_width_mbr": pytest.approx(1.0),
+            "or_bars_used": 15,
+            "opening_range_basis": "1m",
+            "slots_to_break": 3,
+            "open_vs_prior_close_pct": pytest.approx(0.5),
+        },
+        "volume": {
+            "rvol_trigger_bar": pytest.approx(1.0),
+            "approach_rvol_max": pytest.approx(0.5),
+            "spike_into_trigger_verdict": "constructive",
+            "spiky_approach": False,
+        },
+        "market": _NO_SPY_MARKET,
+        "principles": ["P4"],
+        "disclosures": {
+            "gapped_beyond_chase": False,
+            "session_bar_count": 6,
+            "attempt_count": 0,
+            "bars_to_close": 2,
+            "concurrent_signals": [],
+            "euphoria_recent": False,
+            "capitulation_recent": False,
+        },
+    }
+
+
+def test_open_low_break_mirrors_the_high_side():
+    """The mirror side: a session whose 5m bars only ever break DOWN through or_low, entry/
+    invalidation/side all mirrored per spec §0."""
+    bars = [
+        _bar("OLB1", E_OPEN, 100.5, 100.9, 100.1, 100.4, 500),
+        _bar("OLB1", E_OPEN + 300.0, 100.4, 100.9, 100.1, 100.4, 500),
+        _bar("OLB1", E_OPEN + 600.0, 100.4, 100.9, 100.1, 100.4, 500),
+        _bar("OLB1", E_OPEN + 900.0, 100.2, 100.3, 99.5, 99.8, 1000),  # trigger: breaks 100.0 low
+        _bar("OLB1", E_OPEN + 1200.0, 99.8, 99.9, 99.6, 99.7, 800),
+    ]
+    signal, diagnostic = detect_opening_range_breaks(
+        bars, _CANONICAL_OR, _CANONICAL_BASELINE, "OLB1", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
+    )
+    assert diagnostic is None
+    assert signal["setup_id"] == "open_low_break"
+    assert signal["side"] == "short"
+    assert signal["trigger_price"] == 100.0
+    # open=100.2 is still ABOVE T=100.0 -- the near (not-yet-crossed) side for a short breaking
+    # DOWN through the level -- so the modeled fill is at the level itself, not the open.
+    assert signal["entry"] == 100.0
+    assert signal["entry_kind"] == "level"
+    assert signal["invalidation_price"] == pytest.approx(101.3)  # or_high + 0.30*(or_high-or_low)
+    assert signal["geometry"]["open_vs_prior_close_pct"] is None  # prior_close=None -> honest null
+
+
+# --- TC-3: the wide-OR near-miss -- zero signals regardless of what the bars do afterward --------
+
+
+def test_wide_opening_range_fires_no_signal():
+    wide_or = {"high": 105.0, "low": 100.0, "width": 5.0, "basis": "1m", "bars_used": 15}
+    bars = [
+        _bar("WIDE", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar("WIDE", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar("WIDE", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar("WIDE", E_OPEN + 900.0, 100.8, 106.0, 100.7, 105.5, 1000),  # would break 105 if checked
+    ]
+    signal, diagnostic = detect_opening_range_breaks(
+        bars, wide_or, _CANONICAL_BASELINE, "WIDE", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
+    )
+    assert signal is None
+    assert diagnostic is None
+
+
+# --- TC-4: the 5m-basis opening range on an otherwise-firing signal --------------------------------
+
+
+def test_5m_basis_opening_range_still_fires_with_the_basis_disclosed():
+    five_min_or = {"high": 101.0, "low": 100.0, "width": 1.0, "basis": "5m", "bars_used": 3}
+    signal, diagnostic = detect_opening_range_breaks(
+        _canonical_session_bars("OR5M"), five_min_or, _CANONICAL_BASELINE, "OR5M", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
+    )
+    assert diagnostic is None
+    assert signal["geometry"]["opening_range_basis"] == "5m"
+    assert signal["geometry"]["or_bars_used"] == 3
+    assert signal["trigger_price"] == 101.0  # geometry unaffected by the basis itself
+
+
+# --- TC-5: a bar strictly breaking both OR sides, neither previously broken -----------------------
+
+
+def test_ambiguous_outside_bar_fires_no_signal_and_records_a_diagnostic():
+    bars = [
+        _bar("AMBIG", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar("AMBIG", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar("AMBIG", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar("AMBIG", E_OPEN + 900.0, 100.5, 102.0, 99.0, 100.5, 1000),  # breaks BOTH 101 and 100
+    ]
+    signal, diagnostic = detect_opening_range_breaks(
+        bars, _CANONICAL_OR, _CANONICAL_BASELINE, "AMBIG", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
+    )
+    assert signal is None
+    assert diagnostic == {
+        "symbol": "AMBIG", "diagnostic": "ambiguous_outside_bar", "at_utc": _iso(E_OPEN + 900.0),
+    }
+
+
+def test_a_session_that_never_breaks_either_side_fires_nothing():
+    bars = [
+        _bar("QUIET", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
+        _bar("QUIET", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar("QUIET", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
+        _bar("QUIET", E_OPEN + 900.0, 100.6, 100.9, 100.2, 100.5, 500),  # stays inside [100, 101]
+    ]
+    signal, diagnostic = detect_opening_range_breaks(
+        bars, _CANONICAL_OR, _CANONICAL_BASELINE, "QUIET", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
+    )
+    assert signal is None
+    assert diagnostic is None
+
+
+# --- TC-6: the generic lookahead property test -----------------------------------------------------
+#
+# Registered fixtures, each ``(session_bars, or_result, baseline, symbol, index_bars,
+# index_baseline, prior_close, trigger_idx)`` -- J-04/J-05/J-06 extend this list with their OWN
+# detector's canonical-firing fixtures (and their own detect_* call, parametrized alongside) WITHOUT
+# touching the two assertion bodies below.
+
+_LOOKAHEAD_FIXTURES = [
+    (
+        _canonical_session_bars("LOOK1"), _CANONICAL_OR, _CANONICAL_BASELINE, "LOOK1",
+        [], _EMPTY_INDEX_BASELINE, 100.0, 3,
+    ),
+]
+
+
+@pytest.mark.parametrize("bars, or_result, baseline, symbol, index_bars, index_baseline, prior_close, trigger_idx", _LOOKAHEAD_FIXTURES)
+def test_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields(
+    bars, or_result, baseline, symbol, index_bars, index_baseline, prior_close, trigger_idx
+):
+    """``detect(bars[:trigger_index+1])`` must reproduce the SAME trigger_price, invalidation_price
+    and geometry as the full-session call -- these are the fields a genuinely lookahead-clean
+    detection can never depend on bars after the trigger for. (``bars_to_close`` legitimately
+    differs under truncation -- it describes how much of the session remains, not a detection
+    decision -- so it is deliberately excluded from this comparison; the MUTATION variant below
+    proves the whole signal, including disclosures, is unaffected when nothing about the session's
+    LENGTH changes.)"""
+    full_signal, _ = detect_opening_range_breaks(
+        bars, or_result, baseline, symbol, SESSION_DATE, index_bars, index_baseline,
+        _PARAMS, prior_close,
+    )
+    assert full_signal is not None
+
+    truncated_signal, _ = detect_opening_range_breaks(
+        bars[: trigger_idx + 1], or_result, baseline, symbol, SESSION_DATE, index_bars,
+        index_baseline, _PARAMS, prior_close,
+    )
+    assert truncated_signal is not None
+    assert truncated_signal["trigger_price"] == full_signal["trigger_price"]
+    assert truncated_signal["invalidation_price"] == full_signal["invalidation_price"]
+    assert truncated_signal["geometry"] == full_signal["geometry"]
+
+
+@pytest.mark.parametrize("bars, or_result, baseline, symbol, index_bars, index_baseline, prior_close, trigger_idx", _LOOKAHEAD_FIXTURES)
+def test_mutating_a_bar_after_the_trigger_changes_nothing(
+    bars, or_result, baseline, symbol, index_bars, index_baseline, prior_close, trigger_idx
+):
+    """Mutating any bar strictly AFTER the trigger index (same session length, different values)
+    must leave the detected signal byte-identical -- proving no disclosure secretly reads ahead."""
+    original_signal, _ = detect_opening_range_breaks(
+        bars, or_result, baseline, symbol, SESSION_DATE, index_bars, index_baseline,
+        _PARAMS, prior_close,
+    )
+    assert original_signal is not None
+    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"
+
+    mutated = list(bars)
+    victim = mutated[trigger_idx + 1]
+    mutated[trigger_idx + 1] = RawBar(
+        victim.symbol, victim.timeframe, victim.epoch,
+        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
+    )
+    mutated_signal, mutated_diagnostic = detect_opening_range_breaks(
+        mutated, or_result, baseline, symbol, SESSION_DATE, index_bars, index_baseline,
+        _PARAMS, prior_close,
+    )
+    assert mutated_diagnostic is None
+    assert mutated_signal == original_signal
diff --git a/apps/backend/tests/test_desk_playbook_features.py b/apps/backend/tests/test_desk_playbook_features.py
new file mode 100644
index 0000000..c55b41a
--- /dev/null
+++ b/apps/backend/tests/test_desk_playbook_features.py
@@ -0,0 +1,307 @@
+"""``desk_playbook_features.py`` -- the Playbook's eight shared primitives (Era B2, J-01).
+
+Coverage: RTH session slicing excludes pre/post-market bars on the same UTC date; opening_range's
+1m basis, its 1m->5m honest degrade, and its null (neither basis) case; baselines' MBR/sessions/
+slot-volume-median math, its thin-baseline case, and its zero-bars case; swing_pivots' parity with
+``levels._swing_pivots``' strict-extreme rule (including the tie-is-not-a-pivot case); the maximal
+qualifying consolidation_range window and its "nothing qualifies" case; vertical_move's move/close
+gates and its require_volume clause; zone_touches' full-exit re-arm rule; market_context's
+no-SPY-bars null case, its insufficient-lookback null case, and its computed-move case."""
+
+from __future__ import annotations
+
+import pytest
+
+from app.providers.adapters.base import RawBar
+from app.research.bars import BarStore
+from app.research.desk_playbook_features import (
+    baselines,
+    consolidation_range,
+    market_context,
+    opening_range,
+    rth_session_slice,
+    swing_pivots,
+    vertical_move,
+    zone_touches,
+)
+from app.research.levels import _swing_pivots as _levels_swing_pivots
+
+# 2026-06-22T13:30:00Z == 09:30 ET that day (EDT, UTC-4) -- verified against
+# test_desk_forward.py's own E_OPEN constant.
+SESSION_DATE = "2026-06-22"
+E_OPEN = 1782135000.0
+_RTH_SECONDS = 6.5 * 3600.0  # 09:30 -> 16:00 ET
+
+
+def _bar(symbol: str, timeframe: str, epoch: float, o: float, h: float, low: float, c: float, v: int = 1000) -> RawBar:
+    return RawBar(symbol, timeframe, epoch, o, h, low, c, v)
+
+
+def _plant(bar_store: BarStore, symbol: str, timeframe: str, bars: list[RawBar]) -> None:
+    bar_store.record(
+        symbol=symbol, timeframe=timeframe,
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
+        feed="test", bars=bars,
+    )
+
+
+@pytest.fixture
+def bar_store(tmp_path):
+    return BarStore(tmp_path / "bars")
+
+
+# --- rth_session_slice ---------------------------------------------------------------------------
+
+
+def test_rth_session_slice_excludes_pre_and_post_market_bars(bar_store):
+    bars = [
+        _bar("RTHX", "5m", E_OPEN - 1800.0, 99.0, 99.2, 98.8, 99.0),  # 09:00 ET -- pre-market
+        _bar("RTHX", "5m", E_OPEN, 100.0, 101.0, 99.0, 100.5),  # 09:30 ET -- slot 0
+        _bar("RTHX", "5m", E_OPEN + 300.0, 100.5, 101.5, 100.0, 101.0),  # 09:35 ET -- slot 1
+        _bar("RTHX", "5m", E_OPEN + _RTH_SECONDS + 300.0, 101.0, 101.5, 100.5, 101.2),  # 16:05 ET
+    ]
+    _plant(bar_store, "RTHX", "5m", bars)
+    result = rth_session_slice(bar_store.merged_bars("RTHX", "5m"), SESSION_DATE)
+    assert [b.epoch for b in result] == [E_OPEN, E_OPEN + 300.0]
+
+
+def test_rth_session_slice_on_a_winter_est_date_still_resolves_0930_correctly(bar_store):
+    """DST correctness: January is EST (UTC-5), not the June fixtures' EDT (UTC-4) -- 09:30 ET on
+    2026-01-15 is 14:30Z, not 13:30Z. A fixed-offset bug would silently include/exclude an hour."""
+    winter_open = 1768487400.0  # 2026-01-15T14:30:00Z == 09:30 ET (EST)
+    bars = [
+        _bar("WNTR", "5m", winter_open - 300.0, 50.0, 50.2, 49.8, 50.0),  # 09:25 ET -- pre-market
+        _bar("WNTR", "5m", winter_open, 50.0, 50.5, 49.5, 50.2),  # 09:30 ET -- slot 0
+    ]
+    _plant(bar_store, "WNTR", "5m", bars)
+    result = rth_session_slice(bar_store.merged_bars("WNTR", "5m"), "2026-01-15")
+    assert [b.epoch for b in result] == [winter_open]
+
+
+def test_rth_session_slice_empty_series_is_empty(bar_store):
+    assert rth_session_slice([], SESSION_DATE) == []
+
+
+# --- opening_range ---------------------------------------------------------------------------------
+
+
+def test_opening_range_1m_basis_uses_all_available_1m_bars_in_the_window(bar_store):
+    bars_1m = [
+        _bar("OR1M", "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5) for i in range(12)
+    ]
+    _plant(bar_store, "OR1M", "1m", bars_1m)
+    result = opening_range(bar_store.merged_bars("OR1M", "1m"), [], SESSION_DATE, 15, 10)
+    assert result == {"high": 101.0, "low": 100.0, "width": 1.0, "basis": "1m", "bars_used": 12}
+
+
+def test_opening_range_degrades_to_5m_basis_below_the_1m_floor(bar_store):
+    bars_1m = [_bar("OR5M", "1m", E_OPEN + i * 60.0, 100.5, 100.6, 100.4, 100.5) for i in range(4)]
+    bars_5m = [
+        _bar("OR5M", "5m", E_OPEN, 100.0, 100.8, 99.8, 100.2),
+        _bar("OR5M", "5m", E_OPEN + 300.0, 100.2, 101.0, 100.0, 100.9),
+        _bar("OR5M", "5m", E_OPEN + 600.0, 100.9, 100.9, 99.9, 100.4),
+    ]
+    _plant(bar_store, "OR5M", "1m", bars_1m)
+    _plant(bar_store, "OR5M", "5m", bars_5m)
+    result = opening_range(
+        bar_store.merged_bars("OR5M", "1m"), bar_store.merged_bars("OR5M", "5m"),
+        SESSION_DATE, 15, 10,
+    )
+    assert result["high"] == pytest.approx(101.0)
+    assert result["low"] == pytest.approx(99.8)
+    assert result["width"] == pytest.approx(1.2)
+    assert result["basis"] == "5m"
+    assert result["bars_used"] == 3
+
+
+def test_opening_range_5m_fallback_never_builds_from_bars_outside_the_opening_window(bar_store):
+    """A session whose 5m series is MISSING its 09:30 and 09:35 bars has no opening range -- the
+    honest answer is the null (the caller's disclosed absence), never an "opening range" quietly
+    built from the 09:40/09:45/09:50 bars and served as ``basis: "5m"`` like a genuine one.
+    Positional ``session_5m[:3]`` slicing did exactly that; both bases read the same
+    ``09:30 .. 09:45`` epoch window."""
+    bars_5m = [
+        _bar("ORGAP", "5m", E_OPEN + 600.0, 100.0, 100.4, 99.8, 100.2),  # 09:40 -- inside window
+        _bar("ORGAP", "5m", E_OPEN + 900.0, 100.2, 100.6, 100.0, 100.5),  # 09:45 -- OUTSIDE
+        _bar("ORGAP", "5m", E_OPEN + 1200.0, 100.5, 100.9, 100.3, 100.8),  # 09:50 -- OUTSIDE
+        _bar("ORGAP", "5m", E_OPEN + 1500.0, 100.8, 101.2, 100.6, 101.0),
+    ]
+    _plant(bar_store, "ORGAP", "5m", bars_5m)
+    assert opening_range([], bar_store.merged_bars("ORGAP", "5m"), SESSION_DATE, 15, 10) is None
+
+
+def test_opening_range_null_when_neither_basis_is_available(bar_store):
+    bars_1m = [_bar("ORNULL", "1m", E_OPEN + i * 60.0, 100.5, 100.6, 100.4, 100.5) for i in range(4)]
+    bars_5m = [_bar("ORNULL", "5m", E_OPEN, 100.0, 100.8, 99.8, 100.2)]  # only 1 -- need >= 3
+    _plant(bar_store, "ORNULL", "1m", bars_1m)
+    _plant(bar_store, "ORNULL", "5m", bars_5m)
+    result = opening_range(
+        bar_store.merged_bars("ORNULL", "1m"), bar_store.merged_bars("ORNULL", "5m"),
+        SESSION_DATE, 15, 10,
+    )
+    assert result is None
+
+
+# --- baselines -------------------------------------------------------------------------------------
+
+_PRIOR_DATES_12 = [f"2026-06-{d:02d}" for d in range(1, 13)]  # 12 dates, all < 2026-06-22
+
+
+def _plant_prior_sessions(bar_store, symbol, dates, *, flat=False, volume=1000):
+    bars = []
+    for day_offset, day in enumerate(dates):
+        day_open = E_OPEN - (22 - int(day[-2:])) * 86_400.0
+        for slot in range(4):
+            if flat:
+                o = h = low = c = 100.0
+            else:
+                o, h, low, c = 100.0, 100.5, 99.5, 100.0
+            bars.append(_bar(symbol, "5m", day_open + slot * 300.0, o, h, low, c, volume))
+    _plant(bar_store, symbol, "5m", bars)
+
+
+def test_baselines_computes_mbr_and_slot_volume_medians_over_prior_sessions(bar_store):
+    _plant_prior_sessions(bar_store, "BASE", _PRIOR_DATES_12)
+    result = baselines(bar_store, "BASE", SESSION_DATE, 20, 10)
+    assert result["sessions"] == 12
+    assert result["mbr"] == pytest.approx(1.0)
+    assert result["slot_volume_medians"] == {0: 1000, 1: 1000, 2: 1000, 3: 1000}
+
+
+def test_baselines_reports_a_thin_session_count_below_the_minimum(bar_store):
+    _plant_prior_sessions(bar_store, "THIN", _PRIOR_DATES_12[:3])  # only 3 prior sessions
+    result = baselines(bar_store, "THIN", SESSION_DATE, 20, 10)
+    assert result["sessions"] == 3
+    assert result["mbr"] == pytest.approx(1.0)  # still computable -- the CALLER applies the floor
+
+
+def test_baselines_reports_mbr_zero_for_flat_bars(bar_store):
+    _plant_prior_sessions(bar_store, "FLAT", _PRIOR_DATES_12, flat=True)
+    result = baselines(bar_store, "FLAT", SESSION_DATE, 20, 10)
+    assert result["sessions"] == 12
+    assert result["mbr"] == 0.0
+
+
+def test_baselines_with_no_bars_at_all_is_an_honest_zero(bar_store):
+    result = baselines(bar_store, "NOBARS", SESSION_DATE, 20, 10)
+    assert result == {"mbr": 0.0, "sessions": 0, "slot_volume_medians": {}}
+
+
+# --- swing_pivots ------------------------------------------------------------------------------------
+
+
+def test_swing_pivots_matches_levels_swing_pivots_strict_extreme_rule():
+    # highs: pivots at index 2 (105) and index 8 (106); lows: one pivot at index 5 (80); every
+    # near-miss (a tie, or falling short on one side) is deliberately included to prove both
+    # modules agree on the STRICT rule, not just the easy cases.
+    highs = [100, 101, 105, 101, 100, 99, 100, 101, 106, 101, 100]
+    lows = [90, 89, 88, 87, 86, 80, 86, 87, 88, 89, 90]
+    bars = [
+        _bar("PIVOT", "5m", E_OPEN + i * 300.0, (highs[i] + lows[i]) / 2, highs[i], lows[i], (highs[i] + lows[i]) / 2)
+        for i in range(len(highs))
+    ]
+    mine = swing_pivots(bars, lookback=2)
+    reference = _levels_swing_pivots(bars, "5m", 2, 0.0, 1.0)
+
+    mine_prices = sorted(p["price"] for p in mine)
+    reference_prices = sorted(level["price"] for level in reference)
+    assert mine_prices == reference_prices == [80.0, 105.0, 106.0]
+
+    by_price = {p["price"]: p for p in mine}
+    assert by_price[105.0]["kind"] == "high"
+    assert by_price[105.0]["index"] == 2
+    assert by_price[105.0]["confirmed_at"] == 4  # index + lookback
+    assert by_price[106.0]["kind"] == "high"
+    assert by_price[80.0]["kind"] == "low"
+    assert by_price[80.0]["index"] == 5
+
+
+def test_swing_pivots_too_short_a_series_yields_nothing():
+    bars = [_bar("SHORT", "5m", E_OPEN + i * 300.0, 100, 101, 99, 100) for i in range(3)]
+    assert swing_pivots(bars, lookback=2) == []  # needs 2*lookback+1 == 5 bars minimum
+
+
+# --- consolidation_range ------------------------------------------------------------------------------
+
+
+_CONSOL_BARS = [
+    _bar("CONS", "5m", E_OPEN + i * 300.0, o, h, low, c)
+    for i, (o, h, low, c) in enumerate(
+        [(100.0, 100.5, 99.5, 100.2), (100.2, 100.6, 99.6, 100.3), (100.3, 100.4, 99.7, 100.1), (100.1, 100.7, 99.5, 100.4)]
+    )
+]
+
+
+def test_consolidation_range_returns_the_maximal_qualifying_window():
+    result = consolidation_range(_CONSOL_BARS, end_idx=3, min_bars=2, max_bars=4, max_range=1.5)
+    assert result == (0, 100.7, 99.5)  # the full 4-bar window already qualifies (range 1.2 <= 1.5)
+
+
+def test_consolidation_range_none_when_even_the_shortest_window_fails():
+    result = consolidation_range(_CONSOL_BARS, end_idx=3, min_bars=2, max_bars=4, max_range=0.5)
+    assert result is None
+
+
+# --- vertical_move -------------------------------------------------------------------------------------
+
+_VERT_BARS = [
+    _bar("VERT", "5m", E_OPEN + i * 300.0, c, c + 0.2, c - 0.2, c)
+    for i, c in enumerate([100.0, 100.2, 100.5, 103.0])
+]
+
+
+def test_vertical_move_true_when_the_net_move_and_close_direction_both_qualify():
+    assert vertical_move(_VERT_BARS, end_idx=3, n=3, k=2.5, direction="up") is True
+
+
+def test_vertical_move_false_when_the_net_move_is_too_small():
+    assert vertical_move(_VERT_BARS, end_idx=3, n=3, k=5.0, direction="up") is False
+
+
+def test_vertical_move_require_volume_gate():
+    rising = [1.0, 1.2, 1.5, 2.5]
+    assert vertical_move(
+        _VERT_BARS, 3, 3, 2.5, "up", require_volume=True, rvol_surge=2.0, rvols=rising
+    ) is True
+    below_surge = [1.0, 1.2, 1.5, 1.9]
+    assert vertical_move(
+        _VERT_BARS, 3, 3, 2.5, "up", require_volume=True, rvol_surge=2.0, rvols=below_surge
+    ) is False
+
+
+# --- zone_touches ------------------------------------------------------------------------------------
+
+
+def test_zone_touches_re_arms_only_after_a_full_exit():
+    def _in(i):
+        return _bar("ZT", "5m", E_OPEN + i * 300.0, 100.6, 100.8, 99.5, 100.2)
+
+    def _above(i):
+        return _bar("ZT", "5m", E_OPEN + i * 300.0, 101.0, 101.5, 100.5, 101.0)
+
+    bars = [_in(0), _in(1), _above(2), _in(3)]
+    assert zone_touches(bars, 99.0, 100.0) == [0, 3]
+
+
+# --- market_context ------------------------------------------------------------------------------------
+
+
+def test_market_context_null_with_no_spy_bars_at_all():
+    assert market_context([], SESSION_DATE, E_OPEN + 900.0, lookback_bars=6) is None
+
+
+def test_market_context_null_when_not_enough_lookback_bars_exist_yet():
+    bars = [_bar("SPY", "5m", E_OPEN + i * 300.0, 400.0, 400.5, 399.5, 400.2) for i in range(3)]
+    # lookback=6 needs 7 prior bars; only 3 exist before the trigger epoch.
+    assert market_context(bars, SESSION_DATE, E_OPEN + 3 * 300.0, lookback_bars=6) is None
+
+
+def test_market_context_computes_the_move_once_enough_bars_exist():
+    bars = [
+        _bar("SPY", "5m", E_OPEN + i * 300.0, 400.0 + i * 0.1, 400.5 + i * 0.1, 399.5 + i * 0.1, 400.0 + i * 0.1)
+        for i in range(10)
+    ]
+    result = market_context(bars, SESSION_DATE, E_OPEN + 9 * 300.0 + 1.0, lookback_bars=6)
+    assert result == {
+        "move": pytest.approx(0.6), "close_before": pytest.approx(400.9), "bars_available": 10,
+    }
```
