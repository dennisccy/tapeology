# Iteration Summary — goal-tradable_wall-iter-6

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-15
**Iteration:** 6

## In plain words

**What you can do now:** You can watch simulated buy and sell pressure in the trading cockpit, keep a trading journal, replay past trading studies, and check an honest profit scorecard. On the Structure page, you can fetch real historical prices from Yahoo Finance, then see — by default — a short, ranked list of a stock's handful of truly important price zones instead of a wall of a thousand-plus lines. You can browse a growing library of over 800 real historical examples of price touching those zones (including the Apple example that mattered most, which now ranks #1), drill into what happened at each one, and read an honest profit-comparison report — the original detailed view is still one click away if you want it.

**What changed this time:** This iteration finally put the last several rounds of behind-the-scenes work on screen. Loading a stock on the Structure page now leads with the short, ranked list of price zones instead of the old wall of lines. A new section lets you click through real historical examples of price touching those zones to see what happened each time, and a new profit-comparison report is now visible too (honestly empty for now, since no real trade data has been recorded for these stocks yet). Nothing that worked before was removed — everything from before is one click away or simply lower on the page, and it all still works exactly the same.

**What's next:** Next we'll bring this same short list of important price zones to the live trading cockpit chart, with a small note when the price is sitting at one of them.

## Headline

/structure declutters: Tradable Map default + Case Studies + Edge Report ship (J-05 passing)

## Direction

**Signal:** improving
**Why:** J-05 flipped from failing to passing this iteration — the first browser-verified render of the Tradable Map, Case Studies, and Edge Report on `/structure` (15/15 browser-QA), with J-01/J-02/J-04/J-07 all re-verified green and zero regressions or anti-goal violations. J-03 stays partial (credentialed recording still operator-gated) and J-06 (cockpit confluence) is the only remaining failing journey, already scoped and queued for iteration 7. Four of the last five iterations advanced a journey (J-02, J-04, J-05 newly passing; J-03 forward to partial) — only iteration 5's backend-only enabler pass had zero flips by design — so the trend is healthy.

**Trend (last 5 iters):**
- Newly passing this iter: J-05
- Newly passing in last 5 iters total: J-02, J-04, J-05
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5

**Latest evaluator reasoning:** "J-05 (`/structure` decluttered) is genuinely achieved — the pure-frontend render flipped it `failing -> passing` on its first attempt, verified by me directly against the UT-02 + UT-06 screenshots and a 15/15 browser-QA pass: the Tradable Map is the default view with exactly 10 bands (the pinned 300.17–302.27 Class-A round-number resistance band ranking #1 of 5 resistance bands), the raw-levels view is behind an off-by-default toggle, and the Case Studies + Edge Report sections render their owning endpoints verbatim. All frozen foundations hold (working-tree diff = exactly 6 files, zero frozen-file leakage, `config_fingerprint` independently recomputed to `4d665603569b9dbf`), coherence is `COHERENCE-PASS`, and my own credential + banned-vocabulary greps are clean. This is not GOAL_ACHIEVED because J-03 remains `partial` (credentialed ≥10-window headline still operator-gated) and J-06 remains `failing` (cockpit confluence deferred to iter-7) — so the loop continues with J-06 as the last agent-buildable journey."

## What was done

- Replaced `/structure`'s default raw ~1,800-level view with a scored Tradable Map (≤10 bands) — verified exactly 10 bands for AAPL as-of 2026-06-22, with the pinned ~300–302 resistance band ranking #1 of 5 resistance bands.
- Added a "Show raw levels" toggle (off by default) that restores the prior full raw-levels + confluence-zones view byte-identically when switched on.
- Added a Case Studies section: a browsable, filterable registry of 801 historical band-touch events across the 12-symbol panel, with a drill-in showing reaction, forward returns, and (when recorded) a tape timeline.
- Added an Edge Report section rendering the 3-way strategy comparison verbatim, including an honest all-empty first-class state on the current real data (no watchlist-symbol recordings exist yet).
- Hardened the iter-5 scan cache's write path in `setups.py` to a single atomic `(key, result)` tuple rebind, closing a torn-read race now that the page fires three reads concurrently on load; added a structural regression guard plus a 16-thread concurrency test.
- Full backend suite green at 1339 passed / 7 skipped / 0 failed (+2 vs iter-5); zero regressions; `config_fingerprint` unchanged at `4d665603569b9dbf`; diff scoped to exactly 6 files.
- Verified 15 target journey(s) pass browser QA (15/15, 0 skipped).

## What's left

