"""Store-scope guard for the DERIVED cache DBs: automated tests never touch the live ones.

The framework's store-scope guard protects the append-only stores from automated BROWSER lanes
and deliberately leaves the derived accelerator DBs unprotected — a read path legitimately
updates those, so listing them would turn every clean browser run into a false breach. That
reasoning does not transfer to pytest: a test has no business opening the operator's cache DBs at
all, and iter-28 wired the three real-corpus fixtures onto exactly those two files
(``.data/dataset_index.db`` and ``.data/micro_readiness_cache.db``), making a test run and a
running backend two writers of one SQLite file for no benefit (iter-28 audit; owner ruling
2026-08-24, task A2).

This file is the pytest half of the guard, in three layers:

1. PATH IDENTITY — the test-owned paths are provably not the live ones, and live under a
   dedicated ``test-cache/`` namespace that is safe to ``rm -rf``.
2. ENV INDEPENDENCE — the operator env vars that point the LIVE backend at its cache DBs cannot
   drag the test namespace back onto them. This is the exact mechanism iter-28 used and the exact
   one that must never be reintroduced.
3. STATIC SCAN — no test module resolves a cache DB through the live resolver or the live env
   vars, so the defect cannot come back by copy-paste into a fourth file.

The fourth and strongest layer is not here but in ``conftest.py``:
``_forbid_live_cache_db_construction`` refuses, for the whole session, to let ANY test construct
``DatasetIndex`` or ``MicroReadinessCache`` against a live path. Constructing either creates the
file, its WAL sidecars and its schema, so refusing the constructor is strictly stronger than
refusing a write — and unlike an mtime watch it can never false-fail because the operator's own
backend touched a file while the suite ran.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.config import CONFIG
from app.research.dataset_index import DatasetIndex
from app.research.micro_readiness import MicroReadinessCache, resolve_micro_readiness_cache_db_path
from tests import real_corpus_cache as rcc

TESTS_DIR = Path(__file__).resolve().parent

# The three files whose fixtures run against the real corpus and therefore need a persistent,
# test-owned cache rather than a throwaway one.
REAL_CORPUS_TEST_FILES = (
    "test_micro_readiness.py",
    "test_micro_join.py",
    "test_micro_snapshots.py",
)


# --- layer 1: path identity -------------------------------------------------------------------


@pytest.mark.parametrize("dataset_dir_name", ["dataset_dir", "dataset_dir_resolved"])
def test_test_owned_cache_paths_are_never_the_live_ones(dataset_dir_name):
    """Both DBs, for BOTH dataset-dir resolutions the suite actually uses."""
    dataset_dir = (
        CONFIG.dataset_dir if dataset_dir_name == "dataset_dir" else CONFIG.dataset_dir_resolved()
    )
    assert rcc.test_dataset_index_db_path(dataset_dir) != rcc.live_dataset_index_db_path(dataset_dir)
    assert rcc.test_micro_readiness_cache_db_path(
        dataset_dir
    ) != rcc.live_micro_readiness_cache_db_path(dataset_dir)
    assert rcc.test_cache_dir(dataset_dir) != rcc.live_cache_dir(dataset_dir)


def test_the_test_cache_lives_in_its_own_deletable_directory():
    """A directory, not a filename prefix — so the whole reset procedure is one ``rm -rf`` that
    cannot possibly catch a live file."""
    dataset_dir = CONFIG.dataset_dir
    cache_dir = rcc.test_cache_dir(dataset_dir)
    assert cache_dir.name == rcc.TEST_CACHE_DIRNAME
    assert cache_dir.parent == rcc.live_cache_dir(dataset_dir)
    for path in (
        rcc.test_dataset_index_db_path(dataset_dir),
        rcc.test_micro_readiness_cache_db_path(dataset_dir),
    ):
        assert Path(path).parent == cache_dir


def test_the_live_path_helpers_match_the_production_resolvers(tmp_path, monkeypatch):
    """The guard is only meaningful if what it calls "live" really is what production resolves
    to. Pinned against the production resolver itself, with the env override cleared so the
    sibling default is what is compared."""
    monkeypatch.delenv("TAPEOLOGY_MICRO_READINESS_CACHE_DB", raising=False)
    dataset_dir = str(tmp_path / "datasets")
    assert rcc.live_micro_readiness_cache_db_path(dataset_dir) == str(
        Path(resolve_micro_readiness_cache_db_path(dataset_dir)).resolve()
    )
    # get_dataset_store()'s env-else-sibling shape (routes.py), the index half of the same policy.
    assert rcc.live_dataset_index_db_path(dataset_dir) == str(
        (Path(dataset_dir).resolve().parent / "dataset_index.db")
    )


# --- layer 2: env independence ----------------------------------------------------------------


def test_the_operator_cache_env_vars_cannot_drag_the_test_namespace_onto_live_files(monkeypatch):
    """iter-28's exact mechanism: ``index_db_override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
    or <sibling>``. With the operator's backend running, both of these are commonly set, and
    honouring them is how the test path landed on the live DB. The test namespace must be deaf to
    them."""
    dataset_dir = CONFIG.dataset_dir
    before_index = rcc.test_dataset_index_db_path(dataset_dir)
    before_cache = rcc.test_micro_readiness_cache_db_path(dataset_dir)

    monkeypatch.setenv("TAPEOLOGY_DATASET_INDEX_DB", rcc.live_dataset_index_db_path(dataset_dir))
    monkeypatch.setenv(
        "TAPEOLOGY_MICRO_READINESS_CACHE_DB", rcc.live_micro_readiness_cache_db_path(dataset_dir)
    )

    assert rcc.test_dataset_index_db_path(dataset_dir) == before_index
    assert rcc.test_micro_readiness_cache_db_path(dataset_dir) == before_cache
    assert rcc.test_dataset_index_db_path(dataset_dir) != rcc.live_dataset_index_db_path(dataset_dir)


def test_the_namespace_has_its_own_override_and_it_is_honoured(tmp_path, monkeypatch):
    """``TAPEOLOGY_TEST_CACHE_DIR`` is this namespace's own knob (CI, or a scoped run) — distinct
    from the operator's."""
    monkeypatch.setenv(rcc.TEST_CACHE_DIR_ENV, str(tmp_path / "elsewhere"))
    dataset_dir = CONFIG.dataset_dir
    assert rcc.test_cache_dir(dataset_dir) == (tmp_path / "elsewhere").resolve()
    assert rcc.test_dataset_index_db_path(dataset_dir) == str(
        (tmp_path / "elsewhere").resolve() / rcc.DATASET_INDEX_DB_NAME
    )


