"""The research taxonomy — the SINGLE backend owner of every research label (capability 24).

``GET /research/taxonomy`` serves this verbatim; the frontend hardcodes NONE of it (setup names,
direction/verdict display copy, the per-setup level requirement, and the expected-behaviour
statement templates all come from here). Centralizing the catalog here is what lets the declare
form be fully taxonomy-driven and keeps copy discipline (J-66: thesis-attributed, present-tense,
descriptive — never imperative/predictive/certain) enforced in ONE place.

This iteration the verdict stays ``pending`` for every thesis (the verdict-transition engine is
next iteration), so the verdict enum here carries display copy only; nothing here evaluates a
verdict. The expected-behaviour statement templates ARE evaluated live by the monitor against the
existing engine states/features (statuses ``met | not_yet | violated``) — they compose EXISTING
signals only, never a new indicator.
"""

from __future__ import annotations

# --- Direction enum -----------------------------------------------------------------------------
DIRECTIONS: dict[str, str] = {
    "long": "Long",
    "short": "Short",
}

# --- Verdict enum (display copy only this iteration; the transition engine is next) -------------
# Per the design direction: pending = slate; confirming green; weakening amber; rejecting /
# invalidated red. Only ``pending`` is ever published this iteration.
VERDICTS: dict[str, str] = {
    "pending": "Pending",
    "confirming": "Confirming",
    "weakening": "Weakening",
    "rejecting": "Rejecting",
    "invalidated": "Invalidated",
    "expired": "Expired",
}

# --- Statement-status enum (the monitor's live read of each expected-behaviour statement) -------
# met = the statement's premise is observed in the current engine read; not_yet = not observed yet
# (the honest default — no evidence is not a failure); violated = the engine read contradicts it.
STATEMENT_STATUSES: tuple[str, ...] = ("not_yet", "met", "violated")

# --- Statement kind keys (machine handles the monitor maps to the engine read) ------------------
# Each expected-behaviour statement carries a ``kind`` so the monitor can evaluate it from EXISTING
# engine states/features (no per-setup branching on free text). Kinds compose existing signals only.
#   tape_state_is        — the engine tape_state matches one of the statement's ``states``.
#   directional_impact   — price impact on the thesis direction is present (sign per direction).
#   above_invalidation   — last is on the correct side of the declared invalidation price.
STATEMENT_KINDS: tuple[str, ...] = (
    "tape_state_is",
    "directional_impact",
    "above_invalidation",
)


def _statement(text: str, kind: str, **params: object) -> dict:
    """One frozen expected-behaviour statement template (text + a machine-evaluable kind)."""
    return {"text": text, "kind": kind, "params": params}


