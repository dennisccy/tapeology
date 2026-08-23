# Phase goal-rapid-microscope-iter-27 — UI Test Results

**Phase:** goal-rapid-microscope-iter-27
**Date:** 2026-08-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 browser-tested journeys passed (1 skipped — no UI surface exists for J-07)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | smoke | P1 | `GET /research/desk/micro/readiness` serves corpus totals, per-shard inventory (each tagged `exploratory`/`hand_assigned`), and a floors table where every pilot study reads `floor_unmet`; the `/desk` Microscope Readiness section renders those same served values verbatim (element screenshot). | Navigated to `/desk` ("Playbook Signals" heading present, matching golden step 1); clicked `desk-section-expand-microReadiness`; extracted the expanded `[data-testid="micro-readiness-section"]` element and cross-checked field-by-field against a live `GET http://localhost:8301/research/desk/micro/readiness`: Distinct symbol-days 2, Distinct datasets 3, RTH minutes 1.75, Session-equivalents 0.0045, Referee tick-gate 150 — byte-identical to the JSON. All 3 shards (PG×2 + PGQA) rendered with matching checksums, all `hand_assigned`/`exploratory`. All 3 Pilot-Study Floor rows (`range_wall_failed_aggression`, `delta_divergence_level_tests`, `capitulation_exhaustion`) read `floor_unmet`. Sealed Tranche aggregate block (1 shard/1 symbol-day, `iter25-qa-sealed-only-universe`) also matched verbatim. "No integrity errors." Note (consistent with the established, previously-PASSED pattern since iter-3/iter-6/iter-23/iter-24/iter-26): the store-scoped QA rig (`:8301`/`:3301`) carries a small fixture corpus, not the real 12-symbol-day/18-file legacy corpus goal.md's acceptance text illustrates (`distinct_symbol_days: 12`, `session_equivalents ≈ 3.0`) — this is a pre-existing, out-of-scope rig-seeding gap, not a regression; the actually-verifiable claim (UI renders the endpoint's served values verbatim, correct tagging, all floors unmet) holds exactly. | PASS | `reports/qa/goal-rapid-microscope-iter-27-evidence/J-01-result.png` |
| UT-J-07 | Graduation — provenance in, nothing laundered out | functional | P2 | Fixture candidate walks `exploratory → walkforward_survivor → sealed_survivor → referee_handoff_ready`; diagnostic-only twin refused at first transition; failed-sealed twin carries its permanent verdict in the export bundle; every `referee_*` module stays byte-identical. | No `/desk` UI section or browser-reachable reveal exists for Graduation — confirmed by source inspection (`grep -in graduation apps/frontend/app/desk/page.tsx` returns zero hits) and by navigation: `GET http://localhost:8301/research/desk/micro/graduation` (backend port) returns 200 with real ledger data (one family, state `exploratory`, one `sealed_evaluation` row with `verdict: "pass"`, `chain_verification.ok: true`), but the SAME path through the frontend port `http://localhost:3301/research/desk/micro/graduation` 404s (no Next.js rewrite exists for raw `/research/...` paths — matches the iter-22 lesson recorded in this iteration's own NOTES). goal.md's own journeys preamble states only J-01 and J-08 are browser-verifiable, with J-09's results rendering through J-08's sections — J-07 carries no such browser-reveal clause. Supplementary backend evidence: `PYTHONPATH=. .venv/bin/pytest -q tests/test_micro_graduation.py` → 23/23 passed. | SKIP | none (no UI surface to capture) |
| UT-J-10 | The kept product stands — traps armed, sentinel green | smoke | P1 | Sentinel screenshots show every kept surface (cockpit live-tape/chart, `/structure` load + Tradable Map, every shipped `/desk` section including all 3 Referee sections plus the 4 Rapid-Microscope sections) rendering as shipped, browser-verified via the store-scoped rig. | Drove the full 17-step sentinel walkthrough fresh via Chrome MCP: (1) `/` shows "No ticker watched"; (2-3) watched `SIM-BUYER`, "Buyer Control" state rendered; (4) `/structure` shows "Tradable Map"; (5-7) loaded AAPL @ 2026-06-22 16:00:00 ET, tradable band "300.11–302.2" rendered; (8) `/desk` shows "Playbook Signals"; (9) expanded Playbook Evidence, "Built from signature:" present; (10) filled session date 2026-06-22, "recorded signals, none hidden" present; (11) expanded Microscope Readiness, "Distinct symbol-days" present; (12) expanded Scout Ledger, "variants tried" present; (13) expanded Walk-Forward, "No fold specs registered." present; (14) expanded Validation Vault, "iter18-qa-universe" present; (15) expanded Referee Registry, "config fingerprint 08e471b10130e1e2" present; (16) expanded Referee Adjudications, "No hypotheses registered." present; (17) expanded Referee Runs, "No evaluation runs recorded yet." present. All 17 expectations held; every kept surface plus all 4 Rapid-Microscope sections render as shipped. (Backend trap-suite (TR-1..TR-30) / deterministic-rerun / full-suite / fingerprint-pin / referee-SHA re-check are backend-verification concerns outside browser-QA scope — covered by dev/auditor artifacts, not re-verified here.) | PASS | `reports/qa/goal-rapid-microscope-iter-27-evidence/J-10-result.png` |

---

## Passed Tests

### UT-J-01 — The era transition stands — the corpus truth on the record
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-27-evidence/J-01-result.png`
- `/desk` Microscope Readiness section expanded and cross-checked field-by-field against the live `GET /research/desk/micro/readiness` response — byte-identical.
- All 3 shards tagged `exploratory`/`hand_assigned`; all 3 pilot-study floor rows `floor_unmet`; no integrity errors.
- Golden replay script written/overwritten at `runs/goal-session-rapid-microscope/journey-scripts/J-01.json` (lint-clean via `demo_runner.py --mode lint`).

### UT-J-10 — The kept product stands — traps armed, sentinel green
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-27-evidence/J-10-result.png`
- Full 17-step sentinel walkthrough (cockpit live-tape, `/structure` Tradable Map load, all shipped `/desk` sections including all 3 Referee sections plus the 4 Rapid-Microscope sections) executed fresh; every step's expected text held.
- Golden replay script written/overwritten at `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` (lint-clean via `demo_runner.py --mode lint`).
- Passenger side effect: this pass also captured the "Desk readiness figures" and "Scout Ledger family row + variants tried" make-up captures named in `iteration-state.md` (steps 11 and 12 above) — flagging per iter-27's NOTES as a natural side effect, not manufactured scope.

---

## Skipped Tests

### UT-J-07 — Graduation — provenance in, nothing laundered out
**Verdict:** SKIPPED
**Reason:** No `/desk` UI section or browser-reachable page renders Graduation data. Source inspection confirms zero "graduation" references anywhere in `apps/frontend/app/desk/page.tsx`; the `GET /research/desk/micro/graduation` route exists and serves real data on the backend port (`:8301` → 200, non-empty ledger), but is not proxied through the frontend port (`:3301` → 404; no Next.js rewrite for raw `/research/...` paths — the exact discrepancy this iteration's own NOTES already flag as a recurring lesson from iter-22). goal.md's journeys preamble explicitly names only J-01 and J-08 as browser-verifiable (with J-09 rendering through J-08's sections); J-07 carries no browser-reveal clause and its Acceptance is entirely about a fixture-pipeline proof, not UI rendering. Supplementary non-browser evidence: `test_micro_graduation.py` 23/23 passed. No golden replay script was written for J-07 (best-effort, per instructions) since there is no browser surface to script.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Chrome MCP (headless, CDP :9222)
- **Test Date:** 2026-08-23
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-27-evidence/`
