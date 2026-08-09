"""Two operator cleanups over the recorded screens, each dry-run by default and each with its own
explicit CLI flag. They share the printing and the "never unlink a file yourself" discipline, and
nothing else -- the questions they answer are different, and so are their plans.

**Mode 1 (default) -- collapse duplicate copies of a date.** The ONE-TIME migration to one snapshot
per date: every screen date that already carries more than one recorded copy is collapsed to its
newest, and the forward records left pointing at the copies removed are dropped.

This exists because the rule changed, not because anything is broken. ``ScreenStore`` deduped on a
5-pin key whose ``bar_store_signature`` moved on ANY bar top-up -- including bars for days after the
screen date, which cannot change one row of it -- so re-running an older date wrote a second file
for it. ``desk_screen_decision`` now settles a date on every run, so the store converges on its own
from here; this CLI is only for the copies already on disk when the rule changed.

**Dry-run by default.** Prints exactly what it would remove and exits without touching a byte;
``--apply`` is the explicit second step. The ``desk_topup_compute.py``/``desk_screen_compute.py``
CLI precedent, minus their ``--date`` requirement (this one operates on whatever the store holds).

**The safety valve.** A date is collapsed to its NEWEST copy, matching what a run's own
``find_by_date`` would settle on. If that newest copy resolved FEWER members than an older one --
which would mean discarding a richer snapshot in favour of a thinner one -- the date is REFUSED and
reported instead, and every other date still proceeds. Nothing about the live store trips this
today; it exists so that if it ever does, a human decides rather than a script.

**Mode 2 (``--non-sessions``) -- drop screens for dates that never traded.** The desk chain used to
enumerate raw CALENDAR days, so a [From, To] range recorded screens for Saturdays, Sundays, US
market holidays and dates that had not happened yet, each with a forward record that is all-absent
by construction: ~280 of the 939 snapshots on disk on 2026-08-08, and ~272 matching forward records.
The chain and both compute entry points now refuse those dates; this mode is for what they already
left behind.

Mode 1 structurally cannot do this job. ``prune_superseded`` keeps a date's newest copy by
definition, and there is no correct snapshot for a Saturday to be superseded BY -- so mode 2 goes
through ``ScreenStore.prune_dates``, the store's second removal path, which is the only one that
can empty a date.

Which dates qualify is derived from recorded DAILY bars (``desk_sessions``), never a hardcoded
calendar, and fails OPEN: only a date the daily bars BRACKET and do not contain is ever proposed.
A date past the last recorded daily bar is deliberately left alone -- daily bars cannot prove
anything about a session nobody has recorded yet, and a dry run that silently deleted next Monday
would be exactly the kind of surprise this whole module is written to avoid.

The screen and forward RUN ledgers are left untouched by both modes. A run that happened, happened;
the ledgers are the honest record of what was attempted, and pruning them would erase the evidence
that a non-session was ever screened at all.
"""

from __future__ import annotations

import argparse

from ..config import CONFIG
from .desk_forward import ForwardStore, resolve_desk_forward_dir
from .desk_screen import ScreenStore, resolve_desk_screen_dir
from .desk_sessions import is_known_non_session, recorded_session_dates, session_evidence
from .desk_universe import UniverseStore

# A member the recorded walk actually settled -- the SAME accounting `desk_screen_decision` uses
# for its own completeness check (a `"no_bars"` skip is a member whose bars had not been fetched
# yet, so it is not evidence of a richer snapshot).
_RESOLVED_SKIP_REASON = "no_basis"


def _resolved_member_count(record: dict) -> int:
    return len(record["rows"]) + sum(
        1 for skip in record["skipped"] if skip.get("reason") == _RESOLVED_SKIP_REASON
    )


def plan_cleanup(screen_store: ScreenStore, forward_store: ForwardStore) -> dict:
    """What a cleanup WOULD do, computed without touching anything:
    ``{"dates": [...], "refused": [...], "screen_errors": [...]}``.

    Each ``dates`` entry is ``{"screen_date", "keep", "remove", "forward_remove"}`` -- ``keep``/
    ``remove`` carry ``{"id", "created_utc", "resolved"}`` so the printed plan is readable without a
    second lookup. A date holding a single copy is not listed at all (there is nothing to do)."""
    records, screen_errors = screen_store.list()
    forward_records, _forward_errors = forward_store.list()

    by_date: dict[str, list[dict]] = {}
    for record in records:
        by_date.setdefault(record["screen_date"], []).append(record)

    dates: list[dict] = []
    refused: list[dict] = []
    for screen_date in sorted(by_date):
        # `list` is already (created_utc, id)-sorted, so the last entry is the newest -- the SAME
        # copy `ScreenStore.find_by_date` (and therefore a run) would settle on.
        copies = by_date[screen_date]
        if len(copies) < 2:
            continue
        keep, remove = copies[-1], copies[:-1]

        keep_resolved = _resolved_member_count(keep)
        richer = [r for r in remove if _resolved_member_count(r) > keep_resolved]
        if richer:
            refused.append(
                {
                    "screen_date": screen_date,
                    "keep": keep["id"],
                    "keep_resolved": keep_resolved,
                    "richer": [
                        {"id": r["id"], "resolved": _resolved_member_count(r)} for r in richer
                    ],
                }
            )
            continue

        remove_ids = {r["id"] for r in remove}
        dates.append(
            {
                "screen_date": screen_date,
                "keep": {
                    "id": keep["id"], "created_utc": keep["created_utc"],
                    "resolved": keep_resolved,
                },
                "remove": [
                    {
                        "id": r["id"], "created_utc": r["created_utc"],
                        "resolved": _resolved_member_count(r),
                    }
                    for r in remove
                ],
                "forward_remove": [
                    f["id"] for f in forward_records if f["screen_id"] in remove_ids
                ],
            }
        )

    return {"dates": dates, "refused": refused, "screen_errors": screen_errors}


