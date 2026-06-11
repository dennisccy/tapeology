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

# --- Thesis status / resolution enum (J-51; data-contract row 24) --------------------------------
# The SINGLE backend owner of the thesis lifecycle-status display copy — the journal table renders
# these VERBATIM (the frontend hardcodes none of them). ``active`` is the only non-terminal status;
# the other four are RESOLUTIONS (terminal statuses). Design direction: invalidated/expired carry the
# terminal-red treatment, played_out/abandoned the resolved treatment, active the live treatment —
# the frontend maps the COLOR from the id (a visual concern), but the LABEL text comes from here.
STATUSES: dict[str, str] = {
    "active": "Active",
    "played_out": "Played out",
    "abandoned": "Abandoned",
    "invalidated": "Invalidated",
    "expired": "Expired",
}

# The terminal statuses that count as RESOLUTIONS (a resolution IS a terminal status). Surfaced as its
# own enum so the journal filter's resolution control is taxonomy-driven (not a hardcoded list).
RESOLUTIONS: tuple[str, ...] = ("played_out", "abandoned", "invalidated", "expired")


# --- Monitor-status enum + lifecycle display copy (capability 24, J-47; data-contract row 24) ----
# The research monitor's status, owned ONCE on the backend and read VERBATIM by the strip:
#   ok            — the thesis is being watched and judged live.
#   failed        — the monitor or its store write errored (surfaced honestly, never hidden).
#   not_evaluated — the thesis carries a real entry mark and SURVIVES a stop/restart as
#                   active-but-not-evaluated: it is not orphaned, but no verdict accrues while the
#                   matching source is not being watched. Re-watching the SAME source resumes it.
MONITOR_STATUSES: tuple[str, ...] = ("ok", "failed", "not_evaluated")

# The plain-language notice shown on a surviving entry-marked thesis while it is not being
# evaluated. Present-tense, descriptive, thesis-attributed (J-66) — never imperative/predictive.
NOT_EVALUATED_NOTICE = (
    "not currently evaluated — re-watch this source to resume"
)


def not_evaluated_notice(bound_source: str) -> str:
    """The backend-owned not-evaluated notice naming the thesis's bound source (row 24).

    Rendered VERBATIM by the strip — the frontend composes none of this copy. Naming the bound
    source makes the resume action concrete ("re-watch THIS source")."""
    return f"{NOT_EVALUATED_NOTICE} ({bound_source})"


def mismatched_source_notice(bound_source: str, watched_source: str) -> str:
    """The backend-owned notice when a DIFFERENT source is watched than the thesis was declared on.

    A thesis is bound to its source identity and is NEVER evaluated against a different source
    (source-honesty anti-goal). The notice names the declared (bound) source so the user knows
    which watch would resume it. Present-tense, descriptive (J-66)."""
    return (
        f"not evaluated against this source — your thesis is bound to {bound_source}, "
        f"not {watched_source}; re-watch {bound_source} to resume"
    )


# --- Chart-geometry labels (capability 25, J-48; data-contract row 24) ---------------------------
# The backend-owned plain-language labels the chart renders VERBATIM on the thesis geometry
# overlay — the frontend hardcodes NONE of them (one copy register, J-66). Present-tense,
# descriptive, never imperative/predictive ("Descriptive only — not trading advice" extends to the
# chart). The invalidation/level lines name what the user DECLARED; the verdict/entry/exit marker
# labels reuse the established verdict + action vocabulary.
GEOMETRY_INVALIDATION_LINE_LABEL = "Invalidation"
GEOMETRY_LEVEL_LINE_LABEL = "Level"

# Marker labels keyed by verdict (the verdict-transition markers reuse the VERDICTS display copy);
# the entry/exit marks and the first-confirmation marker carry their own descriptive labels.
GEOMETRY_ENTRY_MARK_LABEL = "Entry"
GEOMETRY_EXIT_MARK_LABEL = "Exit"
GEOMETRY_FIRST_CONFIRMATION_LABEL = "First confirmation"


def verdict_marker_label(verdict: str) -> str:
    """The chart label for a published verdict-transition marker — the VERDICTS display copy.

    Reuses the single verdict enum (``VERDICTS``) so the chart, the strip, and the timeline all read
    the same words. An unknown verdict falls back to its own raw key (never a fabricated label)."""
    return VERDICTS.get(verdict, verdict)


