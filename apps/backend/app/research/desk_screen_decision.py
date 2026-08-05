"""Skip or re-walk? -- the ONE owner of "does the snapshot already recorded for this date hold that
date's full data", shared verbatim by the compute path (``desk_screen_compute.run_screen_and_record``,
which ACTS on the answer) and the pins route (``desk_screen_pins.resolve_desk_screen_pins``, which
DISCLOSES it before the operator clicks anything). One rule, one implementation -- the panel can
never promise a reuse the run then turns into a walk.

**The problem this replaces.** ``ScreenStore`` deduped on its 5-pin key, whose ``bar_store_signature``
hashes every member's UNCLAMPED latest bar instant. Any top-up -- including bars for days AFTER the
screen date, which cannot change one row of it -- moved that hash, so re-running an older date read
as a brand-new key and wrote a SECOND file for it. The live store carried six such dates, and the
copies were not equivalent: ``2026-07-27`` held ``63 ranked/38 skipped`` from a run taken before its
members' bars had been fetched, beside a later, fuller one.

**The rule.** A date's stored snapshot is REUSED (zero ``compute_tradability`` calls, zero
``BarStore`` reads -- everything below comes from the already-fetched, ``bar_index``-backed coverage
payload ``desk_screen.resolve_screen_pins`` returns) only when ALL FOUR hold:

1. it was computed over the SAME registered universe snapshot;
2. it was computed under the SAME ``config_fingerprint``;
3. its ``screen_coverage_signature`` still matches -- **the bars reach that date**. Clamped to the
   screen's own ``as_of``, so it settles permanently once coverage passes the date (see
   ``desk_screen.screen_coverage_signature``);
4. it already resolved at least as many members as the coverage says are rankable today -- **the
   skip count has not shrunk**. ``rows`` plus the ``"no_basis"`` skips, against
   ``rankable_member_count``.

(3) and (4) are deliberately BOTH required and are not redundant: (3) is the freshness question
("have this date's inputs moved?") and (4) is the completeness question ("did the recorded walk
actually resolve everyone it could?"), and only (4) catches a snapshot left short by a partial walk
under otherwise-identical pins.

**Why (4) terminates rather than re-walking forever.** ``"no_basis"`` skips count as RESOLVED. A
member with a daily series whose every session falls after the screen date is honestly un-rankable
for that date and always will be -- counting it as unresolved would make its date permanently
"incomplete" and re-walk it on every single refresh. A ``"no_bars"`` skip that now HAS bars is the
opposite: genuinely fixable, and exactly the ``63/38 -> 100/1`` signal.

**Legacy snapshots.** Anything recorded before this addition carries no ``screen_coverage_signature``
at all (absent, never ``null`` -- ``desk_screen.py``'s own append-only row-content discipline). There
is no way to reconstruct what its clamped signature WAS, and inventing one would be a fabrication, so
(3) falls back to the pre-existing exact ``bar_store_signature`` pin: identical means nothing
whatsoever has changed, which is strictly stronger than (3) and safely reuses. Anything else is
``replace`` -- one re-walk per date, after which every date carries the new pin and settles.
"""

from __future__ import annotations

# The skip reason that counts as RESOLVED for the completeness check -- see the module docstring.
# `desk_screen.compute_screen` writes exactly two reasons; `"no_bars"` is the fixable one.
_RESOLVED_SKIP_REASON = "no_basis"


def _resolved_member_count(existing: dict) -> int:
    """How many members the recorded walk actually settled: every ranked row, plus every member it
    honestly could not resolve a basis for. Deliberately NOT ``len(rows) + len(skipped)`` -- a
    ``"no_bars"`` skip is a member whose bars had not been fetched yet, which is precisely what a
    re-walk is for."""
    return len(existing["rows"]) + sum(
        1 for skip in existing["skipped"] if skip.get("reason") == _RESOLVED_SKIP_REASON
    )


def resolve_screen_decision(
    existing: dict | None,
    pins: dict,
    *,
    screen_date: str,
    universe_snapshot_id: str | None,
    config_fingerprint: str,
) -> dict:
    """``{"action": "record" | "reuse" | "replace", "screen_id": str | None, "reason": str}`` for
    ONE screen date.

    ``existing`` is ``ScreenStore.find_by_date(screen_date)`` -- the newest snapshot recorded for
    that date, or ``None``. ``pins`` is ``desk_screen.resolve_screen_pins``'s output (one coverage
    fetch, three values). ``screen_id`` names the snapshot the decision is ABOUT: the one a
    ``"reuse"`` serves, or the one a ``"replace"`` will supersede. ``reason`` is a plain operator
    sentence -- the pins panel renders it verbatim, so it names the actual snapshot rather than
    describing the rule in the abstract."""
    if existing is None:
        return {
            "action": "record",
            "screen_id": None,
            "reason": (
                f"no screen is recorded for {screen_date} yet -- a run will walk the registered "
                f"universe and record one."
            ),
        }

    existing_id = existing["id"]

    def replace(reason: str) -> dict:
        return {"action": "replace", "screen_id": existing_id, "reason": reason}

    if existing["universe_snapshot_id"] != universe_snapshot_id:
        return replace(
            f"the registered universe changed since {existing_id} was recorded -- a run will "
            f"re-walk {screen_date} and replace that snapshot."
        )

    if existing["config_fingerprint"] != config_fingerprint:
        return replace(
            f"the config fingerprint changed since {existing_id} was recorded -- a run will "
            f"re-walk {screen_date} and replace that snapshot."
        )

    recorded_coverage_signature = existing.get("screen_coverage_signature")
    if recorded_coverage_signature is None:
        # Legacy: no date-scoped pin was ever recorded for this snapshot. Fall back to the exact
        # pre-existing bar-store pin -- see the module docstring's "Legacy snapshots" section.
        if existing["bar_store_signature"] != pins["bar_store_signature"]:
            return replace(
                f"{existing_id} predates the date-scoped completeness pin and the bar store has "
                f"moved since it was recorded -- a run will re-walk {screen_date} and replace that "
                f"snapshot."
            )
    elif recorded_coverage_signature != pins["screen_coverage_signature"]:
        return replace(
            f"bars have moved for {screen_date} since {existing_id} was recorded -- a run will "
            f"re-walk it and replace that snapshot."
        )

    resolved = _resolved_member_count(existing)
    rankable = pins["rankable_member_count"]
    if resolved < rankable:
        return replace(
            f"{rankable - resolved} more member(s) now have bars than {existing_id} could resolve "
            f"({resolved} of {rankable}) -- a run will re-walk {screen_date} and replace that "
            f"snapshot."
        )

    return {
        "action": "reuse",
        "screen_id": existing_id,
        "reason": (
            f"{screen_date} is already complete: {existing_id} resolved {resolved} of the "
            f"{rankable} member(s) whose bars reach that date, and nothing it was computed from "
            f"has moved since -- a run will reuse it and walk nothing."
        ),
    }
