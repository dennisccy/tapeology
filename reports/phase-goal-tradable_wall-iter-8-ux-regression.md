# Phase goal-tradable_wall-iter-8 — UX Regression Review

**Date:** 2026-07-15

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

No new capability was shipped this iteration — the plan, the phase spec ("New user actions: None"),
and both the ui-impact-analyst and ui-test-designer agree this is a cleanup (F1 transient-flash fix
+ T1 stale-docstring fix) plus a verification pass confirming two already-shipped `/structure`
sections now render real credentialed data instead of empty placeholders. There is nothing new to
assess for first-time discoverability. For completeness, the two surfaces whose *content* changed
retain exactly the navigation profile established when they were built:

| Surface | Navigation path | Clicks from home | Assessment |
|---|---|---|---|
| Cockpit band overlay + confluence chip (content unchanged, only fetch *timing* fixed) | Renders automatically inside the existing "Price Chart — Tape-State Markers" panel on `/` (home) while watching Sim/Historical | 0 | Unchanged from iter-7's own PASS discoverability finding. |
| Case Studies drill-in (now populated for the pinned case) | `/structure` (1 click from nav) → click a table row | 1 | Unchanged from iter-6. Nav bar independently re-confirmed present with exactly 5 items (Cockpit/Journal/Studies/Performance/Structure) via direct review of `reports/qa/goal-tradable_wall-iter-8-evidence/UT-07-result.png`. |
| Edge Report (intended to now be populated) | `/structure`, renders on mount, no click needed | 0 | Unchanged nav path from iter-6 — see UI vs Backend Parity below for why "populated" is not yet browser-confirmed. |

No label confusion: "Case Studies," "Edge Report," "Tradable Map," and "Tape timeline" all read
exactly as before and match what actually renders.

---

## Regression Risk

This iteration's entire code diff is two files: `apps/frontend/components/PriceChart.tsx` (the
cockpit fetch-effect fix) and `apps/backend/tests/test_price_chart_confluence.py` (test-only).
`apps/frontend/app/structure/page.tsx`, `StructureChart.tsx`, and `NavBar.tsx` are **not** in the
diff (independently confirmed: `git diff --stat -- apps/` lists exactly the two files above; a
direct `grep` for nav-defining files found only `NavBar.tsx`, which reads its links from
`GET /meta/ui-routes` with no hardcoded list, and it is untouched).

| Shared component | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `PriceChart.tsx` tradability-fetch effect | Cockpit band overlay + confluence chip (iter-7, itself flagged WARN for this exact transient bug) | Early-return guard added; wall-clock fallback removed; dependency array unchanged (`[ticker, history?.epoch_anchor]`) | **Low — verified.** Independently re-viewed `UT-02-result.png`: the historical AAPL 2026-06-22 replay shows correct `2026-06-18`-basis bands (`R class A · score 153 · round 300.17` etc.) with no artifact of a stale/wrong-day render, and the QA report's fetch-interceptor evidence shows exactly one `research/tradability` request, `as_of=2026-06-22T13:30:00.001Z`, no precursor. This closes iter-7's own flagged regression risk rather than opening a new one. |
| `PriceChart.tsx` tape-state markers, bar-size selector, thesis price-lines (frozen, pre-iter-7) | Core cockpit visualization | Untouched — only the tradability effect's guard changed | **Low.** UT-01/UT-03/UT-04 (SIM render, live-mode-hidden) all PASS with direct evidence. |
| `apps/frontend/app/structure/page.tsx` — **Tradable Map section (J-05, built iter-6)** | Default `/structure` view: ≤10 bands, pinned resistance band, raw-levels toggle off by default | **Zero code touch this iteration** — but see Flags below: the plan (`runs/goal-tradable_wall-iter-8/plan.md`) and phase spec both explicitly require this be re-verified as a regression check this iteration, and neither QA pipeline actually exercised it. | **Medium — verification gap, not a code-risk finding.** Code-diff evidence makes an actual regression very unlikely; the gap is that nobody clicked "Load" on the Tradable Map this session to confirm it. |
| `apps/backend/app/research/setups.py` / `edge_report.py` read paths (frozen this iteration) | Case Studies drill-in + Edge Report (iter-6) | Zero code change; only the operator's newly-persisted dataset volume changed what these paths return | **Low for Case Studies** (UT-07 directly confirms populated, correct rendering with independently-reviewed screenshot evidence — 426 real tape-timeline entries, `AAPL · 2026-06-22`, `rejected`, negative forward returns). **Not yet confirmed for Edge Report** — see UI vs Backend Parity below. |
| `NavBar.tsx` (J-07 regression sentinel) | Nav bar unchanged (Cockpit/Journal/Studies/Performance/Structure) | Zero code touch; data-driven from `/meta/ui-routes`, no hardcoded list | **Low — self-resolved by direct evidence.** No dedicated automated regression test in either QA pipeline this iteration explicitly re-enumerated the nav bar (the `qa` agent's TC-12 was SKIPPED for Chrome-startup reasons; the browser-qa-agent's own test plan contains no nav-count test), but I independently reviewed `UT-07-result.png` and confirmed all 5 nav items render correctly with "Structure" correctly highlighted as active. |

