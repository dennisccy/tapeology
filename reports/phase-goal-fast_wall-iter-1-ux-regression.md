# Phase goal-fast_wall-iter-1 — UX Regression Review

**Date:** 2026-07-17

**Verdict:** UX-REGRESSION-PASS

---

## Summary

J-01 adds exactly one new UI state — a `NotComputedPanel` inside the existing `/structure` →
Edge Report section — and touches no navigation, no other page, and no other section. Direct
source inspection confirms the implementation matches every claim in the plan and handoffs:
`apps/frontend/app/structure/page.tsx:1873-1884` inserts the `status === "not_computed"` branch
strictly before the pre-existing `EdgeReportBody` fallback, and `NotComputedPanel`
(`page.tsx:287-297`) reuses `UnavailablePanel`'s exact Tailwind classes verbatim
(`page.tsx:254-266`). Browser QA (`reports/phase-goal-fast_wall-iter-1-ui-test-results.md`,
7/7 PASS) directly exercised both the new state and the four neighboring sections with live DOM
captures, not just a page-load smoke check.

## New Capability Discoverability

**Capability:** the "Edge report not computed yet." panel (cold cache + ≥1 registered dataset).

- **Navigation path:** Cockpit (`/`) → "Structure" nav link → `/structure` → Edge Report section.
  1 click from home, confirmed live in UT-05 (`window.location.href` verified as
  `http://localhost:3301/structure` after a single nav click). The Edge Report section was
  already part of `/structure` before this phase (era 5B) — this phase adds a new *state* inside
  an already-discoverable section, not a new destination that needs its own path.
- **Action required to reach it:** none beyond the pre-existing act of opening `/structure` — the
  panel appears automatically based on server state (goal.md explicitly scopes this iteration to
  zero new user actions: "no button, no trigger"). There is nothing to "find" — it is not a
  feature gated behind a menu, tab, or toggle a user would need to discover.
- **Label clarity:** headline "Edge report not computed yet." is plain language; the detail line
  is the server's own `detail` string rendered verbatim (confirmed byte-identical between backend
  JSON and rendered DOM in UT-02). No jargon, no internal class/function names in the copy (UT-05
  explicitly checked for this).
- **Visual feedback:** the panel itself IS the feedback — replaces what used to be an indefinite
  spinner or (pre-J-01) a silent multi-hour hang. UT-01 confirms the loading placeholder
  (`edge-report-loading`) still appears first, then resolves to the correct terminal state.

**Conclusion:** not a "hidden capability" or "undiscoverable capability" in the skill's sense —
there is no separate feature to surface via new navigation; the change is an additional honest
render branch inside an already 1-click-reachable section. No flag warranted.

## Regression Risk

Per the ui-regression-scout method: current phase touched `apps/frontend/app/structure/page.tsx`,
`apps/frontend/lib/api.ts`, `apps/frontend/lib/types.ts` only (confirmed via `git status` — no
other frontend file in the diff). `structure/page.tsx` is a large shared file also hosting
Tradable Map and Case Studies (era `tradable_wall`), the Fetch-from-Yahoo panel (era
`yahoo_fetch`), and the Registry/Comparison sections (era `tradable_wall`/`structure_ui`).

