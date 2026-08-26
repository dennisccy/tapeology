"""era-desk-iter-6 (J-05) source-introspection guard tests -- the ``test_copy_discipline.py``
pattern (read a frontend .tsx file as TEXT, assert on substrings; no browser, no runtime).

Guards, each proving something about the frontend a backend-only test suite otherwise could
not see:

  (a) TC-5 -- ``apps/frontend/app/desk/page.tsx`` never references any of the structure-side
      compute endpoints/functions (``/research/tradability``, ``/research/levels``,
      ``compute_tradability``, ``compute_levels``) -- every number the desk briefing renders comes
      from the already-fetched screen snapshot (``GET /research/desk/screen``), never a second,
      divergent computation (single-source-of-truth -- the era's own hard anti-goal).
  (b) TC-6 -- the NEW ``/structure`` query-param prefill block (delimited by the
      ``J-05-PREFILL-START``/``J-05-PREFILL-END`` markers in ``structure/page.tsx``) calls the
      SAME ``handleLoad`` the manual Load button already calls, and introduces no second
      fetch/compute path.
  (c) goal-desk-iter-17 (J-13) TC-8 -- ``apps/frontend/app/desk/page.tsx`` never derives a price
      value via arithmetic on ``row.distance_bps``/``row.price_low``/``row.price_high`` -- the new
      ``band`` column/tooltip line renders ``row.reference_close`` beside the row's own
      ``price_low``/``price_high``, never a value recomputed from them client-side.
  (d) goal-desk-iter-18 (J-14) TC-11 -- the SAME arithmetic guard, extended to also cover
      ``row.opposite_band``'s ``distance_bps``/``price_low``/``price_high``/``band_score`` and
      ``row.bands_by_class``'s ``A``/``B``/``C``/``unclassified`` counts -- the new ``opposite``
      column/tooltip line renders these fields verbatim, never a derived distance, price, or count.
  (e) goal-desk-iter-24 (J-16) TC-7 -- the ranked table's own layout REFLOW must not become a
      layout that silently changes what's rendered: `rows` renders in served order only (no
      `.sort(`/`.reverse(`/re-slice/comparator anywhere over `rows` -- the new `rank` cell is the
      `.map` index, never a client-recomputed position), and every `data-testid` a shipped
      journey's golden script or guard test depends on is still present in source after the
      reflow.

A guard that can never fail proves nothing -- each carries a seeded counter-test proving the
detection logic itself actually catches a violation (the ``test_copy_discipline.py``
seeded-violation precedent)."""

from __future__ import annotations

import pathlib
import re
from test_copy_discipline import find_violations

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
_SORTABLE_HEADER = _FRONTEND_ROOT / "components" / "SortableHeader.tsx"

# Comment strippers, matching `test_playbook_shape_overlay_guards.py`'s own `_code` convention: a
# guard must never pass or fail on prose that merely DESCRIBES the thing it forbids. This page's
# comments quote `.sort(`/`.reverse(` call syntax while explaining why the page does not use it.
_JSX_COMMENT = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")


def _code(source: str) -> str:
    source = _JSX_COMMENT.sub(" ", source)
    source = _BLOCK_COMMENT.sub(" ", source)
    return _LINE_COMMENT.sub(" ", source)
_STRUCTURE_PAGE = _FRONTEND_ROOT / "app" / "structure" / "page.tsx"

_FORBIDDEN_DESK_REFERENCES = (
    "/research/tradability",
    "/research/levels",
    "compute_tradability",
    "compute_levels",
)

# Every fetch/compute-trigger function this page already imports from lib/api, PLUS a bare
# `fetch(` -- if the prefill block ever grows a second network call of its own rather than
# reusing `handleLoad`, one of these substrings will be present.
_FORBIDDEN_PREFILL_CALLS = (
    "fetchLevels(",
    "fetchTradability(",
    "recordBarSeries(",
    "createBacktest(",
    "triggerEdgeReportCompute(",
    "fetch(",
)


def test_desk_page_never_references_structure_compute_endpoints():
    """TC-5: every rendered desk value comes from the already-fetched screen snapshot -- the desk
    page source contains zero references to the structure-side compute endpoints/functions."""
    source = _DESK_PAGE.read_text()
    hits = [needle for needle in _FORBIDDEN_DESK_REFERENCES if needle in source]
    assert not hits, (
        f"apps/frontend/app/desk/page.tsx references {hits} -- the desk briefing must read every "
        "value from GET /research/desk/screen verbatim, never recompute a structure number "
        "client-side"
    )


def test_desk_page_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_source = "const x = fetch('/research/tradability?symbol=AAPL');"
    hits = [needle for needle in _FORBIDDEN_DESK_REFERENCES if needle in seeded_source]
    assert hits == ["/research/tradability"]


def _extract_prefill_block(source: str) -> str:
    start = source.index("// J-05-PREFILL-START")
    end = source.index("// J-05-PREFILL-END")
    assert start < end, "J-05-PREFILL-START must precede J-05-PREFILL-END"
    return source[start:end]


def test_structure_page_has_the_j05_prefill_markers():
    """The extraction below is only meaningful if the markers actually exist -- an absent block
    would otherwise make ``test_structure_prefill_reuses_the_existing_load_function`` vacuous
    (``str.index`` raises ``ValueError`` rather than silently matching nothing, so a missing
    marker already fails loudly; this test names that failure mode explicitly)."""
    source = _STRUCTURE_PAGE.read_text()
    assert "// J-05-PREFILL-START" in source
    assert "// J-05-PREFILL-END" in source
    assert "useSearchParams" in source


def test_structure_prefill_reuses_the_existing_load_function():
    """TC-6: the new query-param prefill block calls the SAME ``handleLoad`` the manual Load
    button already calls -- no second fetch/compute function is introduced."""
    source = _STRUCTURE_PAGE.read_text()
    block = _extract_prefill_block(source)
    assert "handleLoad(" in block, (
        "the J-05 prefill block never calls handleLoad() -- it must reuse the manual Load "
        "button's own load path, not a second one"
    )
    hits = [needle for needle in _FORBIDDEN_PREFILL_CALLS if needle in block]
    assert not hits, (
        f"the J-05 prefill block calls {hits} -- it must call ONLY the existing handleLoad(), "
        "never a second fetch/compute function"
    )


