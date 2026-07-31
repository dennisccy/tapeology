# Iteration 29 — Coherence Audit

**Iteration:** goal-desk-iter-29
**Date:** 2026-07-31
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen run records (per-run outcome ledger) — id/pins/state/reused/members/ranked/skipped/screen_id/error/failed_member | OK | `apps/backend/app/research/desk_screen_log.py:97-267` (new module, sole owner) served by ONE route `apps/backend/app/research/desk_routes.py:498-511` (`GET /research/desk/screen/runs`); registered additively in `runs/goal-session-desk/state/blueprint.md` Data Contract table before the build (RESOLVED-at-iter-29 note). Matches the DoD shape exactly (honest-empty `{"runs": [], "latest": null}` + `integrity_errors`, meta-only bulk list, full `latest`). |
| The five screen pins (`as_of`, `universe_snapshot_id`, `config_fingerprint`, `bar_store_signature`, plus `screen_date`) | OK (see advisory note below) | `apps/backend/app/research/desk_screen_compute.py:155-161` (pre-walk resolution, used for the `find_by_key` pre-check and for the run-log write) vs. `apps/backend/app/research/desk_screen.py:437-451` (`compute_screen`'s own internal resolution, used for the recorded snapshot). Both call sites invoke the SAME canonical accessors (`screen_as_of`, `UniverseStore.list()`, `Config.config_fingerprint()`, `compute_bar_store_signature`/`_bar_store_signature` over `get_desk_coverage`) — this is the same registered source called twice, not an independently-derived value, so it is not a Step-1 duplicate-computation violation. Flagged as an advisory race window below. |
| Screen snapshot / row / skip shapes, rank order, five-pin key (`desk_screen.ScreenStore`) | OK — zero diff | `git diff` confirms `desk_screen.py` itself is untouched; `screen_store.record(...)` call in `desk_screen_compute.py:340-347` still passes `result["..."]` (compute_screen's own return) verbatim, exactly as before this iteration. |
| MCP surface (17 tools, read-only proxy) | OK | `apps/backend/tests/test_mcp_server.py:1087-1105` (new) proves `GET /research/desk/screen/runs` is reachable through the existing `/research/` allowlist with zero new tool and asserts `len(TOOL_NAMES) == 17`; no `_STATIC_PATHS`/tool-registry edit in the diff. |
| `Config().config_fingerprint()` / fingerprint pin | OK | No diff to `config.py` in the changeset; storage dir uses `resolve_desk_screen_log_dir`'s bare env-var-or-sibling default (`desk_screen_log.py:72-83`), explicitly not a `Config` field, matching the `resolve_desk_topup_log_dir` precedent already sanctioned in the Data Contract. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` "Screen Runs" section (J-18) | OK | `apps/frontend/app/desk/page.tsx:2255-2262` — new `<section aria-label="Screen Runs">` rendered as a fourth panel on the existing `/desk` page, immediately after the already-registered Index Reconciliation section. No new route, no new page, no nav-skeleton change (confirmed by `reports/phase-goal-desk-iter-29-ui-surface-map.md`'s own "Navigation changes: no" line). Blueprint's IA table (`runs/goal-session-desk/state/blueprint.md`, J-18 row) registers this exact home before the build. Reachable in 0 additional clicks beyond `/desk` itself, which was already ≤2 clicks from the app's nav skeleton in prior iterations. |
| `GET /research/desk/screen/runs` route registration | OK | `apps/backend/app/research/desk_routes.py:498` — exactly one `@router.get("/screen/runs")` declaration; no duplicate route, no second module serving the same concept. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Dual pin resolution — narrow race window (WARN, not FAIL).** `run_screen_and_record` now
  resolves the five pins once before the walk (`desk_screen_compute.py:155-161`, used for the
  pre-check and for what gets written to the new run-log) and `compute_screen` resolves them again
  internally microseconds later (`desk_screen.py:437-451`, used for what gets written to the actual
  `ScreenStore` snapshot). Both call the identical canonical accessors over the identical stores, so
  in the overwhelmingly common case they agree byte-for-byte and this is not an independent/divergent
  computation of a registered value. But if the underlying universe/bar store mutated in that window
  (e.g., a concurrent top-up run), the run-log's recorded pins could disagree with the snapshot's own
  pins for the same `screen_id` — the "numbers don't match" shape, just gated behind a very narrow
  race rather than architectural duplication. The dev's own audit (`docs/handoffs/goal-desk-iter-29-audit.md`,
  finding B3) already surfaced this and classified it as an accepted observation, backstopped by
  `ScreenAlreadyRecorded`, with the alternative (threading pins into `compute_screen`) explicitly
  out of scope for this iteration. No fix required this iteration; if a future iteration touches
  `run_screen_and_record` again, prefer threading the pre-resolved pins into `compute_screen` rather
  than re-resolving, to close the window.
- **Reused-run detail framing reads as incomplete (WARN, cosmetic).** `apps/frontend/app/desk/page.tsx`'s
  `LatestScreenRunDetail` renders the amber "`<N>` members not reached" chip and a "0 ranked · 0
  skipped..." line for a `reused` run (0/101 attempted is literally true for a reuse), which sits
  beside the honest "reused `<id>` — no walk was performed" text and can read as an incomplete/failed
  run rather than a successful short-circuit. Every value shown is accurate; this is a labeling/framing
  clarity issue, not a second source of truth or a hidden feature. Already logged by the dev's own
  audit (finding F1) as left unfixed / scope creep. Does not block this iteration; worth a one-line
  guard (`unreached > 0 && !(run.state === "done" && run.reused)`) in a future pass.
- **Golden replay script pinned to a mutable ambient value (out of coherence scope, noted for
  awareness).** `runs/goal-session-desk/journey-scripts/J-18.json` asserts against today's specific
  `screen_id`, which the dev's own audit (finding T1) flags as fragile against the next real screen
  run. This is a test/evidence durability concern, not an SSOT or IA violation, so it does not affect
  this verdict.

No new displayed value in this iteration is unregistered — the one new entity (screen run records)
was registered in the blueprint's Data Contract table before the build, matching the iteration
spec's "Data-contract additions" section verbatim. No parallel shell, no duplicate home, and no
second computation path was introduced for any value already owned elsewhere in the app.
