# Iteration diff (bounded)

Files changed: 12. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/micro_features.py` (68 lines not shown)
- `apps/backend/app/research/micro_observer.py` (367 lines not shown)
- `apps/backend/app/research/micro_snapshots.py` (123 lines not shown)
- `apps/backend/tests/test_micro_features.py` (31 lines not shown)
- `apps/backend/tests/test_micro_observer.py` (132 lines not shown)
- `apps/backend/tests/test_micro_snapshots.py` (126 lines not shown)

```diff
diff --git a/README.md b/README.md
index 47b2a9a..3f12367 100644
--- a/README.md
+++ b/README.md
@@ -72,6 +72,7 @@ Current capabilities:
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /research/desk/coverage`, `POST /research/desk/topup/compute`, `GET /research/desk/topup/compute`, `POST /research/desk/topup/compute/cancel`, `GET /research/desk/topup/runs`, `GET /research/desk/screen`, `POST /research/desk/screen/compute`, `GET /research/desk/screen/compute`, `POST /research/desk/screen/compute/cancel`, `POST /research/desk/coverage/reconcile/compute`, `GET /research/desk/coverage/reconcile/compute`, `POST /research/desk/coverage/reconcile/compute/cancel`, `GET /research/desk/coverage/reconcile/runs`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, S&P 100 universe snapshots, the Desk screen ledger, top-up run history, index reconciliation runs, and navigation data the REST API serves. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 - **Desk screening briefing (iter-22 complete)** — the third top-level page (`/desk`) presents a daily briefing over a registered S&P 100 universe snapshot, showing per-symbol the closest tradable support/resistance band, its A/B/C class, the closing price it was measured from, and how many days of historical data back it. Every row displays coverage badges for which timeframes have bars recorded, a "nearest opposite-side wall" disclosure showing the wall on the other side of price (or an honest note when none exists), a hover tooltip breaking down the walls by quality class, and clickable drill-in to the Structure page for that symbol on that date. A "Provenance" line tracks which universe snapshot, screen date, and configuration produced the briefing. Explicit operator-run "Run Screen" and "Top-up" buttons with live progress and cancel show real-time work, never auto-triggered on page load. Browsable screen history lists every past run; clicking a past run renders that exact snapshot's saved rows (no recompute). A "Top-up Runs" section logs every bar-fetch attempt with outcome detail — how many series were reused from storage, freshly fetched, or failed — and a "Reconcile Index" tool keeps the coverage badges honest by checking for drift between the bar index and stored files. All numbers on the page are read from their canonical owners (the tradability module for bands, the bar index for coverage) and never recomputed in the browser.
+- **Microscope Readiness on the Desk page** — a new "Microscope Readiness" section on `/desk` displays the corpus truth: the inventory of recorded tick-level market-data datasets (symbol-days, shards, bytes, session-equivalents), per-shard coverage (completeness, fallback fractions for aggressor-side inference, integrity checksums), and an honest statement of which predeclared research floors are met — today showing 12 symbol-days across 18 shards (~3.0 session-equivalents), all marked as exploratory and hand-assigned, with every pilot-study floor unmet.
 <!-- /AUTO:capabilities -->
 
 ## Reading the Desk page
diff --git a/apps/backend/app/research/datasets.py b/apps/backend/app/research/datasets.py
index a38b3dc..76f7861 100644
--- a/apps/backend/app/research/datasets.py
+++ b/apps/backend/app/research/datasets.py
@@ -373,16 +373,29 @@ class DatasetStore:
         symbol = loaded.meta["symbol"]
         return [_row_to_event(symbol, row) for row in loaded.rows]
 
-    def replay(self, dataset_id: str, config: Config) -> Iterator[EngineSnapshot]:
+    def replay(
+        self, dataset_id: str, config: Config, *, observer: object | None = None
+    ) -> Iterator[EngineSnapshot]:
         """Replay the stored dataset UNPACED through a FRESH ``TapeEngine``, yielding every
         per-event snapshot. Deterministic: the stored stream, the stored
         source descriptor, and the stored epoch anchor fully determine the output — re-runs are
-        byte-identical, and both match replaying the original source stream."""
+        byte-identical, and both match replaying the original source stream.
+
+        ``observer`` (era "The Rapid Microscope" J-02, spec section 2.1) is an ADDITIVE,
+        default-``None`` kwarg: when given, it is registered on the fresh engine via the EXISTING
+        ``TapeEngine.add_observer`` seam (capability 20) once, before the event loop starts.
+        ``observer=None`` is byte-identical to before this kwarg existed — every pre-existing call
+        site (none of which pass it) is unaffected, and ``tests/test_observer_equivalence.py``
+        already proves attaching an observer never perturbs a single yielded snapshot. This is the
+        ONE replay entry point; no second replay implementation exists anywhere for research code
+        to attach to."""
         loaded = self._load_by_id(dataset_id)
         meta = loaded.meta
         engine = TapeEngine(
             meta["symbol"], meta["source"], config, epoch_anchor=meta["epoch_anchor"]
         )
+        if observer is not None:
+            engine.add_observer(observer)
         for row in loaded.rows:
             yield engine.process_event(_row_to_event(meta["symbol"], row))
 
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index b5d34af..7fdf083 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -1,28 +1,36 @@
-"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, the era's
-first route. A fresh router/file mounted separately in ``main.py``, mirroring
+"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold plus J-02's
+three snapshot routes. A fresh router/file mounted separately in ``main.py``, mirroring
 ``referee_routes.py``'s own precedent and rationale (that file's own docstring: "the SAME
 rationale desk_routes.py itself gives for splitting off routes.py"). The era's own Data Contract
-table (``docs/goal.md``'s Product Shape) names six MORE micro routes landing in later iterations
-(snapshots, scout, walkforward, vault, recorder, graduation) under this SAME
-``/research/desk/micro`` prefix -- a dedicated file is the right home from the start.
+table (``docs/goal.md``'s Product Shape) names four MORE micro routes landing in later iterations
+(scout, walkforward, vault, recorder, graduation) under this SAME ``/research/desk/micro`` prefix
+-- a dedicated file is the right home from the start.
 
 Depends on a store this route does NOT own: the dataset store dependency is imported verbatim
-from ``routes.get_dataset_store`` (never a second, redefined provider). The readiness cache is
-this module's OWN wiring (the ``referee_routes.py`` precedent: "this module owns its own wiring
-end to end") -- a config-derived, env-overridable path exactly like every sibling durable cache's
-own FastAPI dependency (``get_edge_report_cache``/``get_bar_index`` in ``routes.py``).
+from ``routes.get_dataset_store`` (never a second, redefined provider). The readiness cache and
+the snapshot-compute manager are this module's OWN wiring (the ``referee_routes.py`` precedent:
+"this module owns its own wiring end to end") -- the manager lives as a module-level singleton
+behind a ``Depends``-able accessor (the ``desk_routes.py`` ``get_desk_playbook_compute_manager``
+precedent, so a test overrides the DEPENDENCY with a fresh manager, never reaches into the
+module-level singleton directly).
 
-``GET /readiness`` is a plain read: it triggers nothing but the readiness fold's own documented
-one-time-then-cached per-shard classification (page-load GETs never compute a SECOND time, T-8;
-the module itself is the ONE place, this route only wires it)."""
+``GET /readiness`` and ``GET /snapshots``/``GET /snapshots/runs`` are plain reads: page-load GETs
+never compute (T-8) -- a snapshot BUILD is an explicit operator act through
+``POST /snapshots/compute``, exactly like the desk's own compute-manager pattern."""
 
 from __future__ import annotations
 
-from fastapi import APIRouter, Depends
+from fastapi import APIRouter, Depends, HTTPException
 
 from ..config import CONFIG
 from .datasets import DatasetStore
 from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
+from .micro_snapshots import (
+    MicroSnapshotComputeManager,
+    list_snapshot_meta,
+    read_run_log,
+    resolve_micro_snapshots_dir,
+)
 from .routes import get_dataset_store
 
 router = APIRouter(prefix="/research/desk/micro", tags=["micro"])
@@ -50,3 +58,88 @@ def get_micro_readiness(
     ``shards`` list (``study_floors`` still carries its 3 rows, each read against a 0-session
     corpus) at HTTP 200."""
     return build_readiness(dataset_store, cache, dataset_dir=CONFIG.dataset_dir_resolved())
+
+
+def get_micro_snapshots_dir() -> str:
+    """The snapshot store's directory -- ``TAPEOLOGY_MICRO_SNAPSHOTS_DIR`` if set, else a
+    SIBLING of the config-owned dataset directory (``micro_snapshots.resolve_micro_snapshots_dir``
+    -- see that function's own docstring)."""
+    return resolve_micro_snapshots_dir(CONFIG.dataset_dir_resolved())
+
+
+# The single in-flight (or last-terminal) snapshot-build job for THIS process -- the
+# ``desk_routes.py`` module-singleton-behind-a-Depends-accessor precedent (module docstring), never
+# per-request-constructed (a fresh manager per request could never observe a job it just started).
+_micro_snapshot_compute_manager = MicroSnapshotComputeManager()
+
+
+def get_micro_snapshot_compute_manager() -> MicroSnapshotComputeManager:
+    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
+    ``get_desk_playbook_compute_manager`` precedent) -- never reaches into the module-level
+    singleton directly."""
+    return _micro_snapshot_compute_manager
+
+
+@router.get("/snapshots")
+def get_micro_snapshots(
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    snapshots_dir: str = Depends(get_micro_snapshots_dir),
+) -> dict:
+    """BUILD METADATA only -- the identity tuple, ``row_count``, ``quote_size_unit``, timestamps
+    -- for every CURRENTLY VALID (identity re-verified) snapshot; never raw per-event feature
+    rows (the boundary note: an origin-fenced, event-level read is ``micro_accessor.py``'s
+    exclusive door, J-05, not this route). Never 404/500 on zero built snapshots -- an honest
+    empty list, the desk router's established convention."""
+    return {"snapshots": list_snapshot_meta(snapshots_dir, dataset_store, CONFIG)}
+
+
+@router.post("/snapshots/compute")
+def trigger_micro_snapshots_compute(
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    snapshots_dir: str = Depends(get_micro_snapshots_dir),
+    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
+) -> dict:
+    """Start a snapshot build for every dataset currently in the store (reusing any already-valid
+    snapshot -- ``run_snapshot_build_and_record``'s own reuse-or-build discipline), or refuse
+    (single-flight) if one is already running."""
+    result = manager.trigger(dataset_store, CONFIG, snapshots_dir)
+    if result["state"] == "refused":
+        return result
+    return {"state": result["state"], "run_id": result["run_id"]}
+
+
+@router.get("/snapshots/compute")
+def get_micro_snapshots_compute(
+    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
+) -> dict:
+    """The current (or last-terminal) build job's progress -- never 404 (the ``_IDLE_SNAPSHOT``
+    default before any job has ever run this process)."""
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
+@router.post("/snapshots/compute/cancel")
+def cancel_micro_snapshots_compute(
+    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
+) -> dict:
+    """Signal cooperative cancellation for the in-flight job -- a 409 for an idle manager (the
+    ``desk_playbook`` "the ROUTE is the one that rejects an idle cancel with a 409" precedent),
+    else ``{"state": "cancelled"}`` acknowledging the REQUEST (the worker itself settles at the
+    next dataset boundary -- ``MicroSnapshotComputeManager.cancel``'s own docstring)."""
+    if manager.snapshot()["state"] != "running":
+        raise HTTPException(status_code=409, detail="no snapshot build is currently running")
+    manager.cancel()
+    return {"state": "cancelled"}
+
+
+@router.get("/snapshots/runs")
+def get_micro_snapshots_runs(snapshots_dir: str = Depends(get_micro_snapshots_dir)) -> dict:
+    """The durable build-run history, newest first -- never 404 on zero runs (an honest empty
+    list)."""
+    return {"runs": read_run_log(snapshots_dir)}
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index bc02591..a9c445b 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -36,6 +36,17 @@
 # (read-only) so J-10's /structure step measures the kept product, not a fixture. See that script's
 # own docstring for the nineteen-member universe and the two computes it records.
 #
+# goal-rapid-microscope-iter-2 (J-01's browser gap + J-02 test infra) extends it once more, again
+# in place (never rewritten — this file's own long-standing rule): stages the two ALREADY-COMMITTED
+# PG SIP tick-dataset fixtures (tests/fixtures/datasets/*.json — the exact on-disk DatasetStore file
+# shape, so a plain copy suffices; never a pointer at, or copy of, the real .data/datasets store)
+# into this rig's own throwaway $ROOT/datasets before backend start, mirroring how the datasets dir
+# was already exported (TAPEOLOGY_DATASET_DIR) but left with zero tick shards. This closes the gap
+# iteration 1 left open: the Microscope Readiness panel could only be proven via API/text-extract
+# through this mandated rig, never a real non-empty screenshot (T-10). Real, non-fabricated, but
+# deliberately small — seeding the full 18-dataset/12-symbol-day corpus is deferred to whichever
+# LATER iteration first needs it (J-06/J-08/J-09), per the rubric's "smallest fix that unblocks now."
+#
 # The default root name changes to playbook-iter8-replay-fixture-qa (a genuinely FRESH root, never
 # an earlier one reused) — the universe/signature composition is wider again, and the script's own
 # long-standing rule ("use a fresh root whenever the seeded composition changed") applies to this
@@ -75,6 +86,13 @@ JOURNAL_DB="$ROOT/journal.db"
 mkdir -p "$BAR_DIR" "$UNIVERSE_DIR" "$PLAYBOOK_DIR" "$PLAYBOOK_LOG_DIR" \
          "$PLAYBOOK_BACKSCAN_LOG_DIR" "$SCREEN_DIR" "$DATASET_DIR"
 
+# goal-rapid-microscope-iter-2: seed the two already-committed PG SIP tick-dataset fixtures (a
+# plain file copy — the fixture IS the on-disk DatasetStore shape already) so J-01's Microscope
+# Readiness panel finally photographs a real, non-empty shard table through this rig instead of an
+# empty corpus (see the header comment above).
+cp "$BACKEND_DIR/tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json" "$DATASET_DIR/"
+cp "$BACKEND_DIR/tests/fixtures/datasets/d9f9dbe04fb24a7caccc53f0c6805412.json" "$DATASET_DIR/"
+
 export TAPEOLOGY_BAR_DIR="$BAR_DIR"
 export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
 export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index c7d8b12..5a5177b 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -517,6 +517,21 @@ def test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmeti
     seeded_signal_unmeasured = "const measured = cell.signal.n - cell.signal.n_unmeasured;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_unmeasured) is not None
 
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
 
 def test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic():
     """goal-rapid-microscope-iter-1 (J-01) TC-9 counter-test: the extended guard catches
@@ -538,21 +553,6 @@ def test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmet
     seeded_shortfall = "const shortfall = floor.required_sessions - floor.available_sessions;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_shortfall) is not None
 
-    seeded_signal_sessions = "const perSession = cell.signal.n / cell.signal.n_sessions;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_sessions) is not None
-
-    seeded_baseline_truncated = "const clean = cell.baseline.n_baseline - cell.baseline.n_truncated;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_truncated) is not None
-
-    seeded_baseline_unmeasured = "const total = cell.baseline.n_baseline + cell.baseline.n_unmeasured;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_unmeasured) is not None
-
-    seeded_baseline_sessions = "const perSession = cell.baseline.n_baseline / cell.baseline.n_sessions;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_sessions) is not None
-
-    seeded_basis = "const perDate = basis.n_records / basis.dates.length;"
-    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_basis) is not None
-
     # And the pattern does NOT over-match: the real page's own guard test below still finds zero
     # hits, so this new coverage does not accidentally flag legitimate, non-arithmetic JSX.
     assert _PRICE_ARITHMETIC_PATTERN.search("const label = `${basis.n_records} records`;") is None
diff --git a/apps/backend/app/research/micro_features.py b/apps/backend/app/research/micro_features.py
new file mode 100644
index 0000000..076719d
--- /dev/null
+++ b/apps/backend/app/research/micro_features.py
@@ -0,0 +1,462 @@
+"""``micro_features.py`` -- Era "The Rapid Microscope" J-02: the Wave-1 feature FAMILIES
+
+(``docs/rapid-validation-spec.md`` section 3) plus the closed outcome set (section 4) and the
+section 2.6 cross-basis unit gate. Every value here is a PURE function of its explicit inputs --
+no state, no I/O, no wall-clock, no randomness -- so the same inputs reproduce byte-identical
+outputs (the determinism anti-goal) and every family has a hand-derived oracle fixture
+(``tests/test_micro_features.py``, TR-16 feature-level vectors).
+
+**This module owns the constants table (spec section 1), narrowed to exactly what J-02 consumes.**
+The remaining rows of that table (``SCOUT_*``, ``WF_*`` beyond what ``micro_readiness.py`` already
+transcribed, ``VAULT_*``, ``TRANCHE_MINIMUMS``, ``KILL_REASONS``, ``ALPACA_QUOTE_SIZE_UNIT_
+EFFECTIVE``, ``MICRO_HORIZON_*``) belong to the modules that actually read them (``scout.py``,
+``walkforward.py``, ``vault.py``, ``tick_recorder.py`` -- J-04 through J-06) and are deliberately
+NOT pre-declared here: minting an unused constant now would risk a second, independently-valued
+copy the day those modules land (the exact anti-pattern ``micro_readiness.py``'s own docstring
+warns against for ``WF_TRAIN_MIN_SESSIONS``/``WF_TEST_MIN_SESSIONS``). Every constant below is
+frozen verbatim from the spec table -- arbitrary-but-fixed, chosen before any outcome was read; a
+change to any of them is a NAMED REVISION, never a tuning act.
+
+**Statelessness is the point.** The STREAMING state machine that turns one ordered event stream
+into rows (rolling buffers, deferred-construct pending queues, the prefix law itself) lives in
+``micro_observer.py`` -- this module supplies the pure arithmetic that state machine calls into,
+so every formula is independently testable against a hand-computed fixture without replaying a
+single event.
+
+**Reuse, never recompute (spec section 2.5).** Nothing here re-derives the aggressor side, the
+five engine window features, tape state, or bid/ask/spread/last -- those are read verbatim off the
+``EngineSnapshot`` by the observer and threaded through untouched. This module computes ONLY the
+additive research quantities the engine does not already produce.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import statistics
+from typing import Sequence
+
+__all__ = [
+    "MICRO_SEED",
+    "MICRO_ALGO_VERSION",
+    "MICRO_FEATURE_WINDOW_TRADES",
+    "MICRO_FEATURE_WINDOW_SHARES",
+    "REFILL_M_QUOTES",
+    "RESPONSE_K_TRADES",
+    "BURST_BASELINE_TRAILING_WINDOWS",
+    "DEPLETION_WINDOW_QUOTES",
+    "IMPACT_FLATNESS_SCALE_BPS",
+    "DIVERGENCE_TRAILING_SECONDS",
+    "DIVERGENCE_DELTA_VOLUME_FRACTION",
+    "QUOTE_SIZE_UNITS",
+    "CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT",
+    "CROSS_BASIS_SHARE_DENOMINATED_KINDS",
+    "SIDE_SOURCE_QUOTE_RULE",
+    "SIDE_SOURCE_TICK_TEST",
+    "SIDE_SOURCE_CARRIED",
+    "SIDE_SOURCE_UNKNOWN",
+    "micro_parameters",
+    "micro_parameters_hash",
+    "dominant_side_volume_share",
+    "failed_aggression_score",
+    "rolling_imbalance",
+    "quote_imbalance",
+    "microprice",
+    "mid_price",
+    "bps_move",
+    "price_extreme_trailing",
+    "divergence_delta_threshold",
+    "divergence_at_level",
+    "OutcomeRefused",
+    "resolve_outcome_start",
+    "require_outcome_start_not_before_conditioning",
+    "mid_outcome",
+    "last_trade_outcome",
+    "CrossBasisUnverifiedUnitError",
+    "is_verified_unit",
+    "require_verified_unit",
+    "require_uniform_unit_for_pool",
+    "require_share_denominated_magnitude_allowed",
+    "execution_vs_replenishment_ratio",
+]
+
+# --- Pre-registered constants (docs/rapid-validation-spec.md section 1 -- transcribed verbatim,
+# narrowed to J-02's own consumption; see module docstring). --------------------------------------
+
+MICRO_SEED = 314159
+MICRO_ALGO_VERSION = 1
+
+MICRO_FEATURE_WINDOW_TRADES: tuple[int, ...] = (20, 100)
+MICRO_FEATURE_WINDOW_SHARES: tuple[int, ...] = (5_000, 50_000)
+REFILL_M_QUOTES = 20
+RESPONSE_K_TRADES = 20
+BURST_BASELINE_TRAILING_WINDOWS = 20
+DEPLETION_WINDOW_QUOTES = 20
+IMPACT_FLATNESS_SCALE_BPS = 5.0
+DIVERGENCE_TRAILING_SECONDS = 120.0
+DIVERGENCE_DELTA_VOLUME_FRACTION = 0.25
+
+QUOTE_SIZE_UNITS: tuple[str, ...] = ("shares", "round_lots", "unverified")
+
+# The closed refusal vocabulary of the section 2.6 gate. A STREAMING caller (``micro_observer.py``)
+# cannot let ``CrossBasisUnverifiedUnitError`` escape -- aborting a whole replay because one
+# dataset's unit basis is unverified would refuse the unit-INVARIANT features too -- so it records
+# this token on the affected value instead: same refusal, same fail-closed meaning, expressed as
+# persisted data rather than as an exception. Kept short deliberately: it lands on every refused
+# row of a multi-GB snapshot corpus.
+CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT = "cross_basis_unverified_quote_size_unit"
+
+# The deferred-construct kinds whose VALUE is a raw share-denominated cross-basis magnitude (spec
+# section 3: "as is any share-denominated depletion/replenishment magnitude") -- each one refused
+# unless its dataset's ``quote_size_unit`` is verified. The closed list the TR-18 guards sweep.
+CROSS_BASIS_SHARE_DENOMINATED_KINDS: tuple[str, ...] = ("quote_depletion",)
+
+# The side_source vocabulary (spec section 2.5) -- the ONLY four values that may ever appear.
+SIDE_SOURCE_QUOTE_RULE = "quote_rule"
+SIDE_SOURCE_TICK_TEST = "tick_test"
+SIDE_SOURCE_CARRIED = "carried"
+SIDE_SOURCE_UNKNOWN = "unknown"
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding this module hashes -- the identical ``datasets.py``
+    ``_canonical`` shape (sorted keys, no whitespace), duplicated here (not imported) because it
+    is a generic 1-line utility, not a second implementation of any measurement rail."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def micro_parameters() -> dict:
+    """Every module constant a persisted feature value actually depends on, embedded VERBATIM
+    (the desk ``playbook_parameters()`` pattern) -- keyed on its hash by every persisted snapshot
+    record. A monkeypatched constant must move BOTH this dict's hash AND the depending result's
+    own identity (counter-tested in ``tests/test_micro_features.py``)."""
+    return {
+        "micro_seed": MICRO_SEED,
+        "micro_feature_window_trades": list(MICRO_FEATURE_WINDOW_TRADES),
+        "micro_feature_window_shares": list(MICRO_FEATURE_WINDOW_SHARES),
+        "refill_m_quotes": REFILL_M_QUOTES,
+        "response_k_trades": RESPONSE_K_TRADES,
+        "burst_baseline_trailing_windows": BURST_BASELINE_TRAILING_WINDOWS,
+        "depletion_window_quotes": DEPLETION_WINDOW_QUOTES,
+        "impact_flatness_scale_bps": IMPACT_FLATNESS_SCALE_BPS,
+        "divergence_trailing_seconds": DIVERGENCE_TRAILING_SECONDS,
+        "divergence_delta_volume_fraction": DIVERGENCE_DELTA_VOLUME_FRACTION,
+    }
+
+
+def micro_parameters_hash() -> str:
+    """sha256 of ``micro_parameters()``'s canonical encoding -- one component of the snapshot
+    identity tuple (``micro_snapshots.py``, spec section 2.3)."""
+    return _sha256(_canonical(micro_parameters()))
+
+
+# --- F-FLOW ------------------------------------------------------------------------------------
+
+
+def rolling_imbalance(buy_volume: float, sell_volume: float) -> float | None:
+    """``(buy - sell) / (buy + sell)`` over whatever window the caller already accumulated;
+    ``None`` (undefined, never a fabricated 0.0) when the window carries no directional volume."""
+    directional = buy_volume + sell_volume
+    if directional <= 0:
+        return None
+    return (buy_volume - sell_volume) / directional
+
+
+def dominant_side_volume_share(buy_volume: float, sell_volume: float) -> float:
+    """``max(buy, sell) / directional`` -- ``0.0`` when neither side has traded (spec section 3's
+    own stated default), never ``None`` (this one feeds a continuous score, not a ratio display)."""
+    directional = buy_volume + sell_volume
+    if directional <= 0:
+        return 0.0
+    return max(buy_volume, sell_volume) / directional
+
+
+def volume_burst(window_volume: float, baseline_window_volumes: Sequence[float]) -> float | None:
+    """``window_volume`` (the trailing feature-window's own volume) divided by the median of the
+    prior ``BURST_BASELINE_TRAILING_WINDOWS`` non-overlapping same-length baseline windows.
+    ``None`` (undefined, COUNTED never guessed) with fewer than 5 baseline windows (spec section
+    3) or a zero median (a burst ratio against zero volume is not a meaningful multiple)."""
+    if len(baseline_window_volumes) < 5:
+        return None
+    baseline = statistics.median(baseline_window_volumes)
+    if baseline <= 0:
+        return None
+    return window_volume / baseline
+
+
+def mid_price(bid: float | None, ask: float | None) -> float | None:
+    if bid is None or ask is None:
+        return None
+    return (bid + ask) / 2.0
+
+
+def bps_move(mid_start: float | None, mid_end: float | None) -> float | None:
+    """Signed move from ``mid_start`` to ``mid_end`` in basis points of ``mid_start``. ``None``
+    when either side is unmeasured or the starting mid is non-positive (no basis to express a
+    bps move against)."""
+    if mid_start is None or mid_end is None or mid_start <= 0:
+        return None
+    return (mid_end - mid_start) / mid_start * 10_000.0
+
+
+def price_extreme_trailing(
+    price_history: Sequence[tuple[float, float]], tau: float, window_seconds: float = DIVERGENCE_TRAILING_SECONDS
+) -> float | None:
+    """The max mid over the TRAILING ``[tau - window_seconds, tau]`` window, AS-OF ``tau`` (never
+    a later value) -- spec section 3's ``price_extreme(tau)`` for the divergence-at-level formula.
+    Max (never min): "bearish divergence" pairs a HIGHER price high against a weaker cumulative
+    delta -- a named interpretation call (a higher price extreme is the one meaningful basis for a
+    *bearish* reading; the spec's "max/min" phrasing does not otherwise disambiguate), logged in
+    the dev handoff. ``price_history`` is an ascending ``(ts, mid)`` sequence; ``None`` with no
+    point in range (undefined, never fabricated)."""
+    lo = tau - window_seconds
+    values = [mid for ts, mid in price_history if lo <= ts <= tau]
+    if not values:
+        return None
+    return max(values)
+
+
+def divergence_delta_threshold(baseline_volumes: Sequence[float]) -> float | None:
+    """``delta = DIVERGENCE_DELTA_VOLUME_FRACTION x median(trailing-120s session-prefix baseline
+    volumes)`` (spec section 3, Card 9.1's fraction) -- "the SAME session-prefix baseline windows"
+    ``volume_burst`` draws from, so the identical ``BURST_BASELINE_TRAILING_WINDOWS``-derived floor
+    applies: fewer than 5 windows is undefined (counted), never a thin-sample guess."""
+    if len(baseline_volumes) < 5:
+        return None
+    return DIVERGENCE_DELTA_VOLUME_FRACTION * statistics.median(baseline_volumes)
+
+
+def divergence_at_level(
+    *,
+    price_history: Sequence[tuple[float, float]],
+    tau1: float,
+    tau2: float,
+    cum_delta_at_tau1: float,
+    cum_delta_at_tau2: float,
+    baseline_volumes: Sequence[float],
+) -> dict:
+    """Divergence-at-level (Card 9.1, amended r2): bearish divergence iff
+    ``price_extreme(tau2) > price_extreme(tau1)`` AND ``CD(tau2) <= CD(tau1) - delta``, at
+    consecutive touches ``tau1 < tau2`` of the same recorded band. Pure and oracle-testable: the
+    caller (a future ``micro_join.py``, J-03 -- out of scope this iteration, since no band-touch
+    join exists yet) supplies the two cumulative-delta readings and the trailing price history
+    directly; this function performs no lookup of its own. ``available_at = tau2`` (the later
+    touch fixes when the comparison could first be made)."""
+    price_extreme_tau1 = price_extreme_trailing(price_history, tau1)
+    price_extreme_tau2 = price_extreme_trailing(price_history, tau2)
+    delta = divergence_delta_threshold(baseline_volumes)
+    bearish: bool | None
+    if price_extreme_tau1 is None or price_extreme_tau2 is None or delta is None:
+        bearish = None
+    else:
+        bearish = (price_extreme_tau2 > price_extreme_tau1) and (
+            cum_delta_at_tau2 <= cum_delta_at_tau1 - delta
+        )
+    return {
+        "tau1": tau1,
+        "tau2": tau2,
+        "price_extreme_tau1": price_extreme_tau1,
+        "price_extreme_tau2": price_extreme_tau2,
+        "cum_delta_tau1": cum_delta_at_tau1,
+        "cum_delta_tau2": cum_delta_at_tau2,
+        "delta_volume_fraction_threshold": delta,
+        "bearish_divergence": bearish,
+        "available_at": tau2,
+    }
+
+
+# --- F-RESPONSE ----------------------------------------------------------------------------------
+
+
+def failed_aggression_score(dominant_share: float, delta_mid_bps: float | None) -> float:
+    """``dominant_side_volume_share x clamp(1 - |delta_mid_bps| / IMPACT_FLATNESS_SCALE_BPS, 0, 1)``
+    (spec section 3, the continuous complement to the engine's own gated ``absorption_score``).
+    A ``None`` price move (no quote basis) reads as maximal flatness (1.0) -- consistent with the
+    engine's own ``absorption_score``, which also treats "no measured impact" as flat, never as
+    undefined."""
+    if delta_mid_bps is None:
+        flatness = 1.0
+    else:
+        flatness = max(0.0, min(1.0, 1.0 - abs(delta_mid_bps) / IMPACT_FLATNESS_SCALE_BPS))
+    return dominant_share * flatness
+
+
+def impact_efficiency(delta_mid_bps: float | None, aggressive_shares: float) -> float | None:
+    """Signed mid move (bps, aggressor-signed -- ``delta_mid_bps`` is expected pre-signed by the
+    caller) per 1,000 aggressive shares over a feature window. ``None`` with no measured move or
+    zero aggressive volume (no basis for a per-1000-share rate)."""
+    if delta_mid_bps is None or aggressive_shares <= 0:
+        return None
+    return delta_mid_bps / (aggressive_shares / 1_000.0)
+
+
+# --- F-LIQUIDITY ---------------------------------------------------------------------------------
+
+
+def quote_imbalance(bid_size: float, ask_size: float) -> float | None:
+    total = bid_size + ask_size
+    if total <= 0:
+        return None
+    return (bid_size - ask_size) / total
+
+
+def microprice(bid: float, ask: float, bid_size: float, ask_size: float) -> float | None:
+    total = bid_size + ask_size
+    if total <= 0:
+        return None
+    return (ask * bid_size + bid * ask_size) / total
+
+
+# --- The closed outcome set (spec section 4) ------------------------------------------------------
+
+
+class OutcomeRefused(Exception):
+    """A requested outcome start precedes its conditioning feature set's maximum ``available_at``
+    (TR-17c) -- refused, never silently measured early."""
+
+
+def resolve_outcome_start(conditioning_available_at: Sequence[float]) -> float:
+    """Outcome start = the conditioning feature set's maximum ``available_at`` (spec section 4;
+    equals ``anchor_at`` when every conditioning feature is prefix, strictly later for a deferred
+    construct). The canonical, always-legal resolution -- callers that want the guarded, possibly-
+    illegal path use ``require_outcome_start_not_before_conditioning`` instead (TC-6/TR-17c)."""
+    if not conditioning_available_at:
+        raise ValueError("at least one conditioning available_at instant is required")
+    return max(conditioning_available_at)
+
+
+def require_outcome_start_not_before_conditioning(
+    requested_start: float, conditioning_available_at: Sequence[float]
+) -> float:
+    """TR-17c's refusal: a ``requested_start`` earlier than the conditioning set's maximum
+    ``available_at`` is refused with a typed error, never silently measured early. Returns
+    ``requested_start`` unchanged when it is legal (>= the conditioning floor)."""
+    floor = resolve_outcome_start(conditioning_available_at)
+    if requested_start < floor:
+        raise OutcomeRefused(
+            f"requested outcome start {requested_start!r} precedes the conditioning feature "
+            f"set's maximum available_at {floor!r} -- refused (TR-17c), never measured early"
+        )
+    return requested_start
+
+
+def _signed(value: float | None, side: str | None) -> float | None:
+    if value is None:
+        return None
+    return -value if side == "sell" else value
+
+
+def mid_outcome(
+    *,
+    mid_at_start: float | None,
+    mid_at_horizon: float | None,
+    outcome_start: float,
+    horizon_ts: float,
+    session_end_ts: float,
+    side: str | None,
+) -> dict:
+    """The mid-basis PRIMARY outcome (spec section 4): forward mid-price move from ``outcome_
+    start`` to ``horizon_ts``, side-signed when ``side`` names a hypothesis direction ("buy"/
+    "sell"), session-truncated with the truncation flagged (and the row excluded from any later
+    average, never silently measured past the session). A row lacking a quote mid at either end is
+    ``unmeasured`` -- excluded and counted, never silently measured off the last trade."""
+    truncated = horizon_ts > session_end_ts
+    unmeasured = mid_at_start is None or mid_at_horizon is None
+    value = None
+    if not unmeasured and not truncated:
+        value = _signed(mid_at_horizon - mid_at_start, side)
+    return {
+        "basis": "mid",
+        "outcome_start": outcome_start,
+        "horizon_ts": horizon_ts,
+        "value": value,
+        "unmeasured": unmeasured,
+        "truncated": truncated,
+    }
+
+
+def last_trade_outcome(
+    *,
+    price_at_start: float | None,
+    price_at_horizon: float | None,
+    outcome_start: float,
+    horizon_ts: float,
+    session_end_ts: float,
+    side: str | None,
+) -> dict:
+    """The SEPARATELY NAMED last-trade-basis sensitivity column (spec section 4) -- identical
+    shape to ``mid_outcome``, never pooled with, substituted for, or averaged into the mid-basis
+    primary. Callers must keep the two bases apart at every serving surface."""
+    truncated = horizon_ts > session_end_ts
... [diff_bound] apps/backend/app/research/micro_features.py: 68 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/micro_observer.py b/apps/backend/app/research/micro_observer.py
new file mode 100644
index 0000000..55930f4
--- /dev/null
+++ b/apps/backend/app/research/micro_observer.py
@@ -0,0 +1,761 @@
+"""``micro_observer.py`` -- Era "The Rapid Microscope" J-02: the streaming, prefix-honest observer
+
+(``docs/rapid-validation-spec.md`` section 2.2) that turns ONE ordered replay pass into a
+sequence of trade-anchored feature rows. Attached via the additive ``DatasetStore.replay(...,
+observer=...)`` kwarg (section 2.1) onto the engine's EXISTING ``add_observer`` seam -- this
+module reads the engine's per-tick snapshot, never a second replay, never a recomputed side.
+
+**The prefix law, mechanically.** ``on_event`` is called once per event, in stored order, by the
+engine's own ``_notify_event`` (``tape_engine.py``). Row *i* (this module appends one row per
+TRADE event -- see "Granularity" below) is built and appended to ``self.rows`` synchronously
+inside that call, using only: (a) accumulated state from events ``1..i`` this instance has already
+seen, and (b) the engine snapshot handed to THIS call (itself a pure function of events ``1..i``).
+Once a row is appended it is **NEVER mutated** -- a later event may only ever APPEND new rows or
+attach a deferred completion (see below) to a row not yet appended; it can never reach back and
+edit an already-flushed row. This is what makes truncation byte-identical to a prefix of the full
+run (TR-1): rows ``1..k`` of a replay stopped after event ``k`` are, by construction, identical to
+rows ``1..k`` of the full replay, because no later event can ever have touched them.
+
+**Granularity: one row per TRADE, not one row per raw event.** The section 2.4 benchmark
+(``micro_snapshots.py`` / ``scripts/micro_snapshot_granularity_benchmark.py``) measures this
+choice against a per-raw-event and a fixed-stride-block alternative and records the comparison;
+this module implements the winning representation. Quotes update this observer's OWN internal
+state (it tracks its own bid/ask/bid_size/ask_size from the raw ``QuoteEvent`` -- the engine's
+``FeatureEngine`` drops quote SIZES at ``add_quote``, so nowhere else carries them) but never
+produce a row of their own; every research question this era asks is anchored at a trade or a
+future structural touch (spec section 4), never at a bare quote tick.
+
+**Reuse, never recompute (spec section 2.5).** The aggressor SIDE for a trade is read verbatim
+from ``snapshot.recent_trades[0].side`` (the engine's own just-computed decision, freshly
+``appendleft``-ed by ``process_event`` before ``on_event`` fires) -- this module never calls
+``classify_aggressor`` itself. ``side_source`` (which of the classifier's two stages decided) is
+NOT part of the engine's public surface at all, so it cannot be "read" from anywhere; this module
+derives it by mirroring ``classify_aggressor``'s own DOCUMENTED stage-1 precondition (the identical
+technique ``micro_readiness.py``'s ``_quote_rule_decides`` already uses and its own docstring
+justifies at length) against quote/prior-trade state this observer tracks itself, in lockstep with
+what the engine's ``MarketState``/``_last_tick_dir`` carry internally (mirrored, never read, since
+the engine exposes neither) -- it is never a second implementation of the SIDE decision, only of
+the (undisclosed) stage that decided it.
+
+**Deferred constructs (spec section 0 / 2.2).** ``response_asymmetry`` (K subsequent trades),
+``refill_consistent`` (M subsequent same-side quote updates) and ``quote_depletion`` (a same-price
+quote run, up to its own update bound) cannot be known at their own anchor row. Each is tracked in
+a small pending queue; the moment it resolves (or is proven ``unavailable`` at session end via
+``finalize``) it is attached to the ``deferred`` list of whichever row is CURRENTLY being built
+when the resolution happens -- never retroactively edited into the anchor's own already-flushed
+row. ``response_asymmetry`` resolves exactly at the K-th subsequent trade's OWN row (a trade-count
+horizon over a trade-anchored stream lines up exactly); ``refill_consistent``/``quote_depletion``
+are quote-driven and may resolve between two trades, so they queue in ``self._pending_attachments``
+until the next row is built (or ``finalize`` sweeps them into an honest closing summary if the
+session ends first).
+
+**The section 2.6 cross-basis unit gate, in the STREAMING path (TR-18).** ``quote_depletion``'s
+value is a raw SHARE-denominated magnitude, which spec section 3 names CROSS-BASIS alongside the
+execution-vs-replenishment ratio: it is refused unless this dataset's ``quote_size_unit`` is
+verified. ``_resolve_depletion`` therefore passes ``mf.require_share_denominated_magnitude_allowed``
+at the point of emission, and on refusal attaches ``value: None`` plus the closed-vocabulary
+``refusal_reason`` (``mf.CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT``) instead of the number -- every one
+of the 18 legacy datasets is ``unverified``, so this is the LIVE path, not a corner case. The
+refusal is DATA, not an exception, because the alternative -- letting the error escape mid-replay --
+would refuse the unit-INVARIANT features (quote imbalance, microprice, everything in F-FLOW and
+F-RESPONSE) along with it; the two extra keys ride only on the affected ``quote_depletion``
+attachments, so consumers of the OTHER deferred kinds read an unchanged shape. ``refill_consistent``
+needs no gate: it compares a displayed size to a displayed size in the SAME dataset, which is
+unit-invariant at any ``quote_size_unit`` (spec section 2.6's own carve-out), and it serves a
+boolean, never a magnitude. The row-level ``quote_size_unit`` stamp is the label itself, not
+arithmetic over it."""
+
+from __future__ import annotations
+
+from collections import deque
+from typing import Deque
+
+from ..providers.base import Event, QuoteEvent, Side, TradeEvent
+from . import micro_features as mf
+
+__all__ = ["MicroObserver", "MicroObserverFailure"]
+
+
+class MicroObserverFailure(Exception):
+    """``MicroObserver.on_event`` raised while streaming a replay.
+
+    The engine's ``_notify_event`` is exception-ISOLATED by design (``tape_engine.py``: a research
+    observer must never perturb engine output, so a raise there is logged, flagged on the ENGINE,
+    and swallowed). That is correct for the engine -- but it means a mid-stream observer failure is
+    otherwise INVISIBLE to the snapshot builder, which would then persist a silently truncated row
+    set and identity-verify it as a complete, valid snapshot. ``MicroObserver`` therefore records
+    its own failure (``self.failure``) and stops consuming, and ``micro_snapshots.build_snapshot_
+    rows`` raises this typed error rather than writing a partial snapshot -- fail-closed, explicit,
+    never a silently short corpus."""
+
+_WINDOW_SIZES: tuple[int, ...] = mf.MICRO_FEATURE_WINDOW_TRADES  # (20, 100)
+_SHARE_WINDOW_SIZES: tuple[int, ...] = mf.MICRO_FEATURE_WINDOW_SHARES  # (5_000, 50_000)
+
+
+class _SlidingPair:
+    """O(1)-amortized bookkeeping for ONE trade-count window size ``n``: a "current" trailing
+    window of the last ``n`` trades and the "prior" NON-OVERLAPPING window of the ``n`` trades
+    immediately before it -- both needed for ``efficiency_trend``/``spread_change`` (current minus
+    prior) and ``volume_burst`` (current against a trailing tile history), without ever rescanning
+    a deque slice (essential at NVDA's ~929K-trade scale -- see module docstring and the dev
+    handoff's timing note).
+
+    On each ``push``: if ``current`` is already full, its OLDEST entry graduates into ``prior``
+    (evicting prior's own oldest entry first, if prior is also full) BEFORE the new entry enters
+    ``current`` -- so ``current`` always holds the ``n`` most recent trades and ``prior`` the ``n``
+    immediately before those, both bounded, both O(1) per push."""
+
+    __slots__ = (
+        "n",
+        "current",
+        "prior",
+        "cur_buy",
+        "cur_sell",
+        "cur_spread_sum",
+        "cur_spread_n",
+        "cur_fallback",
+        "cur_unknown",
+        "prior_buy",
+        "prior_sell",
+        "prior_spread_sum",
+        "prior_spread_n",
+    )
+
+    def __init__(self, n: int) -> None:
+        self.n = n
+        self.current: Deque[dict] = deque()
+        self.prior: Deque[dict] = deque()
+        self.cur_buy = 0.0
+        self.cur_sell = 0.0
+        self.cur_spread_sum = 0.0
+        self.cur_spread_n = 0
+        self.cur_fallback = 0
+        self.cur_unknown = 0
+        self.prior_buy = 0.0
+        self.prior_sell = 0.0
+        self.prior_spread_sum = 0.0
+        self.prior_spread_n = 0
+
+    def _remove_from_prior(self, entry: dict) -> None:
+        if entry["side"] == "buy":
+            self.prior_buy -= entry["size"]
+        elif entry["side"] == "sell":
+            self.prior_sell -= entry["size"]
+        if entry["spread"] is not None:
+            self.prior_spread_sum -= entry["spread"]
+            self.prior_spread_n -= 1
+
+    def _add_to_prior(self, entry: dict) -> None:
+        if entry["side"] == "buy":
+            self.prior_buy += entry["size"]
+        elif entry["side"] == "sell":
+            self.prior_sell += entry["size"]
+        if entry["spread"] is not None:
+            self.prior_spread_sum += entry["spread"]
+            self.prior_spread_n += 1
+
+    def _remove_from_current(self, entry: dict) -> None:
+        if entry["side"] == "buy":
+            self.cur_buy -= entry["size"]
+        elif entry["side"] == "sell":
+            self.cur_sell -= entry["size"]
+        if entry["spread"] is not None:
+            self.cur_spread_sum -= entry["spread"]
+            self.cur_spread_n -= 1
+        if entry["side_source"] in (mf.SIDE_SOURCE_TICK_TEST, mf.SIDE_SOURCE_CARRIED):
+            self.cur_fallback -= 1
+        elif entry["side_source"] == mf.SIDE_SOURCE_UNKNOWN:
+            self.cur_unknown -= 1
+
+    def _add_to_current(self, entry: dict) -> None:
+        if entry["side"] == "buy":
+            self.cur_buy += entry["size"]
+        elif entry["side"] == "sell":
+            self.cur_sell += entry["size"]
+        if entry["spread"] is not None:
+            self.cur_spread_sum += entry["spread"]
+            self.cur_spread_n += 1
+        if entry["side_source"] in (mf.SIDE_SOURCE_TICK_TEST, mf.SIDE_SOURCE_CARRIED):
+            self.cur_fallback += 1
+        elif entry["side_source"] == mf.SIDE_SOURCE_UNKNOWN:
+            self.cur_unknown += 1
+
+    def push(self, entry: dict) -> None:
+        if len(self.current) >= self.n:
+            graduate = self.current.popleft()
+            self._remove_from_current(graduate)
+            if len(self.prior) >= self.n:
+                evicted = self.prior.popleft()
+                self._remove_from_prior(evicted)
+            self.prior.append(graduate)
+            self._add_to_prior(graduate)
+        self.current.append(entry)
+        self._add_to_current(entry)
+
+    # --- derived readings -------------------------------------------------------------------
+
+    def window_volume(self) -> float:
+        return self.cur_buy + self.cur_sell  # directional only -- unknown-sided prints excluded
+
+    def total_window_volume(self) -> float:
+        return sum(e["size"] for e in self.current)  # ALL prints, incl. unknown-sided
+
+    def rolling_imbalance(self) -> float | None:
+        return mf.rolling_imbalance(self.cur_buy, self.cur_sell)
+
+    def fallback_frac(self) -> float | None:
+        if not self.current:
+            return None
+        return self.cur_fallback / len(self.current)
+
+    def unknown_frac(self) -> float | None:
+        if not self.current:
+            return None
+        return self.cur_unknown / len(self.current)
+
+    def _window_mid_delta_bps(self, buf: Deque[dict], buy: float, sell: float) -> float | None:
+        if not buf:
+            return None
+        mid_start = buf[0]["mid"]
+        mid_end = buf[-1]["mid"]
+        raw = mf.bps_move(mid_start, mid_end)
+        if raw is None:
+            return None
+        return raw if buy >= sell else -raw  # aggressor-signed (module docstring's own note)
+
+    def current_delta_bps(self) -> float | None:
+        """The aggressor-signed mid move over THIS window -- exposed publicly (not just used
+        internally by ``impact_efficiency``) so ``failed_aggression_score`` can share the exact
+        same reading rather than recompute it a second way."""
+        return self._window_mid_delta_bps(self.current, self.cur_buy, self.cur_sell)
+
+    def impact_efficiency(self) -> float | None:
+        return mf.impact_efficiency(self.current_delta_bps(), self.window_volume())
+
+    def prior_impact_efficiency(self) -> float | None:
+        if len(self.prior) < self.n:
+            return None
+        delta_bps = self._window_mid_delta_bps(self.prior, self.prior_buy, self.prior_sell)
+        return mf.impact_efficiency(delta_bps, self.prior_buy + self.prior_sell)
+
+    def efficiency_trend(self) -> float | None:
+        cur = self.impact_efficiency()
+        prior = self.prior_impact_efficiency()
+        if cur is None or prior is None:
+            return None
+        return cur - prior
+
+    def spread_change(self) -> float | None:
+        if len(self.prior) < self.n or self.cur_spread_n == 0 or self.prior_spread_n == 0:
+            return None
+        return (self.cur_spread_sum / self.cur_spread_n) - (self.prior_spread_sum / self.prior_spread_n)
+
+
+class _ShareWindow:
+    """The volume-time counterpart to ``_SlidingPair``: a trailing window bounded by cumulative
+    SHARES (``MICRO_FEATURE_WINDOW_SHARES``) rather than trade count. O(1) amortized: a deque of
+    (side, size) trimmed from the front while the running total exceeds the threshold."""
+
+    __slots__ = ("threshold", "buf", "buy", "sell")
+
+    def __init__(self, threshold: int) -> None:
+        self.threshold = threshold
+        self.buf: Deque[tuple[str, float]] = deque()
+        self.buy = 0.0
+        self.sell = 0.0
+
+    def push(self, side: str, size: float) -> None:
+        # Unknown-sided prints carry no direction to contribute to a directional volume-time
+        # window -- they are deliberately never buffered here at all (never merely zero-weighted),
+        # so ``buf`` only ever holds entries whose size IS reflected in ``buy``/``sell``/``total``;
+        # trimming below can then subtract any evicted entry's size from ``total`` unconditionally,
+        # with no risk of double-uncounting an entry that was never counted in the first place.
+        if side not in ("buy", "sell"):
+            return
+        self.buf.append((side, size))
+        if side == "buy":
+            self.buy += size
+        else:
+            self.sell += size
+        total = self.buy + self.sell
+        while total > self.threshold and len(self.buf) > 1:
+            old_side, old_size = self.buf[0]
+            # Only trim while the window's directional total still exceeds the threshold WITHOUT
+            # the oldest entry -- never trim the entry that is itself needed to stay >= threshold
+            # (a share-bounded window is "at least this many shares", the natural reading of a
+            # volume-time window).
+            remaining = total - old_size
+            if remaining < self.threshold:
+                break
+            self.buf.popleft()
+            if old_side == "buy":
+                self.buy -= old_size
+            else:
+                self.sell -= old_size
+            total = self.buy + self.sell
+
+    def rolling_imbalance(self) -> float | None:
+        return mf.rolling_imbalance(self.buy, self.sell)
+
+
+class MicroObserver:
+    """One instance per replay (constructed fresh, exactly like the ``TapeEngine`` it attaches
+    to). ``on_event`` is the ONLY method the engine's ``_notify_event`` calls; every other method
+    is this module's own orchestration, called by the snapshot builder (``micro_snapshots.py``)
+    around the replay loop."""
+
+    def __init__(self, *, quote_size_unit: str) -> None:
+        self.quote_size_unit = quote_size_unit
+        self.rows: list[dict] = []
+        # The engine swallows observer exceptions (MicroObserverFailure's docstring), so this is
+        # the ONLY place a mid-stream failure survives for the snapshot builder to refuse on.
+        self.failure: BaseException | None = None
+
+        # --- side_source mirror state (module docstring) -- lockstep with the engine's own
+        # MarketState/_last_tick_dir, which the engine does not expose. ---------------------------
+        self._current_quote: QuoteEvent | None = None
+        self._current_bid_size: int | None = None
+        self._current_ask_size: int | None = None
+        self._prior_trade_price: float | None = None
+        self._last_tick_dir: Side | None = None
+
+        self._event_index = 0
+        self._trade_index = 0
+
+        # --- F-FLOW: cumulative delta ---------------------------------------------------------
+        self._cumulative_delta = 0.0
+        self._cd_unknown_excluded_count = 0
+
+        # --- F-FLOW / F-RESPONSE / F-LIQUIDITY: trade-count sliding windows ---------------------
+        self._pairs: dict[int, _SlidingPair] = {n: _SlidingPair(n) for n in _WINDOW_SIZES}
+        self._share_windows: dict[int, _ShareWindow] = {
+            s: _ShareWindow(s) for s in _SHARE_WINDOW_SIZES
+        }
+
+        # --- F-FLOW: same-side run length --------------------------------------------------------
+        self._run_side: str | None = None
+        self._run_length = 0
+
+        # --- F-FLOW: volume-burst non-overlapping baseline tiles ---------------------------------
+        self._tile_accum: dict[int, float] = {n: 0.0 for n in _WINDOW_SIZES}
+        self._tile_count: dict[int, int] = {n: 0 for n in _WINDOW_SIZES}
+        self._tile_history: dict[int, Deque[float]] = {
+            n: deque(maxlen=mf.BURST_BASELINE_TRAILING_WINDOWS) for n in _WINDOW_SIZES
+        }
+
+        # --- F-RESPONSE: deferred response_asymmetry -----------------------------------------------
+        self._response_pending: list[dict] = []
+
+        # --- F-LIQUIDITY: deferred refill_consistent (per side) + quote-depletion runs ------------
+        self._refill_pending: dict[str, list[dict]] = {"bid": [], "ask": []}
+        self._depletion_run: dict[str, dict | None] = {"bid": None, "ask": None}
+
+        # Completions resolved by the quote stream, waiting to attach to the next-built row.
+        self._pending_attachments: list[dict] = []
+
+        self._last_event_ts: float | None = None
+
+    # --- the engine-called hook ---------------------------------------------------------------
+
+    def on_event(self, event: Event, snapshot) -> None:
+        """The engine's ONE call-in. Records any exception on ``self.failure`` and stops consuming
+        (a state machine that already raised cannot honestly keep accumulating rows) so the
+        snapshot builder can refuse to persist a truncated stream -- see ``MicroObserverFailure``.
+        The engine itself is unaffected either way, exactly as its own isolation guarantees."""
+        if self.failure is not None:
+            return
+        try:
+            self._consume(event, snapshot)
+        except Exception as exc:  # noqa: BLE001 -- recorded here, surfaced by build_snapshot_rows
+            self.failure = exc
+
+    def _consume(self, event: Event, snapshot) -> None:
+        self._last_event_ts = event.timestamp
+        # The TRUE overall event ordinal ("i" in spec section 2.2's "row i is a pure function of
+        # events 1..i") -- counts EVERY event, quotes included, even though only trades ever get
+        # their own row; a row's own ``event_index`` is therefore the ordinal of the STREAM
+        # position it was built at, distinct from ``trade_index`` (that trade's own ordinal among
+        # trades only).
+        self._event_index += 1
+        if isinstance(event, QuoteEvent):
+            self._on_quote(event)
+            return
+        if isinstance(event, TradeEvent):
+            self._on_trade(event, snapshot)
+
+    # --- quote handling: side_source mirror state + the two quote-driven deferred families -------
+
+    def _on_quote(self, event: QuoteEvent) -> None:
+        self._advance_depletion_run("bid", event.bid, event.bid_size, event.timestamp)
+        self._advance_depletion_run("ask", event.ask, event.ask_size, event.timestamp)
+        self._advance_refill_pending("bid", event.bid, event.bid_size, event.timestamp)
+        self._advance_refill_pending("ask", event.ask, event.ask_size, event.timestamp)
+        self._current_quote = event
+        self._current_bid_size = event.bid_size
... [diff_bound] apps/backend/app/research/micro_observer.py: 367 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/micro_snapshots.py b/apps/backend/app/research/micro_snapshots.py
new file mode 100644
index 0000000..0ab9829
--- /dev/null
+++ b/apps/backend/app/research/micro_snapshots.py
@@ -0,0 +1,517 @@
+"""``micro_snapshots.py`` -- Era "The Rapid Microscope" J-02: snapshot identity + load-time
+
+verification (``docs/rapid-validation-spec.md`` section 2.3), persistence, the single-flight
+compute manager + CLI (the shipped desk pattern: ``desk_forward_compute.py`` /
+``desk_playbook_compute.py`` -- one in-flight job slot, an in-memory progress snapshot, cooperative
+cancel, no new pattern invented), and the section 2.4 granularity-benchmark helpers.
+
+**Storage shape.** One snapshot = two sibling files under the resolved snapshots directory: a
+row-oriented ``<dataset_id>.jsonl`` (one ``micro_observer.MicroObserver`` row per line -- JSONL,
+not one giant JSON array, so a build WRITES streaming and a future reader can iterate without
+loading the whole file) and a small ``<dataset_id>.meta.json`` sidecar (the identity tuple +
+``row_count``/``bytes_on_disk``/``built_utc``/``quote_size_unit`` -- exactly what
+``GET /research/desk/micro/snapshots`` serves; the boundary note in the iteration spec is explicit
+that this route serves BUILD METADATA only, never raw per-event rows -- an origin-fenced,
+event-level reader is ``micro_accessor.py``'s exclusive door, J-05, not built here).
+
+**Derived, rebuildable, owns nothing** (spec section 2.3) -- exactly the ``dataset_index.py`` /
+``tradability_cache.py`` discipline applied to a bigger artifact: losing every snapshot file loses
+nothing irreplaceable, the next build reproduces it byte-identically from the immutable dataset +
+the frozen algorithm. There is therefore no tamper checksum ON the meta file itself (unlike
+``datasets.py``'s own irreplaceable recordings) -- staleness is instead caught by RE-VERIFYING the
+three identity components spec section 2.3 names (``dataset_checksum``, ``config_fingerprint``,
+``feature_source_hash``) against a FRESH computation on every load; any mismatch is an honest
+cache MISS (rebuild), never a served stale value (TR-7)."""
+
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import os
+import threading
+import uuid
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Callable
+
+from ..config import CONFIG, Config
+from . import micro_features as mf
+from . import micro_observer as mo
+from .datasets import DatasetNotFound, DatasetStore
+from .micro_observer import MicroObserver, MicroObserverFailure
+
+__all__ = [
+    "SNAPSHOT_FORMAT_VERSION",
+    "MicroSnapshotIntegrityError",
+    "MicroObserverFailure",
+    "resolve_micro_snapshots_dir",
+    "feature_source_hash",
+    "snapshot_identity",
+    "quote_size_unit_for_dataset",
+    "build_snapshot_rows",
+    "write_snapshot",
+    "load_snapshot_meta",
+    "list_snapshot_meta",
+    "run_snapshot_build_and_record",
+    "MicroSnapshotComputeManager",
+    "append_run_log",
+    "read_run_log",
+]
+
+# spec section 2.4's benchmark pins this; see scripts/micro_snapshot_granularity_benchmark.py and
+# the dev handoff's measured table.
+SNAPSHOT_FORMAT_VERSION = "micro-snapshot-v1"
+
+_SNAPSHOTS_DIR_ENV = "TAPEOLOGY_MICRO_SNAPSHOTS_DIR"
+
+_IDENTITY_KEYS = (
+    "dataset_checksum",
+    "micro_algo_version",
+    "snapshot_format_version",
+    "feature_source_hash",
+    "config_fingerprint",
+    "params_hash",
+)
+
+
+class MicroSnapshotIntegrityError(Exception):
+    """A snapshot meta file failed its on-load shape check -- corrupted or tampered, surfaced
+    explicitly (the ``datasets.DatasetIntegrityError`` discipline, reused in spirit -- module
+    docstring; a distinct class because a snapshot is a different failure domain, the codebase's
+    own one-exception-class-per-module-domain convention)."""
+
+
+def resolve_micro_snapshots_dir(dataset_dir_resolved: str) -> str:
+    """``TAPEOLOGY_MICRO_SNAPSHOTS_DIR`` if set, else a ``micro_snapshots`` SIBLING of the
+    caller's already-resolved dataset directory -- the ``resolve_desk_playbook_dir`` pattern,
+    deliberately NOT a ``Config`` field (the ``TAPEOLOGY_MICRO_*`` family, goal.md Constraints)."""
+    override = os.environ.get(_SNAPSHOTS_DIR_ENV)
+    if override:
+        return override
+    return str(Path(dataset_dir_resolved).parent / "micro_snapshots")
+
+
+_IDENTITY_SOURCE_MODULES = (mf, mo)
+
+
+def feature_source_hash() -> str:
+    """sha256 over the source bytes of EVERY module a persisted row's values depend on, hashed in
+    the fixed ``_IDENTITY_SOURCE_MODULES`` order -- the early-warning for ANY constant/formula
+    change (TR-7); recomputed fresh on every call, never cached, since it must reflect whatever
+    code is ACTUALLY running right now.
+
+    Spec section 2.3 names "sha256 over the feature-module bytes"; the arithmetic lives in
+    ``micro_features.py`` but the values that actually LAND in a row are produced by
+    ``micro_observer.py``'s streaming state machine (the windows, the cumulative accumulators, the
+    deferred-construct resolution, the section 2.6 emission gate). Hashing only the former left a
+    real hole: an observer-only edit CHANGES every stored row's values while every stored identity
+    still verifies, so the corpus would be served as valid against code that no longer produces it.
+    Covering both is strictly MORE conservative than the spec's literal wording -- it can only ever
+    turn a would-be hit into an honest MISS (rebuild), never the reverse -- which is the
+    fail-closed direction section 2.3 exists to guarantee."""
+    digest = hashlib.sha256()
+    for module in _IDENTITY_SOURCE_MODULES:
+        digest.update(Path(module.__file__).read_bytes())
+    return digest.hexdigest()
+
+
+def quote_size_unit_for_dataset(dataset_meta: dict) -> str:
+    """spec section 2.6: every LEGACY dataset (none carries a recorded verification act) is
+    ``"unverified"``. Forward-compatible with a FUTURE (J-06) recorder that stamps
+    ``dataset_meta["quote_size_unit"]`` at record time -- read verbatim when present, defaulted to
+    ``"unverified"`` when absent (every dataset on disk today)."""
+    return dataset_meta.get("quote_size_unit", "unverified")
+
+
+def snapshot_identity(dataset_meta: dict, config: Config) -> dict:
+    """The section 2.3 seven-component identity tuple (as a dict; ``dataset_id`` plus the six
+    ``_IDENTITY_KEYS`` re-verified on every load)."""
+    return {
+        "dataset_id": dataset_meta["id"],
+        "dataset_checksum": dataset_meta["checksum"],
+        "micro_algo_version": mf.MICRO_ALGO_VERSION,
+        "snapshot_format_version": SNAPSHOT_FORMAT_VERSION,
+        "feature_source_hash": feature_source_hash(),
+        "config_fingerprint": config.config_fingerprint(),
+        "params_hash": mf.micro_parameters_hash(),
+    }
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def _rows_path(root: Path, dataset_id: str) -> Path:
+    return root / f"{dataset_id}.jsonl"
+
+
+def _meta_path(root: Path, dataset_id: str) -> Path:
+    return root / f"{dataset_id}.meta.json"
+
+
+# --- build (the ONE replay pass, per the additive observer= seam) --------------------------------
+
+
+def build_snapshot_rows(
+    dataset_store: DatasetStore, dataset_id: str, config: Config, *, quote_size_unit: str
+) -> list[dict]:
+    """The ONE replay pass (spec section 2.1): attach a fresh ``MicroObserver`` to
+    ``DatasetStore.replay``, drain it to completion, then ``finalize()`` to sweep any still-
+    pending deferred construct into an honest ``unavailable`` close-out (module docstring of
+    ``micro_observer.py``). Never a second replay implementation.
+
+    Refuses (``MicroObserverFailure``) if the observer raised anywhere mid-stream: the engine
+    isolates observer exceptions by design, so WITHOUT this check a failed stream would be
+    persisted as a silently TRUNCATED snapshot and identity-verified as complete. Nothing is
+    written on that path -- fail-closed, the compute manager surfaces it as ``state: "failed"``
+    with the error verbatim."""
+    observer = MicroObserver(quote_size_unit=quote_size_unit)
+    for _snapshot in dataset_store.replay(dataset_id, config, observer=observer):
+        pass
+    if observer.failure is not None:
+        raise MicroObserverFailure(
+            f"the micro observer failed while streaming dataset '{dataset_id}' "
+            f"({type(observer.failure).__name__}: {observer.failure}) -- refusing to persist a "
+            "partial snapshot"
+        ) from observer.failure
+    observer.finalize()
+    return observer.rows
+
+
+def write_snapshot(root_dir: str, dataset_id: str, rows: list[dict], identity_and_unit: dict) -> dict:
+    """Persist ONE snapshot: the JSONL rows file, then the meta sidecar (``row_count``/
+    ``bytes_on_disk``/``built_utc`` computed from what was ACTUALLY written, never estimated)."""
+    root = Path(root_dir)
+    root.mkdir(parents=True, exist_ok=True)
+    rows_path = _rows_path(root, dataset_id)
+    with rows_path.open("w", encoding="utf-8") as fh:
+        for row in rows:
+            fh.write(json.dumps(row, sort_keys=True))
+            fh.write("\n")
+    meta = {
+        **identity_and_unit,
+        "row_count": len(rows),
+        "bytes_on_disk": rows_path.stat().st_size,
+        "built_utc": _iso_utc_now(),
+    }
+    _meta_path(root, dataset_id).write_text(json.dumps(meta, sort_keys=True))
+    return meta
+
+
+# --- load, with re-verification (TR-7) ------------------------------------------------------------
+
+
+def load_snapshot_meta(
+    root_dir: str, dataset_store: DatasetStore, dataset_id: str, config: Config
+) -> dict | None:
+    """The stored meta dict IFF it exists AND its identity still matches a FRESH computation of
+    the dataset's current checksum + the current ``config_fingerprint`` + the current
+    ``feature_source_hash`` (and the algo/format-version/params-hash components too, for full
+    honesty) -- else ``None``, an honest cache MISS meaning "rebuild, never serve stale" (TR-7).
+    A malformed meta FILE (present but unparseable) is a distinct, louder failure -- corruption,
+    not staleness -- surfaced as ``MicroSnapshotIntegrityError``, never silently treated as a
+    miss."""
+    meta_path = _meta_path(Path(root_dir), dataset_id)
+    if not meta_path.exists():
+        return None
+    try:
+        stored = json.loads(meta_path.read_text())
+    except (OSError, ValueError) as exc:
+        raise MicroSnapshotIntegrityError(
+            f"snapshot meta file for '{dataset_id}' is not parseable ({exc}) -- corrupted or tampered"
+        ) from exc
+    try:
+        dataset_meta = dataset_store.get(dataset_id)
+    except DatasetNotFound:
+        return None  # the underlying dataset vanished -- nothing to verify against; an honest miss
+    current = snapshot_identity(dataset_meta, config)
+    for key in _IDENTITY_KEYS:
+        if stored.get(key) != current[key]:
+            return None  # MISS -- rebuild rather than serve stale (TR-7)
+    return stored
+
+
+def list_snapshot_meta(root_dir: str, dataset_store: DatasetStore, config: Config) -> list[dict]:
+    """Every CURRENTLY VALID (identity re-verified) snapshot's meta, sorted by ``dataset_id`` for
+    deterministic ordering. A stale meta file (present but no longer identity-matching) is
+    silently excluded -- exactly the honest "never serve stale" TR-7 discipline applied to the
+    listing surface, not merely the single-dataset loader."""
+    root = Path(root_dir)
+    if not root.exists():
+        return []
+    out: list[dict] = []
+    for meta_file in sorted(root.glob("*.meta.json")):
+        dataset_id = meta_file.name[: -len(".meta.json")]
+        meta = load_snapshot_meta(root_dir, dataset_store, dataset_id, config)
+        if meta is not None:
+            out.append(meta)
+    out.sort(key=lambda m: m["dataset_id"])
+    return out
+
+
+# --- the run-and-record orchestration (reuse-or-build per dataset) -------------------------------
+
+
+def run_snapshot_build_and_record(
+    dataset_store: DatasetStore,
+    config: Config,
+    root_dir: str,
+    dataset_ids: list[str] | None = None,
+    *,
+    progress: Callable[[str], None] | None = None,
+    should_abort: Callable[[], bool] | None = None,
+) -> list[dict]:
+    """Builds (or REUSES, if a currently-valid snapshot already exists -- ``load_snapshot_meta``)
+    a snapshot for every id in ``dataset_ids`` (default: every dataset currently in the store, in
+    ``DatasetStore.list()``'s own oldest-first order), returning each result's meta dict in order.
+    A requested abort is honoured at DATASET boundaries only -- the current dataset's build always
+    completes or is skipped-as-already-done; nothing is ever recorded half-built."""
+    if dataset_ids is None:
+        records, _errors = dataset_store.list()
+        dataset_ids = [r["id"] for r in records]
+    results: list[dict] = []
+    for dataset_id in dataset_ids:
+        if should_abort is not None and should_abort():
+            break
+        existing = load_snapshot_meta(root_dir, dataset_store, dataset_id, config)
+        if existing is not None:
+            results.append(existing)
+        else:
+            dataset_meta = dataset_store.get(dataset_id)
+            quote_size_unit = quote_size_unit_for_dataset(dataset_meta)
+            rows = build_snapshot_rows(dataset_store, dataset_id, config, quote_size_unit=quote_size_unit)
+            identity = snapshot_identity(dataset_meta, config)
+            meta = write_snapshot(root_dir, dataset_id, rows, {**identity, "quote_size_unit": quote_size_unit})
+            results.append(meta)
+        if progress is not None:
+            progress(dataset_id)
+    return results
+
+
+# --- the durable run log (GET .../snapshots/runs) --------------------------------------------------
+
+
+def _runs_log_path(root_dir: str) -> Path:
+    return Path(root_dir) / "runs.jsonl"
+
+
+def append_run_log(root_dir: str, entry: dict) -> None:
+    """Append ONE terminal run outcome -- a plain JSONL append-only history (a build-run log, not
+    a research evidence ledger; no hash-chaining -- that discipline belongs to ledgers research
+    CLAIMS depend on, e.g. ``scout_ledger.py``, not this operational build-progress record)."""
+    path = _runs_log_path(root_dir)
+    path.parent.mkdir(parents=True, exist_ok=True)
+    with path.open("a", encoding="utf-8") as fh:
+        fh.write(json.dumps(entry, sort_keys=True))
+        fh.write("\n")
+
+
+def read_run_log(root_dir: str, *, limit: int = 50) -> list[dict]:
+    """The most recent ``limit`` runs, NEWEST FIRST. A missing/corrupted log is an honest empty
+    list (a build-run history is convenience bookkeeping, never a claim of record -- unlike a
+    dataset or a ledger, losing it loses nothing the snapshots themselves do not already prove)."""
+    path = _runs_log_path(root_dir)
+    if not path.exists():
+        return []
+    try:
+        lines = path.read_text().splitlines()
+    except OSError:
+        return []
+    out: list[dict] = []
+    for line in lines:
+        line = line.strip()
+        if not line:
+            continue
+        try:
+            out.append(json.loads(line))
+        except ValueError:
+            continue
+    out.reverse()
+    return out[:limit]
+
+
+# --- the single-flight compute manager (the desk_forward_compute / desk_playbook_compute pattern) -
+
+
+_IDLE_SNAPSHOT: dict = {
+    "run_id": None,
+    "state": "idle",
+    "progress": {"datasets_total": 0, "datasets_done": 0, "current_dataset_id": None},
+    "started_utc": None,
+    "finished_utc": None,
+    "error": None,
+}
+
+
+class MicroSnapshotComputeManager:
+    """Owns the SINGLE in-flight (or last-terminal) snapshot-build job for this process. Construct
+    with no arguments -- every ``trigger()`` call takes its stores/config/dataset-ids explicitly
+    (the ``DeskPlaybookComputeManager`` per-call-injection precedent)."""
+
+    def __init__(self) -> None:
+        self._lock = threading.Lock()
+        self._snapshot: dict = dict(_IDLE_SNAPSHOT)
+        self._run_id: str | None = None
+        self._cancel_event: threading.Event | None = None
+        self._thread: threading.Thread | None = None
+
+    def snapshot(self) -> dict:
+        with self._lock:
+            return dict(self._snapshot)
+
+    def trigger(
+        self,
+        dataset_store: DatasetStore,
+        config: Config,
+        root_dir: str,
+        dataset_ids: list[str] | None = None,
+    ) -> dict:
+        """Start a NEW build job, or -- if one is already ``state == "running"`` -- refuse
+        (single-flight, process-wide). Never blocks: the walk runs on a dedicated worker thread."""
+        with self._lock:
+            if self._snapshot["state"] == "running":
+                return {"state": "refused", "reason": "already_running"}
+
+            if dataset_ids is None:
+                records, _errors = dataset_store.list()
+                resolved_ids = [r["id"] for r in records]
+            else:
+                resolved_ids = list(dataset_ids)
+
+            run_id = uuid.uuid4().hex
+            self._run_id = run_id
+            cancel_event = threading.Event()
+            self._cancel_event = cancel_event
+            self._snapshot = {
+                "run_id": run_id,
+                "state": "running",
+                "progress": {
+                    "datasets_total": len(resolved_ids),
+                    "datasets_done": 0,
+                    "current_dataset_id": resolved_ids[0] if resolved_ids else None,
+                },
+                "started_utc": _iso_utc_now(),
... [diff_bound] apps/backend/app/research/micro_snapshots.py: 123 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/micro_snapshot_granularity_benchmark.py b/apps/backend/scripts/micro_snapshot_granularity_benchmark.py
new file mode 100644
index 0000000..cdea1a1
--- /dev/null
+++ b/apps/backend/scripts/micro_snapshot_granularity_benchmark.py
@@ -0,0 +1,220 @@
+"""Era "The Rapid Microscope" J-02, spec section 2.4: the ONE-TIME granularity-decision benchmark.
+
+Before ``SNAPSHOT_FORMAT_VERSION`` is frozen, this script measures THREE candidate snapshot
+representations on >=2 real datasets (including the largest on disk, NVDA ``72ca8bc0``) for bytes-
+on-disk amplification vs. the raw dataset, one-pass build time, and anchor-query latency:
+
+  A. **per-event rows** -- one row for EVERY raw event (trade AND quote).
+  B. **per-event sampled-at-anchors** -- one row per TRADE only (the "anchor" the whole research
+     question is built around -- spec section 4's outcomes, the observer's own row model); quotes
+     update internal state but never get a row of their own. This is what
+     ``micro_observer.MicroObserver``/``micro_snapshots.py`` ALREADY ship as the production
+     representation -- this script reuses the REAL built snapshot file directly for B's numbers
+     (a second, throwaway implementation of the SAME representation would defeat the point of a
+     fair comparison).
+  C. **fixed-stride event blocks** -- one SUMMARY row every ``STRIDE`` raw events (first/last
+     price, volume, trade count over the block), the coarsest, boundedly-sized candidate.
+
+This is exploratory, throwaway measurement code -- not the shipped observer -- run once via
+``python -m scripts.micro_snapshot_granularity_benchmark`` (or directly) against the REAL
+``apps/backend/.data/datasets`` store, never through the browser-QA lane and never in the hermetic
+pytest suite (module docstring rationale in ``micro_snapshots.py``). The measured table is recorded
+verbatim in ``docs/handoffs/goal-rapid-microscope-iter-2-dev.md``.
+"""
+
+from __future__ import annotations
+
+import json
+import sys
+import time
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
+
+from app.config import CONFIG  # noqa: E402
+from app.providers.base import QuoteEvent, TradeEvent  # noqa: E402
+from app.research import micro_snapshots as ms  # noqa: E402
+from app.research.datasets import DatasetStore  # noqa: E402
+from app.research.micro_observer import MicroObserver  # noqa: E402
+
+STRIDE = 200  # Rep C's fixed stride (events per summary block) -- arbitrary-but-fixed for THIS
+# one-time measurement only (never a shipped constant; the winning representation's own constants
+# are spec section 1's, in micro_features.py).
+
+
+def _raw_dataset_bytes(dataset_dir: str, dataset_id: str) -> int:
+    return (Path(dataset_dir) / f"{dataset_id}.json").stat().st_size
+
+
+def _rep_a_per_event_rows(store: DatasetStore, dataset_id: str, config, out_path: Path) -> tuple[float, int]:
+    """Every event gets a row: trade rows are the REAL full feature row; quote rows are a smaller
+    liquidity-only projection (ts/bid/ask/sizes/quote_imbalance/microprice) -- still genuinely
+    computed and written, not fabricated."""
+    observer = MicroObserver(quote_size_unit="unverified")
+    quote_rows: list[dict] = []
+
+    def _on_event_wrapper(event, snapshot, _orig=observer.on_event):
+        _orig(event, snapshot)
+        if isinstance(event, QuoteEvent):
+            imbalance = None
+            microprice = None
+            total = event.bid_size + event.ask_size
+            if total > 0:
+                imbalance = (event.bid_size - event.ask_size) / total
+                microprice = (event.ask * event.bid_size + event.bid * event.ask_size) / total
+            quote_rows.append(
+                {
+                    "ts": event.timestamp, "bid": event.bid, "ask": event.ask,
+                    "bid_size": event.bid_size, "ask_size": event.ask_size,
+                    "quote_imbalance": imbalance, "microprice": microprice,
+                }
+            )
+
+    observer.on_event = _on_event_wrapper  # type: ignore[method-assign]
+    t0 = time.time()
+    for _snap in store.replay(dataset_id, config, observer=observer):
+        pass
+    observer.finalize()
+    all_rows = sorted(observer.rows + quote_rows, key=lambda r: r["ts"] if "ts" in r else r["anchor_at"])
+    with out_path.open("w") as fh:
+        for row in all_rows:
+            fh.write(json.dumps(row, sort_keys=True))
+            fh.write("\n")
+    build_seconds = time.time() - t0
+    return build_seconds, len(all_rows)
+
+
+def _rep_c_fixed_stride_blocks(store: DatasetStore, dataset_id: str, config, out_path: Path) -> tuple[float, int]:
+    """One summary row every STRIDE raw events (trade+quote alike): first/last trade price seen in
+    the block, block volume, trade count, and the block's end timestamp."""
+    t0 = time.time()
+    block_rows: list[dict] = []
+    block_first_price: float | None = None
+    block_last_price: float | None = None
+    block_volume = 0
+    block_trades = 0
+    block_end_ts = 0.0
+    n = 0
+    for event in store.load_events(dataset_id):
+        n += 1
+        block_end_ts = event.timestamp
+        if isinstance(event, TradeEvent):
+            block_trades += 1
+            block_volume += event.size
+            if block_first_price is None:
+                block_first_price = event.price
+            block_last_price = event.price
+        if n % STRIDE == 0:
+            block_rows.append(
+                {
+                    "block_end_ts": block_end_ts, "first_price": block_first_price,
+                    "last_price": block_last_price, "volume": block_volume, "trade_count": block_trades,
+                }
+            )
+            block_first_price = None
+            block_last_price = None
+            block_volume = 0
+            block_trades = 0
+    if block_trades or block_volume:
+        block_rows.append(
+            {
+                "block_end_ts": block_end_ts, "first_price": block_first_price,
+                "last_price": block_last_price, "volume": block_volume, "trade_count": block_trades,
+            }
+        )
+    with out_path.open("w") as fh:
+        for row in block_rows:
+            fh.write(json.dumps(row, sort_keys=True))
+            fh.write("\n")
+    build_seconds = time.time() - t0
+    return build_seconds, len(block_rows)
+
+
+def _query_latency_seconds(jsonl_path: Path, ts_key: str, probe_ts: float, trials: int = 200) -> float:
+    """Anchor-query latency: load the (ts-sorted) rows once, then time ``trials`` binary searches
+    for the row nearest a probe timestamp -- a fair, representation-agnostic proxy (fewer/lighter
+    rows search faster)."""
+    rows = [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]
+    stamps = [r[ts_key] for r in rows]
+    import bisect
+
+    t0 = time.time()
+    for i in range(trials):
+        probe = probe_ts * (0.2 + 0.6 * (i / max(trials - 1, 1)))
+        bisect.bisect_left(stamps, probe)
+    return (time.time() - t0) / trials
+
+
+def benchmark_one(dataset_id: str, label: str, work_dir: Path) -> dict:
+    store = DatasetStore(CONFIG.dataset_dir)
+    dataset_meta = store.get(dataset_id)
+    raw_bytes = _raw_dataset_bytes(CONFIG.dataset_dir, dataset_id)
+
+    # --- Rep B: REUSE the real, already-shipped observer output (see module docstring) ---------
+    snapshots_dir = ms.resolve_micro_snapshots_dir(CONFIG.dataset_dir)
+    rep_b_meta = ms.load_snapshot_meta(snapshots_dir, store, dataset_id, CONFIG)
+    if rep_b_meta is None:
+        t0 = time.time()
+        rows = ms.build_snapshot_rows(store, dataset_id, CONFIG, quote_size_unit="unverified")
+        rep_b_build_seconds = time.time() - t0
+        rep_b_meta = ms.write_snapshot(snapshots_dir, dataset_id, rows, {**ms.snapshot_identity(dataset_meta, CONFIG), "quote_size_unit": "unverified"})
+    else:
+        rep_b_build_seconds = None  # reused -- see the dev handoff for a from-scratch timing note
+    rep_b_path = Path(snapshots_dir) / f"{dataset_id}.jsonl"
+    rep_b_latency = _query_latency_seconds(rep_b_path, "anchor_at", dataset_meta["event_counts"]["total"])
+
+    # --- Rep A: per-event rows ------------------------------------------------------------------
+    # anchor_at exists on trade rows but not quote rows in rep A -- every row carries EITHER key.
+    rep_a_path = work_dir / f"{dataset_id}.rep_a.jsonl"
+    rep_a_seconds, rep_a_count = _rep_a_per_event_rows(store, dataset_id, CONFIG, rep_a_path)
+    rep_a_rows = [json.loads(line) for line in rep_a_path.read_text().splitlines() if line.strip()]
+    rep_a_stamps = sorted(r.get("anchor_at", r.get("ts")) for r in rep_a_rows)
+    import bisect
+
+    t0 = time.time()
+    for i in range(200):
+        probe = dataset_meta["event_counts"]["total"] * (0.2 + 0.6 * (i / 199))
+        bisect.bisect_left(rep_a_stamps, probe)
+    rep_a_latency = (time.time() - t0) / 200
+
+    # --- Rep C: fixed-stride blocks -----------------------------------------------------------
+    rep_c_path = work_dir / f"{dataset_id}.rep_c.jsonl"
+    rep_c_seconds, rep_c_count = _rep_c_fixed_stride_blocks(store, dataset_id, CONFIG, rep_c_path)
+    rep_c_latency = _query_latency_seconds(rep_c_path, "block_end_ts", dataset_meta["event_counts"]["total"])
+
+    return {
+        "dataset_id": dataset_id, "label": label,
+        "raw_bytes": raw_bytes, "raw_events": dataset_meta["event_counts"]["total"],
+        "raw_trades": dataset_meta["event_counts"]["trades"],
+        "rep_a": {
+            "row_count": rep_a_count, "bytes": rep_a_path.stat().st_size,
+            "amplification": rep_a_path.stat().st_size / raw_bytes,
+            "build_seconds": rep_a_seconds, "query_latency_seconds": rep_a_latency,
+        },
+        "rep_b": {
+            "row_count": rep_b_meta["row_count"], "bytes": rep_b_meta["bytes_on_disk"],
+            "amplification": rep_b_meta["bytes_on_disk"] / raw_bytes,
+            "build_seconds": rep_b_build_seconds, "query_latency_seconds": rep_b_latency,
+        },
+        "rep_c": {
+            "row_count": rep_c_count, "bytes": rep_c_path.stat().st_size,
+            "amplification": rep_c_path.stat().st_size / raw_bytes,
+            "build_seconds": rep_c_seconds, "query_latency_seconds": rep_c_latency,
+        },
+    }
+
+
+def main() -> int:
+    work_dir = Path(CONFIG.dataset_dir).parent / "micro_snapshot_benchmark_tmp"
+    work_dir.mkdir(parents=True, exist_ok=True)
+    targets = [
+        ("72ca8bc0e5d24e40bef8d2dc6c0fe44b", "NVDA (largest, 1.97M events)"),
+        ("dcfcf3cd58184c12bf2db98ed08a2bf7", "PG (14,241 events, the dense_replay_gate twin)"),
+    ]
+    results = [benchmark_one(dsid, label, work_dir) for dsid, label in targets]
+    print(json.dumps(results, indent=2, default=str))
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_micro_features.py b/apps/backend/tests/test_micro_features.py
new file mode 100644
index 0000000..0bb9b38
--- /dev/null
+++ b/apps/backend/tests/test_micro_features.py
@@ -0,0 +1,425 @@
+"""``micro_features.py`` (Era "The Rapid Microscope" J-02) -- hand-derived oracle fixtures for the
+pure per-value arithmetic (TR-16 feature-level vectors), the closed outcome set (spec section 4,
+TC-6/TR-17c), and the cross-basis unit gate (spec section 2.6, TC-7/TR-18).
+
+Test-first contract: TC-6 through TC-10 in ``docs/phases/goal-rapid-microscope-iter-2.md``. The
+STATEFUL streaming integration (cumulative delta, rolling windows, run length, the deferred
+constructs) is exercised through a real ``TapeEngine`` + ``MicroObserver`` in
+``test_micro_observer.py`` instead -- this file covers ONLY the stateless arithmetic each row's
+computation ultimately calls into."""
+
+from __future__ import annotations
+
+import pytest
+
+from app.research import micro_features as mf
+
+
+# --- F-FLOW: rolling_imbalance / dominant_side_volume_share / volume_burst -----------------------
+
+
+def test_rolling_imbalance_all_buy_is_one():
+    assert mf.rolling_imbalance(10, 0) == 1.0
+
+
+def test_rolling_imbalance_all_sell_is_minus_one():
+    assert mf.rolling_imbalance(0, 10) == -1.0
+
+
+def test_rolling_imbalance_balanced_is_zero():
+    assert mf.rolling_imbalance(5, 5) == 0.0
+
+
+def test_rolling_imbalance_no_directional_volume_is_none():
+    assert mf.rolling_imbalance(0, 0) is None
+
+
+def test_dominant_side_volume_share_hand_computed():
+    assert mf.dominant_side_volume_share(30, 10) == pytest.approx(0.75)
+    assert mf.dominant_side_volume_share(10, 30) == pytest.approx(0.75)
+
+
+def test_dominant_side_volume_share_no_volume_is_zero_not_none():
+    assert mf.dominant_side_volume_share(0, 0) == 0.0
+
+
+def test_volume_burst_hand_computed():
+    # baseline windows [100, 120, 90, 110, 105] -> median 105; window volume 210 -> 210/105 = 2.0
+    assert mf.volume_burst(210, [100, 120, 90, 110, 105]) == pytest.approx(2.0)
+
+
+def test_volume_burst_undefined_with_fewer_than_five_baseline_windows():
+    assert mf.volume_burst(100, [100, 100, 100, 100]) is None  # 4 windows -- undefined, counted
+    assert mf.volume_burst(100, []) is None
+
+
+def test_volume_burst_undefined_with_zero_median_baseline():
+    assert mf.volume_burst(100, [0, 0, 0, 0, 0]) is None
+
+
+# --- F-FLOW: price_extreme_trailing / divergence_at_level (Card 9.1, amended r2) ------------------
+
+
+def test_price_extreme_trailing_hand_computed():
+    history = [(0.0, 100.0), (30.0, 100.5), (60.0, 101.0), (90.0, 100.8)]
+    # tau=60, window [-60, 60] -> every point in range -> max = 101.0
+    assert mf.price_extreme_trailing(history, tau=60.0) == pytest.approx(101.0)
+    # tau=90, window [-30, 90] -> points at 30/60/90 in range (0.0 excluded) -> max = 101.0
+    assert mf.price_extreme_trailing(history, tau=90.0) == pytest.approx(101.0)
+
+
+def test_price_extreme_trailing_none_with_no_point_in_range():
+    history = [(0.0, 100.0)]
+    assert mf.price_extreme_trailing(history, tau=1000.0) is None
+
+
+def test_divergence_delta_threshold_hand_computed():
+    # median([1000, 1200, 900, 1100, 1000]) = 1000 -> 0.25 * 1000 = 250
+    assert mf.divergence_delta_threshold([1000, 1200, 900, 1100, 1000]) == pytest.approx(250.0)
+
+
+def test_divergence_at_level_bearish_when_price_higher_and_delta_collapses():
+    history = [
+        (0.0, 100.0), (30.0, 100.5), (60.0, 101.0),
+        (90.0, 100.8), (150.0, 101.5), (200.0, 102.0),
+    ]
+    result = mf.divergence_at_level(
+        price_history=history, tau1=60.0, tau2=200.0,
+        cum_delta_at_tau1=500.0, cum_delta_at_tau2=100.0,
+        baseline_volumes=[1000, 1200, 900, 1100, 1000],
+    )
+    assert result["price_extreme_tau1"] == pytest.approx(101.0)
+    assert result["price_extreme_tau2"] == pytest.approx(102.0)
+    assert result["delta_volume_fraction_threshold"] == pytest.approx(250.0)
+    # price made a higher high (102.0 > 101.0) AND CD(200)=100 <= CD(60)-delta=500-250=250 -> True
+    assert result["bearish_divergence"] is True
+    assert result["available_at"] == 200.0
+
+
+def test_divergence_at_level_false_when_delta_does_not_collapse_enough():
+    history = [(0.0, 100.0), (60.0, 101.0), (200.0, 102.0)]
+    result = mf.divergence_at_level(
+        price_history=history, tau1=60.0, tau2=200.0,
+        cum_delta_at_tau1=500.0, cum_delta_at_tau2=400.0,  # 400 > 250 -> condition fails
+        baseline_volumes=[1000, 1200, 900, 1100, 1000],
+    )
+    assert result["bearish_divergence"] is False
+
+
+def test_divergence_at_level_none_with_insufficient_baseline():
+    history = [(0.0, 100.0), (60.0, 101.0), (200.0, 102.0)]
+    result = mf.divergence_at_level(
+        price_history=history, tau1=60.0, tau2=200.0,
+        cum_delta_at_tau1=500.0, cum_delta_at_tau2=100.0,
+        baseline_volumes=[1000, 1200],  # only 2 windows -- undefined
+    )
+    assert result["delta_volume_fraction_threshold"] is None
+    assert result["bearish_divergence"] is None
+
+
+# --- F-RESPONSE: failed_aggression_score / impact_efficiency ---------------------------------------
+
+
+def test_failed_aggression_score_hand_computed():
+    # dominant_share=0.8, |delta|=2.5bps of a 5.0bps scale -> flatness=1-2.5/5.0=0.5 -> 0.8*0.5=0.4
+    assert mf.failed_aggression_score(0.8, 2.5) == pytest.approx(0.4)
+
+
+def test_failed_aggression_score_clamps_flatness_at_zero_for_a_large_move():
+    # |delta| = 10 bps > the 5.0 scale -> flatness clamps to 0.0 -> score 0.0 regardless of share
+    assert mf.failed_aggression_score(0.9, 10.0) == 0.0
+
+
+def test_failed_aggression_score_treats_no_measured_move_as_maximally_flat():
+    assert mf.failed_aggression_score(0.6, None) == pytest.approx(0.6)
+
+
+def test_impact_efficiency_hand_computed():
+    # 4.0 bps over 2,000 aggressive shares -> 4.0 / (2000/1000) = 2.0 bps per 1,000 shares
+    assert mf.impact_efficiency(4.0, 2000) == pytest.approx(2.0)
+
+
+def test_impact_efficiency_none_with_zero_aggressive_volume():
+    assert mf.impact_efficiency(4.0, 0) is None
+
+
+def test_impact_efficiency_none_with_no_measured_move():
+    assert mf.impact_efficiency(None, 2000) is None
+
+
+# --- F-LIQUIDITY: quote_imbalance / microprice / mid_price / bps_move ------------------------------
+
+
+def test_quote_imbalance_hand_computed():
+    assert mf.quote_imbalance(bid_size=300, ask_size=100) == pytest.approx(0.5)
+    assert mf.quote_imbalance(bid_size=100, ask_size=300) == pytest.approx(-0.5)
+
+
+def test_quote_imbalance_none_with_zero_total_size():
+    assert mf.quote_imbalance(0, 0) is None
+
+
+def test_microprice_hand_computed():
+    # bid=99.90 (size 300), ask=100.10 (size 100) -> (100.10*300 + 99.90*100) / 400
+    expected = (100.10 * 300 + 99.90 * 100) / 400
+    assert mf.microprice(bid=99.90, ask=100.10, bid_size=300, ask_size=100) == pytest.approx(expected)
+
+
+def test_mid_price_and_bps_move_hand_computed():
+    mid_start = mf.mid_price(99.98, 100.02)
+    mid_end = mf.mid_price(100.08, 100.12)
+    assert mid_start == pytest.approx(100.0)
+    assert mid_end == pytest.approx(100.10)
+    assert mf.bps_move(mid_start, mid_end) == pytest.approx(10.0)  # +0.10 on 100.0 = 10 bps
+
+
+def test_bps_move_none_with_missing_side():
+    assert mf.bps_move(None, 100.0) is None
+    assert mf.bps_move(100.0, None) is None
+
+
+# --- micro_parameters(): every constant embedded verbatim, moves when monkeypatched ----------------
+
+
+def test_micro_parameters_embeds_every_constant_it_uses():
+    params = mf.micro_parameters()
+    assert params["refill_m_quotes"] == mf.REFILL_M_QUOTES
+    assert params["response_k_trades"] == mf.RESPONSE_K_TRADES
+    assert params["burst_baseline_trailing_windows"] == mf.BURST_BASELINE_TRAILING_WINDOWS
+    assert params["depletion_window_quotes"] == mf.DEPLETION_WINDOW_QUOTES
+    assert params["impact_flatness_scale_bps"] == mf.IMPACT_FLATNESS_SCALE_BPS
+    assert params["divergence_trailing_seconds"] == mf.DIVERGENCE_TRAILING_SECONDS
+    assert params["divergence_delta_volume_fraction"] == mf.DIVERGENCE_DELTA_VOLUME_FRACTION
+
+
+def test_a_monkeypatched_constant_moves_the_parameters_hash(monkeypatch):
+    """The counter-test the goal.md Constraints section demands: a changed constant must move
+    BOTH the parameters dict AND its hash (never a stale hash over a changed formula)."""
+    before_params = mf.micro_parameters()
+    before_hash = mf.micro_parameters_hash()
+    monkeypatch.setattr(mf, "REFILL_M_QUOTES", mf.REFILL_M_QUOTES + 1)
+    after_params = mf.micro_parameters()
+    after_hash = mf.micro_parameters_hash()
+    assert after_params != before_params
+    assert after_hash != before_hash
+
+
+# --- the closed outcome set (spec section 4) --------------------------------------------------------
+
+
+def test_resolve_outcome_start_is_the_max_of_conditioning_available_at():
+    assert mf.resolve_outcome_start([10.0, 25.0, 5.0]) == 25.0
+
+
+def test_resolve_outcome_start_requires_at_least_one_instant():
+    with pytest.raises(ValueError):
+        mf.resolve_outcome_start([])
+
+
+def test_require_outcome_start_not_before_conditioning_passes_a_legal_start():
+    assert mf.require_outcome_start_not_before_conditioning(30.0, [10.0, 25.0]) == 30.0
+    assert mf.require_outcome_start_not_before_conditioning(25.0, [10.0, 25.0]) == 25.0  # equal is legal
+
+
+def test_tc6_planted_outcome_before_conditioning_max_is_refused():
+    """TC-6 / TR-17c: a planted outcome start earlier than the conditioning set's maximum
+    available_at is refused with a typed error, never silently measured early."""
+    with pytest.raises(mf.OutcomeRefused):
+        mf.require_outcome_start_not_before_conditioning(20.0, [10.0, 25.0])  # 20 < 25 -- illegal
+
+
+def test_mid_outcome_hand_computed_side_signed():
+    buy = mf.mid_outcome(
+        mid_at_start=100.0, mid_at_horizon=100.5, outcome_start=0.0, horizon_ts=30.0,
+        session_end_ts=100.0, side="buy",
+    )
+    assert buy == {
+        "basis": "mid", "outcome_start": 0.0, "horizon_ts": 30.0,
+        "value": pytest.approx(0.5), "unmeasured": False, "truncated": False,
+    }
+    sell = mf.mid_outcome(
+        mid_at_start=100.0, mid_at_horizon=100.5, outcome_start=0.0, horizon_ts=30.0,
+        session_end_ts=100.0, side="sell",
+    )
+    assert sell["value"] == pytest.approx(-0.5)  # sell-signed: the same raw move flips sign
+
+
+def test_mid_outcome_unmeasured_when_a_mid_is_missing():
+    result = mf.mid_outcome(
+        mid_at_start=None, mid_at_horizon=100.5, outcome_start=0.0, horizon_ts=30.0,
+        session_end_ts=100.0, side=None,
+    )
+    assert result["unmeasured"] is True
+    assert result["value"] is None
+
+
+def test_mid_outcome_truncated_when_horizon_exceeds_session_end():
+    result = mf.mid_outcome(
+        mid_at_start=100.0, mid_at_horizon=100.5, outcome_start=0.0, horizon_ts=150.0,
+        session_end_ts=100.0, side="buy",
+    )
+    assert result["truncated"] is True
+    assert result["value"] is None  # excluded, never measured past the session
+
+
+def test_last_trade_outcome_is_a_separately_named_basis_never_the_primary():
+    result = mf.last_trade_outcome(
+        price_at_start=50.0, price_at_horizon=50.25, outcome_start=0.0, horizon_ts=30.0,
+        session_end_ts=100.0, side="buy",
+    )
+    assert result["basis"] == "last_trade"
+    assert result["value"] == pytest.approx(0.25)
+
+
+# --- the section 2.6 cross-basis unit gate (TC-7 / TR-18) -------------------------------------------
+
+
+def test_is_verified_unit():
+    assert mf.is_verified_unit("shares") is True
+    assert mf.is_verified_unit("round_lots") is True
+    assert mf.is_verified_unit("unverified") is False
+
+
+def test_tc7_unverified_unit_refuses_cross_basis_feature():
+    with pytest.raises(mf.CrossBasisUnverifiedUnitError):
+        mf.execution_vs_replenishment_ratio(executed_volume=100, replenished_size=50, quote_size_unit="unverified")
+
+
+def test_tc7_verified_unit_serves_cross_basis_feature():
+    value = mf.execution_vs_replenishment_ratio(executed_volume=100, replenished_size=50, quote_size_unit="shares")
+    assert value == pytest.approx(2.0)
+    value2 = mf.execution_vs_replenishment_ratio(executed_volume=100, replenished_size=50, quote_size_unit="round_lots")
+    assert value2 == pytest.approx(2.0)
+
+
+def test_execution_vs_replenishment_ratio_none_with_zero_replenishment():
+    assert mf.execution_vs_replenishment_ratio(executed_volume=100, replenished_size=0, quote_size_unit="shares") is None
+
+
+def test_tc7_pooled_request_spanning_unverified_and_verified_is_refused_outright():
+    with pytest.raises(mf.CrossBasisUnverifiedUnitError):
+        mf.require_uniform_unit_for_pool(["shares", "unverified"])
+
+
+def test_tc7_pooled_request_of_a_single_unanimous_verified_unit_is_served():
+    assert mf.require_uniform_unit_for_pool(["shares", "shares"]) == "shares"
+
+
+def test_tc7_pooled_request_of_a_single_unanimous_but_unverified_unit_is_still_refused():
+    with pytest.raises(mf.CrossBasisUnverifiedUnitError):
+        mf.require_uniform_unit_for_pool(["unverified", "unverified"])
+
+
+def test_require_share_denominated_magnitude_allowed_mirrors_the_ratio_gate():
+    mf.require_share_denominated_magnitude_allowed("shares")  # does not raise
+    with pytest.raises(mf.CrossBasisUnverifiedUnitError):
+        mf.require_share_denominated_magnitude_allowed("unverified")
+
+
+def test_tr18_source_scan_every_function_referencing_quote_size_unit_is_gated():
+    """TR-18's source-scan requirement: no silent normalization path exists -- EVERY function
+    body in this module that reads ``quote_size_unit`` (a parameter or local named exactly that)
+    is either one of the gate functions themselves, or calls one of them before returning. An AST
+    walk (not a plain substring grep) so a comment or docstring mentioning the name cannot hide a
+    genuine violation, and a genuine violation cannot hide behind unusual formatting."""
+    import ast
+    import inspect
+
+    gate_names = {"require_verified_unit", "require_uniform_unit_for_pool", "is_verified_unit"}
+    tree = ast.parse(inspect.getsource(mf))
+
+    def _calls_a_gate(node: ast.AST) -> bool:
+        for child in ast.walk(node):
+            if isinstance(child, ast.Call):
+                func = child.func
+                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
+                if name in gate_names:
+                    return True
+        return False
+
+    violations: list[str] = []
+    for node in ast.walk(tree):
+        if not isinstance(node, ast.FunctionDef):
+            continue
+        if node.name in gate_names:
+            continue
+        param_names = {a.arg for a in node.args.args}
+        references_unit = "quote_size_unit" in param_names or any(
+            isinstance(n, ast.Name) and n.id == "quote_size_unit" for n in ast.walk(node)
+        )
+        if references_unit and not _calls_a_gate(node):
+            violations.append(node.name)
+    assert violations == [], f"ungated quote_size_unit reference(s): {violations}"
+
+
+def test_tr18_source_scan_every_streaming_emitter_of_a_share_denominated_magnitude_is_gated():
+    """TR-18's source-scan requirement extended to the STREAMING layer -- the half the scan above
+    structurally cannot see, since it walks only THIS module while the code that actually runs
+    against the 18 real (all ``unverified``) datasets lives in ``micro_observer.py``. Rule: every
+    function there that CONSTRUCTS a deferred completion whose ``kind`` is a cross-basis
+    share-denominated one (``CROSS_BASIS_SHARE_DENOMINATED_KINDS``) must call a section 2.6 gate in
+    its own body -- so a new emitter that attaches a raw magnitude ungated fails here rather than
+    silently persisting a share-denominated number for an unverified dataset. Scoped to the
+    EMITTERS (not to every reader of ``quote_size_unit``) deliberately: serving the unit as a row
+    LABEL is not arithmetic over it, and a rule that flagged the label would have to be muzzled by
+    an exemption list -- which is how a guard stops guarding."""
+    import ast
+    import inspect
+
+    from app.research import micro_observer
+
+    gate_names = {
+        "require_verified_unit",
+        "require_uniform_unit_for_pool",
+        "require_share_denominated_magnitude_allowed",
+        "is_verified_unit",
+    }
+    tree = ast.parse(inspect.getsource(micro_observer))
+
+    def _emits_a_cross_basis_kind(node: ast.AST) -> bool:
+        for child in ast.walk(node):
+            if not isinstance(child, ast.Dict):
+                continue
+            for key, value in zip(child.keys, child.values):
+                if (
+                    isinstance(key, ast.Constant)
+                    and key.value == "kind"
+                    and isinstance(value, ast.Constant)
+                    and value.value in mf.CROSS_BASIS_SHARE_DENOMINATED_KINDS
+                ):
+                    return True
+        return False
+
+    def _calls_a_gate(node: ast.AST) -> bool:
+        for child in ast.walk(node):
... [diff_bound] apps/backend/tests/test_micro_features.py: 31 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_micro_observer.py b/apps/backend/tests/test_micro_observer.py
new file mode 100644
index 0000000..89996e2
--- /dev/null
+++ b/apps/backend/tests/test_micro_observer.py
@@ -0,0 +1,526 @@
+"""``micro_observer.py`` (Era "The Rapid Microscope" J-02) -- the streaming state-machine's
+
+integration behavior over hand-crafted event sequences run through a REAL ``TapeEngine`` (the
+``test_observer_equivalence.py`` pattern: construct an engine, ``add_observer``, feed events one
+at a time via ``process_event``) plus the additive ``DatasetStore.replay(observer=...)`` wiring
+and the TR-1/TR-17a/TR-17b traps against a small REAL committed tick fixture. Test-first contract:
+TC-1, TC-2, TC-4, TC-5, TC-8, TC-9, TC-10 in ``docs/phases/goal-rapid-microscope-iter-2.md``."""
+
+from __future__ import annotations
+
+import json
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG
+from app.engine.tape_engine import TapeEngine
+from app.providers.base import QuoteEvent, Side, TradeEvent
+from app.research import micro_features as mf
+from app.research.datasets import DatasetStore
+from app.research.micro_observer import MicroObserver
+
+TICKER = "TEST"
+SCENARIO = "test scenario"
+
+_SMALL_FIXTURE = Path(__file__).parent / "fixtures" / "datasets" / "6c9bf2c700d749e0993efd92c5807de3.json"
+
+
+def _run(events: list, quote_size_unit: str = "unverified") -> list[dict]:
+    """Feed ``events`` through a fresh engine + a fresh, attached ``MicroObserver``; return the
+    observer's rows after ``finalize()``."""
+    engine = TapeEngine(TICKER, SCENARIO, CONFIG)
+    observer = MicroObserver(quote_size_unit=quote_size_unit)
+    engine.add_observer(observer)
+    for event in events:
+        engine.process_event(event)
+    observer.finalize()
+    return observer.rows
+
+
+def _non_close_out(rows: list[dict]) -> list[dict]:
+    return [r for r in rows if not r.get("close_out")]
+
+
+# --- TC-1: the additive observer= kwarg on DatasetStore.replay --------------------------------------
+
+
+def _events_for_store() -> list:
+    return [
+        QuoteEvent(TICKER, 0.0, 99.99, 100.02, 100, 100),
+        TradeEvent(TICKER, 0.1, 100.03, 10, Side.UNKNOWN),  # engine classifies: >= ask -> BUY
+        TradeEvent(TICKER, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> SELL
+    ]
+
+
+def _plant(store: DatasetStore) -> dict:
+    return store.record(
+        symbol=TICKER, source="fixture", source_kind="fixture", source_id="fixture",
+        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(),
+    )
+
+
+class _ProbeObserver:
+    def __init__(self) -> None:
+        self.events: list = []
+
+    def on_event(self, event, snapshot) -> None:
+        self.events.append(event)
+
+
+def test_tc1_replay_with_no_observer_arg_is_unaffected(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    no_observer_snapshots = list(store.replay(meta["id"], CONFIG))
+    assert len(no_observer_snapshots) == 3
+    # A second no-observer replay reproduces byte-identical snapshots (determinism preserved).
+    again = list(store.replay(meta["id"], CONFIG))
+    assert [s.tape_state for s in no_observer_snapshots] == [s.tape_state for s in again]
+    assert [s.event_count for s in no_observer_snapshots] == [s.event_count for s in again]
+
+
+def test_tc1_probe_observer_fires_once_per_event_in_stored_order(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    probe = _ProbeObserver()
+    snapshots = list(store.replay(meta["id"], CONFIG, observer=probe))
+    assert len(probe.events) == 3 == len(snapshots)
+    assert [type(e).__name__ for e in probe.events] == ["QuoteEvent", "TradeEvent", "TradeEvent"]
+    assert [e.timestamp for e in probe.events] == [0.0, 0.1, 0.2]
+
+
+def test_tc1_attaching_a_micro_observer_does_not_change_the_replayed_snapshots(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    plain = list(store.replay(meta["id"], CONFIG))
+    observed = list(store.replay(meta["id"], CONFIG, observer=MicroObserver(quote_size_unit="unverified")))
+    assert [s.tape_state for s in plain] == [s.tape_state for s in observed]
+    assert [s.bid for s in plain] == [s.bid for s in observed]
+    assert [s.recent_trades for s in plain] == [s.recent_trades for s in observed]
+
+
+def test_micro_observer_produces_one_row_per_trade_never_per_quote(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    observer = MicroObserver(quote_size_unit="unverified")
+    for _snap in store.replay(meta["id"], CONFIG, observer=observer):
+        pass
+    observer.finalize()
+    assert len(_non_close_out(observer.rows)) == 2  # 2 TradeEvents, 1 QuoteEvent -- no quote row
+
+
+# --- F-FLOW: cumulative delta, same-side run length, rolling imbalance (TC-8) -----------------------
+
+
+def _flow_fixture_events() -> list:
+    return [
+        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),
+        TradeEvent(TICKER, 1.0, 100.10, 10, Side.UNKNOWN),  # >= ask -> BUY
+        TradeEvent(TICKER, 2.0, 100.10, 20, Side.UNKNOWN),  # >= ask -> BUY
+        TradeEvent(TICKER, 3.0, 100.00, 5, Side.UNKNOWN),  # <= bid -> SELL
+        TradeEvent(TICKER, 4.0, 100.10, 15, Side.UNKNOWN),  # >= ask -> BUY
+        TradeEvent(TICKER, 5.0, 100.00, 8, Side.UNKNOWN),  # <= bid -> SELL
+        TradeEvent(TICKER, 6.0, 100.00, 2, Side.UNKNOWN),  # <= bid -> SELL
+    ]
+
+
+def test_tc8_cumulative_delta_and_run_length_hand_computed():
+    rows = _non_close_out(_run(_flow_fixture_events()))
+    assert [r["side"] for r in rows] == ["buy", "buy", "sell", "buy", "sell", "sell"]
+    assert [r["cumulative_delta"] for r in rows] == [10.0, 30.0, 25.0, 40.0, 32.0, 30.0]
+    assert [r["same_side_run_length"] for r in rows] == [1, 2, 1, 1, 1, 2]
+    assert all(r["cumulative_delta_unknown_excluded_count"] == 0 for r in rows)
+
+
+def test_tc8_cumulative_delta_excludes_and_counts_unknown_sided_prints():
+    # The FIRST print has no quote in effect and no prior trade -- the one honest UNKNOWN case.
+    events = [
+        TradeEvent(TICKER, 0.0, 100.0, 10, Side.UNKNOWN),  # no quote, no prior -> UNKNOWN
+        QuoteEvent(TICKER, 0.5, 99.99, 100.02, 100, 100),
+        TradeEvent(TICKER, 1.0, 100.03, 5, Side.UNKNOWN),  # >= ask -> BUY
+    ]
+    rows = _non_close_out(_run(events))
+    assert rows[0]["side"] == "unknown"
+    assert rows[0]["cumulative_delta"] == 0.0
+    assert rows[0]["cumulative_delta_unknown_excluded_count"] == 1
+    assert rows[0]["same_side_run_length"] == 0
+    assert rows[1]["side"] == "buy"
+    assert rows[1]["cumulative_delta"] == 5.0
+    assert rows[1]["cumulative_delta_unknown_excluded_count"] == 1  # carried forward, not reset
+
+
+def test_tc8_rolling_imbalance_20t_matches_the_pure_formula_within_the_window():
+    rows = _non_close_out(_run(_flow_fixture_events()))
+    # Fewer than 20 trades total -> the whole session is "the window" so far; hand-computed
+    # cumulative buy/sell after each row: (10,0) (30,0) (30,5) (45,5) (45,13) (45,15).
+    expected = [
+        mf.rolling_imbalance(10, 0), mf.rolling_imbalance(30, 0), mf.rolling_imbalance(30, 5),
+        mf.rolling_imbalance(45, 5), mf.rolling_imbalance(45, 13), mf.rolling_imbalance(45, 15),
+    ]
+    assert [r["rolling_imbalance_20t"] == pytest.approx(e) for r, e in zip(rows, expected)]
+    for r, e in zip(rows, expected):
+        assert r["rolling_imbalance_20t"] == pytest.approx(e)
+        assert r["rolling_imbalance_5000sh"] == pytest.approx(e)  # also within the 5,000-share window
+
+
+def test_tc8_side_source_distinguishes_quote_rule_tick_test_and_carried():
+    events = [
+        QuoteEvent(TICKER, 0.0, 99.99, 100.02, 100, 100),
+        TradeEvent(TICKER, 1.0, 100.03, 5, Side.UNKNOWN),  # >= ask -> quote_rule
+        TradeEvent(TICKER, 2.0, 100.01, 5, Side.UNKNOWN),  # strictly between, prior 100.03 -> tick_test (down)
+        TradeEvent(TICKER, 3.0, 100.01, 5, Side.UNKNOWN),  # strictly between, price==prior -> carried
+    ]
+    rows = _non_close_out(_run(events))
+    assert [r["side_source"] for r in rows] == ["quote_rule", "tick_test", "carried"]
+
+
+def test_tc8_volume_burst_undefined_below_five_baseline_windows():
+    # Only 6 trades total -- zero completed 20-trade tiles -> undefined (counted), never guessed.
+    rows = _non_close_out(_run(_flow_fixture_events()))
+    assert all(r["volume_burst_20t"] is None for r in rows)
+    assert all(r["volume_burst_100t"] is None for r in rows)
+
+
+def test_volume_burst_defined_once_five_baseline_tiles_complete():
+    # 5 completed 20-trade tiles (100 trades) of volume 10 each, then a 6th (current, in-progress)
+    # tile whose running volume so far is checked against the median baseline of 10.
+    events: list = [QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500)]
+    ts = 1.0
+    for _tile in range(5):
+        for _i in range(20):
+            events.append(TradeEvent(TICKER, ts, 100.10, 1, Side.UNKNOWN))  # size 1 x 20 = tile volume 20
+            ts += 1.0
+    events.append(TradeEvent(TICKER, ts, 100.10, 40, Side.UNKNOWN))  # one more trade, size 40
+    rows = _non_close_out(_run(events))
+    last = rows[-1]
+    # window_volume (total, trailing 20t) = 19 * 1 + 40 = 59 (the last 20 trades: 19 of size-1 + this one)
+    assert last["volume_burst_20t"] == pytest.approx(59 / 20.0)  # median baseline of five 20-volume tiles = 20
+
+
+# --- F-RESPONSE: absorption_score reuse, failed_aggression_score, response_asymmetry (TC-9) --------
+
+
+def test_tc9_absorption_score_is_reused_verbatim_from_the_engine():
+    engine = TapeEngine(TICKER, SCENARIO, CONFIG)
+    observer = MicroObserver(quote_size_unit="unverified")
+    engine.add_observer(observer)
+    snap = None
+    for event in _flow_fixture_events():
+        snap = engine.process_event(event)
+    assert observer.rows[-1]["absorption_score"] == snap.primary_features["absorption_score"]
+
+
+def test_tc9_response_asymmetry_resolves_at_the_kth_subsequent_trade():
+    events: list = [QuoteEvent(TICKER, 0.0, 100.00, 100.02, 500, 500)]
+    ts = 1.0
+    for _i in range(10):  # trades 1..10 at the initial quote
+        events.append(TradeEvent(TICKER, ts, 100.02, 10, Side.UNKNOWN))  # >= ask -> BUY
+        ts += 1.0
+    events.append(QuoteEvent(TICKER, ts, 100.10, 100.12, 500, 500))  # the quote shifts
+    ts += 1.0
+    for _i in range(11):  # trades 11..21 at the shifted quote -- 21 trades total
+        events.append(TradeEvent(TICKER, ts, 100.12, 10, Side.UNKNOWN))  # >= ask -> BUY
+        ts += 1.0
+    rows = _non_close_out(_run(events))
+    assert len(rows) == 21
+    # trade #1's mid was (100.00+100.02)/2=100.01; by trade #21 (K=20 subsequent trades later) the
+    # mid is (100.10+100.12)/2=100.11 -- resolved on row 21 (index 20), attached to THAT row.
+    row21_deferred = rows[20]["deferred"]
+    resolved = [d for d in row21_deferred if d["kind"] == "response_asymmetry" and d["anchor_at"] == 1.0]
+    assert len(resolved) == 1
+    expected = mf.bps_move(100.01, 100.11)
+    assert resolved[0]["value"] == pytest.approx(expected)
+    assert resolved[0]["side"] == "buy"
+    assert resolved[0]["available_at"] == resolved[0]["observed_through"]
+    assert resolved[0]["unavailable"] is False
+    # No PRIOR row (1..20) carries this anchor's completion -- it is attached exactly once.
+    for row in rows[:20]:
+        assert all(d["anchor_at"] != 1.0 for d in row["deferred"] if d["kind"] == "response_asymmetry")
+
+
+def test_tc9_response_asymmetry_is_unavailable_when_the_session_ends_first():
+    events: list = [QuoteEvent(TICKER, 0.0, 100.00, 100.02, 500, 500)]
+    ts = 1.0
+    for _i in range(5):  # only 5 trades -- far short of RESPONSE_K_TRADES (20)
+        events.append(TradeEvent(TICKER, ts, 100.02, 10, Side.UNKNOWN))
+        ts += 1.0
+    rows = _run(events)  # includes the close-out row this time -- finalize() must sweep the pending anchors
+    all_deferred = [d for row in rows for d in row["deferred"]]
+    response_completions = [d for d in all_deferred if d["kind"] == "response_asymmetry"]
+    assert len(response_completions) == 5  # every one of the 5 buy anchors swept at finalize
+    assert all(d["unavailable"] is True and d["value"] is None for d in response_completions)
+
+
+# --- F-LIQUIDITY: quote_imbalance, microprice, quote_depletion, refill_consistent (TC-10) ----------
+
+
+def test_tc10_quote_imbalance_and_microprice_hand_computed():
+    events = [
+        QuoteEvent(TICKER, 0.0, 99.90, 100.10, 300, 100),
+        TradeEvent(TICKER, 1.0, 100.10, 5, Side.UNKNOWN),
+    ]
+    rows = _non_close_out(_run(events))
+    assert rows[0]["quote_imbalance"] == pytest.approx(mf.quote_imbalance(300, 100))
+    assert rows[0]["microprice"] == pytest.approx(mf.microprice(99.90, 100.10, 300, 100))
+
+
+def _depletion_events() -> list:
+    return [
+        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),  # ask run starts: price 100.10, size 500
+        QuoteEvent(TICKER, 1.0, 100.00, 100.10, 500, 400),  # same price, size drops to 400
+        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 300),  # same price, size drops to 300
+        QuoteEvent(TICKER, 3.0, 100.00, 100.20, 500, 300),  # PRICE CHANGE -- resolves the old run
+        TradeEvent(TICKER, 4.0, 100.20, 10, Side.UNKNOWN),  # first trade at/after resolution
+    ]
+
+
+def _one_ask_depletion(rows: list[dict]) -> dict:
+    assert len(rows) == 1
+    depletions = [d for d in rows[0]["deferred"] if d["kind"] == "quote_depletion" and d["side"] == "ask"]
+    assert len(depletions) == 1
+    return depletions[0]
+
+
+def test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_the_next_trade_row():
+    """The VERIFIED-unit half of the contract: the run's own timing facts, and -- because
+    ``quote_size_unit`` is verified -- the share-denominated magnitude itself, served."""
+    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="shares"))
+    d = _one_ask_depletion(rows)
+    assert d["anchor_at"] == 0.0  # the run's own start
+    assert d["observed_through"] == 2.0  # the LAST update still at the old price
+    assert d["available_at"] == 2.0
+    assert d["value"] == pytest.approx(200.0)  # 500 - 300
+    assert d["unavailable"] is False
+    assert d["refused"] is False
+    assert d["refusal_reason"] is None
+
+
+def test_tc7_tr18_quote_depletion_magnitude_is_refused_under_an_unverified_unit():
+    """TR-18 at the STREAMING call site: the depletion magnitude is share-denominated CROSS-BASIS
+    (spec section 3), so under an unverified ``quote_size_unit`` -- the state of all 18 legacy
+    datasets -- it is refused with the closed-vocabulary reason, never served as a raw number. The
+    run's unit-INVARIANT facts (availability triple, price, updates observed) are served either
+    way, and ``unavailable`` stays False: the window closed, only its magnitude is not reportable."""
+    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="unverified"))
+    d = _one_ask_depletion(rows)
+    assert d["value"] is None
+    assert d["refused"] is True
+    assert d["refusal_reason"] == mf.CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT
+    assert d["unavailable"] is False  # observed to completion -- refused, not missing
+    # the unit-invariant facts are unaffected by the refusal
+    assert d["anchor_at"] == 0.0
+    assert d["observed_through"] == 2.0
+    assert d["available_at"] == 2.0
+    assert d["price"] == pytest.approx(100.10)
+    assert d["updates_observed"] == 2
+
+
+def test_tc7_tr18_round_lots_is_a_verified_unit_for_the_depletion_magnitude_too():
+    """The gate asks "verified?", never "shares?" -- ``round_lots`` is a RECORDED unit basis, so it
+    serves the magnitude (in round lots) exactly as ``shares`` does."""
+    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="round_lots"))
+    d = _one_ask_depletion(rows)
+    assert d["value"] == pytest.approx(200.0)
+    assert d["refused"] is False
+
+
+def test_tc7_tr18_unit_invariant_liquidity_features_are_never_refused_by_the_gate():
+    """The section 2.6 carve-out, counter-tested: quote imbalance and microprice compare quote
+    sizes only to quote sizes WITHIN one dataset, so an unverified unit must NOT suppress them --
+    a gate that refused everything would be as dishonest as one that refused nothing."""
+    events = [
+        QuoteEvent(TICKER, 0.0, 99.90, 100.10, 300, 100),
+        TradeEvent(TICKER, 1.0, 100.10, 5, Side.UNKNOWN),
+    ]
+    rows = _non_close_out(_run(events, quote_size_unit="unverified"))
+    assert rows[0]["quote_size_unit"] == "unverified"
+    assert rows[0]["quote_imbalance"] == pytest.approx(mf.quote_imbalance(300, 100))
+    assert rows[0]["microprice"] == pytest.approx(mf.microprice(99.90, 100.10, 300, 100))
+
+
+def test_tc10_refill_consistent_true_when_size_is_restored_within_the_window():
+    events = [
+        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),
+        TradeEvent(TICKER, 1.0, 100.10, 200, Side.UNKNOWN),  # lifts the ask (quote_rule) -- consumes 200
+        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 200),  # ask size still down -- not yet restored
+        QuoteEvent(TICKER, 3.0, 100.00, 100.10, 500, 500),  # restored to >= the pre-trade size
+        TradeEvent(TICKER, 4.0, 100.10, 5, Side.UNKNOWN),  # first trade at/after resolution
+    ]
+    rows = _non_close_out(_run(events))
+    refills = [d for row in rows for d in row["deferred"] if d["kind"] == "refill_consistent"]
+    assert len(refills) == 1
+    assert refills[0]["value"] is True
+    assert refills[0]["side"] == "ask"
+    assert refills[0]["anchor_at"] == 1.0
+    assert refills[0]["observed_through"] == 3.0
+
+
+def test_tc10_refill_consistent_false_when_the_window_expires_unresolved(monkeypatch):
+    monkeypatch.setattr(mf, "REFILL_M_QUOTES", 2)  # shrink the window so the test stays small
+    events = [
+        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),
+        TradeEvent(TICKER, 1.0, 100.10, 200, Side.UNKNOWN),  # lifts the ask -- consumes 200
+        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 200),  # update 1: still not restored
+        QuoteEvent(TICKER, 3.0, 100.00, 100.10, 500, 250),  # update 2 (== M): still short of 500 -> expires False
+        TradeEvent(TICKER, 4.0, 100.10, 5, Side.UNKNOWN),
+    ]
+    rows = _non_close_out(_run(events))
+    refills = [d for row in rows for d in row["deferred"] if d["kind"] == "refill_consistent"]
+    assert len(refills) == 1
+    assert refills[0]["value"] is False
+    assert refills[0]["unavailable"] is False  # observed to completion -- a negative outcome, not missing
+
+
+def _unfinished_depletion_events() -> list:
+    """A depletion run the session CUTS SHORT: the ask price never changes and the run never
+    reaches ``DEPLETION_WINDOW_QUOTES`` updates, so its window simply never ends."""
+    return [
+        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),  # ask run starts at 500
+        TradeEvent(TICKER, 0.5, 100.10, 10, Side.UNKNOWN),
+        QuoteEvent(TICKER, 1.0, 100.00, 100.10, 500, 400),  # same price, size drops
+        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 100),  # ...and the stream ends here
+    ]
+
+
+@pytest.mark.parametrize("unit", ["shares", "round_lots", "unverified"])
+def test_quote_depletion_is_unavailable_when_the_session_ends_before_the_window_closes(unit):
+    """Audit regression (spec section 0's availability law, section 3's "ends at a price change or
+    the bound"): a depletion window the session cut short NEVER ended, so ``finalize()`` must sweep
+    it as ``unavailable`` (counted, never guessed) exactly like ``response_asymmetry``/
+    ``refill_consistent`` -- never as a completed observation carrying a magnitude. Before the fix
+    it was resolved with ``unavailable: False`` and, under a VERIFIED unit, a real number (400),
+    asserting a window closure that never happened."""
+    rows = _run(_unfinished_depletion_events(), quote_size_unit=unit)
... [diff_bound] apps/backend/tests/test_micro_observer.py: 132 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_micro_snapshots.py b/apps/backend/tests/test_micro_snapshots.py
new file mode 100644
index 0000000..7bd9882
--- /dev/null
+++ b/apps/backend/tests/test_micro_snapshots.py
@@ -0,0 +1,520 @@
+"""``micro_snapshots.py`` + the three ``GET``/``POST`` snapshot routes (Era "The Rapid Microscope"
+J-02) -- identity/persistence/load-time re-verification (TC-3/TR-7), the single-flight compute
+manager (TC-13), and the real 18-dataset legacy-corpus build (TC-12). Test-first contract: TC-3,
+TC-12, TC-13 in ``docs/phases/goal-rapid-microscope-iter-2.md``.
+
+The real-corpus tests (TC-12) run against the ACTUAL committed 18-dataset legacy tick corpus at
+``apps/backend/.data/datasets`` -- the ``test_micro_readiness.py`` precedent: a fixture cannot
+substitute for the real-corpus build acceptance. A snapshot is DERIVED and REUSABLE (module
+docstring), so this module-scoped fixture pays the real build cost only the FIRST time it ever
+runs against a given machine's ``.data`` tree; every subsequent run (including a re-run of just
+this file) reuses the already-valid snapshots near-instantly (``load_snapshot_meta``'s own
+identity re-verification)."""
+
+from __future__ import annotations
+
+import threading
+import time
+from contextlib import contextmanager
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app
+from app.research import micro_snapshots as ms
+from app.research.datasets import DatasetStore
+from app.research.micro_routes import (
+    get_micro_snapshot_compute_manager,
+    get_micro_snapshots_dir,
+)
+from app.research.routes import get_dataset_store
+from tests.test_micro_observer import _events_for_store
+
+TICKER = "TEST"
+
+
+def _plant(store: DatasetStore, symbol: str = TICKER) -> dict:
+    return store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id="fixture",
+        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(),
+    )
+
+
+# --- identity + quote_size_unit ---------------------------------------------------------------------
+
+
+def test_feature_source_hash_is_stable_across_calls():
+    assert ms.feature_source_hash() == ms.feature_source_hash()
+
+
+def test_feature_source_hash_covers_the_observer_module_not_only_the_feature_module(monkeypatch):
+    """Audit regression (spec section 2.3, fail-closed direction): the values that land in a
+    persisted row are produced by ``micro_observer.py``'s streaming state machine, so an
+    observer-only edit MUST re-key the snapshot identity. Hashing ``micro_features.py`` alone left
+    every stored identity verifying against code that no longer produces those rows."""
+    import hashlib
+    from pathlib import Path
+
+    from app.research import micro_features as mf_mod
+    from app.research import micro_observer as mo_mod
+
+    assert ms._IDENTITY_SOURCE_MODULES == (mf_mod, mo_mod)
+    both = ms.feature_source_hash()
+    monkeypatch.setattr(ms, "_IDENTITY_SOURCE_MODULES", (mf_mod,))
+    features_only = ms.feature_source_hash()
+    assert features_only == hashlib.sha256(Path(mf_mod.__file__).read_bytes()).hexdigest()
+    assert both != features_only  # the observer's own bytes genuinely participate
+
+
+def test_quote_size_unit_for_dataset_defaults_to_unverified():
+    assert ms.quote_size_unit_for_dataset({"id": "x"}) == "unverified"
+
+
+def test_quote_size_unit_for_dataset_reads_a_future_stamped_value_verbatim():
+    assert ms.quote_size_unit_for_dataset({"id": "x", "quote_size_unit": "shares"}) == "shares"
+
+
+def test_snapshot_identity_carries_every_component(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    identity = ms.snapshot_identity(meta, CONFIG)
+    assert identity["dataset_id"] == meta["id"]
+    assert identity["dataset_checksum"] == meta["checksum"]
+    assert identity["micro_algo_version"] == 1
+    assert identity["snapshot_format_version"] == ms.SNAPSHOT_FORMAT_VERSION
+    assert identity["config_fingerprint"] == CONFIG.config_fingerprint()
+
+
+# --- write_snapshot / load_snapshot_meta round trip --------------------------------------------------
+
+
+def test_write_then_load_round_trips(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    rows = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
+    identity = ms.snapshot_identity(meta, CONFIG)
+    written = ms.write_snapshot(str(tmp_path / "snapshots"), meta["id"], rows, {**identity, "quote_size_unit": "unverified"})
+    assert written["row_count"] == len(rows)
+    assert written["bytes_on_disk"] > 0
+
+    loaded = ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG)
+    assert loaded == written
+
+
+def test_load_snapshot_meta_is_none_when_nothing_was_ever_built(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG) is None
+
+
+def test_load_snapshot_meta_raises_on_a_corrupted_meta_file(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    snapshots_dir = tmp_path / "snapshots"
+    snapshots_dir.mkdir()
+    (snapshots_dir / f"{meta['id']}.meta.json").write_text("not json")
+    with pytest.raises(ms.MicroSnapshotIntegrityError):
+        ms.load_snapshot_meta(str(snapshots_dir), store, meta["id"], CONFIG)
+
+
+# --- a mid-stream observer failure is refused, never persisted as a short snapshot -----------------
+
+
+def test_a_mid_stream_observer_failure_refuses_the_build_instead_of_truncating_silently(
+    tmp_path, monkeypatch
+):
+    """Audit regression: ``TapeEngine._notify_event`` isolates observer exceptions BY DESIGN (the
+    engine must never be perturbed by a research observer), so a raising observer simply stops
+    producing rows -- invisibly. This test proves both halves: the engine really does sail on
+    (every event still yields its snapshot, and the observer's row set is silently short), and
+    ``build_snapshot_rows`` now REFUSES rather than persisting that short row set as a complete,
+    identity-verified snapshot."""
+    from app.research.micro_observer import MicroObserver
+
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    real_consume = MicroObserver._consume
+
+    def _boom_on_the_last_event(self, event, snapshot):
+        if event.timestamp >= 0.2:
+            raise RuntimeError("simulated observer bug")
+        real_consume(self, event, snapshot)
+
+    monkeypatch.setattr(MicroObserver, "_consume", _boom_on_the_last_event)
+
+    # (a) the engine is unaffected -- all 3 events still replay, and the observer is silently short
+    observer = MicroObserver(quote_size_unit="unverified")
+    snapshots = list(store.replay(meta["id"], CONFIG, observer=observer))
+    assert len(snapshots) == 3
+    assert observer.failure is not None
+    assert len(observer.rows) == 1  # the second trade's row never happened -- silently
+
+    # (b) the builder refuses, and nothing is written
+    root = str(tmp_path / "snapshots")
+    with pytest.raises(ms.MicroObserverFailure):
+        ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
+    with pytest.raises(ms.MicroObserverFailure):
+        ms.run_snapshot_build_and_record(store, CONFIG, root, [meta["id"]])
+    assert ms.load_snapshot_meta(root, store, meta["id"], CONFIG) is None
+
+
+def test_a_failed_build_surfaces_as_a_failed_run_never_a_silent_success(tmp_path, monkeypatch):
+    """The manager's own half of the same rail: the refusal reaches ``state: "failed"`` with the
+    error verbatim, and the durable run log records it -- never a "done" over a partial corpus."""
+    from app.research.micro_observer import MicroObserver
+
+    store = DatasetStore(tmp_path / "datasets")
+    _plant(store)
+    monkeypatch.setattr(
+        MicroObserver,
+        "_consume",
+        lambda self, event, snapshot: (_ for _ in ()).throw(RuntimeError("simulated observer bug")),
+    )
+    root = str(tmp_path / "snapshots")
+    manager = ms.MicroSnapshotComputeManager()
+    manager.trigger(store, CONFIG, root)
+    manager.join_all(timeout=10.0)
+    time.sleep(0.05)
+    snap = manager.snapshot()
+    assert snap["state"] == "failed"
+    assert "simulated observer bug" in (snap["error"] or "")
+    assert ms.read_run_log(root)[0]["state"] == "failed"
+
+
+# --- TC-3 / TR-7: cache MISS on a config_fingerprint change or a mutated feature-module byte --------
+
+
+def test_tc3_cache_miss_on_config_fingerprint_change(tmp_path, monkeypatch):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    rows = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
+    identity = ms.snapshot_identity(meta, CONFIG)
+    ms.write_snapshot(str(tmp_path / "snapshots"), meta["id"], rows, {**identity, "quote_size_unit": "unverified"})
+
+    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG) is not None
+
+    class _FakeConfig:
+        def config_fingerprint(self) -> str:
+            return "deadbeefdeadbeef"
+
+    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], _FakeConfig()) is None
+
+
+def test_tc3_cache_miss_on_a_mutated_feature_module_byte(tmp_path, monkeypatch):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    rows = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
+    identity = ms.snapshot_identity(meta, CONFIG)
+    ms.write_snapshot(str(tmp_path / "snapshots"), meta["id"], rows, {**identity, "quote_size_unit": "unverified"})
+
+    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG) is not None
+
+    monkeypatch.setattr(ms, "feature_source_hash", lambda: "simulated-different-source-hash")
+    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG) is None
+
+
+def test_tc3_rebuild_after_a_miss_serves_fresh_not_stale(tmp_path, monkeypatch):
+    import dataclasses
+
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    root = str(tmp_path / "snapshots")
+    first = ms.run_snapshot_build_and_record(store, CONFIG, root, [meta["id"]])
+    assert first[0]["config_fingerprint"] == CONFIG.config_fingerprint()
+
+    changed_config = dataclasses.replace(CONFIG, large_print_size=CONFIG.large_print_size + 1)
+    assert changed_config.config_fingerprint() != CONFIG.config_fingerprint()
+    second = ms.run_snapshot_build_and_record(store, changed_config, root, [meta["id"]])
+    assert second[0]["config_fingerprint"] == changed_config.config_fingerprint()  # rebuilt, not stale
+
+
+# --- run_snapshot_build_and_record: reuse-or-build -----------------------------------------------------
+
+
+def test_run_snapshot_build_and_record_reuses_an_already_valid_snapshot(tmp_path, monkeypatch):
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    root = str(tmp_path / "snapshots")
+    ms.run_snapshot_build_and_record(store, CONFIG, root, [meta["id"]])
+
+    calls = {"n": 0}
+    original = ms.build_snapshot_rows
+
+    def _spy(*args, **kwargs):
+        calls["n"] += 1
+        return original(*args, **kwargs)
+
+    monkeypatch.setattr(ms, "build_snapshot_rows", _spy)
+    ms.run_snapshot_build_and_record(store, CONFIG, root, [meta["id"]])
+    assert calls["n"] == 0  # reused -- no second replay
+
+
+def test_run_snapshot_build_and_record_defaults_to_every_dataset_in_the_store(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    a = _plant(store, symbol="AAA")
+    b = _plant(store, symbol="BBB")
+    results = ms.run_snapshot_build_and_record(store, CONFIG, str(tmp_path / "snapshots"))
+    assert {r["dataset_id"] for r in results} == {a["id"], b["id"]}
+
+
+# --- the durable run log -------------------------------------------------------------------------------
+
+
+def test_run_log_append_and_read_newest_first(tmp_path):
+    root = str(tmp_path / "snapshots")
+    ms.append_run_log(root, {"run_id": "a", "state": "done"})
+    ms.append_run_log(root, {"run_id": "b", "state": "failed"})
+    runs = ms.read_run_log(root)
+    assert [r["run_id"] for r in runs] == ["b", "a"]
+
+
+def test_run_log_read_is_an_honest_empty_list_when_nothing_was_ever_recorded(tmp_path):
+    assert ms.read_run_log(str(tmp_path / "nonexistent")) == []
+
+
+# --- TC-13: the single-flight compute manager --------------------------------------------------------
+
+
+def test_tc13_manager_reports_idle_before_any_job(tmp_path):
+    manager = ms.MicroSnapshotComputeManager()
+    snap = manager.snapshot()
+    assert snap["state"] == "idle"
+    assert snap["progress"]["datasets_total"] == 0
+
+
+def test_tc13_manager_refuses_a_second_concurrent_trigger(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    a = _plant(store, symbol="AAA")
+    manager = ms.MicroSnapshotComputeManager()
+    first = manager.trigger(store, CONFIG, str(tmp_path / "snapshots"), [a["id"]])
+    assert first["state"] == "running"
+    second = manager.trigger(store, CONFIG, str(tmp_path / "snapshots"), [a["id"]])
+    assert second == {"state": "refused", "reason": "already_running"}
+    manager.join_all(timeout=5.0)
+
+
+def test_tc13_progress_increases_monotonically_to_done(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    for i in range(3):
+        _plant(store, symbol=f"SYM{i}")
+    manager = ms.MicroSnapshotComputeManager()
+    manager.trigger(store, CONFIG, str(tmp_path / "snapshots"))
+    manager.join_all(timeout=10.0)
+    seen_done_counts: list[int] = []
+    deadline = time.time() + 5.0
+    while time.time() < deadline:
+        snap = manager.snapshot()
+        seen_done_counts.append(snap["progress"]["datasets_done"])
+        if snap["state"] == "done":
+            break
+        time.sleep(0.01)
+    assert seen_done_counts == sorted(seen_done_counts)  # monotonically non-decreasing
+    final = manager.snapshot()
+    assert final["state"] == "done"
+    assert final["progress"]["datasets_done"] == 3
+    assert final["progress"]["datasets_total"] == 3
+
+
+def test_tc13_cancel_on_an_idle_manager_is_a_harmless_no_op(tmp_path):
+    manager = ms.MicroSnapshotComputeManager()
+    result = manager.cancel()
+    assert result["accepted"] is False
+
+
+def test_tc13_run_log_gains_one_terminal_entry_per_job(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    _plant(store, symbol="AAA")
+    root = str(tmp_path / "snapshots")
+    manager = ms.MicroSnapshotComputeManager()
+    manager.trigger(store, CONFIG, root)
+    manager.join_all(timeout=10.0)
+    time.sleep(0.05)
+    runs = ms.read_run_log(root)
+    assert len(runs) == 1
+    assert runs[0]["state"] == "done"
+    assert runs[0]["datasets_done"] == 1
+
+
+# --- routes (TestClient) ------------------------------------------------------------------------------
+
+
+@pytest.fixture
+def client(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    snapshots_dir = str(tmp_path / "snapshots")
+    manager = ms.MicroSnapshotComputeManager()
+    app.dependency_overrides[get_dataset_store] = lambda: dataset_store
+    app.dependency_overrides[get_micro_snapshots_dir] = lambda: snapshots_dir
+    app.dependency_overrides[get_micro_snapshot_compute_manager] = lambda: manager
+    with TestClient(app) as c:
+        yield c, dataset_store, snapshots_dir, manager
+    app.dependency_overrides.pop(get_dataset_store, None)
+    app.dependency_overrides.pop(get_micro_snapshots_dir, None)
+    app.dependency_overrides.pop(get_micro_snapshot_compute_manager, None)
+
+
+def test_get_snapshots_is_an_honest_empty_list_on_a_fresh_store(client):
+    c, _store, _dir, _manager = client
+    resp = c.get("/research/desk/micro/snapshots")
+    assert resp.status_code == 200
+    assert resp.json() == {"snapshots": []}
+
+
+def test_snapshots_route_lists_a_built_snapshot(client):
+    c, store, snapshots_dir, _manager = client
+    meta = _plant(store)
+    ms.run_snapshot_build_and_record(store, CONFIG, snapshots_dir, [meta["id"]])
+    resp = c.get("/research/desk/micro/snapshots")
+    body = resp.json()
+    assert len(body["snapshots"]) == 1
+    assert body["snapshots"][0]["dataset_id"] == meta["id"]
+    assert body["snapshots"][0]["quote_size_unit"] == "unverified"
+    assert "row_count" in body["snapshots"][0] and "bytes_on_disk" in body["snapshots"][0]
+    # never raw per-event rows (the boundary note) -- only metadata keys are served
+    assert "deferred" not in body["snapshots"][0] and "cumulative_delta" not in body["snapshots"][0]
+
+
+def test_compute_route_triggers_a_build_and_reports_progress_to_done(client):
+    c, store, _dir, _manager = client
+    _plant(store)
+    post_resp = c.post("/research/desk/micro/snapshots/compute")
+    assert post_resp.status_code == 200
+    assert post_resp.json()["state"] == "running"
+    assert "run_id" in post_resp.json()
+
+    deadline = time.time() + 5.0
+    state = None
+    while time.time() < deadline:
+        get_resp = c.get("/research/desk/micro/snapshots/compute")
+        state = get_resp.json()["state"]
+        if state == "done":
+            break
+        time.sleep(0.01)
... [diff_bound] apps/backend/tests/test_micro_snapshots.py: 126 more diff lines omitted — Read the file for full detail
```
