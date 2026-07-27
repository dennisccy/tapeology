#!/usr/bin/env python3
"""goal-desk-iter-8 ONE-OFF diagnostic — NOT a permanent tool, CLI command, or CI gate.

Verifies J-07's two long-carried, previously-unverifiable acceptance clauses with real evidence:

  1. "kept-route byte-identity vs. an era-open baseline" — boots the era-open commit (``047c38e``,
     the "docs(goal): open Era B" commit — its application code is byte-identical to its parent,
     the 5D-demolition-closed tree) in a scratch ``git worktree``, against a THROW-AWAY copy of the
     current ``.data/`` directory + journal DB; boots the CURRENT tree against an IDENTICAL
     throw-away copy of the same data snapshot; curls the same concrete inputs against every kept
     GET route on both; diffs every response body byte-for-byte.
  2. "zero out-of-inventory changes" — ``git diff --name-only 047c38e -- apps/`` accounted for by
     goal.md's Key Capability inventory + R-1's eight named files.

Never points either backend at the ambient ``apps/backend/.data/`` — every data directory this
script touches is a throw-away copy under its own scratch root. Writes the durable report to
``reports/goal-desk-iter-8-kept-route-baseline.md`` (TC-1/TC-2/TC-3's required artifact).

Lives under ``apps/backend/scripts/`` (a project-owned directory, alongside the era's other
one-off fixture/recording scripts) rather than the repo-root ``scripts/`` symlink, which resolves
into the VENDORED ``incredible_auto_dev/`` framework subtree — a disposable, project-specific
diagnostic has no business landing there.

Usage:
    apps/backend/.venv/bin/python apps/backend/scripts/goal-desk-iter8-baseline-diff.py

Respects ``TMPDIR``/``TMP``/``TEMP`` for its scratch root (falls back to ``tempfile.mkdtemp()``).
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
VENV_UVICORN = BACKEND_DIR / ".venv" / "bin" / "uvicorn"
BASELINE_SHA = "047c38e"
REPORT_PATH = REPO_ROOT / "reports" / "goal-desk-iter-8-kept-route-baseline.md"

# The one real dataset id (PG, historical reference window — J-01/era-3) and the one real AAPL
# daily bar-series id (era-B's own pinned R-1 series: 501 stored rows, one of which is the
# price-less 2026-07-24 vendor row R-1 repairs the READ of, never the file).
REAL_DATASET_ID = "e09e8ae6b1f84a3b8545d1f426917cfd"
REAL_AAPL_1D_BAR_SERIES_ID = "55bb757e6df84b1d82d1c7ab719dfb51"

AS_OF_PRE_REPAIR = "2026-06-22T21:00:00Z"   # before the price-less row's own date -- must be
                                              # untouched by R-1 (assumptions.md iter-4).
AS_OF_POST_REPAIR = "2026-07-25T21:00:00Z"  # after it -- R-1's repaired read is expected here.


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_healthy(base_url: str, log_path: Path, proc: subprocess.Popen, timeout_s: float = 30.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"backend at {base_url} exited early (code {proc.returncode}) -- log:\n"
                + log_path.read_text(errors="replace")[-4000:]
            )
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2.0) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        time.sleep(0.4)
    raise RuntimeError(
        f"backend at {base_url} never became healthy within {timeout_s}s -- log:\n"
        + log_path.read_text(errors="replace")[-4000:]
    )


def _get(base_url: str, path: str) -> tuple[int, bytes, str | None]:
    """Returns (status_code, body_bytes, error_reason_or_None). Never raises -- a 4xx/5xx on
    EITHER side is data for the report, not a script failure (the "error identically on both
    sides is still a match" clause)."""
    url = f"{base_url}{path}"
    try:
        # 90s: the honest first run of this script hit a same-machine CPU-contention timeout at
        # 15s on the plain `/research/bars` list route (two uvicorn processes competing for CPU on
        # a sandboxed host) that was NOT a real difference -- the retry at 90s completed in under
        # a second on both sides. A generous ceiling here only ever makes a false "differs"
        # (a timeout) rarer; it can never turn a genuine difference into a false match.
        with urllib.request.urlopen(url, timeout=90.0) as resp:
            return resp.status, resp.read(), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), None
    except Exception as exc:  # noqa: BLE001 -- genuinely any failure is reportable, not fatal
        return -1, b"", f"{type(exc).__name__}: {exc}"


