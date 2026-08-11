# Iteration diff (bounded)

Files changed: 24. Shown in full: 22.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/desk_playbook_evidence.py` (39 lines not shown)
- `apps/backend/tests/test_desk_playbook_evidence.py` (120 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_playbook_backscan.py b/apps/backend/app/research/desk_playbook_backscan.py
index ddea881..59a3bd0 100644
--- a/apps/backend/app/research/desk_playbook_backscan.py
+++ b/apps/backend/app/research/desk_playbook_backscan.py
@@ -86,6 +86,7 @@ __all__ = [
     "BackscanRunStore",
     "DeskPlaybookBackscanComputeManager",
     "PlaybookNotScopedError",
+    "malformed_days",
     "plan_backscan",
     "record_backscan_run",
     "resolve_desk_playbook_backscan_log_dir",
@@ -195,10 +196,44 @@ def _assert_scoped(root: str | Path) -> None:
 # --- the plan (pure, metadata-only) ----------------------------------------------------------------
 
 
+def _is_calendar_day(value: str) -> bool:
+    """Whether ``value`` parses as a real ``yyyy-MM-dd`` calendar day -- the ONE parse rule both the
+    tolerant plan read (``_planned_dates``) and the trigger's own refusal (``malformed_days``)
+    share, so "what counts as a real date" is never defined a second way."""
+    try:
+        date.fromisoformat(value)
+    except ValueError:
+        return False
+    return True
+
+
+def malformed_days(from_day: str, to_day: str) -> list[str]:
+    """Which of the two boundary strings is NOT a parseable calendar day -- ``[]`` when both are.
+
+    The WRITE-side companion to ``_planned_dates``' read-side tolerance (goal-playbook-iter-8 audit,
+    B1). Reading a plan for a half-typed date is an honest empty plan; STARTING a back-scan over one
+    is not the same act: a job planned from an uninterpretable string walks zero dates and then
+    finalizes ``"done"``, appending a permanently un-prunable ledger row that claims a completed run
+    over a range nothing could parse. An INVERTED range is deliberately NOT malformed -- both of its
+    boundaries are real days, it simply names an empty span (TC-17), and that stays a legitimate,
+    honestly-empty walk."""
+    return [value for value in (from_day, to_day) if not _is_calendar_day(value)]
+
+
 def _planned_dates(from_day: str, to_day: str) -> list[str]:
     """Every calendar day in ``[from_day, to_day]`` inclusive, ``yyyy-MM-dd`` ascending -- pure date
     arithmetic, no store touched at all (the ``plan_deep_windows`` precedent). An inverted range
-    (``from_day > to_day``) is an honest empty list, never an error (TC-17)."""
+    (``from_day > to_day``) is an honest empty list, never an error (TC-17). A malformed/partial
+    date (e.g. a half-typed ``2026-06-2``, mid-keystroke in the Backscan panel's own From/To boxes)
+    is the SAME honest empty list rather than a raised ``ValueError`` -- T-5 ("fail closed, disclose
+    the absence") is the governing rail here, since a not-yet-a-real-date string describes no
+    calendar range at all, exactly like an inverted one (iter-8's own carried defect fix: this used
+    to propagate the ``ValueError`` straight into an HTTP 500 at the route). NOTE this tolerance is
+    a READ-side rule only: the TRIGGER route refuses a malformed boundary outright (see
+    ``malformed_days``) rather than starting a phantom zero-date job over a string nothing could
+    interpret."""
+    if not _is_calendar_day(from_day) or not _is_calendar_day(to_day):
+        return []
     start = date.fromisoformat(from_day)
     end = date.fromisoformat(to_day)
     if start > end:
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index f2c22aa..32ff5f0 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -95,6 +95,7 @@ dependencies instead (the ``get_universe_fetcher`` seam), test-overridable via
 from __future__ import annotations
 
 import os
+import sqlite3
 from datetime import date, datetime, timedelta, timezone
 from typing import Callable
 
@@ -127,10 +128,12 @@ from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
 from .desk_playbook_backscan import (
     BackscanRunStore,
     DeskPlaybookBackscanComputeManager,
+    malformed_days,
     plan_backscan,
     resolve_desk_playbook_backscan_log_dir,
 )
 from .desk_playbook_compute import DeskPlaybookComputeManager
+from .desk_playbook_evidence import PlaybookEvidenceCache, fold_evidence, inspect_signature
 from .desk_playbook_log import PlaybookRunStore, resolve_desk_playbook_log_dir
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
@@ -1218,7 +1221,26 @@ def trigger_desk_playbook_backscan_compute(
     thread, off this request, so this route returns immediately however long the scan takes. Every
     planned date is walked through the ONE shared ``run_playbook_and_record`` entry point — a date
     already recorded reuses with zero detector calls, so re-triggering the SAME range resumes
-    rather than restarting."""
+    rather than restarting.
+
+    Refuses — 422, naming the malformed boundary, never starting a job or writing a ledger row —
+    when either date is not a parseable calendar day (``malformed_days``), the
+    ``trigger_desk_playbook_compute`` pre-check precedent verbatim. The PLAN read stays tolerant of
+    a half-typed date (an honest empty plan, iter-8's own TC-9), but STARTING a scan over a string
+    nothing could interpret is a different act: it would walk zero dates and then append a
+    permanently un-prunable ``"done"`` ledger row claiming a completed run over an unparseable
+    range (goal-playbook-iter-8 audit, B1). An INVERTED range is not malformed — both boundaries
+    are real days — and still starts an honestly-empty walk (TC-17)."""
+    malformed = malformed_days(body.from_day, body.to_day)
+    if malformed:
+        raise HTTPException(
+            status_code=422,
+            detail=(
+                "back-scan refused — not a calendar date: "
+                + ", ".join(repr(day) for day in malformed)
+                + ". No job was started and no run-ledger row was written."
+            ),
+        )
     return manager.trigger(
         body.from_day, body.to_day, universe_store, bar_store, CONFIG, playbook_store, run_store,
     )
@@ -1264,6 +1286,69 @@ def get_desk_playbook_backscan_runs(store: BackscanRunStore = Depends(get_backsc
     }
 
 
+# --- The Playbook Evidence view (Era B2, J-08) — a read-only fold of every recorded playbook file
+# at ONE signature into per-(setup_id, side, measure) distribution cells beside the pooled
+# baseline. See `desk_playbook_evidence.py` for the fold/cache mechanics this route only wires up.
+# ------------------------------------------------------------------------------------------------
+
+
+def playbook_evidence_cache_db_path() -> str:
+    """The resolved durable playbook-evidence projection-cache path — the
+    ``screen_meta_cache_db_path``/``forward_meta_cache_db_path`` resolver verbatim: the
+    ``TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB`` env var if set, else a file co-located as a SIBLING of
+    the playbook directory (``.data/playbook`` -> ``.data/playbook_evidence_cache.db``). A derived
+    path, never a ``Config`` field, so ``config_fingerprint`` stays frozen."""
+    override = os.environ.get("TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB")
+    if override:
+        return override
+    playbook_dir = resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved())
+    return os.path.join(os.path.dirname(playbook_dir), "playbook_evidence_cache.db")
+
+
+def get_playbook_evidence_cache() -> PlaybookEvidenceCache | None:
+    """The evidence projection cache — a FastAPI dependency so a test overrides it outright via
+    ``app.dependency_overrides``. An unopenable DB (a bad path, a locked/corrupt file) is a missing
+    optimisation, never a failed read (the ``ForwardStore._durable_meta_cache`` rule, applied here
+    since ``fold_evidence`` takes the cache as a plain optional argument rather than owning a store
+    instance itself)."""
+    try:
+        return PlaybookEvidenceCache(playbook_evidence_cache_db_path())
+    except sqlite3.Error:
+        return None
+
+
+@router.get("/playbook/evidence")
+def get_desk_playbook_evidence(
+    signature: str | None = None,
+    universe_store: UniverseStore = Depends(get_universe_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+    cache: PlaybookEvidenceCache | None = Depends(get_playbook_evidence_cache),
+) -> dict:
+    """Two shapes, selected by ``?signature=`` (the ``GET /research/desk/playbook`` ``?date=``/
+    ``?id=`` convention):
+
+      * ``signature`` absent: the full pooled fold at the CURRENT default signature —
+        ``{"signature", "cells", "invalidation_breached", "other_signatures", "parameters",
+        "register"}``. Only the default signature's own recorded signals ever enter ``cells``; a
+        cell with zero recorded signals is still served (``n: 0``), never omitted.
+      * ``signature=<value>``: that ONE named signature's own ``{"signature", "dates",
+        "created_span"}`` — inspects any recorded signature (default or not) WITHOUT pooling it
+        into any cell (T-7/the "one signature" anti-goal — this branch never even resolves the
+        current default).
+
+    A plain read: writes nothing, triggers nothing, recomputes nothing (GET-never-computes) — the
+    only bar-content-adjacent call anywhere in this path is ``compute_playbook_input_signature``'s
+    own ``list(include_bars=False)`` metadata scan, the SAME cost the back-scan plan already pays."""
+    if signature is not None:
+        return inspect_signature(playbook_store, signature)
+    records, _errors = universe_store.list()
+    members = list(records[-1]["members"]) if records else []
+    return fold_evidence(
+        playbook_store, bar_store, members, CONFIG.config_fingerprint(), cache=cache
+    )
+
+
 # --- Coverage-index reconciliation (J-10, goal-desk-iter-14) — a trigger/poll/cancel trio mirroring
 # the top-up compute trio exactly, plus ONE durable read mirroring ``GET /research/desk/topup/runs``.
 # See ``desk_index_reconcile.py`` for the classify/repair/record mechanics this only wires up. -------
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index c332035..bc02591 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -1,40 +1,54 @@
 #!/usr/bin/env bash
 # qa_playbook_iter7_fixture_scoped_backend.sh — Stand up a FIXTURE-SCOPED backend carrying the
-# iter-6 J-04/J-05/J-06 playbook rig PLUS two additional recorded session dates for the Backscan
-# panel (Era B2, J-07), for a browser-QA / golden-replay pass. Never touches the ambient
-# apps/backend/.data/ store: every bar/universe/playbook/run-ledger directory this backend reads or
-# writes lives under a fresh root, so a "Run Backscan" click in the browser can never land in the
-# operator's real store (the iter-3 lesson, restated by this session's own iter-6 audit findings for
-# the run-ledger siblings specifically — all FOUR playbook env vars are exported here, including
-# TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR).
+# iter-6 J-04/J-05/J-06 playbook rig PLUS the Backscan (J-07) and Evidence (J-08) fixture layers,
+# for a browser-QA / golden-replay pass. Never touches the ambient apps/backend/.data/ store: every
+# bar/universe/playbook/run-ledger/evidence-cache directory this backend reads or writes lives
+# under a fresh root, so a "Run Backscan" click (or ANY playbook-touching golden replay) in the
+# browser can never land in the operator's real store (the iter-3 lesson, restated by the iter-6
+# audit for the run-ledger siblings, and made MANDATORY for every playbook journey's replay lane by
+# the iter-7 evaluator's own carry-item: this script -- extended forward, never rewritten -- is now
+# the ONE launcher every playbook golden-replay run (J-01..J-08, and J-10's playbook-touching
+# steps) MUST use; a replay script that instead reaches whatever is already listening on :8301 is
+# the exact hole that carry item closed).
 #
-# This is an iter-7 VARIANT of qa_playbook_iter6_fixture_scoped_backend.sh, not an edit of it —
-# both scripts stay usable; this one is the ONLY backend entry point for this iteration's test/
-# browser work (per the phase spec's own instruction). It reuses
-# seed_playbook_iter7_backscan_fixture.py, which itself reuses seed_playbook_fixture_rig.py's own
-# main() verbatim (never a second implementation of the DECOR/RTAAA/DTAAA fixtures).
+# goal-playbook-iter-8 (J-08) EXTENDS this iter-7 file in place (per this iteration's own
+# instruction: extend the launcher forward, never rewrite it) rather than spawning an iter-8
+# variant — the launcher stays SINGULAR precisely so "the mandatory launcher" never becomes
+# ambiguous between iterations. It adds:
+#   - the evidence projection cache's own scoping var (TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB),
+#     kept under $ROOT exactly like every other playbook store/log dir;
+#   - seed_playbook_iter8_evidence_fixture.py (reusing seed_playbook_iter7_backscan_fixture.py's
+#     own main() verbatim, in turn reusing seed_playbook_fixture_rig.py's — never a second
+#     implementation of the DECOR/RTAAA/DTAAA/BSCAN fixtures), which on top of everything iter-7
+#     already seeded ALSO plants twelve OHB01..OHB12 members firing the SAME canonical
+#     open_high_break session as BSCAN, on 2026-06-25 (a FRESH date — deliberately NOT 2026-06-22,
+#     which would re-record the date J-07's own golden asserts is still missing) — giving the
+#     evidence fold's (open_high_break, long, *) cells n >= PLAYBOOK_MIN_N_DISCLOSURE at the short
+#     horizons beside its OWN 1h/4h cells at n = 0, which are below_min_n for free.
 #
-# What it seeds, on top of the iter-6 rig's own 2026-06-22 (DECOR/RTAAA/DTAAA, one playbook record
-# already computed):
-#   - BSCAN — a plain canonical open_high_break firing session, planted on TWO new dates
-#     (2026-06-23, 2026-06-24), each with its own 10 prior baseline sessions, LEFT UNRECORDED in
-#     the playbook store.
-#   - a fourth, NEW universe snapshot naming all four members (universe registration is
-#     append-only — this never edits iter-6's own three-member snapshot). Registering BSCAN
-#     changes playbook_input_signature (it hashes members ∪ {SPY}), so 2026-06-22's own
-#     three-member record no longer matches the CURRENT signature either — a plan preview over
-#     [2026-06-22, 2026-06-24] honestly reports all THREE dates missing, and a real "Run Backscan"
-#     click has genuine, non-trivial work to do on all three (the old three-member record stays on
-#     disk, untouched — append-only, a new version is minted beside it, never over it).
+# goal-playbook-iter-8 FIX PASS (audit finding B2) extends it once more, again in place: the seed
+# entry point becomes seed_playbook_iter8_replay_rig.py, which reuses the evidence seeder's main()
+# verbatim and then adds what the REMAINING required goldens need, so all EIGHT required-still-
+# passing journeys (J-01..J-07, J-10) replay green against THIS one backend instead of five of them
+# silently requiring the operator's real store: a weekday-only daily-bar calendar (CALDR) that makes
+# J-01's and J-03's non-session refusals reachable, the canonical open_low_break / JBE / DBI
+# sessions on 2026-08-07 (J-02, J-04), and every AAPL bar series copied verbatim from the real store
+# (read-only) so J-10's /structure step measures the kept product, not a fixture. See that script's
+# own docstring for the nineteen-member universe and the two computes it records.
+#
+# The default root name changes to playbook-iter8-replay-fixture-qa (a genuinely FRESH root, never
+# an earlier one reused) — the universe/signature composition is wider again, and the script's own
+# long-standing rule ("use a fresh root whenever the seeded composition changed") applies to this
+# extension exactly as it would to detector logic.
 #
 # Usage:
 #   bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh [root_dir] [port]
 #
-#   root_dir  Fresh root to seed (default: ${TMPDIR:-/tmp}/playbook-iter7-fixture-qa). Use a
-#             FRESH one whenever detector logic OR the back-scan module changed: playbook records
-#             are append-only and keyed (session_date, playbook_input_signature), so a root seeded
-#             by an older build would keep serving that build's recorded signals at the same
-#             signature.
+#   root_dir  Fresh root to seed (default: ${TMPDIR:-/tmp}/playbook-iter8-replay-fixture-qa). Use a
+#             FRESH one whenever detector logic, the back-scan module, OR the seeded fixture
+#             composition changed: playbook records are append-only and keyed
+#             (session_date, playbook_input_signature), so a root seeded by an older build would
+#             keep serving that build's recorded signals at the same signature.
 #   port      Backend port (default: 8301, the era's browser-QA rig convention — pair with
 #             `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`).
 set -euo pipefail
@@ -43,7 +57,7 @@ SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
 REPO_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"
 
-ROOT="${1:-${TMPDIR:-/tmp}/playbook-iter7-fixture-qa}"
+ROOT="${1:-${TMPDIR:-/tmp}/playbook-iter8-replay-fixture-qa}"
 PORT="${2:-8301}"
 
 BAR_DIR="$ROOT/bars"
@@ -51,6 +65,7 @@ UNIVERSE_DIR="$ROOT/universe"
 PLAYBOOK_DIR="$ROOT/playbook"
 PLAYBOOK_LOG_DIR="$ROOT/playbook_runs"
 PLAYBOOK_BACKSCAN_LOG_DIR="$ROOT/playbook_backscan_runs"
+PLAYBOOK_EVIDENCE_CACHE_DB="$ROOT/playbook_evidence_cache.db"
 SCREEN_DIR="$ROOT/screen"
 DATASET_DIR="$ROOT/datasets"
 BAR_INDEX_DB="$ROOT/bar_index.db"
@@ -65,20 +80,22 @@ export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
 export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
 export TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR="$PLAYBOOK_LOG_DIR"
 export TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR="$PLAYBOOK_BACKSCAN_LOG_DIR"
+export TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB="$PLAYBOOK_EVIDENCE_CACHE_DB"
 export TAPEOLOGY_DESK_SCREEN_DIR="$SCREEN_DIR"
 export TAPEOLOGY_DATASET_DIR="$DATASET_DIR"
 export TAPEOLOGY_BAR_INDEX_DB="$BAR_INDEX_DB"
 export TAPEOLOGY_DATASET_INDEX_DB="$DATASET_INDEX_DB"
 export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"
 
-"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_playbook_iter7_backscan_fixture.py" "$ROOT"
+"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_playbook_iter8_replay_rig.py" "$ROOT"
 
-echo "[playbook-iter7-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
+echo "[playbook-iter8-replay-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
 for var in TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR \
            TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR \
+           TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB \
            TAPEOLOGY_DESK_SCREEN_DIR TAPEOLOGY_DATASET_DIR TAPEOLOGY_BAR_INDEX_DB \
            TAPEOLOGY_DATASET_INDEX_DB TAPEOLOGY_JOURNAL_DB; do
-  echo "[playbook-iter7-fixture-scoped-backend] $var=${!var}" >&2
+  echo "[playbook-iter8-replay-fixture-scoped-backend] $var=${!var}" >&2
 done
 
 exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
diff --git a/apps/backend/tests/test_desk_playbook_backscan.py b/apps/backend/tests/test_desk_playbook_backscan.py
index 1bc2d4f..edeeac7 100644
--- a/apps/backend/tests/test_desk_playbook_backscan.py
+++ b/apps/backend/tests/test_desk_playbook_backscan.py
@@ -27,6 +27,7 @@ from app.research.desk_playbook_backscan import (
     DeskPlaybookBackscanComputeManager,
     PlaybookNotScopedError,
     _assert_scoped,
+    malformed_days,
     plan_backscan,
     resolve_desk_playbook_backscan_log_dir,
     run_backscan,
@@ -140,6 +141,101 @@ def test_tc17_an_inverted_range_is_an_honest_empty_plan(tmp_path, env):
     }
 
 
+# --- goal-playbook-iter-8 TC-9: a malformed/partial date is an honest empty plan, never a 500 ------
+
+
+def test_iter8_tc9_a_malformed_from_date_is_an_honest_empty_plan_not_a_500(tmp_path, env):
+    """A half-typed From box (``2026-06-2``, mid-keystroke) used to raise ``ValueError`` straight
+    out of ``date.fromisoformat`` -- the SAME empty-plan shape the already-handled inverted-range
+    case (TC-17) returns, never an exception."""
+    bar_store, universe_store, playbook_store = env
+    result = plan_backscan("2026-06-2", D2, bar_store, [], CONFIG.config_fingerprint(), playbook_store)
+    assert result == {
+        "from": "2026-06-2", "to": D2,
+        "playbook_input_signature": compute_playbook_input_signature(bar_store, [], CONFIG.config_fingerprint()),
+        "dates": [], "total": 0, "missing": 0,
+    }
+
+
+def test_iter8_tc9_a_malformed_to_date_is_also_an_honest_empty_plan(tmp_path, env):
+    bar_store, universe_store, playbook_store = env
+    result = plan_backscan(D0, "not-a-date", bar_store, [], CONFIG.config_fingerprint(), playbook_store)
+    assert result["dates"] == [] and result["total"] == 0 and result["missing"] == 0
+
+
+def test_iter8_tc9_route_level_malformed_date_returns_http_200_never_500(tmp_path, monkeypatch):
+    """Route-level companion (mirrors ``test_tc9_route_level_stub_barstore_returns_http_200_...``
+    above): ``GET .../backscan/plan?from=2026-06-2&to=...`` returns an honest HTTP 200 empty plan,
+    never the HTTP 500 the uncaught ``ValueError`` used to produce."""
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
+    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(store, CONFIG)
+    set_registry(registry)
+
+    with TestClient(app) as client:
+        response = client.get(
+            "/research/desk/playbook/backscan/plan", params={"from": "2026-06-2", "to": D2}
+        )
+    assert response.status_code == 200
+    body = response.json()
+    assert body["dates"] == [] and body["total"] == 0 and body["missing"] == 0
+
+    set_registry(None)
+    store.close()
+
+
+# --- goal-playbook-iter-8 AUDIT (B1): the plan READ tolerates a malformed date; the TRIGGER must
+# refuse it outright, never start a phantom job that appends an un-prunable "done" ledger row -------
+
+
+def test_audit_b1_malformed_days_names_only_the_unparseable_boundaries():
+    """The ONE shared parse rule: an inverted range is NOT malformed (both boundaries are real
+    days, it simply names an empty span -- TC-17's honestly-empty walk stays legitimate)."""
+    assert malformed_days(D0, D2) == []
+    assert malformed_days(D2, D0) == []  # inverted, but both are real calendar days
+    assert malformed_days("2026-06-2", D2) == ["2026-06-2"]
+    assert malformed_days(D0, "not-a-date") == ["not-a-date"]
+    assert malformed_days("2026-06-2", "") == ["2026-06-2", ""]
+
+
+def test_audit_b1_trigger_refuses_a_malformed_date_and_writes_no_ledger_row(route_ctx):
+    """Before this fix the iter-8 ``_planned_dates`` try/except turned a half-typed From box into
+    an HTTP 200 ``started: true`` job over ZERO dates, which then finalized ``"done"`` and appended
+    a permanent ``{"from": "2026-06-2", ..., "status": "done", "planned_total": 0}`` row to the
+    append-only run ledger -- a false success over a string nothing could parse, in a store the
+    immutable-data rail forbids ever pruning. The trigger now refuses (422) BEFORE any job exists,
+    the ``trigger_desk_playbook_compute`` non-session pre-check precedent verbatim."""
+    client, manager, _tmp = route_ctx
+
+    response = client.post(
+        "/research/desk/playbook/backscan/compute",
+        json={"from_day": "2026-06-2", "to_day": D2},
+    )
+    assert response.status_code == 422
+    assert "2026-06-2" in response.json()["detail"]
+
+    assert manager.snapshot()["status"] == "idle"  # no job was ever created
+    runs = client.get("/research/desk/playbook/backscan/runs").json()
+    assert runs["runs"] == [] and runs["latest"] is None  # and no ledger row was written
+
+
+def test_audit_b1_an_inverted_range_still_starts_an_honestly_empty_walk(route_ctx):
+    """The refusal is scoped to UNPARSEABLE boundaries only -- TC-17's inverted-but-real range
+    keeps its established behavior (a started job that walks zero dates and records its own honest
+    ledger row), so this fix narrows nothing the spec already decided."""
+    client, manager, _tmp = route_ctx
+    response = client.post(
+        "/research/desk/playbook/backscan/compute", json={"from_day": D2, "to_day": D0}
+    )
+    assert response.status_code == 200
+    assert response.json()["started"] is True
+    snap = _wait_for_terminal(manager)
+    assert snap["status"] == "done" and snap["planned_total"] == 0
+
+
 class _RaisingBarStore:
     """A stub proving ``plan_backscan`` performs ZERO ``BarStore`` bar-CONTENT reads (TC-9) --
     every content-reading method raises; ``list`` (metadata-only, exactly what
diff --git a/apps/backend/tests/test_desk_playbook_guards.py b/apps/backend/tests/test_desk_playbook_guards.py
index 10c2f8a..a3c3c15 100644
--- a/apps/backend/tests/test_desk_playbook_guards.py
+++ b/apps/backend/tests/test_desk_playbook_guards.py
@@ -10,6 +10,13 @@ one call-COUNTING instrumentation (a stub/counting double patched onto the real
 desk's own structural-wall computations" is a property of RUNTIME CALLS a source-scan regex could
 not usefully police either (the playbook module imports neither function today, but a future
 refactor could introduce an indirect call path a regex would miss; instrumentation survives that).
+goal-playbook-iter-8 (J-08) retires guard (b)'s own "does not exist yet" companion fact (the
+evidence module now exists) and adds two of its own, kept beside the class/behavior they guard
+rather than duplicated here: ``PlaybookEvidenceCache`` has no ``update``/``delete`` method
+(``test_desk_playbook_evidence.py::test_playbook_evidence_cache_has_no_update_or_delete_method`` --
+the ``test_playbook_store_has_no_update_or_delete_method`` per-file precedent), and the pooling
+code never merges two signatures into one cell (``test_desk_playbook_evidence.py``'s own TC-5 --
+another property of DATA a fixture proves directly, not code SHAPE a regex would usefully police).
 
 (a) TC-12 -- the no-threshold-sweep guard: no playbook module (``desk_playbook.py``,
     ``desk_playbook_detect.py``, ``desk_playbook_features.py``) contains a ``for``/comprehension
@@ -222,14 +229,19 @@ def _repo_root() -> pathlib.Path:
     return pathlib.Path(__file__).resolve().parents[3]
 
 
-def test_desk_playbook_evidence_module_does_not_exist_yet():
-    """A companion structural fact this guard's own docstring leans on: ``desk_playbook_evidence.py``
-    genuinely does not exist yet this iteration (J-08) -- the import-graph guard above is a forward
-    guard, not (yet) an enforcement of an existing exclusion."""
+def test_desk_playbook_evidence_module_now_exists_and_still_imports_nothing_from_detect():
+    """goal-playbook-iter-8 (J-08) UPDATE: ``desk_playbook_evidence.py`` now exists (replacing the
+    iter-4-era ``test_desk_playbook_evidence_module_does_not_exist_yet`` forward guard, which this
+    iteration is exactly what makes obsolete). The import-graph guard above is now a LIVE
+    enforcement rather than a forward one: the required direction is detect -> (never evidence),
+    proven both ways -- the evidence module exists, and it is STILL never imported by detect."""
     evidence_path = (
         _repo_root() / "apps" / "backend" / "app" / "research" / "desk_playbook_evidence.py"
     )
-    assert not evidence_path.exists()
+    assert evidence_path.exists()
+    source = open(desk_playbook_detect_module.__file__, encoding="utf-8").read()
+    hits = [line for line in _import_lines(source) if "evidence" in line.lower()]
+    assert not hits
 
 
 # --- (c) TC-5 -- the marker-decoration forward-only guard (goal-playbook-iter-5, J-05) -------------
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 0c328bf..bc59dca 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -179,6 +179,12 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
 # none of these are prices, but the IN SCOPE contract for this panel is "no client-side arithmetic
 # on served numerics" full stop, so they are guarded here on the same footing as the price fields
 # above rather than left to convention.
+# goal-playbook-iter-8 (J-08): extended AGAIN for the new Playbook Evidence section's own served
+# numerics -- the evidence table renders `cell.signal.*`/`cell.baseline.*` (n/n_truncated/
+# n_baseline/median_pct/p25_pct/p75_pct/mean_pct) verbatim per (setup_id, side, measure) row, and
+# the invalidation-breach line renders `breach.breached_count`/`breach.total_count` verbatim --
+# every one of these is a straight pass-through of `GET /research/desk/playbook/evidence`, never a
+# client-recomputed spread, ratio, or rate.
 _PRICE_ARITHMETIC_FIELDS = (
     r"row\.(?:distance_bps|price_low|price_high|reference_close"
     r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
@@ -197,6 +203,9 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|plan\.(?:total|missing)"
     r"|compute\.(?:planned_total|completed)"
     r"|outcomes\.(?:reused|recorded|refused_non_session|failed)"
+    r"|cell\.signal\.(?:n|n_truncated|median_pct|p25_pct|p75_pct|mean_pct)"
+    r"|cell\.baseline\.(?:n_baseline|median_pct|p25_pct|p75_pct|mean_pct)"
+    r"|breach\.(?:breached_count|total_count)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -348,6 +357,22 @@ def test_desk_page_price_arithmetic_guard_catches_range_family_field_arithmetic(
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_rvol_ratio) is not None
 
 
+def test_desk_page_price_arithmetic_guard_catches_evidence_field_arithmetic():
+    """goal-playbook-iter-8 (J-08) counter-test: the extended guard catches arithmetic on the new
+    Playbook Evidence section's own `cell.signal.*`/`cell.baseline.*`/`breach.*` bindings."""
+    seeded_spread = "const spread = cell.signal.p75_pct - cell.signal.p25_pct;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_spread) is not None
+
+    seeded_skew = "const skew = cell.signal.mean_pct - cell.baseline.mean_pct;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_skew) is not None
+
+    seeded_count = "const observed = cell.signal.n - cell.signal.n_truncated;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_count) is not None
+
+    seeded_rate = "const rate = breach.breached_count / breach.total_count;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_rate) is not None
+
+
 # goal-playbook-iter-4 audit (F1): `base_lows_ascending` is ONE served field name carrying the
 # direction-appropriate triangle check underneath (non-decreasing LOWS for `jbe`, non-increasing
 # HIGHS for `dbi` -- see `desk_playbook_detect._base_lows_ascending`). The continuation geometry
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index bddea2c..eb31c98 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -32,6 +32,7 @@ import {
   fetchDeskPlaybookBackscanPlan,
   fetchDeskPlaybookBackscanRuns,
   fetchDeskPlaybookCompute,
+  fetchDeskPlaybookEvidence,
   fetchDeskPlaybookRuns,
   triggerDeskDeepBackfillCompute,
   triggerDeskForwardCompute,
@@ -62,6 +63,10 @@ import type {
   DeskPlaybookBackscanRun,
   DeskPlaybookBackscanRunsListResult,
   DeskPlaybookComputeSnapshot,
+  DeskPlaybookEvidence,
+  DeskPlaybookEvidenceBreach,
+  DeskPlaybookEvidenceCell,
+  DeskPlaybookEvidenceOtherSignature,
   DeskPlaybookReadResult,
   DeskPlaybookRecord,
   DeskPlaybookRun,
@@ -3744,6 +3749,192 @@ function BackscanRunsSection({
   );
 }
 
+// --- Playbook Evidence (Era B2, J-08) -- goal-playbook-iter-8: a read-only fold of every recorded
+// playbook signal at ONE signature into per-(setup_id, side, measure) distribution cells beside
+// the pooled seeded baseline, rendered BELOW the shipped Backscan panel (the blueprint's own
+// reserved "Playbook Evidence" IA slot). No client-side arithmetic anywhere in this section --
+// every number below is a straight pass-through of GET /research/desk/playbook/evidence
+// (test_desk_ui_guards.py's own `cell.signal.*`/`cell.baseline.*`/`breach.*` guard). No new user
+// action beyond scrolling (T-7: GETs never compute) -- this section carries no refresh/compute
+// control of its own, unlike every OTHER section on this page.
+
+function PlaybookEvidenceCellRow({ cell }: { cell: DeskPlaybookEvidenceCell }) {
+  return (
+    <tr data-testid="desk-evidence-cell-row" className="border-t border-slate-800/60">
+      <td className="whitespace-nowrap px-1.5 py-1 text-left font-mono text-xs text-slate-300">{cell.setup_id}</td>
+      <td className="whitespace-nowrap px-1.5 py-1 text-left font-mono text-xs text-slate-400">{cell.side}</td>
+      <td className="whitespace-nowrap px-1.5 py-1 text-left font-mono text-xs text-slate-400">{cell.measure}</td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-signal-n">
+        {fmt(cell.signal.n, 0)}
+      </td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(cell.signal.n_truncated, 0)}</td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-signal-median">
+        {fmt(cell.signal.median_pct)}
+      </td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(cell.signal.p25_pct)}</td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(cell.signal.p75_pct)}</td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(cell.signal.mean_pct)}</td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-baseline-n">
+        {fmt(cell.baseline.n_baseline, 0)}
+      </td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(cell.baseline.median_pct)}</td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(cell.baseline.p25_pct)}</td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(cell.baseline.p75_pct)}</td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(cell.baseline.mean_pct)}</td>
+      <td className="px-1.5 py-1 text-center">
+        {cell.below_min_n ? (
+          <span
+            data-testid="desk-evidence-below-min-n"
+            className="rounded border border-amber-800/60 bg-amber-950/40 px-1.5 py-0.5 text-[10px] text-amber-300"
+          >
+            low n
+          </span>
+        ) : (
+          <span className="text-[10px] text-slate-600">—</span>
+        )}
+      </td>
+    </tr>
+  );
+}
+
+function PlaybookEvidenceCellsTable({ cells }: { cells: DeskPlaybookEvidenceCell[] }) {
+  return (
+    <div className="overflow-x-auto">
+      <table data-testid="desk-evidence-cells-table" className="w-full min-w-[900px] border-collapse text-xs">
+        <thead>
+          <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-500">
+            <th className="px-1.5 py-1 text-left" rowSpan={2}>
+              Setup
+            </th>
+            <th className="px-1.5 py-1 text-left" rowSpan={2}>
+              Side
+            </th>
+            <th className="px-1.5 py-1 text-left" rowSpan={2}>
+              Measure
+            </th>
+            <th className="px-1.5 py-1 text-center" colSpan={6}>
+              Signal
+            </th>
+            <th className="px-1.5 py-1 text-center" colSpan={5}>
+              Baseline
+            </th>
+            <th className="px-1.5 py-1 text-center" rowSpan={2}>
+              Flag
+            </th>
+          </tr>
+          <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-500">
+            <th className="px-1.5 py-1 text-right">n</th>
+            <th className="px-1.5 py-1 text-right">trunc</th>
+            <th className="px-1.5 py-1 text-right">median</th>
+            <th className="px-1.5 py-1 text-right">p25</th>
+            <th className="px-1.5 py-1 text-right">p75</th>
+            <th className="px-1.5 py-1 text-right">mean</th>
+            <th className="px-1.5 py-1 text-right">n</th>
+            <th className="px-1.5 py-1 text-right">median</th>
+            <th className="px-1.5 py-1 text-right">p25</th>
+            <th className="px-1.5 py-1 text-right">p75</th>
+            <th className="px-1.5 py-1 text-right">mean</th>
+          </tr>
+        </thead>
+        <tbody>
+          {cells.map((cell) => (
+            <PlaybookEvidenceCellRow key={`${cell.setup_id}:${cell.side}:${cell.measure}`} cell={cell} />
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
+function PlaybookEvidenceBreachRow({ breach }: { breach: DeskPlaybookEvidenceBreach }) {
+  return (
+    <tr data-testid="desk-evidence-breach-row" className="border-t border-slate-800/60">
+      <td className="whitespace-nowrap px-1.5 py-1 text-left font-mono text-xs text-slate-300">{breach.setup_id}</td>
+      <td className="whitespace-nowrap px-1.5 py-1 text-left font-mono text-xs text-slate-400">{breach.side}</td>
+      <td className="whitespace-nowrap px-1.5 py-1 text-left font-mono text-xs text-slate-400">{breach.horizon}</td>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-evidence-breach-count">
+        {fmt(breach.breached_count, 0)}
+      </td>
+      <td className={ROW_NUMERIC_CELL}>{fmt(breach.total_count, 0)}</td>
+    </tr>
+  );
+}
+
+function PlaybookEvidenceBreachTable({ breaches }: { breaches: DeskPlaybookEvidenceBreach[] }) {
+  return (
+    <div className="mt-4 overflow-x-auto">
+      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Invalidation breaches</h3>
+      <table data-testid="desk-evidence-breach-table" className="w-full border-collapse text-xs">
+        <thead>
+          <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-500">
+            <th className="px-1.5 py-1 text-left">Setup</th>
+            <th className="px-1.5 py-1 text-left">Side</th>
+            <th className="px-1.5 py-1 text-left">Horizon</th>
+            <th className="px-1.5 py-1 text-right">Breached</th>
+            <th className="px-1.5 py-1 text-right">Total</th>
+          </tr>
+        </thead>
+        <tbody>
+          {breaches.map((breach) => (
+            <PlaybookEvidenceBreachRow key={`${breach.setup_id}:${breach.side}:${breach.horizon}`} breach={breach} />
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
+function PlaybookEvidenceOtherSignatures({ entries }: { entries: DeskPlaybookEvidenceOtherSignature[] }) {
+  if (entries.length === 0) return null;
+  return (
+    <div className="mt-4" data-testid="desk-evidence-other-signatures">
+      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
+        Other signatures (listed, never pooled)
+      </h3>
+      <ul className="space-y-1 text-xs text-slate-400">
+        {entries.map((entry) => (
+          <li key={entry.signature} data-testid="desk-evidence-other-signature-row">
+            <span className="font-mono text-slate-300">{entry.signature}</span> — {entry.dates.length} date
+            {entry.dates.length === 1 ? "" : "s"} ({entry.created_span.from} .. {entry.created_span.to})
+          </li>
+        ))}
+      </ul>
+    </div>
+  );
+}
+
+function PlaybookEvidenceSection({
+  result,
+}: {
+  result: { ok: boolean; data: DeskPlaybookEvidence | null; error?: string } | null;
+}) {
+  if (result === null) {
+    return <LoadingPanel testid="desk-evidence-loading" />;
+  }
+  if (!result.ok || result.data === null) {
+    return (
+      <UnavailablePanel
+        testid="desk-evidence-unavailable"
+        message={result.error ?? "The playbook evidence view could not be loaded."}
+      />
+    );
+  }
+  const data = result.data;
+  const hasAnySignal = data.cells.some((cell) => cell.signal.n > 0);
+  return (
+    <div data-testid="desk-evidence-section">
+      <p className="mb-3 text-xs text-slate-500">{data.register}</p>
+      {hasAnySignal ? (
+        <PlaybookEvidenceCellsTable cells={data.cells} />
+      ) : (
+        <EmptyState testid="desk-evidence-empty" title="No playbook signals recorded at the current signature yet." />
+      )}
+      <PlaybookEvidenceBreachTable breaches={data.invalidation_breached} />
+      <PlaybookEvidenceOtherSignatures entries={data.other_signatures} />
+    </div>
+  );
+}
+
 // era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
 // operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
 // many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
@@ -5636,6 +5827,15 @@ export default function DeskPage() {
   const [backscanCancelRequested, setBackscanCancelRequested] = useState(false);
   const [backscanCancelError, setBackscanCancelError] = useState<string | null>(null);
 
+  // goal-playbook-iter-8 (J-08): the Playbook Evidence section's own state — a single mount-time
+  // read (T-7: GETs never compute), no compute manager, no From/To, no trigger/cancel of any kind
+  // — the simplest state shape on this whole page.
+  const [evidenceResult, setEvidenceResult] = useState<{
+    ok: boolean;
+    data: DeskPlaybookEvidence | null;
+    error?: string;
+  } | null>(null);
+
   // The chained refresh (see the REFRESH-CHAIN block above). `refreshChain` is plain state and is
   // deliberately NOT persisted: a reload clears it and nothing resumes, which is what keeps "every
   // run is an explicit operator act" true structurally rather than by convention. Whatever job was
@@ -5733,6 +5933,13 @@ export default function DeskPage() {
     fetchDeskPlaybookBackscanRuns().then((result) => {
       if (alive) setBackscanRunsResult(result);
     });
+    // goal-playbook-iter-8 (J-08): seeds the Playbook Evidence section — a single mount-time read,
+    // joined into this SAME effect rather than opening a new one (the page's effect census is
+    // pinned; see test_desk_refresh_chain_guard.py). No poll, no re-fire on any input: T-7 ("GETs
+    // never compute") means there is nothing to re-trigger this section's own read.
+    fetchDeskPlaybookEvidence().then((result) => {
+      if (alive) setEvidenceResult(result);
+    });
     return () => {
       alive = false;
     };
@@ -7111,6 +7318,18 @@ export default function DeskPage() {
             </div>
           </Panel>
         </section>
+
+        {/* goal-playbook-iter-8 (J-08): the Playbook Evidence section, rendered directly BELOW the
+            shipped Backscan panel above — Blueprint's own pre-reserved "Playbook Evidence" slot in
+            runs/goal-session-playbook/state/blueprint.md's Information Architecture. Rendered
+            unconditionally, the SAME "always rendered" precedent every other section on this page
+            already establishes. No compute/refresh control here at all (T-7) — a pure read-only
+            fold of what the playbook store already recorded. */}
+        <section aria-label="Playbook Evidence" className="mt-6">
+          <Panel title="Playbook Evidence">
+            <PlaybookEvidenceSection result={evidenceResult} />
+          </Panel>
+        </section>
       </main>
     </div>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index b521329..cf426f5 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -21,6 +21,7 @@ import type {
   DeskPlaybookBackscanPlan,
   DeskPlaybookBackscanRunsListResult,
   DeskPlaybookComputeSnapshot,
+  DeskPlaybookEvidence,
   DeskPlaybookReadResult,
   DeskPlaybookRunsListResult,
   DeskScreenPinsResult,
@@ -1976,3 +1977,30 @@ export async function fetchDeskPlaybookBackscanRuns(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// GET /research/desk/playbook/evidence (Era B2, J-08) — the pooled evidence fold at the current
+// default signature, served VERBATIM (no client-side arithmetic anywhere downstream — every
+// number the Playbook Evidence section renders is a straight pass-through of this body). A plain
+// read (T-7: GETs never compute) — no compute manager, no trigger, no poll.
+export async function fetchDeskPlaybookEvidence(): Promise<{
+  ok: boolean;
+  data: DeskPlaybookEvidence | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/playbook/evidence`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskPlaybookEvidence };
+    }
+    let error = "The playbook evidence view could not be loaded.";
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
index 8e1cb09..d841389 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1740,6 +1740,60 @@ export interface DeskPlaybookBackscanRunsListResult {
   integrity_errors: { file: string; error: string }[];
 }
 
