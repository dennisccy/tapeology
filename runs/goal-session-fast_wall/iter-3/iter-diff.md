# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/backtests.py b/apps/backend/app/research/backtests.py
index fd898af..20cbd88 100644
--- a/apps/backend/app/research/backtests.py
+++ b/apps/backend/app/research/backtests.py
@@ -89,6 +89,7 @@ The disciplines, clause by clause:
 
 from __future__ import annotations
 
+import bisect
 import random
 import threading
 import time
@@ -97,10 +98,10 @@ import uuid
 from ..config import Config, PROFILE_DEFAULT, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID
 from .bars import BarStore
 from .datasets import DatasetIntegrityError, DatasetNotFound, DatasetStore
-from .levels import compute_levels, CLASS_A, CLASS_B, CLASS_C
+from .levels import compute_levels, level_change_points, CLASS_A, CLASS_B, CLASS_C
 from .marks import r_basis
 from .store import BacktestRecord, JournalStore
-from .tradability import RESISTANCE, SUPPORT, compute_tradability
+from .tradability import RESISTANCE, SUPPORT, basis_day_key, compute_tradability
 
 # The status vocabulary and the state-native helpers are REUSED from the studies module (one
 # owner per literal / per mapping — never a second copy): the premise-state arming map, the
@@ -392,6 +393,55 @@ def _aggregate_by_class(trades: list[dict], config: Config) -> dict:
     return breakdown
 
 
+class _StructureArmMemo:
+    """goal-fast_wall J-03 ("the arm memo", ``docs/goal.md`` Key Capability 3): a small per-run
+    accelerator serving ``structure_tape``/``structure_tape_map``'s arming checks from the
+    handful of real level/tradability states a session actually has, instead of re-running the
+    FULL ``compute_levels``/``compute_tradability`` pipeline on every confirming tick.
+
+    In-memory, ONE instance built fresh inside ``_structure_tape_trades`` /
+    ``_structure_tape_map_trades`` -- once per ``BacktestRunner.run()`` call, never shared across
+    runs, never persisted to disk or any store: a rebuildable, non-canonical accelerator (the
+    interlude's "never a source of truth" discipline -- deleting/skipping it loses nothing, since
+    every miss falls through to the SAME canonical owner call a ``memo=None`` caller would make).
+
+    ``levels_at(as_of_epoch)`` buckets ``as_of_epoch`` via ``bisect.bisect_right`` into the
+    ``levels.level_change_points`` tuple resolved ONCE at construction -- the contract that
+    function documents (``compute_levels`` is constant between two consecutive change points)
+    means every ``as_of_epoch`` landing in the SAME bucket shares a byte-identical result, so the
+    real owner is called at most once per bucket actually visited. ``tradability_at(as_of_epoch)``
+    buckets by ``tradability.basis_day_key(as_of_epoch)`` (constant per UTC session date) the
+    identical way. Both are a PURE memoization of an EXISTING owner call -- never a second
+    computation path (the two source-introspection guard tests pin this: the literal
+    ``compute_levels(``/``compute_tradability(`` owner calls stay present in
+    ``_structure_tape_arm``'s/``_structure_tape_map_arm``'s own fallback branch, and no
+    level-internal helper name is ever referenced here)."""
+
+    def __init__(self, bar_store: BarStore, symbol: str, config: Config) -> None:
+        self._bar_store = bar_store
+        self._symbol = symbol
+        self._config = config
+        self._change_points = level_change_points(bar_store, symbol)
+        self._levels_cache: dict[int, dict] = {}
+        self._tradability_cache: dict[str, dict] = {}
+
+    def levels_at(self, as_of_epoch: float) -> dict:
+        bucket = bisect.bisect_right(self._change_points, as_of_epoch)
+        cached = self._levels_cache.get(bucket)
+        if cached is None:
+            cached = compute_levels(self._bar_store, self._symbol, as_of_epoch, self._config)
+            self._levels_cache[bucket] = cached
+        return cached
+
+    def tradability_at(self, as_of_epoch: float) -> dict:
+        key = basis_day_key(as_of_epoch)
+        cached = self._tradability_cache.get(key)
+        if cached is None:
+            cached = compute_tradability(self._bar_store, self._symbol, as_of_epoch, self._config)
+            self._tradability_cache[key] = cached
+        return cached
+
+
 class BacktestRunner:
     """Runs one backtest end-to-end and persists its report ONCE (row 31's single computer).
 
@@ -632,9 +682,15 @@ class BacktestRunner:
         symbol with no recorded bar series, and a corrupt SOLE bar series (``compute_levels``
         aliases that to ``no_bar_series_for_symbol`` — the iter-2 seam, unchanged here) each yield
         zero classified levels to test against, so ``structure_tape`` arms nothing rather than
-        fabricating a partial computation."""
+        fabricating a partial computation.
+
+        goal-fast_wall J-03: builds exactly ONE ``_StructureArmMemo`` here (per run, in-memory,
+        never shared/persisted) and threads it into every ``_structure_tape_arm`` call below —
+        collapsing the per-tick ``compute_levels`` calls this loop used to make into one per real
+        level-change-point interval, byte-identically (see ``_StructureArmMemo``'s own docstring)."""
         if bar_store is None or not symbol or epoch_anchor is None:
             return []
+        memo = _StructureArmMemo(bar_store, symbol, self._config)
         entries = strategy["entries"]
         horizon = strategy["exits"]["horizon_seconds"]
         cooldown = entries["arm_cooldown_seconds"]
@@ -654,7 +710,8 @@ class BacktestRunner:
                 and point.timestamp >= cooldown_until
             ):
                 arm = self._structure_tape_arm(
-                    point, bar_store, symbol, epoch_anchor + point.timestamp, entries, config
+                    point, bar_store, symbol, epoch_anchor + point.timestamp, entries, config,
+                    memo=memo,
                 )
                 if arm is not None:
                     direction, setup_type, level, opposing_price = arm