def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail (counter-test): a seeded second fetch call inside the prefill block is
    caught, and a block missing the handleLoad() call is caught too."""
    seeded_block_with_second_fetch = (
        "// J-05-PREFILL-START\n"
        "useEffect(() => { fetchLevels(symbol, asOf); handleLoad(symbol, asOf); }, []);\n"
        "// J-05-PREFILL-END\n"
    )
    hits = [
        needle for needle in _FORBIDDEN_PREFILL_CALLS if needle in seeded_block_with_second_fetch
    ]
    assert hits == ["fetchLevels("]

    seeded_block_missing_handle_load = (
        "// J-05-PREFILL-START\nuseEffect(() => { setSymbolInput(symbol); }, []);\n"
        "// J-05-PREFILL-END\n"
    )
    assert "handleLoad(" not in seeded_block_missing_handle_load


# goal-desk-iter-17 (J-13) TC-8: no expression in the desk page may derive a NEW price value via
# arithmetic on `distance_bps`/`price_low`/`price_high` -- the honest disclosure this journey ships
# (`row.reference_close`, `row.price_low`-`row.price_high`) is a verbatim render of already-served
# values, never a client-side recomputation of the very number `reference_close` exists to disclose
# instead of forcing an operator (or agent) to invert `distance_bps` against a band edge.
# goal-desk-iter-18 (J-14): extended (never duplicated -- the iter-17 direct precedent) to also
# cover `row.opposite_band.*`'s distance/price/score fields and `row.bands_by_class.*`'s per-class
# counts -- the new `opposite` column/tooltip line renders these verbatim too, never a derived
# distance, price, or count (e.g. a client-side "total bands" sum or an implied spread).
# Forward-test era v2 (touch-anchored): extended AGAIN (the same never-duplicated discipline)
# to cover the Forward Returns panel's numeric paths -- the row's own band range and touch
# counts, plus the binding names its components MUST use (`touchRow` for a touch/anchor line,
# `touchValue` for a per-horizon leaf, `avgCell` for a row average, `summaryCell` for a summary
# cell) so a derived spread/sum/ratio over ANY served forward value is caught. The v1 `*_bps`
# paths died with the close-anchored shape.
# goal-playbook-iter-3 (J-03): extended AGAIN for the Playbook Signals section's own NEW numeric
# fields -- `signal.trigger_price`/`signal.invalidation_price` (a playbook signal's own served
# prices, with no forward-panel analogue). The section's per-horizon forward cells and baseline
# summary cells introduce NO new binding at all: `PlaybookSignalForward`/`PlaybookSummaryCells`
# reuse `ForwardTouchTable`/`ForwardTouchMeasureCells`/`ForwardAvgCellView` VERBATIM, so those
# values are already reached through the EXISTING `touchRow.*`/`touchValue.*`/`avgCell.*` bindings
# this guard already covers -- see test_desk_page_price_arithmetic_guard_catches_playbook_field_
# arithmetic below for the counter-test proving both the new and the reused bindings are caught.
# goal-playbook-iter-4 (J-04): extended AGAIN for the continuation family (jbe/dbi) and cup_handle's
# own NEW `signal.geometry.*` numerics -- `PlaybookSignalDetail`'s two new setup-branches render
# every one of these verbatim (base/jump geometry + ladder-step-ratio; cup/handle geometry + the
# three RVOL medians), never a client-recomputed spread or ratio.
# goal-playbook-iter-5 (J-05): extended AGAIN for capitulation's own NEW `signal.geometry.*`
# numerics -- `PlaybookSignalDetail`'s capitulation branch renders `decline_mbr`/`climax_rvol`/
# `bars_from_climax_to_trigger` verbatim (`decline_bars` is a plain bar count, like `base_bars`/
# `cup_bars` before it, so it stays outside this price-arithmetic list by the same precedent).
# goal-playbook-iter-6 (J-06): extended AGAIN for the range family's own NEW `signal.geometry.*`
# numerics -- `PlaybookSignalDetail`'s range_trade branch renders `range_width_mbr` verbatim, and
# its double_top/double_bottom branch renders `tops_gap_mbr`/`valley_depth_mbr`/
# `nominal_risk_mbr`/`second_top_rvol_vs_first` verbatim. Bar-count/int-count fields
# (`tops_separation_bars`, `low_zone_touches`, `high_zone_touches`) stay OUT of this list, following
# the `base_bars`/`cup_bars`/`decline_bars` precedent -- a plain count is not a price.
# goal-playbook-iter-7 (J-07): extended AGAIN for the new Backscan panel's own served numerics --
# `BackscanPlanPreview` renders `plan.total`/`plan.missing` verbatim, `BackscanControl`'s running
# indicator renders `compute.planned_total`/`compute.completed` verbatim, and
# `BackscanOutcomeCounts` (shared by the live progress view AND every runs-table row) renders
# `outcomes.reused`/`outcomes.recorded`/`outcomes.refused_non_session`/`outcomes.failed` verbatim --
# none of these are prices, but the IN SCOPE contract for this panel is "no client-side arithmetic
# on served numerics" full stop, so they are guarded here on the same footing as the price fields
# above rather than left to convention.
# goal-playbook-iter-8 (J-08): extended AGAIN for the new Playbook Evidence section's own served
# numerics -- the evidence table renders `cell.signal.*`/`cell.baseline.*` (n/n_truncated/
# n_baseline/median_pct/p25_pct/p75_pct/mean_pct) verbatim per (setup_id, side, measure) row, and
# the invalidation-breach line renders `breach.breached_count`/`breach.total_count` verbatim --
# every one of these is a straight pass-through of `GET /research/desk/playbook/evidence`, never a
# client-recomputed spread, ratio, or rate.
# goal-playbook-iter-12 (J-11): extended AGAIN for the Playbook Evidence section's five NEW served
# exclusion counts -- `cell.signal.*` gains `n_unmeasured`/`n_sessions` and `cell.baseline.*` gains
# `n_truncated`/`n_unmeasured`/`n_sessions` (already-declared bindings widened, never a new one),
# plus the new basis line's own `basis.n_records` (`PlaybookEvidenceBasisLine`'s own prop, the
# `plan.*`/`compute.*`/`outcomes.*` top-level-binding precedent). No client-side arithmetic on any
# of these is ever legitimate: they are exclusion/record COUNTS, not prices, but this panel's own
# IN SCOPE contract is "no client-side arithmetic on served numerics" full stop, the J-07 precedent.
# 2026-08-12 (the refresh chain's sixth and seventh steps): extended for the playbook compute
# snapshot's own progress pair, `signals_done`/`signals_total`. This closes a PRE-EXISTING gap
# rather than covering only new code -- the Playbook Signals section has rendered both verbatim
# since J-03 and neither was ever in this alternation; the chain's per-day tick line now renders
# them too, through the `tick.` binding its own waiter hands it. Same contract as the counts above.
_PRICE_ARITHMETIC_FIELDS = (
    r"row\.(?:distance_bps|price_low|price_high|reference_close"
    r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
    r"|bands_by_class\.(?:A|B|C|unclassified)"
    r"|band_price_low|band_price_high|touch_count|touches_beyond_cap)"
    r"|touchRow\.(?:entry_price|to_close_pct|close_price|mdd_long_pct|mdd_short_pct"
    r"|minutes_to_close)"
    r"|touchValue\.(?:return_pct|exit_price|mdd_long_pct|mdd_short_pct|effective_minutes)"
    r"|avgCell\.(?:mean_pct|median_pct)"
    r"|summaryCell\.(?:mean_pct|median_pct)"
    r"|signal\.(?:trigger_price|invalidation_price)"
    r"|geometry\.(?:jump_mbr|base_range_mbr|ladder_step_ratio|cup_depth_mbr|handle_retrace_frac"
    r"|handle_duration_frac|cup_middle_third_rvol_median|cup_outer_third_rvol_median"
    r"|handle_rvol_median|decline_mbr|climax_rvol|bars_from_climax_to_trigger"
    r"|range_width_mbr|tops_gap_mbr|valley_depth_mbr|nominal_risk_mbr|second_top_rvol_vs_first)"
    r"|plan\.(?:total|missing)"
    r"|compute\.(?:planned_total|completed)"
    r"|outcomes\.(?:reused|recorded|refused_non_session|failed)"
    r"|cell\.signal\.(?:n|n_positive|positive_share|n_truncated|n_unmeasured|n_sessions|median_pct|p25_pct|p75_pct"
    r"|mean_pct)"
    # The band-context lens (spec §6): a location is SERVED, never re-derived on the client -- the
    # distance, the band edges, and the threshold comparison all belong to the backend.
    r"|context\.(?:backing_bps|headroom_bps|risk_bps|room_r)"
    r"|context\.(?:containing_band|wall_below|wall_above)"
    r"\.(?:distance_bps|price_low|price_high|quality_score|member_count)"
    r"|bandContext\.(?:backing_bps|headroom_bps|risk_bps|room_r)"
    r"|band\.parameters\.(?:near_band_bps|room_r_edges)"
    r"|cell\.baseline\.(?:n_baseline|n_positive|positive_share|n_truncated|n_unmeasured|n_sessions|median_pct"
    r"|p25_pct|p75_pct"
    r"|mean_pct)"
    r"|breach\.(?:breached_count|total_count)"
    r"|basis\.(?:n_records)"
    r"|(?:compute|tick|snapshot)\.(?:signals_done|signals_total)"
    # goal-referee-iter-8 (J-07): the Referee Registry section's own served numerics -- a
    # shortlist candidate's live readiness (never divide/subtract these client-side; the backend
    # already served accrual_rate_sessions_per_day/projected_days_to_target as computed numbers)
    # and a registered hypothesis's discovery count (never combined with its accrual siblings).
    # goal-referee-iter-12 (J-11): widened for the TWO new per-candidate fields beside the shipped
    # pair -- informative_sessions_per_pooled_session (API-only this iteration, no dedicated
    # column yet, guarded here anyway per "every new served numeric joins this list") and
    # projected_pooled_sessions_to_target (the new "Projected sessions" column).
    r"|candidate\.(?:n|n_sessions|accrual_rate_sessions_per_day|projected_days_to_target"
    r"|informative_sessions_per_pooled_session|projected_pooled_sessions_to_target)"
    r"|hyp\.discovery\.(?:n|n_sessions)"
    # goal-referee-iter-12 (J-11): the Referee Registry section's own new accrual-basis line --
    # accrualBasis.* (the RefereeRegistrySection's own local binding for `shortlist.accrual_basis`)
    # -- a corpus-wide recorded/pooled session count or day-span must never be recombined
    # client-side (e.g. a client-computed "stale share" or "days since last gap").
    r"|accrualBasis\.(?:corpus_span_days|recorded_sessions_in_span|pooled_sessions_at_current_basis"
    r"|longest_zero_session_stretch_days)"
    # goal-referee-iter-9 (J-08 rider): the Referee Registry section's own accrual numerics --
    # mirrors the existing `hyp.discovery.*` entry above (a "sessions accrued so far" readout is
    # the obvious client-side subtraction to reach for and the obvious thing to get wrong; the
    # backend already served both halves of the ratio as computed numbers).
    r"|hyp\.accrual\.(?:informative_post_boundary_sessions|target_sessions)"
    # goal-referee-iter-10 (J-09): the Referee Adjudications section's own served numerics -- the
    # live pre-checkpoint accrual pair (the SAME "sessions accrued so far" risk the `hyp.accrual.*`
    # entry above already guards, applied to the adjudications response's own `live_coverage` fold
    # -- `entry.live_coverage?.post_boundary_sessions`/`?.target_sessions` in
    # `RefereeAdjudicationEntryRow`, `\??` covering the optional-chaining `?.` the JSX actually
    # uses) and the recorded checkpoint snapshot's own Benjamini-Hochberg fold (`snapshot.bh.k_star`/
    # `.m`/`.q` -- never combined into a client-computed pass rate or "how many below threshold"
    # count).
    r"|entry\.live_coverage\??\.(?:post_boundary_sessions|target_sessions)"
    r"|snapshot\.bh\.(?:k_star|m|q)"
    # goal-referee-iter-10 (J-09): the Referee Runs section's own served numerics -- both
    # single-flight-PER-KEY compute managers' live `{done,total}` progress pair
    # (`compute?.done`/`compute?.total` in `RefereeNullBuildControl`/`RefereeEvaluateControl`,
    # `\??` covering the same optional-chaining usage), and the durable run-ledger's own
    # `{done,total}` progress pair, nested one level deeper under `run.progress` (`RefereeNullRunRow`/
    # `RefereeEvaluationRunRow`).
    r"|compute\??\.(?:done|total)"
    r"|run\.progress\.(?:done|total)"
    # goal-referee-iter-13 (J-12): the Referee Registry section's own new evidence-readiness
    # blocks -- GET /research/desk/referee/evidence read verbatim for the FIRST time in the
    # browser. J-12's whole point is "zero client-side arithmetic on any served numeric", so
    # every one of the seven counts this component renders joins this list on the same footing
    # as every other referee numeric above (evidence.playbook_occurrence.*/
    # evidence.strategy_trade.* -- the RefereeEvidenceReadinessSection's own local binding for
    # the fetched `GET /research/desk/referee/evidence` body).
    r"|evidence\.playbook_occurrence\.(?:records|distinct_sessions|signals_at_current_basis)"
    r"|evidence\.strategy_trade\.(?:dataset_count|trade_count)"
    r"|evidence\.strategy_trade\.per_split_counts\.(?:train|holdout)"
    # goal-rapid-microscope-iter-1 (J-01): the new Microscope Readiness section's own served
    # numerics -- GET /research/desk/micro/readiness read verbatim for the first time in the
    # browser. Every corpus total, per-shard count/byte-size/fallback-fraction, and per-study
    # floor pair renders as served (`.toFixed()`/`.toLocaleString()` are FORMATTING calls, never
    # arithmetic); no client-side symbol-day share, byte-to-MB conversion, fallback percentage,
    # or floor-shortfall arithmetic is ever legitimate here.
    r"|readiness\.totals\.(?:distinct_symbol_days|distinct_datasets|rth_minutes_covered"
    r"|session_equivalents|referee_tick_gate_symbol_days"
    # r14: the two session quantities, named explicitly so neither can stand in for the other --
    # `distinct_session_dates` is the fold-geometry unit (spec §0), `full_session_equivalents` is
    # RTH coverage. Both render as served; the `.toFixed()` on the second is formatting.
    r"|distinct_session_dates|full_session_equivalents)"
    r"|shard\.(?:trade_count|quote_count|bytes|fallback_frac)"
    # r14: the pilot-floor row now serves the two EXECUTABLE floors (first fold / survivor), the
    # actual constructible fold count, and the retained arithmetic-only pair. Every one renders as
    # served -- the whole point of the change is that the browser stops implying a fold arithmetic
    # the backend never performed.
    r"|floor\.(?:required_sessions|available_sessions|available_session_dates"
    # r14.2: `constructible_folds_min_session_dates` is the accurate name for the same number --
    # a session COUNT proves folds are BUILDABLE, never that a survivor is reachable. Renders as
    # served, like every other floor value here.
    r"|first_fold_min_session_dates|survivor_min_session_dates"
    r"|constructible_folds_min_session_dates|folds_constructible)"
    # goal-rapid-microscope-iter-14 (J-08 half 1): the new Scout Ledger / Walk-Forward / Validation
    # Vault sections' own served numerics -- GET /research/desk/micro/{scout,walkforward,vault}
    # read verbatim for the first time in the browser. The Scout Ledger's `screen_result` and the
    # Walk-Forward sequence's `sequence_verdict`/raw `fold_results`/fold-spec geometry are rendered
    # via `JSON.stringify(...)` (a serialization call, never arithmetic, the SAME class as
    # `.toFixed()`/`.toLocaleString()` above) rather than destructured field-by-field, so no
    # per-field entry is needed for those -- only the fields this page actually binds to a local
    # name join this list. `size_bucket` (Vault, order-of-magnitude only) and
    # `checksum_commitment`/`rule_commitment`/`vault_secret_commitment`/`commitment_nonce` (opaque
    # strings) carry no numeric value and are deliberately absent from every alternation below.
    r"|family\.(?:variants_tried)"
    r"|trial\.(?:withheld_excluded)"
    r"|fold\.(?:fold_index|effect|n|n_sessions)"
    r"|sequence\.decay_view\.recency\.(?:older_fold_count|recent_fold_count|older_positive_share"
    r"|recent_positive_share)"
    r"|compute\??\.progress\.(?:candidates_done|candidates_total|steps_done|steps_total)"
    r"|run\.(?:candidates_done|candidates_total|steps_done|steps_total|folds_evaluated)"
    r"|universe\.(?:symbol_rule_size|date_rule_size)"
    # goal-rapid-microscope-iter-15 (J-08 half 2): the Microscope Readiness section's own TWO new
    # aggregate-only served numerics -- the sealed-tranche totals (`sealed_tranche.shard_count`/
    # `.symbol_days`, plus the per-universe breakdown's own `shard_count`/`symbol_days` counts,
    # rendered off the destructured `[universeId, universeCounts]` entry) and the joinable-corpus
    # `withheld_excluded` count. Both are ALREADY served by unchanged `micro_readiness.py` code --
    # this iteration only adds a reader -- but per this file's own "every new served numeric joins
    # this list" contract, they join it on the same footing as every other readiness field above.
    r"|readiness\.sealed_tranche\.(?:shard_count|symbol_days)"
    r"|universeCounts\.(?:shard_count|symbol_days)"
    r"|readiness\.joinable_corpus\.(?:withheld_excluded)"
    # goal-rapid-microscope-iter-31 (J-11): the new Graduation section's own served numeric --
    # GET /research/desk/micro/graduation read verbatim for the first time in the browser. Each
    # sealed-evaluation row's own observation count (`evaluation.n`, `GraduationSealedEvaluation
    # Row`'s destructured field) is the only graduation numeric the section binds to a local name
    # directly -- every OTHER field of a transition/sealed-evaluation row (heterogeneous by
    # transition target state / evaluation artifact shape) is rendered via `JSON.stringify(...)`
    # (a serialization call, never arithmetic, the `screen_result`/raw `fold_results` precedent),
    # so no per-field entry is needed for those.
    r"|evaluation\.(?:n)"
    # goal-rapid-microscope-iter-33 (J-12): the new Feature Snapshots section's own served
    # numerics -- GET /research/desk/micro/snapshots read verbatim for the first time in the
    # browser (registered since era baseline; zero UI/MCP readers before this iteration). Each
    # snapshot row's own `row_count`/`bytes_on_disk` (`FeatureSnapshotsSection`'s `snapshot.`
    # destructured field) and the route's own two disclosure counts (`report.withheld_excluded`/
    # `report.stale_excluded`, the fetched response body's own local binding) join this list on
    # the same footing as every other served numeric above -- no client-side byte-to-MB
    # conversion, no withheld/stale share arithmetic, is ever legitimate here.
    r"|snapshot\.(?:row_count|bytes_on_disk)"
    r"|report\.(?:withheld_excluded|stale_excluded)"
)
_PRICE_ARITHMETIC_PATTERN = re.compile(
    rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
)


def test_desk_page_never_derives_a_price_via_arithmetic_on_distance_or_band_edges():
    """TC-8/TC-11: scans `apps/frontend/app/desk/page.tsx`'s source for any expression combining
    `row.distance_bps`/`row.price_low`/`row.price_high` (goal-desk-iter-17, J-13) or
    `row.opposite_band.*`/`row.bands_by_class.*` (goal-desk-iter-18, J-14) with an arithmetic
    operator. The `band` column/tooltip line renders `row.reference_close` beside
    `row.price_low`/`row.price_high`, and the new `opposite` column/tooltip line renders
    `row.opposite_band`/`row.bands_by_class` verbatim -- never a derived value."""
    source = _DESK_PAGE.read_text()
    hits = _PRICE_ARITHMETIC_PATTERN.findall(source)
    assert not hits, (
        f"apps/frontend/app/desk/page.tsx derives a value via arithmetic on distance_bps/price_low/"
        f"price_high/opposite_band/bands_by_class ({hits}) -- the page must render only what "
        "GET /research/desk/screen already served, never recompute a value client-side"
    )


def test_desk_page_price_arithmetic_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_source = "const implied = row.price_high - row.reference_close;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_source) is not None
    # 2026-08-12: the playbook progress pair the refresh chain's per-day tick line also renders. A
    # "members left to walk" readout is the obvious thing to reach for and the obvious thing to get
    # wrong -- the served pair is the only honest account of that walk.
    seeded_remaining = "const remaining = tick.signals_total - tick.signals_done;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_remaining) is not None


def test_desk_page_price_arithmetic_guard_catches_opposite_band_and_bands_by_class_arithmetic():
    """TC-11 (goal-desk-iter-18, J-14) counter-test: the extended guard also catches arithmetic on
    the new `opposite_band`/`bands_by_class` fields, not just the pre-existing distance_bps/
    price_low/price_high ones."""
    seeded_opposite = "const gap = row.opposite_band.price_high - row.price_high;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_opposite) is not None

    seeded_score = "const combined = row.opposite_band.band_score + row.band_score;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_score) is not None


def test_desk_page_price_arithmetic_guard_catches_referee_evidence_arithmetic():
    """goal-referee-iter-13 (J-12) TC-12 counter-test: the widened guard also catches arithmetic
    over the new Referee evidence-readiness numerics (GET /research/desk/referee/evidence's first
    UI reader), proving the widened pattern actually fails on injected client-side arithmetic --
    not just that it passes on unmodified source."""
    seeded_total = (
        "const total = evidence.playbook_occurrence.records + "
        "evidence.playbook_occurrence.distinct_sessions;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_total) is not None


def test_desk_page_price_arithmetic_guard_catches_feature_snapshots_arithmetic():
    """goal-rapid-microscope-iter-33 (J-12) TC-5 counter-test: the widened guard also catches
    arithmetic over the new Feature Snapshots numerics (GET /research/desk/micro/snapshots' first
    UI reader), proving the widened pattern actually fails on injected client-side arithmetic --
    not just that it passes on unmodified source."""
    seeded_bytes = "const avgBytes = snapshot.bytes_on_disk / snapshot.row_count;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bytes) is not None

    seeded_share = "const share = report.withheld_excluded + report.stale_excluded;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_share) is not None

    seeded_signals = (
        "const share = evidence.playbook_occurrence.signals_at_current_basis / "
        "evidence.playbook_occurrence.records;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signals) is not None

    seeded_split = (
        "const combined = evidence.strategy_trade.per_split_counts.train + "
        "evidence.strategy_trade.per_split_counts.holdout;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_split) is not None

    seeded_trades = (
        "const perDataset = evidence.strategy_trade.trade_count / "
        "evidence.strategy_trade.dataset_count;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_trades) is not None

    seeded_bands_by_class = "const total = row.bands_by_class.A + row.bands_by_class.B;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bands_by_class) is not None


def test_desk_page_price_arithmetic_guard_catches_forward_field_arithmetic():
    """Forward-test era v2 counter-test: the extended guard also catches arithmetic over the
    touch-anchored panel's served values -- the row's band range, a touch line's own numbers, a
    per-horizon leaf, a row average, and a summary cell -- so a client-derived spread, sum, or
    ratio over any of them is caught, exactly like the ranked-table fields before it."""
    seeded_band = "const width = row.band_price_high - row.band_price_low;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_band) is not None

    seeded_touch = "const range = touchRow.mdd_long_pct - touchRow.mdd_short_pct;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_touch) is not None

    seeded_entry = "const off = touchRow.entry_price - row.price_low;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_entry) is not None

    seeded_horizon = "const bps = touchValue.return_pct * 100;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_horizon) is not None

    seeded_avg = "const skew = avgCell.mean_pct - avgCell.median_pct;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_avg) is not None

    seeded_summary = "const lift = summaryCell.mean_pct - summaryCell.median_pct;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_summary) is not None


def test_desk_page_price_arithmetic_guard_catches_exit_price_and_per_horizon_mdd_arithmetic():
    """The exit price exists so a reader can CHECK the served return, not so the page can compute
    one. Recomputing `(exit - entry) / entry` client-side would silently become a second owner of
    the number `return_pct` already is -- caught, along with any derivation over a horizon's own
    two drawdowns or the session-end close."""
    seeded_return = "const pct = (touchValue.exit_price - touchRow.entry_price) / touchRow.entry_price;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_return) is not None

    seeded_close = "const move = touchRow.close_price - touchRow.entry_price;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_close) is not None

    seeded_horizon_mdd = "const span = touchValue.mdd_short_pct - touchValue.mdd_long_pct;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_horizon_mdd) is not None

    seeded_worst = "const worst = Math.abs(touchValue.mdd_long_pct * 2);"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_worst) is not None


def test_desk_page_price_arithmetic_guard_catches_playbook_field_arithmetic():
    """goal-playbook-iter-3 (J-03) counter-test: the extended guard catches arithmetic on the
    Playbook Signals section's own NEW `signal.trigger_price`/`signal.invalidation_price` bindings,
    and -- since that section's forward-cell/summary-cell renderers REUSE `ForwardTouchTable`/
    `ForwardTouchMeasureCells`/`ForwardAvgCellView` verbatim rather than re-declaring lookalikes --
    also still catches arithmetic on the `touchRow`/`touchValue`/`avgCell` bindings those shared
    renderers use, proving the reuse did not quietly route the playbook's forward/baseline numbers
    around this guard."""
    seeded_trigger = "const stop = signal.trigger_price - signal.invalidation_price;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_trigger) is not None

    seeded_forward = "const gain = touchValue.exit_price - touchRow.entry_price;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_forward) is not None

    seeded_baseline = "const edge = avgCell.mean_pct - avgCell.median_pct;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline) is not None


def test_desk_page_price_arithmetic_guard_catches_continuation_and_cup_handle_field_arithmetic():
    """goal-playbook-iter-4 (J-04) counter-test: the extended guard catches arithmetic on the
    continuation family's (jbe/dbi) and cup_handle's own NEW `geometry.*` bindings."""
    seeded_jbe = "const net = geometry.jump_mbr - geometry.base_range_mbr;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_jbe) is not None

    seeded_ladder = "const decay = geometry.ladder_step_ratio * 2;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_ladder) is not None

    seeded_cup = "const drop = geometry.cup_depth_mbr - geometry.handle_retrace_frac;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_cup) is not None

    seeded_rvol_contrast = (
        "const contrast = geometry.cup_middle_third_rvol_median / geometry.cup_outer_third_rvol_median;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_rvol_contrast) is not None

    seeded_handle_rvol = "const dry = geometry.handle_rvol_median - geometry.cup_outer_third_rvol_median;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_handle_rvol) is not None


def test_desk_page_price_arithmetic_guard_catches_capitulation_field_arithmetic():
    """goal-playbook-iter-5 (J-05) counter-test: the extended guard catches arithmetic on
    capitulation's own NEW `geometry.*` bindings."""
    seeded_decline = "const net = geometry.decline_mbr - geometry.climax_rvol;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_decline) is not None

    seeded_bars = "const pace = geometry.bars_from_climax_to_trigger * 5;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bars) is not None


