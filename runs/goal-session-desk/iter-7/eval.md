# Iteration 7 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

The two Claude-readable Desk tools are real and correct: I booted my own copy of the backend and
checked, tool by tool, that each one hands back exactly the same text the web address hands back —
both when nothing has been saved yet and when a saved universe and a saved screen exist. The tool
count is now 17, the page list is still three, and my own run of the whole test suite passed (1349
tests, 0 failures, 8 skipped). Six of the seven journeys now pass with fresh evidence I checked
myself. The seventh, J-07 "The kept product stands", finally has the four pictures it has been
missing since iteration 4 — the simulated cockpit, the Apple wall on the Structure page, the Case
Studies drill-in and the honest "not computed yet" Edge Report panel — and I opened every one of
them. But J-07 still cannot pass, and the reason is not code: three of its own written conditions
are blocked by one question that only the owner can answer. That question has now been asked three
times without an answer, and nothing the automation can do next will change it. So the run stops
here and hands the decision over.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | passing | passing | Row UT-J-01 in `reports/phase-goal-desk-iter-7-ui-test-results.md`; my own read of `apps/backend/.data/universe/universe-2026-07-25-49b33fa31680.json` (101 members inside the 90–110 bounds, sorted + unique, `BRK-B` with `raw_members["BRK-B"]=="BRK.B"`, own file checksum) |
| J-02 Coverage + top-up | passing | passing | Row UT-J-02 (index reads ~7–9 ms; PG shows tick evidence with no bars — two independent reads); my own query of `apps/backend/.data/bar_index.db` (281 rows, 60 symbols, e.g. ABBV 1d 501 bars) |
| J-03 The screen | passing | passing | Row UT-J-03; my own read of both saved screens `apps/backend/.data/screen/screen-2026-06-22-3ecd45c062c7.json` and `screen-2026-07-25-e184a7dc2f86.json` (five pins each, 10 rows / 91 skips, AAPL `0.33523150389608725` bps / score 97.0 / band 298.02–300.1001), matched against the band table in `reports/qa/goal-desk-iter-7-evidence/UT-09-structure-aapl-wall.png` |
| J-04 The /desk briefing page | passing | passing | `reports/qa/goal-desk-iter-7-evidence/J-04-verify.png` (saved-script replay, 2/2 PASS in `reports/phase-goal-desk-iter-7-regression-replay-results.md`); `UT-01-loaded.png`, `UT-12-nav-routes.png`, `UT-02-hover-side-cell.png`, `UT-06-rest-state.png` |
| J-05 Ledger history + drill-in | passing | passing | `reports/qa/goal-desk-iter-7-evidence/J-05-verify.png` (replay of the fixed script; Structure opens with AAPL and `2026-06-22T23:59:59Z` already filled and the wall drawn at 300.10/302.20); rows UT-04, UT-05, UT-07 |
| J-06 MCP contract v3 — 17 tools | failing | **passing** | My own live run: a real backend on a throw-away folder, `desk_universe` and `desk_screen` byte-identical to the same web addresses in the empty state and the filled state, `?date=` proxied exactly, a date with no match giving `{"screen": null}` and no error, `len(TOOL_NAMES) == 17`; plus my own suite run (1349 tests, 0 failures) |
| J-07 The kept product stands | partial | partial (four pictures newly taken; three conditions still blocked) | Met: my own suite run + live fingerprint `08e471b10130e1e2`; page list exactly three (`/meta/ui-routes` live + `UT-12-nav-routes.png`); 17 tools; `UT-08-cockpit-buyer-control.png`, `UT-09-structure-aapl-wall.png`, `UT-10-case-studies-drillin.png` + `TC-15-case-studies.png`, `UT-11-edge-report.png` + `TC-16-edge-report.png`. Unmet: see the three items below |

### Why J-07 is still partial (verified, not assumed)

