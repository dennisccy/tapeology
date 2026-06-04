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
