"""The SINGLE owner of the scenario -> ``data_feed`` mapping (data-contract row 26, iter-24).

A leaf module so both ``monitor`` and ``hints`` (and ``studies`` / ``routes``) import the ONE
function with no monitor<->hints import cycle. Before iter-24 the mapping lived in two copies
(``monitor.py`` canonical + a ``hints.py`` local duplicate), each HARDCODING ``"iex"``/``"sip"``;
editing two copies in lockstep is exactly the drift the coherence-auditor exists to prevent, so the
mapping consolidates here and reads the config-owned per-mode feed keys.

Why config-aligned (J-67's final acceptance clause, now provable):
  * a ``live <SYM>`` source streams ``config.live_feed`` (default ``"iex"``);
  * a ``historical <SYM> <window>`` source replays ``config.historical_feed`` (default ``"sip"``);
  * everything else is a simulated scenario -> ``"sim"``.

Defaults are unchanged (``live_feed="iex"``, ``historical_feed="sip"``), so every existing stamp,
pinned test, and persisted record is BYTE-IDENTICAL. A SIP-entitled operator who upgrades live by
flipping ``live_feed="sip"`` in config relabels NEW stamps and the served basis with ZERO relabeling
code — the single-config-value clause. Both keys are already IN ``config_fingerprint`` (not in the
exclusion set), so this consolidation moves no fingerprint.

The ``live ``/``historical `` PREFIXES always resolve via config — never a silent literal — and only a
genuine sim scenario (no recognized prefix) falls through to ``"sim"`` (the honest default).
"""

from __future__ import annotations

from ..config import Config


def data_feed_for_scenario(scenario: str, config: Config) -> str:
    """Map the snapshot's source descriptor (``scenario``) to the canonical ``data_feed`` stamp.

    Reads the config-owned per-mode feed keys (``config.live_feed`` / ``config.historical_feed``) so
    the feed-per-mode seam stays config-owned: a ``live <SYM>`` source -> ``config.live_feed``; a
    ``historical <SYM> <window>`` source -> ``config.historical_feed``; everything else -> ``"sim"``.
    No hardcoded ``"iex"``/``"sip"`` literal — the single-config-value upgrade clause (J-67)."""
    if scenario.startswith("live "):
        return config.live_feed
    if scenario.startswith("historical "):
        return config.historical_feed
    return "sim"
