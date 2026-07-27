# Iteration Summary — goal-desk-iter-9

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-27
**Iteration:** 9

## In plain words

**What you can do now:** Run a simulated trading session and watch it settle into a read like "Buyer Control," with live moving price bars. Open the Structure page to see a stock's key support and resistance levels on a real price chart, and browse case studies of past price touches. Open the Desk page to scan about 100 well-known stocks, refresh their price history, and see them ranked — including, on every row, how many days old the price reading behind it is. Revisit any past scan exactly as it was recorded, and jump from any scan row straight into the Structure chart for that stock and date. A connected Claude conversation can read the Desk's company list and scan results too.

**What changed this time:** Every ranked row on the Desk page now says exactly how old its price reading is — for example, "basis 2026-07-23, 4 days before as-of" — both at a glance and in full detail when you hover. Older, already-saved scans honestly say the information wasn't recorded back then, instead of guessing. The feature works and was checked thoroughly, but the team still owes one specific photo: a very fresh reading (2 days old or less) shown right next to a very stale one (10 days old or more). Today's photo showed 3 days next to 14 days instead, so that one proof is not quite finished.

**What's next:** Take that one photo properly — using a practice copy of the data set to a slightly earlier date, which will show a 1-day-old reading next to 12-day-old ones — and this small addition will be fully done.

## Headline

New "basis" column on Desk shows how old each ranked stock's price reading is

## Direction

**Signal:** holding
**Why:** J-08 "Every ranked briefing row names the bar its distance was measured from" is functionally built and independently re-verified on real data, but its literal ≤2 d/≥10 d screenshot clause is unmet (the evidence shows 3 d vs 14 d), so it stays `partial` and the verdict is CONTINUE, not GOAL_ACHIEVED. J-01–J-07 all re-verified passing with zero regressions and zero anti-goal violations, so nothing moved backward and nothing newly crossed into passing this round — direction reads holding, with a single, low-risk, code-free fix already identified for next iteration.

