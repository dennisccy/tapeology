# goal-desk-iter-6 Audit Report

**Date:** 2026-07-26
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-05 is genuinely shipped: `/desk`'s history rows fetch-and-swap a past snapshot verbatim (one GET,
no POST, no recompute), every ranked and skipped row drills into `/structure?symbol=&asof=` with the
displayed snapshot's own `as_of`, and `/structure` prefills + auto-loads through the SAME `handleLoad`
the manual Load button uses while staying byte-unchanged with absent or partial params — all of it
verified live by me in a fixture-scoped browser run, not taken from the handoffs. Two real defects the
whole pipeline missed were found by hit-testing and state-probing the running page: the "not the
latest" banner asserted something false whenever the operator selected the newest screen's own history
row (**fixed and re-verified in this audit**), and the new stretched drill-in anchor now shadows every
`title` tooltip on both row tables — silently disabling iter-4's own audit fix that kept the 2-decimal
rounding honest (**documented, not fixed: every available fix changes the row click/hover contract
this iteration's browser QA and two goldens verified, so it needs an owner design call plus a fresh
browser pass, not a surgical patch**).

---

## 2. Findings

### Backend Findings

No backend product code changed this iteration, and none needed to: `GET /research/desk/screen?date=`
(`apps/backend/app/research/desk_routes.py:248-266`) serves `matching[-1]` from a plain
`store.list()` filter — a pure read with no write side effect, already covered by
`tests/test_desk_screen_compute.py:518` (honest null) and `:627` (verbatim dated snapshot). I
confirmed this live against a fixture-scoped instance: `GET /research/desk/screen?date=2026-07-25`
returned the persisted record verbatim, and the ambient store's two files were byte-identical (md5)
before and after my whole pass.

**B1 — GAP (not fixed): a same-date re-run makes the history click ambiguous, and `?date=` cannot
disambiguate it.**
`apps/backend/app/research/desk_screen.py` (record: `screen_id = f"screen-{screen_date}-{checksum}"`
over the 5-pin key) permits two snapshots with the SAME `screen_date` and different ids — a top-up
changes `bar_store_signature`, so re-running the screen the same day records a second file. The
history list then shows two rows with identical dates, while the new click path
(`apps/frontend/app/desk/page.tsx:928-941` → `fetchDeskScreenByDate`) can only ask by DATE, so the
route returns the LAST recording for that date whichever row was clicked, and `selectedDate`
(matched on `screen_date`, `page.tsx:430`) highlights both rows at once. Nothing false is displayed
(the Provenance panel always shows the displayed snapshot's own pins), but the operator can click row
A and be shown row B's content. This is inherited from the contract the spec mandated (there is no
id-keyed read); resolving it needs a `?id=` read on the backend — correctly out of iter-6 scope.

### Frontend Findings

**F1 — IMPORTANT (fixed): the "not the latest" banner stated something false whenever the newest
screen's own history row was selected.**
`apps/frontend/app/desk/page.tsx:978` derived `isViewingLatest = viewingSnapshot === null` — i.e.
"nothing was clicked", not "what is on screen is the newest record". The newest screen IS a row in
the history list (`GET /research/desk/screen` returns `screens` = every meta, oldest-first, and
`latest` = `records[-1]`), so clicking it displayed exactly `latest` under the banner
`Viewing the recorded screen for 2026-07-25 — not the latest.` plus a "Latest" button that could only
undo a state the page was not in. Verified live before the fix (fixture-scoped backend on `:8399`,
frontend `:3399`, real copies of both recorded snapshots):

```
B_after_clicking_latest_row (pre-fix)
  indicator: 'Viewing the recorded screen for 2026-07-25 — not the latest. Latest'
  first_briefing_symbol: TSLA        # == the latest screen's own first row
  history_rows: [06-22:false, 07-25:true]
```

**Fix applied** (`page.tsx:973-984`) — compare the displayed snapshot's id with `latest`'s:
`const isViewingLatest = viewingSnapshot === null || viewingSnapshot.id === latest?.id;`

**Post-fix verification** (same rig, same script, both directions plus the TC-2 control):

```
load        indicator: null                first: TSLA   selected: [06-22:false, 07-25:false]
after 0622  indicator: 'Viewing the recorded screen for 2026-06-22 — not the latest. Latest'
                                           first: AAPL   selected: [06-22:true,  07-25:false]
after Latest indicator: null               first: TSLA   selected: [06-22:false, 07-25:false]
after 0725  indicator: null                first: TSLA   selected: [06-22:false, 07-25:true]
row-centre click on the AAPL row -> /structure?symbol=AAPL&asof=2026-06-22T23%3A59%3A59Z
```

TC-1 (past snapshot rendered), TC-2 ("Latest" reverts), TC-3 (row drill-in) all still behave as the
browser QA recorded them; `npx tsc --noEmit` exit 0; `tests/test_desk_ui_guards.py` +
`tests/test_copy_discipline.py` = 35 tests, 0 failures after the change. The dev handoff's own wording
("whenever a history row (not `latest`) is on screen") describes the FIXED behaviour, so no handoff
claim needed correcting.

