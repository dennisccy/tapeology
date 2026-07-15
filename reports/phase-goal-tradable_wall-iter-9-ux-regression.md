# Phase goal-tradable_wall-iter-9 — UX Regression Review

**Date:** 2026-07-15

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

This iteration ships **zero new UI surface** by design. The plan, the phase spec ("UI surface
changes: none... no new button, form, page, or nav entry — nav frozen for Era 5B"), the
ui-impact-analyst, and the developer's own frontend handoff all agree: J-08 is a backend result
cache wrapped around an endpoint (`GET /research/edge-report`) that an existing panel already
reads verbatim. Confirmed independently via `git log`/`git status` — the last commit touching
`apps/frontend/` is iter-8 (`489c45c`); `apps/frontend/` is clean for this iteration. There is
nothing new to assess for first-time discoverability.

For completeness, the one surface whose *behavior* (load latency, not content) changes retains
exactly the navigation profile it has always had:

| Surface | Navigation path | Clicks from home | Assessment |
|---|---|---|---|
| Edge Report panel (`/structure`, renders on mount) | `/structure` (1 click from the 5-item nav: Cockpit/Journal/Studies/Performance/Structure) → scroll to "Edge Report" | 1 | Unchanged nav path, unchanged since iter-6. Same panel, same URL, same fields — only latency changes once an operator warms the cache (per `user-visible-changes.md`). |

No label confusion: "Edge Report," "Tradable Map," "Case Studies" all read exactly as before and
match what renders (UT-01/UT-07/UT-08 confirm exact caption/heading text).

The new **PnL-history append capability** (`python -m app.research.pnl_history --append-report
...`) is explicitly, deliberately CLI-only per spec ("Frontend: verify-only... do not touch any
other `/structure` or cockpit surface"; OUT OF SCOPE section: "any new nav entry"). This is not a
discoverability failure — it was never claimed to need a UI path this iteration, and every
artifact (`user-visible-changes.md`'s "Not Visible Yet," `implementation-summary.md`'s
"Backend-Only Items") discloses this consistently and honestly. See UI vs Backend Parity below
for the forward-looking note on this.

---

## Regression Risk

This iteration's entire production diff is backend-only: `edge_report.py` (rename + thin
dispatcher), new `edge_report_cache.py`, `routes.py`'s `get_edge_report` dependency, and additive
functions in `pnl_ledger.py`/`pnl_history.py`. Nav components (`NavBar.tsx`), `page.tsx`'s
Tradable Map/Case Studies/raw-levels-toggle logic, and `PriceChart.tsx` (cockpit) are untouched.

| Shared component | Prior feature it serves | This iteration's change | Risk | Evidence |
|---|---|---|---|---|
| `apps/frontend/app/structure/page.tsx` — Edge Report section (`EdgeReportBody` et al.) | Edge Report render (J-08's own home; existing since iter-6) | Zero frontend code touch. Serving path behind `GET /research/edge-report` gained a cache dependency; response shape byte-identical (confirmed via dev handoff's dedicated key-order regression test and the MCP byte-identity test). | **Low — verified.** UT-01 confirms the loading state renders identically (exact caption text, `edge-report-loading` testid, no `edge-report-unavailable`, no blank area). |
| `page.tsx` — Tradable Map section (**J-05**, built iter-6, re-verification gap flagged by iter-8's UX review) | Default `/structure` view: ≤10 bands, pinned resistance band, raw-levels toggle off by default | Zero code touch. This iteration's plan explicitly required re-verifying this as a regression check. | **Low — verified, and this CLOSES iter-8's flagged gap.** UT-08 confirms idle state → Load → exactly 10 rows, first row `resistance, 300.17–302.27, Class A, score 153` matching the iter-7-pinned case, "Show raw levels" unchanged after Load. UT-09 confirms the raw-levels toggle still reveals/hides the full levels+zones view correctly. |
| `page.tsx` — Case Studies section (**J-03**) | Filter/table/empty-state drill-in | Zero code touch. | **Low — verified.** UT-07 confirms 801-row table, correct no-match empty state on a bad filter, correct restore on clear. |
| `PriceChart.tsx` cockpit (**J-06**, tape-state markers, band overlay, confluence chip) | Cockpit SIM/Live/Historical rendering | Zero code touch (confirmed: `edge_report_cache.py`/`edge_report.py`/`routes.py`/`pnl_ledger.py`/`pnl_history.py` are the only production files in this iteration's diff — none is `PriceChart.tsx` or `tradability.py`). | **Low — verified for the hard requirements; one open, non-blocking observation.** UT-10 confirms SIM honest-empty-state and Live-mode full-component-hiding both unregressed, nav bar exactly 5 items. UT-11 confirms the chart/tape-state-markers hard requirement across 4 real-data windows. See Flags below for the band-overlay/confluence-chip sub-observation. |
| `NavBar.tsx` (**J-07**, nav regression sentinel) | Nav bar unchanged (Cockpit/Journal/Studies/Performance/Structure) | Zero code touch; data-driven from `GET /meta/ui-routes`. | **Low.** UT-10 directly re-confirms exactly 5 nav items, unchanged labels. |

No shared component this iteration's diff touches is used by a prior-phase UI feature — the
production diff is entirely backend serving-path plumbing behind one existing, unmodified panel.

---

## UI vs Backend Parity

| Backend capability | Owning module (this iteration) | UI exposure |
|---|---|---|
| `EdgeReportCache` (durable SQLite + in-process fast path) | `edge_report_cache.py` (new) | Fully invisible plumbing, as designed — its only observable effect is the Edge Report panel's load latency, which is unchanged in *code* and correctly documented as "not yet observed warm in a browser this session" (see below). Consistent across `user-visible-changes.md`, `ui-surface-map.md`, `implementation-summary.md` — no contradiction. |
| `append_strategy_comparison_row` / `append_strategy_comparison_and_render` (PnL-history append) | `pnl_ledger.py`, `pnl_history.py` | CLI-only, explicitly out of scope for UI this iteration (spec: "any new nav entry" is OUT OF SCOPE). Honestly disclosed as CLI-only in `user-visible-changes.md`. **Forward-looking note, not a this-iteration gap:** `user-visible-changes.md` itself flags that even after a future real append, the new `kind: "strategy_comparison"` ledger row type would still have **no rendering path anywhere on `/structure`** — the page's only PnL-ledger consumption today is a single `founding`-row lookup for the Champion-vs-Challenger view. This is accurately self-disclosed, not hidden, and is correctly out of this iteration's scope — but it means a future iteration that performs the real append must also add a render path, or the recorded finding stays permanently invisible in the app. |
| `GET /research/edge-report` warm-cache render, end-to-end in a browser | `edge_report.py` → `routes.py` | **Not observed this session — cache confirmed genuinely cold throughout QA** (0 rows in `edge_report_cache.db` at session start and ~1h later; backend pinned 90–100% CPU running the real uncached sweep). This is the **third consecutive iteration** (iter-6: report was empty/no data; iter-8: real data present but 10+h uncached, never observed complete; iter-9: the caching fix now exists and is thoroughly unit/integration-tested, but the warm render itself is still unobserved in a browser) where nobody has watched a populated Edge Report actually finish rendering on `/structure`. **This is explicitly, deliberately operator-gated** — the phase spec's own NOTES section logs it as an "Interpretation call," mirroring the established J-03/J-04 credentialed-carry precedent elsewhere in this project, and the ui-test-plan itself pre-authorizes the exact carve-out taken (UT-02/UT-03 SKIP). Every artifact discloses this consistently and prominently (`user-visible-changes.md`'s "Not Visible Yet," `what-to-click.md` step 2's "either outcome is correct," `implementation-summary.md`'s "Known Limitations") — nothing over-claims this as done. Not a UI defect: the frontend handoff independently confirmed the existing fetch/render code already correctly handles both the slow-cold and fast-warm cases with no client-side timeout, so no code change is waiting on this. |

No backend capability is described as "complete" while silently missing from the UI, and no
artifact contradicts another.

---

## Flags

### Hidden Capabilities
- None found. No new capability was added in kind this iteration.

### Undiscoverable Capabilities
- None found. The one behavior change (latency) rides the existing, already-discoverable Edge
  Report panel; no new click path was needed or omitted.

### Potential Regressions
- **None confirmed.** All four regression-check journeys this iteration's plan named (J-05
  Tradable Map, J-06 cockpit, J-03 Case Studies, J-07 nav) were directly, positively re-verified
  by browser-qa-agent with screenshot/DOM evidence (UT-07, UT-08, UT-09, UT-10, UT-11), not merely
  inferred from an unchanged diff. This closes the specific J-05 verification gap iter-8's UX
  review flagged as open (iter-8: "nobody in this session's QA actually clicked Load on the
  Tradable Map" → iter-9's UT-08 does exactly that, with pinned-value confirmation).
- **Two low-risk, non-blocking open observations from QA, both explained by conditions this
  iteration's diff did not create:**
  1. An intermittent amber `data-testid="nav-unavailable"` advisory appeared on `/structure`
     during the QA session. QA's own analysis ties this to the nav bar's `GET /meta/ui-routes`
     fetch degrading gracefully while the backend was saturated by the real, still-running
     ~10+h uncached compute (the exact condition this iteration's cache is designed to
     eliminate for *future* requests once warmed) — not caused by this iteration's code, never
     blocked an interaction, and not observed on `/` (cockpit).
  2. UT-11's band-overlay/`confluence-chip` sub-check was inconclusive: neither appeared in any
     of 4 sampled historical AAPL windows despite price sitting inside the pinned band's range in
     two of them. QA plausibly ties this to the confluence chip's own documented dependency on a
     populated edge-report ("measured history: edge report"), which was cold for the whole
     session — but this was not independently confirmed (e.g. by warming the cache and
     re-testing). Zero code was touched in `PriceChart.tsx` or `tradability.py` this iteration,
     so whatever the cause, it is pre-existing behavior, not a regression from this diff.

### Visual Consistency
- No visual change of any kind — zero `apps/frontend/` files were modified this iteration
  (confirmed via `git log`/`git status`). All rendered surfaces reviewed in QA evidence
  (`UT-01`, `UT-07/08/09`, `UT-10/11` screenshots, all present in
  `reports/qa/goal-tradable_wall-iter-9-evidence/`) show the same dark instrument-panel language,
  amber honest-empty/loading treatment, and band/chip coloring established in iter-6/iter-7. No
  arbitrary/off-token values to assess since no new markup was introduced.

---

## Recommendation

No blocking action required for this iteration's own closure — the two journeys this iteration's
own plan required as regression checks (J-05, J-06) are positively re-confirmed with direct
evidence, not merely a clean diff.

One forward-looking item worth tracking, carried over and sharpened from iter-8's own
recommendation:

1. **Warm the Edge Report cache for real, soon, and re-run the browser check.** This is now the
   third consecutive iteration without an actual browser-observed populated Edge Report render.
   The blocking mechanism (the ~10+h uncached compute) is exactly what this iteration built a
   tested, correct fix for — but the fix's own success has not yet been visually confirmed end to
   end because warming it requires the same operator-gated real compute the phase spec
   deliberately keeps out of agent scope. Once an operator lets `GET /research/edge-report`
   complete once for real, a follow-up should: (a) reload `/structure` and confirm the panel
   resolves within seconds (closing UT-02/UT-03/UT-06), (b) refresh and confirm it stays fast
   (durability), and (c) re-check UT-11's open band-overlay/confluence-chip observation now that
   the edge-report dependency it plausibly gates on is populated.
2. **When the real PnL-history append eventually happens, plan a render path for the new
   `strategy_comparison` row type** — `user-visible-changes.md` already flags that `/structure`'s
   PnL-ledger consumption today is a single `founding`-row lookup with no general table, so the
   newly-recorded row would otherwise land in the ledger with zero UI visibility. Not a gap in
   this iteration (correctly out of scope), but worth scoping into whichever future iteration
   performs the real append.

No hidden or undiscoverable capability; no confirmed regression in any prior user journey; the
one gap flagged by the prior iteration's UX review (J-05's unclosed verification) is now
genuinely closed with direct evidence.
