# Phase goal-yahoo_fetch-iter-6 — User-Visible Changes

**Phase:** goal-yahoo_fetch-iter-6
**Date:** 2026-07-11
**Written by:** ui-impact-analyst

---

## Summary: zero user-visible change this iteration

This iteration made **no product source changes**. Confirmed independently: `git diff --stat HEAD --
apps/` returns empty output, and the dev handoff's own file-by-file re-check of every frozen file
(`config.py`, `research/levels.py`, `research/bars.py`, `providers/adapters/{yahoo,alpaca}.py`,
`app/structure/page.tsx`, `FeedBasisBadge.tsx`, `SymbolSearch.tsx`, etc.) agrees. The only two new
files this iteration produced are process documents
(`docs/handoffs/goal-yahoo_fetch-iter-6-dev.md`, `reports/phase-goal-yahoo_fetch-iter-6-implementation-summary.md`)
— neither is rendered anywhere in the running app. Every page, button, label, and behavior a user
encounters today is byte-identical to what iter-5 shipped.

This iteration's actual job was to prove the environment is ready to land real browser evidence of
that already-shipped surface (a clean, unoccluded provenance-badge screenshot and a browser-captured
honest empty state) — the capture itself happens in the downstream ui-test-designer / browser-qa-agent
pipeline steps, not in this analysis.

The four sections below answer strictly against **this iteration's diff** (which is empty), per this
agent's mandate to describe only what changed. For the still-accurate description of the underlying
capability (built in iter-5, unchanged), see
`reports/phase-goal-yahoo_fetch-iter-5-user-visible-changes.md` — every claim in that report was
independently spot-checked against current source during this analysis (citations below) and remains
accurate today.

---

## What Users Can Now Do

**Nothing new.** No capability was added this iteration. The "Fetch from Yahoo Finance" control on
`/structure`, its store-first instant re-serve for an already-fetched window, the
auto-populating candlestick chart / S/R level lines / A-B-C confluence-zone table, the "Yahoo Finance"
provenance badge, and the specific per-error-code messaging were all already available to users as of
iter-5 and remain available, unchanged, today. Re-verified directly against source:
`apps/frontend/app/structure/page.tsx`, `apps/frontend/components/FeedBasisBadge.tsx`, and
`apps/frontend/components/SymbolSearch.tsx` all show zero diff against what iter-5 shipped.

## What Changed in the Visible UI

**Nothing.** No page, component, label, layout, form field, or navigation element changed. A user at
the browser today sees an identical `/structure` page to the one iter-5 left behind — same fetch
panel, same badge placement (directly above the price chart, `structure/page.tsx:1096`, immediately
before `<StructureChart>` at line 1099), same empty/error states.

## What Old Behavior Changed

**None.** No existing behavior changed. The dev handoff's live re-check against the real running app
reconfirmed iter-5's behavior still holds exactly: a repeat `POST /research/bars` for an
already-indexed window returned `200` (not a live network fetch) in ~10ms wall-clock, `GET
/research/levels` returned real computed levels/zones from real Yahoo-sourced bars, and `GET
/research/taxonomy` still serves `{"id":"yahoo","name":"Yahoo Finance"}` for the badge to read.

## Not Visible Yet

**None new.** No backend capability was added this iteration that lacks UI wiring, because there is no
backend change at all this iteration. (Iter-5's own pre-existing "not visible yet" item — a `GET
/research/bars` blank-parameter fix with no reachable UI trigger — is likewise unchanged; it is not
re-listed here since nothing about it is new to this iteration.)

---

## Why this iteration exists despite zero UI change (context for the downstream QA/test-design steps)

Nothing in the app changed, but two pieces of **evidence about the existing UI** were missing, and
closing that gap is this iteration's entire purpose:

1. **The "Yahoo Finance" badge is occluded in every iter-5 screenshot.** The badge itself
   (`data-testid="feed-basis-label"`, `FeedBasisBadge.tsx:60,68,71`) computes its label from `GET
   /research/taxonomy` (`feeds.find((f) => f.id === dataFeed)?.name`) with zero hardcoding, and is
   confirmed rendered correctly. The occlusion is caused by a *different*, pre-existing component:
   `SymbolSearch`'s suggestion dropdown auto-opens (`SymbolSearch.tsx:44-68`) because
   `handleFetchYahoo`'s success path programmatically sets the Load form's own symbol field
   (`structure/page.tsx:793`, `setSymbolInput(result.bar_series.symbol)`), and `SymbolSearch` cannot
   distinguish that from a user keystroke. This is a real, user-visible quirk — but it is deferred
   (see the phase spec's Out of Scope), not fixed, because a clean screenshot is obtainable with zero
   code change: `SymbolSearch` already has a second, unconditional outside-click dismiss handler
   (`SymbolSearch.tsx:71-77`) that the evidence-capture step must invoke (click elsewhere on the page)
   immediately before the badge screenshot.
2. **The honest "no bar series" empty state (`data-testid="structure-no-bar-series"`,
   `structure/page.tsx:1068`) has never been browser-captured**, only unit-tested. The dev handoff
   confirms `TSLA` returns zero stored series live (`GET /research/bars?symbol=TSLA` →
   `{"bar_series":[],"integrity_errors":[]}`) and recommends it as the capture symbol.

Neither of these is a code change a user would notice differently — they are gaps in this project's
own proof trail, which `phase-closure-auditor` checks. See
`reports/phase-goal-yahoo_fetch-iter-6-ui-surface-map.md` for the concrete surfaces and exact test
actions the downstream browser lane needs to exercise to close them.
