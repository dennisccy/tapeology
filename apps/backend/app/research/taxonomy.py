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

# --- Feed-basis display copy (capability 28 honesty stamps, J-67; data-contract row 24 additive) --
# The SINGLE backend owner of the per-feed badge labels and the live IEX-vs-SIP disclosure line. The
# cockpit feed-basis badge renders the served ``data_feed`` (sim | iex | sip) VERBATIM with these
# labels; on the live IEX basis the disclosure line renders beside it. The frontend hardcodes none of
# it. The served basis VALUE comes from the ONE config-aligned mapping (``feed_basis`` module / row
# 29) — this block is only the DISPLAY copy. Descriptive, present-tense, never imperative/predictive
# (J-66). The disclosure string is VERBATIM from goal.md (J-67's acceptance copy).
FEED_BASIS_LABELS: dict[str, str] = {
    "sim": "Simulated",
    "iex": "IEX (live)",
    "sip": "SIP (consolidated)",
}
FEED_BASIS_LIVE_DISCLOSURE: str = (
    "live verdicts read the single-venue IEX feed; historical replay and studies use SIP "
    "— spreads and prints differ"
)

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


# --- Management-stance enum + display copy (capability 27, J-53; data-contract rows 24 & 25) ------
# The SINGLE backend owner of the holding-period management stance — the stance the thesis strip shows
# while a thesis is ENTRY-MARKED and UNRESOLVED, answering "does the tape still support this position?".
# The frontend hardcodes NONE of this copy (it reads the label + evidence verbatim off the projection).
#
# The stance is a pure DERIVATION from the latest row-16 PUBLISHED verdict (stance.py owns the timing
# + dwell; this module owns the verdict->stance MAP and every display string). Three values only —
# the established verdict/stance palette (design direction): ``thesis_intact`` emerald,
# ``thesis_weakening`` amber, ``thesis_invalidated`` rose with the terminal treatment. Copy is
# present-tense, factual, thesis-attributed (J-66 / anti-goals) — never imperative, never predictive.
MANAGEMENT_STANCES: dict[str, str] = {
    "thesis_intact": "Thesis intact",
    "thesis_weakening": "Thesis weakening",
    "thesis_invalidated": "Thesis invalidated",
}

# The verdict -> management-stance MAP (the backend-owned table the spec mandates). The full
# five-verdict mapping, with ONE home:
#   * ``confirming``  -> ``thesis_intact``      (the tape published a confirmation; the position holds);
#   * ``weakening``   -> ``thesis_weakening``   (the confirming evidence faded);
#   * ``rejecting``   -> ``thesis_weakening``   (the opposite side took control — the position is under
#                                                pressure, not yet system-invalidated);
#   * ``pending``     -> ``thesis_weakening``   (the HONEST J-54 case: an entry while the verdict is
#                                                still pending NEVER reads ``thesis_intact`` — no
#                                                published confirmation backs it; its evidence names
#                                                the actual verdict via ``STANCE_PENDING_EVIDENCE``);
#   * ``invalidated`` -> ``thesis_invalidated`` (the J-44 system auto-resolve — terminal, dwell-exempt).
# Kept here (not inline in stance.py) so the verdict->stance mapping + its copy share ONE owner.
_VERDICT_TO_STANCE: dict[str, str] = {
    "confirming": "thesis_intact",
    "weakening": "thesis_weakening",
    "rejecting": "thesis_weakening",
    "pending": "thesis_weakening",
    "invalidated": "thesis_invalidated",
}

# The honest "entry while not confirmed" evidence (the J-54 case): an entry marked while the verdict is
# pending (or carrying no published evidence yet) reads as NOT-confirmed — never ``thesis_intact``,
# never a fabricated weakening-from-confirmation. Present-tense, factual, thesis-attributed.
STANCE_PENDING_EVIDENCE = (
    "The tape has not published a confirmation of your thesis since you marked entry — the position "
    "is open without a confirming read."
)

# The two DISTINCT honest-absence copies (iter-15 lesson: one fallback string must not cover two
# causes). They name WHY no management stance is shown — these are causally different states:
#   * NO_ENTRY_MARK   — the thesis is live and evaluating, but the user has not marked an entry, so
#                       there is no position to manage (the verdict view stands on its own).
#   * NOT_EVALUATED   — the thesis carries a real entry mark but its watch is not evaluating (the
#                       surviving not-evaluated / mismatched-source path) — no live tape to read a
#                       stance from, and deliberately NO frozen-stale stance.
STANCE_ABSENCE_NO_ENTRY_MARK = (
    "No entry is marked on this thesis, so there is no held position to read a management stance for "
    "yet — mark your entry to see whether the tape still supports it."
)
STANCE_ABSENCE_NOT_EVALUATED = (
    "This thesis is not being evaluated right now, so no live management stance is read — re-watch its "
    "source to resume; no stale stance is shown."
)

