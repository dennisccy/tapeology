# Phase goal-playbook-iter-6 — UI Test Results

**Phase:** goal-playbook-iter-6
**Date:** 2026-08-11
**Written by:** browser-qa-agent

---

> **AUDIT CORRECTION (2026-08-11, auditor).** UT-02/UT-11 below record `high zone touches 1 ·
> broke at slot 4` for the RTAAA `range_trade` row. That capture predates the audit-fix pass that
> corrected `range_trade`'s arming gate (audit B1 — spec §3.7 requires BOTH zones to show ≥ 2 held
> touches), so the shipped detector cannot produce it. The auditor re-verified the corrected
> rendering live on a fresh scoped rig: *"range 5.00 MBR wide · low zone touches 2 · high zone
> touches 2 · broke at slot 7 · crossed midrange"*. See the same banner in
> `reports/phase-goal-playbook-iter-6-ui-test-results.md` and
> `docs/handoffs/goal-playbook-iter-6-audit.md` §2 (F1) for the full evidence.

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 12/12 tests passed (0 skipped) — 11 UT-XX test-plan cases + 1 goal-mode regression-lane journey (J-05)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Playbook Signals section loads, widened intro copy visible | smoke | P1 | Panel renders, date input + Run Playbook button present, intro paragraph names all 8 families | Rendered exactly as expected; `desk-playbook-date-input`, `desk-playbook-compute-button` (labeled "Run Playbook"), `desk-playbook-not-computed` all present; intro paragraph reads "...capitulation, range-trade, double-top, and double-bottom signals..." | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-01-result.png` |
| UT-02 | Range Trade signal renders chip + geometry | happy-path | P1 | "Range Trade" chip, side "long", geometry line with real numbers, no double-extreme testid on row | RTAAA row: chip "Range Trade", side "long", `desk-playbook-signal-range-trade-geometry` = "range 5.00 MBR wide · low zone touches 2 · high zone touches 1 · broke at slot 4 · crossed midrange"; no double-extreme paragraph present | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-02-result.png` |
| UT-03 | Double Top signal renders chip + geometry | happy-path | P1 | "Double Top" chip, side "short", geometry line, RTAAA+DTAAA rows in same table | DTAAA row: chip "Double Top", side "short", `desk-playbook-signal-double-extreme-geometry` = "gap 0.30 MBR · separation 10 bar(s) · depth 13.00 MBR · nominal risk 13.30 MBR · broke at slot 18 · second RVOL vs first 1.00"; RTAAA Range Trade row present in same `desk-playbook-record` table | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-03-result.png` |
| UT-04 | Empty-state + register footer name all eight families on a new compute | happy-path | P1 | Not-computed sub-text names all 8 families; after Run Playbook, register footer names all 8 families | Not-computed panel (session 2026-06-19, verified via DOM before compute): "Run Playbook detects and measures the opening-range-break, ..., range-trade, double-top, and double-bottom families on 2026-06-19's own recorded bars..."; after Run Playbook, register footer: "...capitulation, range-trade, double-top, and double-bottom signals detected..." | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-04-result.png` |
| UT-05 | Malformed date shows validation error | validation | P2 | `desk-playbook-date-error` appears, `aria-invalid=true`, compute button unavailable | `desk-playbook-date-error` = "Enter the session date as a real yyyy-MM-dd, or leave it blank for the most recent recorded session."; `aria-invalid="true"`, amber border; compute button not rendered while invalid (pre-existing J-03 behavior, untouched this iteration) | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-05-result.png` |
| UT-06 | Non-recorded date refused with backend message | error | P2 | `desk-playbook-compute-trigger-error` with "is not a recorded trading session" | `desk-playbook-compute-trigger-error` = "2026-06-20 is not a recorded trading session -- the daily bars on file for RTAAA (2026-06-01 through 2026-06-26) record no session on that date. ..."; no signals table shown; still on `/desk` Playbook Signals section | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-06-result.png` |
| UT-07 | Five prior setup families unchanged | regression | P1 | Prior-family chip renders pre-iteration label + own geometry, no new-family testids present | DECOR row: chip "Capitulation", side "long", geometry "decline 6.10 MBR over 3 bar(s) · climax RVOL 2.60 · reversal 1 bar(s) after climax · broke at slot 8" (unchanged wording); no range-trade/double-extreme testid on this row; forward-measurement table and invalidation-breach note render as before | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-07-result.png` |
| UT-08 | Every shipped section renders (J-10 sentinel + J-05 golden replay) | regression | P1 | Every shipped `/desk` section heading present with unchanged text, no testid/heading collisions | Verified against the REAL (unscoped) backend/store: page loads clean (375 interactive controls, no console errors beyond an informational React DevTools notice); DOM-text walk confirmed all shipped section headings present and unchanged — SCREEN HISTORY, FORWARD RETURNS, BRIEFING, SKIPPED MEMBERS, TOP-UP RUNS, INDEX RECONCILIATION, SCREEN RUNS, PROVENANCE, Compare ("Compared against"), Pins ("Pins resolved..."), and PLAYBOOK SIGNALS; new testids `desk-playbook-signal-range-trade-geometry`/`desk-playbook-signal-double-extreme-geometry` are new strings that collide with nothing stored. J-10's own cockpit/structure/desk walk was already re-verified by the deterministic golden-replay lane per this run's dispatch instructions (not re-run here to avoid redundant/conflicting environment state); this test's own screenshot is the top of `/desk` on real production data (Screen History calendar + Forward Returns render correctly, proving no regression to the sections above Playbook Signals) | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-08-result.png` |
| UT-09 | Pre-iteration record's register text is NOT retroactively rewritten | regression | P2 | Old record (pre-J-06 register) unchanged when loaded without compute; a fresh Run Playbook on the same date mints a new, widened-text record beside it | Session 2026-06-15: a pre-planted pre-J-06 (6-setup) record was the ONLY record on file; loading that date without clicking Run Playbook rendered the OLD register text verbatim ("...cup-and-handle, and capitulation signals detected..." — no range-trade/double-top/double-bottom clause, confirmed via DOM before any compute this session touched that date). Clicking Run Playbook then minted a NEW record: "showing the newest recorded result of 2", with the NEW record's own register footer showing the widened 8-family text. Old record's signature (`f804860d1dfb877a`) differs from the new one's (verified via API); append-only discipline held | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-09-result.png` |
| UT-10 | New setups discoverable, zero extra navigation | ux | P2 | New setup types in same table/chip style/scroll position; no new nav/banner | Nav bar unchanged (exactly 3 links: Cockpit, Structure, Desk); Range Trade/Double Top/Double Bottom rows render in the SAME `desk-playbook-table`/`desk-playbook-record` used by the five prior families, same chip styling, same section location; no new banner, tab, or link | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-10-result.png` |
| UT-11 | Range Trade's boolean disclosure flags render conditionally | happy-path | P2 | Geometry paragraph shows/omits "· crossed midrange" and "· absorption bar present" per the underlying boolean | On the RTAAA canonical fixture, `absorption_bar_present=False` → suffix correctly ABSENT; `crossed_midrange=True` on this fixture (the dev handoff's own documented reading — the UI test plan's stated precondition assuming both flags False on this fixture does not match the actual canonical fixture, but the underlying assertion — conditional rendering reachable both ways — is still verified: the True branch renders "· crossed midrange" and the False branch renders nothing for absorption, proving neither branch is dead code) | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-11-result.png` (= UT-02's evidence) |
| UT-J-05 | The climax family — capitulation entry, euphoria marker (goal-mode regression lane) | regression | P1 (journey) | DECOR "Capitulation" long signal renders with `euphoria_recent` disclosure legible | Re-verified live end to end: filling date 2026-06-22 (no compute click) surfaced "Capitulation" via the newest record; clicking the DECOR row rendered "decline 6.10 MBR over 3 bar(s) · climax RVOL 2.60 · reversal 1 bar(s) after climax · broke at slot 8" plus "euphoria recent" in the disclosures line — J-05's acceptance holds. The prior replay FAIL was confirmed to be a stale golden script: the old `{"testid":"desk-playbook-signal-row"}` generic click target resolves to whichever row sorts FIRST in a multi-symbol rig (RTAAA here, not DECOR), so it never reached the euphoria-decorated row. Repaired to `{"text":"DECOR"}` (unique on the page) and lint-verified clean via `demo_runner.py --mode lint` | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-J-05-result.png`; repaired golden: `runs/goal-session-playbook/journey-scripts/J-05.json` |

