# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 11. Shown in full: 9.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/scout.py` (453 lines not shown)
- `apps/backend/tests/test_scout.py` (194 lines not shown)

```diff
diff --git a/apps/backend/app/research/micro_join.py b/apps/backend/app/research/micro_join.py
index 5316940..471090d 100644
--- a/apps/backend/app/research/micro_join.py
+++ b/apps/backend/app/research/micro_join.py
@@ -49,6 +49,15 @@ not-yet-a-number band-touch state): numerically identical to before this fix, si
 ``0`` always contributed nothing to the sum either (TC-16). Defining an actual touch enumeration
 stays J-09's job; when it lands, this becomes ``{"status": "enumerated", "count": <int>}``.
 
+**J-09 materializes it (this iteration).** ``joinable_corpus_counts`` gains an OPTIONAL, keyword-
+only ``resolver`` (default ``None``, byte-identical to before for every existing caller that omits
+it -- the ``playbook_store`` optionality precedent): when given, ``band_touch_count`` becomes the
+REAL ``{"status": "enumerated", "count": <int>}`` -- the sum of ``enumerate_band_touches`` across
+every withheld-excluded dataset already in ``records`` (the SAME denominator ``playbook_signal_
+count`` already reads, never a second corpus enumeration); when omitted, the honest ``not_
+enumerated`` sentinel is unchanged. ``total`` stays ``playbook_signal_count`` alone either way
+(this field has never summed the band-touch state, materialized or not -- TC-16 unaffected).
+
 **A corrupt playbook record surfaces honestly, never a silent undercount (iter-4 passenger fix).**
 ``playbook_store.list()`` returns ``(records, errors)`` (the SAME shape ``DatasetStore.list()``
 serves, and the shape every reader of it already surfaces at ITS own call site --
@@ -83,6 +92,7 @@ from __future__ import annotations
 from typing import TYPE_CHECKING, Sequence
 
 from . import micro_features as mf
+from ..providers.base import TradeEvent
 from .datasets import DatasetStore, parse_utc_epoch
 from .micro_accessor import MicroAccessor
 # ``exclude_withheld``: spec section 7.5 point 6 (r4) -- the ONE withholding predicate every
@@ -102,6 +112,7 @@ __all__ = [
     "JOIN_STATUS_NO_ROW_BEFORE_TRIGGER",
     "JOIN_STATUS_NO_BAND_CONTEXT",
     "BAND_TOUCH_STATUS_NOT_ENUMERATED",
+    "BAND_TOUCH_STATUS_ENUMERATED",
     "find_covering_dataset",
     "find_covering_snapshot",
     "feature_row_at_trigger",
@@ -110,6 +121,7 @@ __all__ = [
     "outcome_row_at_single_horizon",
     "join_playbook_signal",
     "join_band_touch",
+    "enumerate_band_touches",
     "joinable_corpus_counts",
 ]
 
@@ -490,12 +502,78 @@ def join_band_touch(
     return {**core, "symbol": symbol, "as_of_epoch": as_of_epoch, "band_map": band_map}
 
 
+# --- the band-touch enumerator (J-09, goal.md Key Capability 5's own primitive) --------------------
+
+
+def _band_id(band: dict) -> str:
+    """A stable identifier for ONE band, from its own ``(side, price_low, price_high)`` identity --
+    the SAME two price bounds ``setups.py``'s own ``_event_id`` precedent hashes beside its call's
+    symbol/session/touch_ts (that module's own docstring) -- never ``quality_score``/``class``/
+    ``members``, which can shift between two computes of the IDENTICAL wall (a re-ranked
+    ``quality_score`` after a bar backfill, say) without changing WHICH wall it is."""
+    return f"{band['side']}:{band['price_low']!r}:{band['price_high']!r}"
+
+
+def enumerate_band_touches(
+    dataset_meta: dict, dataset_store: DatasetStore, resolver: "BandMapResolver"
+) -> list[dict]:
+    """Ordered per-wall touch instants -- ``{"symbol", "as_of_epoch", "band_id"}`` -- across ONE
+    dataset's own recorded trade timeline (spec section 3's structural join primitive; goal.md Key
+    Capability 5). The band map is resolved ONCE, at the dataset's own window start (module
+    docstring: a recorded RTH window never spans an ET midnight, so one basis session covers every
+    trade in it) -- ``resolver.resolve(...)`` is READ-ONLY (``compute=False`` at the caller's own
+    construction, per goal.md's own framing); an unresolvable map is an honest empty list, never a
+    fabricated touch (TC-3).
+
+    Reads the dataset's OWN raw event stream (``DatasetStore.load_events`` -- an existing,
+    already-sanctioned store reader, the SAME call ``micro_readiness.py``'s own ``fallback_frac``
+    fold already makes; TR-3's accessor fence governs SNAPSHOT/vault reads, not this) rather than a
+    built snapshot's feature rows -- deliberately, so this enumeration NEVER requires a snapshot to
+    already exist (the ``joinable_corpus_counts`` docstring's own "never requires a snapshot to
+    already be BUILT" law, extended here from playbook signals to band touches). The expensive
+    event load only happens AFTER the band map resolves (a durable-cache hit or an honest miss) --
+    the common case today (most symbol/dates have no operator-warmed tradability map) pays only the
+    cheap resolver lookup, never a multi-million-row parse for nothing.
+
+    A touch mirrors ``setups.py``'s own ``_touches`` "first touch, re-arm only once fully exited"
+    rule (that function's own docstring), applied here to a TRADE PRICE against one band's
+    ``[price_low, price_high]`` instead of a bar's own ``[low, high]`` range: each band arms/re-arms
+    INDEPENDENTLY, so one trade can touch several bands at once, and a later trade only re-arms the
+    bands it has fully exited."""
+    symbol = dataset_meta.get("symbol")
+    if not symbol:
+        return []
+    band_map = resolver.resolve(symbol, parse_utc_epoch(dataset_meta["window_start_utc"]))
+    if band_map is None:
+        return []
+    bands = band_map.get("bands") or []
+    if not bands:
+        return []
+    epoch_anchor = dataset_meta.get("epoch_anchor") or 0.0
+    armed = [True] * len(bands)
+    touches: list[dict] = []
+    for event in dataset_store.load_events(dataset_meta["id"]):
+        if not isinstance(event, TradeEvent):
+            continue
+        absolute_epoch = epoch_anchor + event.timestamp
+        for i, band in enumerate(bands):
+            inside = band["price_low"] <= event.price <= band["price_high"]
+            if inside and armed[i]:
+                touches.append(
+                    {"symbol": symbol, "as_of_epoch": absolute_epoch, "band_id": _band_id(band)}
+                )
+                armed[i] = False
+            elif not inside:
+                armed[i] = True
+    return touches
+
+
 # --- the honest joinable-corpus count (micro_readiness.py's new field) -----------------------------
 
-# The closed vocabulary for band_touch_count's "not enumerated" state (iter-4 passenger fix) -- see
-# the module docstring. A future J-09 caller wiring a real touch enumeration in adds a sibling
-# "enumerated" status; this iteration serves only the honest absence.
+# The closed vocabulary for band_touch_count's status (iter-4 passenger fix; J-09 adds the
+# "enumerated" sibling the iter-4 docstring already predicted -- see the module docstring).
 BAND_TOUCH_STATUS_NOT_ENUMERATED = "not_enumerated"
+BAND_TOUCH_STATUS_ENUMERATED = "enumerated"
 
 
 def _band_touch_not_enumerated() -> dict:
@@ -505,7 +583,9 @@ def _band_touch_not_enumerated() -> dict:
     return {"status": BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
 
 
-def joinable_corpus_counts(dataset_store: DatasetStore, playbook_store) -> dict:
+def joinable_corpus_counts(
+    dataset_store: DatasetStore, playbook_store, *, resolver: "BandMapResolver | None" = None
+) -> dict:
     """``total``/``playbook_signal_count``/``band_touch_count``/``by_setup_id``/
     ``playbook_integrity_errors`` -- every recorded playbook signal whose ``(symbol, trigger_ts)``
     falls inside a recorded tick dataset's own window (module docstring's dataset-window match),
@@ -549,13 +629,25 @@ def joinable_corpus_counts(dataset_store: DatasetStore, playbook_store) -> dict:
             setup_id = signal.get("setup_id") or "unknown"
             by_setup_id[setup_id] = by_setup_id.get(setup_id, 0) + 1
 
+    # J-09: materialized ONLY when a resolver is supplied (module docstring) -- summed over the
+    # SAME withheld-excluded `records` the playbook loop above already reads, so a sealed shard is
+    # excluded from this count the identical way it is excluded from `playbook_signal_count`
+    # (never a second, differently-scoped corpus).
+    if resolver is None:
+        band_touch_count = _band_touch_not_enumerated()
+    else:
+        total_band_touches = sum(
+            len(enumerate_band_touches(meta, dataset_store, resolver)) for meta in records
+        )
+        band_touch_count = {"status": BAND_TOUCH_STATUS_ENUMERATED, "count": total_band_touches}
+
     return {
         # `playbook_signal_count` alone -- `band_touch_count` is no longer a plain number to sum
         # (module docstring); numerically identical to the pre-fix total, since the prior bare `0`
         # always contributed nothing to the sum either (TC-16).
         "total": total_playbook,
         "playbook_signal_count": total_playbook,
-        "band_touch_count": _band_touch_not_enumerated(),
+        "band_touch_count": band_touch_count,
         "by_setup_id": by_setup_id,
         "playbook_integrity_errors": playbook_errors,
         # Spec section 7.5 point 6 (r4): the count of registered datasets whose windows were NOT
diff --git a/apps/backend/app/research/micro_readiness.py b/apps/backend/app/research/micro_readiness.py
index 24f6956..40c4750 100644
--- a/apps/backend/app/research/micro_readiness.py
+++ b/apps/backend/app/research/micro_readiness.py
@@ -71,6 +71,7 @@ import os
 import sqlite3
 from datetime import date, datetime, time, timezone
 from pathlib import Path
+from typing import TYPE_CHECKING
 from zoneinfo import ZoneInfo
 
 from ..providers.base import Event, QuoteEvent, TradeEvent
@@ -79,6 +80,9 @@ from .micro_join import BAND_TOUCH_STATUS_NOT_ENUMERATED, joinable_corpus_counts
 from .referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
 from . import vault
 
+if TYPE_CHECKING:  # pragma: no cover -- type-checking only, never a runtime import (no cycle risk)
+    from .desk_playbook_context import BandMapResolver
+
 __all__ = [
     "WF_TRAIN_MIN_SESSIONS",
     "WF_TEST_MIN_SESSIONS",
@@ -290,7 +294,12 @@ class MicroReadinessCache:
 
 
 def build_readiness(
-    store: DatasetStore, cache: MicroReadinessCache, *, dataset_dir: str, playbook_store=None
+    store: DatasetStore,
+    cache: MicroReadinessCache,
+    *,
+    dataset_dir: str,
+    playbook_store=None,
+    resolver: "BandMapResolver | None" = None,
 ) -> dict:
     """The whole ``GET /research/desk/micro/readiness`` body -- a pure aggregation over
     ``DatasetStore.list()``'s already-verified records (module docstring). Deterministic and
@@ -303,6 +312,15 @@ def build_readiness(
     ``joinable_corpus`` zero rather than an error, since "no playbook evidence was even checked"
     is a true statement in that case, never a fabricated one.
 
+    ``resolver`` (J-09, ``desk_playbook_context.BandMapResolver``) is likewise OPTIONAL, defaulting
+    to ``None`` -- passed straight through to ``micro_join.joinable_corpus_counts`` (never
+    constructed here; this module owns no ``BarStore``/``Config`` wiring of its own -- the caller,
+    ``micro_routes.py``, already holds both). Omitting it (every pre-J-09 test) keeps
+    ``band_touch_count`` at its honest ``not_enumerated`` sentinel; supplying one materializes the
+    real enumerated int (``micro_join.py``'s own docstring). Only consulted when ``playbook_store``
+    is also given -- the ``playbook_store is None`` branch below already answers "nothing was
+    checked" honestly for BOTH counts at once, never a mixed state.
+
     **Sealed-tranche AGGREGATES only (iter-9, spec section 7.5 point 4, r3; widened iteration 11,
     point 7, r5).** A dataset that is part of an UNRESOLVED registered-universe pool gets NO
     per-shard row and NO per-shard ``exposure_state`` here -- its row would carry the symbol,
@@ -472,7 +490,7 @@ def build_readiness(
             "withheld_excluded": 0,
         }
     else:
-        joinable_corpus = joinable_corpus_counts(store, playbook_store)
+        joinable_corpus = joinable_corpus_counts(store, playbook_store, resolver=resolver)
 
     sealed_tranche = {
         "shard_count": sealed_shard_count,
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 9fa438c..1aced09 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -43,6 +43,7 @@ from .bar_index import BarIndex
 from .bars import BarStore
 from .datasets import DatasetStore
 from .desk_playbook import PlaybookStore
+from .desk_playbook_context import BandMapResolver
 from .desk_routes import get_playbook_store, get_universe_store
 from .desk_universe import UniverseStore
 from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
@@ -85,6 +86,7 @@ def get_micro_readiness(
     dataset_store: DatasetStore = Depends(get_dataset_store),
     cache: MicroReadinessCache = Depends(get_micro_readiness_cache),
     playbook_store: PlaybookStore = Depends(get_playbook_store),
+    bar_store: BarStore = Depends(get_bar_store),
 ) -> dict:
     """J-01's corpus-truth fold: the honest per-shard inventory, corpus totals beside the
     referee's tick-gate figure, and the three pilot studies' floor table -- see
@@ -95,9 +97,21 @@ def get_micro_readiness(
 
     J-03: ``playbook_store`` is the EXISTING ``desk_routes.get_playbook_store`` dependency,
     reused verbatim (never a second, redefined provider) -- it feeds the ``joinable_corpus``
-    field, computed by ``micro_join.joinable_corpus_counts``."""
+    field, computed by ``micro_join.joinable_corpus_counts``.
+
+    J-09: ``resolver`` is constructed HERE, per request, from the EXISTING ``routes.get_bar_store``
+    dependency plus ``CONFIG`` -- the ``desk_routes.py`` ``GET .../playbook/{id}/context`` route's
+    OWN construction call, verbatim (``BandMapResolver(bar_store, CONFIG)`` defaults to
+    ``compute=False``, so this GET never computes a tradable map it does not already hold -- T-8).
+    It materializes ``joinable_corpus.band_touch_count`` from the ``not_enumerated`` sentinel to a
+    real int (``micro_join.py``'s own docstring); nothing else in this payload changes shape."""
+    resolver = BandMapResolver(bar_store, CONFIG)
     return build_readiness(
-        dataset_store, cache, dataset_dir=CONFIG.dataset_dir_resolved(), playbook_store=playbook_store
+        dataset_store,
+        cache,
+        dataset_dir=CONFIG.dataset_dir_resolved(),
+        playbook_store=playbook_store,
+        resolver=resolver,
     )
 
 
@@ -237,17 +251,42 @@ def get_scout(ledger_dir: str = Depends(get_scout_ledger_dir)) -> dict:
     }
 
 
+class ScoutComputeRequest(BaseModel):
+    """Body for ``POST /research/desk/micro/scout/compute`` (J-09, additive). ``grid`` defaults to
+    ``None`` -- omitted (or the body omitted entirely, same as every pre-J-09 caller), this route's
+    behavior stays byte-identical: the unchanged default reference grid.
+    ``scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`` runs ONLY the ONE J-09 pilot candidate this era
+    screens (Studies 1/3 stay frozen-in-source only -- structurally unreachable through this
+    route)."""
+
+    grid: str | None = None
+
+
 @router.post("/scout/compute")
 def trigger_scout_compute(
+    body: ScoutComputeRequest | None = None,
     dataset_store: DatasetStore = Depends(get_dataset_store),
     snapshots_dir: str = Depends(get_micro_snapshots_dir),
     ledger_dir: str = Depends(get_scout_ledger_dir),
+    bar_store: BarStore = Depends(get_bar_store),
     manager: ScoutComputeManager = Depends(get_scout_compute_manager),
 ) -> dict:
     """Start a Scout screening run over the bounded reference candidate grid (ensuring
     prerequisite snapshots exist first -- reuse-or-build), or refuse (single-flight) if one is
-    already running."""
-    result = manager.trigger(dataset_store, CONFIG, snapshots_dir, ledger_dir)
+    already running.
+
+    J-09: ``body.grid`` selects ``ScoutComputeManager.trigger``'s own ``grid_selector`` -- see
+    that method's docstring. ``bar_store`` is an ADDITIVE dependency (the SAME
+    ``routes.get_bar_store`` the readiness route now also uses); constructing the
+    ``BandMapResolver`` it feeds is CONDITIONAL on a non-default selector -- this is a POST,
+    operator-triggered act (never a page-load GET), so the construction cost only lands on the
+    request that actually asks for it."""
+    grid_selector = body.grid if body is not None else None
+    resolver = BandMapResolver(bar_store, CONFIG) if grid_selector is not None else None
+    result = manager.trigger(
+        dataset_store, CONFIG, snapshots_dir, ledger_dir,
+        grid_selector=grid_selector, resolver=resolver,
+    )
     if result["state"] == "refused":
         return result
     return {"state": result["state"], "run_id": result["run_id"]}
diff --git a/apps/backend/app/research/scout.py b/apps/backend/app/research/scout.py
index b7940db..745c236 100644
--- a/apps/backend/app/research/scout.py
+++ b/apps/backend/app/research/scout.py
@@ -7,14 +7,20 @@ economic-relevance column. Registers candidates through ``scout_ledger.py``'s ha
 the two production-boundary rules that module deliberately does NOT (module docstring there):
 ``SCOUT_MAX_VARIANTS_PER_FAMILY`` (TC-9) and the TR-9 registration-ordering refusal (TC-7).
 
-**This iteration's registered grid is generic, never study-specific.** ``structure_context.kind ==
-"none"`` throughout: every trade-anchored snapshot row is an eligible anchor, with no playbook-
-signal or band-touch conditioning. A pilot-study-specific mechanism (range-wall failed aggression,
-delta divergence, capitulation exhaustion) is J-09's own scope (goal.md OUT OF SCOPE); this module
-only builds and proves the generic screening machinery, and runs it on a bounded FIXTURE grid.
-``extract_anchors`` therefore refuses (a typed error, never a silent skip) any
-``structure_context.kind`` other than ``"none"`` -- there is no read path wired for the other two
-values yet.
+**``default_fixture_grid`` stays generic, never study-specific.** ``structure_context.kind ==
+"none"`` throughout its own registered grid: every trade-anchored snapshot row is an eligible
+anchor, with no playbook-signal or band-touch conditioning -- this era's OPERATOR-run production
+grid (the CLI, ``ScoutComputeManager``'s default trigger) is unchanged by J-09.
+
+**J-09 wires the other two ``structure_context.kind`` values, in a SEPARATE, frozen
+``pilot_study_candidate_grid``.** ``extract_anchors`` now supports ``"band_touch"`` (via
+``micro_join.enumerate_band_touches`` + ``micro_join.join_band_touch``) and ``"playbook_signal"``
+(via ``micro_join.join_playbook_signal``) -- ``ScoutUnsupportedStructureContextError`` still guards
+any FUTURE, genuinely-unsupported value (there is none today: the closed
+``STRUCTURE_CONTEXT_KINDS`` set is now fully wired). Only ONE of the three predeclared pilot-study
+candidates (delta divergence at level tests) is taken through ``register_and_screen_candidate``
+this iteration -- the other two exist frozen-in-source only (goal.md OUT OF SCOPE, explicitly
+deferred per the era's own scope-pressure order).
 
 **Read-side law: no second outcome implementation.** Anchor extraction reads snapshot rows through
 ``micro_accessor.MicroAccessor`` (J-05 re-point, unfenced -- TR-3's import-ban; after
@@ -70,7 +76,7 @@ import threading
 import uuid
 from collections import Counter
 from datetime import datetime, timezone
-from typing import Callable
+from typing import TYPE_CHECKING, Callable
 from zoneinfo import ZoneInfo
 
 import numpy as np
@@ -78,6 +84,7 @@ import numpy as np
 from ..config import CONFIG, Config
 from . import micro_features as mf
 from . import micro_join as mj
+from . import walkforward as wf
 from .datasets import DatasetNotFound, DatasetStore, parse_utc_epoch
 from .micro_accessor import MicroAccessor
 from .micro_snapshots import (
@@ -100,6 +107,11 @@ from .scout_ledger import (
     resolve_scout_ledger_dir,
 )
 
+if TYPE_CHECKING:  # pragma: no cover -- type-checking only, never a runtime import (no cycle risk)
+    from .desk_playbook import PlaybookStore
+    from .desk_playbook_context import BandMapResolver
+    from .micro_accessor import ExposureRegistry
+
 __all__ = [
     "SCOUT_BLOCK_PERMUTATIONS",
     "SCOUT_SCREEN_ALPHA",
@@ -129,7 +141,10 @@ __all__ = [
     "screen_candidate",
     "register_and_screen_candidate",
     "default_fixture_grid",
+    "pilot_study_candidate_grid",
+    "GRID_SELECTOR_DELTA_DIVERGENCE_PILOT",
     "run_scout_grid_and_record",
+    "register_screen_and_walkforward_check",
     "list_scout_families",
     "ScoutComputeManager",
     "main",
@@ -193,6 +208,15 @@ FEATURE_FAMILY_OF: dict[str, str] = {
     "microprice": "F-LIQUIDITY",
     "spread_change_20t": "F-LIQUIDITY",
     "spread_change_100t": "F-LIQUIDITY",
+    # J-09 Study 2 (delta divergence at level tests): spec section 3's own F-FLOW bullet names
+    # `divergence_at_level` right beside `cumulative_delta` ("Divergence-at-level (Card 9.1,
+    # amended r2)") -- the SAME family, never a fourth invented one. `_extract_divergence_anchors`
+    # below is this feature's dedicated PAIRED-TOUCH extraction path (module docstring's own
+    # dispatch); its `feature_value` is `1.0`/`0.0` (never a fabricated third state) for
+    # `divergence_at_level(...)["bearish_divergence"] is True`/`False`, reusing the EXISTING
+    # threshold-transform membership check (`op="ge", value=1.0`) rather than inventing a second
+    # "boolean" transform kind.
+    "divergence_at_level_bearish": "F-FLOW",
 }
 
 # spec section 3/5.4: F-FLOW and F-RESPONSE are derived from the engine's aggressor SIDE
@@ -238,10 +262,10 @@ class ScoutUnsupportedHorizonError(Exception):
 
 
 class ScoutUnsupportedStructureContextError(Exception):
-    """``structure_context.kind`` names a value ``extract_anchors`` has no read path for this
-    iteration -- ``"playbook_signal"``/``"band_touch"``-conditioned candidates are J-09's
-    pilot-study-specific scope (goal.md OUT OF SCOPE); this iteration's registered grid uses
-    ``"none"`` only (module docstring)."""
+    """``structure_context.kind`` names a value ``extract_anchors`` has no read path for -- as of
+    J-09, this can only fire for a value outside the closed ``STRUCTURE_CONTEXT_KINDS`` set itself
+    (``"none"``/``"band_touch"``/``"playbook_signal"`` are all wired -- module docstring); kept as
+    the guard against any FUTURE addition to that set arriving with no extraction path yet."""
 
 
 def scout_stream(
@@ -356,35 +380,23 @@ def _cached_dataset_rows(
     return dataset_meta, rows
 
 
-def extract_anchors(
-    *,
-    feature_name: str,
-    structure_context_kind: str,
-    horizon_key: str,
-    sidedness: str | None,
-    corpus_manifest: list[dict],
-    dataset_store: DatasetStore,
-    snapshots_dir: str,
-    config: Config,
-    rows_cache: dict[str, list[dict]] | None = None,
-) -> list[dict]:
-    """One row per eligible trade-anchored snapshot row across ``corpus_manifest`` (spec section
-    5.1's own field -- a list of ``{"dataset_id": ...}`` entries): ``{dataset_id, symbol,
-    session_date, anchor_at, trade_index, feature_value, outcome_value, tod_bucket,
-    fallback_frac}``. Never triggers a snapshot build (T-8: reads never compute) -- a dataset with
-    no currently-valid snapshot is an honest skip, not a fabricated row (TR-7's own "rebuild, never
-    serve stale", applied to a reader that never rebuilds at all). ``rows_cache`` is the
-    ``_cached_dataset_rows`` opt-in (see that function's own docstring) -- ``None`` by default,
-    every existing call site's exact prior behavior."""
-    if structure_context_kind != "none":
-        raise ScoutUnsupportedStructureContextError(
-            f"structure_context.kind={structure_context_kind!r} has no anchor-extraction path "
-            "this iteration -- pilot-study-specific joins (playbook_signal/band_touch) are J-09's "
-            "scope (goal.md OUT OF SCOPE); J-04 registers structure_context.kind='none' "
-            "candidates only"
-        )
-    horizon_kind, horizon_value = HORIZON_KEYS[horizon_key]
+def _outcome_at_horizon(outcomes: list[dict], horizon_kind: str, horizon_value: int) -> dict | None:
+    """Picks the ONE entry matching ``(horizon_kind, horizon_value)`` out of an already-computed
+    closed outcome set (``micro_join.join_band_touch``/``join_playbook_signal``'s own ``outcomes``
+    list, built by ``_outcome_rows_after``) -- a LOOKUP, never a recompute (the read-side law: this
+    module adds no new outcome math, module docstring)."""
+    for outcome in outcomes:
+        if outcome["horizon_kind"] == horizon_kind and outcome["horizon_value"] == horizon_value:
+            return outcome
+    return None
+
 
+def _extract_none_anchors(
+    *, feature_name, horizon_kind, horizon_value, sidedness, corpus_manifest, dataset_store,
+    snapshots_dir, config, rows_cache,
+) -> list[dict]:
+    """``structure_context.kind == "none"`` -- every trade-anchored snapshot row is an eligible
+    anchor (the ORIGINAL J-04 body, unmodified)."""
     anchors: list[dict] = []
     for entry in corpus_manifest:
         dataset_id = entry["dataset_id"]
@@ -431,6 +443,316 @@ def extract_anchors(
     return anchors
 
 
+def _extract_band_touch_anchors(
+    *, feature_name, horizon_kind, horizon_value, sidedness, corpus_manifest, dataset_store,
+    snapshots_dir, config, rows_cache, resolver,
+) -> list[dict]:
+    """``structure_context.kind == "band_touch"``, GENERIC single-touch path (J-09): every
+    enumerated wall touch (``micro_join.enumerate_band_touches``) is one candidate anchor, joined
+    via ``micro_join.join_band_touch`` (the SAME join primitive J-03 already proved -- no second
+    join implementation). ``feature_name == "divergence_at_level_bearish"`` dispatches to
+    ``_extract_divergence_anchors`` instead (that feature needs a PAIR of consecutive touches on
+    the same band, never a single-touch row -- spec section 3's own formula)."""
+    if feature_name == _DIVERGENCE_FEATURE_NAME:
+        return _extract_divergence_anchors(
+            corpus_manifest=corpus_manifest, dataset_store=dataset_store, snapshots_dir=snapshots_dir,
+            config=config, rows_cache=rows_cache, resolver=resolver, horizon_kind=horizon_kind,
+            horizon_value=horizon_value, sidedness=sidedness,
+        )
+    anchors: list[dict] = []
+    for entry in corpus_manifest:
+        dataset_id = entry["dataset_id"]
+        dataset_meta, _rows = _cached_dataset_rows(
+            dataset_id, dataset_store, snapshots_dir, config, rows_cache
+        )
+        if dataset_meta is None:
+            continue  # honest absence -- never a compute-on-read (T-8)
+        touches = mj.enumerate_band_touches(dataset_meta, dataset_store, resolver)
+        for touch in touches:
+            joined = mj.join_band_touch(touch, resolver, dataset_store, snapshots_dir, config)
+            if joined["status"] != mj.JOIN_STATUS_JOINED:
+                continue  # honest miss (no covering snapshot, no row before the touch)
+            feature_at_trigger = joined["feature_at_trigger"]
+            feature_value = feature_at_trigger.get(feature_name)
+            if feature_value is None:
+                continue
+            outcome = _outcome_at_horizon(joined["outcomes"], horizon_kind, horizon_value)
+            if outcome is None or outcome["mid"]["unmeasured"] or outcome["mid"]["truncated"]:
+                continue
+            anchors.append(
+                {
+                    "dataset_id": dataset_id,
+                    "symbol": touch["symbol"],
+                    "session_date": _session_date_for_dataset(dataset_meta),
+                    "anchor_at": feature_at_trigger["anchor_at"],
+                    "trade_index": feature_at_trigger["trade_index"],
+                    "feature_value": feature_value,
+                    "outcome_value": outcome["mid"]["value"],
+                    "tod_bucket": tod_bucket_for_epoch(touch["as_of_epoch"]),
+                    "fallback_frac": feature_at_trigger.get("fallback_frac_20t"),
+                }
+            )
+    return anchors
+
+
+def _windowed_trade_volumes(
+    trade_rows: list[dict], end_logical_ts: float, *, window_seconds: float, max_windows: int
+) -> list[float]:
+    """The trailing, NON-OVERLAPPING, WHOLE ``window_seconds``-long trade-volume windows ending at
+    ``end_logical_ts`` (spec section 3's "trailing-120s volume ... over the session-prefix baseline
+    windows" -- the SAME window length as the divergence trailing window itself,
+    ``BURST_BASELINE_TRAILING_WINDOWS`` of them at most). Only WHOLE windows that fit entirely
+    within the dataset's own recorded prefix (before ``end_logical_ts``) are ever counted -- the
+    caller (``divergence_delta_threshold``) already treats fewer than 5 as undefined, so this never
+    zero-pads a thin prefix into a false floor-clearing count."""
+    if not trade_rows:
+        return []
+    earliest_ts = trade_rows[0]["anchor_at"]
+    available_windows = int((end_logical_ts - earliest_ts) // window_seconds)
+    n_windows = max(0, min(max_windows, available_windows))
+    volumes: list[float] = []
+    window_end = end_logical_ts
+    for _ in range(n_windows):
+        window_start = window_end - window_seconds
+        volume = sum(
+            row["size"] for row in trade_rows if window_start <= row["anchor_at"] < window_end
+        )
+        volumes.append(float(volume))
+        window_end = window_start
+    return volumes
+
+
+def _extract_divergence_anchors(
+    *, corpus_manifest, dataset_store, snapshots_dir, config, rows_cache, resolver, horizon_kind,
+    horizon_value, sidedness,
+) -> list[dict]:
+    """Study 2's own PAIRED-touch anchor path (spec section 3, Card 9.1 amended r2): for every pair
+    of CONSECUTIVE touches (tau1 < tau2) of the SAME band within one dataset, reuses
+    ``micro_features.divergence_at_level`` VERBATIM over that pair's own cumulative-delta readings
+    (read straight off the two touches' own snapshot rows -- never recomputed) plus a trailing
+    ``(anchor_at, mid)`` price history and the session-prefix baseline trade-volume windows this
+    function builds (``_windowed_trade_volumes``) -- new plumbing this iteration wires (the
+    formula itself is 100% pre-coded; only its inputs were unbuilt, per the phase spec's own
+    BACKGROUND). ``feature_value`` is ``1.0``/``0.0`` for ``bearish_divergence`` True/False, ``None``
+    (excluded, never fabricated) when the formula itself is undefined (too little price/volume
+    history). The outcome is measured FROM tau2 (``available_at = tau2`` -- spec section 3's own
+    line), the later touch that fixes when the comparison could first be made."""
+    anchors: list[dict] = []
+    for entry in corpus_manifest:
+        dataset_id = entry["dataset_id"]
+        dataset_meta, rows = _cached_dataset_rows(
+            dataset_id, dataset_store, snapshots_dir, config, rows_cache
+        )
+        if dataset_meta is None:
+            continue
+        touches = mj.enumerate_band_touches(dataset_meta, dataset_store, resolver)
+        by_band: dict[str, list[dict]] = {}
+        for touch in touches:
+            by_band.setdefault(touch["band_id"], []).append(touch)
+
+        trade_rows = [r for r in rows if not r.get("close_out")]
+        session_end_ts = _session_end_logical_ts(dataset_meta)
+        session_date = _session_date_for_dataset(dataset_meta)
+        epoch_anchor = dataset_meta.get("epoch_anchor") or 0.0
+
+        for band_touches in by_band.values():
+            for tau1_touch, tau2_touch in zip(band_touches, band_touches[1:]):
+                tau1_logical = tau1_touch["as_of_epoch"] - epoch_anchor
+                tau2_logical = tau2_touch["as_of_epoch"] - epoch_anchor
+                tau1_row = mj.feature_row_at_trigger(rows, tau1_logical)
+                tau2_row = mj.feature_row_at_trigger(rows, tau2_logical)
+                if tau1_row is None or tau2_row is None:
+                    continue
+                cum_delta_tau1 = tau1_row.get("cumulative_delta")
+                cum_delta_tau2 = tau2_row.get("cumulative_delta")
+                if cum_delta_tau1 is None or cum_delta_tau2 is None:
+                    continue
+                price_history = [
+                    (row["anchor_at"], row["mid"])
+                    for row in trade_rows
+                    if tau1_logical - mf.DIVERGENCE_TRAILING_SECONDS <= row["anchor_at"] <= tau2_logical
+                    and row.get("mid") is not None
+                ]
+                baseline_volumes = _windowed_trade_volumes(
+                    trade_rows, tau1_logical,
+                    window_seconds=mf.DIVERGENCE_TRAILING_SECONDS,
+                    max_windows=mf.BURST_BASELINE_TRAILING_WINDOWS,
+                )
+                divergence = mf.divergence_at_level(
+                    price_history=price_history, tau1=tau1_logical, tau2=tau2_logical,
+                    cum_delta_at_tau1=cum_delta_tau1, cum_delta_at_tau2=cum_delta_tau2,
+                    baseline_volumes=baseline_volumes,
+                )
+                bearish = divergence["bearish_divergence"]
+                if bearish is None:
+                    continue  # undefined (thin price/volume history) -- excluded, never fabricated
+                feature_value = 1.0 if bearish else 0.0
+
+                tau2_pos = trade_rows.index(tau2_row)
+                outcome = mj.outcome_row_at_single_horizon(
+                    trade_rows, tau2_pos, horizon_kind, horizon_value, session_end_ts,
+                    side=sidedness,
+                )
+                if outcome is None or outcome["mid"]["unmeasured"] or outcome["mid"]["truncated"]:
+                    continue
+                anchors.append(
+                    {
+                        "dataset_id": dataset_id,
+                        "symbol": tau2_touch["symbol"],
+                        "session_date": session_date,
+                        "anchor_at": tau2_row["anchor_at"],
+                        "trade_index": tau2_row["trade_index"],
+                        "feature_value": feature_value,
+                        "outcome_value": outcome["mid"]["value"],
+                        "tod_bucket": tod_bucket_for_epoch(epoch_anchor + tau2_row["anchor_at"]),
+                        "fallback_frac": tau2_row.get("fallback_frac_20t"),
+                    }
+                )
+    return anchors
+
+
+def _signal_in_dataset_window(signal: dict, dataset_meta: dict) -> bool:
+    """A small technical window-containment check, mirroring ``micro_join._covering_dataset``'s OWN
+    ``(symbol, window)`` match -- re-implemented locally (rather than imported) because it is
+    scoped to ONE already-known dataset, not a store-wide search; the same class of judgment call
+    ``micro_join.py``'s own docstring already documents for mirroring rather than importing a
+    sibling module's small technical helper."""
+    symbol = signal.get("symbol")
+    trigger_ts = signal.get("trigger_ts")
+    if not symbol or not trigger_ts or symbol != dataset_meta["symbol"]:
+        return False
+    trigger_epoch = parse_utc_epoch(trigger_ts)
+    return (
+        parse_utc_epoch(dataset_meta["window_start_utc"])
+        <= trigger_epoch
+        <= parse_utc_epoch(dataset_meta["window_end_utc"])
+    )
+
+
+def _extract_playbook_signal_anchors(
+    *, feature_name, horizon_kind, horizon_value, sidedness, corpus_manifest, dataset_store,
+    snapshots_dir, config, rows_cache, playbook_store, setup_id,
+) -> list[dict]:
+    """``structure_context.kind == "playbook_signal"`` (J-09): every recorded playbook signal whose
+    ``(symbol, trigger_ts)`` falls inside a dataset already in ``corpus_manifest`` is one candidate
+    anchor, joined via ``micro_join.join_playbook_signal`` (the SAME join primitive J-03 already
+    proved). ``setup_id`` (``None`` by default) narrows to signals carrying that exact value verbatim
+    (Study 3's own ``setup_id="capitulation"`` -- goal.md's stated frozen field) -- omitted, every
+    recorded setup is eligible."""
+    playbook_records, _errors = playbook_store.list()
+    all_signals = [
+        signal
+        for record in playbook_records
+        for signal in (record.get("signals") or [])
+        if setup_id is None or signal.get("setup_id") == setup_id
+    ]
+    anchors: list[dict] = []
+    for entry in corpus_manifest:
+        dataset_id = entry["dataset_id"]
+        dataset_meta, _rows = _cached_dataset_rows(
+            dataset_id, dataset_store, snapshots_dir, config, rows_cache
+        )
+        if dataset_meta is None:
+            continue
+        for signal in all_signals:
+            if not _signal_in_dataset_window(signal, dataset_meta):
+                continue
+            joined = mj.join_playbook_signal(signal, dataset_store, snapshots_dir, config)
+            if joined["status"] != mj.JOIN_STATUS_JOINED:
+                continue
+            feature_at_trigger = joined["feature_at_trigger"]
+            feature_value = feature_at_trigger.get(feature_name)
+            if feature_value is None:
+                continue
+            outcome = _outcome_at_horizon(joined["outcomes"], horizon_kind, horizon_value)
+            if outcome is None or outcome["mid"]["unmeasured"] or outcome["mid"]["truncated"]:
+                continue
+            trigger_epoch = parse_utc_epoch(signal["trigger_ts"])
+            anchors.append(
+                {
+                    "dataset_id": dataset_id,
+                    "symbol": signal.get("symbol"),
+                    "session_date": _session_date_for_dataset(dataset_meta),
+                    "anchor_at": feature_at_trigger["anchor_at"],
+                    "trade_index": feature_at_trigger["trade_index"],
+                    "feature_value": feature_value,
+                    "outcome_value": outcome["mid"]["value"],
+                    "tod_bucket": tod_bucket_for_epoch(trigger_epoch),
+                    "fallback_frac": feature_at_trigger.get("fallback_frac_20t"),
+                }
+            )
+    return anchors
+
... [diff_bound] apps/backend/app/research/scout.py: 453 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/walkforward.py b/apps/backend/app/research/walkforward.py
index 08474b3..b9ca630 100644
--- a/apps/backend/app/research/walkforward.py
+++ b/apps/backend/app/research/walkforward.py
@@ -154,6 +154,7 @@ __all__ = [
     "playbook_observations",
     "run_diagnostic_walkforward",
     "run_tick_family_fold_request",
+    "scout_candidate_walkforward_floor_check",
     "main",
 ]
 
@@ -1132,6 +1133,73 @@ def run_tick_family_fold_request(ledger: WalkForwardLedger, config: Config) -> d
     }
 
 
+def scout_candidate_walkforward_floor_check(
+    exposure_registry: ExposureRegistry,
+    *,
+    corpus_id: str,
+    observations: list[dict],
+    registered_at: str,
+) -> dict:
+    """Whether a Scout candidate's own anchor corpus (goal.md J-09) clears the floor for ONE
+    walk-forward fold BEFORE any fold is ever evaluated -- the SAME typed-refusal-BEFORE-any-
+    evaluation discipline ``run_tick_family_fold_request`` established for the diagnostic run's own
+    corpus-wide session count (iter-8), applied here to ONE candidate's own ``{session_date,
+    symbol, value}`` observations (the exact shape ``playbook_observations`` and
+    ``summarize_fold_observations`` already share) instead of a corpus-wide inventory.
+
+    **Class law, applied at the floor boundary (spec section 6.7).** Only sessions NOT already
+    exposed before ``registered_at`` count toward this floor -- a session the exposure registry
+    already marks exposed contributes ZERO oos observations, exactly the "evidence classes never
+    mix" rail (a diagnostic-class observation must never sneak into a class-2 floor count) applied
+    BEFORE the fold-evaluation function could ever be reached, not merely after. When
+    ``corpus_id`` has NO exposure entries at all (the registry was never r2-initialized for it in
+    this process), this function reads that as "nothing is yet PROVEN either exposed or unexposed"
+    and counts ZERO oos sessions -- never the opposite (an uninitialized registry's ``is_exposed_before``
+    always answers ``False``, which would otherwise let an already-published legacy corpus masquerade
+    as fresh out-of-sample evidence; the anti-goal this guards is worse than the false-negative
+    this conservative default trades for it).
+
+    Reuses ``summarize_fold_observations``'s own ``WF_FOLD_MIN_OBSERVATIONS``/``WF_FOLD_MIN_SIGNAL_
+    SESSIONS`` floors verbatim (no second floor arithmetic) plus a session-COUNT floor
+    (``WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS`` -- the SAME pair ``micro_readiness.py``'s own
+    ``study_floors`` table already reads for "enough sessions for even one fold to exist"). Returns
+    ``{"status": "sufficient"|"insufficient_n", "oos_session_count", "oos_observation_count",
+    "required_sessions", "missing"}`` -- ``missing`` is empty iff ``status == "sufficient"``.
+    Source-level guard-tested to NEVER call the fold-evaluation function walk-forward folds are
+    actually SCORED through -- this function only decides whether that call would be legitimate
+    (T-8, applied to a floor rather than a compute)."""
+    all_sessions = sorted({o["session_date"] for o in observations})
+    if not has_any_exposure_entries(exposure_registry, corpus_id):
+        oos_sessions: list[str] = []
+    else:
+        oos_sessions = [
+            s for s in all_sessions
+            if not exposure_registry.is_exposed_before(corpus_id=corpus_id, window=s, instant=registered_at)
+        ]
+    oos_observations = [o for o in observations if o["session_date"] in set(oos_sessions)]
+
+    floors = {
+        "wf_fold_min_observations": WF_FOLD_MIN_OBSERVATIONS,
+        "wf_fold_min_signal_sessions": WF_FOLD_MIN_SIGNAL_SESSIONS,
+    }
+    summary = summarize_fold_observations(oos_observations, floors)
+    missing = dict(summary["missing"])
+    required_sessions = WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS
+    if len(oos_sessions) < required_sessions:
+        missing["oos_sessions"] = (
+            f"{len(oos_sessions)} < {required_sessions} "
+            "(WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS)"
+        )
+    status = "insufficient_n" if missing else "sufficient"
+    return {
+        "status": status,
+        "oos_session_count": len(oos_sessions),
+        "oos_observation_count": summary["n"],
+        "required_sessions": required_sessions,
+        "missing": missing,
+    }
+
+
 def playbook_observations(
     playbook_store, *, setup_ids: tuple[str, ...], horizon_label: str, default_signature: str, exclude_session_dates: tuple[str, ...] = ()
 ) -> list[dict]:
diff --git a/apps/backend/tests/test_micro_join.py b/apps/backend/tests/test_micro_join.py
index 9577ce7..86907fa 100644
--- a/apps/backend/tests/test_micro_join.py
+++ b/apps/backend/tests/test_micro_join.py
@@ -32,7 +32,7 @@ from app.research import desk_playbook as desk_playbook_module
 from app.research import desk_playbook_context as desk_playbook_context_module
 from app.research import micro_join
 from app.research import vault
-from app.research.datasets import DatasetStore
+from app.research.datasets import DatasetStore, parse_utc_epoch
 from app.research.desk_playbook import PlaybookStore, playbook_parameters
 from app.research.desk_playbook_context import BandMapResolver
 from app.research.micro_snapshots import read_snapshot_rows, resolve_micro_snapshots_dir, run_snapshot_build_and_record
@@ -382,6 +382,170 @@ def test_tc2_an_uncached_band_map_is_an_honest_absence_never_a_fabricated_wall(p
     assert result["outcomes"] == []
 
 
+# --- TC-3 (goal-rapid-microscope-iter-21, J-09): the band-touch enumerator, a hand-derived oracle ---
+#
+# A fully synthetic dataset (never the PG fixture -- the "hand-derived oracle fixture" testing style
+# ``scout.py``'s own module docstring names) so every touch instant is chosen, never reverse-
+# engineered from real prints. ``enumerate_band_touches`` reads RAW dataset events
+# (``DatasetStore.load_events``, an existing store reader -- never a snapshot), so no snapshot build
+# is needed here at all.
+
+_TOUCH_BAND = {"side": "resistance", "price_low": 149.00, "price_high": 149.02}
+
+
+def _plant_touch_timeline(store: DatasetStore, *, symbol: str = "TQE") -> dict:
+    """A trade price sequence crossing ``_TOUCH_BAND`` at exactly 3 known instants (t=1.0, 4.0,
+    6.0), fully exiting the band between each (the ``setups.py`` ``_touches`` "re-arm only once
+    fully exited" rule, mirrored for a TRADE price rather than a bar range -- module docstring)."""
+    events = [
+        QuoteEvent(symbol, 0.0, 148.98, 149.03, 100, 100),
+        TradeEvent(symbol, 0.0, 148.90, 10, Side.SELL),  # outside (below) -- armed stays True
+        TradeEvent(symbol, 1.0, 149.01, 10, Side.BUY),  # TOUCH #1
+        TradeEvent(symbol, 2.0, 149.01, 10, Side.BUY),  # still inside -- no new touch
+        TradeEvent(symbol, 3.0, 148.90, 10, Side.SELL),  # exits below -- re-arms
+        TradeEvent(symbol, 4.0, 149.015, 10, Side.BUY),  # TOUCH #2
+        TradeEvent(symbol, 5.0, 149.05, 10, Side.BUY),  # exits above -- re-arms
+        TradeEvent(symbol, 6.0, 149.00, 10, Side.BUY),  # TOUCH #3 (the price_low boundary, inclusive)
+        TradeEvent(symbol, 7.0, 149.019, 10, Side.BUY),  # still inside -- no new touch
+    ]
+    meta = store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-touch-fixture",
+        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+        data_feed="sip", epoch_anchor=0.0, events=events,
+    )
+    return meta
+
+
+def test_tc3_enumerate_band_touches_returns_exactly_3_ordered_touch_records(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _plant_touch_timeline(dataset_store)
+    resolver = _resolver(tmp_path)
+    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key("TQE", window_start_epoch), {"basis_day": "2026-06-08", "bands": [_TOUCH_BAND]}
+    )
+
+    touches = micro_join.enumerate_band_touches(meta, dataset_store, resolver)
+
+    assert [t["as_of_epoch"] for t in touches] == [1.0, 4.0, 6.0]
+    assert all(t["symbol"] == "TQE" for t in touches)
+    band_id = touches[0]["band_id"]
+    assert all(t["band_id"] == band_id for t in touches)  # the SAME wall, every touch
+    assert isinstance(band_id, str) and band_id  # a stable, non-empty identifier
+
+
+def test_tc3_enumerate_band_touches_is_an_honest_empty_list_when_no_band_map_resolves(tmp_path):
+    """An unresolved band map (``compute=False``, nothing published) is an honest empty list --
+    never a fabricated touch."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _plant_touch_timeline(dataset_store, symbol="ZUX")
+    resolver = _resolver(tmp_path)  # nothing published -- a genuine miss
+
+    touches = micro_join.enumerate_band_touches(meta, dataset_store, resolver)
+
+    assert touches == []
+
+
+def test_tc3_enumerate_band_touches_is_an_honest_empty_list_when_the_map_has_no_bands(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _plant_touch_timeline(dataset_store, symbol="VYP")
+    resolver = _resolver(tmp_path)
+    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key("VYP", window_start_epoch), {"basis_day": "2026-06-08", "bands": []}
+    )
+
+    touches = micro_join.enumerate_band_touches(meta, dataset_store, resolver)
+
+    assert touches == []
+
+
+def test_tc3_two_bands_arm_and_touch_independently(tmp_path):
+    """A trade inside BOTH bands at once touches both; a later trade re-arms only the band it has
+    fully exited."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    symbol = "DBW"
+    events = [
+        QuoteEvent(symbol, 0.0, 100.98, 101.03, 100, 100),
+        TradeEvent(symbol, 0.0, 101.01, 10, Side.BUY),  # inside BOTH bands -> 2 touches at t=0
+        TradeEvent(symbol, 1.0, 101.01, 10, Side.BUY),  # still inside both -- no new touches
+        TradeEvent(symbol, 2.0, 101.005, 10, Side.SELL),  # exits the narrow band [101.006,101.02]
+        # ... but stays inside the wide one [101.00, 101.05] -- only the narrow band re-arms
+        TradeEvent(symbol, 3.0, 101.01, 10, Side.BUY),  # re-touches the narrow band only
+    ]
+    meta = dataset_store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-touch-fixture",
+        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+        data_feed="sip", epoch_anchor=0.0, events=events,
+    )
+    wide_band = {"side": "resistance", "price_low": 101.00, "price_high": 101.05}
+    narrow_band = {"side": "resistance", "price_low": 101.006, "price_high": 101.02}
+    resolver = _resolver(tmp_path)
+    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key(symbol, window_start_epoch),
+        {"basis_day": "2026-06-08", "bands": [wide_band, narrow_band]},
+    )
+
+    touches = micro_join.enumerate_band_touches(meta, dataset_store, resolver)
+
+    by_band: dict[str, list[float]] = {}
+    for t in touches:
+        by_band.setdefault(t["band_id"], []).append(t["as_of_epoch"])
+    assert len(by_band) == 2
+    counts = sorted(len(v) for v in by_band.values())
+    assert counts == [1, 2]  # the wide band touches once (never re-armed); the narrow one twice
+
+
+# --- TC-9 (goal-rapid-microscope-iter-21, J-09): joinable_corpus_counts materializes the real int --
+
+
+def test_tc9_joinable_corpus_counts_materializes_band_touch_count_with_a_resolver(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _plant_touch_timeline(dataset_store)
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    resolver = _resolver(tmp_path)
+    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key("TQE", window_start_epoch), {"basis_day": "2026-06-08", "bands": [_TOUCH_BAND]}
+    )
+
+    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store, resolver=resolver)
+
+    assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_ENUMERATED, "count": 3}
+
+
+def test_tc9_joinable_corpus_counts_omitting_resolver_still_serves_the_sentinel(tmp_path):
+    """Byte-identical to every pre-J-09 caller when ``resolver`` is omitted (module docstring)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _plant_touch_timeline(dataset_store)
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+
+    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+
+    assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
+
+
+def test_tc9_joinable_corpus_counts_excludes_a_withheld_shard_from_band_touch_count(tmp_path):
+    """The SAME withheld-excluded ``records`` the playbook loop already reads -- a sealed shard's
+    events are never read for the band-touch count either (the era's *(critical)* anti-goal: no
+    exploratory read of a sealed shard)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    sealed_meta = _plant_touch_timeline(dataset_store)
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    resolver = _resolver(tmp_path)
+    window_start_epoch = parse_utc_epoch(sealed_meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key("TQE", window_start_epoch), {"basis_day": "2026-06-08", "bands": [_TOUCH_BAND]}
+    )
+    _seal(dataset_store, sealed_meta)
+
+    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store, resolver=resolver)
+
+    assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_ENUMERATED, "count": 0}
+    assert counts["withheld_excluded"] == 1
+
+
 # --- joinable_corpus_counts (micro_readiness.py's new field; TC-5's own computation) -----------------
 
 
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
index 237de10..482e3ba 100644
--- a/apps/backend/tests/test_micro_readiness.py
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -25,7 +25,7 @@ from app.main import app
 from app.engine.aggressor import classify_aggressor
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import micro_readiness as micro_readiness_module
-from app.research.datasets import DatasetStore
+from app.research.datasets import DatasetStore, parse_utc_epoch
 from app.research.micro_readiness import (
     EXPOSURE_STATE_EXPLORATORY,
     PILOT_STUDY_IDS,
@@ -36,12 +36,15 @@ from app.research.micro_readiness import (
     build_readiness,
     resolve_micro_readiness_cache_db_path,
 )
+from app.research.bars import BarStore
 from app.research.desk_playbook import PlaybookStore, playbook_parameters
+from app.research.desk_playbook_context import BandMapResolver
 from app.research.desk_routes import get_playbook_store
-from app.research.micro_join import joinable_corpus_counts
+from app.research.micro_join import BAND_TOUCH_STATUS_ENUMERATED, joinable_corpus_counts
 from app.research.micro_routes import get_micro_readiness_cache
 from app.research.referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
-from app.research.routes import get_dataset_store
+from app.research.routes import get_bar_store, get_dataset_store
+from app.research.tradability_cache import TradabilityCache, resolve_tradability_cache_db_path
 from app.research import vault
 
 _ET = ZoneInfo("America/New_York")
@@ -92,14 +95,21 @@ def client(tmp_path):
     # tmp_path-scoped, empty-by-default one, so this fixture's existing hermeticity contract is
     # unaffected (never the real, ambient .data/playbook directory).
     playbook_store = PlaybookStore(tmp_path / "playbook")
+    # J-09: the route now also depends on a bar store (the resolver that materializes
+    # `band_touch_count` -- `BandMapResolver.__init__` unconditionally lists it) -- a
+    # tmp_path-scoped, empty-by-default one, the SAME hermeticity discipline as the playbook store
+    # above, never the real, ambient `.data/bars` directory.
+    bar_store = BarStore(tmp_path / "bars")
     app.dependency_overrides[get_dataset_store] = lambda: dataset_store
     app.dependency_overrides[get_micro_readiness_cache] = lambda: cache
     app.dependency_overrides[get_playbook_store] = lambda: playbook_store
+    app.dependency_overrides[get_bar_store] = lambda: bar_store
     with TestClient(app) as c:
         yield c, dataset_store, cache
     app.dependency_overrides.pop(get_dataset_store, None)
     app.dependency_overrides.pop(get_micro_readiness_cache, None)
     app.dependency_overrides.pop(get_playbook_store, None)
+    app.dependency_overrides.pop(get_bar_store, None)
 
 
 # --- _quote_rule_decides: cross-validated against classify_aggressor's own OBSERVABLE behavior ------
@@ -544,9 +554,11 @@ def test_joinable_corpus_is_served_through_the_route_and_is_non_negative_and_nev
     assert first == second
     for key in ("total", "playbook_signal_count"):
         assert isinstance(first[key], int) and first[key] >= 0
-    # band_touch_count is a typed "not enumerated" state, never a bare int (iter-4 passenger fix,
-    # TC-15) -- distinguishable from a real zero count.
-    assert first["band_touch_count"] == {"status": "not_enumerated", "count": None}
+    # band_touch_count is a typed state, never a bare int (iter-4 passenger fix, TC-15) --
+    # distinguishable from a real count read straight off the field. J-09 materializes the ROUTE's
+    # own value (this fixture's tmp_path-scoped bar store carries no tradable map, so an honest
+    # real zero, never the pre-J-09 sentinel -- see the dedicated TC-15 block below).
+    assert first["band_touch_count"] == {"status": BAND_TOUCH_STATUS_ENUMERATED, "count": 0}
     assert first["playbook_signal_count"] == 1  # only the in-window signal counts
     assert first["by_setup_id"] == {"jbe": 1}
 
@@ -569,20 +581,79 @@ def test_real_corpus_readiness_still_serves_an_honest_zero_joinable_corpus_witho
 
 
 # --- TC-15 (iter-4 passenger fix, docs/phases/goal-rapid-microscope-iter-4.md): band_touch_count is
-# a typed "not enumerated" state on THIS route, never a bare zero a reader could mistake for a real
-# count ------------------------------------------------------------------------------------------
+# a typed state on THIS route, never a bare int a reader could mistake for something else. J-09
+# (docs/phases/goal-rapid-microscope-iter-21.md, TC-9) materializes the route's OWN value: it now
+# ALWAYS constructs a resolver (`micro_routes.get_micro_readiness`'s own docstring), so this route's
+# served state is `enumerated` from this iteration forward -- `build_readiness` called DIRECTLY
+# without a `resolver` (every other caller in this file) still serves the honest `not_enumerated`
+# sentinel unchanged (`micro_join.py`'s own "byte-identical when omitted" contract). ---------------
 
 
-def test_tc15_readiness_route_serves_band_touch_count_as_a_typed_not_enumerated_state(client):
+def test_tc15_readiness_route_serves_band_touch_count_as_a_typed_enumerated_state(client):
     c, _store, _cache = client
     resp = c.get("/research/desk/micro/readiness")
     assert resp.status_code == 200
     band_touch = resp.json()["joinable_corpus"]["band_touch_count"]
     assert not isinstance(band_touch, int)
-    assert band_touch == {"status": "not_enumerated", "count": None}
+    # No dataset planted in this test's own tmp_path corpus, and no tradable map exists in its
+    # tmp_path-scoped bar store either -- an honest, real ZERO (never the pre-J-09 sentinel).
+    assert band_touch == {"status": BAND_TOUCH_STATUS_ENUMERATED, "count": 0}
+
+
+# --- TC-9 (goal-rapid-microscope-iter-21, J-09): a 3-known-touch fixture, through the LIVE route --
+
+
+def _plant_touch_dataset(store: DatasetStore, *, symbol: str = "TQR") -> dict:
+    """A trade price sequence crossing a `[149.00, 149.02]` band at exactly 3 known instants
+    (t=1.0, 4.0, 6.0) -- the SAME hand-derived oracle pattern `test_micro_join.py`'s own TC-3
+    tests use, transcribed here so this route-level test can plant it directly (`_plant_dataset`
+    above uses a fixed, unrelated 3-event fixture built for the `fallback_frac` tests)."""
+    events = [
+        QuoteEvent(symbol, 0.0, 148.98, 149.03, 100, 100),
+        TradeEvent(symbol, 0.0, 148.90, 10, Side.SELL),
+        TradeEvent(symbol, 1.0, 149.01, 10, Side.BUY),
+        TradeEvent(symbol, 2.0, 149.01, 10, Side.BUY),
+        TradeEvent(symbol, 3.0, 148.90, 10, Side.SELL),
+        TradeEvent(symbol, 4.0, 149.015, 10, Side.BUY),
+        TradeEvent(symbol, 5.0, 149.05, 10, Side.BUY),
+        TradeEvent(symbol, 6.0, 149.00, 10, Side.BUY),
+        TradeEvent(symbol, 7.0, 149.019, 10, Side.BUY),
+    ]
+    return store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-touch-fixture",
+        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+        data_feed="sip", epoch_anchor=0.0, events=events,
+    )
+
+
+def test_tc9_readiness_route_serves_the_real_band_touch_count_on_a_3_known_touch_fixture(client):
+    """TC-9, verbatim: given a fixture with 3 known wall touches, ``GET /research/desk/micro/
+    readiness`` serves ``joinable_corpus.band_touch_count == 3``, not the ``not_enumerated``
+    sentinel. Publishes the band map into the SAME on-disk cache the route's own internally
+    constructed ``BandMapResolver`` reads (``resolve_tradability_cache_db_path`` over the
+    ``client`` fixture's own overridden ``bar_store``) -- never a second, in-process-only
+    resolver the route could not possibly see."""
+    c, store, _cache = client
+    meta = _plant_touch_dataset(store)
+    bar_store = app.dependency_overrides[get_bar_store]()  # the SAME override the route resolves
+    route_cache = TradabilityCache(resolve_tradability_cache_db_path(str(bar_store.root)))
+    resolver = BandMapResolver(bar_store, CONFIG, cache=route_cache)
+    window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key("TQR", window_start_epoch),
+        {"basis_day": "2026-06-08", "bands": [{"side": "resistance", "price_low": 149.00, "price_high": 149.02}]},
+    )
+
+    resp = c.get("/research/desk/micro/readiness")
+    assert resp.status_code == 200
+    band_touch = resp.json()["joinable_corpus"]["band_touch_count"]
+    assert band_touch == {"status": "enumerated", "count": 3}
 
 
 def test_tc15_real_corpus_readiness_also_serves_the_typed_band_touch_count(real_readiness):
+    """``real_readiness`` (module-scoped) calls ``build_readiness`` DIRECTLY, with no ``resolver``
+    -- byte-identical to every pre-J-09 caller (module docstring's own "omitting it keeps the
+    sentinel" contract), independent of what the LIVE route now serves."""
     band_touch = real_readiness["joinable_corpus"]["band_touch_count"]
     assert not isinstance(band_touch, int)
     assert band_touch["status"] == "not_enumerated"
diff --git a/apps/backend/tests/test_scout.py b/apps/backend/tests/test_scout.py
index 6d31072..358a0a5 100644
--- a/apps/backend/tests/test_scout.py
+++ b/apps/backend/tests/test_scout.py
@@ -12,7 +12,9 @@ from __future__ import annotations
 
 import json
 import shutil
+import tempfile
 import time
+from datetime import datetime, timezone
 from pathlib import Path
 
 import pytest
@@ -20,9 +22,12 @@ from fastapi.testclient import TestClient
 
 from app.config import CONFIG
 from app.main import app
+from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import micro_join as mj
 from app.research import scout, scout_ledger
-from app.research.datasets import DatasetStore
+from app.research.datasets import DatasetStore, parse_utc_epoch
+from app.research.desk_playbook import PlaybookStore, playbook_parameters
+from app.research.desk_playbook_context import BandMapResolver
 from app.research.micro_routes import (
     get_scout_compute_manager,
     get_scout_ledger_dir,
@@ -33,6 +38,7 @@ from app.research.micro_snapshots import (
 )
 from app.research.routes import get_dataset_store
 from app.research.micro_routes import get_micro_snapshots_dir
+from app.research.tradability_cache import TradabilityCache
 
 _FIXTURE_DIRS = [
     Path(__file__).resolve().parent / "fixtures" / "datasets",
@@ -539,15 +545,180 @@ def test_extract_anchors_returns_one_row_per_measured_trade_anchor(pg_snapshot_s
         assert a["tod_bucket"] in ("open", "mid", "close", None)
 
 
-def test_extract_anchors_refuses_a_non_none_structure_context():
+def test_extract_anchors_refuses_a_structure_context_outside_the_closed_set():
+    """J-09: ``"band_touch"``/``"playbook_signal"`` are now wired (see the dedicated TC-1/TC-2
+    tests below) -- ``ScoutUnsupportedStructureContextError`` fires only for a value genuinely
+    outside the closed ``STRUCTURE_CONTEXT_KINDS`` set."""
     with pytest.raises(scout.ScoutUnsupportedStructureContextError):
         scout.extract_anchors(
-            feature_name="cumulative_delta", structure_context_kind="playbook_signal",
+            feature_name="cumulative_delta", structure_context_kind="not_a_real_kind",
             horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
             snapshots_dir="/nonexistent", config=CONFIG,
         )
 
 
+def test_extract_anchors_band_touch_requires_a_resolver():
+    with pytest.raises(ValueError, match="requires a resolver"):
+        scout.extract_anchors(
+            feature_name="failed_aggression_score", structure_context_kind="band_touch",
+            horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
+            snapshots_dir="/nonexistent", config=CONFIG,
+        )
+
+
+def test_extract_anchors_playbook_signal_requires_a_playbook_store():
+    with pytest.raises(ValueError, match="requires a playbook_store"):
+        scout.extract_anchors(
+            feature_name="failed_aggression_score", structure_context_kind="playbook_signal",
+            horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
+            snapshots_dir="/nonexistent", config=CONFIG,
+        )
+
+
+# === TC-1/TC-2 (goal-rapid-microscope-iter-21, J-09): band_touch / playbook_signal are wired ======
+
+
+class _EmptyBarStore:
+    def __init__(self, root="/tmp/does-not-exist-scout-touch-test"):
+        self.root = root
+
+    def list(self):
+        return [], []
+
+
+def _touch_resolver(tmp_path) -> BandMapResolver:
+    return BandMapResolver(
+        _EmptyBarStore(), CONFIG, cache=TradabilityCache(str(tmp_path / "trad.db"))
+    )
+
+
+def test_tc1_extract_anchors_band_touch_returns_rows_joined_via_join_band_touch(pg_snapshot_store, tmp_path):
+    """TC-1: given ``structure_context_kind="band_touch"`` and a fixture dataset with a resolvable
+    band map, ``extract_anchors`` returns anchor rows joined via ``join_band_touch`` instead of
+    raising -- a WIDE band over the real PG price range (148.80-149.20) so at least one of the
+    fixture's ~1,000 real trade prints genuinely touches it."""
+    store, snapshots_dir, manifest = pg_snapshot_store
+    resolver = _touch_resolver(tmp_path)
+    first_meta = store.get(manifest[0]["dataset_id"])
+    window_start_epoch = parse_utc_epoch(first_meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key("PG", window_start_epoch),
+        {"basis_day": "2026-06-08", "bands": [{"side": "resistance", "price_low": 148.80, "price_high": 149.20}]},
+    )
+
+    anchors = scout.extract_anchors(
+        feature_name="failed_aggression_score", structure_context_kind="band_touch",
+        horizon_key="trades_20", sidedness=None, corpus_manifest=manifest, dataset_store=store,
+        snapshots_dir=snapshots_dir, config=CONFIG, resolver=resolver,
+    )
+
+    assert anchors, "no anchors extracted -- the band never touched, or the join silently failed"
+    for a in anchors:
+        assert a["symbol"] == "PG"
+        assert isinstance(a["feature_value"], float)
+        assert isinstance(a["outcome_value"], float)
+
+
+def test_tc1_extract_anchors_band_touch_still_raises_for_a_kind_outside_the_closed_set():
+    with pytest.raises(scout.ScoutUnsupportedStructureContextError):
+        scout.extract_anchors(
+            feature_name="failed_aggression_score", structure_context_kind="not_a_real_kind",
+            horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
+            snapshots_dir="/nonexistent", config=CONFIG,
+        )
+
+
+def _plant_capitulation_signal(tmp_path, *, dataset_meta: dict) -> PlaybookStore:
+    """One recorded playbook signal, ``setup_id="capitulation"`` verbatim, whose ``trigger_ts``
+    falls inside ``dataset_meta``'s own window."""
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    window_start_epoch = parse_utc_epoch(dataset_meta["window_start_utc"])
+
+    trigger_dt = datetime.fromtimestamp(window_start_epoch + 5.0, tz=timezone.utc)
+    trigger_ts = trigger_dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
+    playbook_store.record(
+        session_date="2026-06-09",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature="sig-tc2-capitulation",
+        payload_version=1,
+        parameters=playbook_parameters(),
+        register="",
+        signals=[
+            {"symbol": dataset_meta["symbol"], "setup_id": "capitulation", "trigger_ts": trigger_ts},
+        ],
+        absences=[], diagnostics=[],
+    )
+    return playbook_store
+
+
+def test_tc2_extract_anchors_playbook_signal_carries_setup_id_verbatim(pg_snapshot_store, tmp_path):
+    """TC-2: given ``structure_context_kind="playbook_signal"`` and a fixture recorded signal with
+    ``setup_id="capitulation"``, ``extract_anchors`` returns an anchor row joined via
+    ``join_playbook_signal`` -- this module's own anchor row does not carry ``setup_id`` (the
+    "none"-path row shape, unchanged by J-09), so this test proves the join happened by asserting a
+    genuine, non-empty row grounded in the recorded signal's own window, and separately (below)
+    that ``join_playbook_signal`` itself carries ``setup_id`` verbatim (the underlying primitive
+    J-03 already proved -- this test proves J-09 REACHES it)."""
+    store, snapshots_dir, manifest = pg_snapshot_store
+    first_meta = store.get(manifest[0]["dataset_id"])
+    playbook_store = _plant_capitulation_signal(tmp_path, dataset_meta=first_meta)
+
+    anchors = scout.extract_anchors(
+        feature_name="failed_aggression_score", structure_context_kind="playbook_signal",
+        horizon_key="trades_20", sidedness=None, corpus_manifest=manifest, dataset_store=store,
+        snapshots_dir=snapshots_dir, config=CONFIG, playbook_store=playbook_store,
+    )
+
+    assert len(anchors) == 1
+    assert anchors[0]["symbol"] == "PG"
+    assert isinstance(anchors[0]["feature_value"], float)
+    assert isinstance(anchors[0]["outcome_value"], float)
+
+    # The underlying join primitive DOES carry setup_id verbatim (micro_join.py's own contract,
+    # J-03) -- proves the ROUTE this anchor traveled, not merely that a row exists.
+    signal = playbook_store.list()[0][0]["signals"][0]
+    joined = mj.join_playbook_signal(signal, store, snapshots_dir, CONFIG)
+    assert joined["status"] == mj.JOIN_STATUS_JOINED
+    assert joined["setup_id"] == "capitulation"
+
+
+def test_tc2_extract_anchors_playbook_signal_narrows_by_setup_id(pg_snapshot_store, tmp_path):
+    store, snapshots_dir, manifest = pg_snapshot_store
+    first_meta = store.get(manifest[0]["dataset_id"])
+    playbook_store = _plant_capitulation_signal(tmp_path, dataset_meta=first_meta)
+    # A second signal, a DIFFERENT setup_id, at a different instant -- must be excluded when
+    # narrowed to "capitulation".
+    window_start_epoch = parse_utc_epoch(first_meta["window_start_utc"])
+    other_ts = datetime.fromtimestamp(window_start_epoch + 8.0, tz=timezone.utc).isoformat(
+        timespec="microseconds"
+    ).replace("+00:00", "Z")
+    playbook_store.record(
+        session_date="2026-06-09",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature="sig-tc2-other",
+        payload_version=1,
+        parameters=playbook_parameters(),
+        register="",
+        signals=[{"symbol": "PG", "setup_id": "opening_range_break", "trigger_ts": other_ts}],
+        absences=[], diagnostics=[],
+    )
+
+    narrowed = scout.extract_anchors(
+        feature_name="failed_aggression_score", structure_context_kind="playbook_signal",
+        horizon_key="trades_20", sidedness=None, corpus_manifest=manifest, dataset_store=store,
+        snapshots_dir=snapshots_dir, config=CONFIG, playbook_store=playbook_store,
+        setup_id="capitulation",
+    )
+    unnarrowed = scout.extract_anchors(
+        feature_name="failed_aggression_score", structure_context_kind="playbook_signal",
+        horizon_key="trades_20", sidedness=None, corpus_manifest=manifest, dataset_store=store,
+        snapshots_dir=snapshots_dir, config=CONFIG, playbook_store=playbook_store,
+    )
+
+    assert len(narrowed) == 1
+    assert len(unnarrowed) == 2
+
+
 def test_extract_anchors_skips_a_dataset_with_no_currently_valid_snapshot(tmp_path):
     store = DatasetStore(tmp_path / "datasets")
     anchors = scout.extract_anchors(
@@ -732,6 +903,44 @@ def scout_client(tmp_path):
     app.dependency_overrides.pop(get_scout_compute_manager, None)
 
 
+# === J-09 (goal-rapid-microscope-iter-21): the additive grid-selector on POST /scout/compute =====
+
+
+def test_compute_route_omitted_body_is_byte_identical_to_the_default_grid(scout_client):
+    """The route's own additive-body contract: no body at all (every pre-J-09 caller) triggers the
+    UNCHANGED default reference grid -- ``candidates_total`` matches ``default_fixture_grid``'s own
+    width."""
+    c, store, snapshots_dir, ledger_dir, manager = scout_client
+    expected = len(scout.default_fixture_grid(store))
+
+    resp = c.post("/research/desk/micro/scout/compute")
+    assert resp.status_code == 200
+    assert resp.json()["state"] == "running"
+    manager.join_all(timeout=30.0)
+    assert manager.snapshot()["progress"]["candidates_total"] == expected
+
+
+def test_compute_route_pilot_grid_selector_runs_the_one_delta_divergence_candidate(scout_client):
+    """The additive ``{"grid": "delta_divergence_pilot"}`` body selects the ONE J-09 pilot
+    candidate this era screens -- ``candidates_total == 1``, never the 6-wide default grid, and
+    never Study 1/3 (structurally unreachable through this route -- goal.md OUT OF SCOPE)."""
+    c, store, snapshots_dir, ledger_dir, manager = scout_client
+
+    resp = c.post("/research/desk/micro/scout/compute", json={"grid": scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT})
+    assert resp.status_code == 200
+    assert resp.json()["state"] == "running"
+    manager.join_all(timeout=30.0)
+    snap = manager.snapshot()
+    assert snap["progress"]["candidates_total"] == 1
+    assert snap["state"] == "done"
+
+    ledger_body = c.get("/research/desk/micro/scout").json()
+    families = ledger_body["families"]
+    assert len(families) == 1
+    assert families[0]["trials"][0]["feature"]["name"] == scout._DIVERGENCE_FEATURE_NAME
+    assert families[0]["trials"][0]["structure_context"]["kind"] == "band_touch"
+
+
 def test_tc12_served_screen_carries_every_mandatory_disclosure(scout_client):
     c, store, snapshots_dir, ledger_dir, manager = scout_client
     manager.trigger(store, CONFIG, snapshots_dir, ledger_dir)
@@ -976,3 +1185,329 @@ def test_runs_route_lists_a_completed_job(scout_client):
     assert len(runs) == 1
     assert runs[0]["run_id"] == run_id
     assert runs[0]["state"] == "done"
+
+
+# === TC-4/TC-7 (goal-rapid-microscope-iter-21, J-09): the pilot-study candidate grid =================
+
+
+def test_tc4_pilot_study_candidate_grid_carries_all_three_requests_in_priority_order(tmp_path):
+    store = _combined_fixture_store(tmp_path)
+    grid = scout.pilot_study_candidate_grid(store)
+
+    assert list(grid.keys()) == [
+        scout.PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION,
+        scout.PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS,
+        scout.PILOT_STUDY_CAPITULATION_EXHAUSTION,
+    ]
+
+
+def test_tc4_every_pilot_request_carries_fully_constructed_frozen_fields(tmp_path):
+    store = _combined_fixture_store(tmp_path)
+    grid = scout.pilot_study_candidate_grid(store)
+
+    for study_id, request in grid.items():
+        spec = scout.build_candidate_spec_fields(
+            feature_name=request["feature_name"], transform=request["transform"],
+            params=request["params"], structure_context_kind=request["structure_context_kind"],
+            horizon_key=request["horizon_key"], sidedness=request["sidedness"],
+            fitting_rule=request["fitting_rule"], family_median_spread_bps=1.5,
+            corpus_manifest=request["corpus_manifest"], grid_version=request["grid_version"],
+            setup_id=request.get("setup_id"),
+        )
+        assert spec["feature"]["name"] and spec["feature"]["transform"] and spec["feature"]["params"], study_id
+        assert spec["structure_context"]["kind"] == request["structure_context_kind"], study_id
+        assert spec["outcome"]["horizon_key"] == request["horizon_key"], study_id
+        assert spec["econ_floor"]["floor_bps"] is not None, study_id
+
+
+def test_tc4_the_three_pilot_requests_have_three_distinct_family_root_ids(tmp_path):
+    store = _combined_fixture_store(tmp_path)
+    grid = scout.pilot_study_candidate_grid(store)
+
+    root_ids = set()
+    for request in grid.values():
+        spec = scout.build_candidate_spec_fields(
+            feature_name=request["feature_name"], transform=request["transform"],
+            params=request["params"], structure_context_kind=request["structure_context_kind"],
+            horizon_key=request["horizon_key"], sidedness=request["sidedness"],
+            fitting_rule=request["fitting_rule"], family_median_spread_bps=1.5,
+            corpus_manifest=request["corpus_manifest"], grid_version=request["grid_version"],
+            setup_id=request.get("setup_id"),
+        )
+        root_ids.add(spec["family_root_id"])
+    assert len(root_ids) == 3
+
+
+def test_tc4_capitulation_request_carries_its_setup_id_in_structure_context(tmp_path):
+    store = _combined_fixture_store(tmp_path)
+    request = scout.pilot_study_candidate_grid(store)[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION]
+    assert request["structure_context_kind"] == "playbook_signal"
+    assert request["setup_id"] == "capitulation"
+
+    spec = scout.build_candidate_spec_fields(
+        feature_name=request["feature_name"], transform=request["transform"],
+        params=request["params"], structure_context_kind=request["structure_context_kind"],
+        horizon_key=request["horizon_key"], sidedness=request["sidedness"],
+        fitting_rule=request["fitting_rule"], family_median_spread_bps=1.5,
+        corpus_manifest=request["corpus_manifest"], grid_version=request["grid_version"],
+        setup_id=request["setup_id"],
+    )
+    assert spec["structure_context"] == {"kind": "playbook_signal", "setup_id": "capitulation"}
+
+
+def test_tc4_setup_id_omitted_from_structure_context_when_not_given():
+    """A pre-J-09 caller (never passing ``setup_id``) sees the IDENTICAL, byte-unmodified
+    ``structure_context`` shape -- ``{"kind": ...}`` alone, no key added."""
+    spec = scout.build_candidate_spec_fields(
+        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
+        structure_context_kind="none", horizon_key="trades_20", sidedness=None, fitting_rule=None,
+        family_median_spread_bps=1.5, corpus_manifest=[], grid_version=1,
+    )
+    assert spec["structure_context"] == {"kind": "none"}
+
+
+def test_tc7_range_wall_and_capitulation_are_frozen_but_never_screened(tmp_path):
+    """TC-7: range-wall-failed-aggression and capitulation-exhaustion exist in the frozen grid but
+    are NOT passed through ``register_and_screen_candidate`` this iteration -- no partial ledger
+    row for either. This test proves the negative directly: an empty scout ledger stays empty
+    after only INSPECTING the frozen grid (never calling the registration entry point for those
+    two study ids)."""
+    store = _combined_fixture_store(tmp_path)
+    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
+    grid = scout.pilot_study_candidate_grid(store)
+
+    # Inspecting the frozen requests never writes anything.
+    assert grid[scout.PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION]
+    assert grid[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION]
+    assert ledger.all_rows() == []
+
+
+# === TC-5/TC-6 (goal-rapid-microscope-iter-21, J-09): the delta-divergence candidate, screened +
+# walk-forward-floor-checked end to end, on a committed hermetic hand-derived oracle fixture. ========
+
+
+class _DivergenceEmptyBarStore:
+    def __init__(self, root="/tmp/does-not-exist-scout-divergence-test"):
+        self.root = root
+
+    def list(self):
+        return [], []
+
+
+def _divergence_band_group(symbol: str, price_low: float, *, bearish: bool, t0: float) -> tuple[list, list, float]:
+    """4 touches of a ``[price_low, price_low + 0.02]`` band, then a neutral 26-trade tail so the
+    ``trades_20`` outcome horizon is measurable at every pair's own tau2.
+
+    ``bearish=True``: each touch is followed by a small BUY that sets a NEW LOCAL HIGH above the
+    band (progressively higher across the 3 pairs -- ``price_extreme`` rises pair to pair), while
+    the DOMINANT volume around each touch is a heavy SELL (``cumulative_delta`` falls pair to
+    pair) -- the textbook divergence signature (Card 9.1). ``bearish=False``: no excursion above
+    the band is ever made, so ``price_extreme`` never rises -- ``bearish_divergence`` is ``False``
+    regardless of the delta side, by the formula's own AND condition. Validated against
+    ``micro_features.divergence_at_level`` directly before being transcribed here (dev handoff)."""
+    events: list = []
+    events.append(QuoteEvent(symbol, 0.1, price_low - 0.20, price_low - 0.15, 500, 500))
+    events.append(TradeEvent(symbol, 0.1, price_low - 0.18, 5, Side.SELL))
+    t = t0
+
+    def _q(bid: float, ask: float) -> None:
+        events.append(QuoteEvent(symbol, t, bid, ask, 500, 500))
+
+    def _buy(price: float, size: int = 10) -> None:
+        _q(price - 0.02, price)
+        events.append(TradeEvent(symbol, t, price, size, Side.BUY))
+
... [diff_bound] apps/backend/tests/test_scout.py: 194 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_walkforward.py b/apps/backend/tests/test_walkforward.py
index fafec23..22d795a 100644
--- a/apps/backend/tests/test_walkforward.py
+++ b/apps/backend/tests/test_walkforward.py
@@ -1616,3 +1616,83 @@ def test_t3_a_sealed_shards_date_IS_still_seeded_when_an_unsealed_sibling_shares
     # the date IS seeded -- through the UNSEALED sibling's own contribution, not the sealed shard's
     assert {r["window"] for r in tick_rows} == {"2026-06-09"}
     assert len(tick_rows) == 1  # exactly one entry: a date is seeded once, whoever contributed it
+
+
+# === TC-6 (goal-rapid-microscope-iter-21, J-09): scout_candidate_walkforward_floor_check ============
+#
+# A DISTINCT numbering scope from this file's own earlier "TC-6" (a prior iteration's own
+# has_any_exposure_entries guard test) -- disambiguated by the docs/phases/goal-rapid-microscope-
+# iter-21.md reference in this section's own name, the same convention test_micro_join.py's own
+# module docstring already documents for cross-iteration TC collisions.
+
+
+def _observations(*, session_dates: list[str], symbol: str = "DVA", value: float = 1.0) -> list[dict]:
+    return [{"session_date": s, "symbol": symbol, "value": value} for s in session_dates]
+
+
+def test_iter21_tc6_a_fresh_never_initialized_registry_counts_zero_oos_sessions(tmp_path):
+    """A fresh, never-r2-initialized registry is read CONSERVATIVELY -- zero oos sessions, never
+    the opposite (module docstring: an uninitialized registry's own ``is_exposed_before`` always
+    answers ``False``, which would otherwise let an already-published legacy corpus masquerade as
+    fresh out-of-sample evidence)."""
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    observations = _observations(session_dates=[f"2026-06-{d:02d}" for d in range(1, 10)])
+
+    result = wf.scout_candidate_walkforward_floor_check(
+        registry, corpus_id="a-never-seen-corpus", observations=observations,
+        registered_at="2026-08-20T00:00:00.000000Z",
+    )
+
+    assert result["status"] == "insufficient_n"
+    assert result["oos_session_count"] == 0
+    assert result["required_sessions"] == wf.WF_TRAIN_MIN_SESSIONS + wf.WF_TEST_MIN_SESSIONS
+    assert "oos_sessions" in result["missing"]
+    assert "WF_TRAIN_MIN_SESSIONS" in result["missing"]["oos_sessions"]
+
+
+def test_iter21_tc6_a_session_exposed_before_registered_at_is_excluded_from_the_oos_count(tmp_path):
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    registry.log_exposure(
+        corpus_id="c1", window="2026-06-01", surface="test", logged_at="2026-08-01T00:00:00.000000Z"
+    )
+    observations = _observations(session_dates=["2026-06-01", "2026-06-02"])
+
+    result = wf.scout_candidate_walkforward_floor_check(
+        registry, corpus_id="c1", observations=observations, registered_at="2026-08-20T00:00:00.000000Z",
+    )
+
+    assert result["oos_session_count"] == 1  # only 2026-06-02 -- 2026-06-01 was already exposed
+    assert result["status"] == "insufficient_n"  # 1 session is still far below the floor
+
+
+def test_iter21_tc6_enough_never_exposed_sessions_and_observations_clears_the_floor(tmp_path):
+    """The floor CAN clear -- proves this is a genuine floor, not a function that always refuses
+    regardless of its own inputs. The registry IS r2-initialized for ``corpus_id`` (a dummy entry
+    on an UNRELATED window, so ``has_any_exposure_entries`` is true and the per-session check
+    genuinely runs) but carries no entry for any of this test's own 60 sessions -- none of them
+    was ever exposed."""
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    registry.log_exposure(
+        corpus_id="c2", window="1999-01-01", surface="test", logged_at="2020-01-01T00:00:00.000000Z"
+    )
+    session_dates = [f"2026-{m:02d}-{d:02d}" for m in range(1, 7) for d in range(1, 11)]  # 60 dates
+    observations = []
+    for i, session_date in enumerate(session_dates):
+        symbol = "DVA" if i % 2 == 0 else "DVB"  # WF_FOLD_MIN_SYMBOLS(2) needs >= 2 symbols
+        observations.append({"session_date": session_date, "symbol": symbol, "value": float(i)})
+
+    result = wf.scout_candidate_walkforward_floor_check(
+        registry, corpus_id="c2", observations=observations, registered_at="2026-08-20T00:00:00.000000Z",
+    )
+
+    assert result["status"] == "sufficient"
+    assert result["missing"] == {}
+    assert result["oos_session_count"] == len(session_dates)
+
+
+def test_iter21_tc6_never_calls_the_fold_evaluation_function():
+    """A source-level guard (the ``test_the_banned_plain_shuffle_null_is_never_imported_or_called_
+    by_a_production_path`` precedent, ``test_scout.py``)."""
+    import inspect
+
+    assert "evaluate_mode_b_fold" not in inspect.getsource(wf.scout_candidate_walkforward_floor_check)
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 7e077ef..d076ca9 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -6011,6 +6011,20 @@ function MicroReadinessSection({
                   {readiness.joinable_corpus.withheld_excluded}
                 </td>
               </tr>
+              {/* J-09: the real materialized int (or the honest not_enumerated state) -- never a
+                  bare number a reader could mistake for a real zero (micro_join.py's own typed
+                  band_touch_count contract, served verbatim). */}
+              <tr>
+                <td className="px-1.5 py-1 text-slate-500">Joinable corpus — band touches</td>
+                <td
+                  data-testid="micro-readiness-band-touch-count"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.joinable_corpus.band_touch_count.status === "enumerated"
+                    ? readiness.joinable_corpus.band_touch_count.count
+                    : "not enumerated"}
+                </td>
+              </tr>
             </tbody>
           </table>
         </div>
@@ -6319,6 +6333,15 @@ function ScoutLedgerSection({
                           </td>
                           <td className="px-1.5 py-1 text-slate-300">
                             {trial.feature?.name ?? "—"} / {trial.feature?.transform ?? "—"}
+                            {/* J-09: structure_context.kind rendered generically -- "none" (the
+                                shipped J-04 default grid) shows nothing extra, byte-identical to
+                                before this iteration; "band_touch"/"playbook_signal" candidates
+                                (this iteration's new anchor-extraction paths) show their kind
+                                inline, inside the EXISTING Feature cell -- no new column/heading
+                                (T-11). */}
+                            {trial.structure_context?.kind && trial.structure_context.kind !== "none" ? (
+                              <span className="ml-1 text-slate-500">({trial.structure_context.kind})</span>
+                            ) : null}
                           </td>
                           <td className="px-1.5 py-1 text-slate-400">{trial.outcome?.horizon_key ?? "—"}</td>
                           <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index c5866f9..a78a57d 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2516,7 +2516,10 @@ export interface MicroReadinessStudyFloor {
 // its own return statement) -- were fetched but silently dropped by this interface until now. Only
 // `joinable_corpus.withheld_excluded` and every `sealed_tranche` field are rendered this iteration
 // (aggregate-only, spec section 7.5); `total`/`playbook_signal_count`/`band_touch_count`/
-// `by_setup_id`/`playbook_integrity_errors` stay typed/fetched but UNRENDERED (a future J-09 home).
+// `by_setup_id`/`playbook_integrity_errors` stay typed/fetched but UNRENDERED.
+// goal-rapid-microscope-iter-21 (J-09): `band_touch_count` is now rendered too (the "future J-09
+// home" this comment used to name) -- the real materialized int, or the honest typed
+// `not_enumerated` state, never a bare number a reader could mistake for a real zero.
 export interface MicroReadinessJoinableCorpus {
   total: number;
   playbook_signal_count: number;
@@ -2566,7 +2569,10 @@ export interface ScoutTrialRow {
   candidate_id: string;
   spec_hash: string;
   feature: { name: string; transform: string; params: Record<string, unknown> };
-  structure_context: { kind: string };
+  // J-09: `setup_id` is additive and OPTIONAL -- present only on a "playbook_signal"-kind
+  // candidate whose frozen spec names one verbatim (e.g. Study 3's "capitulation"); absent
+  // everywhere else, byte-identical to the pre-J-09 `{ kind: string }` shape.
+  structure_context: { kind: string; setup_id?: string };
   outcome: { horizon_key: string; sidedness: string | null };
   fitting_rule: string | null;
   econ_floor: Record<string, unknown>;
```

## Excluded-path stat (dependency/lockfile visibility)

 .../journey-scripts/J-10.json                            | 16 +++++++++-------
 runs/goal-session-rapid-microscope/telemetry.jsonl       |  7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl     |  2 ++
 3 files changed, 18 insertions(+), 7 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
