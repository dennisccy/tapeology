# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

```diff
diff --git a/apps/backend/tests/test_micro_join.py b/apps/backend/tests/test_micro_join.py
index f5b313f7..acb7e300 100644
--- a/apps/backend/tests/test_micro_join.py
+++ b/apps/backend/tests/test_micro_join.py
@@ -21,6 +21,7 @@ from __future__ import annotations
 
 import hashlib
 import inspect
+import os
 import sqlite3
 from datetime import datetime, timezone
 from pathlib import Path
@@ -50,6 +51,20 @@ def _iso(epoch: float) -> str:
     )
 
 
+def _real_corpus_dataset_store() -> DatasetStore:
+    """iter-28: a ``DatasetStore`` over the real ``.data/datasets`` corpus wired with the SAME
+    durable ``index_db_path=`` primitive the live backend's own ``get_dataset_store()``
+    (``routes.py``) already uses -- ``TAPEOLOGY_DATASET_INDEX_DB`` env-or-sibling
+    ``dataset_index.db``. Without this, the two real-corpus tests below re-parsed and
+    re-checksummed the whole real corpus from scratch on every single test run; the index is a
+    content-checksum-keyed, "owns nothing" derived cache, so sharing it with the running backend
+    is the intended reuse, never a new mechanism."""
+    dataset_dir = CONFIG.dataset_dir_resolved()
+    override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
+    index_db_path = override or os.path.join(os.path.dirname(dataset_dir), "dataset_index.db")
+    return DatasetStore(dataset_dir, index_db_path=index_db_path)
+
+
 # --- shared fixture: the real PG snapshot, built once per module (577 trades -- cheap) -------------
 
 
@@ -948,7 +963,7 @@ def test_tc16_real_corpus_joinable_corpus_arithmetic_is_unchanged_by_the_passeng
     enumerated arithmetic itself."""
     from app.research.desk_playbook import resolve_desk_playbook_dir
 
-    dataset_store = DatasetStore(CONFIG.dataset_dir_resolved())
+    dataset_store = _real_corpus_dataset_store()
     playbook_store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
 
     counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
@@ -972,7 +987,7 @@ def test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_p
     non-``None`` ``feature_at_trigger``, and a full closed outcome set."""
     from app.research.desk_playbook import resolve_desk_playbook_dir
 
-    dataset_store = DatasetStore(CONFIG.dataset_dir_resolved())
+    dataset_store = _real_corpus_dataset_store()
     playbook_store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
     snapshots_dir = resolve_micro_snapshots_dir(CONFIG.dataset_dir_resolved())
 
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
index de124d52..f0a758f7 100644
--- a/apps/backend/tests/test_micro_readiness.py
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -14,6 +14,7 @@ cost is paid once for the whole file. Every OTHER test builds its own small, her
 from __future__ import annotations
 
 import json
+import os
 from datetime import date, datetime
 from zoneinfo import ZoneInfo
 
@@ -384,6 +385,108 @@ def test_corrupted_dataset_surfaces_through_the_route_too(client, tmp_path):
     assert [s["dataset_id"] for s in body["shards"]] == [healthy["id"]]
 
 
+# --- iter-28 TC-10: a warm durable index shared with a DIFFERENT store's content must never mask
+# a checksum failure in a brand-new store's own files -- ``DatasetIndex.lookup`` keys on the
+# absolute file path (``dataset_index.py``), so a scratch copy's never-before-seen path is always
+# a genuine miss regardless of what else is warm in the shared index db.
+
+
+def test_tc10_corrupted_dataset_surfaces_with_a_warm_durable_index_from_a_different_store(tmp_path):
+    shared_index_db = str(tmp_path / "shared_dataset_index.db")
+
+    # Warm the shared index db against a FIRST, unrelated, healthy store.
+    other_store = DatasetStore(tmp_path / "other_datasets", index_db_path=shared_index_db)
+    _plant_dataset(other_store, symbol="GOOG")
+    other_store.list()  # populate the durable index for the OTHER store's own paths
+
+    # A brand-new scratch store (a distinct root -> distinct absolute paths) pointed at the SAME
+    # now-warm index db.
+    store = DatasetStore(tmp_path / "scratch_datasets", index_db_path=shared_index_db)
+    healthy = _plant_dataset(store, symbol="AAPL")
+    corrupted = _plant_dataset(
+        store, symbol="MSFT",
+        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
+    )
+    path = tmp_path / "scratch_datasets" / f"{corrupted['id']}.json"
+    payload = json.loads(path.read_text())
+    payload["record"]["meta"]["checksum"] = "deadbeef" * 8
+    path.write_text(json.dumps(payload))
+
+    cache = MicroReadinessCache(str(tmp_path / "readiness_cache.db"))
+    result = build_readiness(store, cache, dataset_dir=str(tmp_path / "scratch_datasets"))
+
+    assert len(result["integrity_errors"]) == 1
+    assert result["integrity_errors"][0]["file"] == f"{corrupted['id']}.json"
+    assert result["totals"]["distinct_datasets"] == 1
+    assert [s["dataset_id"] for s in result["shards"]] == [healthy["id"]]
+
+
+# --- iter-28 AUDIT (TC-10 reinforcement): the TC-10 test above plants its corrupted file in a
+# scratch store whose absolute paths were NEVER written to the shared index, so
+# ``DatasetIndex.lookup`` (``dataset_index.py``, keyed on ``(path, size, mtime_ns)``) is a
+# guaranteed miss and the "warm index" premise cannot make that test fail -- it passes identically
+# with the warming removed. The case that CAN exercise the cache is a warm row for the SAME path.
+# This test pins that real boundary in all three directions, changing no production behaviour:
+# (a) METADATA may legitimately be served from a warm row whenever the stat is byte-identical, so
+# the one tamper shape that preserves BOTH size and mtime_ns is not surfaced by ``list()`` -- the
+# stat IS the documented key; (b) dataset CONTENT is never served from any cache -- the full
+# verifier runs on EVERY ``load_events``/``replay`` call with no bypass; (c) ANY stat difference
+# re-runs the verifier and surfaces the integrity error explicitly.
+
+
+def test_tc10b_warm_same_path_index_row_never_serves_tampered_content_and_re_verifies_on_any_stat_change(
+    tmp_path,
+):
+    import app.research.datasets as datasets_module
+    from app.research.datasets import DatasetIntegrityError
+
+    index_db = str(tmp_path / "shared_dataset_index.db")
+    root = tmp_path / "datasets"
+    store = DatasetStore(root, index_db_path=index_db)
+    record = _plant_dataset(store, symbol="AAPL")
+    path = root / f"{record['id']}.json"
+
+    # Age the file past the racy-write guard so it is publishable to the durable index, then warm
+    # a REAL row for THIS exact path.
+    st = os.stat(path)
+    os.utime(path, ns=(st.st_atime_ns - 10_000_000_000, st.st_mtime_ns - 10_000_000_000))
+    records, errors = store.list()
+    assert errors == []
+    assert len(records) == 1
+    warm_stat = os.stat(path)
+
+    # Tamper with the CONTENT while restoring the exact (size, mtime_ns) the warm row is keyed on:
+    # a sha256 hex digest is swapped for another 64-character hex string, so the byte size is
+    # unchanged by construction.
+    original = path.read_text()
+    assert original.count(record["checksum"]) == 1
+    path.write_text(original.replace(record["checksum"], "deadbeef" * 8))
+    os.utime(path, ns=(warm_stat.st_atime_ns, warm_stat.st_mtime_ns))
+    tampered_stat = os.stat(path)
+    assert tampered_stat.st_size == warm_stat.st_size
+    assert tampered_stat.st_mtime_ns == warm_stat.st_mtime_ns
+
+    datasets_module._reset_verified_cache_for_tests()
+    warm_store = DatasetStore(root, index_db_path=index_db)
+
+    # (a) the documented boundary, pinned honestly rather than left unknown.
+    warm_records, warm_errors = warm_store.list()
+    assert warm_errors == []
+    assert len(warm_records) == 1
+
+    # (b) CONTENT is never served from a cache -- the full verifier runs on every read.
+    with pytest.raises(DatasetIntegrityError):
+        warm_store.load_events(record["id"])
+
+    # (c) ANY stat difference re-runs the verifier and surfaces the corruption explicitly.
+    os.utime(path, ns=(tampered_stat.st_atime_ns, tampered_stat.st_mtime_ns - 20_000_000_000))
+    datasets_module._reset_verified_cache_for_tests()
+    restat_store = DatasetStore(root, index_db_path=index_db)
+    restat_records, restat_errors = restat_store.list()
+    assert [e["file"] for e in restat_errors] == [f"{record['id']}.json"]
+    assert restat_records == []
+
+
 # --- TC-7: a repeat call/GET never re-classifies, and the response is byte-identical ----------------
 
 
@@ -458,20 +561,38 @@ def test_zero_corpus_is_an_honest_200_with_three_unmet_floor_rows(client):
 
 
 @pytest.fixture(scope="module")
-def real_readiness(tmp_path_factory):
+def real_readiness():
     # CONFIG.dataset_dir (never `_resolved()`) is the un-overridden package default -- the
     # committed real corpus, independent of any ambient TAPEOLOGY_DATASET_DIR the environment
     # might carry.
+    #
+    # iter-28: a fresh `tmp_path_factory` dir every pytest invocation forced a full re-parse +
+    # re-checksum of the whole real store (26 GB / 98 files at this era's corpus size) on every
+    # single run. Point BOTH the `MicroReadinessCache` DB and the `DatasetStore`'s own metadata
+    # index at their PRODUCTION durable-cache paths instead of a throwaway dir -- the exact same
+    # `resolve_micro_readiness_cache_db_path` / `TAPEOLOGY_DATASET_INDEX_DB`-env-or-sibling
+    # primitives `get_dataset_store()` already wires in `routes.py` for the live backend. Both
+    # caches are content-checksum-keyed (`Store discipline`: "no second mutable input to go
+    # stale") -- sharing them with the running backend is exactly the intended reuse, not a new
+    # cache mechanism, and both files already live under the gitignored `.data/` tree.
     dataset_dir = CONFIG.dataset_dir
-    store = DatasetStore(dataset_dir)
-    cache_dir = tmp_path_factory.mktemp("micro_readiness_real_cache")
-    cache = MicroReadinessCache(str(cache_dir / "cache.db"))
+    index_db_override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
+    index_db_path = index_db_override or os.path.join(
+        os.path.dirname(dataset_dir), "dataset_index.db"
+    )
+    store = DatasetStore(dataset_dir, index_db_path=index_db_path)
+    cache = MicroReadinessCache(resolve_micro_readiness_cache_db_path(dataset_dir))
     return build_readiness(store, cache, dataset_dir=dataset_dir)
 
 
 @pytest.fixture(scope="module")
 def real_dataset_records():
-    store = DatasetStore(CONFIG.dataset_dir)
+    dataset_dir = CONFIG.dataset_dir
+    index_db_override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
+    index_db_path = index_db_override or os.path.join(
+        os.path.dirname(dataset_dir), "dataset_index.db"
+    )
+    store = DatasetStore(dataset_dir, index_db_path=index_db_path)
     records, errors = store.list()
     assert errors == []  # the committed corpus is healthy -- a real integrity error here would
     # be a repo-hygiene regression, not something this iteration's tests should silently paper
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 7069436d..652cc174 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -5017,6 +5017,17 @@ function RefereeHypothesesTable({
   );
 }
 
+// goal-rapid-microscope-iter-28 (J-01/J-10, spec section 10.7 r5 owner ruling): the ONE
+// deliberate, owner-authorized exception to Foundation invariant 5 -- static disclosure copy
+// only, never a computed value, never a behavior change. `referee_evidence.strategy_trade_
+// readiness` counts dataset FILES through its own enumeration and may include withheld/unexposed
+// Rapid-Microscope shards; `referee_evidence.py`/`referee_routes.py` stay byte-frozen this era
+// (never edited, never intercepted), so the caveat can ONLY be served here, at the rendering
+// layer, verbatim beside the served `strategy_trade` figures. Defined ONCE as a shared constant
+// (never duplicated ad hoc -- TC-4) so a single edit keeps every render site in sync.
+const REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT =
+  "Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope shards and must not be used as the canonical Rapid-Microscope readiness count.";
+
 // goal-referee-iter-13 (J-12): the readiness-fold blocks -- GET /research/desk/referee/evidence's
 // FIRST direct UI reader (registered since J-01/iteration-1; previously curl/tests-only). Rendered
 // directly BELOW the shipped Registered Hypotheses table above, inside the SAME "Referee Registry"
