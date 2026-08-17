# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/research/micro_join.py b/apps/backend/app/research/micro_join.py
index d6c366d..3aa169a 100644
--- a/apps/backend/app/research/micro_join.py
+++ b/apps/backend/app/research/micro_join.py
@@ -33,14 +33,33 @@ implementation of any measurement rail (the same class of judgment call
 importing, a sibling module's technique). Logged as an interpretation call in the iteration's dev
 handoff.
 
-**``band_touch_count`` is honestly zero this iteration.** No module anywhere in the shipped
-product yet enumerates discrete band-map wall-touch INSTANTS as a stored, countable list --
-identifying what counts as a "touch" is explicitly J-09's own predeclared-mechanism work (goal.md
-OUT OF SCOPE: "Any pilot-study-specific mechanism ... is J-09; J-03 only builds the generic join
-primitive and its honest corpus count"). ``join_band_touch`` below proves the JOIN PRIMITIVE
-itself works against an explicit, caller-supplied ``(symbol, as_of_epoch)`` pair (TC-2); there is
-simply no existing corpus of such pairs to count over yet, so ``joinable_corpus_counts`` reports
-the honest, non-fabricated zero rather than inventing a detector.
+**``band_touch_count`` is a typed "not enumerated" state, never a bare zero (iter-4 passenger
+fix).** No module anywhere in the shipped product yet enumerates discrete band-map wall-touch
+INSTANTS as a stored, countable list -- identifying what counts as a "touch" is explicitly J-09's
+own predeclared-mechanism work (goal.md OUT OF SCOPE: "Any pilot-study-specific mechanism ... is
+J-09; J-03 only builds the generic join primitive and its honest corpus count"). ``join_band_touch``
+below proves the JOIN PRIMITIVE itself works against an explicit, caller-supplied ``(symbol,
+as_of_epoch)`` pair (TC-2); there is simply no existing corpus of such pairs to count over yet. The
+J-03 iteration originally served a bare ``0`` here -- indistinguishable, at the response's own
+surface, from "we counted and found zero touches". The iter-4 fix (goal.md J-04 passenger item)
+replaces it with ``{"status": "not_enumerated", "count": None}`` (``_band_touch_not_enumerated``,
+``BAND_TOUCH_STATUS_NOT_ENUMERATED``) -- a reader can no longer mistake absence-of-a-detector for a
+real, counted zero. ``total`` is defined as ``playbook_signal_count`` alone (never summing a
+not-yet-a-number band-touch state): numerically identical to before this fix, since the prior bare
+``0`` always contributed nothing to the sum either (TC-16). Defining an actual touch enumeration
+stays J-09's job; when it lands, this becomes ``{"status": "enumerated", "count": <int>}``.
+
+**A corrupt playbook record surfaces honestly, never a silent undercount (iter-4 passenger fix).**
+``playbook_store.list()`` returns ``(records, errors)`` (the SAME shape ``DatasetStore.list()``
+serves, and the shape every reader of it already surfaces at ITS own call site --
+``desk_playbook.PlaybookStore.list()``'s own docstring: "an EXPLICIT error row per file that failed
+verification"). The J-03 iteration's own ``joinable_corpus_counts`` discarded the error half
+outright (``playbook_store.list()[0]``) -- a corrupted playbook file would silently vanish from
+``total``/``playbook_signal_count``/``by_setup_id`` with no trace anywhere in the response. Fixed
+by capturing both halves and serving the error half verbatim as ``playbook_integrity_errors`` --
+the corruption is now visible beside the (necessarily undercounted, but no longer SILENTLY
+undercounted) count, the same discipline dataset errors already get via ``micro_readiness.py``'s
+own ``integrity_errors`` field.
 
 **Outcome-start basis (assumption-ledger entry, this iteration).** Outcome start = the trigger's
 own ``anchor_at`` (never a later, conditioned instant) -- no per-candidate conditioning feature
@@ -76,10 +95,13 @@ __all__ = [
     "JOIN_STATUS_NO_COVERING_SNAPSHOT",
     "JOIN_STATUS_NO_ROW_BEFORE_TRIGGER",
     "JOIN_STATUS_NO_BAND_CONTEXT",
+    "BAND_TOUCH_STATUS_NOT_ENUMERATED",
     "find_covering_dataset",
     "find_covering_snapshot",
     "feature_row_at_trigger",
     "outcome_rows_after_trigger",
+    "outcome_rows_at_position",
+    "outcome_row_at_single_horizon",
     "join_playbook_signal",
     "join_band_touch",
     "joinable_corpus_counts",
@@ -207,8 +229,16 @@ def _trade_horizon_row(trade_rows: list[dict], anchor_pos: int, n_trades: int) -
 
 
 def _shares_horizon_row(trade_rows: list[dict], anchor_pos: int, shares_threshold: int) -> dict | None:
+    """iter-4 perf fix (behavior-unchanged): iterates by INDEX rather than ``trade_rows[anchor_pos
+    + 1:]`` -- that slice notation copies every remaining row on EVERY call regardless of how
+    quickly the loop below breaks, which is O(n) per call and, summed across one caller evaluating
+    every anchor of a dataset (``scout.extract_anchors``, J-04), O(n^2) overall -- measured to hang
+    ``POST /research/desk/micro/scout/compute`` against the real 18-dataset corpus. Output is
+    byte-identical: same iteration order, same early-return row, same ``None`` when the threshold
+    is never reached."""
     cumulative = 0.0
-    for row in trade_rows[anchor_pos + 1 :]:
+    for i in range(anchor_pos + 1, len(trade_rows)):
+        row = trade_rows[i]
         cumulative += row["size"]
         if cumulative >= shares_threshold:
             return row
@@ -218,9 +248,14 @@ def _shares_horizon_row(trade_rows: list[dict], anchor_pos: int, shares_threshol
 def _clock_horizon_row(trade_rows: list[dict], anchor_pos: int, horizon_ts: float) -> dict | None:
     """The nearest at-or-before row for a CLOCK horizon, sampled from the trade-anchored
     representation (the ONLY representation the section 2.4 benchmark chose -- there is no
-    standalone quote row to sample instead; an interpretation call, logged in the dev handoff)."""
+    standalone quote row to sample instead; an interpretation call, logged in the dev handoff).
+
+    iter-4 perf fix (behavior-unchanged): the SAME index-iteration fix as ``_shares_horizon_row``
+    above, for the identical reason (``trade_rows[anchor_pos:]`` was an O(n)-per-call slice
+    copy)."""
     candidate = None
-    for row in trade_rows[anchor_pos:]:
+    for i in range(anchor_pos, len(trade_rows)):
+        row = trade_rows[i]
         if row["anchor_at"] <= horizon_ts:
             candidate = row
         else:
@@ -287,12 +322,87 @@ def outcome_rows_after_trigger(
     ``anchor_row`` (a row returned by ``feature_row_at_trigger`` over the SAME ``rows``). Outcome
     start = ``anchor_row["anchor_at"]`` (this iteration's assumption-ledger entry -- module
     docstring). Each entry carries the mid-basis primary, the last-trade sensitivity basis, and
-    the spread-at-outcome-start cost-proxy column, never merged into either outcome's own value."""
+    the spread-at-outcome-start cost-proxy column, never merged into either outcome's own value.
+
+    ``trade_rows.index(anchor_row)`` is an O(n) scan -- fine for the single at-or-before lookup
+    this function's own callers (``_join_core``) make once per join, but pathological for a
+    caller iterating every anchor of a whole snapshot (O(n^2) overall). ``outcome_rows_at_position``
+    below is the O(1)-position counterpart for exactly that caller shape (iter-4, J-04's own
+    ``scout.extract_anchors``, added when a live run against the real 18-dataset corpus stalled on
+    this scan -- see that function's own docstring)."""
     trade_rows = _trade_rows(rows)
     anchor_pos = trade_rows.index(anchor_row)
     return _outcome_rows_after(trade_rows, anchor_pos, session_end_ts, side=side)
 
 
+def outcome_rows_at_position(
+    trade_rows: list[dict], anchor_pos: int, session_end_ts: float, *, side: str | None = None
+) -> list[dict]:
+    """The O(1)-position counterpart to ``outcome_rows_after_trigger`` (module docstring, iter-4):
+    for a caller that ALREADY knows an anchor's own position in its trade-only row list (e.g. one
+    iterating via ``enumerate(trade_rows)``), this skips the O(n) ``.index()`` lookup that function
+    performs internally -- byte-identical output to
+    ``outcome_rows_after_trigger(rows, trade_rows[anchor_pos], session_end_ts, side=side)`` for the
+    SAME ``trade_rows``/``anchor_pos``/``session_end_ts``/``side`` (both call the SAME
+    ``_outcome_rows_after`` core -- no second outcome implementation, the read-side law honored).
+
+    Takes ``trade_rows`` (a plain ``list``, not ``Sequence``) and passes it through UNCOPIED:
+    ``_outcome_rows_after`` only ever reads it, never mutates it, so a defensive ``list(...)`` copy
+    here would itself be an O(n) cost paid on EVERY call -- exactly the anti-pattern this function
+    exists to eliminate, and the reason a caller iterating every anchor of a large dataset must
+    pass the SAME list object through every call, never a fresh copy per anchor."""
+    return _outcome_rows_after(trade_rows, anchor_pos, session_end_ts, side=side)
+
+
+def outcome_row_at_single_horizon(
+    trade_rows: list[dict],
+    anchor_pos: int,
+    horizon_kind: str,
+    horizon_value: int,
+    session_end_ts: float,
+    *,
+    side: str | None = None,
+) -> dict:
+    """ONE entry of the closed outcome set (spec section 4) -- computes only the requested
+    ``(horizon_kind, horizon_value)`` pair, byte-identical to the matching entry of
+    ``outcome_rows_at_position(...)``'s own list, by calling the IDENTICAL per-horizon-kind
+    row-finder (``_trade_horizon_row``/``_shares_horizon_row``/``_clock_horizon_row``) and
+    ``_build_outcome`` core those functions already use (no second implementation).
+
+    Exists because ``_outcome_rows_after`` always computes the FULL closed set (2 trade + 2 shares
+    + 3 clock horizons) even when a caller wants exactly one -- fine for the join primitives' own
+    call volume (once per playbook signal or band touch), but for a caller evaluating one horizon
+    across EVERY anchor of a large dataset (``scout.extract_anchors``, J-04), the other 6 unused
+    horizons' own forward scans (``_shares_horizon_row``/``_clock_horizon_row``, each bounded only
+    by how many subsequent trades it takes to satisfy the threshold) are pure waste -- measured on
+    the real NVDA dataset (~929K trades) to turn a should-be-fast trade-count-horizon extraction
+    into a multi-minute stall. A trade-count horizon (``horizon_kind="trades"``) resolves in O(1)
+    here (direct index arithmetic, no scan of any kind) since the unused shares/clock row-finders
+    are never even called."""
+    anchor_row = trade_rows[anchor_pos]
+    if horizon_kind == "trades":
+        horizon_row = _trade_horizon_row(trade_rows, anchor_pos, horizon_value)
+        horizon_ts = (
+            horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
+        )
+    elif horizon_kind == "shares":
+        horizon_row = _shares_horizon_row(trade_rows, anchor_pos, horizon_value)
+        horizon_ts = (
+            horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
+        )
+    elif horizon_kind == "clock_seconds":
+        horizon_ts = anchor_row["anchor_at"] + horizon_value
+        horizon_row = (
+            None if horizon_ts > session_end_ts else _clock_horizon_row(trade_rows, anchor_pos, horizon_ts)
+        )
+    else:
+        raise ValueError(f"unknown horizon_kind {horizon_kind!r}")
+    return _build_outcome(
+        kind=horizon_kind, value=horizon_value, anchor_row=anchor_row, horizon_row=horizon_row,
+        horizon_ts=horizon_ts, session_end_ts=session_end_ts, side=side,
+    )
+
+
 # --- the shared join core --------------------------------------------------------------------------
 
 
@@ -364,25 +474,43 @@ def join_band_touch(
 
 # --- the honest joinable-corpus count (micro_readiness.py's new field) -----------------------------
 
+# The closed vocabulary for band_touch_count's "not enumerated" state (iter-4 passenger fix) -- see
+# the module docstring. A future J-09 caller wiring a real touch enumeration in adds a sibling
+# "enumerated" status; this iteration serves only the honest absence.
+BAND_TOUCH_STATUS_NOT_ENUMERATED = "not_enumerated"
+
+
+def _band_touch_not_enumerated() -> dict:
+    """A FRESH dict every call (never a shared mutable literal -- the ``desk_playbook.py``
+    per-list-copy discipline, applied to a plain dict here) so no caller can ever poison a later
+    read by mutating what it received."""
+    return {"status": BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
+
 
 def joinable_corpus_counts(dataset_store: DatasetStore, playbook_store) -> dict:
-    """``total``/``playbook_signal_count``/``band_touch_count``/``by_setup_id`` -- every recorded
-    playbook signal whose ``(symbol, trigger_ts)`` falls inside a recorded tick dataset's own
-    window (module docstring's dataset-window match), counted honestly from the real stores.
-    Never requires a snapshot to already be BUILT: a snapshot is a reproducible, rebuildable cache
-    of the SAME tick data (``micro_snapshots.py``'s own "derived, rebuildable" docstring) -- an
-    unbuilt one says nothing about whether the underlying evidence is joinable.
+    """``total``/``playbook_signal_count``/``band_touch_count``/``by_setup_id``/
+    ``playbook_integrity_errors`` -- every recorded playbook signal whose ``(symbol, trigger_ts)``
+    falls inside a recorded tick dataset's own window (module docstring's dataset-window match),
+    counted honestly from the real stores. Never requires a snapshot to already be BUILT: a
+    snapshot is a reproducible, rebuildable cache of the SAME tick data (``micro_snapshots.py``'s
+    own "derived, rebuildable" docstring) -- an unbuilt one says nothing about whether the
+    underlying evidence is joinable.
 
     Fails CLOSED, never silently under-counts (the iter-2 "streamed-artifact completeness"
     lesson, applied to this enumeration loop): a signal recording no symbol or no ``trigger_ts``
     is a structural, honest absence and is skipped (the identical treatment
     ``desk_playbook_context.record_band_context`` already gives it); a signal whose ``trigger_ts``
     is PRESENT but unparseable is never silently skipped -- ``parse_utc_epoch`` raises and this
-    function raises with it, rather than serving an undercounted total."""
+    function raises with it, rather than serving an undercounted total. A CORRUPTED playbook
+    record (``playbook_store.list()``'s own error half) is skipped from the count -- there is no
+    signal content to read from a file that failed verification -- but is never silently dropped
+    from the RESPONSE: it is surfaced verbatim in ``playbook_integrity_errors`` (module docstring's
+    iter-4 passenger fix)."""
     records, _errors = dataset_store.list()
     total_playbook = 0
     by_setup_id: dict[str, int] = {}
-    for playbook_record in playbook_store.list()[0]:
+    playbook_records, playbook_errors = playbook_store.list()
+    for playbook_record in playbook_records:
         for signal in playbook_record.get("signals") or []:
             symbol = signal.get("symbol")
             trigger_ts = signal.get("trigger_ts")
@@ -395,14 +523,13 @@ def joinable_corpus_counts(dataset_store: DatasetStore, playbook_store) -> dict:
             setup_id = signal.get("setup_id") or "unknown"
             by_setup_id[setup_id] = by_setup_id.get(setup_id, 0) + 1
 
-    # Honestly zero this iteration -- see the module docstring's "band_touch_count is honestly
-    # zero" section. Expressed as a variable (never a bare literal at the return site) so a future
-    # J-09 caller wiring a real touch enumeration in changes exactly one line.
-    band_touch_count = 0
-
     return {
-        "total": total_playbook + band_touch_count,
+        # `playbook_signal_count` alone -- `band_touch_count` is no longer a plain number to sum
+        # (module docstring); numerically identical to the pre-fix total, since the prior bare `0`
+        # always contributed nothing to the sum either (TC-16).
+        "total": total_playbook,
         "playbook_signal_count": total_playbook,
-        "band_touch_count": band_touch_count,
+        "band_touch_count": _band_touch_not_enumerated(),
         "by_setup_id": by_setup_id,
+        "playbook_integrity_errors": playbook_errors,
     }
diff --git a/apps/backend/app/research/micro_readiness.py b/apps/backend/app/research/micro_readiness.py
index 448c1b0..3caedbf 100644
--- a/apps/backend/app/research/micro_readiness.py
+++ b/apps/backend/app/research/micro_readiness.py
@@ -75,7 +75,7 @@ from zoneinfo import ZoneInfo
 
 from ..providers.base import Event, QuoteEvent, TradeEvent
 from .datasets import DatasetStore
-from .micro_join import joinable_corpus_counts
+from .micro_join import BAND_TOUCH_STATUS_NOT_ENUMERATED, joinable_corpus_counts
 from .referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
 
 __all__ = [
@@ -377,10 +377,19 @@ def build_readiness(
     # J-03: honestly zero (never computed) when no playbook_store is given at all -- a true
     # statement ("no playbook evidence was even checked"), never a fabricated count. When one IS
     # given, the count is owned entirely by micro_join.joinable_corpus_counts (never re-derived
-    # here -- module docstring).
+    # here -- module docstring). iter-4 passenger fix: this fallback shape now mirrors
+    # joinable_corpus_counts's own typed band_touch_count ("not enumerated", never a bare 0) and
+    # its playbook_integrity_errors key -- `[]` here is the SAME "nothing was checked, so nothing
+    # is known to be corrupt" convention every other empty/unbuilt store in this codebase reports
+    # (DatasetStore.list()/PlaybookStore.list() both answer `[]` on an absent store, never a
+    # fabricated warning).
     if playbook_store is None:
         joinable_corpus = {
-            "total": 0, "playbook_signal_count": 0, "band_touch_count": 0, "by_setup_id": {},
+            "total": 0,
+            "playbook_signal_count": 0,
+            "band_touch_count": {"status": BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None},
+            "by_setup_id": {},
+            "playbook_integrity_errors": [],
         }
     else:
         joinable_corpus = joinable_corpus_counts(store, playbook_store)
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 27708d3..497b9d1 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -34,6 +34,8 @@ from .micro_snapshots import (
     resolve_micro_snapshots_dir,
 )
 from .routes import get_dataset_store
+from .scout import ScoutComputeManager, list_scout_families
+from .scout_ledger import ScoutLedger, resolve_scout_ledger_dir
 
 router = APIRouter(prefix="/research/desk/micro", tags=["micro"])
 
@@ -152,3 +154,83 @@ def get_micro_snapshots_runs(snapshots_dir: str = Depends(get_micro_snapshots_di
     """The durable build-run history, newest first -- never 404 on zero runs (an honest empty
     list)."""
     return {"runs": read_run_log(snapshots_dir)}
+
+
+# --- J-04: the Scout + exploratory candidate ledger (scout.py, scout_ledger.py) -----------------
+
+
+def get_scout_ledger_dir() -> str:
+    """The scout ledger's directory -- ``TAPEOLOGY_MICRO_SCOUT_DIR`` if set, else a SIBLING of the
+    config-owned dataset directory (``scout_ledger.resolve_scout_ledger_dir`` -- see that
+    function's own docstring)."""
+    return resolve_scout_ledger_dir(CONFIG.dataset_dir_resolved())
+
+
+# The single in-flight (or last-terminal) scout-screening job for THIS process -- the same
+# module-singleton-behind-a-Depends-accessor precedent as the snapshot manager above.
+_scout_compute_manager = ScoutComputeManager()
+
+
+def get_scout_compute_manager() -> ScoutComputeManager:
+    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
+    ``get_micro_snapshot_compute_manager`` precedent) -- never reaches into the module-level
+    singleton directly."""
+    return _scout_compute_manager
+
+
+@router.get("/scout")
+def get_scout(ledger_dir: str = Depends(get_scout_ledger_dir)) -> dict:
+    """Every registered family's trials, verbatim as ledgered (``scout.list_scout_families`` --
+    see that function's own docstring). Never 404/500 on an empty ledger -- an honest empty
+    ``families`` list, the desk router's established never-404-on-absence convention. Page-load
+    GETs never compute (T-8): a screening RUN is an explicit operator act through
+    ``POST /scout/compute``."""
+    ledger = ScoutLedger(ledger_dir)
+    return {"families": list_scout_families(ledger)}
+
+
+@router.post("/scout/compute")
+def trigger_scout_compute(
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    snapshots_dir: str = Depends(get_micro_snapshots_dir),
+    ledger_dir: str = Depends(get_scout_ledger_dir),
+    manager: ScoutComputeManager = Depends(get_scout_compute_manager),
+) -> dict:
+    """Start a Scout screening run over the bounded reference candidate grid (ensuring
+    prerequisite snapshots exist first -- reuse-or-build), or refuse (single-flight) if one is
+    already running."""
+    result = manager.trigger(dataset_store, CONFIG, snapshots_dir, ledger_dir)
+    if result["state"] == "refused":
+        return result
+    return {"state": result["state"], "run_id": result["run_id"]}
+
+
+@router.get("/scout/compute")
+def get_scout_compute(manager: ScoutComputeManager = Depends(get_scout_compute_manager)) -> dict:
+    """The current (or last-terminal) screening job's progress -- never 404 (the idle default
+    before any job has ever run this process)."""
+    snap = manager.snapshot()
+    return {
+        "state": snap["state"],
+        "progress": snap["progress"],
+        "started_utc": snap["started_utc"],
+        "finished_utc": snap["finished_utc"],
+        "error": snap["error"],
+    }
+
+
+@router.post("/scout/compute/cancel")
+def cancel_scout_compute(manager: ScoutComputeManager = Depends(get_scout_compute_manager)) -> dict:
+    """Signal cooperative cancellation for the in-flight job -- a 409 for an idle manager (the
+    snapshot-compute-cancel route's own precedent), else ``{"state": "cancelled"}`` acknowledging
+    the REQUEST (the worker itself settles at the next candidate boundary)."""
+    if manager.snapshot()["state"] != "running":
+        raise HTTPException(status_code=409, detail="no scout screening run is currently running")
+    manager.cancel()
+    return {"state": "cancelled"}
+
+
+@router.get("/scout/runs")
+def get_scout_runs(ledger_dir: str = Depends(get_scout_ledger_dir)) -> dict:
+    """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
+    return {"runs": read_run_log(ledger_dir)}
diff --git a/apps/backend/tests/test_micro_join.py b/apps/backend/tests/test_micro_join.py
index 5e8a913..3104817 100644
--- a/apps/backend/tests/test_micro_join.py
+++ b/apps/backend/tests/test_micro_join.py
@@ -7,7 +7,15 @@ the existing (already-tested) J-02 pipeline -- this file never re-verifies J-02'
 only that ``micro_join.py`` LOCATES and serves the right rows. TC-4 is a pinned whole-module
 byte-freeze (the ``test_referee_guards.py`` precedent). TC-5's ``joinable_corpus`` readiness field
 is exercised end to end in ``test_micro_readiness.py`` instead -- this file covers the counting
-function it calls into (``joinable_corpus_counts``) directly, over small hermetic fixtures."""
+function it calls into (``joinable_corpus_counts``) directly, over small hermetic fixtures.
+
+**iter-4 passenger-fix additions (TC-14, TC-15, TC-16 -- ``docs/phases/goal-rapid-microscope-
+iter-4.md``, a DISTINCT numbering scope from this file's own iter-3 TC-1..9 above):** a corrupt
+playbook record now surfaces in ``playbook_integrity_errors`` rather than silently vanishing from
+the count (TC-14); ``band_touch_count`` is now a typed ``{"status": "not_enumerated", "count":
+None}`` rather than a bare ``0`` a reader could mistake for a real zero (TC-15); the REAL-corpus
+enumerated arithmetic (``playbook_signal_count``/``by_setup_id``) is unchanged by either fix
+(TC-16)."""
 
 from __future__ import annotations
 
@@ -427,9 +435,10 @@ def test_joinable_corpus_counts_only_counts_signals_inside_a_recorded_tick_windo
     counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
 
     assert counts["playbook_signal_count"] == 1
-    assert counts["band_touch_count"] == 0
+    assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
     assert counts["total"] == 1
     assert counts["by_setup_id"] == {"opening_range_break": 1}
+    assert counts["playbook_integrity_errors"] == []
 
 
 def test_joinable_corpus_counts_breaks_down_by_setup_id(tmp_path):
@@ -460,7 +469,13 @@ def test_joinable_corpus_counts_is_an_honest_zero_with_no_playbook_records(tmp_p
 
     counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
 
-    assert counts == {"total": 0, "playbook_signal_count": 0, "band_touch_count": 0, "by_setup_id": {}}
+    assert counts == {
+        "total": 0,
+        "playbook_signal_count": 0,
+        "band_touch_count": {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None},
+        "by_setup_id": {},
+        "playbook_integrity_errors": [],
+    }
 
 
 def test_joinable_corpus_counts_fails_closed_on_a_malformed_trigger_ts_never_silently_undercounts(tmp_path):
@@ -507,3 +522,198 @@ def test_find_covering_snapshot_is_none_without_a_built_snapshot(tmp_path):
         "ZJN", micro_join.parse_utc_epoch("2026-06-09T13:00:10Z"), dataset_store, snapshots_dir, CONFIG
     )
     assert result is None
+
+
+# --- TC-14 (iter-4 passenger fix): a corrupt playbook record surfaces honestly, never a silent
+# undercount --------------------------------------------------------------------------------------
+
+
+def test_tc14_a_corrupted_playbook_record_surfaces_in_playbook_integrity_errors(tmp_path):
+    """Mirrors ``test_micro_readiness.py``'s own ``test_corrupted_dataset_is_surfaced_never_
+    dropped_never_a_crash`` precedent, applied to the PLAYBOOK store's own on-disk shape (the same
+    ``{"file_checksum": ..., "record": {...}}`` envelope every store in this codebase hashes)."""
+    import json
+
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _plant_dataset(
+        dataset_store, symbol="ZJN",
+        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+    )
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    healthy = _plant_playbook_signal(
+        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-healthy",
+        signals=[{"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:10Z"}],
+    )
+    corrupted = _plant_playbook_signal(
+        playbook_store, session_date="2026-06-10", playbook_input_signature="sig-corrupt",
+        signals=[{"symbol": "ZJN", "setup_id": "jbe", "trigger_ts": "2026-06-10T13:00:10Z"}],
+    )
+    corrupted_path = playbook_store._path(corrupted["id"])
+    payload = json.loads(corrupted_path.read_text())
+    payload["record"]["meta"]["session_date"] = "tampered"
+    corrupted_path.write_text(json.dumps(payload))
+
+    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+
+    assert len(counts["playbook_integrity_errors"]) == 1
+    assert counts["playbook_integrity_errors"][0]["file"] == corrupted_path.name
+    # the healthy record is NEVER dropped alongside the corrupted one -- never a silent full
+    # undercount just because ONE other file failed verification.
+    assert counts["playbook_signal_count"] == 1
+    assert counts["by_setup_id"] == {"opening_range_break": 1}
+    assert counts["total"] == 1
+
+
+def test_tc14_healthy_playbook_records_still_count_when_none_are_corrupted(tmp_path):
+    """A lint that can fail proves something: the healthy path still serves an EMPTY error list,
+    never a fabricated one."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _plant_dataset(
+        dataset_store, symbol="ZJN",
+        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+    )
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    _plant_playbook_signal(
+        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-clean",
+        signals=[{"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:10Z"}],
+    )
+    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+    assert counts["playbook_integrity_errors"] == []
+    assert counts["playbook_signal_count"] == 1
+
+
+# --- TC-15 (iter-4 passenger fix): band_touch_count is a typed "not enumerated" state --------------
+
+
+def test_tc15_band_touch_count_is_a_typed_not_enumerated_state_never_a_bare_zero(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+    band_touch = counts["band_touch_count"]
+    assert not isinstance(band_touch, int)  # never a bare int a reader could read as "counted zero"
+    assert band_touch == {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
+    assert band_touch["status"] == "not_enumerated"
+    assert band_touch["count"] is None
+
+
+def test_tc15_band_touch_count_shape_is_a_fresh_dict_every_call_never_shared_mutable_state(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    first = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+    first["band_touch_count"]["count"] = 999  # mutate the caller's own copy
+    second = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+    assert second["band_touch_count"]["count"] is None  # unaffected by the earlier mutation
+
+
+# --- TC-16: the real-corpus enumerated arithmetic is unchanged by either passenger fix --------------
+
+
+def test_tc16_real_corpus_joinable_corpus_arithmetic_is_unchanged_by_the_passenger_fixes():
+    """Against the REAL ``.data/datasets`` + playbook stores (a direct call against the real
+    stores, per the phase spec's own TC-16 wording -- not the browser rig): ``playbook_signal_
+    count`` stays ``2`` and ``by_setup_id`` stays ``{"range_trade": 2}`` -- the fixes changed only
+    corruption-surfacing and the ``band_touch_count``/``total`` representation, never the
+    enumerated arithmetic itself."""
+    from app.research.desk_playbook import resolve_desk_playbook_dir
+
+    dataset_store = DatasetStore(CONFIG.dataset_dir_resolved())
+    playbook_store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
+
+    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+
+    assert counts["playbook_signal_count"] == 2
+    assert counts["by_setup_id"] == {"range_trade": 2}
+    assert counts["total"] == 2  # total == playbook_signal_count alone now (module docstring)
+    assert counts["playbook_integrity_errors"] == []  # the real corpus is healthy
+    assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
+
+
+# --- iter-4 perf fix: outcome_rows_at_position / outcome_row_at_single_horizon are byte-identical
+# to outcome_rows_after_trigger's own output -- added when a live Scout run against the real
+# 18-dataset corpus (J-04) exposed an O(n^2) cost in the O(n) `.index()` lookup + a per-call
+# O(n) slice copy inside `_shares_horizon_row`/`_clock_horizon_row`; both are rewritten here to
+# avoid an O(n)-per-call cost, with zero output change -----------------------------------------
+
+
+def test_outcome_rows_at_position_matches_outcome_rows_after_trigger_exactly(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    rows = pg_snapshot["rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
+
+    for anchor_pos in (0, 9, 49, 50, len(trade_rows) - 3, len(trade_rows) - 1):
+        anchor_row = trade_rows[anchor_pos]
+        via_trigger = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts, side=None)
+        via_position = micro_join.outcome_rows_at_position(trade_rows, anchor_pos, session_end_ts, side=None)
+        assert via_position == via_trigger
+
+
+def test_outcome_rows_at_position_matches_with_a_hypothesis_side(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    rows = pg_snapshot["rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
+    anchor_pos = 9
+    anchor_row = trade_rows[anchor_pos]
+
+    via_trigger = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts, side="buy")
+    via_position = micro_join.outcome_rows_at_position(trade_rows, anchor_pos, session_end_ts, side="buy")
+    assert via_position == via_trigger
+
+
+def test_outcome_row_at_single_horizon_matches_the_corresponding_entry_of_the_full_closed_set(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
+
+    horizon_pairs = [
+        ("trades", 20), ("trades", 100),
+        ("shares", 5_000), ("shares", 50_000),
+        ("clock_seconds", 30), ("clock_seconds", 60), ("clock_seconds", 300),
+    ]
+    for anchor_pos in (9, 49, len(trade_rows) - 3):
+        full_set = micro_join.outcome_rows_at_position(trade_rows, anchor_pos, session_end_ts, side=None)
+        for kind, value in horizon_pairs:
+            single = micro_join.outcome_row_at_single_horizon(
+                trade_rows, anchor_pos, kind, value, session_end_ts, side=None
+            )
+            expected = next(o for o in full_set if o["horizon_kind"] == kind and o["horizon_value"] == value)
+            assert single == expected
+
+
+def test_outcome_row_at_single_horizon_rejects_an_unknown_horizon_kind(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
+    with pytest.raises(ValueError):
+        micro_join.outcome_row_at_single_horizon(trade_rows, 9, "not-a-real-kind", 20, session_end_ts)
+
+
+def test_shares_and_clock_horizon_rows_are_unchanged_by_the_index_iteration_rewrite(pg_snapshot):
+    """A hand-computed oracle over the SAME small fixture TC-1 already trusts: the rewritten
+    ``_shares_horizon_row``/``_clock_horizon_row`` (index iteration, never a slice copy) return
+    the identical row a naive, obviously-correct reference implementation finds."""
+    trade_rows = pg_snapshot["trade_rows"]
+    anchor_pos = 9
+
+    def _reference_shares_horizon_row(threshold):
+        cumulative = 0.0
+        for row in trade_rows[anchor_pos + 1 :]:
+            cumulative += row["size"]
+            if cumulative >= threshold:
+                return row
+        return None
+
+    def _reference_clock_horizon_row(horizon_ts):
+        candidate = None
+        for row in trade_rows[anchor_pos:]:
+            if row["anchor_at"] <= horizon_ts:
+                candidate = row
+            else:
+                break
+        return candidate
+
+    assert micro_join._shares_horizon_row(trade_rows, anchor_pos, 5_000) == _reference_shares_horizon_row(5_000)
+    assert micro_join._shares_horizon_row(trade_rows, anchor_pos, 50_000) == _reference_shares_horizon_row(50_000)
+    horizon_ts = trade_rows[anchor_pos]["anchor_at"] + 60
+    assert micro_join._clock_horizon_row(trade_rows, anchor_pos, horizon_ts) == _reference_clock_horizon_row(horizon_ts)
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
index 14c4a57..963e67d 100644
--- a/apps/backend/tests/test_micro_readiness.py
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -466,7 +466,11 @@ def test_joinable_corpus_defaults_to_an_honest_zero_without_a_playbook_store(tmp
     cache = MicroReadinessCache(str(tmp_path / "cache.db"))
     body = build_readiness(store, cache, dataset_dir=str(tmp_path / "datasets"))
     assert body["joinable_corpus"] == {
-        "total": 0, "playbook_signal_count": 0, "band_touch_count": 0, "by_setup_id": {},
+        "total": 0,
+        "playbook_signal_count": 0,
+        "band_touch_count": {"status": "not_enumerated", "count": None},
+        "by_setup_id": {},
+        "playbook_integrity_errors": [],
     }
 
 
@@ -496,8 +500,11 @@ def test_joinable_corpus_matches_joinable_corpus_counts_directly(tmp_path):
 
     assert body["joinable_corpus"] == joinable_corpus_counts(store, playbook_store)
     assert body["joinable_corpus"] == {
-        "total": 1, "playbook_signal_count": 1, "band_touch_count": 0,
+        "total": 1,
+        "playbook_signal_count": 1,
+        "band_touch_count": {"status": "not_enumerated", "count": None},
         "by_setup_id": {"opening_range_break": 1},
+        "playbook_integrity_errors": [],
     }
 
 
@@ -530,8 +537,11 @@ def test_joinable_corpus_is_served_through_the_route_and_is_non_negative_and_nev
     second = c.get("/research/desk/micro/readiness").json()["joinable_corpus"]
 
     assert first == second
-    for key in ("total", "playbook_signal_count", "band_touch_count"):
+    for key in ("total", "playbook_signal_count"):
         assert isinstance(first[key], int) and first[key] >= 0
+    # band_touch_count is a typed "not enumerated" state, never a bare int (iter-4 passenger fix,
+    # TC-15) -- distinguishable from a real zero count.
+    assert first["band_touch_count"] == {"status": "not_enumerated", "count": None}
     assert first["playbook_signal_count"] == 1  # only the in-window signal counts
     assert first["by_setup_id"] == {"jbe": 1}
 
@@ -543,5 +553,30 @@ def test_real_corpus_readiness_still_serves_an_honest_zero_joinable_corpus_witho
     ``playbook_store``) -- confirms the new field is present and honestly zero there too, never an
     absent key on the real 18-dataset corpus response."""
     assert real_readiness["joinable_corpus"] == {
-        "total": 0, "playbook_signal_count": 0, "band_touch_count": 0, "by_setup_id": {},
+        "total": 0,
+        "playbook_signal_count": 0,
+        "band_touch_count": {"status": "not_enumerated", "count": None},
+        "by_setup_id": {},
+        "playbook_integrity_errors": [],
     }
+
+
+# --- TC-15 (iter-4 passenger fix, docs/phases/goal-rapid-microscope-iter-4.md): band_touch_count is
+# a typed "not enumerated" state on THIS route, never a bare zero a reader could mistake for a real
+# count ------------------------------------------------------------------------------------------
+
+
+def test_tc15_readiness_route_serves_band_touch_count_as_a_typed_not_enumerated_state(client):
+    c, _store, _cache = client
+    resp = c.get("/research/desk/micro/readiness")
+    assert resp.status_code == 200
+    band_touch = resp.json()["joinable_corpus"]["band_touch_count"]
+    assert not isinstance(band_touch, int)
+    assert band_touch == {"status": "not_enumerated", "count": None}
+
+
+def test_tc15_real_corpus_readiness_also_serves_the_typed_band_touch_count(real_readiness):
+    band_touch = real_readiness["joinable_corpus"]["band_touch_count"]
+    assert not isinstance(band_touch, int)
+    assert band_touch["status"] == "not_enumerated"
+    assert band_touch["count"] is None
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-rapid-microscope-index.html   |  11 ++-
 .../.engine.lock/epoch                             |   2 +-
 .../goal-session-rapid-microscope/.engine.lock/pid |   2 +-
 runs/goal-session-rapid-microscope/engine.pid      |   2 +-
 runs/goal-session-rapid-microscope/session.json    |   6 +-
 runs/goal-session-rapid-microscope/summary.md      | 100 +++++++++++++++++----
 runs/goal-session-rapid-microscope/telemetry.jsonl |  21 +++++
 .../trace/trace.jsonl                              |   2 +
 8 files changed, 118 insertions(+), 28 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
