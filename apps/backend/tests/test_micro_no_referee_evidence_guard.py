"""Guard/source-scan test (Era "The Rapid Microscope" J-09, goal.md IN SCOPE, TC-10): no
``micro_*.py``/``scout*.py``/``walkforward*.py``/``vault.py`` module in ``app/research/`` imports
or calls ``referee_evidence.strategy_trade_readiness`` or ``referee_evidence.referee_evidence``
(both defined in ``referee_evidence.py`` -- ``strategy_trade_readiness`` at line 328,
``referee_evidence`` at line 358).

**Why this guard exists (spec section 10.7, r5).** ``strategy_trade_readiness``'s served metric is
SEAL-UNAWARE -- it counts every registered dataset regardless of vault lifecycle state, a
correctness gap the spec names explicitly. The era's own ``referee_*`` modules are byte-frozen
this whole era (goal.md's own Foundation invariants), so this gap is tolerated there for now; a
Rapid-Microscope module reading it would import a seal-unaware count into code whose WHOLE job is
seal-awareness (the "no exploratory read of a sealed shard" anti-goal) -- a genuine, structural
regression risk this guard exists to catch BEFORE it ever ships (T-1's own "the guard is exactly
what would catch a future regression into that state", goal.md NOTES).

**Two distinct reference shapes, both banned (the ``test_micro_accessor.py`` TC-3 precedent,
mirrored -- module docstring there: "the bypass a pure import-scan misses").**

1. A direct name import of either function: ``from .referee_evidence import
   strategy_trade_readiness`` or ``from .referee_evidence import referee_evidence`` (this second
   form is the FUNCTION, name-collided with its own defining module -- distinguished structurally
   from (2) below by requiring ``node.module`` to actually name ``referee_evidence``, never a bare
   ``from . import referee_evidence``).
2. A module-qualified attribute reference on a name bound to the ``referee_evidence`` module
   (``from . import referee_evidence`` then ``referee_evidence.strategy_trade_readiness(...)``, or
   any aliased/absolute equivalent) -- the bypass a pure import-name scan cannot see.

**Deliberately NOT banned: importing the ``referee_evidence`` MODULE itself, or any OTHER symbol
from it.** ``micro_readiness.py`` already legitimately does ``from .referee_evidence import
REFEREE_TICK_GATE_SYMBOL_DAYS`` (a single-source-of-truth reuse of the tick-gate constant, not the
seal-unaware readiness function) -- a guard that flagged the bare module name would false-positive
on that existing, correct import. This guard's own counter-test proves both directions: the banned
shapes ARE caught, and this exact existing import is NOT."""

from __future__ import annotations

import ast
import pathlib

_APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"
_RESEARCH_DIR = _APP_DIR / "research"

_BANNED_NAMES = ("strategy_trade_readiness", "referee_evidence")
_DEFINING_MODULE = "referee_evidence"

# The scope this iteration's own DoD names verbatim: micro_*.py / scout*.py / walkforward*.py /
# vault.py -- never the whole app tree (referee_evidence.py's OWN module, and referee_routes.py,
# legitimately reference these functions -- that is their job, not a violation).
_SCOPED_GLOBS = ("micro_*.py", "scout*.py", "walkforward*.py", "vault.py")


def _scoped_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for pattern in _SCOPED_GLOBS:
        files.extend(sorted(_RESEARCH_DIR.glob(pattern)))
    return files


def _direct_name_import_violations(tree: ast.AST) -> set[str]:
    """``from .referee_evidence import strategy_trade_readiness`` / ``from .referee_evidence
    import referee_evidence`` -- a name-targeted import FROM the defining module specifically
    (``node.module`` must actually name it), never a bare ``from . import referee_evidence``
    (module docstring's own "deliberately NOT banned" clause)."""
    violations: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module is None or node.module.split(".")[-1] != _DEFINING_MODULE:
            continue
        for alias in node.names:
            if alias.name in _BANNED_NAMES:
                violations.add(f"from ...{_DEFINING_MODULE} import {alias.name}")
    return violations


def _module_bound_names(tree: ast.AST) -> set[str]:
    """Every LOCAL name this file binds to the ``referee_evidence`` MODULE itself -- ``from . import
    referee_evidence`` (binds ``referee_evidence``), ``from . import referee_evidence as re_mod``
    (binds ``re_mod``), ``import app.research.referee_evidence as re_mod`` (binds ``re_mod``)."""
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module is not None and node.module.split(".")[-1] != _DEFINING_MODULE:
                continue
            for alias in node.names:
                if alias.name == _DEFINING_MODULE:
                    bound.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[-1] == _DEFINING_MODULE:
                    bound.add(alias.asname or alias.name.split(".")[0])
    return bound