| Shared component | Prior feature / era | Current change | Risk | Evidence |
|---|---|---|---|---|
| `EdgeReportBody` + `edge-report-empty`/`edge-report-register` testids (`page.tsx:758-773`) | Era 5B (`tradable_wall`) edge report | Route rewired to `peek_strategy_comparison_report`; new branch inserted *before* this component, component itself untouched | Low (closest prior feature to this change, thoroughly tested) | UT-03: byte-exact DOM match on register banner text, empty-state title/detail, survives a full reload |
| Tradable Map (`tradable-map-idle`, `tradable-map-loading`, etc.) | Era 5B `tradable_wall` | None — different section, no shared state (`edgeReportResult`/`edgeReport` grep-confirmed scoped only to lines 1195-1884) | Low | UT-06: idle message byte-exact, unaffected |
| Case Studies (`case-studies-filter-symbol`/`-reaction`) | Era 5B `tradable_wall` | None | Low | UT-06: filters render immediately, unaffected |
| Fetch-from-Yahoo Finance panel | Era 5 `yahoo_fetch` | None — only repositioned historically, not touched this phase | Low | UT-06: section present in usual place, order unchanged (Tradable Map → Case Studies → Edge Report → Fetch-from-Yahoo → Registry → Comparison) |
| `NavBar.tsx` (Cockpit/Journal/Studies/Performance/Structure) | Era `structure_ui` (J-51) | Not touched (absent from `git status` diff) | None | UT-05 (5 links present, nav works) + UT-04 (nav's own honest-degrade behavior + 5-link recovery confirmed still intact, though that behavior predates this phase) |
| `fetchEdgeReport()` (`lib/api.ts:1144`) | Era 5B | Return type widened to `EdgeReportPayload` union; fetch call/endpoint/error handling byte-unchanged per dev handoff | Low | Single call site confirmed via grep (`page.tsx:1269`); no other consumer of this function found |
| Cockpit `/`, Journal, Journal detail, Studies, Performance pages | Various prior eras | Not touched | None | Not in this phase's file diff; J-07 sentinel (full backend suite + engine equivalence) passing |

No High or Medium risk items identified. The one component with genuine adjacency
(`EdgeReportBody`/its frozen testids) received the most direct, targeted regression evidence of
anything in this phase (UT-03's byte-exact comparison plus a reload check), which is the right
level of scrutiny for the highest-adjacency shared component.

## UI vs Backend Parity

| Backend capability | UI exposure this iteration | Status |
|---|---|---|
| `peek_strategy_comparison_report` three-way response (not-computed / warm / empty-registry) | Fully surfaced — `NotComputedPanel` for not-computed, `EdgeReportBody` for warm, same for empty-registry (unchanged) | Parity |
| `EdgeReportCache.lookup()` | Internal read path only, no separate UI signal needed (its effect IS the not-computed/warm distinction above) | Parity (by nature) |
| `EdgeReportCache.compute_and_publish()` | **Not wired to any UI trigger** — no button, no POST, no CLI surfaced in-app | **Intentional gap, disclosed** |
| `resolve_cache_db_path()` | Pure internal refactor, no observable behavior change | N/A (correctly backend-only) |
| `dataset_count` field on the not-computed payload | Fetched and typed, not rendered anywhere in the panel | **Intentional gap, disclosed** |

Both intentional gaps are the sanctioned case per my instructions ("if capabilities are
intentionally backend-only for this phase, that is acceptable"): `docs/goal.md`'s own dependency
order states J-04 ("the operator-run compute") is a **later** journey in this same interlude, and
the phase spec's OUT OF SCOPE section explicitly excludes "any 'Compute edge report'
button/POST/polling (J-04)." `reports/phase-goal-fast_wall-iter-1-implementation-summary.md` and
`reports/phase-goal-fast_wall-iter-1-user-visible-changes.md` both independently disclose the
exact same gap in the exact same terms ("no button or command yet... wired up and ready for the
next update") — implementation-summary and user-visible-changes are in full agreement, no
discrepancy between "what was built" and "what users can see." The phase goal itself is scoped to
"stop the bleeding" (removing the dangerous synchronous compute), not "add a compute trigger" — so
the absence of a trigger button does not contradict this iteration's own stated goal.

One soft observation carried forward for J-04 (not a defect in this iteration): the panel's own
server-supplied detail text says "an operator must trigger the compute," but there is currently no
in-app way to do so (`reports/qa/goal-fast_wall-iter-1-evidence/UT-02-not-computed-panel.png`
shows only two `<p>` tags, no button/input). This is fully expected for this iteration's scope,
but J-04's design should make sure the eventual trigger lands inside this exact panel so the
copy's implicit promise gets closed by the very next journey, not lost track of.

## Flags

### Hidden Capabilities

None.

### Undiscoverable Capabilities

None.

### Potential Regressions

None identified with Medium or High risk. See Regression Risk table above for the full Low-risk
inventory and its supporting evidence.

### Visual Consistency

- `NotComputedPanel` (`page.tsx:287-297`) reuses `UnavailablePanel`'s classes
  (`rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center`,
  `text-sm font-medium text-amber-300` headline, `text-xs text-amber-200/70` detail) **verbatim**
  — confirmed by direct source read, not just the handoff's claim. This is the same amber
  degraded/honest-absence pattern already used at 8+ other sites on this same page
  (`tradable-map-unavailable`, `structure-degraded`, `case-studies-unavailable`,
  `fetch-yahoo-error`, `comparison-founding-unavailable`, `comparison-datasets-unavailable`,
  `comparison-run-error`, `edge-report-unavailable` itself). Fully consistent with the
  DESIGN SYSTEM and with `docs/goal.md`'s explicit Design Direction ("no new visual language"),
  dark/dense/terminal-grade throughout, no glassmorphism or glow introduced.
- Advisory-only note (does not affect verdict): because `NotComputedPanel` and `UnavailablePanel`
  share identical styling, a "not computed yet" state (benign — nobody has run the sweep) and a
  genuine error state (backend unreachable, integrity failure) are visually indistinguishable at a
  glance; the only differentiator is the text content. This was a deliberate, reasoned tradeoff
  documented in `docs/handoffs/goal-fast_wall-iter-1-frontend.md` ("Visual Treatment") and is the
  correct call given the explicit "no new visual language" constraint — introducing a third color
  treatment would itself be a design-system deviation. Worth a glance when J-04 adds the compute
  button/trigger to this same panel, in case real operator usage shows the two states get
  confused.

## Recommendation

No action required. The panel is reachable exactly where and how the spec intends (1 click from
home, inside the pre-existing Edge Report section), the DESIGN SYSTEM reuse is verbatim rather
than approximate, and the four adjacent `/structure` sections plus the site nav were positively
re-confirmed unaffected with live DOM evidence rather than only a diff/code inference. The one
UI-vs-backend gap (`compute_and_publish` unwired) is intentional, disclosed identically across
implementation-summary and user-visible-changes, and matches this session's own declared
multi-iteration roadmap (J-01 → J-04) — carry the soft note above into J-04's design, not as a
blocker here.
