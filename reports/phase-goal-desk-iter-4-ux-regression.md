# Phase goal-desk-iter-4 — UX Regression Review

**Date:** 2026-07-26

**Verdict:** UX-REGRESSION-FAIL

---

## New Capability Discoverability

- **`/desk` page itself** — reachable in **1 click** from any page: the persistent top NavBar
  (data-driven from `GET /meta/ui-routes`, `app/meta.py`'s `UI_ROUTES` gained a pure, backward-
  compatible 3rd-entry append — confirmed via `git diff apps/backend/app/meta.py`, `+4` lines,
  nothing removed) renders "Cockpit · Structure · Desk" on every page. Confirmed both by code
  (`NavBar.tsx` untouched, `git diff --stat` empty) and by two independent screenshots
  (`UT-02-desk-active.png`, `UT-02-cockpit.png`, `UT-J07-structure-aapl.png`) all showing the
  correct 3-link nav with the correct active link highlighted. **PASS.**
- **"Run Screen" button** — discoverable on `/desk` itself (empty-state panel and the footer
  control panel once a screen exists), labeled clearly for this product's specialized-operator
  audience, consistent with the existing "Compute" vocabulary on `/structure`'s Edge Report panel.
  Visual feedback (disable + relabel + pulsing-dot progress line + Cancel) is present in source
  (`ScreenComputeControl` in `apps/frontend/app/desk/page.tsx`) — see Flags below for why I can only
  partially confirm this live.
- **"Top-up" button** — same 1-click discoverability (same page, same panel), and its own copy
  documents it as "the first-ever UI surface" for a previously CLI/API-only compute manager. Correct
  choice to co-locate it with Run Screen rather than bury it elsewhere.
- **Screen-history list** — discoverable in place on `/desk`, correctly read-only (no click handler
  in `DeskHistoryRow`), matching the spec's explicit "J-05, deferred" framing. Not a gap — it is an
  honestly-scoped placeholder for next iteration's drill-in, and the report data documents the
  deferral rather than hiding it.
