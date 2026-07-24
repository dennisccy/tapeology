# Phase goal-clean_slate-iter-6 — UX Regression Review

**Date:** 2026-07-24

**Verdict:** UX-REGRESSION-PASS

---

## Context

This iteration (target journey J-05, "the kept product stands — regression sentinel") is the
interlude's closing hardening pass. Its own spec states "New user-facing capability: None,"
"New information displayed: None," "New user actions: None," "UI surface changes: None." I
independently verified this rather than taking the handoffs at face value:

- `git status --porcelain` / `git diff HEAD --stat` show exactly one tracked-source file changed
  anywhere in `apps/`: `apps/backend/app/research/routes.py` (67 deletions, 0 insertions). Zero
  `.tsx`/`.ts` files changed.
- `git diff HEAD -- apps/backend/app/research/routes.py` (read in full, not summarized) confirms
  the entire diff is a pure subtraction of 5 Pydantic `BaseModel` class definitions
  (`ThesisRequest`, `ResolveRequest`, `ActionRequest`, `StudyRequest`, `ReviewRequest`) and their
  docstrings — no route decorator, no other class, no import line, no live handler touched.
- `app/meta.py`'s `UI_ROUTES` (the nav's single source of truth) is unchanged: exactly
  `{"/", "Cockpit"}` and `{"/structure", "Structure"}`.
- `apps/frontend/app/structure/page.tsx`'s `SHOW_CASE_STUDIES` is still `true` (line 335) — the
  Case Studies capability iter-5 restored is not regressed back to hidden.

Because there is no new capability this iteration, Step 1 of my process (new-capability
discoverability) is trivially satisfied — there is nothing new to trace a navigation path to.
The substantive part of this review is Step 2 (regression risk) and Step 3 (parity), applied to a
backend-only diff that happens to live in a file (`routes.py`) that also serves several of
`/structure`'s live routes.

---

## New Capability Discoverability

N/A — zero new capabilities. `user-visible-changes.md` and `implementation-summary.md` agree
exactly ("None" in both), and my own diff read confirms no frontend file changed that could have
introduced an undocumented capability.

---

## Regression Risk

| Shared surface | Prior feature / owning era | Touched by this iteration's diff? | Verification | Risk |
|---|---|---|---|---|
| `apps/backend/app/research/routes.py` (rest of the file: `BacktestRequest`, `DatasetRecordRequest`, `BarRecordRequest`, `EdgeReportComputeRequest`, `get_study_market_adapter`, and every live route handler) | Backtests (era 3), dataset/bar recording (era 5 "The Library"), Edge Report compute (era 5C "Fast Wall"), taxonomy/feed-basis badge | Same file, but a disjoint region — confirmed via full diff read: only the 5 named classes' lines were removed; every kept class and handler is byte-adjacent and untouched | Browser QA UT-06 (Edge Report honest state + Compute button present), UT-J-01 (taxonomy 200 w/ slimmed payload), full `pytest` 1169 passed / 0 failed, guard/chart-guard isolation 354 passed / 0 failed with empty `git diff` on each file | **Low** — verified, not just claimed |
| `app/meta.py` `UI_ROUTES` (nav) | 2-item nav (era 5D `clean_slate` iter-1/2) | No — confirmed unchanged by direct read | Browser QA UT-07/UT-11/TC-11 (screenshot `TC-11-nav.png` visually reviewed by me: exactly "Cockpit" + "Structure", "Cockpit" active-highlighted) | **None** (untouched, independently re-confirmed) |
| `StructureChart.tsx` / `PriceChart.tsx` | Chart rendering (era 5B/5C, 2026-07-23 cockpit-chart-upgrade) | No — veto-class if touched; 0-line diff confirmed | Guard suites `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`, `test_cockpit_chart_upgrade.py` pass with empty `git diff` | **None** |
| Case Studies panel + drill-in (`page.tsx`) | Era 5B/5C build, un-hidden in iter-5 | No frontend file changed | Browser QA UT-04: Load renders "300.11" band, row click opens a real `case-drillin` panel with correct data and honest "No recorded tape for this event." fallback | **Low** |
| Cockpit ticker watch/stop flow (`app/page.tsx`, `useTapeStream.ts`, `lib/api.ts`) | Sim cockpit (era `tape_to_profit` onward) | No — confirmed the DELETE `/watch/{ticker}` handler lives in `app/main.py`, a different file from the one this iteration edited (`grep` confirms zero occurrence of that route in `routes.py`) | Browser QA UT-03: Watch → "Buyer Control", bar-size switch → caption text, Stop → eventual "No ticker watched" (see Observation below) | **Low**, with one flagged observation (not attributable to this iteration — see below) |

