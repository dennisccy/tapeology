"""``desk_screen_decision.py`` -- the ONE owner of "does the snapshot already recorded for this date
hold that date's full data?", shared verbatim by the compute path and the pins route.

The rule is four conditions (universe, config fingerprint, date-scoped coverage signature, resolved
member count); this file is their truth table, plus the two properties the design turns on: a
``"no_basis"`` skip counts as RESOLVED (so a date cannot re-walk forever), and a legacy snapshot
recorded before the date-scoped pin existed falls back to the exact pre-existing ``bar_store_signature``
rather than having a value invented for it.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from app.research import desk_screen_decision
from app.research.desk_screen_decision import resolve_screen_decision

SCREEN_DATE = "2026-07-27"
UNIVERSE_ID = "universe-2026-07-25-49b33fa31680"
FINGERPRINT = "08e471b10130e1e2"


def _pins(*, bar="bar-sig-0000", coverage="cov-sig-0000", rankable=3) -> dict:
    return {
        "bar_store_signature": bar,
        "screen_coverage_signature": coverage,
        "rankable_member_count": rankable,
    }


def _existing(
    *,
    ranked=3,
    no_basis=0,
    no_bars=0,
    bar="bar-sig-0000",
    coverage="cov-sig-0000",
    universe=UNIVERSE_ID,
    fingerprint=FINGERPRINT,
    legacy=False,
) -> dict:
    meta = {
        "id": f"screen-{SCREEN_DATE}-abcdef012345",
        "screen_date": SCREEN_DATE,
        "as_of": f"{SCREEN_DATE}T23:59:59Z",
        "universe_snapshot_id": universe,
        "config_fingerprint": fingerprint,
        "bar_store_signature": bar,
        "created_utc": "2026-07-27T21:42:14.636275Z",
        "rows": [{"symbol": f"SYM{n}"} for n in range(ranked)],
        "skipped": (
            [{"symbol": f"NB{n}", "reason": "no_basis"} for n in range(no_basis)]
            + [{"symbol": f"XX{n}", "reason": "no_bars"} for n in range(no_bars)]
        ),
    }
    if not legacy:
        # A snapshot recorded before this addition OMITS the key entirely -- never `null`.
        meta["screen_coverage_signature"] = coverage
    return meta


def _decide(existing, pins) -> dict:
    return resolve_screen_decision(
        existing, pins, screen_date=SCREEN_DATE,
        universe_snapshot_id=UNIVERSE_ID, config_fingerprint=FINGERPRINT,
    )


# --- the four reuse conditions --------------------------------------------------------------------


def test_no_snapshot_for_the_date_is_record():
    decision = _decide(None, _pins())
    assert decision["action"] == "record"
    assert decision["screen_id"] is None
    assert SCREEN_DATE in decision["reason"]


def test_all_four_conditions_holding_is_reuse():
    decision = _decide(_existing(), _pins())
    assert decision["action"] == "reuse"
    assert decision["screen_id"] == f"screen-{SCREEN_DATE}-abcdef012345"


def test_a_changed_universe_snapshot_is_replace():
    decision = _decide(_existing(universe="universe-2026-08-01-000000000000"), _pins())
    assert decision["action"] == "replace"
    assert "universe" in decision["reason"]


def test_a_changed_config_fingerprint_is_replace():
    decision = _decide(_existing(fingerprint="0000000000000000"), _pins())
    assert decision["action"] == "replace"
    assert "config fingerprint" in decision["reason"]


def test_a_moved_date_scoped_coverage_signature_is_replace():
    """Condition 3 -- the bars this date could consume have changed."""
    decision = _decide(_existing(coverage="cov-sig-0000"), _pins(coverage="cov-sig-9999"))
    assert decision["action"] == "replace"
    assert "bars have moved" in decision["reason"]


def test_a_snapshot_that_resolved_fewer_members_than_are_rankable_is_replace():
    """Condition 4 -- the ``63 ranked/38 skipped`` -> ``100/1`` signal the live store recorded: the
    snapshot's ``no_bars`` skips are members whose bars have since been fetched."""
    decision = _decide(_existing(ranked=1, no_bars=2), _pins(rankable=3))
    assert decision["action"] == "replace"
    assert "2 more member(s)" in decision["reason"]


