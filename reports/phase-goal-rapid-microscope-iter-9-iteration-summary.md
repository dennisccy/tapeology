# Iteration Summary — goal-rapid-microscope-iter-9

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-18
**Iteration:** 9

## In plain words

**What you can do now:** On the Desk page, see an honest readiness report showing how much tick-by-tick market data is on hand and whether it's enough to trust a study. Behind the scenes, the product also reads buying and selling pressure tick by tick without peeking at the future, matches chart-pattern signals to that activity, keeps a tamper-evident record of every trading idea it screens (including the ones that fail), and can honestly refuse a result — for example saying "you have 11 days of history, you need 105" — instead of guessing.

**What changed this time:** Built a new locked "Vault" behind the Desk page's data-readiness area, able to seal away newly recorded market data so nobody — not even the product's own reports — can peek at it early. Taught the file list, the corpus-readiness panel, the profit-comparison reports, and the pattern-screening tool to skip and honestly count anything sealed instead of accidentally reading it. Nothing is sealed yet, so nothing looks different on screen today — but a safety review found a way to work out which recordings would be hidden just by watching what's missing from the public list, so real data won't go into the vault until that gets closed.

**What's next:** Next, the team plans to build the step that makes sure every failed idea still gets counted honestly when handed to final review — but no real market data will go into the vault until you decide how to close the last privacy gap.

## Headline

Validation Vault (J-06 step 3) ships; sealed-membership leak still open, gating step 4 until ruled

## Direction

**Signal:** holding
**Why:** J-06 step 3 (the sealed-evidence vault) shipped and passed three audit rounds under two owner rulings (spec revisions r3, r4), closing two long-carried items (the exposure-registry sealed filter, the §2.6 rule-text stamp) — but J-06 itself stays partial because the auditor's own CRITICAL B2 shows the vault's core secrecy promise isn't achieved yet (cartesian closure of the public dataset listing recovers the sealed set exactly, 5 of 5 in the probe). No journey regressed, J-01–J-05 all independently re-verified against real data, and the full suite grew from 3,092 to 3,166 with 0 failures, so the session's engineering discipline (independent auditor in the loop) keeps paying off even though no journey formally flipped to "passing" this round.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-05 (iter-7)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 4 critical, all introduced-and-fixed within the same round (3 in iter-5, 1 in iter-7) — none carried open; a further string of minor items opened/closed across iters 5-9, with 3 new minor items opened in iter-9 (all open, owner-owed); 0 unresolved critical as of this iter
- Iters with no journey state change: 3 of last 5 (iter-6, iter-8, iter-9)

**Latest evaluator reasoning:** "I took nothing on trust. I ran the whole test suite myself and got 3,166 tests, 3,158 passed, 8 skipped, 0 failures — and I ran it AFTER every file edit in the tree, so it is the true current number. The quality report's 3,130 is out of date and should not be quoted. I opened the pictures instead of reading the rows: the Desk page really shows your corpus panel with real numbers and honest 'floor not met' lines, the Structure page really loads its full wall map with the pinned AAPL band reading 300.11-302.2, and the Cockpit really watches a live tape."

## What was done

