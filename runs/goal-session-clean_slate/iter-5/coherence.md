# Iteration 5 — Coherence Audit

**Iteration:** goal-clean_slate-iter-5
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

This iteration (J-05's Case Studies restore) is a visibility flip, not new work: `git diff
0fd54f658dcd8b3eed9fbab88b6f725ded2d2fb0 --stat` (harness/lockfile noise excluded) shows exactly
two files touched — `apps/frontend/app/structure/page.tsx` (2 hunks: `SHOW_CASE_STUDIES` `false`→
`true` at line 335, and one reinstated sentence in the `structure-framing` paragraph) and
`README.md` (an unrelated "Chart timeframe" documentation bullet, discussed below). No backend
file, no nav file (`app/meta.py`), no new component, and no new endpoint appear anywhere in the
diff — independently corroborated by this iteration's own `runs/goal-session-clean_slate/iter-5/
diff-vs-inventory-crosscheck.md` ("exactly one file: `apps/frontend/app/structure/page.tsx`... No
other `apps/` file is touched").

The restored Case Studies panel/drill-in reads from the pre-existing, byte-unchanged
`fetchSetups()`/`fetchSetupDetail()` functions in `apps/frontend/lib/api.ts` (lines 763, 790),
which target `GET /research/setups` and `GET /research/setups/{id}` — exactly the blueprint's
registered canonical source for "Touch events / setups." Neither `lib/api.ts` nor `setups.py`
appears in the diff; only the render-time boolean gate in `page.tsx` changed. No new displayed
value/entity was introduced — the iteration spec's own "Data-contract additions: None" is accurate.

`/structure` is already the blueprint's canonical home for Case Studies (the IA nav skeleton names
"case studies" explicitly under Structure's row), so restoring an existing, already-built section
on its existing page needs no new nav entry, no new route, and no shell change — confirmed by nav
being untouched in the diff.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Touch events / setups (Case Studies list + drill-in) | OK | `apps/frontend/lib/api.ts:763` `fetchSetups()` → `fetch(\`${API_BASE}/research/setups...\`)`; `apps/frontend/lib/api.ts:790` `fetchSetupDetail()` → `fetch(\`${API_BASE}/research/setups/${id}\`)`. Both unchanged by this diff. Matches `blueprint.md:56` ("Touch events / setups \| `setups.py` ... \| `GET /research/setups`"). Called from `apps/frontend/app/structure/page.tsx:1510` (`fetchSetups().then(...)`) and `:1592` (`fetchSetupDetail(selectedSetupId).then(...)`) — both pre-existing call sites, only their rendering gate (line 335) changed. |
| All other registered values (bands, edge cells, edge-report compute, PnL ledger, bars, levels, strategy registry, datasets, backtests, profiles, taxonomy, route/nav inventory, `config_fingerprint`) | OK | Zero touch — `git diff --stat` shows no backend file (`tradability.py`, `setups.py`, `edge_report.py`, `bars.py`, `levels.py`, `strategies.py`, `datasets.py`, `backtests.py`, `profiles.py`, `taxonomy.py`, `app/meta.py`, `config.py`) in the diff at all. |

No new displayed value/entity to classify under A4/A5 — the one visibility change surfaces an
already-registered value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Case Studies panel + drill-in restoration (`/structure`) | OK | `blueprint.md:28-30` already lists "case studies" as part of Structure's (`/structure`) description in the nav skeleton — the canonical home predates this iteration. `app/meta.py` (the single nav owner per `blueprint.md:16`) does not appear in the diff, confirming nav is unchanged: still exactly 2 top-level rows (Cockpit, Structure). The panel is a `<section>` inside the existing `/structure` page (`apps/frontend/app/structure/page.tsx:2339-2341`), not a new route — reachable in the same 1 click from the top nav as before; no parallel shell, no duplicate home. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md` (lines 51, 55, 56 at HEAD) still describes Case Studies as "currently withheld from
  view pending an operator decision" / "currently withheld from the Structure page pending an
  operator decision." This wording predates iter-5 (already present at the snapshot SHA, inherited
  from iter-3's `e224583` showcase commit — confirmed via `git show
  0fd54f658d...:README.md`), but this iteration's own `SHOW_CASE_STUDIES` flip now makes it stale.
  The readme-maintainer did touch `README.md` this iteration (a different, unrelated "Chart
  timeframe" dropdown bullet reflecting an earlier, previously-undocumented feature), but left these
  three now-inaccurate sentences in place. This is a documentation-prose issue, not a live-app
  IA/Data-Contract violation (README is not a rendered product surface), so it does not affect this
  verdict — flagged for the next README-maintainer pass to drop the "withheld... pending an operator
  decision" clause in all three spots now that the section renders again.
- No other coherence-relevant drift observed. Labels, endpoints, and formatting for the restored
  section match its pre-existing (era-5B/5C) implementation verbatim; nothing was rebuilt.
