# Iteration 8 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean (moot — GOAL_ACHIEVED halts the loop for the deterministic gate + two-key confirm)

## Summary

J-03 moved partial -> passing: the iter-7 STALLED blocker (the credentialed >=10-window recording) was closed by operator action alone — 11 durable historical `sip` tick-window datasets across 10 panel symbols (incl. the pinned AAPL 2026-06-22) now sit in `apps/backend/.data/datasets/`, and the pinned drill-in renders its real 426-entry five-state tape timeline in the browser (UT-07). All seven Must-have journeys are now passing/already_passing, no anti-goal is violated, coherence is COHERENCE-PASS, and no goal text drifted (all 7 spec-hashes match). This is the first key toward GOAL_ACHIEVED; the outer loop's deterministic achievement gate + fresh-context two-key confirm re-verify.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | Backend byte-identical (tradability.py absent from diff; fingerprint 4d665603569b9dbf); pinned band 300.17-302.27 score 153 renders on cockpit overlay `reports/qa/goal-tradable_wall-iter-8-evidence/UT-02-result.png` |
| J-02 | passing | passing | setups.py absent from diff; registry populated (801 rows) in `reports/qa/goal-tradable_wall-iter-8-evidence/UT-06-result.png`; dev live-read 801 events |
| J-03 | partial | **passing** | Evaluator disk-enumeration of `apps/backend/.data/datasets/` (11 historical / 10 symbols / all sip / 7 train+4 holdout / checksummed / pinned AAPL 06-22 present); populated drill-in `reports/qa/goal-tradable_wall-iter-8-evidence/UT-07-result.png` (426-entry five-state timeline, rejected, both forward returns negative) |
| J-04 | passing | passing | edge_report.py/backtests.py/strategies.py/config.py absent from diff; champion still v1/default (UT-07 registry); honest loading state `reports/qa/goal-tradable_wall-iter-8-evidence/UT-12-result.png` |
| J-05 | passing | passing | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-06-result.png` — Tradable Map default + off-by-default raw-levels toggle + populated Case Studies registry; page.tsx/StructureChart.tsx absent from diff |
| J-06 | passing | passing | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-02-result.png` — band overlay on 06-22 replay at correct 06-18 basis (F1 confirmed, as_of=session anchor never wall-clock); UT-04 live-hidden; UT-05 descriptive-only |
| J-07 | already_passing | already_passing | `git diff` = exactly PriceChart.tsx + test file (no frozen file); fingerprint recomputed 4d665603569b9dbf; suite 1348 passed/7 skipped/0 failed; nav intact in UT-02/UT-04/UT-06 |

**Status change verified this iteration:** J-03 (partial -> passing). Screenshot opened: UT-07 (headline). Stable spot-checks opened: UT-02 (J-06), UT-06 (J-05). Backend-owned stable journeys (J-01/J-02/J-04/J-07) re-verified via frozen-file diff-absence + independent fingerprint recompute + full-suite green + the dev's live read-path confirmation.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | scan-report CLEAN; test_no_credential_in_artifacts.py 4/4; evaluator grep of all 18 dataset bodies + the 2 changed product files found no key patterns; datasets 0 tracked by git (gitignored) |
| Paid/external SaaS dependency | OK | No manifest change; scan-report CLEAN (no dependency findings). Alpaca is the pre-existing operator-env adapter (goal-sanctioned), used read-only for recording |
| License change | OK | scan-report CLEAN; no LICENSE/license-field diff |
| Fabricated/substituted data | OK | All 11 recordings are real credentialed `sip` ticks (feed stamped verbatim; no iex/yahoo pooling); pinned drill-in forward returns byte-match iter-2 (deterministic, not fabricated); empty states shown honestly (UT-10, UT-12) |
| No execution path, ever (critical) | OK | Diff is a fetch-timing fix + a test; no brokerage/order/trading code; UT-04 confirms live mode fully hides the chart; test_no_execution_path.py in the 1348-green suite |
| No profit claims / no advice (critical) | OK | UT-05 descriptive-only ("Descriptive only — not trading advice"); band labels "R class A · score N · round"; no imperative/prediction language |
| Frozen foundations byte-identical (critical) | OK | config_fingerprint independently recomputed to 4d665603569b9dbf; no frozen file in the 2-file diff |
| Hold-out-only promotion (critical) | OK | Champion still v1/default (UT-07 registry); backtests.py/config.py untouched; splits frozen at registration (7 train/4 holdout) |
| No lookahead (critical) | OK | F1 STRENGTHENS this — removes the wall-clock as_of fallback so bands only fetch with the anchor-derived morning-markup basis; UT-02 fetch-interceptor confirms as_of=session anchor, not today |
| Single source of truth (critical) | OK | coherence.md COHERENCE-PASS — F1 is a re-format/timing fix, not a duplicate computation; zero client recomputation traced |
| Feed honesty — never pool (critical) | OK | Every historical dataset data_feed='sip'; no iex/yahoo present to pool; cockpit shows "SIP (consolidated)" honestly |
| No gate bending for a headline (critical) | OK | edge_report.py untouched; n>=5-or-insufficient gate intact; empty/all-insufficient report is a goal-sanctioned valid outcome |
| Immutable data (critical) | OK | Datasets append-only, checksummed, split-frozen at registration; owning DatasetStore (datasets.py) absent from diff |
| Persistence stays scoped (critical) | OK | Recording is event-windowed (touch -60/+90 min, ~2.5h windows) around registered scan events; no ambient/scheduled/bulk recording |
| Keys never committed/logged (critical) | OK | See secrets row — grep + test + scan all clean; datasets gitignored |
| New strategy code additive/registered (critical) | OK | structure_tape_map registered since J-04; strategies.py/config.py untouched this iter; fingerprint frozen |
| Live mode untouched (critical) | OK | UT-04 — Price Chart panel fully absent in Live mode |
| No vocabulary drift | OK | No banned vocabulary in the frontend diff; "simulated — not indicative of live results" register served, not client-hardcoded |
| Read-only MCP (critical) | OK | No MCP change in diff |

