"""Observation Contract v1 -- Binding Execution Order step 6 (J-06; docs/goal.md).

The GUARD SUITE (Key Capability 8; Required Trap Coverage items 40-45) -- five structural
mechanisms, each proven non-vacuous by its own ``test_counterexample_*``. Item 2, the RECOMPUTE
guard, already lives in ``test_tape_observation_projection.py`` and is deliberately NOT
duplicated here (the iteration's own assumption log records this).

TAUTOLOGICAL-SUMMARY-TEST WARNING (this exact file is named by the iter-3 and iter-4 lessons as
the risk to watch for): every mechanism below scans REAL source, a REAL live-served artifact, or
the REAL ``app/`` tree through ONE scan function, and every ``test_counterexample_*`` calls that
SAME function against a perturbed copy of REAL content (a temp-file copy of real source with an
injected line, or a mutated copy of a real fetched artifact) -- never a second hand-written
literal compared only to itself.

The five mechanisms:

  1. Copy-discipline lint (``find_violations``, reused verbatim from ``test_copy_discipline.py``
     -- never reimplemented) PLUS a fixed compound-identifier ban, over (a)
     ``observation_contract.py``'s source, (b) the five EXISTING ``test_tape_observation_*.py``
     modules' source, and (c) one live-served ``/tape/{ticker}/observation`` artifact fetched
     from a REAL uvicorn subprocess (never ``TestClient``-only, per this iteration's plan).
  2. External-system reference guard: ``workstation`` / ``trendora`` / ``tensteps`` absent,
     case-insensitively, under ``apps/`` and in ``docs/observation-contract-spec.md``.
  3. English-only guard over the observation schema's keys, enum values and
     ``observation_contract.py``'s module identifiers (Constitution §8 explicitly excludes
     free-text labels such as the historical scenario string, which legitimately carries an en
     dash -- ``app/main.py``'s ``f"historical {ticker} {body.start}-{body.end}"`` -- so this
     guard never scans ``source.scenario`` or ``observations[]``).
  4. Real-provider isolation guard: no ``test_tape_observation_*`` module (all six, INCLUDING
     this one) reaches ``AlpacaAdapter`` outside an environment-gated smoke test.
  5. Mutator-call-site guard: every ``TapeEngine`` mutator call under ``app/`` lives inside a
     ``WatchManager`` method that RE-SETTLES the observation pair (``watch_manager.py``, i.e. the
     method's own body calls ``self._settle(...)``) or inside ``DatasetStore.replay``
     (``research/datasets.py``) -- goal.md J-06 step 3 / Required Trap Coverage item 44. Exactly
     one documented carve-out (``WatchManager.stop``, which deletes the engine in the same method,
     leaving nothing reachable to re-settle).

SELF exclusion: this module's own filename matches the ``test_tape_observation_*.py`` glob that
mechanisms 1 and 4 walk, and this docstring itself names every banned token as data (the same
``test_no_execution_path.py`` precedent: "this gate itself names every pattern as data"). Both
mechanisms exclude ``SELF`` explicitly (mechanism 1: the five-module glob excludes this file by
construction and is proven non-vacuous below; mechanism 4 deliberately INCLUDES this file in its
scanned set instead, since its own scan is AST-identifier-precise and this module never writes
``AlpacaAdapter`` as a bare name -- only as a quoted string -- so it needs no textual exclusion).

No test in this module contacts Alpaca, the network (beyond one loopback subprocess of THIS
app), or requires credentials or market hours -- Sim mode only.
"""

from __future__ import annotations

import ast
import copy
import io
import os
import re
import socket
import subprocess
import sys
import time
import tokenize
from pathlib import Path

import httpx
import pytest

from app import observation_contract
from app.config import CONFIG
from app.research.feed_basis import data_feed_for_scenario
from test_copy_discipline import _walk_strings, find_violations

