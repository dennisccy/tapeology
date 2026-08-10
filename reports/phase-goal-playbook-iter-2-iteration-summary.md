# Iteration Summary — goal-playbook-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-10
**Iteration:** 2

## In plain words

**What you can do now:** You can still watch a simulated ticker's live buy-and-sell pressure, load a real stock's chart with support-and-resistance walls drawn on it, and run the desk's daily screen for a ranked briefing with forward-looking return numbers — all of that keeps working exactly as before. Behind the scenes, the desk now also spots a stock's "opening range breakout" AND measures what price did afterward for each one it finds, using the same measuring rules it already trusts elsewhere — though there's still no button for any of this yet; only someone with direct technical access can ask for it today.

**What changed this time:** Nothing changed on the pages you can already click through — Cockpit, Structure, and Desk all look and behave exactly the same. Behind the scenes, the desk learned to measure what happened after each opening-range breakout it spots — how price moved over the next few minutes and hours, and an honest note about whether price later crossed the danger line that would call the pattern off. A separate double-check also re-ran the whole product top to bottom and confirmed nothing that already worked had broken.

**What's next:** Next, the desk will put this pattern-spotting and measuring work on the Desk page itself, with a button an operator can actually see and press.

## Headline

The desk can now say what price did after each signal it finds.

## Direction

**Signal:** improving
**Why:** J-02 "Every signal measured" moved from failing to passing this iteration — the desk now measures every detected opening-range signal using `desk_forward.py`'s own imported (not copied) forward-return, dual-MDD, and seeded-baseline conventions, verified by a byte-identical convention-identity test and a suite jump to 2025 pass / 8 skip. J-01 re-verified unchanged and J-10's outstanding golden-replay evidence gap from iter-1 was explicitly closed this iteration (PASS 1/1). The evaluator's next-step recommendation targets J-03 next, the first Playbook UI surface on `/desk`, so the era keeps moving forward at its natural dependency pace.

**Trend (last 3 iters):**
- Newly passing this iter: J-02
- Newly passing in last 3 iters total: J-01 (iter-1), J-02 (iter-2)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: iter-1: 1 critical (found and fixed in the same iteration) + 1 minor (opened, then resolved in iter-2); iter-0 and iter-2: none new
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** The desk can now say what price did after each signal it finds. J-02 "Every signal measured" is genuinely done: every detected opening-range break carries a forward measurement made with the desk's existing measuring rules, plus an honest note about whether price later traded through the book's own invalidation level. I checked this myself rather than trusting the write-ups — I re-ran the whole backend test suite (2025 pass, 8 skipped, nothing failed), read the new code to confirm the measuring maths is borrowed from the existing rail instead of copied, and confirmed by git that none of the protected files and none of the website files changed. The kept-product check that was skipped last time was run this time and passed, and I opened its screenshot to confirm it.

## What was done

- Product changes: apps/backend/app/research/desk_playbook.py, apps/backend/app/research/desk_playbook_compute.py, apps/backend/app/research/desk_playbook_log.py, apps/backend/app/research/desk_routes.py, docs/playbook-detector-spec.md, POST/GET/POST-cancel /research/desk/playbook/compute, GET /research/desk/playbook/runs
- Extended `compute_playbook` in `desk_playbook.py` to measure every detected opening-range signal in the same walk: forward return/dual-MDD/truncation (imported verbatim from `desk_forward._measure_from`, zero diff to that file) plus an honest `invalidation_breached` disclosure.
- Added seeded, cross-symbol baseline anchors and a per-(setup, side) summary block, reusing the rail's own averaging helpers and capped at the rail's existing pooling constant.
- Built new `desk_playbook_compute.py` (single-flight compute manager + CLI) and `desk_playbook_log.py` (terminal-state-only run ledger), plus four new routes on `desk_routes.py` for triggering/polling/cancelling a playbook compute and reading its run ledger.
- Closed three audit-flagged test gaps (T1 x2, T3) with real `compute_playbook`/detector-level fixtures, and two documentation-only spec catch-ups (B3, B4) — zero code/value change, source-diff verified.
- Ran the J-10 "kept product stands" golden-script replay explicitly (the evidence gap iter-1 left open) — PASS 1/1, closing that gap.
- Full backend suite: 2025 passed / 8 skipped / 0 failed (up from the 1969 floor), fingerprint `08e471b10130e1e2` unchanged, zero diff to every frozen module and to `apps/frontend/`.
- Verified 1 required-still-passing journey (J-10) pass browser QA via the golden-script replay; J-01 and J-02 are keyless/automated with no browser step and were correctly SKIPped.

## What's left

- Journey J-03 (The Playbook lands on /desk) failing — no UI surface exists yet; targeted next.
- Journey J-04 (The continuation family — JBE, DBI, cup-and-handle) failing.
- Journey J-05 (The climax family — capitulation entry, euphoria marker) failing.
- Journey J-06 (The range family — range trades, double top/bottom) failing.
- Journey J-07 (The back-scan — every recorded session, resumable and append-only) failing.
- Journey J-08 (The evidence view — distributions beside the null, min-n honest) failing.
- Journey J-09 (MCP contract v4 — 20 read-only tools) failing — MCP still at 18 tools.
- Journey J-10 (The kept product stands — regression sentinel) still partial — its own wording needs 20 Claude tools, which can't be true until J-09 ships; nothing about the kept product itself is broken.
- Two interpretive design calls flagged for the reviewer/auditor: the cross-symbol baseline pool reuses an existing rail constant rather than a spec-named one, and a new `signals_beyond_cap` field isn't named verbatim in the iteration spec.
- An unused import flagged by review (`desk_routes.py:126`) still needs removing.

