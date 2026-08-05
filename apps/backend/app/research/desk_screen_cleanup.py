"""The ONE-TIME migration to one snapshot per date: collapse every screen date that already
carries more than one recorded copy, keeping the newest, and drop the forward records left pointing
at the copies removed.

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
"""

from __future__ import annotations

import argparse

from ..config import CONFIG
from .desk_forward import ForwardStore, resolve_desk_forward_dir
from .desk_screen import ScreenStore, resolve_desk_screen_dir

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


def main() -> int:
    """``python -m app.research.desk_screen_cleanup [--apply]`` against the operator's real screen
    and forward dirs."""
    parser = argparse.ArgumentParser(
        description="Collapse every screen date that carries more than one recorded snapshot down "
        "to its newest copy, dropping the forward records left pointing at the copies removed. "
        "Dry-run unless --apply is given."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="actually remove the superseded snapshots; without it this prints the plan and exits "
        "having touched nothing.",
    )
    args = parser.parse_args()

    universe_dir = CONFIG.desk_universe_dir_resolved()
    screen_store = ScreenStore(resolve_desk_screen_dir(universe_dir))
    forward_store = ForwardStore(resolve_desk_forward_dir(universe_dir))

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