# The journaled-measurement register for the live position readouts (consistent with the realized-R
# label discipline) — the distance-to-invalidation + open-R caption. R-units only, never currency,
# never a prediction. The "Descriptive only — not trading advice" register extends to the stance block.
STANCE_READOUT_CAPTION = "journaled measurement, R = |entry − invalidation|"


# --- Entry-checklist enums + display copy (capability 33, J-63; data-contract rows 24 & 25) --------
# The SINGLE backend owner of EVERY entry-checklist string — the strip's pre-entry-mark cue block.
# The frontend hardcodes NONE of it (it reads each check's label + the rendered margin VERBATIM off the
# projection, and the stance/nearest-counterevidence copy from here). At the moment of decision (an
# active, evaluated, not-yet-entry-marked thesis) the checklist answers, check by check with a LIVE
# MEASURED MARGIN, whether the tape currently meets the entry conditions — never a naked signal.
#
# Copy discipline (J-66 / anti-goals): present-tense, FACTUAL, descriptive — never imperative
# ("buy / enter"), never predictive (no price target, no forecast), never certain. A check DESCRIBES a
# measured condition; the aggregate stance DESCRIBES what the tape is doing NOW relative to the thesis.

# The eight named checks, in display order. Each LABEL is a short, neutral noun phrase naming the
# condition (NOT a command). The eight compose ONLY existing canonical engine values (the spec's row-25
# checklist half) — no new indicator. Owned ONCE here so the strip is fully taxonomy-driven.
CHECKLIST_CHECKS: dict[str, str] = {
    "verdict_confirming": "Verdict confirming",
    "warm": "Classifier warm",
    "feed_live": "Feed live",
    "tape_lag_ok": "Tape delivery current",
    "spread_stable": "Spread within stability",
    "trade_speed_ok": "Trade speed at floor",
    "invalidation_distance_ok": "Invalidation clear of spread",
    "not_chasing": "Entry not chasing",
}

# The PER-CHECK margin CAPTION — a short unit note rendered beside each check's measured margin so the
# user reads the margin in its OWN units (the spec: "live measured margin in its own units, never a
# bare boolean"). Descriptive only. The numeric margin itself is computed server-side and rendered
# verbatim by the strip; this caption only NAMES the unit/comparison.
CHECKLIST_CHECK_CAPTIONS: dict[str, str] = {
    "verdict_confirming": "the published verdict against your thesis",
    "warm": "events processed vs the classifier's warm-up floor",
    "feed_live": "the canonical stream status",
    "tape_lag_ok": "delivery lag (s) vs the freshness bound",
    "spread_stable": "average spread (bps) vs the stability cap",
    "trade_speed_ok": "trade speed (trades/s) vs the floor",
    "invalidation_distance_ok": "distance to invalidation in spread-multiples vs the floor",
    "not_chasing": "move since the rule first held vs the chase threshold",
}

# The four aggregate STANCES — the entry checklist's read at the moment of decision. The established
# verdict/stance palette EXTENDED (design direction): ``conditions_met`` emerald, ``conditions_not_met``
# slate, ``tape_against`` rose, ``no_fresh_tape`` amber. The frontend maps COLOR from the id (a visual
# concern) but reads the LABEL text from here. Factual, present-tense, never imperative/predictive.
CHECKLIST_STANCES: dict[str, str] = {
    "conditions_met": "Conditions met",
    "conditions_not_met": "Conditions not met",
    "tape_against": "Tape against",
    "no_fresh_tape": "No fresh tape",
}


def checklist_check_label(check: str) -> str:
    """Display label for a checklist-check id. Unknown -> itself (never fabricated)."""
    return CHECKLIST_CHECKS.get(check, check)


def checklist_check_caption(check: str) -> str:
    """The per-check unit caption. Unknown -> empty (never fabricated)."""
    return CHECKLIST_CHECK_CAPTIONS.get(check, "")


def checklist_stance_label(stance: str) -> str:
    """Display label for a checklist-stance id. Unknown -> itself (never fabricated)."""
    return CHECKLIST_STANCES.get(stance, stance)