**Everything this iteration's own diff could plausibly have affected was independently re-verified,
not just re-asserted.** I did not rely solely on the dev handoff's self-description.

### Notable non-blocking observation: Stop-watching settle-time inconsistency (not caused by this iteration)

Browser QA's own UT-03 write-up documents that, on an isolated, controlled retest (fresh watch →
single "Stop watching" click → no other interaction), the cockpit correctly reached "No ticker
watched" but took roughly **13–25 seconds** to do so, with stale "Watching SIM-BUYER" data and a
WS status of "Closed" visible for most of that window. I looked into this independently rather
than accepting the QA note at face value:

- `stopTicker()` (`apps/frontend/lib/api.ts:321`) is a single, un-looped `DELETE /watch/{ticker}`
  fetch with no client-side retry/backoff.
- `useTapeStream.ts` performs a single synchronous `ws.close()` on teardown — no client-side
  polling or delay logic.
- The `DELETE /watch/{ticker}` handler itself lives in `apps/backend/app/main.py`, **not** in
  `apps/backend/app/research/routes.py` (confirmed via `grep` — zero occurrence in the edited
  file). This iteration's entire diff is 67 deleted lines in a completely different router.

This rules out this iteration's diff as the cause with direct evidence, not just plausibility.
However, the observation itself is worth carrying forward because it is a **behavioral
inconsistency across this same session's own regression sentinels**: iter-5's browser QA hit an
apparently similar stall during a busy back-to-back sequence, then ran an isolated retest and
concluded "the idle state appearing correctly on the very first click, with no artificial delay."
Iter-6's browser QA ran the same kind of isolated retest and measured a genuine 13–25s delay. Two
consecutive dedicated attempts to isolate the same interaction produced materially different
findings — that is exactly the kind of drift a regression sentinel exists to surface, even when
(as here) the current iteration's own code is demonstrably not the cause. This is not attributed
to any prior era's or this iteration's specific change; it reads as latent, likely intermittent
behavior in the simulated-scenario tick loop or the `/watch` teardown path (era 3/`tape_to_profit`
vintage code, well before this interlude), possibly related to the already-documented
"SIM-BUYER scenario timing varies run to run" characteristic iter-2's QA recorded as legitimate,
pre-existing simulated-scenario behavior. J-05's own acceptance text ("'Stop watching' returns the
page to 'No ticker watched'") carries no timing bound, so this does not fail J-05 or block this
iteration. Recommended follow-up: root-cause whether `DELETE /watch/{ticker}` in `app/main.py` or
the simulated-scenario tick loop can block the teardown for double-digit seconds, and consider
either a faster server-side stop path or optimistic client-side idle-on-click feedback so the UI
doesn't show stale "Watching" data after the connection has already gone "Closed."

### Carried-forward, still-open, correctly out-of-scope: Case Studies drill-in scroll-into-view

Iter-5's own ux-regression review (`reports/phase-goal-clean_slate-iter-5-ux-regression.md`,
verdict WARN) flagged that the Case Studies row-click drill-in renders ~65,000px below the page
top on the default unfiltered (~1,758-row) table, with no auto-scroll/toast/inline-expand
affordance — a real user could reasonably conclude a row click did nothing. That gap is **still
present** (no frontend file changed this iteration) and is **correctly untouched** — this
iteration's own scope explicitly forbids new UI behavior ("No new features," zero `.tsx` edits),
so fixing it here would itself have been an anti-goal violation. I am not re-flagging this as a
new WARN for iter-6 (iter-6 did not newly surface it — iter-5 already did, and already recommended
the fix for "a future iteration"), but noting it for continuity so it is not lost: it remains an
open, non-blocking, real UX friction point in a shared component, unaddressed across two
iterations now.

