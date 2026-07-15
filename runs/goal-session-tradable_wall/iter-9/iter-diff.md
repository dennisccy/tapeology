# Iteration diff (bounded)

Files changed: 10. Shown in full: 9.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_edge_report_cache.py` (27 lines not shown)

```diff
diff --git a/apps/backend/app/research/edge_report.py b/apps/backend/app/research/edge_report.py
index d944f44..6c34063 100644
--- a/apps/backend/app/research/edge_report.py
+++ b/apps/backend/app/research/edge_report.py
@@ -72,6 +72,7 @@ from .bars import BarStore
 # second R/$/edge formula.
 from .backtests import BacktestJobManager, REGISTER, STATUS_DONE, _aggregate
 from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, parse_utc_epoch
+from .edge_report_cache import EdgeReportCache
 from .setups import compute_setups
 from .store import JournalStore
 
@@ -424,16 +425,49 @@ def _surviving_train_cells(
 
 
 def run_strategy_comparison_report(
+    store: JournalStore,
+    dataset_store: DatasetStore,
+    bar_store: BarStore,
+    config: Config,
+    *,
+    cache: EdgeReportCache | None = None,
+) -> dict:
+    """The public entry point for the 3-way strategy-comparison report (era-5B J-04; ``GET
+    /research/edge-report`` + the MCP ``edge_report`` proxy serve this VERBATIM). See
+    ``_compute_strategy_comparison_report`` below for the full algorithm docstring — this function
+    is now a thin dispatcher over that ONE computation, never a second copy of it.
+
+    era-5B J-08: ``cache`` is an OPTIONAL rebuildable result cache
+    (``edge_report_cache.EdgeReportCache``). ``cache=None`` (the default) is the EXACT pre-J-08
+    behaviour — always calls ``_compute_strategy_comparison_report`` directly, byte-for-byte
+    identical to before — so every EXISTING call site (every test in ``test_edge_report.py``, and
+    any future caller with no cache to offer) is untouched and stays uncached. When a cache IS
+    supplied (the route's DI-wired path — see ``routes.get_edge_report``), this function serves
+    ``_compute_strategy_comparison_report``'s output VERBATIM through it: the cache never
+    re-derives a cell, a measurement, or a null baseline — a miss recomputes byte-identically
+    through the SAME one function below (single source of truth; no second computation path,
+    anywhere)."""
+
+    def compute() -> dict:
+        return _compute_strategy_comparison_report(store, dataset_store, bar_store, config)
+
+    if cache is None:
+        return compute()
+    return cache.get_or_compute(dataset_store, config, compute)
+
+
+def _compute_strategy_comparison_report(
     store: JournalStore, dataset_store: DatasetStore, bar_store: BarStore, config: Config
 ) -> dict:
-    """The ONE computer of the 3-way strategy-comparison report (era-5B J-04; ``GET
-    /research/edge-report`` + the MCP ``edge_report`` proxy serve this VERBATIM). Measures ``v1``,
-    ``structure_tape``, and ``structure_tape_map`` over EVERY registered event-window dataset that
-    resolves an owning, classified scan event, aggregated into per strategy x class x side x
-    reaction x feed cells. Raises ``EdgeReportError`` for a dishonest state (the identical
-    ``_split_datasets`` integrity discipline ``run_edge_report`` uses) — nothing is written by the
-    CALLER in that case. Strictly read-only: promotes nothing, appends no ledger row, moves no
-    champion pointer (see the module docstring)."""
+    """The ONE computer of the 3-way strategy-comparison report (era-5B J-04; renamed from
+    ``run_strategy_comparison_report`` at era-5B J-08 — see that function's own docstring for why:
+    this is the byte-identical pure-compute body, now wrapped by an optional cache rather than
+    called directly). Measures ``v1``, ``structure_tape``, and ``structure_tape_map`` over EVERY
+    registered event-window dataset that resolves an owning, classified scan event, aggregated
+    into per strategy x class x side x reaction x feed cells. Raises ``EdgeReportError`` for a
+    dishonest state (the identical ``_split_datasets`` integrity discipline ``run_edge_report``
+    uses) — nothing is written by the CALLER in that case. Strictly read-only: promotes nothing,
+    appends no ledger row, moves no champion pointer (see the module docstring)."""
     jobs = BacktestJobManager(store, config)
     train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
     holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)
diff --git a/apps/backend/app/research/pnl_history.py b/apps/backend/app/research/pnl_history.py
index e051336..4e423fd 100644
--- a/apps/backend/app/research/pnl_history.py
+++ b/apps/backend/app/research/pnl_history.py
@@ -8,20 +8,101 @@ Deterministic: regenerating with unchanged rows is a byte-level no-op (verifiabl
 ``git diff`` on the committed file). Keyless; reads the operator's journal DB via the same
 ``TAPEOLOGY_JOURNAL_DB`` resolution seam the backend uses. An empty ledger renders the honest
 explicit empty state — never fabricated rows.
+
+era-5B J-08 additive: ``--append-report`` gives the operator a single command to append a
+COMPLETED ``run_strategy_comparison_report`` output (e.g. the first real, credentialed,
+cache-warmed compute over the full corpus — the operator-gated carry this iteration builds the
+machinery for but does not itself run) to the ledger, then regenerate the committed markdown from
+the now-updated stored rows in the SAME step. Composition is the single
+``append_strategy_comparison_row`` writer (``pnl_ledger.py``); rendering is the SAME
+``write_history_markdown`` every other regeneration uses — no second path. Omitting
+``--append-report`` keeps ``main()``'s pre-J-08 behaviour EXACTLY as before (render-only, no
+append) — byte-for-byte unchanged.
+
+era-5B J-08 additive: ``--out`` optionally overrides the render target (the ``edge_report.py
+--out`` precedent), defaulting to ``None`` — i.e. the EXACT pre-J-08 default (the config-owned
+committed path) — when omitted. Exists so this CLI is safely testable end-to-end (a hermetic
+``tmp_path`` target) without ever risking a write to the real committed file; an operator running
+the real append still omits it to target the committed file, exactly as before.
 """
 
 from __future__ import annotations
 
-from ..config import CONFIG
-from .pnl_ledger import write_history_markdown
-from .store import JournalStore
+import argparse
+import json
+import sys
+from pathlib import Path
+
+from ..config import CONFIG, Config
+from .pnl_ledger import LedgerCompositionError, append_strategy_comparison_row, write_history_markdown
+from .store import DuplicateEnhancementError, JournalStore
+
+
+def append_strategy_comparison_and_render(
+    store: JournalStore,
+    config: Config,
+    *,
+    enhancement_id: str,
+    title: str,
+    report: dict,
+    path: Path | None = None,
+) -> Path:
+    """Append ONE completed 3-way comparison report to the PnL ledger, then regenerate the
+    markdown from the (now-updated) stored rows — the single operator-run act that lands a real
+    edge-report compute's register (era-5B J-08). Composition is the single
+    ``append_strategy_comparison_row`` writer; rendering is the SAME ``write_history_markdown``
+    every other regeneration uses — no second path. Raises ``LedgerCompositionError`` (a malformed
+    ``report``) or the store's ``DuplicateEnhancementError`` (a re-used ``enhancement_id``)
+    explicitly — nothing is appended OR rendered on either failure."""
+    append_strategy_comparison_row(
+        store, config, enhancement_id=enhancement_id, title=title, report=report
+    )
+    return write_history_markdown(store, config, path)
 
 
 def main() -> int:
+    parser = argparse.ArgumentParser(
+        description="Regenerate the committed PnL-history markdown from the stored ledger rows, "
+        "optionally appending ONE completed 3-way strategy-comparison report first."
+    )
+    parser.add_argument(
+        "--append-report",
+        metavar="PATH",
+        help="path to a completed run_strategy_comparison_report JSON file to append before "
+        "rendering (era-5B J-08); omit for the pre-J-08 render-only behaviour",
+    )
+    parser.add_argument("--enhancement-id", help="the enhancement id for the appended row (required with --append-report)")
+    parser.add_argument("--title", help="the appended row's title (required with --append-report)")
+    parser.add_argument(
+        "--out",
+        metavar="PATH",
+        help="override the markdown output path (default: the config-owned committed "
+        "reports/pnl/pnl-history.md — omit this for a real operator run)",
+    )
+    args = parser.parse_args()
+
+    if args.append_report and (not args.enhancement_id or not args.title):
+        print(
+            "error: --append-report requires both --enhancement-id and --title", file=sys.stderr
+        )
+        return 1
+
+    out_path = Path(args.out) if args.out else None
     config = CONFIG
     store = JournalStore(config.journal_db_path_resolved(), config)
     try:
-        path = write_history_markdown(store, config)
+        if args.append_report:
+            report = json.loads(Path(args.append_report).read_text())
+            try:
+                path = append_strategy_comparison_and_render(
+                    store, config, enhancement_id=args.enhancement_id, title=args.title,
+                    report=report, path=out_path,
+                )
+            except (LedgerCompositionError, DuplicateEnhancementError) as exc:
+                print(f"error: {exc}", file=sys.stderr)
+                return 1
+        else:
+            path = write_history_markdown(store, config, out_path)
     finally:
         store.close()
     print(f"pnl history rendered: {path}")
diff --git a/apps/backend/app/research/pnl_ledger.py b/apps/backend/app/research/pnl_ledger.py
index f66d267..9331ce2 100644
--- a/apps/backend/app/research/pnl_ledger.py
+++ b/apps/backend/app/research/pnl_ledger.py
@@ -53,6 +53,14 @@ from .backtests import REGISTER, STATUS_DONE
 from .datasets import SPLIT_HOLDOUT, SPLIT_TRAIN
 from .store import JournalStore, PnlLedgerRecord
 
+# The NEW row-shape discriminator ``render_history_markdown`` branches on (era-5B J-08) — present
+# ONLY on a row appended by ``append_strategy_comparison_row`` below; every EXISTING/OLD row
+# (appended by ``append_validation_row`` above) carries no ``kind`` key at all, so
+# ``row.get("kind")`` reads ``None`` for them — an explicit tag rather than inferring the shape
+# from "has no 'candidate' key" (the codebase's ``_ROW_TRADE``/``_ROW_QUOTE`` tagged-shape
+# precedent in ``datasets.py``, applied here).
+_KIND_STRATEGY_COMPARISON = "strategy_comparison"
+
 
 class LedgerCompositionError(Exception):
     """A ledger row could not be composed from its source backtest reports — missing report,