def checklist_stance_evidence(stance: str, passed: int, total: int) -> str:
    """The factual plain-language evidence for an aggregate checklist stance (no naked stance).

    Present-tense, descriptive, in the goal's "N/8 checks pass" register — NEVER imperative
    ("enter now"), NEVER predictive (no price/forecast), NEVER certain. Each stance names what the
    tape is doing NOW relative to the thesis's entry conditions:
      * ``conditions_met``     — every check passes after confirmation;
      * ``conditions_not_met`` — at least one check is unmet (the blocker list travels separately);
      * ``tape_against``       — the published verdict is rejecting the thesis;
      * ``no_fresh_tape``      — the feed is not live / the tape is not current, so the conditions
                                 cannot be read against fresh tape (a previous green never persists).
    """
    fraction = f"{passed}/{total} checks pass"
    if stance == "conditions_met":
        return (
            f"The tape currently meets every entry condition for your thesis — {fraction}."
        )
    if stance == "tape_against":
        return (
            "The published verdict is rejecting your thesis — the tape is currently working against "
            f"it ({fraction})."
        )
    if stance == "no_fresh_tape":
        return (
            "The feed is not delivering current tape, so the entry conditions cannot be read against "
            f"fresh data right now ({fraction})."
        )
    # conditions_not_met (and any unknown stance) — name the shortfall factually.
    return (
        f"The tape does not yet meet every entry condition for your thesis — {fraction}; the unmet "
        "checks are listed below."
    )


def checklist_nearest_counterevidence(check_label: str, margin: str, met: bool) -> str:
    """The nearest-counterevidence line (capability 33) — the closest condition that would FLIP the
    current read, with its margin, computed once server-side and rendered verbatim.

    When the conditions ARE met it names the passing check nearest its boundary (the first that would
    drop if the tape moves); when they are NOT met it names the nearest-to-passing blocker (the first
    that would clear). Descriptive, present-tense — it states which condition is closest to its line,
    never a forecast that it WILL cross. ``margin`` is the already-formatted margin string."""
    if met:
        return (
            f"Closest to flipping: {check_label} sits nearest its boundary at {margin}."
        )
    return (
        f"Nearest to passing: {check_label} at {margin}."
    )


# The checklist honest-absence copy — shown on the active-but-not-yet-checklist paths so the absence is
# never a silent blank. ONE distinct cause per string (the iter-15 lesson). The not-evaluated /
# no-entry-mark / mismatched-source absences are covered by the management-stance + monitor-notice copy
# already; THIS string covers the checklist's own "evaluating but no fresh tape to read" intermediate.
CHECKLIST_ABSENCE_NO_FRESH_TAPE = (
    "The feed is not delivering current tape, so the entry checklist is not read against fresh data "
    "right now — no stale checklist is shown."
)


def stance_for_verdict(verdict: str) -> str:
    """The management stance for a published verdict (the backend-owned map; J-53).

    An unknown/never-mapped verdict (e.g. ``expired`` — which never reaches the stance, the keys being
    absent then) falls back to ``thesis_weakening`` (the conservative NOT-intact reading — a stance is
    never ``thesis_intact`` without an explicit ``confirming`` verdict)."""
    return _VERDICT_TO_STANCE.get(verdict, "thesis_weakening")


def management_stance_label(stance: str) -> str:
    """Display label for a management-stance id. Unknown -> itself (never fabricated)."""
    return MANAGEMENT_STANCES.get(stance, stance)


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


# --- Excursion-outcome enums + display copy (capability 30, J-58; data-contract row 24) ----------
# The SINGLE backend owner of the excursion display copy — the journal detail's two excursion blocks
# render these VERBATIM (the frontend hardcodes none of them). R-units only, never currency, never a
# prediction (the copy register is descriptive, past-tense). The two POPULATIONS are segregated and
# never pooled; their titles + caption copy live here so the frontend never re-words them.
EXCURSION_TERNARY_OUTCOMES: dict[str, str] = {
    "+1R_first": "+1R first",
    "-1R_first": "−1R first",
    "neither_within_horizon": "Neither within horizon",
}
# The TRUNCATED flag (a horizon the stream end / a gap cut short before its outcome could resolve).
EXCURSION_TRUNCATED_LABEL: str = "Truncated"
# The two excursion POPULATION titles (capability 30) — distinct anchors, never pooled.
EXCURSION_POPULATIONS: dict[str, str] = {
    "confirmation": "From first confirmation",
    "entry": "From entry mark",
}
# Honest-absence copy: each block reads its explicit not-applicable when its anchor never existed
# (never-confirmed => no confirmation population; no entry mark => no entry population). The
# ``not_tracked`` copy is the restart-sweep marker (no in-memory price path to measure from).
EXCURSION_NOT_APPLICABLE_COPY: dict[str, str] = {
    "confirmation": (
        "This thesis never published a confirming verdict, so there is no first-confirmation "
        "anchor to measure excursions from."
    ),
    "entry": (
        "No entry was recorded for this thesis, so there is no entry anchor to measure excursions "
        "from — no mark, no metric."
    ),
}
EXCURSION_NOT_TRACKED_COPY: str = (
    "Excursions were not tracked for this thesis — it resolved on a restart sweep with no live tape "
    "to measure against, so no numbers are shown rather than fabricated ones."
)
# The per-block caption naming the R basis + spread cost (the no-cost caveat is always one line away).
EXCURSION_R_BASIS_CAPTION: str = "R = |reference − invalidation|"


