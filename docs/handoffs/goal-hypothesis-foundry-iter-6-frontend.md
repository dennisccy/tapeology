# goal-hypothesis-foundry-iter-6 Frontend Handoff

**Phase:** goal-hypothesis-foundry-iter-6
**Date:** 2026-08-27
**Agent:** developer
**Status:** complete

## What Was Built

- **New "Runner / Checkpoint" subsection** on `/desk` → Hypothesis Foundry, appended after the
  existing "Epoch / Manifest" subsection (same `CollapsibleSection` pattern, same closed/open
  toggle discipline, same `RealEpochBanner` "Real Epoch — not a fixture" visual treatment). Shows,
  verbatim from the backend's new `exhaust_progress` key:
  - First-read-lock recorded timestamp (or an honest "not yet run" empty state before the
    operator's own exhaust-CLI act).
  - Resolved eligible-corpus manifest hash.
  - Checkpoint ordinal, rendered as "N of M" (frozen-ready total).
  - Protected/withheld/sealed read count (green when zero, rose otherwise).
  - Runner lock status (idle / running / refused_concurrent — the third value is a defensive render
    path never exercised by the real epoch, per the phase spec's own Visual Requirements).
  - Freeze integrity verdict (green / not_yet_verified / a typed halt code).
  - An honest completion sentence — including the explicit "zero FROZEN_READY variants this epoch
    — an honest, vacuous completion" caveat for this era's real (empty) result.
- No new user actions — the Foundry surface stays entirely read-only this era. The exhaust CLI is
  an operator/CLI act outside the app, never triggered by a page load.
- No navigation changes — one new subsection inside the existing Hypothesis Foundry panel.

## Files Changed

- `apps/frontend/lib/types.ts` -- new `FoundryExhaustProgress` interface; `DeskFoundryResponse`
  grows `exhaust_progress: FoundryExhaustProgress`.
- `apps/frontend/app/desk/page.tsx` -- new `RunnerCheckpointSubsection` component; wired into
  `HypothesisFoundrySection` as a new `CollapsibleSection` (`id="foundry-runner-checkpoint-section"`,
  title "Runner / Checkpoint"), reusing the page's existing `openSubsections` toggle state (no new
  hook/state shape).

## New testids

`foundry-runner-checkpoint`, `foundry-runner-checkpoint-real-banner`,
`foundry-runner-checkpoint-empty`, `foundry-runner-first-read-lock`,
`foundry-runner-eligible-corpus-hash`, `foundry-runner-checkpoint-counts`,
`foundry-runner-checkpoint-ordinal`, `foundry-runner-protected-read-count`,
`foundry-runner-single-flight-status`, `foundry-runner-freeze-integrity-verdict`,
`foundry-runner-exhaust-complete`, `foundry-runner-exhaust-incomplete`.

## Tests Run

`cd apps/frontend && ./node_modules/.bin/tsc --noEmit` -- clean, zero errors.

Browser check (Chrome CDP against the real `:8301` backend + `:3301` frontend, real committed
epoch): navigated to `/desk`, expanded Hypothesis Foundry → Runner / Checkpoint, extracted the
rendered element's `innerText` and confirmed it matches the served `exhaust_progress` JSON exactly
(first-read-lock timestamp `2026-08-27T06:55:51.071173Z`, the real eligible-corpus hash,
"Checkpoint: 0 of 0", "Protected/withheld/sealed reads: 0", "Runner lock: Idle — lock free",
"Freeze integrity: green", and the honest zero-candidate completion sentence). A full-page/element
PNG screenshot came back blank on every attempt in this headless environment (a known, previously-
documented limitation, not a rendering defect) — the DOM-text extraction is the evidence of record.

## Known Issues

- No component-level unit test was added for `RunnerCheckpointSubsection` in isolation (this
  project's frontend test coverage for `/desk` subsections is via TypeScript typing + the backend's
  own route contract tests + browser verification, matching every sibling Foundry subsection's own
  precedent — none of `EpochManifestSubsection`/`HermeticOraclesSubsection`/etc. carry a dedicated
  React unit test either).
- The `single_flight_status: "refused_concurrent"` render path is present in the component's own
  label map but is not exercised against real state this era (the real exhaust CLI only ever ran
  once, and no concurrent invocation was attempted against the real epoch) — proven instead by the
  backend's own unit tests for the `SingleFlightLock` primitive.

---

## Fix Notes (review FAIL pass — 2026-08-27)

**No frontend source changed in this pass.** `tsc --noEmit` re-run: exit 0.

Two frontend-relevant claims from the section above are now upgraded from "text-extraction only,
against the developer's own live backend" to "screenshot, through the mandated scoped QA rig":

- The reviewer correctly found that the earlier browser check ran against the developer's own
  `:8301` (the real production store), never against
  `qa_playbook_iter7_fixture_scoped_backend.sh`'s sandboxed rig — which had no copy of the real
  trial ledger and would therefore have rendered the honest-but-wrong pre-lock EmptyState. That
  provisioning gap is fixed in the launcher (see the dev handoff's Fix Notes) and re-verified: a
  freshly-seeded rig on `:8301` with the frontend on `:3301` renders the real Runner / Checkpoint
  state.
- The "screenshot came back blank on every attempt" note has a working method now: the blank is a
  deep-scroll capture artifact, and enlarging the viewport so the subsection sits inside an
  unscrolled page produces a real image. Evidence committed at
  `reports/qa/goal-hypothesis-foundry-iter-6-runner-checkpoint-scoped-rig.png` (full page, 1400x4200)
  and `...-crop.png` (the subsection alone). The rendered values in the image are the real ones:
  the `REAL EPOCH — NOT A FIXTURE` banner, first-read lock `2026-08-27T06:55:51.071173Z`,
  eligible-corpus hash `da7488f8…5c3260`, `Checkpoint: 0 of 0`,
  `Protected/withheld/sealed reads: 0`, `Runner lock: Idle — lock free`,
  `Freeze integrity: green`, and the zero-candidate completion sentence.

Both Known Issues above still stand unchanged.
