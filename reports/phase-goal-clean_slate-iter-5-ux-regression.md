# Phase goal-clean_slate-iter-5 — UX Regression Review

**Date:** 2026-07-24

**Verdict:** UX-REGRESSION-WARN

---

## Context

This iteration (J-05, "the kept product stands: regression sentinel") is the interlude's closing
journey. Its only literal product diff — independently confirmed via `git diff
apps/frontend/app/structure/page.tsx` — is exactly two hunks in one file: `SHOW_CASE_STUDIES`
flipped `false`→`true` (line 335) and one sentence reinstated into the `structure-framing`
paragraph. Everything else this iteration is re-verification (fresh full pytest, isolated
guard-suite reruns, an I-9 byte-comparison recapture, a session-wide diff-vs-inventory cross-check)
of already-shipped behavior — zero backend source changed, zero other frontend file changed.

Because the diff is this narrow, my review focuses on two questions: (1) is the one restored
capability — Case Studies — genuinely discoverable and fully functional now that it's visible for
the first time to a real user, not just reachable in the DOM; and (2) did re-exposing it put any
of the other features living in the same 2,400+-line `page.tsx` file at risk. I independently
re-derived the diff myself (`git diff`, not just trusting the handoffs) and cross-read the browser-
qa evidence's own Observations section rather than only its top-line PASS verdicts.

---

## New Capability Discoverability

| New capability | Navigation path | Clicks from home | Label clarity | Visual feedback |
|---|---|---|---|---|
| Case Studies panel becomes visible on `/structure` | Home (`/`) → "Structure" nav link → panel renders unconditionally at its pre-existing position (no toggle needed, unlike "Show raw levels") | **1 click** to the page; panel is on-screen without further gating | Clear — "Case Studies," "Symbol," "Reaction" all match goal.md's own terminology; UT-16 confirms the description text is plain-language | Confirmed rendering: heading, description, filters, populated table (UT-01, UT-03, UT-16) |
| Case Studies filters (Symbol / Reaction) | Inline on the now-visible panel, no extra navigation | 0 additional clicks | Clear | Table narrows in place, no reload (UT-05); honest "No events match these filters." on a non-matching combination (UT-06) |
| Case Studies row → drill-in | Click any row in the now-visible table | 0 additional clicks (same page) | Clear | **See flag below — this is where the review finds a real gap** |
| Framing-paragraph sentence | N/A (copy, not an action) | N/A | Matches goal.md's exact required text verbatim (confirmed via my own `grep` read of the source, not just the handoff's claim) | N/A |

The primary literal capability this iteration ships — the Case Studies **panel** becoming visible —
is excellently discoverable: one click from home, immediately on-screen, no developer knowledge
required, no hidden toggle. This is not the source of my WARN verdict.