1. **"Every guard test passes byte-unmodified" is false.** `apps/backend/tests/test_structure_chart_viewport.py:191-198` was relaxed from an exact-text check to a pattern check in iteration 4.
2. **"Zero out-of-inventory changes in the cumulative diff" is false.** `git diff --name-only 047c38e -- apps/` (my own run) still lists `apps/backend/app/research/bars.py`, `apps/frontend/components/StructureChart.tsx` and that guard test. `docs/goal.md`'s list of allowed changes names none of them, and `docs/goal.md` itself is byte-unchanged since the era opened (my own check).
3. **"Kept pages answer byte-identically against an era-open recording" was never checked.** No such recording was ever made (QA marked it SKIP; the audit searched and found none). My substitute check: the only changed code behind the kept pages is the bar store's read-time skipping of price-less rows, plus one error-code mapping on the bar-writing path; the kept read handlers themselves are untouched, and the tool module is imported by nothing in the web app.

## Anti-goal Check

Worked from `runs/goal-session-desk/iter-7/scan-report.md` (CLEAN) and `iter-7/iter-diff.md`
(5 files: `app/mcp/__init__.py`, `tests/test_mcp_server.py`, new `tests/test_desk_hover_tooltip_guard.py`,
`app/desk/page.tsx`, `README.md`, plus two saved test scripts).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN; no config or environment file in the diff; `test_no_credential_in_artifacts.py` green in my own suite run |
| Paid / external SaaS | OK | scan-report reports no dependency findings; no manifest file in the diff |
| License | OK | no LICENSE or license field in the diff |
| Fabricated or substituted data | OK | both new tools return the proxied text verbatim (my byte-identity run); the new hover text prints served fields only, uses "never" for a missing date, and omits distance/score entirely on a skipped row (`UT-03` + the new guard test). The one surprise — ABBV showing real bands on Structure while the saved screen says "no bars" — is honest: I confirmed the store really does hold 501 ABBV daily bars now, recorded after that screen was frozen |
| 1. No execution path, ever | OK | nothing added; `test_no_execution_path.py` green in my own run |
| 2. No profit claims and no advice | OK | copy lint green and unmodified; the new hover text is measurement only |
| 3. Frozen foundations | **CARRIED VIOLATION (minor, unresolved)** | This iteration opened none of the protected files. The iteration-4 changes to `bars.py`, `StructureChart.tsx` and the chart guard test are still unratified — this is the single blocker on J-07 and on the whole era |
| 4. Hold-out-only promotion | OK | no strategy, backtest, champion or ledger file in the diff |
| 5. No lookahead | OK | no computation added |
| 6. Single source of truth | OK | `iter-7/coherence.md` = COHERENCE-PASS with a per-value table; my own byte-identity run proves the tools recompute nothing |
| 7. Deterministic and seeded | OK | no randomness added. Noted: one new test only passes as part of the whole file (audit B1) — a test-order weakness, not a product one |
| 8. Read-only MCP | OK | I printed the proxy function's source: it can only issue GET; both new tools resolve through the static-path table |
| 9. Immutable data | OK | no data-writing code changed; no screen or universe file added (folder dates still 2026-07-25). Fourteen bar files appeared at 2026-07-26 22:41–22:45, after the pipeline's last recorded step (21:05:48) and outside every agent run — the owner's own use of the product, which the rules allow |
| 10. Persistence stays scoped | OK | same evidence as above |
| Membership is never a signal | OK | no computation changed |
| Snapshots append-only and pinned | OK | I read both saved screens: separate ids, separate checksums, five pins each |
| Every run is an explicit operator act | OK | no scheduler; the new tools are read-only page requests, and I confirmed a request before anything is saved returns the honest empty answer without starting any work |
| The briefing describes, never advises | OK | copy lint green; new text is a distance, a score and dates |
| No new statistics, gates or strategies | OK | none added |
| The demolition stays demolished | OK | no old journal machinery; the tool surface cannot write |
| The ledger never holds orders | OK | no order, size or account concept anywhere in the diff |
| The suite stays keyless and hermetic | OK | the new tests start a local backend and fill the stores directly; no network; skip count unchanged at 8 |
| The fingerprint pin does not move | OK | live print `08e471b10130e1e2`; no new settings field this iteration |
| The enhancement loop stays inside its box | OK | `docs/goal.md` is byte-unchanged since the era opened |

