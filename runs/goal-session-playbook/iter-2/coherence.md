# Iteration 2 — Coherence Audit

**Iteration:** goal-playbook-iter-2
**Date:** 2026-08-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration is backend-only (`Frontend Present: no`, confirmed by zero diff to `apps/frontend`).
It ships into the three rows the blueprint pre-registered at baseline, each explicitly marked
"Ships at: J-02". All three land on exactly their registered owner module and endpoint; no
duplicate computation, no non-canonical source, and no diff to any frozen rail module.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Playbook records (signals + `forward`/`invalidation_breached`/`baseline_anchors`/`summary`) | OK | Extended in place in the SAME registered owner `apps/backend/app/research/desk_playbook.py` (`compute_playbook` :~330, `_measure_signal` :158, `PlaybookStore.record` :760), served verbatim by the SAME registered endpoint `GET /research/desk/playbook` (`desk_routes.py:1024`, unchanged this iteration) |
| Playbook compute progress | OK | New owner `apps/backend/app/research/desk_playbook_compute.py` (`DeskPlaybookComputeManager`), served by the SAME registered endpoint shape `POST/GET/POST-cancel /research/desk/playbook/compute` (`desk_routes.py:449-528`) — matches the blueprint row exactly |
| Playbook run ledger | OK | New owner `apps/backend/app/research/desk_playbook_log.py` (`PlaybookRunStore`/`record_playbook_run`), served by the SAME registered endpoint `GET /research/desk/playbook/runs` (`desk_routes.py:531-555`) — matches the blueprint row exactly |
| Rail measurement math (horizons, dual-MDD, truncation, seeded baseline draw) | OK — imported, not re-implemented | `desk_playbook.py:24-34` imports `_measure_from`, `_draw_anchor_indices`, `_avg_cell`, `_collect_measures`, `DESK_FORWARD_MAX_TOUCHES_PER_ROW`, `DESK_FORWARD_MEASURE_KEYS`, `DESK_FORWARD_BASELINE_SEED`, `DESK_FORWARD_HORIZONS_MINUTES`, `DESK_FORWARD_HORIZON_MEASURES` from `desk_forward.py` and calls them verbatim in `_measure_signal` (:158-177) and `compute_playbook`'s pooling block (:279-294). Confirmed by `git diff <snapshot> -- apps/backend/app/research/desk_forward.py` = empty (0 lines) — the rail file itself carries zero diff this iteration, matching TC-22/OUT-OF-SCOPE's own claim |
| `invalidation_breached` (new field, same "Playbook records" row) | OK — genuinely new logic, correctly NOT rail-owned | `_invalidation_breached` (`desk_playbook.py:113-155`) is a playbook-only concept (did price trade through the book's own structural level) that has no equivalent in `desk_forward.py`'s registered rail — it is computed OUTSIDE `_measure_from` per spec and does not touch the rail's served shape. Registered under the same "Playbook records" row per this iteration's own Data-contract-additions section, not a duplicate of any existing contract value |
| `compute_tradability`/`compute_levels`/`levels._swing_pivots` (blueprint's "different owners" boundary) | OK — zero calls | `grep -rn "compute_tradability\|compute_levels\|_swing_pivots"` across every changed/new playbook module returns only one hit: a doc-comment in the unchanged (pre-existing, non-diffed) `desk_playbook_features.py` describing a mirrored-but-not-called convention — no production call site anywhere in this iteration's diff |

One minor internal-implementation observation, noted under Advisory below (not a contract violation:
it duplicates a two-line directional-sign mapping, not the registered rail math itself).

## Information Architecture check

No new page/route/feature ships this iteration — `Frontend Present: no` is confirmed structurally
(`git diff <snapshot-sha> --stat -- apps/frontend` returns empty) and the nav skeleton
(`Cockpit /`, `Structure /structure`, `Desk /desk`, driven by `app/meta.py` `UI_ROUTES`) is
untouched. The two new HTTP endpoints (`/research/desk/playbook/compute`,
`/research/desk/playbook/runs`) are API-only surfaces with no UI route yet — the blueprint's own IA
table explicitly defers any UI for this work to J-03 ("no standalone UI until J-03"), so there is
nothing to check for nav placement this iteration.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new UI surface this iteration)* | N/A | `apps/frontend` diff is empty against the snapshot SHA |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `desk_playbook.py`'s `_measure_signal` (:170) and `compute_playbook`'s pooling block (:281) each
  independently write `sign = 1.0 if signal["side"] == "long" else -1.0` rather than importing
  `desk_forward.py`'s existing `_side_sign(side)` helper (`desk_forward.py:443`), which computes the
  identical mapping. This is not a Data Contract violation — the two-line sign lookup is not itself
  a registered/displayed value, and the actual measurement math (horizons/MDD/truncation/seed) is
  correctly imported everywhere — but it is a small, easy consolidation the next iteration touching
  this file could pick up: import `_side_sign` from `desk_forward.py` and call it in both spots
  instead of re-deriving the same two branches twice in one module.