# --- Entry risk-flag catalog (capability 26, J-49; data-contract rows 17 & 24) -------------------
# The SINGLE backend owner of every risk-flag LABEL and its plain-language EVIDENCE copy — the
# frontend hardcodes NONE of it. Each flag is computed ONCE at declaration from the live engine
# snapshot + config (in ``monitor.compute_risk_flags``) and FROZEN on the thesis; the strip renders
# the label + the measured-evidence sentence VERBATIM as an amber advisory chip. Advisory, never
# blocking — a fired flag is a record of the entry MOMENT, never a live indicator.
#
# Copy discipline (J-66): present-tense, descriptive, MEASURED — it states what was true at
# declaration ("recent buy impact +0.44% exceeds the 0.20% chase threshold"), never imperative
# ("don't buy"), never predictive, never certain. The label is the short chip title; the evidence
# is the one-line measured margin built from the canonical engine values behind the flag.
RISK_FLAGS: dict[str, str] = {
    "before_warmup": "Declared before warm-up",
    "invalidation_too_tight": "Invalidation too tight",
    "chasing_entry": "Chasing an extended move",
    "wide_spread_illiquid": "Wide spread / illiquid",
    "low_trade_speed": "Low trade speed",
    "against_expected_tape": "Against the expected tape",
}


def is_valid_risk_flag(flag: str) -> bool:
    return flag in RISK_FLAGS


def risk_flag_label(flag: str) -> str:
    """The short chip title for a risk flag. An unknown key falls back to itself (never fabricated)."""
    return RISK_FLAGS.get(flag, flag)


def _pct(return_value: float) -> str:
    """Format an impact-as-return as a signed percent (e.g. 0.0044 -> ``+0.44%``) for evidence copy."""
    return f"{return_value * 100:+.2f}%"


def before_warmup_evidence(trade_count: int, warmup_min_events: int) -> str:
    return (
        f"declared after {trade_count} trades, below the {warmup_min_events}-trade warm-up the "
        f"classifier needs for a confident read"
    )


def invalidation_too_tight_evidence(
    distance: float, spread: float, multiple: float
) -> str:
    band = spread * multiple
    return (
        f"the invalidation sits {distance:.2f} from the last, inside the {band:.2f} band "
        f"({multiple:g}× the {spread:.2f} spread) where ordinary spread noise could trip it"
    )


def chasing_entry_evidence(impact_return: float, threshold: float, side: str) -> str:
    return (
        f"recent {side} impact {_pct(impact_return)} already exceeds the {_pct(threshold)} "
        f"chase threshold — the move has run before this entry"
    )


def wide_spread_illiquid_evidence(spread_metric: float, max_spread: float, unit: str) -> str:
    if unit == "bps":
        return (
            f"the average spread is {spread_metric:.1f} bps, wider than the "
            f"{max_spread:.1f} bps the classifier treats as stable"
        )
    return (
        f"the average spread is {spread_metric:.2f}, wider than the {max_spread:.2f} "
        f"the classifier treats as stable"
    )


def low_trade_speed_evidence(trade_speed: float, min_trade_speed: float) -> str:
    return (
        f"the tape is running at {trade_speed:.2f} trades/s, below the {min_trade_speed:.2f} "
        f"trades/s floor the classifier needs for a confident read"
    )


def against_expected_tape_evidence(tape_state: str, expected: list[str]) -> str:
    expected_copy = " or ".join(s.replace("_", " ") for s in expected) if expected else "its setup"
    state_copy = tape_state.replace("_", " ")
    return (
        f"the tape reads {state_copy} at declaration, not the {expected_copy} this setup expects"
    )


# --- Mistake-tag catalog (capability 29, J-54/J-56; data-contract row 24) ------------------------
# The SINGLE backend owner of every mistake-tag id + its display copy — the frontend hardcodes NONE
# of it (the review picker is taxonomy-driven). The full catalog per goal.md capability 29. The
# review SAVE flow (``POST …/review``) lands with J-57 (iter-14); this iteration only renders the
# machine SUGGESTED tags pre-selected + toggleable in a disabled-Save picker — the system never
# records a confirmed tag on its own.
#
# Copy discipline (J-66): each label is a short, neutral, descriptive phrase — never imperative, never
# a verdict on the user. ``moved_invalidation`` is annotated self-assessed because the system cannot
# observe a moved stop (the invalidation is frozen on the thesis); only the user can claim it.
# ``other`` REQUIRES a free-text note at save time (enforced in the J-57 save flow, not here).
MISTAKE_TAGS: dict[str, str] = {
    "chased": "Chased an extended move",
    "entered_before_confirmation": "Entered before confirmation",
    "ignored_rejection": "Ignored a rejection / held through the stop",
    "ignored_risk_flags": "Ignored entry risk flags",
    "moved_invalidation": "Moved the invalidation (self-assessed)",
    "no_clear_setup": "No clear setup",
    "wrong_setup_type": "Wrong setup type",
    "overstayed": "Overstayed the move",
    "other": "Other (note required)",
}

# Tags that REQUIRE a free-text note when saved (enforced in the J-57 review save flow, not here).
MISTAKE_TAGS_REQUIRING_NOTE: tuple[str, ...] = ("other",)

