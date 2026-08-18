# Iteration diff (bounded)

Files changed: 33. Shown in full: 31.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/vault.py` (443 lines not shown)
- `apps/backend/tests/test_vault.py` (842 lines not shown)

```diff
diff --git a/apps/backend/app/research/datasets.py b/apps/backend/app/research/datasets.py
index fc2ffba..d36c987 100644
--- a/apps/backend/app/research/datasets.py
+++ b/apps/backend/app/research/datasets.py
@@ -319,6 +319,15 @@ class DatasetStore:
         self._index_db_path = index_db_path
         self._index: DatasetIndex | None = None
 
+    @property
+    def root(self) -> Path:
+        """This store's own resolved directory (the ``desk_forward.ForwardStore.root`` precedent).
+        Read-only, no I/O. Exists so a caller holding only a store can resolve the SIBLING vault
+        location the same way every other vault consumer does
+        (``vault.shard_ledger_for_dataset_dir``) instead of reaching for ``CONFIG``, which would
+        resolve the OPERATOR's real store from a ``tmp_path``-scoped test."""
+        return self._root
+
     def _durable_index(self) -> DatasetIndex | None:
         if self._index_db_path is None:
             return None
@@ -498,6 +507,8 @@ class DatasetStore:
         events: list[Event],
         schema_basis: str | None = None,
         quote_size_unit: str | None = None,
