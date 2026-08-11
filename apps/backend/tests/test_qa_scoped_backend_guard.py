"""The QA store-scope assert: is the backend a browser lane is about to drive the FIXTURE rig, or
the operator's real store?

WHY THIS EXISTS (goal-playbook-iter-8 audit, finding B2): iteration 8 shipped a launcher that
stands up a fixture-scoped backend -- and its own pipeline run then replayed a golden containing a
"Run Backscan" click against the operator's AMBIENT backend, computing three real S&P-100 playbook
records and appending a run-ledger row into an append-only store that can never be pruned. The
launcher was never wrong; nothing was OBLIGED to use it. The framework's store-scope guard
(``incredible_auto_dev/scripts/automation/store-scope/store-scope.sh``) now refuses to run any
browser lane unless a project-owned assert command proves the backend under test is scoped --
``scripts/assert_scoped_qa_backend.py`` is tapeology's implementation of that assert, and this file
is its unit coverage.

The classifier is deliberately a PURE function of the served ``GET /research/desk/universe`` body,
so the decision rule is testable without a live server: the fixture rig registers its universe
snapshots with a ``fixture-rig*`` ``source_url`` (``seed_playbook_fixture_rig.py`` and its two
extensions), while the real store's latest snapshot carries the Wikipedia S&P-100 URL it was
actually fetched from. Every unproven case fails CLOSED -- "cannot prove scoped" and "proved
unscoped" both mean no browser lane may run, which is the only safe reading when the alternative is
writing into the operator's store.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from assert_scoped_qa_backend import scoped_verdict  # noqa: E402

_REAL_PAYLOAD = {
    "snapshots": [{"id": "universe-2026-07-25-49b33fa31680", "source_url": "https://en.wikipedia.org/wiki/S%26P_100"}],
    "latest": {
        "id": "universe-2026-07-25-49b33fa31680",
        "source_url": "https://en.wikipedia.org/wiki/S%26P_100",
        "member_count": 101,
        "members": ["AAPL", "ABBV", "ABT"],
    },
    "integrity_errors": [],
}

_FIXTURE_PAYLOAD = {
    "snapshots": [{"id": "universe-2026-06-22-aaaa", "source_url": "fixture-rig"}],
    "latest": {
        "id": "universe-2026-06-22-bbbb",
        "source_url": "fixture-rig-iter8",
        "member_count": 16,
        "members": ["DECOR", "RTAAA", "DTAAA", "BSCAN"],
    },
    "integrity_errors": [],
}


def test_fixture_rig_universe_is_scoped():
    """The rig's own snapshots are registered with a fixture-rig source_url -- the one marker no
    real fetch can produce (``UniverseStore.record`` stores the source it was fetched from)."""
    scoped, reason = scoped_verdict(_FIXTURE_PAYLOAD)
    assert scoped is True
    assert "fixture-rig-iter8" in reason


def test_real_sp100_universe_is_not_scoped():
    """The exact body the operator's real backend serves -- the configuration iteration 8's replay
    lane actually ran against."""
    scoped, reason = scoped_verdict(_REAL_PAYLOAD)
    assert scoped is False
    assert "en.wikipedia.org" in reason


def test_an_empty_universe_store_fails_closed():
    """No snapshot at all proves nothing either way: a freshly created scoped root looks exactly
    like a real backend whose universe was never registered. Unproven is refused, never allowed."""
    scoped, reason = scoped_verdict({"snapshots": [], "latest": None, "integrity_errors": []})
    assert scoped is False
    assert "no universe snapshot" in reason


def test_a_malformed_body_fails_closed():
    """A body that is not the universe payload at all (a 404 JSON, an error object, a proxy page)
    is refused rather than parsed optimistically."""
    for payload in ({}, {"detail": "Not Found"}, {"latest": "nonsense"}, []):
        scoped, reason = scoped_verdict(payload)
        assert scoped is False, payload
        assert reason


def test_the_required_prefix_is_a_parameter_not_a_hardcoded_string():
    """The marker is the rig's own convention, so a future rig can rename it in ONE place (the
    store-scope.env the framework guard reads) instead of forking the classifier."""
    scoped, _ = scoped_verdict(_FIXTURE_PAYLOAD, required_prefix="some-other-rig")
    assert scoped is False
    scoped, _ = scoped_verdict(
        {"latest": {"source_url": "some-other-rig-v2", "member_count": 3}}, required_prefix="some-other-rig"
    )
    assert scoped is True