# --- Segregated journal analytics display copy (capability 31, J-59) -----------------------------
# Owned ONCE here so the analytics view on /journal is taxonomy-driven (the frontend hardcodes no
# label / caption / framing). Descriptive, R-units, NEVER a profitability/edge/win-rate claim — the
# framing line is the honesty caveat the spec mandates beside every figure. Copy register matches the
# existing research strings: thesis-attributed, present-tense, descriptive (J-66 / anti-goals).
ANALYTICS_COPY: dict[str, str] = {
    # The view title + the one-line framing the anti-goals require (journaled measurements, never edge).
    "title": "Analytics",
    "measurement_framing": (
        "These are journaled measurements of your own recorded theses — not a profitability claim, "
        "an edge, a win rate, or a forecast. Every figure shows its n; abandoned theses stay in the "
        "count; results are never pooled across data feeds or config fingerprints."
    ),
    # Partition + group section labels (a partition is one feed × fingerprint; a group is setup × dir).
    "partition_title": "Data feed × config fingerprint",
    "data_feed_label": "Feed",
    "fingerprint_label": "Config fingerprint",
    "group_title": "Setup × direction",
    # The always-visible counts.
    "n_label": "n",
    "abandonment_label": "Abandoned (kept in n)",
    # The insufficient-sample gate (shown WITH its n — never a bare percentage on a thin pool).
    "insufficient_sample_label": "Insufficient sample",
    "insufficient_sample_caption": (
        "Below the minimum sample size — n is shown, but distributions are withheld rather than read "
        "as a measurement from too few theses."
    ),
    # The confirmation-anchored excursion block (reuses the excursion population title + truncated flag).
    "confirmation_excursions_title": "From first confirmation — per-horizon outcomes (R)",
    "horizon_label": "Horizon",
    "truncated_label": EXCURSION_TRUNCATED_LABEL,
    "truncated_caption": (
        "Horizons the stream end or a gap cut short before +1R or −1R could resolve — counted "
        "separately, never folded into the resolved outcomes, never extrapolated."
    ),
    # Median spread / R sits beside every +1R figure (the no-cost caveat as a number).
    "spread_per_r_caption": "median spread / R",
    # Median time-to-confirm (logical seconds; honestly omitted when a group has no confirmation).
    "time_to_confirm_label": "Median time to confirm",
    "time_to_confirm_unit": "s (logical)",
    "time_to_confirm_absent": "No confirmation recorded in this group.",
    # User-confirmed mistake-tag frequencies (machine suggestions are never counted).
    "tag_frequencies_title": "Mistake tags (your confirmed reviews)",
    "tag_frequencies_absent": "No confirmed review tags in this group yet.",
    # The acted-trade block — STRUCTURALLY SEPARATE from the confirmation-anchored stats.
    "acted_trade_title": "Acted trades — realized move (R)",
    "acted_trade_caption": (
        "Entry-and-exit-marked theses only, kept apart from the confirmation-anchored figures above. "
        "Realized move in R units, never currency, never a profit/loss claim."
    ),
    "median_realized_r_label": "Median realized R",
    "acted_trade_absent": "No acted (entry-and-exit-marked) trades in this group.",
    # The honest empty state (no records at all in the journal).
    "empty": "No theses recorded yet — declare and resolve a thesis to populate the analytics.",
}


# --- Replay-studies display copy (capability 32, J-60/J-61/J-62) ---------------------------------
# Owned ONCE here so the /studies page is taxonomy-driven (the frontend hardcodes no label / caption /
# framing). This is the MOST edge-claim-prone surface in the product (the J-66 sweep will audit it),
# so every string is written CLEAN now: descriptive, present-tense, measurement-framed — n + caveats
# always visible, NEVER "edge" / "win rate" as advice, NEVER imperative, NEVER predictive. The
# side-by-side null baseline is the honesty mechanism: a setup distribution is only meaningful BESIDE
# the random-arm-time control over the same window.