Pipeline health: review PASS, QA PASS, audit PASS_WITH_GAPS, closure CLOSURE-PASS, UX
UX-REGRESSION-PASS, coherence COHERENCE-PASS, replay 2/2. The merged results header reads
"15/17 journeys passed" — that is a counting bug in `merge_ui_test_results.py:109` meeting two
"PASS (see note)" cells; every one of the 17 rows is a pass.

## Next-Step Recommendation

The next run should be at **full** depth, and it must start with the owner's answer, because
without it J-07 cannot pass no matter what is built. Once the answer is in, the work is short and
already fully specified:

1. Record the answer in `docs/goal.md` (see the three options below) so the sentinel's own wording
   matches what the product actually contains.
2. Make the one era-open recording that was never made: check out the era-open commit `047c38e`
   into a second working copy, start it against a throw-away copy of the data folder, save the
   answers of the kept pages, then compare them with today's answers and write down every
   difference and its reason (the expected difference is the price-less-row skipping on the sixty
   affected series).
3. Restore step 10 of `runs/goal-session-desk/journey-scripts/J-07.json` to the chart-caption
   target it had before, and prove it by replaying J-07 once and keeping the results file — the
   reason given for changing it was shown to be wrong.
4. Photograph the cockpit once more in Historical mode on a real symbol, so the "candles,
   timeframe switch and level overlay" wording is covered by a picture and not only by the
   Structure page.
5. Two one-line clean-ups whenever those files are next opened: let the new date-lookup test save
   its own screen so it also passes when run alone, and delete the comment at
   `apps/frontend/app/desk/page.tsx:207`, which now says something untrue.
6. Keep carrying, do not force: the same-day screen ambiguity, keyboard access for the history
   rows, and the three older one-line hardening items.

One sentence for the owner: everything asked for this era is built and proven except one written
permission, so please answer the question below and then let the run continue.

## Halt Justification

I am halting with STALLED, not CONTINUE, because every way to finish the last journey runs through
the owner. This is the "human-owned blocker" case, not the "no progress" case — real progress
landed this iteration (the two Desk tools now work and are proven).

The blocker, in plain terms: in iteration 4 the automation changed three files that `docs/goal.md`
declares off-limits for this era — the bar store (`apps/backend/app/research/bars.py`), the
Structure chart (`apps/frontend/components/StructureChart.tsx`) and a chart guard test. It did so
to repair a real fault it had just caused: sixty saved price series each held one row with no
price, which crashed the Structure page and silently emptied the level map. The repair works and
nothing was deleted. But the only permission for it is a note the developer wrote into his own
iteration plan, and `docs/goal.md` was never changed. J-07's own wording ("every guard test
unmodified", "zero changes outside the listed inventory") is therefore false, and it will stay
false until a person decides.

Options to unblock — any one of them is enough:

1. **Ratify.** Add one line to `docs/goal.md` allowing the price-less-row repair in the bar store
   and the Structure chart, and the matching guard-test update. Then `--resume`; the next run does
   the five items above and the era can be declared finished.
2. **Revert.** Order the three files put back exactly as they were. Be aware of the measured cost:
   the price-less rows come back into what the app serves, Apple's level map as of 2026-07-25
   becomes empty, and the Structure page crashes when it meets one of those rows — so a revert
   needs a replacement plan for the sixty affected files (all of which are still untouched on
   disk, so every option remains open).
3. **Narrow the wording.** Change J-07 in `docs/goal.md` to require "no undisclosed changes outside
   the inventory" and to allow a guard test updated for a rename. Then the existing evidence closes
   the era on the next run.

Two smaller things also need the owner's eye but block nothing: no era-open recording of the kept
pages was ever made (so that condition has never been checkable as written), and the sentinel's own
replay script was edited late in this run for a reason the audit disproved.
