# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 57. Shown in full: 13.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/monitor.py` (988 lines not shown)
- `apps/backend/app/research/routes.py` (936 lines not shown)
- `apps/backend/app/research/stance.py` (209 lines not shown)
- `apps/backend/app/research/store.py` (758 lines not shown)
- `apps/backend/app/research/studies.py` (471 lines not shown)
- `apps/backend/app/research/taxonomy.py` (828 lines not shown)
- `apps/backend/app/research/verdict.py` (440 lines not shown)
- `apps/backend/tests/test_analytics.py` (374 lines not shown)
- `apps/backend/tests/test_analytics_api.py` (110 lines not shown)
- `apps/backend/tests/test_backtests.py` (52 lines not shown)
- `apps/backend/tests/test_backtests_api.py` (19 lines not shown)
- `apps/backend/tests/test_bars_api.py` (17 lines not shown)
- `apps/backend/tests/test_copy_discipline.py` (133 lines not shown)
- `apps/backend/tests/test_datasets_api.py` (17 lines not shown)
- `apps/backend/tests/test_excursions.py` (362 lines not shown)
- `apps/backend/tests/test_execution_checks.py` (309 lines not shown)
- `apps/backend/tests/test_grades.py` (131 lines not shown)
- `apps/backend/tests/test_journal_list.py` (280 lines not shown)
- `apps/backend/tests/test_journal_migration.py` (1625 lines not shown)
- `apps/backend/tests/test_levels_api.py` (17 lines not shown)
- `apps/backend/tests/test_observer_equivalence.py` (92 lines not shown)
- `apps/backend/tests/test_research_action.py` (267 lines not shown)
- `apps/backend/tests/test_research_api.py` (839 lines not shown)
- `apps/backend/tests/test_research_checklist.py` (437 lines not shown)
- `apps/backend/tests/test_research_excursions_integration.py` (228 lines not shown)
- `apps/backend/tests/test_research_execution_checks_api.py` (185 lines not shown)
- `apps/backend/tests/test_research_freshness_integration.py` (212 lines not shown)
- `apps/backend/tests/test_research_geometry.py` (291 lines not shown)
- `apps/backend/tests/test_research_hints.py` (472 lines not shown)
- `apps/backend/tests/test_research_hints_api.py` (270 lines not shown)
- `apps/backend/tests/test_research_lifecycle.py` (190 lines not shown)
- `apps/backend/tests/test_research_marks.py` (122 lines not shown)
- `apps/backend/tests/test_research_monitor.py` (910 lines not shown)
- `apps/backend/tests/test_research_resolve.py` (238 lines not shown)
- `apps/backend/tests/test_research_review.py` (274 lines not shown)
- `apps/backend/tests/test_research_risk_flags.py` (300 lines not shown)
- `apps/backend/tests/test_research_stance.py` (201 lines not shown)
- `apps/backend/tests/test_research_store.py` (507 lines not shown)
- `apps/backend/tests/test_setups_api.py` (17 lines not shown)
- `apps/backend/tests/test_studies.py` (357 lines not shown)
- `apps/backend/tests/test_studies_api.py` (298 lines not shown)
- `apps/backend/tests/test_studies_reference.py` (192 lines not shown)
- `apps/backend/tests/test_tradability_api.py` (17 lines not shown)
- `apps/backend/tests/test_verdict_engine.py` (462 lines not shown)

