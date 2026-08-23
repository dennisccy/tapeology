# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

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
index ad8eb06..30f8858 100644
--- a/apps/backend/scripts/j06_operator.py
+++ b/apps/backend/scripts/j06_operator.py
@@ -745,10 +745,75 @@ def residual_pool_uncertainty(
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
+    on one day, so the floor comfortably holds. Fed a SYNTHETIC full-precision reproduction of the
+    OLD served shape instead (the iter-24 non-vacuity counter-test), the same logic instead
+    separates the four same-day runs from each other, and the 1-shard run bucket collapses the
+    candidate count to 1 -- correctly BELOW the floor.
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
+    buckets = {}
+    for key, run_sealed_count in run_sealed_by_bucket.items():
+        served_count = served_by_bucket.get(key, 0)
+        if run_sealed_count <= 0 or served_count <= 0:
+            # nothing PUBLICLY sealed this bucket, or nothing from it remains sealed today (every
+            # member since exposed) -- no residual identity question to ask for this bucket.
+            continue
+        buckets[key] = {
+            "sealed_this_run_total": run_sealed_count,
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
@@ -759,6 +824,11 @@ def stage_tr2() -> dict:
 
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
@@ -799,17 +869,29 @@ def stage_tr2() -> dict:
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
index e628e4a..03d12f0 100644
--- a/apps/backend/tests/test_j06_operator.py
+++ b/apps/backend/tests/test_j06_operator.py
@@ -269,6 +269,83 @@ def test_uncertainty_holds_for_every_disclosure_count_short_of_the_collapse_poin
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
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/qa-scoped-backend-store-manifest.md        | 28 ++++++------
 .../journey-scripts/J-08.json                      |  2 +-
 .../journey-scripts/J-10.json                      |  2 +-
 .../state/assumptions.md                           | 53 ++++++++++++++++++++++
 runs/goal-session-rapid-microscope/telemetry.jsonl |  7 +++
 .../trace/trace.jsonl                              |  2 +
 6 files changed, 78 insertions(+), 16 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
