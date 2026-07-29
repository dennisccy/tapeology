# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-20-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-20-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-20-evidence/J-07-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression-evidence | P1 | A fresh full-page (non-viewport-clipped) screenshot of `screen-2026-07-27-936543601e75` shows the NFLX ranked row's `1d` coverage badge and the page's "... every timeframe badge dark" sentence together in one image; same-date pair (936543601e75 / 3ad3c57aa6ba) remain independently selectable by id | Clicked screen-history row `screen-2026-07-27-936543601e75`; Provenance panel showed Snapshot id + Recorded at `2026-07-27T21:42:14.636275Z`; briefing sentence "3 ranked row(s) below show every timeframe badge dark" rendered above the table; NFLX row (rank 5/63) confirmed via DOM eval to carry `data-has-bars="false"` on all 4 timeframe badges (1h/4h/1d/1w); full-page screenshot (1785×11044) captures the sentence and NFLX's dark badge set together; re-clicked `screen-2026-07-27-3ad3c57aa6ba` and confirmed its distinct `Recorded at 2026-07-28T21:30:16.111871Z` | PASS | `reports/qa/goal-desk-iter-20-evidence/UT-J-12-result.png` |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression-evidence | P1 | On the fields-complete populated screen `screen-2026-07-20-ca185294a384` (100 ranked rows), the `band` column renders a row's recorded `price_low`–`price_high` beside its `reference_close`; at least one ranked row's close lies inside its recorded band and one lies outside it, both legible in one screenshot; legacy rows show the honest "close not recorded in this snapshot" fallback | Clicked screen-history row `screen-2026-07-20-ca185294a384`; DOM eval confirmed BRK-B's row renders `band 488.50–490.91 · close 490.91` — byte-identical to the row's own recorded `price_low`/`price_high`/`reference_close` fetched directly from `GET /research/desk/screen?id=screen-2026-07-20-ca185294a384`; scrolled the table's horizontal overflow container to reveal the band/opposite columns and captured a screenshot showing BRK-B in-band (close 490.91 at the band's own upper edge, distance 0.00 bps) together with LMT out-of-band (`band 508.79–512.31 · close 508.77`, close below the band's low edge) in the same image; clicked legacy row `screen-2026-06-22-3ecd45c062c7` and confirmed its rows render "close not recorded in this snapshot" | PASS | `reports/qa/goal-desk-iter-20-evidence/UT-J-13-result.png` |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | regression-evidence | P1 | On the same populated screen, the `opposite` column renders a row's nearest wall on the other side of price (side/class/price range/distance); at least one row's opposite wall is within 25 bps and one is beyond 1,000 bps, both legible in one screenshot; legacy rows show the honest "opposite wall not recorded in this snapshot" fallback | DOM eval confirmed BRK-B's row renders `opposite resistance A 490.97–494.39 · 1.22 bps` — byte-identical to the row's own recorded `opposite_band` from the same GET; the same scrolled screenshot used for UT-J-13 shows BRK-B (1.22 bps), UBER (1.38 bps) and MDT (2.40 bps) all within 25 bps, together with DIS (1128.29 bps) well beyond 1,000 bps, all legible in one image; clicked legacy row `screen-2026-06-22-3ecd45c062c7` and confirmed its rows render "opposite wall not recorded in this snapshot" (bands_by_class hover-tooltip screenshot remains out of scope per iter-20 spec — structurally uncapturable native `title` attribute, confirmed in prior iterations) | PASS | `reports/qa/goal-desk-iter-20-evidence/UT-J-14-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29

