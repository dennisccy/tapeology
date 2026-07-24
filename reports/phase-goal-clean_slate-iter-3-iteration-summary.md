# Iteration Summary — goal-clean_slate-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-24
**Iteration:** 3

## In plain words

**What you can do now:** Watch a ticker's tape — simulated, live, or a recorded historical replay — and see it settle into a clear market read, with a price chart that shows candles, lets you switch time windows, shades support-and-resistance zones, and keeps updating live as new bars form. Open the Structure page, load a stock and a date, and see its strongest price "walls" highlighted. The product is exactly the two pages it set out to be — Cockpit and Structure — since the old trade-journal, replay-studies, and performance pages were removed; visiting their old addresses still shows the site's normal "page not found" screen.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. This iteration tidied up the list of tools available to outside AI assistants that connect to the app: three tools that used to point at the now-removed journal, replay-studies, and performance features are gone, and every remaining tool was re-checked to confirm it still reports the exact same numbers as the website itself.

**What's next:** Next, the team will carefully retire some leftover internal settings and update an internal "version stamp" the app's saved numbers are tied to — a delicate step that must not change any of the numbers the app currently shows.

## Headline

MCP tool catalog trimmed to exactly 15 read-only tools; last pre-authorized red test now green

## Direction

**Signal:** improving
**Why:** J-03 (MCP contract v2 — 15 read-only tools) moved from failing to passing this iteration: independently re-verified via grep (zero hits for the three deleted tool identifiers, exactly 15 `types.Tool` blocks matching the I-6 set) and a fresh `pytest` run showing 29 passed / 0 failed — the one pre-authorized red test carried since iteration 1 is now green. J-01 and J-02 held passing, J-05's scoped "15 tools" sub-clause now holds too, and the fingerprint stayed frozen with zero anti-goal violations. Four iterations running have each moved a journey forward with no regressions, so direction remains healthy.

**Trend (last 4 iters):**
- Newly passing this iter: J-03
- Newly passing in last 4 iters total: J-01, J-02, J-03
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** "Lean, backend-only, keyless iteration that landed J-03 (MCP contract v2 — 15 read-only tools). A pure surgical deletion of the three dead `journal`/`analytics`/`studies` MCP proxies (whose target routes J-01/J-02 already 404'd), mirrored in the test contract, plus one new honest-404 regression test — diff is exactly the two named backend files. I independently re-verified the target: exactly 15 `types.Tool` blocks matching the I-6 set, zero deleted-tool identifiers, the MCP suite 29 passed / 0 failed (the one pre-authorized red test carried since iter-1 is now green), and the fingerprint frozen at `4d665603569b9dbf`. Not GOAL_ACHIEVED (J-04 failing, J-05 partial); progress made and coherence is COHERENCE-PASS → CONTINUE."

## What was done

- Removed the `journal`, `analytics`, `studies` MCP tool entries (`_STATIC_PATHS` rows + `types.Tool` blocks) from `app/mcp/__init__.py` — the MCP server now advertises exactly the 15 kept tools, with no reordering of the survivors.
- Trimmed `tests/test_mcp_server.py`'s `EXPECTED_TOOLS`/`LIVE_STATIC` to match, closing the one pre-authorized red test carried since iteration 1.
- Added a new regression test proving `get_endpoint`'s honest-404 contract holds for an actually-deleted route (`/research/journal`), distinct from the pre-existing synthetic-canary coverage.
- Re-ran the I-9 kept-route byte-comparison capture (`iter-3/kept-route-after.txt`) — 0 of 28 kept routes differ vs. iteration 2's capture.
- Re-confirmed the fingerprint unchanged (`4d665603569b9dbf`) and zero of the 13 pin sites live in either touched file.
- Ran the full backend suite fresh: 1164 passed / 7 skipped / 0 failed / 0 errors — the first literal "0 failed" claim since iteration 1.
- Verified 4 target journey(s) pass browser QA (J-01, J-02, J-03, J-05 sanity/regression checks — 4/4 PASS, 0 skipped).

## What's left

- Journey J-04 (The fingerprint epoch bump — §0.4 Path B) failing — Config field deletions, the fingerprint exclusion-set prune, and the 13 fingerprint-pin updates are still untouched, reserved for iteration 4.
- Journey J-05 (The kept product stands — regression sentinel) partial — full closure (Case Studies drill-in, full-suite-under-the-new-pin, cumulative diff-vs-inventory) still depends on J-04; this iteration only advanced its "MCP = 15 tools" sub-clause.
- Decision still pending, carried forward a third time: restore `SHOW_CASE_STUDIES` vs. operator rescopes J-05's "Case Study drill-in" acceptance clause.
- Non-blocking note: the surviving 15 MCP tools' order differs cosmetically from goal.md's prose enumeration (membership identical; no consumer depends on ordinal position) — logged, no action needed.

## Next step

