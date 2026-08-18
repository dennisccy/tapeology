# Phase goal-rapid-microscope-iter-9 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-9
**Date:** 2026-08-18
**Written by:** ui-impact-analyst

---

**Context (read this first):** this iteration's entire diff is backend Python — 5 source files
(`apps/backend/app/research/vault.py` **NEW**, `apps/backend/app/research/micro_routes.py`,
`apps/backend/app/research/walkforward.py`, `apps/backend/app/research/datasets.py`,
`apps/backend/app/research/tick_recorder.py`) plus 4 test files (`test_vault.py` **NEW**,
`test_walkforward.py`, `test_datasets.py`, `test_tick_recorder.py`), independently confirmed via
`git status --porcelain` (7 modified + 2 new files, all under `apps/backend/`; 0 `.tsx`/`.ts`/`.css`
files anywhere in the diff — matches the dev handoff's own claim exactly). `Frontend Present: yes`
is declared on the plan not because any UI shipped, but as the documented mechanical workaround
(iter-4 through iter-8 precedent) that keeps the browser-QA harness's entire browser lane —
including the required-still-passing regression journeys J-01–J-05 and the J-10 sentinel — from
being skipped outright. So the sections below are short and factual: there is genuinely no new UI
to describe this iteration, and one section's continued *absence* is itself the thing this
iteration's target journey needs proven.

---

## What Users Can Now Do

None, in the product's web UI. This iteration's entire deliverable — the Validation Vault
(`vault.py`) — lands beneath the surface:

- **Universe registration and the sealed → assigned → exposed shard lifecycle** now exist as
  backend machinery (hash-chained ledgers, HMAC-based seal assignment, the TR-2/4/12/20 refusal
  rules), but there is no button, form, page, or command anywhere in the running app that an
  operator can click to register a universe or seal a shard. The only way to exercise any of it is
  the backend test suite or a direct HTTP call.
- **`GET /research/desk/micro/vault`** is a real, working endpoint an operator with terminal/API
  access could call directly (e.g. `curl http://localhost:8301/research/desk/micro/vault`) to see
  the vault's current state — today an honest empty `shards`/`universes` list, since no universe has
  ever been registered. This is not reachable by clicking anything in the app; independently
  confirmed by grep — the string "vault" does not appear anywhere under `apps/frontend/`.

## What Changed in the Visible UI

None. No page, component, section, or navigation element changed this iteration. Independently
confirmed against the current `apps/frontend/app/desk/page.tsx`: the same 10 possible collapsible
sections exist before and after this diff (`topupRuns`, `indexReconciliation`, `screenRuns`,
`screenComparison`, `provenance`, `playbookEvidence`, `refereeRegistry`, `refereeAdjudications`,
`refereeRuns`, `microReadiness`) — no `vault` section, no new column, no new field. The one thing
this iteration's own acceptance criteria cares about seeing on screen is a **negative** — that a
"Validation Vault" section still does *not* exist anywhere on `/desk` — see the Regression note
below.

## What Old Behavior Changed

None. Every change in this iteration is purely additive with an absent-key default:

- `DatasetStore.record`/`record_from_source` gained two new optional keyword arguments
  (`quote_size_unit_rule_text`, `quote_size_unit_verification_note`); no existing caller other than
  `tick_recorder.py`'s own `_finalize_day` supplies them, and `_finalize_day` never actually runs
  this iteration (no live, credentialed recording — that is J-06 step 4, explicitly deferred), so no
  dataset on disk gains these fields as a side effect of this diff.
- `walkforward.py`'s `_tick_dataset_session_dates` gained an additive `sealed_dataset_ids` keyword
  (default `frozenset()`, byte-identical for the one existing call site that doesn't pass it); the
  new sealed-exclusion logic only fires inside `run_diagnostic_walkforward`'s one-time r2-seed path
  for `TICK_LEGACY_CORPUS_ID` — a code path the `/desk` Microscope Readiness section does not read
  (confirmed: `micro_readiness.py` imports neither `walkforward.py` nor `vault.py`; its
  `exposure_state` value for legacy shards is a hardcoded constant, not a computed one).

This matches the dev handoff's own claim ("Changed Behavior: None... existing behavior, existing
stored data, and every existing screen render exactly as before").

## Not Visible Yet

- **The Validation Vault** (universe registration; the sealed → assigned → exposed shard lifecycle;
  `GET /research/desk/micro/vault`) — fully built and tested this iteration, but no `/desk` section
  renders it. That is explicitly J-08 scope (see `docs/goal.md` J-08 step 1: "Render the ... **
  Validation Vault** sections on `/desk` below Microscope Readiness").
- **The §2.6 rule-text + verification-note stamp** — a dataset manifest can now optionally carry
  `quote_size_unit_rule_text` and `quote_size_unit_verification_note` beside its existing
  `quote_size_unit` stamp, but the Microscope Readiness shard table has no column for either field
  (nor for `quote_size_unit`/`schema_basis`, which have carried the same "stored but not rendered"
  status since an earlier iteration) — and, as noted above, no dataset on disk carries the new
  fields yet regardless, since no live recording ran.
- **The exposure-registry sealed filter** — a correctness fix (closes a latent hole where a freshly
  sealed shard could have been wrongly marked "already exposed" by the walk-forward diagnostic
  seed) with zero observable effect today, because nothing is sealed yet. Its value is entirely
  prospective — it protects the *next* iteration's real sealing act (J-06 step 4), not anything a
  user can see now.

---

## Regression note (why a test plan exists despite no UI change)

Because `Frontend Present: yes` forces the browser lane to genuinely dispatch this iteration, the
test plan and operator guide below are a **regression pass over pre-existing, unmodified
surfaces** — plus one new negative check this iteration specifically requires: the phase spec's own
Testing Requirements state that J-06's "primary proof this iteration is the backend suite + fixture
runs..., not an on-screen pass," and that its one browser artifact is "an element capture of `/desk`
confirming the Validation Vault section is genuinely ABSENT (proving OUT OF SCOPE held)." So UT-01
below checks for that absence explicitly, alongside the routine re-verification of the Microscope
Readiness section (J-01) and the J-10 kept-product sentinel (`journey-scripts/J-10.json`, reused
byte-unmodified — cockpit `/`, `/structure`, and several `/desk` sections).

One correction carried forward from the last two backend-only iterations (first found stale in
iteration 6, restated correctly by iteration 7, and reconfirmed fresh here by re-reading the
fixture files directly): the Microscope Readiness expectations below are pinned to what the
store-scoped QA rig actually seeds — **1 distinct symbol-day / 2 datasets, both symbol PG, session
date 2026-06-09** (`apps/backend/tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json` and
`.../d9f9dbe04fb24a7caccc53f0c6805412.json`, both independently opened and confirmed for this
report) — never the real store's 12 symbol-days / 18 datasets, which
`apps/backend/scripts/start_scoped_qa_backend.sh` structurally cannot show (it delegates to
`qa_playbook_iter7_fixture_scoped_backend.sh`, which seeds exactly those two fixtures and nothing
else). Iteration 6's equivalent check asserted the real store's larger numbers against this same rig
and failed spuriously as a result (`docs/handoffs/goal-rapid-microscope-iter-6-audit.md`, finding
E3) — that mistake is not repeated here. See
`reports/phase-goal-rapid-microscope-iter-9-ui-surface-map.md` for the full surface-by-surface
breakdown.
