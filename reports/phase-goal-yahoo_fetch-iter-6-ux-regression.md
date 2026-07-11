# Phase goal-yahoo_fetch-iter-6 — UX Regression Review

**Date:** 2026-07-11

**Verdict:** UX-REGRESSION-PASS

## Context

This iteration is a **closure/evidence-remediation pass with zero product source change** — not a
feature iteration. Independently confirmed before forming any judgment below:

- `git diff --stat HEAD -- apps/` and `git diff --stat -- apps/` both return **empty output** (checked
  directly, not merely taken from the dev handoff's claim).
- `git log --oneline` shows the working tree's only uncommitted files are this iteration's own
  report/handoff/evidence artifacts (`docs/handoffs/goal-yahoo_fetch-iter-6-dev.md`,
  `reports/phase-goal-yahoo_fetch-iter-6-*`, `reports/qa/goal-yahoo_fetch-iter-6-*`) — no `apps/` file
  appears in `git status --short`.
- `reports/phase-goal-yahoo_fetch-iter-6-user-visible-changes.md` and
  `-ui-surface-map.md` (ui-impact-analyst) both independently confirm zero UI surfaces changed.
- `docs/handoffs/goal-yahoo_fetch-iter-6-dev.md` confirms the full backend suite (1207/0/0/6-skipped,
  exact match to iter-5), engine equivalence (22/22), and config fingerprint (`4d665603569b9dbf`,
  unchanged).

Because there is no new capability, no new UI surface, and no touched shared component this
iteration, the three review axes below are correspondingly narrow: this iteration's entire UX-relevant
job was to close two **evidence gaps** flagged by iter-5's own UX regression review (badge occlusion,
missing TC-11 capture), and I assess specifically whether it did.

## New Capability Discoverability

No new capability was added this iteration (confirmed above). The underlying capability — the
"Fetch from Yahoo Finance" control on `/structure`, 1 click from the top nav, unchanged since iter-5 —
was already assessed clean (PASS) in `reports/phase-goal-yahoo_fetch-iter-5-ux-regression.md`'s
discoverability table, and nothing in this iteration's diff (there is none) could have altered that.
Re-confirmed via this iteration's own browser evidence: UT-01 (`reports/phase-goal-yahoo_fetch-iter-6-ui-test-results.md`)
shows `/structure` loading cleanly with the fetch panel, framing copy, and Load form all visible with
no navigation change.

| Capability | Navigation path | Clicks from home | Status this iteration |
|---|---|---|---|
| "Fetch from Yahoo Finance" control | Top nav → Structure (`/structure`) | 1 | Unchanged, re-verified (UT-01, UT-02) |
| "Yahoo Finance" provenance badge | Renders inline on fetch/load success | 0 (same page) | Unchanged; **evidence gap now closed** — see Flags |
| Honest empty state (no stored bars) | Renders inline via the Load form | 0 (same page) | Unchanged; **evidence gap now closed** — see Flags |

## Regression Risk

Per the ui-regression-scout method: collect this iteration's changed components (empty set, confirmed
above) and intersect with prior-phase components. **The intersection is empty by construction** —
nothing was touched, so no shared component carries new regression risk from this iteration.

| Shared component | Prior feature it served | This iteration's change | Risk |
|---|---|---|---|
| `SymbolSearch.tsx` | J-04 manual Load flow; also used by `TopBar.tsx` (all pages) and `StudyCreateForm.tsx` | None (zero diff) | **None from this iteration** — carried-forward cosmetic quirk unchanged, see Flags |
| `FeedBasisBadge.tsx` | Cockpit live-feed badge (`/`) + `/structure` (iter-5) | None (zero diff) | None |
| `apps/frontend/app/structure/page.tsx` | J-01–J-05 | None (zero diff) | None |
| `apps/frontend/lib/api.ts`, `lib/types.ts` | All pages importing these modules | None (zero diff) | None |

Beyond the zero-diff guarantee, the browser lane itself exercised two explicit regression checks this
iteration and both passed:
- **UT-07** — the pre-existing "Load" workflow (predates this era) still renders chart + levels +
  zones correctly for `AAPL`, ruling out any collateral breakage.
- **UT-08** — repeating an already-fetched window still store-first-serves (200, no 409/"duplicate"
  text), confirming the iter-3 contract holds.

Required-still-passing journeys J-01–J-04 and J-06 are further backed by the dev handoff's full-suite
(1207/0/0/6-skipped, byte-identical to iter-5), engine-equivalence (22/22), and config-fingerprint
(`4d665603569b9dbf`, unchanged) results — none of which a UI-only review can improve on, so I treat
this as sufficient non-regression evidence for the backend-side guarantees underneath the UI.

## UI vs Backend Parity

No backend change this iteration (confirmed). The parity question is therefore unchanged from iter-5's
own clean assessment: the store-first fetch, the taxonomy-sourced badge label, and the honest
empty/error states were already fully surfaced with no backend capability silently withheld. Nothing
in this iteration's (empty) diff could have altered that conclusion, and this iteration's own browser
evidence (UT-02, UT-03, UT-05, UT-06) re-confirms each of those surfaces still renders correctly end
to end.

