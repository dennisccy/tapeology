# Iteration Summary — goal-clean_slate-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-24
**Iteration:** 2

## In plain words

**What you can do now:** Watch a ticker's tape — simulated, live, or a recorded historical replay — and see it settle into a clear market read, with a price chart that shows candles, lets you switch time windows, shades support-and-resistance zones, and keeps updating live as new bars form. Open the Structure page, load a stock and a date, and see its strongest price "walls" highlighted. The product is now exactly the two pages it set out to be — Cockpit and Structure — since the old trade-journal, replay-studies, and performance pages were removed this iteration; visiting their old addresses now shows the site's normal "page not found" screen.

**What changed this time:** This iteration removed what was left of the manual trade-journal, replay-studies, and performance features: the three pages themselves are gone, the top menu shrank from five links to two, and the trading screen no longer shows the thesis-tracking strip, hint panel, or sound toggle. Nothing new was added — this was pure cleanup — and both charts, the Structure page, and the feed-source badge were all re-checked afterward and still work exactly as before.

**What's next:** Next, the team plans to retire three leftover entries from an AI-assistant tool list — for the journal, studies, and analytics features that already honestly say "not found" today — a tidy-up most users won't see directly.

## Headline

Top menu now shows exactly two links: Cockpit and Structure (previously five)

## Direction

**Signal:** improving
**Why:** J-02 (Frontend + WS demolition — the two-page product) moved from failing to passing this iteration: browser QA passed 18/18 tests (16 UI cases plus the J-01 and J-05 regression lanes), and review, audit, and coherence all landed on accepted verdicts with zero anti-goal violations. J-01 held passing under an independently re-verified byte-comparison re-capture against the iter-1 baseline, and J-05 stays partial pending J-04. Three iterations in, this session has advanced a journey forward every single time with zero regressions, so direction is healthy.

**Trend (last 3 iters):**
- Newly passing this iter: J-02
- Newly passing in last 3 iters total: J-01, J-02
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** "J-02 ('Frontend + WS demolition — the two-page product') lands: verified via 18/18 browser QA (screenshots personally opened) plus review PASS_WITH_NOTES, QA PASS, audit PASS_WITH_GAPS, and coherence COHERENCE-PASS. This is a disciplined pure subtraction (6,820 deletions / 99 insertions, zero new function/const/class definitions) — the veto-class chart rails held byte-identically, the fingerprint stayed frozen, and no historical record was touched. J-01 (Required-still-passing) re-verified green; J-03/J-04 remain out-of-scope `failing` and J-05 stays `partial`, so the goal is not yet achieved — progress made → CONTINUE."

## What was done

