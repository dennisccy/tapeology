# Iteration 6 — Coherence Audit

**Iteration:** goal-playbook-iter-6
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iteration 6 (J-06) adds three detectors — `range_trade`, `double_top`, `double_bottom` — plus 10
new geometry fields, all landing on the blueprint's already-registered "Playbook records" row
(`runs/goal-session-playbook/state/blueprint.md` Data Contract table, row 1: owner
`app/research/desk_playbook.py` + `desk_playbook_detect.py`, endpoint
`GET /research/desk/playbook`). Verified against the diff (`git diff
d0dded1436081344a2f59fbec64cbf5c2e54be6f`):

- `apps/backend/app/research/desk_playbook_detect.py` — new `detect_range_trade` /
  `_range_trade_side` / `_zone_held` (:1030-1415) and `detect_double_top` / `detect_double_bottom` /
  `_find_double_extreme` (:1418-1648) call ONLY existing primitives (`zone_touches`,
  `swing_pivots`, `_rvol`, `_market_block`, `_spike_into_trigger_verdict`, `vertical_move`) already
  owned by `desk_playbook_features.py`/`desk_playbook_detect.py` — confirmed zero diff to
  `desk_playbook_features.py` (`git diff … -- apps/backend/app/research/desk_playbook_features.py`
  is empty), so no primitive was re-implemented a second way.
- `apps/backend/app/research/desk_playbook.py` — the three new detectors are wired into the SAME
  per-member `compute_playbook` walk (:669-690) beside the existing five, `PLAYBOOK_SETUPS`
  extended in place (:157-159), `PLAYBOOK_REGISTER` widened in place (:176-179). No new function,
  module, or endpoint was added — `git diff` shows zero new `def`/route/`APIRouter` lines, and
  `apps/backend/app/research/desk_routes.py` has zero diff against the snapshot SHA (confirmed).
- `apps/frontend/lib/types.ts` — 10 new optional fields added to the existing
  `DeskPlaybookGeometry` interface (:1519-1530); no new type, no new fetch target.
- `apps/frontend/app/desk/page.tsx` — two new conditional render branches in the existing
  `PlaybookSignalDetail` component (:4645-4668) display the new fields via the existing `fmt()`
  formatter, verbatim from `signal.geometry`. `apps/frontend/lib/api.ts` has zero diff (confirmed)
  — no new fetch call, no new endpoint reference. The counter-tests in
  `apps/backend/tests/test_desk_ui_guards.py` (`_PRICE_ARITHMETIC_FIELDS` extended :168-186,
  `test_desk_page_price_arithmetic_guard_catches_range_family_field_arithmetic` added :322-337)
  positively assert the renderer performs no client-side arithmetic on the new numerics.
- The J-06-specific guard added at `apps/backend/tests/test_desk_playbook_guards.py:523`
  (`test_compute_playbook_calls_neither_compute_tradability_nor_compute_levels`, a call-counting
  stub, not a source-scan regex) enforces the blueprint's own explicit anti-duplication clause ("the
  `desk_playbook` walk performs ZERO `compute_tradability`/`compute_levels` calls" — blueprint
  Data Contract, line 97-98). `git diff` confirms zero diff to `levels.py`.

No new module, endpoint, or client-side recomputation was introduced. The new fields are
re-formats of one canonical source, which is not a violation per the skill's Part A.3.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Playbook records (now incl. `range_trade`/`double_top`/`double_bottom`) | OK | `apps/backend/app/research/desk_playbook.py:669-690` (same walk, same endpoint `GET /research/desk/playbook`) |
| `geometry.range_width_mbr`, `low_zone_touches`, `high_zone_touches`, `crossed_midrange`, `absorption_bar_present` | OK | `apps/backend/app/research/desk_playbook_detect.py:1030-1415` (computed once, in the detector); `apps/frontend/app/desk/page.tsx:4648-4655` (rendered verbatim via `fmt()`) |
| `geometry.tops_gap_mbr`, `tops_separation_bars`, `valley_depth_mbr`, `nominal_risk_mbr`, `second_top_rvol_vs_first` | OK | `apps/backend/app/research/desk_playbook_detect.py:1418-1648`; `apps/frontend/app/desk/page.tsx:4660-4667` |
| `compute_tradability` / `compute_levels` (unchanged owners, must never be called from the playbook walk) | OK | zero diff to `levels.py`/`tradability` call sites; new guard `apps/backend/tests/test_desk_playbook_guards.py:523` |

## Information Architecture check

No new page or route. The iteration spec ("UI surface changes: No new section") and the ui-surface
map (`reports/phase-goal-playbook-iter-6-ui-surface-map.md`) both confirm the change is two new
conditional geometry-line branches inside the already-shipped `PlaybookSignalDetail` component on
the existing `/desk` route, plus two copy-widening spots in the same file. `apps/frontend/app/desk/page.tsx`
diff (`:4648-4655`, `:4660-4667`, `:5020-5022`, `:5117-5123`) confirms no new top-level component,
no new router entry, no new nav element. `/desk` already has its canonical nav entry per the
blueprint's IA (unchanged this era) — the three new setup types simply extend the existing
Playbook Signals section's setup-type range, exactly as the blueprint's "Feature / journey homes"
table names ("J-06 Range family … lands on J-03's section, `/desk`").

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `range_trade`/`double_top`/`double_bottom` geometry display, `/desk` Playbook Signals section | OK | `apps/frontend/app/desk/page.tsx:4648-4667` (same component, same route); no nav file touched — `NavBar.tsx`/`app/meta.py` `UI_ROUTES` have zero diff |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The register/blurb widening (`PLAYBOOK_REGISTER`, the two `/desk` copy spots) was applied
  in the same commit as the setup-family extension, per the iter-4/iter-5 lesson this spec cites —
  no drift between the served register text and the actual detector set observed.
- All 10 new fields were pre-registered at iteration 0 in the blueprint's Data Contract table
  ("Ships at" column already named J-06 landing this signature move on the same row), so there is
  no unregistered-value note to raise.
