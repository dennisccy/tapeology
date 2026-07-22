"""Structural guards for the /structure edge-report compute LIVE STATUS UI (era-fast_wall
follow-up: "the ui should be able to show the status of the compute and make the user knows it
is running").

The frontend has no test runner (the repo's established precedent — see
test_price_chart_confluence.py's module docstring); frontend logic is pinned keylessly by reading
the `.tsx` source directly. This module pins the compute-status surface added to
`NotComputedPanel` in `apps/frontend/app/structure/page.tsx`:

  1. the RUNNING state renders a live progress block — the done/total counts, the CURRENT
     dataset x strategy pair (served verbatim from the snapshot's own ``progress.current``, the
     dataset id resolved to its symbol via the ALREADY-FETCHED registry rows — a pure lookup of
     served values, never a recomputation), and an elapsed clock derived from the snapshot's own
     ``started_utc``;
  2. a Cancel action wired to the EXISTING `cancelEdgeReportCompute()` client (the J-04 endpoint
     that shipped unused), with the cooperative-cancel copy honest about finishing the current
     backtest first;
  3. an explicit terminal `cancelled` state (never rendered as plain idle);
  4. the poll loop keeps its resume-on-load seeding and its refetch-once-on-done swap.

Real browser verification (screenshots of running/cancelled/report states) is the browser-QA
layer's job; these pins keep the SOURCE honest between browser passes.
"""

from __future__ import annotations

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
STRUCTURE_PAGE = BACKEND_DIR.parent / "frontend" / "app" / "structure" / "page.tsx"


def _source() -> str:
    assert STRUCTURE_PAGE.exists(), f"missing {STRUCTURE_PAGE}"
    return STRUCTURE_PAGE.read_text(encoding="utf-8")


def test_running_state_renders_progress_current_pair_and_elapsed():
    src = _source()
    for testid in (
        "edge-report-compute-running",
        "edge-report-compute-progress",
        "edge-report-compute-current",
        "edge-report-compute-elapsed",
    ):
        assert f'data-testid="{testid}"' in src, f"missing running-state testid {testid}"
    # The current pair is the SERVED snapshot value (progress.current), and the symbol comes from
    # the already-fetched dataset registry rows — a lookup, never a recomputation.
    assert "progress.current" in src
    assert "datasets.find((d) => d.id === current.dataset_id)" in src
    # The elapsed clock derives from the snapshot's own started_utc (display-only).
    assert "formatComputeElapsed(compute.started_utc)" in src


def test_cancel_action_is_wired_to_the_existing_client_and_is_honest_about_cooperative_cancel():
    src = _source()
    assert 'data-testid="edge-report-compute-cancel"' in src
    assert "cancelEdgeReportCompute()" in src, "must call the existing J-04 cancel client"
    # Honest cooperative-cancel copy: the server observes cancellation BETWEEN backtests.
    assert "Cancelling — finishing the current backtest…" in src
    assert 'data-testid="edge-report-compute-cancel-error"' in src


def test_cancelled_terminal_state_is_explicit_never_plain_idle():
    src = _source()
    assert 'data-testid="edge-report-compute-cancelled"' in src
    assert 'compute?.state === "cancelled"' in src
    assert "Compute cancelled" in src


def test_poll_loop_keeps_resume_seed_and_refetch_once_on_done():
    src = _source()
    # Mount effect seeds the snapshot from the not-computed payload (resume-on-load, J-04).
    assert "setComputeSnapshot(result.data.compute)" in src
    # The poll refetches the report exactly once when the job resolves done (the panel swap).
    assert 'next.data.state === "done"' in src
    assert "fetchEdgeReport()" in src