@@ -674,6 +731,8 @@ class BacktestRunner:
         as_of_epoch: float,
         entries: dict,
         config: Config,
+        *,
+        memo: "_StructureArmMemo | None" = None,
     ) -> tuple[str, str, dict, float | None] | None:
         """One flat-event arming check: resolve which reading (if any) the CURRENT tape state
         confirms, and — only then — read the row-39 levels as of THIS event's own absolute
@@ -687,12 +746,21 @@ class BacktestRunner:
         ``next_opposing_zone_price`` (era-4 J-05) is resolved from this SAME ``compute_levels``
         result (never a second/future levels read — the no-lookahead discipline) via
         ``_next_opposing_zone_price``, feeding the class-scaled reward-target exit; ``None`` when
-        no zone qualifies on the side ``direction`` implies."""
+        no zone qualifies on the side ``direction`` implies.
+
+        ``memo`` (goal-fast_wall J-03, keyword-only, defaulting to ``None``): when provided,
+        levels are served through its ``levels_at`` (a memoized read, byte-identical to a fresh
+        ``compute_levels`` call — see ``_StructureArmMemo``'s own docstring for the contract);
+        ``None`` (every caller that does not opt in, e.g. a direct test call) preserves today's
+        EXACT direct-call behaviour, unchanged."""
         reading = _structure_tape_reading(point.tape_state, entries)
         if reading is None:
             return None
         direction, setup_type = reading
-        result = compute_levels(bar_store, symbol, as_of_epoch, config)
+        if memo is not None:
+            result = memo.levels_at(as_of_epoch)
+        else:
+            result = compute_levels(bar_store, symbol, as_of_epoch, config)
         band_bps = entries["proximity_band_bps"]
         zones = result["confluence_zones"]
         for zone in zones:
@@ -725,9 +793,16 @@ class BacktestRunner:
         ONLY difference is the arming SOURCE: ``_structure_tape_map_arm`` (tradable-map bands)
         instead of ``_structure_tape_arm`` (raw classified levels/zones). See
         ``_structure_tape_map_arm``'s own docstring for the arming rule and its honest-emptiness
-        floors (missing bar_store/symbol/epoch_anchor, no bar series, no classified band)."""
+        floors (missing bar_store/symbol/epoch_anchor, no bar series, no classified band).
+
+        goal-fast_wall J-03: builds exactly ONE ``_StructureArmMemo`` here (per run, in-memory,
+        never shared/persisted — a SEPARATE instance from ``_structure_tape_trades``'s own, since
+        each is scoped to its own run) and threads it into every ``_structure_tape_map_arm`` call
+        below — collapsing the per-tick ``compute_tradability`` calls this loop used to make into
+        one per real UTC session date, byte-identically (see ``_StructureArmMemo``'s docstring)."""
         if bar_store is None or not symbol or epoch_anchor is None:
             return []
+        memo = _StructureArmMemo(bar_store, symbol, self._config)
         entries = strategy["entries"]
         horizon = strategy["exits"]["horizon_seconds"]
         cooldown = entries["arm_cooldown_seconds"]
@@ -747,7 +822,8 @@ class BacktestRunner:
                 and point.timestamp >= cooldown_until
             ):
                 arm = self._structure_tape_map_arm(
-                    point, bar_store, symbol, epoch_anchor + point.timestamp, entries, config
+                    point, bar_store, symbol, epoch_anchor + point.timestamp, entries, config,
+                    memo=memo,
                 )
                 if arm is not None:
                     direction, setup_type, level, opposing_price = arm
@@ -767,6 +843,8 @@ class BacktestRunner:
         as_of_epoch: float,
         entries: dict,
         config: Config,
+        *,
+        memo: "_StructureArmMemo | None" = None,
     ) -> tuple[str, str, dict, float | None] | None:
         """One flat-event arming check — the IDENTICAL shape ``_structure_tape_arm`` performs
         (resolve which reading the CURRENT tape state confirms FIRST, so a non-confirming tick
@@ -799,12 +877,21 @@ class BacktestRunner:
         ``next_opposing_price`` is resolved from this SAME ``compute_tradability`` result (never a
         second/future map read) via ``_next_opposing_band_price``, feeding the identical
         class-scaled reward-target exit ``structure_tape`` uses; ``None`` when no band qualifies on
-        the side ``direction`` implies."""
+        the side ``direction`` implies.
+
+        ``memo`` (goal-fast_wall J-03, keyword-only, defaulting to ``None``): when provided,
+        tradability is served through its ``tradability_at`` (a memoized read, byte-identical to a
+        fresh ``compute_tradability`` call — see ``_StructureArmMemo``'s own docstring for the
+        contract); ``None`` (every caller that does not opt in, e.g. a direct test call) preserves
+        today's EXACT direct-call behaviour, unchanged."""
         reading = _structure_tape_reading(point.tape_state, entries)
         if reading is None:
             return None
         direction, setup_type = reading
-        result = compute_tradability(bar_store, symbol, as_of_epoch, config)
+        if memo is not None:
+            result = memo.tradability_at(as_of_epoch)
+        else:
+            result = compute_tradability(bar_store, symbol, as_of_epoch, config)
         band_bps = entries["proximity_band_bps"]
         bands = result["bands"]
         wanted_side = _structure_tape_map_side_for_reading(direction, setup_type)
diff --git a/apps/backend/app/research/levels.py b/apps/backend/app/research/levels.py
index fe612a1..18ec9a6 100644
--- a/apps/backend/app/research/levels.py
+++ b/apps/backend/app/research/levels.py
@@ -322,3 +322,43 @@ def compute_levels(store: BarStore, symbol: str, as_of_epoch: float, config: Con
         "no_bar_series_for_symbol": False,
         "confluence_zones": compute_confluence_zones(levels, config),
     }
