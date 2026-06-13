# Iteration Summary — goal-i_will_be_super_rich_with_my_loved_ones-iter-24

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-06-13
**Iteration:** 24

## In plain words

**What you can do now:** Watch any stock ticker (simulated, historical, or live) and see a real-time cockpit with tape-state verdicts, confidence, quotes, trades, features, and a price chart at true clock time. Choose a data source — simulated, live, or historical replay — and the cockpit now shows a small badge labeling which data basis it is reading from (Simulated, IEX live, or SIP consolidated). If the live IEX feed is active, an honest one-line note explains that live verdicts read the IEX feed while historical research uses SIP, so spreads and prints can differ. Every hint the cockpit has ever shown now includes a "Feed" stamp on each row in the hints log, so you always know which data basis a pattern was observed on. Declare a trading thesis and watch it judged live; see an eight-item entry checklist with live measured margins; get a management stance while holding a position; see setup-forming hints with evidence and study citations. Browse the Journal for a full trade history with review grades, excursion outcomes, analytics partitioned by data source and config, and replay studies against a null baseline.

**What changed this time:** The cockpit now shows a feed-basis badge next to the stream status indicator. When you are watching a simulated ticker it reads "Simulated"; on a live IEX watch it reads "IEX (live)" and shows the disclosure note; on historical replay it reads "SIP (consolidated)". When no ticker is being watched, the badge stays hidden — it never guesses. The hints log in the Journal gained a new "Feed" column that shows the stored data basis for each hint row. Under the hood, the single config-aligned function that maps the current watch mode to its feed label was consolidated to one place, so upgrading from IEX to SIP in the future only requires changing one config value with no code changes.

**What's next:** Next we will run a cue-discipline sweep, walking every piece of copy on every screen to confirm nothing is imperative or predictive, adding a copy-quality test, and wiring up an optional sound cue that defaults to off.

## Headline

Feed basis is always labeled: cockpit badge + hint-log stamp + one config-aligned mapping (J-67 passing)

## Direction

**Signal:** improving
**Why:** J-67 ("the live-feed basis is always labeled") flipped from failing to passing this iteration, verified in browser pixels — cockpit feed badge, hint-log FEED column, analytics partitioning, and honest idle absence all confirmed. No regressions, no anti-goal violations, and all six required-still-passing journeys re-verified green. The project has moved a journey forward in each of the last five iterations (J-65 in iter-23, J-64 in iter-22, J-63 in iter-21, J-53 in iter-20, J-60/J-61 in iter-19), maintaining steady forward momentum toward the remaining two items before GOAL_ACHIEVED consideration.

**Trend (last 5 iters):**
- Newly passing this iter: J-67
- Newly passing in last 5 iters total: J-53 (iter-20), J-63 (iter-21), J-64 (iter-22), J-65 (iter-23), J-67 (iter-24)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-67 flips to passing on direct pixel evidence — cockpit "feed Simulated" badge, hint-log FEED column, analytics feed+fingerprint partitions, honest idle absence — plus the unit-proven single-config-value clause (ONE config-aligned data_feed_for_scenario in feed_basis.py, AST-proven; REST==WS verbatim; suite 812/1 exit 0 twice). Coherence COHERENCE-PASS (duplicate mapping removed, not paralleled); independently verified no engine/provider file in the diff. All six required-still-passing journeys re-verified green.

## What was done

- Created `feed_basis.py` — a new leaf module owning the single config-aligned `data_feed_for_scenario(scenario, config)` function; the `hints.py` local copy was removed; `monitor.py`, `hints.py`, `studies.py`, `routes.py`, and `serializers.py` all import the one function
- Made the mapping config-aligned: `live ...` → `config.live_feed`, `historical ...` → `config.historical_feed`, everything else → `"sim"` — replacing hardcoded literals; defaults unchanged so all existing stamps and pinned tests stay byte-identical
- Added additive `data_feed` field to the row-6 snapshot projection (`serialize_summary` + `serialize_stream`), computed once from the one mapping; REST summary value equals WS frame verbatim (unit-proven + live ASGI probe)
- Added `feed_basis` taxonomy block to `GET /research/taxonomy`: per-feed badge labels plus the live disclosure line verbatim from goal.md; frontend hardcodes none of it
- Built `FeedBasisBadge.tsx` and wired it into `TopBar.tsx`: renders the served `data_feed` with taxonomy labels; shows the disclosure only when `dataFeed === "iex"`; renders nothing when idle (honest absence)
- Added "Feed" column to `HintLog.tsx` rendering each row's stored `data_feed` stamp with taxonomy labels
- Added `hint_log_max` fingerprint-stability + counter test pair in `test_research_hints.py` — the assurance pair the `config.py` comment claimed now exists in the suite
- Verified 6/6 browser QA tests passed (J-67 target + J-01, J-08, J-59, J-63, J-65 regressions); full backend suite 812 passed / 1 skipped / 0 failed

## What's left

- Journey J-66 (Cue-discipline sweep — no imperative, no prediction, sound off by default) failing — all-surface copy walk, copy-lint test, optional sound cue defaults-off
- Journey J-68 (The existing cockpit is unchanged — regression sentinel) partial — the "J-01–J-37 all remain green" backlog clause (J-11, J-14, J-16, J-18, J-20, J-22, J-23, J-27, J-28, J-29, J-32 partial; J-15 unknown/gated)
- J-67 credential-gated legs to opportunistically close: live-IEX badge + disclosure pixels (market was closed during QA); live-declared journal row stored `iex` stamp (requires market hours + credentials)
- Pre-existing reviewer NOTE carry-forward: `routes.py:1207/1232` hardcoded `"sip"` study pre-stamp at creation — tracked for the J-66 sweep
- Full-pipeline `qa_complete` harness halt remains open (depth stays lean until fixed)

## Next step

Target **J-66** (cue-discipline sweep) at **lean** depth: the all-surface copy walk (thesis strip across verdicts/stances, hint cards, chart geometry labels, journal rows + detail, analytics, studies, taxonomy), the copy-lint test over UI strings (a J-66 copy-discipline test was already seeded in `test_research_api.py` — extend/verify coverage), and the optional sound cue (defaults OFF, transition-only, with cooldown, explicit toggle). Fold in the reviewer NOTE (`routes.py:1207/1232` hardcoded `"sip"` study pre-stamp) as a sweep carry-along. If run during US market hours with credentials, opportunistically capture the live-IEX badge + disclosure pixels to close J-67's gated leg. After J-66: the J-68 backlog re-verification (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-28/J-29/J-32 partial, J-15 gated) — the last items before GOAL_ACHIEVED consideration. Depth stays lean while the full-pipeline `qa_complete` harness halt (iter-23 eval, open item 3) remains unfixed.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_will_be_super_rich_with_my_loved_ones-iter-24.md |
| Dev handoff | — | docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-24-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_will_be_super_rich_with_my_loved_ones-iter-24-review.md |
| Browser QA | PASS | reports/phase-goal-i_will_be_super_rich_with_my_loved_ones-iter-24-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_will_be_super_rich_with_my_loved_ones/iter-24/eval.md |
| Journey history | — | runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/journey-history.json |
