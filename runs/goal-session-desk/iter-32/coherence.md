# Iteration 32 — Coherence Audit

**Iteration:** goal-desk-iter-32
**Date:** 2026-07-31
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Top-up run records — new per-pair field `store_frozen_through_after` | OK | `apps/backend/app/research/desk_topup_compute.py:339` (`window_after = _pair_window(bar_store, symbol, timeframe)`) and `:352` (`entry["store_frozen_through_after"] = window_after["store_frozen_through"]`) — same canonical accessor `_pair_window` already used pre-fetch at `:334`, called a second time post-fetch; no new accessor, no `bar_index.window_end_utc` read. Registered in `runs/goal-session-desk/state/blueprint.md:179` (iter-32 addition note) BEFORE the build, matching the iter spec's Data-contract-additions section. |
| Top-up run records — served shape | OK | `apps/backend/app/research/desk_topup_log.py` has zero diff (confirmed via `git diff --stat`); the new field rides through the existing generic per-entry-dict persister. Served by the already-registered `GET /research/desk/topup/runs` — no new endpoint. |
| `/desk` UI consumption of the new field | OK | `apps/frontend/app/desk/page.tsx:864-901` (`topupLibraryReach`) reads `run.outcomes` from the SAME `DeskTopupRun` object already fetched for the Top-up Runs panel — no new fetch call, no client-side recomputation of a registered value, a plain read+format (extreme/tally over already-served fields), matching Part A.3 (re-format is fine). |
| Distinctness from `desk_coverage`'s freshness value / `bar_index.window_end_utc` | OK | Both the module docstring (`desk_topup_compute.py:79-108` new prose) and the frontend comment (`page.tsx:320-328`) explicitly state the new value is never `bar_index`'s `window_end_utc` and creates no second coverage path; `desk_coverage.py`, `bar_index.py`, `bars.py` all show zero diff in the snapshot-diff stat. |
| Legacy-run fallback (`store_frozen_through_after` absent) | OK | `page.tsx:875` (`if (outcomes.some((o) => o.store_frozen_through_after === undefined)) return null;`) renders the honest `LIBRARY_REACH_NOT_RECORDED` fallback rather than computing/backfilling — verified structurally by the new guard test `test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after` (`apps/backend/tests/test_desk_topup_library_reach_guard.py:487-497`). |

No new function/service/endpoint independently recomputes any registered value; no new UI surface fetches a registered value from a non-canonical source; the one new value is registered in the blueprint's Data Contract in the same commit as the code, not a synonym of any existing registered value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-19 library-reach disclosure | OK | No new route/page/section. `apps/frontend/app/desk/page.tsx` diff only adds a block inside the already-shipped `LatestTopupRunDetail` component, on the already-registered `/desk` page (nav entry unchanged since iter-4). Checked `apps/backend/app/meta.py`'s `UI_ROUTES` is not in this iteration's diff (zero diff, per the snapshot-stat) — the 3-row nav skeleton is untouched. |
| Placement within the existing Top-up Runs panel | OK | New guard test `test_the_reach_line_and_earlier_list_are_present_beside_the_window_basis_line` (`apps/backend/tests/test_desk_topup_library_reach_guard.py:476-484`) structurally proves the new `desk-topup-run-latest-reach`/`-reach-earlier` blocks sit between the existing `desk-topup-run-latest-window-basis` and `desk-topup-run-latest-failed` blocks — same section, no reordering, no new control. |

No new page, no new nav-skeleton row, no duplicate home for an existing entity, no parallel shell. `blueprint.md`'s Feature/journey-homes table already lists J-19's canonical home as `/desk` (existing Top-up Runs section) before this build, and the code matches it exactly.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The page now carries two distinct "how far does the data reach" concepts — `desk_coverage`'s "window last requested" freshness badge (whole-store, screen-compute-time) and this iteration's new "newest recorded reach" line (per-run, per-pair, topup-attempt-time). Both are clearly and differently labeled, and the distinction is deliberate and already documented in the blueprint (this is a continuation of the same discipline established at iter-2/iter-26, not a new pattern introduced this iteration) — noted only so a future reader doesn't mistake the two for the same measurement if they ever drift apart in wording.
- Everything else checked (field naming consistency across backend/`types.ts`/frontend, zero diff on the explicitly-frozen files list, fingerprint/MCP-tool-count invariance per the spec's DoD) is in order; no further advisory notes.
