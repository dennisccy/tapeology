"""ASGI entrypoint shim.

The QA harness starts the backend with ``uvicorn main:app --app-dir apps/backend`` (a
top-level ``main:app``). The real app lives in the ``app`` package; re-export it here so
both ``main:app`` and ``app.main:app`` resolve to the same FastAPI instance.
"""

from app.main import app  # noqa: F401
