# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/referee_registry.py b/apps/backend/app/research/referee_registry.py
index 9c12276..a05a622 100644
--- a/apps/backend/app/research/referee_registry.py
+++ b/apps/backend/app/research/referee_registry.py
@@ -1099,6 +1099,29 @@ def _corpus_session_span_days(newest_by_date: dict[str, dict]) -> int:
     return (latest - earliest).days + 1
 
 
+def _longest_zero_session_stretch(newest_by_date: dict[str, dict]) -> tuple[int, str, str]:
+    """goal-referee-iter-12 (J-11): the corpus's longest RECORDING gap -- the calendar days with
+    ZERO recorded sessions strictly between two CONSECUTIVE recorded ``session_date`` keys
+    (``(later - earlier).days - 1``), plus the two recorded dates immediately bounding it. Walks
+    the SAME sorted date keys ``_corpus_session_span_days`` already sorts (T-6's own
+    ``newest_by_date`` -- no second store scan, no second pooling walk). Fewer than two recorded
+    dates has no gap to measure: ``(0, "", "")``, the same empty-string discipline
+    ``accrual_basis``'s other date fields use on an empty/singleton corpus."""
+    if len(newest_by_date) < 2:
+        return 0, "", ""
+    dates = sorted(newest_by_date)
+    best_days = -1
+    best_start = ""
+    best_end = ""
+    for earlier, later in zip(dates, dates[1:]):
+        gap_days = (date.fromisoformat(later) - date.fromisoformat(earlier)).days - 1
+        if gap_days > best_days:
+            best_days = gap_days
+            best_start = earlier
+            best_end = later
+    return best_days, best_start, best_end
+
+
 def _starter_context_readiness(
     newest_by_date: dict[str, dict],
     config_fingerprint: str,
@@ -1168,7 +1191,21 @@ def shortlist_response(
     estimand-A candidates, against the real corpus), i.e. "ready now" for a wait that is really
     ``target_sessions`` post-boundary sessions away -- and counted historical observations as
     progress toward a confirmatory target, which the era's own "the historical atlas is exploratory
-    forever" anti-goal forbids."""
+    forever" anti-goal forbids.
+
+    goal-referee-iter-12 (J-11): ALSO serves ``accrual_basis`` (the corpus's own recorded-session
+    accounting -- first/last recorded date, calendar-day span, recorded vs. pooled-at-current-basis
+    session counts, and the longest zero-recorded-session gap) plus, per candidate, two fields
+    BESIDE (never replacing) ``accrual_rate_sessions_per_day``/``projected_days_to_target``:
+    ``informative_sessions_per_pooled_session`` (that candidate's own already-computed
+    ``n_sessions`` over ``accrual_basis.pooled_sessions_at_current_basis``) and
+    ``projected_pooled_sessions_to_target`` (``target_sessions`` over that rate). Both new
+    per-candidate fields reuse the SAME divide-by-zero discipline as the shipped pair (``0.0`` /
+    ``None``, never a ``ZeroDivisionError``) -- a raw calendar-day span silently includes stretches
+    with zero recorded trading sessions, inflating the shipped projection; this basis answers "how
+    many sessions has the corpus ACTUALLY recorded" instead. Purely a read-side planning disclosure
+    (docs/referee-statistical-spec.md Sec9 addendum): feeds no null, no test statistic, no p-value,
+    no BH denominator, no verdict, no gate, and adds no ``referee_parameters()`` entry."""
     readiness = playbook_occurrence_readiness(playbook_store, config_fingerprint)
     per_setup_side = {(cell["setup"], cell["side"]): cell for cell in readiness["per_setup_side"]}
 
@@ -1177,6 +1214,13 @@ def shortlist_response(
     corpus_span_days = _corpus_session_span_days(newest_by_date)
     context_resolver = BandMapResolver(bar_store, config, compute=False)
 
+    sorted_dates = sorted(newest_by_date)
+    corpus_first_session_date = sorted_dates[0] if sorted_dates else ""
+    corpus_last_session_date = sorted_dates[-1] if sorted_dates else ""
+    recorded_sessions_in_span = readiness["distinct_sessions"]
+    pooled_sessions_at_current_basis = recorded_sessions_in_span - len(readiness["stale_basis_dates"])
+    stretch_days, stretch_start, stretch_end = _longest_zero_session_stretch(newest_by_date)
+
     candidates = []
     for spec in REFEREE_STARTER_FAMILY_SHORTLIST:
         context_predicate = spec["context_predicate"]
@@ -1199,6 +1243,17 @@ def shortlist_response(
             spec["target_sessions"] / accrual_rate
             if accrual_rate > 0 else None
         )
+        # goal-referee-iter-12 (J-11): the SAME "from zero, never net of history" discipline
+        # above, applied to the recorded-session basis instead of the raw calendar-day one --
+        # divides this candidate's own ALREADY-computed n_sessions (never a fresh or
+        # differently-filtered recomputation) by the corpus-wide pooled_sessions_at_current_basis.
+        pooled_rate = (
+            n_sessions / pooled_sessions_at_current_basis
+            if pooled_sessions_at_current_basis > 0 else 0.0
+        )
+        projected_pooled_sessions = (
+            spec["target_sessions"] / pooled_rate if pooled_rate > 0 else None
+        )
         candidates.append(
             {
                 "candidate_id": spec["candidate_id"],
@@ -1219,6 +1274,8 @@ def shortlist_response(
                 "min_occurrences": spec["min_occurrences"],
                 "accrual_rate_sessions_per_day": accrual_rate,
                 "projected_days_to_target": projected_days,
+                "informative_sessions_per_pooled_session": pooled_rate,
+                "projected_pooled_sessions_to_target": projected_pooled_sessions,
             }
         )
     # goal-referee-iter-9 rider (closes iter-8 coherence-audit F1 WARN): `family_id`/`family_q`
@@ -1229,6 +1286,20 @@ def shortlist_response(
         "candidates": candidates,
         "family_id": REFEREE_STARTER_FAMILY_ID,
         "family_q": REFEREE_DEFAULT_Q,
+        # goal-referee-iter-12 (J-11): the corpus-honest accrual disclosure -- recorded/pooled
+        # session counts, span, and the longest zero-recorded-session gap. Zero on an empty corpus
+        # (never a crash): `_corpus_session_span_days`/`_longest_zero_session_stretch` already
+        # return 0/""/"" there, and `pooled_sessions_at_current_basis` is `0 - 0 == 0`.
+        "accrual_basis": {
+            "corpus_first_session_date": corpus_first_session_date,
+            "corpus_last_session_date": corpus_last_session_date,
+            "corpus_span_days": corpus_span_days,
+            "recorded_sessions_in_span": recorded_sessions_in_span,
+            "pooled_sessions_at_current_basis": pooled_sessions_at_current_basis,
+            "longest_zero_session_stretch_days": stretch_days,
+            "longest_zero_session_stretch_start": stretch_start,
+            "longest_zero_session_stretch_end": stretch_end,
+        },
     }
 
 
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 7d7217d..141a621 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -249,8 +249,19 @@ _PRICE_ARITHMETIC_FIELDS = (
     # shortlist candidate's live readiness (never divide/subtract these client-side; the backend
     # already served accrual_rate_sessions_per_day/projected_days_to_target as computed numbers)
     # and a registered hypothesis's discovery count (never combined with its accrual siblings).
-    r"|candidate\.(?:n|n_sessions|accrual_rate_sessions_per_day|projected_days_to_target)"
+    # goal-referee-iter-12 (J-11): widened for the TWO new per-candidate fields beside the shipped
+    # pair -- informative_sessions_per_pooled_session (API-only this iteration, no dedicated
+    # column yet, guarded here anyway per "every new served numeric joins this list") and
+    # projected_pooled_sessions_to_target (the new "Projected sessions" column).
+    r"|candidate\.(?:n|n_sessions|accrual_rate_sessions_per_day|projected_days_to_target"
+    r"|informative_sessions_per_pooled_session|projected_pooled_sessions_to_target)"
     r"|hyp\.discovery\.(?:n|n_sessions)"
+    # goal-referee-iter-12 (J-11): the Referee Registry section's own new accrual-basis line --
+    # accrualBasis.* (the RefereeRegistrySection's own local binding for `shortlist.accrual_basis`)
+    # -- a corpus-wide recorded/pooled session count or day-span must never be recombined
+    # client-side (e.g. a client-computed "stale share" or "days since last gap").
+    r"|accrualBasis\.(?:corpus_span_days|recorded_sessions_in_span|pooled_sessions_at_current_basis"
+    r"|longest_zero_session_stretch_days)"
     # goal-referee-iter-9 (J-08 rider): the Referee Registry section's own accrual numerics --
     # mirrors the existing `hyp.discovery.*` entry above (a "sessions accrued so far" readout is
     # the obvious client-side subtraction to reach for and the obvious thing to get wrong; the
@@ -583,6 +594,56 @@ def test_desk_page_price_arithmetic_guard_catches_referee_adjudications_and_runs
     ) is None
 
 
+def test_desk_page_price_arithmetic_guard_catches_accrual_basis_and_pooled_projection_arithmetic():
+    """goal-referee-iter-12 (J-11) counter-test: the extended guard catches arithmetic on the new
+    accrual-basis line's own `accrualBasis.*` bindings (corpus-wide recorded/pooled session counts
+    and the day span) and on the two new per-candidate fields
+    (`candidate.informative_sessions_per_pooled_session`/`candidate.projected_pooled_sessions_to_target`)
+    -- proving the widened `candidate.*` group and the new `accrualBasis.*` group each genuinely
+    catch a violation, not just list it (the "a lint that cannot fail proves nothing" precedent)."""
+    seeded_stale_share = (
+        "const stale = accrualBasis.recorded_sessions_in_span - "
+        "accrualBasis.pooled_sessions_at_current_basis;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_stale_share) is not None
+
+    seeded_pooled_rate = (
+        "const rate = accrualBasis.pooled_sessions_at_current_basis / accrualBasis.corpus_span_days;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_pooled_rate) is not None
+
+    seeded_gap_pct = (
+        "const share = accrualBasis.longest_zero_session_stretch_days / "
+        "accrualBasis.corpus_span_days;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_gap_pct) is not None
+
+    seeded_pooled_projection = (
+        "const soon = candidate.projected_pooled_sessions_to_target * 2;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_pooled_projection) is not None
+
+    seeded_pooled_rate_diff = (
+        "const gap = candidate.accrual_rate_sessions_per_day - "
+        "candidate.informative_sessions_per_pooled_session;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_pooled_rate_diff) is not None
+
+    # And the pattern does NOT over-match: rendering the basis line's fields as plain descriptive
+    # text, and the new column's value via the SAME null-guarded ternary the shipped "Projected
+    # days" column already uses, both stay clean.
+    assert _PRICE_ARITHMETIC_PATTERN.search(
+        "`${accrualBasis.recorded_sessions_in_span} recorded / "
+        "${accrualBasis.pooled_sessions_at_current_basis} pooled over "
+        "${accrualBasis.corpus_span_days}d`"
+    ) is None
+    assert _PRICE_ARITHMETIC_PATTERN.search(
+        "candidate.projected_pooled_sessions_to_target === null "
+        '? "—" '
+        ": candidate.projected_pooled_sessions_to_target.toFixed(0)"
+    ) is None
+
+
 # goal-playbook-iter-4 audit (F1): `base_lows_ascending` is ONE served field name carrying the
 # direction-appropriate triangle check underneath (non-decreasing LOWS for `jbe`, non-increasing
 # HIGHS for `dbi` -- see `desk_playbook_detect._base_lows_ascending`). The continuation geometry
diff --git a/apps/backend/tests/test_referee_registry.py b/apps/backend/tests/test_referee_registry.py
index 9eee4b2..3ff1a6c 100644
--- a/apps/backend/tests/test_referee_registry.py
+++ b/apps/backend/tests/test_referee_registry.py
@@ -11,6 +11,7 @@ re-implement anything ``PlaybookStore`` already owns."""
 from __future__ import annotations
 
 import datetime