+
+
+def level_change_points(store: BarStore, symbol: str) -> tuple[float, ...]:
+    """goal-fast_wall J-03 ("the arm memo"): a SAFE SUPERSET of every instant at which
+    ``compute_levels(store, symbol, as_of, config)`` could possibly change for ``symbol`` --
+    between any two CONSECUTIVE entries of the returned tuple, ``compute_levels`` is a constant
+    function of ``as_of``. A superset of the true change points is always safe (it costs at most
+    one harmless extra memo split); a MISSING true change point is never safe, since it would
+    silently serve a stale result across a genuine regime change. ``research/backtests.py``'s
+    ``_StructureArmMemo`` is the ONE reader of this contract, using it to collapse thousands of
+    per-tick ``compute_levels`` recomputes into the handful of real level states a session
+    actually has -- this function itself computes NOTHING about levels; it only enumerates WHEN
+    the already-frozen ``compute_levels``/``compute_confluence_zones`` bodies above could move.
+
+    Mirrors ``compute_levels``'s OWN healthy-series enumeration exactly (the SAME ``store.list()``
+    healthy-``records`` half, the SAME ``_select_one_series_per_timeframe`` tie-break, the SAME
+    ``PRIOR_PERIOD_TIMEFRAMES``/``_PERIOD_SECONDS``) so this function can never omit a series
+    ``compute_levels`` itself would read: the union of every SELECTED series' own bar epochs (a
+    newly-visible bar can create or newly confirm a swing pivot near either end of the as-of-
+    truncated prefix -- see ``_swing_pivots``) plus, for each series whose timeframe is in
+    ``PRIOR_PERIOD_TIMEFRAMES``, each of ITS bars' own period-closing instant
+    (``epoch + period_seconds`` -- the exact instant ``_prior_period_extremes`` newly treats that
+    bar as "completed"). Unlike ``compute_levels``, this reads bars WITHOUT any ``_bars_as_of``
+    truncation of its own -- a single per-run tuple must cover every ``as_of`` the run will ever
+    ask about, resolved ONCE, so a change point later than any ``as_of`` a particular caller
+    happens to query is still a safe, if unused, entry.
+
+    Returns an empty tuple for a symbol with no healthy recorded series at all -- the
+    ``no_bar_series_for_symbol`` precedent's honest absence, never a fabricated instant."""
+    records, _integrity_errors = store.list()
+    matching = [r for r in records if r["symbol"] == symbol]
+    if not matching:
+        return ()
+    points: set[float] = set()
+    for timeframe, record in _select_one_series_per_timeframe(matching).items():
+        for bar in store.load_bars(record["id"]):
+            points.add(bar.epoch)
+            if timeframe in PRIOR_PERIOD_TIMEFRAMES:
+                points.add(bar.epoch + _PERIOD_SECONDS[timeframe])
+    return tuple(sorted(points))
diff --git a/apps/backend/app/research/tradability.py b/apps/backend/app/research/tradability.py
index 8a39087..eff4015 100644
--- a/apps/backend/app/research/tradability.py
+++ b/apps/backend/app/research/tradability.py
@@ -380,3 +380,18 @@ def compute_tradability(store: BarStore, symbol: str, as_of_epoch: float, config
         "no_bar_series_for_symbol": False,
         "basis_as_of": basis_as_of,
     }
+
+
+def basis_day_key(as_of_epoch: float) -> str:
+    """goal-fast_wall J-03 ("the arm memo"): the UTC session-date key ``_resolve_basis``'s chosen
+    prior session is CONSTANT for -- reuses the EXISTING ``_session_date`` date-resolution helper
+    verbatim (never a second date derivation). ``_resolve_basis`` filters candidate daily bars by
+    ``_session_date(b.epoch) < _session_date(as_of_epoch)`` (the requested session's own UTC
+    calendar date) and picks the latest survivor -- a decision that depends on ``as_of_epoch``
+    ONLY through its own UTC calendar date, so every ``as_of_epoch`` sharing one UTC date resolves
+    the IDENTICAL prior session/basis. ``research/backtests.py``'s ``_StructureArmMemo`` is the
+    ONE reader of this contract, using it to collapse per-tick ``compute_tradability`` recomputes
+    into one real basis per UTC session date actually visited -- this function computes nothing
+    about tradability itself; it only names the key ``_resolve_basis``'s own (frozen, unchanged)
+    behaviour is already constant across."""
+    return _session_date(as_of_epoch).isoformat()
diff --git a/apps/backend/tests/test_backtests.py b/apps/backend/tests/test_backtests.py
index 76ebdf2..d210978 100644
--- a/apps/backend/tests/test_backtests.py
+++ b/apps/backend/tests/test_backtests.py
@@ -58,9 +58,11 @@ from app.research.backtests import (
 )
 from app.research.bars import BarStore
 from app.research.datasets import DatasetStore
+from app.research.levels import compute_levels, level_change_points
 from app.research.marks import r_basis
 from app.research.store import JournalStore
 from app.research.studies import _PathPoint
+from app.research.tradability import compute_tradability
 
 # The synthetic three-timeframe confluence fixture (class A/B/C zones at exact, known prices) --
 # REUSED verbatim from test_levels.py (the plan's own directive: the committed real PG bar fixture
@@ -1506,3 +1508,377 @@ def test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner
     assert "compute_levels(" in src
     for forbidden in ("_swing_pivots", "_prior_period_extremes", "_cluster_levels", "_grade_zone"):
         assert forbidden not in src, f"backtests.py must not recompute levels itself: {forbidden}"