def _dotted_source(node: ast.AST) -> str | None:
    """``referee_evidence.strategy_trade_readiness`` -> ``"referee_evidence"`` for the attribute's
    OWN qualifying value; ``None`` when it is not a plain dotted name (the
    ``test_micro_accessor.py`` ``_dotted_source`` precedent, mirrored)."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _module_qualified_violations(tree: ast.AST) -> set[str]:
    """``referee_evidence.strategy_trade_readiness(...)`` / ``re_mod.referee_evidence(...)`` -- an
    attribute reference whose OWN name is banned, qualified on a name this file bound to the
    ``referee_evidence`` module (the bypass a pure import-name scan cannot see)."""
    bound = _module_bound_names(tree)
    if not bound:
        return set()
    violations: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _BANNED_NAMES:
            source = _dotted_source(node.value)
            if source is not None and source in bound:
                violations.add(f"{source}.{node.attr}")
    return violations


def _violations(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text())
    return _direct_name_import_violations(tree) | _module_qualified_violations(tree)


def test_tc10_no_scoped_module_imports_or_calls_the_seal_unaware_readiness_functions():
    """TC-10, verbatim: a source scan of every ``micro_*.py``/``scout*.py``/``walkforward*.py``/
    ``vault.py`` file asserts zero occurrences of ``strategy_trade_readiness`` or
    ``referee_evidence`` as an import or call target."""
    files = _scoped_files()
    assert len(files) >= 8, f"only {len(files)} scoped files found -- has the module set moved?"
    names = {p.name for p in files}
    for expected in ("micro_join.py", "micro_readiness.py", "scout.py", "walkforward.py", "vault.py"):
        assert expected in names, f"{expected} not found in the scoped scan -- has it moved/renamed?"

    violations: dict[str, set[str]] = {}
    for path in files:
        found = _violations(path)
        if found:
            violations[path.name] = found
    assert not violations, (
        f"seal-unaware referee_evidence.{_BANNED_NAMES} referenced in scoped modules: {violations}"
    )


def test_tc10_the_scan_is_non_vacuous_it_catches_both_banned_shapes(tmp_path):
    """The counter-test (iter-15's own lesson: a new trap-adjacent assertion needs a non-vacuity
    proof that the state it sweeps is genuinely reachable) -- both banned reference shapes ARE
    caught by a planted violation."""
    direct_import = tmp_path / "direct_import.py"
    direct_import.write_text(
        "from .referee_evidence import strategy_trade_readiness\n"
        "def use():\n"
        "    return strategy_trade_readiness\n"
    )
    assert _violations(direct_import) == {
        f"from ...{_DEFINING_MODULE} import strategy_trade_readiness"
    }

    direct_import_fn = tmp_path / "direct_import_fn.py"
    direct_import_fn.write_text("from .referee_evidence import referee_evidence\n")
    assert _violations(direct_import_fn) == {f"from ...{_DEFINING_MODULE} import referee_evidence"}

    qualified_call = tmp_path / "qualified_call.py"
    qualified_call.write_text(
        "from . import referee_evidence\n"
        "def use(playbook_store, dataset_store, journal_store, fp):\n"
        "    return referee_evidence.referee_evidence(\n"
        "        playbook_store=playbook_store, dataset_store=dataset_store,\n"
        "        journal_store=journal_store, config_fingerprint=fp,\n"
        "    )\n"
    )
    assert _violations(qualified_call) == {"referee_evidence.referee_evidence"}


def test_tc10_the_scan_never_flags_the_existing_legitimate_constant_import(tmp_path):
    """``micro_readiness.py`` already legitimately imports ``REFEREE_TICK_GATE_SYMBOL_DAYS`` from
    ``referee_evidence.py`` (single-source-of-truth reuse of the tick-gate constant, module
    docstring) -- a bare module import, or an import/use of any OTHER symbol, is never a
    violation."""
    legitimate = tmp_path / "legitimate.py"
    legitimate.write_text(
        "from .referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS\n"
        "def gate():\n"
        "    return REFEREE_TICK_GATE_SYMBOL_DAYS\n"
    )
    assert _violations(legitimate) == set()

    bare_module_import = tmp_path / "bare_module_import.py"
    bare_module_import.write_text(
        "from . import referee_evidence\n"
        "def gate():\n"
        "    return referee_evidence.REFEREE_TICK_GATE_SYMBOL_DAYS\n"
    )
    assert _violations(bare_module_import) == set()


def test_tc10_micro_readiness_py_still_carries_its_legitimate_constant_import():
    """A live check on the real file (never only the synthetic counter-tests above): confirms the
    scan actually ran over content carrying a real ``from .referee_evidence import ...`` line, and
    still cleared it -- a scan that silently skipped this file would prove nothing."""
    path = _RESEARCH_DIR / "micro_readiness.py"
    assert "from .referee_evidence import" in path.read_text()
    assert _violations(path) == set()