- Removed the WS `thesis`/`hint` frame merge from `app/main.py` and the four now-dead `ResearchRegistry` stub methods (`monitor_for`, `projection_for`, `_surviving_projection`, `hint_projection_for`) plus the `_monitors` dict from `app/research/routes.py`, in the same commit.
- Trimmed `app/meta.py`'s `UI_ROUTES` from 6 rows to exactly 2 (Cockpit, Structure); the nav bar shrank automatically since it already reads the route list at runtime — no frontend nav file was touched.
- Deleted the Journal, Studies, and Performance pages outright (3 pages, 11 components) — visiting them now renders the app's real 404, not a placeholder.
- Removed 14 `lib/api.ts` functions and roughly 30 `lib/types.ts` type families tied to the deleted surfaces; `fetchTaxonomy` (the provenance badge's dependency) was kept.
- Stripped the Cockpit's thesis/hint/sound integration from `app/page.tsx` and `Cockpit.tsx` (including the orphaned `onHintDeclare` prop), and removed only `PriceChart.tsx`'s thesis-geometry overlay build — `StructureChart.tsx` stayed byte-unmodified.
- Re-verified live in a browser that both charts, the sim cockpit flow, the `/structure` wall band, and the provenance badge all still work exactly as before; a captured WS frame (3,595 real frames) confirms no `thesis`/`hint` key remains.
- Verified 1 target journey (J-02) plus the J-01 and J-05 regression lanes pass browser QA — 18/18 tests PASS, 0 failed, 0 skipped.

## What's left

- Journey J-03 (MCP contract v2 — 15 read-only tools) failing — the three now-dead MCP tools (`journal`, `analytics`, `studies`) still proxy to 404 routes; closing them clears the one pre-authorized red test in the backend suite.
- Journey J-04 (The fingerprint epoch bump — §0.4 Path B) failing — Config field deletion and the 13 fingerprint-pin updates remain untouched by design, reserved for their own dedicated iteration.
- Journey J-05 (The kept product stands — regression sentinel) partial — full closure (Case Studies drill-in, full-suite-under-the-new-pin, cumulative diff-vs-inventory) still depends on J-04; this iteration only re-verified its browser-walkable subset (both charts, provenance badge, sim cockpit).
- Decision still pending, carried forward a second time: restore `SHOW_CASE_STUDIES` vs. operator rescopes J-05's "Case Study drill-in" acceptance clause.
- The AI-assistant (MCP) tool list still offers three now-dead tools (`journal`, `analytics`, `studies`) that honestly 404 but haven't been removed from the offered list yet — deferred to J-03.
- Non-blocking housekeeping noted by the audit: a stray untracked build-output directory left from an unrelated prior session, and a pre-existing PriceChart timeframe-button highlight quirk unrelated to this iteration's diff.

## Next step

Target J-03 (MCP contract v2 — 15 read-only tools) next — the natural next step in goal.md's J-01→J-02→J-03→J-04→J-05 dependency order, and the journey that closes the one pre-authorized red test (`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`, currently proxying the `journal` tool to a now-404 route). Scope per I-6: remove the `journal`/`analytics`/`studies` `_TOOL_PATHS` rows + `types.Tool` blocks (keep `taxonomy`), update `test_mcp_server.py` to the exact 15-tool contract keeping byte-identity + honest-error clauses for every kept tool, leave `get_endpoint`'s allowlist unchanged. Depth = lean — J-03 is backend-only, not browser-verifiable, and small (3 tool rows + one contract-test file); escalate to full only if it turns out to require re-rendering neutral-source framework assets that reference the deleted MCP tools. Carry forward for J-05's own iteration: `SHOW_CASE_STUDIES = false` must be resolved (restore the flag vs. operator rescopes the acceptance clause) before J-05 can close.

## Assumptions made

- iter-2 · goal-evaluator — Ambiguity: J-01's Required-still-passing re-capture (TC-14) showed THREE diffs against the iter-1 baseline, not just the one sanctioned `meta.ui-routes` diff — two extra diffs (`research.backtests.list`, `research.pnl_ledger`) read literally as a possible J-01 regression signal. We chose: scored J-01 `passing`, accepting the dev's root-cause that the 2 extra diffs are a launch-cwd DATA artifact (a different `tapeology_journal.db` file was read, not different code) — independently confirmed `backtests.py`/`pnl_ledger.py`/`store.py` are 0-diff vs the snapshot. Reversible: yes.
- iter-2 · goal-decomposer — Ambiguity: goal.md's I-9 protocol says taxonomy is "the ONE sanctioned diff," which read literally could forbid any OTHER route payload from ever differing across J-01/J-02/J-03 — contradicting J-02's own acceptance clause that `GET /meta/ui-routes` must shrink to the kept routes. We chose: read the I-9 protocol as a per-journey cumulative sanctioned-diff list, so J-02's re-capture is expected to show exactly one new sanctioned diff (`meta.ui-routes`, 6→2 rows) on top of J-01's already-accepted taxonomy diff. Reversible: yes.
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires "the full remaining backend suite is green," but the suite is 1165 passed / 1 failed / 7 skipped — the one failure is the MCP `journal` tool proxying to a now-correctly-404 route, a test the spec explicitly leaves for J-03. We chose: read "full suite green" as "green modulo the J-03-owned MCP-contract test" and scored J-01 `passing`, not `partial`. Reversible: yes.
- iter-0 · goal-evaluator — Ambiguity: J-05's literal acceptance ties full closure to the post-J-04 end state, and separately the spec's "Case Study drill-in" clause is unreachable in the shipped app (`SHOW_CASE_STUDIES = false`). We chose: `partial`, not `passing` — the full acceptance isn't yet evaluable pre-J-04 and a genuine acceptance clause is unmet; not `failing` because the checkable kept-product core verified intact. Reversible: yes.

## Quick verify

From `reports/phase-goal-clean_slate-iter-2-what-to-click.md`:

1. Open `http://localhost:3301/` in your browser.
2. Type each of these three addresses into the URL bar, one at a time: `http://localhost:3301/journal`, `http://localhost:3301/studies`, `http://localhost:3301/performance`.
3. Go back to `http://localhost:3301/`. Type `SIM-BUYER` into the ticker field (it shows the grey placeholder text "Ticker e.g. SIM-BUYER" when empty), then click the green "Watch" button.
4. In the price chart's header row, click the "30s" button (in the small button group on the left, under the label "Tape").
5. Wait until the "Tape State" panel's large heading reads "Buyer Control" (this can take a minute or two), then click the red "Stop" button in the top-right of the header.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-clean_slate-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-clean_slate-iter-2-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-clean_slate-iter-2-review.md |
| Browser QA | PASS | reports/phase-goal-clean_slate-iter-2-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-clean_slate-iter-2-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-clean_slate-iter-2-user-visible-changes.md |
| What to click | — | reports/phase-goal-clean_slate-iter-2-what-to-click.md |
| UI surface map | — | reports/phase-goal-clean_slate-iter-2-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-clean_slate-iter-2-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-clean_slate-iter-2-ux-regression.md |
| QA | PASS | reports/qa/goal-clean_slate-iter-2-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-clean_slate-iter-2-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-clean_slate-iter-2-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-clean_slate/iter-2/eval.md |
| Journey history | — | runs/goal-session-clean_slate/state/journey-history.json |