+
+
+# === The arm memo (goal-fast_wall J-03): per-run levels/tradability memoization =====================
+# structure_tape / structure_tape_map now build one in-memory ``_StructureArmMemo`` per run and
+# thread it into every arming check — collapsing the per-tick ``compute_levels``/
+# ``compute_tradability`` calls into one per real change-point interval / UTC session date. Every
+# test below proves the SAME thing the goal.md acceptance names: byte-identity vs the direct-call
+# path (TC-5/TC-6), two genuine memo-bust legs (TC-7/TC-8), two counting spies (TC-9/TC-10), and an
+# interactive-budget multi-interval smoke test (TC-11).
+
+
+class _NoCacheArmMemo:
+    """A drop-in stand-in for ``backtests._StructureArmMemo`` that performs ZERO caching — every
+    ``levels_at``/``tradability_at`` call goes straight to the real owner function. Swapped in via
+    monkeypatch for "today's direct-call path" (the ``memo=None`` behaviour) comparison runs below,
+    so the SURROUNDING control flow (the interleaved arm/exit loop in ``_structure_tape_trades`` /
+    ``_structure_tape_map_trades``) is the EXACT production code path — only the caching behaviour
+    differs, isolating precisely the property TC-5..TC-8 must prove without duplicating that loop
+    by hand in this test module."""
+
+    def __init__(self, bar_store, symbol, config):
+        self._bar_store = bar_store
+        self._symbol = symbol
+        self._config = config
+
+    def levels_at(self, as_of_epoch):
+        return compute_levels(self._bar_store, self._symbol, as_of_epoch, self._config)
+
+    def tradability_at(self, as_of_epoch):
+        return compute_tradability(self._bar_store, self._symbol, as_of_epoch, self._config)
+
+
+def _run_unmemoized(jobs, store, dataset_store, dataset_id, bar_store, monkeypatch, *, strategy_id):
+    """Runs the SAME backtest with the arm memo's caching disabled (every level/tradability read
+    forced through a fresh owner-function computation) — "today's direct-call path" for the
+    TC-5..TC-8 byte-identity comparisons below."""
+    import app.research.backtests as backtests_module
+
+    monkeypatch.setattr(backtests_module, "_StructureArmMemo", _NoCacheArmMemo)
+    return _run(jobs, store, dataset_store, dataset_id, strategy_id=strategy_id, bar_store=bar_store)
+
+
+def test_structure_tape_memoized_run_is_byte_identical_to_the_direct_call_path(
+    tmp_path, store, jobs, confluence_bar_store, monkeypatch
+):
+    """TC-5: a memoized ``structure_tape`` run and the SAME run with the memo's caching disabled
+    (today's direct-call path) produce a byte-identical ``result``."""
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER", max_logical=100.0)
+    memoized = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
+    )
+    direct = _run_unmemoized(
+        jobs, store, dstore, meta["id"], confluence_bar_store, monkeypatch, strategy_id=STRATEGY_TAPE_ID
+    )
+    assert json.dumps(memoized["result"], sort_keys=True) == json.dumps(direct["result"], sort_keys=True)
+    assert len(memoized["result"]["trades"]) >= 1, "the proof must exercise at least one real trade"
+
+
+def test_structure_tape_map_memoized_run_is_byte_identical_to_the_direct_call_path(
+    tmp_path, store, jobs, confluence_bar_store, monkeypatch
+):
+    """TC-6: a memoized ``structure_tape_map`` run and the SAME run with the memo's caching
+    disabled (today's direct-call path) produce a byte-identical ``result``."""
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER")
+    memoized = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
+    )
+    direct = _run_unmemoized(
+        jobs, store, dstore, meta["id"], confluence_bar_store, monkeypatch,
+        strategy_id=STRATEGY_TAPE_MAP_ID,
+    )
+    assert json.dumps(memoized["result"], sort_keys=True) == json.dumps(direct["result"], sort_keys=True)
+    assert len(memoized["result"]["trades"]) >= 1, "the proof must exercise at least one real trade"
+
+
+# --- TC-7 (memo-bust leg 1): a daily period's close instant strictly between two intraday bars -----
+
+_MEMO_BUST_LEVEL_SYMBOL = "SYN-MEMO-BUST-LEVEL"
+_MEMO_BUST_1H_BASE = _CONFLUENCE_BASE
+_MEMO_BUST_DAILY_EPOCH = _MEMO_BUST_1H_BASE + 10_000.0
+# The 1d bar's OWN period-close instant — a level_change_points entry with NO bar recorded exactly
+# at it (TC-7's own premise, mechanically confirmed inside the test below).
+_MEMO_BUST_CHANGE_POINT = _MEMO_BUST_DAILY_EPOCH + _DAY
+
+
+def _memo_bust_level_bar_fixture(store: BarStore) -> None:
+    """A 3-bar ``1h`` sandwich (the ``class_b_bar_fixture`` pattern) producing ONE swing-high
+    pivot at 100.00, confirmed once the third bar is visible (well before
+    ``_MEMO_BUST_CHANGE_POINT``); a 4th ``1h`` bar recorded strictly AFTER that change point (a
+    far-away noise price, inert for pivot detection — its only role is bracketing the change point
+    between two recorded intraday epochs, TC-7's own premise); and ONE ``1d`` bar whose own
+    period-close instant IS ``_MEMO_BUST_CHANGE_POINT`` and whose close (100.02) joins the 1h
+    pivot's confluence band ONLY once that period has closed — so NO zone (and therefore no arm)
+    exists before the change point, and a genuine 2-member zone exists after it."""
+    hourly_specs = [(50, 40, 45), (100.00, 41, 98), (55, 42, 50)]
+    hourly_bars = [
+        RawBar(_MEMO_BUST_LEVEL_SYMBOL, "1h", _MEMO_BUST_1H_BASE + i * 3600.0, close, high, low, close, 1_000)
+        for i, (high, low, close) in enumerate(hourly_specs)
+    ]
+    hourly_bars.append(
+        RawBar(_MEMO_BUST_LEVEL_SYMBOL, "1h", _MEMO_BUST_CHANGE_POINT + 3600.0, 695.0, 700.0, 690.0, 695.0, 1_000)
+    )
+    daily_bars = [
+        RawBar(_MEMO_BUST_LEVEL_SYMBOL, "1d", _MEMO_BUST_DAILY_EPOCH, 100.02, 900.0, 10.0, 100.02, 1_000),
+    ]
+    store.record(
+        symbol=_MEMO_BUST_LEVEL_SYMBOL, timeframe="1h",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-03T00:00:00Z",
+        feed="sip", bars=hourly_bars,
+    )
+    store.record(
+        symbol=_MEMO_BUST_LEVEL_SYMBOL, timeframe="1d",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-03T00:00:00Z",
+        feed="sip", bars=daily_bars,
+    )
+
+
+def test_structure_tape_memo_bust_daily_period_close_between_intraday_bars(
+    tmp_path, store, jobs, monkeypatch
+):
+    """TC-7 (memo-bust leg 1)."""
+    bar_store = BarStore(tmp_path / "memo-bust-level-bars")
+    _memo_bust_level_bar_fixture(bar_store)
+
+    # The change point genuinely sits strictly between two recorded intraday ("1h") bar epochs,
+    # with no bar recorded exactly at it — the fixture's own premise, mechanically confirmed.
+    change_points = level_change_points(bar_store, _MEMO_BUST_LEVEL_SYMBOL)
+    hourly_epochs = {
+        _MEMO_BUST_1H_BASE, _MEMO_BUST_1H_BASE + 3600.0, _MEMO_BUST_1H_BASE + 7200.0,
+        _MEMO_BUST_CHANGE_POINT + 3600.0,
+    }
+    assert _MEMO_BUST_CHANGE_POINT not in hourly_epochs
+    assert any(e < _MEMO_BUST_CHANGE_POINT for e in hourly_epochs)
+    assert any(e > _MEMO_BUST_CHANGE_POINT for e in hourly_epochs)
+    assert _MEMO_BUST_CHANGE_POINT in change_points
+
+    # Non-vacuous, independent of any recorded dataset's own tick alignment: the SAME reading/price
+    # arms strictly AFTER the change point but not strictly before it.
+    entries = CONFIG.strategy_definition(STRATEGY_TAPE_ID)["entries"]
+    breakthrough_long_state = CONFIG.structure_tape_breakthrough_state_by_direction["long"]
+    probe = _PathPoint(timestamp=0.0, last=150.0, spread=0.02, tape_state=breakthrough_long_state)
+    before = BacktestRunner._structure_tape_arm(
+        probe, bar_store, _MEMO_BUST_LEVEL_SYMBOL, _MEMO_BUST_CHANGE_POINT - 1.0, entries, CONFIG
+    )
+    assert before is None, "no confluence zone exists before the 1d period closes"
+    after = BacktestRunner._structure_tape_arm(
+        probe, bar_store, _MEMO_BUST_LEVEL_SYMBOL, _MEMO_BUST_CHANGE_POINT + 1.0, entries, CONFIG
+    )
+    assert after is not None, "the 2-member zone must exist once the 1d period closes"
+
+    # Byte-identity across the SAME boundary, via a real recorded run: memoized vs the direct-call
+    # path, AND the arming decision genuinely differs (0 arms before the boundary, 1 after it).
+    anchor = _MEMO_BUST_CHANGE_POINT - 50.0
+    dstore, meta = _record_structure_tape_dataset(
+        tmp_path, "SIM-BUYER", anchor=anchor, max_logical=70.0, symbol=_MEMO_BUST_LEVEL_SYMBOL
+    )
+    memoized = _run(jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=bar_store)
+    direct = _run_unmemoized(
+        jobs, store, dstore, meta["id"], bar_store, monkeypatch, strategy_id=STRATEGY_TAPE_ID
+    )
+    assert json.dumps(memoized["result"], sort_keys=True) == json.dumps(direct["result"], sort_keys=True)
+    trades = memoized["result"]["trades"]
+    assert len(trades) == 1, "arms exactly once, only once the boundary closes the 1d period"
+    assert trades[0]["entry"]["logical_ts"] >= 50.0, "must not have armed strictly before the boundary"
+
+
+# --- TC-8 (memo-bust leg 2): a recorded run spanning a UTC calendar-date boundary -------------------
+
+
+def test_structure_tape_map_memo_bust_utc_date_boundary(
+    tmp_path, store, jobs, confluence_bar_store, monkeypatch
+):
+    """TC-8 (memo-bust leg 2)."""
+    boundary = _CONFLUENCE_BASE + 2 * _DAY  # a clean UTC midnight; confluence_bar_store's own 1d
+    # series (day 0, day 1) resolves a DIFFERENT prior session on either side of it.
+    before_map = compute_tradability(confluence_bar_store, _CONFLUENCE_SYMBOL, boundary - 1.0, CONFIG)
+    after_map = compute_tradability(confluence_bar_store, _CONFLUENCE_SYMBOL, boundary + 1.0, CONFIG)
+    assert before_map["basis_as_of"] is not None and after_map["basis_as_of"] is not None
+    assert before_map["basis_as_of"] != after_map["basis_as_of"], (
+        "the fixture's own premise: the tradability basis must genuinely differ across the boundary"
+    )
+
+    anchor = boundary - 50.0
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER", anchor=anchor, max_logical=70.0)
+    memoized = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
+    )
+    direct = _run_unmemoized(
+        jobs, store, dstore, meta["id"], confluence_bar_store, monkeypatch,
+        strategy_id=STRATEGY_TAPE_MAP_ID,
+    )
+    assert json.dumps(memoized["result"], sort_keys=True) == json.dumps(direct["result"], sort_keys=True)
+
+
+# --- TC-9: a counting spy proves compute_levels runs once per change-point interval, not per tick ---
+
+_MANY_INTERVAL_SYMBOL = "SYN-MEMO-BUST-MANY"
+_MANY_INTERVAL_BASE = _CONFLUENCE_BASE + 1000 * _DAY
+_MANY_INTERVAL_STEP = 300.0
+_MANY_INTERVAL_COUNT = 7
+
+
+def _many_interval_bar_fixture(store: BarStore) -> None:
+    """7 STRICTLY monotonically-increasing ``1h`` bars (both high and low increase with every bar)
+    — no bar is EVER a strict extreme over both its neighbours, so no swing pivot ever forms and
+    ``confluence_zones`` stays honestly empty for every ``as_of`` — the cleanest possible substrate
+    for a call-counting spy, free of any arming noise. Gives exactly 7 real
+    ``level_change_points`` (one per bar epoch; "1h" is not a prior-period timeframe)."""
+    bars = [
+        RawBar(
+            _MANY_INTERVAL_SYMBOL, "1h", _MANY_INTERVAL_BASE + i * _MANY_INTERVAL_STEP,
+            10.0 + i, 20.0 + i, 5.0 + i, 10.0 + i, 1_000,
+        )
+        for i in range(_MANY_INTERVAL_COUNT)
+    ]
+    store.record(
+        symbol=_MANY_INTERVAL_SYMBOL, timeframe="1h",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-01T02:00:00Z",
+        feed="sip", bars=bars,
+    )
+
+
+def test_structure_tape_memo_calls_compute_levels_once_per_change_point_interval_not_per_tick(
+    tmp_path, store, jobs, monkeypatch
+):
+    """TC-9."""
+    bar_store = BarStore(tmp_path / "many-interval-bars")
+    _many_interval_bar_fixture(bar_store)
+    change_points = level_change_points(bar_store, _MANY_INTERVAL_SYMBOL)
+    assert len(change_points) == 7, "the fixture's own premise: 7 monotonic bars, one change point each"
+
+    anchor = _MANY_INTERVAL_BASE - 19.5  # ts=19.5 (buyer_control confirms) lands exactly on cp[0]
+    dstore, meta = _record_structure_tape_dataset(
+        tmp_path, "SIM-BUYER", anchor=anchor, max_logical=2000.0, symbol=_MANY_INTERVAL_SYMBOL
+    )
+
+    import app.research.backtests as backtests_module
+
+    calls: list[int] = []
+    real_compute_levels = backtests_module.compute_levels
+
+    def _counting_compute_levels(*args, **kwargs):
+        calls.append(1)
+        return real_compute_levels(*args, **kwargs)
+
+    monkeypatch.setattr(backtests_module, "compute_levels", _counting_compute_levels)
+
+    payload = _run(jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=bar_store)
+    assert payload["status"] == STATUS_DONE
+    assert payload["result"]["trades"] == [], (
+        "the fixture's own premise: a strictly monotonic series never forms a qualifying zone, so "
+        "this run stays flat throughout — every confirming tick reaches the arming check"
+    )
+    assert len(calls) == len(change_points) == 7, (
+        "one real compute_levels call per distinct change-point interval actually visited — never "
+        "once per confirming tick (many hundreds of eligible ticks visit each interval here)"
+    )
+    events, _provider = _sim_events("SIM-BUYER", 2000.0)
+    confirming_tick_count = len({e.timestamp for e in events if e.timestamp >= 19.5})
+    assert len(calls) < confirming_tick_count, (
+        f"{len(calls)} real compute_levels calls must be far fewer than the "
+        f"{confirming_tick_count} confirming ticks this run actually visited"
+    )
+
+
+# --- TC-10: a counting spy proves compute_tradability runs once per UTC day, not per tick -----------
+
+
+def test_structure_tape_map_memo_calls_compute_tradability_once_per_day_key_not_per_tick(
+    tmp_path, store, jobs, monkeypatch
+):
+    """TC-10. ``basis_day_key`` is a pure function of ``as_of_epoch`` alone (it never touches the
+    store), so even an EMPTY bar store still exercises the memo meaningfully — every confirming
+    tick reaches ``tradability_at``, which always resolves the honest ``no_bar_series_for_symbol``
+    state, memoized once per distinct UTC day actually visited."""
+    empty_bar_store = BarStore(tmp_path / "empty-bars-for-day-key-spy")
+    midnight = _CONFLUENCE_BASE + 2 * _DAY  # a clean UTC midnight
+    anchor = midnight - 50.0
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER", anchor=anchor, max_logical=70.0)
+
+    import app.research.backtests as backtests_module
+
+    calls: list[int] = []
+    real_compute_tradability = backtests_module.compute_tradability
+
+    def _counting_compute_tradability(*args, **kwargs):
+        calls.append(1)
+        return real_compute_tradability(*args, **kwargs)
+
+    monkeypatch.setattr(backtests_module, "compute_tradability", _counting_compute_tradability)
+
+    payload = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=empty_bar_store
+    )
+    assert payload["status"] == STATUS_DONE
+    assert payload["result"]["trades"] == [], "an empty bar store's own honest never-arms state"
+    assert len(calls) == 2, "one real compute_tradability call per distinct UTC day actually visited"
+    events, _provider = _sim_events("SIM-SELLER", 70.0)
+    confirming_tick_count = len({e.timestamp for e in events if e.timestamp >= 19.5})
+    assert len(calls) < confirming_tick_count, (
+        f"{len(calls)} real compute_tradability calls must be far fewer than the "
+        f"{confirming_tick_count} confirming ticks this run actually visited"
+    )
+
+
+# --- TC-11: a multi-interval structure_tape backtest completes within an interactive test budget ----
+
+_MULTI_INTERVAL_SYMBOL = "SYN-MEMO-BUST-TRADE"
+_MULTI_INTERVAL_BASE = _CONFLUENCE_BASE + 2000 * _DAY
+_MULTI_INTERVAL_STEP = 200.0
+
+
+def _multi_interval_trade_bar_fixture(store: BarStore) -> None:
+    """The ``class_b_bar_fixture`` pivot-at-100.00 pattern, PLUS three extra monotonically
+    increasing filler ``1h`` bars (the ``_many_interval_bar_fixture`` proof: never new pivots) so
+    the series alone carries >= 5 distinct ``level_change_points`` — while still arming exactly
+    once the pivot confirms (a real, non-empty ``trades`` list)."""
+    specs = [(50, 40, 45), (100.00, 41, 98), (55, 42, 50), (60, 43, 55), (65, 44, 58), (70, 45, 60)]
+    hourly_bars = [
+        RawBar(
+            _MULTI_INTERVAL_SYMBOL, "1h", _MULTI_INTERVAL_BASE + i * _MULTI_INTERVAL_STEP,
+            close, high, low, close, 1_000,
+        )
+        for i, (high, low, close) in enumerate(specs)
+    ]
+    # A "1d" bar whose close (100.02) joins the 1h pivot's confluence band, its OWN period ALREADY
+    # closed long before this series even starts — decoupling zone availability from this
+    # fixture's own change-point count (unlike TC-7, which deliberately gates on it).
+    daily_bars = [
+        RawBar(_MULTI_INTERVAL_SYMBOL, "1d", _MULTI_INTERVAL_BASE - 1_000_000.0, 100.02, 900.0, 10.0, 100.02, 1_000),
+    ]
+    store.record(
+        symbol=_MULTI_INTERVAL_SYMBOL, timeframe="1h",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-01T01:00:00Z",
+        feed="sip", bars=hourly_bars,
+    )
+    store.record(
+        symbol=_MULTI_INTERVAL_SYMBOL, timeframe="1d",
+        window_start_utc="2025-01-01T00:00:00Z", window_end_utc="2025-01-02T00:00:00Z",
+        feed="sip", bars=daily_bars,
+    )
+
+
+def test_structure_tape_multi_interval_backtest_completes_fast_with_a_real_trade(tmp_path, store, jobs):
+    """TC-11."""
+    import bisect
+    import time
+
+    bar_store = BarStore(tmp_path / "multi-interval-trade-bars")
+    _multi_interval_trade_bar_fixture(bar_store)
+    change_points = level_change_points(bar_store, _MULTI_INTERVAL_SYMBOL)
+    assert len(change_points) >= 5, "the fixture's own premise"
+
+    anchor = _MULTI_INTERVAL_BASE - 300.0
+    max_logical = 2000.0
+    events, _provider = _sim_events("SIM-BUYER", max_logical)
+    first_bucket = bisect.bisect_right(change_points, anchor + min(e.timestamp for e in events))
+    last_bucket = bisect.bisect_right(change_points, anchor + max(e.timestamp for e in events))
+    assert last_bucket - first_bucket >= 5, (
+        "the fixture's own premise: the recorded tick stream must cross >= 5 distinct intervals"
+    )
+
+    dstore, meta = _record_structure_tape_dataset(
+        tmp_path, "SIM-BUYER", anchor=anchor, max_logical=max_logical, symbol=_MULTI_INTERVAL_SYMBOL
+    )
+    start = time.time()
+    payload = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=bar_store
+    )
+    elapsed = time.time() - start
+
+    assert payload["status"] == STATUS_DONE
+    assert elapsed < 10.0, f"multi-interval structure_tape backtest took {elapsed:.2f}s"
+    assert len(payload["result"]["trades"]) >= 1, "the proof must exercise at least one real trade"
diff --git a/apps/backend/tests/test_levels.py b/apps/backend/tests/test_levels.py
index 91120d3..c41f7c9 100644
--- a/apps/backend/tests/test_levels.py
+++ b/apps/backend/tests/test_levels.py
@@ -35,6 +35,7 @@ from app.research.levels import (
     SWING_PIVOT,
     compute_confluence_zones,
     compute_levels,
+    level_change_points,
 )
 
 FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"