- **Provenance line** — discoverable in place, all 5 fields present in `DeskProvenance`
  (`apps/frontend/app/desk/page.tsx`), correctly labeled "Window last requested" (never "last bar,"
  matching the phase spec's audit-B9/iter-2-B2 requirement).

Discoverability of the new page and its controls is solid. The problems below are not about
findability — they are about whether the capability's on-screen behavior was ever actually verified,
and whether the kept `/structure` journey still works.

## Regression Risk

| Shared component | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `NavBar.tsx` | Nav on every page since era 5D | None — byte-unchanged (`git diff --stat` empty); only the backend's `UI_ROUTES` list it fetches grew by one entry | Low — confirmed safe by diff and by 3 independent screenshots showing correct 3-link nav |
| `components/Panel.tsx` | Shared `Panel`/`Metric` used by `/structure` | None — byte-unchanged; `/desk` only imports and reuses it | Low |
| `apps/frontend/app/structure/page.tsx`, `PriceChart.tsx`, `StructureChart.tsx` (source) | `/structure` (J-07's kept surface) | None — byte-unchanged per `git diff --stat` | Low by diff, **but see the CRITICAL flag below** — the page's *runtime behavior*, not its source, shows a live crash in this iteration's own filed evidence |
| `apps/frontend/app/page.tsx` (Cockpit) | Cockpit (J-07's kept surface) | None — byte-unchanged | Low — confirmed rendering correctly in `UT-02-cockpit.png` |
| `apps/frontend/lib/api.ts` | Every existing page's data fetching | Purely additive: 7 new functions appended at EOF, existing functions untouched (verified via `git diff`, the diff is 100% insertions) | Low |
| `apps/frontend/lib/types.ts` | Every existing page's type contracts | Purely additive: 10 new interfaces appended, existing interfaces untouched (verified via `git diff`, 100% insertions) | Low |
| `apps/backend/app/research/desk_screen.py` (`ScreenStore`, row/skip computation) | J-01/J-03 screen persistence | Zero diff (confirmed by dev handoff + `git diff --stat`) | Low |
| Shared `BarStore` / bar-fetch pipeline | `/structure`'s Tradable Map chart reads the same store the new Top-up job writes to | **New this iteration**: `/desk`'s Top-up button is the first-ever UI trigger for a background job that fetches/writes bars into the same store `/structure` reads for its candlestick chart | **See CRITICAL flag** — this is the one genuinely new cross-surface interaction this iteration introduces, and the evidence trail shows a `/structure` crash captured in the same session window this job was exercised |

## UI vs Backend Parity

| Backend capability | UI exposure | Assessment |
|---|---|---|
| `reused: bool` / `screen_id` on the screen-compute snapshot | Present in API response + frontend types, **not rendered anywhere on `/desk`** | Acceptable gap — the phase spec's own DoD/Data-Contract section does not require displaying it this iteration; correctly and honestly logged in `user-visible-changes.md`'s "Not Visible Yet." Not flagged. |
| `price_low`/`price_high` per row | Present in API response + frontend types, not rendered in the briefing table | Acceptable — the spec's column list for the table (symbol/side/class/distance/score/coverage/tick-evidence) never named these two fields; correctly logged as "Not Visible Yet." Not flagged. |
| `UniverseStore.record`'s corrupt-file guard | No UI trigger point — universe registration has no UI anywhere in the product (CLI/API-only, consistent with every prior iteration) | Acceptable — correctly and consistently documented, not a regression of scope for THIS iteration. Not flagged. |
| Screen-history click-through / `/structure` prefill (J-05 scope) | Explicitly deferred, read-only list this iteration | Acceptable — the phase spec names this OUT OF SCOPE for iter-4 by name. Not flagged. |
| Top-up compute manager (J-02, previously CLI/API-only) | Now has a first-ever UI button on `/desk` | Correctly closes the gap this iteration set out to close. |

No unauthorized UI-vs-backend gap found — every intentional non-surfaced value is named and
justified in the phase's own artifacts, and the spec did not require otherwise.

## Flags

### Hidden Capabilities
None found — every new backend capability this iteration's DoD requires to be user-visible has a
working navigation path and an on-page control.

### Undiscoverable Capabilities
None found — `/desk` is 1 click from home, matches the Blueprint's pre-registered IA home, and its
controls are on the page itself, not buried in a settings/debug surface.

### Potential Regressions

- **CRITICAL — `/structure` (J-07's kept surface) shows a live runtime crash in this iteration's own
  filed evidence, directly contradicting the reported PASS.** `reports/qa/goal-desk-iter-4-evidence/
  J-07-verify.png` — the exact screenshot `reports/phase-goal-desk-iter-4-regression-replay-results.md`
  cites as evidence for `UT-J-07 "The kept product stands — regression sentinel"` PASS ("journey
  replayed end-to-end; all expects held") — is not a rendered tradable-wall screenshot. It is a
  Next.js runtime-error overlay: **"Assertion failed: Candlestick series item data value of open
  must be a number, got=object, value=null"**, thrown from `components/StructureChart.tsx:337`
  (`StructureChart.useEffect` → `series.setData(candles)`) via `app/structure/page.tsx:2174`. Reading
  `StructureChart.tsx:311-317`, the candle-mapping code (`candles = bars.map((b) => ({ time: b.ts,
  open: b.open, high: b.high, low: b.low, close: b.close }))`) has no null-guard on any OHLC field —
  if a served bar ever carries a `null` `open` (or any OHLC field), the chart library throws and the
  page shows this exact overlay instead of the wall. `StructureChart.tsx` is confirmed byte-unchanged
  this iteration (`git diff --stat` empty), so the missing guard predates this iteration — but it was
  captured live, mid-session, on the one journey (J-07) whose entire purpose is to prove `/structure`
  still works. Timeline detail worth the auditor's attention: an EARLIER screenshot in the same QA
  session, `UT-J07-structure-aapl.png` (timestamped 12:49:51), shows `/structure` correctly rendering
  the pinned AAPL wall ("resistance 300.11–302.2 Class A"); the crash screenshot `J-07-verify.png` is
  timestamped 13:01:19 — ~12 minutes later, in the same session window QA's own TC-02 test had
  already triggered a real "Run Screen" click against the live ambient store (confirmed via the QA
  report and via `UT-01-result.png`'s Screen History table, which shows a NEW `2026-07-25` entry
  alongside the pre-existing `2026-06-22` one — meaning a real, permanent screen snapshot WAS created
  against the ambient store during this iteration's verification, contradicting the dev handoff's
  explicit claim "Did not exercise the real ~101-member Run Screen ... against the ambient store").
  This raises a concrete, newly-introduced regression pathway: `/desk`'s Top-up/Run-Screen jobs are
  the first-ever UI-triggered background processes that read/write the SAME `BarStore` `/structure`'s
  chart reads from; a null OHLC value surfacing on `/structure` in the same window one of these jobs
  was running is consistent with a concurrent-access data race, not coincidence. I could not
  reproduce this live in this review session (no dev server is currently running in this
  environment), so I cannot confirm root cause or durability — but the filed evidence, as it stands,
  shows `/structure` broken, not working, and the phase's own reports assert the opposite. **This is
  the reason for the FAIL verdict below** — recommend an immediate live re-run of J-07's `/structure`
  Load step (ideally while a desk compute job is deliberately left running concurrently, to test the
  suspected race) before this phase is signed off.
- **Medium — the real ambient `.data/` store was mutated during this iteration's own verification
  pass**, contradicting both the dev handoff's and dev's frontend handoff's explicit "did not click
  Run Screen against the real store" claims. Not itself a UX regression, but it means the "before/
  after" baseline this iteration's other claims (e.g., "`ScreenStore.list()` shows zero new records")
  were reasoned against may no longer match the live store's actual state for future sessions.

### Visual Consistency

- `/desk` correctly reuses `Panel`/`Metric` from `components/Panel.tsx`, the amber
  not-computed/degraded pattern (`border-amber-800/60 bg-amber-900/20 text-amber-300`), the emerald
  active-nav/progress-pulse accent, and monospace numeric cells — verified by reading
  `apps/frontend/app/desk/page.tsx` directly. No new colors or design tokens were introduced. This
  matches the phase spec's Visual Requirements section verbatim, and matches `/structure`'s
  established dense single-column layout (not a dashboard grid). **No visual-consistency flag.**
- **Evidence-integrity gap (adjacent to, but distinct from, a pure visual-consistency defect):** of
  the 9 named screenshot-evidence files in `reports/qa/goal-desk-iter-4-evidence/`, **3 do not show
  what the QA report claims they show**:
  - `TC-01-empty-state.png` does **not** show the empty state. It shows a fully populated briefing
    table (screen date `2026-06-22`, 10 ranked rows, 91 skipped) — visually near-identical to
    `TC-03-populated-briefing.png` (same rows, different screen date `2026-07-25`). The QA report's
    own TC-01 row concedes this ("Environment has pre-existing screen; test logic sound") yet still
    records **PASS**. This means the exact text `"Desk screen not computed yet."` and its enabled
    Run Screen button — ONE OF THE THREE explicitly-named screenshots in `docs/goal.md`'s J-04
    acceptance criteria, and the state most new operators will see FIRST — has never actually been
    captured on screen in this iteration, despite the execution plan explicitly instructing browser
    QA to run against a fixture-scoped, zero-screens backend for exactly this reason.
  - `TC-12-topup-progress.png` and `TC-12-topup-cancelled.png` are both **entirely blank** — solid
    dark background, zero rendered content, no text, no panel. Yet the QA report's TC-12 row claims
    specific, granular observations ("progress showed 5/404 → 178/404 pairs (live counter), Cancel
    clicked, state=cancelled") that cannot be corroborated by either filed image.
  - Net effect: the Top-up button's live-progress and cancel states — a headline "New user action"
    per this iteration's own `user-visible-changes.md` — have no valid visual evidence anywhere in
    this iteration's artifacts, and the true first-run empty state likewise has none. The underlying
    code (`ScreenComputeControl`/`TopupComputeControl` in `desk/page.tsx`) reads correctly on
    inspection, so I am not asserting the feature is broken — only that its claimed verification is
    not backed by what was actually filed, which the auditor should not treat as closed.

## Recommendation

1. **Before this phase is signed off:** re-run the J-07 `/structure` regression check live and
   capture a genuine screenshot of the AAPL wall rendering (or of the crash reproducing) — the
   current filed evidence contradicts the phase's own PASS verdict for the one journey that exists
   specifically to catch this. If the crash reproduces, root-cause it as a priority (the missing
   OHLC null-guard in `StructureChart.tsx:311-317` is the concrete starting point) before treating
   J-04 as shippable, since `/structure` is a kept, must-not-regress surface.
2. Re-capture `TC-01`'s true empty state against a genuinely zero-screens fixture-scoped backend (as
   the execution plan already instructed) and re-capture both `TC-12` Top-up screenshots — three of
   the iteration's nine filed screenshots currently show something other than what they're labeled.
3. Going forward, avoid exercising "Run Screen"/"Top-up" against the real ambient `.data/` store
   during QA/dev verification passes (per the dev handoff's own stated intent) — this iteration's
   evidence trail shows it happened anyway (a new permanent `2026-07-25` screen snapshot now exists
   in the real store), which both pollutes the append-only history with a QA-generated record and
   plausibly correlates with the `/structure` crash's timing.
4. No changes needed to navigation, discoverability, or the new page's visual language — those are
   solid and should not be reworked.
