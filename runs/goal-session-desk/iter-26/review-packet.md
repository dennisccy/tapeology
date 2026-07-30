# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

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
diff --git a/docs/goal.md b/docs/goal.md
index a95f9a8..10c797f 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1276,6 +1276,131 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     own it, while the iter-21 and iter-23 walkthrough films were RECORDED_WITH_NOTES for exactly this
     reason.)*
 
+- **J-17: A top-up asks the vendor only for the bars the frozen store cannot already prove**
+  - Steps:
+    1. Choose each pair's fetch window from that pair's OWN frozen content, read verbatim from the
+       canonical owner — the single ascending `BarStore.merged_bars(symbol, timeframe)` read
+       (`bars.py:557`, the SAME accessor `desk_screen._resolve_reference_close_and_history` and
+       `tradability._select_daily_series` already use), never from `bar_index`'s
+       `window_end_utc`, which records what an earlier run ASKED for rather than what the store can
+       prove (and whose single owner stays `desk_coverage`). Exactly three cases, decided per pair
+       inside the shared walker's own `_run_one_pair` (`desk_topup_compute.py:141`): a pair with
+       NOTHING frozen keeps the byte-identical full `_TOPUP_LOOKBACK_DAYS` window it asks for today
+       (`:98`/`_fetch_window_now`, `:109`); a pair whose frozen bars do NOT reach back to that
+       lookback start keeps that SAME full window, so short histories keep deepening exactly as they
+       do now; and a pair whose frozen bars already reach the lookback start asks for a tail window
+       `[the pair's own newest frozen bar's UTC date, today]`, so the boundary session is always
+       re-requested and re-merged, never assumed complete. The end bound stays `_fetch_window_now()`'s
+       wall-clock today, unchanged. **Zero diff** to `bars.py`, `record_bar_series`
+       (`routes.py:521`), `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py` and
+       `levels.py`: the SAME single fetch-and-record seam is called with a different window — no
+       second fetch path, no new adapter, no new store, no new `Config` field (`_TOPUP_LOOKBACK_DAYS`
+       stays the module constant it is).
+    2. Name the vendor's "you already have this" answer honestly. `record_bar_series` refuses content
+       already registered with the frozen store's own 409 (`BarSeriesAlreadyRegistered`,
+       `routes.py:681`), which `_run_one_pair`'s `except HTTPException` records as `failed` today — a
+       tail window makes that the NORMAL weekend/holiday answer. Add exactly ONE new outcome value,
+       `unchanged` (a vendor call ran and returned only bars already frozen), beside J-09's shipped
+       `reused` (a store-first exact-key hit with ZERO vendor calls — its meaning stays
+       byte-unchanged), `fetched` and `failed`; every other refusal keeps its verbatim detail and its
+       `failed` label, and nothing is ever recorded as reused that a vendor call actually served.
+    3. Record what each pair asked for and why: on each per-pair outcome entry, `requested_window`
+       (`{start, end}` — the exact strings that pair sent), `store_frozen_from` and
+       `store_frozen_through` (that pair's own earliest/newest frozen bar, both `null` when nothing is
+       frozen) and `window_basis` (`"tail"` | `"full_lookback"`; names at build discretion), written
+       at the run's terminal state by the SAME single shared writer both callers already use
+       (`desk_topup_log.record_topup_run`, from the manager's resolve path and the CLI's `main`) —
+       never a second writer, never a second outcome shape. The run-level `requested_window` keeps its
+       recorded meaning verbatim (the run's own full-lookback bound). The append-only rail is
+       absolute: no recorded run is backfilled, rewritten or recomputed;
+       `GET /research/desk/topup/runs` serves legacy runs exactly as recorded and `/desk` renders
+       their absent fields as an honest `"window basis not recorded in this run"` (the established
+       J-08/J-11/J-13 legacy-absence pattern), never a value derived at read time.
+    4. Own it exactly once: register the added per-pair fields and the `unchanged` value on the
+       blueprint Data Contract's top-up-run-record row BEFORE the code lands — `desk_topup_log` stays
+       the only owner and `GET /research/desk/topup/runs` the only serving endpoint. No new endpoint,
+       route, store, `Config` field or MCP tool (J-06's exactly-17-tool contract stays green and
+       `get_endpoint`'s `/research/` allowlist already reaches the path). Coverage and freshness keep
+       their single existing owner — `desk_coverage.get_desk_coverage` over `bar_index` — and this
+       journey creates no second coverage path and serves no coverage value; the top-up stays an
+       explicit operator act (POST + CLI + the shipped button), page-load GETs trigger nothing, and no
+       scheduler, retry loop or auto-refresh is added anywhere.
+    5. Surface it on `/desk` inside the SHIPPED Top-up Runs section — no new section, no new control,
+       and NO new column on the ranked table, so J-16's measured width contract stands untouched: the
+       latest-run counts line extends to `N reused · N fetched · N unchanged · N failed`
+       (`topupOutcomeCounts`, `apps/frontend/app/desk/page.tsx:809` — a plain tally of the served
+       payload, nothing derived), one descriptive line states how many pairs asked for a tail window
+       and how many for the full lookback, and each already-rendered failed pair additionally shows
+       its own recorded `requested_window`. Copy = descriptive measurement only: the page states what
+       was asked for and what came back, and never a saving, waste, efficiency, speed or
+       recommendation claim; `tests/test_copy_discipline.py` stays green unmodified.
+    6. Test fixture-scoped with the suite's own injected fake adapter (the `test_desk_topup_compute.py`
+       pattern — no test touches the network): a pair whose planted frozen bars span past the lookback
+       start asks for a tail window starting at its own newest frozen bar (asserted BOTH on the
+       adapter's received arguments and on the recorded entry); a pair with a short frozen history and
+       a pair with nothing frozen each ask for the byte-identical full window they ask for today; a
+       fetch whose answer holds only already-frozen bars records `unchanged`, not `failed`, and writes
+       no second series file; and every EXISTING test in `test_desk_topup_compute.py` — including
+       TC-7's "a second run is all-reused with zero vendor calls" and TC-8's resumability guarantee —
+       passes UNMODIFIED (if any existing assertion genuinely pins the shipped window for a pair whose
+       frozen history already reaches the lookback start, disclose it in the iteration record rather
+       than edit the test).
+  - Acceptance: on the fixture-scoped rig, a pair whose frozen series reaches back past the lookback
+    start is asked for `[that pair's own newest frozen bar's UTC date, today]` — proven by the fake
+    adapter's received window AND by the run record's own `requested_window`/`store_frozen_through` —
+    while a pair with nothing frozen, and a pair whose frozen history stops short of the lookback
+    start, are each asked for the byte-identical full `_TOPUP_LOOKBACK_DAYS` window they are asked for
+    today (a golden comparison proves the shipped window unmoved for both); a vendor answer holding
+    only already-frozen bars is recorded `unchanged` with its `requested_window` and adds no second
+    series file, never `failed` (**single source of truth**: the window is derived only from the
+    canonical `BarStore`'s own merged read — never from `bar_index`'s request-bound `window_end_utc` —
+    the run record stays owned by `desk_topup_log` alone and served by `GET /research/desk/topup/runs`
+    alone, with the added fields and the new outcome value registered in the Data Contract BEFORE the
+    code lands, and coverage/freshness still come solely from `desk_coverage` over `bar_index`; this
+    SSOT criterion stands in place of a PnL-ledger append, which this era's Non-Goals forbid); every
+    bar series file already on disk is proven byte-identical before and after the iteration (SHA-256
+    listing — a top-up only ever APPENDS a new series; nothing is deleted, re-keyed, superseded or
+    rewritten), and every previously recorded universe, screen, top-up and reconciliation record is
+    proven byte-identical too, with legacy top-up runs rendering the honest `"window basis not
+    recorded in this run"` state; in a real browser after the T-9 clean rebuild, `/desk`'s Top-up Runs
+    section shows the four-outcome counts including at least one `unchanged`, the tail-versus-full
+    window line, and one failed pair with its own recorded `requested_window`, all legible in ONE
+    screenshot at a 1440×900 viewport with no horizontal scroll, and the ranked briefing table renders
+    exactly as J-16 shipped it (T-10: no screenshot ⇒ `unknown`, never `passing`; no native `title`
+    tooltip is required by this journey, so the T-10a headed rig is not needed); a
+    **`[NEW]`-flagged demo-narrator walkthrough** covers the top-up's window disclosure end to end,
+    narrated over a populated run; and the full backend suite is green with
+    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
+    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17 tools,
+    zero diff to
+    `bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/`tradability.py`/`levels.py`/`StructureChart.tsx`,
+    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
+    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable. The
+    real ~100-symbol Yahoo top-up stays an operator-run act, reported honestly as run-or-not-run —
+    never a CI gate. Why: measured 2026-07-30 from the desk's own recorded ledger and the frozen store.
+    The one recorded real top-up, `topup-2026-07-29-5de907c83fc4` (404 pairs, 12:00:29Z → 12:04:53Z),
+    reports **`0 reused · 390 fetched · 14 failed`** — `reused` has never once been recorded on a real
+    run. Cause: `_fetch_window_now()` is wall-clock (end = today, start = 730 d earlier) while
+    `record_bar_series`'s store-first is an **exact-key** `(symbol, timeframe, window_start,
+    window_end)` index hit (its own docstring, `routes.py:558`), so a window whose end moves each day
+    can structurally never hit — Key Capability 2's "store-first (a symbol×timeframe already frozen in
+    the store is reused, never re-fetched)" is unreachable on the real path, and J-02's "a second run
+    reports all-reused" holds only for two runs inside one UTC day. Cost, measured against the store's
+    own files: for the **235** pairs the store ALREADY held before that run, the run downloaded
+    **276,714** bars and gained **13,533** new ones (**4.9 %**); for **174** of those 235 the entire
+    download yielded **≤ 5** new bars (91,226 downloaded, 348 new), median 4. AAPL `1d` is the clean
+    case — a 500-bar 730-day series re-downloaded to add exactly **one** bar to the 501 already frozen;
+    MSFT `1d` is the counter-case the full window must keep serving, gaining 112. Steady state today:
+    **390 of the 404** member × timeframe pairs already hold bars reaching past the lookback start,
+    **5** hold shorter histories (HONA ×4, MSFT `1h`) and **9** hold nothing (8 × `1h` + NOW `1d`), so
+    the next daily run under today's rule re-downloads on the order of the 462,535 bars / 68.5 MB that
+    run recorded across 390 series to gain a day. The whole store is 759 series files / 220 MB /
+    1,766,542 recorded rows, of which 301,271 (17.1 %) are timestamps another series for the same pair
+    already holds. And the wrinkle a tail window creates is already visible in the code: an
+    already-registered answer raises the store's 409 (`routes.py:681`), which `_run_one_pair` records
+    as `failed` — so without the `unchanged` outcome a weekend run would print a wall of false
+    failures.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-desk-index.html               |  13 +-
 runs/goal-session-desk/.engine.lock/epoch          |   2 +-
 runs/goal-session-desk/.engine.lock/pid            |   2 +-
 runs/goal-session-desk/dispatch/.pump-alive        |   4 +-
 runs/goal-session-desk/engine.pid                  |   2 +-
 runs/goal-session-desk/journey-scripts/J-05.json   |   7 +-
 runs/goal-session-desk/session.json                |   6 +-
 runs/goal-session-desk/state/assumptions.md        | 187 ++++-----------------
 .../state/assumptions.md.archive.md                | 157 +++++++++++++++++
 runs/goal-session-desk/state/blueprint.md          |  45 ++++-
 .../state/enhancement-proposals.jsonl              |   2 +
 runs/goal-session-desk/state/lessons.md            |  29 +---
 runs/goal-session-desk/state/lessons.md.archive.md |  36 ++++
 runs/goal-session-desk/state/proposer-result.json  |   8 +-
 runs/goal-session-desk/summary.md                  | 103 ++++++++----
 runs/goal-session-desk/telemetry.jsonl             |  75 +++++++++
 runs/goal-session-desk/trace/trace.jsonl           |   8 +
 17 files changed, 449 insertions(+), 237 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