@@ -659,3 +660,76 @@ def test_sr_config_fields_are_excluded_from_config_fingerprint():
     )
     # ...while a real classifier threshold still moves it (the counter-test).
     assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
+
+
+# --- level_change_points: the arm memo's change-point contract (goal-fast_wall J-03) ---------------
+# Reuses the synthetic three-timeframe ``_confluence_fixture`` directly above (already has a
+# non-prior-period series ("1h") AND two prior-period series ("1d", "1w") -- exactly TC-1's own
+# premise) rather than a second, near-duplicate fixture.
+
+
+def test_level_change_points_returns_sorted_deduped_superset_of_bar_epochs_and_period_closes(tmp_path):
+    """TC-1: the union of every healthy series' own bar epochs, plus each PRIOR_PERIOD_TIMEFRAMES
+    bar's own epoch + period_seconds close instant -- sorted, deduplicated -- verified by direct
+    computation against the confluence fixture's own known epochs (never hand-waved)."""
+    store = BarStore(tmp_path / "bars")
+    _confluence_fixture(store)
+    points = level_change_points(store, _CONFLUENCE_SYMBOL)
+
+    assert points == tuple(sorted(points)), "must be sorted ascending"
+    assert len(points) == len(set(points)), "must be deduplicated"
+
+    # Every 1h bar's own epoch (11 hourly bars; "1h" is NOT a prior-period timeframe -- only its
+    # own epochs are change points, never an epoch+period_seconds entry).
+    hourly_epochs = {_BASE + i * 3600.0 for i in range(11)}
+    assert hourly_epochs <= set(points)
+
+    # The 1d series (a PRIOR_PERIOD_TIMEFRAMES member, two bars at day 0 and day 1): both bars'
+    # own epochs (also shared with the 1h/1w series' own day-0 epoch) AND bar 1's own
+    # epoch + period_seconds (86400s) close instant.
+    assert {_BASE, _BASE + _DAY} <= set(points)
+    assert _BASE + 2 * _DAY in points
+
+    # The 1w series (also a PRIOR_PERIOD_TIMEFRAMES member, one bar at day 0): its own epoch
+    # (already covered above) AND its own epoch + period_seconds (604800s) close instant.
+    assert _BASE + 7 * _DAY in points
+
+    # Exact count: 11 distinct hourly epochs (i=0..10, spanning BASE..BASE+36000) plus the 1d/1w
+    # period-close instants NOT already covered by an hourly epoch (BASE+DAY=86400 and
+    # BASE+2*DAY=172800 from the 1d series, BASE+7*DAY=604800 from the 1w series -- none of which
+    # coincide with any hourly epoch, all <= 36000) -- verified by direct computation.
+    assert len(points) == 14
+
+
+def test_compute_levels_is_constant_between_two_consecutive_change_points(tmp_path):
+    """TC-2: the change-point contract, mechanically proven -- two ``as_of`` instants strictly
+    between the SAME two consecutive ``level_change_points`` entries produce byte-identical
+    ``compute_levels`` output (the property ``backtests.py``'s ``_StructureArmMemo`` relies on to
+    memoize arming checks by change-point interval instead of per confirming tick)."""
+    store = BarStore(tmp_path / "bars")
+    _confluence_fixture(store)
+    points = level_change_points(store, _CONFLUENCE_SYMBOL)
+
+    # BASE+2*DAY and BASE+7*DAY are two CONSECUTIVE entries -- nothing else falls between them on
+    # this fixture (verified by direct computation against the fixture's own known epochs, per the
+    # exact-count proof above).
+    lower, upper = _BASE + 2 * _DAY, _BASE + 7 * _DAY
+    idx = points.index(lower)
+    assert points[idx + 1] == upper, "the fixture's own premise: these must be consecutive entries"
+
+    as_of_1 = lower + 1.0  # strictly between
+    as_of_2 = upper - 1.0  # strictly between, far from as_of_1
+    assert lower < as_of_1 < as_of_2 < upper
+
+    result_1 = compute_levels(store, _CONFLUENCE_SYMBOL, as_of_1, CONFIG)
+    result_2 = compute_levels(store, _CONFLUENCE_SYMBOL, as_of_2, CONFIG)
+    assert json.dumps(result_1, sort_keys=True) == json.dumps(result_2, sort_keys=True)
+    assert len(result_1["levels"]) >= 1, "the proof must exercise at least one real level"
+
+
+def test_level_change_points_empty_for_symbol_with_no_healthy_bar_series(tmp_path):
+    """The honest empty-tuple absence -- mirrors ``no_bar_series_for_symbol``'s own precedent
+    (never a fabricated instant for a symbol with nothing recorded)."""
+    store = BarStore(tmp_path / "bars")
+    _swing_fixture(store)  # records ONLY `_SWING_SYMBOL` -- never the queried symbol below
+    assert level_change_points(store, "NEVER-RECORDED") == ()
diff --git a/apps/backend/tests/test_tradability.py b/apps/backend/tests/test_tradability.py
index e4f39ae..f1e7a0e 100644
--- a/apps/backend/tests/test_tradability.py
+++ b/apps/backend/tests/test_tradability.py
@@ -27,7 +27,7 @@ import pytest
 from app.config import CONFIG, Config
 from app.providers.adapters.base import RawBar
 from app.research.bars import BarStore
