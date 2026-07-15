"""The PnL-history markdown regeneration CLI (era-3 capability 5, J-04) —
``python -m app.research.pnl_history``.

Pure-renders the stored PnL-ledger rows into the committed ``reports/pnl/pnl-history.md`` (the
config-owned ``pnl_history_md_path``) through the SAME ``ledger_projection`` read the
``GET /research/pnl/ledger`` route serves — never a second query, labeling, or formatting path.
Deterministic: regenerating with unchanged rows is a byte-level no-op (verifiable via
``git diff`` on the committed file). Keyless; reads the operator's journal DB via the same
``TAPEOLOGY_JOURNAL_DB`` resolution seam the backend uses. An empty ledger renders the honest
explicit empty state — never fabricated rows.

era-5B J-08 additive: ``--append-report`` gives the operator a single command to append a
COMPLETED ``run_strategy_comparison_report`` output (e.g. the first real, credentialed,
cache-warmed compute over the full corpus — the operator-gated carry this iteration builds the
machinery for but does not itself run) to the ledger, then regenerate the committed markdown from
the now-updated stored rows in the SAME step. Composition is the single
``append_strategy_comparison_row`` writer (``pnl_ledger.py``); rendering is the SAME
``write_history_markdown`` every other regeneration uses — no second path. Omitting
``--append-report`` keeps ``main()``'s pre-J-08 behaviour EXACTLY as before (render-only, no
append) — byte-for-byte unchanged.

era-5B J-08 additive: ``--out`` optionally overrides the render target (the ``edge_report.py
--out`` precedent), defaulting to ``None`` — i.e. the EXACT pre-J-08 default (the config-owned
committed path) — when omitted. Exists so this CLI is safely testable end-to-end (a hermetic
``tmp_path`` target) without ever risking a write to the real committed file; an operator running
the real append still omits it to target the committed file, exactly as before.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..config import CONFIG, Config
from .pnl_ledger import LedgerCompositionError, append_strategy_comparison_row, write_history_markdown
from .store import DuplicateEnhancementError, JournalStore


def append_strategy_comparison_and_render(
    store: JournalStore,
    config: Config,
    *,
    enhancement_id: str,
    title: str,
    report: dict,
    path: Path | None = None,
) -> Path:
    """Append ONE completed 3-way comparison report to the PnL ledger, then regenerate the
    markdown from the (now-updated) stored rows — the single operator-run act that lands a real
    edge-report compute's register (era-5B J-08). Composition is the single
    ``append_strategy_comparison_row`` writer; rendering is the SAME ``write_history_markdown``
    every other regeneration uses — no second path. Raises ``LedgerCompositionError`` (a malformed
    ``report``) or the store's ``DuplicateEnhancementError`` (a re-used ``enhancement_id``)
    explicitly — nothing is appended OR rendered on either failure."""
    append_strategy_comparison_row(
        store, config, enhancement_id=enhancement_id, title=title, report=report
    )
    return write_history_markdown(store, config, path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate the committed PnL-history markdown from the stored ledger rows, "
        "optionally appending ONE completed 3-way strategy-comparison report first."
    )
    parser.add_argument(
        "--append-report",
        metavar="PATH",
        help="path to a completed run_strategy_comparison_report JSON file to append before "
        "rendering (era-5B J-08); omit for the pre-J-08 render-only behaviour",
    )
    parser.add_argument("--enhancement-id", help="the enhancement id for the appended row (required with --append-report)")
    parser.add_argument("--title", help="the appended row's title (required with --append-report)")
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="override the markdown output path (default: the config-owned committed "
        "reports/pnl/pnl-history.md — omit this for a real operator run)",
    )
    args = parser.parse_args()

    if args.append_report and (not args.enhancement_id or not args.title):
        print(
            "error: --append-report requires both --enhancement-id and --title", file=sys.stderr
        )
        return 1

    out_path = Path(args.out) if args.out else None
    config = CONFIG
    store = JournalStore(config.journal_db_path_resolved(), config)
    try:
        if args.append_report:
            report = json.loads(Path(args.append_report).read_text())
            try:
                path = append_strategy_comparison_and_render(
                    store, config, enhancement_id=args.enhancement_id, title=args.title,
                    report=report, path=out_path,
                )
            except (LedgerCompositionError, DuplicateEnhancementError) as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
        else:
            path = write_history_markdown(store, config, out_path)
    finally:
        store.close()
    print(f"pnl history rendered: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