**F2 — IMPORTANT (gap, not fixed): the stretched drill-in anchor shadows every `title` tooltip on the
ranked and skipped rows.**
`page.tsx:198-213` / `:288-300` put `<Link className="absolute inset-0">` inside the first `<td>` of a
`position: relative` `<tr>`. That anchor is a positioned element, so it paints and hit-tests above all
in-flow cell content. Hit-tested live at each element's own centre with `document.elementFromPoint`:

| element (ranked row) | its own `title` | topmost element at its centre |
|---|---|---|
| `desk-row-distance` | `0.33523150389608725` | `<a data-testid="desk-row-drill-in">` |
| `desk-row-score` | `97` | `<a data-testid="desk-row-drill-in">` |
| `desk-coverage-badge` | `window last requested: 2026-07-23` | `<a data-testid="desk-row-drill-in">` |
| `desk-skip-row` badge | `window last requested: never` | `<a data-testid="desk-skip-row-drill-in">` |

The anchor carries no `title`, so none of those tooltips can be shown any more. This silently disables
two shipped affordances: iter-4's audit fix F3 (the cell displays `0.34 bps` and the comment at
`page.tsx:181-183` promises "each cell's `title` carries the served value in full, so nothing is lost,
only formatted" — that full value is now unreachable by hover) and iter-2's per-timeframe
"window last requested" badge tooltips. No number displayed is wrong and the exact values remain in
the DOM and in the endpoint payload, so this is an affordance regression, not a data defect — I
weighed GAP vs IMPORTANT and chose IMPORTANT because it quietly undoes a previous audit's honesty fix.

Not fixed in-audit deliberately. Every candidate changes the contract this iteration's own evidence
pinned: (a) raising the tooltip cells (`relative z-10`) restores hover but makes them non-navigating,
and the row's centre point falls in the distance column — that is exactly what `J-05.json` step 4 and
demo step 5 click, so both goldens would break; (b) `pointer-events: none` on the anchor plus a
row-level `onClick`/`router.push` restores everything but replaces the reviewed stretched-link pattern
(and silently drops ctrl/middle-click-anywhere-to-open-in-a-new-tab) — a design call plus a fresh
browser pass, not a surgical patch. Recommended for iter-7 with a hit-test assertion in the guard
suite.

**F3 — GAP: arriving via a drill-in link auto-opens the symbol-suggestions dropdown.**
`components/SymbolSearch.tsx:44-68` keys its debounced lookup on `value` and ends with
`setOpen(true)`, so the prefill's programmatic `setSymbolInput` (`structure/page.tsx:1710`) makes the
page open a listbox nobody asked for and issue an unrequested `GET /symbols/search?q=AAPL`. Verified
live: `{"symbol_value":"AAPL","aria_expanded":"true","listbox_open":true,"activeElement":"BODY"}` — and
it is visible in QA's own accepted evidence (`UT-05-result.png`, the dropdown covering the top of the
Tradable-Map panel). Self-clearing on the first outside click; the fix belongs in the shared
`SymbolSearch` (out of this iteration's scope).

**F4 — GAP: the history click-through is mouse-only.**
`DeskHistoryRow` (`page.tsx:379-397`) is a `<tr onClick>` with `cursor-pointer` and no `tabIndex`,
`role`, or key handler, so a keyboard user cannot select a past screen. The drill-in path is
unaffected (real `next/link` anchors, focusable, Enter works).

**F5 — OBSERVATION: no pending state on a history click.** `handleSelectHistoryScreen` awaits the GET
with no spinner or row-disabled state; against a slow backend the click looks inert until the swap
lands. Honest, just unfeedbacked.

**F6 — OBSERVATION: stale "deferred" comments.** `lib/types.ts:835` ("no click-through (J-05 scope,
deferred)") and `lib/api.ts:921` ("the `?date=` variant is J-05 scope, deferred") now describe
behaviour that shipped this iteration.

**F7 — OBSERVATION: the `Suspense fallback={null}` wrapper is inert here, but only because this
project never serves a production build.** With `useSearchParams()` inside a `Suspense` boundary, a
statically prerendered `/structure` would ship an empty shell. Both launchers (`scripts/dev.sh`,
`scripts/start-frontend.sh`) run `next dev`, and I confirmed the served HTML still contains the page
shell in that mode: `data-testid="structure-title"` and `data-testid="tradable-map-idle"` are present
in `curl`ed `/structure` output with and without query params. Worth remembering before anyone ever
runs `next build && next start`.

### Test Findings

**T1 — GAP: `J-05.json` is a brand-new golden that has never been executed, and it selects its history
row by ordinal.** Neither `phase-goal-desk-iter-6-ui-test-results.md` nor
`phase-goal-desk-iter-6-regression-replay-results.md` contains a UT-J-05 row — the replay lane ran
J-04 and J-07 only, and J-05 was proven by the LLM browser pass instead. Step 2 clicks
`{"testid": "desk-history-row"}` (the first match) and asserts the 2026-06-22 banner; that holds only
because the backend sorts `screens` oldest-first and the fixture root's oldest screen is 2026-06-22.
The demo script pins the same row properly (`[data-testid="desk-history-row"][data-screen-date="2026-06-22"]`).
Given this era's own crux lesson (a golden replayed unfixed cost iterations twice), iter-7 should
replay J-05.json once and pin that selector by date.

**T2 — OBSERVATION: one mis-attributed evidence line in the QA report.** UT-J-03 credits the rank-order
check to the 2026-06-22 snapshot with distances `0.00, 0.00, 0.30, 0.31, 0.73, 1.62, 78.37, 95.54,
144.94, 148.08`; those are the 2026-07-25 snapshot's values (06-22's are
`0.34, 0.41, 0.47, 1.30, 3.23, 7.24, 20.56, 41.75, 70.65, 0.00`). The rank-order claim itself holds for
both snapshots — only the attribution is wrong.

