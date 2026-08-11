# Iteration Summary — goal-playbook-iter-8

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-11
**Iteration:** 8

## In plain words

**What you can do now:** Open the Desk page and see every one of the trading-book's setups the system finds for a chosen day — opening-range breaks, jump-base and drop-base breakouts, cup-and-handle, capitulation entries with a "recent climax" tag, and range trades and double-top/double-bottom reversals — each one measured against what actually happened afterward, honestly, never as advice. Run a bulk "Backscan" across a date range to check and fill in any missing days at once. Scroll further down the Desk page to see a new "Playbook Evidence" table that pools every recorded signal, by pattern and direction, and shows how it performed compared with a random-chance baseline, with thin, not-yet-reliable rows honestly flagged rather than hidden.

**What changed this time:** The Desk page now has a new "Playbook Evidence" panel at the very bottom, below the Backscan panel — it shows, for each pattern and direction, how many times it fired and what happened to price afterward (median, typical spread, and average), compared against a random-chance baseline, with thin data openly marked "low n" instead of hidden. Typing a half-finished date into the Backscan boxes no longer risks a raw server error — it now shows a clean "nothing planned yet" message. Behind the scenes, the automated testing pipeline was also hardened with a real safety check so it can no longer accidentally read or write real trading records while checking the product — an earlier version of that same automated check briefly did exactly that during this round, and it was caught and fixed the same day.

**What's next:** Next, the desk will gain two more built-in tools so outside programs can read the playbook and its new evidence table, and then get one full walk-through in a real browser to confirm nothing else on the site changed by accident.

## Headline

J-08 "The evidence view" ships — pooled pattern distributions vs. baseline, thin cells honestly tagged

## Direction

**Signal:** improving
**Why:** J-08 "The evidence view" (the pooled per-pattern distribution table, importing the existing measurement rail with zero re-implementation) went from failing to passing this iteration — the sixth straight iteration to land a new journey (J-03 in iter-3 through J-08 in iter-8), with zero regressions and all seven prior required journeys re-verified passing. The verdict is CONTINUE rather than a plain pass because a fix-mode pass was needed mid-iteration: the audit caught the automated replay lane briefly writing real records to the operator's live store, which is now closed by a genuine store-scope mechanism rather than a launcher script; J-09 (the MCP tool count) and J-10 (the full regression sentinel) remain the last piece of the era.

**Trend (last 5 iters):**
- Newly passing this iter: J-08
- Newly passing in last 5 iters total: J-04, J-05, J-06, J-07, J-08
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 11 minor findings across iters 4-8 (most found-and-fixed the same iteration or resolved by a later one; 3 remain open — two owner-ruling items carried since iter-6 and one narrower store-scope-coverage gap opened this iteration); 0 critical
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** "The Playbook Evidence table is real and honest. I opened the pictures myself: one screen shows a thin cell (3 signals, marked "low n") sitting right beside a full cell (14 signals, no mark), both with real numbers, and a second screen shows the whole new section with its heading, its plain-English disclosure paragraph and the signal-versus-random-chance columns side by side. All eight older journeys were re-run automatically on a clean test copy and all eight passed. Two things stop this being the end: the Claude tool list still has 18 entries where the goal asks for 20, so J-09 "MCP contract v4" is not built and J-10 "The kept product stands" cannot close."

## What was done

