"""goal-referee-iter-1 (J-01) — two structural guard-test pins named verbatim in ``docs/goal.md``'s
J-01 acceptance and this iteration's spec (``docs/phases/goal-referee-iter-1.md`` TC-6/TC-7/TC-8):

(a) The ``playbook-band-context-v3`` spec-drift pin. The era-6 opening commit caught up
    ``docs/playbook-detector-spec.md`` §6's own version pointer (v2 -> v3, reconciling the doc to
    code that had already shipped) — a DOC-ONLY edit, zero behavior change. This pin makes that
    reconciliation permanent two ways: (1) the doc's heading block and its "Structural (shape, not
    thresholds)" constants line both still name the LIVE ``PLAYBOOK_CONTEXT_ALGORITHM_VERSION``
    value verbatim, so the two can never silently diverge again; (2) ``desk_playbook_context.py``
    itself — the LENS this doc describes — is byte-unchanged this iteration (a doc catch-up is
    never a licence to touch the lens), via the ``test_desk_playbook_guards.py::test_decline_
    disclosure_doc_edit_left_the_capitulation_code_byte_unchanged`` precedent: a pinned
    ``hashlib.sha256(inspect.getsource(...))`` hash over the WHOLE module (the broadest possible
    zero-diff claim, since this iteration's IN SCOPE names ``desk_playbook*.py`` as a zero-diff
    file, not just two of its functions).

(b) The ``docs/research-directions.md`` catalog-reconciliation pins. The era-6 opening commit
    reconciled the year-long research catalog's status table (eras 5/5B/5C/5D/B/B2, all already
    recorded) and dated two Card entries "AMENDED 2026-08-14" (6.2's bootstrap-p retraction, 6.3's
    store-design supersession). String-presence pins so neither the status-table rows nor the
    amendment notes can be silently reworded or removed later — this iteration only PINS
    already-reconciled text; it edits neither document (IN SCOPE / OUT OF SCOPE both say so).

Every guard here carries a seeded counter-test (the ``test_copy_discipline.py`` / ``test_desk_
playbook_guards.py`` precedent: "a lint that cannot fail proves nothing")."""

from __future__ import annotations

import hashlib
import inspect
import pathlib

from app.research import desk_playbook_context as desk_playbook_context_module
from app.research.desk_playbook_context import PLAYBOOK_CONTEXT_ALGORITHM_VERSION

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SPEC_PATH = REPO_ROOT / "docs" / "playbook-detector-spec.md"
_CATALOG_PATH = REPO_ROOT / "docs" / "research-directions.md"


# --- (a) the playbook-band-context-v3 spec-drift pin (TC-6, TC-7) ----------------------------------

# Recorded at the START of this iteration (``desk_playbook_context.py`` as it exists on `main`
# before goal-referee-iter-1 touches anything) — this iteration ships ZERO diff to this module, so
# the hash below must still match at the END of the iteration too.
_DESK_PLAYBOOK_CONTEXT_MODULE_SHA256 = (
    "75537d161661b9660cf82896c56b60d92acdf3179fd77bd041c38ae45530fc23"
)


def test_desk_playbook_context_module_is_byte_unchanged_this_iteration():
    """TC-7: this iteration's doc catch-up in ``docs/playbook-detector-spec.md`` §6 ships ZERO
    diff to ``desk_playbook_context.py`` — the WHOLE module's own live source (via
    ``inspect.getsource``) still hashes to the value recorded at the start of this iteration."""
    source = inspect.getsource(desk_playbook_context_module)
    assert hashlib.sha256(source.encode()).hexdigest() == _DESK_PLAYBOOK_CONTEXT_MODULE_SHA256


def test_desk_playbook_context_zero_diff_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail — a lint that cannot fail proves nothing."""
    source = inspect.getsource(desk_playbook_context_module)
    real_hash = hashlib.sha256(source.encode()).hexdigest()
    seeded_wrong_hash = "0" * 64
    assert real_hash != seeded_wrong_hash


def test_playbook_band_context_v3_named_in_spec_heading_block():
    """TC-6 (heading half): §6's heading and its immediate supersession note both name the LIVE
    ``PLAYBOOK_CONTEXT_ALGORITHM_VERSION`` value verbatim — fails the instant the doc's version
    pointer and the shipped code constant diverge."""
    text = _SPEC_PATH.read_text()
    start = text.index("## 6. Band context")
    end = text.index("\n### Pre-registered constants", start)
    heading_block = text[start:end]
    assert PLAYBOOK_CONTEXT_ALGORITHM_VERSION in heading_block


def test_playbook_band_context_v3_named_in_spec_constants_line():
    """TC-6 (constants-line half): the "Structural (shape, not thresholds)" line names the LIVE
    ``PLAYBOOK_CONTEXT_ALGORITHM_VERSION`` value verbatim."""
    text = _SPEC_PATH.read_text()
    assert f'PLAYBOOK_CONTEXT_ALGORITHM_VERSION = "{PLAYBOOK_CONTEXT_ALGORITHM_VERSION}"' in text


def test_playbook_band_context_v3_spec_pin_guard_can_fail_on_a_seeded_divergence():
    """The lint CAN fail: a deliberately wrong version string is rejected."""
    text = _SPEC_PATH.read_text()
    seeded_wrong_version = "playbook-band-context-v999"
    assert seeded_wrong_version not in text


# --- (b) the docs/research-directions.md catalog-reconciliation pins (TC-8) ------------------------

# One distinctive, single-line substring per pinned status-table row — long enough that an
# accidental match elsewhere in the document is not a realistic risk, short enough to be an honest
# transcription (each verified byte-for-byte against the committed file at authoring time).
_STATUS_TABLE_ROW_PINS = (
    "`yahoo_fetch` | done | The era pivoted to a keyless Yahoo Finance BAR library",  # era 5
    "`tradable_wall` | done | Tradable",  # era 5B
    "`fast_wall` | done | Store stat-caches + durable dataset index",  # era 5C
    "`clean_slate` | done | Journal era deleted (14 routes, 3 pages",  # era 5D
    "`desk` | done | `/desk`: fetched S&P100 universe, append-only screen ledger",  # era B
    "`playbook` | done | Nine pre-registered Graifer/Schumacher intraday detectors",  # era B2
)

_CARD_AMENDMENT_PINS = (
    "AMENDED 2026-08-14 (era-6 opening; statistical correction",  # Card 6.2
    "AMENDED 2026-08-14, era-6 opening: the store design below is superseded",  # Card 6.3
)


def test_catalog_status_table_names_every_pinned_era_row():
    """TC-8 (status-table half): one row per named era (5/5B/5C/5D/B/B2) is still present, fails
    the instant any row's own finding sentence is reworded or removed."""
    text = _CATALOG_PATH.read_text()
    for pin in _STATUS_TABLE_ROW_PINS:
        assert pin in text, f"status-table row pin missing: {pin!r}"


def test_catalog_names_the_card_6_2_and_6_3_amendment_notes():
    """TC-8 (amendment-note half): the dated "AMENDED 2026-08-14" notes under Card 6.2 and
    Card 6.3 are still present."""
    text = _CATALOG_PATH.read_text()
    for pin in _CARD_AMENDMENT_PINS:
        assert pin in text, f"catalog amendment-note pin missing: {pin!r}"


def test_catalog_reconciliation_guard_can_fail_on_a_seeded_removal():
    """The lint CAN fail: a string genuinely absent from the doc is rejected."""
    text = _CATALOG_PATH.read_text()
    assert "this exact sentence was never written to the catalog, ever" not in text
