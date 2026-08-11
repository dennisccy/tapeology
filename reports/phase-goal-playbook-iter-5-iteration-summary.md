# Iteration Summary — goal-playbook-iter-5

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-11
**Iteration:** 5

## In plain words

**What you can do now:** On the Desk page, pick a date and run the Playbook to see five kinds of chart pattern the desk finds for that day: opening-range breakouts, Jump-Base Explosions, Drop-Base Implosions, Cup and Handles, and now Capitulation reversals — each shown with what happened afterward compared to random chance. Any signal that fires shortly after a sharp reversal now carries a "recent climax" tag for the first time. You can still watch a simulated ticker's buyer/seller pressure live, load a real stock's chart with support-and-resistance zones drawn on it, and run the desk's daily screen across about a hundred companies for a ranked briefing with forward-looking return numbers.

**What changed this time:** The Desk page's Playbook Signals table now finds a fifth pattern, Capitulation — a sharp panic decline that reverses. Any pattern (of any kind) that fires soon after this kind of reversal now shows a "recent climax" note for the first time. The descriptive sentence printed beside the table, and the page's own heading text, were also widened to name all five patterns instead of just the first one — closing a wording gap left over from last time.

**What's next:** Next the desk will learn the range family of patterns (range trades and double-top/double-bottom), built with an extra, deeper safety review this time — the last two attempts to run that deeper review got turned into a faster pass by the system's own time limit.

## Headline

The climax family works and is visible on the Desk page.

## Direction

**Signal:** improving
**Why:** This iteration shipped J-05 "The climax family — capitulation entry, euphoria marker," now passing browser QA and unit tests — the fifth of ten Must-have journeys is green, continuing an unbroken streak of one new journey landing every iteration since iter-1. J-01 through J-04 were all re-verified passing with zero regressions. The evaluator escalated only because the plan called for a deep pass with an auditor and the engine's own timing rule turned it into a fast one for the second iteration running, leaving two detector rules settled in code rather than in the written spec — not because anything broke.

**Trend (last 5 iters):**
- Newly passing this iter: J-05
- Newly passing in last 5 iters total: J-01 (iter-1), J-02 (iter-2), J-03 (iter-3), J-04 (iter-4), J-05 (iter-5)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 7 opened across iters 1-5 — 1 critical (iter-1, found and fixed inside the same iteration); 6 minor (iter-1: 1, resolved iter-2; iter-3: 1, resolved iter-4; iter-4: 2, one found-and-fixed inside the same iteration and one resolved iter-5; iter-5: 2, both still open)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The climax family works and is visible on the Desk page. I opened both new pictures myself: one shows a "Capitulation" signal for AAA with its four new numbers on screen, the other shows a signal tagged "euphoria recent" for the first time, and neither picture contains a "Euphoria" row of its own — which is exactly what the goal asks for. I also re-ran the whole backend test suite to the end (2079 passed, 8 skipped) and checked the pin and the protected files by hand. I am asking for a deeper next iteration, not because something here is broken, but because this iteration was planned as a deep one, ran in fast mode, and again nobody with an auditor's brief read the new detection maths — and the developer had to decide two rules by himself that the written spec does not spell out.

## What was done

- Product changes: apps/backend/app/research/desk_playbook.py, apps/backend/app/research/desk_playbook_detect.py, apps/backend/tests/test_desk_playbook.py, apps/backend/tests/test_desk_playbook_detect.py, apps/backend/tests/test_desk_playbook_guards.py, apps/backend/tests/test_desk_ui_guards.py, apps/frontend/app/desk/page.tsx, apps/frontend/lib/types.ts
- Implemented `detect_capitulation` (vertical decline into a climax bar, reversal within the bounce window, re-anchoring on new lows) and `detect_euphoria` (its mirror, marker-only — never appended to any signal, pool, or summary key).
- Wired capitulation into the compute walk and `PLAYBOOK_SETUPS` (now 6 entries); euphoria deliberately excluded since it is never a recorded setup.
- Added the forward-only `_decorate_markers` pass so signals firing after a same-symbol climax now carry real `euphoria_recent`/`capitulation_recent` flags (previously always served `false`).
- Widened `PLAYBOOK_REGISTER` and both `/desk` copy spots to name all five shipped pattern families, closing iter-4's open anti-goal item, with a new pinned-text guard so the next widening cannot silently drift.
- Extended the frontend (`types.ts`, `page.tsx`) with the capitulation geometry branch and setup label; re-took the carried DBI screenshot with the corrected "descending base" label.
- Full backend suite: 2079 passed / 8 skipped (up from the 2061 floor); zero diff to every protected file; fingerprint unchanged (`08e471b10130e1e2`).
- Verified 6 of 6 target/regression journeys pass browser QA (J-01, J-02, J-03, J-04, J-05, J-10).

## What's left

