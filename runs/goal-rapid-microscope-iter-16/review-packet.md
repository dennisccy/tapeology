# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/micro_observer.py b/apps/backend/app/research/micro_observer.py
index 55930f4..8fbae5a 100644
--- a/apps/backend/app/research/micro_observer.py
+++ b/apps/backend/app/research/micro_observer.py
@@ -637,6 +637,13 @@ class MicroObserver:
         run = self._depletion_run[side]
         if run is None or run["price"] != price:
             if run is not None:
+                # r6 (spec section 3): a price-change termination is REVEALED by the price-CHANGING
+                # quote itself, not by the run's own last same-price update -- "measurement end !=
+                # knowledge time". The depletion MAGNITUDE stays computed from the pre-change run's
+                # own start_size/current_size (untouched below); only the availability stamp moves
+                # to THIS quote's own instant `ts`, the point at which the observer actually learns
+                # the run has ended (was: the run's own stale `observed_through`, one quote early).
+                run["observed_through"] = ts
                 self._resolve_depletion(side, run)
             self._depletion_run[side] = {
                 "run_start_ts": ts,
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 1d5d21b..ba02cc5 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -586,6 +586,29 @@ def test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmet
     assert _PRICE_ARITHMETIC_PATTERN.search("const label = `${basis.n_records} records`;") is None
 
 
+def test_desk_page_price_arithmetic_guard_catches_sealed_tranche_and_universe_counts_and_withheld_excluded_arithmetic():
+    """goal-rapid-microscope-iter-16 (J-10) TC-15 counter-test: the iteration-15-added
+    ``readiness.sealed_tranche.*``/``universeCounts.*``/``readiness.joinable_corpus.
+    withheld_excluded`` clauses (module docstring above, "iter-15" note) catch arithmetic on their
+    own served numerics -- closing iteration 15's own open MINOR finding that these two clauses had
+    never been proven capable of failing."""
+    seeded_ratio = (
+        "const ratio = readiness.sealed_tranche.shard_count / readiness.sealed_tranche.symbol_days;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_ratio) is not None
+
+    seeded_total = "const total = universeCounts.shard_count + universeCounts.symbol_days;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_total) is not None
+
+    seeded_included = "const included = 1 - readiness.joinable_corpus.withheld_excluded;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_included) is not None
+
+    # And the pattern does NOT over-match: a non-arithmetic render of the same fields is clean.
+    assert _PRICE_ARITHMETIC_PATTERN.search(
+        "const label = `${readiness.sealed_tranche.shard_count} shards`;"
+    ) is None
+
+
 def test_desk_page_price_arithmetic_guard_catches_referee_shortlist_and_discovery_field_arithmetic():
     """goal-referee-iter-8 (J-07) counter-test: the extended guard catches arithmetic on the new
     Referee Registry section's own `candidate.*` (shortlist readiness) and `hyp.discovery.*`
diff --git a/apps/backend/tests/test_micro_accessor.py b/apps/backend/tests/test_micro_accessor.py
index 93376ad..4fd7f82 100644
--- a/apps/backend/tests/test_micro_accessor.py
+++ b/apps/backend/tests/test_micro_accessor.py
@@ -103,6 +103,62 @@ def test_tc1_a_dataset_id_that_does_not_exist_raises_dataset_not_found_never_swa
         accessor.read_snapshot_rows("does-not-exist")
 
 
+# === TR-3: the accessor origin-fence -- explicitly-labeled trap-suite entry (spec section 9) ========
+# goal-rapid-microscope-iter-16 (J-10): TR-3 requires three proven clauses. (a) The single-read
+# origin fence is proven by the TC-1 tests directly above -- test_tc1_a_read_at_or_before_origin_
+# succeeds / test_tc1_a_read_strictly_after_origin_raises_a_typed_error_never_empty / test_tc1_
+# origin_equal_to_the_dataset_session_date_is_visible_the_fence_is_inclusive -- folded in
+# unchanged, never re-derived. (b) The multi-session AGGREGATE-boundary proof lives in
+# test_walkforward.py (test_tr3_an_origin_fenced_loop_over_several_sessions_returns_exactly_the_
+# set_le_origin) -- see that file's own TR-3 note for why: direct code inspection found no
+# production call site actually constructs MicroAccessor(origin=...) today (both micro_join.py/
+# scout.py pass origin=None; walkforward.py's build_folds never touches the accessor), so this is
+# a NEW test, not a pointer to existing code, and production edits to micro_accessor.py/
+# walkforward.py are out of scope this round. (c) The import-ban is proven by the TC-3 section
+# below -- test_tc3_no_module_other_than_micro_accessor_imports_read_snapshot_rows / test_tc3_the_
+# guard_also_catches_a_module_qualified_call_that_imports_no_banned_name / test_tc3_micro_join_
+# and_scout_no_longer_import_read_snapshot_rows_directly / test_tc3_import_ban_guard_can_fail_on_a_
+# seeded_violation (its own non-vacuity proof, already existing) -- folded in unchanged. The test
+# immediately below is the ORIGIN-FENCE clause's own non-vacuity mutation-proof (this round's
+# binding rule -- iteration 15's own opaque-pool regression test was proven structurally unable to
+# fail; every new trap this round must prove the opposite). Deliberately unnumbered (no bare
+# "tcN" prefix): this file's own TC-2/TC-3/TC-4 already name OTHER, unrelated concepts (sealed-
+# shard invisibility; the micro_join/scout re-point) under this era's historical per-file
+# numbering, so this round's new tests carry only the globally-unambiguous "tr3"/"tr22"/"tr26"
+# spec-trap tags, never a reused bare TC number.
+
+
+def test_tr3_weakening_the_origin_fence_comparison_makes_the_guarding_assertion_fail_restoring_it_passes(
+    rig, monkeypatch
+):
+    """Deliberately defeat the origin-fence comparison (monkeypatch the session-date resolver so
+    EVERY dataset reports a date at/before any origin -- the exact effect of a comparison that never
+    refuses) and show the read TC-1 requires to be REFUSED instead silently SUCCEEDS, leaking the
+    strictly-after-origin dataset's rows; restore (``monkeypatch.undo()``) and show the refusal
+    fires again, byte-identically to the shipped fence."""
+    dataset_store, snapshots_dir = rig
+    after = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="LEAK",
+        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
+    )
+    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
+
+    # Sanity: the shipped fence genuinely refuses this read before any mutation.
+    with pytest.raises(ma.MicroAccessorOriginFenceError):
+        accessor.read_snapshot_rows(after["id"])
+
+    # Weaken: defeat the comparison by making the session-date resolver always report a date
+    # at/before the origin -- the exact effect of the defect TR-3 exists to catch.
+    monkeypatch.setattr(ma, "_session_date_for_dataset", lambda dataset_meta: "2000-01-01")
+    leaked_rows = accessor.read_snapshot_rows(after["id"])  # would raise if the fence still worked
+    assert leaked_rows, "the weakened fence leaked the strictly-after-origin dataset's rows"
+
+    # Restore: undo the monkeypatch and prove the fence refuses again, byte-identically.
+    monkeypatch.undo()
+    with pytest.raises(ma.MicroAccessorOriginFenceError):
+        accessor.read_snapshot_rows(after["id"])
+
+
 # === TC-2: sealed-shard invisibility =================================================================
 
 
diff --git a/apps/backend/tests/test_micro_observer.py b/apps/backend/tests/test_micro_observer.py
index 89996e2..8277e6a 100644
--- a/apps/backend/tests/test_micro_observer.py
+++ b/apps/backend/tests/test_micro_observer.py
@@ -284,13 +284,22 @@ def _one_ask_depletion(rows: list[dict]) -> dict:
 
 def test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_the_next_trade_row():
     """The VERIFIED-unit half of the contract: the run's own timing facts, and -- because
-    ``quote_size_unit`` is verified -- the share-denominated magnitude itself, served."""
+    ``quote_size_unit`` is verified -- the share-denominated magnitude itself, served.
+
+    goal-rapid-microscope-iter-16 (TR-26, r6 owner ruling 2026-08-18): ``observed_through``/
+    ``available_at`` corrected from the pre-fix ``2.0`` (the LAST same-price quote -- measurement
+    end) to ``3.0`` (the price-CHANGING/REVEALING quote's own instant -- knowledge time). This is
+    the specified behaviour fix itself, not a regression: the spec's own words are "measurement end
+    != knowledge time" (section 3) -- the observer does not actually LEARN the run has ended until
+    it sees the price-changing quote, so THAT instant is when the completion becomes available, even
+    though the run's magnitude (500 - 300 = 200, unaffected) is still measured only over the
+    same-price quotes that preceded it."""
     rows = _non_close_out(_run(_depletion_events(), quote_size_unit="shares"))
     d = _one_ask_depletion(rows)
     assert d["anchor_at"] == 0.0  # the run's own start
-    assert d["observed_through"] == 2.0  # the LAST update still at the old price
-    assert d["available_at"] == 2.0
-    assert d["value"] == pytest.approx(200.0)  # 500 - 300
+    assert d["observed_through"] == 3.0  # the REVEALING price-changing quote (r6) -- was 2.0 pre-fix
+    assert d["available_at"] == 3.0
+    assert d["value"] == pytest.approx(200.0)  # 500 - 300, unaffected by the timestamp fix
     assert d["unavailable"] is False
     assert d["refused"] is False
     assert d["refusal_reason"] is None
@@ -310,8 +319,11 @@ def test_tc7_tr18_quote_depletion_magnitude_is_refused_under_an_unverified_unit(
     assert d["unavailable"] is False  # observed to completion -- refused, not missing
     # the unit-invariant facts are unaffected by the refusal
     assert d["anchor_at"] == 0.0
-    assert d["observed_through"] == 2.0
-    assert d["available_at"] == 2.0
+    # goal-rapid-microscope-iter-16 (TR-26): the same timing fix as TC-10 above -- the revealing
+    # quote's own instant (3.0), not the last same-price quote (was 2.0 pre-fix). The unit gate
+    # only ever governs `value`/`refused`/`refusal_reason`; it does not touch this timestamp.
+    assert d["observed_through"] == 3.0
+    assert d["available_at"] == 3.0
     assert d["price"] == pytest.approx(100.10)
     assert d["updates_observed"] == 2
 
@@ -411,6 +423,122 @@ def test_quote_depletion_that_genuinely_closes_is_still_a_completed_observation(
     assert d["value"] == pytest.approx(200.0)
 
 
+# === TR-26: quote_depletion's revealing-quote availability (r6, spec section 3) =====================
+# goal-rapid-microscope-iter-16 (J-10): a genuine production bug, fixed here. `_advance_depletion_
+# run`'s price-change-termination branch used to resolve using the OLD run's own last-recorded
+# `observed_through` (the last same-price quote) -- the r6 owner ruling (docs/rapid-validation-
+# spec.md revision header, 2026-08-18) requires the REVEALING price-CHANGING quote's own instant
+# instead ("measurement end != knowledge time"). TC-9 above is the corrected assertion (the fix
+# itself); TC-10 below proves the OTHER termination path (hitting DEPLETION_WINDOW_QUOTES) was
+# already correct and stays that way; TC-11 proves the fix is prefix-honest (TR-1-style) at the
+# exact revealing instant; TC-12 is this trap's own non-vacuity mutation-proof.
+
+
+def _bound_terminated_depletion_events() -> list:
+    """A depletion run that terminates by hitting ``DEPLETION_WINDOW_QUOTES`` (20 same-side,
+    same-price updates) -- NEVER a price change -- the OTHER termination path (spec section 1's own
+    table), already correct before this iteration's fix (the bound-termination branch already
+    stamps ``run["observed_through"] = ts`` on every same-price update, the 20th included, before
+    checking the bound) and untouched by it; this fixture is this iteration's first DEDICATED test
+    of that path."""
+    events = [QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500)]  # run starts: price 100.10, size 500
+    size = 500
+    for i in range(1, mf.DEPLETION_WINDOW_QUOTES + 1):
+        size -= 1  # any same-price update advances the run; the exact size path is not asserted
+        events.append(QuoteEvent(TICKER, float(i), 100.00, 100.10, 500, size))
+    events.append(TradeEvent(TICKER, float(mf.DEPLETION_WINDOW_QUOTES) + 1.0, 100.10, 10, Side.UNKNOWN))
+    return events
+
+
+def test_tc10_bound_terminated_depletion_resolves_at_the_bound_hitting_quotes_own_instant():
+    events = _bound_terminated_depletion_events()
+    rows = _non_close_out(_run(events, quote_size_unit="shares"))
+    d = _one_ask_depletion(rows)
+    assert d["unavailable"] is False
+    assert d["available_at"] == d["observed_through"] == float(mf.DEPLETION_WINDOW_QUOTES)
+    assert d["updates_observed"] == mf.DEPLETION_WINDOW_QUOTES
+
+
+def test_tc11_truncating_strictly_before_the_revealing_quote_leaves_the_run_unresolved():
+    """Truncate the stream strictly BEFORE the price-changing/revealing quote's own instant
+    (``ts=3.0`` in ``_depletion_events()``) -- the run's only termination trigger never arrives, so
+    it must surface as ``unavailable`` (counted, never guessed), exactly like any other deferred
+    construct the session cuts short -- never a value computed as if the window had closed."""
+    events = _depletion_events()
+    truncated = [e for e in events if e.timestamp < 3.0]  # strictly before the revealer
+    rows = _run(truncated, quote_size_unit="shares")
+    depletions = [
+        d for row in rows for d in row["deferred"] if d["kind"] == "quote_depletion" and d["side"] == "ask"
+    ]
+    assert len(depletions) == 1
+    d = depletions[0]
+    assert d["unavailable"] is True
+    assert d["value"] is None
+    assert d["available_at"] == d["observed_through"] == 2.0  # the last event genuinely seen
+
+
+def test_tc11_truncating_at_the_revealing_quote_resolves_the_run_deterministically():
+    """The counter-test: INCLUDING the revealing quote's own instant resolves the run immediately --
+    deterministically, matching the full replay's own value -- even with no trade afterward to carry
+    the completion; the close-out row (``finalize()``) attaches it, proving the resolution does not
+    depend on a LATER trade ever occurring."""
+    events = _depletion_events()
+    truncated = [e for e in events if e.timestamp <= 3.0]  # at/after -> inclusive of the revealer
+    rows = _run(truncated, quote_size_unit="shares")
+    depletions = [
+        d
+        for row in rows
+        for d in row["deferred"]
+        if d["kind"] == "quote_depletion" and d["side"] == "ask" and d["anchor_at"] == 0.0
+    ]
+    assert len(depletions) == 1
+    d = depletions[0]
+    assert d["unavailable"] is False
+    assert d["value"] == pytest.approx(200.0)
+    assert d["available_at"] == d["observed_through"] == 3.0  # the revealing quote itself
+
+
+def test_tc12_tr26_reverting_the_fix_makes_the_corrected_assertion_fail_restoring_it_passes(monkeypatch):
+    """Non-vacuity, this round's binding rule (iteration 15's own opaque-pool regression test was
+    proven structurally unable to fail -- every new trap this round must prove the opposite):
+    monkeypatch in the EXACT pre-fix ``_advance_depletion_run`` (stamps the OLD run's own already-
+    stale ``observed_through`` instead of threading the revealing quote's own ``ts`` through) and
+    show the corrected TC-9 assertion (``observed_through == 3.0``) would FAIL against it --
+    reproducing the exact pre-fix wrong value, ``2.0`` -- then restore (``monkeypatch.undo()``) and
+    show it passes again, byte-identically to the shipped fix."""
+    import app.research.micro_observer as mo
+
+    def _pre_fix_advance_depletion_run(self, side, price, size, ts):
+        run = self._depletion_run[side]
+        if run is None or run["price"] != price:
+            if run is not None:
+                self._resolve_depletion(side, run)  # BUG: stamps the OLD run's own stale observed_through
+            self._depletion_run[side] = {
+                "run_start_ts": ts, "price": price, "start_size": size, "current_size": size,
+                "updates_seen": 0, "observed_through": ts,
+            }
+            return
+        run["current_size"] = size
+        run["updates_seen"] += 1
+        run["observed_through"] = ts
+        if run["updates_seen"] >= mf.DEPLETION_WINDOW_QUOTES:
+            self._resolve_depletion(side, run)
+            self._depletion_run[side] = None
+
+    monkeypatch.setattr(mo.MicroObserver, "_advance_depletion_run", _pre_fix_advance_depletion_run)
+    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="shares"))
+    d = _one_ask_depletion(rows)
+    # The exact leaked/incorrect value the pre-fix code produces -- proving the corrected assertion
+    # (observed_through == 3.0) WOULD fail against this reverted code.
+    assert d["observed_through"] == 2.0
+    assert d["observed_through"] != 3.0
+
+    monkeypatch.undo()
+    rows_restored = _non_close_out(_run(_depletion_events(), quote_size_unit="shares"))
+    d_restored = _one_ask_depletion(rows_restored)
+    assert d_restored["observed_through"] == 3.0
+
+
 def test_refill_consistent_only_registers_on_a_confirmed_quote_rule_execution():
     # A tick-test-decided trade never confirms it executed AGAINST the displayed quote -- no refill
     # check should register for it (module docstring's own gating rule).
diff --git a/apps/backend/tests/test_walkforward.py b/apps/backend/tests/test_walkforward.py
index 07416c8..fafec23 100644
--- a/apps/backend/tests/test_walkforward.py
+++ b/apps/backend/tests/test_walkforward.py
@@ -3,13 +3,20 @@
 chronological walk-forward engine. Test-first contract: TC-6 through TC-19, TC-23 through TC-26 in
 ``docs/phases/goal-rapid-microscope-iter-5.md`` (TC-21/TC-22, the TR-16 end-to-end oracles, live in
 ``test_walkforward_oracles.py`` -- see that file's own module docstring). TC-1/TC-2/TC-3 live in
-``test_micro_accessor.py``; TC-4/TC-5 in ``test_micro_join.py``/``test_scout.py``."""
+``test_micro_accessor.py``; TC-4/TC-5 in ``test_micro_join.py``/``test_scout.py``.
+
+goal-rapid-microscope-iter-16 (J-10): two explicitly-labeled trap-suite entries added, both
+test-file-only (no production edit to this module or ``micro_accessor.py``) -- TR-3's own
+multi-session aggregate-boundary proof (a NEW test; see its own section header below for why) and
+TR-22's own non-vacuity mutation-proof (the existing ``test_tc13_*``/``test_tc14_*`` tests already
+prove both classification directions and the r2 initialization; see that section's own header)."""
 
 from __future__ import annotations
 
 import pytest
 from fastapi.testclient import TestClient
 
+from app.config import CONFIG
 from app.main import app
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import walkforward as wf
@@ -19,6 +26,8 @@ from app.research.datasets import DatasetStore
 from app.research.micro_accessor import (
     R2_REVISION_INSTANT,
     ExposureRegistry,
+    MicroAccessor,
+    MicroAccessorOriginFenceError,
     has_any_exposure_entries,
     initialize_r2_exposure_registry,
 )
@@ -28,8 +37,10 @@ from app.research.micro_routes import (
     get_walkforward_compute_manager,
     get_walkforward_ledger_dir,
 )
+from app.research.micro_snapshots import resolve_micro_snapshots_dir
 from app.research.desk_routes import get_playbook_store, get_universe_store
 from app.research.routes import get_bar_store
+from tests.test_micro_accessor import _plant_dataset_and_snapshot
 
 
 # === helpers ==========================================================================================
@@ -60,6 +71,55 @@ def _five_sufficient_oos_rule_process_folds(**overrides) -> list[dict]:
     return [_sufficient_fold_row(fold_index=i, **overrides) for i in range(5)]
 
 
+# === TR-3: the accessor origin-fence -- the aggregate-boundary clause (spec section 9(b)) ===========
+# goal-rapid-microscope-iter-16 (J-10): TC-1 (single-read fence) and the import-ban live in
+# test_micro_accessor.py (that file's own TR-3 header names every clause and test). This is TR-3's
+# OWN multi-session AGGREGATE proof, placed HERE rather than there per this round's own scope note
+# (runs/goal-rapid-microscope-iter-16/plan.md): direct code inspection found no production call
+# site that actually constructs MicroAccessor(origin=...) today -- both micro_join.py and scout.py
+# pass origin=None (the disclosed unfenced mode), and this file's own build_folds is a pure
+# function over session-date strings that never touches the accessor -- so the spec's TC-2
+# framing ("the walk-forward origin-window path, its one existing origin= consumer") describes no
+# real call site to re-point; this is a NEW TEST proving the accessor's own aggregate behaviour
+# directly. No production edit to micro_accessor.py or walkforward.py; no new helper -- reuses
+# test_micro_accessor.py's own _plant_dataset_and_snapshot verbatim (imported, never re-derived).
+
+
+def test_tr3_an_origin_fenced_loop_over_several_sessions_returns_exactly_the_set_le_origin(tmp_path):
+    """Sessions S1=2026-06-08 < T=S2=2026-06-09 < S3=2026-06-10. At origin=T, the accepted set is
+    exactly {S1, S2} (S3 refused); at origin=T+1=S3, exactly {S1, S2, S3} (nothing refused) --
+    boundary-exact BOTH directions (the iter-11 lesson: never prove only the refusal side)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    snapshots_dir = resolve_micro_snapshots_dir(str(tmp_path / "datasets"))
+    s1 = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="S1",
+        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
+    )
+    s2 = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="S2",
+        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
+    )
+    s3 = _plant_dataset_and_snapshot(
+        dataset_store, snapshots_dir, symbol="S3",
+        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
+    )
+    datasets = {"S1": s1, "S2": s2, "S3": s3}
+
+    def _accepted_set(origin: str) -> set[str]:
+        accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=origin)
+        accepted: set[str] = set()
+        for label, meta in datasets.items():
+            try:
+                accessor.read_snapshot_rows(meta["id"])
+            except MicroAccessorOriginFenceError:
+                continue
+            accepted.add(label)
+        return accepted
+
+    assert _accepted_set("2026-06-09") == {"S1", "S2"}        # origin = T = S2
+    assert _accepted_set("2026-06-10") == {"S1", "S2", "S3"}  # origin = T+1 = S3, nothing refused
+
+
 # === TC-6: fold-spec registration is frozen verbatim; clustering_unit is corpus-size-invariant ======
 
 
@@ -318,6 +378,58 @@ def test_tc14_freshly_initialized_registry_reads_every_named_window_exposed_befo
         assert registry.is_exposed_before(corpus_id="legacy_tick", window=window, instant="2026-08-17T00:00:00.000000Z")
 
 
+# === TR-22: the exposure-registry auto-classification -- explicitly-labeled trap-suite entry ========
+# goal-rapid-microscope-iter-16 (J-10): TR-22 requires three proven clauses -- (a) registered-after-
+# exposure auto-classes historical_exposed_diagnostic, proven above by test_tc13_a_mode_b_spec_
+# registered_after_a_logged_exposure_is_auto_classed_diagnostic; (b) registered-before-any-exposure
+# classes historical_oos, proven above by test_tc13_a_mode_b_spec_registered_before_any_exposure_
+# of_its_window_classes_historical_oos (both directions of the SAME mechanical rule, the iter-11
+# lesson: never prove only one side) -- folded in unchanged, never re-derived; (c) the r2
+# initialization pre-marks every playbook-corpus/legacy-tick window exposed, proven above by
+# test_tc14_freshly_initialized_registry_reads_every_named_window_exposed_before_any_serving_act
+# (this file) and test_tc14_r2_initialization_pre_marks_every_named_window_exposed_before_any_
+# serving_act (test_micro_accessor.py) -- folded in unchanged. The test immediately below is this
+# clause's own non-vacuity mutation-proof (this round's binding rule): a comparison that silently
+# stops detecting prior exposure would let genuinely-exposed/diagnostic-quality evidence
+# auto-classify as fake historical_oos -- the exact class-mixing anti-goal this trap exists to
+# prevent -- so the proof targets `is_exposed_before` directly, never through `evaluate_mode_b_
+# fold`'s own ledger (append_fold_result is idempotent on (sequence_id, fold_index, spec_hash) --
+# calling it twice with the SAME spec/fold would silently replay the FIRST cached row rather than
+# re-run the classification, making a naive non-vacuity test through that path itself vacuous;
+# discovered while writing this test, noted here so a later lane does not repeat the mistake).
+
+
+def test_tr22_mutating_is_exposed_before_to_always_return_false_makes_the_auto_classification_assertion_fail_restoring_it_passes(
+    tmp_path, monkeypatch
+):
+    registry = ExposureRegistry(str(tmp_path / "exposure"))
+    corpus_id = "tr22-non-vacuity-corpus"
+    registry.log_exposure(
+        corpus_id=corpus_id, window="2026-04-05", surface="prior-serving",
+        logged_at="2026-04-06T00:00:00.000000Z",
+    )
+
+    # Weaken: is_exposed_before's strict `<` comparison, mutated to always report "never exposed".
+    monkeypatch.setattr(ExposureRegistry, "is_exposed_before", lambda self, **kwargs: False)
+    leaked = wf.classify_evidence_class(
+        registry, corpus_id=corpus_id, window_sessions=["2026-04-05"],
+        registered_at="2026-04-10T00:00:00.000000Z",  # AFTER the logged exposure entry
+    )
+    # The exact leaked/incorrect value the mutated comparison produces -- proving the guarding
+    # assertion (evidence_class == historical_exposed_diagnostic) WOULD fail against it: genuinely
+    # exposed evidence silently promoted to a fake historical_oos.
+    assert leaked == wf.EVIDENCE_CLASS_HISTORICAL_OOS
+    assert leaked != wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
+
+    # Restore: undo the monkeypatch and prove the correct classification fires again.
+    monkeypatch.undo()
+    restored = wf.classify_evidence_class(
+        registry, corpus_id=corpus_id, window_sessions=["2026-04-05"],
+        registered_at="2026-04-10T00:00:00.000000Z",
+    )
+    assert restored == wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
+
+
 # === TC-15: WF_SURVIVOR_RULE_V1 -- all five conditions, individually violated =========================
 
 
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index a708654..7e077ef 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -5889,14 +5889,20 @@ function MicroReadinessSection({
   readinessResult: { ok: boolean; data: MicroReadinessResponse | null; error?: string } | null;
 }) {
   if (readinessResult === null) {
-    return <LoadingPanel testid="micro-readiness-loading" />;
+    return (
+      <div data-testid="micro-readiness-section">
+        <LoadingPanel testid="micro-readiness-loading" />
+      </div>
+    );
   }
   if (!readinessResult.ok || readinessResult.data === null) {
     return (
-      <UnavailablePanel
-        testid="micro-readiness-unavailable"
-        message={readinessResult.error ?? "The microscope readiness corpus could not be loaded."}
-      />
+      <div data-testid="micro-readiness-section">
+        <UnavailablePanel
+          testid="micro-readiness-unavailable"
+          message={readinessResult.error ?? "The microscope readiness corpus could not be loaded."}
+        />
+      </div>
     );
   }
   const readiness = readinessResult.data;
@@ -6312,9 +6318,9 @@ function ScoutLedgerSection({
                             {trial.candidate_id}
                           </td>
                           <td className="px-1.5 py-1 text-slate-300">
-                            {trial.feature.name} / {trial.feature.transform}
+                            {trial.feature?.name ?? "—"} / {trial.feature?.transform ?? "—"}
                           </td>
-                          <td className="px-1.5 py-1 text-slate-400">{trial.outcome.horizon_key}</td>
+                          <td className="px-1.5 py-1 text-slate-400">{trial.outcome?.horizon_key ?? "—"}</td>
                           <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
                             {formatDateTimeET(trial.registered_at, { seconds: false })}
                           </td>
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
