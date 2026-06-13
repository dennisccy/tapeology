"""The ONE consolidated scenario -> ``data_feed`` mapping (data-contract row 26, iter-24, J-67).

These pin the single owner (``app.research.feed_basis.data_feed_for_scenario``):
  * defaults are byte-identical to the pre-iter-24 hardcoded literals (every existing stamp /
    pinned test / persisted record unchanged);
  * it reads the config-owned per-mode feed keys, so flipping ``live_feed="sip"`` relabels NEW
    stamps with ZERO code change (the J-67 single-config-value clause);
  * the ``live ``/``historical `` prefixes ALWAYS resolve via config — never a silent literal;
  * exactly ONE such function exists in the codebase (no parallel copy in ``hints.py``).
"""

import ast
import pathlib

from app.config import CONFIG, Config
from app.research.feed_basis import data_feed_for_scenario


def test_defaults_byte_identical_to_prior_hardcoded_literals():
    # The default config keeps live_feed="iex", historical_feed="sip" -> the exact prior outputs.
    assert data_feed_for_scenario("buyer_control", CONFIG) == "sim"
    assert data_feed_for_scenario("bid_absorption", CONFIG) == "sim"
    assert data_feed_for_scenario("SIM-CHOP", CONFIG) == "sim"
    assert (
        data_feed_for_scenario(
            "historical AAPL 2024-05-14T09:30-2024-05-14T09:40", CONFIG
        )
        == "sip"
    )
    assert data_feed_for_scenario("live AAPL", CONFIG) == "iex"


def test_flipping_live_feed_relabels_new_stamps_with_no_code_change():
    # A SIP-entitled operator upgrades live with ONE config value — no relabeling code (J-67).
    sip_live = Config(live_feed="sip")
    assert data_feed_for_scenario("live AAPL", sip_live) == "sip"
    # Historical is independent and still SIP.
    assert data_feed_for_scenario("historical AAPL win", sip_live) == "sip"
    # Sim is unaffected by the feed config.
    assert data_feed_for_scenario("buyer_control", sip_live) == "sim"


def test_flipping_historical_feed_relabels_via_config():
    iex_hist = Config(historical_feed="iex")
    assert data_feed_for_scenario("historical AAPL win", iex_hist) == "iex"
    assert data_feed_for_scenario("live AAPL", iex_hist) == "iex"  # default live unchanged


def test_prefixes_always_resolve_via_config_never_a_literal():
    # Even an exotic feed value flows through verbatim — the prefix NEVER yields a silent literal.
    exotic = Config(live_feed="otc", historical_feed="darkpool")
    assert data_feed_for_scenario("live TSLA", exotic) == "otc"
    assert data_feed_for_scenario("historical TSLA win", exotic) == "darkpool"
    # A genuine sim scenario (no recognized prefix) still falls through to the honest "sim".
    assert data_feed_for_scenario("ask_absorption", exotic) == "sim"


def test_both_feed_keys_are_in_the_config_fingerprint():
    # Both keys are IN config_fingerprint (NOT excluded) — flipping either MUST move the fingerprint
    # (the never-pool-across-feeds honesty mechanism). Consolidation itself adds NO new key, so the
    # DEFAULT fingerprint is unchanged (asserted implicitly by every pinned stamp test staying green).
    base = CONFIG.config_fingerprint()
    assert base != Config(live_feed="sip").config_fingerprint()
    assert base != Config(historical_feed="iex").config_fingerprint()


def test_exactly_one_mapping_function_in_the_codebase():
    # The hints.py duplicate is REMOVED, not paralleled: exactly ONE module DEFINES the function.
    app_dir = pathlib.Path(__file__).resolve().parent.parent / "app"
    definers: list[str] = []
    for py in app_dir.rglob("*.py"):
        tree = ast.parse(py.read_text(), filename=str(py))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == "data_feed_for_scenario"
            ):
                definers.append(str(py.relative_to(app_dir)))
    assert definers == ["research/feed_basis.py"], (
        f"exactly one definition expected, found: {definers}"
    )
