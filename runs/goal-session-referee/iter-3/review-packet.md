# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/tests/test_referee_evidence.py b/apps/backend/tests/test_referee_evidence.py
index 8d5f20e..1231577 100644
--- a/apps/backend/tests/test_referee_evidence.py
+++ b/apps/backend/tests/test_referee_evidence.py
@@ -24,15 +24,23 @@ from app.providers.base import Side, TradeEvent
 from app.research import desk_playbook as desk_playbook_module
 from app.research import referee_evidence as referee_evidence_module
 from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
-from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
+from app.research.desk_playbook import (
+    PLAYBOOK_REGISTER,
+    PlaybookStore,
+    playbook_parameters,
+    resolve_desk_playbook_dir,
+)
 from app.research.desk_routes import get_playbook_store
 from app.research.referee_evidence import (
     REFEREE_FORMING_BAR_BASIS_CAVEAT,
+    REFEREE_SESSION_COMPLETE_ET,
     REFEREE_TICK_GATE_SYMBOL_DAYS,
     RefereeObservationCache,
+    _signal_reaches_session_complete,
     _tick_gate_state,
     current_playbook_detector_basis,
     playbook_observations,
+    resolve_referee_obs_cache_db_path,
     strategy_observations,
 )
 from app.research.routes import ResearchRegistry, get_dataset_store, set_registry
@@ -741,3 +749,100 @@ def test_adapters_write_nothing_to_any_pre_existing_store(client):
 
     assert after == before
     assert after_journal == before_journal
