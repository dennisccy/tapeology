"""The research taxonomy — the SINGLE backend owner of the feed-basis display labels.

``GET /research/taxonomy`` serves this verbatim. era-5D J-01 ("The Clean Slate" demolition
interlude) SLIMMED this module to its one surviving kept-surface consumer: the cockpit's and
``/structure``'s ``FeedBasisBadge`` component, which reads ``feed_basis.feeds[].{id,name}`` and
``feed_basis.live_disclosure`` verbatim to label the served ``data_feed`` (sim | iex | sip | yahoo).
Every other label family this module used to own — verdict/thesis-status/monitor-status,
management-stance, entry-checklist, chart-geometry, risk-flag, mistake-tag, grade, excursion,
analytics, replay-study, setup-forming-hint, sound-cue, and thesis setup-catalog copy — was deleted
whole this iteration along with the journal/studies/performance product surfaces that were its only
readers (see ``docs/goal.md``'s I-2 taxonomy SLIM row).
"""

from __future__ import annotations

# --- Feed-basis display copy (capability 28 honesty stamps, J-67; data-contract row 24 additive) --
# The SINGLE backend owner of the per-feed badge labels and the live IEX-vs-SIP disclosure line. The
# cockpit feed-basis badge renders the served ``data_feed`` (sim | iex | sip) VERBATIM with these
# labels; on the live IEX basis the disclosure line renders beside it. The frontend hardcodes none of
# it. The served basis VALUE comes from the ONE config-aligned mapping (``feed_basis`` module / row
# 29) — this block is only the DISPLAY copy. Descriptive, present-tense, never imperative/predictive
# (J-66). The disclosure string is VERBATIM from goal.md (J-67's acceptance copy).
#
# Era-5 J-05 additive entry: ``"yahoo"`` — the keyless Yahoo Finance bar-fetch feed stamped by
# ``YahooAdapter``/``BarStore`` (era-5 J-01). The `/structure` fetch-control's provenance badge reads
# this label VERBATIM via ``GET /research/taxonomy`` (the SAME ``FeedBasisBadge`` component the
# cockpit uses) — the frontend hardcodes no "Yahoo Finance" string anywhere.
FEED_BASIS_LABELS: dict[str, str] = {
    "sim": "Simulated",
    "iex": "IEX (live)",
    "sip": "SIP (consolidated)",
    "yahoo": "Yahoo Finance",
}
FEED_BASIS_LIVE_DISCLOSURE: str = (
    "live verdicts read the single-venue IEX feed; historical replay and studies use SIP "
    "— spreads and prints differ"
)


def taxonomy_payload() -> dict:
    """The full ``GET /research/taxonomy`` body — just the feed-basis label block (era-5D J-01
    slimmed this to the one surviving kept-surface reader, ``FeedBasisBadge.tsx``).

    The frontend hardcodes none of it. This block doubles as the code-identity canary — ``GET
    /research/taxonomy`` carrying ``feed_basis`` proves the running server code is live."""
    return {
        "feed_basis": {
            "feeds": [{"id": k, "name": v} for k, v in FEED_BASIS_LABELS.items()],
            "live_disclosure": FEED_BASIS_LIVE_DISCLOSURE,
        },
    }