def test_conditions_3_and_4_are_independent_not_redundant():
    """A partial walk leaves a snapshot short under otherwise-IDENTICAL pins -- only condition 4
    catches it, which is why both are required rather than just the signature."""
    short_under_identical_pins = _existing(ranked=1, no_bars=0, no_basis=0)
    decision = _decide(short_under_identical_pins, _pins(rankable=3))
    assert decision["action"] == "replace"


# --- why condition 4 terminates -------------------------------------------------------------------


def test_a_no_basis_skip_counts_as_resolved_so_the_date_settles():
    """A member with a daily series whose every session falls after the screen date is honestly
    un-rankable for that date and always will be. Counting it as unresolved would re-walk the date
    on every single refresh, forever."""
    decision = _decide(_existing(ranked=1, no_basis=2), _pins(rankable=3))
    assert decision["action"] == "reuse"


def test_a_no_bars_skip_does_not_count_as_resolved():
    """The mirror image: a ``no_bars`` skip is a member whose bars simply had not been fetched --
    genuinely fixable, so it must NOT be counted as settled."""
    decision = _decide(_existing(ranked=1, no_bars=2), _pins(rankable=3))
    assert decision["action"] == "replace"


def test_resolving_more_members_than_are_rankable_today_is_still_reuse():
    """Coverage can only ever GROW the rankable ceiling in normal operation, but a snapshot that
    resolved more than the ceiling (an index row removed by a reconcile, say) is not evidence the
    date is incomplete -- the check is a floor, not an equality."""
    decision = _decide(_existing(ranked=5), _pins(rankable=3))
    assert decision["action"] == "reuse"


# --- legacy snapshots -----------------------------------------------------------------------------


def test_a_legacy_snapshot_with_an_unchanged_bar_store_signature_is_reuse():
    """No date-scoped pin was ever recorded for it and none can be reconstructed, so the fallback
    is the exact pre-existing pin: identical means nothing whatsoever has changed."""
    decision = _decide(_existing(legacy=True, bar="bar-sig-0000"), _pins(bar="bar-sig-0000"))
    assert decision["action"] == "reuse"


def test_a_legacy_snapshot_with_a_moved_bar_store_signature_is_replace():
    decision = _decide(_existing(legacy=True, bar="bar-sig-0000"), _pins(bar="bar-sig-9999"))
    assert decision["action"] == "replace"
    assert "predates the date-scoped completeness pin" in decision["reason"]


def test_a_legacy_snapshot_is_never_given_a_fabricated_coverage_signature():
    """The absence is read as an absence. A legacy record whose bar-store pin is unchanged must not
    be compared against the live coverage signature at all -- that value never existed for it."""
    legacy = _existing(legacy=True, bar="bar-sig-0000")
    assert "screen_coverage_signature" not in legacy
    decision = _decide(legacy, _pins(bar="bar-sig-0000", coverage="cov-sig-9999"))
    assert decision["action"] == "reuse"


# --- structural: this module can compute nothing --------------------------------------------------


def test_the_decision_module_cannot_reach_a_bar_store_or_compute_tradability():
    """Structural, not behavioural (the ``desk_screen._bar_store_signature`` "cannot call what it
    never received" argument): the module imports nothing at all beyond ``__future__``, so there is
    no path from here to a bar read or a tradability computation."""
    source = Path(inspect.getfile(desk_screen_decision)).read_text()
    imports = [
        line for line in source.splitlines()
        if line.startswith(("import ", "from ")) and "__future__" not in line
    ]
    assert imports == [], f"the decision module grew an import: {imports}"

    # Belt and braces: nothing from another module of this project is bound in its namespace
    # either, so there is no smuggled-in reference an import scan could miss.
    borrowed = [
        name for name, value in vars(desk_screen_decision).items()
        if not name.startswith("__")
        and name != "annotations"  # the `from __future__` flag object itself
        and getattr(value, "__module__", desk_screen_decision.__name__)
        != desk_screen_decision.__name__
    ]
    assert borrowed == [], f"the decision module borrowed {borrowed} from elsewhere"


def test_the_structural_import_guard_can_fail_on_a_seeded_violation():
    """A lint that cannot fail proves nothing."""
    seeded = "from __future__ import annotations\nfrom .bars import BarStore\n"
    imports = [
        line for line in seeded.splitlines()
        if line.startswith(("import ", "from ")) and "__future__" not in line
    ]
    assert imports == ["from .bars import BarStore"]
