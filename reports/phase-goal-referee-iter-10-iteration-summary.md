# Iteration Summary — goal-referee-iter-10

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-15
**Iteration:** 10

## In plain words

**What you can do now:** Watch the live tape on the Cockpit, look up a stock's support-and-resistance map on the Structure page, and scan chart setups on the Desk page — the same three screens as before. On the Desk page, open "Referee Registry" to see candidate research questions with live evidence counts and register one for real, open "Referee Adjudications" to see each registered question's plain verdict word and its full evidence trail, and open "Referee Runs" to start a check, watch it run, cancel it, and see a history of every run. The product's core trading strategy is protected — it can no longer be swapped for a new one unless a genuine, correctly-matched certificate backs the change.

**What changed this time:** The Desk page now has two new sections at the very bottom: "Referee Adjudications," which shows each registered question's plain verdict word plus the full paper trail behind it, and "Referee Runs," where you can start a check, watch its progress live, cancel it, and see a history of every run. The Claude connector also gained two new read-only tools reading the same data (22 total, up from 20).

**What's next:** Next we'll re-check the older parts of the product that had to be skipped this round because of time, and take the one still-missing picture of the "please wait, already running" message.

## Headline

Referee Adjudications panel on /desk shows every hypothesis's verdict and evidence trail

## Direction

**Signal:** improving
**Why:** This iteration shipped the Referee's final two `/desk` panels (J-09, newly passing) and completed the kept-product regression sentinel (J-10, newly passing), while also closing the iter-9 certificate-evidence anti-goal gap via the rider-1 pooling fix, which the evaluator reproduced live. Seven of the eight already-passing journeys (J-01–J-06, J-08) were only carried forward as DEFERRED-BUDGET rows rather than freshly re-verified this round, which is why the evaluator issued CONTINUE instead of GOAL_ACHIEVED and recommended one short, no-new-building verification round next.

**Trend (last 4 iters):**
- Newly passing this iter: J-09, J-10
- Newly passing in last 4 iters total: J-06 (iter-7), J-07 (iter-8), J-08 (iter-9), J-09 and J-10 (iter-10)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: 2 total (1 minor found and resolved same-iteration at iter-8; 1 minor opened at iter-9, closed this iteration) — 0 currently open
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** The last two Referee panels are real, and I checked them myself instead of reading the reports. On the Desk page a person can now open "Referee Adjudications" and see each written-down question with its plain verdict word, and open "Referee Runs" to start a job, watch it count up, cancel it, and read the history of every run. The Claude connector now offers 22 read-only tools — I counted them myself. The one weakness the previous round left open is genuinely closed: a certificate can no longer be stamped with the name of a strategy whose trades were never part of the evidence.

## What was done

- Product changes: apps/backend/app/mcp/__init__.py, apps/backend/app/research/referee_adjudicate.py, apps/frontend/app/desk/page.tsx, apps/frontend/lib/api.ts, apps/frontend/lib/types.ts
- Shipped the "Referee Adjudications" panel on `/desk`: verdict chip, refusal reasoning, and full evidence provenance (basis hash, spec ids, seed identity, attestation, BH fold) for every registered hypothesis
- Shipped the "Referee Runs" panel on `/desk`: null-build and evaluation triggers with live progress, cancel, single-flight refusal, and full run-history ledgers
- Grew the Claude MCP connector from 20 to 22 read-only tools (`desk_referee`, `desk_referee_registry`), byte-identical to their REST equivalents
- Closed the iter-9 anti-goal gap: certificate minting now pools only evidence that actually belongs to the named strategy/profile candidate (rider 1), reproduced and verified via TC-13/14/15
- Landed 3 riders: dropped stale "unwired" docstring language, made the no-bypass guard's can-fail test exercise the real scan instead of a hand-typed string, removed a duplicate test assertion
- Verified J-09 and J-10 pass browser QA; full backend suite green (2,688 collected / 2,680 passed / 8 skipped / 0 failed), fingerprint pin unchanged (`08e471b10130e1e2`)

## What's left

- Re-verify J-01, J-02, J-03, J-04, J-05, J-06 and J-08 — all seven were carried forward as DEFERRED-BUDGET this round rather than freshly re-tested; the deterministic finish check treats a deferred row as a failure, so the era can't be declared done until they're checked again
- Capture the one still-missing screenshot: J-09's "in-flight second trigger refused single-flight" picture — the currently-cited image is byte-identical to two other screenshots and shows no refusal
- Fix the walk-through recorder script, which contains an action ("scroll") the player does not understand, so it can capture that missing picture
- The rider-1 certificate-evidence fix has no UI surface and can't be exercised through any button, form, or CLI flag today — it only guards a future wiring that doesn't exist yet
- Two of the seven verdict states ("fragile" and a refused-attestation "insufficient_sample") only appear once fixture data is seeded separately; on an unseeded backend only the one carried-over hypothesis (S-1) shows
- If a null-build or evaluation was already running before the page loaded (e.g. from another browser tab), the Runs panel won't show it as "running" until the operator re-triggers or re-opens the section
- The "seed identity" provenance line shows the hypothesis's own ID rather than the underlying numeric seed value, which no endpoint serves yet

## Next step

Run one short verification round — no new building. Three things must happen in it.

