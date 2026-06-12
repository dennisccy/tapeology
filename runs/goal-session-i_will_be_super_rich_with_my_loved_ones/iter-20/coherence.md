# Iteration 20 — Coherence Audit

**Iteration:** goal-i_will_be_super_rich_with_my_loved_ones-iter-20
**Date:** 2026-06-12
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 15 — thesis projection (`management_stance`, `distance_to_invalidation`, `open_r` additive keys) | OK | `apps/backend/app/research/monitor.py` — served exclusively via the single `build_projection` function; no second endpoint, no second computation path |
| Row 24 — taxonomy (management-stance display copy) | OK | `apps/backend/app/research/taxonomy.py:taxonomy_payload()` — additive keys added to the single existing `GET /research/taxonomy` response; no new endpoint |
| Row 25 — management stance (stance half build-out) | OK | `apps/backend/app/research/stance.py:StanceEvaluator` is the single computation owner; driven from `monitor.py`; served only via row 15's single `build_projection` — no second computation path, no second endpoint |
| Row 27 — R basis (fifth registered consumer) | OK | `apps/backend/app/research/stance.py:compute_position_readouts` calls `from .marks import r_basis` (the single `r_basis()` definition in `marks.py:27`) — one formula, one owner; not a second implementation |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Management-stance block on `/` thesis strip (J-53) | OK | No new route; `ThesisStrip.tsx` is the existing component. Blueprint canonical home is `/` thesis strip, nav section Cockpit — confirmed in blueprint IA feature-home row "J-38–J-46, J-49, J-50, J-52, J-53 … `/` thesis strip". Reachable in 1 click from persistent top bar. No nav-skeleton change. |

## Blocking violations (FAIL only)

None

## Advisory notes (non-blocking)

- The `journaled measurement, R = |entry − invalidation|` caption string at `apps/frontend/components/ThesisStrip.tsx:220` (new `ManagementStanceBlock`) is hardcoded as a literal rather than read from `taxonomy.stance_readout_caption` (which the backend serves). The identical literal appears at lines 345 and 633 in pre-existing code (realized-R block) — this iteration follows the carry-forward pattern rather than introducing new drift. The taxonomy-driven path is already wired: the `ResearchTaxonomy` type has `stance_readout_caption?` and the strip reads it for other copy. A future copy-sweep (J-66) should consolidate all three hardcoded instances to read from taxonomy. Not a FAIL: the string is identical in both places; no displayed value is wrong.