# --- Setup catalog --------------------------------------------------------------------------------
# Each setup: display name, whether a level price is REQUIRED (the two level setups) or FORBIDDEN
# (the others), and its expected-behaviour statement templates (frozen on the thesis at creation,
# then evaluated live by the monitor). Statements are direction-aware in the monitor — the templates
# describe the LONG reading; the monitor mirrors the sign/side for SHORT. Copy is descriptive and
# thesis-attributed (J-66), never imperative or predictive.
#
# ``requires_level`` is the single authority for the 422 rules in POST /research/thesis:
#   level REQUIRED for level_break + failed_move_fade; FORBIDDEN for the other two.
SETUPS: dict[str, dict] = {
    "absorption_reversal": {
        "name": "Absorption reversal",
        "requires_level": False,
        "statements": [
            _statement(
                "Aggression into the level is being absorbed — price holds rather than following.",
                "tape_state_is",
                states_long=["bid_absorption"],
                states_short=["ask_absorption"],
            ),
            _statement(
                "The tape then flips to control on your side, lifting price off the absorbed level.",
                "tape_state_is",
                states_long=["buyer_control"],
                states_short=["seller_control"],
            ),
        ],
    },
    "trend_continuation": {
        "name": "Trend continuation",
        "requires_level": False,
        "statements": [
            _statement(
                "Control on your side is sustained, with price impact in your direction.",
                "tape_state_is",
                states_long=["buyer_control"],
                states_short=["seller_control"],
            ),
            _statement(
                "Price keeps making progress in your direction rather than stalling.",
                "directional_impact",
            ),
        ],
    },
    "level_break": {
        "name": "Level break-and-go",
        "requires_level": True,
        "statements": [
            _statement(
                "Price breaks the declared level and control holds on your side after the break.",
                "tape_state_is",
                states_long=["buyer_control"],
                states_short=["seller_control"],
            ),
            _statement(
                "Price stays beyond the level rather than falling back through it.",
                "above_invalidation",
            ),
        ],
    },
    "failed_move_fade": {
        "name": "Failed-move fade",
        "requires_level": True,
        # goal.md J-46 side mapping (iter-6 fix): a LONG fmf fades a failed DOWNSIDE break absorbed at
        # the BID (``bid_absorption``); a SHORT fmf fades a failed UPSIDE break absorbed at the ASK
        # (``ask_absorption``). Statement 2 then expects control turning to YOUR side
        # (long => buyer_control; short => seller_control). The prior templates had both inverted —
        # statement 1 ask_absorption-for-long and statement 2 seller_control-for-long (the latter
        # contradicting even the verdict engine's own control branch) — goal.md wins.
        "statements": [
            _statement(
                "A push beyond the level fails to find control and is absorbed back toward it.",
                "tape_state_is",
                states_long=["bid_absorption"],
                states_short=["ask_absorption"],
            ),
            _statement(
                "Control then turns to your side as the failed move fades back from the level.",
                "tape_state_is",
                states_long=["buyer_control"],
                states_short=["seller_control"],
            ),
        ],
    },
}


def setup_requires_level(setup_type: str) -> bool:
    """Whether ``setup_type`` REQUIRES a level price (the two level setups). KeyError-safe callers
    should validate the enum first; this raises KeyError for an unknown setup (caller maps to 422)."""
    return SETUPS[setup_type]["requires_level"]


def is_valid_setup(setup_type: str) -> bool:
    return setup_type in SETUPS


def is_valid_direction(direction: str) -> bool:
    return direction in DIRECTIONS


def frozen_statements(setup_type: str, direction: str) -> list[dict]:
    """Derive the frozen expected-behaviour statements for a thesis at CREATION time.

    Resolves each template to its direction-specific reading (the LONG/SHORT ``states_*`` pair
    collapses to one ``states`` list; direction-neutral kinds pass through) so the stored statement
    is fully concrete and never re-derived at read time (the frozen-statements anti-goal). Returns a
    list of ``{text, kind, params}`` dicts to persist verbatim on the thesis.
    """
    resolved: list[dict] = []
    for tmpl in SETUPS[setup_type]["statements"]:
        params = dict(tmpl["params"])
        if "states_long" in params or "states_short" in params:
            key = "states_long" if direction == "long" else "states_short"
            params = {"states": list(params[key])}
        resolved.append({"text": tmpl["text"], "kind": tmpl["kind"], "params": params})
    return resolved


def taxonomy_payload() -> dict:
    """The full ``GET /research/taxonomy`` body — setups (with name + level requirement + statement
    templates), direction enum, verdict enum, and the statement-status enum, all with display copy.

    The frontend reads this to build the declare form (which setups exist, their display names, and
    whether each needs a level field) and to label the active-thesis display — it hardcodes none of
    it. The "Descriptive only — not trading advice" discipline note travels with the payload so the
    one copy register lives on the backend (J-66)."""
    return {
        "setups": [
            {
                "id": setup_id,
                "name": spec["name"],
                "requires_level": spec["requires_level"],
                "statements": [
                    {"text": s["text"], "kind": s["kind"]} for s in spec["statements"]
                ],
            }
            for setup_id, spec in SETUPS.items()
        ],
        "directions": [{"id": k, "name": v} for k, v in DIRECTIONS.items()],
        "verdicts": [{"id": k, "name": v} for k, v in VERDICTS.items()],
        "statement_statuses": list(STATEMENT_STATUSES),
        "disclaimer": "Descriptive only — not trading advice.",
    }
