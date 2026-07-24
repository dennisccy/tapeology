# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 9. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/config.py` (36 lines not shown)

```diff
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 6dd9d1c..e533e70 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -489,131 +489,6 @@ class Config:
     # (``tests/test_datasets.py``).
     dataset_dir: str = str(Path(__file__).resolve().parents[1] / ".data" / "datasets")
 
-    # --- Research evolution: verdict-transition engine (capability 24) -------------------------
-    # RESEARCH DEFAULTS — a starting point calibrated against the deterministic sims, NEVER a
-    # validated edge (the goal doc's Research-config-defaults constraint: every research value lives
-    # in config with its sim calibration documented; no literal in research code). These enter the
-    # ``config_fingerprint`` automatically (it hashes the entire frozen config), so a verdict timeline
-    # is never silently compared across different verdict timings.
-    #
-    # PER-SETUP VERDICT DWELL (LOGICAL seconds): how long the raw verdict rule must hold CONTINUOUSLY
-    # (in logical time, restarting at thesis creation) before the verdict is PUBLISHED — so a single
-    # flickering tick never publishes a transition and confirmation is always backed by sustained
-    # post-declaration evidence. Calibrated against the sim phase lengths: SIM-BUYER/SIM-REVERSAL's
-    # control phase and SIM-REVERSAL's absorption phase each run well past 30s logical once settled
-    # (the classifier's 30s primary window), so a 3.0s dwell publishes comfortably INSIDE the phase
-    # while still demanding several consecutive confirming ticks (at the 0.5s sim tick that is ~6
-    # ticks). Keyed per setup so a slower-to-trust setup can carry a longer dwell without a magic
-    # number anywhere else; all four share the same default here (one documented starting point).
-    verdict_dwell_seconds: dict = field(
-        default_factory=lambda: {
-            "absorption_reversal": 3.0,
-            "trend_continuation": 3.0,
-            "level_break": 3.0,
-            "failed_move_fade": 3.0,
-        }
-    )
-    # INVALIDATION ε (a spread multiple): a single print beyond the declared invalidation by AT LEAST
-    # this many TIMES the current spread is a hard, dwell-exempt invalidation — far enough past the
-    # level that one genuinely-bad print (a fat-finger inside the guard) does NOT trip it. The guard
-    # band is ``epsilon × spread`` on the wrong side of the invalidation. Calibrated so the sim's
-    # $0.02 spread yields a ~$0.03 band: a print $0.04+ through the level invalidates immediately,
-    # while a lone print $0.02 through it (inside the band) does not. A spread multiple (not a dollar
-    # figure) so it scales to any instrument's price/liquidity (the no-magic-numbers discipline).
-    invalidation_epsilon_spread_multiple: float = 1.5
-    # k CONSECUTIVE prints beyond the invalidation (INSIDE the ε guard band) that together invalidate:
-    # a sustained leak through the level — not a single ≥ε breach, not a lone bad print — is itself
-    # decisive. ``k`` consecutive prints on the wrong side (each by any margin > 0) auto-resolve the
-    # thesis. Keeps a slow drift through the level honest without waiting for one big ≥ε print.
-    invalidation_k_consecutive: int = 3
-    # The append-only verdict timeline is capped at this many PUBLISHED rows per thesis (the oldest
-    # are pruned on append once the cap is exceeded). A safety bound on an unbounded live watch — a
-    # generous default since transitions are rare (dwell-gated). Capacity bound only; the surviving
-    # rows are never edited (append-only at the repository level holds — pruning is the store's own
-    # capacity management, distinct from any update/delete of a retained row, which does not exist).
-    verdict_timeline_cap: int = 500
-
-    # --- Research evolution: MANAGEMENT-STANCE DWELL (capability 27, J-53; data-contract row 25) ----
-    # RESEARCH DEFAULT — a starting point calibrated against the deterministic sims, NEVER a validated
-    # edge (the goal doc's Research-config-defaults constraint: every research value lives in config
-    # with its sim calibration documented; no literal in research code). The holding-period MANAGEMENT
-    # STANCE (``thesis_intact | thesis_weakening | thesis_invalidated``) is a pure derivation from the
-    # latest PUBLISHED verdict; it publishes through THIS config-owned, LOGICAL-time dwell so a single
-    # flickering verdict tick never flaps the stance — EXCEPT ``thesis_invalidated``, which is
-    # dwell-exempt (it mirrors the hard, dwell-exempt invalidation trigger and is terminal). Calibrated
-    # to the SAME 3.0 s the per-setup verdict dwell uses (the verdict it reads is already dwell-gated,
-    # so a SHORT additional stance dwell suffices to absorb a one-tick verdict flicker without lagging
-    # the user's read; at the 0.5 s sim tick that is a few consecutive ticks). One documented starting
-    # point; tighten/loosen only with a re-measured justification, never to fit a result.
-    #
-    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with the
-    # codified iter-12 / iter-16 discipline: the stance is NEVER PERSISTED (it is a live cue, derived
-    # at read from the published verdict + the recorded marks — schema stays v7, no stance row exists).
-    # A serving-only timing value that touches NO persisted research value (no verdict, feature, grade,
-    # excursion, or stamp) MUST NOT move the fingerprint — else two journals identical in every
-    # threshold but served at different stance dwells would mint different fingerprints and could never
-    # be pooled. Pinned by a fingerprint-stability test (changing it does NOT move the fingerprint) and
-    # its counter-test (a real classifier threshold STILL does).
-    management_stance_dwell_seconds: float = 3.0
-
-    # --- Research evolution: ENTRY-CHECKLIST STANCE DWELL (capability 33, J-63; data-contract row 25) -
-    # RESEARCH DEFAULT — a starting point calibrated against the deterministic sims, NEVER a validated
-    # edge (the goal doc's Research-config-defaults constraint: every research value lives in config
-    # with its sim calibration documented; no literal in research code). The entry-checklist AGGREGATE
-    # STANCE (``conditions_met | conditions_not_met | tape_against | no_fresh_tape``) is composed at the
-    # moment of decision from EXISTING engine values; it publishes through THIS config-owned,
-    # LOGICAL-time dwell so a single flickering check (a lone tick where one margin dips under its
-    # boundary) never flaps the stance. Calibrated to the SAME 3.0 s the management-stance + per-setup
-    # verdict dwells use — the checks it aggregates read already-dwelled canonical values (the published
-    # verdict is itself dwell-gated), so a SHORT additional stance dwell suffices to absorb a one-tick
-    # flicker without lagging the user's read; at the 0.5 s sim tick that is a few consecutive ticks.
-    # One documented starting point; tighten/loosen only with a re-measured justification, never to fit.
-    #
-    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with the
-    # codified iter-12 / iter-16 / iter-20 discipline: the checklist + its stance are NEVER PERSISTED
-    # (a live cue computed at read from the published verdict + canonical features — schema stays v7,
-    # no checklist row exists). A serving-only timing value that touches NO persisted research value
-    # (no verdict, feature, grade, excursion, or stamp) MUST NOT move the fingerprint — else two
-    # journals identical in every threshold but served at different checklist dwells would mint
-    # different fingerprints and could never be pooled. Pinned by a fingerprint-stability test (changing
-    # it does NOT move the fingerprint) and its counter-test (a real classifier threshold STILL does).
-    checklist_stance_dwell_seconds: float = 3.0
-
-    # --- Research evolution: DELIVERY-LAG BOUND (capability 22 row 14, J-63; data-contract row 14) -----
-    # RESEARCH DEFAULT — a documented starting point, NEVER a validated edge. The ``tape_lag_ok``
-    # entry-checklist check (J-63) passes when the feeder-owned ``delivery_lag_seconds`` (the latest
-    # record's epoch vs wall clock in LIVE mode; the feeder's processing backlog vs its own pacing
-    # schedule in paced replay) is at/under THIS bound. A healthy live or sim feed reads a lag well
-    # under it; a stalled/backlogged feeder reads above it and ``tape_lag_ok`` honestly fails (feeding
-    # ``no_fresh_tape``). Calibrated to the SAME family as ``stale_gap_seconds`` (10.0 s) but tighter:
-    # the stale gap is the hard "no event at all" watchdog, whereas this lag bound is the gentler
-    # "events are arriving but the processed tape trails real time" honesty gate — 5.0 s so a momentary
-    # dense-tape catch-up does not trip it while a sustained processing lag does. Seconds (a wall-clock
-    # delivery metric, NEVER read by classification — determinism unchanged), so no relative scaling.
-    #
-    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with the
-    # SAME iter-12/16/20 discipline: the lag check is part of the never-persisted checklist (schema
-    # stays v7), and ``delivery_lag_seconds`` is feeder-owned DELIVERY metadata that never enters any
-    # persisted research value (no verdict, feature, grade, excursion, or stamp). A serving-only bound
-    # MUST NOT move the fingerprint — else two journals identical in every threshold but served under
-    # different lag bounds could never be pooled. Pinned by a fingerprint-stability test + counter-test.
-    delivery_lag_ok_bound_seconds: float = 5.0
-
-    # --- Research evolution: JOURNAL LIST serving (capability 31 / J-51) ------------------------
-    # The journal LIST endpoint (``GET /research/journal``) page-size policy. These are SERVING-ONLY
-    # values: the number of persisted thesis rows returned per page. They are EXCLUDED from
-    # ``config_fingerprint`` (see the exclusion set below) for the same reason ``journal_db_path`` is —
-    # a page-size choice cannot affect ANY persisted research value (it never touches a verdict, a
-    # feature, a grade, or a stamp). Including it would dishonestly fragment the analytics pools (two
-    # journals identical in every threshold but served at different page sizes would mint different
-    # fingerprints and could never be pooled), so it is deliberately excluded — never forgotten.
-    #   * ``journal_list_default_limit`` — the page size used when the request omits ``limit``.
-    #   * ``journal_list_max_limit``     — the hard cap; a request ``limit`` above this is CLAMPED down
-    #                                      to it (a serving safety bound, never a 422 — an over-large
-    #                                      page is honestly satisfied with the most rows we will serve).
-    journal_list_default_limit: int = 50
-    journal_list_max_limit: int = 200
-
     # --- Research evolution: SEGREGATED JOURNAL ANALYTICS (capability 31 / J-59) -----------------
     # The minimum group sample size for the analytics view (``GET /research/analytics``). A per
     # ``setup_type`` × ``direction`` group whose ``n`` is BELOW this serves an explicit
@@ -630,109 +505,6 @@ class Config:
     # (changing this value must NOT change ``config_fingerprint``).
     analytics_min_sample_size: int = 5
 
-    # --- Research evolution: ENTRY RISK FLAGS (capability 26, J-49) -----------------------------
-    # RESEARCH DEFAULTS — a starting point calibrated against the deterministic sims, NEVER a
-    # validated edge (same discipline as the verdict-dwell defaults above). The flag set is computed
-    # ONCE from the declaration-time engine snapshot and FROZEN on the thesis (advisory, never
-    # blocking). FOUR of the six flags reuse EXISTING gates with NO new constant:
-    #   * ``before_warmup``        reuses ``warmup_min_events`` (the classifier's own warm-up floor);
-    #   * ``wide_spread_illiquid`` reuses the classifier's relative-spread gate
-    #                              (``max_stable_spread_bps`` when a price basis exists, else the
-    #                              absolute ``max_stable_spread``) — VERBATIM, no second threshold;
-    #   * ``low_trade_speed``      reuses ``min_trade_speed`` — VERBATIM;
-    #   * ``against_expected_tape`` is setup-aware (snapshot tape state vs the setup's expected tape)
-    #                              and needs no numeric threshold at all.
-    # Only the TWO below are genuinely new (capability 26 names exactly these two as new):
-    #
-    # CHASE RETURN THRESHOLD (a directional impact-as-return): a declaration is ``chasing_entry`` when
-    # the recent FAVORABLE-side price-impact return (the SAME ``buy_price_impact``/``sell_price_impact``
-    # divided by the canonical ``reference_price`` the classifier already uses as its relative impact
-    # metric — direction-aware: buy for a long, |sell| for a short) ALREADY exceeds this. Calibrated
-    # against SIM-BUYER's buyer-control phase: the favorable buy-impact return sits at ~0.0033 right at
-    # warm-up and climbs past ~0.0040 a few seconds later (an EXTENDED move), so a 0.0040 threshold
-    # fires ``chasing_entry`` on a well-past-warm-up declare (the move has already run) while a clean
-    # at-warm-up declare does not — the honest "you are chasing an extended move" boundary. Expressed
-    # as a RETURN (not a dollar move) so it scales to any instrument's price level (no-magic-numbers).
-    chase_return_threshold: float = 0.0040
-    # INVALIDATION-TOO-TIGHT SPREAD MULTIPLE: a declaration is ``invalidation_too_tight`` when the
-    # distance from the current last to the declared invalidation is BELOW this many times the current
-    # spread — i.e. the stop sits so close to price that ordinary spread noise would trip it. A spread
-    # MULTIPLE (not a dollar band) so it scales to any instrument's price/liquidity, mirroring the
-    # invalidation-ε robustness multiple. Calibrated against the sim's ~$0.02 spread: at a 2.0×
-    # multiple an invalidation within ~$0.04 of the last is flagged too tight, while a normal
-    # invalidation ~$1 away (50× the spread) is comfortably clear.
-    invalidation_too_tight_spread_multiple: float = 2.0
-
-    # --- Research evolution: OUTCOME × PROCESS GRADES (capability 29, J-56) ----------------------
-    # The config-owned rules for the two review grades, computed ONCE at terminal resolution
-    # (alongside execution checks) and persisted (schema v6). NO numeric score anywhere — both axes
-    # are ENUM labels with plain-language evidence naming which named checks drove them.
-    #
-    # OUTCOME (``thesis_held | thesis_failed | no_read``) is 1:1 from the resolution (goal.md
-    # capability 29) — a fixed, config-owned map, never a judgement:
-    #   * ``played_out``  -> ``thesis_held``   (the idea ran its course on your side);
-    #   * ``invalidated`` -> ``thesis_failed`` (the tape resolved it against the thesis);
-    #   * ``expired``     -> ``no_read``       (the watch ended before the thesis resolved either way);
-    #   * ``abandoned``   -> ``no_read``       (closed without running its course — no outcome read).
-    # Kept in config (not hardcoded in research code) so the single 1:1 mapping has ONE owner.
-    process_outcome_grade_map: dict = field(
-        default_factory=lambda: {
-            "played_out": "thesis_held",
-            "invalidated": "thesis_failed",
-            "expired": "no_read",
-            "abandoned": "no_read",
-        }
-    )
-    # PROCESS (``clean | flagged | violated``) is a config-owned RULE over the named, evidence-backed
-    # checks (the FROZEN entry risk flags + the persisted execution checks) — NEVER a numeric score,
-    # and CRITICALLY: being invalidated is never by itself a process failure (the system enforces
-    # invalidation; an invalidated thesis with no failed execution check and no fired risk flag grades
-    # ``clean``). The rule, in priority order (the worst named finding wins):
-    #   * ``violated`` — at least ``process_violated_min_failed_checks`` execution check(s) read
-    #     ``failed`` (the user demonstrably did something the checks flag: held through the stop,
-    #     chased, cut a confirming thesis early, entered before confirmation). A failed EXECUTION
-    #     check is grounded in the user's OWN recorded marks, so it is a process matter.
-    #   * ``flagged`` — no failed execution check, but at least
-    #     ``process_flagged_min_risk_flags`` entry risk flag(s) fired at declaration (an advisory the
-    #     user declared into). Risk flags are advisory, so they ``flag`` rather than ``violate``.
-    #   * ``clean``   — neither (no failed execution check, no fired risk flag).
-    # The two thresholds are config-owned (no literal in research code) and default to 1 (any single
-    # failed check violates; any single fired flag flags). They are documented research defaults — a
-    # starting point, never a validated edge.
-    process_violated_min_failed_checks: int = 1
-    process_flagged_min_risk_flags: int = 1
-
-    # --- Research evolution: EXCURSION OUTCOMES (capability 30, J-58) ----------------------------
-    # The config-owned excursion horizons, computed ONCE at terminal resolution / stream-end (a
-    # research record, schema v7) and served VERBATIM on the journal detail. NO numeric "score"
-    # anywhere — each horizon reports MFE/MAE in R units + a TERNARY outcome
-    # (``+1R_first | -1R_first | neither_within_horizon``) resolved by FIRST TOUCH in logical time.
-    # These are documented RESEARCH DEFAULTS — a starting point, never a validated edge — and they
-    # enter ``config_fingerprint`` (it hashes the entire config), so a record created after this
-    # iteration carries a new fingerprint (the intended honesty mechanism: analytics never pool
-    # across fingerprints). This is NOT a defect — it is the same fingerprint-shift discipline every
-    # prior research-config addition introduced.
-    #
-    # HORIZONS (logical seconds past the anchor): the canonical 10 / 30 / 60 / 120 s family
-    # (goal.md's predictive-value horizons). Calibrated against the seeded J-58 substrate — J-42's
-    # ``SIM-BUYER`` confirmed long with the EXACT J-42 invalidation of 98.00 (R ≈ 2.21 at the
-    # confirmation, which lands ~22.5s logical in). SIM-BUYER grinds price strictly UP but only at
-    # ~$0.012/s, so a full +1R favorable move ($2.21 past the anchor) is NOT reached within any short
-    # horizon: the 10 / 30 / 60s horizons fully ELAPSE at ``neither_within_horizon`` (a partial
-    # favorable excursion honestly recorded as MFE, well under +1R) — at least one COMPLETED horizon.
-    # The J-58 script ends the watch ~77s of logical time past the confirmation (the entry-marked
-    # thesis then survives active-but-not-evaluated at the stream end), which is BEFORE the 120s
-    # horizon elapses, so the 120s horizon is still open and is TRUNCATED at the stream end — at least
-    # one STREAM-END-TRUNCATED horizon. Both requirements the spec calls for are thus deterministically
-    # exercised by the seeded run (proven in test_excursions.py's J-58 calibration test).
-    excursion_horizons_seconds: tuple = (10.0, 30.0, 60.0, 120.0)
-    # The R MULTIPLE at which the ternary outcome resolves by first touch (favorable reaches
-    # ``+excursion_target_r`` before adverse reaches ``-excursion_target_r``, or neither within the
-    # horizon). Kept in config (no literal in research code) so the "+1R / -1R" definition has ONE
-    # owner; defaults to 1.0 R (the goal-doc ternary ``+1R_first | -1R_first | neither``). A research
-    # default — a starting point, never a validated edge.
-    excursion_target_r: float = 1.0
-
     # --- Engine-performance gate: dense-replay CI time budget (capability 34, J-62) -------------
     # The wall-clock BUDGET (seconds) the CI timing gate allows for an UNPACED replay of the
     # committed ≈10-minute real SIP dense fixture through a fresh full ``TapeEngine`` (the same
@@ -771,13 +543,6 @@ class Config:
     # intended honesty mechanism: studies never pool across fingerprints). This is NOT a defect — it is
     # the same fingerprint-shift discipline every prior research-config addition introduced.
     #
-    # STUDY NULL-ARM COUNT: how many random-arm-time NULL-baseline occurrences are drawn (from the
-    # recorded seed) over the SAME window, SAME direction, SAME R definition, and SAME horizons as the
-    # setup arms. The seed is persisted on the study record so the baseline reproduces exactly. A
-    # control population large enough to be a meaningful comparison yet bounded so one in-memory replay
-    # pass serves both populations within the CI budget. Defaults to 100 (the goal.md register's
-    # "random-time baseline: 41/100" illustration).
-    study_null_arm_count: int = 100
     # STUDY ARMING SUSTAIN (logical seconds): the auto-arming rule for the two state-native setups
     # (absorption_reversal / trend_continuation) requires the setup's PREMISE tape state to hold
     # CONTINUOUSLY for at least this long before an occurrence is armed — so a single flickering tick
@@ -814,75 +579,6 @@ class Config:
     # spread to scale; documented research default calibrated against the sims' ~$0.01 tick so it is a
     # few ticks. Enters the fingerprint (it shapes the persisted R basis).
     study_occurrence_r_floor: float = 0.05
-    # STUDY NULL-BASELINE SEED: the default seed used to draw the random null-arm times when a study
-    # does not carry its own. Persisted on each study record at creation so the baseline reproduces
-    # exactly (same seed ⇒ identical arms). A documented research default; it shapes the persisted null
-    # baseline, so it ENTERS the fingerprint. Per-study override is possible (recorded on the record),
-    # but the default keeps the committed reference study reproducible in CI.
-    study_null_baseline_seed: int = 1729
-    # STUDY LIST PAGE SIZE (``GET /research/studies``): a SERVING-ONLY value — the max number of study
-    # rows the list returns. EXCLUDED from ``config_fingerprint`` (see the exclusion set in
-    # ``config_fingerprint``) by the SAME iter-12 page-size precedent (``journal_list_*``): a list page
-    # size touches NO persisted study value (it never changes an occurrence, an R basis, a baseline, or
-    # a stamp), so two journals identical in every threshold but served at different study-list page
-    # sizes MUST share a fingerprint (else fragmenting the very pools studies exist to compare). Pinned
-    # by a fingerprint-stability test (changing it does NOT move the fingerprint) and its counter-test.
-    study_list_max: int = 100
-    # HINT SUSTAIN DWELL (logical seconds, capability 33 / J-65): a state-native setup-forming hint
-    # fires only after its PREMISE tape state (one of the four sustained states — bid_absorption /
-    # ask_absorption / buyer_control / seller_control) has held CONTINUOUSLY for at least this long —
-    # so a single flickering tick, or SIM-CHOP's flapping unclear/mixed stream, NEVER sustains past
-    # it and NEVER fires a hint (the same sustained-evidence discipline the verdict dwell and the
-    # study-arm sustain enforce). Composed ONLY of EXISTING engine states (no new indicator). A
-    # RESEARCH DEFAULT — a starting point, never a validated edge. Logical-time (the verdict-dwell
-    # precedent), so sim journeys are deterministic and no wall-clock enters a hint decision (the wall
-    # ts on the record is a stamp only). Calibrated against the sims' phase lengths so SIM-BIDABS's
-    # sustained bid_absorption phase fires exactly one hint within a browser-verifiable wait, while
-    # SIM-CHOP's flapping never holds one premise state long enough to reach it. ENTERS the fingerprint
-    # (it shapes the persisted hint records — the study-arm-sustain precedent).
-    hint_sustain_dwell_seconds: float = 5.0
-    # HINT COOLDOWN (logical seconds, capability 33 / J-65): after a hint fires for a pattern on the
-    # watched ticker, no further hint of the SAME pattern on the SAME ticker fires until this much
-    # logical time has elapsed past the fire — so one sustained premise phase produces ONE logged hint,
-    # not a hint every tick (the study-arm-cooldown precedent). A generous default so re-fires are
-    # well-separated; the active-hint lifecycle (clear-on-state-leave / clear-on-non-live-status) is
-    # independent of this re-fire gate. A RESEARCH DEFAULT, logical-time, deterministic. ENTERS the
-    # fingerprint (it shapes which hint records are persisted — the study-arm-cooldown precedent).
-    hint_cooldown_seconds: float = 180.0
-    # HINT LOG PAGE SIZE (``GET /research/hints``): a SERVING-ONLY value — the default/max number of
-    # persisted hint-log rows the list returns. EXCLUDED from ``config_fingerprint`` (see the exclusion
-    # set in ``config_fingerprint``) by the SAME iter-12 page-size precedent (``journal_list_*`` /
-    # ``study_list_max``): a list page size touches NO persisted hint value (it never changes a hint
-    # record, its evidence, its citation, or its stamps), so two journals identical in every threshold
-    # but served at different hint-log page sizes MUST share a fingerprint. Pinned by a
-    # fingerprint-stability test (changing it does NOT move the fingerprint) and its counter-test
-    # (``test_hint_log_max_is_serving_only_excluded_from_fingerprint`` +
-    # ``test_a_real_threshold_still_changes_fingerprint`` in ``tests/test_research_hints.py``, iter-24).
-    hint_log_max: int = 200
-    # SOUND-CUE COOLDOWN (wall-clock seconds, capability 33 / J-66): the OPTIONAL, off-by-default
-    # client sound cue (the last capability-33 item) fires ONLY on a stance/verdict TRANSITION and then
-    # stays silent for at least this many seconds before it may fire again — a debounce so a brief
-    # verdict flicker (or two transitions in quick succession) never machine-guns the speaker. The cue
-    # itself is a CLIENT-LOCAL UI preference: the toggle state is never sent to the backend and the cue
-    # is NEVER PERSISTED. This key is SERVING-ONLY — it is served additively to the frontend via the
-    # row-24 taxonomy payload (alongside the sound-cue display copy) so the cooldown is config-owned
-    # (no magic number in the UI), and the browser reads it verbatim. A RESEARCH DEFAULT — a documented
-    # starting point, never a validated edge. Calibrated to the SAME 3.0 s family as the verdict /
-    # stance dwells (the values it debounces are themselves already dwell-gated), so a single extra
-    # debounce of that order suffices to avoid a double-fire without lagging a genuine second
-    # transition. Seconds (a wall-clock UI debounce, NEVER read by classification — determinism
-    # unchanged), so no relative scaling.
-    #
-    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with the
-    # codified iter-12/16/20/23 discipline: the cue is NEVER PERSISTED (schema stays v7 — no cue row
-    # exists), so this serving-only timing value touches NO persisted research value (no verdict,
-    # feature, grade, excursion, stamp, hint, or study). It MUST NOT move the fingerprint — else two
-    # journals identical in every threshold but served at different cue cooldowns would mint different
-    # fingerprints and could never be pooled. Pinned by a fingerprint-stability test (changing it does
-    # NOT move the fingerprint) + the real-threshold counter-test, in the SAME commit as this key (the
-    # ``study_list_max`` / ``hint_log_max`` serving-only pattern; iter-23 lesson — never promised only
-    # in prose).
-    sound_cue_cooldown_seconds: float = 3.0
 
     # --- Profit-research era: STRATEGY GRAMMAR V1 + BACKTEST models (capabilities 3/4, J-03) -------
     # RESEARCH DEFAULTS — documented starting points calibrated against the deterministic sims and
@@ -963,8 +659,10 @@ class Config:
     # Both values are persisted VERBATIM into the row, so they are row-shaping and DELIBERATELY
     # NOT excluded from ``config_fingerprint`` (the never-pool honesty mechanism — pinned by the
     # counter-test in tests/test_pnl_ledger.py).
-    pnl_founding_enhancement_id: str = "founding-baseline-strategy-v1-default"
-    pnl_founding_enhancement_title: str = "founding baseline — strategy v1 on default"
+    pnl_founding_enhancement_id: str = "founding-baseline-strategy-v1-default-clean-slate"
+    pnl_founding_enhancement_title: str = (
+        "founding baseline — strategy v1 on default (post-clean-slate epoch)"
+    )
     # THE FOUNDING WINDOWS (UTC ISO start/end pairs): the exact slices of the committed keyless
     # ``PG_SIP_REFERENCE`` window the founding row measures — chosen to reproduce the committed
     # fixture dataset pair CONTENT-IDENTICALLY (the seeding CLI records through the real store
@@ -1626,22 +1324,14 @@ class Config:
         Operational store-tuning fields (the journal DB path / busy timeout) are EXCLUDED: they do
         not affect any engine/verdict computation, so two journals that differ only in where they
         live must share a fingerprint (else every temp-path test would mint a unique one). The
-        journal LIST page-size fields (``journal_list_default_limit`` / ``journal_list_max_limit``)
-        are EXCLUDED for the same reason: a serving page size touches no persisted research value, so
-        two journals identical in every threshold but served at different page sizes MUST share a
-        fingerprint (else their analytics pools would be dishonestly fragmented). The analytics
-        min-sample threshold (``analytics_min_sample_size``) is EXCLUDED for the identical reason
-        (capability 31 / J-59): it is a serving/presentation-only display gate that touches no
+        analytics min-sample threshold (``analytics_min_sample_size``) is EXCLUDED for the identical
+        reason (capability 31 / J-59): it is a serving/presentation-only display gate that touches no
         persisted research value, so two journals identical in every threshold but viewed at
         different min-sample sizes MUST share a fingerprint (else fragmenting the very pools the
         analytics surface exists to compare). The dense-replay CI timing budget
         (``dense_replay_time_budget_seconds``) is EXCLUDED for the identical reason (capability 34 /
         J-62): a CI gate value touches no persisted research value, so two journals identical in every
-        threshold but run under different CI budgets MUST share a fingerprint. The management-stance
-        dwell (``management_stance_dwell_seconds``) is EXCLUDED for the identical reason (capability
-        27 / J-53): the stance is a live cue that is NEVER PERSISTED (schema stays v7), so a stance
-        timing value touches no persisted research value and two journals identical in every threshold
-        but served at different stance dwells MUST share a fingerprint.
+        threshold but run under different CI budgets MUST share a fingerprint.
         """
         excluded = {
             "journal_db_path",
@@ -1744,60 +1434,12 @@ class Config:
             "recording_post_touch_minutes",
             "recording_event_selection_cap",
             "recording_holdout_fraction",
-            "journal_list_default_limit",
-            "journal_list_max_limit",
             "analytics_min_sample_size",
             # The dense-replay CI timing budget (capability 34 / J-62): a CI GATE value that never
             # enters any persisted research computation, so two journals identical in every threshold
             # but run under different CI budgets MUST share a fingerprint (else fragmenting the
             # analytics pools). Same iter-12/iter-16 precedent as the serving/display fields above.
             "dense_replay_time_budget_seconds",
-            # The study-list page size (capability 32 / J-60): a SERVING-ONLY value that never enters
-            # any persisted study computation (it touches no occurrence, R basis, baseline, or stamp),
-            # so two journals identical in every threshold but served at different study-list page sizes
-            # MUST share a fingerprint. Same iter-12 page-size precedent (``journal_list_*`` above). The
-            # FIVE other new study keys (``study_null_arm_count``, ``study_arm_sustain_seconds``,
-            # ``study_arm_cooldown_seconds``, ``study_occurrence_r_spread_multiple``,
-            # ``study_occurrence_r_floor``, ``study_null_baseline_seed``) are DELIBERATELY NOT excluded
-            # — they shape the persisted study results, so they MOVE the fingerprint (the intended
-            # never-pool-across-fingerprints honesty mechanism).
-            "study_list_max",
-            # The management-stance dwell (capability 27 / J-53): the stance is a live cue that is
-            # NEVER PERSISTED (schema stays v7 — no stance row exists), so this timing value touches no
-            # persisted research value (no verdict, feature, grade, excursion, or stamp). It is
... [diff_bound] apps/backend/app/config.py: 36 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_backtests.py b/apps/backend/tests/test_backtests.py
index 46c170e..aa922d3 100644
--- a/apps/backend/tests/test_backtests.py
+++ b/apps/backend/tests/test_backtests.py
@@ -413,7 +413,7 @@ def test_default_fingerprint_still_pinned_after_registering_structure_tape_map()
     # structure_tape_map introduces NO new Config field (it reuses the six structure_tape_* fields
     # verbatim — see strategy_definition), so no new exclusion-set entry is needed at all; the
     # fingerprint stays pinned trivially. Verified by direct computation, not assumed.
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
 
 
 def test_structure_tape_breakthrough_long_arms_at_the_class_a_resistance_level(
@@ -1482,7 +1482,7 @@ def test_default_fingerprint_still_pinned_with_the_new_structure_tape_fields_pre
     # Ground truth (the test_profile_equivalence.py precedent): the founding PnL-ledger row was
     # appended under THIS exact fingerprint. Every new structure_tape field above is present on
     # CONFIG but excluded, so adding them must not move it.
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
 
 
 # --- Single-source discipline: one R formula, one dataset reader ------------------------------------
diff --git a/apps/backend/tests/test_edge_report.py b/apps/backend/tests/test_edge_report.py
index eb0c2e4..aa3082d 100644
--- a/apps/backend/tests/test_edge_report.py
+++ b/apps/backend/tests/test_edge_report.py
@@ -210,7 +210,7 @@ def test_fixture_pair_yields_no_positive_edge_dataset_with_real_measured_numbers
     assert report["positive_edge_dataset_ids"] == []
     assert report["finding"] == NO_POSITIVE_EDGE_FINDING
     # Default-frozen cross-check: untouched by this iteration (no new Config field).
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
 
 
 # --- Split separation (Key Test Scenario 2) -------------------------------------------------------
diff --git a/apps/backend/tests/test_levels.py b/apps/backend/tests/test_levels.py
index 8e9b364..05a4359 100644
--- a/apps/backend/tests/test_levels.py
+++ b/apps/backend/tests/test_levels.py
@@ -715,7 +715,7 @@ def test_sr_parameters_are_config_sourced_no_magic_numbers():
 
 
 def test_sr_config_fields_are_excluded_from_config_fingerprint():
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
     assert Config(sr_pivot_lookback=5).config_fingerprint() == CONFIG.config_fingerprint()
     assert Config(sr_touch_tolerance_bps=50.0).config_fingerprint() == CONFIG.config_fingerprint()
     assert (
diff --git a/apps/backend/tests/test_pnl_scan.py b/apps/backend/tests/test_pnl_scan.py
index fef6833..0491758 100644
--- a/apps/backend/tests/test_pnl_scan.py
+++ b/apps/backend/tests/test_pnl_scan.py
@@ -190,7 +190,7 @@ def test_fixture_sweep_is_zero_survivors_and_leaves_everything_untouched(store,
 
     # Untouched: the founding row is still the only row; the default fingerprint is still pinned.
     assert len(store.list_pnl_ledger()) == 1
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
     assert profiles_projection(store, CONFIG)["champion"] == report["champion_before"]
 
 
@@ -263,7 +263,7 @@ def test_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(s
     assert row["provenance"]["holdout"]["dataset_id"] == holdout_meta["id"]
 
     # The default profile and every engine default are byte-identical to before this ran.
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
 
     # Single-source: the projection reflects the SAME moved pointer, verbatim.
     assert profiles_projection(store, test_config)["champion"] == report["champion_after"]
@@ -566,7 +566,7 @@ def test_strategy_axis_fixture_sweep_matches_shape_and_is_honestly_no_survivor(s
 
     # Nothing written, nothing moved, foundation untouched.
     assert len(store.list_pnl_ledger()) == 0
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
 
 
 def test_strategy_axis_determinism_two_independent_fresh_state_runs_are_byte_identical(tmp_path, monkeypatch):
@@ -643,7 +643,7 @@ def test_strategy_axis_controlled_survivor_moves_champion_and_appends_exactly_on
     assert row["provenance"]["holdout"]["dataset_id"] == holdout_meta["id"]
 
     # Frozen foundation AFTER a STRATEGY-axis promotion too: fingerprint unmoved.
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
     # Single-source: the projection reflects the SAME moved pointer, verbatim.
     assert profiles_projection(store, test_config)["champion"] == report["champion_after"]
 
diff --git a/apps/backend/tests/test_profile_equivalence.py b/apps/backend/tests/test_profile_equivalence.py
index 36725d0..d759bfa 100644
--- a/apps/backend/tests/test_profile_equivalence.py
+++ b/apps/backend/tests/test_profile_equivalence.py
@@ -118,7 +118,7 @@ def test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field():
     # Ground truth: the founding PnL-ledger row (reports/pnl/pnl-history.md, committed) was
     # appended under THIS exact fingerprint. If this pin ever moves, that row (and every
     # archived-era record) has silently drifted — the strongest guard against that.
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
 
 
 def test_profile_candidate_field_is_serving_only_excluded_from_fingerprint():
@@ -133,7 +133,7 @@ def test_profile_candidate_field_is_serving_only_excluded_from_fingerprint():
 def test_candidate_resolved_fingerprint_is_distinct_from_default():
     resolved = CONFIG.resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP)
     assert resolved.config_fingerprint() != CONFIG.config_fingerprint()
-    assert resolved.config_fingerprint() == "8c2c0fbf978228e3"
+    assert resolved.config_fingerprint() == "16d7c98e4fdca755"
 
 
 def test_a_real_classifier_threshold_still_changes_the_fingerprint():
diff --git a/apps/backend/tests/test_setups.py b/apps/backend/tests/test_setups.py
index fb57a1a..7eded97 100644
--- a/apps/backend/tests/test_setups.py
+++ b/apps/backend/tests/test_setups.py
@@ -406,7 +406,7 @@ def test_setups_parameters_are_config_sourced_no_magic_numbers():
 
 
 def test_setups_config_fields_are_excluded_from_config_fingerprint():
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
     assert (
         Config(setups_panel_symbols=("AAPL",)).config_fingerprint() == CONFIG.config_fingerprint()
     )
@@ -776,7 +776,7 @@ def test_compute_setups_itself_never_touches_the_dataset_store():
 
 
 def test_recording_config_fields_are_excluded_from_config_fingerprint():
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
     assert Config(recording_pre_touch_minutes=1.0).config_fingerprint() == CONFIG.config_fingerprint()
     assert Config(recording_post_touch_minutes=1.0).config_fingerprint() == CONFIG.config_fingerprint()
     assert Config(recording_event_selection_cap=1).config_fingerprint() == CONFIG.config_fingerprint()
diff --git a/apps/backend/tests/test_timeframe_history_api.py b/apps/backend/tests/test_timeframe_history_api.py
index e470db3..acf955a 100644
--- a/apps/backend/tests/test_timeframe_history_api.py
+++ b/apps/backend/tests/test_timeframe_history_api.py
@@ -191,4 +191,4 @@ def test_timeframe_for_anchorless_engine_is_empty_200():
 # --- Belt-and-braces: this feature adds no Config field -------------------------------------
 
 def test_fingerprint_unchanged_by_this_feature():
-    assert Config().config_fingerprint() == "4d665603569b9dbf"
+    assert Config().config_fingerprint() == "08e471b10130e1e2"
diff --git a/apps/backend/tests/test_tradability.py b/apps/backend/tests/test_tradability.py
index 0ddc302..0f3a6b9 100644
--- a/apps/backend/tests/test_tradability.py
+++ b/apps/backend/tests/test_tradability.py
@@ -367,7 +367,7 @@ def test_tradability_parameters_are_config_sourced_no_magic_numbers():
 
 
 def test_tradability_config_fields_are_excluded_from_config_fingerprint():
-    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
     assert Config(tradability_band_cap_per_side=1).config_fingerprint() == CONFIG.config_fingerprint()
     assert Config(tradability_band_width_bps=999.0).config_fingerprint() == CONFIG.config_fingerprint()
     assert (
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/pnl/pnl-history.md                      | 15 +++++++++++++++
 runs/goal-session-clean_slate/telemetry.jsonl   |  6 ++++++
 runs/goal-session-clean_slate/trace/trace.jsonl |  3 +++
 3 files changed, 24 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
