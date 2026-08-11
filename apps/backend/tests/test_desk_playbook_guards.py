"""goal-playbook-iter-4 (J-04) -- two new structural guards, source-introspection style (the
``test_copy_discipline.py``/``test_desk_ui_guards.py`` pattern: read a module as TEXT, assert on
substrings/regex; no runtime, no import-time side effects beyond reading the file).

(a) TC-12 -- the no-threshold-sweep guard: no playbook module (``desk_playbook.py``,
    ``desk_playbook_detect.py``, ``desk_playbook_features.py``) contains a ``for``/comprehension
    loop that iterates OVER a ``PLAYBOOK_*`` name, or over a literal sequence of two-or-more
    numeric candidates, to select a threshold -- the concrete, module-scoped form of the
    Playbook-era anti-goal "no code path iterates thresholds against outcomes". Every genuine loop
    in these three modules today walks BAR DATA (``for symbol in members``, ``for t in
    range(min_bars, n)``, ``for left in highs``, ...), never a threshold candidate list -- this
    guard makes that structural fact machine-checked, permanently.

(b) TC-13 -- the import-graph guard: ``desk_playbook_detect.py`` imports nothing named
    ``*evidence*`` -- a forward guard against ``desk_playbook_evidence.py``, which does not exist
    yet (J-08). Locking the required detect -> evidence import direction to NEVER EXISTING before
    it is even possible to violate it, per the goal's own "no second implementation" /
    single-source-of-truth discipline (the evidence view reads recorded playbook FILES, it must
    never let a detector reach into it).

Both guards carry a seeded counter-test (the ``test_copy_discipline.py`` precedent: "a lint that
can never fail proves nothing")."""

from __future__ import annotations

import pathlib
import re

from app.research import desk_playbook as desk_playbook_module
from app.research import desk_playbook_detect as desk_playbook_detect_module
from app.research import desk_playbook_features as desk_playbook_features_module

_PLAYBOOK_MODULES = (
    desk_playbook_module,
    desk_playbook_detect_module,
    desk_playbook_features_module,
)

# --- (a) the no-threshold-sweep guard ---------------------------------------------------------------

# A `for`/comprehension `in` clause naming a `PLAYBOOK_*` constant as (part of) its OWN iterable --
# e.g. `for x in PLAYBOOK_THRESHOLDS:` or `for x in [PLAYBOOK_A, PLAYBOOK_B]:`. Scoped to the
# clause between `in` and the next `:`/`]`/`)` so a `PLAYBOOK_*` reference elsewhere on the SAME
# line (a body statement on one line, or a trailing comment) is not what is being matched.
#
# Excludes the module's own documented "companion structural constants (shape, not thresholds)"
# (``desk_playbook.py``'s own comment beside ``PLAYBOOK_SETUPS``) -- ``compute_playbook`` already
# (J-02, unmodified this iteration) iterates ``PLAYBOOK_SIGNAL_MEASURES`` to build one summary cell
# per already-fixed measure KEY, which is not "picking a threshold" in any sense the anti-goal
# means; flagging it would be a false positive on already-shipped, unrelated code, not a real
# violation this guard exists to catch.
_STRUCTURAL_PLAYBOOK_CONSTANTS = (
    "SETUPS",
    "MARKET_SYMBOL",
    "BASELINE_SEED",
    "RETURN_SIGN_CONVENTION",
    "SIGNAL_MEASURES",
    "MIN_N_DISCLOSURE",
)
_SWEEP_OVER_NAMED_CONSTANT = re.compile(
    r"for\s+\w+(?:\s*,\s*\w+)*\s+in\s+[^\n:]*PLAYBOOK_(?!"
    + "|".join(rf"{name}\b" for name in _STRUCTURAL_PLAYBOOK_CONSTANTS)
    + r")"
)

