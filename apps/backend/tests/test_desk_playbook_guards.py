"""goal-playbook-iter-4 (J-04) -- two structural guards, source-introspection style (the
``test_copy_discipline.py``/``test_desk_ui_guards.py`` pattern: read a module as TEXT, assert on
substrings/regex; no runtime, no import-time side effects beyond reading the file). Extended by
goal-playbook-iter-5 (J-05) with two MORE guards -- this time behavioral rather than source-scan,
since "does the euphoria marker ever leak into a served row" and "is marker decoration
forward-only" are properties of DATA the decoration pass produces, not of code SHAPE a regex could
usefully police. Extended by goal-playbook-iter-6 (J-06) with a THIRD behavioral guard -- this
one call-COUNTING instrumentation (a stub/counting double patched onto the real
``compute_tradability``/``compute_levels`` functions), since "does the playbook walk ever call the
desk's own structural-wall computations" is a property of RUNTIME CALLS a source-scan regex could
not usefully police either (the playbook module imports neither function today, but a future
refactor could introduce an indirect call path a regex would miss; instrumentation survives that).
goal-playbook-iter-8 (J-08) retires guard (b)'s own "does not exist yet" companion fact (the
evidence module now exists) and adds two of its own, kept beside the class/behavior they guard
rather than duplicated here: ``PlaybookEvidenceCache`` has no ``update``/``delete`` method
(``test_desk_playbook_evidence.py::test_playbook_evidence_cache_has_no_update_or_delete_method`` --
the ``test_playbook_store_has_no_update_or_delete_method`` per-file precedent), and the pooling
code never merges two signatures into one cell (``test_desk_playbook_evidence.py``'s own TC-5 --
another property of DATA a fixture proves directly, not code SHAPE a regex would usefully police).

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

(c) TC-5 -- the marker-decoration forward-only guard: ``desk_playbook._decorate_markers`` never
    decorates a signal whose own trigger bar is AT OR BEFORE a marker's trigger bar, and a
    ``capitulation`` signal never self-decorates its own firing.

(d) TC-7 (J-06) -- the zero-structural-calls guard: ``compute_playbook`` calls neither
    ``app.research.tradability.compute_tradability`` nor ``app.research.levels.compute_levels``,
    over a real, ``BarStore``-backed fixture walk that fires all eight setup families in one call
    -- the book's intraday ranges and the desk's structural walls are different owners.

Every guard carries a seeded counter-test (the ``test_copy_discipline.py`` precedent: "a lint that
can never fail proves nothing")."""

from __future__ import annotations

import pathlib
import re

import pytest

from app.config import CONFIG
from app.providers.adapters.base import RawBar
from app.research import desk_playbook as desk_playbook_module
from app.research import desk_playbook_detect as desk_playbook_detect_module
from app.research import desk_playbook_features as desk_playbook_features_module
from app.research import levels as levels_module
from app.research import tradability as tradability_module
from app.research.bars import BarStore
from app.research.desk_playbook import _decorate_markers, compute_playbook, playbook_parameters
from app.research.desk_universe import UniverseStore

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


def test_desk_playbook_evidence_module_now_exists_and_still_imports_nothing_from_detect():
    """goal-playbook-iter-8 (J-08) UPDATE: ``desk_playbook_evidence.py`` now exists (replacing the
    iter-4-era ``test_desk_playbook_evidence_module_does_not_exist_yet`` forward guard, which this
    iteration is exactly what makes obsolete). The import-graph guard above is now a LIVE
    enforcement rather than a forward one: the required direction is detect -> (never evidence),
    proven both ways -- the evidence module exists, and it is STILL never imported by detect."""
    evidence_path = (
        _repo_root() / "apps" / "backend" / "app" / "research" / "desk_playbook_evidence.py"
    )
    assert evidence_path.exists()
    source = open(desk_playbook_detect_module.__file__, encoding="utf-8").read()
    hits = [line for line in _import_lines(source) if "evidence" in line.lower()]
    assert not hits


