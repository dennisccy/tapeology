# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/micro_features.py b/apps/backend/app/research/micro_features.py
index 076719d..bfa34c6 100644
--- a/apps/backend/app/research/micro_features.py
+++ b/apps/backend/app/research/micro_features.py
@@ -72,6 +72,7 @@ __all__ = [
     "require_outcome_start_not_before_conditioning",
     "mid_outcome",
     "last_trade_outcome",
+    "spread_bps",
     "CrossBasisUnverifiedUnitError",
     "is_verified_unit",
     "require_verified_unit",
@@ -406,6 +407,19 @@ def last_trade_outcome(
     }
 
 
+def spread_bps(spread: float | None, mid: float | None) -> float | None:
+    """The quoted spread (dollar terms, exactly as the engine/observer already compute it)
+    expressed in basis points of the mid -- spec section 4's cost-proxy column: "Quoted spread at
+    the outcome start (bps) is served beside every outcome ... never netted into the outcome
+    silently." A caller (``micro_join.py``, the FIRST caller of this closed outcome set) reads
+    this beside ``mid_outcome``/``last_trade_outcome`` as an independent field -- it is never
+    added to or subtracted from either outcome's own ``value``. ``None`` with no measured spread
+    or mid, or a non-positive mid (no basis for a bps expression), never a fabricated 0.0."""
+    if spread is None or mid is None or mid <= 0:
+        return None
+    return spread / mid * 10_000.0
+
+
 # --- The section 2.6 cross-basis unit gate (TR-18) ------------------------------------------------
 
 
diff --git a/apps/backend/app/research/micro_readiness.py b/apps/backend/app/research/micro_readiness.py
index bc7f58a..448c1b0 100644
--- a/apps/backend/app/research/micro_readiness.py
+++ b/apps/backend/app/research/micro_readiness.py
@@ -6,6 +6,13 @@ actually exists today, and which of the three predeclared pilot-study floors it
 honestly). It never fabricates, never re-derives a value another store already owns, and never
 computes at GET time beyond the one per-shard cost documented below.
 
+**J-03 addition:** the SAME "Corpus readiness truth" Data Contract row (no new endpoint) now also
+carries ``joinable_corpus`` -- how many recorded playbook signals fall inside a recorded tick
+dataset's own window, with a ``by_setup_id`` breakdown, computed by ``micro_join.
+joinable_corpus_counts`` (never a second, independently-valued copy of that count here). Read the
+full rationale, including why ``band_touch_count`` is honestly zero this iteration, in
+``micro_join.py``'s own module docstring.
+
 **Reads verbatim, never re-derives.** Every shard's ``checksum``/``trade_count``/``quote_count``/
 ``data_feed``/``window_start_utc``/``window_end_utc`` is read straight off
 ``DatasetStore.list()``'s own already-checksum-verified metadata -- this module performs no
@@ -68,6 +75,7 @@ from zoneinfo import ZoneInfo
 
 from ..providers.base import Event, QuoteEvent, TradeEvent
 from .datasets import DatasetStore