# STUDY STATUS LABELS — each status its OWN explicit label (iter-15 lesson: one absence-fallback copy
# string must NOT serve two distinct states). The frontend renders these verbatim; the status COLOR
# semantics (slate for queued/cancelled, amber for running/partial, slate-green-FREE for done so it
# never reads as an "edge win", rose for failed) live in the frontend's design tokens, not here.
STUDY_STATUSES: dict[str, str] = {
    "queued": "Queued",
    "running": "Running",
    "done": "Done",
    "cancelled": "Cancelled",
    "failed": "Failed",
}

# PER-STATUS HONEST-ABSENCE COPY — each status gets its OWN explicit sentence for the results area when
# there is nothing (yet) to show (iter-15 lesson: each state distinct, never a shared fallback). These
# describe what the study IS doing / DID, never a result that does not exist.
STUDY_STATUS_ABSENCE_COPY: dict[str, str] = {
    "queued": "This study is queued — it has not started replaying yet, so there are no results to show.",
    "running": (
        "This study is replaying its window now — results appear once the replay finishes. Nothing is "
        "shown mid-run rather than a partial number that could be misread."
    ),
    "cancelled": (
        "This study was cancelled before it finished. Any occurrences shown below are PARTIAL — they "
        "cover only the part of the window that replayed, and are not a complete measurement."
    ),
    "failed": (
        "This study could not produce a result (no data, an unavailable provider, or an empty window). "
        "The explicit reason is shown — never an empty or fabricated success."
    ),
}

STUDY_COPY: dict[str, str] = {
    # The page title + the one-line framing the anti-goals require beside every figure.
    "title": "Replay studies",
    "intro": (
        "Run your setup grammar over a chosen past window and read the occurrence outcomes side-by-side "
        "with a seeded random-arm-time baseline — so you can see whether the setup measurably differs "
        "from arming at random over the same window, before trusting any live cue."
    ),
    "measurement_framing": (
        "These are journaled MEASUREMENTS of a replay over recorded data — not a profitability claim, "
        "an edge, a win rate, or a forecast. Every distribution shows its n beside the random-arm-time "
        "baseline; truncated horizons are counted separately; results are stamped with their data feed "
        "and config fingerprint and are never pooled across either."
    ),
    # The create form.
    "create_title": "New study",
    "source_label": "Source",
    "reference_source_label": "Reference window (committed PG SIP fixture — no credentials)",
    "sim_source_label": "Seeded sim scenario",
    "historical_source_label": "Symbol + past window",
    "setup_label": "Setup",
    "direction_label": "Direction",
    "level_label": "Level price (required for level setups)",
    "create_button": "Run study",
    # The hindsight-level label + caption (a level study is illustrative + excluded from aggregates).
    "hindsight_level_label": "Level chosen with hindsight",
    "hindsight_level_caption": (
        "This level setup used a level you supplied with full knowledge of the window — it is "
        "illustrative only and is excluded from any cross-study comparison."
    ),
    # The job list.
    "jobs_title": "Studies",
    "jobs_empty": "No studies yet — create one above to run your setup grammar over a chosen window.",
    "cancel_button": "Cancel",
    "progress_label": "events processed",
    # The results view.
    "results_title": "Results",
    "occurrences_title": "Occurrences",
    "occurrence_arm_label": "Arm time (logical s)",
    "occurrence_verdict_label": "Verdict reached",
    "occurrence_r_label": "R basis",
    "setup_distribution_label": "Your setup",
    "null_baseline_label": "Random-time baseline",
    "null_baseline_caption": (
        "The same window, direction, R definition, and horizons — but arm times drawn at random from a "
        "recorded seed, so the setup distribution is read against an honest control, not in isolation."
    ),
    "seed_label": "Baseline seed",
    "n_label": "n",
    "horizon_label": "Horizon",
    "truncated_label": EXCURSION_TRUNCATED_LABEL,
    "truncated_caption": (
        "Horizons the window end cut short before +1R or −1R could resolve — counted separately, never "
        "folded into the resolved outcomes, never extrapolated."
    ),
    "feed_label": "Feed",
    "fingerprint_label": "Config fingerprint",
    "insufficient_sample_label": "Insufficient sample",
    "insufficient_sample_caption": (
        "Below the minimum sample size — n is shown, but the distribution is read with care rather than "
        "as a measurement from too few occurrences."
    ),
    "rerun_button": "Re-run identical",
    # The R-definition note (the named occurrence-R design decision, surfaced honestly to the user).
    "occurrence_r_caption": (
        "An auto-armed occurrence has no typed invalidation, so its R is a config-owned synthetic "
        "distance from the arm price (a spread multiple on the adverse side) — the same definition for "
        "your setup and the random-time baseline. R = |arm price − synthetic invalidation|."
    ),
}


