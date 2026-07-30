# Iteration diff (bounded)

Files changed: 26. Shown in full: 25.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh` (49 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_topup_compute.py b/apps/backend/app/research/desk_topup_compute.py
index 40a281e..7941036 100644
--- a/apps/backend/app/research/desk_topup_compute.py
+++ b/apps/backend/app/research/desk_topup_compute.py
@@ -39,6 +39,31 @@ at or after it. This reads only the ALREADY-RETURNED ``created_utc`` field — i
 ``record_bar_series``'s own adapter-selection/feed-derivation decisions, so it cannot drift out of
 sync with that logic.
 
+**goal-desk-iter-26, J-17 — a per-pair fetch window derived from the store's OWN content, plus the
+honest ``"unchanged"`` outcome.** ``_pair_window`` (below) reads ONE pair's own frozen bars via the
+SAME canonical ``BarStore.merged_bars`` accessor ``desk_screen.py``'s reference-close/history walk
+already uses (never ``bar_index``'s ``window_end_utc``, which records what an EARLIER run ASKED
+for, not what the store can prove) and picks one of two windows: the byte-identical full
+``_TOPUP_LOOKBACK_DAYS`` window ``_fetch_window_now()`` already asks for today (nothing frozen yet,
+or a frozen history that does not reach back that far — short histories keep deepening exactly as
+they do today), or — once the pair's frozen history reaches the lookback start — a TAIL window
+``[that pair's own newest frozen bar's UTC date, today]``, so the boundary session is always
+re-requested and re-merged, never assumed complete. ``_run_one_pair`` calls it once, internally, to
+build the actual fetch body; ``run_topup`` calls it again, independently, immediately BEFORE
+calling ``_run_one_pair`` for the SAME pair, purely to capture the pre-fetch provenance
+(``requested_window``/``store_frozen_from``/``store_frozen_through``/``window_basis``) for that
+pair's outcome entry — both reads see identical content because nothing is written to the store
+between them, so the two calls always agree. ``_run_one_pair``'s own call signature/return contract
+is UNCHANGED (still ``(symbol, timeframe, bar_store, bar_index, registry) -> (outcome, str|None)``)
+so every existing test that monkeypatches it wholesale keeps working unmodified.
+
+A tail window makes the vendor's "you already have this" answer — ``record_bar_series``'s own 409
+(``BarSeriesAlreadyRegistered``, ``routes.py:681``) — the NORMAL weekend/holiday response, not a
+failure: ``_run_one_pair`` now classifies a 409 specifically as ``"unchanged"`` (a vendor call ran
+and returned only bars already frozen), distinct from ``"reused"`` (a store-first exact-key hit,
+ZERO vendor calls — unchanged meaning). Every OTHER refusal keeps its verbatim detail and its
+``"failed"`` label.
+
 **J-09 — the append-only run log.** Every run's OWN already-computed outcomes are persisted, once,
 at terminal state, by the single shared writer ``desk_topup_log.record_topup_run`` — called from
 BOTH ``_work``'s two exit paths below (the ``except`` branch for a whole-job ``"failed"``, and the
@@ -123,6 +148,66 @@ def _parse_iso(value: str) -> datetime:
     return datetime.fromisoformat(value.replace("Z", "+00:00"))
 
 
+def _iso_bar_epoch(epoch: float) -> str:
+    """The SAME epoch -> ISO formatting ``bars.py``'s own ``_iso_utc``/``desk_screen.py``'s own
+    ``_iso`` use — kept as a local copy (this project's per-module tiny-helper convention) so a
+    pair's OWN frozen-bar timestamps are formatted identically wherever they are read."""
+    return (
+        datetime.fromtimestamp(epoch, tz=timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _pair_window(bar_store: BarStore, symbol: str, timeframe: str) -> dict:
+    """goal-desk-iter-26, J-17 — derive ONE pair's fetch window from that pair's OWN frozen
+    content, read via the SAME canonical ``BarStore.merged_bars`` accessor (``bars.py:557``) —
+    never ``bar_index``'s ``window_end_utc``. A single ascending ``merged_bars`` read decides one
+    of three cases:
+
+      * nothing frozen for this pair -> the byte-identical full ``_TOPUP_LOOKBACK_DAYS`` window
+        ``_fetch_window_now()`` already asks for today (``window_basis: "full_lookback"``).
+      * the pair's frozen history does NOT reach back to that lookback start -> the SAME full
+        window (``"full_lookback"``) — short histories keep deepening exactly as they do today.
+      * the pair's frozen history reaches the lookback start -> a tail window
+        ``[that pair's own newest frozen bar's UTC date, today]`` (``"tail"``). The end bound stays
+        ``_fetch_window_now()``'s wall-clock today either way.
+
+    Returns ``{"requested_window": {"start", "end"}, "store_frozen_from", "store_frozen_through",
+    "window_basis"}`` — ``store_frozen_from``/``store_frozen_through`` are that pair's own
+    earliest/newest frozen bar (full ISO timestamp), both ``None`` together when nothing is
+    frozen. A PURE read (zero vendor calls, zero writes) — safe to call more than once against the
+    same pre-fetch store state (see the module docstring's J-17 section)."""
+    lookback_start, today = _fetch_window_now()
+    bars = bar_store.merged_bars(symbol, timeframe)
+    if not bars:
+        return {
+            "requested_window": {"start": lookback_start, "end": today},
+            "store_frozen_from": None,
+            "store_frozen_through": None,
+            "window_basis": "full_lookback",
+        }
+    frozen_from = _iso_bar_epoch(bars[0].epoch)
+    frozen_through = _iso_bar_epoch(bars[-1].epoch)
+    if frozen_from[:10] > lookback_start[:10]:
+        # The pair's OWN earliest frozen bar is more recent than the lookback start -- its
+        # history does not reach back that far yet. Keep asking for the same full window so a
+        # short history keeps deepening exactly as it does today.
+        return {
+            "requested_window": {"start": lookback_start, "end": today},
+            "store_frozen_from": frozen_from,
+            "store_frozen_through": frozen_through,
+            "window_basis": "full_lookback",
+        }
+    tail_start = frozen_through[:10] + "T00:00:00Z"
+    return {
+        "requested_window": {"start": tail_start, "end": today},
+        "store_frozen_from": frozen_from,
+        "store_frozen_through": frozen_through,
+        "window_basis": "tail",
+    }
+
+
 def _copy_snapshot(snapshot: dict) -> dict:
     """A caller-safe copy (the ``progress.outcomes`` list is fresh too) so a reader mutating what
     ``snapshot()`` returns can never poison ``DeskTopupComputeManager``'s own internal state (the
@@ -148,20 +233,31 @@ def _run_one_pair(
     """Fetch+record ONE ``(symbol, timeframe)`` pair through ``record_bar_series`` (in-process —
     never a second fetch-and-record implementation) and classify the honest outcome:
 
-      * ``"reused"``  — ``record_bar_series`` answered store-first (its own ``bar_index``-backed
+      * ``"reused"``    — ``record_bar_series`` answered store-first (its own ``bar_index``-backed
         coordinator), zero vendor calls.
-      * ``"fetched"`` — a real vendor call ran and a BRAND NEW series was recorded.
-      * ``"failed"``  — ``record_bar_series`` raised (the existing ``NoDataForWindow``/
-        ``VendorTimeout``/``UnsupportedTimeframe`` taxonomy, all converted to ``HTTPException``
-        inside ``record_bar_series``, or any other unexpected error) — the detail is preserved
-        verbatim, never swallowed, and the caller (``run_topup``) continues to the remaining pairs
-        rather than aborting the whole job."""
-    start, end = _fetch_window_now()
+      * ``"fetched"``   — a real vendor call ran and a BRAND NEW series was recorded.
+      * ``"unchanged"`` — goal-desk-iter-26 (J-17): a real vendor call ran (this pair's derived
+        window, see ``_pair_window``) and the vendor answered with content already registered —
+        ``record_bar_series``'s own 409 (``BarSeriesAlreadyRegistered``). A genuine vendor call, so
+        never conflated with ``"reused"``'s zero-vendor-calls meaning.
+      * ``"failed"``    — ``record_bar_series`` raised any OTHER error (the existing
+        ``NoDataForWindow``/``VendorTimeout``/``UnsupportedTimeframe`` taxonomy, all converted to
+        ``HTTPException`` inside ``record_bar_series``, or any other unexpected error) — the detail
+        is preserved verbatim, never swallowed, and the caller (``run_topup``) continues to the
+        remaining pairs rather than aborting the whole job.
+
+    The fetch window itself is this pair's OWN derived window (``_pair_window`` — goal-desk-iter-26,
+    J-17), never the run-wide wall-clock window unconditionally."""
+    window = _pair_window(bar_store, symbol, timeframe)
+    start = window["requested_window"]["start"]
+    end = window["requested_window"]["end"]
     body = BarRecordRequest(symbol=symbol, timeframe=timeframe, start=start, end=end)
     t_before = datetime.now(timezone.utc)
     try:
         result = record_bar_series(body=body, registry=registry, store=bar_store, index=bar_index)
     except HTTPException as exc:
+        if exc.status_code == 409:
+            return "unchanged", str(exc.detail)
         return "failed", str(exc.detail)
     except Exception as exc:  # noqa: BLE001 -- never swallowed, never aborts the whole run (TC-14)
         return "failed", str(exc)
@@ -185,7 +281,12 @@ def run_topup(
     """Walk ``members x DESK_TOPUP_TIMEFRAMES``, in order, calling ``_run_one_pair`` for each pair
     — the SOLE walker; ``DeskTopupComputeManager`` and the CLI warmer both call this and nothing
     else (the ``run_strategy_comparison_report`` precedent). Returns the list of per-pair outcome
-    dicts (``{"symbol", "timeframe", "outcome", "detail"}``), in iteration order.
+    dicts, in iteration order: ``{"symbol", "timeframe", "outcome", "detail"}`` plus (goal-desk-
+    iter-26, J-17) ``"requested_window"``, ``"store_frozen_from"``, ``"store_frozen_through"``,
+    ``"window_basis"`` — that pair's own pre-fetch provenance, captured via ``_pair_window``
+    IMMEDIATELY before ``_run_one_pair`` runs (so it reflects the store's content BEFORE this run's
+    fetch, exactly as the Data Contract requires) and independent of whatever ``_run_one_pair``
+    itself is (real or a test fake) — see the module docstring's J-17 section.
 
     ``progress``, if given, is called after EACH pair with the outcome dict just appended (so a
     caller can publish incremental state). ``should_abort``, if given and it returns ``True``
@@ -198,8 +299,18 @@ def run_topup(
         for timeframe in DESK_TOPUP_TIMEFRAMES:
             if should_abort is not None and should_abort():
                 return outcomes
+            window = _pair_window(bar_store, symbol, timeframe)
             outcome, detail = _run_one_pair(symbol, timeframe, bar_store, bar_index, registry)
-            entry = {"symbol": symbol, "timeframe": timeframe, "outcome": outcome, "detail": detail}
+            entry = {
+                "symbol": symbol,
+                "timeframe": timeframe,
+                "outcome": outcome,
+                "detail": detail,
+                "requested_window": window["requested_window"],
+                "store_frozen_from": window["store_frozen_from"],
+                "store_frozen_through": window["store_frozen_through"],
+                "window_basis": window["window_basis"],
+            }
             outcomes.append(entry)
             if progress is not None:
                 progress(entry)
@@ -449,8 +560,12 @@ def main() -> int:
 
     n_fetched = sum(1 for o in outcomes if o["outcome"] == "fetched")
     n_reused = sum(1 for o in outcomes if o["outcome"] == "reused")
+    n_unchanged = sum(1 for o in outcomes if o["outcome"] == "unchanged")
     n_failed = sum(1 for o in outcomes if o["outcome"] == "failed")
-    print(f"desk top-up complete: {n_fetched} fetched, {n_reused} reused, {n_failed} failed.")
+    print(
+        f"desk top-up complete: {n_fetched} fetched, {n_reused} reused, {n_unchanged} unchanged, "
+        f"{n_failed} failed."
+    )
     return 0 if n_failed == 0 else 1
 
 
diff --git a/apps/backend/tests/test_desk_topup_compute.py b/apps/backend/tests/test_desk_topup_compute.py
index a4ccfd6..df25dc5 100644
--- a/apps/backend/tests/test_desk_topup_compute.py
+++ b/apps/backend/tests/test_desk_topup_compute.py
@@ -24,6 +24,7 @@ from __future__ import annotations
 import sys
 import threading
 import time
+from datetime import datetime, timedelta, timezone
 
 import pytest
 from fastapi.testclient import TestClient
@@ -561,6 +562,213 @@ def test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_con
     assert len(records[0]["outcomes"]) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
 
 
+# ==================================================================================================
+# goal-desk-iter-26 (J-17) -- a per-pair fetch window derived from that pair's OWN frozen content
+# (never `bar_index.window_end_utc`), plus the honest "unchanged" outcome for a vendor call that
+# genuinely ran and returned only content already frozen. `_plant_bar_series`/`_epoch_days_ago`
+# give a test control over EXACTLY which bars are frozen for a pair BEFORE the walk under test
+# runs, by writing directly through `BarStore.record` -- bypassing `record_bar_series`/the fetch
+# route (and therefore `bar_index`) entirely, so a subsequent real walk's store-first index lookup
+# genuinely misses and falls through to the injected `FakeAdapter`.
+#
+# THE ONE EXISTING-ASSERTION CARVE-OUT (reviewer-directed; see
+# `reports/reviews/goal-desk-iter-26-review.md`, CRITICAL):
+# `test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manager_triggered_one`'s
+# `assert outcome.keys() == {...}` (above, ~line 1081) is the SINGLE existing assertion this
+# iteration edits -- its four-key literal is EXTENDED to the eight keys the Data Contract mandates
+# on every per-pair outcome entry (`requested_window`/`store_frozen_from`/`store_frozen_through`/
+# `window_basis`). It is a schema mirror, not a window pin, so the iteration spec's own
+# "disclose rather than edit" exception (which covers only tests pinning the SHIPPED WINDOW) does
+# not reach it, while the DEFINITION OF DONE's unqualified "full backend suite green" does.
+# There is no implementation of the mandated contract under which a REAL run's persisted outcome
+# entries keep exactly four keys. Proven structurally, not just observed: the SAME file's
+# `test_manager_triggered_runs_persisted_outcomes_are_byte_identical_to_run_topups_own_return`
+# requires the persisted record's `outcomes` to equal `run_topup`'s own raw return value
+# byte-for-byte, so the new fields MUST originate inside `run_topup`/`_run_one_pair` itself (never
+# a downstream enrichment step) for that assertion to keep holding -- which means every path
+# (manager- and CLI-triggered alike) produces the same eight-key entries. The edit preserves the
+# assertion's stated intent (exact cross-path key-SET equality against the one shared writer's
+# schema; a drift between the CLI and manager paths still fails it) and is the ONLY edit to any
+# pre-existing assertion in this file -- TC-7 (all-reused second run) and TC-8 (resumability), the
+# two the spec names explicitly, pass untouched. See `docs/handoffs/goal-desk-iter-26-dev.md`.
+# ==================================================================================================
+
+
+def _epoch_days_ago(days: float) -> float:
+    return (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
+
+
+def _plant_bar_series(bar_store: BarStore, *, symbol: str, timeframe: str, feed: str, bars) -> dict:
+    """Directly record a bar series into `bar_store` (bypassing `record_bar_series`/the fetch
+    route and `bar_index` entirely) -- see this section's own header comment."""
+    epochs = [b.epoch for b in bars]
+    window_start = datetime.fromtimestamp(min(epochs), tz=timezone.utc).date().isoformat() + "T00:00:00Z"
+    window_end = datetime.fromtimestamp(max(epochs), tz=timezone.utc).date().isoformat() + "T00:00:00Z"
+    return bar_store.record(
+        symbol=symbol, timeframe=timeframe,
+        window_start_utc=window_start, window_end_utc=window_end,
+        feed=feed, bars=list(bars),
+    )
+
+
+def test_desk_topup_compute_reads_merged_bars_and_never_reads_bar_index_window_end_utc():
+    """A source-introspection guard (TESTING REQUIREMENTS' own explicit ask): the window
+    derivation reads the canonical `BarStore.merged_bars` accessor and never ATTRIBUTE-ACCESSES
+    `bar_index`'s `window_end_utc` field — proven by reading `desk_topup_compute.py`'s own source
+    as text (the `test_desk_ui_guards.py` pattern, applied backend-side). Matches a literal
+    `.window_end_utc` attribute access (never present in this module's CODE — only in its prose,
+    which explains why it deliberately reads `merged_bars` instead), so a real regression (some
+    future edit reaching into `bar_index`'s own `window_end_utc` column) is what this guard would
+    actually catch — proven by the counter-test below."""
+    import pathlib
+    import re
+
+    source = pathlib.Path(desk_topup_compute.__file__).read_text()
+    assert "merged_bars(" in source
+    assert re.search(r"\.window_end_utc\b", source) is None
+
+
+def test_the_window_end_utc_guard_can_fail_on_a_seeded_violation():
+    """The guard above can never fail proves nothing -- a seeded `.window_end_utc` attribute
+    access is caught."""
+    import re
+
+    seeded = 'latest = bar_index.window_end_utc\nmerged_bars(x)\n'
+    assert re.search(r"\.window_end_utc\b", seeded) is not None
+
+
+def test_pair_window_is_the_byte_identical_full_lookback_when_nothing_is_frozen(manager_env):
+    """TC-2 (goal.md J-17): a pair with NO frozen bars asks for the byte-identical full
+    `_TOPUP_LOOKBACK_DAYS` window `_fetch_window_now()` already asks for today."""
+    _universe_store, bar_store, _bar_index, _registry, _topup_run_store = manager_env
+    expected_start, expected_end = desk_topup_compute._fetch_window_now()
+
+    window = desk_topup_compute._pair_window(bar_store, "NEW", "1d")
+
+    assert window["window_basis"] == "full_lookback"
+    assert window["requested_window"] == {"start": expected_start, "end": expected_end}
+    assert window["store_frozen_from"] is None
+    assert window["store_frozen_through"] is None
+
+
+def test_pair_window_is_the_byte_identical_full_lookback_when_frozen_history_is_shorter_than_the_lookback(
+    manager_env,
+):
+    """TC-3 (goal.md J-17): a pair whose frozen history does NOT reach back to the lookback start
+    keeps asking for the SAME full window -- short histories keep deepening exactly as they do
+    today."""
+    _universe_store, bar_store, _bar_index, registry, _topup_run_store = manager_env
+    short_epoch = _epoch_days_ago(10)  # far short of the 730-day lookback
+    from app.providers.adapters.base import RawBar
+
+    _plant_bar_series(
+        bar_store, symbol="SHORT", timeframe="1d", feed=registry.config.historical_feed,
+        bars=[RawBar("SHORT", "1d", short_epoch, 10.0, 11.0, 9.0, 10.5, 500)],
+    )
+    expected_start, expected_end = desk_topup_compute._fetch_window_now()
+
+    window = desk_topup_compute._pair_window(bar_store, "SHORT", "1d")
+
+    assert window["window_basis"] == "full_lookback"
+    assert window["requested_window"] == {"start": expected_start, "end": expected_end}
+    assert window["store_frozen_from"] == desk_topup_compute._iso_bar_epoch(short_epoch)
+    assert window["store_frozen_through"] == desk_topup_compute._iso_bar_epoch(short_epoch)
+
+
+def test_pair_window_is_a_tail_window_when_frozen_history_reaches_the_lookback_start(manager_env):
+    """TC-1 (goal.md J-17): a pair whose frozen bars reach back past `_TOPUP_LOOKBACK_DAYS` asks
+    for a tail window starting at its own newest frozen bar's UTC date."""
+    _universe_store, bar_store, _bar_index, registry, _topup_run_store = manager_env
+    deep_epoch = _epoch_days_ago(desk_topup_compute._TOPUP_LOOKBACK_DAYS + 70)  # past the lookback
+    newest_epoch = _epoch_days_ago(5)
+    from app.providers.adapters.base import RawBar
+
+    _plant_bar_series(
+        bar_store, symbol="DEEP", timeframe="1d", feed=registry.config.historical_feed,
+        bars=[
+            RawBar("DEEP", "1d", deep_epoch, 10.0, 11.0, 9.0, 10.5, 500),
+            RawBar("DEEP", "1d", newest_epoch, 20.0, 21.0, 19.0, 20.5, 700),
+        ],
+    )
+    _lookback_start, expected_end = desk_topup_compute._fetch_window_now()
+    expected_tail_start = (
+        datetime.fromtimestamp(newest_epoch, tz=timezone.utc).date().isoformat() + "T00:00:00Z"
+    )
+
+    window = desk_topup_compute._pair_window(bar_store, "DEEP", "1d")
+
+    assert window["window_basis"] == "tail"
+    assert window["requested_window"] == {"start": expected_tail_start, "end": expected_end}
+    assert window["store_frozen_from"] == desk_topup_compute._iso_bar_epoch(deep_epoch)
+    assert window["store_frozen_through"] == desk_topup_compute._iso_bar_epoch(newest_epoch)
+
+
+def test_run_topup_asks_the_fake_adapter_for_the_derived_tail_window_and_records_it_on_the_outcome(
+    manager_env,
+):
+    """TC-1's end-to-end half: the walk's fake adapter genuinely RECEIVES the derived tail window
+    (proven on `adapter.fetch_bars_calls`), and the recorded outcome entry carries the identical
+    `requested_window`/`window_basis`/`store_frozen_from`/`store_frozen_through`."""
+    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
+    deep_epoch = _epoch_days_ago(desk_topup_compute._TOPUP_LOOKBACK_DAYS + 70)
+    newest_epoch = _epoch_days_ago(5)
+    from app.providers.adapters.base import RawBar
+
+    _plant_bar_series(
+        bar_store, symbol="DEEP", timeframe="1d", feed=registry.config.historical_feed,
+        bars=[
+            RawBar("DEEP", "1d", deep_epoch, 10.0, 11.0, 9.0, 10.5, 500),
+            RawBar("DEEP", "1d", newest_epoch, 20.0, 21.0, 19.0, 20.5, 700),
+        ],
+    )
+    adapter = _inject_adapter(bars=_bars())  # distinct content -> a genuinely NEW series ("fetched")
+    expected_tail_start = (
+        datetime.fromtimestamp(newest_epoch, tz=timezone.utc).date().isoformat() + "T00:00:00Z"
+    )
+
+    outcomes = run_topup(["DEEP"], bar_store, bar_index, registry)
+
+    entry = next(o for o in outcomes if o["symbol"] == "DEEP" and o["timeframe"] == "1d")
+    assert entry["outcome"] == "fetched"
+    assert entry["window_basis"] == "tail"
+    assert entry["requested_window"]["start"] == expected_tail_start
+    assert entry["store_frozen_through"] == desk_topup_compute._iso_bar_epoch(newest_epoch)
+    call = next(c for c in adapter.fetch_bars_calls if c[0] == "DEEP" and c[3] == "1d")
+    assert call[1].astimezone(timezone.utc).date().isoformat() == expected_tail_start[:10]
+
+
+def test_a_vendor_answer_holding_only_already_frozen_bars_records_unchanged_not_failed(manager_env):
+    """TC-4 (goal.md J-17): the vendor's "you already have this" answer --
+    `record_bar_series`'s own 409 (`BarSeriesAlreadyRegistered`) -- is recorded as `"unchanged"`,
+    never `"failed"`: a genuine vendor call ran, but wrote no second series file.
+    `requested_window` and `store_frozen_through` are both present on the recorded entry."""
+    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
+    already_frozen = _bars()
+    _plant_bar_series(
+        bar_store, symbol="SAME", timeframe="1d", feed=registry.config.historical_feed,
+        bars=already_frozen,
+    )
+    before_series, before_errors = bar_store.list(include_bars=False)
+    assert before_errors == []
+    _inject_adapter(bars=already_frozen)  # the vendor's answer holds ONLY content already frozen
+
+    outcomes = run_topup(["SAME"], bar_store, bar_index, registry)
+
+    entry = next(o for o in outcomes if o["symbol"] == "SAME" and o["timeframe"] == "1d")
+    assert entry["outcome"] == "unchanged"
+    assert entry["detail"] is not None
+    assert entry["requested_window"] is not None
+    assert entry["store_frozen_through"] is not None
+
+    after_series, after_errors = bar_store.list(include_bars=False)
+    assert after_errors == []
+    # No second series file was written for this pair -- the store gained nothing new.
+    same_before = [m for m in before_series if m["symbol"] == "SAME" and m["timeframe"] == "1d"]
+    same_after = [m for m in after_series if m["symbol"] == "SAME" and m["timeframe"] == "1d"]
+    assert len(same_before) == 1
+    assert same_after == same_before
+
+
 # ==================================================================================================
 # Routes -- GET-never-computes, single-flight/cancel through HTTP, idle-cancel 409 (TC-15).
 # ==================================================================================================
@@ -875,7 +1083,17 @@ def test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manag
     assert len(record["outcomes"]) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
     assert {o["outcome"] for o in record["outcomes"]} == {"fetched"}
     for outcome in record["outcomes"]:
-        assert outcome.keys() == {"symbol", "timeframe", "outcome", "detail"}
+        # goal-desk-iter-26 (J-17), the ONE reviewer-sanctioned carve-out to this iteration's
+        # "existing assertions pass unmodified" rule: this pin is a mirror of the SHARED writer's
+        # per-pair schema, extended -- not relaxed -- with the four Data-Contract fields every path
+        # now carries. It stays an exact key-SET equality, so cross-path schema drift (the property
+        # this test's own name claims) still fails it. See the section header below and
+        # `docs/handoffs/goal-desk-iter-26-dev.md` for why no implementation of the mandated
+        # contract can keep a real run's outcome entries at four keys.
+        assert outcome.keys() == {
+            "symbol", "timeframe", "outcome", "detail",
+            "requested_window", "store_frozen_from", "store_frozen_through", "window_basis",
+        }
 
 
 def test_cli_with_no_universe_snapshot_persists_no_run_record(tmp_path, monkeypatch):
diff --git a/apps/backend/tests/test_desk_topup_log.py b/apps/backend/tests/test_desk_topup_log.py
index df9212c..cf494a3 100644
--- a/apps/backend/tests/test_desk_topup_log.py
+++ b/apps/backend/tests/test_desk_topup_log.py
@@ -242,3 +242,53 @@ def test_resolve_desk_topup_log_dir_defaults_to_a_sibling_of_the_universe_dir(mo
 def test_resolve_desk_topup_log_dir_env_override(monkeypatch):
     monkeypatch.setenv("TAPEOLOGY_DESK_TOPUP_LOG_DIR", "/tmp/custom-topup-log-dir")
     assert resolve_desk_topup_log_dir("/some/root/.data/universe") == "/tmp/custom-topup-log-dir"
+
+
+# --- goal-desk-iter-26 (J-17): the store is a pure passthrough for whatever per-pair outcome shape
+# a caller gives it -- it validates NOTHING about outcome-dict keys, so the four new fields
+# (`requested_window`/`store_frozen_from`/`store_frozen_through`/`window_basis`) need no store-side
+# code change; these tests document that the passthrough genuinely holds for the new shape, and
+# that an OLD-shape (pre-iter-26) run record still round-trips exactly as it always has (the
+# "legacy runs served verbatim, never backfilled" DoD clause, at the store layer). ------------------
+
+J17_OUTCOMES = [
+    {
+        "symbol": "AAA", "timeframe": "1d", "outcome": "unchanged",
+        "detail": "already registered", "requested_window": {"start": "2024-07-01T00:00:00Z", "end": "2026-07-30T00:00:00Z"},
+        "store_frozen_from": "2024-06-01T00:00:00.000000Z", "store_frozen_through": "2026-07-25T00:00:00.000000Z",
+        "window_basis": "tail",
+    },
+    {
+        "symbol": "BBB", "timeframe": "1d", "outcome": "fetched", "detail": None,
+        "requested_window": {"start": "2024-07-30T00:00:00Z", "end": "2026-07-30T00:00:00Z"},
+        "store_frozen_from": None, "store_frozen_through": None, "window_basis": "full_lookback",
+    },
+]
+
+
+def test_record_and_list_round_trip_the_new_j17_per_pair_fields_verbatim(tmp_path):
+    store = TopupRunStore(tmp_path / "topup_runs")
+    meta = _record_sample(store, outcomes=J17_OUTCOMES)
+
+    assert meta["outcomes"] == J17_OUTCOMES
+    records, errors = store.list()
+    assert errors == []
+    assert records[0]["outcomes"] == J17_OUTCOMES
+
+
+def test_a_legacy_pre_iter26_run_record_round_trips_without_the_new_fields(tmp_path):
+    """A run recorded BEFORE this iteration's code shipped never gains the four new fields at
+    read time -- `list()` serves it exactly as it was written, absent fields absent (never a
+    computed or backfilled value)."""
+    store = TopupRunStore(tmp_path / "topup_runs")
+    legacy_outcomes = [{"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None}]
+    meta = _record_sample(store, outcomes=legacy_outcomes)
+
+    assert meta["outcomes"] == legacy_outcomes
+    for outcome in meta["outcomes"]:
+        assert "window_basis" not in outcome
+        assert "requested_window" not in outcome
+
+    records, errors = store.list()
+    assert errors == []
+    assert records[0]["outcomes"] == legacy_outcomes
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 1572e67..e56637b 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -806,19 +806,49 @@ function DeskHistoryTable({
 // (per-outcome counts, every failed pair's detail verbatim, the honest unreached-pairs count) for
 // the latest run ONLY — the one entry the backend's `latest` field actually carries `outcomes` for.
 // Read-only, no click-through, no new control (this iteration's own OUT OF SCOPE text). -----------
+//
+// goal-desk-iter-26 (J-17): the counts line gains an `unchanged` bucket (a vendor call ran and
+// returned only bars already frozen -- distinct from `reused`'s zero-vendor-calls meaning); a new
+// descriptive line states how many pairs asked for a tail window vs. the full lookback window
+// (`topupWindowBasisCounts` -- a plain tally, nothing derived); and each already-rendered failed
+// pair additionally shows its own recorded `requested_window`. A run recorded BEFORE this
+// iteration's code shipped lacks all four new fields on every outcome entry -- rendered as the
+// honest `WINDOW_BASIS_NOT_RECORDED` fallback, never computed or backfilled. No new section, no
+// new control, no new ranked-table column (J-16's measured width contract stays untouched).
 
 function topupOutcomeCounts(outcomes: DeskTopupOutcome[]): {
   reused: number;
   fetched: number;
+  unchanged: number;
   failed: number;
 } {
   return {
     reused: outcomes.filter((o) => o.outcome === "reused").length,
     fetched: outcomes.filter((o) => o.outcome === "fetched").length,
+    unchanged: outcomes.filter((o) => o.outcome === "unchanged").length,
     failed: outcomes.filter((o) => o.outcome === "failed").length,
   };
 }
 
+// goal-desk-iter-26 (J-17) -- the honest fallback for a run recorded BEFORE this iteration's code
+// shipped: legacy runs never carry `window_basis` on any outcome entry, and the fields are never
+// computed or backfilled at read time (the established J-08/J-11/J-13 legacy-absence pattern).
+const WINDOW_BASIS_NOT_RECORDED = "window basis not recorded in this run";
+
+// A plain tally of the served payload's own `window_basis` field, nothing derived (the
+// `topupOutcomeCounts` precedent) -- `null` when ANY outcome in the run lacks `window_basis`
+// (a single shared writer lands a run's outcomes all at once, so a run is either entirely
+// pre-iter-26 or entirely post-iter-26 -- never a mix).
+function topupWindowBasisCounts(
+  outcomes: DeskTopupOutcome[],
+): { tail: number; full_lookback: number } | null {
+  if (outcomes.some((o) => o.window_basis === undefined)) return null;
+  return {
+    tail: outcomes.filter((o) => o.window_basis === "tail").length,
+    full_lookback: outcomes.filter((o) => o.window_basis === "full_lookback").length,
+  };
+}
+
 function TopupRunRow({ meta }: { meta: DeskTopupRunMeta }) {
   return (
     <tr data-testid="desk-topup-run-row" className="border-b border-slate-800/60 last:border-b-0">
@@ -872,6 +902,7 @@ function TopupRunsTable({ runs }: { runs: DeskTopupRunMeta[] }) {
 // reached" claim of completeness the run didn't make; it is simply omitted when zero).
 function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
   const counts = topupOutcomeCounts(run.outcomes);
+  const windowBasisCounts = topupWindowBasisCounts(run.outcomes);
   const unreached = run.pairs_total - run.pairs_attempted;
   const failedOutcomes = run.outcomes.filter((o) => o.outcome === "failed");
   return (
@@ -888,7 +919,8 @@ function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
           {run.pairs_attempted} of {run.pairs_total} pairs attempted
         </span>
         <span data-testid="desk-topup-run-latest-counts">
-          {counts.reused} reused · {counts.fetched} fetched · {counts.failed} failed
+          {counts.reused} reused · {counts.fetched} fetched · {counts.unchanged} unchanged ·{" "}
+          {counts.failed} failed
         </span>
         {unreached > 0 && (
           <span data-testid="desk-topup-run-latest-unreached" className="text-amber-200/70">
@@ -896,6 +928,13 @@ function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
           </span>
         )}
       </div>
+      <div data-testid="desk-topup-run-latest-window-basis" className="text-xs text-slate-400">
+        {windowBasisCounts === null
+          ? WINDOW_BASIS_NOT_RECORDED
+          : `${windowBasisCounts.tail} pair${windowBasisCounts.tail === 1 ? "" : "s"} asked for a ` +
+            `tail window · ${windowBasisCounts.full_lookback} pair` +
+            `${windowBasisCounts.full_lookback === 1 ? "" : "s"} asked for the full lookback window`}
+      </div>
       {failedOutcomes.length > 0 && (
         <div data-testid="desk-topup-run-latest-failed">
           <h4 className="mb-1 text-[11px] font-medium text-slate-500">
@@ -914,6 +953,13 @@ function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
                 —{" "}
                 <span data-testid="desk-topup-run-latest-failed-detail">
                   {outcome.detail ?? "(no detail recorded)"}
+                </span>{" "}
+                <span data-testid="desk-topup-run-latest-failed-window" className="text-slate-500">
+                  ·{" "}
+                  {outcome.requested_window
+                    ? `requested ${outcome.requested_window.start.slice(0, 10)} → ` +
+                      `${outcome.requested_window.end.slice(0, 10)}`
+                    : WINDOW_BASIS_NOT_RECORDED}
                 </span>
               </li>
             ))}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 951d3fe..c237b61 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -940,11 +940,22 @@ export interface DeskScreenComputeSnapshot {
 // The desk bar top-up compute manager's job snapshot (`DeskTopupComputeManager`, shipped J-02,
 // iter-2), served VERBATIM by GET/POST `/research/desk/topup/compute`. THIS iteration (J-04) is
 // its first-ever UI consumer (a Top-up button on `/desk`) -- read-only wiring, zero shape change.
+// goal-desk-iter-26 (J-17): `requested_window`/`store_frozen_from`/`store_frozen_through`/
+// `window_basis` are additive to every per-pair outcome entry of a run recorded from THIS
+// iteration onward -- a run recorded BEFORE this iteration's code shipped never carries them
+// (`undefined` on that entry, never backfilled or computed at read time; the page renders the
+// honest "window basis not recorded in this run" fallback for such a run instead). `"unchanged"`
+// is a NEW outcome value: a vendor call ran and returned only bars already frozen (distinct from
+// `"reused"`'s zero-vendor-calls store-first hit).
 export interface DeskTopupOutcome {
   symbol: string;
   timeframe: string;
-  outcome: "reused" | "fetched" | "failed";
+  outcome: "reused" | "fetched" | "unchanged" | "failed";
   detail: string | null;
+  requested_window?: { start: string; end: string };
+  store_frozen_from?: string | null;
+  store_frozen_through?: string | null;
+  window_basis?: "tail" | "full_lookback";
 }
 
 export interface DeskTopupComputeProgress {
diff --git a/incredible_auto_dev/.claude/anti-patterns/27-software-guards-without-reset-reason.md b/incredible_auto_dev/.claude/anti-patterns/27-software-guards-without-reset-reason.md
new file mode 100644
index 0000000..2ed0f1a
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/27-software-guards-without-reset-reason.md
@@ -0,0 +1,9 @@
+## 27. Iterating on software guards without reading the hardware's own reset-reason register
+
+**Pattern:** A machine keeps failing in a way that looks like a resource problem, and each occurrence produces a more elaborate software mitigation — while the platform has been recording, and printing, the actual cause the whole time. Observed: a host hard-reset seven times in eleven days under goal-mode load. Reset #6 produced the machine-global aggregate bound (anti-pattern 26); reset #7 on 2026-07-30 17:14:08 then happened with that bound deployed to both projects, armed, and green on every single check — masks inside the machine budget, `10G + 10G` under a 22G budget, boost off *and* persisted, QA browsers confined, both engines visible to each other in the registry. The 1 Hz sampler recorded 65 °C, 26 W, load 6.54 on 8 threads, 11.5 GB free and memory PSI 0.00 at T-1s. Every software hypothesis was refuted, and the answer was one `journalctl -k` line that had been printed on every boot since the first reset: `x86/amd: Previous system reset reason [0x08000800]: an uncorrected error caused a data fabric sync flood event` — an uncorrectable SoC/Infinity-Fabric error, present on seven of the last ten boots, one of which fired at load 1.53 and 22 W.
+
+**Why it fails:** A hardware-asserted reset leaves exactly the same evidence as a mysterious software crash — nothing. No panic, no OOM kill, no thermal event, no watchdog, no vmcore, and (because journald syncs every five minutes by default) not even the last minutes of log. That absence reads as "we haven't instrumented enough yet", which is why the natural response is another guard rather than another *source*. Meanwhile the platform's postmortem registers — the AMD reset-reason MSR, `/sys/fs/pstore`, RAS/MCE logs — sit outside the process the investigation is looking at, and no amount of care inside the software layer can reach them. The failure compounds: each new guard passes its own tests, gets certified, and becomes evidence that the *next* reset must have a subtler software cause. A near-idle occurrence (load 1.53) should have falsified the load hypothesis outright, but a guard already built is hard to argue with. Load correlation was real yet incidental — concurrency changes how often marginal hardware trips, not whether it is marginal.
+
+**Prevention:** When a machine fails as a machine — resets, freezes, spontaneous reboots, corruption — read the platform's own postmortem **first**, before writing a single mitigation: `journalctl -k -b 0 | grep -i 'reset reason'`, `/sys/fs/pstore`, `rasdaemon`/`mcelog`, `dmidecode` for firmware age. One line there outranks any amount of software telemetry, because it is the only witness that survives the OS never being notified. Then make it automatic and self-documenting, so the register is read for you and the next incident arrives with evidence attached: a reader wired into preflight and the doctor (`host-guard/reset-forensics.sh`, doctor row `reset-reason`), an idempotent postmortem bundle captured *before* anything sweeps the state that says who was running, fsync'd recording that outlives a power cut (1 Hz sampler, machine-wide event ledger, `journald SyncIntervalSec=15s`), and boot-id-keyed staleness so locks and pidfiles from the dead boot self-clear instead of being silently believed. Two discipline rules follow. **Distinguish "unreadable" from "clean"** — a checker that cannot read the register must report UNKNOWN, never PASS, or it certifies every host as healthy; and classify what it reads, since an ordinary `reboot` also writes a reset reason (`software wrote 0x6 to reset control register 0xCF9`) and counting it would cry wolf forever. **State plainly what software can and cannot do**: once the cause is hardware, the honest mitigations are firmware/BIOS updates, memory-timing changes, memtest and RMA — plus, at most, capping concurrency to shrink the exposure window. Tightening a CPU mask further, on a fault that fires at idle, is theatre that costs throughput and buys nothing.
+
+---
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
index 6a10395..02ec626 100644
--- a/incredible_auto_dev/.claude/anti-patterns/README.md
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -3,7 +3,7 @@
 One file per numbered entry, split from the former monolith (CTX-12) so a reader loads
 only what matches the situation: scan this index, open the matching `<NN>-<slug>.md`,
 nothing else. Numbering is FROZEN forever — files keep their original `## <N>. <title>`