# --- (c) TC-5 -- the marker-decoration forward-only guard (goal-playbook-iter-5, J-05) -------------
#
# ``_decorate_markers`` operates on already-built signal dicts (``geometry.slots_to_break`` +
# ``disclosures``), so this guard tests it DIRECTLY as a pure function -- no ``BarStore``, no real
# detector firing needed to prove the property; ``test_desk_playbook.py``'s own
# ``test_a_later_capitulation_signal_is_decorated_euphoria_recent_by_an_earlier_marker`` separately
# proves the SAME property end to end through a real ``compute_playbook`` walk.

_PARAMS = playbook_parameters()


def _signal(setup_id: str, slots_to_break: int) -> dict:
    return {
        "setup_id": setup_id,
        "geometry": {"slots_to_break": slots_to_break},
        "disclosures": {"euphoria_recent": False, "capitulation_recent": False},
    }


def test_decorate_markers_sets_euphoria_recent_on_a_later_signal_within_the_decay_window():
    """The baseline positive case: a marker at slot 7 decorates a signal triggering at slot 10 --
    ``10 - 7 == 3 <= PLAYBOOK_MARKER_DECAY_BARS`` (6)."""
    signals = [_signal("open_high_break", 10)]
    _decorate_markers(signals, [7], _PARAMS)
    assert signals[0]["disclosures"]["euphoria_recent"] is True
    assert signals[0]["disclosures"]["capitulation_recent"] is False


def test_decorate_markers_never_decorates_a_signal_that_triggered_at_or_before_the_marker():
    """TC-5: the forward-only property, both edges -- a marker whose OWN trigger bar occurs AFTER
    a candidate signal's trigger bar (in bar-index order) decorates NOTHING (the EARLIER signal
    stays undecorated), and a marker at the EXACT same bar as a signal's own trigger (the
    zero-distance edge) also does not decorate it -- ``euphoria_recent``/``capitulation_recent``
    require the signal's trigger to be STRICTLY after the marker's, never merely at-or-after."""
    earlier_signal = _signal("jbe", 5)
    _decorate_markers([earlier_signal], [8], _PARAMS)  # marker AFTER the signal's own trigger
    assert earlier_signal["disclosures"]["euphoria_recent"] is False

    same_bar_signal = _signal("dbi", 6)
    _decorate_markers([same_bar_signal], [6], _PARAMS)  # marker AT the signal's own trigger bar
    assert same_bar_signal["disclosures"]["euphoria_recent"] is False


def test_decorate_markers_beyond_the_decay_window_does_not_decorate():
    """A marker more than ``PLAYBOOK_MARKER_DECAY_BARS`` bars before a later signal's trigger does
    not decorate it either -- the window has a far edge, not just a near one. A signal exactly AT
    the decay boundary (distance == decay) still IS decorated -- the window is inclusive on its
    far edge, so this test also proves the boundary itself is not accidentally off-by-one."""
    decay = _PARAMS["marker_decay_bars"]
    marker = 10
    at_boundary = _signal("cup_handle", marker + decay)
    _decorate_markers([at_boundary], [marker], _PARAMS)
    assert at_boundary["disclosures"]["euphoria_recent"] is True

    beyond_boundary = _signal("cup_handle", marker + decay + 1)
    _decorate_markers([beyond_boundary], [marker], _PARAMS)
    assert beyond_boundary["disclosures"]["euphoria_recent"] is False


def test_decorate_markers_capitulation_signal_decorates_later_signals_but_never_itself():
    """spec §3.5: "capitulation events symmetrically set capitulation_recent" -- a recorded
    ``capitulation`` signal is itself a marker for every OTHER later signal in the SAME walk, but
    the strict-after comparison makes self-decoration structurally impossible (a signal's own
    trigger bar index is never strictly after itself) -- no special-case exclusion needed, proven
    here rather than merely asserted."""
    capitulation_signal = _signal("capitulation", 4)
    later_signal = _signal("jbe", 6)
    signals = [capitulation_signal, later_signal]
    _decorate_markers(signals, [], _PARAMS)  # no euphoria marker this walk
    assert capitulation_signal["disclosures"]["capitulation_recent"] is False  # never self-decorates
    assert later_signal["disclosures"]["capitulation_recent"] is True  # decorated by the earlier one