- Product changes: apps/backend/app/research/desk_playbook_evidence.py, apps/backend/app/research/desk_routes.py (new route GET /research/desk/playbook/evidence), apps/backend/app/research/desk_playbook_backscan.py, apps/frontend/app/desk/page.tsx, apps/frontend/lib/api.ts, apps/frontend/lib/types.ts
- Built the Playbook Evidence fold module (`desk_playbook_evidence.py`): pools every recorded signal at the current signature into a 270-cell setup x side x measure table beside a pooled baseline, tagging (never filtering) cells under 12 signals, behind a stat-keyed cache with no update/delete method.
- Wired the new `/desk` Playbook Evidence panel and Invalidation Breaches table — a pure pass-through of the served JSON, no client-side arithmetic.
- Fixed the Backscan plan endpoint's HTTP 500 on a malformed/partial date on both the read path (now an honest empty plan) and the trigger path (now a pre-refusal, no phantom job).
- Fixed J-05's golden replay assertion, which was colliding with static page copy, and recorded a new J-06 golden replay script.
- Fix-mode pass (after the audit's critical finding): built a real store-scope guard — wired into both browser-QA lanes — that refuses, snapshots, and verifies the operator's real data store stays untouched; proven CLEAN across 9,841 protected files with all 8 required journeys replaying green on one scoped rig.
- Audit found and fixed a false disclosure claim in the new evidence table's register text (it overclaimed what the baseline comparison column actually covers).
- Verified 1 target journey (J-08 "The evidence view") plus all 7 required-still-passing journeys (J-01..J-07, J-10) pass browser QA on the scoped rig.

## What's left

- Journey J-09 "MCP contract v4" failing — the Claude tool count is still 18, not the 20 the goal names.
- Journey J-10 "The kept product stands" stays partial — blocked on the same 18-vs-20 tool-count gap until J-09 ships.
- The store-scope guard covers only the two goal-mode browser lanes; the QA agent's own browser pass is still ungated (it ran read-only against the real backend this iteration).
- A detected store-scope breach discloses loudly but does not stop the run; whether it should be made terminal is still an open decision.
- The guard's prepare command is hardcoded project-wide to the playbook fixture rig, which would force a future era's QA backend onto playbook fixtures unless re-scoped per session.
- The new Playbook Evidence panel doesn't show which recorded signature it is pooling, even though the page names every other signature (audit finding F1).
- The evidence endpoint's `?signature=` parameter (inspect a non-default signature) has no UI control anywhere on `/desk`.
- Two owner rulings from iteration 6 remain open: ratify or reject the range-trade "degenerate trigger reference" spec clarification, and settle three places where shipped detectors read the rule book more narrowly than it is written.

## Next step

Build J-09 "MCP contract v4" next: add the two read-only Claude tools for the playbook and its evidence table so the tool count goes from 18 to 20, then close J-10 "The kept product stands" — walk the whole product in a real browser with a picture of every shipped Desk section, the Cockpit and the Structure page, and prove no kept page changed except the two allowed additions. This is the last piece of the era, so run it as a deep iteration with the auditor; the auditor was again the only reader who found real problems this time.

Carry four cheap items in the same cycle: make the store-scope guard also cover the QA agent's own browser pass, and decide whether a detected write into the operator's store should stop the run instead of only reporting it; stop the guard from forcing the playbook fixture data onto a future, unrelated project run; and show the signature the evidence table is built from on screen, since the page currently names every other signature but not that one. Two questions still wait for the owner, unchanged since iteration 6: say yes or no to the one sentence a developer added to the rule book about range trades, and settle the three places where the shipped code reads the rule book more narrowly than it is written.

## Assumptions made

- iter-8 · goal-evaluator — Ambiguity: J-06's owed re-capture screenshot of the Range Trade row was taken on an earlier build of the seed script than the final replay rig; goal.md doesn't say which seed build a capture must come from. We chose: clear the evidence-makeup flag — the substance (the same RTAAA Range Trade row, full geometry line, matching numbers) is legible and agrees with the final-rig capture, so a third re-capture of something already proven twice is not warranted. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: the critical "Persistence stays scoped" / "Immutable data" rails don't say whether a genuine, ledgered, append-only compute made by an automated verification lane (rather than a human) counts as a critical violation; at 14:45 the replay lane pressed Run Backscan against the real backend and wrote three real playbook records plus one run row. We chose: minor and resolved-by-mechanism, not critical — nothing was fabricated or deleted, deleting the records would itself breach the append-only rail, and the new store-scope guard now proves refuse-then-clean across 9,841 protected files. Reversible: no — the records are permanent by design; only the process was fixable.
- iter-8 · goal-decomposer — Ambiguity: neither goal.md nor the canonical spec states a status code or body shape for a malformed (not just inverted) date range on the back-scan plan endpoint. We chose: return HTTP 200 with an empty/disclosed plan, mirroring the already-handled "from after to" case, rather than inventing a new HTTP error contract. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: the new back-scan plan endpoint's HTTP 500 on a malformed/partial date, and the panel's per-keystroke refetch, aren't named by J-07's acceptance text. We chose: keep J-07 passing and record the 500 as a real defect and next-iteration carry item rather than an acceptance failure. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: the spec's scoping-guard requirement allows either a structural (route-level) or a procedural (test-lane) reading, and the developer built a test-lane-only helper. We chose: the test-lane-only reading satisfies the requirement, so J-07 isn't blocked — but the residual gap is recorded against the still-open iter-6 scoping item, since a procedural guard only protects lanes that call it. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: the QA lane clicked Run Playbook against an unscoped backend and permanently recorded a real 57-signal file plus its ledger row; the iteration spec put real-universe computes out of scope but doesn't say whether a genuine, ledgered, unasked-for compute is a critical violation or a process breach. We chose: minor and open — nothing was fabricated, rewritten or pruned, and deleting the record would itself breach the immutable-data rail, so the remedy is process, not removal. Reversible: no — the record is permanent by design; only the process is fixable.
- iter-6 · goal-evaluator — Ambiguity: J-06's acceptance asks for one range signal and one double-top signal legible "in the same clean-rebuilt pass," but the two post-fix screenshots that exist come from two different post-fix rig builds. We chose: pass J-06 with the evidence-makeup flag set — both required geometry lines are legible and every number agrees across the two captures, so the gap is presentation, not behavior, and a re-capture rides the next iteration as a passenger task. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: whether documenting the already-shipped range-trade "degenerate trigger reference" clarification satisfies the critical rule that every threshold must exist in the spec before the code that uses it, given the developer wrote the spec sentence himself to close a bug rather than the owner. We chose: minor and open pending owner ratification — the literal rule is satisfied since the spec edit landed before the code, the change only removes signals and never invents them, and the developer surfaced it via the assumption ledger himself. Reversible: yes
- iter-6 · developer — Ambiguity: the range-trade invalidation clause inverts in a reachable corner (a reversal bar can produce a trigger below the stop-loss, serving a long recorded born-invalidated), the spec doesn't say what should happen there, and the rule is that a developer facing an unimplementable detector should drop it and surface it rather than improvise. We chose: both — write a fail-closed "degenerate trigger reference" clarification into the spec first, then patch the code to void it, and surface the whole thing for an owner ruling. Reversible: yes — one code guard plus the spec paragraph.
- iter-6 · goal-decomposer — Ambiguity: whether documenting an already-shipped, already-tested reading (the capitulation detector's whole-decline-leg definition) into the canonical spec, with zero behavior change, needs a prior owner ruling or can proceed as a doc-only edit. We chose: scope it as a developer-executed, documentation-only spec edit with a source-scan test proving the code lines didn't move — the same pattern this session had already ratified three times. Reversible: yes

## Quick verify

From `reports/phase-goal-playbook-iter-8-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Scroll to the very bottom of the page
3. In the "Playbook Evidence" panel's main table, find a row for setup `open_high_break`, side `long`, measure `5m`
4. In the same table, find a row for setup `open_high_break`, side `long`, measure `1h`
5. Scroll down a little further to the "Invalidation breaches" heading

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-playbook-iter-8.md |
| Dev handoff | — | docs/handoffs/goal-playbook-iter-8-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-playbook-iter-8-review.md |
| Browser QA | PASS | reports/phase-goal-playbook-iter-8-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-playbook-iter-8-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-playbook-iter-8-user-visible-changes.md |
| What to click | — | reports/phase-goal-playbook-iter-8-what-to-click.md |
| UI surface map | — | reports/phase-goal-playbook-iter-8-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-playbook-iter-8-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-playbook-iter-8-ux-regression.md |
| QA | PASS | reports/qa/goal-playbook-iter-8-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-playbook-iter-8-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-playbook-iter-8-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-playbook/iter-8/eval.md |
| Journey history | — | runs/goal-session-playbook/state/journey-history.json |