+// The Playbook Evidence view (Era B2, J-08) -- GET /research/desk/playbook/evidence's own served
+// shapes. `DeskPlaybookEvidenceCellStats` deliberately does NOT reuse `DeskForwardAvgCell`: the
+// evidence fold serves p25_pct/p75_pct the rail's own avg cell never had (desk_playbook_evidence.py
+// pools them with its own new quartile math -- see that module's docstring for why this is NOT a
+// second implementation of the rail).
+export interface DeskPlaybookEvidenceCellStats {
+  n: number;
+  n_truncated: number;
+  median_pct: number | null;
+  p25_pct: number | null;
+  p75_pct: number | null;
+  mean_pct: number | null;
+}
+
+export interface DeskPlaybookEvidenceBaselineStats {
+  n_baseline: number;
+  median_pct: number | null;
+  p25_pct: number | null;
+  p75_pct: number | null;
+  mean_pct: number | null;
+}
+
+export interface DeskPlaybookEvidenceCell {
+  setup_id: string;
+  side: "long" | "short";
+  measure: string;
+  signal: DeskPlaybookEvidenceCellStats;
+  baseline: DeskPlaybookEvidenceBaselineStats;
+  below_min_n: boolean;
+}
+
+export interface DeskPlaybookEvidenceBreach {
+  setup_id: string;
+  side: "long" | "short";
+  horizon: string;
+  breached_count: number;
+  total_count: number;
+}
+
+export interface DeskPlaybookEvidenceOtherSignature {
+  signature: string;
+  dates: string[];
+  created_span: { from: string; to: string };
+}
+
+export interface DeskPlaybookEvidence {
+  signature: string;
+  cells: DeskPlaybookEvidenceCell[];
+  invalidation_breached: DeskPlaybookEvidenceBreach[];
+  other_signatures: DeskPlaybookEvidenceOtherSignature[];
+  parameters: DeskPlaybookParameters;
+  register: string;
+}
+
 // ONE registered universe membership snapshot's own served meta -- `UniverseStore.record`'s return
 // value verbatim (desk_universe.py's `meta` dict), which `POST /research/desk/universe/fetch`
 // serves under its `universe` key. Every field is the store's own; nothing here is derived. The
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index 77b2cc7..392112c 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -230,6 +230,31 @@ else
   [[ -n "$_fe_tail" ]] && { echo "[browser-qa] Frontend start log tail (${QA_FRONTEND_LOG:-?}):" >&2; echo "$_fe_tail" >&2; }
 fi
 
