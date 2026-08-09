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