@@ -5196,6 +5207,12 @@ function RefereeEvidenceReadinessSection({
         >
           {evidence.strategy_trade.tick_gate_statement}
         </p>
+        <p
+          data-testid="referee-evidence-strategy-seal-unaware-caveat"
+          className="mt-2 text-[11px] text-slate-500"
+        >
+          {REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT}
+        </p>
         <ul
           data-testid="referee-evidence-strategy-basis-caveats"
           className="mt-2 space-y-1 text-[11px] text-slate-500"
diff --git a/apps/backend/tests/test_micro_readiness_seal_unaware_caveat.py b/apps/backend/tests/test_micro_readiness_seal_unaware_caveat.py
new file mode 100644
index 00000000..54efa165
--- /dev/null
+++ b/apps/backend/tests/test_micro_readiness_seal_unaware_caveat.py
@@ -0,0 +1,102 @@
+"""Static-scan guard (Era "The Rapid Microscope", iter-28, phase spec IN SCOPE / TC-4): the
+spec's section 10.7 (r5 owner ruling) verbatim caveat sentence about the seal-unaware legacy
+Referee readiness metric (``referee_evidence.strategy_trade_readiness``) must be:
+
+1. defined EXACTLY ONCE as a shared string constant in the frontend source
+   (``apps/frontend/app/desk/page.tsx``), never duplicated ad hoc; and
+2. character-for-character identical to the sentence quoted verbatim in
+   ``docs/rapid-validation-spec.md`` section 10.7.
+
+``referee_evidence.py``/``referee_routes.py`` stay byte-frozen this whole era (Foundation
+invariant 2) -- the caveat can only be served at the frontend rendering layer (the iteration's
+own one deliberate, owner-authorized exception to Foundation invariant 5), so this guard is a
+source-text scan, never a live route/DOM assertion (that lives in the browser-QA lane's TC-5).
+
+This is a NEW sibling file, deliberately never touching the existing, frozen
+``test_micro_no_referee_evidence_guard.py`` (goal.md IN SCOPE: "Do NOT rebuild or modify
+test_micro_no_referee_evidence_guard.py's existing 4 tests -- only extend it (or add a sibling)")."""
+
+from __future__ import annotations
+
+import pathlib
+import re
+
+_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
+_SPEC_PATH = _REPO_ROOT / "docs" / "rapid-validation-spec.md"
+_PAGE_PATH = _REPO_ROOT / "apps" / "frontend" / "app" / "desk" / "page.tsx"
+
+
+def _spec_caveat_sentence() -> str:
+    """The section-10.7 quoted caveat, extracted from the spec and whitespace-normalized (the
+    markdown source hard-wraps it across multiple lines inside a numbered list item)."""
+    text = _SPEC_PATH.read_text(encoding="utf-8")
+    match = re.search(
+        r'\*"(Legacy Referee readiness metric.*?readiness count\.)"\*', text, re.DOTALL
+    )
+    assert match is not None, "spec section 10.7's verbatim caveat sentence was not found -- has it moved or been reworded?"
+    return re.sub(r"\s+", " ", match.group(1)).strip()
+
+
+def test_spec_section_10_7_caveat_sentence_is_present_and_extractable():
+    """Non-vacuity: the extraction itself must find real content, not silently produce an empty
+    string on a match failure elsewhere in this test module."""
+    sentence = _spec_caveat_sentence()
+    assert sentence.startswith("Legacy Referee readiness metric")
+    assert sentence.endswith("Rapid-Microscope readiness count.")
+    assert "seal-unaware in the Rapid Microscope era" in sentence
+
+
+def test_frontend_source_carries_the_verbatim_caveat_exactly_once_as_a_shared_constant():
+    """TC-4, verbatim: grepped for the verbatim sentence, it is found exactly once, sourced from a
+    single shared string constant -- never duplicated ad hoc."""
+    sentence = _spec_caveat_sentence()
+    source = _PAGE_PATH.read_text(encoding="utf-8")
+
+    occurrences = source.count(sentence)
+    assert occurrences == 1, (
+        f"expected the verbatim caveat sentence exactly once in {_PAGE_PATH}, found {occurrences}"
+    )
+
+    # Sourced from a single shared string constant: the sentence's line must itself be a
+    # `const <NAME> = "..."` assignment, and every OTHER reference in the file must be a bare
+    # identifier read of that constant, never a second inline copy of the literal text.
+    const_pattern = re.compile(
+        r'const\s+([A-Z][A-Z0-9_]*)\s*=\s*\n?\s*"' + re.escape(sentence) + r'"\s*;'
+    )
+    const_match = const_pattern.search(source)
+    assert const_match is not None, (
+        "the caveat sentence must be assigned to a single module-level string constant "
+        "(e.g. `const REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT = \"...\";`), never inlined directly "
+        "into JSX"
+    )
+    const_name = const_match.group(1)
+
+    # The constant must actually be READ somewhere (e.g. rendered inside JSX) -- a defined-but-
+    # unused constant would not actually serve the caveat to any user.
+    usage_pattern = re.compile(r"\{" + re.escape(const_name) + r"\}")
+    assert usage_pattern.search(source), (
+        f"the shared constant {const_name} is defined but never rendered in JSX"
+    )
+
+
+def test_frontend_caveat_matches_spec_section_10_7_character_for_character():
+    """The frontend's served sentence, once whitespace-normalized (JSX may hard-wrap a long
+    string source-side without changing the RENDERED text), is byte-for-byte identical to the
+    spec's own section 10.7 wording -- neither a paraphrase nor a stale copy that drifted from a
+    since-edited spec."""
+    spec_sentence = _spec_caveat_sentence()
+    source = _PAGE_PATH.read_text(encoding="utf-8")
+    assert spec_sentence in source, (
+        "the frontend source does not contain the spec's exact section-10.7 sentence "
+        "character-for-character"
+    )
+
+
+def test_the_scan_is_non_vacuous_a_paraphrase_would_not_pass(tmp_path):
+    """Counter-test: a near-miss paraphrase (missing the em dash, or reworded) must NOT satisfy
+    the exact-match check above -- proving the scan can actually fail."""
+    spec_sentence = _spec_caveat_sentence()
+    paraphrased = spec_sentence.replace("seal-unaware", "not seal-aware")
+    assert paraphrased != spec_sentence
+    fake_source = f'const FAKE_CAVEAT = "{paraphrased}";\n<p>{{FAKE_CAVEAT}}</p>\n'
+    assert spec_sentence not in fake_source
```