+# ── Store-scope gate (project-declared; automation/store-scope/) ─────────────
+# BEFORE any lane touches a browser: prove the backend under test is the
+# project's scoped QA backend, and baseline its protected store paths. A project
+# without project-extensions/store-scope/store-scope.env is unaffected — both
+# calls no-op and every variable below keeps its default.
+#
+# WHY it gates here and not inside the replay lane alone: BOTH lanes drive the
+# same browser at the same frontend, so a golden replay and an LLM dispatch have
+# exactly the same power to make the app write into the operator's real store
+# (tapeology goal-playbook-iter-8: a replayed "Run Backscan" click computed three
+# real records and appended an un-prunable ledger row). Refusing here is the only
+# place that covers both. A refusal reuses the REL-14 shape — no dispatch, an
+# out-of-band token, journeys scored pending-infra — because an unscopeable
+# backend is an environment fault, not a product regression.
+STORE_SCOPE_BLOCKED="no"
+STORE_SCOPE_MANIFEST="${CHAIN_TMPDIR:-${TMPDIR:-/tmp}}/store-scope-$PHASE.$$.manifest"
+STORE_SCOPE_REPORT="$REPO_ROOT/reports/qa/${PHASE}-store-scope-guard.md"
+if ! store_scope_require; then
+  STORE_SCOPE_BLOCKED="yes"
+  FRONTEND_AVAILABLE="no"
+  FRONTEND_SKIP_REASON="backend under test is not the project's scoped QA backend — browser lanes refused (store-scope guard)"
+  echo "[browser-qa] STORE-SCOPE REFUSAL: the backend serving this frontend is not the project's scoped QA backend. Neither the replay lane nor the browser-qa dispatch will run — an automated pass against the operator's real store is exactly the defect this guard prevents." >&2
+fi
+store_scope_snapshot "$STORE_SCOPE_MANIFEST" || true
+
 # ── Goal-mode deterministic regression replay (replay-gap fix) ───────────────
 # For goal-session iterations (phase name `goal-<sid>-iter-<N>` — the same
 # regex run-phase.sh keys its evaluator-log pre-trim on) this step runs the
@@ -345,6 +370,16 @@ if [[ "$GOAL_REPLAY_ACTIVE" == "yes" ]]; then
   _bqa_tok_set="$(echo "$_bqa_tok_set" | tr ' ' '\n' | grep -E '^J-[0-9]+$' | sort -u | tr '\n' ' ' || true)"
   _bqa_tok_set="${_bqa_tok_set% }"
 fi
+if [[ "$STORE_SCOPE_BLOCKED" == "yes" ]]; then
+  # Refused above: skip the dispatch outright and record WHY out of band, the
+  # same way a dead browser is recorded — the journeys were not verified, and
+  # nothing may report them as if they had been.
+  _bqa_infra_blocked="yes"
+  if [[ "$GOAL_REPLAY_ACTIVE" == "yes" && -n "${GOAL_SESSION_DIR:-}" && -n "${GOAL_ITER_INDEX:-}" ]]; then
+    bqa_write_infra_token "$GOAL_SESSION_DIR/iter-$GOAL_ITER_INDEX" "$_bqa_tok_set" \
+      "store-scope guard refused the browser lanes: the backend under test is not the project's scoped QA backend" "store-scope"
+  fi
+fi
 if [[ "${CHAIN_BQA_PREFLIGHT:-false}" == "true" && "$FRONTEND_AVAILABLE" == "yes" ]]; then
   if ! bqa_preflight; then
     _bqa_infra_blocked="yes"
@@ -440,6 +475,34 @@ if [[ "$GOAL_REPLAY_ACTIVE" == "yes" ]]; then
   replay_lane_golden_coverage "$UI_TEST_RESULTS" "$PHASE"
 fi
 
+# ── Store-scope verification (the other half of the gate) ───────────────────
+# Re-read the protected store paths and compare against the baseline taken
+# before the lanes ran. CLEAN writes the disclosure artifact a later reader can
+# cite instead of prose; a BREACH additionally lands a loud section IN the
+# authoritative results file, because that is the one artifact the evaluator and
+# the achievement gate are guaranteed to read. Deliberately NOT an exit: the
+# run's verdicts still have to be published and read — a silent pipeline abort
+# would hide the very thing this section exists to disclose.
+if ! store_scope_verify "$STORE_SCOPE_MANIFEST" "$STORE_SCOPE_REPORT"; then
+  echo "[browser-qa] STORE-SCOPE BREACH — a browser lane wrote into a protected store path this run. See $STORE_SCOPE_REPORT." >&2
+  if [[ -f "$UI_TEST_RESULTS" ]]; then
+    {
+      echo ""
+      echo "## Store-scope breach (automated guard)"
+      echo ""
+      echo "_A browser lane in THIS run wrote into a path the project declares protected"
+      echo "(append-only records/ledgers of the operator's real store). The affected files are"
+      echo "listed in \`reports/qa/${PHASE}-store-scope-guard.md\`. Any claim in this report that"
+      echo "the operator's store was untouched is contradicted by that artifact._"
+    } >> "$UI_TEST_RESULTS" 2>/dev/null || true
+  fi
+  if declare -F record_telemetry_event >/dev/null 2>&1; then
+    record_telemetry_event "store_scope_breach" "$(jq -cn --arg n "$PHASE" --arg r "reports/qa/${PHASE}-store-scope-guard.md" \
+        '{iter_name:$n, disclosure:$r}' 2>/dev/null || printf '{"iter_name":"%s"}' "$PHASE")"
+  fi
+fi
+rm -f "$STORE_SCOPE_MANIFEST" 2>/dev/null || true
+
 # REL-14 post-scan (same knob): a dispatch that returned but left no results
 # file (mid-run browser death; quota pauses excluded) or an all-SKIP results
 # file carrying an explicit browser-infra reason also earns the token — no
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index 21e9922..df0aba9 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -337,6 +337,24 @@ cd "$REPO_ROOT"
 
 replay_lane_paths "$ITER_NAME"
 
+# Store-scope gate (project-declared; automation/store-scope/ — no-op without
+# project-extensions/store-scope/store-scope.env). Prove the backend under test
+# is the project's scoped QA backend and baseline its protected store paths
+# BEFORE either lane drives a browser: a golden replay and an LLM dispatch have
+# identical power to make the app write into the operator's real store. A
+# refusal rides the existing FRONTEND_AVAILABLE=no + REL-14 token path (see the
+# parent's dispatch gate below), so no journey is ever reported as verified by a
+# lane that did not run.
+STORE_SCOPE_BLOCKED="no"
+STORE_SCOPE_MANIFEST="${CHAIN_TMPDIR:-${TMPDIR:-/tmp}}/store-scope-${ITER_NAME}.manifest"
+if ! store_scope_require; then
+  STORE_SCOPE_BLOCKED="yes"
+  FRONTEND_AVAILABLE="no"
+  FRONTEND_SKIP_REASON="backend under test is not the project's scoped QA backend — browser lanes refused (store-scope guard)"
+  echo "[goal-iter-lean] STORE-SCOPE REFUSAL: the backend serving $FRONTEND_URL is not the project's scoped QA backend — neither the replay lane nor the LLM dispatch will run." >&2
+fi
+store_scope_snapshot "$STORE_SCOPE_MANIFEST" || true
+
 # Golden partition + lane 1 (deterministic replay) — shared implementation in
 # lib/replay-lane.sh: stale-artifact hygiene, lint-quarantine of invalid
 # goldens, rc=5 → REPLAY_FAILED re-confirm via the LLM lane, rc=6 → service