+from .micro_join import joinable_corpus_counts
 from .referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
 
 __all__ = [
@@ -280,12 +288,19 @@ class MicroReadinessCache:
 # --- the whole readiness aggregation -----------------------------------------------------------------
 
 
-def build_readiness(store: DatasetStore, cache: MicroReadinessCache, *, dataset_dir: str) -> dict:
+def build_readiness(
+    store: DatasetStore, cache: MicroReadinessCache, *, dataset_dir: str, playbook_store=None
+) -> dict:
     """The whole ``GET /research/desk/micro/readiness`` body -- a pure aggregation over
     ``DatasetStore.list()``'s already-verified records (module docstring). Deterministic and
     byte-reproducible: an unchanged store + a warm cache yields a byte-identical response on
     every call (TC-7) -- nothing here reads the wall clock into the served shape (the cache's own
-    ``created_utc`` never leaves the cache)."""
+    ``created_utc`` never leaves the cache).
+
+    ``playbook_store`` (J-03, ``desk_playbook.PlaybookStore``) is OPTIONAL and defaults to
+    ``None`` -- callers that do not pass one (every pre-J-03 test in this file) get the honest
+    ``joinable_corpus`` zero rather than an error, since "no playbook evidence was even checked"
+    is a true statement in that case, never a fabricated one."""
     records, errors = store.list()
     root = Path(dataset_dir)
 
@@ -359,9 +374,21 @@ def build_readiness(store: DatasetStore, cache: MicroReadinessCache, *, dataset_
         "referee_tick_gate_symbol_days": REFEREE_TICK_GATE_SYMBOL_DAYS,
     }
 
+    # J-03: honestly zero (never computed) when no playbook_store is given at all -- a true
+    # statement ("no playbook evidence was even checked"), never a fabricated count. When one IS
+    # given, the count is owned entirely by micro_join.joinable_corpus_counts (never re-derived
+    # here -- module docstring).
+    if playbook_store is None:
+        joinable_corpus = {
+            "total": 0, "playbook_signal_count": 0, "band_touch_count": 0, "by_setup_id": {},
+        }
+    else:
+        joinable_corpus = joinable_corpus_counts(store, playbook_store)
+
     return {
         "totals": totals,
         "shards": shards,
         "study_floors": study_floors,
         "integrity_errors": errors,
+        "joinable_corpus": joinable_corpus,
     }
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 7fdf083..27708d3 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -24,6 +24,8 @@ from fastapi import APIRouter, Depends, HTTPException
 
 from ..config import CONFIG
 from .datasets import DatasetStore
+from .desk_playbook import PlaybookStore
+from .desk_routes import get_playbook_store
 from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
 from .micro_snapshots import (
     MicroSnapshotComputeManager,
@@ -50,14 +52,21 @@ def get_micro_readiness_cache() -> MicroReadinessCache:
 def get_micro_readiness(
     dataset_store: DatasetStore = Depends(get_dataset_store),
     cache: MicroReadinessCache = Depends(get_micro_readiness_cache),
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
 ) -> dict:
     """J-01's corpus-truth fold: the honest per-shard inventory, corpus totals beside the
     referee's tick-gate figure, and the three pilot studies' floor table -- see
     ``micro_readiness.build_readiness``'s own docstring for the full contract. Never 404/500 on
     an empty corpus (the desk router's established never-404-on-absence convention) -- an empty
     ``shards`` list (``study_floors`` still carries its 3 rows, each read against a 0-session
-    corpus) at HTTP 200."""
-    return build_readiness(dataset_store, cache, dataset_dir=CONFIG.dataset_dir_resolved())
+    corpus) at HTTP 200.
+
+    J-03: ``playbook_store`` is the EXISTING ``desk_routes.get_playbook_store`` dependency,
+    reused verbatim (never a second, redefined provider) -- it feeds the ``joinable_corpus``
+    field, computed by ``micro_join.joinable_corpus_counts``."""
+    return build_readiness(
+        dataset_store, cache, dataset_dir=CONFIG.dataset_dir_resolved(), playbook_store=playbook_store
+    )
 
 
 def get_micro_snapshots_dir() -> str:
diff --git a/apps/backend/app/research/micro_snapshots.py b/apps/backend/app/research/micro_snapshots.py
index 0ab9829..20db39a 100644
--- a/apps/backend/app/research/micro_snapshots.py
+++ b/apps/backend/app/research/micro_snapshots.py
@@ -51,6 +51,7 @@ __all__ = [
     "quote_size_unit_for_dataset",
     "build_snapshot_rows",
     "write_snapshot",
+    "read_snapshot_rows",
     "load_snapshot_meta",
     "list_snapshot_meta",
     "run_snapshot_build_and_record",
@@ -199,6 +200,32 @@ def write_snapshot(root_dir: str, dataset_id: str, rows: list[dict], identity_an
     return meta
 
 
+# --- the plain row reader (J-03: micro_join.py's ONLY door onto a snapshot's persisted rows) ------
+
+
+def read_snapshot_rows(root_dir: str, dataset_id: str) -> list[dict]:
+    """Every persisted row of ONE snapshot, in their ORIGINAL append (ascending ``anchor_at``)
+    order -- a plain JSONL iterator, co-located with the writer (module docstring) since both read
+    and write the identical on-disk shape. Callers MUST have already established the snapshot is
+    CURRENT (``load_snapshot_meta`` -- TR-7's re-verification) before calling this: unlike that
+    function, this reader performs no identity check of its own and raises ``FileNotFoundError``
+    verbatim for a dataset with no snapshot on disk, never a silent empty list.
+
+    This is deliberately a PLAIN reader, not an origin-fenced one -- ``micro_accessor.py`` (J-05)
+    becomes the sole, origin-fenced, sealed-shard-aware door onto snapshot AND vault event data
+    (the era's "the accessor is the only door" rail); until it exists, the still-fully-exploratory
+    legacy corpus this iteration reads has no sealed shard to protect, and the iteration's own
+    NOTES record this boundary as an explicit, later re-pointing (J-05 is expected to route
+    ``micro_join.py``'s reads through the accessor once it lands, not to duplicate this reader)."""
+    rows: list[dict] = []
+    with _rows_path(Path(root_dir), dataset_id).open("r", encoding="utf-8") as fh:
+        for line in fh:
+            line = line.strip()
+            if line:
+                rows.append(json.loads(line))
+    return rows
+
+
 # --- load, with re-verification (TR-7) ------------------------------------------------------------
 
 
diff --git a/apps/backend/tests/test_micro_features.py b/apps/backend/tests/test_micro_features.py
index 0bb9b38..b890430 100644
--- a/apps/backend/tests/test_micro_features.py
+++ b/apps/backend/tests/test_micro_features.py
@@ -271,6 +271,24 @@ def test_last_trade_outcome_is_a_separately_named_basis_never_the_primary():
     assert result["value"] == pytest.approx(0.25)
 
 
+# --- J-03: the section 4 cost-proxy column, served BESIDE every outcome, never netted in -----------
+
+
+def test_spread_bps_hand_computed():
+    # 0.06 wide on a 149.0 mid -> (0.06 / 149.0) * 10_000.
+    assert mf.spread_bps(0.06, 149.0) == pytest.approx(0.06 / 149.0 * 10_000.0)
+
+
+def test_spread_bps_none_with_no_measured_spread_or_mid():
+    assert mf.spread_bps(None, 149.0) is None
+    assert mf.spread_bps(0.06, None) is None
+
+
+def test_spread_bps_none_with_a_non_positive_mid():
+    assert mf.spread_bps(0.06, 0.0) is None
+    assert mf.spread_bps(0.06, -1.0) is None
+
+
 # --- the section 2.6 cross-basis unit gate (TC-7 / TR-18) -------------------------------------------
 
 
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
index 80c6acc..14c4a57 100644
--- a/apps/backend/tests/test_micro_readiness.py
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -36,6 +36,9 @@ from app.research.micro_readiness import (
     build_readiness,
     resolve_micro_readiness_cache_db_path,
 )
+from app.research.desk_playbook import PlaybookStore, playbook_parameters
+from app.research.desk_routes import get_playbook_store
+from app.research.micro_join import joinable_corpus_counts
 from app.research.micro_routes import get_micro_readiness_cache
 from app.research.referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
 from app.research.routes import get_dataset_store
@@ -84,12 +87,18 @@ def _plant_dataset(
 def client(tmp_path):
     dataset_store = DatasetStore(tmp_path / "datasets")
     cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    # J-03: the route now also depends on a playbook store (the joinable_corpus field) -- a
+    # tmp_path-scoped, empty-by-default one, so this fixture's existing hermeticity contract is
+    # unaffected (never the real, ambient .data/playbook directory).
+    playbook_store = PlaybookStore(tmp_path / "playbook")
     app.dependency_overrides[get_dataset_store] = lambda: dataset_store
     app.dependency_overrides[get_micro_readiness_cache] = lambda: cache
+    app.dependency_overrides[get_playbook_store] = lambda: playbook_store
     with TestClient(app) as c:
         yield c, dataset_store, cache
     app.dependency_overrides.pop(get_dataset_store, None)
     app.dependency_overrides.pop(get_micro_readiness_cache, None)
+    app.dependency_overrides.pop(get_playbook_store, None)
 
 
 # --- _quote_rule_decides: cross-validated against classify_aggressor's own OBSERVABLE behavior ------
@@ -439,3 +448,100 @@ def test_tc5_real_corpus_all_three_pilot_studies_read_floor_unmet(real_readiness
         assert floor["required_sessions"] == 60
         assert floor["available_sessions"] == 11
         assert floor["status"] == "floor_unmet"
+
+
+# --- J-03 TC-5: the joinable_corpus field (docs/phases/goal-rapid-microscope-iter-3.md) ------------
+#
+# NOT the same "TC-5" as the J-01 real-corpus block just above (a numbering coincidence across
+# iterations, not a duplicate) -- this section covers THIS iteration's own DEFINITION OF DONE item
+# "GET /research/desk/micro/readiness serves the honest joinable_corpus breakdown".
+
+
+def test_joinable_corpus_defaults_to_an_honest_zero_without_a_playbook_store(tmp_path):
+    """``build_readiness`` called the OLD way (no ``playbook_store``, every pre-J-03 call site)
+    still serves a well-shaped, honestly-zero ``joinable_corpus`` -- never an error, never an
+    absent key."""
+    store = DatasetStore(tmp_path / "datasets")
+    _plant_dataset(store, symbol="AAPL")
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    body = build_readiness(store, cache, dataset_dir=str(tmp_path / "datasets"))
+    assert body["joinable_corpus"] == {
+        "total": 0, "playbook_signal_count": 0, "band_touch_count": 0, "by_setup_id": {},
+    }
+
+
+def test_joinable_corpus_matches_joinable_corpus_counts_directly(tmp_path):
+    """``build_readiness``'s served field is BYTE-IDENTICAL to calling ``joinable_corpus_counts``
+    directly over the same two stores -- single source of truth, never a second computation."""
+    store = DatasetStore(tmp_path / "datasets")
+    _plant_dataset(store, symbol="AAPL")
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    playbook_store.record(
+        session_date="2026-06-09",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature="sig-readiness-tc5",
+        payload_version=1,
+        parameters=playbook_parameters(),
+        register="",
+        signals=[
+            {"symbol": "AAPL", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:30Z"},
+        ],
+        absences=[], diagnostics=[],
+    )
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+
+    body = build_readiness(
+        store, cache, dataset_dir=str(tmp_path / "datasets"), playbook_store=playbook_store
+    )
+
+    assert body["joinable_corpus"] == joinable_corpus_counts(store, playbook_store)
+    assert body["joinable_corpus"] == {
+        "total": 1, "playbook_signal_count": 1, "band_touch_count": 0,
+        "by_setup_id": {"opening_range_break": 1},
+    }
+
+
+def test_joinable_corpus_is_served_through_the_route_and_is_non_negative_and_never_hardcoded(
+    client, tmp_path
+):
+    """TC-5's own route-level acceptance: called twice, the SERVED ``joinable_corpus`` is
+    identical, every count is a non-negative int, and it reflects a REAL planted signal -- never a
+    hardcoded placeholder."""
+    c, store, _cache = client
+    _plant_dataset(store, symbol="AAPL")
+    # Plants into the SAME tmp_path the `client` fixture already scoped its (overridden) playbook
+    # store to -- a second PlaybookStore instance over the identical on-disk directory.
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    playbook_store.record(
+        session_date="2026-06-09",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature="sig-readiness-route-tc5",
+        payload_version=1,
+        parameters=playbook_parameters(),
+        register="",
+        signals=[
+            {"symbol": "AAPL", "setup_id": "jbe", "trigger_ts": "2026-06-09T13:00:15Z"},
+            {"symbol": "AAPL", "setup_id": "jbe", "trigger_ts": "2099-01-01T00:00:00Z"},  # not joinable
+        ],
+        absences=[], diagnostics=[],
+    )
+
+    first = c.get("/research/desk/micro/readiness").json()["joinable_corpus"]
+    second = c.get("/research/desk/micro/readiness").json()["joinable_corpus"]
+
+    assert first == second
+    for key in ("total", "playbook_signal_count", "band_touch_count"):
+        assert isinstance(first[key], int) and first[key] >= 0
+    assert first["playbook_signal_count"] == 1  # only the in-window signal counts
+    assert first["by_setup_id"] == {"jbe": 1}
+
+
+def test_real_corpus_readiness_still_serves_an_honest_zero_joinable_corpus_without_a_playbook_store(
+    real_readiness,
+):
+    """The module-scoped real-corpus fixture above calls ``build_readiness`` the OLD way (no
+    ``playbook_store``) -- confirms the new field is present and honestly zero there too, never an
+    absent key on the real 18-dataset corpus response."""
+    assert real_readiness["joinable_corpus"] == {
+        "total": 0, "playbook_signal_count": 0, "band_touch_count": 0, "by_setup_id": {},
+    }
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/journey-scripts/J-10.json | 9 +++++----
 runs/goal-session-rapid-microscope/telemetry.jsonl           | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl         | 1 +
 3 files changed, 13 insertions(+), 4 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