---

## UI vs Backend Parity

| Backend capability | Owning module (unchanged this iter) | UI exposure this iteration |
|---|---|---|
| Real credentialed dataset store (18 datasets, 11 real, 10 symbols, `sip`-stamped) | `DatasetStore` | Not directly listed anywhere in the UI (no `/datasets` page — explicitly out of scope, consistent with iter-6's same disclosed gap) — only indirectly visible through Case Studies/Edge Report content it feeds. Both `user-visible-changes.md` and the dev's `implementation-summary.md` agree and disclose this consistently; no contradiction. |
| Pinned AAPL 2026-06-22 `tape_timeline` (`GET /research/setups/{id}`) | `setups.py` | **Confirmed end-to-end in the UI.** UT-07's evidence — independently re-viewed — shows 426 dated, stated timeline entries rendered in the Case Studies drill-in, replacing the prior empty-state text. This is the iteration's headline (J-03) claim and it is genuinely, verifiably closed. |
| Edge-report cells (`GET /research/edge-report`) | `edge_report.py` | **Backend-side readiness is strongly evidenced but UI-rendering parity is NOT confirmed this session.** The dev independently cross-referenced all 11 real datasets against the 801-event registry using the endpoint's own matching rule and found all 11 resolve to a classified scan event (0 skipped) — strong indirect evidence the report will populate correctly. But the actual computation (~10+ hours, uncached, restarts on every page load/reload) was never observed to complete in a browser: `reports/phase-goal-tradable_wall-iter-8-ui-test-results.md`'s UT-13/UT-14/UT-15/UT-16 are all the test plan's own pre-authorized "loading correctly, not yet resolved this session" carve-out, not passes. This is the same category of gap iter-6's UX review flagged (then: no real data existed yet; now: real data exists and is independently confirmed correct, but nobody has watched the report actually finish rendering in a page). `user-visible-changes.md` discloses this caveat explicitly and accurately ("nobody has actually watched this section finish loading in a browser"); no artifact over-claims this as done. |
| `test_price_chart_confluence.py` docstring/test #5 correction (T1) | Test-only | No UI surface — correctly disclosed as backend-only in `ui-surface-map.md`. |

No backend capability is described as "complete" while silently missing from the UI. Every gap
(Edge Report render-parity, no `/datasets` page) is consistently and honestly disclosed across
`user-visible-changes.md`, `ui-surface-map.md`, `implementation-summary.md`, and the dev handoff —
no contradiction found between any pair of these artifacts.

---

## Flags

### Hidden Capabilities
- None found.

### Undiscoverable Capabilities
- None found. No new capability shipped; existing capabilities retain their iter-6/iter-7-established
  0–1-click discoverability from `/structure` or the cockpit.

### Potential Regressions

- **J-05 Tradable Map regression check was required by this iteration's own plan and spec but was not
  executed by either QA pipeline.** `runs/goal-tradable_wall-iter-8/plan.md`'s Key Test Scenarios
  section states verbatim: *"Browser — J-05: `/structure` still defaults to the Tradable Map (≤10
  bands, pinned resistance band present), raw-levels toggle off by default — unaffected by this
  iteration's changes; re-verify as a regression check."* The phase spec's TESTING REQUIREMENTS
  repeats this. Both QA pipelines that ran this iteration missed it:
  - The `qa` agent's own functional test plan (`reports/qa/goal-tradable_wall-iter-8-test-plan.md`)
    correctly wrote `TC-11 — /structure Tradable Map still defaults to ≤10 bands with pinned
    resistance (J-05 regression)` — but its QA report (`reports/qa/goal-tradable_wall-iter-8-qa.md`)
    records it as **SKIPPED: "Chrome startup unavailable in QA environment"**, alongside 6 other
    browser tests (TC-01, TC-02, TC-08, TC-09, TC-10, TC-12).
  - The separate `browser-qa-agent` (which did get a working Chrome via a shared-instance workaround
    and ran 16 tests, UT-01–UT-16) never wrote or ran an equivalent test at all — no UT test in
    `reports/phase-goal-tradable_wall-iter-8-ui-test-results.md` or its own test plan
    (`reports/phase-goal-tradable_wall-iter-8-ui-test-plan.md`) checks the Tradable Map's default
    populated state, band count, pinned resistance band, or the raw-levels toggle's default state.
  - I independently reviewed `reports/qa/goal-tradable_wall-iter-8-evidence/UT-07-result.png` (a
    full-page capture taken during this same QA session) and can confirm the Tradable Map section
    is present and renders without error, but it is showing its **idle, pre-Load** state ("Choose a
    symbol and an as-of time, then Load, to see its tradable level map.") — i.e., nobody in this
    session's QA actually clicked Load on the Tradable Map to exercise the ≤10-band/pinned-band/
    toggle-off acceptance criteria the plan named.
  - **Why this is Medium, not High/blocking:** the code diff touching `/structure` is empty this
    iteration (confirmed via `git diff --stat`), `StructureChart.tsx` and `page.tsx`'s Tradable Map
    logic are byte-identical to iter-6, and iter-6's own QA already verified this exact acceptance
    criterion in depth when it was built. The risk is a **verification-completeness gap**, not
    evidence of an actual break. Given this iteration is explicitly flagged as the
    **GOAL_ACHIEVED-candidate** iteration, this gap is worth closing (a single ~1-minute browser
    check: load `/structure` with AAPL, confirm the Tradable Map still shows ≤10 bands with the
    ~300 resistance band and the raw-levels toggle off) before treating J-05 as re-confirmed for the
    era-closing decision.

- **Edge Report end-to-end render parity remains unconfirmed in a browser, now for the second
  consecutive iteration, with the underlying performance characteristic freshly measured at "10+
  hours."** See UI vs Backend Parity above. Not a regression caused by this iteration's code (no
  backend production file changed), but a genuine, escalating reachability concern: the same
  real-data volume that finally makes J-03's Case Studies drill-in meaningful (426 real timeline
  entries) is also what makes the Edge Report's from-scratch, uncached replay-based computation
  impractically slow for any single QA/user session to observe complete. This was low-severity in
  iter-6 (the report was simply empty, nothing to wait for) and is now a more severe, quantified
  practical-reachability gap on the exact same UI surface. Non-blocking for this iteration (the
  test plan itself pre-authorizes this exact carve-out, and the dev's independent 11/11
  dataset-cross-reference check gives real, if indirect, confidence the eventual render will be
  correct), but it should not be allowed to become a permanent, un-owned gap given it directly
  undermines end-to-end confidence in one of this iteration's two headline UI claims.

