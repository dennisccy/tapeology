"""Operator/gated REAL Wikipedia S&P 100 constituents fetch (Era B "The Desk", J-01) —
out-of-loop, not hermetic.

Per `.claude/core.md` (External Integration Testing) the hermetic suite alone is NOT sufficient
evidence the real integration works. This is the runnable proof that ``fetch_constituents_html``
+ ``parse_constituents`` genuinely reach the live Wikipedia page and produce a valid, in-bounds
S&P 100 membership snapshot — keyless (no credentials) and with no market-hours gate (a static
reference page, not a live feed). GATED behind an explicit opt-in so it is SKIPPED in the
autonomous loop by default and never makes a network call by accident (mirrors
``test_yahoo_live_integration.py``'s / ``test_live_integration.py``'s existing
``TAPEOLOGY_LIVE_INTEGRATION`` gate — the SAME shared env var, since this is the SAME class of
operator-run real-external-system check, just against a third vendor).

Run it (operator, any time — no credentials needed):

    TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_desk_universe_live_integration.py -v -s
"""

from __future__ import annotations

import os

import pytest

from app.config import CONFIG
from app.research.desk_universe import fetch_constituents_html, parse_constituents

pytestmark = pytest.mark.integration


def _skip_unless_live_integration() -> None:
    if os.environ.get("TAPEOLOGY_LIVE_INTEGRATION") != "1":
        pytest.skip(
            "gated: set TAPEOLOGY_LIVE_INTEGRATION=1 to run the real Wikipedia fetch check"
        )


def test_real_wikipedia_fetch_parses_a_valid_sp100_snapshot():
    _skip_unless_live_integration()

    html = fetch_constituents_html(CONFIG.desk_universe_source_url, timeout=15.0)
    parsed = parse_constituents(
        html,
        min_members=CONFIG.desk_universe_min_members,
        max_members=CONFIG.desk_universe_max_members,
    )

    assert CONFIG.desk_universe_min_members <= len(parsed.members) <= CONFIG.desk_universe_max_members
    for member in parsed.members:
        assert 1 <= len(member) <= 6
    assert parsed.members == sorted(parsed.members)
    assert len(parsed.members) == len(set(parsed.members))
    # A durable, long-standing large-cap constituent — a sanity check that this is genuinely the
    # S&P 100 table and not some other page content.
    assert "AAPL" in parsed.members
