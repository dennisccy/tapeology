# Phase goal-clean_slate-iter-2 — UX Regression Review

**Date:** 2026-07-24

**Verdict:** UX-REGRESSION-PASS

---

## Context

J-02 ("Frontend + WS demolition — the two-page product") is a **subtractive-only** iteration.
Goal.md's own Anti-goals name this the ONE sanctioned exception to "frozen foundations" this era:
the journal/studies/performance product surfaces are removed outright, by explicit operator
approval, never mutated-in-place. That inverts the usual UX-regression posture: the disappearance
of `/journal`, `/journal/[id]`, `/studies`, `/performance`, the thesis strip, the hint dock, and the
sound-cue toggle is the *goal*, not a defect. This review therefore checks two different things: (1)
that the removal is complete and clean (no orphaned nav entries, dead links, or half-deleted
screens), and (2) that the SURVIVING product — Cockpit (`/`) and Structure (`/structure`), including
every feature prior eras built into them — still works, since this iteration edited several
high-centrality shared files (`app/page.tsx`, `Cockpit.tsx`, `PriceChart.tsx`, the WS stream handler,
the nav route list).

I independently re-verified a sample of the strongest claims in the reports rather than taking them
at face value — see inline evidence below. The dev/QA servers were not running at review time (no
live browser pass performed by me), so the primary evidence for live rendering remains the
browser-qa-agent's 18/18-PASS run with DOM assertions, screenshots, and a 3,595-frame WS capture
(`reports/phase-goal-clean_slate-iter-2-ui-test-results.md`); my own checks targeted the filesystem
and git history claims, which don't require a running server.

---

## New Capability Discoverability

**N/A — zero new capabilities, information, or actions were added this iteration**, confirmed
consistently across goal.md's own acceptance text, `user-visible-changes.md`,
`implementation-summary.md`, and both dev handoffs. There is nothing new to assess for
discoverability.

The inverse check — is the *removal* itself clean and complete, not a half-measure — is what
matters here:

| Removed capability | Navigation-path check | Result |
|---|---|---|
| `/journal`, `/journal/[id]` | No nav entry anywhere; direct URL → app's real 404 | Independently confirmed: `apps/frontend/app/journal/` does not exist on disk (`ls` → "No such file or directory"); `find apps/frontend/app -iname "*journal*"` → zero hits (no orphan `loading.tsx`/`error.tsx` either) |
| `/studies` | Same | Independently confirmed: directory absent, zero filename hits |
| `/performance` | Same | Independently confirmed: directory absent, zero filename hits |
| Thesis strip / hint dock / sound toggle | No nav or in-page affordance anywhere on Cockpit | Confirmed via QA's UT-08 (0 SVG circle markers, no thesis/hint/sound text across 2 full Watch→Stop cycles) and UT-16 (full-body DOM text scan for "Declare thesis"/"Hint"/"Prefill" on `/` and `/structure` → zero hits) |
| Nav bar itself | Should show exactly "Cockpit" + "Structure", nothing greyed-out | QA UT-03/UT-15 confirm via `document.querySelectorAll('nav a')` → exactly `["Cockpit","Structure"]` on both pages, one-click navigation works, active link highlights correctly |

`apps/frontend/app/` now contains exactly `globals.css`, `layout.tsx`, `page.tsx`, `structure/` —
independently confirmed via `ls`. This is precisely the two-page skeleton the session's own
blueprint (`runs/goal-session-clean_slate/state/blueprint.md`) pre-registered as this interlude's
target Information Architecture, independently cross-checked: its Navigation skeleton section and
its Feature/journey-homes table both list only `/` (Cockpit) and `/structure` (Structure) as live
routes after J-02, matching the shipped state exactly.

No "coming soon" placeholder or custom tombstone page was built — all four deleted URLs fall through
to the app's one pre-existing not-found treatment (same component, same styling), which is what
goal.md's anti-goals require.

---

## Regression Risk

Per the UI Regression Scout method, the components this iteration's `ui-surface-map.md` touches are
cross-referenced against the features prior eras built on top of them:

| Shared component touched this iteration | Prior feature(s) depending on it | Risk (pre-verification) | Verification found | Residual risk |
|---|---|---|---|---|
| WS stream handler (`app/main.py`) — `thesis`/`hint` merge removed | The entire live-tape experience (every panel on Cockpit, across every era back to `tape_to_profit`) reads this frame | **High** — touches the one feed every live feature depends on | QA UT-13 independently captured 3,595 real frames via a `WebSocket` monkey-patch; 0 contain `thesis`, 0 contain `hint`; the full surviving key set (`ticker, scenario, stream_status, paused, data_feed, delivery_lag_seconds, warm, timestamp, market, tape_state, confidence, primary_window, features, headline_features, observations, event_log, recent_trades`) matches what every surviving panel needs | **Low** |
| `PriceChart.tsx` — thesis-geometry overlay removed only | The 2026-07-23 "Cockpit chart upgrade" (candles, timeframe switching, S/R band overlay, live moving bars; `StructureChart` unification) — the single most recently-built feature this file carries | **High** — most recently-built, highest-centrality touched file | QA UT-10 (Tape 30s/60s switch via `aria-pressed`, live price move 100.88→103.08 over 15s, x-axis window shift, 0 circle markers) + UT-11 (History 1h switch, S/R band renders "R A · 171 · round" at 300.10, provenance badge correct, 0 circle markers) + 3 chart guard test suites (33 tests, all pass, all 3 files byte-unmodified). Dev's own Known Issue #1 shows the guard suite caught a near-miss (an over-deletion of the `extraPriceLines` prop-passing seam) **before** it shipped — evidence the safety net is working, not a residual gap | **Low** |
| `StructureChart.tsx` — the shared renderer both `/structure` and `PriceChart` delegate to | Every chart-consuming feature since `structure_ui`/`tradable_wall`/`fast_wall`/the 2026-07-23 chart-upgrade era | **High** if touched | Independently re-ran `git diff HEAD~1 -- apps/frontend/components/StructureChart.tsx` → **0 lines**, confirming the T-8 veto-class guarantee held | **None** (untouched) |
| `Cockpit.tsx` — `HintDock`/`onHintDeclare`/`Hint` removed, one wrapper div simplified | The core tape_to_profit-era panel grid (Quote/RecentTrades/Features/TapeState/Observations/EventLog) | **Medium** | Dev handoff states these six components are byte-untouched; QA UT-08 confirms the 6-panel grid renders correctly across two full Watch cycles | **Low** |
| `app/page.tsx` — thesis/hint state, handlers, and both `<ThesisStrip>` render sites removed | Watch/Stop flow, ticker validation, idle/failure/live state machine — core since the earliest cockpit eras | **Medium** | QA UT-01 (idle state), UT-08 (Watch→Buyer Control), UT-09 (Stop→idle, confirmed no surviving-thesis branch lingers via DOM `bodyHasNoTicker`/`bodyHasWatching`), UT-14 (empty-ticker validation) all pass | **Low** |
| `app/meta.py` nav route list | Reachability of every page, all eras | **High** (universal dependency) | QA UT-03/UT-15 confirm both pages show the correct 2-link nav with correct active-highlight and working client-side navigation; `NavBar.tsx` independently confirmed byte-unedited (`git diff HEAD~1` → empty) | **Low** |
| `test_profile_equivalence.py` — 1 test deleted (read the now-gone `/performance` page's source off disk) | Backend test coverage only, no UI surface | Low | Dev handoff documents this as a T-14 correction; the other ~14 tests in the file are untouched | **None** (test-only) |

**Not touched, and therefore not re-tested, this iteration** — `/structure`'s own page-level
features from prior eras (the "Fetch from Yahoo Finance" button, the Compute button/resumable
sweep, the edge-report cache display, the tradable-map table, the strategy-registry/champion
comparison): `apps/frontend/app/structure/page.tsx` is not in this iteration's changed-file list,
and independently confirmed via `git log -1` its last touching commit is `fa76460`
(2026-07-23, predating this goal session). QA's own pass re-verified only the Load flow + wall-band
render (UT-12) and the nav/idle state (UT-02) for this page, not the Fetch/Compute buttons
specifically — reasonable, since none of the files this iteration edited are reachable from those
buttons' code paths, so there is no plausible regression vector. Noting this for completeness, not
as a flag.

---

## UI vs Backend Parity

This iteration is unusual in that "backend capability not yet surfaced in UI" doesn't apply — there
is no new backend capability to surface, only backend deletions that the UI already reflects
one-for-one:

| Backend change | UI reflection | Parity |
|---|---|---|
| WS `thesis`/`hint` merge removed | Thesis strip / hint dock / sound toggle gone from Cockpit | Matched |
| `ResearchRegistry` dead stubs removed | No UI surface (was never rendered — permanent `None` stubs) | N/A, correctly backend-only |
| `UI_ROUTES` trimmed 6→2 | Nav shows exactly 2 links | Matched |
| 4 pages deleted on the frontend | Same 4 routes already 404 on the backend since iter-1 | Matched |

**One genuine backend/UI-surface gap exists, but it is not a browser-UI gap and is explicitly,
correctly scoped out of this iteration**: the MCP tool list (an AI-assistant integration surface,
not the browser UI) still offers three tools named `journal`, `analytics`, `studies`. They already
honestly return "not found" (their backing routes 404'd since iter-1) rather than failing silently or
returning stale data — so the gap is disclosed and non-deceptive, not hidden. `user-visible-changes.md`'s
own "Not Visible Yet" section documents it, the phase spec's Out-of-Scope section defers it to J-03 by
name, and iter-1's audit (finding B1) independently confirms the same scoping. This does not affect
any real end user in a browser and does not warrant a flag under this phase's own goal (which is
explicitly "the two-page product... in a browser").

---

## Flags

### Hidden Capabilities
None. Nothing new was added this iteration, so there is nothing that could be hidden.

### Undiscoverable Capabilities
None.

### Potential Regressions
None confirmed. Every shared/touched component in the Regression Risk table above was independently
or QA-verified to still serve its prior-era behavior. The highest-centrality touched file
(`PriceChart.tsx`, carrying the 2026-07-23 chart-upgrade feature) has the strongest evidence trail:
live DOM assertions, two independent watch scenarios, 33 passing chart-guard tests across all 3
chart files, and a documented near-miss that the guard suite itself caught pre-ship.

### Visual Consistency
- No new UI shipped this iteration (pure deletion + one prop removal), so there is no
  new-page-vs-established-style comparison to make. The one structural change
  (`Cockpit.tsx`'s wrapper-div simplification around `TapeStatePanel`, since `HintDock` was its only
  sibling) is confirmed visually inert by both the dev handoff and QA's UT-08 screenshot evidence.
- The 404 treatment for all four deleted URLs reuses the app's single pre-existing not-found
  component — consistent by construction (same component instance handles all four), not a
  new/divergent design.
- **One informational, non-blocking note found via independent verification, not a UX-visible
  issue**: TC-11's acceptance grep (`grep -rln "<25 doomed identifiers>" apps/frontend/`, excluding
  history dirs) was re-run by me exactly as specified in the phase spec, and it returns **one hit**
  outside the excluded directories: `apps/frontend/app/structure/page.tsx:1305`, matching the literal
  substring `StudyResultsView` inside a source comment ("...unlike a Study's cancelled-but-partial
  results, so this is intentionally NOT a reuse of `StudyResultsView`'s `results-cancelled` copy").
  Both this iteration's dev handoff and frontend handoff describe this occurrence as "the bare word
  'Study'" and state it "does not trip TC-11's grep" — that description is inaccurate; the comment
  contains the exact compound identifier the grep targets, and the grep does match it. **This has
  zero user-facing impact**: it is inside a `//` comment, never rendered to the DOM, not imported or
  called, and UT-16's own full-body rendered-text scan (the UX-relevant check) correctly found zero
  occurrences of forbidden text on either live page. I flag the discrepancy for the record — the
  handoff's self-description of this item should be corrected — but it does not change this review's
  verdict and does not warrant blocking on its own (the dev's stated reasoning for leaving it alone,
  not touching an out-of-scope high-stakes file for one stale comment word, is sound either way).

---

## Recommendation

No blocking action required. This is a clean demolition iteration: the four deleted routes are fully
gone (grep- and filesystem-provably, independently re-verified), the two surviving pages retain every
prior-era behavior this iteration's diff could plausibly have touched (both charts, the panel grid,
the provenance badge, the nav), and the one backend/UI surface still lagging (the MCP tool list) is
honestly disclosed and correctly scoped to next iteration (J-03).

Optional, non-blocking cleanup for whoever next legitimately opens `apps/frontend/app/structure/page.tsx`:
reword the comment at line 1305 to drop the literal `StudyResultsView` identifier (e.g., "a
replay-study's cancelled-but-partial results" instead of naming the deleted component), so the
TC-11-style grep genuinely returns zero hits rather than needing a documented exception. Not worth a
dedicated edit to an otherwise-untouched, high-stakes kept page on its own.