BACKEND_DIR = Path(__file__).resolve().parents[1]
APPS_ROOT = BACKEND_DIR.parent
REPO_ROOT = APPS_ROOT.parent
TESTS_DIR = Path(__file__).resolve().parent
APP_ROOT = BACKEND_DIR / "app"
SPEC_PATH = REPO_ROOT / "docs" / "observation-contract-spec.md"
OBS_CONTRACT_PATH = Path(observation_contract.__file__)
SELF = Path(__file__).resolve()

TICKER = "SIM-BIDABS"
SCENARIO = "bid_absorption"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# --- shared: the five EXISTING test_tape_observation_*.py modules (SELF excluded) ---------------


def _existing_observation_test_modules() -> list[Path]:
    """The five modules named explicitly by this iteration's plan -- a glob would also match
    THIS file (SELF), so it is excluded by construction, never accidentally scanning itself."""
    return sorted(p for p in TESTS_DIR.glob("test_tape_observation_*.py") if p.resolve() != SELF)


def test_existing_observation_test_modules_glob_is_not_vacuous_and_excludes_self():
    names = {p.name for p in _existing_observation_test_modules()}
    assert names == {
        "test_tape_observation_lifecycle_feed.py",
        "test_tape_observation_path_equivalence.py",
        "test_tape_observation_projection.py",
        "test_tape_observation_route.py",
        "test_tape_observation_time.py",
    }
    assert SELF not in _existing_observation_test_modules()


# === Mechanism 1: copy-discipline lint + compound-identifier ban (TC-1, TC-2) ====================
#
# Reuses ``find_violations`` verbatim (never reimplemented). ``#`` comments, every docstring, and
# every ``test_counterexample_*`` function's full body are stripped from SOURCE texts before
# scanning -- resolving two concrete, verified false positives WITHOUT touching either frozen
# file: (a) ``test_tape_observation_route.py:174``'s comment "... guaranteed to observe ..." trips
# ``find_violations``' certainty-claim pattern; (b) ``test_tape_observation_lifecycle_feed.py``'s
# own ``test_counterexample_actionability_scan_catches_an_injected_token`` legitimately embeds
# ``trade_allowed`` as SEEDED FIXTURE DATA proving an EARLIER (iteration-3) guard's scanner can
# fail -- data about the anti-pattern, not the anti-pattern itself, exactly the
# ``test_no_execution_path.py`` SELF-exemption principle. Regular (non-docstring) string literals
# are otherwise left intact and fully scanned -- an accidentally-embedded served-copy literal
# would still be caught.

COMPOUND_IDENTIFIER_BAN: tuple[str, ...] = (
    "should_trade",
    "trade_signal",
    "entry_price",
    "stop_loss",
    "position_size",
    "trade_allowed",
    "READY",
    "NO_TRADE",
    "NO_VERDICT",
    "PENDING_CONDITION",
    "composite_policy",
)

# Pre-existing, legitimate exceptions: a file that ALREADY names one or more banned tokens as ITS
# OWN protective pattern-list DATA (an earlier guard's constant, not a violation). Scoped per file
# and per token -- injecting any OTHER token, or these same tokens into any OTHER file, still
# trips the ban. Mirrors ``test_no_execution_path.py``'s documented ``TIER2_ALLOWED`` precedent.
_KNOWN_PATTERN_LIST_EXCEPTIONS: dict[str, frozenset[str]] = {
    # ``ACTIONABILITY_TOKENS`` (iteration-3's own "no actionability token" guard constant,
    # Required Trap Coverage item 31 -- shared with, and pre-dating, this iteration's J-06).
    "test_tape_observation_lifecycle_feed.py": frozenset(
        {"trade_allowed", "READY", "NO_TRADE", "NO_VERDICT", "PENDING_CONDITION"}
    ),
}