-from app.research.tradability import RESISTANCE, SUPPORT, compute_tradability
+from app.research.tradability import RESISTANCE, SUPPORT, basis_day_key, compute_tradability
 
 FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
 
@@ -347,6 +347,46 @@ def test_tradability_config_fields_are_excluded_from_config_fingerprint():
     assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
 
 
+# --- basis_day_key: the arm memo's day-key contract (goal-fast_wall J-03) ----------------------
+
+
+def test_basis_day_key_same_utc_date_is_stable():
+    """TC-3: two ``as_of_epoch`` values on the SAME UTC calendar date resolve to the identical key
+    -- reusing ``_session_date`` (never a second date derivation), mirroring
+    ``test_no_lookahead_shifting_as_of_within_the_same_session_is_unchanged``'s own premise."""
+    early = _SYN_AS_OF  # 2026-01-08T00:00:00Z
+    late = _SYN_AS_OF + 23 * 3600  # same UTC date, 23:00
+    assert basis_day_key(early) == basis_day_key(late)
+
+
+def test_basis_day_key_differs_across_a_utc_midnight_boundary():
+    """TC-4: an ``as_of_epoch`` strictly before, and one strictly after, a UTC midnight boundary
+    resolve to DIFFERENT keys -- the property ``backtests.py``'s ``_StructureArmMemo`` relies on
+    to memoize ``tradability_at`` once per real UTC session date instead of per confirming tick."""
+    just_before_midnight = _SYN_AS_OF - 1.0  # 2026-01-07T23:59:59Z
+    just_after_midnight = _SYN_AS_OF + 1.0  # 2026-01-08T00:00:01Z
+    assert basis_day_key(just_before_midnight) != basis_day_key(just_after_midnight)
+
+
+def test_basis_day_key_matches_the_date_boundary_compute_tradability_itself_shifts_basis_across(tmp_path):
+    """Direct-computation cross-check (never hand-waved): the SAME midnight boundary where
+    ``basis_day_key`` changes is really where ``compute_tradability`` itself resolves a DIFFERENT
+    ``basis_as_of`` (the existing ``test_no_lookahead_a_later_session_shifts_the_basis_forward``
+    fixture, reused) -- proving the memo's cache key genuinely tracks the value it stands in for."""
+    store = BarStore(tmp_path / "bars")
+    _seed_synthetic(store, num_days=8)
+    boundary = _SYN_AS_OF + _DAY  # 2026-01-09T00:00:00Z -- the day8/day9 boundary this fixture uses
+
+    before_key = basis_day_key(boundary - 1.0)
+    after_key = basis_day_key(boundary + 1.0)
+    assert before_key != after_key
+
+    before_map = compute_tradability(store, _SYN_SYMBOL, boundary - 1.0, CONFIG)
+    after_map = compute_tradability(store, _SYN_SYMBOL, boundary + 1.0, CONFIG)
+    assert before_map["basis_as_of"] != after_map["basis_as_of"]
+
+
+
 # --- "Lens, not a second engine": tradability.py never re-detects structure ------------------
 
 
```
