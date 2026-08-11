"""Prove — or refuse to claim — that the backend a browser lane is about to drive is the FIXTURE
rig rather than the operator's real store.

This is tapeology's ``STORE_SCOPE_ASSERT_CMD``: the framework's store-scope guard
(``incredible_auto_dev/scripts/automation/store-scope/store-scope.sh``) runs it before ANY browser
lane -- deterministic golden replay or LLM dispatch -- and refuses to run the lane at all when it
exits non-zero.

WHY (goal-playbook-iter-8 audit, finding B2): iteration 8 shipped
``qa_playbook_iter7_fixture_scoped_backend.sh``, a launcher that stands up a fully scoped backend,
and the same iteration's pipeline run then replayed J-07's "Run Backscan" click against whatever
was listening on the QA port -- the operator's ambient backend. Three real S&P-100 playbook records
and a back-scan ledger row landed in an append-only store the project's own immutable-data rail
forbids ever pruning. The launcher was correct; nothing obliged anyone to use it. This script is the
obligation.

THE MARKER. ``UniverseStore.record`` stores the ``source_url`` a membership was fetched from, and
every fixture seeder registers its snapshot as ``fixture-rig*`` (``seed_playbook_fixture_rig.py`` ->
``fixture-rig``, the iter-7 extension -> ``fixture-rig-iter7``, iter-8 -> ``fixture-rig-iter8``,
iter-8's replay rig -> ``fixture-rig-iter8-replay``), while the real store's latest snapshot carries
the Wikipedia S&P-100 URL a real fetch produced. The served ``latest`` snapshot therefore says which
store is behind the port, in the backend's own words, with no new endpoint and no new served field.

FAIL CLOSED, ALWAYS. Anything the payload cannot prove -- no snapshot yet, an unreadable body, a
connection error, a non-200 -- is "not scoped". The cost of a false negative is a QA lane that
refuses to run and says why; the cost of a false positive is another un-prunable write into the
operator's store.

Usage (normally through the framework guard, which passes nothing and relies on the env):

    .venv/bin/python scripts/assert_scoped_qa_backend.py [BASE_URL]

    BASE_URL  default: $QA_BACKEND_BASE_URL, else http://localhost:${CHAIN_BACKEND_PORT:-8301}

Exit: 0 = provably the fixture rig · 1 = not scoped / cannot prove (the lane must not run).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_REQUIRED_PREFIX = "fixture-rig"
_TIMEOUT_S = 10


def scoped_verdict(payload, required_prefix: str = DEFAULT_REQUIRED_PREFIX) -> tuple[bool, str]:
    """``(is_scoped, reason)`` for a ``GET /research/desk/universe`` body -- a PURE function, so the
    decision rule is unit-testable without a live server (``tests/test_qa_scoped_backend_guard.py``).

    Scoped iff the LATEST registered snapshot's ``source_url`` starts with ``required_prefix``. The
    reason always names what was actually seen, so a refusal is diagnosable from one log line."""
    if not isinstance(payload, dict):
        return False, f"universe body is not an object ({type(payload).__name__}) -- cannot prove scoped"
    latest = payload.get("latest")
    if latest is None:
        snapshots = payload.get("snapshots")
        if isinstance(snapshots, list) and not snapshots:
            return False, "no universe snapshot is registered on this backend -- cannot prove scoped"
        return False, "universe body carries no 'latest' snapshot -- cannot prove scoped"
    if not isinstance(latest, dict):
        return False, f"universe 'latest' is not an object ({type(latest).__name__}) -- cannot prove scoped"
    source_url = latest.get("source_url")
    if not isinstance(source_url, str) or not source_url:
        return False, "latest universe snapshot carries no source_url -- cannot prove scoped"
    members = latest.get("member_count")
    if source_url.startswith(required_prefix):
        return True, (
            f"latest universe snapshot source_url={source_url!r} (member_count={members}) -- "
            f"this backend serves the fixture rig"
        )
    return False, (
        f"latest universe snapshot source_url={source_url!r} (member_count={members}) -- this is NOT "
        f"a {required_prefix!r} backend; a browser lane here would read and write the operator's real store"
    )


def _fetch_universe(base_url: str) -> tuple[object | None, str]:
    url = base_url.rstrip("/") + "/research/desk/universe"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as response:  # noqa: S310 (localhost QA probe)
            if response.status != 200:
                return None, f"GET {url} returned HTTP {response.status}"
            return json.loads(response.read().decode("utf-8")), ""
    except urllib.error.HTTPError as exc:
        return None, f"GET {url} returned HTTP {exc.code}"
    except Exception as exc:  # connection refused, timeout, bad JSON -- all fail closed
        return None, f"GET {url} failed: {type(exc).__name__}: {exc}"


def main(argv: list[str]) -> int:
    base_url = (
        argv[1] if len(argv) > 1
        else os.environ.get("QA_BACKEND_BASE_URL")
        or f"http://localhost:{os.environ.get('CHAIN_BACKEND_PORT', '8301')}"
    )
    required_prefix = os.environ.get("STORE_SCOPE_UNIVERSE_PREFIX", DEFAULT_REQUIRED_PREFIX)
    payload, error = _fetch_universe(base_url)
    if error:
        print(f"[assert-scoped-qa-backend] NOT SCOPED ({base_url}): {error}", file=sys.stderr)
        return 1
    scoped, reason = scoped_verdict(payload, required_prefix)
    stream = sys.stdout if scoped else sys.stderr
    print(f"[assert-scoped-qa-backend] {'SCOPED' if scoped else 'NOT SCOPED'} ({base_url}): {reason}", file=stream)
    return 0 if scoped else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