# --- layer 3: static scan ---------------------------------------------------------------------


_LIVE_RESOLVER_RE = re.compile(
    r"resolve_micro_readiness_cache_db_path\s*\(|"
    r"environ(?:\.get)?\s*[(\[]\s*[\"']TAPEOLOGY_(?:DATASET_INDEX_DB|MICRO_READINESS_CACHE_DB)[\"']"
)


def test_no_real_corpus_test_file_resolves_a_cache_db_through_the_live_policy():
    """The three real-corpus files must get their cache paths from ``real_corpus_cache``, never
    by re-deriving the live env-else-sibling policy themselves.

    Scoped to the three files rather than the whole suite on purpose: other modules legitimately
    exercise the live resolver as the unit under test (``test_micro_readiness.py`` does too, which
    is why the check below is line-based and skips its own resolver tests by looking only at
    fixture/store-construction context)."""
    offenders: list[str] = []
    for name in REAL_CORPUS_TEST_FILES:
        path = TESTS_DIR / name
        assert path.is_file(), f"{name} is missing — update REAL_CORPUS_TEST_FILES"
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            code = line.split("#", 1)[0]
            if "DatasetStore(" not in code and "MicroReadinessCache(" not in code:
                continue
            if _LIVE_RESOLVER_RE.search(code):
                offenders.append(f"{name}:{lineno}: {line.strip()}")
    assert offenders == [], (
        "a real-corpus test builds a store/cache from the LIVE cache policy:\n  "
        + "\n  ".join(offenders)
        + "\nUse tests/real_corpus_cache.py instead."
    )


def test_every_real_corpus_file_sources_its_caches_from_the_shared_helper():
    """The positive half of the same property: each of the three imports the shared namespace, so
    there is exactly one place the decision lives and no duplicate cache wiring."""
    for name in REAL_CORPUS_TEST_FILES:
        text = (TESTS_DIR / name).read_text(encoding="utf-8")
        assert "real_corpus_cache" in text, f"{name} does not use tests/real_corpus_cache.py"


# --- the conftest construction guard is itself guarded ------------------------------------------


def test_the_session_guard_refuses_a_live_cache_db_construction():
    """The conftest guard is the strongest layer, so it gets a mutation test of its own: if it
    ever stopped being installed, this would pass silently and the suite would go back to opening
    the operator's DBs."""
    live_index = rcc.live_dataset_index_db_path(CONFIG.dataset_dir)
    live_cache = rcc.live_micro_readiness_cache_db_path(CONFIG.dataset_dir)

    with pytest.raises(AssertionError, match="LIVE backend cache DB"):
        DatasetIndex(live_index)
    with pytest.raises(AssertionError, match="LIVE backend cache DB"):
        MicroReadinessCache(live_cache)


def test_the_session_guard_allows_test_owned_and_hermetic_paths(tmp_path):
    """...and it must not be a blanket ban: the test namespace and ordinary ``tmp_path`` DBs are
    exactly what tests are supposed to use."""
    hermetic = DatasetIndex(str(tmp_path / "dataset_index.db"))
    assert Path(hermetic.db_path).is_file()
    MicroReadinessCache(str(tmp_path / "micro_readiness_cache.db"))

    dataset_dir = CONFIG.dataset_dir
    owned = DatasetIndex(rcc.test_dataset_index_db_path(dataset_dir))
    assert Path(owned.db_path).parent == rcc.test_cache_dir(dataset_dir)
