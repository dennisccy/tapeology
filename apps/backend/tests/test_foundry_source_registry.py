"""``foundry_source_registry.py`` -- the Hypothesis Foundry's source registry (goal-hypothesis-
foundry-iter-1). Test-first contract: TC-5 through TC-9 and TC-12/TC-13 in
``docs/phases/goal-hypothesis-foundry-iter-1.md`` (the blocked/aliased/proxy dispositions, the
exact-quote lint, and the era-open baseline snapshot). ``test_foundry_compiler.py`` covers TC-3/
TC-4/TC-10/TC-11 (the compileable/family/hash cases), since those need the compiler module too.

Fixtures cover exactly the seven hermetic source archetypes ``docs/goal.md`` J-02 step 2 names.
Each fixture's ``source_excerpt``/``quoted_spans`` are deliberately synthetic sentences invented
for this test -- never real ratified repository text -- since J-02 step 2 explicitly scopes this
iteration to compiler-RULE machinery proven on hermetic fixtures, not the real 11 required source
objects (that is J-06).

TC-10 (``docs/phases/goal-hypothesis-foundry-iter-3.md``) covers the ``source_hash``/
``alternatives`` fields added this iteration; the two-frozen-legal-variant ``alternatives`` case
(TC-11) lives in ``test_foundry_compiler.py`` beside the fixture pair it extends."""

from __future__ import annotations

import json

import pytest

from app.research import foundry_source_registry as fsr


def _span(text: str, excerpt: str) -> fsr.QuotedSpan:
    """A ``QuotedSpan`` located at ``text``'s real offset inside ``excerpt`` -- computed, never
    hand-counted, so a fixture's own wording can change without silently mis-locating the span."""
    return fsr.QuotedSpan(text=text, location=excerpt.index(text))


# --- TC-3 (compileable natural-boundary scalar) is exercised in test_foundry_compiler.py, since
# it also needs a CandidateBlueprint. This file keeps the disposition-only half of that fixture
# for the registry-level assertions (TC-13-adjacent: disposition alone, no CandidateSpec). -------


def test_natural_boundary_scalar_compiles():
    excerpt = "A signed variable's zero boundary is bid-heavy when quote_imbalance is positive."
    span_text = "signed variable's zero boundary is bid-heavy when quote_imbalance is positive"
    record = fsr.SourceRecord(
        source_id="fixture-natural-boundary",
        source_path="docs/fixtures/mechanism.md",
        section_ref="2.3",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="quote imbalance zero-crossing implies bid-heavy",
        operative_formula_refs=("quote_imbalance",),
        direction_derivation="positive quote_imbalance implies bid-heavy -> long",
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="zero boundary intrinsic to the signed variable's own definition, per quoted text",
        threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
    )
    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_COMPILED


# --- TC-5: unresolved magnitude word -> BLOCKED_SPEC_GAP, disposition only (no CandidateSpec). ---


def test_unresolved_magnitude_word_blocks_spec_gap():
    excerpt = "A collapse in impact defines a high-aggression signal at the wall."
    span_text = "collapse in impact defines a high-aggression signal"
    record = fsr.SourceRecord(
        source_id="fixture-magnitude-word",
        source_path="docs/fixtures/mechanism.md",
        section_ref="1.9",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="impact collapse at the wall implies reversal",
        operative_formula_refs=("impact_efficiency",),
        direction_derivation="collapse implies reversal -> long",
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="'collapse'/'high' are undefined magnitude words -- no ratified numeric meaning exists",
        unresolved_magnitude_words=("collapse", "high"),
    )
    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_BLOCKED_SPEC_GAP


# --- TC-6: proxy-only -> ALIASED_PROXY_ONLY, do_not preserved. -----------------------------------


def test_proxy_only_source_aliases_and_preserves_do_not():
    excerpt = "The frozen pilot proxy stands in for Study 1's impact_efficiency mechanism."
    span_text = "frozen pilot proxy stands in for Study 1's impact_efficiency mechanism"
    record = fsr.SourceRecord(
        source_id="fixture-proxy",
        source_path="docs/fixtures/mechanism.md",
        section_ref="1.1-proxy",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="pilot proxy candidate request for Study 1",
        operative_formula_refs=("impact_efficiency_pilot_proxy",),
        direction_derivation="long",
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="a frozen pilot proxy is provenance only, never the full mechanism",
        proxy_of=fsr.ProxyDeclaration(
            parked_study_source_id="study-1-range-wall-failed-aggression",
            do_not="do_not_claim_full_study_1_mechanism",
        ),
    )
    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_ALIASED_PROXY_ONLY
    assert record.proxy_of.do_not == "do_not_claim_full_study_1_mechanism"