- Product changes: apps/backend/app/research/vault.py (NEW), apps/backend/app/research/micro_routes.py (new route GET /research/desk/micro/vault), apps/backend/app/research/datasets.py, apps/backend/app/research/routes.py, apps/backend/app/research/walkforward.py, apps/backend/app/research/tick_recorder.py, apps/backend/app/research/edge_report.py, apps/backend/app/research/edge_report_cache.py, apps/backend/app/research/pnl_scan.py, apps/backend/app/research/pnl_ledger.py, apps/backend/app/research/scout.py, apps/backend/app/research/micro_join.py, apps/backend/app/research/micro_readiness.py, apps/backend/app/research/micro_snapshots.py, apps/backend/app/research/desk_screen.py, apps/backend/app/research/desk_screen_compute.py, apps/backend/app/research/setups.py
- Built `vault.py`: universe registration with a committed rule-hash, HMAC-based seal assignment (secret sourced from `TAPEOLOGY_VAULT_SECRET_FILE`, never logged — only its sha256 recorded), and a one-way `sealed → assigned → exposed` hash-chained shard-lifecycle ledger (TR-2/4/12/20 all green on fixtures).
- Shipped `GET /research/desk/micro/vault` (opaque-only serving for a sealed shard; full symbol/date/family provenance from `assigned` onward) — no UI consumer yet.
- Closed two carried items in the same build: the exposure-registry sealed filter (iter-6's latent hole — a freshly sealed shard can no longer be marked "already exposed") and the §2.6 vendor rule-text + verification-note stamp (iter-8's gap).
- Fix round r3 (owner-ruled, spec revision): replaced the raw dataset id and raw checksum a sealed shard served with opaque HMAC surrogates and salted commitments; added seal-aware refusals on the dataset routes, MCP, and backtests; rewrote TR-2 as an adversarial sweep over every registered GET route.
- Fix round r4 (owner-ruled, after the second audit found the `/desk` compute buttons could still read sealed shards): every corpus-wide report (edge report, PnL sweep, snapshot build, Scout, desk screen, walkforward, readiness) now excludes withheld shards through one shared predicate and discloses a `withheld_excluded` count instead of silently shrinking.
- Full backend suite: 3,166 collected / 3,158 passed / 8 skipped / 0 failed (the evaluator's own post-edit run, superseding the QA report's stale 3,130); frozen foundations re-verified (fingerprint `08e471b10130e1e2`, all six `referee_*.py` hashes unchanged, 22-tool MCP list, real `.data/datasets` store byte-identical before/after).
- Verified 9/9 executed browser-QA checks pass (J-01 replay + UT-01..UT-08, including the "Validation Vault section is genuinely absent" proof); J-02–J-05's on-screen re-checks were deferred for iteration budget but independently re-derived by the evaluator against real data and held.

## What's left

- Journey J-07 ("Graduation — provenance in, nothing laundered out") failing — not yet built; entirely fixture-based, needs no owner ruling, and is named as the next target.
- Journey J-08 ("The surface and MCP v6 — the funnel is visible") failing — no Validation Vault UI section yet; MCP still the 22-tool contract, not the v6/26-tuple.
- Journey J-09 ("The pilot studies — three predeclared questions, honest answers") failing — the three study ids still exist only as floor-unmet rows; no study spec is ledgered.
- Journey J-06 ("The recorder and the Vault") partial — step 3 of 5 landed, but audit CRITICAL B2 (carried) shows §7.3's "sealed membership cannot be inferred from public information" is NOT achieved as built: the public dataset listing alone still lets an attacker recover the sealed set exactly by cartesian closure (5 of 5 in the auditor's probe). This is a HARD GATE on steps 4-5, pending an owner ruling.
- Journey J-10 ("The kept product stands") partial — 19 of 22 leakage traps armed; TR-3 (accessor fence), TR-17 (future-event availability), and TR-22 (exposure registry) are still absent.
- Audit CRITICAL B3 (carried): the recorder's live compute-progress route (`GET /research/desk/micro/recorder/compute`) still serves a sealed shard's symbol/date/raw dataset id once real tape exists — not reachable today since the recorder has never run for real.
- Two IMPORTANT owner-ruling items carried: B4 (the vault's withholding predicates fail OPEN, not closed, on a corrupted ledger — now 11 consumers depend on the answer) and B5 (a frozen `referee_*.py` file counts withheld shards, colliding with the era's byte-identical freeze pin).
- Two standing owner decisions still waiting since round 2: the one-quote-early depletion timing stamp, and whether J-01's readiness photo must show the real 12-symbol-day corpus.
- The Validation Vault has no `/desk` UI section yet and no operator-facing way to register a universe or seal a shard (J-08 / step-4 scope).

## Next step

Build **J-07 "Graduation — provenance in, nothing laundered out"** next, under the full pipeline with the independent checker. It is the next step in order, it runs entirely on made-up test data, and it needs no decision from you — so it is real work that can start immediately while the vault questions wait. Keep the independent checker in the loop: it has now found a real honesty fault in five of the five full rounds it has run, and J-07 is exactly the kind of work where one would hide (it is the step that must carry every failed trial into the export, with nothing quietly dropped).

Do **not** let the next round record real tape. J-06's last two steps are blocked until you decide three things, all the same kind of question you have already answered twice:

1. **The big one.** Anyone can still work out which recordings are hidden, by listing the public ones and noticing which combinations are missing. Pick one: hide the whole batch's names and dates until the batch is finished with; add extra recordings so "missing" no longer means "hidden"; or accept it in writing and state plainly that hiding protects the DATA, not the MEMBERSHIP.
2. **Damaged-record behaviour.** Should a damaged vault record make everything refuse (safe), or make everything open (what happens today)?
3. **A frozen file.** One of the six frozen judge files counts hidden recordings toward a research threshold; fixing it means touching a file this era promised never to touch.

Please also settle the timing stamp that is one quote too early — it has been waiting since round 2. Carry three passenger items: fix the recorder progress page so it stops showing a hidden recording's name and date (cheap, but do it after decision 1 sets the direction); add the three missing traps TR-3, TR-17 and TR-22; and re-run the browser check, since this round's pictures were taken before the last fix landed (I re-computed the values by hand and they match, so nothing is scored down, but the pictures should be refreshed). One process note worth keeping: your ruling to split the work into smaller rounds rather than raise the clock budget WORKED — this round ran the full pipeline, the checker ran three times, and it caught a real fault everything else had passed. Keep scoping one step per round.

**In one sentence for you to act on:** approve building the Graduation step next, and answer the three vault questions above before any real tape is recorded or hidden.

## Assumptions made

