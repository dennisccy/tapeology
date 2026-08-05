"""Source-introspection guards for the recorded screen's basis note -- the
``test_desk_ui_guards.py`` / ``test_desk_forward_ui_guard.py`` pattern (read the frontend .tsx as
TEXT, assert on substrings; no browser, no runtime).

A screen dated D is marked up from the last completed session STRICTLY BEFORE D
(``tradability._resolve_basis``), and the forward measurement then reads D's own session. The
convention is what makes the product honest -- the screen date names the TRADE day, not the data
day -- and until this note shipped the page never said so, which is precisely how a reader
concludes the forward numbers were measured on the same data the map was built from.

Guards, each proving something a backend-only suite otherwise could not see:

  (a) the note SHIPS -- its testid renders inside ``DeskPopulatedScreen``, so every displayed
      snapshot (latest or a history selection) carries it.
  (b) it is a READ, not a derivation -- ``screenDataThroughDate`` selects the served rows' own
      ``basis_as_of`` and nothing else: no sort, no reorder, no ``rows`` slice, no fetch. The desk
      never recomputes a value the snapshot already recorded (the era's own hard anti-goal), and a
      basis the browser worked out for itself would be exactly that.
  (c) both branches ship, and BOTH clear the copy lint -- including the honest legacy branch for
      snapshots whose rows predate ``basis_as_of`` (rows recorded before goal-desk-iter-9 omit the
      key entirely and are never backfilled).
  (d) the note cannot INTERCEPT a shipped golden. It renders first inside the populated screen, so
      a page-wide (unscoped) golden assertion whose text is a substring of this note would start
      matching here instead of the element it was written for. Goldens scoped to a testid target
      cannot be intercepted and are excluded.

A guard that can never fail proves nothing -- each carries a seeded counter-test proving the
detection logic itself actually catches a violation."""

from __future__ import annotations

import json
import pathlib

from test_copy_discipline import find_violations

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
_JOURNEY_SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "runs" / "goal-session-desk" / "journey-scripts"
)

_BASIS_NOTE_TESTID = 'data-testid="desk-screen-basis-note"'

# The two branches as SOURCE substrings (the interpolations left in place -- pinning them is the
# point: a note that stopped naming the snapshot's own date would be decoration).
_PRESENT_BRANCH = (
    "`Screen for ${snapshot.screen_date} — built from data through ${dataThrough} close "
    "(each ranked row's basis cell names its own session).`"
)
_ABSENT_BRANCH = (
    "`Screen for ${snapshot.screen_date} — the sessions its map was built from are not recorded "
    "in this snapshot's rows.`"
)

# The same two branches as an operator READS them -- what the copy lint and the interception guard
# below must judge (a lint over the raw template literal would judge `${dataThrough}`, not English).
_RENDERED_PRESENT = (
    "Screen for 2026-08-05 — built from data through 2026-08-04 close "
    "(each ranked row's basis cell names its own session)."
)
_RENDERED_ABSENT = (
    "Screen for 2026-08-05 — the sessions its map was built from are not recorded in this "
    "snapshot's rows."
)

# Everything that would make this note a computation rather than a read.
_FORBIDDEN_IN_HELPER = (".sort(", ".reverse(", "rows.slice(", "fetch(", "compute")


def _extract_function(source: str, name: str) -> str:
    """The named function's full body by brace-walk (this suite's convention -- each guard module
    owns its own copy rather than sharing one; see ``test_desk_ui_guards.py``'s twin).

    The parameter list is walked FIRST and skipped: a component destructures its props, so the
    first ``{`` after the name opens the DESTRUCTURING PATTERN, not the body -- walking from there
    would return a props pattern and every assertion over it would pass on an empty haystack."""
    marker = f"function {name}("
    start = source.index(marker)
    paren_depth = 0
    body_start = -1
    for index in range(start + len(marker) - 1, len(source)):
        char = source[index]
        if char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
            if paren_depth == 0:
                body_start = source.index("{", index)
                break
    assert body_start != -1, f"{name}'s parameter list never closes"
    depth = 0
    for index in range(body_start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"{name}'s body never closes")


def test_the_function_extractor_returns_a_body_not_a_props_pattern():
    """A counter-test for the helper: if the walk stops at the destructuring pattern, every ``in``
    assertion over the result silently passes on an empty haystack."""
    seeded = "function Widget({ snapshot }: Props) {\n  return snapshot.screen_date + 1;\n}\n"
    body = _extract_function(seeded, "Widget")
    assert "snapshot.screen_date + 1" in body, "the extractor stopped at the props pattern"
    assert body.endswith("}")


