# Iteration 4 — Coherence Audit

**Iteration:** goal-playbook-iter-4
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

The blueprint registers exactly one row this iteration touches — "Playbook records" — owner
`app/research/desk_playbook.py` + `desk_playbook_detect.py`, endpoint `GET /research/desk/playbook`.
The iter spec's own "Data-contract additions" section states this iteration adds new fields
*within* that already-registered row (no new owner, no new endpoint) — verified directly against
the diff.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Playbook records — new `jbe`/`dbi` geometry (`jump_mbr`, `base_range_mbr`, `base_bars`, `base_flatline`, `base_lows_ascending`, `ladder_step_ratio`) | OK | Computed in `apps/backend/app/research/desk_playbook_detect.py:399-436` (`_find_one_continuation`), the registered detect module; wired into the registered walk at `apps/backend/app/research/desk_playbook.py:463-472` (`detect_jbe`/`detect_dbi` calls). Served on the unchanged `GET /research/desk/playbook` payload (no `desk_routes.py` diff). |
| Playbook records — new `cup_handle` geometry (`cup_bars`, `cup_depth_mbr`, `handle_retrace_frac`, `handle_duration_frac`, `cup_optimal`, `handle_duration_desirable`, three RVOL medians) | OK | Computed in `desk_playbook_detect.py:659-681` (`detect_cup_handle`), same registered module; wired at `desk_playbook.py:474-478`. Same endpoint, same owner. |
| Measurement rail (`forward`, `invalidation_breached`, seeded baseline anchors) applied to the three new setups | OK | `desk_playbook.py:634-668` reuses the SAME `_measure_signal`/`_baseline_seed`/`_draw_anchor_indices`/`_measure_from` call sites J-01/J-02 shipped, now looped over `detected_signals` instead of a single `signal` — no second implementation. `desk_forward.py` has zero diff (confirmed: `git diff <sha> --stat -- desk_forward.py` empty). |
| Shared primitives `consolidation_range`, `swing_pivots`, `vertical_move` | OK | Imported at `desk_playbook_detect.py:227-234`, called (not reimplemented) at `desk_playbook_detect.py:310` (`consolidation_range`) and `:549` (`swing_pivots`). `desk_playbook_features.py` has zero diff (confirmed empty `--stat`). |
| Frontend rendering of all new `signal.geometry.*` fields | OK — re-format only | `apps/frontend/app/desk/page.tsx:1447-1478` reads `geometry.jump_mbr`, `.base_range_mbr`, `.cup_depth_mbr`, etc. verbatim from the already-fetched payload via `fmt()`; no client-side arithmetic combining two fields (guard-tested: `apps/backend/tests/test_desk_ui_guards.py:1343-1361` extends `_PRICE_ARITHMETIC_FIELDS` and asserts the pattern catches injected arithmetic on every new field). |
| `ladder_step_ratio` (derived value: `jump_mbr / previous_jump_mbr`) | OK | Computed ONCE server-side at `desk_playbook_detect.py:372`, served as a plain field, read verbatim on the frontend — not re-derived client-side. |
| Nav/route/endpoint surface (`config_fingerprint`, MCP tool count, `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`, `levels.py`, `config.py`, `app/mcp/__init__.py`) | OK — zero diff | Confirmed via `git diff <sha> --stat` against each path: empty for all seven, matching the iteration's own OUT-OF-SCOPE claims. |

No new function computes an already-registered value a second way; no new UI surface fetches from
a non-canonical endpoint; every new field is a genuinely new addition inside the one row the
blueprint already names as this era's target (`blueprint.md`'s own text: "J-04/J-05/J-06 (each adds
a detector family to the same shared detect module — signature moves, endpoint/owner do not)").

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Three new setup types (`jbe`, `dbi`, `cup_handle`) rendering inside the existing Playbook Signals section, `/desk` | OK | No new route, no new page, no nav edit. `apps/backend/app/meta.py` (`UI_ROUTES`, nav source) and the frontend nav component have zero diff (confirmed empty `--stat`). The three new render branches (`apps/frontend/app/desk/page.tsx:1447-1478`) live inside `PlaybookSignalDetail`, the same component that already renders the opening-range-break geometry line — no parallel shell, no second "signals" surface. |

Blueprint's IA already names this exact target shape ("Playbook Signals — ... extended visibly by
the detector families J-04/J-05/J-06"), so no `blueprint.md` edit was required or made, matching the
iter spec's own "Blueprint conformance" note.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Two new constants (`PLAYBOOK_BASE_FLATLINE_MAX_MBR`, `PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC`)
  promote spec-prose thresholds to named constants, per the module's own docstring
  (`desk_playbook.py:44-49`) — this is flagged by the developer as needing "the same owner ruling"
  as the prior `PLAYBOOK_OR_MIN_1M_BARS` precedent. This is a spec-conformance/process question, not
  an IA or Data Contract violation (no new owner, no new endpoint, no duplicate value) — noted for
  the record, does not block.
- The three cup-and-handle RVOL median field names (`cup_middle_third_rvol_median`,
  `cup_outer_third_rvol_median`, `handle_rvol_median`) are the decomposer's own proposed names
  (spec §3.6 names the quantities in prose only) — they are correctly and exclusively registered in
  this iteration's Data-contract additions, so no unregistered-value WARN applies.
