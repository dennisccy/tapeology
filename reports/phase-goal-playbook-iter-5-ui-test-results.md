# UI Test Results (merged)

**Date:** 2026-08-11
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-5-evidence/J-01-verify.png |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-5-evidence/J-02-verify.png |
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-5-evidence/J-03-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-5-evidence/J-10-verify.png |
| UT-J-04 | J-04: The continuation family — JBE, DBI, cup-and-handle | happy-path | P1 | Fixture goldens for JBE/DBI/cup-and-handle fire with exact geometry; near-misses stay silent (unit-tested, not re-run here); in the browser at least one signal of each new setup type legible in the J-03 Playbook Signals section (screenshot) | On the fixture rig (`LADDER`/`DBI1`/`CUP1`, session `2026-06-22`), all three fired: LADDER's 2nd `jbe` firing renders chip "Jump-Base Explosion", side long, geometry "base 0.80 MBR wide (3 bars) · jump 4.10 MBR · broke at slot 19 · flatline base · ascending base · ladder step ratio 0.68"; DBI1's `dbi` firing renders chip "Drop-Base Implosion", side short, geometry "base 0.80 MBR wide (3 bars) · jump 6.00 MBR · broke at slot 9 · flatline base · **descending base**" (the corrected label — TC-18 carried item closed, see below); CUP1's `cup_handle` firing renders chip "Cup and Handle", side long, geometry "cup 12 bars · depth 5.00 MBR · handle retrace 0.44 · handle duration 0.25 of cup · broke at slot 19 · optimal cup length · desirable handle length · RVOL cup mid 0.30 / cup outer 1.00 / handle 0.40". All three setup:side pairs (`jbe:long`, `dbi:short`, `cup_handle:long`) also appear in the summary-vs-baseline table above the signals table | PASS | `reports/qa/goal-playbook-iter-5-evidence/UT-J-04-jbe-result.png`, `reports/qa/goal-playbook-iter-5-evidence/UT-J-04-dbi-descending-base-result.png`, `reports/qa/goal-playbook-iter-5-evidence/UT-J-04-cup-handle-result.png` |
| UT-J-05 | J-05: The climax family — capitulation entry, euphoria marker | happy-path | P1 | Fixture goldens for capitulation/euphoria exact; marker never appears as a measurable row (structural, unit-tested); lookahead-clean (unit-tested); browser: a capitulation signal + a marker-decorated signal legible on the fixture rig (screenshot) | On the same fixture rig, AAA's `capitulation` firing (TC-1) renders chip "Capitulation", side long, geometry "decline 4.70 MBR over 3 bar(s) · climax RVOL 2.50 · reversal 1 bar(s) after climax · broke at slot 4" — the four new geometry fields (`decline_mbr`, `decline_bars`, `climax_rvol`, `bars_from_climax_to_trigger`) all legible. DECOR's `capitulation` firing (TC-3) renders the SAME geometry shape ("decline 6.10 MBR over 3 bar(s) · climax RVOL 2.60 · reversal 1 bar(s) after climax · broke at slot 8") PLUS, for the first time across any setup type, the decoration disclosure — the disclosures line ends "1 approach attempt(s) · 0 bar(s) to close · **euphoria recent**", proving `disclosures.euphoria_recent` renders real `true` data (previously always stub-`false`). Confirmed structurally in the same page: the signals table lists exactly 9 rows (LADDER×3, DBI1×2, CUP1×2, AAA×1, DECOR×1) and none carries setup "Euphoria" anywhere — the marker never became a served row, consistent with TC-4 | PASS | `reports/qa/goal-playbook-iter-5-evidence/UT-J-05-capitulation-tc1-result.png`, `reports/qa/goal-playbook-iter-5-evidence/UT-J-05-euphoria-decoration-tc3-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-11

