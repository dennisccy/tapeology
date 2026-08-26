# Phase goal-hypothesis-foundry-iter-3 — UI Surface Map

**Phase:** goal-hypothesis-foundry-iter-3
**Date:** 2026-08-26
**Written by:** ui-impact-analyst

---

**Status:** N/A — Backend-only phase (Frontend Present: no)

No UI surfaces affected.

## Backend-Only Changes (No UI Impact)

| File | What it does | UI surface affected |
|------|--------------|---------------------|
| `apps/backend/tests/test_foundry_hermetic_epoch.py` (new) | Hermetic oracle test suite (TC-1..TC-8) driving the real `foundry_compiler → foundry_interpreter → foundry_family → foundry_ledger → foundry_runner` pipeline through composite/all-blocked/all-killed/multi-survivor/checkpoint-resume/protected-data-trip fixture epochs | None — hermetic pytest fixtures only, never served through any endpoint |
| `apps/backend/app/research/foundry_runner.py` | `run_one_candidate`'s already-terminal fast path now re-verifies `manifest_hash`/`econ_floor_bps` and raises `FoundryResumeIdentityMismatch` on drift (TC-9) | None — internal integrity check inside a research pipeline function with no route |
| `apps/backend/app/research/foundry_source_registry.py` | `SourceRecord` gains `source_hash` (derived `sha256(source_excerpt)`) and `alternatives` (`tuple[str, ...]`) fields | None — not read by any served endpoint yet; real 11-source registry authoring is deferred to a later iteration |
| `apps/backend/tests/test_foundry_source_registry.py` | New tests for `source_hash`/`alternatives` correctness | None — test-only |
| `apps/backend/tests/test_foundry_compiler.py` | Extends the existing two-legal-variant fixture with `alternatives` (TC-11) | None — test-only |
| `apps/backend/tests/test_foundry_runner.py` | New resume-identity-mismatch tests (TC-9) | None — test-only |
| `docs/hypothesis-foundry-spec.md` | §1.4 field table gains the `alternatives` row (documentation only) | None — internal implementation spec, not user-facing documentation |

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 6 source/test files + 1 doc file (see table above)

The existing `/desk` "Hypothesis Foundry" panel and its `GET /research/desk/micro/foundry` endpoint are
unchanged this iteration (byte-identical served response shape). J-01's golden replay
(`runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json`) is the only relevant browser check
this iteration, and it is a pure regression check against already-shipped UI, not new coverage —
consistent with the phase spec's own instruction that "the only browser check is a regression replay of
the existing J-01 golden script, not new frontend work."
