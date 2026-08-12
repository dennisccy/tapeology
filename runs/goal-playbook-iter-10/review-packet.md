# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/research/desk_playbook_detect.py b/apps/backend/app/research/desk_playbook_detect.py
index dc17c0c..ded93c3 100644
--- a/apps/backend/app/research/desk_playbook_detect.py
+++ b/apps/backend/app/research/desk_playbook_detect.py
@@ -1188,6 +1188,18 @@ def _range_trade_side(
             any(bar.high >= midrange for bar in between) if side == "long"
             else any(bar.low <= midrange for bar in between)
         )
+        # `turned_at_midrange` (spec §3.7 Disclosures, R-3.2(b) -- disclosure only, reuses `hold_tol`
+        # already computed above, no new constant): the SAME approach window's own extreme -- the
+        # furthest point price reached before returning to complete the arming touch `b` -- lies
+        # within `PLAYBOOK_RANGE_HOLD_TOL_MBR * MBR` of the midpoint. Long reads the window's own
+        # highest high (the swing up off the low zone's first touch, before it turned back down to
+        # re-touch); short mirrors on the window's own lowest low. Never gates, suppresses, or
+        # creates a signal -- a served fact about where the prior swing turned, nothing else.
+        swing_extreme = (
+            max(bar.high for bar in between) if side == "long"
+            else min(bar.low for bar in between)
+        )
+        turned_at_midrange = abs(swing_extreme - midrange) <= hold_tol
         # `absorption_bar_present` (spec §3.7): a zone TOUCH bar with RVOL >= RVOL_ELEVATED and its
         # own range <= RANGE_HOLD_TOL*MBR (P6 passive accumulation/distribution).
         absorption_bar_present = False
@@ -1244,6 +1256,7 @@ def _range_trade_side(
                 "low_zone_touches": len(low_touches),
                 "high_zone_touches": len(high_touches),
                 "crossed_midrange": crossed_midrange,
+                "turned_at_midrange": turned_at_midrange,
                 "absorption_bar_present": absorption_bar_present,
             },
             "volume": {
diff --git a/apps/backend/scripts/seed_playbook_iter8_replay_rig.py b/apps/backend/scripts/seed_playbook_iter8_replay_rig.py
index 7d9407f..73f421f 100644
--- a/apps/backend/scripts/seed_playbook_iter8_replay_rig.py
+++ b/apps/backend/scripts/seed_playbook_iter8_replay_rig.py
@@ -73,11 +73,14 @@ import seed_playbook_iter8_evidence_fixture as iter8_seed  # noqa: E402
 
 from app.config import Config  # noqa: E402
 from app.providers.adapters.base import RawBar  # noqa: E402
+from app.research.bar_index import BarIndex  # noqa: E402
 from app.research.bars import BarStore  # noqa: E402
+from app.research.desk_index_reconcile import run_reconcile  # noqa: E402
 from app.research.desk_playbook import PlaybookStore, resolve_desk_playbook_dir  # noqa: E402
 from app.research.desk_playbook_backscan import _assert_scoped  # noqa: E402
 from app.research.desk_playbook_compute import run_playbook_and_record  # noqa: E402
 from app.research.desk_universe import UniverseStore  # noqa: E402
+from app.research.routes import get_bar_index  # noqa: E402
 
 # The detector showcase date: a Friday, OUTSIDE J-07's [2026-06-22, 2026-06-24] back-scan window and
 # outside the evidence date (2026-06-25), and already the date J-02's stored golden types in.
@@ -238,6 +241,27 @@ def _copy_kept_symbol_series(scoped_bar_dir: Path, real_bar_dir: Path) -> int:
     return copied
 
 
+def _reindex_copied_series(bar_store: BarStore, bar_index: BarIndex) -> dict:
+    """goal-playbook-iter-10: repair the scoped rig's own ``bar_index.db`` after
+    ``_copy_kept_symbol_series`` -- through the SOLE repair path (``desk_index_reconcile.
+    run_reconcile``, never a second one), never mutating bar content.
+
+    Root cause this closes (the iter-9 blank-``/structure``-chart evidence gap): a raw
+    ``shutil.copy2`` never updates the index, and ``GET /research/bars?symbol=...`` -- what
+    ``/structure``'s chart fetches -- resolves a ``symbol=`` filter through ``BarIndex.list()``
+    (``app/research/routes.py``), so an unindexed copy stayed invisible to that filtered read even
+    though the levels/tradability table (a separate cache path) already showed real numbers, which
+    is why the gap was missed before."""
+    result = run_reconcile(bar_store, bar_index)
+    print(
+        f"[seed-playbook-iter8-replay] reconciled bar_index.db: "
+        f"{result['rows_indexed_before']} -> {result['rows_indexed_after']} rows indexed "
+        f"({result['series_on_disk']} series on disk)",
+        file=sys.stderr,
+    )
+    return result
+
+
 def main(root: Path) -> int:
     # Reuse the iter-8 evidence rig VERBATIM first (which reuses iter-7, which reuses iter-6):
     # DECOR/RTAAA/DTAAA on 2026-06-22, BSCAN on 2026-06-23/24 (unrecorded), OHB01..OHB12 on
@@ -279,8 +303,13 @@ def main(root: Path) -> int:
         )
         print(f"[seed-playbook-iter8-replay] planted {symbol}: {len(bars)} 5m bars", file=sys.stderr)
 