-headings; the next new entry takes the next free number (24) as `<NN>-<slug>.md` plus a
+headings; the next new entry takes the next free number (28) as `<NN>-<slug>.md` plus a
 row here (maintenance protocol §2).
 
 | # | Entry | Applies when | Rule (one line) |
@@ -34,3 +34,4 @@ row here (maintenance protocol §2).
 | 24 | [24-evidence-chasing-iterations.md](24-evidence-chasing-iterations.md) | evaluator/decomposer evidence demands | Evidence expires with change, not time; capture gaps ride the make-up lane or Depth: evidence — never an iteration goal |
 | 25 | [25-self-justifying-governor-bypass.md](25-self-justifying-governor-bypass.md) | gates on agent behavior | A governor must validate against signals the governed agent cannot author; a self-written justification line is a suggestion, not a gate |
 | 26 | [26-per-scope-caps-no-machine-aggregate.md](26-per-scope-caps-no-machine-aggregate.md) | resource caps on shared hardware | Per-scope ceilings need a machine-level aggregate over a registry of live consumers, plus verification of every host assumption they rest on |
+| 27 | [27-software-guards-without-reset-reason.md](27-software-guards-without-reset-reason.md) | a machine resets, freezes, or reboots itself | Read the platform's own postmortem registers (reset reason, pstore, RAS) BEFORE building another software guard; "unreadable" is never "clean" |
diff --git a/incredible_auto_dev/.claude/commands/goal-status.md b/incredible_auto_dev/.claude/commands/goal-status.md
index ebcfada..0feaaf6 100644
--- a/incredible_auto_dev/.claude/commands/goal-status.md
+++ b/incredible_auto_dev/.claude/commands/goal-status.md
@@ -21,6 +21,21 @@ the engine, dispatch agents, or write anything.
    interrupted/orphaned (e.g. a Ctrl+C that never reached the detached engine) —
    say so and point to `/goal-resume <sid>`. Also point the user at the full
    timestamped log: `tail -f runs/goal-session-<sid>/engine.log`.
