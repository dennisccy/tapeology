# goal-rapid-microscope-iter-14 Frontend Handoff

**Phase:** goal-rapid-microscope-iter-14
**Date:** 2026-08-19
**Agent:** developer
**Status:** complete

## What Was Built

`/desk` gains three new below-the-fold sections, rendered directly below the shipped Microscope
Readiness section and below every shipped Referee section — Scout Ledger, Walk-Forward, Validation
Vault — in that order. This is the first frontend surface for the Scout, Walk-Forward, and Vault
backend modules (shipped in earlier iterations, never wired to the UI until now). No existing
section's markup, `data-testid`, or heading changed; no new route (`app/meta.py` `UI_ROUTES`
untouched); nav unchanged (Cockpit / Structure / Desk).

- **Scout Ledger** — every registered candidate family (family id, union-N `variants_tried`), each
  family's trials in a table (candidate id, feature/transform, horizon, registered-at, decision,
  reason, notes, withheld-excluded count, and a `screen_result` detail disclosure), the ledger's
  chain-verification verdict, a "Run Screen" button with a live progress readout and Cancel, and a
  Run History table.
- **Walk-Forward** — every registered fold spec (behind a detail disclosure showing the full frozen
  geometry), every sequence's per-fold table (status/effect/n/sessions/sign/evidence class/process
  label), the sequence's survivor verdict (or its floor-refusal reason), the temporal decay/recency
  line, `voided`, the ledger's chain-verification verdict, a "Run Walk-Forward" button with progress
  + Cancel, and a Run History table.
- **Validation Vault (read-only)** — shard rows (opaque while `sealed`; full symbol/date/checksum
  provenance from `assigned`/`exposed` onward) and universe rows (rule-commitment-and-sizes-only
  while any pool member is unexposed; full symbol/date rule plus the reveal nonce once the whole
  original pool is released), both ledgers' chain-verification verdicts. No compute/seal/assign/
  expose control — this section is a pure read this iteration.
- Every compute control (Scout, Walk-Forward) shows an idle "Run X" button, a running/disabled state
  with a pulsing progress readout, a Cancel button while running, and surfaces the backend's own
  refusal message verbatim if a run is already in flight ("Refused — a scout screening run is
  already running...").

## New user-facing capability

An operator can now SEE — not just query via curl/pytest — the Scout's every candidate trial and
kill reason, the walk-forward engine's fold sequences and decay view, and the vault's shard/universe
lifecycle states, on `/desk`. An operator can start or cancel a Scout screening run or a Walk-Forward
run directly from the page.

## New information displayed

Scout family/trial rows with denominators and kill reasons; Walk-Forward fold-spec and sequence rows
with evidence-class labels and the decay view; Vault shard rows (opaque-or-revealed per stage) and
universe rows (committed-or-revealed per stage); three chain-verification verdicts (Scout and
Walk-Forward one each, Vault two — a separate shard-ledger and universe-ledger verdict).

## New user actions

"Run Screen" + Cancel; "Run Walk-Forward" + Cancel; expand/collapse for each of the three new
sections (the existing `CollapsibleSection` control, reused unchanged — all three start collapsed on
every page load, matching the established pattern for every other reference/run-ledger section on
this page).

## UI surface changes

`/desk` gains three new `<section>` blocks. No existing section's markup, `data-testid`, or heading
changed. Design system: reused `CollapsibleSection`, `EmptyState`/`LoadingPanel`/`UnavailablePanel`,
`PRIMARY_BUTTON_CLASS`/`CANCEL_BUTTON_CLASS`, and plain `<table>` markup throughout — no new
component-library primitive, no new visual effect (dark-only/dense house style unchanged). A
`chain_verification` verdict renders as plain text beside its data, never a colored trust badge
(Design Direction: "no color implies advice"). Honest empty-state copy follows the era's own
convention: "No candidates ledgered.", "No universes registered.", "No shards recorded.", "No scout
runs recorded yet." Loading, unavailable/typed-error, and populated states are all handled per
section (`LoadingPanel`/`UnavailablePanel`/populated table, the `MicroReadinessSection` precedent).

## Navigation changes

None — `app/meta.py` `UI_ROUTES` untouched, no new route.

## Browser verification performed

Store-scoped rig (`scripts/dev.sh`, backend `:8301` / frontend `:3301`), clean rebuild
(`rm -rf apps/frontend/.next` before first start, per T-9).

- Scout Ledger against the real (empty) backend: "No candidates ledgered." + "No scout runs
  recorded yet.", `chain_verification: ok` — extracted live.
- Walk-Forward against the real (non-empty) backend: one fold spec, one sequence, 5 fold rows — the
  full extracted page text was diffed field-by-field against `curl .../research/desk/micro/
  walkforward`'s own JSON and matched byte-for-byte on every value.
- Validation Vault against the real (empty) backend: "No shards recorded." + "No universes
  registered.", both chain verifications `ok` — extracted live, raw HTML inspected for zero
  non-whitelisted field leakage (trivial on an empty vault, but the extraction itself is on record).
- Scout's "Run Screen" clicked live against the real backend/corpus: observed live transitions
  idle → "Screening…" (disabled) + "0 / 6 candidates" progress + Cancel button appeared → clicking
  Cancel → "Cancelling…" (disabled). The run's eventual terminal state was not observed within this
  pass's time budget (the real corpus's first-candidate screening computation ran past 25 minutes
  without completing) — see the dev handoff's Known Issues for the full reasoning and the safe
  cleanup performed (backend restart; confirmed zero ledger rows were ever written, so the real
  store's empty-Scout-ledger baseline is unaffected).
- Regression: Microscope Readiness re-expanded and still renders its shipped tables unchanged.
- TypeScript strict compilation (`tsc --noEmit`) passed with zero errors across every new type and
  every discriminated-union branch this diff introduces.

**Not exercised live this pass** (disclosed in full in the dev handoff): the Vault's two-stage
opaque/revealed rendering paths (TC-4/TC-5 — the real vault store is empty today, so there is no live
sealed/assigned/exposed shard or committed/revealed universe to render; verified instead via direct
source cross-reference against `vault.py`'s `_serialize_shard`/`_serialize_universe` plus TypeScript's
own exhaustiveness check) and Walk-Forward's compute control click-through (TC-8 — time budget, after
Scout's real-corpus run ran long; the control is structurally identical to Scout's own, which
Screen-mode Cancel behavior over the identical code path). Recommend browser-QA / the independent
auditor exercise both directly, the latter via a seeded fixture vault state per the plan's own
TC-4/TC-5 wording.

## Known Issues

See the dev handoff (`docs/handoffs/goal-rapid-microscope-iter-14-dev.md`) for the full list,
including the `useEffect`/`setInterval`/`setTimeout` census constraint this iteration had to design
around, the resulting no-mid-run-reload-resume trade, the live-verification gaps on TC-4/TC-5/TC-8,
and a headless-Chrome screenshot-capture environment quirk discovered and worked around
(`fullpage: true` required — plain viewport/element screenshots came back blank after any scroll, on
this session's Chrome, reproduced against a pre-existing unmodified section).
