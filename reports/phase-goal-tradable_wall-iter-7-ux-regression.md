# Phase goal-tradable_wall-iter-7 — UX Regression Review

**Date:** 2026-07-15

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

| Capability | Navigation path | Clicks from home | Assessment |
|---|---|---|---|
| Tradable-band overlay on the cockpit `PriceChart` | None needed — renders automatically inside the pre-existing "Price Chart — Tape-State Markers" panel on `/` (the Cockpit, which IS the home page) whenever a symbol is watched in Simulated/Historical mode | 0 (beyond the existing Watch flow, unchanged) | Excellent. Exceeds the 2-click bar — the feature surfaces itself passively at the exact moment/place a user is already looking, with no new nav entry, page, button, or menu required. |
| Descriptive confluence chip | Same panel, appears/disappears automatically below the chart canvas | 0 | Excellent. Verified live via browser QA screenshot (`UT-04-confluence-chip.png`): chip text is plain descriptive English, no imperative/prediction language (independently re-scanned by UT-13). |
| "No tradable map for {ticker}." honest empty state | Same panel, same location | 0 | Excellent. Confirmed via real DOM query + screenshot (`UT-02-result.png`) for a SIM ticker. |

No new page, route, or nav entry was added or was needed (nav is frozen for Era 5B, confirmed unchanged: `UT-11-nav.png` shows exactly the same 5 links as before). Band axis labels use a compact "R class A · score 153 · round" convention — this is an **established precedent from iter-6's `/structure` page**, not a new label introduced by this iteration, so it does not constitute new label confusion.

**No hidden or undiscoverable capability found.** This is a well-executed "surface it where trading happens" delivery: the phase spec's own stated goal (make the tradable map visible in the cockpit, not just on `/structure`) is met with the best possible discoverability score — zero additional navigation of any kind.

## Regression Risk

Blast radius independently confirmed via `git diff --stat` (uncommitted working tree): exactly three frontend files touched — `apps/frontend/app/page.tsx` (1 additive prop-thread line + comment), `apps/frontend/components/PriceChart.tsx` (+204/-4 lines), `apps/frontend/lib/types.ts` (+18/-2, additive interface widening). Backend diff is empty (`git diff --stat -- apps/backend/` = nothing; only one new untracked test file). Confirmed via `grep` that `PriceChart` is imported ONLY by `apps/frontend/app/page.tsx` (the Cockpit) — `/journal`, `/studies`, `/performance` import nothing this iteration touched, and `StructureChart.tsx`'s "PriceChart" hits are comments referencing it as a pattern precedent, not an import.