```diff
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index a365f78..7042660 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -144,22 +144,18 @@ async def _warm_symbol_universe_bg(adapter: MarketDataAdapter) -> None:
 async def lifespan(app: FastAPI):
     # Research store + registry (capabilities 23 / 28). The journal-scoped SQLite store is opened at
     # the operator's resolved DB path (``TAPEOLOGY_JOURNAL_DB`` or the config default); the registry
-    # owns the per-ticker monitors and is wired to the WatchManager's engine-created hook so every
-    # watch gets a monitor attached at the engine's observer seam. A startup SWEEP resolves any
-    # thesis left ``active`` in the DB by a prior process to ``expired`` (lifecycle honesty — no
-    # orphaned active theses). A test injects its own registry via ``set_registry`` BEFORE the app
-    # starts, in which case we leave it in place (skip building the default file store).
+    # owns the backtest/edge-compute job managers. era-5D J-01 ("The Clean Slate" demolition
+    # interlude) removed the WatchManager engine-created wiring and the startup expiry sweep that
+    # used to run here (both were journal-era thesis-lifecycle machinery, deleted along with
+    # ``ResearchRegistry.on_engine_created``/``.startup_sweep``). A test injects its own registry via
+    # ``set_registry`` BEFORE the app starts, in which case we leave it in place (skip building the
+    # default file store).
     own_registry = False
     if get_registry_or_none() is None:
         store = JournalStore(CONFIG.journal_db_path_resolved(), CONFIG)
         registry = ResearchRegistry(store, CONFIG)
         set_registry(registry)
-        manager.set_on_engine_created(registry.on_engine_created)
         own_registry = True
-        try:
-            registry.startup_sweep()
-        except Exception:
-            logger.exception("research startup sweep failed")
 
     # Fire-and-forget the symbol-universe warm at startup through the NEUTRAL adapter seam (J-30)
     # — main.py never names the SDK or the universe cache. Non-blocking: startup does not wait on
@@ -179,16 +175,13 @@ async def lifespan(app: FastAPI):
         if own_registry:
             reg = get_registry_or_none()
             if reg is not None:
-                # Drain any in-flight replay-study jobs (capability 32) and backtest jobs
-                # (era-3 capability 4, J-03) before closing the store so a daemon worker never
-                # writes to a closed store on shutdown.
-                with contextlib.suppress(Exception):
-                    reg.study_jobs.join_all(timeout=5.0)
+                # Drain any in-flight backtest jobs (era-3 capability 4, J-03) before closing the
+                # store so a daemon worker never writes to a closed store on shutdown. era-5D J-01:
+                # the replay-study job manager this used to also drain was deleted whole.
                 with contextlib.suppress(Exception):
                     reg.backtest_jobs.join_all(timeout=5.0)
                 reg.store.close()
             set_registry(None)
-            manager.set_on_engine_created(None)
 
 
 app = FastAPI(title="Tapeology", version="0.1.0", lifespan=lifespan)
diff --git a/apps/backend/app/research/analytics.py b/apps/backend/app/research/analytics.py
deleted file mode 100644
index 73a00d9..0000000
--- a/apps/backend/app/research/analytics.py
+++ /dev/null
@@ -1,254 +0,0 @@
-"""Segregated journal analytics (capability 31, J-59) — the SINGLE-owner read-only aggregator.
-
-This is the ONE place the J-59 aggregates are computed. The single serving path
-``GET /research/analytics`` renders this module's projection VERBATIM (the frontend derives nothing).
-
-What it does — and, just as bindingly, what it MUST NOT do:
-
-  * **Reads persisted rows ONLY.** It aggregates already-persisted values — the ``theses`` rows
-    (status / setup / direction / feed / fingerprint / grades / review tags), the persisted excursion
-    records (``theses.excursions``), the action marks (``actions``), and the append-only verdict
-    timeline (``verdict_events``). It NEVER recomputes any underlying canonical value: no re-derived
-    verdict, no second excursion math, no second R formula. Realized-R for the acted-trade block comes
-    from the ONE registered R path (``marks.marks_projection`` — the row-27 projection), never a second
-    formula or inline arithmetic.
-
-  * **Never pools.** The top-level shape is a list of partitions keyed by (``data_feed``,
-    ``config_fingerprint``); within a partition, groups are per ``setup_type`` × ``direction``. There
-    is NO "all" / pooled / overall rollup anywhere (the honesty anti-goal — analytics MUST NOT pool
-    across feeds or fingerprints).
-
-  * **Abandonment stays visible.** Abandoned theses remain in every denominator (``n``) — no
-    survivorship pruning — AND surface as their own ``abandonment`` count (present even when 0).
-
-  * **Insufficient-sample is an explicit gate, never a silent percentage.** A group whose ``n`` is
-    below ``Config.analytics_min_sample_size`` carries ``insufficient_sample: True`` with ``n`` still
-    present; the distributions are still computed (the frontend chooses to show the marker instead of
-    bare numbers), so the data is honest either way.
-
-  * **Truncated horizons counted separately.** A truncated horizon (the stream/gap cut it short
-    before +1R / -1R could be answered) is counted in its own ``truncated`` bucket per horizon —
-    NEVER folded into the resolved ternary buckets, never extrapolated.
-
-  * **Honest omission.** Median time-to-confirm is ``None`` for a group with no confirmation (never a
-    fabricated zero). Median spread/R is ``None`` where no anchored population carries one. The two
-    excursion populations (confirmation-anchored / entry-anchored) are kept structurally apart.
-
-  * **Deterministic.** Output depends only on the persisted rows + the config — two identical calls
-    over a fixed DB are byte-equal (groups + partitions are emitted in a stable sorted order, R
-    figures rounded the same way the persisted records are).
-"""
-
-from __future__ import annotations
-
-import statistics
-
-from ..config import Config
-from .marks import marks_projection
-from .store import JournalStore, ThesisRecord
-
-# The terminal status that is the abandonment bucket (kept in n; surfaced as its own count).
-_ABANDONED = "abandoned"
-
-# The published-verdict id the median time-to-confirm anchors on (first such timeline event wins).
-_CONFIRMING = "confirming"
-
-# The confirmation-anchored excursion population id (the segregated population analytics aggregates;
-# the entry-anchored population's R lives in the acted-trade block via the marks projection instead).
-_CONFIRMATION_POP = "confirmation"
-
-# The ternary outcome ids (mirrors excursions.py — LABELS only, never a numeric score). A truncated
-# horizon (outcome still ``None`` AND ``truncated``) is counted in its OWN bucket, never these three.
-_TERNARY_IDS = ("+1R_first", "-1R_first", "neither_within_horizon")
-
-
-def _median_or_none(values: list[float]) -> float | None:
-    """The median of ``values`` rounded to 4 dp (byte-stable), or ``None`` for an empty list.
-
-    ``None`` is the honest omission (no data → no number, never a fabricated zero). Rounding mirrors
-    the persisted excursion records' 4-dp discipline so two runs are byte-equal."""
-    if not values:
-        return None
-    return round(statistics.median(values), 4)
-
-
-def _confirm_logical_ts(events: list) -> float | None:
-    """The logical-time instant of the FIRST published ``confirming`` event (else ``None``).
-
-    Reads the append-only verdict timeline VERBATIM — never recomputed. ``None`` (no confirmation ever
-    published) is the honest omission the median treats as "this thesis contributes no time-to-confirm".
-    """
-    for ev in events:  # the store returns events in insertion (logical) order
-        if ev.verdict == _CONFIRMING:
-            return ev.logical_ts
-    return None
-
-
-def _empty_horizon_row(horizon: float) -> dict:
-    """A zeroed per-horizon ternary row (all buckets + truncated at 0, no spread/R yet)."""
-    return {
-        "horizon": horizon,
-        "+1R_first": 0,
-        "-1R_first": 0,
-        "neither_within_horizon": 0,
-        "truncated": 0,
-        "median_spread_per_r": None,
-    }
-
-
-def _aggregate_group(
-    theses: list[ThesisRecord],
-    *,
-    store: JournalStore,
-    config: Config,
-) -> dict:
-    """Aggregate ONE (feed, fingerprint, setup, direction) group from its persisted theses.
-
-    Every figure is a read/aggregation of already-persisted values — no canonical value is recomputed.
-    Realized-R reuses ``marks.marks_projection`` (the ONE registered R path); excursion ternaries /
-    truncation / spread-at-anchor come from the persisted ``theses.excursions`` record; the
-    time-to-confirm comes from the persisted append-only timeline.
-    """
-    n = len(theses)
-    abandonment = sum(1 for t in theses if t.status == _ABANDONED)
-
-    # --- confirmation-anchored excursion distribution (per configured horizon) ------------------
-    # Per horizon: ternary bucket counts + a separate truncated count + the spreads/R for the median.
-    horizon_rows: dict[float, dict] = {
-        h: _empty_horizon_row(h) for h in config.excursion_horizons_seconds
-    }
-    horizon_spreads: dict[float, list[float]] = {h: [] for h in config.excursion_horizons_seconds}
-
-    for t in theses:
-        excursions = t.excursions
-        if not excursions or not excursions.get("tracked"):
-            continue  # absent / not-tracked record contributes nothing (honest omission, never a zero)
-        pop = excursions.get("populations", {}).get(_CONFIRMATION_POP)
-        if not pop:
-            continue
-        r_basis_value = pop.get("r_basis")
-        spread_at_anchor = pop.get("spread_at_anchor")
-        for hz in pop.get("horizons", []):
-            h = hz.get("horizon")
-            row = horizon_rows.get(h)
-            if row is None:
-                continue  # a horizon not in the current config (a pre-config-change record) is skipped
-            outcome = hz.get("outcome")
-            truncated = bool(hz.get("truncated"))
-            if truncated and outcome is None:
-                # Truncated BEFORE the ternary could resolve — its OWN bucket, never a resolved bucket.
-                row["truncated"] += 1
-            elif outcome in _TERNARY_IDS:
-                row[outcome] += 1
-            # An open-but-not-truncated horizon (outcome None, not truncated) is genuinely undetermined
-            # and contributes to NO bucket (neither resolved nor truncated) — never fabricated.
-            # Spread/R (the no-cost caveat as a number) — only when both the anchor spread and a
-            # positive R basis are present (a degenerate R == 0 yields no honest cost figure).
-            if spread_at_anchor is not None and r_basis_value:
-                horizon_spreads[h].append(spread_at_anchor / r_basis_value)
-
-    for h, row in horizon_rows.items():
-        row["median_spread_per_r"] = _median_or_none(horizon_spreads[h])
-
-    confirmation_excursions = {
-        "horizons": [horizon_rows[h] for h in config.excursion_horizons_seconds]
-    }
-
-    # --- median time-to-confirm (declaration -> first published confirming, logical time) -------
-    times_to_confirm: list[float] = []
-    for t in theses:
-        confirm_ts = _confirm_logical_ts(store.verdict_events(t.id))
-        if confirm_ts is not None:
-            times_to_confirm.append(confirm_ts - t.created_logical_ts)
-    median_time_to_confirm = _median_or_none(times_to_confirm)
-
-    # --- tag frequencies (USER-confirmed reviews only — machine suggestions never counted) ------
-    tag_counts: dict[str, int] = {}
-    for t in theses:
-        if not t.reviewed or not t.review_tags:
-            continue
-        for tag in t.review_tags:
-            tag_counts[tag] = tag_counts.get(tag, 0) + 1
-    tag_frequencies = [
-        {"tag": tag, "count": tag_counts[tag]} for tag in sorted(tag_counts)
-    ]
-
-    # --- acted-trade block (entry+exit-marked) — STRUCTURALLY DISJOINT from confirmation stats --
-    # Realized-R comes from the ONE registered R path (marks_projection) over the persisted marks —
-    # never a second formula, never inline arithmetic here.
-    realized_rs: list[float] = []
-    acted_spread_per_r: list[float] = []
-    for t in theses:
-        actions = store.get_actions(t.id)
-        proj = marks_projection(t, actions)
-        realized_r = proj.get("realized_r")
-        if realized_r is None:
-            continue  # not an acted (entry+exit) trade — excluded from this population
-        realized_rs.append(round(realized_r, 4))
-        entry = proj.get("entry")
-        r_basis_value = proj.get("r_basis")
-        if entry is not None and entry.get("spread_at_mark") is not None and r_basis_value:
-            acted_spread_per_r.append(entry["spread_at_mark"] / r_basis_value)
-    acted_trade = {
-        "n": len(realized_rs),
-        "median_realized_r": _median_or_none(realized_rs),
-        "median_spread_per_r": _median_or_none(acted_spread_per_r),
-    }
-
-    return {
-        "setup_type": theses[0].setup_type,
-        "direction": theses[0].direction,
-        "n": n,
-        "abandonment": abandonment,
-        "insufficient_sample": n < config.analytics_min_sample_size,
-        "confirmation_excursions": confirmation_excursions,
-        "median_time_to_confirm": median_time_to_confirm,
-        "tag_frequencies": tag_frequencies,
-        "acted_trade": acted_trade,
-    }
-
-
-def compute_analytics(store: JournalStore, config: Config) -> dict:
-    """The full ``GET /research/analytics`` projection (capability 31, J-59) — read-only over persisted rows.
-
-    Reads every persisted thesis (``store.list_theses()`` with no filter / no limit), buckets them into
-    (``data_feed``, ``config_fingerprint``) partitions and, within each, per ``setup_type`` ×
-    ``direction`` groups, and aggregates each group via :func:`_aggregate_group`. NEVER pools across
-    feeds or fingerprints; emits NO "all"/overall rollup. Partitions and groups are emitted in a stable
-    sorted order so two identical calls are byte-equal (the J-59 determinism clause). An empty journal
-    yields ``{"partitions": [], "min_sample_size": ...}`` — an honest empty payload, not an error and
-    not a fabricated group.
-    """
-    all_theses = store.list_theses()  # no filter, no limit => every persisted thesis row, verbatim
-
-    # Partition key = (data_feed, config_fingerprint); group key (within) = (setup_type, direction).
-    partitions: dict[tuple[str, str], dict[tuple[str, str], list[ThesisRecord]]] = {}
-    for t in all_theses:
-        pkey = (t.data_feed, t.config_fingerprint)
-        gkey = (t.setup_type, t.direction)
-        partitions.setdefault(pkey, {}).setdefault(gkey, []).append(t)
-
-    partition_payloads: list[dict] = []
-    for (data_feed, fingerprint) in sorted(partitions):
-        groups = partitions[(data_feed, fingerprint)]
-        group_payloads = [
-            _aggregate_group(groups[gkey], store=store, config=config)
-            for gkey in sorted(groups)
-        ]
-        partition_payloads.append(
-            {
-                "data_feed": data_feed,
-                "config_fingerprint": fingerprint,
-                # A short form for compact display; the FULL value is always present above so two
-                # records are never silently compared across fingerprints.
-                "config_fingerprint_short": fingerprint[:8],
-                "groups": group_payloads,
-            }
-        )
-
-    return {
-        "partitions": partition_payloads,
-        # The serving-only min-sample threshold echoed so the frontend labels the gate honestly (it is
-        # excluded from config_fingerprint — a display choice never fragments the pools).
-        "min_sample_size": config.analytics_min_sample_size,
-    }
diff --git a/apps/backend/app/research/backtests.py b/apps/backend/app/research/backtests.py
index 114f395..8cd8c6e 100644
--- a/apps/backend/app/research/backtests.py
+++ b/apps/backend/app/research/backtests.py
@@ -23,29 +23,33 @@ report payload, and sent nowhere (the no-live-execution anti-goal; enforced repo
 
 The disciplines, clause by clause:
 
-  * **Entries reuse the studies' state-native arming — no new indicator, no new threshold.** Each
-    strategy setup x direction combo arms when its premise tape state (via the studies' ONE
-    ``_premise_state`` mapping) has held CONTINUOUSLY for ``study_arm_sustain_seconds``, gated by
+  * **Entries reuse the former studies module's state-native arming — no new indicator, no new
+    threshold.** Each strategy setup x direction combo arms when its premise tape state (via the
+    ONE ``_premise_state`` mapping, this module's own private helper since era-5D J-01 relocated
+    it here) has held CONTINUOUSLY for ``study_arm_sustain_seconds``, gated by
     ``study_arm_cooldown_seconds`` per combo — the exact sustained-premise + cooldown rules and
-    constants the study runner proved. ONE OPEN TRADE AT A TIME: while a simulated position is
-    open no new entry arms; eligibility is re-checked every recorded event, exits are processed
-    BEFORE arming at each event, and concurrent eligibility resolves in the strategy's declared
-    setup order — all deterministic, all documented in the config-owned definition.
+    constants the (now-demolished) study runner proved. ONE OPEN TRADE AT A TIME: while a
+    simulated position is open no new entry arms; eligibility is re-checked every recorded event,
+    exits are processed BEFORE arming at each event, and concurrent eligibility resolves in the
+    strategy's declared setup order — all deterministic, all documented in the config-owned
+    definition.
 
   * **Exits: R-stop / reward-target / horizon / state-flip / dataset_end.** The R-stop is the
-    studies' arm-instant synthetic invalidation (the REUSED ``_synthetic_invalidation`` helper —
-    ``study_occurrence_r_spread_multiple`` x arm spread, floored at ``study_occurrence_r_floor``,
-    adverse side), with R via the shared ``marks.r_basis`` (row 27 — never a second formula); it
-    triggers on a recorded print at/through the invalidation. ``structure_tape`` AND
-    ``structure_tape_map`` trades (era-4 J-05 / era-5B J-04, gated on the arming ``level``/class
-    being present, never on the strategy id) instead use a class-scaled, LEVEL-relative
-    invalidation (``_class_scaled_invalidation``) and additionally carry a reward-target exit
+    arm-instant synthetic invalidation (the ``_synthetic_invalidation`` helper, relocated here
+    alongside the rest of the state-native arming family — ``study_occurrence_r_spread_multiple``
+    x arm spread, floored at ``study_occurrence_r_floor``, adverse side), with R via the shared
+    ``r_basis`` helper (row 27 — never a second formula; also relocated here, era-5D J-01, this
+    module's own private helper since the journal-era ``marks.py`` was demolished); it triggers on
+    a recorded print at/through the invalidation. ``structure_tape`` AND ``structure_tape_map``
+    trades (era-4 J-05 / era-5B J-04, gated on the arming ``level``/class being present, never on
+    the strategy id) instead use a class-scaled, LEVEL-relative invalidation
+    (``_class_scaled_invalidation``) and additionally carry a reward-target exit
     (``_class_scaled_target`` — a class R-multiple bounded by the next opposing level/band resolved
     at arm time); v1/null trades never carry a ``target_price`` and so can never reach that exit.
-    The state-flip exit fires when the tape reads the OPPOSING control state (the
-    studies' ``_control_state`` vocabulary). The time horizon exits at the first recorded event
-    at/after ``strategy_exit_horizon_seconds`` past entry. A trade still open when the stream ends
-    is handled EXPLICITLY and deterministically: forced exit at the LAST recorded price, labeled
+    The state-flip exit fires when the tape reads the OPPOSING control state (the ``_control_state``
+    vocabulary, also relocated here). The time horizon exits at the first recorded event at/after
+    ``strategy_exit_horizon_seconds`` past entry. A trade still open when the stream ends is
+    handled EXPLICITLY and deterministically: forced exit at the LAST recorded price, labeled
     ``dataset_end`` — documented, never silent. Exit precedence within one event is fixed and
     documented: r_stop, then reward_target, then state_flip, then horizon. Exit evaluation begins
     strictly AFTER the entry event.
@@ -94,33 +98,15 @@ import random
 import threading
 import time
 import uuid
+from dataclasses import dataclass
 
 from ..config import Config, PROFILE_DEFAULT, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID
 from .bars import BarStore
 from .datasets import DatasetIntegrityError, DatasetNotFound, DatasetStore
 from .levels import compute_levels, level_change_points, CLASS_A, CLASS_B, CLASS_C
-from .marks import r_basis
 from .store import BacktestRecord, JournalStore
 from .tradability import RESISTANCE, SUPPORT, basis_day_key, compute_tradability
 
-# The status vocabulary and the state-native helpers are REUSED from the studies module (one
-# owner per literal / per mapping — never a second copy): the premise-state arming map, the
-# control-state vocabulary the state-flip exit reads, the arm-instant synthetic invalidation,
-# the recorded-path point shape, and the throttled progress cadence.
-from .studies import (
-    STATUS_CANCELLED,
-    STATUS_DONE,
-    STATUS_FAILED,
-    STATUS_QUEUED,
-    STATUS_RUNNING,
-    TERMINAL_STATUSES,
-    _control_state,
-    _premise_state,
-    _synthetic_invalidation,
-    _PathPoint,
-    _PROGRESS_EVERY,
-)
-
 __all__ = [
     "BacktestJobManager",
     "BacktestRunner",
@@ -138,6 +124,7 @@ __all__ = [
     "STATUS_QUEUED",
     "STATUS_RUNNING",
     "TERMINAL_STATUSES",
+    "r_basis",
 ]
 
 # The visible honesty register carried by EVERY report payload (the PnL-honesty constraint):
@@ -158,10 +145,91 @@ EXIT_STATE_FLIP = "state_flip"
 EXIT_DATASET_END = "dataset_end"
 
 
+# === Relocated from the (demolished) journal-era ``marks.py`` / ``studies.py`` modules ==============
+# era-5D J-01 ("The Clean Slate" demolition interlude): this module was the only surviving runtime
+# consumer of the symbols below outside the two source modules' own internals — see
+# ``docs/goal.md``'s I-2 RELOCATE table (``r_basis``) and this iteration's dev handoff (the
+# additional STATUS_*/state-native-arming family the plan's own inventory review surfaced). Every
+# definition is copied VERBATIM (same math, same behaviour, no renamed semantics) — a pure move, not
+# a rewrite. ``marks.py`` and ``studies.py`` are deleted whole later in this same iteration.
+
+def r_basis(reference_price: float, invalidation_price: float) -> float:
+    """The ONE shared R basis: ``R = |reference - invalidation|`` (the goal-doc glossary's R unit).
+
+    The SINGLE owner of the R definition — this runner's realized/gross-R math is the sole
+    remaining consumer since the journal-era marks/excursions machinery was demolished (era-5D
+    J-01). A degenerate ``R == 0`` (reference exactly at the invalidation) is returned as-is so
+    the caller decides the honest no-metric behaviour (no divide-by-zero, no fabricated
+    infinity)."""
+    return abs(reference_price - invalidation_price)
+
+
+# The study-job status vocabulary (queued -> running -> done | cancelled | failed) — this runner's
+# OWN job lifecycle mirrors it byte-identically (one owner per literal, never a second copy); the
+# former studies.py replay engine that originated this vocabulary is gone, this is now its sole
+# owner.
+STATUS_QUEUED = "queued"
+STATUS_RUNNING = "running"
+STATUS_DONE = "done"
+STATUS_CANCELLED = "cancelled"
+STATUS_FAILED = "failed"
+TERMINAL_STATUSES = frozenset({STATUS_DONE, STATUS_CANCELLED, STATUS_FAILED})
+
+# How often (in processed events) a running backtest refreshes its persisted progress — throttled
+# so the progress write is never a hot path (a replay processes thousands of events; a write every
+# event would hammer the writer queue). A whole-number internal cadence, not a tuned research value.
+_PROGRESS_EVERY = 250
+
+
+@dataclass
+class _PathPoint:
+    """One recorded snapshot-path point (logical ts + last + spread + the canonical tape state).
+    Tape data lives ONLY here in memory during the run — never persisted (the persistence-scope
+    anti-goal)."""
+
+    timestamp: float
+    last: float | None
+    spread: float | None
+    tape_state: str
+
+
+def _control_state(direction: str) -> str:
+    return "buyer_control" if direction == "long" else "seller_control"
+
+
+def _absorption_state(direction: str) -> str:
+    # absorption_reversal premise: long expects sellers absorbed at the bid (bid_absorption);
+    # short expects buyers absorbed at the ask (ask_absorption).
+    return "bid_absorption" if direction == "long" else "ask_absorption"
+
+
+def _premise_state(setup_type: str, direction: str) -> str:
+    """The EXISTING engine tape state whose SUSTAINED presence arms a state-native entry.
+
+    absorption_reversal arms on sustained matching ABSORPTION (the premise). trend_continuation
+    arms on sustained matching CONTROL. Composed ONLY of existing states (no new indicator)."""
+    if setup_type == "absorption_reversal":
+        return _absorption_state(direction)
+    return _control_state(direction)  # trend_continuation
+
+
+def _synthetic_invalidation(arm_price: float, spread: float | None, direction: str, config: Config) -> float:
+    """The deterministic arm-instant synthetic invalidation (the named design decision).
+
+    A synthetic invalidation placed ``study_occurrence_r_spread_multiple × spread`` (floored at
+    ``study_occurrence_r_floor``) on the ADVERSE side of the arm price (below for a long, above for
+    a short). Derived ONLY from existing engine values at the arm instant (arm price + arm-instant
+    spread); NEVER fitted. R is then ``|arm_price − this|`` via the shared ``r_basis`` helper
+    above."""
+    s = spread if spread is not None and spread > 0 else 0.0
+    band = max(s * config.study_occurrence_r_spread_multiple, config.study_occurrence_r_floor)
+    return arm_price - band if direction == "long" else arm_price + band
+
+
 def _opposing_control_state(direction: str) -> str:
     """The OPPOSING control state whose read is the state-flip exit (existing vocabulary only):
-    a long is broken by ``seller_control``, a short by ``buyer_control`` — via the studies' one
-    ``_control_state`` mapping, never a second copy of the state names."""
+    a long is broken by ``seller_control``, a short by ``buyer_control`` — via the ``_control_state``
+    mapping above, never a second copy of the state names."""
     return _control_state("short" if direction == "long" else "long")
 
 
diff --git a/apps/backend/app/research/datasets.py b/apps/backend/app/research/datasets.py
index 35d5f7d..a38b3dc 100644
--- a/apps/backend/app/research/datasets.py
+++ b/apps/backend/app/research/datasets.py
@@ -11,9 +11,9 @@ directory (``TAPEOLOGY_DATASET_DIR`` override, ``config.dataset_dir`` default 
 Disciplines (each an anti-goal or a J-02 acceptance clause):
 
   * **Explicit recording only.** Recording is a research ACTION through ``record_from_source``
-    (the same source resolution studies use: the committed keyless reference window, or an
-    arbitrary window through the EXISTING adapter fetch seam). Nothing in the watch/stream path
-    imports this module — the live cockpit's tape is never persisted (no ambient recording).
+    (the committed keyless reference window, or an arbitrary window through the EXISTING adapter
+    fetch seam). Nothing in the watch/stream path imports this module — the live cockpit's tape is
+    never persisted (no ambient recording).
   * **Checksummed + re-verified on every content change (stat-keyed) for ``get``/``list`` — every
     load, forever, for ``load_events``/``replay``.** ``meta.checksum`` is a sha256 over the tape
     CONTENT (symbol + feed + anchor + events) computed at registration; a second whole-record
@@ -33,9 +33,9 @@ Disciplines (each an anti-goal or a J-02 acceptance clause):
     under a different split (the re-tag attempt) — or the same split — raises the 409-style
     ``DatasetAlreadyRegistered`` naming the existing dataset and its frozen tag.
   * **Byte-identical replay.** ``DatasetStore.replay`` replays a stored dataset UNPACED through
-    a FRESH ``TapeEngine`` (the studies-runner pattern), yielding snapshots byte-identical to
-    replaying the original source stream, deterministic across re-runs. Consumed by tests now
-    and by J-03's backtester next — there is no REST replay endpoint (Product Shape lists none).
+    a FRESH ``TapeEngine``, yielding snapshots byte-identical to replaying the original source
+    stream, deterministic across re-runs. Consumed by tests and by the backtester — there is no
+    REST replay endpoint (Product Shape lists none).
   * **Honest failure states.** Unknown id -> ``DatasetNotFound``; an empty requested window ->
     ``EmptyWindowError`` (nothing written); an unavailable reference fixture ->
     ``DatasetRecordError``. Every error is distinct and explicit.
@@ -61,19 +61,26 @@ from ..providers.historical import HistoricalProvider
 from .dataset_index import DatasetIndex
 from .feed_basis import data_feed_for_scenario
 
-# The dataset source vocabulary REUSES the studies module's source-resolution names (one owner
-# per literal — never a second copy), and the reference loader below reuses its one committed
-# fixture loader. Datasets are HISTORICAL tape: the committed keyless reference window, or an
-# arbitrary real window through the EXISTING adapter fetch seam. A seeded sim stream reproduces
-# on demand, so ``sim`` is deliberately NOT a dataset source kind.
-from .studies import SOURCE_HISTORICAL, SOURCE_REFERENCE
-from .studies import _load_reference_window as _load_reference
-
 # The frozen split vocabulary (assigned at registration, immutable forever after).
 SPLIT_TRAIN = "train"
 SPLIT_HOLDOUT = "holdout"
 VALID_SPLITS = frozenset({SPLIT_TRAIN, SPLIT_HOLDOUT})
 
+# === Relocated from the (demolished) journal-era ``studies.py`` module ==============================
+# era-5D J-01 ("The Clean Slate" demolition interlude, I-2 RELOCATE table): this module is now the
+# SOLE owner of the dataset source-kind vocabulary and the committed reference-window loader — a
+# pure move (same values, same behaviour), landed before ``studies.py`` is deleted whole later in
+# this same iteration. Datasets are HISTORICAL tape: the committed keyless reference window, or an
+# arbitrary real window through the EXISTING adapter fetch seam. A seeded sim stream reproduces on
+# demand, so ``sim`` is deliberately NOT a dataset source kind (kept in the former studies.py only,
+# for its own sim-replay path).
+SOURCE_REFERENCE = "reference"
+SOURCE_HISTORICAL = "historical"
+
+# The committed reference window — the PG SIP fixture. Loadable without credentials. The id the
+# (now-removed) study create form's quick-pick used to send; datasets.py's own callers still use it.
+REFERENCE_SOURCE_ID = "PG_SIP_REFERENCE"
+
 VALID_SOURCE_KINDS = frozenset({SOURCE_REFERENCE, SOURCE_HISTORICAL})
 
 # Stored event-row type tags (one explicit copy each).
@@ -367,8 +374,8 @@ class DatasetStore:
         return [_row_to_event(symbol, row) for row in loaded.rows]
 
     def replay(self, dataset_id: str, config: Config) -> Iterator[EngineSnapshot]:
-        """Replay the stored dataset UNPACED through a FRESH ``TapeEngine`` (the studies-runner
-        pattern), yielding every per-event snapshot. Deterministic: the stored stream, the stored
+        """Replay the stored dataset UNPACED through a FRESH ``TapeEngine``, yielding every
+        per-event snapshot. Deterministic: the stored stream, the stored
         source descriptor, and the stored epoch anchor fully determine the output — re-runs are
         byte-identical, and both match replaying the original source stream."""
         loaded = self._load_by_id(dataset_id)
@@ -440,6 +447,34 @@ class DatasetStore:
 # --- source resolution + record (the explicit research action) ------------------------------------
 
 
+def _load_reference_window():
+    """Load the committed PG SIP reference fixture without credentials. Relocated verbatim from
+    the (demolished) journal-era ``studies.py`` module (era-5D J-01, I-2 RELOCATE table) — same
+    fixture path, same behaviour. Returns the ``HistoricalWindow`` or ``None`` if absent (the
+    caller raises its own explicit error — never a synthetic stand-in)."""
+    import json
+    from pathlib import Path
+
+    from ..providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
+
+    fixture = (
+        Path(__file__).resolve().parents[2]
+        / "tests"
+        / "fixtures"
+        / "alpaca"
+        / "PG_20260609_170000_171000_sip.json"
+    )
+    if not fixture.exists():
+        return None
+    data = json.loads(fixture.read_text())
+    trades = tuple(RawTrade(t["epoch"], t["price"], t["size"]) for t in data["trades"])
+    quotes = tuple(
+        RawQuote(q["epoch"], q["bid"], q["ask"], q["bid_size"], q["ask_size"])
+        for q in data["quotes"]
+    )
+    return HistoricalWindow(data["symbol"], trades, quotes)
+
+
 def _slice_window(window: HistoricalWindow, start_epoch: float | None, end_epoch: float | None) -> HistoricalWindow:
     """The half-open ``[start, end)`` epoch slice of a source window — pure selection of REAL
     records (nothing fabricated, dropped beyond the bounds, or reordered)."""
@@ -473,14 +508,14 @@ def record_from_source(
 ) -> dict:
     """Record + register ONE dataset from a historical source (the explicit research action).
 
-    Source resolution mirrors the studies runner: ``reference`` loads the committed keyless PG
-    SIP fixture (optionally sliced to ``[start, end)``); ``historical`` calls the injected
-    ``historical_fetch`` built on the EXISTING neutral adapter seam (credentials / no-data /
-    timeouts surface that seam's explicit errors — never fabricated, never fixture-substituted).
-    The stream is materialised through the SAME ``HistoricalProvider`` the watch and studies
-    paths replay, so the stored events ARE the source stream, byte for byte."""
+    ``reference`` loads the committed keyless PG SIP fixture (optionally sliced to
+    ``[start, end)``); ``historical`` calls the injected ``historical_fetch`` built on the
+    EXISTING neutral adapter seam (credentials / no-data / timeouts surface that seam's explicit
+    errors — never fabricated, never fixture-substituted). The stream is materialised through the
+    SAME ``HistoricalProvider`` the watch path replays, so the stored events ARE the source
+    stream, byte for byte."""
     if source_kind == SOURCE_REFERENCE:
-        window = _load_reference()
+        window = _load_reference_window()
         if window is None or (not window.trades and not window.quotes):
             raise DatasetRecordError("the committed reference window is unavailable")
     elif source_kind == SOURCE_HISTORICAL:
@@ -517,9 +552,8 @@ def record_from_source(
 
 
 def parse_utc_epoch(value: str) -> float:
-    """ISO-8601 (``Z`` accepted) -> UTC epoch seconds; a naive value is taken as UTC (the studies
-    window-parse convention). Raises ``ValueError`` for a malformed value (the route maps it to
-    an explicit 422)."""
+    """ISO-8601 (``Z`` accepted) -> UTC epoch seconds; a naive value is taken as UTC. Raises
+    ``ValueError`` for a malformed value (the route maps it to an explicit 422)."""
     parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
     if parsed.tzinfo is None:
         parsed = parsed.replace(tzinfo=timezone.utc)
diff --git a/apps/backend/app/research/edge_report.py b/apps/backend/app/research/edge_report.py
index 087a13d..65bec17 100644
--- a/apps/backend/app/research/edge_report.py
+++ b/apps/backend/app/research/edge_report.py
@@ -69,11 +69,11 @@ from ..config import (
     STRATEGY_V1_ID,
 )
 from .bars import BarStore
-# ``_aggregate`` is imported PRIVATE (the ``datasets.py`` -> ``from .studies import
-# _load_reference_window as _load_reference`` precedent): the ONE trade-population aggregator
-# every other report in this codebase already computes with (n/gross/net R and $/win_rate/
-# max_drawdown_r) -- reused VERBATIM for a strategy-comparison cell's pooled trade list, never a
-# second R/$/edge formula.
+# ``_aggregate`` is imported PRIVATE (the ``backtests.py``-owned-private-helper precedent —
+# ``r_basis``/the state-native arming family relocated there whole, era-5D J-01): the ONE
+# trade-population aggregator every other report in this codebase already computes with
+# (n/gross/net R and $/win_rate/max_drawdown_r) -- reused VERBATIM for a strategy-comparison
+# cell's pooled trade list, never a second R/$/edge formula.
 from .backtests import BacktestJobManager, REGISTER, STATUS_DONE, _aggregate
 from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, parse_utc_epoch
 # era-fast_wall J-05: ``pair_cache_key``/``EdgeReportBacktestCache`` for the per-pair sub-cache;
diff --git a/apps/backend/app/research/excursions.py b/apps/backend/app/research/excursions.py
deleted file mode 100644
index 17e5422..0000000
--- a/apps/backend/app/research/excursions.py
+++ /dev/null
@@ -1,362 +0,0 @@
-"""Excursion outcomes (capability 30, J-58) — the SINGLE-owner in-memory tracker + persist seam.
-
-This is the ONE place per-horizon excursion outcomes are measured. Excursions are the first surface
-of the EVIDENCE layer: after a thesis runs its course the journal detail shows — per configured
-horizon — how far the tape actually went FOR and AGAINST the idea in **R units**, separately from the
-moment the tape CONFIRMED it and from the moment the user actually ENTERED. Two populations, never
-pooled.
-
-Discipline (the binding lessons + anti-goals this rides):
-  * **Read-only over the engine.** The tracker is fed ONLY by the research-monitor observer's
-    ``on_event`` snapshots — it never mutates engine/feature/classifier state. Engine outputs stay
-    byte-identical with or without it (equivalence anti-goal).
-  * **R basis reuses ONE helper.** ``R = |reference - invalidation|`` via the SAME ``r_basis`` helper
-    row 27 (``marks.r_basis``) uses — never a second formula.
-  * **Reference prices come from already-persisted facts.** The confirmation anchor's reference price
-    is the ``last`` recorded on the FIRST published ``confirming`` timeline event (already on the
-    append-only timeline). The entry anchor's reference price is the verbatim entry-mark price.
-  * **Spread-at-anchor is a MOMENT value, stamped ONCE at arming** (mirroring row 18's
-    ``spread_at_mark``) — never recomputed at read. The entry population REUSES row 18's already
-    stamped ``spread_at_mark`` (never re-stamped); the confirmation population captures the snapshot
-    spread once at the arming instant.
-  * **First-touch ternary in LOGICAL time.** Each horizon resolves to ``+1R_first | -1R_first |
-    neither_within_horizon`` by which R multiple (``excursion_target_r``) the price touches FIRST,
-    measured in logical seconds past the anchor. Running MFE/MAE in R are tracked per population.
-  * **Truncation, never extrapolation.** An open horizon is TRUNCATED at stream end or at a gap
-    event (``paused`` teardown / ``watch_restarted`` / a stale span) — flagged ``truncated``, never
-    bridged across a gap, never extrapolated past the data.
-  * **Two populations fully segregated end to end** — separate anchors, separate R bases, separate
-    per-horizon rows; nothing pooled or averaged across them.
-  * **Persist ONCE at the defining moment, never recomputed at read.** ``compute_and_persist_excursions``
-    snapshots the tracker's resolved state and persists it on the thesis row (schema v7) through the
-    single writer queue. Once persisted, values are frozen. Where no tracker is available at the
-    persist moment (the restart-expiry sweep after a backend restart — the watch that declared the
-    thesis is long gone), an explicit honest ``not_tracked`` record is persisted — never fabricated
-    numbers, never a dishonest zero.
-"""
-
-from __future__ import annotations
-
-from dataclasses import dataclass, field
-
-from ..config import Config
-from ..engine.snapshot import EngineSnapshot
-from .marks import r_basis as _r_basis
-from .store import JournalStore
-
-# The two population ids — segregated end to end, never pooled.
-CONFIRMATION = "confirmation"
-ENTRY = "entry"
-
-# The ternary per-horizon outcome enum (by first touch, in logical time). LABELS only — never a
-# numeric score. ``not_resolved`` is NOT one of these: an open horizon reads ``neither_within_horizon``
-# only once the horizon has fully elapsed; before that it is reported as ``truncated`` if the stream
-# ended inside it.
-TERNARY_PLUS = "+1R_first"
-TERNARY_MINUS = "-1R_first"
-TERNARY_NEITHER = "neither_within_horizon"
-
-
-@dataclass
-class _Population:
-    """One armed excursion population (confirmation OR entry) — its anchor + per-horizon running state.
-
-    Mutable while live (the tracker advances it each event); SNAPSHOTTED to a frozen dict at the
-    persist moment. ``reference_price`` and ``invalidation_price`` give the R basis (computed via the
-    ONE shared ``marks.r_basis`` helper); ``r`` is cached once at arming (the basis never changes).
-    ``spread_at_anchor`` is the moment spread stamped ONCE at arming. Each horizon tracks running
-    MFE/MAE (in R) and a resolved ternary outcome + a per-horizon ``done`` / ``truncated`` flag.
-    """
-
-    population: str
-    anchor_logical_ts: float
-    anchor_wall_ts: float
-    reference_price: float
-    invalidation_price: float
-    spread_at_anchor: float | None
-    r: float
-    # Per horizon (keyed by the horizon's float seconds): the running excursion state.
-    horizons: dict[float, "_HorizonState"] = field(default_factory=dict)
-
-
-@dataclass
-class _HorizonState:
-    horizon: float
-    mfe_r: float = 0.0          # max favorable excursion in R (>= 0; favorable = the thesis direction)
-    mae_r: float = 0.0          # max adverse excursion in R (<= 0)
-    # The ternary outcome LATCHED at FIRST TOUCH (the R target reached first). Distinct from
-    # ``done``: the ternary is decided once and never changes, but the horizon keeps tracking running
-    # MFE/MAE over the WHOLE window (goal.md capability 30 — MFE/MAE are measured over the horizon,
-    # the ternary is a separate first-touch determination).
-    outcome: str | None = None
-    done: bool = False          # the horizon fully elapsed (MFE/MAE final) — no longer updated
-    truncated: bool = False     # the stream/gap cut this horizon short before it fully elapsed
-
-
-class ExcursionTracker:
-    """Tracks running excursions for one thesis across the two populations (capability 30, J-58).
-
-    Fed ONLY by the research-monitor observer: ``on_event(snapshot)`` advances every armed population,
-    ``arm_confirmation`` / ``arm_entry`` arm a population ONCE at its defining moment, and
-    ``truncate_open`` marks every still-open horizon ``truncated`` at a stream end / gap event. The
-    tracker is read-only over the engine — it only reads the handed snapshot.
-
-    Determinism: the tracker reads ONLY the snapshot's logical timestamp + last (and, once, the
-    arming spread), so the SAME ordered stream + the SAME arming sequence yields a byte-identical
-    persisted record (J-58's determinism clause).
-    """
-
-    def __init__(self, *, invalidation_price: float, direction: str, config: Config) -> None:
-        self._invalidation = invalidation_price
-        self._direction = direction
-        self._config = config
-        self._populations: dict[str, _Population] = {}
-
-    # --- arming (called at the defining moments, NOT every event) -------------------------------
-    def arm_confirmation(
-        self, snapshot: EngineSnapshot, reference_price: float, *, wall_ts: float | None = None
-    ) -> None:
-        """Arm the confirmation population ONCE at the first published ``confirming`` event.
-
-        ``reference_price`` is the ``last`` recorded on that published timeline event (the basis the
-        spec mandates). ``wall_ts`` is the true clock instant the monitor stamped on that published
-        event (passed in so the anchor's true-clock display matches the timeline row verbatim); when
-        omitted (the pure unit path) it defaults to ``0.0`` — an honest sentinel, the UI renders the
-        logical anchor regardless. The spread-at-anchor is captured ONCE here from the snapshot (a
-        moment value, like row 18's ``spread_at_mark``). Re-confirmation after weakening never re-arms
-        (idempotent guard) — the FIRST confirmation owns the population."""
-        if CONFIRMATION in self._populations:
-            return
-        if reference_price is None:
-            return
-        self._populations[CONFIRMATION] = self._make_population(
-            CONFIRMATION,
-            anchor_logical_ts=snapshot.timestamp,
-            anchor_wall_ts=wall_ts if wall_ts is not None else 0.0,
-            reference_price=reference_price,
-            spread_at_anchor=snapshot.spread,
-        )
-
-    def arm_entry(
-        self,
-        *,
-        logical_ts: float,
-        wall_ts: float,
-        reference_price: float,
-        spread_at_mark: float | None,
-    ) -> None:
-        """Arm the entry population ONCE at the recorded entry mark.
-
-        ``reference_price`` is the verbatim mark price; ``spread_at_mark`` is the moment spread ALREADY
-        stamped by row 18 on the action record (REUSED here, never re-stamped). Idempotent — a second
-        entry can never exist (the API enforces one entry), but the guard keeps the FIRST arming."""
-        if ENTRY in self._populations:
-            return
-        self._populations[ENTRY] = self._make_population(
-            ENTRY,
-            anchor_logical_ts=logical_ts,
-            anchor_wall_ts=wall_ts,
-            reference_price=reference_price,
-            spread_at_anchor=spread_at_mark,
-        )
-
-    def _make_population(
-        self,
-        population: str,
-        *,
-        anchor_logical_ts: float,
-        anchor_wall_ts: float,
-        reference_price: float,
-        spread_at_anchor: float | None,
-    ) -> _Population:
-        # R basis via the ONE shared helper (row 27) — never a second formula.
-        r = _r_basis(reference_price, self._invalidation)
-        pop = _Population(
-            population=population,
-            anchor_logical_ts=anchor_logical_ts,
-            anchor_wall_ts=anchor_wall_ts,
-            reference_price=reference_price,
-            invalidation_price=self._invalidation,
-            spread_at_anchor=spread_at_anchor,
-            r=r,
-            horizons={
-                h: _HorizonState(horizon=h)
-                for h in self._config.excursion_horizons_seconds
-            },
-        )
-        return pop
-
-    @property
-    def is_armed(self) -> bool:
-        return bool(self._populations)
-
-    @property
-    def armed_populations(self) -> tuple[str, ...]:
-        return tuple(self._populations.keys())
-
-    # --- the hot path (read-only over the engine) ------------------------------------------------
-    def on_event(self, snapshot: EngineSnapshot) -> None:
-        """Advance every armed population against this snapshot (read-only).
-
-        For each population with at least one open horizon: compute the directional move in R from the
-        anchor's reference price, update running MFE/MAE, resolve the ternary by FIRST TOUCH (the R
-        target reached first wins), and mark a horizon ``done`` once the logical time past the anchor
-        exceeds it. A degenerate ``R == 0`` basis (reference exactly at the invalidation) yields no
-        measurable move — every horizon resolves ``neither_within_horizon`` honestly (never a
-        divide-by-zero, never a fabricated infinity)."""
-        last = snapshot.last
-        if last is None:
-            return
-        for pop in self._populations.values():
-            self._advance_population(pop, snapshot.timestamp, last)
-
-    def _advance_population(self, pop: _Population, logical_ts: float, last: float) -> None:
-        dt = logical_ts - pop.anchor_logical_ts
-        if dt < 0:
-            return  # a snapshot before the anchor never contributes (defensive)
-        # Directional move in R: favorable = the thesis direction (long => price up; short => down).
-        if pop.r > 0:
-            raw_move = last - pop.reference_price
-            directed = raw_move if self._direction == "long" else -raw_move
-            move_r = directed / pop.r
-        else:
-            move_r = 0.0  # degenerate basis — no measurable move (honest, never fabricated)
-        target = self._config.excursion_target_r
-        for hs in pop.horizons.values():
-            if hs.done:
-                continue
-            within = dt <= hs.horizon
-            if within:
-                # Running MFE/MAE in R over the WHOLE horizon window (favorable >= 0, adverse <= 0) —
-                # kept updating even after the ternary latches (MFE/MAE and the ternary are distinct
-                # measurements over the same window, per goal.md capability 30).
-                if move_r > hs.mfe_r:
-                    hs.mfe_r = move_r
-                if move_r < hs.mae_r:
-                    hs.mae_r = move_r
-                # First-touch ternary: whichever R target is reached FIRST within the horizon wins,
-                # latched ONCE (re-touch never changes it). The horizon stays OPEN for MFE/MAE.
-                if hs.outcome is None:
-                    if move_r >= target:
-                        hs.outcome = TERNARY_PLUS
-                    elif move_r <= -target:
-                        hs.outcome = TERNARY_MINUS
-            else:
-                # The logical time has passed the horizon: MFE/MAE are final. If no R target was ever
-                # touched within the window, the ternary resolves ``neither_within_horizon``. The
-                # horizon is fully elapsed (not truncated) — never updated again.
-                if hs.outcome is None:
-                    hs.outcome = TERNARY_NEITHER
-                hs.done = True
-
-    # --- truncation (stream end / gap event) -----------------------------------------------------
-    def truncate_open(self) -> None:
-        """Mark every still-open horizon (in every armed population) ``truncated`` (J-58).
-
-        Called at the defining truncation moment — a stream end, or a gap event (``paused`` teardown,
-        ``watch_restarted``, a stale span). A horizon is TRUNCATED iff its ternary outcome is still
-        UNDETERMINED (``outcome is None``) AND it has not fully elapsed: the window was cut short
-        before the question "did the tape reach +1R or -1R within H seconds?" could be answered, so it
-        is flagged ``truncated`` (its running MFE/MAE so far are kept as the honest partial excursion),
-        never bridged across the gap, never extrapolated. A horizon whose ternary ALREADY latched by
-        first touch (``+1R_first`` / ``-1R_first``) is NOT truncated — that answer is final regardless
-        of the cut (the target was definitively touched within the window); only its MFE/MAE stop
-        growing. A horizon already fully elapsed (``done``) is untouched."""
-        for pop in self._populations.values():
-            for hs in pop.horizons.values():
-                if hs.done:
-                    continue
-                if hs.outcome is None:
-                    hs.truncated = True
-                # In both cases the horizon stops updating at the cut (no extrapolation past the data).
-                hs.done = True
-
-    # --- snapshot to the persisted shape ---------------------------------------------------------
-    def to_record(self) -> dict:
-        """Freeze the tracker's resolved state into the persisted excursion record (schema v7).
-
-        Returns ``{"tracked": True, "populations": {confirmation?: {...}, entry?: {...}}}`` where each
-        present population carries its anchor (logical + wall ts, reference price, R basis,
-        spread-at-anchor) and per-horizon rows (horizon, mfe_r, mae_r, outcome, truncated). Only ARMED
-        populations appear — a never-confirmed thesis has NO confirmation key; a no-entry thesis has
-        NO entry key (honest omission, never a fabricated zero). Both populations are fully
-        segregated — independent anchors, independent R bases, independent rows."""
-        populations: dict[str, dict] = {}
-        for pop_id, pop in self._populations.items():
-            populations[pop_id] = {
-                "population": pop.population,
-                "anchor_logical_ts": pop.anchor_logical_ts,
-                "anchor_wall_ts": pop.anchor_wall_ts,
-                "reference_price": pop.reference_price,
-                "invalidation_price": pop.invalidation_price,
-                "r_basis": pop.r,
-                "spread_at_anchor": pop.spread_at_anchor,
-                "horizons": [
-                    {
-                        "horizon": hs.horizon,
-                        "mfe_r": _round_r(hs.mfe_r),
-                        "mae_r": _round_r(hs.mae_r),
-                        # An open-but-not-truncated horizon (e.g. a persist mid-stream that never
-                        # truncated) reads ``neither_within_horizon`` only once fully elapsed; while
-                        # genuinely open it is ``None`` and the ``truncated`` flag tells the story.
-                        "outcome": hs.outcome,
-                        "truncated": hs.truncated,
-                    }
-                    for hs in pop.horizons.values()
-                ],
-            }
-        return {"tracked": True, "populations": populations}
-
-
-def _round_r(value: float) -> float:
-    """Round an R figure to 4 dp so the persisted/served numbers are byte-stable across runs.
-
-    The deterministic seeded re-run must reproduce IDENTICAL numbers (J-58's determinism clause);
-    rounding kills any last-ULP float drift while keeping R to a precision finer than the 2-dp display
-    the UI renders."""
-    return round(value, 4)
-
-
-# --- the not-tracked honest marker (restart-expiry sweep, no tracker available) -------------------
-
-def not_tracked_record() -> dict:
-    """The explicit honest record persisted where no tracker state exists at the persist moment.
-
-    The restart-expiry sweep resolves a thesis whose declaring watch is long gone (a backend restart):
-    there is no in-memory price path to measure excursions from, and tape data is NEVER persisted, so
-    the excursions CANNOT be reconstructed. Rather than fabricate numbers or a dishonest zero, persist
-    ``{"tracked": False}`` — the journal detail then renders an explicit not-tracked notice."""
-    return {"tracked": False, "populations": {}}
-
-
-# --- the persist seam (mirrors execution_checks / grades / final-statuses) -----------------------
-
-def compute_and_persist_excursions(
-    store: JournalStore,
-    thesis_id: str,
-    tracker: "ExcursionTracker | None",
-) -> dict | None:
-    """Persist the excursion record for a thesis ONCE at its defining moment (capability 30, J-58).
-
-    Called by every terminal-resolution path (user resolve, system invalidation, stream-end / stop
-    expiry, restart-expiry sweep) AND at the stream-end SURVIVAL path for an entry-marked thesis that
-    survives active-but-not-evaluated (J-58's script ends exactly there — the record must exist
-    without a resolution). Follows the proven persist-once seam: it snapshots the live ``tracker``'s
-    resolved state (the price path is in memory, NEVER persisted — tape data stays unpersisted) and
-    writes it on the thesis row via ``store.set_excursions`` through the single writer queue. Once
-    persisted, the values are frozen — never recomputed at read, never reopened on a matching-source
-    re-attach.
-
-    ``tracker`` is ``None`` ONLY where no tracker exists at the persist moment (the restart-expiry
-    sweep after a backend restart): an explicit ``not_tracked`` record is then persisted (honest
-    absence over fabricated numbers). Idempotent guard: if the thesis already carries an excursion
-    record (a double-resolve race), it is NOT recomputed — the first record stands (append-only
-    spirit). Returns the persisted record (or ``None`` if the thesis is gone)."""
-    thesis = store.get_thesis(thesis_id)
-    if thesis is None:
-        return None
-    if thesis.excursions is not None:
-        return thesis.excursions
-    record = tracker.to_record() if tracker is not None else not_tracked_record()
-    store.set_excursions(thesis_id, record)
-    return record
diff --git a/apps/backend/app/research/execution_checks.py b/apps/backend/app/research/execution_checks.py
deleted file mode 100644
index 01faaab..0000000
--- a/apps/backend/app/research/execution_checks.py
+++ /dev/null
@@ -1,316 +0,0 @@
-"""Machine-derived execution checks (capability 27, J-54) — the SINGLE-owner pure function.
-
-This is the ONE place the four named execution checks are computed. Every terminal-resolution code
-path (the user ``POST /research/thesis/{id}/resolve``, the system invalidation auto-resolve, the
-stream-end / stop expiry, and the restart-expiry sweep) calls THIS function exactly ONCE at the
-defining moment and persists the result on the thesis row (schema v5). The journal-detail endpoint
-serves the persisted result VERBATIM — nothing is recomputed at read (single-source-of-truth + the
-data-contract row-19 execution-checks half).
-
-The four checks (capability 27 / goal.md), computed from the recorded action marks + the append-only
-verdict timeline + the FROZEN thesis fields ONLY (no engine, no live snapshot — deterministic):
-
-  * ``entered_before_confirmation`` — the entry mark's logical_ts precedes the FIRST published
-    ``confirming`` event (or no ``confirming`` was ever published while entry-marked).
-  * ``chased_entry`` — the entry price is beyond the recorded ``rule_first_true_price`` + the
-    config-owned chase return threshold, direction-aware. The chase check anchors at the recorded
-    ``rule_first_true`` price (the first logical instant the raw confirming rule held), NEVER the
-    post-dwell publish price (per the Constraints) — reusing the existing ``chase_return_threshold``
-    config seam (no new magic number).
-  * ``exited_beyond_invalidation`` — the exit mark is recorded beyond the declared invalidation in
-    the adverse direction (the user held through the stop).
-  * ``cut_confirming_early`` — the exit was recorded while the latest published verdict was
-    ``confirming`` (before any weakening / rejecting / invalidation).
-
-Each check yields an ENUM status — ``failed | passed | not_applicable`` (labels, NEVER a numeric
-score) — plus plain-language evidence quoting the measured values (timestamps, prices, thresholds).
-With no marks the mark-dependent checks read an explicit ``not_applicable`` (never a fabricated
-pass/fail). The backend-owned check → suggested-mistake-tag mapping (taxonomy ``CHECK_SUGGESTED_TAG``)
-derives the suggested tags for the FAILED checks — the system SUGGESTS only; it never records a
-confirmed tag.
-"""
-
-from __future__ import annotations
-
-from ..config import Config
-from .store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord
-from .taxonomy import suggested_tag_for_check
-
-# The four checks, in a stable display/order — the result list is built in this order so the served
-# payload and every test are deterministic.
-CHECK_NAMES: tuple[str, ...] = (
-    "entered_before_confirmation",
-    "chased_entry",
-    "exited_beyond_invalidation",
-    "cut_confirming_early",
-)
-
-# Enum statuses (labels, never numeric scores).
-_FAILED = "failed"
-_PASSED = "passed"
-_NOT_APPLICABLE = "not_applicable"
-
-
-def _price(value: float | None) -> str:
-    return "n/a" if value is None else f"{value:.2f}"
-
-
-def _ts(value: float | None) -> str:
-    # Logical seconds, one decimal place — quotes the measured logical instant honestly (e.g.
-    # "14.0s"). The journal detail renders the same timeline in TRUE clock time from the persisted
-    # wall_ts; this evidence string names the logical instant the check measured.
-    return "n/a" if value is None else f"{value:.1f}s"
-
-
-def _pct(value: float) -> str:
-    return f"{value * 100:.2f}%"
-
-
-def _first(actions: list[ActionRecord], kind: str) -> ActionRecord | None:
-    return next((a for a in actions if a.kind == kind), None)
-
-
-def _first_confirming(timeline: list[VerdictEventRecord]) -> VerdictEventRecord | None:
-    """The FIRST published ``confirming`` event in the append-only timeline (insertion order)."""
-    return next((e for e in timeline if e.verdict == "confirming"), None)
-
-
-def _check(name: str, status: str, evidence: str) -> dict:
-    """One execution-check result row — status is an ENUM label, never a numeric score."""
-    return {"check": name, "status": status, "evidence": evidence}
-
-
-# --- the four checks ------------------------------------------------------------------------------
-
-def _entered_before_confirmation(
-    thesis: ThesisRecord,
-    entry: ActionRecord | None,
-    first_confirming: VerdictEventRecord | None,
-) -> dict:
-    name = "entered_before_confirmation"
-    if entry is None:
-        return _check(
-            name,
-            _NOT_APPLICABLE,
-            "No entry was recorded, so whether the entry preceded confirmation cannot be checked.",
-        )
-    if first_confirming is None:
-        return _check(
-            name,
-            _FAILED,
-            f"You recorded an entry at {_ts(entry.logical_ts)}, but the thesis never published a "
-            f"confirming verdict while you held it.",
-        )
-    if entry.logical_ts < first_confirming.logical_ts:
-        return _check(
-            name,
-            _FAILED,
-            f"Your entry at {_ts(entry.logical_ts)} precedes the first confirming verdict published "
-            f"at {_ts(first_confirming.logical_ts)} — you entered before the tape confirmed your "
-            f"thesis.",
-        )
-    return _check(
-        name,
-        _PASSED,
-        f"Your entry at {_ts(entry.logical_ts)} came after the first confirming verdict published "
-        f"at {_ts(first_confirming.logical_ts)}.",
-    )
-
-
-def _chased_entry(
-    thesis: ThesisRecord,
-    entry: ActionRecord | None,
-    first_confirming: VerdictEventRecord | None,
-    config: Config,
-) -> dict:
-    name = "chased_entry"
-    if entry is None:
-        return _check(
-            name,
-            _NOT_APPLICABLE,
-            "No entry was recorded, so whether the entry chased an extended move cannot be checked.",
-        )
-    # Anchor at the recorded ``rule_first_true`` price — the first logical instant the raw confirming
-    # rule held — NEVER the post-dwell publish price (per the Constraints). Without that anchor the
-    # check cannot be measured (a fabricated pass/fail would be dishonest).
-    anchor = first_confirming.rule_first_true_price if first_confirming is not None else None
-    if anchor is None:
-        return _check(
-            name,
-            _NOT_APPLICABLE,
-            "No first-confirmation anchor price was recorded, so whether the entry chased an "
-            "extended move cannot be measured.",
-        )
-    threshold = config.chase_return_threshold
-    if thesis.direction == "long":
-        # A long chases when it enters ABOVE the anchor by more than the chase return.
-        band = anchor * (1.0 + threshold)
-        chased = entry.price > band
-        side = "above"
-    else:
-        # A short chases when it enters BELOW the anchor by more than the chase return (the move has
-        # already fallen).
-        band = anchor * (1.0 - threshold)
-        chased = entry.price < band
-        side = "below"
-    move_return = abs(entry.price - anchor) / anchor if anchor else 0.0
-    if chased:
-        return _check(
-            name,
-            _FAILED,
-            f"Your entry at {_price(entry.price)} is {side} the first-confirmation price "
-            f"{_price(anchor)} by {_pct(move_return)}, past the {_pct(threshold)} chase threshold — "
-            f"the move had already run before you entered.",
-        )
-    return _check(
-        name,
-        _PASSED,
-        f"Your entry at {_price(entry.price)} is within {_pct(threshold)} of the first-confirmation "
-        f"price {_price(anchor)} ({_pct(move_return)} away) — you did not chase an extended move.",
-    )
-
-
-def _exited_beyond_invalidation(
-    thesis: ThesisRecord,
-    exit_: ActionRecord | None,
-) -> dict:
-    name = "exited_beyond_invalidation"
-    if exit_ is None:
-        return _check(
-            name,
-            _NOT_APPLICABLE,
-            "No exit was recorded, so whether the exit was beyond your invalidation cannot be checked.",
-        )
-    inval = thesis.invalidation_price
-    if thesis.direction == "long":
-        beyond = exit_.price <= inval  # a long is invalidated at/below the invalidation
-        side = "at or below"
-    else:
-        beyond = exit_.price >= inval  # a short is invalidated at/above the invalidation
-        side = "at or above"
-    if beyond:
-        return _check(
-            name,
-            _FAILED,
-            f"Your exit at {_price(exit_.price)} is {side} your invalidation at {_price(inval)} — "
-            f"you held through the stop.",
-        )
-    return _check(
-        name,
-        _PASSED,
-        f"Your exit at {_price(exit_.price)} is on the right side of your invalidation at "
-        f"{_price(inval)} — you did not hold through the stop.",
-    )
-
-
-def _cut_confirming_early(
-    thesis: ThesisRecord,
-    exit_: ActionRecord | None,
-    timeline: list[VerdictEventRecord],
-) -> dict:
-    name = "cut_confirming_early"
-    if exit_ is None:
-        return _check(
-            name,
-            _NOT_APPLICABLE,
-            "No exit was recorded, so whether a confirming thesis was cut early cannot be checked.",
-        )
-    # The latest PUBLISHED verdict at the exit's logical_ts: the last timeline row whose logical_ts is
-    # at or before the exit (the append-only timeline is in insertion = logical order). A verdict
-    # describes the tape at its logical instant; the exit is judged against the verdict in effect then.
-    latest_verdict: str | None = None
-    latest_ts: float | None = None
-    for e in timeline:
-        if e.logical_ts <= exit_.logical_ts and e.verdict in (
-            "pending",
-            "confirming",
-            "weakening",
-            "rejecting",
-            "invalidated",
-        ):
-            latest_verdict = e.verdict
-            latest_ts = e.logical_ts
-    if latest_verdict == "confirming":
-        return _check(
-            name,
-            _FAILED,
-            f"Your exit at {_ts(exit_.logical_ts)} came while the latest published verdict was "
-            f"confirming (published at {_ts(latest_ts)}) — you cut a confirming thesis early, "
-            f"before it weakened or rejected.",
-        )
-    return _check(
-        name,
-        _PASSED,
-        f"Your exit at {_ts(exit_.logical_ts)} came while the latest published verdict was "
-        f"{latest_verdict or 'pending'} — you did not cut a confirming thesis early.",
-    )
-
-
-def compute_execution_checks(
-    thesis: ThesisRecord,
-    *,
-    actions: list[ActionRecord],
-    timeline: list[VerdictEventRecord],
-    config: Config,
-) -> dict:
-    """Compute the four named execution checks ONCE at terminal resolution (capability 27, J-54).
-
-    PURE: derives everything from the persisted ``actions`` (in insertion order), the append-only
-    ``timeline`` (in insertion = logical order), and the FROZEN ``thesis`` fields + ``config`` — no
-    engine, no live snapshot. Returns ``{"checks": [...], "suggested_mistake_tags": [...]}``:
-      * ``checks`` — one row per check (in ``CHECK_NAMES`` order), each ``{check, status, evidence}``
-        with an ENUM status (``failed | passed | not_applicable`` — never a numeric score) and
-        plain-language evidence quoting the measured values;
-      * ``suggested_mistake_tags`` — the backend-owned tags for the FAILED checks (taxonomy
-        ``CHECK_SUGGESTED_TAG``), de-duplicated and in ``CHECK_NAMES`` order. The system SUGGESTS
-        only; the user confirms tags in the review flow (J-57).
-    """
-    entry = _first(actions, "entry")
-    exit_ = _first(actions, "exit")
-    first_confirming = _first_confirming(timeline)
-
-    checks = [
-        _entered_before_confirmation(thesis, entry, first_confirming),
-        _chased_entry(thesis, entry, first_confirming, config),
-        _exited_beyond_invalidation(thesis, exit_),
-        _cut_confirming_early(thesis, exit_, timeline),
-    ]
-
-    # Suggested tags for the FAILED checks only — deduplicated, in CHECK_NAMES order.
-    suggested: list[str] = []
-    for check in checks:
-        if check["status"] != _FAILED:
-            continue
-        tag = suggested_tag_for_check(check["check"])
-        if tag is not None and tag not in suggested:
-            suggested.append(tag)
-
-    return {"checks": checks, "suggested_mistake_tags": suggested}
-
-
-def compute_and_persist_execution_checks(
-    store: JournalStore, thesis_id: str, config: Config
-) -> dict | None:
-    """Compute the execution checks for a just-resolved thesis from the store ONCE and persist them.
-
-    The single entry point every terminal-resolution code path calls (user resolve, system
-    invalidation, stream-end / stop expiry, restart-expiry sweep) right AFTER the thesis status is
-    flipped: it reads the thesis + its recorded marks + its append-only timeline back from the store,
-    runs the pure :func:`compute_execution_checks`, and persists the result on the thesis row via
-    ``store.set_execution_checks`` — so the checks are computed and stored exactly ONCE at the
-    defining moment, never recomputed at read. Returns the computed result (or ``None`` if the thesis
-    is gone). Idempotent guard: if the thesis already carries execution_checks (a double-resolve
-    race), it is NOT recomputed — the first computation stands (append-only spirit)."""
-    thesis = store.get_thesis(thesis_id)
-    if thesis is None:
-        return None
-    if thesis.execution_checks is not None:
-        return thesis.execution_checks
-    result = compute_execution_checks(
-        thesis,
-        actions=store.get_actions(thesis_id),
-        timeline=store.verdict_events(thesis_id),
-        config=config,
-    )
-    store.set_execution_checks(thesis_id, result)
-    return result
diff --git a/apps/backend/app/research/grades.py b/apps/backend/app/research/grades.py
deleted file mode 100644
index 83805cb..0000000
--- a/apps/backend/app/research/grades.py
+++ /dev/null
@@ -1,154 +0,0 @@
-"""Outcome × process grades (capability 29, J-56) — the SINGLE-owner pure functions.
-
-This is the ONE place the two review grades are computed. Every terminal-resolution code path (the
-user ``POST /research/thesis/{id}/resolve``, the system invalidation auto-resolve, the stream-end /
-stop expiry, and the restart-expiry sweep) calls THIS once at the defining moment — right AFTER the
-execution checks are persisted — and stores the result on the thesis row (schema v6). The journal
-surfaces serve the persisted result VERBATIM; nothing is recomputed at read.
-
-Both axes are ENUM LABELS with plain-language evidence — NEVER a numeric score (the no-numeric-score
-anti-goal):
-
-  * **outcome** ∈ ``thesis_held | thesis_failed | no_read`` — 1:1 from the resolution via the
-    config-owned ``process_outcome_grade_map`` (goal.md capability 29). A fixed mapping, never a
-    judgement: ``played_out → thesis_held``, ``invalidated → thesis_failed``,
-    ``expired``/``abandoned → no_read``.
-  * **process** ∈ ``clean | flagged | violated`` — a config-owned RULE over the named,
-    evidence-backed checks (the FROZEN entry risk flags + the persisted execution checks). The worst
-    named finding wins: a FAILED execution check (grounded in the user's OWN recorded marks)
-    ``violates``; an entry risk flag that fired at declaration (advisory) ``flags``; neither is
-    ``clean``. CRITICALLY — **being invalidated is never by itself a process failure** (the system
-    enforces invalidation): an invalidated thesis with no failed execution check and no fired risk
-    flag grades ``clean``. The grade is evidence-backed: it names exactly which checks / flags drove
-    it (no-naked-outputs).
-
-The grade thresholds (how many failed checks ``violate``, how many fired flags ``flag``) are
-config-owned (``process_violated_min_failed_checks`` / ``process_flagged_min_risk_flags``) — no
-literal lives here.
-"""
-
-from __future__ import annotations
-
-from ..config import Config
-from .store import ThesisRecord
-
-# The grade enum ids (display copy lives in the taxonomy — the frontend hardcodes none of them).
-OUTCOME_GRADES: tuple[str, ...] = ("thesis_held", "thesis_failed", "no_read")
-PROCESS_GRADES: tuple[str, ...] = ("clean", "flagged", "violated")
-
-_FAILED = "failed"  # the execution-check status that grounds a process violation
-
-
-def _compute_outcome(resolution: str, config: Config) -> str:
-    """The outcome grade — 1:1 from the resolution via the config-owned map (never a judgement).
-
-    A resolution outside the map (which should never happen — the four terminal statuses are the
-    only resolutions) yields ``no_read`` honestly rather than a fabricated outcome."""
-    return config.process_outcome_grade_map.get(resolution, "no_read")
-
-
-def _named_findings(thesis: ThesisRecord) -> tuple[list[str], list[str]]:
-    """The named findings the process rule weighs, read VERBATIM from the persisted record:
-
-      * the FAILED execution checks (by check name) — grounded in the user's OWN recorded marks;
-      * the fired entry risk flags (by flag id) — advisory, frozen at declaration.
-
-    Honest absence: a thesis with no computed execution checks contributes no failed checks; one
-    never risk-assessed (``risk_flags`` ``None``) contributes no fired flags. Neither is fabricated.
-    """
-    failed_checks: list[str] = []
-    if thesis.execution_checks is not None:
-        for check in thesis.execution_checks.get("checks", []):
-            if check.get("status") == _FAILED:
-                failed_checks.append(check.get("check", "unknown_check"))
-    fired_flags: list[str] = []
-    if thesis.risk_flags:  # None (never assessed) or [] (nothing fired) -> no fired flags
-        fired_flags = [f.get("flag", "unknown_flag") for f in thesis.risk_flags]
-    return failed_checks, fired_flags
-
-
-def _process_evidence(grade: str, failed_checks: list[str], fired_flags: list[str]) -> str:
-    """Plain-language evidence naming the checks/flags that drove the process grade (no naked grade).
-
-    Present-tense, descriptive, thesis-attributed (J-66) — never imperative/predictive, never a
-    numeric score. Names the SPECIFIC findings so the grade is auditable."""
-    def _names(ids: list[str]) -> str:
-        return ", ".join(i.replace("_", " ") for i in ids)
-
-    if grade == "violated":
-        return (
-            f"Your own execution checks flagged: {_names(failed_checks)}. "
-            "A process violation reflects what you did — being invalidated is never itself a "
-            "process failure."
-        )
-    if grade == "flagged":
-        return (
-            f"No execution check failed, but entry risk flags fired at declaration: "
-            f"{_names(fired_flags)}. The entry carried advisories you declared into."
-        )
-    # clean
-    return (
-        "No execution check failed and no entry risk flag fired — the process was clean. "
-        "Being invalidated is never itself a process failure."
-    )
-
-
-def _compute_process(thesis: ThesisRecord, config: Config) -> tuple[str, str]:
-    """The process grade + its evidence (the config-owned rule over the named checks).
-
-    Worst named finding wins: a FAILED execution check ``violates``; else a fired entry risk flag
-    ``flags``; else ``clean``. Invalidation alone never grades a failure (the system enforces it —
-    it is recorded as the outcome ``thesis_failed``, never re-counted as a process fault)."""
-    failed_checks, fired_flags = _named_findings(thesis)
-    if len(failed_checks) >= config.process_violated_min_failed_checks:
-        grade = "violated"
-    elif len(fired_flags) >= config.process_flagged_min_risk_flags:
-        grade = "flagged"
-    else:
-        grade = "clean"
-    return grade, _process_evidence(grade, failed_checks, fired_flags)
-
-
-def compute_grades(thesis: ThesisRecord, resolution: str, *, config: Config) -> dict:
-    """Compute the outcome × process grades ONCE at terminal resolution (capability 29, J-56).
-
-    PURE: derives both from the (already-persisted at this point) execution checks + the FROZEN entry
-    risk flags + the resolution + ``config`` — no engine, no live snapshot. Returns::
-
-        {
-          "outcome": "thesis_held" | "thesis_failed" | "no_read",
-          "process": "clean" | "flagged" | "violated",
-          "process_evidence": "<plain-language sentence naming the checks/flags that drove it>",
-        }
-
-    Both axes are ENUM labels — NEVER a numeric score. The display copy for the labels comes from the
-    taxonomy (the frontend hardcodes none); ``process_evidence`` is the no-naked-outputs evidence
-    naming the specific named findings.
-    """
-    outcome = _compute_outcome(resolution, config)
-    process, process_evidence = _compute_process(thesis, config)
-    return {
-        "outcome": outcome,
-        "process": process,
-        "process_evidence": process_evidence,
-    }
-
-
-def compute_and_persist_grades(store, thesis_id: str, resolution: str, config: Config) -> dict | None:
-    """Compute the grades for a just-resolved thesis ONCE and persist them on the thesis row.
-
-    Called by every terminal-resolution path right AFTER the execution checks are persisted (the
-    process rule weighs those checks), so the grades are computed and stored exactly ONCE at the
-    defining moment — never recomputed at read. Reads the thesis BACK from the store (so it picks up
-    the just-persisted ``execution_checks``), runs the pure :func:`compute_grades`, and persists via
-    ``store.set_grades``. Returns the computed result (or ``None`` if the thesis is gone). Idempotent
-    guard: if the thesis already carries grades (a double-resolve race), it is NOT recomputed — the
-    first computation stands (append-only spirit)."""
-    thesis = store.get_thesis(thesis_id)
-    if thesis is None:
-        return None
-    if thesis.grades is not None:
-        return thesis.grades
-    result = compute_grades(thesis, resolution, config=config)
-    store.set_grades(thesis_id, result)
-    return result
diff --git a/apps/backend/app/research/hints.py b/apps/backend/app/research/hints.py
deleted file mode 100644
index e10b817..0000000
--- a/apps/backend/app/research/hints.py
+++ /dev/null
@@ -1,254 +0,0 @@
-"""The setup-forming hint engine (capability 33, J-65) — the SINGLE computing owner of hints.
-
-Driven by the research monitor's ``on_event`` / ``on_status`` seam (observer-only; NO
-engine/classifier/feature file is ever touched, so engine outputs stay byte-identical with or without
-it — the equivalence anti-goal). The engine is a PURE, DETERMINISTIC, LOGICAL-TIME evaluator: it reads
-ONLY the frozen snapshot's tape state + its logical timestamp and decides, per event, whether a
-state-native pattern has SUSTAINED past the config dwell. No wall-clock enters a hint decision (the wall
-ts on a fired record is a stamp only — the verdict-dwell precedent), so sim journeys are deterministic.
-
-Discipline (the goal's capability 33 + the iter-23 spec):
-  * **Patterns compose EXISTING engine states ONLY** (no new indicator): a sustained absorption arms an
-    absorption_reversal context; a sustained control arms a trend_continuation context. ``unclear`` never
-    arms a hint; the two level setups have no state-native arming, so they never produce hints.
-  * **Dwell + cooldown are config-owned, logical-time, IN the fingerprint** (``hint_sustain_dwell_seconds``
-    / ``hint_cooldown_seconds`` — they shape the persisted hint records, the study-arm precedent). A
-    pattern fires ONCE when its premise state holds CONTINUOUSLY past the dwell; the cooldown gates a
-    re-fire of the SAME pattern on the SAME ticker. A flapping stream (SIM-CHOP) never holds one premise
-    long enough to fire — by construction.
-  * **Fire-once persistence** goes through the store's single writer queue (``insert_hint``), NEVER from
-    event processing / the WS serialization path; the monitor enqueues it from its exception-isolated
-    observer callback so a write failure surfaces as ``monitor_status: failed`` rather than killing the
-    feeder.
-  * **Active-hint lifecycle**: the hint stays active while its pattern's state persists; it clears when
-    the state leaves the pattern, when the watch stops, and on any non-live status flip (paused / stale /
-    closed / failed) — present-tense "is forming" copy must never sit over a non-live tape (the iter-22
-    J-64 freshness lesson). Clearing an ACTIVE hint never touches the persisted log record.
-  * **No naked outputs**: every fired/active hint carries plain-language evidence (with the measured
-    sustain duration) and a baseline citation — the user's matching studied baseline cited verbatim, or
-    exactly "no studied baseline — unvalidated pattern".
-"""
-
-from __future__ import annotations
-
-import logging
-import time
-import uuid
-
-from ..config import Config
-from ..engine.snapshot import EngineSnapshot
-from .feed_basis import data_feed_for_scenario
-from .store import HintRecord, JournalStore
-from .taxonomy import (
-    HINT_BASELINE_UNVALIDATED,
-    HINT_PATTERNS,
-    hint_baseline_citation,
-    hint_evidence,
-    hint_pattern_label,
-)
-
-logger = logging.getLogger(__name__)
-
-# Map a sustained tape state -> the pattern id it arms. The single authority for which states arm a hint
-# (composed ONLY of the existing engine states); ``unclear`` is deliberately absent (it never arms one).
-_STATE_TO_PATTERN: dict[str, str] = {
-    spec["tape_state"]: pid for pid, spec in HINT_PATTERNS.items()
-}
-
-# ``data_feed_for_scenario`` is re-exported from the leaf ``feed_basis`` module (the ONE owner,
-# data-contract row 26, iter-24) so existing ``from app.research.hints import data_feed_for_scenario``
-# call sites keep resolving. The iter-23 LOCAL copy is REMOVED, not paralleled — the single definition
-# now lives in ``feed_basis`` and reads the config-owned per-mode feed keys (J-67 single-config-value).
-
-
-def _baseline_citation(
-    store: JournalStore,
-    *,
-    setup_type: str,
-    data_feed: str,
-    config_fingerprint: str,
-) -> str:
-    """Produce the baseline citation ONCE at fire (capability 33, J-65). Reads the user's most recent
-    PERSISTED ``done`` study matching this hint's setup_type + data_feed + config_fingerprint (level
-    studies excluded by construction) and cites the STORED aggregates VERBATIM (n + the first-horizon
-    ternary distribution). When none exists the citation is EXACTLY the honest unvalidated string.
-
-    Never recomputes a study at read — it reads the already-persisted aggregate numbers; a read failure
-    degrades to the honest unvalidated string (a citation must never crash the fire path)."""
-    try:
-        study = store.latest_done_study_for(
-            setup_type=setup_type,
-            data_feed=data_feed,
-            config_fingerprint=config_fingerprint,
-        )
-    except Exception:  # pragma: no cover - defensive: a citation read must never crash the fire
-        logger.exception("hint baseline citation read failed")
-        return HINT_BASELINE_UNVALIDATED
-    if study is None:
-        return HINT_BASELINE_UNVALIDATED
-    aggregates = study.payload.get("aggregates", {})
-    setup_agg = aggregates.get("setup", {})
-    n = setup_agg.get("n", 0)
-    horizons = setup_agg.get("horizons", [])
-    if n <= 0 or not horizons:
-        return HINT_BASELINE_UNVALIDATED
-    first = horizons[0]
-    return hint_baseline_citation(
-        n=n,
-        plus=first.get("+1R_first", 0),
-        minus=first.get("-1R_first", 0),
-        neither=first.get("neither_within_horizon", 0),
-        horizon=first.get("horizon", 0),
-    )
-
-
-class HintEngine:
-    """One ticker's setup-forming hint evaluator (capability 33, J-65). Attached at engine creation
-    REGARDLESS of any thesis — it observes every event and serves the active-hint projection.
-
-    Holds the in-flight sustain clock (which premise state is currently building and since when), the
-    last fired logical time per pattern (the cooldown gate), and the currently ACTIVE hint record (the
-    live projection). All decisions are logical-time + deterministic; the store is touched only to
-    PERSIST a fired hint (through the single writer queue) and to READ the baseline at fire."""
-
-    def __init__(self, store: JournalStore, config: Config, ticker: str) -> None:
-        self._store = store
-        self._config = config
-        self._ticker = ticker
-        # The premise state currently building toward the dwell, and the logical instant it began.
-        self._pending_pattern: str | None = None
-        self._pending_since: float | None = None
-        # The last fired logical time per pattern (the cooldown gate against a same-pattern re-fire).
-        self._last_fired_logical: dict[str, float] = {}
-        # The currently ACTIVE hint projection (the live dock read) — ``None`` when no hint is active.
-        # It carries the persisted record's payload verbatim (the log record + the projection are the
-        # same dict by construction). Cleared on state-leave / non-live status (never touches the log).
-        self._active: dict | None = None
-
-    # --- the observer seam (driven by the monitor; runs inside its exception isolation) -----------
-    def on_event(self, snapshot: EngineSnapshot) -> None:
-        """Advance the sustain clock against this event's tape state; fire ONCE past the dwell.
-
-        Pure read of the snapshot (read-only over the engine — no engine/feature mutation). Logical-time
-        only: the dwell + cooldown measure ``snapshot.timestamp`` deltas. A non-live stream never sustains
-        a hint (an event arriving while the snapshot is not live clears any active hint — defensive; the
-        status seam is the primary freshness path)."""
-        # Freshness: a present-tense "is forming" hint must never sit over a non-live tape (J-64).
-        if snapshot.stream_status != "live":
-            self._clear_active()
-            self._pending_pattern = None
-            self._pending_since = None
-            return
-
-        state = snapshot.tape_state
-        logical = snapshot.timestamp
-        pattern = _STATE_TO_PATTERN.get(state)
-
-        if pattern is None:
-            # ``unclear`` (or any non-arming state) — the premise is broken; reset the sustain clock and
-            # clear any active hint (its pattern's state has left).
-            self._pending_pattern = None
-            self._pending_since = None
-            self._clear_active()
-            return
-
-        # The premise state changed -> restart the sustain clock at THIS logical instant. Any active hint
-        # for a now-departed pattern is cleared (its state left). A continuing same-pattern active hint is
-        # left in place (it stays active while its state persists).
-        if pattern != self._pending_pattern:
-            self._pending_pattern = pattern
-            self._pending_since = logical
-            if self._active is not None and self._active.get("pattern_id") != pattern:
-                self._clear_active()
-
-        # If a hint for THIS pattern is already active, keep it (active while its state persists) — no
-        # re-fire until the cooldown lets it (which only matters after it clears).
-        if self._active is not None and self._active.get("pattern_id") == pattern:
-            return
-
-        held_for = logical - (self._pending_since if self._pending_since is not None else logical)
-        if held_for < self._config.hint_sustain_dwell_seconds:
-            return  # premise not sustained past the dwell yet
-
-        # Cooldown: gate a re-fire of the SAME pattern within the window (logical-time).
-        last_fired = self._last_fired_logical.get(pattern)
-        if last_fired is not None and (logical - last_fired) < self._config.hint_cooldown_seconds:
-            # Within the cooldown — do NOT fire a new record, but the premise IS sustained, so the dock
-            # would otherwise show nothing; the spec gates RE-FIRES (new log records), not the visibility
-            # of the sustained state. We leave no active hint here (the previous one cleared on
-            # state-leave); a re-fire is suppressed until the cooldown elapses.
-            return
-
-        self._fire(snapshot, pattern, held_for)
-
-    def on_status(self, status: str) -> None:
-        """Clear the active hint on any non-live status flip (paused / stale / closed / failed) — the
-        present-tense copy must never sit over a non-live tape (J-64). The sustain clock is also reset so
-        a resume re-accrues the dwell from scratch (a paused gap is not sustained tape). Clearing never
-        touches the persisted log record (the log survives every status flip)."""
-        if status != "live":
-            self._clear_active()
-            self._pending_pattern = None
-            self._pending_since = None
-
-    # --- firing + projection ----------------------------------------------------------------------
-    def _fire(self, snapshot: EngineSnapshot, pattern: str, held_for: float) -> None:
-        """Produce the hint record ONCE and persist it through the single writer queue.
-
-        Builds the full payload (pattern, plain-language evidence with the measured sustain duration,
-        setup-type context + direction, baseline citation, honesty stamps, logical + wall ts), persists
-        it via ``insert_hint`` (the writer queue — never the event/WS path), records the cooldown anchor,
-        and sets it as the active projection. A persist failure RAISES so the monitor's try/except flips
-        ``monitor_status: failed`` (the feeder stays alive) — no half-state: no active hint, no cooldown
-        anchor advanced, on failure."""
-        spec = HINT_PATTERNS[pattern]
-        setup_type = spec["setup_type"]
-        direction = spec["direction"]
-        data_feed = data_feed_for_scenario(snapshot.scenario, self._config)
-        fingerprint = self._config.config_fingerprint()
-        citation = _baseline_citation(
-            self._store,
-            setup_type=setup_type,
-            data_feed=data_feed,
-            config_fingerprint=fingerprint,
-        )
-        payload = {
-            "id": uuid.uuid4().hex,
-            "ticker": self._ticker,
-            "pattern_id": pattern,
-            "pattern_label": hint_pattern_label(pattern),
-            "evidence": hint_evidence(pattern, held_for),
-            "setup_type": setup_type,
-            "direction": direction,
-            "baseline_citation": citation,
-            "bound_source": snapshot.scenario,
-            "data_feed": data_feed,
-            "config_fingerprint": fingerprint,
-            "logical_ts": snapshot.timestamp,
-            "wall_ts": time.time(),
-        }
-        record = HintRecord(
-            id=payload["id"],
-            ticker=self._ticker,
-            payload=payload,
-            created_wall_ts=payload["wall_ts"],
-        )
-        # Persist FIRST (through the writer queue). A failure raises out to the monitor's try/except
-        # before any in-memory state is advanced, so a failed write never leaves a phantom active hint or
-        # a falsely-advanced cooldown.
-        self._store.insert_hint(record)
-        self._last_fired_logical[pattern] = snapshot.timestamp
-        self._active = payload
-
-    def _clear_active(self) -> None:
-        """Clear the live active-hint projection (never touches the persisted log record)."""
-        self._active = None
-
-    def projection(self) -> dict | None:
-        """The active-hint projection (the dock read), or ``None`` (a NORMAL state, not an error).
-
-        Both ``GET /research/hints/active`` and the WS ``hint`` key call THIS one function, so the two
-        are verbatim-equal by construction (data-contract row 22). The projection is the fired record's
-        payload verbatim — the log record and the live projection are the same dict (single source of
-        truth; the dock never recomputes evidence or citation)."""
-        return self._active
diff --git a/apps/backend/app/research/journal_rows.py b/apps/backend/app/research/journal_rows.py
deleted file mode 100644
index 13aef65..0000000
--- a/apps/backend/app/research/journal_rows.py
+++ /dev/null
@@ -1,75 +0,0 @@
-"""Journal-row projection (J-51, data-contract row 21 — journal-rows half) — the SINGLE source.
-
-This is the ONE place a compact journal-list row is built from a persisted thesis record. The list
-endpoint ``GET /research/journal`` is the ONLY serving path for these rows (no second endpoint, no
-second computation). Mirrors ``marks.py``'s single-owner discipline: every value is a VERBATIM read
-of an already-persisted record — id, ticker, bound source, ``data_feed``, ``config_fingerprint``,
-setup, direction, declared logical + wall timestamps, status, the resolution (the terminal status,
-or ``None`` while active), the VERBATIM persisted expired/interruption reason, and entry/exit-mark
-presence. NOTHING is recomputed at read: the resolution reason is the literal ``evidence`` string the
-verdict engine / lifecycle sweep already wrote to the terminal timeline event; mark presence is the
-persisted action fact, never inferred from a price.
-
-Grade / reviewed fields (data-contract row 21 — the pre-announced additive keys, J-56/J-57): the
-``grades`` object is added VERBATIM as a row key ONLY once it has been computed at resolution (a
-pre-grade row OMITS it — honest omission, never a dishonest placeholder); ``reviewed`` is ALWAYS
-present (a boolean fact — ``False`` until the user saves a review). Both are reads of the persisted
-record — never recomputed at read.
-"""
-
-from __future__ import annotations
-
-from .store import ThesisRecord
-
-# The terminal statuses that count as a RESOLUTION (a resolution IS the thesis's terminal status).
-# An ``active`` thesis has no resolution — the row reports ``resolution: None`` (honest absence).
-_TERMINAL_STATUSES = ("played_out", "abandoned", "invalidated", "expired")
-
-
-def journal_row(
-    thesis: ThesisRecord,
-    *,
-    resolution_reason: str | None,
-    has_entry: bool,
-    has_exit: bool,
-) -> dict:
-    """The single, canonical compact journal-list row for one persisted thesis (computed once).
-
-    Args (all read VERBATIM from already-persisted records — never recomputed):
-      * ``thesis`` — the persisted ``theses`` row.
-      * ``resolution_reason`` — the verbatim ``evidence`` of the thesis's terminal verdict event (the
-        persisted expired/interruption/resolution reason), or ``None`` while the thesis is active. The
-        caller reads it from the append-only timeline; this function never derives it.
-      * ``has_entry`` / ``has_exit`` — the persisted action-mark presence facts (never inferred).
-
-    ``resolution`` is the terminal status (or ``None`` while active) — the same string as ``status``
-    once terminal, surfaced under its own key so the frontend reads a resolution explicitly rather
-    than inferring one from the status."""
-    is_terminal = thesis.status in _TERMINAL_STATUSES
-    row = {
-        "id": thesis.id,
-        "ticker": thesis.ticker,
-        "bound_source": thesis.bound_source,
-        "data_feed": thesis.data_feed,
-        "config_fingerprint": thesis.config_fingerprint,
-        "setup_type": thesis.setup_type,
-        "direction": thesis.direction,
-        "created_logical_ts": thesis.created_logical_ts,
-        "created_wall_ts": thesis.created_wall_ts,
-        "status": thesis.status,
-        # A resolution IS the terminal status; ``None`` while active (honest absence, never fabricated).
-        "resolution": thesis.status if is_terminal else None,
-        # The VERBATIM persisted reason (terminal-event evidence) — never recomputed at read.
-        "resolution_reason": resolution_reason if is_terminal else None,
-        # Mark presence — the persisted action fact the UI reads (never inferred from a price).
-        "has_entry": has_entry,
-        "has_exit": has_exit,
-        # The user-confirmed-review fact (J-57, data-contract row 21) — ALWAYS present (a boolean: a
-        # pre-review row reads ``False``, never absent — it is a definite fact, not a computed value).
-        "reviewed": thesis.reviewed,
-    }
-    # The outcome × process grades (J-56, data-contract row 21) — added VERBATIM ONLY once computed at
-    # resolution (a pre-grade row OMITS the key entirely — honest omission, never a fabricated grade).
-    if thesis.grades is not None:
-        row["grades"] = thesis.grades
-    return row
diff --git a/apps/backend/app/research/marks.py b/apps/backend/app/research/marks.py
deleted file mode 100644
index 9557c66..0000000
--- a/apps/backend/app/research/marks.py
+++ /dev/null
@@ -1,84 +0,0 @@
-"""Action-mark + realized-R projection (J-52, data-contract rows 18 & 27) — the SINGLE source.
-
-This is the ONE place the entry/exit marks and the realized move in R are computed. Both the
-row-15 thesis projection (REST ``/research/thesis/active`` ≡ the WS ``thesis`` key) and
-``GET /research/journal/{id}`` call THIS function, so the values are identical by construction
-(no second computation path, no client-side arithmetic — the strip renders the result verbatim).
-
-R semantics (per the goal doc glossary + the iter spec):
-  * **R basis** ``R = |entry_price − invalidation_price|`` — present once an ENTRY mark exists.
-  * **Realized move in R** — present ONLY once BOTH marks exist: the price change from entry to exit
-    expressed in R units and SIGNED BY DIRECTION (a long that exited higher than entry is a positive
-    realized move; a short that exited lower is positive). It is a journaled MEASUREMENT in R units
-    only — never currency P&L, never a profit/loss claim (no-profitability anti-goal).
-  * With no marks, the realized keys are ``None`` — NO realized metric is shown (no dishonest zero).
-  * ``spread_at_mark`` is carried per mark verbatim (a recorded moment value; never recomputed).
-
-A degenerate ``R == 0`` basis (entry exactly at invalidation — the API rejects a wrong-side
-invalidation, but a mark recorded verbatim could still land there) yields a ``None`` realized move
-rather than a divide-by-zero or a fabricated infinity — honest absence over a fabricated number.
-"""
-
-from __future__ import annotations
-
-from .store import ActionRecord, ThesisRecord
-
-
-def r_basis(reference_price: float, invalidation_price: float) -> float:
-    """The ONE shared R basis: ``R = |reference - invalidation|`` (the goal-doc glossary's R unit).
-
-    The SINGLE owner of the R definition — both ``marks_projection`` (row 27 realized-R) and the
-    excursion calculator (row 20, capability 30) call THIS function, so the R basis is computed by
-    one formula everywhere (never a second one). ``reference_price`` is the entry mark for realized-R
-    and the entry/confirmation anchor's reference price for excursions; ``invalidation_price`` is the
-    declared invalidation. A degenerate ``R == 0`` (reference exactly at the invalidation) is returned
-    as-is so the caller decides the honest no-metric behaviour (no divide-by-zero, no fabricated
-    infinity)."""
-    return abs(reference_price - invalidation_price)
-
-
-def _mark_dict(record: ActionRecord) -> dict:
-    """One mark, projected verbatim (price + logical/wall stamps + recorded moment spread)."""
-    return {
-        "kind": record.kind,
-        "price": record.price,
-        "logical_ts": record.logical_ts,
-        "wall_ts": record.wall_ts,
-        "spread_at_mark": record.spread_at_mark,
-    }
-
-
-def marks_projection(thesis: ThesisRecord, actions: list[ActionRecord]) -> dict:
-    """The single, canonical marks + realized-R projection for a thesis (computed once).
-
-    ``actions`` is the thesis's persisted action rows in insertion order. Returns a dict with:
-      * ``entry`` / ``exit`` — the verbatim mark (or ``None`` if not recorded);
-      * ``has_entry`` — the entry-marked fact the UI reads to WITHDRAW the Abandon control (it never
-        guesses);
-      * ``r_basis`` — ``|entry − invalidation|`` once an entry exists, else ``None``;
-      * ``realized_r`` — the signed realized move in R once BOTH marks exist, else ``None``.
-    The first ``entry`` / first ``exit`` win (one of each is enforced at the API; this is defensive).
-    """
-    entry = next((a for a in actions if a.kind == "entry"), None)
-    exit_ = next((a for a in actions if a.kind == "exit"), None)
-
-    r_basis_value: float | None = None
-    realized_r: float | None = None
-    if entry is not None:
-        # The ONE shared R-basis helper (never a second formula) — also used by the excursion
-        # calculator so realized-R and excursions share a single R definition.
-        r_basis_value = r_basis(entry.price, thesis.invalidation_price)
-        if exit_ is not None and r_basis_value > 0:
-            # Price change from entry to exit, signed so a move in the thesis's FAVOR is positive
-            # (long: exit above entry; short: exit below entry), expressed in R units.
-            raw_move = exit_.price - entry.price
-            directed = raw_move if thesis.direction == "long" else -raw_move
-            realized_r = directed / r_basis_value
-
-    return {
-        "entry": _mark_dict(entry) if entry is not None else None,
-        "exit": _mark_dict(exit_) if exit_ is not None else None,
-        "has_entry": entry is not None,
-        "r_basis": r_basis_value,
-        "realized_r": realized_r,
-    }
diff --git a/apps/backend/app/research/monitor.py b/apps/backend/app/research/monitor.py
deleted file mode 100644
index b9a61d9..0000000
--- a/apps/backend/app/research/monitor.py
+++ /dev/null
@@ -1,1382 +0,0 @@
-"""The research monitor — attached to the engine's observer seam, read-only over the engine.
-
-One ``ResearchMonitor`` is attached per watched ticker via ``TapeEngine.add_observer`` (capability
-20). It holds that ticker's active thesis, recomputes each frozen expected-behaviour statement's
-LIVE status (met / not_yet / violated) on every processed event from EXISTING engine
-states/features ONLY, and serves the single thesis projection that feeds BOTH the REST
-``/research/thesis/active`` read and the WS ``thesis`` key (so they are verbatim-equal by
-construction). The verdict is fixed at ``pending`` this iteration.
-
-Discipline:
-  * **Read-only over the engine** — the monitor never mutates engine/classifier/feature state, so
-    engine outputs stay byte-identical with or without it (equivalence anti-goal). It only READS the
-    snapshot handed to ``on_event`` and the thesis it is holding.
-  * **Exception-isolated, feed never dies** — the engine already isolates a throwing observer; on
-    top of that, the monitor catches its OWN errors (e.g. a statement-eval bug, or a store write
-    failure on the verdict-event path) and flips an internal ``_failed`` flag so the projection
-    reads ``monitor_status: failed`` rather than killing the feeder or silently dropping records.
-  * **Writes go through the store's queue** — the initial ``pending`` event is enqueued; a store
-    write failure surfaces as ``monitor_status: failed``.
-
-The entry risk flags (capability 26, J-49) are computed ONCE at declaration by ``compute_risk_flags``
-(invoked from ``POST /research/thesis`` where ``entry_context`` is frozen) and stored verbatim on the
-thesis; ``build_projection`` re-exposes the FROZEN list verbatim as the additive ``risk_flags`` key
-(omitting the key entirely for a pre-v4 thesis that was never assessed — an absent key and an empty
-list are distinct honest states). Flags are never recomputed at read and never a second computation
-path — exactly the geometry pattern.
-"""
-
-from __future__ import annotations
-
-import logging
-import time
-
-from ..config import Config
-from ..engine.snapshot import EngineSnapshot
-from .excursions import ExcursionTracker, compute_and_persist_excursions
-from .feed_basis import data_feed_for_scenario
-from .execution_checks import compute_and_persist_execution_checks
-from .grades import compute_and_persist_grades
-from .hints import HintEngine
-from .marks import marks_projection
-from .stance import (
-    EntryChecklistEvaluator,
-    StanceEvaluator,
-    build_checklist,
-    compute_position_readouts,
-)
-from .store import JournalStore, ThesisRecord, VerdictEventRecord
-from .taxonomy import (
-    GEOMETRY_ENTRY_MARK_LABEL,
-    GEOMETRY_EXIT_MARK_LABEL,
-    GEOMETRY_FIRST_CONFIRMATION_LABEL,
-    GEOMETRY_INVALIDATION_LINE_LABEL,
-    GEOMETRY_LEVEL_LINE_LABEL,
-    against_expected_tape_evidence,
-    before_warmup_evidence,
-    chasing_entry_evidence,
-    invalidation_too_tight_evidence,
-    low_trade_speed_evidence,
-    management_stance_label,
-    mismatched_source_notice,
-    risk_flag_label,
-    verdict_marker_label,
-    wide_spread_illiquid_evidence,
-)
-from .verdict import VerdictEvaluator
-
-# Timeline rows that are GAP/segment delimiters, not published verdict transitions: they are never
-# drawn as verdict markers (capability 25 / J-48). ``watch_restarted`` ALSO delimits the current
-# watch's drawable segment (the honest segment rule below). ``paused`` / ``stale`` join it here when
-# those gap rows are appended (forward-compatible; only ``watch_restarted`` is written today).
-_GAP_VERDICTS: frozenset[str] = frozenset({"watch_restarted", "paused", "stale"})
-
-logger = logging.getLogger(__name__)
-
-# ``data_feed_for_scenario`` is the ONE consolidated scenario -> ``data_feed`` mapping, owned by the
-# leaf ``feed_basis`` module (data-contract row 26, iter-24). It is re-exported here (imported above)
-# so existing ``from app.research.monitor import data_feed_for_scenario`` call sites keep resolving;
-# the single DEFINITION lives in ``feed_basis`` (no parallel copy — the hints.py duplicate is gone).
-__all__ = ["data_feed_for_scenario"]
-
-
-def _evaluate_statement(
-    statement: dict, snap: EngineSnapshot, thesis: ThesisRecord, config: Config
-) -> str:
-    """The LIVE status of one frozen statement from EXISTING engine states/features only.
-
-    Returns one of ``met | not_yet | violated``. No new indicator is computed — each ``kind`` reads
-    canonical snapshot values (tape_state, primary-window price impact, last vs invalidation). The
-    honest default is ``not_yet`` (no evidence is not a failure); ``violated`` is reserved for a read
-    that contradicts the statement. ``config`` supplies the config-owned cutoffs the
-    ``directional_impact`` adverse-side dominance test reuses (no magic number in research code).
-    """
-    kind = statement.get("kind")
-    params = statement.get("params", {})
-    direction = thesis.direction
-
-    if kind == "tape_state_is":
-        states = params.get("states", [])
-        return "met" if snap.tape_state in states else "not_yet"
-
-    if kind == "directional_impact":
-        # Progress in the thesis direction is judged by a TRUE favorable-vs-adverse DOMINANCE
-        # comparison (iter-8 fix), not the adverse-fires-first ordering of iter-6/7 (which branded a
-        # cleanly CONFIRMING SIM-BUYER tape — buy +0.42 dominating a minority sell −0.14 — "violated"
-        # one line under evidence saying the tape confirms). It composes ONLY the existing
-        # primary-window ``buy_price_impact`` / ``sell_price_impact`` values, read verbatim from the
-        # snapshot (single source of truth — never recomputed), against the classifier's OWN
-        # config-owned real-price-progress cutoffs (no magic number in research code): a side is
-        # "material" when its impact clears that cutoff (``buy_price_impact >= min_buy_price_impact`` /
-        # ``sell_price_impact <= max_sell_price_impact``). For a LONG thesis the favorable side is
-        # buying and the adverse side is selling; for a SHORT thesis the sides swap.
-        #
-        # Semantics (direction-aware; the SHORT case is the exact symmetric mirror):
-        #   * neither side material            => not_yet  (no evidence is not a failure)
-        #   * only the favorable side material => met
-        #   * only the adverse side material   => violated
-        #   * BOTH material                    => the side with the larger impact MAGNITUDE rules
-        #       (favorable dominant => met; adverse dominant => violated). A plain magnitude
-        #       comparison — no tolerance/ratio is needed, so no new config value/literal is
-        #       introduced (and the config fingerprint is unchanged by this fix).
-        #
-        # Truth anchors (the four-quadrant + flat tests pin these): SIM-BUYER long (buy +0.42 vs sell
-        # −0.14) => met; SIM-SELLER long (sell ~−0.28 dominant) => violated; SIM-BUYER short =>
-        # violated; SIM-SELLER short => met. The iter-6 direction-awareness is preserved: an
-        # incidentally positive buy_impact on a genuinely falling tape still reads violated for a
-        # long because the dominant (adverse) sell impact wins.
-        primary = snap.primary_features
-        buy_impact = primary.get("buy_price_impact", 0.0)
-        sell_impact = primary.get("sell_price_impact", 0.0)
-        if direction == "long":
-            favorable_impact = buy_impact
-            adverse_impact = sell_impact
-            favorable = buy_impact >= config.min_buy_price_impact
-            adverse = sell_impact <= config.max_sell_price_impact
-        else:
-            favorable_impact = sell_impact
-            adverse_impact = buy_impact
-            favorable = sell_impact <= config.max_sell_price_impact
-            adverse = buy_impact >= config.min_buy_price_impact
-
-        if not favorable and not adverse:
-            return "not_yet"
-        if favorable and not adverse:
-            return "met"
-        if adverse and not favorable:
-            return "violated"
-        # Both sides are material — the dominant side (by impact magnitude) rules.
-        return "met" if abs(favorable_impact) > abs(adverse_impact) else "violated"
-
-    if kind == "above_invalidation":
-        # last on the correct side of the declared invalidation (long => above; short => below).
-        # A print through the invalidation reads ``violated``; this is a status read only — the
-        # dwell-exempt invalidation-RESOLUTION engine arrives next iteration.
-        last = snap.last
-        if last is None:
-            return "not_yet"
-        if direction == "long":
-            return "met" if last > thesis.invalidation_price else "violated"
-        else:
-            return "met" if last < thesis.invalidation_price else "violated"
-
-    return "not_yet"
-
-
-# --- Per-statement FINAL statuses, persisted ONCE at terminal resolution (J-55) -----------------
-# A FINAL-status-only enum value: where no live evaluation context exists at the terminal moment
-# (e.g. the restart-expiry sweep over an unwatched thesis), each statement records this explicit,
-# honest enum — never fabricated, never recomputed at read.
-_NOT_EVALUATED = "not_evaluated"
-
-
-def compute_final_statement_statuses(
-    thesis: ThesisRecord, snapshot: EngineSnapshot | None, config: Config
-) -> list[dict]:
-    """The FINAL status of each frozen statement at the terminal moment (J-55), computed ONCE.
-
-    For a live-monitored terminal path (user resolve while still watched, system invalidation,
-    stream-end expiry) the snapshot is the engine's read at the terminal moment, and each statement's
-    final status is its at-resolution evaluation from the SAME ``_evaluate_statement`` the live
-    projection uses (one owner — no second evaluation rule). Where no live context exists (the
-    restart-expiry sweep over an unwatched thesis, ``snapshot is None``) every statement records the
-    explicit ``not_evaluated`` enum — an honest "no read at the terminal moment", never a fabricated
-    met/violated.
-
-    Returns one ``{"status": <enum>}`` entry per frozen statement, in statement order. The frozen
-    ``statements`` JSON is NEVER mutated — this is an additive parallel list keyed positionally to it.
-    """
-    if snapshot is None:
-        return [{"status": _NOT_EVALUATED} for _ in thesis.statements]
-    return [
-        {"status": _evaluate_statement(s, snapshot, thesis, config)}
-        for s in thesis.statements
-    ]
-
-
-def compute_and_persist_final_statuses(
-    store: JournalStore,
-    thesis_id: str,
-    snapshot: EngineSnapshot | None,
-    config: Config,
-) -> list[dict] | None:
-    """Compute the per-statement FINAL statuses for a just-resolved thesis ONCE and persist them.
-
-    The single entry point every terminal-resolution path calls right after the resolution: reads the
-    thesis back from the store, computes the final statuses via the pure
-    :func:`compute_final_statement_statuses` (using the handed terminal-moment ``snapshot``, or an
-    explicit ``not_evaluated`` per statement when there is none), and persists via
-    ``store.set_statement_final_statuses`` — so the statuses are recorded exactly ONCE at the defining
-    moment, never recomputed at read. Returns the computed list (or ``None`` if the thesis is gone).
-    Idempotent guard: if the thesis already carries final statuses (a double-resolve race), it is NOT
-    recomputed — the first computation stands (append-only spirit)."""
-    thesis = store.get_thesis(thesis_id)
-    if thesis is None:
-        return None
-    if thesis.statement_final_statuses is not None:
-        return thesis.statement_final_statuses
-    result = compute_final_statement_statuses(thesis, snapshot, config)
-    store.set_statement_final_statuses(thesis_id, result)
-    return result
-
-
-def _build_geometry(
-    thesis: ThesisRecord,
-    verdict_events: list,
-    marks: dict,
-) -> dict:
-    """The chart-ready ``geometry`` for a thesis (capability 25 / J-48) — a PURE projection.
-
-    Computed ONCE inside ``build_projection`` (the single row-15 builder) from canonical owners
-    ONLY — the declared thesis prices, the append-only verdict timeline (row 16), and the row-18
-    action marks already computed by ``marks_projection``. It recomputes NO side/state/price/time
-    basis (the chart draws this verbatim on the row-13 epoch anchor); the timeline is never edited or
-    recomputed here — its rows are re-exposed verbatim as markers.
-
-    Shape::
-
-        {
-          "price_lines": [ {kind, price, label}, … ],   # invalidation always; level only when set
-          "markers":     [ {kind, …}, … ],              # verdict transitions + marks + 1st-confirm
-        }
-
-    Honest segment rule: only events placeable on the CURRENT watch's logical timeline are drawn —
-    i.e. events at/after the latest ``watch_restarted`` gap event when one exists. A re-attached
-    thesis's pre-gap events belong to a previous watch's timeline and would be MISPLACED on this
-    watch's clock, so they are omitted from the chart (they remain fully visible in the journal
-    timeline). Price-lines are time-independent and ALWAYS served.
-    """
-    # --- price-lines (time-independent; declared prices verbatim) ---------------------------------
-    price_lines = [
-        {
-            "kind": "invalidation",
-            "price": thesis.invalidation_price,
-            "label": GEOMETRY_INVALIDATION_LINE_LABEL,
-        }
-    ]
-    if thesis.level_price is not None:
-        price_lines.append(
-            {
-                "kind": "level",
-                "price": thesis.level_price,
-                "label": GEOMETRY_LEVEL_LINE_LABEL,
-            }
-        )
-
-    # --- segment boundary: the latest watch_restarted gap (current-watch events only) -------------
-    # Rows are returned in insertion order (append-only ``id ASC``), so the LAST gap row index is the
-    # boundary; everything strictly after it belongs to the current watch's drawable timeline. The
-    # boundary is identified positionally for the timeline rows AND by its WALL time for the marks —
-    # ``logical_ts`` RESETS per watch (the engine's per-stream logical clock), so it cannot discriminate
-    # a pre-gap mark from a post-gap one; ``wall_ts`` is monotonic across re-watches (a re-watch always
-    # happens later in real time), so a mark recorded BEFORE the latest restart's wall time belongs to
-    # the previous watch's timeline and is omitted (it stays visible in the journal timeline).
-    boundary_wall: float | None = None
-    boundary_idx = -1
-    for i, ev in enumerate(verdict_events):
-        if ev.verdict == "watch_restarted":
-            boundary_idx = i
-            boundary_wall = ev.wall_ts
-    current_rows = verdict_events[boundary_idx + 1 :] if boundary_idx >= 0 else verdict_events
-
-    # --- verdict-transition markers (one per published transition; pure projection) ---------------
-    markers: list[dict] = []
-    first_confirmation_ts: float | None = None
-    for ev in current_rows:
-        if ev.verdict in _GAP_VERDICTS:
-            continue  # a gap delimiter is never drawn as a verdict marker
-        markers.append(
-            {
-                "kind": "verdict",
-                "verdict": ev.verdict,
-                "logical_ts": ev.logical_ts,
-                "wall_ts": ev.wall_ts,
-                "last": ev.last,
-                "label": verdict_marker_label(ev.verdict),
-            }
-        )
-        if ev.verdict == "confirming" and first_confirmation_ts is None:
-            first_confirmation_ts = ev.logical_ts
-
-    # --- the first-confirmation marker (identified once; only within the current segment) ---------
-    if first_confirmation_ts is not None:
-        markers.append(
-            {
-                "kind": "first_confirmation",
-                "logical_ts": first_confirmation_ts,
-                "label": GEOMETRY_FIRST_CONFIRMATION_LABEL,
-            }
-        )
-
-    # --- entry / exit mark markers (verbatim; present ONLY when the mark exists) -------------------
-    # Marks belonging to a PREVIOUS watch (recorded before the latest watch_restarted) are omitted by
-    # the same segment rule: a pre-gap mark's logical_ts cannot be placed on the current watch's
-    # clock. With no gap (the common case) every recorded mark is current and drawn.
-    def _mark_in_segment(mark: dict | None) -> bool:
-        if mark is None:
-            return False
-        if boundary_wall is None:
-            return True
-        return mark["wall_ts"] >= boundary_wall
-
-    entry = marks.get("entry")
-    if _mark_in_segment(entry):
-        markers.append(
-            {
-                "kind": "entry",
-                "price": entry["price"],
-                "logical_ts": entry["logical_ts"],
-                "wall_ts": entry["wall_ts"],
-                "label": GEOMETRY_ENTRY_MARK_LABEL,
-            }
-        )
-    exit_ = marks.get("exit")
-    if _mark_in_segment(exit_):
-        markers.append(
-            {
-                "kind": "exit",
-                "price": exit_["price"],
-                "logical_ts": exit_["logical_ts"],
-                "wall_ts": exit_["wall_ts"],
-                "label": GEOMETRY_EXIT_MARK_LABEL,
-            }
-        )
-
-    return {"price_lines": price_lines, "markers": markers}
-
-
-def _expected_tape_states(statements: list[dict]) -> list[str]:
-    """The setup's expected tape states — the union of every ``tape_state_is`` statement's resolved
-    ``states`` (direction already collapsed at ``frozen_statements``). The single source of truth for
-    ``against_expected_tape`` (composes EXISTING engine states only — no new mapping table)."""
-    expected: list[str] = []
-    for s in statements:
-        if s.get("kind") == "tape_state_is":
-            for st in s.get("params", {}).get("states", []):
-                if st not in expected:
-                    expected.append(st)
-    return expected
-
-
-def compute_risk_flags(
-    snapshot: EngineSnapshot,
-    *,
-    setup_type: str,
-    direction: str,
-    invalidation_price: float,
-    statements: list[dict],
-    config: Config,
-) -> list[dict]:
-    """Compute the capability-26 entry risk-flag set ONCE from the declaration-time snapshot + config.
-
-    Called exactly once inside ``POST /research/thesis`` (where ``entry_context`` is frozen); the
-    returned list is stored verbatim on the thesis and NEVER recomputed at read. Advisory only —
-    creation always succeeds regardless of how many fire. Returns a (possibly empty) list of frozen
-    entries, each ``{flag, label, evidence, measured}`` where:
-      * ``flag``     — the canonical flag id (taxonomy ``RISK_FLAGS``);
-      * ``label``    — the taxonomy-owned chip title (frozen so review reads it verbatim later);
-      * ``evidence`` — the plain-language MEASURED margin (taxonomy-owned template, J-66 copy);
-      * ``measured`` — the raw canonical values behind the flag (so review can show them with zero
-                       recompute).
-
-    Each flag READS canonical engine values verbatim (single source of truth) and REUSES the
-    classifier's OWN gates — it never duplicates a threshold:
-      * ``before_warmup``        — declaration trade count below ``warmup_min_events``;
-      * ``invalidation_too_tight`` — |last − invalidation| below the new
-        ``invalidation_too_tight_spread_multiple`` × current spread band;
-      * ``chasing_entry``        — the favorable-side price-impact RETURN (direction-aware; the SAME
-        ``buy_price_impact`` / ``sell_price_impact`` ÷ the canonical ``reference_price`` the classifier
-        uses as its relative impact metric) already past the new ``chase_return_threshold``;
-      * ``wide_spread_illiquid`` — the classifier's relative-spread gate VERBATIM (bps vs
-        ``max_stable_spread_bps`` when a price basis exists, else absolute vs ``max_stable_spread``);
-      * ``low_trade_speed``      — ``trade_speed`` below ``min_trade_speed`` VERBATIM;
-      * ``against_expected_tape`` — a DEFINITE snapshot tape state (not ``unclear``) that is NOT among
-        the setup's expected premise states (setup-aware; ``unclear`` is no contradiction so it never
... [diff_bound] apps/backend/app/research/monitor.py: 988 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/pnl_baseline.py b/apps/backend/app/research/pnl_baseline.py
index 5297ea8..2d29b76 100644
--- a/apps/backend/app/research/pnl_baseline.py
+++ b/apps/backend/app/research/pnl_baseline.py
@@ -34,13 +34,14 @@ from .datasets import (
     DatasetRecordError,
     DatasetStore,
     EmptyWindowError,
+    REFERENCE_SOURCE_ID,
+    SOURCE_REFERENCE,
     SPLIT_HOLDOUT,
     SPLIT_TRAIN,
     record_from_source,
 )
 from .pnl_ledger import LedgerCompositionError, append_validation_row
 from .store import DuplicateEnhancementError, JournalStore
-from .studies import REFERENCE_SOURCE_ID, SOURCE_REFERENCE
 
 
 class FoundingSeedError(Exception):
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 13e56f5..305e808 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -1,28 +1,24 @@
-"""The ``/research/*`` REST namespace (capabilities 23 / 24) — declare + read a thesis, taxonomy.
-
-Endpoints this iteration:
-  * ``GET  /research/taxonomy``            — the single backend owner of every research label.
-  * ``POST /research/thesis``              — declare a thesis with HONEST validation (404/409/422).
-  * ``GET  /research/thesis/active``       — the canonical thesis projection (``null`` is normal).
-
-Validation is never silent coercion: a not-watched ticker is 404, a second active thesis is 409,
-and every incoherent input (wrong-side invalidation, missing/forbidden level, unknown enums) is a
-422 — with NOTHING persisted on rejection. On success the entry context + expected-behaviour
-statements are frozen, the thesis is bound to its SOURCE IDENTITY (the snapshot's scenario
-descriptor, never the bare ticker), stamped with bound source + ``data_feed`` + ``config_fingerprint``,
-and the initial ``pending`` verdict event is appended (the timeline starts here).
+"""The ``/research/*`` REST namespace — the kept research surfaces: taxonomy (feed-basis labels),
+historical tape datasets, the multi-timeframe bar store, deterministic support/resistance levels +
+the tradable-level map, the touch-event/case-study registry, deterministic backtests, the PnL
+ledger, the profile + strategy registries, and the 3-way strategy-comparison edge report.
+
+era-5D J-01 ("The Clean Slate" demolition interlude) removed the journal-era thesis-declaration,
+replay-studies, and analytics routes from this file (14 route handlers total — see
+``docs/goal.md``'s I-1 inventory) — the manual-journaling product surfaces the operator judged not
+useful for digging the edge. Every route below is read-only-safe apart from the explicit,
+research-action POSTs (record a dataset, record a bar series, create a backtest, trigger an
+edge-report compute) — none of them execute a trade (``tests/test_no_execution_path.py`` is the
+tier-1 guard).
 
 The router depends on the app-provided ``ResearchRegistry`` (which owns the journal store and the
-per-ticker monitors) via FastAPI dependency-injection, so tests inject a temp-path store + a test
-WatchManager through ``dependency_overrides`` exactly like the market-adapter seam.
+backtest/edge-compute job managers) via FastAPI dependency-injection, so tests inject a temp-path
+store + a test WatchManager through ``dependency_overrides`` exactly like the market-adapter seam.
 """
 
 from __future__ import annotations
 
-import math
 import os
-import time
-import uuid
 
 from fastapi import APIRouter, Depends, HTTPException
 from pydantic import BaseModel
@@ -35,7 +31,6 @@ from ..providers.adapters.base import (
     VendorTimeout,
 )
 from ..providers.adapters.yahoo import YahooAdapter
-from .analytics import compute_analytics
 from .backtests import (
     BacktestJobManager,
     PROFILE_DEFAULT,
@@ -71,56 +66,22 @@ from .datasets import (
     DatasetRecordError,
     DatasetStore,
     EmptyWindowError,
+    REFERENCE_SOURCE_ID,
+    SOURCE_HISTORICAL,
+    SOURCE_REFERENCE,
     parse_utc_epoch,
     record_from_source,
 )
-from .excursions import compute_and_persist_excursions
-from .execution_checks import compute_and_persist_execution_checks
-from .grades import compute_and_persist_grades
-from .marks import marks_projection
-from .monitor import (
-    ResearchMonitor,
-    build_projection,
-    compute_and_persist_final_statuses,
-    compute_risk_flags,
-)
 from .pnl_ledger import ledger_projection
 from .profiles import profiles_projection
 from .strategies import strategies_projection
 from .feed_basis import data_feed_for_scenario
-from .journal_rows import journal_row
-from .store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord
-from .studies import (
-    REFERENCE_SOURCE_ID,
-    SOURCE_HISTORICAL,
-    SOURCE_REFERENCE,
-    SOURCE_SIM,
-    TERMINAL_STATUSES as STUDY_TERMINAL_STATUSES,
-    StudyJobManager,
-)
-from .taxonomy import not_evaluated_notice
-from .taxonomy import (
-    MISTAKE_TAGS_REQUIRING_NOTE,
-    frozen_statements,
-    is_valid_direction,
-    is_valid_mistake_tag,
-    is_valid_setup,
-    setup_requires_level,
-    taxonomy_payload,
-)
+from .store import JournalStore
+from .taxonomy import taxonomy_payload
 
 router = APIRouter(prefix="/research", tags=["research"])
 
 
-# The terminal statuses a thesis can carry. A USER may set only ``played_out`` / ``abandoned`` via
-# the resolve endpoint; ``invalidated`` / ``expired`` are SYSTEM-owned (the verdict engine / the
-# lifecycle path own them) and a request for either is a 422. Any status in this set means the thesis
-# is already resolved (a second resolve is a 409).
-_USER_RESOLUTIONS = ("played_out", "abandoned")
-_SYSTEM_RESOLUTIONS = ("invalidated", "expired")
-_TERMINAL_STATUSES = (*_USER_RESOLUTIONS, *_SYSTEM_RESOLUTIONS)
-
-
 class ThesisRequest(BaseModel):
     """Body for ``POST /research/thesis``. ``level_price`` is optional at the schema level — the
     per-setup REQUIRED/FORBIDDEN rule is enforced in the route (a 422), never by the schema, so the
@@ -256,44 +217,40 @@ class ReviewRequest(BaseModel):
 
 
 class ResearchRegistry:
-    """Owns the journal store and one ``ResearchMonitor`` per watched ticker.
-
-    Wired to the WatchManager's ``on_engine_created`` hook: each freshly-built engine gets a fresh
-    monitor attached at the engine's observer seam. On a re-watch the engine is rebuilt, so a new
-    monitor replaces the prior one (the prior engine's ``on_status('closed')`` already expired any
-    active thesis during teardown). The routes look a monitor up by ticker to declare/read.
+    """Owns the journal store and the backtest/edge-compute background job managers.
+
+    era-5D J-01 ("The Clean Slate" demolition interlude): this registry previously also attached a
+    ``ResearchMonitor`` to every freshly-built watch engine (the WatchManager's
+    ``on_engine_created`` hook) and ran a startup expiry sweep over stale theses — both were removed
+    along with the journal-era thesis-declaration surfaces, so ``main.py`` no longer wires either
+    one up. ``_monitors`` and the methods below that read it are kept as inert, permanently-empty
+    plumbing this iteration ONLY because ``app/main.py``'s WS ``thesis``/``hint`` frame merge still
+    calls ``projection_for``/``hint_projection_for`` (that merge is explicitly J-02's job to remove,
+    not this iteration's) — both degrade to their own documented ``None`` normal-state answer now
+    that nothing ever populates ``_monitors``.
     """
 
     def __init__(self, store: JournalStore, config: Config) -> None:
         self._store = store
         self._config = config
         self._fingerprint = config.config_fingerprint()
-        self._monitors: dict[str, ResearchMonitor] = {}
-        # The replay-study background-job manager (capability 32, J-60/J-61). Process-scoped: it owns
-        # the cancellable worker threads and runs studies OFF the event loop, persisting through the
-        # SAME single writer queue. One per registry (a backend restart loses in-flight jobs — a study
-        # left ``running`` from a prior process is surfaced honestly, never silently completed).
-        self._study_jobs = StudyJobManager(store, config)
-        # The backtest background-job manager (era-3 capability 4, J-03) — the StudyJobManager
-        # pattern verbatim: cancellable worker threads OFF the event loop, persistence through the
-        # SAME single writer queue, in-flight jobs honestly lost on restart (never silently done).
+        self._monitors: dict[str, object] = {}
+        # The backtest background-job manager (era-3 capability 4, J-03): cancellable worker threads
+        # OFF the event loop, persistence through the SAME single writer queue, in-flight jobs
+        # honestly lost on restart (never silently done).
         self._backtest_jobs = BacktestJobManager(store, config)
         # The edge-report compute manager (era-fast_wall J-04) — a single-flight, cancellable,
         # progress-reporting background job around ``run_strategy_comparison_report``. Unlike
-        # ``_study_jobs``/``_backtest_jobs`` it needs no ``store``/``config`` at construction time
-        # (every ``trigger()`` call takes its store/dataset_store/bar_store/config/cache
-        # explicitly) — process-scoped, in-memory-only bookkeeping, honestly lost on restart, never
-        # a research value.
+        # ``_backtest_jobs`` it needs no ``store``/``config`` at construction time (every
+        # ``trigger()`` call takes its store/dataset_store/bar_store/config/cache explicitly) —
+        # process-scoped, in-memory-only bookkeeping, honestly lost on restart, never a research
+        # value.
         self._edge_report_compute = EdgeReportComputeManager()
 
     @property
     def store(self) -> JournalStore:
         return self._store
 
-    @property
-    def study_jobs(self) -> StudyJobManager:
-        return self._study_jobs
-
     @property
     def backtest_jobs(self) -> BacktestJobManager:
         return self._backtest_jobs
@@ -306,38 +263,16 @@ class ResearchRegistry:
     def config(self) -> Config:
         return self._config
 
-    def on_engine_created(self, ticker: str, engine: object) -> None:
-        """Attach a fresh monitor to a freshly-built engine (the WatchManager hook).
-
-        The monitor is given the engine (so its ``on_status`` can read the terminal ``end_reason``).
-        If a SURVIVING entry-marked active thesis exists for this ticker (it was NOT expired on a
-        prior stop/restart because it carries a real position, J-47), it is OFFERED to the fresh
-        monitor: the monitor adopts it — appending exactly one ``watch_restarted`` gap event and
-        resuming evaluation — only once the first snapshot confirms the new watch's source identity
-        equals the thesis's ``bound_source`` (a mismatch is never adopted)."""
-        monitor = ResearchMonitor(self._store, self._config, ticker)
-        monitor.attach_engine(engine)
-        self._monitors[ticker] = monitor
-        engine.add_observer(monitor)
-        # Offer any surviving entry-marked active thesis for re-attach (source match decided at the
-        # first snapshot). An unmarked active row would already have been expired on the prior stop /
-        # restart sweep, so this only ever finds a genuinely surviving position.
-        surviving = self._store.get_active_thesis(ticker)
-        if surviving is not None and self._store.has_entry_mark(surviving.id):
-            monitor.offer_surviving(surviving)
-
-    def monitor_for(self, ticker: str) -> ResearchMonitor | None:
+    def monitor_for(self, ticker: str) -> object | None:
         return self._monitors.get(ticker)
 
     def projection_for(self, ticker: str) -> dict | None:
-        """The canonical thesis projection for ``ticker`` (``None`` is a normal state).
-
-        The LIVE monitor's projection wins when it serves one (an active live thesis, a resolved
-        ``invalidated`` terminal treatment, or a mismatched-source survivor notice). Otherwise — a
-        stopped/unwatched ticker — a SURVIVING entry-marked active thesis is served from its
-        persisted record via the SAME ``build_projection`` path (data-contract row 15 — never a
-        second computation), flagged ``not_evaluated`` with the backend-owned bound-source notice.
-        ``None`` remains the answer when nothing survives."""
+        """The canonical thesis projection for ``ticker`` — always ``None`` this iteration.
+
+        era-5D J-01: ``_monitors`` is never populated anymore (see the class docstring), so this
+        always falls through to :meth:`_surviving_projection`, itself a permanent ``None`` — kept
+        callable only because ``app/main.py``'s WS ``thesis`` merge (untouched this iteration) still
+        calls it; ``None`` is that key's own documented normal state."""
         monitor = self._monitors.get(ticker)
         if monitor is not None:
             projection = monitor.projection()
@@ -346,72 +281,28 @@ class ResearchRegistry:
         return self._surviving_projection(ticker)
 
     def _surviving_projection(self, ticker: str) -> dict | None:
-        """Serve a surviving entry-marked active thesis (unwatched) as not-evaluated, or ``None``.
-
-        Built from the persisted ``active`` record via the ONE shared ``build_projection`` — no live
-        snapshot (statements read ``not_yet``; an unwatched survivor accrues no new status), the
-        ``not_evaluated`` monitor status, and the backend-owned plain-language notice naming the
-        bound source. A non-entry-marked active row never reaches here (it was expired on stop /
-        restart), so this only ever surfaces a genuinely surviving position."""
-        surviving = self._store.get_active_thesis(ticker)
-        if surviving is None or not self._store.has_entry_mark(surviving.id):
-            return None
-        return build_projection(
-            surviving,
-            self._store.get_actions(surviving.id),
-            config=self._config,
-            snapshot=None,
-            status=surviving.status,
-            verdict="pending",
-            verdict_evidence=(
-                "This thesis carries a recorded entry and survives the stopped watch; it is not "
-                "being evaluated until its source is watched again."
-            ),
-            monitor_status="not_evaluated",
-            monitor_notice=not_evaluated_notice(surviving.bound_source),
-            verdict_events=self._store.verdict_events(surviving.id),
-        )
+        """Always ``None`` this iteration.
+
+        era-5D J-01: this used to serve a surviving entry-marked active thesis (unwatched) via the
+        journal-era ``JournalStore.get_active_thesis``/``has_entry_mark``/``get_actions``/
+        ``verdict_events`` methods and ``monitor.build_projection`` — all deleted whole this
+        iteration (I-2/I-3). Its only remaining caller, :meth:`projection_for`, is itself only
+        reached from ``app/main.py``'s WS ``thesis`` merge (not touched this iteration, J-02's job);
+        ``None`` is that key's own documented normal state, so this never fabricates a value."""
+        return None
 
     def hint_projection_for(self, ticker: str) -> dict | None:
-        """The canonical active-hint projection for ``ticker`` (capability 33, J-65; ``None`` is a NORMAL
-        state). Served from the LIVE monitor's hint engine — a hint exists only on an actively watched
-        ticker (no background detection), so an unwatched / not-watched ticker is always ``None`` (never
-        an error). Both ``GET /research/hints/active`` and the WS ``hint`` key read THIS one method."""
+        """The canonical active-hint projection for ``ticker`` — always ``None`` this iteration.
+
+        era-5D J-01: ``_monitors`` is never populated anymore (see the class docstring), so this
+        always takes its own early-return branch below — kept callable only because
+        ``app/main.py``'s WS ``hint`` merge (untouched this iteration) still calls it; ``None`` is
+        that key's own documented normal state."""
         monitor = self._monitors.get(ticker)
         if monitor is None:
             return None
         return monitor.hint_projection()
 
-    def startup_sweep(self) -> list[str]:
-        """Resolve any thesis left ``active`` in the DB (from a prior process) to ``expired``.
-
-        Each thesis the sweep expires (UNMARKED actives — an entry-marked thesis is exempt and
-        survives) has its execution checks, per-statement FINAL statuses (J-55), and outcome × process
-        grades (J-56) computed ONCE here and persisted on its row — the SAME single functions every
-        other terminal-resolution path calls (capabilities 27/29). An expired unmarked thesis has no
-        marks, so its mark-dependent checks read ``not_applicable`` honestly (never a fabricated
-        pass/fail). The restart-expiry sweep has NO live engine context (the watch that declared the
-        thesis is long gone), so each statement's final status is the explicit ``not_evaluated`` enum
-        (``snapshot=None``) — an honest "no read at the terminal moment", never fabricated. The grades
-        weigh the just-persisted execution checks, so they run after them (resolution is ``expired``)."""
-        expired = self._store.expire_stale_actives(time.time())
-        for thesis_id in expired:
-            try:
-                compute_and_persist_execution_checks(self._store, thesis_id, self._config)
-                compute_and_persist_final_statuses(self._store, thesis_id, None, self._config)
-                compute_and_persist_grades(self._store, thesis_id, "expired", self._config)
-                # Excursions (capability 30, J-58): the restart-expiry sweep has NO in-memory tracker
-                # (the watch that declared the thesis is long gone and tape data is never persisted, so
-                # the price path cannot be reconstructed). Passing ``tracker=None`` persists the
-                # explicit ``not_tracked`` honest marker — never fabricated numbers, never a dishonest
-                # zero. The journal detail then renders an explicit not-tracked notice.
-                compute_and_persist_excursions(self._store, thesis_id, None)
-            except Exception:
-                # A computation failure must not abort the sweep (the resolution already stands); the
-                # key stays honestly absent for that thesis.
-                pass
-        return expired
-
 
 # The app sets this in lifespan (or a test injects one via dependency_overrides). A module-level
 # holder keeps the dependency simple while still overridable.
@@ -445,832 +336,26 @@ def get_watch_manager():
 
 @router.get("/taxonomy")
 def get_taxonomy() -> dict:
-    """The setup catalog, enums, and display copy — the single backend owner of research labels.
-
-    Passes the registry's config (when present) so the additive ``sound_cue`` block carries the
-    config-owned ``sound_cue_cooldown_seconds`` value (serving-only — the cue is never persisted). The
-    taxonomy needs no active watch; with no registry it falls back to the shared default config."""
-    registry = get_registry_or_none()
-    return taxonomy_payload(registry.config if registry is not None else None)
-
-
-@router.get("/analytics")
-def get_analytics(registry: ResearchRegistry = Depends(get_registry)) -> dict:
-    """The segregated journal analytics (capability 31, J-59) — the SINGLE serving path.
-
-    Serves the ``analytics.compute_analytics`` projection VERBATIM (the frontend renders it directly,
-    display-rounding only — no client-side arithmetic). Read-only over persisted rows: partitions
-    keyed by (``data_feed``, ``config_fingerprint``), per ``setup_type`` × ``direction`` groups, with
-    the abandonment bucket always visible and median spread/R beside every +1R figure. NEVER pools
-    across feeds or fingerprints; an empty journal serves an honest empty payload (not an error)."""
-    return compute_analytics(registry.store, registry._config)
-
-
-@router.get("/thesis/active")
-def get_active_thesis(
-    ticker: str, registry: ResearchRegistry = Depends(get_registry)
-) -> dict:
-    """The canonical thesis projection for ``ticker`` (``thesis: null`` is a NORMAL state).
-
-    Reads the SAME ``monitor.projection()`` the WS ``thesis`` key reads, so the two are
-    verbatim-equal by construction (data-contract row 15)."""
-    return {"thesis": registry.projection_for(ticker)}
-
-
-@router.get("/hints/active")
-def get_active_hint(
-    ticker: str, registry: ResearchRegistry = Depends(get_registry)
-) -> dict:
-    """The canonical active setup-forming hint projection for ``ticker`` (capability 33, J-65;
-    ``hint: null`` is a NORMAL state, not an error — a not-watched ticker, an unclear tape, or a tape
-    that has not sustained a pattern past the dwell all read ``null``).
-
-    Reads the SAME ``monitor.hint_projection()`` the WS ``hint`` key reads, so the two are verbatim-equal
-    by construction (data-contract row 22). Computed once server-side; rendered verbatim by the dock."""
-    return {"hint": registry.hint_projection_for(ticker)}
-
-
-@router.get("/hints")
-def list_hints(
-    ticker: str | None = None,
-    limit: int | None = None,
-    offset: int = 0,
-    registry: ResearchRegistry = Depends(get_registry),
-) -> dict:
-    """The persisted hint log (capability 33, J-65; data-contract row 22 log half) — the ONLY serving
-    path for hint-log rows. Reads persisted ``hints`` rows VERBATIM (newest-first) and returns each
-    record's stored ``payload`` directly (no recomputation, no second path — the log record IS the dock
-    projection by construction). Optionally filtered by ``ticker`` (free-form — an unknown ticker matches
-    nothing, never an error).
-
-    Page size is CONFIG-OWNED and serving-only (``hint_log_max``, excluded from ``config_fingerprint``):
-    an omitted / non-positive ``limit`` uses ``hint_log_max``; a larger ``limit`` is CLAMPED down to it
-    (a serving safety bound, never a 422). ``offset`` paginates (a negative offset normalises to 0 — the
-    same lenient convention the journal endpoint uses; malformed non-integer params are a 422 at the
-    schema layer before the route runs)."""
-    config = registry._config
-    if limit is None or limit <= 0:
-        effective_limit = config.hint_log_max
-    else:
-        effective_limit = min(limit, config.hint_log_max)
-    effective_offset = max(offset, 0)
-    records = registry.store.list_hints(
-        ticker=ticker, limit=effective_limit, offset=effective_offset
-    )
-    return {"rows": [r.payload for r in records]}
-
-
-# Valid LIST filter enums (J-51). ``status`` accepts the non-terminal ``active`` plus every terminal
-# status; ``resolution`` accepts the terminal statuses only (a resolution IS a terminal status).
-# Unknown values for any of these → 422 (never silent coercion). ``ticker`` is a free-form symbol, NOT
-# an enum, so it is never validated against a fixed set (an unknown ticker just matches nothing).
-_LIST_STATUSES = ("active", *_TERMINAL_STATUSES)
-_LIST_RESOLUTIONS = _TERMINAL_STATUSES
... [diff_bound] apps/backend/app/research/routes.py: 936 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/setups.py b/apps/backend/app/research/setups.py
index 7dfc154..e435f48 100644
--- a/apps/backend/app/research/setups.py
+++ b/apps/backend/app/research/setups.py
@@ -12,7 +12,8 @@ read-only MCP ``setups`` tool all serve this module's output VERBATIM (single so
 no second computation path, mirroring ``tradability.py``'s own MCP/REST discipline).
 
 Two DIFFERENT "setup" vocabularies exist in this codebase -- READ THIS before touching either
-module. ``research/studies.py`` owns an UNRELATED, pre-existing concept: a live TAPE-ARMING
+module. ``research/backtests.py`` owns an UNRELATED, pre-existing concept (era-5D J-01 relocated it
+there, byte-identically, from the demolished journal-era ``studies.py``): a live TAPE-ARMING
 OCCURRENCE (``level_break`` / ``failed_move_fade`` / ``absorption_reversal`` / ``trend_continuation``)
 checked against the frozen ``TapeEngine``'s live STATE. THIS module's "event" is a completely
 different thing: a STORED 2026-dated 5m bar's OHLC range intersecting a tradable-map BAND, checked
diff --git a/apps/backend/app/research/stance.py b/apps/backend/app/research/stance.py
deleted file mode 100644
index e842c0d..0000000
--- a/apps/backend/app/research/stance.py
+++ /dev/null
@@ -1,603 +0,0 @@
-"""The management-stance evaluator (data-contract row 25, stance half; capability 27 / J-53).
-
-While the user HOLDS a journaled position (an entry-marked, unresolved thesis), the thesis strip
-answers one question — *does the tape still support this position?* — with the **management stance**:
-
-  * ``thesis_intact``       — the latest published verdict is ``confirming``;
-  * ``thesis_weakening``    — the latest published verdict shows the position is NOT confirmed
-                              (``weakening`` / ``rejecting``, or still ``pending`` after the entry —
-                              the honest J-54 case: an entry while pending NEVER reads intact);
-  * ``thesis_invalidated``  — the verdict resolved ``invalidated`` (the J-44 auto-resolve) — a
-                              TERMINAL, dwell-exempt display treatment.
-
-DISCIPLINE (the iter-20 spec + the goal anti-goals):
-  * **Pure derivation, never a record.** The stance is derived EXCLUSIVELY from the latest row-16
-    PUBLISHED verdict — it composes NO new indicator, reads NO engine/feature state directly, and is
-    NEVER persisted (schema stays v7). The research layer stays read-only over the engine.
-  * **No naked stance.** Every stance carries plain-language EVIDENCE. For ``thesis_intact`` /
-    ``thesis_weakening`` the evidence is the published verdict's own evidence (already
-    thesis-attributed, present-tense, descriptive); for the honest ``pending`` case it names the
-    actual verdict ("the tape has not confirmed your thesis since you marked entry"); for
-    ``thesis_invalidated`` it is the offending-print facts the verdict engine recorded.
-  * **Its own dwell, ``invalidated`` dwell-exempt.** The stance publishes through a config-owned,
-    LOGICAL-time dwell (``management_stance_dwell_seconds``) so a single flickering verdict tick never
-    flaps the stance — EXCEPT ``thesis_invalidated``, which is dwell-exempt (it mirrors the hard,
-    dwell-exempt invalidation trigger and is terminal). The dwell is a derivation-timing concern only;
-    the stance is never stored, so the dwell state lives in memory on the monitor.
-  * **Never imperative, never predictive.** Present-tense, factual, thesis-attributed copy — it
-    describes what the tape is doing NOW relative to the declared thesis, never a forecast and never
-    a buy/sell/enter/exit command. The "Descriptive only — not trading advice" register extends here.
-
-The LIVE position readouts that travel WITH the stance (``distance_to_invalidation`` in $ and R, and
-``open_r``) are computed by :func:`compute_position_readouts` from the SAME single ``r_basis()`` helper
-in ``marks.py`` (data-contract row 27) — the stance is its FIFTH registered consumer, never a second
-R formula. ``open_r`` is the current open move in R, SIGNED BY DIRECTION with the SAME convention as
-``marks.py``'s realized move (a move in the thesis's favor is positive).
-"""
-
-from __future__ import annotations
-
-from ..config import Config
-from ..engine.snapshot import EngineSnapshot
-from .marks import r_basis
-from .taxonomy import (
-    STANCE_PENDING_EVIDENCE,
-    checklist_check_caption,
-    checklist_check_label,
-    checklist_nearest_counterevidence,
-    checklist_stance_evidence,
-    checklist_stance_label,
-    stance_for_verdict,
-)
-
-# The published-verdict -> management-stance map (the backend-owned table the spec mandates). The
-# FULL five-verdict mapping lives in ``taxonomy.stance_for_verdict`` (the single copy owner); this
-# module reads it so the mapping + its display copy have ONE home. ``expired`` never reaches the
-# stance (an expired thesis is unmarked or survives not-evaluated — the stance keys are absent then).
-
-
-class StanceEvaluator:
-    """Holds one entry-marked thesis's PUBLISHED management stance and advances it per event (no I/O).
-
-    Constructed when the monitor holds a thesis; advanced in ``on_event`` AFTER the verdict step so it
-    reads the just-published verdict for this snapshot. Owns: the currently published stance, and the
-    dwell tracker (which raw stance is accumulating + the first logical instant it began). Performs NO
-    persistence and reads NOTHING but the published verdict + the snapshot's logical timestamp it is
-    handed — so the engine stays byte-identical with it attached (equivalence anti-goal).
-
-    The stance only MATTERS once an entry mark exists, but the dwell accumulates from the verdict
-    regardless, so by the time the user marks entry the stance is already settled (no artificial
-    "warm-up" gap at the mark). Whether the stance/readout keys are actually SERVED is gated separately
-    in ``build_projection`` (entry-marked AND unresolved AND a live monitor).
-    """
-
-    def __init__(self, dwell_seconds: float) -> None:
-        self._dwell = float(dwell_seconds)
-        # Published stance state. Starts at the pending reading (no published confirmation yet) — an
-        # entry while pending never reads ``thesis_intact`` by construction.
-        self._published: str = "thesis_weakening"
-        self._published_evidence: str = STANCE_PENDING_EVIDENCE
-        self._terminal = False  # thesis_invalidated => frozen terminal stance
-        # Dwell tracker: which raw stance is currently accumulating and the first logical instant it
-        # held. Seeded ``None`` so the first event starts the dwell clock.
-        self._pending_raw: str | None = None
-        self._raw_first_ts: float | None = None
-
-    @property
-    def published_stance(self) -> str:
-        return self._published
-
-    @property
-    def published_evidence(self) -> str:
-        return self._published_evidence
-
-    def advance(
-        self,
-        *,
-        verdict: str,
-        verdict_evidence: str,
-        logical_ts: float,
-        invalidation_evidence: str | None = None,
-    ) -> None:
-        """Advance the published stance against the latest published verdict for this event.
-
-        ``verdict`` is the monitor's CURRENT published verdict (already dwell-gated by the verdict
-        engine); ``verdict_evidence`` is that verdict's plain-language evidence (carried verbatim onto
-        the stance — no naked stance). ``logical_ts`` is the snapshot's logical timestamp (the dwell is
-        logical-time). ``invalidation_evidence`` overrides the evidence on the terminal invalidated
-        stance (the offending-print facts the verdict engine recorded), when available.
-
-        Publication rule: the raw stance derived from the verdict must hold CONTINUOUSLY for the dwell
-        before it is published — EXCEPT ``thesis_invalidated``, which publishes IMMEDIATELY (dwell-exempt)
-        and freezes the stance terminal.
-        """
-        if self._terminal:
-            return
-
-        raw_stance = stance_for_verdict(verdict)
-        raw_evidence = self._evidence_for(raw_stance, verdict, verdict_evidence, invalidation_evidence)
-
-        # thesis_invalidated is dwell-exempt + terminal — publish immediately, freeze.
-        if raw_stance == "thesis_invalidated":
-            self._published = raw_stance
-            self._published_evidence = raw_evidence
-            self._terminal = True
-            return
-
-        # Dwell tracking for the non-terminal stances: reset the clock whenever the raw stance changes,
-        # so a transition publishes only after the raw stance has held continuously for the dwell.
-        if raw_stance != self._pending_raw:
-            self._pending_raw = raw_stance
-            self._raw_first_ts = logical_ts
-
-        held_for = logical_ts - (self._raw_first_ts if self._raw_first_ts is not None else logical_ts)
-        dwell_elapsed = held_for >= self._dwell
-
-        if raw_stance == self._published:
-            # Same stance — keep the evidence current (the verdict evidence may refresh) without a flap.
-            self._published_evidence = raw_evidence
-            return
-        if dwell_elapsed:
-            self._published = raw_stance
-            self._published_evidence = raw_evidence
-
-    @staticmethod
-    def _evidence_for(
-        raw_stance: str,
-        verdict: str,
-        verdict_evidence: str,
-        invalidation_evidence: str | None,
-    ) -> str:
-        """The plain-language evidence carried on a raw stance (no naked stance).
-
-        ``thesis_intact`` / ``thesis_weakening`` carry the published verdict's OWN evidence verbatim
-        (already descriptive + thesis-attributed). The honest ``pending`` case (an entry while pending —
-        no published confirmation) reads its OWN explicit copy naming the actual verdict, never the
-        seeded pending placeholder. ``thesis_invalidated`` carries the offending-print evidence the
-        verdict engine recorded when available, else the published verdict evidence.
-        """
-        if raw_stance == "thesis_invalidated":
-            return invalidation_evidence or verdict_evidence or STANCE_PENDING_EVIDENCE
-        if verdict == "pending" or not verdict_evidence:
-            # Entry while pending: the tape has not confirmed the thesis since the mark — name it
-            # honestly rather than read as "weakening from a confirmation that never happened".
-            return STANCE_PENDING_EVIDENCE
-        return verdict_evidence
-
-
-def compute_position_readouts(
-    *,
-    entry_price: float,
-    invalidation_price: float,
-    direction: str,
-    last: float | None,
-) -> dict:
-    """The LIVE position readouts that travel with the stance (data-contract row 27, consumer #5).
-
-    Computed ONCE here from the SAME single ``marks.r_basis()`` helper (never a second R formula):
-
-      * ``r_basis`` — ``R = |entry − invalidation|`` (the goal-doc R unit). The single basis both the
-        distance-in-R and the open-R divide by.
-      * ``distance_to_invalidation`` — how far the CURRENT last sits from the declared invalidation,
-        in ``dollars`` (signed so a POSITIVE distance means price is on the SAFE side of the
-        invalidation — above it for a long, below it for a short; negative once price has crossed it)
-        and in ``r`` (that dollar distance ÷ the R basis). A move toward the invalidation shrinks it
-        toward 0; a print through it goes negative — the honest "how close is the idea to being wrong".
-      * ``open_r`` — the current open move from entry to the last, in R units, SIGNED BY DIRECTION
-        with the SAME convention as ``marks.py``'s realized move (a long that is up, or a short that is
-        down, is POSITIVE). ``None`` until a ``last`` exists.
-
-    A degenerate ``R == 0`` basis (entry exactly at the invalidation) yields ``None`` for the R-unit
-    figures (never a divide-by-zero / fabricated infinity), while the dollar distance still reads —
-    honest absence over a fabricated number (mirrors ``marks.py``'s realized-R discipline). ``last``
-    is ``None`` only before any trade prints; the R/dollar readouts that need it are then ``None``.
-    """
-    basis = r_basis(entry_price, invalidation_price)
-
-    distance_dollars: float | None = None
-    distance_r: float | None = None
-    open_r: float | None = None
-    if last is not None:
-        # Signed so POSITIVE = the safe side of the invalidation (above it for a long, below for a short).
-        if direction == "long":
-            distance_dollars = last - invalidation_price
-            open_dollars = last - entry_price
-        else:
-            distance_dollars = invalidation_price - last
-            open_dollars = entry_price - last
-        if basis > 0:
-            distance_r = distance_dollars / basis
-            open_r = open_dollars / basis
-
-    return {
-        "r_basis": basis if basis > 0 else None,
-        "distance_to_invalidation": {
-            "dollars": distance_dollars,
-            "r": distance_r,
-        },
-        "open_r": open_r,
-    }
-
-
-# =================================================================================================
-# The ENTRY-CHECKLIST evaluator (data-contract row 25, CHECKLIST half; capability 33 / J-63).
-# =================================================================================================
-#
-# At the moment of decision — an active, evaluated, NOT-yet-entry-marked thesis — the strip shows the
-# ENTRY CHECKLIST: eight named checks each rendering its LIVE measured margin IN ITS OWN UNITS (never a
-# bare boolean), an aggregate STANCE publishing through its own dwell, and a NEAREST-COUNTEREVIDENCE
-# line — all computed ONCE here, server-side.
-#
-# DISCIPLINE (the iter-21 spec + the goal anti-goals):
-#   * **Composed from EXISTING canonical values only.** Every check reads a value the engine/monitor
-#     ALREADY computed (the published verdict, ``event_count`` vs the warm-up floor, ``stream_status``,
-#     the feeder ``delivery_lag_seconds``, the primary-window spread/speed, the declared invalidation,
-#     the recorded ``rule_first_true`` price) — NO new indicator, NO second computation of any contract
-#     value. The reused gates are the classifier's OWN (warm-up floor, stability spread cap in bps, the
-#     trade-speed floor) + the two declaration-time research defaults (invalidation-too-tight multiple,
-#     chase-return threshold) — no new threshold.
-#   * **A live measured margin per check, never a bare boolean.** Each check carries pass/fail PLUS its
-#     measured margin in its own units (a verdict string; events vs floor; the stream status; lag s vs
-#     bound; spread bps vs cap; speed vs floor; distance in spread-multiples vs floor; chase return vs
-#     threshold), formatted ONCE here so the UI renders it verbatim (display rounding only).
-#   * **Read-only over the engine.** The evaluator only READS the snapshot + the published verdict it is
-#     handed — it mutates no engine/feature/classifier state, so engine outputs stay byte-identical
-#     (equivalence anti-goal). Never persisted (schema stays v7).
-#   * **Honest degradation, no frozen green.** Whenever the feed is not live / the tape is not current
-#     (``feed_live`` / ``tape_lag_ok`` fail) the aggregate stance is ``no_fresh_tape`` — a previous
-#     ``conditions_met`` MUST NOT persist over non-live data.
-#   * **Its own dwell.** The aggregate stance publishes through a config-owned LOGICAL-time dwell
-#     (``checklist_stance_dwell_seconds``) so a single flickering check never flaps the stance — EXCEPT
-#     ``no_fresh_tape``/``tape_against``, which publish IMMEDIATELY (honest degradation must never lag
-#     behind a stale feed, and a rejecting verdict is itself already dwell-gated).
-#   * **Never imperative, never predictive.** Present-tense, factual copy describing the tape NOW.
-
-
-def _check(check_id: str, passed: bool, margin: str, distance: float | None) -> dict:
-    """One checklist-check projection row — pass/fail + the live measured margin (its own units).
-
-    ``margin`` is the already-formatted, render-verbatim margin string (the UI does display rounding
-    only, no arithmetic). ``distance`` is the SIGNED normalized distance from this check's boundary
-    (POSITIVE = passing with this much room; NEGATIVE = failing by this much), used ONLY server-side to
-    pick the nearest-counterevidence check — it is NOT a second contract value, just a ranking key. The
-    label + caption come from the taxonomy (the frontend hardcodes none)."""
-    return {
-        "check": check_id,
-        "label": checklist_check_label(check_id),
-        "caption": checklist_check_caption(check_id),
-        "passed": passed,
-        "margin": margin,
-        "_distance": distance,  # server-only ranking key (stripped before serving — see evaluate)
-    }
-
-
-def evaluate_entry_checks(
-    *,
-    snapshot: EngineSnapshot,
-    verdict: str,
-    invalidation_price: float,
-    direction: str,
-    rule_first_true_price: float | None,
-    config: Config,
-) -> list[dict]:
-    """The eight entry-checklist checks, each with its live measured margin, computed ONCE.
-
-    Composes ONLY existing canonical values (single source of truth — never recomputes a contract
-    value): the published ``verdict`` (row 16), ``snapshot.event_count`` vs ``warmup_min_events``,
-    ``snapshot.stream_status`` (row 6), the feeder ``snapshot.delivery_lag_seconds`` (row 14) vs the
-    config bound, the primary-window ``average_spread`` (as bps of ``reference_price`` — the classifier's
-    OWN stability metric) vs ``max_stable_spread_bps``, the primary-window ``trade_speed`` vs
-    ``min_trade_speed``, ``|last − invalidation|`` in spread-multiples vs
-    ``invalidation_too_tight_spread_multiple``, and the directional return from the recorded
-    ``rule_first_true_price`` to the current last vs ``chase_return_threshold`` (anchored at
-    ``rule_first_true`` — NEVER the post-dwell publish).
-
-    Returns the eight ``_check`` rows in display order. Each ``_distance`` is the signed margin from the
-    check's boundary in a comparable, normalized space (used only to rank the nearest counterevidence).
-    """
-    primary = snapshot.primary_features
-    checks: list[dict] = []
-
-    # 1) verdict_confirming — the current published row-16 verdict (margin = the verdict itself). A
-    #    rejecting/invalidated verdict fails it; pending/weakening fail it too (only confirming passes).
-    vc_pass = verdict == "confirming"
-    checks.append(
-        _check(
-            "verdict_confirming",
-            vc_pass,
-            margin=f"verdict {verdict}",
-            distance=1.0 if vc_pass else -1.0,
-        )
-    )
-
-    # 2) warm — events processed vs the classifier's OWN warm-up floor (no new threshold).
-    events = snapshot.event_count
-    floor = config.warmup_min_events
-    warm_pass = events >= floor
-    checks.append(
-        _check(
-            "warm",
-            warm_pass,
-            margin=f"{events}/{floor} events",
-            distance=float(events - floor),
-        )
-    )
-
-    # 3) feed_live — the canonical row-6 stream_status MUST be ``live`` (margin = the actual status).
-    status = snapshot.stream_status
-    live_pass = status == "live"
-    checks.append(
-        _check(
-            "feed_live",
-            live_pass,
-            margin=f"status {status}",
-            distance=1.0 if live_pass else -1.0,
-        )
-    )
-
-    # 4) tape_lag_ok — the feeder-owned row-14 ``delivery_lag_seconds`` vs the config bound (seconds).
-    #    Reads the SAME value the UI lag readout reads. ``None`` (no lag measured yet) is treated as
-    #    NOT current (honest — we cannot assert freshness without a measurement); margin names it.
-    bound = config.delivery_lag_ok_bound_seconds
-    lag = snapshot.delivery_lag_seconds
-    if lag is None:
-        lag_pass = False
-        lag_margin = f"lag — / {bound:.1f}s"
-        lag_distance = -bound  # treated as maximally stale for ranking (no measurement)
-    else:
-        lag_pass = lag <= bound
-        lag_margin = f"lag {lag:.1f}s / {bound:.1f}s"
-        lag_distance = bound - lag
-    checks.append(_check("tape_lag_ok", lag_pass, margin=lag_margin, distance=lag_distance))
-
-    # 5) spread_stable — the average spread within the classifier's OWN stability domain, in bps
-    #    (capability-26 precedent: reuse the classifier gate, no new threshold). The spread is judged
-    #    in bps of the canonical ``reference_price`` (the SAME relative metric the classifier uses);
-    #    with no price basis it falls back to the absolute dollar cap (byte-identical to the classifier).
-    spread = primary.get("average_spread", 0.0)
-    reference_price = primary.get("reference_price", 0.0)
-    if reference_price > 0.0:
-        spread_metric = spread / reference_price * 10000.0  # basis points
-        spread_cap = config.max_stable_spread_bps
-        spread_margin = f"{spread_metric:.1f} / {spread_cap:.1f} bps"
-    else:
-        spread_metric = spread
-        spread_cap = config.max_stable_spread
-        spread_margin = f"{spread_metric:.2f} / {spread_cap:.2f}"
-    spread_pass = spread_metric <= spread_cap
-    checks.append(
-        _check(
-            "spread_stable",
-            spread_pass,
-            margin=spread_margin,
-            distance=spread_cap - spread_metric,
-        )
-    )
-
-    # 6) trade_speed_ok — trade speed at/above the classifier's OWN floor (events/s; no new threshold).
-    speed = primary.get("trade_speed", 0.0)
-    speed_floor = config.min_trade_speed
-    speed_pass = speed >= speed_floor
-    checks.append(
-        _check(
-            "trade_speed_ok",
-            speed_pass,
-            margin=f"{speed:.2f} / {speed_floor:.2f} trades/s",
-            distance=speed - speed_floor,
-        )
-    )
-
-    # 7) invalidation_distance_ok — the distance from the current last to the declared invalidation, in
-    #    SPREAD-MULTIPLES, vs ``invalidation_too_tight_spread_multiple`` (the same too-tight gate, no new
-    #    threshold). A stop comfortably outside spread noise PASSES; one inside the band FAILS. With no
-    #    spread / no last the multiple is unmeasurable — honest fail naming the absence. Direction-aware
-    #    only in the SIGN of "distance" the spec wants: the magnitude |last − invalidation| is what the
... [diff_bound] apps/backend/app/research/stance.py: 209 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/store.py b/apps/backend/app/research/store.py
index 028bbc9..bbccdcf 100644
--- a/apps/backend/app/research/store.py
+++ b/apps/backend/app/research/store.py
@@ -25,6 +25,12 @@ Discipline mandated by the goal doc and re-stated in the iteration spec:
 
 The store is constructed with an explicit DB path (the operator's ``TAPEOLOGY_JOURNAL_DB`` or a
 test's temp path), so persistence is dependency-injected and hermetic in tests.
+
+era-5D J-01 ("The Clean Slate" demolition interlude): the journal-era THESIS/HINT/STUDY read+write
+methods and their record dataclasses were deleted from this class (the ``theses``, ``verdict_events``,
+``hints``, ``actions``, ``studies``, ``study_occurrences`` tables stay — dormant, untouched, per the
+"migrations are history" discipline: no v9, no table drops, no backfill). This store now serves the
+KEPT research surfaces only: backtests, the PnL ledger, and the champion pointer.
 """
 
 from __future__ import annotations
@@ -140,140 +146,6 @@ CREATE TABLE IF NOT EXISTS champion_pointer (
 """
 
 
-@dataclass(frozen=True)
-class ThesisRecord:
-    """One persisted thesis row (read back as an immutable record).
-
-    ``risk_flags`` (capability 26, J-49) is the frozen entry risk-flag set computed ONCE at
-    declaration and stored verbatim — a list of ``{flag, label, evidence, measured}`` entries, or an
-    empty list when assessed-but-nothing-fired. It is ``None`` ONLY for a pre-v4 thesis that was never
-    risk-assessed (NULL in the DB, never backfilled): the projection then OMITS the ``risk_flags`` key
-    entirely rather than read a dishonest empty list. Defaulted ``None`` so every existing call site /
-    fixture stays valid (additive) and so the two honest-omission states (ABSENT vs EMPTY) never
-    collapse."""
-
-    id: str
-    ticker: str
-    setup_type: str
-    direction: str
-    invalidation_price: float
-    level_price: float | None
-    status: str
-    bound_source: str
-    data_feed: str
-    config_fingerprint: str
-    entry_context: dict
-    statements: list[dict]
-    created_logical_ts: float
-    created_wall_ts: float
-    risk_flags: list[dict] | None = None
-    # ``execution_checks`` (capability 27, J-54) is the machine-derived execution-check result —
-    # ``{"checks": [...], "suggested_mistake_tags": [...]}`` — computed ONCE at terminal resolution
-    # from the recorded marks + the append-only timeline + the frozen thesis fields, and stored
-    # verbatim. It is ``None`` until a thesis is resolved with the checks computed (a pre-v5 resolved
-    # thesis stays ``None`` — NULL in the DB, never backfilled): the journal detail then OMITS the
-    # ``execution_checks`` key entirely rather than fabricate a pass/fail at read. Defaulted ``None``
-    # so every existing call site / fixture stays valid (additive) and the two honest-omission states
-    # (ABSENT vs computed) never collapse.
-    execution_checks: dict | None = None
-    # --- v6 review-pillar fields (J-55 / J-56 / J-57), all persisted ONCE at their defining moment --
-    # ``statement_final_statuses`` (J-55) is the list of per-statement FINAL statuses recorded ONCE at
-    # terminal resolution — one ``{status}`` entry per frozen statement, in statement order (the
-    # status is the monitor's last live evaluation at the terminal moment, or an explicit
-    # ``not_evaluated`` enum where no live context exists — e.g. the restart-expiry sweep). It is
-    # ``None`` until recorded (a pre-v6 resolution stays ``None`` — NULL in the DB, never backfilled):
-    # the journal detail then renders the frozen statements WITHOUT a final-status badge (honest
-    # omission). The frozen ``statements`` JSON itself is NEVER mutated — this is an additive parallel.
-    statement_final_statuses: list[dict] | None = None
-    # ``grades`` (J-56) is the outcome × process grade — ``{"outcome", "process", "process_evidence"}``
-    # — computed ONCE at terminal resolution from the persisted execution checks + the frozen risk
-    # flags + the resolution, and stored verbatim. ``None`` until computed (a pre-v6 resolution stays
-    # ``None``): the journal detail/list then OMIT the grade keys (honest omission). ENUM labels only,
-    # never a numeric score.
-    grades: dict | None = None
-    # ``review_tags`` / ``review_note`` / ``reviewed`` (J-57) are the user-CONFIRMED review, recorded
-    # ONCE by ``POST …/review``. ``reviewed`` is ``False`` until the user saves a review; ``review_tags``
-    # is the list of confirmed mistake-tag ids (distinct from the machine-SUGGESTED tags on
-    # ``execution_checks``) and ``review_note`` the optional free text (required only for ``other``).
-    review_tags: list[str] | None = None
-    review_note: str | None = None
-    reviewed: bool = False
-    # ``excursions`` (capability 30, J-58) is the per-horizon excursion record —
-    # ``{"tracked": bool, "populations": {confirmation?: {...}, entry?: {...}}}`` — measured ONCE at
-    # the terminal resolution / stream-end (the proven persist-once seam) from the in-memory price
-    # path and stored verbatim. The two populations (confirmation-anchored / entry-anchored) are
-    # segregated and never pooled. It is ``None`` until measured (a pre-v7 resolution stays ``None`` —
-    # NULL in the DB, never backfilled): the journal detail then OMITS the ``excursions`` key entirely
-    # rather than fabricate numbers at read. A ``{"tracked": False}`` record is the explicit honest
-    # marker persisted where no tracker existed at the persist moment (the restart-expiry sweep).
-    # Defaulted ``None`` so every existing call site / fixture stays valid (additive) and the
-    # honest-omission states (ABSENT vs measured vs not-tracked) never collapse.
-    excursions: dict | None = None
-
-
-@dataclass(frozen=True)
-class ActionRecord:
-    """One persisted action mark (entry | exit) — recorded verbatim from the user (no inferred fill).
-
-    ``price`` is recorded EXACTLY as the user submitted it (never an inferred/simulated fill);
-    ``spread_at_mark`` is the snapshot's spread taken ONCE at recording (a moment value — ``None``
-    when there was no quote — never recomputable later). The entry-mark UI is J-52; this record's
-    ``spread_at_mark`` column arrives with the v2 → v3 migration. ``spread_at_mark`` is defaulted so
-    every existing call site / fixture stays valid (additive) and a pre-v3 row reads ``None``."""
-
-    id: str
-    thesis_id: str
-    kind: str
-    price: float
-    logical_ts: float
-    wall_ts: float
-    spread_at_mark: float | None = None
-
-
-@dataclass(frozen=True)
-class VerdictEventRecord:
-    thesis_id: str
-    logical_ts: float
-    wall_ts: float
-    verdict: str
-    evidence: str
-    tape_state: str | None
-    confidence: float | None
-    last: float | None
-    # The verdict-transition timing record (capability 24): the first logical instant + price at which
-    # the RAW rule began holding, distinct from ``logical_ts`` (the publication instant, after dwell).
-    # Defaulted ``None`` so every existing call site / fixture stays valid (additive) and so the
-    # initial ``pending`` / lifecycle rows (no raw rule) record no spurious timing.
-    rule_first_true_ts: float | None = None
-    rule_first_true_price: float | None = None
-
-
-@dataclass(frozen=True)
-class StudyRecord:
-    """One persisted replay-study row (capability 32, J-60/J-61/J-62) — read back as an immutable record.
-
-    The ``studies`` + ``study_occurrences`` tables exist from schema v1 in a PAYLOAD-BLOB shape, so a
-    study's ENTIRE state (status, stamps, seed, progress, create params, and — at completion /
-    cancellation — its occurrence rows + aggregates + null baseline) lives in the ``studies.payload``
-    JSON. No schema bump is needed (schema stays v7): the blob absorbs the record. The study runner is
-    the single owner that builds the payload; the routes serve it VERBATIM (never recomputed at read).
-
-    Honesty stamps the runner writes into ``payload`` at creation (capability 32 / never-pool): the
-    bound ``source`` descriptor, the ``data_feed`` (``sip | iex | sim``), the ``config_fingerprint``
-    over the entire frozen config, and the ``null_baseline_seed`` — so a study reproduces exactly and
-    is never silently compared across feeds or fingerprints.
-
-    ``id`` is the study id (a uuid). ``payload`` is the full served projection. ``created_wall_ts`` is
-    the creation instant. The occurrence rows are ALSO written verbatim into ``study_occurrences`` at
-    the persist-once moment (first writes to that table) so both tables are populated; the canonical
-    served result remains the ``studies.payload`` (one source of truth — the occurrence rows mirror it,
-    never a second computation)."""
-
-    id: str
-    payload: dict
-    created_wall_ts: float
-
-
 @dataclass(frozen=True)
 class BacktestRecord:
     """One persisted backtest row (era-3 capability 4, J-03) — read back as an immutable record.
@@ -294,29 +166,6 @@ class BacktestRecord:
     created_wall_ts: float
 
 
-@dataclass(frozen=True)
-class HintRecord:
-    """One persisted setup-forming hint row (capability 33, J-65) — read back as an immutable record.
-
-    The ``hints`` table exists from schema v1 in a PAYLOAD-BLOB shape (``id, ticker, payload,
-    created_wall_ts``), so a hint's ENTIRE state lives in the ``hints.payload`` JSON. No schema bump is
-    needed (schema stays v7): the blob absorbs the record. The hint engine (``app/research/hints.py``,
-    driven by the research monitor) is the single owner that builds the payload ONCE at fire; the routes
-    + the WS ``hint`` key serve it VERBATIM (never recomputed at read).
-
-    The ``payload`` carries: the pattern id, the plain-language evidence (with measured values), the
-    setup-type context + direction, the baseline citation, the honesty stamps (bound ``source``, the
-    ``data_feed`` ``sip | iex | sim``, the ``config_fingerprint`` over the entire frozen config), the
-    logical + wall timestamps, and — once the user completes a declaration from this hint — a
-    ``declared_from`` linkage (the created thesis id). Clearing an ACTIVE hint never touches this
-    persisted record; the log is the record."""
-
-    id: str
-    ticker: str
-    payload: dict
-    created_wall_ts: float
-
-
 @dataclass(frozen=True)
 class PnlLedgerRecord:
     """One persisted PnL-ledger row (era-3 capability 5, J-04) — read back as an immutable record.
@@ -705,534 +554,6 @@ class JournalStore:
             raise payload
         return payload
 
-    # --- writes (theses + verdict_events only this iteration) ------------------------------------
-    @staticmethod
-    def _encode_risk_flags(risk_flags: list[dict] | None) -> str | None:
-        """Serialize the frozen risk-flag list to JSON, preserving the ABSENT/EMPTY distinction.
-
-        ``None`` (never assessed) is stored as SQL ``NULL`` so the projection can OMIT the key; an
-        empty list (assessed, nothing fired) is stored as ``"[]"`` so it reads back as an explicit
-        empty list. The two honest-omission states never collapse."""
-        return None if risk_flags is None else json.dumps(risk_flags)
-
-    @staticmethod
-    def _encode_execution_checks(execution_checks: dict | None) -> str | None:
-        """Serialize the execution-check result to JSON, preserving the ABSENT/computed distinction.
-
-        ``None`` (never computed — a pre-v5 resolution, or a thesis not yet resolved) is stored as SQL
-        ``NULL`` so the journal detail can OMIT the key; a computed dict is stored as JSON so it reads
-        back verbatim. The two honest-omission states never collapse (absent ≠ a computed-but-empty
-        result)."""
-        return None if execution_checks is None else json.dumps(execution_checks)
-
-    @staticmethod
-    def _encode_json_or_none(value: object | None) -> str | None:
-        """Serialize a JSON-able value to a string, preserving the ABSENT (NULL) state.
-
-        Used for the v6 ``statement_final_statuses`` / ``grades`` / ``review_tags`` columns — ``None``
-        (never recorded/computed) stays SQL ``NULL`` so the journal surfaces OMIT the key; a value
-        (incl. an empty list) is stored as JSON so it reads back verbatim. The ABSENT vs
-        recorded-but-empty states never collapse (the established honest-omission discipline)."""
-        return None if value is None else json.dumps(value)
-
-    def insert_thesis(self, record: ThesisRecord) -> None:
-        def _fn(conn: sqlite3.Connection) -> None:
-            conn.execute(
-                """
-                INSERT INTO theses (
-                    id, ticker, setup_type, direction, invalidation_price, level_price,
-                    status, bound_source, data_feed, config_fingerprint,
-                    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags,
-                    execution_checks, statement_final_statuses, grades, review_tags, review_note,
-                    reviewed, excursions
-                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
-                """,
-                (
-                    record.id,
-                    record.ticker,
-                    record.setup_type,
-                    record.direction,
-                    record.invalidation_price,
-                    record.level_price,
-                    record.status,
-                    record.bound_source,
-                    record.data_feed,
-                    record.config_fingerprint,
-                    json.dumps(record.entry_context),
-                    json.dumps(record.statements),
-                    record.created_logical_ts,
-                    record.created_wall_ts,
-                    self._encode_risk_flags(record.risk_flags),
-                    self._encode_execution_checks(record.execution_checks),
-                    self._encode_json_or_none(record.statement_final_statuses),
-                    self._encode_json_or_none(record.grades),
-                    self._encode_json_or_none(record.review_tags),
-                    record.review_note,
-                    1 if record.reviewed else 0,
-                    self._encode_json_or_none(record.excursions),
-                ),
-            )
-
-        self._do_write(_fn)
-
-    def insert_thesis_with_event(
-        self, thesis: ThesisRecord, event: VerdictEventRecord
-    ) -> None:
-        """Declare a thesis ATOMICALLY: the thesis row + its initial verdict event in ONE writer
-        transaction (single ``BEGIN IMMEDIATE`` … commit, owned by the writer worker).
-
-        A failure at any point rolls BOTH back — so a thesis row without its initial timeline event
-        can no longer exist (the iter-4 two-transaction defect). This is the only declaration path the
-        route uses; the standalone ``insert_thesis`` / ``append_verdict_event`` remain for the
-        lifecycle/test paths that legitimately write one row at a time. The append-only guarantee is
-        preserved (this only INSERTs; it never updates/deletes a verdict row)."""
-
-        def _fn(conn: sqlite3.Connection) -> None:
-            conn.execute(
-                """
-                INSERT INTO theses (
-                    id, ticker, setup_type, direction, invalidation_price, level_price,
-                    status, bound_source, data_feed, config_fingerprint,
-                    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags,
-                    execution_checks, statement_final_statuses, grades, review_tags, review_note,
-                    reviewed, excursions
-                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
-                """,
-                (
-                    thesis.id,
-                    thesis.ticker,
-                    thesis.setup_type,
-                    thesis.direction,
-                    thesis.invalidation_price,
-                    thesis.level_price,
-                    thesis.status,
-                    thesis.bound_source,
-                    thesis.data_feed,
-                    thesis.config_fingerprint,
-                    json.dumps(thesis.entry_context),
-                    json.dumps(thesis.statements),
-                    thesis.created_logical_ts,
-                    thesis.created_wall_ts,
-                    self._encode_risk_flags(thesis.risk_flags),
-                    self._encode_execution_checks(thesis.execution_checks),
-                    self._encode_json_or_none(thesis.statement_final_statuses),
-                    self._encode_json_or_none(thesis.grades),
-                    self._encode_json_or_none(thesis.review_tags),
-                    thesis.review_note,
-                    1 if thesis.reviewed else 0,
-                    self._encode_json_or_none(thesis.excursions),
-                ),
-            )
-            conn.execute(
-                """
-                INSERT INTO verdict_events (
-                    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
-                    rule_first_true_ts, rule_first_true_price
-                ) VALUES (?,?,?,?,?,?,?,?,?,?)
-                """,
-                (
-                    event.thesis_id,
-                    event.logical_ts,
-                    event.wall_ts,
-                    event.verdict,
-                    event.evidence,
-                    event.tape_state,
-                    event.confidence,
-                    event.last,
-                    event.rule_first_true_ts,
-                    event.rule_first_true_price,
-                ),
-            )
-
-        self._do_write(_fn)
-
-    def append_verdict_event(self, record: VerdictEventRecord) -> None:
-        """Append ONE verdict event. There is deliberately NO update/delete counterpart — the
-        timeline is append-only at the repository level (capability 28 / journal-integrity).
-
-        A config-owned capacity CAP (``verdict_timeline_cap``) bounds an unbounded live watch: once a
-        thesis exceeds the cap, the OLDEST surviving rows are pruned. This is capacity management, NOT
-        an edit of a retained row — the surviving rows are never rewritten, so the append-only
-        guarantee (no update/delete method exists) holds: there is no way to change what a kept row
-        says. A pruned row is gone, never altered."""
-
-        def _fn(conn: sqlite3.Connection) -> None:
-            conn.execute(
-                """
-                INSERT INTO verdict_events (
-                    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
-                    rule_first_true_ts, rule_first_true_price
-                ) VALUES (?,?,?,?,?,?,?,?,?,?)
-                """,
-                (
-                    record.thesis_id,
-                    record.logical_ts,
-                    record.wall_ts,
-                    record.verdict,
-                    record.evidence,
-                    record.tape_state,
-                    record.confidence,
-                    record.last,
-                    record.rule_first_true_ts,
-                    record.rule_first_true_price,
-                ),
-            )
-            self._prune_timeline(conn, record.thesis_id)
-
-        self._do_write(_fn)
-
-    def _prune_timeline(self, conn: sqlite3.Connection, thesis_id: str) -> None:
-        """Enforce the config-owned per-thesis timeline cap by deleting the OLDEST rows over the cap.
-
-        Runs INSIDE the same writer-queue transaction as the append (so the cap is maintained
-        atomically off any hot path). Deletes only the oldest excess rows (by ascending ``id`` =
-        insertion order); the kept rows are untouched. Capacity bound only — distinct from any
-        update/delete of a RETAINED row, which the repository deliberately does not expose."""
-        cap = self._config.verdict_timeline_cap
-        count = conn.execute(
-            "SELECT COUNT(*) FROM verdict_events WHERE thesis_id=?", (thesis_id,)
-        ).fetchone()[0]
-        if count <= cap:
-            return
-        conn.execute(
-            """
-            DELETE FROM verdict_events
-            WHERE id IN (
-                SELECT id FROM verdict_events WHERE thesis_id=? ORDER BY id ASC LIMIT ?
-            )
-            """,
-            (thesis_id, count - cap),
-        )
-
-    def resolve_thesis(self, thesis_id: str, status: str) -> None:
-        """Set a thesis's terminal status (played_out | abandoned | invalidated | expired).
-
-        This updates the THESES row only — it is NOT an edit of any verdict_events row (those stay
-        append-only); the resolution's timeline entry is a separately APPENDED verdict event. Used
-        by the lifecycle-honesty path (expired-on-stop) and the startup sweep."""
-
-        def _fn(conn: sqlite3.Connection) -> None:
-            conn.execute(
... [diff_bound] apps/backend/app/research/store.py: 758 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/studies.py b/apps/backend/app/research/studies.py
deleted file mode 100644
index 7a88fa3..0000000
--- a/apps/backend/app/research/studies.py
+++ /dev/null
@@ -1,865 +0,0 @@
-"""Replay-study runner + cancellable background-job manager (capability 32, J-60/J-61/J-62).
-
-THE single owner of replay studies. A study runs the EXISTING setup grammar over an explicitly
-chosen source + past window as an **unpaced offline replay through a FRESH ``TapeEngine``** — the
-exact fixture-replay pattern of ``test_real_data_classify.py`` / ``test_dense_replay_gate.py`` —
-attaching ONLY via the engine's existing observer seam. It is **read-only over the engine**: it never
-mutates engine / classifier / feature / history state, so the same stream yields byte-identical
-snapshots with the study observer attached or absent (the observer-equivalence anti-goal, J-68).
-
-What the runner does, and the discipline it rides (every clause is an anti-goal or a spec line):
-
-  * **State-native auto-arming** for ``absorption_reversal`` / ``trend_continuation`` from EXISTING
-    engine states only — sustained matching ABSORPTION (the premise) for absorption_reversal,
-    sustained matching CONTROL for trend_continuation — each gated by a config-owned sustain + a
-    config-owned cooldown so one premise phase arms ONE occurrence (never one per tick). No new
-    indicator, no new threshold in code: ``study_arm_sustain_seconds`` / ``study_arm_cooldown_seconds``
-    are config-owned and IN ``config_fingerprint``.
-
-  * **Level setups require a user-supplied level** (``level_break`` / ``failed_move_fade``): the study
-    is stamped ``hindsight_level`` and EXCLUDED from any cross-study aggregate (enforced here + tested);
-    a level setup with no level is a 422 at the route (never a guessed level). With a level supplied,
-    arming latches on the cross of that level + matching control (the existing verdict-engine semantics).
-
-  * **Each armed occurrence runs the EXISTING per-setup verdict rule table** (``verdict.VerdictEvaluator``
-    — no new rule, no new indicator) from a FRESH evaluator armed at the occurrence, recording its
-    per-occurrence verdict summary (did it ever publish ``confirming`` / ``rejecting`` / ``invalidated``).
-
-  * **Deterministic occurrence-R (the named design decision — documented in the dev handoff):** an
-    auto-armed occurrence has no user-typed invalidation, so its R basis is derived DETERMINISTICALLY
-    from existing engine values at the arm instant — a synthetic invalidation placed
-    ``study_occurrence_r_spread_multiple × spread_at_arm`` (floored at ``study_occurrence_r_floor``) on
-    the ADVERSE side of the arm price. ``R = |arm_price − synthetic_invalidation|`` then flows through
-    the EXISTING ``marks.r_basis`` helper + the ``excursions.ExcursionTracker`` ternary/horizon
-    machinery (``excursion_horizons_seconds``) — the study is a REGISTERED CONSUMER of the one R
-    formula, never a second one. IDENTICAL for setup and null arms. NEVER fitted.
-
-  * **Seeded random-arm-time null baseline:** ``study_null_arm_count`` arm times drawn from a recorded
-    seed over the SAME window, SAME direction, SAME R definition, SAME horizons. The seed is persisted
-    on the study record so the baseline reproduces exactly. ONE replay pass serves BOTH populations —
-    the observer records the full snapshot path in memory ONCE, and every arm (setup or null) measures
-    its excursions against that recorded path (N engine re-replays would blow the CI budget). No tape
-    data is persisted (in-job memory only — the persisted study holds R-unit summaries, never prints).
-
-  * **Excursions per occurrence:** arm-anchored, per config horizon, first-touch in logical time;
-    horizons cut short by window end are flagged ``truncated`` and counted separately — never dropped,
-    never extrapolated (the existing ``ExcursionTracker.truncate_open`` at window end).
-
-  * **Cancellable background jobs:** ``queued | running | done | cancelled | failed`` with progress;
-    cancellation honored between events; cancelled → explicit ``cancelled`` with partial-marked results;
-    failed (no data / provider error) → explicit error, never an empty success. The replay runs OFF
-    the event loop (a worker thread), and ALL SQLite writes go through the existing single writer queue.
-
-  * **Honesty stamps + never-pool:** every study carries its bound source, ``data_feed``,
-    ``config_fingerprint``, and the baseline seed; aggregates render with n + the descriptive
-    measurement framing; groups below the config minimum reuse the insufficient-sample marker. Results
-    are NEVER pooled across feed or fingerprint (each study IS one feed + one fingerprint).
-"""
-
-from __future__ import annotations
-
-import random
-import threading
-import time
-import uuid
-from dataclasses import dataclass
-from typing import Callable
-
-from ..config import Config
-from ..engine.snapshot import EngineSnapshot
-from ..engine.tape_engine import TapeEngine
-from ..providers.base import Event
-from ..providers.historical import HistoricalProvider
-from ..providers.simulated import SIM_SCENARIOS, SimulatedProvider, is_sim_ticker
-from .excursions import (
-    ExcursionTracker,
-    TERNARY_MINUS,
-    TERNARY_NEITHER,
-    TERNARY_PLUS,
-)
-from .feed_basis import data_feed_for_scenario
-from .marks import r_basis as _r_basis
-from .store import JournalStore, StudyRecord
-from .verdict import VerdictEvaluator
-
-# --- study status enum (capability 32 / J-61 — each status its OWN explicit copy, iter-15 lesson) ---
-STATUS_QUEUED = "queued"
-STATUS_RUNNING = "running"
-STATUS_DONE = "done"
-STATUS_CANCELLED = "cancelled"
-STATUS_FAILED = "failed"
-TERMINAL_STATUSES = frozenset({STATUS_DONE, STATUS_CANCELLED, STATUS_FAILED})
-
-# The two state-native auto-arming setups (no user level). The two level setups
-# (``level_break`` / ``failed_move_fade``) require a user-supplied level (hindsight) — handled below.
-_STATE_NATIVE_SETUPS = frozenset({"absorption_reversal", "trend_continuation"})
-_LEVEL_SETUPS = frozenset({"level_break", "failed_move_fade"})
-
-# The two source kinds the study runner accepts (validated at the route): a reference/sim/historical
-# replay. ``reference`` is the committed PG SIP fixture (no credentials). ``sim`` is a seeded sim
-# scenario. ``historical`` is an arbitrary symbol + past window through the EXISTING fetch path.
-SOURCE_REFERENCE = "reference"
-SOURCE_SIM = "sim"
-SOURCE_HISTORICAL = "historical"
-
-# The committed reference window — the PG SIP fixture (the iter-17 capability-34 fixture; this is its
-# second consumer). Loadable without credentials. The id the create form's quick-pick sends.
-REFERENCE_SOURCE_ID = "PG_SIP_REFERENCE"
-
-# How often (in processed events) a running study refreshes its persisted progress — throttled so the
-# progress write is never a hot path (the replay processes thousands of events; a write every event
-# would hammer the writer queue). A whole-number internal cadence, not a tuned research value.
-_PROGRESS_EVERY = 250
-
-# How often the cancellation flag is polled during the replay (every event is cheap — a bool read).
-# Cancellation is honored between events (cooperative), so a long study stops promptly on cancel.
-
-
-@dataclass
-class _PathPoint:
-    """One recorded snapshot-path point (logical ts + last + spread + the canonical tape state). Tape
-    data lives ONLY here in memory during the job — never persisted (the persistence-scope anti-goal).
-    A lightweight stand-in that ``ExcursionTracker`` can consume (it reads ``.timestamp`` / ``.last`` /
-    ``.spread``); ``tape_state`` is the engine's single-source-of-truth read at the tick, used by the
-    state-native arming + the per-occurrence verdict summary (read-only — never recomputed)."""
-
-    timestamp: float
-    last: float | None
-    spread: float | None
-    tape_state: str
-
-
-@dataclass
-class _Occurrence:
-    """One armed occurrence (setup OR null) before its excursions are measured."""
-
-    population: str            # "setup" | "null"
-    arm_logical_ts: float
-    arm_price: float
-    spread_at_arm: float | None
-    invalidation_price: float  # the synthetic deterministic invalidation (adverse side)
-    r_basis: float
-
-
-class StudyCancelled(Exception):
-    """Raised inside the replay loop when a cancellation is observed (caught by the runner)."""
-
-
-class StudyFailed(Exception):
-    """Raised when a study cannot produce a result (no data / provider error / empty window)."""
-
-
-class _PathObserver:
-    """The engine observer that records the snapshot path for ONE study replay (read-only).
-
-    Attached at the engine's existing observer seam. ``on_event`` appends a lightweight path point and
-    feeds the live state machine that decides the state-native SETUP arms; ``on_status`` is a no-op
-    here (the study replay is an offline finite stream — there is no live status flip to react to). The
-    observer NEVER mutates the engine (it only reads the handed snapshot), so the engine stays
-    byte-identical with it attached (J-68)."""
-
-    def __init__(self) -> None:
-        self.path: list[_PathPoint] = []
-
-    def on_event(self, event: Event, snapshot: EngineSnapshot) -> None:
-        self.path.append(
-            _PathPoint(
-                timestamp=snapshot.timestamp,
-                last=snapshot.last,
-                spread=snapshot.spread,
-                tape_state=snapshot.tape_state,
-            )
-        )
-
-    def on_status(self, status: str) -> None:  # offline finite stream — no live status to react to
-        return
-
-
-def _provider_for_source(
-    *,
-    source_kind: str,
-    source_id: str,
-    config: Config,
-    historical_fetch: Callable[[], object] | None,
-):
-    """Build the replay provider for a study source through an EXISTING seam (never a new path).
-
-    Returns ``(provider, source_descriptor)``. Raises ``StudyFailed`` for an empty/absent window so the
-    job resolves to an explicit ``failed`` (never an empty success). The historical path is injected as
-    a callable (``historical_fetch``) that returns a ``HistoricalWindow`` via the EXISTING adapter fetch
-    — so credentials/timeouts/no-data are handled by the same explicit-error machinery the watch path
-    uses (a credentialless arbitrary-window study fails explicitly, never fixture-substituted)."""
-    if source_kind == SOURCE_REFERENCE:
-        # The committed PG SIP fixture — loadable WITHOUT credentials. Imported lazily (the loader
-        # lives in the test fakes module on the test path; the committed fixture is the canonical one).
-        window = _load_reference_window()
-        if window is None or not window.trades:
-            raise StudyFailed("the committed reference window is unavailable")
-        provider = HistoricalProvider(window.symbol, window, f"historical {window.symbol} reference")
-        return provider, provider.scenario
-    if source_kind == SOURCE_SIM:
-        if not is_sim_ticker(source_id):
-            raise StudyFailed(f"unknown sim scenario '{source_id}'")
-        provider = SimulatedProvider(source_id, SIM_SCENARIOS[source_id])
-        return provider, provider.scenario
-    if source_kind == SOURCE_HISTORICAL:
-        if historical_fetch is None:
-            raise StudyFailed("no historical fetch available for this study")
-        window = historical_fetch()  # may raise the existing explicit vendor errors — never fabricated
-        if window is None or not getattr(window, "trades", None):
-            raise StudyFailed("no data for that window")
-        descriptor = f"historical {source_id}"
-        provider = HistoricalProvider(source_id, window, descriptor)
-        return provider, provider.scenario
-    raise StudyFailed(f"unknown source kind '{source_kind}'")
-
-
-def _load_reference_window():
-    """Load the committed PG SIP reference fixture without credentials. The fixture path mirrors the
-    capability-34 gate's committed file (one fixture, two consumers). Returns the ``HistoricalWindow``
-    or ``None`` if absent (the caller raises ``StudyFailed`` — never a synthetic stand-in)."""
-    import json
-    from pathlib import Path
-
-    from ..providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
-
-    fixture = (
-        Path(__file__).resolve().parents[2]
-        / "tests"
-        / "fixtures"
-        / "alpaca"
-        / "PG_20260609_170000_171000_sip.json"
-    )
-    if not fixture.exists():
-        return None
-    data = json.loads(fixture.read_text())
-    trades = tuple(RawTrade(t["epoch"], t["price"], t["size"]) for t in data["trades"])
-    quotes = tuple(
-        RawQuote(q["epoch"], q["bid"], q["ask"], q["bid_size"], q["ask_size"])
-        for q in data["quotes"]
-    )
-    return HistoricalWindow(data["symbol"], trades, quotes)
-
-
-def _control_state(direction: str) -> str:
-    return "buyer_control" if direction == "long" else "seller_control"
-
-
-def _absorption_state(direction: str) -> str:
-    # absorption_reversal premise: long expects sellers absorbed at the bid (bid_absorption);
-    # short expects buyers absorbed at the ask (ask_absorption).
-    return "bid_absorption" if direction == "long" else "ask_absorption"
-
-
-def _premise_state(setup_type: str, direction: str) -> str:
-    """The EXISTING engine tape state whose SUSTAINED presence arms a state-native occurrence.
-
-    absorption_reversal arms on sustained matching ABSORPTION (the premise — the reversal itself is
-    then judged by the per-occurrence verdict evaluator). trend_continuation arms on sustained matching
-    CONTROL. Composed ONLY of existing states (no new indicator)."""
-    if setup_type == "absorption_reversal":
-        return _absorption_state(direction)
-    return _control_state(direction)  # trend_continuation
-
-
-def _synthetic_invalidation(arm_price: float, spread: float | None, direction: str, config: Config) -> float:
-    """The deterministic occurrence-R synthetic invalidation (the named design decision).
-
-    A synthetic invalidation placed ``study_occurrence_r_spread_multiple × spread`` (floored at
-    ``study_occurrence_r_floor``) on the ADVERSE side of the arm price (below for a long, above for a
-    short). IDENTICAL for setup and null arms; derived ONLY from existing engine values at the arm
-    instant (arm price + arm-instant spread); NEVER fitted. R is then ``|arm_price − this|`` via the
-    shared ``marks.r_basis`` helper."""
-    s = spread if spread is not None and spread > 0 else 0.0
-    band = max(s * config.study_occurrence_r_spread_multiple, config.study_occurrence_r_floor)
-    return arm_price - band if direction == "long" else arm_price + band
-
-
-def _arm_occurrence(
-    population: str,
-    *,
-    arm_logical_ts: float,
-    arm_price: float,
-    spread_at_arm: float | None,
-    direction: str,
-    config: Config,
-) -> _Occurrence:
-    invalidation = _synthetic_invalidation(arm_price, spread_at_arm, direction, config)
-    # R basis via the ONE shared helper (row 27 / capability 30) — never a second formula.
-    r = _r_basis(arm_price, invalidation)
-    return _Occurrence(
-        population=population,
-        arm_logical_ts=arm_logical_ts,
-        arm_price=arm_price,
-        spread_at_arm=spread_at_arm,
-        invalidation_price=invalidation,
-        r_basis=r,
-    )
-
-
-def _measure_excursions(
-    occ: _Occurrence,
-    path: list[_PathPoint],
-    direction: str,
-    config: Config,
-) -> dict:
-    """Measure ONE occurrence's per-horizon excursions against the recorded snapshot path (J-58
-    machinery, one replay pass). Arms an ``ExcursionTracker`` at the occurrence and advances it over
-    every recorded path point at/after the arm; truncates open horizons at the window end. Returns the
-    per-horizon ternary outcomes + truncation flags + running MFE/MAE (R units), the registered
-    consumer of the one excursion formula — never a second one."""
-    tracker = ExcursionTracker(
-        invalidation_price=occ.invalidation_price, direction=direction, config=config
-    )
-    # Arm the entry population at the occurrence (the entry-anchored arm is exactly the study's
-    # arm-anchored excursion — same single helper as a journaled entry mark).
-    tracker.arm_entry(
-        logical_ts=occ.arm_logical_ts,
-        wall_ts=0.0,  # offline study — logical anchor only (no true-clock display for an occurrence)
-        reference_price=occ.arm_price,
-        spread_at_mark=occ.spread_at_arm,
-    )
-    for point in path:
-        if point.timestamp < occ.arm_logical_ts:
-            continue
-        tracker.on_event(point)  # _PathPoint quacks like a snapshot (.timestamp/.last/.spread)
-    # The offline window ends here — every still-open horizon is TRUNCATED at the window end (never
-    # extrapolated past the data), exactly the live stream-end semantics.
-    tracker.truncate_open()
-    record = tracker.to_record()
-    entry_pop = record["populations"].get("entry", {})
-    return {
-        "arm_logical_ts": occ.arm_logical_ts,
-        "arm_price": round(occ.arm_price, 4),
-        "spread_at_arm": occ.spread_at_arm,
-        "invalidation_price": round(occ.invalidation_price, 4),
-        "r_basis": round(occ.r_basis, 4),
-        "horizons": entry_pop.get("horizons", []),
-    }
-
-
-def _aggregate_horizons(occurrence_rows: list[dict], config: Config) -> list[dict]:
-    """Aggregate a population's per-horizon ternary distribution (the side-by-side comparison).
-
-    For each configured horizon: count ``+1R_first`` / ``-1R_first`` / ``neither_within_horizon`` and a
-    SEPARATE ``truncated`` bucket (a horizon the window end cut short before +1R/−1R could resolve) —
-    never folded into the resolved buckets, never extrapolated. n is the occurrence count. The
-    distribution is a journaled MEASUREMENT, never an edge/win-rate claim."""
-    horizons = list(config.excursion_horizons_seconds)
-    rows: list[dict] = []
-    for h in horizons:
-        plus = minus = neither = truncated = 0
-        for occ in occurrence_rows:
-            for hz in occ["horizons"]:
-                if hz["horizon"] != h:
-                    continue
-                outcome = hz.get("outcome")
-                if hz.get("truncated") and outcome is None:
-                    truncated += 1
-                elif outcome == TERNARY_PLUS:
-                    plus += 1
-                elif outcome == TERNARY_MINUS:
-                    minus += 1
-                elif outcome == TERNARY_NEITHER:
-                    neither += 1
-        rows.append(
-            {
-                "horizon": h,
-                TERNARY_PLUS: plus,
-                TERNARY_MINUS: minus,
-                TERNARY_NEITHER: neither,
-                "truncated": truncated,
-            }
-        )
-    return rows
-
-
-class StudyRunner:
-    """Runs one study end-to-end (off the event loop) and persists its result ONCE.
-
-    The runner builds a FRESH ``TapeEngine``, attaches the read-only ``_PathObserver`` at the existing
-    observer seam, replays the source UNPACED (cooperative cancellation between events), records the
-    snapshot path in memory ONCE, then derives BOTH the state-native setup arms and the seeded
-    random-arm-time null arms from that single pass and measures each arm's excursions through the
-    EXISTING ``ExcursionTracker``. All persistence goes through the injected ``JournalStore``'s single
-    writer queue."""
-
-    def __init__(self, store: JournalStore, config: Config) -> None:
-        self._store = store
-        self._config = config
-
-    def run(
-        self,
-        *,
-        study_id: str,
... [diff_bound] apps/backend/app/research/studies.py: 471 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/taxonomy.py b/apps/backend/app/research/taxonomy.py
index 11b9c4f..aef3730 100644
--- a/apps/backend/app/research/taxonomy.py
+++ b/apps/backend/app/research/taxonomy.py
@@ -1,31 +1,18 @@
-"""The research taxonomy — the SINGLE backend owner of every research label (capability 24).
-
-``GET /research/taxonomy`` serves this verbatim; the frontend hardcodes NONE of it (setup names,
-direction/verdict display copy, the per-setup level requirement, and the expected-behaviour
-statement templates all come from here). Centralizing the catalog here is what lets the declare
-form be fully taxonomy-driven and keeps copy discipline (J-66: thesis-attributed, present-tense,
-descriptive — never imperative/predictive/certain) enforced in ONE place.
-
-This iteration the verdict stays ``pending`` for every thesis (the verdict-transition engine is
-next iteration), so the verdict enum here carries display copy only; nothing here evaluates a
-verdict. The expected-behaviour statement templates ARE evaluated live by the monitor against the
-existing engine states/features (statuses ``met | not_yet | violated``) — they compose EXISTING
-signals only, never a new indicator.
+"""The research taxonomy — the SINGLE backend owner of the feed-basis display labels.
+
+``GET /research/taxonomy`` serves this verbatim. era-5D J-01 ("The Clean Slate" demolition
+interlude) SLIMMED this module to its one surviving kept-surface consumer: the cockpit's and
+``/structure``'s ``FeedBasisBadge`` component, which reads ``feed_basis.feeds[].{id,name}`` and
+``feed_basis.live_disclosure`` verbatim to label the served ``data_feed`` (sim | iex | sip | yahoo).
+Every other label family this module used to own — verdict/thesis-status/monitor-status,
+management-stance, entry-checklist, chart-geometry, risk-flag, mistake-tag, grade, excursion,
+analytics, replay-study, setup-forming-hint, sound-cue, and thesis setup-catalog copy — was deleted
+whole this iteration along with the journal/studies/performance product surfaces that were its only
+readers (see ``docs/goal.md``'s I-2 taxonomy SLIM row).
 """
 
 from __future__ import annotations
 
-from typing import TYPE_CHECKING
-
-if TYPE_CHECKING:
-    from ..config import Config
-
-# --- Direction enum -----------------------------------------------------------------------------
-DIRECTIONS: dict[str, str] = {
-    "long": "Long",
-    "short": "Short",
-}
-
 # --- Feed-basis display copy (capability 28 honesty stamps, J-67; data-contract row 24 additive) --
 # The SINGLE backend owner of the per-feed badge labels and the live IEX-vs-SIP disclosure line. The
 # cockpit feed-basis badge renders the served ``data_feed`` (sim | iex | sip) VERBATIM with these
@@ -49,1175 +36,16 @@ FEED_BASIS_LIVE_DISCLOSURE: str = (
     "— spreads and prints differ"
 )
 
-# --- Verdict enum (display copy only this iteration; the transition engine is next) -------------
-# Per the design direction: pending = slate; confirming green; weakening amber; rejecting /
-# invalidated red. Only ``pending`` is ever published this iteration.
-VERDICTS: dict[str, str] = {
-    "pending": "Pending",
-    "confirming": "Confirming",
-    "weakening": "Weakening",
-    "rejecting": "Rejecting",
-    "invalidated": "Invalidated",
-    "expired": "Expired",
-}
-
-# --- Thesis status / resolution enum (J-51; data-contract row 24) --------------------------------
-# The SINGLE backend owner of the thesis lifecycle-status display copy — the journal table renders
-# these VERBATIM (the frontend hardcodes none of them). ``active`` is the only non-terminal status;
-# the other four are RESOLUTIONS (terminal statuses). Design direction: invalidated/expired carry the
-# terminal-red treatment, played_out/abandoned the resolved treatment, active the live treatment —
-# the frontend maps the COLOR from the id (a visual concern), but the LABEL text comes from here.
-STATUSES: dict[str, str] = {
-    "active": "Active",
-    "played_out": "Played out",
-    "abandoned": "Abandoned",
-    "invalidated": "Invalidated",
-    "expired": "Expired",
-}
-
-# The terminal statuses that count as RESOLUTIONS (a resolution IS a terminal status). Surfaced as its
-# own enum so the journal filter's resolution control is taxonomy-driven (not a hardcoded list).
-RESOLUTIONS: tuple[str, ...] = ("played_out", "abandoned", "invalidated", "expired")
-
-
-# --- Monitor-status enum + lifecycle display copy (capability 24, J-47; data-contract row 24) ----
-# The research monitor's status, owned ONCE on the backend and read VERBATIM by the strip:
-#   ok            — the thesis is being watched and judged live.
-#   failed        — the monitor or its store write errored (surfaced honestly, never hidden).
-#   not_evaluated — the thesis carries a real entry mark and SURVIVES a stop/restart as
-#                   active-but-not-evaluated: it is not orphaned, but no verdict accrues while the
-#                   matching source is not being watched. Re-watching the SAME source resumes it.
-MONITOR_STATUSES: tuple[str, ...] = ("ok", "failed", "not_evaluated")
-
-# The plain-language notice shown on a surviving entry-marked thesis while it is not being
-# evaluated. Present-tense, descriptive, thesis-attributed (J-66) — never imperative/predictive.
-NOT_EVALUATED_NOTICE = (
-    "not currently evaluated — re-watch this source to resume"
-)
-
-
-def not_evaluated_notice(bound_source: str) -> str:
-    """The backend-owned not-evaluated notice naming the thesis's bound source (row 24).
-
-    Rendered VERBATIM by the strip — the frontend composes none of this copy. Naming the bound
-    source makes the resume action concrete ("re-watch THIS source")."""
-    return f"{NOT_EVALUATED_NOTICE} ({bound_source})"
-
-
-def mismatched_source_notice(bound_source: str, watched_source: str) -> str:
-    """The backend-owned notice when a DIFFERENT source is watched than the thesis was declared on.
-
-    A thesis is bound to its source identity and is NEVER evaluated against a different source
-    (source-honesty anti-goal). The notice names the declared (bound) source so the user knows
-    which watch would resume it. Present-tense, descriptive (J-66)."""
-    return (
-        f"not evaluated against this source — your thesis is bound to {bound_source}, "
-        f"not {watched_source}; re-watch {bound_source} to resume"
-    )
-
-
-# --- Management-stance enum + display copy (capability 27, J-53; data-contract rows 24 & 25) ------
-# The SINGLE backend owner of the holding-period management stance — the stance the thesis strip shows
-# while a thesis is ENTRY-MARKED and UNRESOLVED, answering "does the tape still support this position?".
-# The frontend hardcodes NONE of this copy (it reads the label + evidence verbatim off the projection).
-#
-# The stance is a pure DERIVATION from the latest row-16 PUBLISHED verdict (stance.py owns the timing
-# + dwell; this module owns the verdict->stance MAP and every display string). Three values only —
-# the established verdict/stance palette (design direction): ``thesis_intact`` emerald,
-# ``thesis_weakening`` amber, ``thesis_invalidated`` rose with the terminal treatment. Copy is
-# present-tense, factual, thesis-attributed (J-66 / anti-goals) — never imperative, never predictive.
-MANAGEMENT_STANCES: dict[str, str] = {
-    "thesis_intact": "Thesis intact",
-    "thesis_weakening": "Thesis weakening",
-    "thesis_invalidated": "Thesis invalidated",
-}
-
-# The verdict -> management-stance MAP (the backend-owned table the spec mandates). The full
-# five-verdict mapping, with ONE home:
-#   * ``confirming``  -> ``thesis_intact``      (the tape published a confirmation; the position holds);
-#   * ``weakening``   -> ``thesis_weakening``   (the confirming evidence faded);
-#   * ``rejecting``   -> ``thesis_weakening``   (the opposite side took control — the position is under
-#                                                pressure, not yet system-invalidated);
-#   * ``pending``     -> ``thesis_weakening``   (the HONEST J-54 case: an entry while the verdict is
-#                                                still pending NEVER reads ``thesis_intact`` — no
-#                                                published confirmation backs it; its evidence names
-#                                                the actual verdict via ``STANCE_PENDING_EVIDENCE``);
-#   * ``invalidated`` -> ``thesis_invalidated`` (the J-44 system auto-resolve — terminal, dwell-exempt).
-# Kept here (not inline in stance.py) so the verdict->stance mapping + its copy share ONE owner.
-_VERDICT_TO_STANCE: dict[str, str] = {
-    "confirming": "thesis_intact",
-    "weakening": "thesis_weakening",
-    "rejecting": "thesis_weakening",
-    "pending": "thesis_weakening",
-    "invalidated": "thesis_invalidated",
-}
-
-# The honest "entry while not confirmed" evidence (the J-54 case): an entry marked while the verdict is
-# pending (or carrying no published evidence yet) reads as NOT-confirmed — never ``thesis_intact``,
-# never a fabricated weakening-from-confirmation. Present-tense, factual, thesis-attributed.
-STANCE_PENDING_EVIDENCE = (
-    "The tape has not published a confirmation of your thesis since you marked entry — the position "
-    "is open without a confirming read."
-)
-
-# The two DISTINCT honest-absence copies (iter-15 lesson: one fallback string must not cover two
-# causes). They name WHY no management stance is shown — these are causally different states:
-#   * NO_ENTRY_MARK   — the thesis is live and evaluating, but the user has not marked an entry, so
-#                       there is no position to manage (the verdict view stands on its own).
-#   * NOT_EVALUATED   — the thesis carries a real entry mark but its watch is not evaluating (the
-#                       surviving not-evaluated / mismatched-source path) — no live tape to read a
-#                       stance from, and deliberately NO frozen-stale stance.
-STANCE_ABSENCE_NO_ENTRY_MARK = (
-    "No entry is marked on this thesis, so there is no held position to read a management stance for "
-    "yet — mark your entry to see whether the tape still supports it."
-)
-STANCE_ABSENCE_NOT_EVALUATED = (
-    "This thesis is not being evaluated right now, so no live management stance is read — re-watch its "
-    "source to resume; no stale stance is shown."
-)
-
-# The journaled-measurement register for the live position readouts (consistent with the realized-R
-# label discipline) — the distance-to-invalidation + open-R caption. R-units only, never currency,
-# never a prediction. The "Descriptive only — not trading advice" register extends to the stance block.
-STANCE_READOUT_CAPTION = "journaled measurement, R = |entry − invalidation|"
-
-
-# --- Entry-checklist enums + display copy (capability 33, J-63; data-contract rows 24 & 25) --------
-# The SINGLE backend owner of EVERY entry-checklist string — the strip's pre-entry-mark cue block.
-# The frontend hardcodes NONE of it (it reads each check's label + the rendered margin VERBATIM off the
-# projection, and the stance/nearest-counterevidence copy from here). At the moment of decision (an
-# active, evaluated, not-yet-entry-marked thesis) the checklist answers, check by check with a LIVE
-# MEASURED MARGIN, whether the tape currently meets the entry conditions — never a naked signal.
-#
-# Copy discipline (J-66 / anti-goals): present-tense, FACTUAL, descriptive — never imperative
-# ("buy / enter"), never predictive (no price target, no forecast), never certain. A check DESCRIBES a
-# measured condition; the aggregate stance DESCRIBES what the tape is doing NOW relative to the thesis.
-
-# The eight named checks, in display order. Each LABEL is a short, neutral noun phrase naming the
-# condition (NOT a command). The eight compose ONLY existing canonical engine values (the spec's row-25
-# checklist half) — no new indicator. Owned ONCE here so the strip is fully taxonomy-driven.
-CHECKLIST_CHECKS: dict[str, str] = {
-    "verdict_confirming": "Verdict confirming",
-    "warm": "Classifier warm",
-    "feed_live": "Feed live",
-    "tape_lag_ok": "Tape delivery current",
-    "spread_stable": "Spread within stability",
-    "trade_speed_ok": "Trade speed at floor",
-    "invalidation_distance_ok": "Invalidation clear of spread",
-    "not_chasing": "Entry not chasing",
-}
-
-# The PER-CHECK margin CAPTION — a short unit note rendered beside each check's measured margin so the
-# user reads the margin in its OWN units (the spec: "live measured margin in its own units, never a
-# bare boolean"). Descriptive only. The numeric margin itself is computed server-side and rendered
-# verbatim by the strip; this caption only NAMES the unit/comparison.
-CHECKLIST_CHECK_CAPTIONS: dict[str, str] = {
-    "verdict_confirming": "the published verdict against your thesis",
-    "warm": "events processed vs the classifier's warm-up floor",
-    "feed_live": "the canonical stream status",
-    "tape_lag_ok": "delivery lag (s) vs the freshness bound",
-    "spread_stable": "average spread (bps) vs the stability cap",
-    "trade_speed_ok": "trade speed (trades/s) vs the floor",
-    "invalidation_distance_ok": "distance to invalidation in spread-multiples vs the floor",
-    "not_chasing": "move since the rule first held vs the chase threshold",
-}
-
-# The four aggregate STANCES — the entry checklist's read at the moment of decision. The established
-# verdict/stance palette EXTENDED (design direction): ``conditions_met`` emerald, ``conditions_not_met``
-# slate, ``tape_against`` rose, ``no_fresh_tape`` amber. The frontend maps COLOR from the id (a visual
-# concern) but reads the LABEL text from here. Factual, present-tense, never imperative/predictive.
-CHECKLIST_STANCES: dict[str, str] = {
-    "conditions_met": "Conditions met",
-    "conditions_not_met": "Conditions not met",
-    "tape_against": "Tape against",
-    "no_fresh_tape": "No fresh tape",
-}
-
-
-def checklist_check_label(check: str) -> str:
-    """Display label for a checklist-check id. Unknown -> itself (never fabricated)."""
-    return CHECKLIST_CHECKS.get(check, check)
-
-
-def checklist_check_caption(check: str) -> str:
-    """The per-check unit caption. Unknown -> empty (never fabricated)."""
-    return CHECKLIST_CHECK_CAPTIONS.get(check, "")
-
-
-def checklist_stance_label(stance: str) -> str:
-    """Display label for a checklist-stance id. Unknown -> itself (never fabricated)."""
-    return CHECKLIST_STANCES.get(stance, stance)
-
-
-def checklist_stance_evidence(stance: str, passed: int, total: int) -> str:
-    """The factual plain-language evidence for an aggregate checklist stance (no naked stance).
-
-    Present-tense, descriptive, in the goal's "N/8 checks pass" register — NEVER imperative
-    ("enter now"), NEVER predictive (no price/forecast), NEVER certain. Each stance names what the
-    tape is doing NOW relative to the thesis's entry conditions:
-      * ``conditions_met``     — every check passes after confirmation;
-      * ``conditions_not_met`` — at least one check is unmet (the blocker list travels separately);
-      * ``tape_against``       — the published verdict is rejecting the thesis;
-      * ``no_fresh_tape``      — the feed is not live / the tape is not current, so the conditions
-                                 cannot be read against fresh tape (a previous green never persists).
-    """
-    fraction = f"{passed}/{total} checks pass"
-    if stance == "conditions_met":
-        return (
-            f"The tape currently meets every entry condition for your thesis — {fraction}."
-        )
-    if stance == "tape_against":
-        return (
-            "The published verdict is rejecting your thesis — the tape is currently working against "
-            f"it ({fraction})."
-        )
-    if stance == "no_fresh_tape":
-        return (
-            "The feed is not delivering current tape, so the entry conditions cannot be read against "
-            f"fresh data right now ({fraction})."
-        )
-    # conditions_not_met (and any unknown stance) — name the shortfall factually.
-    return (
-        f"The tape does not yet meet every entry condition for your thesis — {fraction}; the unmet "
-        "checks are listed below."
-    )
-
-
-def checklist_nearest_counterevidence(check_label: str, margin: str, met: bool) -> str:
-    """The nearest-counterevidence line (capability 33) — the closest condition that would FLIP the
-    current read, with its margin, computed once server-side and rendered verbatim.
-
-    When the conditions ARE met it names the passing check nearest its boundary (the first that would
-    drop if the tape moves); when they are NOT met it names the nearest-to-passing blocker (the first
-    that would clear). Descriptive, present-tense — it states which condition is closest to its line,
-    never a forecast that it WILL cross. ``margin`` is the already-formatted margin string."""
-    if met:
-        return (
-            f"Closest to flipping: {check_label} sits nearest its boundary at {margin}."
-        )
-    return (
-        f"Nearest to passing: {check_label} at {margin}."
-    )
-
-
-# The checklist honest-absence copy — shown on the active-but-not-yet-checklist paths so the absence is
-# never a silent blank. ONE distinct cause per string (the iter-15 lesson). The not-evaluated /
-# no-entry-mark / mismatched-source absences are covered by the management-stance + monitor-notice copy
-# already; THIS string covers the checklist's own "evaluating but no fresh tape to read" intermediate.
-CHECKLIST_ABSENCE_NO_FRESH_TAPE = (
-    "The feed is not delivering current tape, so the entry checklist is not read against fresh data "
-    "right now — no stale checklist is shown."
-)
-
-
-def stance_for_verdict(verdict: str) -> str:
-    """The management stance for a published verdict (the backend-owned map; J-53).
-
-    An unknown/never-mapped verdict (e.g. ``expired`` — which never reaches the stance, the keys being
-    absent then) falls back to ``thesis_weakening`` (the conservative NOT-intact reading — a stance is
-    never ``thesis_intact`` without an explicit ``confirming`` verdict)."""
-    return _VERDICT_TO_STANCE.get(verdict, "thesis_weakening")
-
-
-def management_stance_label(stance: str) -> str:
-    """Display label for a management-stance id. Unknown -> itself (never fabricated)."""
-    return MANAGEMENT_STANCES.get(stance, stance)
-
-
-# --- Chart-geometry labels (capability 25, J-48; data-contract row 24) ---------------------------
-# The backend-owned plain-language labels the chart renders VERBATIM on the thesis geometry
-# overlay — the frontend hardcodes NONE of them (one copy register, J-66). Present-tense,
-# descriptive, never imperative/predictive ("Descriptive only — not trading advice" extends to the
-# chart). The invalidation/level lines name what the user DECLARED; the verdict/entry/exit marker
-# labels reuse the established verdict + action vocabulary.
-GEOMETRY_INVALIDATION_LINE_LABEL = "Invalidation"
-GEOMETRY_LEVEL_LINE_LABEL = "Level"
-
-# Marker labels keyed by verdict (the verdict-transition markers reuse the VERDICTS display copy);
-# the entry/exit marks and the first-confirmation marker carry their own descriptive labels.
-GEOMETRY_ENTRY_MARK_LABEL = "Entry"
-GEOMETRY_EXIT_MARK_LABEL = "Exit"
-GEOMETRY_FIRST_CONFIRMATION_LABEL = "First confirmation"
-
-
-def verdict_marker_label(verdict: str) -> str:
-    """The chart label for a published verdict-transition marker — the VERDICTS display copy.
-
-    Reuses the single verdict enum (``VERDICTS``) so the chart, the strip, and the timeline all read
-    the same words. An unknown verdict falls back to its own raw key (never a fabricated label)."""
-    return VERDICTS.get(verdict, verdict)
-
-
-# --- Entry risk-flag catalog (capability 26, J-49; data-contract rows 17 & 24) -------------------
-# The SINGLE backend owner of every risk-flag LABEL and its plain-language EVIDENCE copy — the
-# frontend hardcodes NONE of it. Each flag is computed ONCE at declaration from the live engine
-# snapshot + config (in ``monitor.compute_risk_flags``) and FROZEN on the thesis; the strip renders
-# the label + the measured-evidence sentence VERBATIM as an amber advisory chip. Advisory, never
-# blocking — a fired flag is a record of the entry MOMENT, never a live indicator.
-#
-# Copy discipline (J-66): present-tense, descriptive, MEASURED — it states what was true at
-# declaration ("recent buy impact +0.44% exceeds the 0.20% chase threshold"), never imperative
-# ("don't buy"), never predictive, never certain. The label is the short chip title; the evidence
-# is the one-line measured margin built from the canonical engine values behind the flag.
-RISK_FLAGS: dict[str, str] = {
-    "before_warmup": "Declared before warm-up",
-    "invalidation_too_tight": "Invalidation too tight",
-    "chasing_entry": "Chasing an extended move",
-    "wide_spread_illiquid": "Wide spread / illiquid",
-    "low_trade_speed": "Low trade speed",
-    "against_expected_tape": "Against the expected tape",
-}
-
-
-def is_valid_risk_flag(flag: str) -> bool:
-    return flag in RISK_FLAGS
-
-
-def risk_flag_label(flag: str) -> str:
-    """The short chip title for a risk flag. An unknown key falls back to itself (never fabricated)."""
-    return RISK_FLAGS.get(flag, flag)
-
-
-def _pct(return_value: float) -> str:
-    """Format an impact-as-return as a signed percent (e.g. 0.0044 -> ``+0.44%``) for evidence copy."""
-    return f"{return_value * 100:+.2f}%"
-
-
-def before_warmup_evidence(trade_count: int, warmup_min_events: int) -> str:
-    return (
-        f"declared after {trade_count} trades, below the {warmup_min_events}-trade warm-up the "
-        f"classifier needs for a confident read"
-    )
-
-
-def invalidation_too_tight_evidence(
-    distance: float, spread: float, multiple: float
-) -> str:
-    band = spread * multiple
-    return (
-        f"the invalidation sits {distance:.2f} from the last, inside the {band:.2f} band "
-        f"({multiple:g}× the {spread:.2f} spread) where ordinary spread noise could trip it"
-    )
... [diff_bound] apps/backend/app/research/taxonomy.py: 828 more diff lines omitted — Read the file for full detail
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-clean_slate-index.html     | 11 +++++++----
 runs/goal-session-clean_slate/engine.pid        |  2 +-
 runs/goal-session-clean_slate/session.json      |  6 +++++-
 runs/goal-session-clean_slate/telemetry.jsonl   | 13 +++++++++++++
 runs/goal-session-clean_slate/trace/trace.jsonl |  3 +++
 5 files changed, 29 insertions(+), 6 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
