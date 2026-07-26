# Goal Iteration 6 — Desk history drill-in to Structure

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-07
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk` BESIDE the kept two pages — the one sanctioned kept-surface edit is J-05's additive `/structure` prefill.) *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*

## GOAL

An operator on `/desk` can click a past recorded screen to see its own rows exactly as recorded (no
recompute), and can click any briefing row to jump straight into `/structure` with that symbol and
as-of already loaded — while `/structure` with no query params keeps behaving exactly as shipped.

## BACKGROUND

J-05 is next in the natural dependency order (J-01→J-04 all passing; J-06 is independent and
scheduled next per iter-5's own recommendation) and it is an unblocker for J-07's full acceptance
walk-through (a briefing → structure drill-in is part of the era's intended product story). Depth is
**full** — trigger 1 (structural/cross-cutting): this iteration makes the era's ONE sanctioned edit
to `apps/frontend/app/structure/page.tsx`, a file every other journey (J-07's regression sentinel)
walks as a kept, frozen surface, and wires a new cross-page link from `/desk` into it plus a new
guard test spanning both pages — exactly the class of change the anti-goal rail "Frozen foundations"
calls out by name as needing care, and iter-4's still-open, unrelated frozen-file exception (bars.py +
StructureChart.tsx) means this era's frozen-file discipline is already under scrutiny. "Needs unit
tests" is not the reason; the reason is the blast radius of touching the one frozen file this era
permits touching at all.

Backend needs **zero** new routes: `GET /research/desk/screen?date=YYYY-MM-DD` already exists
(shipped J-03, iter-3) and returns the exact persisted snapshot for that date verbatim — confirmed
live in this session's own inspection of `apps/backend/app/research/desk_routes.py:248-266`. J-05 is
therefore a frontend-wiring + guard-test iteration reusing already-registered contract values, not a
new-data-kind iteration.

Lessons applied from `lessons.md` (read before this iteration, all still live risks):
- iter-5's crux lesson: `runs/goal-session-desk/journey-scripts/J-04.json` step 5 clicks "Run Screen"
  — a WRITE action. This iteration's own full-depth pipeline runs the deterministic replay lane over
  the Required-still-passing set (which includes J-04); if that golden replays unfixed against any
  backend that is not a disposable copy, it records a real screen snapshot. Fixing it is IN SCOPE
  below, ahead of any browser-QA dispatch this iteration.
- iter-4's crux lesson: any browser/QA pass that can trigger a write path must be scoped to a
  throw-away data root, never the ambient `apps/backend/.data/`. J-05's own acceptance needs a
  screen that actually contains an AAPL row for 2026-06-22 (confirmed live in this session:
  `apps/backend/.data/screen/screen-2026-06-22-3ecd45c062c7.json` has `AAPL / class A / distance_bps
  0.335 / price_low 298.02 / price_high 300.1001 / as_of 2026-06-22T23:59:59Z`) — the browser pass
  must seed a **read-only copy** of that real screen snapshot plus its real AAPL bars into a
  throw-away root (the iter-5 fixture-scoped-backend recipe, extended with this one extra seed file),
  never point the QA browser at the operator's real `.data/`.
- iter-5's lesson on capture aids: if any display trick is used to photograph a transient state,
  disclose it up front in the QA report.
- iter-3's lesson on content-addressed stores: not directly touched this iteration (no store code
  changes), noted only because `desk_screen.py`'s `?date=` read path is being relied on — it already
  has no write side effect (a plain `store.list()` filter), so this risk does not apply to J-05.

## IN SCOPE

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`: make each row of `DeskHistoryTable` clickable. Selecting a
  past entry fetches `GET /research/desk/screen?date=<screen_date>` and renders THAT snapshot's own
  `rows`/`skipped`/provenance in place of the currently-shown one — no POST, no recompute. Provide an
  explicit control to return to the latest screen.
- [ ] `apps/frontend/app/desk/page.tsx`: make each ranked row AND each skip row a link to
  `/structure?symbol=<row.symbol>&asof=<currently-displayed-snapshot's as_of>` (the snapshot-level
  `as_of`, not a per-row field — it is shared by every row in one screen).
- [ ] `apps/frontend/lib/api.ts`: add the one client helper for the date-filtered read of the
  already-registered `GET /research/desk/screen?date=` endpoint (no new backend route; byte-identical
  proxy of what iter-3 already ships).
- [ ] `apps/frontend/app/structure/page.tsx`: on mount, read `symbol`/`asof` query params (Next.js
  `useSearchParams`, wrapped in the `Suspense` boundary the App Router requires); when BOTH are
  present, prefill `symbolInput`/`asOfInput` and invoke the SAME load path `handleSubmit`/`handleLoad`
  already use for a manual Load click. Additive only (T-8): zero change to any default, control, or
  rendered state when the params are absent.