-    # 3. Kept-product bars for J-10's /structure step (verbatim copies, real store read-only).
-    _copy_kept_symbol_series(Path(bar_dir), Path(config.bar_dir))
+    # 3. Kept-product bars for J-10's /structure step (verbatim copies, real store read-only), then
+    #    indexed via the SOLE repair path (goal-playbook-iter-10) -- a raw copy alone never updated
+    #    bar_index.db, so GET /research/bars?symbol=... (what /structure's chart fetches) resolved
+    #    through BarIndex.list() and saw nothing even though the file was physically present.
+    copied = _copy_kept_symbol_series(Path(bar_dir), Path(config.bar_dir))
+    if copied:
+        _reindex_copied_series(bar_store, get_bar_index())
 
     # 4. ONE new snapshot naming every member, then the two computes it re-keys.
     members = [
diff --git a/apps/backend/tests/test_desk_playbook.py b/apps/backend/tests/test_desk_playbook.py
index c56192a..41c117a 100644
--- a/apps/backend/tests/test_desk_playbook.py
+++ b/apps/backend/tests/test_desk_playbook.py
@@ -323,6 +323,33 @@ def test_monkeypatched_constant_moves_parameters_and_signature_and_mints_a_new_v
     # The original file is untouched by the second, differently-keyed write.
     assert store.get(first_meta["id"]) == first_meta
 
+    monkeypatch.undo()  # back to PLAYBOOK_NARROW_OR_MAX_MBR's real value
+
+    # goal-playbook-iter-10 (TC-9): the SAME proof, for the constant THIS iteration's new
+    # `geometry.turned_at_midrange` disclosure reuses (`PLAYBOOK_RANGE_HOLD_TOL_MBR`, spec §3.7,
+    # R-3.2(b)) -- proving the field's own binding constraint (reuse an existing constant, never
+    # mint one) is honestly wired into the signature, not merely asserted in a docstring.
+    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_RANGE_HOLD_TOL_MBR", 5.0)
+    hold_tol_moved_params = playbook_parameters()
+    hold_tol_moved_signature = compute_playbook_input_signature(
+        bar_store, ["AAA"], CONFIG.config_fingerprint()
+    )
+    assert hold_tol_moved_params != original_params
+    assert hold_tol_moved_params["range_hold_tol_mbr"] == 5.0
+    assert hold_tol_moved_signature != original_signature
+    monkeypatch.undo()
+
+    # And the reverse (TC-9's second half): with EVERY constant back to its real value -- this
+    # iteration's own new code (the turned_at_midrange disclosure) changed no constant -- both
+    # `playbook_parameters()` and the signature reproduce the EXACT pre-monkeypatch value on the
+    # same bar/member inputs, byte for byte, and the fingerprint pin is unmoved. A disclosure is
+    # not a threshold (T-1).
+    reverted_params = playbook_parameters()
+    reverted_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())
+    assert reverted_params == original_params
+    assert reverted_signature == original_signature
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
+
 
 def test_compute_playbook_input_signature_is_deterministic(bar_store):
     _plant_baseline_sessions(bar_store, "AAA")
@@ -1263,6 +1290,48 @@ def test_range_trade_wired_into_compute_playbook_is_measured_like_every_other_se
     assert result["baseline_anchors"]["range_trade:long"]
 
 
+def test_a_pre_iteration_10_style_range_trade_record_serves_geometry_without_the_new_key(
+    tmp_path, bar_store, monkeypatch,
+):
+    """TC-8 (goal-playbook-iter-10): `geometry.turned_at_midrange` is optional and NEVER
+    backfilled -- `PlaybookStore`'s append-only discipline means a record's on-disk shape is
+    exactly what was written, never reshaped on read. Simulated the way this file already
+    simulates a pre-J-06 record (strip what the newer code adds, write the result back under the
+    CURRENT signature-computing code, confirm the served geometry still lacks the key -- absent,
+    never `null` -- and the read is still HTTP 200). The sanity check below proves this
+    iteration's OWN code does add the key on a fresh compute, so the absence on the
+    "pre-iteration-10" copy is provably the store's own fidelity, not a detector that silently
+    never wrote the field."""
+    universe_store = _register_universe(tmp_path, ["RTAAA"])
+    _plant_decoration_baseline_sessions(bar_store, "RTAAA", slots=10)
+    _plant_range_trade_session(bar_store, "RTAAA")
+
+    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    rt_signals = [s for s in result["signals"] if s["symbol"] == "RTAAA" and s["setup_id"] == "range_trade"]
+    assert len(rt_signals) == 1
+    assert "turned_at_midrange" in rt_signals[0]["geometry"]  # this iteration's code adds it fresh
+
+    del rt_signals[0]["geometry"]["turned_at_midrange"]  # simulate an on-disk pre-iteration-10 file
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
+    store = PlaybookStore(tmp_path / "playbook")
+    meta = store.record(**result)
+
+    reloaded = store.get(meta["id"])
+    reloaded_rt = [
+        s for s in reloaded["signals"] if s["symbol"] == "RTAAA" and s["setup_id"] == "range_trade"
+    ][0]
+    assert "turned_at_midrange" not in reloaded_rt["geometry"]
+
+    client = TestClient(app)
+    response = client.get("/research/desk/playbook", params={"id": meta["id"]})
+    assert response.status_code == 200
+    served_rt = [
+        s for s in response.json()["playbook"]["signals"]
+        if s["symbol"] == "RTAAA" and s["setup_id"] == "range_trade"
+    ][0]
+    assert "turned_at_midrange" not in served_rt["geometry"]
+
+
 def _plant_double_top_session(bar_store: BarStore, symbol: str) -> None:
     """The ``test_desk_playbook_detect.py`` canonical double_top fixture, planted through a real
     ``BarStore``."""