# --- TC-7: unsupported statistic -> BLOCKED_UNSUPPORTED_STUDY_FORM. ------------------------------


def test_unsupported_statistic_blocks_study_form():
    excerpt = "A shuffled-side persistence statistic is not a supported Scout study form here."
    span_text = "shuffled-side persistence statistic is not a supported Scout study form"
    record = fsr.SourceRecord(
        source_id="fixture-unsupported-stat",
        source_path="docs/fixtures/mechanism.md",
        section_ref="9.6",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="shuffled-side persistence statistic",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation=fsr.BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL,
        audit_note="the existing Scout screen has no shuffled-side permutation null; unsupported study form",
    )
    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM


# --- TC-8: alias/supersession -> ALIASED_VARIANT_VOCABULARY (or ALIASED_LINEAGE), superseded_fields
# cite the newer ref. -------------------------------------------------------------------------


def test_alias_supersession_cites_the_newer_ref():
    excerpt = "Card 9.7 event-time windows are now embodied by the current frozen feature windows."
    span_text = "event-time windows are now embodied by the current frozen feature windows"
    record = fsr.SourceRecord(
        source_id="fixture-alias-older",
        source_path="docs/fixtures/mechanism.md",
        section_ref="9.7",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="event-time feature windows",
        operative_formula_refs=("event_time_window",),
        direction_derivation="long",
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="Card 9.7 is variant vocabulary for an already-frozen current feature window, per §1.3",
        superseded_fields={"event_time_window": "docs/rapid-validation-spec.md#feature-windows"},
        supersession=fsr.SupersessionDeclaration(
            newer_source_ref="docs/rapid-validation-spec.md#feature-windows",
            alias_kind=fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY,
        ),
    )
    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY
    assert record.superseded_fields["event_time_window"] == "docs/rapid-validation-spec.md#feature-windows"


def test_alias_supersession_may_select_lineage_instead():
    record = fsr.SourceRecord(
        source_id="fixture-alias-lineage",
        source_path="docs/fixtures/mechanism.md",
        section_ref="9.4",
        quoted_spans=(),
        source_excerpt="",
        mechanism_statement="burst/climax lineage",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="distinct lineage id, same underlying exhaustion mechanism as Study 3",
        supersession=fsr.SupersessionDeclaration(
            newer_source_ref="study-3-capitulation-exhaustion", alias_kind=fsr.DISPOSITION_ALIASED_LINEAGE
        ),
    )
    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_ALIASED_LINEAGE


def test_supersession_alias_kind_rejects_a_non_alias_disposition():
    with pytest.raises(ValueError):
        fsr.SupersessionDeclaration(newer_source_ref="x", alias_kind=fsr.DISPOSITION_COMPILED)


# --- TC-9: directionless mechanism -> BLOCKED_DIRECTION. -----------------------------------------


def test_directionless_mechanism_blocks_direction():
    excerpt = "The mechanism describes co-occurrence with no stated directional implication."
    span_text = "co-occurrence with no stated directional implication"
    record = fsr.SourceRecord(
        source_id="fixture-directionless",
        source_path="docs/fixtures/mechanism.md",
        section_ref="9.5",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="spread-dynamics regime co-occurrence",
        operative_formula_refs=("spread_regime",),
        direction_derivation=fsr.BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement_within_same_eligible_population",
        audit_note="the quoted text states co-occurrence only; no mechanical long/short implication exists",
    )
    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_BLOCKED_DIRECTION


# --- TC-12: exact-quote lint fails closed on a mismatched span; passes over correct ones. --------


def _good_record(source_id: str) -> fsr.SourceRecord:
    excerpt = f"{source_id}: the quoted span below exists verbatim in this excerpt."
    span_text = "the quoted span below exists verbatim in this excerpt"
    return fsr.SourceRecord(
        source_id=source_id,
        source_path="docs/fixtures/mechanism.md",
        section_ref="0",
        quoted_spans=(_span(span_text, excerpt),),
        source_excerpt=excerpt,
        mechanism_statement="m",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="note",
    )


def test_lint_passes_over_exact_spans():
    fsr.lint_quoted_spans([_good_record("a"), _good_record("b")])  # must not raise


def test_lint_fails_closed_on_a_mismatched_span():
    bad = fsr.SourceRecord(
        source_id="fixture-bad-quote",
        source_path="docs/fixtures/mechanism.md",
        section_ref="0",
        quoted_spans=(fsr.QuotedSpan(text="says Y", location=4),),
        source_excerpt="The real text says X.",
        mechanism_statement="m",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="note",
    )
    with pytest.raises(fsr.QuoteMismatch):
        fsr.lint_quoted_spans([_good_record("a"), bad])


