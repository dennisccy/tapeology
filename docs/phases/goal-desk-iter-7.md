# Goal Iteration 7 — 17-tool MCP contract, the F2 hover-honesty fix, and the closing sentinel walk

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06, J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk` BESIDE the kept two pages — the one sanctioned kept-surface edit is J-05's additive `/structure` prefill.) *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*

## GOAL

Claude (via MCP) can read the whole desk — `desk_universe` and `desk_screen` join the 15 existing
read-only tools for a 17-tool contract — the `/desk` row-hover honesty regression audit found is
repaired without touching the row's already-verified click behavior, and the era's full kept-product
regression sentinel (J-07) finally has every screenshot it has been missing since iteration 4.

## BACKGROUND

Only two journeys are not yet passing: J-06 ("17 tools", currently 15) and J-07 (partial for that one
reason alone). iter-6's evaluator explicitly framed iteration 7 as the closing run and asked for four
things together: build J-06; settle audit F2 (the whole-row drill-in link now sits on top of every
cell, so the `title` tooltips that carried full-precision `distance_bps`/`band_score` and each
timeframe's "window last requested" freshness are unreachable); take J-07's three still-missing
kept-product screenshots (sim cockpit, Case Studies drill-in, Edge Report); and fix
`journey-scripts/J-05.json` step 2, which currently picks its history row by table position instead
of by date. Per the priority rubric this is a clean **unblocker** pick (rule 3): J-06 is the single
remaining gap keeping J-07 partial, none of the four items touch the same file as another (mcp module
vs. desk page vs. a golden JSON vs. a pure browser walk), and none is individually risky (rule 5 —
J-06 is mechanical/additive, the F2 fix is deliberately chosen below to make zero change to click
geometry, J-07 needs no code at all). Coherence was `COHERENCE-PASS` last iteration, so no forced
consolidation (rule 2); nothing regressed (rule 1).

**Depth is full — trigger 1 (structural/cross-cutting).** This iteration's combined surface spans the
backend MCP registry (`app/mcp/__init__.py` + its contract test), the frontend `/desk` row-interaction
contract (`page.tsx`), a golden-script fix, and — because this is the era's closing regression pass —
a full kept-product browser walk across Cockpit + Structure + the nav + the MCP tool count, whose
combined acceptance (exactly 17 tools, exactly 3 routes, byte-identical kept routes, zero
out-of-inventory diff) is J-07's own acceptance and is not covered by any single journey's unit tests.
This is also, functionally, the last planned iteration before the era can be evaluated for
`GOAL_ACHIEVED`, so the full pipeline's extra closure/audit checks (phase-closure-auditor,
ux-regression-reviewer) matter here specifically. "Needs unit tests" is not the reason.

**F2 fix — an explicit build-time decision, logged to `assumptions.md`.** The eval framed F2 as a
choice between "whole-row link" and "per-cell hover text." A THIRD option is chosen instead, for a
concrete regression-safety reason: `journey-scripts/J-05.json` step 4 clicks the `desk-screen-row`
testid (the whole `<tr>`), and a real click resolves to whatever element is actually topmost at that
point — if the distance/score/coverage cells reclaimed pointer-event priority over the anchor (either
candidate the eval named), a click landing over those cells could silently stop navigating, which
would rebuild/break J-05's own already-verified click behavior (the binding "Do not redo" entry). The
chosen fix instead **consolidates every now-unreachable per-cell tooltip into the row's own single
drill-in anchor** (already the topmost element everywhere in the row): hovering ANYWHERE in the row
reveals one composite tooltip carrying the full-precision `distance_bps`, `band_score`, and each
coverage entry's `latest_window_end_utc` — restoring reachability with **zero change** to the anchor's
`href`, `absolute inset-0` positioning, or the row's click geometry. This does not touch the rounded,
2-decimal DISPLAY audit F3 chose for scanability — only where the full-precision detail is reachable
from.

Lessons applied (all still live risks):
- The "stretched link" lesson (iter-6): a `title` on an element the stretched anchor paints over is
  unreachable by pointer no matter how deeply nested. The fix above sidesteps this entirely by putting
  the composite detail on the anchor itself, not on any covered cell.
- The golden-write-path lesson (iter-4/iter-5): `journey-scripts/J-05.json`'s own steps stay read-only;
  the date-selector fix below only changes WHICH row step 2 clicks, not what kind of action it is.
- The screenshot-honesty lesson (iter-4/iter-5): any capture aid used for a transient state (e.g. a
  held poll reply) must be disclosed up front in the QA report; none of J-07's three missing shots are
  transient states, so no aid should be needed, but disclose one if used.
- The evidence-existence lesson (iter-4): before trusting any verdict prose, confirm
  `reports/phase-goal-desk-iter-7-ui-test-results.md` exists and the trace shows a real
  `browser-qa-agent` dispatch.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/mcp/__init__.py`: add two new no-required-argument static-path tools to
  `_STATIC_PATHS` — `desk_universe` → `/research/desk/universe`, `desk_screen` → `/research/desk/screen`
  — plus their `types.Tool(...)` registry entries, mirroring the existing `datasets`/`setups`/
  `edge_report` no-arg shape exactly. `TOOL_NAMES` grows from 15 to 17. `get_endpoint`'s allowlist
  needs no change (`/research/desk/*` is already covered by the `/research/` prefix).
