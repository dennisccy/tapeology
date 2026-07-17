# goal-fast_wall-iter-1 Frontend Handoff

**Phase:** goal-fast_wall-iter-1
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

`/structure`'s Edge Report section gains a fifth, honest state: **not-computed**. Previously the
section only ever rendered loading → unavailable → populated (empty or with cells); now a cold
backend cache with a non-empty dataset registry renders a distinct panel instead of either an
indefinite spinner or (before this iteration's backend fix) a page load that silently pinned the
backend at high CPU for hours.

- New panel: `NotComputedPanel` — headline **"Edge report not computed yet."**, followed by the
  server's own `detail` string rendered verbatim (never a frontend-authored message). No button,
  no interactive element — this iteration's not-computed panel is read-only; the "Compute edge
  report" trigger is explicitly out of scope (J-04).
- New information surfaced: the not-computed payload's `detail` (why nothing has computed yet)
  becomes visible on `/structure` whenever the cache is cold. (`dataset_count` and `register` are
  part of the payload but not separately rendered this iteration — `EdgeReportBody` already shows
  the register banner in the populated state, and `dataset_count` has no existing UI slot; neither
  omission changes any acceptance criterion.)
- No new page, no new nav entry, no new user action beyond navigating to `/structure` (unchanged).

## Visual Treatment

Reused the existing `UnavailablePanel`'s exact Tailwind classes (`rounded-lg border
border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center`, amber headline + amber-200/70 detail
text) rather than inventing a new visual language, per the phase spec's Design Direction. This was
a judgment call between `UnavailablePanel`'s amber "needs attention" treatment and `EmptyState`'s
slate "calm empty result" treatment — the not-computed state is closer in spirit to the former (an
operator action would resolve it) than the latter (a genuinely completed empty result), so amber
was chosen. `NotComputedPanel` has its own `data-testid="edge-report-not-computed"` and its own
copy — never sharing a testid with `UnavailablePanel` or `EmptyState`.

## Files Changed

- `apps/frontend/lib/types.ts` — `EdgeReportResponse` gained a `status?: undefined` field (a
  TypeScript-only discriminant, never present on the wire); added `EdgeReportNotComputed` and the
  `EdgeReportPayload` union type.
- `apps/frontend/lib/api.ts` — `fetchEdgeReport()` return type updated from `EdgeReportResponse |
  null` to `EdgeReportPayload | null`. The fetch call, endpoint, and error-handling logic are
  byte-unchanged.
- `apps/frontend/app/structure/page.tsx` — added the `NotComputedPanel` component (placed beside
  `LoadingPanel`/`UnavailablePanel`/`EmptyState`); updated the `edgeReportResult` state type;
  inserted one new conditional branch (`edgeReport.status === "not_computed"`) in the Edge Report
  section's render, checked before the `EdgeReportBody` fallback.

## States Handled (Edge Report section, five total)

1. Loading (existing, unchanged) — `LoadingPanel`.
2. Fetch-unavailable (existing, unchanged) — `UnavailablePanel`, backend unreachable or non-200.
3. **Not-computed (new this iteration)** — `NotComputedPanel`, cold cache + non-empty registry.
4. Warm-empty (existing, byte-unchanged) — `EmptyState` "No edge-report cells yet." + register
   banner, frozen testids `edge-report-empty` / `edge-report-register`.
5. Warm-populated (existing, unchanged) — `EdgeReportBody` with the cell tables.

## Tests Run

Command: `cd apps/frontend && npm run build` (isolated `NEXT_DIST_DIR`)
Result: compiled successfully, zero TypeScript errors under `strict: true`, all 7 app routes
built including `/structure`.

This project has no frontend unit-test framework (no jest/vitest, no `.test.tsx` files) — `npm
run build`'s type-check is the frontend test command per `README.md`. UI behavior verification was
done via a real browser (Chrome MCP) against a scoped backend — see the dev handoff's "Live
verification" section for the exact steps and evidence (both the cold not-computed render and the
warm frozen-empty-state render were confirmed via `await_text` and full-page text extraction).

## Known Issues

- No automated browser test is checked into the repo for this panel (this project's test
  discipline puts browser verification in the QA pipeline stage, not developer-authored frontend
  unit tests — consistent with how prior UI iterations in this codebase were handled).
- The not-computed panel's `dataset_count` field is fetched and typed but not rendered anywhere in
  the UI this iteration — not a spec requirement (the spec only requires `detail` to be visible),
  flagging in case a reviewer expects it.
