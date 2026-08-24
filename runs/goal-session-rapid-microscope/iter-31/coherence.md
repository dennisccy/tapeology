# Iteration 31 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-31
**Date:** 2026-08-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Iter-31 (J-11) is scoped as "new readers only" of one already-registered Data Contract row
("Graduation states + export bundles", owner `micro_graduation.py` /
`micro_sealed_evaluation.py`, endpoint `GET /research/desk/micro/graduation`, registered since
era baseline). Confirmed against the actual diff, not just the spec's claim:

- `apps/backend/app/research/micro_routes.py` (the route module that owns
  `GET /research/desk/micro/graduation`, `micro_routes.py:692-719`) is **untouched** in this
  iteration's diff — no second computation path was added anywhere.
- The new MCP tool `desk_graduation` (`apps/backend/app/mcp/__init__.py:158,479-490`) is a
  static-path proxy entry pointing at the identical string `/research/desk/micro/graduation` —
  same canonical endpoint, no independent fetch/compute logic. `test_mcp_server.py`'s new
  byte-identical tests (`test_desk_graduation_tool_byte_identical_on_the_honest_empty_state` /
  `..._on_a_populated_state`, lines ~167-207) assert the tool's JSON equals the REST route's JSON
  exactly.
- The new frontend section (`GraduationSection` in `apps/frontend/app/desk/page.tsx:342-509`)
  fetches via `fetchDeskGraduation()` in `apps/frontend/lib/api.ts:583-604`, which calls
  `${API_BASE}/research/desk/micro/graduation` — the same canonical endpoint, no other route.
  `grep -rln "graduation" apps/frontend/` returns exactly three files (`api.ts`, `types.ts`,
  `desk/page.tsx`) — no parallel or duplicate fetch path anywhere else in the frontend.
- All rendered fields (`family_root_id`, `state`, `from_state`/`to_state`/`evaluated_at` on
  transitions, `dataset_id`/`verdict`/`n`/`evaluated_at` on sealed evaluations,
  `chain_verification.ok/failed_at_row/reason`) are read verbatim off the response body; the only
  transform applied is `formatDateTimeET(...)` (display formatting, not recomputation — explicitly
  allowed by the methodology's "re-format is fine" rule) and `JSON.stringify(...)` for the opaque
  per-row detail (matches the codebase's own established `screen_result`/raw-`fold_results`
  precedent for heterogeneous row shapes).
- The static `GRADUATION_REFEREE_HANDOFF_NOTE` copy string
  (`apps/frontend/app/desk/page.tsx:330-331`) is verified byte-identical, character-for-character,
  against the backend's `REFEREE_FUTURE_REVISION_SENTENCE` constant
  (`apps/backend/app/research/micro_graduation.py:170-176`) — confirmed by reading both strings
  directly — and is additionally guarded by a real counter-test
  (`test_desk_page_graduation_section_never_derives_a_second_computation_of_the_referee_note`,
  `test_desk_ui_guards.py:94-105`) that imports the backend constant and asserts it appears
  verbatim in the frontend source, so any future drift would fail the suite rather than silently
  diverge. This is a static label tied to a state token, not an independent computation of a
  served value — no violation.
- No new value/entity is introduced that isn't already in the Data Contract — this iteration adds
  readers of one existing row, nothing new to register.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Graduation states + export bundles (families/transitions/sealed_evaluations/chain_verification) | OK | `apps/frontend/lib/api.ts:589` fetches `GET /research/desk/micro/graduation`; `apps/backend/app/mcp/__init__.py:158` proxies same path; `apps/backend/app/research/micro_routes.py:692-719` (untouched, sole route) |
| `REFEREE_FUTURE_REVISION_SENTENCE` / `GRADUATION_REFEREE_HANDOFF_NOTE` static copy | OK (re-format/static label, not a second computation) | `apps/frontend/app/desk/page.tsx:330-331` vs. `apps/backend/app/research/micro_graduation.py:170-176`, guarded by `test_desk_ui_guards.py:94-105` |

## Information Architecture check

- New surface: a "Graduation" collapsible section on the already-registered `/desk` route,
  rendered as the next sibling directly below the shipped Validation Vault `<section>`
  (`apps/frontend/app/desk/page.tsx:548-558`). This matches the blueprint's IA table row exactly:
  "Graduation surface + MCP v7 (J-11) | `/desk` → Graduation (below Validation Vault) | Desk"
  and the nav-skeleton note ("Rapid Microscope ... Graduation (J-11, iter-31 ... renders BELOW the
  Referee sections") — no new page, no new route, no new top-level nav entry.
- No parallel shell: the section uses the same `DeskPage` component, the same
  `CollapsibleSection` wrapper (`id="graduation"`, `title="Graduation"`) every other Rapid
  Microscope section already uses — no independent layout/nav was introduced.
- Reachability: `/desk` is an existing top-level nav item (1 click), and the Graduation section is
  a same-page collapsible sibling of the other four sections (no additional click to reach the
  section header; expanding it is the same one-toggle pattern already used by Readiness / Scout
  Ledger / Walk-Forward / Validation Vault) — within the blueprint's ≤2-click bound. The nav
  skeleton itself (`app/meta.py` `UI_ROUTES`) is untouched this iteration, consistent with the
  blueprint note "unchanged this era."
- No duplicate home: Graduation had zero prior UI surface (the golden-gap note in
  `runs/goal-session-rapid-microscope/state/golden-gaps` and the era-baseline IA row both confirm
  it was previously keyless/automated-only); this is a first-time, single UI home for it, not a
  second page for an entity that already had one.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` → Graduation section | OK | `apps/frontend/app/desk/page.tsx:548-558` (section placement); blueprint IA table + nav-skeleton block (`runs/goal-session-rapid-microscope/state/blueprint.md:24-31,47`) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The iteration is a clean, narrowly-scoped "new readers of an already-registered
  endpoint" addition: no new computation module, no new route, no new nav entry, and the one
  static copy string that could have drifted (the referee-handoff note) is both verified
  byte-identical by direct inspection and mechanically guarded by a counter-test that imports the
  backend constant. The blueprint itself was updated additively (a dated iter-31 note appended,
  the IA table's already-existing Graduation leaf and Data Contract row cross-referenced) with no
  nav-skeleton or Data Contract shape change — consistent with the iteration spec's own
  "Blueprint conformance" and "Data-contract additions: None" claims, both independently confirmed
  against the diff rather than taken on trust.
