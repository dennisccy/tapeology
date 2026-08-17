# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/research/walkforward.py b/apps/backend/app/research/walkforward.py
index 0415e06..c580fce 100644
--- a/apps/backend/app/research/walkforward.py
+++ b/apps/backend/app/research/walkforward.py
@@ -55,9 +55,11 @@ import uuid
 from datetime import datetime, timezone
 from pathlib import Path
 from typing import Callable
+from zoneinfo import ZoneInfo
 
 from ..config import CONFIG, Config
 from .bars import BarStore
+from .datasets import DatasetStore
 from .desk_playbook import PlaybookStore, compute_playbook_input_signature, resolve_desk_playbook_dir
 from .desk_universe import UniverseStore
 from .micro_accessor import (
@@ -147,6 +149,7 @@ __all__ = [
     "PLAYBOOK_DIAGNOSTIC_SETUP_IDS",
     "PLAYBOOK_DIAGNOSTIC_HORIZON_LABEL",
     "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE",
+    "TICK_LEGACY_CORPUS_ID",
     "playbook_observations",
     "run_diagnostic_walkforward",
     "main",
@@ -966,6 +969,37 @@ PLAYBOOK_DIAGNOSTIC_HORIZON_LABEL = "1h"
 # ordering is a genuine, contiguous trading calendar rather than one artifact date sitting alone.
 PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE = "2025-06-03"
 
+# The legacy tick corpus's OWN corpus_id for the section 6.7 exposure registry (iter-6, closing
+# iter-5 audit finding B2: "the exposure registry is never r2-initialized for the 12 legacy tick
+# symbol-days in production -- a latent breach of the 'never historical_oos' anti-goal"). A name
+# DISTINCT from PLAYBOOK_DIAGNOSTIC_CORPUS_ID -- an implementation choice this iteration's own plan
+# explicitly authorizes and asks to be logged (T-1: never invented silently); "_v1" mirrors that
+# sibling constant's own versioned-name shape, so a future Card-5.2 recorder revision that changes
+# what "the legacy tick corpus" even means is a distinguishable v2, never a silent redefinition.
+TICK_LEGACY_CORPUS_ID = "tick_legacy_symbol_days_v1"
+
+_ET_ZONE = ZoneInfo("America/New_York")
+
+
+def _tick_dataset_session_dates(dataset_store: DatasetStore) -> list[str]:
+    """Every currently-registered tick dataset's own ET session date (spec section 0: "a session
+    is an ET RTH trading date"), one entry per DISTINCT date -- the SAME ET-conversion technique
+    ``micro_readiness.py``'s own ``_et_datetime`` and ``micro_accessor.py``'s own
+    ``_session_date_for_dataset`` already use (mirrored, not imported -- the established
+    per-module private-``ZoneInfo`` idiom those modules' own docstrings document), read straight
+    off ``DatasetStore.list()``'s own already-checksum-verified metadata -- no second inventory
+    mechanism, no hardcoded date list (iter-6 plan). Cheap: ``list()`` is metadata-only (no event
+    replay), the identical cost ``micro_readiness.py``'s own per-shard ``session_date`` derivation
+    already pays."""
+    records, _errors = dataset_store.list()
+    session_dates: set[str] = set()
+    for meta in records:
+        parsed = datetime.fromisoformat(meta["window_start_utc"].replace("Z", "+00:00"))
+        if parsed.tzinfo is None:
+            parsed = parsed.replace(tzinfo=timezone.utc)
+        session_dates.add(parsed.astimezone(_ET_ZONE).date().isoformat())
+    return sorted(session_dates)
+
 
 def playbook_observations(
     playbook_store, *, setup_ids: tuple[str, ...], horizon_label: str, default_signature: str, exclude_session_dates: tuple[str, ...] = ()
@@ -1031,7 +1065,19 @@ def run_diagnostic_walkforward(
     classifies every window honestly from whatever IS on record -- never a special-cased 'diagnostic
     always' shortcut). Never a blocking pytest recomputation (the Constraints' own iteration-hygiene
     rail) -- this function is the ONE body both ``WalkForwardComputeManager``'s worker and the CLI's
-    ``main()`` call."""
+    ``main()`` call.
+
+    **iter-6 additions (closing iter-5 audit findings B5 and B2).** Immediately before
+    ``build_folds``, this function now calls ``require_sufficient_sessions_for_folds`` (TR-15) --
+    a below-floor corpus raises ``InsufficientSessionsForFoldsError`` naming the exact shortfall,
+    caught by both the CLI's ``main()`` (prints + non-zero exit) and
+    ``WalkForwardComputeManager.trigger``'s existing generic handler (resolves the run to
+    ``"failed"``); today's real 155-session corpus stays far above the 105-session floor, so this
+    is defensive and does not change the served result. It also self-initializes a SECOND,
+    corpus-scoped r2 exposure registry seed for ``TICK_LEGACY_CORPUS_ID`` (the 12 legacy tick
+    symbol-days), mirroring the playbook seed immediately above it -- so the critical anti-goal
+    ("never `historical_oos`" for those 12 symbol-days) can never be breached by an unseeded
+    registry once a future spec is registered against a tick window."""
     # THE PREDECLARATION, FIRST -- before this function reads anything at all (goal.md J-05 IN
     # SCOPE item 8: "predeclare (ledgered, before any outcome read) ... the run's candidate
     # rule(s)"; spec section 6.5's own "registered (ledger row, spec hash, timestamp) FIRST").
@@ -1072,6 +1118,17 @@ def run_diagnostic_walkforward(
     if not has_any_exposure_entries(exposure_registry, PLAYBOOK_DIAGNOSTIC_CORPUS_ID):
         initialize_r2_exposure_registry(exposure_registry, corpus_id=PLAYBOOK_DIAGNOSTIC_CORPUS_ID, windows=session_dates)
 
+    # iter-6 (closing iter-5 audit finding B2): the SAME r2 initialization, for the legacy TICK
+    # corpus -- resolved via `config.dataset_dir_resolved()` the exact way `micro_readiness.py`
+    # already does (no second inventory mechanism), under its OWN distinct corpus_id so the two
+    # corpora's exposure rows are never conflated (TC-7 proves `micro_readiness.py`'s separately-
+    # served, per-shard `exposure_state` is untouched by this). Fires from this SAME operator-act
+    # entry point -- never a GET route (era Non-Goal: "No scheduling").
+    if not has_any_exposure_entries(exposure_registry, TICK_LEGACY_CORPUS_ID):
+        tick_dataset_store = DatasetStore(config.dataset_dir_resolved())
+        tick_session_dates = _tick_dataset_session_dates(tick_dataset_store)
+        initialize_r2_exposure_registry(exposure_registry, corpus_id=TICK_LEGACY_CORPUS_ID, windows=tick_session_dates)
+
     corpus_manifest_hash = _sha256(_canonical(session_dates))
     floors = {
         "wf_fold_min_observations": WF_FOLD_MIN_OBSERVATIONS,
@@ -1082,6 +1139,13 @@ def run_diagnostic_walkforward(
         ledger, corpus_id=PLAYBOOK_DIAGNOSTIC_CORPUS_ID, corpus_manifest_hash=corpus_manifest_hash,
         geometry=DIAGNOSTIC_GEOMETRY, floors=floors,
     )
+    # iter-6 (closing iter-5 audit finding B5): TR-15's typed floor refusal, wired into the ONE
+    # production fold-building call site -- immediately before `build_folds`, so a below-floor
+    # corpus raises `InsufficientSessionsForFoldsError` naming the exact shortfall instead of
+    # `build_folds` silently returning `[]` (the "empty fold report standing in for the refusal"
+    # TR-15's own wording forbids). Placed AFTER `register_fold_spec` -- the frozen geometry is
+    # still committed to the ledger even for a below-floor corpus; only fold EVALUATION is refused.
+    require_sufficient_sessions_for_folds(session_dates, DIAGNOSTIC_GEOMETRY)
     folds = build_folds(session_dates, DIAGNOSTIC_GEOMETRY)
 
     observations = playbook_observations(
@@ -1153,10 +1217,15 @@ def main() -> int:
         print("nothing to do -- pass --diagnostic to run the acceptance run.")
         return 0
 
-    result = run_diagnostic_walkforward(
-        ledger, exposure_registry, playbook_store, universe_store, bar_store, config,
-        progress=lambda step: print(f"  [{step}] fold evaluated", flush=True),
-    )
+    try:
+        result = run_diagnostic_walkforward(
+            ledger, exposure_registry, playbook_store, universe_store, bar_store, config,
+            progress=lambda step: print(f"  [{step}] fold evaluated", flush=True),
+        )
+    except InsufficientSessionsForFoldsError as exc:
+        # TC-4: the typed refusal, printed and exited non-zero -- never an unhandled traceback.
+        print(f"diagnostic walk-forward refused: {exc}")
+        return 1
     print(
         f"diagnostic walk-forward complete: {result['folds_evaluated']} fold(s) "
         f"({result['folds_appended']} newly recorded, {result['folds_replayed']} replayed from the "
diff --git a/apps/backend/tests/test_walkforward.py b/apps/backend/tests/test_walkforward.py
index 89fef79..a6aa1b4 100644
--- a/apps/backend/tests/test_walkforward.py
+++ b/apps/backend/tests/test_walkforward.py
@@ -11,9 +11,12 @@ import pytest
 from fastapi.testclient import TestClient
 
 from app.main import app
+from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import walkforward as wf
 from app.research import walkforward_ledger as wl
-from app.research.micro_accessor import ExposureRegistry, initialize_r2_exposure_registry
+from app.research.datasets import DatasetStore
+from app.research.micro_accessor import ExposureRegistry, has_any_exposure_entries, initialize_r2_exposure_registry
+from app.research.micro_readiness import EXPOSURE_STATE_EXPLORATORY, MicroReadinessCache, build_readiness
 from app.research.micro_routes import (
     get_micro_exposure_registry_dir,
     get_walkforward_compute_manager,
@@ -509,12 +512,46 @@ class _FakeUniverseStore:
 
 
 class _FakeConfig:
-    """A stand-in for ``app.config.Config`` -- the ONLY method ``run_diagnostic_walkforward``'s
-    own (monkeypatched-away in this test) ``compute_playbook_input_signature`` call needs."""
+    """A stand-in for ``app.config.Config`` -- the two methods ``run_diagnostic_walkforward``
+    calls on it: ``config_fingerprint`` (via ``compute_playbook_input_signature``, monkeypatched
+    away in most of these tests) and, since iter-6, ``dataset_dir_resolved`` (the tick-corpus
+    exposure-seeding call, TC-5/TC-6/TC-7). Defaults to a directory that deliberately does not
+    exist, so ``DatasetStore.list()`` honestly answers zero tick datasets (``DatasetStore``'s own
+    documented "construction is cheap, no I/O" contract; ``list()`` returns ``[]`` for a
+    non-existent root) rather than every test that does not care about the tick corpus needing to
+    fabricate one."""
+
+    def __init__(self, dataset_dir: str = "no-tick-corpus-for-this-fake-config") -> None:
+        self._dataset_dir = dataset_dir
 
     def config_fingerprint(self) -> str:
         return "fake-fingerprint"
 
+    def dataset_dir_resolved(self) -> str:
+        return self._dataset_dir
+
+
+def _tick_events(symbol: str, *, price: float) -> list:
+    """A minimal one-quote/one-trade pair -- these tests only need ``DatasetStore.list()``'s own
+    metadata (``window_start_utc``), never event CONTENT, so the fixture stays tiny (the
+    ``test_micro_readiness.py`` ``_events``/``_plant_dataset`` precedent, trimmed to what this
+    file's own tests actually exercise). ``price`` is a pure content differentiator -- ``DatasetStore.
+    record``'s own checksum hashes ``(symbol, data_feed, epoch_anchor, rows)``, NOT the window
+    times, so two shards for the SAME symbol on two DIFFERENT session dates need distinct content
+    or the store's immutable-dataset guard (correctly) refuses the second as an exact re-record."""
+    return [
+        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
+        TradeEvent(symbol, 0.1, price, 10, Side.BUY),
+    ]
+
+
+def _plant_tick_dataset(store: DatasetStore, *, symbol: str, window_start_utc: str, window_end_utc: str, price: float = 100.00) -> dict:
+    return store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-fixture",
+        split="train", window_start_utc=window_start_utc, window_end_utc=window_end_utc,
+        data_feed="sip", epoch_anchor=0.0, events=_tick_events(symbol, price=price),
+    )
+
 
 def _fake_signal(setup_id: str, symbol: str, return_pct: float) -> dict:
     return {
@@ -615,6 +652,148 @@ def test_tc23_and_tc24_the_diagnostic_run_over_a_small_synthetic_corpus(tmp_path
     assert operator_verdict["verdict"] == "not_survivor"
 
 
+# === iter-6: TR-15 wiring + tick-corpus exposure seeding (closing iter-5 audit findings B5/B2) ======
+
+
+def test_tc2_run_diagnostic_walkforward_itself_raises_the_typed_refusal_below_the_session_floor(tmp_path, monkeypatch):
+    """TR-15, wired into the ONE production fold-building call site: a below-floor session list
+    must raise through the REAL ``run_diagnostic_walkforward`` path (not merely the standalone
+    ``require_sufficient_sessions_for_folds`` TC-20 already covers) -- never a success dict with
+    an empty ``rows`` list standing in for the refusal (iter-5 audit finding B5)."""
+    signature = "sig-below-floor"
+    sessions = [f"2026-06-{d:02d}" for d in range(1, 11)]  # 10 sessions, far below the 105 floor
+    records = [
+        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
+        for s in sessions
+    ]
+    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
+    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+
+    with pytest.raises(wf.InsufficientSessionsForFoldsError, match=r"10 < 105"):
+        wf.run_diagnostic_walkforward(
+            ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None, config=_FakeConfig(),
+        )
+
+    # register_fold_spec ran (the frozen geometry is committed even for a below-floor corpus) but
+    # fold EVALUATION never did -- never a success dict with an empty `rows` list standing in for
+    # the refusal (B5's own wording).
+    assert wl.latest_fold_spec(ledger, wf.PLAYBOOK_DIAGNOSTIC_CORPUS_ID) is not None
+    assert ledger.rows_of_kind(wl.ROW_KIND_FOLD_RESULT) == []
+
+
+def test_tc5_first_diagnostic_run_seeds_one_tick_exposure_entry_per_session_window(tmp_path, monkeypatch):
+    """TC-5 (closing iter-5 audit finding B2): the FIRST diagnostic walk-forward operator act
+    against a tick ``DatasetStore`` that has never been exposure-seeded gains one entry per
+    session window of EVERY currently-registered tick dataset, under ``wf.TICK_LEGACY_CORPUS_ID``
+    -- a corpus_id DISTINCT from ``PLAYBOOK_DIAGNOSTIC_CORPUS_ID``, resolved via
+    ``config.dataset_dir_resolved()`` the SAME way ``micro_readiness.py`` already does (no second
+    inventory mechanism, no hardcoded date list)."""
+    signature = "sig-tc5"
+    sessions = [f"2026-07-{d:03d}" for d in range(1, 156)]
+    records = [
+        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
+        for s in sessions
+    ]
+    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
+    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+
+    tick_dir = tmp_path / "tick_datasets"
+    tick_store = DatasetStore(tick_dir)
+    _plant_tick_dataset(tick_store, symbol="AAPL", window_start_utc="2026-06-08T13:30:00Z", window_end_utc="2026-06-08T20:00:00Z")
+    _plant_tick_dataset(tick_store, symbol="MSFT", window_start_utc="2026-06-08T13:30:00Z", window_end_utc="2026-06-08T20:00:00Z")
+    _plant_tick_dataset(tick_store, symbol="AAPL", window_start_utc="2026-06-09T13:30:00Z", window_end_utc="2026-06-09T20:00:00Z", price=101.00)
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    assert not has_any_exposure_entries(registry, wf.TICK_LEGACY_CORPUS_ID)
+
+    wf.run_diagnostic_walkforward(
+        ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None,
+        config=_FakeConfig(dataset_dir=str(tick_dir)),
+    )
+
+    assert wf.TICK_LEGACY_CORPUS_ID != wf.PLAYBOOK_DIAGNOSTIC_CORPUS_ID
+    tick_rows = [r for r in registry.all_rows() if r["corpus_id"] == wf.TICK_LEGACY_CORPUS_ID]
+    # one entry per DISTINCT session window, not per shard (3 shards, 2 distinct dates) -- the
+    # playbook seeding's own convention, mirrored.
+    assert {r["window"] for r in tick_rows} == {"2026-06-08", "2026-06-09"}
+    assert len(tick_rows) == 2
+
+    # the two corpora's rows never mix.
+    playbook_rows = [r for r in registry.all_rows() if r["corpus_id"] == wf.PLAYBOOK_DIAGNOSTIC_CORPUS_ID]
+    assert len(playbook_rows) == 155
+
+
+def test_tc6_a_second_diagnostic_run_leaves_the_tick_corpus_exposure_row_count_unchanged(tmp_path, monkeypatch):
+    """TC-6: mirrors the existing playbook ``has_any_exposure_entries`` guard (module docstring)
+    -- a repeated operator act against the SAME durable registry must never re-append the tick
+    corpus's whole window list a second time (idempotent seeding)."""
+    signature = "sig-tc6"
+    sessions = [f"2026-08-{d:03d}" for d in range(1, 156)]
+    records = [
+        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
+        for s in sessions
+    ]
+    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
+    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+
+    tick_dir = tmp_path / "tick_datasets"
+    tick_store = DatasetStore(tick_dir)
+    _plant_tick_dataset(tick_store, symbol="AAPL", window_start_utc="2026-06-08T13:30:00Z", window_end_utc="2026-06-08T20:00:00Z")
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    config = _FakeConfig(dataset_dir=str(tick_dir))
+
+    wf.run_diagnostic_walkforward(ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None, config=config)
+    rows_after_first = len([r for r in registry.all_rows() if r["corpus_id"] == wf.TICK_LEGACY_CORPUS_ID])
+    assert rows_after_first == 1
+
+    wf.run_diagnostic_walkforward(ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None, config=config)
+    rows_after_second = len([r for r in registry.all_rows() if r["corpus_id"] == wf.TICK_LEGACY_CORPUS_ID])
+    assert rows_after_second == rows_after_first
+
+
+def test_tc7_micro_readiness_exposure_state_is_unaffected_by_the_new_tick_exposure_registry(tmp_path, monkeypatch):
+    """TC-7: the walk-forward-internal ``ExposureRegistry`` (this iteration's own
+    ``historical_oos`` classification mechanism) and ``micro_readiness.py``'s served, PER-SHARD
+    ``exposure_state`` (``exploratory``/``hand_assigned`` -- the vault's own, separate vocabulary)
+    are two DIFFERENT mechanisms and must never be conflated: seeding the former must never move
+    the latter (the critical anti-goal -- "the 12 pre-existing tick symbol-days are permanently
+    exploratory")."""
+    tick_dir = tmp_path / "tick_datasets"
+    tick_store = DatasetStore(tick_dir)
+    _plant_tick_dataset(tick_store, symbol="AAPL", window_start_utc="2026-06-08T13:30:00Z", window_end_utc="2026-06-08T20:00:00Z")
+    _plant_tick_dataset(tick_store, symbol="MSFT", window_start_utc="2026-06-09T13:30:00Z", window_end_utc="2026-06-09T20:00:00Z")
+
+    signature = "sig-tc7"
+    sessions = [f"2026-09-{d:03d}" for d in range(1, 156)]
+    records = [
+        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
+        for s in sessions
+    ]
+    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
+    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    wf.run_diagnostic_walkforward(
+        ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None,
+        config=_FakeConfig(dataset_dir=str(tick_dir)),
+    )
+    tick_rows = [r for r in registry.all_rows() if r["corpus_id"] == wf.TICK_LEGACY_CORPUS_ID]
+    assert len(tick_rows) == 2  # the seeding genuinely happened
+
+    cache = MicroReadinessCache(str(tmp_path / "readiness_cache.db"))
+    readiness = build_readiness(tick_store, cache, dataset_dir=str(tick_dir))
+    assert len(readiness["shards"]) == 2
+    for shard in readiness["shards"]:
+        assert shard["exposure_state"] == EXPOSURE_STATE_EXPLORATORY
+
+
 # === audit regression: a REPEAT operator run never double-counts a sequence's own evidence =========
 # (found by the iteration-5 audit against the REAL ledger: pressing POST /walkforward/compute -- or
 # re-running the CLI warmer -- a second time appended a second physical fold_result row per fold, so
@@ -795,11 +974,14 @@ def test_tc26_a_truncated_walkforward_ledger_tail_is_caught_even_though_the_chai
 # === the CLI is a thin wrapper, never a second implementation (the scout.py CLI-test precedent) ======
 
 
-def test_the_cli_runs_the_same_run_diagnostic_walkforward_against_real_env_var_scoped_stores(tmp_path, monkeypatch):
+def test_the_cli_prints_the_typed_refusal_and_exits_non_zero_on_a_below_floor_corpus(tmp_path, monkeypatch, capsys):
     """``python -m app.research.walkforward --diagnostic`` -- points every store at ``tmp_path``
     via the SAME env-var overrides ``CONFIG.dataset_dir_resolved()``/``desk_universe_dir_resolved
-    ()``/``bar_dir_resolved()`` already read, never touches the real ``.data`` corpus. An empty
-    store tree is an honest 0-fold run, never a crash."""
+    ()``/``bar_dir_resolved()`` already read, never touching the real ``.data`` corpus (this
+    test's original intent, preserved). TC-4: a completely empty store tree is a below-floor
+    corpus (0 sessions, far under the 105-session floor) -- since iter-6's TR-15 wiring, this now
+    prints the typed refusal and exits non-zero, never an unhandled Python traceback (previously:
+    an honest-but-unrefused 0-fold run -- exactly the B5 gap this iteration closes)."""
     import sys
 
     monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
@@ -810,13 +992,20 @@ def test_the_cli_runs_the_same_run_diagnostic_walkforward_against_real_env_var_s
     monkeypatch.setattr(sys, "argv", ["walkforward.py", "--diagnostic"])
 
     exit_code = wf.main()
-    assert exit_code == 0
+    assert exit_code != 0
+
+    captured = capsys.readouterr()
+    assert captured.err == ""  # never an unhandled traceback
+    assert "0 < 105" in captured.out
+    assert "TR-15" in captured.out
 
     ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
-    # an empty universe/playbook tree registers the fold spec but evaluates zero folds -- honest,
-    # never a crash (build_folds([], ...) == []).
+    # the fold spec IS registered (require_sufficient_sessions_for_folds fires AFTER register_
+    # fold_spec, per this iteration's own call-site placement) -- but zero fold_result rows, never
+    # a fabricated evaluation over an insufficient sample.
     fold_specs = wl.latest_fold_spec(ledger, wf.PLAYBOOK_DIAGNOSTIC_CORPUS_ID)
     assert fold_specs is not None
+    assert ledger.rows_of_kind(wl.ROW_KIND_FOLD_RESULT) == []
     assert fold_specs["geometry"] == wf.DIAGNOSTIC_GEOMETRY
 
 
@@ -839,6 +1028,11 @@ def test_walkforward_routes_serve_empty_state_honestly_and_the_compute_trigger_r
     ]
     monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
     monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+    # trigger_walkforward_compute passes the REAL CONFIG (not FastAPI-injected) straight through
+    # to run_diagnostic_walkforward, which -- since iter-6 -- also reads CONFIG.dataset_dir_
+    # resolved() for the tick-corpus exposure seed; redirect it so this route test never touches
+    # the real .data/datasets corpus.
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "no_tick_datasets"))
 
     ledger_dir = str(tmp_path / "wf_ledger")
     exposure_dir = str(tmp_path / "wf_exposure")
@@ -880,3 +1074,51 @@ def test_walkforward_routes_serve_empty_state_honestly_and_the_compute_trigger_r
     finally:
         for dep in (get_walkforward_ledger_dir, get_micro_exposure_registry_dir, get_walkforward_compute_manager, get_universe_store, get_bar_store, get_playbook_store):
             app.dependency_overrides.pop(dep, None)
+
+
+def test_tc3_the_compute_routes_worker_resolves_the_typed_refusal_to_a_failed_run_never_a_500(tmp_path, monkeypatch):
+    """TC-3: ``WalkForwardComputeManager.trigger``'s EXISTING generic exception handler
+    (``walkforward.py``'s own ``except Exception as exc: self._resolve_terminal(..., "failed",
+    error=str(exc))``, read-and-confirmed rather than re-plumbed -- iter-6 plan item 2) already
+    resolves a raised ``InsufficientSessionsForFoldsError`` from the compute route's worker to
+    ``{"state": "failed", "error": "<message>"}`` -- never an unhandled 500, never a
+    silently-empty success."""
+    signature = "sig-route-below-floor"
+    sessions = [f"2026-10-{d:02d}" for d in range(1, 11)]  # 10 sessions, below the 105 floor
+    records = [
+        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
+        for s in sessions
+    ]
+    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
+    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "no_tick_datasets"))  # never the real corpus
+
+    ledger_dir = str(tmp_path / "wf_ledger")
+    exposure_dir = str(tmp_path / "wf_exposure")
+    manager = wf.WalkForwardComputeManager()
+
+    app.dependency_overrides[get_walkforward_ledger_dir] = lambda: ledger_dir
+    app.dependency_overrides[get_micro_exposure_registry_dir] = lambda: exposure_dir
+    app.dependency_overrides[get_walkforward_compute_manager] = lambda: manager
+    app.dependency_overrides[get_universe_store] = lambda: _FakeUniverseStore(["AAPL"])
+    app.dependency_overrides[get_bar_store] = lambda: None
+    app.dependency_overrides[get_playbook_store] = lambda: _FakePlaybookStore(records)
+    try:
+        with TestClient(app) as client:
+            triggered = client.post("/research/desk/micro/walkforward/compute")
+            assert triggered.status_code == 200
+            assert triggered.json()["state"] == "running"
+
+            manager.join_all(timeout=30.0)
+            polled = client.get("/research/desk/micro/walkforward/compute")
+            assert polled.status_code == 200
+            body = polled.json()
+            assert body["state"] == "failed"
+            assert "10 < 105" in body["error"]
+
+            # the run log carries the SAME "failed" terminal state, never a silently-empty success
+            runs = client.get("/research/desk/micro/walkforward/runs")
+            assert runs.json()["runs"][0]["state"] == "failed"
+    finally:
+        for dep in (get_walkforward_ledger_dir, get_micro_exposure_registry_dir, get_walkforward_compute_manager, get_universe_store, get_bar_store, get_playbook_store):
+            app.dependency_overrides.pop(dep, None)
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 9 +++++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 11 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
