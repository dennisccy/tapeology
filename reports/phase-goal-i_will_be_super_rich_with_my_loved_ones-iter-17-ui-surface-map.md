# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-17 — UI Surface Map

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-17
**Date:** 2026-06-12
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No UI surfaces changed this iteration. `Frontend Present: yes` exists solely to force browser QA to run two regression sentinels against existing cockpit surfaces after the engine touch. The rows below document those sentinel check points — not new features.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/cockpit/SIM-BUYER` (no thesis declared) | Cockpit chart panel with "Control" marker | Regression sentinel (J-68) | Engine internals changed; byte-identity of rendered output must be confirmed | Start a watch on SIM-BUYER with no thesis, wait for the chart to render, capture the full page — confirm the Control marker is present, the confidence badge reads the same value as pre-iter-17 captures, and the capture file is non-blank (> 0 bytes) |
| `/cockpit/SIM-BUYER` (no thesis declared) | Observations panel | Regression sentinel (J-68) | Same engine change; observations are derived from feature computation | On the same SIM-BUYER cockpit page, scroll the observations panel into view and verify it lists at least one observation entry with a non-empty text body — no "undefined" or blank rows |
| `/cockpit/SIM-BUYER` (no thesis declared) | Event log panel | Regression sentinel (J-68) | Same engine change; event log reflects engine-emitted events | On the same SIM-BUYER cockpit page, confirm the event log shows at least one timestamped event entry and does not show an error state or empty-state placeholder |
| `/cockpit/SIM-BUYER` (no thesis declared) | Confidence display | Regression sentinel (J-68) | Confidence is computed by the same engine path that was refactored | Confirm the displayed confidence value is a non-zero decimal (expected ~0.86 for SIM-BUYER buyer_control) and that the classification label reads "buyer_control" — not a blank, zero, or error state |
| `/tape/:symbol/state` (REST endpoint, consumed by cockpit) | `GET /tape/SIM-BUYER/state` JSON response | Regression sentinel (J-08 REST == UI) | Backend API must agree with what the cockpit renders after the engine change | Call `GET /tape/SIM-BUYER/state` directly; confirm the `classification` field is `buyer_control` and the `confidence` value matches (within display rounding) what the cockpit UI shows for the same symbol |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/features.py` — replaced the permanent post-eviction O(n²) merge fallback in `_Window` with an incremental `_RefreshSide`-based structure; byte-identical outputs; no API shape change — no UI surface affected
- `apps/backend/app/config.py` — added `dense_replay_time_budget_seconds = 60.0` to the config, excluded from `config_fingerprint` (CI gate value only) — no displayed value changes, no UI surface affected
- `apps/backend/tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json` — committed ≈10-min real SIP dense fixture (PG, 2026-06-09 17:00–17:10 UTC); consumed only by the test suite — no UI surface affected
- `apps/backend/tests/test_dense_replay_gate.py` — new CI timing gate + structural no-rescan + pinned anchor + fingerprint-pair tests — no UI surface affected
- `apps/backend/tests/test_refresh_increment.py` — new `_RefreshSide` differential + oracle-equivalence + error-case tests — no UI surface affected
- `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` — additive iter-17 build-out note registering the fixture and budget key as test/CI assets — no UI surface affected

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 6
