# Iteration diff (bounded)

Files changed: 26. Shown in full: 17.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `diff --git areports/qa/goal-tape_to_profit-iter-6-evidence/J-01-verify.png breports/qa/goal-tape_to_profit-iter-6-evidence/J-01-verify.png` (4 diff lines)
- `diff --git areports/qa/goal-tape_to_profit-iter-6-evidence/J-05-verify.png breports/qa/goal-tape_to_profit-iter-6-evidence/J-05-verify.png` (4 diff lines)
- `diff --git areports/qa/goal-tape_to_profit-iter-6-evidence/J-08-verify.png breports/qa/goal-tape_to_profit-iter-6-evidence/J-08-verify.png` (4 diff lines)
- `diff --git areports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-ambient-check.png breports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-ambient-check.png` (4 diff lines)
- `diff --git areports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png breports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png` (4 diff lines)
- `diff --git areports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png breports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png` (4 diff lines)
- `diff --git areports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png breports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png` (4 diff lines)
- `diff --git areports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png breports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png` (4 diff lines)
- `diff --git aruns/goal-session-tape_to_profit/trace/.lock bruns/goal-session-tape_to_profit/trace/.lock` (3 diff lines)

```diff
diff --git a/runs/goal-session-tape_to_profit/telemetry.jsonl b/runs/goal-session-tape_to_profit/telemetry.jsonl
index 9fa63f3..23fd424 100644
--- a/runs/goal-session-tape_to_profit/telemetry.jsonl
+++ b/runs/goal-session-tape_to_profit/telemetry.jsonl
@@ -148,3 +148,17 @@
 {"reason":"AWAITING_PUMP","detected_at_step":"executor","ts":"2026-07-03T17:26:30Z","session_id":"tape_to_profit","iter":6,"event":"halt","cli":"claude"}
 {"final_verdict":"AWAITING_PUMP","total_iterations":6,"wall_time_seconds":3009,"quota_pause_count":0,"ts":"2026-07-03T17:26:30Z","session_id":"tape_to_profit","iter":6,"event":"session_end","cli":"claude"}
 {"mode":"resume","max_iterations":0,"stall_window":3,"auto_release":false,"ts":"2026-07-03T17:29:26Z","session_id":"tape_to_profit","iter":null,"event":"session_start","cli":"claude"}
+{"iter_name":"goal-tape_to_profit-iter-6","prior_verdict":"CONTINUE","prior_depth":"lean","snapshot_sha":"14a7ea463f4cc674e1721d253e897cd6178f2277","ts":"2026-07-03T17:29:27Z","session_id":"tape_to_profit","iter":6,"event":"iter_start","cli":"claude"}
+{"agent":"goal-decomposer","ts":"2026-07-03T17:29:27Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_start","cli":"claude"}
+{"agent":"goal-decomposer","exit_status":0,"duration_seconds":679,"retries":0,"ts":"2026-07-03T17:40:46Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_end","cli":"claude"}
+{"depth":"lean","target_journeys":"J-06","ts":"2026-07-03T17:40:46Z","session_id":"tape_to_profit","iter":6,"event":"iter_dispatch","cli":"claude"}
+{"iter_name":"goal-tape_to_profit-iter-6","depth":"lean","ts":"2026-07-03T17:40:47Z","session_id":"tape_to_profit","iter":6,"event":"iter_dispatch","cli":"claude"}
+{"agent":"developer","ts":"2026-07-03T17:40:47Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_start","cli":"claude"}
+{"agent":"developer","exit_status":0,"duration_seconds":2465,"retries":0,"ts":"2026-07-03T18:21:52Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_end","cli":"claude"}
+{"agent":"reviewer","ts":"2026-07-03T18:21:52Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_start","cli":"claude"}
+{"agent":"reviewer","exit_status":0,"duration_seconds":1085,"retries":0,"ts":"2026-07-03T18:39:57Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_end","cli":"claude"}
+{"agent":"browser-qa-agent","ts":"2026-07-03T18:40:26Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_start","cli":"claude"}
+{"agent":"browser-qa-agent","exit_status":0,"duration_seconds":697,"retries":0,"ts":"2026-07-03T18:52:03Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_end","cli":"claude"}
+{"agent":"coherence-auditor","ts":"2026-07-03T18:52:04Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_start","cli":"claude"}
+{"agent":"coherence-auditor","exit_status":0,"duration_seconds":278,"retries":0,"ts":"2026-07-03T18:56:42Z","session_id":"tape_to_profit","iter":6,"event":"agent_invocation_end","cli":"claude"}
+{"verdict":"COHERENCE-PASS","ts":"2026-07-03T18:56:42Z","session_id":"tape_to_profit","iter":6,"event":"coherence_audit","cli":"claude"}
diff --git aapps/backend/tests/test_profile_equivalence.py bapps/backend/tests/test_profile_equivalence.py
new file mode 100644
index 0000000..0b11013
--- /dev/null
+++ bapps/backend/tests/test_profile_equivalence.py
@@ -0,0 +1,327 @@
+"""Versioned indicator profiles (era-3 capability 2, J-06) — the config-owned registry plus the
+per-run overlay that lets a backtest select a candidate WITHOUT ever perturbing the frozen
+``default`` engine path (Data Contract row 33).
+
+Locked disciplines (each a J-06 acceptance clause or a coherence watchpoint):
+  * ONE registry source — ``Config.profile_definition`` / ``Config.profile_registry`` — feeds
+    BOTH ``GET /research/profiles`` (``app/research/profiles.py``) and the backtest route's
+    validation; there is no second allowlist anywhere.
+  * ``default`` resolves to the SAME ``Config`` object, unchanged (the strongest possible
+    byte-identical guarantee) — proven here against BOTH a literal pinned fingerprint and a
+    pinned replay of the committed PG SIP reference fixture.
+  * The ONE registered candidate is a genuinely ADDITIVE alternate threshold
+    (``warmup_min_events``, applied ONLY inside a per-run overlay ``Config`` via
+    ``dataclasses.replace`` — never a mutation of the shared ``CONFIG`` singleton) and is proven
+    to legitimately move classified output (a real ``tape_state`` flip, not merely a confidence
+    nudge) on the committed fixture — the iter-4 "make it fire" lesson.
+  * ``config_fingerprint`` folds the profile through the ONE existing hasher: the candidate's
+    distinct fingerprint comes from the overlaid, always-hashed ``warmup_min_events`` field, not
+    a second mechanism. The new registry-metadata field itself
+    (``profile_candidate_warmup_min_events``) is excluded so its mere existence never moves
+    ``default``'s fingerprint (pinned against the founding PnL-ledger row's committed value).
+  * No engine/cockpit path outside the backtest run param may ever resolve a profile (a
+    source-scan guard), and the ``/performance`` panel offers no selection control.
+"""
+
+from __future__ import annotations
+
+import dataclasses
+from pathlib import Path
+
+import pytest
+
+from app.config import (
+    CONFIG,
+    PROFILE_CANDIDATE_FASTER_WARMUP,
+    PROFILE_DEFAULT,
+    STRATEGY_V1_ID,
+)
+from app.research.backtests import BacktestJobManager, STATUS_DONE
+from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore, record_from_source
+from app.research.store import JournalStore
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+_PRIMARY = CONFIG.primary_window_label
+
+# The SAME founding windows the PnL ledger's founding row measures (config-owned — no literal
+# duplication of the dates/times anywhere in this file).
+TRAIN_WINDOW = CONFIG.pnl_founding_train_window
+HOLDOUT_WINDOW = CONFIG.pnl_founding_holdout_window
+
+
+def _register(store: DatasetStore, *, split: str, window: tuple[str, str]) -> dict:
+    return record_from_source(
+        store,
+        source_kind="reference",
+        source_id="PG_SIP_REFERENCE",
+        split=split,
+        start=window[0],
+        end=window[1],
+        config=CONFIG,
+    )
+
+
+# --- the registry itself: ONE source, config-owned, mirrors the strategy_definition pattern -------
+
+
+def test_profile_registry_lists_default_and_the_registered_candidate():
+    registry = CONFIG.profile_registry()
+    assert [p["id"] for p in registry] == [PROFILE_DEFAULT, PROFILE_CANDIDATE_FASTER_WARMUP]
+    default, candidate = registry
+    assert default == {"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}
+    assert candidate["frozen"] is False
+    assert candidate["is_default"] is False
+    assert candidate["based_on"] == PROFILE_DEFAULT
+    assert candidate["overrides"] == {"warmup_min_events": CONFIG.profile_candidate_warmup_min_events}
+
+
+def test_profile_definition_unknown_id_is_none():
+    assert CONFIG.profile_definition("nonexistent-profile") is None
+    assert CONFIG.profile_definition("") is None
+
+
+# --- resolution: default is IDENTITY; the candidate is a scoped, non-mutating overlay --------------
+
+
+def test_resolved_for_profile_default_is_the_same_object_unchanged():
+    # The strongest possible "byte-identical" guarantee: default resolves to the IDENTICAL Config
+    # object — no new instance, no copy, nothing that could ever drift from the live cockpit's
+    # own config (the frozen-default anti-goal).
+    assert CONFIG.resolved_for_profile(PROFILE_DEFAULT) is CONFIG
+
+
+def test_resolved_for_profile_candidate_overlays_only_its_declared_field():
+    resolved = CONFIG.resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP)
+    assert resolved is not CONFIG
+    assert resolved.warmup_min_events == CONFIG.profile_candidate_warmup_min_events
+    assert resolved.warmup_min_events != CONFIG.warmup_min_events
+    # Every OTHER field is untouched: putting warmup_min_events back reproduces CONFIG exactly
+    # (proves the overlay is scoped to ONLY its declared additive override).
+    assert dataclasses.replace(resolved, warmup_min_events=CONFIG.warmup_min_events) == CONFIG
+
+
+def test_resolved_for_profile_unknown_id_is_none():
+    assert CONFIG.resolved_for_profile("nonexistent-profile") is None
+
+
+# --- config_fingerprint: the ONE existing hasher, default untouched, candidate distinct -------------
+
+
+def test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field():
+    # Ground truth: the founding PnL-ledger row (reports/pnl/pnl-history.md, committed) was
+    # appended under THIS exact fingerprint. If this pin ever moves, that row (and every
+    # archived-era record) has silently drifted — the strongest guard against that.
+    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+
+
+def test_profile_candidate_field_is_serving_only_excluded_from_fingerprint():
+    # Registry metadata only (the value resolved_for_profile OVERLAYS onto the real
+    # warmup_min_events field) — never itself read by engine/classifier code, so its mere
+    # presence (at ANY value) must not move ANY existing fingerprint.
+    base = CONFIG.config_fingerprint()
+    bumped = dataclasses.replace(CONFIG, profile_candidate_warmup_min_events=999).config_fingerprint()
+    assert bumped == base
+
+
+def test_candidate_resolved_fingerprint_is_distinct_from_default():
+    resolved = CONFIG.resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP)
+    assert resolved.config_fingerprint() != CONFIG.config_fingerprint()
+    assert resolved.config_fingerprint() == "8c2c0fbf978228e3"
+
+
+def test_a_real_classifier_threshold_still_changes_the_fingerprint():
+    # The counter-test every fingerprint-exclusion claim in this file needs (the established
+    # test_backtests.py / test_datasets.py precedent).
+    assert dataclasses.replace(CONFIG, min_aggressive_buy_ratio=0.61).config_fingerprint() != (
+        CONFIG.config_fingerprint()
+    )
+
+
+# --- the pinned default-equivalence test (J-06 acceptance: byte-identical vs pre-profile) ----------
+
+
+def test_default_profile_replay_pins_exact_state_confidence_and_features(tmp_path):
+    """Replays the committed PG SIP reference fixture (the SAME windows the founding PnL row
+    measures) through the SAME production path the backtest runner uses
+    (``DatasetStore.replay``) under the profile-resolved ``default`` config, and asserts the
+    first AND last snapshot of each split match values pinned BEFORE this iteration's Config
+    change — proving the profile machinery is a pure additive overlay that never perturbs the
+    frozen default path."""
+    store = DatasetStore(tmp_path / "datasets")
+    train = _register(store, split=SPLIT_TRAIN, window=TRAIN_WINDOW)
+    holdout = _register(store, split=SPLIT_HOLDOUT, window=HOLDOUT_WINDOW)
+
+    run_config = CONFIG.resolved_for_profile(PROFILE_DEFAULT)
+    train_snaps = list(store.replay(train["id"], run_config))
+    holdout_snaps = list(store.replay(holdout["id"], run_config))
+
+    assert len(train_snaps) == 1321
+    assert len(holdout_snaps) == 1158
+
+    first, last = train_snaps[0], train_snaps[-1]
+    assert (first.tape_state, first.confidence, first.warm, first.event_count) == ("unclear", 0.1, False, 0)
+    assert (last.tape_state, last.confidence, last.warm, last.event_count) == (
+        "seller_control",
+        0.7562609836229536,
+        True,
+        376,
+    )
+    feat = last.features[_PRIMARY]
+    assert feat["buy_price_impact"] == pytest.approx(1.8245000000000573)
+    assert feat["sell_price_impact"] == pytest.approx(-1.9235000000000468)
+    assert feat["aggressive_buy_ratio"] == pytest.approx(0.3408139977177634)
+
+    first, last = holdout_snaps[0], holdout_snaps[-1]
+    assert (first.tape_state, first.confidence, first.warm, first.event_count) == ("unclear", 0.1, False, 0)
+    assert (last.tape_state, last.confidence, last.warm, last.event_count) == (
+        "buyer_control",
+        0.741002066460636,
+        True,
+        228,
+    )
+    feat = last.features[_PRIMARY]
+    assert feat["buy_price_impact"] == pytest.approx(2.452000000000055)
+    assert feat["sell_price_impact"] == pytest.approx(-2.1690000000000396)
+    assert feat["aggressive_buy_ratio"] == pytest.approx(0.6422896352473817)
+
+    # Double-run determinism (re-runs are byte-identical — the row-30 replay guarantee).
+    train_again = list(store.replay(train["id"], run_config))
+    assert [(s.tape_state, s.confidence) for s in train_snaps] == [
+        (s.tape_state, s.confidence) for s in train_again
+    ]
+
+
+def test_default_profile_replay_matches_plain_config_replay_exactly(tmp_path):
+    # A second, independent proof of "byte-identical": profile-resolving `default` and replaying
+    # under the bare CONFIG singleton (today's pre-J-06 call shape) yield IDENTICAL snapshot
+    # sequences, event for event — including the full features dict, not just state/confidence.
+    store = DatasetStore(tmp_path / "datasets")
+    train = _register(store, split=SPLIT_TRAIN, window=TRAIN_WINDOW)
+    plain = list(store.replay(train["id"], CONFIG))
+    via_profile = list(store.replay(train["id"], CONFIG.resolved_for_profile(PROFILE_DEFAULT)))
+    assert [(s.tape_state, s.confidence, s.features) for s in plain] == [
+        (s.tape_state, s.confidence, s.features) for s in via_profile
+    ]
+
+
+# --- the candidate-difference test: a REAL, legitimate, deterministic change -----------------------
+
+
+def test_candidate_profile_legitimately_differs_from_default_on_the_fixture(tmp_path):
+    """The 'make it fire' lesson (iter-4): the candidate must demonstrably and deterministically
+    alter at least one classified output on the committed fixture — never a vacuous no-op. Pinned
+    on BOTH founding windows: the candidate's lower warm-up floor calls its first directional
+    state genuinely EARLIER (a real ``tape_state`` flip, not merely a confidence nudge)."""
+    store = DatasetStore(tmp_path / "datasets")
+    train = _register(store, split=SPLIT_TRAIN, window=TRAIN_WINDOW)
+    holdout = _register(store, split=SPLIT_HOLDOUT, window=HOLDOUT_WINDOW)
+    candidate_config = CONFIG.resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP)
+
+    for dataset, expected_diff_count, expected_first_diff_idx, expected_state in (
+        (train, 13, 129, "seller_control"),
+        (holdout, 24, 136, "buyer_control"),
+    ):
+        default_snaps = list(store.replay(dataset["id"], CONFIG))
+        candidate_snaps = list(store.replay(dataset["id"], candidate_config))
+        diffs = [
+            i
+            for i, (a, b) in enumerate(zip(default_snaps, candidate_snaps))
+            if a.tape_state != b.tape_state
+        ]
+        assert len(diffs) == expected_diff_count
+        assert diffs[0] == expected_first_diff_idx
+        assert default_snaps[diffs[0]].tape_state == "unclear"
+        assert candidate_snaps[diffs[0]].tape_state == expected_state
+
+        # Determinism: an identical re-run of the CANDIDATE reproduces byte-identically.
+        rerun = list(store.replay(dataset["id"], candidate_config))
+        assert [(s.tape_state, s.confidence) for s in candidate_snaps] == [
+            (s.tape_state, s.confidence) for s in rerun
+        ]
+
+
+def test_candidate_backtest_report_differs_from_default_only_via_legitimate_behavior(tmp_path):
+    """The backtest-report-level leg: the SAME dataset backtested under ``default`` vs the
+    candidate profile. Train's armed trade happens to be unaffected on this fixture (the earlier
+    candidate transition does not move the SUSTAINED arm instant there); hold-out's DOES — a
+    materially different entry (timestamp, price, and thus R/$) — proving the difference is
+    real, not merely a metadata relabel. Both remain individually deterministic."""
+    store = DatasetStore(tmp_path / "datasets")
+    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    try:
+        train = _register(store, split=SPLIT_TRAIN, window=TRAIN_WINDOW)
+        holdout = _register(store, split=SPLIT_HOLDOUT, window=HOLDOUT_WINDOW)
+
+        def run(profile: str, dataset_id: str) -> dict:
+            jobs = BacktestJobManager(journal, CONFIG)
+            payload = jobs.create(
+                {"dataset_id": dataset_id, "strategy_id": STRATEGY_V1_ID, "profile": profile}
+            )
+            jobs.run_sync(payload["id"], dataset_store=store)
+            record = journal.get_backtest(payload["id"])
+            assert record.payload["status"] == STATUS_DONE, record.payload
+            return record.payload["result"]
+
+        default_train = run(PROFILE_DEFAULT, train["id"])
+        candidate_train = run(PROFILE_CANDIDATE_FASTER_WARMUP, train["id"])
+        default_holdout = run(PROFILE_DEFAULT, holdout["id"])
+        candidate_holdout = run(PROFILE_CANDIDATE_FASTER_WARMUP, holdout["id"])
+
+        # Every report is stamped with its own resolved profile + a correctly distinguishing
+        # fingerprint (the SAME hasher; the candidate's two reports share a fingerprint with each
+        # other and differ from every default report).
+        assert default_train["config_fingerprint"] == CONFIG.config_fingerprint()
+        assert default_holdout["config_fingerprint"] == CONFIG.config_fingerprint()
+        assert candidate_train["config_fingerprint"] == candidate_holdout["config_fingerprint"]
+        assert candidate_train["config_fingerprint"] != CONFIG.config_fingerprint()
+        assert candidate_train["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP
+        assert candidate_holdout["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP
+
+        # TRAIN: this fixture's sustained-arm instant happens not to move — trades stay identical
+        # (proving the candidate changes NOTHING it does not legitimately touch).
+        assert candidate_train["trades"] == default_train["trades"]
+
+        # HOLDOUT: the earlier directional call DOES move the sustained-arm instant — a
+        # materially different entry (never merely a relabel).
+        assert len(default_holdout["trades"]) == 1
+        assert len(candidate_holdout["trades"]) == 1
+        d_entry = default_holdout["trades"][0]["entry"]
+        c_entry = candidate_holdout["trades"][0]["entry"]
+        assert d_entry["logical_ts"] == pytest.approx(6.549988031387329)
+        assert c_entry["logical_ts"] == pytest.approx(6.278010845184326)
+        assert d_entry["logical_ts"] != c_entry["logical_ts"]
+        assert default_holdout["trades"][0]["net_r"] == pytest.approx(0.3334000000001356)
+        assert candidate_holdout["trades"][0]["net_r"] == pytest.approx(-0.1728000000000723)
+
+        # Determinism: an identical re-run of the candidate is byte-identical.
+        rerun_holdout = run(PROFILE_CANDIDATE_FASTER_WARMUP, holdout["id"])
+        assert rerun_holdout["trades"] == candidate_holdout["trades"]
+    finally:
+        journal.close()
+
+
+# --- the "no UI/engine path outside the backtest run param selects a profile" guard ----------------
+
+
+def test_resolved_for_profile_is_called_only_by_the_backtest_runner():
+    # The live cockpit / WatchManager / every archived-era engine path must NEVER resolve a
+    # profile — only a backtest run (its explicit ``profile`` request param) may ever apply the
+    # candidate overlay.
+    app_dir = BACKEND_DIR / "app"
+    callers = []
+    for path in sorted(app_dir.rglob("*.py")):
+        if path.name == "config.py":  # the method's own definition site
+            continue
+        if "resolved_for_profile" in path.read_text():
+            callers.append(path.relative_to(app_dir).as_posix())
+    assert callers == ["research/backtests.py"], callers
+
+
+def test_performance_page_offers_no_profile_selection_control():
+    # The read-only registry panel renders the profiles array verbatim (no selection affordance,
+    # the J-06 frontend constraint) — no <select>, and no hardcoded reference to the candidate id
+    # (it must render generically, from the API payload, never a client-side copy).
+    frontend_page = BACKEND_DIR.parent / "frontend" / "app" / "performance" / "page.tsx"
+    source = frontend_page.read_text()
+    assert "<select" not in source
+    assert PROFILE_CANDIDATE_FASTER_WARMUP not in source
diff --git adocs/handoffs/goal-tape_to_profit-iter-6-dev.md bdocs/handoffs/goal-tape_to_profit-iter-6-dev.md
new file mode 100644
index 0000000..db17efc
--- /dev/null
+++ bdocs/handoffs/goal-tape_to_profit-iter-6-dev.md
@@ -0,0 +1,230 @@
+# goal-tape_to_profit-iter-6 Dev Handoff
+
+**Phase:** goal-tape_to_profit-iter-6
+**Date:** 2026-07-03
+**Agent:** developer
+**Status:** complete
+
+## Resume posture — verify-and-complete (this session)
+
+Per the iter spec's explicit resume posture, HEAD was already at the iter-5 commit with a
+**complete, uncommitted J-06 implementation** in the working tree plus this exact handoff file
+already written (an earlier developer-agent invocation). This session made **zero code changes**
+— it independently re-verified every DoD item from scratch (fresh test run, fresh live server,
+fresh curl/API checks) rather than trusting the prior session's claims on inspection alone. Every
+check below was re-run independently in this session; none required a fix:
+
+- Read the full diff of all 6 changed files (`config.py`, `backtests.py`, `profiles.py`,
+  `routes.py`, `test_profiles_api.py`, `test_backtests_api.py`) plus the new
+  `test_profile_equivalence.py` (327 lines / 15 tests) end-to-end against the iter spec's IN
+  SCOPE bullets — confirmed line-by-line, not just the handoff's prose summary.
+- Ran the **full backend suite** fresh: **1004 passed, 1 skipped, 0 failed** (0 FAILED/ERROR via
+  `grep`), matching the claimed 988-baseline + 16 net-new. Confirmed via `-v` output that
+  `test_profile_equivalence.py` (15/15), the profile-related tests in `test_backtests_api.py` and
+  `test_profiles_api.py`, `test_no_execution_path.py` (4/4), and `test_observer_equivalence.py`
+  (7/7) all show clean dot-runs with no `F`.
+- Confirmed OUT-OF-SCOPE files are untouched: `git diff --stat` on `pnl_ledger.py`,
+  `pnl_baseline.py`, `pnl_history.py`, `reports/pnl/pnl-history.md`, `app/mcp/`, and
+  `apps/frontend/` all show **zero diff**; `pnl_min_sample_size` does not appear anywhere in the
+  `config.py` diff.
+- Read `apps/frontend/app/performance/page.tsx` directly (not just the source-scan test) and
+  confirmed it maps `profiles.profiles` generically with no hardcoded candidate id and no
+  `<select>` — the "zero frontend changes needed" claim holds structurally.
+- Confirmed the MCP↔REST byte-identical requirement for `/research/profiles` is already covered
+  by the pre-existing `test_get_endpoint_profiles_byte_identical_on_the_live_200` in
+  `test_mcp_server.py` (part of the green full-suite run); `app/mcp/` has zero diff so this
+  continues to hold.
+- **Live end-to-end verification against a freshly started server** (not just re-running pytest):
+  `GET /research/profiles` → both profiles, exact registry shape; re-registering the founding
+  TRAIN window correctly `409`s (already registered, immutable); `POST /research/backtests` under
+  `default` → queued+done with `config_fingerprint` `4d665603569b9dbf` at both the queued and
+  terminal stamp; under `candidate-faster-warmup` → queued+done with `8c2c0fbf978228e3` at both
+  stamps; under `nonexistent-profile` → `422` listing `['default', 'candidate-faster-warmup']`;
+  the TRAIN backtest's aggregates were byte-identical between profiles live (matches the pinned
+  "train trade doesn't move" claim); J-08 sentinel — `SIM-BUYER` → `buyer_control` @ 0.86 —
+  and `/`, `/journal`, `/studies`, `/performance` all `200` live.
+- **Restart test**: stopped all servers, restarted `scripts/dev.sh` a second time, confirmed no
+  port conflicts on `:8301`/`:3301`, and re-confirmed `GET /research/profiles` still served
+  correctly post-restart.
+- **Environment note (not a defect, worth recording for the next session):** `pyproject.toml`
+  sets `addopts = "-q"`; passing an additional `-q` on the command line compounds to `-qq`, which
+  in pytest 9.1.1 suppresses the final `N passed` summary line entirely (dots only, no count) even
+  though the run completes normally with exit code 0. The project's documented command
+  (`pytest tests/ -v`) does not hit this — `-v` cancels the config's `-q` back to normal verbosity
+  and the summary line prints correctly. Confirmed by direct byte inspection (`xxd`) of a `-qq`
+  run's output — the summary line is genuinely never written, not a display/capture truncation.
+- **Process-cleanup finding reproduced twice** (matches the prior session's note, so this is a
+  stable characteristic of `scripts/dev.sh`'s process tree, not a one-off): after
+  `pkill -f "next dev"` / `pkill -f "next-server"`, the `npm exec next dev` → `sh -c` → `node
+  next dev` → `next-server` chain (plus, after killing an active `uvicorn --reload`, its orphaned
+  `multiprocessing.resource_tracker`/`spawn_main` helpers reparented to `systemd --user`) survived
+  the pattern-based `pkill` both times and needed an explicit `kill -9 <pid>` by PID. `fuser -k -9
+  $PORT/tcp` (what `scripts/dev.sh` itself uses internally) reliably frees the **port** each time
+  — confirmed by the clean second `dev.sh` startup with no conflicts — so the automation pipeline
+  is unaffected; this only matters for an interactive agent's own manual `pkill`-by-name cleanup.
+  All processes this session started are confirmed stopped (`lsof -ti :8301 :3301` empty, full
+  `ps aux` sweep clean except one pre-existing, not-mine `python -m app.mcp` stdio process on
+  `pts/2` that predates this session and was never touched).
+
+No further action was needed — every DoD checklist item held on independent re-verification. The
+rest of this handoff (below) is the original implementation narrative, confirmed accurate.
+
+## What Was Built
+
+J-06 (versioned indicator profiles): a config-owned profile registry with the frozen `default`
+plus the era's first additive candidate, selectable only by an explicit backtest run.
+
+- **`Config.profile_definition(profile_id)`** (`app/config.py`) — the ONE registry lookup,
+  mirroring the existing `strategy_definition` pattern. `default` → `{id, frozen: True,
+  is_default: True}`. The registered candidate `candidate-faster-warmup` → `{id, frozen: False,
+  is_default: False, based_on: "default", overrides: {"warmup_min_events": 30}}` (self-documenting:
+  id, base, and the exact declared override — all read from config, no magic numbers). Unregistered
+  ids return `None`.
+- **`Config.profile_registry()`** — the full ordered list (`default` then the candidate); the
+  single source `GET /research/profiles` and the backtest route's validation both consult.
+- **`Config.resolved_for_profile(profile_id)`** — the per-run `Config` for a profile: `default`
+  returns the identical `CONFIG` object (not a copy — the strongest byte-identical guarantee);
+  the candidate returns a fresh `dataclasses.replace(self, warmup_min_events=30)` overlay, never
+  mutating the shared singleton. Unregistered → `None`.
+- **New `Config` field `profile_candidate_warmup_min_events: int = 30`** — the candidate's one
+  additive alternate-threshold value (lowers the classifier's cold-start floor from the default
+  40). Excluded from `config_fingerprint()` (it's registry metadata only, never itself read by
+  engine code — the OVERLAID `warmup_min_events` field, never excluded, is what actually moves the
+  fingerprint for a candidate-resolved config).
+- **`app/research/routes.py`** — retired the hardcoded `if body.profile != PROFILE_DEFAULT: 422`
+  in `create_backtest`; replaced with `registry.config.profile_definition(body.profile) is None`.
+  A registered candidate is now accepted (previously always 422); an unregistered profile still
+  422s, listing the known ids.
+- **`app/research/backtests.py`** — `BacktestRunner.run()` resolves `run_config =
+  self._config.resolved_for_profile(params["profile"])` and passes it ONLY into `_replay()` (the
+  fresh engine construction for that one run) and the persisted `result["config_fingerprint"]`.
+  Every OTHER computation in the module (fees, slippage, the strategy grammar, the null baseline)
+  still reads the manager's base `self._config` unconditionally — a profile is an
+  engine/classifier concern (Data Contract row 33), never a strategy-grammar one (row 34).
+  `BacktestJobManager.create()`'s queued-time stamp now resolves the same way, so the queued
+  payload's `config_fingerprint` already matches what the terminal report will carry.
+- **`app/research/profiles.py`** — rewritten to project `Config.profile_registry()` instead of a
+  hardcoded single-entry list; no longer imports from `.backtests` (both modules now depend only
+  on `config.py`, an even cleaner dependency graph than before).
+- **`PROFILE_DEFAULT`** moved from `app/research/backtests.py` to `app/config.py` (beside
+  `STRATEGY_V1_ID` — the same "id constant + Config-owned definition method" pattern for both).
+  `backtests.py` still re-exports it via `__all__`, so all 7 pre-existing importers
+  (`routes.py`, `pnl_baseline.py`, 4 test files) needed zero changes.
+
+### The candidate is empirically proven to fire (not a no-op)
+
+Per iter-5's lesson, I replayed the committed PG SIP reference fixture under both profiles before
+writing any pinned test values. Lowering `warmup_min_events` from 40 to 30 genuinely moves the
+first directional `tape_state` call earlier on **both** founding windows:
+
+- TRAIN (17:00:00–17:01:00Z): 13 snapshots flip state (first at index 129 vs default's 248) —
+  but the strategy's *sustained*-arm instant happens not to move, so the TRAIN backtest report is
+  byte-identical between profiles (proving the candidate changes nothing it doesn't legitimately
+  touch).
+- HOLDOUT (17:05:00–17:05:45Z): 24 snapshots flip state (first at index 136 vs default's 160) —
+  and this **does** move the sustained-arm instant: the candidate's holdout trade enters at
+  ts=6.278 vs default's ts=6.550, a different price, and flips net R from +0.333 to −0.173. A
+  real, materially different, deterministic outcome — not a metadata relabel.
+
+## Files Changed
+
+- `apps/backend/app/config.py` — `PROFILE_DEFAULT`/`PROFILE_CANDIDATE_FASTER_WARMUP` constants,
+  `profile_candidate_warmup_min_events` field (fingerprint-excluded), `profile_definition` /
+  `profile_registry` / `resolved_for_profile` methods.
+- `apps/backend/app/research/backtests.py` -- resolves the per-run profile config in `run()` and
+  `create()`; `_replay()` takes an explicit `config` param instead of reading `self._config`.
+- `apps/backend/app/research/profiles.py` -- projects `Config.profile_registry()` instead of a
+  hardcoded single entry.
+- `apps/backend/app/research/routes.py` -- registry-backed profile validation (was hardcoded);
+  updated docstrings/comments that described the pre-J-06 state.
+- `apps/backend/tests/test_profile_equivalence.py` (new) -- 15 tests: registry/resolution unit
+  tests, fingerprint pin + exclusion + counter-tests, the pinned default-equivalence test (byte-
+  identical vs pre-J-06 literal values on the committed fixture), the candidate-difference test
+  (engine-level state diffs + backtest-report-level trade diffs, both individually deterministic),
+  and the "no engine path outside the backtest runner resolves a profile" + "no frontend selection
+  control" source-scan guards.
+- `apps/backend/tests/test_profiles_api.py` -- updated the 2 tests whose names/docstrings
+  explicitly said "before J-06" to assert the new 2-profile registry shape; extended the
+  no-duplicate-literal source scan to cover the new candidate id.
+- `apps/backend/tests/test_backtests_api.py` -- renamed `..._until_the_profile_registry_ships` to
+  `test_unregistered_profile_is_422`; added `test_registered_candidate_profile_is_accepted_and_runs_to_done`.
+
+No frontend files changed — see "Frontend" below.
+
+## Tests Run
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (per `.claude/project-template.md`)
+
+Result: **1004 passed, 1 skipped** (0 failed). Baseline at iter-5 was 988 passed / 1 skipped; this
+iteration added 16 net new tests (15 in the new file + 1 net in `test_backtests_api.py`; the 2
+renamed tests in `test_profiles_api.py` are a 1:1 swap) and deleted none.
+
+Targeted re-run of the 3 changed/new files alone: 32/32 passed.
+
+Frontend: `cd apps/frontend && npm run build` — compiled clean, 7/7 static pages, `/performance`
+unchanged at 2.52 kB.
+
+## Frontend
+
+No frontend code was changed. The existing `/performance` registry panel (`app/performance/page.tsx`,
+shipped at J-05) already renders `profiles.profiles.map(...)` generically — `key={profile.id}`,
+reading only `id`/`frozen`/`is_default` — with no hardcoded assumption of exactly one row and no
+selection control. A registered candidate therefore appears automatically as a second `<li>`; this
+is exactly the "display consequence of row 33 gaining a candidate" the iter spec anticipated, not
+a new frontend feature. Verified live:
+
+- `npm run build` compiles clean (unchanged route sizes).
+- Started the dev backend + frontend via `scripts/dev.sh`; `curl :8301/research/profiles` returns
+  both profiles with the exact registry shape; `curl -o /dev/null -w '%{http_code}' :3301/performance`
+  → 200.
+- Confirmed via `tests/test_profile_equivalence.py::test_performance_page_offers_no_profile_selection_control`
+  (a source-scan: no `<select` element, no hardcoded reference to the candidate id in the page
+  source) that the "no selection affordance" constraint holds structurally, not just by inspection.
+
+No `docs/handoffs/goal-tape_to_profit-iter-6-frontend.md` was written since there is no frontend
+diff to hand off.
+
+## Pre-handoff Verification
+
+- **Service startup**: `bash scripts/dev.sh` — backend (`:8301`) and frontend (`:3301`) both came
+  up clean. Stopped (port-killed) and restarted via the same script a second time — no port
+  conflicts, both came back up on the identical ports, `/research/profiles` still served both
+  profiles correctly post-restart.
+- **Live end-to-end checks** (real running server, not mocked):
+  - `GET /research/profiles` → `default` + `candidate-faster-warmup`, exact shape matched the
+    pinned unit tests.
+  - `POST /research/backtests` with `profile: "nonexistent-profile"` → 422, listing the two known
+    ids.
+  - `POST /research/backtests` with `profile: "candidate-faster-warmup"` on the real founding
+    TRAIN dataset → ran to `done`; both the queued-time and terminal `config_fingerprint` read
+    `8c2c0fbf978228e3` (matching the pinned test value, and matching each other — no divergence
+    between the two stamps).
+  - The identical dataset under `profile: "default"` → `done`, `config_fingerprint`
+    `4d665603569b9dbf` on both stamps — byte-identical to the value pinned before this iteration
+    (verified against the committed `reports/pnl/pnl-history.md` founding row, untouched).
+  - `POST /watch/SIM-BUYER?mode=sim` → warms to `buyer_control` at confidence ~0.93 (J-08
+    sentinel, live-checked, not just via the suite).
+- **External integrations**: none added this iteration (no new adapters/scrapers/vendor calls —
+  the candidate reuses the existing committed reference-fixture path).
+- **Native dependency binaries**: none added.
+- **Process cleanup note** (not a defect, just a verification finding worth recording): after my
+  manual `pkill -f "next dev"` cleanup, a `next-server` grandchild process remained running,
+  invisible to a pattern that only matches "next dev" — I had to also `pkill -f "next-server"`.
+  `scripts/dev.sh` itself is unaffected: its own kill logic is port-based (`lsof -ti :$PORT` /
+  `fuser -k -9 $PORT/tcp`), which I proved correctly reclaims the port on a second invocation
+  (the restart test above came up clean). All server processes are stopped as of this handoff
+  (verified via `lsof -ti :8301 :3301` and a full `ps aux` scan, both empty).
+
+## Known Issues
+
+None. Every IN SCOPE item and DEFINITION OF DONE bullet in the iter spec is implemented and
+tested; OUT OF SCOPE items (the sweep harness, any ledger append, moving the champion pointer, any
+new MCP tool, `pnl_min_sample_size`/fixture changes, registering more than the one candidate) were
+left untouched — confirmed via `git diff --stat` showing zero diff on `pnl_ledger.py`,
+`pnl_baseline.py`, `pnl_history.py`, `reports/pnl/pnl-history.md`, and the `app/mcp/` package.
+
+One scope judgment call worth flagging for the reviewer: `BacktestJobManager.create()`'s
+queued-time `config_fingerprint` stamp was not explicitly called out in the iter spec's IN SCOPE
+list (only the terminal report's fingerprint was), but I updated it too so the two stamps in a
+persisted backtest record never diverge for a candidate run (see "What Was Built" above). This
+touches only `backtests.py`, which is already an IN SCOPE file for this iteration.
diff --git adocs/phases/goal-tape_to_profit-iter-6.md bdocs/phases/goal-tape_to_profit-iter-6.md
new file mode 100644
index 0000000..2a9e741
--- /dev/null
+++ bdocs/phases/goal-tape_to_profit-iter-6.md
@@ -0,0 +1,110 @@
+# Goal Iteration 6 — Versioned indicator profiles: register a candidate, keep `default` byte-identical (J-06)
+
+<!-- machine-readable goal-mode metadata -->
+## Goal Mode Metadata
+
+- **Session ID:** tape_to_profit
+- **Iteration:** 6
+- **Mode:** next
+- **Depth:** lean
+- **Frontend Present:** no (no frontend code change; the existing `/performance` panel renders the new registry row generically — see Frontend below)
+- **Target journeys:** J-06
+- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-08
+- **Anti-goal reminders (verbatim from `docs/goal.md`):**
+  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets, no recommendation to execute. The ONLY permitted "fill" is the offline backtester's simulated fill computed against recorded historical tape, clearly labeled simulated and sent nowhere. *(critical)*
+  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — and MUST never be presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
+  - **Default engine outputs are frozen.** Indicator evolution is additive and versioned only: candidate profiles may add feature keys or alternate thresholds, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, and no enhancement may mutate an archived-era behavior to pass. *(critical)*
+  - **No train-only promotion.** Nothing becomes the champion, a proposed journey, or a claimed improvement on the strength of train data alone: hold-out survival (net R AND net $, with the configured minimum n) is the only promotion gate; overfit results are labeled overfit. *(critical)*
+  - **No ML, no online tuning.** Candidate search is bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops inside the engine, no thresholds that move at runtime.
+  - **No fabricated data — honest failure states.** No synthesized trades, quotes, fills, datasets, or PnL to force a green journey; every failure mode (backend down, corrupt dataset, empty window, missing credentials, insufficient n) surfaces an explicit, distinct state. *(critical)*
+  - **Single source of truth.** Every canonical value in the Data Contract is computed once and read verbatim by every surface — REST, WebSocket, UI, markdown reports, and MCP. A second computation path or a diverging number across surfaces is a defect. *(critical)*
+  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
+  - **Persistence stays scoped.** SQLite holds research records (now including backtests and the PnL ledger); the dataset store holds explicitly recorded historical tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
+  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the default profile byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*
+
+## GOAL
+
+A researcher (and the MCP agent) can list a **candidate indicator profile** registered beside the frozen `default`, backtest the committed fixture dataset under **both** profiles, and see the two reports differ only where the candidate legitimately changes behavior — while the `default` read stays provably byte-identical (equivalence-pinned) and no surface offers a way to select a candidate for the live cockpit.
+
+## BACKGROUND
+
+Passing: J-01–J-05, J-08. Remaining: **J-06** (versioned profiles) and **J-07** (candidate sweep). Target selection follows the priority rubric: no journey regressed (rule 1), the last coherence verdict (`iter-5/coherence.md`) was **COHERENCE-PASS** so no consolidation is owed (rule 2), and J-06 is the head of the last dependency chain **J-06 → J-07** — the sweep has nothing to evaluate until a candidate profile exists, so J-06 is the unblocker (rule 3). J-06 and J-07 are the two remaining *risky* journeys (engine/config seam vs. promotion-gate harness); they are **never bundled** (rule 5) — J-07 is deferred to iter-7.
+
+**Depth = lean** (justified): backend-only with no frontend code change — one config-additive change + one route validation + one backtest-runner overlay + tests, the same machine-surface shape as J-02/J-03/J-04 which all shipped lean. It touches `config.py`'s fingerprint and the engine warm-up gate (the one risky seam this iteration), but that is a single risky journey travelling alone, guarded by a pinned byte-equivalence suite. The prior evaluator explicitly recommended lean (`iter-5/eval.md`) and the evaluator log emitted **no ESCALATE**, so `full` is not forced.
+
+**Resume posture — VERIFY-AND-COMPLETE, do NOT rebuild (lesson iter-5).** HEAD is the iter-5 commit (`9173a7d`) and the working tree already contains a complete, uncommitted J-06 implementation: `apps/backend/app/config.py` (candidate `candidate-faster-warmup` + `profile_definition`/`profile_registry`/`resolved_for_profile`), `apps/backend/app/research/backtests.py` (per-run resolved config + fingerprint stamping), `apps/backend/app/research/profiles.py`, `apps/backend/app/research/routes.py` (registry-backed 422 validation), and `apps/backend/tests/test_profile_equivalence.py` (new) plus updated `test_profiles_api.py` / `test_backtests_api.py`. The decomposer ran the 32 targeted J-06 tests — all pass. The developer's job is to **verify every DoD check independently and change only what a failed check requires** (as in iter-5's zero-churn resume), not to re-implement.
+
+**Failing-baseline framing (lesson iter-5):** `GET /research/profiles` already returned `200` at J-05 with a *zero-candidate* registry — that `200` was NOT J-06 credit. J-06 passes only when the candidate is registered, backtests run under it stamped with its profile id + distinct fingerprint, and the live cockpit is provably locked to `default`.
+
+## IN SCOPE
+
+### Backend
+- [ ] **Config-owned profile registry** (Data Contract row 33): `Config.profile_definition(id)` / `Config.profile_registry()` / `_PROFILE_IDS_IN_ORDER` register `default` (frozen, `is_default`) plus exactly ONE additive candidate `candidate-faster-warmup` — an alternate threshold value for the EXISTING `warmup_min_events` gate (40→30, `based_on: default`), value from config (no magic number). This is the ONE allowlist that BOTH `GET /research/profiles` and the backtest route consult — never a second allowlist.
+- [ ] **Registry-backed route validation:** `POST /research/backtests` validates `body.profile` against `Config.profile_definition` — a registered candidate is accepted and the job starts; an unregistered/unknown profile returns an honest `422` listing the registered profiles. (The old hardcoded `!= PROFILE_DEFAULT` refusal is already replaced in the working tree — verify it is gone, not restore it.)
+- [ ] **Per-run profile overlay, applied inside the fresh backtest engine only:** `Config.resolved_for_profile(id)` returns the identical `Config` object for `default` (strongest byte-identical guarantee) and a fresh `dataclasses.replace` overlay for a candidate — applied ONLY to that one replay, never mutating the shared `CONFIG` singleton. Fees, slippage, the strategy grammar, and the null baseline still read the base config (a profile is an engine/classifier concern — row 33 — never a strategy-grammar one — row 34).
+- [ ] **Fingerprint through the ONE existing hasher:** the candidate report carries a distinct `config_fingerprint` (`8c2c0fbf978228e3`) folded from its overlaid, always-hashed `warmup_min_events`; the `default` fingerprint stays the pinned `4d665603569b9dbf` (archived-era records + the founding PnL-ledger row's fingerprint unmoved). The serving-only registry-metadata field `profile_candidate_warmup_min_events` is excluded from the fingerprint so its mere presence moves nothing. Each report stamps its resolved `profile` id (row 31 already carries `profile`).
+- [ ] **Pinned default-equivalence test** (J-06's acceptance): replay fixed event streams under `default` and assert **byte-identical** state / confidence / features against pinned **pre-profile** outputs (`tests/test_profile_equivalence.py`). Keep the observer-equivalence suite (7/7) and the full engine suite green.
+- [ ] **Candidate-difference test:** a fixture-dataset backtest under the candidate differs from the default backtest **only** where the candidate legitimately changes behavior (a real `tape_state` flip and a materially different hold-out entry — candidate net R `-0.1728` vs default `+0.3334`, never a metadata relabel), and both are individually deterministic (byte-identical re-runs).
+
+### Frontend (if applicable)
+- None. The existing read-only `/performance` registry panel renders the profiles array generically (proven at J-05 and re-asserted by `test_performance_page_offers_no_profile_selection_control` — no `<select>`, no hardcoded candidate id), so the candidate row appears with **zero page changes**. Add no selection affordance, no new endpoint, no client-side computation.
+
+### New user-facing capability
+The research/MCP surface gains its first additive, versioned candidate indicator profile and the ability to backtest a dataset under `default` vs. the candidate — the mechanism J-07's hold-out sweep will later evaluate — while guaranteeing the live read is frozen.
+
+### New information displayed
+`GET /research/profiles` now lists `default` **and** `candidate-faster-warmup` (read-only registry). The `/performance` registry panel reflects it as a second read-only row (`based_on: default`, `overrides: {warmup_min_events}`). Candidate backtest reports are stamped with the candidate profile id and a distinct `config_fingerprint`.
+
+### New user actions
+`POST /research/backtests` now accepts `profile: candidate-faster-warmup` (previously `422`); MCP `get_endpoint("/research/profiles")` returns the candidate. No new UI control — profile selection is a backtest-run parameter only, never a cockpit/UI affordance.
+
+### UI surface changes
+None. The existing `/performance` read-only registry panel gains one data row via its generic renderer (a display consequence of row 33; no new control, no selection).
+
+### Product surface delta
+The product gains additive, versioned indicator evolution: a candidate lives beside the frozen `default`, selectable solely by backtest runs, with the live cockpit and every archived-era surface proven byte-identical on `default`.
+
+### Blueprint conformance
+No new surfaces. J-06 lives on its pre-declared **machine** home in the blueprint IA table (`GET /research/profiles` + MCP `get_endpoint`); the read-only display rides the already-registered `/performance` page (Performance nav section). No Information-Architecture or nav-skeleton change — no `blueprint.reapproval-requested`.
+
+### Data-contract additions
+**None.** J-06 realizes the *candidate side* of the already-registered **row 33** ("Indicator profiles + champion pointer … additive-only candidates; profile id folds into `config_fingerprint`", served ONLY by `GET /research/profiles`) and stamps backtests under **row 31** (which already carries `profile` id + `config_fingerprint` in provenance). No value gains a new computing module or a new serving endpoint, so `blueprint.md` needs no edit. Never introduce a second registrable-profile list or a second fingerprint path — read the one config-owned registry (`Config.profile_definition`) and the one `config_fingerprint()` hasher.
+
+## OUT OF SCOPE
+
+- The candidate sweep harness `python -m app.research.pnl_scan` and any promotion / champion-movement mechanics — that is **J-07** (risk isolation: the two remaining risky journeys are never bundled).
+- Appending any PnL-ledger row (no promotion happens in J-06; the ledger stays exactly the founding row) and moving the champion pointer (stays `v1/default`; only a hold-out survivor may move it — J-07).
+- Any change to the `default` profile's outputs, the live cockpit, or any archived-era behavior.
+- Any new MCP tool (`/research/profiles` is read via the existing `get_endpoint` allowlist; `app/mcp/__init__.py` stays untouched, docstring-at-most).
+- Any change to `pnl_min_sample_size` or the committed fixture datasets (the J-05 golden script pins "insufficient sample (n < 5)"; lesson iter-4 — the fixtures arm n=1 per split).
+- Any second candidate profile — exactly ONE candidate proves the mechanism (goal capability 2 / J-06 asks for "at least one"); keep the change set small.
+
+## DEFINITION OF DONE
+
+- [ ] **J-06 passes:** `GET /research/profiles` (and MCP `get_endpoint("/research/profiles")`) lists `default` + the candidate `candidate-faster-warmup`; the committed fixture-dataset backtest runs to `done` under **both** `default` and the candidate; `tests/test_profile_equivalence.py` (pinned default equivalence + candidate-fires difference + fingerprint pins + source-scan guards), `test_profiles_api.py`, and `test_backtests_api.py` are green — verified via browser-qa-agent (Chrome MCP in-page API legs) and the automated suite.
+- [ ] The `default`-profile backtest report on the fixture is **byte-identical** to the pre-J-06 default report and `config_fingerprint()` for `default` is **unchanged** (`4d665603569b9dbf` — archived-era records + founding PnL-ledger row unmoved); the candidate report carries a **distinct** fingerprint (`8c2c0fbf978228e3`) + its profile id.
+- [ ] An unknown/unregistered profile id is rejected with an honest `422` listing the registered profiles.
+- [ ] A source-scan test proves `resolved_for_profile` is called only by the backtest runner (`research/backtests.py`) — the live cockpit and every archived-era engine path are locked to `default`; `/performance` has no profile-selection control.
+- [ ] Required-still-passing **J-01, J-02, J-03, J-04, J-05, J-08 remain green** — J-01/J-05/J-08 via golden replay with an explicit per-journey result row (lesson iter-1); J-02/J-03/J-04 via the automated suite (lesson iter-2).
+- [ ] **No anti-goal violation:** default byte-identical (equivalence green); no UI path selects a candidate; no promotion, no ledger append, champion still `v1/default`; MCP read-only (`app/mcp/__init__.py` diff docstring-at-most); no execution path (`test_no_execution_path.py` green).
+- [ ] Unit tests pass; **no regressions** — full backend suite green with the new J-06 tests added and none deleted (≥ iter-5's 988-passed baseline).
+- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit-iter-6-dev.md` (verify-and-complete: state which checks were re-run independently and that no rebuild was needed, or list exactly what a failed check required).
+
+## TESTING REQUIREMENTS
+
+- **Browser** (demand an explicit result row per journey — lesson iter-1):
+  - **J-06** (own journey, machine-surface — no golden replay script exists, lesson iter-2): Chrome MCP in-page `fetch()` from a backend-origin page — `GET /research/profiles` shows `default` + candidate; `POST /research/backtests` under `default` → started/`done`; under `candidate-faster-warmup` → accepted/`done` (report stamped with the candidate profile id + distinct fingerprint); under an unknown profile → `422` honest refusal.
+  - **J-05** (golden script + in-page page-equals-API): `/performance` registry panel lists `default` + candidate, **read-only, NO selection control**; ledger + champion unchanged (still `v1/default`).
+  - **J-01** (golden nav script + MCP): `get_endpoint("/research/profiles")` JSON byte-identical to the REST payload; nav unchanged (4 links).
+  - **J-08** (golden regression script + suite): cockpit `/`, `/journal`, `/studies` intact; full backend suite green; observer-equivalence 7/7.
+- **Unit/integration:** registry lists `default` + candidate; route consults the registry (candidate accepted, unknown → `422`); `default` backtest byte-identical to pre-J-06 (pinned state/confidence/features); candidate backtest deterministic and differing only on the legitimate change; `config_fingerprint` — `default` unchanged (`4d665603569b9dbf`), candidate distinct (`8c2c0fbf978228e3`), registry-metadata field excluded while a real classifier threshold still moves the fingerprint; a source-scan test that `resolved_for_profile` is called only by the backtest runner and that no cockpit/`/performance` control selects a profile.
+- **Error cases:** unknown/unregistered profile id → `422` honest (lists registered profiles); `resolved_for_profile(default)` returns the identical `Config` object (never a drifting copy); an unregistered id → `None` (never a silent coercion to `default`); the frozen `default` cannot be mutated or re-defined; backend-down MCP → explicit tool error (unchanged).
+
+## NOTES
+
+- **Coherence watchpoints** (last verdict was PASS — keep it): (1) `config_fingerprint` folds the profile through the **one** existing `config_fingerprint()` hasher — the `default` fingerprint must not move (else archived records + the founding PnL row drift → J-08 fail + a never-pool honesty break); (2) **one** registry source (`Config.profile_definition`) feeds both `GET /research/profiles` and the backtest route's validation — no second profile allowlist; (3) `default` engine byte-identity via *overlay-only-inside-the-backtest-engine* — no engine default constant changes, no shared mutable config (the shared `CONFIG` singleton is never mutated); (4) `/research/profiles` stays the single serving endpoint and no Data-Contract row is added (row 33 already covers candidates; row 31 already carries the profile id + fingerprint); (5) no UI selection path; (6) `app/mcp/__init__.py` untouched — profiles reach MCP via the existing `get_endpoint`.
+- **Make the candidate fire on the fixture** (lesson iter-4): the committed fixture pair arms only n=1 per split, so the candidate's additive change (lower `warmup_min_events`) is calibrated to demonstrably and deterministically move at least one classified output on the fixture (a real `tape_state` flip earlier, and a materially different hold-out entry/R) — never a vacuous no-op. J-06's acceptance is byte-identity of `default` + a *real* legitimate difference for the candidate + determinism, NOT any sample-size gate (that is J-07). The candidate's hold-out net R turning negative (`-0.1728`) vs default's `+0.3334` is a legitimate measured difference under disclosed assumptions — NOT a promotion, an edge claim, or a profit claim.
+- **Machine-surface regression lane** (lesson iter-2): J-06 gets no golden replay script (`demo_runner.py` is goto/click/fill only, no POST); its durable regression lane is the backend suite, and browser verification of the API legs uses Chrome MCP in-page `fetch()`. J-02/J-03/J-04 likewise ride the suite; the browser replay lane carries J-01/J-05/J-08 golden scripts.
+- **Environment caution** (lesson iter-3): before diagnosing "flaky browser" / `net::ERR_INSUFFICIENT_RESOURCES` / sqlite `Disk quota exceeded`, run `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota; at planning time it was healthy (2.4G of 6.5G, 50%). If large-suite or browser lanes flake, point pytest `TMPDIR` + `--basetemp` off tmpfs to a root-filesystem dir (the decomposer's targeted J-06 run used `/home/dennis-chan/.cache/tapeology-pytest`).
+- **References:** evaluator next-step `runs/goal-session-tape_to_profit/iter-5/eval.md`; the registry + overlay + fingerprint live in `apps/backend/app/config.py`; registry serving side `apps/backend/app/research/profiles.py`; route validation + report stamping `apps/backend/app/research/routes.py` + `apps/backend/app/research/backtests.py`; the pinned equivalence + candidate-difference + source-scan tests in `apps/backend/tests/test_profile_equivalence.py`.
+- **After J-06:** J-07 (the candidate sweep harness `python -m app.research.pnl_scan`), whose promotion-gate tests must control the configured minimum-n both ways since the fixtures arm only n=1 per split (lesson iter-4).
diff --git areports/phase-goal-tape_to_profit-iter-6-demo-results.md breports/phase-goal-tape_to_profit-iter-6-demo-results.md
new file mode 100644
index 0000000..2d6c5a4
--- /dev/null
+++ breports/phase-goal-tape_to_profit-iter-6-demo-results.md
@@ -0,0 +1,4 @@
+# Demo Results — goal-tape_to_profit-iter-6
+
+**Demo Verdict:** SKIPPED
+**Reason:** Backend-only iteration (Frontend Present: no). No browser walkthrough was performed.
diff --git areports/phase-goal-tape_to_profit-iter-6-demo-script.md breports/phase-goal-tape_to_profit-iter-6-demo-script.md
new file mode 100644
index 0000000..8ecd0f6
--- /dev/null
+++ breports/phase-goal-tape_to_profit-iter-6-demo-script.md
@@ -0,0 +1,6 @@
+# Demo Script — goal-tape_to_profit-iter-6
+
+**Mode:** record
+**Status:** N/A — Backend-only iteration (Frontend Present: no)
+
+This iteration made no user-visible changes; there is nothing to demonstrate in a browser.
diff --git areports/phase-goal-tape_to_profit-iter-6-regression-replay-results.md breports/phase-goal-tape_to_profit-iter-6-regression-replay-results.md
new file mode 100644
index 0000000..3142ad8
--- /dev/null
+++ breports/phase-goal-tape_to_profit-iter-6-regression-replay-results.md
@@ -0,0 +1,27 @@
+# Regression Replay — goal-tape_to_profit-iter-6
+
+**Phase:** goal-tape_to_profit-iter-6
+**Date:** 2026-07-03
+**Written by:** demo_runner.py (deterministic replay)
+
+---
+
+**Browser QA Verdict:** PASS
+
+**Overall:** 3/3 journeys passed (0 skipped)
+
+---
+
+## Results Table
+
+| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
+|---------|------|------|----------|----------|--------|---------|----------|
+| UT-J-01 | A read-only MCP server exposes the product over the canonical API | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-01-verify.png |
+| UT-J-05 | The /performance page reports PnL per enhancement honestly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-05-verify.png |
+| UT-J-08 | The existing product is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-08-verify.png |
+
+## Environment
+
+- **Frontend URL:** http://localhost:3301
+- **Browser:** Chromium via Playwright (deterministic replay, verify)
+- **Test Date:** 2026-07-03
diff --git areports/phase-goal-tape_to_profit-iter-6-ui-test-results.llm.md breports/phase-goal-tape_to_profit-iter-6-ui-test-results.llm.md
new file mode 100644
index 0000000..d8d853d
--- /dev/null
+++ breports/phase-goal-tape_to_profit-iter-6-ui-test-results.llm.md
@@ -0,0 +1,125 @@
+# Goal Iteration 6 — UI/Browser Test Results
+
+**Phase:** goal-tape_to_profit-iter-6
+**Date:** 2026-07-03
+**Written by:** browser-qa-agent
+
+---
+
+**Browser QA Verdict:** PASS
+
+<!-- PASS: All smoke and happy-path tests pass. -->
+
+**Overall:** 4/4 tests passed (0 skipped)
+
+Scope this run (lean-mode dispatch): **J-02, J-03, J-04, J-06** — all four are backend/machine-surface
+journeys with no frontend UI (Frontend Present: no for iter-6; the `/performance` panel that
+renders the new profile row is J-05's concern and is explicitly out of scope this run, verified
+separately by golden replay along with J-01 and J-08). Verified via Chrome MCP **in-page
+`fetch()`** from a backend-origin page (`http://localhost:8301/docs`), per the iter-6 spec's
+"Machine-surface regression lane" note — `demo_runner.py`'s golden-replay format is
+goto/click/fill only and cannot express the POST-heavy flows these journeys require, so **no
+golden replay scripts were written** for J-02/J-03/J-04/J-06 this run (consistent with the spec's
+own guidance that their durable regression lane is the backend suite, not the replay lane).
+
+---
+
+## Results Table
+
+| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
+|---------|------|------|----------|----------|--------|---------|----------|
+| UT-J-02 | Historical tape datasets persist and replay byte-identically | regression | P1 | Record dataset (symbol/window/feed/checksum stored); re-tag attempt refused 409; list reflects it; watching a sim ticker writes no rows | Recorded new dataset (7th row), checksum+metadata stored; re-tag same content → 409 with honest re-tag message; list count 6→7, new row present verbatim; watch/unwatch SIM-BUYER left dataset count unchanged (7→7→7) | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png`, `UT-J-02-ambient-check.png` |
+| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | regression | P1 | POST starts job, polls to done; report has trades + net/gross R&$, win rate, max drawdown, n, null baseline, full provenance; identical re-run is byte-identical; no broker code | POST→`queued`→`done`; aggregates carry gross_r/net_r/gross_usd/net_usd/win_rate/max_drawdown_r/n; null_baseline present (seed 1729); provenance stamped (dataset id+checksum, strategy_id, profile, fingerprint); re-run produced a different backtest id with byte-identical trades/aggregates/null_baseline; both runs appear in the list; grep found no broker/order/paper-trading code (only a comment documenting the anti-goal) | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png` |
+| UT-J-04 | Every enhancement lands one honest row in the PnL ledger | regression | P1 | Ledger shows founding row (baseline null, train+holdout separate, n, provenance, timestamp); no update/delete path; markdown regen is a byte-level no-op; REST/markdown numbers match | Founding row present: train net_r -0.16000000000001136 (n=1, insufficient sample), holdout net_r 0.3334000000001356 (n=1, insufficient sample), full provenance + timestamp; DELETE/PUT/POST all → 405; `python -m app.research.pnl_history` regen produced byte-identical sha256 before/after (`git diff` empty); markdown numbers match REST exactly | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png` |
+| UT-J-06 | Indicator profiles are versioned; the default stays byte-identical | smoke | P1 | `/research/profiles` lists default+candidate; backtests under both profiles differ only legitimately; unknown profile → honest 422; default fingerprint unchanged, candidate fingerprint distinct | `GET /research/profiles` → `default` (frozen) + `candidate-faster-warmup` (based_on default, overrides `warmup_min_events:30`); champion still `v1`/`default`; default holdout backtest: fingerprint `4d665603569b9dbf`, net_r `+0.3334000000001356` (exact pinned match); candidate holdout backtest: fingerprint `8c2c0fbf978228e3`, net_r `-0.1728000000000723` (exact pinned match) — same setup/direction (`trend_continuation`/`long`), materially different outcome (win_rate 1.0→0.0); candidate re-run byte-identical (deterministic); unknown profile → 422 `"unknown profile 'nonexistent-profile-xyz' — the registered profiles are ['default', 'candidate-faster-warmup']"` | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png` |
+
+---
+
+## Passed Tests
+
+### UT-J-02 — Historical tape datasets persist and replay byte-identically
+**Verdict:** PASS
+**Evidence:** `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png`, `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-ambient-check.png`
+
+- `GET /research/datasets` before: 6 datasets (all with symbol, UTC window, feed, event_counts, checksum, split — pre-existing from prior iterations).
+- `POST /research/datasets` with a fresh, previously-unused fixture sub-window (`source_kind: reference`, `split: train`, `start: 2026-06-09T17:03:00Z`, `end: 2026-06-09T17:03:15Z`) → `200`, new dataset `cb493e80dd574a7eaaf904726698649a` (232 trades, 272 quotes, checksum `b00a6dc9...`) — proves the committed reference fixture records keyless.
+- Immediate re-POST of the **exact same window** under `split: holdout` (the re-tag attempt) → `409` with an honest, explicit message: *"this exact tape is already registered as dataset 'cb493e80dd574a7eaaf904726698649a' with split 'train' — split tags are frozen at registration, so re-tagging it 'holdout' is refused"*.
+- `GET /research/datasets` after: count 6→7, new row present verbatim (same id/checksum/metadata echoed back).
+- `GET /research/datasets/does-not-exist-xyz` → `404` (bonus check, honest not-found).
+- **No-ambient-recording check** (anti-goal "Persistence stays scoped"): `POST /watch/SIM-BUYER` → `200 watching`; waited 2.5s; `GET /tape/SIM-BUYER/state` → `200` (live stream, warming up); dataset count during watch stayed at 7; `DELETE /watch/SIM-BUYER` → `200`; dataset count after unwatch stayed at 7. Watching a sim ticker wrote **zero** dataset rows.
+- **Not independently re-verified live** (covered by the automated suite, not re-triggered here to avoid corrupting shared state): checksum-tamper → explicit integrity error; byte-identical replay of the stored dataset vs. the original source stream (an internal engine-level comparison with no REST surface to drive from the browser). Indirect evidence: J-03/J-06 below both show two independent backtest runs against the same dataset reproducing byte-identical trades/aggregates, which is only possible if the dataset replays deterministically.
+
+### UT-J-03 — Strategy grammar v1 backtests a dataset into a deterministic PnL report
+**Verdict:** PASS
+**Evidence:** `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png`
+
+- `POST /research/backtests` (`dataset_id: 9396fd58...`, `strategy_id: v1`, `profile: default`) → `200`, job created `queued`, polled to `done`.
+- Report `register`: *"simulated — assumed fees/slippage — not indicative of live results"*.
+- `aggregates` carries all required fields: `n`, `gross_r`, `net_r`, `gross_usd`, `net_usd`, `win_rate`, `max_drawdown_r` (values: n=1, gross_r=-0.05, net_r=-0.16000000000001136, gross_usd=-5, net_usd=-16.000000000001137, win_rate=0, max_drawdown_r=0.16000000000001136).
+- `null_baseline` present with recorded seed `1729` (seeded random-entry baseline beside the strategy result).
+- Full provenance stamped: dataset id + checksum, `strategy_id`, `profile`, `config_fingerprint` (`4d665603569b9dbf`).
+- Identical re-run (same dataset/strategy/profile) produced a **different** backtest id but **byte-identical** `trades`, `aggregates`, and `null_baseline` (string-compared) — determinism confirmed.
+- Both runs appear in `GET /research/backtests`.
+- Supplementary grep (`apps/backend/app`, excluding tests) for broker/order/paper-trading code: only one hit, a comment in `providers/adapters/alpaca.py` explicitly documenting the anti-goal ("integrates no execution/brokerage capability") — no actual broker/order/account code exists.
+
+### UT-J-04 — Every enhancement lands one honest row in the PnL ledger
+**Verdict:** PASS
+**Evidence:** `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png`
+
+- `GET /research/pnl/ledger` → `register` = simulated caveat string; `min_sample_size` = 5; 1 row (the founding baseline, no promotions yet — matches J-06's out-of-scope guarantee that no ledger row was appended this iteration).
+- Founding row: `enhancement_id: founding-baseline-strategy-v1-default`, `baseline: null` (no prior incumbent, never fabricated), `train: {net_r: -0.16000000000001136, net_usd: -16.000000000001137, n: 1, insufficient_sample: true}`, `holdout: {net_r: 0.3334000000001356, net_usd: 33.34000000001356, n: 1, insufficient_sample: true}` — train and holdout kept separate, never pooled; both correctly labeled "insufficient sample" since n=1 < min_sample_size=5.
+- Full provenance (strategy/profile/fingerprint + per-split backtest id, dataset id, dataset checksum) and `created_utc` timestamp present.
+- **No write surface:** `DELETE`, `PUT`, and `POST` to `/research/pnl/ledger` all → `405` (no handler exists — matches "no update or delete path").
+- Regenerated the markdown via `python -m app.research.pnl_history`: sha256 of `reports/pnl/pnl-history.md` identical before and after (`4ad09e96f4e2ba...`), `git diff --stat` empty — a byte-level no-op, confirming the markdown is a pure render.
+- Read the regenerated markdown directly: numbers match the REST payload exactly (train `-0.16000000000001136`/`-16.000000000001137`, holdout `0.3334000000001356`/`33.34000000001356`, fingerprint `4d665603569b9dbf`, same backtest/dataset/checksum ids), and the date is rendered `03-07-2026` (dd-MM-yyyy, per the foundation invariant).
+
+### UT-J-06 — Indicator profiles are versioned; the default stays byte-identical
+**Verdict:** PASS
+**Evidence:** `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png`
+
+- `GET /research/profiles` → `profiles: [{id: default, frozen: true, is_default: true}, {id: candidate-faster-warmup, frozen: false, is_default: false, based_on: default, overrides: {warmup_min_events: 30}}]`; `champion: {strategy_id: v1, profile: default}` — unmoved.
+- Ran the same fixture holdout dataset (`aa749b668553473294e7ca5a9caa69d6`) as a backtest under **both** profiles:
+  - `default` → `done`, `config_fingerprint: 4d665603569b9dbf` (the pinned, unchanged default fingerprint), `net_r: 0.3334000000001356` — this **exactly** matches the founding PnL-ledger row's holdout leg read independently in UT-J-04, i.e. an independent fresh run reproduces the archived-era number exactly.
+  - `candidate-faster-warmup` → `done`, `config_fingerprint: 8c2c0fbf978228e3` (distinct, pinned candidate fingerprint), `net_r: -0.1728000000000723`.
+  - Both trades share the same `setup_type` (`trend_continuation`) and `direction` (`long`) — the candidate's earlier warmup arms the same setup but the outcome flips from a clean winner (`win_rate: 1.0`) to a loss (`win_rate: 0.0`) — a real, legitimate behavioral difference, not a metadata relabel.
+  - Re-ran the candidate a second time: aggregates and per-trade summary byte-identical to the first candidate run (different backtest id) — individually deterministic.
+- Unknown profile: `POST /research/backtests` with `profile: nonexistent-profile-xyz` → `422`, `detail: "unknown profile 'nonexistent-profile-xyz' — the registered profiles are ['default', 'candidate-faster-warmup']"` — an honest refusal listing the registered profiles, never a silent fallback.
+- Supplementary source check: `grep -rn "resolved_for_profile(" app/` (excluding tests) shows exactly two call sites, both inside `app/research/backtests.py` (the backtest runner) plus the method's own definition in `config.py` — no cockpit/live/archived-era path calls it. Read `Config.resolved_for_profile`: `default` returns `self` unchanged (the identical object — the strongest byte-identical guarantee); a candidate returns a fresh `dataclasses.replace(self, **overrides)` (the shared `CONFIG` singleton is never mutated); an unregistered id returns `None` (never a silent default fallback).
+- **Not independently re-verified live** (covered by the automated suite): the full pinned-fixture equivalence assertion in `tests/test_profile_equivalence.py` (byte-identical state/confidence/features/history against a pre-profile golden snapshot) — no REST surface exposes that internal comparison for a browser check to drive; the fingerprint + net-R matches above are strong indirect evidence of the same guarantee.
+
+---
+
+## Failed Tests
+
+None.
+
+---
+
+## Skipped Tests
+
+None. Both the frontend precondition and Chrome MCP were available; all four in-scope journeys were exercised.
+
+**Note on MCP-tool cross-checks:** J-02/J-03/J-04's acceptance text calls for comparing REST output against the MCP `datasets`/`backtests`/`pnl_ledger` tools. This agent's direct `mcp__tapeology__*` tool access is wired to the canonical default port `http://localhost:8000`, but this goal-mode session's backend runs on the session-offset port `8301` (confirmed nothing listens on 8000 in this environment). Calling `mcp__tapeology__datasets` correctly returned an explicit connection error rather than fabricated data — itself consistent with the read-only-MCP anti-goal, but it means I could not diff MCP JSON against this session's REST payloads directly. This is an environment/session-topology fact, not a product defect (the byte-identical MCP↔REST proxy behavior is J-01's own acceptance test, explicitly out of scope this run and verified separately by golden replay). All REST-surface behavior for J-02/J-03/J-04/J-06 was verified directly and thoroughly.
+
+---
+
+## Golden replay scripts
+
+**None written this run.** J-02, J-03, J-04, and J-06 are all backend/machine-surface journeys
+driven by `POST` + polling `GET` sequences (dataset recording, backtest jobs, ledger reads,
+profile validation). `demo_runner.py`'s replay schema supports only `goto` / `click` / `fill`
+actions and cannot express a `POST` body or a fetch-based assertion, so none of these four
+journeys has a goto/click/fill equivalent to record. This matches the iter-6 spec's own
+"Machine-surface regression lane" note: their durable regression lane is the backend test suite,
+not the golden-replay lane. (J-01/J-05/J-08 already have golden scripts from prior iterations and
+were correctly excluded from this run's browser QA scope.)
+
+---
+
+## Environment
+
+- **Frontend URL:** http://localhost:3301 (not exercised — Frontend Present: no for iter-6; no UI surface changed)
+- **Backend URL:** http://localhost:8301 (session-offset port; used as the same-origin page for in-page `fetch()` — `/docs` Swagger UI)
+- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless
+- **Test Date:** 2026-07-03
+- **Evidence directory:** `reports/qa/goal-tape_to_profit-iter-6-evidence/`
diff --git areports/phase-goal-tape_to_profit-iter-6-ui-test-results.md breports/phase-goal-tape_to_profit-iter-6-ui-test-results.md
new file mode 100644
index 0000000..22d69f1
--- /dev/null
+++ breports/phase-goal-tape_to_profit-iter-6-ui-test-results.md
@@ -0,0 +1,30 @@
+# UI Test Results (merged)
+
+**Date:** 2026-07-03
+**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)
+
+---
+
+**Browser QA Verdict:** PASS
+
+**Overall:** 7/7 journeys passed (0 skipped)
+
+---
+
+## Results Table
+
+| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
+|---------|------|------|----------|----------|--------|---------|----------|
+| UT-J-01 | A read-only MCP server exposes the product over the canonical API | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-01-verify.png |
+| UT-J-05 | The /performance page reports PnL per enhancement honestly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-05-verify.png |
+| UT-J-08 | The existing product is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-08-verify.png |
+| UT-J-02 | Historical tape datasets persist and replay byte-identically | regression | P1 | Record dataset (symbol/window/feed/checksum stored); re-tag attempt refused 409; list reflects it; watching a sim ticker writes no rows | Recorded new dataset (7th row), checksum+metadata stored; re-tag same content → 409 with honest re-tag message; list count 6→7, new row present verbatim; watch/unwatch SIM-BUYER left dataset count unchanged (7→7→7) | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png`, `UT-J-02-ambient-check.png` |
+| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | regression | P1 | POST starts job, polls to done; report has trades + net/gross R&$, win rate, max drawdown, n, null baseline, full provenance; identical re-run is byte-identical; no broker code | POST→`queued`→`done`; aggregates carry gross_r/net_r/gross_usd/net_usd/win_rate/max_drawdown_r/n; null_baseline present (seed 1729); provenance stamped (dataset id+checksum, strategy_id, profile, fingerprint); re-run produced a different backtest id with byte-identical trades/aggregates/null_baseline; both runs appear in the list; grep found no broker/order/paper-trading code (only a comment documenting the anti-goal) | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png` |
+| UT-J-04 | Every enhancement lands one honest row in the PnL ledger | regression | P1 | Ledger shows founding row (baseline null, train+holdout separate, n, provenance, timestamp); no update/delete path; markdown regen is a byte-level no-op; REST/markdown numbers match | Founding row present: train net_r -0.16000000000001136 (n=1, insufficient sample), holdout net_r 0.3334000000001356 (n=1, insufficient sample), full provenance + timestamp; DELETE/PUT/POST all → 405; `python -m app.research.pnl_history` regen produced byte-identical sha256 before/after (`git diff` empty); markdown numbers match REST exactly | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png` |
+| UT-J-06 | Indicator profiles are versioned; the default stays byte-identical | smoke | P1 | `/research/profiles` lists default+candidate; backtests under both profiles differ only legitimately; unknown profile → honest 422; default fingerprint unchanged, candidate fingerprint distinct | `GET /research/profiles` → `default` (frozen) + `candidate-faster-warmup` (based_on default, overrides `warmup_min_events:30`); champion still `v1`/`default`; default holdout backtest: fingerprint `4d665603569b9dbf`, net_r `+0.3334000000001356` (exact pinned match); candidate holdout backtest: fingerprint `8c2c0fbf978228e3`, net_r `-0.1728000000000723` (exact pinned match) — same setup/direction (`trend_continuation`/`long`), materially different outcome (win_rate 1.0→0.0); candidate re-run byte-identical (deterministic); unknown profile → 422 `"unknown profile 'nonexistent-profile-xyz' — the registered profiles are ['default', 'candidate-faster-warmup']"` | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png` |
+
+## Environment
+
+- **Browser:** Chromium (LLM browser-qa + deterministic replay)
+- **Test Date:** 2026-07-03
+
diff --git areports/reviews/goal-tape_to_profit-iter-6-review.md breports/reviews/goal-tape_to_profit-iter-6-review.md
new file mode 100644
index 0000000..506c78c
--- /dev/null
+++ breports/reviews/goal-tape_to_profit-iter-6-review.md
@@ -0,0 +1,34 @@
+**Verdict:** PASS_WITH_NOTES
+
+```yaml
+phase: goal-tape_to_profit-iter-6
+date: 2026-07-03
+reviewer: reviewer
+summary: |
+  Implements J-06: a config-owned profile registry (default + candidate-faster-warmup) that both
+  GET /research/profiles and the backtest route's validation consult, a non-mutating per-run
+  overlay Config, and fingerprint stamping through the one existing hasher. Independently
+  verified: full backend suite 1004 passed / 1 skipped / 0 failed (own run, 360s) and targeted
+  32/32; default fingerprint pin cross-checked against the committed pnl-history.md founding row;
+  the 422 refusal was live-checked to genuinely list both registered profiles; all out-of-scope
+  files (ledger, mcp, frontend) confirmed zero-diff; resolved_for_profile confirmed callable only
+  from backtests.py by independent grep.
+spec_alignment:
+  definition_of_done: complete
+  scope_creep: none
+issues:
+  - severity: MINOR
+    file: apps/backend/tests/test_backtests_api.py
+    line: 169
+    category: tests
+    summary: test_unregistered_profile_is_422 asserts only that the unknown id is echoed in the 422 detail, not that the registered profiles (default, candidate-faster-warmup) are listed — the actual behavior is correct (verified live) but a regression dropping that clause would slip past this test
+    fix: add an assertion that both "default" and "candidate-faster-warmup" appear in r.json()["detail"], or exact-match the full detail string
+standards:
+  state_transitions_server_side: pass
+  test_quality: pass
+  no_dead_code: pass
+  no_hardcoded_localhost: n/a
+  ui_evolved_with_capability: n/a
+  navigation_updated: n/a
+  architecture_principles: pass
+```
diff --git aruns/goal-session-tape_to_profit/dispatch/prompt-req.nOCEyl.md bruns/goal-session-tape_to_profit/dispatch/prompt-req.nOCEyl.md
new file mode 100644
index 0000000..5e1b69e
--- /dev/null
+++ bruns/goal-session-tape_to_profit/dispatch/prompt-req.nOCEyl.md
@@ -0,0 +1,176 @@
+You are the goal-decomposer agent for goal-mode iteration planning.
+
+Mode: next
+Session ID: tape_to_profit
+Iteration index: 6
+Iter name: goal-tape_to_profit-iter-6
+Prior verdict: CONTINUE
+Prior depth: lean
+
+Project template: .claude/project-template.md
+Project goal (SLICED — vision + anti-goals + failing/target journeys verbatim; stable passing journeys digested to one line): runs/goal-session-tape_to_profit/iter-6/goal-slice.md
+  Full goal file: docs/goal.md — Read it ONLY if a digested journey becomes relevant to your plan.
+Agent instructions: .claude/agents/goal-decomposer.md  <-- read this first
+(CLAUDE.md is already in your system prompt — do not Read it again.)
+
+Recent evaluator log entries (last 3, pre-trimmed):
+```
+# Goal Session tape_to_profit — Evaluator Log
+
+## Iteration 0 — goal-tape_to_profit-iter-0
+
+**Date:** 2026-07-03T02:25:50+01:00
+**Verdict:** CONTINUE
+**Depth dispatched:** lean
+**Journey deltas:**
+- Newly passing: none (baseline — J-08 recorded `already_passing`)
+- Newly failing: J-01, J-02, J-03, J-04, J-05, J-06, J-07 (baseline absence — not built, exactly as the spec predicted)
+- Regressed: none
+- Anti-goal violations: none (zero source changes; `git diff HEAD` empty)
+
+**Reasoning:** Verify-only baseline executed cleanly. J-08 verified passing with independent evidence at every layer: 848/849 backend suite green, equivalence suite 7/7, and browser screenshots confirming SIM-BUYER → Buyer Control and SIM-SELLER → Seller Control with all cockpit panels populated plus honest empty states on /journal and /studies. All seven era-3 journeys confirmed absent via live 404s / module-not-found probes plus screenshots — matching the spec's prediction letter for letter. Coherence audit not run (zero-diff baseline, blueprint drafted this iteration) — no veto. Era-3 baseline anchor: 848 passing tests, 3-entry nav.
+
+**Next-step recommendation:** Iter-1 = J-01 (MCP server + `/meta/ui-routes` + nav rendered from the route map) at lean depth — independent of the J-02→J-05 chain, unlocks MCP-assisted verification for all later work, and retires the hardcoded NavBar list before J-05 adds a Performance entry (pre-empting a duplicate nav source-of-truth coherence risk). J-02 is the acceptable alternate. J-08 goes into required-still-passing from iter-1 onward.
+
+## Iteration 1 — goal-tape_to_profit-iter-1
+
+**Date:** 2026-07-03T04:14:31+01:00
+**Verdict:** CONTINUE
+**Depth dispatched:** lean
+**Journey deltas:**
+- Newly passing: J-01
+- Newly failing: none
+- Regressed: none
+- Anti-goal violations: none (MCP verified GET-only with zero `app`-package imports; policy diff exactly one allowlist entry `mcp`; `.mcp.json` untracked; equivalence 7/7 re-run independently by this evaluator)
+
+**Reasoning:** J-01 passes on cross-checked evidence at every layer: reviewer independently re-ran the 20 new tests plus the full suite (868 passed / 1 skipped, exact match to the dev handoff), browser QA produced four screenshots (all inspected — nav renders exactly Cockpit/Journal/Studies from `GET /meta/ui-routes` on all pages, `/journal/[id]` keeps Journal active, no Performance, no degraded state), the dev's live stdio session proved byte-identity and backend-down honesty, and I re-executed `test_meta_routes.py` + equivalence (12/12, exit 0). J-08 stays green (suite + equivalence twice-run, all three surfaces screenshot-verified) with one caveat: the deterministic J-08 replay silently no-oped — Playwright is not installed (engine.log 04:00:13) — so the SIM-BUYER in-browser leg rests on the live API verification plus untouched cockpit code this iteration. Coherence: COHERENCE-PASS.
+
+**Next-step recommendation:** Iter-2 = J-02 (dataset store: record/register, checksum verification, immutable train/hold-out tags with 409 re-tag refusal, committed fixture pair, byte-identical replay) at lean depth — head of the J-02→J-05 chain; the MCP `datasets` tool flips from honest 404 to live data with zero MCP changes. Must-fix alongside: install Playwright for the replay runner (or have browser QA run the J-08 SIM-BUYER leg explicitly) so required-still-passing browser regression checks stop silently no-oping.
+
+## Iteration 2 — goal-tape_to_profit-iter-2
+
+**Date:** 2026-07-03T06:00:19+01:00
+**Verdict:** CONTINUE
+**Depth dispatched:** lean
+**Journey deltas:**
+- Newly passing: J-02
+- Newly failing: none
+- Regressed: none
+- Anti-goal violations: none (no execution/broker code — import + grep verified; MCP untouched, `git diff -- app/mcp app/meta.py` empty; policy diff exactly one `"playwright"` allowlist entry, spec-authorized; runtime datasets gitignored; no ambient recording browser-proven via real cockpit watch/stop with md5sum-identical dataset dir)
+
+**Reasoning:** J-02 passes on evidence this evaluator re-verified independently at every layer: full suite re-run 901 passed / 1 skipped (exact match to dev + reviewer; 902 collected = iter-1's 869 + 33 new, nothing deleted), the 32 new dataset tests + 16 MCP tests + equivalence 7/7 all re-run green, and all key screenshots inspected — the 404→200 flip against the iter-0 baseline, full metadata (symbol/UTC window/feed/counts/checksum/frozen split), the 409 frozen-tag refusal, a tampered file surfacing explicitly in `integrity_errors` while healthy rows kept serving, and restore-to-clean. The iter-1 must-fix landed: Playwright 1.61.0 installed and the deterministic replay lane produced real rows (engine.log 05:25:42, demo_runner verdict PASS 2/2) — J-01-verify.png and J-08-verify.png match their golden scripts' final steps exactly, closing the silent no-op hole. Coherence: COHERENCE-PASS (single writer, one verified load path, exactly three routes, MCP flip free by construction).
+
+**Next-step recommendation:** Iter-3 = J-03 (strategy grammar v1 + deterministic backtest engine: config-owned entries/exits, fee/slippage models, $-per-R notional, `POST/GET /research/backtests` + cancel as a studies-style job, per-trade report with net/gross R AND $ beside a seeded random-entry null baseline, full provenance, byte-identical re-runs) at lean depth — next link in the J-02→J-05 chain, keyless on the committed fixture pair via `DatasetStore.replay`. MCP `backtests` flips from honest 404 with zero MCP code changes; when moving it out of the test suite's honest-404 premise, fold in the reviewer's NOTE (stale "404 until J-02 ships" description at app/mcp/__init__.py:165). J-03's acceptance also demands the grep-style no-broker/order/account test — build it in from the start.
+
+## Iteration 3 — goal-tape_to_profit-iter-3
+
+**Date:** 2026-07-03T08:34:58+01:00
+**Verdict:** CONTINUE
+**Depth dispatched:** lean
+**Journey deltas:**
+- Newly passing: J-03
+- Newly failing: none
+- Regressed: none
+- Anti-goal violations: none (no-execution gate 4/4 re-run by this evaluator and proven signal-bearing; MCP diff read directly — exactly two description strings; engine/serializers/datasets/meta/requirements zero diff; equivalence 7/7 re-run; register string verbatim in evidence; goal.md untouched)
+
+**Reasoning:** J-03 passes on independently cross-checked evidence: full suite re-run green by this evaluator (952 collected — 951 passed / 1 skipped, exact match to dev + reviewer; +50 tests over iter-2, none deleted), the 42 new backtest/API/no-broker tests green, and all three J-03 screenshots inspected — the 404→200 flip, a done report carrying per-trade fills/fees/slippage, aggregates (net/gross R AND $, win rate 0.2, max drawdown, n=5), seeded null baseline (seed 1729, entry_count 100), full verbatim provenance, and the exact register string, plus honest 404/422 error legs. Byte-identity verified three ways (QA's two independent POSTs → identical 59,157-char result blocks; dev's live 59,844-byte re-POST; the API-level test). J-01/J-02/J-08 all re-verified with explicit result rows (replay lane crashed, browser-qa ran the fallback legs per the iter-1 lesson). Coherence: COHERENCE-PASS. Root cause found for this iteration's browser instability: the per-user tmpfs quota on /tmp (5.2G) is pinned by ~4.5G of accumulated pytest basetemp dirs — it killed Playwright at launch, starved Chrome, and initially broke this evaluator's own suite run; deletion was permission-denied, so it remains outstanding.
+
+**Next-step recommendation:** Iter-4 = J-04 (append-only PnL ledger: founding baseline row from strategy v1 on the fixture train AND hold-out datasets via this iteration's backtest reports; `GET /research/pnl/ledger`; pure-rendered `reports/pnl/pnl-history.md` with byte-level no-op regeneration; no update/delete paths; "insufficient sample" labeling; MCP `pnl_ledger` out of NOT_YET_SHIPPED with the non-empty-200 byte-identity test) at lean depth. Environment must-fix: clear `/tmp/pytest-of-dennis-chan` (~4.5G, pins the per-user tmpfs quota) or route pytest basetemp off tmpfs — otherwise browser lanes and large suite runs stay flaky.
+
+## Iteration 4 — goal-tape_to_profit-iter-4
+
+**Date:** 2026-07-03T10:17:12+01:00
+**Verdict:** CONTINUE
+**Depth dispatched:** lean
+**Journey deltas:**
+- Newly passing: J-04
+- Newly failing: none
+- Regressed: none
+- Anti-goal violations: none
+
+**Reasoning:** J-04 verified passing on multi-surface evidence: iter-0 404 → live 200 with the founding row (explicit `baseline: null`, candidate net R+$ per split, n=1 both splits labeled insufficient sample, full provenance, register verbatim); POST/DELETE → 405; the row's aggregates equal the independent J-03 re-run capture EXACTLY and its dataset ids + checksums appear verbatim in the J-02 datasets-list capture; committed `reports/pnl/pnl-history.md` shows identical numbers; MCP `pnl_ledger` byte-identity tested (last tool out of honest-404). Evaluator independently confirmed the `app/mcp/__init__.py` diff is two documentation strings only and the only UPDATE SQL is schema_version bookkeeping. Suite 983 passed / 1 skipped, equivalence 7/7, replay lane 2/2 (J-01, J-08), COHERENCE-PASS.
+
+**Next-step recommendation:** Iter-5 = J-05 (`/performance` page: render `GET /research/pnl/ledger` verbatim — $ beside R beside n, register visible, train/hold-out separate, insufficient-sample labels exercised by the real n=1 founding row; champion summary per blueprint; Performance nav entry rendered from `/meta/ui-routes`, adding `/performance` to the route map — note the stored golden J-01 nav expectations must evolve with the 4th link) at lean depth. J-06 then J-07 after. J-07 planning heads-up: fixture windows arm n=1 per split (< min 5) — see lessons.md.
+
+## Iteration 5 — goal-tape_to_profit-iter-5
+
+**Date:** 2026-07-03T14:12:54+01:00
+**Verdict:** CONTINUE
+**Depth dispatched:** lean
+**Journey deltas:**
+- Newly passing: J-05
+- Newly failing: none
+- Regressed: none
+- Anti-goal violations: none
+
+**Reasoning:** J-05 verified end-to-end: `/performance` reached from the fourth top-bar link (rendered from `/meta/ui-routes`, single owner `app/meta.py`), ledger + champion rendered verbatim (browser-qa's live in-page 24/24 page-equals-API check; screenshot values match the raw ledger JSON capture value-for-value), founding row shows full-precision R/$/n, "insufficient sample (n < 5)" on both splits, the explicit "no prior incumbent" marker, register from the API payload, champion v1/default from the minimally-landed `GET /research/profiles`. Verify-and-complete resume worked as designed: all interrupted-dispatch claims independently reproduced (988 passed / 1 skipped, equivalence 7/7, build clean, replay J-01+J-05 green) with zero code changes. All 5 required-still-passing journeys re-verified (J-01 via the evolved 4-destination golden script, J-08 via replay, J-02/J-03/J-04 via fresh in-page API cycles + suite). MCP diff docstring-only, protected files zero-diff, COHERENCE-PASS. Passing: J-01–J-05, J-08; remaining: J-06, J-07.
+
+**Next-step recommendation:** J-06 at lean depth — register one candidate profile (additive feature key or alternate threshold set), refactor the backtest route's profile refusal to consult the registry, backtest the fixture dataset under default AND the candidate, pin pre-profile equivalence outputs. Caution: `/research/profiles` now returns 200 with a zero-candidate registry (landed minimally at J-05) — that 200 is NOT partial J-06 credit. Required-still-passing browser lane now carries three golden scripts (J-01, J-05, J-08). Then J-07 (sweep), whose promotion-gate tests must control minimum-n both ways (fixture pair arms n=1 per split).
+```
+Lessons learned (full file, append-only):
+```
+# Goal Session tape_to_profit — Lessons Learned
+
+Append-only ledger of takeaways from prior iterations. The goal-evaluator
+appends one entry per iteration; the goal-decomposer reads this file before
+planning each iteration to avoid repeating known pitfalls.
+
+Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
+failures, regression triggers, or decisions that worked well. Avoid
+restating the verdict (the evaluator-log.md already does that).
+
+## iter-1 — 2026-07-03T04:14:31+01:00
+
+**Verdict:** CONTINUE
+**Lesson:** The deterministic replay of required-still-passing journeys silently no-ops when Playwright is missing: engine.log shows "Playwright (Python) is not available" at the J-08 replay step, yet the merged UI report still claims "LLM browser-qa + deterministic replay" and reports "1/1 passed (0 skipped)" with no replay row and no failure. Only engine.log reveals the gap — a real J-08 regression could have passed unnoticed if the automated suite had not covered it.
+**Applies to:** every future iteration (all carry J-08 as required-still-passing) — until `python3 -m pip install --user playwright && python3 -m playwright install chromium` is done, browser QA must explicitly execute required-still-passing browser legs, and the evaluator must demand a result row per required journey rather than trusting the merge header.
+
+## iter-2 — 2026-07-03T06:00:19+01:00
+
+**Verdict:** CONTINUE
+**Lesson:** Machine-surface journeys (no frontend page) structurally cannot get golden replay scripts: `demo_runner.py` supports only goto/click/fill (no POST) and its `normalize_url` rewrites ANY localhost URL onto the single frontend base_url, so a `goto` aimed at the backend port silently hits the frontend instead. Their durable regression lane is the backend test suite; for browser-originated verification, Chrome MCP's `eval` issuing in-page `fetch()` from a backend-origin page works well (iter-2 drove POST/409/422 flows that way).
+**Applies to:** J-03, J-04, J-06, J-07 (all machine-surface per the blueprint IA table) — dispatch browser-qa knowing no replay script will exist for them, and route their required-still-passing coverage through the automated suite, not the replay lane.
+
+## iter-3 — 2026-07-03T08:34:58+01:00
+
+**Verdict:** CONTINUE
+**Lesson:** Three seemingly unrelated failures this iteration — the replay lane's Playwright Chromium killed at launch (SIGTRAP, engine.log 07:29:19), browser-qa's Chrome `net::ERR_INSUFFICIENT_RESOURCES` + hydration stalls, and sqlite `Disk quota exceeded` errors under pytest — share ONE root cause: `/tmp` is a tmpfs with a per-user quota (~5.2G = 80%), pinned at the limit by ~4.5G of accumulated pytest basetemp dirs in `/tmp/pytest-of-dennis-chan` (~4-5MB per suite run x hundreds of framework runs; pytest's keep-3 cleanup has not kept up). Symptom looks like flaky browsers or a broken product; it is neither. Workaround proven this iteration: run pytest with `TMPDIR` + `--basetemp` pointed at a root-filesystem dir; real fix is clearing the pytest dir (this evaluator's delete was permission-denied — operator action).
+**Applies to:** every future iteration's browser-qa / replay / large-suite lane — before diagnosing "flaky browser" or unexplained sqlite I/O errors, check `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota first.
+
+## iter-4 — 2026-07-03T10:17:12+01:00
+
+**Verdict:** CONTINUE
+**Lesson:** The committed fixture dataset pair arms exactly n=1 trade per split under strategy v1's sustain/cooldown rules (train net_r −0.16, holdout net_r +0.3334, both < `pnl_min_sample_size` 5) — the iter-3 note's "n=5" figure came from a different substrate. Consequence: on the current fixtures NO candidate can ever satisfy an n ≥ 5 hold-out promotion gate, so J-07's sweep tests must control the configured minimum (both ways) or use enlarged fixture windows to exercise a real promotion; the founding row's insufficient-sample labeling also means J-05's page renders that label from day one with real data.
+**Applies to:** J-07 (promotion-gate test design on the fixture pair), J-05 (insufficient-sample rendering is live-data-exercised), any iter asserting sample-size gates against `tests/fixtures/datasets/`
+
+## iter-5 — 2026-07-03T14:12:54+01:00
+
+**Verdict:** CONTINUE
+**Lesson:** The verify-and-complete resume protocol delivered a zero-churn success: every interrupted-dispatch claim (988/1 suite, equivalence 7/7, build, 2/2 replay) reproduced independently and "no code changes — verified as-is" was the correct developer outcome — re-verification, not rebuilding, is the right posture for an uncommitted-but-complete working tree. Side effect to heed: `GET /research/profiles` now serves 200 with a zero-candidate registry (row 33 landed minimally for J-05's champion summary), so J-06's fresh-failing evidence is "registry lists no candidate", no longer a 404 — a 200 there must not be misread as J-06 progress.
+**Applies to:** any future interrupted-dispatch resume (verify first, change only what a failed check requires); the J-06 iteration's failing-baseline framing and acceptance evidence.
+```
+Journey state (inline digest; Read runs/goal-session-tape_to_profit/state/journey-history.json only for fields the digest omits):
+```
+J-01 | passing         | last_passing=goal-tape_to_profit-iter-5 | A read-only MCP server exposes the product over the canonical API
+J-02 | passing         | last_passing=goal-tape_to_profit-iter-5 | Historical tape datasets persist and replay byte-identically (train/hold-out registry)
+J-03 | passing         | last_passing=goal-tape_to_profit-iter-5 | Strategy grammar v1 backtests a dataset into a deterministic PnL report
+J-04 | passing         | last_passing=goal-tape_to_profit-iter-5 | Every enhancement lands one honest row in the PnL ledger
+J-05 | passing         | last_passing=goal-tape_to_profit-iter-5 | The /performance page reports PnL per enhancement honestly
+J-06 | failing         | last_passing=- | Indicator profiles are versioned; the default stays byte-identical
+J-07 | failing         | last_passing=- | The candidate sweep survives hold-out or says so honestly
+J-08 | passing         | last_passing=goal-tape_to_profit-iter-5 | The existing product is unchanged (regression sentinel)
+```
+
+Last iteration eval: runs/goal-session-tape_to_profit/iter-5/eval.md
+
+Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.
+
+Write the iteration spec to: docs/phases/goal-tape_to_profit-iter-6.md
+Also keep runs/goal-session-tape_to_profit/state/blueprint.md current per your agent instructions: register any new displayed value in the Data Contract and place new pages under an existing Information-Architecture home (additive edits only). For a nav-skeleton change, make the edit AND write a one-line reason to runs/goal-session-tape_to_profit/state/blueprint.reapproval-requested.
+
+The spec MUST include a 'Goal Mode Metadata' section with at minimum:
+  - Mode: next
+  - Depth: lean | full
+  - Target journeys: <comma-separated journey IDs>
+
+Do NOT write code or implement anything. The iteration spec and any blueprint edits are planning documents, not code. STOP after writing them.
\ No newline at end of file
diff --git aruns/goal-session-tape_to_profit/iter-6/coherence.md bruns/goal-session-tape_to_profit/iter-6/coherence.md
new file mode 100644
index 0000000..7e76540
--- /dev/null
+++ bruns/goal-session-tape_to_profit/iter-6/coherence.md
@@ -0,0 +1,68 @@
+# Iteration 6 — Coherence Audit
+
+**Iteration:** goal-tape_to_profit-iter-6
+**Date:** 2026-07-03
+**Written by:** coherence-auditor
+
+---
+
+**Verdict:** COHERENCE-PASS
+
+---
+
+## Scope of this audit
+
+`docs/phases/goal-tape_to_profit-iter-6.md` metadata declares `Frontend Present: no`. The
+invocation's snapshot SHA (`14a7ea463f4cc674e1721d253e897cd6178f2277`) is a WIP stash-style commit
+that already captured the resumed J-06 implementation before this iteration's dispatch ran (per
+the spec's "Resume posture — VERIFY-AND-COMPLETE" note), so `git diff <snapshot-sha>` shows only a
+`telemetry.jsonl` update. To audit the actual iteration content I widened the diff to the last
+audited baseline, `git diff 9173a7d` (the iter-5 commit, whose `iter-5/coherence.md` verdict was
+COHERENCE-PASS). That diff touches exactly: `apps/backend/app/config.py`,
+`apps/backend/app/research/{backtests,profiles,routes}.py`,
+`apps/backend/tests/{test_backtests_api.py,test_profiles_api.py}`, and new
+`apps/backend/tests/test_profile_equivalence.py`. `apps/frontend/`, `apps/backend/app/mcp/`, and
+every other module are confirmed zero-diff (`git diff --stat 9173a7d -- apps/frontend` /
+`-- apps/backend/app/mcp` both empty). No `reports/phase-goal-tape_to_profit-iter-6-ui-surface-map.md`
+exists, consistent with the no-frontend-change declaration.
+
+## Data Contract check
+
+| Value / entity | Result | Evidence (file:line) |
+|---|---|---|
+| Row 33 — Indicator profiles + champion pointer | OK | Single owner `Config.profile_definition` (`apps/backend/app/config.py:984`) / `Config.profile_registry` (`apps/backend/app/config.py:1007`), built from the private `_PROFILE_IDS_IN_ORDER` tuple (`apps/backend/app/config.py:44`). Served ONLY by `GET /research/profiles` → `profiles_projection()` (`apps/backend/app/research/profiles.py:38`) → `CONFIG.profile_registry()`. `POST /research/backtests`'s validation reads the SAME registry — `registry.config.profile_definition(body.profile)` (`apps/backend/app/research/routes.py:1530`) — not a second allowlist. `apps/backend/tests/test_profiles_api.py` asserts `app/research/profiles.py` carries no literal id-string copy. Champion pointer constants (`STRATEGY_V1_ID`, `PROFILE_DEFAULT`) unmoved. |
+| Row 31 — Backtest reports (`profile` id + `config_fingerprint` in provenance) | OK | Stamped via `run_config.config_fingerprint()` where `run_config = self._config.resolved_for_profile(params["profile"])` (`apps/backend/app/research/backtests.py:221` terminal report, `:550` queued-time stamp) — the ONE pre-existing `Config.config_fingerprint()` hasher (`apps/backend/app/config.py`, exclusion set updated at the same diff to add `profile_candidate_warmup_min_events` so the new registry-metadata field cannot move any fingerprint), applied to either the identical `default` `Config` object or a `dataclasses.replace()` overlay that never mutates the shared `CONFIG` singleton. `test_profile_equivalence.py:110-129` pins `default` at `4d665603569b9dbf` (unchanged from pre-J-06) and the candidate at a distinct `8c2c0fbf978228e3` — corroborated live in the dev handoff and QA evidence (`reports/phase-goal-tape_to_profit-iter-6-ui-test-results.md` UT-J-06 row). |
+| Engine-path exclusivity (supports rows 31/33) | OK | `test_profile_equivalence.py:306-317` (`test_resolved_for_profile_is_called_only_by_the_backtest_runner`) source-scans every `app/**/*.py` file (excluding `config.py`'s own definition) and asserts the only caller is `research/backtests.py` — confirmed by direct grep: the sole non-definition, non-test call sites are `apps/backend/app/research/backtests.py:221,550`. No cockpit/live-tape path resolves a profile. |
+| New payload sub-fields (`based_on`, `overrides`) on the row-33 profile descriptor | Not a new entity — OK | These are richer shape on the SAME registered row-33 entity (the profile registry), not a new displayed value; no Data-Contract addition needed, matching the iter spec's explicit "Data-contract additions: None." |
+
+No new function/service/endpoint independently recomputes any registered value, and no new UI
+surface fetches a registered value from a non-canonical source (the frontend is zero-diff; the
+existing `/performance` registry panel — unchanged since J-05 — already reads
+`GET /research/profiles` generically). `test_performance_page_offers_no_profile_selection_control`
+(`test_profile_equivalence.py:320-327`) directly asserts the frontend source has no `<select>` and
+no hardcoded candidate-id literal.
+
+## Information Architecture check
+
+| Feature / route | Result | Evidence (nav file inspected) |
+|---|---|---|
+| (none — no new page/route/feature this iteration) | OK | `git diff --stat 9173a7d -- apps/frontend` is empty; `apps/frontend/components/NavBar.tsx` untouched. `GET /research/profiles` and `POST /research/backtests` are pre-existing endpoints on their pre-declared blueprint machine home (IA table rows for J-06/J-03); the read-only display continues to ride the pre-existing `/performance` page with zero page changes, exactly as the iter spec's "Blueprint conformance" section states ("No new surfaces… No Information-Architecture or nav-skeleton change"). |
+
+No new page, no parallel shell, no duplicate home — there is nothing new to reach via navigation
+this iteration.
+
+## Blocking violations (FAIL only)
+
+None.
+
+## Advisory notes (non-blocking)
+
+- `PROFILE_DEFAULT` moved from `apps/backend/app/research/backtests.py` to
+  `apps/backend/app/config.py` (single source now lives beside the new `profile_definition`/
+  `profile_registry` methods); `backtests.py` re-exports it for existing importers
+  (`apps/backend/app/config.py:32`, re-export confirmed in `apps/backend/app/research/backtests.py`
+  diff). This is a consolidation, not a duplication — noted only for the record.
+- Reviewer report (`reports/reviews/goal-tape_to_profit-iter-6-review.md`, verdict
+  PASS_WITH_NOTES) independently corroborates the single-registry/single-hasher/zero-out-of-scope-
+  diff findings above and flags one MINOR test-completeness nit (an assertion could be stronger in
+  `test_unregistered_profile_is_422`) — a test-quality item, not a coherence violation.
diff --git aruns/goal-session-tape_to_profit/iter-6/goal-slice.md bruns/goal-session-tape_to_profit/iter-6/goal-slice.md
new file mode 100644
index 0000000..6a3d580
--- /dev/null
+++ bruns/goal-session-tape_to_profit/iter-6/goal-slice.md
@@ -0,0 +1,334 @@
+<!-- GOAL SLICE: generated by goal_gate.py. Stable passing journeys are
+     digested to one line (6 of 8); vision, anti-goals, and
+     target/failing journeys are verbatim. Full text: docs/goal.md -->
+# Tapeology — Project Goal (Era 3: the profit-research evolution)
+
+> Eras 1–2 (tape reading + the research evolution, journeys J-01 – J-68, GOAL_ACHIEVED across
+> three goal-mode sessions) are archived at [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md).
+> Everything they shipped is the **foundation** of this goal and MUST NOT regress.
+
+## Vision
+
+Tapeology already reads the tape: one US-stock ticker in, live order flow watched, and the
+current tape state classified into one of five states — `buyer_control`, `seller_control`,
+`bid_absorption`, `ask_absorption`, `unclear` — on the defining principle of **price impact,
+not raw aggression**. On top of that read sits a decision-support research layer: declared
+theses, tape-confirmation verdicts, an append-only journal, and replay studies with null
+baselines. Data comes from a deterministic seedable simulator (default, keyless) or from real
+US-equity vendors behind a provider-agnostic seam (Alpaca today: SIP historical, IEX live).
+
+The **profit-research era** answers the question the first two eras deliberately refused to
+ask: **does the tape read convert to simulated profit — and does each enhancement to the read
+improve it?**
+
+To answer it honestly, the product gains:
+
+- **Persisted historical tape datasets** — recorded trade/quote streams that replay
+  byte-identically, split into **frozen train and hold-out sets**, so every measurement is
+  reproducible and nothing is ever judged on the data it was tuned on.
+- **A config-owned strategy grammar and a deterministic backtest engine** — simulated entries
+  and exits driven by the existing tape states and indicators, producing PnL in **R-multiples
+  AND dollars**, gross and net of an explicit fee/slippage model, always beside a seeded
+  random-entry null baseline.
+- **Versioned indicator profiles** — candidate indicator adjustments and additions live beside
+  the frozen `default` profile; the live cockpit never changes, and only the backtest layer may
+  opt into candidates.
+- **A read-only MCP server** — the whole product becomes machine-readable for the AI dev-chain
+  (the goal-mode MCP loop): every MCP tool is a thin proxy over the same canonical REST API a
+  human uses.
+- **An autonomous enhancement loop** — after every must-have journey passes, a proposer surveys
+  the product, screens candidate improvements against the hold-out data, promotes only
+  **hold-out survivors** as new journeys, and every promoted enhancement appends **one honest
+  row to the PnL ledger** so the operator can watch the PnL improve (or honestly not improve)
+  enhancement by enhancement.
+
+Absolutes, unchanged from day one: **no broker, no order placement (real or paper), no ML, no
+advice**. Every PnL figure is a measurement of the past under disclosed assumptions — never a
+forecast, never a promise.
+
+## Target Users
+
+- The discretionary intraday trader (the project owner) using the tape read to support
+  decisions — now also as a **systematic researcher** measuring whether that read carries
+  simulated edge and which refinements improve it.
+- AI dev-chain agents (the goal-mode loop) surveying the product through its read-only MCP
+  tools and judging every enhancement by its hold-out simulated-PnL delta.
+
+## Foundation invariants (imported from the archived constitution — still law)
+
+The archived goal's critical rules remain binding on ALL new code:
+
+1. **Price impact over raw aggression** — high one-sided aggression with no price progress is
+   absorption, never control.
+2. **Honest uncertainty** — weak/mixed evidence reads `unclear`; spread and impact are judged
+   relative to price, feed-aware and halt-aware; never manufacture a directional call.
+3. **No fabricated data** — every failure mode surfaces an explicit state (`stale`, error,
+   no-data, closed, unavailable); nothing is synthesized to force a green journey.
+4. **Single source of truth** — every value is computed exactly once and read identically by
+   REST, WebSocket, UI, MCP, and reports; nothing downstream recomputes it.
+5. **No magic numbers** — every threshold, window, fee, slippage, minimum-n, and cutoff comes
+   from config.
+6. **Provider-agnostic engine** — vendor SDKs live in one adapter behind the neutral seam.
+7. **Deterministic & reproducible** — same inputs, same seeds, same outputs, byte-identical.
+8. **No secrets in source** — keys only from environment; keyless runs are simulator-only with
+   explicit "unavailable" real modes.
+9. **Research stays read-only over the engine** — observers never mutate engine outputs
+   (byte-identical equivalence, exception-isolated).
+10. **Journal integrity** — research records are append-only, never backfilled, never inferred.
+11. **Source, feed, and config honesty** — every record stamps its source, `data_feed`, and
+    `config_fingerprint`; nothing pools across feeds or fingerprints.
+12. **Dates are dd-MM-yyyy everywhere**; times in the user's local timezone with US-session
+    quick-picks.
+13. **The existing surfaces stay intact** — cockpit `/`, `/journal`, `/journal/[id]`,
+    `/studies` keep working exactly as shipped.
+
+## Success Criteria
+
+In priority order — honesty and non-regression outrank any profit number:
+
+1. **Nothing existing regresses.** The full backend suite stays green, the engine equivalence
+   test keeps proving byte-identical default outputs, and the archived-era surfaces keep
+   working (J-08).
+2. **Datasets are trustworthy.** A recorded dataset replays byte-identically to its source
+   stream, re-runs are identical, checksums verify, and train/hold-out tags are frozen at
+   registration.
+3. **Backtests are deterministic and honest.** PnL is reported in R AND $, gross and net of
+   the configured fee/slippage model, with trade count n, beside a seeded random-entry null
+   baseline, stamped with full provenance (dataset id + checksum, strategy config, profile id,
+   `config_fingerprint`).
+4. **Nothing is promoted on train performance alone.** A candidate becomes the champion only
+   by beating the incumbent on the frozen hold-out set with at least the configured minimum
+   trade count; train-only winners are labeled overfit and rejected.
+5. **The default read is frozen.** Indicator evolution is additive and versioned; the live
+   cockpit and every archived-era journey run on the byte-identical `default` profile.
+6. **Every enhancement reports its PnL delta.** One append-only PnL-ledger row per
+   enhancement (baseline vs candidate, train AND hold-out, R and $), surfaced at
+   `/performance`, in `reports/pnl/pnl-history.md`, and over REST/MCP.
+7. **The product is machine-readable.** Every MCP tool returns byte-identical JSON to its
+   canonical REST endpoint; everything an agent can do over MCP has a curl-equivalent.
+
+## Key Capabilities
+
+Layered strictly on top of the archived eras' capabilities 1–34, which remain unchanged.
+
+1. **Historical tape dataset store.** Recorded trade/quote event streams per
+   symbol + window + feed, stored under `TAPEOLOGY_DATASET_DIR` (default
+   `apps/backend/.data/datasets/`, gitignored), each with metadata (symbol, UTC window, feed,
+   event counts, checksum) and an immutable `train | holdout` split tag assigned at
+   registration. A committed miniature train + hold-out fixture pair proves the whole pipeline
+   keyless in CI. The live cockpit's tape is never persisted — recording is an explicit
+   research action.
+2. **Versioned indicator profiles.** Named engine-feature/classifier configurations. `default`
+   is the frozen legacy configuration, guarded by a byte-equivalence test against pinned
+   outputs. Candidate profiles may only add new feature keys or alternate threshold values;
+   they are selectable solely by backtest/study runs (never by the live cockpit) and the
+   profile id folds into `config_fingerprint`.
+3. **Strategy grammar v1.** Config-owned, human-readable rules: entries armed by the existing
+   setup/tape-state rules (setup type × direction), exits by invalidation R-stop, time horizon,
+   or state-flip; an explicit fee model (per-share + minimum) and slippage model (spread
+   fraction); a fixed $-per-R notional for dollar conversion. No ML anywhere.
+4. **Deterministic backtest engine.** Replays a dataset unpaced through a fresh engine (the
+   existing replay-study runner pattern), simulates fills at recorded prices adjusted by the
+   slippage model, and produces a persisted report: per-trade list and aggregates — net/gross
+   R and $, win rate, max drawdown (R), n — beside a seeded random-entry null baseline on the
+   same dataset. Runs as a cancellable job like studies.
+5. **The PnL ledger.** An append-only SQLite table (journal DB) + `GET /research/pnl/ledger` +
+   a pure-rendered `reports/pnl/pnl-history.md`. One row per enhancement: enhancement id and
+   title, baseline vs candidate net R and net $ on train AND hold-out, n per split, full
+   provenance, timestamp. No update or delete paths exist.
+6. **Read-only MCP server.** `python -m app.mcp` (stdio), spawned on demand by the AI CLI.
+   Tools are thin HTTP clients against the running backend (`TAPEOLOGY_API_BASE`, default
+   `http://localhost:8000`) — never a second app instance, never direct engine imports:
+   `tape_state`, `tape_features`, `tape_history`, `journal`, `analytics`, `studies`,
+   `datasets`, `backtests`, `pnl_ledger`, `taxonomy`, `ui_route_map`, plus a generic
+   `get_endpoint(path)` allowlisted to GET `/tape/*`, `/research/*`, `/meta/*`. Backend down →
+   explicit tool error. Registered for the dev-chain via `project-extensions/mcp-servers.yaml`.
+7. **Candidate sweep harness.** `python -m app.research.pnl_scan --out <path>` evaluates every
+   registered candidate (profile or strategy variant) against the champion over all train
+   datasets, validates survivors on the hold-out set, appends promotions to the PnL ledger,
+   and writes a machine-readable scan report. Zero candidates or zero survivors is an honest,
+   exit-0 outcome.
+8. **The `/performance` page.** A fourth top-level page rendering the PnL ledger and the
+   current champion (strategy + profile) verbatim from the canonical endpoints, in the
+   existing dark cockpit design language.
+9. **A canonical UI route map.** `GET /meta/ui-routes` owns the list of user-facing routes;
+   the rendered navigation and the MCP `ui_route_map` tool read it, never a hand-maintained
+   duplicate.
+
+## Non-Goals
+
+- No brokerage integration, order placement, routing, or execution of any kind — **neither
+  real-money nor paper-trading APIs**. Simulated fills exist only inside the offline
+  backtester, computed against recorded historical tape and sent nowhere.
+- No machine learning, no online/in-engine tuning, no fitted thresholds — candidate search is
+  bounded, config-enumerated, offline, and hold-out-validated.
+- No trading advice, no imperative cues ("buy", "sell", "enter now"), no prediction language,
+  no expected-return claims. Simulated PnL describes the past under stated assumptions.
+- No account, capital, portfolio, or position management; no compounding equity projections.
+- No stock scanning/screening, multi-symbol dashboards, news/sentiment, fundamentals, or
+  general-purpose charting — unchanged from the archived eras.
+- No auto-modification of the `default` profile or any live-cockpit behavior by the
+  enhancement loop.
+
+## Constraints
+
+- **Stack (carried over):** Backend Python 3.12 + FastAPI (uvicorn, REST + WebSocket), tests
+  via pytest (venv at `apps/backend/.venv/`, package manager `uv`). Frontend Next.js 15 App
+  Router + TypeScript + Tailwind v3 (npm), charts via `lightweight-charts`. Research
+  persistence in the journal-scoped SQLite (`TAPEOLOGY_JOURNAL_DB`). Backend
+  `http://localhost:8000`, frontend `http://localhost:3000`. Reserved sim tickers
+  (`SIM-BUYER`, `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`) still work keyless.
+- **Dataset discipline:** datasets live under `TAPEOLOGY_DATASET_DIR` (gitignored except the
+  committed CI fixture pair), are immutable once registered (content checksum verified on
+  load), stamp their feed, and carry a split tag that can never be changed afterwards.
+- **Profile discipline:** the `default` profile is frozen and equivalence-tested; candidates
+  are additive-only; every artifact touching a non-default profile is stamped with the profile
+  id; profile id is part of `config_fingerprint`.
+- **Backtest determinism:** seeded, unpaced, single-threaded per run; identical inputs and
+  seeds reproduce byte-identical reports; the null baseline uses a seeded RNG recorded in the
+  report.
+- **PnL honesty register:** a dollar figure never appears without its R figure, its n, and the
+  visible register "simulated — assumed fees/slippage — not indicative of live results";
+  results with n below the configured minimum are labeled "insufficient sample"; train and
+  hold-out numbers are never pooled or averaged together.
+- **MCP read-only discipline:** the MCP server exposes no mutating tools, proxies the
+  canonical REST API over HTTP, adds no second computation path, and fails explicitly when the
+  backend is unreachable.
+- **Design direction:** the `/performance` page follows the existing dark tape-cockpit design
+  tokens; density and honesty over decoration.
+
+### Glossary (new terms; archived glossary still applies)
+
+- **Dataset** — an immutable recorded trade/quote event stream (symbol + window + feed) with
+  checksum and split tag.
+- **Train / hold-out** — the two frozen dataset splits; tuning may only ever see train;
+  promotion is decided only on hold-out.
+- **Profile** — a named, versioned engine indicator/classifier configuration; `default` is the
+  frozen legacy one.
+- **Strategy** — a config-owned rule set mapping tape states/features to simulated entries and
+  exits.
+- **Backtest** — a deterministic replay of one dataset under one strategy + profile, producing
+  a PnL report beside a null baseline.
+- **PnL ledger** — the append-only record of per-enhancement baseline-vs-candidate PnL deltas.
+- **Champion** — the currently promoted strategy + profile pair; only a hold-out survivor may
+  replace it.
+
+## Product Shape
+
+Nav (top bar): **Cockpit `/` · Journal `/journal` (+ `/journal/[id]`) · Studies `/studies` ·
+Performance `/performance`** — the first three exactly as shipped in the archived eras.
+
+**API surface.** The archived canonical endpoints are unchanged: `/health`,
+`POST/DELETE /watch/{ticker}` (+ `/pause`, `/resume`, `/speed`), `/symbols/search`,
+`/market/clock`, `GET /tape/{ticker}/state|features|events|summary|history`,
+`WS /tape/{ticker}/stream`, and `/research/*` (taxonomy, analytics, thesis, hints, journal,
+studies). The profit-research era adds, every projection computed once server-side:
+
+- `POST /research/datasets` (record/register) · `GET /research/datasets` · `GET /research/datasets/{id}`
+- `POST /research/backtests` · `GET /research/backtests` · `GET /research/backtests/{id}` (+ cancel, mirroring studies)
+- `GET /research/pnl/ledger`
+- `GET /research/profiles`
+- `GET /meta/ui-routes`
+
+MCP tools are thin proxies over exactly these — no new computation, no divergent serialization.
+
+**Data Contract (canonical values — each computed once, owned by one place):**
+
+- Tape state, confidence, features, history — computed in the engine (unchanged owner).
+- Dataset records and checksums — owned by the dataset store; served only via
+  `/research/datasets*`.
+- Backtest results (trades, R/$ aggregates, null baseline) — computed once by the backtest
+  runner and persisted; `/performance`, reports, and MCP read the stored rows verbatim.
+- PnL-ledger rows — appended once at validation time; every surface (REST, page, markdown,
+  MCP) renders the same stored rows.
+- Indicator profiles and the champion pointer — config-owned; served via `/research/profiles`.
+- The UI route map — owned by `/meta/ui-routes`; the nav renders it, never a second list.
+
+## Must-have user journeys
+
+Journeys **J-01 – J-08** are the profit-research era. Each is sized for one lean iteration.
+All are verifiable **keyless** via the simulator and the committed fixture dataset pair;
+real-scale datasets are an operator action requiring Alpaca credentials and only enlarge the
+data — they change no behavior. Natural dependency order: J-02 → J-03 → J-04 → J-05 and
+J-06 → J-07; J-01 is independent; J-08 guards continuously. The foundation (archived
+J-01 – J-68 behavior) MUST NOT regress.
+- **J-01: A read-only MCP server exposes the product over the canonical API** — passing (stable; digested)
+- **J-02: Historical tape datasets persist and replay byte-identically (train/hold-out registry)** — passing (stable; digested)
+- **J-03: Strategy grammar v1 backtests a dataset into a deterministic PnL report** — passing (stable; digested)
+- **J-04: Every enhancement lands one honest row in the PnL ledger** — passing (stable; digested)
+- **J-05: The /performance page reports PnL per enhancement honestly** — passing (stable; digested)
+
+- **J-06: Indicator profiles are versioned; the default stays byte-identical**
+  - Steps:
+    1. List profiles via `GET /research/profiles` (and the MCP tool): `default` plus at least
+       one registered candidate (a new additive feature key or an alternate threshold set)
+    2. Run the same fixture-dataset backtest under `default` and under the candidate
+    3. Run the engine equivalence suite and the full backend suite
+  - Acceptance: an automated equivalence test replays fixed event streams under `default` and
+    asserts **byte-identical** state/confidence/features/history against pinned pre-profile
+    outputs; the live cockpit and every archived-era surface use `default` only (no UI path
+    selects a candidate); candidate outputs appear only in backtest/study artifacts stamped
+    with their profile id; the two backtests differ only where the candidate legitimately
+    changes behavior and both remain individually deterministic. *(Keyless; automated.)*
+
+- **J-07: The candidate sweep survives hold-out or says so honestly**
+  - Steps:
+    1. Run `python -m app.research.pnl_scan --out <path>` with at least one registered
+       candidate and the fixture datasets
+    2. Read the scan report and the PnL ledger afterwards; re-run the identical scan
+  - Acceptance: the scan evaluates every registered candidate against the champion over all
+    **train** datasets and validates apparent winners on the **hold-out** set; the report
+    records, per candidate: train and hold-out net R/$ deltas, n per split, per-dataset
+    breakdown, `survivor` (true iff it beats the champion on hold-out net R AND net $ with
+    n ≥ the configured minimum), and `robustness: robust|speculative` (robust iff positive on
+    every train dataset individually); train-only winners are explicitly labeled overfit and
+    never promoted; a promotion appends a PnL-ledger row and moves the champion pointer
+    **without modifying the `default` profile or any engine default**; the scan is
+    deterministic under fixed seeds and identical re-runs produce identical reports; zero
+    candidates or zero survivors produces an explicit honest report and **exit code 0**.
+    *(Keyless; automated.)*
+- **J-08: The existing product is unchanged (regression sentinel)** — passing (stable; digested)
+<!-- AUTO:journeys -->
+<!-- /AUTO:journeys -->
+
+## Anti-goals
+
+- **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere —
+  no brokerage integration, no trading API, **no paper-trading API**, no order tickets, no
+  recommendation to execute. The ONLY permitted "fill" is the offline backtester's simulated
+  fill computed against recorded historical tape, clearly labeled simulated and sent nowhere.
+  *(critical)*
+- **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always
+  appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out
+  basis, and its null baseline — and MUST never be presented as expected live results, an edge
+  claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
+- **Default engine outputs are frozen.** Indicator evolution is additive and versioned only:
+  candidate profiles may add feature keys or alternate thresholds, but the `default` profile's
+  outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, and
+  no enhancement may mutate an archived-era behavior to pass. *(critical)*
+- **No train-only promotion.** Nothing becomes the champion, a proposed journey, or a claimed
+  improvement on the strength of train data alone: hold-out survival (net R AND net $, with
+  the configured minimum n) is the only promotion gate; overfit results are labeled overfit.
+  *(critical)*
+- **No ML, no online tuning.** Candidate search is bounded, config-enumerated, offline, and
+  deterministic; no fitted models, no optimizer loops inside the engine, no thresholds that
+  move at runtime.
+- **No fabricated data — honest failure states.** No synthesized trades, quotes, fills,
+  datasets, or PnL to force a green journey; every failure mode (backend down, corrupt
+  dataset, empty window, missing credentials, insufficient n) surfaces an explicit, distinct
+  state. *(critical)*
+- **Single source of truth.** Every canonical value in the Data Contract is computed once and
+  read verbatim by every surface — REST, WebSocket, UI, markdown reports, and MCP. A second
+  computation path or a diverging number across surfaces is a defect. *(critical)*
+- **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical
+  GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second
+  implementation of any computation. *(critical)*
+- **Persistence stays scoped.** SQLite holds research records (now including backtests and the
+  PnL ledger); the dataset store holds explicitly recorded historical tape for research
+  replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
+- **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
+  inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this
+  Anti-goals section, or any other part of this file; proposed journeys MUST carry a
+  PnL-ledger acceptance criterion, keep the default profile byte-identical, and include a
+  [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is
+  a failure. *(critical)*
diff --git aruns/goal-session-tape_to_profit/iter-6/journey-history.pre.json bruns/goal-session-tape_to_profit/iter-6/journey-history.pre.json
new file mode 100644
index 0000000..bae6fc0
--- /dev/null
+++ bruns/goal-session-tape_to_profit/iter-6/journey-history.pre.json
@@ -0,0 +1,78 @@
+{
+  "journeys": {
+    "J-01": {
+      "id": "J-01",
+      "name": "A read-only MCP server exposes the product over the canonical API",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit-iter-5",
+      "last_passing_iter": "goal-tape_to_profit-iter-5",
+      "first_seen_iter": "goal-tape_to_profit-iter-0",
+      "last_evidence_path": "reports/qa/goal-tape_to_profit-iter-5-evidence/J-01-verify.png"
+    },
+    "J-02": {
+      "id": "J-02",
+      "name": "Historical tape datasets persist and replay byte-identically (train/hold-out registry)",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit-iter-5",
+      "last_passing_iter": "goal-tape_to_profit-iter-5",
+      "first_seen_iter": "goal-tape_to_profit-iter-0",
+      "last_evidence_path": "reports/qa/goal-tape_to_profit-iter-5-evidence/J-02-record-detail-200.png"
+    },
+    "J-03": {
+      "id": "J-03",
+      "name": "Strategy grammar v1 backtests a dataset into a deterministic PnL report",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit-iter-5",
+      "last_passing_iter": "goal-tape_to_profit-iter-5",
+      "first_seen_iter": "goal-tape_to_profit-iter-0",
+      "last_evidence_path": "reports/qa/goal-tape_to_profit-iter-5-evidence/J-03-backtest-done-report.png"
+    },
+    "J-04": {
+      "id": "J-04",
+      "name": "Every enhancement lands one honest row in the PnL ledger",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit-iter-5",
+      "last_passing_iter": "goal-tape_to_profit-iter-5",
+      "first_seen_iter": "goal-tape_to_profit-iter-0",
+      "last_evidence_path": "reports/qa/goal-tape_to_profit-iter-5-evidence/J-04-ledger-founding-row-200.png"
+    },
+    "J-05": {
+      "id": "J-05",
+      "name": "The /performance page reports PnL per enhancement honestly",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit-iter-5",
+      "last_passing_iter": "goal-tape_to_profit-iter-5",
+      "first_seen_iter": "goal-tape_to_profit-iter-0",
+      "last_evidence_path": "reports/qa/goal-tape_to_profit-iter-5-evidence/J-05-02-performance-page.png"
+    },
+    "J-06": {
+      "id": "J-06",
+      "name": "Indicator profiles are versioned; the default stays byte-identical",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit-iter-5",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit-iter-0",
+      "last_evidence_path": "reports/qa/goal-tape_to_profit-iter-5-evidence/J-05-02-performance-page.png"
+    },
+    "J-07": {
+      "id": "J-07",
+      "name": "The candidate sweep survives hold-out or says so honestly",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit-iter-0",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit-iter-0",
+      "last_evidence_path": "reports/phase-goal-tape_to_profit-iter-0-ui-test-results.md"
+    },
+    "J-08": {
+      "id": "J-08",
+      "name": "The existing product is unchanged (regression sentinel)",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit-iter-5",
+      "last_passing_iter": "goal-tape_to_profit-iter-5",
+      "first_seen_iter": "goal-tape_to_profit-iter-0",
+      "last_evidence_path": "reports/qa/goal-tape_to_profit-iter-5-evidence/J-08-verify.png"
+    }
+  },
+  "anti_goal_violations": [],
+  "updated_at": "2026-07-03T14:12:54+01:00"
+}
diff --git aruns/goal-session-tape_to_profit/iter-6/snapshot-sha bruns/goal-session-tape_to_profit/iter-6/snapshot-sha
new file mode 100644
index 0000000..3cb7c3d
--- /dev/null
+++ bruns/goal-session-tape_to_profit/iter-6/snapshot-sha
@@ -0,0 +1 @@
+14a7ea463f4cc674e1721d253e897cd6178f2277
\ No newline at end of file
diff --git aruns/goal-session-tape_to_profit/trace/trace.jsonl bruns/goal-session-tape_to_profit/trace/trace.jsonl
new file mode 100644
index 0000000..6e68035
--- /dev/null
+++ bruns/goal-session-tape_to_profit/trace/trace.jsonl
@@ -0,0 +1,7 @@
+{"step":1,"agent":"goal-decomposer","cli":"claude","backend":"interactive","ts":"2026-07-03T16:45:21Z","exit_code":0,"duration_seconds":539,"stdout_path":"0001-goal-decomposer.log","args":["-p","You are the goal-decomposer agent for goal-mode iteration planning.","","Mode: next","Session ID: tape_to_profit","Iteration index: 6","Iter name: goal-tape_to_profit-iter-6","Prior verdict: CONTINUE","Prior depth: lean","","Project template: .claude/project-template.md","Project goal (SLICED — vision + anti-goals + failing/target journeys verbatim; stable passing journeys digested to one line): runs/goal-session-tape_to_profit/iter-6/goal-slice.md","  Full goal file: docs/goal.md — Read it ONLY if a digested journey becomes relevant to your plan.","Agent instructions: .claude/agents/goal-decomposer.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","","Recent evaluator log entries (last 3, pre-trimmed):","```","# Goal Session tape_to_profit — Evaluator Log","","## Iteration 0 — goal-tape_to_profit-iter-0","","**Date:** 2026-07-03T02:25:50+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: none (baseline — J-08 recorded `already_passing`)","- Newly failing: J-01, J-02, J-03, J-04, J-05, J-06, J-07 (baseline absence — not built, exactly as the spec predicted)","- Regressed: none","- Anti-goal violations: none (zero source changes; `git diff HEAD` empty)","","**Reasoning:** Verify-only baseline executed cleanly. J-08 verified passing with independent evidence at every layer: 848/849 backend suite green, equivalence suite 7/7, and browser screenshots confirming SIM-BUYER → Buyer Control and SIM-SELLER → Seller Control with all cockpit panels populated plus honest empty states on /journal and /studies. All seven era-3 journeys confirmed absent via live 404s / module-not-found probes plus screenshots — matching the spec's prediction letter for letter. Coherence audit not run (zero-diff baseline, blueprint drafted this iteration) — no veto. Era-3 baseline anchor: 848 passing tests, 3-entry nav.","","**Next-step recommendation:** Iter-1 = J-01 (MCP server + `/meta/ui-routes` + nav rendered from the route map) at lean depth — independent of the J-02→J-05 chain, unlocks MCP-assisted verification for all later work, and retires the hardcoded NavBar list before J-05 adds a Performance entry (pre-empting a duplicate nav source-of-truth coherence risk). J-02 is the acceptable alternate. J-08 goes into required-still-passing from iter-1 onward.","","## Iteration 1 — goal-tape_to_profit-iter-1","","**Date:** 2026-07-03T04:14:31+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-01","- Newly failing: none","- Regressed: none","- Anti-goal violations: none (MCP verified GET-only with zero `app`-package imports; policy diff exactly one allowlist entry `mcp`; `.mcp.json` untracked; equivalence 7/7 re-run independently by this evaluator)","","**Reasoning:** J-01 passes on cross-checked evidence at every layer: reviewer independently re-ran the 20 new tests plus the full suite (868 passed / 1 skipped, exact match to the dev handoff), browser QA produced four screenshots (all inspected — nav renders exactly Cockpit/Journal/Studies from `GET /meta/ui-routes` on all pages, `/journal/[id]` keeps Journal active, no Performance, no degraded state), the dev's live stdio session proved byte-identity and backend-down honesty, and I re-executed `test_meta_routes.py` + equivalence (12/12, exit 0). J-08 stays green (suite + equivalence twice-run, all three surfaces screenshot-verified) with one caveat: the deterministic J-08 replay silently no-oped — Playwright is not installed (engine.log 04:00:13) — so the SIM-BUYER in-browser leg rests on the live API verification plus untouched cockpit code this iteration. Coherence: COHERENCE-PASS.","","**Next-step recommendation:** Iter-2 = J-02 (dataset store: record/register, checksum verification, immutable train/hold-out tags with 409 re-tag refusal, committed fixture pair, byte-identical replay) at lean depth — head of the J-02→J-05 chain; the MCP `datasets` tool flips from honest 404 to live data with zero MCP changes. Must-fix alongside: install Playwright for the replay runner (or have browser QA run the J-08 SIM-BUYER leg explicitly) so required-still-passing browser regression checks stop silently no-oping.","","## Iteration 2 — goal-tape_to_profit-iter-2","","**Date:** 2026-07-03T06:00:19+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-02","- Newly failing: none","- Regressed: none","- Anti-goal violations: none (no execution/broker code — import + grep verified; MCP untouched, `git diff -- app/mcp app/meta.py` empty; policy diff exactly one `\"playwright\"` allowlist entry, spec-authorized; runtime datasets gitignored; no ambient recording browser-proven via real cockpit watch/stop with md5sum-identical dataset dir)","","**Reasoning:** J-02 passes on evidence this evaluator re-verified independently at every layer: full suite re-run 901 passed / 1 skipped (exact match to dev + reviewer; 902 collected = iter-1's 869 + 33 new, nothing deleted), the 32 new dataset tests + 16 MCP tests + equivalence 7/7 all re-run green, and all key screenshots inspected — the 404→200 flip against the iter-0 baseline, full metadata (symbol/UTC window/feed/counts/checksum/frozen split), the 409 frozen-tag refusal, a tampered file surfacing explicitly in `integrity_errors` while healthy rows kept serving, and restore-to-clean. The iter-1 must-fix landed: Playwright 1.61.0 installed and the deterministic replay lane produced real rows (engine.log 05:25:42, demo_runner verdict PASS 2/2) — J-01-verify.png and J-08-verify.png match their golden scripts' final steps exactly, closing the silent no-op hole. Coherence: COHERENCE-PASS (single writer, one verified load path, exactly three routes, MCP flip free by construction).","","**Next-step recommendation:** Iter-3 = J-03 (strategy grammar v1 + deterministic backtest engine: config-owned entries/exits, fee/slippage models, $-per-R notional, `POST/GET /research/backtests` + cancel as a studies-style job, per-trade report with net/gross R AND $ beside a seeded random-entry null baseline, full provenance, byte-identical re-runs) at lean depth — next link in the J-02→J-05 chain, keyless on the committed fixture pair via `DatasetStore.replay`. MCP `backtests` flips from honest 404 with zero MCP code changes; when moving it out of the test suite's honest-404 premise, fold in the reviewer's NOTE (stale \"404 until J-02 ships\" description at app/mcp/__init__.py:165). J-03's acceptance also demands the grep-style no-broker/order/account test — build it in from the start.","","## Iteration 3 — goal-tape_to_profit-iter-3","","**Date:** 2026-07-03T08:34:58+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-03","- Newly failing: none","- Regressed: none","- Anti-goal violations: none (no-execution gate 4/4 re-run by this evaluator and proven signal-bearing; MCP diff read directly — exactly two description strings; engine/serializers/datasets/meta/requirements zero diff; equivalence 7/7 re-run; register string verbatim in evidence; goal.md untouched)","","**Reasoning:** J-03 passes on independently cross-checked evidence: full suite re-run green by this evaluator (952 collected — 951 passed / 1 skipped, exact match to dev + reviewer; +50 tests over iter-2, none deleted), the 42 new backtest/API/no-broker tests green, and all three J-03 screenshots inspected — the 404→200 flip, a done report carrying per-trade fills/fees/slippage, aggregates (net/gross R AND $, win rate 0.2, max drawdown, n=5), seeded null baseline (seed 1729, entry_count 100), full verbatim provenance, and the exact register string, plus honest 404/422 error legs. Byte-identity verified three ways (QA's two independent POSTs → identical 59,157-char result blocks; dev's live 59,844-byte re-POST; the API-level test). J-01/J-02/J-08 all re-verified with explicit result rows (replay lane crashed, browser-qa ran the fallback legs per the iter-1 lesson). Coherence: COHERENCE-PASS. Root cause found for this iteration's browser instability: the per-user tmpfs quota on /tmp (5.2G) is pinned by ~4.5G of accumulated pytest basetemp dirs — it killed Playwright at launch, starved Chrome, and initially broke this evaluator's own suite run; deletion was permission-denied, so it remains outstanding.","","**Next-step recommendation:** Iter-4 = J-04 (append-only PnL ledger: founding baseline row from strategy v1 on the fixture train AND hold-out datasets via this iteration's backtest reports; `GET /research/pnl/ledger`; pure-rendered `reports/pnl/pnl-history.md` with byte-level no-op regeneration; no update/delete paths; \"insufficient sample\" labeling; MCP `pnl_ledger` out of NOT_YET_SHIPPED with the non-empty-200 byte-identity test) at lean depth. Environment must-fix: clear `/tmp/pytest-of-dennis-chan` (~4.5G, pins the per-user tmpfs quota) or route pytest basetemp off tmpfs — otherwise browser lanes and large suite runs stay flaky.","","## Iteration 4 — goal-tape_to_profit-iter-4","","**Date:** 2026-07-03T10:17:12+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-04","- Newly failing: none","- Regressed: none","- Anti-goal violations: none","","**Reasoning:** J-04 verified passing on multi-surface evidence: iter-0 404 → live 200 with the founding row (explicit `baseline: null`, candidate net R+$ per split, n=1 both splits labeled insufficient sample, full provenance, register verbatim); POST/DELETE → 405; the row's aggregates equal the independent J-03 re-run capture EXACTLY and its dataset ids + checksums appear verbatim in the J-02 datasets-list capture; committed `reports/pnl/pnl-history.md` shows identical numbers; MCP `pnl_ledger` byte-identity tested (last tool out of honest-404). Evaluator independently confirmed the `app/mcp/__init__.py` diff is two documentation strings only and the only UPDATE SQL is schema_version bookkeeping. Suite 983 passed / 1 skipped, equivalence 7/7, replay lane 2/2 (J-01, J-08), COHERENCE-PASS.","","**Next-step recommendation:** Iter-5 = J-05 (`/performance` page: render `GET /research/pnl/ledger` verbatim — $ beside R beside n, register visible, train/hold-out separate, insufficient-sample labels exercised by the real n=1 founding row; champion summary per blueprint; Performance nav entry rendered from `/meta/ui-routes`, adding `/performance` to the route map — note the stored golden J-01 nav expectations must evolve with the 4th link) at lean depth. J-06 then J-07 after. J-07 planning heads-up: fixture windows arm n=1 per split (< min 5) — see lessons.md.","","## Iteration 5 — goal-tape_to_profit-iter-5","","**Date:** 2026-07-03T14:12:54+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-05","- Newly failing: none","- Regressed: none","- Anti-goal violations: none","","**Reasoning:** J-05 verified end-to-end: `/performance` reached from the fourth top-bar link (rendered from `/meta/ui-routes`, single owner `app/meta.py`), ledger + champion rendered verbatim (browser-qa's live in-page 24/24 page-equals-API check; screenshot values match the raw ledger JSON capture value-for-value), founding row shows full-precision R/$/n, \"insufficient sample (n < 5)\" on both splits, the explicit \"no prior incumbent\" marker, register from the API payload, champion v1/default from the minimally-landed `GET /research/profiles`. Verify-and-complete resume worked as designed: all interrupted-dispatch claims independently reproduced (988 passed / 1 skipped, equivalence 7/7, build clean, replay J-01+J-05 green) with zero code changes. All 5 required-still-passing journeys re-verified (J-01 via the evolved 4-destination golden script, J-08 via replay, J-02/J-03/J-04 via fresh in-page API cycles + suite). MCP diff docstring-only, protected files zero-diff, COHERENCE-PASS. Passing: J-01–J-05, J-08; remaining: J-06, J-07.","","**Next-step recommendation:** J-06 at lean depth — register one candidate profile (additive feature key or alternate threshold set), refactor the backtest route's profile refusal to consult the registry, backtest the fixture dataset under default AND the candidate, pin pre-profile equivalence outputs. Caution: `/research/profiles` now returns 200 with a zero-candidate registry (landed minimally at J-05) — that 200 is NOT partial J-06 credit. Required-still-passing browser lane now carries three golden scripts (J-01, J-05, J-08). Then J-07 (sweep), whose promotion-gate tests must control minimum-n both ways (fixture pair arms n=1 per split).","```","Lessons learned (full file, append-only):","```","# Goal Session tape_to_profit — Lessons Learned","","Append-only ledger of takeaways from prior iterations. The goal-evaluator","appends one entry per iteration; the goal-decomposer reads this file before","planning each iteration to avoid repeating known pitfalls.","","Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising","failures, regression triggers, or decisions that worked well. Avoid","restating the verdict (the evaluator-log.md already does that).","","## iter-1 — 2026-07-03T04:14:31+01:00","","**Verdict:** CONTINUE","**Lesson:** The deterministic replay of required-still-passing journeys silently no-ops when Playwright is missing: engine.log shows \"Playwright (Python) is not available\" at the J-08 replay step, yet the merged UI report still claims \"LLM browser-qa + deterministic replay\" and reports \"1/1 passed (0 skipped)\" with no replay row and no failure. Only engine.log reveals the gap — a real J-08 regression could have passed unnoticed if the automated suite had not covered it.","**Applies to:** every future iteration (all carry J-08 as required-still-passing) — until `python3 -m pip install --user playwright && python3 -m playwright install chromium` is done, browser QA must explicitly execute required-still-passing browser legs, and the evaluator must demand a result row per required journey rather than trusting the merge header.","","## iter-2 — 2026-07-03T06:00:19+01:00","","**Verdict:** CONTINUE","**Lesson:** Machine-surface journeys (no frontend page) structurally cannot get golden replay scripts: `demo_runner.py` supports only goto/click/fill (no POST) and its `normalize_url` rewrites ANY localhost URL onto the single frontend base_url, so a `goto` aimed at the backend port silently hits the frontend instead. Their durable regression lane is the backend test suite; for browser-originated verification, Chrome MCP's `eval` issuing in-page `fetch()` from a backend-origin page works well (iter-2 drove POST/409/422 flows that way).","**Applies to:** J-03, J-04, J-06, J-07 (all machine-surface per the blueprint IA table) — dispatch browser-qa knowing no replay script will exist for them, and route their required-still-passing coverage through the automated suite, not the replay lane.","","## iter-3 — 2026-07-03T08:34:58+01:00","","**Verdict:** CONTINUE","**Lesson:** Three seemingly unrelated failures this iteration — the replay lane's Playwright Chromium killed at launch (SIGTRAP, engine.log 07:29:19), browser-qa's Chrome `net::ERR_INSUFFICIENT_RESOURCES` + hydration stalls, and sqlite `Disk quota exceeded` errors under pytest — share ONE root cause: `/tmp` is a tmpfs with a per-user quota (~5.2G = 80%), pinned at the limit by ~4.5G of accumulated pytest basetemp dirs in `/tmp/pytest-of-dennis-chan` (~4-5MB per suite run x hundreds of framework runs; pytest's keep-3 cleanup has not kept up). Symptom looks like flaky browsers or a broken product; it is neither. Workaround proven this iteration: run pytest with `TMPDIR` + `--basetemp` pointed at a root-filesystem dir; real fix is clearing the pytest dir (this evaluator's delete was permission-denied — operator action).","**Applies to:** every future iteration's browser-qa / replay / large-suite lane — before diagnosing \"flaky browser\" or unexplained sqlite I/O errors, check `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota first.","","## iter-4 — 2026-07-03T10:17:12+01:00","","**Verdict:** CONTINUE","**Lesson:** The committed fixture dataset pair arms exactly n=1 trade per split under strategy v1's sustain/cooldown rules (train net_r −0.16, holdout net_r +0.3334, both < `pnl_min_sample_size` 5) — the iter-3 note's \"n=5\" figure came from a different substrate. Consequence: on the current fixtures NO candidate can ever satisfy an n ≥ 5 hold-out promotion gate, so J-07's sweep tests must control the configured minimum (both ways) or use enlarged fixture windows to exercise a real promotion; the founding row's insufficient-sample labeling also means J-05's page renders that label from day one with real data.","**Applies to:** J-07 (promotion-gate test design on the fixture pair), J-05 (insufficient-sample rendering is live-data-exercised), any iter asserting sample-size gates against `tests/fixtures/datasets/`","","## iter-5 — 2026-07-03T14:12:54+01:00","","**Verdict:** CONTINUE","**Lesson:** The verify-and-complete resume protocol delivered a zero-churn success: every interrupted-dispatch claim (988/1 suite, equivalence 7/7, build, 2/2 replay) reproduced independently and \"no code changes — verified as-is\" was the correct developer outcome — re-verification, not rebuilding, is the right posture for an uncommitted-but-complete working tree. Side effect to heed: `GET /research/profiles` now serves 200 with a zero-candidate registry (row 33 landed minimally for J-05's champion summary), so J-06's fresh-failing evidence is \"registry lists no candidate\", no longer a 404 — a 200 there must not be misread as J-06 progress.","**Applies to:** any future interrupted-dispatch resume (verify first, change only what a failed check requires); the J-06 iteration's failing-baseline framing and acceptance evidence.","```","Journey state (inline digest; Read runs/goal-session-tape_to_profit/state/journey-history.json only for fields the digest omits):","```","J-01 | passing         | last_passing=goal-tape_to_profit-iter-5 | A read-only MCP server exposes the product over the canonical API","J-02 | passing         | last_passing=goal-tape_to_profit-iter-5 | Historical tape datasets persist and replay byte-identically (train/hold-out registry)","J-03 | passing         | last_passing=goal-tape_to_profit-iter-5 | Strategy grammar v1 backtests a dataset into a deterministic PnL report","J-04 | passing         | last_passing=goal-tape_to_profit-iter-5 | Every enhancement lands one honest row in the PnL ledger","J-05 | passing         | last_passing=goal-tape_to_profit-iter-5 | The /performance page reports PnL per enhancement honestly","J-06 | failing         | last_passing=- | Indicator profiles are versioned; the default stays byte-identical","J-07 | failing         | last_passing=- | The candidate sweep survives hold-out or says so honestly","J-08 | passing         | last_passing=goal-tape_to_profit-iter-5 | The existing product is unchanged (regression sentinel)","```","","Last iteration eval: runs/goal-session-tape_to_profit/iter-5/eval.md","","Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.","","Write the iteration spec to: docs/phases/goal-tape_to_profit-iter-6.md","Also keep runs/goal-session-tape_to_profit/state/blueprint.md current per your agent instructions: register any new displayed value in the Data Contract and place new pages under an existing Information-Architecture home (additive edits only). For a nav-skeleton change, make the edit AND write a one-line reason to runs/goal-session-tape_to_profit/state/blueprint.reapproval-requested.","","The spec MUST include a 'Goal Mode Metadata' section with at minimum:","  - Mode: next","  - Depth: lean | full","  - Target journeys: <comma-separated journey IDs>","","Do NOT write code or implement anything. The iteration spec and any blueprint edits are planning documents, not code. STOP after writing them."],"model":"claude-opus-4-8"}
+{"step":2,"agent":"developer","cli":"claude","backend":"interactive","ts":"2026-07-03T17:26:30Z","exit_code":0,"duration_seconds":2469,"stdout_path":"0002-developer.log","args":["-p","You are the developer agent for goal-mode lean iteration.","","Iteration: goal-tape_to_profit-iter-6","Iter spec: docs/phases/goal-tape_to_profit-iter-6.md","Project goal: docs/goal.md  <-- read Must-have user journeys and Anti-goals","Project template: .claude/project-template.md","Agent instructions: .claude/agents/developer.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","","Mode: INITIAL BUILD","","","This is a LEAN goal-mode iteration. Implement only what the iter spec's IN SCOPE","section calls for. Tighter scope than a full phase. Do NOT introduce features","outside the iter spec's IN SCOPE list.","","When complete:","- Write dev handoff to: docs/handoffs/goal-tape_to_profit-iter-6-dev.md","- Update runs/goal-tape_to_profit-iter-6/status.json with current_step: dev_complete",""],"model":"claude-sonnet-5"}
+{"step":3,"agent":"goal-decomposer","cli":"claude","backend":"interactive","ts":"2026-07-03T17:40:46Z","exit_code":0,"duration_seconds":679,"stdout_path":"0003-goal-decomposer.log","args":["-p","You are the goal-decomposer agent for goal-mode iteration planning.","","Mode: next","Session ID: tape_to_profit","Iteration index: 6","Iter name: goal-tape_to_profit-iter-6","Prior verdict: CONTINUE","Prior depth: lean","","Project template: .claude/project-template.md","Project goal (SLICED — vision + anti-goals + failing/target journeys verbatim; stable passing journeys digested to one line): runs/goal-session-tape_to_profit/iter-6/goal-slice.md","  Full goal file: docs/goal.md — Read it ONLY if a digested journey becomes relevant to your plan.","Agent instructions: .claude/agents/goal-decomposer.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","","Recent evaluator log entries (last 3, pre-trimmed):","```","# Goal Session tape_to_profit — Evaluator Log","","## Iteration 0 — goal-tape_to_profit-iter-0","","**Date:** 2026-07-03T02:25:50+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: none (baseline — J-08 recorded `already_passing`)","- Newly failing: J-01, J-02, J-03, J-04, J-05, J-06, J-07 (baseline absence — not built, exactly as the spec predicted)","- Regressed: none","- Anti-goal violations: none (zero source changes; `git diff HEAD` empty)","","**Reasoning:** Verify-only baseline executed cleanly. J-08 verified passing with independent evidence at every layer: 848/849 backend suite green, equivalence suite 7/7, and browser screenshots confirming SIM-BUYER → Buyer Control and SIM-SELLER → Seller Control with all cockpit panels populated plus honest empty states on /journal and /studies. All seven era-3 journeys confirmed absent via live 404s / module-not-found probes plus screenshots — matching the spec's prediction letter for letter. Coherence audit not run (zero-diff baseline, blueprint drafted this iteration) — no veto. Era-3 baseline anchor: 848 passing tests, 3-entry nav.","","**Next-step recommendation:** Iter-1 = J-01 (MCP server + `/meta/ui-routes` + nav rendered from the route map) at lean depth — independent of the J-02→J-05 chain, unlocks MCP-assisted verification for all later work, and retires the hardcoded NavBar list before J-05 adds a Performance entry (pre-empting a duplicate nav source-of-truth coherence risk). J-02 is the acceptable alternate. J-08 goes into required-still-passing from iter-1 onward.","","## Iteration 1 — goal-tape_to_profit-iter-1","","**Date:** 2026-07-03T04:14:31+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-01","- Newly failing: none","- Regressed: none","- Anti-goal violations: none (MCP verified GET-only with zero `app`-package imports; policy diff exactly one allowlist entry `mcp`; `.mcp.json` untracked; equivalence 7/7 re-run independently by this evaluator)","","**Reasoning:** J-01 passes on cross-checked evidence at every layer: reviewer independently re-ran the 20 new tests plus the full suite (868 passed / 1 skipped, exact match to the dev handoff), browser QA produced four screenshots (all inspected — nav renders exactly Cockpit/Journal/Studies from `GET /meta/ui-routes` on all pages, `/journal/[id]` keeps Journal active, no Performance, no degraded state), the dev's live stdio session proved byte-identity and backend-down honesty, and I re-executed `test_meta_routes.py` + equivalence (12/12, exit 0). J-08 stays green (suite + equivalence twice-run, all three surfaces screenshot-verified) with one caveat: the deterministic J-08 replay silently no-oped — Playwright is not installed (engine.log 04:00:13) — so the SIM-BUYER in-browser leg rests on the live API verification plus untouched cockpit code this iteration. Coherence: COHERENCE-PASS.","","**Next-step recommendation:** Iter-2 = J-02 (dataset store: record/register, checksum verification, immutable train/hold-out tags with 409 re-tag refusal, committed fixture pair, byte-identical replay) at lean depth — head of the J-02→J-05 chain; the MCP `datasets` tool flips from honest 404 to live data with zero MCP changes. Must-fix alongside: install Playwright for the replay runner (or have browser QA run the J-08 SIM-BUYER leg explicitly) so required-still-passing browser regression checks stop silently no-oping.","","## Iteration 2 — goal-tape_to_profit-iter-2","","**Date:** 2026-07-03T06:00:19+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-02","- Newly failing: none","- Regressed: none","- Anti-goal violations: none (no execution/broker code — import + grep verified; MCP untouched, `git diff -- app/mcp app/meta.py` empty; policy diff exactly one `\"playwright\"` allowlist entry, spec-authorized; runtime datasets gitignored; no ambient recording browser-proven via real cockpit watch/stop with md5sum-identical dataset dir)","","**Reasoning:** J-02 passes on evidence this evaluator re-verified independently at every layer: full suite re-run 901 passed / 1 skipped (exact match to dev + reviewer; 902 collected = iter-1's 869 + 33 new, nothing deleted), the 32 new dataset tests + 16 MCP tests + equivalence 7/7 all re-run green, and all key screenshots inspected — the 404→200 flip against the iter-0 baseline, full metadata (symbol/UTC window/feed/counts/checksum/frozen split), the 409 frozen-tag refusal, a tampered file surfacing explicitly in `integrity_errors` while healthy rows kept serving, and restore-to-clean. The iter-1 must-fix landed: Playwright 1.61.0 installed and the deterministic replay lane produced real rows (engine.log 05:25:42, demo_runner verdict PASS 2/2) — J-01-verify.png and J-08-verify.png match their golden scripts' final steps exactly, closing the silent no-op hole. Coherence: COHERENCE-PASS (single writer, one verified load path, exactly three routes, MCP flip free by construction).","","**Next-step recommendation:** Iter-3 = J-03 (strategy grammar v1 + deterministic backtest engine: config-owned entries/exits, fee/slippage models, $-per-R notional, `POST/GET /research/backtests` + cancel as a studies-style job, per-trade report with net/gross R AND $ beside a seeded random-entry null baseline, full provenance, byte-identical re-runs) at lean depth — next link in the J-02→J-05 chain, keyless on the committed fixture pair via `DatasetStore.replay`. MCP `backtests` flips from honest 404 with zero MCP code changes; when moving it out of the test suite's honest-404 premise, fold in the reviewer's NOTE (stale \"404 until J-02 ships\" description at app/mcp/__init__.py:165). J-03's acceptance also demands the grep-style no-broker/order/account test — build it in from the start.","","## Iteration 3 — goal-tape_to_profit-iter-3","","**Date:** 2026-07-03T08:34:58+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-03","- Newly failing: none","- Regressed: none","- Anti-goal violations: none (no-execution gate 4/4 re-run by this evaluator and proven signal-bearing; MCP diff read directly — exactly two description strings; engine/serializers/datasets/meta/requirements zero diff; equivalence 7/7 re-run; register string verbatim in evidence; goal.md untouched)","","**Reasoning:** J-03 passes on independently cross-checked evidence: full suite re-run green by this evaluator (952 collected — 951 passed / 1 skipped, exact match to dev + reviewer; +50 tests over iter-2, none deleted), the 42 new backtest/API/no-broker tests green, and all three J-03 screenshots inspected — the 404→200 flip, a done report carrying per-trade fills/fees/slippage, aggregates (net/gross R AND $, win rate 0.2, max drawdown, n=5), seeded null baseline (seed 1729, entry_count 100), full verbatim provenance, and the exact register string, plus honest 404/422 error legs. Byte-identity verified three ways (QA's two independent POSTs → identical 59,157-char result blocks; dev's live 59,844-byte re-POST; the API-level test). J-01/J-02/J-08 all re-verified with explicit result rows (replay lane crashed, browser-qa ran the fallback legs per the iter-1 lesson). Coherence: COHERENCE-PASS. Root cause found for this iteration's browser instability: the per-user tmpfs quota on /tmp (5.2G) is pinned by ~4.5G of accumulated pytest basetemp dirs — it killed Playwright at launch, starved Chrome, and initially broke this evaluator's own suite run; deletion was permission-denied, so it remains outstanding.","","**Next-step recommendation:** Iter-4 = J-04 (append-only PnL ledger: founding baseline row from strategy v1 on the fixture train AND hold-out datasets via this iteration's backtest reports; `GET /research/pnl/ledger`; pure-rendered `reports/pnl/pnl-history.md` with byte-level no-op regeneration; no update/delete paths; \"insufficient sample\" labeling; MCP `pnl_ledger` out of NOT_YET_SHIPPED with the non-empty-200 byte-identity test) at lean depth. Environment must-fix: clear `/tmp/pytest-of-dennis-chan` (~4.5G, pins the per-user tmpfs quota) or route pytest basetemp off tmpfs — otherwise browser lanes and large suite runs stay flaky.","","## Iteration 4 — goal-tape_to_profit-iter-4","","**Date:** 2026-07-03T10:17:12+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-04","- Newly failing: none","- Regressed: none","- Anti-goal violations: none","","**Reasoning:** J-04 verified passing on multi-surface evidence: iter-0 404 → live 200 with the founding row (explicit `baseline: null`, candidate net R+$ per split, n=1 both splits labeled insufficient sample, full provenance, register verbatim); POST/DELETE → 405; the row's aggregates equal the independent J-03 re-run capture EXACTLY and its dataset ids + checksums appear verbatim in the J-02 datasets-list capture; committed `reports/pnl/pnl-history.md` shows identical numbers; MCP `pnl_ledger` byte-identity tested (last tool out of honest-404). Evaluator independently confirmed the `app/mcp/__init__.py` diff is two documentation strings only and the only UPDATE SQL is schema_version bookkeeping. Suite 983 passed / 1 skipped, equivalence 7/7, replay lane 2/2 (J-01, J-08), COHERENCE-PASS.","","**Next-step recommendation:** Iter-5 = J-05 (`/performance` page: render `GET /research/pnl/ledger` verbatim — $ beside R beside n, register visible, train/hold-out separate, insufficient-sample labels exercised by the real n=1 founding row; champion summary per blueprint; Performance nav entry rendered from `/meta/ui-routes`, adding `/performance` to the route map — note the stored golden J-01 nav expectations must evolve with the 4th link) at lean depth. J-06 then J-07 after. J-07 planning heads-up: fixture windows arm n=1 per split (< min 5) — see lessons.md.","","## Iteration 5 — goal-tape_to_profit-iter-5","","**Date:** 2026-07-03T14:12:54+01:00","**Verdict:** CONTINUE","**Depth dispatched:** lean","**Journey deltas:**","- Newly passing: J-05","- Newly failing: none","- Regressed: none","- Anti-goal violations: none","","**Reasoning:** J-05 verified end-to-end: `/performance` reached from the fourth top-bar link (rendered from `/meta/ui-routes`, single owner `app/meta.py`), ledger + champion rendered verbatim (browser-qa's live in-page 24/24 page-equals-API check; screenshot values match the raw ledger JSON capture value-for-value), founding row shows full-precision R/$/n, \"insufficient sample (n < 5)\" on both splits, the explicit \"no prior incumbent\" marker, register from the API payload, champion v1/default from the minimally-landed `GET /research/profiles`. Verify-and-complete resume worked as designed: all interrupted-dispatch claims independently reproduced (988 passed / 1 skipped, equivalence 7/7, build clean, replay J-01+J-05 green) with zero code changes. All 5 required-still-passing journeys re-verified (J-01 via the evolved 4-destination golden script, J-08 via replay, J-02/J-03/J-04 via fresh in-page API cycles + suite). MCP diff docstring-only, protected files zero-diff, COHERENCE-PASS. Passing: J-01–J-05, J-08; remaining: J-06, J-07.","","**Next-step recommendation:** J-06 at lean depth — register one candidate profile (additive feature key or alternate threshold set), refactor the backtest route's profile refusal to consult the registry, backtest the fixture dataset under default AND the candidate, pin pre-profile equivalence outputs. Caution: `/research/profiles` now returns 200 with a zero-candidate registry (landed minimally at J-05) — that 200 is NOT partial J-06 credit. Required-still-passing browser lane now carries three golden scripts (J-01, J-05, J-08). Then J-07 (sweep), whose promotion-gate tests must control minimum-n both ways (fixture pair arms n=1 per split).","```","Lessons learned (full file, append-only):","```","# Goal Session tape_to_profit — Lessons Learned","","Append-only ledger of takeaways from prior iterations. The goal-evaluator","appends one entry per iteration; the goal-decomposer reads this file before","planning each iteration to avoid repeating known pitfalls.","","Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising","failures, regression triggers, or decisions that worked well. Avoid","restating the verdict (the evaluator-log.md already does that).","","## iter-1 — 2026-07-03T04:14:31+01:00","","**Verdict:** CONTINUE","**Lesson:** The deterministic replay of required-still-passing journeys silently no-ops when Playwright is missing: engine.log shows \"Playwright (Python) is not available\" at the J-08 replay step, yet the merged UI report still claims \"LLM browser-qa + deterministic replay\" and reports \"1/1 passed (0 skipped)\" with no replay row and no failure. Only engine.log reveals the gap — a real J-08 regression could have passed unnoticed if the automated suite had not covered it.","**Applies to:** every future iteration (all carry J-08 as required-still-passing) — until `python3 -m pip install --user playwright && python3 -m playwright install chromium` is done, browser QA must explicitly execute required-still-passing browser legs, and the evaluator must demand a result row per required journey rather than trusting the merge header.","","## iter-2 — 2026-07-03T06:00:19+01:00","","**Verdict:** CONTINUE","**Lesson:** Machine-surface journeys (no frontend page) structurally cannot get golden replay scripts: `demo_runner.py` supports only goto/click/fill (no POST) and its `normalize_url` rewrites ANY localhost URL onto the single frontend base_url, so a `goto` aimed at the backend port silently hits the frontend instead. Their durable regression lane is the backend test suite; for browser-originated verification, Chrome MCP's `eval` issuing in-page `fetch()` from a backend-origin page works well (iter-2 drove POST/409/422 flows that way).","**Applies to:** J-03, J-04, J-06, J-07 (all machine-surface per the blueprint IA table) — dispatch browser-qa knowing no replay script will exist for them, and route their required-still-passing coverage through the automated suite, not the replay lane.","","## iter-3 — 2026-07-03T08:34:58+01:00","","**Verdict:** CONTINUE","**Lesson:** Three seemingly unrelated failures this iteration — the replay lane's Playwright Chromium killed at launch (SIGTRAP, engine.log 07:29:19), browser-qa's Chrome `net::ERR_INSUFFICIENT_RESOURCES` + hydration stalls, and sqlite `Disk quota exceeded` errors under pytest — share ONE root cause: `/tmp` is a tmpfs with a per-user quota (~5.2G = 80%), pinned at the limit by ~4.5G of accumulated pytest basetemp dirs in `/tmp/pytest-of-dennis-chan` (~4-5MB per suite run x hundreds of framework runs; pytest's keep-3 cleanup has not kept up). Symptom looks like flaky browsers or a broken product; it is neither. Workaround proven this iteration: run pytest with `TMPDIR` + `--basetemp` pointed at a root-filesystem dir; real fix is clearing the pytest dir (this evaluator's delete was permission-denied — operator action).","**Applies to:** every future iteration's browser-qa / replay / large-suite lane — before diagnosing \"flaky browser\" or unexplained sqlite I/O errors, check `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota first.","","## iter-4 — 2026-07-03T10:17:12+01:00","","**Verdict:** CONTINUE","**Lesson:** The committed fixture dataset pair arms exactly n=1 trade per split under strategy v1's sustain/cooldown rules (train net_r −0.16, holdout net_r +0.3334, both < `pnl_min_sample_size` 5) — the iter-3 note's \"n=5\" figure came from a different substrate. Consequence: on the current fixtures NO candidate can ever satisfy an n ≥ 5 hold-out promotion gate, so J-07's sweep tests must control the configured minimum (both ways) or use enlarged fixture windows to exercise a real promotion; the founding row's insufficient-sample labeling also means J-05's page renders that label from day one with real data.","**Applies to:** J-07 (promotion-gate test design on the fixture pair), J-05 (insufficient-sample rendering is live-data-exercised), any iter asserting sample-size gates against `tests/fixtures/datasets/`","","## iter-5 — 2026-07-03T14:12:54+01:00","","**Verdict:** CONTINUE","**Lesson:** The verify-and-complete resume protocol delivered a zero-churn success: every interrupted-dispatch claim (988/1 suite, equivalence 7/7, build, 2/2 replay) reproduced independently and \"no code changes — verified as-is\" was the correct developer outcome — re-verification, not rebuilding, is the right posture for an uncommitted-but-complete working tree. Side effect to heed: `GET /research/profiles` now serves 200 with a zero-candidate registry (row 33 landed minimally for J-05's champion summary), so J-06's fresh-failing evidence is \"registry lists no candidate\", no longer a 404 — a 200 there must not be misread as J-06 progress.","**Applies to:** any future interrupted-dispatch resume (verify first, change only what a failed check requires); the J-06 iteration's failing-baseline framing and acceptance evidence.","```","Journey state (inline digest; Read runs/goal-session-tape_to_profit/state/journey-history.json only for fields the digest omits):","```","J-01 | passing         | last_passing=goal-tape_to_profit-iter-5 | A read-only MCP server exposes the product over the canonical API","J-02 | passing         | last_passing=goal-tape_to_profit-iter-5 | Historical tape datasets persist and replay byte-identically (train/hold-out registry)","J-03 | passing         | last_passing=goal-tape_to_profit-iter-5 | Strategy grammar v1 backtests a dataset into a deterministic PnL report","J-04 | passing         | last_passing=goal-tape_to_profit-iter-5 | Every enhancement lands one honest row in the PnL ledger","J-05 | passing         | last_passing=goal-tape_to_profit-iter-5 | The /performance page reports PnL per enhancement honestly","J-06 | failing         | last_passing=- | Indicator profiles are versioned; the default stays byte-identical","J-07 | failing         | last_passing=- | The candidate sweep survives hold-out or says so honestly","J-08 | passing         | last_passing=goal-tape_to_profit-iter-5 | The existing product is unchanged (regression sentinel)","```","","Last iteration eval: runs/goal-session-tape_to_profit/iter-5/eval.md","","Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.","","Write the iteration spec to: docs/phases/goal-tape_to_profit-iter-6.md","Also keep runs/goal-session-tape_to_profit/state/blueprint.md current per your agent instructions: register any new displayed value in the Data Contract and place new pages under an existing Information-Architecture home (additive edits only). For a nav-skeleton change, make the edit AND write a one-line reason to runs/goal-session-tape_to_profit/state/blueprint.reapproval-requested.","","The spec MUST include a 'Goal Mode Metadata' section with at minimum:","  - Mode: next","  - Depth: lean | full","  - Target journeys: <comma-separated journey IDs>","","Do NOT write code or implement anything. The iteration spec and any blueprint edits are planning documents, not code. STOP after writing them."],"model":"claude-opus-4-8"}
+{"step":4,"agent":"developer","cli":"claude","backend":"interactive","ts":"2026-07-03T18:21:52Z","exit_code":0,"duration_seconds":2465,"stdout_path":"0004-developer.log","args":["-p","You are the developer agent for goal-mode lean iteration.","","Iteration: goal-tape_to_profit-iter-6","Iter spec: docs/phases/goal-tape_to_profit-iter-6.md","Project goal: docs/goal.md  <-- read Must-have user journeys and Anti-goals","Project template: .claude/project-template.md","Agent instructions: .claude/agents/developer.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","","Mode: INITIAL BUILD","","","This is a LEAN goal-mode iteration. Implement only what the iter spec's IN SCOPE","section calls for. Tighter scope than a full phase. Do NOT introduce features","outside the iter spec's IN SCOPE list.","","When complete:","- Write dev handoff to: docs/handoffs/goal-tape_to_profit-iter-6-dev.md","- Update runs/goal-tape_to_profit-iter-6/status.json with current_step: dev_complete",""],"model":"claude-sonnet-5"}
+{"step":5,"agent":"reviewer","cli":"claude","backend":"interactive","ts":"2026-07-03T18:39:57Z","exit_code":0,"duration_seconds":1085,"stdout_path":"0005-reviewer.log","args":["-p","You are the reviewer agent for goal-mode lean iteration.","","Iteration: goal-tape_to_profit-iter-6","Iter spec: docs/phases/goal-tape_to_profit-iter-6.md","Dev handoff: docs/handoffs/goal-tape_to_profit-iter-6-dev.md","Project template: .claude/project-template.md","Agent instructions: .claude/agents/reviewer.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","","Run: git diff HEAD to see what changed.","","Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.","","Write your review report to: reports/reviews/goal-tape_to_profit-iter-6-review.md","","The report MUST start with a line matching exactly:","**Verdict:** PASS","  or","**Verdict:** PASS_WITH_NOTES","  or","**Verdict:** FAIL",""],"model":"claude-sonnet-5"}
+{"step":6,"agent":"browser-qa-agent","cli":"claude","backend":"interactive","ts":"2026-07-03T18:52:03Z","exit_code":0,"duration_seconds":697,"stdout_path":"0006-browser-qa-agent.log","args":["-p","You are the browser-qa-agent for goal-mode lean iteration.","","Iteration: goal-tape_to_profit-iter-6","Iter spec: docs/phases/goal-tape_to_profit-iter-6.md","Project goal: docs/goal.md  <-- read \"Must-have user journeys\" section for journey definitions","Agent instructions: .claude/agents/browser-qa-agent.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","Skill: .claude/skills/browser-workflow-executor.md  <-- read for Chrome MCP technique","","GOAL-MODE LEAN MODE — test EXACTLY these journeys this run: J-02,J-03,J-04,J-06","Do NOT test these — a deterministic replay verifies them separately: J-01 J-05 J-08 ","  1. For each journey ID above, read its numbered steps + Acceptance line from the project goal's \"Must-have user journeys\" section.","  2. Execute the steps with Chrome MCP; use the journey ID as the test case ID (e.g. UT-J-01).","","Frontend URL: http://localhost:3301","Frontend available: yes","","Chrome MCP browser checks ARE required. Use mcp__plugin_superpowers-chrome_chrome__use_browser.","","For each journey:","  - Execute the numbered steps exactly as written in goal.md","  - Verify the Acceptance condition","  - Take a screenshot of the end state, save to reports/qa/goal-tape_to_profit-iter-6-evidence/","  - Record PASS / FAIL / SKIP with a short failure description if FAIL","","GOLDEN REPLAY SCRIPTS (goal-mode regression speedup): for every journey you verify","PASS, ALSO write a self-contained deterministic replay script to","runs/goal-session-tape_to_profit/journey-scripts/<J-XX>.json (overwrite if present) so future iterations can","re-verify it without a browser-driving model. Follow the 'Golden replay script'","section of your agent instructions for the exact JSON shape. Best-effort: if you","cannot produce one for a journey, skip it (that journey just falls back to the LLM","next time).","","Write your results to: reports/phase-goal-tape_to_profit-iter-6-ui-test-results.llm.md","Use template: templates/ui-test-results.md","Map each journey ID to a UT row.","","The report MUST contain a line at the top:","**Browser QA Verdict:** PASS","  or","**Browser QA Verdict:** FAIL","  or","**Browser QA Verdict:** SKIPPED","","Then STOP."],"model":"claude-sonnet-5"}
+{"step":7,"agent":"coherence-auditor","cli":"claude","backend":"interactive","ts":"2026-07-03T18:56:42Z","exit_code":0,"duration_seconds":278,"stdout_path":"0007-coherence-auditor.log","args":["-p","You are the coherence-auditor agent for goal-mode coherence enforcement.","","Session ID: tape_to_profit","Iteration index: 6","Iter name: goal-tape_to_profit-iter-6","","Blueprint (the contract): runs/goal-session-tape_to_profit/state/blueprint.md","Iter spec: docs/phases/goal-tape_to_profit-iter-6.md","Agent instructions: .claude/agents/coherence-auditor.md  <-- read this first","Methodology: .claude/skills/coherence-audit.md","(CLAUDE.md is already in your system prompt — do not Read it again.)","","This iteration's changes: run `git diff 14a7ea463f4cc674e1721d253e897cd6178f2277` (and `git status` / `git diff HEAD` for uncommitted changes). If the snapshot SHA is empty, fall back to `git diff HEAD~1`.","UI surface map (read if it exists): reports/phase-goal-tape_to_profit-iter-6-ui-surface-map.md","","Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.","","Write your verdict to: runs/goal-session-tape_to_profit/iter-6/coherence.md","The verdict line MUST appear first and start exactly with:","**Verdict:** COHERENCE-PASS","  or **Verdict:** COHERENCE-WARN","  or **Verdict:** COHERENCE-FAIL"],"model":"claude-sonnet-5"}
diff --git aruns/goal-tape_to_profit-iter-6/status.json bruns/goal-tape_to_profit-iter-6/status.json
new file mode 100644
index 0000000..2b441c7
--- /dev/null
+++ bruns/goal-tape_to_profit-iter-6/status.json
@@ -0,0 +1,22 @@
+{
+  "phase": "goal-tape_to_profit-iter-6",
+  "status": "in_progress",
+  "current_step": "dev_complete",
+  "updated_at": "2026-07-03T18:20:38.000000Z",
+  "started_at": "2026-07-03T17:45:00.000000Z",
+  "cli": "claude",
+  "blockers": [],
+  "changed_files": [
+    "apps/backend/app/config.py",
+    "apps/backend/app/research/backtests.py",
+    "apps/backend/app/research/profiles.py",
+    "apps/backend/app/research/routes.py",
+    "apps/backend/tests/test_profile_equivalence.py",
+    "apps/backend/tests/test_profiles_api.py",
+    "apps/backend/tests/test_backtests_api.py"
+  ],
+  "tests_run": true,
+  "browser_checks_run": false,
+  "next_action": "review",
+  "notes": "J-06 (versioned indicator profiles): registered ONE additive candidate profile (candidate-faster-warmup, an alternate warmup_min_events threshold) in a config-owned registry (Config.profile_definition/profile_registry/resolved_for_profile, mirroring the existing strategy_definition pattern). Retired the hardcoded profile != default 422 check in routes.py in favor of the ONE registry. The backtest runner applies the resolved profile ONLY inside its own fresh per-run engine construction (dataclasses.replace, never mutating the shared CONFIG singleton). Empirically verified the candidate legitimately flips tape_state earlier on the committed PG SIP fixture (both founding train/holdout windows) and produces a materially different holdout backtest trade, while the train trade and the ENTIRE default-profile path stay byte-identical (fingerprint pinned to the pre-existing 4d665603569b9dbf; candidate resolves to a distinct 8c2c0fbf978228e3 via the SAME hasher). Full backend suite: 1004 passed, 1 skipped (988+1 baseline + 16 new J-06 tests, 0 failed, 0 deleted). Frontend needed zero code changes — the existing /performance registry panel already renders profiles generically; verified live via curl + npm build. No frontend handoff file written (no frontend diff exists). RESUME SESSION (verify-and-complete): this dispatch found the implementation already complete and uncommitted in the working tree with this exact handoff already written by a prior invocation. Made zero code changes; independently re-verified every DoD item from scratch — fresh full-suite run (1004 passed/1 skipped/0 failed, confirmed via grep for FAILED/ERROR), fresh live-server curl checks for all three profile-validation paths (default/candidate/unknown) with both queued- and terminal-stamp fingerprints matching the pinned values live, a full stop/restart cycle of scripts/dev.sh with no port conflicts, and confirmation that every OUT-OF-SCOPE file (pnl_ledger.py, pnl_baseline.py, pnl_history.py, pnl-history.md, app/mcp/, apps/frontend/) has zero diff. See the dev handoff's new 'Resume posture — verify-and-complete (this session)' section for full detail."
+}
```