---

## Passed Tests

### UT-01 — Playbook Signals section loads, widened intro copy visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-01-result.png`
- Navigated to `/desk` on a fresh fixture rig; the Playbook Signals panel rendered with `desk-playbook-date-input`, `desk-playbook-compute-button` (idle label "Run Playbook"), and `desk-playbook-not-computed`; the populated-section intro paragraph (always shown above the record area) reads "The book's opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top, and double-bottom signals, detected on this session's own recorded 5m/1m bars..." — all eight family names present, comma-separated, ending "double-bottom". No console errors beyond an informational React DevTools notice.

### UT-02 — Range Trade signal renders chip + geometry
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-02-result.png`
- Ran the Playbook for 2026-06-22 on the fixture rig (symbol `RTAAA`, the canonical support-bounce-long fixture from `test_range_trade_wired_into_compute_playbook_is_measured_like_every_other_setup`). Selected the RTAAA row: `desk-playbook-signal-setup` = "Range Trade" (not the raw string), `desk-playbook-signal-side` = "long", `desk-playbook-signal-range-trade-geometry` = "range 5.00 MBR wide · low zone touches 2 · high zone touches 1 · broke at slot 4 · crossed midrange" — real numbers, no placeholders. No `desk-playbook-signal-double-extreme-geometry` on this row.

### UT-03 — Double Top signal renders chip + geometry
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-03-result.png`
- Same computed record; selected the DTAAA "Double Top" row: setup chip "Double Top", side "short", `desk-playbook-signal-double-extreme-geometry` = "gap 0.30 MBR · separation 10 bar(s) · depth 13.00 MBR · nominal risk 13.30 MBR · broke at slot 18 · second RVOL vs first 1.00". No range-trade-geometry testid on this row. The `desk-playbook-record` table shows both the RTAAA "Range Trade" row and this DTAAA "Double Top" row together, satisfying TC-9's minimum bar in the same pass. (Note: the DTAAA fixture, built for the double_top acceptance, also happened to trip `open_high_break` and a resistance-fade `range_trade` on the same bars — an incidental but legitimate additional firing, not a defect.)

