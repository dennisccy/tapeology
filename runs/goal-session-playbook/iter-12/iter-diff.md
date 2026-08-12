# Iteration diff (bounded)

Files changed: 9. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_desk_playbook_evidence.py` (26 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_playbook_backscan.py b/apps/backend/app/research/desk_playbook_backscan.py
index 59a3bd0..95d45fe 100644
--- a/apps/backend/app/research/desk_playbook_backscan.py
+++ b/apps/backend/app/research/desk_playbook_backscan.py
@@ -105,14 +105,21 @@ _TERMINAL_STATES = ("done", "cancelled", "error")
 # exactly (never a fifth value).
 _OUTCOME_KEYS = ("reused", "recorded", "refused_non_session", "failed")
 
-# TC-13's positive scoping guard: the FOUR env vars every playbook/back-scan test or browser-QA rig
+# TC-13's positive scoping guard: the FIVE env vars every playbook/back-scan test or browser-QA rig
 # must scope together (the session ledger's own lesson -- reading a raw ``config.*_dir`` field or
 # scoping the store dir without its log-dir siblings silently orphans writes into the real store).
+# goal-playbook-iter-12 (J-11 passenger): ``TAPEOLOGY_BAR_INDEX_DB`` joins the other four -- the
+# derived bar-lookup index (``routes.py.get_bar_index``) lives under ``.data/`` by default too, so a
+# rig that scopes every OTHER store but leaves this one ambient would still touch the real
+# ``bar_index.db`` on any compute path that reads it. Every real scoped-rig launcher already exports
+# it (``qa_playbook_iter7_fixture_scoped_backend.sh`` and its siblings); this closes the gap between
+# what those scripts already DO and what this guard actually CHECKS.
 _SCOPING_ENV_VARS = (
     "TAPEOLOGY_DESK_PLAYBOOK_DIR",
     "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR",
     "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR",
     "TAPEOLOGY_DESK_UNIVERSE_DIR",
+    "TAPEOLOGY_BAR_INDEX_DB",
 )
 
 
@@ -159,13 +166,13 @@ def _empty_outcomes() -> dict:
 
 def _assert_scoped(root: str | Path) -> None:
     """A TEST/BROWSER-QA-LANE-ONLY positive guard -- NEVER called from the live HTTP routes below.
-    An operator's REAL compute legitimately runs with none of the four ``_SCOPING_ENV_VARS`` set,
+    An operator's REAL compute legitimately runs with none of the five ``_SCOPING_ENV_VARS`` set,
     resolving to the ambient ``.data/`` store; wiring this into the route would wrongly refuse every
     genuine production compute. Instead, a test fixture or browser-QA rig calls this BEFORE
     triggering any playbook or back-scan compute against a scoped root, so a scoping mistake is
     refused loudly, in the rig itself, before it ever reaches ``run_playbook_and_record``.
 
-    Raises ``PlaybookNotScopedError`` unless EVERY one of the four scoping env vars is set AND
+    Raises ``PlaybookNotScopedError`` unless EVERY one of the five scoping env vars is set AND
     resolves to a path rooted under ``root`` and outside any ``.data/`` directory. Mirrors
     ``scripts/seed_playbook_fixture_rig.py``'s own ``_assert_scoped`` helper (that script's own,
     narrower three-directory version predates this one and is left as-is); this module's version is
@@ -188,8 +195,8 @@ def _assert_scoped(root: str | Path) -> None:
             "playbook/back-scan compute REFUSED -- store directories are not scoped:\n  "
             + "\n  ".join(problems)
             + "\nExport TAPEOLOGY_DESK_PLAYBOOK_DIR / TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR / "
-              "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR / TAPEOLOGY_DESK_UNIVERSE_DIR (all four) "
-              "at the scoped root first."
+              "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR / TAPEOLOGY_DESK_UNIVERSE_DIR / "
+              "TAPEOLOGY_BAR_INDEX_DB (all five) at the scoped root first."
         )
 
 
diff --git a/apps/backend/app/research/desk_playbook_evidence.py b/apps/backend/app/research/desk_playbook_evidence.py
index 0b5898f..f56fca1 100644
--- a/apps/backend/app/research/desk_playbook_evidence.py
+++ b/apps/backend/app/research/desk_playbook_evidence.py
@@ -11,11 +11,16 @@ baseline anchor's own forward-shaped measurement were ALREADY produced by
 module never touches a bar, never calls ``_measure_from``, and reuses
 ``desk_forward._collect_measures`` (imported verbatim, zero diff) to pool the ALREADY-MEASURED
 per-signal/per-anchor leaves into per-measure value lists with their truncation-exclusion already
-applied. The ONLY genuinely new math here is the quartile fold (``_quartile_stats``) --
-``_collect_measures``/``_avg_cell`` (the rail's own pooling helpers) produce ``n``/``mean_pct``/
-``median_pct``/``n_truncated`` but carry no p25/p75 at all; J-08 needs its own evidence-only fold
-for those two, which is new EVIDENCE math, not a second implementation of anything the rail
-already had.
+applied. The genuinely new math here is EVIDENCE-only, never a second implementation of anything
+the rail already had: the quartile fold (``_quartile_stats``) -- ``_collect_measures``/
+``_avg_cell`` (the rail's own pooling helpers) produce ``n``/``mean_pct``/``median_pct``/
+``n_truncated`` but carry no p25/p75 at all, so J-08 folds those two itself -- and (J-11) the
+exclusion-count fold (``_n_unmeasured_by_label``), which COUNTS, never re-derives, how many pooled
+events carry a null ``return_pct`` at each horizon label: the exact fact
+``_collect_measures``'s own ``if measure["return_pct"] is None: continue`` already reads per event
+and then lets evaporate uncounted. This module also folds ``n_sessions`` -- the number of distinct
+recorded ``session_date``s behind a pool -- straight off the per-file projection's own
+``session_date``, again zero re-derivation of anything the rail or the store computes.
 
 **The evidence pools exactly ONE signature (a hard anti-goal).** ``fold_evidence`` resolves the
 CURRENT default signature via ``compute_playbook_input_signature`` (the exact function
@@ -106,8 +111,14 @@ EVIDENCE_REGISTER = (
     "A cell tagged below_min_n has fewer than the disclosure floor's worth of recorded signals — "
     "a disclosure, never a filter: its numbers are still served, never hidden, never nulled out "
     "for being thin. Truncated values are excluded from every median/mean pool with the exclusion "
-    "counted, never silently dropped. A signature other than the current one is listed by its own "
-    "dates and created span, never folded into these cells. No fills and no costs are modeled "
+    "counted, never silently dropped — and a signal whose own horizon leaf was recorded "
+    "unmeasurable at that window (finer than the session's own recorded touch series) is excluded "
+    "the same way, counted as n_unmeasured instead of n_truncated, on the signal side and, "
+    "identically, on the baseline side (n_truncated, n_unmeasured), beside n_sessions, the number "
+    "of distinct recorded dates each pool draws from. A signature other than the current one is "
+    "listed by its own dates, record count, and created span, never folded into these cells, and "
+    "the pooled signature's own record count, dates, and created span are named the same way, up "
+    "front, in this payload's own basis block. No fills and no costs are modeled "
     "anywhere on this payload, which describes measurements of what already happened and nothing "
     "about what happens next"
 )
@@ -268,11 +279,13 @@ def _quartile_stats(values: list[float]) -> tuple[float | None, float | None, fl
     return statistics.median(values), p25, p75, statistics.mean(values)
 
 
-def _signal_cell(values: list[float], n_truncated: int) -> dict:
+def _signal_cell(values: list[float], n_truncated: int, n_unmeasured: int, n_sessions: int) -> dict:
     median, p25, p75, mean = _quartile_stats(values)
     return {
         "n": len(values),
         "n_truncated": n_truncated,
+        "n_unmeasured": n_unmeasured,
+        "n_sessions": n_sessions,
         "median_pct": median,
         "p25_pct": p25,
         "p75_pct": p75,
@@ -280,10 +293,13 @@ def _signal_cell(values: list[float], n_truncated: int) -> dict:
     }
 
 
-def _baseline_cell(values: list[float]) -> dict:
+def _baseline_cell(values: list[float], n_truncated: int, n_unmeasured: int, n_sessions: int) -> dict:
     median, p25, p75, mean = _quartile_stats(values)
     return {
         "n_baseline": len(values),
+        "n_truncated": n_truncated,
+        "n_unmeasured": n_unmeasured,
+        "n_sessions": n_sessions,
         "median_pct": median,
         "p25_pct": p25,
         "p75_pct": p75,
@@ -291,6 +307,59 @@ def _baseline_cell(values: list[float]) -> dict:
     }
 
 
+# --- exclusion counting (J-11, new evidence-only math -- pure counts, never a re-measurement) -------
+
+# The four rail horizon LABELS, in the rail's own declared order -- NOT re-derived from
+# PLAYBOOK_SIGNAL_MEASURES/DESK_FORWARD_MEASURE_KEYS, whose own order interleaves them with the
+# session-level trio and the mdd siblings.
+_HORIZON_LABELS: tuple[str, ...] = tuple(label for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES)
+
+
+def _measure_horizon_label(measure: str) -> str | None:
+    """Which of the four horizon LABELS governs ``measure``'s own unmeasurability -- a horizon's
+    own return key (e.g. ``"1h"``) and its two ``mdd_long_1h``/``mdd_short_1h`` siblings all read
+    the EXACT SAME ``event["horizons"]["1h"]["return_pct"]`` fact (``_measure_from`` writes a
+    horizon leaf as one all-null shape or one all-populated shape, never a mix), so all three
+    measure keys share one label and therefore one shared count (TC-2). ``None`` for the
+    session-level trio (``to_close``/``mdd_long``/``mdd_short``), which reads the session-end
+    fields ``_measure_from`` always populates -- never unmeasurable."""
+    if measure in _HORIZON_LABELS:
+        return measure
+    for prefix in ("mdd_long_", "mdd_short_"):
+        if measure.startswith(prefix) and measure[len(prefix) :] in _HORIZON_LABELS:
+            return measure[len(prefix) :]
+    return None
+
+
+def _n_unmeasured_by_label(events: list[dict]) -> dict[str, int]:
+    """Per horizon LABEL, how many of ``events`` carry ``return_pct: None`` there -- the exact fact
+    ``desk_forward._collect_measures`` silently ``continue``s past with no counter. Read directly
+    off each event's own leaf, never derived by subtracting pool lengths (the module NOTES this
+    iteration carries: an MDD sibling's own value list can in principle be shorter than its return
+    sibling's for a reason UNRELATED to unmeasurability -- a pre-per-horizon-MDD legacy leaf missing
+    ``mdd_long_pct``/``mdd_short_pct`` while ``return_pct`` is populated; never observed in playbook
+    data today, not provably impossible, and a subtraction-only reading would silently get it wrong
+    the day it is). Every label is always a key, even at ``0`` -- an empty ``events`` list (an empty
+    pool) reads every label ``0``, never an omitted key, mirroring the existing zero-signals
+    precedent the rest of this module already follows."""
+    counts = {label: 0 for label in _HORIZON_LABELS}
+    for event in events:
+        horizons = event.get("horizons") or {}
+        for label in _HORIZON_LABELS:
+            leaf = horizons.get(label)
+            if leaf is not None and leaf.get("return_pct") is None:
+                counts[label] += 1
+    return counts
+
+
+def _n_unmeasured_for(measure: str, unmeasured_by_label: dict[str, int]) -> int:
+    """``0`` for the session-level trio (never unmeasurable); otherwise the SAME count its own
+    horizon label's return key and its two mdd siblings all share -- never independently
+    recomputed per measure key (TC-2)."""
+    label = _measure_horizon_label(measure)
+    return unmeasured_by_label[label] if label is not None else 0
+
+
 def _fold_cells(default_projections: list[dict]) -> list[dict]:
     """The FULL declared cross product of ``PLAYBOOK_SETUPS`` x sides x
     ``PLAYBOOK_SIGNAL_MEASURES`` -- every cell served, never a sparse "whatever fired" set (see the
@@ -298,29 +367,60 @@ def _fold_cells(default_projections: list[dict]) -> list[dict]:
     the ENTIRE truncation-exclusion/grouping-by-measure-key job; this function only pools the raw
     per-file event lists across every default-signature file first, so a signal recorded in one
     session-date's file and a signal recorded in another's pool into the SAME cell exactly as if
-    they had been measured in one walk."""
+    they had been measured in one walk.
+
+    ``n_unmeasured`` and ``n_sessions`` (J-11) are each computed ONCE per ``(setup_id, side)`` pool
+    -- not independently per measure -- then applied identically to every one of that pool's
+    ``PLAYBOOK_SIGNAL_MEASURES`` cells: ``n_unmeasured`` shares one count per horizon LABEL across a
+    return key and its two mdd siblings (``_n_unmeasured_for``), and ``n_sessions`` counts distinct
+    recorded dates behind the WHOLE pool of raw signal events, not behind any one measure's own
+    filtered sub-pool (a session contributed ``>= 1`` signal, full stop -- which horizons that
+    signal happened to measure at is a separate, per-measure fact already carried by ``n``/
+    ``n_truncated``/``n_unmeasured``)."""
     cells: list[dict] = []
     for setup_id in PLAYBOOK_SETUPS:
         for side in _SIDES:
             pool_key = f"{setup_id}:{side}"
             signal_events: list[dict] = []
             baseline_events: list[dict] = []
+            signal_dates: set[str] = set()
+            baseline_dates: set[str] = set()
             for projection in default_projections:
-                signal_events.extend(projection["signal_events"].get(pool_key, []))
-                baseline_events.extend(projection["baseline_events"].get(pool_key, []))
+                pool_signals = projection["signal_events"].get(pool_key, [])
+                pool_baseline = projection["baseline_events"].get(pool_key, [])
+                signal_events.extend(pool_signals)
+                baseline_events.extend(pool_baseline)
+                if pool_signals:
+                    signal_dates.add(projection["session_date"])
+                if pool_baseline:
+                    baseline_dates.add(projection["session_date"])
             signal_pools = _collect_measures(signal_events)
             baseline_pools = _collect_measures(baseline_events)
+            signal_unmeasured = _n_unmeasured_by_label(signal_events)
+            baseline_unmeasured = _n_unmeasured_by_label(baseline_events)
+            n_sessions_signal = len(signal_dates)
+            n_sessions_baseline = len(baseline_dates)
             for measure in PLAYBOOK_SIGNAL_MEASURES:
                 signal_values, n_truncated = signal_pools[measure]
-                baseline_values, _baseline_truncated = baseline_pools[measure]
-                signal_block = _signal_cell(signal_values, n_truncated)
+                baseline_values, baseline_truncated = baseline_pools[measure]
+                signal_block = _signal_cell(
+                    signal_values,
+                    n_truncated,
+                    _n_unmeasured_for(measure, signal_unmeasured),
+                    n_sessions_signal,
+                )
                 cells.append(
                     {
                         "setup_id": setup_id,
                         "side": side,
                         "measure": measure,
                         "signal": signal_block,
-                        "baseline": _baseline_cell(baseline_values),
+                        "baseline": _baseline_cell(
+                            baseline_values,
+                            baseline_truncated,
+                            _n_unmeasured_for(measure, baseline_unmeasured),
+                            n_sessions_baseline,
+                        ),
                         "below_min_n": signal_block["n"] < PLAYBOOK_MIN_N_DISCLOSURE,
                     }
                 )
@@ -356,27 +456,35 @@ def _fold_invalidation_breached(default_projections: list[dict]) -> list[dict]:
     return entries
 
 
+def _signature_basis(projections: list[dict]) -> dict:
+    """The ``dates``/``n_records``/``created_span`` ONE signature's own recorded projections
+    disclose -- extracted so ``_fold_other_signatures`` (below) and ``fold_evidence``'s new
+    payload-level ``basis`` block (J-11) both call the SAME summarizer instead of each growing its
+    own copy. ``dates`` deduplicated and sorted (a signature can record at most ONE file per date --
+    ``PlaybookStore``'s own 2-pin key refuses a duplicate -- so dedup here is defensive, not
+    load-bearing); ``n_records`` is the plain count of ``projections`` (by that same 2-pin-key
+    invariant, always equal to ``len(dates)`` for a fixed signature -- served as its own field
+    anyway so a reader is never asked to derive it). ``created_span`` is ``None`` iff ``projections``
+    is empty, matching ``inspect_signature``'s own ``min``/``max`` convention byte-for-byte (both
+    read the identical ``session_date``/``recorded_at`` fields off the identical records -- one via
+    a projection, the other via a fresh ``store.get`` -- so the two are provably the same computation
+    under two different callers, not two independent ones; TC-5)."""
+    dates = sorted({p["session_date"] for p in projections})
+    recorded_ats = sorted(p["recorded_at"] for p in projections)
+    created_span = {"from": recorded_ats[0], "to": recorded_ats[-1]} if recorded_ats else None
+    return {"dates": dates, "n_records": len(projections), "created_span": created_span}
+
+
 def _fold_other_signatures(other_projections: list[dict]) -> list[dict]:
-    """Every NON-default signature present, its own ``dates``/``created_span`` only -- listed,
-    never pooled (the hard anti-goal: "the evidence pools one signature"). Signatures sorted for a
-    deterministic served order; ``dates`` deduplicated and sorted (a signature can record at most
-    ONE file per date -- ``PlaybookStore``'s own 2-pin key refuses a duplicate -- so dedup here is
-    defensive, not load-bearing)."""
+    """Every NON-default signature present, its own ``dates``/``n_records``/``created_span`` only --
+    listed, never pooled (the hard anti-goal: "the evidence pools one signature"). Signatures sorted
+    for a deterministic served order."""
     by_signature: dict[str, list[dict]] = {}
     for projection in other_projections:
         by_signature.setdefault(projection["playbook_input_signature"], []).append(projection)
     result: list[dict] = []
     for signature in sorted(by_signature):
-        entries = by_signature[signature]
-        dates = sorted({entry["session_date"] for entry in entries})
-        recorded_ats = sorted(entry["recorded_at"] for entry in entries)
-        result.append(
-            {
-                "signature": signature,
-                "dates": dates,
-                "created_span": {"from": recorded_ats[0], "to": recorded_ats[-1]},
-            }
-        )
+        result.append({"signature": signature, **_signature_basis(by_signature[signature])})
     return result
 
 
@@ -408,6 +516,7 @@ def fold_evidence(
         "cells": _fold_cells(default_projections),
         "invalidation_breached": _fold_invalidation_breached(default_projections),
         "other_signatures": _fold_other_signatures(other_projections),
+        "basis": _signature_basis(default_projections),
         "parameters": playbook_parameters(),
         "register": EVIDENCE_REGISTER,
     }
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 32ff5f0..8bbbbce 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -1329,9 +1329,11 @@ def get_desk_playbook_evidence(
     ``?id=`` convention):
 
       * ``signature`` absent: the full pooled fold at the CURRENT default signature —
-        ``{"signature", "cells", "invalidation_breached", "other_signatures", "parameters",
-        "register"}``. Only the default signature's own recorded signals ever enter ``cells``; a
-        cell with zero recorded signals is still served (``n: 0``), never omitted.
+        ``{"signature", "cells", "invalidation_breached", "other_signatures", "basis",
+        "parameters", "register"}`` (``basis``: J-11's own ``{dates, n_records, created_span}``
+        disclosure for the pooled/default signature). Only the default signature's own recorded
+        signals ever enter ``cells``; a cell with zero recorded signals is still served (``n: 0``),
+        never omitted.
       * ``signature=<value>``: that ONE named signature's own ``{"signature", "dates",
         "created_span"}`` — inspects any recorded signature (default or not) WITHOUT pooling it
         into any cell (T-7/the "one signature" anti-goal — this branch never even resolves the
diff --git a/apps/backend/tests/test_desk_playbook_backscan.py b/apps/backend/tests/test_desk_playbook_backscan.py
index edeeac7..410a40a 100644
--- a/apps/backend/tests/test_desk_playbook_backscan.py
+++ b/apps/backend/tests/test_desk_playbook_backscan.py
@@ -649,15 +649,31 @@ def test_resolve_desk_playbook_backscan_log_dir_defaults_to_a_universe_sibling(m
 
 
 # --- TC-13: the positive scoping guard ----------------------------------------------------------------
+# goal-playbook-iter-12 (J-11 passenger, TC-15): extended from four to five vars --
+# TAPEOLOGY_BAR_INDEX_DB joins the other four. The three tests below are widened so "all env vars
+# unset"/"all env vars properly scoped" keep meaning what they say; a NEW dedicated negative
+# counter-test (below) isolates the fifth var alone, and a source-scan test pins that this guard
+# still has no caller under desk_routes.py (never wired into a live route).
+
+_ALL_SCOPED_ENV_VARS = (
+    "TAPEOLOGY_DESK_PLAYBOOK_DIR",
+    "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR",
+    "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR",
+    "TAPEOLOGY_DESK_UNIVERSE_DIR",
+    "TAPEOLOGY_BAR_INDEX_DB",
+)
+
+
+def _set_all_scoped(tmp_path, monkeypatch) -> None:
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR", str(tmp_path / "playbook_backscan_runs"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(tmp_path / "bar_index.db"))
 
 
-def test_tc13_assert_scoped_raises_when_all_four_env_vars_are_unset(tmp_path, monkeypatch):
-    for name in (
-        "TAPEOLOGY_DESK_PLAYBOOK_DIR",
-        "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR",
-        "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR",
-        "TAPEOLOGY_DESK_UNIVERSE_DIR",
-    ):
+def test_tc13_assert_scoped_raises_when_all_five_env_vars_are_unset(tmp_path, monkeypatch):
+    for name in _ALL_SCOPED_ENV_VARS:
         monkeypatch.delenv(name, raising=False)
 
     with pytest.raises(PlaybookNotScopedError):
@@ -669,15 +685,44 @@ def test_tc13_assert_scoped_raises_when_a_var_points_at_a_dot_data_store(tmp_pat
     monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
     monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR", str(tmp_path / "playbook_backscan_runs"))
     monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", "/some/repo/apps/backend/.data/desk_universe")
+    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(tmp_path / "bar_index.db"))
 
     with pytest.raises(PlaybookNotScopedError):
         _assert_scoped(tmp_path)
 
 
-def test_tc13_assert_scoped_passes_when_all_four_are_properly_scoped(tmp_path, monkeypatch):
-    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
-    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", str(tmp_path / "playbook_runs"))
-    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR", str(tmp_path / "playbook_backscan_runs"))
-    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+def test_tc13_assert_scoped_passes_when_all_five_are_properly_scoped(tmp_path, monkeypatch):
+    _set_all_scoped(tmp_path, monkeypatch)
 
     _assert_scoped(tmp_path)  # does not raise
+
+
+def test_tc15_assert_scoped_raises_when_only_the_fifth_var_is_unset_and_names_it(tmp_path, monkeypatch):
+    """TC-15's own negative counter-test: the other four properly scoped, ONLY
+    ``TAPEOLOGY_BAR_INDEX_DB`` unset -- still refused, and the raised message names that exact var
+    (not a generic "something is wrong")."""
+    _set_all_scoped(tmp_path, monkeypatch)
+    monkeypatch.delenv("TAPEOLOGY_BAR_INDEX_DB", raising=False)
+
+    with pytest.raises(PlaybookNotScopedError) as excinfo:
+        _assert_scoped(tmp_path)
+    assert "TAPEOLOGY_BAR_INDEX_DB" in str(excinfo.value)
+    # And it is the ONLY problem named -- the other four were genuinely fine.
+    for name in _ALL_SCOPED_ENV_VARS[:-1]:
+        assert f"{name} is unset" not in str(excinfo.value)
+        assert f"{name}=" not in str(excinfo.value)
+
+
+def test_tc15_assert_scoped_has_no_caller_under_desk_routes():
+    """TC-15: a source-scan confirms ``_assert_scoped`` is still never wired into a live HTTP route
+    -- it stays a test/browser-QA-rig-only positive guard, exactly as its own docstring claims."""
+    import pathlib
+
+    import app.research.desk_routes as desk_routes_module
+
+    routes_source = pathlib.Path(desk_routes_module.__file__).read_text()
+    assert "_assert_scoped" not in routes_source, (
+        "desk_routes.py must never call _assert_scoped -- an operator's REAL compute legitimately "
+        "runs with none of the five scoping env vars set, and wiring the guard into a route would "
+        "wrongly refuse every genuine production compute"
+    )
diff --git a/apps/backend/tests/test_desk_playbook_evidence.py b/apps/backend/tests/test_desk_playbook_evidence.py
index 92eeb8e..34f616d 100644
--- a/apps/backend/tests/test_desk_playbook_evidence.py
+++ b/apps/backend/tests/test_desk_playbook_evidence.py
@@ -66,6 +66,19 @@ def _truncated_forward(entry: float, exit_price: float, *, side: str = "long") -
     return _forward(entry, exit_price, side=side, n_bars=5)
 
 
+def _unmeasurable_at_1h_forward(entry: float, *, side: str = "long", n_bars: int = 15) -> dict:
+    """A REAL ``_measure_from`` leaf whose ``horizons["1h"]`` is the null shape
+    (``return_pct: None``) -- built on a touch series (``tf_minutes=7``) that does not evenly
+    divide 60 (nor 1/5/240: every horizon is finer/coarser than a 7m series, so this fixture reads
+    unmeasurable at EVERY horizon, which is fine -- no test below asserts anything about this
+    event's OTHER horizons). The exact bar prices are irrelevant: ``_measure_from`` decides the
+    null shape from ``minutes % tf_minutes`` alone, before reading a single bar (goal-playbook-
+    iter-12, J-11 TC-1/TC-2/TC-3/TC-8's "a signal unmeasurable at 1h" fixture)."""
+    sign = 1.0 if side == "long" else -1.0
+    bars = [_bar("SYN", E_OPEN + i * 300.0, entry) for i in range(n_bars)]
+    return _measure_from(bars, 0, entry, "level", 7, sign)
+
+
 def _signal(setup_id: str, side: str, forward: dict, *, breached: dict | None = None) -> dict:
     return {
         "symbol": "SYN",
@@ -223,18 +236,27 @@ def test_tc3_below_min_n_cell_still_serves_populated_numbers(store, bar_store, m
 
 def test_a_cell_with_zero_recorded_signals_is_served_as_n0_not_omitted(store, bar_store):
     """Error case: every (setup_id, side, measure) combination is present in ``cells`` even with an
-    entirely empty store -- the full declared cross product, never a sparse/omitted set."""
+    entirely empty store -- the full declared cross product, never a sparse/omitted set.
+
+    TC-7 (goal-playbook-iter-12, J-11): extended -- an entirely empty store also serves the
+    payload-level ``basis`` as ``{"dates": [], "n_records": 0, "created_span": None}``, and every
+    cell's five new fields (``signal.n_unmeasured``/``n_sessions``,
+    ``baseline.n_truncated``/``n_unmeasured``/``n_sessions``) read ``0`` -- present, never omitted,
+    mirroring the pre-existing zero-signals precedent this test already pins."""
     body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
     assert len(body["cells"]) == len(PLAYBOOK_SETUPS) * 2 * len(DESK_FORWARD_MEASURE_KEYS)
+    assert body["basis"] == {"dates": [], "n_records": 0, "created_span": None}
     cell = next(
         c for c in body["cells"]
         if c["setup_id"] == "open_high_break" and c["side"] == "long" and c["measure"] == "1h"
     )
     assert cell["signal"] == {
-        "n": 0, "n_truncated": 0, "median_pct": None, "p25_pct": None, "p75_pct": None, "mean_pct": None,
+        "n": 0, "n_truncated": 0, "n_unmeasured": 0, "n_sessions": 0,
+        "median_pct": None, "p25_pct": None, "p75_pct": None, "mean_pct": None,
     }
     assert cell["baseline"] == {
-        "n_baseline": 0, "median_pct": None, "p25_pct": None, "p75_pct": None, "mean_pct": None,
+        "n_baseline": 0, "n_truncated": 0, "n_unmeasured": 0, "n_sessions": 0,
+        "median_pct": None, "p25_pct": None, "p75_pct": None, "mean_pct": None,
     }
     assert cell["below_min_n"] is True
 
@@ -464,6 +486,19 @@ def test_tc7_evidence_register_carries_no_forbidden_language(store, bar_store):
     body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
     assert body["register"] == EVIDENCE_REGISTER
 
+    # TC-11 (goal-playbook-iter-12, J-11): the updated exclusion-disclosure sentence textually names
+    # the unmeasurable class, the baseline's own truncated/unmeasured counts, and the basis
+    # disclosure -- not just "some new words somewhere", but the SAME three things J-11 requires.
+    assert "unmeasurable" in low
+    assert "n_unmeasured" in low and "n_truncated" in low
+    baseline_idx = low.index("baseline side")
+    nearby = low[baseline_idx : baseline_idx + 80]
+    assert "n_truncated" in nearby and "n_unmeasured" in nearby, (
+        "the baseline's own truncated/unmeasured counts must be named TOGETHER with the baseline "
+        "side, not merely present somewhere else in the sentence"
+    )
+    assert "basis" in low
+
 
 # --- structural guard: the evidence cache class exposes no update/delete method ----------------------
 
@@ -500,6 +535,9 @@ def test_route_serves_an_honest_empty_body_before_any_record_exists(client):
     assert body["other_signatures"] == []
     assert body["register"] == EVIDENCE_REGISTER
     assert len(body["cells"]) == len(PLAYBOOK_SETUPS) * 2 * len(DESK_FORWARD_MEASURE_KEYS)
+    # goal-playbook-iter-12 (J-11): the basis block over the live HTTP route, not just fold_evidence
+    # called directly.
+    assert body["basis"] == {"dates": [], "n_records": 0, "created_span": None}
 
 
 def test_route_signature_query_param_inspects_without_pooling(client):
@@ -512,3 +550,340 @@ def test_route_signature_query_param_inspects_without_pooling(client):
         "signature": SIG_OLDER, "dates": ["2026-06-10"],
         "created_span": {"from": body["created_span"]["from"], "to": body["created_span"]["to"]},
     }
+
+
+# =====================================================================================================
+# goal-playbook-iter-12 (J-11): "every evidence cell states the basis of its own n" -- five new
+# per-cell fields (signal.n_unmeasured/n_sessions, baseline.n_truncated/n_unmeasured/n_sessions) plus
+# a payload-level basis block and other_signatures[].n_records. Test-first contract: TC-1 through
+# TC-9 in docs/phases/goal-playbook-iter-12.md (this iteration's OWN numbering -- distinct from, and
+# not to be confused with, the file's pre-existing TC-1..TC-7 above, which TC-9 below re-verifies
+# stayed numerically unchanged).
+# =====================================================================================================
+
+
+# --- TC-1: unmeasured at "1m", measured at "1h" -------------------------------------------------------
+
+
+def test_iter12_tc1_unmeasured_at_1m_zero_unmeasured_at_1h(store, bar_store, monkeypatch):
+    """TC-1: a 5m-basis signal's own "1m" cell serves n=0/n_truncated=0/n_unmeasured=1 (the one
+    recorded signal, unmeasurable there -- "finer than the 5m touch series"), while the SAME
+    signal's own "1h" cell (same pool) serves n_unmeasured=0 -- 1h IS measurable on a 5m-basis
+    session. A second, different-pool signal (whose own 1h leaf is also measurable) proves no
+    cross-pool leakage into either assertion, the file's own established non-leakage precedent."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [
+            _signal("jbe", "long", _forward(100.0, 102.0)),
+            _signal("dbi", "short", _forward(100.0, 99.0, side="short")),
+        ],
+    )
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+
+    def _jbe_cell(measure):
+        return next(
+            c for c in body["cells"]
+            if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == measure
+        )
+
+    cell_1m = _jbe_cell("1m")
+    assert cell_1m["signal"]["n"] == 0
+    assert cell_1m["signal"]["n_truncated"] == 0
+    assert cell_1m["signal"]["n_unmeasured"] == 1
+
+    cell_1h = _jbe_cell("1h")
+    assert cell_1h["signal"]["n"] == 1
+    assert cell_1h["signal"]["n_unmeasured"] == 0
+
+    # No cross-pool leakage: dbi/short's own "1h" cell is unaffected by jbe/long's signal.
+    dbi_1h = next(
+        c for c in body["cells"] if c["setup_id"] == "dbi" and c["side"] == "short" and c["measure"] == "1h"
+    )
+    assert dbi_1h["signal"]["n"] == 1
+    assert dbi_1h["signal"]["n_unmeasured"] == 0
+
+
+# --- TC-2: n + n_truncated + n_unmeasured == pool total; mdd siblings share the count; session-level
+# measures are never unmeasurable ------------------------------------------------------------------
+
+
+def test_iter12_tc2_signal_exclusion_counts_sum_to_the_pool_and_mdd_siblings_match(store, bar_store, monkeypatch):
+    """TC-2: three pooled (jbe, long) signals -- one untruncated, one truncated, one unmeasurable at
+    "1h" -- so the "1h" cell's n + n_truncated + n_unmeasured == 3 exactly; its mdd_long_1h/
+    mdd_short_1h siblings serve the IDENTICAL three counts (not independently recomputed); and the
+    to_close/mdd_long/mdd_short (session-level) cells for the SAME pool serve n_unmeasured == 0
+    regardless (the session end is never unmeasurable)."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    untruncated = _forward(100.0, 102.0)
+    truncated = _truncated_forward(100.0, 103.0)
+    unmeasurable = _unmeasurable_at_1h_forward(100.0)
+    assert untruncated["horizons"]["1h"]["return_pct"] is not None
+    assert untruncated["horizons"]["1h"]["truncated"] is False
+    assert truncated["horizons"]["1h"]["return_pct"] is not None
+    assert truncated["horizons"]["1h"]["truncated"] is True
+    assert unmeasurable["horizons"]["1h"]["return_pct"] is None
+
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [
+            _signal("jbe", "long", untruncated),
+            _signal("jbe", "long", truncated),
+            _signal("jbe", "long", unmeasurable),
+        ],
+    )
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+
+    def _cell(measure):
+        return next(
+            c for c in body["cells"]
+            if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == measure
+        )
+
+    hour = _cell("1h")["signal"]
+    assert (hour["n"], hour["n_truncated"], hour["n_unmeasured"]) == (1, 1, 1)
+    assert hour["n"] + hour["n_truncated"] + hour["n_unmeasured"] == 3
+
+    for sibling in ("mdd_long_1h", "mdd_short_1h"):
+        sib = _cell(sibling)["signal"]
+        assert (sib["n"], sib["n_truncated"], sib["n_unmeasured"]) == (
+            hour["n"], hour["n_truncated"], hour["n_unmeasured"],
+        ), f"{sibling} must serve the IDENTICAL three counts as its own return sibling, not recompute them"
+
+    for session_level in ("to_close", "mdd_long", "mdd_short"):
+        sess = _cell(session_level)["signal"]
+        assert sess["n_unmeasured"] == 0
+        assert sess["n"] == 3  # every event pools at the session-end trio regardless of horizon
+
+
+# --- TC-3: baseline truncated/unmeasured are wired, not omitted -------------------------------------
+
+
+def test_iter12_tc3_baseline_truncated_and_unmeasured_are_wired_not_omitted(store, bar_store, monkeypatch):
+    """TC-3: three baseline_anchors planted for one pool key -- one untruncated, one truncated, one
+    unmeasurable at "1h" -- so baseline.n_truncated and baseline.n_unmeasured are BOTH wired (never
+    both 0 by omission) and n_baseline + n_truncated + n_unmeasured == 3 for the "1h" cell."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [_signal("jbe", "long", _forward(100.0, 102.0))],
+        baseline_anchors={
+            "jbe:long": [
+                _forward(100.0, 101.0),
+                _truncated_forward(100.0, 101.5),
+                _unmeasurable_at_1h_forward(100.0),
+            ]
+        },
+    )
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    cell = next(
+        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    baseline = cell["baseline"]
+    assert baseline["n_truncated"] == 1
+    assert baseline["n_unmeasured"] == 1
+    assert baseline["n_baseline"] + baseline["n_truncated"] + baseline["n_unmeasured"] == 3
+
+
+# --- TC-4: n_sessions counts distinct CONTRIBUTING dates, shared across every measure in the pool ---
+
+
+def test_iter12_tc4_n_sessions_counts_distinct_contributing_dates_only(store, bar_store, monkeypatch):
+    """TC-4: four records at four distinct session_dates, three of which each contribute exactly
+    one (jbe, long) signal and the fourth contributing only an OTHER setup -- the (jbe, long) cell's
+    signal.n_sessions == 3 (not 4), and the SAME count is shared by every measure in that pool (not
+    independently recomputed per measure)."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(store, "2026-06-22", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 102.0))])
+    _record(store, "2026-06-23", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 103.0))])
+    _record(store, "2026-06-24", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 104.0))])
+    _record(store, "2026-06-25", SIG_DEFAULT, [_signal("dbi", "short", _forward(100.0, 98.0, side="short"))])
+
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    cell_1h = next(
+        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    assert cell_1h["signal"]["n"] == 3
+    assert cell_1h["signal"]["n_sessions"] == 3
+
+    cell_1m = next(
+        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1m"
+    )
+    assert cell_1m["signal"]["n_sessions"] == 3  # shared across the whole pool, not re-derived per measure
+
+    dbi_cell = next(
+        c for c in body["cells"] if c["setup_id"] == "dbi" and c["side"] == "short" and c["measure"] == "1h"
+    )
+    assert dbi_cell["signal"]["n_sessions"] == 1
+
+
+# --- TC-5: basis is byte-identical to inspect_signature for the SAME signature ----------------------
+
+
+def test_iter12_tc5_basis_matches_inspect_signature_for_the_same_signature(store, bar_store, monkeypatch):
+    """TC-5: three records at the default signature across three distinct dates --
+    payload["basis"] == {"dates": <the 3 dates, sorted>, "n_records": 3, "created_span": {...}}, and
+    basis["dates"]/basis["created_span"] are byte-identical to
+    inspect_signature(store, that_same_signature)'s own dates/created_span -- one implementation,
+    two views."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(store, "2026-06-22", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 102.0))])
+    _record(store, "2026-06-23", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 103.0))])
+    _record(store, "2026-06-24", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 104.0))])
+
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    assert body["basis"]["dates"] == ["2026-06-22", "2026-06-23", "2026-06-24"]
+    assert body["basis"]["n_records"] == 3
+    assert body["basis"]["created_span"]["from"] <= body["basis"]["created_span"]["to"]
+
+    inspected = inspect_signature(store, SIG_DEFAULT)
+    assert body["basis"]["dates"] == inspected["dates"]
+    assert body["basis"]["created_span"] == inspected["created_span"]
+
+
+# --- TC-6: other_signatures[] also serves n_records --------------------------------------------------
+
+
+def test_iter12_tc6_other_signatures_entry_also_serves_n_records(store, bar_store, monkeypatch):
+    """TC-6: one record at an OLDER, non-default signature -- its other_signatures entry now also
+    serves n_records: 1 alongside its existing signature/dates/created_span, unchanged otherwise."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(store, "2026-06-10", SIG_OLDER, [_signal("jbe", "long", _forward(100.0, 999.0))])
+
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    assert len(body["other_signatures"]) == 1
+    other = body["other_signatures"][0]
+    assert other["signature"] == SIG_OLDER
+    assert other["dates"] == ["2026-06-10"]
+    assert other["n_records"] == 1
+    assert other["created_span"]["from"] <= other["created_span"]["to"]
+
+
+# --- TC-7 (the entirely-empty-store case) is covered above: see the extended
+# test_a_cell_with_zero_recorded_signals_is_served_as_n0_not_omitted and
+# test_route_serves_an_honest_empty_body_before_any_record_exists.
+
+
+# --- TC-8: cache cold/warm/rebuilt stay byte-identical WITH the seven new fields non-trivially set --
+
+
+def test_iter12_tc8_cache_cold_warm_and_rebuilt_stay_byte_identical_with_new_fields(
+    store, bar_store, tmp_path, monkeypatch
+):
+    """TC-8: extends the file's own pre-existing TC-2 (cold/warm)/TC-6 (deleted-then-rebuilt)
+    byte-identity precedent to explicitly exercise the seven new J-11 fields -- a pool spanning two
+    session dates with a truncated signal, an unmeasurable-at-1h signal, and an unmeasurable
+    baseline anchor gives every new count a genuinely NON-ZERO value first (so the byte-identity
+    check below is not vacuously true at 0 everywhere), then proves cold == warm == rebuilt-after-
+    delete for the FULL enriched body."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [_signal("jbe", "long", _forward(100.0, 102.0)), _signal("jbe", "long", _truncated_forward(100.0, 103.0))],
+        baseline_anchors={"jbe:long": [_unmeasurable_at_1h_forward(100.0)]},
+    )
+    _record(
+        store, "2026-06-23", SIG_DEFAULT,
+        [_signal("jbe", "long", _unmeasurable_at_1h_forward(100.0))],
+    )
+
+    db_path = tmp_path / "evidence_cache.db"
+    cache1 = PlaybookEvidenceCache(str(db_path))
+    cold = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache1)
+    warm = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache1)
+
+    db_path.unlink()  # the cache DB is gone; nothing here touches the playbook store itself
+    cache2 = PlaybookEvidenceCache(str(db_path))  # a fresh, empty DB -- every file re-verified
+    rebuilt = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache2)
+
+    cell = next(
+        c for c in cold["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    assert cell["signal"]["n_truncated"] > 0
+    assert cell["signal"]["n_unmeasured"] > 0
+    assert cell["signal"]["n_sessions"] > 0
+    assert cell["baseline"]["n_unmeasured"] > 0
+    assert cold["basis"]["n_records"] == 2
+
+    assert json.dumps(cold, sort_keys=False) == json.dumps(warm, sort_keys=False)
+    assert json.dumps(cold, sort_keys=False) == json.dumps(rebuilt, sort_keys=False)
+
+
+# --- TC-9: every PRE-EXISTING served number is numerically unchanged by this iteration's diff -------
+
+
+def test_iter12_tc9_pre_existing_numbers_are_unchanged_by_the_new_fields(store, bar_store, monkeypatch):
+    """TC-9: replays the file's own pre-existing TC-1 fixture (three jbe/long records, 1h returns
+    2.0/4.0/6.0, hand-verified median 4.0/mean 4.0/p25 3.0/p75 5.0) after this iteration's diff --
+    every PRE-EXISTING served number (n, n_truncated, median_pct, p25_pct, p75_pct, mean_pct,
+    below_min_n) is numerically unchanged, and the invalidation-breach counts (a fold this
+    iteration's diff never touches) still sum correctly over the SAME three signals."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [
+            _signal("jbe", "long", _forward(100.0, 102.0)),
+            _signal("dbi", "short", _forward(100.0, 99.0, side="short")),
+            _signal("capitulation", "long", _forward(100.0, 101.0)),
+        ],
+    )
+    _record(
+        store, "2026-06-23", SIG_DEFAULT,
+        [
+            _signal("jbe", "long", _forward(100.0, 104.0)),
+            _signal("range_trade", "long", _forward(100.0, 100.5)),
+        ],
+    )
+    _record(
+        store, "2026-06-24", SIG_DEFAULT,
+        [_signal("jbe", "long", _forward(100.0, 106.0))],
... [diff_bound] apps/backend/tests/test_desk_playbook_evidence.py: 26 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index bc59dca..a6e35b8 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -185,6 +185,13 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
 # the invalidation-breach line renders `breach.breached_count`/`breach.total_count` verbatim --
 # every one of these is a straight pass-through of `GET /research/desk/playbook/evidence`, never a
 # client-recomputed spread, ratio, or rate.
+# goal-playbook-iter-12 (J-11): extended AGAIN for the Playbook Evidence section's five NEW served
+# exclusion counts -- `cell.signal.*` gains `n_unmeasured`/`n_sessions` and `cell.baseline.*` gains
+# `n_truncated`/`n_unmeasured`/`n_sessions` (already-declared bindings widened, never a new one),
+# plus the new basis line's own `basis.n_records` (`PlaybookEvidenceBasisLine`'s own prop, the
+# `plan.*`/`compute.*`/`outcomes.*` top-level-binding precedent). No client-side arithmetic on any
+# of these is ever legitimate: they are exclusion/record COUNTS, not prices, but this panel's own
+# IN SCOPE contract is "no client-side arithmetic on served numerics" full stop, the J-07 precedent.
 _PRICE_ARITHMETIC_FIELDS = (
     r"row\.(?:distance_bps|price_low|price_high|reference_close"
     r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
@@ -203,9 +210,11 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|plan\.(?:total|missing)"
     r"|compute\.(?:planned_total|completed)"
     r"|outcomes\.(?:reused|recorded|refused_non_session|failed)"
-    r"|cell\.signal\.(?:n|n_truncated|median_pct|p25_pct|p75_pct|mean_pct)"
-    r"|cell\.baseline\.(?:n_baseline|median_pct|p25_pct|p75_pct|mean_pct)"
+    r"|cell\.signal\.(?:n|n_truncated|n_unmeasured|n_sessions|median_pct|p25_pct|p75_pct|mean_pct)"
+    r"|cell\.baseline\.(?:n_baseline|n_truncated|n_unmeasured|n_sessions|median_pct|p25_pct|p75_pct"
+    r"|mean_pct)"
     r"|breach\.(?:breached_count|total_count)"
+    r"|basis\.(?:n_records)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -373,6 +382,36 @@ def test_desk_page_price_arithmetic_guard_catches_evidence_field_arithmetic():
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_rate) is not None
 
 
+def test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmetic():
+    """goal-playbook-iter-12 (J-11) counter-test: the extended guard catches arithmetic on the five
+    NEW exclusion-count bindings (`cell.signal.n_unmeasured`/`n_sessions`,
+    `cell.baseline.n_truncated`/`n_unmeasured`/`n_sessions`) and the new basis line's own
+    `basis.n_records` -- proving the widened `cell.signal.*`/`cell.baseline.*` groups and the new
+    `basis.*` group actually catch a violation, the "a lint that cannot fail proves nothing"
+    precedent applied to each new field individually."""
+    seeded_signal_unmeasured = "const measured = cell.signal.n - cell.signal.n_unmeasured;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_unmeasured) is not None
+
+    seeded_signal_sessions = "const perSession = cell.signal.n / cell.signal.n_sessions;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_sessions) is not None
+
+    seeded_baseline_truncated = "const clean = cell.baseline.n_baseline - cell.baseline.n_truncated;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_truncated) is not None
+
+    seeded_baseline_unmeasured = "const total = cell.baseline.n_baseline + cell.baseline.n_unmeasured;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_unmeasured) is not None
+
+    seeded_baseline_sessions = "const perSession = cell.baseline.n_baseline / cell.baseline.n_sessions;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_sessions) is not None
+
+    seeded_basis = "const perDate = basis.n_records / basis.dates.length;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_basis) is not None
+
+    # And the pattern does NOT over-match: the real page's own guard test below still finds zero
+    # hits, so this new coverage does not accidentally flag legitimate, non-arithmetic JSX.
+    assert _PRICE_ARITHMETIC_PATTERN.search("const label = `${basis.n_records} records`;") is None
+
+
 # goal-playbook-iter-4 audit (F1): `base_lows_ascending` is ONE served field name carrying the
 # direction-appropriate triangle check underneath (non-decreasing LOWS for `jbe`, non-increasing
 # HIGHS for `dbi` -- see `desk_playbook_detect._base_lows_ascending`). The continuation geometry
@@ -884,3 +923,97 @@ def test_desk_row_label_prefix_guard_can_fail_on_a_seeded_violation():
     # and the pin itself is non-vacuous: J-13/J-14 really do assert those literal texts today
     assert any(t.startswith("band ") for t in _golden_expected_texts("J-13.json"))
     assert any(t.startswith("opposite ") for t in _golden_expected_texts("J-14.json"))
+
+
+# --- goal-playbook-iter-12 (J-11 passenger, TC-14): the Playbook Signals date input's amber border -
+# ASOF_INPUT_CLASS's own `border-slate-700` and a plain, conditionally-appended `border-amber-500`
+# are an equal-CSS-specificity Tailwind collision (both single-class border-color utilities), so the
+# COMPILED stylesheet's own utility order silently decides the tie regardless of this class list's
+# order in the JSX -- and it is `border-slate-700` that wins live, leaving the input grey on an
+# invalid value. The fix (Tailwind's `!` important modifier) is scoped to `desk-playbook-date-input`
+# alone: `ASOF_INPUT_CLASS` itself and its other four call sites (Refresh Data From/To -- the SAME
+# collision, deliberately carried; Backscan/Deep-backfill From/To -- never had the amber affordance
+# at all) must stay byte-unchanged.
+
+
+def _asof_input_class_expr(source: str, testid: str) -> str:
+    """The `className={...}` JSX expression immediately following one
+    `data-testid="<testid>"` input -- found by a brace-walk from the FIRST `className={` after the
+    testid (this page's own consistent attribute order: data-testid precedes className on every
+    ASOF-styled input), mirroring `_extract_function`'s own walk-from-a-known-anchor style."""
+    start = source.index(f'data-testid="{testid}"')
+    class_start = source.index("className={", start)
+    open_brace = class_start + len("className=")
+    depth = 0
+    for index in range(open_brace, len(source)):
+        if source[index] == "{":
+            depth += 1
+        elif source[index] == "}":
+            depth -= 1
+            if depth == 0:
+                return source[class_start : index + 1]
+    raise AssertionError(f"{testid}'s className expression never closes")
+
+
+def test_desk_playbook_date_input_amber_border_fix_is_scoped_to_itself_only():
+    """TC-14: `desk-playbook-date-input`'s own className now forces the amber border to win on an
+    invalid value; `ASOF_INPUT_CLASS`'s own definition, the Refresh Data From/To inputs sharing the
+    IDENTICAL (still unfixed) collision, and the Backscan/Deep-backfill From/To inputs (which never
+    had the amber affordance) all stay byte-unchanged."""
+    source = _DESK_PAGE.read_text()
+
+    playbook_input_class = _asof_input_class_expr(source, "desk-playbook-date-input")
+    assert '"!border-amber-500"' in playbook_input_class, (
+        "desk-playbook-date-input's className must force the amber border with Tailwind's `!` "
+        "important modifier -- a bare `border-amber-500` loses the equal-specificity tie against "
+        "ASOF_INPUT_CLASS's own border-slate-700 and the input stays grey on an invalid value"
+    )
+
+    # ASOF_INPUT_CLASS's own definition is untouched: still carries border-slate-700, never amber.
+    class_def_start = source.index("const ASOF_INPUT_CLASS =")
+    class_def_end = source.index(";", class_def_start)
+    class_def = source[class_def_start:class_def_end]
+    assert "border-slate-700" in class_def
+    assert "amber" not in class_def
+
+    # The Refresh Data From/To inputs share the IDENTICAL, still-UNFIXED collision (carried,
+    # per this iteration's own scoping decision) -- neither gained the `!` fix.
+    unfixed_pattern = '${ASOF_INPUT_CLASS} ${dayRangeError !== null ? "border-amber-500" : ""}`'
+    assert source.count(unfixed_pattern) == 2, (
+        "the Refresh Data From/To inputs' own border collision must stay byte-unchanged and "
+        "unforced -- only desk-playbook-date-input is fixed this iteration"
+    )
+    assert "!border-amber-500" not in unfixed_pattern
+
+    # The Backscan/Deep-backfill From/To inputs never had the amber affordance at all -- still four
+    # bare `className={ASOF_INPUT_CLASS}` call sites, none of them this one.
+    assert source.count("className={ASOF_INPUT_CLASS}") == 4
+
+
+def test_desk_playbook_date_input_amber_border_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded = (
+        'data-testid="desk-playbook-date-input"\n'
+        "          value={dateInput}\n"
+        "          className={`${ASOF_INPUT_CLASS} "
+        '${validated.error !== null ? "border-amber-500" : ""}`}\n'
+    )
+    extracted = _asof_input_class_expr(seeded, "desk-playbook-date-input")
+    assert "!border-amber-500" not in extracted
+    assert "border-amber-500" in extracted  # the pre-fix shape really is present to catch
+
+
+def test_the_asof_class_expr_extractor_returns_the_right_inputs_own_expression():
+    """A counter-test for the helper itself: it must not accidentally return a DIFFERENT input's
+    className (e.g. the first one it happens to find in the file) -- each of the five ASOF-styled
+    inputs must extract its OWN expression."""
+    seeded = (
+        'data-testid="alpha"\n'
+        '          className={ASOF_INPUT_CLASS}\n'
+        'data-testid="beta"\n'
+        "          className={`${ASOF_INPUT_CLASS} "
+        '${cond ? "border-amber-500" : ""}`}\n'
+    )
+    assert _asof_input_class_expr(seeded, "alpha") == "className={ASOF_INPUT_CLASS}"
+    beta = _asof_input_class_expr(seeded, "beta")
+    assert "border-amber-500" in beta and "ASOF_INPUT_CLASS" in beta
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 2b1ce10..5ae0c2c 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -628,7 +628,8 @@ async def test_desk_playbook_evidence_tool_byte_identical_on_the_honest_empty_st
     assert rest.status_code == 200
     payload = rest.json()
     assert set(payload) == {
-        "signature", "cells", "invalidation_breached", "other_signatures", "parameters", "register",
+        "signature", "cells", "invalidation_breached", "other_signatures", "basis", "parameters",
+        "register",
     }
     assert payload["other_signatures"] == []
     assert payload["cells"], "the declared cross product must be non-empty even with no records"
@@ -734,7 +735,8 @@ async def test_desk_playbook_evidence_tool_byte_identical_on_a_populated_state(m
     assert rest.status_code == 200
     payload = rest.json()
     assert set(payload) == {
-        "signature", "cells", "invalidation_breached", "other_signatures", "parameters", "register",
+        "signature", "cells", "invalidation_breached", "other_signatures", "basis", "parameters",
+        "register",
     }
     assert len(payload["other_signatures"]) >= 2, "both arbitrary-signature records must surface here"
     assert all(cell["signal"]["n"] == 0 for cell in payload["cells"]), (
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 0ea506b..18387ee 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -64,6 +64,7 @@ import type {
   DeskPlaybookBackscanRunsListResult,
   DeskPlaybookComputeSnapshot,
   DeskPlaybookEvidence,
+  DeskPlaybookEvidenceBasis,
   DeskPlaybookEvidenceBreach,
   DeskPlaybookEvidenceCell,
   DeskPlaybookEvidenceOtherSignature,
@@ -3768,6 +3769,12 @@ function PlaybookEvidenceCellRow({ cell }: { cell: DeskPlaybookEvidenceCell }) {
         {fmt(cell.signal.n, 0)}
       </td>
       <td className={ROW_NUMERIC_CELL}>{fmt(cell.signal.n_truncated, 0)}</td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-signal-n-unmeasured">
+        {fmt(cell.signal.n_unmeasured, 0)}
+      </td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-signal-n-sessions">
+        {fmt(cell.signal.n_sessions, 0)}
+      </td>
       <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-signal-median">
         {fmt(cell.signal.median_pct)}
       </td>
@@ -3777,6 +3784,15 @@ function PlaybookEvidenceCellRow({ cell }: { cell: DeskPlaybookEvidenceCell }) {
       <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-baseline-n">
         {fmt(cell.baseline.n_baseline, 0)}
       </td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-baseline-n-truncated">
+        {fmt(cell.baseline.n_truncated, 0)}
+      </td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-baseline-n-unmeasured">
+        {fmt(cell.baseline.n_unmeasured, 0)}
+      </td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-baseline-n-sessions">
+        {fmt(cell.baseline.n_sessions, 0)}
+      </td>
       <td className={ROW_NUMERIC_CELL}>{fmt(cell.baseline.median_pct)}</td>
       <td className={ROW_NUMERIC_CELL}>{fmt(cell.baseline.p25_pct)}</td>
       <td className={ROW_NUMERIC_CELL}>{fmt(cell.baseline.p75_pct)}</td>
@@ -3800,7 +3816,7 @@ function PlaybookEvidenceCellRow({ cell }: { cell: DeskPlaybookEvidenceCell }) {
 function PlaybookEvidenceCellsTable({ cells }: { cells: DeskPlaybookEvidenceCell[] }) {
   return (
     <div className="overflow-x-auto">
-      <table data-testid="desk-evidence-cells-table" className="w-full min-w-[900px] border-collapse text-xs">
+      <table data-testid="desk-evidence-cells-table" className="w-full min-w-[1180px] border-collapse text-xs">
         <thead>
           <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-500">
             <th className="px-1.5 py-1 text-left" rowSpan={2}>
@@ -3812,10 +3828,10 @@ function PlaybookEvidenceCellsTable({ cells }: { cells: DeskPlaybookEvidenceCell
             <th className="px-1.5 py-1 text-left" rowSpan={2}>
               Measure
             </th>
-            <th className="px-1.5 py-1 text-center" colSpan={6}>
+            <th className="px-1.5 py-1 text-center" colSpan={8}>
               Signal
             </th>
-            <th className="px-1.5 py-1 text-center" colSpan={5}>
+            <th className="px-1.5 py-1 text-center" colSpan={8}>
               Baseline
             </th>
             <th className="px-1.5 py-1 text-center" rowSpan={2}>
@@ -3825,11 +3841,16 @@ function PlaybookEvidenceCellsTable({ cells }: { cells: DeskPlaybookEvidenceCell
           <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-500">
             <th className="px-1.5 py-1 text-right">n</th>
             <th className="px-1.5 py-1 text-right">trunc</th>
+            <th className="px-1.5 py-1 text-right">unmeas</th>
+            <th className="px-1.5 py-1 text-right">sess</th>
             <th className="px-1.5 py-1 text-right">median</th>
             <th className="px-1.5 py-1 text-right">p25</th>
             <th className="px-1.5 py-1 text-right">p75</th>
             <th className="px-1.5 py-1 text-right">mean</th>
             <th className="px-1.5 py-1 text-right">n</th>
+            <th className="px-1.5 py-1 text-right">trunc</th>
+            <th className="px-1.5 py-1 text-right">unmeas</th>
+            <th className="px-1.5 py-1 text-right">sess</th>
             <th className="px-1.5 py-1 text-right">median</th>
             <th className="px-1.5 py-1 text-right">p25</th>
             <th className="px-1.5 py-1 text-right">p75</th>
@@ -3903,6 +3924,21 @@ function PlaybookEvidenceOtherSignatures({ entries }: { entries: DeskPlaybookEvi
   );
 }
 
+// goal-playbook-iter-12 (J-11): the pooled/default signature's own basis disclosure -- a NEW line
+// beside the existing "Built from signature:" line above it, never replacing or altering that
+// line's own text. Own component (own `basis` binding) so the price-arithmetic guard's naming
+// convention (`basis.n_records`, matching `plan.*`/`compute.*`/`outcomes.*` before it) reaches this
+// served numeric the same way it reaches every other served block on this page.
+function PlaybookEvidenceBasisLine({ basis }: { basis: DeskPlaybookEvidenceBasis }) {
+  return (
+    <p className="mb-3 text-xs text-slate-500" data-testid="desk-evidence-basis">
+      Basis: {basis.n_records} record{basis.n_records === 1 ? "" : "s"} pooled from{" "}
+      {basis.dates.length === 0 ? "no recorded dates" : basis.dates.join(", ")}
+      {basis.created_span ? ` (created ${basis.created_span.from} .. ${basis.created_span.to})` : ""}
+    </p>
+  );
+}
+
 function PlaybookEvidenceSection({
   result,
 }: {
@@ -3926,6 +3962,7 @@ function PlaybookEvidenceSection({
       <p className="mb-1 text-xs text-slate-400" data-testid="desk-evidence-signature">
         Built from signature: <span className="font-mono text-slate-300">{data.signature}</span>
       </p>
+      <PlaybookEvidenceBasisLine basis={data.basis} />
       <p className="mb-3 text-xs text-slate-500">{data.register}</p>
       {hasAnySignal ? (
         <PlaybookEvidenceCellsTable cells={data.cells} />
@@ -5588,7 +5625,16 @@ function PlaybookSection({
             onChange={(e) => onDateInputChange(e.target.value)}
             placeholder="yyyy-MM-dd"
             aria-invalid={validated.error !== null}
-            className={`${ASOF_INPUT_CLASS} ${validated.error !== null ? "border-amber-500" : ""}`}
+            // goal-playbook-iter-12 passenger fix: ASOF_INPUT_CLASS's own `border-slate-700` and a
+            // plain `border-amber-500` are an equal-CSS-specificity Tailwind collision (both
+            // single-class border-color utilities), so the compiled stylesheet's own utility order
+            // silently decides the tie regardless of this class list's order -- and it is
+            // border-slate-700 that wins, leaving the border grey on an invalid value. Tailwind's
+            // `!` important modifier forces the error color to win, scoped to this ONE input only;
+            // ASOF_INPUT_CLASS itself and every other call site are untouched (still plain
+            // "border-amber-500", still losing the tie -- carried, not fixed, per this iteration's
+            // own scoping decision).
+            className={`${ASOF_INPUT_CLASS} ${validated.error !== null ? "!border-amber-500" : ""}`}
           />
         </label>
         {validated.error !== null && (
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 046a062..1ca38d3 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1750,9 +1750,14 @@ export interface DeskPlaybookBackscanRunsListResult {
 // evidence fold serves p25_pct/p75_pct the rail's own avg cell never had (desk_playbook_evidence.py
 // pools them with its own new quartile math -- see that module's docstring for why this is NOT a
 // second implementation of the rail).
+// goal-playbook-iter-12 (J-11): both stats shapes gain n_unmeasured/n_sessions (baseline also
+// gains n_truncated -- already computed server-side, previously discarded) -- every new count a
+// straight pass-through of GET /research/desk/playbook/evidence's enriched body, no client math.
 export interface DeskPlaybookEvidenceCellStats {
   n: number;
   n_truncated: number;
+  n_unmeasured: number;
+  n_sessions: number;
   median_pct: number | null;
   p25_pct: number | null;
   p75_pct: number | null;
@@ -1761,6 +1766,9 @@ export interface DeskPlaybookEvidenceCellStats {
 
 export interface DeskPlaybookEvidenceBaselineStats {
   n_baseline: number;
+  n_truncated: number;
+  n_unmeasured: number;
+  n_sessions: number;
   median_pct: number | null;
   p25_pct: number | null;
   p75_pct: number | null;
@@ -1787,14 +1795,26 @@ export interface DeskPlaybookEvidenceBreach {
 export interface DeskPlaybookEvidenceOtherSignature {
   signature: string;
   dates: string[];
+  n_records: number;
   created_span: { from: string; to: string };
 }
 
+// goal-playbook-iter-12 (J-11): the pooled/default signature's OWN basis disclosure -- built by the
+// same per-signature summarizer `other_signatures[]` above already uses. `created_span` is `null`
+// iff `n_records` is `0` (an entirely empty store) -- the ONE case `other_signatures[]` entries
+// never hit (a signature only appears there once it has recorded >= 1 file).
+export interface DeskPlaybookEvidenceBasis {
+  dates: string[];
+  n_records: number;
+  created_span: { from: string; to: string } | null;
+}
+
 export interface DeskPlaybookEvidence {
   signature: string;
   cells: DeskPlaybookEvidenceCell[];
   invalidation_breached: DeskPlaybookEvidenceBreach[];
   other_signatures: DeskPlaybookEvidenceOtherSignature[];
+  basis: DeskPlaybookEvidenceBasis;
   parameters: DeskPlaybookParameters;
   register: string;
 }
```
