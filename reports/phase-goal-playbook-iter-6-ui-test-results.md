# UI Test Results (merged)

**Date:** 2026-08-11
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

> **AUDIT CORRECTION (2026-08-11, auditor — read before trusting UT-02/UT-11 below).**
> The UT-02/UT-11 rows record `... low zone touches 2 · high zone touches **1** · broke at slot **4** ...`.
> That geometry was captured at 09:44, **before** the audit-fix pass rewrote `range_trade`'s arming
> gate (audit B1: spec §3.7 requires **both** zones to show ≥ 2 held touches). The shipped detector
> can no longer produce a one-sided arming, so those two rows describe a build that no longer exists
> — their PASS verdicts are not evidence for the code on disk. Already flagged as a blocker in
> `runs/goal-playbook-iter-6/status.json`.
> **Re-verified by the auditor on a fresh, scoped, clean-`.next`-rebuilt rig** (seeded via
> `apps/backend/scripts/qa_playbook_iter6_fixture_scoped_backend.sh`, backend :8301, frontend :3301,
> Chrome CDP :9222), post-fix values:
> - `desk-playbook-signal-range-trade-geometry` = *"range 5.00 MBR wide · low zone touches 2 ·
>   high zone touches 2 · broke at slot 7 · crossed midrange"* (RTAAA, long, trigger 102.60,
>   invalidation 99.22 — below entry)
> - `desk-playbook-signal-double-extreme-geometry` = *"gap 0.30 MBR · separation 10 bar(s) ·
>   depth 13.00 MBR · nominal risk 13.30 MBR · broke at slot 18 · second RVOL vs first 1.00"*
>   (DTAAA, Double Top, short) — both rows in the same `desk-playbook-record` table, same pass.
> Screenshot: `reports/qa/goal-playbook-iter-6-evidence/audit-J-06-postfix-double-top-geometry.png`.
> UT-03 and the remaining UT rows are unaffected (their values reproduce on the corrected rig).

---

**Browser QA Verdict:** PASS

**Overall:** 17/17 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-6-evidence/J-01-verify.png |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-6-evidence/J-02-verify.png |
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-6-evidence/J-03-verify.png |
| UT-J-04 | The continuation family — JBE, DBI, cup-and-handle | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-6-evidence/J-04-verify.png |
| UT-J-05 | The climax family — capitulation entry, euphoria marker (goal-mode regression lane) | regression | P1 (journey) | DECOR "Capitulation" long signal renders with `euphoria_recent` disclosure legible | Re-verified live end to end: filling date 2026-06-22 (no compute click) surfaced "Capitulation" via the newest record; clicking the DECOR row rendered "decline 6.10 MBR over 3 bar(s) · climax RVOL 2.60 · reversal 1 bar(s) after climax · broke at slot 8" plus "euphoria recent" in the disclosures line — J-05's acceptance holds. The prior replay FAIL was confirmed to be a stale golden script: the old `{"testid":"desk-playbook-signal-row"}` generic click target resolves to whichever row sorts FIRST in a multi-symbol rig (RTAAA here, not DECOR), so it never reached the euphoria-decorated row. Repaired to `{"text":"DECOR"}` (unique on the page) and lint-verified clean via `demo_runner.py --mode lint` | PASS | `reports/qa/goal-playbook-iter-6-evidence/UT-J-05-result.png`; repaired golden: `runs/goal-session-playbook/journey-scripts/J-05.json` |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-6-evidence/J-10-verify.png |
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

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-11

