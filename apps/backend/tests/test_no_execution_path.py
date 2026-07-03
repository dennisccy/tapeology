"""The repo-wide no-execution-path gate (J-03 acceptance; the CRITICAL no-live-execution anti-goal).

Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no
trading API, no paper-trading API, no order tickets, no account/position management. The ONLY
permitted "fill" is the offline backtester's simulated fill computed against recorded historical
tape. This test makes that an ENFORCED invariant over every source file under ``apps/`` from the
day the first simulated fill ships.

Design (signal-bearing, not a naive substring grep):
  * Patterns are COMPOUND identifiers (``submit_order``, ``TradingClient``, ``paper_trading``,
    broker-SDK module names) — never bare prose words, so "ordered events" / "insertion order"
    / the backtests' job-``cancel`` route can never false-positive.
  * Two tiers. Tier 1 (order placement / account management / broker execution SDKs) is
    forbidden EVERYWHERE with no exceptions. Tier 2 (the vendor's ``TradingClient`` /
    ``alpaca.trading`` import / ``paper=True`` endpoint flag) is documented READ-ONLY usage —
    the one market-data adapter uses it solely for the asset-list and market-clock reference
    reads, and its own dedicated gate (``test_no_execution_or_account_api_in_adapter`` in
    ``test_real_data_gate.py``) asserts that module contains no order/account/position API.
    Tier 2 is therefore forbidden everywhere EXCEPT that one adapter (and the two test files
    that police/fake exactly those symbols).
  * The scan is proven non-vacuous (it must see a substantial file count and the app package
    itself) and the matcher is proven signal-bearing against a seeded counter-example.
"""

from __future__ import annotations

from pathlib import Path

# apps/backend/tests/<this file> -> parents[2] is the apps/ tree root.
REPO_APPS = Path(__file__).resolve().parents[2]

# Directories that carry no first-party source (build products, dependencies, virtualenvs,
# recorded data). ``fixtures`` holds committed DATA (recorded tape JSON / schema SQL), not code.
_SKIP_DIRS = {".venv", "node_modules", ".next", "__pycache__", ".data", ".pytest_cache", "fixtures"}

_SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js"}

# --- Tier 1: forbidden EVERYWHERE — order placement, routing, account/position management ---------
# Each entry is a compound identifier used by brokerage/execution APIs; none can appear in honest
# prose or in this product's own vocabulary.
TIER1_PATTERNS = (
    # Order submission / routing / lifecycle verbs (brokerage API method names).
    "submit_order",
    "place_order",
    "create_order",
    "cancel_order",
    "replace_order",
    "close_position",
    "close_all_positions",
    # Brokerage order-request types (alpaca-py trading + generic).
    "OrderRequest",
    "MarketOrderRequest",
    "LimitOrderRequest",
    "StopOrderRequest",
    "TradingStream",
    # Account / position management reads (an account surface is execution-adjacent).
    "get_account(",
    "get_all_positions",
    "get_open_position",
    # Paper trading is an EXECUTION PATH even without real money (the anti-goal names it).
    "paper_trading",
    "paper-api.alpaca.markets",
    # Broker / execution SDKs (the market-DATA modules of alpaca-py are allowed; these are not).
    "alpaca_trade_api",
    "ib_insync",
    "import ibapi",
    "robin_stocks",
    "import ccxt",
)

# --- Tier 2: the vendor trading-namespace symbols with ONE documented read-only home ---------------
TIER2_PATTERNS = (
    "alpaca.trading",  # the SDK's trading namespace (used read-only for assets/clock)
    "TradingClient",
    "paper=True",      # selects the keyless-capable endpoint for those read-only reference reads
)

# Files allowed to carry Tier-2 symbols (relative to the ``apps/`` root), each with a reason:
#   * the one vendor adapter — read-only asset/clock reference, guarded by its own no-order test;
#   * the vendor gate test — names these symbols as its own forbidden/fake-list data;
#   * the responsiveness test — monkeypatches the read-only TradingClient for clock/universe fakes.
TIER2_ALLOWED = {
    "backend/app/providers/adapters/alpaca.py",
    "backend/tests/test_real_data_gate.py",
    "backend/tests/test_vendor_responsiveness.py",
}

# This gate itself names every pattern as data, and the adapter gate test names the Tier-1 verbs
# as ITS forbidden-list data — both are scanning/policing code, not execution code.
SELF = "backend/tests/test_no_execution_path.py"
TIER1_ALLOWED = {SELF, "backend/tests/test_real_data_gate.py"}


def _source_files() -> list[Path]:
    files = []
    for path in sorted(REPO_APPS.rglob("*")):
        if not path.is_file() or path.suffix not in _SOURCE_SUFFIXES:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def _rel(path: Path) -> str:
    return path.relative_to(REPO_APPS).as_posix()


def test_scan_is_not_vacuous():
    files = _source_files()
    rels = {_rel(p) for p in files}
    # A path bug must never silently pass an empty scan: the sweep sees the real tree.
    assert len(files) > 100
    assert "backend/app/main.py" in rels
    assert "backend/app/research/backtests.py" in rels  # the module that ships simulated fills
    assert any(r.startswith("frontend/") for r in rels)


def test_matcher_catches_a_seeded_counter_example():
    # Signal-bearing by proof: a line of would-be broker code trips the patterns.
    seeded = "client = TradingClient(key, secret); client.submit_order(order)"
    assert any(p in seeded for p in TIER1_PATTERNS)
    assert any(p in seeded for p in TIER2_PATTERNS)


def test_no_order_account_or_broker_execution_code_anywhere():
    offenders: list[str] = []
    for path in _source_files():
        rel = _rel(path)
        if rel in TIER1_ALLOWED:
            continue
        text = path.read_text(errors="ignore")
        for pattern in TIER1_PATTERNS:
            if pattern in text:
                offenders.append(f"{rel}: {pattern!r}")
    assert offenders == [], (
        "order-placement / account-management / broker-SDK code found — the no-execution "
        f"anti-goal is violated: {offenders}"
    )


def test_vendor_trading_namespace_confined_to_the_read_only_adapter():
    offenders: list[str] = []
    for path in _source_files():
        rel = _rel(path)
        if rel in TIER2_ALLOWED or rel == SELF:
            continue
        text = path.read_text(errors="ignore")
        for pattern in TIER2_PATTERNS:
            if pattern in text:
                offenders.append(f"{rel}: {pattern!r}")
    assert offenders == [], (
        "vendor trading-namespace symbols outside the one documented read-only adapter: "
        f"{offenders}"
    )