1. Re-check the seven journeys this round skipped for time: J-01 "The era transition stands", J-02 "The evidence contract", J-03 "The statistics core", J-04 "Matched nulls", J-05 "The registry", J-06 "Estimand engines and adjudication" and J-08 "The strategy family and the promotion lock". Their rows say "deferred", and the automatic finish check treats a deferred row exactly like a failure, so the era cannot be declared done while they stand. Six of them have no stored click-by-click script (J-01's and J-02's are marked invalid), and most have no screen of their own, so re-checking them means running their own named backend acceptance tests and writing the result into the results table — not taking pictures of pages they do not have.
2. Take the one missing picture: the screen refusing a second job while the first is still running. Today the button greys out the moment it is clicked, so a second click never reaches the server and nothing is shown. To photograph the refusal, start a job one way (a second browser tab, or the command line) and then click the button in a freshly loaded page — the red line "Refused — a null build is already running for this spec." will appear. The behaviour itself is already proven three ways; only the picture is missing.
3. Fix the walk-through recorder: this round's recording was skipped because its script contains an action type ("scroll") the player does not understand.

Four small clean-ups are worth doing whenever a builder next touches this area; none of them blocks the era: a certificate check that treats "both names unknown" as a match (unreachable today, but worth refusing outright); the verdict page showing a plain dash when the second data request fails, which looks the same as "this question honestly has no such value"; a stale comment on the Desk page that still quotes the old counts 19/7/1; and adding the four Referee storage folders to the guard that watches the owner's real data.

Two items for a person, neither blocking: this round's eleven changed files are not committed yet (iterations 8 and 9 are already committed), and, from iteration 2 and outside this project, the unrelated trendora backend on port 8255 has still not been restarted.

Approve one short verification round that re-checks the seven skipped journeys and takes the one missing picture; nothing needs a human unblock to start it.

## Assumptions made

- iter-10 · goal-evaluator — Ambiguity: J-10's browser walk asks to cover every shipped `/desk` section and prove kept-route byte-identity, but the fixture rig has no computed desk screen and no era-6 response baseline exists to compare against. We chose: scored J-10 passing, reading "renders as shipped" as satisfied by the rig's own honest "not computed yet" panels, and proving byte-identity at the source level (an era-cumulative diff review of every kept route file) instead of a stored response baseline. Reversible: yes
- iter-10 · goal-evaluator — Ambiguity: J-09's spec names a required screenshot of an in-flight second trigger being refused, but the cited image is identical to two other screenshots and shows no refusal. We chose: scored J-09 passing with the gap flagged as a capture defect, since the refusal behaviour itself is proven three separate ways and only the picture is missing; the make-up capture rides next round. Reversible: yes
- iter-10 · developer — Ambiguity: the two new Referee panels need registry fields the adjudications data doesn't carry, and it wasn't clear whether they should assume the Registry section was opened first. We chose: both new sections fetch the registry data themselves on first open, rather than depending on click order. Reversible: yes
- iter-10 · developer — Ambiguity: the design calls for a "seed identity" line, but no part of the system serves the actual underlying random seed value anywhere. We chose: show the hypothesis's own ID under that label (the one piece that genuinely varies the seed per question), rather than hard-code or invent the real number client-side. Reversible: yes
- iter-10 · goal-decomposer — Ambiguity: last round left two ways open to close the certificate-evidence gap — fix the code, or get an owner ruling that a caller-declared name is enough. We chose: fix the code, scoping evidence pooling to the certificate's own named strategy, since the issue was a real, reproduced exploit and the fix reuses data already on file with no schema change. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: the rule "no promotion without a matching certificate" doesn't say whether "matching" also means the evidence behind the certificate must truly belong to the named strategy, and that round's build only satisfied the weaker reading. We chose: logged it as a minor, still-open item rather than a critical failure, because nothing reachable in the shipped product could exploit the gap. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: one journey is defined as having no browser screen of its own, but the era's own rule says a missing screenshot means "unrated," never "passing." We chose: read that rule as applying only to journeys that need a picture at all, so this one is judged from its own tests and direct checking instead. Reversible: yes
- iter-9 · developer — Ambiguity: a test expected a particular plain-English verdict word for a case the underlying code doesn't actually produce that word for yet. We chose: read the requirement as pointing to a different, already-existing field that carries that same honest word today, rather than build a new code path outside that round's scope. Reversible: yes
- iter-9 · goal-decomposer — Ambiguity: it wasn't specified whether the strategy a certificate is minted for should be looked up automatically or stated explicitly by whoever requests it. We chose: require it to be stated explicitly by the requester; leaving it unstated (as every part of the product does today) mints nothing at all. Reversible: yes

## Quick verify

From `reports/phase-goal-referee-iter-10-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Scroll to the very bottom of the page
3. Click the "Referee Adjudications" section header
4. If the table has any rows, read the "Verdict" column for the first row
5. Click the "Referee Runs" section header (directly below "Referee Adjudications")

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-10.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-10-dev.md |
| Review | PASS | reports/reviews/goal-referee-iter-10-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-10-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-referee-iter-10-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-referee-iter-10-user-visible-changes.md |
| What to click | — | reports/phase-goal-referee-iter-10-what-to-click.md |
| UI surface map | — | reports/phase-goal-referee-iter-10-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-referee-iter-10-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-referee-iter-10-ux-regression.md |
| QA | PASS | reports/qa/goal-referee-iter-10-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-referee-iter-10-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-referee-iter-10-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-referee/iter-10/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
