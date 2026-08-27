# Phase goal-hypothesis-foundry-iter-6 — User-Visible Changes

**Phase:** goal-hypothesis-foundry-iter-6
**Date:** 2026-08-27
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open `http://localhost:3301/desk`, expand "Hypothesis Foundry", then expand a new
  "Runner / Checkpoint" subsection to see whether the real, one-time Foundry exhaust pass has been
  run and what it found.
- Users can now see the exact timestamp the exhaust pass's "first-read lock" was recorded, proving
  the era's one real research plan has been definitively evaluated (not just frozen).
- Users can now see the resolved "eligible-corpus manifest hash" — a fingerprint of exactly which
  research-data files were in scope for this evaluation (with sealed/withheld data already excluded
  before hashing).
- Users can now see a checkpoint count ("N of M") showing how many of the frozen research
  candidates reached a final result, plus an honest "0" count for protected/withheld/sealed data
  reads — the on-screen proof that nothing off-limits was ever touched.
- Users can now see a "Runner lock" status line ("Idle — lock free", "Running — lock held by
  another invocation", or "Refused — a concurrent invocation was rejected") and a "Freeze
  integrity" verdict ("green" or a named halt code) for this evaluation run.
- Users can now see the plain-language completion message: for this era's real (empty) result, the
  panel states plainly that zero candidates ever existed to evaluate and the exhaust pass reached
  an honest, vacuous completion.

## What Changed in the Visible UI

- `/desk` → "Hypothesis Foundry" panel gains a sixth subsection, "Runner / Checkpoint", appended
  directly below the existing "Epoch / Manifest" subsection. It uses the same collapsed-by-default,
  click-to-expand pattern as every sibling subsection ("Sources / Compiler", "Interpreter
  Fixtures", "Freeze / Integrity", "Hermetic Oracles", "Epoch / Manifest").
- The new subsection carries the same "REAL EPOCH — NOT A FIXTURE" green banner already used on
  "Epoch / Manifest", signaling this data reflects the one real research plan, not a demonstration
  fixture.
- No other page, route, or navigation element changed. There is no new top-level page and no new
  entry in any menu — this is one additional collapsible block inside an already-existing panel.

## What Old Behavior Changed

- None. Every prior `/desk` subsection ("Sources / Compiler", "Interpreter Fixtures", "Freeze /
  Integrity", "Hermetic Oracles", "Epoch / Manifest") is unchanged — this iteration only appends a
  new subsection after the last existing one and adds one new key (`exhaust_progress`) to the
  already-existing `GET /research/desk/micro/foundry` response. Existing fields and existing
  subsection content are untouched.

## Not Visible Yet

- There is no button, form, or any other control anywhere in the UI to trigger the exhaust pass —
  and this is intentional, not a gap: the exhaust pass is deliberately an operator/CLI-only act,
  never a page-load-triggered computation, per this era's design. This is a read-only status
  display, not a control.
- Per-candidate detail (which specific research idea reached which outcome, survivor labelling) is
  not shown anywhere yet — this era's one real research plan has zero candidates, so there is
  nothing to drill into yet regardless. A future iteration (J-08) is expected to add that detail
  view for when a future era's plan does contain candidates.
- The freeze-record's new "era-open evidence-class contract" field (added to the backend's
  freeze-record bookkeeping this iteration) is not rendered anywhere in the "Runner / Checkpoint" or
  any other UI subsection — it exists only as an internal audit-trail field consumed by backend
  integrity checks, not as a displayed value.
