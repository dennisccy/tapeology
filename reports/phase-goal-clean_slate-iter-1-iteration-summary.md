# Iteration Summary — goal-clean_slate-iter-1

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-24
**Iteration:** 1

## In plain words

**What you can do now:** Watch a simulated or live trading tape settle into a clear market read, with a price chart that shows candles, lets you switch time windows, highlights support-and-resistance zones, and updates live as new price bars form. Open the Structure page to load a stock and a date and see its strongest price "walls" highlighted, plus an honest note on whether the deeper edge analysis has been run yet. The trade journal, replay studies, and performance pages are also still there and fully working today — though they are the parts about to be retired.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team quietly removed the internal engine that powered the old journal, replay-studies, and performance pages — the web addresses those pages used to call now honestly say "not found" instead of doing anything wrong. The pages themselves haven't been touched yet, so if you open the app right now everything still looks and works exactly as before.

**What's next:** Next, the team removes the old trade-journal pages, the navigation entries, and the leftover on-screen widgets from the app itself — that's the point where you'll actually see the product change.

## Headline

Backend demolition (J-01): 14 journal/studies routes deleted, kept routes byte-identical

## Direction

**Signal:** improving
**Why:** J-01 (Backend demolition with byte-identical relocations) completed a full pass this iteration: 14 routes deleted and 404-verified, 11 modules plus ~25 tests removed, 3 code families relocated byte-identically, and 27/28 kept routes plus the frozen config fingerprint proven byte-identical via sha256 diff. Review (PASS), QA (11/11 test cases PASS), audit (PASS_WITH_GAPS, zero blocking findings), and the closure-auditor (CLOSURE-PASS) all independently concur, with zero regressions and zero anti-goal violations found. The evaluator has not yet formally re-scored `journey-history.json` for this iteration (it still reflects iter-0's snapshot), so J-01 isn't machine-marked `passing` yet — but every gate this iteration passed cleanly, so the honest signal is improving, not merely holding.

**Trend (last 1 iter):**
- Newly passing this iter: none confirmed in journey-history yet — the evaluator has not formally re-scored iter-1 (J-01's backend work is closure-verified PASS, pending that formal sign-off)
- Newly passing in last 1 iter total: none
- Regressions in last 1 iter: none
- Anti-goal violations in last 1 iter: none
- Iters with no journey state change: 1 of last 1 (journey-history.json still reflects the iter-0 verification snapshot)

**Latest evaluator reasoning:** (carried from iter-0's evaluation — iter-1's own evaluator pass has not run yet) Verify-only baseline. Opened the J-05 cockpit + structure screenshots and confirmed they match the browser-QA report (Buyer Control settled, 30s candles + timeframe switch, AAPL 300.11–302.2 Class A wall band on StructureChart); the same screenshots show the 5-item nav + thesis/hint/sound UI, corroborating J-02 `failing`. J-01/J-03/J-04 are keyless/automated backend journeys with curl/grep/python evidence — no screenshot by design — all showing the pre-demolition state. Not GOAL_ACHIEVED (J-01–J-04 failing, J-05 partial); not REGRESSION (no prior pass to lose; no anti-goal violation); not STALLED (J-01 is tractable dev work); not ESCALATE (review lane PASSED).

## What was done

- Deleted the 14 journal-era backend routes (`/research/analytics`, `/research/thesis/*`, `/research/hints*`, `/research/journal*`, `/research/studies*`) — each now returns an honest HTTP 404, curl-verified individually.
- Slimmed `GET /research/taxonomy` from ~14 KB to ~300 bytes, keeping only the `feed_basis` labels (Simulated/IEX/SIP/Yahoo) the app still uses.
- Deleted 11 backend modules (`journal_rows`, `monitor`, `hints`, `stance`, `verdict`, `grades`, `marks`, `excursions`, `execution_checks`, `analytics`, `studies`) and 25 journal-era test files; a repo-wide grep confirmed zero live imports remain.
- Relocated three genuinely shared code families byte-identically before deleting their old homes — the R-multiple helper (`r_basis`), the reference/historical dataset-source loader, and the state-native arming vocabulary (a gap the plan's own inventory had missed) — plus a second undocumented consumer of `get_study_market_adapter` the dev caught and relocated rather than deleted.
- Deleted `JournalStore`'s journal-era methods and dataclasses while proving every KEEP method (`insert_backtest`, `append_pnl_ledger_row`, `get_champion_pointer`, `list_pnl_ledger`) stayed byte-untouched.
- Proved zero regression via sha256 byte-comparison: 27 of 28 kept routes are byte-identical before/after (only the sanctioned taxonomy shrink differs), and `config_fingerprint()` plus all 13 pinned assertion sites are untouched.
- No browser QA needed this iteration (Frontend Present: no) — verified instead via the full pytest suite (1165 passed / 1 pre-authorized expected fail / 7 skipped), curl 404 checks, and repo-wide grep.

## What's left

- Journey J-02 (Frontend + WS demolition — the two-page product) failing — untouched this iteration (backend-only); pages, nav, and the cockpit's thesis/hint/sound UI are still live; targeted next.
- Journey J-03 (MCP contract v2 — 15 read-only tools) failing — MCP still registers 18 tools, including the now-orphaned journal/analytics/studies tools.
- Journey J-04 (The fingerprint epoch bump — §0.4 Path B) failing — `config_fingerprint()` and all 13 pins were intentionally left untouched this iteration; deferred to its own dedicated iteration.
- Journey J-05 (The kept product stands — regression sentinel) partial — the Case Studies drill-in is still blocked by the pre-existing `SHOW_CASE_STUDIES = false` flag; a restore-vs-rescope decision is still outstanding before J-05 can close.
- Journey J-01's `journey-history.json` record has not yet been updated by the evaluator for this iteration — this iteration's closure-verdict/QA/audit all independently confirm the backend demolition met its acceptance criteria; formal re-verification is the evaluator's next step.
- Four `ResearchRegistry` methods (`hint_projection_for`, `projection_for`, `monitor_for`, `_surviving_projection`) were kept as `None`-returning stubs rather than deleted, since their only live caller (the WS thesis/hint merge) is J-02's job — must be deleted in the same commit that removes that merge.
- One pre-authorized test stays red on purpose (`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`, the `journal` MCP proxy now 404ing) — closes under J-03, not before.

## Next step

Proceed to J-02 (frontend/WS demolition) — delete the `/journal`, `/studies`, `/performance` pages, the 5-item nav, and the cockpit's thesis/hint/sound UI. Carry forward two items this iteration's audit and dev handoff both flag: (1) delete the four now-stubbed `ResearchRegistry` methods (`hint_projection_for`, `projection_for`, `monitor_for`, `_surviving_projection`) in the same commit that removes the WS thesis/hint merge; (2) leave the one pre-authorized `test_mcp_server.py` failure alone — it closes under J-03, not J-02. Also still pending: resolve the `/structure` Case Studies suppression (restore the flag vs. operator rescopes J-05) before J-05 can close.

## Assumptions made

none recorded

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-clean_slate-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-clean_slate-iter-1-dev.md |
| Review | PASS | reports/reviews/goal-clean_slate-iter-1-review.md |
| Browser QA | SKIPPED | reports/phase-goal-clean_slate-iter-1-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-clean_slate-iter-1-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-clean_slate-iter-1-user-visible-changes.md |
| What to click | — | reports/phase-goal-clean_slate-iter-1-what-to-click.md |
| UI surface map | — | reports/phase-goal-clean_slate-iter-1-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-clean_slate-iter-1-ui-test-plan.md |
| QA | PASS | reports/qa/goal-clean_slate-iter-1-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-clean_slate-iter-1-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-clean_slate-iter-1-closure-verdict.md |
| Journey history | — | runs/goal-session-clean_slate/state/journey-history.json |