def test_desk_page_price_arithmetic_guard_catches_range_family_field_arithmetic():
    """goal-playbook-iter-6 (J-06) counter-test: the extended guard catches arithmetic on the range
    family's own NEW `geometry.*` bindings (range_trade's `range_width_mbr`; double_top/
    double_bottom's `tops_gap_mbr`/`valley_depth_mbr`/`nominal_risk_mbr`/
    `second_top_rvol_vs_first`)."""
    seeded_range_width = "const half = geometry.range_width_mbr / 2;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_range_width) is not None

    seeded_tops = "const net = geometry.tops_gap_mbr - geometry.valley_depth_mbr;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_tops) is not None

    seeded_risk = "const scaled = geometry.nominal_risk_mbr * 2;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_risk) is not None

    seeded_rvol_ratio = "const inverse = 1 / geometry.second_top_rvol_vs_first;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_rvol_ratio) is not None


def test_desk_page_price_arithmetic_guard_catches_evidence_field_arithmetic():
    """goal-playbook-iter-8 (J-08) counter-test: the extended guard catches arithmetic on the new
    Playbook Evidence section's own `cell.signal.*`/`cell.baseline.*`/`breach.*` bindings."""
    seeded_spread = "const spread = cell.signal.p75_pct - cell.signal.p25_pct;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_spread) is not None

    seeded_skew = "const skew = cell.signal.mean_pct - cell.baseline.mean_pct;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_skew) is not None

    seeded_count = "const observed = cell.signal.n - cell.signal.n_truncated;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_count) is not None

    seeded_rate = "const rate = breach.breached_count / breach.total_count;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_rate) is not None


def test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmetic():
    """goal-playbook-iter-12 (J-11) counter-test: the extended guard catches arithmetic on the five
    NEW exclusion-count bindings (`cell.signal.n_unmeasured`/`n_sessions`,
    `cell.baseline.n_truncated`/`n_unmeasured`/`n_sessions`) and the new basis line's own
    `basis.n_records` -- proving the widened `cell.signal.*`/`cell.baseline.*` groups and the new
    `basis.*` group actually catch a violation, the "a lint that cannot fail proves nothing"
    precedent applied to each new field individually."""
    seeded_signal_unmeasured = "const measured = cell.signal.n - cell.signal.n_unmeasured;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_unmeasured) is not None

    seeded_signal_sessions = "const perSession = cell.signal.n / cell.signal.n_sessions;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_sessions) is not None

    seeded_baseline_truncated = "const clean = cell.baseline.n_baseline - cell.baseline.n_truncated;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_truncated) is not None

    seeded_baseline_unmeasured = "const total = cell.baseline.n_baseline + cell.baseline.n_unmeasured;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_unmeasured) is not None

    seeded_baseline_sessions = "const perSession = cell.baseline.n_baseline / cell.baseline.n_sessions;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_baseline_sessions) is not None

    seeded_basis = "const perDate = basis.n_records / basis.dates.length;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_basis) is not None


