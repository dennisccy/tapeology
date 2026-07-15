# Phase goal-tradable_wall-iter-6 — UX Regression Review

**Date:** 2026-07-15

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

All six new capabilities live on the already-registered `/structure` nav item (1 click from any
page in the app; nav bar independently confirmed unchanged at exactly 5 items — Cockpit / Journal /
Studies / Performance / Structure — via `reports/qa/goal-tradable_wall-iter-6-evidence/UT-15-nav-before.png`,
which I re-viewed directly). This is an unusually strong discoverability outcome because the two
headline capabilities are made the *default* render rather than something a user has to find:

| Capability | Navigation path | Clicks from home | Assessment |
|---|---|---|---|
| Tradable Map (≤10 bands, chart overlay) | `/structure` → Load form (pre-existing) | 1 (to `/structure`) + Load | Default view. Best-case discoverability — confirmed via direct screenshot review of `UT-01-top.png`: idle-state copy "Choose a symbol and an as-of time, then Load, to see its tradable level map." sits directly under the page's rewritten framing paragraph. |
| Band overlay lines on chart | Automatic once Tradable Map is populated | 0 (no action needed) | Confirmed via `UT-03-chart-zoom.png`: solid rose/emerald lines, visually distinct from the raw view's dashed lines, with inline `"R class A · score 153 · round"`-style labels. |
| "Show raw levels" toggle | `/structure` → button below Tradable Map | 1 click | Label flips Show↔Hide (confirmed `UT-04-raw-levels-shown.png` / `-hidden-again.png`); clear, accurate label. |
| Case Studies registry + filters | `/structure`, fetches on mount | 0 (visible on scroll, no click) | Confirmed via `UT-01-top.png` — table is already populated below the toggle on first page load, no Load-form submission required. |
| Case Studies row → drill-in | Click a table row | 1 click | Works (QA UT-06/UT-07); no explicit hover/pointer-cursor affordance was reported by QA to signal rows are clickable, but this is a minor nuance, not a discoverability failure — the row itself is a filled table row, a widely understood clickable-row convention. |
| Edge Report | `/structure`, fetches on mount | 0 (visible on scroll) | Confirmed populated on load with its own honest-empty state when unpopulated. |

Labels checked against function: "Tradable Map," "Case Studies," "Edge Report," and "Show raw
levels" all match both the spec's own vocabulary (`docs/goal.md`, `docs/phases/goal-tradable_wall-iter-6.md`)
and what they actually render. No label-confusion flags.

**No hidden or undiscoverable capabilities found.** Every new capability this iteration built is
reachable in 0–1 clicks from an already-existing nav entry, with no developer knowledge required.

