# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/research/vault.py b/apps/backend/app/research/vault.py
index 809b4c5..e14e794 100644
--- a/apps/backend/app/research/vault.py
+++ b/apps/backend/app/research/vault.py
@@ -1483,6 +1483,17 @@ def unresolved_pool_dataset_ids(
 # === GET /research/desk/micro/vault (served verbatim, no second computation in the route) ==========
 
 
+def _coarsen_sealed_at_to_date(sealed_at: str) -> str:
+    """Iteration 24: the served-only precision narrowing ``_serialize_shard`` applies to
+    ``sealed_at``. ``_iso_utc_now`` always produces ``YYYY-MM-DDTHH:MM:SS.ffffffZ`` (module's own
+    ``isoformat(timespec="microseconds")`` format), so the date component is exactly the first 10
+    characters -- no parse/reformat round-trip needed, and none of the ``+00:00``/``Z`` suffix
+    handling above this function's call site can affect a slice that never reaches it. A single
+    slice point (called from exactly one place, ``_serialize_shard``) means there is nowhere else
+    for a full-precision value to leak back in."""
+    return sealed_at[:10]
+
+
 def _serialize_shard(row: dict) -> dict:
     """Section 7.5's three-stage reveal, as an explicit whitelist per stage -- never ``dict(row)``,
     so neither a ledger-internal key (``row_hash``/``prev_hash``/``row_index``) nor a sealed-side
@@ -1502,8 +1513,26 @@ def _serialize_shard(row: dict) -> dict:
     ``exposure_unknown``), which would have disclosed symbol/date for any unrecognised state; r8
     (module docstring) removed the fourth state, and the whitelist form makes the serving layer
     fail CLOSED on an unrecognised one rather than depending on the exhaustiveness of a
-    blacklist."""
+    blacklist.
+
+    **Iteration 24: ``sealed_at`` is coarsened to date-only precision at this serve-time
+    projection point, for every state alike.** The stored ledger row (written by ``seal_shard``,
+    carried forward byte-identical through ``assign_shard``/``expose_shard`` via ``_row_content``)
+    keeps its original microsecond-precision ISO timestamp forever -- append-only discipline, never
+    rewritten. Coarsening only ``opaque["sealed_at"]`` here (rather than each state's dict
+    separately) is what makes the narrowing apply uniformly to ``sealed``, ``assigned`` AND
+    ``exposed`` rows alike (TC-9): ``revealed`` below is built as ``{**opaque, ...}``, so it
+    inherits the already-coarsened value with no second call site to remember. The reason: a
+    full-precision ``sealed_at`` is itself a side channel (closed by the iter-23 audit finding) --
+    joined against the committed per-run ``sealed_this_run`` counts in
+    ``reports/j06-tranche/recording-runs.json``, a fine-grained seal instant can narrow which
+    run (and, combined with that run's small count, which few candidate identities) a given
+    still-sealed shard belongs to, in tension with the r5 opaque-pool rule this module exists to
+    enforce. Date-only precision keeps the field meaningful (still visibly grouped by day) while
+    collapsing same-day seals -- which every real run so far has been -- into one indistinguishable
+    bucket."""
     opaque = {key: row[key] for key in _OPAQUE_SHARD_KEYS}
+    opaque["sealed_at"] = _coarsen_sealed_at_to_date(opaque["sealed_at"])
     state = row["exposure_state"]
     if state not in (STATE_ASSIGNED, STATE_EXPOSED):
         return opaque
diff --git a/apps/backend/scripts/j06_operator.py b/apps/backend/scripts/j06_operator.py
index ad8eb06..294e02e 100644
--- a/apps/backend/scripts/j06_operator.py
+++ b/apps/backend/scripts/j06_operator.py
@@ -745,10 +745,81 @@ def residual_pool_uncertainty(
     }
 
 
+RECORDING_RUNS_PATH = STATE_DIR / "recording-runs.json"
+
+
+def _load_recording_runs(path: Path = RECORDING_RUNS_PATH) -> list[dict]:
+    """The committed §8 run ledger (``reports/j06-tranche/recording-runs.json``) -- read-only,
+    never written by this stage (record-integrity: iteration 24 narrows what is SERVED going
+    forward, it does not retroactively edit a committed operator report)."""
+    return json.loads(path.read_text())["runs"]
+
+
+def residual_pool_uncertainty_by_run_time_bucket(
+    runs: list[dict], served_sealed_at_values: list[str]
+) -> dict:
+    """The RUN-AWARE half of TR-2 (iteration 24, closing the sealing-time leak the iter-23 audit
+    found): the combinatorial half above never reads ``recording-runs.json`` at all, so a channel
+    that joins the committed per-run ``sealed_this_run`` counts against the SERVED per-shard
+    ``sealed_at`` values was a genuine blind spot -- a future run could narrow a still-sealed
+    shard's identity through this join without the automated check ever seeing it.
+
+    Deliberately generic over whatever PRECISION ``served_sealed_at_values`` carries -- it buckets
+    both sides by that precision (a run's own ``at`` timestamp truncated to the same length),
+    rather than hardcoding "date-only". Fed the REAL, now-coarsened (date-only) served values, every
+    run sealed on the same calendar day collapses into ONE bucket, so the residual candidate count
+    per bucket is the number of still-currently-sealed shards sharing that day -- today, all 21 fall
+    on one day, so the floor comfortably holds. Fed any full-precision reproduction of the OLD
+    served shape instead (the iter-24 non-vacuity counter-tests), the same logic instead separates
+    the runs from each other -- and since each shard's own seal instant is distinct at that
+    precision, every bucket collapses to a candidate count of 1, correctly BELOW the floor.
+
+    Asserted against the SAME existing floor ``residual_pool_uncertainty`` already enforces
+    (``candidate_identities_per_unexposed_selected_shard >= 2``) -- no new floor number invented
+    here."""
+    if not served_sealed_at_values:
+        return {"buckets": {}, "any_bucket_below_floor": False, "worst_bucket_candidates": None}
+
+    bucket_len = len(served_sealed_at_values[0])
+    run_sealed_by_bucket: dict[str, int] = {}
+    for run in runs:
+        key = str(run.get("at", ""))[:bucket_len]
+        run_sealed_by_bucket[key] = run_sealed_by_bucket.get(key, 0) + int(run.get("sealed_this_run", 0))
+
+    served_by_bucket: dict[str, int] = {}
+    for value in served_sealed_at_values:
+        served_by_bucket[value] = served_by_bucket.get(value, 0) + 1
+
+    # Iterate the SERVED buckets, not the run buckets (iteration-24 audit finding B1). The
+    # attacker's starting point is a served `sealed_at` value, so EVERY served value must sit in an
+    # anonymity set of >= 2 -- including one that no run's own bucket claims. Walking the run
+    # buckets instead (and skipping a bucket with `run_sealed_count <= 0`) made the check silently
+    # blind at fine precision: a run's `at` is stamped at the END of the run by `_utc()`
+    # (second precision) while each shard's `sealed_at` is stamped per-seal by `vault._iso_utc_now`
+    # (microsecond precision), so at full precision NO served value ever prefix-equals a run key,
+    # every bucket was skipped, and the check reported "safe" against exactly the leak it exists to
+    # catch. Keyed on the served value, the same fine precision instead gives each shard its own
+    # bucket of 1 -- correctly BELOW the floor. `sealed_this_run_total` stays in the record (0 when
+    # no run claims the bucket, itself a finding worth reading) but never gates.
+    buckets = {}
+    for key, served_count in served_by_bucket.items():
+        buckets[key] = {
+            "sealed_this_run_total": run_sealed_by_bucket.get(key, 0),
+            "currently_sealed_served_count": served_count,
+            "candidate_identities_per_unexposed_selected_shard": served_count,
+        }
+    candidate_counts = [b["candidate_identities_per_unexposed_selected_shard"] for b in buckets.values()]
+    return {
+        "buckets": buckets,
+        "any_bucket_below_floor": any(c < 2 for c in candidate_counts),
+        "worst_bucket_candidates": min(candidate_counts) if candidate_counts else None,
+    }
+
+
 def stage_tr2() -> dict:
     """TR-2 re-run with the disclosure treated as attacker-known public information.
 
-    Two independent halves, because the leak has two shapes:
+    Three independent halves, because the leak has three shapes:
 
     (1) COMBINATORIAL. The attacker knows the registered universe (80 pairs), the publicly
         published selected COUNT, and now that one specific position is non-selected. Certainty
@@ -759,6 +830,11 @@ def stage_tr2() -> dict:
 
     (2) OBSERVATIONAL. Every genuine J-06 dataset must still be withheld from the served surfaces
         by the shared opaque-pool predicate, so no listing can be differenced against the universe.
+
+    (3) RUN-AWARE (iteration 24). The committed per-run ``sealed_this_run`` counts
+        (``reports/j06-tranche/recording-runs.json``) joined against the SERVED per-shard
+        ``sealed_at`` values -- the channel (1) and (2) do not model at all. See
+        ``residual_pool_uncertainty_by_run_time_bucket`` above.
     """
     uled, shled, _sled, store, ddir = _ledgers()
     universe = vault.find_universe(uled, UNIVERSE_ID)
@@ -799,17 +875,29 @@ def stage_tr2() -> dict:
         "legacy_datasets_visible_by_design": len(by_id) - len(withheld),
     }
 
+    # --- (3) the run-aware half, against the REAL committed run report + REAL served state -------
+    runs = _load_recording_runs()
+    served_state = vault.build_vault_state(shled, uled)
+    served_sealed_at_values = [
+        entry["sealed_at"] for entry in served_state["shards"]
+        if entry.get("universe_id") == UNIVERSE_ID
+        and entry.get("exposure_state") == vault.STATE_SEALED
+    ]
+    run_aware = residual_pool_uncertainty_by_run_time_bucket(runs, served_sealed_at_values)
+
     ok = (not combinatorial["any_identity_certain"]
           and combinatorial["candidate_identities_per_unexposed_selected_shard"] >= 2
-          and observational["leaked_to_served_surfaces"] == 0)
+          and observational["leaked_to_served_surfaces"] == 0
+          and not run_aware["any_bucket_below_floor"])
     out = {"stage": "tr2_disclosure_analysis", "universe_id": UNIVERSE_ID, "at": _utc(),
            "attacker_knowledge": [
                "the registered universe rule (8 symbols x 10 dates = 80 pairs)",
                "every served/public artifact, including the published selected COUNT",
                "the legacy-dataset collision at one registered pair",
                f"the disclosed non-selected pool position(s): {len(disclosed)}",
-               "readiness / dataset / run / UI / MCP surfaces"],
-           "combinatorial": combinatorial, "observational": observational,
+               "readiness / dataset / run / UI / MCP surfaces",
+               "the committed per-run sealed_this_run counts, joined against served sealed_at"],
+           "combinatorial": combinatorial, "observational": observational, "run_aware": run_aware,
            "no_identity_determinable_with_certainty": ok}
     _write("tr2-disclosure-analysis.json", out)
     if not ok:
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index c1d3ee4..0c332bb 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -52,6 +52,16 @@
 # long-standing rule ("use a fresh root whenever the seeded composition changed") applies to this
 # extension exactly as it would to detector logic.
 #
+# goal-rapid-microscope-iter-24 extends this file once more, again in place: after the iter-18
+# graduation seed step, it also runs seed_micro_scout_iter24_j09_fixture.py (a real
+# setup_id="capitulation" playbook signal anchored on the already-staged real PG SIP tick dataset,
+# then a real scout.register_screen_and_walkforward_check() call — never a hand-rolled JSON blob)
+# so journey-scripts/J-09.json's own golden replay finally has a genuine, non-vacuous pilot-study
+# Scout Ledger row to assert against on this rig, instead of the honest-but-non-discriminating
+# empty state every prior pass recorded for J-09's own sections. Reuses the ALREADY-STAGED PG
+# dataset the iter-2 extension above copies in, so no new dataset (hence no new collision surface)
+# is introduced.
+#
 # goal-rapid-microscope-iter-18 extends this file once more, again in place: after the tick-dataset
 # fixtures above stage, it also runs seed_micro_graduation_iter18_fixture.py (a plain dataset +
 # vault-shard + real evaluate_sealed_verdict() call, never a hand-rolled JSON blob) so J-07's own
@@ -120,6 +130,12 @@ export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"
 # own docstring for the full seven-step sequence this exercises for real.
 "$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_graduation_iter18_fixture.py" "$ROOT"
 
+# goal-rapid-microscope-iter-24 (J-09): seed ONE real, non-vacuous pilot-study (Study 3,
+# capitulation_exhaustion_pilot) Scout Ledger row through the real
+# scout.register_screen_and_walkforward_check() production entry point -- see
+# seed_micro_scout_iter24_j09_fixture.py's own docstring for the full sequence this exercises.
+"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_scout_iter24_j09_fixture.py" "$ROOT"
+
 # goal-rapid-microscope-iter-19 (TC-9): the ONE list of store-root vars this launch bound the
 # backend to -- shared by the stderr echo below AND the durable manifest file, so the two can never
 # silently diverge. Closes iteration 18's evaluator finding ("the quality report states that the
diff --git a/apps/backend/tests/test_j06_operator.py b/apps/backend/tests/test_j06_operator.py
index e628e4a..91138e9 100644
--- a/apps/backend/tests/test_j06_operator.py
+++ b/apps/backend/tests/test_j06_operator.py
@@ -23,6 +23,8 @@ Every trap here carries its own counter-test: the pre-fix behaviour is exercised
 passing assertion proves the fix bites rather than that the scenario never arises.
 """
 
+from datetime import datetime, timedelta, timezone
+
 import pytest
 
 from app.research import vault
@@ -269,6 +271,124 @@ def test_uncertainty_holds_for_every_disclosure_count_short_of_the_collapse_poin
     assert r["any_identity_certain"] is False
 
 
+# === §4 widened, iteration 24: the run-aware half that closes the sealing-time leak ================
+#
+# The combinatorial half above never reads `reports/j06-tranche/recording-runs.json` at all -- the
+# iter-23 audit's own genuine finding. These tests exercise the widened check against the REAL
+# committed run report (`op._load_recording_runs()`, no fixture stand-in -- its 7/13/1/0/0 split
+# and four `2026-08-21` + one `2026-08-22` run timestamps are read directly off disk) crossed with
+# a served-`sealed_at` list built the SAME way the real route builds it: through the real, production
+# `vault._coarsen_sealed_at_to_date` function, never a hand-rolled slice reimplemented in the test.
+
+
+def test_iter24_run_aware_check_passes_against_the_real_recording_runs_and_coarsened_sealed_at():
+    """(a) TC-3's own contract: given the REAL committed run report and sealed_at served at the
+    REAL (iteration-24, date-only) precision, every run-time-bucket's residual candidate count is
+    `>= 2` and the check reports no violation. Reproduces today's actual shape -- all four
+    2026-08-21 runs collapse into ONE date bucket (7+13+1+0=21 candidates), comfortably above the
+    floor; the fifth run's 2026-08-22 bucket sealed nothing (`sealed_this_run=0`) so it contributes
+    no bucket at all."""
+    runs = op._load_recording_runs()
+    assert [r["sealed_this_run"] for r in runs] == [7, 13, 1, 0, 0]  # today's real, on-record split
+
+    served_sealed_at_values = []
+    for run in runs:
+        coarsened = vault._coarsen_sealed_at_to_date(run["at"])
+        served_sealed_at_values.extend([coarsened] * run["sealed_this_run"])
+    assert len(served_sealed_at_values) == 21
+
+    result = op.residual_pool_uncertainty_by_run_time_bucket(runs, served_sealed_at_values)
+
+    assert result["any_bucket_below_floor"] is False
+    assert result["worst_bucket_candidates"] >= 2
+    assert result["buckets"] == {
+        "2026-08-21": {
+            "sealed_this_run_total": 21,
+            "currently_sealed_served_count": 21,
+            "candidate_identities_per_unexposed_selected_shard": 21,
+        }
+    }
+
+
+def test_iter24_the_same_widened_check_correctly_FAILS_against_the_old_full_precision_join():
+    """(b) The non-vacuity counter-test (the Study-3 break-then-restore precedent, applied to a
+    check rather than a fix): feed the SAME widened logic a synthetic reproduction of the OLD,
+    pre-iteration-24 full-precision `sealed_at` -- each shard's served value literally equal to its
+    OWN run's `at` timestamp, joined against the SAME real 7/13/1/0/0 split -- and prove it
+    correctly reports a violation. Without this, `any_bucket_below_floor is False` above would be
+    unfalsifiable -- it could be `False` because the check never actually looks, not because the
+    real data is safe."""
+    runs = op._load_recording_runs()
+
+    served_full_precision_sealed_at_values = []
+    for run in runs:
+        served_full_precision_sealed_at_values.extend([run["at"]] * run["sealed_this_run"])
+    assert len(served_full_precision_sealed_at_values) == 21
+
+    result = op.residual_pool_uncertainty_by_run_time_bucket(runs, served_full_precision_sealed_at_values)
+
+    assert result["any_bucket_below_floor"] is True
+    # the third 2026-08-21 run sealed exactly one shard -- under full precision that shard is the
+    # UNIQUE candidate in its own bucket, the exact identification the r5 floor exists to prevent.
+    assert result["worst_bucket_candidates"] == 1
+    third_run_at = runs[2]["at"]
+    assert runs[2]["sealed_this_run"] == 1
+    assert result["buckets"][third_run_at]["candidate_identities_per_unexposed_selected_shard"] == 1
+
+
+def test_iter24audit_the_widened_check_also_fails_against_a_REALISTIC_old_full_precision_shape():
+    """Iteration-24 audit finding B1 -- the counter-test above is necessary but NOT sufficient: it
+    feeds each shard's served value as its own run's ``at`` string, an alignment that cannot occur
+    in production. A run's ``at`` is stamped once at the END of the run by
+    ``j06_operator._utc()`` (SECOND precision, ``2026-08-21T16:43:09Z``), while each shard's
+    ``sealed_at`` is stamped per-seal by ``vault._iso_utc_now()`` (MICROSECOND precision,
+    ``2026-08-21T16:42:19.876544Z``) -- so under the genuine pre-iteration-24 served shape no
+    served value ever equalled a run key.
+
+    Against the ORIGINAL implementation (which walked the RUN buckets and skipped any bucket a run
+    did not claim) that meant zero buckets, ``any_bucket_below_floor: False`` -- the widened check
+    reporting "safe" against exactly the leak it was built to catch. Keyed on the SERVED bucket
+    instead, each distinct full-precision instant is its own anonymity set of ONE, and the floor
+    correctly bites."""
+    runs = op._load_recording_runs()
+
+    # a faithful reconstruction of what `seal_shard` actually wrote per shard: distinct
+    # microsecond-precision instants shortly BEFORE their own run's `at`, never equal to it.
+    served_realistic_old_shape = []
+    for run in runs:
+        run_end = datetime.strptime(run["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
+        n = run["sealed_this_run"]
+        for i in range(n):
+            instant = run_end - timedelta(seconds=(n - i) * 7, microseconds=123456 + i)
+            served_realistic_old_shape.append(
+                instant.isoformat(timespec="microseconds").replace("+00:00", "Z")
+            )
+    assert len(served_realistic_old_shape) == 21
+    assert len(set(served_realistic_old_shape)) == 21           # every instant distinct...
+    assert not set(served_realistic_old_shape) & {r["at"] for r in runs}   # ...and none is a run key
+
+    result = op.residual_pool_uncertainty_by_run_time_bucket(runs, served_realistic_old_shape)
+
+    assert result["any_bucket_below_floor"] is True
+    assert result["worst_bucket_candidates"] == 1
+    assert len(result["buckets"]) == 21
+    assert all(
+        b["candidate_identities_per_unexposed_selected_shard"] == 1 for b in result["buckets"].values()
+    )
+
+
+def test_iter24_stage_tr2_source_wires_the_run_aware_half_into_its_own_ok_gate():
+    """Structural companion (the `test_the_preflight_stop_is_not_weakened...` precedent above): pins
+    that `stage_tr2`'s own pass/fail gate actually consults the widened check's verdict, rather than
+    computing it and discarding the result -- the failure mode a passing test-suite could otherwise
+    hide."""
+    import inspect
+
+    source = inspect.getsource(op.stage_tr2)
+    assert "residual_pool_uncertainty_by_run_time_bucket" in source
+    assert 'not run_aware["any_bucket_below_floor"]' in source
+
+
 def test_the_recorder_walk_derives_already_recorded_from_the_genuine_shard_predicate():
     """Structural companion to the repair: the walk must key off ``_recorded_pairs`` (hence
     ``is_genuine_j06_dataset``), never off a second, drifting "some dataset exists here" map. The
diff --git a/apps/backend/tests/test_vault.py b/apps/backend/tests/test_vault.py
index ccbc08a..dcc9ffc 100644
--- a/apps/backend/tests/test_vault.py
+++ b/apps/backend/tests/test_vault.py
@@ -20,6 +20,7 @@ from __future__ import annotations
 
 import hashlib
 import json
+import re
 import shutil
 import time
 from pathlib import Path
@@ -289,6 +290,84 @@ def test_tc6_a_sealed_shards_entry_carries_only_the_section_7_5_opaque_fields(tm
     assert _SEALED_CONTENT_CHECKSUM not in json.dumps(entry)
 
 
+# === Iteration 24: the sealing-time-leak close -- served `sealed_at` is coarsened to date-only,
+# while the underlying ledger row keeps its full precision (serve-time-only, never a ledger
+# rewrite). TC-1/TC-2/TC-9. ===========================================================================
+
+_DATE_ONLY_SHAPE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
+
+
+def test_tc1_a_sealed_rows_served_sealed_at_is_date_only_precision(tmp_path):
+    shard_ledger = _sealed_shard_ledger(tmp_path)
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+
+    entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
+
+    assert _DATE_ONLY_SHAPE.match(entry["sealed_at"]), entry["sealed_at"]
+    # the fixture's own full-precision seal instant (`_sealed_shard_ledger` lets `seal_shard`
+    # default it via `_iso_utc_now`) always starts with the served value -- proving this is a
+    # genuine coarsening of the SAME instant, not an unrelated string.
+    stored_full_precision = shard_ledger.all_rows()[0]["sealed_at"]
+    assert stored_full_precision.startswith(entry["sealed_at"])
+    assert stored_full_precision != entry["sealed_at"]  # the time-of-day component was dropped
+
+
+def test_tc2_the_underlying_ledger_rows_sealed_at_stays_full_precision_never_rewritten(tmp_path):
+    """Proves the coarsening in `_serialize_shard` is a serve-time-only projection: reading the
+    shard ledger DIRECTLY (bypassing `build_vault_state`/`_serialize_shard` entirely) must still
+    show the original microsecond-precision ISO timestamp `seal_shard` wrote -- append-only
+    discipline holds, nothing on disk was rewritten to accommodate the narrower served shape."""
+    explicit_sealed_at = "2026-06-09T14:32:07.481932Z"
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    vault.seal_shard(
+        shard_ledger, dataset_id=_SEALED_DATASET_ID, universe_id="u1",
+        content_checksum=_SEALED_CONTENT_CHECKSUM, event_count=45_231,
+        vault_secret=_FIXTURE_SECRET, sealed_at=explicit_sealed_at,
+    )
+
+    stored_row = shard_ledger.all_rows()[0]
+    assert stored_row["sealed_at"] == explicit_sealed_at  # byte-identical, untouched
+
+    served_entry = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(str(tmp_path / "vault")))["shards"][0]
+    assert served_entry["sealed_at"] == "2026-06-09"
+    assert stored_row["sealed_at"] != served_entry["sealed_at"]  # the two are genuinely different
+
+
+def test_tc9_assigned_and_exposed_rows_also_serve_a_date_only_sealed_at(tmp_path):
+    """TC-9: the coarsening is uniform across all three exposure states, not sealed-only -- an
+    `assigned` or `exposed` shard's served `sealed_at` (inherited unchanged from its original
+    sealed row, per `_row_content`) narrows exactly the same way."""
+    explicit_sealed_at = "2026-06-09T14:32:07.481932Z"
+    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
+    vault.seal_shard(
+        shard_ledger, dataset_id=_SEALED_DATASET_ID, universe_id="u1",
+        content_checksum=_SEALED_CONTENT_CHECKSUM, event_count=45_231,
+        vault_secret=_FIXTURE_SECRET, sealed_at=explicit_sealed_at,
+    )
+    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
+    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
+
+    vault.assign_shard(
+        shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root,
+        symbol="PG", session_date="2026-06-09",
+    )
+    assigned_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
+    assert assigned_entry["exposure_state"] == "assigned"
+    assert _DATE_ONLY_SHAPE.match(assigned_entry["sealed_at"])
+    assert assigned_entry["sealed_at"] == "2026-06-09"
+
+    vault.expose_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root)
+    exposed_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
+    assert exposed_entry["exposure_state"] == "exposed"
+    assert _DATE_ONLY_SHAPE.match(exposed_entry["sealed_at"])
+    assert exposed_entry["sealed_at"] == "2026-06-09"
+
+    # the underlying ledger rows for BOTH transitions still carry the original full-precision
+    # value verbatim (`_row_content` carries it forward unchanged) -- never rewritten anywhere.
+    for stored_row in shard_ledger.all_rows():
+        assert stored_row["sealed_at"] == explicit_sealed_at
+
+
 def test_r3_the_served_shard_id_is_a_surrogate_with_no_derivable_relation_to_the_dataset_id(tmp_path):
     """Spec section 7.5 point 1: "not the id, not a hash of it, not a prefix". Each of those three
     is checked literally, plus the property that makes the surrogate non-derivable at all -- it is
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index d076ca9..7069436 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -6798,7 +6798,13 @@ function ValidationVaultSection({
                       {shard.checksum_commitment}
                     </td>
                     <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
-                      {formatDateTimeET(shard.sealed_at, { seconds: false })}
+                      {/* A DAY MARKER since iteration 24 (`vault._serialize_shard` coarsens the
+                          served `sealed_at` to `yyyy-MM-dd`), so it is read LEXICALLY --
+                          `formatDateTimeET` would parse the bare date as UTC midnight and
+                          render it as the PREVIOUS day plus a 19:00-20:00 ET time that was
+                          never in the record. `assigned_at`/`exposed_at` below are still
+                          genuine instants and keep the instant formatter. */}
+                      {formatDayMarker(shard.sealed_at)}
                     </td>
                     <td className="px-1.5 py-1 text-slate-300">{shard.exposure_state}</td>
                     {shard.exposure_state === "sealed" ? (
diff --git a/apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py b/apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py
new file mode 100644
index 0000000..c6011ce
--- /dev/null
+++ b/apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py
@@ -0,0 +1,197 @@
+"""Plants a real pilot-study Scout Ledger row for J-09's stored golden replay (era "The Rapid
+Microscope", goal-rapid-microscope-iter-24).
+
+**Why this exists.** ``journey-scripts/J-09.json`` is a pure browser-action replay script
+(``goto``/``click``/``expect`` only -- ``demo_runner.py`` has no raw-HTTP action type), so it
+cannot itself issue the ``POST /research/desk/micro/scout/compute`` call that would trigger a
+pilot-study screen, and the ``/desk`` frontend's own Scout compute button sends only the default
+reference grid (no UI control selects a pilot grid). This script is the one-time fixture-seeding
+act the iteration plan calls for: it plants a genuine, non-vacuous Study-3
+(``capitulation_exhaustion_pilot``) Scout Ledger row through the REAL production entry point
+(``scout.register_screen_and_walkforward_check`` -- never a hand-rolled JSON blob), so the
+resulting row is already on disk when the golden replay's ``goto``/``click``/``expect`` steps run
+against the scoped QA rig. Mirrors the ``seed_micro_graduation_iter18_fixture.py`` precedent
+(J-07/``micro_graduation.py``), applied here to J-09/``scout.py``.
+
+**What this plants.** ONE real ``setup_id="capitulation"`` playbook signal -- the SAME
+``_plant_capitulation_signal(tmp_path, dataset_meta=...)`` shape ``tests/test_scout.py``'s own
+``test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor`` already proves
+produces a genuine, non-vacuous screen -- anchored on the FIRST already-staged real PG SIP tick
+dataset this rig's own ``qa_playbook_iter7_fixture_scoped_backend.sh`` copies into
+``$ROOT/datasets`` BEFORE any seeder runs (never a second, synthetic dataset: the real committed
+historical PG fixture is the exact same, already-proven-workable anchor target
+``tests/test_scout.py``'s own ``pg_snapshot_store`` fixture uses). Then calls
+``scout.register_screen_and_walkforward_check`` for real (Study 3's own frozen request from
+``scout.pilot_study_candidate_grid``), writing through the SAME scout ledger dir
+``GET /research/desk/micro/scout`` reads from when the scoped backend serves the same
+``TAPEOLOGY_DATASET_DIR``.
+
+**Never touches the real ``.data`` store.** Every directory this script writes to is derived from
+the ``root`` argument's own ``TAPEOLOGY_DATASET_DIR``-relative resolvers
+(``resolve_scout_ledger_dir``, ``resolve_micro_exposure_registry_dir``,
+``resolve_micro_snapshots_dir`` -- the SAME sibling-of-dataset-dir defaults every other era module
+uses, and the SAME ones ``GET /research/desk/micro/scout`` resolves when it serves this rig); the
+rig's playbook store path (``TAPEOLOGY_DESK_PLAYBOOK_DIR``, already exported by the launcher) is
+reused verbatim, not re-derived, so the signal this script plants and the one the served ``/desk``
+Playbook section reads are the SAME store.
+
+Uses a distinct ``playbook_input_signature``
+(``"goal-rapid-microscope-iter24-j09-capitulation-pilot"``) so this signal can never collide with
+anything ``seed_playbook_iter8_replay_rig.py`` or any other seed script in this rig already
+planted -- ``PlaybookStore.record``'s own duplicate-key discipline is keyed on
+``(session_date, playbook_input_signature)``, never on ``setup_id`` alone: multiple signals
+coexist at the same session date routinely (``_plant_capitulation_signal``'s own two-signal test
+in ``tests/test_scout.py`` proves exactly this).
+
+**Never a production code path change.** This script imports and calls the SAME
+``scout.register_screen_and_walkforward_check``/``PlaybookStore.record``/
+``run_snapshot_build_and_record`` functions the shipped product uses; it adds no new module, no
+new endpoint, no new branch inside any of them.
+
+Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports
+``TAPEOLOGY_DATASET_DIR``/``TAPEOLOGY_DESK_PLAYBOOK_DIR``/``TAPEOLOGY_DESK_UNIVERSE_DIR`` first,
+AFTER the PG tick fixtures are copied and after the other seed scripts have run):
+
+    TAPEOLOGY_DATASET_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
+      .venv/bin/python scripts/seed_micro_scout_iter24_j09_fixture.py ROOT
+"""
+
+from __future__ import annotations
+
+import os
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+from zoneinfo import ZoneInfo
+
+_SCRIPTS_DIR = Path(__file__).resolve().parent
+sys.path.insert(0, str(_SCRIPTS_DIR))
+sys.path.insert(0, str(_SCRIPTS_DIR.parent))
+
+from app.config import CONFIG  # noqa: E402
+from app.research import scout  # noqa: E402
+from app.research.datasets import DatasetStore, parse_utc_epoch  # noqa: E402
+from app.research.desk_playbook import PlaybookStore, playbook_parameters  # noqa: E402
+from app.research.desk_playbook import resolve_desk_playbook_dir  # noqa: E402
+from app.research.micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir  # noqa: E402
+from app.research.micro_snapshots import resolve_micro_snapshots_dir, run_snapshot_build_and_record  # noqa: E402
+from app.research.scout_ledger import ScoutLedger, resolve_scout_ledger_dir  # noqa: E402
+
+_PLAYBOOK_INPUT_SIGNATURE = "goal-rapid-microscope-iter24-j09-capitulation-pilot"
+_ET_ZONE = ZoneInfo("America/New_York")
+
+
+def _session_date_of(dataset_meta: dict) -> str:
+    """The dataset's ET session date, derived from its own recorded window -- the
+    ``j06_operator._session_date_of`` shape, mirrored (never re-derived from a hardcoded guess)."""
+    start = datetime.fromisoformat(dataset_meta["window_start_utc"].replace("Z", "+00:00"))
+    return start.astimezone(_ET_ZONE).date().isoformat()
+
+
+def _first_real_pg_dataset(dataset_store: DatasetStore) -> dict:
+    """The FIRST already-staged real PG SIP tick dataset this rig's launcher copies into
+    ``$ROOT/datasets`` before any seeder runs -- the SAME real committed fixture
+    ``tests/test_scout.py``'s own ``pg_snapshot_store`` fixture reads (never a second, synthetic
+    dataset). Sorted by id for a deterministic pick across repeated rig launches."""
+    records, _errors = dataset_store.list()
+    pg = sorted((r for r in records if r["symbol"] == "PG"), key=lambda r: r["id"])
+    if not pg:
+        raise SystemExit(
+            "[seed-micro-scout-iter24-j09] no PG dataset found in the dataset store -- this "
+            "seeder must run AFTER the rig's own PG SIP tick-fixture copy step, never before it"
+        )
+    return pg[0]
+
+
+def _plant_capitulation_signal(playbook_dir: str, *, dataset_meta: dict) -> PlaybookStore:
+    """ONE real ``setup_id="capitulation"`` playbook signal, ``trigger_ts`` inside
+    ``dataset_meta``'s own window -- the ``tests/test_scout.py`` ``_plant_capitulation_signal``
+    shape, mirrored, against the RIG's own playbook store dir rather than a throwaway
+    ``tmp_path``, with ONE deliberate addition: ``"side": "long"``.
+
+    ``_plant_capitulation_signal`` itself omits ``side`` (harmless for its own callers -- Scout's
+    ``join_playbook_signal`` never reads it), but a REAL ``detect_capitulation`` signal always
+    carries it (``desk_playbook_detect.py``'s own ``"capitulation entry, long only"`` -- every
+    real signal dict is built with ``"side": "long"`` verbatim, never omitted). This rig's own
+    ``/research/desk/referee/registry/shortlist`` route reads EVERY playbook signal at the live
+    detector basis (``referee_evidence.playbook_occurrence_readiness``, keyed on
+    ``(setup_id, side)``) -- discovered live while wiring this seeder in: a signal missing
+    ``side`` 500s that route with ``KeyError: 'side'``, breaking J-10's own Referee Registry step.
+    Adding the ONE field a genuine signal always carries closes that gap without touching
+    ``referee_evidence.py`` (a frozen module this era) at all."""
+    playbook_store = PlaybookStore(playbook_dir)
+    window_start_epoch = parse_utc_epoch(dataset_meta["window_start_utc"])
+    trigger_dt = datetime.fromtimestamp(window_start_epoch + 5.0, tz=timezone.utc)
+    trigger_ts = trigger_dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
+    playbook_store.record(
+        session_date=_session_date_of(dataset_meta),
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature=_PLAYBOOK_INPUT_SIGNATURE,
+        payload_version=1,
+        parameters=playbook_parameters(),
+        register="",
+        signals=[
+            {
+                "symbol": dataset_meta["symbol"], "setup_id": "capitulation", "side": "long",
+                "trigger_ts": trigger_ts,
+            },
+        ],
+        absences=[], diagnostics=[],
+    )
+    return playbook_store
+
+
+def main(root: Path) -> int:
+    dataset_dir = root / "datasets"
+    dataset_store = DatasetStore(dataset_dir)
+    dataset_meta = _first_real_pg_dataset(dataset_store)
+    print(
+        f"[seed-micro-scout-iter24-j09] anchoring on real PG dataset {dataset_meta['id']} "
+        f"({dataset_meta['symbol']} / {dataset_meta['window_start_utc']})", file=sys.stderr,
+    )
+
+    # --- ensure prerequisite feature snapshots exist (the CLI's own `main()` does this first) ------
+    snapshots_dir = resolve_micro_snapshots_dir(str(dataset_dir))
+    run_snapshot_build_and_record(dataset_store, CONFIG, snapshots_dir, None)
+
+    # --- plant ONE real capitulation playbook signal, into the RIG's own playbook store -----------
+    playbook_dir = os.environ.get("TAPEOLOGY_DESK_PLAYBOOK_DIR") or resolve_desk_playbook_dir(
+        str(root / "universe")
+    )
+    playbook_store = _plant_capitulation_signal(playbook_dir, dataset_meta=dataset_meta)
+    print(f"[seed-micro-scout-iter24-j09] planted capitulation signal at {playbook_dir}", file=sys.stderr)
+
+    # --- register+screen Study 3's frozen request, THEN its walk-forward floor check, for real ----
+    request = scout.pilot_study_candidate_grid(dataset_store)[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION]
+    ledger = ScoutLedger(resolve_scout_ledger_dir(str(dataset_dir)))
+    exposure_registry = ExposureRegistry(resolve_micro_exposure_registry_dir(str(dataset_dir)))
+    result = scout.register_screen_and_walkforward_check(
+        ledger=ledger, dataset_store=dataset_store, snapshots_dir=snapshots_dir, config=CONFIG,
+        exposure_registry=exposure_registry, playbook_store=playbook_store,
+        feature_name=request["feature_name"], transform=request["transform"],
+        params=request["params"], structure_context_kind=request["structure_context_kind"],
+        horizon_key=request["horizon_key"], corpus_manifest=request["corpus_manifest"],
+        grid_version=request["grid_version"], sidedness=request["sidedness"],
+        fitting_rule=request["fitting_rule"], setup_id=request["setup_id"],
+        withheld_excluded=request["withheld_excluded"],
+    )
+    screen_row = result["screen_row"]
+    screen_result = screen_row["screen_result"]
+    print(
+        f"[seed-micro-scout-iter24-j09] register_screen_and_walkforward_check -> "
+        f"candidate_id={screen_row['candidate_id']!r} family_id={screen_row['family_id']!r} "
+        f"decision={screen_row['decision']!r} n_candidate={screen_result['n_candidate']} "
+        f"n_comparator={screen_result['n_comparator']}", file=sys.stderr,
+    )
+    if screen_result["n_candidate"] + screen_result["n_comparator"] <= 0:
+        print(
+            "[seed-micro-scout-iter24-j09] ERROR: vacuous screen -- zero anchors joined "
+            "(n_candidate + n_comparator == 0); the planted signal never reached the screen",
+            file=sys.stderr,
+        )
+        return 1
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
diff --git a/apps/backend/tests/test_desk_vault_sealed_at_day_marker_guard.py b/apps/backend/tests/test_desk_vault_sealed_at_day_marker_guard.py
new file mode 100644
index 0000000..e32fbbc
--- /dev/null
+++ b/apps/backend/tests/test_desk_vault_sealed_at_day_marker_guard.py
@@ -0,0 +1,72 @@
+"""Source-introspection guard for the Validation Vault's "Sealed at" cell -- the
+``test_desk_ui_guards.py``/``test_desk_touch_time_et_guard.py`` pattern (read the frontend .tsx as
+TEXT, assert on substrings; no browser, no runtime).
+
+**Why this guard exists (iteration-24 audit finding F1).** Iteration 24 narrowed the SERVED
+``sealed_at`` from a full-precision ISO instant to a bare day marker (``vault._serialize_shard``
+-> ``_coarsen_sealed_at_to_date``, proven by ``test_vault.py``'s TC-1/TC-2/TC-9). The cell that
+renders it kept calling ``formatDateTimeET``, the INSTANT formatter -- and a bare ``yyyy-MM-dd``
+fed to it is parsed as UTC midnight, which in US-Eastern is the PREVIOUS calendar day at 19:00 or
+20:00. The live browser pass reproduced it exactly: the backend served ``"2026-05-01"`` and the
+page printed ``2026-04-30 20:00 ET`` -- a wrong date, plus a time-of-day that was never in the
+record and that the coarsening exists to remove.
+
+``lib/datetime.ts`` already states the rule this guard pins: a day marker "names a DAY, not an
+instant, so it is read LEXICALLY" and goes through ``formatDayMarker``. The neighbouring
+``assigned_at``/``exposed_at`` cells are still genuine full-precision instants and correctly keep
+``formatDateTimeET`` -- so this guard is scoped to the ``sealed_at`` cell alone, and asserts the
+neighbours are NOT swept along with it.
+
+Each check carries a seeded counter-test: a guard that cannot fail proves nothing.
+"""
+
+from __future__ import annotations
+
+import pathlib
+
+_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
+_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
+
+# The exact regression: the instant formatter applied to the day-marker field.
+_INSTANT_FORMATTER_ON_SEALED_AT = "formatDateTimeET(shard.sealed_at"
+_DAY_MARKER_FORMATTER_ON_SEALED_AT = "formatDayMarker(shard.sealed_at)"
+
+
+def _source() -> str:
+    return _DESK_PAGE.read_text()
+
+
+def _sealed_at_cell_check(source: str) -> bool:
+    """Pure function of the source text, so the identical check can be re-run against a seeded
+    violation below."""
+    return (
+        _DAY_MARKER_FORMATTER_ON_SEALED_AT in source
+        and _INSTANT_FORMATTER_ON_SEALED_AT not in source
+    )
+
+
+def test_the_vault_sealed_at_cell_renders_the_day_marker_lexically():
+    """The served ``sealed_at`` is a day marker since iteration 24 -- rendering it through the
+    instant formatter prints the previous calendar day plus a spurious 19:00-20:00 ET time."""
+    assert _sealed_at_cell_check(_source()) is True, (
+        "the Validation Vault 'Sealed at' cell must render shard.sealed_at through "
+        "formatDayMarker (lexical, yyyy-MM-dd) -- formatDateTimeET parses the bare date as UTC "
+        "midnight and renders the PREVIOUS day with a time-of-day that is not in the record"
+    )
+
+
+def test_the_sealed_at_guard_can_fail_on_the_seeded_pre_fix_violation():
+    """The literal pre-fix line, run through the SAME check -- proving the guard bites."""
+    seeded = "{formatDateTimeET(shard.sealed_at, { seconds: false })}\n"
+    assert _sealed_at_cell_check(seeded) is False
+
+
+def test_the_neighbouring_instant_columns_keep_the_instant_formatter():
+    """Scope pin: ``assigned_at``/``exposed_at`` are still full-precision instants (untouched by
+    the iteration-24 coarsening), so they must NOT be converted to day markers -- doing so would
+    silently drop a real time-of-day the record does carry."""
+    source = _source()
+    assert "formatDateTimeET(shard.assigned_at" in source
+    assert "formatDateTimeET(shard.exposed_at" in source
+    assert "formatDayMarker(shard.assigned_at" not in source
+    assert "formatDayMarker(shard.exposed_at" not in source
```