- Journey J-06 "The range family — range trades, double top/bottom" failing (not yet built)
- Journey J-07 "The back-scan — every recorded session, resumable and append-only" failing (route does not exist)
- Journey J-08 "The evidence view — distributions beside the null, min-n honest" failing (route does not exist)
- Journey J-09 "MCP contract v4 — 20 read-only tools" failing (18 of 20 tools shipped)
- Journey J-10 "The kept product stands" held at partial — everything shipped still works, but its own wording asks for 20 tools until J-09 ships
- Two detector rules (what `decline_bars`/`decline_mbr` mean, and the re-anchoring rule) are settled in code but not yet written into the spec — open minor item to close before J-06
- Two run-history ledger rows point at record files nobody can find (pre-existing, not caused by this iteration, still unresolved) — needs checking before J-07's back-scan reads that ledger
- Two owner-ruling questions carried from iter-4 remain open (the 1.5x jump-to-base gate reachability; the cup's rim constant naming), now joined by a third about the "decline bars" wording

## Next step

Build J-06 "The range family" (range trades and double top/bottom) next, and run it as a deep iteration with the auditor — the deep pass has caught a real honesty bug each time new detection maths landed, J-06 is the biggest remaining piece of detection maths (three detectors, one of which the written spec itself marks as provisional), and the last two attempts at a deep pass were both turned into fast passes by the engine's own timing rule. Carry three small items inside the same cycle: write into the detector spec what `decline_bars` and `decline_mbr` actually mean and how re-anchoring works (no number or behavior changes); check the two run-history rows that point to records nobody can find, and make every test and browser run write its run history to the same scratch folder as its records; and record a stored replay script for J-05 so the climax family is re-checked automatically from now on. Three questions still wait for the owner: whether the 1.5x jump-to-base rule is meant to be unreachable, whether the cup's rim test should use the rim number the spec names, and whether the whole-leg reading of "decline bars" is the one he wants.

## Assumptions made

- iter-5 · goal-evaluator — Ambiguity: Two terminal "recorded" rows in the operator's own run ledger name record files a filesystem-wide search cannot locate; unclear whether this means a record was deleted (critical) or a run wrote its record to a scratch dir while its ledger row went to the operator default (hygiene). We chose: minor and explicitly unconfirmed, not critical, and not attributed to this iteration — both rows predate iteration 5's start and its diff contains zero store/ledger code; recorded as an open minor item to answer before J-07's back-scan reads this ledger. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: The critical "no threshold exists outside the spec" anti-goal sits against two RULES this iteration settled in code — the exact meaning of `decline_bars`/`decline_mbr` and the concrete re-anchoring walk — which the spec states only loosely. We chose: minor, not critical — no threshold was invented, tuned, or swept (all constants already in spec, zero spec diff this iteration); recorded as an open minor violation to close before J-06 adds three more detectors. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: J-05's acceptance text doesn't say whether the euphoria/capitulation decay window runs forward, backward, or both, or whether decoration ever crosses symbols. We chose: forward-only (a marker may decorate a later same-symbol signal, never the reverse) and same-symbol-session only — the only reading consistent with the era's "no lookahead" anti-goal; a dedicated structural guard test now machine-checks this reading. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: The critical "no threshold outside the spec" anti-goal sits against two constants introduced this iteration whose spec table rows were added in the same commit as the code. We chose: not a violation — both values already existed in spec prose before this iteration (only naming/tabulation is new), following the session's own iter-2 precedent; flagged for owner visibility. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: whether the register/blurb text still naming only "opening-range-break signals" (while new records already carry jbe/dbi/cup_handle signals) is a J-04 acceptance failure or an era-level copy defect. We chose: era-level OPEN minor violation, not a J-04 failure — J-04's own acceptance criteria don't mention the register; recorded as unresolved until fixed (closed the following iteration). Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: whether a screenshot predating an in-iteration fix (the DBI base-shape label) still satisfies a browser acceptance line. We chose: J-04 passing with evidence_makeup: true — the DBI row is legible with its full geometry in that screenshot, and the fix changed only one descriptive word to match the measurement already served; a one-row re-capture rides the next iteration as a passenger task. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: the browser-QA lane planted a synthetic test record into the operator's live playbook store to exercise a test case; unclear whether this is a critical violation (forcing a REGRESSION halt) or a hygiene defect. We chose: minor, not critical — nothing was rewritten, the record self-discloses as a fixture, it is git-ignored, and the "one signature only" rail keeps it out of any distribution; recorded as an open minor violation requiring deletion before the era can be declared achieved. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-03's provenance line names "parameters hash" but no such field is served anywhere, and the acceptance text doesn't enumerate fields. We chose: counted the provenance requirement as met by record id + `playbook_input_signature` + `config_fingerprint` + a rendered sentence stating what the signature hashes; rejected computing a parameters hash client-side as a single-source-of-truth violation; flagged for an owner ruling before J-07/J-08 reuse this line. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: whether a carried next-step recommendation (reuse the rail's own long/short helper `_side_sign`) must be followed literally even when closer reading shows the named helper is semantically wrong for the target vocabulary. We chose: did not literally reuse `_side_sign` (it would silently flip every short signal's sign); instead consolidated three duplicated literals into one new playbook-owned helper, satisfying the actual concern without importing an incompatible helper. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: whether the critical "no threshold outside the spec" anti-goal is violated by a new numeric knob (the cross-symbol pooling cap) the code depends on but that appears in no spec row. We chose: not a violation — the spec's own Measurement paragraph already delegates this area verbatim and the number is imported, not invented; recorded as an observation only. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's acceptance text quotes an exact absence sentence that exists nowhere in the product, which instead serves a structural, machine-detectable absence. We chose: counted J-02's requirement as met by the structural absence (proven never-backfilled and SHA-256-unchanged by a dedicated test), and moved the literal sentence into J-03's binding carry list where the goal itself places it as page copy. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: whether an audit-flagged documentation gap (a missing spec table row and an undocumented code mapping) needs a human operator's ruling or can be resolved inside the goal-mode chain when the fix is zero-behavior-change documentation catch-up. We chose: scoped both as developer-executed, documentation-only spec edits that transcribe values/rules already present in spec prose or code comments into the spec's table — neither invents a threshold nor changes behavior. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-playbook-iter-5.md |
| Dev handoff | — | docs/handoffs/goal-playbook-iter-5-dev.md |
| Review | PASS | reports/reviews/goal-playbook-iter-5-review.md |
| Browser QA | PASS | reports/phase-goal-playbook-iter-5-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-playbook/iter-5/eval.md |
| Journey history | — | runs/goal-session-playbook/state/journey-history.json |
