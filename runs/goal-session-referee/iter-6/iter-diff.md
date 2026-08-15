# Iteration diff (bounded)

Files changed: 6. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/referee_registry.py` (560 lines not shown)
- `apps/backend/tests/test_referee_registry.py` (429 lines not shown)

```diff
diff --git a/apps/backend/app/research/referee_null.py b/apps/backend/app/research/referee_null.py
index c5c2b13..3828e0a 100644
--- a/apps/backend/app/research/referee_null.py
+++ b/apps/backend/app/research/referee_null.py
@@ -529,8 +529,15 @@ def build_null_record(
             # substitution" (spec Sec4.2) -- an unresolvable map means NO candidate can be
             # VERIFIED to satisfy the predicate, so the honest eligible population is empty, not a
             # fallback to the unfiltered ToD population.
+            #
+            # iter-6 rider (reviewer NOTE carried from iteration 5): when `tod_eligible_count == 0`
+            # but `map_result` WAS resolved, zero candidates were even CHECKED against the
+            # predicate -- `None` ("nothing measurable") is the honest reading, not `0.0` (which
+            # implies a measured 0% match rate over a real, non-empty candidate population). The
+            # genuine `len(matched) / tod_eligible_count == 0.0` case (real candidates checked,
+            # zero matched) is unaffected -- it stays in the `else` branch below, untouched.
             eligible_positions = []
-            backing_rate = None if map_result is None else 0.0
+            backing_rate = None
         else:
             matched: list[int] = []
             for idx in tod_eligible:
diff --git a/apps/backend/app/research/referee_routes.py b/apps/backend/app/research/referee_routes.py
index 3d1d614..44fcb84 100644
--- a/apps/backend/app/research/referee_routes.py
+++ b/apps/backend/app/research/referee_routes.py
@@ -23,6 +23,8 @@ from __future__ import annotations
 from fastapi import APIRouter, Depends, HTTPException
 from pydantic import BaseModel
 
+from typing import Optional
+
 from ..config import CONFIG
 from .bars import BarStore
 from .datasets import DatasetStore
@@ -38,6 +40,21 @@ from .referee_null import (
     resolve_referee_null_dir,
     resolve_referee_null_log_dir,
 )
+from .referee_registry import (
+    CertificateStore,
+    ConfirmationRequired,
+    FamilyAlreadyRecorded,
+    FamilyStore,
+    HypothesisAlreadyRecorded,
+    HypothesisMalformed,
+    HypothesisStore,
+    RetroactiveBoundary,
+    UnknownSpecId,
+    WithdrawalStore,
+    register_hypothesis,
+    registry_response,
+    resolve_referee_registry_dir,
+)
 from .routes import ResearchRegistry, get_bar_store, get_dataset_store, get_registry
 
 router = APIRouter(prefix="/research/desk/referee", tags=["referee"])
@@ -194,3 +211,111 @@ def get_referee_nulls_runs(
         "latest": records[-1] if records else None,
         "integrity_errors": errors,
     }
+
+
+# === J-05: the registry -- family/hypothesis/withdrawal/certificate stores + routes ===================
+#
+# See ``referee_registry.py``'s own module docstring for the mechanics (family+hypothesis
+# registered together through ONE act; withdrawal and certificate seeding stay library/CLI-only
+# this iteration -- the Data Contract names exactly one POST route). GET never computes (T-8):
+# the accrual fold below is a pure read over already-recorded stores.
+
+
+def get_referee_family_store() -> FamilyStore:
+    """The durable family store, rooted at the SAME resolved registry directory as the other
+    three registry stores (zero new ``Config`` field — ``referee_registry.resolve_referee_
+    registry_dir``) — a FastAPI dependency so a test overrides it via the env var or outright."""
+    return FamilyStore(resolve_referee_registry_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def get_referee_hypothesis_store() -> HypothesisStore:
+    return HypothesisStore(resolve_referee_registry_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def get_referee_withdrawal_store() -> WithdrawalStore:
+    return WithdrawalStore(resolve_referee_registry_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def get_referee_certificate_store() -> CertificateStore:
+    return CertificateStore(resolve_referee_registry_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+@router.get("/registry")
+def get_referee_registry(
+    family_store: FamilyStore = Depends(get_referee_family_store),
+    hypothesis_store: HypothesisStore = Depends(get_referee_hypothesis_store),
+    withdrawal_store: WithdrawalStore = Depends(get_referee_withdrawal_store),
+    certificate_store: CertificateStore = Depends(get_referee_certificate_store),
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+) -> dict:
+    """The pinned four-key registry fold (``families``/``hypotheses``/``withdrawals``/
+    ``certificates``) — every hypothesis served with its read-side ``status``/``accrual``
+    additions, never persisted on the record itself. Never 404/500 on an empty registry."""
+    return registry_response(
+        family_store=family_store,
+        hypothesis_store=hypothesis_store,
+        withdrawal_store=withdrawal_store,
+        certificate_store=certificate_store,
+        playbook_store=playbook_store,
+        config_fingerprint=CONFIG.config_fingerprint(),
+    )
+
+
+class RefereeHypothesisRegistrationRequest(BaseModel):
+    """Body for ``POST /research/desk/referee/registry/hypotheses`` — every field optional at the
+    pydantic level (``register_hypothesis`` itself is the ONE place that validates presence/
+    vocabulary/floors, so CLI, POST, and tests all refuse through the identical distinct-error
+    paths rather than FastAPI's own built-in 422 shape for some fields and a custom one for
+    others). ``confirm`` must be explicitly ``True`` before any write (the desk pattern's
+    "explicit confirmation required" made a literal field).
+
+    **``registered_at`` is deliberately NOT a field here** (iter-6 audit, finding B1): the
+    boundary is DERIVED from the registration instant (spec Sec5), so a caller-supplied instant
+    would be a caller-chosen ``confirmation_start_boundary`` — the exact thing
+    ``RetroactiveBoundary`` refuses on the sibling ``confirmation_start_boundary`` field, and a
+    direct breach of the era's "the historical atlas is exploratory forever" anti-goal (a
+    backdated boundary makes already-recorded historical sessions count as post-boundary
+    accrual). The server always stamps the real instant. ``register_hypothesis``'s own
+    payload-level override survives as a hermetic TEST seam only (TC-8's 23:30-ET fixture);
+    neither operator-reachable surface (this route, the CLI) can reach it."""
+
+    confirm: bool = False
+    hypothesis_id: Optional[str] = None
+    family_id: Optional[str] = None
+    family_q: Optional[float] = None
+    family_candidate_hypothesis_ids: Optional[list[str]] = None
+    evidence_family: Optional[str] = None
+    estimand: Optional[str] = None
+    setup_id: Optional[str] = None
+    side: Optional[str] = None
+    context_predicate: Optional[dict] = None
+    primary_measure_key: Optional[str] = None
+    primary_horizon: Optional[str] = None
+    sidedness: Optional[str] = None
+    null_spec_id: Optional[str] = None
+    test_spec_id: Optional[str] = None
+    target_sessions: Optional[int] = None
+    min_occurrences: Optional[int] = None
+    confirmation_start_boundary: Optional[str] = None
+
+
+@router.post("/registry/hypotheses")
+def post_referee_registry_hypothesis(
+    body: RefereeHypothesisRegistrationRequest,
+    family_store: FamilyStore = Depends(get_referee_family_store),
+    hypothesis_store: HypothesisStore = Depends(get_referee_hypothesis_store),
+) -> dict:
+    """The registration act (goal.md J-05 Step 2): registers one hypothesis (through its family,
+    create-if-absent/verify-if-present — see ``referee_registry.py``). Refuses — 422, naming the
+    distinct reason, never starting a write — on malformed fields, an unrecognised spec id, a
+    retroactive boundary, a family-definition mismatch, or a missing ``confirm``; 409 on a
+    duplicate ``family_id``/``hypothesis_id`` (append-only, never a silent overwrite). The
+    registration instant is server-stamped, never caller-supplied — see the request model."""
+    payload = body.model_dump(exclude={"confirm"})
+    try:
+        record = register_hypothesis(family_store, hypothesis_store, payload, confirm=body.confirm)
+    except (HypothesisMalformed, UnknownSpecId, RetroactiveBoundary, ConfirmationRequired) as exc:
+        raise HTTPException(status_code=422, detail=str(exc)) from exc
+    except (FamilyAlreadyRecorded, HypothesisAlreadyRecorded) as exc:
+        raise HTTPException(status_code=409, detail=str(exc)) from exc
+    return record
diff --git a/apps/backend/tests/test_referee_guards.py b/apps/backend/tests/test_referee_guards.py
index 866ff8d..2d93ae5 100644
--- a/apps/backend/tests/test_referee_guards.py
+++ b/apps/backend/tests/test_referee_guards.py
@@ -310,3 +310,35 @@ def test_referee_stats_import_ban_guard_can_fail_on_a_seeded_violation():
     for banned in _REFEREE_STATS_BANNED_MODULES:
         hits |= _mentioning(seeded_imports, banned)
     assert hits == {"app.research.desk_forward", "app.research.levels"}
+
+
+# --- goal-referee-iter-6: referee_registry.py sits inside the same Read-side-law boundary --------
+#
+# `referee_registry.py`'s Estimand-C structural check (spec Sec3.3) needs the fixed backing-bucket
+# vocabulary, but reads it TRANSITIVELY through `referee_null.py` (`from .referee_null import
+# PLAYBOOK_CONTEXT_BACKING_BUCKETS`) rather than importing `desk_playbook_context` itself -- it
+# never touches `BandMapResolver` or any live map computation. The glob-based guards above
+# (`test_no_referee_module_imports_the_detect_module` /
+# `test_no_referee_module_other_than_referee_null_imports_the_context_module`) already cover this
+# new file automatically (they iterate every `referee_*.py` module on disk), so no existing
+# assertion needed editing -- this explicit, file-named test makes that coverage undeniable to a
+# reviewer rather than leaving it merely implicit in a glob.
+
+
+def test_referee_registry_module_imports_neither_the_detect_nor_the_context_module():
+    """goal-referee-iter-6 IN SCOPE: ``referee_registry.py`` may import the rail/``referee_
+    evidence``/other referee modules, but -- like every referee module except ``referee_null.py``
+    -- never ``desk_playbook_detect`` or ``desk_playbook_context`` directly."""
+    path = _RESEARCH_DIR / "referee_registry.py"
+    assert path.exists(), "referee_registry.py not found at the expected location -- has it moved?"
+    imported = _imported_module_names(path)
+    assert not _mentioning(imported, "desk_playbook_detect")
+    assert not _mentioning(imported, "desk_playbook_context")
+
+
+def test_referee_registry_import_ban_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_imports = {"app.research.desk_playbook_context", "app.research.other"}
+    assert _mentioning(seeded_imports, "desk_playbook_context") == {
+        "app.research.desk_playbook_context"
+    }
diff --git a/apps/backend/tests/test_referee_null.py b/apps/backend/tests/test_referee_null.py
index 08a9c19..0d70af9 100644
--- a/apps/backend/tests/test_referee_null.py
+++ b/apps/backend/tests/test_referee_null.py
@@ -39,6 +39,7 @@ from app.research.referee_null import (
     RefereeNullStore,
     _eligible_anchor_positions,
     _session_close_epoch,
+    _window_overlap_fraction,
     build_null_record,
     null_context_spec_signature,
     null_tod_spec_signature,
@@ -524,6 +525,175 @@ def test_tc16_test_perm_spec_blob_is_exactly_spec_section1s_stated_contents():
     assert blob["id"] == REFEREE_TEST_PERM_SPEC_ID
 
 
+# === iter-6 rider 1: backing_bucket_eligibility_rate is None, never 0.0, when nothing is =============
+# measurable at all (a resolved map, but zero ToD-eligible candidates were even checked) ==============
+
+
+def test_iter6_rider1_backing_rate_is_none_when_map_resolves_but_zero_candidates_are_tod_eligible(env):
+    """TC-17 (this iteration's numbering): a single-bar session (only the trigger itself, so
+    ``tod_eligible_count == 0``) with a context resolver that DOES return a real map --
+    ``backing_bucket_eligibility_rate`` must be ``None`` (nothing was ever CHECKED against the
+    predicate), never ``0.0`` (which would falsely imply a measured 0% match over a real
+    population). Before the rider fix this served ``0.0`` because the OLD code only special-cased
+    ``map_result is None``, not the ``tod_eligible_count == 0`` half of the SAME disclosure."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [_bar5("R1", 0)]  # only the trigger -- zero other bars, so zero ToD-eligible candidates
+    observation = _plant_occurrence(playbook_store, bar_store, "R1", bars)
+
+    class _FakeResolver:
+        def resolve(self, symbol, as_of_epoch):
+            return {
+                "bands": [
+                    {
+                        "side": "support", "class": "A", "price_low": 99.9, "price_high": 100.1,
+                        "quality_score": 1.0, "round_number": False, "member_count": 1,
+                    }
+                ],
+                "basis_as_of": "2026-06-21",
+            }
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_CONTEXT_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+        context_resolver=_FakeResolver(),
+    )
+    assert record["excluded"] is True
+    assert record["eligible_count"] == 0
+    assert record["backing_bucket_eligibility_rate"] is None  # never 0.0 -- nothing was measurable
+
+
+def test_iter6_rider1_genuine_zero_match_rate_over_a_real_population_still_serves_0_0(env):
+    """The rider fix's own can-fail counter-test: when candidates WERE actually checked (a real,
+    non-empty ToD-eligible population) and NONE matched the predicate, ``0.0`` is still the
+    correct, honest value -- the rider narrows the ``None`` case, it does not eliminate the
+    genuine-zero-match case."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [
+        _bar5("R1B", 0, close=100.05),  # trigger -- near the band
+        _bar5("R1B", 1, close=500.0),  # far from the band -- checked, does not match
+    ]
+    observation = _plant_occurrence(playbook_store, bar_store, "R1B", bars)
+
+    class _FakeResolver:
+        def resolve(self, symbol, as_of_epoch):
+            return {
+                "bands": [
+                    {
+                        "side": "support", "class": "A", "price_low": 99.9, "price_high": 100.1,
+                        "quality_score": 1.0, "round_number": False, "member_count": 1,
+                    }
+                ],
+                "basis_as_of": "2026-06-21",
+            }
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_CONTEXT_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+        context_resolver=_FakeResolver(),
+    )
+    assert record["excluded"] is True  # the one candidate was checked and failed the predicate
+    assert record["eligible_count"] == 0
+    assert record["backing_bucket_eligibility_rate"] == 0.0  # a REAL measured 0% -- not None
+
+
+# === iter-6 rider 2: the seeded subset draw, discriminated by a genuine >4-eligible fixture ===========
+
+
+def test_iter6_tc15_seeded_draw_is_reproducible_and_non_trivial_over_7_eligible_candidates(env):
+    """TC-15: 8 bars (trigger + 7 candidates, all in the SAME ToD bucket) -> eligible_count == 7 >
+    K == 4, so the draw is actually discriminated (iter-5's own carried lesson: every EXISTING
+    fixture had eligible_count <= 4, where "draw all of them" is correct regardless of whether the
+    selector's own randomization logic works at all). Two independent builds over the IDENTICAL
+    observation return the IDENTICAL 4-anchor subset (determinism); the SAME independent
+    re-derivation TC-1 already established (a fresh ``referee_stream`` + ``_draw_anchor_indices``
+    call) matches byte-for-byte; and the subset is NOT merely "the first 4 eligible positions in
+    order" (the non-trivial check a naive/broken selector that ignored the RNG entirely would
+    fail)."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [_bar5("R2", i) for i in range(8)]  # index 0 = trigger, 1..7 = 7 candidates
+    observation = _plant_occurrence(playbook_store, bar_store, "R2", bars)
+
+    first = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    assert first["eligible_count"] == 7
+    assert first["k_drawn"] == 4
+    assert len(first["anchors"]) == 4
+
+    second = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    first_ts = sorted(a["anchor_ts"] for a in first["anchors"])
+    second_ts = sorted(a["anchor_ts"] for a in second["anchors"])
+    assert first_ts == second_ts  # byte-identical repeat draw (TC-15's own "both runs" wording)
+
+    # Independent re-derivation (TC-1's own established methodology, now over a genuinely
+    # discriminating eligible_count=7 > k=4 population).
+    stream = referee_stream(
+        REFEREE_NULL_TOD_SPEC_ID, "null-draw", session_date=observation["session_date"],
+        i=observation["observation_id"],
+    )
+    eligible_positions = [1, 2, 3, 4, 5, 6, 7]
+    expected_drawn = _draw_anchor_indices(stream, 7, 4)
+    expected_indices = sorted(eligible_positions[j] for j in expected_drawn)
+    actual_indices = sorted(
+        i for i, bar in enumerate(bars)
+        if referee_null_module._iso(bar.epoch) in {a["anchor_ts"] for a in first["anchors"]}
+    )
+    assert actual_indices == expected_indices
+    # Non-trivial: a selector that ignored the RNG and simply took the first K eligible positions
+    # would (mis)produce exactly [1, 2, 3, 4] -- the real seeded draw must not coincide with that.
+    assert expected_indices != [1, 2, 3, 4]
+
+
+def test_iter6_tc15_a_different_observation_key_draws_a_different_subset(env):
+    """TC-15's second half: a DIFFERENT observation (a different symbol -> a different
+    ``observation_id``, the seeded stream's own ``i=`` component) over the IDENTICAL 7-candidate
+    bar shape draws a DIFFERENT 4-anchor subset -- proving the stream is genuinely keyed per
+    occurrence, not a hidden constant that happens to look reproducible."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars_a = [_bar5("R2A", i) for i in range(8)]
+    bars_b = [_bar5("R2B", i) for i in range(8)]
+    obs_a = _plant_occurrence(playbook_store, bar_store, "R2A", bars_a, signature="sig-r2a")
+    obs_b = _plant_occurrence(playbook_store, bar_store, "R2B", bars_b, signature="sig-r2b")
+
+    record_a = build_null_record(
+        obs_a, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    record_b = build_null_record(
+        obs_b, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    # Anchor timestamps are compared by their INDEX within each symbol's own bar array (the
+    # timestamps themselves differ across symbols only in which array they index into, since both
+    # fixtures share the identical E_OPEN + i*300 schedule) -- so the comparison is over the drawn
+    # INDEX sets, not the raw ISO strings.
+    indices_a = sorted(
+        i for i, bar in enumerate(bars_a)
+        if referee_null_module._iso(bar.epoch) in {a["anchor_ts"] for a in record_a["anchors"]}
+    )
+    indices_b = sorted(
+        i for i, bar in enumerate(bars_b)
+        if referee_null_module._iso(bar.epoch) in {a["anchor_ts"] for a in record_b["anchors"]}
+    )
+    assert indices_a != indices_b
+
+
+def test_iter6_tc16_window_overlap_fraction_hand_computed():
+    """TC-16 (this iteration's numbering): hand-computed measurement-window pairs against
+    ``_window_overlap_fraction`` directly. Occurrence window [0, 10) (length 10): an anchor window
+    [5, 12) overlaps [5, 10) -- 5 bars, a 0.5 fraction; an anchor window [15, 20) does not overlap
+    at all -- 0.0, never negative."""
+    assert _window_overlap_fraction(0, 10, 5, 12) == pytest.approx(0.5)
+    assert _window_overlap_fraction(0, 10, 15, 20) == pytest.approx(0.0)
+    # A partial overlap on the LEFT: anchor window [-3, 4) overlaps [0, 4) -- 4 bars of the
+    # occurrence's own 10-bar window -- 0.4.
+    assert _window_overlap_fraction(0, 10, -3, 4) == pytest.approx(0.4)
+
+
 # === store discipline: no update/delete method exists anywhere =======================================
 
 
diff --git a/apps/backend/app/research/referee_registry.py b/apps/backend/app/research/referee_registry.py
new file mode 100644
index 0000000..30c04e0
--- /dev/null
+++ b/apps/backend/app/research/referee_registry.py
@@ -0,0 +1,954 @@
+"""Era 6 "The Referee" (J-05) -- the registry: pre-registration with an immutable boundary. The
+FOURTH ``referee_*.py`` module, following ``referee_evidence.py``/``referee_null.py``'s exact
+conventions (append-only file-per-record stores, checksum-verified loads, a resolved
+env-var-or-sibling storage directory, a CLI warmer matching ``argparse``/``main()``).
+
+**What this module builds, spec-verbatim (``docs/referee-statistical-spec.md`` Sec5).** Four
+append-only record kinds -- FAMILY, HYPOTHESIS, WITHDRAWAL, CERTIFICATE -- plus the registration
+act (``register_hypothesis``) that writes the first two, the withdrawal act
+(``withdraw_hypothesis``) that writes the third, and the read-side fold (``registry_response``)
+``GET /research/desk/referee/registry`` serves. The CERTIFICATE store exists this iteration in
+SHAPE only (append-only-ness tested); its mint path is explicitly J-08's job
+(``docs/goal.md``: "mintable only through the real evaluation rail").
+
+**Family + hypothesis are registered together, through ONE act.** The Data Contract names
+exactly one POST route (``.../registry/hypotheses``) and the goal's own Steps describe
+"Registration acts: CLI + POST ... with explicit confirmation" as a single act, never two. A
+FAMILY's ``candidate_hypothesis_ids`` must be "the COMPLETE planned list -- the BH denominator m,
+forever" (spec Sec5), decided BEFORE any of its hypotheses are individually registered -- so
+every hypothesis-registration call carries its OWN family's full definition
+(``family_id``/``family_q``/``family_candidate_hypothesis_ids``) alongside the hypothesis's own
+fields. The FIRST call naming a given ``family_id`` CREATES that family record (append-only,
+from that call's own family fields); every LATER call naming the SAME ``family_id`` must supply
+the IDENTICAL ``q``/candidate list (else refused -- a family's definition can never drift after
+its first sighting) and its own ``hypothesis_id`` must already be a member of that list (a
+hypothesis can never "join a family retroactively" -- the era's own anti-goal, made structural).
+``FamilyStore`` is independently a plain append-only store (TC-1 exercises it directly, with no
+hypothesis involved at all) -- ``register_hypothesis`` is simply its ONE production caller this
+iteration.
+
+**``hypothesis_id``/``family_id``/``certificate_id`` are caller-supplied, not derived.** Unlike
+``RefereeNullStore`` (whose identity is a pure function of an observation + null-spec, so a
+re-run over an unchanged corpus must DEDUPE, never duplicate), a hypothesis is a genuinely new,
+rare, deliberate operator act each time -- there is no "the same content should collapse to the
+same record" requirement anywhere in the spec, and mandating one would invent an identity
+function the spec never names. A caller-chosen mnemonic string (mirroring how ``family_id``,
+setup ids, and dataset ids are already caller-named throughout this codebase) is the simplest
+design that satisfies every TC: "duplicate hypothesis_id/family_id" (IN SCOPE) means exactly
+"the same id string submitted twice," structurally identical to ``NullAlreadyRecorded``'s own
+append-only-with-raise discipline.
+
+**The boundary is computed, not chosen -- and no operator surface can name the instant it is
+computed FROM (iter-6 audit, finding B1).** ``confirmation_start_boundary`` is DEFINED as "the ET
+calendar date of ``registered_at``" (spec Sec5) -- never independently choosable. The
+payload-level ``registered_at`` override below survives as a hermetic TEST seam only (the ONLY way
+a keyless test can exercise a specific ET calendar instant -- e.g. TC-8's 23:30 ET fixture --
+without waiting on the real clock): the POST route does not expose the field at all and the CLI
+carries no ``--registered-at`` flag, so every operator-reachable registration is stamped with real
+wall-clock ``_iso_utc_now()``. That containment is load-bearing, not hygiene -- a caller-chosen
+instant IS a caller-chosen boundary, and a backdated boundary makes already-recorded HISTORICAL
+sessions accrue as post-boundary confirmation, breaching the era's "the historical atlas is
+exploratory forever" anti-goal into an append-only record with no delete path. An explicit
+``confirmation_start_boundary`` in the payload is likewise never stored as-is: a value AT OR
+BEFORE the honest computed one is refused (``RetroactiveBoundary``, TC-4); a value strictly after
+it is ignored (the stored value is always exactly the computed one -- spec Sec5 names no "delay
+the boundary" feature). This is a defensive validation path, not a feature a real caller is
+expected to use.
+
+**The Estimand-C "cannot evaluate" check is structural, never a live resolve (Build Notes,
+iteration spec).** A hypothesis registers against a setup+side ABSTRACTLY -- no concrete
+symbol/session exists yet to hand ``BandMapResolver.resolve()``. The spec's own text ("not
+evaluable at anchor bars from recorded data") is satisfied by checking the named
+``backing_bucket`` value against the FIXED vocabulary (``PLAYBOOK_CONTEXT_BACKING_BUCKETS``) --
+never a live map lookup. This module does NOT import ``desk_playbook_context`` (the
+import-topology guard's existing, unmodified ban already covers it, since it globs every
+``referee_*.py`` module) -- it reads the vocabulary constant TRANSITIVELY through
+``referee_null.py`` (the one referee module the guard exempts to hold it in the first place),
+never touching the live resolver, never duplicating the vocabulary as a second hand-copied
+tuple (single source of truth).
+
+**Withdrawal's evaluation-existence signal is injected, not queried.** No evaluation store
+exists until J-06 -- ``withdraw_hypothesis`` takes a plain ``post_boundary_evaluation_exists:
+bool`` parameter (default ``False``, the honest answer for EVERY real hypothesis today, since no
+evaluation of any kind has ever run this era) rather than reaching into a store that does not
+exist. J-06 wires the real signal through this identical parameter once it exists -- the
+refusal RULE itself (tested both ways via the injected bool, TC-9/TC-10) does not change.
+
+**Accrual is a disclosed readiness PROXY, not spec Sec3.1's exact informative-session count**
+(ratified, ``runs/goal-session-referee/state/assumptions.md`` iter-6): the count of distinct
+POST-BOUNDARY ``session_date``s carrying >=1 observation in the hypothesis's own
+``(setup_id, side)`` cell, computed with the SAME shared pooling primitives
+``referee_evidence.playbook_occurrence_readiness()`` is built from
+(``_newest_per_session_date``, ``_is_stale_basis``, ``current_playbook_detector_basis``) --
+never a second, independently-written date/basis loop, and never a second ``PlaybookStore``
+scan per hypothesis: ``registry_response`` scans the store exactly ONCE per call and folds every
+hypothesis's own accrual against that single scan."""
+
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import os
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+
+from ..config import CONFIG, Config
+from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
+from .referee_evidence import (
+    _epoch_from_iso,
+    _et_session_date,
+    _is_stale_basis,
+    _newest_per_session_date,
+    _record_detector_basis,
+    current_playbook_detector_basis,
+)
+from .referee_null import (
+    PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
+    PLAYBOOK_CONTEXT_BACKING_BUCKETS,
+    REFEREE_NULL_CONTEXT_SPEC_ID,
+    REFEREE_NULL_TOD_SPEC_ID,
+    REFEREE_TEST_PERM_SPEC_ID,
+)
+
+__all__ = [
+    "REFEREE_MIN_SESSIONS",
+    "REFEREE_MIN_OCCURRENCES",
+    "REFEREE_HYPOTHESIS_ORIGIN",
+    "resolve_referee_registry_dir",
+    "RegistryIntegrityError",
+    "FamilyAlreadyRecorded",
+    "HypothesisAlreadyRecorded",
+    "CertificateAlreadyRecorded",
+    "HypothesisMalformed",
+    "RetroactiveBoundary",
+    "UnknownSpecId",
+    "ConfirmationRequired",
+    "WithdrawalRefused",
+    "FamilyStore",
+    "HypothesisStore",
+    "WithdrawalStore",
+    "CertificateStore",
+    "register_hypothesis",
+    "withdraw_hypothesis",
+    "registry_response",
+]
+
+# === spec Sec1: the two floors this module is the first consumer of (module constants, never
+# Config fields -- the `REFEREE_NULL_ANCHORS_PER_OCCURRENCE`-in-`referee_null.py` precedent: a
+# constant lives in the FIRST module that actually needs it, not in a shared catch-all). ===========
+
+REFEREE_MIN_SESSIONS: int = 12
+REFEREE_MIN_OCCURRENCES: int = 12
+
+# Every hypothesis this era carries this exact origin label (goal.md: "the atlas was inspected
+# before these questions were written down") -- server-stamped, never caller-supplied.
+REFEREE_HYPOTHESIS_ORIGIN: str = "historical-exploration"
+
+_EVIDENCE_FAMILIES = frozenset({"playbook", "strategy"})
+_ESTIMANDS = frozenset({"A", "B", "C"})
+_SIDES = frozenset({"long", "short"})
+_SIDEDNESS_VALUES = frozenset({"greater", "less", "two-sided"})
+_NULL_SPEC_IDS = frozenset({REFEREE_NULL_TOD_SPEC_ID, REFEREE_NULL_CONTEXT_SPEC_ID})
+_TEST_SPEC_IDS = frozenset({REFEREE_TEST_PERM_SPEC_ID})
+_CONTEXTUAL_ESTIMANDS = frozenset({"B", "C"})
+
+_REGISTRY_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR"
+
+_REQUIRED_HYPOTHESIS_FIELDS: tuple[str, ...] = (
+    "hypothesis_id",
+    "family_id",
+    "family_q",
+    "family_candidate_hypothesis_ids",
+    "evidence_family",
+    "estimand",
+    "setup_id",
+    "side",
+    "primary_measure_key",
+    "primary_horizon",
+    "sidedness",
+    "test_spec_id",
+    "target_sessions",
+    "min_occurrences",
+)
+
+
+def resolve_referee_registry_dir(desk_universe_dir_resolved: str) -> str:
+    """The registry's ONE storage directory (all four record kinds live here, distinguished by
+    filename prefix): ``TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR`` if set, else a ``referee_registry``
+    SIBLING of the caller's own already-resolved universe directory
+    (``resolve_referee_null_dir``'s exact pattern). Deliberately NOT a ``Config`` field."""
+    override = os.environ.get(_REGISTRY_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "referee_registry")
+
+
+def _canonical(obj: object) -> bytes:
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+# === exceptions =======================================================================================
+
+
+class RegistryIntegrityError(Exception):
+    """An on-disk registry record file failed its checksum verification on load -- corrupted or
+    tampered, surfaced explicitly (never silence, never a fabricated record)."""
+
+
+class FamilyAlreadyRecorded(Exception):
+    def __init__(self, family_id: str) -> None:
+        self.family_id = family_id
+        super().__init__(
+            f"a family record with id {family_id!r} is already recorded -- family records are "
+            f"immutable and are never re-recorded"
+        )
+
+
+class HypothesisAlreadyRecorded(Exception):
+    def __init__(self, hypothesis_id: str) -> None:
+        self.hypothesis_id = hypothesis_id
+        super().__init__(
+            f"a hypothesis record with id {hypothesis_id!r} is already recorded -- hypothesis "
+            f"records are immutable and are never re-recorded"
+        )
+
+
+class CertificateAlreadyRecorded(Exception):
+    def __init__(self, certificate_id: str) -> None:
+        self.certificate_id = certificate_id
+        super().__init__(
+            f"a certificate record with id {certificate_id!r} is already recorded -- certificate "
+            f"records are immutable and are never re-recorded"
+        )
+
+
+class HypothesisMalformed(Exception):
+    """A registration payload is missing a required field, carries an out-of-vocabulary value, a
+    below-floor sample target, an unevaluable Estimand-C context predicate, or a family
+    definition that disagrees with that family's own already-recorded fields."""
+
+
+class RetroactiveBoundary(Exception):
+    """A payload's own explicit ``confirmation_start_boundary`` disagrees with the honest value
+    ``registered_at`` computes to -- refused (the boundary is derived, never chosen)."""
+
+
+class UnknownSpecId(Exception):
+    """A payload names a ``null_spec_id``/``test_spec_id`` outside the pinned set (spec Sec1)."""
+
+
+class ConfirmationRequired(Exception):
+    """``confirm`` was not explicitly ``True`` -- no record is ever written without it."""
+
+
+class WithdrawalRefused(Exception):
+    """A withdrawal was refused: unknown ``hypothesis_id``, a post-boundary evaluation already
+    exists, or the hypothesis is already withdrawn."""
+
+
+# === shared checksum-verified JSON record read/write (4 store classes below share this) ==============
+
+
+def _write_json_record(root: Path, path: Path, fields: dict, *, kind: str) -> dict:
+    record = {"meta": dict(fields)}
+    payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
+    root.mkdir(parents=True, exist_ok=True)
+    path.write_text(json.dumps(payload))
+    return dict(fields)
+
+
+def _load_json_record(path: Path, *, kind: str) -> dict:
+    try:
+        data = json.loads(path.read_text())
+    except (OSError, ValueError) as exc:
+        raise RegistryIntegrityError(
+            f"{kind} file '{path.name}' is not parseable ({exc}) -- corrupted or tampered"
+        ) from exc
+    if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
+        raise RegistryIntegrityError(
+            f"{kind} file '{path.name}' does not carry the expected record shape -- corrupted "
+            f"or tampered"
+        )
+    record = data["record"]
+    if _sha256(_canonical(record)) != data["file_checksum"]:
+        raise RegistryIntegrityError(
+            f"{kind} file '{path.name}' failed its integrity check (checksum mismatch) -- the "
+            f"file was corrupted or tampered with"
+        )
+    meta = record.get("meta")
+    if not isinstance(meta, dict):
+        raise RegistryIntegrityError(
+            f"{kind} file '{path.name}' does not carry the expected record shape -- corrupted "
+            f"or tampered"
+        )
+    return meta
+
+
+# === the four append-only stores (one shared directory, one filename prefix each) ====================
+
+
+class FamilyStore:
+    """File-based store rooted at the resolved registry directory, ``family-*.json`` files only.
+    No update/delete method exists anywhere on this class (structural -- source-scan
+    guard-tested); ``record`` refuses an already-present ``family_id`` (``FamilyAlreadyRecorded``,
+    TC-1) or a corrupted file already occupying that id's own deterministic path
+    (``RegistryIntegrityError``, never a silent overwrite)."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    @property
+    def root(self) -> Path:
+        return self._root
+
+    def _path(self, family_id: str) -> Path:
+        return self._root / f"family-{family_id}.json"
+
+    def get(self, family_id: str) -> dict | None:
+        path = self._path(family_id)
+        if not path.exists():
+            return None
+        meta = _load_json_record(path, kind="family")
+        if meta.get("family_id") != family_id:
+            return None
+        return dict(meta)
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        if not self._root.exists():
+            return [], []
+        records: list[dict] = []
+        errors: list[dict] = []
+        for path in sorted(self._root.glob("family-*.json")):
+            try:
+                records.append(dict(_load_json_record(path, kind="family")))
+            except RegistryIntegrityError as exc:
+                errors.append({"file": path.name, "error": str(exc)})
+        records.sort(key=lambda meta: (meta.get("registered_at", ""), meta.get("family_id", "")))
+        return records, errors
+
+    def record(self, fields: dict) -> dict:
+        family_id = fields["family_id"]
+        path = self._path(family_id)
+        if path.exists():
+            try:
+                _load_json_record(path, kind="family")
+            except RegistryIntegrityError:
+                raise
+            raise FamilyAlreadyRecorded(family_id)
+        return _write_json_record(self._root, path, fields, kind="family")
+
+
+class HypothesisStore:
+    """File-based store rooted at the resolved registry directory, ``hypothesis-*.json`` files
+    only. No update/delete method exists anywhere on this class (structural); ``record`` refuses
+    an already-present ``hypothesis_id`` (``HypothesisAlreadyRecorded``, TC-2's own duplicate
+    check)."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    @property
+    def root(self) -> Path:
+        return self._root
+
+    def _path(self, hypothesis_id: str) -> Path:
+        return self._root / f"hypothesis-{hypothesis_id}.json"
+
+    def get(self, hypothesis_id: str) -> dict | None:
+        path = self._path(hypothesis_id)
+        if not path.exists():
+            return None
+        meta = _load_json_record(path, kind="hypothesis")
+        if meta.get("hypothesis_id") != hypothesis_id:
+            return None
+        return dict(meta)
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        if not self._root.exists():
+            return [], []
+        records: list[dict] = []
+        errors: list[dict] = []
+        for path in sorted(self._root.glob("hypothesis-*.json")):
+            try:
+                records.append(dict(_load_json_record(path, kind="hypothesis")))
+            except RegistryIntegrityError as exc:
+                errors.append({"file": path.name, "error": str(exc)})
+        records.sort(
+            key=lambda meta: (meta.get("registered_at", ""), meta.get("hypothesis_id", ""))
+        )
+        return records, errors
+
+    def record(self, fields: dict) -> dict:
+        hypothesis_id = fields["hypothesis_id"]
+        path = self._path(hypothesis_id)
+        if path.exists():
... [diff_bound] apps/backend/app/research/referee_registry.py: 560 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_referee_registry.py b/apps/backend/tests/test_referee_registry.py
new file mode 100644
index 0000000..36a1a7e
--- /dev/null
+++ b/apps/backend/tests/test_referee_registry.py
@@ -0,0 +1,823 @@
+"""``referee_registry.py`` + the ``/research/desk/referee/registry*`` routes (Era 6 "The Referee",
+J-05) -- pre-registration with an immutable boundary. Test-first contract: TC-1 through TC-14 in
+``docs/phases/goal-referee-iter-6.md``, full depth (mandatory per the prior ESCALATE verdict).
+
+Fixtures build a complete, valid Estimand-A registration payload (``_estimand_a_payload``) that
+each malformed-class test overrides exactly ONE field of -- and plant real ``PlaybookStore``
+records (via that store's own public ``record`` write path, the ``test_referee_null.py``
+precedent) for the accrual fold tests, since ``register_hypothesis``/``registry_response`` never
+re-implement anything ``PlaybookStore`` already owns."""
+
+from __future__ import annotations
+
+import datetime
+import sys
+import zoneinfo
+
+import pytest
+from fastapi.testclient import TestClient
+
+import app.research.referee_registry as referee_registry_module
+from app.config import CONFIG
+from app.main import app
+from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
+from app.research.referee_null import REFEREE_NULL_TOD_SPEC_ID, REFEREE_TEST_PERM_SPEC_ID
+from app.research.referee_registry import (
+    REFEREE_MIN_OCCURRENCES,
+    REFEREE_MIN_SESSIONS,
+    CertificateAlreadyRecorded,
+    CertificateStore,
+    ConfirmationRequired,
+    FamilyAlreadyRecorded,
+    FamilyStore,
+    HypothesisAlreadyRecorded,
+    HypothesisMalformed,
+    HypothesisStore,
+    RetroactiveBoundary,
+    UnknownSpecId,
+    WithdrawalRefused,
+    WithdrawalStore,
+    register_hypothesis,
+    registry_response,
+    withdraw_hypothesis,
+)
+
+_ET = zoneinfo.ZoneInfo("America/New_York")
+
+
+def _et_instant_iso(year: int, month: int, day: int, hour: int, minute: int) -> str:
+    """An ISO-8601 UTC string for an ET wall-clock instant -- DST-correct by construction
+    (mirrors ``test_referee_null.py`` TC-4's own ``datetime.combine(..., tzinfo=et)`` idiom,
+    never a hand-computed UTC offset)."""
+    dt = datetime.datetime.combine(
+        datetime.date(year, month, day), datetime.time(hour, minute), tzinfo=_ET
+    )
+    return dt.astimezone(datetime.timezone.utc).isoformat(timespec="microseconds").replace(
+        "+00:00", "Z"
+    )
+
+
+# A fixed, mid-DST registration instant every test below uses unless it overrides
+# ``registered_at`` itself: 2026-06-10 12:00 ET -> boundary "2026-06-10".
+_REGISTERED_AT = _et_instant_iso(2026, 6, 10, 8, 0)
+_BOUNDARY = "2026-06-10"
+
+
+def _estimand_a_payload(hypothesis_id: str, family_id: str, **overrides: object) -> dict:
+    """A complete, valid Estimand-A (``capitulation``/``long``/``5m``) registration payload --
+    spec Sec7's S-1 shape. Each malformed-class test overrides exactly the one field it means to
+    break."""
+    payload = {
+        "hypothesis_id": hypothesis_id,
+        "family_id": family_id,
+        "family_q": 0.10,
+        "family_candidate_hypothesis_ids": [hypothesis_id],
+        "evidence_family": "playbook",
+        "estimand": "A",
+        "setup_id": "capitulation",
+        "side": "long",
+        "context_predicate": None,
+        "primary_measure_key": "5m",
+        "primary_horizon": "5m",
+        "sidedness": "greater",
+        "null_spec_id": REFEREE_NULL_TOD_SPEC_ID,
+        "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+        "target_sessions": REFEREE_MIN_SESSIONS,
+        "min_occurrences": REFEREE_MIN_OCCURRENCES,
+        "registered_at": _REGISTERED_AT,
+    }
+    payload.update(overrides)
+    return payload
+
+
+@pytest.fixture
+def stores(tmp_path):
+    family_store = FamilyStore(tmp_path / "registry")
+    hypothesis_store = HypothesisStore(tmp_path / "registry")
+    withdrawal_store = WithdrawalStore(tmp_path / "registry")
+    certificate_store = CertificateStore(tmp_path / "registry")
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    return family_store, hypothesis_store, withdrawal_store, certificate_store, playbook_store
+
+
+def _plant_playbook_signals(
+    playbook_store: PlaybookStore, session_date: str, signals: list[dict]
+) -> None:
+    """One playbook record at ``session_date`` carrying ``signals`` verbatim -- minimal dicts are
+    sufficient (``PlaybookStore.record`` stores ``signals`` opaquely with zero shape validation,
+    and the accrual fold reads only ``setup_id``/``side`` off each one)."""
+    playbook_store.record(
+        session_date=session_date,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature=f"sig-{session_date}",
+        payload_version=3,
+        parameters=playbook_parameters(),
+        register=PLAYBOOK_REGISTER,
+        signals=signals,
+        absences=[],
+        diagnostics=[],
+    )
+
+
+def _signal(setup_id: str, side: str, symbol: str = "AAA") -> dict:
+    return {"setup_id": setup_id, "side": side, "symbol": symbol}
+
+
+# === TC-1: FamilyStore -- duplicate family_id raises; exactly one record survives ====================
+
+
+def test_tc1_duplicate_family_id_raises_and_store_keeps_exactly_one_record(stores):
+    family_store, _hyp, _wd, _cert, _pb = stores
+    fields = {
+        "family_id": "fam-tc1",
+        "q": 0.10,
+        "candidate_hypothesis_ids": ["hyp-a", "hyp-b"],
+        "registered_at": _REGISTERED_AT,
+    }
+    family_store.record(fields)
+    with pytest.raises(FamilyAlreadyRecorded):
+        family_store.record(fields)
+    records, errors = family_store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0]["family_id"] == "fam-tc1"
+
+
+# === TC-2: a fixture Estimand-A registration returns a hypothesis_id; boundary == ET date =============
+
+
+def test_tc2_estimand_a_registration_returns_a_hypothesis_id_with_the_correct_boundary(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload("hyp-tc2", "fam-tc2")
+    record = register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert record["hypothesis_id"] == "hyp-tc2"
+    assert record["confirmation_start_boundary"] == _BOUNDARY
+    assert record["origin"] == "historical-exploration"
+    assert record["detector_basis"] is not None  # playbook family -- server-computed
+    assert record["context_predicate"] is None  # estimand A -- never contextual
+
+    public_methods = {name for name in dir(HypothesisStore) if not name.startswith("_")}
+    assert public_methods == {"root", "get", "list", "record"}  # no update/delete method
+
+
+# === TC-3: missing required field (primary_horizon) refused, no record written =======================
+
+
+def test_tc3_missing_required_field_is_refused_and_writes_nothing(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload("hyp-tc3", "fam-tc3")
+    del payload["primary_horizon"]
+    with pytest.raises(HypothesisMalformed):
+        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    hyp_records, _errors = hypothesis_store.list()
+    assert hyp_records == []
+    fam_records, _errors = family_store.list()
+    assert fam_records == []  # the family is never created behind a malformed hypothesis either
+
+
+# === TC-4: an explicit boundary at/before registered_at's own ET date is refused =====================
+
+
+def test_tc4_retroactive_boundary_is_refused_and_writes_nothing(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload(
+        "hyp-tc4", "fam-tc4", confirmation_start_boundary=_BOUNDARY  # == registered_at's own date
+    )
+    with pytest.raises(RetroactiveBoundary):
+        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert hypothesis_store.list()[0] == []
+
+    # A date strictly BEFORE registered_at's own ET date is refused too ("at or before").
+    payload_earlier = _estimand_a_payload(
+        "hyp-tc4b", "fam-tc4b", confirmation_start_boundary="2026-06-01"
+    )
+    with pytest.raises(RetroactiveBoundary):
+        register_hypothesis(family_store, hypothesis_store, payload_earlier, confirm=True)
+    assert hypothesis_store.list()[0] == []
+
+
+# === TC-5: an unknown null_spec_id is refused, no record written =====================================
+
+
+def test_tc5_unknown_null_spec_id_is_refused_and_writes_nothing(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload("hyp-tc5", "fam-tc5", null_spec_id="referee-null-made-up-v9")
+    with pytest.raises(UnknownSpecId):
+        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert hypothesis_store.list()[0] == []
+
+
+def test_tc5_unknown_test_spec_id_is_refused_and_writes_nothing(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload("hyp-tc5b", "fam-tc5b", test_spec_id="referee-test-made-up-v9")
+    with pytest.raises(UnknownSpecId):
+        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert hypothesis_store.list()[0] == []
+
+
+# === TC-6: an Estimand-C registration with an unevaluable context_predicate is refused ================
+
+
+def test_tc6_estimand_c_unevaluable_context_predicate_is_refused_and_writes_nothing(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload(
+        "hyp-tc6", "fam-tc6",
+        estimand="C", setup_id="range_trade", side="long",
+        context_predicate={"backing_bucket": "not_a_real_bucket"},
+        primary_measure_key="1h", primary_horizon="1h",
+    )
+    with pytest.raises(HypothesisMalformed):
+        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert hypothesis_store.list()[0] == []
+
+
+def test_tc6_estimand_c_missing_context_predicate_entirely_is_also_refused(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload(
+        "hyp-tc6b", "fam-tc6b",
+        estimand="C", setup_id="range_trade", side="long",
+        context_predicate=None, primary_measure_key="1h", primary_horizon="1h",
+    )
+    with pytest.raises(HypothesisMalformed):
+        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert hypothesis_store.list()[0] == []
+
+
+def test_tc6_estimand_c_valid_at_wall_context_predicate_is_accepted(stores):
+    """The can-fail counter-test: a VALID ``backing_bucket`` (``at_wall``, spec Sec7 S-5) is
+    accepted -- the refusal above is discriminating, not a blanket ban on Estimand C."""
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload(
+        "hyp-tc6c", "fam-tc6c",
+        estimand="C", setup_id="range_trade", side="long",
+        context_predicate={"backing_bucket": "at_wall"},
+        primary_measure_key="1h", primary_horizon="1h",
+    )
+    record = register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert record["context_predicate"] == {"backing_bucket": "at_wall"}
+    assert record["context_algorithm_version"] is not None
+
+
+# === TC-7: target_sessions below REFEREE_MIN_SESSIONS is refused, no record written ===================
+
+
+def test_tc7_target_sessions_below_the_floor_is_refused_and_writes_nothing(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload("hyp-tc7", "fam-tc7", target_sessions=REFEREE_MIN_SESSIONS - 1)
+    with pytest.raises(HypothesisMalformed):
+        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert hypothesis_store.list()[0] == []
+
+
+def test_tc7_min_occurrences_below_the_floor_is_refused_and_writes_nothing(stores):
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    payload = _estimand_a_payload(
+        "hyp-tc7b", "fam-tc7b", min_occurrences=REFEREE_MIN_OCCURRENCES - 1
+    )
+    with pytest.raises(HypothesisMalformed):
+        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert hypothesis_store.list()[0] == []
+
+
+# === TC-8: the ET-midnight boundary case (23:30 ET on a DST date) ====================================
+
+
+def test_tc8_2330_et_registration_lands_on_the_same_et_calendar_date(stores):
+    """2026-06-22 is DST (EDT, UTC-4) -- 23:30 ET on that date is 03:30 UTC on 2026-06-23. A naive
+    implementation using the UTC calendar date would wrongly store "2026-06-23"; the correct,
+    ET-aware boundary is "2026-06-22" -- the SAME ET date the registration instant fell on."""
+    family_store, hypothesis_store, _wd, _cert, _pb = stores
+    registered_at = _et_instant_iso(2026, 6, 22, 23, 30)
+    assert registered_at.startswith("2026-06-23T03:30:00")  # sanity: genuinely crosses midnight UTC
+
+    payload = _estimand_a_payload("hyp-tc8", "fam-tc8", registered_at=registered_at)
+    record = register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    assert record["confirmation_start_boundary"] == "2026-06-22"  # the ET date, not "2026-06-23"
+
+
+# === TC-9 / TC-10: withdrawal ==========================================================================
+
+
+def test_tc9_withdrawal_succeeds_when_no_post_boundary_evaluation_exists(stores):
+    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
+    payload = _estimand_a_payload("hyp-tc9", "fam-tc9")
+    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+
+    withdrawn = withdraw_hypothesis(
+        hypothesis_store, withdrawal_store, hypothesis_id="hyp-tc9", reason="superseded",
+        post_boundary_evaluation_exists=False,
+    )
+    assert withdrawn["hypothesis_id"] == "hyp-tc9"
+    assert withdrawn["reason"] == "superseded"
+    records, errors = withdrawal_store.list()
+    assert errors == []
+    assert len(records) == 1
+
+    response = registry_response(
+        family_store=family_store, hypothesis_store=hypothesis_store,
+        withdrawal_store=withdrawal_store, certificate_store=cert_store,
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    folded = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc9")
+    assert folded["status"] == "withdrawn"
+
+    public_methods = {name for name in dir(WithdrawalStore) if not name.startswith("_")}
+    assert public_methods == {"root", "get", "list", "record"}  # no update/delete method
+
+
+def test_tc10_withdrawal_refused_when_a_post_boundary_evaluation_exists(stores):
+    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
+    payload = _estimand_a_payload("hyp-tc10", "fam-tc10")
+    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+
+    with pytest.raises(WithdrawalRefused):
+        withdraw_hypothesis(
+            hypothesis_store, withdrawal_store, hypothesis_id="hyp-tc10",
+            post_boundary_evaluation_exists=True,
+        )
+    records, errors = withdrawal_store.list()
+    assert errors == []
+    assert records == []  # no WITHDRAWAL record written
+
+    response = registry_response(
+        family_store=family_store, hypothesis_store=hypothesis_store,
+        withdrawal_store=withdrawal_store, certificate_store=cert_store,
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    folded = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc10")
+    assert folded["status"] == "active"
+
+
+def test_withdrawal_of_an_unknown_hypothesis_id_is_refused(stores):
+    _fam, hypothesis_store, withdrawal_store, _cert, _pb = stores
+    with pytest.raises(WithdrawalRefused):
+        withdraw_hypothesis(hypothesis_store, withdrawal_store, hypothesis_id="no-such-hypothesis")
+
+
+def test_a_second_withdrawal_of_an_already_withdrawn_hypothesis_is_refused(stores):
+    family_store, hypothesis_store, withdrawal_store, _cert, _pb = stores
+    payload = _estimand_a_payload("hyp-tc10b", "fam-tc10b")
+    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
+    withdraw_hypothesis(hypothesis_store, withdrawal_store, hypothesis_id="hyp-tc10b")
+    with pytest.raises(WithdrawalRefused):
+        withdraw_hypothesis(hypothesis_store, withdrawal_store, hypothesis_id="hyp-tc10b")
+    records, _errors = withdrawal_store.list()
+    assert len(records) == 1  # still exactly one -- the second attempt wrote nothing
+
+
+# === TC-11: accrual fold matches a hand-counted value from a populated fixture corpus =================
+
+
+def test_tc11_accrual_matches_a_hand_counted_value_over_two_distinct_setup_side_cells(stores):
+    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
+    hyp_a = _estimand_a_payload(
+        "hyp-tc11-cap", "fam-tc11-cap", setup_id="capitulation", side="long"
+    )
+    hyp_b = _estimand_a_payload(
+        "hyp-tc11-jbe", "fam-tc11-jbe", setup_id="jbe", side="long", primary_horizon="1h",
+        primary_measure_key="1h",
+    )
+    register_hypothesis(family_store, hypothesis_store, hyp_a, confirm=True)
+    register_hypothesis(family_store, hypothesis_store, hyp_b, confirm=True)
+
+    # Pre-boundary (2026-06-10): must NEVER count, regardless of cell match.
+    _plant_playbook_signals(playbook_store, "2026-06-09", [_signal("capitulation", "long")])
+    # Post-boundary, both cells present the same date.
+    _plant_playbook_signals(
+        playbook_store, "2026-06-11",
+        [_signal("capitulation", "long"), _signal("jbe", "long")],
+    )
+    # Post-boundary, capitulation/long only.
+    _plant_playbook_signals(playbook_store, "2026-06-12", [_signal("capitulation", "long")])
+    # Post-boundary, capitulation/long only (a third date for this cell).
+    _plant_playbook_signals(playbook_store, "2026-06-16", [_signal("capitulation", "long")])
+    # Post-boundary, jbe/long only.
... [diff_bound] apps/backend/tests/test_referee_registry.py: 429 more diff lines omitted — Read the file for full detail
```