diff --git a/apps/backend/tests/test_desk_playbook_detect.py b/apps/backend/tests/test_desk_playbook_detect.py
index aa75178..f0a737b 100644
--- a/apps/backend/tests/test_desk_playbook_detect.py
+++ b/apps/backend/tests/test_desk_playbook_detect.py
@@ -1138,6 +1138,10 @@ def test_canonical_range_trade_long_matches_the_hand_computed_signal():
     assert geometry["low_zone_touches"] == 2
     assert geometry["high_zone_touches"] == 2
     assert geometry["crossed_midrange"] is True
+    # goal-playbook-iter-10 (R-3.2(b)): the approach swing's own peak is bar 4's high (104.8),
+    # 2.3 away from the 102.5 midpoint -- well beyond the 0.50 `PLAYBOOK_RANGE_HOLD_TOL_MBR`
+    # tolerance, so the swing did NOT turn at midrange even though it crossed it.
+    assert geometry["turned_at_midrange"] is False
     assert geometry["absorption_bar_present"] is False
     assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(2.0)
     assert signal["principles"] == []
@@ -1170,12 +1174,95 @@ def test_canonical_range_trade_short_mirrors_the_long_fixture():
     assert geometry["low_zone_touches"] == 2
     assert geometry["high_zone_touches"] == 2
     assert geometry["crossed_midrange"] is False
+    # goal-playbook-iter-10 (R-3.2(b)): the approach swing's own trough is bar 5's low (202.0),
+    # exactly 0.50 away from the 201.5 midpoint -- AT the `PLAYBOOK_RANGE_HOLD_TOL_MBR` boundary
+    # (the `_zone_held`-style inclusive "<=" reading), so the swing DID turn at midrange even
+    # though it never crossed it -- proof the two disclosures are genuinely independent facts.
+    assert geometry["turned_at_midrange"] is True
     assert geometry["absorption_bar_present"] is False
     assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(2.0)
     assert signal["principles"] == ["P5"]  # "P5 at the high side" -- the resistance-fade short
     assert signal["disclosures"]["attempt_count"] == 1
 
 
