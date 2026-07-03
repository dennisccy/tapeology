"""The PnL-history markdown regeneration CLI (era-3 capability 5, J-04) —
``python -m app.research.pnl_history``.

Pure-renders the stored PnL-ledger rows into the committed ``reports/pnl/pnl-history.md`` (the
config-owned ``pnl_history_md_path``) through the SAME ``ledger_projection`` read the
``GET /research/pnl/ledger`` route serves — never a second query, labeling, or formatting path.
Deterministic: regenerating with unchanged rows is a byte-level no-op (verifiable via
``git diff`` on the committed file). Keyless; reads the operator's journal DB via the same
``TAPEOLOGY_JOURNAL_DB`` resolution seam the backend uses. An empty ledger renders the honest
explicit empty state — never fabricated rows.
"""

from __future__ import annotations

from ..config import CONFIG
from .pnl_ledger import write_history_markdown
from .store import JournalStore


def main() -> int:
    config = CONFIG
    store = JournalStore(config.journal_db_path_resolved(), config)
    try:
        path = write_history_markdown(store, config)
    finally:
        store.close()
    print(f"pnl history rendered: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
