# Phase goal-referee-iter-4 — User-Visible Changes

**Phase:** goal-referee-iter-4
**Date:** 2026-08-14
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration shipped zero new user-facing capability. Every changed production file is a
backend research/statistics module (`apps/backend/app/research/referee_stats.py`,
`apps/backend/app/research/referee_evidence.py`) plus their pytest suites; none is imported by any
frontend component, page, or MCP tool. Independently confirmed:
- `grep -rn "referee" apps/frontend/app apps/frontend/components apps/frontend/lib` returns zero
  matches — no frontend file references any referee module, route, or field.
- The MCP tool roster is unchanged at 20 tools (per this iteration's own DoD and the live
  deferred-tool listing available to this session) — no `referee`-named MCP tool exists yet.
- `git status --porcelain` shows only backend `.py` files and doc/report artifacts changed — zero
  files under `apps/frontend/`.

---

## What Changed in the Visible UI

None. No page, component, route, form, table, chart, or navigation element changed. The one
already-shipped route this iteration's diff touches, `GET /research/desk/referee/evidence`
(backed by `playbook_occurrence_readiness()`), is not called by any frontend code today — it is
exercised only by the backend pytest suite, exactly as before this iteration.

---

## What Old Behavior Changed

None visible to a user. Inside `permutation_test`'s exact-enumeration branch, a floating-point
accumulation bug is fixed so a p-value can no longer be reported as more statistically significant
than the method's own math allows — but nothing on any screen reads this function's output yet, so
no number, chart, or report a user can see is affected today.

Every field the `GET /research/desk/referee/evidence` route already served keeps its exact
existing value, byte-for-byte, on every fixture and on the real production corpus — this
iteration's one field addition (below) is purely additive.

---

## Not Visible Yet

- **The corrected statistics engine (`referee_stats.py`)** — `permutation_test`'s exact-enumeration
  p-value can no longer fall below its own mathematical floor, proven by a hand-verified minimal
  reproduction and large generated property sweeps (20,000+ cases, zero violations). No page, chart,
  or report calls this function yet; a later iteration (J-04) is the first planned caller.
- **`stale_basis_dates`** — `GET /research/desk/referee/evidence` (and the not-yet-routed
  `playbook_observations()`) now additionally report which dates, if any, were excluded from the
  readiness count because their newest Playbook record no longer matches the live detector
  configuration, instead of silently contributing nothing. On today's real data this list is always
  empty (`[]`) — no detector revision has happened this era — and no page renders this field
  regardless. A later iteration (J-09) is the first planned UI consumer.