def test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic():
    """goal-rapid-microscope-iter-1 (J-01) TC-9 counter-test: the extended guard catches
    arithmetic on the new Microscope Readiness section's own served numerics -- proving the
    widened pattern actually fails on injected client-side arithmetic, not just that it passes on
    unmodified source."""
    seeded_share = (
        "const share = readiness.totals.distinct_symbol_days / "
        "readiness.totals.referee_tick_gate_symbol_days;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_share) is not None

    seeded_pct = "const pct = shard.fallback_frac * 100;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_pct) is not None

    seeded_mb = "const mb = shard.bytes / 1_000_000;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_mb) is not None

    seeded_shortfall = "const shortfall = floor.required_sessions - floor.available_sessions;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_shortfall) is not None

    # And the pattern does NOT over-match: the real page's own guard test below still finds zero
    # hits, so this new coverage does not accidentally flag legitimate, non-arithmetic JSX.
    assert _PRICE_ARITHMETIC_PATTERN.search("const label = `${basis.n_records} records`;") is None


def test_desk_page_price_arithmetic_guard_catches_sealed_tranche_and_universe_counts_and_withheld_excluded_arithmetic():
    """goal-rapid-microscope-iter-16 (J-10) TC-15 counter-test: the iteration-15-added
    ``readiness.sealed_tranche.*``/``universeCounts.*``/``readiness.joinable_corpus.
    withheld_excluded`` clauses (module docstring above, "iter-15" note) catch arithmetic on their
    own served numerics -- closing iteration 15's own open MINOR finding that these two clauses had
    never been proven capable of failing."""
    seeded_ratio = (
        "const ratio = readiness.sealed_tranche.shard_count / readiness.sealed_tranche.symbol_days;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_ratio) is not None

    seeded_total = "const total = universeCounts.shard_count + universeCounts.symbol_days;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_total) is not None

    seeded_included = "const included = 1 - readiness.joinable_corpus.withheld_excluded;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_included) is not None

    # And the pattern does NOT over-match: a non-arithmetic render of the same fields is clean.
    assert _PRICE_ARITHMETIC_PATTERN.search(
        "const label = `${readiness.sealed_tranche.shard_count} shards`;"
    ) is None


def test_desk_page_price_arithmetic_guard_catches_referee_shortlist_and_discovery_field_arithmetic():
    """goal-referee-iter-8 (J-07) counter-test: the extended guard catches arithmetic on the new
    Referee Registry section's own `candidate.*` (shortlist readiness) and `hyp.discovery.*`
    bindings -- these numbers are computed once, on the backend (referee_registry.py's
    `shortlist_response()`/`_hypothesis_discovery()`), and must never be re-derived client-side."""
    seeded_days = (
        "const days = (candidate.target_sessions - candidate.n_sessions) / "
        "candidate.accrual_rate_sessions_per_day;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_days) is not None

    seeded_n_diff = "const untested = candidate.n - candidate.n_sessions;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_n_diff) is not None

    seeded_projected = "const soon = candidate.projected_days_to_target * 2;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_projected) is not None

    seeded_discovery_total = "const total = hyp.discovery.n + hyp.accrual.informative_post_boundary_sessions;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_discovery_total) is not None

    seeded_discovery_sessions = "const ratio = hyp.discovery.n_sessions / hyp.discovery.n;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_discovery_sessions) is not None

    # And the pattern does NOT over-match: rendering the two numbers side by side as plain text
    # (never an arithmetic operator between the field accesses themselves) stays clean -- exactly
    # the SAME "X / Y" display idiom this component actually uses.
    assert _PRICE_ARITHMETIC_PATTERN.search(
        "const label = `${hyp.discovery.n} / ${hyp.discovery.n_sessions}`;"
    ) is None


def test_desk_page_price_arithmetic_guard_catches_hyp_accrual_arithmetic_in_isolation():
    """goal-referee-iter-9 rider (TC-18): ``hyp.accrual.*`` isolated -- never paired with a
    ``hyp.discovery.*`` field, so this proves THIS iteration's own extension is what catches it
    (the pre-existing seeded string above already matched on its own ``hyp.discovery.n`` half,
    which would have passed even before this rider). A mutated-to-arithmetic "sessions remaining"
    readout fails; the shipped pass-through rendering (the exact
    ``{hyp.accrual.informative_post_boundary_sessions} / {hyp.accrual.target_sessions}`` JSX line)
    passes clean."""
    seeded_remaining = (
        "const remaining = hyp.accrual.target_sessions - "
        "hyp.accrual.informative_post_boundary_sessions;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_remaining) is not None

    seeded_ratio = (
        "const pct = hyp.accrual.informative_post_boundary_sessions / hyp.accrual.target_sessions;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_ratio) is not None


def test_desk_page_price_arithmetic_guard_catches_referee_adjudications_and_runs_field_arithmetic():
    """goal-referee-iter-10 (J-09) counter-test: the extended guard catches arithmetic on the new
    Referee Adjudications section's `entry.live_coverage.*`/`snapshot.bh.*` bindings and the new
    Referee Runs section's `compute.*`/`run.progress.*` bindings -- covering BOTH the
    optional-chaining (`?.`) and plain-dot forms the guard's `\\??` now accepts, proving each new
    field path is genuinely covered (not just listed, TC-20)."""
    seeded_live_coverage = (
        "const remaining = entry.live_coverage.target_sessions - "
        "entry.live_coverage.post_boundary_sessions;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_live_coverage) is not None

    seeded_live_coverage_optional = (
        "const remaining = entry.live_coverage?.target_sessions - "
        "entry.live_coverage?.post_boundary_sessions;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_live_coverage_optional) is not None

    seeded_bh = "const nonSignificant = snapshot.bh.m - snapshot.bh.k_star;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bh) is not None

    seeded_bh_rate = "const passRate = snapshot.bh.k_star / snapshot.bh.m;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bh_rate) is not None

    seeded_compute = "const remaining = compute.total - compute.done;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_compute) is not None

    seeded_compute_optional = "const remaining = compute?.total - compute?.done;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_compute_optional) is not None

    seeded_run_progress = "const remaining = run.progress.total - run.progress.done;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_run_progress) is not None

    # And the pattern does NOT over-match: the real page's own pass-through renderings -- the
    # optional-chaining accrual pair, the BH template-literal display, the fmt()-wrapped compute
    # progress, and the run-ledger progress pair -- stay clean (the EXACT JSX/template-literal
    # idioms RefereeAdjudicationEntryRow/RefereeNullBuildControl/RefereeEvaluateControl/
    # RefereeNullRunRow/RefereeEvaluationRunRow actually use).
    assert _PRICE_ARITHMETIC_PATTERN.search(
        '{entry.live_coverage?.post_boundary_sessions ?? 0} /{" "}\n'
        "{entry.live_coverage?.target_sessions ?? 0} sessions"
    ) is None
    assert _PRICE_ARITHMETIC_PATTERN.search(
        "`${snapshot.bh.k_star} / ${snapshot.bh.m} (q=${snapshot.bh.q})`"
    ) is None
    assert _PRICE_ARITHMETIC_PATTERN.search(
        "{fmt(compute?.done ?? 0, 0)} / {fmt(compute?.total ?? 0, 0)}"
    ) is None
    assert _PRICE_ARITHMETIC_PATTERN.search("{run.progress.done} / {run.progress.total}") is None

    # The shipped pass-through rendering (page.tsx's own "X / Y" JSX line) stays clean.
    assert _PRICE_ARITHMETIC_PATTERN.search(
        "{hyp.accrual.informative_post_boundary_sessions} / {hyp.accrual.target_sessions}"
    ) is None


def test_desk_page_price_arithmetic_guard_catches_accrual_basis_and_pooled_projection_arithmetic():
    """goal-referee-iter-12 (J-11) counter-test: the extended guard catches arithmetic on the new
    accrual-basis line's own `accrualBasis.*` bindings (corpus-wide recorded/pooled session counts
    and the day span) and on the two new per-candidate fields
    (`candidate.informative_sessions_per_pooled_session`/`candidate.projected_pooled_sessions_to_target`)
    -- proving the widened `candidate.*` group and the new `accrualBasis.*` group each genuinely
    catch a violation, not just list it (the "a lint that cannot fail proves nothing" precedent)."""
    seeded_stale_share = (
        "const stale = accrualBasis.recorded_sessions_in_span - "
        "accrualBasis.pooled_sessions_at_current_basis;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_stale_share) is not None

    seeded_pooled_rate = (
        "const rate = accrualBasis.pooled_sessions_at_current_basis / accrualBasis.corpus_span_days;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_pooled_rate) is not None

    seeded_gap_pct = (
        "const share = accrualBasis.longest_zero_session_stretch_days / "
        "accrualBasis.corpus_span_days;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_gap_pct) is not None

    seeded_pooled_projection = (
        "const soon = candidate.projected_pooled_sessions_to_target * 2;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_pooled_projection) is not None

    seeded_pooled_rate_diff = (
        "const gap = candidate.accrual_rate_sessions_per_day - "
        "candidate.informative_sessions_per_pooled_session;"
    )
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_pooled_rate_diff) is not None

    # And the pattern does NOT over-match: rendering the basis line's fields as plain descriptive
    # text, and the new column's value via the SAME null-guarded ternary the shipped "Projected
    # days" column already uses, both stay clean.
    assert _PRICE_ARITHMETIC_PATTERN.search(
        "`${accrualBasis.recorded_sessions_in_span} recorded / "
        "${accrualBasis.pooled_sessions_at_current_basis} pooled over "
        "${accrualBasis.corpus_span_days}d`"
    ) is None
    assert _PRICE_ARITHMETIC_PATTERN.search(
        "candidate.projected_pooled_sessions_to_target === null "
        '? "—" '
        ": candidate.projected_pooled_sessions_to_target.toFixed(0)"
    ) is None


# goal-playbook-iter-4 audit (F1): `base_lows_ascending` is ONE served field name carrying the
# direction-appropriate triangle check underneath (non-decreasing LOWS for `jbe`, non-increasing
# HIGHS for `dbi` -- see `desk_playbook_detect._base_lows_ascending`). The continuation geometry
# line must therefore label the shape the detector ACTUALLY measured for that side; a single
# unconditional "ascending base" string described a dbi base as the opposite of what was measured.
_CONTINUATION_GEOMETRY_LINE = re.compile(
    r'data-testid="desk-playbook-signal-continuation-geometry".*?</p>', re.DOTALL
)


def test_desk_page_labels_the_dbi_base_shape_as_descending_not_ascending():
    """The rendered base-shape label branches on `setup_id`: `jbe` reads "ascending base" (its
    lows), `dbi` reads "descending base" (its highs) -- never one unconditional word for both."""
    source = _DESK_PAGE.read_text()
    match = _CONTINUATION_GEOMETRY_LINE.search(source)
    assert match is not None, "the jbe/dbi geometry line is missing from apps/frontend/app/desk/page.tsx"
    line = match.group(0)
    assert "base_lows_ascending" in line
    assert "ascending base" in line and "descending base" in line, (
        "the continuation geometry line must render BOTH direction labels -- rendering only "
        '"ascending base" describes a dbi (short) base as the opposite of the measured geometry'
    )
    assert 'signal.setup_id === "jbe"' in line, (
        "the base-shape label must be selected by setup_id, so each side reads the shape its own "
        "detector actually measured"
    )


def test_dbi_base_shape_label_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- the pre-audit shape (one unconditional "ascending base") is caught."""
    seeded_line = (
        '<p data-testid="desk-playbook-signal-continuation-geometry">'
        '{geometry.base_flatline && " · flatline base"}'
        '{geometry.base_lows_ascending && " · ascending base"}</p>'
    )
    match = _CONTINUATION_GEOMETRY_LINE.search(seeded_line)
    assert match is not None
    assert "descending base" not in match.group(0)
    assert 'signal.setup_id === "jbe"' not in match.group(0)


# goal-desk-iter-24 (J-16) TC-7 (a): the ranked table's own reflow adds a `rank` cell rendering
# each row's own 1-based position in the served `rows` array (the `.map` index) -- this guard
# proves the page never sorts, reverses, or re-slices `rows` to produce that position (or any
# other display order) client-side. Matches a direct chain (`rows.sort(`), a spread-then-chain
# (`[...rows].sort(`), and an intervening simple call (e.g. `rows.filter(...).sort(`) -- `.filter(`
# alone (used elsewhere on this page only to COUNT rows, never to reorder or re-render them) is not
# itself forbidden.
_ROWS_REORDER_PATTERN = re.compile(
    r"(?:\[\s*\.\.\.\s*rows\s*\]|\brows\b)\s*(?:\.\s*\w+\([^()]*\)\s*)*\.\s*(?:sort|reverse)\s*\("
)

# The ONE sanctioned `rows` slice on this page: the ranked table's own contiguous page window.
# Matched separately from the reorder pattern above so the two intents stay distinct -- a reorder
# changes WHICH order rows are in, a window changes only WHICH of them are on screen.
_ROWS_SLICE_PATTERN = re.compile(
    r"(?:\[\s*\.\.\.\s*rows\s*\]|\brows\b)\s*(?:\.\s*\w+\([^()]*\)\s*)*\.\s*slice\s*\("
)

# The ranked table's page window now slices the DISPLAYED order rather than `rows` itself, because
# the operator can choose an order other than the served one. `sort.entries` is the shared hook's
# own total, one-per-served-row projection, so a window over it still preserves every property the
# `rows` window had.
_ORDERED_SLICE_PATTERN = re.compile(r"\bsort\.entries\b\s*\.\s*slice\s*\(")

# The TWO sanctioned slices of a displayed order on this page, each pinned by its exact expression.
# They are different acts and stay named separately: a WINDOW pages through everything (every row
# stays reachable), a CAP truncates (rows past it are not shown at all) -- which is why the cap
# ships its own "showing N of M" disclosure and the window ships a pager.
_RANKED_PAGE_WINDOW = "sort.entries.slice(pageStart, pageStart + RANKED_ROWS_PAGE_SIZE)"
_SCREEN_COMPARE_CAP = "sort.entries.slice(0, SCREEN_COMPARE_ROWS_DISPLAY_CAP)"

# The ONE sanctioned way any table on this page may render an order other than the served one: the
# shared, separately-guarded hook. A hand-rolled comparator would be a second, untested source of
# display order -- exactly what the reorder guard's narrowing below refuses to permit.
_SORT_HOOK_CALL = "useTableSort("

# The one `.sort(` this page is allowed to contain: picking the MAXIMUM of a set of session dates.
# It orders a date set to select one value, never a set of rows for display, so it is not a display
# order in any sense the reorder guard means.
_SANCTIONED_PAGE_SORT = "[...window.sessions].sort()"


def _extract_function(source: str, name: str) -> str:
    """The named function's full body by brace-walk (the `test_desk_hover_tooltip_guard.py`
    helper shape -- each guard module owning its own copy is this suite's convention).

    The parameter list is walked FIRST and skipped: every component on this page destructures its
    props, so the first `{` after the function name opens the DESTRUCTURING PATTERN, not the body.
    Walking from there returns `function Name({ rows, asOf }` and every assertion over it passes
    vacuously -- a silent false green, which is the one failure mode a guard must not have."""
    marker = f"function {name}("
    start = source.index(marker)
    paren_depth = 0
    body_start = -1
    for index in range(start + len(marker) - 1, len(source)):
        char = source[index]
        if char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
            if paren_depth == 0:
                body_start = source.index("{", index)
                break
    assert body_start != -1, f"{name}'s parameter list never closes"
    depth = 0
    for index in range(body_start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"{name}'s body never closes")


def test_the_function_extractor_returns_a_body_not_a_props_pattern():
    """A counter-test for the helper itself: every guard below is only as honest as this walk.
    If it stops at the destructuring pattern, every `in` assertion over the result silently
    passes on an empty haystack."""
    seeded = "function Widget({ rows, asOf }: Props) {\n  const x = rows.slice(0, 2);\n}\n"
    body = _extract_function(seeded, "Widget")
    assert "rows.slice(0, 2)" in body, "the extractor stopped at the props pattern"
    assert body.endswith("}")


def test_desk_page_never_reorders_rows_client_side():
    """TC-7: `rows` renders in the exact order `GET /research/desk/screen` served it in -- the
    page never sorts or reverses it. The `rank` cell renders each row's own position in that SAME
    served order, never a client-recomputed one."""
    source = _DESK_PAGE.read_text()
    match = _ROWS_REORDER_PATTERN.search(source)
    assert match is None, (
        f"apps/frontend/app/desk/page.tsx reorders `rows` client-side ({match.group(0)!r}) -- the "
        "page must render the served order verbatim; the rank cell renders each row's own served "
        "position, never a value derived from a client-side sort/reverse"
    )


def test_desk_page_rows_reorder_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_sort = "const ranked = [...rows].sort((a, b) => a.distance_bps - b.distance_bps);"
    assert _ROWS_REORDER_PATTERN.search(seeded_sort) is not None

    seeded_reverse = "const reversed = rows.reverse();"
    assert _ROWS_REORDER_PATTERN.search(seeded_reverse) is not None

    seeded_chained = "const top = rows.filter(hasTickEvidence).sort((a, b) => a.rank - b.rank);"
    assert _ROWS_REORDER_PATTERN.search(seeded_chained) is not None


def test_the_reorder_guard_deliberately_no_longer_treats_a_window_slice_as_a_reorder():
    """A deliberate, PAID-FOR narrowing, recorded rather than hidden.

    This pattern used to forbid `slice` alongside `sort`/`reverse`, and its counter-test seeded
    exactly ``rows.slice(0, 10)``. The ranked table now renders one 10-row page at a time, which
    IS a `rows.slice(` -- so the guard had to either widen a loophole (slice a differently-NAMED
    array and sail past `\\brows\\b`) or narrow honestly. It narrows honestly: a page window
    preserves the served order, the served direction, and -- via `pageStart` -- the served
    ABSOLUTE position of every row it renders, so it is not a reorder in any sense TC-7 meant.

    The narrowing is bounded by the two guards below, which pin the exact window expression and
    the exact rank expression. Deleting either one re-opens what this line gave up."""
    assert _ROWS_REORDER_PATTERN.search("const page1 = rows.slice(0, 10);") is None
    assert _ROWS_REORDER_PATTERN.search("const r = [...rows].sort(cmp);") is not None


def test_the_reorder_guard_deliberately_permits_an_operator_chosen_sort():
    """A second deliberate, PAID-FOR narrowing, recorded rather than hidden.

    TC-7's property was never "no `.sort(` appears in this file". It was: THE PAGE NEVER CHOOSES A
    DISPLAY ORDER ON THE OPERATOR'S BEHALF, and every value derived from a row's position means its
    position in the record. Every table on /desk is now sortable by clicking a column header, which
    does not touch that property -- a header the operator clicks is the operator choosing, not the
    page choosing.

    The dishonest way to permit this was available and is refused: `useTableSort(rows, ...)` sails
    straight past `_ROWS_REORDER_PATTERN` (no `.sort(` is chained off `rows`), so this guard would
    have gone on passing while the thing it was written to prevent shipped underneath it. That is
    exactly the "sail past `\\brows\\b`" loophole this module's sibling narrowing above warns
    against, so the permission is written down here instead.

    What is given up: the ranked table can now display its rows in an order the snapshot did not
    serve. What pays for it, all four pinned below:

      (a) There is exactly ONE reordering path in the product -- the shared hook, whose own
          contract (served order is the untouched default, the mapping is total, nothing is
          dropped) is guarded in test_table_sort_guards.py. The page owns no comparator.
      (b) The page contains no `.sort(`/`.reverse(` of its own beyond one sanctioned max-of-a-set.
      (c) A non-served order is always DISCLOSED, in words, by a note above the table.
      (d) A non-served order is always REVERSIBLE, by a control inside that note.

    Delete any one of these and the narrowing is no longer paid for."""
    source = _DESK_PAGE.read_text()
    table = _extract_function(source, "DeskRowsTable")

    # (a) the one sanctioned reordering path, and it is the shared, separately-tested one
    assert f"{_SORT_HOOK_CALL}rows, DESK_ROW_COLUMNS)" in table, (
        "DeskRowsTable no longer reaches its display order through the shared sort hook"
    )

    # (b) the page still owns no comparator of its own. Counted over the CODE, never the prose:
    # this page's own comments quote the call syntax while explaining why it is not used.
    code = _code(source)
    stray_sorts = re.findall(r"\.\s*(?:sort|reverse)\s*\([^\n]{0,60}", code)
    assert len(re.findall(r"\.\s*(?:sort|reverse)\s*\(", code)) == 1, (
        f"apps/frontend/app/desk/page.tsx contains a hand-rolled comparator ({stray_sorts!r}) -- "
        "every display order must go through the shared hook"
    )
    assert _SANCTIONED_PAGE_SORT in code, (
        f"the one sanctioned page sort ({_SANCTIONED_PAGE_SORT!r}) is gone -- if it was removed on "
        "purpose, tighten the count above to 0 rather than leaving this guard vacuous"
    )

    # (c) + (d) disclosed and reversible
    assert 'data-testid="desk-sort-active-note"' in _SORTABLE_HEADER.read_text(), (
        "the sort disclosure note is gone -- a table in a non-served order would be "
        "indistinguishable from the record's own ranking"
    )
    assert 'data-testid="desk-sort-reset"' in _SORTABLE_HEADER.read_text(), (
        "the reset-to-served-order control is gone -- an operator could not get back to what the "
        "record actually said"
    )


def test_the_operator_sort_narrowing_can_fail_on_a_seeded_violation():
    """Each of the four bounds above is a real check, not a restatement."""
    # (a) a filtered input would silently drop rows from the pager
    seeded_filtered = "function DeskRowsTable() { useTableSort(rows.filter(f), DESK_ROW_COLUMNS) }"
    assert f"{_SORT_HOOK_CALL}rows, DESK_ROW_COLUMNS)" not in seeded_filtered

    # (b) a hand-rolled comparator beside the sanctioned one is two hits, not one
    seeded_two = f"const a = {_SANCTIONED_PAGE_SORT};\nconst b = [...entries].sort(cmp);"
    assert len(re.findall(r"\.\s*(?:sort|reverse)\s*\(", _code(seeded_two))) == 2

    # ...and the stripper really does hide prose, so the count above cannot be satisfied (or
    # tripped) by a comment that merely names the syntax.
    assert re.findall(r"\.\s*sort\s*\(", _code("// never call .sort( here\nconst a = 1;")) == []
    assert re.findall(r"\.\s*sort\s*\(", _code("{/* not a .sort( either */}\nconst a = 1;")) == []


def test_desk_page_slices_rows_only_for_the_ranked_page_window():
    """The page window is the ONLY slice of the ranked rows on the page, and it is the exact
    contiguous expression -- any other slice could drop, overlap or re-origin rows without the rank
    cell noticing.

    A deliberate, PAID-FOR re-pointing, recorded rather than hidden. The window used to be pinned
    against `rows` because `rows` WAS the only order this table could render. The operator can now
    choose another (see the narrowing note on the reorder guard above), so the window is pinned
    against the DISPLAYED order instead -- `sort.entries`, which is `rows` verbatim by default.

    What that gives up: `_ROWS_SLICE_PATTERN` no longer has a live hit to count, so the assertion
    that `rows` itself is never sliced becomes a `== []` rather than a `== 1`. What pays for it: the
    absolute-position property `pageStart` used to carry is now carried EXPLICITLY by `servedIndex`
    (pinned by the rank guard below), which is strictly stronger -- `pageStart` could only describe
    a position under the served order, while `servedIndex` survives any order at all. The window
    remaining total is pinned separately, in
    apps/backend/tests/test_table_sort_guards.py::test_the_hook_is_a_total_mapping_of_its_input."""
    source = _DESK_PAGE.read_text()
    table = _extract_function(source, "DeskRowsTable")
    assert _ROWS_SLICE_PATTERN.findall(source) == [], (
        "`rows` is sliced directly in apps/frontend/app/desk/page.tsx -- the ranked table windows "
        "the DISPLAYED order (`sort.entries`), so a raw `rows` slice would bypass the sort and "
        "render a page of the served order under a sorted table's headers"
    )
    file_hits = _ORDERED_SLICE_PATTERN.findall(source)
    assert len(file_hits) == 2, (
        f"the displayed order is sliced {len(file_hits)} time(s) in "
        "apps/frontend/app/desk/page.tsx -- the only sanctioned slices are DeskRowsTable's page "
        "window and ScreenCompareTable's display cap, both pinned below"
    )
    assert len(_ORDERED_SLICE_PATTERN.findall(table)) == 1, (
        "the one page-window slice is not inside DeskRowsTable"
    )
    assert _RANKED_PAGE_WINDOW in table, (
        f"DeskRowsTable no longer windows via {_RANKED_PAGE_WINDOW!r}"
    )
    assert "pageEntries.map((entry) =>" in table, (
        "DeskRowsTable maps something other than its own page window"
    )

    # The second sanctioned slice: a shipped display cap that predates sorting. It now caps the
    # DISPLAYED order rather than the served one, and that ordering is load-bearing -- capping
    # first would sort a window the operator never chose, so "the top 50 by rank change" would
    # quietly mean "whichever of the first 50 SERVED rows rank highest".
    compare = _extract_function(source, "ScreenCompareTable")
    assert _SCREEN_COMPARE_CAP in compare, (
        f"ScreenCompareTable no longer caps via {_SCREEN_COMPARE_CAP!r}"
    )
    assert compare.index("useTableSort(") < compare.index(_SCREEN_COMPARE_CAP), (
        "ScreenCompareTable caps BEFORE it sorts -- the cap must be a window over the chosen "
        "order, not a pre-selection the sort is then applied inside"
    )
    assert 'data-testid="desk-screen-compare-cap-note"' in compare, (
        "the cap lost its own disclosure -- a truncated table that does not say so is the one "
        "thing a cap may never be"
    )


def test_the_page_window_guard_can_fail_on_a_seeded_violation():
    """A lint that cannot fail proves nothing -- both halves of the swap above are checked."""
    assert _ROWS_SLICE_PATTERN.findall("const p = rows.slice(0, 10);") != []
    assert _ORDERED_SLICE_PATTERN.findall("const p = rows.slice(0, 10);") == []
    assert len(_ORDERED_SLICE_PATTERN.findall(_RANKED_PAGE_WINDOW)) == 1
    assert len(_ORDERED_SLICE_PATTERN.findall(_SCREEN_COMPARE_CAP)) == 1
    # A THIRD slice of a displayed order anywhere on the page must fail the count above.
    seeded_third = f"{_RANKED_PAGE_WINDOW}\n{_SCREEN_COMPARE_CAP}\nsort.entries.slice(0, 5)"
    assert len(_ORDERED_SLICE_PATTERN.findall(seeded_third)) == 3


def test_desk_ranked_rows_render_an_absolute_rank_across_pages():
    """Row 11 reads 11, never 1: the rank cell is the row's position in the SERVED array.

    This used to mean "the window offset plus the map index", which was only correct while the
    served order was the ONLY order. Under an operator-chosen sort that expression names where a row
    happens to sit on screen, so a row served 11th could render as 1. The cell now reads the row's
    own `servedIndex`, which is the position the snapshot recorded it at under every display order.

    Both superseded forms are asserted ABSENT, not merely the old one: `index + 1` is page-relative
    (page 2 would restart at 1) and `pageStart + index + 1` is display-relative (a sorted page 1
    would restart at 1). Either would silently contradict the snapshot's own recorded order."""
    table = _extract_function(_DESK_PAGE.read_text(), "DeskRowsTable")
    assert "rank={entry.servedIndex + 1}" in table, (
        "the ranked table does not render the row's SERVED position as its rank"
    )
    assert "rank={index + 1}" not in table, (
        "the ranked table passes a PAGE-relative rank -- page 2 would restart the briefing at 1 "
        "and silently contradict the snapshot's own recorded order"
    )
    assert "rank={pageStart + index + 1}" not in table, (
        "the ranked table passes a DISPLAY-relative rank -- correct only while the served order is "
        "the only order, and this table can now be sorted"
    )


def test_the_absolute_rank_guard_can_fail_on_a_seeded_violation():
    page_relative = (
        "function DeskRowsTable() { pageEntries.map((row, index) => <DeskRow rank={index + 1} />) }"
    )
    body = _extract_function(page_relative, "DeskRowsTable")
    assert "rank={entry.servedIndex + 1}" not in body
    assert "rank={index + 1}" in body

    display_relative = (
        "function DeskRowsTable() { pageEntries.map((row, index) => "
        "<DeskRow rank={pageStart + index + 1} />) }"
    )
    body = _extract_function(display_relative, "DeskRowsTable")
    assert "rank={entry.servedIndex + 1}" not in body
    assert "rank={pageStart + index + 1}" in body


# EVERY table on /desk. Each must reach any non-served display order through the one shared hook --
# a hand-rolled comparator would be a second, untested source of display order, and the whole
# reorder narrowing above is written on the premise that there is exactly one.
#
# The last six belong to sections that render COLLAPSED. They were briefly excluded, while those
# sections were suppressed outright and wiring a control into them would have been dead code; the
# sections are back behind an expand control, so the exclusion is gone and this tuple is once again
# the whole page.
_SORTABLE_DESK_TABLES = (
    "DeskRowsTable",
    "DeskSkipTable",
    "ForwardRunsNote",
    "ForwardTouchTable",
    "DeskForwardSummaryView",
    "DeskForwardTable",
    "BackscanRunsTable",
    "PlaybookSignalsTable",
    "PlaybookAbsencesTable",
    "PlaybookOccurrenceList",
    "PlaybookSummaryView",
    "PlaybookRunsNote",
    "TopupRunsTable",
    "IndexReconciliationTable",
    "ScreenRunsTable",
    "ScreenCompareTable",
    "PlaybookEvidenceCellsTable",
    "PlaybookEvidenceBreachTable",
)


def test_every_rendered_desk_table_sorts_through_the_one_shared_primitive():
    source = _DESK_PAGE.read_text()
    for name in _SORTABLE_DESK_TABLES:
        body = _extract_function(source, name)
        assert _SORT_HOOK_CALL in body, (
            f"{name} does not use the shared sort hook -- either it is unsortable (and the user "
            "asked for every column of every table to sort) or it hand-rolled a second comparator"
        )
        assert "<SortableHeader" in body, (
            f"{name} renders its own header cells instead of the shared, accessibility-guarded "
            "SortableHeader"
        )
        assert "<TableSortNote" in body, (
            f"{name} can be sorted without disclosing it -- a non-served order must always say so "
            "and always be reversible"
        )


# The two summary views whose rows come in PAIRS: a measured line and its baseline, joined by a
# `rowSpan={2}` label cell. (The playbook one adds a third, conditional occurrences row.)
_PAIRED_ROW_SUMMARIES = (
    ("DeskForwardSummaryView", "useTableSort(sides", "PlaybookSummaryCells"),
    ("PlaybookSummaryView", "useTableSort(poolKeys", "ForwardSummaryCells"),
)


def test_the_paired_row_summaries_sort_groups_and_never_individual_rows():
    """A correctness guard, not a taste one.

    Each pool/side owns two `<tr>`s joined by a `rowSpan={2}` chip that labels BOTH. Ordering the
    rows independently would slide a baseline line out from under its own label and place it under
    a different pool's -- a wrong number stated confidently, which is the worst failure this page
    can have. Ordering the GROUPS moves each pair as a unit by construction.

    The hook is therefore handed the group keys (`sides` / `poolKeys`), never the rendered rows."""
    source = _DESK_PAGE.read_text()
    for name, group_call, foreign_cells in _PAIRED_ROW_SUMMARIES:
        body = _extract_function(source, name)
        assert group_call in body, (
            f"{name} no longer sorts its GROUP keys -- sorting its rows would separate a baseline "
            "line from the rowSpan label that names it"
        )
        assert "rowSpan={2}" in body, (
            f"{name} lost the rowSpan that joins each pair -- the group-sorting rationale above "
            "depends on the pair being one labelled unit"
        )
        assert foreign_cells not in body, (
            f"{name} renders the OTHER summary's cells -- the two were extracted separately and "
            "must not drift into one another"
        )
        # The hook must not be pointed at the served summary map itself: that is a record of
        # measured values, not a list of rows, and sorting it would be meaningless.
        assert f"{_SORT_HOOK_CALL}record.summary" not in body


def test_the_group_sorting_guard_can_fail_on_a_seeded_violation():
    seeded = (
        "function PlaybookSummaryView() { const s = useTableSort(rowsForEveryLine, C); "
        "return <tr rowSpan={2} />; }"
    )
    body = _extract_function(seeded, "PlaybookSummaryView")
    assert "useTableSort(poolKeys" not in body


def test_a_column_with_no_single_served_value_opts_out_rather_than_ordering_arbitrarily():
    """`source` labels which of two paired lines a row is; `outcomes` renders several served
    counters side by side. Ordering on either would silently pick a winner among equals, and summing
    the counters would be a number no run ever recorded."""
    source = _DESK_PAGE.read_text()
    for name in ("DeskForwardSummaryView", "PlaybookSummaryView"):
        body = _extract_function(source, name)
        assert 'id: "source", label: "source", kind: "text", sortable: false' in body, (
            f"{name}'s `source` column is sortable -- it names which line of a pair a row is, not a "
            "value the record served"
        )
    # Read off the module-level column declaration, not the component body -- these columns are
    # hoisted so the hook's memo sees a stable identity.
    start = source.index("const BACKSCAN_RUN_COLUMNS")
    backscan_columns = source[start : source.index("function BackscanRunsTable")]
    assert 'id: "outcomes"' in backscan_columns and "sortable: false" in backscan_columns, (
        "the back-scan `outcomes` column is sortable -- it renders several counters, so ordering "
        "would pick one arbitrarily and summing them would invent a number"
    )


def test_sorting_the_ranked_table_rewinds_its_pager():
    """Re-ordering the whole table while parked on page 4 strands the operator in the middle of an
    order they have not seen the start of. The rewind is plain state in the event handler, never a
    twelfth effect -- the page's effect census is pinned."""
    table = _extract_function(_DESK_PAGE.read_text(), "DeskRowsTable")
    assert "sort.toggle(columnId);\n    setPage(1);" in table, (
        "toggling a sort no longer rewinds the ranked table's pager"
    )
    assert "sort.reset();\n    setPage(1);" in table, (
        "resetting to the served order no longer rewinds the ranked table's pager"
    )
    assert "useEffect" not in table, (
        "DeskRowsTable introduced an effect -- the pager rewind must stay in the event handler"
    )


def test_the_ranked_tables_measured_column_widths_survive_the_sortable_headers():
    """The thirteen `<colgroup>` widths are MEASURED values summing to the 1214px container, which
    is what keeps `scrollWidth === clientWidth` at 1440px. Adding a control inside each header must
    not have moved any of them."""
    table = _extract_function(_DESK_PAGE.read_text(), "DeskRowsTable")
    widths = re.findall(r'<col className="w-\[(\d+)px\]" />', table)
    assert len(widths) == 13, f"the ranked table no longer declares 13 column widths ({widths})"
    assert sum(int(width) for width in widths) == 1214, (
        f"the measured column widths no longer sum to 1214px (got {sum(int(w) for w in widths)}) -- "
        "the ranked table would scroll horizontally inside its own container"
    )
    assert "revealOnHover" in table, (
        "the ranked table's headers show their sort glyph permanently -- on a `table-fixed` layout "
        "with measured widths that widens the idle header row"
    )


def test_the_ranked_table_resets_to_page_one_when_the_displayed_snapshot_changes():
    """The reset is a React `key`, not a twelfth useEffect (the chain guard pins the page at
    exactly 11). Deleting the key is a silent defect: selecting a 10-row screen from history
    while on page 4 would leave the operator staring at an empty table."""
    populated = _extract_function(_DESK_PAGE.read_text(), "DeskPopulatedScreen")
    assert "<DeskRowsTable" in populated, "DeskRowsTable is no longer rendered by DeskPopulatedScreen"
    assert "key={snapshot.id}" in populated, (
        "the ranked table has no `key={snapshot.id}` -- its page state would survive a snapshot "
        "switch, stranding the operator on a page the new snapshot may not have"
    )


# goal-desk-iter-24 (J-16) TC-7 (b): every `data-testid` a shipped journey's golden replay script,
# guard test, or hover-tooltip contract depends on is still present in the source after the
# reflow -- the reflow may move a disclosure's markup (a new element, a new line inside the SAME
# row), but it must never drop, hide, or rename the testid itself. "the compute controls" (goal.md
# J-16 step 4) are the three primary trigger buttons this page ships (Run Screen / Top-up /
# Reconcile Index) -- untouched by this iteration's ranked-row-only reflow, checked here anyway as
# the cheapest possible proof nothing regressed. `desk-refresh-all-button` is the FOURTH compute
# control by that same definition (it drives all three of the above in sequence, plus the
# membership fetch). No golden script targets it and none ever should -- it is a write path, and
# every shipped desk golden is deliberately read-only -- so this static presence pin is the ONLY
# automated proof it still ships at all. Its behavioural guards live in
# test_desk_refresh_chain_guard.py.
_REQUIRED_DESK_TESTIDS = (
    "desk-screen-rows-table",
    "desk-row-drill-in",
    "desk-row-side",
    "desk-row-band-class",
    "desk-row-distance",
    "desk-row-score",
    "desk-coverage-badges",
    "desk-coverage-badge",
    "desk-row-tick-evidence",
    "desk-row-basis",
    "desk-row-history",
    "desk-row-band",
    "desk-row-opposite",
    "desk-row-levels",
    "desk-skip-row",
    # Screen History is a year-at-a-glance calendar, not a table: `desk-history-row` /
    # `desk-history-table` retired with it (one snapshot per date removed the near-duplicate rows
    # the table existed to tell apart -- see `DeskHistoryCalendar`'s own comment). `desk-history-day`
    # is the click target J-05/J-08's goldens now use, still carrying `data-screen-date`.
    "desk-history-calendar",
    "desk-history-day",
    "desk-history-year-label",
    "desk-history-prev-year",
    "desk-history-next-year",
    # Selecting a history date is a fetch, and it used to be a SILENT one: the page kept rendering
    # the previous snapshot with nothing indicating a click had registered. This note (plus the
    # clicked cell's own pulse) is what says the read is in flight and for which date.
    "desk-history-pending",
    "desk-provenance",
    "desk-title",
    "desk-run-screen-button",
    "desk-topup-button",
    "desk-reconcile-button",
    "desk-refresh-all-button",
    # Forward-test era: the as-of range fields (the chain's one date source) and the Forward
    # Returns panel's primary surfaces -- same static-presence rationale as the compute controls
    # above (no golden ever clicks a write path; presence is the cheapest proof they still ship).
    "desk-as-of-from-input",
    "desk-as-of-to-input",
    "desk-forward-section",
    "desk-forward-table",
    "desk-forward-compute-button",
    # The ranked table's page window: the pager and its disclosure. Presence-only, same rationale
    # as the compute controls above -- the window itself is proved by the slice/rank guards.
    "desk-rows-pagination",
    "desk-rows-prev-page",
    "desk-rows-next-page",
    "desk-rows-page-note",
)


def _missing_testids(source: str) -> list[str]:
    """Which required testids are not ACTUALLY assigned in ``source``.

    Matches the assignment ``testid="<id>"`` rather than a bare substring, which covers both the
    literal ``data-testid="<id>"`` attribute and the ``testid=`` prop the shared `EmptyState`/
    tooltip components take. The bare-substring form this guard used before was satisfied by a
    PROSE COMMENT naming a testid -- live-verified: after the Screen History table was replaced by
    the calendar, `desk-history-row` was gone from every element on the page and the guard still
    passed, because a comment further down mentioned it. A guard that a comment can satisfy is not
    a guard."""
    return [testid for testid in _REQUIRED_DESK_TESTIDS if f'testid="{testid}"' not in source]


def test_desk_page_keeps_every_shipped_testid_after_the_reflow():
    """TC-7: every testid a shipped journey's golden script/guard test/tooltip contract depends
    on is still ASSIGNED in the reflowed source -- the layout changed, nothing else did."""
    missing = _missing_testids(_DESK_PAGE.read_text())
    assert not missing, (
        f"apps/frontend/app/desk/page.tsx is missing testid(s) {missing} after the reflow -- a "
        "shipped journey's golden script/guard test/tooltip contract depends on each of these "
        "remaining present with the same text"
    )


def test_desk_page_testid_presence_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    assert _missing_testids("const x = 1;") == list(_REQUIRED_DESK_TESTIDS)


def test_desk_page_testid_presence_guard_is_not_satisfied_by_a_mere_mention():
    """The tightened form's own counter-test: a testid named only in a comment (or in any other
    prose) does not count as shipped."""
    mentioned_only = "// never reuse desk-history-day as a click target here\n"
    assert "desk-history-day" in _missing_testids(mentioned_only)


# --- Screen History calendar (one snapshot per date) ----------------------------------------------


_EMPTY_DAY_BRANCH = "if (meta === undefined) {"


def _empty_day_branch(body: str) -> str:
    """``DeskHistoryDayCell``'s no-screen branch, by brace-walk from its own `if`.

    Deliberately NOT "everything before the recorded branch's first marker attribute": that would
    make the guard depend on the ORDER attributes happen to be written in, which is exactly the
    kind of incidental coupling that turns a guard into a trip hazard for the next editor."""
    start = body.index(_EMPTY_DAY_BRANCH)
    depth = 0
    for index in range(body.index("{", start), len(body)):
        if body[index] == "{":
            depth += 1
        elif body[index] == "}":
            depth -= 1
            if depth == 0:
                return body[start : index + 1]
    raise AssertionError("DeskHistoryDayCell's no-screen branch never closes")


def test_the_empty_day_branch_extractor_returns_only_that_branch():
    """A counter-test for the helper: if the walk overshoots into the recorded branch, every
    assertion below passes on the wrong haystack."""
    branch = _empty_day_branch(_extract_function(_DESK_PAGE.read_text(), "DeskHistoryDayCell"))
    assert 'data-has-screen="false"' in branch
    assert 'data-has-screen="true"' not in branch


def test_every_calendar_day_cell_is_a_plain_button_and_an_empty_day_is_disabled():
    """The calendar's cells are ordinary click targets and nothing more: a `<button
    type="button">` (never a form submit), and a day with no recorded screen is `disabled` rather
    than a live target that would fire a fetch for a snapshot that does not exist."""
    body = _extract_function(_DESK_PAGE.read_text(), "DeskHistoryDayCell")

    buttons = body.count("<button")
    assert buttons == 2, (
        f"DeskHistoryDayCell renders {buttons} button(s) -- expected exactly two (the no-screen "
        "branch and the recorded branch); a new branch has to state its own click semantics here"
    )
    assert body.count('type="button"') == 2, (
        "every calendar day cell must be an explicit type=\"button\" -- a bare <button> inside a "
        "form submits it"
    )
    empty_branch = _empty_day_branch(body)
    assert "disabled" in empty_branch, (
        "a calendar day with no recorded screen must be disabled -- a live target there would fire "
        "a fetch for a snapshot that was never recorded"
    )


def test_a_calendar_cell_only_carries_a_screen_id_when_a_screen_was_recorded():
    """`data-screen-id` is the id a golden clicks and the page then fetches. The no-screen branch
    must not carry one at all -- an id there would be invented, not served."""
    body = _extract_function(_DESK_PAGE.read_text(), "DeskHistoryDayCell")
    empty_branch = _empty_day_branch(body)
    assert "data-screen-id" not in empty_branch
    assert 'data-screen-id={meta.id}' in body


def test_the_calendar_never_renders_a_day_its_month_does_not_have():
    """A fixed 31-row grid is only honest if 30 February renders as blank space rather than as a
    cell claiming a date that never existed."""
    body = _extract_function(_DESK_PAGE.read_text(), "DeskHistoryCalendar")
    assert "isRealDayOfMonth(" in body, (
        "DeskHistoryCalendar must skip days its month does not have -- the 31-row grid otherwise "
        "renders 30/31 February as real dates"
    )


def test_a_proven_non_session_day_is_never_selectable():
    """The calendar used to offer every Saturday, Sunday and market holiday as an ordinary
    tradable date, because it mirrored whatever the store held and the chain had recorded a screen
    for each of them. A snapshot for a day the market was shut carries a wall map copied from the
    PRIOR session and a forward measurement that is empty by construction, so opening one tells a
    reader nothing true about that date.

    The cell must therefore be `disabled` whenever `nonSession` -- in BOTH branches: the no-screen
    branch (the normal state once the non-session snapshots are cleaned up) is already disabled,
    and the recorded branch must become so. `data-session` marks it for the eye and for a test."""
    body = _extract_function(_DESK_PAGE.read_text(), "DeskHistoryDayCell")
    assert "disabled={nonSession}" in body, (
        "DeskHistoryDayCell's recorded branch must refuse to open a snapshot recorded for a date "
        "the daily bars prove did not trade -- otherwise a weekend is clickable again"
    )
    assert 'data-session={nonSession ? "false"' in body


def test_a_non_session_is_only_ever_claimed_when_the_daily_bars_prove_it():
    """The fail-open half of the same rule, and the more important one. A date is called closed
    ONLY when the recorded daily bars bracket it and do not contain it; a failed read, a store with
    no daily series, or a date outside the recorded span must all render exactly as they did before
    any of this existed. No hardcoded holiday table, no weekday arithmetic -- `desk_sessions.py`'s
    contract, mirrored client-side rather than re-invented."""
    source = _DESK_PAGE.read_text()
    window = _extract_function(source, "provenSessionWindow")
    assert "if (result === null || !result.ok || result.data === null) return null;" in window
    assert "if (evidence.anchor_symbols.length === 0) return null;" in window
    assert "if (evidence.from === null || evidence.through === null) return null;" in window

    proven = _extract_function(source, "isProvenNonSession")
    assert "if (window === null) return false;" in proven
    assert "if (isoDate < window.from || isoDate > window.through) return false;" in proven
    assert "return !window.sessions.has(isoDate);" in proven

    # No calendar arithmetic anywhere in the decision: a `getDay()`/`getUTCDay()` weekend test or a
    # holiday list would answer where the bars are silent, which is precisely the claim this page
    # must not make.
    for banned in ("getDay()", "getUTCDay()", "HOLIDAY", "isWeekend"):
        assert banned not in window and banned not in proven


def test_the_calendar_guards_can_fail_on_a_seeded_violation():
    """The lints CAN fail -- lints that cannot fail prove nothing."""
    seeded = (
        'function DeskHistoryDayCell({ meta }: Props) {\n'
        '  if (meta === undefined) {\n'
        '    return <button data-screen-id="invented" data-has-screen="false">·</button>;\n'
        "  }\n"
        '  return <button data-has-screen="true">{day}</button>;\n'
        "}\n"
    )
    body = _extract_function(seeded, "DeskHistoryDayCell")
    empty_branch = _empty_day_branch(body)
    assert body.count('type="button"') != 2  # the type is missing entirely
    assert "disabled" not in empty_branch  # the dead cell is still clickable
    assert "data-screen-id" in empty_branch  # and carries an invented id

    assert "isRealDayOfMonth(" not in "function DeskHistoryCalendar({ screens }: Props) {\n}\n"


# goal-desk-iter-24 (J-16) TC-6/TC-7 (c): the reflow's own regression guard for the defect the
# iter-24 review caught -- dropping a ranked cell's in-cell label prefix ALSO deletes the literal
# page text a stored golden replay script asserts through `page.get_by_text`, which matches
# VISIBLE DOM TEXT only (the composite drill-in `title` carrying the same word is invisible to it).
# TC-6 allows zero golden-script edits, so the two cells a golden pins by literal text
# (`desk-row-band` <- J-13.json, `desk-row-opposite` <- J-14.json) must keep the prefix WORD the
# script's expected text starts with. This guard reads BOTH artifacts and ties them together, so a
# future prefix drop fails here (a fast, keyless, browser-free test) instead of only in a browser
# replay lane. The other three disclosure cells (basis/history/levels) are deliberately absent from
# this list: no stored golden asserts their prefixed text (J-08 pins "d before as-of", J-11 pins
# "sessions", J-15 has no script), which is exactly why dropping THOSE prefixes was safe.
_JOURNEY_SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "runs" / "goal-session-desk" / "journey-scripts"
)

_GOLDEN_TEXT_PINNED_CELLS = (
    ("J-13.json", "desk-row-band", "band "),
    ("J-14.json", "desk-row-opposite", "opposite "),
)


def _desk_cell_source(source: str, testid: str) -> str:
    """The source of the single `<td ... data-testid="<testid>"> ... </td>` block."""
    start = source.index(f'data-testid="{testid}"')
    end = source.index("</td>", start)
    return source[start:end]


def _golden_expected_texts(script_name: str) -> list[str]:
    """Every literal `text` a golden script asserts (step `expect` action or `expect` clause)."""
    import json

    data = json.loads((_JOURNEY_SCRIPTS_DIR / script_name).read_text())
    texts: list[str] = []
    for step in data.get("steps", []):
        for holder in (step.get("action") or {}, step.get("expect") or {}):
            text = holder.get("text")
            if isinstance(text, str):
                texts.append(text)
    return texts


def test_desk_row_cells_keep_the_label_prefix_their_golden_script_asserts():
    """TC-6: the `band`/`opposite` cells still render the prefix WORD their stored golden replay
    script's expected page text starts with -- dropping it fails J-13/J-14 on replay."""
    source = _DESK_PAGE.read_text()
    for script_name, testid, prefix in _GOLDEN_TEXT_PINNED_CELLS:
        pinned = [t for t in _golden_expected_texts(script_name) if t.startswith(prefix)]
        assert pinned, (
            f"{script_name} no longer asserts any page text starting with {prefix!r} -- this pin "
            f"has gone vacuous; re-derive it from the script's own expected texts"
        )
        cell = _desk_cell_source(source, testid)
        assert f"`{prefix}" in cell, (
            f"apps/frontend/app/desk/page.tsx's {testid} cell no longer renders the {prefix!r} "
            f"label prefix, but {script_name} asserts the literal page text {pinned[0]!r} via "
            f"page.get_by_text (visible DOM text only -- a `title` attribute does not satisfy it). "
            f"TC-6 permits zero golden-script edits, so this cell must keep the prefix word."
        )


def test_desk_row_label_prefix_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_cell = (
        'data-testid="desk-row-band">\n'
        "  {row.reference_close == null\n"
        "    ? `${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`\n"
        "    : `${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}`}\n"
        "</td>"
    )
    cell = _desk_cell_source(seeded_cell, "desk-row-band")
    assert "`band " not in cell

    # and the pin itself is non-vacuous: J-13/J-14 really do assert those literal texts today
    assert any(t.startswith("band ") for t in _golden_expected_texts("J-13.json"))
    assert any(t.startswith("opposite ") for t in _golden_expected_texts("J-14.json"))


# --- goal-playbook-iter-12 (J-11 passenger, TC-14): the Playbook Signals date input's amber border -
# ASOF_INPUT_CLASS's own `border-slate-700` and a plain, conditionally-appended `border-amber-500`
# are an equal-CSS-specificity Tailwind collision (both single-class border-color utilities), so the
# COMPILED stylesheet's own utility order silently decides the tie regardless of this class list's
# order in the JSX -- and it is `border-slate-700` that wins live, leaving the input grey on an
# invalid value. The fix (Tailwind's `!` important modifier) is scoped to `desk-playbook-date-input`
# alone: `ASOF_INPUT_CLASS` itself and its other four call sites (Refresh Data From/To -- the SAME
# collision, deliberately carried; Backscan/Deep-backfill From/To -- never had the amber affordance
# at all) must stay byte-unchanged.


def _asof_input_class_expr(source: str, testid: str) -> str:
    """The `className={...}` JSX expression immediately following one
    `data-testid="<testid>"` input -- found by a brace-walk from the FIRST `className={` after the
    testid (this page's own consistent attribute order: data-testid precedes className on every
    ASOF-styled input), mirroring `_extract_function`'s own walk-from-a-known-anchor style."""
    start = source.index(f'data-testid="{testid}"')
    class_start = source.index("className={", start)
    open_brace = class_start + len("className=")
    depth = 0
    for index in range(open_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[class_start : index + 1]
    raise AssertionError(f"{testid}'s className expression never closes")


def test_desk_playbook_date_input_amber_border_fix_is_scoped_to_itself_only():
    """TC-14: `desk-playbook-date-input`'s own className now forces the amber border to win on an
    invalid value; `ASOF_INPUT_CLASS`'s own definition, the Refresh Data From/To inputs sharing the
    IDENTICAL (still unfixed) collision, and the Backscan/Deep-backfill From/To inputs (which never
    had the amber affordance) all stay byte-unchanged."""
    source = _DESK_PAGE.read_text()

    playbook_input_class = _asof_input_class_expr(source, "desk-playbook-date-input")
    assert '"!border-amber-500"' in playbook_input_class, (
        "desk-playbook-date-input's className must force the amber border with Tailwind's `!` "
        "important modifier -- a bare `border-amber-500` loses the equal-specificity tie against "
        "ASOF_INPUT_CLASS's own border-slate-700 and the input stays grey on an invalid value"
    )

    # ASOF_INPUT_CLASS's own definition is untouched: still carries border-slate-700, never amber.
    class_def_start = source.index("const ASOF_INPUT_CLASS =")
    class_def_end = source.index(";", class_def_start)
    class_def = source[class_def_start:class_def_end]
    assert "border-slate-700" in class_def
    assert "amber" not in class_def

    # The Refresh Data From/To inputs share the IDENTICAL, still-UNFIXED collision (carried,
    # per this iteration's own scoping decision) -- neither gained the `!` fix.
    unfixed_pattern = '${ASOF_INPUT_CLASS} ${dayRangeError !== null ? "border-amber-500" : ""}`'
    assert source.count(unfixed_pattern) == 2, (
        "the Refresh Data From/To inputs' own border collision must stay byte-unchanged and "
        "unforced -- only desk-playbook-date-input is fixed this iteration"
    )
    assert "!border-amber-500" not in unfixed_pattern

    # The Backscan/Deep-backfill From/To inputs never had the amber affordance at all -- still four
    # bare `className={ASOF_INPUT_CLASS}` call sites, none of them this one.
    assert source.count("className={ASOF_INPUT_CLASS}") == 4


def test_desk_playbook_date_input_amber_border_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded = (
        'data-testid="desk-playbook-date-input"\n'
        "          value={dateInput}\n"
        "          className={`${ASOF_INPUT_CLASS} "
        '${validated.error !== null ? "border-amber-500" : ""}`}\n'
    )
    extracted = _asof_input_class_expr(seeded, "desk-playbook-date-input")
    assert "!border-amber-500" not in extracted
    assert "border-amber-500" in extracted  # the pre-fix shape really is present to catch


def test_the_asof_class_expr_extractor_returns_the_right_inputs_own_expression():
    """A counter-test for the helper itself: it must not accidentally return a DIFFERENT input's
    className (e.g. the first one it happens to find in the file) -- each of the five ASOF-styled
    inputs must extract its OWN expression."""
    seeded = (
        'data-testid="alpha"\n'
        '          className={ASOF_INPUT_CLASS}\n'
        'data-testid="beta"\n'
        "          className={`${ASOF_INPUT_CLASS} "
        '${cond ? "border-amber-500" : ""}`}\n'
    )
    assert _asof_input_class_expr(seeded, "alpha") == "className={ASOF_INPUT_CLASS}"
    beta = _asof_input_class_expr(seeded, "beta")
    assert "border-amber-500" in beta and "ASOF_INPUT_CLASS" in beta


# --- Band context on /desk (docs/playbook-detector-spec.md §6) -------------------------------------
# The location columns, the near-band display filter, and the evidence split are all pass-throughs of
# served fields. These guards pin what the page must SAY about them, because the copy is the part
# that could quietly turn a description of where a signal happened into a claim about what it means.

_BAND_CONTEXT_TESTIDS = (
    "desk-playbook-signal-wall-behind",
    "desk-playbook-signal-wall-ahead",
    "desk-playbook-signal-room",
    "desk-playbook-band-filter",
    "desk-playbook-band-filter-count",
    "desk-playbook-inside-filter",
    "desk-evidence-signal-n-positive",
    "desk-evidence-baseline-n-positive",
    "desk-evidence-band-context",
    "desk-evidence-band-context-basis",
    "desk-evidence-band-context-table",
    "desk-evidence-cell-backing",
    "desk-evidence-cell-room",
)


def test_desk_page_ships_every_band_context_testid():
    source = _DESK_PAGE.read_text()
    missing = [
        testid for testid in _BAND_CONTEXT_TESTIDS if f'data-testid="{testid}"' not in source
    ]
    assert not missing, f"apps/frontend/app/desk/page.tsx is missing band-context testid(s) {missing}"


def test_the_band_context_testid_guard_can_fail_on_a_seeded_violation():
    seeded = '<div data-testid="desk-playbook-signal-wall-behind" />'
    missing = [testid for testid in _BAND_CONTEXT_TESTIDS if f'data-testid="{testid}"' not in seeded]
    assert missing, "a source shipping only ONE of the testids must still be reported as missing"


def test_the_band_filter_calls_itself_a_display_filter():
    """The filter hides ROWS, never records — and it must say so where an operator reads it. A
    filter that looked like it narrowed the evidence would misrepresent what the payload still
    serves and still counts."""
    source = _DESK_PAGE.read_text()
    assert "a display filter; every signal stays recorded and served" in source
    assert "recorded signals, none hidden" in source


def test_the_band_filter_defaults_to_all_recorded():
    """Nothing is hidden until an operator asks for it — pinned on the exact declaration so a
    future edit cannot quietly start the page in a filtered state."""
    source = _DESK_PAGE.read_text()
    assert (
        'const [playbookBandFilter, setPlaybookBandFilter] = useState<PlaybookBandFilter>("all");'
        in source
    )


def test_band_context_copy_carries_no_advice_forecast_or_edge_claim():
    """Every band-context string the page ships is run through the project's own copy lint rather
    than eyeballed."""
    source = _DESK_PAGE.read_text()
    phrases = [
        "all recorded signals",
        "at a wall behind",
        "at a wall behind with room ≥ 1×",
        "a display filter; every signal stays recorded and served",
        "recorded signals, none hidden",
        "By location relative to the tradable band map",
        # Source-wrapped in the basis line, so the guard pins the fragment that survives the wrap.
        "band map has not been computed yet",
        "recorded measurements greater than zero",
        "with no derivable",
        "off one, ",
        "with nothing\n        behind",
    ]
    for phrase in phrases:
        assert phrase in source, f"expected band-context copy missing: {phrase!r}"
        assert find_violations(phrase) == [], phrase


def test_the_structure_drill_in_captions_the_served_band_context():
    """The caption is the SERVED sentence, rendered verbatim: the /structure page must not compose
    its own from the band's parts, or the caption and the bands the chart draws could disagree."""
    source = (_FRONTEND_ROOT / "app" / "structure" / "page.tsx").read_text()
    assert 'data-testid="structure-playbook-band-context"' in source
    assert "{playbookBandContext.caption}" in source


# --- Screen History <-> Playbook Signals session linkage --------------------------------------------
# Clicking a day on the calendar is a statement about which session the desk is looking at. If the
# Playbook section kept its own date, the page would show two different sessions at once under one
# heading -- the kind of quiet incoherence that makes a reader trust the wrong numbers.


def test_selecting_a_history_day_moves_the_playbook_to_that_session():
    """The calendar click sets the Playbook's session date from the screen's OWN served
    `screen_date` -- never a date the page derived for itself."""
    source = _DESK_PAGE.read_text()
    assert "setPlaybookDateInput(result.data.screen_date);" in source


def test_reverting_to_the_latest_screen_releases_the_playbook_date():
    """The inverse: going back to Latest must not strand the Playbook on whichever historical day
    was last clicked. Blank is the section's own honest default (the newest recorded session)."""
    source = _DESK_PAGE.read_text()
    show_latest = source[source.index("function handleShowLatest()") :]
    show_latest = show_latest[: show_latest.index("\n  }")]
    assert 'setPlaybookDateInput("")' in show_latest


def test_the_linkage_guard_can_fail_on_a_seeded_violation():
    """Non-vacuous: a `handleShowLatest` that only reverts the snapshot is caught."""
    seeded = 'function handleShowLatest() {\n    setViewingSnapshot(null);\n  }\n'
    body = seeded[: seeded.index("\n  }")]
    assert 'setPlaybookDateInput("")' not in body


# --- Both playbook tables drill in to the SAME chart -------------------------------------------------
# The flat signals table and the per-setup occurrence list list the same recorded signals. If each
# built its own URL they could silently diverge — one carrying the record id and one not, say — and
# the same signal would open two different charts.

_PLAYBOOK_LIB = _FRONTEND_ROOT / "lib" / "playbook.ts"


def test_the_drill_in_url_is_built_in_exactly_one_place():
    """One builder, imported by both tables — never two URL literals to drift apart."""
    lib = _PLAYBOOK_LIB.read_text()
    assert "export function playbookDrillInHref(" in lib
    page = _DESK_PAGE.read_text()
    # No PLAYBOOK drill-in URL is composed on the page itself. (The ranked screen rows have their
    # own, unrelated `?symbol=&asof=` link — this is about the playbook's record/signal identity.)
    assert "playbook=${encodeURIComponent" not in page
    assert page.count("playbookDrillInHref(signal, recordId, detectTimeframe)") == 2, (
        "both the signals table and the occurrence list must drill in through the ONE builder"
    )


def test_the_url_builder_carries_every_term_structure_needs_to_draw_the_setup():
    """`asof` positions the chart and the band map; `tf` names the detect timeframe; the (record id,
    signal key) pair is what makes /structure draw THIS occurrence's own recorded outline."""
    lib = _PLAYBOOK_LIB.read_text()
    builder = lib[lib.index("export function playbookDrillInHref(") :]
    for term in ("symbol=", "&asof=", "&tf=", "&playbook=", "&signal="):
        assert term in builder, f"the drill-in URL must carry {term}"
    assert "playbookSignalKey(signal)" in builder


def test_the_signals_row_drill_in_does_not_swallow_the_rows_own_click():
    """This table's row click owns the disclosures panel, so the drill-in is the SYMBOL cell and
    stops propagation — a stretched link (the occurrence list's pattern, where no panel exists)
    would make the panel unreachable."""
    page = _DESK_PAGE.read_text()
    assert 'data-testid="desk-playbook-signal-drill-in"' in page
    assert "onClick={(event) => event.stopPropagation()}" in page
    # The panel it protects is still wired.
    assert 'data-testid="desk-playbook-signal-detail"' in page


def test_both_playbook_drill_ins_open_a_new_tab_safely():
    """The desk is the working surface an operator returns to — a session's whole signal list, its
    filters, its expanded pools. Navigating away in place to look at one chart would discard all of
    it, so both drill-ins open a new tab, and each carries `noopener noreferrer` (the standard
    pairing for a `_blank` target, denying the opened page any handle on this one)."""
    page = _DESK_PAGE.read_text()
    for testid in ("desk-playbook-signal-drill-in", "desk-playbook-occurrence-drill-in"):
        anchor = page.index(f'data-testid="{testid}"')
        # The element's own attribute block, bounded by the JSX tag it sits in.
        element = page[anchor : page.index(">", anchor)]
        assert 'target="_blank"' in element, f"{testid} must open a new tab"
        assert 'rel="noopener noreferrer"' in element, f"{testid} must not hand over window.opener"


def test_the_new_tab_is_announced_to_assistive_tech():
    """A link that opens elsewhere says so — otherwise a screen-reader user loses their place with
    no warning."""
    page = _DESK_PAGE.read_text()
    assert page.count("ET in Structure, in a new tab`}") == 2


def test_the_wall_cells_are_trade_relative_not_geometric():
    """The Playbook tables mix longs and shorts, so a wall column must mean one thing per ROW. The
    behind/ahead slots are resolved from each row's OWN served `side` — selecting between two
    served wall objects, the same move the side-matched drawdown column already makes.

    Geometric below/above columns read wrong for shorts: an entry INSIDE a band is the nearest
    structure in both directions, so naming it once had to pick a column, and picking "below"
    assumed every row was a long — a short fading a band it sat inside found that band in neither
    cell."""
    lib = _PLAYBOOK_LIB.read_text()
    assert 'side === "long" ? context.wall_below : context.wall_above' in lib, (
        "the BEHIND wall must be chosen by the row's own served side"
    )
    assert 'side === "long" ? context.wall_above : context.wall_below' in lib, (
        "the AHEAD wall must be chosen by the row's own served side"
    )
    page = _DESK_PAGE.read_text()
    assert 'playbookWallLabel(context, side, "behind")' in page
    assert 'playbookWallLabel(context, side, "ahead")' in page


def test_the_trade_relative_guard_can_fail_on_a_seeded_violation():
    """Non-vacuous: the long-biased form this replaced is not accepted."""
    seeded = 'const wall = slot === "behind" ? context.wall_below : context.wall_above;'
    assert 'side === "long" ? context.wall_below : context.wall_above' not in seeded


def test_the_at_wall_tint_marks_the_wall_the_trade_is_actually_at():
    """`backing_bucket` is side-resolved by the backend, so the tint must sit on the BEHIND cell —
    on a geometric column it lit the wrong cell for every short."""
    page = _DESK_PAGE.read_text()
    behind = page.index('data-testid="desk-playbook-signal-wall-behind"')
    ahead = page.index('data-testid="desk-playbook-signal-wall-ahead"')
    tint = page.index('backed ? "text-amber-300" : undefined')
    assert behind < tint < ahead, "the at-wall tint belongs to the behind cell"


def test_the_wall_columns_sort_on_served_bps_not_label_text():
    """One ordering that is right for both sides, and an entry inside a band sorts first on its own
    served 0.0 rather than on where "i" falls in the alphabet."""
    page = _DESK_PAGE.read_text()
    assert "value: (item) => contextFor(item)?.backing_bps ?? null," in page
    assert "value: (item) => contextFor(item)?.headroom_bps ?? null," in page


# --- the composed cohort: one filter selection, one meaning everywhere -------------------------------
# The section's two filters compose into a cohort the BACKEND pooled. That is the whole point: the
# per-setup summary renders pooled means, and a browser re-pooling them over a filtered subset would
# make the section's headline numbers browser-derived.


def test_the_summary_renders_the_backend_pooled_cohort_not_a_browser_reduction():
    """The pooled means come from the served cohort block. If this ever became a client-side
    reduction over `record.signals`, the numbers a reader trusts most would stop being the
    backend's."""
    source = _DESK_PAGE.read_text()
    assert "const cohort = cohorts?.cohorts?.[cohortKey] ?? null;" in source
    assert "const activeSummary = cohort?.summary ?? record.summary;" in source
    # The cells still read a served pool object, never a recomputed one.
    assert "pool={activeSummary[poolKey]}" in source
    for banned in (".reduce(", "sum +="):
        section = source[source.index("function PlaybookSummaryView") : source.index("function PlaybookEvidenceBandContextTable")]
        assert banned not in section, f"the summary must not {banned} its way to a mean"


def test_cohort_membership_is_read_from_the_served_list_never_re_derived():
    """Especially for "not inside": the lens serves a null containing band for every ABSENCE too,
    so a browser-side `containing_band === null` test would file every un-warmed signal as "not
    inside a band" — claiming a location for an event that has none. The backend owns it."""
    source = _DESK_PAGE.read_text()
    assert "row.cohorts.includes(cohortKey)" in source
    assert "containing_band === null" not in source
    assert "containing_band !== null" not in source


def test_the_two_filters_compose_into_the_backends_own_cohort_key():
    source = _DESK_PAGE.read_text()
    assert "function playbookCohortKey(band: PlaybookBandFilter, inside: PlaybookInsideFilter)" in source
    assert 'return `${band}:${inside}`;' in source
    assert 'const UNFILTERED_COHORT = "all:all";' in source


def test_the_inside_filter_defaults_to_showing_everything():
    source = _DESK_PAGE.read_text()
    assert (
        'const [playbookInsideFilter, setPlaybookInsideFilter] = useState<PlaybookInsideFilter>("all");'
        in source
    )


def test_the_beyond_cap_chip_reads_the_served_flag_not_a_row_position():
    """Under a filter the row's position is no longer its position in the record's pool."""
    source = _DESK_PAGE.read_text()
    assert "return row === undefined ? false : !row.in_cap;" in source
    assert "entry.servedIndex >= cap" not in source


def test_the_cohort_filter_copy_is_clean():
    source = _DESK_PAGE.read_text()
    phrases = [
        "inside or not",
        "inside a band",
        "not inside a band",
        "and the pooled means above are this cohort's own",
    ]
    for phrase in phrases:
        assert phrase in source, f"expected cohort copy missing: {phrase!r}"
        assert find_violations(phrase) == [], phrase


# goal-rapid-microscope-iter-31 (J-11): the new Graduation section's price-arithmetic guard --
# TC-5's own seeded counter-test proving the extended `_PRICE_ARITHMETIC_FIELDS` pattern is live,
# not vacuous.


def test_desk_page_price_arithmetic_guard_catches_graduation_evaluation_n_arithmetic():
    """TC-5 counter-test: a client-side sum/rate over the new `evaluation.n` binding (the Graduation
    section's own sealed-evaluation observation count) is caught, exactly like every other served
    numeric this guard already covers."""
    seeded_sum = "const total = evaluation.n + evaluation.n;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_sum) is not None


def test_desk_page_graduation_section_never_derives_a_second_computation_of_the_referee_note():
    """J-11's own Acceptance text ("no second computation path"): the Graduation section's static
    `referee_handoff_ready` copy is transcribed BYTE-FOR-BYTE from `micro_graduation.py`'s own
    `REFEREE_FUTURE_REVISION_SENTENCE` -- proven here by importing the backend constant directly and
    asserting it appears verbatim in the frontend source, so the two can never silently drift."""
    from app.research.micro_graduation import REFEREE_FUTURE_REVISION_SENTENCE

    source = _DESK_PAGE.read_text()
    assert REFEREE_FUTURE_REVISION_SENTENCE in source, (
        "the Graduation section's referee_handoff_ready copy does not match "
        "micro_graduation.REFEREE_FUTURE_REVISION_SENTENCE byte-for-byte"
    )