@@ -366,6 +384,8 @@ _bqa_state_save() {
     printf 'REPLAY_SKIPPED_INFRA=%q\n' "${REPLAY_SKIPPED_INFRA:-}"
     printf 'REPLAY_MASS_FAIL=%q\n'     "${REPLAY_MASS_FAIL:-}"
     printf 'REPLAY_CANARIES=%q\n'      "${REPLAY_CANARIES:-}"
+    printf 'STORE_SCOPE_BLOCKED=%q\n'  "${STORE_SCOPE_BLOCKED:-no}"
+    printf 'STORE_SCOPE_MANIFEST=%q\n' "${STORE_SCOPE_MANIFEST:-}"
     printf 'export QA_BACKEND_HEALTH_URL=%q\n'       "${QA_BACKEND_HEALTH_URL:-}"
     printf 'export QA_BACKEND_START_CMD=%q\n'        "${QA_BACKEND_START_CMD:-}"
     printf 'export QA_BACKEND_LOG=%q\n'              "${QA_BACKEND_LOG:-}"
@@ -819,6 +839,14 @@ bqa_browser_confine
 # the SKIPPED-stub block below keeps the evaluator fed and the merged verdict
 # enum untouched. FRONTEND_AVAILABLE=no paths (single-service projects, REL-12)
 # keep today's honest agent-side SKIP and are never tokenized here.
+if [[ "${STORE_SCOPE_BLOCKED:-no}" == "yes" ]]; then
+  # The store-scope guard refused above: skip the dispatch and record WHY out of
+  # band, exactly like a dead browser — these journeys were NOT verified.
+  _bqa_infra_blocked="yes"
+  echo "[goal-iter-lean] Store-scope guard refused the browser lanes — skipping the LLM browser-qa dispatch for: ${LLM_JOURNEYS:-(none)}" >&2
+  bqa_write_infra_token "$ITER_DIR" "$LLM_JOURNEYS" \
+    "store-scope guard refused the browser lanes: the backend under test is not the project's scoped QA backend" "store-scope"
+fi
 if [[ "${CHAIN_BQA_PREFLIGHT:-false}" == "true" && "$FRONTEND_AVAILABLE" == "yes" \
       && ( -n "$_llm_csv" || "$_use_replay" != "yes" ) ]]; then
   if ! bqa_preflight; then
@@ -882,6 +910,29 @@ fi
 # iteration) — gaps simply return to the LLM lane next iteration.
 replay_lane_golden_coverage "$UI_TEST_RESULTS" "$ITER_NAME"
 
+# Store-scope verification (the other half of the gate): re-read the protected
+# store paths and compare against the pre-lane baseline. CLEAN writes the
+# disclosure artifact a later reader cites instead of prose; a BREACH also lands
+# a loud section in the authoritative results file — the one artifact the
+# evaluator and the achievement gate always read. Never an exit: the verdicts
+# still have to be published, and a silent abort would hide the disclosure.
+if ! store_scope_verify "${STORE_SCOPE_MANIFEST:-}" "$REPO_ROOT/reports/qa/${ITER_NAME}-store-scope-guard.md"; then
+  echo "[goal-iter-lean] STORE-SCOPE BREACH — a browser lane wrote into a protected store path this run. See reports/qa/${ITER_NAME}-store-scope-guard.md" >&2
+  if [[ -f "$UI_TEST_RESULTS" ]]; then
+    {
+      echo ""
+      echo "## Store-scope breach (automated guard)"
+      echo ""
+      echo "_A browser lane in THIS run wrote into a path the project declares protected"
+      echo "(append-only records/ledgers of the operator's real store). The affected files are"
+      echo "listed in \`reports/qa/${ITER_NAME}-store-scope-guard.md\`. Any claim in this report"
+      echo "that the operator's store was untouched is contradicted by that artifact._"
+    } >> "$UI_TEST_RESULTS" 2>/dev/null || true
+  fi
+  record_telemetry_event "store_scope_breach" "$(jq -cn --arg n "$ITER_NAME" --arg r "reports/qa/${ITER_NAME}-store-scope-guard.md" '{iter_name:$n, disclosure:$r}' 2>/dev/null || printf '{"iter_name":"%s"}' "$ITER_NAME")"
+fi
+rm -f "${STORE_SCOPE_MANIFEST:-/nonexistent}" 2>/dev/null || true
+
 # Checkpoint: reusable on resume only with a real PASS/FAIL verdict (never a
 # SKIPPED stub) and the journey signature this run actually covered.
 # SPEED-3: inside the full fork the mark is DEFERRED to the join
diff --git a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
index 00ceb3f..bd7da5d 100644
--- a/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
+++ b/incredible_auto_dev/scripts/automation/lib/replay-lane.sh
@@ -172,6 +172,43 @@ bqa_browser_confine() {
   return 0
 }
 
+# ── STORE-SCOPE guard (project-declared; see automation/store-scope/) ─────────
+# Three thin wrappers around store-scope/store-scope.sh so both callers
+# (browser-qa-phase.sh at full depth, goal-iter-lean.sh at lean) stay
+# one-liners, exactly like bqa_browser_confine above. Every wrapper is a no-op
+# returning 0 when the engine has no store-scope script or the project declares
+# no store-scope.env — the framework stays project-neutral.
+#
+#   store_scope_require            0 = the backend under test is provably the
+#                                  project's scoped QA backend (or the project
+#                                  declares no scope) → browser lanes may run.
+#                                  1 = REFUSE: running a lane now would let an
+#                                  automated pass write into the operator's real
+#                                  store. Callers treat it like the REL-14 infra
+#                                  case: write the token, skip the dispatch.
+#   store_scope_snapshot <file>    baseline the protected store paths.
+#   store_scope_verify <file> [md] 1 = a lane wrote into a protected path
+#                                  (disclosure artifact written either way).
+_store_scope_script() { echo "$_REPLAY_LANE_LIB_DIR/../store-scope/store-scope.sh"; }
+
+store_scope_require() {
+  local s; s="$(_store_scope_script)"
+  [[ -f "$s" ]] || return 0
+  STORE_SCOPE_ROOT="${STORE_SCOPE_ROOT:-${REPO_ROOT:-$PWD}}" bash "$s" require
+}
+
+store_scope_snapshot() {
+  local s; s="$(_store_scope_script)"
+  [[ -f "$s" && -n "${1:-}" ]] || return 0
+  STORE_SCOPE_ROOT="${STORE_SCOPE_ROOT:-${REPO_ROOT:-$PWD}}" bash "$s" snapshot "$1"
+}
+
+store_scope_verify() {
+  local s; s="$(_store_scope_script)"
+  [[ -f "$s" && -n "${1:-}" ]] || return 0
+  STORE_SCOPE_ROOT="${STORE_SCOPE_ROOT:-${REPO_ROOT:-$PWD}}" bash "$s" verify "$1" "${2:-}"
+}
+
 # bqa_preflight — probe → one re-check via ensure_services_running (idempotent:
 # it returns immediately when services already answer) → probe again. Mirrors
 # the REL-5 rc-6 retry shape above. Returns 0 = the dispatch may proceed;
diff --git a/incredible_auto_dev/scripts/automation/run-evals.sh b/incredible_auto_dev/scripts/automation/run-evals.sh
index 55a74b0..50bf85a 100755
--- a/incredible_auto_dev/scripts/automation/run-evals.sh
+++ b/incredible_auto_dev/scripts/automation/run-evals.sh
@@ -184,7 +184,7 @@ fi
 
 # ── 2c. Standalone unit-test scripts (API-free by design) ────────────────────
 _log "2c. tests/automation unit tests"
-for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh tests/automation/test-reset-forensics.sh; do
+for _t in tests/automation/test-escalation-warn.sh tests/automation/test-quota-retry.sh tests/automation/test-goal-inline-tail.sh tests/automation/test-install-gate.sh tests/automation/test-goal-checkpoints.sh tests/automation/test-goal-async-tail.sh tests/automation/test-intent-checkpoint.sh tests/automation/test-doc-drift.sh tests/automation/test-github-preflight.sh tests/automation/test-tmp-cleanup.sh tests/automation/test-goal-retro.sh tests/automation/test-benchmark-runner.sh tests/automation/test-goal-parallel-bqa.sh tests/automation/test-project-template-slice.sh tests/automation/test-phase-telemetry.sh tests/automation/test-testplan-skip.sh tests/automation/test-summary-dedupe.sh tests/automation/test-depth-cadence.sh tests/automation/test-depth-arbiter.sh tests/automation/test-goal-context-slice.sh tests/automation/test-golden-autoderive.sh tests/automation/test-ui-combined.sh tests/automation/test-audit-rerun-cap.sh tests/automation/test-review-packet.sh tests/automation/test-replay-lane.sh tests/automation/test-replay-lane-full.sh tests/automation/test-store-scope-guard.sh tests/automation/test-browser-infra-makeup.sh tests/automation/test-doctor.sh tests/automation/test-engine-lock.sh tests/automation/test-pump-liveness.sh tests/automation/test-goal-iteration-state.sh tests/automation/test-plain-language.sh tests/automation/test-zero-change-guard.sh tests/automation/test-evidence-depth.sh tests/automation/test-closure-gate.sh tests/automation/test-iter-budget.sh tests/automation/test-host-guard.sh tests/automation/test-host-guard-browser.sh tests/automation/test-reset-forensics.sh; do
   if bash "$_t" >/dev/null 2>&1; then
     _pass "unit: $_t"
   else
diff --git a/apps/backend/app/research/desk_playbook_evidence.py b/apps/backend/app/research/desk_playbook_evidence.py
new file mode 100644
index 0000000..0b5898f
--- /dev/null
+++ b/apps/backend/app/research/desk_playbook_evidence.py
@@ -0,0 +1,433 @@
+"""The Playbook Evidence view (Era B2, J-08) -- a READ-ONLY fold of every already-recorded
+``PlaybookStore`` record at ONE signature into per-``(setup_id, side, measure)`` distribution
+cells beside the pooled seeded baseline, honestly tagging low-``n`` cells. Nothing here detects,
+measures, or records anything new -- it reads what ``desk_playbook.py``'s own compute already
+wrote (``PlaybookStore.get``, ``compute_playbook_input_signature``, ``playbook_parameters``, all
+imported verbatim) and folds it.
+
+**Zero re-implementation of the measurement rail.** Every signal's ``forward`` block and every
+baseline anchor's own forward-shaped measurement were ALREADY produced by
+``desk_forward._measure_from`` at compute time (see ``desk_playbook.py``'s own docstring); this
+module never touches a bar, never calls ``_measure_from``, and reuses
+``desk_forward._collect_measures`` (imported verbatim, zero diff) to pool the ALREADY-MEASURED
+per-signal/per-anchor leaves into per-measure value lists with their truncation-exclusion already
+applied. The ONLY genuinely new math here is the quartile fold (``_quartile_stats``) --
+``_collect_measures``/``_avg_cell`` (the rail's own pooling helpers) produce ``n``/``mean_pct``/
+``median_pct``/``n_truncated`` but carry no p25/p75 at all; J-08 needs its own evidence-only fold
+for those two, which is new EVIDENCE math, not a second implementation of anything the rail
+already had.
+
+**The evidence pools exactly ONE signature (a hard anti-goal).** ``fold_evidence`` resolves the
+CURRENT default signature via ``compute_playbook_input_signature`` (the exact function
+``compute_playbook`` itself calls) and only ever folds a file whose own recorded
+``playbook_input_signature`` matches it into ``cells``/``invalidation_breached``; every other
+signature is listed under ``other_signatures`` (its own ``dates``/``created_span``), NEVER pooled.
+``inspect_signature`` (``?signature=``) answers the SAME dates/created-span question for one named
+signature, default or not, without ever touching ``cells`` -- "inspect", never "pool".
+
+**Cells are the FULL declared cross product, never sparse.** Every ``(setup_id, side, measure)``
+combination in ``PLAYBOOK_SETUPS`` x ``("long", "short")`` x ``PLAYBOOK_SIGNAL_MEASURES`` is always
+served, so a combination with zero recorded signals reads ``n: 0`` (an honest absence, never a
+fabricated 0.0 in the mean/median/p25/p75 slots -- ``_quartile_stats`` returns ``None`` across the
+board at ``n == 0``, the ``_avg_cell`` null convention) rather than being silently omitted. This
+also makes the served body deterministic and independent of file-processing order -- byte-identity
+between a cold and a warm cache read (TC-2) does not depend on dict insertion order surviving a
+JSON cache round trip, because ``cells``/``invalidation_breached`` are always built by iterating
+the SAME fixed, declared sequences.
+
+**The projection cache mirrors ``desk_meta_cache.py``'s contract -- a copy-paste precedent, not an
+import.** ``desk_meta_cache.DeskMetaCache`` caches a lightweight META-ONLY projection keyed off
+ONE store's own files; this module's own fold needs a DIFFERENT per-file projection shape (every
+recorded signal's ``forward``/``invalidation_breached`` leaves, grouped by pool key, plus the
+record's own ``baseline_anchors``) that store was never built to hold, and reusing its class across
+an unrelated schema would either widen a foundation file for one caller or force this module to
+smuggle its own shape through a generic blob -- `PlaybookEvidenceCache` below is therefore a fresh,
+small class following the EXACT same rules (stat-keyed by ``(path, size, mtime_ns)``, ``json.dumps``
+WITHOUT ``sort_keys`` so a cache hit reproduces the identical key order a fresh parse would, no
+``update``/``delete`` method anywhere on the class -- a stale row is simply replaced by
+``INSERT OR REPLACE`` under its own path, never edited or removed). Deleting the DB file changes
+nothing about ``fold_evidence``'s OUTPUT -- only how many files must be re-verified through
+``PlaybookStore.get`` to reproduce it (TC-6): an unopenable/deleted cache is a missing
+optimisation, never a failed read (the ``ForwardStore._durable_meta_cache`` rule, applied at the
+FastAPI dependency layer in ``desk_routes.py`` since this module's own functions take the cache as
+a plain optional argument rather than owning a store instance)."""
+
+from __future__ import annotations
+
+import json
+import sqlite3
+import statistics
+import threading
+from pathlib import Path
+
+from .desk_forward import DESK_FORWARD_HORIZONS_MINUTES, _collect_measures
+from .desk_playbook import (
+    PLAYBOOK_MIN_N_DISCLOSURE,
+    PLAYBOOK_SETUPS,
+    PLAYBOOK_SIGNAL_MEASURES,
+    PlaybookStore,
+    compute_playbook_input_signature,
+    playbook_parameters,
+)
+
+__all__ = [
+    "EVIDENCE_REGISTER",
+    "EVIDENCE_TABLE",
+    "PlaybookEvidenceCache",
+    "fold_evidence",
+    "inspect_signature",
+]
+
+# Every side a signal can carry (``desk_playbook_detect.py``'s own complete vocabulary) -- a fixed,
+# declared pair, never discovered from data (see the module docstring: cells are the full cross
+# product, not a sparse "whatever appeared" set).
+_SIDES: tuple[str, ...] = ("long", "short")
+
+# The invalidation-breach horizon vocabulary -- the rail's own four labels plus ``to_close``,
+# mirroring ``desk_playbook._invalidation_breached``'s own served keys exactly (that function is
+# the ONLY writer of this shape; this module only reads and pools it).
+_BREACH_HORIZONS: tuple[str, ...] = tuple(
+    label for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES
+) + ("to_close",)
+
+# The visible honesty register carried by every evidence payload -- the ``PLAYBOOK_REGISTER``/
+# ``FORWARD_REGISTER`` pattern verbatim (a single descriptive string, lint-checked via
+# ``test_copy_discipline.find_violations`` in ``tests/test_desk_playbook_evidence.py``, the SAME
+# per-module precedent those two constants use rather than a change to ``test_copy_discipline.py``
+# itself, which carries no per-register assertion for any existing REGISTER constant either).
+EVIDENCE_REGISTER = (
+    "every recorded playbook signal at ONE input signature, pooled per setup/side/measure into "
+    "forward-return and max-drawdown distributions beside the pooled baseline — the seeded random "
+    "anchors already drawn beside those signals at compute time, one anchor per signal up to each "
+    "session's own per-setup-and-side pooling cap, so a cell whose n_baseline is smaller than its "
+    "n is one where that cap was reached and the two columns do not cover the same set of signals. "
+    "Median, p25, p75, and mean of the "
+    "already-recorded, already-measured values, nothing recomputed and nothing fit to an outcome. "
+    "A cell tagged below_min_n has fewer than the disclosure floor's worth of recorded signals — "
+    "a disclosure, never a filter: its numbers are still served, never hidden, never nulled out "
+    "for being thin. Truncated values are excluded from every median/mean pool with the exclusion "
+    "counted, never silently dropped. A signature other than the current one is listed by its own "
+    "dates and created span, never folded into these cells. No fills and no costs are modeled "
+    "anywhere on this payload, which describes measurements of what already happened and nothing "
+    "about what happens next"
+)
+
+_BUSY_TIMEOUT_MS = 5000
+EVIDENCE_TABLE = "playbook_evidence_meta_cache"
+
+
+class PlaybookEvidenceCache:
+    """The durable, stat-keyed per-file evidence-projection cache for ONE playbook store --
+    ``desk_meta_cache.DeskMetaCache``'s contract, copied fresh (see the module docstring for why a
+    new class rather than an import). Owns nothing: every row only ever remembers one
+    already-verified file's own already-extracted projection, keyed by that file's exact
+    ``(path, size, mtime_ns)``. Deliberately carries no ``update``/``delete`` method anywhere on
+    this class (structural, guard-tested) -- ``insert``/``insert_many`` are ``INSERT OR REPLACE``,
+    idempotent under the identical key a legitimately re-verified file would produce."""
+
+    def __init__(self, db_path: str) -> None:
+        self._db_path = str(db_path)
+        if self._db_path != ":memory:":
+            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
+        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
+        self._conn.row_factory = sqlite3.Row
+        # One connection, several threads (FastAPI's sync-route threadpool) -- the
+        # ``bar_index.py``/``desk_meta_cache.py`` serialization, for the identical reason.
+        self._lock = threading.Lock()
+        if self._db_path != ":memory:":
+            self._conn.execute("PRAGMA journal_mode=WAL")
+        self._conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
+        with self._lock, self._conn:
+            self._conn.execute(
+                f"CREATE TABLE IF NOT EXISTS {EVIDENCE_TABLE} ("
+                "    path         TEXT PRIMARY KEY,"
+                "    size         INTEGER NOT NULL,"
+                "    mtime_ns     INTEGER NOT NULL,"
+                "    meta_json    TEXT NOT NULL)"
+            )
+
+    @property
+    def db_path(self) -> str:
+        return self._db_path
+
+    def lookup(self, path: str, size: int, mtime_ns: int) -> dict | None:
+        """An exact ``(path, size, mtime_ns)`` match -- ANY stat difference (a genuine content
+        change, a moved file, or simply no row yet) is an honest miss, never a stale hit."""
+        with self._lock:
+            row = self._conn.execute(
+                f"SELECT size, mtime_ns, meta_json FROM {EVIDENCE_TABLE} WHERE path=?", (path,)
+            ).fetchone()
+        if row is None or row["size"] != size or row["mtime_ns"] != mtime_ns:
+            return None
+        return json.loads(row["meta_json"])
+
+    def insert(self, path: str, size: int, mtime_ns: int, projection: dict) -> None:
+        """Additively remember ONE already-extracted file projection. ``json.dumps`` WITHOUT
+        ``sort_keys`` -- a cache hit must reproduce the EXACT key order a fresh extraction would
+        (the ``desk_meta_cache.py`` byte-identity precedent), so a served response never differs
+        between a cold and a warm read (TC-2)."""
+        with self._lock, self._conn:
+            self._conn.execute(
+                f"INSERT OR REPLACE INTO {EVIDENCE_TABLE} (path, size, mtime_ns, meta_json) "
+                "VALUES (?,?,?,?)",
+                (path, size, mtime_ns, json.dumps(projection)),
+            )
+
+
+# --- per-file projection extraction (pure data extraction -- zero measurement) ----------------------
+
+
+def _file_projection(record: dict) -> dict:
+    """Extract ONE already-verified playbook record's own per-``(setup_id, side)`` signal/baseline
+    forward-shaped events plus per-``(setup_id, side, horizon)`` invalidation-breach counts -- pure
+    grouping of data ``compute_playbook`` already wrote; nothing here calls ``_measure_from`` or
+    any other rail function. A signal recorded before J-02's measurement pass existed (an honest,
+    older-format record) carries no ``forward`` block -- it is excluded from this record's own
+    projection (the same "predates measurement" absence ``PlaybookStore._registered`` already reads
+    back verbatim for the record-level fields), never fabricated, never a crash."""
+    signal_events: dict[str, list[dict]] = {}
+    breach_counts: dict[str, dict[str, dict[str, int]]] = {}
+    for signal in record["signals"]:
+        forward = signal.get("forward")
+        if forward is None:
+            continue
+        pool_key = f"{signal['setup_id']}:{signal['side']}"
+        signal_events.setdefault(pool_key, []).append(forward)
+        breached = signal.get("invalidation_breached") or {}
+        counts = breach_counts.setdefault(pool_key, {})
+        for horizon in _BREACH_HORIZONS:
+            if horizon not in breached:
+                continue
+            cell = counts.setdefault(horizon, {"breached": 0, "total": 0})
+            cell["total"] += 1
+            if breached[horizon]:
+                cell["breached"] += 1
+    return {
+        "playbook_input_signature": record["playbook_input_signature"],
+        "session_date": record["session_date"],
+        "recorded_at": record["recorded_at"],
+        "signal_events": signal_events,
+        "baseline_events": {
+            key: list(events) for key, events in record.get("baseline_anchors", {}).items()
+        },
+        "breach_counts": breach_counts,
+    }
+
+
+def _projections_by_signature(
+    store: PlaybookStore, cache: PlaybookEvidenceCache | None
+) -> list[dict]:
+    """Every recorded playbook file's own projection, oldest-path-first -- a cache hit skips the
+    file's own parse+checksum verification entirely; a cache miss reads it through
+    ``PlaybookStore.get`` (the store's own public, verified reader -- zero re-implementation of its
+    checksum/corruption handling) and remembers the freshly extracted projection for next time. A
+    file that fails verification (``PlaybookStore.get`` returns ``None``) is silently excluded from
+    the fold -- ``GET /research/desk/playbook``'s own ``integrity_errors`` already surfaces a
+    corrupted file explicitly; this evidence fold does not duplicate that disclosure, it simply
+    never crashes and never fabricates a projection for a file it could not verify."""
+    if not store.root.exists():
+        return []
+    projections: list[dict] = []
+    for path in sorted(store.root.glob("*.json")):
+        try:
+            stat = path.stat()
+        except OSError:
+            continue
+        key = str(path)
+        cached = cache.lookup(key, stat.st_size, stat.st_mtime_ns) if cache is not None else None
+        if cached is not None:
+            projections.append(cached)
+            continue
+        record = store.get(path.stem)
+        if record is None:
+            continue
+        projection = _file_projection(record)
+        if cache is not None:
+            cache.insert(key, stat.st_size, stat.st_mtime_ns, projection)
+        projections.append(projection)
+    return projections
+
+
+# --- the quartile fold (new evidence-only math -- see the module docstring) -------------------------
+
+
+def _quartile_stats(values: list[float]) -> tuple[float | None, float | None, float | None, float | None]:
+    """``(median, p25, p75, mean)`` over one pooled value list -- ``None`` across the board at
+    ``n == 0`` (``_avg_cell``'s own honest-absence convention, never a fabricated 0.0). At
+    ``n == 1`` every one of the four readings IS that single value (``statistics.quantiles``
+    refuses fewer than two points, and repeating the lone value is the only non-fabricating
+    reading of "this cell's own p25/p75/median/mean"). ``method="inclusive"`` (linear
+    interpolation between order statistics, the common convention) is the ONE deterministic
+    quantile method this module ever uses -- proven against TC-1's hand-computed fixture."""
+    if not values:
+        return None, None, None, None
+    if len(values) == 1:
+        v = values[0]
+        return v, v, v, v
+    p25, _p50, p75 = statistics.quantiles(values, n=4, method="inclusive")
+    return statistics.median(values), p25, p75, statistics.mean(values)
+
+
+def _signal_cell(values: list[float], n_truncated: int) -> dict:
+    median, p25, p75, mean = _quartile_stats(values)
+    return {
+        "n": len(values),
+        "n_truncated": n_truncated,
+        "median_pct": median,
+        "p25_pct": p25,
+        "p75_pct": p75,
+        "mean_pct": mean,
+    }
+
+
+def _baseline_cell(values: list[float]) -> dict:
+    median, p25, p75, mean = _quartile_stats(values)
+    return {
+        "n_baseline": len(values),
+        "median_pct": median,
+        "p25_pct": p25,
+        "p75_pct": p75,
+        "mean_pct": mean,
+    }
+
+
+def _fold_cells(default_projections: list[dict]) -> list[dict]:
+    """The FULL declared cross product of ``PLAYBOOK_SETUPS`` x sides x
+    ``PLAYBOOK_SIGNAL_MEASURES`` -- every cell served, never a sparse "whatever fired" set (see the
+    module docstring). ``_collect_measures`` (the rail's own pooling helper, imported verbatim) does
+    the ENTIRE truncation-exclusion/grouping-by-measure-key job; this function only pools the raw
+    per-file event lists across every default-signature file first, so a signal recorded in one
+    session-date's file and a signal recorded in another's pool into the SAME cell exactly as if
+    they had been measured in one walk."""
+    cells: list[dict] = []
+    for setup_id in PLAYBOOK_SETUPS:
+        for side in _SIDES:
+            pool_key = f"{setup_id}:{side}"
+            signal_events: list[dict] = []
+            baseline_events: list[dict] = []
+            for projection in default_projections:
+                signal_events.extend(projection["signal_events"].get(pool_key, []))
+                baseline_events.extend(projection["baseline_events"].get(pool_key, []))
+            signal_pools = _collect_measures(signal_events)
+            baseline_pools = _collect_measures(baseline_events)
+            for measure in PLAYBOOK_SIGNAL_MEASURES:
+                signal_values, n_truncated = signal_pools[measure]
+                baseline_values, _baseline_truncated = baseline_pools[measure]
+                signal_block = _signal_cell(signal_values, n_truncated)
+                cells.append(
+                    {
+                        "setup_id": setup_id,
+                        "side": side,
+                        "measure": measure,
+                        "signal": signal_block,
+                        "baseline": _baseline_cell(baseline_values),
+                        "below_min_n": signal_block["n"] < PLAYBOOK_MIN_N_DISCLOSURE,
+                    }
+                )
+    return cells
+
+
+def _fold_invalidation_breached(default_projections: list[dict]) -> list[dict]:
+    """The FULL declared cross product of setups x sides x breach horizons, each entry a plain sum
+    of the per-file breach counts already extracted by ``_file_projection`` -- no re-derivation of
+    "did price breach the level", that fact was already computed once, outside ``_measure_from``,
+    by ``desk_playbook._invalidation_breached`` at compute time."""
+    entries: list[dict] = []
+    for setup_id in PLAYBOOK_SETUPS:
+        for side in _SIDES:
+            pool_key = f"{setup_id}:{side}"
+            for horizon in _BREACH_HORIZONS:
+                breached = 0
+                total = 0
+                for projection in default_projections:
+                    counts = projection["breach_counts"].get(pool_key, {}).get(horizon)
+                    if counts is not None:
+                        breached += counts["breached"]
+                        total += counts["total"]
+                entries.append(
+                    {
+                        "setup_id": setup_id,
+                        "side": side,
+                        "horizon": horizon,
+                        "breached_count": breached,
+                        "total_count": total,
+                    }
+                )
+    return entries
+
+
+def _fold_other_signatures(other_projections: list[dict]) -> list[dict]:
+    """Every NON-default signature present, its own ``dates``/``created_span`` only -- listed,
+    never pooled (the hard anti-goal: "the evidence pools one signature"). Signatures sorted for a
+    deterministic served order; ``dates`` deduplicated and sorted (a signature can record at most
+    ONE file per date -- ``PlaybookStore``'s own 2-pin key refuses a duplicate -- so dedup here is
+    defensive, not load-bearing)."""
+    by_signature: dict[str, list[dict]] = {}
+    for projection in other_projections:
+        by_signature.setdefault(projection["playbook_input_signature"], []).append(projection)
+    result: list[dict] = []
+    for signature in sorted(by_signature):
+        entries = by_signature[signature]
+        dates = sorted({entry["session_date"] for entry in entries})
+        recorded_ats = sorted(entry["recorded_at"] for entry in entries)
+        result.append(
+            {
+                "signature": signature,
+                "dates": dates,
+                "created_span": {"from": recorded_ats[0], "to": recorded_ats[-1]},
+            }
+        )
+    return result
+
+
+def fold_evidence(
+    store: PlaybookStore,
+    bar_store,
+    members: list[str],
+    config_fingerprint: str,
+    *,
+    cache: PlaybookEvidenceCache | None = None,
+) -> dict:
+    """The whole ``GET /research/desk/playbook/evidence`` body -- a pure fold over every recorded
+    playbook file (via ``PlaybookStore``'s own verified reader, zero re-implementation), split by
+    whether each file's own ``playbook_input_signature`` matches the CURRENT default signature
+    (``compute_playbook_input_signature``, imported verbatim -- the EXACT function
... [diff_bound] apps/backend/app/research/desk_playbook_evidence.py: 39 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/scripts/assert_scoped_qa_backend.py b/apps/backend/scripts/assert_scoped_qa_backend.py
new file mode 100644
index 0000000..b61a070
--- /dev/null
+++ b/apps/backend/scripts/assert_scoped_qa_backend.py
@@ -0,0 +1,112 @@
+"""Prove — or refuse to claim — that the backend a browser lane is about to drive is the FIXTURE
+rig rather than the operator's real store.
+
+This is tapeology's ``STORE_SCOPE_ASSERT_CMD``: the framework's store-scope guard
+(``incredible_auto_dev/scripts/automation/store-scope/store-scope.sh``) runs it before ANY browser
+lane -- deterministic golden replay or LLM dispatch -- and refuses to run the lane at all when it
+exits non-zero.
+
+WHY (goal-playbook-iter-8 audit, finding B2): iteration 8 shipped
+``qa_playbook_iter7_fixture_scoped_backend.sh``, a launcher that stands up a fully scoped backend,
+and the same iteration's pipeline run then replayed J-07's "Run Backscan" click against whatever
+was listening on the QA port -- the operator's ambient backend. Three real S&P-100 playbook records
+and a back-scan ledger row landed in an append-only store the project's own immutable-data rail
+forbids ever pruning. The launcher was correct; nothing obliged anyone to use it. This script is the
+obligation.
+
+THE MARKER. ``UniverseStore.record`` stores the ``source_url`` a membership was fetched from, and
+every fixture seeder registers its snapshot as ``fixture-rig*`` (``seed_playbook_fixture_rig.py`` ->
+``fixture-rig``, the iter-7 extension -> ``fixture-rig-iter7``, iter-8 -> ``fixture-rig-iter8``,
+iter-8's replay rig -> ``fixture-rig-iter8-replay``), while the real store's latest snapshot carries
+the Wikipedia S&P-100 URL a real fetch produced. The served ``latest`` snapshot therefore says which
+store is behind the port, in the backend's own words, with no new endpoint and no new served field.
+
+FAIL CLOSED, ALWAYS. Anything the payload cannot prove -- no snapshot yet, an unreadable body, a
+connection error, a non-200 -- is "not scoped". The cost of a false negative is a QA lane that
+refuses to run and says why; the cost of a false positive is another un-prunable write into the
+operator's store.
+
+Usage (normally through the framework guard, which passes nothing and relies on the env):
+
+    .venv/bin/python scripts/assert_scoped_qa_backend.py [BASE_URL]
+
+    BASE_URL  default: $QA_BACKEND_BASE_URL, else http://localhost:${CHAIN_BACKEND_PORT:-8301}
+
+Exit: 0 = provably the fixture rig · 1 = not scoped / cannot prove (the lane must not run).
+"""
+
+from __future__ import annotations
+
+import json
+import os
+import sys
+import urllib.error
+import urllib.request
+
+DEFAULT_REQUIRED_PREFIX = "fixture-rig"
+_TIMEOUT_S = 10
+
+
+def scoped_verdict(payload, required_prefix: str = DEFAULT_REQUIRED_PREFIX) -> tuple[bool, str]:
+    """``(is_scoped, reason)`` for a ``GET /research/desk/universe`` body -- a PURE function, so the
+    decision rule is unit-testable without a live server (``tests/test_qa_scoped_backend_guard.py``).
+
+    Scoped iff the LATEST registered snapshot's ``source_url`` starts with ``required_prefix``. The
+    reason always names what was actually seen, so a refusal is diagnosable from one log line."""
+    if not isinstance(payload, dict):
+        return False, f"universe body is not an object ({type(payload).__name__}) -- cannot prove scoped"
+    latest = payload.get("latest")
+    if latest is None:
+        snapshots = payload.get("snapshots")
+        if isinstance(snapshots, list) and not snapshots:
+            return False, "no universe snapshot is registered on this backend -- cannot prove scoped"
+        return False, "universe body carries no 'latest' snapshot -- cannot prove scoped"
+    if not isinstance(latest, dict):
+        return False, f"universe 'latest' is not an object ({type(latest).__name__}) -- cannot prove scoped"
+    source_url = latest.get("source_url")
+    if not isinstance(source_url, str) or not source_url:
+        return False, "latest universe snapshot carries no source_url -- cannot prove scoped"
+    members = latest.get("member_count")
+    if source_url.startswith(required_prefix):
+        return True, (
+            f"latest universe snapshot source_url={source_url!r} (member_count={members}) -- "
+            f"this backend serves the fixture rig"
+        )
+    return False, (
+        f"latest universe snapshot source_url={source_url!r} (member_count={members}) -- this is NOT "
+        f"a {required_prefix!r} backend; a browser lane here would read and write the operator's real store"
+    )
+
+
+def _fetch_universe(base_url: str) -> tuple[object | None, str]:
+    url = base_url.rstrip("/") + "/research/desk/universe"
+    try:
+        with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as response:  # noqa: S310 (localhost QA probe)
+            if response.status != 200:
+                return None, f"GET {url} returned HTTP {response.status}"
+            return json.loads(response.read().decode("utf-8")), ""
+    except urllib.error.HTTPError as exc:
+        return None, f"GET {url} returned HTTP {exc.code}"
+    except Exception as exc:  # connection refused, timeout, bad JSON -- all fail closed
+        return None, f"GET {url} failed: {type(exc).__name__}: {exc}"
+
+
+def main(argv: list[str]) -> int:
+    base_url = (
+        argv[1] if len(argv) > 1
+        else os.environ.get("QA_BACKEND_BASE_URL")
+        or f"http://localhost:{os.environ.get('CHAIN_BACKEND_PORT', '8301')}"
+    )
+    required_prefix = os.environ.get("STORE_SCOPE_UNIVERSE_PREFIX", DEFAULT_REQUIRED_PREFIX)
+    payload, error = _fetch_universe(base_url)
+    if error:
+        print(f"[assert-scoped-qa-backend] NOT SCOPED ({base_url}): {error}", file=sys.stderr)
+        return 1
+    scoped, reason = scoped_verdict(payload, required_prefix)
+    stream = sys.stdout if scoped else sys.stderr
+    print(f"[assert-scoped-qa-backend] {'SCOPED' if scoped else 'NOT SCOPED'} ({base_url}): {reason}", file=stream)
+    return 0 if scoped else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(sys.argv))
diff --git a/apps/backend/scripts/seed_playbook_iter8_evidence_fixture.py b/apps/backend/scripts/seed_playbook_iter8_evidence_fixture.py
new file mode 100644
index 0000000..d93415e
--- /dev/null
+++ b/apps/backend/scripts/seed_playbook_iter8_evidence_fixture.py
@@ -0,0 +1,131 @@
+"""Extend the J-04/J-05/J-06/J-07 playbook browser-QA rig (``seed_playbook_iter7_backscan_
+fixture.py``) with a well-populated Playbook Evidence corpus, for J-08's own browser-QA pass
+(Era B2, goal-playbook-iter-8) -- TC-8 needs one cell with ``n >= 12`` legible beside a
+``below_min_n``-tagged one in a single screenshot.
+
+Reuses the iter-7 rig VERBATIM (calls its own ``main()`` -- never a second implementation of the
+DECOR/RTAAA/DTAAA/BSCAN fixtures or their compute) and adds:
+
+  * TWELVE new universe members, ``OHB01``..``OHB12`` -- each the SAME canonical
+    open_high_break-firing session ``seed_playbook_iter7_backscan_fixture.py``'s own ``BSCAN``
+    already uses (``_firing_session_bars``, imported verbatim), planted on a FRESH session date,
+    2026-06-25 -- deliberately NOT 2026-06-22 (see "why a fresh date" below). ``compute_playbook``
+    pools every member's signal for the SAME ``(setup_id, side)`` within one session-date walk, so
+    12 members firing the identical setup on one date clears the evidence fold's
+    ``(open_high_break, long, *)`` cells past the disclosure floor
+    (``PLAYBOOK_MIN_N_DISCLOSURE = 12``) exactly -- the floor met, not padded. The 1h/4h measures
+    for this SAME cell stay empty (the 6-bar OHB sessions truncate long before a 1h offset), so the
+    SAME (setup_id, side) group shows a well-populated row (5m/to_close/mdd_*) directly beside a
+    below_min_n one (1h/4h) -- exactly TC-8's own "one well populated cell and one below_min_n
+    cell legible in a single screenshot" shape, with zero extra fixture work. Every OTHER setup
+    (capitulation/range_trade/double_top/dbi/jbe/cup_handle) is below_min_n too, at n = 0 (no
+    member fires them on 2026-06-25) -- an honest absence, not a fabricated thinness.
+  * a NEW, sixteen-member universe snapshot (DECOR, RTAAA, DTAAA, BSCAN, OHB01..OHB12) --
+    registration is append-only, so this is a genuinely new record, becoming the LATEST snapshot
+    every route reads.
+  * ONE fresh playbook compute + record for 2026-06-25 under this NEW (16-member) signature.
+
+  **Why a fresh date (2026-06-25), never 2026-06-22.** The FIRST version of this script reused
+  2026-06-22 for the evidence compute too -- but that recomputes AND RECORDS a NEW version for the
+  SAME date the Backscan panel's own J-07 golden (``journey-scripts/J-07.json``) already asserts
+  "3 missing at the current signature" over ``[2026-06-22, 2026-06-24]``. Recording 2026-06-22 under
+  the (now current) 16-member signature would make it ``recorded_at_current_signature``, silently
+  dropping J-07's own count to "2 missing" and breaking an ALREADY-PASSING golden as a side effect
+  of an unrelated fixture addition -- exactly the kind of one-iteration-breaks-another regression
+  this era's own append-only/no-second-implementation discipline exists to prevent. 2026-06-25 is
+  outside the Backscan golden's own date range, so J-07's own three dates stay
+  ``missing_at_current_signature`` at the 16-member signature, UNCHANGED, while the evidence corpus
+  still gets a real, fresh, well-populated record to fold.
+
+Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports the store
+env vars first -- ALL FOUR playbook scoping vars, per the iter-6/iter-7 lesson):
+
+    TAPEOLOGY_BAR_DIR=... TAPEOLOGY_DESK_UNIVERSE_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
+    TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR=... TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR=... \\
+    .venv/bin/python scripts/seed_playbook_iter8_evidence_fixture.py ROOT
+"""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+_SCRIPTS_DIR = Path(__file__).resolve().parent
+sys.path.insert(0, str(_SCRIPTS_DIR))
+sys.path.insert(0, str(_SCRIPTS_DIR.parent))
+
+import seed_playbook_iter7_backscan_fixture as iter7_seed  # noqa: E402
+
+from app.config import Config  # noqa: E402
+from app.research.bars import BarStore  # noqa: E402
+from app.research.desk_playbook import PlaybookStore, resolve_desk_playbook_dir  # noqa: E402
+from app.research.desk_playbook_backscan import _assert_scoped  # noqa: E402
+from app.research.desk_playbook_compute import run_playbook_and_record  # noqa: E402
+from app.research.desk_universe import UniverseStore  # noqa: E402
+
+_EVIDENCE_SESSION_DATE = "2026-06-25"  # a FRESH date -- outside J-07's own [06-22, 06-24] range
+_OHB_MEMBERS = [f"OHB{i:02d}" for i in range(1, 13)]  # exactly 12 -- the disclosure floor, met
+
+
+def main(root: Path) -> int:
+    # Reuse the iter-7 rig VERBATIM first -- plants DECOR/RTAAA/DTAAA on 2026-06-22, BSCAN on
+    # 2026-06-23/24 (unrecorded), registers the four-member universe, and records ONE real
+    # playbook compute for 2026-06-22 at the three-member signature. Never a second implementation
+    # of any of that.
+    result = iter7_seed.main(root)
+    if result != 0:
+        return result
+
+    config = Config()
+    bar_dir = config.bar_dir_resolved()
+    universe_dir = config.desk_universe_dir_resolved()
+    playbook_dir = resolve_desk_playbook_dir(universe_dir)
+    _assert_scoped(root)
+
+    bar_store = BarStore(bar_dir)
+    universe_store = UniverseStore(universe_dir)
+    playbook_store = PlaybookStore(playbook_dir)
+
+    # 2026-06-22 + 3 calendar days == 2026-06-25 -- the SAME "day offset in seconds" arithmetic
+    # seed_playbook_iter7_backscan_fixture.py's own BSCAN dates use (both June, EDT, no DST
+    # transition -- plain day arithmetic against E_OPEN resolves the same epoch a fresh ET
+    # conversion would).
+    e_open = iter7_seed.seed_playbook_fixture_rig.E_OPEN + 3 * 86_400.0
+    for symbol in _OHB_MEMBERS:
+        bars = iter7_seed._baseline_bars(symbol, e_open) + iter7_seed._firing_session_bars(symbol, e_open)
+        bar_store.record(
+            symbol=symbol, timeframe="5m",
+            window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
+            feed="test", bars=bars,
+        )
+        print(f"[seed-playbook-iter8-evidence] planted {symbol}: {len(bars)} 5m bars", file=sys.stderr)
+
+    members = [
+        *iter7_seed.seed_playbook_fixture_rig.MEMBERS, iter7_seed.BSCAN_SYMBOL, *_OHB_MEMBERS,
+    ]
+    universe_store.record(
+        members=members, raw_members={m: m for m in members},
+        source_url="fixture-rig-iter8", min_members=1, max_members=len(members),
+    )
+    print(f"[seed-playbook-iter8-evidence] universe snapshot: {members}", file=sys.stderr)
+
+    record, reused = run_playbook_and_record(
+        universe_store, bar_store, config, playbook_store, _EVIDENCE_SESSION_DATE,
+    )
+    if record is None:
+        print("[seed-playbook-iter8-evidence] ERROR: compute produced no record", file=sys.stderr)
+        return 1
+    setup_counts: dict[str, int] = {}
+    for s in record["signals"]:
+        key = f"{s['setup_id']}:{s['side']}"
+        setup_counts[key] = setup_counts.get(key, 0) + 1
+    print(
+        f"[seed-playbook-iter8-evidence] recorded {record['id']} (reused={reused}) "
+        f"signature={record['playbook_input_signature']} signal_counts={setup_counts}",
+        file=sys.stderr,
+    )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
diff --git a/apps/backend/scripts/seed_playbook_iter8_replay_rig.py b/apps/backend/scripts/seed_playbook_iter8_replay_rig.py
new file mode 100644
index 0000000..7d9407f
--- /dev/null
+++ b/apps/backend/scripts/seed_playbook_iter8_replay_rig.py
@@ -0,0 +1,325 @@
+"""Extend the iter-8 evidence rig (``seed_playbook_iter8_evidence_fixture.py``) with everything the
+REMAINING required goldens need, so ALL EIGHT required-still-passing journeys replay green against
+ONE scoped backend.
+
+WHY THIS EXISTS (goal-playbook-iter-8 audit, finding B2 + recommended next step 2). Iteration 8
+made the replay lane's scoping a *launcher* and its own pipeline run ignored it, replaying against
+the operator's ambient backend and writing three real playbook records + a back-scan ledger row.
+Closing that hole with the framework's store-scope guard is only half the fix: with the guard armed,
+every browser lane runs on the fixture rig, and five goldens (J-01, J-02, J-03, J-04, J-10) were
+authored against scenarios only the operator's real store held. The audit's own words: *"Until then
+no single backend exists on which all eight required journeys pass."* This layer builds that
+backend.
+
+What it adds on top of the iter-8 evidence rig (which itself reuses iter-7 -> iter-6 verbatim):
+
+  * ``CALDR`` -- a member holding ONLY a daily (``1d``) series: one bar per WEEKDAY from
+    2024-01-02 through 2026-08-14. ``desk_sessions`` derives "is this date a trading session"
+    entirely from recorded daily bars over the first five members that hold them, and the rig had
+    none at all -- so ``is_known_non_session`` could never answer True and the refusal J-01
+    (2026-06-13, a Saturday) and J-03 (2024-01-06, a Saturday) assert was structurally unreachable.
+    With this calendar both dates fall INSIDE the anchor's recorded span and outside its session
+    set, which is exactly what ``non_session_refusal`` needs to say its one sentence. Weekends only:
+    the rig models no holiday table (neither does the product -- see that module's opening
+    paragraph), and no journey asserts one.
+
+  * ``OLBRK`` / ``JBEXP`` / ``DBIMP`` -- the canonical open_low_break, jump-base-explosion and
+    drop-base-implosion sessions, bar-for-bar from the committed detector goldens
+    (``tests/test_desk_playbook_detect.py``), planted on 2026-08-07 with the rig's own ten flat
+    baseline sessions. J-02 already asserts "Open-Low Break" on 2026-08-07 (its golden needs no
+    edit); J-04's date moves from 2026-06-22 to this one, because 2026-06-22 cannot carry them: a
+    record for that date at the CURRENT signature would flip J-07's own
+    "3 missing at the current signature" assertion to 2 and break an already-passing golden.
+
+  * every ``AAPL`` bar series COPIED VERBATIM from the operator's real store (read-only: the source
+    files are opened for reading and never written, moved, or re-tagged). J-10 -- the kept-product
+    sentinel -- loads ``/structure?symbol=AAPL&asof=2026-06-22...`` and asserts a real computed
+    price. Levels are a pure function of the bars, so byte-identical bars reproduce the same
+    numbers; substituting synthetic bars would have quietly turned the sentinel into a test of the
+    fixture instead of a test of the kept product. Skipped with a loud note when the real store is
+    absent (a fresh clone) -- the rest of the rig still seeds.
+
+  * ONE new universe snapshot naming all nineteen members, then TWO fresh computes:
+    2026-06-25 (the evidence corpus -- re-keyed, because the three new 5m members change
+    ``playbook_input_signature`` and the evidence fold pools the DEFAULT signature only) and
+    2026-08-07 (the new detector showcase). Both are append-only new versions beside the records the
+    earlier layers wrote; nothing is rewritten (T-4).
+
+  What it deliberately does NOT touch: 2026-06-22's own record (J-04/J-05/J-06 read it as
+  ``newest_for_date``) and the 2026-06-22..24 back-scan window J-07 walks. Every addition lands on
+  dates outside that window, for exactly the reason the iter-8 evidence seeder moved its own corpus
+  to 2026-06-25.
+
+Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports the store
+env vars first):
+
+    TAPEOLOGY_BAR_DIR=... TAPEOLOGY_DESK_UNIVERSE_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
+    TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR=... TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR=... \\
+    TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB=... .venv/bin/python scripts/seed_playbook_iter8_replay_rig.py ROOT
+"""
+
+from __future__ import annotations
+
+import shutil
+import sys
+from datetime import date, timedelta
+from pathlib import Path
+
+_SCRIPTS_DIR = Path(__file__).resolve().parent
+sys.path.insert(0, str(_SCRIPTS_DIR))
+sys.path.insert(0, str(_SCRIPTS_DIR.parent))
+
+import seed_playbook_iter8_evidence_fixture as iter8_seed  # noqa: E402
+
+from app.config import Config  # noqa: E402
+from app.providers.adapters.base import RawBar  # noqa: E402
+from app.research.bars import BarStore  # noqa: E402
+from app.research.desk_playbook import PlaybookStore, resolve_desk_playbook_dir  # noqa: E402
+from app.research.desk_playbook_backscan import _assert_scoped  # noqa: E402
+from app.research.desk_playbook_compute import run_playbook_and_record  # noqa: E402
+from app.research.desk_universe import UniverseStore  # noqa: E402
+
+# The detector showcase date: a Friday, OUTSIDE J-07's [2026-06-22, 2026-06-24] back-scan window and
+# outside the evidence date (2026-06-25), and already the date J-02's stored golden types in.
+DETECTOR_SESSION_DATE = "2026-08-07"
+_DETECTOR_E_OPEN = 1786109400.0  # 2026-08-07T13:30:00Z == 09:30 ET (verified by direct conversion)
+
+# The session-evidence calendar. Starts before J-03's asserted 2024-01-06 and ends after every
+# fixture session date, so every date any golden types falls INSIDE the anchor's recorded span --
+# the bound `is_known_non_session` requires before it will call anything a non-session.
+CALENDAR_SYMBOL = "CALDR"
+CALENDAR_FROM = "2024-01-02"
+CALENDAR_THROUGH = "2026-08-14"
+_CALENDAR_BAR_SECONDS = 48_600.0  # 13:30:00Z within the day -- same UTC date as the session
+
+# Kept-product symbols copied verbatim from the real store for J-10's /structure step.
+KEPT_SYMBOLS = ("AAPL",)
+
+_BASELINE_DAYS = 10
+
+
+def _bar(symbol: str, epoch: float, o: float, h: float, low: float, c: float, v: int,
+         timeframe: str = "5m") -> RawBar:
+    return RawBar(symbol, timeframe, epoch, float(o), float(h), float(low), float(c), int(v))
+
+
+def _baseline_bars(symbol: str, day_open: float, slots: int) -> list[RawBar]:
+    """The rig's own ten-flat-sessions baseline recipe (MBR = 1.0, slot volume median 1000),
+    parameterized by BOTH the session open and the slot count -- the two existing copies each fix
+    one of them (``seed_playbook_fixture_rig._baseline_bars`` fixes the open,
+    ``seed_playbook_iter7_backscan_fixture._baseline_bars`` fixes the slot count at 6) and the
+    twelve-slot continuation fixtures need both to vary. Same numbers, no third recipe."""
+    bars: list[RawBar] = []
+    for day in range(_BASELINE_DAYS):
+        prior_open = day_open - (day + 1) * 86_400.0
+        for slot in range(slots):
+            bars.append(_bar(symbol, prior_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
+    return bars
+
+
+def _open_low_break_bars(symbol: str, day_open: float) -> list[RawBar]:
+    """``tests/test_desk_playbook_detect.py::test_open_low_break_mirrors_the_high_side``'s own
+    fixture, bar for bar: a narrow opening range and a slot-3 trigger that breaks only the LOW side
+    (fires exactly one ``open_low_break`` short)."""
+    rows = [
+        (100.5, 100.9, 100.1, 100.4, 500),
+        (100.4, 100.9, 100.1, 100.4, 500),
+        (100.4, 100.9, 100.1, 100.4, 500),
+        (100.2, 100.3, 99.5, 99.8, 1000),   # trigger: breaks the 100.1 opening-range low
+        (99.8, 99.9, 99.6, 99.7, 800),
+        (99.7, 99.8, 99.5, 99.6, 800),
+    ]
+    return [_bar(symbol, day_open + i * 300.0, *row) for i, row in enumerate(rows)]
+
+
+def _jbe_bars(symbol: str, day_open: float) -> list[RawBar]:
+    """``_canonical_jbe_bars`` verbatim: a high-volume lookback, a three-bar tight base, and a
+    trigger breaking UP through the base high."""
+    rows = [
+        (98.4, 98.5, 98.0, 98.3, 1200),
+        (98.3, 98.4, 98.1, 98.3, 1200),
+        (98.3, 98.4, 98.05, 98.3, 1200),
+        (98.3, 98.45, 98.2, 98.3, 1200),
+        (98.3, 98.4, 98.15, 98.3, 1200),
+        (98.3, 98.5, 98.3, 98.4, 3000),     # lookback volume surge
+        (103.5, 103.8, 103.2, 103.6, 400),  # base bar 1
+        (103.6, 104.0, 103.3, 103.7, 500),  # base bar 2
+        (103.7, 103.9, 103.4, 103.8, 450),  # base bar 3
+        (103.9, 104.8, 103.8, 104.5, 1500), # trigger: breaks U=104.0
+        (104.5, 104.7, 104.3, 104.6, 900),
+        (104.6, 104.8, 104.4, 104.7, 900),
+    ]
+    return [_bar(symbol, day_open + i * 300.0, *row) for i, row in enumerate(rows)]
+
+
+def _dbi_bars(symbol: str, day_open: float) -> list[RawBar]:
+    """``_canonical_dbi_bars`` verbatim: the exact mirror of the JBE fixture."""
+    rows = [
+        (109.6, 110.0, 109.5, 109.7, 1200),
+        (109.7, 109.9, 109.6, 109.7, 1200),
+        (109.7, 109.95, 109.6, 109.7, 1200),
+        (109.7, 109.8, 109.55, 109.7, 1200),
+        (109.7, 109.85, 109.6, 109.7, 1200),
+        (109.6, 109.7, 109.5, 109.6, 3000),  # lookback volume surge
+        (104.5, 104.8, 104.2, 104.4, 400),   # base bar 1
+        (104.4, 104.7, 104.0, 104.3, 500),   # base bar 2
+        (104.3, 104.6, 104.1, 104.2, 450),   # base bar 3
+        (104.1, 104.2, 103.2, 103.5, 1500),  # trigger: breaks L=104.0
+        (103.5, 103.7, 103.3, 103.4, 900),
+        (103.4, 103.6, 103.2, 103.3, 900),
+    ]
+    return [_bar(symbol, day_open + i * 300.0, *row) for i, row in enumerate(rows)]
+
+
+DETECTOR_MEMBERS = {
+    "OLBRK": (_open_low_break_bars, 6),
+    "JBEXP": (_jbe_bars, 12),
+    "DBIMP": (_dbi_bars, 12),
+}
+
+
+def _calendar_bars(symbol: str) -> list[RawBar]:
+    """One daily bar per WEEKDAY across the calendar span -- the rig's session evidence.
+
+    Flat, unremarkable values: nothing reads these bars for price, only for the FACT that a session
+    was recorded on that date (``desk_sessions`` derives its whole answer from a daily bar's
+    existence). Weekends are absent, which is what makes 2024-01-06 and 2026-06-13 provable
+    non-sessions rather than merely unrecorded ones."""
+    bars: list[RawBar] = []
+    day = date.fromisoformat(CALENDAR_FROM)
+    last = date.fromisoformat(CALENDAR_THROUGH)
+    while day <= last:
+        if day.weekday() < 5:
+            epoch = (
+                (day - date(1970, 1, 1)).days * 86_400.0 + _CALENDAR_BAR_SECONDS
+            )
+            bars.append(_bar(symbol, epoch, 100.0, 101.0, 99.0, 100.0, 1_000_000, timeframe="1d"))
+        day += timedelta(days=1)
+    return bars
+
+
+def _copy_kept_symbol_series(scoped_bar_dir: Path, real_bar_dir: Path) -> int:
+    """Copy every recorded series for ``KEPT_SYMBOLS`` from the operator's real bar store into the
+    scoped one, file for file.
+
+    READ-ONLY on the source, by construction: the real directory is listed and its JSON files are
+    opened for reading; nothing is written, renamed, or deleted there (the immutable-data rail
+    applies to a QA rig exactly as it applies to the product). The destination is the scoped root,
+    which ``_assert_scoped`` has already proven is not a ``.data`` store.
+
+    Byte-identical copies matter: J-10 asserts a REAL computed price from the kept ``/structure``
+    surface, and levels/zones are a pure function of the bars. Synthetic substitutes would turn the
+    kept-product sentinel into a test of the fixture."""
+    if not real_bar_dir.exists():
+        print(
+            f"[seed-playbook-iter8-replay] NOTE: no real bar store at {real_bar_dir} -- kept-symbol "
+            f"series ({', '.join(KEPT_SYMBOLS)}) NOT copied; J-10's /structure step cannot pass on "
+            "this rig.",
+            file=sys.stderr,
+        )
+        return 0
+    if real_bar_dir.resolve() == scoped_bar_dir.resolve():
+        raise SystemExit("[seed-playbook-iter8-replay] REFUSING: scoped bar dir IS the real bar dir")
+    records, _errors = BarStore(real_bar_dir).list(include_bars=False)
+    copied = 0
+    for record in records:
+        if record["symbol"] not in KEPT_SYMBOLS:
+            continue
+        source = real_bar_dir / f"{record['id']}.json"
+        if not source.exists():
+            continue
+        shutil.copy2(source, scoped_bar_dir / source.name)
+        copied += 1
+    print(
+        f"[seed-playbook-iter8-replay] copied {copied} kept-symbol series verbatim from the real "
+        f"store (read-only): {', '.join(KEPT_SYMBOLS)}",
+        file=sys.stderr,
+    )
+    return copied
+
+
+def main(root: Path) -> int:
+    # Reuse the iter-8 evidence rig VERBATIM first (which reuses iter-7, which reuses iter-6):
+    # DECOR/RTAAA/DTAAA on 2026-06-22, BSCAN on 2026-06-23/24 (unrecorded), OHB01..OHB12 on
+    # 2026-06-25, and the sixteen-member universe + evidence compute.
+    result = iter8_seed.main(root)
+    if result != 0:
+        return result
+
+    config = Config()
+    bar_dir = config.bar_dir_resolved()
+    universe_dir = config.desk_universe_dir_resolved()
+    playbook_dir = resolve_desk_playbook_dir(universe_dir)
+    _assert_scoped(root)
+
+    bar_store = BarStore(bar_dir)
+    universe_store = UniverseStore(universe_dir)
+    playbook_store = PlaybookStore(playbook_dir)
+
+    # 1. The session calendar (J-01 / J-03's refusals).
+    calendar = _calendar_bars(CALENDAR_SYMBOL)
+    bar_store.record(
+        symbol=CALENDAR_SYMBOL, timeframe="1d",
+        window_start_utc=f"{CALENDAR_FROM}T00:00:00Z", window_end_utc=f"{CALENDAR_THROUGH}T23:59:59Z",
+        feed="test", bars=calendar,
+    )
+    print(
+        f"[seed-playbook-iter8-replay] planted {CALENDAR_SYMBOL}: {len(calendar)} daily bars "
+        f"({CALENDAR_FROM}..{CALENDAR_THROUGH}, weekdays only)",
+        file=sys.stderr,
+    )
+
+    # 2. The detector showcase session (J-02's Open-Low Break, J-04's JBE + DBI).
+    for symbol, (builder, slots) in DETECTOR_MEMBERS.items():
+        bars = _baseline_bars(symbol, _DETECTOR_E_OPEN, slots) + builder(symbol, _DETECTOR_E_OPEN)
+        bar_store.record(
+            symbol=symbol, timeframe="5m",
+            window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
+            feed="test", bars=bars,
+        )
+        print(f"[seed-playbook-iter8-replay] planted {symbol}: {len(bars)} 5m bars", file=sys.stderr)
+
+    # 3. Kept-product bars for J-10's /structure step (verbatim copies, real store read-only).
+    _copy_kept_symbol_series(Path(bar_dir), Path(config.bar_dir))
+
+    # 4. ONE new snapshot naming every member, then the two computes it re-keys.
+    members = [
+        *iter8_seed.iter7_seed.seed_playbook_fixture_rig.MEMBERS,
+        iter8_seed.iter7_seed.BSCAN_SYMBOL,
+        *iter8_seed._OHB_MEMBERS,
+        CALENDAR_SYMBOL,
+        *DETECTOR_MEMBERS,
+    ]
+    universe_store.record(
+        members=members, raw_members={m: m for m in members},
+        source_url="fixture-rig-iter8-replay", min_members=1, max_members=len(members),
+    )
+    print(f"[seed-playbook-iter8-replay] universe snapshot: {members}", file=sys.stderr)
+
+    # The evidence corpus must be re-recorded at the NEW signature: three new members hold 5m
+    # series, so `compute_playbook_input_signature` moves, and the evidence fold pools the DEFAULT
+    # signature only. Append-only -- the sixteen-member version stays on disk untouched beside it.
+    for session_date in (iter8_seed._EVIDENCE_SESSION_DATE, DETECTOR_SESSION_DATE):
+        record, reused = run_playbook_and_record(
+            universe_store, bar_store, config, playbook_store, session_date,
+        )
+        if record is None:
+            print(
+                f"[seed-playbook-iter8-replay] ERROR: compute produced no record for {session_date}",
+                file=sys.stderr,
+            )
+            return 1
+        counts: dict[str, int] = {}
+        for signal in record["signals"]:
+            key = f"{signal['setup_id']}:{signal['side']}"
+            counts[key] = counts.get(key, 0) + 1
+        print(
+            f"[seed-playbook-iter8-replay] recorded {record['id']} for {session_date} "
+            f"(reused={reused}) signature={record['playbook_input_signature']} signal_counts={counts}",
+            file=sys.stderr,
+        )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
diff --git a/apps/backend/scripts/start_scoped_qa_backend.sh b/apps/backend/scripts/start_scoped_qa_backend.sh
new file mode 100755
index 0000000..ecd5060
--- /dev/null
+++ b/apps/backend/scripts/start_scoped_qa_backend.sh
@@ -0,0 +1,85 @@
+#!/usr/bin/env bash
+# start_scoped_qa_backend.sh — put the FIXTURE-SCOPED backend on the QA port, replacing whatever
+# is listening there.
+#
+# This is tapeology's STORE_SCOPE_PREPARE_CMD: the framework's store-scope guard
+# (incredible_auto_dev/scripts/automation/store-scope/store-scope.sh) runs it ONCE when
+# assert_scoped_qa_backend.py says the backend a browser lane is about to drive is not the rig,
+# then re-runs the assert. Nothing here decides anything — the assert does; this script only tries
+# to make the assert true.
+#
+# WHY IT MAY KILL THE OPERATOR'S OWN BACKEND: on this host the QA port (8301) is also where the
+# operator runs a backend bound to the REAL apps/backend/.data/ store. A browser lane driving that
+# backend is exactly the goal-playbook-iter-8 defect (three real playbook records + an un-prunable
+# back-scan ledger row written by a replayed "Run Backscan" click). Replacing the listener for the
+# duration of a QA pass is the lesser cost, and it is disclosed: the replaced process's command line
+# is written to <log-dir>/replaced-listener-<port>.txt so the operator (or the next agent) can
+# restart it verbatim.
+#
+# Usage: start_scoped_qa_backend.sh [root_dir] [port]
+#   root_dir  fresh scoped root (default: ${TMPDIR:-/tmp}/tapeology-store-scope-qa/rig).
+#             RECREATED on every call: the playbook/bar/universe stores are append-only, so a
+#             re-seed into a used root would collide instead of producing the rig's own composition.
+#             (Which is why the replaced-listener record is written BESIDE the root, not inside it.)
+#   port      QA backend port (default: $CHAIN_BACKEND_PORT, else 8301)
+# Exit: 0 = a scoped backend answers /health on the port · 1 = it does not
+set -uo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
+
+ROOT="${1:-${TMPDIR:-/tmp}/tapeology-store-scope-qa/rig}"
+PORT="${2:-${CHAIN_BACKEND_PORT:-8301}}"
+LOG="${STORE_SCOPE_QA_BACKEND_LOG:-${TMPDIR:-/tmp}/tapeology-store-scope-qa/backend-${PORT}.log}"
+
+# Refuse to wipe anything that is not obviously a throwaway QA root — a bug here would delete a
+# real store, which is the opposite of this script's whole purpose.
+case "$ROOT" in
+  *"/.data"*|"$BACKEND_DIR"|"$BACKEND_DIR/"*)
+    echo "[scoped-qa-backend] REFUSING: root '$ROOT' is inside the backend tree / a .data store." >&2
+    exit 1 ;;
+  ""|"/"|"$HOME") echo "[scoped-qa-backend] REFUSING: root '$ROOT' is not a scoped path." >&2; exit 1 ;;
+esac
+
+mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
+
+# 1. Free the port, disclosing what was there. The record lives BESIDE the root, never inside it:
+# step 2 wipes the root (append-only stores cannot be re-seeded in place), which would delete the
+# very disclosure that lets the operator restart what this script replaced.
+REPLACED_RECORD="$(dirname "$LOG")/replaced-listener-${PORT}.txt"
+_pids="$(lsof -ti "tcp:$PORT" -sTCP:LISTEN 2>/dev/null || true)"
+if [[ -n "$_pids" ]]; then
+  {
+    echo "# Replaced by start_scoped_qa_backend.sh at $(date -u +%Y-%m-%dT%H:%M:%SZ) on port $PORT"
+    for p in $_pids; do
+      echo "pid=$p cmd=$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null || echo '?')"
+    done
+  } > "$REPLACED_RECORD" 2>/dev/null || true
+  echo "[scoped-qa-backend] Replacing the listener on :$PORT (pids: $(echo "$_pids" | tr '\n' ' ')) — its command line is recorded in $REPLACED_RECORD so it can be restarted verbatim." >&2
+  # shellcheck disable=SC2086
+  kill $_pids 2>/dev/null || true
+  for _ in $(seq 1 20); do
+    sleep 0.5
+    lsof -ti "tcp:$PORT" -sTCP:LISTEN >/dev/null 2>&1 || break
+  done
+  # shellcheck disable=SC2086
+  lsof -ti "tcp:$PORT" -sTCP:LISTEN >/dev/null 2>&1 && kill -9 $_pids 2>/dev/null || true
+fi
+
+# 2. Fresh root (append-only stores cannot be re-seeded in place), then the ONE mandatory launcher.
+rm -rf "$ROOT" 2>/dev/null || true
+mkdir -p "$ROOT" 2>/dev/null || true
+echo "[scoped-qa-backend] Seeding + starting the fixture rig at root=$ROOT port=$PORT (log: $LOG)" >&2
+nohup bash "$SCRIPT_DIR/qa_playbook_iter7_fixture_scoped_backend.sh" "$ROOT" "$PORT" > "$LOG" 2>&1 &
+
+# 3. Wait for health. The seed walks ~16 fixture members plus two playbook computes before uvicorn
+# binds, so the budget is generous; a shorter one would report a working rig as a failure.
+for _ in $(seq 1 240); do
+  sleep 1
+  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://localhost:$PORT/health" 2>/dev/null || echo 000)"
+  [[ "$code" =~ ^[23] ]] && { echo "[scoped-qa-backend] Scoped backend healthy on :$PORT (root=$ROOT)."; exit 0; }
+done
+
+echo "[scoped-qa-backend] Scoped backend did NOT become healthy on :$PORT within the budget — see $LOG" >&2
+tail -n 25 "$LOG" >&2 2>/dev/null || true
+exit 1
diff --git a/apps/backend/tests/test_desk_playbook_evidence.py b/apps/backend/tests/test_desk_playbook_evidence.py
new file mode 100644
index 0000000..92eeb8e
--- /dev/null
+++ b/apps/backend/tests/test_desk_playbook_evidence.py
@@ -0,0 +1,514 @@
+"""``desk_playbook_evidence.py`` (Era B2, J-08) -- the pooled evidence fold, the projection cache's
+cold/warm/deleted byte-identity, min-n tagging, truncation-exclusion, single-signature pooling,
+and the wired ``GET /research/desk/playbook/evidence`` route. Test-first contract: TC-1 through
+TC-7 (+ TC-15's suite-floor lives in the full-suite run, not here) in
+``docs/phases/goal-playbook-iter-8.md``.
+
+Builds its own hand-crafted ``PlaybookStore`` records directly through the store's public
+``record`` writer (never through a real ``compute_playbook``/detector walk -- that path is already
+covered end to end by ``test_desk_playbook.py``/``test_desk_playbook_detect.py``) so every pooled
+value in every assertion below is a number this file's own hand computation can reproduce, not one
+a detector happened to produce. Every per-signal ``forward`` leaf is built through the REAL
+``desk_forward._measure_from`` over small synthetic bar lists (the ``test_desk_playbook.py``
+``test_measure_signal_and_measure_from_produce_byte_identical_leaves`` precedent) -- never a
+hand-typed dict shape that could silently drift from what the rail actually produces."""
+
+from __future__ import annotations
+
+import json
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app
+from app.providers.adapters.base import RawBar
+from app.research.bars import BarStore
+from app.research.desk_forward import DESK_FORWARD_MEASURE_KEYS, _measure_from
+from app.research.desk_playbook import PLAYBOOK_MIN_N_DISCLOSURE, PLAYBOOK_SETUPS, PlaybookStore
+from app.research.desk_playbook_evidence import (
+    EVIDENCE_REGISTER,
+    PlaybookEvidenceCache,
+    fold_evidence,
+    inspect_signature,
+)
+from app.research.desk_routes import get_playbook_evidence_cache, get_playbook_store
+from app.research.desk_universe import UniverseStore
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+from test_copy_discipline import find_violations
+
+E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET
+
+
+def _bar(symbol: str, epoch: float, close: float) -> RawBar:
+    """A flat 5m bar (open == high == low == close) -- makes every drawdown/exit-price computation
+    trivial by construction, so only the ``return_pct`` this file actually asserts on varies."""
+    return RawBar(symbol, "5m", epoch, close, close, close, close, 1000)
+
+
+def _forward(entry: float, at_1h: float, *, side: str = "long", n_bars: int = 15) -> dict:
+    """A REAL ``_measure_from`` leaf: ``n_bars`` flat 5m bars, entry at bar 0, the 1h horizon
+    (offset 12 bars on a 5m series) closing at ``at_1h`` -- so ``horizons["1h"]["return_pct"]`` is
+    EXACTLY ``sign * (at_1h - entry) / entry * 100.0``, a number this file's own assertions
+    hand-compute independently rather than trusting."""
+    sign = 1.0 if side == "long" else -1.0
+    closes = [entry] * n_bars
+    if n_bars > 12:
+        closes[12] = at_1h
+    bars = [_bar("SYN", E_OPEN + i * 300.0, c) for i, c in enumerate(closes)]
+    return _measure_from(bars, 0, entry, "level", 5, sign)
+
+
+def _truncated_forward(entry: float, exit_price: float, *, side: str = "long") -> dict:
+    """A short (5-bar) session -- the 1h horizon (needs offset 12) is unreachable, so every
+    signal's ``horizons["1h"]`` measures AT the last bar with ``truncated: True``. Used for TC-4."""
+    return _forward(entry, exit_price, side=side, n_bars=5)
+
+
+def _signal(setup_id: str, side: str, forward: dict, *, breached: dict | None = None) -> dict:
+    return {
+        "symbol": "SYN",
+        "setup_id": setup_id,
+        "side": side,
+        "geometry": {"slots_to_break": 0},
+        "trigger_price": forward["entry_price"],
+        "invalidation_price": forward["entry_price"] - 1.0 if side == "long" else forward["entry_price"] + 1.0,
+        "entry": forward["entry_price"],
+        "entry_kind": forward["entry_kind"],
+        "disclosures": {},
+        "forward": forward,
+        "invalidation_breached": breached
+        or {"1m": False, "5m": False, "1h": False, "4h": False, "to_close": False, "first_breach_minutes": None},
+    }
+
+
+def _record(
+    store: PlaybookStore,
+    session_date: str,
+    signature: str,
+    signals: list[dict],
+    baseline_anchors: dict[str, list[dict]] | None = None,
+) -> dict:
+    return store.record(
+        session_date=session_date,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature=signature,
+        payload_version=2,
+        parameters={"fixture": True},
+        register="fixture register",
+        signals=signals,
+        absences=[],
+        diagnostics=[],
+        baseline_anchors=baseline_anchors or {},
+    )
+
+
+SIG_DEFAULT = "current-signature-abc123"
+SIG_OLDER = "older-signature-def456"
+
+
+@pytest.fixture
+def store(tmp_path) -> PlaybookStore:
+    return PlaybookStore(tmp_path / "playbook")
+
+
+@pytest.fixture
+def bar_store(tmp_path) -> BarStore:
+    return BarStore(tmp_path / "bars")
+
+
+def _members(universe_store: UniverseStore) -> list[str]:
+    records, _errors = universe_store.list()
+    return list(records[-1]["members"]) if records else []
+
+
+# --- TC-1: pooling math against a hand-computed fixture ---------------------------------------------
+
+
+def test_tc1_pooled_1h_cell_matches_the_hand_computed_aggregate(store, bar_store, monkeypatch):
+    """Three recorded records at the SAME (current) signature, each contributing exactly one
+    (jbe, long) signal plus a scatter of OTHER setups (dbi/capitulation/range_trade) that must
+    never leak into the jbe cell. jbe/long/1h return_pct values: 2.0, 4.0, 6.0 -- median 4.0, mean
+    4.0, p25 3.0, p75 5.0 (``statistics.quantiles(..., n=4, method="inclusive")`` over [2, 4, 6])."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [
+            _signal("jbe", "long", _forward(100.0, 102.0)),
+            _signal("dbi", "short", _forward(100.0, 99.0, side="short")),
+            _signal("capitulation", "long", _forward(100.0, 101.0)),
+        ],
+    )
+    _record(
+        store, "2026-06-23", SIG_DEFAULT,
+        [
+            _signal("jbe", "long", _forward(100.0, 104.0)),
+            _signal("range_trade", "long", _forward(100.0, 100.5)),
+        ],
+    )
+    _record(
+        store, "2026-06-24", SIG_DEFAULT,
+        [_signal("jbe", "long", _forward(100.0, 106.0))],
+    )
+
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    assert body["signature"] == SIG_DEFAULT
+
+    cell = next(
+        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    assert cell["signal"]["n"] == 3
+    assert cell["signal"]["n_truncated"] == 0
+    assert cell["signal"]["median_pct"] == pytest.approx(4.0)
+    assert cell["signal"]["mean_pct"] == pytest.approx(4.0)
+    assert cell["signal"]["p25_pct"] == pytest.approx(3.0)
+    assert cell["signal"]["p75_pct"] == pytest.approx(5.0)
+    assert cell["baseline"]["n_baseline"] == 0  # no baseline_anchors planted for this pool key
+    assert cell["below_min_n"] is True  # 3 < PLAYBOOK_MIN_N_DISCLOSURE (12)
+
+    # The scattered dbi/capitulation/range_trade signals never leak into the jbe cell.
+    dbi_cell = next(
+        c for c in body["cells"] if c["setup_id"] == "dbi" and c["side"] == "short" and c["measure"] == "1h"
+    )
+    assert dbi_cell["signal"]["n"] == 1
+
+
+# --- TC-2: cache cold vs warm byte-identity ----------------------------------------------------------
+
+
+def test_tc2_cache_cold_and_warm_reads_are_byte_identical(store, bar_store, tmp_path, monkeypatch):
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(store, "2026-06-22", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 102.0))])
+
+    cache = PlaybookEvidenceCache(str(tmp_path / "evidence_cache.db"))
+    cold = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache)
+    warm = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache)
+    assert json.dumps(cold, sort_keys=False) == json.dumps(warm, sort_keys=False)
+
+
+# --- TC-3: below_min_n tags while still serving populated numbers -----------------------------------
+
+
+def test_tc3_below_min_n_cell_still_serves_populated_numbers(store, bar_store, monkeypatch):
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [
+            _signal("dbi", "short", _forward(100.0, 98.0, side="short")),
+            _signal("dbi", "short", _forward(100.0, 97.0, side="short")),
+            _signal("dbi", "short", _forward(100.0, 99.0, side="short")),
+        ],
+    )
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    cell = next(
+        c for c in body["cells"] if c["setup_id"] == "dbi" and c["side"] == "short" and c["measure"] == "1h"
+    )
+    assert cell["signal"]["n"] == 3 < PLAYBOOK_MIN_N_DISCLOSURE
+    assert cell["below_min_n"] is True
+    assert cell["signal"]["median_pct"] is not None
+    assert cell["signal"]["p25_pct"] is not None
+    assert cell["signal"]["p75_pct"] is not None
+    assert cell["signal"]["mean_pct"] is not None
+
+
+def test_a_cell_with_zero_recorded_signals_is_served_as_n0_not_omitted(store, bar_store):
+    """Error case: every (setup_id, side, measure) combination is present in ``cells`` even with an
+    entirely empty store -- the full declared cross product, never a sparse/omitted set."""
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    assert len(body["cells"]) == len(PLAYBOOK_SETUPS) * 2 * len(DESK_FORWARD_MEASURE_KEYS)
+    cell = next(
+        c for c in body["cells"]
+        if c["setup_id"] == "open_high_break" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    assert cell["signal"] == {
+        "n": 0, "n_truncated": 0, "median_pct": None, "p25_pct": None, "p75_pct": None, "mean_pct": None,
+    }
+    assert cell["baseline"] == {
+        "n_baseline": 0, "median_pct": None, "p25_pct": None, "p75_pct": None, "mean_pct": None,
+    }
+    assert cell["below_min_n"] is True
+
+
+# --- TC-4: truncated values excluded from the pool, the exclusion counted ---------------------------
+
+
+def test_tc4_a_truncated_value_is_excluded_from_the_pool_but_counted(store, bar_store, monkeypatch):
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    untruncated = _forward(100.0, 102.0)
+    truncated = _truncated_forward(100.0, 999.0)  # exit_price 999 would wreck the mean if pooled
+    assert untruncated["horizons"]["1h"]["truncated"] is False
+    assert truncated["horizons"]["1h"]["truncated"] is True
+
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [_signal("jbe", "long", untruncated), _signal("jbe", "long", truncated)],
+    )
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    cell = next(
+        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    assert cell["signal"]["n"] == 1  # the truncated value never entered the pool
+    assert cell["signal"]["n_truncated"] == 1
+    assert cell["signal"]["mean_pct"] == pytest.approx(2.0)  # untruncated's own return only
+    assert cell["signal"]["median_pct"] == pytest.approx(2.0)
+
+
+# --- T1 (goal-playbook-iter-8 audit): the BASELINE half of the fold -----------------------------
+# The audit's finding T1: every fixture above records ``baseline_anchors={}``, so the pooled
+# baseline -- the "beside the pooled baseline" half of J-08's whole promise -- had no unit coverage
+# at all, and the ``f"{setup_id}:{side}"`` key agreement between ``desk_playbook.py``'s writer and
+# ``desk_playbook_evidence.py``'s reader was load-bearing yet unasserted. The auditor verified it by
+# hand; these two tests make it a guard, so a rename on either side fails here instead of silently
+# serving an empty baseline column beside populated signal numbers.
+
+
+def test_t1_pooled_baseline_anchors_fold_into_the_baseline_half_of_the_matching_cell(
+    store, bar_store, monkeypatch
+):
+    """Baseline anchors keyed EXACTLY as the writer keys them (``setup_id:side``) pool into that
+    cell's ``baseline`` block across files, with their own hand-computed quartiles -- and the
+    signal half of the same cell keeps its own, unmixed."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    # signals: 1h returns 2.0 and 4.0 -> median 3.0. baselines: 1.0, 3.0, 5.0 -> median 3.0,
+    # p25 2.0, p75 4.0, mean 3.0 (statistics.quantiles([1,3,5], n=4, method="inclusive")).
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [_signal("jbe", "long", _forward(100.0, 102.0))],
+        baseline_anchors={"jbe:long": [_forward(100.0, 101.0), _forward(100.0, 103.0)]},
+    )
+    _record(
+        store, "2026-06-23", SIG_DEFAULT,
+        [_signal("jbe", "long", _forward(100.0, 104.0))],
+        baseline_anchors={"jbe:long": [_forward(100.0, 105.0)]},
+    )
+
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    cell = next(
+        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    assert cell["signal"]["n"] == 2
+    assert cell["signal"]["median_pct"] == pytest.approx(3.0)
+    assert cell["baseline"]["n_baseline"] == 3  # pooled ACROSS both files, like the signal half
+    assert cell["baseline"]["median_pct"] == pytest.approx(3.0)
+    assert cell["baseline"]["p25_pct"] == pytest.approx(2.0)
+    assert cell["baseline"]["p75_pct"] == pytest.approx(4.0)
+    assert cell["baseline"]["mean_pct"] == pytest.approx(3.0)
+
+
+def test_t1_baseline_anchors_never_leak_across_setup_or_side(store, bar_store, monkeypatch):
+    """The pool key is (setup, side) on BOTH halves: a ``dbi:short`` anchor set never appears in
+    the ``jbe:long`` cell's baseline, and a cell whose key nothing planted serves an honest zero
+    rather than borrowing a neighbour's anchors."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [_signal("jbe", "long", _forward(100.0, 102.0)), _signal("dbi", "short", _forward(100.0, 98.0, side="short"))],
+        baseline_anchors={"dbi:short": [_forward(100.0, 99.0, side="short")]},
+    )
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    jbe = next(
+        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    dbi = next(
+        c for c in body["cells"] if c["setup_id"] == "dbi" and c["side"] == "short" and c["measure"] == "1h"
+    )
+    assert jbe["signal"]["n"] == 1 and jbe["baseline"]["n_baseline"] == 0
+    assert jbe["baseline"]["median_pct"] is None  # honest absence, never a fabricated 0.0
+    assert dbi["baseline"]["n_baseline"] == 1
+    assert dbi["baseline"]["median_pct"] == pytest.approx(1.0)  # short side: (100 - 99)/100 * 100
+
+
+def test_b1_a_cell_whose_baseline_pool_is_capped_serves_both_counts_and_discloses_why(
+    store, bar_store, monkeypatch
+):
+    """goal-playbook-iter-8 audit, finding B1: ``compute_playbook`` draws ONE baseline anchor per
+    signal only while that ``(setup_id, side)`` is within the rail's own
+    ``DESK_FORWARD_MAX_TOUCHES_PER_ROW`` pooling cap for the session, while EVERY signal (in-cap or
+    beyond) carries a ``forward`` block and enters the signal pool. On the operator's own real
+    corpus this bites hard -- ``(double_top, short)`` pools 90 signals against 32 baseline anchors
+    -- so the served register must not claim the baseline covers every signal. This fixture
+    reproduces the shape (5 signals, 2 anchors) and pins BOTH halves: the two counts are served
+    side by side, and ``EVIDENCE_REGISTER`` names the cap as the reason they can differ."""
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(
+        store, "2026-06-22", SIG_DEFAULT,
+        [_signal("double_top", "short", _forward(100.0, 99.0, side="short")) for _ in range(5)],
+        baseline_anchors={"double_top:short": [_forward(100.0, 99.5, side="short") for _ in range(2)]},
+    )
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    cell = next(
+        c for c in body["cells"]
+        if c["setup_id"] == "double_top" and c["side"] == "short" and c["measure"] == "1h"
+    )
+    assert cell["signal"]["n"] == 5
+    assert cell["baseline"]["n_baseline"] == 2  # the capped half, served as its own honest count
+    low = body["register"].lower()
+    assert "cap" in low and "n_baseline" in low, (
+        "EVIDENCE_REGISTER must disclose that the baseline column can cover fewer signals than the "
+        "signal column because of the per-setup-and-side pooling cap"
+    )
+    assert find_violations(body["register"]) == []
+
+
+# --- TC-5: two signatures -- only the default pools, the other is listed, never merged --------------
+
+
+def test_tc5_only_the_default_signature_pools_the_other_is_listed_not_merged(store, bar_store, monkeypatch):
+    monkeypatch.setattr(
+        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
+        lambda *_a, **_k: SIG_DEFAULT,
+    )
+    _record(store, "2026-06-22", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 102.0))])
+    _record(store, "2026-06-10", SIG_OLDER, [_signal("jbe", "long", _forward(100.0, 999.0))])
+    _record(store, "2026-06-11", SIG_OLDER, [_signal("jbe", "long", _forward(100.0, 999.0))])
+
+    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
+    cell = next(
+        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
+    )
+    assert cell["signal"]["n"] == 1  # the older signature's two signals never entered this pool
+    assert cell["signal"]["mean_pct"] == pytest.approx(2.0)
+
+    assert len(body["other_signatures"]) == 1
... [diff_bound] apps/backend/tests/test_desk_playbook_evidence.py: 120 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_qa_scoped_backend_guard.py b/apps/backend/tests/test_qa_scoped_backend_guard.py
new file mode 100644
index 0000000..12ce362
--- /dev/null
+++ b/apps/backend/tests/test_qa_scoped_backend_guard.py
@@ -0,0 +1,97 @@
+"""The QA store-scope assert: is the backend a browser lane is about to drive the FIXTURE rig, or
+the operator's real store?
+
+WHY THIS EXISTS (goal-playbook-iter-8 audit, finding B2): iteration 8 shipped a launcher that
+stands up a fixture-scoped backend -- and its own pipeline run then replayed a golden containing a
+"Run Backscan" click against the operator's AMBIENT backend, computing three real S&P-100 playbook
+records and appending a run-ledger row into an append-only store that can never be pruned. The
+launcher was never wrong; nothing was OBLIGED to use it. The framework's store-scope guard
+(``incredible_auto_dev/scripts/automation/store-scope/store-scope.sh``) now refuses to run any
+browser lane unless a project-owned assert command proves the backend under test is scoped --
+``scripts/assert_scoped_qa_backend.py`` is tapeology's implementation of that assert, and this file
+is its unit coverage.
+
+The classifier is deliberately a PURE function of the served ``GET /research/desk/universe`` body,
+so the decision rule is testable without a live server: the fixture rig registers its universe
+snapshots with a ``fixture-rig*`` ``source_url`` (``seed_playbook_fixture_rig.py`` and its two
+extensions), while the real store's latest snapshot carries the Wikipedia S&P-100 URL it was
+actually fetched from. Every unproven case fails CLOSED -- "cannot prove scoped" and "proved
+unscoped" both mean no browser lane may run, which is the only safe reading when the alternative is
+writing into the operator's store.
+"""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
+sys.path.insert(0, str(SCRIPTS_DIR))
+
+from assert_scoped_qa_backend import scoped_verdict  # noqa: E402
+
+_REAL_PAYLOAD = {
+    "snapshots": [{"id": "universe-2026-07-25-49b33fa31680", "source_url": "https://en.wikipedia.org/wiki/S%26P_100"}],
+    "latest": {
+        "id": "universe-2026-07-25-49b33fa31680",
+        "source_url": "https://en.wikipedia.org/wiki/S%26P_100",
+        "member_count": 101,
+        "members": ["AAPL", "ABBV", "ABT"],
+    },
+    "integrity_errors": [],
+}
+
+_FIXTURE_PAYLOAD = {
+    "snapshots": [{"id": "universe-2026-06-22-aaaa", "source_url": "fixture-rig"}],
+    "latest": {
+        "id": "universe-2026-06-22-bbbb",
+        "source_url": "fixture-rig-iter8",
+        "member_count": 16,
+        "members": ["DECOR", "RTAAA", "DTAAA", "BSCAN"],
+    },
+    "integrity_errors": [],
+}
+
+
+def test_fixture_rig_universe_is_scoped():
+    """The rig's own snapshots are registered with a fixture-rig source_url -- the one marker no
+    real fetch can produce (``UniverseStore.record`` stores the source it was fetched from)."""
+    scoped, reason = scoped_verdict(_FIXTURE_PAYLOAD)
+    assert scoped is True
+    assert "fixture-rig-iter8" in reason
+
+
+def test_real_sp100_universe_is_not_scoped():
+    """The exact body the operator's real backend serves -- the configuration iteration 8's replay
+    lane actually ran against."""
+    scoped, reason = scoped_verdict(_REAL_PAYLOAD)
+    assert scoped is False
+    assert "en.wikipedia.org" in reason
+
+
+def test_an_empty_universe_store_fails_closed():
+    """No snapshot at all proves nothing either way: a freshly created scoped root looks exactly
+    like a real backend whose universe was never registered. Unproven is refused, never allowed."""
+    scoped, reason = scoped_verdict({"snapshots": [], "latest": None, "integrity_errors": []})
+    assert scoped is False
+    assert "no universe snapshot" in reason
+
+
+def test_a_malformed_body_fails_closed():
+    """A body that is not the universe payload at all (a 404 JSON, an error object, a proxy page)
+    is refused rather than parsed optimistically."""
+    for payload in ({}, {"detail": "Not Found"}, {"latest": "nonsense"}, []):
+        scoped, reason = scoped_verdict(payload)
+        assert scoped is False, payload
+        assert reason
+
+
+def test_the_required_prefix_is_a_parameter_not_a_hardcoded_string():
+    """The marker is the rig's own convention, so a future rig can rename it in ONE place (the
+    store-scope.env the framework guard reads) instead of forking the classifier."""
+    scoped, _ = scoped_verdict(_FIXTURE_PAYLOAD, required_prefix="some-other-rig")
+    assert scoped is False
+    scoped, _ = scoped_verdict(
+        {"latest": {"source_url": "some-other-rig-v2", "member_count": 3}}, required_prefix="some-other-rig"
+    )
+    assert scoped is True
diff --git a/incredible_auto_dev/scripts/automation/store-scope/store-scope.sh b/incredible_auto_dev/scripts/automation/store-scope/store-scope.sh
new file mode 100755
index 0000000..93770b0
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/store-scope/store-scope.sh
@@ -0,0 +1,188 @@
+#!/usr/bin/env bash
+# store-scope.sh — make "the automated run never touched the operator's real
+# store" a MECHANISM instead of a claim.
+#
+# WHY: a project can ship a launcher that stands up a fixture-scoped backend for
+# browser/replay work, and the pipeline can still run its lanes against whatever
+# backend happens to be listening on the QA port. That is exactly what happened
+# in tapeology's goal-playbook-iter-8: the deterministic replay lane replayed a
+# golden containing a "Run Backscan" click against the operator's AMBIENT
+# backend, computed three real S&P-100 playbook records and appended a run-ledger
+# row into an append-only store that by the project's own rails can never be
+# pruned — while the iteration's own acceptance said that could no longer happen.
+# A launcher nothing is obliged to use is not a mechanism; a gate is.
+#
+# THE GATE, three verbs:
+#   require              — refuse to run any browser lane unless the project's
+#                          own assert command PROVES the backend under test is
+#                          the scoped one. One prepare attempt in between, when
+#                          the project declares a prepare command. rc 1 = the
+#                          caller must NOT dispatch a browser lane.
+#   snapshot <manifest>  — record every regular file under the project's
+#                          protected store paths (size + mtime), before the run.
+#   verify <manifest> [report.md]
+#                        — re-read those paths and hard-fail (rc 1) on ANY
+#                          delta: added, removed, or modified. Writes a
+#                          disclosure artifact either way, so a later reader
+#                          cites an executed check instead of prose.
+#
+# PROJECT-NEUTRAL BY CONSTRUCTION (the host-guard precedent): with no
+# project-extensions/store-scope/store-scope.env — or with STORE_SCOPE_ENABLED
+# not 1 — every verb is a no-op exiting 0 and prints nothing but a single
+# skip line to stderr. Nothing about any other project's behavior changes.
+#
+# Config (project-extensions/store-scope/store-scope.env):
+#   STORE_SCOPE_ENABLED=1
+#   STORE_SCOPE_LABEL="..."             human name used in logs/disclosure
+#   STORE_SCOPE_PROTECTED_PATHS="a b"   repo-relative dirs/files, space-separated
+#   STORE_SCOPE_ASSERT_CMD="..."        exits 0 iff the backend under test is scoped
+#   STORE_SCOPE_PREPARE_CMD="..."       optional; run once when the assert fails
+#
+# Both commands run with the project root as CWD and inherit the caller's
+# environment (CHAIN_BACKEND_PORT, FRONTEND_URL, ... are therefore visible).
+#
+# Usage: store-scope.sh require | snapshot <manifest> | verify <manifest> [report.md]
+# Exit:  0 = ok/no-op · 1 = refusal (require) or breach (verify) · 2 = bad usage
+set -uo pipefail
+
+ROOT="${STORE_SCOPE_ROOT:-$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd)}"
+[[ "$ROOT" == */incredible_auto_dev ]] && ROOT="${ROOT%/incredible_auto_dev}"
+ENV_FILE="$ROOT/project-extensions/store-scope/store-scope.env"
+
+_ss_log()  { echo "[store-scope] $*"; }
+_ss_warn() { echo "[store-scope] $*" >&2; }
+
+# shellcheck disable=SC1090
+[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" 2>/dev/null
+
+CMD="${1:-}"
+[[ -n "$CMD" ]] || { echo "usage: store-scope.sh require | snapshot <manifest> | verify <manifest> [report.md]" >&2; exit 2; }
+
+if [[ "${STORE_SCOPE_ENABLED:-0}" != "1" ]]; then
+  _ss_warn "no store-scope declared for $ROOT — nothing to guard ($CMD)."
+  exit 0
+fi
+
+LABEL="${STORE_SCOPE_LABEL:-store scope}"
+PATHS="${STORE_SCOPE_PROTECTED_PATHS:-}"
+
+# One manifest line per regular file: "<size> <mtime> <repo-relative path>",
+# sorted by path so two manifests diff deterministically. Deliberately stat-based
+# (never a content hash): the guard must stay cheap enough to run around EVERY
+# browser lane, and any write that a checksum would catch moves size or mtime
+# too. A missing protected path contributes nothing and is not an error — a
+# store directory that does not exist yet is a legitimate state, and its later
+# CREATION shows up as its first file appearing.
+_ss_manifest() {  # $1 = output file
+  local out="$1" p
+  : > "$out" || return 1
+  for p in $PATHS; do
+    [[ -e "$ROOT/$p" ]] || continue
+    ( cd "$ROOT" && find "$p" -type f -printf '%s\t%T@\t%p\n' 2>/dev/null ) >> "$out"
+  done
+  LC_ALL=C sort -t"$(printf '\t')" -k3 -o "$out" "$out" 2>/dev/null || true
+}
+
+case "$CMD" in
+
+  require)
+    if [[ -z "${STORE_SCOPE_ASSERT_CMD:-}" ]]; then
+      _ss_warn "$LABEL: store-scope is enabled but declares no STORE_SCOPE_ASSERT_CMD — the backend under test CANNOT be proven scoped; the snapshot/verify gate is the only remaining guard."
+      exit 0
+    fi
+    if ( cd "$ROOT" && eval "$STORE_SCOPE_ASSERT_CMD" ); then
+      _ss_log "$LABEL: backend under test is provably scoped — browser lanes may run."
+      exit 0
+    fi
+    if [[ -n "${STORE_SCOPE_PREPARE_CMD:-}" ]]; then
+      _ss_warn "$LABEL: backend under test is NOT scoped — running the project's prepare command once before deciding."
+      ( cd "$ROOT" && eval "$STORE_SCOPE_PREPARE_CMD" ) || _ss_warn "$LABEL: prepare command exited non-zero (continuing to the re-assert, which is the only thing that decides)."
+      if ( cd "$ROOT" && eval "$STORE_SCOPE_ASSERT_CMD" ); then
+        _ss_log "$LABEL: backend scoped by the prepare command — browser lanes may run."
+        exit 0
+      fi
+    fi
+    _ss_warn "$LABEL: REFUSING the browser lane — the backend under test is not scoped and could not be made scoped. Running it would let an automated pass write into the operator's real store (the exact defect this guard exists to prevent)."
+    exit 1
+    ;;
+
+  snapshot)
+    MANIFEST="${2:-}"
+    [[ -n "$MANIFEST" ]] || { echo "usage: store-scope.sh snapshot <manifest>" >&2; exit 2; }
+    mkdir -p "$(dirname "$MANIFEST")" 2>/dev/null || true
+    _ss_manifest "$MANIFEST" || { _ss_warn "$LABEL: could not write the baseline manifest at $MANIFEST — verify will report UNKNOWN rather than a false CLEAN."; exit 0; }
+    _ss_log "$LABEL: baseline captured — $(wc -l < "$MANIFEST" | tr -d ' ') file(s) under: ${PATHS}"
+    exit 0
+    ;;
+
+  verify)
+    MANIFEST="${2:-}"
+    REPORT="${3:-}"
+    [[ -n "$MANIFEST" ]] || { echo "usage: store-scope.sh verify <manifest> [report.md]" >&2; exit 2; }
+    NOW="$(mktemp "${TMPDIR:-/tmp}/store-scope-now.XXXXXX")"
+    _ss_manifest "$NOW"
+    VERDICT="CLEAN"; ADDED=""; REMOVED=""; MODIFIED=""
+    if [[ ! -s "$MANIFEST" && ! -s "$NOW" ]]; then
+      : # both empty: nothing protected exists yet — genuinely clean
+    fi
+    if [[ ! -f "$MANIFEST" ]]; then
+      VERDICT="UNKNOWN"
+      _ss_warn "$LABEL: no baseline manifest at $MANIFEST — this run cannot prove the store was untouched (absent beats a false CLEAN)."
+    else
+      # Path sets first (added/removed), then, for paths present in BOTH, a
+      # stat comparison (modified). One awk pass each, keyed on the tab-
+      # delimited path field so a path containing spaces cannot smear columns.
+      ADDED="$(LC_ALL=C comm -13 <(cut -f3- "$MANIFEST" | LC_ALL=C sort) <(cut -f3- "$NOW" | LC_ALL=C sort))"
+      REMOVED="$(LC_ALL=C comm -23 <(cut -f3- "$MANIFEST" | LC_ALL=C sort) <(cut -f3- "$NOW" | LC_ALL=C sort))"
+      MODIFIED="$(awk -F'\t' 'NR==FNR{a[$3]=$1"\t"$2; next} ($3 in a) && a[$3] != $1"\t"$2 {print $3}' \
+                    "$MANIFEST" "$NOW")"
+      [[ -n "${ADDED//[[:space:]]/}" || -n "${REMOVED//[[:space:]]/}" || -n "${MODIFIED//[[:space:]]/}" ]] && VERDICT="BREACH"
+    fi
+    if [[ -n "$REPORT" ]]; then
+      mkdir -p "$(dirname "$REPORT")" 2>/dev/null || true
+      {
+        echo "# Store-scope guard — $LABEL"
+        echo ""
+        echo "**Verdict:** $VERDICT"
+        echo ""
+        echo "- Protected paths: \`${PATHS}\`"
+        echo "- Baseline manifest: \`$MANIFEST\` ($( [[ -f "$MANIFEST" ]] && wc -l < "$MANIFEST" | tr -d ' ' || echo 0 ) file(s))"
+        echo "- Post-run scan: $(wc -l < "$NOW" | tr -d ' ') file(s)"
+        echo "- Checked: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
+        echo ""
+        if [[ "$VERDICT" == "CLEAN" ]]; then
+          echo "_Every protected path holds exactly the files it held before this run, byte-size and"
+          echo "mtime unchanged. The automated lanes wrote nothing into the operator's store._"
+        elif [[ "$VERDICT" == "UNKNOWN" ]]; then
+          echo "_No baseline was captured for this run, so nothing here proves the store was untouched._"
+        else
+          echo "_An automated lane wrote into a protected store path. Records and ledgers in this"
+          echo "project are append-only, so these files cannot simply be deleted — they are listed"
+          echo "here so the next reader knows what caused them._"
+          echo ""
+          echo "| Change | Path |"
+          echo "|--------|------|"
+          for f in $ADDED;    do [[ -n "$f" ]] && echo "| ADDED | \`$f\` |"; done
+          for f in $REMOVED;  do [[ -n "$f" ]] && echo "| REMOVED | \`$f\` |"; done
+          for f in $MODIFIED; do [[ -n "$f" ]] && echo "| MODIFIED | \`$f\` |"; done
+        fi
+      } > "$REPORT" 2>/dev/null || _ss_warn "$LABEL: could not write the disclosure artifact at $REPORT."
+    fi
+    rm -f "$NOW" 2>/dev/null || true
+    if [[ "$VERDICT" == "BREACH" ]]; then
+      _ss_warn "$LABEL: STORE-SCOPE BREACH — an automated lane wrote into a protected store path:"
+      for f in $ADDED;    do [[ -n "$f" ]] && _ss_warn "  ADDED    $f"; done
+      for f in $REMOVED;  do [[ -n "$f" ]] && _ss_warn "  REMOVED  $f"; done
+      for f in $MODIFIED; do [[ -n "$f" ]] && _ss_warn "  MODIFIED $f"; done
+      [[ -n "$REPORT" ]] && _ss_warn "  disclosure: $REPORT"
+      exit 1
+    fi
+    _ss_log "$LABEL: store-scope verified $VERDICT${REPORT:+ (disclosure: $REPORT)}."
+    exit 0
+    ;;
+
+  *)
+    echo "usage: store-scope.sh require | snapshot <manifest> | verify <manifest> [report.md]" >&2
+    exit 2
+    ;;
+esac
diff --git a/incredible_auto_dev/tests/automation/test-store-scope-guard.sh b/incredible_auto_dev/tests/automation/test-store-scope-guard.sh
new file mode 100755
index 0000000..97c531e
--- /dev/null
+++ b/incredible_auto_dev/tests/automation/test-store-scope-guard.sh
@@ -0,0 +1,173 @@
+#!/usr/bin/env bash
+# test-store-scope-guard.sh — unit tests for scripts/automation/store-scope/store-scope.sh
+# and the lib/replay-lane.sh wrappers that call it.
+#
+# WHY THIS EXISTS: a goal-mode iteration shipped a *launcher* that stands up a
+# fixture-scoped backend, and then the pipeline's own browser/replay lanes ran
+# against whatever backend happened to be listening — writing real records and a
+# run-ledger row into the operator's append-only store. A launcher nothing is
+# obliged to use is not a mechanism. This guard makes it one:
+#
+#   • require  — refuse to run any browser lane unless the project's own assert
+#     command proves the backend under test is the scoped one (one prepare
+#     attempt in between, when the project declares a prepare command);
+#   • snapshot/verify — bracket the run with a manifest of the project's
+#     protected store paths and hard-fail on ANY delta, so "the real store was
+#     untouched" stops being prose and becomes an artifact.
+#
+# Absent project-extensions/store-scope/store-scope.env ⇒ every entry point is a
+# no-op exiting 0: the framework stays project-neutral (the host-guard
+# precedent), and every other project's stdout is byte-identical.
+#
+# No API calls, no network, no browser; runs in about a second.
+#
+# shellcheck disable=SC1090,SC1091,SC2015,SC2034
+set -euo pipefail
+
+SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+ENGINE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
+
+PASS=0
+FAIL=0
+assert() {
+  if [[ "$2" == "pass" ]]; then echo "  PASS  $1"; PASS=$((PASS + 1)); else echo "  FAIL  $1"; FAIL=$((FAIL + 1)); fi
+}
+
+WORK="$(mktemp -d)"
+cleanup() { rm -rf "$WORK"; }
+trap cleanup EXIT
+
+SBX="$WORK/proj"
+mkdir -p "$SBX"
+cp -r "$ENGINE_ROOT/scripts" "$SBX/"
+GUARD="$SBX/scripts/automation/store-scope/store-scope.sh"
+LIB="$SBX/scripts/automation/lib/replay-lane.sh"
+
+STORE="$SBX/apps/backend/.data"
+mkdir -p "$STORE/playbook" "$STORE/playbook_runs"
+echo '{"id":"pre-existing"}' > "$STORE/playbook/record-1.json"
+
+write_env() {  # $1 = extra lines
+  mkdir -p "$SBX/project-extensions/store-scope"
+  {
+    echo 'STORE_SCOPE_ENABLED=1'
+    echo 'STORE_SCOPE_LABEL="test rig"'
+    echo 'STORE_SCOPE_PROTECTED_PATHS="apps/backend/.data/playbook apps/backend/.data/playbook_runs"'
+    printf '%s\n' "$1"
+  } > "$SBX/project-extensions/store-scope/store-scope.env"
+}
+
+run_guard() {  # subcommand + args; echoes rc
+  local rc=0
+  ( cd "$SBX" && STORE_SCOPE_ROOT="$SBX" bash "$GUARD" "$@" ) >"$WORK/guard.out" 2>&1 || rc=$?
+  echo "$rc"
+}
+
+echo "== 1. No project config: every entry point is a neutral no-op =="
+rm -rf "$SBX/project-extensions/store-scope"
+rc="$(run_guard require)";                          [[ "$rc" == "0" ]] && assert "require no-ops without config" pass || assert "require no-ops without config (rc=$rc)" fail
+rc="$(run_guard snapshot "$WORK/m0.txt")";          [[ "$rc" == "0" ]] && assert "snapshot no-ops without config" pass || assert "snapshot no-ops without config (rc=$rc)" fail
+rc="$(run_guard verify "$WORK/m0.txt" "$WORK/r0.md")"; [[ "$rc" == "0" ]] && assert "verify no-ops without config" pass || assert "verify no-ops without config (rc=$rc)" fail
+[[ ! -f "$WORK/r0.md" ]] && assert "no disclosure artifact written without config" pass || assert "no disclosure artifact written without config" fail
+
+echo "== 2. require: the project's assert command decides =="
+write_env 'STORE_SCOPE_ASSERT_CMD="bash scripts-assert.sh"'
+cat > "$SBX/scripts-assert.sh" <<'EOF'
+#!/usr/bin/env bash
+echo "assert ran" >> "$SBX_STAMP"
+[[ -f "$SBX_SCOPED_MARKER" ]]
+EOF
+export SBX_STAMP="$WORK/assert.log" SBX_SCOPED_MARKER="$WORK/scoped.marker"
+: > "$SBX_STAMP"; : > "$SBX_SCOPED_MARKER"
+rc="$(run_guard require)"
+[[ "$rc" == "0" ]] && assert "require passes when the assert command succeeds" pass || assert "require passes when the assert command succeeds (rc=$rc)" fail
+[[ "$(wc -l < "$SBX_STAMP")" == "1" ]] && assert "assert command ran exactly once on the happy path" pass || assert "assert command ran exactly once on the happy path" fail
+
+echo "== 3. require: assert fails, prepare rescues it =="
+write_env 'STORE_SCOPE_ASSERT_CMD="bash scripts-assert.sh"
+STORE_SCOPE_PREPARE_CMD="bash scripts-prepare.sh"'
+cat > "$SBX/scripts-prepare.sh" <<'EOF'
+#!/usr/bin/env bash
+echo "prepare ran" >> "$SBX_PREP_STAMP"
+touch "$SBX_SCOPED_MARKER"
+EOF
+export SBX_PREP_STAMP="$WORK/prepare.log"
+: > "$SBX_STAMP"; : > "$SBX_PREP_STAMP"; rm -f "$SBX_SCOPED_MARKER"
+rc="$(run_guard require)"
+[[ "$rc" == "0" ]] && assert "require passes after the prepare command scopes the backend" pass || assert "require passes after prepare (rc=$rc)" fail
+[[ "$(wc -l < "$SBX_PREP_STAMP")" == "1" ]] && assert "prepare ran exactly once" pass || assert "prepare ran exactly once" fail
+[[ "$(wc -l < "$SBX_STAMP")" == "2" ]] && assert "assert re-ran after prepare (2 invocations)" pass || assert "assert re-ran after prepare" fail
+
+echo "== 4. require: prepare cannot scope it -> refusal (rc 1) =="
+cat > "$SBX/scripts-prepare.sh" <<'EOF'
+#!/usr/bin/env bash
+echo "prepare ran" >> "$SBX_PREP_STAMP"
+EOF
+: > "$SBX_STAMP"; : > "$SBX_PREP_STAMP"; rm -f "$SBX_SCOPED_MARKER"
+rc="$(run_guard require)"
+[[ "$rc" == "1" ]] && assert "require REFUSES when the backend cannot be scoped" pass || assert "require REFUSES when the backend cannot be scoped (rc=$rc)" fail
+grep -qi "not scoped\|refus" "$WORK/guard.out" && assert "refusal says why, loudly" pass || assert "refusal says why, loudly" fail
+
+echo "== 5. snapshot/verify: an untouched store verifies CLEAN =="
+write_env ''
+: > "$WORK/m1.txt"
+rc="$(run_guard snapshot "$WORK/m1.txt")"
+[[ "$rc" == "0" && -s "$WORK/m1.txt" ]] && assert "snapshot writes a manifest" pass || assert "snapshot writes a manifest (rc=$rc)" fail
+rc="$(run_guard verify "$WORK/m1.txt" "$WORK/r1.md")"
+[[ "$rc" == "0" ]] && assert "verify is CLEAN when nothing changed" pass || assert "verify is CLEAN when nothing changed (rc=$rc)" fail
+grep -q "CLEAN" "$WORK/r1.md" && assert "clean run still writes the disclosure artifact" pass || assert "clean run still writes the disclosure artifact" fail
+
+echo "== 6. verify: a NEW record file under a protected path is a BREACH =="
+# This is the iteration-8 failure, reproduced: a replay run appended a playbook
+# record + a back-scan ledger row into the operator's real store.
+echo '{"id":"playbook-2026-06-22"}' > "$STORE/playbook/record-2.json"
+echo '{"status":"done"}' > "$STORE/playbook_runs/backscanrun-1.json"
+rc="$(run_guard verify "$WORK/m1.txt" "$WORK/r2.md")"
+[[ "$rc" == "1" ]] && assert "verify FAILS on a new file under a protected path" pass || assert "verify FAILS on a new file under a protected path (rc=$rc)" fail
+grep -q "BREACH" "$WORK/r2.md" && assert "breach report is headlined BREACH" pass || assert "breach report is headlined BREACH" fail
+grep -q "record-2.json" "$WORK/r2.md" && assert "breach report names the added record file" pass || assert "breach report names the added record file" fail
+grep -q "backscanrun-1.json" "$WORK/r2.md" && assert "breach report names the added ledger file" pass || assert "breach report names the added ledger file" fail
+
+echo "== 7. verify: a MODIFIED protected file is a BREACH too =="
+rm -f "$STORE/playbook/record-2.json" "$STORE/playbook_runs/backscanrun-1.json"
+: > "$WORK/m2.txt"; run_guard snapshot "$WORK/m2.txt" >/dev/null
+sleep 0.01
+echo '{"id":"pre-existing","tampered":true}' > "$STORE/playbook/record-1.json"
+rc="$(run_guard verify "$WORK/m2.txt" "$WORK/r3.md")"
+[[ "$rc" == "1" ]] && assert "verify FAILS on a modified protected file" pass || assert "verify FAILS on a modified protected file (rc=$rc)" fail
+grep -q "record-1.json" "$WORK/r3.md" && assert "breach report names the modified file" pass || assert "breach report names the modified file" fail
+
+echo "== 8. lib/replay-lane.sh wrappers =="
+run_wrapper() {  # $1 = wrapper call
+  (
+    set -euo pipefail
+    source "$LIB"
+    REPO_ROOT="$SBX"
+    STORE_SCOPE_ROOT="$SBX"
+    eval "$1"
+  ) >"$WORK/wrap.out" 2>&1
+}
+write_env 'STORE_SCOPE_ASSERT_CMD="bash scripts-assert.sh"'
+: > "$SBX_STAMP"; : > "$SBX_SCOPED_MARKER"
+rc=0; run_wrapper 'store_scope_require' || rc=$?
+[[ "$rc" == "0" ]] && assert "store_scope_require wrapper passes through success" pass || assert "store_scope_require wrapper passes through success (rc=$rc)" fail
+rm -f "$SBX_SCOPED_MARKER"
+rc=0; run_wrapper 'store_scope_require' || rc=$?
+[[ "$rc" == "1" ]] && assert "store_scope_require wrapper passes through refusal" pass || assert "store_scope_require wrapper passes through refusal (rc=$rc)" fail
+rc=0; run_wrapper "store_scope_snapshot '$WORK/m3.txt'" || rc=$?
+[[ "$rc" == "0" && -s "$WORK/m3.txt" ]] && assert "store_scope_snapshot wrapper writes the manifest" pass || assert "store_scope_snapshot wrapper writes the manifest (rc=$rc)" fail
+echo '{"id":"another"}' > "$STORE/playbook/record-3.json"
+rc=0; run_wrapper "store_scope_verify '$WORK/m3.txt' '$WORK/r4.md'" || rc=$?
+[[ "$rc" == "1" ]] && assert "store_scope_verify wrapper passes through the breach" pass || assert "store_scope_verify wrapper passes through the breach (rc=$rc)" fail
+rm -f "$STORE/playbook/record-3.json"
+
+# The wrappers must survive a stripped engine (no store-scope dir at all) —
+# a project that never syncs the feature keeps today's behavior exactly.
+mv "$SBX/scripts/automation/store-scope" "$WORK/store-scope-away"
+rc=0; run_wrapper 'store_scope_require' || rc=$?
+[[ "$rc" == "0" ]] && assert "wrappers no-op when the guard script is absent" pass || assert "wrappers no-op when the guard script is absent (rc=$rc)" fail
+mv "$WORK/store-scope-away" "$SBX/scripts/automation/store-scope"
+
+echo ""
+echo "test-store-scope-guard: $PASS passed, $FAIL failed"
+[[ "$FAIL" -eq 0 ]]
diff --git a/project-extensions/store-scope/README.md b/project-extensions/store-scope/README.md
new file mode 100644
index 0000000..b71580f
--- /dev/null
+++ b/project-extensions/store-scope/README.md
@@ -0,0 +1,69 @@
+# Store-scope guard — the QA lanes cannot reach the operator's real store
+
+## Why this exists
+
+`goal-playbook-iter-8` shipped a launcher — `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`
+— that stands up a fully fixture-scoped backend (own bars, own universe, own playbook/ledger dirs,
+own caches) so a browser pass can click **Run Playbook** or **Run Backscan** without touching
+`apps/backend/.data/`. The launcher was correct. Nothing was obliged to use it.
+
+In that same iteration's own pipeline run, the deterministic replay lane replayed J-07 — whose
+golden contains a real "Run Backscan" click — against whatever was listening on the QA port: the
+operator's ambient backend. It computed three real S&P-100 playbook records and appended a back-scan
+run-ledger row:
+
+```
+apps/backend/.data/playbook/playbook-2026-06-22-fc4182ae9bb8.json          14:45:30
+apps/backend/.data/playbook/playbook-2026-06-23-e496c53902bc.json          14:45:45
+apps/backend/.data/playbook/playbook-2026-06-24-e5f41a0c720e.json          14:45:47
+apps/backend/.data/playbook_backscan_runs/backscanrun-2026-08-11-…json     14:45:47
+```
+
+Those files are append-only by the project's own immutable-data rail, so they stay. The audit's
+verdict on the deliverable was exact: **the fix was a launcher, not a mechanism.** This directory is
+the mechanism.
+
+## What it does
+
+`store-scope.env` is read by the framework guard
+(`incredible_auto_dev/scripts/automation/store-scope/store-scope.sh`), which the goal-mode browser
+lanes call around every run — `browser-qa-phase.sh` at full depth and `goal-iter-lean.sh` at lean:
+
+| Phase | Call | Effect |
+|-------|------|--------|
+| Before any lane | `store_scope_require` | Runs `assert_scoped_qa_backend.py`. If the QA backend is not the fixture rig it runs `start_scoped_qa_backend.sh` once and re-asserts. Still not scoped ⇒ **neither the replay lane nor the LLM browser dispatch runs at all** (journeys are tokenised `pending-infra`, never reported as verified). |
+| Before any lane | `store_scope_snapshot` | Manifest (size + mtime) of every file under `STORE_SCOPE_PROTECTED_PATHS`. |
+| After the lanes | `store_scope_verify` | Re-scans and hard-fails on ANY delta — added, removed, or modified — writing `reports/qa/<iter>-store-scope-guard.md` either way, plus a loud section in the authoritative `ui-test-results.md` and a `store_scope_breach` telemetry event on a breach. |
+
+The disclosure artifact is the point: "the operator's store was untouched" stops being a sentence in
+a report and becomes an executed check with a file list behind it.
+
+## The two project-owned commands
+
+* **`apps/backend/scripts/assert_scoped_qa_backend.py`** — reads `GET /research/desk/universe` and
+  requires the LATEST snapshot's `source_url` to start with `fixture-rig`. Every fixture seeder
+  registers its universe that way; a real fetch registers the Wikipedia S&P-100 URL. Anything it
+  cannot prove (no snapshot, unreadable body, connection refused) is **not scoped**. Unit-tested in
+  `apps/backend/tests/test_qa_scoped_backend_guard.py`.
+* **`apps/backend/scripts/start_scoped_qa_backend.sh`** — frees the QA port (recording the replaced
+  process's command line in `<log-dir>/replaced-listener-<port>.txt` so the operator can restart it
+  verbatim),
+  seeds a fresh scoped root through the one mandatory launcher, and waits for `/health`.
+
+## Running it by hand
+
+```bash
+bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh require
+bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh snapshot /tmp/base.manifest
+#   … browser / replay work …
+bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh verify /tmp/base.manifest \
+     reports/qa/<iter>-store-scope-guard.md
+```
+
+## What is deliberately NOT protected
+
+The derived accelerator DBs (`bar_index.db`, `*_meta_cache.db`, `tradability_cache.db`,
+`setups_scan_cache.db`, `edge_report_*.db`, `playbook_evidence_cache.db`, `journal.db`). They are
+stat-keyed projections that own nothing and are rebuilt on demand, and a legitimate read path
+updates them. Listing them would make every clean run a false breach — and a guard that cries wolf
+is a guard the next reader ignores.
diff --git a/project-extensions/store-scope/store-scope.env b/project-extensions/store-scope/store-scope.env
new file mode 100644
index 0000000..d0cf68a
--- /dev/null
+++ b/project-extensions/store-scope/store-scope.env
@@ -0,0 +1,35 @@
+# store-scope.env — which store paths an automated browser lane may never write, and how this
+# project proves the backend under test is the fixture rig.
+#
+# Read by incredible_auto_dev/scripts/automation/store-scope/store-scope.sh, which the goal-mode
+# browser lanes (browser-qa-phase.sh at full depth, goal-iter-lean.sh at lean) call BEFORE any
+# replay or LLM dispatch and AFTER the run.
+#
+# WHY (goal-playbook-iter-8 audit, finding B2): the iteration whose acceptance said "no replay
+# script can ever reach the operator's ambient :8301 / real .data/ store" replayed J-07's
+# "Run Backscan" click against exactly that backend. It computed three real S&P-100 playbook
+# records (2026-06-22/23/24) and appended a back-scan run-ledger row — into stores this project's
+# own immutable-data rail forbids ever pruning. The launcher that would have prevented it existed
+# and was correct; nothing obliged the lane to use it. These four lines are that obligation.
+
+STORE_SCOPE_ENABLED=1
+STORE_SCOPE_LABEL="tapeology real .data store"
+
+# PROTECTED: the append-only record/ledger stores. Every path here is content the project promises
+# is never rewritten, pruned, or superseded — so an automated lane creating or touching one is a
+# rail violation, not a cache miss.
+#
+# Deliberately NOT listed: the derived accelerator DBs (bar_index.db, *_meta_cache.db,
+# tradability_cache.db, setups_scan_cache.db, edge_report_*.db, playbook_evidence_cache.db,
+# journal.db). They are stat-keyed projections that own nothing and are rebuilt on demand; a read
+# path legitimately updates them, and listing them would turn every clean run into a false breach —
+# which would train the next reader to ignore the guard. The stores below are the ones that matter.
+STORE_SCOPE_PROTECTED_PATHS="apps/backend/.data/playbook apps/backend/.data/playbook_runs apps/backend/.data/playbook_backscan_runs apps/backend/.data/universe apps/backend/.data/screen apps/backend/.data/screen_runs apps/backend/.data/forward apps/backend/.data/forward_runs apps/backend/.data/topup_runs apps/backend/.data/index_reconcile_runs apps/backend/.data/bars apps/backend/.data/datasets"
+
+# ASSERT: exits 0 only when the backend on the QA port serves a fixture-rig universe snapshot.
+# Fails closed on anything it cannot prove (see the script's docstring).
+STORE_SCOPE_ASSERT_CMD="apps/backend/.venv/bin/python apps/backend/scripts/assert_scoped_qa_backend.py"
+
+# PREPARE: put the fixture rig on the QA port (replacing the ambient listener, disclosed) so the
+# assert can pass. Runs at most once per lane; the assert — never this — decides.
+STORE_SCOPE_PREPARE_CMD="bash apps/backend/scripts/start_scoped_qa_backend.sh"
```