Iteration 4 targets **J-04 (the §0.4 Path B fingerprint epoch bump)** — next in the J-01→J-05 order and the last blocker before J-05's full sentinel close. Recommend **full** depth: unlike J-03's zero-trigger mechanical trim, J-04 is the single most delicate operation of the era — it deletes ~18 `Config` fields under a grep-closure rule, prunes the fingerprint EXCLUSION set, updates the fingerprint literal at all **13 verified pin sites** (I-9; the ONE sanctioned pin edit of the whole interlude, maximum blast radius), re-seeds the founding PnL baseline (an append-beside-never-rewrite operation gated by the critical "never touch a historical record" anti-goal), and must prove byte-identical VALUES — only the stamp moves — across the recomputed content-hash caches (a value diff is veto-class). That dense stack of critical anti-goal adjacencies plus the wide multi-file blast radius is exactly what the full pipeline's audit / coherence / closure lanes exist to trace. Carry forward for whoever plans J-05: `SHOW_CASE_STUDIES = false` (`apps/frontend/app/structure/page.tsx:335`) still unresolved — restore vs. operator-rescope J-05's "Case Study drill-in" clause before J-05 can close.

## Assumptions made

- iter-4 · goal-decomposer — Ambiguity: goal.md's J-04 Step 3 says re-running `pnl_baseline` under the new epoch appends a new founding row beside the untouched old rows, but names no Config value to change to make that happen — followed literally, an unchanged enhancement id would make the write refuse as a duplicate no-op. We chose: bump `Config.pnl_founding_enhancement_id`/`pnl_founding_enhancement_title`'s literal default values (existing fields, not new ones) to a new distinct string, landed in the same commit as the field deletions; the ledger's primary-key/duplicate-id discipline stays untouched. Reversible: yes.
- iter-4 · goal-decomposer — Ambiguity: goal.md's I-4 "Confirmed DELETE list" names 18 Config fields as safe to delete, but a planning-pass grep found it both over-inclusive (4 fields are still read live by kept strategy/backtest code) and under-inclusive (9 other fields qualify for deletion under I-4's own closure rule but aren't named). We chose: corrected the delete list to 23 fields — the confirmed 18 minus the 4 wrongly-listed ones, plus the 9 verified closure-rule finds — and explicitly excluded the 4 study_* fields and `analytics_min_sample_size` from deletion. Reversible: yes.
- iter-3 · goal-decomposer — Ambiguity: goal.md's I-6 prose lists the resulting 15 MCP tools in a specific order, but surgically deleting the 3 dead rows in place (no reordering) leaves the code's natural order sequenced differently among 3 tool names, though the membership is identical. We chose: read "this exact list" as specifying tool membership, not order, and kept the code's natural residual order rather than reordering for zero functional benefit. Reversible: yes.
- iter-2 · goal-evaluator — Ambiguity: J-01's Required-still-passing re-capture showed three diffs against the iteration-1 baseline, not just the one sanctioned `meta.ui-routes` diff — two extra diffs read literally as a possible regression signal. We chose: scored J-01 `passing`, accepting the dev's root-cause that the 2 extra diffs are a launch-cwd data artifact (a different journal database file was read, not different code) — independently confirmed the entire read/serialize path is 0-diff. Reversible: yes.
- iter-2 · goal-decomposer — Ambiguity: goal.md's I-9 protocol calls taxonomy "the ONE sanctioned diff," which read literally could forbid any other route payload from ever differing across J-01/J-02/J-03 — contradicting J-02's own acceptance clause that the UI-routes list must shrink to the kept routes. We chose: read the I-9 protocol as a per-journey cumulative sanctioned-diff list, so J-02's re-capture is expected to show exactly one new sanctioned diff on top of J-01's already-accepted one. Reversible: yes.
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires "the full remaining backend suite is green," but the suite was 1165 passed / 1 failed / 7 skipped — the one failure being the MCP `journal` tool proxying to a now-correctly-404 route, a test the spec explicitly leaves for J-03. We chose: read "full suite green" as "green modulo the J-03-owned MCP-contract test" and scored J-01 `passing`, not `partial`. Reversible: yes.
- iter-0 · goal-evaluator — Ambiguity: J-05's literal acceptance ties full closure to the post-J-04 end state, and separately the spec's "Case Study drill-in" clause is unreachable in the shipped app (`SHOW_CASE_STUDIES = false`). We chose: scored J-05 `partial`, not `passing` — the full acceptance isn't yet evaluable pre-J-04 and a genuine acceptance clause is unmet; not `failing` because the checkable kept-product core verified intact via opened screenshots. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-clean_slate-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-clean_slate-iter-3-dev.md |
| Review | PASS | reports/reviews/goal-clean_slate-iter-3-review.md |
| Browser QA | PASS | reports/phase-goal-clean_slate-iter-3-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-clean_slate/iter-3/eval.md |
| Journey history | — | runs/goal-session-clean_slate/state/journey-history.json |