## Next step

Build **J-03 "The Playbook lands on /desk"** next, at full depth. This is the first time the playbook becomes visible to the person using the product: a session-date box, a Run Playbook button with live progress and a cancel, the signals table with its forward numbers, and honest wording when nothing has been computed yet. It needs a real browser pass with screenshots, and it touches the protective tests that guard the desk page, so the fuller review-and-audit pass is worth it.

Ask that iteration to also carry four small items rather than making them their own iteration: (1) show the exact sentence "measurement not recorded in this record" for records made before measurement existed — today the backend leaves the measurement block out, which is honest, but the sentence the goal names has never been written anywhere; (2) remove the unused import flagged in the review (`desk_routes.py:126`); (3) use the rail's own `_side_sign` helper instead of repeating the two-line long/short mapping twice (`desk_playbook.py:170` and `:281`), as the coherence audit advises; (4) before adding more setup families, fix the baseline-anchor draw so it works when one symbol fires more than one signal of the same setup in a session — today it hard-codes one anchor per symbol (`desk_playbook.py:557`) and re-seeds with the same string each time, which is correct only because opening-range breaks can fire at most once per symbol per day.

In one sentence: next, put the playbook on the Desk page where the operator can actually see and run it, and fold the four small clean-ups above into that same piece of work.

## Assumptions made

- iter-3 · goal-decomposer — Ambiguity: The iter-2 evaluator's next-step recommendation asked to "reuse the rail's own long/short helper instead of repeating it," naming `desk_forward.py`'s `_side_sign` as that helper; `docs/goal.md` never says whether a carried recommendation must be followed literally even when closer reading shows the named helper is semantically wrong for the target vocabulary. We chose: did NOT literally reuse `_side_sign` (called with the playbook's own vocabulary it would silently flip every short signal's sign positive); instead consolidated the three duplicated long/short literals into one new playbook-owned `side_sign` helper, satisfying the actual concern (one owner, not three copies) without importing an incompatible helper. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: The critical anti-goal "No threshold exists outside the spec" sits against a new numeric knob the code depends on: the cross-symbol pooling cap for `baseline_anchors`/`summary`, implemented via the rail's existing `DESK_FORWARD_MAX_TOUCHES_PER_ROW`, which appears in no row of the spec's own constants table. We chose: not a violation — the spec's §0 Measurement paragraph already delegates this area verbatim to the rail, the number is imported rather than invented, and it's echoed into `playbook_parameters()` so a future change re-keys records; recorded as an observation only. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's acceptance text says J-01-era records must serve with the honest "measurement not recorded in this record" sentence, but the product instead serves a structural absence (no `forward` key, empty pooled fields) plus its own register sentence — the same literal string is also listed under J-03 as UI copy. We chose: counted J-02's absence requirement as met by the structural, machine-detectable absence (proven never-backfilled and SHA-256-unchanged by test), and moved the literal sentence into J-03's binding carry list, where the goal itself places it as page copy. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: The iter-1 audit flagged `PLAYBOOK_OR_MIN_1M_BARS` missing from spec §1's table (B3) and a `principles` mapping existing in code without matching spec prose (B4), each needing an "owner ruling" before further code relies on them; neither the audit nor the goal says whether that owner must be the human operator or can be resolved inside the goal-mode chain when the fix is zero-behavior-change documentation catch-up. We chose: scoped both into iter-2 as developer-executed, documentation-only spec edits — neither invents a threshold, changes a value, or alters tested behavior, both just catch the spec up to what iter-1 already shipped. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: `docs/goal.md` marks "No threshold exists outside the spec" as critical, but `desk_playbook_detect.py:276` settles a spec rule in code without inventing any threshold or sweeping anything; the auditor was genuinely unsure between GAP and IMPORTANT, and critical severity would force a REGRESSION halt. We chose: minor, not critical — nothing is fabricated, no threshold is invented, no sweep exists, and the field is a disclosure label that gates no computation; recorded as an open minor violation requiring an owner ruling before J-08. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-10's required verification (TC-14, the golden-script replay) was executed by nobody, and the auditor recommended recording J-10 as `unknown-by-replay`; the goal never says whether a sentinel journey keeps its status when the iteration provably touches none of its surfaces. We chose: kept J-10 at `partial` (its prior status) under the evidence-durability rule — the frontend diff is empty and the only shipped-file change is `desk_routes.py`, so iter-0's screenshots still show the current product; the un-run replay is recorded as an explicit gap. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-10's acceptance text bundles kept-product behaviour with a clause that only becomes true at the END of the era ("MCP = exactly 20 tools"), and the goal never says how to score J-10 while the era is mid-flight. We chose: `partial` — the kept half is fully evidenced, while the 20-tool clause is recorded as not-yet-satisfiable rather than as a failure of the kept product, mirroring the previous era's baseline sentinel journey. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-playbook-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-playbook-iter-2-dev.md |
| Review | PASS | reports/reviews/goal-playbook-iter-2-review.md |
| Browser QA | PASS | reports/phase-goal-playbook-iter-2-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-playbook/iter-2/eval.md |
| Journey history | — | runs/goal-session-playbook/state/journey-history.json |