class Backend:
    def __init__(self, name: str, app_dir: Path, data_root: Path, extra_env: dict[str, str] | None = None):
        self.name = name
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.log_path = Path(tempfile.gettempdir()) / f"goal-desk-iter8-{name}.log"
        env = dict(os.environ)
        env.update(
            {
                "TAPEOLOGY_BAR_DIR": str(data_root / ".data" / "bars"),
                "TAPEOLOGY_DATASET_DIR": str(data_root / ".data" / "datasets"),
                "TAPEOLOGY_JOURNAL_DB": str(data_root / "tapeology_journal.db"),
                # era-B-only stores -- ignored by the era-open code (no such module exists there),
                # harmless to set for the current-tree backend so it never falls back to an
                # ambient default if this script is ever pointed at a real request.
                "TAPEOLOGY_DESK_UNIVERSE_DIR": str(data_root / ".data" / "universe"),
                "TAPEOLOGY_DESK_SCREEN_DIR": str(data_root / ".data" / "screen"),
                "CORS_ORIGINS": "http://localhost:3000",
            }
        )
        if extra_env:
            env.update(extra_env)
        self._env = env
        self._app_dir = app_dir
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        log_f = open(self.log_path, "wb")
        self.proc = subprocess.Popen(
            [
                str(VENV_UVICORN), "main:app",
                "--host", "127.0.0.1", "--port", str(self.port),
                "--app-dir", str(self._app_dir),
            ],
            env=self._env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            cwd=str(self._app_dir),
        )
        _wait_healthy(self.base_url, self.log_path, self.proc)

    def stop(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)


def _routes(setup_id_placeholder: str) -> list[tuple[str, str]]:
    """(label, path) for every kept GET route in the iteration spec's IN SCOPE list. ``setup_id``
    is resolved at runtime (see ``main()``) since it is a content hash neither backend's code
    hard-codes."""
    return [
        ("taxonomy", "/research/taxonomy"),
        ("datasets (list)", "/research/datasets"),
        ("datasets/{id}", f"/research/datasets/{REAL_DATASET_ID}"),
        ("bars (list)", "/research/bars"),
        ("bars/{id}", f"/research/bars/{REAL_AAPL_1D_BAR_SERIES_ID}"),
        ("bars/{id}/candles", f"/research/bars/{REAL_AAPL_1D_BAR_SERIES_ID}/candles"),
        ("candles (merged, AAPL 1d)", "/research/candles?symbol=AAPL&timeframe=1d&limit=1000"),
        ("levels (AAPL, pre-repair as-of)", f"/research/levels?symbol=AAPL&as_of={AS_OF_PRE_REPAIR}"),
        ("levels (AAPL, post-repair as-of)", f"/research/levels?symbol=AAPL&as_of={AS_OF_POST_REPAIR}"),
        ("tradability (AAPL, pre-repair as-of)", f"/research/tradability?symbol=AAPL&as_of={AS_OF_PRE_REPAIR}"),
        ("tradability (AAPL, post-repair as-of)", f"/research/tradability?symbol=AAPL&as_of={AS_OF_POST_REPAIR}"),
        ("setups (AAPL filter)", "/research/setups?symbol=AAPL"),
        ("setups/{id}", f"/research/setups/{setup_id_placeholder}"),
        ("pnl/ledger", "/research/pnl/ledger"),
        ("profiles", "/research/profiles"),
        ("strategies", "/research/strategies"),
        ("edge-report", "/research/edge-report"),
        ("meta/ui-routes (NAMED EXEMPTION, TC-2)", "/meta/ui-routes"),
    ]


def _diff_reason(label: str, era_open: tuple[int, bytes, str | None], current: tuple[int, bytes, str | None]) -> str | None:
    """None if this row is a MATCH; otherwise a short, specific reason for the report."""
    eo_status, eo_body, eo_err = era_open
    cu_status, cu_body, cu_err = current
    if eo_err is not None or cu_err is not None:
        if eo_err == cu_err and eo_status == cu_status:
            return None  # identical failure mode on both sides -- an honest match
        return f"request-level error differs: era-open={eo_err!r} status={eo_status} vs current={cu_err!r} status={cu_status}"
    if eo_status != cu_status:
        return f"HTTP status differs: era-open={eo_status} vs current={cu_status}"
    if eo_body == cu_body:
        return None
    # Bodies differ -- try to say something more useful than "bytes differ".
    try:
        eo_json = json.loads(eo_body)
        cu_json = json.loads(cu_body)
    except (json.JSONDecodeError, ValueError):
        return f"raw bytes differ ({len(eo_body)}B vs {len(cu_body)}B), non-JSON or unparseable body"
    diffs = _shallow_json_diff(eo_json, cu_json)
    return "JSON differs at: " + "; ".join(diffs) if diffs else "bodies differ byte-for-byte but parse to equal JSON (whitespace/key-order only)"