@@ -190,6 +198,105 @@ def append_validation_row(
     return row
 
 
+# --- The 3-way strategy-comparison append (era-5B J-08) — an ADDITIVE second writer beside
+# ``append_validation_row`` above (untouched by this section), composing a DIFFERENT row shape
+# from a DIFFERENT source. --------------------------------------------------------------------
+
+
+def _ledger_cell(cell: dict, basis: str) -> dict:
+    """One report cell, denormalized for a ledger row: a COPY of the source ``edge_report.py``
+    cell (never mutated) with ``basis`` (``"train"`` / ``"holdout"``) added — the split a cell
+    floating alone (e.g. copy-pasted out of the row) still honestly names. ``measurement``,
+    ``null_baseline``, and ``insufficient_sample`` are copied VERBATIM — ``edge_report.py``'s
+    ``_split_cells`` already computed all three against the SAME ``pnl_min_sample_size`` this
+    row's own ``pnl_min_sample_size`` field carries, so re-deriving any of them here would risk a
+    second, driftable copy of that gate (never recomputed, per this module's own writer
+    discipline)."""
+    return {**copy.deepcopy(cell), "basis": basis}
+
+
+def append_strategy_comparison_row(
+    store: JournalStore,
+    config: Config,
+    *,
+    enhancement_id: str,
+    title: str,
+    report: dict,
+) -> dict:
+    """Compose and append ONE 3-way strategy-comparison PnL-ledger row (era-5B J-08) from an
+    ALREADY-COMPLETED ``run_strategy_comparison_report`` output — the identical "verbatim copy,
+    never recompute" discipline ``append_validation_row`` uses for its own two source reports,
+    applied here to the report's OWN cells (never a dataset/engine/aggregate call of any kind;
+    this function takes no dataset store, bar store, or backtest-job manager of any kind — its
+    only inputs are the journal store it appends through, the config it reads assumptions from,
+    and the already-completed report dict itself).
+
+    Distinct from ``append_validation_row`` above (untouched by this function): that writer
+    composes a TWO-SIDED (baseline vs ONE candidate) row from two PERSISTED BACKTEST reports
+    fetched by id; THIS writer composes a THREE-STRATEGY (``v1`` / ``structure_tape`` /
+    ``structure_tape_map``) row DIRECTLY from an in-memory 3-way comparison report's own cells —
+    the report itself already IS the single completed measurement (no per-report id to fetch, no
+    provenance to cross-check between two sources). Both writers share the SAME append mechanism
+    (``store.append_pnl_ledger_row``) and the SAME structural append-only/no-update-or-delete
+    guarantee; ``ledger_projection`` below needs NO change to serve either shape verbatim (a new
+    row's absent ``"baseline"``/``"candidate"`` keys make its existing per-row label loop skip it
+    silently — see that function's own docstring).
+
+    The appended row NEVER pools: every cell keeps its own (strategy, class, side, reaction, feed)
+    identity and its own ``basis`` (train/holdout — kept as two separate top-level lists,
+    mirroring the report's own ``train``/``holdout`` shape); this function only re-shapes/labels
+    the report's cells (adding ``basis``), it never sums, averages, or merges any two of them, and
+    it never touches a cell's ``feed`` (so two feeds recorded into the SAME report stay exactly as
+    un-pooled as ``edge_report.py`` already left them). Every cell carries its measurement
+    (n/gross/net R/$), its OWN null baseline, and the row-level fee/slippage/dollars-per-R
+    assumptions read VERBATIM from ``config`` (never re-derived) — a single shared block rather
+    than repeated per cell, since every registered strategy currently shares the identical fee/
+    slippage model (``config.strategy_definition``'s own documented "FEES / SLIPPAGE / DOLLAR
+    CONVERSION — IDENTICAL to v1" clause). ``insufficient_sample`` is copied VERBATIM from the
+    source cell.
+
+    Raises ``LedgerCompositionError`` (never appends a partial row) if ``report`` does not carry
+    the expected ``train.cells`` / ``holdout.cells`` shape — the identical honest-failure
+    discipline ``_completed_report`` enforces for the two-way writer above. A duplicate
+    ``enhancement_id`` raises the store's own ``DuplicateEnhancementError`` (unchanged, structural,
+    the SAME one row per enhancement guarantee every ledger row shares)."""
+    for split in (SPLIT_TRAIN, SPLIT_HOLDOUT):
+        section = report.get(split)
+        if not isinstance(section, dict) or "cells" not in section:
+            raise LedgerCompositionError(
+                f"the report does not carry a '{split}.cells' section — a 3-way comparison row "
+                f"is only ever composed from a genuinely completed run_strategy_comparison_report "
+                f"output, so nothing was appended"
+            )
+    now = time.time()
+    row = {
+        "kind": _KIND_STRATEGY_COMPARISON,
+        "enhancement_id": enhancement_id,
+        "title": title,
+        "register": report.get("register", REGISTER),
+        "pnl_min_sample_size": report.get("pnl_min_sample_size", config.pnl_min_sample_size),
+        "config_fingerprint": config.config_fingerprint(),
+        "assumptions": {
+            "fees": {
+                "per_share": config.strategy_fee_per_share,
+                "min_per_trade": config.strategy_fee_min_per_trade,
+            },
+            "slippage": {"spread_fraction": config.strategy_slippage_spread_fraction},
+            "dollars_per_r": config.strategy_dollars_per_r,
+        },
+        "cells": {
+            SPLIT_TRAIN: [_ledger_cell(cell, SPLIT_TRAIN) for cell in report[SPLIT_TRAIN]["cells"]],
+            SPLIT_HOLDOUT: [_ledger_cell(cell, SPLIT_HOLDOUT) for cell in report[SPLIT_HOLDOUT]["cells"]],
+        },
+        "created_wall_ts": now,
+        "created_utc": _iso_utc(now),
+    }
+    store.append_pnl_ledger_row(
+        PnlLedgerRecord(enhancement_id=enhancement_id, payload=row, created_wall_ts=now)
+    )
+    return row
+
+
 # --- the ONE serving read (REST, markdown, and — via the route — MCP all consume this) -------------
 
 
@@ -224,6 +331,53 @@ def _ddmmyyyy(created_utc: str) -> str:
     return datetime.fromisoformat(created_utc.replace("Z", "+00:00")).strftime("%d-%m-%Y")
 
 
+def _render_strategy_comparison_row_lines(row: dict, index: int) -> list[str]:
+    """The era-5B J-08 rendering branch for a ``_KIND_STRATEGY_COMPARISON`` row — a per-cell
+    table (strategy x class x side x reaction x feed) for each split, mirroring the EXISTING
+    two-way row's table shape (one line per measurement, net R beside net $ beside n beside its
+    sample label) but WITHOUT a ``side`` column (there is no baseline/candidate distinction here —
+    ``strategy_id`` already carries that role, comparing all three registered strategies
+    side-by-side)."""
+    lines = [
+        f"## {index}. {row['title']}",
+        "",
+        f"- Enhancement id: `{row['enhancement_id']}`",
+        f"- Appended (UTC): {_ddmmyyyy(row['created_utc'])}",
+        f"- Config fingerprint `{row['config_fingerprint']}`",
+        f"- Register: {row['register']}",
+        f"- Assumptions: fees `{row['assumptions']['fees']['per_share']}`/share (minimum "
+        f"`{row['assumptions']['fees']['min_per_trade']}`/trade) · slippage "
+        f"`{row['assumptions']['slippage']['spread_fraction']}` of spread · "
+        f"`{row['assumptions']['dollars_per_r']}` per R",
+        "- Three-way strategy comparison (`v1` / `structure_tape` / `structure_tape_map`) — "
+        "train and hold-out separate, feeds never pooled.",
+        "",
+    ]
+    min_n = row["pnl_min_sample_size"]
+    for split in (SPLIT_TRAIN, SPLIT_HOLDOUT):
+        cells = row["cells"][split]
+        lines += [f"### {split}", ""]
+        if not cells:
+            lines += ["No cells for this split.", ""]
+            continue
+        lines += [
+            "| strategy | class | side | reaction | feed | net R | net $ | n | sample |",
+            "|----------|-------|------|----------|------|------:|------:|--:|--------|",
+        ]
+        for cell in cells:
+            measurement = cell["measurement"]
+            label = (
+                f"insufficient sample (n < {min_n})" if cell["insufficient_sample"] else "ok"
+            )
+            lines.append(
+                f"| {cell['strategy_id']} | {cell['band_class']} | {cell['band_side']} | "
+                f"{cell['reaction']} | {cell['feed']} | {measurement['net_r']} | "
+                f"{measurement['net_usd']} | {measurement['n']} | {label} |"
+            )
+        lines.append("")
+    return lines
+
+
 def render_history_markdown(store: JournalStore, config: Config) -> str:
     """Render the ledger to markdown — a PURE function of the stored rows via the SAME
     ``ledger_projection`` read the route serves (never a second query or labeling path).
@@ -253,6 +407,9 @@ def render_history_markdown(store: JournalStore, config: Config) -> str:
         ]
         return "\n".join(lines)
     for index, row in enumerate(rows, start=1):
+        if row.get("kind") == _KIND_STRATEGY_COMPARISON:
+            lines += _render_strategy_comparison_row_lines(row, index)
+            continue
         provenance = row["provenance"]
         lines += [
             f"## {index}. {row['title']}",
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 5cfb8f5..8fd1fb6 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -50,6 +50,7 @@ from .bars import (
     EmptyBarWindowError,
 )
 from .edge_report import EdgeReportError, run_strategy_comparison_report
+from .edge_report_cache import EdgeReportCache
 from .levels import compute_levels
 from .setups import BROKE, CHOPPED, REJECTED, compute_setups, enrich_with_tape_timeline
 from .tradability import compute_tradability
@@ -1560,6 +1561,22 @@ def get_bar_index() -> BarIndex:
     return BarIndex(db_path)
 
 
+def get_edge_report_cache() -> EdgeReportCache:
+    """The persisted, rebuildable 3-way strategy-comparison result cache (era-5B J-08) — a
+    config-DERIVED, env-overridable path so ``config.py`` stays byte-identical
+    (``config_fingerprint`` unaffected — the identical ``get_bar_index`` rationale): the
+    ``TAPEOLOGY_EDGE_REPORT_CACHE_DB`` env var if set, else a file co-located as a SIBLING of the
+    config-owned dataset directory (``get_dataset_store``'s own ``dataset_dir_resolved()``, e.g.
+    ``.data/datasets`` -> ``.data/edge_report_cache.db`` — the SAME ``.data/`` directory
+    ``bar_index.db`` already lives in). A FastAPI dependency so tests can override it outright or
+    point it at a temp path via the env var — the ``get_bar_index`` pattern, exactly."""
+    override = os.environ.get("TAPEOLOGY_EDGE_REPORT_CACHE_DB")
+    db_path = override if override else os.path.join(
+        os.path.dirname(CONFIG.dataset_dir_resolved()), "edge_report_cache.db"
+    )
+    return EdgeReportCache(db_path)
+
+
 def get_bar_fetch_adapter():
     """The market adapter for the BAR-FETCH path ONLY (``POST /research/bars`` — era-5 J-01).
 
@@ -2078,16 +2095,23 @@ def get_edge_report(
     registry: ResearchRegistry = Depends(get_registry),
     dataset_store: DatasetStore = Depends(get_dataset_store),
     bar_store: BarStore = Depends(get_bar_store),
+    cache: EdgeReportCache = Depends(get_edge_report_cache),
 ) -> dict:
     """The 3-way strategy-comparison report (``v1`` / ``structure_tape`` / ``structure_tape_map``)
     aggregated into per strategy x class x side x reaction x feed cells over every registered
     event-window dataset that resolves an owning, classified scan event — served VERBATIM from
-    ``run_strategy_comparison_report`` (era-5B J-04). A dataset failing integrity verification
-    aborts the whole report with an explicit 500 (the ``create_backtest``/``EdgeReportError``
-    precedent) — partial results are never served. An all-empty or all-``insufficient_sample``
-    report (the expected shape on a keyless, single-fixture registry) is a valid 200, never an
-    error."""
+    ``run_strategy_comparison_report`` (era-5B J-04), through the rebuildable result cache
+    (era-5B J-08 — ``edge_report_cache.get_edge_report_cache``, the SAME DI-overridable seam
+    ``get_bar_index`` uses) so a warm cache answers within an interactive budget instead of the
+    documented ~10+h sweep. The cache is an accelerator only: a miss recomputes byte-identically
+    through the SAME one function; this route's response shape is UNCHANGED either way. A dataset
+    failing integrity verification aborts the whole report with an explicit 500 (the
+    ``create_backtest``/``EdgeReportError`` precedent) — partial results are never served, and
+    never cached. An all-empty or all-``insufficient_sample`` report (the expected shape on a
+    keyless, single-fixture registry) is a valid 200, never an error."""
     try:
-        return run_strategy_comparison_report(registry.store, dataset_store, bar_store, registry.config)
+        return run_strategy_comparison_report(
+            registry.store, dataset_store, bar_store, registry.config, cache=cache
+        )
     except EdgeReportError as exc:
         raise HTTPException(status_code=500, detail=f"edge report could not complete: {exc}")
diff --git a/apps/backend/tests/test_edge_report.py b/apps/backend/tests/test_edge_report.py
index 75738ee..8704506 100644
--- a/apps/backend/tests/test_edge_report.py
+++ b/apps/backend/tests/test_edge_report.py
@@ -823,3 +823,159 @@ def test_3way_report_source_reuses_the_shared_aggregate_and_never_a_second_edge_
     # No second R/$/win-rate/drawdown formula anywhere in the new section.
     for forbidden in ("sum(t[", "win_rate =", "max_dd", "cum +="):
         assert forbidden not in src, f"a second aggregate formula leaked into edge_report.py: {forbidden}"
+
+
+# ==================================================================================================
+# The rebuildable result cache (era-5B J-08) — ``run_strategy_comparison_report``'s optional
+# ``cache=`` param, wired to ``edge_report_cache.EdgeReportCache``. Every test ABOVE this marker
+# calls ``run_strategy_comparison_report`` WITHOUT a cache (``cache=None``, the default) and stays
+# green UNMODIFIED — proof by construction that the pre-J-08 uncached path is byte-for-byte
+# untouched. ``EdgeReportCache``'s OWN mechanics (keying, durability, concurrency, torn-read
+# safety) are unit-tested in isolation in ``tests/test_edge_report_cache.py`` against a cheap
+# counting stub; this section proves the WIRING into the real ``_compute_strategy_comparison_
+# report`` — byte-identity against a real, non-degenerate report shape (the iter-4 lesson: never
+# merely the vacuous ``cells: []`` case) and that a warmed cache genuinely skips recomputation.
+# ==================================================================================================
+
+from app.research.edge_report_cache import EdgeReportCache  # noqa: E402
+
+
+def test_cache_none_default_is_byte_identical_to_the_pre_j08_uncached_call(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """The literal DoD default: omitting ``cache=`` recomputes directly, exactly as every OTHER
+    test in this file already proves implicitly by staying green unmodified — this test makes the
+    claim explicit and non-degenerate (the real 3-cell synthetic-scan-join shape, not ``[]``)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+
+    without_kwarg = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
+    with_explicit_none = run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, cache=None
+    )
+
+    assert json.dumps(without_kwarg, sort_keys=True) == json.dumps(with_explicit_none, sort_keys=True)
+    assert len(without_kwarg["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape
+
+
+def test_warm_cache_report_is_byte_identical_to_a_fresh_cache_cleared_compute(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """era-5B J-08 determinism (DoD-mandated; the iter-4 lesson: proven on a NON-degenerate report
+    shape — the real synthetic scan-join fixture, never merely the vacuous empty case). A warm
+    cache's served report is byte-identical to an INDEPENDENT fresh, uncached compute — the cache
+    changes nothing about WHAT is returned, only whether it is recomputed."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    warm = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+    fresh = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)  # cache=None
+
+    assert json.dumps(warm, sort_keys=True) == json.dumps(fresh, sort_keys=True)
+    assert len(warm["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape, not []
+
+
+def test_second_call_on_a_warmed_cache_never_recomputes(tmp_path, store, scan_bar_store, scan_config, monkeypatch):
+    """The whole point of J-08: a SECOND call against an identical, already-warmed cache must never
+    re-enter ``_compute_strategy_comparison_report`` at all (the ``test_compute_setups_runs_at_
+    most_once_per_report_call`` counting-wrapper pattern, applied to the NEW cache-aware entry
+    point)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    calls = []
+    real_compute = edge_report._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)
+
+    first = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+    second = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+
+    assert len(calls) == 1  # the SECOND call served entirely from the cache
+    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+
+
+def test_a_new_recorded_dataset_busts_the_wired_cache(tmp_path, store, scan_bar_store, scan_config):
+    """Adding a NEW registered dataset changes the checksum set the cache is keyed on, so the very
+    next call must recompute and reflect the new dataset — never serve the stale pre-addition
+    report."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta_a = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+
+    first = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+    first_v1_cell = next(c for c in first["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
+    assert first_v1_cell["dataset_ids"] == [meta_a["id"]]
+
+    meta_b = _record_v1_arming_dataset(dataset_store, max_logical=200.0, split=SPLIT_TRAIN, feed="sim", label="b")
+    second = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+    second_v1_cell = next(c for c in second["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
+
+    assert second_v1_cell["dataset_ids"] == sorted([meta_a["id"], meta_b["id"]])
+    assert second_v1_cell["measurement"]["n"] == 2  # both datasets pooled into the recomputed cell
+
+
+def test_durability_across_a_simulated_backend_restart_via_the_wired_function(
+    tmp_path, store, scan_bar_store, scan_config, monkeypatch
+):
+    """The DoD's literal restart scenario, exercised through the REAL public entry point (not just
+    ``EdgeReportCache`` in isolation): a BRAND NEW ``EdgeReportCache`` at the SAME persisted path
+    (simulating a backend restart) serves the prior warm report WITHOUT ever calling
+    ``_compute_strategy_comparison_report`` again."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    db_path = str(tmp_path / "cache.db")
+
+    original_cache = EdgeReportCache(db_path)
+    warm = run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, cache=original_cache
+    )
+
+    restarted_cache = EdgeReportCache(db_path)  # no in-process state carried over
+    calls = []
+    real_compute = edge_report._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)
+
+    served = run_strategy_comparison_report(
+        store, dataset_store, scan_bar_store, scan_config, cache=restarted_cache
+    )
+
+    assert len(calls) == 0  # never recomputed post-"restart" — served from the durable row alone
+    assert json.dumps(served, sort_keys=True) == json.dumps(warm, sort_keys=True)
+
+
+def test_cached_report_never_moves_the_champion_pointer(tmp_path, store, scan_bar_store, scan_config):
+    """The no-hand-promotion guard, re-proven through the cached path specifically: a cache is an
+    accelerator over a strictly read-only report, never a new surface that could promote."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    before = store.get_champion_pointer()
+
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)  # warm hit too
+
+    assert store.get_champion_pointer() == before == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
+
+
+def test_cache_wiring_source_never_duplicates_the_computation():
+    """A coherence guard: the cache-aware ``run_strategy_comparison_report`` is a thin dispatcher —
+    it calls ``_compute_strategy_comparison_report`` (directly or via ``cache.get_or_compute``) and
+    nothing else computes a cell."""
+    src = (BACKEND_DIR / "app" / "research" / "edge_report.py").read_text()
+    assert "def _compute_strategy_comparison_report(" in src
+    assert "cache.get_or_compute(dataset_store, config, compute)" in src
+    # Exactly ONE definition of each — never a second copy under a different name.
+    assert src.count("def run_strategy_comparison_report(") == 1
+    assert src.count("def _compute_strategy_comparison_report(") == 1
diff --git a/apps/backend/tests/test_edge_report_api.py b/apps/backend/tests/test_edge_report_api.py
index 34a226d..6b8ea69 100644
--- a/apps/backend/tests/test_edge_report_api.py
+++ b/apps/backend/tests/test_edge_report_api.py
@@ -122,3 +122,97 @@ def test_edge_report_route_wired_through_the_existing_get_bar_store_seam():
     assert "Depends(get_bar_store)" in src
     assert "Depends(get_dataset_store)" in src
     assert get_bar_store is routes.get_bar_store
+
+
+# --- The rebuildable result cache (era-5B J-08) — route-level wiring -----------------------------
+
+
+def test_edge_report_route_wired_through_the_new_cache_dependency():
+    """The route depends on the NEW ``get_edge_report_cache`` seam — the identical
+    ``Depends(get_bar_index)`` pattern ``record_bar_series``/``list_bar_series`` already use for
+    their own derived, DI-overridable cache."""
+    import inspect
+
+    from app.research import routes
+
+    src = inspect.getsource(routes.get_edge_report)
+    assert "Depends(get_edge_report_cache)" in src
+    assert "cache=cache" in src
+
+
+def test_edge_report_route_serves_a_warm_result_on_the_second_call_without_recomputing(ctx, monkeypatch):
+    """The end-to-end proof J-08 exists for: TWO real HTTP requests against the SAME running
+    backend, the second of which must never re-enter the expensive computation — proven by
+    counting calls to ``_compute_strategy_comparison_report`` (the ONE real computer), not merely
+    inferring it from response shape."""
+    client, _store, _tmp_path = ctx
+    recorded = client.post(
+        "/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:00:00Z",
+            "end": "2026-06-09T17:00:30Z",
+        },
+    )
+    assert recorded.status_code == 200, recorded.text
+
+    from app.research import edge_report as edge_report_module
+
+    calls = []
+    real_compute = edge_report_module._compute_strategy_comparison_report
+
+    def _counting_compute(*args, **kwargs):
+        calls.append(1)
+        return real_compute(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)
+
+    first = client.get("/research/edge-report")
+    second = client.get("/research/edge-report")
+
+    assert first.status_code == 200 and second.status_code == 200
+    assert len(calls) == 1  # the SECOND request served entirely from the warm cache
+    assert first.json() == second.json()
+
+
+def test_edge_report_route_response_is_byte_identical_whether_cache_is_cold_or_warm(ctx):
+    client, _store, _tmp_path = ctx
+    recorded = client.post(
+        "/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:00:00Z",
+            "end": "2026-06-09T17:00:30Z",
+        },
+    )
+    assert recorded.status_code == 200, recorded.text
+
+    cold = client.get("/research/edge-report")
+    warm = client.get("/research/edge-report")
+
+    assert cold.status_code == 200 and warm.status_code == 200
+    assert json.dumps(cold.json(), sort_keys=True) == json.dumps(warm.json(), sort_keys=True)
+
+
+def test_edge_report_route_cache_db_lives_hermetically_beside_the_test_dataset_dir(ctx):
+    """The ``get_bar_index`` "every existing test gets this hermetically for free" property,
+    proven for the NEW cache seam too: the ``ctx`` fixture only points ``TAPEOLOGY_DATASET_DIR`` at
+    a temp dir (never a dedicated cache env var), yet the cache DB must land inside that SAME temp
+    tree — never the real package-anchored default (which would leak state across test runs)."""
+    client, _store, tmp_path = ctx
+    recorded = client.post(
+        "/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:00:00Z",
+            "end": "2026-06-09T17:00:30Z",
+        },
+    )
+    assert recorded.status_code == 200, recorded.text
+
+    response = client.get("/research/edge-report")
+    assert response.status_code == 200
+    assert (tmp_path / "edge_report_cache.db").exists()
diff --git a/apps/backend/tests/test_pnl_ledger.py b/apps/backend/tests/test_pnl_ledger.py
index 65076da..29c2875 100644
--- a/apps/backend/tests/test_pnl_ledger.py
+++ b/apps/backend/tests/test_pnl_ledger.py
@@ -43,6 +43,7 @@ from app.research.datasets import DatasetStore
 from app.research.pnl_baseline import seed_founding_row
 from app.research.pnl_ledger import (
     LedgerCompositionError,
+    append_strategy_comparison_row,
     append_validation_row,
     ledger_projection,
     render_history_markdown,
@@ -519,3 +520,230 @@ def test_row_shaping_founding_values_still_move_the_fingerprint():
     # the fingerprint (the never-pool honesty mechanism) — the exclusion above is not a blanket.
     base = Config().config_fingerprint()
     assert Config(pnl_founding_enhancement_id="other-id").config_fingerprint() != base
+
+
+# ==================================================================================================
+# The 3-way strategy-comparison append (era-5B J-08) — ``append_strategy_comparison_row``. Every
+# test above this marker exercises ``append_validation_row``/the two-way row shape UNMODIFIED —
+# proof by construction that writer (and its row shape) is byte-for-byte untouched. This section
+# feeds ``append_strategy_comparison_row`` a HAND-BUILT, report-shaped dict (the
+# ``test_edge_report.py`` ``_cell()`` / ``test_surviving_train_cells_...`` precedent: what is under
+# test here is the COMPOSITION/labeling logic, never PnL math, which is already exhaustively
+# proven in ``test_edge_report.py``) — never the committed ``reports/pnl/pnl-history.md`` file,
+# which every test below writes to an explicit ``tmp_path`` target instead.
+# ==================================================================================================
+
+
+def _comparison_cell(
+    strategy_id: str, band_class: str, band_side: str, reaction: str, feed: str,
+    *, n: int, net_r: float, net_usd: float, null_net_r: float = -1.0, null_net_usd: float = -100.0,
+) -> dict:
+    return {
+        "strategy_id": strategy_id,
+        "band_class": band_class,
+        "band_side": band_side,
+        "reaction": reaction,
+        "feed": feed,
+        "dataset_ids": ["ds-1"],
+        "measurement": {
+            "n": n, "gross_r": net_r, "net_r": net_r, "gross_usd": net_usd, "net_usd": net_usd,
+            "win_rate": 1.0 if n else None, "max_drawdown_r": 0.0 if n else None,
+        },
+        "null_baseline": {
+            "n": 100, "gross_r": null_net_r, "net_r": null_net_r, "gross_usd": null_net_usd,
+            "net_usd": null_net_usd, "win_rate": 0.4, "max_drawdown_r": 1.0,
+        },
+        "insufficient_sample": n < CONFIG.pnl_min_sample_size,
+    }
+
+
+def _comparison_report(train_cells: list[dict], holdout_cells: list[dict]) -> dict:
+    """A hand-built ``run_strategy_comparison_report``-SHAPED dict — never a real backtest sweep;
+    see this section's own header comment for why this is a legitimate, precedented technique for
+    testing composition logic in isolation."""
+    return {
+        "register": REGISTER,
+        "pnl_min_sample_size": CONFIG.pnl_min_sample_size,
+        "train": {"cells": train_cells},
+        "holdout": {"cells": holdout_cells},
+        "surviving_train_cells": [],
+    }
+
+
+def test_append_strategy_comparison_row_composes_cells_verbatim_with_basis_added(fresh_store):
+    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=3.0, net_usd=300.0)
+    holdout_cell = _comparison_cell(
+        "structure_tape_map", "B", "support", "rejected", "iex", n=2, net_r=-0.5, net_usd=-50.0
+    )
+    report = _comparison_report([train_cell], [holdout_cell])
+
+    row = append_strategy_comparison_row(
+        fresh_store, CONFIG, enhancement_id="e-3way", title="3-way test", report=report
+    )
+
+    assert fresh_store.get_pnl_ledger_row("e-3way").payload == row  # served-verbatim
+    assert row["kind"] == "strategy_comparison"
+    assert row["register"] == REGISTER
+    assert row["pnl_min_sample_size"] == CONFIG.pnl_min_sample_size
+    assert row["config_fingerprint"] == CONFIG.config_fingerprint()
+    assert row["assumptions"] == {
+        "fees": {
+            "per_share": CONFIG.strategy_fee_per_share,
+            "min_per_trade": CONFIG.strategy_fee_min_per_trade,
+        },
+        "slippage": {"spread_fraction": CONFIG.strategy_slippage_spread_fraction},
+        "dollars_per_r": CONFIG.strategy_dollars_per_r,
+    }
+    (train_out,) = row["cells"]["train"]
+    (holdout_out,) = row["cells"]["holdout"]
+    # Every source field survives verbatim, PLUS the added `basis`.
+    assert train_out == {**train_cell, "basis": "train"}
+    assert holdout_out == {**holdout_cell, "basis": "holdout"}
+    # measurement/null_baseline/insufficient_sample are the SOURCE cell's own values, unchanged.
+    assert train_out["measurement"]["net_r"] == 3.0
+    assert train_out["insufficient_sample"] is False  # n=6 >= 5
+    assert holdout_out["insufficient_sample"] is True  # n=2 < 5
+    assert holdout_out["null_baseline"]["net_r"] == -1.0
+
+
+def test_append_never_pools_train_and_holdout(fresh_store):
+    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=1.0, net_usd=100.0)
+    holdout_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=2.0, net_usd=200.0)
+    report = _comparison_report([train_cell], [holdout_cell])
+
+    row = append_strategy_comparison_row(
+        fresh_store, CONFIG, enhancement_id="e-split", title="split test", report=report
+    )
+
+    assert len(row["cells"]["train"]) == 1
+    assert len(row["cells"]["holdout"]) == 1
+    assert row["cells"]["train"][0]["measurement"]["net_r"] == 1.0
+    assert row["cells"]["holdout"][0]["measurement"]["net_r"] == 2.0  # NEVER summed/averaged
+    assert "cells" not in row or set(row["cells"].keys()) == {"train", "holdout"}  # no pooled 3rd key
+
+
+def test_append_never_pools_feeds(fresh_store):
+    sim_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=1.0, net_usd=100.0)
+    iex_cell = _comparison_cell("v1", "A", "resistance", "broke", "iex", n=6, net_r=9.0, net_usd=900.0)
+    report = _comparison_report([sim_cell, iex_cell], [])
+
+    row = append_strategy_comparison_row(
+        fresh_store, CONFIG, enhancement_id="e-feeds", title="feed test", report=report
+    )
+
+    assert len(row["cells"]["train"]) == 2  # two DISTINCT entries — never merged
+    feeds = {c["feed"]: c["measurement"]["net_r"] for c in row["cells"]["train"]}
+    assert feeds == {"sim": 1.0, "iex": 9.0}
+
+
+def test_append_refuses_a_report_missing_a_split_section(fresh_store):
+    malformed = {"register": REGISTER, "pnl_min_sample_size": 5, "train": {"cells": []}}  # no "holdout"
+    with pytest.raises(LedgerCompositionError, match="holdout"):
+        append_strategy_comparison_row(
+            fresh_store, CONFIG, enhancement_id="e-bad", title="bad", report=malformed
+        )
+    assert fresh_store.list_pnl_ledger() == []  # nothing appended on the honest refusal
+
+
+def test_append_duplicate_enhancement_id_is_refused(fresh_store):
+    report = _comparison_report([], [])
+    append_strategy_comparison_row(fresh_store, CONFIG, enhancement_id="e-dup3", title="t", report=report)
+    with pytest.raises(DuplicateEnhancementError):
+        append_strategy_comparison_row(fresh_store, CONFIG, enhancement_id="e-dup3", title="t2", report=report)
+    assert len(fresh_store.list_pnl_ledger()) == 1
+
+
+def test_empty_report_appends_an_honest_all_empty_row(fresh_store):
+    """An all-empty (or, equivalently, all-``insufficient_sample``) comparison report is a VALID
+    outcome to record, never refused — the identical "empty is honest, not an error" discipline
+    ``edge_report.py`` itself already establishes for the source report."""
+    report = _comparison_report([], [])
+    row = append_strategy_comparison_row(
+        fresh_store, CONFIG, enhancement_id="e-empty", title="empty", report=report
+    )
+    assert row["cells"] == {"train": [], "holdout": []}
+
+
+# --- projection: the new row shape passes through verbatim, unlabeled --------------------------
+
+
+def test_projection_serves_the_new_row_shape_verbatim_without_baseline_candidate_labeling(fresh_store):
+    """``ledger_projection`` needs NO change for the new row shape (see
+    ``append_strategy_comparison_row``'s own docstring): its per-row ``baseline``/``candidate``
+    labeling loop finds neither key on a NEW row and silently skips both — the row is served
+    exactly as stored, cells' own ``insufficient_sample`` untouched by the projection."""
+    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=2, net_r=1.0, net_usd=100.0)
+    report = _comparison_report([train_cell], [])
+    append_strategy_comparison_row(fresh_store, CONFIG, enhancement_id="e-proj", title="t", report=report)
+
+    projection = ledger_projection(fresh_store, CONFIG)
+
+    (row,) = projection["rows"]
+    assert row["kind"] == "strategy_comparison"
+    assert row["cells"]["train"][0]["insufficient_sample"] is True  # n=2 < 5, from the SOURCE cell
+    assert "baseline" not in row and "candidate" not in row
+
+
+# --- markdown: the new branch, and old rows staying byte-identical alongside it -----------------
+
+
+def test_regenerating_markdown_from_an_unchanged_comparison_row_is_a_byte_level_no_op(fresh_store):
+    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=1.0, net_usd=100.0)
+    report = _comparison_report([train_cell], [])
+    append_strategy_comparison_row(fresh_store, CONFIG, enhancement_id="e-md3", title="md test", report=report)
+
+    first = render_history_markdown(fresh_store, CONFIG)
+    second = render_history_markdown(fresh_store, CONFIG)
+
+    assert first == second
+    assert "md test" in first
+    assert "strategy" in first and "class" in first  # the new per-cell table header
+
+
+def test_existing_two_way_rows_render_unchanged_alongside_a_new_3way_row(fresh_store, tmp_path):
+    """The critical non-regression proof: an OLD (two-way) row and a NEW (3-way) row in the SAME
+    ledger each render through their OWN branch. Two independent checks:
+      1. the OLD row's rendered SECTION (from its own heading up to the next row's heading) is
+         BYTE-IDENTICAL to what a ledger containing ONLY that old row renders (proving the new
+         branch's mere presence in the source never perturbs the old branch's own output);
+      2. the NEW row's section additionally exists, with its own distinct per-cell table shape.
+    """
+    old_row = _ledger_row("e-old", train_n=5, holdout_n=3)
+    _append(fresh_store, old_row)
+    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=1.0, net_usd=100.0)
+    append_strategy_comparison_row(
+        fresh_store, CONFIG, enhancement_id="e-new", title="new 3way", report=_comparison_report([train_cell], [])
+    )
+
+    combined_md = render_history_markdown(fresh_store, CONFIG)
+
+    only_old_store = JournalStore(str(tmp_path / "only-old.db"), CONFIG)
+    try:
+        _append(only_old_store, old_row)
+        only_old_md = render_history_markdown(only_old_store, CONFIG)
+    finally:
+        only_old_store.close()
+
+    # (1) The OLD row's own section renders byte-identically whether or not a NEW row follows it
+    # in the SAME ledger: `only_old_md` (one row only) is everything render_history_markdown
+    # produces for that row; `combined_md` must carry that EXACT text as its prefix, immediately
+    # followed by the new row's own heading (never anything perturbed at the boundary).
+    assert combined_md.startswith(only_old_md)
+    assert combined_md[len(only_old_md):].startswith("\n## 2. new 3way")
+    assert "insufficient sample" in only_old_md  # holdout_n=3 < 5, the OLD label logic unchanged
+    # (2) The NEW row's own section follows, with its own distinct per-cell table shape.
+    assert "## 2. new 3way" in combined_md
+    assert "e-new" in combined_md
+    assert "strategy | class | side | reaction | feed" in combined_md
+
+
+def test_committed_pnl_history_file_is_not_a_default_target_of_these_tests(fresh_store):
+    """A guardrail against accidentally writing the REAL committed file: every test in this
+    section calls ``render_history_markdown`` (pure, in-memory) or, when writing to disk, passes
+    an explicit ``tmp_path`` target — never bare ``write_history_markdown(store, config)``. This
+    test only documents/pins that discipline; it does not itself touch the filesystem."""
+    src = Path(__file__).read_text()
+    # Every call in THIS test module either omits write_history_markdown entirely or passes an
+    # explicit path=... — never the bare two-arg form that would target the committed file.
+    assert "write_history_markdown(fresh_store, CONFIG)\n" not in src
+    assert "write_history_markdown(store, CONFIG)\n" not in src
diff --git a/apps/backend/app/research/edge_report_cache.py b/apps/backend/app/research/edge_report_cache.py
new file mode 100644
index 0000000..38f7f6e
--- /dev/null
+++ b/apps/backend/app/research/edge_report_cache.py
@@ -0,0 +1,266 @@
+"""A rebuildable, checksum-keyed result cache around ``run_strategy_comparison_report`` (era-5B
+J-08) — makes the era's central "what actually profits" deliverable observable within an
+interactive time budget on a warm cache, instead of the documented ~10+h / ~9.1M-tick sweep the
+``BacktestJobManager`` runs inside ``edge_report.py``'s ``_compute_strategy_comparison_report``
+(the sweep this module accelerates; NOT ``compute_setups``, which already owns its own
+process-local ``_SCAN_CACHE`` in ``setups.py`` — untouched, unrelated, a different cost center).
+
+THIS MODULE stores a REBUILDABLE RESULT ONLY and OWNS NOTHING — mirrors ``bar_index.py``'s
+"metadata/derived-cache only, the canonical computation stays elsewhere" discipline, adapted from
+an indexed lookup to a computed report: ``edge_report.py`` stays the SOLE computer; a cache miss
+(first-ever call, or any input change) always recomputes byte-identically through the caller's
+OWN ``compute_fn`` — this module never re-derives a cell, a measurement, a null baseline, or any
+other research value itself. Deleting the persisted DB file loses nothing and fabricates nothing:
+the very next call simply recomputes and republishes (the ``bar_index.py`` "loss loses and
+fabricates nothing" guarantee, applied to a report instead of an index row).
+
+Two layers, mirroring the plan's two named precedents:
+
+  * **Durable (SQLite, mirrors ``bar_index.py``).** One row per cache key, WAL journal mode +
+    ``busy_timeout``, a hermetic dependency-injected path — survives a backend restart. Every
+    read and write opens its OWN short-lived connection (the ``JournalStore._read_conn()``
+    precedent — see ``store.py`` — NOT ``bar_index.py``'s one-long-lived-connection-with-
+    ``check_same_thread=False`` shape): this module's own concurrency test fires many THREADS at
+    one shared ``EdgeReportCache`` instance, and sharing a single ``sqlite3.Connection`` object
+    across genuinely concurrent callers is unproven and unnecessary here, so it is sidestepped
+    entirely rather than relied upon. A write is one atomic transaction (``INSERT OR REPLACE``
+    inside ``with conn:``) — a reader can only ever observe the fully-committed prior row or the
+    fully-committed new one, never a partial write.
+  * **In-process fast path (mirrors ``setups.py``'s ``_SCAN_CACHE``, lines 357-408).** An
+    INSTANCE-scoped (never module-level) atomic ``(key, result)`` tuple: a single rebind publishes
+    a complete pair in one step, and every reader takes ONE local reference before inspecting it
+    (read-local-reference-before-inspect) — the identical iter-6-hardened pattern, so a concurrent
+    cold-cache reader either observes a complete prior publish or safely (redundantly, harmlessly)
+    recomputes, never a torn key/result pairing. INSTANCE-scoped (not a module global) is
+    deliberate: a freshly constructed ``EdgeReportCache`` always starts at ``_hot = None``, so
+    "no in-process state carried over" (the durability test's simulated-restart premise) is a
+    structural fact of construction, never a promise this class could accidentally break.
+
+**Cache key — why it is FOUR parts, not the three the plan names.** The plan's key description is
+"dataset checksums + strategy registry + ``config_fingerprint``". Three of those are exactly what
+is implemented below — but ``config_fingerprint()`` is *deliberately* scoped to the tape/backtest/
+PnL pipeline (see its own docstring's exclusion rationale in ``config.py``) and excludes several
+field families this report's OWN call graph reads directly:
+
+  * ``pnl_min_sample_size`` — the ``insufficient_sample`` gate ``edge_report.py``'s
+    ``_split_cells`` bakes into every cell. It is fingerprint-excluded because everywhere ELSE
+    that gate is a fresh PRESENTATION overlay recomputed on every read (``pnl_ledger.
+    ledger_projection``), never persisted or cached — this report is the FIRST place its result
+    gets baked into a value that might now be cached, so the "safe to exclude because never
+    cached" premise no longer holds for this caller.
+  * The ``sr_*`` / ``tradability_*`` / ``setups_*`` families (pivot/touch/cluster/band/quality/
+    panel/horizon/threshold parameters) — excluded because levels/tradability/setups are
+    documented as "a SEPARATE research computation... never stamped with, or compared across, a
+    ``config_fingerprint`` anywhere" (``config.py``'s own words), true for every OTHER caller. But
+    ``run_strategy_comparison_report`` calls ``compute_setups`` (which calls ``compute_tradability``,
+    which consumes ``compute_levels``) to resolve each dataset's owning event, so a change to ANY
+    of these parameters genuinely changes this report's cells (band class/side, reaction, or
+    whether an event exists at all).
+
+Rather than hand-enumerate and maintain that exact field list a second time here — the identical
+"second copy of a policy" risk ``config_fingerprint``'s own docstring warns against ("not a
+hand-picked subset") — the key ADDITIONALLY hashes the config's ENTIRE field content (the same
+``dataclasses.asdict`` + canonical-JSON + sha256 mechanism ``config_fingerprint()`` itself uses,
+with NO exclusion set) as a conservative catch-all: any config field change, fingerprinted or not,
+busts this cache. The harmless cost: a purely-operational path field (e.g. a test's own temp
+``journal_db_path``) also busts it on a genuine value change — an extra, harmless recompute,
+accepted in exchange for NEVER silently serving a report computed under different levels/
+tradability/setups/label parameters. ``config_fingerprint()`` and ``strategy_registry()`` stay in
+the key too (not merely subsumed): ``strategy_registry()`` additionally catches a registered
+STRATEGY SET/SHAPE change that no single field's value encodes (e.g. a new strategy id
+registered in code), and ``config_fingerprint()`` is kept as an explicit, literally-named
+component for auditability against the plan's own wording. This is a flagged judgment call — see
+the dev handoff for the full reasoning.
+
+**Store-integrity failures bypass the cache entirely — never risk masking one.** If
+``dataset_store.list()`` reports ANY integrity error, ``get_or_compute`` does not attempt to key
+or consult the cache at all; it calls ``compute_fn`` directly, which raises the SAME explicit
+``EdgeReportError`` the uncached path always has (mirroring ``edge_report.py``'s own "a dataset
+failing integrity verification aborts the whole report" discipline). Excluding corrupt files from
+the signature (the ``setups.py`` ``_store_signature`` precedent) would otherwise risk a corrupt
+file that is NOT part of any previously-cached healthy subset coincidentally matching a stale
+cached key and silently serving a result that never saw the corruption — never worth the risk for
+what is already the rare, explicit-failure path.
+"""
+
+from __future__ import annotations
+
+import dataclasses
+import hashlib
+import json
+import sqlite3
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Callable
+
+from ..config import Config
+from .datasets import DatasetStore
+
+__all__ = ["EdgeReportCache"]
+
+# Mirrors ``bar_index.py``'s ``_BUSY_TIMEOUT_MS`` (5000ms) — the identical brief writer-contention
+# tolerance a low-frequency, small-payload cache needs.
+_BUSY_TIMEOUT_MS = 5000
+
+_SCHEMA = """
+CREATE TABLE IF NOT EXISTS edge_report_cache (
+    cache_key    TEXT PRIMARY KEY,
+    result_json  TEXT NOT NULL,
+    created_utc  TEXT NOT NULL
+)
+"""
+
+
+def _iso_utc_now() -> str:
+    return (
+        datetime.now(timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _canonical(obj: object) -> str:
+    """The one canonical JSON encoding this module HASHES/KEYS with (stable across processes:
+    sorted keys, no whitespace) — the ``datasets.py`` ``_canonical`` idiom, reused by name rather
+    than re-derived a second time. HASHING/KEYING use ONLY: never used to serialize a RESULT for
+    storage (see ``EdgeReportCache._insert``'s own docstring for why sorting there would break
+    response byte-identity) — key order is irrelevant to a hash, but load-bearing for a stored
+    report."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
+
+
+def _config_content_hash(config: Config) -> str:
+    """A conservative hash over EVERY ``Config`` field value (no exclusion set) — see the module
+    docstring's "why four parts" section for exactly why ``config_fingerprint()`` alone is not
+    enough for this specific cache. Reuses ``config_fingerprint()``'s own
+    ``asdict`` + canonical-JSON + sha256 mechanism (never re-derived differently), just without
+    its hand-picked exclusion set."""
+    return hashlib.sha256(_canonical(dataclasses.asdict(config)).encode("utf-8")).hexdigest()
+
+
+def _cache_key(records: list[dict], config: Config) -> str:
+    """The full key material: every registered dataset's (id, checksum) — train and hold-out
+    together, sorted for order-independence (the ``setups.py`` ``_store_signature`` precedent) —
+    plus the strategy registry, ``config_fingerprint()``, and the conservative whole-config
+    content hash (see module docstring). Callers MUST have already confirmed ``records`` came from
+    an error-free ``dataset_store.list()`` call (``get_or_compute`` enforces this — a store with
+    integrity errors never reaches this function)."""
+    payload = {
+        "dataset_checksums": sorted((r["id"], r["checksum"]) for r in records),
+        "strategy_registry": config.strategy_registry(),
+        "config_fingerprint": config.config_fingerprint(),
+        "config_content_hash": _config_content_hash(config),
+    }
+    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
+
+
+class EdgeReportCache:
+    """The persisted, rebuildable edge-report result cache — construct with an explicit, hermetic
+    DB path (the ``BarIndex``/``DatasetStore``/``BarStore`` dependency-injection precedent)."""
+
+    def __init__(self, db_path: str) -> None:
+        self._db_path = str(db_path)
+        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
+        conn = self._connect()
+        try:
+            with conn:
+                conn.execute(_SCHEMA)
+        finally:
+            conn.close()
+        # In-process atomic fast-path slot (mirrors setups.py's `_SCAN_CACHE`) — INSTANCE-scoped,
+        # never a module-level global: see the module docstring for why this is load-bearing for
+        # the durability test's "no in-process state carried over" simulated-restart guarantee.
+        self._hot: tuple[str, dict] | None = None
+
+    @property
+    def db_path(self) -> str:
+        """The resolved DB file path this cache was constructed with (introspection/tests only —
+        never used to bypass ``get_or_compute``)."""
+        return self._db_path
+
+    def _connect(self) -> sqlite3.Connection:
+        """A FRESH, short-lived connection (the ``JournalStore._read_conn()`` precedent — never
+        one long-lived connection shared across threads; see the module docstring). Callers close
+        it explicitly when done."""
+        conn = sqlite3.connect(self._db_path, check_same_thread=False)
+        conn.row_factory = sqlite3.Row
+        conn.execute("PRAGMA journal_mode=WAL")
+        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
+        return conn
+
+    def _select(self, key: str) -> dict | None:
+        conn = self._connect()
+        try:
+            row = conn.execute(
+                "SELECT result_json FROM edge_report_cache WHERE cache_key=?", (key,)
+            ).fetchone()
+        finally:
+            conn.close()
+        return None if row is None else json.loads(row["result_json"])
+
+    def _insert(self, key: str, result: dict) -> None:
+        """One atomic transaction (``INSERT OR REPLACE`` inside ``with conn:``) — a concurrent
+        reader can only ever observe the fully-committed prior row or the fully-committed new one,
+        never a partial write (the torn-read guard's durable-layer half; the in-process tuple is
+        the other half — see the module docstring).
+
+        Deliberately serialized WITHOUT ``sort_keys`` (never ``_canonical`` — that helper is for
+        HASHING/KEYING only, see its own docstring): FastAPI/Starlette's ``JSONResponse`` serializes
+        a route's returned dict in its NATURAL insertion order, never alphabetically — so a
+        cold-miss response (the caller's freshly computed dict, declaration order) and a
+        durable-cache-hit response (this row, ``json.loads`` back into a fresh dict) are
+        byte-identical ONLY if storage preserves that SAME order verbatim. Sorting here would
+        silently make a warm SQLite-served response byte-DIFFER from an uncached one despite
+        carrying identical content — the exact regression this discipline avoids (caught by
+        ``tests/test_mcp_server.py``'s REST/MCP-proxy byte-identity tests, which compare raw wire
+        bytes, not merely parsed-JSON equality)."""
+        conn = self._connect()
+        try:
+            with conn:
+                conn.execute(
+                    "INSERT OR REPLACE INTO edge_report_cache "
+                    "(cache_key, result_json, created_utc) VALUES (?,?,?)",
+                    (key, json.dumps(result), _iso_utc_now()),
+                )
+        finally:
+            conn.close()
+
+    def get_or_compute(
+        self,
+        dataset_store: DatasetStore,
+        config: Config,
+        compute_fn: Callable[[], dict],
+    ) -> dict:
+        """Serve a cached result for the CURRENT ``(dataset_store, config)`` signature, or call
+        ``compute_fn`` (the caller's ONE computation path — this method never computes a report
+        itself) and publish its result to both layers.
+
+        A store-integrity failure bypasses the cache entirely (see module docstring): ``compute_fn``
+        is called directly and its exception (if any) propagates unchanged — no key is ever
+        computed or consulted in that case.
+
+        Atomic against concurrent callers (mirrors ``setups.py``'s iter-6 ``_SCAN_CACHE``
+        hardening): ``self._hot`` is read ONCE into a local (``hot``) before any inspection, so a
+        concurrent rebind by another thread can never be observed as two different values within
+        one call here. A cache miss on multiple concurrent threads only ever costs redundant,
+        harmless recompute (``compute_fn`` is a pure function of its inputs) — it can never produce
+        a torn key/result pairing, on either the in-process tuple or the durable SQLite row (whose
+        own write is one atomic transaction)."""
+        records, errors = dataset_store.list()
+        if errors:
+            return compute_fn()
+        key = _cache_key(records, config)
+
+        hot = self._hot  # read-local-reference-before-inspect
+        if hot is not None and hot[0] == key:
+            return hot[1]
+
+        persisted = self._select(key)
+        if persisted is not None:
+            self._hot = (key, persisted)  # single atomic rebind
+            return persisted
+
+        result = compute_fn()
+        self._insert(key, result)
+        self._hot = (key, result)  # single atomic rebind, published AFTER the durable write
+        return result
diff --git a/apps/backend/tests/test_edge_report_cache.py b/apps/backend/tests/test_edge_report_cache.py
new file mode 100644
index 0000000..7505c94
--- /dev/null
+++ b/apps/backend/tests/test_edge_report_cache.py
@@ -0,0 +1,421 @@
+"""``EdgeReportCache`` (era-5B J-08) — store-level discipline, tested standalone (no FastAPI, no
+real backtests): mirrors ``tests/test_bar_index.py``'s directness. Every test here feeds
+``get_or_compute`` a CHEAP, counting stub instead of a real ``run_strategy_comparison_report``
+sweep — the cache mechanics (keying, durability, concurrency, torn-read safety) are independent of
+what ``compute_fn`` actually does, so proving them against a fast stub is both faster and a purer
+isolation than routing every case through a real multi-strategy backtest. The wiring into
+``edge_report.run_strategy_comparison_report`` (byte-identity against a real, non-degenerate
+report; key-busting under real dataset/config changes) is covered separately in
+``tests/test_edge_report.py``; the route-level DI wiring is covered in ``tests/test_edge_report_api.py``.
+"""
+
+from __future__ import annotations
+
+import dataclasses
+import json
+import threading
+import time
+
+import pytest
+
+from app.config import CONFIG
+from app.providers.base import QuoteEvent, Side, TradeEvent
+from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
+from app.research.edge_report_cache import EdgeReportCache
+
+WINDOW_START, WINDOW_END = "2026-01-02T14:30:00Z", "2026-01-02T14:30:05Z"
+
+
+def _record(dstore: DatasetStore, ticker: str, *, split: str, price: float = 100.0) -> dict:
+    """The minimal REAL ``DatasetStore.record`` public path (never hand-crafted JSON) needed to
+    give a dataset a genuine, content-addressed checksum — no interesting price action is needed
+    here, since these tests never run a real backtest over the recorded content."""
+    events = [
+        QuoteEvent(ticker, 0.0, price, price + 0.02, 800, 800),
+        TradeEvent(ticker, 0.0, price + 0.02, 100, Side.UNKNOWN),
+    ]
+    return dstore.record(
+        symbol=ticker, source=f"cache-test {ticker}", source_kind="reference", source_id=ticker,
+        split=split, window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
+        data_feed="sim", epoch_anchor=CONFIG.sim_session_anchor_epoch, events=events,
+    )
+
+
+class _CountingCompute:
+    """A stub ``compute_fn`` that counts its own invocations and returns a fixed, report-shaped
+    (but otherwise arbitrary) dict — never a real backtest sweep (see module docstring)."""
+
+    def __init__(self, result: dict | None = None) -> None:
+        self.calls = 0
+        self._result = result if result is not None else {"train": {"cells": []}, "holdout": {"cells": []}}
+
+    def __call__(self) -> dict:
+        self.calls += 1
+        return self._result
+
+
+# --- cold miss -> compute once, persist both layers ------------------------------------------
+
+
+def test_cold_cache_miss_calls_compute_fn_once_and_returns_its_result(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    compute = _CountingCompute({"train": {"cells": ["x"]}, "holdout": {"cells": []}})
+
+    result = cache.get_or_compute(dstore, CONFIG, compute)
+
+    assert compute.calls == 1
+    assert result == {"train": {"cells": ["x"]}, "holdout": {"cells": []}}
+
+
+def test_warm_in_process_hit_never_calls_compute_fn_again(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    compute = _CountingCompute()
+
+    first = cache.get_or_compute(dstore, CONFIG, compute)
+    second = cache.get_or_compute(dstore, CONFIG, compute)
+
+    assert compute.calls == 1  # the SECOND call never recomputes
+    assert first == second
+
+
+def test_result_persists_to_the_durable_row_on_a_cold_miss(tmp_path):
+    """The durable SQLite row exists after a cold-miss compute — proven directly against the
+    table, not merely inferred from a second in-process hit (the in-process and durable layers are
+    tested independently; see the durability test below for the layer that matters most)."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    db_path = str(tmp_path / "cache.db")
+    cache = EdgeReportCache(db_path)
+    compute = _CountingCompute({"train": {"cells": []}, "holdout": {"cells": []}})
+
+    cache.get_or_compute(dstore, CONFIG, compute)
+
+    import sqlite3
+
+    conn = sqlite3.connect(db_path)
+    try:
+        rows = conn.execute("SELECT cache_key, result_json FROM edge_report_cache").fetchall()
+    finally:
+        conn.close()
+    assert len(rows) == 1
+    assert json.loads(rows[0][1]) == {"train": {"cells": []}, "holdout": {"cells": []}}
+
+
+# --- durability across a simulated backend restart --------------------------------------------
+
+
+def test_durability_across_simulated_restart_serves_prior_result_without_recompute(tmp_path):
+    """The DoD's literal scenario: construct a FRESH ``EdgeReportCache`` at the SAME persisted
+    path (no in-process state carried over — a genuinely new instance, the ``BarIndex``
+    "delete the DB file and reproduce identical lookups" precedent, applied to "restart the
+    process and reproduce the identical warm report")."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    db_path = str(tmp_path / "cache.db")
+
+    warm_result = {"train": {"cells": ["real-shape"]}, "holdout": {"cells": []}}
+    original = EdgeReportCache(db_path)
+    original_compute = _CountingCompute(warm_result)
+    original.get_or_compute(dstore, CONFIG, original_compute)
+    assert original_compute.calls == 1
+
+    # Simulate a backend restart: a BRAND NEW instance, no in-process state carried over.
+    restarted = EdgeReportCache(db_path)
+    restarted_compute = _CountingCompute({"should": "never be returned"})
+
+    served = restarted.get_or_compute(dstore, CONFIG, restarted_compute)
+
+    assert served == warm_result
+    assert restarted_compute.calls == 0  # never recomputed — served from the durable row alone
+
+
+def test_result_round_trips_byte_identically_through_json_persistence(tmp_path):
+    """Floats, nested lists/dicts, and ``None`` all survive a JSON round-trip through the durable
+    layer byte-identically (``json.dumps(..., sort_keys=True)`` equality) — the exact equality
+    discipline the determinism DoD requires."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    db_path = str(tmp_path / "cache.db")
+    original_result = {
+        "train": {"cells": [{"n": 3, "net_r": 5.050000000001056, "win_rate": None, "tags": [1, 2, 3]}]},
+        "holdout": {"cells": []},
+        "surviving_train_cells": [],
+    }
+    EdgeReportCache(db_path).get_or_compute(dstore, CONFIG, _CountingCompute(original_result))
+
+    reloaded = EdgeReportCache(db_path).get_or_compute(dstore, CONFIG, _CountingCompute())
+
+    assert json.dumps(reloaded, sort_keys=True) == json.dumps(original_result, sort_keys=True)
+
+
+def test_result_key_order_is_preserved_through_the_durable_round_trip_not_merely_content_equal(tmp_path):
+    """Byte-identity needs MORE than content equality: FastAPI/Starlette serializes a route's
+    returned dict in its NATURAL insertion order (never alphabetically), so a durable-cache-hit
+    response must reconstruct the SAME key order as the original fresh dict — not merely equal
+    content under a sorted comparison. Deliberately picks a top-level key ("register") that would
+    sort to a DIFFERENT position than its declared one, so a stray ``sort_keys=True`` anywhere on
+    the stored blob would flip this test red (this is the exact regression
+    ``tests/test_mcp_server.py``'s raw-bytes REST/MCP-proxy comparison caught for real)."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    db_path = str(tmp_path / "cache.db")
+    original_result = {
+        "register": "z-would-sort-last-if-broken",
+        "pnl_min_sample_size": 5,
+        "train": {"cells": []},
+        "holdout": {"cells": []},
+        "surviving_train_cells": [],
+    }
+    EdgeReportCache(db_path).get_or_compute(dstore, CONFIG, _CountingCompute(original_result))
+
+    reloaded = EdgeReportCache(db_path).get_or_compute(dstore, CONFIG, _CountingCompute())
+
+    assert list(reloaded.keys()) == list(original_result.keys())
+    assert json.dumps(reloaded) == json.dumps(original_result)  # NO sort_keys -- true wire-byte identity
+
+
+# --- key-busting: dataset set, strategy registry, config_fingerprint, and the catch-all -------
+
+
+def test_adding_a_dataset_busts_the_cache(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))
+
+    _record(dstore, "SYN-B", split=SPLIT_HOLDOUT)
+    second = _CountingCompute({"v": 2})
+    result = cache.get_or_compute(dstore, CONFIG, second)
+
+    assert second.calls == 1
+    assert result == {"v": 2}
+
+
+def test_removing_a_dataset_busts_the_cache(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    meta_b = _record(dstore, "SYN-B", split=SPLIT_HOLDOUT)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))
+
+    (tmp_path / "datasets" / f"{meta_b['id']}.json").unlink()
+    second = _CountingCompute({"v": 2})
+    result = cache.get_or_compute(dstore, CONFIG, second)
+
+    assert second.calls == 1
+    assert result == {"v": 2}
+
+
+def test_strategy_registry_affecting_field_busts_the_cache(tmp_path):
+    """A ``structure_tape_*`` field change (``config_fingerprint``-EXCLUDED, per config.py's own
+    documented rationale — arming-only, never fingerprinted) still changes
+    ``config.strategy_registry()``'s own output, so the cache must bust on it regardless."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))
+
+    changed_config = dataclasses.replace(
+        CONFIG, structure_tape_proximity_band_bps=CONFIG.structure_tape_proximity_band_bps + 1.0
+    )
+    assert changed_config.config_fingerprint() == CONFIG.config_fingerprint()  # sanity: excluded
+    second = _CountingCompute({"v": 2})
+    result = cache.get_or_compute(dstore, changed_config, second)
+
+    assert second.calls == 1
+    assert result == {"v": 2}
+
+
+def test_config_fingerprint_affecting_field_busts_the_cache(tmp_path):
+    """A field that DOES move ``config_fingerprint()`` (and is unrelated to the strategy registry)
+    busts the cache too — proof the fingerprint component is genuinely load-bearing, not merely
+    subsumed."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))
+
+    changed_config = dataclasses.replace(
+        CONFIG, backtest_null_entry_count=CONFIG.backtest_null_entry_count + 1
+    )
+    assert changed_config.config_fingerprint() != CONFIG.config_fingerprint()  # sanity: fingerprinted
+    second = _CountingCompute({"v": 2})
+    result = cache.get_or_compute(dstore, changed_config, second)
+
+    assert second.calls == 1
+    assert result == {"v": 2}
+
+
+def test_pnl_min_sample_size_change_busts_the_cache_despite_fingerprint_exclusion(tmp_path):
+    """``pnl_min_sample_size`` is EXCLUDED from ``config_fingerprint()`` (config.py's own
+    documented "serving/presentation-only... two journals... MUST share a fingerprint"
+    rationale) AND is not read by ``strategy_registry()`` — yet it directly gates every cell's own
+    ``insufficient_sample`` label inside ``edge_report.py``'s ``_split_cells``. This is exactly the
+    gap the module docstring's "why four parts" section documents; the whole-config-content
+    catch-all component is what catches it."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))
+
+    changed_config = dataclasses.replace(CONFIG, pnl_min_sample_size=CONFIG.pnl_min_sample_size + 1)
+    assert changed_config.config_fingerprint() == CONFIG.config_fingerprint()  # sanity: excluded
+    assert changed_config.strategy_registry() == CONFIG.strategy_registry()  # sanity: unaffected
+    second = _CountingCompute({"v": 2})
+    result = cache.get_or_compute(dstore, changed_config, second)
+
+    assert second.calls == 1
+    assert result == {"v": 2}
+
+
+def test_tradability_field_change_busts_the_cache_despite_fingerprint_exclusion(tmp_path):
+    """``tradability_band_cap_per_side`` is ALSO ``config_fingerprint``-excluded (the "separate
+    research computation" rationale) but genuinely changes what ``compute_setups`` (hence this
+    report's cells) can resolve — the identical gap ``pnl_min_sample_size`` proves above, for the
+    other named family (``sr_*`` / ``tradability_*`` / ``setups_*``)."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))
+
+    changed_config = dataclasses.replace(
+        CONFIG, tradability_band_cap_per_side=CONFIG.tradability_band_cap_per_side + 1
+    )
+    assert changed_config.config_fingerprint() == CONFIG.config_fingerprint()  # sanity: excluded
+    second = _CountingCompute({"v": 2})
+    result = cache.get_or_compute(dstore, changed_config, second)
+
+    assert second.calls == 1
+    assert result == {"v": 2}
+
+
+def test_unchanged_inputs_reuse_the_cache_across_a_fresh_config_object_with_equal_values(tmp_path):
+    """The counter-proof: a fresh ``dataclasses.replace(CONFIG)`` with NO field actually changed
+    (a new Python object, equal content) must still HIT — the key is content-based, never
+    ``id(config)``-based (unlike ``setups.py``'s in-process-only ``_SCAN_CACHE``, which this
+    module's own docstring explains cannot be reused here because it would not survive a restart)."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))
+
+    equal_but_distinct_config = dataclasses.replace(CONFIG)
+    assert equal_but_distinct_config is not CONFIG
+    second = _CountingCompute({"v": 2})
+    result = cache.get_or_compute(dstore, equal_but_distinct_config, second)
+
+    assert second.calls == 0  # never recomputed — content-equal, so still a hit
+    assert result == {"v": 1}
+
+
+# --- store-integrity failures bypass the cache entirely ----------------------------------------
+
+
+def test_store_integrity_error_bypasses_the_cache_and_persists_nothing(tmp_path):
+    dstore = DatasetStore(tmp_path / "datasets")
+    meta = _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    path = tmp_path / "datasets" / f"{meta['id']}.json"
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
+    path.write_text(json.dumps(data))
+    db_path = str(tmp_path / "cache.db")
+    cache = EdgeReportCache(db_path)
+
+    class _Boom(Exception):
+        pass
+
+    def _raising_compute():
+        raise _Boom("the real EdgeReportError path, standing in for it here")
+
+    with pytest.raises(_Boom):
+        cache.get_or_compute(dstore, CONFIG, _raising_compute)
+
+    import sqlite3
+
+    conn = sqlite3.connect(db_path)
+    try:
+        rows = conn.execute("SELECT * FROM edge_report_cache").fetchall()
+    finally:
+        conn.close()
+    assert rows == []  # nothing persisted on the integrity-error bypass path
+
+
+# --- concurrency / torn-read (mirrors test_setups.py's atomic-publish guard) --------------------
+
+
+def test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair(tmp_path):
+    """Many threads racing a COLD cache (nothing published yet, neither in-process nor durable)
+    with a deliberately widened publish window (a sleep injected into ``compute_fn``, forcing
+    genuine overlap around the moment the winning thread's result would be published) must ALL
+    return a real, non-``None``, byte-identical result — never a crash, never a torn key/result
+    pairing. Mirrors ``tests/test_setups.py``'s
+    ``test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair`` exactly (same
+    barrier-based pattern), applied to ``EdgeReportCache`` instead of the module-level
+    ``_SCAN_CACHE``."""
+    dstore = DatasetStore(tmp_path / "datasets")
+    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
+    cache = EdgeReportCache(str(tmp_path / "cache.db"))
+    fixed_result = {"train": {"cells": [{"n": 5, "net_r": 1.23456789}]}, "holdout": {"cells": []}}
+
+    def _slow_compute() -> dict:
+        time.sleep(0.05)  # widen the window so concurrent callers genuinely overlap the publish
+        return fixed_result
+
+    thread_count = 16
+    results: list[dict | None] = [None] * thread_count
+    errors: list[BaseException] = []
+    start_barrier = threading.Barrier(thread_count)
+
+    def _call(index: int) -> None:
+        start_barrier.wait()  # every thread reaches get_or_compute at roughly the same instant
+        try:
+            results[index] = cache.get_or_compute(dstore, CONFIG, _slow_compute)
+        except BaseException as exc:  # pragma: no cover -- failure path only
+            errors.append(exc)
+
+    threads = [threading.Thread(target=_call, args=(i,)) for i in range(thread_count)]
+    for t in threads:
+        t.start()
+    for t in threads:
+        t.join(timeout=10.0)
+
+    assert errors == [], f"a concurrent cold-cache read raised (never a torn read, never a crash): {errors}"
+    assert all(r is not None for r in results), (
+        "every concurrent caller must return a real result -- a None here IS the torn-read bug"
+    )
+    expected = json.dumps(results[0], sort_keys=True)
+    assert all(json.dumps(r, sort_keys=True) == expected for r in results), (
+        "every concurrent caller must observe the SAME byte-identical result -- a mismatch would "
+        "mean some reader saw a torn/partial key-result pairing"
+    )
... [diff_bound] apps/backend/tests/test_edge_report_cache.py: 27 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_pnl_history.py b/apps/backend/tests/test_pnl_history.py
new file mode 100644
index 0000000..d22293c
--- /dev/null
+++ b/apps/backend/tests/test_pnl_history.py
@@ -0,0 +1,185 @@
+"""The PnL-history CLI (``app.research.pnl_history``) — era-5B J-08 additive ``--append-report``
++ ``--out`` flags. Every test here targets an explicit ``tmp_path`` output (via ``--out`` /
+``path=``) and a ``tmp_path``-scoped journal DB (via ``TAPEOLOGY_JOURNAL_DB``) — NEVER the real
+committed ``reports/pnl/pnl-history.md`` or the real operator journal (Key Test Scenario 9's
+"never the committed file" discipline).
+
+``append_strategy_comparison_row``'s own composition/labeling logic (cell shape, no-pooling,
+``insufficient_sample`` verbatim, malformed-report refusal) is exhaustively covered in
+``tests/test_pnl_ledger.py``; this file covers ONLY the CLI-level plumbing (argument handling, the
+append-then-render sequencing, and that omitting the new flags reproduces the pre-J-08 behaviour
+byte-for-byte).
+"""
+
+from __future__ import annotations
+
+import json
+import sys
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG, STRATEGY_V1_ID
+from app.research import pnl_history
+from app.research.pnl_history import append_strategy_comparison_and_render
+from app.research.pnl_ledger import LedgerCompositionError, REGISTER
+from app.research.store import DuplicateEnhancementError, JournalStore
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+
+
+def _report(train_cells: list[dict] | None = None, holdout_cells: list[dict] | None = None) -> dict:
+    return {
+        "register": REGISTER,
+        "pnl_min_sample_size": CONFIG.pnl_min_sample_size,
+        "train": {"cells": train_cells or []},
+        "holdout": {"cells": holdout_cells or []},
+        "surviving_train_cells": [],
+    }
+
+
+def _cell(*, n: int = 6, net_r: float = 1.0, net_usd: float = 100.0) -> dict:
+    return {
+        "strategy_id": STRATEGY_V1_ID,
+        "band_class": "A",
+        "band_side": "resistance",
+        "reaction": "broke",
+        "feed": "sim",
+        "dataset_ids": ["ds-1"],
+        "measurement": {
+            "n": n, "gross_r": net_r, "net_r": net_r, "gross_usd": net_usd, "net_usd": net_usd,
+            "win_rate": 1.0, "max_drawdown_r": 0.0,
+        },
+        "null_baseline": {
+            "n": 100, "gross_r": -1.0, "net_r": -1.0, "gross_usd": -100.0, "net_usd": -100.0,
+            "win_rate": 0.4, "max_drawdown_r": 1.0,
+        },
+        "insufficient_sample": n < CONFIG.pnl_min_sample_size,
+    }
+
+
+# --- append_strategy_comparison_and_render (the function J-08 adds) ----------------------------
+
+
+def test_append_and_render_writes_the_new_row_and_regenerates_markdown(tmp_path):
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    out_path = tmp_path / "history.md"
+    try:
+        written = append_strategy_comparison_and_render(
+            store, CONFIG,
+            enhancement_id="e-cli-1", title="cli append test",
+            report=_report([_cell()]), path=out_path,
+        )
+    finally:
+        store.close()
+
+    assert written == out_path
+    text = out_path.read_text()
+    assert "cli append test" in text
+    assert "e-cli-1" in text
+    assert "strategy | class | side | reaction | feed" in text
+
+
+def test_append_and_render_raises_and_writes_nothing_on_a_malformed_report(tmp_path):
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    out_path = tmp_path / "history.md"
+    try:
+        with pytest.raises(LedgerCompositionError):
+            append_strategy_comparison_and_render(
+                store, CONFIG,
+                enhancement_id="e-cli-bad", title="bad",
+                report={"train": {"cells": []}},  # missing "holdout"
+                path=out_path,
+            )
+    finally:
+        store.close()
+    assert store.list_pnl_ledger() == []  # nothing appended
+    assert not out_path.exists()  # rendering never ran either — the honest refusal wrote nothing
+
+
+def test_append_and_render_duplicate_enhancement_id_writes_nothing_new(tmp_path):
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    out_path = tmp_path / "history.md"
+    try:
+        append_strategy_comparison_and_render(
+            store, CONFIG, enhancement_id="e-cli-dup", title="t1", report=_report([_cell()]), path=out_path
+        )
+        with pytest.raises(DuplicateEnhancementError):
+            append_strategy_comparison_and_render(
+                store, CONFIG, enhancement_id="e-cli-dup", title="t2", report=_report([_cell()]), path=out_path
+            )
+    finally:
+        store.close()
+    assert len(store.list_pnl_ledger()) == 1  # the refused second append changed nothing
+
+
+# --- main() CLI wiring: every call targets --out (never the real committed path) ----------------
+
+
+def test_main_without_append_flag_matches_the_pre_j08_render_only_behavior(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    out_path = tmp_path / "history.md"
+    monkeypatch.setattr(sys, "argv", ["pnl_history", "--out", str(out_path)])
+
+    exit_code = pnl_history.main()
+
+    assert exit_code == 0
+    assert out_path.exists()
+    assert "ledger is empty" in out_path.read_text()  # honest empty state, nothing appended
+
+
+def test_main_with_append_report_flag_appends_and_renders_in_one_step(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    report_path = tmp_path / "report.json"
+    report_path.write_text(json.dumps(_report([_cell()])))
+    out_path = tmp_path / "history.md"
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "pnl_history", "--append-report", str(report_path),
+            "--enhancement-id", "e-main-append", "--title", "main append test",
+            "--out", str(out_path),
+        ],
+    )
+
+    exit_code = pnl_history.main()
+
+    assert exit_code == 0
+    text = out_path.read_text()
+    assert "main append test" in text
+    assert "e-main-append" in text
+
+
+def test_main_append_report_missing_required_flags_is_an_explicit_error(tmp_path, monkeypatch, capsys):
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    report_path = tmp_path / "report.json"
+    report_path.write_text(json.dumps(_report([_cell()])))
+    out_path = tmp_path / "history.md"
+    monkeypatch.setattr(
+        sys, "argv", ["pnl_history", "--append-report", str(report_path), "--out", str(out_path)]
+    )  # --enhancement-id / --title both omitted
+
+    exit_code = pnl_history.main()
+
+    assert exit_code == 1
+    assert "--enhancement-id" in capsys.readouterr().err
+    assert not out_path.exists()  # nothing rendered on the argument-validation refusal
+
+
+def test_main_append_report_malformed_json_file_is_an_explicit_error(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    report_path = tmp_path / "report.json"
+    report_path.write_text(json.dumps({"train": {"cells": []}}))  # missing "holdout"
+    out_path = tmp_path / "history.md"
+    monkeypatch.setattr(
+        sys, "argv",
+        [
+            "pnl_history", "--append-report", str(report_path),
+            "--enhancement-id", "e-malformed", "--title", "t", "--out", str(out_path),
+        ],
+    )
+
+    exit_code = pnl_history.main()
+
+    assert exit_code == 1
+    assert not out_path.exists()
```
