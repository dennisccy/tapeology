# goal-structure_ui-iter-2 Frontend Handoff

**Phase:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

The **Registry section** — a new section on the existing `/structure` page (below the J-01 Levels &
Zones section), showing the two registered strategies (`v1`, `structure_tape`) with their
config-owned parameters and the current champion, all read verbatim from `GET /research/strategies`.
This is the app's first browser surface for era-4's strategy registry — previously visible only via
`curl`/MCP.

## New user-facing capability

A person on `/structure` now sees, without scrolling away from the page they're already on:

- Two strategy cards. `v1`'s shows its entry rule, its `r_stop`/`state_flip`/`horizon`/`dataset_end`
  exit rule names, and a static caption describing the exit-check order.
  `structure_tape`'s additionally shows a `reward_target` row (v1 genuinely has none — an honest
  omission) plus three compact tables: stop distance, reward target, and simulated size, each broken
  out by confluence class (A/B/C).
- A **Champion** badge showing which strategy/profile pair is currently favored (`v1`/`default`,
  the founding pair, on this keyless fixture), with a small caption confirming it matches the
  champion served by the profile-registry endpoint too.
- If the registry can't be reached, an explicit amber "unavailable" panel — never a blank section,
  never a guessed `v1`/`default` placeholder.

This section loads on page open — no button click needed (the spec calls for this: the registry and
champion are populated even without any symbol chosen or any bars recorded).

## Component/file map

- `apps/frontend/app/structure/page.tsx` — the Registry section lives here: `ClassMapTable` (a small
  class → value table, reused 3× per `structure_tape` card), `StrategyCard` (one strategy's full
  card), the mount-time fetch effect, and the champion cross-check. The existing Levels & Zones
  section above it is unchanged.
- `apps/frontend/lib/api.ts` — `fetchStrategies()` (new), sitting beside the pre-existing
  `fetchProfiles()` it now also calls from the page.
- `apps/frontend/lib/types.ts` — `Strategy` / `StrategyExits` / `StrategyExitRule` /
  `StrategiesPayload` (new). `StrategiesPayload.champion` reuses the existing `ProfilesPayload`
  champion shape rather than declaring a new one.
- `apps/frontend/components/StructureChart.tsx` — untouched. Read directly to confirm the iter-1
  audit's empty-state z-index fix (line 99, `z-10`) and corrected copy (line 100, "No candles to
  draw at this as-of time.") are both already in place; no residual occlusion was found, so no edit
  was needed here this iteration.

## Visual/UX states implemented