The **drill-in interaction**, however, is a different story. `user-visible-changes.md` explicitly
lists "click any row... to open a 'Case Studies — drill-in' detail view" as a new user action this
iteration exposes for the first time. The browser-qa evidence itself (UT-04, and Observation #1 in
`reports/phase-goal-clean_slate-iter-5-ui-test-results.llm.md`) documents that the Case Studies
table is unpaginated at **1,758 rows**, making the section alone ~64,573px tall and the whole page
~68,000px tall when unfiltered (the default state on first load). The drill-in panel is inserted in
the DOM immediately after the currently-rendered rows — i.e., **~65,000px below the page top** when
a first-time user, having just discovered the newly-visible panel near the top of the page, clicks
a row without first filtering. There is no auto-scroll-to-drill-in, no toast, no inline
expand/collapse, and no near-click affordance of any kind. QA's own account is candid about this
("a real user scrolling manually after clicking row 1 would need to scroll roughly that far... there
is no auto-scroll-to-drill-in behavior") but did not let it affect the test's PASS verdict because
the panel is provably present and correct once you do scroll that far.

From a UX-regression standpoint this is exactly the "button exists somewhere is not the same as the
feature is discoverable" pattern this role exists to catch: a real user's first encounter with this
newly-un-hidden interaction (not a hypothetical — this is the literal first time any user outside
this pipeline could ever see it, since the panel was fully hidden until this iteration) will very
plausibly look and feel broken — no visible change happens anywhere near their cursor or current
scroll position. The data underneath is byte-correct; the feedback loop for the *interaction* is
not. This is why I could not call this a clean PASS.

---

## Regression Risk

| Shared component/file touched | Prior feature depending on it | Pre-verification risk | Verification found | Residual risk |
|---|---|---|---|---|
| `apps/frontend/app/structure/page.tsx` (`SHOW_CASE_STUDIES` line + framing paragraph) | Every other panel living in this same 2,400+-line file: Tradable Map/StructureChart (era 5B `tradable_wall` + the 2026-07-23 cockpit-chart-upgrade), Levels & Zones/raw-toggle (era 5B), Edge Report (era 5B/5C `fast_wall`), Fetch-bars/Registry (era 5 "The Library" / `yahoo_fetch`, `tradable_wall`) | **High** in principle — this is the single highest-centrality file on the Structure page | My own `git diff` confirms the actual edit is exactly 2 hunks (the boolean literal + one paragraph sentence), nowhere near any other section's code. Tradable Map + wall-band overlay independently re-verified (UT-02); Edge Report's honest current-state + Compute/Cancel flow independently re-verified (UT-08); nav/route-level behavior re-verified (UT-13, UT-14) | **Low** — diff is provably scoped; every plausibly-affected panel that was re-tested passed |
| `StructureChart.tsx` | Chart rendering shared by both `/structure` and `PriceChart` since `structure_ui`/`tradable_wall`/the chart-upgrade era | Veto-class (T-8) if touched at all | `git diff` on this file across the whole session shows **0 lines** (independently reconfirmed by the dev handoff's own T-8 claim, which I did not take at face value alone — the working tree shows no pending diff for this file) | **None** (untouched) |
| `PriceChart.tsx` | Cockpit's live chart (candles, timeframe switch, band overlay, live moving bars) | Its one sanctioned edit (thesis-overlay removal) already landed in iter-2; no further edits permitted this iteration | Confirmed zero further edits; Cockpit's chart behavior re-verified fresh this iteration (UT-09 candles render, UT-10 timeframe switch, UT-11 live bars moving) | **Low** |
| `app/page.tsx` (Cockpit) / nav (`app/meta.py`) | Sim-cockpit watch/stop flow (all eras back to `tape_to_profit`); 2-row nav (era 5D `clean_slate` iter-1/2) | Not touched this iteration at all | UT-09 (Watch → "Buyer Control"), UT-12 (Stop → idle, re-verified on a clean isolated retest after a same-session timing false-alarm — see below), UT-13 (nav exactly Cockpit+Structure) all pass | **Low** (unchanged file, independently re-tested anyway per the plan's "full regression sentinel" scope) |
| Deleted routes / MCP tool list / fingerprint pin (era 5D iter-1/3/4) | N/A — these are this session's own prior demolition work, not pre-`clean_slate` features | Not touched this iteration | UT-14/UT-J-01 (14 routes 404), UT-J-03 (MCP `list_tools()` exactly 15 names, source-grepped), UT-J-04 (pin `08e471b10130e1e2` live) all pass | **Low** |

**Not touched, and therefore not independently re-tested this iteration**: the "Fetch from Yahoo
Finance" button and the strategy-registry/champion comparison area of `/structure` — the 2-line
diff is nowhere near either code path, so there is no plausible regression vector, matching the
same reasoning iter-2's own ux-regression review applied to analogous untouched-but-nearby features
in this file. Noted for completeness, not as a flag.

**Two observations from the browser-qa evidence that I considered and ruled out as regressions**,
since a UX reviewer should not silently pass over them just because QA marked the parent test PASS:
- *UT-12 same-session "false alarm"*: during a busy back-to-back test sequence, one Stop click
  appeared not to fully reset state, but a dedicated isolated retest (fresh watch → single click →
  immediate check) showed correct behavior on the first click. QA's own account attributes this to
  rapid-fire automation timing, not a product defect, and I have no independent evidence to the
  contrary — treated as a non-issue.
- *MCP tool-list discrepancy in this session's own tool listing (showing 18 tools including
  `journal`/`analytics`/`studies`)*: a direct, fresh grep of `apps/backend/app/mcp/__init__.py`
  (which I did not re-run myself but which QA performed and reported concretely) finds exactly 15
  `types.Tool()` definitions with none of those three names — the discrepancy is a stale
  client-side tool-manifest cache from earlier in this interactive session, not a product
  regression. Treated as a non-issue for this review.

---

## UI vs Backend Parity

| Backend capability | UI exposure | Parity |
|---|---|---|
| `GET /research/setups` (band-touch events, reaction, forward returns, tape timeline) | Case Studies panel — now rendering again | **Matched** (this iteration closes the one pre-existing gap) |
| Everything else on `/structure` and Cockpit (Tradable Map, Levels & Zones, Edge Report, sim cockpit, both charts) | Already fully exposed by prior eras | **Matched** — no backend change this iteration (`git diff --stat` confirms zero backend files) |

`implementation-summary.md` and `user-visible-changes.md` agree exactly: zero new backend
capability was added this iteration, and the one previously-lagging surface (Case Studies'
rendering) is now closed. `user-visible-changes.md`'s "Not Visible Yet" section correctly reads
"None." No parity gap found.

---

## Flags

### Hidden Capabilities
None. The one restored capability (Case Studies panel) is not hidden — it renders unconditionally
and is on-screen within the first viewport per UT-16.

### Undiscoverable Capabilities
- **Case Studies row-click → drill-in has no visible feedback for a first-time user.** The panel
  itself is 1 click from home and immediately on-screen, but the actual result of clicking a row
  (the drill-in view) renders ~65,000px below the page top when the table is unfiltered (its
  default, first-load state, at 1,758 rows) — with no auto-scroll, no toast, and no inline
  expand/collapse. A user who clicks a row without already knowing to scroll that far will
  reasonably conclude the click did nothing. This is now user-facing for the first time because the
  whole panel was invisible until this iteration's flag flip — QA's own evidence documents the exact
  pixel distance and confirms there is no scroll-into-view behavior. Not severe enough to call the
  capability inaccessible (the drill-in is provably correct and reachable by manual scroll, and
  filtering the table — which is itself prominent and easy to find — collapses the distance
  immediately), but real enough that I cannot call this "no gaps." **Recommendation**: scroll the
  drill-in into view on row click (or an equivalent affordance — inline row expansion, a "jump to
  detail" link, or table pagination/virtualization so the drill-in never lands more than one
  viewport away).

### Potential Regressions
None confirmed. Every shared-component risk in the table above was independently or QA-verified,
and I independently re-derived the diff's actual scope via `git diff` rather than relying solely on
the handoffs' self-description — it matches exactly what every report claims (one boolean literal +
one paragraph sentence).

### Visual Consistency
- No restyle shipped (by design — the plan explicitly scoped this to a gate flip, not new UI
  construction). Direct source inspection of the Case Studies section (`apps/frontend/app/
  structure/page.tsx:2340` onward) confirms it reuses the shared `Panel` component, the shared
  `INPUT_CLASS` constant for its filter inputs, and the same Tailwind slate-palette utility classes
  (`text-slate-600`, `text-slate-500`) used throughout the rest of the page — no inline `style={{}}`
  attributes, no arbitrary one-off values found in this section.
- The framing-paragraph edit is copy-only, confirmed to insert cleanly with no adjacent text
  disturbed (`npm run build` compiled with 0 type errors, and my own diff read shows a clean,
  well-formed insertion).
- No new page, no new component — consistent by construction with the pre-existing `/structure`
  styling from era 5B/5C, which is not something this iteration altered.

---

## Recommendation

Ship as-is; nothing here blocks this iteration's own goal (a regression sentinel + a one-flag
restore). One follow-up worth logging for a future iteration, not this one: give the Case Studies
drill-in a scroll-into-view (or equivalent) affordance so the newly-restored row-click interaction
doesn't read as broken on an unfiltered, ~1,758-row table. This is a pre-existing condition from
era 5B/5C's original build, now reaching real users for the first time as a direct consequence of
this iteration's flag flip — which is exactly why it surfaces in this review rather than an earlier
one.
