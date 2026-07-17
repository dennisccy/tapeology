# Iteration 3 — Coherence Audit

**Iteration:** goal-fast_wall-iter-3
**Date:** 2026-07-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

J-03 ships exactly the ONE accelerator blueprint.md's "Rebuildable accelerators" list pre-registered
at baseline verbatim ("the per-run `_StructureArmMemo` (in-memory, one instance per backtest run —
never persisted)", `blueprint.md:69`), and touches no canonical-value owner's served bytes. Traced
each row against both the registered source and the diff (`git diff b059adef… -- apps/backend/app
apps/backend/tests`, 6 files, 643 insertions / 11 deletions, zero route/config/frontend files).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Raw levels + A/B/C zones (owner: `levels.py`, served by `GET /research/levels`) | OK | `compute_levels`'s and `compute_confluence_zones`'s bodies are byte-unmodified — the levels.py diff is a pure append after the existing `compute_levels` return (`levels.py:322` old-file end); zero lines removed anywhere in the file. New `level_change_points` (`levels.py:327-364`) computes no level/zone value itself; it enumerates bar epochs only, reusing the EXISTING `_select_one_series_per_timeframe`/`PRIOR_PERIOD_TIMEFRAMES`/`_PERIOD_SECONDS` (none redefined in the diff — confirmed pre-existing) rather than re-deriving series selection. |
| Tradable level map / basis (owner: `tradability.py`, served by `GET /research/tradability`) | OK | `compute_tradability`'s and `_resolve_basis`'s bodies are byte-unmodified — same pure-append pattern (addition after old-file line 380); zero lines removed. New `basis_day_key` (`tradability.py:385-397`) computes nothing about tradability; it returns `_session_date(as_of_epoch).isoformat()` — the SAME pre-existing date helper `_resolve_basis` already uses, not a second derivation. |
| Per-run `_StructureArmMemo` (pre-registered accelerator, in-memory, never persisted) | OK — matches registration field-for-field | `apps/backend/app/research/backtests.py:396-441`. `levels_at` (`:428-434`) and `tradability_at` (`:436-441`) are pure memoization: on a cache miss each calls straight through to the SAME canonical owner (`compute_levels` at `:432`, `compute_tradability` at `:440`) — no reimplementation, no second computation path. Exactly ONE instance built per run inside `_structure_tape_trades` (`:693`) and inside `_structure_tape_map_trades` (`:805`, a separate instance, correctly scoped to its own run) — never shared, never written to disk or any store. |
| Non-canonical source check (new UI/consumer reading the value another way) | OK — N/A, no new consumer | `_structure_tape_arm` (`:761-763`) and `_structure_tape_map_arm` (`:892-894`) still fall through to the literal `compute_levels(`/`compute_tradability(` owner calls when `memo=None` — the two existing source-introspection guard tests (`test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner`, `test_structure_tape_map_reads_tradability_never_recomputes_levels_or_zones`) that pin these literal substrings are untouched: the new 376-line test block is appended AFTER the last existing guard test (hunk header `@@ -1506,3 +1508,377 @@ def test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner`), and a whole-diff scan for removed lines (`git diff … \| grep '^-'`) found exactly one, an import-statement widening in `test_tradability.py` (`-from app.research.tradability import RESISTANCE, SUPPORT, compute_tradability` → `+...RESISTANCE, SUPPORT, basis_day_key, compute_tradability`), not a test-body edit. |
| New displayed value / field | N/A — none added | Iteration spec's own "New information displayed: None" / "Data-contract additions: None" (`docs/phases/goal-fast_wall-iter-3.md`) is corroborated by the diff: `level_change_points` and `basis_day_key` are private helpers consumed only by `_StructureArmMemo` inside `backtests.py` — never returned by any route, never touched by `routes.py`, `edge_report.py`, or any frontend file (all show zero diff in `git diff --stat` against the snapshot SHA). |

No new function anywhere in the diff independently recomputes levels, confluence zones, or the
tradable map; no new UI surface fetches either value from a non-canonical endpoint (there is no new
UI surface at all this iteration). `GET /research/levels` and `GET /research/tradability` remain the
ONE serving endpoints for their respective values, unchanged.

## Information Architecture check

`Frontend Present: no` (iteration spec header), confirmed by
`reports/phase-goal-fast_wall-iter-3-ui-surface-map.md` ("Backend-only phase... No UI surfaces
affected") and by the repo-wide diff: `git diff b059adef… --stat` (noise-excluded) touches exactly 6
files, all under `apps/backend/app/research/` or `apps/backend/tests/` — no route, store, config, or
frontend file. `blueprint.md`'s Feature/journey homes table already registers J-03 as "no dedicated UI
panel — accelerates the backtest sweep the J-04 button triggers | Structure (cross-cutting)"
(`blueprint.md:38`); this iteration ships nothing that contradicts that — no page, panel, or nav entry
is added, moved, or duplicated.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK — N/A | No nav/router/frontend file appears anywhere in the diff or `git status`; `blueprint.md`'s pre-registered "cross-cutting, no dedicated UI panel" home for J-03 is unaffected. |

`blueprint.md` itself is untouched this iteration (zero diff, confirmed via `git diff --stat`) —
correct, since the spec's own "No blueprint edit" note is accurate: the pre-registered accelerator row
already matches this diff's `_StructureArmMemo` field-for-field.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- This is a clean backend-accelerator iteration with zero product surface delta, exactly as scoped:
  the entire diff is confined to `levels.py`, `tradability.py`, `backtests.py`, and their three test
  files — no route, store, config, or frontend file touched (mechanically confirmed, not just
  asserted by the spec). Nothing for a future iteration to consolidate.
- The blueprint's "every accelerator ships with a determinism/equivalence test proving byte-identity"
  requirement is addressed at the specification level by TC-5 through TC-10 (memoized-vs-`memo=None`
  byte-identity, both named memo-bust legs, both counting spies) — I did not execute the suite myself
  (outside this gate's scope; that is the reviewer/auditor's job), but the diff's shape (pure appends
  beside frozen function bodies, guard tests structurally untouched, memo falling through to the same
  canonical calls) is consistent with what those tests would need to hold.