No anti-goal violation (critical or minor). Coherence COHERENCE-PASS.

## Next-Step Recommendation

HALT — Era 5B "The Tradable Wall" is complete, subject to the deterministic achievement gate + two-key confirm. The wall is distilled to <=10 tradable bands (J-01), scanned into an 801-event case registry (J-02), recorded with real credentialed `sip` tape at 11 windows/10 symbols including the pinned AAPL 06-22 (J-03), measured by the honest 3-way edge report under the frozen era-3/4 gates (J-04), and surfaced on both `/structure` (J-05) and the cockpit (J-06) reading canonical endpoints verbatim, with the foundation unchanged (J-07). No further agent-buildable journey remains.

Non-blocking carries for a FUTURE (post-goal) enhancement iteration — none of which affect the verdict:
1. Add an `edge_report.py` result cache mirroring the `_SCAN_CACHE` precedent so `GET /research/edge-report` returns in seconds rather than the current ~10+h over the real ~9.1M-tick corpus (audit B2). This is the only real usability limitation and would let a browser-QA finally observe the populated Edge Report cells directly (the one DoD item not observed end-to-end this iteration).
2. QA test-plan T3 corrections before any re-run: real state vocabulary `{buyer_control, seller_control, bid_absorption, ask_absorption, unclear}` and the pinned event id `13e24a2f185b1299` (not the 32-hex dataset id, which would 404).
3. Pre-existing `scripts/dev.sh` SIGTERM child-process-tree cleanup leak (dev-flagged, out of this iteration's file scope).

## Halt Justification

GOAL_ACHIEVED per decision-tree item 3: every Must-have journey is passing/already_passing, there is no unresolved anti-goal violation, coherence.md is COHERENCE-PASS (not FAIL), and there is no journeys-changed.md drift (all 7 spec-hashes match the current goal text).

The single status change — J-03 partial -> passing — is backed by evidence I personally opened and reproduced, not by the PASS reports:
- **Datasets (disk-enumerated by the evaluator):** `apps/backend/.data/datasets/` holds 18 files; 11 are `source_kind=historical` recordings created 2026-07-15 across 10 distinct panel symbols (AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, SPY, TSLA), splits 7 train / 4 holdout, EVERY `data_feed='sip'` (no iex/yahoo lineage to pool), all checksummed, all with window_start/end, 0 tracked by git. The pinned `5c7f1a44` = AAPL 2026-06-22 window 12:30->15:00Z (touch -60/+90 min), 555,382 real trades+quotes, checksummed. This EXCEEDS the >=10-window / >=5-symbol / pinned-AAPL headline.
- **Populated pinned drill-in (browser screenshot opened):** UT-07 shows AAPL·2026-06-22, band 300.17-302.27 Class A, reaction `rejected`, forward returns 78b -0.00462 / 234b -0.04269 (both negative, byte-matching iter-2's deterministic values), and a 426-entry five-state tape timeline (bid_absorption/buyer_control/seller_control/ask_absorption) — the "No recorded tape for this event." empty state is gone (0 occurrences). The dev independently read the same 426-entry timeline via `GET /research/setups/13e24a2f185b1299`.
- **Engine/recorder byte-identical, no credential, keyless suite:** frozen `engine/`, `adapters/`, `datasets.py` absent from the 2-file diff; test_no_credential_in_artifacts.py 4/4 + evaluator grep clean; full backend suite 1348 passed / 7 skipped / 0 failed via the committed fixture.

Every J-03 acceptance clause is met with positive, independently-verified evidence, against the unchanged goal text (spec_hash `3b3dd4e4…`) — so the iter-7 halt was resolved by operator action, not by weakening the bar.

The audit's PASS_WITH_GAPS ("do not certify J-03 passing on this evidence alone") was written against the QA report, in which browser tests were SKIPPED because Chrome would not launch in the QA environment. The audit itself named the remedy — "a real browser-QA pass of J-03 (pinned drill-in renders the populated timeline)" — which the separately-dispatched browser-qa-agent then delivered (UT-07 PASS, via a documented Chrome-sharing recovery). That satisfies the audit's own condition #1; the evaluator opened the resulting screenshot to confirm it first-hand.

Honest scoped gap (does NOT block the verdict; logged in assumptions.md iter-8): the fully-rendered populated Edge Report cells (iter-8 DoD item 2) were not observed end-to-end — `GET /research/edge-report` is a documented ~10+h uncached computation over ~9.1M ticks, so UT-13/14/15 resolved to the test plan's sanctioned "still loading, backend genuinely computing at 98% CPU" carve-out. Populated cells are not a journey acceptance criterion; the goal explicitly names an empty/all-`insufficient_sample` report a valid outcome (Success Criterion 5, anti-goal "No gate bending for a headline"); the report is genuinely computing and will populate (the dev's cross-check confirmed all 11/11 real datasets resolve to classified scan events); and J-05 renders an honest loading state (UT-12). It is a runtime/usability limitation (a future caching enhancement), not an honesty or correctness defect, and therefore does not gate GOAL_ACHIEVED.