+        quote_size_unit_rule_text: str | None = None,
+        quote_size_unit_verification_note: str | None = None,
     ) -> dict:
         """Persist ONE new dataset (record + register in a single explicit action). The split tag
         is assigned HERE and frozen: content already registered under any split raises the
@@ -516,7 +527,15 @@ class DatasetStore:
         supplied ``quote_size_unit`` is validated against the EXISTING
         ``micro_features.QUOTE_SIZE_UNITS`` tuple (the sole unit vocabulary in the repo — this
         module defines no second one) and rejected explicitly, never silently accepted, exactly
-        like the ``split`` check immediately below."""
+        like the ``split`` check immediately below.
+
+        ``quote_size_unit_rule_text``/``quote_size_unit_verification_note`` (era "The Rapid
+        Microscope" J-06 step 3, spec section 2.6's own closing clause: "the recorder records the
+        rule text and the verification note beside the stamp") are two FURTHER optional, additive
+        manifest siblings of ``quote_size_unit`` — same absent-key-is-absent stamping discipline
+        (TC-12), same checksum exclusion (manifest metadata, never tape content — TC-13's
+        byte-identical-checksum counter-test proves it, exactly like ``schema_basis``/
+        ``quote_size_unit`` already do)."""
         if split not in VALID_SPLITS:
             raise ValueError(f"unknown split {split!r} — expected one of {sorted(VALID_SPLITS)}")
         if quote_size_unit is not None and quote_size_unit not in QUOTE_SIZE_UNITS:
@@ -558,6 +577,10 @@ class DatasetStore:
             meta["schema_basis"] = schema_basis
         if quote_size_unit is not None:
             meta["quote_size_unit"] = quote_size_unit
+        if quote_size_unit_rule_text is not None:
+            meta["quote_size_unit_rule_text"] = quote_size_unit_rule_text
+        if quote_size_unit_verification_note is not None:
+            meta["quote_size_unit_verification_note"] = quote_size_unit_verification_note
         record = {"meta": meta, "events": rows}
         payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
         self._root.mkdir(parents=True, exist_ok=True)
@@ -628,12 +651,15 @@ def record_from_source(
     historical_fetch: Callable[[], HistoricalWindow] | None = None,
     schema_basis: str | None = None,
     quote_size_unit: str | None = None,
+    quote_size_unit_rule_text: str | None = None,
+    quote_size_unit_verification_note: str | None = None,
 ) -> dict:
     """Record + register ONE dataset from a historical source (the explicit research action).
 
-    ``schema_basis``/``quote_size_unit`` (era "The Rapid Microscope" J-06 step 1) pass straight
-    through to ``DatasetStore.record`` — see that method's own docstring; omitted by every
-    existing caller (none pass these yet), so the manifest shape is byte-unchanged for them.
+    ``schema_basis``/``quote_size_unit``/``quote_size_unit_rule_text``/
+    ``quote_size_unit_verification_note`` (era "The Rapid Microscope" J-06 steps 1 and 3) pass
+    straight through to ``DatasetStore.record`` — see that method's own docstring; omitted by
+    every pre-J-06-step-3 caller, so the manifest shape is byte-unchanged for them.
 
     ``reference`` loads the committed keyless PG SIP fixture (optionally sliced to
     ``[start, end)``); ``historical`` calls the injected ``historical_fetch`` built on the
@@ -677,6 +703,8 @@ def record_from_source(
         events=events,
         schema_basis=schema_basis,
         quote_size_unit=quote_size_unit,
+        quote_size_unit_rule_text=quote_size_unit_rule_text,
+        quote_size_unit_verification_note=quote_size_unit_verification_note,
     )
 
 
diff --git a/apps/backend/app/research/desk_screen.py b/apps/backend/app/research/desk_screen.py
index b8938b4..e1a2e6e 100644
--- a/apps/backend/app/research/desk_screen.py
+++ b/apps/backend/app/research/desk_screen.py
@@ -149,6 +149,8 @@ from .datasets import DatasetStore
 from .desk_coverage import DESK_TOPUP_TIMEFRAMES, get_desk_coverage
 from .desk_meta_cache import SCREEN_TABLE, DeskMetaCache
 from .desk_universe import UniverseStore
+# Spec section 7.5 point 6 (r4): the ONE withholding predicate, imported not re-implemented.
+from .micro_snapshots import exclude_withheld
 from .tradability import compute_tradability
 
 # The two band sides `compute_tradability` serves. Only `RESISTANCE` is referenced by name below
@@ -703,6 +705,12 @@ def compute_screen(
     coverage_signature = screen_coverage_signature(coverage_payload, as_of)
 
     dataset_records, _dataset_errors = dataset_store.list()
+    # Spec section 7.5 point 6 (r4) + iter-9 audit finding B6: a symbol whose ONLY tick recording
+    # is a withheld Validation-Vault shard must not flip `tick_evidence` to true -- that boolean
+    # leaks sealed-tranche membership at symbol granularity, and section 7.5 withholds symbol
+    # membership until exposure. Excluded through the ONE shared predicate, and the count (never
+    # the ids) is disclosed in this screen's own payload and recorded snapshot below.
+    dataset_records, withheld_excluded = exclude_withheld(dataset_records, dataset_store)
     tick_symbols = {meta["symbol"] for meta in dataset_records}
 
     config_fingerprint = config.config_fingerprint()
@@ -783,6 +791,9 @@ def compute_screen(
         "screen_coverage_signature": coverage_signature,
         "rows": rows,
         "skipped": skipped,
+        # Spec section 7.5 point 6 (r4): how many recorded tick datasets were NOT eligible to
+        # supply `tick_evidence` for this screen, because their vault shards are withheld.
+        "withheld_excluded": withheld_excluded,
     }
 
 
@@ -1167,6 +1178,7 @@ class ScreenStore:
         rows: list[dict],
         skipped: list[dict],
         screen_coverage_signature: str | None = None,
+        withheld_excluded: int | None = None,
     ) -> dict:
         """Persist ONE new screen snapshot (record + register in a single explicit action). A
         snapshot already registered under this EXACT 5-pin key raises the 409-style
@@ -1181,7 +1193,13 @@ class ScreenStore:
         distinguishing power. Omitting it (the default) writes a snapshot in the pre-addition shape
         -- the key ABSENT from ``meta`` entirely, never ``null`` -- which is what every snapshot
         recorded before this addition looks like on disk and what a test planting a legacy record
-        wants; the compute path always passes a real value."""
+        wants; the compute path always passes a real value.
+
+        ``withheld_excluded`` (spec section 7.5 point 6, r4) follows the IDENTICAL optional shape,
+        for the identical reason: it is the count of recorded tick datasets ``run_screen`` left out
+        of this screen's ``tick_evidence`` basis because their Validation-Vault shards are withheld
+        -- a count, never an id, never part of the key or the id checksum. Omitted entirely when
+        not supplied, so every snapshot recorded before r4 stays byte-identical on disk."""
         existing = self.find_by_key(
             screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature
         )
@@ -1218,6 +1236,8 @@ class ScreenStore:
         }
         if screen_coverage_signature is not None:
             meta["screen_coverage_signature"] = screen_coverage_signature
+        if withheld_excluded is not None:
+            meta["withheld_excluded"] = withheld_excluded
         record = {"meta": meta}
         payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
         self._root.mkdir(parents=True, exist_ok=True)
diff --git a/apps/backend/app/research/desk_screen_compute.py b/apps/backend/app/research/desk_screen_compute.py
index 9618b3a..b3d78c1 100644
--- a/apps/backend/app/research/desk_screen_compute.py
+++ b/apps/backend/app/research/desk_screen_compute.py
@@ -287,6 +287,10 @@ def run_screen_and_record(
                 screen_coverage_signature=result["screen_coverage_signature"],
                 rows=result["rows"],
                 skipped=result["skipped"],
+                # Spec section 7.5 point 6 (r4): the screen's own disclosure of how many withheld
+                # vault shards were left out of its `tick_evidence` basis, recorded WITH the
+                # snapshot so a stored screen states the basis it was actually computed over.
+                withheld_excluded=result["withheld_excluded"],
             )
             # The replacement is on disk BEFORE its predecessors are removed, and the run is logged
             # `done` even if the prune itself raises (a full disk, a read-only dir): the snapshot
diff --git a/apps/backend/app/research/edge_report.py b/apps/backend/app/research/edge_report.py
index 65bec17..91867c8 100644
--- a/apps/backend/app/research/edge_report.py
+++ b/apps/backend/app/research/edge_report.py
@@ -81,6 +81,10 @@ from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, parse_utc_epoch
 # second time -- see ``edge_report_backtest_cache.py``'s own module docstring for the full "why").
 from .edge_report_backtest_cache import EdgeReportBacktestCache, pair_cache_key
 from .edge_report_cache import EdgeReportCache, _config_content_hash
+# Spec section 7.5 point 6 (r4, owner ruling): the ONE withholding predicate every corpus-wide
+# enumerator shares -- imported, never re-implemented here (a divergent second copy is exactly how
+# the iter-9 audit's B2 leak survived the route-level fix).
+from .micro_snapshots import exclude_withheld
 # ``_store_signature`` imported PRIVATE (the identical ``_aggregate`` precedent above, and the
 # phase plan's own explicit suggestion): the ONE bar-store-signature tuple shape ``setups.py``
 # already computes for its OWN scan cache, reused verbatim here rather than duplicated.
@@ -105,6 +109,16 @@ _ALL_STRATEGY_IDS: tuple[str, ...] = (STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY
 # datasets clear the positive-edge gate, including the true-empty-registry case.
 NO_POSITIVE_EDGE_FINDING = "no positive-edge dataset"
 
+# Spec section 7.5 point 6 (r4): "a run whose entire eligible corpus is withheld reports that
+# honestly rather than emitting an empty-but-shaped result". This finding replaces the
+# no-positive-edge one in exactly that case, so a reader can never mistake "every shard is sealed"
+# for "the champion was measured and showed no edge".
+FULLY_WITHHELD_FINDING = (
+    "no dataset was measured: every registered dataset is a withheld Validation-Vault shard "
+    "(spec section 7.5) -- this report measures nothing, rather than reporting an empty result "
+    "as if the corpus had been read"
+)
+
 # era-fast_wall J-01: the not-computed payload's own explanatory ``detail`` string (DoD: "a detail
 # naming the trigger") — ONE canonical literal, never restated inline at ``peek_strategy_
 # comparison_report``'s own call site.
@@ -134,26 +148,40 @@ class EdgeReportComputeCancelled(Exception):
 # --- reused computation: ONE backtest per dataset, via the EXISTING runner ----------------------
 
 
-def _verified_records(dataset_store: DatasetStore) -> list[dict]:
-    """Every registered dataset metadata row, checksum-verified (the ONE ``DatasetStore.list``
-    read). A file that fails integrity verification anywhere in the store aborts explicitly — a
-    partial report is a misleading report. Shared by ``_split_datasets`` (below, filtered to one
-    split) and ``peek_strategy_comparison_report`` (era-fast_wall J-01, which needs the FULL,
-    unfiltered registry to key the cache and report ``dataset_count``) — ONE list-and-verify call
-    site, never a second copy of this error-formatting."""
+def _verified_corpus(dataset_store: DatasetStore) -> tuple[list[dict], int]:
+    """``(records, withheld_excluded)`` — the ONE ``DatasetStore.list`` read this module makes,
+    checksum-verified and seal-filtered. A file that fails integrity verification anywhere in the
+    store aborts explicitly — a partial report is a misleading report.
+
+    **Spec section 7.5 point 6 (r4, owner ruling).** This is the module's single enumeration choke
+    point, so it is where the seal is honoured: a shard whose vault lifecycle has not reached
+    ``exposed`` is EXCLUDED (its events would otherwise be replayed by a backtest, and
+    ``backtests.py`` embeds the stored manifest verbatim into every persisted result, which
+    ``GET /research/backtests`` then serves and ``pnl_ledger`` copies into an append-only row —
+    the iter-9 re-audit's finding B2). The exclusion is never silent: the returned COUNT (never
+    the ids) is carried into every report body this module produces. Byte-identical to the
+    pre-r4 behaviour while nothing is sealed."""
     records, errors = dataset_store.list()
     if errors:
         raise EdgeReportError(
             f"{len(errors)} dataset file(s) failed integrity verification "
             f"({[e['file'] for e in errors]}) — the report stops with nothing written"
         )
-    return records
+    return exclude_withheld(records, dataset_store)
+
+
+def _verified_records(dataset_store: DatasetStore) -> list[dict]:
+    """``_verified_corpus``'s records half, for the callers that need no disclosure of their own
+    (``_eligible_datasets``' parallel pre-warm task set) — never a second list-and-verify."""
+    return _verified_corpus(dataset_store)[0]
 
 
-def _split_datasets(dataset_store: DatasetStore, split: str) -> list[dict]:
-    """Every registered dataset metadata row for ``split`` — see ``_verified_records`` for the
-    integrity discipline."""
-    return [r for r in _verified_records(dataset_store) if r["split"] == split]
+def _split_datasets(records: list[dict], split: str) -> list[dict]:
+    """One split's rows out of an ALREADY-verified, already-seal-filtered record list (never a
+    second ``DatasetStore.list()`` read of its own — both report builders below enumerate once
+    through ``_verified_corpus`` and slice in memory, so the disclosed ``withheld_excluded`` count
+    and the measured rows can never come from two different reads of the store)."""
+    return [r for r in records if r["split"] == split]
 
 
 def _run_backtest(
@@ -259,8 +287,9 @@ def run_edge_report(store: JournalStore, dataset_store: DatasetStore, config: Co
     champion = store.get_champion_pointer()
     jobs = BacktestJobManager(store, config)
 
-    train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
-    holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)
+    records, withheld_excluded = _verified_corpus(dataset_store)
+    train_datasets = _split_datasets(records, SPLIT_TRAIN)
+    holdout_datasets = _split_datasets(records, SPLIT_HOLDOUT)
 
     train_rows = _rank(
         [_dataset_row(jobs, store, dataset_store, ds, champion) for ds in train_datasets]
@@ -278,11 +307,14 @@ def run_edge_report(store: JournalStore, dataset_store: DatasetStore, config: Co
         if row["positive_edge"]:
             positive_edge_ids.append(row["dataset_id"])
 
-    finding = (
-        NO_POSITIVE_EDGE_FINDING
-        if not positive_edge_ids
-        else f"positive-edge dataset(s): {', '.join(positive_edge_ids)}"
-    )
+    if positive_edge_ids:
+        finding = f"positive-edge dataset(s): {', '.join(positive_edge_ids)}"
+    elif withheld_excluded and not records:
+        # r4: the whole eligible corpus was withheld — say so, rather than serving the
+        # indistinguishable "measured everything, found no edge" sentence.
+        finding = FULLY_WITHHELD_FINDING
+    else:
+        finding = NO_POSITIVE_EDGE_FINDING
 
     return {
         "register": REGISTER,
@@ -292,6 +324,9 @@ def run_edge_report(store: JournalStore, dataset_store: DatasetStore, config: Co
         "holdout": {"datasets": holdout_rows},
         "positive_edge_dataset_ids": positive_edge_ids,
         "finding": finding,
+        # Spec section 7.5 point 6 (r4): how many registered datasets this report did NOT measure
+        # because their vault shards are withheld — a count only, never an id.
+        "withheld_excluded": withheld_excluded,
     }
 
 
@@ -299,8 +334,8 @@ def run_edge_report(store: JournalStore, dataset_store: DatasetStore, config: Co
 # "edge-report cells") -- an ADDITIVE extension of THIS module, never a fork: reuses the ONE
 # ``BacktestJobManager.create`` + ``run_sync`` path above (``_run_backtest``, now threading
 # ``bar_store`` through, see its own docstring), the verbatim ``_aggregate`` trade-population
-# arithmetic (imported from ``backtests.py`` — never re-derived), and ``_split_datasets``' ONE
-# checksum-verified ``DatasetStore.list()`` read per split (a dataset failing integrity
+# arithmetic (imported from ``backtests.py`` — never re-derived), and ``_verified_corpus``' ONE
+# checksum-verified, seal-filtered ``DatasetStore.list()`` read (a dataset failing integrity
 # verification anywhere aborts the WHOLE report explicitly, same as ``run_edge_report`` above).
 # ``run_edge_report``/``main``/``_render_report`` and every helper above this comment stay
 # UNTOUCHED — the era-3 champion-only CLI's behaviour is byte-identical to before.
@@ -335,7 +370,7 @@ def _dataset_event(dataset_meta: dict, events: list[dict]) -> dict | None:
     ``setups._matching_dataset`` window-containment TEST, mirrored (numeric epoch comparison,
     inclusive both ends — the identical ``parse_utc_epoch`` discipline, never a lexicographic
     string compare) but in the OPPOSITE direction: given ONE already-verified dataset (from THIS
-    module's own ``_split_datasets`` read), scan the already-computed ``events`` list for a match,
+    module's own ``_verified_corpus`` read), scan the already-computed ``events`` list for a match,
     rather than re-opening a second ``DatasetStore.list()`` read the way ``_matching_dataset``
     itself does internally (which silently drops a corrupt file's error — inconsistent with this
     module's OWN all-or-nothing integrity discipline, so it is never called from here). Ties (more
@@ -873,7 +908,7 @@ def peek_strategy_comparison_report(
     ``registry.edge_report_compute.snapshot()`` — the SAME snapshot ``GET /research/edge-report/
     compute`` itself serves, so the two are byte-identical in shape by construction (one owner, one
     read, two callers)."""
-    records = _verified_records(dataset_store)
+    records, withheld_excluded = _verified_corpus(dataset_store)
     if not records:
         return _compute_strategy_comparison_report(store, dataset_store, bar_store, config)
     cached = cache.lookup(records, config)
@@ -885,6 +920,10 @@ def peek_strategy_comparison_report(
         "dataset_count": len(records),
         "register": REGISTER,
         "compute": compute,
+        # Spec section 7.5 point 6 (r4): `dataset_count` above is the SEAL-FILTERED registry the
+        # cache is keyed on, so the shards it leaves out are disclosed beside it rather than
+        # silently shrinking the stated basis.
+        "withheld_excluded": withheld_excluded,
     }
 
 
@@ -904,7 +943,7 @@ def _compute_strategy_comparison_report(
     called directly). Measures ``v1``, ``structure_tape``, and ``structure_tape_map`` over EVERY
     registered event-window dataset that resolves an owning, classified scan event, aggregated
     into per strategy x class x side x reaction x feed cells. Raises ``EdgeReportError`` for a
-    dishonest state (the identical ``_split_datasets`` integrity discipline ``run_edge_report``
+    dishonest state (the identical ``_verified_corpus`` integrity discipline ``run_edge_report``
     uses) — nothing is written by the CALLER in that case. Strictly read-only: promotes nothing,
     appends no ledger row, moves no champion pointer (see the module docstring).
 
@@ -928,8 +967,9 @@ def _compute_strategy_comparison_report(
     ``BacktestRunner``'s one-slot contract; byte-identical persisted reports, two of three
     full-engine replays removed)."""
     jobs = BacktestJobManager(store, config, reuse_replay_path=True)
-    train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
-    holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)
+    records, withheld_excluded = _verified_corpus(dataset_store)
+    train_datasets = _split_datasets(records, SPLIT_TRAIN)
+    holdout_datasets = _split_datasets(records, SPLIT_HOLDOUT)
 
     # ONE ``compute_setups`` call for the WHOLE report (audit B2 hot-path guard) — never per
     # dataset, never per split; reused for both the train and hold-out join below. Skipped
@@ -957,13 +997,24 @@ def _compute_strategy_comparison_report(
         reporter=reporter, should_abort=should_abort, run_pair=run_pair,
     )
 
-    return {
+    body = {
         "register": REGISTER,
         "pnl_min_sample_size": config.pnl_min_sample_size,
         "train": {"cells": train_cells},
         "holdout": {"cells": holdout_cells},
         "surviving_train_cells": _surviving_train_cells(train_cells, holdout_cells, config),
+        # Spec section 7.5 point 6 (r4): the count of registered datasets this sweep never
+        # measured because their vault shards are withheld — never the ids, never omitted.
+        "withheld_excluded": withheld_excluded,
     }
+    if withheld_excluded and not records:
+        # r4's "a run whose entire eligible corpus is withheld reports that honestly rather than
+        # emitting an empty-but-shaped result": an all-empty `cells` list is otherwise a LEGITIMATE
+        # degenerate outcome here (see this section's own comment block), so the distinguishing
+        # statement is carried explicitly rather than left to the reader's arithmetic. Present ONLY
+        # in that case — the honest-omission convention, never a fabricated `null`.
+        body["finding"] = FULLY_WITHHELD_FINDING
+    return body
 
 
 def _render_report(report: dict) -> str:
diff --git a/apps/backend/app/research/edge_report_cache.py b/apps/backend/app/research/edge_report_cache.py
index 8b48c66..1dc06c8 100644
--- a/apps/backend/app/research/edge_report_cache.py
+++ b/apps/backend/app/research/edge_report_cache.py
@@ -82,8 +82,17 @@ file that is NOT part of any previously-cached healthy subset coincidentally mat
 cached key and silently serving a result that never saw the corruption — never worth the risk for
 what is already the rare, explicit-failure path.
 
+**The key's corpus is SEAL-FILTERED (spec section 7.5 point 6, r4).** ``get_or_compute`` and
+``compute_and_publish`` derive their key from ``exclude_withheld(records, dataset_store)`` — the
+ONE withholding predicate ``edge_report._verified_corpus`` measures under and ``lookup``'s caller
+(``peek_strategy_comparison_report``) already passes in. Without this the two halves would key the
+SAME report under two different corpus views the moment a shard is sealed: the write half would
+publish under a key including the withheld shard, and every read would miss forever. Byte-identical
+while nothing is withheld, and a genuine re-key (a new sealed shard changes what the report
+measures, so it must change what the cache serves) once something is.
+
 **era-fast_wall J-01 additions — ``lookup``/``compute_and_publish`` beside ``get_or_compute``.**
-``get_or_compute`` stays UNTOUCHED (byte-identical, every one of its own tests unmodified). Two
+``get_or_compute`` keeps its J-01 behaviour (only the r4 key basis above changed). Two
 new methods split its "check cache, else compute" behaviour into its two named halves, for the
 interlude's headline "no compute on a GET, ever" anti-goal: ``lookup(records, config)`` is the
 READ-ONLY half (hot slot then durable row, returns ``None`` on a miss, NEVER calls a compute
@@ -110,6 +119,8 @@ from typing import Callable
 from ..config import Config
 from .algorithm_version import LEVELS_ALGORITHM_VERSION
 from .datasets import DatasetStore
+# Spec section 7.5 point 6 (r4): the ONE withholding predicate — imported, never re-implemented.
+from .micro_snapshots import exclude_withheld
 
 __all__ = ["EdgeReportCache", "resolve_cache_db_path"]
 
@@ -296,6 +307,10 @@ class EdgeReportCache:
         records, errors = dataset_store.list()
         if errors:
             return compute_fn()
+        # Spec section 7.5 point 6 (r4): key on the SEAL-FILTERED registry -- the identical basis
+        # `edge_report._verified_corpus` measures and `lookup`'s callers pass in, so the write and
+        # read halves of this cache can never key one report under two different corpus views.
+        records, _withheld_excluded = exclude_withheld(records, dataset_store)
         key = _cache_key(records, config)
 
         hot = self._hot  # read-local-reference-before-inspect
@@ -355,6 +370,10 @@ class EdgeReportCache:
         records, errors = dataset_store.list()
         if errors:
             return compute_fn()
+        # Spec section 7.5 point 6 (r4): key on the SEAL-FILTERED registry -- the identical basis
+        # `edge_report._verified_corpus` measures and `lookup`'s callers pass in, so the write and
+        # read halves of this cache can never key one report under two different corpus views.
+        records, _withheld_excluded = exclude_withheld(records, dataset_store)
         key = _cache_key(records, config)
 
         result = compute_fn()
diff --git a/apps/backend/app/research/micro_join.py b/apps/backend/app/research/micro_join.py
index 9d54966..5316940 100644
--- a/apps/backend/app/research/micro_join.py
+++ b/apps/backend/app/research/micro_join.py
@@ -85,7 +85,9 @@ from typing import TYPE_CHECKING, Sequence
 from . import micro_features as mf
 from .datasets import DatasetStore, parse_utc_epoch
 from .micro_accessor import MicroAccessor
-from .micro_snapshots import load_snapshot_meta
+# ``exclude_withheld``: spec section 7.5 point 6 (r4) -- the ONE withholding predicate every
+# corpus-wide enumerator shares, imported rather than re-implemented here.
+from .micro_snapshots import exclude_withheld, load_snapshot_meta
 
 if TYPE_CHECKING:  # pragma: no cover -- type-checking only, never a runtime import (no cycle risk)
     from ..config import Config
@@ -168,8 +170,14 @@ def _covering_dataset(symbol: str, at_epoch: float, records: Sequence[dict]) ->
 def find_covering_dataset(symbol: str, at_epoch: float, dataset_store: DatasetStore) -> dict | None:
     """The single-lookup convenience form of ``_covering_dataset`` -- lists the store fresh for
     THIS one call. A caller checking many instants against the SAME store (``joinable_corpus_
-    counts`` below) lists once and calls ``_covering_dataset`` directly instead."""
+    counts`` below) lists once and calls ``_covering_dataset`` directly instead.
+
+    Withheld Validation-Vault shards are excluded (spec section 7.5 point 6, r4): this lookup is
+    the door onto a covering SNAPSHOT and therefore onto a shard's rows, so a sealed shard covering
+    the instant is an honest ``None`` (the same answer this function already gives when no window
+    covers it) rather than a read of held-out tape."""
     records, _errors = dataset_store.list()
+    records, _withheld_excluded = exclude_withheld(records, dataset_store)
     return _covering_dataset(symbol, at_epoch, records)
 
 
@@ -515,8 +523,16 @@ def joinable_corpus_counts(dataset_store: DatasetStore, playbook_store) -> dict:
     record (``playbook_store.list()``'s own error half) is skipped from the count -- there is no
     signal content to read from a file that failed verification -- but is never silently dropped
     from the RESPONSE: it is surfaced verbatim in ``playbook_integrity_errors`` (module docstring's
-    iter-4 passenger fix)."""
+    iter-4 passenger fix).
+
+    **Withheld shards are excluded, and the exclusion is disclosed (spec section 7.5 point 6, r4;
+    iter-9 audit finding B5).** A dataset whose vault shard has not reached ``exposed`` is not
+    available evidence, so counting its window as joinable would make this number disagree with
+    ``micro_readiness``' own ``totals.distinct_datasets`` (which already excludes it) inside one
+    payload. ``withheld_excluded`` carries the COUNT -- never the ids -- so the shrink is never
+    silent. Byte-identical (``0``) while nothing is sealed."""
     records, _errors = dataset_store.list()
+    records, withheld_excluded = exclude_withheld(records, dataset_store)
     total_playbook = 0
     by_setup_id: dict[str, int] = {}
     playbook_records, playbook_errors = playbook_store.list()
@@ -542,4 +558,7 @@ def joinable_corpus_counts(dataset_store: DatasetStore, playbook_store) -> dict:
         "band_touch_count": _band_touch_not_enumerated(),
         "by_setup_id": by_setup_id,
         "playbook_integrity_errors": playbook_errors,
+        # Spec section 7.5 point 6 (r4): the count of registered datasets whose windows were NOT
+        # eligible to make a signal joinable, because their vault shards are withheld.
+        "withheld_excluded": withheld_excluded,
     }
diff --git a/apps/backend/app/research/micro_readiness.py b/apps/backend/app/research/micro_readiness.py
index 3caedbf..0e1a549 100644
--- a/apps/backend/app/research/micro_readiness.py
+++ b/apps/backend/app/research/micro_readiness.py
@@ -77,6 +77,7 @@ from ..providers.base import Event, QuoteEvent, TradeEvent
 from .datasets import DatasetStore
 from .micro_join import BAND_TOUCH_STATUS_NOT_ENUMERATED, joinable_corpus_counts
 from .referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
+from . import vault
 
 __all__ = [
     "WF_TRAIN_MIN_SESSIONS",
@@ -300,16 +301,58 @@ def build_readiness(
     ``playbook_store`` (J-03, ``desk_playbook.PlaybookStore``) is OPTIONAL and defaults to
     ``None`` -- callers that do not pass one (every pre-J-03 test in this file) get the honest
     ``joinable_corpus`` zero rather than an error, since "no playbook evidence was even checked"
-    is a true statement in that case, never a fabricated one."""
+    is a true statement in that case, never a fabricated one.
+
+    **Sealed-tranche AGGREGATES only (iter-9, spec section 7.5 point 4, r3).** A dataset whose
+    Validation-Vault shard has not yet reached ``exposed`` gets NO per-shard row and NO per-shard
+    ``exposure_state`` here -- its row would carry the symbol, session date and exact trade/quote
+    counts section 7.5 withholds, and the iter-9 audit's finding B1 demonstrated this table doing
+    exactly that. Such a shard is counted instead in ``sealed_tranche`` (shard count, distinct
+    symbol-days, per-universe totals -- section 7.5's own enumerated aggregate list) and is
+    excluded from ``totals``/``study_floors``, since sealed evidence is by construction not
+    available to any study. The exclusion also means this fold never LOADS a sealed shard's
+    events, so the ``fallback_frac`` walk below can never become an exploratory read of sealed
+    tape (the era's *(critical)* anti-goal). The vault is read through the SAME
+    ``vault.shard_ledger_for_dataset_dir(dataset_dir)`` resolution every other consumer uses --
+    one vault location, never a second. With nothing sealed, ``sealed_tranche`` is an all-zero
+    row and every other value in this payload is byte-identical to its pre-iter-9 self.
+
+    Membership is the VAULT's answer, never re-derived here; the arithmetic over it is this
+    module's own, exactly as it already is for ``totals`` (the ``joinable_corpus`` precedent, where
+    ``micro_join`` owns the count and this module owns nothing but its placement). ``sealed_tranche``
+    counts the withheld shards PRESENT IN THIS STORE -- a vault ledger row naming a dataset that no
+    longer sits in ``dataset_dir`` contributes nothing here, since this payload's whole subject is
+    what evidence exists on this disk."""
     records, errors = store.list()
     root = Path(dataset_dir)
+    withheld_universe_by_id = vault.withheld_universe_by_dataset_id(
+        vault.shard_ledger_for_dataset_dir(dataset_dir)
+    )
 
     shards: list[dict] = []
     symbol_days: set[tuple[str, str]] = set()
     session_dates: set[str] = set()
     rth_minutes_total = 0.0
+    sealed_symbol_days: set[tuple[str, str]] = set()
+    sealed_shard_count = 0
+    sealed_symbol_days_by_universe: dict[str, set[tuple[str, str]]] = {}
+    sealed_shard_count_by_universe: dict[str, int] = {}
 
     for meta in records:
+        if meta["id"] in withheld_universe_by_id:
+            # Section 7.5 point 4: aggregates only. Computed from the store's own metadata
+            # SERVER-side and never served per shard -- the payload below carries counts, never a
+            # symbol, a date, or an id.
+            universe_id = withheld_universe_by_id[meta["id"]]
+            symbol_day = (meta["symbol"], _et_datetime(meta["window_start_utc"]).date().isoformat())
+            sealed_shard_count += 1
+            sealed_symbol_days.add(symbol_day)
+            sealed_shard_count_by_universe[universe_id] = (
+                sealed_shard_count_by_universe.get(universe_id, 0) + 1
+            )
+            sealed_symbol_days_by_universe.setdefault(universe_id, set()).add(symbol_day)
+            continue
+
         start_et = _et_datetime(meta["window_start_utc"])
         end_et = _et_datetime(meta["window_end_utc"])
         session_date = start_et.date()
@@ -368,7 +411,10 @@ def build_readiness(
 
     totals = {
         "distinct_symbol_days": len(symbol_days),
-        "distinct_datasets": len(records),
+        # The EXPLORATORY inventory: `shards` above, one row each. A sealed shard is deliberately
+        # absent from both (spec section 7.5 point 4) -- it is neither available evidence nor a
+        # servable row -- and is counted in `sealed_tranche` below instead.
+        "distinct_datasets": len(shards),
         "rth_minutes_covered": round(rth_minutes_total, 2),
         "session_equivalents": round(rth_minutes_total / _RTH_MINUTES_PER_SESSION, 4),
         "referee_tick_gate_symbol_days": REFEREE_TICK_GATE_SYMBOL_DAYS,
@@ -390,14 +436,31 @@ def build_readiness(
             "band_touch_count": {"status": BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None},
             "by_setup_id": {},
             "playbook_integrity_errors": [],
+            # Spec section 7.5 point 6 (r4): a run that enumerated nothing excluded nothing --
+            # a true statement about THIS fallback, not a copy of the real count (which only
+            # `joinable_corpus_counts` below is entitled to compute).
+            "withheld_excluded": 0,
         }
     else:
         joinable_corpus = joinable_corpus_counts(store, playbook_store)
 
+    sealed_tranche = {
+        "shard_count": sealed_shard_count,
+        "symbol_days": len(sealed_symbol_days),
+        "by_universe": {
+            universe_id: {
+                "shard_count": sealed_shard_count_by_universe[universe_id],
+                "symbol_days": len(sealed_symbol_days_by_universe[universe_id]),
+            }
+            for universe_id in sorted(sealed_shard_count_by_universe)
+        },
+    }
+
     return {
         "totals": totals,
         "shards": shards,
         "study_floors": study_floors,
         "integrity_errors": errors,
         "joinable_corpus": joinable_corpus,
+        "sealed_tranche": sealed_tranche,
     }
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 7d72d7c..220a509 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -1,10 +1,16 @@
 """``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, J-02's three
-snapshot routes, J-04's Scout routes, and J-05's three walk-forward routes. A fresh router/file
-mounted separately in ``main.py``, mirroring ``referee_routes.py``'s own precedent and rationale
-(that file's own docstring: "the SAME rationale desk_routes.py itself gives for splitting off
-routes.py"). The era's own Data Contract table (``docs/goal.md``'s Product Shape) names THREE more
-micro routes landing in later iterations (vault, recorder, graduation) under this SAME
-``/research/desk/micro`` prefix -- a dedicated file is the right home from the start.
+snapshot routes, J-04's Scout routes, J-05's three walk-forward routes, J-06 step 2's recorder
+routes, and J-06 step 3's ONE read-only vault route. A fresh router/file mounted separately in
+``main.py``, mirroring ``referee_routes.py``'s own precedent and rationale (that file's own
+docstring: "the SAME rationale desk_routes.py itself gives for splitting off routes.py"). The
+era's own Data Contract table (``docs/goal.md``'s Product Shape) names ONE more micro route
+landing in a later iteration (graduation) under this SAME ``/research/desk/micro`` prefix -- a
+dedicated file is the right home from the start.
+
+``GET /vault`` is GET-only this iteration -- no ``/vault/compute`` route and no CLI (the phase
+spec's own OUT OF SCOPE: "no operator act in this iteration or the next calls registration
+standalone; that lands with step 4"), so it needs no compute manager and no ``POST``/cancel
+sibling routes, unlike the sections above it.
 
 Depends on stores this route does NOT own: the dataset store dependency is imported verbatim from
 ``routes.get_dataset_store``, the universe/bar-store dependencies from ``desk_routes.
@@ -50,6 +56,7 @@ from .tick_recorder import (
     resolve_tick_recorder_checkpoint_dir,
     resolve_tick_recorder_log_dir,
 )
+from . import vault
 from . import walkforward as wf
 from .walkforward_ledger import WalkForwardLedger
 
@@ -140,7 +147,11 @@ def get_micro_snapshots_compute(
     manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
 ) -> dict:
     """The current (or last-terminal) build job's progress -- never 404 (the ``_IDLE_SNAPSHOT``
-    default before any job has ever run this process)."""
+    default before any job has ever run this process).
+
+    ``withheld_excluded`` (spec section 7.5 point 6, r4) is this run's own disclosure of how many
+    Validation-Vault shards the build enumeration left out -- a COUNT only, never an id, and never
+    silently omitted. ``0`` whenever the vault holds nothing withheld, which is every run today."""
     snap = manager.snapshot()
     return {
         "state": snap["state"],
@@ -148,6 +159,7 @@ def get_micro_snapshots_compute(
         "started_utc": snap["started_utc"],
         "finished_utc": snap["finished_utc"],
         "error": snap["error"],
+        "withheld_excluded": snap["withheld_excluded"],
     }
 
 
@@ -493,3 +505,29 @@ def cancel_tick_recorder_compute(
 def get_tick_recorder_runs(run_log_dir: str = Depends(get_tick_recorder_log_dir)) -> dict:
     """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
     return {"runs": read_run_log(run_log_dir)}
+
+
+# --- J-06 step 3: the Validation Vault (vault.py) -- GET-only this iteration ------------------------
+
+
+def get_vault_dir() -> str:
+    """The vault's storage directory -- ``TAPEOLOGY_MICRO_VAULT_DIR`` if set, else a SIBLING of
+    the config-owned dataset directory (``vault.resolve_vault_dir`` -- see that function's own
+    docstring)."""
+    return vault.resolve_vault_dir(CONFIG.dataset_dir_resolved())
+
+
+@router.get("/vault")
+def get_vault(vault_dir: str = Depends(get_vault_dir)) -> dict:
+    """Serves ``vault.py``'s own state verbatim (``vault.build_vault_state`` -- no second
+    computation in this handler): every shard's CURRENT lifecycle state (opaque-only while
+    ``sealed``, full symbol/date/family provenance from ``assigned`` onward -- section 7.5, TR-2),
+    every registered universe (never the raw secret, only its commitment -- and, while any of that
+    universe's shards is still withheld, only its ``rule_hash``/sizes rather than the
+    ``symbol_rule``/``date_rule`` LISTS, since those minus the public dataset listing would spell
+    out the sealed tranche by subtraction: iter-9 audit third pass, ``vault._serialize_universe``),
+    and both ledgers' own chain-verification verdicts. Never 404/500 on an empty vault -- the desk
+    router's established never-404-on-absence convention: an honest empty ``shards``/``universes``
+    before any universe is ever registered (registration is a step-4, operator-attended act, out of THIS iteration's
+    scope)."""
+    return vault.build_vault_state(vault.VaultShardLedger(vault_dir), vault.VaultUniverseLedger(vault_dir))
diff --git a/apps/backend/app/research/micro_snapshots.py b/apps/backend/app/research/micro_snapshots.py
index 20db39a..f5de227 100644
--- a/apps/backend/app/research/micro_snapshots.py
+++ b/apps/backend/app/research/micro_snapshots.py
@@ -38,6 +38,7 @@ from typing import Callable
 from ..config import CONFIG, Config
 from . import micro_features as mf
 from . import micro_observer as mo
+from . import vault
 from .datasets import DatasetNotFound, DatasetStore
 from .micro_observer import MicroObserver, MicroObserverFailure
 
@@ -45,6 +46,8 @@ __all__ = [
     "SNAPSHOT_FORMAT_VERSION",
     "MicroSnapshotIntegrityError",
     "MicroObserverFailure",
+    "withheld_dataset_ids_for_store",
+    "exclude_withheld",
     "resolve_micro_snapshots_dir",
     "feature_source_hash",
     "snapshot_identity",
@@ -93,6 +96,46 @@ def resolve_micro_snapshots_dir(dataset_dir_resolved: str) -> str:
     return str(Path(dataset_dir_resolved).parent / "micro_snapshots")
 
 
+def withheld_dataset_ids_for_store(dataset_store: DatasetStore) -> frozenset[str]:
+    """Every dataset id whose Validation-Vault shard has not yet reached ``exposed`` (spec
+    section 7.5 point 3, r3), resolved through the ONE
+    ``vault.shard_ledger_for_dataset_dir`` resolver every other vault consumer shares --
+    keyed on THIS store's own directory, never ``CONFIG``'s, so a ``tmp_path``-scoped caller
+    never reads the operator's real vault.
+
+    Snapshot building is where a sealed shard's raw EVENTS would be replayed, and the snapshot
+    listing is where its ``dataset_id``/raw ``dataset_checksum``/``row_count``/``bytes_on_disk``
+    would be re-published -- exactly the identity, exact counts and bytes section 7.5 withholds
+    until exposure. Both are closed against this set (iter-9 audit finding B1): the era's
+    *(critical)* anti-goal is that a sealed shard's event data and outcome aggregates are
+    "refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure", and a
+    screening/feature pass over sealed tape would destroy the held-out property the vault exists
+    to create. Empty -- and therefore byte-identical to the pre-iter-9 behaviour -- until the
+    first shard is ever sealed."""
+    return vault.withheld_dataset_ids(vault.shard_ledger_for_dataset_dir(str(dataset_store.root)))
+
+
+def exclude_withheld(records: list[dict], dataset_store: DatasetStore) -> tuple[list[dict], int]:
+    """Spec section 7.5 point 6 (r4): the ONE exclusion-and-disclosure primitive every corpus-wide
+    enumerator shares. Returns ``(kept_records, withheld_excluded)`` -- the records whose shards
+    are servable, and the COUNT (never the ids) of the ones this run left out.
+
+    Owner ruling r4, stated as code: "a refusal wired only into a route is bypassed by any module
+    that enumerates the store itself", so every enumerator filters at its single
+    ``DatasetStore.list()`` choke point -- through THIS function, never a second predicate of its
+    own (a divergent copy is exactly how the iter-9 audit's B2 leak survived the route-level fix).
+    The count travels into the caller's report body and into any append-only row the run writes:
+    **silent exclusion is forbidden** -- these call sites already hold that "a partial report is a
+    misleading report", and the era's denominator rail forbids a corpus that shrinks without
+    saying so.
+
+    Zero-cost and byte-identical while nothing is sealed: an empty vault withholds nothing, so
+    ``kept is`` every record and the disclosed count is ``0``."""
+    withheld = withheld_dataset_ids_for_store(dataset_store)
+    kept = [record for record in records if record["id"] not in withheld]
+    return kept, len(records) - len(kept)
+
+
 _IDENTITY_SOURCE_MODULES = (mf, mo)
 
 
@@ -267,9 +310,17 @@ def list_snapshot_meta(root_dir: str, dataset_store: DatasetStore, config: Confi
     root = Path(root_dir)
     if not root.exists():
         return []
+    # Spec section 7.5 point 3 (r3), iter-9 audit B1: a withheld shard's meta carries its
+    # `dataset_id`, its RAW `dataset_checksum`, its exact `row_count` and `bytes_on_disk` -- the
+    # identity, counts and bytes withheld until exposure. Omitted here even if a snapshot file
+    # for it exists on disk (a shard sealed AFTER its snapshot was built), so the withholding is
+    # fail-closed rather than dependent on build order.
+    withheld = withheld_dataset_ids_for_store(dataset_store)
     out: list[dict] = []
     for meta_file in sorted(root.glob("*.meta.json")):
         dataset_id = meta_file.name[: -len(".meta.json")]
+        if dataset_id in withheld:
+            continue
         meta = load_snapshot_meta(root_dir, dataset_store, dataset_id, config)
         if meta is not None:
             out.append(meta)
@@ -297,6 +348,13 @@ def run_snapshot_build_and_record(
     if dataset_ids is None:
         records, _errors = dataset_store.list()
         dataset_ids = [r["id"] for r in records]
+    # Spec section 7.4/7.5 + the era's *(critical)* anti-goal, iter-9 audit B1: a sealed (or
+    # merely `assigned`) shard's raw events are NEVER replayed. Applied to an EXPLICITLY passed
+    # id list too, not only the default enumeration -- this is the one place snapshot rows are
+    # built, so it is the one place the guarantee can be fail-closed rather than dependent on
+    # every caller remembering to filter.
+    withheld = withheld_dataset_ids_for_store(dataset_store)
+    dataset_ids = [dataset_id for dataset_id in dataset_ids if dataset_id not in withheld]
     results: list[dict] = []
     for dataset_id in dataset_ids:
         if should_abort is not None and should_abort():
@@ -368,6 +426,9 @@ _IDLE_SNAPSHOT: dict = {
     "started_utc": None,
     "finished_utc": None,
     "error": None,
+    # Spec section 7.5 point 6 (r4): the disclosure of what this build left out. `0` on an idle
+    # manager is a true statement (no run has excluded anything yet), never a placeholder.
+    "withheld_excluded": 0,
 }
 
 
@@ -405,6 +466,17 @@ class MicroSnapshotComputeManager:
                 resolved_ids = [r["id"] for r in records]
             else:
                 resolved_ids = list(dataset_ids)
+            # iter-9 audit B1: the published progress block below carries
+            # `current_dataset_id`, so an unfiltered enumeration would serve a sealed shard's
+            # dataset id on `GET /snapshots/compute` for the duration of the run. Filtered here
+            # as well as in `run_snapshot_build_and_record` (which is authoritative for what is
+            # actually READ) so `datasets_total` counts what the walk will really do. The count
+            # of what was left out is DISCLOSED below and in this run's own append-only run-log
+            # row (spec section 7.5 point 6, r4) -- never silently dropped.
+            withheld = withheld_dataset_ids_for_store(dataset_store)
+            kept_ids = [dataset_id for dataset_id in resolved_ids if dataset_id not in withheld]
+            withheld_excluded = len(resolved_ids) - len(kept_ids)
+            resolved_ids = kept_ids
 
             run_id = uuid.uuid4().hex
             self._run_id = run_id
@@ -421,6 +493,7 @@ class MicroSnapshotComputeManager:
                 "started_utc": _iso_utc_now(),
                 "finished_utc": None,
                 "error": None,
+                "withheld_excluded": withheld_excluded,
             }
             published = dict(self._snapshot)
 
@@ -473,6 +546,9 @@ class MicroSnapshotComputeManager:
                 "datasets_done": current["progress"]["datasets_done"],
                 "datasets_total": current["progress"]["datasets_total"],
                 "error": error,
+                # Spec section 7.5 point 6 (r4): the append-only row this run writes discloses how
+                # many withheld shards the walk excluded -- the count only, never an id.
+                "withheld_excluded": current["withheld_excluded"],
             }
         append_run_log(root_dir, entry)
 
@@ -536,7 +612,13 @@ def main() -> int:
     results = run_snapshot_build_and_record(
         dataset_store, config, root_dir, dataset_ids, progress=_cli_progress_printer()
     )
-    print(f"snapshot build complete: {len(results)} dataset(s) processed; store={root_dir}")
+    # Spec section 7.5 point 6 (r4): what this run left out is stated, never silently dropped.
+    records, _errors = dataset_store.list()
+    _kept, withheld_excluded = exclude_withheld(records, dataset_store)
+    print(
+        f"snapshot build complete: {len(results)} dataset(s) processed "
+        f"({withheld_excluded} withheld vault shard(s) excluded); store={root_dir}"
+    )
     return 0
 
 
diff --git a/apps/backend/app/research/pnl_ledger.py b/apps/backend/app/research/pnl_ledger.py
index ab72b2b..21bceec 100644
--- a/apps/backend/app/research/pnl_ledger.py
+++ b/apps/backend/app/research/pnl_ledger.py
@@ -147,6 +147,7 @@ def append_validation_row(
     candidate_train_report_id: str,
     candidate_holdout_report_id: str,
     baseline: dict | None = None,
+    withheld_excluded: int | None = None,
 ) -> dict:
     """Compose and append ONE PnL-ledger row (row 32) at validation time — the single writer.
 
@@ -159,7 +160,14 @@ def append_validation_row(
     split); the shared provenance stamps (strategy id, profile, ``config_fingerprint``) must
     AGREE across the two reports — composing across mismatched stamps would pool across
     fingerprints, so it is an explicit refusal. Returns the appended payload (which the store now
-    serves verbatim). A duplicate enhancement id raises the store's ``DuplicateEnhancementError``."""
+    serves verbatim). A duplicate enhancement id raises the store's ``DuplicateEnhancementError``.
+
+    ``withheld_excluded`` (spec section 7.5 point 6, r4 — the sweep is its only caller today) is
+    the COUNT of registered datasets the writing run left out because their Validation-Vault
+    shards are withheld; it is stamped into ``provenance`` so an APPEND-ONLY row can never claim a
+    corpus its run never read. Never the ids. Omitted entirely when the caller passes nothing
+    (``pnl_baseline``'s founding seed) — the honest-omission convention this row already uses for
+    ``baseline``, and byte-identical to every row recorded before r4."""
     train = _completed_report(store, candidate_train_report_id, SPLIT_TRAIN)
     holdout = _completed_report(store, candidate_holdout_report_id, SPLIT_HOLDOUT)
     for stamp in ("strategy_id", "profile", "config_fingerprint"):
@@ -171,6 +179,15 @@ def append_validation_row(
                 f"was appended"
             )
     now = time.time()
+    provenance = {
+        "strategy_id": train["result"]["strategy_id"],
+        "profile": train["result"]["profile"],
+        "config_fingerprint": train["result"]["config_fingerprint"],
+        SPLIT_TRAIN: _split_provenance(train),
+        SPLIT_HOLDOUT: _split_provenance(holdout),
+    }
+    if withheld_excluded is not None:
+        provenance["withheld_excluded"] = withheld_excluded
     row = {
         "enhancement_id": enhancement_id,
         "title": title,
@@ -182,13 +199,7 @@ def append_validation_row(
             SPLIT_TRAIN: _split_measurement(train),
             SPLIT_HOLDOUT: _split_measurement(holdout),
         },
-        "provenance": {
-            "strategy_id": train["result"]["strategy_id"],
-            "profile": train["result"]["profile"],
-            "config_fingerprint": train["result"]["config_fingerprint"],
-            SPLIT_TRAIN: _split_provenance(train),
-            SPLIT_HOLDOUT: _split_provenance(holdout),
-        },
+        "provenance": provenance,
         "created_wall_ts": now,
         "created_utc": _iso_utc(now),
     }
diff --git a/apps/backend/app/research/pnl_scan.py b/apps/backend/app/research/pnl_scan.py
index df9902c..7169fab 100644
--- a/apps/backend/app/research/pnl_scan.py
+++ b/apps/backend/app/research/pnl_scan.py
@@ -146,6 +146,10 @@ from ..config import CONFIG, Config, PROFILE_DEFAULT
 from .backtests import BacktestJobManager, REGISTER, STATUS_DONE
 from .bars import BarStore
 from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
+# Spec section 7.5 point 6 (r4, owner ruling): the ONE withholding predicate every corpus-wide
+# enumerator shares -- imported, never re-implemented (a divergent second copy is exactly how the
+# iter-9 audit's B2 leak survived the route-level fix).
+from .micro_snapshots import exclude_withheld
 from .pnl_ledger import LedgerCompositionError, append_validation_row
 from .referee_adjudicate import REFEREE_GATE_VERSION, authorize_promotion, referee_parameters_hash
 from .referee_registry import CertificateStore, resolve_referee_registry_dir
@@ -170,6 +174,15 @@ BREAKTHROUGH_ANCHOR_CAVEAT = (
     "(see docs/goal.md iter-6 NOTES, audit item B1)."
 )
 
+# Spec section 7.5 point 6 (r4): the sentence a fully-withheld corpus carries, so an empty sweep
+# can never read as "every registered dataset was measured and nothing survived". Static and
+# config-independent, exactly like the caveat above, so byte-identical reruns are unaffected.
+FULLY_WITHHELD_CAVEAT = (
+    "no dataset was measured: every registered dataset is a withheld Validation-Vault shard "
+    "(spec section 7.5) -- this sweep measures nothing, rather than reporting an empty result as "
+    "if the corpus had been read."
+)
+
 
 class ScanError(Exception):
     """The sweep could not complete honestly — a dataset failed integrity verification, a
@@ -213,16 +226,33 @@ def _run_backtest(
     return payload["id"], final["result"]
 
 
-def _split_datasets(dataset_store: DatasetStore, split: str) -> list[dict]:
-    """Every registered dataset metadata row for ``split`` (checksum-verified on load, the ONE
-    ``DatasetStore.list`` read). A file that fails integrity verification anywhere in the store
-    aborts the whole sweep explicitly — a partial report is a misleading report."""
+def _verified_corpus(dataset_store: DatasetStore) -> tuple[list[dict], int]:
+    """``(records, withheld_excluded)`` — the ONE ``DatasetStore.list`` read this sweep makes,
+    checksum-verified and seal-filtered. A file that fails integrity verification anywhere in the
+    store aborts the whole sweep explicitly — a partial report is a misleading report.
+
+    **Spec section 7.5 point 6 (r4, owner ruling).** This module drives ``BacktestJobManager``
+    directly, so a route-level refusal never sees it: a withheld Validation-Vault shard (state
+    != ``exposed``) is excluded HERE, at the single enumeration choke point, or its events would
+    be replayed and its stored manifest (id + raw checksum + window + counts) would land verbatim
+    in every persisted backtest result and, on a promotion, in the APPEND-ONLY PnL ledger — the
+    iter-9 re-audit's finding B2. Excluding it silently is equally forbidden ("a partial report is
+    a misleading report", above), so the COUNT — never the ids — travels into this run's report
+    body and into the ledger row it may write. Byte-identical while nothing is sealed."""
     records, errors = dataset_store.list()
     if errors:
         raise ScanError(
             f"{len(errors)} dataset file(s) failed integrity verification "
             f"({[e['file'] for e in errors]}) — the sweep stops with nothing written"
         )
+    return exclude_withheld(records, dataset_store)
+
+
+def _split_datasets(records: list[dict], split: str) -> list[dict]:
+    """One split's rows out of an ALREADY-verified, already-seal-filtered record list (never a
+    second ``DatasetStore.list()`` read of its own — ``run_sweep`` enumerates once through
+    ``_verified_corpus`` and slices in memory, so the disclosed ``withheld_excluded`` count and
+    the measured rows can never come from two different reads of the store)."""
     return [r for r in records if r["split"] == split]
 
 
@@ -305,6 +335,7 @@ def _promote(
     train_rows: list[dict],
     holdout_rows: list[dict],
     certificate_store: CertificateStore,
+    withheld_excluded: int = 0,
 ) -> dict:
     """Promote a genuine hold-out survivor: append ONE PnL-ledger row (the EXISTING single
     writer) THEN move the persisted champion pointer — in that crash-safe order (see the module
@@ -322,7 +353,12 @@ def _promote(
     era-6 J-08: with EXACTLY one train/hold-out dataset registered, ``authorize_promotion`` is
     consulted BEFORE ``append_validation_row`` — a valid, candidate-specific Referee certificate
     is REQUIRED or nothing is written and nothing moves (fail closed; no bypass of any kind).
-    ``live_scan_context`` is built FRESH from this run's own values every call, never cached."""
+    ``live_scan_context`` is built FRESH from this run's own values every call, never cached.
+
+    ``withheld_excluded`` (spec section 7.5 point 6, r4) is this sweep's own count of registered
+    datasets it never measured because their vault shards are withheld — stamped into the
+    APPEND-ONLY ledger row's provenance so a permanently recorded promotion can never claim a
+    corpus it did not read. A count only; never an id."""
     if len(train_datasets) != 1 or len(holdout_datasets) != 1:
         return {
             "candidate_id": candidate_id,
@@ -372,6 +408,7 @@ def _promote(
             candidate_train_report_id=train_rows[0]["candidate_report_id"],
             candidate_holdout_report_id=holdout_rows[0]["candidate_report_id"],
             baseline=baseline,
+            withheld_excluded=withheld_excluded,
         )
     except (LedgerCompositionError, DuplicateEnhancementError) as exc:
         raise ScanError(
@@ -444,8 +481,9 @@ def run_sweep(
         candidates = [p for p in config.profile_registry() if not p["is_default"]]
         champion_strategy_id, champion_profile = champion["strategy_id"], champion["profile"]
 
-    train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
-    holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)
+    records, withheld_excluded = _verified_corpus(dataset_store)
+    train_datasets = _split_datasets(records, SPLIT_TRAIN)
+    holdout_datasets = _split_datasets(records, SPLIT_HOLDOUT)
 
     champion_train: list[tuple[str, dict]] = []
     champion_holdout: list[tuple[str, dict]] = []
@@ -532,8 +570,17 @@ def run_sweep(
                 train_rows=train_rows,
                 holdout_rows=holdout_rows,
                 certificate_store=certificate_store,
+                withheld_excluded=withheld_excluded,
             )
 
+    # r4's "a run whose entire eligible corpus is withheld reports that honestly rather than
+    # emitting an empty-but-shaped result": an all-empty sweep is otherwise indistinguishable from
+    # a genuinely empty registry, so the reason is stated. Static text, so byte-identical reruns
+    # are unaffected.
+    assumptions = [BREAKTHROUGH_ANCHOR_CAVEAT]
+    if withheld_excluded and not records:
+        assumptions.append(FULLY_WITHHELD_CAVEAT)
+
     return {
         "register": REGISTER,
         "promotion_min_sample_size": config.promotion_min_sample_size,
@@ -541,9 +588,12 @@ def run_sweep(
         "champion_after": store.get_champion_pointer(),
         "candidates": candidate_entries,
         "promotion": promotion,
+        # Spec section 7.5 point 6 (r4): how many registered datasets this sweep never measured
+        # because their vault shards are withheld — a count only, never an id.
+        "withheld_excluded": withheld_excluded,
         # era-4 J-06 (audit item B1): disclosed, never re-armed this iteration — see the constant's
         # own docstring. Static and config-independent, so it never perturbs byte-identical reruns.
-        "provenance": {"assumptions": [BREAKTHROUGH_ANCHOR_CAVEAT]},
+        "provenance": {"assumptions": assumptions},
     }
 
 
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 98b5c30..031dd20 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -79,6 +79,7 @@ from .strategies import strategies_projection
 from .feed_basis import data_feed_for_scenario
 from .store import JournalStore
 from .taxonomy import taxonomy_payload
+from . import vault
 
 router = APIRouter(prefix="/research", tags=["research"])
 
@@ -390,20 +391,62 @@ def record_dataset(
     return {"dataset": meta}
 
 
+def get_withheld_dataset_ids() -> frozenset[str]:
+    """The dataset ids whose Validation-Vault shard has not yet reached ``exposed``
+    (``vault.withheld_dataset_ids`` — spec §7.5 point 3, r3). A FastAPI dependency resolved through
+    the SAME `TAPEOLOGY_MICRO_VAULT_DIR`-or-sibling-of-the-dataset-dir path every other vault
+    consumer uses (`vault.shard_ledger_for_dataset_dir`), so there is exactly one answer to "which
+    shards are sealed" in the process, and tests can override it outright.
+
+    Empty — and therefore a provable no-op for every existing behaviour — until the first shard is
+    ever sealed."""
+    return vault.withheld_dataset_ids(
+        vault.shard_ledger_for_dataset_dir(CONFIG.dataset_dir_resolved())
+    )
+
+
 @router.get("/datasets")
-def list_datasets(store: DatasetStore = Depends(get_dataset_store)) -> dict:
+def list_datasets(
+    store: DatasetStore = Depends(get_dataset_store),
+    withheld_ids: frozenset[str] = Depends(get_withheld_dataset_ids),
+) -> dict:
     """List every registered dataset's metadata (each file checksum-verified on load), oldest
     first. A file that fails verification is surfaced EXPLICITLY in ``integrity_errors`` — never
-    silently hidden, never served as data. The MCP ``datasets`` tool proxies this byte-for-byte."""
+    silently hidden, never served as data. The MCP ``datasets`` tool proxies this byte-for-byte.
+
+    Sealed-shard withholding (spec §7.5 point 3, r3): a dataset whose vault shard has not yet
+    reached ``exposed`` is OMITTED from ``datasets`` — its manifest carries the symbol, session
+    window and exact event counts §7.5 withholds, and this listing is the join surface the iter-9
+    audit's finding B1 demonstrated. The omission is DISCLOSED, never silent: ``sealed_withheld``
+    counts how many stored datasets were withheld, so a reader can always tell "nothing recorded"
+    from "recorded and sealed". The count alone reveals no shard identity, and the shards
+    themselves are served — opaquely — by their own canonical endpoint,
+    ``GET /research/desk/micro/vault``."""
     records, errors = store.list()
-    return {"datasets": records, "integrity_errors": errors}
+    served = [meta for meta in records if meta["id"] not in withheld_ids]
+    return {
+        "datasets": served,
+        "integrity_errors": errors,
+        "sealed_withheld": len(records) - len(served),
+    }
 
 
 @router.get("/datasets/{dataset_id}")
-def get_dataset(dataset_id: str, store: DatasetStore = Depends(get_dataset_store)) -> dict:
+def get_dataset(
+    dataset_id: str,
+    store: DatasetStore = Depends(get_dataset_store),
+    withheld_ids: frozenset[str] = Depends(get_withheld_dataset_ids),
+) -> dict:
     """One dataset's stored metadata, verbatim (checksum-verified on load). 404 for an unknown
     id; an explicit 500 integrity error for a corrupted/tampered file (never a fabricated
-    dataset)."""
+    dataset); and — spec §7.5 point 3 (r3) — a typed 403 refusal for a dataset whose vault shard
+    has not yet reached ``exposed``, checked BEFORE the file is even opened (fail-closed). The
+    refusal states only that the id is sealed: never the symbol, window, counts, or universe
+    (``vault.SealedShardWithheldError`` owns the single wording)."""
+    if dataset_id in withheld_ids:
+        raise HTTPException(
+            status_code=403, detail=str(vault.SealedShardWithheldError(dataset_id))
+        )
     try:
         meta = store.get(dataset_id)
     except DatasetNotFound:
@@ -1095,6 +1138,7 @@ def create_backtest(
     registry: ResearchRegistry = Depends(get_registry),
     store: DatasetStore = Depends(get_dataset_store),
     bar_store: BarStore = Depends(get_bar_store),
+    withheld_ids: frozenset[str] = Depends(get_withheld_dataset_ids),
 ) -> dict:
     """Create + START a deterministic backtest job (J-03; era-4 J-04 adds the additive
     ``structure_tape`` strategy) over one registered dataset under ``default`` or a registered
@@ -1123,6 +1167,16 @@ def create_backtest(
             status_code=422,
             detail=f"unknown profile '{body.profile}' — the registered profiles are {known}",
         )
+    # 403 — a sealed shard is never READ (spec §7.5/§7.4 and the era's own *(critical)* anti-goal:
+    # "Event data and outcome aggregates of a `sealed` shard are refused everywhere ... fail-
+    # closed"). A backtest is exactly an outcome aggregate over a dataset's events, and its
+    # RESULT re-publishes the dataset's full manifest through `GET /research/backtests` and
+    # `GET /research/pnl/ledger` — so this refusal is what keeps those two surfaces provably clean
+    # for a sealed shard (TR-2's sweep asserts both). Checked before the dataset is even opened.
+    if body.dataset_id in withheld_ids:
+        raise HTTPException(
+            status_code=403, detail=str(vault.SealedShardWithheldError(body.dataset_id))
+        )
     # 404-style — the dataset must exist (a checksum-verified load; never a fabricated dataset).
     try:
         store.get(body.dataset_id)
diff --git a/apps/backend/app/research/scout.py b/apps/backend/app/research/scout.py
index 5c4c748..b7940db 100644
--- a/apps/backend/app/research/scout.py
+++ b/apps/backend/app/research/scout.py
@@ -82,6 +82,7 @@ from .datasets import DatasetNotFound, DatasetStore, parse_utc_epoch
 from .micro_accessor import MicroAccessor
 from .micro_snapshots import (
     append_run_log,
+    exclude_withheld,
     load_snapshot_meta,
     resolve_micro_snapshots_dir,
     run_snapshot_build_and_record,
@@ -1053,6 +1054,7 @@ def register_and_screen_candidate(
     econ_floor_computed_at: str | None = None,
     family_median_spread_bps: float | None = None,
     rows_cache: dict[str, list[dict]] | None = None,
+    withheld_excluded: int = 0,
 ) -> dict:
     """The ONE production entry point: builds the frozen spec, enforces TR-9 (ordering) and the
     24-variant grid bound BEFORE any outcome is read or any ledger row is written, extracts
@@ -1155,6 +1157,11 @@ def register_and_screen_candidate(
         "notes": result["notes"],
         "screen_result": result["screen_result"],
         "superseded_by": None,
+        # Spec section 7.5 point 6 (r4): how many registered datasets this candidate's corpus
+        # manifest left out because their vault shards are withheld -- a count, never an id, and
+        # deliberately OUTSIDE ``spec_fields`` (which ``compute_spec_hash`` hashes), so disclosing
+        # it re-keys no ``spec_hash`` and no ``candidate_id``, and no already-recorded row moves.
+        "withheld_excluded": withheld_excluded,
     }
     return ledger.append_row(row_fields)
 
@@ -1190,7 +1197,21 @@ def default_fixture_grid(dataset_store: DatasetStore, *, grid_version: int = 1)
     ``dataset_store`` currently holds -- reused unmodified by the manager, the CLI, and the test
     suite's manager/CLI-parity check (TC-11)."""
     records, _errors = dataset_store.list()
-    corpus_manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]
+    # Spec section 7.4/7.5 (r3) + the era's *(critical)* anti-goal, iter-9 audit finding B1: a
+    # shard whose vault lifecycle has not reached ``exposed`` is excluded from the corpus
+    # manifest. Two distinct reasons, both fatal without this line: (1) the manifest is written
+    # VERBATIM into the append-only, hash-chained scout ledger and served by
+    # ``GET /research/desk/micro/scout``, so a sealed shard's ``dataset_id`` and RAW ``checksum``
+    # -- precisely the two join keys section 7.5 withholds until exposure -- would be published
+    # irreversibly; and (2) screening a sealed shard would READ its snapshot rows and fold its
+    # outcomes into an exploratory statistic, destroying the held-out property the whole vault
+    # exists to create. Empty (hence byte-identical) until the first shard is ever sealed.
+    # Spec section 7.5 point 6 (r4): the exclusion is DISCLOSED as a count on every row this grid
+    # writes (``register_and_screen_candidate``'s ``withheld_excluded``, carried OUTSIDE the frozen
+    # spec fields so no ``spec_hash``/``candidate_id`` re-keys) -- silent shrinking of a screened
+    # corpus is exactly what the era's denominator rail forbids.
+    kept, withheld_excluded = exclude_withheld(records, dataset_store)
+    corpus_manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in kept]
     requests: list[dict] = []
     for feature_name, horizon_key in DEFAULT_GRID_FEATURES:
         for op, value in DEFAULT_GRID_THRESHOLDS:
@@ -1205,6 +1226,7 @@ def default_fixture_grid(dataset_store: DatasetStore, *, grid_version: int = 1)
                     "fitting_rule": None,
                     "corpus_manifest": corpus_manifest,
                     "grid_version": grid_version,
+                    "withheld_excluded": withheld_excluded,
                 }
             )
     return requests
diff --git a/apps/backend/app/research/setups.py b/apps/backend/app/research/setups.py
index e435f48..e5c438e 100644
--- a/apps/backend/app/research/setups.py
+++ b/apps/backend/app/research/setups.py
@@ -137,6 +137,8 @@ from ..providers.adapters.base import RawBar
 from .bars import BarStore
 from .datasets import DatasetStore, parse_utc_epoch
 from .edge_report_cache import _config_content_hash
+# Spec section 7.5 point 6 (r4): the ONE withholding predicate, imported not re-implemented.
+from .micro_snapshots import exclude_withheld
 from .setups_scan_cache import SetupsScanCache, resolve_scan_cache_db_path, scan_cache_key
 from .tradability import RESISTANCE, SUPPORT, compute_tradability
 
@@ -516,6 +518,13 @@ def _matching_dataset(symbol: str, touch_ts: str, dataset_store: DatasetStore) -
     then ``id`` -- deterministic, never insertion-order happenstance."""
     touch_epoch = parse_utc_epoch(touch_ts)
     records, _errors = dataset_store.list()
+    # Spec section 7.5 point 6 (r4): this lookup's caller REPLAYS the matched dataset's raw events
+    # into a served drill-in timeline, so a withheld Validation-Vault shard is excluded here -- the
+    # drill-in then carries its existing, honest "no recorded dataset matches" empty timeline
+    # rather than a read of held-out tape (the era's *(critical)* anti-goal: a sealed shard's event
+    # data is refused everywhere until its recorded exposure). Byte-identical while nothing is
+    # sealed.
+    records, _withheld_excluded = exclude_withheld(records, dataset_store)
     candidates = [
         r for r in records
         if r["symbol"] == symbol
diff --git a/apps/backend/app/research/tick_recorder.py b/apps/backend/app/research/tick_recorder.py
index f110d45..912d34a 100644
--- a/apps/backend/app/research/tick_recorder.py
+++ b/apps/backend/app/research/tick_recorder.py
@@ -42,7 +42,12 @@ constant ``micro_features.py``'s own docstring reserves for this module) and
 ``quote_size_unit_for_session_date`` implement the frozen rule verbatim: Alpaca CTA/UTP displayed
 quote sizes are SHARES for sessions on/after ``2025-11-03``, ROUND LOTS before -- validated (by
 ``DatasetStore.record`` itself) against the single existing ``micro_features.QUOTE_SIZE_UNITS``
-tuple, never a second vocabulary.
+tuple, never a second vocabulary. J-06 step 3 closes section 2.6's own remaining clause ("the
+recorder records the rule text and the verification note beside the stamp"): ``_finalize_day``
+now also passes ``QUOTE_SIZE_UNIT_RULE_TEXT`` (the one frozen sentence, verbatim on every dataset)
+and ``quote_size_unit_verification_note(session_date)`` (a genuinely per-dataset note naming the
+actual comparison) to ``record_from_source`` -- two further optional, checksum-excluded manifest
+siblings of ``quote_size_unit`` (``datasets.py``'s own docstring covers the exclusion).
 
 **The split rule (spec section 7.3, Card 5.2 -- published, frozen, NOT this module's invention).**
 ``DatasetStore.record`` requires a split tag; ``recorder_split_for`` computes the EXISTING published
@@ -113,10 +118,12 @@ __all__ = [
     "RecorderPreservationCapabilityMissing",
     "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE",
     "RECORDER_SCHEMA_BASIS",
+    "QUOTE_SIZE_UNIT_RULE_TEXT",
     "RECORDER_PAGE_BUDGET_PER_MINUTE",
     "RECORDER_CHUNK_SECONDS",
     "verify_preservation_capability",
     "quote_size_unit_for_session_date",
+    "quote_size_unit_verification_note",
     "recorder_split_for",
     "plan_recorder_chunks",
     "RecorderCheckpointStore",
@@ -171,6 +178,15 @@ ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE = "2025-11-03"
 # writes ships WITH the fields (TR-19 refuses otherwise), so there is exactly one basis value.
 RECORDER_SCHEMA_BASIS = "tick_recorder_v1_card_5_1_preservation_present"
 
+# J-06 step 3 (spec section 2.6's own closing clause): "the recorder records the rule text ... "
+# -- the FROZEN vendor-rule sentence verbatim, stamped beside every `quote_size_unit` this module
+# writes. Composed FROM `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` (never a second, independently-typed
+# date literal) so the two constants can never drift apart.
+QUOTE_SIZE_UNIT_RULE_TEXT = (
+    "Alpaca CTA/UTP displayed quote sizes are SHARES for windows on/after "
+    f"{ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE}, ROUND LOTS before."
+)
+
 
 def quote_size_unit_for_session_date(session_date: str) -> str:
     """Stamps ``quote_size_unit`` per the dated Alpaca CTA/UTP vendor rule (spec section 2.6):
@@ -184,6 +200,23 @@ def quote_size_unit_for_session_date(session_date: str) -> str:
     return unit
 
 
+def quote_size_unit_verification_note(session_date: str) -> str:
+    """J-06 step 3 (spec section 2.6's own closing clause): "... and the verification note beside
+    the stamp" -- names the ACTUAL comparison (``session_date`` against
+    ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE``) and constant that produced THIS dataset's specific
+    ``quote_size_unit`` stamp, so the note is genuinely per-dataset and auditable rather than one
+    frozen sentence repeated regardless of which side of the date a given recording fell on
+    (``QUOTE_SIZE_UNIT_RULE_TEXT`` above is that one frozen sentence; this is its per-call
+    companion)."""
+    comparison = ">=" if session_date >= ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE else "<"
+    resolved_unit = quote_size_unit_for_session_date(session_date)
+    return (
+        f"verified by comparing this recording's session_date ({session_date!r}) {comparison} "
+        f"ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE ({ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE!r}) -> "
+        f"quote_size_unit={resolved_unit!r}"
+    )
+
+
 # --- spec section 7.3: the published sha256 split rule (Card 5.2, frozen, unchanged) --------------
 
 
@@ -376,7 +409,16 @@ def _existing_dataset_for_day(
     """Whether a dataset already covers this EXACT (symbol, day-window) -- the day-level
     short-circuit (TC-3): checked BEFORE any chunk of the day is even looked at, so a
     fully-recorded day costs zero ``DatasetStore.record`` calls, zero vendor calls, and zero
-    checkpoint reads."""
+    checkpoint reads.
+
+    **This enumeration deliberately does NOT apply the spec section 7.5 point 6 (r4) seal filter,
+    and must never be "fixed" to.** r4 makes corpus-wide enumerators exclude withheld shards
+    because they READ or REPUBLISH evidence; this one does neither -- it is the recorder's own
+    idempotency check, and its whole job is to answer "have I already written this day". Hiding a
+    sealed shard here would make the recorder re-fetch and re-record a day it already holds,
+    duplicating an immutable recording (and burning credentialed vendor calls) precisely for the
+    tranche the vault exists to protect. Nothing is served or measured from this answer: the caller
+    either skips the day or records it."""
     records, _errors = dataset_store.list()
     for meta in records:
         if (
@@ -439,6 +481,8 @@ def _finalize_day(
             historical_fetch=lambda: assembled,
             schema_basis=RECORDER_SCHEMA_BASIS,
             quote_size_unit=quote_size_unit_for_session_date(session_date),
+            quote_size_unit_rule_text=QUOTE_SIZE_UNIT_RULE_TEXT,
+            quote_size_unit_verification_note=quote_size_unit_verification_note(session_date),
         )
     except DatasetAlreadyRegistered as exc:
         return exc.existing_id, "unchanged"
diff --git a/apps/backend/app/research/walkforward.py b/apps/backend/app/research/walkforward.py
index 9587311..08474b3 100644
--- a/apps/backend/app/research/walkforward.py
+++ b/apps/backend/app/research/walkforward.py
@@ -69,7 +69,8 @@ from .micro_accessor import (
     resolve_micro_exposure_registry_dir,
 )
 from .micro_readiness import WF_TEST_MIN_SESSIONS, WF_TRAIN_MIN_SESSIONS
-from .micro_snapshots import append_run_log
+from .micro_snapshots import append_run_log, exclude_withheld
+from . import vault
 from .walkforward_ledger import (
     ROW_KIND_FOLD_RESULT,
     ROW_KIND_FOLD_SPEC,
@@ -982,7 +983,9 @@ TICK_LEGACY_CORPUS_ID = "tick_legacy_symbol_days_v1"
 _ET_ZONE = ZoneInfo("America/New_York")
 
 
-def _tick_dataset_session_dates(dataset_store: DatasetStore) -> tuple[list[str], list[dict]]:
+def _tick_dataset_session_dates(
+    dataset_store: DatasetStore, *, excluded_dataset_ids: frozenset[str] = frozenset()
+) -> tuple[list[str], list[dict]]:
     """Every currently-registered tick dataset's own ET session date (spec section 0: "a session
     is an ET RTH trading date"), one entry per DISTINCT date -- the SAME ET-conversion technique
     ``micro_readiness.py``'s own ``_et_datetime`` and ``micro_accessor.py``'s own
@@ -999,10 +1002,40 @@ def _tick_dataset_session_dates(dataset_store: DatasetStore) -> tuple[list[str],
     bound it to ``_errors`` and dropped it), so a damaged tick recording is REPORTED rather than
     quietly excluded from the known-session-dates count. The healthy records' dates are computed
     exactly as before; a corrupt file simply contributes no date (its own session, if any, is
-    honestly absent from the count) while every other healthy shard is unaffected."""
+    honestly absent from the count) while every other healthy shard is unaffected.
+
+    ``excluded_dataset_ids`` (iter-9, additive and default-empty -- byte-identical for a caller
+    that passes nothing): any dataset whose own ``id`` is in this set contributes NO session date
+    at all. The two production callers deliberately pass DIFFERENT predicates, and the parameter is
+    named for what it does rather than for either one (T-2 vocabulary discipline):
+
+      * ``run_diagnostic_walkforward``'s r2 seed passes ``vault.currently_sealed_dataset_ids`` --
+        strictly ``sealed``, because ASSIGNMENT is itself the recorded act that makes a shard's
+        window legitimately seedable (closes the latent hole named in the iter-9 spec's
+        BACKGROUND);
+      * ``run_tick_family_fold_request``'s corpus INVENTORY passes the wider
+        ``micro_snapshots.exclude_withheld`` set (state != ``exposed``), because spec section 7.5
+        point 6 (r4) requires every corpus-wide enumerator to exclude withheld shards from what it
+        counts and hashes (iter-9 audit finding B4).
+
+    **The filter's real granularity, stated exactly (iter-9 audit finding B4).** This registry's
+    unit is the DATE, not the dataset: an entry says "this corpus's window ``2026-06-09`` has been
+    served", with no dataset id in it. So the filter's guarantee is precisely "a sealed dataset
+    contributes no date of its OWN", which equals "the sealed shard's date carries no entry" only
+    when that date is unique to sealed datasets. A date shared with an UNSEALED sibling still gets
+    seeded via that sibling's own contribution -- and in a realistic tranche (many symbols per
+    date) most dates will have such a sibling, so most sealed shards' dates WILL be seeded as
+    exposed. Do not read this filter as "a sealed shard's window is provably unexposed" in
+    general. That is acceptable only because these entries are scoped to
+    ``TICK_LEGACY_CORPUS_ID``, under which a sealed shard must never be evaluated at all (spec
+    section 7.7: the legacy corpus is permanently exploratory and disjoint from any sealed
+    tranche); the vault's OWN shard-lifecycle ledger, not this one, is the authority on whether a
+    sealed shard has been exposed."""
     records, errors = dataset_store.list()
     session_dates: set[str] = set()
     for meta in records:
+        if meta["id"] in excluded_dataset_ids:
+            continue
         parsed = datetime.fromisoformat(meta["window_start_utc"].replace("Z", "+00:00"))
         if parsed.tzinfo is None:
             parsed = parsed.replace(tzinfo=timezone.utc)
@@ -1046,14 +1079,38 @@ def run_tick_family_fold_request(ledger: WalkForwardLedger, config: Config) -> d
     recording is reported to this function's caller rather than quietly excluded from the
     known-session-dates count."""
     tick_dataset_store = DatasetStore(config.dataset_dir_resolved())
-    session_dates, errors = _tick_dataset_session_dates(tick_dataset_store)
+    # Spec section 7.5 point 6 (r4) + iter-9 audit finding B4: this inventory is a corpus-wide
+    # enumerator, so a withheld shard must not contribute its session date to `TICK_LEGACY_CORPUS_
+    # ID`'s floor count or to the `corpus_manifest_hash` registered in the fold ledger -- section
+    # 7.7 makes the legacy corpus permanently exploratory and disjoint from any sealed tranche, so
+    # a sealed shard silently inflating it is exactly the "code path that has never heard of
+    # sealing" this era set out to close. The count is DISCLOSED in the returned body below (never
+    # the ids). Wider than the r2 seed's `sealed`-only filter on purpose -- see
+    # `_tick_dataset_session_dates`' own docstring for why the two callers differ.
+    records, _list_errors = tick_dataset_store.list()
+    kept, withheld_excluded = exclude_withheld(records, tick_dataset_store)
+    excluded_ids = frozenset(r["id"] for r in records) - frozenset(k["id"] for k in kept)
+    session_dates, errors = _tick_dataset_session_dates(
+        tick_dataset_store, excluded_dataset_ids=excluded_ids
+    )
     corpus_manifest_hash = _sha256(_canonical(session_dates))
     floors = {
         "wf_fold_min_observations": WF_FOLD_MIN_OBSERVATIONS,
         "wf_fold_min_signal_sessions": WF_FOLD_MIN_SIGNAL_SESSIONS,
         "wf_fold_min_symbols": WF_FOLD_MIN_SYMBOLS,
     }
-    require_sufficient_sessions_for_folds(session_dates, DIAGNOSTIC_GEOMETRY)
+    try:
+        require_sufficient_sessions_for_folds(session_dates, DIAGNOSTIC_GEOMETRY)
+    except InsufficientSessionsForFoldsError as exc:
+        if not withheld_excluded:
+            raise  # byte-identical to the pre-r4 refusal whenever nothing was withheld
+        # Spec section 7.5 point 6 (r4): a below-floor caller only ever SEES this refusal, so the
+        # disclosure has to travel with it -- otherwise the shortfall it names would silently
+        # reflect a corpus this run quietly shrank. A count, never an id.
+        raise InsufficientSessionsForFoldsError(
+            f"{exc} (this count excludes {withheld_excluded} withheld Validation-Vault shard(s), "
+            "spec section 7.5 point 6)"
+        ) from exc
     # Reached only by a corpus that genuinely clears the floor -- registers exactly as the
     # pre-iter-8 ordering did for this same case (idempotent on repeat calls via
     # `register_fold_spec`'s own "identical geometry replays the existing row" contract).
@@ -1065,6 +1122,13 @@ def run_tick_family_fold_request(ledger: WalkForwardLedger, config: Config) -> d
         "corpus_id": TICK_LEGACY_CORPUS_ID,
         "session_count": len(session_dates),
         "integrity_errors": errors,
+        # Spec section 7.5 point 6 (r4): how many registered datasets this inventory excluded
+        # because their vault shards are withheld -- a count, never an id. Deliberately NOT
+        # stamped into `register_fold_spec`'s row: that row is idempotent on `geometry_hash`
+        # alone, so a per-RUN count stored there would be frozen at whatever the first
+        # above-floor run happened to see and silently replayed as fact forever. The honest home
+        # for a per-run number is this per-run body.
+        "withheld_excluded": withheld_excluded,
     }
 
 
@@ -1193,11 +1257,23 @@ def run_diagnostic_walkforward(
     # entry point -- never a GET route (era Non-Goal: "No scheduling").
     if not has_any_exposure_entries(exposure_registry, TICK_LEGACY_CORPUS_ID):
         tick_dataset_store = DatasetStore(config.dataset_dir_resolved())
+        # iter-9 (closes the known latent hole the iter-9 spec's BACKGROUND names): before this
+        # seed reaches `initialize_r2_exposure_registry`, exclude any dataset id `vault.py`
+        # currently reports `sealed` -- read via the SAME sibling-of-the-dataset-dir resolution
+        # every other TAPEOLOGY_MICRO_* store uses (`vault.resolve_vault_dir`), so a freshly
+        # sealed shard can never be marked "already exposed" by a code path that has never heard
+        # of sealing (T-2: `vault.py`'s OWN shard-lifecycle ledger is a DIFFERENT ledger from this
+        # WALKFORWARD exposure registry -- this is the one, deliberate bridge between them).
+        sealed_dataset_ids = vault.currently_sealed_dataset_ids(
+            vault.shard_ledger_for_dataset_dir(config.dataset_dir_resolved())
+        )
         # iter-8: `_tick_dataset_session_dates` now returns `(dates, errors)` -- this call site
         # only ever needed the dates (a corrupt file simply contributes no exposure-seed window,
         # exactly as it always contributed no session date), so the errors half is intentionally
         # unused here, unlike `run_tick_family_fold_request`'s own call site which SERVES them.
-        tick_session_dates, _tick_dataset_errors = _tick_dataset_session_dates(tick_dataset_store)
+        tick_session_dates, _tick_dataset_errors = _tick_dataset_session_dates(
+            tick_dataset_store, excluded_dataset_ids=sealed_dataset_ids
+        )
         initialize_r2_exposure_registry(exposure_registry, corpus_id=TICK_LEGACY_CORPUS_ID, windows=tick_session_dates)
 
     corpus_manifest_hash = _sha256(_canonical(session_dates))
diff --git a/apps/backend/tests/test_datasets.py b/apps/backend/tests/test_datasets.py
index 49473e4..fc99148 100644
--- a/apps/backend/tests/test_datasets.py
+++ b/apps/backend/tests/test_datasets.py
@@ -602,6 +602,78 @@ def test_tc3_schema_basis_and_quote_size_unit_are_stamped_verbatim_when_supplied
         )
 
 
+# --- era "The Rapid Microscope" J-06 step 3 (spec section 2.6's own closing clause): the rule- ------
+# --- text + verification-note manifest fields -- TC-12, TC-13 (docs/phases/goal-rapid-microscope- --
+# --- iter-9.md). Two FURTHER optional, checksum-excluded siblings of schema_basis/quote_size_unit. -
+
+
+def test_tc12_the_rule_text_and_verification_note_are_stamped_verbatim_when_supplied(tmp_path):
+    """TC-12: ``record(..., quote_size_unit_rule_text=..., quote_size_unit_verification_note=...)``
+    stamps both into the manifest verbatim and they survive a store reload -- the exact
+    ``schema_basis``/``quote_size_unit`` precedent, extended to their two new siblings."""
+    store = DatasetStore(tmp_path / "datasets")
+    meta = store.record(
+        symbol="PG", source="test", source_kind="reference", source_id="",
+        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
+        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0,
+        events=[TradeEvent("PG", 0.0, 148.53, 100, Side.UNKNOWN)],
+        schema_basis="v2_preservation", quote_size_unit="shares",
+        quote_size_unit_rule_text="Alpaca CTA/UTP displayed quote sizes are SHARES for windows "
+        "on/after 2025-11-03, ROUND LOTS before.",
+        quote_size_unit_verification_note="verified by comparing session_date '2026-06-09' >= "
+        "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE ('2025-11-03') -> quote_size_unit='shares'",
+    )
+    assert meta["quote_size_unit_rule_text"].startswith("Alpaca CTA/UTP displayed quote sizes")
+    assert "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE" in meta["quote_size_unit_verification_note"]
+
+    reloaded = DatasetStore(tmp_path / "datasets").get(meta["id"])
+    assert reloaded["quote_size_unit_rule_text"] == meta["quote_size_unit_rule_text"]
+    assert reloaded["quote_size_unit_verification_note"] == meta["quote_size_unit_verification_note"]
+
+
+def test_tc12_the_two_new_fields_are_absent_when_not_supplied_never_a_null_placeholder(tmp_path):
+    """The ``observer=``-kwarg absent-key precedent, extended: a caller that omits the two new
+    kwargs (every pre-J-06-step-3 caller) gets a manifest with NEITHER key present at all -- never
+    an emitted ``"quote_size_unit_rule_text": null``."""
+    store = DatasetStore(tmp_path / "datasets")
+    meta = store.record(
+        symbol="PG", source="test", source_kind="reference", source_id="",
+        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
+        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0,
+        events=[TradeEvent("PG", 0.0, 148.53, 100, Side.UNKNOWN)],
+    )
+    assert "quote_size_unit_rule_text" not in meta
+    assert "quote_size_unit_verification_note" not in meta
+
+
+def test_tc13_the_content_checksum_is_byte_identical_with_and_without_the_two_new_fields_supplied(tmp_path):
+    """TC-13: the two new fields are manifest metadata, never tape content -- proven, not assumed,
+    by recording the SAME tape into two separate stores (avoiding the immutable-dataset re-tag
+    refusal) with and without them supplied, and comparing ``meta["checksum"]`` byte for byte (the
+    ``test_the_frozen_split_guard_still_refuses_one_tape_re_fetched_with_preservation_fields``
+    two-separate-stores technique, applied to this exclusion instead of the row-level one)."""
+    events = [
+        QuoteEvent("PG", 0.0, 148.49, 148.53, 700, 100),
+        TradeEvent("PG", 0.02, 148.53, 100, Side.UNKNOWN),
+    ]
+    common = dict(
+        symbol="PG", source="test", source_kind="reference", source_id="",
+        split=SPLIT_TRAIN, window_start_utc="2026-06-09T17:00:00Z",
+        window_end_utc="2026-06-09T17:00:01Z", data_feed="sip", epoch_anchor=0.0, events=events,
+    )
+
+    bare = DatasetStore(tmp_path / "datasets_bare").record(**common)
+    rich = DatasetStore(tmp_path / "datasets_rich").record(
+        **common,
+        schema_basis="v2_preservation", quote_size_unit="shares",
+        quote_size_unit_rule_text="Alpaca CTA/UTP displayed quote sizes are SHARES for windows "
+        "on/after 2025-11-03, ROUND LOTS before.",
+        quote_size_unit_verification_note="verified by comparing session_date '2026-06-09' >= "
+        "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE ('2025-11-03') -> quote_size_unit='shares'",
+    )
+    assert bare["checksum"] == rich["checksum"]
+
+
 def test_tc9_the_dated_rule_constant_lives_exactly_once_in_tick_recorder_never_duplicated():
     """TC-9 (iter-7) updated to its own anticipated iter-8 shape, not silently dropped:
     ``micro_features.QUOTE_SIZE_UNITS`` stays the SOLE unit-vocabulary tuple in the repo (this
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
index bc797f0..9d71c41 100644
--- a/apps/backend/tests/test_desk_screen.py
+++ b/apps/backend/tests/test_desk_screen.py
@@ -93,11 +93,11 @@ def _register_fixture_universe(universe_dir: Path) -> UniverseStore:
     return UniverseStore(universe_dir)
 
 
-def _register_dataset(dataset_store: DatasetStore, symbol: str) -> None:
+def _register_dataset(dataset_store: DatasetStore, symbol: str) -> dict:
     """A minimal, single-trade synthetic dataset registration -- proves ONLY that ``symbol`` is a
     presence in the dataset store (the tick-evidence badge's own honest contract), never a claim
     about real tick content."""
-    dataset_store.record(
+    return dataset_store.record(
         symbol=symbol, source=f"synthetic {symbol}", source_kind="reference", source_id=symbol,
         split=SPLIT_TRAIN, window_start_utc="2026-01-02T14:30:00Z", window_end_utc="2026-01-02T14:30:01Z",
         data_feed="sim", epoch_anchor=None,
@@ -2227,3 +2227,41 @@ def test_sha256_of_every_universe_screen_topup_run_reconcile_run_file_is_unchang
 
     after = _checksums()
     assert after == before
+
+
+# ==================================================================================================
+# spec section 7.5 point 6 (r4) + iter-9 audit finding B6: `tick_evidence` honours the seal
+# ==================================================================================================
+
+
+def test_r4_a_withheld_shard_never_flips_tick_evidence_and_the_exclusion_is_disclosed(ctx):
+    """`tick_evidence` is a per-symbol boolean over the dataset store, so a symbol whose ONLY tick
+    recording is a withheld Validation-Vault shard would leak sealed-tranche membership at symbol
+    granularity -- spec section 7.5 withholds symbol membership until exposure. The count of
+    excluded shards is disclosed in the screen's own payload."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    universe_records, _errors = universe_store.list()
+    members = list(universe_records[-1]["members"])
+    sealed_symbol, public_symbol = members[0], members[1]
+    sealed_meta = _register_dataset(dataset_store, sealed_symbol)
+    _register_dataset(dataset_store, public_symbol)
+
+    before = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    before_entries = {e["symbol"]: e for e in (*before["rows"], *before["skipped"])}
+    assert before_entries[sealed_symbol]["tick_evidence"] is True
+    assert before["withheld_excluded"] == 0
+
+    from app.research import vault
+
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(dataset_store.root)),
+        dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=b"desk-screen-fixture-secret",
+    )
+    after = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    after_entries = {e["symbol"]: e for e in (*after["rows"], *after["skipped"])}
+
+    assert after_entries[sealed_symbol]["tick_evidence"] is False  # membership no longer leaks
+    assert after_entries[public_symbol]["tick_evidence"] is True  # ... targeted, not a blanket break
+    assert after["withheld_excluded"] == 1  # ... and the exclusion is stated, never silent
diff --git a/apps/backend/tests/test_desk_screen_compute.py b/apps/backend/tests/test_desk_screen_compute.py
index f4c885a..bb69308 100644
--- a/apps/backend/tests/test_desk_screen_compute.py
+++ b/apps/backend/tests/test_desk_screen_compute.py
@@ -130,6 +130,10 @@ def test_trigger_members_total_is_known_synchronously_before_any_background_work
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
             "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc",
             "rows": [], "skipped": [],
+            "withheld_excluded": 0,  # r4 (spec section 7.5 point 6): the stub mirrors the real shape
+            # spec section 7.5 point 6 (r4): `compute_screen` now always reports what its
+            # dataset enumeration excluded; this stub mirrors the real return shape.
+            "withheld_excluded": 0,
         }
 
     monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
@@ -185,6 +189,10 @@ def test_second_trigger_while_running_returns_the_same_job_started_false(manager
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
             "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc",
             "rows": [], "skipped": [],
+            "withheld_excluded": 0,  # r4 (spec section 7.5 point 6): the stub mirrors the real shape
+            # spec section 7.5 point 6 (r4): `compute_screen` now always reports what its
+            # dataset enumeration excluded; this stub mirrors the real return shape.
+            "withheld_excluded": 0,
         }
 
     monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
@@ -209,6 +217,9 @@ def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env, mo
         lambda *a, **k: {
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
             "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
+            # spec section 7.5 point 6 (r4): `compute_screen` now always reports what its
+            # dataset enumeration excluded; this stub mirrors the real return shape.
+            "withheld_excluded": 0,
         },
     )
 
@@ -247,6 +258,9 @@ def test_a_cancellation_signal_resolves_state_cancelled_with_partial_progress_an
         return {
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
             "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
+            # spec section 7.5 point 6 (r4): `compute_screen` now always reports what its
+            # dataset enumeration excluded; this stub mirrors the real return shape.
+            "withheld_excluded": 0,
         }
 
     monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
@@ -298,6 +312,9 @@ def test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_sile
         lambda *a, **k: {
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
             "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
+            # spec section 7.5 point 6 (r4): `compute_screen` now always reports what its
+            # dataset enumeration excluded; this stub mirrors the real return shape.
+            "withheld_excluded": 0,
         },
     )
 
@@ -331,6 +348,9 @@ def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_referenc
         lambda *a, **k: {
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
             "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
+            # spec section 7.5 point 6 (r4): `compute_screen` now always reports what its
+            # dataset enumeration excluded; this stub mirrors the real return shape.
+            "withheld_excluded": 0,
         },
     )
 
@@ -461,6 +481,10 @@ def test_initial_and_running_snapshot_carry_the_honest_reused_false_screen_id_nu
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
             "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc",
             "rows": [], "skipped": [],
+            "withheld_excluded": 0,  # r4 (spec section 7.5 point 6): the stub mirrors the real shape
+            # spec section 7.5 point 6 (r4): `compute_screen` now always reports what its
+            # dataset enumeration excluded; this stub mirrors the real return shape.
+            "withheld_excluded": 0,
         }
 
     monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
@@ -739,6 +763,9 @@ def test_cancel_while_running_succeeds_and_a_subsequent_cancel_is_409(route_ctx,
         return {
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
             "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": [],
+            # spec section 7.5 point 6 (r4): `compute_screen` now always reports what its
+            # dataset enumeration excluded; this stub mirrors the real return shape.
+            "withheld_excluded": 0,
         }
 
     monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
@@ -999,6 +1026,9 @@ def test_tc5_a_cancellation_mid_walk_records_state_cancelled_with_partial_attemp
         return {
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
             "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": rows, "skipped": skipped,
+            # spec section 7.5 point 6 (r4): the real `compute_screen` always reports what its
+            # dataset enumeration excluded; this stub mirrors that shape.
+            "withheld_excluded": 0,
         }
 
     monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
@@ -1202,6 +1232,9 @@ def test_a_terminal_log_write_that_raises_is_never_re_logged_as_a_second_failed_
         return {
             "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
             "config_fingerprint": "y", "bar_store_signature": "z", "screen_coverage_signature": "zc", "rows": [], "skipped": skipped,
+            # spec section 7.5 point 6 (r4): the real `compute_screen` always reports what its
+            # dataset enumeration excluded; this stub mirrors that shape.
+            "withheld_excluded": 0,
         }
 
     monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
diff --git a/apps/backend/tests/test_edge_report.py b/apps/backend/tests/test_edge_report.py
index aa3082d..627f530 100644
--- a/apps/backend/tests/test_edge_report.py
+++ b/apps/backend/tests/test_edge_report.py
@@ -29,6 +29,7 @@ from __future__ import annotations
 import dataclasses
 import json
 import random
+import shutil
 import sys
 from pathlib import Path
 
@@ -44,6 +45,7 @@ from app.config import (
 )
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import edge_report
+from app.research import vault
 from app.research.backtests import BacktestJobManager, REGISTER, STATUS_DONE
 from app.research.bars import BarStore
 from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
@@ -1652,3 +1654,99 @@ def test_parallel_prewarm_with_zero_eligible_datasets_never_spins_up_a_process_p
     )
 
     assert results == []
+
+
+# === spec section 7.5 point 6 (r4, owner ruling): corpus enumerators honour the seal =============
+# iter-9 re-audit finding B2: this module drives ``BacktestJobManager`` directly, so the r3
+# route-level refusal never saw it -- a corpus-wide report replayed a sealed shard's events and
+# republished its stored manifest (id + raw checksum + window + counts) through
+# ``GET /research/backtests``. The fix EXCLUDES withheld shards at the single ``DatasetStore.list``
+# choke point and DISCLOSES the count; the tests below pin both halves, plus the counter-test that
+# the public siblings are still measured (a blanket break would "pass" an exclusion-only check).
+
+
+def _writable_fixture_store(tmp_path) -> DatasetStore:
+    target = tmp_path / "r4-datasets"
+    shutil.copytree(FIXTURE_DATASET_DIR, target)
+    return DatasetStore(target)
+
+
+def _seal(dataset_store: DatasetStore, meta: dict) -> None:
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(dataset_store.root)),
+        dataset_id=meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=meta["checksum"], event_count=meta["event_counts"]["total"],
+        vault_secret=b"edge-report-fixture-secret",
+    )
+
+
+def test_r4_a_withheld_shard_is_never_measured_and_the_count_is_disclosed(store, tmp_path):
+    dataset_store = _writable_fixture_store(tmp_path)
+    store.set_champion_pointer(strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT, wall_ts=1.0)
+    records, _errors = dataset_store.list()
+    train_meta = next(r for r in records if r["split"] == SPLIT_TRAIN)
+    holdout_meta = next(r for r in records if r["split"] == SPLIT_HOLDOUT)
+
+    before = run_edge_report(store, dataset_store, CONFIG)
+    assert [r["dataset_id"] for r in before["train"]["datasets"]] == [train_meta["id"]]
+    assert [r["dataset_id"] for r in before["holdout"]["datasets"]] == [holdout_meta["id"]]
+    assert before["withheld_excluded"] == 0  # an empty vault withholds nothing
+
+    _seal(dataset_store, train_meta)
+    after = run_edge_report(store, dataset_store, CONFIG)
+
+    assert after["train"]["datasets"] == []  # the sealed shard was never backtested
+    assert after["withheld_excluded"] == 1  # ... and the shrink is stated, not silent
+    # the counter-test: withholding is TARGETED, not a blanket break of the report
+    assert [r["dataset_id"] for r in after["holdout"]["datasets"]] == [holdout_meta["id"]]
+    assert after["holdout"]["datasets"][0]["champion"] == before["holdout"]["datasets"][0]["champion"]
+    # a COUNT, never an identity: neither the id nor the raw checksum reaches the report body
+    rendered = json.dumps(after, sort_keys=True)
+    assert train_meta["id"] not in rendered
+    assert train_meta["checksum"] not in rendered
+
+
+def test_r4_a_fully_withheld_corpus_says_so_instead_of_looking_like_a_measured_empty(store, tmp_path):
+    """r4's "a run whose entire eligible corpus is withheld reports that honestly rather than
+    emitting an empty-but-shaped result" -- otherwise this report is byte-indistinguishable from
+    "every dataset was measured and none showed an edge"."""
+    dataset_store = _writable_fixture_store(tmp_path)
+    store.set_champion_pointer(strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT, wall_ts=1.0)
+    for meta in dataset_store.list()[0]:
+        _seal(dataset_store, meta)
+
+    report = run_edge_report(store, dataset_store, CONFIG)
+
+    assert report["train"]["datasets"] == [] and report["holdout"]["datasets"] == []
+    assert report["withheld_excluded"] == 2
+    assert report["finding"] == edge_report.FULLY_WITHHELD_FINDING
+    assert report["finding"] != NO_POSITIVE_EDGE_FINDING
+    assert store.list_backtests(limit=10) == []  # not one sealed shard's events was ever replayed
+
+
+def test_r4_a_genuinely_empty_registry_still_reads_as_no_positive_edge_not_as_withholding(store, tmp_path):
+    """The counter-test for the finding above: zero datasets and zero withheld shards is the
+    pre-existing honest empty report, unchanged -- ``FULLY_WITHHELD_FINDING`` is reserved for the
+    case where something really was held back."""
+    dataset_store = DatasetStore(tmp_path / "empty-datasets")
+
+    report = run_edge_report(store, dataset_store, CONFIG)
+
+    assert report["finding"] == NO_POSITIVE_EDGE_FINDING
+    assert report["withheld_excluded"] == 0
+
+
+def test_r4_the_three_way_comparison_report_discloses_the_same_count(store, tmp_path):
+    dataset_store = _writable_fixture_store(tmp_path)
+    bar_store = BarStore(tmp_path / "r4-bars")  # empty: no scan event, so an honest cells-free run
+    train_meta = next(r for r in dataset_store.list()[0] if r["split"] == SPLIT_TRAIN)
+
+    before = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)
+    assert before["withheld_excluded"] == 0
+    assert "finding" not in before  # honest omission while nothing is withheld
+
+    _seal(dataset_store, train_meta)
+    after = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)
+
+    assert after["withheld_excluded"] == 1
+    assert train_meta["id"] not in json.dumps(after, sort_keys=True)
diff --git a/apps/backend/tests/test_edge_report_cache.py b/apps/backend/tests/test_edge_report_cache.py
index 12203ed..6cf5f19 100644
--- a/apps/backend/tests/test_edge_report_cache.py
+++ b/apps/backend/tests/test_edge_report_cache.py
@@ -21,7 +21,9 @@ import pytest
 from app.config import CONFIG
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
+from app.research import vault
 from app.research.edge_report_cache import EdgeReportCache, resolve_cache_db_path
+from app.research.micro_snapshots import exclude_withheld
 
 WINDOW_START, WINDOW_END = "2026-01-02T14:30:00Z", "2026-01-02T14:30:05Z"
 
@@ -594,3 +596,58 @@ def test_resolve_cache_db_path_defaults_to_a_sibling_of_the_dataset_dir(monkeypa
     dataset_dir = str(tmp_path / "datasets")
 
     assert resolve_cache_db_path(dataset_dir) == str(tmp_path / "edge_report_cache.db")
+
+
+# --- spec section 7.5 point 6 (r4): the key's corpus is the SEAL-FILTERED one -------------------
+# The write half (`get_or_compute`/`compute_and_publish`) and the read half (`lookup`, whose
+# caller `edge_report.peek_strategy_comparison_report` passes already-filtered records) must key
+# the SAME report under the SAME corpus view. Without the shared filter, the first sealed shard
+# would make every subsequent GET miss forever while the compute kept republishing.
+
+
+def _seal(dstore: DatasetStore, meta: dict) -> None:
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(dstore.root)),
+        dataset_id=meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=meta["checksum"], event_count=meta["event_counts"]["total"],
+        vault_secret=b"edge-report-cache-fixture-secret",
+    )
+
+
+def test_r4_a_warm_key_written_with_a_shard_sealed_is_found_by_the_read_half(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    sealed = _record(dstore, "SYN-B", split=SPLIT_HOLDOUT)
+    _seal(dstore, sealed)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    compute = _CountingCompute({"train": {"cells": ["only-the-public-sibling"]}, "holdout": {"cells": []}})
+
+    published = cache.get_or_compute(dstore, CONFIG, compute)
+
+    # the read half keys off the SAME seal-filtered registry the report was computed over
+    records, _errors = dstore.list()
+    kept, withheld_excluded = exclude_withheld(records, dstore)
+    assert withheld_excluded == 1
+    assert cache.lookup(kept, CONFIG) == published
+    assert compute.calls == 1  # a second dispatch through the write half is a genuine hit
+    assert cache.get_or_compute(dstore, CONFIG, compute) == published
+    assert compute.calls == 1
+
+
+def test_r4_sealing_a_shard_busts_the_cache_because_the_report_now_measures_less(tmp_path):
+    """The counter-test to the parity above: a sealed shard genuinely CHANGES what the report
+    measures, so it must change what the cache serves — never a stale report served under a
+    corpus that no longer exists."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    to_seal = _record(dstore, "SYN-B", split=SPLIT_HOLDOUT)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    compute = _CountingCompute()
+
+    cache.get_or_compute(dstore, CONFIG, compute)
+    assert compute.calls == 1
+
+    _seal(dstore, to_seal)
+    cache.get_or_compute(dstore, CONFIG, compute)
+
+    assert compute.calls == 2  # a cold key: the corpus this report measures really did change
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index a700812..0bb7771 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -1353,7 +1353,12 @@ async def test_edge_report_tool_byte_identical_to_rest(mcp_env):
     assert payload.get("status") == "not_computed", (
         "expected the not-computed shape: registry is non-empty and nothing has warmed the cache"
     )
-    assert set(payload) == {"status", "detail", "dataset_count", "register", "compute"}
+    # `withheld_excluded` (spec section 7.5 point 6, r4): the seal-filtered `dataset_count`
+    # above states this report's basis, so what it leaves out is disclosed beside it.
+    assert set(payload) == {
+        "status", "detail", "dataset_count", "register", "compute", "withheld_excluded",
+    }
+    assert payload["withheld_excluded"] == 0  # nothing is sealed on this live backend
     assert result.isError is False
     assert len(result.content) == 1
     assert result.content[0].text.encode("utf-8") == rest.content, "edge_report not byte-identical"
diff --git a/apps/backend/tests/test_micro_join.py b/apps/backend/tests/test_micro_join.py
index 7c9c2f1..9577ce7 100644
--- a/apps/backend/tests/test_micro_join.py
+++ b/apps/backend/tests/test_micro_join.py
@@ -31,6 +31,7 @@ from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import desk_playbook as desk_playbook_module
 from app.research import desk_playbook_context as desk_playbook_context_module
 from app.research import micro_join
+from app.research import vault
 from app.research.datasets import DatasetStore
 from app.research.desk_playbook import PlaybookStore, playbook_parameters
 from app.research.desk_playbook_context import BandMapResolver
@@ -475,6 +476,8 @@ def test_joinable_corpus_counts_is_an_honest_zero_with_no_playbook_records(tmp_p
         "band_touch_count": {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None},
         "by_setup_id": {},
         "playbook_integrity_errors": [],
+        # spec section 7.5 point 6 (r4): the enumerator's own disclosure of what it left out.
+        "withheld_excluded": 0,
     }
 
 
@@ -751,3 +754,76 @@ def test_shares_and_clock_horizon_rows_are_unchanged_by_the_index_iteration_rewr
     assert micro_join._shares_horizon_row(trade_rows, anchor_pos, 50_000) == _reference_shares_horizon_row(50_000)
     horizon_ts = trade_rows[anchor_pos]["anchor_at"] + 60
     assert micro_join._clock_horizon_row(trade_rows, anchor_pos, horizon_ts) == _reference_clock_horizon_row(horizon_ts)
+
+
+# --- spec section 7.5 point 6 (r4): the seal-aware enumerator + its disclosure -------------------
+# iter-9 audit finding B5: `micro_readiness` already excludes a withheld shard from
+# `totals.distinct_datasets`, but this counter enumerated the store itself and counted the SAME
+# shard's window as joinable evidence -- two numbers in one payload, one excluding sealed shards
+# and one including them.
+
+
+def _seal(dataset_store: DatasetStore, meta: dict, *, universe_id: str = "starter-tranche-v1") -> None:
+    """Seal one already-recorded dataset through the vault's OWN public lifecycle entry point
+    (never a hand-written ledger line), resolved from THIS store's own directory."""
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(dataset_store.root)),
+        dataset_id=meta["id"],
+        universe_id=universe_id,
+        content_checksum=meta["checksum"],
+        event_count=meta["event_counts"]["total"],
+        vault_secret=b"micro-join-fixture-secret",
+    )
+
+
+def test_r4_a_withheld_shards_window_never_counts_as_joinable_evidence(tmp_path):
+    """A signal whose ONLY covering tick window belongs to a withheld Validation-Vault shard is
+    not joinable evidence -- and the count that dropped is DISCLOSED, never silently shrunk."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    sealed_meta = _plant_dataset(
+        dataset_store, symbol="ZJN",
+        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+    )
+    _plant_dataset(
+        dataset_store, symbol="PBL",
+        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+    )
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    _plant_playbook_signal(
+        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-r4",
+        signals=[
+            {"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:30Z"},
+            {"symbol": "PBL", "setup_id": "jbe", "trigger_ts": "2026-06-09T13:00:30Z"},
+        ],
+    )
+
+    before = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+    assert before["total"] == 2
+    assert before["by_setup_id"] == {"opening_range_break": 1, "jbe": 1}
+    assert before["withheld_excluded"] == 0  # an empty vault withholds nothing
+
+    _seal(dataset_store, sealed_meta)
+    after = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
+
+    assert after["total"] == 1  # only the PUBLIC sibling's signal remains joinable
+    assert after["by_setup_id"] == {"jbe": 1}
+    assert after["withheld_excluded"] == 1  # the shrink is stated, never silent
+    assert "ZJN" not in str(after) and sealed_meta["id"] not in str(after)  # a COUNT, never an id
+
+
+def test_r4_find_covering_dataset_refuses_to_hand_back_a_withheld_shard(tmp_path):
+    """``find_covering_dataset`` is the door onto a covering SNAPSHOT and therefore onto a shard's
+    rows: a withheld shard covering the instant is an honest ``None``, exactly as if no window
+    covered it -- never a read of held-out tape."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _plant_dataset(
+        dataset_store, symbol="ZJN",
+        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+    )
+    at_epoch = datetime(2026, 6, 9, 13, 0, 30, tzinfo=timezone.utc).timestamp()
+
+    found = micro_join.find_covering_dataset("ZJN", at_epoch, dataset_store)
+    assert found is not None and found["id"] == meta["id"]
+
+    _seal(dataset_store, meta)
+    assert micro_join.find_covering_dataset("ZJN", at_epoch, dataset_store) is None
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
index 963e67d..246f303 100644
--- a/apps/backend/tests/test_micro_readiness.py
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -471,6 +471,8 @@ def test_joinable_corpus_defaults_to_an_honest_zero_without_a_playbook_store(tmp
         "band_touch_count": {"status": "not_enumerated", "count": None},
         "by_setup_id": {},
         "playbook_integrity_errors": [],
+        # spec section 7.5 point 6 (r4): the enumerator's own disclosure of what it left out.
+        "withheld_excluded": 0,
     }
 
 
@@ -505,6 +507,8 @@ def test_joinable_corpus_matches_joinable_corpus_counts_directly(tmp_path):
         "band_touch_count": {"status": "not_enumerated", "count": None},
         "by_setup_id": {"opening_range_break": 1},
         "playbook_integrity_errors": [],
+        # spec section 7.5 point 6 (r4): the enumerator's own disclosure of what it left out.
+        "withheld_excluded": 0,
     }
 
 
@@ -558,6 +562,8 @@ def test_real_corpus_readiness_still_serves_an_honest_zero_joinable_corpus_witho
         "band_touch_count": {"status": "not_enumerated", "count": None},
         "by_setup_id": {},
         "playbook_integrity_errors": [],
+        # spec section 7.5 point 6 (r4): the enumerator's own disclosure of what it left out.
+        "withheld_excluded": 0,
     }
 
 
diff --git a/apps/backend/tests/test_pnl_ledger.py b/apps/backend/tests/test_pnl_ledger.py
index 0f621fc..0449c28 100644
--- a/apps/backend/tests/test_pnl_ledger.py
+++ b/apps/backend/tests/test_pnl_ledger.py
@@ -747,3 +747,44 @@ def test_committed_pnl_history_file_is_not_a_default_target_of_these_tests(fresh
     # explicit path=... — never the bare two-arg form that would target the committed file.
     assert "write_history_markdown(fresh_store, CONFIG)\n" not in src
     assert "write_history_markdown(store, CONFIG)\n" not in src
+
+
+# --- spec section 7.5 point 6 (r4): the append-only row discloses what its run left out ----------
+
+
+def test_r4_the_ledger_row_records_the_writing_runs_withheld_count(reports_ctx):
+    """An APPEND-ONLY row can never be corrected, so a promotion recorded over a shrunken corpus
+    must SAY the corpus shrank (spec section 7.5 point 6, r4 — ``pnl_scan``'s sweep is the caller
+    that passes this). A count, never an id."""
+    store, _dstore, train_report, holdout_report = reports_ctx
+
+    row = append_validation_row(
+        store,
+        CONFIG,
+        enhancement_id="e-withheld-disclosed",
+        title="a promotion measured over a partially withheld corpus",
+        candidate_train_report_id=train_report["id"],
+        candidate_holdout_report_id=holdout_report["id"],
+        withheld_excluded=3,
+    )
+
+    assert row["provenance"]["withheld_excluded"] == 3
+    assert store.get_pnl_ledger_row("e-withheld-disclosed").payload == row  # persisted verbatim
+
+
+def test_r4_a_caller_that_passes_nothing_records_the_pre_r4_shape_exactly(reports_ctx):
+    """The honest-omission counter-test: ``pnl_baseline``'s founding seed knows nothing about a
+    corpus enumeration, so its row carries NO ``withheld_excluded`` key at all — never a
+    fabricated ``0`` implying a check that never happened."""
+    store, _dstore, train_report, holdout_report = reports_ctx
+
+    row = append_validation_row(
+        store,
+        CONFIG,
+        enhancement_id="e-no-withheld-key",
+        title="founding seed shape",
+        candidate_train_report_id=train_report["id"],
+        candidate_holdout_report_id=holdout_report["id"],
+    )
+
+    assert "withheld_excluded" not in row["provenance"]
diff --git a/apps/backend/tests/test_pnl_scan.py b/apps/backend/tests/test_pnl_scan.py
index 8bcc513..365a4ad 100644
--- a/apps/backend/tests/test_pnl_scan.py
+++ b/apps/backend/tests/test_pnl_scan.py
@@ -55,6 +55,7 @@ from app.config import (
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.providers.simulated import SIM_SCENARIOS, SimulatedProvider
 from app.research import pnl_scan
+from app.research import vault
 from app.research.bars import BarStore
 from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, record_from_source
 from app.research.pnl_baseline import seed_founding_row
@@ -1278,3 +1279,75 @@ def test_no_bypass_guard_can_fail_on_a_seeded_violation():
     )
     with pytest.raises(AssertionError):
         _assert_no_bypass_tokens(seeded_source, label="seeded pnl_scan.py")
+
+
+# === spec section 7.5 point 6 (r4, owner ruling): corpus enumerators honour the seal =============
+# iter-9 re-audit finding B2: this sweep enumerates the whole store and drives
+# ``BacktestJobManager`` directly, so the r3 route-level refusal never saw it -- a sealed shard's
+# events were replayed and its stored manifest (id + raw checksum + window + counts) landed in
+# every persisted backtest result, and on a promotion in the APPEND-ONLY PnL ledger.
+
+
+def _writable_fixture_store(tmp_path) -> DatasetStore:
+    import shutil
+
+    target = tmp_path / "r4-datasets"
+    shutil.copytree(FIXTURE_DATASET_DIR, target)
+    return DatasetStore(target)
+
+
+def _seal(dataset_store: DatasetStore, meta: dict) -> None:
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(dataset_store.root)),
+        dataset_id=meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=meta["checksum"], event_count=meta["event_counts"]["total"],
+        vault_secret=b"pnl-scan-fixture-secret",
+    )
+
+
+def test_r4_a_withheld_shard_is_never_swept_and_the_count_is_disclosed(store, tmp_path, certificate_store):
+    dataset_store = _writable_fixture_store(tmp_path)
+    train_meta = next(r for r in dataset_store.list()[0] if r["split"] == SPLIT_TRAIN)
+    holdout_meta = next(r for r in dataset_store.list()[0] if r["split"] == SPLIT_HOLDOUT)
+
+    before = run_sweep(store, dataset_store, CONFIG, certificate_store=certificate_store)
+    (candidate_before,) = before["candidates"]
+    assert [d["dataset_id"] for d in candidate_before["train"]["datasets"]] == [train_meta["id"]]
+    assert before["withheld_excluded"] == 0
+
+    _seal(dataset_store, train_meta)
+    after = run_sweep(store, dataset_store, CONFIG, certificate_store=certificate_store)
+
+    (candidate_after,) = after["candidates"]
+    assert candidate_after["train"]["datasets"] == []  # the sealed shard was never backtested
+    assert after["withheld_excluded"] == 1  # ... and the shrink is stated, not silent
+    # the counter-test: the public hold-out sibling is still measured, byte-identically
+    assert [d["dataset_id"] for d in candidate_after["holdout"]["datasets"]] == [holdout_meta["id"]]
+    assert candidate_after["holdout"]["aggregate"] == candidate_before["holdout"]["aggregate"]
+    rendered = json.dumps(after, sort_keys=True)
+    assert train_meta["id"] not in rendered and train_meta["checksum"] not in rendered
+
+
+def test_r4_a_fully_withheld_corpus_says_so_rather_than_reporting_an_empty_sweep(
+    store, tmp_path, certificate_store
+):
+    dataset_store = _writable_fixture_store(tmp_path)
+    for meta in dataset_store.list()[0]:
+        _seal(dataset_store, meta)
+
+    report = run_sweep(store, dataset_store, CONFIG, certificate_store=certificate_store)
+
+    assert report["withheld_excluded"] == 2
+    assert pnl_scan.FULLY_WITHHELD_CAVEAT in report["provenance"]["assumptions"]
+    (candidate,) = report["candidates"]
+    assert candidate["train"]["datasets"] == [] and candidate["holdout"]["datasets"] == []
+    assert candidate["survivor"] is False
+    assert store.list_backtests(limit=10) == []  # not one sealed shard's events was ever replayed
+
+
+def test_r4_an_ordinary_sweep_carries_no_fully_withheld_caveat(store, certificate_store):
+    """The counter-test: the caveat is reserved for a genuinely fully-withheld corpus, never a
+    standing decoration on every report."""
+    report = run_sweep(store, DatasetStore(FIXTURE_DATASET_DIR), CONFIG, certificate_store=certificate_store)
+    assert report["withheld_excluded"] == 0
+    assert report["provenance"]["assumptions"] == [pnl_scan.BREAKTHROUGH_ANCHOR_CAVEAT]
diff --git a/apps/backend/tests/test_setups.py b/apps/backend/tests/test_setups.py
index 7eded97..6f39787 100644
--- a/apps/backend/tests/test_setups.py
+++ b/apps/backend/tests/test_setups.py
@@ -1325,3 +1325,35 @@ def test_tc8_durable_publish_failure_never_blocks_compute_setups_from_serving_th
     result = compute_setups(store, config)  # must not raise
 
     assert len(result["events"]) >= 1, "the freshly-scanned (correct) result must still be served"
+
+
+def test_r4_a_withheld_shard_is_never_replayed_into_a_served_drill_in(tmp_path):
+    """Spec section 7.5 point 6 (r4): this join enumerates the dataset store and then REPLAYS the
+    matched dataset's raw events into a served drill-in, so a withheld Validation-Vault shard must
+    never match -- the drill-in falls back to its existing, honest empty timeline (the same answer
+    it already gives when no window covers the touch), never a read of held-out tape."""
+    import shutil
+
+    from app.research import vault
+
+    bar_store = BarStore(tmp_path / "bars")
+    _seed_pg_join_bars(bar_store)
+    event = _pg_join_event(bar_store)
+    target = tmp_path / "j03-datasets"
+    shutil.copytree(FIXTURE_DATASETS_J03_DIR, target)
+    dataset_store = DatasetStore(target)
+
+    joined = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
+    assert joined["tape_timeline"], "the baseline join must be non-empty or this proves nothing"
+
+    (covering,) = dataset_store.list()[0]
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(dataset_store.root)),
+        dataset_id=covering["id"], universe_id="starter-tranche-v1",
+        content_checksum=covering["checksum"], event_count=covering["event_counts"]["total"],
+        vault_secret=b"setups-fixture-secret",
+    )
+
+    after = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
+    assert after["tape_timeline"] == []
+    assert after == event  # the event is returned unchanged, exactly as for an unmatched touch
diff --git a/apps/backend/tests/test_tick_recorder.py b/apps/backend/tests/test_tick_recorder.py
index ac6a4a8..9a8fcc0 100644
--- a/apps/backend/tests/test_tick_recorder.py
+++ b/apps/backend/tests/test_tick_recorder.py
@@ -279,16 +279,6 @@ def test_events_recorded_carry_the_card_5_1_preservation_fields_verbatim(rec_ctx
 # ==================================================================================================
 
 
-class _StrippedTradeEventMissingConditions:
-    """A deliberately-incomplete stand-in dataclass -- SIMULATES the preservation prerequisite
-    being absent without needing to monkeypatch the real, already-shipped ``TradeEvent`` (which
-    would be a fiction: the real class already carries these fields as of iter-7)."""
-
-    __dataclass_fields__ = {
-        name: None for name in ("ticker", "timestamp", "price", "size", "side", "exchange", "tape", "trade_id")
-    }  # deliberately missing "conditions"
-
-
 def test_tc8_the_recorder_refuses_to_record_anything_when_the_preservation_capability_is_absent(rec_ctx):
     import dataclasses as _dc
 
@@ -366,6 +356,40 @@ def test_tc10_recorded_datasets_carry_the_stamped_quote_size_unit_from_the_singl
     assert by_symbol["AAPL"]["schema_basis"] == tr.RECORDER_SCHEMA_BASIS
 
 
+def test_tc12_finalize_day_stamps_the_rule_text_and_a_per_dataset_verification_note(rec_ctx):
+    """iter-9 TC-12 (spec section 2.6's own closing clause): ``_finalize_day``'s
+    ``record_from_source`` call gains the two new sibling fields alongside the existing
+    ``schema_basis``/``quote_size_unit`` stamps -- the rule text is the ONE frozen sentence
+    (``QUOTE_SIZE_UNIT_RULE_TEXT``) verbatim on every dataset regardless of which side of the
+    cutover it falls on; the verification note is genuinely PER-DATASET (names each dataset's own
+    ``session_date`` and the actual comparison direction against ``ALPACA_QUOTE_SIZE_UNIT_
+    EFFECTIVE``, TC-13's own "not one frozen sentence repeated regardless" contract)."""
+    adapter, dataset_store, checkpoint_store = rec_ctx
+    pre_chunks = tr.plan_recorder_chunks(["AAPL"], ["2025-10-15"], chunk_seconds=7800.0)
+    post_chunks = tr.plan_recorder_chunks(["MSFT"], ["2025-11-10"], chunk_seconds=7800.0)
+    tr.run_tick_recording(pre_chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+    tr.run_tick_recording(post_chunks, dataset_store, checkpoint_store, adapter, CONFIG)
+
+    records, _errors = dataset_store.list()
+    by_symbol = {r["symbol"]: r for r in records}
+
+    for symbol in ("AAPL", "MSFT"):
+        assert by_symbol[symbol]["quote_size_unit_rule_text"] == tr.QUOTE_SIZE_UNIT_RULE_TEXT
+        assert "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE" in by_symbol[symbol]["quote_size_unit_verification_note"]
+
+    # the pre-cutover (round_lots) dataset's note names a "<" comparison; the post-cutover
+    # (shares) dataset's note names a ">=" comparison -- genuinely per-dataset, not one constant
+    # string copy-pasted onto every row regardless of its own date.
+    assert "('2025-10-15') < " in by_symbol["AAPL"]["quote_size_unit_verification_note"]
+    assert "('2025-11-10') >= " in by_symbol["MSFT"]["quote_size_unit_verification_note"]
+    assert by_symbol["AAPL"]["quote_size_unit_verification_note"] != by_symbol["MSFT"]["quote_size_unit_verification_note"]
+
+    # both survive a reload verbatim (the schema_basis/quote_size_unit reload precedent, extended).
+    reloaded = DatasetStore(str(Path(checkpoint_store._root).parent / "datasets")).get(by_symbol["AAPL"]["id"])
+    assert reloaded["quote_size_unit_rule_text"] == tr.QUOTE_SIZE_UNIT_RULE_TEXT
+    assert reloaded["quote_size_unit_verification_note"] == by_symbol["AAPL"]["quote_size_unit_verification_note"]
+
+
 def test_tc11_an_out_of_vocabulary_quote_size_unit_is_still_rejected_by_the_existing_guard(rec_ctx):
     _adapter, dataset_store, _checkpoint_store = rec_ctx
     with pytest.raises(ValueError, match="unknown quote_size_unit"):
@@ -544,8 +568,9 @@ def test_tc6_a_concurrent_second_trigger_returns_the_in_flight_runs_snapshot_unc
 def test_tc7_cancel_on_an_idle_manager_is_rejected_by_the_route_layers_own_409_contract(manager_ctx):
     """The manager's OWN ``.cancel()`` is a harmless no-op when idle (module docstring); the route
     is what turns "idle" into an HTTP 409 (micro_routes.py's established convention, tested at the
-    route layer in test_micro_routes_recorder.py). Pinned here at the manager level: cancelling an
-    idle manager never raises, and its own ``accepted`` flag says nothing was running."""
+    route layer by ``test_cancelling_an_idle_recorder_is_a_409`` further down in THIS SAME file,
+    section 11's REST-route tests). Pinned here at the manager level: cancelling an idle manager
+    never raises, and its own ``accepted`` flag says nothing was running."""
     manager, _dataset_store, _checkpoint_store, _run_log_dir = manager_ctx
     result = manager.cancel()
     assert result == {"state": "cancelled", "accepted": False}
diff --git a/apps/backend/tests/test_walkforward.py b/apps/backend/tests/test_walkforward.py
index b3bf83a..07416c8 100644
--- a/apps/backend/tests/test_walkforward.py
+++ b/apps/backend/tests/test_walkforward.py
@@ -14,8 +14,14 @@ from app.main import app
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import walkforward as wf
 from app.research import walkforward_ledger as wl
+from app.research import vault
 from app.research.datasets import DatasetStore
-from app.research.micro_accessor import ExposureRegistry, has_any_exposure_entries, initialize_r2_exposure_registry
+from app.research.micro_accessor import (
+    R2_REVISION_INSTANT,
+    ExposureRegistry,
+    has_any_exposure_entries,
+    initialize_r2_exposure_registry,
+)
 from app.research.micro_readiness import EXPOSURE_STATE_EXPLORATORY, MicroReadinessCache, build_readiness
 from app.research.micro_routes import (
     get_micro_exposure_registry_dir,
@@ -1148,7 +1154,11 @@ def test_tc14_run_tick_family_fold_request_surfaces_integrity_errors_on_its_succ
     # 110 distinct labels clear the WF_MIN_SUFFICIENT_FOLDS floor (105) under DIAGNOSTIC_GEOMETRY;
     # never parsed as real calendar dates by the function under test, only counted and hashed.
     fake_dates = [f"session-{i:04d}" for i in range(110)]
-    monkeypatch.setattr(wf, "_tick_dataset_session_dates", lambda store: (fake_dates, fake_errors))
+    # `**_kwargs` absorbs the r4 `excluded_dataset_ids` the caller now passes (spec section 7.5
+    # point 6) -- this stub is about the errors half, not about which ids were excluded.
+    monkeypatch.setattr(
+        wf, "_tick_dataset_session_dates", lambda store, **_kwargs: (fake_dates, fake_errors)
+    )
 
     ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
     config = _FakeConfig(dataset_dir=str(tmp_path / "unused-datasets"))
@@ -1276,3 +1286,221 @@ def test_tc3_the_compute_routes_worker_resolves_the_typed_refusal_to_a_failed_ru
     finally:
         for dep in (get_walkforward_ledger_dir, get_micro_exposure_registry_dir, get_walkforward_compute_manager, get_universe_store, get_bar_store, get_playbook_store):
             app.dependency_overrides.pop(dep, None)
+
+
+# === iter-9: the exposure-registry sealed filter (TC-10/TC-11) -- closes the known latent hole ======
+# a freshly `vault.py`-sealed tick dataset must never be marked "already exposed" by the
+# WALKFORWARD registry's own r2 seed for TICK_LEGACY_CORPUS_ID, which (pre-iter-9) read "every
+# currently-registered tick dataset" with no notion of sealing at all.
+
+
+def test_tc10_a_sealed_datasets_window_carries_no_r2_exposure_entry_while_an_unsealed_siblings_does(tmp_path, monkeypatch):
+    signature = "sig-tc10"
+    sessions = [f"2026-10-{d:03d}" for d in range(1, 156)]
+    records = [
+        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
+        for s in sessions
+    ]
+    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
+    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+
+    tick_dir = tmp_path / "tick_datasets"
+    tick_store = DatasetStore(tick_dir)
+    # D: sealed via vault.py before this run -- its own window must carry NO r2 exposure entry.
+    sealed_meta = _plant_tick_dataset(
+        tick_store, symbol="AAPL", window_start_utc="2026-06-08T13:30:00Z", window_end_utc="2026-06-08T20:00:00Z"
+    )
+    # E: an ordinary, unsealed sibling on a DIFFERENT date -- its window IS exposed, as before.
+    unsealed_meta = _plant_tick_dataset(
+        tick_store, symbol="MSFT", window_start_utc="2026-06-09T13:30:00Z", window_end_utc="2026-06-09T20:00:00Z", price=101.00
+    )
+
+    shard_ledger = vault.shard_ledger_for_dataset_dir(str(tick_dir))
+    vault.seal_shard(
+        shard_ledger, dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=b"a-fixture-vault-secret",
+    )
+    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({sealed_meta["id"]})
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+
+    wf.run_diagnostic_walkforward(
+        ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None,
+        config=_FakeConfig(dataset_dir=str(tick_dir)),
+    )
+
+    tick_rows = [r for r in registry.all_rows() if r["corpus_id"] == wf.TICK_LEGACY_CORPUS_ID]
+    windows = {r["window"] for r in tick_rows}
+    assert windows == {"2026-06-09"}  # E's date only -- D's 2026-06-08 is honestly absent
+    assert len(tick_rows) == 1
+    assert tick_rows[0]["logged_at"] == R2_REVISION_INSTANT
+    assert unsealed_meta["symbol"] == "MSFT"  # sanity: E really is the unsealed one
+
+
+def test_tc11_d_stays_absent_from_a_later_seed_inspection_even_after_the_vault_exposes_it(tmp_path, monkeypatch):
+    """TC-11: exposing D through vault.py's OWN lifecycle (assign -> expose) does not retroactively
+    (or on a later inspection) inject its window into the WALKFORWARD registry's r2 seed for
+    TICK_LEGACY_CORPUS_ID -- that seed is guarded to run at most once per registry
+    (``has_any_exposure_entries``) regardless of vault state, so D's exposure lives ONLY in the
+    vault's own shard ledger (TC-7), never double-recorded here."""
+    signature = "sig-tc11"
+    sessions = [f"2026-11-{d:03d}" for d in range(1, 156)]
+    records = [
+        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
+        for s in sessions
+    ]
+    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
+    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+
+    tick_dir = tmp_path / "tick_datasets"
+    tick_store = DatasetStore(tick_dir)
+    sealed_meta = _plant_tick_dataset(
+        tick_store, symbol="AAPL", window_start_utc="2026-06-08T13:30:00Z", window_end_utc="2026-06-08T20:00:00Z"
+    )
+    _plant_tick_dataset(
+        tick_store, symbol="MSFT", window_start_utc="2026-06-09T13:30:00Z", window_end_utc="2026-06-09T20:00:00Z", price=101.00
+    )
+
+    shard_ledger = vault.shard_ledger_for_dataset_dir(str(tick_dir))
+    vault.seal_shard(
+        shard_ledger, dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=b"a-fixture-vault-secret",
+    )
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    config = _FakeConfig(dataset_dir=str(tick_dir))
+
+    wf.run_diagnostic_walkforward(ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None, config=config)
+    tick_rows_after_first_run = [r for r in registry.all_rows() if r["corpus_id"] == wf.TICK_LEGACY_CORPUS_ID]
+    assert {r["window"] for r in tick_rows_after_first_run} == {"2026-06-09"}
+
+    # NOW expose D through the vault's own one-way lifecycle.
+    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+    vault.assign_shard(shard_ledger, dataset_id=sealed_meta["id"], family_root_id=family_root, symbol="AAPL", session_date="2026-06-08")
+    vault.expose_shard(shard_ledger, dataset_id=sealed_meta["id"], family_root_id=family_root)
+    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset()  # D is no longer sealed
+
+    # a SECOND diagnostic run (the "later seed inspection") -- the once-only guard means the r2
+    # seed for TICK_LEGACY_CORPUS_ID never re-examines vault state at all, so D's window stays
+    # absent from THIS registry regardless of its now-exposed vault state.
+    wf.run_diagnostic_walkforward(ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None, config=config)
+    tick_rows_after_second_run = [r for r in registry.all_rows() if r["corpus_id"] == wf.TICK_LEGACY_CORPUS_ID]
+    assert tick_rows_after_second_run == tick_rows_after_first_run  # unchanged -- no re-seed, no D
+    assert "2026-06-08" not in {r["window"] for r in tick_rows_after_second_run}
+
+
+# === iter-9 audit B4 + T3: the tick-family corpus inventory honours the seal, and the r2 filter's
+# === disclosed granularity limit is pinned rather than left to drift silently
+
+
+def test_b4_the_tick_family_corpus_inventory_excludes_and_discloses_withheld_shards(tmp_path):
+    """Spec section 7.5 point 6 (r4): ``run_tick_family_fold_request`` enumerates the whole store
+    to size ``TICK_LEGACY_CORPUS_ID``, so a withheld shard would silently inflate the floor count
+    and the ``corpus_manifest_hash`` registered in the fold ledger (section 7.7 makes the legacy
+    corpus permanently disjoint from any sealed tranche). Below floor -- which is every call today
+    -- the typed refusal itself carries the disclosure, since it is all a caller ever sees."""
+    tick_dir = tmp_path / "tick_datasets"
+    tick_store = DatasetStore(tick_dir)
+    sealed_meta = _plant_tick_dataset(
+        tick_store, symbol="AAPL", window_start_utc="2026-06-08T13:30:00Z", window_end_utc="2026-06-08T20:00:00Z"
+    )
+    _plant_tick_dataset(
+        tick_store, symbol="MSFT", window_start_utc="2026-06-09T13:30:00Z", window_end_utc="2026-06-09T20:00:00Z", price=101.00
+    )
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    config = _FakeConfig(dataset_dir=str(tick_dir))
+
+    with pytest.raises(wf.InsufficientSessionsForFoldsError) as before:
+        wf.run_tick_family_fold_request(ledger, config)
+    assert str(before.value).startswith("2 < 105")  # both dates counted, no disclosure appended
+    assert "withheld" not in str(before.value)
+
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(tick_dir)),
+        dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=b"a-fixture-vault-secret",
+    )
+
+    with pytest.raises(wf.InsufficientSessionsForFoldsError) as after:
+        wf.run_tick_family_fold_request(ledger, config)
+    message = str(after.value)
+    assert message.startswith("1 < 105")  # the sealed shard's date no longer inflates the corpus
+    assert "excludes 1 withheld Validation-Vault shard(s)" in message  # ... and it SAYS so
+    assert sealed_meta["id"] not in message  # a count, never an id
+    assert ledger.all_rows() == []  # a request that never ran still writes nothing
+
+
+def test_b4_the_success_return_carries_the_withheld_count(tmp_path, monkeypatch):
+    """The floor-CLEARING half, monkeypatched exactly like TC-14 above so it stays hermetic: the
+    returned body carries the same disclosure the refusal does."""
+    fake_dates = [f"session-{i:04d}" for i in range(110)]
+    monkeypatch.setattr(
+        wf, "_tick_dataset_session_dates", lambda store, **_kwargs: (fake_dates, [])
+    )
+    tick_dir = tmp_path / "tick_datasets"
+    tick_store = DatasetStore(tick_dir)
+    sealed_meta = _plant_tick_dataset(
+        tick_store, symbol="AAPL", window_start_utc="2026-06-08T13:30:00Z", window_end_utc="2026-06-08T20:00:00Z"
+    )
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(tick_dir)),
+        dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=b"a-fixture-vault-secret",
+    )
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+
+    result = wf.run_tick_family_fold_request(ledger, _FakeConfig(dataset_dir=str(tick_dir)))
+
+    assert result["withheld_excluded"] == 1
+    assert result["session_count"] == 110
+
+
+def test_t3_a_sealed_shards_date_IS_still_seeded_when_an_unsealed_sibling_shares_it(tmp_path, monkeypatch):
+    """iter-9 audit finding T3 — pins the r2 filter's honestly DISCLOSED granularity limit (see
+    ``_tick_dataset_session_dates``' own docstring): the WALKFORWARD registry's unit is the DATE,
+    so the filter guarantees only "a sealed dataset contributes no date of its OWN". TC-10/TC-11
+    both give the sealed and unsealed shards DIFFERENT dates -- the only case where the stronger
+    reading holds. This is the shared-date case, asserted in the direction the code actually
+    behaves, so a future change in EITHER direction fails loudly instead of drifting."""
+    signature = "sig-t3"
+    sessions = [f"2026-12-{d:03d}" for d in range(1, 156)]
+    records = [
+        _fake_playbook_record(s, signature, [_fake_signal("range_trade", "AAPL", 0.3), _fake_signal("range_trade", "MSFT", 0.3)])
+        for s in sessions
+    ]
+    monkeypatch.setattr(wf, "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE", "2020-01-01")
+    monkeypatch.setattr(wf, "compute_playbook_input_signature", lambda bar_store, members, config_fingerprint: signature)
+
+    tick_dir = tmp_path / "tick_datasets"
+    tick_store = DatasetStore(tick_dir)
+    sealed_meta = _plant_tick_dataset(
+        tick_store, symbol="AAPL", window_start_utc="2026-06-09T13:30:00Z", window_end_utc="2026-06-09T20:00:00Z"
+    )
+    # the SHARED-DATE sibling: same ET session date, a different symbol, not sealed
+    _plant_tick_dataset(
+        tick_store, symbol="MSFT", window_start_utc="2026-06-09T13:30:00Z", window_end_utc="2026-06-09T20:00:00Z", price=101.00
+    )
+    shard_ledger = vault.shard_ledger_for_dataset_dir(str(tick_dir))
+    vault.seal_shard(
+        shard_ledger, dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
+        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=b"a-fixture-vault-secret",
+    )
+
+    ledger = wl.WalkForwardLedger(str(tmp_path / "wf"))
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    wf.run_diagnostic_walkforward(
+        ledger, registry, _FakePlaybookStore(records), _FakeUniverseStore(["AAPL"]), bar_store=None,
+        config=_FakeConfig(dataset_dir=str(tick_dir)),
+    )
+
+    tick_rows = [r for r in registry.all_rows() if r["corpus_id"] == wf.TICK_LEGACY_CORPUS_ID]
+    # the date IS seeded -- through the UNSEALED sibling's own contribution, not the sealed shard's
+    assert {r["window"] for r in tick_rows} == {"2026-06-09"}
+    assert len(tick_rows) == 1  # exactly one entry: a date is seeded once, whoever contributed it
diff --git a/docs/goal.md b/docs/goal.md
index 2433f05..4a5031f 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -564,9 +564,10 @@ operator-attended act inside the era.
        the published sha256 split beside the HMAC seal assignment
        (`TAPEOLOGY_VAULT_SECRET_FILE`, commitment recorded), one-way
        `sealed → assigned → exposed` exposure ledger keyed on the computed `family_root_id`,
-       **opaque pre-exposure metadata (spec §7.5 r2: no symbol, no date range until
-       assignment — aggregates only on readiness)**, TR-2 route sweep, TR-4 cherry-pick
-       refusal, TR-12 single-shot exposure, TR-20 root-lineage refusal.
+       **opaque pre-exposure metadata (spec §7.5 r3: surrogate shard id, salted commitment,
+       no symbol/date until assignment, sealed dataset ids refused on the dataset + MCP
+       surfaces — aggregates only on readiness)**, TR-2 join-resistance sweep, TR-4
+       cherry-pick refusal, TR-12 single-shot exposure, TR-20 root-lineage refusal.
     4. Operator act, inside the era: resolve Tier-B by the spec §7.2 mandatory order (screen
        by the frozen Card-5.2 criteria → record criteria hash, as-of, provenance, full output,
        resolved list → freeze the list → `symbol_rule` → register the universe → commitment +
diff --git a/docs/rapid-validation-spec.md b/docs/rapid-validation-spec.md
index 12a338b..6f66625 100644
--- a/docs/rapid-validation-spec.md
+++ b/docs/rapid-validation-spec.md
@@ -23,6 +23,35 @@
 > registry + human/agent rules for `historical_oos` (§6.7); `rule_process` vs
 > `operator_process` sequence labels (§6.8); frozen clustering semantics and the explicit
 > `WF_SURVIVOR_RULE_V1` (§6.2/§6.6); and traps TR-17–TR-22 (§9).
+>
+> **Revision r3 (2026-08-18, owner ruling — sealed-shard join resistance).** A narrow named
+> revision applied while ZERO shards are sealed, so nothing re-keys and no recorded verdict
+> moves. The iteration-9 audit proved r2's §7.5 opacity is defeated in one hop: the served
+> `shard_id` was the `DatasetStore` dataset id, so `GET /research/datasets/{id}` (and the
+> `datasets` MCP tool, `get_endpoint`, and `micro_readiness`'s per-shard rows) returned the
+> sealed shard's symbol, window and event counts. r2 already REQUIRED an "opaque `shard_id`",
+> so that part was a compliance gap, not a spec gap — but r2 also MANDATED serving the
+> `checksum commitment`, which is itself an equally good join key against the public dataset
+> record. Resolving that tension is a genuine methodological change, hence this revision.
+> r3 replaces §7.5's identity rules (surrogate ids, salted pre-exposure commitment, explicit
+> refusal on the pre-existing dataset surfaces) and widens TR-2 from a field-whitelist sweep to
+> a join-resistance sweep. Owner ruling recorded 2026-08-18; the alternatives considered and
+> rejected were a separate sealed store path (strongest, largest build) and accepting the leak
+> with a documented caveat (cheapest, materially weaker vault).
+>
+> **Revision r4 (2026-08-18, owner ruling — corpus enumerators honour the seal).** Applied while
+> ZERO shards are sealed, so no recorded report or ledger row changes. The iteration-9 re-audit
+> proved r3's refusals are route-scoped and therefore bypassable: `edge_report._all_datasets`
+> and `pnl_scan._split_datasets` each enumerate the WHOLE store through their own
+> `DatasetStore.list()` and drive `BacktestJobManager` directly, so a corpus-wide report would
+> read a sealed shard's events and republish its id, raw checksum and outcome aggregates through
+> `GET /research/backtests` and the append-only PnL ledger. r4 adds §7.5 point 6: enumerators
+> EXCLUDE withheld shards and DISCLOSE the exclusion. This is a derivation, not a free choice —
+> goal.md's critical rail already says event data and outcome aggregates of a sealed shard are
+> "refused everywhere… fail-closed", and both call sites already carry the honesty convention
+> that "a partial report is a misleading report", which forbids the silent variant. Rejected:
+> aborting a whole sweep whenever any sealed shard exists (renders the edge report unusable the
+> moment the vault holds anything) and accepting the bypass (re-opens exactly what r3 closed).
 
 ---
 
@@ -462,16 +491,49 @@ root-family-level and single-shot**: a renamed or re-parameterized family comput
 root and can never treat the same shard as fresh, and a failed sealed verdict is a permanent
 root-family fact carried in every later export bundle (TR-12, TR-20).
 
-### 7.5 Sealed metadata minimization — OPAQUE pre-exposure (r2)
-While sealed, a shard serves only: an opaque `shard_id`, its `universe_id`, a coarse size
-bucket (order of magnitude), the checksum commitment, `sealed_at`, and the exposure state.
+### 7.5 Sealed metadata minimization — OPAQUE pre-exposure (r3)
+While sealed, a shard serves only: a surrogate `shard_id`, its `universe_id`, a coarse size
+bucket (order of magnitude), a **salted** commitment, `sealed_at`, and the exposure state.
 **Symbol and date range are NOT served pre-exposure** — they would let bar-level public
 outcomes (desk/playbook, served for every date) be looked up against sealed membership; both
 are revealed at ASSIGNMENT and recorded in the exposure ledger. Exact event counts, bytes, and
-any feature/outcome aggregate are withheld until exposure (TR-2 sweeps every registered route,
-closing the `get_endpoint` path structurally). Readiness serves sealed-tranche AGGREGATES only
-(shard count, total symbol-days, per-universe totals), never per-shard identity. Recorder run
-logs commit per-shard identity and counts by hash while sealed.
+any feature/outcome aggregate are withheld until exposure.
+
+**Join resistance is the actual requirement (r3).** Field-level minimization is not enough: a
+served value that merely *identifies* the shard on another surface leaks everything that
+surface serves. Therefore:
+
+1. **Surrogate identity.** The served `shard_id` is a vault-minted opaque token bearing no
+   derivable relation to the `DatasetStore` dataset id (not the id, not a hash of it, not a
+   prefix). The surrogate → dataset-id mapping lives only in the sealed-side ledger and is
+   revealed at assignment.
+2. **Salted commitment.** The pre-exposure commitment is `HMAC(vault_secret, content_checksum)`
+   — not the raw `content_checksum`, which is served publicly per dataset and would join
+   directly. The raw checksum is revealed at exposure, at which point the salted commitment can
+   be re-derived and verified against it, preserving auditability.
+3. **Refusal on the pre-existing surfaces.** `GET /research/datasets` / `/research/datasets/{id}`,
+   the `datasets` MCP tool, and any `get_endpoint` path resolving to them REFUSE a sealed
+   dataset id with a typed refusal until its exposure is recorded. The refusal states only that
+   the id is sealed — never symbol, window, counts, or universe.
+4. **Readiness serves sealed-tranche AGGREGATES only** (shard count, total symbol-days,
+   per-universe totals) — never a per-shard row, never a per-shard `exposure_state`.
+5. Recorder run logs commit per-shard identity and counts by hash while sealed.
+6. **Corpus enumerators honour the seal (r4).** A refusal wired only into a route is bypassed by
+   any module that enumerates the store itself. Therefore every corpus-wide enumerator —
+   `edge_report._all_datasets`, `pnl_scan._split_datasets`, the Scout's corpus manifest, the
+   snapshot builder and its compute manager, and any future sibling — EXCLUDES withheld shards
+   (state ≠ `exposed`) at its single `DatasetStore.list()` choke point, and **DISCLOSES the
+   exclusion**: a `withheld_excluded` count (never the ids) travels into the report body and
+   into any append-only row the run writes. Silent exclusion is forbidden — these call sites
+   already hold that "a partial report is a misleading report", and the era's denominator rail
+   forbids a corpus that shrinks without saying so. A run whose entire eligible corpus is
+   withheld reports that honestly rather than emitting an empty-but-shaped result.
+
+No pre-exposure field may equal, contain, or be derivable from any field the public surfaces
+serve for the same shard, and no exploratory statistic may be computed from one. TR-2 proves
+this by construction, not by whitelist review — and it exercises the operator compute acts
+(snapshot build, Scout run, edge report, PnL sweep) BEFORE sweeping, so it cannot pass merely
+because the rig computed nothing.
 
 ### 7.6 The starter tranche (this era's recording acceptance)
 Minimums (all must hold): ≥30 symbol-days; ≥8 distinct Card-5.2-panel symbols including `PG`,
@@ -527,7 +589,7 @@ No state ever moves backward except by a voiding event (§6.2), which is itself
 | Trap | Asserts |
 |---|---|
 | TR-1 prefix/tail | Truncated-dataset snapshot rows byte-identical to the full run's prefix (3 cut points incl. i=1); appending one tail event changes no prior row |
-| TR-2 sealed sweep | Every registered route + MCP tool serves only §7.5 metadata (or refusal) for a sealed shard |
+| TR-2 sealed sweep (r3: join-resistance) | Every registered route + MCP tool serves only §7.5 metadata (or a typed refusal) for a sealed shard — AND the sweep is adversarial, not a whitelist review: seal a fixture shard, collect every value any surface serves for it pre-exposure, and assert none equals, contains, or derives the dataset id, raw `content_checksum`, symbol, window, or event counts. Explicitly includes `/research/datasets{,/{id}}`, the `datasets` MCP tool, `get_endpoint`, and `micro_readiness` (which must expose no per-shard row at all) |
 | TR-3 accessor fence | Origin-T accessor refuses reads > T with a typed error; corpus aggregates exclude > T exactly; import-ban: only `micro_accessor` opens snapshot/vault data paths |
 | TR-4 cherry-pick refusal | A recording batch ≠ its universe rule's computed set (net of disclosed failures) is refused |
 | TR-5 class mixing | Pooling `historical_exposed_diagnostic` with `historical_oos` rows in one statistic is refused; diagnostic folds contribute zero to graduation |
diff --git a/apps/backend/app/research/vault.py b/apps/backend/app/research/vault.py
new file mode 100644
index 0000000..30bf52c
--- /dev/null
+++ b/apps/backend/app/research/vault.py
@@ -0,0 +1,837 @@
+"""``vault.py`` -- Era "The Rapid Microscope" J-06 step 3 (``docs/rapid-validation-spec.md``
+section 7.2-7.5): pre-registered recording universes (rule-hash committed BEFORE any fetch), the
+split/seal dual assignment (the opaque HMAC seal axis, NEW and independent of
+``tick_recorder.recorder_split_for``'s own published split rule -- this module never reimplements
+that rule; it only adds the seal axis), and the one-way ``sealed -> assigned -> exposed``
+shard-lifecycle ledger keyed on the COMPUTED ``family_root_id`` (imported from
+``scout_ledger.compute_family_root_id``, never reimplemented -- TR-20 depends on there being
+exactly one identity function).
+
+**Two distinct ledgers, per the phase spec's own naming (T-2 vocabulary trap).** ``VaultUniverseLedger``
+(recording-universe registrations: ``{universe_id, symbol_rule, date_rule, registered_at,
+rule_hash, vault_secret_commitment}``) and ``VaultShardLedger`` (the shard-lifecycle
+``sealed -> assigned -> exposed`` transitions) are TWO separate ``micro_chain_ledger.
+HashChainedLedger`` instances -- the ``walkforward_ledger.WalkForwardLedger`` "thin domain wrapper
+over ONE HashChainedLedger" shape, built here TWICE (module docstring precedent: "once per
+ledger"), never a fourth hash-chain implementation and never one ledger pretending to be two.
+Neither of these is the WALKFORWARD ``ExposureRegistry`` (``micro_accessor.py``, section 6.7) --
+that ledger tracks whether a (corpus, session-window) has ever been SERVED; this module's shard
+ledger tracks whether a (family, shard) has ever been ASSIGNED/EXPOSED. The two interact (see
+``currently_sealed_dataset_ids`` below, the bridge ``walkforward.py`` calls) but are never the same
+file, the same identity key, or the same vocabulary.
+
+**A vault "shard" IS a ``DatasetStore`` dataset -- but its SERVED identity is a surrogate (spec
+section 7.5, revision r3).** The recorder (``tick_recorder.py``) finalizes exactly one dataset per
+recorded symbol-day, and this module keys every ledger row and every lifecycle guard on that
+dataset's own ``id`` (``dataset_id`` -- the SAME identity ``micro_readiness.py``'s per-shard
+``dataset_id`` field and ``micro_accessor.MicroAccessor``'s ``sealed_dataset_ids: frozenset[str]``
+parameter already use; no second shard-identity scheme is invented here). What is SERVED while the
+shard is still sealed is NOT that id: it is ``shard_id``, a vault-minted surrogate
+(``compute_surrogate_shard_id``) bearing no publicly derivable relation to the dataset id, whose
+mapping back to the dataset id lives only in this module's own sealed-side ledger and is revealed
+at ASSIGNMENT.
+
+**Why the surrogate exists (iter-9 audit finding B1, closed by the owner's r3 ruling).** Serving the
+raw dataset id (and the raw ``content_checksum``) pre-exposure defeated section 7.5's whole purpose
+even though the served FIELD LIST was correct: either value joins in one hop to
+``GET /research/datasets/{id}`` / ``GET /research/datasets`` / the ``datasets`` MCP tool /
+``get_endpoint`` / ``micro_readiness``, each of which serves the shard's symbol, session date and
+exact event counts -- precisely what section 7.5 withholds. Field-level minimization is therefore
+not enough; JOIN RESISTANCE is the actual requirement (r3), and it is met here in three parts:
+
+1. the surrogate ``shard_id`` above;
+2. a SALTED commitment ``HMAC(vault_secret, content_checksum)`` (``commit_content_checksum``)
+   instead of the raw checksum, which is itself served publicly per dataset and would join
+   directly -- the raw checksum is revealed at EXPOSURE, at which point the salted commitment can
+   be re-derived from it and verified, so auditability survives intact; and
+3. a seal-aware REFUSAL on the pre-existing public surfaces, keyed on ``withheld_dataset_ids``
+   below (``routes.py``'s dataset list/detail + backtest-creation routes, and
+   ``micro_readiness.build_readiness``'s per-shard rows -- the MCP ``datasets`` tool and
+   ``get_endpoint`` inherit it structurally, being byte-identical GET proxies of those same
+   routes); and
+4. a COMMITTED (not published) universe rule while any of that universe's shards is still
+   withheld (``_serialize_universe``) -- iter-9 audit (third pass) finding B1. Parts 1-3 close
+   every per-shard join, but the universe rule is the tranche's own COMPLEMENT: TR-4 requires the
+   recorded batch to be exactly ``symbol_rule x date_rule`` net of disclosed failures, so
+   publishing those two lists beside a ``GET /research/datasets`` that omits precisely the sealed
+   rows lets any reader compute ``sealed = expected - served`` and de-anonymise the whole sealed
+   tranche by set subtraction -- defeating section 7.3's stated guarantee that "sealed membership
+   cannot be inferred from public information before exposure". So the rule lists follow the SAME
+   commit-then-reveal discipline part 2 applies to ``content_checksum``: ``rule_hash`` (already
+   computed at registration) is served throughout, the raw lists only once every shard of that
+   universe has reached ``exposed``. Section 7.2's requirement is that the rule be RECORDED in the
+   vault ledger before any fetch -- unchanged here, and ``find_universe``/the TR-4 verifier still
+   read it verbatim from that ledger, so nothing about the batch check or its auditability moves.
+
+TR-2 proves this by construction rather than by whitelist review (``tests/test_vault.py``'s
+adversarial join-resistance sweep over every registered GET route).
+
+**The single-shot discipline (TR-12) is shard-GLOBAL, not merely (family, shard)-scoped -- a
+disclosed interpretation call (T-1).** Spec section 7.4 says assignment "binds ONE candidate
+family LINE to the shard" -- read here as: once a shard leaves ``sealed``, it belongs to exactly
+ONE family for the rest of its history; a second ``assign_shard``/``expose_shard`` call for that
+shard is refused regardless of which ``family_root_id`` it names (``ShardLifecycleOrderError``).
+This is the STRICTER of the two readings the sentence admits (the looser one would scope the
+refusal to the exact (family_root_id, dataset_id) pair and allow a different, unrelated family to
+claim the same shard while it is still merely ``assigned``) -- chosen because a shard's content is
+no longer meaningfully "sealed" for a second family once a first family has been bound to it, and
+because every scenario TC-1..TC-9 actually exercises passes identically under either reading (the
+stricter rule can only refuse a superset of what the looser one would). Logged here rather than
+silently assumed, per this module's own T-1 discipline; nothing about it can widen without a
+plan-owner decision, since narrowing a refusal after real sealed evidence exists would not be safe
+to reverse. The iter-9 audit reviewed this call (its observation O1) and sided with it; the owner
+ruling is still open, so ``test_vault.py``'s ``test_audit_t1_...`` now PINS the stricter behaviour
+(the audit's own finding T1) so it cannot regress silently while that ruling is pending.
+
+**Expected recording set = the cartesian product of ``symbol_rule`` x ``date_rule`` (a second
+disclosed interpretation call).** Spec section 7.2 calls both "explicit" (the panel list, the date
+range/rule) and requires them FULLY RESOLVED before registration (the Tier-B resolution order,
+section 7.2: the resolved list is frozen BEFORE ``register_universe`` is ever called) -- so by the
+time this module ever sees them, both are already concrete ``list[str]``s, and "the rule's own
+computed output" is unambiguously every (symbol, date) pair between them, the exact shape
+``tick_recorder.plan_recorder_chunks(symbols, dates)`` already walks for real fetches (no second,
+diverging notion of "the universe's expected batch").
+
+**The vault secret never enters a row, a log line, or this module's own return values in raw
+form.** ``load_vault_secret`` reads it once from the path named by ``TAPEOLOGY_VAULT_SECRET_FILE``
+(a genuinely NEW env var -- no existing "_SECRET_FILE" precedent in this codebase) and returns raw
+bytes to the CALLER only; ``register_universe`` accepts only a pre-computed
+``vault_secret_commitment`` string (``commit_vault_secret``'s own output), and ``seal_shard`` --
+the one other function that must hold the raw secret, since r3's surrogate and salted commitment
+are both keyed on it -- consumes it ONLY as an argument to the two HMAC helpers and writes neither
+it nor anything reversible to it into the row it appends. A missing or unreadable secret file is
+``VaultSecretUnavailable`` -- typed, never a crash, never a fabricated default secret (TC-5).
+
+**Storage -- no new ``Config`` field.** ``resolve_vault_dir`` mirrors ``scout_ledger.
+resolve_scout_ledger_dir`` exactly: ``TAPEOLOGY_MICRO_VAULT_DIR`` if set, else a ``micro_vault``
+SIBLING of the caller's own already-resolved dataset directory (the ``TAPEOLOGY_MICRO_*`` family,
+goal.md Constraints)."""
+
+from __future__ import annotations
+
+import hashlib
+import hmac
+import json
+import math
+import os
+from datetime import datetime, timezone
+from pathlib import Path
+
+from .micro_chain_ledger import HashChainedLedger
+from .scout_ledger import compute_family_root_id
+
+__all__ = [
+    "VAULT_SEAL_HEX_BELOW",
+    "SURROGATE_SHARD_ID_PREFIX",
+    "STATE_SEALED",
+    "STATE_ASSIGNED",
+    "STATE_EXPOSED",
+    "VaultUniverseNotRegisteredError",
+    "VaultUniverseAlreadyRegisteredError",
+    "CherryPickedBatchError",
+    "VaultSecretUnavailable",
+    "ShardLifecycleOrderError",
+    "SealedShardWithheldError",
+    "resolve_vault_dir",
+    "shard_ledger_for_dataset_dir",
+    "VaultUniverseLedger",
+    "VaultShardLedger",
+    "compute_rule_hash",
+    "register_universe",
+    "find_universe",
+    "expected_recording_pairs",
+    "verify_recording_batch",
+    "verify_universe_recording_batch",
+    "load_vault_secret",
+    "commit_vault_secret",
+    "compute_seal",
+    "compute_surrogate_shard_id",
+    "commit_content_checksum",
+    "seal_shard",
+    "assign_shard",
+    "expose_shard",
+    "currently_sealed_dataset_ids",
+    "withheld_dataset_ids",
+    "withheld_universe_by_dataset_id",
+    "build_vault_state",
+    "compute_family_root_id",
+    "RULE_DISCLOSURE_COMMITTED",
+    "RULE_DISCLOSURE_REVEALED",
+]
+
+# docs/rapid-validation-spec.md section 1, transcribed verbatim -- NEVER a Config field (every
+# rapid-microscope constant is a plain module constant embedded in the era's own parameters
+# discipline; this module has no persisted "parameters" record of its own to embed it in, since
+# nothing here is a research MEASUREMENT -- the seal decision is auditable directly from the
+# committed secret hash instead).
+VAULT_SEAL_HEX_BELOW = 4
+
+# The served surrogate id's fixed prefix (spec section 7.5 r3). Deliberately NOT the 32-hex shape
+# a `DatasetStore` id has, so a surrogate can never be mistaken for -- or accidentally passed as --
+# a dataset id by a reader, a log line, or a future UI.
+SURROGATE_SHARD_ID_PREFIX = "vshard-"
+
+# Domain-separation labels for the two secret-keyed derivations below, so the surrogate id and the
+# checksum commitment can never collide even if some caller ever fed the identical input string to
+# both (the standard HMAC domain-separation discipline; each is versioned so a future scheme change
+# is a distinguishable v2, never a silent redefinition).
+_SURROGATE_LABEL = "vault-shard-surrogate-v1:"
+_CHECKSUM_COMMITMENT_LABEL = "vault-checksum-commitment-v1:"
+
+# The one-way lifecycle's three states (module docstring T-2: this module's OWN vocabulary,
+# distinct from micro_readiness.py's EXPOSURE_STATE_EXPLORATORY/SPLIT_PROVENANCE_HAND_ASSIGNED).
+STATE_SEALED = "sealed"
+STATE_ASSIGNED = "assigned"
+STATE_EXPOSED = "exposed"
+
+# The universe rule's two serving stages (module docstring's join-resistance part 4). A DIFFERENT
+# vocabulary from the shard lifecycle above on purpose: a universe has no lifecycle of its own --
+# its rule's disclosure is a pure function of whether every shard it owns has reached `exposed`.
+RULE_DISCLOSURE_COMMITTED = "committed"
+RULE_DISCLOSURE_REVEALED = "revealed"
+
+_VAULT_DIR_ENV = "TAPEOLOGY_MICRO_VAULT_DIR"
+_VAULT_SECRET_FILE_ENV = "TAPEOLOGY_VAULT_SECRET_FILE"
+
+_UNIVERSE_LEDGER_FILENAME = "vault_universe_ledger.jsonl"
+_SHARD_LEDGER_FILENAME = "vault_shard_ledger.jsonl"
+
+# Ledger-machinery keys ``HashChainedLedger.append_row`` itself manages -- stripped before a row's
+# OWN content is carried forward into a later row (``assign_shard``/``expose_shard`` below), so a
+# re-appended row is never confused with the raw ledger internals of the row it was built from.
+_LEDGER_INTERNAL_KEYS = ("row_hash", "prev_hash", "row_index")
+
+# The opaque, sealed-safe projection (spec section 7.5) -- the ONLY keys ever served for a shard
+# still in `sealed` state (TC-6). Listed once here so `_serialize_shard` cannot silently drift from
+# what `seal_shard` actually writes.
+_OPAQUE_SHARD_KEYS = ("shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state")
+
+
+class VaultUniverseNotRegisteredError(Exception):
+    """TC-1: a recording batch was asked to validate against a ``universe_id`` with no registered
+    rule -- refused, never a silent pass and never an invented default rule."""
+
+
+class VaultUniverseAlreadyRegisteredError(Exception):
+    """iter-9 audit fix B2: spec section 7.2 FREEZES a universe's rule at registration ("After
+    universe registration: no Tier-B re-screen, no substitution because a symbol is inconvenient,
+    no replacement from vendor availability or observed data"). A second registration of the SAME
+    ``universe_id`` under a different rule (or a different secret commitment) is therefore refused
+    -- without this, TR-4's cherry-pick refusal is fully evadable: re-register the inconvenient
+    symbol out of ``symbol_rule`` and the exact batch that was just refused validates, because
+    ``find_universe`` resolves to the LATEST row."""
+
+    def __init__(self, universe_id: str, registered_rule_hash: str, attempted_rule_hash: str) -> None:
+        self.universe_id = universe_id
+        self.registered_rule_hash = registered_rule_hash
+        self.attempted_rule_hash = attempted_rule_hash
+        super().__init__(
+            f"universe {universe_id!r} is already registered under rule_hash "
+            f"{registered_rule_hash!r} -- a registered universe rule is frozen (spec section 7.2) "
+            f"and can never be re-registered as {attempted_rule_hash!r}; record the shortfall as a "
+            "DISCLOSED per-symbol failure in the batch report instead (TR-4)"
+        )
+
+
+class CherryPickedBatchError(Exception):
+    """TR-4/TC-3: a recording batch's (symbol, date) set differs from its universe rule's own
+    computed set net of disclosed failures -- refused, naming the specific missing/unexpected
+    entries."""
+
+
+class VaultSecretUnavailable(Exception):
+    """TC-5: ``TAPEOLOGY_VAULT_SECRET_FILE`` is unset, or the path it names cannot be read, or is
+    empty -- a typed configuration refusal, never a crash and never a fabricated default secret."""
+
+
+class ShardLifecycleOrderError(Exception):
+    """TR-12/TC-8: a shard-lifecycle transition was attempted out of the one-way
+    ``sealed -> assigned -> exposed`` order -- either skipping a step or repeating one already
+    recorded (single-shot, shard-global -- module docstring).
+
+    Operator-side only: this message names the real ``dataset_id`` (the transitions are keyed on
+    it), and no route in this codebase invokes a transition, so it never reaches a public payload.
+    A future operator-facing seal/assign/expose route must NOT surface it verbatim to an
+    unauthenticated caller -- use ``SealedShardWithheldError`` below for anything served."""
+
+    def __init__(self, dataset_id: str, expected_state: str | None, actual_state: str | None) -> None:
+        self.dataset_id = dataset_id
+        self.expected_state = expected_state
+        self.actual_state = actual_state
+        super().__init__(
+            f"shard {dataset_id!r} is not eligible for this transition: expected its latest "
+            f"recorded state to be {expected_state!r}, found {actual_state!r} -- the one-way "
+            "sealed -> assigned -> exposed lifecycle refuses any transition taken out of order "
+            "or repeated for a shard already past it (TR-12)"
+        )
+
+
+class SealedShardWithheldError(Exception):
+    """spec section 7.5 point 3 (r3): a public surface was asked for a dataset whose vault shard has
+    not yet reached ``exposed``. The refusal states ONLY that the id is sealed -- never the symbol,
+    the window, the counts, or even the universe (each of which would re-open the join this refusal
+    exists to close). ``routes.py`` serves ``str(exc)`` as its HTTP 403 detail, so there is exactly
+    ONE wording of this refusal in the codebase.
+
+    The message does not echo the ``dataset_id`` either. Repeating an id the caller just supplied
+    discloses nothing NEW -- but TR-2's sweep is written as an absolute ("this id appears in no
+    response body of any route"), and a message that quotes it back would force that trap to carry
+    a carve-out. An assertion with no exceptions is worth more than a marginally friendlier error,
+    so the id stays available programmatically (``exc.dataset_id``) and out of the wire."""
+
+    def __init__(self, dataset_id: str) -> None:
+        self.dataset_id = dataset_id
+        super().__init__(
+            "this dataset is sealed in the validation vault -- its metadata is withheld until "
+            "its exposure is recorded (spec section 7.5)"
+        )
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding this module hashes -- the identical sorted-keys,
+    no-whitespace shape every sibling ledger in this codebase hashes (``scout_ledger.py``,
+    ``micro_chain_ledger.py``, ...)."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256_hex(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def resolve_vault_dir(dataset_dir_resolved: str) -> str:
+    """``TAPEOLOGY_MICRO_VAULT_DIR`` if set, else a ``micro_vault`` SIBLING of the caller's
+    already-resolved dataset directory -- the ``resolve_scout_ledger_dir`` pattern verbatim."""
+    override = os.environ.get(_VAULT_DIR_ENV)
+    if override:
+        return override
+    return str(Path(dataset_dir_resolved).parent / "micro_vault")
+
+
+def shard_ledger_for_dataset_dir(dataset_dir_resolved: str) -> "VaultShardLedger":
+    """The shard-lifecycle ledger for a caller that knows only its dataset directory -- the ONE
+    resolver every non-vault consumer of this module's state shares (``routes.py``'s refusal
+    dependency, ``micro_readiness.build_readiness``, ``walkforward.py``'s r2-seed sealed filter),
+    so there can never be two vault locations answering "which shards are sealed" differently."""
+    return VaultShardLedger(resolve_vault_dir(dataset_dir_resolved))
+
+
+# === the two ledgers (module docstring: "once per ledger") =========================================
+
+
+class VaultUniverseLedger:
+    """A thin domain wrapper over ONE ``HashChainedLedger`` -- every registered recording
+    universe, in append order. Enforces no business rule of its own (the ``ScoutLedger``/
+    ``WalkForwardLedger`` split); ``register_universe``/``find_universe`` below are the validated
+    entry points every caller uses."""
+
+    def __init__(self, root_dir: str) -> None:
+        self._chain = HashChainedLedger(root_dir, _UNIVERSE_LEDGER_FILENAME)
+
+    def verify_chain(self) -> dict:
+        return self._chain.verify_chain()
+
+    def all_rows(self) -> list[dict]:
+        return self._chain.all_rows()
+
+    def append_row(self, fields: dict) -> dict:
+        return self._chain.append_row(fields)
+
+
+class VaultShardLedger:
+    """A thin domain wrapper over ONE ``HashChainedLedger`` -- every shard-lifecycle transition
+    (``sealed``/``assigned``/``exposed`` rows, one global chain, discriminated by each row's own
+    ``exposure_state`` -- the ``WalkForwardLedger`` "one global chain, several row kinds"
+    precedent). ``seal_shard``/``assign_shard``/``expose_shard`` below are the validated entry
+    points every caller uses."""
+
+    def __init__(self, root_dir: str) -> None:
+        self._chain = HashChainedLedger(root_dir, _SHARD_LEDGER_FILENAME)
+
+    def verify_chain(self) -> dict:
+        return self._chain.verify_chain()
+
+    def all_rows(self) -> list[dict]:
+        return self._chain.all_rows()
+
+    def append_row(self, fields: dict) -> dict:
+        return self._chain.append_row(fields)
+
+
+# === universe registration (spec section 7.2) =======================================================
+
+
+def compute_rule_hash(symbol_rule: list[str], date_rule: list[str]) -> str:
+    """A pure content hash over the resolved, explicit ``symbol_rule``/``date_rule`` lists --
+    excludes any wall-clock-derived value (``registered_at`` is never part of this), so two
+    genuinely separate registration acts of the IDENTICAL rule compute the identical hash (the
+    ``scout_ledger.compute_spec_hash`` precedent, TC-2)."""
+    return _sha256_hex(_canonical({"symbol_rule": list(symbol_rule), "date_rule": list(date_rule)}))
+
+
+def register_universe(
+    ledger: VaultUniverseLedger,
+    *,
+    universe_id: str,
+    symbol_rule: list[str],
+    date_rule: list[str],
+    vault_secret_commitment: str,
+    registered_at: str | None = None,
+) -> dict:
+    """Freezes a recording universe's rule (spec section 7.2): ``{universe_id, symbol_rule,
+    date_rule, registered_at, rule_hash, vault_secret_commitment}``. ``vault_secret_commitment`` is
+    ``commit_vault_secret``'s own output (``sha256(vault_secret).hexdigest()``) -- this function
+    never sees, accepts, or persists the raw secret itself (module docstring; TC-5).
+
+    **The freeze is ENFORCED, not merely documented (iter-9 audit fix B2).** Section 7.2's "no
+    substitution because a symbol is inconvenient" is a rule about the universe_id's WHOLE history,
+    not just its first row, so a second registration of the same ``universe_id`` is:
+
+    * an idempotent no-op returning the EXISTING row (no second ledger row) when the rule and the
+      secret commitment are byte-identical -- a crash-retry of the one operator registration act
... [diff_bound] apps/backend/app/research/vault.py: 443 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_vault.py b/apps/backend/tests/test_vault.py
new file mode 100644
index 0000000..84aaa98
--- /dev/null
+++ b/apps/backend/tests/test_vault.py
@@ -0,0 +1,1236 @@
+"""``vault.py`` (Era "The Rapid Microscope" J-06 step 3) -- test-first contract: TC-1 through
+TC-9 plus TR-2/4/12/20, per ``docs/phases/goal-rapid-microscope-iter-9.md``. Mirrors
+``test_scout_ledger.py``'s own split: most of these tests exercise the ledger's own primitives
+directly over a throwaway ``tmp_path`` (no ``DatasetStore``/snapshot machinery needed for those --
+a vault shard's ``dataset_id``/``content_checksum`` are opaque strings as far as this module's own
+logic is concerned); the route-level tests load the already-committed hermetic PG fixtures (the
+``test_scout_ledger._combined_fixture_store`` precedent) to prove the whole stack -- real dataset
+metadata through ``seal_shard`` through every registered GET route -- end to end.
+
+**TR-2 is an ADVERSARIAL JOIN-RESISTANCE SWEEP (spec section 7.5/section 9, revision r3), not a
+whitelist review** -- see ``test_tr2_...`` at the bottom of this file. The iter-9 audit's finding
+B1 showed why: the served field LIST can be perfectly minimal and the guarantee still be defeated,
+because a served value that merely IDENTIFIES the shard on another surface leaks everything that
+surface serves. So the sweep seals a real fixture shard, calls every registered GET route, and
+asserts that nothing anywhere equals, contains, or derives that shard's dataset id, raw
+``content_checksum``, symbol, window bounds or exact event counts -- and then executes the join
+attack itself, feeding every value the vault DOES serve back into the dataset routes."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import shutil
+import time
+from pathlib import Path
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.main import app
+from app.providers.base import QuoteEvent, Side, TradeEvent
+from app.research import vault
+from app.research.datasets import DatasetStore
+from app.research.scout_ledger import compute_family_root_id as _scout_compute_family_root_id
+
+_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "datasets"
+
+# The one fixture secret every lifecycle test in this file keys its HMACs on. A literal, never the
+# operator's real `TAPEOLOGY_VAULT_SECRET_FILE` -- no test in this repo ever reads that file.
+_FIXTURE_SECRET = b"a-fixture-vault-secret"
+
+
+def _write_secret_file(tmp_path: Path, content: str = "correct-horse-battery-staple") -> str:
+    path = tmp_path / "vault_secret.txt"
+    path.write_text(content)
+    return str(path)
+
+
+# === no reimplementation: this module reuses scout_ledger's own identity function verbatim ==========
+
+
+def test_compute_family_root_id_is_the_same_function_object_scout_ledger_exports():
+    """TR-20 depends on there being exactly one identity function -- proven directly, not merely
+    by matching output, so a future accidental local reimplementation is caught immediately."""
+    assert vault.compute_family_root_id is _scout_compute_family_root_id
+
+
+# === TC-1/TC-2: universe registration + the rule_hash round trip ====================================
+
+
+def test_tc1_an_unregistered_universe_id_refuses_batch_validation(tmp_path):
+    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    with pytest.raises(vault.VaultUniverseNotRegisteredError, match="never-registered-universe"):
+        vault.verify_universe_recording_batch(
+            ledger, "never-registered-universe", recorded=[("PG", "2026-06-09")]
+        )
+
+
+def test_tc2_a_registered_universe_round_trips_its_rule_hash_exactly(tmp_path):
+    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    symbol_rule = ["PG", "AAPL"]
+    date_rule = ["2026-06-08", "2026-06-09"]
+    commitment = vault.commit_vault_secret(b"a-fixture-secret")
+
+    row = vault.register_universe(
+        ledger, universe_id="starter-tranche-v1", symbol_rule=symbol_rule, date_rule=date_rule,
+        vault_secret_commitment=commitment,
+    )
+    assert row["registered_at"] is not None
+    assert row["rule_hash"] == vault.compute_rule_hash(symbol_rule, date_rule)
+
+    reread = vault.find_universe(ledger, "starter-tranche-v1")
+    assert reread["rule_hash"] == row["rule_hash"]
+    assert reread["registered_at"] == row["registered_at"]
+    assert reread["vault_secret_commitment"] == commitment
+
+
+# === iter-9 audit fix B2: the registered rule is FROZEN (spec section 7.2) ==========================
+
+
+def test_audit_b2_a_narrowed_re_registration_is_refused_and_cannot_neutralize_the_tr4_refusal(tmp_path):
+    """The escape hatch this fix closes, reproduced end to end: register a 2x2 universe, watch a
+    cherry-picked batch get refused (TR-4), then attempt exactly what spec section 7.2 forbids
+    ("no substitution because a symbol is inconvenient") -- re-register the SAME ``universe_id``
+    with the inconvenient symbol dropped. Pre-fix, ``find_universe``'s LATEST-row resolution made
+    that second row govern and the identical batch validated ``{"ok": True}``. The registration
+    must now refuse, append NO row, and leave the ORIGINAL rule still governing the verifier."""
+    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    commitment = vault.commit_vault_secret(b"secret")
+    vault.register_universe(
+        ledger, universe_id="starter-tranche-v1", symbol_rule=["PG", "AAPL"],
+        date_rule=["2026-06-08", "2026-06-09"], vault_secret_commitment=commitment,
+    )
+    cherry_picked = [("PG", "2026-06-08"), ("PG", "2026-06-09")]  # AAPL dropped, nothing disclosed
+    with pytest.raises(vault.CherryPickedBatchError):
+        vault.verify_universe_recording_batch(ledger, "starter-tranche-v1", recorded=cherry_picked)
+
+    with pytest.raises(vault.VaultUniverseAlreadyRegisteredError) as exc_info:
+        vault.register_universe(
+            ledger, universe_id="starter-tranche-v1", symbol_rule=["PG"],
+            date_rule=["2026-06-08", "2026-06-09"], vault_secret_commitment=commitment,
+        )
+    assert "starter-tranche-v1" in str(exc_info.value)
+
+    assert len(ledger.all_rows()) == 1  # the refused registration appended nothing
+    assert vault.find_universe(ledger, "starter-tranche-v1")["symbol_rule"] == ["PG", "AAPL"]
+    # and the batch the re-registration was trying to legalize is STILL refused.
+    with pytest.raises(vault.CherryPickedBatchError):
+        vault.verify_universe_recording_batch(ledger, "starter-tranche-v1", recorded=cherry_picked)
+
+
+def test_audit_b2_a_byte_identical_re_registration_is_an_idempotent_no_op(tmp_path):
+    """A crash-retry of the ONE operator registration act must not fork the universe's history:
+    an identical re-registration returns the EXISTING row (same ``registered_at``, same
+    ``row_hash``) and appends no second row -- the era's own "idempotency everywhere, not
+    everywhere except one path" lesson, applied to the freeze this fix introduces."""
+    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    commitment = vault.commit_vault_secret(b"secret")
+    kwargs = dict(
+        universe_id="starter-tranche-v1", symbol_rule=["PG", "AAPL"],
+        date_rule=["2026-06-08", "2026-06-09"], vault_secret_commitment=commitment,
+    )
+    first = vault.register_universe(ledger, **kwargs)
+    again = vault.register_universe(ledger, **kwargs)
+
+    assert again["row_hash"] == first["row_hash"]
+    assert again["registered_at"] == first["registered_at"]
+    assert len(ledger.all_rows()) == 1
+    assert ledger.verify_chain() == {"ok": True, "failed_at_row": None, "reason": None}
+
+
+def test_audit_b2_a_re_registration_under_a_different_secret_commitment_is_also_refused(tmp_path):
+    """The rule hash is not the only frozen half: swapping the vault secret under an already-
+    registered universe would silently re-randomize which shards are sealed (section 7.3), so an
+    identical rule with a DIFFERENT commitment is refused too."""
+    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    vault.register_universe(
+        ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
+        vault_secret_commitment=vault.commit_vault_secret(b"first-secret"),
+    )
+    with pytest.raises(vault.VaultUniverseAlreadyRegisteredError):
+        vault.register_universe(
+            ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
+            vault_secret_commitment=vault.commit_vault_secret(b"a-different-secret"),
+        )
+    assert len(ledger.all_rows()) == 1
+
+
+# === TC-3/TC-4: TR-4 cherry-pick refusal + disclosed-failure success ================================
+
+
+def _registered_universe_ledger(tmp_path) -> tuple[vault.VaultUniverseLedger, str]:
+    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    vault.register_universe(
+        ledger, universe_id="u1", symbol_rule=["PG", "AAPL"], date_rule=["2026-06-08", "2026-06-09"],
+        vault_secret_commitment=vault.commit_vault_secret(b"secret"),
+    )
+    return ledger, "u1"
+
+
+def test_tc3_a_cherry_picked_batch_is_refused_naming_the_missing_entry(tmp_path):
+    ledger, universe_id = _registered_universe_ledger(tmp_path)
+    # the rule's full 2x2 = 4 pairs, minus ("AAPL", "2026-06-09") -- no disclosed failure for it.
+    recorded = [("PG", "2026-06-08"), ("PG", "2026-06-09"), ("AAPL", "2026-06-08")]
+    with pytest.raises(vault.CherryPickedBatchError) as exc_info:
+        vault.verify_universe_recording_batch(ledger, universe_id, recorded=recorded)
+    assert "('AAPL', '2026-06-09')" in str(exc_info.value)
+
+
+def test_tc4_a_batch_matching_the_rule_minus_one_disclosed_failure_is_ok(tmp_path):
+    ledger, universe_id = _registered_universe_ledger(tmp_path)
+    recorded = [("PG", "2026-06-08"), ("PG", "2026-06-09"), ("AAPL", "2026-06-08")]
+    result = vault.verify_universe_recording_batch(
+        ledger, universe_id, recorded=recorded, disclosed_failures=[("AAPL", "2026-06-09")]
+    )
+    assert result == {"ok": True}
+
+
+def test_an_unexpected_extra_entry_is_also_refused_never_silently_accepted(tmp_path):
+    """The mirror image of TC-3: a batch carrying an entry OUTSIDE the registered rule (not merely
+    short one) is refused too -- TR-4 guards both directions, never only under-recording."""
+    ledger, universe_id = _registered_universe_ledger(tmp_path)
+    recorded = [("PG", "2026-06-08"), ("PG", "2026-06-09"), ("AAPL", "2026-06-08"), ("AAPL", "2026-06-09"), ("MSFT", "2026-06-08")]
+    with pytest.raises(vault.CherryPickedBatchError) as exc_info:
+        vault.verify_universe_recording_batch(ledger, universe_id, recorded=recorded)
+    assert "('MSFT', '2026-06-08')" in str(exc_info.value)
+
+
+# === TC-5: the HMAC seal decision + the never-logged-raw-secret discipline ==========================
+
+
+def test_tc5_the_seal_decision_is_deterministic_across_repeated_calls(tmp_path):
+    secret = vault.load_vault_secret(_write_secret_file(tmp_path))
+    first = vault.compute_seal(secret, "PG", "2026-06-09")
+    second = vault.compute_seal(secret, "PG", "2026-06-09")
+    assert first == second
+    assert isinstance(first, bool)
+
+
+def test_tc5_the_raw_secret_string_never_appears_in_a_universe_row_or_the_ledger_file_on_disk(tmp_path):
+    raw_secret_text = "the-actual-raw-vault-secret-do-not-leak-me"
+    secret = vault.load_vault_secret(_write_secret_file(tmp_path, raw_secret_text))
+    commitment = vault.commit_vault_secret(secret)
+    assert commitment != raw_secret_text  # sanity: the commitment is a sha256 hex digest, not the secret
+
+    vault_dir = str(tmp_path / "vault")
+    ledger = vault.VaultUniverseLedger(vault_dir)
+    row = vault.register_universe(
+        ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
+        vault_secret_commitment=commitment,
+    )
+    assert raw_secret_text not in json.dumps(row)
+    assert row["vault_secret_commitment"] == commitment
+
+    on_disk = (Path(vault_dir) / "vault_universe_ledger.jsonl").read_text()
+    assert raw_secret_text not in on_disk
+
+
+def test_tc5_a_missing_vault_secret_file_env_var_is_a_typed_refusal_never_a_crash(monkeypatch):
+    monkeypatch.delenv("TAPEOLOGY_VAULT_SECRET_FILE", raising=False)
+    with pytest.raises(vault.VaultSecretUnavailable):
+        vault.load_vault_secret()
+
+
+def test_tc5_an_unreadable_vault_secret_path_is_a_typed_refusal(tmp_path):
+    with pytest.raises(vault.VaultSecretUnavailable):
+        vault.load_vault_secret(str(tmp_path / "does-not-exist.txt"))
+
+
+def test_tc5_an_empty_vault_secret_file_is_a_typed_refusal(tmp_path):
+    path = tmp_path / "empty_secret.txt"
+    path.write_text("   \n")
+    with pytest.raises(vault.VaultSecretUnavailable):
+        vault.load_vault_secret(str(path))
+
+
+def test_tc5_the_env_var_is_read_when_no_explicit_path_is_given(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_VAULT_SECRET_FILE", _write_secret_file(tmp_path, "env-sourced-secret"))
+    secret = vault.load_vault_secret()
+    assert secret == b"env-sourced-secret"
+
+
+# === TC-6: section 7.5 opaque pre-exposure serving ==================================================
+
+
+_SEALED_DATASET_ID = "dataset-1"
+_SEALED_CONTENT_CHECKSUM = "a" * 64
+
+
+def _sealed_shard_ledger(
+    tmp_path, *, dataset_id: str = _SEALED_DATASET_ID, event_count: int = 45_231
+) -> vault.VaultShardLedger:
+    ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    vault.seal_shard(
+        ledger, dataset_id=dataset_id, universe_id="u1",
+        content_checksum=_SEALED_CONTENT_CHECKSUM, event_count=event_count,
+        vault_secret=_FIXTURE_SECRET,
+    )
+    return ledger
+
+
+def test_tc6_a_sealed_shards_entry_carries_only_the_section_7_5_opaque_fields(tmp_path):
+    shard_ledger = _sealed_shard_ledger(tmp_path)
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+
+    state = vault.build_vault_state(shard_ledger, universe_ledger)
+    assert len(state["shards"]) == 1
+    entry = state["shards"][0]
+
+    assert set(entry.keys()) == {"shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state"}
+    assert entry["exposure_state"] == "sealed"
+    assert "symbol" not in entry
+    assert "session_date" not in entry
+    assert "45231" not in json.dumps(entry)  # the exact event count never appears anywhere
+    assert entry["size_bucket"] != 45_231
+    # r3: neither of the two join keys the iter-9 audit found is served -- not the dataset id the
+    # public dataset routes are keyed on, and not the raw content checksum they publish.
+    assert _SEALED_DATASET_ID not in json.dumps(entry)
+    assert _SEALED_CONTENT_CHECKSUM not in json.dumps(entry)
+
+
+def test_r3_the_served_shard_id_is_a_surrogate_with_no_derivable_relation_to_the_dataset_id(tmp_path):
+    """Spec section 7.5 point 1: "not the id, not a hash of it, not a prefix". Each of those three
+    is checked literally, plus the property that makes the surrogate non-derivable at all -- it is
+    keyed on the vault SECRET, so the same dataset id under a different secret mints a different
+    token (an attacker holding every public dataset id still cannot compute the mapping)."""
+    entry = vault.build_vault_state(
+        _sealed_shard_ledger(tmp_path), vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    )["shards"][0]
+    surrogate = entry["shard_id"]
+
+    assert surrogate.startswith(vault.SURROGATE_SHARD_ID_PREFIX)
+    assert surrogate != _SEALED_DATASET_ID
+    assert hashlib.sha256(_SEALED_DATASET_ID.encode()).hexdigest() not in surrogate
+    assert not surrogate.endswith(_SEALED_DATASET_ID) and _SEALED_DATASET_ID not in surrogate
+    assert not _SEALED_DATASET_ID.startswith(surrogate.removeprefix(vault.SURROGATE_SHARD_ID_PREFIX))
+
+    # deterministic under the same secret (the era's no-unseeded-randomness anti-goal) ...
+    assert vault.compute_surrogate_shard_id(_FIXTURE_SECRET, _SEALED_DATASET_ID) == surrogate
+    # ... and unpredictable without it.
+    assert vault.compute_surrogate_shard_id(b"a-different-secret", _SEALED_DATASET_ID) != surrogate
+
+
+def test_r3_the_sealed_commitment_is_salted_and_re_derivable_once_exposure_reveals_the_checksum(tmp_path):
+    """Spec section 7.5 point 2: the pre-exposure commitment is ``HMAC(vault_secret,
+    content_checksum)``, NOT the raw checksum (which is served publicly per dataset and would join
+    directly) and not a plain hash of it (equally derivable). Auditability survives because
+    exposure reveals the raw checksum, against which the salted commitment re-derives exactly."""
+    shard_ledger = _sealed_shard_ledger(tmp_path)
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    sealed_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
+    commitment = sealed_entry["checksum_commitment"]
+
+    assert commitment != _SEALED_CONTENT_CHECKSUM
+    assert commitment != hashlib.sha256(_SEALED_CONTENT_CHECKSUM.encode()).hexdigest()
+    assert vault.commit_content_checksum(b"a-different-secret", _SEALED_CONTENT_CHECKSUM) != commitment
+
+    family_root = vault.compute_family_root_id("f", "c", "o")
+    vault.assign_shard(
+        shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root,
+        symbol="PG", session_date="2026-06-09",
+    )
+    assigned_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
+    assert "content_checksum" not in assigned_entry  # still withheld at `assigned`
+    assert assigned_entry["dataset_id"] == _SEALED_DATASET_ID  # the mapping IS revealed here (r3)
+
+    vault.expose_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root)
+    exposed_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
+    assert exposed_entry["content_checksum"] == _SEALED_CONTENT_CHECKSUM
+    # the whole point of a commitment: it verifies against what exposure revealed.
+    assert vault.commit_content_checksum(_FIXTURE_SECRET, exposed_entry["content_checksum"]) == commitment
+
+
+def test_size_bucket_is_order_of_magnitude_only_and_monotonic():
+    assert vault._coarse_size_bucket(0) == "~0"
+    small = vault._coarse_size_bucket(50)
+    large = vault._coarse_size_bucket(45_231)
+    assert small != large
+    assert "45231" not in small and "45231" not in large
+
+
+# === TC-7: assignment reveals symbol/date; the chain still verifies =================================
+
+
+def test_tc7_assignment_reveals_symbol_and_date_and_the_chain_still_verifies(tmp_path):
+    shard_ledger = _sealed_shard_ledger(tmp_path)
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    sealed_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
+    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+
+    vault.assign_shard(
+        shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root, symbol="PG",
+        session_date="2026-06-09",
+    )
+
+    state = vault.build_vault_state(shard_ledger, universe_ledger)
+    entry = state["shards"][0]
+    assert entry["exposure_state"] == "assigned"
+    assert entry["symbol"] == "PG"
+    assert entry["session_date"] == "2026-06-09"
+    assert entry["family_root_id"] == family_root
+    # the opaque fields survive alongside the newly-revealed ones -- never REPLACED, only added to.
+    assert entry["checksum_commitment"] == sealed_entry["checksum_commitment"]
+    assert entry["shard_id"] == sealed_entry["shard_id"]
+    assert state["shard_ledger_chain_verification"] == {"ok": True, "failed_at_row": None, "reason": None}
+
+
+# === TC-8/TR-12: single-shot refusal =================================================================
+
+
+def test_tc8_a_second_assignment_for_the_same_shard_is_refused_and_appends_no_row(tmp_path):
+    shard_ledger = _sealed_shard_ledger(tmp_path)
+    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+    vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root, symbol="PG", session_date="2026-06-09")
+    rows_after_first_assignment = len(shard_ledger.all_rows())
+
+    with pytest.raises(vault.ShardLifecycleOrderError):
+        vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root, symbol="PG", session_date="2026-06-09")
+
+    assert len(shard_ledger.all_rows()) == rows_after_first_assignment  # no new row for that pair
+
+
+def test_audit_t1_a_genuinely_different_family_cannot_claim_an_already_assigned_shard(tmp_path):
+    """iter-9 audit finding T1: TC-8/TC-9 both re-attempt with the SAME ``family_root_id``, so the
... [diff_bound] apps/backend/tests/test_vault.py: 842 more diff lines omitted — Read the file for full detail
```
