# Iteration diff (bounded)

Files changed: 1. Shown in full: 0.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_tape_observation_guards.py` (356 lines not shown)

```diff
diff --git a/apps/backend/tests/test_tape_observation_guards.py b/apps/backend/tests/test_tape_observation_guards.py
new file mode 100644
index 00000000..1033f4db
--- /dev/null
+++ b/apps/backend/tests/test_tape_observation_guards.py
@@ -0,0 +1,750 @@
+"""Observation Contract v1 -- Binding Execution Order step 6 (J-06; docs/goal.md).
+
+The GUARD SUITE (Key Capability 8; Required Trap Coverage items 40-45) -- five structural
+mechanisms, each proven non-vacuous by its own ``test_counterexample_*``. Item 2, the RECOMPUTE
+guard, already lives in ``test_tape_observation_projection.py`` and is deliberately NOT
+duplicated here (the iteration's own assumption log records this).
+
+TAUTOLOGICAL-SUMMARY-TEST WARNING (this exact file is named by the iter-3 and iter-4 lessons as
+the risk to watch for): every mechanism below scans REAL source, a REAL live-served artifact, or
+the REAL ``app/`` tree through ONE scan function, and every ``test_counterexample_*`` calls that
+SAME function against a perturbed copy of REAL content (a temp-file copy of real source with an
+injected line, or a mutated copy of a real fetched artifact) -- never a second hand-written
+literal compared only to itself.
+
+The five mechanisms:
+
+  1. Copy-discipline lint (``find_violations``, reused verbatim from ``test_copy_discipline.py``
+     -- never reimplemented) PLUS a fixed compound-identifier ban, over (a)
+     ``observation_contract.py``'s source, (b) the five EXISTING ``test_tape_observation_*.py``
+     modules' source, and (c) one live-served ``/tape/{ticker}/observation`` artifact fetched
+     from a REAL uvicorn subprocess (never ``TestClient``-only, per this iteration's plan).
+  2. External-system reference guard: ``workstation`` / ``trendora`` / ``tensteps`` absent,
+     case-insensitively, under ``apps/`` and in ``docs/observation-contract-spec.md``.
+  3. English-only guard over the observation schema's keys, enum values and
+     ``observation_contract.py``'s module identifiers (Constitution §8 explicitly excludes
+     free-text labels such as the historical scenario string, which legitimately carries an en
+     dash -- ``app/main.py``'s ``f"historical {ticker} {body.start}-{body.end}"`` -- so this
+     guard never scans ``source.scenario`` or ``observations[]``).
+  4. Real-provider isolation guard: no ``test_tape_observation_*`` module (all six, INCLUDING
+     this one) reaches ``AlpacaAdapter`` outside an environment-gated smoke test.
+  5. Mutator-call-site guard: every ``TapeEngine`` mutator call under ``app/`` lives inside a
+     ``WatchManager`` method that RE-SETTLES the observation pair (``watch_manager.py``, i.e. the
+     method's own body calls ``self._settle(...)``) or inside ``DatasetStore.replay``
+     (``research/datasets.py``) -- goal.md J-06 step 3 / Required Trap Coverage item 44. Exactly
+     one documented carve-out (``WatchManager.stop``, which deletes the engine in the same method,
+     leaving nothing reachable to re-settle).
+
+SELF exclusion: this module's own filename matches the ``test_tape_observation_*.py`` glob that
+mechanisms 1 and 4 walk, and this docstring itself names every banned token as data (the same
+``test_no_execution_path.py`` precedent: "this gate itself names every pattern as data"). Both
+mechanisms exclude ``SELF`` explicitly (mechanism 1: the five-module glob excludes this file by
+construction and is proven non-vacuous below; mechanism 4 deliberately INCLUDES this file in its
+scanned set instead, since its own scan is AST-identifier-precise and this module never writes
+``AlpacaAdapter`` as a bare name -- only as a quoted string -- so it needs no textual exclusion).
+
+No test in this module contacts Alpaca, the network (beyond one loopback subprocess of THIS
+app), or requires credentials or market hours -- Sim mode only.
+"""
+
+from __future__ import annotations
+
+import ast
+import copy
+import io
+import os
+import re
+import socket
+import subprocess
+import sys
+import time
+import tokenize
+from pathlib import Path
+
+import httpx
+import pytest
+
+from app import observation_contract
+from app.config import CONFIG
+from app.research.feed_basis import data_feed_for_scenario
+from test_copy_discipline import _walk_strings, find_violations
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+APPS_ROOT = BACKEND_DIR.parent
+REPO_ROOT = APPS_ROOT.parent
+TESTS_DIR = Path(__file__).resolve().parent
+APP_ROOT = BACKEND_DIR / "app"
+SPEC_PATH = REPO_ROOT / "docs" / "observation-contract-spec.md"
+OBS_CONTRACT_PATH = Path(observation_contract.__file__)
+SELF = Path(__file__).resolve()
+
+TICKER = "SIM-BIDABS"
+SCENARIO = "bid_absorption"
+
+
+def _free_port() -> int:
+    with socket.socket() as sock:
+        sock.bind(("127.0.0.1", 0))
+        return sock.getsockname()[1]
+
+
+# --- shared: the five EXISTING test_tape_observation_*.py modules (SELF excluded) ---------------
+
+
+def _existing_observation_test_modules() -> list[Path]:
+    """The five modules named explicitly by this iteration's plan -- a glob would also match
+    THIS file (SELF), so it is excluded by construction, never accidentally scanning itself."""
+    return sorted(p for p in TESTS_DIR.glob("test_tape_observation_*.py") if p.resolve() != SELF)
+
+
+def test_existing_observation_test_modules_glob_is_not_vacuous_and_excludes_self():
+    names = {p.name for p in _existing_observation_test_modules()}
+    assert names == {
+        "test_tape_observation_lifecycle_feed.py",
+        "test_tape_observation_path_equivalence.py",
+        "test_tape_observation_projection.py",
+        "test_tape_observation_route.py",
+        "test_tape_observation_time.py",
+    }
+    assert SELF not in _existing_observation_test_modules()
+
+
+# === Mechanism 1: copy-discipline lint + compound-identifier ban (TC-1, TC-2) ====================
+#
+# Reuses ``find_violations`` verbatim (never reimplemented). ``#`` comments, every docstring, and
+# every ``test_counterexample_*`` function's full body are stripped from SOURCE texts before
+# scanning -- resolving two concrete, verified false positives WITHOUT touching either frozen
+# file: (a) ``test_tape_observation_route.py:174``'s comment "... guaranteed to observe ..." trips
+# ``find_violations``' certainty-claim pattern; (b) ``test_tape_observation_lifecycle_feed.py``'s
+# own ``test_counterexample_actionability_scan_catches_an_injected_token`` legitimately embeds
+# ``trade_allowed`` as SEEDED FIXTURE DATA proving an EARLIER (iteration-3) guard's scanner can
+# fail -- data about the anti-pattern, not the anti-pattern itself, exactly the
+# ``test_no_execution_path.py`` SELF-exemption principle. Regular (non-docstring) string literals
+# are otherwise left intact and fully scanned -- an accidentally-embedded served-copy literal
+# would still be caught.
+
+COMPOUND_IDENTIFIER_BAN: tuple[str, ...] = (
+    "should_trade",
+    "trade_signal",
+    "entry_price",
+    "stop_loss",
+    "position_size",
+    "trade_allowed",
+    "READY",
+    "NO_TRADE",
+    "NO_VERDICT",
+    "PENDING_CONDITION",
+    "composite_policy",
+)
+
+# Pre-existing, legitimate exceptions: a file that ALREADY names one or more banned tokens as ITS
+# OWN protective pattern-list DATA (an earlier guard's constant, not a violation). Scoped per file
+# and per token -- injecting any OTHER token, or these same tokens into any OTHER file, still
+# trips the ban. Mirrors ``test_no_execution_path.py``'s documented ``TIER2_ALLOWED`` precedent.
+_KNOWN_PATTERN_LIST_EXCEPTIONS: dict[str, frozenset[str]] = {
+    # ``ACTIONABILITY_TOKENS`` (iteration-3's own "no actionability token" guard constant,
+    # Required Trap Coverage item 31 -- shared with, and pre-dating, this iteration's J-06).
+    "test_tape_observation_lifecycle_feed.py": frozenset(
+        {"trade_allowed", "READY", "NO_TRADE", "NO_VERDICT", "PENDING_CONDITION"}
+    ),
+}
+
+
+def _docstring_nodes(tree: ast.Module) -> list[ast.AST]:
+    """Every module/class/function docstring ``Expr`` statement in ``tree``."""
+    nodes: list[ast.AST] = []
+    scopes: list[ast.AST] = [tree] + [
+        n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
+    ]
+    for scope in scopes:
+        body = getattr(scope, "body", None)
+        if (
+            body
+            and isinstance(body[0], ast.Expr)
+            and isinstance(body[0].value, ast.Constant)
+            and isinstance(body[0].value.value, str)
+        ):
+            nodes.append(body[0])
+    return nodes
+
+
+def _counterexample_function_nodes(tree: ast.Module) -> list[ast.AST]:
+    """Every ``test_counterexample_*`` function -- seeded-violation fixture bodies, not scanned."""
+    return [
+        node
+        for node in ast.walk(tree)
+        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
+        and node.name.startswith("test_counterexample_")
+    ]
+
+
+def _blank_ast_node_lines(text: str, nodes: list[ast.AST]) -> str:
+    """Replace every line spanned by each node in ``nodes`` with a blank line (line-count
+    preserving, so this stays a pure text filter -- never re-parsed as Python afterward)."""
+    lines = text.splitlines(keepends=True)
+    for node in nodes:
+        for i in range(node.lineno - 1, node.end_lineno):
+            if i < len(lines):
+                lines[i] = "\n"
+    return "".join(lines)
+
+
+def _stripped_python_source(path: Path) -> str:
+    """The scan-ready text of a Python source file: ``#`` comments, every docstring, and every
+    ``test_counterexample_*`` function body removed. Everything else -- including every OTHER
+    string literal -- is left intact and fully scanned."""
+    source = path.read_text()
+    tree = ast.parse(source)
+    blanked = _blank_ast_node_lines(source, _docstring_nodes(tree) + _counterexample_function_nodes(tree))
+    out: list[str] = []
+    for tok in tokenize.generate_tokens(io.StringIO(blanked).readline):
+        if tok.type == tokenize.COMMENT:
+            continue
+        out.append(tok.string)
+    return " ".join(out)
+
+
+def _compound_identifier_violations(text: str, *, source_name: str = "") -> list[str]:
+    exceptions = _KNOWN_PATTERN_LIST_EXCEPTIONS.get(source_name, frozenset())
+    return [
+        token
+        for token in COMPOUND_IDENTIFIER_BAN
+        if token not in exceptions and re.search(r"\b" + re.escape(token) + r"\b", text)
+    ]
+
+
+def _scanned_source_texts() -> list[tuple[str, str]]:
+    """``[(name, stripped_text), ...]`` for ``observation_contract.py`` + the five existing
+    test modules -- the ONE list both the copy-discipline and compound-identifier source scans
+    (and their counter-tests) read."""
+    texts = [(OBS_CONTRACT_PATH.name, _stripped_python_source(OBS_CONTRACT_PATH))]
+    texts += [(p.name, _stripped_python_source(p)) for p in _existing_observation_test_modules()]
+    return texts
+
+
+def test_copy_discipline_lint_is_clean_over_module_and_test_sources():
+    offenders = [
+        f"{name}: {violations}"
+        for name, text in _scanned_source_texts()
+        if (violations := find_violations(text))
+    ]
+    assert offenders == [], offenders
+
+
+def test_compound_identifier_ban_is_clean_over_module_and_test_sources():
+    offenders = [
+        f"{name}: {violations}"
+        for name, text in _scanned_source_texts()
+        if (violations := _compound_identifier_violations(text, source_name=name))
+    ]
+    assert offenders == [], offenders
+
+
+def test_counterexample_copy_discipline_lint_detects_an_injected_phrase_in_source(tmp_path):
+    poisoned = OBS_CONTRACT_PATH.read_text() + '\n\n_LEAKED_COPY = "You should sell now."\n'
+    temp_file = tmp_path / "observation_contract.py"
+    temp_file.write_text(poisoned)
+    assert find_violations(_stripped_python_source(temp_file)) != []
+
+
+def test_counterexample_compound_identifier_ban_detects_an_injected_identifier_in_source(tmp_path):
+    poisoned = OBS_CONTRACT_PATH.read_text() + "\n\ncomposite_policy = None\n"
+    temp_file = tmp_path / "observation_contract.py"
+    temp_file.write_text(poisoned)
+    assert _compound_identifier_violations(
+        _stripped_python_source(temp_file), source_name=temp_file.name
+    ) != []
+
+
+# --- Mechanism 1, leg (c): one live-served artifact from a REAL uvicorn subprocess --------------
+
+
+@pytest.fixture(scope="module")
+def live_served_observation(tmp_path_factory):
+    """One live-served ``/tape/{ticker}/observation`` artifact fetched over HTTP from a REAL
+    uvicorn subprocess -- the plan explicitly forbids ``TestClient``-only for this leg. Follows
+    ``test_tape_observation_route.py``'s own real-uvicorn-subprocess pattern, self-contained here
+    per this repository's established per-module fixture convention (duplicated, not imported)."""
+    port = _free_port()
+    base = f"http://127.0.0.1:{port}"
+    env = os.environ.copy()
+    env["TAPEOLOGY_JOURNAL_DB"] = str(tmp_path_factory.mktemp("guards-journal") / "journal.db")
+    log_path = tmp_path_factory.mktemp("guards-uvicorn") / "uvicorn.log"
+    with open(log_path, "wb") as log:
+        proc = subprocess.Popen(
+            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
+            cwd=BACKEND_DIR, env=env, stdout=log, stderr=subprocess.STDOUT,
+        )
+        try:
+            deadline = time.time() + 20
+            while True:
+                try:
+                    if httpx.get(f"{base}/health", timeout=1.0).status_code == 200:
+                        break
+                except httpx.HTTPError:
+                    pass
+                if proc.poll() is not None or time.time() > deadline:
+                    raise AssertionError(f"test backend failed to start:\n{log_path.read_text()[-2000:]}")
+                time.sleep(0.2)
+
+            assert httpx.post(f"{base}/watch/{TICKER}", timeout=5.0).status_code == 200
+            deadline = time.time() + 15
+            while time.time() < deadline:
+                state = httpx.get(f"{base}/tape/{TICKER}/state", timeout=5.0).json()
+                if state.get("tape_state") == SCENARIO:
+                    break
+                time.sleep(0.2)
+            else:
+                raise AssertionError(f"{TICKER} did not settle on the test backend")
+            assert httpx.post(f"{base}/watch/{TICKER}/pause", timeout=5.0).status_code == 200
+
+            response = httpx.get(f"{base}/tape/{TICKER}/observation", timeout=5.0)
+            assert response.status_code == 200
+            yield response.json()
+        finally:
+            proc.terminate()
+            proc.wait(timeout=10)
+
+
+def test_copy_discipline_lint_is_clean_over_the_live_served_artifact(live_served_observation):
+    offenders = [
+        f"{json_path}: {violations} :: {value!r}"
+        for json_path, value in _walk_strings(live_served_observation)
+        if (violations := find_violations(value))
+    ]
+    assert offenders == [], offenders
+
+
+def test_compound_identifier_ban_is_clean_over_the_live_served_artifact(live_served_observation):
+    encoded = observation_contract.canonical_encode(live_served_observation).decode("utf-8")
+    assert _compound_identifier_violations(encoded) == []
+
+
+def test_counterexample_copy_discipline_lint_detects_an_injected_phrase_in_the_artifact(
+    live_served_observation,
+):
+    mutated = copy.deepcopy(live_served_observation)
+    mutated["observations"] = list(mutated["observations"]) + ["You should sell now."]
+    offenders = [
+        json_path for json_path, value in _walk_strings(mutated) if find_violations(value)
+    ]
+    assert offenders != []
+
+
+def test_counterexample_compound_identifier_ban_detects_an_injected_token_in_the_artifact(
+    live_served_observation,
+):
+    mutated = copy.deepcopy(live_served_observation)
+    mutated["composite_policy"] = "irrelevant value"  # a banned token as a FIELD NAME
+    encoded = observation_contract.canonical_encode(mutated).decode("utf-8")
+    assert _compound_identifier_violations(encoded) != []
+
+
+# === Mechanism 2: external-system reference guard (TC-3, TC-4) ==================================
+#
+# ``docs/goal.md``, ``docs/phases/``, ``docs/goal-archive/`` and ``project-extensions/host-guard/``
+# need no explicit exclusion code: the two scan roots below (the ``apps/`` tree, and the ONE named
+# spec file) never reach any of those paths in the first place -- host-guard.env legitimately
+# names sibling host projects ("trendora", "tensteps") for shared resource budgeting, confirmed by
+# direct inspection, which is exactly why goal.md excludes that path from ANY such scan.
+
+EXTERNAL_SYSTEM_TOKENS: tuple[str, ...] = ("workstation", "trendora", "tensteps")
+
+_APPS_SKIP_DIRS = {".venv", "node_modules", ".next", "__pycache__", ".data", ".pytest_cache", "fixtures"}
+_APPS_SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js"}
+
+
+def _apps_source_files() -> list[Path]:
+    files = []
+    for path in sorted(APPS_ROOT.rglob("*")):
+        if not path.is_file() or path.suffix not in _APPS_SOURCE_SUFFIXES:
+            continue
+        if any(part in _APPS_SKIP_DIRS for part in path.parts):
+            continue
+        if path.resolve() == SELF:  # this module names every token as data (SELF exclusion)
+            continue
+        files.append(path)
+    return files
+
+
+def _scan_files_for_tokens(files: list[Path], tokens: tuple[str, ...]) -> list[str]:
+    low_tokens = tuple(t.lower() for t in tokens)
+    offenders = []
+    for path in files:
+        text = path.read_text(errors="ignore").lower()
+        for token in low_tokens:
+            if token in text:
+                offenders.append(f"{path}: {token!r}")
+    return offenders
+
+
+def _external_system_reference_violations(files: list[Path] | None = None) -> list[str]:
+    if files is None:
+        files = _apps_source_files() + [SPEC_PATH]
+    return _scan_files_for_tokens(files, EXTERNAL_SYSTEM_TOKENS)
+
+
+def test_external_system_reference_scan_is_not_vacuous():
+    files = _apps_source_files()
+    assert len(files) > 100
+    rels = {p.relative_to(APPS_ROOT).as_posix() for p in files}
+    assert "backend/app/main.py" in rels
+    assert SPEC_PATH.exists()
+
+
... [diff_bound] apps/backend/tests/test_tape_observation_guards.py: 356 more diff lines omitted — Read the file for full detail
```