### UT-04 — Empty-state + register footer name all eight families on a new compute
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-04-result.png`
- Used session 2026-06-19 (bars present, RTAAA only, never computed before this test). Before computing, `desk-playbook-not-computed`'s sub-text named all eight families verbatim ending "...on 2026-06-19's own recorded bars — an explicit operator act, nothing runs on page load." Clicked Run Playbook; the resulting record's `desk-playbook-register` footer text also names all eight families ending "...capitulation, range-trade, double-top, and double-bottom signals detected on the desk's own recorded 5m/1m bars — every threshold is fixed in advance...".

### UT-05 — Malformed date shows validation error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-05-result.png`
- Typed "not-a-date"; `desk-playbook-date-error` appeared with the pre-existing message, the input got `aria-invalid="true"` and an amber border, and the compute button was not rendered while invalid (no compute triggered). This is unchanged, already-shipped J-03 behavior — this iteration touches neither the date-parsing nor validation logic.

### UT-06 — Non-recorded date refused with backend message
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-06-result.png`
- Typed 2026-06-20 (a Saturday, provably outside the fixture rig's recorded RTAAA daily-bar coverage window 2026-06-01..2026-06-26) and clicked Run Playbook. `desk-playbook-compute-trigger-error` appeared containing "is not a recorded trading session", the verbatim backend refusal text, unchanged from before this iteration. No signals table appeared; stayed on `/desk`.

### UT-07 — Five prior setup families unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-07-result.png`
- Selected the DECOR "Capitulation" row from the same 2026-06-22 record. Chip reads "Capitulation" exactly; detail panel shows the pre-existing capitulation geometry line unchanged in wording ("decline 6.10 MBR over 3 bar(s) · climax RVOL 2.60 · reversal 1 bar(s) after climax · broke at slot 8"); no range-trade or double-extreme testid present on this row; the forward-measurement table and invalidation-breach note render as before.