def _docstring_nodes(tree: ast.Module) -> list[ast.AST]:
    """Every module/class/function docstring ``Expr`` statement in ``tree``."""
    nodes: list[ast.AST] = []
    scopes: list[ast.AST] = [tree] + [
        n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for scope in scopes:
        body = getattr(scope, "body", None)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            nodes.append(body[0])
    return nodes


def _counterexample_function_nodes(tree: ast.Module) -> list[ast.AST]:
    """Every ``test_counterexample_*`` function -- seeded-violation fixture bodies, not scanned."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_counterexample_")
    ]


def _blank_ast_node_lines(text: str, nodes: list[ast.AST]) -> str:
    """Replace every line spanned by each node in ``nodes`` with a blank line (line-count
    preserving, so this stays a pure text filter -- never re-parsed as Python afterward)."""
    lines = text.splitlines(keepends=True)
    for node in nodes:
        for i in range(node.lineno - 1, node.end_lineno):
            if i < len(lines):
                lines[i] = "\n"
    return "".join(lines)


def _stripped_python_source(path: Path) -> str:
    """The scan-ready text of a Python source file: ``#`` comments, every docstring, and every
    ``test_counterexample_*`` function body removed. Everything else -- including every OTHER
    string literal -- is left intact and fully scanned."""
    source = path.read_text()
    tree = ast.parse(source)
    blanked = _blank_ast_node_lines(source, _docstring_nodes(tree) + _counterexample_function_nodes(tree))
    out: list[str] = []
    for tok in tokenize.generate_tokens(io.StringIO(blanked).readline):
        if tok.type == tokenize.COMMENT:
            continue
        out.append(tok.string)
    return " ".join(out)


def _compound_identifier_violations(text: str, *, source_name: str = "") -> list[str]:
    exceptions = _KNOWN_PATTERN_LIST_EXCEPTIONS.get(source_name, frozenset())
    return [
        token
        for token in COMPOUND_IDENTIFIER_BAN
        if token not in exceptions and re.search(r"\b" + re.escape(token) + r"\b", text)
    ]


def _scanned_source_texts() -> list[tuple[str, str]]:
    """``[(name, stripped_text), ...]`` for ``observation_contract.py`` + the five existing
    test modules -- the ONE list both the copy-discipline and compound-identifier source scans
    (and their counter-tests) read."""
    texts = [(OBS_CONTRACT_PATH.name, _stripped_python_source(OBS_CONTRACT_PATH))]
    texts += [(p.name, _stripped_python_source(p)) for p in _existing_observation_test_modules()]
    return texts


def test_copy_discipline_lint_is_clean_over_module_and_test_sources():
    offenders = [
        f"{name}: {violations}"
        for name, text in _scanned_source_texts()
        if (violations := find_violations(text))
    ]
    assert offenders == [], offenders


def test_compound_identifier_ban_is_clean_over_module_and_test_sources():
    offenders = [
        f"{name}: {violations}"
        for name, text in _scanned_source_texts()
        if (violations := _compound_identifier_violations(text, source_name=name))
    ]
    assert offenders == [], offenders


def test_counterexample_copy_discipline_lint_detects_an_injected_phrase_in_source(tmp_path):
    poisoned = OBS_CONTRACT_PATH.read_text() + '\n\n_LEAKED_COPY = "You should sell now."\n'
    temp_file = tmp_path / "observation_contract.py"
    temp_file.write_text(poisoned)
    assert find_violations(_stripped_python_source(temp_file)) != []


def test_counterexample_compound_identifier_ban_detects_an_injected_identifier_in_source(tmp_path):
    poisoned = OBS_CONTRACT_PATH.read_text() + "\n\ncomposite_policy = None\n"
    temp_file = tmp_path / "observation_contract.py"
    temp_file.write_text(poisoned)
    assert _compound_identifier_violations(
        _stripped_python_source(temp_file), source_name=temp_file.name
    ) != []


# --- Mechanism 1, leg (c): one live-served artifact from a REAL uvicorn subprocess --------------


@pytest.fixture(scope="module")
def live_served_observation(tmp_path_factory):
    """One live-served ``/tape/{ticker}/observation`` artifact fetched over HTTP from a REAL
    uvicorn subprocess -- the plan explicitly forbids ``TestClient``-only for this leg. Follows
    ``test_tape_observation_route.py``'s own real-uvicorn-subprocess pattern, self-contained here
    per this repository's established per-module fixture convention (duplicated, not imported)."""
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["TAPEOLOGY_JOURNAL_DB"] = str(tmp_path_factory.mktemp("guards-journal") / "journal.db")
    log_path = tmp_path_factory.mktemp("guards-uvicorn") / "uvicorn.log"
    with open(log_path, "wb") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=BACKEND_DIR, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.time() + 20
            while True:
                try:
                    if httpx.get(f"{base}/health", timeout=1.0).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if proc.poll() is not None or time.time() > deadline:
                    raise AssertionError(f"test backend failed to start:\n{log_path.read_text()[-2000:]}")
                time.sleep(0.2)

            assert httpx.post(f"{base}/watch/{TICKER}", timeout=5.0).status_code == 200
            deadline = time.time() + 15
            while time.time() < deadline:
                state = httpx.get(f"{base}/tape/{TICKER}/state", timeout=5.0).json()
                if state.get("tape_state") == SCENARIO:
                    break
                time.sleep(0.2)
            else:
                raise AssertionError(f"{TICKER} did not settle on the test backend")
            assert httpx.post(f"{base}/watch/{TICKER}/pause", timeout=5.0).status_code == 200

            response = httpx.get(f"{base}/tape/{TICKER}/observation", timeout=5.0)
            assert response.status_code == 200
            yield response.json()
        finally:
            proc.terminate()
            proc.wait(timeout=10)


def test_copy_discipline_lint_is_clean_over_the_live_served_artifact(live_served_observation):
    offenders = [
        f"{json_path}: {violations} :: {value!r}"
        for json_path, value in _walk_strings(live_served_observation)
        if (violations := find_violations(value))
    ]
    assert offenders == [], offenders


def test_compound_identifier_ban_is_clean_over_the_live_served_artifact(live_served_observation):
    encoded = observation_contract.canonical_encode(live_served_observation).decode("utf-8")
    assert _compound_identifier_violations(encoded) == []


def test_counterexample_copy_discipline_lint_detects_an_injected_phrase_in_the_artifact(
    live_served_observation,
):
    mutated = copy.deepcopy(live_served_observation)
    mutated["observations"] = list(mutated["observations"]) + ["You should sell now."]
    offenders = [
        json_path for json_path, value in _walk_strings(mutated) if find_violations(value)
    ]
    assert offenders != []


def test_counterexample_compound_identifier_ban_detects_an_injected_token_in_the_artifact(
    live_served_observation,
):
    mutated = copy.deepcopy(live_served_observation)
    mutated["composite_policy"] = "irrelevant value"  # a banned token as a FIELD NAME
    encoded = observation_contract.canonical_encode(mutated).decode("utf-8")
    assert _compound_identifier_violations(encoded) != []


# === Mechanism 2: external-system reference guard (TC-3, TC-4) ==================================
#
# ``docs/goal.md``, ``docs/phases/``, ``docs/goal-archive/`` and ``project-extensions/host-guard/``
# need no explicit exclusion code: the two scan roots below (the ``apps/`` tree, and the ONE named
# spec file) never reach any of those paths in the first place -- host-guard.env legitimately
# names sibling host projects ("trendora", "tensteps") for shared resource budgeting, confirmed by
# direct inspection, which is exactly why goal.md excludes that path from ANY such scan.

EXTERNAL_SYSTEM_TOKENS: tuple[str, ...] = ("workstation", "trendora", "tensteps")

_APPS_SKIP_DIRS = {".venv", "node_modules", ".next", "__pycache__", ".data", ".pytest_cache", "fixtures"}
_APPS_SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js"}


def _apps_source_files() -> list[Path]:
    files = []
    for path in sorted(APPS_ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in _APPS_SOURCE_SUFFIXES:
            continue
        if any(part in _APPS_SKIP_DIRS for part in path.parts):
            continue
        if path.resolve() == SELF:  # this module names every token as data (SELF exclusion)
            continue
        files.append(path)
    return files


def _scan_files_for_tokens(files: list[Path], tokens: tuple[str, ...]) -> list[str]:
    low_tokens = tuple(t.lower() for t in tokens)
    offenders = []
    for path in files:
        text = path.read_text(errors="ignore").lower()
        for token in low_tokens:
            if token in text:
                offenders.append(f"{path}: {token!r}")
    return offenders


def _external_system_reference_violations(files: list[Path] | None = None) -> list[str]:
    if files is None:
        files = _apps_source_files() + [SPEC_PATH]
    return _scan_files_for_tokens(files, EXTERNAL_SYSTEM_TOKENS)


def test_external_system_reference_scan_is_not_vacuous():
    files = _apps_source_files()
    assert len(files) > 100
    rels = {p.relative_to(APPS_ROOT).as_posix() for p in files}
    assert "backend/app/main.py" in rels
    assert SPEC_PATH.exists()


def test_no_external_system_reference_under_apps_or_in_the_spec():
    assert _external_system_reference_violations() == []


def test_counterexample_external_system_reference_guard_detects_an_injected_token(tmp_path):
    poisoned = SPEC_PATH.read_text() + "\n\nSee trendora's own dashboard for context.\n"
    temp_file = tmp_path / "observation-contract-spec.md"
    temp_file.write_text(poisoned)
    assert _external_system_reference_violations(files=[temp_file]) != []


# === Mechanism 3: English-only guard (TC-5, TC-6) ================================================
#
# Scoped EXACTLY to schema keys, enum values and ``observation_contract.py``'s module identifiers
# (Constitution §8) -- deliberately NOT ``source.scenario`` or ``observations[]``, which are
# free-text labels; ``app/main.py``'s historical scenario string
# (``f"historical {ticker} {body.start}-{body.end}"``) legitimately carries an en dash and is
# explicitly exempted by goal.md itself.


def _is_ascii_english(value: str) -> bool:
    return value.isascii()


def _schema_key_segments() -> set[str]:
    segments: set[str] = set()
    for path in observation_contract.field_partition_map():
        segments.update(path.split("."))
    return segments


def _closed_enum_values() -> set[str]:
    values = set(observation_contract.TAPE_STATE_VOCABULARY)
    values.update(observation_contract._AVAILABILITY_BASIS_BY_SOURCE_MODE.keys())  # source_mode
    values.update(observation_contract._AVAILABILITY_BASIS_BY_SOURCE_MODE.values())  # availability_basis
    values.add(CONFIG.live_feed)  # data_feed closed set, config-owned (feed_basis.py)
    values.add(CONFIG.historical_feed)
    values.add(data_feed_for_scenario(SCENARIO, CONFIG))  # "sim"
    # lifecycle.stream_status (Constitution §4's frozen seven-status closed set).
    values.update({"connecting", "waiting", "live", "stale", "paused", "closed", "failed"})
    return values


def _module_identifiers() -> set[str]:
    tree = ast.parse(OBS_CONTRACT_PATH.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def _english_only_violations(values: set[str]) -> list[str]:
    return sorted(v for v in values if not _is_ascii_english(v))


def test_english_only_scan_targets_are_not_vacuous():
    assert len(_schema_key_segments()) > 10
    assert len(_closed_enum_values()) >= 15
    assert len(_module_identifiers()) > 20


def test_english_only_guard_over_schema_keys_enum_values_and_module_identifiers():
    violations = (
        _english_only_violations(_schema_key_segments())
        + _english_only_violations(_closed_enum_values())
        + _english_only_violations(_module_identifiers())
    )
    assert violations == []


def test_counterexample_english_only_guard_detects_a_non_ascii_value():
    mutated = set(_closed_enum_values())
    mutated.add("bid–absorption")  # an en dash injected into a copy of a real enum value
    assert _english_only_violations(mutated) != []


# === Mechanism 4: real-provider isolation guard (TC-7, TC-8) =====================================
#
# Scans all SIX ``test_tape_observation_*.py`` modules, INCLUDING this one: an AST-precise scan
# (real ``Name``/``Attribute``/import nodes, never a text substring) so this module's own prose
# discussing "AlpacaAdapter" as a quoted string never self-triggers -- no SELF exclusion needed.

_REAL_PROVIDER_SMOKE_ENV = "TAPEOLOGY_REAL_PROVIDER_SMOKE"


def _alpaca_references(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "AlpacaAdapter":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "AlpacaAdapter":
            return True
        if isinstance(node, ast.ImportFrom) and any(alias.name == "AlpacaAdapter" for alias in node.names):
            return True
    return False


def _is_gated_smoke_module(source: str) -> bool:
    """An allowed real-provider smoke test both names the gating env var AND is conditioned on it
    via ``pytest.mark.skipif`` -- so a module cannot merely mention the env var's name to smuggle
    an ungated ``AlpacaAdapter`` reference past this guard. No such module exists yet this era
    (``TAPEOLOGY_REAL_PROVIDER_SMOKE`` is unused today, confirmed by direct inspection); this
    keeps the carve-out real for when one is added."""
    return _REAL_PROVIDER_SMOKE_ENV in source and "skipif" in source


def _real_provider_isolation_violations(modules: list[Path]) -> list[str]:
    offenders = []
    for path in modules:
        source = path.read_text()
        if _alpaca_references(source) and not _is_gated_smoke_module(source):
            offenders.append(path.name)
    return offenders


def test_no_test_tape_observation_module_reaches_alpaca_adapter_outside_the_gated_smoke_test():
    modules = _existing_observation_test_modules() + [SELF]
    assert len(modules) == 6
    assert _real_provider_isolation_violations(modules) == []


def test_counterexample_real_provider_isolation_guard_detects_an_ungated_reference(tmp_path):
    real_text = (TESTS_DIR / "test_tape_observation_time.py").read_text()
    poisoned = real_text + "\n\nfrom app.providers.adapters.alpaca import AlpacaAdapter\n"
    temp_file = tmp_path / "test_tape_observation_time.py"
    temp_file.write_text(poisoned)
    assert _real_provider_isolation_violations([temp_file]) != []


def test_gated_smoke_module_pattern_is_recognized_as_exempt(tmp_path):
    fixture_source = (
        "import os\nimport pytest\n"
        "from app.providers.adapters.alpaca import AlpacaAdapter\n\n"
        "@pytest.mark.skipif(not os.environ.get('TAPEOLOGY_REAL_PROVIDER_SMOKE'), reason='gated')\n"
        "def test_real_provider_smoke():\n    AlpacaAdapter()\n"
    )
    temp_file = tmp_path / "test_tape_observation_smoke.py"
    temp_file.write_text(fixture_source)
    assert _alpaca_references(fixture_source) is True
    assert _real_provider_isolation_violations([temp_file]) == []


# === Mechanism 5: mutator-call-site guard (TC-9, TC-10) ==========================================
#
# Every real ``TapeEngine`` instance under ``app/`` is bound to a variable/parameter named
# EXACTLY ``engine`` at every construction and call site (verified by direct inspection: five
# ``TapeEngine(...)`` constructions, ~30 call sites, all named ``engine``) -- distinct from
# ``WatchManager.pause``/``resume`` (bound to ``manager`` in ``app/main.py``, a same-named but
# DIFFERENT class) and ``HistoryBuffer.set_epoch_anchor`` (called as ``self._history.
# set_epoch_anchor(...)`` inside ``TapeEngine`` itself, a different receiver). The scan below
# restricts to a bare ``Name(id="engine")`` receiver specifically to avoid those two same-name
# collisions -- both confirmed absent from the results by the non-vacuous check below.

_MUTATOR_METHOD_NAMES = frozenset(
    {"process_event", "set_stream_status", "set_delivery_lag", "set_epoch_anchor", "pause", "resume"}
)


class _MutatorCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.class_stack: list[str] = []
        self.function_stack: list[str] = []
        self.call_sites: list[tuple[str | None, str, int]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def _visit_function(self, node: "ast.FunctionDef | ast.AsyncFunctionDef") -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr in _MUTATOR_METHOD_NAMES
            and isinstance(func.value, ast.Name)
            and func.value.id == "engine"
        ):
            class_name = self.class_stack[-1] if self.class_stack else None
            function_name = self.function_stack[-1] if self.function_stack else "<module>"
            self.call_sites.append((class_name, function_name, node.lineno))
        self.generic_visit(node)


def _mutator_call_sites(source: str) -> list[tuple[str | None, str, int]]:
    visitor = _MutatorCallVisitor()
    visitor.visit(ast.parse(source))
    return visitor.call_sites


# ``docs/goal.md``'s own wording for this mechanism (J-06 step 3; Required Trap Coverage item 44)
# is "watch_manager.py methods THAT RE-SETTLE, or DatasetStore.replay" -- a LOCATION-only check
# would pass a ``WatchManager`` method that mutates the engine and never re-settles the pair, which
# is exactly the Constitution §2 breakage this guard exists to prevent. The allowed set is therefore
# computed from the scanned file's OWN source: a method qualifies only when its body calls
# ``self._settle(...)``.
#
# ONE documented carve-out, scoped to a single (file, class, method) triple:
_NON_SETTLING_CARVE_OUTS: frozenset[tuple[str, str, str]] = frozenset(
    {
        # ``WatchManager.stop`` flips the engine to ``closed`` and then DELETES it from
        # ``self._engines`` in the SAME method, so no settled pair for that ticker stays reachable:
        # ``get_observation_source`` looks the engine up first and returns ``None``, and the route
        # 404s (verified by direct inspection of ``stop`` / ``get_observation_source`` and by the
        # post-stop 404 coverage in ``test_tape_observation_lifecycle_feed.py``). There is nothing
        # left to re-settle -- the only mutator call site under ``app/`` for which that is true.
        ("watch_manager.py", "WatchManager", "stop"),
    }
)


def _settling_method_names(source: str) -> set[str]:
    """Every function in ``source`` whose body calls ``self._settle(...)`` (AST, never a text
    match) -- the manager's ONE re-settling helper (``watch_manager.py``'s ``_settle``)."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and inner.func.attr == "_settle"
                and isinstance(inner.func.value, ast.Name)
                and inner.func.value.id == "self"
            ):
                names.add(node.name)
                break
    return names


def _is_allowed_mutator_call_site(
    path_name: str,
    class_name: str | None,
    function_name: str,
    *,
    settling_methods: set[str],
) -> bool:
    if path_name == "watch_manager.py" and class_name == "WatchManager":
        if function_name in settling_methods:
            return True
        return (path_name, class_name, function_name) in _NON_SETTLING_CARVE_OUTS
    if path_name == "datasets.py" and class_name == "DatasetStore" and function_name == "replay":
        return True
    return False


def _mutator_call_site_violations_in_file(path: Path, source: str | None = None) -> list[str]:
    source = path.read_text() if source is None else source
    settling_methods = _settling_method_names(source)
    violations = []
    for class_name, function_name, lineno in _mutator_call_sites(source):
        if not _is_allowed_mutator_call_site(
            path.name, class_name, function_name, settling_methods=settling_methods
        ):
            violations.append(
                f"{path.name}:{lineno} {class_name}.{function_name} calls engine.<mutator> "
                "outside a re-settling WatchManager method / DatasetStore.replay"
            )
    return violations


def _all_app_python_files() -> list[Path]:
    return sorted(p for p in APP_ROOT.rglob("*.py") if "__pycache__" not in p.parts)


def _mutator_call_site_violations() -> list[str]:
    violations = []
    for path in _all_app_python_files():
        violations += _mutator_call_site_violations_in_file(path)
    return violations


def test_mutator_call_site_scan_is_not_vacuous():
    watch_manager_sites = _mutator_call_sites((APP_ROOT / "watch_manager.py").read_text())
    assert len(watch_manager_sites) > 10
    assert all(class_name == "WatchManager" for class_name, _fn, _ln in watch_manager_sites)

    dataset_sites = _mutator_call_sites((APP_ROOT / "research" / "datasets.py").read_text())
    assert any(
        class_name == "DatasetStore" and function_name == "replay"
        for class_name, function_name, _ln in dataset_sites
    )


def test_settling_method_detection_is_not_vacuous_and_names_one_documented_carve_out():
    """The re-settling half of the guard must be REAL: the manager's feeders/pause/resume are
    detected as re-settling, and ``stop`` -- the one mutator-calling method that does not settle
    (it deletes the engine instead) -- is the ONLY carve-out. An accidental widening of either set
    fails here rather than silently widening what the guard accepts."""
    source = (APP_ROOT / "watch_manager.py").read_text()
    settling = _settling_method_names(source)
    assert {"pause", "resume", "_feed", "_feed_paced", "_feed_progressive", "_feed_live",
            "_replay_events"} <= settling
    mutator_methods = {function_name for _cls, function_name, _ln in _mutator_call_sites(source)}
    assert sorted(m for m in mutator_methods if m not in settling) == ["stop"]
    assert _NON_SETTLING_CARVE_OUTS == frozenset({("watch_manager.py", "WatchManager", "stop")})


def test_every_tape_engine_mutator_call_lives_in_watch_manager_or_dataset_store_replay():
    assert _mutator_call_site_violations() == []


def test_counterexample_mutator_call_site_guard_detects_a_non_settling_watch_manager_method(
    tmp_path,
):
    """The location-only version of this guard passed a ``WatchManager`` method that mutates the
    engine and never re-settles the pair. Inject exactly that into a copy of the REAL
    ``watch_manager.py`` (spliced inside the real class body, not a hand-written stand-in) and the
    guard must report it."""
    real_text = (APP_ROOT / "watch_manager.py").read_text()
    lines = real_text.splitlines(keepends=True)
    class_end = max(
        node.end_lineno
        for node in ast.walk(ast.parse(real_text))
        if isinstance(node, ast.ClassDef) and node.name == "WatchManager"
    )
    poisoned = (
        "".join(lines[:class_end])
        + "\n    def _mutates_without_re_settling(self, ticker):\n"
          "        engine = self._engines[ticker]\n"
          "        engine.set_stream_status('failed')\n"
          "        return True\n"
        + "".join(lines[class_end:])
    )
    temp_file = tmp_path / "watch_manager.py"
    temp_file.write_text(poisoned)
    violations = _mutator_call_site_violations_in_file(temp_file)
    assert violations != []
    assert any("_mutates_without_re_settling" in v for v in violations), violations


def test_counterexample_mutator_call_site_guard_detects_a_call_outside_the_allowed_locations(tmp_path):
    real_text = (APP_ROOT / "research" / "datasets.py").read_text()
    poisoned = real_text + (
        "\n\ndef _leaked_mutator_call_for_test(engine, event):\n"
        "    engine.process_event(event)\n"
    )
    temp_file = tmp_path / "datasets.py"
    temp_file.write_text(poisoned)
    assert _mutator_call_site_violations_in_file(temp_file) != []
