# Phase goal-desk-iter-20 — UI Test Results

**Phase:** goal-desk-iter-20
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression-evidence | P1 | A fresh full-page (non-viewport-clipped) screenshot of `screen-2026-07-27-936543601e75` shows the NFLX ranked row's `1d` coverage badge and the page's "... every timeframe badge dark" sentence together in one image; same-date pair (936543601e75 / 3ad3c57aa6ba) remain independently selectable by id | Clicked screen-history row `screen-2026-07-27-936543601e75`; Provenance panel showed Snapshot id + Recorded at `2026-07-27T21:42:14.636275Z`; briefing sentence "3 ranked row(s) below show every timeframe badge dark" rendered above the table; NFLX row (rank 5/63) confirmed via DOM eval to carry `data-has-bars="false"` on all 4 timeframe badges (1h/4h/1d/1w); full-page screenshot (1785×11044) captures the sentence and NFLX's dark badge set together; re-clicked `screen-2026-07-27-3ad3c57aa6ba` and confirmed its distinct `Recorded at 2026-07-28T21:30:16.111871Z` | PASS | `reports/qa/goal-desk-iter-20-evidence/UT-J-12-result.png` |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression-evidence | P1 | On the fields-complete populated screen `screen-2026-07-20-ca185294a384` (100 ranked rows), the `band` column renders a row's recorded `price_low`–`price_high` beside its `reference_close`; at least one ranked row's close lies inside its recorded band and one lies outside it, both legible in one screenshot; legacy rows show the honest "close not recorded in this snapshot" fallback | Clicked screen-history row `screen-2026-07-20-ca185294a384`; DOM eval confirmed BRK-B's row renders `band 488.50–490.91 · close 490.91` — byte-identical to the row's own recorded `price_low`/`price_high`/`reference_close` fetched directly from `GET /research/desk/screen?id=screen-2026-07-20-ca185294a384`; scrolled the table's horizontal overflow container to reveal the band/opposite columns and captured a screenshot showing BRK-B in-band (close 490.91 at the band's own upper edge, distance 0.00 bps) together with LMT out-of-band (`band 508.79–512.31 · close 508.77`, close below the band's low edge) in the same image; clicked legacy row `screen-2026-06-22-3ecd45c062c7` and confirmed its rows render "close not recorded in this snapshot" | PASS | `reports/qa/goal-desk-iter-20-evidence/UT-J-13-result.png` |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | regression-evidence | P1 | On the same populated screen, the `opposite` column renders a row's nearest wall on the other side of price (side/class/price range/distance); at least one row's opposite wall is within 25 bps and one is beyond 1,000 bps, both legible in one screenshot; legacy rows show the honest "opposite wall not recorded in this snapshot" fallback | DOM eval confirmed BRK-B's row renders `opposite resistance A 490.97–494.39 · 1.22 bps` — byte-identical to the row's own recorded `opposite_band` from the same GET; the same scrolled screenshot used for UT-J-13 shows BRK-B (1.22 bps), UBER (1.38 bps) and MDT (2.40 bps) all within 25 bps, together with DIS (1128.29 bps) well beyond 1,000 bps, all legible in one image; clicked legacy row `screen-2026-06-22-3ecd45c062c7` and confirmed its rows render "opposite wall not recorded in this snapshot" (bands_by_class hover-tooltip screenshot remains out of scope per iter-20 spec — structurally uncapturable native `title` attribute, confirmed in prior iterations) | PASS | `reports/qa/goal-desk-iter-20-evidence/UT-J-14-result.png` |

---

## Passed Tests