# --- Setup-forming hints display copy (capability 33, J-65) --------------------------------------
# Owned ONCE here so the cockpit's hint dock + the /journal hint log are taxonomy-driven (the frontend
# hardcodes NO pattern label, evidence template, citation string, dock title, register line, declared-
# from label, log column, or empty-state copy). This is a cue surface, so the copy discipline is at its
# strictest (the J-66 sweep audits it next): every string is DESCRIPTIVE and PRESENT-TENSE — a hint
# DESCRIBES a forming pattern on the tape NOW, it is NEVER an imperative (no buy/sell/enter/exit), NEVER
# a prediction (no "will"/"about to"/price target), NEVER a certainty/edge claim, and NEVER a thesis by
# itself. The pattern→setup mapping below composes ONLY the EXISTING engine tape states (no new
# indicator): sustained absorption arms an absorption_reversal context; sustained control arms a
# trend_continuation context (the state-native arming the goal's capability 33 names).

# The four state-native hint patterns. Each maps a SUSTAINED existing tape state to a setup-type context
# + direction (the declaration the dock prefills). ``unclear`` is deliberately absent — it never produces
# a hint; the two level setups have no state-native arming, so they never produce hints either.
HINT_PATTERNS: dict[str, dict] = {
    "sustained_bid_absorption": {
        "name": "Bid absorption forming",
        "tape_state": "bid_absorption",
        "setup_type": "absorption_reversal",
        "direction": "long",
    },
    "sustained_ask_absorption": {
        "name": "Ask absorption forming",
        "tape_state": "ask_absorption",
        "setup_type": "absorption_reversal",
        "direction": "short",
    },
    "sustained_buyer_control": {
        "name": "Buyer control forming",
        "tape_state": "buyer_control",
        "setup_type": "trend_continuation",
        "direction": "long",
    },
    "sustained_seller_control": {
        "name": "Seller control forming",
        "tape_state": "seller_control",
        "setup_type": "trend_continuation",
        "direction": "short",
    },
}

# The exact honest-absence citation string the spec mandates VERBATIM (a hint with no matching studied
# baseline for its setup/feed/fingerprint). One canonical string, owned here, rendered verbatim.
HINT_BASELINE_UNVALIDATED: str = "no studied baseline — unvalidated pattern"

HINT_COPY: dict[str, str] = {
    # The dock title + the register line the cue-discipline mandates beside every hint (the cockpit's
    # existing "Descriptive only — not trading advice" discipline, extended verbatim to the hint dock).
    "dock_title": "Setup forming",
    "dock_register": "Descriptive only — not trading advice.",
    # The declare affordance label (one click PREFILLS the declare form — it never creates a thesis).
    "declare_label": "Prefill a thesis from this hint",
    "declare_caption": (
        "Prefills the setup and direction on the declare form — you still type the invalidation price "
        "yourself. One click never creates a thesis."
    ),
    # The declared-from label (shown on the hint-log row once the user completed a declaration from it).
    "declared_from_label": "Declared from this hint",
    # The hint-log view title + its honest empty-state copy.
    "log_title": "Hints",
    "log_empty": (
        "No hints logged yet — a setup-forming hint is recorded here each time a sustained pattern "
        "is described on a watched ticker."
    ),
}

# The hint-log column labels — the /journal hint-log table renders these verbatim (no hardcoded header).
HINT_LOG_COLUMNS: dict[str, str] = {
    "time": "Time",
    "ticker": "Ticker",
    "pattern": "Pattern",
    # The stored ``data_feed`` stamp column (J-67, additive): the persisted per-row feed basis is
    # displayed VERBATIM (labels from the FEED_BASIS_LABELS block) — closing the one confirmed
    # hint-log display gap. Read, never recomputed.
    "feed": "Feed",
    "evidence": "Evidence",
    "baseline": "Studied baseline",
    "declared_from": "Declared from",
}


def hint_pattern_label(pattern_id: str) -> str:
    """Display label for a hint pattern id. Unknown -> humanised (never fabricated)."""
    spec = HINT_PATTERNS.get(pattern_id)
    return spec["name"] if spec is not None else pattern_id.replace("_", " ")


