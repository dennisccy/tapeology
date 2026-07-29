# Goal Iteration goal-desk-iter-21 — UI Test Results

**Phase:** goal-desk-iter-21
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->

**Overall:** 2/2 tests passed (0 skipped)

Scope note: per this iteration's lean-mode dispatch, ONLY J-13 and J-14 were browser-tested this
run. J-04, J-05, J-07, J-12 were NOT tested here — they are covered by a separate deterministic
golden-replay pass (evidence already present in `reports/qa/goal-desk-iter-21-evidence/` as
`J-04-verify.png`, `J-05-verify.png`, `J-07-verify.png`, `J-12-verify.png`). Iteration
goal-desk-iter-21 itself makes zero production code change (`Depth: evidence`, capture-only) —
J-13 and J-14's behavioral acceptance was already built and browser-verified in prior iterations
(iter-17 for J-13, iter-18/19 for J-14); this run is a live regression re-check confirming nothing
broke, using the current running rig (backend `:8301` / frontend `:3301`) and the same
fields-complete populated screen (`screen-2026-07-20-ca185294a384`, 100 ranked rows) prior QA runs
used.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | `/desk` briefing's `band` column renders a row's own recorded `price_low`–`price_high` beside its `reference_close`, with at least one ranked row whose close lies inside its recorded band and one whose close lies outside it, both legible in the same screenshot; legacy (pre-J-13) snapshots render the honest `"close not recorded in this snapshot"` fallback | Opened `screen-2026-07-20-ca185294a384` via its Screen History row; BRK-B rendered `band 488.50–490.91 · close 490.91` (close sits exactly on the band's own upper edge — inside); LMT rendered `band 508.79–512.31 · close 508.77` (close sits below the band's low edge — outside); both legible in the same cropped screenshot. Selecting the legacy screen `screen-2026-06-22-3ecd45c062c7` rendered `band <range> · close not recorded in this snapshot` on every checked row. Page remained live and responsive to further navigation. | PASS | `reports/qa/goal-desk-iter-21-evidence/UT-J-13-result.png` |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | regression | P1 | `/desk` briefing's `opposite` column renders a row's own recorded `opposite_band` (side/class/price range/distance), with at least one ranked row whose nearest opposite wall is within 25 bps and one whose nearest opposite wall is more than 1,000 bps away, both legible in the same screenshot, plus the row's full-precision `bands_by_class` line readable from the drill-in anchor's tooltip; legacy (pre-J-14) snapshots render the honest `"opposite wall not recorded in this snapshot"` fallback | Opened `screen-2026-07-20-ca185294a384`; BRK-B rendered `opposite resistance A 490.97–494.39 · 1.22 bps` (near, ≤25 bps) and DIS (3 rows down) rendered `opposite resistance A 108.69–109.45 · 1128.29 bps` (far, >1,000 bps); both legible in the same cropped screenshot. DOM-eval of BRK-B's drill-in anchor `title` attribute confirmed the composite tooltip carries `bands by class A 10 · B 0 · C 0 · unclassified 0` (the established DOM-text-read substitute for the native-tooltip photograph this headless rig cannot capture, per prior iterations' notes). Selecting the legacy screen `screen-2026-06-22-3ecd45c062c7` rendered `opposite wall not recorded in this snapshot` on every checked row. Page remained live and responsive to further navigation. | PASS | `reports/qa/goal-desk-iter-21-evidence/UT-J-14-result.png` |

---

## Passed Tests

### UT-J-13 — Every ranked briefing row states the price its wall sits at and the close it was measured from
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-21-evidence/UT-J-13-result.png`
- Navigated to `http://localhost:3301/desk`; page loaded with heading "Desk".
- Clicked the Screen History row for `screen-2026-07-20-ca185294a384` (100 ranked / 1 skipped,
  recorded 2026-07-29T12:24:33Z); the provenance panel updated to that snapshot id and the
  BRIEFING table re-rendered with the `band` column populated for every ranked row.