One capability gap, not a discoverability gap: the backend's `band_class` filter on `GET
/research/setups` has no corresponding UI control (only symbol + reaction filters were wired). This
is honestly disclosed in `user-visible-changes.md`'s "Not Visible Yet" section and the dev handoff's
Known Issues #4, and it was explicitly out of the DoD's required scope — see UI vs Backend Parity
below rather than a discoverability flag.

---

## Regression Risk

`apps/frontend/app/structure/page.tsx` and `apps/frontend/components/StructureChart.tsx` are the
single shared surface for every `/structure` capability built across two prior sessions:
`goal-structure_ui` (J-01 Levels & Zones chart, J-02 Registry/Champion, J-03 Comparison) and
`goal-yahoo_fetch` (J-05 Fetch-from-Yahoo control + `FeedBasisBadge`). This iteration touches both
files extensively (page.tsx: +1173/−~193 lines per `git diff --stat`).

| Prior feature | Origin | Shared component touched | Risk level | Evidence this iteration didn't break it |
|---|---|---|---|---|
| Raw S/R levels chart + Confluence zones | `goal-structure_ui` iter-1 | `page.tsx`, `StructureChart.tsx` | Low (was Medium before verification) | Moved behind a toggle, not deleted; dev/frontend handoffs claim a whitespace-normalized byte-identical diff; QA `UT-04` PASS with before/after screenshots; I independently viewed `UT-04-raw-levels-shown.png` and confirmed dashed lines, "feed Yahoo Finance" badge, and Class-C zone cards all render as documented in the original `goal-structure_ui-iter-1/2` handoffs. |
| Registry (strategy cards + champion) | `goal-structure_ui` iter-2 | `page.tsx` | Low | Repositioned only; QA `UT-13` PASS — confirmed via DOM-text extraction (champion `v1`/`default`, 3 strategy cards, cross-check line) rather than screenshot (see page-length note below). |
| Comparison (`structure_tape`-vs-`v1`) | `goal-structure_ui` iter-3 | `page.tsx` | Low | Repositioned only; QA `UT-14` PASS — champion/founding-baseline boxes unchanged, a real comparison run reached the expected states, verified via DOM extraction + a direct backend job-status cross-check. |
| Fetch-from-Yahoo control + `FeedBasisBadge` | `goal-yahoo_fetch` iter-5 | `page.tsx`, `FeedBasisBadge.tsx` (not touched this iteration) | Low | Repositioned only, one intentional framing-copy sentence updated; QA `UT-12` PASS with screenshot (`UT-12-fetch-success-feedbadge.png`), confirmed the badge and store-first fetch flow both still work. |
| `apps/backend/app/research/setups.py` cache read path | `goal-tradable_wall` iters 1–5 (J-02 registry, J-04 edge report) | `setups.py` `_SCAN_CACHE` | Low | Existing B1/B3 tests (byte-identity, computed-once spy, checksum-bust, enriched-detail-never-leaks) stay green; 2 new tests added (structural + 16-thread concurrency); dev handoff documents proving the new structural test reliably fails against the reverted old implementation (a real regression guard, not just a passing coincidence). |

**Emergent, non-blocking regression risk not caused by broken code but by the repositioning decision
interacting with real data volume:** the Case Studies table renders all matching rows with **no
pagination or virtualization** — 801 rows on the operator's real store. QA's own report documents
the resulting page height as **~8,000–33,000px** depending on the raw-levels-toggle and filter state,
and states this caused a reproducible screenshot-compositing artifact in their tooling at deep scroll
depths — which is why `UT-13` (Registry) and `UT-14` (Comparison) have no screenshot evidence, only
DOM-text extraction.

Reframed from a UX (not tooling) angle: the three repositioned era-5 sections — Fetch-from-Yahoo,
Registry, and Comparison — are **functionally intact** (confirmed above) but are now reachable only
by scrolling past an unbounded 801-row table (plus Edge Report, plus, if the raw-levels toggle is on,
the full raw levels chart and confluence-zone list too). Before this iteration these three sections
sat near the top of the page. This is a genuine reachability regression for real (non-fixture) data,
even though nothing is broken and every value is confirmed correct once reached.

---

## UI vs Backend Parity

This iteration's entire purpose was closing a UI/backend parity gap that existed since iters 1–5
(J-01/J-02/J-04 were "passing" backend-only journeys, invisible in the UI). It closes that gap
essentially completely for its three target endpoints:

| Backend capability | Owning module | UI exposure this iteration |
|---|---|---|
| Tradable bands (`GET /research/tradability`) | `research/tradability.py` (iter-1, unchanged this iter) | Fully rendered: chart overlay + bands table + `basis_as_of`, default view |
| Touch-event registry + drill-in (`GET /research/setups`, `/{id}`) | `research/setups.py` (cache hardened this iter, logic unchanged) | Fully rendered: table + symbol/reaction filters + drill-in incl. boundary-honesty and tape-timeline states — **except** the endpoint's `band_class` filter param, which has no UI control (disclosed gap, not required by DoD) |
| Edge report cells (`GET /research/edge-report`) | `research/edge_report.py` (iter-4, unchanged this iter) | Fully rendered verbatim, including the correct honest all-empty state on the operator's current data |
| `setups.py` cache atomicity hardening | `research/setups.py` | Correctly has **no** UI surface — internal reliability fix only; both `user-visible-changes.md` and `implementation-summary.md` agree on this and neither over- or under-claims it |

Cross-checked `reports/phase-goal-tradable_wall-iter-6-implementation-summary.md` against
`reports/phase-goal-tradable_wall-iter-6-user-visible-changes.md`: no contradictions found. Both
documents independently and consistently disclose the same three residual gaps:

1. **`band_class` filter** — backend supports it, no UI control. Minor, explicitly out of the DoD's
   required scope (symbol + reaction only).
2. **J-06 cockpit confluence** (band overlay + descriptive chip on the cockpit `PriceChart`) — not
   built this iteration at all, explicitly deferred to iter-7 per the phase spec's OUT OF SCOPE
   section. This is a roadmap sequencing decision, not a hidden capability — there is nothing built
   and hidden; the capability genuinely does not exist yet.
3. **Edge Report populated-cell view** and **Case Studies tape-timeline populated view** — both are
   fully built and wired in the UI, but the operator's current real data has no watchlist-symbol
   credentialed tick recordings, so both correctly render their honest empty states. This is a *data*
   gap (operator-gated J-03 recording), not a UI gap — the rendering code paths exist and were
   confirmed against the exact JSON shape the backend would return once data exists (dev handoff's
   live smoke test).

No backend capability was found described as "complete" while silently absent from the UI. All gaps
are explicitly and consistently disclosed across both artifacts.

---

## Flags

### Hidden Capabilities
- None found.

### Undiscoverable Capabilities
- None found. Every new capability is 0–1 clicks from the existing `/structure` nav entry, and two of
  the three major new sections (Case Studies, Edge Report) render without any user action at all.

### Potential Regressions
- **Reachability of Registry / Comparison / Fetch-from-Yahoo sections** (prior features from
  `goal-structure_ui` iters 2–3 and `goal-yahoo_fetch` iter-5, all in `apps/frontend/app/structure/page.tsx`):
  functionally unbroken (QA `UT-12`/`UT-13`/`UT-14` all PASS), but now sit below an unbounded,
  unpaginated 801-row Case Studies table (plus Edge Report, plus the raw-levels view when toggled
  on), pushing total page height to an estimated 8,000–33,000px per QA's own measurement. This is a
  genuine, evidence-backed reachability degradation from where these sections sat before this
  iteration (near the top of the page) — not a "broken" regression, but a discoverability/usability
  one, and it is severe enough that it broke the QA agent's own screenshot tooling for two of the
  three regression checks (DOM-text extraction was used instead). Risk level: **Medium** — real,
  reproducible, but does not make any feature inaccessible, only slower/more effortful to reach.

### Visual Consistency
- No visual inconsistency found. Independently reviewed three screenshots
  (`UT-01-top.png`, `UT-03-chart-zoom.png`, `UT-04-raw-levels-shown.png`) alongside the dev/frontend
  handoffs' design-system claims: new sections reuse the existing `Panel`/`EmptyState`/
  `UnavailablePanel`/`LoadingPanel` components, the established `border-slate-800 bg-slate-900/60`
  surface treatment, uppercase tracked section titles, `font-mono` numerics, and amber
  (`border-amber-800/60 bg-amber-900/20`) honest-state styling consistent with every other page built
  across the `goal-structure_ui` and `goal-yahoo_fetch` sessions. No glassmorphism/glow was added
  (matches the plan's explicit "no new visual effects" requirement). One deliberate, well-reasoned new
  visual distinction: band-overlay lines are drawn solid vs. the raw view's dashed lines, so the two
  never look identical if a future iteration overlays both on one chart — this is additive
  differentiation, not drift.
- No arbitrary/off-token values observed in the reviewed screenshots or the handoffs' styling
  descriptions — all new tables/panels cite reuse of existing constants (`INPUT_CLASS`,
  `HEADER_CELL`/`LABEL_CELL`/`NUMERIC_CELL`, the existing button classes) rather than introducing new
  ones.

---

## Recommendation

No blocking action required — this iteration should proceed. One follow-up worth logging for a
future iteration (not this one, and not part of this iteration's DoD):

1. **Add pagination, virtualization, or a row cap to the Case Studies table** (currently renders all
   801 rows unfiltered with no limit). This would both restore quick reachability to the
   now-buried Fetch-from-Yahoo/Registry/Comparison sections and remove the screenshot-tooling
   fragility QA already hit at extreme scroll depths. A lower-effort alternative: an in-page "jump to
   Registry / Comparison" anchor link near the top, so those sections don't require scrolling through
   the full Case Studies + Edge Report content to reach.
2. Optional, low-priority: wire the backend's existing `band_class` filter into the Case Studies UI
   alongside symbol/reaction, since the endpoint already supports it and the other two filters are
   already built using the same pattern.

Neither item blocks this iteration's Definition of Done — both are forward-looking, non-blocking
observations consistent with a WARN (not FAIL) verdict.