def hint_evidence(pattern_id: str, sustained_seconds: float) -> str:
    """The plain-language, PRESENT-TENSE evidence for a fired hint, carrying the measured sustain
    duration (capability 33 / no-naked-outputs). DESCRIPTIVE only — it states what the tape IS doing
    now, never an imperative, never a prediction, never a price target or certainty/edge claim.

    The measured value (the logical seconds the premise state has sustained) grounds the description in
    a canonical engine fact, exactly the example the iter spec gives ("bid absorption sustained 45 s —
    sellers being absorbed at the bid")."""
    secs = int(round(sustained_seconds))
    bodies = {
        "sustained_bid_absorption": (
            f"Bid absorption is sustained {secs}s — aggressive selling is being absorbed at the bid "
            "with no meaningful downward price progress."
        ),
        "sustained_ask_absorption": (
            f"Ask absorption is sustained {secs}s — aggressive buying is being absorbed at the ask "
            "with no meaningful upward price progress."
        ),
        "sustained_buyer_control": (
            f"Buyer control is sustained {secs}s — aggressive buying is moving price higher with "
            "stable spread."
        ),
        "sustained_seller_control": (
            f"Seller control is sustained {secs}s — aggressive selling is moving price lower with "
            "stable spread."
        ),
    }
    return bodies.get(
        pattern_id,
        f"The {hint_pattern_label(pattern_id).lower()} pattern is sustained {secs}s on the tape.",
    )


def hint_baseline_citation(n: int, plus: int, minus: int, neither: int, horizon: int) -> str:
    """The baseline-citation sentence for a fired hint that HAS a matching studied baseline — cites the
    STORED study aggregates VERBATIM (n occurrences + the first-horizon ternary distribution vs the
    seeded null baseline is named on the study itself). DESCRIPTIVE measurement framing, never an edge
    or win-rate claim (J-66): it states what the user's OWN recorded studies measured, with n always
    shown. Reads the already-persisted aggregate numbers — NEVER recomputes anything at read."""
    return (
        f"Your studies of this setup on this feed: n={n} occurrences; over the {horizon}s horizon "
        f"{plus} reached +1R first, {minus} reached −1R first, {neither} neither — a journaled "
        "measurement of your own studies, not an edge claim."
    )


def study_status_label(status: str) -> str:
    """Display label for a study status id. Unknown -> humanised (never fabricated)."""
    return STUDY_STATUSES.get(status, status.replace("_", " "))


def excursion_outcome_label(outcome: str | None) -> str:
    """Display label for a ternary excursion outcome id. ``None`` (an open/undetermined horizon) and
    any unknown value fall back to a humanised form (never fabricated)."""
    if outcome is None:
        return "—"
    return EXCURSION_TERNARY_OUTCOMES.get(outcome, outcome.replace("_", " "))