+
+
+# === goal-referee-iter-3 carried rider 1 -- TC-20: _signal_reaches_session_complete ==================
+#
+# Zero assertions existed for this function before this iteration (a gap-blind estimate J-06's
+# confirmatory-eligibility fold will lean on). ``REFEREE_SESSION_COMPLETE_ET`` = "15:55" ET.
+
+
+def _forward_signal(at_utc: str, minutes_to_close: float) -> dict:
+    """The minimal shape ``_signal_reaches_session_complete`` reads -- only
+    ``forward["at_utc"]``/``forward["minutes_to_close"]``, exactly as it is read off a real
+    already-measured signal's own ``forward`` block."""
+    return {"forward": {"at_utc": at_utc, "minutes_to_close": minutes_to_close}}
+
+
+def test_signal_reaches_session_complete_at_and_around_the_boundary():
+    """TC-20: a fixture signal engineered so its computed ``last_bar_epoch`` lands exactly at, one
+    second before, and one second after ``_session_complete_epoch(session_date)`` -- True at and
+    after the boundary, False strictly before it. The anchor (``at_utc``) is held FIXED across all
+    three cases; only ``minutes_to_close`` varies, isolating the boundary comparison from any other
+    variable."""
+    session_date = "2026-06-08"
+    boundary_epoch = referee_evidence_module._session_complete_epoch(session_date)
+    anchor_epoch = boundary_epoch - 600.0  # 10 minutes before the boundary
+    at_utc = referee_evidence_module._iso(anchor_epoch)
+
+    at_boundary = _forward_signal(at_utc, 10.0)
+    one_second_before = _forward_signal(at_utc, 10.0 - 1.0 / 60.0)
+    one_second_after = _forward_signal(at_utc, 10.0 + 1.0 / 60.0)
+
+    assert _signal_reaches_session_complete(at_boundary, session_date) is True
+    assert _signal_reaches_session_complete(one_second_before, session_date) is False
+    assert _signal_reaches_session_complete(one_second_after, session_date) is True
+
+
+def test_signal_reaches_session_complete_is_false_with_no_forward_block():
+    """A signal recorded before the (era-B2) forward-measurement pass existed carries no ``forward``
+    block at all -- an honest False, never a crash and never a fabricated True."""
+    assert _signal_reaches_session_complete({"symbol": "AAPL"}, "2026-06-08") is False
+
+
+def test_signal_reaches_session_complete_reads_bar_count_minutes_not_wall_clock_and_says_so():
+    """The disclosed bar-gap-blind limitation (module docstring), asserted as a real behavior
+    rather than left to pass silently: ``minutes_to_close`` is a BAR-COUNT-equivalent figure, not
+    measured wall-clock time, so this function is blind to any intra-session gap in the finest
+    measurement series. Two signals whose ``(anchor_epoch, minutes_to_close)`` PRODUCT is identical
+    are treated identically regardless of how much real wall-clock time actually elapsed on either
+    side of a gap -- exercised here by anchoring EARLIER in the session (23 minutes before the
+    boundary) with a bar-count-equivalent ``minutes_to_close`` that under-counts a gapped series and
+    still lands exactly one second short of the boundary: the same honest False as a gap-free
+    signal in the direct boundary test above, never a "corrected" True."""
+    session_date = "2026-06-08"
+    boundary_epoch = referee_evidence_module._session_complete_epoch(session_date)
+    anchor_epoch = boundary_epoch - 1380.0  # 23 minutes before the boundary (a gappier series)
+    at_utc = referee_evidence_module._iso(anchor_epoch)
+    gap_blind_minutes_to_close = (1380.0 - 1.0) / 60.0  # bar-count-equivalent, one second short
+
+    signal = _forward_signal(at_utc, gap_blind_minutes_to_close)
+
+    assert _signal_reaches_session_complete(signal, session_date) is False
+
+
+def test_referee_session_complete_et_is_the_pinned_1555_boundary():
+    """The boundary constant itself, pinned (spec Sec1): 15:55 ET."""
+    assert REFEREE_SESSION_COMPLETE_ET == "15:55"
+
+
+# === goal-referee-iter-3 carried rider 2 -- TC-21: resolve_referee_obs_cache_db_path =================
+#
+# Exported, never called, before this iteration.
+
+
+def test_resolve_referee_obs_cache_db_path_env_override_returns_verbatim(monkeypatch):
+    """TC-21 (env-var-override half): ``TAPEOLOGY_REFEREE_OBS_CACHE_DB`` set returns that EXACT
+    path, verbatim -- never joined, never normalized."""
+    monkeypatch.setenv("TAPEOLOGY_REFEREE_OBS_CACHE_DB", "/explicit/override/path/obs.db")
+
+    result = resolve_referee_obs_cache_db_path("/anything/universe/dir")
+
+    assert result == "/explicit/override/path/obs.db"
+
+
+def test_resolve_referee_obs_cache_db_path_defaults_to_a_sibling_of_the_playbook_dir(monkeypatch):
+    """TC-21 (sibling-of-playbook-dir default half): with the env var unset, the resolved path is
+    ``referee_obs_cache.db`` co-located as a SIBLING of ``resolve_desk_playbook_dir``'s own
+    resolved directory -- the ``playbook_evidence_cache_db_path`` resolver pattern verbatim, one
+    level up (this module has no dependency on ``desk_routes.py``)."""
+    monkeypatch.delenv("TAPEOLOGY_REFEREE_OBS_CACHE_DB", raising=False)
+    universe_dir = "/some/resolved/desk/universe"
+    playbook_dir = resolve_desk_playbook_dir(universe_dir)
+    expected = os.path.join(os.path.dirname(playbook_dir), "referee_obs_cache.db")
+
+    result = resolve_referee_obs_cache_db_path(universe_dir)
+
+    assert result == expected
+    assert os.path.basename(result) == "referee_obs_cache.db"
+    assert os.path.dirname(result) == os.path.dirname(playbook_dir)
diff --git a/apps/backend/tests/test_referee_guards.py b/apps/backend/tests/test_referee_guards.py
index b2557a6..2397188 100644
--- a/apps/backend/tests/test_referee_guards.py
+++ b/apps/backend/tests/test_referee_guards.py
@@ -210,3 +210,45 @@ def test_import_ban_guard_can_fail_on_a_seeded_violation():
     seeded_referee_imports = {"app.research.referee_evidence", "app.research.other"}
     hits = {name for name in seeded_referee_imports if name.split(".")[-1].startswith("referee_")}
     assert hits == {"app.research.referee_evidence"}