- Journey J-06 (Cockpit confluence — bands + tape markers + a descriptive chip) failing — the cockpit's live price chart doesn't yet show these tradable bands or the descriptive chip; queued for iteration 7.
- Journey J-03 (Real tape at the wall — credentialed event-window recording) stays partial — the durable ≥10-window credentialed recording and a populated pinned-AAPL tape timeline remain operator-gated (needs the operator to run the recorder with Alpaca credentials).
- Case Studies filters cover symbol + reaction only; the backend's `band_class` filter has no UI control yet (out of this iteration's scope).
- Edge Report renders its honest empty state on the current real data — populated cells will only appear once credentialed recordings exist for a watchlist symbol (J-03's parallel, operator-gated carry).
- Minor, non-blocking UX nuance: the Case Studies drill-in doesn't auto-clear when a filter change hides the selected row.

## Next step

Build J-06 (Cockpit confluence — `PriceChart` band overlay + descriptive confluence chip) at depth full — the last remaining agent-buildable journey and the phase-spec/audit-sequenced next. Full depth is warranted: it is a new cockpit UI surface (coherence-relevant — must not duplicate `/structure`'s home for the same values), browser-verifiable, and it crosses the strategies-mapping read boundary. Rails to enforce: (1) the chip's rejection/breakthrough mapping + labels must be read from `GET /research/strategies` (structure_tape_map's config-owned mapping, registered since J-04) — never client-hardcoded; (2) descriptive-never-imperative on all chip copy — conditions + measured-history citation only, no prediction/expected-return/advice language; (3) bands read from `GET /research/tradability` as-of the prior session close (morning-markup / no-lookahead); (4) SIM-*/no-bars symbols show an honest "no tradable map" empty state; (5) live mode stays hidden / byte-identical (no execution path, ever); (6) zero client recomputation — "price-in-band" is a display conjunction of two served values, not a recomputation. The credentialed AAPL 06-22 replay portion is operator-Alpaca-gated (honestly blocked when keys absent, never simulated); the keyless band-overlay + chip-logic + SIM empty-state + live-unchanged portions are agent-buildable and browser-verifiable now. Non-blocking carries (do NOT block J-06): optionally auto-clear the Case Studies drill-in when a filter change hides its row (review MINOR / audit F1); and when J-03's credentialed ≥10-window headline + populated pinned-AAPL tape timeline lands, the next browser-QA should screenshot the populated Edge Report cells + a real drill-in tape timeline (closes audit T1).

## Assumptions made

- iter-6 · goal-evaluator — Ambiguity: J-05's acceptance conditions the pinned AAPL 06-22 drill-in's tape timeline on "once J-03 ran," but J-03's credentialed recording hasn't durably landed, so the timeline renders an honest empty-state instead of a populated one — is J-05 fully passing with an empty tape timeline, or only partial until J-03 populates it?. We chose: passing — the acceptance parenthetical explicitly conditions the timeline on J-03, the spec sanctions the honest empty-state as a pass condition, and every other J-05-owned element is verified present; the populated timeline is tracked separately as J-03's own journey. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: "declutter" could mean the raw all-levels rendering moves behind a toggle while everything else on `/structure` stays, or it could mean the era-5 Registry and Comparison sections must be removed entirely. We chose: the non-regressing reading — only the raw levels/zones rendering moves behind an off-by-default toggle; the Fetch control, provenance badge, Registry, and Comparison sections are preserved intact, positioned below the new sections. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: the goal is silent on how a touch event should be presented when its reaction is computed from a truncated sub-horizon while its horizon-0 forward return honestly reports `None` (13/801 live events) — surface the effective horizon, flag-suppress the reaction, or exclude the event entirely?. We chose: additive disclosure — the event keeps its existing reaction label and forward returns, and additively carries the effective reaction horizon plus a boundary flag so the UI can render it honestly as truncated. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: whether the keyless committed-fixture run of J-04 must produce a populated all-`insufficient_sample` report, or whether a vacuously-empty report on the literal fixture plus a synthetic-panel proof of the populated cell structure satisfies J-04's passing bar. We chose: the empty-is-valid reading — J-04 passes on its keyless core since the goal explicitly names an empty/all-insufficient report a valid outcome, and every required acceptance element was independently verified; the credentialed enrichment is an operator-gated carry parallel to J-03. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: whether J-04 can be scored passing on the keyless committed-fixture run alone, or whether the credentialed ≥10-window recorded data (tied to J-03's still-blocked credentialed portion) is required first. We chose: the keyless reading — a correct, gate-honoring, all-insufficient_sample report is J-04's passing core; the credentialed enrichment is an operator-gated carry parallel to J-03, not a blocker. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: whether J-03's "exist"/"shows" acceptance requires durable persistence in the canonical store plus the pinned-AAPL drill-in, or whether a demonstrated-but-ephemeral recording run (real data landed in a since-GC-eligible pytest temp dir, only a JPM proxy timeline shown) is enough to score the credentialed headline met. We chose: the stricter reading — the credentialed headline is met only when datasets persist in the canonical store and the pinned-AAPL drill-in is demonstrated end-to-end; under this bar J-03 = partial. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the iteration spec instructs recording credential-gated J-03 and J-06 as "blocked," but the journey-history status vocabulary has no `blocked` value. We chose: `failing` for both — there is positive evidence their features are entirely absent at baseline, so they are definitively not-passing, not merely untested; the credential gate is preserved as a note field rather than the primary status. Reversible: yes

## Quick verify

From `reports/phase-goal-tradable_wall-iter-6-what-to-click.md`:

1. Open `http://localhost:3301` in your browser, then click "Structure" in the top navigation bar
2. In the form near the top, type `AAPL` into "Symbol" and `2026-06-22T15:00:00Z` into "As-of (UTC, ISO-8601)", then click "Load"
3. Directly below the Tradable Map, click the "Show raw levels" button
4. Scroll down to "Case Studies". Type `AAPL` into the Symbol field just above its table, then click the row dated `2026-06-22`
5. Scroll down to "Edge Report"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tradable_wall-iter-6.md |
| Dev handoff | — | docs/handoffs/goal-tradable_wall-iter-6-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-tradable_wall-iter-6-review.md |
| Browser QA | PASS | reports/phase-goal-tradable_wall-iter-6-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-tradable_wall-iter-6-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-tradable_wall-iter-6-user-visible-changes.md |
| What to click | — | reports/phase-goal-tradable_wall-iter-6-what-to-click.md |
| UI surface map | — | reports/phase-goal-tradable_wall-iter-6-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-tradable_wall-iter-6-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-tradable_wall-iter-6-ux-regression.md |
| QA | PASS | reports/qa/goal-tradable_wall-iter-6-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-tradable_wall-iter-6-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-tradable_wall-iter-6-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-tradable_wall/iter-6/eval.md |
| Journey history | — | runs/goal-session-tradable_wall/state/journey-history.json |