def excursion_population_title(population: str) -> str:
    """Display title for an excursion population id. Unknown -> itself (never fabricated)."""
    return EXCURSION_POPULATIONS.get(population, population.replace("_", " "))


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
        # The feed-basis display copy (capability 28 honesty stamps, J-67; data-contract row 24
        # additive) — owned ONCE here so the cockpit feed-basis badge + the live disclosure line are
        # taxonomy-driven (the frontend hardcodes no feed label or disclosure text). The served basis
        # VALUE comes from the ONE config-aligned mapping (the ``feed_basis`` module / row 29); this
        # block is the DISPLAY copy only. This block doubles as iter-24's code-identity canary —
        # ``GET /research/taxonomy`` carrying ``feed_basis`` proves the NEW server code is live.
        "feed_basis": {
            "feeds": [{"id": k, "name": v} for k, v in FEED_BASIS_LABELS.items()],
            "live_disclosure": FEED_BASIS_LIVE_DISCLOSURE,
        },
        # Thesis lifecycle statuses + the resolution subset (J-51) — the journal table + its filter
        # controls render these VERBATIM (the frontend hardcodes no status/resolution label).
        "statuses": [{"id": k, "name": v} for k, v in STATUSES.items()],
        "resolutions": [{"id": k, "name": STATUSES[k]} for k in RESOLUTIONS],
        "statement_statuses": list(STATEMENT_STATUSES),
        "monitor_statuses": list(MONITOR_STATUSES),
        # The management-stance catalog (capability 27, J-53; row 25 stance half) — id + display label
        # for each of the three stances, the two DISTINCT honest-absence copies (iter-15 lesson), and
        # the journaled-measurement readout caption. Owned ONCE here so the strip's holding-period block
        # is taxonomy-driven (the frontend hardcodes none of it). Present-tense, factual, never
        # imperative or predictive (J-66). This block is also iter-20's code-identity canary —
        # ``GET /research/taxonomy`` carrying ``management_stances`` proves the NEW server code is live.
        "management_stances": [
            {"id": k, "name": v} for k, v in MANAGEMENT_STANCES.items()
        ],
        "stance_absence": {
            "no_entry_mark": STANCE_ABSENCE_NO_ENTRY_MARK,
            "not_evaluated": STANCE_ABSENCE_NOT_EVALUATED,
        },
        "stance_readout_caption": STANCE_READOUT_CAPTION,
        # The entry-checklist catalog (capability 33, J-63; row 25 checklist half) — the strip's
        # pre-entry-mark cue block is fully taxonomy-driven (the frontend hardcodes none of it). The
        # eight check labels + their per-check unit captions, the four aggregate-stance labels, and the
        # checklist honest-absence copy. The per-check MARGINS + the stance EVIDENCE + the
        # nearest-counterevidence line travel computed-once on each thesis projection (built from this
        # module's templates), never re-worded on the frontend. Present-tense, factual, never
        # imperative/predictive (J-66). This block doubles as iter-21's code-identity canary —
        # ``GET /research/taxonomy`` carrying ``checklist_checks`` proves the NEW server code is live.
        "checklist_checks": [
            {"id": k, "name": v, "caption": CHECKLIST_CHECK_CAPTIONS.get(k, "")}
            for k, v in CHECKLIST_CHECKS.items()
        ],
        "checklist_stances": [
            {"id": k, "name": v} for k, v in CHECKLIST_STANCES.items()
        ],
        "checklist_absence": {
            "no_fresh_tape": CHECKLIST_ABSENCE_NO_FRESH_TAPE,
        },
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
        # The excursion-outcome display copy (capability 30, J-58) — owned ONCE here so the journal
        # detail's two excursion blocks are taxonomy-driven (the frontend hardcodes no ternary label,
        # truncated flag, population title, or honest-absence copy). R-units only, descriptive copy.
        "excursions": {
            "ternary_outcomes": [
                {"id": k, "name": v} for k, v in EXCURSION_TERNARY_OUTCOMES.items()
            ],
            "truncated_label": EXCURSION_TRUNCATED_LABEL,
            "populations": [
                {"id": k, "name": v} for k, v in EXCURSION_POPULATIONS.items()
            ],
            "not_applicable": EXCURSION_NOT_APPLICABLE_COPY,
            "not_tracked": EXCURSION_NOT_TRACKED_COPY,
            "r_basis_caption": EXCURSION_R_BASIS_CAPTION,
        },
        # The segregated-analytics display copy (capability 31, J-59) — owned ONCE here so the
        # /journal analytics view is taxonomy-driven (the frontend hardcodes no label / caption /
        # framing). Descriptive, R-units, never a profitability / edge / win-rate claim.
        "analytics": dict(ANALYTICS_COPY),
        # The replay-studies display copy (capability 32, J-60/J-61/J-62) — owned ONCE here so the
        # /studies page is taxonomy-driven (the frontend hardcodes no label / caption / framing). Each
        # study status carries its OWN explicit label + honest-absence sentence (iter-15 lesson);
        # descriptive, measurement-framed, never an edge / win-rate / imperative / prediction claim.
        "studies": {
            "statuses": [{"id": k, "name": v} for k, v in STUDY_STATUSES.items()],
            "status_absence": dict(STUDY_STATUS_ABSENCE_COPY),
            "copy": dict(STUDY_COPY),
            # The two state-native auto-arming setups vs the two level (hindsight) setups, so the
            # create form knows which need a user-supplied level (it also reads ``setups[].requires_level``).
            "state_native_setups": ["absorption_reversal", "trend_continuation"],
            "level_setups": ["level_break", "failed_move_fade"],
            "ternary_outcomes": [
                {"id": k, "name": v} for k, v in EXCURSION_TERNARY_OUTCOMES.items()
            ],
        },
        # The setup-forming hints display copy (capability 33, J-65) — owned ONCE here so the cockpit's
        # hint dock + the /journal hint log are taxonomy-driven (the frontend hardcodes no pattern label,
        # dock title, register line, declared-from label, log column, or empty-state copy). The PER-HINT
        # evidence + baseline citation travel computed-once on each persisted hint record (built from this
        # module's ``hint_evidence`` / ``hint_baseline_citation`` templates), never re-worded on the
        # frontend. Strictest copy register: descriptive, present-tense, NEVER imperative/predictive/
        # certain (J-66). This block doubles as iter-23's code-identity canary — ``GET /research/taxonomy``
        # carrying ``hints`` proves the NEW server code is live.
        "hints": {
            "patterns": [
                {
                    "id": pid,
                    "name": spec["name"],
                    "setup_type": spec["setup_type"],
                    "direction": spec["direction"],
                }
                for pid, spec in HINT_PATTERNS.items()
            ],
            "copy": dict(HINT_COPY),
            "log_columns": dict(HINT_LOG_COLUMNS),
            "baseline_unvalidated": HINT_BASELINE_UNVALIDATED,
        },
        "disclaimer": "Descriptive only — not trading advice.",
    }
