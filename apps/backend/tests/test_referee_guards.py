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

import ast
import hashlib
import inspect
import pathlib

from app.research import desk_playbook_context as desk_playbook_context_module
from app.research.desk_playbook_context import PLAYBOOK_CONTEXT_ALGORITHM_VERSION

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SPEC_PATH = REPO_ROOT / "docs" / "playbook-detector-spec.md"
_CATALOG_PATH = REPO_ROOT / "docs" / "research-directions.md"
_RESEARCH_DIR = pathlib.Path(__file__).resolve().parents[1] / "app" / "research"


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


# --- (c) goal-referee-iter-2 TC-10: the bidirectional import-ban -------------------------------------
#
# goal.md's "the Referee never feeds back" anti-goal (critical): no referee_*.py module may import
# the live detection/context machinery (it reads already-recorded records only), and neither
# desk_playbook_detect.py nor desk_playbook_context.py may import any referee_* module (the frozen
# detection/context layer stays wholly unaware the Referee exists). AST-structural
# (``test_bar_store_projection_guard.py``'s precedent), not a regex over source text, which a
# comment or a string literal could false-positive.


def _imported_module_names(path: pathlib.Path) -> set[str]:
    """Every dotted name this file's ``import``/``from ... import ...`` statements mention --
    both the bare module (``import a.b`` -> ``a.b``; ``from a.b import c`` -> ``a.b``) and each
    imported name alone AND module-qualified (``from a.b import c`` also adds ``c`` and
    ``a.b.c``), so ``from . import referee_evidence``, ``from .referee_evidence import X``, and
    ``from app.research import referee_evidence`` are all caught the same way."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
            for alias in node.names:
                names.add(alias.name)
                if node.module:
                    names.add(f"{node.module}.{alias.name}")
    return names


def _mentioning(names: set[str], target: str) -> set[str]:
    """Every name in ``names`` whose own LAST dotted component equals ``target`` exactly --
    ``app.research.desk_playbook_context`` matches ``desk_playbook_context``;
    ``desk_playbook_context_module`` (a local alias' own bound name, never an import target) does
    not."""
    return {name for name in names if name.split(".")[-1] == target}


def _referee_modules() -> list[pathlib.Path]:
    return sorted(_RESEARCH_DIR.glob("referee_*.py"))


def test_no_referee_module_imports_the_detect_or_context_modules():
    """TC-10 (first direction): zero imports of ``desk_playbook_detect`` or
    ``desk_playbook_context`` inside any ``referee_*.py`` module."""
    referee_modules = _referee_modules()
    assert referee_modules, "no referee_*.py module found -- has the glob/location changed?"
    for path in referee_modules:
        imported = _imported_module_names(path)
        hit = _mentioning(imported, "desk_playbook_detect") | _mentioning(imported, "desk_playbook_context")
        assert not hit, f"{path.name} imports the banned module(s) {hit}"


def test_the_detect_and_context_modules_import_no_referee_module():
    """TC-10 (second direction): zero imports of any ``referee_*`` module inside
    ``desk_playbook_detect.py`` or ``desk_playbook_context.py``."""
    for filename in ("desk_playbook_detect.py", "desk_playbook_context.py"):
        path = _RESEARCH_DIR / filename
        assert path.exists(), f"{filename} not found at the expected location -- has it moved?"
        imported = _imported_module_names(path)
        hits = {name for name in imported if name.split(".")[-1].startswith("referee_")}
        assert not hits, f"{filename} imports referee module(s) {hits}"


def test_import_ban_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing (this file's own established
    per-guard precedent, e.g. ``test_desk_playbook_context_zero_diff_guard_can_fail_on_a_seeded_
    violation`` above)."""
    seeded_imports = {"app.research.desk_playbook_detect", "app.research.other"}
    assert _mentioning(seeded_imports, "desk_playbook_detect") == {
        "app.research.desk_playbook_detect"
    }
    seeded_referee_imports = {"app.research.referee_evidence", "app.research.other"}
    hits = {name for name in seeded_referee_imports if name.split(".")[-1].startswith("referee_")}
    assert hits == {"app.research.referee_evidence"}


# --- goal-referee-iter-3 TC-23: the referee_stats.py-scoped import ban -----------------------------
#
# IN SCOPE: "referee_stats.py imports none of desk_playbook_detect, desk_playbook_context,
# desk_forward, levels, tradability (the stats core is estimand-agnostic -- it consumes plain
# numeric/session arrays a future caller passes in, never rail/detector/context data directly)".
# The bidirectional guard above already proves the first two (desk_playbook_detect/
# desk_playbook_context) for EVERY referee_*.py module via `_referee_modules()`'s glob; this guard
# is `referee_stats.py`-SCOPED and names all five banned modules explicitly, matching the iter
# spec's own AST-structural pattern verbatim.

_REFEREE_STATS_BANNED_MODULES = (
    "desk_playbook_detect",
    "desk_playbook_context",
    "desk_forward",
    "levels",
    "tradability",
)


def test_referee_stats_module_imports_none_of_the_banned_rail_detector_context_modules():
    """TC-23: zero imports of desk_playbook_detect/desk_playbook_context/desk_forward/levels/
    tradability inside referee_stats.py -- the stats core is estimand-agnostic (it consumes plain
    numeric/session arrays a caller passes in, never rail/detector/context data directly)."""
    path = _RESEARCH_DIR / "referee_stats.py"
    assert path.exists(), "referee_stats.py not found at the expected location -- has it moved?"
    imported = _imported_module_names(path)
    hits: set[str] = set()
    for banned in _REFEREE_STATS_BANNED_MODULES:
        hits |= _mentioning(imported, banned)
    assert not hits, f"referee_stats.py imports the banned module(s) {hits}"


def test_referee_stats_import_ban_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing (TC-23's own can-fail
    counter-test)."""
    seeded_imports = {"app.research.desk_forward", "app.research.levels", "app.research.other"}
    hits: set[str] = set()
    for banned in _REFEREE_STATS_BANNED_MODULES:
        hits |= _mentioning(seeded_imports, banned)
    assert hits == {"app.research.desk_forward", "app.research.levels"}
