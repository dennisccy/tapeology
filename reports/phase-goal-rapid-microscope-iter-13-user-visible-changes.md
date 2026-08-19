# Phase goal-rapid-microscope-iter-13 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-13
**Date:** 2026-08-19
**Written by:** ui-impact-analyst

---

## Summary verdict

**No user-visible changes shipped this iteration.** This is a backend-only correctness fix with
zero frontend files touched (`git status --porcelain apps/frontend/` returns empty) and zero
production call sites for the function it corrects. `Frontend Present: yes` is declared in the
plan solely to trigger the mechanical browser-QA regression lane, not because any page, control,
or displayed value changed. This is confirmed independently below, not merely asserted from the
dev handoff — see "Why this is provably invisible."

---

## What Users Can Now Do

None. `vault.recover_shard_ledger` (the function this iteration corrects) is an operator-invoked
recovery routine with no route, no button, and no CLI wired to it. There are zero recording plans
registered and no `micro_vault` directory on disk in the real `.data` store, so the code path this
iteration touches has never run in production and has nothing to act on today.

---

## What Changed in the Visible UI

None. No page, component, table, form, chart, or navigation element changed. The three existing
routes (`/` Cockpit, `/structure` Structure, `/desk` Desk) are unmodified.

---

## What Old Behavior Changed

None visible. The underlying Python function's *internal* behavior changed substantially (see
below), but nothing a user can reach through the app renders, computes, or is gated by that
function today.

For context (not user-visible, but worth recording so a later reviewer understands what actually
moved): `vault.recover_shard_ledger`'s recovery logic went from a two-way split (proven-complete /
mark-prefix-only) to, briefly during this same iteration's first dev pass, a three-way split
(proven-complete / named-but-unverified-union-marking / cannot-be-named-halt) — then, after a
failed code review found that the middle branch could be tricked by a same-row-count
"reconstruction" naming a fabricated dataset, the owner ruled recovery **halt-only**: either a
reconstruction hash-matches the tail anchor byte-for-byte, or the vault refuses to resume at all.
The `exposure_unknown` shard state that the deleted middle branch was the only producer of was
removed from the module's vocabulary entirely (`sealed` / `assigned` / `exposed` are the only three
states now). None of this is reachable from any page.

---

## Not Visible Yet

- **`vault.recover_shard_ledger`'s corrected halt-only recovery logic** — hardens the vault against
  a genuine data-loss/tampering scenario (a destroyed ledger row silently reappearing as an
  ordinary never-sealed dataset), but has no serving endpoint, CLI, or button. It runs only when an
  operator calls it directly from Python during an incident.
- **The vault's own read-only surface, `GET /research/desk/micro/vault`, is unchanged** and
  continues to refuse to answer while a logbook is damaged — this route existed before this
  iteration and nothing about its served shape changed.
- **`seal_shard`/`assign_shard`/`expose_shard`'s docstring clarification** (their corruption
  gating is scoped to their own shard ledger only, by design) — documentation only, zero behavior
  change, zero production call sites.
- **`micro_routes.py`'s `get_tick_recorder_compute` docstring fix** — corrects stale prose
  (`trades_total`/`quotes_total` → the actually-served `trades_total_bucket`/`quotes_total_bucket`).
  The route's real JSON response (`_progress_view`) is byte-unchanged; only the docstring was wrong
  before.

---

## Why this is provably invisible (not just asserted)

Verified directly against the source during this analysis, independent of the dev handoff's own
claims:

1. `git status --porcelain apps/frontend/` returns nothing — the only files this iteration touched
   are `apps/backend/app/research/vault.py`, `apps/backend/app/research/micro_routes.py`, and two
   test files (`test_vault.py`, `test_tick_recorder.py`).
2. The one column in the shipped UI whose name sounds related — the "Exposure state" column in
   `/desk`'s "Legacy Tick Shards" table (part of the already-shipped Microscope Readiness section)
   — is **not** a live read of `vault.py`'s per-shard state at all. `micro_readiness.py:424` sets
   it to the hardcoded constant `EXPOSURE_STATE_EXPLORATORY = "exploratory"` for every row,
   unconditionally, by deliberate design (the era's anti-goal: no served surface may reveal a
   partitioned sealed/exposed view of an unexposed pool). `micro_readiness.py` itself has zero diff
   this iteration (`git diff --stat` empty), so this column could not have changed even if it were
   wired up.
3. The real `.data` store (18 dataset files, confirmed via `ls`) has no `micro_vault` directory —
   there is nothing for the vault code to act on even in principle.

---

## Regression assurance (what to re-verify, not what changed)

Because `Frontend Present: yes` triggers the mechanical browser-QA lane, the practical value of a
manual check this iteration is confirming **sameness**, not discovering something new. See the
companion UI Surface Map, UI Test Plan, and What-to-Click reports for the exact regression steps
against the three kept routes.
