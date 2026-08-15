# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 9. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (10 lines not shown)

```diff
diff --git a/apps/backend/app/research/referee_adjudicate.py b/apps/backend/app/research/referee_adjudicate.py
index 40ca1f2..d98bf51 100644
--- a/apps/backend/app/research/referee_adjudicate.py
+++ b/apps/backend/app/research/referee_adjudicate.py
@@ -1132,6 +1132,18 @@ def run_evaluation_and_record(
                     fields["entry_basis_sign_flip"] = _signs_differ(entry_t, primary_t)
         _tick()
 
+        # iter-8 Rider 1 (evaluator-diagnosed, iteration 7): a failed oracle attestation must
+        # never mint the hypothesis's ONE permanent checkpoint snapshot -- the WRITE side needs
+        # the SAME gate the READ side (`_snapshot_fold`, via `verify_oracle_attestation`) already
+        # carries, because the read side can be re-run and an append-only record cannot.
+        # Downgrades ONLY the "checkpoint" case: "monitoring"/"pending" never write a snapshot
+        # regardless (only `role == "checkpoint"` reaches `_build_and_record_snapshot` below), so
+        # nothing else changes. Every other field (T/permutation_p/CIs/etc.) stays exactly as
+        # computed above -- they are honest descriptive numbers regardless of attestation state;
+        # only the permanent-write eligibility is gated.
+        if fields["role"] == "checkpoint" and not fields["attestation"]["passed"]:
+            fields["role"] = "pending"
+
         recorded = evaluation_store.record(fields)
     except Exception as exc:  # noqa: BLE001 -- logged, then re-raised verbatim, never swallowed
         _log(state="failed", done=done_units, total=total_units, error=str(exc))
@@ -1403,8 +1415,13 @@ def adjudications_response(
     pure-function fold (TC-23: byte-stable across calls against an unchanged store). A hypothesis
     whose OWN snapshot file exists but fails its integrity check folds to a dedicated refusal
     (never silently treated as "no snapshot", which would misrepresent an already-checkpointed
-    hypothesis). Never 404/500 on an empty or partially-corrupted registry (TC-25)."""
-    hypotheses, _errors = hypothesis_store.list()
+    hypothesis). Never 404/500 on an empty or partially-corrupted registry (TC-25). Also carries
+    ``integrity_errors`` (iter-8 Rider 2, evaluator-diagnosed iteration 7): ``hypothesis_store.
+    list()``'s own errors, surfaced the SAME way ``referee_registry.registry_response()`` already
+    surfaces its four stores' errors, instead of the ``_errors`` this function used to discard
+    silently -- an integrity-error disclosure belongs on EVERY reader of a store, not just the one
+    an audit happened to name."""
+    hypotheses, hypothesis_errors = hypothesis_store.list()
     live_basis = current_playbook_detector_basis()
     snapshot_records, snapshot_errors = snapshot_store.list()
     snapshot_by_hypothesis_id = {r["hypothesis_id"]: r for r in snapshot_records}
@@ -1422,7 +1439,11 @@ def adjudications_response(
             live_basis=live_basis, snapshot_unverifiable=hypothesis_id in unverifiable_hypothesis_ids,
         )
         entries.append({"hypothesis_id": hypothesis_id, **folded})
-    return {"entries": entries, "register": REFEREE_REGISTER}
+    return {
+        "entries": entries,
+        "register": REFEREE_REGISTER,
+        "integrity_errors": hypothesis_errors,
+    }
 
 
 # === authorize_promotion: the J-08 interlock's pure decision function (unwired this iteration) ========
diff --git a/apps/backend/app/research/referee_registry.py b/apps/backend/app/research/referee_registry.py
index 8e96329..1a349fa 100644
--- a/apps/backend/app/research/referee_registry.py
+++ b/apps/backend/app/research/referee_registry.py
@@ -82,7 +82,18 @@ POST-BOUNDARY ``session_date``s carrying >=1 observation in the hypothesis's own
 (``_newest_per_session_date``, ``_is_stale_basis``, ``current_playbook_detector_basis``) --
 never a second, independently-written date/basis loop, and never a second ``PlaybookStore``
 scan per hypothesis: ``registry_response`` scans the store exactly ONCE per call and folds every
-hypothesis's own accrual against that single scan."""
+hypothesis's own accrual against that single scan.
+
+**iter-8 (J-07) additions -- the starter-family shortlist + the discovery fold, plus two
+write-side riders.** ``shortlist_response()`` serves spec Sec7's five PINNED candidates
+(``REFEREE_STARTER_FAMILY_SHORTLIST``) beside LIVE readiness (``GET .../registry/shortlist``) --
+the FIRST real, browser-usable Referee action of the whole era. ``registry_response()``'s
+per-hypothesis fold gains a ``discovery`` block (``_hypothesis_discovery``): the exact
+PRE-boundary complement of ``accrual``, over the SAME pooling primitives -- never a confirmatory
+count, always labeled ``"discovery (exploratory)"``. Neither addition writes anything; both are
+pure reads over the identical already-scanned corpus. This module's own two write-side riders
+(a failed-attestation write gate, an integrity-error disclosure) live in ``referee_adjudicate.py``
+instead, since that is where the affected writer/reader actually is."""
 
 from __future__ import annotations
 
@@ -90,10 +101,11 @@ import argparse
 import hashlib
 import json
 import os
-from datetime import datetime, timezone
+from datetime import date, datetime, timezone
 from pathlib import Path
 
-from ..config import CONFIG
+from ..config import CONFIG, Config
+from .bars import BarStore
 from .desk_playbook import PlaybookStore
 from .referee_evidence import (
     _epoch_from_iso,
@@ -102,19 +114,24 @@ from .referee_evidence import (
     _newest_per_session_date,
     _record_detector_basis,
     current_playbook_detector_basis,
+    playbook_occurrence_readiness,
 )
 from .referee_null import (
+    AT_WALL,
     PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
     PLAYBOOK_CONTEXT_BACKING_BUCKETS,
     REFEREE_NULL_CONTEXT_SPEC_ID,
     REFEREE_NULL_TOD_SPEC_ID,
     REFEREE_TEST_PERM_SPEC_ID,
+    BandMapResolver,
+    resolve_occurrence_backing_bucket,
 )
 
 __all__ = [
     "REFEREE_MIN_SESSIONS",
     "REFEREE_MIN_OCCURRENCES",
     "REFEREE_HYPOTHESIS_ORIGIN",
+    "REFEREE_STARTER_FAMILY_SHORTLIST",
     "resolve_referee_registry_dir",
     "RegistryIntegrityError",
     "FamilyAlreadyRecorded",
@@ -132,6 +149,7 @@ __all__ = [
     "register_hypothesis",
     "withdraw_hypothesis",
     "registry_response",
+    "shortlist_response",
 ]
 
 # === spec Sec1: the two floors this module is the first consumer of (module constants, never
@@ -815,6 +833,43 @@ def _hypothesis_accrual(
     }
 
 
+def _hypothesis_discovery(
+    hypothesis: dict,
+    newest_by_date: dict[str, dict],
+    *,
+    live_basis: str,
+    config_fingerprint: str,
+) -> dict:
+    """The ``discovery (exploratory)`` block (goal.md J-07 Step 4): pre-boundary (``session_date
+    <= confirmation_start_boundary``) observations in the hypothesis's own ``(setup_id, side)``
+    cell -- the exact COMPLEMENT of ``_hypothesis_accrual``'s own post-boundary walk, over the
+    SAME already-scanned ``newest_by_date`` map and the SAME current-basis filter (never a second
+    pooling implementation). ``state/assumptions.md`` (iter-8) rules the stale-basis exclusion
+    applies here too, for consistency with ``accrual``. Never contributes to the ``accrual``
+    block; a deep-backfilled pre-boundary record recorded AFTER registration still lands here,
+    keyed on ``session_date`` alone -- never ``recorded_at`` (TC-10)."""
+    boundary = hypothesis["confirmation_start_boundary"]
+    setup_id = hypothesis["setup_id"]
+    side = hypothesis["side"]
+    n = 0
+    discovery_dates: set[str] = set()
+    for session_date, record in newest_by_date.items():
+        if session_date > boundary:
+            continue  # discovery is PRE-boundary only -- accrual's own filter, inverted
+        if _is_stale_basis(
+            _record_detector_basis(record),
+            record["config_fingerprint"],
+            live_basis=live_basis,
+            live_config_fingerprint=config_fingerprint,
+        ):
+            continue  # T-6: pool only at the current (detector_basis, config_fingerprint)
+        for signal in record["signals"]:
+            if signal["setup_id"] == setup_id and signal["side"] == side:
+                n += 1
+                discovery_dates.add(session_date)
+    return {"n": n, "n_sessions": len(discovery_dates), "label": "discovery (exploratory)"}
+
+
 def registry_response(
     *,
     family_store: FamilyStore,
@@ -825,9 +880,10 @@ def registry_response(
     config_fingerprint: str,
 ) -> dict:
     """The whole ``GET /research/desk/referee/registry`` body -- the pinned five-key shape
-    (``runs/goal-session-referee/state/blueprint.md`` iter-6/iter-7 notes): ``families``,
-    ``hypotheses`` (each folded with ``status`` + ``accrual``), ``withdrawals``, ``certificates``,
-    plus ``integrity_errors`` (iter-7 Rider 2, audit gap B4). Never 404/500 on an empty or
+    (``runs/goal-session-referee/state/blueprint.md`` iter-6/iter-7/iter-8 notes): ``families``,
+    ``hypotheses`` (each folded with ``status`` + ``accrual`` + ``discovery``, iter-8 J-07),
+    ``withdrawals``, ``certificates``, plus ``integrity_errors`` (iter-7 Rider 2, audit gap B4).
+    Never 404/500 on an empty or
     partially-corrupted registry (the desk router's established never-404-on-absence convention;
     ``get_referee_nulls``'s own ``{"records": [...], "integrity_errors": [...]}`` disclosure
     pattern, reused here rather than inventing a second shape -- each of the four stores' own
@@ -858,8 +914,13 @@ def registry_response(
         accrual = _hypothesis_accrual(
             hypothesis, newest_by_date, live_basis=live_basis, config_fingerprint=config_fingerprint
         )
+        discovery = _hypothesis_discovery(
+            hypothesis, newest_by_date, live_basis=live_basis, config_fingerprint=config_fingerprint
+        )
         status = "withdrawn" if hypothesis["hypothesis_id"] in withdrawn_ids else "active"
-        folded_hypotheses.append({**hypothesis, "status": status, "accrual": accrual})
+        folded_hypotheses.append(
+            {**hypothesis, "status": status, "accrual": accrual, "discovery": discovery}
+        )
 
     return {
         "families": families,
@@ -870,6 +931,208 @@ def registry_response(
     }
 
 
+# === J-07: the starter-family shortlist -- GET /research/desk/referee/registry/shortlist ==============
+#
+# goal.md J-07 Step 1 ("serve the shortlist... beside LIVE readiness"). spec Sec7's five candidates
+# as PINNED module constants (T-1: never derived, never tunable) -- the exact same field values
+# ``test_referee_registry.py``'s own already-established ``_starter_family_payloads()`` helper
+# already uses to test the write path (that helper builds REGISTRATION-payload fixtures; these are
+# the shortlist's own read-side PRODUCTION constants -- the two serve different purposes,
+# state/assumptions.md iter-8). "No hard-coded hypothesis set" (goal.md J-07 Step 2) governs the
+# REGISTRATION WRITE PATH staying generic (``register_hypothesis`` already accepts any valid
+# hypothesis, never only these five) -- it does not forbid the shortlist's own spec-pinned list from
+# existing as a module constant, exactly like ``REFEREE_MIN_SESSIONS`` or the null-spec ids already
+# do (state/assumptions.md iter-8).
+
+REFEREE_STARTER_FAMILY_SHORTLIST: tuple[dict, ...] = (
+    {
+        "candidate_id": "S-1", "estimand": "A", "evidence_family": "playbook",
+        "setup_id": "capitulation", "side": "long", "context_predicate": None,
+        "primary_measure_key": "5m", "primary_horizon": "5m", "sidedness": "greater",
+        "null_spec_id": REFEREE_NULL_TOD_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
+        "rationale": (
+            "the book's capitulation claim is the immediate reflexive snapback off climax "
+            "exhaustion -- minutes-scale, not session-scale"
+        ),
+    },
+    {
+        "candidate_id": "S-2", "estimand": "A", "evidence_family": "playbook",
+        "setup_id": "jbe", "side": "long", "context_predicate": None,
+        "primary_measure_key": "1h", "primary_horizon": "1h", "sidedness": "greater",
+        "null_spec_id": REFEREE_NULL_TOD_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
+        "rationale": (
+            "jump-base-explosion claims continuation of an established leg -- the follow-through "
+            "hour after the base resolves"
+        ),
+    },
+    {
+        "candidate_id": "S-3", "estimand": "A", "evidence_family": "playbook",
+        "setup_id": "double_top", "side": "short", "context_predicate": None,
+        "primary_measure_key": "to_close", "primary_horizon": "to_close", "sidedness": "greater",
+        "null_spec_id": REFEREE_NULL_TOD_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
+        "rationale": (
+            "a completed reversal structure claims the session's trend has turned -- always "
+            "measurable by construction"
+        ),
+    },
+    {
+        "candidate_id": "S-4", "estimand": "B", "evidence_family": "playbook",
+        "setup_id": "range_trade", "side": "long",
+        "context_predicate": {"backing_bucket": AT_WALL},
+        "primary_measure_key": "1h", "primary_horizon": "1h", "sidedness": "greater",
+        "null_spec_id": None, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
+        "rationale": (
+            "a range bounce plays out over the traverse toward the opposite boundary -- to_close "
+            "would contaminate with post-breakout regimes"
+        ),
+    },
+    {
+        "candidate_id": "S-5", "estimand": "C", "evidence_family": "playbook",
+        "setup_id": "range_trade", "side": "long",
+        "context_predicate": {"backing_bucket": AT_WALL},
+        "primary_measure_key": "1h", "primary_horizon": "1h", "sidedness": "greater",
+        "null_spec_id": REFEREE_NULL_CONTEXT_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
+        "rationale": (
+            "the combined claim: a wall-backed bounce is priced better than chance at that time "
+            "and place"
+        ),
+    },
+)
+
+
+def _corpus_session_span_days(newest_by_date: dict[str, dict]) -> int:
+    """The recorded corpus's own calendar-day span -- earliest recorded ``session_date`` to the
+    latest, inclusive -- the denominator each shortlist candidate's own
+    ``accrual_rate_sessions_per_day`` divides by. No spec-pinned accrual-rate methodology exists
+    (``docs/referee-statistical-spec.md`` Sec7 lists only static authoring-time corpus counts, not
+    a formula); this basis -- a candidate's OWN ``n_sessions`` over the WHOLE corpus's own
+    trailing day-span -- is disclosed here, not hidden (state/assumptions.md iter-8). Zero when
+    the corpus is empty (no session dates recorded at all) -- the caller reads this as its own
+    divide-by-zero guard, never crashing (TC-2)."""
+    if not newest_by_date:
+        return 0
+    dates = sorted(newest_by_date)
+    earliest = date.fromisoformat(dates[0])
+    latest = date.fromisoformat(dates[-1])
+    return (latest - earliest).days + 1
+
+
+def _starter_context_readiness(
+    newest_by_date: dict[str, dict],
+    config_fingerprint: str,
+    *,
+    setup_id: str,
+    side: str,
+    backing_bucket: str,
+    context_resolver: BandMapResolver,
+) -> tuple[int, int]:
+    """LIVE ``(n, n_sessions)`` among ``(setup_id, side)`` occurrences at the CURRENT detector
+    basis (T-6) whose OWN entry resolves into ``backing_bucket`` -- the S-4/S-5 shortlist
+    candidates' own readiness. Walks the IDENTICAL newest-per-date, current-basis-only raw-record
+    set ``playbook_occurrence_readiness()`` already walks (never a second pooling
+    implementation), adding ONE per-signal context resolve via the referee-era's own
+    already-imported band-context primitive -- ``referee_null.resolve_occurrence_backing_bucket``
+    over a ``compute=False`` ``BandMapResolver`` (a RECORDED-band-map lookup, never a fresh
+    compute, T-8) -- the SAME primitive ``referee_adjudicate.py``'s own Estimand B/C pooling
+    (``_pool_cell_vs_complement``) already calls."""
+    live_basis = current_playbook_detector_basis()
+    n = 0
+    sessions: set[str] = set()
+    for session_date, record in newest_by_date.items():
+        if _is_stale_basis(
+            _record_detector_basis(record),
+            record["config_fingerprint"],
+            live_basis=live_basis,
+            live_config_fingerprint=config_fingerprint,
+        ):
+            continue  # T-6: pool only at the current (detector_basis, config_fingerprint)
+        for signal in record["signals"]:
+            if signal["setup_id"] != setup_id or signal["side"] != side:
+                continue
+            cell = resolve_occurrence_backing_bucket(
+                signal, signal["symbol"], _epoch_from_iso(signal["trigger_ts"]),
+                signal.get("entry"), side, context_resolver,
+            )
+            if cell == backing_bucket:
+                n += 1
+                sessions.add(session_date)
+    return n, len(sessions)
+
+
+def shortlist_response(
+    *,
+    playbook_store: PlaybookStore,
+    config_fingerprint: str,
+    bar_store: BarStore,
+    config: Config,
+) -> dict:
+    """The whole ``GET /research/desk/referee/registry/shortlist`` body (J-07): spec Sec7's five
+    PINNED candidates (``REFEREE_STARTER_FAMILY_SHORTLIST``) beside LIVE readiness computed fresh
+    on every call -- a plain read (GET never computes, T-8; the band-context lookup below is
+    ``compute=False``, a lookup over the ALREADY-RECORDED band map, never a fresh map build). n/
+    n_sessions for S-1..S-3 (estimand A, no context) reuse ``playbook_occurrence_readiness()``'s
+    existing ``per_setup_side`` pooling verbatim; S-4/S-5 (``at_wall`` context) reuse
+    ``_starter_context_readiness`` above. ``accrual_rate_sessions_per_day``/
+    ``projected_days_to_target`` never divide by zero (TC-2): both read ``0``/``None`` on an empty
+    corpus or a zero-eligible cell, and ``projected_days_to_target`` floors at ``0.0`` rather than
+    going negative once a cell already meets or exceeds its own ``target_sessions``."""
+    readiness = playbook_occurrence_readiness(playbook_store, config_fingerprint)
+    per_setup_side = {(cell["setup"], cell["side"]): cell for cell in readiness["per_setup_side"]}
+
+    records, _errors = playbook_store.list()
+    newest_by_date = _newest_per_session_date(records)
+    corpus_span_days = _corpus_session_span_days(newest_by_date)
+    context_resolver = BandMapResolver(bar_store, config, compute=False)
+
+    candidates = []
+    for spec in REFEREE_STARTER_FAMILY_SHORTLIST:
+        context_predicate = spec["context_predicate"]
+        if context_predicate is None:
+            cell = per_setup_side.get((spec["setup_id"], spec["side"]))
+            n = cell["n"] if cell is not None else 0
+            n_sessions = cell["n_sessions"] if cell is not None else 0
+        else:
+            n, n_sessions = _starter_context_readiness(
+                newest_by_date, config_fingerprint,
+                setup_id=spec["setup_id"], side=spec["side"],
+                backing_bucket=context_predicate["backing_bucket"],
+                context_resolver=context_resolver,
+            )
+        accrual_rate = (n_sessions / corpus_span_days) if corpus_span_days > 0 else 0.0
+        projected_days = (
+            max(0.0, (spec["target_sessions"] - n_sessions) / accrual_rate)
+            if accrual_rate > 0 else None
+        )
+        candidates.append(
+            {
+                "candidate_id": spec["candidate_id"],
+                "estimand": spec["estimand"],
+                "evidence_family": spec["evidence_family"],
+                "setup_id": spec["setup_id"],
+                "side": spec["side"],
+                "context_predicate": context_predicate,
+                "primary_measure_key": spec["primary_measure_key"],
+                "primary_horizon": spec["primary_horizon"],
+                "sidedness": spec["sidedness"],
+                "null_spec_id": spec["null_spec_id"],
+                "test_spec_id": spec["test_spec_id"],
+                "rationale": spec["rationale"],
+                "n": n,
+                "n_sessions": n_sessions,
+                "target_sessions": spec["target_sessions"],
+                "min_occurrences": spec["min_occurrences"],
+                "accrual_rate_sessions_per_day": accrual_rate,
+                "projected_days_to_target": projected_days,
+            }
+        )
+    return {"candidates": candidates}
+
+
 # --- The CLI (register / withdraw) --------------------------------------------------------------------
 
 
diff --git a/apps/backend/app/research/referee_routes.py b/apps/backend/app/research/referee_routes.py
index 501ea13..1749e88 100644
--- a/apps/backend/app/research/referee_routes.py
+++ b/apps/backend/app/research/referee_routes.py
@@ -63,6 +63,7 @@ from .referee_registry import (
     register_hypothesis,
     registry_response,
     resolve_referee_registry_dir,
+    shortlist_response,
 )
 from .routes import ResearchRegistry, get_bar_store, get_dataset_store, get_registry
 
@@ -271,6 +272,22 @@ def get_referee_registry(
     )
 
 
+@router.get("/registry/shortlist")
+def get_referee_registry_shortlist(
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+    bar_store: BarStore = Depends(get_bar_store),
+) -> dict:
+    """J-07's starter-family shortlist: spec Sec7's five pre-registered candidates (S-1..S-5)
+    beside LIVE readiness (a plain read; GET never computes, T-8 -- the band-context lookup
+    behind S-4/S-5 is ``compute=False``, over the ALREADY-RECORDED band map)."""
+    return shortlist_response(
+        playbook_store=playbook_store,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store,
+        config=CONFIG,
+    )
+
+
 class RefereeHypothesisRegistrationRequest(BaseModel):
     """Body for ``POST /research/desk/referee/registry/hypotheses`` — every field optional at the
     pydantic level (``register_hypothesis`` itself is the ONE place that validates presence/
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index f6593d9..63fd056 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -245,6 +245,12 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|breach\.(?:breached_count|total_count)"
     r"|basis\.(?:n_records)"
     r"|(?:compute|tick|snapshot)\.(?:signals_done|signals_total)"
+    # goal-referee-iter-8 (J-07): the Referee Registry section's own served numerics -- a
+    # shortlist candidate's live readiness (never divide/subtract these client-side; the backend
+    # already served accrual_rate_sessions_per_day/projected_days_to_target as computed numbers)
+    # and a registered hypothesis's discovery count (never combined with its accrual siblings).
+    r"|candidate\.(?:n|n_sessions|accrual_rate_sessions_per_day|projected_days_to_target)"
+    r"|hyp\.discovery\.(?:n|n_sessions)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -447,6 +453,37 @@ def test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmeti
     assert _PRICE_ARITHMETIC_PATTERN.search("const label = `${basis.n_records} records`;") is None
 
 
+def test_desk_page_price_arithmetic_guard_catches_referee_shortlist_and_discovery_field_arithmetic():
+    """goal-referee-iter-8 (J-07) counter-test: the extended guard catches arithmetic on the new
+    Referee Registry section's own `candidate.*` (shortlist readiness) and `hyp.discovery.*`
+    bindings -- these numbers are computed once, on the backend (referee_registry.py's
+    `shortlist_response()`/`_hypothesis_discovery()`), and must never be re-derived client-side."""
+    seeded_days = (
+        "const days = (candidate.target_sessions - candidate.n_sessions) / "
+        "candidate.accrual_rate_sessions_per_day;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_days) is not None
+
+    seeded_n_diff = "const untested = candidate.n - candidate.n_sessions;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_n_diff) is not None
+
+    seeded_projected = "const soon = candidate.projected_days_to_target * 2;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_projected) is not None
+
+    seeded_discovery_total = "const total = hyp.discovery.n + hyp.accrual.informative_post_boundary_sessions;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_discovery_total) is not None
+
+    seeded_discovery_sessions = "const ratio = hyp.discovery.n_sessions / hyp.discovery.n;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_discovery_sessions) is not None
+
+    # And the pattern does NOT over-match: rendering the two numbers side by side as plain text
+    # (never an arithmetic operator between the field accesses themselves) stays clean -- exactly
+    # the SAME "X / Y" display idiom this component actually uses.
+    assert _PRICE_ARITHMETIC_PATTERN.search(
+        "const label = `${hyp.discovery.n} / ${hyp.discovery.n_sessions}`;"
+    ) is None
+
+
 # goal-playbook-iter-4 audit (F1): `base_lows_ascending` is ONE served field name carrying the
 # direction-appropriate triangle check underneath (non-decreasing LOWS for `jbe`, non-increasing
 # HIGHS for `dbi` -- see `desk_playbook_detect._base_lows_ascending`). The continuation geometry
diff --git a/apps/backend/tests/test_referee_adjudicate.py b/apps/backend/tests/test_referee_adjudicate.py
index a6480e9..1bc9394 100644
--- a/apps/backend/tests/test_referee_adjudicate.py
+++ b/apps/backend/tests/test_referee_adjudicate.py
@@ -387,6 +387,63 @@ def test_tc9_below_target_reports_the_real_recount_never_the_registry_proxy(stor
     assert record["confirmatory_eligible"] is False
 
 
+# === iter-8 Rider 1: a failed oracle attestation must never mint a checkpoint or its snapshot =========
+
+
+def test_iter8_rider1_a_failed_attestation_never_mints_a_checkpoint_or_a_snapshot(stores, monkeypatch):
+    """iter-8 Rider 1 (evaluator-diagnosed, iteration 7): ``run_evaluation_and_record`` must never
+    mint ``role: "checkpoint"`` -- and therefore never write the hypothesis's ONE permanent
+    adjudication snapshot -- when ``attestation["passed"]`` is ``False``. Forces the SAME
+    otherwise-checkpoint-eligible fixture ``test_known_positive_corpus_round_trip_checkpoints_
+    corroborated`` uses to hit a deliberately failing oracle attestation (the module's own
+    ``run_oracle_attestation``, monkeypatched at its call site inside ``referee_adjudicate.py``).
+    The honest computed statistics (T/permutation_p/CIs) stay served regardless -- only the
+    permanent-write eligibility is gated (the write side needs the SAME gate the read side
+    (``_snapshot_fold``, via ``verify_oracle_attestation``) already carries)."""
+    _plant_known_corpus(
+        stores, "hyp-rider1", "fam-rider1", n_sessions=13, trigger_close=100.0, flat_close=102.0,
+    )
+    real_attestation = run_oracle_attestation()
+    assert real_attestation["passed"] is True  # sanity: the real attestation genuinely passes
+    failing_attestation = {**real_attestation, "passed": False}
+    monkeypatch.setattr(
+        referee_adjudicate_module, "run_oracle_attestation", lambda: failing_attestation
+    )
+
+    result = _run_eval(stores, "hyp-rider1")
+    record = result["record"]
+    assert record["confirmatory_eligible"] is True  # coverage floors WERE met
+    assert record["role"] == "pending"  # never "checkpoint" -- the write-side gate
+    assert record["attestation"]["passed"] is False
+    assert record["permutation_p"] is not None  # the honest computed stats stay served
+    assert result["snapshot"] is None
+
+    snapshots, errors = stores["snapshot_store"].list()
+    assert errors == []
+    assert snapshots == []  # no permanent record was ever minted
+
+    # A second evaluation act against the SAME (still attestation-failing) store must not reuse a
+    # phantom checkpoint either -- it dedupes on the identical evaluation_basis and still reports
+    # no snapshot.
+    second = _run_eval(stores, "hyp-rider1")
+    assert second["reused"] is True
+    assert second["record"]["role"] == "pending"
+    assert second["snapshot"] is None
+
+
+def test_iter8_rider1_a_passing_attestation_still_mints_the_checkpoint_can_fail_counter_test(stores):
+    """The can-fail companion to Rider 1's own test above: with the REAL (passing) attestation,
+    the identical fixture still checkpoints -- proving Rider 1's gate is discriminating, not a
+    blanket refusal."""
+    _plant_known_corpus(
+        stores, "hyp-rider1-ok", "fam-rider1-ok", n_sessions=13, trigger_close=100.0, flat_close=102.0,
+    )
+    result = _run_eval(stores, "hyp-rider1-ok")
+    assert result["record"]["role"] == "checkpoint"
+    assert result["snapshot"] is not None
+    assert result["snapshot"]["verdict"] == "corroborated"
+
+
 def test_tc13_an_extra_payload_field_never_influences_the_recorded_coverage(stores):
     """TC-13 (route level): a ``POST .../evaluate`` body carrying an extra
     ``post_boundary_informative_sessions`` field is ignored -- pydantic's own default
@@ -848,6 +905,62 @@ def test_tc25_zero_hypotheses_registered_returns_200_with_empty_lists(stores):
         playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
     )
     assert fold["entries"] == []
+    assert fold["integrity_errors"] == []
+
+
+# === iter-8 Rider 2: a corrupted hypothesis file is surfaced on GET /adjudications, never dropped ======
+
+
+def test_iter8_rider2_a_corrupted_hypothesis_file_is_surfaced_in_adjudications_integrity_errors(
+    stores,
+):
+    """iter-8 Rider 2 (evaluator-diagnosed, iteration 7): ``adjudications_response()`` must
+    surface ``hypothesis_store.list()``'s integrity errors the same way ``GET /registry`` already
+    does (``referee_registry.py``'s own iteration-7 Rider-2 precedent) -- a corrupted hypothesis
+    file alongside a healthy, already-checkpointed one is NAMED, not silently dropped, and the
+    healthy hypothesis's own entry still folds correctly."""
+    _plant_known_corpus(
+        stores, "hyp-rider2-ok", "fam-rider2", n_sessions=13, trigger_close=100.0, flat_close=102.0,
+    )
+    checkpoint = _run_eval(stores, "hyp-rider2-ok")
+    assert checkpoint["snapshot"]["verdict"] == "corroborated"
+
+    hypothesis_dir = stores["hypothesis_store"].root
+    (hypothesis_dir / "hypothesis-corrupt.json").write_text("not valid json at all")
+
+    fold = adjudications_response(
+        hypothesis_store=stores["hypothesis_store"], snapshot_store=stores["snapshot_store"],
+        playbook_store=stores["playbook_store"], config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    assert len(fold["entries"]) == 1  # the healthy, checkpointed hypothesis still folds
+    assert fold["entries"][0]["hypothesis_id"] == "hyp-rider2-ok"
+    assert fold["entries"][0]["verdict"] == "corroborated"
+
+    assert len(fold["integrity_errors"]) == 1
+    error = fold["integrity_errors"][0]
+    assert error["file"] == "hypothesis-corrupt.json"
+    assert "error" in error and error["error"]
+
+
+def test_get_adjudications_route_serves_integrity_errors_key_on_a_healthy_store(stores):
+    """The route-level companion (never 404/500, TC-25's own established honest-empty pattern):
+    the key exists and is an empty list on a healthy, uncorrupted store."""
+    app.dependency_overrides.clear()
+    from app.research.desk_routes import get_playbook_store
+    from app.research.referee_routes import get_referee_hypothesis_store, get_referee_snapshot_store
+
+    app.dependency_overrides[get_referee_hypothesis_store] = lambda: stores["hypothesis_store"]
+    app.dependency_overrides[get_referee_snapshot_store] = lambda: stores["snapshot_store"]
+    app.dependency_overrides[get_playbook_store] = lambda: stores["playbook_store"]
+    try:
+        with TestClient(app) as client:
+            resp = client.get("/research/desk/referee/adjudications")
+    finally:
+        app.dependency_overrides.clear()
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["integrity_errors"] == []
+    assert set(body) == {"entries", "register", "integrity_errors"}
 
 
 # === TC-26, TC-27, TC-28: authorize_promotion ==========================================================
diff --git a/apps/backend/tests/test_referee_registry.py b/apps/backend/tests/test_referee_registry.py
index b5c7fe6..ca8a921 100644
--- a/apps/backend/tests/test_referee_registry.py
+++ b/apps/backend/tests/test_referee_registry.py
@@ -20,11 +20,13 @@ from fastapi.testclient import TestClient
 import app.research.referee_registry as referee_registry_module
 from app.config import CONFIG
 from app.main import app
+from app.research.bars import BarStore
 from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
 from app.research.referee_null import REFEREE_NULL_TOD_SPEC_ID, REFEREE_TEST_PERM_SPEC_ID
 from app.research.referee_registry import (
     REFEREE_MIN_OCCURRENCES,
     REFEREE_MIN_SESSIONS,
+    REFEREE_STARTER_FAMILY_SHORTLIST,
     CertificateAlreadyRecorded,
     CertificateStore,
     ConfirmationRequired,
@@ -39,6 +41,7 @@ from app.research.referee_registry import (
     WithdrawalStore,
     register_hypothesis,
     registry_response,
+    shortlist_response,
     withdraw_hypothesis,
 )
 
@@ -100,6 +103,15 @@ def stores(tmp_path):
     return family_store, hypothesis_store, withdrawal_store, certificate_store, playbook_store
 
 
+@pytest.fixture
+def bar_store(tmp_path):
+    """A SEPARATE fixture (rather than growing ``stores``' own tuple, which every existing test in
+    this file already destructures at a fixed length) -- only the iter-8 shortlist tests need a
+    ``BarStore`` (``shortlist_response``'s S-4/S-5 band-context lookup requires one to construct a
+    ``BandMapResolver``)."""
+    return BarStore(tmp_path / "referee_bars")
+
+
 def _plant_playbook_signals(
     playbook_store: PlaybookStore, session_date: str, signals: list[dict]
 ) -> None:
@@ -415,6 +427,16 @@ def test_tc11_accrual_matches_a_hand_counted_value_over_two_distinct_setup_side_
     assert folded_cap["accrual"]["basis_current"] is True
     assert folded_jbe["accrual"]["basis_current"] is True
 
+    # iter-8 (J-07): discovery is the exact pre-boundary COMPLEMENT of accrual, over the SAME
+    # planted corpus -- 2026-06-09 is the only pre-boundary date, and it carries capitulation:long
+    # only (never jbe:long); it must never contribute to either hypothesis's accrual above.
+    assert folded_cap["discovery"] == {
+        "n": 1, "n_sessions": 1, "label": "discovery (exploratory)",
+    }
+    assert folded_jbe["discovery"] == {
+        "n": 0, "n_sessions": 0, "label": "discovery (exploratory)",
+    }
+
     assert set(response) == {
         "families", "hypotheses", "withdrawals", "certificates", "integrity_errors",
     }
@@ -587,6 +609,241 @@ def test_tc14_all_five_starter_candidates_register_cleanly_with_distinct_ids(sto
     assert families[0]["candidate_hypothesis_ids"] == ["hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5"]
 
 
+# === J-07 (iter-8): the starter-family shortlist -- GET .../registry/shortlist =========================
+#
+# spec Sec7's five PINNED module candidates beside LIVE readiness (goal.md J-07 Step 1). n/
+# n_sessions for S-1..S-3 (estimand A) reuse playbook_occurrence_readiness()'s existing
+# per_setup_side pooling; S-4/S-5 (at_wall context) reuse the referee-era's own band-context
+# primitive (referee_null.resolve_occurrence_backing_bucket) -- see
+# test_starter_context_readiness_discriminates_at_wall_from_off_wall_and_dedupes_sessions below for
+# the non-vacuous proof that the S-4/S-5 wiring genuinely discriminates.
+
+
+def test_tc1_shortlist_serves_exactly_five_pinned_candidates_with_non_negative_readiness(
+    stores, bar_store,
+):
+    _fam, _hyp, _wd, _cert, playbook_store = stores  # an EMPTY corpus -- the honest baseline
+    response = shortlist_response(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    candidates = response["candidates"]
+    assert [c["candidate_id"] for c in candidates] == ["S-1", "S-2", "S-3", "S-4", "S-5"]
+    for candidate in candidates:
+        assert candidate["n"] >= 0
+        assert candidate["n_sessions"] >= 0
+        assert candidate["accrual_rate_sessions_per_day"] >= 0
+        assert candidate["target_sessions"] == REFEREE_MIN_SESSIONS
+        assert candidate["min_occurrences"] == REFEREE_MIN_OCCURRENCES
+        assert candidate["test_spec_id"] == REFEREE_TEST_PERM_SPEC_ID
+        assert candidate["rationale"]  # a non-empty semantic sentence, per candidate
+
+    by_id = {c["candidate_id"]: c for c in candidates}
+    assert (by_id["S-1"]["estimand"], by_id["S-1"]["setup_id"], by_id["S-1"]["side"]) == (
+        "A", "capitulation", "long",
+    )
+    assert (by_id["S-2"]["estimand"], by_id["S-2"]["setup_id"], by_id["S-2"]["side"]) == (
+        "A", "jbe", "long",
+    )
+    assert (by_id["S-3"]["estimand"], by_id["S-3"]["setup_id"], by_id["S-3"]["side"]) == (
+        "A", "double_top", "short",
+    )
+    assert by_id["S-4"]["estimand"] == "B" and by_id["S-4"]["context_predicate"] == {
+        "backing_bucket": "at_wall",
+    }
+    assert by_id["S-4"]["null_spec_id"] is None  # Estimand B: no null population (spec Sec3.2)
+    assert by_id["S-5"]["estimand"] == "C" and by_id["S-5"]["null_spec_id"] == "referee-null-context-v1"
+
+    # These five are the exact SAME pinned definitions test_tc14 already registers through the
+    # write path -- proof the shortlist's own module constants and the registration fixture stay
+    # in lockstep (never two independently-drifting copies).
+    assert [c["candidate_id"] for c in REFEREE_STARTER_FAMILY_SHORTLIST] == [
+        "S-1", "S-2", "S-3", "S-4", "S-5",
+    ]
+
+
+def test_tc2_zero_jbe_long_signals_amid_a_nonempty_corpus_serves_zero_never_a_divide_by_zero(
+    stores, bar_store,
+):
+    _fam, _hyp, _wd, _cert, playbook_store = stores
+    # A nonempty corpus that carries NO jbe:long signal at all -- proves S-2's own zero reading is
+    # a genuine per-cell fact, not an artifact of an all-empty store (the iter-5 lesson: a test
+    # must exercise the regime where the assertion is actually discriminating).
+    _plant_playbook_signals(playbook_store, "2026-06-01", [_signal("capitulation", "long")])
+
+    response = shortlist_response(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    by_id = {c["candidate_id"]: c for c in response["candidates"]}
+    assert by_id["S-1"]["n"] == 1 and by_id["S-1"]["n_sessions"] == 1  # genuinely nonzero elsewhere
+
+    s2 = by_id["S-2"]
+    assert s2["setup_id"] == "jbe" and s2["side"] == "long"
+    assert s2["n"] == 0
+    assert s2["n_sessions"] == 0
+    assert s2["accrual_rate_sessions_per_day"] == 0
+    assert s2["projected_days_to_target"] is None  # never a divide-by-zero value
+
+
+def test_shortlist_projected_days_to_target_is_zero_when_already_at_or_above_target(
+    stores, bar_store,
+):
+    """A can-fail companion to TC-2: once a cell's own n_sessions already meets/exceeds its
+    target_sessions, the honest reading is zero days remaining, never a negative number."""
+    _fam, _hyp, _wd, _cert, playbook_store = stores
+    for i in range(REFEREE_MIN_SESSIONS + 3):
+        _plant_playbook_signals(
+            playbook_store, f"2026-05-{i + 1:02d}", [_signal("capitulation", "long")],
+        )
+    response = shortlist_response(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    s1 = next(c for c in response["candidates"] if c["candidate_id"] == "S-1")
+    assert s1["n_sessions"] >= s1["target_sessions"]
+    assert s1["accrual_rate_sessions_per_day"] > 0
+    assert s1["projected_days_to_target"] == 0.0
+
+
+def test_get_registry_shortlist_route_honest_state_against_a_real_empty_store(route_ctx):
+    """TC-6 (the shortlist half): against the real store, with no operator action taken, the
+    shortlist still serves 5 candidates and the registry's own hypotheses list stays empty -- the
+    honest not-yet-acted state, never fabricated."""
+    client, _tmp = route_ctx
+    resp = client.get("/research/desk/referee/registry/shortlist")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert [c["candidate_id"] for c in body["candidates"]] == ["S-1", "S-2", "S-3", "S-4", "S-5"]
+
+    registry = client.get("/research/desk/referee/registry")
+    assert registry.json()["hypotheses"] == []
+
+
+class _FakeWallResolver:
+    """The wall at [99.9, 100.1] -- prices INSIDE it (or within 70bps of it) resolve ``at_wall``,
+    prices far from it resolve ``off_wall`` (the ``test_referee_adjudicate.py``
+    ``_FakeContextResolver`` pattern, reused here verbatim -- never a second fake-resolver
+    implementation)."""
+
+    def resolve(self, symbol, as_of_epoch):
+        return {
+            "bands": [
+                {
+                    "side": "support", "class": "A", "price_low": 99.9, "price_high": 100.1,
+                    "quality_score": 1.0, "round_number": False, "member_count": 1,
+                }
+            ],
+            "basis_as_of": "2026-06-21",
+        }
+
+
+def _context_signal(*, entry: float, symbol: str) -> dict:
+    return {
+        "setup_id": "range_trade", "side": "long", "symbol": symbol,
+        "trigger_ts": _et_instant_iso(2026, 6, 21, 10, 0),  # fixed instant -- irrelevant to the fake
+        "entry": entry, "invalidation_price": entry - 0.5,
+    }
+
+
+def test_starter_context_readiness_discriminates_at_wall_from_off_wall_and_dedupes_sessions(stores):
+    """The non-vacuous proof S-4/S-5's own live readiness genuinely discriminates (not just "zero
+    everywhere"): two ``at_wall`` occurrences on the SAME session (deduping to one date), one
+    ``at_wall`` occurrence on a second session, and one ``off_wall`` occurrence that must NEVER
+    count."""
+    _fam, _hyp, _wd, _cert, playbook_store = stores
+    _plant_playbook_signals(
+        playbook_store, "2026-06-21",
+        [
+            _context_signal(entry=100.0, symbol="RTA"),   # containing the band -> at_wall
+            _context_signal(entry=99.95, symbol="RTB"),    # containing the band -> at_wall
+        ],
+    )
+    _plant_playbook_signals(
+        playbook_store, "2026-06-22", [_context_signal(entry=100.05, symbol="RTC")],  # at_wall
+    )
+    _plant_playbook_signals(
+        playbook_store, "2026-06-23", [_context_signal(entry=110.0, symbol="RTD")],  # off_wall
+    )
+    records, _errors = playbook_store.list()
+    newest_by_date = referee_registry_module._newest_per_session_date(records)
+    n, n_sessions = referee_registry_module._starter_context_readiness(
+        newest_by_date, CONFIG.config_fingerprint(),
+        setup_id="range_trade", side="long", backing_bucket="at_wall",
+        context_resolver=_FakeWallResolver(),
+    )
+    assert n == 3  # RTA, RTB, RTC -- RTD (off_wall) never counts
+    assert n_sessions == 2  # 2026-06-21 and 2026-06-22 -- the same-session pair dedupes to one date
+
+
+def test_shortlist_s4_s5_readiness_reflects_the_at_wall_context_resolve(
+    stores, bar_store, monkeypatch,
+):
+    """End-to-end wiring proof (not just the isolated helper above): ``shortlist_response()``
+    itself serves nonzero S-4/S-5 readiness when the corpus genuinely carries ``at_wall``
+    ``range_trade:long`` occurrences, by constructing a REAL ``BandMapResolver`` whose class this
+    test monkeypatches to the fake wall (the class-level substitution ``referee_adjudicate.py``'s
+    own estimand-B/C tests never needed, since those call the pooling function directly with an
+    injected resolver instead of letting it construct one)."""
+    _fam, _hyp, _wd, _cert, playbook_store = stores
+    _plant_playbook_signals(
+        playbook_store, "2026-06-21", [_context_signal(entry=100.0, symbol="RTA")],
+    )
+    monkeypatch.setattr(
+        referee_registry_module, "BandMapResolver", lambda *args, **kwargs: _FakeWallResolver()
+    )
+    response = shortlist_response(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    by_id = {c["candidate_id"]: c for c in response["candidates"]}
+    assert by_id["S-4"]["n"] == 1 and by_id["S-4"]["n_sessions"] == 1
+    assert by_id["S-5"]["n"] == 1 and by_id["S-5"]["n_sessions"] == 1
+
+
+# === TC-9 / TC-10 (iter-8): the write path stays generic; discovery is boundary-gated on
+# session_date, never recorded_at ======================================================================
+
+
+def test_tc9_a_non_shortlist_setup_side_still_registers_the_write_path_stays_generic(route_ctx):
+    """TC-9: a hypothesis payload for a setup/side combination NOT among S-1..S-5 (``dbi:short``,
+    estimand A, per the plan's own example) registers successfully -- the write path accepts any
+    valid hypothesis, never only the five shortlist candidates."""
+    client, _tmp = route_ctx
+    payload = _estimand_a_payload("hyp-dbi-short", "fam-dbi-short", setup_id="dbi", side="short")
+    resp = client.post(
+        "/research/desk/referee/registry/hypotheses", json={**payload, "confirm": True}
+    )
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["setup_id"] == "dbi" and body["side"] == "short"
+
+
+def test_tc10_a_deep_backfilled_pre_boundary_record_lands_in_discovery_never_accrual(stores):
+    """TC-10: a deep-backfilled record for a ``session_date`` before the boundary, recorded
+    (written to disk) AFTER registration, contributes to ``discovery.n_sessions`` -- never to
+    ``accrual.informative_post_boundary_sessions`` -- proving ``session_date``, not
+    ``recorded_at``, gates the boundary. Also covers the boundary-INCLUSIVE edge: a record dated
+    exactly ON the boundary date itself is discovery too (accrual admits only strictly-after)."""
+    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
+    payload = _estimand_a_payload("hyp-tc10-disc", "fam-tc10-disc")  # boundary == _BOUNDARY
+    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+
+    _plant_playbook_signals(playbook_store, "2026-05-01", [_signal("capitulation", "long")])  # deep-backfilled
+    _plant_playbook_signals(playbook_store, _BOUNDARY, [_signal("capitulation", "long")])  # ON the boundary
+    _plant_playbook_signals(playbook_store, "2026-06-11", [_signal("capitulation", "long")])  # post-boundary
+
+    response = registry_response(
+        family_store=family_store, hypothesis_store=hypothesis_store,
+        withdrawal_store=withdrawal_store, certificate_store=cert_store,
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    folded = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc10-disc")
+    assert folded["discovery"]["n_sessions"] == 2  # 2026-05-01 and _BOUNDARY itself
+    assert folded["discovery"]["n"] == 2
+    assert folded["accrual"]["informative_post_boundary_sessions"] == 1  # 2026-06-11 only
+
+
 # === family/hypothesis coupling: consistency + "no candidate joins retroactively" =====================
 
 
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index e62d2ac..29c2c1b 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -43,6 +43,9 @@ import {
   triggerDeskScreenCompute,
   triggerDeskTopupCompute,
   triggerDeskUniverseFetch,
+  fetchRefereeRegistry,
+  fetchRefereeShortlist,
+  postRefereeRegistryHypothesis,
 } from "@/lib/api";
 import type {
   DeskDeepBackfillComputeSnapshot,
@@ -106,6 +109,10 @@ import type {
   DeskTopupRun,
   DeskTopupRunMeta,
   DeskTopupRunsListResult,
+  RefereeHypothesis,
+  RefereeRegistryResponse,
+  RefereeShortlistCandidate,
+  RefereeShortlistResponse,
 } from "@/lib/types";
 import { Metric, Panel } from "@/components/Panel";
 import {
@@ -333,7 +340,8 @@ type DeskCollapsibleSection =
   | "screenRuns"
   | "screenComparison"
   | "provenance"
-  | "playbookEvidence";
+  | "playbookEvidence"
+  | "refereeRegistry";
 // DESK-COLLAPSED-END
 
 const PRIMARY_BUTTON_CLASS =
@@ -342,6 +350,17 @@ const PRIMARY_BUTTON_CLASS =
 const CANCEL_BUTTON_CLASS =
   "mt-1 rounded-md border border-slate-700 bg-transparent px-2.5 py-1 text-xs font-medium text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-red-500 disabled:cursor-not-allowed disabled:opacity-50";
 
+// goal-referee-iter-8 (J-07): the starter family's own registration-mechanics constants -- the
+// shortlist response (RefereeShortlistCandidate) carries every OTHER field a registration payload
+// needs verbatim, but not these three (spec Sec7's shortlist describes research QUESTIONS, not
+// registration mechanics). `family_q` mirrors REFEREE_DEFAULT_Q (0.10,
+// docs/referee-statistical-spec.md Sec1) -- the same value test_referee_registry.py's own
+// `_starter_family_payloads()` fixture already uses for all five candidates. The candidate id SET
+// itself is never hard-coded here — it is read live off the fetched shortlist's own
+// `candidate_id`s at submit time (goal.md J-07 Step 2: "no hard-coded hypothesis set").
+const REFEREE_STARTER_FAMILY_ID = "referee-starter-family";
+const REFEREE_STARTER_FAMILY_Q = 0.1;
+
 // The as-of day text fields (forward-test era) — mirrors structure/page.tsx's own `INPUT_CLASS`
 // shape (each page owns its own copy of this tiny constant per this project's established
 // convention), narrowed and centered for a bare yyyy-MM-dd value.
@@ -4664,6 +4683,247 @@ function PlaybookEvidenceSection({
   );
 }
 
+// goal-referee-iter-8 (J-07): the Referee Registry section -- Era 6's FIRST Referee UI slice. The
+// shortlist (spec Sec7's five pinned candidates + live readiness) sits above the registered-
+// hypotheses table, matching runs/goal-session-referee/state/blueprint.md's own pre-planned
+// Information Architecture row for this journey. Plain dense tables throughout (this house style
+// is explicitly "tables and text, no dashboard cards/gauges") -- no client-side arithmetic on any
+// served numeric field (test_desk_ui_guards.py's extended _PRICE_ARITHMETIC_FIELDS covers every
+// one this component reads).
+function RefereeRegistrySection({
+  shortlistResult,
+  registryResult,
+  selectedCandidateId,
+  onSelect,
+  onCancel,
+  onConfirm,
+  registering,
+  registerError,
+}: {
+  shortlistResult: { ok: boolean; data: RefereeShortlistResponse | null; error?: string } | null;
+  registryResult: { ok: boolean; data: RefereeRegistryResponse | null; error?: string } | null;
+  selectedCandidateId: string | null;
+  onSelect: (candidateId: string) => void;
+  onCancel: () => void;
+  onConfirm: (candidate: RefereeShortlistCandidate) => void;
+  registering: boolean;
+  registerError: string | null;
+}) {
+  if (shortlistResult === null || registryResult === null) {
+    return <LoadingPanel testid="referee-registry-loading" />;
+  }
+  if (!shortlistResult.ok || shortlistResult.data === null) {
+    return (
+      <UnavailablePanel
+        testid="referee-shortlist-unavailable"
+        message={shortlistResult.error ?? "The starter-family shortlist could not be loaded."}
+      />
+    );
+  }
+  const shortlist = shortlistResult.data;
+  const registeredIds = new Set(
+    registryResult.ok && registryResult.data
+      ? registryResult.data.hypotheses.map((h) => h.hypothesis_id)
+      : [],
+  );
+  const selectedCandidate =
+    shortlist.candidates.find((c) => c.candidate_id === selectedCandidateId) ?? null;
+
+  return (
+    <div data-testid="referee-registry-section">
+      <p className="mb-3 text-xs text-slate-500">
+        Spec-pinned starter-family candidates (docs/referee-statistical-spec.md §7) beside their
+        live sample-size readiness. Registering one writes a permanent, boundary-stamped
+        hypothesis — historical observations before that boundary are discovery, never
+        confirmation.
+      </p>
+      <div className="overflow-x-auto">
+        <table
+          data-testid="referee-shortlist-table"
+          className="w-full min-w-[980px] border-collapse text-xs"
+        >
+          <thead>
+            <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-500">
+              <th className="px-1.5 py-1 text-left">Candidate</th>
+              <th className="px-1.5 py-1 text-left">Estimand</th>
+              <th className="px-1.5 py-1 text-left">Setup / Side</th>
+              <th className="px-1.5 py-1 text-left">Primary</th>
+              <th className="px-1.5 py-1 text-left">Rationale</th>
+              <th className="px-1.5 py-1 text-right">n</th>
+              <th className="px-1.5 py-1 text-right">Sessions</th>
+              <th className="px-1.5 py-1 text-right">Accrual / day</th>
+              <th className="px-1.5 py-1 text-right">Projected days</th>
+              <th className="px-1.5 py-1 text-center">Action</th>
+            </tr>
+          </thead>
+          <tbody>
+            {shortlist.candidates.map((candidate) => {
+              const alreadyRegistered = registeredIds.has(candidate.candidate_id);
+              return (
+                <tr
+                  key={candidate.candidate_id}
+                  data-testid={`referee-shortlist-row-${candidate.candidate_id}`}
+                  className="border-b border-slate-900"
+                >
+                  <td className="px-1.5 py-1.5 font-mono text-slate-300">{candidate.candidate_id}</td>
+                  <td className="px-1.5 py-1.5 text-slate-400">{candidate.estimand}</td>
+                  <td className="px-1.5 py-1.5 text-slate-400">
+                    {candidate.setup_id}:{candidate.side}
+                    {candidate.context_predicate
+                      ? ` (${candidate.context_predicate.backing_bucket})`
+                      : ""}
+                  </td>
+                  <td className="px-1.5 py-1.5 text-slate-400">{candidate.primary_horizon}</td>
+                  <td className="px-1.5 py-1.5 text-slate-500">{candidate.rationale}</td>
+                  <td className="px-1.5 py-1.5 text-right font-mono text-slate-300">{candidate.n}</td>
+                  <td className="px-1.5 py-1.5 text-right font-mono text-slate-300">
+                    {candidate.n_sessions}
+                  </td>
+                  <td className="px-1.5 py-1.5 text-right font-mono text-slate-300">
+                    {candidate.accrual_rate_sessions_per_day.toFixed(2)}
+                  </td>
+                  <td className="px-1.5 py-1.5 text-right font-mono text-slate-300">
+                    {candidate.projected_days_to_target === null
+                      ? "—"
+                      : candidate.projected_days_to_target.toFixed(0)}
+                  </td>
+                  <td className="px-1.5 py-1.5 text-center">
+                    <button
+                      type="button"
+                      data-testid={`referee-shortlist-select-${candidate.candidate_id}`}
+                      onClick={() => onSelect(candidate.candidate_id)}
+                      disabled={alreadyRegistered}
+                      className={PRIMARY_BUTTON_CLASS}
+                    >
+                      {alreadyRegistered ? "Registered" : "Select"}
+                    </button>
+                  </td>
+                </tr>
+              );
+            })}
+          </tbody>
+        </table>
+      </div>
+
+      {selectedCandidate && (
+        <div
+          data-testid="referee-registration-confirm-panel"
+          className="mt-3 rounded-md border border-slate-700 bg-slate-900/60 p-3"
+        >
+          <p className="text-xs text-slate-300">
+            Register <span className="font-mono">{selectedCandidate.candidate_id}</span> (
+            {selectedCandidate.setup_id}:{selectedCandidate.side}, Estimand{" "}
+            {selectedCandidate.estimand})? This records a permanent, boundary-stamped hypothesis —
+            the boundary is stamped at registration time and can never move.
+          </p>
+          <div className="mt-2 flex items-center gap-2">
+            <button
+              type="button"
+              data-testid="referee-registration-confirm-button"
+              onClick={() => onConfirm(selectedCandidate)}
+              disabled={registering}
+              className={PRIMARY_BUTTON_CLASS}
+            >
+              {registering ? "Registering…" : "Confirm Registration"}
+            </button>
+            <button
+              type="button"
+              data-testid="referee-registration-cancel-button"
+              onClick={onCancel}
+              disabled={registering}
+              className={CANCEL_BUTTON_CLASS}
+            >
+              Cancel
+            </button>
+          </div>
+          {registerError && (
+            <p data-testid="referee-registration-error" className="mt-2 text-xs text-red-300">
+              {registerError}
+            </p>
+          )}
+        </div>
+      )}
+
+      <div className="mt-4 border-t border-slate-800 pt-4">
+        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
+          Registered Hypotheses
+        </h3>
+        <RefereeHypothesesTable registryResult={registryResult} />
+      </div>
+    </div>
+  );
+}
+
+function RefereeHypothesesTable({
+  registryResult,
+}: {
+  registryResult: { ok: boolean; data: RefereeRegistryResponse | null; error?: string } | null;
+}) {
+  if (!registryResult || !registryResult.ok || registryResult.data === null) {
+    return (
+      <UnavailablePanel
+        testid="referee-hypotheses-unavailable"
+        message={registryResult?.error ?? "The referee registry could not be loaded."}
+      />
+    );
+  }
+  const hypotheses = registryResult.data.hypotheses;
+  if (hypotheses.length === 0) {
+    return <EmptyState testid="referee-hypotheses-empty" title="No hypotheses registered." />;
+  }
+  return (
+    <div className="overflow-x-auto">
+      <table
+        data-testid="referee-hypotheses-table"
+        className="w-full min-w-[900px] border-collapse text-xs"
+      >
+        <thead>
+          <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-500">
+            <th className="px-1.5 py-1 text-left">Hypothesis</th>
+            <th className="px-1.5 py-1 text-left">Setup / Side</th>
+            <th className="px-1.5 py-1 text-left">Boundary</th>
+            <th className="px-1.5 py-1 text-left">Origin</th>
+            <th className="px-1.5 py-1 text-left">Status</th>
+            <th className="px-1.5 py-1 text-right">Accrual</th>
+            <th className="px-1.5 py-1 text-right">Discovery</th>
+          </tr>
+        </thead>
+        <tbody>
+          {hypotheses.map((hyp) => (
+            <tr
+              key={hyp.hypothesis_id}
+              data-testid={`referee-hypotheses-row-${hyp.hypothesis_id}`}
+              className="border-b border-slate-900"
+            >
+              <td className="px-1.5 py-1.5 font-mono text-slate-300">{hyp.hypothesis_id}</td>
+              <td className="px-1.5 py-1.5 text-slate-400">
+                {hyp.setup_id}:{hyp.side}
+              </td>
+              <td className="px-1.5 py-1.5 font-mono text-slate-400">
+                {hyp.confirmation_start_boundary}
+              </td>
+              <td className="px-1.5 py-1.5 text-slate-500">{hyp.origin}</td>
+              <td className="px-1.5 py-1.5 text-slate-400">{hyp.status}</td>
+              <td className="px-1.5 py-1.5 text-right font-mono text-slate-300">
+                {hyp.accrual.informative_post_boundary_sessions} / {hyp.accrual.target_sessions}
+              </td>
+              <td
+                className="px-1.5 py-1.5 text-right text-slate-500"
+                data-testid={`referee-discovery-${hyp.hypothesis_id}`}
+              >
+                <span className="font-mono text-slate-400">
+                  {hyp.discovery.n} / {hyp.discovery.n_sessions}
+                </span>{" "}
+                <span className="italic">{hyp.discovery.label}</span>
+              </td>
+            </tr>
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
 // era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
 // operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
 // many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
@@ -7439,6 +7699,24 @@ export default function DeskPage() {
     error?: string;
   } | null>(null);
 
+  // goal-referee-iter-8 (J-07): the Referee Registry section's own state — two independent
+  // deferred reads (shortlist + registry) issued together on first expand (T-8: GETs never
+  // compute), plus the select -> confirm -> submit registration flow's own local state. No compute
+  // manager, no poll — the registration act is a single POST, resolved synchronously.
+  const [refereeShortlistResult, setRefereeShortlistResult] = useState<{
+    ok: boolean;
+    data: RefereeShortlistResponse | null;
+    error?: string;
+  } | null>(null);
+  const [refereeRegistryResult, setRefereeRegistryResult] = useState<{
+    ok: boolean;
+    data: RefereeRegistryResponse | null;
+    error?: string;
+  } | null>(null);
+  const [refereeSelectedCandidateId, setRefereeSelectedCandidateId] = useState<string | null>(null);
+  const [refereeRegistering, setRefereeRegistering] = useState(false);
+  const [refereeRegisterError, setRefereeRegisterError] = useState<string | null>(null);
+
   // --- the six collapsed sections (see the DESK-COLLAPSED block at the top of this file) ---------
   // Which are currently open. A Set keyed by section, mirroring `PlaybookSummaryView`'s own
   // `expandedPools` — nothing outside this component reads it, and it is deliberately NOT
@@ -7474,7 +7752,48 @@ export default function DeskPage() {
       fetchDeskReconcileRuns().then(setReconcileRunsResult);
     } else if (section === "playbookEvidence") {
       fetchDeskPlaybookEvidence().then(setEvidenceResult);
+    } else if (section === "refereeRegistry") {
+      fetchRefereeShortlist().then(setRefereeShortlistResult);
+      fetchRefereeRegistry().then(setRefereeRegistryResult);
+    }
+  }
+
+  // goal-referee-iter-8 (J-07): the registration act -- a plain async handler (never an effect;
+  // this page pins an exact effect census, test_desk_refresh_chain_guard.py). Submits the
+  // candidate's OWN fields verbatim (never hand-typed or re-derived) plus the caller's own family
+  // framing; on success, re-fetches the registry so the new row renders complete with its
+  // status/accrual/discovery fold additions (which the POST response itself does not carry).
+  async function handleRegisterRefereeCandidate(candidate: RefereeShortlistCandidate) {
+    const shortlist = refereeShortlistResult?.data;
+    if (!shortlist) return;
+    setRefereeRegistering(true);
+    setRefereeRegisterError(null);
+    const result = await postRefereeRegistryHypothesis({
+      confirm: true,
+      hypothesis_id: candidate.candidate_id,
+      family_id: REFEREE_STARTER_FAMILY_ID,
+      family_q: REFEREE_STARTER_FAMILY_Q,
+      family_candidate_hypothesis_ids: shortlist.candidates.map((c) => c.candidate_id),
+      evidence_family: candidate.evidence_family,
+      estimand: candidate.estimand,
+      setup_id: candidate.setup_id,
+      side: candidate.side,
+      context_predicate: candidate.context_predicate,
+      primary_measure_key: candidate.primary_measure_key,
+      primary_horizon: candidate.primary_horizon,
+      sidedness: candidate.sidedness,
+      null_spec_id: candidate.null_spec_id,
+      test_spec_id: candidate.test_spec_id,
+      target_sessions: candidate.target_sessions,
+      min_occurrences: candidate.min_occurrences,
+    });
+    setRefereeRegistering(false);
+    if (!result.ok) {
+      setRefereeRegisterError(result.error ?? "The hypothesis could not be registered.");
+      return;
     }
+    setRefereeSelectedCandidateId(null);
+    fetchRefereeRegistry().then(setRefereeRegistryResult);
   }
 
   // The chained refresh (see the REFRESH-CHAIN block above). `refreshChain` is plain state and is
@@ -9269,6 +9588,34 @@ export default function DeskPage() {
             <PlaybookEvidenceSection result={evidenceResult} />
           </CollapsibleSection>
         </section>
+
+        {/* goal-referee-iter-8 (J-07): the Referee Registry section -- Era 6's FIRST Referee UI
+            slice, rendered directly BELOW the shipped Playbook Evidence section above (the current
+            last section) -- runs/goal-session-referee/state/blueprint.md's own pre-planned
+            "Referee Registry" slot. New data-testids only (T-11); no shipped section, column, or
+            behavior changes anywhere else on this page. */}
+        <section aria-label="Referee Registry" className="mt-6">
+          <CollapsibleSection
+            id="refereeRegistry"
+            title="Referee Registry"
+            open={expandedSections.has("refereeRegistry")}
+            onToggle={() => toggleSection("refereeRegistry")}
+          >
+            <RefereeRegistrySection
+              shortlistResult={refereeShortlistResult}
+              registryResult={refereeRegistryResult}
+              selectedCandidateId={refereeSelectedCandidateId}
+              onSelect={setRefereeSelectedCandidateId}
+              onCancel={() => {
+                setRefereeSelectedCandidateId(null);
+                setRefereeRegisterError(null);
... [diff_bound] apps/frontend/app/desk/page.tsx: 10 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 2e08dc4..25eca23 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -41,6 +41,10 @@ import type {
   PnlLedger,
   ProfilesPayload,
   RecordBarSeriesResult,
+  RefereeHypothesis,
+  RefereeHypothesisRegistrationPayload,
+  RefereeRegistryResponse,
+  RefereeShortlistResponse,
   ResearchTaxonomy,
   SetupDetailResult,
   SetupsListResult,
@@ -2051,3 +2055,89 @@ export async function fetchDeskPlaybookEvidence(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// --- Era 6 "The Referee" (goal-referee-iter-8, J-07) -- the FIRST-EVER frontend bindings for any
+// referee endpoint. Every function below mirrors the established `{ok, data, error?}` shape and
+// `detail`-surfacing convention every other function in this file already uses.
+
+// GET /research/desk/referee/registry/shortlist -- spec Sec7's five pre-registered starter-family
+// candidates beside LIVE readiness, served VERBATIM (no client-side arithmetic anywhere downstream
+// — every number the Referee Registry section renders is a straight pass-through of this body). A
+// plain read (T-8: GETs never compute) — the band-context lookup behind S-4/S-5 is a lookup over
+// the already-recorded band map, never a fresh compute.
+export async function fetchRefereeShortlist(): Promise<{
+  ok: boolean;
+  data: RefereeShortlistResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/registry/shortlist`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as RefereeShortlistResponse };
+    }
+    let error = "The starter-family shortlist could not be loaded.";
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
+// GET /research/desk/referee/registry — families/hypotheses (each folded with status/accrual/
+// discovery)/withdrawals/certificates/integrity_errors, served VERBATIM.
+export async function fetchRefereeRegistry(): Promise<{
+  ok: boolean;
+  data: RefereeRegistryResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/registry`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as RefereeRegistryResponse };
+    }
+    let error = "The referee registry could not be loaded.";
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
+// POST /research/desk/referee/registry/hypotheses — the real registration act (goal.md J-07 Step
+// 3): registers ONE hypothesis (through its family, create-if-absent) only when `confirm: true`.
+// The backend's 422 (malformed / unrecognised spec id / retroactive boundary) and 409 (duplicate
+// family_id/hypothesis_id) `detail` are surfaced VERBATIM, never a client-fabricated message.
+export async function postRefereeRegistryHypothesis(
+  payload: RefereeHypothesisRegistrationPayload,
+): Promise<{ ok: boolean; data: RefereeHypothesis | null; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/registry/hypotheses`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify(payload),
+    });
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as RefereeHypothesis };
+    }
+    let error = "The hypothesis could not be registered.";
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
index cb5d9d1..9ed44db 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2116,3 +2116,141 @@ export interface DeskUniverseSnapshotMeta {
   members: string[];
   raw_members: Record<string, string>;
 }