def test_lint_fails_closed_on_correct_text_at_the_wrong_location():
    """The text matches SOMEWHERE in the excerpt but not at the recorded offset -- must still
    fail (never a "appears anywhere" fallback, per the module's own "deliberately does not use
    keyword matching" rule)."""
    excerpt = "wrong here, right over there: right"
    bad = fsr.SourceRecord(
        source_id="fixture-wrong-location",
        source_path="docs/fixtures/mechanism.md",
        section_ref="0",
        quoted_spans=(fsr.QuotedSpan(text="right", location=0),),
        source_excerpt=excerpt,
        mechanism_statement="m",
        operative_formula_refs=(),
        direction_derivation="long",
        comparator_derivation="complement",
        audit_note="note",
    )
    with pytest.raises(fsr.QuoteMismatch):
        fsr.lint_quoted_spans([bad])


# --- Illegal threshold_provenance is refused at construction, never silently accepted. -----------


def test_illegal_threshold_provenance_is_refused_at_construction():
    with pytest.raises(ValueError):
        fsr.SourceRecord(
            source_id="fixture-illegal-threshold",
            source_path="docs/fixtures/mechanism.md",
            section_ref="0",
            quoted_spans=(),
            source_excerpt="",
            mechanism_statement="m",
            operative_formula_refs=(),
            direction_derivation="long",
            comparator_derivation="complement",
            audit_note="note",
            threshold_provenance="an_invented_fourth_category",
        )


def test_explicit_exclusion_must_be_a_closed_vocabulary_member():
    with pytest.raises(ValueError):
        fsr.SourceRecord(
            source_id="fixture-illegal-exclusion",
            source_path="docs/fixtures/mechanism.md",
            section_ref="0",
            quoted_spans=(),
            source_excerpt="",
            mechanism_statement="m",
            operative_formula_refs=(),
            direction_derivation="long",
            comparator_derivation="complement",
            audit_note="note",
            explicit_exclusion="NOT_A_REAL_DISPOSITION",
        )


def test_explicit_exclusion_short_circuits_every_other_rule():
    """A source explicitly marked excluded reaches its exclusion disposition even if it ALSO
    carries fields that would otherwise block/alias it -- exclusion is decided first (§2's fixed
    precedence, step 0)."""
    record = fsr.SourceRecord(
        source_id="fixture-excluded",
        source_path="docs/fixtures/mechanism.md",
        section_ref="9.1",
        quoted_spans=(),
        source_excerpt="",
        mechanism_statement="m",
        operative_formula_refs=(),
        direction_derivation=fsr.BLOCKED_DIRECTION_SENTINEL,
        comparator_derivation="complement",
        audit_note="Card 9.1/Study 2 was previously killed -- may not be recompiled",
        explicit_exclusion=fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
    )
    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED


# --- The closed vocabulary itself. ----------------------------------------------------------------


def test_disposition_vocabulary_is_exactly_fourteen_members():
    assert len(fsr.SOURCE_DISPOSITIONS) == 14
    for name in (
        "COMPILED", "ALIASED_PROXY_ONLY", "ALIASED_VARIANT_VOCABULARY", "ALIASED_LINEAGE",
        "EXCLUDED_PREVIOUSLY_KILLED", "EXCLUDED_PREREQUISITE_UNMET", "EXCLUDED_GATE_CLOSED",
        "BLOCKED_SPEC_GAP", "BLOCKED_MISSING_PRIMITIVE", "BLOCKED_UNSUPPORTED_STUDY_FORM",
        "BLOCKED_UNSUPPORTED_RELATION", "BLOCKED_DIRECTION", "BLOCKED_VARIANT_EXPLOSION",
        "BLOCKED_UNIT_CONTRACT",
    ):
        assert name in fsr.SOURCE_DISPOSITIONS


# --- source_registry_hash: content-sensitive, order-invariant, excludes `extra`. -----------------


def test_source_registry_hash_changes_when_a_record_changes():
    import dataclasses

    a = _good_record("a")
    b = _good_record("b")
    hash_ab = fsr.source_registry_hash([a, b])
    b_mutated = dataclasses.replace(b, mechanism_statement="a different mechanism entirely")
    hash_ab_mutated = fsr.source_registry_hash([a, b_mutated])
    assert hash_ab != hash_ab_mutated


def test_source_registry_hash_ignores_extra_field():
    import dataclasses

    a = _good_record("a")
    a_extra = dataclasses.replace(a, extra={"effect_bps": 99.0, "p_value": 0.0001, "n": 10_000})
    assert fsr.source_registry_hash([a]) == fsr.source_registry_hash([a_extra])


# --- Era-open baseline: recorded once, served verbatim, never recomputed on read. ----------------