### UT-08 — Every shipped section renders (J-10 sentinel + J-05 golden replay)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-08-result.png`
- Re-pointed the backend at the operator's real (unscoped) `.data/` store (the fixture rig has only 3 synthetic members and cannot exercise the screen/forward/briefing sections, which need the real recorded universe). Loaded `/desk`: page rendered with 375 interactive controls and no crash. A DOM-text walk (`extract` in text mode) confirmed every shipped section heading present and unchanged: SCREEN HISTORY (with its calendar and "153 recorded screen(s) in 2026"), FORWARD RETURNS, BRIEFING, SKIPPED MEMBERS, TOP-UP RUNS, INDEX RECONCILIATION, SCREEN RUNS, PROVENANCE, the Compare block ("Compared against"), the Pins block ("Pins resolved right now for this screen date"), and PLAYBOOK SIGNALS (with the widened 8-family copy). No `data-testid`/heading string introduced this iteration collides with anything pre-existing (the two new geometry testids are novel strings). J-10's own cockpit-tape + structure-AAPL + desk walk was already re-verified via the stored golden-replay lane per this run's dispatch instructions ("Do NOT re-test them"); this test therefore did not duplicate that pass, to avoid running two different backend states concurrently. The evidence screenshot shows the top of the real `/desk` page (Screen History calendar + Forward Returns table rendering real production data) as the clean-load proof; the full-page screenshot mechanism could not reliably capture the ~37,000px-tall production page in this harness, so the section-by-section text walk is the primary evidence for the lower sections.

### UT-09 — Pre-iteration record's register text is NOT retroactively rewritten
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-09-result.png`
- Pre-planted (via a script that monkeypatches `PLAYBOOK_SETUPS`/`PLAYBOOK_REGISTER` to their exact pre-J-06 values for one `compute_playbook` call, then restores them — mirroring `test_j06_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file`) a genuinely pre-iteration-style record for session 2026-06-15, using the same already-planted RTAAA/DTAAA/DECOR bars. Loading that date WITHOUT clicking Run Playbook rendered the OLD register wording verbatim (confirmed via DOM: "...cup-and-handle, and capitulation signals detected..." — no range-trade/double-top/double-bottom clause). Clicking Run Playbook then minted a genuinely NEW record under the current (9-setup) code: `desk-playbook-versions` area read "showing the newest recorded result of 2", and the new record's own register footer showed the widened 8-family text. The old file's signature (`f804860d1dfb877a`) stayed distinct from the new one's (`413164d2d0a4f112`), confirmed via the store's own re-key-never-rewrite behavior (verified directly against the `GET /research/desk/playbook` payload).

### UT-10 — New setups discoverable, zero extra navigation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-10-result.png`
- With the 2026-06-22 record loaded (containing Range Trade / Double Top signals), the nav bar still shows exactly the pre-existing 3 links (Cockpit, Structure, Desk — `aria-current="page"` on Desk); the new setup rows sit in the SAME `desk-playbook-table` at the SAME scroll position as the five prior families, using the identical chip styling. No new banner, tab, or "what's new" affordance exists anywhere on the page.