# The backend-owned check → suggested-mistake-tag mapping (capability 27, J-54). A FAILED execution
# check SUGGESTS exactly the catalog tag it grounds; the system suggests only — it never records a
# confirmed tag. A check with no clean catalog correspondence (e.g. ``cut_confirming_early`` — cutting
# a confirming thesis early is neither ``overstayed`` nor any other catalog tag) maps to NOTHING here
# (the user adds ``other`` + a note in the review flow). Every tag mapped to MUST exist in
# ``MISTAKE_TAGS`` (asserted by the taxonomy test).
CHECK_SUGGESTED_TAG: dict[str, str] = {
    "entered_before_confirmation": "entered_before_confirmation",
    "chased_entry": "chased",
    "exited_beyond_invalidation": "ignored_rejection",
}


def is_valid_mistake_tag(tag: str) -> bool:
    return tag in MISTAKE_TAGS


def mistake_tag_label(tag: str) -> str:
    """The display label for a mistake-tag id. An unknown key falls back to itself (never fabricated)."""
    return MISTAKE_TAGS.get(tag, tag)


def suggested_tag_for_check(check: str) -> str | None:
    """The backend-owned suggested mistake tag for a FAILED execution check, or ``None`` when the
    check has no clean catalog correspondence (the user then adds ``other`` + a note)."""
    return CHECK_SUGGESTED_TAG.get(check)


# --- Grade enums (capability 29, J-56; data-contract row 24) -------------------------------------
# The SINGLE backend owner of the outcome × process grade LABELS — the journal table + the detail
# quadrant render these VERBATIM (the frontend hardcodes none of them). Both axes are ENUM labels,
# NEVER a numeric score. Copy discipline (J-66): descriptive, factual, never a judgement on the user.
#
# OUTCOME — 1:1 from the resolution (capability 29): did the thesis hold, fail, or give no read?
OUTCOME_GRADES: dict[str, str] = {
    "thesis_held": "Thesis held",
    "thesis_failed": "Thesis failed",
    "no_read": "No read",
}
# PROCESS — a config-owned rule over the named checks (capability 29): was the execution clean,
# flagged (advisories the user declared into), or violated (the user's own checks flagged it)?
# Being invalidated is NEVER itself a process failure — that is reflected in the outcome, never here.
PROCESS_GRADES: dict[str, str] = {
    "clean": "Clean",
    "flagged": "Flagged",
    "violated": "Violated",
}


def outcome_grade_label(grade: str) -> str:
    """Display label for an outcome grade id. Unknown -> itself (never fabricated)."""
    return OUTCOME_GRADES.get(grade, grade)


def process_grade_label(grade: str) -> str:
    """Display label for a process grade id. Unknown -> itself (never fabricated)."""
    return PROCESS_GRADES.get(grade, grade)


# --- Statement-status enum (the monitor's live read of each expected-behaviour statement) -------
# met = the statement's premise is observed in the current engine read; not_yet = not observed yet
# (the honest default — no evidence is not a failure); violated = the engine read contradicts it.
# not_evaluated (J-55) = a FINAL status recorded at a terminal moment with NO live evaluation context
# (e.g. the restart-expiry sweep over an unwatched thesis): an explicit honest enum, never fabricated,
# never recomputed at read. It is a FINAL-status-only value — the monitor's LIVE read never emits it.
STATEMENT_STATUSES: tuple[str, ...] = ("not_yet", "met", "violated", "not_evaluated")

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
        # Thesis lifecycle statuses + the resolution subset (J-51) — the journal table + its filter
        # controls render these VERBATIM (the frontend hardcodes no status/resolution label).
        "statuses": [{"id": k, "name": v} for k, v in STATUSES.items()],
        "resolutions": [{"id": k, "name": STATUSES[k]} for k in RESOLUTIONS],
        "statement_statuses": list(STATEMENT_STATUSES),
        "monitor_statuses": list(MONITOR_STATUSES),
        # The outcome × process grade catalogs (capability 29, J-56) — id + display label, owned ONCE
        # here so the journal quadrant + rows are taxonomy-driven (the frontend hardcodes no grade
        # label). ENUM labels only — never a numeric score.
        "outcome_grades": [{"id": k, "name": v} for k, v in OUTCOME_GRADES.items()],
        "process_grades": [{"id": k, "name": v} for k, v in PROCESS_GRADES.items()],
        # The entry risk-flag catalog (capability 26, J-49) — id + display label, owned ONCE here so
        # the strip's amber chips are taxonomy-driven (the measured-evidence sentence travels frozen
        # on each thesis's ``risk_flags``, also built from this module's templates).
        "risk_flags": [{"id": k, "name": v} for k, v in RISK_FLAGS.items()],
        # The mistake-tag catalog (capability 29, J-54) — id + display label, owned ONCE here so the
        # review picker is taxonomy-driven (the frontend hardcodes no tag label). ``requires_note``
        # flags the tags that need a free-text note at save (enforced in the J-57 save flow).
        "mistake_tags": [
            {
                "id": k,
                "name": v,
                "requires_note": k in MISTAKE_TAGS_REQUIRING_NOTE,
            }
            for k, v in MISTAKE_TAGS.items()
        ],
        "disclaimer": "Descriptive only — not trading advice.",
    }
