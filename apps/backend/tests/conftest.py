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
    rely on that being the default starting state rather than re-deriving it itself."""
    import app.research.bars as bars_module
    import app.research.datasets as datasets_module

    bars_module._reset_verified_cache_for_tests()
    datasets_module._reset_verified_cache_for_tests()
    yield