| Shared component | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `PriceChart.tsx` bar-size selector (10s/30s/60s) | Cockpit chart resolution control (pre-iter-7) | Unchanged JSX/logic | **Low — verified.** UT-09 browser-clicked all three sizes on SIM-BUYER and confirmed correct `className` toggling + chart redraw + marker persistence via real screenshots. |
| `PriceChart.tsx` five-state tape markers (`stateMarkersRef`) | Core cockpit tape-state visualization (frozen foundation) | Unchanged; band overlay uses a structurally separate mechanism (`series.createPriceLine`, tracked in `bandPriceLinesRef`) vs. markers (`series.setMarkers`) | **Low — verified.** Markers render correctly alongside the new band lines in UT-01/UT-03/UT-04 screenshots. |
| `PriceChart.tsx` dashed thesis price-lines + thesis markers (J-48) | User's own declared-trade-thesis overlay | Source-verified: kept in a **separate ref** (`priceLinesRef`) from the new band lines (`bandPriceLinesRef`); each effect only clears/redraws its own ref array (read directly, `PriceChart.tsx:130-136, 356-366, 438-445`) | **Low risk by code architecture, but UNVERIFIED on screen this iteration.** UT-09 explicitly discloses: *"no thesis was declared for the watched ticker during this session... the dashed-thesis-price-line sub-clause of this test's Expected Result could not be directly observed."* No prior-iteration QA re-ran this combination either (the band overlay is brand new this iteration). The actual simultaneous on-screen rendering of a user's dashed thesis line next to a new solid band line has never been screenshotted. |
| `page.tsx` live-mode gate (`mode === "sim" \|\| mode === "historical"`) | Keeps `PriceChart` (and everything in it) fully absent from Live mode — a named anti-goal ("Live mode stays untouched") | Untouched condition (source-verified at `page.tsx:251`); only the JSX inside the gate gained a new prop | **Low — verified.** UT-08: watched AAPL live, zero "Price Chart" DOM presence, zero chip/empty-hint testids found. |
| `lib/types.ts` `Strategy.entries` (widened) | `/structure`'s Registry section (iter-6), which reads `Strategy.entries.rule` for the `v1` strategy row | Purely additive/widening (`{rule: string}` → `{rule; + 5 new optional fields}`) | **Effectively zero risk.** This is a TypeScript compile-time-only construct; `tsc --noEmit` confirmed 0 errors both before and after. UT-10 re-verified `/structure`'s Tradable Map works, though did not specifically re-screenshot the Registry `v1` row — given the change cannot alter runtime behavior, this is not worth blocking on. |
| **Bar-size selector × new band-overlay fetch (cross-feature interaction, not previously possible)** | Bar-size selector (prior feature) newly interacts with the band-overlay fetch (this iteration's feature) | See Flags below | **Medium — flagged, not browser-verified on a bands-bearing symbol.** |

## UI vs Backend Parity

- **Full parity.** No backend endpoint, config, or computation was added this iteration (confirmed independently: `git diff --stat -- apps/backend/` is empty except one new test file). Every value the overlay/chip render (`GET /research/tradability`, `GET /research/strategies`, `GET /tape/{ticker}/history`) was already served before this iteration and already displayed somewhere (`/structure`, iter-6) — this iteration is pure UI wiring into a new surface, with nothing left server-side-only.
- **Flagship acceptance criterion independently confirmed.** `docs/goal.md`'s J-06 acceptance line ("during the credentialed AAPL 06-22 replay the band overlay is visible and the chip appears at the 300-test with descriptive copy") is met: UT-03 shows the band overlay at the correct 2026-06-18 basis on the real AAPL 2026-06-22 replay; UT-04 shows the chip firing live with the exact text `Inside R-band 300.17–302.27 (class A) · tape: Seller Control (breakthrough) · measured history: edge report`, captured with a real screenshot, not narration.
- **Stale artifact, not a UX defect:** `reports/phase-goal-tradable_wall-iter-7-user-visible-changes.md`'s "Not Visible Yet" section states the confluence chip firing "was not personally witnessed on screen during this iteration's own verification session" — this was accurate when the ui-impact-analyst wrote it (immediately after the dev handoff, which had the same caveat) but is now superseded: the browser-qa-agent's subsequent run (timestamped after) DID witness and screenshot the chip live (UT-04). This is a pipeline-sequencing artifact (ui-impact-analyst runs before browser-qa-agent), not a product gap — flagged here only so the stale caveat gets refreshed before this phase's artifacts are treated as final.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions

- **Transient wrong-session band/chip flash on bar-size change (new cross-feature interaction, MINOR per code review, not browser-confirmed on-screen).** The code reviewer (`reports/reviews/goal-tradable_wall-iter-7-review.md`) independently flagged: `PriceChart.tsx:203`'s `as_of` fallback (`new Date().toISOString()`) fires not only on first paint but also **transiently on every bar-size change**, because clicking the pre-existing 10s/30s/60s bar-size selector (a prior-phase feature, confirmed working in UT-09) synchronously nulls `history` — and therefore `history?.epoch_anchor` — for roughly a second before the next poll repopulates it. During that window, the tradability effect can re-fetch using **today's** wall-clock basis instead of the replayed/watched session's own basis, meaning a real (non-SIM) symbol's band overlay — and by extension the confluence chip, since both read `tradabilityState.data?.bands`) — could transiently show a wrong-session band for ~1s before self-correcting. This is the same failure class the developer's own mid-build `as_of` fix targeted, but the reviewer notes it is "not fully closed." Severity is MINOR (self-corrects in ~1s, requires a specific real-symbol + bar-size-click sequence, does not affect the flagship credentialed scenario which was verified clean) and the reviewer's overall verdict was `PASS_WITH_NOTES` with a concrete fix suggested (skip the fetch while `epoch_anchor` is null rather than falling back to wall-clock).
  - **Why this belongs in a UX regression report, not just the code review:** the on-screen manifestation of this bug is a specific interaction between a **prior-phase feature** (the bar-size selector) and **this iteration's new feature** (the band overlay/chip) that did not exist before this iteration — clicking bar-size buttons on a real symbol never used to have any side effect on displayed price levels. It was **not visually verified** because UT-09's bar-size re-click test ran against `SIM-BUYER`, a symbol that resolves `no_bar_series_for_symbol` regardless of `as_of` — so even if the transient flash occurred during that test, there were no bands on screen for it to be visible in. No test in this iteration's browser QA clicked a bar-size button while a real, bands-bearing symbol (e.g., AAPL) was being watched.
  - **Action:** a cheap, targeted follow-up browser check — watch AAPL in Historical replay (bands visible, per UT-03), click a bar-size button, and confirm whether a wrong-basis band/chip flashes — would close this gap. Not blocking this phase given the self-correcting behavior and already-logged fix.