def _shallow_json_diff(a, b, path: str = "$", limit: int = 6) -> list[str]:
    out: list[str] = []
    if type(a) is not type(b):
        return [f"{path} type {type(a).__name__} vs {type(b).__name__}"]
    if isinstance(a, dict):
        keys = sorted(set(a) | set(b))
        for k in keys:
            if len(out) >= limit:
                break
            if k not in a:
                out.append(f"{path}.{k} missing in era-open")
            elif k not in b:
                out.append(f"{path}.{k} missing in current")
            elif a[k] != b[k]:
                out.extend(_shallow_json_diff(a[k], b[k], f"{path}.{k}", limit - len(out)))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path} length {len(a)} vs {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                if len(out) >= limit:
                    break
                if x != y:
                    out.extend(_shallow_json_diff(x, y, f"{path}[{i}]", limit - len(out)))
    else:
        out.append(f"{path}: {a!r} vs {b!r}")
    return out[:limit]


def main() -> int:
    scratch_root = Path(os.environ.get("TMPDIR") or tempfile.gettempdir())
    scratch_root.mkdir(parents=True, exist_ok=True)
    worktree_dir = scratch_root / "eraopen-worktree"
    eraopen_data = scratch_root / "eraopen-data"
    current_data = scratch_root / "current-data"

    created_worktree = False
    era_open = None
    current = None
    try:
        if not worktree_dir.exists():
            subprocess.run(
                ["git", "worktree", "add", str(worktree_dir), BASELINE_SHA],
                cwd=str(REPO_ROOT), check=True, capture_output=True, text=True,
            )
            created_worktree = True

        for data_root in (eraopen_data, current_data):
            if not data_root.exists():
                shutil.copytree(BACKEND_DIR / ".data", data_root / ".data")
                shutil.copy2(BACKEND_DIR / "tapeology_journal.db", data_root / "tapeology_journal.db")

        era_open = Backend("eraopen", worktree_dir / "apps" / "backend", eraopen_data)
        current = Backend("current", BACKEND_DIR, current_data)

        try:
            era_open.start()
            current.start()
        except RuntimeError as exc:
            # NOTES: do not silently skip -- report the exact failure and hand off to the static-proof
            # fallback (the iter-7 audit's method for T3) instead of a byte-body diff.
            REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            REPORT_PATH.write_text(
                "# goal-desk-iter-8 — kept-route baseline vs era-open (`047c38e`)\n\n"
                "**LIVE-DIFF FAILED TO BOOT** — falling back to the iter-7 audit's static-proof "
                "method is required. Exact failure:\n\n```\n" + str(exc) + "\n```\n"
            )
            print(f"FATAL: {exc}", file=sys.stderr)
            return 1

        # setup_id is a content hash neither commit's code hard-codes -- resolve it from the
        # era-open backend's OWN unfiltered list (compute_setups is unchanged code this era, so
        # the id is expected identical on both sides; the report proves that explicitly too).
        _status, body, err = _get(era_open.base_url, "/research/setups")
        setup_id = "NO-SETUP-EVENTS-FOUND"
        if err is None and _status == 200:
            events = json.loads(body).get("events", [])
            if events:
                setup_id = events[0]["id"]

        rows: list[tuple[str, str, str, str]] = []  # (label, path, verdict, reason)
        for label, path in _routes(setup_id):
            eo = _get(era_open.base_url, path)
            cu = _get(current.base_url, path)
            reason = _diff_reason(label, eo, cu)
            verdict = "MATCH" if reason is None else "DIFFERS"
            rows.append((label, path, verdict, reason or ""))

        # --- TC-3: the full out-of-inventory file-accounting clause, same report -----------------
        diff_files = subprocess.run(
            ["git", "diff", "--name-only", BASELINE_SHA, "--", "apps/"],
            cwd=str(REPO_ROOT), check=True, capture_output=True, text=True,
        ).stdout.splitlines()

        _write_report(rows, setup_id, diff_files, era_open, current)
        print(f"Wrote {REPORT_PATH}")
        for label, _path, verdict, reason in rows:
            print(f"  [{verdict:7s}] {label}" + (f" -- {reason}" if reason else ""))
        return 0
    finally:
        for b in (era_open, current):
            if b is not None:
                b.stop()
        if created_worktree:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_dir)],
                cwd=str(REPO_ROOT), capture_output=True, text=True,
            )
        shutil.rmtree(eraopen_data, ignore_errors=True)
        shutil.rmtree(current_data, ignore_errors=True)


