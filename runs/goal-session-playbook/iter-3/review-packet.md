# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 11. Shown in full: 10.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (571 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_playbook.py b/apps/backend/app/research/desk_playbook.py
index 7793897..62d8c69 100644
--- a/apps/backend/app/research/desk_playbook.py
+++ b/apps/backend/app/research/desk_playbook.py
@@ -61,7 +61,7 @@ from .desk_forward import (
     _measure_from,
 )
 from .desk_playbook_detect import detect_opening_range_breaks
-from .desk_playbook_features import baselines, opening_range, rth_session_slice
+from .desk_playbook_features import baselines, opening_range, rth_session_slice, side_sign
 from .desk_sessions import refuse_if_not_a_session
 
 __all__ = [
@@ -409,7 +409,7 @@ def _measure_signal(signal: dict, session_5m: list, session_1m: list) -> tuple[d
     measure_bars, anchor_index, tf_minutes = _measurement_anchor(
         session_5m, session_1m, trigger_idx_5m, signal["trigger_price"]
     )
-    sign = 1.0 if signal["side"] == "long" else -1.0
+    sign = side_sign(signal["side"])
     forward = _measure_from(
         measure_bars, anchor_index, signal["entry"], signal["entry_kind"], tf_minutes, sign
     )
@@ -419,6 +419,25 @@ def _measure_signal(signal: dict, session_5m: list, session_1m: list) -> tuple[d
     return forward, breached, measure_bars, tf_minutes
 
 
+def _baseline_seed(session_date: str, symbol: str, setup_id: str, firing_index: int) -> str:
+    """The baseline-anchor draw's own seed for ONE signal firing of ``(symbol, setup_id)`` within
+    ``session_date`` -- ``firing_index`` is the running WITHIN-SESSION count of prior firings of
+    this EXACT ``(symbol, setup_id)`` pair (``0`` for the first).
+
+    **The recipe is UNCHANGED -- no discriminator suffix at all -- for ``firing_index == 0``.**
+    Every currently-recordable signal (opening-range-break fires at MOST once per symbol-session,
+    the detector's own mutual-exclusion rule) draws the byte-identical seed it always has, so a
+    fresh compute over already-recorded fixture inputs reproduces byte-identical output before vs.
+    after this change. A detector that CAN fire more than once for the same ``(symbol, setup_id)``
+    in one session (J-04's JBE ladder steps) gets a distinguishing ``:<firing_index>`` suffix from
+    its SECOND firing on, so each firing draws an INDEPENDENT anchor index instead of colliding on
+    the identical one the un-discriminated seed would draw twice -- today this is a genuine no-op
+    (the collision it guards against cannot occur yet), but it must land before J-04 lands a
+    detector that can trigger it."""
+    discriminator = "" if firing_index == 0 else f":{firing_index}"
+    return f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}{discriminator}"
+
+
 def compute_playbook(
     universe_store,
     bar_store,
@@ -483,6 +502,12 @@ def compute_playbook(
     baseline_pool: dict[str, list[dict]] = {}
     pool_counts: dict[str, int] = {}
     pool_beyond_cap: dict[str, int] = {}
+    # The baseline-draw seed's own per-firing discriminator (see `_baseline_seed`) -- keyed
+    # "<symbol>:<setup_id>", DISTINCT from `pool_counts` above (that one bounds the CROSS-SYMBOL
+    # pooling cap; this one counts how many times THIS symbol's own (symbol, setup_id) pair has
+    # already fired THIS session, currently always 0 since a symbol is walked once and the
+    # opening-range-break detector fires at most one signal per call).
+    firing_counts: dict[str, int] = {}
 
     for symbol in members:
         if should_abort is not None and should_abort():
@@ -550,9 +575,12 @@ def compute_playbook(
             pool_counts[pool_key] = count_so_far + 1
             if count_so_far < DESK_FORWARD_MAX_TOUCHES_PER_ROW:
                 signal_pool.setdefault(pool_key, []).append(forward)
-                sign = 1.0 if signal["side"] == "long" else -1.0
+                sign = side_sign(signal["side"])
+                firing_key = f"{symbol}:{signal['setup_id']}"
+                firing_index = firing_counts.get(firing_key, 0)
+                firing_counts[firing_key] = firing_index + 1
                 rng = random.Random(
-                    f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{signal['setup_id']}"
+                    _baseline_seed(session_date, symbol, signal["setup_id"], firing_index)
                 )
                 k = min(1, len(measure_bars))  # this symbol's own capped signal count is <= 1
                 for anchor_idx in _draw_anchor_indices(rng, len(measure_bars), k):
diff --git a/apps/backend/app/research/desk_playbook_detect.py b/apps/backend/app/research/desk_playbook_detect.py
index f2e7535..178d453 100644
--- a/apps/backend/app/research/desk_playbook_detect.py
+++ b/apps/backend/app/research/desk_playbook_detect.py
@@ -31,7 +31,13 @@ from __future__ import annotations
 from datetime import datetime, timezone
 
 from ..providers.adapters.base import RawBar
-from .desk_playbook_features import market_context, rth_session_slice, vertical_move, zone_touches
+from .desk_playbook_features import (
+    market_context,
+    rth_session_slice,
+    side_sign,
+    vertical_move,
+    zone_touches,
+)
 
 __all__ = ["detect_opening_range_breaks"]
 
@@ -157,7 +163,7 @@ def _market_block(
             "reason": "SPY's own baseline MBR is unavailable -- cannot normalize the market move",
         }
 
-    sign = 1.0 if side == "long" else -1.0
+    sign = side_sign(side)
     move_mbr = mkt["move"] / index_mbr
     signed = sign * move_mbr
     band = params["mkt_neutral_band_mbr"]
diff --git a/apps/backend/app/research/desk_playbook_features.py b/apps/backend/app/research/desk_playbook_features.py
index 368e012..2087ef9 100644
--- a/apps/backend/app/research/desk_playbook_features.py
+++ b/apps/backend/app/research/desk_playbook_features.py
@@ -45,6 +45,7 @@ __all__ = [
     "vertical_move",
     "zone_touches",
     "market_context",
+    "side_sign",
 ]
 
 # Regular trading hours, ET wall-clock -- a market-structure fact, not a tunable (the
@@ -294,3 +295,20 @@ def market_context(
         "close_before": prior[-1].close,
         "bars_available": len(prior),
     }
+
+
+def side_sign(side: str) -> float:
+    """The playbook's OWN long/short directional multiplier: ``+1.0`` for ``"long"``, ``-1.0`` for
+    ``"short"`` -- the single owner of a literal (``1.0 if side == "long" else -1.0``) that used to
+    be written three separate times across ``desk_playbook.py`` (``_measure_signal`` and the
+    baseline-draw branch of ``compute_playbook``) and ``desk_playbook_detect.py``
+    (``_market_block``).
+
+    **Deliberately NOT `desk_forward._side_sign`, and never imported from it.** That helper is
+    built exclusively for the rail's OWN support/resistance wall vocabulary
+    (``-1.0 if side == "resistance" else 1.0``): `desk_forward._side_sign("short")` returns
+    ``+1.0`` (since ``"short" != "resistance"``), which would silently flip every short-side
+    playbook signal's forward return and MDD sign positive -- a fabricated-data bug, not a fix.
+    `desk_forward._measure_from`'s own docstring confirms ``sign`` is a caller-supplied float: each
+    caller computes its OWN sign for its OWN side vocabulary, and this is the playbook's."""
+    return 1.0 if side == "long" else -1.0
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 22cd5b0..4bd17a3 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -123,7 +123,7 @@ from .desk_forward import ForwardStore, resolve_desk_forward_dir
 from .desk_forward_compute import DeskForwardComputeManager
 from .desk_forward_log import ForwardRunStore, resolve_desk_forward_log_dir
 from .desk_forward_pins import resolve_desk_forward_pins
-from .desk_playbook import PlaybookSessionRefused, PlaybookStore, resolve_desk_playbook_dir
+from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
 from .desk_playbook_compute import DeskPlaybookComputeManager
 from .desk_playbook_log import PlaybookRunStore, resolve_desk_playbook_log_dir
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
diff --git a/apps/backend/tests/test_desk_playbook.py b/apps/backend/tests/test_desk_playbook.py
index ca62fff..2c4de3d 100644
--- a/apps/backend/tests/test_desk_playbook.py
+++ b/apps/backend/tests/test_desk_playbook.py
@@ -13,6 +13,7 @@ from __future__ import annotations
 
 import hashlib
 import json
+import random
 from datetime import datetime
 
 import pytest
@@ -25,13 +26,18 @@ from app.research import desk_playbook as desk_playbook_module
 from app.research import desk_playbook_detect as desk_playbook_detect_module
 from app.research import desk_playbook_features as desk_playbook_features_module
 from app.research.bars import BarStore
-from app.research.desk_forward import DESK_FORWARD_MAX_TOUCHES_PER_ROW, _measure_from
+from app.research.desk_forward import (
+    DESK_FORWARD_MAX_TOUCHES_PER_ROW,
+    _draw_anchor_indices,
+    _measure_from,
+)
 from app.research.desk_playbook import (
     PLAYBOOK_REGISTER,
     PlaybookAlreadyRecorded,
     PlaybookIntegrityError,
     PlaybookSessionRefused,
     PlaybookStore,
+    _baseline_seed,
     _invalidation_breached,
     _measure_signal,
     _measurement_anchor,
@@ -417,6 +423,100 @@ def test_playbook_register_passes_copy_discipline():
     assert find_violations(PLAYBOOK_REGISTER) == []
 
 
+# --- goal-playbook-iter-3 (J-03): the sign-duplication consolidation (TC-10) -----------------------
+
+import re as _re  # noqa: E402 -- kept local to this guard section, mirroring the test's own scope
+
+
+def _strip_python_docstrings_and_comments(source: str) -> str:
+    """A source-introspection guard must scan CODE, not the prose that explains it -- this
+    module's own `side_sign` docstring necessarily discusses the literal it replaces and the
+    rail's `_side_sign` it is deliberately NOT, which would otherwise false-positive the very
+    guards below (the ``test_desk_ui_guards.py``/``test_desk_refresh_chain_guard.py``
+    comment-stripping precedent, applied to Python: triple-quoted docstrings and ``#`` comments
+    are removed; ordinary single/double-quoted string literals in real code are left alone)."""
+    without_triple = _re.sub(r'"""(?:.|\n)*?"""', "", source)
+    without_triple = _re.sub(r"'''(?:.|\n)*?'''", "", without_triple)
+    return _re.sub(r"#[^\n]*", "", without_triple)
+
+
+def test_no_playbook_module_still_writes_the_inline_sign_literal():
+    """The one owner is now `desk_playbook_features.side_sign` -- the literal
+    ``1.0 if side == "long" else -1.0`` (in either quote style) must appear nowhere in
+    `desk_playbook.py`'s or `desk_playbook_detect.py`'s own CODE any more (every former call site
+    -- `desk_playbook.py`'s `_measure_signal` and `compute_playbook`'s baseline-draw branch,
+    `desk_playbook_detect.py`'s `_market_block` -- now calls `side_sign` instead), and appears
+    EXACTLY ONCE in `desk_playbook_features.py` -- `side_sign`'s own function body, the single
+    canonical implementation the other two modules now call instead of repeating."""
+    literal_variants = (
+        '1.0 if side == "long" else -1.0',
+        "1.0 if side == 'long' else -1.0",
+        '1.0 if signal["side"] == "long" else -1.0',
+    )
+    for module in (desk_playbook_module, desk_playbook_detect_module):
+        source = _strip_python_docstrings_and_comments(open(module.__file__, encoding="utf-8").read())
+        for literal in literal_variants:
+            assert literal not in source, (
+                f"{module.__file__} still writes the inline sign literal {literal!r} -- it must "
+                "call desk_playbook_features.side_sign instead (the single owner)"
+            )
+
+    features_source = _strip_python_docstrings_and_comments(
+        open(desk_playbook_features_module.__file__, encoding="utf-8").read()
+    )
+    assert features_source.count('1.0 if side == "long" else -1.0') == 1, (
+        "the literal must appear EXACTLY ONCE in desk_playbook_features.py -- side_sign's own "
+        "single canonical implementation, never a second copy"
+    )
+
+
+def test_no_playbook_module_imports_desk_forwards_side_sign():
+    """`desk_forward._side_sign` is built exclusively for the rail's own support/resistance
+    vocabulary -- importing it into a playbook module's CODE would silently flip every short
+    signal's sign positive (see `side_sign`'s own docstring, which is exactly why this scan strips
+    docstrings before looking). Zero diff to `desk_forward.py` itself."""
+    for module in (desk_playbook_module, desk_playbook_detect_module, desk_playbook_features_module):
+        source = _strip_python_docstrings_and_comments(open(module.__file__, encoding="utf-8").read())
+        assert "_side_sign" not in source, (
+            f"{module.__file__} references _side_sign in its own code -- the playbook must use its "
+            "OWN desk_playbook_features.side_sign, never desk_forward's"
+        )
+
+
+def test_measure_signal_and_baseline_draw_both_call_the_shared_side_sign():
+    """Counter-test: proves the source-scan above actually distinguishes the fixed source from the
+    old, un-consolidated one -- a literal reintroduced anywhere in real CODE (not merely prose) is
+    still caught after stripping."""
+    seeded_source = 'sign = 1.0 if signal["side"] == "long" else -1.0\n'
+    stripped = _strip_python_docstrings_and_comments(seeded_source)
+    assert '1.0 if signal["side"] == "long" else -1.0' in stripped
+
+    seeded_docstring_only = '"""mentions 1.0 if side == "long" else -1.0 in prose only."""\n'
+    assert '1.0 if side == "long" else -1.0' not in _strip_python_docstrings_and_comments(
+        seeded_docstring_only
+    )
+
+    playbook_source = open(desk_playbook_module.__file__, encoding="utf-8").read()
+    assert playbook_source.count("side_sign(signal[\"side\"])") == 2  # _measure_signal + baseline draw
+    detect_source = open(desk_playbook_detect_module.__file__, encoding="utf-8").read()
+    assert "side_sign(side)" in detect_source
+
+
+# --- goal-playbook-iter-3 (J-03): desk_routes.py drops the unused import (TC-13) --------------------
+
+
+def test_desk_routes_no_longer_imports_playbook_session_refused():
+    """`PlaybookSessionRefused` is caught internally by `desk_playbook_compute.py`, never by the
+    route layer -- the import at `desk_routes.py` was dead. The app still starts and serves
+    cleanly with it removed."""
+    from app.research import desk_routes as desk_routes_module
+
+    source = open(desk_routes_module.__file__, encoding="utf-8").read()
+    assert "PlaybookSessionRefused" not in source
+    response = TestClient(app).get("/research/desk/playbook")
+    assert response.status_code == 200
+
+
 # --- J-02: measurement -- convention identity (TC-1) --------------------------------------------
 
 
@@ -524,6 +624,86 @@ def test_baseline_anchors_are_seeded_and_reproducible(tmp_path, bar_store, unive
     assert pool[0]["entry_kind"] == "close"
 
 
+def test_baseline_seed_at_firing_index_zero_matches_the_original_recipe_literal():
+    """TC-12: `firing_index=0`'s seed carries NO discriminator suffix at all -- byte-identical to
+    the pre-fix literal recipe (`f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:
+    {setup_id}"`)."""
+    seed0 = _baseline_seed(SESSION_DATE, "AAA", "open_high_break", 0)
+    assert seed0 == f"1729:playbook-{SESSION_DATE}:AAA:open_high_break"
+    from app.research.desk_forward import DESK_FORWARD_BASELINE_SEED
+
+    assert seed0 == f"{DESK_FORWARD_BASELINE_SEED}:playbook-{SESSION_DATE}:AAA:open_high_break"
+
+
+def test_single_firing_baseline_draw_uses_firing_index_zero(monkeypatch, tmp_path, bar_store, universe_store):
+    """TC-12: every currently-recordable signal (opening-range-break fires at most once per
+    symbol-session) draws its baseline anchor at `firing_index=0` -- the ONE case
+    `_baseline_seed` reproduces byte-identically to the pre-fix recipe (the test above). Combined,
+    these two prove the seed-collision fix is a genuine no-op for any signal this iteration's
+    detectors can actually produce."""
+    _plant_baseline_sessions(bar_store, "AAA")
+    _plant_firing_session(bar_store, "AAA")
+    calls: list[tuple] = []
+    original = desk_playbook_module._baseline_seed
+
+    def _spy(session_date, symbol, setup_id, firing_index):
+        calls.append((session_date, symbol, setup_id, firing_index))
+        return original(session_date, symbol, setup_id, firing_index)
+
+    monkeypatch.setattr(desk_playbook_module, "_baseline_seed", _spy)
+    compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert calls == [(SESSION_DATE, "AAA", "open_high_break", 0)]
+
+
+def test_seed_collision_fix_reproduces_byte_identical_output_for_recordable_data(
+    tmp_path, bar_store, universe_store
+):
+    """TC-12: record the canonical single-fire fixture, then run a FRESH compute over the identical
+    inputs post-fix -- every byte of the result (especially `baseline_anchors`/`summary`) matches,
+    and re-recording under the identical key is refused (the same file, never a new version); the
+    original file on disk is untouched."""
+    store, meta = _record_aaa(tmp_path, bar_store, universe_store)
+    path = store._path(meta["id"])
+    before = _sha256_file(path)
+
+    fresh = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
+    assert fresh["baseline_anchors"] == meta["baseline_anchors"]
+    assert fresh["summary"] == meta["summary"]
+    assert fresh["signals"] == meta["signals"]
+
+    with pytest.raises(PlaybookAlreadyRecorded):
+        store.record(**fresh)
+    assert _sha256_file(path) == before
+
+
+def test_two_firings_of_the_same_symbol_setup_pair_draw_independent_non_colliding_anchors():
+    """TC-11: a synthetic fixture where the SAME (symbol, setup_id) pair fires TWICE within one
+    session -- each firing's own seed differs (`firing_index` 0 vs 1) and the anchor indices they
+    draw differ too, so the baseline pool genuinely grows to reflect BOTH independent draws instead
+    of the identical index being drawn twice (today's actual walk cannot yet produce two firings of
+    one symbol -- opening-range-break fires at most once per symbol-session -- so this fixture
+    exercises the seed/draw machinery directly, exactly as the DoD frames it: a no-op today, load-
+    bearing the moment a detector CAN fire twice for one (symbol, setup_id))."""
+    measure_bars = [
+        _bar("AAA", "5m", E_OPEN + i * 300.0, 100.0 + i, 100.5 + i, 99.5 + i, 100.2 + i)
+        for i in range(20)
+    ]
+    pool: list[dict] = []
+    seeds: list[str] = []
+    for firing_index in range(2):
+        seed = _baseline_seed(SESSION_DATE, "AAA", "open_high_break", firing_index)
+        seeds.append(seed)
+        rng = random.Random(seed)
+        (anchor_idx,) = _draw_anchor_indices(rng, len(measure_bars), 1)
+        anchor_bar = measure_bars[anchor_idx]
+        pool.append(_measure_from(measure_bars, anchor_idx, anchor_bar.close, "close", 5, 1.0))
+
+    assert seeds[0] != seeds[1]  # no seed collision -- the discriminator changed the seed
+    assert seeds[1] == f"{seeds[0]}:1"
+    assert len(pool) == 2  # the baseline pool grew to reflect both independent draws
+    assert pool[0]["at_utc"] != pool[1]["at_utc"]  # the two draws landed on different anchor bars
+
+
 def test_baseline_anchors_unchanged_by_an_unrelated_zero_signal_symbol(tmp_path, bar_store):
     _plant_baseline_sessions(bar_store, "AAA")
     _plant_firing_session(bar_store, "AAA")
diff --git a/apps/backend/tests/test_desk_playbook_features.py b/apps/backend/tests/test_desk_playbook_features.py
index c55b41a..3c9646b 100644
--- a/apps/backend/tests/test_desk_playbook_features.py
+++ b/apps/backend/tests/test_desk_playbook_features.py
@@ -20,6 +20,7 @@ from app.research.desk_playbook_features import (
     market_context,
     opening_range,
     rth_session_slice,
+    side_sign,
     swing_pivots,
     vertical_move,
     zone_touches,
@@ -305,3 +306,21 @@ def test_market_context_computes_the_move_once_enough_bars_exist():
     assert result == {
         "move": pytest.approx(0.6), "close_before": pytest.approx(400.9), "bars_available": 10,
     }
+
+
+# --- side_sign (goal-playbook-iter-3, J-03: the one owner of the playbook's own long/short sign) ---
+
+
+def test_side_sign_long_is_positive_and_short_is_negative():
+    assert side_sign("long") == 1.0
+    assert side_sign("short") == -1.0
+
+
+def test_side_sign_is_never_desk_forwards_side_sign():
+    """Deliberately NOT `desk_forward._side_sign` -- that helper is built for the rail's OWN
+    support/resistance vocabulary and returns +1.0 for "short" (since "short" != "resistance"),
+    which would silently flip every short-side playbook signal's sign positive."""
+    from app.research.desk_forward import _side_sign as rail_side_sign
+
+    assert rail_side_sign("short") == 1.0  # the rail's own answer -- proves the two must differ
+    assert side_sign("short") == -1.0
diff --git a/apps/backend/tests/test_desk_refresh_chain_guard.py b/apps/backend/tests/test_desk_refresh_chain_guard.py
index 8113ad0..cecf3da 100644
--- a/apps/backend/tests/test_desk_refresh_chain_guard.py
+++ b/apps/backend/tests/test_desk_refresh_chain_guard.py
@@ -101,8 +101,25 @@ _UNIVERSE_FETCH_PATH = "/research/desk/universe/fetch"
 # BEFORE committing to a sweep measured in hours). The timeout is untouched -- the chain still owns
 # exactly one sleep. Neither new effect can reach a trigger, which is the property the scan below
 # actually polices; the counts are here so that scan stays provably complete.
-_EXPECTED_EFFECT_COUNT = 15
-_EXPECTED_INTERVAL_COUNT = 5
+#
+# 15 -> 17 and 5 -> 6 for the Playbook Signals section (goal-playbook-iter-3, J-03) -- the SIXTH
+# compute manager (`desk_playbook_compute.py`), entirely independent of the refresh chain (a
+# playbook run is never a sixth chain step; the section owns its own session date, resolved from
+# the ALREADY-fetched `sessionsResult`, never from the chain's own as-of range). +1 effect: the
+# resolved-date-keyed read, batched into ONE effect for both the playbook record GET and its run-
+# ledger GET (the mount-effect "several GETs, one effect" precedent, applied here since both
+# answer the SAME resolved date rather than different questions the way the forward-coverage/
+# forward-run-ledger pair above does). +1 effect, +1 interval: the playbook-compute poll, mirroring
+# the existing five polls' shape exactly (registered only while a job the operator STARTED is
+# running -- "running" OR "cancelling", since this manager's own snapshot has no distinct
+# "cancelled" terminal state; a completed cancel reverts it straight to "idle", which already
+# fails both conditions and stops the poll). The mount-time seed for this SIXTH compute snapshot
+# joined the EXISTING nine-GET mount effect (no new effect for it, the `forwardComputeRef` mirror
+# precedent). The timeout is untouched -- the playbook section has no wait-tick of its own; it is
+# not part of the chain. Neither new effect can reach a trigger, which is the property the scan
+# below actually polices; the counts are here so that scan stays provably complete.
+_EXPECTED_EFFECT_COUNT = 17
+_EXPECTED_INTERVAL_COUNT = 6
 _EXPECTED_TIMEOUT_COUNT = 1
 
 # Everything that could start real work. The chain's own driver is included: an effect that calls
@@ -119,6 +136,10 @@ _TRIGGER_CALLS = (
     "triggerDeskReconcileCompute(",
     "triggerDeskScreenCompute(",
     "triggerDeskForwardCompute(",
+    # goal-playbook-iter-3 (J-03): the Playbook Signals section's own handler/client pair --
+    # mirrors the handleTriggerForward(/triggerDeskForwardCompute( pair immediately above exactly.
+    "handleTriggerPlaybook(",
+    "triggerDeskPlaybookCompute(",
 )
 
 # Machinery that can invoke a handler without a user click. None of it is used by this page today;
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index f64768f..619b179 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -149,6 +149,14 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
 # `touchValue` for a per-horizon leaf, `avgCell` for a row average, `summaryCell` for a summary
 # cell) so a derived spread/sum/ratio over ANY served forward value is caught. The v1 `*_bps`
 # paths died with the close-anchored shape.
+# goal-playbook-iter-3 (J-03): extended AGAIN for the Playbook Signals section's own NEW numeric
+# fields -- `signal.trigger_price`/`signal.invalidation_price` (a playbook signal's own served
+# prices, with no forward-panel analogue). The section's per-horizon forward cells and baseline
+# summary cells introduce NO new binding at all: `PlaybookSignalForward`/`PlaybookSummaryCells`
+# reuse `ForwardTouchTable`/`ForwardTouchMeasureCells`/`ForwardAvgCellView` VERBATIM, so those
+# values are already reached through the EXISTING `touchRow.*`/`touchValue.*`/`avgCell.*` bindings
+# this guard already covers -- see test_desk_page_price_arithmetic_guard_catches_playbook_field_
+# arithmetic below for the counter-test proving both the new and the reused bindings are caught.
 _PRICE_ARITHMETIC_FIELDS = (
     r"row\.(?:distance_bps|price_low|price_high|reference_close"
     r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
@@ -159,6 +167,7 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|touchValue\.(?:return_pct|exit_price|mdd_long_pct|mdd_short_pct|effective_minutes)"
     r"|avgCell\.(?:mean_pct|median_pct)"
     r"|summaryCell\.(?:mean_pct|median_pct)"
+    r"|signal\.(?:trigger_price|invalidation_price)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -243,6 +252,24 @@ def test_desk_page_price_arithmetic_guard_catches_exit_price_and_per_horizon_mdd
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_worst) is not None
 
 
+def test_desk_page_price_arithmetic_guard_catches_playbook_field_arithmetic():
+    """goal-playbook-iter-3 (J-03) counter-test: the extended guard catches arithmetic on the
+    Playbook Signals section's own NEW `signal.trigger_price`/`signal.invalidation_price` bindings,
+    and -- since that section's forward-cell/summary-cell renderers REUSE `ForwardTouchTable`/
+    `ForwardTouchMeasureCells`/`ForwardAvgCellView` verbatim rather than re-declaring lookalikes --
+    also still catches arithmetic on the `touchRow`/`touchValue`/`avgCell` bindings those shared
+    renderers use, proving the reuse did not quietly route the playbook's forward/baseline numbers
+    around this guard."""
+    seeded_trigger = "const stop = signal.trigger_price - signal.invalidation_price;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_trigger) is not None
+
+    seeded_forward = "const gain = touchValue.exit_price - touchRow.entry_price;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_forward) is not None
+
+    seeded_baseline = "const edge = avgCell.mean_pct - avgCell.median_pct;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline) is not None
+
+
 # goal-desk-iter-24 (J-16) TC-7 (a): the ranked table's own reflow adds a `rank` cell rendering
 # each row's own 1-based position in the served `rows` array (the `.map` index) -- this guard
 # proves the page never sorts, reverses, or re-slices `rows` to produce that position (or any
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 2153551..014b049 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -25,8 +25,13 @@ import {
   fetchDeskSessions,
   fetchDeskTopupCompute,
   fetchDeskTopupRuns,
+  cancelDeskPlaybookCompute,
+  fetchDeskPlaybook,
+  fetchDeskPlaybookCompute,
+  fetchDeskPlaybookRuns,
   triggerDeskDeepBackfillCompute,
   triggerDeskForwardCompute,
+  triggerDeskPlaybookCompute,
   triggerDeskReconcileCompute,
   triggerDeskScreenCompute,
   triggerDeskTopupCompute,
@@ -45,6 +50,14 @@ import type {
   DeskForwardRun,
   DeskForwardRunsListResult,
   DeskForwardTouch,
+  DeskPlaybookAbsence,
+  DeskPlaybookComputeSnapshot,
+  DeskPlaybookReadResult,
+  DeskPlaybookRecord,
+  DeskPlaybookRun,
+  DeskPlaybookRunsListResult,
+  DeskPlaybookSignal,
+  DeskPlaybookSummaryCell,
   DeskReconcileComputeSnapshot,
   DeskReconcileDrift,
   DeskReconcileRun,
@@ -3682,6 +3695,40 @@ function validateScreenDayRange(
   };
 }
 
+// goal-playbook-iter-3 (J-03): a single-date variant of `validateScreenDayRange` above -- the
+// Playbook Signals section takes ONE session date, not a range, so the two-bound machinery above
+// does not apply. Blank resolves to the newest date PROVEN by `sessionsResult`'s own recorded-
+// session set (already fetched at mount for the history calendar, read through
+// `provenSessionWindow` exactly as the calendar does) -- deliberately NOT `nextTradingStamp()`
+// (screen's OWN "the upcoming session, whether or not it has traded yet" default): a playbook
+// needs bars that already exist to detect against, so its blank default is the newest date proven
+// to have them, never a future guess. A well-formed but not-yet-proven date is still accepted here
+// (this function only checks the STRING is a real calendar day) -- whether it is actually a
+// recorded trading session is the backend's own call, surfaced verbatim from a Run Playbook click
+// against it, never pre-empted by a client-authored guess (see the Playbook Signals section's own
+// non-session-refusal handling).
+function validatePlaybookSessionDay(
+  raw: string,
+  sessionsResult: { ok: boolean; data: DeskSessionsResult | null } | null,
+): { error: string | null; date: string | null } {
+  const trimmed = raw.trim();
+  if (trimmed === "") {
+    const window = provenSessionWindow(sessionsResult);
+    if (window === null || window.sessions.size === 0) {
+      return { error: null, date: null }; // nothing recorded yet to default to -- an honest null
+    }
+    return { error: null, date: [...window.sessions].sort().at(-1) ?? null };
+  }
+  if (!isRealCalendarDay(trimmed)) {
+    return {
+      error:
+        "Enter the session date as a real yyyy-MM-dd, or leave it blank for the most recent recorded session.",
+      date: null,
+    };
+  }
+  return { error: null, date: trimmed };
+}
+
 // Step labels follow the day(s) a RUN actually submitted — a copy choice only, never a derived
 // backend fact. A single-day run for today keeps the shipped label byte-identical.
 function refreshChainStepLabel(key: RefreshChainStepKey, run: RefreshChainRun): string {
@@ -4335,6 +4382,695 @@ function DeskPopulatedScreen({
 
 // --- The page --------------------------------------------------------------------------------------
 
+// --- Playbook Signals (Era B2, J-01/J-02/J-03) -- goal-playbook-iter-3: the FIRST time
+// GET /research/desk/playbook's already-shipped (J-01/J-02) shapes render anywhere in the UI.
+// Rendered as its OWN, self-contained section BELOW every shipped /desk section (Blueprint's own
+// pre-planned placement) -- it owns its own session-date input (blank = the most recent RECORDED
+// session, never "today") and its own compute trigger/poll/cancel trio, entirely independent of
+// the screen history's displayed snapshot and NOT wired into the refresh chain above. A signal's
+// own `forward` block is measured through the identical `desk_forward._measure_from` call the
+// forward rail's own touches/anchors are measured through, so its shape is byte-identical to
+// `DeskForwardTouch` by construction -- this section reuses `ForwardTouchTable`/
+// `ForwardTouchMeasureCells`/`ForwardAvgCellView` VERBATIM for it rather than re-declaring a
+// lookalike renderer, which is also what keeps every `touchRow.*`/`touchValue.*`/`avgCell.*`
+// price-arithmetic guard binding covering this section's forward cells with zero new bindings to
+// introduce for them. -------------------------------------------------------------------------------
+
+const PLAYBOOK_LEGACY_ABSENCE = "measurement not recorded in this record";
+
+function playbookSetupLabel(setupId: string): string {
+  if (setupId === "open_high_break") return "Open-High Break";
+  if (setupId === "open_low_break") return "Open-Low Break";
+  return setupId;
+}
+
+function playbookHorizonLabels(record: DeskPlaybookRecord): string[] {
+  return record.parameters.rail_horizons_minutes.map(([label]) => label);
+}
+
+function playbookPoolKey(signal: DeskPlaybookSignal): string {
+  return `${signal.setup_id}:${signal.side}`;
+}
+
+// The signals table's own row identity -- (trigger_ts, symbol, setup_id) is unique within one
+// record even once a future detector (J-04) can fire more than once for the same symbol in a
+// session, since each firing has its own trigger_ts.
+function playbookSignalKey(signal: DeskPlaybookSignal): string {
+  return `${signal.trigger_ts}:${signal.symbol}:${signal.setup_id}`;
+}
+
+type PlaybookControlProps = {
+  compute: DeskPlaybookComputeSnapshot | null;
+  onTrigger: () => void;
+  triggering: boolean;
+  triggerError: string | null;
+  onCancel: () => void;
+  cancelRequested: boolean;
+  cancelError: string | null;
+  sessionDate: string | null;
+};
+
+// Mirrors `DeskForwardComputeControl` in shape, adapted to `desk_playbook_compute.py`'s own
+// snapshot fields (`status`/`session_date`/`signals_done`/`signals_total`/`error` -- NOT the
+// forward manager's `state`/`progress.rows_*` shape, a genuinely different served contract).
+function DeskPlaybookComputeControl({
+  compute,
+  onTrigger,
+  triggering,
+  triggerError,
+  onCancel,
+  cancelRequested,
+  cancelError,
+  sessionDate,
+}: PlaybookControlProps) {
+  const isRunning = compute?.status === "running" || compute?.status === "cancelling";
+  const isError = compute?.status === "error";
+  const buttonLabel = isRunning ? "Computing…" : isError ? "Retry Run Playbook" : "Run Playbook";
+  return (
+    <div className="flex flex-col items-center gap-1">
+      {isError && compute?.error && (
+        <p data-testid="desk-playbook-compute-error" className="text-xs text-red-300">
+          {compute.error}
+        </p>
+      )}
+      {triggerError && (
+        <p data-testid="desk-playbook-compute-trigger-error" className="text-xs text-red-300">
+          {triggerError}
+        </p>
+      )}
+      {compute?.status === "done" && (
+        <p data-testid="desk-playbook-compute-outcome" className="text-xs text-slate-500">
+          Playbook run complete for {compute.session_date}.
+        </p>
+      )}
+      <button
+        type="button"
+        data-testid="desk-playbook-compute-button"
+        onClick={onTrigger}
+        disabled={triggering || isRunning || sessionDate === null}
+        className={PRIMARY_BUTTON_CLASS}
+      >
+        {buttonLabel}
+      </button>
+      {isRunning && (
+        <div data-testid="desk-playbook-compute-running" className="mt-1 flex flex-col items-center gap-1">
+          <p data-testid="desk-playbook-compute-progress" className="text-xs text-amber-200/70">
+            <span
+              aria-hidden="true"
+              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
+            />
+            {compute.signals_done} / {compute.signals_total} member(s) walked
+          </p>
+          <button
+            type="button"
+            data-testid="desk-playbook-compute-cancel"
+            onClick={onCancel}
+            disabled={cancelRequested || compute?.status === "cancelling"}
+            className={CANCEL_BUTTON_CLASS}
+          >
+            {cancelRequested || compute?.status === "cancelling"
+              ? "Cancelling — finishing the current member…"
+              : "Cancel"}
+          </button>
+          {cancelError && (
+            <p data-testid="desk-playbook-compute-cancel-error" className="text-xs text-red-300">
+              {cancelError}
+            </p>
+          )}
+        </div>
+      )}
+    </div>
+  );
+}
+
+// One signal's forward measurement, rendered through the SAME touch-table renderer the Forward
+// Returns panel already uses. `forward` is absent on a `payload_version` 1 (pre-measurement)
+// record's signal -- the legacy-absence literal, never blank or a fabricated value.
+function PlaybookSignalForward({ signal, labels }: { signal: DeskPlaybookSignal; labels: string[] }) {
+  if (signal.forward === undefined) {
+    return (
+      <p data-testid="desk-playbook-signal-forward-absent" className="text-xs text-amber-200/70">
+        {PLAYBOOK_LEGACY_ABSENCE}
+      </p>
+    );
+  }
+  return (
+    <ForwardTouchTable
+      touches={[signal.forward]}
+      labels={labels}
+      testid="desk-playbook-signal-forward-table"
+    />
+  );
+}
+
+function PlaybookInvalidationBreachedNote({
+  signal,
+  labels,
+}: {
+  signal: DeskPlaybookSignal;
+  labels: string[];
+}) {
+  const breached = signal.invalidation_breached;
+  if (breached === undefined) {
+    return (
+      <p data-testid="desk-playbook-signal-breach-absent" className="text-xs text-amber-200/70">
+        {PLAYBOOK_LEGACY_ABSENCE}
+      </p>
+    );
+  }
+  const marks = [...labels, "to_close"].map(
+    (label) => `${label}: ${breached[label] === true ? "breached" : "not breached"}`,
+  );
+  return (
+    <p data-testid="desk-playbook-signal-breach" className="text-xs text-slate-400">
+      {marks.join(" · ")}
+      {breached.first_breach_minutes !== null &&
+        ` · first breach at ${breached.first_breach_minutes} min`}
+    </p>
+  );
+}
+
+function PlaybookSignalDetail({
+  record,
+  signal,
+  labels,
+}: {
+  record: DeskPlaybookRecord;
+  signal: DeskPlaybookSignal;
+  labels: string[];
+}) {
+  const { geometry, volume, market, disclosures } = signal;
+  const poolKey = playbookPoolKey(signal);
+  return (
+    <div
+      data-testid="desk-playbook-signal-detail"
+      className="rounded border border-slate-800 bg-slate-900/40 px-3 py-2"
+    >
+      <p className="text-xs text-slate-400">
+        <span className="font-mono text-slate-200">{signal.symbol}</span>{" "}
+        <span className={CHIP_CLASS}>{playbookSetupLabel(signal.setup_id)}</span>{" "}
+        <span className={CHIP_CLASS}>{signal.side}</span> trigger{" "}
+        <span className="font-mono" title={String(signal.trigger_price)}>
+          {fmt(signal.trigger_price)}
+        </span>{" "}
+        at {formatTimeET(signal.trigger_ts)} ET · entry{" "}
+        <span className="font-mono">{fmt(signal.entry)}</span> ({signal.entry_kind}) · invalidation{" "}
+        <span className="font-mono" title={String(signal.invalidation_price)}>
+          {fmt(signal.invalidation_price)}
+        </span>
+      </p>
+      <p className="mt-1 text-[11px] text-slate-500">
+        opening range {fmt(geometry.or_low)}–{fmt(geometry.or_high)} ({geometry.opening_range_basis}{" "}
+        basis, {geometry.or_bars_used} bars) · width {fmt(geometry.or_width_mbr)} MBR · broke at
+        slot {geometry.slots_to_break}
+        {geometry.open_vs_prior_close_pct !== null &&
+          ` · open vs prior close ${fmt(geometry.open_vs_prior_close_pct)}%`}
+      </p>
+      <p className="mt-1 text-[11px] text-slate-500">
+        volume: {volume.spike_into_trigger_verdict}
+        {volume.rvol_trigger_bar !== null && ` · trigger RVOL ${fmt(volume.rvol_trigger_bar)}`}
+        {volume.approach_rvol_max !== null && ` · approach RVOL max ${fmt(volume.approach_rvol_max)}`}
+        {volume.spiky_approach && " · spiky approach into the trigger"}
+      </p>
+      <p className="mt-1 text-[11px] text-slate-500">
+        market (SPY): {market.direction ?? "unavailable"}
+        {market.market_move_mbr !== null && ` · move ${fmt(market.market_move_mbr)} MBR`}
+        {market.relative_strength_strong && " · relative strength strong"}
+        {market.reason !== null && ` · ${market.reason}`}
+      </p>
+      <p className="mt-1 text-[11px] text-slate-500">
+        {disclosures.gapped_beyond_chase && "gapped beyond chase · "}
+        {disclosures.attempt_count} approach attempt(s) · {disclosures.bars_to_close} bar(s) to
+        close
+        {disclosures.euphoria_recent && " · euphoria recent"}
+        {disclosures.capitulation_recent && " · capitulation recent"}
+      </p>
+      {signal.principles.length > 0 && (
+        <p className="mt-1 text-[11px] text-slate-500">principles: {signal.principles.join(", ")}</p>
+      )}
+      <div className="mt-2">
+        <p className="mb-1 text-[11px] font-medium text-slate-500">forward measurement</p>
+        <PlaybookSignalForward signal={signal} labels={labels} />
+      </div>
+      <div className="mt-2">
+        <p className="mb-1 text-[11px] font-medium text-slate-500">invalidation disclosure</p>
+        <PlaybookInvalidationBreachedNote signal={signal} labels={labels} />
+      </div>
+      <p data-testid="desk-playbook-signal-baseline-note" className="mt-2 text-[11px] text-slate-500">
+        {signal.forward === undefined
+          ? PLAYBOOK_LEGACY_ABSENCE
+          : `baseline: ${(record.baseline_anchors[poolKey] ?? []).length} anchor(s) recorded for ` +
+            `the ${poolKey} pool — see the summary below`}
+      </p>
+    </div>
+  );
+}
+
+function PlaybookSignalRow({
+  signal,
+  selected,
+  onSelect,
+}: {
+  signal: DeskPlaybookSignal;
+  selected: boolean;
+  onSelect: () => void;
+}) {
+  return (
+    <tr
+      data-testid="desk-playbook-signal-row"
+      onClick={onSelect}
+      aria-selected={selected}
+      className={`cursor-pointer border-t border-slate-800/60 transition-colors hover:bg-slate-800/40 ${
+        selected ? "bg-slate-800/60" : ""
+      }`}
+    >
+      <td className={ROW_BADGE_CELL} data-testid="desk-playbook-signal-symbol">
+        <span className="font-mono text-xs text-slate-200">{signal.symbol}</span>
+      </td>
+      <td className={ROW_BADGE_CELL} data-testid="desk-playbook-signal-setup">
+        <span className={CHIP_CLASS}>{playbookSetupLabel(signal.setup_id)}</span>
+      </td>
+      <td className={ROW_BADGE_CELL} data-testid="desk-playbook-signal-side">
+        <span className={CHIP_CLASS}>{signal.side}</span>
+      </td>
+      <td className={ROW_LABEL_CELL} title={`${signal.trigger_ts} (raw UTC record)`}>
+        {formatTimeET(signal.trigger_ts)}
+      </td>
+      <td className={ROW_NUMERIC_CELL} title={String(signal.trigger_price)}>
+        {fmt(signal.trigger_price)}
+      </td>
+      <td className={ROW_NUMERIC_CELL} title={String(signal.invalidation_price)}>
+        {fmt(signal.invalidation_price)}
+      </td>
+      <td className={ROW_LABEL_CELL}>{signal.entry_kind}</td>
+    </tr>
+  );
+}
+
+function PlaybookSignalsTable({
+  record,
+  labels,
+  selectedSignalKey,
+  onSelectSignal,
+}: {
+  record: DeskPlaybookRecord;
+  labels: string[];
+  selectedSignalKey: string | null;
+  onSelectSignal: (key: string | null) => void;
+}) {
+  if (record.signals.length === 0) {
+    return (
+      <EmptyState testid="desk-playbook-signals-empty" title="No signals fired in this session." />
+    );
+  }
+  return (
+    <div
+      data-testid="desk-playbook-table-scroll"
+      className="max-h-[26rem] overflow-x-auto overflow-y-auto rounded border border-slate-800"
+    >
+      <table data-testid="desk-playbook-table" className="w-full border-collapse">
+        <thead className="sticky top-0 z-10 bg-slate-900">
+          <tr>
+            <th className={ROW_HEADER_CELL_LEFT}>symbol</th>
+            <th className={ROW_HEADER_CELL_LEFT}>setup</th>
+            <th className={ROW_HEADER_CELL_LEFT}>side</th>
+            <th className={ROW_HEADER_CELL_LEFT}>trigger (ET)</th>
+            <th className={ROW_HEADER_CELL}>trigger price</th>
+            <th className={ROW_HEADER_CELL}>invalidation price</th>
+            <th className={ROW_HEADER_CELL_LEFT}>entry</th>
+          </tr>
+        </thead>
+        <tbody>
+          {/* rows render in the SAME order the record itself serves them (trigger ts, symbol) —
+              never sorted, reversed, or re-sliced client-side. */}
+          {record.signals.map((signal) => {
... [diff_bound] apps/frontend/app/desk/page.tsx: 571 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 7213452..fb31950 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -17,6 +17,9 @@ import type {
   DeskForwardPinsResult,
   DeskForwardReadResult,
   DeskForwardRunsListResult,
+  DeskPlaybookComputeSnapshot,
+  DeskPlaybookReadResult,
+  DeskPlaybookRunsListResult,
   DeskScreenPinsResult,
   DeskScreenRunsListResult,
   DeskScreenSnapshot,
@@ -1715,3 +1718,137 @@ export async function cancelDeskForwardCompute(): Promise<{ ok: boolean; error?:
     return { ok: false, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// --- The Playbook (Era B2, J-01/J-02/J-03) -- goal-playbook-iter-3: the FIRST UI callers of these
+// already-shipped endpoints. Mirrors the forward-compute trio above byte-for-byte in shape. --------
+
+// GET /research/desk/playbook(?date=|?id=) — the newest recorded playbook for a session date, or
+// the exact record under one id (the `fetchDeskScreenByDate`/`fetchDeskScreenById` convention,
+// combined into ONE function since the backend route itself takes either, never both — the
+// `desk_routes.py` 422 on both). Exactly one of `params.date`/`params.id` is expected; passing
+// neither would read the route's bulk `{playbooks, latest, integrity_errors}` shape instead, which
+// this function does not serve (no caller on this page needs it).
+export async function fetchDeskPlaybook(params: {
+  date?: string;
+  id?: string;
+}): Promise<{ ok: boolean; data: DeskPlaybookReadResult | null; error?: string }> {
+  try {
+    const query =
+      params.id !== undefined
+        ? `id=${encodeURIComponent(params.id)}`
+        : `date=${encodeURIComponent(params.date ?? "")}`;
+    const res = await fetch(`${API_BASE}/research/desk/playbook?${query}`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskPlaybookReadResult };
+    }
+    let error = "The playbook record could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// POST /research/desk/playbook/compute — start (or, while one is already running, observe) the
+// single-flight playbook compute job for one session date. Mirrors `triggerDeskForwardCompute`'s
+// exact shape; the backend's own 422 (a non-session date) `detail` is surfaced VERBATIM, never a
+// client-fabricated message.
+export async function triggerDeskPlaybookCompute(sessionDate: string): Promise<{
+  ok: boolean;
+  data?: { started: boolean; compute: DeskPlaybookComputeSnapshot };
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/playbook/compute`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify({ session_date: sessionDate }),
+    });
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data };
+    }
+    let error = "The playbook compute could not be started.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/desk/playbook/compute — the playbook compute job's current/last snapshot, served
+// VERBATIM. Mirrors `fetchDeskForwardCompute`: `ok:false, data:null` on any failure so a poll
+// tick's caller keeps the last known view — never fabricates a snapshot.
+export async function fetchDeskPlaybookCompute(): Promise<{
+  ok: boolean;
+  data: DeskPlaybookComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/playbook/compute`);
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as DeskPlaybookComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/desk/playbook/compute/cancel — cancel the in-flight playbook compute job. Mirrors
+// `cancelDeskForwardCompute`; the backend's 409 (idle) `detail` is surfaced verbatim.
+export async function cancelDeskPlaybookCompute(): Promise<{ ok: boolean; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/playbook/compute/cancel`, {
+      method: "POST",
+    });
+    if (res.ok) return { ok: true };
+    let error = "The playbook compute could not be cancelled.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/desk/playbook/runs(?session_date=) — the durable, append-only PLAYBOOK run log,
+// served VERBATIM. Mirrors `fetchDeskForwardRuns`'s exact `{ok, data, error}` shape. An honest-
+// empty result is a valid `ok: true` outcome: no playbook compute for this session has ever
+// reached a LOGGED terminal state (a cancelled run leaves no row at all — `desk_playbook_log.py`'s
+// own terminal-excludes-cancelled contract).
+export async function fetchDeskPlaybookRuns(sessionDate?: string): Promise<{
+  ok: boolean;
+  data: DeskPlaybookRunsListResult | null;
+  error?: string;
+}> {
+  try {
+    const query = sessionDate !== undefined ? `?session_date=${encodeURIComponent(sessionDate)}` : "";
+    const res = await fetch(`${API_BASE}/research/desk/playbook/runs${query}`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskPlaybookRunsListResult };
+    }
+    let error = "The playbook run history could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 34dd5a1..d10da5c 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1469,6 +1469,173 @@ export interface DeskForwardComputeSnapshot {
   progress: { rows_total: number; rows_done: number; current: string | null };
 }
 
+// --- The Playbook (Era B2, J-01/J-02/J-03) -- GET /research/desk/playbook(?date=|?id=) + its
+// compute trio + its durable run ledger. Every field is `desk_playbook.py`'s/
+// `desk_playbook_compute.py`'s/`desk_playbook_log.py`'s own served shape VERBATIM; nothing here is
+// ever derived client-side. A signal's own `forward` block reuses `DeskForwardTouch` /
+// `DeskForwardHorizonMeasure` VERBATIM (not re-declared as a lookalike): `_measure_signal` measures
+// every playbook signal through the SAME `desk_forward._measure_from` the forward rail's own
+// touches/anchors are measured through, so the shape is byte-identical by construction. ------------
+
+export interface DeskPlaybookGeometry {
+  or_high: number;
+  or_low: number;
+  or_width_mbr: number;
+  or_bars_used: number;
+  opening_range_basis: "1m" | "5m";
+  slots_to_break: number;
+  open_vs_prior_close_pct: number | null;
+}
+
+export interface DeskPlaybookVolume {
+  rvol_trigger_bar: number | null;
+  approach_rvol_max: number | null;
+  spike_into_trigger_verdict: "exhausted_spike" | "constructive" | "neutral";
+  spiky_approach: boolean;
+}
+
+export interface DeskPlaybookMarket {
+  direction: "supportive" | "against" | "neutral" | null;
+  market_move_mbr: number | null;
+  book_would_skip_market: boolean;
+  relative_strength_strong: boolean;
+  source: "SPY";
+  reason: string | null;
+}
+
+export interface DeskPlaybookDisclosures {
+  gapped_beyond_chase: boolean;
+  session_bar_count: number;
+  attempt_count: number;
+  bars_to_close: number;
+  concurrent_signals: string[];
+  euphoria_recent: boolean;
+  capitulation_recent: boolean;
+}
+
+// `_invalidation_breached`'s own flat shape: one boolean per rail horizon label plus `to_close`,
+// and the ONE session-wide `first_breach_minutes` fact every horizon leaf reads (never re-derived
+// per horizon). The index signature covers the per-horizon-label keys (`"1m"`/`"5m"`/`"1h"`/`"4h"`),
+// which vary with the record's own `parameters.rail_horizons_minutes` rather than a hardcoded set.
+export interface DeskPlaybookInvalidationBreached {
+  to_close: boolean;
+  first_breach_minutes: number | null;
+  [horizonLabel: string]: boolean | number | null;
+}
+
+export interface DeskPlaybookSignal {
+  symbol: string;
+  setup_id: string;
+  side: "long" | "short";
+  trigger_ts: string;
+  trigger_price: number;
+  entry: number;
+  entry_kind: "level" | "gap_open";
+  price_low: number;
+  price_high: number;
+  invalidation_price: number;
+  geometry: DeskPlaybookGeometry;
+  volume: DeskPlaybookVolume;
+  market: DeskPlaybookMarket;
+  principles: string[];
+  disclosures: DeskPlaybookDisclosures;
+  // OPTIONAL: absent on a `payload_version` 1 (J-01-era, pre-measurement) record's signal -- the
+  // panel renders the literal "measurement not recorded in this record" string for these, never a
+  // blank or a fabricated value.
+  forward?: DeskForwardTouch;
+  invalidation_breached?: DeskPlaybookInvalidationBreached;
+}
+
+export interface DeskPlaybookAbsence {
+  symbol: string;
+  reason: string;
+}
+
+export interface DeskPlaybookDiagnostic {
+  symbol: string;
+  diagnostic: string;
+  at_utc: string;
+}
+
+// One (setup_id:side) pool's per-measure-key summary cell -- the playbook's OWN `{signals,
+// baseline}` split (its record's own field name is `signals`, never `touches` -- the forward
+// rail's vocabulary for a wall's price touches has no playbook analogue).
+export interface DeskPlaybookSummaryCell {
+  signals: DeskForwardAvgCell;
+  baseline: DeskForwardAvgCell;
+}
+
+// The parameters blob embedded verbatim in every record AND hashed into `playbook_input_signature`
+// -- ~45 pre-registered constants (docs/playbook-detector-spec.md). Only the two fields the UI
+// actually reads are named; the rest stay reachable through the index signature rather than being
+// individually re-declared for no reader (nothing here is rendered as arithmetic in any case).
+export interface DeskPlaybookParameters {
+  setups: string[];
+  rail_horizons_minutes: [string, number][];
+  // The rail's own measure-key shape, echoed verbatim (DESK_FORWARD_MEASURE_KEYS) -- the ONE list
+  // every `summary`/`baseline_anchors` pool cell is keyed by; read here rather than re-derived
+  // client-side from `rail_horizons_minutes` (the `forwardMeasureKeys` precedent this section
+  // deliberately does NOT repeat, since the backend already serves the exact list it used).
+  signal_measures: string[];
+  [key: string]: unknown;
+}
+
+export interface DeskPlaybookRecord {
+  id: string;
+  session_date: string;
+  config_fingerprint: string;
+  playbook_input_signature: string;
+  payload_version: number;
+  parameters: DeskPlaybookParameters;
+  register: string;
+  recorded_at: string;
+  signals: DeskPlaybookSignal[];
+  absences: DeskPlaybookAbsence[];
+  diagnostics: DeskPlaybookDiagnostic[];
+  baseline_anchors: Record<string, DeskForwardTouch[]>;
+  summary: Record<string, Record<string, DeskPlaybookSummaryCell>>;
+  signals_beyond_cap: Record<string, number>;
+}
+
+// `GET /research/desk/playbook?date=` -- mirrors `DeskForwardReadResult`'s shape. `versions` is
+// OMITTED by the `?id=` read (the record it names either exists or it doesn't; "how many versions
+// this date has ever accumulated" is a `?date=`-only question) -- never fabricated as 0/1 there.
+export interface DeskPlaybookReadResult {
+  playbook: DeskPlaybookRecord | null;
+  versions?: number;
+}
+
+export interface DeskPlaybookComputeSnapshot {
+  status: "idle" | "running" | "cancelling" | "done" | "error";
+  session_date: string | null;
+  signals_done: number;
+  signals_total: number;
+  error: string | null;
+}
+
+// One terminal playbook-compute attempt, from the durable append-only run log -- survives the
+// compute manager's process-scoped snapshot (the `DeskForwardRun` precedent). Never `"cancelled"`:
+// a cancelled playbook run is never logged at all (`desk_playbook_log.py`'s own terminal-excludes-
+// cancelled contract).
+export interface DeskPlaybookRun {
+  run_id: string;
+  session_date: string;
+  config_fingerprint: string;
+  playbook_input_signature: string | null;
+  started_at: string;
+  finished_at: string;
+  outcome: "recorded" | "reused" | "refused_non_session" | "failed";
+  signals_recorded: number;
+  playbook_id: string | null;
+  error: string | null;
+}
+
+export interface DeskPlaybookRunsListResult {
+  runs: DeskPlaybookRun[];
+  latest: DeskPlaybookRun | null;
+  integrity_errors: { file: string; error: string }[];
+}
+
 // ONE registered universe membership snapshot's own served meta -- `UniverseStore.record`'s return
 // value verbatim (desk_universe.py's `meta` dict), which `POST /research/desk/universe/fetch`
 // serves under its `universe` key. Every field is the store's own; nothing here is derived. The
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-playbook/telemetry.jsonl   | 7 +++++++
 runs/goal-session-playbook/trace/trace.jsonl | 1 +
 2 files changed, 8 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