- **Thesis dashed-line + band-overlay coexistence not visually verified.** `PriceChart.tsx` keeps the prior-phase thesis price-lines (`priceLinesRef`, J-48, dashed) architecturally separate from the new band price-lines (`bandPriceLinesRef`, solid) — confirmed by direct source reading (`PriceChart.tsx:130-136`, `356-366`, `438-445`): each effect only clears and redraws its own ref array, so neither family can clobber the other by construction. Risk is therefore low. However, no browser QA test this iteration declared a thesis on a symbol with an active band, so the actual on-screen simultaneous rendering of both line families (verifying they remain visually distinct and neither obscures/mispositions the other) has never been screenshotted. UT-09 explicitly discloses this gap rather than claiming it verified.
  - **Action:** a follow-up check — declare a thesis on a real symbol with a visible band, confirm both dashed (thesis) and solid (band) lines render correctly together — would close this gap. Not blocking; purely a verification-depth gap backed by sound code architecture.

### Visual Consistency

- **Consistent with the established DESIGN SYSTEM and iter-6 precedent — no flags.**
  - Confluence chip: `className="mt-3 rounded bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300"` (confirmed via a real captured `className` in UT-13) — standard Tailwind slate tokens, matching `FeedBasisBadge.tsx`'s neutral chip family as the plan specified, and correctly **avoiding** the amber palette this app reserves for degraded/empty/truncated states (a confluence chip is a positive descriptive signal, not a warning — the distinction is honored).
  - Solid band lines vs. dashed thesis lines: mirrors the exact solid-vs-dashed convention iter-6 established on `/structure` for bands vs. raw levels — no new visual language invented.
  - Rose (resistance) / emerald (support) band coloring matches the app-wide candle up/down and marker-state palette already in use everywhere else (cross-confirmed in the same UT-12 evidence pair, one screenshot from the cockpit, one from `/structure`).
  - No new glassmorphism, glow, or gradient effects were introduced; the existing `Panel`/`EmptyHint` components are reused verbatim (confirmed via source read — no new className constants invented for layout/chrome, only the new chip/empty-hint content blocks).
  - No arbitrary (non-token) values detected in the new JSX.

## Recommendation

1. **Not blocking**, but recommend a short follow-up browser check (could be folded into the next iteration or the closure audit) that watches a real bands-bearing symbol (e.g., AAPL, Historical replay, same window as UT-03) and clicks a bar-size button, to visually confirm whether the reviewer-flagged transient wrong-basis band/chip flash is observable on screen — and if so, apply the reviewer's suggested fix (skip the tradability fetch while `history?.epoch_anchor` is null instead of falling back to wall-clock time).
2. **Not blocking**, but recommend a short follow-up browser check that declares a thesis on a real bands-bearing symbol and confirms the dashed thesis lines and solid band lines coexist correctly on the same chart (closes the one sub-clause UT-09 disclosed as unobserved).
3. **Housekeeping, not a defect:** refresh `reports/phase-goal-tradable_wall-iter-7-user-visible-changes.md`'s "Not Visible Yet" section, which is now stale — the confluence chip firing it describes as unwitnessed was subsequently witnessed and screenshotted by the browser-qa-agent (UT-04).

No hidden or undiscoverable capability; no confirmed regression in a prior user journey; nav, bar-size selector, tape-state markers, live-mode gating, and `/structure` all independently re-verified working. The two flagged items are verification-depth gaps on cross-feature interaction surfaces, one of which is already caught, logged, and rated MINOR/non-blocking by code review — hence WARN rather than PASS or FAIL.