# A `for`/comprehension iterating directly over a LITERAL sequence of two-or-more numeric
# candidates -- e.g. `for mult in [0.5, 1.0, 1.5]:` or `for k in (1, 2, 3):` -- the "candidate-value
# sequence to pick a threshold" the goal's own Anti-goals name, written out by hand rather than
# named.
_SWEEP_OVER_LITERAL_SEQUENCE = re.compile(
    r"for\s+\w+\s+in\s+[\(\[]\s*-?\d+(?:\.\d+)?\s*(?:,\s*-?\d+(?:\.\d+)?\s*){1,}[\)\]]"
)


def _strip_comments_and_docstrings(source: str) -> str:
    """The ``test_desk_playbook.py``/``test_desk_ui_guards.py`` precedent, applied here too: a
    source-scan guard must scan CODE, not the prose that explains it (this file's own module
    docstring, and every detector docstring discussing the anti-goal in prose, would otherwise
    false-positive a guard that is supposed to be scanning for real loops)."""
    without_triple_double = re.sub(r'"""(?:.|\n)*?"""', "", source)
    without_triple_single = re.sub(r"'''(?:.|\n)*?'''", "", without_triple_double)
    return re.sub(r"#[^\n]*", "", without_triple_single)


def test_no_playbook_module_iterates_over_a_named_playbook_constant():
    """TC-12: zero ``for``/comprehension loops whose iterable names a ``PLAYBOOK_*`` constant, in
    any of the three playbook modules."""
    for module in _PLAYBOOK_MODULES:
        source = _strip_comments_and_docstrings(open(module.__file__, encoding="utf-8").read())
        hits = _SWEEP_OVER_NAMED_CONSTANT.findall(source)
        assert not hits, (
            f"{module.__file__} contains a loop iterating over a PLAYBOOK_* constant ({hits}) -- "
            "no code path may sweep a threshold, per the Playbook-era anti-goal"
        )


def test_no_playbook_module_iterates_over_a_literal_threshold_candidate_sequence():
    """TC-12: zero ``for``/comprehension loops whose iterable is a literal sequence of two-or-more
    numeric candidates."""
    for module in _PLAYBOOK_MODULES:
        source = _strip_comments_and_docstrings(open(module.__file__, encoding="utf-8").read())
        hits = _SWEEP_OVER_LITERAL_SEQUENCE.findall(source)
        assert not hits, (
            f"{module.__file__} contains a loop iterating over a literal numeric sequence ({hits}) "
            "-- no code path may sweep a candidate threshold value, per the Playbook-era anti-goal"
        )


def test_no_threshold_sweep_guard_can_fail_on_seeded_violations():
    """The lint CAN fail on both shapes it is meant to catch (the ``test_copy_discipline.py``
    seeded-violation precedent) -- and does NOT false-positive on the real loops this iteration's
    own detectors actually use."""
    seeded_named_constant = "for candidate in PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION_CANDIDATES:\n    pass\n"
    assert _SWEEP_OVER_NAMED_CONSTANT.search(seeded_named_constant) is not None

    seeded_named_constant_in_list = "for mult in [PLAYBOOK_JUMP_MIN_MULT, PLAYBOOK_STOP_PAD_FRAC]:\n    pass\n"
    assert _SWEEP_OVER_NAMED_CONSTANT.search(seeded_named_constant_in_list) is not None

    seeded_literal_sequence = "for mult in [0.5, 1.0, 1.5, 2.0]:\n    pass\n"
    assert _SWEEP_OVER_LITERAL_SEQUENCE.search(seeded_literal_sequence) is not None

    seeded_literal_tuple = "for k in (1, 2, 3):\n    pass\n"
    assert _SWEEP_OVER_LITERAL_SEQUENCE.search(seeded_literal_tuple) is not None

    # Real loops this iteration's own detectors use -- must NOT be flagged by either pattern.
    benign_loops = [
        "for symbol in members:\n    pass\n",
        "for t in range(min_bars, n):\n    pass\n",
        "for left_i, left in enumerate(highs):\n    pass\n",
        "for right in highs[left_i + 1 :]:\n    pass\n",
        "for idx, bar in enumerate(lookback_bars, start=start_idx - lookback):\n    pass\n",
        "for _ in range(params['max_jbe_signals_per_session']):\n    pass\n",
    ]
    for benign in benign_loops:
        assert _SWEEP_OVER_NAMED_CONSTANT.search(benign) is None, benign
        assert _SWEEP_OVER_LITERAL_SEQUENCE.search(benign) is None, benign

    # The already-shipped, unrelated J-02 loop this guard's own structural exclusion exists for --
    # proves the exclusion is scoped to the EXACT documented structural-constant names, not a
    # prefix match that would also swallow a genuine violation sharing a name prefix.
    already_shipped_structural_loop = "for key in PLAYBOOK_SIGNAL_MEASURES:\n    pass\n"
    assert _SWEEP_OVER_NAMED_CONSTANT.search(already_shipped_structural_loop) is None

    not_actually_excluded = "for x in PLAYBOOK_SETUPS_CANDIDATES:\n    pass\n"
    assert _SWEEP_OVER_NAMED_CONSTANT.search(not_actually_excluded) is not None