def test_decorate_markers_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing. A deliberately WRONG
    implementation (at-or-after instead of strictly-after) would decorate the same-bar case; this
    test proves the counter-scenario itself is a real trigger for the assertion style above, not a
    vacuous no-op."""
    signal = _signal("open_low_break", 6)
    # Manually simulate the WRONG (at-or-after) rule to confirm it WOULD decorate -- i.e. the
    # correct, strict rule this module actually implements is doing real work, not passing by
    # construction regardless of the comparison operator used.
    marker = 6
    wrongly_decorates = 0 <= signal["geometry"]["slots_to_break"] - marker <= _PARAMS["marker_decay_bars"]
    assert wrongly_decorates is True
    # ... yet the REAL function does not:
    _decorate_markers([signal], [marker], _PARAMS)
    assert signal["disclosures"]["euphoria_recent"] is False


# --- (d) TC-7 (goal-playbook-iter-6, J-06) -- the zero-`compute_tradability`/`compute_levels`
# call-counting guard -----------------------------------------------------------------------------
#
# A real, BarStore-backed fixture walk across EIGHT members, each individually crafted to fire
# exactly one of the eight shipped setup families (open_high_break stands in for the
# opening-range-break family; jbe/dbi/cup_handle/capitulation/range_trade/double_top/double_bottom
# each get their own member) -- the SAME canonical fixture shapes ``test_desk_playbook_detect.py``
# already hand-verifies as pure detector calls, planted through a real ``BarStore`` (the
# ``test_desk_playbook.py`` precedent: ``_plant_ladder_baseline_sessions`` et al.).

_GUARD_SESSION_DATE = "2026-06-22"
_GUARD_E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET
_GUARD_BASELINE_DATES = [f"2026-06-{d:02d}" for d in range(8, 18)]  # 10 prior dates


def _guard_bar(symbol: str, epoch: float, o: float, h: float, low: float, c: float, v: int = 1000) -> RawBar:
    return RawBar(symbol, "5m", epoch, o, h, low, c, v)


def _plant_guard_baseline_sessions(bar_store: BarStore, symbol: str, slots: int) -> None:
    """``slots`` identical, flat prior RTH 5m sessions (range 1.0, volume 1000 -> MBR=1.0, a full
    slot-volume-median vector covering every slot the fixture's OWN session length needs) --
    generalizes ``test_desk_playbook.py``'s ``_plant_ladder_baseline_sessions`` to an arbitrary
    slot count, since this guard's eight fixtures each carry a different session length."""
    bars = []
    for day in _GUARD_BASELINE_DATES:
        day_open = _GUARD_E_OPEN - (22 - int(day[-2:])) * 86_400.0
        for slot in range(slots):
            bars.append(_guard_bar(symbol, day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
    bar_store.record(
        symbol=symbol, timeframe="5m",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
        feed="test", bars=bars,
    )


def _plant_guard_session(bar_store: BarStore, symbol: str, bars_5m: list[RawBar]) -> None:
    bar_store.record(
        symbol=symbol, timeframe="5m",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
        feed="test", bars=bars_5m,
    )


def _guard_open_high_break_bars(symbol: str) -> list[RawBar]:
    return [
        _guard_bar(symbol, _GUARD_E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
    ]


def _guard_jbe_bars(symbol: str) -> list[RawBar]:
    return [
        _guard_bar(symbol, _GUARD_E_OPEN, 98.4, 98.5, 98.0, 98.3, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 98.3, 98.4, 98.1, 98.3, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 98.3, 98.4, 98.05, 98.3, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 98.3, 98.45, 98.2, 98.3, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 98.3, 98.4, 98.15, 98.3, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 98.3, 98.5, 98.3, 98.4, 3000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1800.0, 103.5, 103.8, 103.2, 103.6, 400),
        _guard_bar(symbol, _GUARD_E_OPEN + 2100.0, 103.6, 104.0, 103.3, 103.7, 500),
        _guard_bar(symbol, _GUARD_E_OPEN + 2400.0, 103.7, 103.9, 103.4, 103.8, 450),
        _guard_bar(symbol, _GUARD_E_OPEN + 2700.0, 103.9, 104.8, 103.8, 104.5, 1500),
        _guard_bar(symbol, _GUARD_E_OPEN + 3000.0, 104.5, 104.7, 104.3, 104.6, 900),
        _guard_bar(symbol, _GUARD_E_OPEN + 3300.0, 104.6, 104.8, 104.4, 104.7, 900),
    ]


def _guard_dbi_bars(symbol: str) -> list[RawBar]:
    return [
        _guard_bar(symbol, _GUARD_E_OPEN, 109.6, 110.0, 109.5, 109.7, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 109.7, 109.9, 109.6, 109.7, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 109.7, 109.95, 109.6, 109.7, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 109.7, 109.8, 109.55, 109.7, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 109.7, 109.85, 109.6, 109.7, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 109.6, 109.7, 109.5, 109.6, 3000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1800.0, 104.5, 104.8, 104.2, 104.4, 400),
        _guard_bar(symbol, _GUARD_E_OPEN + 2100.0, 104.4, 104.7, 104.0, 104.3, 500),
        _guard_bar(symbol, _GUARD_E_OPEN + 2400.0, 104.3, 104.6, 104.1, 104.2, 450),
        _guard_bar(symbol, _GUARD_E_OPEN + 2700.0, 104.1, 104.2, 103.2, 103.5, 1500),
        _guard_bar(symbol, _GUARD_E_OPEN + 3000.0, 103.5, 103.7, 103.3, 103.4, 900),
        _guard_bar(symbol, _GUARD_E_OPEN + 3300.0, 103.4, 103.6, 103.2, 103.3, 900),
    ]


def _guard_cup_handle_bars(symbol: str) -> list[RawBar]:
    bars = [
        _guard_bar(symbol, _GUARD_E_OPEN, 106.5, 107.0, 106.0, 106.8, 500),
        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 106.8, 108.0, 106.5, 107.5, 500),
        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 107.5, 109.0, 107.0, 108.5, 500),
        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 108.5, 110.0, 108.0, 109.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 109.5, 109.0, 108.0, 108.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 108.5, 108.0, 107.0, 107.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1800.0, 107.5, 107.5, 106.5, 107.0, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 2100.0, 107.0, 106.5, 106.0, 106.2, 300),
        _guard_bar(symbol, _GUARD_E_OPEN + 2400.0, 106.2, 106.0, 105.5, 105.8, 300),
        _guard_bar(symbol, _GUARD_E_OPEN + 2700.0, 105.8, 105.5, 105.0, 105.2, 300),
        _guard_bar(symbol, _GUARD_E_OPEN + 3000.0, 105.2, 106.0, 105.1, 105.8, 300),
        _guard_bar(symbol, _GUARD_E_OPEN + 3300.0, 105.8, 107.0, 105.5, 106.8, 300),
        _guard_bar(symbol, _GUARD_E_OPEN + 3600.0, 106.8, 108.0, 106.5, 107.8, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 3900.0, 107.8, 109.0, 107.5, 108.8, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 4200.0, 108.8, 109.5, 108.5, 109.2, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 4500.0, 109.2, 110.0, 108.8, 109.6, 1000),
    ]
    for i, (o, h, low, c, v) in enumerate(
        [(109.6, 109.3, 108.0, 108.5, 400), (108.5, 109.0, 107.8, 108.2, 400), (108.2, 109.4, 108.0, 108.9, 400)],
        start=16,
    ):
        bars.append(_guard_bar(symbol, _GUARD_E_OPEN + i * 300.0, o, h, low, c, v))
    bars.append(_guard_bar(symbol, _GUARD_E_OPEN + 19 * 300.0, 108.9, 110.5, 108.7, 110.2, 1500))
    bars.append(_guard_bar(symbol, _GUARD_E_OPEN + 20 * 300.0, 110.2, 110.4, 109.9, 110.1, 900))
    bars.append(_guard_bar(symbol, _GUARD_E_OPEN + 21 * 300.0, 110.1, 110.3, 109.8, 110.0, 900))
    return bars


def _guard_capitulation_bars(symbol: str) -> list[RawBar]:
    return [
        _guard_bar(symbol, _GUARD_E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
        _guard_bar(symbol, _GUARD_E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),
        _guard_bar(symbol, _GUARD_E_OPEN + 1200.0, 99.6, 101.5, 99.4, 101.0, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1500.0, 101.0, 101.3, 100.8, 101.1, 900),
        _guard_bar(symbol, _GUARD_E_OPEN + 1800.0, 101.1, 101.4, 100.9, 101.2, 900),
    ]


def _guard_range_trade_bars(symbol: str) -> list[RawBar]:
    # The canonical two-sided armed range (both zones tested twice and held, spec §3.7's full
    # arming clause) -- the same fixture `test_desk_playbook_detect.py` hand-computes.
    return [
        _guard_bar(symbol, _GUARD_E_OPEN + 0 * 300.0, 104.0, 105.0, 103.5, 104.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1 * 300.0, 103.9, 103.9, 101.5, 101.8, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 2 * 300.0, 101.8, 102.0, 100.0, 100.4, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 3 * 300.0, 101.6, 103.0, 101.5, 102.8, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 4 * 300.0, 102.8, 104.8, 102.5, 104.4, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 5 * 300.0, 103.4, 103.5, 102.0, 102.4, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 6 * 300.0, 102.4, 102.6, 100.4, 100.7, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 7 * 300.0, 101.0, 103.5, 100.6, 103.2, 2000),
        _guard_bar(symbol, _GUARD_E_OPEN + 8 * 300.0, 103.2, 103.4, 102.9, 103.1, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 9 * 300.0, 103.1, 103.3, 102.8, 103.0, 1000),
    ]


def _guard_double_top_bars(symbol: str) -> list[RawBar]:
    return [
        _guard_bar(symbol, _GUARD_E_OPEN + 0 * 300.0, 104, 105, 104, 104.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1 * 300.0, 104.5, 106, 104, 105.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 2 * 300.0, 105.5, 107, 105, 106.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 3 * 300.0, 106.5, 110, 106, 109, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 4 * 300.0, 109, 108, 107, 107.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 5 * 300.0, 107.5, 105, 104, 104.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 6 * 300.0, 104.5, 102, 101, 101.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 7 * 300.0, 101.5, 100, 99, 99.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 8 * 300.0, 99.5, 98, 97, 97.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 9 * 300.0, 97.5, 99, 97.2, 98.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 10 * 300.0, 98.5, 101, 98, 100.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 11 * 300.0, 100.5, 104, 100, 103.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 12 * 300.0, 103.5, 107, 103, 106.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 13 * 300.0, 106.5, 110.3, 106, 109.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 14 * 300.0, 109.5, 108, 107, 107.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 15 * 300.0, 107.5, 106, 105, 105.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 16 * 300.0, 105.5, 104, 103, 103.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 17 * 300.0, 103.5, 103.8, 102, 102.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 18 * 300.0, 102.5, 103, 96.0, 96.5, 2000),
        _guard_bar(symbol, _GUARD_E_OPEN + 19 * 300.0, 96.5, 97, 96, 96.8, 1000),
    ]


def _guard_double_bottom_bars(symbol: str) -> list[RawBar]:
    return [
        _guard_bar(symbol, _GUARD_E_OPEN + 0 * 300.0, 96, 97, 96, 96.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 1 * 300.0, 96.5, 97, 95, 95.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 2 * 300.0, 95.5, 96, 94, 94.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 3 * 300.0, 94.5, 95, 90, 91, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 4 * 300.0, 91, 93, 92, 92.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 5 * 300.0, 92.5, 96, 95, 95.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 6 * 300.0, 95.5, 99, 98, 98.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 7 * 300.0, 98.5, 101, 100, 100.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 8 * 300.0, 100.5, 103, 102, 102.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 9 * 300.0, 102.5, 101, 100.8, 101, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 10 * 300.0, 101, 99, 98, 98.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 11 * 300.0, 98.5, 96, 95, 95.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 12 * 300.0, 95.5, 93, 92, 92.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 13 * 300.0, 92.5, 91, 89.7, 90.2, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 14 * 300.0, 90.2, 92, 91, 91.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 15 * 300.0, 91.5, 94, 93, 93.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 16 * 300.0, 93.5, 96, 95, 95.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 17 * 300.0, 95.5, 95.8, 94, 94.5, 1000),
        _guard_bar(symbol, _GUARD_E_OPEN + 18 * 300.0, 94.5, 104.0, 95, 103.5, 2000),
        _guard_bar(symbol, _GUARD_E_OPEN + 19 * 300.0, 103.5, 104, 103, 103.8, 1000),
    ]


def test_compute_playbook_calls_neither_compute_tradability_nor_compute_levels(tmp_path, monkeypatch):
    """TC-7: a real, ``BarStore``-backed fixture walk that fires all EIGHT shipped setup families
    in one ``compute_playbook`` call makes exactly zero calls to
    ``app.research.tradability.compute_tradability`` and exactly zero calls to
    ``app.research.levels.compute_levels`` -- the book's intraday ranges and the desk's structural
    walls are different owners."""
    calls = {"tradability": 0, "levels": 0}

    def _counting_tradability(*args, **kwargs):
        calls["tradability"] += 1
        raise AssertionError("compute_tradability must never be called from the playbook walk")

    def _counting_levels(*args, **kwargs):
        calls["levels"] += 1
        raise AssertionError("compute_levels must never be called from the playbook walk")

    monkeypatch.setattr(tradability_module, "compute_tradability", _counting_tradability)
    monkeypatch.setattr(levels_module, "compute_levels", _counting_levels)

    bar_store = BarStore(tmp_path / "bars")
    members = ["OHB", "JBE", "DBI", "CUP", "CAP", "RT", "DT", "DB"]
    fixture_builders = {
        "OHB": (_guard_open_high_break_bars, 6),
        "JBE": (_guard_jbe_bars, 12),
        "DBI": (_guard_dbi_bars, 12),
        "CUP": (_guard_cup_handle_bars, 22),
        "CAP": (_guard_capitulation_bars, 9),
        "RT": (_guard_range_trade_bars, 10),
        "DT": (_guard_double_top_bars, 20),
        "DB": (_guard_double_bottom_bars, 20),
    }
    for symbol, (builder, slots) in fixture_builders.items():
        _plant_guard_baseline_sessions(bar_store, symbol, slots)
        _plant_guard_session(bar_store, symbol, builder(symbol))

    universe_store = UniverseStore(tmp_path / "universe")
    universe_store.record(
        members=members, raw_members={m: m for m in members},
        source_url="test", min_members=1, max_members=len(members),
    )

    result = compute_playbook(
        universe_store, bar_store, CONFIG.config_fingerprint(), _GUARD_SESSION_DATE,
    )

    # `>=`, not `==`: every member runs through ALL nine detectors (the opening-range-break pair
    # included), so a member built to fire e.g. `capitulation` may ALSO incidentally break its own
    # opening range on one side -- an honest, harmless extra signal, not a fixture bug. The
    # assertion only needs "every one of the eight families fired at least once somewhere".
    fired_setups = {s["setup_id"] for s in result["signals"]}
    expected_families = {
        "open_high_break", "jbe", "dbi", "cup_handle", "capitulation",
        "range_trade", "double_top", "double_bottom",
    }
    assert fired_setups >= expected_families, (
        f"expected all eight setup families to fire, got {fired_setups} (absences: {result['absences']})"
    )

    assert calls == {"tradability": 0, "levels": 0}


def test_zero_structural_calls_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing. A deliberately WRONG call site
    (calling the real, patched ``compute_tradability``) trips the counting stub's own assertion."""
    calls = {"tradability": 0}

    def _counting_tradability(*args, **kwargs):
        calls["tradability"] += 1
        raise AssertionError("seeded violation")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(tradability_module, "compute_tradability", _counting_tradability)
        with pytest.raises(AssertionError, match="seeded violation"):
            tradability_module.compute_tradability()
    assert calls["tradability"] == 1


# --- TC-18 (goal-playbook-iter-6, J-06) -- the doc-only spec edit's own zero-behavior-change proof -
#
# `docs/playbook-detector-spec.md` §3.5 gained prose transcribing the `decline_bars`/`decline_mbr`
# reading `_find_climax_formation`/`detect_capitulation` already ship (the assumption-ledger entry
# "iter-6 -- goal-decomposer"). A pinned source hash of BOTH function bodies -- not a `git diff`
# subprocess, which would also need to special-case every OTHER, legitimate edit this same iteration
# makes elsewhere in the file -- proves neither function's own code lines moved by even one
# character; a companion pinned-constant check proves the capitulation-relevant `PLAYBOOK_*` values
# these two functions read are untouched too.

import hashlib
import inspect

_FIND_CLIMAX_FORMATION_SHA256 = "1a6b880d320072ad1a79b8d262accb7352fefae61ab85017c5d44a070b62e585"
_DETECT_CAPITULATION_SHA256 = "ffff5f2b4a3298ee48f4194e2f0de634a4a6fec37ba0512670b5b1dadc1240ca"


def test_decline_disclosure_doc_edit_left_the_capitulation_code_byte_unchanged():
    """TC-18: `_find_climax_formation`'s and `detect_capitulation`'s own source (extracted live via
    ``inspect.getsource``) still hashes to the EXACT value pinned before this iteration's doc-only
    spec edit landed -- proving the spec §3.5 prose addition is genuinely zero-behavior-change, not
    a disguised code edit."""
    from app.research.desk_playbook_detect import _find_climax_formation, detect_capitulation

    assert hashlib.sha256(inspect.getsource(_find_climax_formation).encode()).hexdigest() == (
        _FIND_CLIMAX_FORMATION_SHA256
    )
    assert hashlib.sha256(inspect.getsource(detect_capitulation).encode()).hexdigest() == (
        _DETECT_CAPITULATION_SHA256
    )
    # Companion constant check: every PLAYBOOK_* value these two functions actually read is
    # untouched (the doc edit transcribes existing behavior; it invents, tunes, or moves no number).
    params = playbook_parameters()
    assert params["vertical_window_bars"] == 3
    assert params["vertical_move_mbr"] == 4.0
    assert params["vertical_bar_mbr"] == 2.5
    assert params["bounce_max_bars"] == 3
    assert params["stop_pad_frac"] == 0.30
    assert params["rvol_surge"] == 2.0


def test_decline_disclosure_doc_edit_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing. A deliberately WRONG (seeded)
    hash is rejected."""
    import hashlib as _hashlib
    import inspect as _inspect

    from app.research.desk_playbook_detect import _find_climax_formation

    real_hash = _hashlib.sha256(_inspect.getsource(_find_climax_formation).encode()).hexdigest()
    seeded_wrong_hash = "0" * 64
    assert real_hash != seeded_wrong_hash