| State | Trigger | Copy (verbatim) | `data-testid` |
|---|---|---|---|
| Loading | Page mount, fetch in flight | pulse-skeleton placeholder (reused `LoadingPanel`) | `structure-registry-loading` |
| Registry unavailable | `GET /research/strategies` unreachable/non-200 | "Backend unreachable — is the API running?" (or the backend's own message) / "Nothing cached and nothing fabricated is shown in its place." | `structure-registry-unavailable` |
| Populated | Fetch succeeds | Two strategy cards + champion badge | `strategy-card` ×2, `champion-summary`, `champion-strategy`, `champion-profile` |
| Champion cross-check — pending | `/research/profiles` still loading | "Cross-checking against GET /research/profiles…" | `structure-champion-crosscheck-pending` |
| Champion cross-check — unavailable | `/research/profiles` failed (registry itself still shown) | "Cross-check against GET /research/profiles: unavailable." | `structure-champion-crosscheck-unavailable` |
| Champion cross-check — match | Both endpoints agree (the expected live case) | "Confirmed identical to the champion served by GET /research/profiles — one store pointer, two read views." | `structure-champion-crosscheck-match` |
| Champion cross-check — mismatch | Endpoints disagree (structurally unreachable on this codebase; defensive only) | "Warning: does not match the champion served by GET /research/profiles." | `structure-champion-crosscheck-mismatch` |

Per-card testids: `strategy-entry-rule`, `strategy-exit-r-stop`, `strategy-exit-reward-target`
(only on `structure_tape`), `strategy-exit-state-flip`, `strategy-exit-horizon`,
`strategy-exit-dataset-end`, `strategy-stop-bps-by-class` / `strategy-r-multiple-by-class` /
`strategy-size-multiple-by-class` (only on `structure_tape`), each `<article>` also carrying
`data-strategy-id` for stable per-card scoping in tests.

## Design system conformance

- Reused the file's existing local `Panel` component as the ONE container for the whole Registry
  section (titled "Registry", matching the uppercase/tracking-wide title style already used for
  "Price chart — S/R levels" and "Confluence zones" above it) — no new visual language introduced.
- Strategy cards and the champion badge reuse the exact `rounded-lg border border-slate-800
  bg-slate-900/60 p-4` card shape already established by `/performance/page.tsx`'s
  `LedgerRowPanel`/`champion-summary` and this file's own `ZoneRow`.
- The champion badge's testids (`champion-summary`/`champion-strategy`/`champion-profile`) are the
  IDENTICAL strings `/performance/page.tsx` uses — safe because the two badges never render on the
  same route at the same time; verified live that loading `/performance` after `/structure` shows no
  interference.
- Font-mono numerics (`NUMERIC_CELL`/`LABEL_CELL`, this file's existing constants) for every strategy
  field and class-map value; amber `border-amber-800/60 bg-amber-900/20 text-amber-300` for the
  unavailable state via the existing local `UnavailablePanel` — no new color introduced.
- Layout: single column, appended below the existing sections inside the same `max-w-7xl` — no
  sidebar, no new grid, per the plan's explicit visual requirement.
- Loading/empty/error states all present: `LoadingPanel` while the fetch is in flight,
  `UnavailablePanel` on failure, and the populated state itself has no "empty" variant (the registry
  is config-owned and always has exactly two entries — there is no honest "zero strategies" state to
  design for).

## Live browser verification performed

Ran the actual app (`bash scripts/dev.sh`) and drove it with the Chrome DevTools Protocol browser
tool end to end: the populated Registry rendered with every field verified byte-for-byte against a
direct `curl` of `GET /research/strategies` and `GET /research/profiles` (see the dev handoff for
the full field-by-field list); the registry-unavailable state was triggered by killing only the
backend process and confirmed to show no fabricated content; a restart of both services was
exercised to confirm no port conflicts; and `/performance` was reloaded afterward to confirm the
reused champion testids cause no cross-page interference. Screenshots were taken for this developer
sanity check but are not the formal QA evidence capture (that is the browser-qa-agent's job, into
`reports/qa/goal-structure_ui-iter-2-evidence/`).

## Known Issues / Limitations

- The `structure-champion-crosscheck-mismatch` state cannot be exercised live in this codebase
  (`GET /research/strategies` and `GET /research/profiles` share one store call, so they cannot
  actually disagree) — it is defensive, honest-state code that a reviewer/auditor may reasonably
  flag as "a handler for a state the system cannot reach." I kept it because a silent
  single-source-of-truth violation is exactly the failure mode the interlude's anti-goals name most
  strongly, and it costs three lines; see the dev handoff for the fuller reasoning.
- v1's own `r_stop` sub-parameters (`spread_multiple`, `floor`) are not rendered on its card — every
  planning document's field enumeration (goal.md, the phase spec, the plan) independently lists the
  same minimal set (entry rule; r_stop/reward_target/state_flip/horizon rule names; structure_tape's
  three class maps), and none of them ask for v1's own stop math. Not a gap against any of the four
  independent spec sources.
- No responsive breakpoint tuning beyond the page's existing `flex-wrap`/`overflow-x-auto`
  conventions — matches the precedent already set by every prior page on this project (`/performance`,
  `/studies`, and this same page's own J-01 section).