### UT-J-12 — Every recorded screen the ledger lists can be read back — snapshots are addressable by id
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-20-evidence/UT-J-12-result.png`
- This iteration's specific deliverable was a corrected full-page (not viewport-clipped) screenshot of `screen-2026-07-27-936543601e75` proving the NFLX ranked row's `1d` coverage badge and the page's divergence-note sentence render together. NFLX ranks #5 of 63 in this snapshot, close enough to the briefing's top that a full-page capture (1785×11044px) trivially contains both in its top ~1,000px — confirmed by cropping and visually inspecting that region: the sentence "3 ranked row(s) below show every timeframe badge dark..." sits directly above the table, and NFLX's row (5 rows down) shows all four timeframe badges (1h/4h/1d/1w) rendered dark/unlit, in contrast to the lit-green badges on the surrounding BRK-B/DHR/HD/IBM/CRM/AMT rows.
- Confirmed via DOM eval that NFLX's badges in this snapshot are `data-has-bars="false"` for all four timeframes, matching `GET /research/desk/screen?id=screen-2026-07-27-936543601e75`'s own served coverage data.
- Re-confirmed the same-date pair distinguishability: selecting `screen-2026-07-27-3ad3c57aa6ba` (the later recording) updates Provenance's Recorded-at to `2026-07-28T21:30:16.111871Z`, distinct from the earlier `2026-07-27T21:42:14.636275Z`.

### UT-J-13 — Every ranked briefing row states the price its wall sits at and the close it was measured from
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-20-evidence/UT-J-13-result.png`
- Opened `screen-2026-07-20-ca185294a384` (100 ranked rows, all carrying `reference_close`) via its screen-history `?id=` link. DOM eval on BRK-B's row returned `band 488.50–490.91 · close 490.91`, matching the backend's own recorded `price_low=488.5`, `price_high≈490.91`, `reference_close≈490.91` for that row exactly (fetched directly via curl against `GET /research/desk/screen?id=screen-2026-07-20-ca185294a384` for cross-check).
- The ranked table's `band`/`opposite` columns sit past the `overflow-x-auto` container's visible width (table 1553px vs container clientWidth 1214px); scrolled the container's `scrollLeft` to its max and captured a screenshot showing both columns. The image legibly shows BRK-B (`band 488.50–490.91 · close 490.91`, close sits exactly at the band's own upper edge — inside) together with LMT (`band 508.79–512.31 · close 508.77`, close sits numerically below the band's low edge 508.79 — outside), satisfying the "one inside, one outside, same screenshot" acceptance clause.
- Confirmed the legacy fallback: selecting the era's earliest recorded screen (`screen-2026-06-22-3ecd45c062c7`, which predates the `reference_close` field) renders "close not recorded in this snapshot" on its rows.

### UT-J-14 — Every ranked briefing row states where the nearest wall on the OTHER side of price sits
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-20-evidence/UT-J-14-result.png`
- On the same populated screen, DOM eval on BRK-B's row returned `opposite resistance A 490.97–494.39 · 1.22 bps`, matching the backend's own recorded `opposite_band` for that row exactly.
- The same scrolled screenshot used for UT-J-13 (one image satisfies both journeys' acceptance, since the `band` and `opposite` columns are adjacent) shows near opposite-wall examples (BRK-B 1.22 bps, UBER 1.38 bps, MDT 2.40 bps — all ≤25 bps) together with a far example (DIS 1128.29 bps, well beyond 1,000 bps), all legible in one image.
- Confirmed the legacy fallback on `screen-2026-06-22-3ecd45c062c7`: rows render "opposite wall not recorded in this snapshot".
- The `bands_by_class` hover-tooltip photograph was NOT re-attempted — per the goal-desk-iter-20 spec, this is explicitly out of scope (a native HTML `title` attribute, confirmed structurally uncapturable by this headless CDP rig across three prior runs); its DOM-text-read substitute stands as already proven.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes on scope

Per the goal-desk-iter-20 spec (`Depth: evidence`, no code changes), all three journeys were
already behaviorally proven passing in prior iterations (J-12 in iter-16, J-13 in iter-17, J-14
in iter-18/19). This run's browser QA re-verified each journey's rendering live against the
running ambient rig (backend :8301 / frontend :3301, serving the real `apps/backend/.data`
store — the same store the fixed screen-history rows `?id=` addressed) and captured fresh,
corrected screenshot evidence per the iteration's Definition of Done (the J-12 full-page crop).
No write path was exercised: every action was a screen-history row click, which drives only
`GET /research/desk/screen?id=<id>`, a plain read. No files under `apps/backend/.data` were
created or modified by this browser QA pass.

Golden replay scripts for all three journeys were refreshed at
`runs/goal-session-desk/journey-scripts/{J-12,J-13,J-14}.json` (lint-clean via
`demo_runner.py --mode lint`) to speed up future regression replay.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Chrome MCP (headless, CDP :9222)
- **Test Date:** 2026-07-29
- **Evidence directory:** `reports/qa/goal-desk-iter-20-evidence/`