**T3 — OBSERVATION: `runs/goal-desk-iter-6/status.json` still says `"browser_checks_run": false`** even
though the browser lane produced 15 LLM results plus 2 replays. Bookkeeping only.

**T4 — GAP (accepted trade-off): no golden exercises the Run Screen write path any more.** TC-7's fix
was the right call, but J-04's replay now only asserts rendered state, and UT-11 deliberately did not
click the button, so UI-level coverage of the compute trigger rests on earlier iterations' evidence
plus the backend's own `test_desk_screen_compute.py` suite. I verified the whole golden lane is now
write-free: the only clicks left across all journey scripts are `desk-history-row`, `desk-screen-row`,
`structure-load-button`, and the `/`-page Simulated/Watch toggles.

Guard-test quality (TC-5/TC-6) is honest: `tests/test_desk_ui_guards.py` reads both `.tsx` sources as
text, asserts the forbidden-reference and `handleLoad(`-inside-the-marker-block conditions, and each
guard carries a seeded counter-test proving the detection actually fires. Its `_FORBIDDEN_PREFILL_CALLS`
list is a substring list, not a parser, so a future prefill could evade it with a differently named
helper — acceptable for a source lint of a 14-line block.

---

## 3. Domain Assessment

The domain claim this iteration had to protect — *a past screen is re-read, never recomputed* — holds
under inspection, not just under the lint. `handleSelectHistoryScreen` calls exactly one GET, the
render path (`DeskPopulatedScreen`) formats `snapshot.rows`/`skipped`/provenance verbatim, and my live
probe reproduced the recorded 2026-06-22 payload field-for-field on screen (AAPL, Class A, `0.34 bps`
with the exact `0.33523150389608725` in the cell's `title`, 298.02–300.1001, 91 skipped). `latest ===
null` remains the single empty-state discriminator, so history state can never fabricate a populated
page. The drill-in composes the snapshot-level `as_of` (never a per-row field), which is what makes the
`/structure` landing state pinned and reproducible; the prefill publishes `loadedQuery` through the
existing `handleLoad` and therefore inherits the page's own no-lookahead read path unchanged — it
issues no POST and triggers no compute, so the "explicit operator act" rail holds (the navigation
itself IS the operator's click). Independently re-verified: full backend suite 1341 tests / 0 failures
/ 0 errors / 8 skipped (1333 passed, floor 1328) and `Config().config_fingerprint()` →
`08e471b10130e1e2`.

Where the domain is weakest is not computation but identity: a screen is addressed by DATE in the one
new read path while the store keys snapshots by a 5-pin checksum (B1). Everything on screen stays
honest because provenance travels with the payload, but "the recorded screen for 2026-06-22" is not a
unique object, and the UI currently talks as if it were.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/desk/page.tsx` | `isViewingLatest` now compares the displayed snapshot's `id` with `latest`'s instead of testing "was anything clicked", so selecting the newest screen's own history row no longer renders the false `— not the latest.` banner (+ its inert "Latest" button). Verified live in both directions on a fixture-scoped rig; `tsc --noEmit` clean; guard + copy-discipline suites green (35/0). |

No other file was touched. The operator's `apps/backend/.data/` was byte-identical (md5 on both screen
snapshots) before and after this audit's browser run, which used a throw-away root under
`/var/tmp/iad.goal-desk-iter-6.822370/audit-fixture` and ports `:8399`/`:3399`; both processes were
killed and both ports confirmed free afterwards.

---

## 5. Recommended Next Step

Proceed to J-06 (MCP contract v3) at lean depth as iter-5/iter-6 both recommend — J-05 is done and
nothing here blocks it. Carry into iter-7, in priority order: (1) decide F2's interaction contract
(full-row link vs. per-cell tooltips) and implement it with a hit-test assertion so it cannot regress
silently again; (2) replay `J-05.json` once and pin its history-row selector by `data-screen-date`
(T1); (3) if a same-date re-run is expected in practice, add an id-keyed screen read and address the
row for what it is (B1). F3–F7 are one-line hygiene items to fold into whichever iteration next opens
those files. Still outstanding from iter-4 and unaffected by this iteration: the owner's written
ratification of the two frozen-file exceptions (`bars.py`, `StructureChart.tsx`).
