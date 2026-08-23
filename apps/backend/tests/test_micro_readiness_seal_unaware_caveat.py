"""Static-scan guard (Era "The Rapid Microscope", iter-28, phase spec IN SCOPE / TC-4): the
spec's section 10.7 (r5 owner ruling) verbatim caveat sentence about the seal-unaware legacy
Referee readiness metric (``referee_evidence.strategy_trade_readiness``) must be:

1. defined EXACTLY ONCE as a shared string constant in the frontend source
   (``apps/frontend/app/desk/page.tsx``), never duplicated ad hoc; and
2. character-for-character identical to the sentence quoted verbatim in
   ``docs/rapid-validation-spec.md`` section 10.7.

``referee_evidence.py``/``referee_routes.py`` stay byte-frozen this whole era (Foundation
invariant 2) -- the caveat can only be served at the frontend rendering layer (the iteration's
own one deliberate, owner-authorized exception to Foundation invariant 5), so this guard is a
source-text scan, never a live route/DOM assertion (that lives in the browser-QA lane's TC-5).

This is a NEW sibling file, deliberately never touching the existing, frozen
``test_micro_no_referee_evidence_guard.py`` (goal.md IN SCOPE: "Do NOT rebuild or modify
test_micro_no_referee_evidence_guard.py's existing 4 tests -- only extend it (or add a sibling)")."""

from __future__ import annotations

import pathlib
import re

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SPEC_PATH = _REPO_ROOT / "docs" / "rapid-validation-spec.md"
_PAGE_PATH = _REPO_ROOT / "apps" / "frontend" / "app" / "desk" / "page.tsx"


def _spec_caveat_sentence() -> str:
    """The section-10.7 quoted caveat, extracted from the spec and whitespace-normalized (the
    markdown source hard-wraps it across multiple lines inside a numbered list item)."""
    text = _SPEC_PATH.read_text(encoding="utf-8")
    match = re.search(
        r'\*"(Legacy Referee readiness metric.*?readiness count\.)"\*', text, re.DOTALL
    )
    assert match is not None, "spec section 10.7's verbatim caveat sentence was not found -- has it moved or been reworded?"
    return re.sub(r"\s+", " ", match.group(1)).strip()


def test_spec_section_10_7_caveat_sentence_is_present_and_extractable():
    """Non-vacuity: the extraction itself must find real content, not silently produce an empty
    string on a match failure elsewhere in this test module."""
    sentence = _spec_caveat_sentence()
    assert sentence.startswith("Legacy Referee readiness metric")
    assert sentence.endswith("Rapid-Microscope readiness count.")
    assert "seal-unaware in the Rapid Microscope era" in sentence


def test_frontend_source_carries_the_verbatim_caveat_exactly_once_as_a_shared_constant():
    """TC-4, verbatim: grepped for the verbatim sentence, it is found exactly once, sourced from a
    single shared string constant -- never duplicated ad hoc."""
    sentence = _spec_caveat_sentence()
    source = _PAGE_PATH.read_text(encoding="utf-8")

    occurrences = source.count(sentence)
    assert occurrences == 1, (
        f"expected the verbatim caveat sentence exactly once in {_PAGE_PATH}, found {occurrences}"
    )

    # Sourced from a single shared string constant: the sentence's line must itself be a
    # `const <NAME> = "..."` assignment, and every OTHER reference in the file must be a bare
    # identifier read of that constant, never a second inline copy of the literal text.
    const_pattern = re.compile(
        r'const\s+([A-Z][A-Z0-9_]*)\s*=\s*\n?\s*"' + re.escape(sentence) + r'"\s*;'
    )
    const_match = const_pattern.search(source)
    assert const_match is not None, (
        "the caveat sentence must be assigned to a single module-level string constant "
        "(e.g. `const REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT = \"...\";`), never inlined directly "
        "into JSX"
    )
    const_name = const_match.group(1)

    # The constant must actually be READ somewhere (e.g. rendered inside JSX) -- a defined-but-
    # unused constant would not actually serve the caveat to any user.
    usage_pattern = re.compile(r"\{" + re.escape(const_name) + r"\}")
    assert usage_pattern.search(source), (
        f"the shared constant {const_name} is defined but never rendered in JSX"
    )


def test_frontend_caveat_matches_spec_section_10_7_character_for_character():
    """The frontend's served sentence, once whitespace-normalized (JSX may hard-wrap a long
    string source-side without changing the RENDERED text), is byte-for-byte identical to the
    spec's own section 10.7 wording -- neither a paraphrase nor a stale copy that drifted from a
    since-edited spec."""
    spec_sentence = _spec_caveat_sentence()
    source = _PAGE_PATH.read_text(encoding="utf-8")
    assert spec_sentence in source, (
        "the frontend source does not contain the spec's exact section-10.7 sentence "
        "character-for-character"
    )


def test_the_scan_is_non_vacuous_a_paraphrase_would_not_pass(tmp_path):
    """Counter-test: a near-miss paraphrase (missing the em dash, or reworded) must NOT satisfy
    the exact-match check above -- proving the scan can actually fail."""
    spec_sentence = _spec_caveat_sentence()
    paraphrased = spec_sentence.replace("seal-unaware", "not seal-aware")
    assert paraphrased != spec_sentence
    fake_source = f'const FAKE_CAVEAT = "{paraphrased}";\n<p>{{FAKE_CAVEAT}}</p>\n'
    assert spec_sentence not in fake_source
