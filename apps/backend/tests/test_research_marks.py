"""The single realized-R + marks projection (J-52, data-contract rows 18 & 27) — pure-function unit
tests of ``app.research.marks.marks_projection`` (the ONE computation path the projection and journal
detail share). R = |entry − invalidation|; realized move signed by direction; absent without marks;
a degenerate R == 0 yields a None realized move (never a divide-by-zero / fabricated infinity)."""

import math

import pytest

from app.research.marks import marks_projection
from app.research.store import ActionRecord, ThesisRecord


def _thesis(*, direction: str = "long", invalidation: float = 98.0) -> ThesisRecord:
    return ThesisRecord(
        id="t1",
        ticker="SIM-BUYER",
        setup_type="trend_continuation",
        direction=direction,
        invalidation_price=invalidation,
        level_price=None,
        status="active",
        bound_source="buyer_control",
        data_feed="sim",
        config_fingerprint="fp",
        entry_context={},
        statements=[],
        created_logical_ts=1.0,
        created_wall_ts=1700000000.0,
    )


def _action(kind: str, price: float, *, spread: float | None = 0.02) -> ActionRecord:
    return ActionRecord(
        id=f"a-{kind}",
        thesis_id="t1",
        kind=kind,
        price=price,
        logical_ts=10.0,
        wall_ts=1700000001.0,
        spread_at_mark=spread,
    )


def test_no_marks_no_realized_metric():
    proj = marks_projection(_thesis(), [])
    assert proj["entry"] is None
    assert proj["exit"] is None
    assert proj["has_entry"] is False
    assert proj["r_basis"] is None
    assert proj["realized_r"] is None


def test_entry_only_gives_r_basis_but_no_realized_move():
    # entry 100, invalidation 98 => R basis 2.0; no exit => no realized move.
    proj = marks_projection(_thesis(invalidation=98.0), [_action("entry", 100.0)])
    assert proj["has_entry"] is True
    assert proj["r_basis"] == pytest.approx(2.0)
    assert proj["realized_r"] is None
    assert proj["entry"]["price"] == 100.0
    assert proj["entry"]["spread_at_mark"] == 0.02


def test_long_realized_move_signed_positive_when_exit_above_entry():
    # long: entry 100, invalidation 98 (R=2), exit 101 => +1.0 / 2.0 = +0.5R.
    proj = marks_projection(
        _thesis(direction="long", invalidation=98.0),
        [_action("entry", 100.0), _action("exit", 101.0)],
    )
    assert proj["r_basis"] == pytest.approx(2.0)
    assert proj["realized_r"] == pytest.approx(0.5)


def test_long_realized_move_signed_negative_when_exit_below_entry():
    # long: entry 100, invalidation 98 (R=2), exit 99 => -1.0 / 2.0 = -0.5R (a move AGAINST the thesis).
    proj = marks_projection(
        _thesis(direction="long", invalidation=98.0),
        [_action("entry", 100.0), _action("exit", 99.0)],
    )
    assert proj["realized_r"] == pytest.approx(-0.5)


def test_short_realized_move_signed_positive_when_exit_below_entry():
    # short: entry 100, invalidation 102 (R=2), exit 99 => a DOWN move is in the thesis's favor =>
    # +1.0 / 2.0 = +0.5R.
    proj = marks_projection(
        _thesis(direction="short", invalidation=102.0),
        [_action("entry", 100.0), _action("exit", 99.0)],
    )
    assert proj["r_basis"] == pytest.approx(2.0)
    assert proj["realized_r"] == pytest.approx(0.5)


def test_short_realized_move_signed_negative_when_exit_above_entry():
    proj = marks_projection(
        _thesis(direction="short", invalidation=102.0),
        [_action("entry", 100.0), _action("exit", 101.0)],
    )
    assert proj["realized_r"] == pytest.approx(-0.5)


def test_degenerate_zero_r_basis_yields_none_realized_move_not_infinity():
    # entry exactly at invalidation (the API rejects a wrong-side invalidation, but a verbatim mark
    # could land there): R basis 0 => realized move is None, never a divide-by-zero or a fabricated inf.
    proj = marks_projection(
        _thesis(direction="long", invalidation=100.0),
        [_action("entry", 100.0), _action("exit", 105.0)],
    )
    assert proj["r_basis"] == 0.0
    assert proj["realized_r"] is None


def test_spread_at_mark_none_is_carried_verbatim():
    # A mark recorded with no quote (spread None) carries None verbatim — never a fabricated 0.
    proj = marks_projection(_thesis(), [_action("entry", 100.0, spread=None)])
    assert proj["entry"]["spread_at_mark"] is None