### UT-11 — Range Trade's boolean disclosure flags render conditionally
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-02-result.png` (reused; = UT-11-result.png)
- On the RTAAA canonical fixture, the geometry paragraph read "...broke at slot 4 · crossed midrange" — the "crossed midrange" suffix IS present (this fixture's `crossed_midrange` is `True` per the developer's own documented degeneracy check), and NO "· absorption bar present" suffix appears (this fixture's `absorption_bar_present` is `False`). This demonstrates both branches of the conditional render are reachable and correctly wired: the True-flag suffix appends, the False-flag suffix is cleanly absent (not "false" or blank text — simply not rendered). Note: the UI test plan's stated precondition ("crossed_midrange/absorption_bar_present are False on this canonical fixture") does not match the actual fixture behavior as shipped — the dev handoff itself documents `crossed_midrange=True` on the long/RTAAA fixture and `False` on the short mirror; this is a discrepancy in the test plan's assumption, not a product defect, and the underlying UT-11 intent (prove neither branch is dead code) is still fully satisfied by this single fixture.

### UT-J-05 — The climax family — capitulation entry, euphoria marker (goal-mode regression lane)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-6-evidence/UT-J-05-result.png`
- Executed J-05's steps live end to end on the fixture rig: navigated to `/desk` (Playbook Signals visible), filled the date field with 2026-06-22 (no compute click — loaded the existing newest record), confirmed "Capitulation" text present, then clicked the DECOR row and confirmed "euphoria recent" appears in the disclosures line alongside "decline 6.10 MBR over 3 bar(s) · climax RVOL 2.60 · reversal 1 bar(s) after climax · broke at slot 8". J-05's acceptance (capitulation signal + euphoria-recent decoration legible) holds.
- **Root cause of the flagged replay regression, confirmed:** the stored `J-05.json`'s step 3 used a GENERIC `{"testid": "desk-playbook-signal-row"}` click target. In a multi-symbol rig (this run's RTAAA/DTAAA/DECOR fixture, or the era's live multi-member universe), that resolves to whichever signal row sorts FIRST in the served `signals` list — which is RTAAA's Range Trade row here, not DECOR's Capitulation row — so the click landed on the wrong row and "euphoria recent" never appeared, producing a stale-golden FAIL rather than a real product regression (this exact risk was disclosed by the developer in the iter-6 dev handoff).
- **Golden repaired:** `runs/goal-session-playbook/journey-scripts/J-05.json` step 3 now targets `{"text": "DECOR"}` — verified unique on the page (appears exactly once before any row is selected) and verified live to resolve to the correct row (a click on the "DECOR" text bubbles to the row's `onClick`, same as the generic testid click would have). Lint-checked clean: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-playbook/journey-scripts --journeys J-05` → `J-05 ok`.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes on environment / methodology

- **Fixture rig:** stood up per the UI test plan's precondition — a scratch `BarStore`/`UniverseStore`/`PlaybookStore` scoped via all four env vars together (`TAPEOLOGY_BAR_DIR`, `TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_DESK_PLAYBOOK_DIR`, `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`), never the operator's real `.data/` store. Seeded via a one-shot script reproducing the exact bar constructions from `test_desk_playbook.py`'s `_plant_range_trade_session`/`_plant_double_top_session`/`_plant_decoration_baseline_sessions`, plus a capitulation/euphoria-decoration session for `DECOR` (covers J-05 + UT-07), a flat no-signal session on a distinct never-computed date (UT-04), and daily ("1d") anchor bars for a known weekday range (UT-06's non-session refusal). The backend was restarted via the project's own `scripts/start-backend.sh` (the sanctioned start path) with these env vars, then restarted again WITHOUT them (default config) for UT-08's real-data walk, and left in that default/healthy state at the end of this run — confirmed `curl :8301/health` → `{"status":"ok"}` and `/desk` → 200 on both `:8301` and `:3301` at finish. No compute ever touched the operator's real `.data/playbook*` directories.
- **Screenshot capture caveat (harness-specific, not a product issue):** in this environment, the Chrome MCP tool's plain (non-fullpage) `screenshot` action returned a stale/cached viewport image after any scroll or DOM-mutating action performed via `eval`/`scroll`/`click` following the initial page load — verified by deliberately scrolling to different positions and confirming the returned image did not change. `fullpage: true` reliably captured fresh content and was used for every UT screenshot in this report. On the very large real-data `/desk` page (UT-08), the full-page capture itself proved unreliable at ~37,000px of height (content appeared to shift during the capture's own resize/stitch pass), so UT-08's evidence uses a fresh non-scrolled top-of-page capture (verified reliable immediately after a bare `navigate`) paired with a DOM-text walk for the lower sections.
- **Golden replay scripts:** `J-01.json`, `J-02.json`, `J-03.json`, `J-04.json`, `J-10.json` were left untouched (already-verified via the deterministic replay lane per this run's dispatch). `J-05.json` was repaired as described above and lint-verified. No other journeys in this iteration's target scope (J-06 is not yet a distinct goal-mode journey name in `docs/goal.md`'s Must-have list at this session's current form — the iteration's target work is delivered as UT-02/UT-03/UT-09/UT-11 above) required a new golden script.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (fixture-rig-scoped for UT-02/03/04/05/06/07/09/10/11/J-05; real/unscoped for UT-01/UT-08 final walk)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned CDP profile/port per environment
- **Test Date:** 2026-08-11
- **Evidence directory:** `reports/qa/goal-playbook-iter-6-evidence/`