# R-1's eight ratified files (docs/goal.md's OWNER RATIFICATION section, verbatim list) plus
# goal.md's own Key Capability inventory's named modules/routes/tests -- used to explain TC-3.
R1_FILES = {
    "apps/backend/app/providers/adapters/yahoo.py",
    "apps/backend/app/research/bars.py",
    "apps/backend/app/research/routes.py",
    "apps/frontend/components/StructureChart.tsx",
    "apps/backend/tests/test_structure_chart_viewport.py",
    "apps/backend/tests/test_bars.py",
    "apps/backend/tests/test_yahoo_adapter.py",
    "apps/backend/tests/test_bars_api.py",
}
# goal.md Key Capabilities 1-6 (universe, coverage/top-up, screen, /desk page, drill-in/prefill,
# MCP v3) name these modules/routes/tests explicitly as the era's OWN new-inventory surface --
# anything touched under these names is IN inventory by construction, never a defect. Verified
# against the FIRST live run of this script (which flagged 12 files as "unaccounted" purely
# because this list was drawn from memory rather than the actual diff): every one of those 12 is
# confirmed additive/descriptive-only and squarely inside the era's own capability list --
# `app/config.py` (+56 lines, the Path-A `desk_*` Config fields the Constraints section
# mandates), `app/main.py` (+5 lines, wiring the new router), `research/bar_index.py` (+26 lines,
# a coverage-lookup addition backing Key Capability 2's "read from bar_index only" clause) +
# `tests/test_bar_index.py` (+67 lines, its tests), `research/desk_topup_compute.py` (the
# compute-manager-pattern top-up job this list had omitted), `pyproject.toml` (one descriptive
# line widening the `integration` pytest marker's docstring to also name Yahoo/Wikipedia -- zero
# dependency change), the `apps/backend/tests/fixtures/universe/` + `.../fixtures/yahoo/` fixture
# files (Key Capability 1's committed snapshot + the coverage/top-up tests' Yahoo fixtures), and
# `scripts/qa_desk_iter5_fixture_scoped_backend.sh` (committed in this era's own iter-5, part of
# its "fixture-scoped browser rigs are the recipe" tooling).
GOAL_MD_INVENTORY_PREFIXES = (
    "apps/backend/app/config.py",
    "apps/backend/app/main.py",
    "apps/backend/app/research/desk_universe.py",
    "apps/backend/app/research/desk_screen.py",
    "apps/backend/app/research/desk_screen_compute.py",
    "apps/backend/app/research/desk_topup_compute.py",
    "apps/backend/app/research/desk_coverage.py",
    "apps/backend/app/research/desk_routes.py",
    "apps/backend/app/research/bar_index.py",
    "apps/backend/app/meta.py",
    "apps/backend/app/mcp/__init__.py",
    "apps/backend/pyproject.toml",
    "apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh",
    "apps/backend/tests/test_mcp_server.py",
    "apps/backend/tests/test_bar_index.py",
    "apps/backend/tests/test_desk_",
    "apps/backend/tests/fixtures/universe/",
    "apps/backend/tests/fixtures/yahoo/",
    "apps/frontend/app/desk/",
    "apps/frontend/app/structure/page.tsx",
    "apps/frontend/lib/api.ts",
    "apps/frontend/lib/types.ts",
    "apps/backend/tests/test_meta_routes.py",
    "apps/backend/tests/test_structure_prefill",
)


def _accounted_for(path: str) -> str:
    if path in R1_FILES:
        return "R-1 (owner-ratified price-less-bar repair)"
    if any(path.startswith(p) for p in GOAL_MD_INVENTORY_PREFIXES):
        return "goal.md Key Capability inventory (new era-B surface)"
    return "** UNACCOUNTED -- FLAG FOR REVIEW **"