### Backend / tests
- [ ] New guard test (source-introspection, the `test_copy_discipline.py` pattern) asserting (a)
  `apps/frontend/app/desk/page.tsx` contains no fetch/import referencing `/research/tradability` or
  `/research/levels` — every desk-page number still comes only from the already-fetched screen
  snapshot; (b) the new `/structure` prefill code path calls the page's existing load function, not a
  second one.
- [ ] Fix `runs/goal-session-desk/journey-scripts/J-04.json`: remove step 5's click on
  `desk-run-screen-button` (and the following `wait_for`), replacing them with read-only assertions
  of the same states, so replaying this golden against any backend never records a screen.
- [ ] Add a small golden or extend `test_desk_routes.py`-style coverage confirming
  `GET /research/desk/screen?date=` behavior used by the new frontend code is exercised (it already
  has backend tests from iter-3 — only add if the new frontend consumption path reveals a gap; do not
  duplicate existing coverage).

### New user-facing capability
Clicking a past entry in the Desk's screen-history list re-renders that recorded screen's own rows in
place; clicking any briefing row (ranked or skipped) jumps to `/structure` with that symbol and as-of
already loaded and the wall/bands already drawn.

### New information displayed
Nothing new is served — this iteration surfaces already-registered values (past screen snapshots,
`/structure`'s existing endpoints) through two new interaction paths.

### New user actions
Click a history-list row; a "Latest" control to return to the newest screen; click a ranked or
skipped briefing row to drill into `/structure`.

### UI surface changes
`/desk`'s screen-history list becomes interactive (read-only render swap, no new page); `/structure`'s
existing Load form gains query-param prefill + auto-Load, additive only.

### Product surface delta
The desk becomes a two-way surface: browse recorded history AND jump straight into the deep-dive
instrument for any row, without adding a fourth page or any new backend value.

### Blueprint conformance
Both homes already exist in `blueprint.md`'s Feature/journey homes table: J-05 → `/desk` (history
list) → `/structure?symbol=<sym>&asof=<iso>` (additive prefill), under the Desk and Structure nav
sections respectively. No nav-skeleton change.

### Data-contract additions
None. J-05 reuses the ALREADY-REGISTERED `GET /research/desk/screen?date=` shape (Data Contract row
"Screen snapshots, rank rows, skip rows," registered at iter-3) verbatim, and `/structure`'s existing
Load-form endpoints (tradability/levels/bars, unchanged). No new value, module, or endpoint is
introduced.

## OUT OF SCOPE

- J-06 (MCP contract v3, 17 tools) — independent of J-05's surface, scheduled next iteration per
  iter-5's own recommendation.
- Any edit to `StructureChart.tsx`, `PriceChart.tsx`, or `bars.py` — frozen; the iter-4 exception
  there is unrelated to J-05 and still awaits the owner's written ratification.
- A date-picker or any alternate-date control on `/desk`'s Run Screen button — settled at iter-4,
  unchanged.