def _unscoped_golden_assertion_texts() -> list[tuple[str, object, str]]:
    """Every literal text a shipped golden asserts PAGE-WIDE -- i.e. with no ``target`` scoping it
    to one element. Only these can be intercepted by a new element rendered earlier in the DOM; a
    scoped assertion looks inside its own testid and never sees this note."""
    found: list[tuple[str, object, str]] = []
    for path in sorted(_JOURNEY_SCRIPTS_DIR.glob("J-*.json")):
        for step in json.loads(path.read_text()).get("steps", []):
            action = step.get("action") or {}
            expect = step.get("expect") or {}
            if action.get("target"):
                continue
            for text in (
                expect.get("text"),
                action.get("text") if action.get("type") == "expect" else None,
            ):
                if isinstance(text, str) and text.strip():
                    found.append((path.name, step.get("n"), text))
    return found


def test_the_basis_note_ships_on_every_displayed_snapshot():
    """(a) The note renders inside ``DeskPopulatedScreen`` itself, not inside one branch of it --
    a snapshot selected from history states its basis exactly as the latest one does."""
    populated = _extract_function(_DESK_PAGE.read_text(), "DeskPopulatedScreen")
    assert _BASIS_NOTE_TESTID in populated, (
        "the recorded screen no longer states the sessions its map was built from -- without it "
        "the screen date reads as the data day, which is the misreading this note exists to stop"
    )
    assert "screenDataThroughDate(snapshot.rows)" in populated, (
        "DeskPopulatedScreen no longer derives the note's date from the DISPLAYED snapshot's own "
        "rows"
    )


def test_the_basis_date_is_selected_from_the_served_rows_never_recomputed():
    """(b) ``screenDataThroughDate`` reads the rows' own recorded ``basis_as_of`` and does nothing
    else to them -- the desk's single-source-of-truth rail, enforced mechanically."""
    helper = _extract_function(_DESK_PAGE.read_text(), "screenDataThroughDate")
    assert "row.basis_as_of" in helper, (
        "screenDataThroughDate no longer reads the rows' own recorded basis"
    )
    hits = [needle for needle in _FORBIDDEN_IN_HELPER if needle in helper]
    assert not hits, (
        f"screenDataThroughDate contains {hits} -- the note must SELECT a date the snapshot "
        "already recorded, never sort, re-window, fetch or recompute one"
    )
    assert "if (value == null) continue;" in helper, (
        "screenDataThroughDate no longer skips rows recorded before basis_as_of existed -- a "
        "legacy row must not be read as a basis"
    )


def test_both_note_branches_ship_and_read_cleanly():
    """(c) The honest-absence branch is as load-bearing as the present one: a pre-iter-9 snapshot
    must say its rows do not record the basis, never show a fabricated or blank date."""
    source = _DESK_PAGE.read_text()
    for branch in (_PRESENT_BRANCH, _ABSENT_BRANCH):
        assert branch in source, f"the basis note no longer ships the branch {branch!r}"
    for rendered in (_RENDERED_PRESENT, _RENDERED_ABSENT):
        assert find_violations(rendered) == [], (
            f"the basis note carries imperative/predictive/claim language: {rendered!r}"
        )


def test_the_basis_note_cannot_intercept_a_shipped_golden():
    """(d) The note renders FIRST inside the populated screen. A page-wide golden assertion whose
    text is a substring of it would silently start matching this note instead of the element the
    journey was written to check -- a green replay proving nothing."""
    texts = _unscoped_golden_assertion_texts()
    assert texts, "no unscoped golden assertions found -- this guard would be vacuous"
    collisions = [
        f"{name} step {n}: {text!r}"
        for name, n, text in texts
        for rendered in (_RENDERED_PRESENT, _RENDERED_ABSENT)
        if text.lower() in rendered.lower() or rendered.lower() in text.lower()
    ]
    assert not collisions, (
        "the basis note's copy would intercept page-wide golden assertions:\n"
        + "\n".join(collisions)
        + "\nreword the note (the goldens are shipped evidence and are never edited to fit new copy)"
    )


def test_the_basis_note_guards_can_fail_on_seeded_violations():
    """Each detection above, seeded."""
    seeded_recompute = (
        "function screenDataThroughDate(rows: DeskScreenRow[]): string | null {\n"
        "  return [...rows].sort((a, b) => 0)[0].basis_as_of;\n"
        "}\n"
    )
    helper = _extract_function(seeded_recompute, "screenDataThroughDate")
    assert [n for n in _FORBIDDEN_IN_HELPER if n in helper] == [".sort("]
    assert "if (value == null) continue;" not in helper

    seeded_populated = "function DeskPopulatedScreen({ snapshot }: Props) {\n  return null;\n}\n"
    assert _BASIS_NOTE_TESTID not in _extract_function(seeded_populated, "DeskPopulatedScreen")

    seeded_collision = "built from data through"
    assert seeded_collision.lower() in _RENDERED_PRESENT.lower()

    assert find_violations("Screen for 2026-08-05 — you should buy this wall now.") != []
