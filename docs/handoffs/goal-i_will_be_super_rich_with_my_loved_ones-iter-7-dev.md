# goal-i_will_be_super_rich_with_my_loved_ones-iter-7 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-7
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

J-50 — user-facing thesis resolution (the only feature work; J-46/J-41 are re-capture-only, no
code change — see Known Issues).

- **New endpoint `POST /research/thesis/{id}/resolve`** (`app/research/routes.py`):
  - Body `{resolution: "played_out" | "abandoned"}` ONLY.
  - `404` unknown thesis id.
  - `422` if `invalidated` or `expired` is requested (system-owned resolutions) OR an unknown enum —
    explicit messages, nothing mutated.
  - `409` if the thesis is already resolved (any terminal status) — idempotent refusal, NO duplicate
    timeline event (a double-click yields one resolution + one 409).
  - `409` if `abandoned` is requested for an ENTRY-marked thesis (anti-survivorship). The entry-mark
    UI is J-52; the guard is enforced at the API/store level and unit-proven by inserting an action
    row directly.
  - On success: routes the resolution through ONE store function (`resolve_thesis_with_event`) so a
    later iteration can compute grades/execution checks "once here" (Data-Contract row 19) without a
    second path; the function flips the terminal status AND appends ONE final timeline event
    (logical + wall timestamps) ATOMICALLY — prior verdict events are never edited (append-only). It
    then detaches the live monitor so no verdict event is appended after resolution, and the active
    projection clears (the strip returns to the declare affordance; a redeclare on the same ticker
    succeeds with no 409). Returns the resolved projection (status + `resolved_logical_ts` +
    `resolved_wall_ts`).
- **Store additions** (`app/research/store.py`):
  - `resolve_thesis_with_event(thesis_id, status, event)` — atomic status-flip + appended final
    event in one `BEGIN IMMEDIATE` writer transaction (mirrors the existing
    `insert_thesis_with_event` declaration path).
  - `insert_action(ActionRecord)` / `get_actions(thesis_id)` / `has_entry_mark(thesis_id)` + a new
    `ActionRecord` dataclass — minimal action-row support so the entry-marked-refuses-abandon guard
    is provable now (the full entry-mark UI/endpoint is J-52). No schema change: the `actions` table
    already existed in the v2 schema.
- **Monitor addition** (`app/research/monitor.py`):
  - `resolve_by_user(resolution)` — detaches verdict evaluation after a user resolution
    (`_resolved=True`, `_resolution=<resolution>`). The hot-path `_evaluate_verdict` already
    early-returns while `_resolved`, so no verdict event is appended after resolution; the existing
    projection logic returns `None` for `played_out`/`abandoned` (a user resolution returns the strip
    to idle, distinct from the system-owned `invalidated` terminal treatment, which stays visible).
- **Frontend** — see `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-7-frontend.md`.

NO schema migration (the `theses.status` column and `actions` table already exist at schema v2).
NO engine/classifier/provider change. NO grading/execution-check computation (J-54/J-56 scope) —
only the resolve path is shaped so they can be added there later.

## Files Changed

- `apps/backend/app/research/routes.py` -- new `POST /research/thesis/{id}/resolve` route + `ResolveRequest` model + resolution-ownership constants.
- `apps/backend/app/research/store.py` -- `ActionRecord`, `resolve_thesis_with_event`, `insert_action`, `get_actions`, `has_entry_mark`.
- `apps/backend/app/research/monitor.py` -- `resolve_by_user(resolution)` (verdict-evaluation detach).
- `apps/backend/tests/test_research_resolve.py` -- NEW: full resolve route matrix (happy paths, slot-frees-up, monitor detach, 404/409/422, entry-marked-refuses-abandon).
- `apps/backend/tests/test_research_store.py` -- store-level resolve/action tests.
- `apps/frontend/components/ThesisStrip.tsx` -- two resolve controls (Played out / Abandon) on the active strip + inline error handling.
- `apps/frontend/lib/api.ts` -- `resolveThesis(thesisId, resolution)` client.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **383 passed, 1 skipped** (baseline was 369 passed / 1 skipped — +14 new tests; no
regressions). Observer-equivalence + verdict-engine suites stay green.

Command: `cd apps/frontend && NEXT_DIST_DIR=.next-dev-check npx next build` (isolated dist dir,
never the live dev server's shared `.next`)
Result: Compiled successfully + type-check clean. (Throwaway dist dir removed; `tsconfig.json` and
`next-env.d.ts` reverted to committed state so the change stays surgical.)

## Live verification (fresh backend, not mocked)

Started a fresh uvicorn (port 8791, temp journal DB) AFTER dev completed and exercised the full
endpoint matrix live; all confirmed:
- **Taxonomy freshness (the iter-6 patch is on disk):** `frozen_statements("failed_move_fade",
  "long")[0]` has `params.states == ["bid_absorption"]`. This is the code identity the QA canary
  must verify (note: the *public* `GET /research/taxonomy` payload exposes statement `text`+`kind`
  but NOT `params` — QA should confirm the canary against the frozen-statement template, e.g. via
  the J-46 confirming-during-bid_absorption behaviour, since `states_long` is not in the public
  payload).
- watch SIM-BUYER → buyer_control; declare trend_continuation/long.
- `invalidated`/`expired`/unknown → 422; `played_out` → 200 with `resolved_logical_ts=21.0` +
  `resolved_wall_ts`; second resolve → 409 (no duplicate event); `active?ticker=` → `null`; journal
  timeline `["pending","played_out"]`; unknown id → 404.
- redeclare on the same ticker → 200 (slot freed); directly-inserted entry action → `abandoned`
  refused 409 ("an entry-marked thesis cannot be abandoned") while `played_out` still → 200.

Backend process killed and temp DB removed after verification; no leftover servers or listening
ports.

## Known Issues

- **J-46 and J-41 require NO code change** — the iter-6 fixes are already on disk and unit-proven
  (verified above: the `failed_move_fade/long` statement template targets `bid_absorption`, and the
  monitor's `directional_impact` is direction-aware/adverse-side). Their target status flips on
  clean pixels against a CANARY-VERIFIED FRESH backend. Per the spec: if a re-capture against a
  fresh, canary-verified server STILL shows the pre-fix behaviour, that is a real code defect to
  report honestly — do not retry into a green.
- **QA canary note:** the spec's canary phrasing (`states_long=["bid_absorption"]`) refers to the
  internal frozen-statement template, not a field on the public `GET /research/taxonomy` response
  (which omits `params`). The code-identity proof is the `frozen_statements` template (confirmed on
  disk) and is observable behaviourally via J-46 (confirming during bid_absorption). QA should still
  (re)start the backend after dev and confirm freshness before any capture.
- **No `/journal` page yet** — the "journal row appears" clause of J-50 is verified via the existing
  `GET /research/journal/{id}` REST read (recorded in the QA report), not a `/journal` UI (J-55).
- **No entry-mark UI** — the entry-marked-refuses-abandon guard is API/store-level and unit-proven
  only (J-52 adds the UI).
- **Carry-forward (not this iteration):** the harness halts at `qa_complete` for FULL iterations
  (audit/closure don't run) — open since iter-4/5. This lean cycle sidesteps it; it must be fixed
  before the next FULL iteration is dispatched.