- Confirmed via full-page text extraction and a horizontally-scrolled screenshot (the `band`/
  `opposite` columns sit past the ranked table's `overflow-x-auto` clientWidth) that:
  - BRK-B (rank 1): `band 488.50–490.91 · close 490.91` — close sits exactly on the band's own
    upper edge (`distance_bps` 0.0 per the underlying JSON) — an in-band example.
  - LMT (rank 20): `band 508.79–512.31 · close 508.77` — close sits just below the band's low
    edge (`distance_bps` 0.38 per the underlying JSON) — an out-of-band example.
  - Both values were cross-checked against a direct `curl` of
    `GET /research/desk/screen?id=screen-2026-07-20-ca185294a384` and are byte-identical to the
    served `price_low`/`price_high`/`reference_close` fields (rounded to 2 decimals for display).
- Cropped the full-page screenshot to the row band containing both BRK-B and LMT so both strings
  are legible in the same image (saved as the test evidence).
- Clicked the legacy Screen History row `screen-2026-06-22-3ecd45c062c7` (predates the
  `reference_close` field) and confirmed via DOM eval that its first 3 rendered rows all show
  `band <range> · close not recorded in this snapshot` — the honest append-only-rail fallback.
- Navigated back to `/desk` as a liveness check; page rendered correctly.

### UT-J-14 — Every ranked briefing row states where the nearest wall on the OTHER side of price sits
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-21-evidence/UT-J-14-result.png`
- Re-selected `screen-2026-07-20-ca185294a384` from Screen History.
- Confirmed the `opposite` column renders a row's recorded `opposite_band`:
  - BRK-B (rank 1): `opposite resistance A 490.97–494.39 · 1.22 bps` — a NEAR opposite wall
    (≤25 bps).
  - DIS (rank 4): `opposite resistance A 108.69–109.45 · 1128.29 bps` — a FAR opposite wall
    (>1,000 bps), only 3 ranked rows below BRK-B.
  - Both values cross-checked against the same direct `curl` of `GET /research/desk/screen?id=...`
    and are byte-identical to the served `opposite_band.side`/`band_class`/`price_low`/
    `price_high`/`distance_bps` fields.
- Cropped the full-page screenshot to the row band containing both BRK-B and DIS so both strings
  are legible in the same image (saved as the test evidence).
- Via DOM eval, read BRK-B's drill-in anchor (`data-testid="desk-row-drill-in"`) `title`
  attribute and confirmed it carries the full-precision `bands_by_class` line:
  `bands by class A 10 · B 0 · C 0 · unclassified 0`. This rig cannot photograph a native HTML
  `title` tooltip (confirmed across prior iterations' runs, `lessons.md` iter-19); per this
  iteration's own OUT-OF-SCOPE note, the DOM-text-read substitute is accepted in place of a
  screenshot of the hover state.
- Clicked the legacy Screen History row `screen-2026-06-22-3ecd45c062c7` (predates the
  `opposite_band` field) and confirmed via DOM eval that its first 3 rendered rows all show
  `opposite wall not recorded in this snapshot` — the honest append-only-rail fallback.
- Navigated back to `/desk` as a liveness check; page rendered correctly.

---

## Failed Tests

None.

---

## Skipped Tests

None — Chrome MCP was available (attached to the pre-existing isolated headless Chrome on CDP
port 9222) and the frontend (`:3301`) / backend (`:8301`) were both up (HTTP 200) for the entire
run.

---

## Golden Replay Scripts

Both journeys PASSed, so deterministic replay scripts were written/overwritten for the goal-mode
regression speedup:
- `runs/goal-session-desk/journey-scripts/J-13.json`
- `runs/goal-session-desk/journey-scripts/J-14.json`

Both lint clean:
```
$ python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-desk/journey-scripts --journeys J-13,J-14
J-13 ok
J-14 ok
```

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** headless Chrome (pre-existing, CDP port 9222, `--headless=new --no-sandbox`) via
  `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Date:** 2026-07-29
- **Production diff during this iteration:** none observed (`git diff` against
  `apps/backend/app/research/desk_screen.py` / `apps/backend/tests/test_desk_screen.py` was empty
  at test time) — consistent with the iteration's `Depth: evidence`, capture-only scope.
