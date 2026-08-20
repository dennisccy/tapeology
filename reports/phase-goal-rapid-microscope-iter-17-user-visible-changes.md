# Phase goal-rapid-microscope-iter-17 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-17
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration is backend-only in effect, even though `Frontend Present: yes` in the plan
(that flag is set only because a full-regression browser pass of the already-shipped product was
required this round, not because any new UI was built). No `apps/frontend/**` file changed
(confirmed: `git status`/dev handoff report zero frontend diffs), no new route, no new page
section, no new button or form, and no existing control changed behavior from a user's point of
view.

---

## What Changed in the Visible UI

Nothing. Every changed file is under `apps/backend/app/research/` or `apps/backend/tests/`:

- `micro_sealed_evaluation.py` (new module) — internal sealed-verdict evaluator, not rendered
  anywhere.
- `micro_graduation.py` — rewrote the internal sealed-verdict persistence call and the
  confirmation-boundary formula; four docstrings corrected. The served response of
  `GET /research/desk/micro/graduation` gains additional fields inside its existing
  `sealed_evaluations` / export-bundle payload (a tri-state verdict, provenance fields, and the
  lineage-boundary derivation), but this endpoint has no `/desk` page section or MCP tool that
  reads it (verified independently by this analyst: `grep -rn "graduation" apps/frontend/` and
  `grep -rln "graduation" apps/backend/app/mcp/` both return zero hits). Nothing on screen changes
  as a result.
- `micro_accessor.py` — one paragraph of the module docstring corrected to describe existing
  behavior accurately; explicitly no behavior change.
- Four test files updated/added — test-only, never user-facing.

No CSS, component, route, navigation element, or `/desk` section was touched.

---

## What Old Behavior Changed

- None from a user's perspective. Internally, `micro_graduation.record_sealed_evaluation` no
  longer accepts a caller-supplied `passed: bool` — that is a Python-API contract change consumed
  only by other backend research code (`micro_sealed_evaluation.py`), never by an HTTP client, the
  frontend, or an MCP tool. No operator-visible request/response contract changed.
- The `GET /research/desk/micro/graduation` endpoint's JSON payload gains additional fields (see
  above), but since no UI or MCP tool consumes this endpoint today, this is not an observable
  behavior change for any user — only for a hypothetical future consumer of that endpoint.

---

## Not Visible Yet

- The sealed-shard evaluation verdict (PASS / FAIL / `insufficient`, with its full provenance —
  candidate/spec identity, shard checksum, effect and floor inputs, rule id/version/hash) is now
  computed and persisted by `micro_sealed_evaluation.py`, and served inside
  `GET /research/desk/micro/graduation`'s JSON — but no `/desk` page section, cockpit panel, or MCP
  tool renders or reads it. It exists only for a direct API/curl caller.
- The lineage-wide `proposed_confirmation_boundary` derivation (frontier evidence ids, embargo
  rule, `evidence_safe_boundary`, `handoff_created_at`) is likewise persisted in the same endpoint's
  export-bundle payload with no UI surface.
- J-10's replay script was run for the first time this era and genuinely FAILED on step 11 (a
  pre-existing data-drift finding in the real store's Walk-Forward section — unrelated to this
  round's code). This is not a new user-visible defect introduced by this iteration; it is an
  existing condition of the real store's data that this round happened to discover while exercising
  the journey for the first time. No fix was applied (per the plan's conditional instruction:
  "record the finding" rather than alter the script).