def plan_non_session_cleanup(
    screen_store: ScreenStore, forward_store: ForwardStore, bar_store, members: list[str]
) -> dict:
    """What a non-session cleanup WOULD do, computed without touching anything:
    ``{"dates": [...], "evidence": {...}, "screen_errors": [...]}``.

    Each ``dates`` entry is ``{"screen_date", "remove", "forward_remove"}`` -- ``remove`` carries
    ``{"id", "created_utc"}`` per snapshot so the printed plan is readable without a second lookup.
    Unlike ``plan_cleanup`` there is no ``keep``: the whole point is that no snapshot for such a
    date should exist.

    Deliberately NOT merged into ``plan_cleanup``. That plan answers "this date has too many
    copies"; this one answers "this date should have none" -- different evidence, different
    removal path, different failure mode. Folding them would make a single ``--apply`` capable of
    both, which is precisely the blast radius an operator cleanup should not have.

    ``evidence`` is carried through verbatim so the printed plan states what the proposal rests on.
    With no daily bars recorded it is the honest-unknown block and ``dates`` is empty -- fail open,
    always."""
    records, screen_errors = screen_store.list()
    forward_records, _forward_errors = forward_store.list()

    evidence = session_evidence(bar_store, members)
    sessions = recorded_session_dates(bar_store, members)

    by_date: dict[str, list[dict]] = {}
    for record in records:
        by_date.setdefault(record["screen_date"], []).append(record)

    dates: list[dict] = []
    for screen_date in sorted(by_date):
        if not is_known_non_session(screen_date, sessions, evidence):
            continue
        copies = by_date[screen_date]
        remove_ids = {r["id"] for r in copies}
        dates.append(
            {
                "screen_date": screen_date,
                "remove": [
                    {"id": r["id"], "created_utc": r["created_utc"]} for r in copies
                ],
                "forward_remove": [
                    f["id"] for f in forward_records if f["screen_id"] in remove_ids
                ],
            }
        )

    return {"dates": dates, "evidence": evidence, "screen_errors": screen_errors}


def apply_non_session_cleanup(
    screen_store: ScreenStore, forward_store: ForwardStore, plan: dict
) -> dict:
    """Execute ``plan``'s ``dates`` entries through the stores' OWN removal paths
    (``ScreenStore.prune_dates`` / ``ForwardStore.prune_for_screen``) -- this module never unlinks
    a file itself. The forward records are dropped FIRST, per screen id, so an interruption leaves
    orphaned screens (harmless, and re-planned identically next run) rather than forward records
    pointing at an id nothing can resolve. Returns
    ``{"removed_screens": [...], "removed_forwards": [...]}``."""
    removed_forwards: list[str] = []
    for entry in plan["dates"]:
        for removal in entry["remove"]:
            removed_forwards.extend(forward_store.prune_for_screen(removal["id"]))
    removed_screens = screen_store.prune_dates({entry["screen_date"] for entry in plan["dates"]})
    return {"removed_screens": removed_screens, "removed_forwards": removed_forwards}


def apply_cleanup(screen_store: ScreenStore, forward_store: ForwardStore, plan: dict) -> dict:
    """Execute ``plan``'s ``dates`` entries through the stores' OWN removal paths
    (``ScreenStore.prune_superseded`` / ``ForwardStore.prune_for_screen``) -- this module never
    unlinks a file itself, so the stores' refusals (an unregistered ``keep_id``, a corrupt file
    withheld from the register) still apply verbatim. Returns
    ``{"removed_screens": [...], "removed_forwards": [...]}``."""
    removed_screens: list[str] = []
    removed_forwards: list[str] = []
    for entry in plan["dates"]:
        superseded = screen_store.prune_superseded(entry["screen_date"], entry["keep"]["id"])
        removed_screens.extend(superseded)
        for screen_id in superseded:
            removed_forwards.extend(forward_store.prune_for_screen(screen_id))
    return {"removed_screens": removed_screens, "removed_forwards": removed_forwards}


