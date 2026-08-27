# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 808d1a66..d0823db6 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -54,7 +54,8 @@ from .foundry_compiler import sources_compiler_hermetic_fixture_view
 from .foundry_freeze import freeze_integrity_hermetic_fixture_view, verify_commit_is_ancestor
 from .foundry_hermetic_summary import build_hermetic_oracles_summary
 from .foundry_interpreter import interpreter_hermetic_fixture_view
-from .foundry_runner import read_exhaust_progress
+from .foundry_ledger import ROW_KIND_TERMINAL, FoundryLedger
+from .foundry_runner import SCOUT_TO_FOUNDRY_STATE, read_exhaust_progress
 from .foundry_source_registry import (
     foundry_era_identity,
     read_era_open_baseline,
@@ -803,6 +804,46 @@ def _git_path_committed_at_head(repo_root: Path, rel_path: str) -> bool:
     return result.returncode == 0
 
 
+# goal-hypothesis-foundry-iter-8 (J-08): the §1.4 canonical-provenance fields the real committed
+# ``source-registry.json`` already carries per-record (``foundry_source_registry._canonical_source_
+# record``'s own JSON shape -- verified directly against the real committed file, not assumed) but
+# the tracked ``epoch-manifest.json``'s own ``source_dispositions[]`` entries never carried. Read
+# verbatim from the registry payload the SAME ``read_epoch_manifest_view`` call already parses --
+# never a second file read, never ``resolve_foundry_dir()``, never a recompile pass.
+# Every field's own honest-absence default -- ``None`` for a scalar, a fresh empty ``list``/``dict``
+# for a collection (never a shared mutable object: each entry below gets its own literal).
+_SOURCE_REGISTRY_PROVENANCE_DEFAULTS: tuple[tuple[str, object], ...] = (
+    ("quoted_spans", []), ("source_hash", None), ("mechanism_statement", None),
+    ("operative_formula_refs", []), ("direction_derivation", None), ("comparator_derivation", None),
+    ("threshold_provenance", None), ("superseded_fields", {}), ("alternatives", []),
+    ("audit_note", None), ("lineage_id", None),
+)
+_SOURCE_REGISTRY_PROVENANCE_FIELDS = tuple(field for field, _default in _SOURCE_REGISTRY_PROVENANCE_DEFAULTS)
+
+
+def _enrich_source_dispositions_with_registry_provenance(
+    source_dispositions: list[dict], registry_records_by_id: dict[str, dict],
+) -> list[dict]:
+    """Merges each ``source_dispositions[]`` entry (``source_id``/``disposition``/``lineage_refs``/
+    ``alias_refs``, the manifest's own fields) with its matching real source-registry record's own
+    §1.4 provenance fields, looked up by ``source_id`` -- a pure dict merge over two ALREADY-PARSED
+    payloads, zero recomputation of any disposition/hash/derivation. A manifest entry with no
+    matching registry record (should never happen for the real, generated-together epoch, but this
+    function must not crash if it did) degrades honestly: the base manifest fields are preserved and
+    every provenance field renders its own honest-absence value (``None``/``[]``/``{}``), never a
+    fabricated placeholder."""
+    enriched = []
+    for entry in source_dispositions:
+        record = registry_records_by_id.get(entry.get("source_id")) or {}
+        merged = dict(entry)
+        for field, default in _SOURCE_REGISTRY_PROVENANCE_DEFAULTS:
+            # `default` is copied (never the same shared list/dict object reused across entries),
+            # even though this default path is never exercised against real data today.
+            merged[field] = record[field] if field in record else (default.copy() if hasattr(default, "copy") else default)
+        enriched.append(merged)
+    return enriched
+
+
 def read_epoch_manifest_view(*, tracked_dir: Path | None = None, repo_root: Path | None = None) -> dict:
     """Reads the real, Git-tracked ``docs/hypothesis-foundry/`` artifacts VERBATIM -- the literal
     repo-relative paths (see the module comment above). Computed ONCE at module import time
@@ -812,7 +853,12 @@ def read_epoch_manifest_view(*, tracked_dir: Path | None = None, repo_root: Path
 
     ``tracked_dir``/``repo_root`` default to the real repo-relative paths; a test may override
     either to exercise the missing-artifact degrade path against a synthetic empty directory
-    without needing to relocate/hide the actual committed repo files."""
+    without needing to relocate/hide the actual committed repo files.
+
+    goal-hypothesis-foundry-iter-8 (J-08): ``source_dispositions[]`` entries additionally carry the
+    full §1.4 canonical provenance already present per-record in the SAME tracked
+    ``source-registry.json`` this function already required to exist -- see
+    ``_enrich_source_dispositions_with_registry_provenance`` above."""
     tracked_dir = tracked_dir if tracked_dir is not None else _FOUNDRY_TRACKED_DIR
     repo_root = repo_root if repo_root is not None else _REPO_ROOT
     not_yet_generated = {
@@ -838,8 +884,15 @@ def read_epoch_manifest_view(*, tracked_dir: Path | None = None, repo_root: Path
     try:
         manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
         freeze_record_payload = json.loads(freeze_record_path.read_text(encoding="utf-8"))
+        # goal-hypothesis-foundry-iter-8 (J-08): parsed here for the FIRST time -- previously only
+        # `.is_file()`-checked above, never read. Same tracked repo-relative path, same try/except
+        # degrade-honestly discipline as the two files already parsed on the lines above.
+        source_registry_payload = json.loads(source_registry_path.read_text(encoding="utf-8"))
     except (OSError, ValueError):
         return not_yet_generated
+    registry_records_by_id = {
+        record.get("source_id"): record for record in source_registry_payload.get("records", [])
+    }
 
     freeze_commit = freeze_record_payload.get("freeze_commit")
     head = _git_rev_parse_head(repo_root)
@@ -874,7 +927,9 @@ def read_epoch_manifest_view(*, tracked_dir: Path | None = None, repo_root: Path
         "freeze_commit": freeze_commit,
         "config_fingerprint": manifest_payload.get("config_fingerprint"),
         "outcome_access_census": manifest_payload.get("outcome_access_census", 0),
-        "source_dispositions": manifest_payload.get("source_dispositions", []),
+        "source_dispositions": _enrich_source_dispositions_with_registry_provenance(
+            manifest_payload.get("source_dispositions", []), registry_records_by_id
+        ),
         "families": manifest_payload.get("families", []),
         "source_registry_audit": {"path": _FOUNDRY_AUDIT_REPORT_REL_PATH, "committed": audit_committed},
     }
@@ -923,6 +978,76 @@ def compute_frozen_ready_total(epoch_manifest_view: dict) -> int:
 _FOUNDRY_FROZEN_READY_TOTAL = compute_frozen_ready_total(_EPOCH_MANIFEST_VIEW)
 
 
+# goal-hypothesis-foundry-iter-8 (J-08): `exhaust_progress.diagnostic_survivor_count`. The Data-
+# Contract names `foundry_runner.read_exhaust_progress()` as this field's owner, but
+# ``foundry_runner.py`` is one of the 59 freeze-set-SEALED files
+# (``docs/hypothesis-foundry/freeze-set.json``) since this era's first-read lock -- editing it
+# would trip ``verify_freeze_set_unchanged`` and halt the real epoch (spec §7.3/§9.3, goal.md
+# anti-goal "no science-affecting code/spec/manifest change after the first-read lock"). This
+# module (never sealed) instead reads the SAME Foundry trial ledger directly -- the identical
+# ``FoundryLedger``/``ROW_KIND_TERMINAL``/``foundry_state`` read ``read_exhaust_progress`` itself
+# already performs, filtered on the SAME closed §7.2 survivor state
+# ``foundry_runner.SCOUT_TO_FOUNDRY_STATE["survive"]`` already names (never a second/duplicated
+# literal) -- and the caller below merges this ONE additive field onto ``read_exhaust_progress``'s
+# own UNCHANGED, byte-identical return value. This is the sole owner of this new field; every
+# OTHER ``exhaust_progress`` field still passes through the sealed function verbatim.
+def _compute_diagnostic_survivor_count(foundry_dir: str | Path) -> int:
+    ledger = FoundryLedger(foundry_dir)
+    return len(
+        [
+            row for row in ledger.all_rows()
+            if row["row_kind"] == ROW_KIND_TERMINAL and row["foundry_state"] == SCOUT_TO_FOUNDRY_STATE["survive"]
+        ]
+    )
+
+
+# The one constant scientific label §16/goal.md's own Anti-goals fix for every real Foundry
+# evaluation this era -- never a second literal elsewhere (T-8: no science-affecting constant
+# duplicated across modules).
+_FOUNDRY_EVIDENCE_CLASS = "historical_exposed_diagnostic"
+
+
+# goal-hypothesis-foundry-iter-8 (J-08): the ONE top-level synthesis `final_summary` key -- a PURE
+# projection over already-computed values (`epoch_manifest_view`'s own `source_dispositions`/
+# `families`, `frozen_ready_total` -- `compute_frozen_ready_total`'s own already-computed result,
+# copied verbatim, never re-summed here -- and the per-request `exhaust_progress` result). Zero
+# independent recomputation of any value already owned elsewhere; the only NEW arithmetic this
+# function performs is tallying each ALREADY-DECIDED `disposition` string by value, which is a
+# projection (a count of existing facts), not a scientific recomputation of what any one
+# disposition IS.
+def compute_foundry_final_summary(
+    epoch_manifest_view: dict, *, frozen_ready_total: int, exhaust_progress: dict,
+) -> dict:
+    """Sole canonical owner of the ``final_summary`` Data-Contract key. Every field is either a
+    verbatim copy of a value some other function already owns (``frozen_ready_total``/
+    ``variant_count`` from ``compute_frozen_ready_total``'s own result; ``diagnostic_survivor_count``/
+    ``freeze_integrity_verdict``/``protected_read_count``/``exhaust_complete`` from
+    ``read_exhaust_progress``'s own result), a trivial ``len()``/tally over already-computed
+    collections (``family_count``, ``source_counts_by_disposition``), or the one constant evidence-
+    class label every real Foundry evaluation this era carries (§16)."""
+    source_counts_by_disposition: dict[str, int] = {}
+    for entry in epoch_manifest_view.get("source_dispositions", []):
+        disposition = entry.get("disposition")
+        source_counts_by_disposition[disposition] = source_counts_by_disposition.get(disposition, 0) + 1
+    return {
+        "source_counts_by_disposition": source_counts_by_disposition,
+        "family_count": len(epoch_manifest_view.get("families", [])),
+        # `variant_count` and `frozen_ready_total` are the SAME underlying scalar (the manifest's
+        # own immutable, complete, pre-outcome variant denominator across every family -- it never
+        # shrinks as evaluation proceeds, since the manifest is frozen and evaluation progress lives
+        # only in the runtime ledger `exhaust_progress` already reads) -- both copied verbatim from
+        # the ONE caller-supplied `frozen_ready_total`, never a second `sum()` over `families` here.
+        "variant_count": frozen_ready_total,
+        "frozen_ready_total": frozen_ready_total,
+        "diagnostic_survivor_count": exhaust_progress["diagnostic_survivor_count"],
+        "freeze_integrity_verdict": exhaust_progress["freeze_integrity_verdict"],
+        "evidence_class": _FOUNDRY_EVIDENCE_CLASS,
+        "protected_read_count": exhaust_progress["protected_read_count"],
+        "exhaust_complete": exhaust_progress["exhaust_complete"],
+        "epoch_status": epoch_manifest_view.get("status"),
+    }
+
+
 @router.get("/foundry")
 def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
     """Serves era/session identity (``foundry_source_registry.foundry_era_identity`` -- a static
@@ -949,7 +1074,27 @@ def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
     UNLIKE ``epoch_manifest``, this reflects genuinely runtime-scoped state (the Foundry trial
     ledger the real exhaust CLI writes under this SAME ``foundry_dir``), so it is read PER REQUEST
     (``foundry_runner.read_exhaust_progress``, verbatim, no recomputation of any scientific value)
-    rather than once at import time -- see that function's own docstring."""
+    rather than once at import time -- see that function's own docstring.
+
+    goal-hypothesis-foundry-iter-8 (J-08): ``exhaust_progress`` additionally carries
+    ``diagnostic_survivor_count`` -- ``foundry_runner.read_exhaust_progress`` itself is UNCHANGED
+    (it lives in a freeze-set-sealed file this era may not edit; see
+    ``_compute_diagnostic_survivor_count``'s own docstring), so this handler merges that ONE
+    additive field on top of the sealed function's own verbatim return value.
+
+    goal-hypothesis-foundry-iter-8 (J-08): one more additive top-level key, ``final_summary`` -- the
+    one top-level synthesis of the whole real epoch's final state. Its manifest-derived half
+    (``_EPOCH_MANIFEST_VIEW``/``_FOUNDRY_FROZEN_READY_TOTAL``) is already frozen at module-import
+    time exactly like every hermetic view above; its ``exhaust_progress``-derived half is genuinely
+    runtime-scoped (same reason ``exhaust_progress`` itself is read per request, immediately above),
+    so this handler reuses the SAME per-request ``exhaust_progress`` dict (already including
+    ``diagnostic_survivor_count``) for both keys below -- never a second ledger read for the same
+    request. ``compute_foundry_final_summary`` itself is a zero-cost dict re-assembly over
+    already-owned values, not a second science computation site."""
+    exhaust_progress = {
+        **read_exhaust_progress(foundry_dir, frozen_ready_total=_FOUNDRY_FROZEN_READY_TOTAL),
+        "diagnostic_survivor_count": _compute_diagnostic_survivor_count(foundry_dir),
+    }
     return {
         "era": foundry_era_identity(),
         "era_open_baseline": read_era_open_baseline(foundry_dir),
@@ -960,5 +1105,9 @@ def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
         "interpreter_fixtures": _INTERPRETER_FIXTURES_VIEW,
         "freeze_integrity": _FREEZE_INTEGRITY_VIEW,
         "hermetic_oracles": _HERMETIC_ORACLES_VIEW,
-        "exhaust_progress": read_exhaust_progress(foundry_dir, frozen_ready_total=_FOUNDRY_FROZEN_READY_TOTAL),
+        "exhaust_progress": exhaust_progress,
+        "final_summary": compute_foundry_final_summary(
+            _EPOCH_MANIFEST_VIEW, frozen_ready_total=_FOUNDRY_FROZEN_READY_TOTAL,
+            exhaust_progress=exhaust_progress,
+        ),
     }
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 3c8621c2..b53901bc 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -365,6 +365,13 @@ _PRICE_ARITHMETIC_FIELDS = (
     # conversion, no withheld/stale share arithmetic, is ever legitimate here.
     r"|snapshot\.(?:row_count|bytes_on_disk)"
     r"|report\.(?:withheld_excluded|stale_excluded)"
+    # goal-hypothesis-foundry-iter-8 (J-08): the new Final Summary subsection's own served
+    # numerics -- `final_summary.*` read verbatim for the first time in the browser
+    # (`FinalSummarySubsection`'s `data.` destructured field, the SAME prop-name convention every
+    # other Foundry subsection already uses). No client-side family/variant/survivor/protected-read
+    # count arithmetic is ever legitimate here.
+    r"|data\.(?:family_count|variant_count|frozen_ready_total|diagnostic_survivor_count"
+    r"|protected_read_count)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -2041,3 +2048,25 @@ def test_desk_page_graduation_section_never_derives_a_second_computation_of_the_
         "the Graduation section's referee_handoff_ready copy does not match "
         "micro_graduation.REFEREE_FUTURE_REVISION_SENTENCE byte-for-byte"
     )
+
+
+def test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic():
+    """TC-6 (goal-hypothesis-foundry-iter-8, J-08) counter-test: the extended guard catches
+    arithmetic on the new Final Summary subsection's own `data.family_count`/`data.variant_count`/
+    `data.frozen_ready_total`/`data.diagnostic_survivor_count`/`data.protected_read_count`
+    bindings, not just the pre-existing groups -- a client-side "family_count minus one" style
+    derivation is exactly the shape of violation this guard exists to catch."""
+    seeded_family = "const priorFamilyCount = data.family_count - 1;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_family) is not None
+
+    seeded_variant = "const half = data.variant_count / 2;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_variant) is not None
+
+    seeded_frozen_ready = "const doubled = data.frozen_ready_total * 2;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_frozen_ready) is not None
+
+    seeded_survivors = "const remaining = data.frozen_ready_total - data.diagnostic_survivor_count;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_survivors) is not None
+
+    seeded_protected = "const share = data.protected_read_count + 1;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_protected) is not None
diff --git a/apps/backend/tests/test_foundry_real_epoch_artifacts.py b/apps/backend/tests/test_foundry_real_epoch_artifacts.py
index d1b749e6..7dfe4a4a 100644
--- a/apps/backend/tests/test_foundry_real_epoch_artifacts.py
+++ b/apps/backend/tests/test_foundry_real_epoch_artifacts.py
@@ -292,8 +292,24 @@ def test_tc6_outcome_access_census_is_zero_in_the_artifact_and_on_the_served_vie
     assert served["outcome_access_census"] == 0
     assert served["epoch_id"] == manifest["epoch_id"]
     assert served["source_registry_hash"] == manifest["source_registry_hash"]
-    assert served["source_dispositions"] == manifest["source_dispositions"]
     assert len(served["source_dispositions"]) == 11
+    # goal-hypothesis-foundry-iter-8 (J-08): the served view no longer equals the raw manifest's
+    # `source_dispositions[]` byte-for-byte -- it ADDITIVELY enriches each entry with the matching
+    # real source-registry record's own §1.4 provenance (see `micro_routes.
+    # _enrich_source_dispositions_with_registry_provenance`). Every base manifest field
+    # (`source_id`/`disposition`/`lineage_refs`/`alias_refs`) must still pass through verbatim,
+    # unchanged, entry-for-entry and in the same order -- proven field-by-field rather than by a
+    # single whole-list equality, which the additive enrichment would now legitimately fail.
+    assert len(served["source_dispositions"]) == len(manifest["source_dispositions"])
+    for served_entry, manifest_entry in zip(served["source_dispositions"], manifest["source_dispositions"]):
+        for key, value in manifest_entry.items():
+            assert served_entry[key] == value, (
+                f"{manifest_entry.get('source_id')!r}.{key} diverged from the raw tracked manifest "
+                "during enrichment"
+            )
+        assert "mechanism_statement" in served_entry, (
+            f"{served_entry.get('source_id')!r} is missing the new §1.4 provenance enrichment"
+        )
     # No outcome-shaped value may appear anywhere in the manifest (§8.2's own closing rule).
     blob = json.dumps(manifest)
     for forbidden in ("p_value", "p_screen", "effect_bps", "forward_return", "observation_count", "pnl"):
diff --git a/apps/backend/tests/test_foundry_route.py b/apps/backend/tests/test_foundry_route.py
index 64f76cd0..d0e7799d 100644
--- a/apps/backend/tests/test_foundry_route.py
+++ b/apps/backend/tests/test_foundry_route.py
@@ -13,6 +13,9 @@ module-level cached view now reflects whatever real files this repository actual
 
 from __future__ import annotations
 
+from pathlib import Path
+
+import pytest
 from fastapi.testclient import TestClient
 
 from app.config import CONFIG
@@ -245,3 +248,226 @@ def test_foundry_route_is_get_only_no_mutation_endpoint_exists():
     assert "/research/desk/micro/foundry" in paths
     ops = paths["/research/desk/micro/foundry"]
     assert set(ops.keys()) == {"get"}
+
+
+# === goal-hypothesis-foundry-iter-8 (J-08): the real §1.4 provenance enrichment on
+# `epoch_manifest.source_dispositions[]`, the new `exhaust_progress.diagnostic_survivor_count`, and
+# the new top-level `final_summary` projection. ====================================================
+
+
+def test_iter8_source_dispositions_carry_full_registry_provenance_verbatim():
+    """TC-2/TC-3: every `source_dispositions[]` entry now carries the full §1.4 canonical
+    provenance -- this test independently re-reads the SAME tracked `source-registry.json` directly
+    (never trusting the route's own enrichment to check itself) and asserts every enriched field
+    agrees exactly with the real committed record, for every one of the real epoch's 11 sources."""
+    import json
+
+    repo_root = Path(__file__).resolve().parents[3]
+    registry_path = repo_root / "docs" / "hypothesis-foundry" / "source-registry.json"
+    if not registry_path.is_file():
+        pytest.skip("the real Hypothesis Foundry source registry has not been generated in this checkout")
+    registry_records_by_id = {
+        record["source_id"]: record for record in json.loads(registry_path.read_text(encoding="utf-8"))["records"]
+    }
+
+    view = micro_routes.read_epoch_manifest_view()
+    assert view["source_dispositions"], "the real committed epoch has no source_dispositions to check"
+    for entry in view["source_dispositions"]:
+        record = registry_records_by_id[entry["source_id"]]
+        for field in micro_routes._SOURCE_REGISTRY_PROVENANCE_FIELDS:
+            assert entry[field] == record[field], (
+                f"{entry['source_id']}.{field} does not match the real committed source-registry "
+                "record -- the route enriched it from something other than a verbatim read"
+            )
+
+
+def test_iter8_source_dispositions_provenance_degrades_honestly_without_a_matching_registry_record(tmp_path):
+    """Error case: a manifest `source_dispositions[]` entry with no matching registry record
+    (should never happen for the real, generated-together epoch) must not crash, and every
+    provenance field renders an explicit honest-absence value -- never a fabricated placeholder."""
+    import json
+
+    tracked_dir = tmp_path / "hypothesis-foundry"
+    tracked_dir.mkdir()
+    (tracked_dir / "source-registry.json").write_text(json.dumps({"records": []}), encoding="utf-8")
+    (tracked_dir / "epoch-manifest.json").write_text(
+        json.dumps(
+            {
+                "epoch_id": "epoch:test", "source_registry_hash": "h", "manifest_hash": "m",
+                "config_fingerprint": "fp", "outcome_access_census": 0,
+                "source_dispositions": [
+                    {
+                        "source_id": "unmatched-source", "disposition": "BLOCKED_SPEC_GAP",
+                        "lineage_refs": [], "alias_refs": [],
+                    }
+                ],
+                "families": [],
+            }
+        ),
+        encoding="utf-8",
+    )
+    (tracked_dir / "freeze-set.json").write_text("{}", encoding="utf-8")
+    (tracked_dir / "freeze-record.json").write_text(
+        json.dumps({"freeze_commit": None, "freeze_set_hash": "fsh"}), encoding="utf-8"
+    )
+
+    view = micro_routes.read_epoch_manifest_view(tracked_dir=tracked_dir, repo_root=tmp_path)
+    entry = view["source_dispositions"][0]
+    assert entry["source_id"] == "unmatched-source"
+    assert entry["quoted_spans"] == []
+    assert entry["source_hash"] is None
+    assert entry["mechanism_statement"] is None
+    assert entry["operative_formula_refs"] == []
+    assert entry["direction_derivation"] is None
+    assert entry["comparator_derivation"] is None
+    assert entry["threshold_provenance"] is None
+    assert entry["superseded_fields"] == {}
+    assert entry["alternatives"] == []
+    assert entry["audit_note"] is None
+    assert entry["lineage_id"] is None
+
+
+def test_iter8_exhaust_progress_diagnostic_survivor_count_is_zero_before_any_exhaust_cli_run(tmp_path, monkeypatch):
+    _scope_dataset_dir(tmp_path, monkeypatch)
+    with TestClient(app) as client:
+        body = client.get("/research/desk/micro/foundry").json()
+    assert body["exhaust_progress"]["diagnostic_survivor_count"] == 0
+
+
+def test_iter8_exhaust_progress_diagnostic_survivor_count_is_a_genuine_filter_not_a_copy_of_terminal_count(
+    tmp_path, monkeypatch
+):
+    """The new count must be a REAL filter over terminal rows whose `foundry_state` is the survivor
+    state -- proven with a ledger carrying TWO terminal rows, only ONE of which survived, so
+    `terminal_count` (2) and `diagnostic_survivor_count` (1) genuinely disagree. A count that were
+    secretly a copy of `terminal_count` would report 2, not 1, here."""
+    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
+    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
+    from app.research import foundry_ledger as fl
+
+    ledger = fl.FoundryLedger(foundry_dir)
+    ledger.record_epoch_open(
+        epoch_id="epoch:test-survivor-count", freeze_commit="c" * 40,
+        manifest_hash="mh", source_registry_hash="srh", spec_hash="sh",
+        candidate_spec_schema_hash="csh", compiler_hash="ch", interpreter_hash="ih",
+        runner_hash="rh", scout_screen_source_hash="ssh", config_fingerprint="fp",
+        freeze_set_hash="fsh", era_open_evidence_class_contract="historical_exposed_diagnostic",
+        eligible_corpus_manifest_hash="ecmh",
+    )
+    ledger.record_terminal(
+        candidate_spec_hash="spec-killed", manifest_hash="mh", foundry_family_id="family:test",
+        foundry_family_variant_count=2, screen_result={"decision": "killed_null"},
+        rule_id="foundry:epoch:test-survivor-count:spec-killed",
+        prospective_root_status="root_deferred_composite", foundry_state="EVALUATED_KILLED",
+    )
+    ledger.record_terminal(
+        candidate_spec_hash="spec-survived", manifest_hash="mh", foundry_family_id="family:test",
+        foundry_family_variant_count=2, screen_result={"decision": "survive"},
+        rule_id="foundry:epoch:test-survivor-count:spec-survived",
+        prospective_root_status="root_deferred_composite",
+        foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+    )
+
+    with TestClient(app) as client:
+        body = client.get("/research/desk/micro/foundry").json()
+    progress = body["exhaust_progress"]
+    assert progress["terminal_count"] == 2
+    assert progress["diagnostic_survivor_count"] == 1
+
+
+def test_iter8_final_summary_matches_tc1_values_against_the_real_committed_epoch(tmp_path, monkeypatch):
+    """TC-1: given the real committed Foundry epoch plus a freshly-recorded first-read-lock row
+    (isolated storage -- never the shared real runtime ledger), `final_summary` carries exactly the
+    values TC-1 specifies -- source counts summing to 11, zero families/variants/survivors, green
+    freeze integrity, zero protected reads, and an honest vacuous exhaust completion."""
+    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
+    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
+    from app.research import foundry_ledger as fl
+
+    ledger = fl.FoundryLedger(foundry_dir)
+    ledger.record_epoch_open(
+        epoch_id="epoch:test-final-summary", freeze_commit="c" * 40,
+        manifest_hash="mh", source_registry_hash="srh", spec_hash="sh",
+        candidate_spec_schema_hash="csh", compiler_hash="ch", interpreter_hash="ih",
+        runner_hash="rh", scout_screen_source_hash="ssh", config_fingerprint="fp",
+        freeze_set_hash="fsh", era_open_evidence_class_contract="historical_exposed_diagnostic",
+        eligible_corpus_manifest_hash="ecmh",
+    )
+
+    with TestClient(app) as client:
+        body = client.get("/research/desk/micro/foundry").json()
+    summary = body["final_summary"]
+    assert sum(summary["source_counts_by_disposition"].values()) == 11
+    assert summary["family_count"] == 0
+    assert summary["variant_count"] == 0
+    assert summary["frozen_ready_total"] == 0
+    assert summary["diagnostic_survivor_count"] == 0
+    assert summary["freeze_integrity_verdict"] == "green"
+    assert summary["evidence_class"] == "historical_exposed_diagnostic"
+    assert summary["protected_read_count"] == 0
+    assert summary["exhaust_complete"] is True
+    assert summary["epoch_status"] == "committed"
+    # The real registry's own known disposition mix (verified directly against the committed
+    # docs/hypothesis-foundry/source-registry.json).
+    assert summary["source_counts_by_disposition"] == {
+        "BLOCKED_DIRECTION": 4,
+        "ALIASED_PROXY_ONLY": 2,
+        "BLOCKED_SPEC_GAP": 1,
+        "ALIASED_VARIANT_VOCABULARY": 1,
+        "EXCLUDED_PREVIOUSLY_KILLED": 1,
+        "EXCLUDED_PREREQUISITE_UNMET": 1,
+        "EXCLUDED_GATE_CLOSED": 1,
+    }
+
+
+def test_iter8_final_summary_copies_frozen_ready_total_verbatim_never_resums_families():
+    """`compute_foundry_final_summary` reads the caller-supplied `frozen_ready_total` for BOTH
+    `.variant_count` and `.frozen_ready_total` rather than independently re-summing
+    `families[].variant_count` -- proven by passing a `frozen_ready_total` that deliberately
+    disagrees with what an independent re-sum of a (deliberately non-empty) `families` list would
+    produce. If this helper ever drifted into a second counting site, this test would catch the
+    disagreement immediately."""
+    fake_view = {
+        "status": "committed",
+        "source_dispositions": [{"source_id": "a", "disposition": "COMPILED"}],
+        "families": [{"foundry_family_id": "f1", "variant_count": 99}],
+    }
+    fake_exhaust_progress = {
+        "diagnostic_survivor_count": 3, "freeze_integrity_verdict": "green",
+        "protected_read_count": 0, "exhaust_complete": True,
+    }
+    summary = micro_routes.compute_foundry_final_summary(
+        fake_view, frozen_ready_total=5, exhaust_progress=fake_exhaust_progress
+    )
+    assert summary["variant_count"] == 5
+    assert summary["frozen_ready_total"] == 5
+    assert summary["family_count"] == 1
+    assert summary["source_counts_by_disposition"] == {"COMPILED": 1}
+    # And the exhaust_progress-derived fields are copied verbatim, never recomputed here either.
+    assert summary["diagnostic_survivor_count"] == 3
+    assert summary["freeze_integrity_verdict"] == "green"
+    assert summary["exhaust_complete"] is True
+
+
+def test_iter8_final_summary_degrades_honestly_when_the_epoch_has_not_been_generated(tmp_path):
+    """Error case: `final_summary` on a `not_yet_generated` epoch status must not fabricate any
+    count -- every field reflects the honestly-empty manifest view it was built from."""
+    empty_dir = tmp_path / "hypothesis-foundry-empty"
+    empty_dir.mkdir()
+    not_yet_generated_view = micro_routes.read_epoch_manifest_view(tracked_dir=empty_dir, repo_root=tmp_path)
+    assert not_yet_generated_view["status"] == "not_yet_generated"
+    fake_exhaust_progress = {
+        "diagnostic_survivor_count": 0, "freeze_integrity_verdict": "not_yet_verified",
+        "protected_read_count": 0, "exhaust_complete": False,
+    }
+    summary = micro_routes.compute_foundry_final_summary(
+        not_yet_generated_view, frozen_ready_total=0, exhaust_progress=fake_exhaust_progress
+    )
+    assert summary["source_counts_by_disposition"] == {}
+    assert summary["family_count"] == 0
+    assert summary["variant_count"] == 0
+    assert summary["frozen_ready_total"] == 0
+    assert summary["diagnostic_survivor_count"] == 0
+    assert summary["freeze_integrity_verdict"] == "not_yet_verified"
+    assert summary["exhaust_complete"] is False
+    assert summary["epoch_status"] == "not_yet_generated"
diff --git a/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py b/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
index 3e9b4ce8..dacf2888 100644
--- a/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
+++ b/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
@@ -180,7 +180,19 @@ def test_frozen_ready_total_sealed_cli_formula_agrees_with_the_canonical_helper(
     transcribed sealed formula agrees with ``micro_routes.compute_frozen_ready_total`` -- the new
     sole canonical owner -- on that same real data. Today this is vacuously ``0 == 0`` (the frozen
     manifest's ``families`` list is ``[]``); the test's permanent value is pinning agreement for
-    this frozen, unchangeable manifest, not proving a non-trivial case."""
+    this frozen, unchangeable manifest, not proving a non-trivial case.
+
+    goal-hypothesis-foundry-iter-8 (J-08) correction, per the iter-7 AUDITOR NOTE: this assertion,
+    BY ITSELF, is not what keeps the two formulas from silently diverging. The two sides read a
+    variant count via DIFFERENT keys (the sealed CLI's ``len(fm.get("variants", []))`` vs. the
+    canonical helper's ``fm["variant_count"]``), which are not proven equal in general -- they only
+    happen to agree here because the real manifest's ``families`` list is empty, so both sides are
+    vacuously ``0``. What actually PREVENTS the two formulas from silently diverging on a real,
+    non-empty future manifest is the freeze-set hash pinning (``docs/hypothesis-foundry/freeze-
+    set.json``): the sealed CLI is one of its 59 enumerated entries, so its line 225 formula cannot
+    be edited without a freeze-set hash mismatch halting the epoch (§8.5/§9.3) -- drift is
+    structurally impossible because the sealed formula itself is frozen, not because this test would
+    catch a hypothetical future disagreement it has never actually exercised."""
     _require_real_epoch_committed()
     manifest = json.loads((FOUNDRY_DOCS_DIR / "epoch-manifest.json").read_text(encoding="utf-8"))
 
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index e92ef348..eba18cfc 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -90,9 +90,11 @@ import type {
   DeskGraduationResponse,
   FoundryEpochManifest,
   FoundryExhaustProgress,
+  FoundryFinalSummary,
   FoundryFreezeIntegrity,
   FoundryHermeticOracles,
   FoundryInterpreterFixtures,
+  FoundrySourceDisposition,
   FoundrySourcesCompiler,
   DeskMicroSnapshotRunsResponse,
   DeskMicroSnapshotsResponse,
@@ -7962,6 +7964,169 @@ function HermeticOraclesSubsection({ data }: { data: FoundryHermeticOracles }) {
   );
 }
 
+// goal-hypothesis-foundry-iter-8 (J-08): Final Summary -- the one top-level synthesis of the whole
+// real epoch's final state (source/family/variant/survivor/integrity/evidence), rendered VERBATIM
+// from `final_summary` (no client-side recomputation -- see the arithmetic-guard's own
+// `data.family_count`/etc. entries), plus a per-source detail drill-in reading the full §1.4
+// canonical provenance now carried on each `epoch_manifest.source_dispositions[]` entry (same
+// `<details>` disclosure convention `SourcesCompilerSubsection` above already uses).
+function FinalSummarySubsection({
+  data,
+  sourceDispositions,
+}: {
+  data: FoundryFinalSummary;
+  sourceDispositions: FoundrySourceDisposition[];
+}) {
+  const dispositionEntries = Object.entries(data.source_counts_by_disposition);
+  const freezeVerdictClass = data.freeze_integrity_verdict === "green" ? "text-emerald-400" : "text-amber-400";
+  return (
+    <div data-testid="foundry-final-summary">
+      <p className="mb-3 text-xs text-slate-500">
+        The real epoch&rsquo;s complete final state, synthesized from the six subsections below --
+        source dispositions, family/variant counts, diagnostic survivors, freeze integrity, and
+        evidence class -- every value read verbatim, never recomputed here.
+      </p>
+
+      <div data-testid="foundry-final-summary-source-counts" className="mb-3 text-[11px] text-slate-500">
+        <p className="mb-1 font-semibold text-slate-400">
+          Source counts by disposition ({dispositionEntries.length} distinct dispositions)
+        </p>
+        <ul className="space-y-0.5">
+          {dispositionEntries.map(([disposition, count]) => (
+            <li key={disposition}>
+              <span className="font-mono text-slate-300">{disposition}</span>
+              {": "}
+              <span className="font-mono text-slate-300">{count}</span>
+            </li>
+          ))}
+        </ul>
+      </div>
+
+      <div data-testid="foundry-final-summary-counts" className="mb-3 space-y-0.5 text-[11px] text-slate-500">
+        <p data-testid="foundry-final-summary-family-count">
+          Family count: <span className="font-mono text-slate-300">{data.family_count}</span>
+        </p>
+        <p data-testid="foundry-final-summary-variant-count">
+          Variant count: <span className="font-mono text-slate-300">{data.variant_count}</span>
+        </p>
+        <p data-testid="foundry-final-summary-frozen-ready-total">
+          Frozen-ready total: <span className="font-mono text-slate-300">{data.frozen_ready_total}</span>
+        </p>
+        <p data-testid="foundry-final-summary-evidence-class">
+          Evidence class: <span className="font-mono text-slate-300">{data.evidence_class}</span>
+        </p>
+        <p data-testid="foundry-final-summary-protected-read-count">
+          Protected/withheld/sealed reads:{" "}
+          <span className={`font-mono ${data.protected_read_count === 0 ? "text-emerald-400" : "text-rose-400"}`}>
+            {data.protected_read_count}
+          </span>
+        </p>
+        <p data-testid="foundry-final-summary-freeze-integrity-verdict">
+          Freeze integrity: <span className={`font-mono ${freezeVerdictClass}`}>{data.freeze_integrity_verdict}</span>
+        </p>
+        <p data-testid="foundry-final-summary-epoch-status">
+          Epoch status: <span className="font-mono text-slate-300">{data.epoch_status}</span>
+        </p>
+      </div>
+
+      {data.diagnostic_survivor_count === 0 ? (
+        <p data-testid="foundry-final-summary-zero-survivors" className="mb-3 text-[11px] text-slate-500">
+          Zero diagnostic survivors exist for this epoch (diagnostic_survivor_count ={" "}
+          <span className="font-mono text-slate-300">{data.diagnostic_survivor_count}</span>) -- no
+          candidate reached DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN this era.
+        </p>
+      ) : (
+        <p data-testid="foundry-final-summary-survivors" className="mb-3 text-[11px] text-amber-400">
+          <span className="font-mono">{data.diagnostic_survivor_count}</span> diagnostic survivor(s)
+          this epoch -- labelled DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN only; not OOS evidence, not
+          Referee-ready, not a confirmed outcome.
+        </p>
+      )}
+
+      {data.exhaust_complete ? (
+        <p data-testid="foundry-final-summary-exhaust-complete" className="mb-3 text-[11px] text-emerald-400">
+          Exhaust complete -- every frozen candidate reached a terminal state
+          {/* goal-hypothesis-foundry-iter-8 AUDIT fix: this top-level truth screen is meant to be
+              read INSTEAD of the six subsections below, so it must not state completion more
+              strongly than `RunnerCheckpointSubsection` already does on the SAME served fact.
+              Same vacuity caveat, same `frozen_ready_total === 0` condition (a comparison, never
+              arithmetic -- the numeric anti-recomputation guard still holds). */}
+          {data.frozen_ready_total === 0
+            ? " (zero FROZEN_READY variants this epoch — an honest, vacuous completion)."
+            : "."}
+        </p>
+      ) : (
+        <p data-testid="foundry-final-summary-exhaust-incomplete" className="mb-3 text-[11px] text-amber-400">
+          Exhaust not yet complete for this epoch.
+        </p>
+      )}
+
+      <p className="mb-1 text-[11px] font-semibold text-slate-400">
+        Source detail ({sourceDispositions.length} of 11 required objects)
+      </p>
+      <ul data-testid="foundry-final-summary-source-detail-rows" className="space-y-2">
+        {sourceDispositions.map((row) => (
+          <li key={row.source_id} className="rounded border border-slate-800 p-2">
+            <div className="mb-1 flex flex-wrap items-center gap-2 text-[11px]">
+              <span className="font-mono text-slate-300">{row.source_id}</span>
+              <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
+                {row.disposition}
+              </span>
+            </div>
+            <details data-testid="foundry-final-summary-source-detail">
+              <summary className="cursor-pointer text-[10px] text-slate-600">Canonical provenance</summary>
+              <div className="mt-1 space-y-1 text-[10px] text-slate-500">
+                <p>
+                  Mechanism: <span className="text-slate-400">{row.mechanism_statement ?? "—"}</span>
+                </p>
+                <p>
+                  Audit note: <span className="text-slate-400">{row.audit_note ?? "—"}</span>
+                </p>
+                <p>
+                  Direction derivation:{" "}
+                  <span className="font-mono text-slate-400">{row.direction_derivation ?? "—"}</span>
+                </p>
+                <p>
+                  Comparator derivation:{" "}
+                  <span className="font-mono text-slate-400">{row.comparator_derivation ?? "—"}</span>
+                </p>
+                <p>
+                  Threshold provenance:{" "}
+                  <span className="font-mono text-slate-400">{row.threshold_provenance ?? "(none)"}</span>
+                </p>
+                <p>
+                  Superseded fields:{" "}
+                  <span className="font-mono text-slate-400">
+                    {Object.keys(row.superseded_fields).length > 0
+                      ? Object.entries(row.superseded_fields)
+                          .map(([field, ref]) => `${field} → ${ref}`)
+                          .join("; ")
+                      : "{}"}
+                  </span>
+                </p>
+                <p>
+                  Alternatives:{" "}
+                  <span className="font-mono text-slate-400">
+                    {row.alternatives.length > 0 ? row.alternatives.join(", ") : "(none)"}
+                  </span>
+                </p>
+                <p>
+                  Source hash: <span className="break-all font-mono text-slate-400">{row.source_hash ?? "—"}</span>
+                </p>
+                {row.quoted_spans.map((span, i) => (
+                  <p key={i} className="font-mono text-slate-600">
+                    &ldquo;{span.text}&rdquo; @ {span.location}
+                  </p>
+                ))}
+              </div>
+            </details>
+          </li>
+        ))}
+      </ul>
+    </div>
+  );
+}
+
 // goal-hypothesis-foundry-iter-1 (J-01): the Hypothesis Foundry panel header -- era/session
 // identity + the era-open baseline, rendered VERBATIM from `GET /research/desk/micro/foundry`
 // (no client-side recomputation, per the goal's own Product Shape). The `foundry-panel`
@@ -8096,6 +8261,25 @@ function HypothesisFoundrySection({
         )}
       </div>
 
+      {/* goal-hypothesis-foundry-iter-8 (J-08): the Final Summary subsection -- the one top-level
+          synthesis of the whole real epoch, positioned above the six existing subsections so an
+          operator sees the complete final state without expanding any of them individually. A
+          SEPARATE block (not nested inside the six-subsection container below), reusing the SAME
+          `openSubsections`/`toggleSubsection` state and the already-fetched `foundry` payload. */}
+      <div className="mt-4">
+        <CollapsibleSection
+          id="foundry-final-summary-section"
+          title="Final Summary"
+          open={openSubsections.has("final-summary")}
+          onToggle={() => toggleSubsection("final-summary")}
+        >
+          <FinalSummarySubsection
+            data={foundry.final_summary}
+            sourceDispositions={foundry.epoch_manifest.source_dispositions}
+          />
+        </CollapsibleSection>
+      </div>
+
       {/* goal-hypothesis-foundry-iter-4 (J-02/J-03/J-04/J-05): the four new fixture subsections --
           nested CollapsibleSections, each its own GET-never-computes read of an ADDITIVE key on
           the SAME already-fetched `foundry` payload (no second fetch). */}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 73fde0f6..b76bf120 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -3129,11 +3129,29 @@ export interface FoundryHermeticOracles {
 // hermetic-fixture subview above. `status` degrades honestly to "not_yet_generated" when the
 // tracked `docs/hypothesis-foundry/` artifacts are absent; `families`/`source_dispositions` are
 // served verbatim from the canonical backend read, never recomputed client-side.
+export interface FoundryQuotedSpan {
+  text: string;
+  location: number;
+}
+
+// goal-hypothesis-foundry-iter-8 (J-08): the full §1.4 canonical provenance, read verbatim from
+// the real committed `source-registry.json` by `source_id` -- never a second compile pass.
 export interface FoundrySourceDisposition {
   source_id: string;
   disposition: string;
   lineage_refs: string[];
   alias_refs: string[];
+  quoted_spans: FoundryQuotedSpan[];
+  source_hash: string | null;
+  mechanism_statement: string | null;
+  operative_formula_refs: string[];
+  direction_derivation: string | null;
+  comparator_derivation: string | null;
+  threshold_provenance: string | null;
+  superseded_fields: Record<string, string>;
+  alternatives: string[];
+  audit_note: string | null;
+  lineage_id: string | null;
 }
 
 export interface FoundryVariant {
@@ -3175,6 +3193,9 @@ export interface FoundryExhaustProgress {
   eligible_corpus_manifest_hash: string | null;
   frozen_ready_total: number;
   terminal_count: number;
+  // goal-hypothesis-foundry-iter-8 (J-08): a genuine read of the real trial ledger's terminal rows
+  // whose `foundry_state` is `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` -- never a copy of `terminal_count`.
+  diagnostic_survivor_count: number;
   checkpoint_ordinal: number;
   protected_read_count: number;
   single_flight_status: "idle" | "running" | "refused_concurrent";
@@ -3184,6 +3205,22 @@ export interface FoundryExhaustProgress {
   exhaust_complete: boolean;
 }
 
+// goal-hypothesis-foundry-iter-8 (J-08): the one top-level synthesis of the whole real epoch's
+// final state -- every field is a projection of an already-canonically-owned value (never a second
+// computation site); see `micro_routes.compute_foundry_final_summary`'s own docstring.
+export interface FoundryFinalSummary {
+  source_counts_by_disposition: Record<string, number>;
+  family_count: number;
+  variant_count: number;
+  frozen_ready_total: number;
+  diagnostic_survivor_count: number;
+  freeze_integrity_verdict: string;
+  evidence_class: string;
+  protected_read_count: number;
+  exhaust_complete: boolean;
+  epoch_status: string;
+}
+
 export interface DeskFoundryResponse {
   era: FoundryEraIdentity;
   // `null` on a fresh install before the operator's one-time recording act has run -- never
@@ -3202,4 +3239,6 @@ export interface DeskFoundryResponse {
   epoch_manifest: FoundryEpochManifest;
   // goal-hypothesis-foundry-iter-6 (J-07): the real exhaust pass's own checkpoint/completion state.
   exhaust_progress: FoundryExhaustProgress;
+  // goal-hypothesis-foundry-iter-8 (J-08): the one top-level "final truth" synthesis.
+  final_summary: FoundryFinalSummary;
 }
```
