# Phase goal-structure_ui-iter-4 — UX Regression Review

**Date:** 2026-07-07

**Verdict:** UX-REGRESSION-PASS

---

## Context

This iteration shipped **zero code change** (independently confirmed: `git diff --stat -- apps/backend`
and `git diff --stat -- apps/frontend` both return empty). Its entire purpose was evidentiary: iter-3
built J-03 (the Comparison section) correctly but browser-qa-agent and demo-narrator ran while the
frontend was unreachable, recording SKIPPED 0/26 — so J-03 sat at `unknown` and this report's own
predecessor (`reports/phase-goal-structure_ui-iter-3-ux-regression.md`) returned **UX-REGRESSION-WARN**
for exactly one reason: *"the single riskiest and most novel render in this iteration ... has no
independent screenshot anywhere in this iteration's artifact trail."* Everything else in that iter-3
report (discoverability, regression risk, backend parity) was already assessed sound.

This review's job is narrow: confirm that gap is now closed, and confirm nothing else regressed in the
process. It is not a re-litigation of J-03's design — that was already reviewed in iter-3.

## Verification performed independently (not just read from reports)

- Ran `git status --short` and `git diff --stat -- apps/backend` / `-- apps/frontend` myself: both
  diffs are byte-empty; only goal-mode bookkeeping/trace files changed. Confirms the zero-diff claim
  directly rather than trusting the handoff's assertion alone.
- Listed `reports/qa/goal-structure_ui-iter-4-evidence/`: 14 PNG files, 130KB–330KB each, timestamped
  10:59–11:21 — real, substantial screenshots (iter-3's equivalent directory held only 3 idle-state
  images).
- Opened three of them directly: `UT-04-finished-comparison.png` (populated Comparison — both
  backtests `done`, side-by-side aggregates, per-class insufficient-sample chips, verbatim register
  lines), `UT-17-one-click-reachable.png` (Structure tab active in the 5-link nav, full page reachable
  by one click + scroll), and `UT-11-backend-unreachable-run-error.png` (honest amber degraded state,
  "Nothing cached and nothing fabricated is shown in its place."). All three visually confirm the
  browser-qa-agent's byte-match claims — this is not just taking the QA report's word for it.
- Searched the repo for a formal design-system spec file (`find -iname "*design-system*"`): none
  exists. Visual-consistency assessment below is therefore made the same way iter-1/2/3's own
  ux-regression reviews made it — by direct cross-page comparison of chrome/typography/color tokens
  in the actual rendered screenshots — since there is no separate written token spec to check against.

## New Capability Discoverability

No new capability shipped this iteration (confirmed via zero diff). The already-shipped J-03 Comparison
capability remains exactly as discoverable as iter-3 established it:

| Capability | Navigation path | Clicks from home | Verdict |
|---|---|---|---|
| Comparison section (dataset selector, "Run comparison", results) | `/structure` (Structure tab, 1 of 5 persistent top-bar links) → scroll to 3rd section | 1 click + scroll | Discoverable (independently re-confirmed via `UT-17-one-click-reachable.png`: the nav's Structure link is active, no accordion/tab gating found) |
| Side-by-side aggregates, per-class A/B/C table, register line, champion cross-check, founding-baseline panel | Inline inside the Comparison panel, no modal/second click | same as above | Discoverable (visually confirmed in `UT-04-finished-comparison.png`) |

No label confusion found — "Run comparison," "Champion (moved never by this view)," "Founding baseline
(PnL ledger)" are unchanged from iter-3 and match established vocabulary.

## Regression Risk

| Shared surface | Prior feature it serves | This iteration's touch | Risk |
|---|---|---|---|
| `apps/frontend/components/StructureChart.tsx` | J-01 — levels/zones chart, iter-1's z-index occlusion fix | Zero diff; independently re-verified live by browser-qa-agent (UT-12): populated chart + 6 confluence zones render with **no empty-state overlay occluding the canvas** — the iter-1(a) fix has not regressed | Low |
| `apps/frontend/app/structure/page.tsx` (Registry + champion badge) | J-02 — strategy registry/champion cards | Zero diff; UT-13 re-confirmed exactly 1 DOM match each for `champion-strategy`/`champion-profile` vs. `comparison-champion-strategy`/`-profile` — iter-2's audit finding T2 (testid collision risk) has not regressed | Low |
| `apps/backend/app/meta.py`, nav component | J-04 — data-driven 5-link nav | Zero diff; UT-14 confirms 5 links, hrefs byte-match `GET /meta/ui-routes`; independently re-confirmed by my own screenshot review (nav shows Cockpit/Journal/Studies/Performance/Structure with Structure active) | Low |
| `apps/frontend/app/performance/**` | J-04 — `/performance` regression sentinel | Zero diff; UT-15 confirms direct load renders `champion-summary` = v1/default with zero `comparison-*` testids leaking onto the page | Low |
| Cockpit sim-ticker flow (`ThesisStrip`, `entry-checklist`) | J-04 — SIM-BUYER/SIM-SELLER settle correctly | Zero diff to Cockpit code; UT-16 went beyond the minimum bar and ran the full thesis → mark-entry → mark-exit → played-out lifecycle for both tickers, confirming `realized-r`/`recorded-marks` populate correctly | Low |
| `apps/backend/**` (all) | J-04 — frozen foundations / `config_fingerprint` | Zero diff (confirmed directly); `config_fingerprint` recomputes to `4d665603569b9dbf`, matching the pinned value | Low |

No component in this iteration's diff shows any change at all — there is no diff. Every regression-risk
row above is backed by an independent browser-qa re-verification with concrete evidence (DOM queries,
byte-matched API calls, or my own screenshot review), not merely restated from iter-3.

## UI vs Backend Parity

Unchanged from iter-3's assessment (no backend or frontend code changed, so no parity delta is possible
this iteration):