### Visual Consistency
- No visual inconsistency found. This iteration introduces zero new visual elements (both the dev
  and frontend handoffs state this explicitly, and independently reviewing `UT-02-result.png` and
  `UT-07-result.png` confirms it): the same dark instrument-panel language, `Panel`/`EmptyHint`
  components, amber honest-empty/degraded treatment, and rose/emerald band coloring from iter-6/
  iter-7 are used unchanged. No arbitrary/off-token values observed in either reviewed screenshot.
- The one behavioral change (deferred fetch, no wall-clock fallback) is purely a *timing* fix with
  no rendered-output difference once the anchor resolves — confirmed by direct screenshot comparison
  against iter-7's own established band/chip appearance.

---

## Recommendation

Not blocking for this iteration's own Definition of Done — the F1/T1 cleanups are genuinely closed
with strong evidence, and the iteration's headline claim (J-03's populated Case Studies drill-in) is
confirmed end-to-end with independently-reviewed screenshot evidence. Two follow-ups worth acting on
given this iteration is the GOAL_ACHIEVED-candidate:

1. **Close the J-05 verification gap before treating it as re-confirmed for era closure:** run a
   single browser check — load `/structure` with AAPL (or any panel symbol with a resolvable basis),
   confirm the Tradable Map still renders as the default view with ≤10 bands, the pinned ~300
   resistance band present, and the raw-levels toggle off by default. This is cheap (the plan itself
   called it a "re-verify," not new testing) and closes a check that both QA pipelines independently
   missed this iteration for unrelated reasons (Chrome failure vs. test-plan omission).
2. **Treat Edge Report caching/performance as a real forward-looking priority**, not indefinitely
   deferred. It is the single largest remaining gap between "the backend genuinely has real,
   cross-referenced data" and "a user can ever actually see it rendered" — already flagged as
   out-of-scope twice (iter-3, iter-4) and now measured concretely at 10+ hours. A future iteration
   should apply the same `_SCAN_CACHE`-style hardening `setups.py` already received (iter-6) to
   `edge_report.py`.
3. Housekeeping only: no artifact contradicts another; no action needed on documentation accuracy.

No hidden or undiscoverable capability; no confirmed on-screen regression in any prior user journey;
the one flagged prior-iteration bug (F1's transient wrong-day flash) is genuinely closed with direct
evidence. The two items above are verification-completeness and reachability gaps, not confirmed
breaks — consistent with WARN rather than FAIL, matching this session's own established pattern
(iter-6 WARN, iter-7 WARN).
