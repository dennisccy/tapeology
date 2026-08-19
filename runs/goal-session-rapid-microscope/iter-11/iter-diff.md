# Iteration diff (bounded)

Files changed: 11. Shown in full: 11.

```diff
diff --git a/apps/backend/app/research/micro_readiness.py b/apps/backend/app/research/micro_readiness.py
index 0e1a549..24f6956 100644
--- a/apps/backend/app/research/micro_readiness.py
+++ b/apps/backend/app/research/micro_readiness.py
@@ -303,19 +303,29 @@ def build_readiness(
     ``joinable_corpus`` zero rather than an error, since "no playbook evidence was even checked"
     is a true statement in that case, never a fabricated one.
 
-    **Sealed-tranche AGGREGATES only (iter-9, spec section 7.5 point 4, r3).** A dataset whose
-    Validation-Vault shard has not yet reached ``exposed`` gets NO per-shard row and NO per-shard
-    ``exposure_state`` here -- its row would carry the symbol, session date and exact trade/quote
-    counts section 7.5 withholds, and the iter-9 audit's finding B1 demonstrated this table doing
-    exactly that. Such a shard is counted instead in ``sealed_tranche`` (shard count, distinct
+    **Sealed-tranche AGGREGATES only (iter-9, spec section 7.5 point 4, r3; widened iteration 11,
+    point 7, r5).** A dataset that is part of an UNRESOLVED registered-universe pool gets NO
+    per-shard row and NO per-shard ``exposure_state`` here -- its row would carry the symbol,
+    session date and exact trade/quote counts section 7.5 withholds, and the iter-9 audit's
+    finding B1 demonstrated this table doing exactly that for a ledger-tracked sealed shard.
+    Iteration 11 widens WHICH datasets that covers: membership is no longer only "carries an
+    explicit vault shard-ledger row" but "is caught by ``vault.
+    unresolved_pool_universe_by_dataset_id``" (that function's own docstring has the full
+    reasoning) -- because a repo-wide grep at authoring finds zero production call sites of
+    ``seal_shard``, so a real recording finalized under a registered universe would otherwise
+    carry NO ledger row at all and be fully identifiable here, the exact leak point 7 exists to
+    close. Such a shard is counted instead in ``sealed_tranche`` (shard count, distinct
     symbol-days, per-universe totals -- section 7.5's own enumerated aggregate list) and is
-    excluded from ``totals``/``study_floors``, since sealed evidence is by construction not
-    available to any study. The exclusion also means this fold never LOADS a sealed shard's
-    events, so the ``fallback_frac`` walk below can never become an exploratory read of sealed
-    tape (the era's *(critical)* anti-goal). The vault is read through the SAME
-    ``vault.shard_ledger_for_dataset_dir(dataset_dir)`` resolution every other consumer uses --
-    one vault location, never a second. With nothing sealed, ``sealed_tranche`` is an all-zero
-    row and every other value in this payload is byte-identical to its pre-iter-9 self.
+    excluded from ``totals``/``study_floors``, since withheld evidence is by construction not
+    available to any study. The exclusion also means this fold never LOADS a withheld shard's
+    events, so the ``fallback_frac`` walk below can never become an exploratory read of withheld
+    tape (the era's *(critical)* anti-goal) -- the withhold check still runs BEFORE
+    ``store.load_events`` below, exactly as before (TC-10). The vault is read through the SAME
+    ``vault.shard_ledger_for_dataset_dir(dataset_dir)``/``vault.universe_ledger_for_dataset_dir(
+    dataset_dir)`` resolution every other consumer uses -- one vault location, never a second.
+    With nothing sealed and no universe registered, ``sealed_tranche`` is an all-zero row and
+    every other value in this payload is byte-identical to its pre-iter-9 self (proven inert
+    against the real corpus, which has zero registered universes today).
 
     Membership is the VAULT's answer, never re-derived here; the arithmetic over it is this
     module's own, exactly as it already is for ``totals`` (the ``joinable_corpus`` precedent, where
@@ -325,8 +335,28 @@ def build_readiness(
     what evidence exists on this disk."""
     records, errors = store.list()
     root = Path(dataset_dir)
-    withheld_universe_by_id = vault.withheld_universe_by_dataset_id(
-        vault.shard_ledger_for_dataset_dir(dataset_dir)
+    # Pure metadata arithmetic (no event replay -- `window_start_utc` is already-verified
+    # manifest data from `store.list()` above): computed for EVERY record, including ones that
+    # turn out withheld, because the iteration-11 pool predicate needs each record's own
+    # (symbol, session_date, created_utc) to test against a registered universe's rule (spec
+    # section 7.5 point 7, r5). This does not touch `store.load_events` -- the load-order guard
+    # (TC-10) is about EVENT reads, which stay confined to the kept branch below exactly as
+    # before.
+    start_et_by_id: dict[str, datetime] = {
+        meta["id"]: _et_datetime(meta["window_start_utc"]) for meta in records
+    }
+    withheld_universe_by_id = vault.unresolved_pool_universe_by_dataset_id(
+        vault.shard_ledger_for_dataset_dir(dataset_dir),
+        vault.universe_ledger_for_dataset_dir(dataset_dir),
+        [
+            (
+                meta["id"],
+                meta["symbol"],
+                start_et_by_id[meta["id"]].date().isoformat(),
+                meta.get("created_utc", ""),
+            )
+            for meta in records
+        ],
     )
 
     shards: list[dict] = []
@@ -340,11 +370,11 @@ def build_readiness(
 
     for meta in records:
         if meta["id"] in withheld_universe_by_id:
-            # Section 7.5 point 4: aggregates only. Computed from the store's own metadata
+            # Section 7.5 point 4/7: aggregates only. Computed from the store's own metadata
             # SERVER-side and never served per shard -- the payload below carries counts, never a
             # symbol, a date, or an id.
             universe_id = withheld_universe_by_id[meta["id"]]
-            symbol_day = (meta["symbol"], _et_datetime(meta["window_start_utc"]).date().isoformat())
+            symbol_day = (meta["symbol"], start_et_by_id[meta["id"]].date().isoformat())
             sealed_shard_count += 1
             sealed_symbol_days.add(symbol_day)
             sealed_shard_count_by_universe[universe_id] = (
@@ -353,7 +383,7 @@ def build_readiness(
             sealed_symbol_days_by_universe.setdefault(universe_id, set()).add(symbol_day)
             continue
 
-        start_et = _et_datetime(meta["window_start_utc"])
+        start_et = start_et_by_id[meta["id"]]
         end_et = _et_datetime(meta["window_end_utc"])
         session_date = start_et.date()
         session_date_str = session_date.isoformat()
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 1f07a4c..459d527 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -483,7 +483,18 @@ def get_tick_recorder_compute(
     manager: TickRecorderComputeManager = Depends(get_tick_recorder_compute_manager),
 ) -> dict:
     """The current (or last-terminal) recording job's progress -- never 404 (the idle default
-    before any job has ever run this process)."""
+    before any job has ever run this process).
+
+    Aggregate-only, at every point during a run (spec section 7.1, r5, era iteration 11):
+    ``progress`` never carries a symbol, a date, a dataset id, or any other per-chunk field --
+    ``chunks_total``/``chunks_done``/``chunks_fetched``/``chunks_reused``/``chunks_unchanged``/
+    ``chunks_failed``/``trades_total``/``quotes_total``/``percent_complete``/``elapsed_seconds``
+    only. ``manager.snapshot()`` already projects it that way
+    (``tick_recorder._copy_recorder_snapshot``/``_progress_view``, an explicit whitelist), so this
+    route forwards it VERBATIM -- no second computation, and deliberately no operator-only bypass
+    parameter, header, or role claim on this route (r5: using one would itself be a human exposure
+    event that destroys the tranche's blindness). TR-2's widened inference trap
+    (``test_vault.py``) sweeps this exact path."""
     snap = manager.snapshot()
     return {
         "state": snap["state"],
diff --git a/apps/backend/app/research/micro_snapshots.py b/apps/backend/app/research/micro_snapshots.py
index f5de227..9917562 100644
--- a/apps/backend/app/research/micro_snapshots.py
+++ b/apps/backend/app/research/micro_snapshots.py
@@ -34,6 +34,7 @@ import uuid
 from datetime import datetime, timezone
 from pathlib import Path
 from typing import Callable
+from zoneinfo import ZoneInfo
 
 from ..config import CONFIG, Config
 from . import micro_features as mf
@@ -86,6 +87,27 @@ class MicroSnapshotIntegrityError(Exception):
     own one-exception-class-per-module-domain convention)."""
 
 
+# This module's own private ZoneInfo constant -- the micro_readiness.py/referee_evidence.py
+# per-module idiom (mirrored, not imported: "each module that needs ET wall-clock resolution owns
+# a private ZoneInfo constant"). Needed only so ``_pool_records`` below can test a record's own
+# (symbol, session_date) against a registered vault universe's ``date_rule`` (spec section 7.5
+# point 7, r5, iteration 11) -- generic ET arithmetic, not a research value, so duplicating it
+# module-locally carries no single-source-of-truth risk (a session date is a stdlib timezone
+# conversion, never a value this module could compute differently from any other).
+_ET_ZONE = ZoneInfo("America/New_York")
+
+
+def _et_session_date(window_start_utc: str) -> str:
+    """A stored UTC ISO ``window_start_utc``, converted to its ET calendar date -- the SAME
+    conversion ``micro_readiness._et_datetime`` performs, needed here only so
+    ``vault.unresolved_pool_dataset_ids`` can test a record's ``(symbol, session_date)`` against a
+    registered universe's ``date_rule``."""
+    parsed = datetime.fromisoformat(window_start_utc.replace("Z", "+00:00"))
+    if parsed.tzinfo is None:
+        parsed = parsed.replace(tzinfo=timezone.utc)
+    return parsed.astimezone(_ET_ZONE).date().isoformat()
+
+
 def resolve_micro_snapshots_dir(dataset_dir_resolved: str) -> str:
     """``TAPEOLOGY_MICRO_SNAPSHOTS_DIR`` if set, else a ``micro_snapshots`` SIBLING of the
     caller's already-resolved dataset directory -- the ``resolve_desk_playbook_dir`` pattern,
@@ -96,23 +118,53 @@ def resolve_micro_snapshots_dir(dataset_dir_resolved: str) -> str:
     return str(Path(dataset_dir_resolved).parent / "micro_snapshots")
 
 
-def withheld_dataset_ids_for_store(dataset_store: DatasetStore) -> frozenset[str]:
-    """Every dataset id whose Validation-Vault shard has not yet reached ``exposed`` (spec
-    section 7.5 point 3, r3), resolved through the ONE
-    ``vault.shard_ledger_for_dataset_dir`` resolver every other vault consumer shares --
-    keyed on THIS store's own directory, never ``CONFIG``'s, so a ``tmp_path``-scoped caller
-    never reads the operator's real vault.
+def _pool_records(records: list[dict]) -> list[tuple[str, str, str, str]]:
+    """Every record's own ``(dataset_id, symbol, session_date, created_utc)`` -- the shape
+    ``vault.unresolved_pool_dataset_ids`` needs to test a dataset against a registered universe's
+    rule (spec section 7.5 point 7, r5, iteration 11). Pure metadata arithmetic over
+    already-loaded ``DatasetStore.list()`` records (``window_start_utc``/``created_utc``, both
+    already-verified manifest fields) -- no event read, so this can never become an exploratory
+    read of a withheld shard's tape."""
+    return [
+        (meta["id"], meta["symbol"], _et_session_date(meta["window_start_utc"]), meta.get("created_utc", ""))
+        for meta in records
+    ]
+
+
+def _unresolved_pool_ids(dataset_store: DatasetStore, records: list[dict]) -> frozenset[str]:
+    """The ONE choke point ``withheld_dataset_ids_for_store``/``exclude_withheld`` below share --
+    resolves both vault ledgers off THIS store's own directory (never ``CONFIG``'s, so a
+    ``tmp_path``-scoped caller never reads the operator's real vault) and delegates the actual
+    withhold DECISION entirely to ``vault.unresolved_pool_dataset_ids`` (never a second, locally
+    reimplemented predicate)."""
+    root_dir = str(dataset_store.root)
+    return vault.unresolved_pool_dataset_ids(
+        vault.shard_ledger_for_dataset_dir(root_dir),
+        vault.universe_ledger_for_dataset_dir(root_dir),
+        _pool_records(records),
+    )
+
 
-    Snapshot building is where a sealed shard's raw EVENTS would be replayed, and the snapshot
+def withheld_dataset_ids_for_store(dataset_store: DatasetStore) -> frozenset[str]:
+    """Every dataset id that is part of an unresolved registered-universe pool -- spec section 7.5
+    point 3 (r3, the ledger-tracked case) and point 7 (r5, iteration 11: the universe-RULE-tracked
+    case too -- see ``vault.unresolved_pool_universe_by_dataset_id``'s own docstring for why the
+    latter is needed at all). Resolved through the SAME ``vault.shard_ledger_for_dataset_dir``/
+    ``vault.universe_ledger_for_dataset_dir`` resolvers every other vault consumer shares -- keyed
+    on THIS store's own directory, never ``CONFIG``'s, so a ``tmp_path``-scoped caller never reads
+    the operator's real vault.
+
+    Snapshot building is where a withheld shard's raw EVENTS would be replayed, and the snapshot
     listing is where its ``dataset_id``/raw ``dataset_checksum``/``row_count``/``bytes_on_disk``
     would be re-published -- exactly the identity, exact counts and bytes section 7.5 withholds
-    until exposure. Both are closed against this set (iter-9 audit finding B1): the era's
-    *(critical)* anti-goal is that a sealed shard's event data and outcome aggregates are
-    "refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure", and a
-    screening/feature pass over sealed tape would destroy the held-out property the vault exists
-    to create. Empty -- and therefore byte-identical to the pre-iter-9 behaviour -- until the
-    first shard is ever sealed."""
-    return vault.withheld_dataset_ids(vault.shard_ledger_for_dataset_dir(str(dataset_store.root)))
+    until exposure. Both are closed against this set (iter-9 audit finding B1, widened iteration
+    11): the era's *(critical)* anti-goal is that a withheld shard's event data and outcome
+    aggregates are "refused everywhere (routes, MCP, accessor, readiness) until its recorded
+    exposure", and a screening/feature pass over withheld tape would destroy the held-out property
+    the vault exists to create. Empty -- and therefore byte-identical to the pre-iter-9 behaviour
+    -- until the first shard is ever sealed OR the first universe is ever registered."""
+    records, _errors = dataset_store.list()
+    return _unresolved_pool_ids(dataset_store, records)
 
 
 def exclude_withheld(records: list[dict], dataset_store: DatasetStore) -> tuple[list[dict], int]:
@@ -123,15 +175,21 @@ def exclude_withheld(records: list[dict], dataset_store: DatasetStore) -> tuple[
     Owner ruling r4, stated as code: "a refusal wired only into a route is bypassed by any module
     that enumerates the store itself", so every enumerator filters at its single
     ``DatasetStore.list()`` choke point -- through THIS function, never a second predicate of its
-    own (a divergent copy is exactly how the iter-9 audit's B2 leak survived the route-level fix).
-    The count travels into the caller's report body and into any append-only row the run writes:
-    **silent exclusion is forbidden** -- these call sites already hold that "a partial report is a
-    misleading report", and the era's denominator rail forbids a corpus that shrinks without
-    saying so.
-
-    Zero-cost and byte-identical while nothing is sealed: an empty vault withholds nothing, so
-    ``kept is`` every record and the disclosed count is ``0``."""
-    withheld = withheld_dataset_ids_for_store(dataset_store)
+    own (a divergent copy is exactly how the iter-9 audit's B2 leak survived the route-level fix,
+    and exactly the class of leak iteration 11 closes again for a dataset a real recorder
+    finalizes with no vault ledger row at all -- see ``vault.unresolved_pool_universe_by_dataset_
+    id``). The count travels into the caller's report body and into any append-only row the run
+    writes: **silent exclusion is forbidden** -- these call sites already hold that "a partial
+    report is a misleading report", and the era's denominator rail forbids a corpus that shrinks
+    without saying so.
+
+    ``records`` is used AS GIVEN, never re-listed -- every existing call site already passes
+    exactly ``dataset_store.list()``'s own record list, so re-listing here would be a redundant,
+    potentially inconsistent second enumeration of the same store.
+
+    Zero-cost and byte-identical while nothing is sealed and no universe is registered: neither
+    predicate withholds anything, so ``kept is`` every record and the disclosed count is ``0``."""
+    withheld = _unresolved_pool_ids(dataset_store, records)
     kept = [record for record in records if record["id"] not in withheld]
     return kept, len(records) - len(kept)
 
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 031dd20..4a07370 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -79,6 +79,7 @@ from .strategies import strategies_projection
 from .feed_basis import data_feed_for_scenario
 from .store import JournalStore
 from .taxonomy import taxonomy_payload
+from . import micro_snapshots
 from . import vault
 
 router = APIRouter(prefix="/research", tags=["research"])
@@ -391,18 +392,30 @@ def record_dataset(
     return {"dataset": meta}
 
 
-def get_withheld_dataset_ids() -> frozenset[str]:
-    """The dataset ids whose Validation-Vault shard has not yet reached ``exposed``
-    (``vault.withheld_dataset_ids`` — spec §7.5 point 3, r3). A FastAPI dependency resolved through
-    the SAME `TAPEOLOGY_MICRO_VAULT_DIR`-or-sibling-of-the-dataset-dir path every other vault
-    consumer uses (`vault.shard_ledger_for_dataset_dir`), so there is exactly one answer to "which
-    shards are sealed" in the process, and tests can override it outright.
+def get_withheld_dataset_ids(store: DatasetStore = Depends(get_dataset_store)) -> frozenset[str]:
+    """Every dataset id that is part of an unresolved registered-universe pool — spec §7.5 point 3
+    (r3, the ledger-tracked case) and point 7 (r5, era iteration 11: the universe-RULE-tracked
+    case too — see ``vault.unresolved_pool_universe_by_dataset_id``'s own docstring for the full
+    reasoning). Delegated entirely to ``micro_snapshots.withheld_dataset_ids_for_store`` — THE one
+    choke point every other corpus-wide consumer already shares — never a second, locally
+    reimplemented predicate for this listing/detail/backtest-creation surface specifically.
+
+    **Iteration 11 closes a real gap here, not a hypothetical one.** This is the era's own
+    ``GET /research/datasets`` — the SAME surface docs/phases/goal-rapid-microscope-iter-11.md's
+    own BACKGROUND section names explicitly: "The instant a real recording under a registered
+    universe finalizes a dataset, it becomes fully identifiable in `GET /research/datasets` and
+    in readiness's `shards` list". Before this iteration, this dependency called
+    ``vault.withheld_dataset_ids`` directly (the ledger-row-only predicate) — a real recording
+    finalized under a registered universe but never explicitly sealed would have been fully
+    identifiable right here, on the single most public dataset-listing surface in the product.
+
+    A FastAPI dependency (resolved through the SAME ``get_dataset_store`` dependency
+    ``list_datasets``/``get_dataset`` themselves already use, so there is exactly one store
+    resolution path) so tests can override it outright.
 
     Empty — and therefore a provable no-op for every existing behaviour — until the first shard is
-    ever sealed."""
-    return vault.withheld_dataset_ids(
-        vault.shard_ledger_for_dataset_dir(CONFIG.dataset_dir_resolved())
-    )
+    ever sealed OR the first universe is ever registered."""
+    return micro_snapshots.withheld_dataset_ids_for_store(store)
 
 
 @router.get("/datasets")
diff --git a/apps/backend/app/research/tick_recorder.py b/apps/backend/app/research/tick_recorder.py
index 912d34a..d960f5f 100644
--- a/apps/backend/app/research/tick_recorder.py
+++ b/apps/backend/app/research/tick_recorder.py
@@ -489,8 +489,20 @@ def _finalize_day(
     return meta["id"], "recorded"
 
 
-def _chunk_entry(chunk: dict, outcome: str, detail: str | None = None) -> dict:
-    return {**chunk, "outcome": outcome, "detail": detail, "dataset_id": None, "dataset_outcome": None}
+def _chunk_entry(
+    chunk: dict, outcome: str, detail: str | None = None, *, trade_count: int = 0, quote_count: int = 0,
+) -> dict:
+    """``trade_count``/``quote_count`` (era iteration 11, spec section 7.1) are populated ONLY at
+    the "fetched" call site below, from that chunk's own freshly-fetched ``HistoricalWindow`` --
+    read by the manager's ``_publish`` ONLY to increment its running ``trades_total``/
+    ``quotes_total`` aggregate. This entry itself (``run_tick_recording``'s own return value) is
+    never served verbatim by any route -- the manager's own live progress view
+    (``_progress_view``) is an explicit whitelist that never includes a per-chunk field, this one
+    included."""
+    return {
+        **chunk, "outcome": outcome, "detail": detail, "dataset_id": None, "dataset_outcome": None,
+        "trade_count": trade_count, "quote_count": quote_count,
+    }
 
 
 def run_tick_recording(
@@ -556,7 +568,9 @@ def run_tick_recording(
                     continue
                 checkpoint_store.put(chunk["symbol"], chunk["date"], chunk["start"], chunk["end"], fetched)
                 day_windows.append(fetched)
-                entry = _chunk_entry(chunk, "fetched")
+                entry = _chunk_entry(
+                    chunk, "fetched", trade_count=len(fetched.trades), quote_count=len(fetched.quotes)
+                )
             outcomes.append(entry)
             if progress is not None:
                 progress(entry)
@@ -606,19 +620,87 @@ def _iso_utc_now() -> str:
     return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
 
 
+# The manager's INTERNAL per-run progress baseline. `outcomes` (each entry's own symbol/date/
+# start/end -- see `_chunk_entry`) is kept SOLELY so `_resolve_terminal`'s pre-existing exception-
+# fallback path (a failure OUTSIDE any single chunk, e.g. TR-19, firing before `run_tick_recording`
+# ever returns its own list) can still build an accurate terminal run-log row from whatever this
+# process itself already saw -- it is NEVER served: `_progress_view` below is an EXPLICIT
+# whitelist (the `vault._serialize_shard` discipline, mirrored) that never spreads `progress`
+# itself into a response, so this internal field can never leak by accident. `trades_total`/
+# `quotes_total` are genuine RUNNING TOTALS (era iteration 11, spec section 7.1) accumulated
+# incrementally by `_publish` below -- never derived from a per-chunk count stored anywhere.
+_IDLE_PROGRESS: dict = {
+    "chunks_total": 0, "chunks_done": 0, "outcomes": [], "trades_total": 0, "quotes_total": 0,
+}
+
 _IDLE_RECORDER_SNAPSHOT: dict = {
     "run_id": None,
     "state": "idle",
-    "progress": {"chunks_total": 0, "chunks_done": 0, "outcomes": []},
+    "progress": dict(_IDLE_PROGRESS),
     "started_utc": None,
     "finished_utc": None,
     "error": None,
 }
 
 
+def _outcome_type_counts(tick_outcomes: list[dict]) -> dict:
+    """The four per-outcome-type counts (spec section 7.1) -- ONE counting implementation, shared
+    by ``_run_log_entry`` (the terminal run-log row, byte-unchanged below) and the live
+    aggregate-only progress projection (``_progress_view`` below, era iteration 11), so the two
+    surfaces can never disagree about how many chunks fetched/reused/were-unchanged/failed."""
+    return {
+        "chunks_fetched": sum(1 for o in tick_outcomes if o["outcome"] == "fetched"),
+        "chunks_reused": sum(1 for o in tick_outcomes if o["outcome"] == "reused"),
+        "chunks_unchanged": sum(1 for o in tick_outcomes if o["outcome"] == "unchanged"),
+        "chunks_failed": sum(1 for o in tick_outcomes if o["outcome"] == "failed"),
+    }
+
+
+def _elapsed_seconds(started_utc: str, end_utc: str) -> float:
+    start = datetime.fromisoformat(started_utc.replace("Z", "+00:00"))
+    end = datetime.fromisoformat(end_utc.replace("Z", "+00:00"))
+    return (end - start).total_seconds()
+
+
+def _progress_view(progress: dict, *, started_utc: str | None, finished_utc: str | None) -> dict:
+    """The aggregate-only PUBLIC projection of the manager's internal progress state (spec section
+    7.1, r5 -- era iteration 11: "GET /research/desk/micro/recorder/compute ... serves only
+    non-identifying aggregates ... MUST NOT serve symbol, date, dataset id, shard id, per-shard
+    byte or event counts, or any other per-chunk identity-bearing metadata"). An EXPLICIT
+    whitelist naming every field it serves, never ``dict(progress)``/``{**progress, ...}`` (the
+    ``vault._serialize_shard`` discipline, mirrored) -- ``progress`` still carries an internal
+    ``outcomes`` list (see ``_IDLE_PROGRESS``'s own docstring), so a blind spread would re-leak it.
+    ``percent_complete``/``elapsed_seconds`` are DERIVED here, never stored on ``progress`` itself,
+    since ``elapsed_seconds`` must reflect "now" for a still-running job."""
+    chunks_total = progress["chunks_total"]
+    chunks_done = progress["chunks_done"]
+    percent_complete = (chunks_done / chunks_total * 100.0) if chunks_total > 0 else 0.0
+    if started_utc is None:
+        elapsed_seconds = 0.0
+    else:
+        elapsed_seconds = _elapsed_seconds(started_utc, finished_utc or _iso_utc_now())
+    return {
+        "chunks_total": chunks_total,
+        "chunks_done": chunks_done,
+        **_outcome_type_counts(progress["outcomes"]),
+        "trades_total": progress["trades_total"],
+        "quotes_total": progress["quotes_total"],
+        "percent_complete": percent_complete,
+        "elapsed_seconds": elapsed_seconds,
+    }
+
+
 def _copy_recorder_snapshot(snapshot: dict) -> dict:
-    progress = snapshot["progress"]
-    return {**snapshot, "progress": {**progress, "outcomes": [dict(o) for o in progress["outcomes"]]}}
+    """The manager's PUBLIC projection -- used by BOTH ``snapshot()`` (``GET .../recorder/compute``)
+    and ``trigger()``'s own immediate return (``POST .../recorder/compute``), so neither surface can
+    diverge from the other. See ``_progress_view``'s own docstring for why this is an explicit
+    whitelist rather than a spread."""
+    return {
+        **snapshot,
+        "progress": _progress_view(
+            snapshot["progress"], started_utc=snapshot["started_utc"], finished_utc=snapshot["finished_utc"]
+        ),
+    }
 
 
 def _run_log_entry(
@@ -627,7 +709,10 @@ def _run_log_entry(
 ) -> dict:
     """THE single shared run-log-entry builder -- called by BOTH the manager's worker resolve path
     and the CLI's ``main()`` (the ``record_deep_backfill_run`` "one shared writer" precedent),
-    so a run's summary counts can never disagree between the two entry points."""
+    so a run's summary counts can never disagree between the two entry points. Byte-identical
+    output to before iteration 11's ``_outcome_type_counts`` extraction -- this route (``GET
+    .../recorder/runs``) is already aggregate-only and its shape is out of this iteration's
+    scope."""
     return {
         "run_id": run_id,
         "state": state,
@@ -635,10 +720,7 @@ def _run_log_entry(
         "finished_utc": finished_utc,
         "chunks_total": chunks_total,
         "chunks_done": len(tick_outcomes),
-        "chunks_fetched": sum(1 for o in tick_outcomes if o["outcome"] == "fetched"),
-        "chunks_reused": sum(1 for o in tick_outcomes if o["outcome"] == "reused"),
-        "chunks_unchanged": sum(1 for o in tick_outcomes if o["outcome"] == "unchanged"),
-        "chunks_failed": sum(1 for o in tick_outcomes if o["outcome"] == "failed"),
+        **_outcome_type_counts(tick_outcomes),
         "datasets_recorded": sum(1 for o in tick_outcomes if o.get("dataset_outcome") == "recorded"),
         "bars_recorded": sum(int(o.get("bars_recorded") or 0) for o in bar_outcomes),
         "error": error,
@@ -692,7 +774,7 @@ class TickRecorderComputeManager:
             self._snapshot = {
                 "run_id": run_id,
                 "state": "running",
-                "progress": {"chunks_total": len(chunks), "chunks_done": 0, "outcomes": []},
+                "progress": {**_IDLE_PROGRESS, "chunks_total": len(chunks)},
                 "started_utc": _iso_utc_now(),
                 "finished_utc": None,
                 "error": None,
@@ -704,12 +786,19 @@ class TickRecorderComputeManager:
                 if self._run_id != run_id:
                     return  # a NEWER job already replaced this one -- a stale reporter, ignored
                 current = self._snapshot
+                progress = current["progress"]
                 self._snapshot = {
                     **current,
                     "progress": {
-                        **current["progress"],
-                        "chunks_done": current["progress"]["chunks_done"] + 1,
-                        "outcomes": [*current["progress"]["outcomes"], entry],
+                        **progress,
+                        "chunks_done": progress["chunks_done"] + 1,
+                        "outcomes": [*progress["outcomes"], entry],
+                        # era iteration 11: running totals, accumulated AT FETCH TIME from each
+                        # "fetched" chunk's own HistoricalWindow (`_chunk_entry`'s own docstring)
+                        # -- a "reused"/"failed" entry's counts are 0, so this only ever grows on a
+                        # genuine new vendor pull THIS run, never on cached/checkpointed content.
+                        "trades_total": progress["trades_total"] + entry["trade_count"],
+                        "quotes_total": progress["quotes_total"] + entry["quote_count"],
                     },
                 }
 
diff --git a/apps/backend/app/research/vault.py b/apps/backend/app/research/vault.py
index 30bf52c..2b8a95b 100644
--- a/apps/backend/app/research/vault.py
+++ b/apps/backend/app/research/vault.py
@@ -105,7 +105,28 @@ it nor anything reversible to it into the row it appends. A missing or unreadabl
 **Storage -- no new ``Config`` field.** ``resolve_vault_dir`` mirrors ``scout_ledger.
 resolve_scout_ledger_dir`` exactly: ``TAPEOLOGY_MICRO_VAULT_DIR`` if set, else a ``micro_vault``
 SIBLING of the caller's own already-resolved dataset directory (the ``TAPEOLOGY_MICRO_*`` family,
-goal.md Constraints)."""
+goal.md Constraints).
+
+**Iteration 11 -- the opaque research pool, closed structurally (spec section 7.5 point 7, r5).**
+Parts 1-4 above close every JOIN a served field could open; point 7 closes something field-level
+minimization cannot reach at all: "no served surface may present a complete identity-labelled
+list of EITHER side while any pool member is unexposed", because the registered universe is
+public BY CONSTRUCTION (section 7.2), so a complete list of the non-withheld side identifies the
+withheld side by subtraction. The gap this closes is concrete, not hypothetical: a repo-wide grep
+at authoring finds ZERO production call sites of ``seal_shard``/``assign_shard``/``expose_shard``
+-- nothing today wires a real recording to this module's ledger the moment it finalizes. So the
+narrower, ledger-row-only ``withheld_universe_by_dataset_id`` above is not wrong, merely
+insufficient: the instant a real recording finalizes under a registered universe, it would be
+fully identifiable in ``GET /research/datasets`` and in ``micro_readiness``'s per-shard ``shards``
+list with zero code path standing in the way. ``unresolved_pool_universe_by_dataset_id`` below
+closes this STRUCTURALLY rather than procedurally -- a universe-RULE-driven predicate, safe the
+INSTANT ``register_universe`` runs, needing no additional recorder-to-vault wiring (see that
+function's own docstring for the full reasoning, including the ``created_utc >= registered_at``
+guard that keeps a later-registered universe from retroactively withholding a pre-existing
+dataset). It is the ONE new choke point ``micro_snapshots.exclude_withheld``/
+``withheld_dataset_ids_for_store`` (hence its 8 existing corpus-wide enumerator consumers) and
+``micro_readiness.build_readiness`` both read -- never a second, divergent implementation of "is
+this dataset withheld"."""
 
 from __future__ import annotations
 
@@ -134,6 +155,7 @@ __all__ = [
     "SealedShardWithheldError",
     "resolve_vault_dir",
     "shard_ledger_for_dataset_dir",
+    "universe_ledger_for_dataset_dir",
     "VaultUniverseLedger",
     "VaultShardLedger",
     "compute_rule_hash",
@@ -153,6 +175,8 @@ __all__ = [
     "currently_sealed_dataset_ids",
     "withheld_dataset_ids",
     "withheld_universe_by_dataset_id",
+    "unresolved_pool_universe_by_dataset_id",
+    "unresolved_pool_dataset_ids",
     "build_vault_state",
     "compute_family_root_id",
     "RULE_DISCLOSURE_COMMITTED",
@@ -319,6 +343,16 @@ def shard_ledger_for_dataset_dir(dataset_dir_resolved: str) -> "VaultShardLedger
     return VaultShardLedger(resolve_vault_dir(dataset_dir_resolved))
 
 
+def universe_ledger_for_dataset_dir(dataset_dir_resolved: str) -> "VaultUniverseLedger":
+    """The universe-registration ledger for a caller that knows only its dataset directory -- the
+    ``shard_ledger_for_dataset_dir`` pattern verbatim, for the OTHER ledger (module docstring:
+    "two separate ``HashChainedLedger`` instances"). Iteration 11's own
+    ``unresolved_pool_universe_by_dataset_id`` is the one caller that needs BOTH resolvers
+    together, so there can never be two vault locations answering "which universes are
+    registered" differently."""
+    return VaultUniverseLedger(resolve_vault_dir(dataset_dir_resolved))
+
+
 # === the two ledgers (module docstring: "once per ledger") =========================================
 
 
@@ -738,6 +772,125 @@ def withheld_dataset_ids(ledger: VaultShardLedger) -> frozenset[str]:
     return frozenset(withheld_universe_by_dataset_id(ledger))
 
 
+# === iteration 11: the opaque-pool predicate (spec section 7.5 point 7, r5) =========================
+#
+# Module docstring's own "Iteration 11" paragraph has the full motivation. Short version: the two
+# functions above answer "does this dataset already carry an explicit vault shard-ledger row short
+# of exposed" -- correct, but not the whole question, because nothing in this codebase's
+# PRODUCTION code path ever calls seal_shard/assign_shard/expose_shard today (verified by grep at
+# authoring). The functions below answer the actual question -- "is this dataset part of an
+# unresolved registered-universe pool" -- by ALSO reading the registered universe RULE itself,
+# which is safe the instant a universe is registered, independent of whether anything ever seals
+# its members explicitly.
+
+
+def _latest_universes(universe_ledger: VaultUniverseLedger) -> list[dict]:
+    """Every currently-registered universe's own latest row (``find_universe``'s "most recent row
+    per ``universe_id``" semantics, applied across EVERY ``universe_id`` at once rather than one
+    named universe) -- the one ledger scan ``_universe_pair_index`` below needs."""
+    latest: dict[str, dict] = {}
+    for row in universe_ledger.all_rows():
+        latest[row["universe_id"]] = row
+    return list(latest.values())
+
+
+def _universe_pair_index(universe_ledger: VaultUniverseLedger) -> dict[tuple[str, str], list[dict]]:
+    """Every registered universe's own ``expected_recording_pairs()``, indexed by each
+    ``(symbol, date)`` pair it covers -- built ONCE per call so a wide ``symbol_rule x date_rule``
+    product is walked once per universe, never once per caller record (``unresolved_pool_
+    universe_by_dataset_id`` below does an O(1) dict lookup per record against this index)."""
+    index: dict[tuple[str, str], list[dict]] = {}
+    for universe in _latest_universes(universe_ledger):
+        for pair in expected_recording_pairs(universe):
+            index.setdefault(pair, []).append(universe)
+    return index
+
+
+def unresolved_pool_universe_by_dataset_id(
+    shard_ledger: VaultShardLedger,
+    universe_ledger: VaultUniverseLedger,
+    records: list[tuple[str, str, str, str]],
+) -> dict[str, str]:
+    """The SINGLE shared "is this dataset part of an unresolved registered-universe pool"
+    predicate (spec section 7.5 point 7, r5 -- module docstring's "Iteration 11" paragraph has the
+    full motivation), mapped to the responsible ``universe_id``. Consumed via
+    ``micro_snapshots.exclude_withheld``/``withheld_dataset_ids_for_store`` (hence its 8 existing
+    corpus-wide enumerator consumers) and directly by ``micro_readiness.build_readiness`` -- never
+    a second, divergent implementation of "is this withheld" anywhere in this codebase.
+
+    A dataset id is caught by the UNION of two independent tests, never a tie-breaker between
+    them:
+
+    (a) today's ledger-row check (``withheld_universe_by_dataset_id`` above, byte-UNCHANGED): the
+        dataset already carries an explicit vault shard-ledger row whose latest state is short of
+        ``exposed``.
+    (b) NEW -- a universe-RULE membership check, but ONLY for a dataset that carries NO vault
+        shard-ledger row AT ALL (any state -- see the ``ledger_tracked_ids`` guard below): the
+        dataset's own ``(symbol, session_date)`` matches some registered universe's
+        ``expected_recording_pairs()``, AND the dataset's own ``created_utc`` is at or after THAT
+        universe's ``registered_at``.
+
+    **The ``ledger_tracked_ids`` guard is load-bearing, not an optimization.** A universe's rule
+    (``symbol_rule``/``date_rule``) never changes after a shard reaches ``exposed`` -- so without
+    this guard, test (b) would keep matching a shard's (symbol, session_date) FOREVER, silently
+    re-withholding a shard the operator legitimately exposed through the normal
+    ``assign_shard``/``expose_shard`` path (caught by this function's own TC-3/TC-10 tests during
+    development: an exposed shard has no row in (a)'s result set, since (a) only lists rows SHORT
+    of exposed, so a naive "not already withheld by (a)" check alone let (b) re-catch it). The
+    fix: test (b) only ever applies to a dataset the shard ledger has NEVER recorded a row for --
+    once ANY row exists (sealed, assigned, OR exposed), the ledger's own answer is authoritative
+    and test (b) never overrides it in either direction.
+
+    ``created_utc >= registered_at`` is the guard that stops a universe registered LATER from
+    retroactively withholding a dataset that already existed when it was registered -- including
+    one of the 12 permanently-exploratory legacy symbol-days that happens to share a (symbol,
+    date) with a brand-new rule (goal.md's own critical anti-goal: "The 12 pre-existing tick
+    symbol-days are permanently exploratory -- never sealed ... never relabeled"). A dataset
+    recorded before a universe existed cannot possibly be one of THAT universe's own recording
+    outputs, so it is never a candidate for (b) regardless of a coincidental (symbol, date) match.
+    Both timestamps are ``datetime.isoformat(timespec="microseconds")`` strings (``datasets.
+    _iso_utc``/this module's own ``_iso_utc_now``) -- fixed-width and lexicographically
+    comparable, so the plain string comparison is exact, never an approximation.
+
+    Store-agnostic (module docstring: this module never imports ``DatasetStore``): ``records`` is
+    the caller's own ``(dataset_id, symbol, session_date, created_utc)`` 4-tuples -- every caller
+    already walks its own store and already holds these four already-verified manifest fields per
+    record, so no event read is ever implied by calling this function.
+
+    When a dataset id is caught by BOTH tests, or matches (b) against more than one universe, the
+    returned ``universe_id`` prefers (a)'s ledger-recorded answer (the authoritative, already-
+    assigned truth) and otherwise the first (b) match found -- every caller uses this only for
+    AGGREGATE per-universe counting (``micro_readiness.py``'s ``sealed_tranche.by_universe``),
+    never as a per-shard identity, so which universe wins a rare double-match is not itself an
+    identity leak."""
+    result: dict[str, str] = dict(withheld_universe_by_dataset_id(shard_ledger))
+    pair_index = _universe_pair_index(universe_ledger)
+    if pair_index:
+        # Every dataset id the ledger has EVER recorded a row for, in ANY state -- including
+        # `exposed`, which `withheld_universe_by_dataset_id` (hence `result` above) deliberately
+        # excludes. Needed so test (b) below never re-catches a shard the operator legitimately
+        # exposed (see this function's own docstring).
+        ledger_tracked_ids = frozenset(_latest_rows_by_dataset_id(shard_ledger))
+        for dataset_id, symbol, session_date, created_utc in records:
+            if dataset_id in result or dataset_id in ledger_tracked_ids:
+                continue
+            for universe in pair_index.get((symbol, session_date), ()):
+                if created_utc >= universe["registered_at"]:
+                    result[dataset_id] = universe["universe_id"]
+                    break
+    return result
+
+
+def unresolved_pool_dataset_ids(
+    shard_ledger: VaultShardLedger,
+    universe_ledger: VaultUniverseLedger,
+    records: list[tuple[str, str, str, str]],
+) -> frozenset[str]:
+    """``unresolved_pool_universe_by_dataset_id``'s key set -- the ``withheld_dataset_ids`` shape,
+    widened to the same universe-rule membership test (spec section 7.5 point 7, r5)."""
+    return frozenset(unresolved_pool_universe_by_dataset_id(shard_ledger, universe_ledger, records))
+
+
 # === GET /research/desk/micro/vault (served verbatim, no second computation in the route) ==========
 
 
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
index 246f303..237de10 100644
--- a/apps/backend/tests/test_micro_readiness.py
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -42,6 +42,7 @@ from app.research.micro_join import joinable_corpus_counts
 from app.research.micro_routes import get_micro_readiness_cache
 from app.research.referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
 from app.research.routes import get_dataset_store
+from app.research import vault
 
 _ET = ZoneInfo("America/New_York")
 
@@ -586,3 +587,201 @@ def test_tc15_real_corpus_readiness_also_serves_the_typed_band_touch_count(real_
     assert not isinstance(band_touch, int)
     assert band_touch["status"] == "not_enumerated"
     assert band_touch["count"] is None
+
+
+# === Iteration 11 (docs/phases/goal-rapid-microscope-iter-11.md, spec section 7.5 point 7, r5):
+# the opaque-pool predicate widens WHICH datasets `build_readiness` withholds -- TC-1/TC-3/TC-4/
+# TC-10. `_plant_pool_dataset` below is a DEDICATED fixture builder, never `_plant_dataset` above
+# (whose fixed `_events(symbol)` shape collides across dates for the SAME symbol on
+# `DatasetAlreadyRegistered`) -- it mirrors `test_vault.py`'s own per-(symbol, date) content-nonce
+# precedent instead.
+# =====================================================================================================
+
+_POOL_FIXTURE_SECRET = b"a-micro-readiness-fixture-vault-secret"
+
+
+def _plant_pool_dataset(store: DatasetStore, *, symbol: str, session_date: str, nonce: float) -> dict:
+    """One dataset for (symbol, session_date), content-distinct via `nonce` in its one trade's
+    price -- so multiple dates for the SAME symbol never collide on `DatasetAlreadyRegistered`."""
+    events = [
+        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
+        TradeEvent(symbol, 0.1, 100.0 + nonce, 10, Side.BUY),
+    ]
+    return store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-fixture",
+        split="train", window_start_utc=f"{session_date}T13:30:00Z",
+        window_end_utc=f"{session_date}T20:00:00Z", data_feed="sip", epoch_anchor=0.0, events=events,
+    )
+
+
+def _pool_fixture(tmp_path):
+    """Registers ONE universe U (``symbol_rule=["ZPQA", "ZPQB"]``, ``date_rule=["2026-06-01",
+    "2026-06-02"]``, 4 expected pairs) and records all 4 corresponding datasets AFTER U's
+    ``registered_at`` (real sequential execution -- register first, record after -- gives this
+    ordering for free, exactly as a real recorder run would). Returns ``(store, dataset_dir,
+    shard_ledger, universe_ledger, metas)`` where ``metas`` maps ``(symbol, date) -> meta``; NONE
+    of the 4 carries any vault shard-ledger row yet -- callers seal/assign/expose as their own
+    scenario requires."""
+    dataset_dir = tmp_path / "datasets"
+    vault_dir = tmp_path / "micro_vault"
+    store = DatasetStore(dataset_dir)
+    universe_ledger = vault.VaultUniverseLedger(str(vault_dir))
+    symbols, dates = ["ZPQA", "ZPQB"], ["2026-06-01", "2026-06-02"]
+    vault.register_universe(
+        universe_ledger, universe_id="pool-u1", symbol_rule=symbols, date_rule=dates,
+        vault_secret_commitment=vault.commit_vault_secret(_POOL_FIXTURE_SECRET),
+    )
+    metas = {}
+    for s_index, symbol in enumerate(symbols):
+        for d_index, session_date in enumerate(dates):
+            metas[(symbol, session_date)] = _plant_pool_dataset(
+                store, symbol=symbol, session_date=session_date, nonce=s_index * 10 + d_index,
+            )
+    shard_ledger = vault.VaultShardLedger(str(vault_dir))
+    return store, str(dataset_dir), shard_ledger, universe_ledger, metas
+
+
+def test_tc1_a_registered_pool_with_mixed_ledger_tracked_and_untracked_members_withholds_all_four(
+    tmp_path,
+):
+    """TC-1 (phase spec): a registered universe's 4 expected pairs, 2 carrying an explicit
+    ``sealed`` ledger row and the other 2 carrying NONE at all -- ``build_readiness`` withholds
+    ALL FOUR per-shard, and ``sealed_tranche`` reports ``shard_count: 4``. This is the exact
+    iteration-11 gap made concrete: pre-fix, the 2 untracked members would have appeared in
+    ``shards`` with full identity, since the old predicate only ever checked for a ledger row."""
+    store, dataset_dir, shard_ledger, _universe_ledger, metas = _pool_fixture(tmp_path)
+
+    # 2 of 4 members get an explicit sealed ledger row; the other 2 get NONE.
+    for pair in [("ZPQA", "2026-06-01"), ("ZPQB", "2026-06-02")]:
+        meta = metas[pair]
+        vault.seal_shard(
+            shard_ledger, dataset_id=meta["id"], universe_id="pool-u1",
+            content_checksum=meta["checksum"], event_count=meta["event_counts"]["total"],
+            vault_secret=_POOL_FIXTURE_SECRET,
+        )
+
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    result = build_readiness(store, cache, dataset_dir=dataset_dir)
+
+    assert result["shards"] == []  # none of the 4 -- ledger-tracked OR untracked -- appears
+    assert result["sealed_tranche"]["shard_count"] == 4
+    assert result["sealed_tranche"]["symbol_days"] == 4
+    assert result["sealed_tranche"]["by_universe"] == {"pool-u1": {"shard_count": 4, "symbol_days": 4}}
+    assert result["totals"]["distinct_datasets"] == 0
+
+
+def test_tc3_exposing_one_pool_member_reveals_only_that_one_row(tmp_path):
+    """TC-3 (phase spec): one pool member is assigned + exposed via the EXISTING family-bound
+    path; the remaining 3 unresolved pairs still contribute zero per-shard rows and only the
+    aggregate count, now ``shard_count: 3``."""
+    store, dataset_dir, shard_ledger, _universe_ledger, metas = _pool_fixture(tmp_path)
+    exposed_pair = ("ZPQA", "2026-06-01")
+    exposed_meta = metas[exposed_pair]
+    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+    vault.seal_shard(
+        shard_ledger, dataset_id=exposed_meta["id"], universe_id="pool-u1",
+        content_checksum=exposed_meta["checksum"], event_count=exposed_meta["event_counts"]["total"],
+        vault_secret=_POOL_FIXTURE_SECRET,
+    )
+    vault.assign_shard(
+        shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root,
+        symbol=exposed_pair[0], session_date=exposed_pair[1],
+    )
+    vault.expose_shard(shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root)
+
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    result = build_readiness(store, cache, dataset_dir=dataset_dir)
+
+    assert [s["dataset_id"] for s in result["shards"]] == [exposed_meta["id"]]
+    assert result["shards"][0]["symbol"] == exposed_pair[0]
+    assert result["shards"][0]["session_date"] == exposed_pair[1]
+    assert result["sealed_tranche"]["shard_count"] == 3
+    assert result["sealed_tranche"]["by_universe"] == {"pool-u1": {"shard_count": 3, "symbol_days": 3}}
+
+
+def test_tc4_a_dataset_recorded_before_a_later_universes_registration_is_never_withheld(tmp_path):
+    """TC-4 (phase spec): a dataset recorded BEFORE a universe's registration is never
+    retroactively withheld by that universe's rule, even when it shares a (symbol, date) with it
+    -- protects the 12 permanently-exploratory legacy symbol-days from a later universe naming the
+    same panel by coincidence."""
+    dataset_dir = tmp_path / "datasets"
+    vault_dir = tmp_path / "micro_vault"
+    store = DatasetStore(dataset_dir)
+
+    # the dataset exists FIRST -- a "legacy" symbol-day, in real chronological order.
+    pre_existing = _plant_pool_dataset(store, symbol="ZPQC", session_date="2026-06-03", nonce=1.0)
+
+    # a LATER universe happens to name the exact same (symbol, date) in its rule.
+    universe_ledger = vault.VaultUniverseLedger(str(vault_dir))
+    vault.register_universe(
+        universe_ledger, universe_id="pool-u2", symbol_rule=["ZPQC"], date_rule=["2026-06-03"],
+        vault_secret_commitment=vault.commit_vault_secret(_POOL_FIXTURE_SECRET),
+    )
+
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    result = build_readiness(store, cache, dataset_dir=str(dataset_dir))
+
+    assert [s["dataset_id"] for s in result["shards"]] == [pre_existing["id"]]
+    assert result["sealed_tranche"] == {"shard_count": 0, "symbol_days": 0, "by_universe": {}}
+
+    # the vault predicate directly, at the boundary -- the same claim, as the module's own unit.
+    shard_ledger = vault.VaultShardLedger(str(vault_dir))
+    membership = vault.unresolved_pool_universe_by_dataset_id(
+        shard_ledger, universe_ledger,
+        [(pre_existing["id"], "ZPQC", "2026-06-03", pre_existing["created_utc"])],
+    )
+    assert membership == {}
+
+
+def test_tc10_the_withhold_check_never_loads_events_for_a_pool_member_before_its_exposure(
+    tmp_path, monkeypatch
+):
+    """TC-10 (phase spec): ``store.load_events`` is never called for a still-withheld shard's
+    dataset id during ``build_readiness``'s ``fallback_frac`` walk -- proven DIRECTLY via a spy,
+    never inferred from the served shape alone. Exercises BOTH withheld shapes at once (one
+    member carries an explicit ``sealed`` ledger row, two carry none at all) alongside a FOURTH,
+    genuinely exposed member -- so the spy has something legitimate to prove it still fires
+    correctly; a trap that would also pass with ``load_events`` disabled entirely proves
+    nothing."""
+    store, dataset_dir, shard_ledger, _universe_ledger, metas = _pool_fixture(tmp_path)
+
+    sealed_pair = ("ZPQA", "2026-06-01")
+    exposed_pair = ("ZPQB", "2026-06-02")
+    untracked_pairs = [("ZPQA", "2026-06-02"), ("ZPQB", "2026-06-01")]
+
+    sealed_meta = metas[sealed_pair]
+    vault.seal_shard(
+        shard_ledger, dataset_id=sealed_meta["id"], universe_id="pool-u1",
+        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=_POOL_FIXTURE_SECRET,
+    )
+    exposed_meta = metas[exposed_pair]
+    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+    vault.seal_shard(
+        shard_ledger, dataset_id=exposed_meta["id"], universe_id="pool-u1",
+        content_checksum=exposed_meta["checksum"], event_count=exposed_meta["event_counts"]["total"],
+        vault_secret=_POOL_FIXTURE_SECRET,
+    )
+    vault.assign_shard(
+        shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root,
+        symbol=exposed_pair[0], session_date=exposed_pair[1],
+    )
+    vault.expose_shard(shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root)
+
+    original_load_events = store.load_events
+    seen_ids: list[str] = []
+
+    def _spy_load_events(dataset_id):
+        seen_ids.append(dataset_id)
+        return original_load_events(dataset_id)
+
+    monkeypatch.setattr(store, "load_events", _spy_load_events)
+
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    result = build_readiness(store, cache, dataset_dir=dataset_dir)
+
+    assert [s["dataset_id"] for s in result["shards"]] == [exposed_meta["id"]]
+    assert result["sealed_tranche"]["shard_count"] == 3  # 1 sealed + 2 untracked
+    withheld_ids = {sealed_meta["id"], *(metas[p]["id"] for p in untracked_pairs)}
+    assert seen_ids == [exposed_meta["id"]]  # ONLY the exposed shard's events were ever read
+    assert not (set(seen_ids) & withheld_ids)
diff --git a/apps/backend/tests/test_tick_recorder.py b/apps/backend/tests/test_tick_recorder.py
index 9a8fcc0..6ba35db 100644
--- a/apps/backend/tests/test_tick_recorder.py
+++ b/apps/backend/tests/test_tick_recorder.py
@@ -15,11 +15,14 @@ per this iteration's own scope note). Covers, in order:
   7. The published sha256 split rule (spec section 7.3, unchanged -- NOT vault.py's new seal
      axis, which stays out of scope this iteration).
   8. Bar pairing through the EXISTING, UNCHANGED ``desk_deep_backfill`` machinery.
+  9. Era iteration 11 (spec section 7.1, r5): the LIVE recorder-progress path is aggregate-only
+     at every point during a run -- TC-6/TC-7, section 12 at the bottom of this file.
 """
 
 from __future__ import annotations
 
 import hashlib
+import json
 import threading
 import time
 from datetime import date, timezone
@@ -598,8 +601,12 @@ def test_tc7_a_cancelled_run_finishes_its_in_flight_chunk_and_stops_before_the_n
         snapshot = manager.snapshot()
 
     assert snapshot["state"] == "cancelled"
-    # A shorter-than-planned outcome list -- the walk stopped before every chunk was visited.
-    assert 0 < len(snapshot["progress"]["outcomes"]) < snapshot["progress"]["chunks_total"]
+    # Fewer chunks done than planned -- the walk stopped before every chunk was visited. Era
+    # iteration 11: `manager.snapshot()`'s own `progress` is now aggregate-only (spec section 7.1,
+    # r5) and no longer carries a raw `outcomes` list at all -- `chunks_done` is the SAME count
+    # `len(outcomes)` always equalled in the pre-iteration-11 shape (both incremented together by
+    # `_publish`), so this assertion's meaning is unchanged.
+    assert 0 < snapshot["progress"]["chunks_done"] < snapshot["progress"]["chunks_total"]
 
     runs = read_run_log(run_log_dir)
     assert len(runs) == 1
@@ -840,4 +847,143 @@ def test_cancel_while_running_stops_the_walk_cooperatively_through_the_route(rou
         mgr.join_all(timeout=10.0)
 
 
+# ==================================================================================================
+# 12. Era iteration 11 (spec section 7.1, r5): the LIVE recorder-progress path is aggregate-only
+#     at every point during a run -- TC-6/TC-7. The run-log route (GET .../recorder/runs, section
+#     11's `test_a_trigger_runs_to_done_records_a_dataset_and_the_runs_route_reports_it`) was
+#     already aggregate-only and is untouched; this section covers ONLY the live GET/POST compute
+#     paths, which used to carry a raw `progress.outcomes` list with each planned chunk's own
+#     symbol/date (`tick_recorder.py`'s pre-iteration-11 `_publish`/`_copy_recorder_snapshot`).
+# ==================================================================================================
+
+
+_PROGRESS_AGGREGATE_KEYS = {
+    "chunks_total", "chunks_done", "chunks_fetched", "chunks_reused", "chunks_unchanged",
+    "chunks_failed", "trades_total", "quotes_total", "percent_complete", "elapsed_seconds",
+}
+
+
+def _assert_progress_is_aggregate_only(progress: dict) -> None:
+    """TC-6's own field-shape assertion: EXACTLY the ten aggregate fields spec section 7.1 (r5)
+    names -- no ``outcomes``, no ``symbol``, no ``date``, no ``dataset_id``, nothing else."""
+    assert set(progress.keys()) == _PROGRESS_AGGREGATE_KEYS, sorted(progress.keys())
+
+
+def test_tc6_recorder_progress_never_leaks_a_planned_chunks_symbol_date_or_dataset_id(
+    route_ctx, monkeypatch
+):
+    """TC-6 (phase spec, literal scenario): "a tick-recorder compute job planned over 3 chunks
+    spanning 2 symbol-days ... polled mid-run and again after it reaches a terminal state ...
+    neither response body contains any planned chunk's symbol or date string value, nor any
+    dataset_id, anywhere in the JSON -- only chunks_total, chunks_done, the four per-outcome-type
+    counts, trades_total, quotes_total, percent_complete, and elapsed_seconds."
+
+    ``plan_recorder_chunks`` is monkeypatched to this EXACT 3-chunk/2-symbol-day plan: its own
+    real ``chunk_seconds`` default is bound at ITS OWN definition time (a plain Python default-
+    argument gotcha), so it cannot be narrowed through the public ``trigger()``/route surface
+    (which always calls it with none) without this -- the alternative, a real 26-chunks-per-
+    symbol-day walk under the recorder's own throttle, works too (proven by the route tests in
+    section 11 above) but is needlessly slow for what this test needs to prove. Everything AFTER
+    planning -- the walk, the checkpoints, the finalize, the manager's publish loop -- is
+    completely real, against the fake adapter."""
+    client, mgr, _adapter, tmp_path = route_ctx
+    from app.main import app, get_market_adapter
+
+    fake_plan = [
+        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T15:00:00Z"},
+        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T15:00:00Z", "end": "2026-06-01T20:00:00Z"},
+        {"symbol": "MSFT", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T20:00:00Z"},
+    ]
+    monkeypatch.setattr(tr, "plan_recorder_chunks", lambda symbols, dates: list(fake_plan))
+
+    blocking_adapter = _BlockingTickAdapter()
+    app.dependency_overrides[get_market_adapter] = lambda: blocking_adapter
+    try:
+        r = client.post(
+            "/research/desk/micro/recorder/compute",
+            json={"symbols": ["AAPL", "MSFT"], "dates": ["2026-06-01"]},
+        )
+        assert r.status_code == 200
+        assert blocking_adapter.started.wait(timeout=5.0)
+
+        # --- mid-run: the first chunk is being fetched, none have resolved yet ----------------
+        mid_run = client.get("/research/desk/micro/recorder/compute").json()
+        assert mid_run["state"] == "running"
+        assert mid_run["progress"]["chunks_total"] == 3
+        _assert_progress_is_aggregate_only(mid_run["progress"])
+        forbidden = {"AAPL", "MSFT", "2026-06-01"}
+        mid_run_text = json.dumps(mid_run)
+        for token in forbidden:
+            assert token not in mid_run_text, f"{token!r} leaked mid-run"
+        # the POST's own immediate return goes through the SAME projection (`trigger()`'s
+        # `published`, built by the SAME `_copy_recorder_snapshot`).
+        assert "AAPL" not in json.dumps(r.json()) and "MSFT" not in json.dumps(r.json())
+
+        blocking_adapter.proceed.set()  # let every remaining chunk (2, 3) proceed unblocked
+
+        deadline = time.time() + 15
+        terminal = None
+        while time.time() < deadline:
+            terminal = client.get("/research/desk/micro/recorder/compute").json()
+            if terminal["state"] != "running":
+                break
+            time.sleep(0.02)
+        assert terminal is not None and terminal["state"] == "done"
+
+        # --- terminal: still aggregate-only, and the aggregates are the RIGHT numbers ---------
+        _assert_progress_is_aggregate_only(terminal["progress"])
+        assert terminal["progress"]["chunks_done"] == terminal["progress"]["chunks_total"] == 3
+        assert terminal["progress"]["chunks_fetched"] == 3
+        assert terminal["progress"]["chunks_reused"] == 0
+        assert terminal["progress"]["chunks_unchanged"] == 0
+        assert terminal["progress"]["chunks_failed"] == 0
+        assert terminal["progress"]["trades_total"] == 3  # 1 trade/chunk -- the fake adapter's shape
+        assert terminal["progress"]["quotes_total"] == 3  # 1 quote/chunk
+        assert terminal["progress"]["percent_complete"] == 100.0
+        assert terminal["progress"]["elapsed_seconds"] >= 0.0
+
+        terminal_text = json.dumps(terminal)
+        for token in forbidden:
+            assert token not in terminal_text, f"{token!r} leaked at the terminal state"
+
+        # a leak-free trap that computed nothing proves nothing (the era's own "cannot pass merely
+        # because the rig computed nothing" discipline) -- the datasets were genuinely recorded.
+        dataset_store = DatasetStore(str(tmp_path / "datasets"))
+        records, _errors = dataset_store.list()
+        assert sorted(m["symbol"] for m in records) == ["AAPL", "MSFT"]
+
+        # the run-log route (already aggregate-only, untouched this iteration) still names them --
+        # proving the withholding above is TARGETED at the live path, never a blanket break.
+        runs = client.get("/research/desk/micro/recorder/runs").json()["runs"]
+        assert runs[0]["datasets_recorded"] == 2
+    finally:
+        blocking_adapter.proceed.set()
+        mgr.join_all(timeout=10.0)
+
+
+def test_tc7_the_recorder_progress_route_accepts_no_bypass_parameter_header_or_role(route_ctx):
+    """TC-7 (phase spec): "given the recorder-progress route's request handling, when it is
+    inspected for any query parameter, header, or role claim that would return per-chunk identity,
+    then none exists." Proven two ways: (1) the route's OWN OpenAPI schema declares zero
+    parameters of any kind (no query, no header, no path beyond the fixed URL); (2) a LIVE
+    behavioural check -- an arbitrary probe of query params and headers that might plausibly spell
+    "reveal it anyway" has literally no effect on the served body, because FastAPI ignores any
+    input a route does not declare. r5's own words: "There is no operator-only bypass -- using one
+    would itself be a human exposure event that destroys the tranche's blindness, and it is
+    unnecessary for ordinary monitoring." """
+    client, _mgr, _adapter, _tmp_path = route_ctx
+    from app.main import app
+
+    schema = app.openapi()["paths"]["/research/desk/micro/recorder/compute"]["get"]
+    assert schema.get("parameters", []) == []
+
+    plain = client.get("/research/desk/micro/recorder/compute").json()
+    probed = client.get(
+        "/research/desk/micro/recorder/compute",
+        params={"reveal": "true", "operator": "true", "role": "admin", "symbol": "AAPL", "bypass": "1"},
+        headers={"X-Operator-Override": "true", "X-Admin-Role": "operator", "Authorization": "Bearer x"},
+    ).json()
+    assert probed == plain  # every extra input is silently ignored -- no bypass exists anywhere
+
+
 from app.config import CONFIG  # noqa: E402 -- imported at bottom to keep the fixture section terse
diff --git a/apps/backend/tests/test_vault.py b/apps/backend/tests/test_vault.py
index 84aaa98..1c9ce12 100644
--- a/apps/backend/tests/test_vault.py
+++ b/apps/backend/tests/test_vault.py
@@ -1234,3 +1234,211 @@ def test_b7_seal_shard_refuses_an_empty_vault_secret(tmp_path):
     )
     assert row["exposure_state"] == "sealed"
     assert len(ledger.all_rows()) == 1
+
+
+# === Iteration 11 (docs/phases/goal-rapid-microscope-iter-11.md, DEFINITION OF DONE): TR-2
+# rewritten into spec section 9's deterministic inference-trap shape -- TC-8/TC-9. The r5
+# governing test, verbatim: "given the registered universe (section 7.2) plus EVERY public
+# artifact the system serves ... no still-unexposed vault-eligible shard is identifiable with
+# certainty." Builds on the SAME rig every TR-2 test above shares
+# (`_combined_fixture_store`/`_scope_everything_to`/`_sweepable_get_paths`/`_scalars`/
+# `_poll_compute`), widened to a REGISTERED universe with FOUR pool members in THREE distinct
+# provenance shapes -- exactly this iteration's own gap: a legitimately EXPOSED member, a
+# ledger-tracked SEALED member (the ONLY case the pre-iteration-11 predicate ever recognized), and
+# TWO UNTRACKED members (zero vault ledger row at all -- what a real recorder run produces TODAY,
+# since nothing wires ``tick_recorder.py`` to ``vault.py`` yet; a repo-wide grep at authoring finds
+# zero production call sites of ``seal_shard``/``assign_shard``/``expose_shard``).
+# =====================================================================================================
+
+
+def _record_pool_dataset(store: DatasetStore, *, symbol: str, session_date: str, nonce: int) -> dict:
+    """One dataset for (symbol, session_date), in NO real panel/universe and globally distinctive
+    via ``nonce`` -- the ``_record_distinctive_dataset`` recipe above, generalized to many
+    (symbol, date) pairs instead of one, at a comparable size (135+ trades/quotes) to the sibling
+    already proven to survive Snapshot/Scout/edge-report/PnL compute acts
+    (``test_tr2_holds_after_the_operator_runs_every_micro_compute_act``/``test_tr2_holds_after_
+    the_corpus_wide_report_acts`` above)."""
+    trades_n, quotes_n = 137 + nonce, 241 + nonce
+    events: list = [QuoteEvent(symbol, float(i), 99.99, 100.02, 100, 100) for i in range(quotes_n)]
+    events += [TradeEvent(symbol, float(i) + 0.5, 100.03 + nonce, 10, Side.BUY) for i in range(trades_n)]
+    return store.record(
+        symbol=symbol, source="historical", source_kind="historical", source_id=symbol,
+        split="train", window_start_utc=f"{session_date}T13:31:07Z",
+        window_end_utc=f"{session_date}T19:57:41Z", data_feed="sip", epoch_anchor=0.0, events=events,
+    )
+
+
+def test_tc8_tc9_r5_inference_trap_a_registered_pool_with_mixed_provenance_leaves_ge2_candidates(
+    tmp_path, monkeypatch
+):
+    """TC-8 + TC-9 (phase spec; spec section 9's TR-2 row): the deterministic r5 inference trap,
+    run against a fixture pool in mixed ledger-tracked/untracked provenance, with the operator
+    compute acts run FIRST so the trap "cannot pass merely because the rig computed nothing."
+
+    TC-8's main assertion: for every still-unexposed member, at least 2 candidate (symbol, date)
+    identities remain consistent with everything served, and no complete identity-labelled
+    exploratory/sealed partition is derivable.
+
+    TC-9's counter-test: the PRE-fix subtraction attack (list ``GET /research/datasets``'s served
+    ids, compute the universe's full expected set, subtract) -- run here directly against the OLD,
+    still-exported ``vault.withheld_universe_by_dataset_id`` predicate (byte-unchanged; iteration
+    11 never edits it, only adds a second, wider predicate alongside it) -- WOULD have isolated
+    the sealed-but-untracked dataset's identity uniquely, proving TC-8's fixed-code assertion
+    above is not vacuous."""
+    _scope_everything_to(tmp_path, monkeypatch)
+    store = _combined_fixture_store(tmp_path)  # the 2 real PG fixtures -- proven compute-safe
+
+    symbols, dates = ["ZQXPOOL1", "ZQXPOOL2"], ["2031-06-01", "2031-06-02"]
+    expected_pairs = frozenset((s, d) for s in symbols for d in dates)
+
+    # the universe is registered BEFORE any of its 4 pairs is recorded (spec section 7.2's own
+    # mandated order, and TC-4's own `created_utc >= registered_at` guard: recording BEFORE
+    # registration would make every pair a pre-existing dataset the universe-rule check must
+    # never withhold -- the exact TC-4 scenario, deliberately NOT this test's scenario).
+    vault_dir = str(tmp_path / "micro_vault")
+    universe_ledger = vault.VaultUniverseLedger(vault_dir)
+    vault.register_universe(
+        universe_ledger, universe_id="pool-tr2", symbol_rule=symbols, date_rule=dates,
+        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
+    )
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+
+    metas: dict[tuple[str, str], dict] = {}
+    for s_index, symbol in enumerate(symbols):
+        for d_index, session_date in enumerate(dates):
+            metas[(symbol, session_date)] = _record_pool_dataset(
+                store, symbol=symbol, session_date=session_date, nonce=s_index * 10 + d_index,
+            )
+
+    exposed_pair = ("ZQXPOOL1", "2031-06-01")
+    sealed_only_pair = ("ZQXPOOL1", "2031-06-02")
+    untracked_pairs = [("ZQXPOOL2", "2031-06-01"), ("ZQXPOOL2", "2031-06-02")]
+    unresolved_pairs = frozenset(expected_pairs - {exposed_pair})
+    assert len(unresolved_pairs) >= 2  # the TC-8 threshold this fixture must clear by construction
+
+    exposed_meta = metas[exposed_pair]
+    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+    vault.seal_shard(
+        shard_ledger, dataset_id=exposed_meta["id"], universe_id="pool-tr2",
+        content_checksum=exposed_meta["checksum"], event_count=exposed_meta["event_counts"]["total"],
+        vault_secret=_FIXTURE_SECRET,
+    )
+    vault.assign_shard(
+        shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root,
+        symbol=exposed_pair[0], session_date=exposed_pair[1],
+    )
+    vault.expose_shard(shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root)
+
+    sealed_meta = metas[sealed_only_pair]
+    vault.seal_shard(
+        shard_ledger, dataset_id=sealed_meta["id"], universe_id="pool-tr2",
+        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=_FIXTURE_SECRET,
+    )
+    # the 2 untracked pairs get NO vault call at all -- today's actual recorder gap.
+
+    from app.config import CONFIG
+    from app.mcp import _STATIC_PATHS
+    from app.research import edge_report, pnl_scan
+    from app.research.referee_registry import CertificateStore
+    from app.research.store import JournalStore
+
+    with TestClient(app) as client:
+        # --- the operator compute acts, RUN FIRST (spec section 9: "cannot pass merely because
+        # the rig computed nothing") -----------------------------------------------------------
+        assert client.post("/research/desk/micro/snapshots/compute").json()["state"] == "running"
+        assert _poll_compute(client, "/research/desk/micro/snapshots/compute")["state"] == "done"
+        assert client.post("/research/desk/micro/scout/compute").json()["state"] == "running"
+        assert _poll_compute(client, "/research/desk/micro/scout/compute")["state"] == "done"
+
+        built = {m["dataset_id"] for m in client.get("/research/desk/micro/snapshots").json()["snapshots"]}
+        assert exposed_meta["id"] in built
+        assert sealed_meta["id"] not in built
+        assert all(metas[p]["id"] not in built for p in untracked_pairs)
+
+        journal = JournalStore(CONFIG.journal_db_path_resolved(), CONFIG)
+        try:
+            report = edge_report.run_edge_report(journal, store, CONFIG)
+            sweep = pnl_scan.run_sweep(
+                journal, store, CONFIG, certificate_store=CertificateStore(tmp_path / "referee_registry"),
+            )
+        finally:
+            journal.close()
+
+        # the counter-test half: the compute acts really did measure something (never vacuous) --
+        # the 2 PG siblings and the legitimately exposed pool dataset, never the 3 unresolved ones.
+        measured = {r["dataset_id"] for r in report["train"]["datasets"] + report["holdout"]["datasets"]}
+        assert exposed_meta["id"] in measured
+        assert sealed_meta["id"] not in measured
+        assert all(metas[p]["id"] not in measured for p in untracked_pairs)
+        assert report["withheld_excluded"] == 3
+        assert sweep["withheld_excluded"] == 3
+
+        # --- NOW sweep every registered route + the recorder-progress path + the `datasets` MCP
+        # tool (structurally proven to coincide with the REST sweep by
+        # test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route above) -------------
+        swept: dict[str, object] = {}
+        for path in _sweepable_get_paths():
+            url = path.replace("{dataset_id}", exposed_meta["id"])
+            if "{" in url:
+                continue
+            response = client.get(url)
+            try:
+                swept[path] = response.json()
+            except ValueError:
+                swept[path] = response.text
+        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
+        assert "/research/desk/micro/recorder/compute" in swept  # TC-6's own path, in this sweep too
+        assert _STATIC_PATHS["datasets"] in swept  # the `datasets` MCP tool's exact proxied path
+
+        served_text = json.dumps(swept, sort_keys=True, default=str)
+
+        # --- TC-8's main assertion: no still-unexposed member's identity is derivable ----------
+        # the positive reconstruction: subtract what IS served from what the KNOWN universe rule
+        # expects -- this is exactly the attack r5 exists to defeat, EXECUTED, not merely asserted
+        # absent.
+        datasets_body = swept["/research/datasets"]
+        served_identified_pairs = {
+            (row["symbol"], _et_session_date(row["window_start_utc"])) for row in datasets_body["datasets"]
+        }
+        assert served_identified_pairs & expected_pairs == {exposed_pair}
+        remaining_candidates = expected_pairs - served_identified_pairs
+        assert remaining_candidates == unresolved_pairs
+        assert len(remaining_candidates) == 3  # >= 2 -- no unique identity isolated for ANY of them
+
+        # readiness's OWN listing must agree byte-for-byte with the same reconstruction -- two
+        # surfaces answering "which pairs are identified" can never diverge.
+        readiness = swept["/research/desk/micro/readiness"]
+        readiness_identified_pairs = {
+            (row["symbol"], row["session_date"])
+            for row in readiness["shards"]
+            if (row["symbol"], row["session_date"]) in expected_pairs
+        }
+        assert readiness_identified_pairs == {exposed_pair}
+        assert readiness["sealed_tranche"]["shard_count"] == 3
+        assert readiness["sealed_tranche"]["by_universe"] == {
+            "pool-tr2": {"shard_count": 3, "symbol_days": 3}
+        }
+
+        # no unresolved member's dataset id or raw checksum appears ANYWHERE in the swept union --
+        # the join-resistance claim, applied to every unresolved member. Both are long, globally
+        # unique hex strings (never a plain small integer -- see `_scope_everything_to`'s own
+        # comment on why THIS file avoids asserting small scalars are absent: a coincidental
+        # collision with an unrelated route's own real count is a false positive, not a leak).
+        for pair in unresolved_pairs:
+            meta = metas[pair]
+            assert meta["id"] not in served_text, f"{pair}'s dataset id leaked"
+            assert meta["checksum"] not in served_text, f"{pair}'s raw checksum leaked"
+
+        # --- TC-9's counter-test: the PRE-fix predicate WOULD have isolated a unique identity --
+        pre_fix_withheld_ids = set(vault.withheld_universe_by_dataset_id(shard_ledger))
+        assert pre_fix_withheld_ids == {sealed_meta["id"]}  # the ONLY case the old predicate saw
+        pre_fix_served_pairs = {
+            pair for pair, meta in metas.items() if meta["id"] not in pre_fix_withheld_ids
+        }
+        pre_fix_remaining = expected_pairs - pre_fix_served_pairs
+        assert pre_fix_remaining == {sealed_only_pair}, (
+            "the pre-fix subtraction attack should isolate exactly the ledger-tracked-but-"
+            "unexposed dataset's (symbol, date) uniquely -- proving TC-8's fixed-code assertion "
+            "above is not vacuous"
+        )
diff --git a/docs/goal.md b/docs/goal.md
index f988cf3..1998325 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -154,14 +154,16 @@ items, in that order.**
    `08e471b10130e1e2` every iteration; every `referee_*` module byte-identical to `main` at
    era open (SHA-256 listing recorded at iteration 0 and re-checked); every kept `/`,
    `/structure`, `/desk` behavior browser-verified as shipped.
-2. **No leakage trap fails, ever.** The TR-1…TR-22 suite of
+2. **No leakage trap fails, ever.** The TR-1…TR-26 suite of
    [`docs/rapid-validation-spec.md`](rapid-validation-spec.md) §9 is implemented and green:
    prefix discipline, origin fencing, sealed-shard sweeps, cherry-pick refusal, class-mixing
    refusal, purge exactness, screening calibration, pool invariance, ledger chain integrity,
    single-shot sealed exposure, geometry freeze, rule identity, tick-corpus refusal, the
-   synthetic known-null / known-effect end-to-end oracles — and the r2 traps: TR-17
+   synthetic known-null / known-effect end-to-end oracles — the r2 traps: TR-17
    future-event availability, TR-18 units gate, TR-19 Card-5.1 preservation prerequisite,
-   TR-20 root-family lineage, TR-21 process-label discipline, TR-22 exposure registry.
+   TR-20 root-family lineage, TR-21 process-label discipline, TR-22 exposure registry — and
+   the r6 traps: TR-23 sealed-verdict ownership, TR-24 lineage confirmation boundary,
+   TR-25 vault-ledger integrity, TR-26 depletion revealing-quote availability.
 3. **Every trial is on the record.** The scout ledger is hash-chained append-only; every
    evaluated variant — every kill, with its closed-vocabulary reason — is a permanent row; the
    union-N denominator is served beside every family; "statistically above null" and
@@ -658,9 +660,11 @@ operator-attended act inside the era.
 
 - **J-10: The kept product stands — traps armed, sentinel green**
   - Steps:
-    1. Land the full TR-1…TR-22 suite (whichever traps did not ship inside J-02…J-07 land
+    1. Land the full TR-1…TR-26 suite (whichever traps did not ship inside J-02…J-07 land
        here — the r2 traps TR-17 availability, TR-18 units, TR-19 preservation, TR-20 root
-       lineage, TR-21 process labels, TR-22 exposure registry included) plus the extended
+       lineage, TR-21 process labels, TR-22 exposure registry, and the r6 traps TR-23
+       sealed-verdict ownership, TR-24 lineage boundary, TR-25 vault-ledger integrity,
+       TR-26 depletion revealing quote, included) plus the extended
        guard tests (accessor import-ban, micro threshold-sweep ban, copy discipline for micro
        copy, `_PRICE_ARITHMETIC_FIELDS` additions).
     2. Run the deterministic-rerun check (byte-identical snapshot/screen/fold outputs on a
diff --git a/docs/rapid-validation-spec.md b/docs/rapid-validation-spec.md
index f79779c..fed596c 100644
--- a/docs/rapid-validation-spec.md
+++ b/docs/rapid-validation-spec.md
@@ -72,6 +72,26 @@
 > the cartesian shape with recording-cost decoys. Where the shipped architecture requires every
 > non-sealed shard to become individually visible at record time, the ARCHITECTURE changes. The
 > one-way exposure history and the single-shot `family_root_id` rules are preserved unchanged.
+>
+> **Revision r6 (2026-08-18, owner rulings — the sealed verdict has an owner).** Four rulings from
+> the iteration-10 escalation, applied while ZERO shards are sealed and ZERO sealed evaluations
+> exist, so nothing re-keys and no recorded verdict moves. (1) **§8.1 `SEALED_PASS_RULE_V1`** — the
+> single-shot sealed verdict gets ONE scientific owner (`micro_sealed_evaluation.py`), which
+> recomputes outcomes from canonical machinery and derives the verdict from already-frozen
+> quantities; `record_sealed_evaluation` may no longer accept a caller-asserted `passed: bool`. This
+> revision exists because the owner's ruling explicitly forbade implementing the evaluator against
+> an undefined pass rule ("stop at the methodology boundary and add the smallest pre-implementation
+> named clarification defining it… do not let the developer choose thresholds"). **It introduces NO
+> new numeric constant** — every floor it applies is one §1 already pins or the family already
+> pre-registered. (2) **§8.2 the confirmation-boundary derivation** — lineage-wide, not
+> survivor-row-wide, with the Referee registration boundary kept as an independent no-backdating
+> floor. (3) **§7.8 vault-ledger corruption** — fail closed on any `verify_chain()` failure, with
+> recovery only through evidence-backed reconstruction; operator attestation is audit metadata,
+> never proof of missing history; unknown exposure history may NEVER be read as "never exposed".
+> (4) **§2.2/§3 `quote_depletion` availability** — the "one quote early" stamp on price-change-
+> terminated runs is corrected to the REVEALING quote. Ruling 4 is recorded here as a note only: it
+> is an implementation bug against r2's existing availability law, not a methodology change, and the
+> owner directed that no revision be created solely for it.
 
 ---
 
@@ -141,7 +161,7 @@
 | `REFILL_M_QUOTES` | `20` | `refill_consistent` observation window: same-side quote updates after the execution; `available_at` = the M-th update; session-end first ⇒ `unavailable` |
 | `RESPONSE_K_TRADES` | `20` | Response-asymmetry window: trades after the print; `available_at` = the K-th trade |
 | `BURST_BASELINE_TRAILING_WINDOWS` | `20` | Burst baseline = median of this many prior non-overlapping same-length windows in the SAME session prefix; fewer than `5` ⇒ burst undefined (counted) |
-| `DEPLETION_WINDOW_QUOTES` | `20` | Quote-depletion observation bound: consecutive same-side quote updates at an unchanged price; ends at a price change or the bound; `available_at` = window end |
+| `DEPLETION_WINDOW_QUOTES` | `20` | Quote-depletion observation bound: consecutive same-side quote updates at an unchanged price; ends at a price change or the bound; `available_at` = the REVEALING quote (r6, §3) — the bound-hitting quote, or the price-CHANGING quote for a price-change termination |
 | `IMPACT_FLATNESS_SCALE_BPS` | `5.0` | The frozen flatness scale: `flatness = clamp(1 − |Δmid_bps| / 5.0, 0, 1)`; `failed_aggression_score = dominant_side_volume_share × flatness` per feature window |
 | `DIVERGENCE_TRAILING_SECONDS` | `120.0` | Divergence-at-level price/volume window: TRAILING `[τ − 120s, τ]`, as-of the touch — supersedes Card 9.1's symmetric "window around the touch"; `available_at` = τ |
 | `DIVERGENCE_DELTA_VOLUME_FRACTION` | `0.25` | Card 9.1's δ fraction, frozen HERE as a module constant (never a Config field): `δ = 0.25 × median trailing-120s volume` over the session-prefix baseline windows |
@@ -264,7 +284,11 @@ and `unknown_frac`. Any aggressor-derived quantity is served beside those two fr
   `quote_size_unit`); quote depletion = the drawdown of same-side displayed size across
   consecutive quote updates at an unchanged price, observed over at most
   `DEPLETION_WINDOW_QUOTES` updates (ends at a price change or the bound; a DEFERRED
-  construct, `available_at` = window end); replenishment (`refill_consistent`: displayed size
+  construct whose `available_at` is the **REVEALING** quote, not the last measured one —
+  **measurement end ≠ knowledge time** (r6): a bound-terminated run is revealed by the
+  bound-hitting quote, so `available_at` is that quote; a price-change-terminated run is only
+  revealed by the price-CHANGING quote, so `available_at` is THAT quote — which is excluded from
+  the depletion measurement itself, exactly as its own conditioning data would be); replenishment (`refill_consistent`: displayed size
   restored at the same price within the next `REFILL_M_QUOTES` same-side quote updates after
   executions against it — a DEFERRED construct, `available_at` = the M-th update or
   `unavailable`; **the ONLY permitted label** — "iceberg", "institutional", "spoof" and any
@@ -614,6 +638,37 @@ same-session bar features, computed on exploratory data) is REPORTED beside seal
 it is a diagnostic only, **never a gate, never tunable, and never an authority**; independence is
 decided by the deterministic provenance/exposure rules above alone.
 
+### 7.8 Vault-ledger integrity — fail closed, recover only on evidence (r6)
+
+**The invariant: unknown exposure history may NEVER be interpreted as "never exposed."** A
+truncated tail that silently makes shards look fresh is the worst failure this system can have.
+
+Every vault/exposure predicate calls `verify_chain()` FIRST. Any verification failure raises a
+typed refusal and halts ALL vault work — no sealing, no assignment, no exposure check, no sealed
+evaluation, no graduation — until a lawful recovery completes. There is no warn-and-continue path,
+and operator attestation alone can NEVER certify missing history; the attestation is audit
+metadata, not evidence.
+
+**Lawful recovery** (the only way back) must, in order: halt vault/sealed work · record the
+corruption event separately and immutably · preserve the corrupt ledger BYTE-FOR-BYTE for forensics
+· identify the last verified chain row · reconstruct the missing suffix from trusted immutable
+sources (durable recorder/vault operation artifacts, immutable §8.1 evaluation artifacts,
+append-only graduation/export records, or a backup whose hash was committed BEFORE the corruption)
+· verify the reconstruction is internally consistent and that every exposure, assignment and
+evaluation event is accounted for · write a NEW ledger epoch/recovery record citing the corrupt
+ledger hash, last verified row + hash, reconstruction sources + hashes, recovered suffix hash,
+operator identity and time, and an explicit recovery reason. Only then may predicates resume.
+
+**If the missing suffix cannot be PROVEN complete, recovery must not truncate to the last verified
+row.** Every shard whose freshness could be affected is conservatively marked `exposure_unknown`
+and is permanently ineligible for sealed-OOS use — or the whole tranche halts.
+
+**Traps.** Truncating the tail ⇒ all exposure predicates fail closed · mutating an interior row ⇒
+fail closed · replacing the ledger with a last-known-good prefix ⇒ still fail closed when a later
+committed checkpoint proves history should exist · a successful hash-pinned reconstruction restores
+the EXACT prior exposure state · an unverifiable recovery can never make an affected shard fresh
+again.
+
 ---
 
 ## 8. Graduation (`micro_graduation.py`)
@@ -640,6 +695,81 @@ States, strictly ordered; every transition is an append-only ledger event with f
 
 No state ever moves backward except by a voiding event (§6.2), which is itself permanent history.
 
+### 8.1 The sealed verdict has one owner — `SEALED_PASS_RULE_V1` (r6)
+
+**The ledger owns history; the evaluator owns the answer.** A caller-supplied `passed: bool` is
+inadmissible for a single-shot permanent verdict. Sealed evaluation has exactly ONE scientific
+owner module, `micro_sealed_evaluation.py`; `micro_graduation.py` and `vault.py` remain
+persistence and transition machinery and neither accepts nor invents the scientific answer.
+
+**The evaluator's mandatory sequence** (any step failing ⇒ typed refusal, never a verdict):
+1. require an ASSIGNED sealed shard and a candidate spec frozen BEFORE that assignment;
+2. load the candidate's canonical registered spec and verify its `spec_hash`, `family_root_id`,
+   outcome basis, sidedness, economic floor, and the sample/breadth floors below;
+3. obtain the shard ONLY through the sanctioned accessor/exposure path (§6.1, §7.4);
+4. RECOMPUTE the sealed outcomes from the canonical snapshot/outcome machinery — a
+   caller-computed effect value is never authoritative;
+5. derive the verdict deterministically from `SEALED_PASS_RULE_V1`;
+6. persist an immutable **evaluation artifact** (below);
+7. pass ONLY that artifact's id + hash to the graduation transition.
+
+**`SEALED_PASS_RULE_V1` (frozen; introduces no new constant).** A (root family, shard) evaluation
+`passes` iff ALL of:
+1. the shard's recomputed observations meet the per-fold sufficiency floors already pinned in §1 —
+   `WF_FOLD_MIN_OBSERVATIONS` observations, `WF_FOLD_MIN_SIGNAL_SESSIONS` signal-bearing sessions,
+   and `WF_FOLD_MIN_SYMBOLS` symbols whenever the family claims breadth; below any floor the
+   verdict is `insufficient`, which is neither a pass nor a fail and consumes the single shot
+   ONLY if the shard was exposed (an exposure is irreversible either way);
+2. the session-clustered effect lies in the family's REGISTERED direction (§5.1 sidedness);
+3. its magnitude ≥ the family's own pre-registered economic floor (§5.5) — the same floor the
+   walk-forward applied, not a new one;
+4. the evaluation rule id/version/hash recorded at assignment is byte-identical to the one applied
+   (a rule changed after assignment fails CLOSED);
+5. the shard's evidence class is `historical_oos` and its process label `rule_process` (§6.7/§6.8).
+Anything less is a FAIL, and a fail is permanent for the root family (§7.4). There is no
+discretionary override and no partial credit.
+
+**The evaluation artifact** (immutable, hash-addressed, sufficient to reproduce the verdict):
+candidate + spec identity and hashes · `family_root_id` · shard identity and checksum AFTER lawful
+assignment · evidence class · process label · outcome basis · n / sessions / symbol breadth ·
+effect and economic-floor inputs · registered direction · rule id/version/hash · the deterministic
+verdict · the closed-vocabulary failure reason when not a pass.
+
+**Traps (all deterministic).** A caller-asserted boolean is impossible/refused · mutating ANY
+evaluation input changes the artifact hash and invalidates the transition · an unregistered rule,
+or one changed after assignment, fails closed · re-running the evaluator over identical inputs
+yields a byte-identical artifact and verdict · a second sealed evaluation for the same
+(`family_root_id`, shard) is refused · a failed verdict travels in every later export bundle.
+
+### 8.2 The proposed confirmation boundary — lineage-wide (r6)
+
+Survivor rows are NOT the basis; the LINEAGE is. Define:
+
+- **`lineage_data_frontier`** = `max(observed_through)` across every evidence item ever touched by
+  the computed `family_root_id` lineage — surviving candidates, killed and superseded siblings,
+  walk-forward folds of ANY verdict, diagnostic and `operator_process` folds, assigned/exposed
+  sealed shards including failed and `insufficient` evaluations, and any other outcome-bearing read
+  in the exposure registry (§6.7). `observed_through` is used, never anchor/event time, so a
+  deferred construct cannot backdate the frontier.
+- **`evidence_safe_boundary`** = `lineage_data_frontier` + the applicable dependency embargo (§6.3),
+  applied in its registered session/market semantics — never as an ad-hoc wall-clock delta.
+- **`proposed_confirmation_boundary`** = the first eligible market/session boundary STRICTLY after
+  `max(evidence_safe_boundary, handoff_created_at)`.
+
+At actual Referee registration the immutable `confirmation_start_boundary` must be no earlier than
+BOTH the bundle's proposed boundary and the Referee's own registration-time boundary:
+`final = next_eligible(max(proposed_confirmation_boundary, referee_registration_boundary))`.
+**Backdating is never permitted.**
+
+The bundle persists the whole derivation: `lineage_data_frontier`, the evidence ids contributing to
+the max, `frontier_observed_through`, the embargo rule id and value, `evidence_safe_boundary`,
+`handoff_created_at`, and `proposed_confirmation_boundary`.
+
+**Traps.** A killed sibling of the same `family_root_id` with a LATER `observed_through` than the
+survivor must push the proposed boundary past it — proving lineage knowledge cannot be laundered
+through candidate selection. A deferred feature with `anchor_at < observed_through` must move the
+boundary by its `observed_through`.
+
 ---
 
 ## 9. The trap suite (all deterministic, all in CI)
@@ -668,6 +798,10 @@ No state ever moves backward except by a voiding event (§6.2), which is itself
 | TR-20 root lineage | A re-registered family with the same (feature family, context kind, outcome family) triple COMPUTES the same `family_root_id` (the rename attack is refused at the sealed door); a genuinely different triple computes a different root |
 | TR-21 process label | A sequence containing a logged operator selection after any fold reveal is `operator_process` and is refused at `walkforward_survivor`; a pre-reveal registered shortlist keeps `rule_process` |
 | TR-22 exposure registry | A spec registered after a logged serving of its validation window is auto-classed `historical_exposed_diagnostic`; the registry's r2 initialization marks every playbook-corpus and legacy-tick window exposed |
+| TR-23 sealed-verdict ownership (r6 §8.1) | A caller-asserted `passed` boolean is impossible/refused · mutating any evaluation input changes the artifact hash and invalidates the transition · a rule unregistered, or changed after assignment, fails closed · re-running the evaluator on identical inputs yields a byte-identical artifact and verdict · a second sealed evaluation for the same (`family_root_id`, shard) is refused · a failed verdict travels in every later export bundle |
+| TR-24 lineage boundary (r6 §8.2) | A KILLED sibling of the same `family_root_id` with a later `observed_through` than the survivor pushes `proposed_confirmation_boundary` past it (lineage knowledge cannot be laundered through candidate selection) · a deferred feature with `anchor_at < observed_through` moves the boundary by its `observed_through` · the final Referee boundary is never earlier than either the proposed or the registration boundary |
+| TR-25 vault-ledger integrity (r6 §7.8) | Tail truncation ⇒ every exposure predicate fails closed · interior-row mutation ⇒ fails closed · a last-known-good prefix still fails closed when a committed checkpoint proves later history existed · a hash-pinned reconstruction restores the exact prior exposure state · an unverifiable recovery never makes an affected shard fresh again (`exposure_unknown`, permanently sealed-OOS-ineligible) |
+| TR-26 depletion revealing quote (r6 §3) | Price-change termination: `available_at` equals the first CHANGED-price quote, not the last same-price one · bound termination: `available_at` equals the bound-hitting quote · truncating immediately BEFORE the revealing quote makes the depletion value non-existent/unavailable, and including it makes the value appear deterministically |
 
 Plus the standing suite: engine golden trace + observer equivalence + frozen-default profile,
 fingerprint pin `08e471b10130e1e2`, referee modules byte-untouched, no-execution scan, copy
```