def _print_plan(plan: dict, *, applied: bool) -> None:
    verb = "Removed" if applied else "Would remove"
    if not plan["dates"] and not plan["refused"]:
        print("Every screen date already holds exactly one snapshot -- nothing to do.")
    for entry in plan["dates"]:
        keep = entry["keep"]
        print(f"\n{entry['screen_date']}:")
        print(f"  keep    {keep['id']}  recorded {keep['created_utc']}  "
              f"{keep['resolved']} member(s) resolved")
        for removal in entry["remove"]:
            print(f"  {verb.lower():<12} {removal['id']}  recorded {removal['created_utc']}  "
                  f"{removal['resolved']} member(s) resolved")
        for forward_id in entry["forward_remove"]:
            print(f"  {verb.lower():<12} {forward_id}  (forward record for a removed snapshot)")
    for refusal in plan["refused"]:
        print(f"\n{refusal['screen_date']}: REFUSED -- the newest copy ({refusal['keep']}) resolved "
              f"{refusal['keep_resolved']} member(s), fewer than "
              + ", ".join(f"{r['id']} ({r['resolved']})" for r in refusal["richer"])
              + ". Left untouched: decide by hand which copy is the right one.")
    for error in plan["screen_errors"]:
        print(f"\nintegrity error, left untouched: {error['file']}: {error['error']}")


def _print_non_session_plan(plan: dict, *, applied: bool) -> None:
    verb = "Removed" if applied else "Would remove"
    evidence = plan["evidence"]
    if not evidence["anchor_symbols"]:
        print(
            "No member holds a recorded daily series, so no date can be shown not to have traded "
            "-- nothing is proposed."
        )
        return
    print(
        f"Sessions derived from the daily bars of {', '.join(evidence['anchor_symbols'])} "
        f"({evidence['from']} through {evidence['through']}, {evidence['sessions_total']} "
        "session(s) recorded). A date outside that span is left alone."
    )
    if not plan["dates"]:
        print("Every recorded screen falls on a date those bars record as a session -- nothing to do.")
    for entry in plan["dates"]:
        print(f"\n{entry['screen_date']}: no daily bar records this date as a session")
        for removal in entry["remove"]:
            print(f"  {verb.lower():<12} {removal['id']}  recorded {removal['created_utc']}")
        for forward_id in entry["forward_remove"]:
            print(f"  {verb.lower():<12} {forward_id}  (forward record for a removed snapshot)")
    for error in plan["screen_errors"]:
        print(f"\nintegrity error, left untouched: {error['file']}: {error['error']}")


def main() -> int:
    """``python -m app.research.desk_screen_cleanup [--non-sessions] [--apply]`` against the
    operator's real screen and forward dirs."""
    parser = argparse.ArgumentParser(
        description="Two cleanups over the recorded screens, dry-run unless --apply is given. By "
        "default: collapse every screen date that carries more than one recorded snapshot down to "
        "its newest copy. With --non-sessions: remove every screen recorded for a date the daily "
        "bars on file show did not trade. Both drop the forward records left pointing at the "
        "snapshots removed."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="actually remove the snapshots; without it this prints the plan and exits having "
        "touched nothing.",
    )
    parser.add_argument(
        "--non-sessions", action="store_true",
        help="run the non-session cleanup instead of the duplicate-copy collapse: remove every "
        "screen recorded for a weekend, a market holiday, or any other date the recorded daily "
        "bars bracket and do not contain. A date past the last recorded daily bar is left alone.",
    )
    args = parser.parse_args()

    universe_dir = CONFIG.desk_universe_dir_resolved()
    screen_store = ScreenStore(resolve_desk_screen_dir(universe_dir))
    forward_store = ForwardStore(resolve_desk_forward_dir(universe_dir))

    if args.non_sessions:
        # Imported here rather than at module scope: the duplicate-copy mode needs neither the bar
        # store nor the universe, and resolving them costs a directory scan it should not pay for.
        from .routes import get_bar_store

        universe_records, _universe_errors = UniverseStore(universe_dir).list()
        members = list(universe_records[-1]["members"]) if universe_records else []
        plan = plan_non_session_cleanup(screen_store, forward_store, get_bar_store(), members)
        if not args.apply:
            print(f"DRY RUN over {screen_store.root} -- nothing will be written.")
            _print_non_session_plan(plan, applied=False)
            print("\nRe-run with --non-sessions --apply to carry this out.")
            return 0
        result = apply_non_session_cleanup(screen_store, forward_store, plan)
        _print_non_session_plan(plan, applied=True)
        print(
            f"\nRemoved {len(result['removed_screens'])} non-session snapshot(s) and "
            f"{len(result['removed_forwards'])} forward record(s) measured against them."
        )
        return 0

    plan = plan_cleanup(screen_store, forward_store)
    if not args.apply:
        print(f"DRY RUN over {screen_store.root} -- nothing will be written.")
        _print_plan(plan, applied=False)
        print("\nRe-run with --apply to carry this out.")
        return 0

    result = apply_cleanup(screen_store, forward_store, plan)
    _print_plan(plan, applied=True)
    print(
        f"\nRemoved {len(result['removed_screens'])} superseded snapshot(s) and "
        f"{len(result['removed_forwards'])} orphaned forward record(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