- The three carried one-line hardening items (CLI screen-write-path guard, per-series price-less-row
  filter, chart-guard-test re-tightening) — none of their files (`desk_screen.py`'s CLI entrypoint,
  `bars.py`'s per-series read route, the chart guard test) are opened by this iteration's work, so
  they stay carried, not addressed here.
- Obtaining the owner's written ratification of the two still-open iter-4 frozen-file exceptions —
  that is a human action, not a build task; it stays as an active blocker note for the evaluator, not
  a blocker on J-05.
- Any change to the screen/universe/coverage compute managers or their persisted shapes.

## DEFINITION OF DONE

- [ ] J-05 passes via browser-qa-agent — history click-through renders a past screen's own rows,
  row drill-in lands on `/structure` with symbol+asof prefilled and auto-loaded, `/structure` with no
  params behaves exactly as shipped
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-07 remain green (deterministic replay
  + LLM fallback)
- [ ] No anti-goal violation introduced — desk pages recompute nothing; `/structure`'s default
  (no-params) behavior is byte-unchanged; copy-discipline lint stays green unmodified
- [ ] Unit tests pass; no regressions — full backend suite stays at or above the current floor
  (1328 pass / 8 skip, 0 fail) and `Config().config_fingerprint()` still prints `08e471b10130e1e2`
- [ ] `runs/goal-session-desk/journey-scripts/J-04.json` no longer contains a mutating click before
  this iteration's own replay lane runs it
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-6-dev.md`

## TESTING REQUIREMENTS

- Browser: J-05 (history click-through + row drill-in + `/structure` no-params baseline); regression
  replay/LLM fallback for J-01, J-02, J-03, J-04, J-07
- Unit/integration: the new source-introspection guard test (no structure recompute on `/desk`; the
  `/structure` prefill reuses the existing load function); existing `desk_routes.py`/`desk_screen.py`
  tests stay green unmodified
- Error cases: a history click for a date with no matching screen leaves the UI on its current
  snapshot (no crash, no blank state); `/structure?symbol=&asof=` with only one of the two params
  present behaves as if neither were present (no partial auto-Load)

Test-first contract:

- TC-1: given `/desk`'s history list shows the two recorded screens (dates 2026-06-22 and
  2026-07-25, from `GET /research/desk/screen`'s `screens` array), when the operator clicks the
  2026-06-22 row, then the page renders exactly that snapshot's AAPL row
  (`band_class A`, `distance_bps 0.33523150389608725`, `price_low 298.02`, `price_high 300.1001`) and
  matching `skipped` count, equal field-for-field to `GET /research/desk/screen?date=2026-06-22`'s
  JSON, with zero new POST request issued.
- TC-2: given the 2026-06-22 screen is being displayed (from TC-1), when the operator clicks the
  "Latest" control, then the page reverts to rendering the top-level `latest` snapshot from
  `GET /research/desk/screen`, unchanged from what it showed before TC-1's click.
- TC-3: given the 2026-06-22 screen is displayed and contains an AAPL row, when the operator clicks
  that row, then the browser navigates to `/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z`, the
  Symbol and As-of fields show exactly those two values, and a load has already run, rendering
  AAPL's tradable-map band covering the 298.02–300.1001 region (screenshot).
- TC-4: given `/structure` is opened directly with no query params, when the page mounts, then the
  Symbol and As-of fields are both empty, no load has been triggered, and the rendered state is
  pixel-for-pixel the same empty/default state as the pre-iteration baseline (screenshot).
- TC-5: given the source of `apps/frontend/app/desk/page.tsx`, when the new guard test scans it,
  then it finds zero references to `/research/tradability`, `/research/levels`,
  `compute_tradability`, or `compute_levels` — confirming every rendered number is read from the
  already-fetched screen snapshot, never recomputed.
- TC-6: given the source of `apps/frontend/app/structure/page.tsx`'s new prefill code, when the
  guard test scans it, then the prefill path calls the same load function the manual Load button
  calls — no second fetch/compute function is introduced.
- TC-7: given `runs/goal-session-desk/journey-scripts/J-04.json` after the fix, when it is loaded and
  inspected, then step 5 is no longer a click on any `testid` matching `run-screen` or `topup`, and
  replaying it against a freshly-seeded backend leaves that backend's screen-store file count
  unchanged before and after.
- TC-8: given the full backend suite, when it is run, then it reports 0 failures at or above the
  1328-pass / 8-skip floor and `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-9: given the iter-5 fixture-scoped `/desk` empty-state and populated-briefing screenshots as the
  shipped baseline, when J-01–J-04 are re-verified this iteration (deterministic golden or LLM
  fallback), then each renders the same acceptance state recorded in `journey-history.json` (no
  regression).
- TC-10: given a browser pass seeded with the throw-away copy of the real `screen-2026-06-22`
  snapshot plus its real AAPL bars, when the whole pass completes, then the operator's real
  `apps/backend/.data/` directory listing is byte-for-byte unchanged (the iter-4/iter-5 persistence
  discipline).

## NOTES

- Assumption logged to `runs/goal-session-desk/state/assumptions.md`: goal.md's J-05 step 3 says
  "make each briefing row a link" without distinguishing ranked rows from skip rows — this iteration
  reads that as BOTH row kinds link (a skipped symbol still drills into `/structure`, which will
  honestly show its own no-bars/empty state there); this is reversible and can be narrowed later if
  the owner disagrees.
- The browser-QA pass for TC-3 needs a backend that actually contains an AAPL row for 2026-06-22 —
  confirmed present in the real ambient store (`screen-2026-06-22-3ecd45c062c7.json`), but the QA
  pass must copy it (plus its real AAPL bar series) into a throw-away, fixture-scoped root — never
  point the browser at the operator's real `.data/` (iter-4's Top-up-pollution lesson and iter-5's
  own established recipe, extended by one seed file).
- Carried forward, not this iteration's job: the owner's written ratification of the two iter-4
  frozen-file touches (bars.py, StructureChart.tsx) — flag it again for the evaluator's active-blocker
  note; it does not block J-05.
- After this iteration, J-06 (MCP 17-tool contract) is the last piece keeping J-07 fully passing —
  plan it next, at lean depth (it is small, additive, and touches only `app/mcp/__init__.py` +
  its own test file, no frontend, no frozen-file surface).