+
+
+# --- goal-referee-iter-3 TC-23: the referee_stats.py-scoped import ban -----------------------------
+#
+# IN SCOPE: "referee_stats.py imports none of desk_playbook_detect, desk_playbook_context,
+# desk_forward, levels, tradability (the stats core is estimand-agnostic -- it consumes plain
+# numeric/session arrays a future caller passes in, never rail/detector/context data directly)".
+# The bidirectional guard above already proves the first two (desk_playbook_detect/
+# desk_playbook_context) for EVERY referee_*.py module via `_referee_modules()`'s glob; this guard
+# is `referee_stats.py`-SCOPED and names all five banned modules explicitly, matching the iter
+# spec's own AST-structural pattern verbatim.
+
+_REFEREE_STATS_BANNED_MODULES = (
+    "desk_playbook_detect",
+    "desk_playbook_context",
+    "desk_forward",
+    "levels",
+    "tradability",
+)
+
+
+def test_referee_stats_module_imports_none_of_the_banned_rail_detector_context_modules():
+    """TC-23: zero imports of desk_playbook_detect/desk_playbook_context/desk_forward/levels/
+    tradability inside referee_stats.py -- the stats core is estimand-agnostic (it consumes plain
+    numeric/session arrays a caller passes in, never rail/detector/context data directly)."""
+    path = _RESEARCH_DIR / "referee_stats.py"
+    assert path.exists(), "referee_stats.py not found at the expected location -- has it moved?"
+    imported = _imported_module_names(path)
+    hits: set[str] = set()
+    for banned in _REFEREE_STATS_BANNED_MODULES:
+        hits |= _mentioning(imported, banned)
+    assert not hits, f"referee_stats.py imports the banned module(s) {hits}"
+
+
+def test_referee_stats_import_ban_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing (TC-23's own can-fail
+    counter-test)."""
+    seeded_imports = {"app.research.desk_forward", "app.research.levels", "app.research.other"}
+    hits: set[str] = set()
+    for banned in _REFEREE_STATS_BANNED_MODULES:
+        hits |= _mentioning(seeded_imports, banned)
+    assert hits == {"app.research.desk_forward", "app.research.levels"}
diff --git a/docs/referee-statistical-spec.md b/docs/referee-statistical-spec.md
index 05d4a97..74fb279 100644
--- a/docs/referee-statistical-spec.md
+++ b/docs/referee-statistical-spec.md
@@ -98,6 +98,14 @@ genuine detector revision moves `detector_basis` and honestly splits the pool. C
 honesty: each pooled record carries its per-symbol coverage; when a newest record covers
 fewer symbols than a superseded one for the same date, a served disclosure names it.
 
+**`provenance.detector_basis` is `None` for every strategy-family observation, by design.** A
+strategy trade has no detector: `detector_basis` is populated only for
+`evidence_family: "playbook_occurrence"` (the pooling identity above) and is honestly `None` on
+every `strategy_trade` observation — the same "`None` when inapplicable" convention
+`context_algorithm_version` already uses. Standing for this era per the assumption ledger
+(`state/assumptions.md`, iter-2/iter-3): a documentation clarification of the contract as
+implemented, not a new field or a redefinition of any existing one.
+
 **Completed-session rule:** a record is confirmatory-eligible for a symbol only if that
 symbol's finest measurement series reaches `REFEREE_SESSION_COMPLETE_ET` (partial mid-day
 records are exploratory-only; the session guard fails open by design, so this predicate is
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-referee/telemetry.jsonl   | 7 +++++++
 runs/goal-session-referee/trace/trace.jsonl | 1 +
 2 files changed, 8 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