# --- (b) the import-graph guard: detect never imports evidence -------------------------------------

# `[ \t]*` (never `\s*`) for the leading indent -- `\s` also matches `\n`, which under
# `re.MULTILINE` would let a blank line's own `^` swallow the newline reaching for the NEXT
# line's `from`/`import`, merging two lines into one match (a genuine regex trap, caught by the
# counter-test below).
_IMPORT_LINE = re.compile(r"^[ \t]*(?:from|import)\s+.*$", re.MULTILINE)


def _import_lines(source: str) -> list[str]:
    return _IMPORT_LINE.findall(source)


def test_detect_module_imports_nothing_named_evidence():
    """TC-13: ``desk_playbook_detect.py`` has zero import statement referencing anything named
    ``*evidence*`` -- ``desk_playbook_evidence.py`` does not exist yet (J-08); this guard locks
    the required detect -> evidence import direction to never having existed, so it can never be
    silently introduced later either."""
    source = open(desk_playbook_detect_module.__file__, encoding="utf-8").read()
    hits = [line for line in _import_lines(source) if "evidence" in line.lower()]
    assert not hits, (
        f"desk_playbook_detect.py imports {hits} -- the detect module must never import anything "
        "named *evidence* (forward-guards the required detect -> evidence import direction, J-08)"
    )


def test_import_graph_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail: a seeded ``from .desk_playbook_evidence import ...`` line is caught."""
    seeded_source = (
        "from __future__ import annotations\n\n"
        "from .desk_playbook_evidence import fold_evidence\n\n"
        "def f():\n    pass\n"
    )
    hits = [line for line in _import_lines(seeded_source) if "evidence" in line.lower()]
    assert hits == ["from .desk_playbook_evidence import fold_evidence"]


def test_import_graph_guard_does_not_false_positive_on_the_real_detect_module():
    """A sanity companion to the guard above: the real file's own (legitimate) imports are never
    mistaken for the seeded violation shape."""
    source = open(desk_playbook_detect_module.__file__, encoding="utf-8").read()
    real_imports = _import_lines(source)
    assert any("desk_playbook_features" in line for line in real_imports)
    assert not any("evidence" in line.lower() for line in real_imports)


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def test_desk_playbook_evidence_module_does_not_exist_yet():
    """A companion structural fact this guard's own docstring leans on: ``desk_playbook_evidence.py``
    genuinely does not exist yet this iteration (J-08) -- the import-graph guard above is a forward
    guard, not (yet) an enforcement of an existing exclusion."""
    evidence_path = (
        _repo_root() / "apps" / "backend" / "app" / "research" / "desk_playbook_evidence.py"
    )
    assert not evidence_path.exists()