### Potential Regressions (confirmed)

None. Every shared component this iteration's diff touches or is adjacent to was independently
re-verified working, and the two observations above are explicitly ruled out as caused by this
iteration's own change (disjoint files, confirmed by direct grep/diff, not by inference alone).

---

## UI vs Backend Parity

| Backend capability | UI exposure | Parity |
|---|---|---|
| Deletion of 5 orphaned Pydantic request-body classes | None expected — these were never reachable by any route, page, or API call before or after (confirmed: each had exactly 1 grep occurrence, its own def line, both before this iteration per the iter-5 audit and now 0 after deletion) | **Matched** (nothing to expose; a UI affordance for an internal schema class would never have existed) |
| New structural guard test (`test_routes_no_orphaned_request_models.py`) | None — a `pytest`-only automated check with no runtime surface | **Matched** (test infrastructure is not a product capability) |
| README wording fix (3 stale sentences) | Verified already absent (`grep -c "pending an operator decision" README.md` = 0); not edited | **Matched** (no drift; a prior iteration's `readme-maintainer` pass already closed this) |

`implementation-summary.md` ("Features Implemented: None... Changed Behavior: None") and
`user-visible-changes.md` ("What Users Can Now Do: None... What Changed in the Visible UI: None")
agree exactly — no gap to flag. This iteration's own goal.md is explicit that this era ships "zero
new product capabilities, pages, endpoints, strategies, or Config fields," so the absence of any
new UI exposure is the correct, intended outcome, not a shortfall.

One pipeline-sequencing note, not a parity gap: `implementation-summary.md`'s "Incomplete Items"
section (written at dev-handoff time) lists "the full hands-on browser walkthrough... is still to
come" — this was true when the developer wrote it, and has since been completed and passed by
browser-qa-agent (12/12) and the deterministic replay (1/1). The document is simply a snapshot from
an earlier pipeline stage; not a real gap by the time of this review.

---

## Flags

### Hidden Capabilities
None. No new capability shipped this iteration.

### Undiscoverable Capabilities
None new. (See "carried-forward" note above for the still-open, pre-existing Case Studies
scroll-into-view gap from iter-5 — not new to this iteration, not caused by it, and correctly left
untouched given this iteration's explicit no-new-UI scope.)

### Potential Regressions
None confirmed as caused by this iteration. One cross-session behavioral inconsistency is flagged
above (Stop-watching settle-time, 13–25s observed this iteration vs. "no artificial delay" observed
in iter-5's isolated retest) with direct evidence that this iteration's own diff cannot be the
cause (disjoint files: `app/research/routes.py` vs. `app/main.py`). Recommend a dedicated
root-cause pass in a future iteration, not a block on this one.

### Visual Consistency
- No new UI shipped, so there is nothing new to check against the DESIGN SYSTEM. I visually
  reviewed the evidence screenshots directly (`TC-11-nav.png`, `UT-03-stop-investigate.png`,
  `UT-03-stop-result.png`) rather than trusting only the text reports: the dark theme, nav
  styling (active-item highlight on "Cockpit"), panel chrome, and typography all match the
  established look from prior eras with nothing arbitrary or inconsistent introduced.
- No arbitrary values, no ad hoc styling — expected, since zero `.tsx`/CSS files changed.

---

## Recommendation

No action required to accept this iteration on UX-regression grounds — the diff is provably
scoped to dead code with zero live references, the nav and every re-tested shared surface behave
identically to iter-5, and UI/backend parity is exact (both correctly report zero new capability).

Two non-blocking follow-ups worth carrying into a future iteration (neither blocks this one):
1. Root-cause the Stop-watching settle-time variability (13–25s observed this iteration on an
   isolated retest, vs. instant in iter-5's isolated retest) — most likely in the `/watch/{ticker}`
   DELETE handler (`app/main.py`) or the simulated-scenario tick loop, not in any code this
   interlude has touched.
2. Give the Case Studies drill-in a scroll-into-view (or equivalent) affordance, per iter-5's
   already-logged recommendation — still open, still correctly out of scope for a
   zero-frontend-diff iteration.
