# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 87daa2a..4d900b4 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -123,6 +123,7 @@ from .desk_forward import ForwardStore, resolve_desk_forward_dir
 from .desk_forward_compute import DeskForwardComputeManager
 from .desk_forward_log import ForwardRunStore, resolve_desk_forward_log_dir
 from .desk_forward_pins import resolve_desk_forward_pins
+from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
 from .desk_screen_diff import ScreenDiffSelfCompareError, compute_screen_diff
@@ -946,6 +947,80 @@ def get_desk_forward_pins(
     )
 
 
+# --- The Playbook (Era B2, J-01) — pre-registered, lookahead-clean intraday setups detected on the
+# desk's own recorded 5m/1m bars (docs/playbook-detector-spec.md). J-01 ships detection only (no
+# measurement, no compute-manager/trigger route, no CLI) plus this ONE read; see desk_playbook.py
+# for the computation, store, and parameters/signature recipe this route only serves verbatim. ----
+
+
+def get_playbook_store() -> PlaybookStore:
+    """The playbook store rooted at a bare env-var-or-sibling-of-the-universe-dir default (zero new
+    ``Config`` field — see ``desk_playbook.resolve_desk_playbook_dir``) — the ``get_forward_store``
+    pattern. A FastAPI dependency so tests can point it at a temp dir via the env var or override
+    it outright."""
+    return PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def _playbook_meta_only(record: dict) -> dict:
+    """The lightweight projection the bulk list serves — id/pins/parameters/counts only, never the
+    full ``signals``/``absences``/``diagnostics`` lists (the ``_forward_meta_only`` convention)."""
+    return {
+        "id": record["id"],
+        "session_date": record["session_date"],
+        "config_fingerprint": record["config_fingerprint"],
+        "playbook_input_signature": record["playbook_input_signature"],
+        "payload_version": record["payload_version"],
+        "parameters": record["parameters"],
+        "recorded_at": record["recorded_at"],
+        "counts": {
+            "signals": len(record["signals"]),
+            "absences": len(record["absences"]),
+            "diagnostics": len(record["diagnostics"]),
+        },
+    }
+
+
+@router.get("/playbook")
+def get_playbook(
+    date: str | None = None, id: str | None = None, store: PlaybookStore = Depends(get_playbook_store)
+) -> dict:
+    """Three shapes, selected by ``?date=``/``?id=`` (the ``GET /research/desk/screen`` convention):
+
+      * neither given: ``{"playbooks": [...meta-only...], "latest": <full record>|null,
+        "integrity_errors": [...]}`` — an explicit HTTP 200 honest-empty payload
+        (``{"playbooks": [], "latest": null, "integrity_errors": []}``) before any playbook has
+        ever been computed, never a 404. ``latest`` is the most recently RECORDED playbook (a
+        playbook, like a forward measurement and unlike a screen, is an ATTEMPT that can carry
+        several versions per date as parameters change — ``desk_forward``'s ``latest`` convention,
+        not ``desk_screen``'s date-first one).
+      * ``date=YYYY-MM-DD`` (``id`` absent): ``{"playbook": <newest record for that date>|null,
+        "versions": <how many records that date has ever accumulated>}`` — a plain read, never
+        recomputed on the GET; an unknown date is an honest ``null``/``0`` at HTTP 200.
+      * ``id=<record id>`` (``date`` absent): ``{"playbook": <that exact persisted record>|null}``
+        — the only way to reach an EARLIER same-date recording once a later one exists (``?date=``
+        always resolves to the newest match); an unknown id is an honest ``null``, never a 404.
+      * ``id`` and ``date`` both given: an honest 4xx refusal — never a silent precedence rule.
+
+    A plain read: writes nothing, triggers nothing, recomputes nothing (GET-never-computes) — this
+    route takes no ``BarStore``/``UniverseStore``/compute-manager dependency at all, so it is
+    structurally incapable of triggering ``compute_playbook``."""
+    if id is not None and date is not None:
+        raise HTTPException(
+            status_code=422, detail="only one of `id` or `date` may be supplied, not both"
+        )
+    if id is not None:
+        return {"playbook": store.get(id)}
+    if date is not None:
+        newest, versions = store.newest_for_date(date)
+        return {"playbook": newest, "versions": versions}
+    records, errors = store.list()
+    return {
+        "playbooks": [_playbook_meta_only(r) for r in records],
+        "latest": records[-1] if records else None,
+        "integrity_errors": errors,
+    }
+
+
 # --- Coverage-index reconciliation (J-10, goal-desk-iter-14) — a trigger/poll/cancel trio mirroring
 # the top-up compute trio exactly, plus ONE durable read mirroring ``GET /research/desk/topup/runs``.
 # See ``desk_index_reconcile.py`` for the classify/repair/record mechanics this only wires up. -------
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-playbook/telemetry.jsonl   | 9 +++++++++
 runs/goal-session-playbook/trace/trace.jsonl | 2 ++
 2 files changed, 11 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
