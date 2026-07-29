# UI Test Results (merged)

**Date:** 2026-07-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-21-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-21-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-21-evidence/J-07-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-21-evidence/J-12-verify.png |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | `/desk` briefing's `band` column renders a row's own recorded `price_low`–`price_high` beside its `reference_close`, with at least one ranked row whose close lies inside its recorded band and one whose close lies outside it, both legible in the same screenshot; legacy (pre-J-13) snapshots render the honest `"close not recorded in this snapshot"` fallback | Opened `screen-2026-07-20-ca185294a384` via its Screen History row; BRK-B rendered `band 488.50–490.91 · close 490.91` (close sits exactly on the band's own upper edge — inside); LMT rendered `band 508.79–512.31 · close 508.77` (close sits below the band's low edge — outside); both legible in the same cropped screenshot. Selecting the legacy screen `screen-2026-06-22-3ecd45c062c7` rendered `band <range> · close not recorded in this snapshot` on every checked row. Page remained live and responsive to further navigation. | PASS | `reports/qa/goal-desk-iter-21-evidence/UT-J-13-result.png` |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | regression | P1 | `/desk` briefing's `opposite` column renders a row's own recorded `opposite_band` (side/class/price range/distance), with at least one ranked row whose nearest opposite wall is within 25 bps and one whose nearest opposite wall is more than 1,000 bps away, both legible in the same screenshot, plus the row's full-precision `bands_by_class` line readable from the drill-in anchor's tooltip; legacy (pre-J-14) snapshots render the honest `"opposite wall not recorded in this snapshot"` fallback | Opened `screen-2026-07-20-ca185294a384`; BRK-B rendered `opposite resistance A 490.97–494.39 · 1.22 bps` (near, ≤25 bps) and DIS (3 rows down) rendered `opposite resistance A 108.69–109.45 · 1128.29 bps` (far, >1,000 bps); both legible in the same cropped screenshot. DOM-eval of BRK-B's drill-in anchor `title` attribute confirmed the composite tooltip carries `bands by class A 10 · B 0 · C 0 · unclassified 0` (the established DOM-text-read substitute for the native-tooltip photograph this headless rig cannot capture, per prior iterations' notes). Selecting the legacy screen `screen-2026-06-22-3ecd45c062c7` rendered `opposite wall not recorded in this snapshot` on every checked row. Page remained live and responsive to further navigation. | PASS | `reports/qa/goal-desk-iter-21-evidence/UT-J-14-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-30

