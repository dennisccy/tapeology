# Phase goal-rapid-microscope-iter-17 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-17
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No new or changed UI surface exists for this iteration — zero `apps/frontend/**` files changed,
and the one touched backend-api surface (`GET /research/desk/micro/graduation`) is not consumed by
any page or MCP tool. Because `Frontend Present: yes` in the plan (the browser pass this round is a
**regression check of already-shipped surfaces**, not new construction), the table below lists the
already-shipped surfaces the plan and phase spec require QA/browser verification to re-touch this
round, each marked "Regression check" — none of them changed code this iteration.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `GET /research/desk/micro/graduation` | Graduation endpoint response (`sealed_evaluations` / export-bundle payload) | Changed behavior (payload only, not rendered) | `micro_sealed_evaluation.py` now supplies a recomputed tri-state verdict + provenance, and `build_export_bundle` persists the new lineage-boundary derivation fields | Navigate directly to `http://localhost:8301/research/desk/micro/graduation` (or run `curl http://localhost:8301/research/desk/micro/graduation`) and confirm HTTP 200 with the honest empty-state body `{"families": [], "message": "No candidates ledgered.", ...}` on a store with no ledgered candidates — this is J-07's own no-golden-script LLM-fallback check named in the plan |
| `/` (cockpit) | Live tape panel + chart | Regression check, no code change | Kept-product sentinel required by J-10's acceptance text this round | Load `http://localhost:3301/`, confirm the live tape stream renders and the chart displays candles/price data without error |
| `/structure` | Tradable Map + level/zone view | Regression check, no code change | Kept-product sentinel required by J-10's acceptance text this round | Load `http://localhost:3301/structure`, set a date, click Load, confirm the Tradable Map renders bands without error |
| `/desk` | Microscope Readiness section | Regression check, no code change | Kept-product sentinel; verifies the trap-suite/module rewrite did not break the readiness aggregate surface | Load `http://localhost:3301/desk`, click to expand the "Microscope Readiness" section, confirm it renders (empty or populated) without a client error |
| `/desk` | Scout Ledger section | Regression check, no code change | Kept-product sentinel | Expand the "Scout Ledger" section on `/desk`, confirm it shows "No candidates ledgered." (honest empty state) or real rows without error |
| `/desk` | Walk-Forward section | Regression check, no code change | Kept-product sentinel; this is the section where J-10's replay genuinely FAILED against the real store (pre-existing data drift unrelated to this round's code, per dev handoff) | Expand the "Walk-Forward" section on `/desk`; note whether it shows "No fold specs registered." (expected on a clean store) or a real fold spec (expected on the current real store, per the dev handoff's documented data-drift finding) — either is acceptable, this is a known pre-existing condition, not a regression to file |
| `/desk` | Referee sections (all three) | Regression check, no code change | Kept-product sentinel required by J-10's acceptance text | Expand each of the three Referee sections on `/desk`, confirm each renders without a client error |
| `/desk` | Four Rapid-Microscope sections | Regression check, no code change | Kept-product sentinel required by J-10's acceptance text | Expand each of the four Rapid-Microscope sections on `/desk`, confirm each renders without a client error |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/micro_sealed_evaluation.py` (NEW) — sole scientific owner of the
  sealed-shard evaluation verdict (7-step sequence, `SEALED_PASS_RULE_V1`); a Python module called
  only by other backend research code, never by an HTTP route or the frontend — no UI surface
  affected.
- `apps/backend/app/research/micro_graduation.py` — `record_sealed_evaluation`'s caller-supplied
  `passed: bool` retired in favor of a computed `artifact: dict`; `_proposed_confirmation_boundary`
  rewritten to the lineage-wide r6 §8.2 formula; `build_export_bundle` persists the new derivation
  fields; four docstrings corrected. These are internal Python-API and payload-shape changes behind
  `GET /research/desk/micro/graduation`, an endpoint with zero frontend or MCP consumers (verified:
  `grep -rn "graduation" apps/frontend/` and `grep -rln "graduation" apps/backend/app/mcp/` both
  return no hits) — no UI surface affected.
- `apps/backend/app/research/micro_accessor.py` — docstring-only correction, explicitly no behavior
  change — no UI surface affected.
- `apps/backend/tests/test_micro_sealed_evaluation.py` (NEW), `apps/backend/tests/test_micro_graduation.py`,
  `apps/backend/tests/test_micro_accessor.py`, `apps/backend/tests/test_micro_observer.py` — test
  files only, never rendered or served — no UI surface affected.
- `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` — run through the replay harness
  for the first time this era; left byte-unchanged (confirmed: `git diff` on this file is empty)
  after a genuine step-11 FAIL traced to pre-existing real-store data drift unrelated to this
  round's code — a test artifact, not a UI surface.
- `docs/goal.md`, `docs/rapid-validation-spec.md`, `docs/handoffs/goal-rapid-microscope-iter-17-dev.md` —
  documentation only — no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 10 (3 production research modules + 4 test files + 1 replay script + 2 docs)