+def _turned_at_midrange_bars(symbol: str, peak_high: float) -> list[RawBar]:
+    """A range_trade LONG arming whose approach swing (the window between the low zone's first
+    touch at slot 4 and its arming-completing touch at slot 6 -- the SAME window `crossed_midrange`
+    reads) peaks at a CONTROLLED level, `peak_high`: the ONLY value that differs between the
+    `turned_at_midrange` True fixture (`peak_high=105.2`, 0.20 from the 105.0 midpoint -- inside
+    the 0.50 `PLAYBOOK_RANGE_HOLD_TOL_MBR` tolerance) and its near-miss control (`peak_high=106.0`,
+    1.00 away -- outside it). The high zone (`SH=110.0`) is touched and held ENTIRELY before the
+    window opens (slots 0 and 2), so it never contributes a bar to the window this disclosure
+    reads -- the swing's own extreme genuinely comes from the approach bar (slot 5), not from a
+    zone-touch bar the arming gate would have forced near an edge anyway. Values cross-checked by
+    direct execution (this module's own convention): the SAME signal fires regardless of
+    `peak_high` (`trigger_price=101.3`, `entry=101.3`, `entry_kind="level"`,
+    `invalidation_price=99.61`), since only slot 5's high ever changes."""
+    return [
+        _bar(symbol, E_OPEN + 0 * 300.0, 108.5, 110.0, 108.3, 109.5, 1000),  # HIGH TOUCH 1 (SH=110.0)
+        _bar(symbol, E_OPEN + 1 * 300.0, 108.8, 108.9, 106.5, 107.0, 1000),  # exits the high zone
+        _bar(symbol, E_OPEN + 2 * 300.0, 107.0, 109.6, 106.8, 109.0, 1000),  # HIGH TOUCH 2 (held, ext 0)
+        _bar(symbol, E_OPEN + 3 * 300.0, 108.0, 108.3, 104.0, 104.5, 1000),  # transition, exits high zone
+        _bar(symbol, E_OPEN + 4 * 300.0, 104.0, 104.2, 100.0, 100.5, 1000),  # LOW TOUCH 1 (SL=100.0)
+        _bar(symbol, E_OPEN + 5 * 300.0, 101.5, peak_high, 101.2, 102.0, 1000),  # the controlled swing peak
+        _bar(symbol, E_OPEN + 6 * 300.0, 101.0, 101.3, 100.2, 100.5, 1000),  # LOW TOUCH 2 (held) -- b=6
+        _bar(symbol, E_OPEN + 7 * 300.0, 100.8, 103.0, 100.5, 102.5, 1000),  # reversal trigger
+        _bar(symbol, E_OPEN + 8 * 300.0, 102.5, 102.8, 102.3, 102.6, 1000),
+        _bar(symbol, E_OPEN + 9 * 300.0, 102.6, 102.9, 102.4, 102.7, 1000),
+    ]
+
+
+def test_range_trade_turned_at_midrange_true_and_its_near_miss_control():
+    """TC-6/TC-7: spec §3.7's R-3.2(b) disclosure. The approach swing's own extreme sits within
+    `PLAYBOOK_RANGE_HOLD_TOL_MBR * MBR` (0.50) of the range midpoint (105.0: `SH=110.0`,
+    `SL=100.0`) in the True fixture (peak 105.2, 0.20 away) and just beyond it in the near-miss
+    control (peak 106.0, 1.00 away) -- the ONLY value that changes between the two calls (the
+    file's own near-miss-pairing convention: a bare change in outcome alone proves nothing without
+    isolating the one mechanism that caused it). Every pre-existing field the signal carries
+    (`trigger_price`, `entry`, `entry_kind`, `invalidation_price`, `crossed_midrange`,
+    `absorption_bar_present`, `range_width_mbr`, the touch counts) is asserted identical between
+    the two, proving this field's own presence changes nothing else."""
+    true_results = detect_range_trade(
+        _turned_at_midrange_bars("RTTM", 105.2), _RANGE_TRADE_BASELINE, "RTTM", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(true_results) == 1
+    true_signal = true_results[0]
+    assert true_signal["side"] == "long"
+    assert true_signal["trigger_price"] == pytest.approx(101.3)
+    assert true_signal["entry"] == pytest.approx(101.3)
+    assert true_signal["entry_kind"] == "level"
+    assert true_signal["invalidation_price"] == pytest.approx(99.61)
+    true_geometry = true_signal["geometry"]
+    assert true_geometry["turned_at_midrange"] is True
+    assert true_geometry["crossed_midrange"] is True
+    assert true_geometry["absorption_bar_present"] is False
+    assert true_geometry["range_width_mbr"] == pytest.approx(10.0)
+    assert true_geometry["low_zone_touches"] == 2
+    assert true_geometry["high_zone_touches"] == 2
+
+    false_results = detect_range_trade(
+        _turned_at_midrange_bars("RTTM", 106.0), _RANGE_TRADE_BASELINE, "RTTM", SESSION_DATE,
+        [], _EMPTY_INDEX_BASELINE, _PARAMS,
+    )
+    assert len(false_results) == 1
+    false_signal = false_results[0]
+    false_geometry = false_signal["geometry"]
+    assert false_geometry["turned_at_midrange"] is False
+
+    # Every OTHER field is byte-identical to the True fixture's own signal -- the near-miss control
+    # changes nothing but the one mechanism this test targets.
+    assert false_signal["trigger_price"] == true_signal["trigger_price"]
+    assert false_signal["entry"] == true_signal["entry"]
+    assert false_signal["entry_kind"] == true_signal["entry_kind"]
+    assert false_signal["invalidation_price"] == true_signal["invalidation_price"]
+    assert false_geometry["crossed_midrange"] == true_geometry["crossed_midrange"]
+    assert false_geometry["absorption_bar_present"] == true_geometry["absorption_bar_present"]
+    assert false_geometry["range_width_mbr"] == true_geometry["range_width_mbr"]
+    assert false_geometry["low_zone_touches"] == true_geometry["low_zone_touches"]
+    assert false_geometry["high_zone_touches"] == true_geometry["high_zone_touches"]
+
+
 def test_range_trade_one_sided_range_never_arms_and_its_two_sided_control_fires_once():
     """Spec §3.7's arming clause is "test the low AND high twice and hold": a session that tests
     one extreme twice while touching the other once -- the breakout-only case Ch 13 excludes --
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index da793db..0ea506b 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -5094,14 +5094,17 @@ function PlaybookSignalDetail({
         </p>
       )}
       {/* goal-playbook-iter-6 (J-06): range_trade's own geometry line -- the tested-and-held
-          range's width, each zone's own touch count, and the two disclosure flags, all rendered
-          verbatim from the served payload. */}
+          range's width, each zone's own touch count, and the disclosure flags, all rendered
+          verbatim from the served payload. goal-playbook-iter-10 (R-3.2(b)) adds one more
+          conditional chip, `turned_at_midrange`, beside the existing `crossed_midrange` --
+          optional like the others, so it renders nothing on a record recorded before it shipped. */}
       {signal.setup_id === "range_trade" && (
         <p data-testid="desk-playbook-signal-range-trade-geometry" className="mt-1 text-[11px] text-slate-500">
           range {fmt(geometry.range_width_mbr)} MBR wide · low zone touches{" "}
           {geometry.low_zone_touches} · high zone touches {geometry.high_zone_touches} · broke at
           slot {geometry.slots_to_break}
           {geometry.crossed_midrange && " · crossed midrange"}
+          {geometry.turned_at_midrange && " · turned at midrange"}
           {geometry.absorption_bar_present && " · absorption bar present"}
         </p>
       )}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index d841389..046a062 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1521,6 +1521,11 @@ export interface DeskPlaybookGeometry {
   low_zone_touches?: number;
   high_zone_touches?: number;
   crossed_midrange?: boolean;
+  // goal-playbook-iter-10 (R-3.2(b)): the BOOK midrange rule's second half -- whether the
+  // approach swing turned at the range's midpoint, beside the existing `crossed_midrange`. Optional
+  // like every other geometry field: absent (never `null`) on every record recorded before this
+  // field shipped.
+  turned_at_midrange?: boolean;
   absorption_bar_present?: boolean;
   // double_top / double_bottom only (J-06, spec §3.8-3.9)
   tops_gap_mbr?: number;
diff --git a/docs/goal.md b/docs/goal.md
index 84d4ee4..af3158d 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -137,6 +137,84 @@ files + `desk_meta_cache.py`/`test_desk_meta_cache.py`; iteration 0 records the
 Where clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
 subject to **R-1** and **R-2**.
 
+**R-3 (2026-08-11, the playbook spec rulings) — ratified.** Iterations 6–9 surfaced two open
+"The spec is canonical" items and halted the session STALLED awaiting them. Both are ruled here.
+This block is the ruling; the spec edits it directs are iteration-10 developer work (the same
+shape as iteration 6's §3.5 doc-only closure), not a licence to change detector behavior beyond
+what is named below.
+
+**R-3.1 — the `range_trade` "degenerate trigger reference" clause is RATIFIED as written.**
+The dated clarification in `docs/playbook-detector-spec.md` §3.7 Edge cases, and the matching
+fail-closed void in `_range_trade_side` (`T ≤ SL` long / `T ≥ SH` short emits nothing and the walk
+continues), stand as canonical. It is ratified on its merits: narrowing-only, no new constant,
+`playbook_input_signature` unmoved, pinned by long- and short-side tests whose controls differ in
+exactly one number, and it prevents a real defect — a long recorded with its own invalidation
+ABOVE its entry. Two corrections to the record it was justified on: the "no recorded record
+contains a `range_trade` signal" premise is now stale (87 real `range_trade` signals sit in four
+append-only records under signature `16a2734d10c91ea7`, all written after the void was in force,
+so none is born-invalidated), and dropping the setup would therefore also move the signature and
+orphan them. `range_trade` stays in `PLAYBOOK_SETUPS`; J-06 ships unchanged.
+The Constraints clause below is NOT relaxed: a developer who finds the spec ambiguous still drops
+and surfaces rather than improvising. This ruling is a decision on one instance, not a standing
+permission — the next such clause needs its own ratification.
+
+**R-3.2 — the shipped narrower-than-spec readings are ACCEPTED as canonical, with one
+completion.** Each was disclosed by an audit, each is deterministic, and iteration 10 writes each
+into the spec so code and rulebook agree. Where the spec and the shipped code differ, the spec
+is edited to match the code — no detector logic changes — EXCEPT R-3.2(b), which adds a
+disclosure:
+
+- **(a) `double_top`/`double_bottom` pair selection.** §3.8's Caps line ("the first valid valley
+  break") is rewritten to the shipped reading: the first pivot pair, in chronological
+  `(p1, p2)` order, whose full formation validates AND triggers; mirrored in §3.9. This is a
+  choice among valid formations, not a wrong one, and 155 recorded signals ride it. Recorded
+  under this reading, they remain canonical. If the back-scan's forward distributions later give
+  cause to prefer the earliest valley break, that is a NAMED revision — it adds a discipline key
+  to `playbook_parameters()` so the signature re-keys and old records are kept beside the new,
+  never a silent logic swap under the same key.
+- **(b) `crossed_midrange` — accepted AND completed.** The shipped boolean answers only §3.7's
+  first half (did price cross the range midpoint on the approach). §3.7 is split so that half is
+  named exactly, and the missing half — whether the prior swing TURNED at midrange (the BOOK
+  midrange rule) — ships as a SECOND served disclosure field on `range_trade` geometry, with its
+  `/desk` chip. Binding constraints: spec-first (the mechanical definition is written into §3.7
+  before any code); disclosure-only (it may never gate, suppress, or create a signal); and it
+  MUST reuse an already pre-registered constant for any tolerance it needs — minting a new
+  constant would move `playbook_input_signature` for a disclosure, which this ruling does not
+  authorize. The field is optional in the served payload and in `types.ts`, so the 87 already
+  recorded `range_trade` signals stay honest by lacking it rather than being backfilled. If the
+  second half genuinely cannot be defined without a new constant, DROP it and surface that —
+  do not mint one.
+- **(c) the BOOK 1.5× jump-to-base ratio is inert, and the spec must say so.** Both §3.3 gates
+  are implemented verbatim, but `PLAYBOOK_JUMP_MIN_MULT · PLAYBOOK_BASE_MAX_RANGE_MBR`
+  (1.5 × 2.0) equals `PLAYBOOK_JUMP_MIN_MOVE_MBR` (3.0), so the ADAPTATION floor always binds
+  first and the BOOK ratio can never reject a formation on its own (min observed ratio across the
+  32 recorded `jbe`/`dbi` signals: 1.735). No number moves — moving one to "activate" the gate
+  would be threshold fitting, which stays barred. §3.3 and the `PLAYBOOK_JUMP_MIN_MULT` row of
+  the constants table record the inertness plainly so the back-scan never credits a gate that has
+  never bound.
+- **(d) the cup rim constant.** §3.6 names `PLAYBOOK_RIM_MATCH_MBR` for the left rim's
+  "within X of session-high-so-far" test, while the code reads `PLAYBOOK_NEAR_EXTREME_MBR` there
+  (the rim-to-rim test correctly uses `RIM_MATCH_MBR`). Both are 1.0, so there is no behavioral
+  difference on any input and `cup_handle` has never fired. §3.6 is edited to name
+  `PLAYBOOK_NEAR_EXTREME_MBR` for the session-high test; the detector is NOT touched. This closes
+  the latent trap where a future revision of `RIM_MATCH_MBR` would silently miss that gate.
+- **(e) the `range_trade` trigger anchor — folded in here because it was never tracked.** The
+  iteration-6 audit's finding B4 (§3.7 anchors the bounce scan on "a bar `b` touches the low
+  zone", while `_range_trade_side` anchors only on the arming-completing touch) is the same
+  species as (a)–(d) but never reached the owner-rulings list. It is ruled with them: §3.7's
+  Trigger clause is narrowed to the arming-completing touch, matching the shipped code. It is
+  fail-closed (fewer signals, never invented ones). It is named here so it cannot resurface after
+  these items close.
+
+**R-3.3 — iteration 10 is the era-closing pass.** Its scope is R-3.2's spec catch-up edits, the
+R-3.2(b) disclosure field, and the iteration-9 evaluator's carried clean-up items: rewrite
+`J-10.json`'s step 6 to assert a stable piece of shipped page furniture instead of a signature
+hash that changes whenever the fixture rig is rebuilt; re-take one `/structure` capture on data
+that actually has price bars; and run the pass at FULL depth with the auditor, which four
+iteration specs asked for and the depth arbiter demoted each time. The operator restored `:8301`
+to the real store before this resume. `Config().config_fingerprint()` stays `08e471b10130e1e2`
+and `playbook_input_signature` does not move.
+
 ## Success Criteria
 
 In priority order — kept-value integrity outranks new-surface completeness outranks convenience:
diff --git a/docs/playbook-detector-spec.md b/docs/playbook-detector-spec.md
index 4da559a..36e3f75 100644
--- a/docs/playbook-detector-spec.md
+++ b/docs/playbook-detector-spec.md
@@ -145,7 +145,7 @@ continuation, P5 decreasing-volume reversal, P6 passive accumulation/distributio
 | `PLAYBOOK_OR_MINUTES` | 15 | BOOK — opening range = first 15–20 min; lower endpoint |
 | `PLAYBOOK_OR_MIN_1M_BARS` | 10 | ADAPTATION — §2 primitive 2's own floor: fewer than 10 of the 15 one-minute bars on file degrades the opening range to the 5m basis (J-01 audit B3: named in code from birth, tabulated here) |
 | `PLAYBOOK_NARROW_OR_MAX_MBR` | 3.0 | ADAPTATION — relative form of the ≤25c narrow range |
-| `PLAYBOOK_JUMP_MIN_MULT` | 1.5 | BOOK — jump ≥ 1.5–2× base; stated minimum |
+| `PLAYBOOK_JUMP_MIN_MULT` | 1.5 | BOOK — jump ≥ 1.5–2× base; stated minimum. **Inert** (2026-08-11, R-3.2(c)): dominated by `PLAYBOOK_JUMP_MIN_MOVE_MBR`/`PLAYBOOK_BASE_MAX_RANGE_MBR` (§3.3) — has never independently rejected a `jbe`/`dbi` formation |
 | `PLAYBOOK_JUMP_MIN_MOVE_MBR` | 3.0 | ADAPTATION — floor so tiny/tiny can't satisfy the ratio |
 | `PLAYBOOK_JUMP_LOOKBACK_BARS` | 6 | ADAPTATION — jump low read from the 30 min before the base |
 | `PLAYBOOK_BASE_MIN_BARS` | 3 | ADAPTATION — book gives no consolidation duration |
@@ -166,7 +166,7 @@ continuation, P5 decreasing-volume reversal, P6 passive accumulation/distributio
 | `PLAYBOOK_VERTICAL_BAR_MBR` | 2.5 | ADAPTATION — single-bar spike (spiky-approach flag) |
 | `PLAYBOOK_BOUNCE_MAX_BARS` | 3 | ADAPTATION — reversal confirmation must come fast |
 | `PLAYBOOK_RANGE_MIN_WIDTH_MBR` | 4.0 | ADAPTATION — narrower = breakout-only per Ch 13 |
-| `PLAYBOOK_RANGE_HOLD_TOL_MBR` | 0.5 | ADAPTATION — "held" tolerance; also the absorption-bar max range |
+| `PLAYBOOK_RANGE_HOLD_TOL_MBR` | 0.5 | ADAPTATION — "held" tolerance; also the absorption-bar max range and (2026-08-11, R-3.2(b)) the `turned_at_midrange` "at the midpoint" tolerance |
 | `PLAYBOOK_TOPS_MATCH_MBR` | 1.0 | ADAPTATION — two tops "at the same level" |
 | `PLAYBOOK_TOPS_MIN_SEPARATION_BARS` | 4 | ADAPTATION — tops ≥ 20 min apart |
 | `PLAYBOOK_LADDER_HEALTHY_LOW` / `_HIGH` | 0.50 / 0.75 | BOOK — ladder step 50–75% of prior step (disclosure only) |
@@ -244,7 +244,14 @@ cases. Side/band/entry/measurement always follow §0.
   `base_range = U − L ≤ PLAYBOOK_BASE_MAX_RANGE_MBR · MBR` (ADAPTATION). Jump: `jump_low` =
   min low of the `PLAYBOOK_JUMP_LOOKBACK_BARS` bars before base start; `jump = U − jump_low`;
   gates `jump ≥ PLAYBOOK_JUMP_MIN_MULT · base_range` (BOOK ≥1.5×) AND
-  `jump ≥ PLAYBOOK_JUMP_MIN_MOVE_MBR · MBR` (ADAPTATION floor). Near the high:
+  `jump ≥ PLAYBOOK_JUMP_MIN_MOVE_MBR · MBR` (ADAPTATION floor). **The BOOK ratio gate is inert**
+  (2026-08-11 annotation, R-3.2(c) — doc text only, no code or constant VALUE changed): `base_range`
+  is itself capped at `PLAYBOOK_BASE_MAX_RANGE_MBR · MBR` (2.0) by the base-formation gate above, so
+  `PLAYBOOK_JUMP_MIN_MULT · base_range` (1.5×) can never exceed `1.5 × 2.0 = 3.0` MBR — exactly
+  `PLAYBOOK_JUMP_MIN_MOVE_MBR` — meaning the ADAPTATION floor always binds at least as tightly. The
+  BOOK ratio has never independently rejected a formation (min observed ratio across the 32 recorded
+  `jbe`/`dbi` signals: 1.735). Both gates stay implemented verbatim; the back-scan must not credit
+  the BOOK ratio with a rejection it structurally cannot make. Near the high:
   `U ≥ session_high_so_far − PLAYBOOK_NEAR_EXTREME_MBR · MBR` at `t−1`. Volume: median
   RVOL(jump bars) ≥ 1.0 with max ≥ `PLAYBOOK_RVOL_ELEVATED` (P3), and median RVOL(base bars)
   ≤ `PLAYBOOK_VOL_CONTRAST_RATIO` × median RVOL(jump bars) (P4 dry base; ADAPTATION ratio).
@@ -293,8 +300,10 @@ cases. Side/band/entry/measurement always follow §0.
   `capitulation_recent`.
 
 ### 3.6 `cup_handle` (long only in v1 — the book presents the long form)
-- **Formation.** Left rim = confirmed swing-high pivot within `PLAYBOOK_RIM_MATCH_MBR · MBR`
-  of session-high-so-far. Cup bottom = min low after it; depth ≥
+- **Formation.** Left rim = confirmed swing-high pivot within `PLAYBOOK_NEAR_EXTREME_MBR · MBR`
+  of session-high-so-far (2026-08-11, R-3.2(d): named to match the shipped code — this
+  session-high-so-far test has never read `RIM_MATCH_MBR`; doc text only, `cup_handle` unchanged).
+  Cup bottom = min low after it; depth ≥
   `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR · MBR` (ADAPTATION). Right rim = later confirmed
   swing-high pivot within `RIM_MATCH` of the left rim, itself near the session high. Cup
   duration ≥ `PLAYBOOK_CUP_MIN_BARS` (BOOK ≥ 30 min; ≥ `PLAYBOOK_CUP_OPTIMAL_BARS` disclosed
@@ -323,18 +332,33 @@ cases. Side/band/entry/measurement always follow §0.
   each with `zone_touches ≥ 2` (re-arm semantics), each later touch extending the extreme by
   ≤ `PLAYBOOK_RANGE_HOLD_TOL_MBR · MBR` ("held").
 - **Trigger — the mechanical reading of "first sign of strength" (the book's vaguest
-  instruction; this reading is the pre-registered choice):** a bar `b` touches the low zone;
-  the first bar `t` with `b < t ≤ b + PLAYBOOK_BOUNCE_MAX_BARS`, `high > high[t−1]`, and
-  `min(low[b..t−1]) ≥ SL − RANGE_HOLD_TOL·MBR`. `T = high[t−1]` — the same reversal-bar
-  grammar as the capitulation bounce (one shared mechanism, not a second vague one).
-  Resistance-fade mirrored.
+  instruction; this reading is the pre-registered choice):** `b` = the arming-completing touch of
+  the low zone specifically — the LAST of the `≥ 2` touches the Arming clause above requires, not
+  any earlier touch in that same sequence (2026-08-11, R-3.2(e): narrowed to name the shipped
+  anchor exactly, `_range_trade_side`, `desk_playbook_detect.py:1068-1153`; doc text only, zero
+  code change). From `b`: the first bar `t` with `b < t ≤ b + PLAYBOOK_BOUNCE_MAX_BARS`,
+  `high > high[t−1]`, and `min(low[b..t−1]) ≥ SL − RANGE_HOLD_TOL·MBR`. `T = high[t−1]` — the same
+  reversal-bar grammar as the capitulation bounce (one shared mechanism, not a second vague one).
+  Resistance-fade mirrored (`b` = the high zone's own arming-completing touch).
 - **Invalidation.** Long `S = SL`, `SL − 0.30·(T − SL)` (BOOK: just outside the range
   bounds). Short mirrored.
 - **Caps.** 1 per side per symbol-session.
-- **Disclosures.** `range_width_mbr`, per-zone touch counts, `crossed_midrange` on the
-  approach + whether the prior swing turned at midrange (BOOK midrange rule),
-  `absorption_bar_present` — a zone bar with `RVOL ≥ PLAYBOOK_RVOL_ELEVATED` and range ≤
-  `RANGE_HOLD_TOL·MBR` (P6 passive accumulation/distribution, mechanical ADAPTATION).
+- **Disclosures.** `range_width_mbr`, per-zone touch counts, `absorption_bar_present` — a zone
+  bar with `RVOL ≥ PLAYBOOK_RVOL_ELEVATED` and range ≤ `RANGE_HOLD_TOL·MBR` (P6 passive
+  accumulation/distribution, mechanical ADAPTATION) — plus two named midrange disclosures
+  (2026-08-11, R-3.2(b): split spec-first, BEFORE any code change, into the two fields below; the
+  shipped boolean answered only the first). Both read over the SAME approach window
+  `session_bars[b0..b]` (`b0` = the armed zone's own FIRST touch, `b` = the Trigger clause's
+  arming-completing touch above) — entry-time legal by construction, since neither reads past `b`:
+  - `crossed_midrange` — did price cross the range midpoint on the approach: any bar's high
+    (long) / low (short) within the window reaches `(SH + SL)/2` or beyond.
+  - `turned_at_midrange` — whether the prior swing turned at midrange (the BOOK midrange rule):
+    the swing's OWN extreme within the SAME window (`max(high)` long / `min(low)` short — the
+    furthest point price reached before returning to complete the arming touch `b`) lies within
+    `PLAYBOOK_RANGE_HOLD_TOL_MBR · MBR` of `(SH + SL)/2` — this detector's own already-registered
+    "held" tolerance, reused verbatim for an "at the midpoint" reading; no new constant. Optional
+    key (absent on every record recorded before this field shipped); disclosure-only — it never
+    gates, suppresses, or creates a signal.
   Principles: P6 when absorption present; P5 at the high side.
 - **Edge cases.** A strict break beyond a zone by > `HOLD_TOL` dissolves range-mode (re-arms
   only on a new twice-tested range).
@@ -365,8 +389,12 @@ cases. Side/band/entry/measurement always follow §0.
   valley break, never the retest.
 - **Invalidation.** `S = max(high(p1), high(p2))`; `S + 0.30·(S − T)` (BOOK: above the top).
   Nominal risk is the full pattern height — disclosed as `nominal_risk_mbr`, never shrunk.
-- **Caps.** 1 per detector per symbol-session (the first valid valley break; a triple top
-  cannot re-fire the same valley).
+- **Caps.** 1 per detector per symbol-session (2026-08-11, R-3.2(a) — rewritten to the shipped
+  reading; doc text only, zero change to `_find_double_extreme`/`desk_playbook_detect.py`): every
+  confirmed-pivot pair `(p1, p2)` is searched in chronological order, and the FIRST pair whose full
+  formation validates AND triggers wins — never the earliest valley break scanned in isolation from
+  which pair produced it. A triple top cannot re-fire the same valley once its own pair has already
+  triggered.
 - **Disclosures.** `tops_gap_mbr`, `tops_separation_bars`, `valley_depth_mbr`,
   `second_top_rvol_vs_first` (median RVOL of p2±1 / p1±1 — P5's drying retest, disclosed not
   gated), `attempt_count` (≥ 3 attempts before the valley break is the book's
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-playbook-index.html           |   4 +-
 runs/goal-session-playbook/.engine.lock/epoch      |   2 +-
 runs/goal-session-playbook/.engine.lock/pid        |   2 +-
 runs/goal-session-playbook/engine.pid              |   2 +-
 .../journey-scripts/J-10.json                      |   4 +-
 runs/goal-session-playbook/session.json            |  11 +-
 runs/goal-session-playbook/state/assumptions.md    | 205 +++------------------
 runs/goal-session-playbook/state/blueprint.md      |  26 ++-
 runs/goal-session-playbook/state/lessons.md        |  94 +---------
 runs/goal-session-playbook/summary.md              | 174 +++++++++++++----
 runs/goal-session-playbook/telemetry.jsonl         |  33 ++++
 runs/goal-session-playbook/trace/trace.jsonl       |   6 +
 12 files changed, 247 insertions(+), 316 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