| Backend capability | UI exposure | Assessment |
|---|---|---|
| `taxonomy.FEED_BASIS_LABELS["yahoo"]` | Read verbatim by `FeedBasisBadge`, now captured cleanly (UT-03) | Fully surfaced |
| Store-first `POST /research/bars` | Triggerable via the fetch control (UT-02, UT-08) | Fully surfaced |
| `levels.no_bar_series_for_symbol` empty state | Renders via the Load form, now browser-captured (UT-06) | Fully surfaced |
| Honest 4xx/5xx fetch errors | Renders via `UnavailablePanel` (UT-05) | Fully surfaced |

No gap. This part is clean: **PASS**.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None introduced by this iteration (zero diff; both explicit regression checks UT-07/UT-08 passed).

### Carried-Forward Known Issue (not a new finding, not caused by this iteration)

**F1 — `SymbolSearch` dropdown auto-opens after a successful fetch, still present in the live product
for real users.** This is worth stating precisely rather than declaring fully closed: this iteration
closes the **evidence** gap iter-5 flagged (every prior screenshot showed the badge occluded) — UT-03
now shows a clean, legible "Yahoo Finance" badge, captured by clicking outside `SymbolSearch` before
the shot. That is a real fix to the *proof*, not a fix to the *product*. The underlying behavior
(`handleFetchYahoo` programmatically sets the Load form's symbol field → `SymbolSearch`'s
`useEffect` cannot distinguish that from a keystroke → the suggestion dropdown auto-opens) is
unchanged in source and will still visibly pop open over the chart/badge area for every real user
after every successful fetch, until they click elsewhere. This is:
- **Not new** — first flagged in `phase-goal-yahoo_fetch-iter-5-ux-regression.md` as a Medium-risk
  "Potential Regression" and a Should-fix recommendation.
- **Not a regression from this iteration** — zero diff means it is neither introduced nor worsened
  here.
- **Explicitly out of scope by design**, with a documented rationale I find sound: `SymbolSearch` is
  shared by `TopBar.tsx` (every page) and `StudyCreateForm.tsx`, and editing its interaction behavior
  on a certification pass risks regressing J-06 for a cosmetic gain — correctly deferred to a future
  guarded polish iteration per the phase spec's Out of Scope section.
- **Self-resolving with one incidental click** and does not block, corrupt, or hide any data or
  action — it is friction, not a broken journey.

Net effect on this iteration's verdict: none. It does not block PASS because it is a known,
pre-existing, deliberately-deferred, non-blocking cosmetic issue, not something this iteration
introduced or was required to fix. It is documented here so the distinction between "evidence gap
closed" and "underlying UX quirk fixed" stays visible for whoever plans the next product-quality
iteration.

**TC-11 (honest empty state) — fully resolved, no residual gap.** Unlike F1, this item had no
underlying product issue at all — the empty state already worked correctly; it simply had never been
browser-captured. UT-06 now captures it end to end (`TSLA`, confirmed live via `GET
/research/bars?symbol=TSLA` → empty, before capture). Nothing outstanding here.

### Visual Consistency
No new pages or components exist to assess (zero diff). Re-confirmed via UT-01 through UT-08 that the
existing dark instrument-panel styling (`border-slate-600 bg-slate-800`, uppercase field labels,
`Panel`/`UnavailablePanel` patterns) renders identically to iter-5 — no arbitrary values, no new
effects, no drift. iter-5's own visual-consistency assessment (clean, reusing `Panel`/`INPUT_CLASS`
verbatim) stands unchanged.

## Evidence-Artifact Quality Check (supporting this verdict)

Since this iteration's entire purpose was landing real evidence (not building UI), I verified the
artifacts themselves are not stubs:
- `reports/phase-goal-yahoo_fetch-iter-6-ui-test-plan.md`: **290 lines** (iter-5's was a 15-line
  SKIPPED stub: *"ui-test-design-phase.sh Claude CLI exited with code 70..."*).
- `reports/phase-goal-yahoo_fetch-iter-6-what-to-click.md`: **85 lines** (iter-5's was a 15-line stub).
- `reports/phase-goal-yahoo_fetch-iter-6-ui-test-results.md`: real top-line `**Browser QA Verdict:**
  PASS`, 8/8 tests, per-test evidence paths (iter-5's equivalent file did not exist at all).
- `reports/qa/goal-yahoo_fetch-iter-6-evidence/`: **15 screenshots** present on disk (UT-01…UT-08 plus
  the QA agent's own TC-05/06/07/09/10 pass), including `UT-03-result.png` (clean badge) and
  `UT-06-result.png` (TC-11 empty state) — the two defining new captures this iteration exists to
  produce.

## Recommendation

No action required to close this iteration. One forward-looking, non-blocking item for a future
guarded polish iteration (already known and already correctly deferred, restated here only for
continuity): fix `SymbolSearch`'s suggestion-dropdown effect to not fire on a programmatic value
change (e.g., gate on a "dirty by typing" flag) so real users don't see the dropdown auto-open after a
successful Yahoo fetch. This is a product-quality nice-to-have, not a blocker — it should be scoped and
UX-regression-verified on its own pass specifically because it touches a component shared by every
page in the app.