| Backend capability | Surfaced in `/structure`? | Assessment |
|---|---|---|
| Backtest aggregates, `aggregates_by_class`/`insufficient_sample`, `register`, champion pointer, PnL-ledger founding row | Yes, all — independently re-confirmed byte-match this iteration (UT-04–UT-09) | Complete |
| `result.null_baseline` (seeded random-entry baseline) | No — typed in `types.ts`, served by backend, never rendered | Carried forward, pre-disclosed in `user-visible-changes.md`; not named in this iteration's (or iter-3's) In-Scope/Data-contract bullets. Acceptable gap. |
| `POST /research/backtests/{id}/cancel` | No — no Comparison-section cancel control | Explicitly out of scope this iteration and iter-3. Acceptable, intentional. |
| `GET /research/backtests` (plural/list) | No — no way to browse a past comparison | Not required by this iteration's DoD. Acceptable; a future-card candidate. |
| Full dataset metadata (`/datasets` library page) | Partial — selector shows only `symbol · split · id-prefix` | Explicit non-goal (roadmap Card 5.9). Acceptable. |

**Conclusion:** identical to iter-3's parity conclusion, as expected from a zero-diff iteration — every
backend capability this iteration's (and iter-3's) spec calls for is surfaced; the four gaps above are
pre-disclosed, explicitly out-of-scope, and none contradicts the phase's own scope bullets.

## Flags

### Hidden Capabilities
None. The Comparison section lives on the already-navigable `/structure` page, reachable by scrolling
below Registry — no new route or control needed, confirmed by direct screenshot review.

### Undiscoverable Capabilities
None. 1 click from the persistent top nav + same-page scroll, confirmed both in the browser-qa report's
DOM-level check (UT-17) and my own review of `UT-17-one-click-reachable.png`.

### Potential Regressions
None found. Every shared surface (StructureChart, Registry/champion badge, 5-link nav, `/performance`,
Cockpit sim-ticker flow, backend config fingerprint) was independently re-verified live this iteration
via browser-qa-agent with concrete evidence (DOM assertions, byte-matched API payloads), on top of a
zero-diff codebase I confirmed directly with `git diff --stat`. This is a stronger regression-risk
posture than iter-3's, which relied partly on static source inspection rather than a live, populated
browser pass.

**Advisory, non-blocking, carried forward (not a regression caused by this iteration):**
`apps/frontend/components/PriceChart.tsx` (Cockpit) has a latent z-index empty-state occlusion issue
(carry-forward finding F2, first noted after iter-1's fix to the sibling `StructureChart.tsx`). This
iteration touches neither the Cockpit route nor `PriceChart.tsx` — confirmed via the zero frontend diff
— so it cannot be a regression introduced here. It remains correctly deferred to a future
Cockpit-touching iteration per the phase spec's own Out of Scope list.

### Visual Consistency
Matches the established style exactly, confirmed via direct screenshot review (`UT-04`, `UT-17`,
`UT-11`) rather than only reading the handoff's description: the dark instrument-panel chrome
(`bg-slate-900`-family panels, uppercase tracking-wide section titles), font-mono numerics, amber
tokens for both the insufficient-sample chips and the honesty register/degraded-state banners, and
rose tokens reserved for failed states are all identical to iter-1/2/3's established look — no new
visual language, no arbitrary one-off color or spacing value found. No repo-level design-system spec
file exists to check tokens against (confirmed via search); the cross-page comparison method used here
matches the method iter-1/2/3's own ux-regression reviews used for the same reason.

## Recommendation

**No action required.** This iteration closes the sole gap that drove iter-3's UX-REGRESSION-WARN
(missing independent, populated-state screenshot evidence for J-03) — that evidence now exists, is
substantial (14 real screenshots vs. iter-3's 3 idle-state-only images), and I independently opened and
visually confirmed three of the most load-bearing ones rather than relying solely on the browser-qa
report's prose. Discoverability, regression risk, and backend parity are all unchanged-and-sound from
iter-3's already-favorable assessment, now backed by a live, independent, populated-data browser pass
instead of static source inspection. The one open item (carry-forward F2, `PriceChart.tsx`) is
pre-existing, non-blocking, and correctly out of scope for this iteration — track it for whenever a
future iteration next touches the Cockpit.