+import pathlib
 import sys
 import zoneinfo
 
@@ -22,6 +23,7 @@ from app.config import CONFIG
 from app.main import app
 from app.research.bars import BarStore
 from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
+from app.research.referee_adjudicate import referee_parameters_hash
 from app.research.referee_null import REFEREE_NULL_TOD_SPEC_ID, REFEREE_TEST_PERM_SPEC_ID
 from app.research.referee_registry import (
     REFEREE_MIN_OCCURRENCES,
@@ -873,6 +875,185 @@ def test_shortlist_s4_s5_s6_readiness_reflects_the_at_wall_context_resolve(
     assert by_id["S-6"]["n"] == 1 and by_id["S-6"]["n_sessions"] == 1
 
 
+# === goal-referee-iter-12 (J-11): the accrual projection states its own basis =========================
+#
+# `accrual_basis` (corpus-honest recorded/pooled session accounting + the longest zero-session
+# recording gap) plus two per-candidate fields BESIDE (never replacing) the shipped
+# accrual_rate_sessions_per_day/projected_days_to_target pair. TC-1/TC-2/TC-4/TC-6 share one
+# fixture corpus (a deliberate multi-month gap, hand-computed numbers); TC-3 uses a SEPARATE empty
+# corpus (pooled_sessions_at_current_basis == 0, the genuine divide-by-zero risk).
+
+
+def _plant_gap_corpus(playbook_store: PlaybookStore) -> None:
+    """Six recorded sessions spanning 2026-01-05..2026-06-20 (167 calendar days inclusive) with a
+    deliberate 65-day zero-session gap between 2026-02-09 and 2026-04-16 (the days 2026-02-10..
+    2026-04-15 inclusive carry no recorded session -- TC-1's own literal example). Every session
+    plants exactly one capitulation:long signal (S-1's cell) -- never a jbe:long one, so S-2 stays
+    genuinely at zero throughout (TC-3's "a fixture candidate whose cell has zero occurrences
+    pooled at the current detector basis", the non-vacuous half, folded into the test below rather
+    than duplicated)."""
+    for session_date in (
+        "2026-01-05", "2026-01-20", "2026-02-09", "2026-04-16", "2026-05-01", "2026-06-20",
+    ):
+        _plant_playbook_signals(playbook_store, session_date, [_signal("capitulation", "long")])
+
+
+def test_tc1_tc2_tc6_accrual_basis_serves_hand_computed_span_and_longest_zero_session_gap(
+    stores, bar_store,
+):
+    """TC-1/TC-2: against the gap corpus, `accrual_basis`'s first/last recorded dates, span,
+    recorded/pooled session counts, and longest zero-session stretch (length + bounding dates) are
+    all hand-computed exact. TC-6 (folded in here rather than duplicated in its own test): the
+    shipped `accrual_rate_sessions_per_day`/`projected_days_to_target` stay byte-identical to their
+    pre-iteration formula against this SAME corpus."""
+    _fam, _hyp, _wd, _cert, playbook_store = stores
+    _plant_gap_corpus(playbook_store)
+
+    response = shortlist_response(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    basis = response["accrual_basis"]
+    assert basis["corpus_first_session_date"] == "2026-01-05"
+    assert basis["corpus_last_session_date"] == "2026-06-20"
+    assert basis["corpus_span_days"] == 167  # (2026-06-20 - 2026-01-05).days + 1, hand-counted
+    assert basis["recorded_sessions_in_span"] == 6  # six distinct recorded session dates
+    assert basis["pooled_sessions_at_current_basis"] == 6  # none stale -- all at the live basis
+    assert basis["longest_zero_session_stretch_days"] == 65  # 2026-02-10..2026-04-15 inclusive
+    assert basis["longest_zero_session_stretch_start"] == "2026-02-09"  # the recorded date BEFORE
+    assert basis["longest_zero_session_stretch_end"] == "2026-04-16"  # the recorded date AFTER
+
+    by_id = {c["candidate_id"]: c for c in response["candidates"]}
+    s1 = by_id["S-1"]  # capitulation:long -- every one of the six sessions
+    assert s1["n"] == 6 and s1["n_sessions"] == 6
+    # TC-6: the shipped pair, byte-identical to the pre-iteration formula
+    # (n_sessions / corpus_span_days, target_sessions / that rate).
+    assert s1["accrual_rate_sessions_per_day"] == pytest.approx(6 / 167)
+    assert s1["projected_days_to_target"] == pytest.approx(12 / (6 / 167))
+    # TC-4: the new recorded-session basis, hand-computed exact -- 6 own sessions over 6 pooled
+    # corpus-wide sessions is a clean 1.0, and 12 target sessions over a 1.0 rate is 12.0.
+    assert s1["informative_sessions_per_pooled_session"] == pytest.approx(1.0)
+    assert s1["projected_pooled_sessions_to_target"] == pytest.approx(12.0)
+
+    # TC-3 (the non-vacuous "zero occurrences pooled" half): S-2 (jbe:long) never fires in this
+    # corpus, so its rate is a genuine 0.0 against a NONEMPTY pooled-session denominator (6) --
+    # never a ZeroDivisionError -- and its projection is null.
+    s2 = by_id["S-2"]
+    assert s2["n"] == 0 and s2["n_sessions"] == 0
+    assert s2["informative_sessions_per_pooled_session"] == 0.0
+    assert s2["projected_pooled_sessions_to_target"] is None
+
+
+def test_tc3_zero_pooled_session_denominator_never_divides_by_zero(stores, bar_store):
+    """TC-3 (the genuine divide-by-zero-risk half) + the empty-corpus error case: an EMPTY corpus
+    has `pooled_sessions_at_current_basis == 0` -- every candidate's own
+    `informative_sessions_per_pooled_session` must read `0.0`, never raise, and every
+    `projected_pooled_sessions_to_target` must read `null`. Mirrors
+    `test_tc2_zero_jbe_long_signals_amid_a_nonempty_corpus_serves_zero_never_a_divide_by_zero`'s own
+    shipped-pair guard, at the corpus-wide denominator rather than one cell's numerator."""
+    _fam, _hyp, _wd, _cert, playbook_store = stores  # empty -- pooled_sessions_at_current_basis == 0
+    response = shortlist_response(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    basis = response["accrual_basis"]
+    assert basis["pooled_sessions_at_current_basis"] == 0
+    assert basis["corpus_first_session_date"] == ""
+    assert basis["corpus_last_session_date"] == ""
+    assert basis["corpus_span_days"] == 0
+    assert basis["recorded_sessions_in_span"] == 0
+    assert basis["longest_zero_session_stretch_days"] == 0
+    assert basis["longest_zero_session_stretch_start"] == ""
+    assert basis["longest_zero_session_stretch_end"] == ""
+    for candidate in response["candidates"]:
+        assert candidate["informative_sessions_per_pooled_session"] == 0.0
+        assert candidate["projected_pooled_sessions_to_target"] is None
+
+
+def test_tc5_shortlist_accrual_basis_is_byte_identical_across_two_back_to_back_calls(
+    stores, bar_store,
+):
+    """TC-5: two calls against the SAME stores with no write between them serve byte-identical
+    bodies, including every new field -- no wall-clock, no unseeded randomness anywhere in this
+    read-side fold."""
+    _fam, _hyp, _wd, _cert, playbook_store = stores
+    _plant_gap_corpus(playbook_store)
+    kwargs = dict(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    first = shortlist_response(**kwargs)
+    second = shortlist_response(**kwargs)
+    assert first == second
+
+
+def test_tc7_shortlist_adds_no_new_store_scan_and_keeps_band_map_resolver_compute_false(
+    stores, bar_store, monkeypatch,
+):
+    """TC-7: this iteration's new fields are computed from data `shortlist_response()` ALREADY
+    scans -- proven by wrapping `PlaybookStore.list` with a counting wrapper and asserting the call
+    count stays at its PRE-ITERATION baseline of 2 (one inside `playbook_occurrence_readiness()`,
+    one direct call the function already made) rather than growing to 3. Also proves
+    `BandMapResolver` is still constructed `compute=False` -- a RECORDED-band-map lookup, never a
+    fresh compute (T-8), unchanged by this iteration."""
+    _fam, _hyp, _wd, _cert, playbook_store = stores
+    _plant_gap_corpus(playbook_store)
+
+    real_list = PlaybookStore.list
+    call_count = {"n": 0}
+
+    def _counting_list(self):
+        call_count["n"] += 1
+        return real_list(self)
+
+    monkeypatch.setattr(PlaybookStore, "list", _counting_list)
+
+    resolver_kwargs: list[dict] = []
+    real_resolver_cls = referee_registry_module.BandMapResolver
+
+    def _spy_resolver(*args, **kwargs):
+        resolver_kwargs.append(kwargs)
+        return real_resolver_cls(*args, **kwargs)
+
+    monkeypatch.setattr(referee_registry_module, "BandMapResolver", _spy_resolver)
+
+    shortlist_response(
+        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store=bar_store, config=CONFIG,
+    )
+    assert call_count["n"] == 2  # unchanged from the pre-iteration baseline -- no third scan added
+    assert len(resolver_kwargs) == 1
+    assert resolver_kwargs[0]["compute"] is False
+
+
+def test_tc8_referee_parameters_served_json_is_unchanged_by_this_iteration():
+    """TC-8 (the `referee_parameters()` half): J-11 adds zero `referee_parameters()` entries --
+    pinned against the exact pre-iteration content hash (mirrors the `Config().config_fingerprint()`
+    `08e471b10130e1e2` pin idiom). A future accidental entry here would move this hash and fail
+    loudly, exactly like a fingerprint-pin regression would."""
+    assert referee_parameters_hash() == "0976d49e3e4583b5"
+
+
+def test_tc17_the_statistical_spec_carries_the_iter12_accrual_addendum():
+    """TC-17: docs/referee-statistical-spec.md Sec9 carries a dated, named addendum paragraph
+    stating the accrual projection is a read-side planning disclosure no statistical procedure
+    consumes, with both bases (calendar-day and recorded-session) served side by side rather than
+    one replacing the other."""
+    spec_path = (
+        pathlib.Path(__file__).resolve().parents[3] / "docs" / "referee-statistical-spec.md"
+    )
+    # Normalized (whitespace/newlines collapsed to single spaces) so this assertion is immune to
+    # the prose's own line-wrap width -- it checks CONTENT, never markdown formatting.
+    text = " ".join(spec_path.read_text().split())
+    assert "goal-referee-iter-12" in text  # the dated, named revision marker
+    assert "2026-08-16" in text
+    assert "read-side planning disclosure" in text.lower()
+    assert "side by side" in text.lower()  # both bases served together -- neither replaces the other
+    # explicitly denies feeding any confirmatory machinery, echoing goal.md's own J-11 Step 2.
+    assert "neither feeds any null, test statistic, p-value, BH denominator, verdict, or gate" in text
+    assert "neither is a `referee_parameters()` entry" in text
+
+
 # === TC-9 / TC-10 (iter-8): the write path stays generic; discovery is boundary-gated on
 # session_date, never recorded_at ======================================================================
 
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index ce1cf23..3771424 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -4736,6 +4736,9 @@ function RefereeRegistrySection({
     );
   }
   const shortlist = shortlistResult.data;
+  // goal-referee-iter-12 (J-11): the corpus-honest accrual disclosure -- read verbatim, zero
+  // client-side arithmetic (referee_registry.py::shortlist_response() computes every field once).
+  const accrualBasis = shortlist.accrual_basis;
   const registeredIds = new Set(
     registryResult.ok && registryResult.data
       ? registryResult.data.hypotheses.map((h) => h.hypothesis_id)
@@ -4752,6 +4755,39 @@ function RefereeRegistrySection({
         hypothesis — historical observations before that boundary are discovery, never
         confirmation.
       </p>
+      <div
+        data-testid="referee-accrual-basis-line"
+        className="mb-3 rounded-md border border-slate-800 bg-slate-900/40 px-3 py-2 text-xs text-slate-400"
+      >
+        {accrualBasis.corpus_first_session_date === "" ? (
+          <span>No sessions recorded yet.</span>
+        ) : (
+          <span>
+            Recorded sessions{" "}
+            <span className="font-mono text-slate-300">
+              {accrualBasis.recorded_sessions_in_span}
+            </span>
+            {" · "}pooled at the current detector basis{" "}
+            <span className="font-mono text-slate-300">
+              {accrualBasis.pooled_sessions_at_current_basis}
+            </span>
+            {" · "}corpus span{" "}
+            <span className="font-mono text-slate-300">{accrualBasis.corpus_span_days}</span>d (
+            {accrualBasis.corpus_first_session_date} {"→"} {accrualBasis.corpus_last_session_date})
+            {" · "}longest zero-session stretch{" "}
+            <span className="font-mono text-slate-300">
+              {accrualBasis.longest_zero_session_stretch_days}
+            </span>
+            d
+            {accrualBasis.longest_zero_session_stretch_start !== "" && (
+              <>
+                {" "}({accrualBasis.longest_zero_session_stretch_start} {"→"}{" "}
+                {accrualBasis.longest_zero_session_stretch_end})
+              </>
+            )}
+          </span>
+        )}
+      </div>
       <div className="overflow-x-auto">
         <table
           data-testid="referee-shortlist-table"
@@ -4768,6 +4804,7 @@ function RefereeRegistrySection({
               <th className="px-1.5 py-1 text-right">Sessions</th>
               <th className="px-1.5 py-1 text-right">Accrual / day</th>
               <th className="px-1.5 py-1 text-right">Projected days</th>
+              <th className="px-1.5 py-1 text-right">Projected sessions</th>
               <th className="px-1.5 py-1 text-center">Action</th>
             </tr>
           </thead>
@@ -4802,6 +4839,14 @@ function RefereeRegistrySection({
                       ? "—"
                       : candidate.projected_days_to_target.toFixed(0)}
                   </td>
+                  <td
+                    data-testid={`referee-shortlist-projected-pooled-${candidate.candidate_id}`}
+                    className="px-1.5 py-1.5 text-right font-mono text-slate-300"
+                  >
+                    {candidate.projected_pooled_sessions_to_target === null
+                      ? "—"
+                      : candidate.projected_pooled_sessions_to_target.toFixed(0)}
+                  </td>
                   <td className="px-1.5 py-1.5 text-center">
                     <button
                       type="button"
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 8fd875d..55054f1 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2154,6 +2154,29 @@ export interface RefereeShortlistCandidate {
   accrual_rate_sessions_per_day: number;
   // `null` only when `accrual_rate_sessions_per_day` is 0 -- never a divide-by-zero value.
   projected_days_to_target: number | null;
+  // goal-referee-iter-12 (J-11): BESIDE (never replacing) the calendar-day pair above -- the SAME
+  // rate/projection shape measured against the corpus's own recorded-session basis
+  // (`accrual_basis.pooled_sessions_at_current_basis`) instead of a raw calendar-day span. `0.0`
+  // when the denominator (the corpus-wide pooled-session count) is 0 -- never a divide-by-zero
+  // value; `projected_pooled_sessions_to_target` is `null` in that same case.
+  informative_sessions_per_pooled_session: number;
+  projected_pooled_sessions_to_target: number | null;
+}
+
+// goal-referee-iter-12 (J-11): the corpus's own recorded-session accounting -- a read-side
+// planning disclosure (docs/referee-statistical-spec.md Sec9 addendum) no statistical procedure
+// consumes. `corpus_span_days` is byte-identical to the value the shipped
+// `accrual_rate_sessions_per_day` already divides by; the four session-date/count fields read ""
+// / `0` on an empty corpus, never a crash.
+export interface RefereeAccrualBasis {
+  corpus_first_session_date: string;
+  corpus_last_session_date: string;
+  corpus_span_days: number;
+  recorded_sessions_in_span: number;
+  pooled_sessions_at_current_basis: number;
+  longest_zero_session_stretch_days: number;
+  longest_zero_session_stretch_start: string;
+  longest_zero_session_stretch_end: string;
 }
 
 // goal-referee-iter-9 rider: `family_id`/`family_q` are the starter family's own
@@ -2163,6 +2186,9 @@ export interface RefereeShortlistResponse {
   candidates: RefereeShortlistCandidate[];
   family_id: string;
   family_q: number;
+  // goal-referee-iter-12 (J-11): the accrual-basis disclosure, computed once inside
+  // shortlist_response()'s existing single store scan (referee_registry.py) -- no second owner.
+  accrual_basis: RefereeAccrualBasis;
 }
 
 // The read-side fold additions GET /research/desk/referee/registry adds to every hypothesis
diff --git a/docs/referee-statistical-spec.md b/docs/referee-statistical-spec.md
index 74fb279..3fa3efc 100644
--- a/docs/referee-statistical-spec.md
+++ b/docs/referee-statistical-spec.md
@@ -377,3 +377,16 @@ sample reality in view.
 7. **The forming-bar caveat (Card 6.4)** applies to structure/strategy-family measurement
    bases and is stamped as `basis_caveats`; it does not touch Playbook context (recorded
    band maps) or these tests' validity.
+8. **(2026-08-16 addendum, goal-referee-iter-12, J-11) The accrual projection is a read-side
+   planning disclosure, not a statistical procedure.** The starter-family shortlist's shipped
+   `accrual_rate_sessions_per_day`/`projected_days_to_target` divide a candidate's recorded
+   sessions by the corpus's raw CALENDAR-day span (`corpus_span_days`), which can silently
+   include stretches with zero recorded trading sessions — a multi-month recording gap inflates
+   that projected wait. This addendum adds a second basis measured in RECORDED sessions instead
+   of calendar days (`accrual_basis`'s `recorded_sessions_in_span`/
+   `pooled_sessions_at_current_basis`/longest zero-session stretch, plus each candidate's own
+   `informative_sessions_per_pooled_session`/`projected_pooled_sessions_to_target`), served SIDE
+   BY SIDE with the calendar-day pair — neither basis ever replaces the other. Both bases are
+   pure read-side arithmetic over already-recorded facts: neither feeds any null, test statistic,
+   p-value, BH denominator, verdict, or gate, and neither is a `referee_parameters()` entry — the
+   spec's estimands, tests, and verdict rules (Sec3-Sec5) are unchanged by this addendum.
```