+
+// --- Era 6 "The Referee" (goal-referee-iter-8, J-07) -- the FIRST Referee UI slice. Nothing
+// referee-related existed in this file before this iteration. Every field below is served
+// VERBATIM by its owning backend fold (referee_registry.py) -- no client-side arithmetic on any
+// of them (test_desk_ui_guards.py's extended _PRICE_ARITHMETIC_FIELDS covers the ones this
+// iteration's JSX actually reads).
+
+export type RefereeEstimand = "A" | "B" | "C";
+export type RefereeSidedness = "greater" | "less" | "two-sided";
+export type RefereeEvidenceFamily = "playbook" | "strategy";
+export type RefereeSide = "long" | "short";
+
+export interface RefereeContextPredicate {
+  backing_bucket: string;
+}
+
+// GET /research/desk/referee/registry/shortlist -- spec Sec7's five pre-registered candidates
+// (S-1..S-5, pinned module constants on the backend) beside LIVE sample-size readiness.
+export interface RefereeShortlistCandidate {
+  candidate_id: string;
+  estimand: RefereeEstimand;
+  evidence_family: RefereeEvidenceFamily;
+  setup_id: string;
+  side: RefereeSide;
+  context_predicate: RefereeContextPredicate | null;
+  primary_measure_key: string;
+  primary_horizon: string;
+  sidedness: RefereeSidedness;
+  null_spec_id: string | null;
+  test_spec_id: string;
+  rationale: string;
+  n: number;
+  n_sessions: number;
+  target_sessions: number;
+  min_occurrences: number;
+  accrual_rate_sessions_per_day: number;
+  // `null` only when `accrual_rate_sessions_per_day` is 0 -- never a divide-by-zero value.
+  projected_days_to_target: number | null;
+}
+
+export interface RefereeShortlistResponse {
+  candidates: RefereeShortlistCandidate[];
+}
+
+// The read-side fold additions GET /research/desk/referee/registry adds to every hypothesis
+// entry -- never persisted on the record itself.
+export interface RefereeAccrual {
+  informative_post_boundary_sessions: number;
+  target_sessions: number;
+  is_proxy: boolean;
+  basis_current: boolean;
+}
+
+// The `discovery (exploratory)` block (goal-referee-iter-8, J-07 Step 4) -- pre-boundary
+// historical observations in the hypothesis's own cell, visibly distinct from `accrual`. NEVER a
+// confirmatory count (the historical atlas is exploratory forever).
+export interface RefereeDiscovery {
+  n: number;
+  n_sessions: number;
+  label: string;
+}
+
+export interface RefereeHypothesis {
+  hypothesis_id: string;
+  family_id: string;
+  registered_at: string;
+  evidence_family: RefereeEvidenceFamily;
+  estimand: RefereeEstimand;
+  setup_id: string;
+  side: RefereeSide;
+  context_predicate: RefereeContextPredicate | null;
+  primary_measure_key: string;
+  primary_horizon: string;
+  sidedness: RefereeSidedness;
+  null_spec_id: string | null;
+  test_spec_id: string;
+  detector_basis: string | null;
+  context_algorithm_version: string | null;
+  confirmation_start_boundary: string;
+  target_sessions: number;
+  min_occurrences: number;
+  origin: string;
+  status: "active" | "withdrawn";
+  accrual: RefereeAccrual;
+  discovery: RefereeDiscovery;
+}
+
+export interface RefereeFamily {
+  family_id: string;
+  q: number;
+  candidate_hypothesis_ids: string[];
+  registered_at: string;
+}
+
+export interface RefereeWithdrawal {
+  hypothesis_id: string;
+  withdrawn_at: string;
+  reason: string | null;
+}
+
+export interface RefereeIntegrityError {
+  store: string;
+  file: string;
+  error: string;
+}
+
+// GET /research/desk/referee/registry -- the pinned five-key registry fold, served verbatim.
+export interface RefereeRegistryResponse {
+  families: RefereeFamily[];
+  hypotheses: RefereeHypothesis[];
+  withdrawals: RefereeWithdrawal[];
+  certificates: unknown[];
+  integrity_errors: RefereeIntegrityError[];
+}
+
+// POST /research/desk/referee/registry/hypotheses -- the real registration act's own request
+// body. `confirm: true` is the explicit-confirmation-required gate every write on this page
+// carries; the rest are the candidate's OWN fields, read verbatim off a shortlist entry (never
+// hand-typed) plus the caller's own family framing.
+export interface RefereeHypothesisRegistrationPayload {
+  confirm: true;
+  hypothesis_id: string;
+  family_id: string;
+  family_q: number;
+  family_candidate_hypothesis_ids: string[];
+  evidence_family: RefereeEvidenceFamily;
+  estimand: RefereeEstimand;
+  setup_id: string;
+  side: RefereeSide;
+  context_predicate: RefereeContextPredicate | null;
+  primary_measure_key: string;
+  primary_horizon: string;
+  sidedness: RefereeSidedness;
+  null_spec_id: string | null;
+  test_spec_id: string;
+  target_sessions: number;
+  min_occurrences: number;
+}
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-referee/state/assumptions.md | 47 ++++++++++++++++++++++++++
 runs/goal-session-referee/telemetry.jsonl      |  8 +++++
 runs/goal-session-referee/trace/trace.jsonl    |  2 ++
 3 files changed, 57 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
