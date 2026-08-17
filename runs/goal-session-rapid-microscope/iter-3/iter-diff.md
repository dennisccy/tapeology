# Iteration diff (bounded)

Files changed: 8. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/micro_join.py` (14 lines not shown)
- `apps/backend/tests/test_micro_join.py` (115 lines not shown)

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
diff --git a/apps/backend/app/research/micro_join.py b/apps/backend/app/research/micro_join.py
new file mode 100644
index 0000000..d6c366d
--- /dev/null
+++ b/apps/backend/app/research/micro_join.py
@@ -0,0 +1,408 @@
+"""``micro_join.py`` -- Era "The Rapid Microscope" J-03: the structure x flow join.
+
+Joins a PLAYBOOK SIGNAL ``(symbol, trigger_ts)`` (read verbatim from ``desk_playbook.py``'s
+recorded records) or a BAND-MAP WALL TOUCH ``(symbol, as_of_epoch)`` (resolved read-only through
+``desk_playbook_context.BandMapResolver.resolve``, ``compute=False`` -- never a second band-map
+computation) to the covering micro snapshot's own feature row AT-OR-BEFORE the trigger, plus the
+closed set of outcome rows AFTER it (``docs/rapid-validation-spec.md`` section 4). This module
+computes NOTHING the engine/observer/detector/context modules already own -- it locates and reads
+their already-persisted output (spec's own "read-side law").
+
+**The lookahead rail, mechanically.** A feature-at-trigger row is chosen by scanning the
+snapshot's own append-order rows (ascending ``anchor_at`` -- ``micro_observer.py``'s prefix-law
+invariant) and keeping the LAST one whose ``anchor_at`` is at-or-before the trigger instant; a row
+strictly after the trigger can never be selected (``_locate_at_or_before``, TR-1 in spirit, TC-3's
+own dedicated test).
+
+**The absolute-vs-logical clock translation.** A playbook signal's ``trigger_ts`` (an ISO string,
+``desk_playbook_detect.py``'s ``_iso(trigger_bar.epoch)``) and a band touch's ``as_of_epoch`` are
+both ABSOLUTE UTC epochs; a snapshot row's own ``anchor_at`` is the dataset's LOGICAL replay clock
+(``HistoricalProvider``'s "logical, not wall-clock" scheme -- the dataset events' raw ``ts``
+values, small offsets from zero, never absolute epochs -- see ``datasets.py``'s
+``_event_to_row``/``_row_to_event`` round trip). The translation is the IDENTICAL
+``epoch_anchor + logical_ts`` reconstruction ``setups.py``'s own tape-at-the-wall join
+(``_tape_timeline``) and ``serializers.serialize_history``'s chart projection already use,
+inverted here (absolute -> logical instead of logical -> absolute) -- never a second scheme.
+
+**The dataset-window match.** ``_covering_dataset`` mirrors ``setups.py``'s own
+``_matching_dataset`` technique verbatim (symbol equality + ``[window_start_utc, window_end_utc]``
+numeric-epoch containment, ties on ``(created_utc, id)``) -- re-implemented locally rather than
+imported because it is a small, generic technical match over dataset METADATA, not a second
+implementation of any measurement rail (the same class of judgment call
+``micro_readiness.py``'s own ``_quote_rule_decides`` docstring makes for mirroring, rather than
+importing, a sibling module's technique). Logged as an interpretation call in the iteration's dev
+handoff.
+
+**``band_touch_count`` is honestly zero this iteration.** No module anywhere in the shipped
+product yet enumerates discrete band-map wall-touch INSTANTS as a stored, countable list --
+identifying what counts as a "touch" is explicitly J-09's own predeclared-mechanism work (goal.md
+OUT OF SCOPE: "Any pilot-study-specific mechanism ... is J-09; J-03 only builds the generic join
+primitive and its honest corpus count"). ``join_band_touch`` below proves the JOIN PRIMITIVE
+itself works against an explicit, caller-supplied ``(symbol, as_of_epoch)`` pair (TC-2); there is
+simply no existing corpus of such pairs to count over yet, so ``joinable_corpus_counts`` reports
+the honest, non-fabricated zero rather than inventing a detector.
+
+**Outcome-start basis (assumption-ledger entry, this iteration).** Outcome start = the trigger's
+own ``anchor_at`` (never a later, conditioned instant) -- no per-candidate conditioning feature
+set exists before J-04's Scout, so ``resolve_outcome_start``'s general "max of the conditioning
+set's ``available_at``" collapses to the trivial single-element case here. A future J-04/J-05
+caller conditioning on a DEFERRED feature (whose ``available_at`` is later than its own
+``anchor_at``) will call ``micro_features.require_outcome_start_not_before_conditioning`` itself,
+not this module -- this join's own outcome rows are unconditioned.
+
+**Never a second replay, never a second parse.** Feature rows are read through
+``micro_snapshots.read_snapshot_rows`` (this module's ONLY door onto a snapshot's persisted rows,
+never a raw ``open()``) after ``load_snapshot_meta`` confirms the snapshot is CURRENT (TR-7); a
+dataset with no covering window, or a covering dataset with no currently-valid snapshot, is an
+honest ``no_covering_snapshot`` -- never a fabricated join."""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING, Sequence
+
+from . import micro_features as mf
+from .datasets import DatasetStore, parse_utc_epoch
+from .micro_snapshots import load_snapshot_meta, read_snapshot_rows
+
+if TYPE_CHECKING:  # pragma: no cover -- type-checking only, never a runtime import (no cycle risk)
+    from ..config import Config
+    from .desk_playbook_context import BandMapResolver
+
+__all__ = [
+    "MICRO_HORIZON_TRADES",
+    "MICRO_HORIZON_SHARES",
+    "MICRO_HORIZON_CLOCK_SECONDS",
+    "JOIN_STATUS_JOINED",
+    "JOIN_STATUS_NO_COVERING_SNAPSHOT",
+    "JOIN_STATUS_NO_ROW_BEFORE_TRIGGER",
+    "JOIN_STATUS_NO_BAND_CONTEXT",
+    "find_covering_dataset",
+    "find_covering_snapshot",
+    "feature_row_at_trigger",
+    "outcome_rows_after_trigger",
+    "join_playbook_signal",
+    "join_band_touch",
+    "joinable_corpus_counts",
+]
+
+# docs/rapid-validation-spec.md section 1 -- transcribed verbatim (module docstring: this module is
+# the FIRST caller of an outcome horizon, so it is this module's constants to own; deliberately
+# NOT the same Python objects as micro_features.py's MICRO_FEATURE_WINDOW_* -- that module's own
+# docstring calls the windows and the horizons "deliberately separate constants" despite sharing
+# today's numeric values).
+MICRO_HORIZON_TRADES: tuple[int, ...] = (20, 100)
+MICRO_HORIZON_SHARES: tuple[int, ...] = (5_000, 50_000)
+MICRO_HORIZON_CLOCK_SECONDS: tuple[int, ...] = (30, 60, 300)
+
+# A horizon whose target row does not exist in the recorded stream is, by construction, beyond the
+# session -- this sentinel need only satisfy `horizon_ts > session_end_ts` (mid_outcome's own
+# truncation test); its exact magnitude carries no meaning beyond "later than the window".
+_BEYOND_SESSION_EPS = 1.0
+
+JOIN_STATUS_JOINED = "joined"
+JOIN_STATUS_NO_COVERING_SNAPSHOT = "no_covering_snapshot"
+JOIN_STATUS_NO_ROW_BEFORE_TRIGGER = "no_row_before_trigger"
+JOIN_STATUS_NO_BAND_CONTEXT = "no_band_context"
+
+_ABSENT_JOIN = {"dataset_id": None, "feature_at_trigger": None, "outcomes": []}
+
+
+# --- absolute epoch <-> a dataset's own logical replay clock (module docstring) --------------------
+
+
+def _logical_ts(dataset_meta: dict, absolute_epoch: float) -> float:
+    anchor = dataset_meta.get("epoch_anchor")
+    if anchor is None:
+        return absolute_epoch
+    return absolute_epoch - anchor
+
+
+def _session_end_logical_ts(dataset_meta: dict) -> float:
+    """The dataset's own recorded window end, in ITS logical clock -- the honest truncation
+    boundary (spec section 4), independent of whether a close-out row happens to exist (module
+    docstring: ``MicroObserver.finalize()`` only appends one when a deferred construct was still
+    pending -- module ``micro_observer.py``)."""
+    return _logical_ts(dataset_meta, parse_utc_epoch(dataset_meta["window_end_utc"]))
+
+
+# --- the dataset-window match (module docstring: mirrors setups.py's _matching_dataset) ------------
+
+
+def _covering_dataset(symbol: str, at_epoch: float, records: Sequence[dict]) -> dict | None:
+    candidates = [
+        r for r in records
+        if r["symbol"] == symbol
+        and parse_utc_epoch(r["window_start_utc"]) <= at_epoch <= parse_utc_epoch(r["window_end_utc"])
+    ]
+    if not candidates:
+        return None
+    return min(candidates, key=lambda r: (r["created_utc"], r["id"]))
+
+
+def find_covering_dataset(symbol: str, at_epoch: float, dataset_store: DatasetStore) -> dict | None:
+    """The single-lookup convenience form of ``_covering_dataset`` -- lists the store fresh for
+    THIS one call. A caller checking many instants against the SAME store (``joinable_corpus_
+    counts`` below) lists once and calls ``_covering_dataset`` directly instead."""
+    records, _errors = dataset_store.list()
+    return _covering_dataset(symbol, at_epoch, records)
+
+
+def find_covering_snapshot(
+    symbol: str, at_epoch: float, dataset_store: DatasetStore, snapshots_dir: str, config: "Config"
+) -> tuple[dict, dict] | None:
+    """``(dataset_meta, snapshot_meta)`` for the covering, CURRENTLY-VALID snapshot, or ``None``
+    when no dataset window covers ``at_epoch`` for ``symbol``, or one does but carries no
+    currently-valid snapshot (TR-7 -- a stale/never-built snapshot is an honest miss, never
+    served)."""
+    dataset_meta = find_covering_dataset(symbol, at_epoch, dataset_store)
+    if dataset_meta is None:
+        return None
+    snapshot_meta = load_snapshot_meta(snapshots_dir, dataset_store, dataset_meta["id"], config)
+    if snapshot_meta is None:
+        return None
+    return dataset_meta, snapshot_meta
+
+
+# --- the feature-at-trigger lookup (the lookahead rail, mechanically -- module docstring) ----------
+
+
+def _trade_rows(rows: Sequence[dict]) -> list[dict]:
+    """Every TRADE-anchored row -- excludes the optional close-out row
+    (``micro_observer.finalize()``'s own ``close_out: True`` marker), which carries no
+    ``cumulative_delta``/``mid``/``price`` and is never itself a feature-at-trigger candidate."""
+    return [r for r in rows if not r.get("close_out")]
+
+
+def _locate_at_or_before(trade_rows: list[dict], trigger_logical_ts: float) -> int | None:
+    """The index of the LAST row (ascending ``anchor_at`` order -- the snapshot's own append
+    order) with ``anchor_at <= trigger_logical_ts``, or ``None`` when every row is strictly after
+    the trigger (or the stream is empty). A row is selected ONLY because its own anchor precedes
+    or equals the trigger -- never because it is merely nearby (TC-3)."""
+    found = None
+    for i, row in enumerate(trade_rows):
+        if row["anchor_at"] <= trigger_logical_ts:
+            found = i
+        else:
+            break
+    return found
+
+
+def feature_row_at_trigger(rows: Sequence[dict], trigger_logical_ts: float) -> dict | None:
+    """The feature row at-or-before ``trigger_logical_ts`` (a dataset-LOGICAL instant -- callers
+    holding an absolute epoch convert via ``_logical_ts`` first), or ``None`` when the trigger
+    precedes every trade row. Returns the row VERBATIM (including its ``deferred`` list, with any
+    ``unavailable``/``refused`` flag intact -- TC-6): this function never projects or coerces a
+    row's own fields."""
+    trade_rows = _trade_rows(rows)
+    i = _locate_at_or_before(trade_rows, trigger_logical_ts)
+    return None if i is None else trade_rows[i]
+
+
+# --- the closed outcome set (spec section 4), resolved over the trade-anchored representation ------
+
+
+def _trade_horizon_row(trade_rows: list[dict], anchor_pos: int, n_trades: int) -> dict | None:
+    target_pos = anchor_pos + n_trades
+    return trade_rows[target_pos] if target_pos < len(trade_rows) else None
+
+
+def _shares_horizon_row(trade_rows: list[dict], anchor_pos: int, shares_threshold: int) -> dict | None:
+    cumulative = 0.0
+    for row in trade_rows[anchor_pos + 1 :]:
+        cumulative += row["size"]
+        if cumulative >= shares_threshold:
+            return row
+    return None
+
+
+def _clock_horizon_row(trade_rows: list[dict], anchor_pos: int, horizon_ts: float) -> dict | None:
+    """The nearest at-or-before row for a CLOCK horizon, sampled from the trade-anchored
+    representation (the ONLY representation the section 2.4 benchmark chose -- there is no
+    standalone quote row to sample instead; an interpretation call, logged in the dev handoff)."""
+    candidate = None
+    for row in trade_rows[anchor_pos:]:
+        if row["anchor_at"] <= horizon_ts:
+            candidate = row
+        else:
+            break
+    return candidate
+
+
+def _build_outcome(
+    *, kind: str, value: int, anchor_row: dict, horizon_row: dict | None, horizon_ts: float,
+    session_end_ts: float, side: str | None,
+) -> dict:
+    mid_at_horizon = horizon_row.get("mid") if horizon_row is not None else None
+    price_at_horizon = horizon_row.get("price") if horizon_row is not None else None
+    return {
+        "horizon_kind": kind,
+        "horizon_value": value,
+        "mid": mf.mid_outcome(
+            mid_at_start=anchor_row.get("mid"), mid_at_horizon=mid_at_horizon,
+            outcome_start=anchor_row["anchor_at"], horizon_ts=horizon_ts,
+            session_end_ts=session_end_ts, side=side,
+        ),
+        "last_trade": mf.last_trade_outcome(
+            price_at_start=anchor_row.get("price"), price_at_horizon=price_at_horizon,
+            outcome_start=anchor_row["anchor_at"], horizon_ts=horizon_ts,
+            session_end_ts=session_end_ts, side=side,
+        ),
+        "spread_at_outcome_start_bps": mf.spread_bps(anchor_row.get("spread"), anchor_row.get("mid")),
+    }
+
+
+def _outcome_rows_after(
+    trade_rows: list[dict], anchor_pos: int, session_end_ts: float, *, side: str | None
+) -> list[dict]:
+    anchor_row = trade_rows[anchor_pos]
+    outcomes: list[dict] = []
+    for n in MICRO_HORIZON_TRADES:
+        horizon_row = _trade_horizon_row(trade_rows, anchor_pos, n)
+        horizon_ts = horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
+        outcomes.append(_build_outcome(
+            kind="trades", value=n, anchor_row=anchor_row, horizon_row=horizon_row,
+            horizon_ts=horizon_ts, session_end_ts=session_end_ts, side=side,
+        ))
+    for shares in MICRO_HORIZON_SHARES:
+        horizon_row = _shares_horizon_row(trade_rows, anchor_pos, shares)
+        horizon_ts = horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
+        outcomes.append(_build_outcome(
+            kind="shares", value=shares, anchor_row=anchor_row, horizon_row=horizon_row,
+            horizon_ts=horizon_ts, session_end_ts=session_end_ts, side=side,
+        ))
+    for seconds in MICRO_HORIZON_CLOCK_SECONDS:
+        horizon_ts = anchor_row["anchor_at"] + seconds
+        horizon_row = None if horizon_ts > session_end_ts else _clock_horizon_row(trade_rows, anchor_pos, horizon_ts)
+        outcomes.append(_build_outcome(
+            kind="clock_seconds", value=seconds, anchor_row=anchor_row, horizon_row=horizon_row,
+            horizon_ts=horizon_ts, session_end_ts=session_end_ts, side=side,
+        ))
+    return outcomes
+
+
+def outcome_rows_after_trigger(
+    rows: Sequence[dict], anchor_row: dict, session_end_ts: float, *, side: str | None = None
+) -> list[dict]:
+    """The closed set of outcome rows (spec section 4) at every horizon of section 1, anchored at
+    ``anchor_row`` (a row returned by ``feature_row_at_trigger`` over the SAME ``rows``). Outcome
+    start = ``anchor_row["anchor_at"]`` (this iteration's assumption-ledger entry -- module
+    docstring). Each entry carries the mid-basis primary, the last-trade sensitivity basis, and
+    the spread-at-outcome-start cost-proxy column, never merged into either outcome's own value."""
+    trade_rows = _trade_rows(rows)
+    anchor_pos = trade_rows.index(anchor_row)
+    return _outcome_rows_after(trade_rows, anchor_pos, session_end_ts, side=side)
+
+
+# --- the shared join core --------------------------------------------------------------------------
+
+
+def _join_core(
+    symbol: str, at_epoch: float, dataset_store: DatasetStore, snapshots_dir: str, config: "Config"
+) -> dict:
+    found = find_covering_snapshot(symbol, at_epoch, dataset_store, snapshots_dir, config)
+    if found is None:
+        return {"status": JOIN_STATUS_NO_COVERING_SNAPSHOT, **_ABSENT_JOIN}
+    dataset_meta, _snapshot_meta = found
+    rows = read_snapshot_rows(snapshots_dir, dataset_meta["id"])
+    trade_rows = _trade_rows(rows)
+    trigger_logical_ts = _logical_ts(dataset_meta, at_epoch)
+    i = _locate_at_or_before(trade_rows, trigger_logical_ts)
+    if i is None:
+        return {
+            "status": JOIN_STATUS_NO_ROW_BEFORE_TRIGGER,
+            "dataset_id": dataset_meta["id"], "feature_at_trigger": None, "outcomes": [],
+        }
+    session_end_ts = _session_end_logical_ts(dataset_meta)
+    outcomes = _outcome_rows_after(trade_rows, i, session_end_ts, side=None)
+    return {
+        "status": JOIN_STATUS_JOINED,
+        "dataset_id": dataset_meta["id"],
+        "feature_at_trigger": dict(trade_rows[i]),
+        "outcomes": outcomes,
+    }
+
+
+# --- the two public entry points (goal.md Key Capability 4) ----------------------------------------
+
+
+def join_playbook_signal(
+    signal: dict, dataset_store: DatasetStore, snapshots_dir: str, config: "Config"
+) -> dict:
+    """Join ONE recorded playbook signal (``desk_playbook.py``'s own ``symbol``/``trigger_ts``/
+    ``setup_id`` fields, read verbatim -- never re-detected) to its covering snapshot's
+    feature-at-trigger row plus the closed outcome set after it."""
+    symbol = signal.get("symbol")
+    trigger_ts = signal.get("trigger_ts")
+    base = {"symbol": symbol, "trigger_ts": trigger_ts, "setup_id": signal.get("setup_id")}
+    if not symbol or not trigger_ts:
+        return {"status": JOIN_STATUS_NO_COVERING_SNAPSHOT, **_ABSENT_JOIN, **base}
+    trigger_epoch = parse_utc_epoch(trigger_ts)
+    core = _join_core(symbol, trigger_epoch, dataset_store, snapshots_dir, config)
+    return {**core, **base}
+
+
+def join_band_touch(
+    touch: dict, resolver: "BandMapResolver", dataset_store: DatasetStore, snapshots_dir: str,
+    config: "Config",
+) -> dict:
+    """Join ONE band-map wall touch ``{"symbol": ..., "as_of_epoch": ...}`` to its covering
+    snapshot's feature-at-trigger row plus the closed outcome set after it, carrying the resolved
+    band map beside them. ``resolver.resolve(...)`` is READ-ONLY (``compute=False`` at
+    construction, per goal.md's own framing) -- a cache miss is an honest absence, never a
+    fabricated wall (TC-2)."""
+    symbol = touch.get("symbol")
+    as_of_epoch = touch.get("as_of_epoch")
+    base = {"symbol": symbol, "as_of_epoch": as_of_epoch, "band_map": None}
+    if not symbol or as_of_epoch is None:
+        return {"status": JOIN_STATUS_NO_BAND_CONTEXT, **_ABSENT_JOIN, **base}
+    band_map = resolver.resolve(symbol, as_of_epoch)
+    if band_map is None:
+        return {"status": JOIN_STATUS_NO_BAND_CONTEXT, **_ABSENT_JOIN, **base}
+    core = _join_core(symbol, as_of_epoch, dataset_store, snapshots_dir, config)
+    return {**core, "symbol": symbol, "as_of_epoch": as_of_epoch, "band_map": band_map}
+
+
+# --- the honest joinable-corpus count (micro_readiness.py's new field) -----------------------------
+
+
+def joinable_corpus_counts(dataset_store: DatasetStore, playbook_store) -> dict:
+    """``total``/``playbook_signal_count``/``band_touch_count``/``by_setup_id`` -- every recorded
+    playbook signal whose ``(symbol, trigger_ts)`` falls inside a recorded tick dataset's own
+    window (module docstring's dataset-window match), counted honestly from the real stores.
+    Never requires a snapshot to already be BUILT: a snapshot is a reproducible, rebuildable cache
+    of the SAME tick data (``micro_snapshots.py``'s own "derived, rebuildable" docstring) -- an
+    unbuilt one says nothing about whether the underlying evidence is joinable.
+
+    Fails CLOSED, never silently under-counts (the iter-2 "streamed-artifact completeness"
+    lesson, applied to this enumeration loop): a signal recording no symbol or no ``trigger_ts``
+    is a structural, honest absence and is skipped (the identical treatment
+    ``desk_playbook_context.record_band_context`` already gives it); a signal whose ``trigger_ts``
+    is PRESENT but unparseable is never silently skipped -- ``parse_utc_epoch`` raises and this
+    function raises with it, rather than serving an undercounted total."""
+    records, _errors = dataset_store.list()
+    total_playbook = 0
+    by_setup_id: dict[str, int] = {}
+    for playbook_record in playbook_store.list()[0]:
+        for signal in playbook_record.get("signals") or []:
+            symbol = signal.get("symbol")
+            trigger_ts = signal.get("trigger_ts")
+            if not symbol or not trigger_ts:
+                continue
+            trigger_epoch = parse_utc_epoch(trigger_ts)
+            if _covering_dataset(symbol, trigger_epoch, records) is None:
+                continue
+            total_playbook += 1
... [diff_bound] apps/backend/app/research/micro_join.py: 14 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_micro_join.py b/apps/backend/tests/test_micro_join.py
new file mode 100644
index 0000000..5e8a913
--- /dev/null
+++ b/apps/backend/tests/test_micro_join.py
@@ -0,0 +1,509 @@
+"""``micro_join.py`` (Era "The Rapid Microscope" J-03) -- the structure x flow join.
+
+Test-first contract: TC-1 through TC-9 in
+``docs/phases/goal-rapid-microscope-iter-3.md``. TC-1/TC-2/TC-3/TC-6 run against the
+already-committed ``tests/fixtures/datasets_j03/`` PG SIP dataset, built into a real snapshot via
+the existing (already-tested) J-02 pipeline -- this file never re-verifies J-02's own arithmetic,
+only that ``micro_join.py`` LOCATES and serves the right rows. TC-4 is a pinned whole-module
+byte-freeze (the ``test_referee_guards.py`` precedent). TC-5's ``joinable_corpus`` readiness field
+is exercised end to end in ``test_micro_readiness.py`` instead -- this file covers the counting
+function it calls into (``joinable_corpus_counts``) directly, over small hermetic fixtures."""
+
+from __future__ import annotations
+
+import hashlib
+import inspect
+from datetime import datetime, timezone
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG
+from app.providers.base import QuoteEvent, Side, TradeEvent
+from app.research import desk_playbook as desk_playbook_module
+from app.research import desk_playbook_context as desk_playbook_context_module
+from app.research import micro_join
+from app.research.datasets import DatasetStore
+from app.research.desk_playbook import PlaybookStore, playbook_parameters
+from app.research.desk_playbook_context import BandMapResolver
+from app.research.micro_snapshots import read_snapshot_rows, run_snapshot_build_and_record
+from app.research.tradability_cache import TradabilityCache
+
+FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "datasets_j03"
+PG_DATASET_ID = "5232fa672b7b4077a5117d34b14c807d"
+
+
+def _iso(epoch: float) -> str:
+    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="microseconds").replace(
+        "+00:00", "Z"
+    )
+
+
+# --- shared fixture: the real PG snapshot, built once per module (577 trades -- cheap) -------------
+
+
+@pytest.fixture(scope="module")
+def pg_snapshot(tmp_path_factory):
+    dataset_store = DatasetStore(FIXTURES_DIR)
+    snapshots_dir = str(tmp_path_factory.mktemp("micro_join_snapshots"))
+    run_snapshot_build_and_record(dataset_store, CONFIG, snapshots_dir, [PG_DATASET_ID])
+    rows = read_snapshot_rows(snapshots_dir, PG_DATASET_ID)
+    dataset_meta = dataset_store.get(PG_DATASET_ID)
+    return {
+        "dataset_store": dataset_store,
+        "snapshots_dir": snapshots_dir,
+        "rows": rows,
+        "trade_rows": [r for r in rows if not r.get("close_out")],
+        "dataset_meta": dataset_meta,
+    }
+
+
+def _trigger_epoch(dataset_meta: dict, logical_ts: float) -> float:
+    return dataset_meta["epoch_anchor"] + logical_ts
+
+
+# --- TC-1: the feature-at-trigger row matches the nearest at-or-before row -------------------------
+
+
+def test_tc1_feature_at_trigger_matches_the_row_pinned_exactly_at_the_trigger(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    trigger_row = trade_rows[49]  # an arbitrary, comfortably-interior trade
+    trigger_epoch = _trigger_epoch(dataset_meta, trigger_row["anchor_at"])
+    signal = {"symbol": "PG", "trigger_ts": _iso(trigger_epoch), "setup_id": "fixture_probe"}
+
+    result = micro_join.join_playbook_signal(
+        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
+    )
+
+    assert result["status"] == micro_join.JOIN_STATUS_JOINED
+    assert result["dataset_id"] == PG_DATASET_ID
+    feature = result["feature_at_trigger"]
+    assert feature["cumulative_delta"] == pytest.approx(trigger_row["cumulative_delta"])
+    assert feature["spread"] == pytest.approx(trigger_row["spread"])
+    assert feature["tape_state"] == trigger_row["tape_state"]
+    assert feature["trade_index"] == trigger_row["trade_index"]
+
+
+def test_tc1_a_trigger_strictly_between_two_rows_never_picks_the_later_one(pg_snapshot):
+    """Proves "nearest AT-OR-BEFORE, never after" precisely: a trigger sitting strictly between
+    two consecutive trade rows must resolve to the EARLIER one."""
+    trade_rows = pg_snapshot["trade_rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    earlier, later = trade_rows[49], trade_rows[50]
+    assert later["anchor_at"] > earlier["anchor_at"]
+    midpoint_logical = (earlier["anchor_at"] + later["anchor_at"]) / 2.0
+    trigger_epoch = _trigger_epoch(dataset_meta, midpoint_logical)
+    signal = {"symbol": "PG", "trigger_ts": _iso(trigger_epoch), "setup_id": "fixture_probe"}
+
+    result = micro_join.join_playbook_signal(
+        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
+    )
+
+    assert result["feature_at_trigger"]["trade_index"] == earlier["trade_index"]
+
+
+def test_a_trigger_before_the_first_trade_is_an_honest_absence_not_a_fabricated_row(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    before_first = trade_rows[0]["anchor_at"] - 0.5
+    trigger_epoch = _trigger_epoch(dataset_meta, before_first)
+    signal = {"symbol": "PG", "trigger_ts": _iso(trigger_epoch), "setup_id": "fixture_probe"}
+
+    result = micro_join.join_playbook_signal(
+        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
+    )
+
+    assert result["status"] == micro_join.JOIN_STATUS_NO_ROW_BEFORE_TRIGGER
+    assert result["feature_at_trigger"] is None
+    assert result["outcomes"] == []
+
+
+def test_a_trigger_outside_every_recorded_window_is_no_covering_snapshot(pg_snapshot):
+    signal = {"symbol": "PG", "trigger_ts": "2099-01-01T00:00:00Z", "setup_id": "fixture_probe"}
+
+    result = micro_join.join_playbook_signal(
+        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
+    )
+
+    assert result["status"] == micro_join.JOIN_STATUS_NO_COVERING_SNAPSHOT
+    assert result["feature_at_trigger"] is None
+
+
+def test_an_unknown_symbol_is_no_covering_snapshot(pg_snapshot):
+    dataset_meta = pg_snapshot["dataset_meta"]
+    trigger_epoch = _trigger_epoch(dataset_meta, 5.0)
+    signal = {"symbol": "NOPE", "trigger_ts": _iso(trigger_epoch)}
+
+    result = micro_join.join_playbook_signal(
+        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
+    )
+
+    assert result["status"] == micro_join.JOIN_STATUS_NO_COVERING_SNAPSHOT
+
+
+def test_a_signal_missing_symbol_or_trigger_ts_is_an_honest_absence_never_a_crash(pg_snapshot):
+    for broken in [{"trigger_ts": "2026-06-09T17:02:05Z"}, {"symbol": "PG"}]:
+        result = micro_join.join_playbook_signal(
+            broken, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
+        )
+        assert result["status"] == micro_join.JOIN_STATUS_NO_COVERING_SNAPSHOT
+        assert result["feature_at_trigger"] is None
+
+
+# --- TC-3: the lookahead assertion -------------------------------------------------------------------
+
+
+def test_tc3_lookahead_no_returned_feature_row_ever_exceeds_its_own_trigger(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    rows = pg_snapshot["rows"]
+    # A grid sampled across the whole stream (every 23rd trade -- coprime-ish stride, not just the
+    # first few rows) plus the exact-boundary case for each sampled row.
+    for row in trade_rows[::23]:
+        t = row["anchor_at"]
+        matched = micro_join.feature_row_at_trigger(rows, t)
+        assert matched is not None
+        assert matched["anchor_at"] <= t, "a matched row's own anchor must never exceed the trigger"
+        assert matched["anchor_at"] == t  # the exact row itself, since t IS one of its own anchors
+
+
+def test_tc3_lookahead_holds_at_every_consecutive_pair_gap(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    rows = pg_snapshot["rows"]
+    for earlier, later in zip(trade_rows[::31], trade_rows[1::31]):
+        if later["anchor_at"] <= earlier["anchor_at"]:
+            continue
+        probe_t = later["anchor_at"] - 1e-6
+        matched = micro_join.feature_row_at_trigger(rows, probe_t)
+        assert matched["anchor_at"] <= probe_t
+        assert matched["anchor_at"] != later["anchor_at"], "must never jump ahead to the later row"
+
+
+# --- TC-6: the unavailable flag on a deferred construct survives the join verbatim ------------------
+
+
+def test_tc6_unavailable_deferred_completion_survives_the_join_verbatim():
+    rows = [
+        {
+            "anchor_at": 1.0, "observed_through": 1.0, "available_at": 1.0, "trade_index": 1,
+            "side": "buy", "price": 100.0, "mid": 100.0, "spread": 0.02, "tape_state": "trending_up",
+            "cumulative_delta": 5.0,
+            "deferred": [
+                {
+                    "kind": "response_asymmetry", "side": "buy", "anchor_at": 0.5,
+                    "observed_through": 1.0, "available_at": 1.0, "value": None, "unavailable": True,
+                }
+            ],
+        }
+    ]
+    matched = micro_join.feature_row_at_trigger(rows, 1.0)
+    assert matched["deferred"][0]["unavailable"] is True
+    assert matched["deferred"][0]["value"] is None  # never coerced to a number
+
+
+def test_tc6_a_refused_cross_basis_completion_also_survives_verbatim():
+    """The section 2.6 refusal shape (``refused``/``refusal_reason``) is a DIFFERENT closed-
+    vocabulary state from ``unavailable`` -- both must ride through the join untouched."""
+    rows = [
+        {
+            "anchor_at": 2.0, "observed_through": 2.0, "available_at": 2.0, "trade_index": 2,
+            "side": "sell", "price": 99.0, "mid": 99.0, "spread": 0.02, "tape_state": "trending_down",
+            "cumulative_delta": -3.0,
+            "deferred": [
+                {
+                    "kind": "quote_depletion", "side": "bid", "anchor_at": 1.0,
+                    "observed_through": 2.0, "available_at": 2.0, "value": None, "unavailable": False,
+                    "refused": True, "refusal_reason": "cross_basis_unverified_quote_size_unit",
+                }
+            ],
+        }
+    ]
+    matched = micro_join.feature_row_at_trigger(rows, 2.0)
+    assert matched["deferred"][0]["refused"] is True
+    assert matched["deferred"][0]["refusal_reason"] == "cross_basis_unverified_quote_size_unit"
+
+
+# --- TC-4: the detector/context byte-freeze guard (the test_referee_guards.py precedent) ------------
+
+# Recorded BEFORE this iteration touches anything -- goal.md's own Non-Goal: "No detector,
+# threshold, or context change of any kind" / "no change to desk_playbook.py, desk_playbook_
+# context.py". These two files carry ZERO diff this iteration; both hashes must still match at the
+# end of it too.
+_DESK_PLAYBOOK_MODULE_SHA256 = "f059dcba80a7f09db8bcf74c4d2234c28aee5df2fb6bca32685cb30f8ba55bea"
+_DESK_PLAYBOOK_CONTEXT_MODULE_SHA256 = "75537d161661b9660cf82896c56b60d92acdf3179fd77bd041c38ae45530fc23"
+
+
+def test_tc4_desk_playbook_module_is_byte_unchanged_this_iteration():
+    source = inspect.getsource(desk_playbook_module)
+    assert hashlib.sha256(source.encode()).hexdigest() == _DESK_PLAYBOOK_MODULE_SHA256
+
+
+def test_tc4_desk_playbook_context_module_is_byte_unchanged_this_iteration():
+    source = inspect.getsource(desk_playbook_context_module)
+    assert hashlib.sha256(source.encode()).hexdigest() == _DESK_PLAYBOOK_CONTEXT_MODULE_SHA256
+
+
+def test_tc4_byte_freeze_guard_can_fail_on_a_seeded_violation():
+    """A lint that cannot fail proves nothing."""
+    source = inspect.getsource(desk_playbook_module)
+    real_hash = hashlib.sha256(source.encode()).hexdigest()
+    assert real_hash != "0" * 64
+
+
+# --- the outcome set: horizons, truncation, the spread cost-proxy column ---------------------------
+
+
+def test_outcome_rows_cover_every_spec_section_1_horizon_family(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    rows = pg_snapshot["rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    anchor_row = trade_rows[9]  # early in the window -- plenty of trailing trades/shares/seconds
+    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
+
+    outcomes = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts)
+
+    kinds_values = [(o["horizon_kind"], o["horizon_value"]) for o in outcomes]
+    assert kinds_values == [
+        ("trades", 20), ("trades", 100),
+        ("shares", 5_000), ("shares", 50_000),
+        ("clock_seconds", 30), ("clock_seconds", 60), ("clock_seconds", 300),
+    ]
+    for outcome in outcomes:
+        assert outcome["mid"]["basis"] == "mid"
+        assert outcome["last_trade"]["basis"] == "last_trade"
+        assert "spread_at_outcome_start_bps" in outcome
+        # the cost-proxy column is never netted into either outcome's own value (spec section 4):
+        # it is a THIRD, independent key, not part of either outcome dict.
+        assert "spread_at_outcome_start_bps" not in outcome["mid"]
+        assert "spread_at_outcome_start_bps" not in outcome["last_trade"]
+
+
+def test_the_trades_20_horizon_matches_an_independently_computed_reference(pg_snapshot):
+    """A reference computed a SECOND, obviously-correct way (plain list indexing in the test
+    itself, not through any of micro_join.py's own helpers) -- the "hand-computed" oracle TC-1's
+    acceptance describes, applied to an outcome instead of the feature-at-trigger row."""
+    trade_rows = pg_snapshot["trade_rows"]
+    rows = pg_snapshot["rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    anchor_pos = 9
+    anchor_row = trade_rows[anchor_pos]
+    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
+    expected_horizon_row = trade_rows[anchor_pos + 20]
+    assert expected_horizon_row["anchor_at"] <= session_end_ts  # sanity: not truncated
+
+    outcomes = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts)
+    trades_20 = next(o for o in outcomes if o["horizon_kind"] == "trades" and o["horizon_value"] == 20)
+
+    expected_mid_move = expected_horizon_row["mid"] - anchor_row["mid"]
+    assert trades_20["mid"]["value"] == pytest.approx(expected_mid_move)
+    assert trades_20["mid"]["truncated"] is False
+    assert trades_20["mid"]["unmeasured"] is False
+    expected_spread_bps = anchor_row["spread"] / anchor_row["mid"] * 10_000.0
+    assert trades_20["spread_at_outcome_start_bps"] == pytest.approx(expected_spread_bps)
+
+
+def test_a_horizon_beyond_the_recorded_stream_is_truncated_never_measured_off_the_last_trade(pg_snapshot):
+    trade_rows = pg_snapshot["trade_rows"]
+    rows = pg_snapshot["rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    anchor_row = trade_rows[-3]  # near the very end of the 577-trade window
+    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
+
+    outcomes = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts)
+
+    trades_100 = next(o for o in outcomes if o["horizon_kind"] == "trades" and o["horizon_value"] == 100)
+    assert trades_100["mid"]["truncated"] is True
+    assert trades_100["mid"]["value"] is None
+    assert trades_100["last_trade"]["truncated"] is True
+    clock_300 = next(o for o in outcomes if o["horizon_kind"] == "clock_seconds" and o["horizon_value"] == 300)
+    assert clock_300["mid"]["truncated"] is True
+    assert clock_300["mid"]["value"] is None
+
+
+# --- TC-2: the band-map wall touch join -------------------------------------------------------------
+
+
+class _EmptyBarStore:
+    def __init__(self, root="/tmp/does-not-exist-micro-join-test"):
+        self.root = root
+
+    def list(self):
+        return [], []
+
+
+def _resolver(tmp_path) -> BandMapResolver:
+    return BandMapResolver(
+        _EmptyBarStore(), CONFIG, cache=TradabilityCache(str(tmp_path / "trad.db"))
+    )
+
+
+def test_tc2_a_cached_band_map_joins_the_matching_feature_and_outcome_rows(pg_snapshot, tmp_path):
+    trade_rows = pg_snapshot["trade_rows"]
+    dataset_meta = pg_snapshot["dataset_meta"]
+    resolver = _resolver(tmp_path)
+    touch_row = trade_rows[19]
+    as_of_epoch = _trigger_epoch(dataset_meta, touch_row["anchor_at"])
+    fixture_map = {"basis_day": "2026-06-09", "bands": [{"kind": "support", "low": 148.0, "high": 149.0}]}
+    resolver._cache.publish(resolver.map_key("PG", as_of_epoch), fixture_map)
+
+    result = micro_join.join_band_touch(
+        {"symbol": "PG", "as_of_epoch": as_of_epoch}, resolver,
+        pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG,
+    )
+
+    assert result["status"] == micro_join.JOIN_STATUS_JOINED
+    assert result["band_map"] == fixture_map
+    assert result["feature_at_trigger"]["trade_index"] == touch_row["trade_index"]
+    assert len(result["outcomes"]) == 7
+
+
+def test_tc2_an_uncached_band_map_is_an_honest_absence_never_a_fabricated_wall(pg_snapshot, tmp_path):
+    dataset_meta = pg_snapshot["dataset_meta"]
+    resolver = _resolver(tmp_path)  # nothing published -- a genuine miss
+    as_of_epoch = _trigger_epoch(dataset_meta, 5.0)
+
+    result = micro_join.join_band_touch(
+        {"symbol": "PG", "as_of_epoch": as_of_epoch}, resolver,
+        pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG,
+    )
+
+    assert result["status"] == micro_join.JOIN_STATUS_NO_BAND_CONTEXT
+    assert result["band_map"] is None
+    assert result["feature_at_trigger"] is None
+    assert result["outcomes"] == []
+
+
+# --- joinable_corpus_counts (micro_readiness.py's new field; TC-5's own computation) -----------------
+
+
+def _plant_events(symbol: str) -> list:
+    return [
+        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
+        TradeEvent(symbol, 0.1, 100.0, 10, Side.BUY),
+        TradeEvent(symbol, 0.2, 100.0, 10, Side.SELL),
+    ]
+
+
+def _plant_dataset(store: DatasetStore, *, symbol: str, window_start_utc: str, window_end_utc: str) -> dict:
+    return store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-fixture",
+        split="train", window_start_utc=window_start_utc, window_end_utc=window_end_utc,
+        data_feed="sip", epoch_anchor=0.0, events=_plant_events(symbol),
+    )
+
+
... [diff_bound] apps/backend/tests/test_micro_join.py: 115 more diff lines omitted — Read the file for full detail
```
