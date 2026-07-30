# Phase goal-desk-iter-22 — UI Test Results

**Phase:** goal-desk-iter-22
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 1/1 tests passed (0 skipped)

Lean/evidence-depth dispatch: only J-14 was in scope this run (J-04, J-05, J-07, J-12, J-13
are verified separately by deterministic replay — see
`reports/phase-goal-desk-iter-22-regression-replay-results.md`, 5/5 PASS, not re-tested here
per the dispatch instruction).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits (this iteration: the owed native-tooltip photograph) | evidence-capture | P1 | `/desk` opposite column shows a near (≤25bps) and far (>1000bps) opposite wall legible in the same screenshot; the row's native `title` tooltip (`bands by class A n · B n · C n · unclassified n`) is photographed via the owner-approved headed qa-rig (T-10a), exits 0, contains the literal substring "bands by class", and matches the DOM-read title and the on-disk `bands_by_class` field; the rig's negative guard is re-verified live | All of the above confirmed live against the ambient rig (`:3301`/`:8301`), which already serves `screen-2026-07-20-ca185294a384` as its latest screen | PASS | `reports/qa/goal-desk-iter-22-evidence/J-14-desk-opposite-column.png`, `reports/qa/goal-desk-iter-22-evidence/J-14-tooltip.png`, `reports/qa/goal-desk-iter-22-evidence/J-14-tooltip-crop.png` |

---

## Passed Tests

### UT-J-14 — Every ranked briefing row states where the nearest wall on the OTHER side of price sits
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-22-evidence/J-14-desk-opposite-column.png`, `reports/qa/goal-desk-iter-22-evidence/J-14-tooltip.png`, `reports/qa/goal-desk-iter-22-evidence/J-14-tooltip-crop.png`

Steps executed (headless CDP `:9222` for DOM/table verification, headed qa-rig `:9333`/Xvfb `:99`
for the native-tooltip photograph, both against the already-running ambient rig `:3301`/`:8301`
which the environment note confirmed already serves the expected fields-complete screen):

1. Navigated to `http://localhost:3301/desk`. Latest screen confirmed via `GET /research/desk/screen`
   to be `screen-2026-07-20-ca185294a384` (100 ranked rows, 1 skipped) — the exact screen this
   iteration's spec names.
2. Read the rendered table (`headers` = symbol/side/class/distance/score/coverage/tick
   evidence/basis/history/band/**opposite**) via DOM query. Row 1 (BRK-B): `opposite resistance A
   490.97–494.39 · 1.22 bps` (≤25bps). Row 4 (DIS): `opposite resistance A 108.69–109.45 ·
   1128.29 bps` (>1000bps). Both byte-match `GET /research/desk/screen?date=2026-07-20`'s own
   `opposite_band`/`distance_bps` for those rows, confirmed via a direct curl of the endpoint before
   touching the browser.
3. Scrolled the table's horizontal `overflow-x-auto` container to bring the `opposite` column into
   view and took one screenshot (`J-14-desk-opposite-column.png`) — BRK-B's near wall (1.22 bps) and
   DIS's far wall (1128.29 bps) both legible in the same frame, 3 rows apart.
4. DOM cross-check (headless `eval`, independent of the rig script): the `[data-testid="desk-row-drill-in"]`
   anchor for row 0 (BRK-B) carries `title` = "...bands by class A 10 · B 0 · C 0 · unclassified 0...",
   matching `screen-2026-07-20-ca185294a384.json`'s recorded `bands_by_class` for BRK-B
   (`{"A": 10, "B": 0, "C": 0, "unclassified": 0}`) exactly.
5. **Negative guard (TC-11), run live before trusting any positive result:** on the headed rig,
   `capture-native-tooltip.py --hover-selector 'h1' --require-title 'bands by class'` exited `4`
   with JSON `{"ok": false, "error": "no element among 1 matches carries a title containing
   'bands by class'"}` and wrote no file — confirmed this run's rig instance cannot produce a false
   positive.
6. **Positive capture:** `capture-native-tooltip.py --url http://localhost:3301/desk
   --hover-selector '[data-testid="desk-row-drill-in"]' --require-title 'bands by class' --out
   reports/qa/goal-desk-iter-22-evidence/J-14-tooltip.png --crop-out
   reports/qa/goal-desk-iter-22-evidence/J-14-tooltip-crop.png` exited `0`. Printed JSON:
   `matched_index: 0` (BRK-B, the same row step 4 read), `title` containing the literal substring
   "bands by class" and reading in full "...bands by class A 10 · B 0 · C 0 · unclassified 0...",
   `tooltip_window` geometry present (id `2097177`, 815×81 at 785,825), both output paths written.
   Both PNGs confirmed non-empty on disk (27,236 bytes crop / 180,224 bytes full frame). Opened
   both: the full frame is a real headed-Chrome window (address bar, tab strip, an "unsupported
   command-line flag: --no-sandbox" infobar) with a native yellow-bordered OS tooltip popup floating
   over the BRK-B row; the crop is a tight, fully legible zoom of that same popup showing
   "distance 0 bps · score 1763 · basis 2026-07-17T04:00:00.000000Z (3 d before as-of) · history 496
   sessions from 2024-07-25T04:00:00.000000Z · band 488.5–490.9100036621094 · close
   490.9100036621094 · **bands by class A 10 · B 0 · C 0 · unclassified 0** · 1h/4h/1d/1w window
   last requested: ...". The rig's printed `title` is byte-identical to step 4's independent DOM
   read.
7. Rig was left running per the environment note ("Do not tear the rig down when you finish") — no
   teardown attempted by this agent.

**One observed wording nuance, not scored as a failure:** the iteration spec's Definition-of-Done
bullet says the crop "shows a legible tooltip popup ... whose text begins `bands by class`." The
actual native `title` attribute (and therefore the crop, which the rig always renders as the whole
tooltip window, per its own README: "a zoomed crop of exactly the tooltip window") begins with
"distance 0 bps · score 1763 · basis ..." and carries "bands by class" mid-string, not as the first
word. This matches the tool's documented behavior and matches the *operative* technical criteria
exactly: TC-3 requires the title *contain* the literal substring "bands by class" (confirmed), and
T-10a's own text states the guard is "the hovered element's own `title` carries the required
substring" (containment, not position). The tooltip is unambiguously legible, non-blank, and carries
the required line in full precision, so this is recorded as a documentation-wording nuance rather
than a defect.

---

## Failed Tests

None.

---

## Skipped Tests

None — J-14 was the only journey in scope for this dispatch; J-04/J-05/J-07/J-12/J-13 were
explicitly out of scope (deterministic replay covers them; see
`reports/phase-goal-desk-iter-22-regression-replay-results.md`).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless CDP `:9222`, ambient) for DOM/table verification; headed
  Chrome via the owner-approved qa-rig (Xvfb `:99`, CDP `:9333`) for the native-tooltip photograph
- **Test Date:** 2026-07-30
- **Evidence directory:** `reports/qa/goal-desk-iter-22-evidence/`
- **Screen under test:** `screen-2026-07-20-ca185294a384` (latest recorded screen on the ambient rig,
  100 ranked rows / 1 skipped — the exact fields-complete recording this iteration's spec names)
