from pathlib import Path

import pytest

# Load apps/backend/.env once for the session (load-if-missing: never overrides an already-set
# var), so a credentialed operator run sees real creds while the suite stays hermetic — each
# gate test still controls the environment via monkeypatch, and the historical/search tests
# inject a fake adapter via dependency_overrides rather than touching the real vendor.
from app.env import load_env

load_env()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_store_verified_caches():
    """era-fast_wall J-02 (TC-12) — this file's FIRST autouse fixture. Resets BOTH new
    module-level, stat-keyed verified-content caches (``bars.py``'s ``_VERIFIED_CACHE``,
    ``datasets.py``'s ``_VERIFIED_META_CACHE``) before every test, via each module's own
    test-only reset helper. Without this, the caches would accumulate entries across the ENTIRE
    test session (harmless for correctness — the cache key is the absolute file path, and
    distinct ``tmp_path`` roots never collide — but unbounded growth over a long suite run is
    still worth avoiding), and any test that intentionally wants a genuinely cold cache can now
    rely on that being the default starting state rather than re-deriving it itself.

    era-fast_wall J-06 additionally resets ``setups.py``'s own in-process hot slot
    (``_SCAN_CACHE``) via its identical ``_reset_scan_cache_for_tests`` helper. Unlike the two
    caches above (keyed by absolute file path, so distinct ``tmp_path`` roots never collide), J-06
    rekeyed that slot on config CONTENT rather than ``id(config)`` — so two unrelated tests using
    genuinely equal config content against a genuinely equal (e.g. both-empty) store signature could
    otherwise observe each other's leftover hot-slot entry. Resetting it here, alongside its two
    siblings, makes every test start from a guaranteed-cold hot slot regardless of ordering (the
    durable ``SetupsScanCache`` tier needs no such reset — its DB path is derived from each test's
    own ``tmp_path``-scoped bar store root, so it is already naturally test-isolated)."""
    import app.research.bars as bars_module
    import app.research.datasets as datasets_module
    import app.research.setups as setups_module

    bars_module._reset_verified_cache_for_tests()
    datasets_module._reset_verified_cache_for_tests()
    setups_module._reset_scan_cache_for_tests()
    yield


@pytest.fixture(autouse=True)
def _walk_the_screen_in_process(monkeypatch):
    """The desk screen walks IN THIS PROCESS for the whole suite.

    ``desk_screen`` divides its member walk across worker processes by default (see
    ``_SCREEN_WORKERS_ENV``), which is right for an operator's ~100-member run and wrong for every
    test: the hermetic universe fixtures already exceed the worker threshold, so each screen test
    would spawn four fresh interpreters — and, more importantly, the walk's reads would happen where
    a ``monkeypatch`` cannot see them, silently voiding the call-count guards that prove
    ``compute_tradability``/``merged_bars`` are called exactly once per member.

    Tests that are ABOUT the parallel walk opt back in explicitly by setting the same variable —
    see ``test_desk_screen_parallel.py``, which is where the worker path's own equivalence to this
    one is proven."""
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_WORKERS", "1")
    yield


@pytest.fixture(scope="session", autouse=True)
def _forbid_live_cache_db_construction():
    """The store-scope guard, applied to the DERIVED cache DBs (owner ruling 2026-08-24, task A2).

    The framework's store-scope guard
    (``incredible_auto_dev/scripts/automation/store-scope/store-scope.sh``) protects the
    APPEND-ONLY stores from automated browser lanes, and deliberately leaves the derived
    accelerator DBs off its protected list -- a read path legitimately updates those, so listing
    them would make every clean run a false breach. That reasoning is right for the browser lane
    and says nothing about pytest, where the opposite is true: a test has no business opening the
    OPERATOR's cache DBs at all. iter-28 wired the real-corpus fixtures onto exactly those two
    files, making a test run and a running backend two writers of one SQLite file for no benefit.

    This is the pytest half of that guard, and it proves the property by CONSTRUCTION rather than
    by watching mtimes: opening either cache class creates the file, its WAL sidecars and its
    schema, so refusing the constructor is strictly stronger than refusing a write -- and it can
    never false-fail because the operator's own backend touched a file mid-session.

    Test-owned caches live under ``.data/test-cache/`` (``tests/real_corpus_cache.py``);
    hermetic per-test caches keep using ``tmp_path`` as they always have. Neither is affected.
    """
    import app.research.dataset_index as dataset_index_module
    import app.research.micro_readiness as micro_readiness_module
    from app.config import CONFIG

    # CONFIG.dataset_dir, never `_resolved()`: the un-overridden package default IS the
    # operator's real store, and that is the only thing this guard protects. A session scoped
    # elsewhere (TAPEOLOGY_DATASET_DIR pointed at a fixture rig) is writing its own throwaway
    # rig DBs, which is fine and must not trip the guard.
    live_dir = Path(CONFIG.dataset_dir).resolve().parent
    forbidden: set[str] = {
        str(live_dir / "dataset_index.db"),
        str(live_dir / "micro_readiness_cache.db"),
    }

    def _guard(db_path: str, cls_name: str) -> None:
        if str(db_path) == ":memory:":
            return
        resolved = str(Path(db_path).resolve())
        if resolved in forbidden:
            raise AssertionError(
                f"{cls_name} was constructed against the LIVE backend cache DB {resolved!r}. "
                "Automated tests must never open the operator's derived cache DBs -- they are "
                "the running backend's files, and a second writer buys nothing. Use "
                "tests/real_corpus_cache.py (persistent, test-owned, under .data/test-cache/) "
                "for real-corpus tests, or a tmp_path DB for a hermetic one."
            )

    originals = {}
    for module, cls_name in (
        (dataset_index_module, "DatasetIndex"),
        (micro_readiness_module, "MicroReadinessCache"),
    ):
        cls = getattr(module, cls_name)
        originals[(module, cls_name)] = cls.__init__

        def _make(original, name):
            def __init__(self, db_path, *args, **kwargs):  # noqa: N807
                _guard(db_path, name)
                return original(self, db_path, *args, **kwargs)
            return __init__

        cls.__init__ = _make(cls.__init__, cls_name)

    yield

    for (module, cls_name), original in originals.items():
        getattr(module, cls_name).__init__ = original
