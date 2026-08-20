# Phase goal-rapid-microscope-iter-19 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-19
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No product UI code changed this iteration (0 `.tsx` diffs). Every row below is an **existing, unchanged** surface whose automated regression coverage was deepened or that must be re-verified fresh because this iteration's diff touches the shared QA rig. "What to Test" describes what the deepened/mandatory replay now checks, not a new capability.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Microscope Readiness section — Legacy Tick Shards table, "Fallback frac" column header (`apps/frontend/app/desk/page.tsx:6071`) | Test coverage only (no product change) | `J-02.json` deepened: step 2 now clicks `desk-section-expand-microReadiness` and asserts the literal text `"Fallback frac"` instead of an unrelated pre-existing Desk heading | Navigate to `/desk`, click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`), confirm the Legacy Tick Shards table's column header row includes the text "Fallback frac". Requires the backend's readiness data to include at least one tick shard — the header itself only renders when `readiness.shards.length !== 0` (empty state renders "No tick shards recorded." instead, with no table). |
| `/desk` | Microscope Readiness section — Joinable Corpus table, "Joinable corpus — withheld (excluded)" row label (`apps/frontend/app/desk/page.tsx:6006`) | Test coverage only (no product change) | `J-03.json` deepened: step 2 now clicks `desk-section-expand-microReadiness` and asserts the literal text `"Joinable corpus — withheld (excluded)"` instead of an unrelated pre-existing Desk heading | Navigate to `/desk`, click the "Microscope Readiness" section header, confirm a table row labeled "Joinable corpus — withheld (excluded)" is visible with a numeric value in the adjacent cell (`data-testid="micro-readiness-withheld-excluded"`). This row renders unconditionally once readiness data loads (not gated on any list being non-empty). |
| `/desk` | Scout Ledger section — "Ledger chain verification:" line (`apps/frontend/app/desk/page.tsx:6268`) | Test coverage only (no product change) | `J-04.json` deepened: step 2 now clicks `desk-section-expand-scoutLedger` and asserts the literal text `"Ledger chain verification:"` instead of an unrelated pre-existing Desk heading | Navigate to `/desk`, click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`), confirm the text "Ledger chain verification:" is visible followed by either "ok" or a "failed at row N (reason)" string, sourced from `GET /research/desk/micro/scout`'s `chain_verification` field. |
| `/desk` | Walk-Forward section — "Ledger chain verification:" line (`apps/frontend/app/desk/page.tsx:6495`) | Test coverage only (no product change) | `J-05.json` deepened: step 2 now clicks `desk-section-expand-walkForward` and asserts the literal text `"Ledger chain verification:"` instead of an unrelated pre-existing Desk heading | Navigate to `/desk`, click the "Walk-Forward" section header (`data-testid="desk-section-expand-walkForward"`), confirm the text "Ledger chain verification:" is visible followed by either "ok" or a "failed at row N (reason)" string, sourced from `GET /research/desk/micro/walkforward`'s `chain_verification` field. |
| `/desk`, `/desk` steps 1 of J-02/J-03/J-04/J-05 | Playbook Signals section heading (`aria-label="Playbook Signals"`) | Test coverage only (no product change) | J-02/J-03/J-04's step 1 was corrected to the shared pattern (`goto /desk` → expect `"Playbook Signals"`) already used by J-01/J-08/J-10, replacing a step that asserted an unrelated heading; J-05's step 1 already matched | Navigate to `/desk`, confirm the page immediately shows the heading "Playbook Signals" (no click needed — it is a top-level, always-rendered section). |
| `/` | Cockpit ticker watch flow (unchanged) | Regression re-verify only | J-10's kept-product sentinel must re-run fresh this round because the shared QA rig changed | Navigate to `/`, confirm "No ticker watched" is visible, type "SIM-BUYER" into the "Ticker" field, click the "Watch" button, confirm "Buyer Control" appears. |
| `/structure` | Tradable Map load flow (unchanged) | Regression re-verify only | J-10's kept-product sentinel must re-run fresh this round | Navigate to `/structure`, confirm "Tradable Map" is visible, type "AAPL" into the "Structure symbol" field, type "2026-06-22 16:00:00" into the as-of field (`data-testid="structure-as-of-input"`), click the load button (`data-testid="structure-load-button"`), confirm the text "300.11–302.2" appears. |
| `/desk` | Referee Registry / Referee Adjudications / Referee Runs sections (unchanged) | Regression re-verify only | J-10's kept-product sentinel must re-run fresh this round | Navigate to `/desk`, click each of `desk-section-expand-refereeRegistry`, `desk-section-expand-refereeAdjudications`, `desk-section-expand-refereeRuns`; confirm "config fingerprint 08e471b10130e1e2", "No hypotheses registered.", and "No evaluation runs recorded yet." respectively. |
| `/desk` | Validation Vault section (unchanged) | Regression re-verify only | Required-still-passing journeys J-08/J-10 must stay green via the full 8-journey replay set this round | Navigate to `/desk`, click `desk-section-expand-validationVault`, confirm the text "iter18-qa-universe" appears. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_micro_deterministic_rerun.py` (new) — 8 pytest tests proving snapshot build, Scout screen, and walk-forward fold evaluation are byte-identical on re-run over unchanged fixture data, plus 3 mutation-proof tests that the comparisons can actually fail. Pure backend test code; not served to any client, no UI surface affected.
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — dev/QA launcher script extended to also write `reports/qa-scoped-backend-store-manifest.md` (resolved `TAPEOLOGY_*` store-root env vars, root dir, port, launch timestamp) alongside its pre-existing stderr echo lines. This is a tooling/reporting artifact consumed by QA/reviewer/auditor agents, not by the running product's frontend or API — no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 2 (new test module; QA launcher script + generated manifest report)
- **Regression-harness-only surfaces (existing, unchanged, coverage deepened or mandatory re-verify):** 8 rows above, covering `/desk` (Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault, all three Referee sections), `/`, and `/structure`.
