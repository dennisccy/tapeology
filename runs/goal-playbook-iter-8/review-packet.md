# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 13. Shown in full: 13.

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
```

## Excluded-path stat (dependency/lockfile visibility)

 .../journey-scripts/J-04.json                      |  4 +-
 .../journey-scripts/J-05.json                      |  2 +-
 .../goal-session-playbook/state/iteration-state.md | 17 +++++++++
 runs/goal-session-playbook/telemetry.jsonl         | 43 ++++++++++++++++++++++
 runs/goal-session-playbook/trace/trace.jsonl       |  9 +++++
 5 files changed, 72 insertions(+), 3 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