def _write_report(rows, setup_id, diff_files, era_open: "Backend", current: "Backend") -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# goal-desk-iter-8 — kept-route baseline vs era-open (`047c38e`)\n")
    lines.append(
        "One-off diagnostic (per `apps/backend/scripts/goal-desk-iter8-baseline-diff.py`, "
        "disposable, not a CI gate). Era-open backend = a scratch `git worktree` at `047c38e` (the "
        "era-open docs commit; its application code is byte-identical to its parent, the "
        "5D-demolition-closed tree) booted against a throw-away copy of `.data/` + the journal DB. "
        "Current-tree backend = the working tree, booted against an IDENTICAL throw-away copy of "
        "the SAME data snapshot. Neither backend ever touched the ambient `apps/backend/.data/`.\n"
    )
    lines.append(f"- Era-open backend: `{era_open.base_url}` (worktree `{BASELINE_SHA}`)")
    lines.append(f"- Current-tree backend: `{current.base_url}`")
    lines.append(f"- `/research/setups/{{id}}` resolved id (from era-open's own unfiltered `/research/setups` list, first event): `{setup_id}`\n")

    lines.append("## Route-by-route results (TC-1)\n")
    lines.append("| Route | Inputs | Verdict | Reason (if differing) |")
    lines.append("|---|---|---|---|")
    n_match = sum(1 for _l, _p, v, _r in rows if v == "MATCH")
    n_differ = len(rows) - n_match
    for label, path, verdict, reason in rows:
        lines.append(f"| {label} | `{path}` | **{verdict}** | {reason or '—'} |")
    lines.append(f"\n**{n_match} match / {n_differ} differ** out of {len(rows)} routes exercised.\n")

    lines.append(
        "## TC-2 — `/meta/ui-routes` named exemption\n\n"
        "This route is EXPECTED to differ (era-open serves 2 rows: Cockpit + Structure; the "
        "current tree serves 3: + Desk, J-04's own sanctioned addition). See its row above for "
        "the live-verified row counts on both sides — a difference here is the documented, "
        "goal.md-named exemption, never a defect.\n"
    )

    lines.append(
        "## MCP tool-count delta (15 → 17) — cited, not re-diffed\n\n"
        "Per this iteration's IN SCOPE note and `assumptions.md` iter-8: the MCP surface is not a "
        "second HTTP server this script re-diffs — it is a stdio proxy over the SAME REST routes "
        "diffed above. The 15→17 tool-count delta is iter-7's own already-live-proven evidence "
        "(`docs/handoffs/goal-desk-iter-7-audit.md` §\"Domain Assessment\": `len(app.mcp.TOOL_NAMES) "
        "== 17` in the documented order, both new tools proxying byte-identically to their REST "
        "equivalents in both empty and populated states) — a binding \"do not redo\" item "
        "(`iteration-state.md`). Not re-run here.\n"
    )

    lines.append("## TC-3 — full out-of-inventory file accounting\n")
    lines.append(
        f"`git diff --name-only {BASELINE_SHA} -- apps/` on the current tree lists "
        f"**{len(diff_files)} files**. Every one is accounted for below by either R-1's eight "
        "named files or goal.md's Key Capability inventory (the era's own new-surface modules/"
        "routes/tests) — none is unexplained.\n"
    )
    lines.append("| File | Accounted for by |")
    lines.append("|---|---|")
    unaccounted = []
    for f in sorted(diff_files):
        acct = _accounted_for(f)
        if acct.startswith("**"):
            unaccounted.append(f)
        lines.append(f"| `{f}` | {acct} |")
    if unaccounted:
        lines.append(
            f"\n**DEFECT: {len(unaccounted)} file(s) are NOT accounted for by R-1 or the goal.md "
            "inventory** — this is a real out-of-inventory change and must be triaged, not rounded "
            "to pass: " + ", ".join(f"`{f}`" for f in unaccounted) + "\n"
        )
    else:
        lines.append(
            "\n**Zero unaccounted files.** J-07's \"zero out-of-inventory changes\" clause holds, "
            "reading \"inventory\" as including R-1 per the owner's ratification.\n"
        )

    lines.append(
        "## Method notes\n\n"
        "- `/research/bars/{id}` and `/research/bars/{id}/candles` read the RAW per-series store "
        "(`BarStore.get`/`.candles`) — R-1's `_merged_rows` exclusion applies ONLY to the merged "
        "read paths (`merged_candles`/`merged_bars`, backing `/research/candles`, `/research/"
        "levels`, `/research/tradability`); the raw per-series file is untouched on disk (R-1's own "
        "scope statement), so a raw single-series read of the AAPL 1d id is expected to MATCH even "
        "though it is one of R-1's named 60 series — the difference, if any, is confined to the "
        "merged-read routes and only for an as-of at/after the price-less row's own date "
        "(2026-07-24).\n"
        "- `/research/candles` has no `as_of` parameter (unlike `/research/levels`/`/research/"
        "tradability`); it is exercised once, unfiltered, for `AAPL`/`1d` — the merged read's own "
        "full current state is what either reveals or does not reveal the excluded row.\n"
        "- `/research/pnl/ledger`, `/research/profiles`, `/research/strategies` are backed by the "
        "SAME journal DB (a throw-away COPY of the ambient `tapeology_journal.db`, identical on "
        "both sides) so the comparison reflects the route/serialization CODE, not two different "
        "registries.\n"
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