- iter-9 · goal-evaluator (second) — Ambiguity: the audit carries two CRITICALs (B2 sealed membership recoverable by cartesian closure of the public dataset listing; B3 the recorder-compute route serving per-chunk symbol/date/raw dataset id) plus B4 (fail-open withholding predicate) and B5 (a frozen referee file counting withheld shards); the decision tree's default is REGRESSION on any unresolved critical anti-goal violation. We chose: record all four as OPEN but minor severity and return CONTINUE rather than REGRESSION, because every anti-goal condition names sealed shards and none exist yet (no vault ledger file on disk, seal/assign/expose have zero production callers, withheld_dataset_ids empty on both stores) — all four are hard-gated on J-06 step 4 in the journey note and next-step recommendation instead. Reversible: no in one direction — if step 4 runs before B2 is ruled, real tape gets sealed under a false guarantee and the manifests are immutable.
- iter-9 · goal-evaluator — Ambiguity: the iter-8 evaluator's precedent for holding a DEFERRED-BUDGET journey at passing leaned on evidence durability because those journeys' own modules were untouched that round; this round J-02/J-03/J-04/J-05's own modules all changed in the r4 fix round, so durability covers none of them and the evaluator's re-derivation is the sole basis. We chose: hold passing for all four with the deferral and the "durability does NOT cover this" caveat stated verbatim in each note, because the r4 change is provably value-neutral today (no vault ledger exists, withheld_dataset_ids is empty, exclude_withheld is the identity function until something is sealed) and each journey's own served value was independently re-derived against real data. Reversible: yes — golden replay scripts for J-01–J-06/J-10 now exist, restoring true lane-level verification next iteration.
- iter-9 · OWNER RULING #2 — Ambiguity: the re-audit's CRITICAL B2 found that r3's sealed-shard refusals are route-scoped, but the Edge Report and PnL sweep each enumerate the whole dataset store directly, so a corpus-wide report/sweep would read a sealed shard's events and republish its identity via the backtests list and the append-only PnL ledger. We chose (owner ruling, spec revision r4): every corpus-wide enumerator excludes withheld shards and discloses a withheld_excluded count — never the ids — because the goal's critical rail already requires sealed data be refused everywhere fail-closed, and both call sites already carry "a partial report is a misleading report," which rules out silent exclusion. Reversible: no — r4 is a named revision; nothing re-keys since zero shards were sealed when it landed.
- iter-9 · OWNER RULING — Ambiguity: the audit's CRITICAL B1 found spec §7.5(r2) required an opaque shard_id but the implementation served the real dataset id, and also served the raw checksum commitment — itself a join key to the public dataset record — so closing the leak necessarily changes published REST/MCP contracts. We chose (owner ruling, spec revision r3, option 1 of 3): opaque surrogate ids plus seal-aware refusal — a surrogate shard_id with no derivable relation to the dataset id, an HMAC-committed checksum revealed only at exposure, and typed refusals for a sealed id on the dataset routes, MCP tool, and readiness. Reversible: no — r3 is a named revision; nothing re-keys since zero shards were sealed when the ruling landed.
- iter-9 · goal-decomposer (second) — Ambiguity: the iter-8 evaluator named a latent hole (the walk-forward exposure registry's seed marks every dataset as exposed with no sealed filter) without prescribing the fix's shape, since the spec predates vault.py (the only source of the "sealed" concept). We chose: the legacy tick corpus's exposure-registry seed excludes any dataset id vault.py currently reports sealed — a sealed shard stays invisible to that seed until the vault's own lifecycle exposes it — as the minimal change restoring the intended invariant without inventing a second exposure concept. Reversible: yes — a pure exclusion at seed time; a later-exposed shard simply stops being excluded on the next seed pass.
- iter-9 · goal-decomposer — Ambiguity: goal.md commits vault.py to serving GET /research/desk/micro/vault but doesn't say whether an operator-facing CLI/route for universe REGISTRATION must ship in the same iteration as the module. We chose: ship the read-only GET .../vault route now but not a universe-registration CLI, because no operator act in this iteration or the next calls registration standalone — it only becomes operator-facing when the credentialed tranche step runs, which the operator's own ruling deliberately deferred. Reversible: yes — the deferred step's iteration adds the CLI/manager wiring calling the same library functions this iteration ships.
- iter-8 · goal-evaluator (second) — Ambiguity: the methodology says a DEFERRED-BUDGET row means a journey "was NOT tested" and keeps its prior status, but doesn't say what last_verified_iter should read when the lane deferred a journey the evaluator itself independently re-derived against the operator's real store in the same iteration. We chose: record last_verified_iter as that iteration for those journeys, with the deferral stated verbatim in each journey's note and the eval table's status cell, so no reader mistakes an endpoint-level re-derivation for an on-screen re-check. Reversible: yes — the next iteration's replay scripts restore lane-level verification.
- iter-8 · goal-evaluator — Ambiguity: the methodology's decision tree fires ESCALATE on "cross-cutting ambiguity/complexity" but doesn't say whether the engine's own budget-driven demotion of a declared-full spec (skipping the independent auditor) counts as such a trigger, nor whether skipping 4 of 6 required-still-passing re-checks does — read narrowly this was a clean, progressing iteration and CONTINUE would be correct. We chose: ESCALATE, because the diff touched the exact surface where the independent auditor has caught a critical, in-run-fixed honesty fault in 4 of the last 4 full iterations, this iteration had no auditor pass at all, a real spec-conformance gap existed that the lean lanes missed, and the next step (the vault) is where an already-known latent hole turns critical. Reversible: yes — a later iteration can return to CONTINUE/lean once the vault lands and budget stops forcing trims.

## Quick verify

From `reports/phase-goal-rapid-microscope-iter-9-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Scroll all the way to the bottom of the page, passing every section header on the way down
3. Click the "Microscope Readiness" section header
4. Open `http://localhost:3301/` (the cockpit page)
5. Type `SIM-BUYER` into the field labeled "Ticker", then click the "Watch" button

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-rapid-microscope-iter-9.md |
| Dev handoff | — | docs/handoffs/goal-rapid-microscope-iter-9-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-rapid-microscope-iter-9-review.md |
| Browser QA | PASS | reports/phase-goal-rapid-microscope-iter-9-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-rapid-microscope-iter-9-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-rapid-microscope-iter-9-user-visible-changes.md |
| What to click | — | reports/phase-goal-rapid-microscope-iter-9-what-to-click.md |
| UI surface map | — | reports/phase-goal-rapid-microscope-iter-9-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-rapid-microscope-iter-9-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-rapid-microscope-iter-9-ux-regression.md |
| QA | PASS | reports/qa/goal-rapid-microscope-iter-9-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-rapid-microscope-iter-9-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-rapid-microscope-iter-9-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-rapid-microscope/iter-9/eval.md |
| Journey history | — | runs/goal-session-rapid-microscope/state/journey-history.json |