- [ ] `apps/backend/tests/test_mcp_server.py`: extend `EXPECTED_TOOLS` to the 17-tool contract; add
  byte-identity coverage for `desk_universe`/`desk_screen`, each proven in BOTH the honest-empty state
  (no universe/screen ever registered) and a populated state — seed via `UniverseStore.record(...)`/
  `ScreenStore.record(...)` directly into the live test backend's data dirs, the same
  `BarStore.record()`-direct-seeding precedent already used for `bars`/`levels`/`tradability`/`setups`.
  Extend the `backend_paths` fixture with the desk stores' own env-var knobs
  (`TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_DESK_SCREEN_DIR`), mirroring the existing
  `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DATASET_DIR` pattern. Add one `get_endpoint` proxy test for
  `/research/desk/screen?date=...` (both a matching and a non-matching date) proving the allowlist
  already covers it verbatim, with zero code change.
- [ ] New source-introspection guard test (sibling of `apps/backend/tests/test_desk_ui_guards.py`):
  asserts `apps/frontend/app/desk/page.tsx`'s drill-in anchor(s) build their tooltip/title content
  from `row.distance_bps`, `row.band_score`, and each coverage entry's `latest_window_end_utc` (the F2
  fix's contract), not a static or empty string — with a seeded-violation counter-test proving the
  check can actually fail.

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`: fix audit F2 by consolidating the now-unreachable per-cell
  honesty tooltips (full-precision distance/score, per-timeframe "window last requested" freshness)
  into the existing single drill-in anchor per row (`desk-row-drill-in` / `desk-skip-row-drill-in`),
  which is already the topmost, whole-row-covering element. Zero change to the anchor's `href`,
  `absolute inset-0` class, `data-testid`, or any other row markup — the click/navigation behavior
  stays byte-identical to what J-04/J-05 already shipped and verified. Skip rows (no distance/score)
  carry only the coverage-freshness portion of the composite tooltip — never a fabricated value for a
  field that does not exist on that row.

### Test & regression assets
- [ ] `runs/goal-session-desk/journey-scripts/J-05.json`: change step 2's click target from the
  positional first-match `{"testid": "desk-history-row"}` to a date-qualified selector (e.g. a `css`
  target such as `[data-testid="desk-history-row"][data-screen-date="2026-06-22"]`, using the
  already-existing `data-screen-date` attribute on that row), so the replay selects the intended
  history entry by its recorded date, never by table position.

### New user-facing capability
None. This iteration adds a machine-readable surface (two new MCP tools) and repairs an honesty
regression on an already-shipped page; the operator-visible product (pages, nav, buttons) is
unchanged.

### New information displayed
None new to the UI. The full-precision `distance_bps`/`band_score`/coverage-freshness detail that
briefly became hover-unreachable is restored via the row's existing hover affordance (now consolidated
on the drill-in anchor). Claude, via MCP, can now read the `desk_universe`/`desk_screen` payloads
directly — the same payloads `/desk` already renders.

### New user actions
None new on `/desk`. A Claude conversation using the MCP server gains two new read-only tool calls,
`desk_universe` and `desk_screen`.

### UI surface changes
No new page, panel, or button. `/desk`'s rows keep their current visible layout; only WHICH element
carries the honesty-preserving hover tooltip changes (the row's drill-in anchor, not individual cells).

### Product surface delta
The Desk becomes fully Claude-operable (17 of 17 planned MCP tools, matching the 15 kept + 2 new).
The one open hover-honesty regression from iteration 6 is closed without touching the row's
already-verified click geometry. The era's kept surfaces (Cockpit, Structure) get the final, complete
browser-evidence pass J-07 has needed since iteration 4, so the sentinel can move to passing and the
era can be evaluated for closure.

### Blueprint conformance
MCP tools have no page (matches the Feature/journey homes table's existing "no page" row for J-06).
The F2 fix stays inside `/desk`'s existing canonical home. J-07's regression walk stays inside the
Cockpit/Structure homes. No new page, no nav-skeleton change; `blueprint.md` is updated additively
(see below) to record the MCP-proxy addition and the F2 build-time decision.

### Data-contract additions
None. `desk_universe`/`desk_screen` are byte-identical MCP proxies of the ALREADY-registered
`GET /research/desk/universe` / `GET /research/desk/screen` rows — no new computing module, no new
endpoint, no shape change. The F2 fix relocates WHERE an already-registered value's full-precision
form is exposed in the DOM (from several per-cell `title`s to one composite anchor tooltip); it adds
no new value.

## OUT OF SCOPE

- Any change to `desk_screen.py`'s CLI write-path guard, `bars.py`'s per-series `_has_finite_prices`
  filter, or the loosened `test_structure_chart_viewport.py:194` assertion — none of those files are
  opened by this iteration's work; carried per "carry, do not force."
- The owner's written ratification of the iteration-4 `bars.py`/`StructureChart.tsx` frozen-file
  exception — a human action, not a build task. Stays as an active-blocker note for the evaluator; it
  blocks nothing this iteration.
- The same-date screen ambiguity (two screens recorded on one date cannot be told apart by the
  date-only `?date=` lookup) — carried; needs an id-keyed read, not this iteration's job.
- Keyboard access for history rows, a pending-state indicator during a history click, and the
  auto-opening suggestion box — carried UX nits, not required by any journey's acceptance.
- Any new `Config` field, new Data-Contract row, or new backend route.
- A date-picker or alternate-date control on Run Screen — settled at iteration 4.
- Any edit to `StructureChart.tsx`, `PriceChart.tsx`, `bars.py`, or `app/engine/` — frozen.
- A live/real 100-symbol top-up or live universe fetch — an operator-run verification, never a
  build/test gate.
- Reducing or reshuffling the whole-row click target's geometry for any cell — explicitly rejected
  above as the regression-risk path.

## DEFINITION OF DONE

- [ ] J-06 passes: the MCP server advertises exactly 17 tools (`TOOL_NAMES`/`EXPECTED_TOOLS`),
  `desk_universe`/`desk_screen` are proven byte-identical to their curl equivalents in BOTH the
  honest-empty and populated fixture states, `get_endpoint` proxies `/research/desk/screen?date=`
  verbatim, and the full MCP suite is green — verified via the backend test suite (goal.md marks J-06
  "Keyless; automated"; no browser-qa dispatch is required for this journey specifically).
- [ ] J-07 passes via browser-qa-agent: sim cockpit Buyer Control screenshot, `/structure` Load for
  pinned AAPL as-of 2026-06-22 (the 300–302.4 wall renders) screenshot, Case Studies drill-in
  screenshot, honest Edge Report panel screenshot, kept-route byte-identity vs. the era-open baseline,
  nav = exactly 3 routes, MCP = exactly 17 tools, zero out-of-inventory diff in the cumulative era
  diff.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05 remain green (deterministic replay +
  LLM fallback) — J-04 and J-05 specifically re-verified against the F2 hover fix.
- [ ] No anti-goal violation introduced — MCP stays read-only (rail 8, nothing added can change state);
  the F2 fix changes no click/navigation geometry; copy-discipline lint stays green unmodified.
- [ ] Unit tests pass; no regressions — full backend suite stays at or above the 1341-collected /
  1333-passing / 8-skipped floor plus the new J-06 + F2 guard tests; `Config().config_fingerprint()`
  still prints `08e471b10130e1e2`.
- [ ] `runs/goal-session-desk/journey-scripts/J-05.json` step 2 selects its history row by
  `data-screen-date`, never by table position.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-7-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (sim cockpit Buyer Control, `/structure` Load + Case Studies + Edge Report, kept-route
  byte-identity, nav-route count, MCP tool count); regression replay/LLM fallback for J-01–J-05,
  including a fresh capture proving the F2 fix's composite tooltip and the row's unchanged click
  behavior. J-06 is keyless/automated per goal.md — no browser dispatch is required for J-06
  specifically, but the extended MCP suite must run.
- Unit/integration: extended `test_mcp_server.py` (17-tool contract; byte-identity for the two new
  tools in both fixture states; `get_endpoint` proxy of `/research/desk/screen?date=`); the new F2
  guard test with its seeded-violation counter-test; existing `test_desk_ui_guards.py`,
  `test_copy_discipline.py`, the chart-guard suites, and the 13 fingerprint-pin assertions all stay
  green unmodified.
- Error cases: an MCP `get_endpoint` call to `/research/desk/screen?date=<a-date-with-no-match>`
  returns the honest `{"screen": null}` body verbatim (never a fabricated row, never an error); an MCP
  call to `desk_universe`/`desk_screen` before ANY universe/screen exists returns the honest-empty 200
  body, never a 404.

Test-first contract:

- TC-1: given a fixture-scoped backend with no universe ever registered, when MCP
  `call_tool("desk_universe", {})` runs, then `content[0].text` is byte-identical to
  `curl GET /research/desk/universe`'s honest-empty body
  `{"snapshots": [], "latest": null, "integrity_errors": []}`.
- TC-2: given the committed fixture universe snapshot registered on that same backend, when MCP
  `call_tool("desk_universe", {})` runs again, then `content[0].text` is byte-identical to
  `curl GET /research/desk/universe`'s populated body (103 members, the fixture's checksum).
- TC-3: given no screen ever computed, when MCP `call_tool("desk_screen", {})` runs, then
  `content[0].text` equals `{"screens": [], "latest": null, "integrity_errors": []}`, byte-identical
  to curl.
- TC-4: given a recorded screen snapshot on that backend, when MCP `call_tool("desk_screen", {})` runs,
  then `content[0].text` is byte-identical to `curl GET /research/desk/screen`'s populated body (the
  `screens` meta-only list plus the full `latest` snapshot).
- TC-5: given `app.mcp.list_tools()`, when called, then it returns exactly 17 tools whose names equal
  the updated `EXPECTED_TOOLS` tuple, including `desk_universe` and `desk_screen` alongside the 15
  existing names.
- TC-6: given the fixture-scoped backend, when MCP
  `call_tool("get_endpoint", {"path": "/research/desk/screen?date=2026-06-22"})` runs on a backend
  holding a screen recorded for that date, then `content[0].text` is byte-identical to
  `curl "GET /research/desk/screen?date=2026-06-22"`.
- TC-7: given the same tool call with a non-matching date, then `content[0].text` equals the honest
  `{"screen": null}` body and `isError` is false (a valid 200, never surfaced as an error).
- TC-8: given a rendered `/desk` ranked row (e.g. AAPL, `distance_bps 0.33523150389608725`, a
  `band_score`, and coverage entries with real `latest_window_end_utc` values), when the pointer
  hovers anywhere within that row (its single drill-in anchor), then the anchor's tooltip text
  contains the row's full unrounded `distance_bps`, full `band_score`, and each populated timeframe's
  exact freshness value.
- TC-9: given the same fix, when the row's markup is inspected, then the drill-in anchor's `href`,
  `absolute inset-0` class, and `data-testid` are byte-unchanged from iteration 6's shipped shape, and
  clicking anywhere in the row still navigates to `/structure?symbol=<sym>&asof=<iso>` exactly as J-05
  already verified.
- TC-10: given a skipped-member row (no distance/score, only coverage), when hovered, then the
  anchor's tooltip honestly includes only the coverage-freshness fields that exist for that row — no
  fabricated distance or score value.
- TC-11: given the new guard test, when it scans `apps/frontend/app/desk/page.tsx`, then it confirms
  the drill-in anchor's tooltip is built from `row.distance_bps`/`row.band_score`/coverage
  `latest_window_end_utc` fields, and a seeded-violation counter-test proves the check fails if a
  future edit strips that composition.
- TC-12: given `runs/goal-session-desk/journey-scripts/J-05.json` after the fix, when step 2 is
  inspected, then its target selects the row whose `data-screen-date="2026-06-22"` rather than the
  first `desk-history-row` match, and replaying the script against a freshly-seeded backend still
  reaches the expected "Viewing the recorded screen for 2026-06-22" text.
- TC-13: given the real browser, when SIM-BUYER is watched on the Cockpit, then the "Buyer Control"
  panel settles and is screenshotted.
- TC-14: given `/structure` Load for pinned AAPL as-of 2026-06-22, when Case Studies is opened, then
  its drill-in view renders and is screenshotted.
- TC-15: given `/structure`'s Edge Report panel, when viewed, then its honest computed-or-not-computed
  state renders (no fabricated cell) and is screenshotted.
- TC-16: given the era-open baseline capture of kept routes (`/`, `/structure`, `/meta/ui-routes`,
  `/research/taxonomy`), when re-curled this iteration, then every response is byte-identical to the
  baseline.
- TC-17: given the full backend suite, when run, then it reports 0 failures at or above the
  1341-collected / 1333-passing / 8-skipped floor, and `Config().config_fingerprint()` prints
  `08e471b10130e1e2`.
- TC-18: given J-01–J-05's already-recorded acceptance states, when re-verified this iteration
  (deterministic replay or LLM fallback), then each still renders the same acceptance state on record
  (no regression).

## NOTES

- Assumption logged to `runs/goal-session-desk/state/assumptions.md`: audit F2's own framing offered
  two candidate fixes ("whole-row link" or "per-cell hover text"); this spec picks neither, choosing a
  third — consolidating the lost tooltips onto the row's existing drill-in anchor — specifically to
  avoid the regression risk either named option carries against `journey-scripts/J-05.json` step 4's
  already-passing click on the `desk-screen-row` testid. Reversible.
- `test_mcp_server.py`'s `backend_paths` fixture needs the two new desk-store env-var knobs
  (`TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_DESK_SCREEN_DIR`) added, mirroring the existing
  `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DATASET_DIR` precedent, so the new tools' tests seed via
  `UniverseStore.record(...)`/`ScreenStore.record(...)` directly rather than touching the ambient
  store.
- Before any browser-QA dispatch: `rm -rf apps/frontend/.next` + rebuild both processes (T-9), and
  warm `/research/setups` + `/structure` Load once on the fixture-scoped rig before timing anything
  (iter-0/iter-1 lessons — the first real call on a cold cache can take minutes).
- Carry forward, not this iteration's job: the owner's written ratification of the iteration-4
  frozen-file touches (`bars.py`, `StructureChart.tsx`); the same-date screen ambiguity; keyboard
  access for history rows; the three one-line hardening items from earlier iterations (CLI
  write-path guard, per-series price-less-row filter, chart-guard-test re-tightening) — none of their
  files are opened this iteration.
- If J-06 and J-07 both land clean this iteration, all 7 journeys are passing and the next dispatch
  should be the evaluator's own `GOAL_ACHIEVED` assessment, not a manufactured 8th journey.