def test_era_open_baseline_round_trips_byte_identically_across_two_reads(tmp_path):
    foundry_dir = tmp_path / "foundry"
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    for name in fsr.REFEREE_MODULES:
        (research_dir / name).write_text(f"# fixture stand-in for {name}\n", encoding="utf-8")

    recorded = fsr.record_era_open_baseline(
        foundry_dir,
        suite_passed=3762,
        suite_skipped=8,
        suite_failed=0,
        tsc_error_count=0,
        config_fingerprint="08e471b10130e1e2",
        research_dir=research_dir,
    )
    assert recorded["backend_suite"] == {"passed": 3762, "skipped": 8, "failed": 0}
    assert recorded["config_fingerprint"] == "08e471b10130e1e2"
    assert set(recorded["referee_module_sha256"]) == set(fsr.REFEREE_MODULES)

    first_read = fsr.read_era_open_baseline(foundry_dir)
    second_read = fsr.read_era_open_baseline(foundry_dir)
    assert first_read == second_read == recorded
    # Byte-identical on-disk persistence too (TC-13: "serve byte-identically with no recomputation
    # between calls") -- re-serializing the read-back dict reproduces the same bytes.
    assert json.dumps(first_read, sort_keys=True) == json.dumps(second_read, sort_keys=True)


def test_era_open_baseline_read_before_any_recording_is_none_never_fabricated(tmp_path):
    assert fsr.read_era_open_baseline(tmp_path / "never-recorded") is None


def test_era_open_baseline_hashes_a_real_referee_module_file(tmp_path):
    """Uses the REAL ``app/research`` directory (not a fixture stand-in) so the recorded hash is
    the actual current ``referee_registry.py`` content -- proves this isn't a fabricated digest."""
    import hashlib
    from pathlib import Path

    research_dir = Path(__file__).resolve().parent.parent / "app" / "research"
    foundry_dir = tmp_path / "foundry"
    recorded = fsr.record_era_open_baseline(
        foundry_dir, suite_passed=1, suite_skipped=0, suite_failed=0, tsc_error_count=0,
        config_fingerprint="x", research_dir=research_dir,
    )
    expected = hashlib.sha256((research_dir / "referee_registry.py").read_bytes()).hexdigest()
    assert recorded["referee_module_sha256"]["referee_registry.py"] == expected


def test_resolve_foundry_dir_env_override(monkeypatch, tmp_path):
    override = str(tmp_path / "custom-foundry-dir")
    monkeypatch.setenv("TAPEOLOGY_FOUNDRY_DIR", override)
    assert fsr.resolve_foundry_dir(str(tmp_path / "datasets")) == override


def test_resolve_foundry_dir_defaults_to_a_sibling_of_dataset_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("TAPEOLOGY_FOUNDRY_DIR", raising=False)
    dataset_dir = str(tmp_path / "datasets")
    assert fsr.resolve_foundry_dir(dataset_dir) == str(tmp_path / "foundry")


# --- TC-10 (goal-hypothesis-foundry-iter-3): source_hash == sha256(source_excerpt), recomputed --
# never caller-supplied -- so it can never drift from source_excerpt. -----------------------------


def test_tc10_source_hash_is_sha256_of_source_excerpt():
    import hashlib

    record = _good_record("hash-check")
    assert record.source_hash == hashlib.sha256(record.source_excerpt.encode("utf-8")).hexdigest()


def test_tc10_source_hash_changes_when_source_excerpt_changes():
    import dataclasses
    import hashlib

    record = _good_record("hash-mutation")
    original_hash = record.source_hash
    mutated = dataclasses.replace(record, source_excerpt=record.source_excerpt + " (a mutated tail)")
    assert mutated.source_hash != original_hash
    assert mutated.source_hash == hashlib.sha256(mutated.source_excerpt.encode("utf-8")).hexdigest()


def test_tc10_source_hash_is_not_a_constructor_parameter():
    """`source_hash` is `init=False` -- a caller cannot pass a value for it at all (it can only be
    derived), so a stale/forged hash can never be smuggled in at construction time."""
    import inspect

    assert "source_hash" not in inspect.signature(fsr.SourceRecord.__init__).parameters


# --- `alternatives` (goal-hypothesis-foundry-iter-3): defaults to empty; participates in the
# registry hash (real disclosure content, unlike the derived `source_hash`). --------------------


def test_alternatives_defaults_to_an_empty_tuple_when_no_ratified_alternative_exists():
    record = _good_record("no-alternative")
    assert record.alternatives == ()


def test_source_registry_hash_changes_when_alternatives_changes():
    import dataclasses

    record = _good_record("alt-hash")
    with_alt = dataclasses.replace(record, alternatives=("some-sibling-source-id",))
    assert fsr.source_registry_hash([record]) != fsr.source_registry_hash([with_alt])