+   **Distinguish a machine reset from an orphan.** Compare the pid file's mtime
+   against this boot: `ls -l --time-style=+%s runs/goal-session-<sid>/engine.pid`
+   versus `awk '/^btime /{print $2}' /proc/stat`. A pid file written BEFORE the
+   boot means the machine went down under the engine — a hardware event, not
+   something the session did wrong. Report it that way, with:
+   - **when** it died — the last pre-boot row of `~/.cache/iad/host-guard/hwmon/hwmon.csv`
+     (or `logs/hwmon/hwmon.csv`), which is fsync'd per second and outlives the journal;
+   - **what it was doing** — `current_iter` from `session.json` plus the last line
+     of `runs/goal-session-<sid>/telemetry.jsonl`, and the machine-wide ledger
+     `~/.cache/iad/host-guard/events.jsonl` for the cross-repo picture;
+   - **why** — `scripts/automation/host-guard/reset-forensics.sh check` and the
+     postmortem at `~/.cache/iad/host-guard/postmortems/latest.md`.
+   Then point at `/goal-resume <sid>`, which clears the stale locks itself. Say
+   plainly that a reset of this class is a hardware fault (see `docs/host-guard.md`
+   § After a hardware reset), so resuming is safe and the iteration is not lost.
 6. Summarize plainly whether the session is **running**, **paused** (and exactly
    how to resume — e.g. review the blueprint then `/goal-resume`; for
    `AWAITING_INTENT_REVIEW` point at `runs/goal-session-<sid>/intent-review.md`,
diff --git a/incredible_auto_dev/commands/goal-status.md b/incredible_auto_dev/commands/goal-status.md
index ebcfada..0feaaf6 100644
--- a/incredible_auto_dev/commands/goal-status.md
+++ b/incredible_auto_dev/commands/goal-status.md
@@ -21,6 +21,21 @@ the engine, dispatch agents, or write anything.
    interrupted/orphaned (e.g. a Ctrl+C that never reached the detached engine) —
    say so and point to `/goal-resume <sid>`. Also point the user at the full
    timestamped log: `tail -f runs/goal-session-<sid>/engine.log`.
+   **Distinguish a machine reset from an orphan.** Compare the pid file's mtime
+   against this boot: `ls -l --time-style=+%s runs/goal-session-<sid>/engine.pid`
+   versus `awk '/^btime /{print $2}' /proc/stat`. A pid file written BEFORE the
+   boot means the machine went down under the engine — a hardware event, not
+   something the session did wrong. Report it that way, with:
+   - **when** it died — the last pre-boot row of `~/.cache/iad/host-guard/hwmon/hwmon.csv`
+     (or `logs/hwmon/hwmon.csv`), which is fsync'd per second and outlives the journal;
+   - **what it was doing** — `current_iter` from `session.json` plus the last line
+     of `runs/goal-session-<sid>/telemetry.jsonl`, and the machine-wide ledger
+     `~/.cache/iad/host-guard/events.jsonl` for the cross-repo picture;
+   - **why** — `scripts/automation/host-guard/reset-forensics.sh check` and the
+     postmortem at `~/.cache/iad/host-guard/postmortems/latest.md`.
+   Then point at `/goal-resume <sid>`, which clears the stale locks itself. Say
+   plainly that a reset of this class is a hardware fault (see `docs/host-guard.md`
+   § After a hardware reset), so resuming is safe and the iteration is not lost.
 6. Summarize plainly whether the session is **running**, **paused** (and exactly
    how to resume — e.g. review the blueprint then `/goal-resume`; for
    `AWAITING_INTENT_REVIEW` point at `runs/goal-session-<sid>/intent-review.md`,
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
index faadd1f..9c0a027 100644
--- a/incredible_auto_dev/docs/host-guard.md
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -51,9 +51,23 @@ So a second file, owned by the machine rather than by any repo, declares what
 HOST_GUARD_GLOBAL_CPU_LIST="0-3,8-11"   # every session's mask must be a SUBSET
 HOST_GUARD_GLOBAL_MEMORY_BUDGET="22G"   # Σ over projects of max(MemoryHigh)
 HOST_GUARD_REQUIRE_BOOST_OFF=1          # /sys/.../cpufreq/boost must read 0
-HOST_GUARD_GLOBAL_ON_CONFLICT=pause     # only 'pause' is implemented
+HOST_GUARD_MAX_ENGINES=1                # concurrent goal engines (absent = unlimited)
 ```
 
+`HOST_GUARD_MAX_ENGINES` caps how many goal-mode engines may run at once across
+the whole machine. Over the cap, the **junior** engine takes the ordinary
+resumable `AWAITING_HOST_GUARD` pause and continues when the senior finishes;
+the senior only warns. Absent ⇒ unlimited.
+
+It exists for one situation: a host whose resets turn out to be **hardware**
+(see § After a hardware reset). Nothing a guard can do prevents those, so a
+narrower CPU mask is theatre — but be clear-eyed that this knob is not a fix
+either. It buys **exposure time, not prevention**: fewer hours under load means
+fewer chances to trip, and nothing more. On the incident host the fault fired at
+load 1.53 as readily as under two concurrent sessions, so the cap was released
+within hours in favour of the real remediation. Its durable use is narrower and
+better: pinning a soak week to a single project so one variable moves at a time.
+
 Every guarded context publishes a record (pid, start time, boot id, project,
 mask, memory ceiling) into a registry under
 `${CHAIN_TMP_ROOT:-~/.cache/iad}/host-guard/registry/`, so any session can see
@@ -106,6 +120,115 @@ cat /sys/devices/system/cpu/cpufreq/boost      # must print 0
 `scripts/automation/doctor.sh --only cpu-boost` reports both the live knob and
 whether the rule that survives a reboot exists.
 
+## After a hardware reset — root-cause runbook
+
+**Read this before tightening anything.** On 2026-07-30 17:14:08 this host reset
+with every host-guard mitigation in force: both projects inside `0-3,8-11`,
+10G+10G against a 22G budget, boost off and persisted, QA browsers confined,
+both engines registered in the machine-global registry, every check green. At
+T-1s the 1 Hz sampler recorded 65 °C, 26 W, load 6.54, 11.5 GB free, memory PSI
+0.00. The cause was never visible to any software check — the CPU printed it on
+the next boot:
+
+```
+x86/amd: Previous system reset reason [0x08000800]: an uncorrected error
+         caused a data fabric sync flood event
+```
+
+A data fabric sync flood is an **uncorrectable SoC/Infinity-Fabric error**. The
+hardware asserts reset immediately; the kernel is never notified, so there is no
+panic, no OOM, no thermal event and no log — which is exactly why six earlier
+resets were misread as load problems. Seven of the last ten boots carried a
+fault-class line, and one of them fired at load 1.53 and 22 W: this is hardware
+**marginality**, not a load limit. Concurrency only changes how often it trips.
+
+The chain's job is therefore to surface, preserve, recover and cap — never to
+pretend it can prevent this:
+
+```bash
+scripts/automation/host-guard/reset-forensics.sh check       # what the platform says
+scripts/automation/host-guard/reset-forensics.sh report      # the newest postmortem
+scripts/automation/doctor.sh --only reset-reason             # same verdict as a row
+```
+
+Every engine preflight writes one idempotent bundle per dead boot into
+`~/.cache/iad/host-guard/postmortems/<boot-id>.md`: the verbatim reset line, the
+fault streak, the registry records naming which projects and sessions were
+running, the final pre-reset second of hardware telemetry from every sampler,
+those sessions' telemetry/engine-log tails, and the machine-wide event ledger.
+Run it **before** resuming a session — the preflight registry sweep is what
+erases the "who was running" evidence.
+
+### Fixing it (all need root; run them yourself, one change per soak week)
+
+```bash
+# 1. journald syncs every 5 min by default — the 07-30 reset erased the final
+#    3m42s of journal. 15 s keeps the tail.
+sudo mkdir -p /etc/systemd/journald.conf.d \
+  && printf '[Journal]\nSyncIntervalSec=15s\n' | sudo tee /etc/systemd/journald.conf.d/99-iad-sync.conf \
+  && sudo systemctl restart systemd-journald
+
+# 2. rasdaemon records the memory/fabric error itself (address, DIMM) — this is
+#    what turns "sync flood" into an actionable RMA or firmware bug report.
+sudo apt-get install -y rasdaemon && sudo systemctl enable --now rasdaemon
+
+# 3. One-time: firmware crash records the kernel could not write.
+sudo sh -c 'ls -la /sys/fs/pstore/ && head -c 4000 /sys/fs/pstore/* 2>/dev/null'
+
+# 4. BIOS/AGESA age is the single most common fix for this signature.
+sudo dmidecode -s bios-version && sudo dmidecode -s bios-release-date
+
+# 5. The definitive DRAM check — run a full pass overnight.
+sudo apt-get install -y memtest86+ && sudo update-grub
+```
+
+Then, in this order, one per week so causality stays readable: **update the
+BIOS**; set memory to **baseline JEDEC** instead of the EXPO/XMP profile; if
+memtest reports errors, reseat/swap the SO-DIMM and RMA. A commonly reported
+workaround for this signature is limiting deep C-states (it costs idle power and
+reverts on reboot):
+
+```bash
+for f in /sys/devices/system/cpu/cpu*/cpuidle/state[2-9]/disable; do echo 1 | sudo tee "$f" >/dev/null; done
+```
+
+`doctor.sh --only ras-logging` verifies what it can read without root (the
+journald drop-in and the rasdaemon unit) and stays silent on hosts that have no
+reset history.
+
+**Acceptance:** seven consecutive days with `reset-reason` reporting CLEAN on
+every boot. That replaces the "7-day zero-unclean-shutdown soak" HOST-1 claimed,
+which reset #7 refuted.
+
+## Machine-global hardware sampler
+
+One 1 Hz sampler covers the machine — it is the only artifact that survives a
+power-cut with its last second intact, because it fsyncs every line.
+
+```bash
+cp scripts/automation/host-guard/iad-hwmon.service ~/.config/systemd/user/
+systemctl --user daemon-reload && systemctl --user enable --now iad-hwmon.service
+loginctl show-user "$USER" --property=Linger      # must print Linger=yes
+tail -2 ~/.cache/iad/host-guard/hwmon/hwmon.csv
+```
+
+No root is needed (it is a `--user` unit). It writes
+`~/.cache/iad/host-guard/hwmon/hwmon.csv`, restarts itself after every reset,
+and keeps two rotated generations (~8 days). Per-repo samplers remain as a
+fallback: an engine preflight only starts one when no machine-global sampler is
+fresh, so migrating a project is just retiring its old unit. If a project still
+runs its own `hwmon-log.service`, disable it after enabling this one.
+
+## Machine-wide event ledger
+
+`~/.cache/iad/host-guard/events.jsonl` — one fsync'd JSON line per chain event
+for the WHOLE machine (engine start/stop, iteration start, every agent dispatch
+and its exit code, each healthy aggregate verdict, every pause). It exists
+because after a reset nothing could answer "what were both repos doing in the
+final seconds?": the aggregate verdict was silent when it passed,
+`telemetry.jsonl` is per-session and never fsync'd, and `engine.log` only exists
+in interactive mode. Filter by `.project` for one repo, `.boot` for one boot.
+
 ## Browser QA confinement
 
 Confining process *trees* is not enough for browser QA. The Chrome MCP does not
@@ -191,10 +314,19 @@ Pump browsers are made safe by affinity instead, which needs no name.
 7. **Browser confinement** (`host-guard/browser-confine.sh`) — QA browsers and
    Chrome-MCP servers that escaped the process tree, see below.
 8. **Forensics sampler** (`host-guard/hwmon-log.sh`) — 1 Hz temps/power/
-   pressure/memory to `<repo>/logs/hwmon/hwmon.csv`, fsync per line, so the
-   final pre-reset second survives a hard reset. `{run|start|stop|status|watch}`;
-   `status`/`start` recognize an externally-run sampler (e.g. a systemd user
-   unit running `run`) by csv freshness and never double-run.
+   pressure/memory/clock, fsync per line, so the final pre-reset second survives
+   a hard reset. Writes `~/.cache/iad/host-guard/hwmon/hwmon.csv` under the
+   machine-global unit, else `<repo>/logs/hwmon/hwmon.csv`.
+   `{run|start|stop|status|watch}`; `status`/`start` recognize an externally-run
+   sampler — including the machine-global one — by csv freshness and never
+   double-run.
+9. **Reset-reason forensics** (`host-guard/reset-forensics.sh`) — reads the
+   platform's own reset register each boot and freezes a postmortem bundle when
+   the last boot died. `{check|ensure-postmortem|report}`; doctor row
+   `reset-reason`. The only layer that can explain a reset no software caused.
+10. **Machine event ledger** (`hg_event`, `lib/host-guard-registry.sh`) — one
+   fsync'd line per chain event for the whole machine, including the healthy
+   aggregate verdict that used to be silent.
 
 ## When `AWAITING_HOST_GUARD` fires
 
@@ -219,3 +351,19 @@ still collectively unbounded, a QA browser could keep a pre-confinement CPU
 mask, and the boost mitigation had silently lapsed at a reboot. Incident
 forensics and the cap-widening verification ladder live in the originating
 project: `trendora/project-extensions/host-guard/README.md`.
+
+A **seventh** reset on 2026-07-30 17:14:08 ended that line of reasoning. It
+happened with the machine-global layer deployed to both projects, armed, and
+green on every check. The answer had been in the kernel log the whole time —
+`Previous system reset reason [0x08000800]: an uncorrected error caused a data
+fabric sync flood event`, present on seven of the last ten boots, once at load
+1.53. The root cause is **hardware** (DDR5/Infinity-Fabric marginality on
+non-ECC SO-DIMMs, BIOS 1.26 dated 09/2025), and no CPU mask, memory ceiling or
+browser confinement can prevent it.
+
+Three generations of guard were built to stop something the CPU was already
+naming on every boot. That is the lesson recorded as anti-pattern 27: **read the
+platform's own postmortem registers before iterating on software mitigations.**
+Since then these layers surface the hardware's verdict, preserve the evidence,
+recover honestly, and cap concurrency — see § After a hardware reset for the
+remediation that actually applies.
diff --git a/incredible_auto_dev/docs/improvement-roadmap.md b/incredible_auto_dev/docs/improvement-roadmap.md
index 557ba36..a678f75 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.md
@@ -4349,8 +4349,191 @@ Machine-global aggregate bound + QA-browser confinement + host-assumption verifi
   (`run-phase.sh` Branch-QA + Branch-UI) onto one shared browser. Pump browsers are made
   safe by affinity instead, which needs no name.
 - **Failure-mode entry:** `.claude/anti-patterns/26-per-scope-caps-no-machine-aggregate.md`.
-- **Owner action outstanding:** re-apply and PERSIST boost-off (docs/host-guard.md
-  § Boost persistence). Until then the engine pauses `AWAITING_HOST_GUARD` by design.
-- **Verification still owed (G8-class):** subtree-pull both projects, a supervised
-  concurrent `/goal-step` per project verifying the live union stays inside `0-3,8-11`,
-  then the 7-day zero-unclean-shutdown soak (trendora README Stage E).
+- **Owner action outstanding:** ~~re-apply and PERSIST boost-off~~ — **DONE 2026-07-29
+  19:40**: `/etc/tmpfiles.d/cpufreq-boost.conf` installed and the knob reads 0 (verified
+  on-disk 2026-07-30).
+- **Verification still owed (G8-class):** ~~subtree-pull both projects~~ — **DONE
+  2026-07-29** (tapeology `8c737c1` 19:45, trendora `e402ce9b` 19:58; all 13 files
+  byte-identical). ~~7-day zero-unclean-shutdown soak~~ — **REFUTED, see addendum.**
+
+**ADDENDUM 2026-07-30 — the soak failed and the root cause is HARDWARE.**
+
+Reset #7 at **2026-07-30 17:14:08** happened with everything above deployed, armed and
+green: both projects inside `0-3,8-11`, `10G+10G` under the 22G budget, boost off and
+persisted, QA browsers and MCP servers confined, both engines registered in the
+machine-global registry, `AWAITING_HOST_GUARD` count 0. At T-1s the 1 Hz sampler recorded
+65 °C, 26 W, load 6.54 on 8 threads, 11.5 GB free, memory PSI 0.00. Machine back up 21 s
+later.
+
+The cause was never visible to any software check. The CPU prints it on every boot:
+
+```
+x86/amd: Previous system reset reason [0x08000800]: an uncorrected error
+         caused a data fabric sync flood event
+```
+
+Present on **7 of the last 10 boots**; one of those resets fired at load 1.53 / 22 W, which
+falsifies the load hypothesis outright. This is an uncorrectable SoC/Infinity-Fabric error
+— DDR5/fabric marginality on non-ECC SO-DIMMs, BIOS 1.26 dated 09/2025 — and the hardware
+asserts reset with the kernel never notified. **No CPU mask, memory ceiling, or browser
+confinement can prevent this class.** HOST-1's mitigations were correct as far as they go
+(the mask union and memory sum WERE real defects) but they were never sufficient, and
+tightening them further is theatre.
+
+Recorded as `.claude/anti-patterns/27-software-guards-without-reset-reason.md`: read the
+platform's own postmortem registers BEFORE iterating on software guards. Remediation is
+firmware/hardware and belongs to the operator (docs/host-guard.md § After a hardware
+reset). The framework's job is now surface / preserve / recover / cap — HOST-2..HOST-9.
+
+- **Honesty note:** `HOST_GUARD_GLOBAL_ON_CONFLICT` shipped in 8a7a400 as a documented
+  knob that NO code ever read. It was deleted rather than implemented — pause is the only
+  sane semantic and is already hardwired.
+- **New acceptance test** (replaces the refuted soak): 7 consecutive days with
+  `doctor.sh --only reset-reason` reporting CLEAN on every boot.
+
+### HOST-2 — IN-PROGRESS 2026-07-30 · P1 · M · LOW
+
+- **Problem:** seven resets were debugged as software load problems while the kernel
+  printed the cause on every boot. Nothing read it, and nothing preserved the evidence:
+  the engine preflight's `hg_sweep` deletes exactly the registry records that say which
+  projects and sessions were running when the machine died.
+- **Current state:** `scripts/automation/host-guard/reset-forensics.sh` (new);
+  `doctor.sh` row `reset-reason`; `run-goal.sh:1026` `_host_guard_reset_forensics` called
+  at the TOP of `preflight_host_guard`, before the sweep at `:1088`.
+- **Change spec:** read the current boot's `Previous system reset reason` line
+  (journalctl → `/var/log/kern.log` → UNKNOWN; never dmesg, `dmesg_restrict` is on).
+  Classify fault vs planned reboot (`software wrote 0x6 to reset control register 0xCF9`
+  is a normal reboot and must NOT raise an alarm). On a fault, write one idempotent bundle
+  per dead boot to `~/.cache/iad/host-guard/postmortems/<boot-id>.md`: verbatim line, fault
+  streak over the last 10 boots, every registry record from the dead boot, the final
+  PRE-BOOT second of each sampler's telemetry (boot-relative — a sampler that restarted
+  would otherwise present live idle data as the time of death), session telemetry/engine.log
+  /session.json tails, ledger tail, journal tail.
+- **DoD:** `check` classifies fault/reboot/clean/unreadable; "unreadable" is never
+  reported as clean; bundle idempotent; no-op on hosts with no reset-reason line.
+- **Verify:** `bash tests/automation/test-reset-forensics.sh` (52/52);
+  `bash scripts/automation/host-guard/reset-forensics.sh ensure-postmortem` on this host
+  reproduces the 07-30 bundle with both dead engines and tapeology's 17:14:08 final sample.
+- **Files:** `scripts/automation/host-guard/reset-forensics.sh`, `doctor.sh`,
+  `run-goal.sh`, `tests/automation/test-reset-forensics.sh`.
+- **Rollback:** delete the script, the doctor row, and the single preflight call.
+
+### HOST-3 — IN-PROGRESS 2026-07-30 · P1 · S · LOW
+
+- **Problem:** the remediation for a hardware fault needs root, which the chain does not
+  have and must not take; and the next postmortem will be just as thin unless the host's
+  own recording is improved first (journald lost the final 3m42s of the 07-30 reset; no
+  rasdaemon, so the fabric error itself was never recorded).
+- **Change spec:** `docs/host-guard.md` § After a hardware reset — copy-paste one-liners
+  the OWNER runs (journald `SyncIntervalSec=15s`, rasdaemon, pstore peek, BIOS version vs
+  GEEKOM support, memtest86+, optional C-state limiting), plus the one-change-per-soak-week
+  discipline. Doctor row `ras-logging` verifies read-only what it can and stays PASS on
+  hosts with no reset history.
+- **DoD/Verify:** row WARNs only with reset history; `test-reset-forensics.sh` § C.
+- **Files:** `docs/host-guard.md`, `doctor.sh`, `tests/automation/test-doctor.sh`.
+
+### HOST-4 — IN-PROGRESS 2026-07-30 · P1 · M · LOW
+
+- **Problem:** after the reset nothing could answer "what were BOTH repos doing in the
+  final seconds?". The aggregate verdict was silent when it passed, `telemetry.jsonl` is
+  per-session and never fsync'd, and `engine.log` exists only in interactive mode.
+- **Change spec:** `hg_event` in `lib/host-guard-registry.sh` → one fsync'd JSON line per
+  chain event into `~/.cache/iad/host-guard/events.jsonl` (machine-wide, `.project`/`.boot`
+  fields for filtering, 5 MiB ring). Seven call sites: engine start/stop, iteration start,
+  dispatch start/end (`agent_with_quota_retry` — the single chokepoint for all three
+  backends, so every agent in every repo is bracketed), the HEALTHY `aggregate_ok` verdict,
+  and pause. Oversized payloads are DROPPED, never truncated.
+- **DoD/Verify:** `test-host-guard.sh` §A (92/92) — valid JSON, no-op rule, rotation,
+  20 concurrent appenders → 20 valid lines.
+- **Files:** `lib/host-guard-registry.sh`, `lib/quota-retry.sh`, `run-goal.sh`.
+
+### HOST-5 — IN-PROGRESS 2026-07-30 · P1 · S · LOW-MED
+
+- **Problem:** the sampler was started per repo by each engine's preflight, so the machine
+  had two half-histories and an asymmetry that cost evidence — after the 07-30 reset only
+  trendora's sampler restarted; tapeology's stayed dead.
+- **Change spec:** `host-guard/iad-hwmon.service` (new, `--user`, `Restart=always`,
+  writes `~/.cache/iad/host-guard/hwmon/hwmon.csv`); `HOST_GUARD_HWMON_DIR` seam;
+  `status`/`start` recognize a fresh machine-global csv and never double-run (so the
+  per-repo preflight fallback simply stops firing); ring → 2 generations (~8 days);
+  append-only new column `cpu_mhz`. No `ac_online` — `/sys/class/power_supply` is empty on
+  this host, the column would be permanently blank.
+- **DoD/Verify:** 15-field v2 header; global-sampler detection; `.1`+`.2` rotation.
+- **Files:** `host-guard/hwmon-log.sh`, `host-guard/iad-hwmon.service`, `run-goal.sh`
+  (`_host_guard_latest_tctl` reads the machine csv first so the thermal gate survives).
+
+### HOST-6 — IN-PROGRESS 2026-07-30 · P1 · S · LOW
+
+- **Problem:** a machine reset reuses the pid space, so locks and heartbeats left by the
+  dead boot can name a pid that is alive NOW — and `engine_lock_classify`'s cmdline check
+  can even confirm it, wedging a session that is not actually held.
+- **Change spec:** record `boot_id` in `acquire_engine_lock` metadata and classify a
+  foreign boot id as STALE (covers `.engine.lock` AND `runs/.phase.lock` AND the doctor row
+  in one edit); `hg_pid_matches <pid> <starttime>`; the iteration gate discards a
+  `.pump-alive` whose recorded start time no longer matches.
+- **Deliberately NOT done:** `trace/.lock` is a kernel flock — it dies with its holder and
+  a leftover file can never block. `engine.pid` already self-heals on resume
+  (`run-goal.sh:257-269`); its honesty half is HOST-7.
+- **DoD/Verify:** `test-engine-lock.sh` §A1b (44/44) — foreign boot id + live pid → STALE;
+  locks without the field keep old behaviour.
+
+### HOST-7 — IN-PROGRESS 2026-07-30 · P1 · S · LOW
+
+- **Problem:** both sessions killed by the reset still read `in_progress` with no halt
+  marker. A session that silently reappears mid-iteration teaches the operator that
+  iterations vanish at random, when the truth is one hardware event with a postmortem
+  on disk.
+- **Change spec:** `hg_boot_epoch`/`hg_file_predates_boot` (`HOST_GUARD_BTIME_OVERRIDE`
+  test seam); `run-goal.sh` resume prints the reset banner + postmortem pointer and emits a
+  one-time `halt {"reason":"machine_reset"}` (env-prefixed with the session dir —
+  `telemetry_enabled` silently returns false before `GOAL_SESSION_DIR` is exported, so
+  without the prefix the event would never be written); `commands/goal-status.md` step 5
+  reports when/what/why with the hwmon, ledger and postmortem pointers.
+- **Files:** `lib/host-guard-registry.sh`, `run-goal.sh`, `commands/goal-status.md` (+
+  `.claude/commands/` mirror via `sync-cli-assets.py`).
+
+### HOST-8 — IN-PROGRESS 2026-07-30 · P1 · S · LOW
+
+- **Change spec:** `HOST_GUARD_MAX_ENGINES` in the machine env — over the cap, the junior
+  engine takes the existing resumable `AWAITING_HOST_GUARD` pause via the extracted
+  `_hg_arbitrate` (same total order as every other breach class); the senior warns. Checked
+  BEFORE the no-budget early return so a machine can configure only the cap. Absent or
+  invalid ⇒ unlimited ⇒ today's behaviour (§20 no-op rule).
+- **Released same-day (2026-07-30, owner decision):** set to 1 on this host, then unset a
+  few hours later along with boost-off and the CPU mask. The honest reading is that all
+  three bought *exposure time*, never prevention — the fault fired at load 1.53 as readily
+  as under two concurrent sessions, and BIOS 1.26 turned out to be the latest, so the
+  remediation moved to C-state limiting and then memtest/RMA. The knob remains the way to
+  isolate a soak week to one project. Attribution is preserved regardless: every engine
+  start records the live mitigation set as a `host_state` ledger event (HOST-4), so the
+  next postmortem names the combination that was running. `HOST_GUARD_GLOBAL_ON_CONFLICT` deleted from env + docs.
+- **DoD/Verify:** `test-host-guard.sh` §A15 — junior PAUSE naming the knob, senior WARN,
+  cap=2 OK, absent/junk/0 OK, pump records don't count as engines.
+
+### HOST-9 — IN-PROGRESS 2026-07-30 · P1 · S · LOW (docs only)
+
+HOST-1 addendum above; anti-pattern 27; `docs/host-guard.md` root-cause rewrite + runbook;
+these items. **Stop-and-ask:** none (docs).
+
+### Known gaps — deliberately NOT fixed in this package (TODO)
+
+Each is real but none is on the path of a hardware-caused reset; fixing them alongside the
+forensics work would have blurred what this package is for.
+
+- **Demo-runner browsers escape every guard.** `lib/demo_runner.py:918-930` launches a
+  Playwright Chromium with no `--user-data-dir` under the superpowers profile root, so
+  `browser-confine.sh` Pass A/D cannot see it and `doctor.sh` classifies it as harmless
+  desktop Chrome. It inherits the engine's mask when spawned by a confined engine, but NOT
+  when `demo.sh --live` runs standalone.
+- **Registry dir is per-session overridable.** `hg_registry_dir` honours
+  `HOST_GUARD_REGISTRY_DIR`/`CHAIN_TMP_ROOT`; a project that sets either gets a PRIVATE
+  registry and silently drops out of the machine view — with no warning, because an empty
+  registry reads as "one live session, all fine". A machine-global facility should not be
+  addressable by a per-project variable.
+- **Registry heartbeat only refreshes at iteration boundaries.** `hg_register` runs at
+  preflight and each gate, so a record's mtime can be hours stale while live (07-30:
+  tapeology's engine record was last touched 81 minutes before the reset). Correspondingly
+  a project that starts mid-iteration is invisible until the current iteration ends.
+- **Trendora carries two un-upstreamed framework patches** worth reverse-porting:
+  `lib/common.sh` (force the browser lane when `CHAIN_GOAL_TARGET_JOURNEYS` is set) and
+  `lib/replay-lane.sh` (rc=7 backend-unreachable handling).
diff --git a/incredible_auto_dev/scripts/automation/doctor.sh b/incredible_auto_dev/scripts/automation/doctor.sh
old mode 100644
new mode 100755
index d2215a2..375126a
--- a/incredible_auto_dev/scripts/automation/doctor.sh
+++ b/incredible_auto_dev/scripts/automation/doctor.sh
@@ -57,9 +57,20 @@ source "$SCRIPT_DIR/lib/common.sh"
 source "$SCRIPT_DIR/lib/engine-lock.sh"
 ROOT="${CHAIN_DOCTOR_REPO_ROOT:-$REPO_ROOT}"
 
+# Running the doctor under sudo is always a mistake, and a quiet one. sudo
+# resets HOME, so every check reads ROOT's world instead of yours: no machine
+# budget file, an empty host-guard registry, the wrong plugin cache — and the
+# table comes back looking healthy about a machine that is not the one you run
+# sessions on. With `sudo -E` it is worse: the postmortem write lands in YOUR
+# cache owned by root, and every later user-run forensics call fails on it.
+# Warn rather than refuse — the doctor is advisory by construction.
+if [[ "${EUID:-$(id -u)}" -eq 0 && -z "${CHAIN_DOCTOR_ALLOW_ROOT:-}" ]]; then
+  echo "[doctor] WARNING: running as root (HOME=$HOME). This table describes root's environment, not yours — host-guard, tmp-health and the reset-reason rows will all be wrong. Re-run it as your own user: bash scripts/automation/doctor.sh" >&2
+fi
+
 CHECKS=(python3 node playwright chrome-mcp gh-auth git-remote disk timeout jq
         pump-heartbeat engine-lock tmp-health chrome-exclusive mcp-affinity
-        host-guard cpu-boost ambient-env)
+        host-guard cpu-boost reset-reason ras-logging ambient-env)
 
 # Run a command under GNU/uutils timeout when available (network probes must
 # degrade, never hang). $1 = seconds, rest = command.
@@ -483,8 +494,15 @@ check_host_guard() {
       return
     fi
     verdict="$(hg_aggregate_verdict "")"
+    local n_eng=0 cap
+    while read -r r; do
+      [[ -n "$r" ]] || continue
+      [[ "$(_hg_rec_field "$r" kind)" == "engine" ]] && n_eng=$(( n_eng + 1 ))
+    done < <(hg_live_records)
+    cap="${HOST_GUARD_MAX_ENGINES:-}"
+    [[ "$cap" =~ ^[0-9]+$ ]] || cap="unlimited"
     case "$verdict" in
-      OK) echo "PASS|mask=$mask mem=$mem inside machine budget ${HOST_GUARD_GLOBAL_CPU_LIST}/${HOST_GUARD_GLOBAL_MEMORY_BUDGET:-unset}; $n live guarded context(s): ${roots:-none}" ;;
+      OK) echo "PASS|mask=$mask mem=$mem inside machine budget ${HOST_GUARD_GLOBAL_CPU_LIST}/${HOST_GUARD_GLOBAL_MEMORY_BUDGET:-unset}; engines=$n_eng/$cap; $n live guarded context(s): ${roots:-none}" ;;
       *)  echo "WARN|${verdict#*|}" ;;
     esac
   )
@@ -523,6 +541,82 @@ check_cpu_boost() {
   fi
 }
 
+# EVIDENCE (2026-07-30 17:14:08, reset #7): the machine hard-reset with EVERY
+# host-guard mitigation in force — masks inside the machine budget, 10G+10G under
+# a 22G budget, boost off and persisted, QA browsers confined — at 65 °C, 26 W,
+# 11.5 GB free, memory PSI 0.00. The cause was never visible to any of those
+# checks; it was printed by the CPU itself on the next boot:
+#   x86/amd: Previous system reset reason [0x08000800]: an uncorrected error
+#            caused a data fabric sync flood event
+# Seven of the last ten boots carried a fault-class line. This row surfaces the
+# hardware's own verdict, which no software-side check can infer.
+#
+# FAIL (not WARN) when the last boot died: a host that resets under load is the
+# single most destructive environment fact there is — it destroys whole
+# iterations. The doctor still never gates (exit 0 by construction), so FAIL here
+# costs nothing but attention, which is exactly what it should cost.
+#
+# This row is the doctor's SECOND sanctioned write (after the tmp-health probe):
+# ensure-postmortem freezes the evidence bundle. It is idempotent, lives in the
+# cache root, never touches a repo — and "the operator ran doctor right after a
+# crash" is precisely when the bundle must be created, because the next engine
+# preflight sweeps the registry records that say who was running.
+check_reset_reason() {
+  local script="$SCRIPT_DIR/host-guard/reset-forensics.sh" verdict pm path
+  [[ -f "$script" ]] || { echo "PASS|reset-forensics.sh not present — no reset-reason reader on this install"; return; }
+  verdict="$(_bounded 20 bash "$script" check 2>/dev/null)"
+  case "$verdict" in
+    RESET\|*)
+      local hex cause streak prev
+      IFS='|' read -r _ hex cause streak prev <<< "$verdict"
+      : "$prev"
+      pm="$(_bounded 30 bash "$script" ensure-postmortem 2>/dev/null)"
+      path="${pm#POSTMORTEM|}"; path="${path%|*}"
+      [[ "$pm" == POSTMORTEM\|* ]] || path="(bundle unavailable: ${pm})"
+      echo "FAIL|the previous boot ended in a HARDWARE-asserted reset: $cause ($hex); $streak recent boots. No CPU mask or memory ceiling can prevent this — postmortem: $path (docs/host-guard.md § After a hardware reset)"
+      ;;
+    CLEAN\|*)  echo "PASS|${verdict#CLEAN|}" ;;
+    UNKNOWN\|*) echo "WARN|${verdict#UNKNOWN|}" ;;
+    *)         echo "WARN|reset-forensics.sh returned an unparseable verdict: ${verdict:-<empty>}" ;;
+  esac
+}
+
+# Two host-level recording facilities that only matter once a machine HAS had a
+# hardware reset, and that the chain cannot install for itself (both need root):
+#   - journald's default SyncIntervalSec is 5 minutes, so the 2026-07-30 reset
+#     erased the final 3m42s of journal; only the 1 Hz fsync'd hwmon csv survived.
+#   - rasdaemon records the memory/fabric error itself (address, DIMM), which is
+#     what turns "sync flood" into an actionable RMA or BIOS bug report.
+# WARN, never FAIL: these improve the NEXT postmortem, they do not make the host
+# unsafe. And on a machine with no reset history the row stays PASS — a framework
+# must not nag hosts that never had the incident.
+check_ras_logging() {
+  local script="$SCRIPT_DIR/host-guard/reset-forensics.sh" hist=0 jdir ras missing=""
+  if [[ -f "$script" ]] && [[ "$(_bounded 20 bash "$script" check 2>/dev/null)" == RESET\|* ]]; then
+    hist=1
+  fi
+  jdir="${CHAIN_DOCTOR_JOURNALD_DIR:-/etc/systemd/journald.conf.d}"
+  if ! grep -rqs 'SyncIntervalSec' "$jdir" 2>/dev/null; then
+    missing+="journald SyncIntervalSec drop-in ($jdir); "
+  fi
+  # `systemctl is-active` PRINTS its verdict and exits non-zero for anything but
+  # "active", so a `|| echo` fallback would append a second line and smuggle a
+  # newline into this row (the wrapper reads only the last line and would call
+  # the whole check crashed). First line only, always.
+  ras="${CHAIN_DOCTOR_RAS_STATE:-$(systemctl is-active rasdaemon 2>/dev/null | head -n 1)}"
+  [[ -n "$ras" ]] || ras="unknown"
+  [[ "$ras" == "active" ]] || missing+="rasdaemon (is-active=$ras); "
+  if [[ -z "$missing" ]]; then
+    echo "PASS|crash recording hardened: journald sync drop-in present and rasdaemon active"
+    return
+  fi
+  if (( hist == 0 )); then
+    echo "PASS|no hardware-reset history on this host — journald/rasdaemon hardening is optional (missing: ${missing%; })"
+    return
+  fi
+  echo "WARN|this host HAS hardware-reset history but the next postmortem will be poorer: ${missing%; }— see docs/host-guard.md § After a hardware reset (both need one sudo command)"
+}
+
 # EVIDENCE (§9 measurement discipline): benchmark/measurement runs record
 # "no ambient CHAIN_* vars" as a precondition — stray knobs silently alter
 # engine behavior. The engine snapshots names BEFORE its own exports
diff --git a/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh b/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
index e5632fd..ec921f5 100755
--- a/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
+++ b/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
@@ -40,11 +40,24 @@ ENV_FILE="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
 
 INTERVAL="${HOST_GUARD_SAMPLER_INTERVAL:-1}"
 MAX_BYTES="${HOST_GUARD_SAMPLER_MAX_BYTES:-10485760}"
-LOG_DIR="$REPO_ROOT/logs/hwmon"
+# HOST_GUARD_HWMON_DIR lets the machine-global systemd user unit
+# (iad-hwmon.service) put the csv in the cache root instead of one repo's logs/.
+# Unset ⇒ per-repo placement, exactly as before.
+LOG_DIR="${HOST_GUARD_HWMON_DIR:-$REPO_ROOT/logs/hwmon}"
 CSV="$LOG_DIR/hwmon.csv"
 PIDFILE="$LOG_DIR/hwmon.pid"
 DAEMON_LOG="$LOG_DIR/hwmon.log"
-HEADER="epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10"
+# Where the machine-global sampler writes. One 1 Hz sampler is enough for the
+# whole machine; a per-repo engine must not start a second writer when it is
+# already running (that is how two repos ended up with two half-histories).
+GLOBAL_CSV="${HOST_GUARD_HWMON_GLOBAL_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/hwmon}/hwmon.csv"
+# Schema is APPEND-ONLY: new columns go at the END so every existing reader
+# (field 1 = epoch, field 2 = tctl) keeps working against old and new files.
+# cpu_mhz was added after the 2026-07-30 sync-flood reset — clock behaviour is
+# the cheapest signal correlated with fabric/VRM transients that the previous
+# schema could not see. (No ac_online column: /sys/class/power_supply is empty
+# on this class of mini-PC, so it would be a permanently blank field.)
+HEADER="epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10,cpu_mhz"
 
 # ── Sensor resolution (by hwmon name, once at startup) ─────────────────────
 TCTL="" GPU_TEMP="" PPT_NOW="" PPT_AVG="" NVME_T="" DIMM0="" DIMM1="" ACPITZ=""
@@ -89,6 +102,18 @@ _psi_avg10() { # $1 /proc/pressure/{cpu,memory} → the "some avg10" value
   printf '%s' "${line%% *}"
   return 0
 }
+_cpu_mhz() { # mean current core clock in MHz ("" when cpufreq is unavailable)
+  local sum=0 n=0 v f
+  for f in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq; do
+    [[ -r "$f" ]] || continue
+    IFS= read -r v < "$f" 2>/dev/null || continue
+    [[ "$v" =~ ^[0-9]+$ ]] || continue
+    sum=$(( sum + v )); n=$(( n + 1 ))
+  done
+  (( n > 0 )) || return 0
+  printf '%s' $(( sum / n / 1000 ))
+  return 0
+}
 MEM_AVAIL_MB="" SWAP_FREE_MB=""
 _mem_fields() {
   MEM_AVAIL_MB="" SWAP_FREE_MB=""
@@ -107,7 +132,7 @@ cmd_run() {
   mkdir -p "$LOG_DIR"
   resolve_sensors
   [[ -f "$CSV" ]] || printf '%s\n' "$HEADER" > "$CSV"
-  local ts tctl gpu ppt pavg nvt d0 d1 az load1 rest psic psim size
+  local ts tctl gpu ppt pavg nvt d0 d1 az load1 rest psic psim size mhz
   while :; do
     ts=$EPOCHSECONDS
     tctl=$(_read_scaled "$TCTL" 1000)
@@ -122,14 +147,19 @@ cmd_run() {
     _mem_fields
     psic=$(_psi_avg10 /proc/pressure/cpu)
     psim=$(_psi_avg10 /proc/pressure/memory)
-    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
+    mhz=$(_cpu_mhz)
+    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
       "$ts" "$tctl" "$gpu" "$ppt" "$pavg" "$nvt" "$d0" "$d1" "$az" \
-      "$load1" "$MEM_AVAIL_MB" "$SWAP_FREE_MB" "$psic" "$psim" >> "$CSV"
+      "$load1" "$MEM_AVAIL_MB" "$SWAP_FREE_MB" "$psic" "$psim" "$mhz" >> "$CSV"
     # fsync the csv so the last pre-crash line survives an instant reset
     # (uutils-compatible file-arg form; plain `sync` as fallback).
     sync "$CSV" 2>/dev/null || sync 2>/dev/null || true
     size=$(stat -c %s "$CSV" 2>/dev/null || echo 0)
     if [[ "$size" =~ ^[0-9]+$ ]] && (( size > MAX_BYTES )); then
+      # Two generations, not one: at 1 Hz a 10 MiB file is ~4 days, and the
+      # incident history that matters spans more than one reset. tapeology's
+      # ring was 99.3% full when the machine went down.
+      if [[ -f "$CSV.1" ]]; then mv -f "$CSV.1" "$CSV.2"; fi
       mv -f "$CSV" "$CSV.1"
       printf '%s\n' "$HEADER" > "$CSV"
     fi
@@ -137,12 +167,17 @@ cmd_run() {
   done
 }
 
-_csv_fresh() { # true iff the csv was written within the last INTERVAL+5 s
-  local mtime
-  [[ -f "$CSV" ]] || return 1
-  mtime=$(stat -c %Y "$CSV" 2>/dev/null || echo 0)
+_file_fresh() { # true iff $1 was written within the last INTERVAL+5 s
+  local f="${1:-}" mtime
+  [[ -f "$f" ]] || return 1
+  mtime=$(stat -c %Y "$f" 2>/dev/null || echo 0)
   (( EPOCHSECONDS - mtime <= INTERVAL + 5 ))
 }
+_csv_fresh() { _file_fresh "$CSV"; }
+# A live machine-global sampler covers this repo too — the hardware it samples
+# is the same hardware. Distinct file only; when this process IS the global
+# sampler the two paths are identical and this is never consulted.
+_global_fresh() { [[ "$GLOBAL_CSV" != "$CSV" ]] && _file_fresh "$GLOBAL_CSV"; }
 
 cmd_start() {
   mkdir -p "$LOG_DIR"
@@ -158,6 +193,10 @@ cmd_start() {
     echo "hwmon-log: already running (external sampler, csv fresh)"
     return 0
   fi
+  if _global_fresh; then
+    echo "hwmon-log: already running (machine-global sampler → $GLOBAL_CSV)"
+    return 0
+  fi
   nohup env HOST_GUARD_ROOT="$REPO_ROOT" bash "$HERE/hwmon-log.sh" run >> "$DAEMON_LOG" 2>&1 &
   pid=$!
   disown "$pid" 2>/dev/null || true
@@ -202,6 +241,11 @@ cmd_status() {
     echo "hwmon-log: running (external sampler), csv fresh: $last"
     return 0
   fi
+  if _global_fresh; then
+    IFS= read -r last < <(tail -n 1 "$GLOBAL_CSV" 2>/dev/null) || last=""
+    echo "hwmon-log: running (machine-global sampler), csv fresh: $last"
+    return 0
+  fi
   echo "hwmon-log: not running"
   return 1
 }
diff --git a/incredible_auto_dev/scripts/automation/host-guard/iad-hwmon.service b/incredible_auto_dev/scripts/automation/host-guard/iad-hwmon.service
new file mode 100644
index 0000000..085f825
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard/iad-hwmon.service
@@ -0,0 +1,29 @@
+[Unit]
+# Machine-global 1 Hz hardware sampler for host-guard crash forensics.
+#
+# WHY A MACHINE UNIT: the sampler used to be started per repo by each engine's
+# preflight. That produced two half-histories and an asymmetry that cost real
+# evidence — after the 2026-07-30 hardware reset only one project's sampler came
+# back, so the other repo's csv stayed frozen and its post-reset behaviour was
+# unrecorded. The hardware is one machine; one sampler covers it, restarts
+# itself after every reset, and writes outside every repo.
+#
+# INSTALL (no root — this is a --user unit; see docs/host-guard.md):
+#   cp scripts/automation/host-guard/iad-hwmon.service ~/.config/systemd/user/
+#   systemctl --user daemon-reload && systemctl --user enable --now iad-hwmon.service
+#   loginctl show-user "$USER" --property=Linger   # must be Linger=yes
+# Edit ExecStart if your framework clone is not at ~/Git/incredible_auto_dev.
+Description=iad host-guard hwmon sampler (1 Hz, machine-global crash forensics)
+
+[Service]
+Type=simple
+Environment=HOST_GUARD_HWMON_DIR=%h/.cache/iad/host-guard/hwmon
+ExecStart=/usr/bin/bash %h/Git/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh run
+Restart=always
+RestartSec=5
+# Never let the forensics sampler become the thing that hurts the host.
+Nice=10
+IOSchedulingClass=idle
+
+[Install]
+WantedBy=default.target
diff --git a/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh b/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh
new file mode 100755
index 0000000..80118cc
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh
@@ -0,0 +1,443 @@
+#!/usr/bin/env bash
+# reset-forensics.sh — the platform's own postmortem, read at every boot.
+#
+# WHY: seven hard resets on this host were debugged as software load problems
+# through three generations of guard (per-scope caps → machine-global aggregate
+# → QA-browser confinement) while the CPU had been printing the answer into the
+# kernel log on every single boot:
+#
+#   x86/amd: Previous system reset reason [0x08000800]: an uncorrected error
+#            caused a data fabric sync flood event
+#
+# A data fabric sync flood is an uncorrectable SoC/Infinity-Fabric error: the
+# hardware asserts reset immediately, the OS is never notified, and NOTHING
+# software does can prevent it. The 2026-07-30 17:14:08 reset happened with the
+# machine-global aggregate bound armed and every check green — both projects
+# inside 0-3,8-11, 10G+10G under a 22G budget, boost off and persisted, QA
+# browsers confined — at 65 °C, 26 W, 11.5 GB free, memory PSI 0.00.
+#
+# So this script does not try to PREVENT anything. It makes every reset
+# self-documenting: read the register, and when the last boot died, freeze what
+# the chain was doing into a bundle BEFORE the engine's own registry sweep
+# (run-goal.sh preflight) erases the only record of who was running.
+#
+# Usage / stdout contract — exactly one line, ALWAYS exit 0 (advisory by
+# construction, like doctor.sh; a broken forensics reader must never stop a run):
+#   check              RESET|<hex>|<cause>|<hits>/<boots>|<prev_boot_id>
+#                      CLEAN|<why>
+#                      UNKNOWN|<why>
+#   ensure-postmortem  POSTMORTEM|<path>|new   POSTMORTEM|<path>|existing
+#                      NONE|<why>              UNKNOWN|<why>
+#   report             print the newest bundle (rc 1 when there is none)
+#
+# NO-OP RULE (roadmap §20): a host whose kernel prints no reset-reason line —
+# every non-AMD box, and every AMD box that has never reset — reports CLEAN and
+# writes nothing at all. No config file is required for the read-only paths.
+#
+# Injection seams (how tests fake the world — no root, no journal, no API):
+#   HOST_GUARD_RESET_KLOG_FILE       stands in for `journalctl -k -b 0`
+#   HOST_GUARD_RESET_KLOG_DIR        per-boot logs: <dir>/<boot-id>.klog (streak)
+#   HOST_GUARD_RESET_BOOTS_FILE      stands in for `journalctl --list-boots`
+#   HOST_GUARD_RESET_JOURNAL_TAIL_FILE  stands in for `journalctl -b -1 -n 80`
+#   HOST_GUARD_POSTMORTEM_DIR        bundle dir (default <tmp-root>/host-guard/postmortems)
+#   HOST_GUARD_RESET_BOOT_WINDOW     how many recent boots the streak scans (10)
+#   HOST_GUARD_REGISTRY_DIR / CHAIN_TMP_ROOT / HOST_GUARD_EVENTS_FILE (via the lib)
+#
+# COST: every kernel-log read is a STREAM into `grep -m1`/`grep -q`, which exits
+# at the first hit and SIGPIPEs the producer, so nothing is ever slurped into
+# memory. Measured on the incident host: ~10 ms per boot, ~120 ms for a 10-boot
+# streak. Do NOT "optimize" this with a head bound — the line lands at kernel
+# log line 942 here, and a bound short enough to matter would report CLEAN on a
+# machine that had just reset.
+#
+# No `set -e` and no `pipefail`: SIGPIPE on the producer is EXPECTED, and every
+# failure path degrades to UNKNOWN rather than to a dead script.
+set -u
+
+HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+
+# The registry library owns the paths this bundle joins over (registry dir,
+# record fields, boot id, events ledger). Source it when present; keep tiny
+# local fallbacks so a vendored copy that is missing the lib still reports.
+if [[ -f "$HERE/../lib/host-guard-registry.sh" ]]; then
+  # shellcheck source=../lib/host-guard-registry.sh
+  source "$HERE/../lib/host-guard-registry.sh"
+fi
+if ! declare -f hg_registry_dir >/dev/null 2>&1; then
+  hg_registry_dir() { echo "${HOST_GUARD_REGISTRY_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/registry}"; }
+  _hg_rec_field() { sed -n "s/^$2=//p" "$1" 2>/dev/null | head -n 1; }
+  _hg_boot_id() { cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo "unknown"; }
+  hg_boot_epoch() { awk '/^btime /{print $2; exit}' /proc/stat 2>/dev/null || echo 0; }
+fi
+
+RESET_PAT='Previous system reset reason'
+# NOT every reset-reason line is an incident. An ordinary `reboot` writes 0x6 to
+# the legacy reset control register 0xCF9, and the SoC dutifully reports it on
+# the next boot ("[0x00080800]: software wrote 0x6 to reset control register
+# 0xCF9"). Counting that as a fault would make every planned reboot look like a
+# crash and would cry wolf on hosts that never had an incident.
+BENIGN_PAT='software wrote|reset control register'
+WINDOW="${HOST_GUARD_RESET_BOOT_WINDOW:-10}"
+POSTMORTEM_DIR="${HOST_GUARD_POSTMORTEM_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/postmortems}"
+EVENTS_FILE="${HOST_GUARD_EVENTS_FILE:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/events.jsonl}"
+GLOBAL_HWMON="${HOST_GUARD_HWMON_GLOBAL_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/hwmon}/hwmon.csv"
+
+# ── Boot enumeration ────────────────────────────────────────────────────────
+
+_boots_stream() { # `journalctl --list-boots` text; rc 1 when unavailable
+  local out=""
+  if [[ -n "${HOST_GUARD_RESET_BOOTS_FILE:-}" ]]; then
+    [[ -r "$HOST_GUARD_RESET_BOOTS_FILE" ]] || return 1
+    cat "$HOST_GUARD_RESET_BOOTS_FILE"
+    return 0
+  fi
+  command -v journalctl >/dev/null 2>&1 || return 1
+  out="$(journalctl --list-boots --no-pager 2>/dev/null)"
+  [[ -n "$out" ]] || return 1
+  printf '%s\n' "$out"
+}
+
+# Rows only (drop the "IDX BOOT ID …" header): "<idx> <boot-id> <rest…>".
+_boot_rows() { _boots_stream | awk '$1 ~ /^-?[0-9]+$/ {print}'; }
+
+_prev_boot_id() { _boot_rows | awk '$1 == "-1" {print $2; exit}'; }
+
+_is_benign() { grep -qiE "$BENIGN_PAT" <<< "${1:-}"; }
+
+_boot_reset_line() { # $1 boot id → that boot's reset-reason line (empty if none)
+  local bid="${1:-}" f
+  if [[ -n "${HOST_GUARD_RESET_KLOG_DIR:-}" ]]; then
+    f="$HOST_GUARD_RESET_KLOG_DIR/$bid.klog"
+    [[ -r "$f" ]] || return 1
+    grep -i -m1 "$RESET_PAT" "$f" 2>/dev/null
+    return 0
+  fi
+  command -v journalctl >/dev/null 2>&1 || return 1
+  journalctl -k -b "$bid" --no-pager 2>/dev/null | grep -i -m1 "$RESET_PAT"
+  return 0
+}
+
+# ── Detection (sets globals; both subcommands share it) ─────────────────────
+
+_DET_STATUS="" _DET_LINE="" _DET_HEX="" _DET_CAUSE="" _DET_WHY=""
+_DET_HITS=0 _DET_TOTAL=0 _DET_PREV="" _DET_ROWS=""
+
+_streak() { # fills _DET_HITS/_DET_TOTAL/_DET_ROWS over the last $WINDOW boots
+  # _DET_HITS counts FAULT-class boots only; a planned reboot is recorded in the
+  # table as "reboot" so the history stays readable without inflating the count.
+  local idx bid rest row hit line
+  _DET_HITS=0 _DET_TOTAL=0 _DET_ROWS=""
+  while read -r row; do
+    [[ -n "$row" ]] || continue
+    idx="$(awk '{print $1}' <<< "$row")"
+    bid="$(awk '{print $2}' <<< "$row")"
+    rest="$(awk '{$1=""; $2=""; sub(/^ +/, ""); print}' <<< "$row")"
+    _DET_TOTAL=$(( _DET_TOTAL + 1 ))
+    line="$(_boot_reset_line "$bid")"
+    if [[ -z "$line" ]]; then
+      hit="no"
+    elif _is_benign "$line"; then
+      hit="reboot"
+    else
+      hit="**FAULT**"; _DET_HITS=$(( _DET_HITS + 1 ))
+    fi
+    _DET_ROWS+="$hit|$idx|$bid|$rest"$'\n'
+  done < <(_boot_rows | tail -n "$WINDOW")
+  return 0
+}
+
+_detect() {
+  _DET_STATUS="" _DET_LINE="" _DET_HEX="" _DET_CAUSE="" _DET_WHY=""
+  local n=0
+
+  if [[ -n "${HOST_GUARD_RESET_KLOG_FILE:-}" ]]; then
+    if [[ ! -r "$HOST_GUARD_RESET_KLOG_FILE" ]]; then
+      _DET_STATUS="UNKNOWN"
+      _DET_WHY="HOST_GUARD_RESET_KLOG_FILE=$HOST_GUARD_RESET_KLOG_FILE is not readable"
+      return 0
+    fi
+    _DET_LINE="$(grep -i -m1 "$RESET_PAT" "$HOST_GUARD_RESET_KLOG_FILE" 2>/dev/null)"
+  elif command -v journalctl >/dev/null 2>&1; then
+    # Liveness probe first: journalctl can exist and still return nothing when
+    # this user cannot read the kernel log. Without the probe, "no permission"
+    # and "no reset line" would both look CLEAN — the exact false negative this
+    # whole script exists to prevent.
+    if [[ -z "$(journalctl -k -b 0 --no-pager -n 1 2>/dev/null)" ]]; then
+      _DET_STATUS="UNKNOWN"
+      _DET_WHY="journalctl returned no kernel log for this boot — this user probably cannot read it; fix with: sudo usermod -aG systemd-journal \$USER (then log out and back in)"
+      return 0
+    fi
+    _DET_LINE="$(journalctl -k -b 0 --no-pager 2>/dev/null | grep -i -m1 "$RESET_PAT")"
+  elif [[ -r /var/log/kern.log ]]; then
+    # kern.log carries history but cannot be scoped to THIS boot, so a hit here
+    # is not evidence that the LAST boot died. Report honestly, never guess.
+    n="$(grep -c -i "$RESET_PAT" /var/log/kern.log 2>/dev/null)"
+    [[ "$n" =~ ^[0-9]+$ ]] || n=0
+    _DET_STATUS="UNKNOWN"
+    _DET_WHY="journalctl is unavailable; /var/log/kern.log carries $n reset-reason line(s) but cannot be scoped to the current boot — install systemd-journal access for an authoritative read"
+    return 0
+  else
+    _DET_STATUS="UNKNOWN"
+    _DET_WHY="no readable kernel log (no journalctl, no /var/log/kern.log) — the platform reset-reason register cannot be read on this host"
+    return 0
+  fi
+
+  if [[ -z "$_DET_LINE" ]]; then
+    _DET_STATUS="CLEAN"
+    _DET_WHY="no reset-reason line in this boot's kernel log — the previous shutdown was orderly (or this platform exposes no reset-reason register)"
+    return 0
+  fi
+  if _is_benign "$_DET_LINE"; then
+    _DET_STATUS="CLEAN"
+    _DET_WHY="previous boot ended in a software-initiated reboot, not a fault (${_DET_LINE#*: })"
+    return 0
+  fi
+
+  _DET_STATUS="RESET"
+  _DET_HEX="$(sed -n 's/.*reset reason \[\([^]]*\)\].*/\1/p' <<< "$_DET_LINE")"
+  _DET_CAUSE="$(sed -n 's/.*reset reason \[[^]]*\]:[[:space:]]*//p' <<< "$_DET_LINE")"
+  [[ -n "$_DET_CAUSE" ]] || _DET_CAUSE="$_DET_LINE"
+  _streak
+  _DET_PREV="$(_prev_boot_id)"
+  return 0
+}
+
+# ── Bundle rendering ────────────────────────────────────────────────────────
+
+_STALE_ROOTS=""   # newline-separated project roots seen in stale records
+_STALE_SESSIONS="" # newline-separated "<root>|<sid>" for stale ENGINE records
+
+_render_records() { # section 3 — and harvest roots/sessions for 4 and 5
+  local dir cur r bid kind root sid
+  dir="$(hg_registry_dir)"
+  cur="$(_hg_boot_id)"
+  _STALE_ROOTS="" _STALE_SESSIONS=""
+  local found=0
+  for r in "$dir"/*.rec; do
+    [[ -e "$r" ]] || continue
+    bid="$(_hg_rec_field "$r" boot_id)"
+    # Records from the CURRENT boot belong to something running right now —
+    # they are not evidence about the boot that died.
+    [[ "$bid" != "$cur" ]] || continue
+    found=$(( found + 1 ))
+    kind="$(_hg_rec_field "$r" kind)"
+    root="$(_hg_rec_field "$r" project_root)"
+    sid="$(_hg_rec_field "$r" session_id)"
+    printf '### %s\n\n' "$(basename "$r")"
+    printf '```\n'
+    cat "$r" 2>/dev/null
+    printf '```\n\n'
+    [[ -z "$root" ]] || _STALE_ROOTS+="$root"$'\n'
+    if [[ "$kind" == "engine" && -n "$root" && -n "$sid" ]]; then
+      _STALE_SESSIONS+="$root|$sid"$'\n'
+    fi
+  done
+  if (( found == 0 )); then
+    printf 'No registry records from a previous boot survive in `%s`.\n' "$dir"
+    printf 'Either nothing was running, or an engine preflight already swept them\n'
+    printf '(the sweep is boot-id keyed — run this script BEFORE resuming a session).\n\n'
+  fi
+  _STALE_ROOTS="$(printf '%s' "$_STALE_ROOTS" | sort -u)"
+  _STALE_SESSIONS="$(printf '%s' "$_STALE_SESSIONS" | sort -u)"
+  return 0
+}
+
+_render_csv_tail() { # $1 csv path, $2 label — the samples that PRECEDE this boot
+  local csv="$1" label="$2" bt rows last mt
+  [[ -f "$csv" ]] || return 0
+  bt="$(hg_boot_epoch)"
+  # Boot-relative, never a plain tail: a sampler that restarted after the reboot
+  # keeps appending, and tailing it would label live idle data "time of death".
+  rows="$(awk -F, -v b="$bt" '$1 ~ /^[0-9]+$/ && $1 + 0 < b' "$csv" 2>/dev/null | tail -n 20)"
+  printf '### %s\n\n' "$label"
+  printf -- '- file: `%s`\n' "$csv"
+  if [[ -z "$rows" ]]; then
+    mt="$(date -d "@$(stat -c %Y "$csv" 2>/dev/null || echo 0)" '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null)"
+    printf -- '- no samples from before this boot survive here (rotated away, or this sampler only started after the reboot). Last written %s.\n\n' "${mt:-unknown}"
+    return 0
+  fi
+  last="$(tail -n 1 <<< "$rows" | cut -d, -f1)"
+  printf -- '- **final sample before the reset: %s** — the closest thing to a time of death\n\n' \
+    "$(date -d "@$last" '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null || echo "epoch $last")"
+  printf '```\n%s\n```\n\n' "$rows"
+  return 0
+}
+
+_render() {
+  local now
+  now="$(date '+%Y-%m-%d %H:%M:%S %Z')"
+
+  printf '# Machine reset postmortem — boot %s\n\n' "${_DET_PREV:-unknown}"
+  printf 'Generated %s by `scripts/automation/host-guard/reset-forensics.sh`.\n\n' "$now"
+  printf 'The previous boot did not shut down. The platform reset-reason register says\n'
+  printf 'the HARDWARE asserted reset, so the kernel was never notified and no software\n'
+  printf 'guard — CPU mask, memory ceiling, browser confinement — could have prevented\n'
+  printf 'it. Remediation is firmware/hardware: see `docs/host-guard.md` §\n'
+  printf 'After a hardware reset — root-cause runbook.\n\n'
+
+  printf '## 1. Reset reason (the platform, verbatim)\n\n```\n%s\n```\n\n' "$_DET_LINE"
+  printf -- '- code: `%s`\n' "${_DET_HEX:-unknown}"
+  printf -- '- cause: %s\n' "${_DET_CAUSE:-unknown}"
+  printf -- '- hardware-fault resets among the last %s boots: **%s** (planned reboots excluded)\n\n' "$_DET_TOTAL" "$_DET_HITS"
+
+  printf '## 2. Recent boot history\n\n'
+  if [[ -n "$_DET_ROWS" ]]; then
+    printf '| verdict | idx | boot id | first → last entry |\n|---|---|---|---|\n'
+    local hit idx bid rest
+    while IFS='|' read -r hit idx bid rest; do
+      [[ -n "$idx" ]] || continue
+      printf '| %s | %s | `%s` | %s |\n' "$hit" "$idx" "$bid" "$rest"
+    done <<< "$_DET_ROWS"
+    printf '\n'
+  else
+    printf 'Boot history unavailable (`journalctl --list-boots` returned nothing).\n\n'
+  fi
+
+  printf '## 3. What was running (registry records from the dead boot)\n\n'
+  _render_records
+
+  printf '## 4. Hardware telemetry, final seconds (1 Hz, fsync per line)\n\n'
+  _render_csv_tail "$GLOBAL_HWMON" "machine-global sampler"
+  local root
+  while read -r root; do
+    [[ -n "$root" ]] || continue
+    _render_csv_tail "$root/logs/hwmon/hwmon.csv" "$(basename "$root")"
+    [[ -f "$root/logs/hwmon/hwmon.csv" ]] || _render_csv_tail "$root/logs/hwmon/hwmon.csv.1" "$(basename "$root") (rotated)"
+  done <<< "$_STALE_ROOTS"
+  printf 'Columns: `%s`\n\n' "epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10[,cpu_mhz]"
+
+  printf '## 5. Session artifacts at the moment of death\n\n'
+  local sid sdir
+  while IFS='|' read -r root sid; do
+    [[ -n "$root" && -n "$sid" ]] || continue
+    sdir="$root/runs/goal-session-$sid"
+    printf '### %s — session `%s`\n\n' "$(basename "$root")" "$sid"
+    if [[ -f "$sdir/telemetry.jsonl" ]]; then
+      printf 'telemetry.jsonl (last 20):\n\n```\n'
+      tail -n 20 "$sdir/telemetry.jsonl" 2>/dev/null
+      printf '```\n\n'
+    fi
+    if [[ -f "$sdir/engine.log" ]]; then
+      printf 'engine.log (last 40):\n\n```\n'
+      tail -n 40 "$sdir/engine.log" 2>/dev/null
+      printf '```\n\n'
+    fi
+    if [[ -f "$sdir/session.json" ]]; then
+      printf 'session.json:\n\n```json\n'
+      cat "$sdir/session.json" 2>/dev/null
+      printf '```\n\n'
+    fi
+  done <<< "$_STALE_SESSIONS"
+  [[ -n "$_STALE_SESSIONS" ]] || printf 'No engine session could be identified from the surviving records.\n\n'
+
+  printf '## 6. Machine-wide chain event ledger (previous boot)\n\n'
+  if [[ -f "$EVENTS_FILE" ]]; then
+    printf 'Last 40 events not belonging to the current boot — `%s`:\n\n```\n' "$EVENTS_FILE"
+    grep -v "$(_hg_boot_id)" "$EVENTS_FILE" 2>/dev/null | tail -n 40
+    printf '```\n\n'
+  else
+    printf 'No event ledger at `%s` yet (written by hg_event once a guarded engine runs).\n\n' "$EVENTS_FILE"
+  fi
+
+  printf '## 6b. Host mitigations — which experiment was running?\n\n'
+  printf 'Read NOW (the boot after the reset), so PERSISTED settings are accurate and a\n'
+  printf 'runtime-only change has already reverted. For what was truly in force during the\n'
+  printf 'run, use the `host_state` event in §6 — the engine records it at start.\n\n'
+  if declare -f hg_host_mitigations >/dev/null 2>&1; then
+    printf '```json\n%s\n```\n\n' "$(hg_host_mitigations)"
+  fi
+  local hostenv
+  hostenv="${HOST_GUARD_HOST_ENV_FILE:-$HOME/.config/iad/host-guard-host.env}"
+  if [[ -f "$hostenv" ]]; then
+    printf 'Machine budget (`%s`):\n\n```\n' "$hostenv"
+    grep -vE '^\s*#|^\s*$' "$hostenv" 2>/dev/null
+    printf '```\n\n'
+  fi
+
+  printf '## 7. Journal tail of the dead boot\n\n'
+  printf 'NOTE: journald syncs every 5 minutes by default, so the last minutes before a\n'
+  printf 'hard reset are usually MISSING here — trust §4 for the time of death.\n\n```\n'
+  if [[ -n "${HOST_GUARD_RESET_JOURNAL_TAIL_FILE:-}" ]]; then
+    tail -n 80 "$HOST_GUARD_RESET_JOURNAL_TAIL_FILE" 2>/dev/null
+  elif command -v journalctl >/dev/null 2>&1; then
+    journalctl -b -1 -n 80 --no-pager 2>/dev/null
+  fi
+  printf '```\n\n'
+
+  printf '## Next steps\n\n'
+  printf '1. Run the root-cause runbook in `docs/host-guard.md` (journald sync interval,\n'
+  printf '   rasdaemon, pstore, BIOS version, overnight memtest).\n'
+  printf '2. Change ONE hardware variable per soak week so causality stays readable.\n'
+  printf '3. Acceptance: seven consecutive days with `doctor.sh --only reset-reason`\n'
+  printf '   reporting CLEAN on every boot.\n'
+  return 0
+}
+
+_link_latest() {
+  local target="$1"
+  ln -sfn "$(basename "$target")" "$POSTMORTEM_DIR/latest.md" 2>/dev/null || true
+}
+
+# ── Subcommands ─────────────────────────────────────────────────────────────
+
+cmd_check() {
+  _detect
+  case "$_DET_STATUS" in
+    RESET) printf 'RESET|%s|%s|%s/%s|%s\n' "${_DET_HEX:-unknown}" "$_DET_CAUSE" \
+             "$_DET_HITS" "$_DET_TOTAL" "${_DET_PREV:-unknown}" ;;
+    CLEAN) printf 'CLEAN|%s\n' "$_DET_WHY" ;;
+    *)     printf 'UNKNOWN|%s\n' "$_DET_WHY" ;;
+  esac
+  return 0
+}
+
+cmd_ensure_postmortem() {
... [diff_bound] incredible_auto_dev/scripts/automation/host-guard/reset-forensics.sh: 49 more diff lines omitted — Read the file for full detail
diff --git a/incredible_auto_dev/scripts/automation/lib/engine-lock.sh b/incredible_auto_dev/scripts/automation/lib/engine-lock.sh
index 76ad52e..fdb374e 100644
--- a/incredible_auto_dev/scripts/automation/lib/engine-lock.sh
+++ b/incredible_auto_dev/scripts/automation/lib/engine-lock.sh
@@ -101,6 +101,19 @@ engine_lock_classify() {
     return 0
   fi
 
+  # Recorded in a previous boot ⇒ the holder cannot possibly be alive, whatever
+  # /proc says now. Checked AFTER the cross-host branch (boot ids are only
+  # comparable on the same host) and BEFORE the pid probe, because a machine
+  # reset is exactly the case where the pid probe can be fooled. Locks written
+  # before this field existed carry no boot_id and fall through unchanged.
+  local lock_boot cur_boot
+  lock_boot="$(_engine_lock_meta "$dir" boot_id)"
+  cur_boot="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null)"
+  if [[ -n "$lock_boot" && -n "$cur_boot" && "$lock_boot" != "$cur_boot" ]]; then
+    echo "STALE|$pid|${host:-$myhost}|${age:-?}|recorded in a previous boot (machine reset or reboot) — the holder cannot be alive"
+    return 0
+  fi
+
   if kill -0 "$pid" 2>/dev/null; then
     # Same-host pid is alive — but pids get recycled across crashes/reboots.
     # If /proc says the live process is something else entirely, the holder
@@ -131,6 +144,10 @@ acquire_engine_lock() {
         _engine_lock_host      > "$dir/host"
         date +%s               > "$dir/epoch"
         basename -- "$0" 2>/dev/null > "$dir/cmd"
+        # Boot id: pids are recycled across a reboot, so after a machine reset a
+        # leftover lock can name a pid that is alive and even runs a matching
+        # command. The boot id is the only field that cannot survive the reset.
+        cat /proc/sys/kernel/random/boot_id 2>/dev/null > "$dir/boot_id"
       } 2>/dev/null || true
       _ENGINE_LOCK_HELD="$dir"
       return 0
diff --git a/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh b/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh
index ba08300..add0adf 100644
--- a/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh
+++ b/incredible_auto_dev/scripts/automation/lib/host-guard-registry.sh
@@ -114,6 +114,38 @@ _hg_proc_starttime() {
   sed 's/.*) //' "/proc/$pid/stat" 2>/dev/null | awk '{print $20}'
 }
 
+# hg_pid_matches <pid> <starttime> — rc 0 iff that pid is alive AND is still the
+# SAME process. After a machine reset the box comes back with the same pid space,
+# so a pidfile left by the dead boot can point at an innocent live process.
+# `kill -0` alone cannot tell them apart; the start time can.
+hg_pid_matches() {
+  local pid="${1:-}" stt="${2:-}"
+  [[ "$pid" =~ ^[0-9]+$ && -n "$stt" ]] || return 1
+  kill -0 "$pid" 2>/dev/null || return 1
+  [[ "$(_hg_proc_starttime "$pid")" == "$stt" ]]
+}
+
+# hg_boot_epoch — unix time this boot started (/proc/stat btime).
+# HOST_GUARD_BTIME_OVERRIDE is the test seam: no test can reboot a machine.
+hg_boot_epoch() {
+  if [[ -n "${HOST_GUARD_BTIME_OVERRIDE:-}" ]]; then
+    echo "$HOST_GUARD_BTIME_OVERRIDE"; return 0
+  fi
+  awk '/^btime /{print $2; exit}' /proc/stat 2>/dev/null || echo 0
+}
+
+# hg_file_predates_boot <path> — rc 0 iff the file was last written BEFORE this
+# boot began, i.e. it is a leftover from a machine that went down without
+# cleaning up. rc 1 when the file is missing, unreadable, or current.
+hg_file_predates_boot() {
+  local f="${1:-}" mt bt
+  [[ -f "$f" ]] || return 1
+  mt="$(stat -c %Y "$f" 2>/dev/null)" || return 1
+  bt="$(hg_boot_epoch)"
+  [[ "$mt" =~ ^[0-9]+$ && "$bt" =~ ^[0-9]+$ ]] || return 1
+  (( mt < bt ))
+}
+
 # ── Registry ──────────────────────────────────────────────────────────────────
 
 hg_registry_dir() {
@@ -202,6 +234,112 @@ hg_release() { # drop THIS process's engine record (best effort)
   return 0
 }
 
+# ── Durable machine-wide event ledger ─────────────────────────────────────────
+# WHY: after the 2026-07-30 hardware reset nothing on disk could answer the one
+# question forensics needs — "what was the machine doing, across BOTH repos, in
+# the final seconds?". The aggregate verdict is silent when it passes,
+# telemetry.jsonl is per-session and never fsync'd, and engine.log only exists in
+# interactive mode. This ledger is one fsync'd line per chain event for the whole
+# machine, so the postmortem can reconstruct a cross-repo timeline.
+#
+# DURABILITY: `sync <file>` after each append — the same idiom that made the
+# hwmon sampler the only artifact to survive the power-cut with its last second
+# intact. Event rate is a few per minute, so the cost is irrelevant.
+#
+# CONCURRENCY: single-line O_APPEND writes from concurrent engines do not
+# interleave on a local filesystem (lines stay far below the atomic-write bound;
+# oversized payloads are dropped rather than truncated, so a reader never meets
+# half a JSON object). Same local-fs assumption the registry already makes.
+
+hg_events_file() {
+  echo "${HOST_GUARD_EVENTS_FILE:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/events.jsonl}"
+}
+
+# hg_host_mitigations — the host knobs a reset investigation actually turns on,
+# as a JSON fragment. Emitted into the ledger at engine start so a postmortem can
+# say WHICH mitigation was in force during the run. Without this the "one change
+# per soak week" discipline is unfalsifiable after the fact: the postmortem is
+# written on the NEXT boot, by which time a runtime-only change (a C-state
+# disable, a boost toggle) has already reverted and reads as though it was never
+# applied. Cheap: five small sysfs reads, once per engine.
+hg_host_mitigations() {
+  local boost cstates drv gov cmdline s name
+  boost="$(tr -dc '0-9' < "${HOST_GUARD_SYS_BOOST_PATH:-/sys/devices/system/cpu/cpufreq/boost}" 2>/dev/null)"
+  for s in /sys/devices/system/cpu/cpu0/cpuidle/state[0-9]*; do
+    [[ -r "$s/name" && -r "$s/disable" ]] || continue
+    IFS= read -r name < "$s/name" 2>/dev/null || continue
+    cstates+="${cstates:+,}$name:$(tr -dc '0-9' < "$s/disable" 2>/dev/null)"
+  done
+  IFS= read -r drv < /sys/devices/system/cpu/cpuidle/current_driver 2>/dev/null || drv=""
+  IFS= read -r gov < /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || gov=""
+  IFS= read -r cmdline < /proc/cmdline 2>/dev/null || cmdline=""
+  # Read the cap from the FILE, not the environment: the engine emits this at
+  # start, before preflight sources the machine budget, so the env var is still
+  # unset and would misreport a capped host as uncapped. Read-only sed, never a
+  # source — same rule the doctor follows for env it does not own.
+  local cap="${HOST_GUARD_MAX_ENGINES:-}"
+  if [[ -z "$cap" ]]; then
+    cap="$(sed -n 's/^[[:space:]]*HOST_GUARD_MAX_ENGINES[[:space:]]*=[[:space:]]*//p' \
+           "$(hg_host_env_file)" 2>/dev/null | tail -n 1)"
+    cap="${cap//\"/}"; cap="${cap//\'/}"
+  fi
+  printf '{"boost":"%s","cstate_disabled":"%s","idle_driver":"%s","governor":"%s","max_engines":"%s","cmdline":"%s"}' \
+    "${boost:-?}" "${cstates:-?}" "$(_hg_json_esc "$drv")" "$(_hg_json_esc "$gov")" \
+    "${cap:-unset}" "$(_hg_json_esc "${cmdline:0:200}")"
+}
+
+_hg_json_esc() { # minimal JSON string escaping for the fields we control
+  local s="${1:-}"
+  s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; s="${s//$'\n'/ }"; s="${s//$'\t'/ }"
+  printf '%s' "$s"
+}
+
+# hg_event <type> [json-object] — best effort, ALWAYS returns 0.
+# The optional second argument is a JSON OBJECT whose body is spliced into the
+# event (e.g. '{"iter":3}'). Never let a ledger problem touch the engine.
+hg_event() {
+  local type="${1:-}" payload="${2:-}"
+  [[ -n "$type" ]] || return 0
+  # NO-OP RULE (roadmap §20): no machine budget file and no project host-guard
+  # ⇒ this function writes nothing at all, on any host.
+  [[ -f "$(hg_host_env_file)" || "${HOST_GUARD_ENABLED:-0}" == "1" ]] || return 0
+
+  local f dir extra="" iso size max
+  f="$(hg_events_file)"; dir="$(dirname "$f")"
+  mkdir -p "$dir" 2>/dev/null || return 0
+
+  if [[ "$payload" == \{*\} ]]; then
+    extra="${payload#\{}"; extra="${extra%\}}"
+    extra="${extra//$'\n'/ }"
+    if (( ${#extra} > 900 )); then
+      extra=',"payload_dropped":true'      # never emit half an object
+    elif [[ -n "$extra" ]]; then
+      extra=",$extra"
+    fi
+  fi
+
+  printf -v iso '%(%Y-%m-%dT%H:%M:%S)T' -1
+  printf '{"ts":%s,"iso":"%s","boot":"%s","host":"%s","pid":%s,"event":"%s","project":"%s","sid":"%s","agent":"%s"%s}\n' \
+    "$EPOCHSECONDS" "$iso" "$(_hg_boot_id)" \
+    "$(_hg_json_esc "${HOSTNAME:-unknown}")" "$$" "$(_hg_json_esc "$type")" \
+    "$(_hg_json_esc "${REPO_ROOT:-$PWD}")" "$(_hg_json_esc "${GOAL_SESSION_ID:-${SESSION_ID:-}}")" \
+    "$(_hg_json_esc "${CHAIN_CURRENT_AGENT:-}")" "$extra" >> "$f" 2>/dev/null || return 0
+  # fsync so the final pre-reset lines survive an instant power-cut reset
+  sync "$f" 2>/dev/null || sync 2>/dev/null || true
+
+  max="${HOST_GUARD_EVENTS_MAX_BYTES:-5242880}"
+  size="$(stat -c %s "$f" 2>/dev/null || echo 0)"
+  if [[ "$size" =~ ^[0-9]+$ && "$max" =~ ^[0-9]+$ ]] && (( size > max )); then
+    if command -v flock >/dev/null 2>&1; then
+      # A racing rotator doing the same mv is harmless; skip rather than wait.
+      ( flock -n 9 && mv -f "$f" "$f.1" ) 9>"$dir/.events.lock" 2>/dev/null || true
+    else
+      mv -f "$f" "$f.1" 2>/dev/null || true
+    fi
+  fi
+  return 0
+}
+
 # hg_self_is_junior_to <own_rec> <other_rec> — rc 0 when SELF loses.
 # Total order over (epoch, starttime, pid): both sides compute the same answer
 # from the same files, so a conflict never ends in both-pause or neither-pause.
@@ -240,6 +378,33 @@ hg_boost_ok() {
   return 0
 }
 
+# ── Arbitration ───────────────────────────────────────────────────────────────
+# _hg_arbitrate <own_rec> <detail> <live_rec>... → "PAUSE|<msg>" | "WARN|<msg>"
+# Someone has to yield. Compare against every OTHER live engine record: if we are
+# junior to all of them we pause; otherwise we warn and keep running while the
+# junior session pauses itself on its own next check. Extracted so every breach
+# class (mask, memory, engine count) yields by the same deterministic rule.
+_hg_arbitrate() {
+  local own_rec="${1:-}" detail="${2:-}"; shift 2 2>/dev/null || true
+  local other kind junior=0 senior_desc=""
+  for other in "$@"; do
+    [[ "$other" == "$own_rec" ]] && continue
+    kind="$(_hg_rec_field "$other" kind)"
+    [[ "$kind" == "engine" ]] || continue
+    if hg_self_is_junior_to "$own_rec" "$other"; then
+      junior=1
+      senior_desc="session '$(_hg_rec_field "$other" session_id)' in $(_hg_rec_field "$other" project_root) (pid $(_hg_rec_field "$other" pid))"
+      break
+    fi
+  done
+  if (( junior )); then
+    echo "PAUSE|$detail. The older session holds the budget: $senior_desc. Stop or narrow that session, or widen the budget in $(hg_host_env_file), then resume."
+  else
+    echo "WARN|$detail. This session started first, so it keeps running; the newer session is expected to pause itself."
+  fi
+  return 0
+}
+
 # ── Aggregate verdict ─────────────────────────────────────────────────────────
 # hg_aggregate_verdict <own_rec> → "OK" | "WARN|<msg>" | "PAUSE|<msg>"
 #
@@ -273,6 +438,26 @@ hg_aggregate_verdict() {
     fi
   done
 
+  # (0) Concurrent-engine cap, checked BEFORE the budget early-return so it works
+  # on a machine that configures only the cap. This is the honest mitigation for
+  # a host whose resets are HARDWARE (2026-07-30: an uncorrected data fabric sync
+  # flood with every mask/memory check green — see docs/host-guard.md § After a
+  # hardware reset): fewer simultaneous engines shrinks the exposure window, a
+  # narrower mask does not. Absent or invalid ⇒ unlimited ⇒ today's behaviour.
+  local cap="${HOST_GUARD_MAX_ENGINES:-}"
+  if [[ "$cap" =~ ^[0-9]+$ ]] && (( cap >= 1 )); then
+    local n_eng=0 er
+    for er in "${live[@]}"; do
+      [[ "$(_hg_rec_field "$er" kind)" == "engine" ]] && n_eng=$(( n_eng + 1 ))
+    done
+    if (( n_eng > cap )); then
+      _hg_arbitrate "$own_rec" \
+        "$n_eng goal-mode engines are live but this machine allows HOST_GUARD_MAX_ENGINES=$cap ($(hg_host_env_file)) — it is recovering from hardware-asserted resets, so concurrent engines are capped until the hardware soaks clean" \
+        "${live[@]}"
+      return 0
+    fi
+  fi
+
   # No machine budget configured: enforcement is off, but say so loudly once
   # two different projects are guarded at the same time — that is exactly the
   # configuration that reset this host.
@@ -318,25 +503,6 @@ hg_aggregate_verdict() {
 
   [[ -n "$detail" ]] || { echo "OK"; return 0; }
 
-  # Someone has to yield. Compare against every OTHER live engine record: if we
-  # are junior to all of them we pause; otherwise we warn and keep going while
-  # the junior session pauses itself on its own next check.
-  local other kind junior=0 senior_desc=""
-  for other in "${live[@]}"; do
-    [[ "$other" == "$own_rec" ]] && continue
-    kind="$(_hg_rec_field "$other" kind)"
-    [[ "$kind" == "engine" ]] || continue
-    if hg_self_is_junior_to "$own_rec" "$other"; then
-      junior=1
-      senior_desc="session '$(_hg_rec_field "$other" session_id)' in $(_hg_rec_field "$other" project_root) (pid $(_hg_rec_field "$other" pid))"
-      break
-    fi
-  done
-
-  if (( junior )); then
-    echo "PAUSE|$detail. The older session holds the budget: $senior_desc. Stop or narrow that session, or widen the budget in $(hg_host_env_file), then resume."
-  else
-    echo "WARN|$detail. This session started first, so it keeps running; the newer session is expected to pause itself."
-  fi
+  _hg_arbitrate "$own_rec" "$detail" "${live[@]}"
   return 0
 }
diff --git a/incredible_auto_dev/scripts/automation/lib/quota-retry.sh b/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
index 72ef847..1b78788 100644
--- a/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
+++ b/incredible_auto_dev/scripts/automation/lib/quota-retry.sh
@@ -269,6 +269,17 @@ _agent_timeout_for() {
 _INTERACTIVE_DISPATCH_LIB="$(dirname "${BASH_SOURCE[0]}")/interactive-dispatch.sh"
 [[ -f "$_INTERACTIVE_DISPATCH_LIB" ]] && source "$_INTERACTIVE_DISPATCH_LIB"
 
+# Machine-wide durable event ledger (host-guard). Sourced here because
+# agent_with_quota_retry below is the SINGLE dispatch chokepoint for all three
+# backends — the engine AND every run-phase child — so bracketing it is what
+# lets a postmortem say which agent each repo was running at the moment the
+# machine died. Pure library, re-source guarded; a no-op stub keeps vendored
+# copies that lack the lib working unchanged.
+_HOST_GUARD_REGISTRY_LIB="$(dirname "${BASH_SOURCE[0]}")/host-guard-registry.sh"
+# shellcheck source=host-guard-registry.sh
+[[ -f "$_HOST_GUARD_REGISTRY_LIB" ]] && source "$_HOST_GUARD_REGISTRY_LIB"
+declare -f hg_event >/dev/null 2>&1 || hg_event() { :; }
+
 # Append a trace record to $CHAIN_TRACE_DIR/trace.jsonl and copy stdout into
 # $CHAIN_TRACE_DIR/<NNNN>-<agent>.log. No-op if CHAIN_TRACE_DIR is unset, the
 # directory does not exist, or is not writable. Always best-effort: failures
@@ -1228,6 +1239,8 @@ agent_with_quota_retry() {
   # CHAIN_AGENT_BACKEND overrides the CLI for dispatch only (assets/personas
   # still come from CHAIN_CLI). Defaults to the CLI, so absence = today's behaviour.
   local backend="${CHAIN_AGENT_BACKEND:-$cli}"
+  local _hg_t0=$EPOCHSECONDS _hg_rc=0
+  hg_event dispatch_start "$(printf '{"backend":"%s"}' "$backend")"
   case "$backend" in
     interactive) _interactive_invoke "$@" ;;
     claude)      _claude_invoke "$@" ;;
@@ -1237,6 +1250,10 @@ agent_with_quota_retry() {
       return 2
       ;;
   esac
+  _hg_rc=$?
+  hg_event dispatch_end \
+    "$(printf '{"backend":"%s","rc":%s,"dur_s":%s}' "$backend" "$_hg_rc" "$(( EPOCHSECONDS - _hg_t0 ))")"
+  return $_hg_rc
 }
 
 # Back-compat alias. Existing scripts call this name; behaviour now depends on
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index ed95801..55a74b0 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -22,6 +22,15 @@ set -euo pipefail
 REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
 cd "$REPO_ROOT"
 
+# Keep the suite out of the MACHINE's forensic state. Several tests drive real
+# dispatch paths, and hg_event writes to a machine-global ledger by design — so
+# an unredirected eval run buries the record of what the machine was actually
+# doing under hundreds of synthetic events (measured: 398 in one run). The
+# postmortem reader is only as useful as that ledger is honest.
+export HOST_GUARD_EVENTS_FILE="${TMPDIR:-/tmp}/iad-evals-events.$$.jsonl"
+export HOST_GUARD_POSTMORTEM_DIR="${TMPDIR:-/tmp}/iad-evals-postmortems.$$"
+trap 'rm -rf "$HOST_GUARD_EVENTS_FILE" "$HOST_GUARD_EVENTS_FILE.1" "$HOST_GUARD_POSTMORTEM_DIR" 2>/dev/null || true' EXIT
+
 VERBOSE=false
 [[ "${1:-}" == "--verbose" ]] && VERBOSE=true
 
@@ -175,7 +184,7 @@ fi
 
 # ── 2c. Standalone unit-test scripts (API-free by design) ────────────────────
 _log "2c. tests/automation unit tests"
-for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh; do
+for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh tests/automation/test-reset-forensics.sh; do
   if bash "$_t" >/dev/null 2>&1; then
     _pass "unit: $_t"
   else
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index 3c451f2..7b05d02 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -256,6 +256,25 @@ fi
 # check guards against a stale pidfile whose PID was reused by another process.
 if [[ "$RESUME" == "true" && -f "$ENGINE_PID_FILE" ]]; then
   _prev_pid="$(cat "$ENGINE_PID_FILE" 2>/dev/null || echo "")"
+  # A pid file older than this boot means the previous engine never got to clean
+  # up: the machine went down under it. Say so plainly — a session that silently
+  # reappears mid-iteration teaches the operator that iterations vanish at
+  # random, when the truth is one hardware event with a postmortem on disk.
+  if hg_file_predates_boot "$ENGINE_PID_FILE" \
+     && python3 -c "import json,sys; sys.exit(0 if json.load(open('$SESSION_JSON')).get('status')=='in_progress' else 1)" 2>/dev/null; then
+    _pm_dir="${HOST_GUARD_POSTMORTEM_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/postmortems}"
+    echo "[run-goal] Resume: the previous engine (pid $_prev_pid) was killed by a machine reset — its pid file predates this boot and the session was still in_progress." >&2
+    if [[ -f "$_pm_dir/latest.md" ]]; then
+      echo "[run-goal]   what the hardware said: $_pm_dir/latest.md" >&2
+    fi
+    # GOAL_SESSION_DIR is only exported much later (the loop), and
+    # telemetry_enabled silently returns false without it — so the event has to
+    # carry its own session context or it would never be written at all.
+    GOAL_SESSION_DIR="$GOAL_SESSION_DIR_LOCAL" GOAL_SESSION_ID="$SESSION_ID" \
+      record_telemetry_event "halt" '{"reason":"machine_reset","detected_at_step":"resume"}'
+    GOAL_SESSION_ID="$SESSION_ID" \
+      hg_event engine_killed_by_reset "$(printf '{"prev_pid":"%s"}' "$_prev_pid")"
+  fi
   if [[ -n "$_prev_pid" ]] && kill -0 "$_prev_pid" 2>/dev/null \
      && grep -qa "run-goal" "/proc/$_prev_pid/cmdline" 2>/dev/null; then
     echo "[run-goal] Resume: a prior engine (pid $_prev_pid) is still running — stopping it cleanly first." >&2
@@ -926,14 +945,48 @@ _host_guard_sampler_path() { # project-local copy wins; framework copy is the de
   local proj="$REPO_ROOT/project-extensions/host-guard/hwmon-log.sh"
   if [[ -f "$proj" ]]; then printf '%s' "$proj"; else printf '%s' "$SCRIPT_DIR/host-guard/hwmon-log.sh"; fi
 }
-_host_guard_latest_tctl() { # newest Tctl (°C) from the sampler csv; empty if missing/stale
-  local csv="$REPO_ROOT/logs/hwmon/hwmon.csv" mtime line t
-  [[ -f "$csv" ]] || return 0
-  mtime=$(stat -c %Y "$csv" 2>/dev/null || echo 0)
-  (( EPOCHSECONDS - mtime <= 15 )) || return 0
-  line=$(tail -n 1 "$csv" 2>/dev/null || true)
-  t="${line#*,}"; t="${t%%,*}"
-  [[ "$t" =~ ^[0-9]+$ ]] && printf '%s' "$t"
+_host_guard_latest_tctl() { # newest Tctl (°C) from a FRESH sampler csv; empty if none
+  # The machine-global sampler (systemd user unit iad-hwmon.service) wins when it
+  # is running; the per-repo csv remains the fallback so a project that has not
+  # migrated keeps its thermal gate. Whichever csv is fresh is the truth.
+  local csv mtime line t
+  for csv in "${HOST_GUARD_HWMON_GLOBAL_DIR:-${CHAIN_TMP_ROOT:-$HOME/.cache/iad}/host-guard/hwmon}/hwmon.csv" \
+             "$REPO_ROOT/logs/hwmon/hwmon.csv"; do
+    [[ -f "$csv" ]] || continue
+    mtime=$(stat -c %Y "$csv" 2>/dev/null || echo 0)
+    (( EPOCHSECONDS - mtime <= 15 )) || continue
+    line=$(tail -n 1 "$csv" 2>/dev/null || true)
+    t="${line#*,}"; t="${t%%,*}"
+    if [[ "$t" =~ ^[0-9]+$ ]]; then printf '%s' "$t"; return 0; fi
+  done
+  return 0
+}
+# Read the platform's OWN postmortem register and freeze the evidence. Runs
+# before every other host-guard check because check 4's hg_sweep deletes the
+# registry records of the dead boot — the only on-disk record of which projects
+# and sessions were running when the machine went down. Never gates: a
+# hardware-asserted reset is not this session's fault and no rerun can avoid it.
+_host_guard_reset_forensics() {
+  local script="$SCRIPT_DIR/host-guard/reset-forensics.sh" out path state chk
+  local tag hex cause streak prev
+  [[ -f "$script" ]] || return 0
+  out="$(bash "$script" ensure-postmortem 2>/dev/null)" || return 0
+  case "$out" in
+    POSTMORTEM\|*) ;;
+    *) return 0 ;;          # CLEAN / NONE / UNKNOWN — say nothing, write nothing
+  esac
+  path="${out#POSTMORTEM|}"; path="${path%|*}"; state="${out##*|}"
+  chk="$(bash "$script" check 2>/dev/null)" || chk=""
+  IFS='|' read -r tag hex cause streak prev <<< "$chk"
+  : "$tag" "$prev"
+  echo "[run-goal] host-guard: the PREVIOUS boot ended in a HARDWARE-asserted reset — ${cause:-unknown} (${hex:-?}), ${streak:-?} of the recent boots."
+  echo "[run-goal] host-guard: this is a hardware fault, not a chain failure; no CPU mask or memory ceiling can prevent it."
+  echo "[run-goal] host-guard: postmortem → $path"
+  echo "[run-goal] host-guard: remediation → docs/host-guard.md § After a hardware reset — root-cause runbook"
+  record_telemetry_event "host_guard_reset_detected" \
+    "$(printf '{"cause":"%s","code":"%s","streak":"%s","postmortem":"%s","bundle":"%s"}' \
+       "$cause" "$hex" "$streak" "$path" "$state")"
+  hg_event reset_detected "$(printf '{"code":"%s","streak":"%s"}' "$hex" "$streak")"
   return 0
 }
 _host_guard_pause() { # $1 reason, $2 detected_at_step — pause AWAITING_HOST_GUARD (resumable) and exit
@@ -953,6 +1006,7 @@ with _os.fdopen(_fd, "w") as _f:
 _os.replace(_tmp, "$SESSION_JSON")
 PY
   record_telemetry_event "halt" "$(printf '{"reason":"AWAITING_HOST_GUARD","detected_at_step":"%s"}' "$step")"
+  hg_event engine_pause "$(printf '{"reason":"AWAITING_HOST_GUARD","step":"%s"}' "$step")"
   echo ""
   echo "Fix the host-guard issue (project-extensions/host-guard/README.md), then resume:"
   echo "  ./scripts/automation/run-goal.sh --resume --session-id $SESSION_ID"
@@ -966,6 +1020,11 @@ preflight_host_guard() {
   # shellcheck disable=SC1090
   source "$hg_env"
   [[ "${HOST_GUARD_ENABLED:-0}" == "1" ]] || return 0
+
+  # 0. Did the LAST boot die? Capture the postmortem BEFORE check 4 sweeps the
+  # registry records that name who was running. Idempotent: one bundle per boot.
+  _host_guard_reset_forensics
+
   local sampler fail_reason=""
   sampler="$(_host_guard_sampler_path)"
 
@@ -1082,10 +1141,19 @@ host_guard_iteration_gate() {
 
   if [[ "${HOST_GUARD_REQUIRE_PUMP_CONFINED:-0}" == "1" && "${AGENT_BACKEND:-}" == "interactive" ]]; then
     local hb="${CHAIN_DISPATCH_DIR:-$GOAL_SESSION_DIR_LOCAL/dispatch}/.pump-alive"
-    local pump_pid="" hb_age=999999 target="" width allowed_list allowed_n
+    local pump_pid="" hb_age=999999 target="" width allowed_list allowed_n hb_stt=""
     if [[ -f "$hb" ]]; then
       hb_age=$(( EPOCHSECONDS - $(stat -c %Y "$hb" 2>/dev/null || echo 0) ))
       pump_pid=$(sed -n 's/^pid=\([0-9][0-9]*\)$/\1/p' "$hb" 2>/dev/null | head -n 1)
+      # Pid-recycling defense across a machine reset: the heartbeat records the
+      # pump's start time, so a pid that now belongs to some other process — the
+      # normal case after a reboot reuses the pid space — is discarded instead of
+      # being verified, adopted, or (worse) tasksetted.
+      hb_stt=$(sed -n 's/^starttime=\([0-9][0-9]*\)$/\1/p' "$hb" 2>/dev/null | head -n 1)
+      if [[ -n "$pump_pid" && -n "$hb_stt" ]] && ! hg_pid_matches "$pump_pid" "$hb_stt"; then
+        echo "[run-goal] host-guard: .pump-alive names pid $pump_pid, but that process is gone or was recycled (a machine reset reuses pids) — ignoring the stale heartbeat."
+        pump_pid=""
+      fi
     fi
     # Verification handle: the CLI session root captured at engine launch wins
     # (it outlives short-lived heartbeat writers); else the live heartbeat pid.
@@ -1147,6 +1215,12 @@ host_guard_iteration_gate() {
       echo "[run-goal] host-guard WARNING: ${hg_verdict#WARN|}"
       record_telemetry_event "host_guard_aggregate_warn" \
         "$(python3 -c 'import json,sys; print(json.dumps({"detail": sys.argv[1]}))' "${hg_verdict#WARN|}")" ;;
+    OK)
+      # The healthy path used to be entirely silent, so after a reset nothing on
+      # disk said what the guard believed at the time — how many sessions were
+      # live, or that it had checked at all. One durable line per gate fixes it.
+      hg_event aggregate_ok \
+        "$(printf '{"live":%s,"iter":%s}' "$(hg_live_records | wc -l | tr -d ' ')" "${CURRENT_ITER:-0}")" ;;
   esac
   return 0
 }
@@ -1773,6 +1847,7 @@ _goal_engine_on_exit() {
   chain_tmp_cleanup
   # Drop this engine's host-guard registry record so a concurrent project sees
   # the freed budget immediately (the pid sweep would catch it anyway).
+  hg_event engine_stop "$(printf '{"iter":%s}' "${CURRENT_ITER:-0}")" 2>/dev/null || true
   hg_release 2>/dev/null || true
   # REL-4: release LAST so the lock covers the whole cleanup window. Owner-
   # checked no-op when this process never acquired (e.g. a refused start).
@@ -1799,6 +1874,12 @@ trap on_abort INT TERM
 # refuses fast with exit $ENGINE_LOCK_REFUSED_EXIT; a dead one is replaced
 # loudly (lib/engine-lock.sh; docs/TROUBLESHOOTING.md "lock held").
 acquire_engine_lock "$GOAL_SESSION_DIR_LOCAL/.engine.lock" "engine for goal session '$SESSION_ID'" || exit $?
+# Machine-wide durable ledger (survives a power-cut reset; see hg_event).
+hg_event engine_start "$(printf '{"resume":"%s","backend":"%s"}' "${RESUME:-false}" "${AGENT_BACKEND:-}")"
+# Which host mitigations were actually in force for THIS run — the postmortem is
+# written on the next boot, when a runtime-only knob has already reverted, so a
+# soak week is only attributable if the state is recorded while the run happens.
+hg_event host_state "$(hg_host_mitigations)"
 
 # Advisory preflight doctor (REL-2): one PASS/WARN/FAIL table of environment
 # truth into the engine log BEFORE anything mutates state (tmp init/janitor
@@ -2025,6 +2106,7 @@ PY
   PRIOR_DEPTH=$(python3 -c "import json; print(json.load(open('$SESSION_JSON')).get('next_depth') or 'lean')")
 
   record_telemetry_event "iter_start" "$(jq -cn --arg n "$ITER_NAME" --arg pv "$PRIOR_VERDICT" --arg pd "$PRIOR_DEPTH" --arg ss "$(cat "$ITER_DIR/snapshot-sha" 2>/dev/null || echo "")" '{iter_name:$n, prior_verdict:$pv, prior_depth:$pd, snapshot_sha:$ss}' 2>/dev/null || printf '{"iter_name":"%s"}' "$ITER_NAME")"
+  hg_event iter_start "$(printf '{"iter":%s,"name":"%s","depth":"%s"}' "${CURRENT_ITER:-0}" "$ITER_NAME" "$PRIOR_DEPTH")"
   # SPEED-15: wall-clock budget clock starts here; exported so the lean/full
   # executor child processes measure from the same origin.
   export CHAIN_ITER_START_EPOCH="$(date +%s)"
diff --git a/incredible_auto_dev/tests/automation/test-doctor.sh b/incredible_auto_dev/tests/automation/test-doctor.sh
index 4367290..58b5964 100644
--- a/incredible_auto_dev/tests/automation/test-doctor.sh
+++ b/incredible_auto_dev/tests/automation/test-doctor.sh
@@ -136,11 +136,19 @@ run_doctor() {
     if [[ "$a" == "--" ]]; then in_args=true; continue; fi
     $in_args && args+=("$a") || envs+=("$a")
   done
+  # The healthy fixture must stay healthy on ANY host — including one that has
+  # actually had a hardware reset. An empty kernel-log fixture pins reset-reason
+  # (and therefore ras-logging, which keys off reset history) to the clean case;
+  # the postmortem dir is redirected so the row's sanctioned write cannot escape
+  # into the real cache.
   env "PATH=$SHIMS:$FARM" "HOME=$FHOME" \
       "CHAIN_DOCTOR_REPO_ROOT=$FREPO" "CHAIN_TMP_ROOT=$FTMP" \
       "PLAYWRIGHT_BROWSERS_PATH=$TMP_DIR/browsers" "PYTHONPATH=$PYDIR" \
+      "HOST_GUARD_RESET_KLOG_FILE=$TMP_DIR/klog-clean" \
+      "HOST_GUARD_POSTMORTEM_DIR=$TMP_DIR/postmortems" \
       "CHAIN_DOCTOR_AMBIENT=" "${envs[@]}" bash "$DOCTOR" "${args[@]}"
 }
+printf 'Jul 30 17:14:29 host kernel: Linux version 7.0.0-28-generic\n' > "$TMP_DIR/klog-clean"
 
 echo ""
 echo "=== doctor.sh: healthy fixture ==="
@@ -176,9 +184,9 @@ echo ""
 
 rc=0; out=$(run_doctor -- --list 2>&1) || rc=$?
 n=$(echo "$out" | grep -c '^[a-z0-9-]*$' || true)
-{ [[ $rc -eq 0 && $n -eq 17 ]]; } \
-  && assert "--list prints the 17 check keys" "pass" \
-  || assert "--list prints the 17 check keys (rc=$rc n=$n)" "fail"
+{ [[ $rc -eq 0 && $n -eq 19 ]]; } \
+  && assert "--list prints the 19 check keys" "pass" \
+  || assert "--list prints the 19 check keys (rc=$rc n=$n)" "fail"
 echo "$out" | grep -qx "tmp-health" && echo "$out" | grep -qx "chrome-exclusive" \
   && assert "--list includes the evidence-born checks" "pass" \
   || assert "--list includes the evidence-born checks" "fail"
@@ -203,6 +211,8 @@ echo ""
 rc=0; out=$(env "PATH=$SHIMS_NOJQ:$FARM" "HOME=$FHOME" \
     "CHAIN_DOCTOR_REPO_ROOT=$FREPO" "CHAIN_TMP_ROOT=$FTMP" \
     "PLAYWRIGHT_BROWSERS_PATH=$TMP_DIR/browsers" "PYTHONPATH=$PYDIR" \
+    "HOST_GUARD_RESET_KLOG_FILE=$TMP_DIR/klog-clean" \
+    "HOST_GUARD_POSTMORTEM_DIR=$TMP_DIR/postmortems" \
     "CHAIN_DOCTOR_AMBIENT=" bash "$DOCTOR" 2>&1) || rc=$?
 [[ $rc -eq 0 ]] && assert "missing jq: non-strict run still exits 0 (advisory)" "pass" \
                 || assert "missing jq: non-strict run still exits 0 (got $rc)" "fail"
@@ -219,6 +229,8 @@ echo "$out" | grep -Eq '\[doctor\] summary: pass=[0-9]+ warn=0 fail=1 skip=0' \
 rc=0; env "PATH=$SHIMS_NOJQ:$FARM" "HOME=$FHOME" \
     "CHAIN_DOCTOR_REPO_ROOT=$FREPO" "CHAIN_TMP_ROOT=$FTMP" \
     "PLAYWRIGHT_BROWSERS_PATH=$TMP_DIR/browsers" "PYTHONPATH=$PYDIR" \
+    "HOST_GUARD_RESET_KLOG_FILE=$TMP_DIR/klog-clean" \
+    "HOST_GUARD_POSTMORTEM_DIR=$TMP_DIR/postmortems" \
     "CHAIN_DOCTOR_AMBIENT=" bash "$DOCTOR" --strict-doctor >/dev/null 2>&1 || rc=$?
 [[ $rc -eq 1 ]] && assert "missing jq: --strict-doctor exits 1" "pass" \
                 || assert "missing jq: --strict-doctor exits 1 (got $rc)" "fail"
@@ -244,6 +256,8 @@ chmod 755 "$ROTMP"
 rc=0; out=$(env "PATH=$SHIMS_CHROME:$FARM" "HOME=$FHOME" \
     "CHAIN_DOCTOR_REPO_ROOT=$FREPO" "CHAIN_TMP_ROOT=$FTMP" \
     "PLAYWRIGHT_BROWSERS_PATH=$TMP_DIR/browsers" "PYTHONPATH=$PYDIR" \
+    "HOST_GUARD_RESET_KLOG_FILE=$TMP_DIR/klog-clean" \
+    "HOST_GUARD_POSTMORTEM_DIR=$TMP_DIR/postmortems" \
     "CHAIN_DOCTOR_AMBIENT=" bash "$DOCTOR" --only chrome-exclusive 2>&1) || rc=$?
 echo "$out" | grep -Eq 'WARN +chrome-exclusive +.*4242' \
   && assert "chrome-exclusive WARNs naming competing PIDs" "pass" \
diff --git a/incredible_auto_dev/tests/automation/test-engine-lock.sh b/incredible_auto_dev/tests/automation/test-engine-lock.sh
index b5604de..34057dc 100644
--- a/incredible_auto_dev/tests/automation/test-engine-lock.sh
+++ b/incredible_auto_dev/tests/automation/test-engine-lock.sh
@@ -98,6 +98,35 @@ else
     assert "A1 acquire creates lock with pid/host/epoch metadata (never appeared)" "fail"
   fi
 
+  # A1b: the boot id is what survives a machine reset. A reset reuses the pid
+  # space, so a lock left by the boot that died can name a pid that is alive
+  # NOW and even runs a matching command — the pid probe would call that FRESH
+  # and refuse to start, wedging the session until someone deletes it by hand.
+  [[ -s "$L1/boot_id" ]] \
+    && assert "A1b acquire records the boot id" "pass" \
+    || assert "A1b acquire records the boot id" "fail"
+  LB="$WORK/a1b.lock"
+  mkdir -p "$LB"
+  echo "$$" > "$LB/pid"; cat /proc/sys/kernel/random/boot_id > "$LB/boot_id"
+  bash -c 'source "'"$LIB"'"; printf "%s" "$(_engine_lock_host)"' > "$LB/host"
+  date +%s > "$LB/epoch"; basename -- "$0" > "$LB/cmd"
+  V="$(bash -c 'source "'"$LIB"'"; engine_lock_classify "$1"' _ "$LB")"
+  [[ "$V" == FRESH* ]] \
+    && assert "A1b current-boot lock with a live pid is FRESH" "pass" \
+    || assert "A1b current-boot lock with a live pid is FRESH (got: $V)" "fail"
+  echo "dead-beef-from-the-boot-that-died" > "$LB/boot_id"
+  V="$(bash -c 'source "'"$LIB"'"; engine_lock_classify "$1"' _ "$LB")"
+  if [[ "$V" == STALE* && "$V" == *"previous boot"* ]]; then
+    assert "A1b lock from a previous boot is STALE even with a live pid" "pass"
+  else
+    assert "A1b lock from a previous boot is STALE even with a live pid (got: $V)" "fail"
+  fi
+  rm -f "$LB/boot_id"
+  V="$(bash -c 'source "'"$LIB"'"; engine_lock_classify "$1"' _ "$LB")"
+  [[ "$V" == FRESH* ]] \
+    && assert "A1b pre-upgrade lock without a boot id keeps old behaviour" "pass" \
+    || assert "A1b pre-upgrade lock without a boot id keeps old behaviour (got: $V)" "fail"
+
   # A2: a second process must refuse fast with the distinct code + message.
   rc=0; err="$WORK/a2.err"
   bash -c 'source "'"$LIB"'"; acquire_engine_lock "$1" "unit second"' _ "$L1" 2>"$err" || rc=$?
diff --git a/incredible_auto_dev/tests/automation/test-host-guard.sh b/incredible_auto_dev/tests/automation/test-host-guard.sh
index 70dc115..0886a7f 100755
--- a/incredible_auto_dev/tests/automation/test-host-guard.sh
+++ b/incredible_auto_dev/tests/automation/test-host-guard.sh
@@ -221,6 +221,119 @@ CHAIN_TMP_ROOT="$WORK/tmproot" HOST_GUARD_REGISTRY_DIR="$WORK/tmproot/host-guard
     ls \"\$HOST_GUARD_REGISTRY_DIR\"/*.rec >/dev/null 2>&1
   " && assert "registry survives the chain-tmp janitor" pass || assert "registry survives the chain-tmp janitor" fail
 
+# 12. Pid identity across a reboot (HOST-6). A machine reset reuses the pid
+# space, so `kill -0` alone will happily confirm a pid recorded by the boot that
+# died — the start time is what tells the two apart.
+setsid sleep 300 & VP=$!; _SPAWNED_PGIDS+=("$VP")
+wait_for 5 test -d "/proc/$VP"
+_VP_STT="$(_hg_proc_starttime "$VP")"
+hg_pid_matches "$VP" "$_VP_STT" && assert "pid_matches: live pid with its own starttime" pass || assert "pid_matches: live pid with its own starttime" fail
+hg_pid_matches "$VP" "1" && assert "pid_matches: recycled pid rejected" fail || assert "pid_matches: recycled pid rejected" pass
+hg_pid_matches "$VP" "" && assert "pid_matches: missing starttime rejected" fail || assert "pid_matches: missing starttime rejected" pass
+kill -KILL "$VP" 2>/dev/null; wait "$VP" 2>/dev/null
+wait_for 5 bash -c "! kill -0 $VP 2>/dev/null"
+hg_pid_matches "$VP" "$_VP_STT" && assert "pid_matches: dead pid rejected" fail || assert "pid_matches: dead pid rejected" pass
+
+# 13. Boot-relative file age (HOST-7): "was this written before the machine came
+# up?" is how a resume tells a crash from a normal stop. No test can reboot a
+# host, so the boot epoch has an override seam.
+: > "$WORK/agefile"
+HOST_GUARD_BTIME_OVERRIDE=1 hg_file_predates_boot "$WORK/agefile" \
+  && assert "predates_boot: current file is not stale" fail || assert "predates_boot: current file is not stale" pass
+HOST_GUARD_BTIME_OVERRIDE=9999999999 hg_file_predates_boot "$WORK/agefile" \
+  && assert "predates_boot: file older than boot detected" pass || assert "predates_boot: file older than boot detected" fail
+HOST_GUARD_BTIME_OVERRIDE=9999999999 hg_file_predates_boot "$WORK/nope" \
+  && assert "predates_boot: missing file is not stale" fail || assert "predates_boot: missing file is not stale" pass
+
+# 14. Durable event ledger (HOST-4). The ledger is the only cross-repo record of
+# what the machine was doing; it must be valid JSON, must respect the no-op rule,
+# and concurrent engines must not shred each other's lines.
+EVENTS="$WORK/events.jsonl"
+( export HOST_GUARD_EVENTS_FILE="$EVENTS" HOST_GUARD_HOST_ENV_FILE="$WORK/absent.env" HOST_GUARD_ENABLED=0
+  source "$LIB"; hg_event noop_check '{"x":1}' )
+[[ -f "$EVENTS" ]] && assert "event: no-op rule (no host env, not enabled) writes nothing" fail || assert "event: no-op rule (no host env, not enabled) writes nothing" pass
+
+printf 'HOST_GUARD_GLOBAL_CPU_LIST="0-3"\n' > "$WORK/host-guard-host.env"
+HOST_GUARD_EVENTS_FILE="$EVENTS" REPO_ROOT=/fake/projA GOAL_SESSION_ID=sessA \
+  CHAIN_CURRENT_AGENT=developer hg_event iter_start '{"iter":7}'
+assert_eq "event: one line written" "1" "$(wc -l < "$EVENTS" | tr -dc 0-9)"
+if command -v jq >/dev/null 2>&1; then
+  jq -e . "$EVENTS" >/dev/null 2>&1 && assert "event: valid JSON" pass || assert "event: valid JSON" fail
+  assert_eq "event: carries project"  "/fake/projA" "$(jq -r '.project' "$EVENTS")"
+  assert_eq "event: carries session"  "sessA"       "$(jq -r '.sid' "$EVENTS")"
+  assert_eq "event: carries agent"    "developer"   "$(jq -r '.agent' "$EVENTS")"
+  assert_eq "event: carries type"     "iter_start"  "$(jq -r '.event' "$EVENTS")"
+  assert_eq "event: splices payload"  "7"           "$(jq -r '.iter' "$EVENTS")"
+  assert_eq "event: carries boot id"  "$(_hg_boot_id)" "$(jq -r '.boot' "$EVENTS")"
+else
+  grep -q '"event":"iter_start"' "$EVENTS" && assert "event: carries type (no jq)" pass || assert "event: carries type (no jq)" fail
+fi
+
+# An oversized payload must be DROPPED, never truncated: half a JSON object in
+# the ledger would break every reader for every later line.
+: > "$EVENTS"
+HOST_GUARD_EVENTS_FILE="$EVENTS" hg_event big "{\"blob\":\"$(head -c 1200 /dev/zero | tr '\0' 'x')\"}"
+if command -v jq >/dev/null 2>&1; then
+  jq -e . "$EVENTS" >/dev/null 2>&1 && assert "event: oversized payload still valid JSON" pass || assert "event: oversized payload still valid JSON" fail
+fi
+grep -q 'payload_dropped' "$EVENTS" && assert "event: oversized payload dropped, not truncated" pass || assert "event: oversized payload dropped, not truncated" fail
+
+: > "$EVENTS"
+# Wait on THESE pids only: a bare `wait` would also block on the long-lived
+# `sleep 300` victim processes the registration tests keep alive, stalling the
+# suite for minutes.
+_APPENDERS=()
+for _i in $(seq 1 20); do
+  ( HOST_GUARD_EVENTS_FILE="$EVENTS" hg_event "concurrent$_i" '{"n":1}' ) &
+  _APPENDERS+=("$!")
+done
+wait "${_APPENDERS[@]}"
+assert_eq "event: 20 concurrent appenders → 20 lines" "20" "$(wc -l < "$EVENTS" | tr -dc 0-9)"
+if command -v jq >/dev/null 2>&1; then
+  assert_eq "event: every concurrent line is valid JSON" "20" "$(jq -c . "$EVENTS" 2>/dev/null | wc -l | tr -dc 0-9)"
+fi
+
+HOST_GUARD_EVENTS_FILE="$EVENTS" HOST_GUARD_EVENTS_MAX_BYTES=200 hg_event rotate_me '{"n":1}'
+[[ -f "$EVENTS.1" ]] && assert "event: ring rotation at max bytes" pass || assert "event: ring rotation at max bytes" fail
+
+# 15. Concurrent-engine cap (HOST-8). On a host whose resets are HARDWARE, the
+# honest mitigation is fewer engines, not a narrower mask.
+CAPREG="$WORK/capreg"; mkdir -p "$CAPREG"
+setsid sleep 300 & C1=$!; _SPAWNED_PGIDS+=("$C1")
+setsid sleep 300 & C2=$!; _SPAWNED_PGIDS+=("$C2")
+wait_for 5 test -d "/proc/$C1"; wait_for 5 test -d "/proc/$C2"
+CAP_SENIOR="$(HOST_GUARD_REGISTRY_DIR="$CAPREG" hg_register engine "$C1" /fake/capA sA "0-3" 4G)"
+sleep 1
+CAP_JUNIOR="$(HOST_GUARD_REGISTRY_DIR="$CAPREG" hg_register engine "$C2" /fake/capB sB "0-3" 4G)"
+_cap_verdict() { # $1 own_rec, $2 cap
+  HOST_GUARD_REGISTRY_DIR="$CAPREG" HOST_GUARD_GLOBAL_CPU_LIST="0-3" \
+    HOST_GUARD_MAX_ENGINES="$2" hg_aggregate_verdict "$1"
+}
+case "$(_cap_verdict "$CAP_JUNIOR" 1)" in
+  PAUSE\|*) assert "cap: junior engine pauses over HOST_GUARD_MAX_ENGINES=1" pass ;;
+  *)        assert "cap: junior engine pauses over HOST_GUARD_MAX_ENGINES=1" fail ;;
+esac
+_cap_verdict "$CAP_JUNIOR" 1 | grep -q 'HOST_GUARD_MAX_ENGINES=1' \
+  && assert "cap: pause message names the knob" pass || assert "cap: pause message names the knob" fail
+case "$(_cap_verdict "$CAP_SENIOR" 1)" in
+  WARN\|*) assert "cap: senior engine warns and keeps running" pass ;;
+  *)       assert "cap: senior engine warns and keeps running" fail ;;
+esac
+assert_eq "cap: cap=2 with 2 engines is OK"    "OK" "$(_cap_verdict "$CAP_JUNIOR" 2)"
+# The case that matters most on a capped host: ONE engine under cap=1 must run.
+# An off-by-one here (>= instead of >) would pause every single session forever.
+SOLOREG="$WORK/soloreg"; mkdir -p "$SOLOREG"
+CAP_SOLO="$(HOST_GUARD_REGISTRY_DIR="$SOLOREG" hg_register engine "$C1" /fake/solo s1 "0-3" 4G)"
+assert_eq "cap: the ONLY engine runs under cap=1" "OK" \
+  "$(HOST_GUARD_REGISTRY_DIR="$SOLOREG" HOST_GUARD_GLOBAL_CPU_LIST="0-3" \
+     HOST_GUARD_MAX_ENGINES=1 hg_aggregate_verdict "$CAP_SOLO")"
+assert_eq "cap: absent cap = unlimited"        "OK" "$(_cap_verdict "$CAP_JUNIOR" '')"
+assert_eq "cap: junk cap ignored"              "OK" "$(_cap_verdict "$CAP_JUNIOR" 'abc')"
+assert_eq "cap: cap=0 ignored (never lock out)" "OK" "$(_cap_verdict "$CAP_JUNIOR" 0)"
+# A pump is not an engine: only engines count toward the cap.
+HOST_GUARD_REGISTRY_DIR="$CAPREG" hg_register pump "$C1" /fake/capA sA "0-3" 4G >/dev/null
+assert_eq "cap: pump records do not count as engines" "OK" "$(_cap_verdict "$CAP_JUNIOR" 2)"
+
 echo ""
 echo "── B. run-goal.sh wiring (real engine, stub claude) ────────────────────"
 
@@ -308,7 +421,15 @@ else
   assert "engine: pause message names the senior session" fail
   assert "engine: pause message names the memory budget" fail
 fi
-[[ -d "$SBX/runs/goal-session-hg1/.engine.lock" ]] && assert "engine: lock released on host-guard pause" fail || assert "engine: lock released on host-guard pause" pass
+# The paused STATUS is written before the process exits; the lock is released in
+# the EXIT trap that follows. Polling for it is the honest assertion — checking
+# the instant the status flips races the trap, and the race widens with every
+# fsync on the cleanup path (the durable event ledger added two).
+if wait_for 20 bash -c "! [[ -d '$SBX/runs/goal-session-hg1/.engine.lock' ]]"; then
+  assert "engine: lock released on host-guard pause" pass
+else
+  assert "engine: lock released on host-guard pause" fail
+fi
 ls "$ENG_REG"/engine-*.rec 2>/dev/null | grep -qv "engine-$SENIOR-" && assert "engine: junior's own record released on pause" fail || assert "engine: junior's own record released on pause" pass
 
 # B2. With the budget raised the same session proceeds (WARN path, not PAUSE).
diff --git a/incredible_auto_dev/tests/automation/test-reset-forensics.sh b/incredible_auto_dev/tests/automation/test-reset-forensics.sh
new file mode 100644
index 0000000..6aa051a
--- /dev/null
+++ b/incredible_auto_dev/tests/automation/test-reset-forensics.sh
@@ -0,0 +1,265 @@
+#!/usr/bin/env bash
+# test-reset-forensics.sh — the platform's own reset-reason register (HOST-2/3/7):
+#   A. classification: fault vs planned reboot vs clean vs unreadable, and the
+#      fault streak over recent boots
+#   B. the postmortem bundle: who was running, the final pre-reset telemetry,
+#      session tails, idempotency, and the no-op rule on healthy hosts
+#   C. doctor rows (reset-reason, ras-logging) driven by the same fixtures
+#   D. engine wiring: the call sites that make any of this fire
+#
+# Offline, no root, no journal, no model calls: every kernel log, boot list and
+# registry record is a fixture, injected through the documented env seams.
+#
+# WHY THIS SUITE EXISTS: seven hard resets were investigated as software load
+# problems while the CPU printed the cause on every boot. The regression this
+# guards against is silence — a reader that reports CLEAN when it cannot read,
+# or that never gets called.
+
+set -uo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+ENGINE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
+RF="$ENGINE_ROOT/scripts/automation/host-guard/reset-forensics.sh"
+DOCTOR="$ENGINE_ROOT/scripts/automation/doctor.sh"
+
+PASS=0
+FAIL=0
+assert() {
+  if [[ "$2" == "pass" ]]; then echo "  PASS  $1"; PASS=$((PASS + 1)); else echo "  FAIL  $1"; FAIL=$((FAIL + 1)); fi
+}
+assert_eq() { # name expected actual
+  if [[ "$2" == "$3" ]]; then assert "$1" pass; else echo "  FAIL  $1 (expected '$2', got '$3')"; FAIL=$((FAIL + 1)); fi
+}
+assert_has() { # name needle haystack
+  if [[ "$3" == *"$2"* ]]; then assert "$1" pass; else echo "  FAIL  $1 (no '$2' in output)"; FAIL=$((FAIL + 1)); fi
+}
+assert_lacks() { # name needle haystack
+  if [[ "$3" != *"$2"* ]]; then assert "$1" pass; else echo "  FAIL  $1 (unexpected '$2' in output)"; FAIL=$((FAIL + 1)); fi
+}
+
+WORK="$(mktemp -d)"
+cleanup() { rm -rf "$WORK"; return 0; }
+trap cleanup EXIT
+
+# ── Fixtures ────────────────────────────────────────────────────────────────
+# The real lines this machine printed, verbatim — a paraphrase would let the
+# parser drift away from the format it actually has to read.
+FAULT_LINE='Jul 30 17:14:29 host kernel: x86/amd: Previous system reset reason [0x08000800]: an uncorrected error caused a data fabric sync flood event'
+REBOOT_LINE='Jul 21 18:40:54 host kernel: x86/amd: Previous system reset reason [0x00080800]: software wrote 0x6 to reset control register 0xCF9'
+
+mkdir -p "$WORK/klogs"
+printf 'Jul 30 17:14:29 host kernel: Linux version 7.0.0-28-generic\nJul 30 17:14:29 host kernel: Command line: ro quiet\n' > "$WORK/klog-clean"
+{ cat "$WORK/klog-clean"; printf '%s\n' "$FAULT_LINE"; }  > "$WORK/klog-fault"
+{ cat "$WORK/klog-clean"; printf '%s\n' "$REBOOT_LINE"; } > "$WORK/klog-reboot"
+
+# Four boots: two faults, one planned reboot, one clean.
+cat > "$WORK/boots" <<'EOF'
+IDX BOOT ID                          FIRST ENTRY                 LAST ENTRY
+ -3 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1 Mon 2026-07-27 20:46:48 BST Tue 2026-07-28 01:07:32 BST
+ -2 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa2 Tue 2026-07-28 01:08:33 BST Wed 2026-07-29 14:00:08 BST
+ -1 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa3 Wed 2026-07-29 14:03:25 BST Thu 2026-07-30 17:10:26 BST
+  0 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa4 Thu 2026-07-30 17:14:29 BST Thu 2026-07-30 20:56:10 BST
+EOF
+cp "$WORK/klog-clean"  "$WORK/klogs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1.klog"
+cp "$WORK/klog-reboot" "$WORK/klogs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa2.klog"
+cp "$WORK/klog-fault"  "$WORK/klogs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa3.klog"
+cp "$WORK/klog-fault"  "$WORK/klogs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa4.klog"
+
+# A dead boot's registry: two engines and a pump from a boot that no longer is.
+REG="$WORK/registry"; mkdir -p "$REG"
+BOOT_EPOCH=1785400000        # pretend the current boot started here
+_mkrec() { # <file> <kind> <pid> <root> <sid>
+  cat > "$REG/$1" <<EOF
+kind=$2
+pid=$3
+starttime=999999
+boot_id=dead-beef-from-the-boot-that-died
+host=testhost
+epoch=1785351643
+project_root=$4
+session_id=$5
+cpu_list=0-3,8-11
+memory_high=10G
+EOF
+}
+_mkrec "engine-101-999999.rec" engine 101 "$WORK/projA" desk
+_mkrec "engine-102-999999.rec" engine 102 "$WORK/projB" ops
+_mkrec "pump-103-999999.rec"   pump   103 "$WORK/projA" ""
+
+for p in projA projB; do
+  mkdir -p "$WORK/$p/logs/hwmon"
+done
+# Pre-reset samples (epoch < BOOT_EPOCH) plus, for projA, post-reboot samples a
+# restarted sampler would append — the bundle must show the former, not the latter.
+{ echo "epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10,cpu_mhz"
+  for i in $(seq 1 25); do echo "$(( BOOT_EPOCH - 100 + i )),65,57,26,22,40,56,55,20,6.54,11513,28522,0.00,0.00,3900"; done
+  echo "$(( BOOT_EPOCH + 5000 )),44,40,8,5,40,45,44,20,0.10,23000,28671,0.00,0.00,1200"
+} > "$WORK/projA/logs/hwmon/hwmon.csv"
+{ echo "epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10,cpu_mhz"
+  echo "$(( BOOT_EPOCH - 3 )),74,60,37,30,41,57,56,21,7.28,11424,28522,0.00,0.00,4100"
+} > "$WORK/projB/logs/hwmon/hwmon.csv"
+
+mkdir -p "$WORK/projA/runs/goal-session-desk" "$WORK/projB/runs/goal-session-ops"
+printf '{"event":"iter_start","iter":26}\n{"event":"coherence_pass","iter":26}\n' \
+  > "$WORK/projA/runs/goal-session-desk/telemetry.jsonl"
+printf '16:56:11 [browser-qa] dispatching J-05 UNIQUEMARKER_ENGINELOG\n' \
+  > "$WORK/projA/runs/goal-session-desk/engine.log"
+printf '{"status":"in_progress","current_iter":26}\n' \
+  > "$WORK/projA/runs/goal-session-desk/session.json"
+printf '{"event":"iter_start","iter":39}\n' > "$WORK/projB/runs/goal-session-ops/telemetry.jsonl"
+
+PM="$WORK/postmortems"
+export HOST_GUARD_RESET_BOOTS_FILE="$WORK/boots"
+export HOST_GUARD_RESET_KLOG_DIR="$WORK/klogs"
+export HOST_GUARD_POSTMORTEM_DIR="$PM"
+export HOST_GUARD_REGISTRY_DIR="$REG"
+export HOST_GUARD_BTIME_OVERRIDE="$BOOT_EPOCH"
+export HOST_GUARD_EVENTS_FILE="$WORK/events.jsonl"
+
+echo "── A. classification ───────────────────────────────────────────────────"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" check)"
+assert_has "check: fault reported as RESET"       "RESET|0x08000800|" "$OUT"
+assert_has "check: cause text preserved"          "data fabric sync flood" "$OUT"
+assert_has "check: streak counts fault boots only" "|2/4|" "$OUT"
+assert_has "check: names the dead boot"           "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa3" "$OUT"
+
+# The single highest-value false positive to avoid: an ordinary `reboot` also
+# prints a reset-reason line. Treating it as an incident would cry wolf forever.
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-reboot" bash "$RF" check)"
+assert_has   "check: planned reboot is CLEAN"        "CLEAN|" "$OUT"
+assert_has   "check: planned reboot says why"        "software-initiated reboot" "$OUT"
+assert_lacks "check: planned reboot is not a RESET"  "RESET|" "$OUT"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-clean" bash "$RF" check)"
+assert_has "check: clean boot reported CLEAN" "CLEAN|" "$OUT"
+
+# Unreadable ≠ clean. A reader that cannot see the register must SAY so, or it
+# silently certifies every machine as healthy.
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/does-not-exist" bash "$RF" check)"
+assert_has "check: unreadable log → UNKNOWN, never CLEAN" "UNKNOWN|" "$OUT"
+# The realistic failure: journalctl EXISTS but returns nothing because this user
+# cannot read the kernel log. Without the liveness probe that case would look
+# exactly like a healthy machine.
+mkdir -p "$WORK/bin"
+printf '#!/bin/sh\nexit 1\n' > "$WORK/bin/journalctl"; chmod +x "$WORK/bin/journalctl"
+OUT="$(PATH="$WORK/bin:$PATH" HOST_GUARD_RESET_KLOG_FILE="" bash "$RF" check 2>/dev/null)"
+assert_has   "check: silent journalctl → UNKNOWN, never CLEAN" "UNKNOWN|" "$OUT"
+assert_has   "check: UNKNOWN explains how to fix access"        "systemd-journal" "$OUT"
+
+echo ""
+echo "── B. postmortem bundle ────────────────────────────────────────────────"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-clean" bash "$RF" ensure-postmortem)"
+assert_has "bundle: clean boot → NONE" "NONE|" "$OUT"
+[[ -d "$PM" && -n "$(ls -A "$PM" 2>/dev/null)" ]] \
+  && assert "bundle: NO-OP RULE — clean boot writes no file" fail \
+  || assert "bundle: NO-OP RULE — clean boot writes no file" pass
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" ensure-postmortem)"
+assert_has "bundle: fault → POSTMORTEM|…|new" "|new" "$OUT"
+BUNDLE="$PM/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa3.md"
+[[ -f "$BUNDLE" ]] && assert "bundle: named after the dead boot" pass || assert "bundle: named after the dead boot" fail
+BODY="$(cat "$BUNDLE" 2>/dev/null)"
+
+assert_has "bundle: verbatim reset line"        "0x08000800" "$BODY"
+assert_has "bundle: boot history table"         "**FAULT**" "$BODY"
+assert_has "bundle: marks the planned reboot"   "| reboot |" "$BODY"
+assert_has "bundle: names both dead engines"    "$WORK/projA" "$BODY"
+assert_has "bundle: names the second project"   "$WORK/projB" "$BODY"
+assert_has "bundle: names the dead session"     "session_id=desk" "$BODY"
+assert_has "bundle: keeps the pump record too"  "kind=pump" "$BODY"
+assert_has "bundle: session telemetry tail"     '"event":"coherence_pass"' "$BODY"
+assert_has "bundle: engine log tail"            "UNIQUEMARKER_ENGINELOG" "$BODY"
+assert_has "bundle: session.json state"         '"status":"in_progress"' "$BODY"
+assert_has "bundle: points at the runbook"      "docs/host-guard.md" "$BODY"
+
+# The telemetry window must be BOOT-RELATIVE. A sampler that restarted after the
+# reboot keeps appending, and a plain `tail` would present live idle data as the
+# machine's dying breath.
+assert_has   "bundle: final pre-reset sample selected" "$(( BOOT_EPOCH - 75 ))" "$BODY"
+assert_lacks "bundle: post-reboot samples excluded"    "$(( BOOT_EPOCH + 5000 ))" "$BODY"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" ensure-postmortem)"
+assert_has "bundle: second run is idempotent" "|existing" "$OUT"
+BEFORE="$(stat -c %Y "$BUNDLE")"
+HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" ensure-postmortem >/dev/null
+assert_eq "bundle: existing bundle is not rewritten" "$BEFORE" "$(stat -c %Y "$BUNDLE")"
+[[ -L "$PM/latest.md" ]] && assert "bundle: latest.md points at the newest" pass || assert "bundle: latest.md points at the newest" fail
+assert_has "report: prints the bundle" "0x08000800" "$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" bash "$RF" report 2>/dev/null)"
+
+echo ""
+echo "── C. doctor rows ──────────────────────────────────────────────────────"
+
+_doc() { # $1 check key — env overrides come from the caller's prefix
+  env CHAIN_DOCTOR_REPO_ROOT="$WORK/projA" bash "$DOCTOR" --only "$1" 2>&1
+}
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" _doc reset-reason)"
+assert_has "doctor: reset-reason FAILs after a hardware reset" "FAIL" "$OUT"
+assert_has "doctor: row carries the code"                      "0x08000800" "$OUT"
+assert_has "doctor: row points at the postmortem"              "$PM/" "$OUT"
+assert_lacks "doctor: row is one line (no crash wrapper)"      "check crashed" "$OUT"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-clean" _doc reset-reason)"
+assert_has "doctor: clean boot PASSes" "PASS" "$OUT"
+
+# ras-logging must stay quiet on hosts that never had the incident, and must not
+# smuggle a newline into its row (systemctl prints AND exits non-zero).
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-clean" CHAIN_DOCTOR_RAS_STATE=inactive \
+       CHAIN_DOCTOR_JOURNALD_DIR="$WORK/nojournald" _doc ras-logging)"
+assert_has   "doctor: ras-logging quiet without reset history" "PASS" "$OUT"
+assert_lacks "doctor: ras-logging never crashes the wrapper"   "check crashed" "$OUT"
+
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" CHAIN_DOCTOR_RAS_STATE=inactive \
+       CHAIN_DOCTOR_JOURNALD_DIR="$WORK/nojournald" _doc ras-logging)"
+assert_has "doctor: ras-logging WARNs once the host has history" "WARN" "$OUT"
+assert_has "doctor: WARN names rasdaemon"                        "rasdaemon" "$OUT"
+
+mkdir -p "$WORK/journald.d"; printf '[Journal]\nSyncIntervalSec=15s\n' > "$WORK/journald.d/99-iad-sync.conf"
+OUT="$(HOST_GUARD_RESET_KLOG_FILE="$WORK/klog-fault" CHAIN_DOCTOR_RAS_STATE=active \
+       CHAIN_DOCTOR_JOURNALD_DIR="$WORK/journald.d" _doc ras-logging)"
+assert_has "doctor: ras-logging PASSes once both are in place" "PASS" "$OUT"
+
+assert_has "doctor: reset-reason is a registered check" "reset-reason" "$(bash "$DOCTOR" --list)"
+assert_has "doctor: ras-logging is a registered check"  "ras-logging"  "$(bash "$DOCTOR" --list)"
+
+echo ""
+echo "── D. engine wiring ────────────────────────────────────────────────────"
+
+RG="$ENGINE_ROOT/scripts/automation/run-goal.sh"
+grep -q '_host_guard_reset_forensics' "$RG" \
+  && assert "wiring: engine preflight reads the reset register" pass \
+  || assert "wiring: engine preflight reads the reset register" fail
+# Ordering is the whole point: hg_sweep deletes the records that say who was
+# running, so the postmortem has to be taken first.
+_fx="$(grep -n '^[[:space:]]*_host_guard_reset_forensics[[:space:]]*$' "$RG" | head -n 1 | cut -d: -f1)"
+_sw="$(grep -n '^[[:space:]]*hg_sweep[[:space:]]*$' "$RG" | head -n 1 | cut -d: -f1)"
+if [[ -n "$_fx" && -n "$_sw" ]] && (( _fx < _sw )); then
+  assert "wiring: forensics runs BEFORE the registry sweep" pass
+else
+  assert "wiring: forensics runs BEFORE the registry sweep" fail
+fi
+grep -q 'machine_reset' "$RG" \
+  && assert "wiring: resume reports a reset-killed session" pass \
+  || assert "wiring: resume reports a reset-killed session" fail
+grep -q 'GOAL_SESSION_DIR="$GOAL_SESSION_DIR_LOCAL" GOAL_SESSION_ID="$SESSION_ID" \\' "$RG" \
+  && assert "wiring: resume event carries its own session context" pass \
+  || assert "wiring: resume event carries its own session context" fail
+grep -q 'hg_event engine_start' "$RG" \
+  && assert "wiring: engine start is ledgered" pass || assert "wiring: engine start is ledgered" fail
+grep -q 'hg_event aggregate_ok' "$RG" \
+  && assert "wiring: the HEALTHY aggregate verdict is ledgered too" pass \
+  || assert "wiring: the HEALTHY aggregate verdict is ledgered too" fail
+QR="$ENGINE_ROOT/scripts/automation/lib/quota-retry.sh"
+grep -q 'hg_event dispatch_start' "$QR" && grep -q 'hg_event dispatch_end' "$QR" \
+  && assert "wiring: every agent dispatch is bracketed in the ledger" pass \
+  || assert "wiring: every agent dispatch is bracketed in the ledger" fail
+grep -q 'iad-hwmon.service' "$ENGINE_ROOT/docs/host-guard.md" 2>/dev/null \
+  && assert "wiring: the machine-global sampler unit is documented" pass \
+  || assert "wiring: the machine-global sampler unit is documented" fail
+
+echo ""
+echo "──────────────────────────────────────────────────────────────────────"
+echo "  PASS: $PASS   FAIL: $FAIL"
+[[ "$FAIL" -eq 0 ]]
diff --git a/project-extensions/host-guard/host-guard.env b/project-extensions/host-guard/host-guard.env
index e3c844c..50696c4 100644
--- a/project-extensions/host-guard/host-guard.env
+++ b/project-extensions/host-guard/host-guard.env
@@ -1,14 +1,23 @@
 # host-guard.env — per-host resource ceilings for the AI dev chain (tapeology).
 #
 # WHY THIS EXISTS: this host (GEEKOM A7 Max mini-PC, Ryzen 9 7940HS, 27 GB RAM)
-# hard-reset FIVE times between 2026-07-20 and 2026-07-28 while goal mode ran —
+# hard-reset seven times between 2026-07-20 and 2026-07-30 while goal mode ran —
 # no OOM, no thermal log, no kernel panic, machine back up within ~1 minute.
-# The 1 Hz hwmon forensics (trendora/logs/hwmon/) captured the final second of
-# the last three resets at benign temps and low package power: the trigger is a
-# millisecond-scale power/VRM transient from bursty all-core load, invisible to
-# any sampler. These caps bound how many CPUs a burst can light at once.
-# Resets #3-#5 happened while tapeology's goal mode ran UNGUARDED (this file
-# did not exist) alongside trendora's — hence the complementary masks below.
+#
+# ROOT CAUSE, SETTLED 2026-07-30: it is HARDWARE. The kernel prints it on the
+# boot after every reset — "x86/amd: Previous system reset reason [0x08000800]:
+# an uncorrected error caused a data fabric sync flood event", on 7 of the last
+# 10 boots, once at load 1.53 and 22 W. An uncorrectable SoC/Infinity-Fabric
+# error makes the hardware assert reset with the OS never notified, so NO cap in
+# this file can prevent it. Reset #7 proved it: it happened with the mask, the
+# memory ceiling, boost-off and browser confinement all in force and green.
+#
+# The earlier theory in this file — "a millisecond-scale power/VRM transient
+# from bursty all-core load" — was wrong, and the CPU mask that followed from it
+# was released on 2026-07-30 (see below). What these caps are still good for:
+# bounding memory, bounding fork storms, and keeping the forensics sampler and
+# the reset-reason reader armed. The real fix is firmware/DRAM and belongs to
+# the operator: incredible_auto_dev/docs/host-guard.md § After a hardware reset.
 # Incident details + runbooks: trendora/project-extensions/host-guard/README.md.
 #
 # CONTRACT: plain KEY=VALUE bash assignments only — this file is `source`d by
@@ -19,26 +28,27 @@
 # Master switch for all host-guard behavior (engine wrap, preflight, gates).
 HOST_GUARD_ENABLED=1
 
-# SMT-AWARE CPU affinity mask. 7940HS sibling pairs are (0,8)(1,9)...(7,15).
-# CHANGED 2026-07-29 (was "4-7,12-15"): the complementary-mask scheme was the
-# CAUSE of reset #6, not a defense. Each project passed its own check while the
-# union — "0-3,8-11" ∪ "4-7,12-15" — was all 16 CPUs, i.e. every physical core
-# available to one burst. Both projects now SHARE this mask, so cores 4-7 stay
-# dark however many projects run. The two goal modes contend for these 8
-# hyperthreads when both dispatch at once; that contention is the price of the
-# headroom. Must remain a subset of HOST_GUARD_GLOBAL_CPU_LIST in
-# ~/.config/iad/host-guard-host.env — the engine pauses otherwise.
-HOST_GUARD_CPU_LIST="0-3,8-11"
+# CPU affinity mask. 7940HS sibling pairs are (0,8)(1,9)...(7,15).
+# RELEASED TO THE WHOLE MACHINE 2026-07-30 (was "0-3,8-11", and "4-7,12-15"
+# before that). Both narrowings were defences against a power-transient theory
+# that reset #7 refuted: the machine reset with "0-3,8-11" in force at 26-37 W
+# and 65-74 °C on a 35-54 W part, because the fault is an uncorrected data
+# fabric error no mask can reach. Half the box was kept dark for nothing.
+# Must remain a subset of HOST_GUARD_GLOBAL_CPU_LIST in
+# ~/.config/iad/host-guard-host.env — the engine pauses otherwise, so widen the
+# machine budget FIRST. Concurrency is now bounded by HOST_GUARD_MAX_ENGINES
+# there instead: how long the box is under load, not which cores carry it.
+HOST_GUARD_CPU_LIST="0-15"
 
 # BLAS/OpenMP/numexpr worker cap: one per physical core in the mask, so N
 # numpy processes cannot oversubscribe the mask with nested thread pools.
-HOST_GUARD_BLAS_THREADS=4
+HOST_GUARD_BLAS_THREADS=8
 
-# systemd user-scope backstops (engine wrap + pump wrapper; skipped when no
-# user bus). CPUQuota averages over ~100 ms so it CANNOT stop the sub-100 ms
-# transient — the cpuset/taskset mask above is the real limiter; this catches
-# sustained overshoot.
-HOST_GUARD_CPUQUOTA="800%"
+# systemd user-scope backstop (engine wrap + pump wrapper; skipped when no user
+# bus). Raised with the mask on 2026-07-30 (was 800%): a quota below the mask
+# width would silently re-impose the cap the mask no longer applies. This bounds
+# sustained overshoot only — it never had anything to do with the reset.
+HOST_GUARD_CPUQUOTA="1600%"
 # Aggregate memory ceiling (reclaim+throttle, never OOM-kill). 10G since
 # 2026-07-29 (was 14G): 14G + 14G = 28G was over the 27.3G installed, and no
 # per-project check could see that. 10G + 10G = 20G fits the 22G machine budget
diff --git a/apps/backend/tests/test_desk_topup_window_disclosure_guard.py b/apps/backend/tests/test_desk_topup_window_disclosure_guard.py
new file mode 100644
index 0000000..e0a516d
--- /dev/null
+++ b/apps/backend/tests/test_desk_topup_window_disclosure_guard.py
@@ -0,0 +1,83 @@
+"""goal-desk-iter-26 (J-17) source-introspection guard test -- the ``test_desk_ui_guards.py``/
+``test_desk_hover_tooltip_guard.py`` pattern (read ``apps/frontend/app/desk/page.tsx`` as TEXT,
+assert on substrings/structure; no browser, no runtime).
+
+Proves the Top-up Runs section's window-disclosure additions actually landed and stay wired the
+way the DoD requires:
+
+  (a) the honest legacy-run fallback text ``"window basis not recorded in this run"`` exists as
+      ONE shared constant (never a second, divergent copy of the string), used by BOTH the
+      tail-vs-full-lookback line and the per-failed-pair window line;
+  (b) the four-outcome counts line (``reused``/``fetched``/``unchanged``/``failed``) is present;
+  (c) ``topupWindowBasisCounts`` never computes a value when any outcome lacks ``window_basis`` --
+      it returns ``null`` in that case, which the render layer maps to the honest fallback rather
+      than a guessed/backfilled count.
+
+A guard that can never fail proves nothing -- ``test_the_fallback_text_guard_can_fail_on_a_seeded_
+violation`` below seeds a violation (a second, drifted copy of the fallback string) and proves the
+same check catches it."""
+
+from __future__ import annotations
+
+import pathlib
+import re
+
+_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
+_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
+
+_FALLBACK_TEXT = "window basis not recorded in this run"
+
+
+def _source() -> str:
+    return _DESK_PAGE.read_text()
+
+
+def test_the_legacy_fallback_text_is_a_single_shared_constant():
+    source = _source()
+    # Exactly ONE string literal carries the fallback text (a `const` definition) -- every OTHER
+    # occurrence in the file references that constant by name, never repeats the literal.
+    literal_occurrences = source.count(f'"{_FALLBACK_TEXT}"')
+    assert literal_occurrences == 1, (
+        f"expected the fallback text to be defined as ONE shared string literal, found "
+        f"{literal_occurrences} -- a second, independently-typed copy risks drifting out of sync"
+    )
+    assert "WINDOW_BASIS_NOT_RECORDED" in source
+
+
+def test_the_tail_vs_full_lookback_line_and_the_failed_pair_window_line_both_use_the_shared_constant():
+    source = _source()
+    assert source.count("WINDOW_BASIS_NOT_RECORDED") >= 3  # 1 definition + >=2 usages
+
+
+def test_the_four_outcome_counts_line_is_present():
+    source = _source()
+    assert "counts.reused" in source
+    assert "counts.fetched" in source
+    assert "counts.unchanged" in source
+    assert "counts.failed" in source
+
+
+def test_window_basis_counts_returns_null_when_any_outcome_lacks_window_basis():
+    """``topupWindowBasisCounts``'s own source slice (from its declaration to the NEXT top-level
+    ``function`` declaration -- simpler and more robust than brace-matching, since the function's
+    OWN return-type annotation is itself a brace-balanced object type that would otherwise close a
+    naive brace counter early) structurally returns ``null`` on an absent field rather than
+    defaulting/backfilling a count."""
+    source = _source()
+    marker = "function topupWindowBasisCounts("
+    start = source.index(marker)
+    next_fn = source.index("\nfunction ", start + len(marker))
+    body = source[start:next_fn]
+    assert "window_basis === undefined" in body
+    assert re.search(r"return\s+null", body) is not None
+
+
+def test_the_fallback_text_guard_can_fail_on_a_seeded_violation():
+    """A guard that can never fail proves nothing -- a seeded SECOND, independently-typed copy of
+    the fallback text is caught by the same counting check above."""
+    seeded = (
+        'const WINDOW_BASIS_NOT_RECORDED = "window basis not recorded in this run";\n'
+        'const other = "window basis not recorded in this run";\n'
+    )
+    literal_occurrences = seeded.count(f'"{_FALLBACK_TEXT}"')
+    assert literal_occurrences != 1
```