**Trend (last 5 iters):**
- Newly passing this iter: none (J-08 was newly scored, but `partial`, not `passing`)
- Newly passing in last 5 iters total: J-04 (iter-5), J-05 (iter-6), J-06 (iter-7), J-07 (iter-8)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none new (one long-carried minor item, open since iter-4, was resolved by the owner's written ratification in iter-8)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The new "basis" column on the Desk page is built, and it is honest. Every ranked row of a new screen now names the exact daily price bar its distance was measured from and how many days old that bar is; rows saved before this change say plainly "basis not recorded in this snapshot" instead of guessing. I checked the numbers myself against the one place that owns them and they match exactly. One thing is missing: the goal text asks for a single picture showing a row that is 2 days old or fresher next to a row that is 10 days old or older.

## What was done

- Added `basis_as_of` and `basis_age_days` to every ranked row of a newly computed `/desk` screen — both read/derived once from the same `compute_tradability` result already fetched for that row, with zero additional `BarStore`/tradability calls.
- Rendered the new column with descriptive text (e.g. "basis 2026-07-23 · 4 d before as-of") and an honest "basis not recorded in this snapshot" fallback for screens recorded before this iteration — legacy rows keep serving with the two fields absent, never backfilled.
- Extended the row's existing consolidated hover tooltip with the full-precision basis detail, reusing the iter-6/iter-7 tooltip-composer pattern instead of adding a new, pointer-unreachable per-cell title.
- Added 5 new/extended backend tests (byte-identity cross-check against the tradability route, a calendar-diff pure function, a zero-extra-call guard, a same-pins re-run check, and a legacy-row honesty check), plus extended the tooltip guard test — full suite now 1346 passed / 8 skipped / 0 failed (floor was 1341/8).
- Recorded a new golden replay script (`journey-scripts/J-08.json`) and a reusable fixture-scoped backend rig script for this and future iterations' browser evidence.
- Verified 17/17 journeys pass browser QA this iteration (the J-01–J-07 regression set plus J-08's new checks), with zero diff to any frozen file and the fingerprint pin unchanged (`08e471b10130e1e2`).

## What's left

- Journey J-08 ("Every ranked briefing row names the bar its distance was measured from") is `partial`: the goal's literal screenshot clause (one row ≤2 d old beside one ≥10 d old) is unmet — the captured evidence legibly shows 3 d vs 14 d instead.
- A zero-code-change fix is already identified: compute a screen for `screen_date=2026-07-25` inside the existing scoped throw-away rig and re-photograph — AAPL would read 1 d and NFLX/META/NVDA would read 12 d, satisfying both thresholds literally.
- The browser-QA pass ran "Run Screen" against the real/ambient data folder instead of the scoped copy the plan directed (a disclosed hygiene deviation, not a rail breach) — the new `J-08.json` replay script's "latest" steps now depend on that ambient state.
- Minor test-coverage gaps noted by the audit (GAP-level, not blocking): the zero-extra-read guard test only counts `compute_tradability` calls, not the full `BarStore`/`bar_index` family named in the spec text; legacy-field-absence is pinned by a committed test at the store layer but only by an ad hoc check at the route layer.
- A stale evidence-file pointer in the dev handoff — the file it cited as J-08 replay proof was later overwritten by the smoke-set replay; the underlying claim is true, only the pointer needs fixing.
- Carried, not forced: the same-date screen ambiguity (two screens recorded on one day can't be told apart by date alone), keyboard access for history rows, and three older one-line hardening items from earlier iterations.

## Next step

Run iteration 10 at **lean** depth — a photography and tidy-up run with no program change. Copy the real data folder to a throw-away place with the existing scoped-rig script, run one screen there for the date 2026-07-25, clear the frontend build, and photograph the Desk page: Apple will read 1 day and Netflix, Meta and Nvidia will read 12 days, satisfying the goal file's literal thresholds in one image. State plainly in the picture report which data folder was used, since this iteration's browser pass used the real one against its own written plan. Do not let a test plan lower a threshold the goal file sets — ask the owner instead. Two small, no-cost tidy-ups can ride along (fix the stale replay-evidence pointer; note that the new script's steps assume the newest saved screen carries the basis fields). Everything else — the column itself, the honest fallback, the untouched legacy records, the tests, and the walkthrough — is already verified and should not be redone.

## Assumptions made

- iter-9 · goal-decomposer — Ambiguity: `docs/goal.md` specifies `basis_age_days` only as "a plain arithmetic derivation" from two ISO datetimes, naming neither the exact formula nor whether it's a whole-day integer. We chose: a whole calendar-date difference (`(date(as_of) - date(basis_as_of)).days`), because it reproduces the proposer's own cited examples exactly. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: the goal's screenshot clause needs a row ≤2 d old beside one ≥10 d old; the captured evidence shows 3 d vs 14 d, and the iteration's own test plan wrote itself an allowance to accept that wider spread. We chose: score J-08 `partial`, not `passing` — a downstream test plan cannot amend the goal file, and the literal thresholds are reachable today with zero code change. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: browser QA ran "Run Screen" against the real data folder instead of the scoped throw-away copy the spec directed, and no rail explicitly names "must not write to the ambient store." We chose: record it as a disclosed hygiene deviation, not an anti-goal violation — it was an explicit button click, append-only, and both pre-existing snapshots stayed provably untouched. Reversible: yes
- iter-8 · goal-decomposer — Ambiguity: J-07's "kept-route byte-identity" clause names no exhaustive route/input list to baseline against era-open, and no baseline was ever captured at era open. We chose: a bounded, reproducible set of pre-desk GET routes with concrete pinned inputs already used by prior evidence, not an exhaustive fuzz. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: the current-tree Case Studies screenshot only proves the panel resolves to its honest empty state (a cold cache), not a real event drill-in, though the clause asks for the drill-in itself. We chose: count iter-7's still-valid frame (the underlying code is provably unchanged) as satisfying that sub-clause, paired with this iteration's fresh empty-state capture. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: a third kept route (`/research/candles`) differed from the captured baseline by one `integrity_errors` count, against a literal "byte-identity holds" clause. We chose: score the clause met — the difference is exactly the owner-ratified price-less-row repair, confirmed in code and bounded to one route. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: loading `/structure` on the ambient store now leaves the Case Studies panel loading for minutes, a cache-key side effect of this era's new Config fields, against the anti-goal "page-load GETs never trigger fetches or computes." We chose: not a violation — no new code path was added and served values are byte-identical; the fix is an operator-run cache-warm, not in-scope product work. Reversible: yes
- iter-7 · goal-decomposer — Ambiguity: the prior audit framed a tooltip regression fix as a binary choice between "the whole row is a link" or "each cell keeps its own hover detail," with neither the goal file nor the blueprint saying which. We chose: consolidate every per-cell tooltip onto the row's existing drill-in anchor, touching no click geometry, rather than either named option. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: whether a disclosed, owner-escalated deviation from a literal "byte-identity holds" clause counts as satisfying it. We chose: score J-07 `partial`, not `passing`, and halt with STALLED so the owner's one written decision gates the era instead of spending another iteration on unchangeable work. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: J-07's cockpit-walk clause names a synthetic symbol that structurally cannot show historical candles or a band overlay. We chose: treat the clause as met for what that symbol can show, evidence the rest from `/structure` instead, and record a real-symbol capture as an open gap for the next iteration. Reversible: yes

## Quick verify

From `reports/phase-goal-desk-iter-9-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser.
2. In the "Screen History" panel near the bottom of the page, click the row dated "2026-07-25".
3. Click the "Latest" button inside that banner.
4. Scroll down to the "Run Screen / Top-up" panel and click the "Run Screen" button.
5. Look at the "basis" column of the ranked table now on screen.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-9.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-9-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-9-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-9-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-desk-iter-9-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-desk-iter-9-user-visible-changes.md |
| What to click | — | reports/phase-goal-desk-iter-9-what-to-click.md |
| UI surface map | — | reports/phase-goal-desk-iter-9-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-desk-iter-9-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-desk-iter-9-ux-regression.md |
| QA | PASS | reports/qa/goal-desk-iter-9-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-desk-iter-9-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-desk-iter-9-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-9/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
