"""Source-introspection guard for the Validation Vault's "Sealed at" cell -- the
``test_desk_ui_guards.py``/``test_desk_touch_time_et_guard.py`` pattern (read the frontend .tsx as
TEXT, assert on substrings; no browser, no runtime).

**Why this guard exists (iteration-24 audit finding F1).** Iteration 24 narrowed the SERVED
``sealed_at`` from a full-precision ISO instant to a bare day marker (``vault._serialize_shard``
-> ``_coarsen_sealed_at_to_date``, proven by ``test_vault.py``'s TC-1/TC-2/TC-9). The cell that
renders it kept calling ``formatDateTimeET``, the INSTANT formatter -- and a bare ``yyyy-MM-dd``
fed to it is parsed as UTC midnight, which in US-Eastern is the PREVIOUS calendar day at 19:00 or
20:00. The live browser pass reproduced it exactly: the backend served ``"2026-05-01"`` and the
page printed ``2026-04-30 20:00 ET`` -- a wrong date, plus a time-of-day that was never in the
record and that the coarsening exists to remove.

``lib/datetime.ts`` already states the rule this guard pins: a day marker "names a DAY, not an
instant, so it is read LEXICALLY" and goes through ``formatDayMarker``. The neighbouring
``assigned_at``/``exposed_at`` cells are still genuine full-precision instants and correctly keep
``formatDateTimeET`` -- so this guard is scoped to the ``sealed_at`` cell alone, and asserts the
neighbours are NOT swept along with it.

Each check carries a seeded counter-test: a guard that cannot fail proves nothing.
"""

from __future__ import annotations

import pathlib

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"

# The exact regression: the instant formatter applied to the day-marker field.
_INSTANT_FORMATTER_ON_SEALED_AT = "formatDateTimeET(shard.sealed_at"
_DAY_MARKER_FORMATTER_ON_SEALED_AT = "formatDayMarker(shard.sealed_at)"


def _source() -> str:
    return _DESK_PAGE.read_text()


def _sealed_at_cell_check(source: str) -> bool:
    """Pure function of the source text, so the identical check can be re-run against a seeded
    violation below."""
    return (
        _DAY_MARKER_FORMATTER_ON_SEALED_AT in source
        and _INSTANT_FORMATTER_ON_SEALED_AT not in source
    )


def test_the_vault_sealed_at_cell_renders_the_day_marker_lexically():
    """The served ``sealed_at`` is a day marker since iteration 24 -- rendering it through the
    instant formatter prints the previous calendar day plus a spurious 19:00-20:00 ET time."""
    assert _sealed_at_cell_check(_source()) is True, (
        "the Validation Vault 'Sealed at' cell must render shard.sealed_at through "
        "formatDayMarker (lexical, yyyy-MM-dd) -- formatDateTimeET parses the bare date as UTC "
        "midnight and renders the PREVIOUS day with a time-of-day that is not in the record"
    )


def test_the_sealed_at_guard_can_fail_on_the_seeded_pre_fix_violation():
    """The literal pre-fix line, run through the SAME check -- proving the guard bites."""
    seeded = "{formatDateTimeET(shard.sealed_at, { seconds: false })}\n"
    assert _sealed_at_cell_check(seeded) is False


def test_the_neighbouring_instant_columns_keep_the_instant_formatter():
    """Scope pin: ``assigned_at``/``exposed_at`` are still full-precision instants (untouched by
    the iteration-24 coarsening), so they must NOT be converted to day markers -- doing so would
    silently drop a real time-of-day the record does carry."""
    source = _source()
    assert "formatDateTimeET(shard.assigned_at" in source
    assert "formatDateTimeET(shard.exposed_at" in source
    assert "formatDayMarker(shard.assigned_at" not in source
    assert "formatDayMarker(shard.exposed_at" not in source
