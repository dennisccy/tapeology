# goal-rapid-microscope-iter-14 Execution Plan

J-08 half 1 of 2 (evaluator-mandated split from iteration 13's ESCALATE verdict). Render three
NEW `/desk` sections — Scout Ledger, Walk-Forward, Validation Vault — directly below the shipped
Microscope Readiness section, each reading its already-built, already-tested backend endpoint
verbatim. Zero backend computation/serialization/route change. The four new MCP tools and the
`EXPECTED_TOOLS` 22→26 bump are iteration 15's half — do not touch them here.

## What to Build

- **Scout Ledger section** — every registered candidate family's trials (denominators, kill
  reasons), the ledger's `chain_verification` verdict beside the data, and a "Run Screen" /
  Cancel compute control with a progress readout (`POST/GET/POST-cancel
  /research/desk/micro/scout/compute`).
- **Walk-Forward section** — fold specs + sequences (per-fold results, evidence-class label, the
  decay view, sequence verdict, `voided`), the ledger's `chain_verification` verdict, and a "Run
  Walk-Forward" / Cancel compute control (`POST/GET/POST-cancel
  /research/desk/micro/walkforward/compute`).
- **Validation Vault section — READ-ONLY** (no compute/seal/assign/expose button; ruling already
  recorded in `runs/goal-session-rapid-microscope/state/assumptions.md` iter-14 entry — do not
  re-litigate) — shard rows (opaque while `sealed`, full provenance from `assigned` onward) and
  universe rows (`rule_commitment`-only pre-release, `symbol_rule`/`date_rule`/nonce
  post-release), both ledgers' own chain-verification verdicts.
- Supporting `lib/types.ts` response/row types and `lib/api.ts` fetch/trigger/cancel functions for
  all three endpoints, transcribed field-for-field from the actual served shapes (verified by
  reading `micro_routes.py` and `vault.py` directly this planning pass — exact shapes below, do
  not re-derive them from the goal.md prose alone).
- One backend touch, mechanical only: widen `test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS`
  allow-list for every newly-rendered numeric binding.

## Agents Required

- developer: yes — one pass covers both the frontend build and the one guard-test extension below.
- backend-data: no — zero change to `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`,
  `walkforward_ledger.py`, or `micro_routes.py`'s computation, serialization, or route shape (all
  four GET endpoints and the two compute triples already exist and are already tested). The one
  `tests/test_desk_ui_guards.py` edit is an allow-list string addition, not backend logic, and
  travels with the same developer pass.
- frontend-ux: yes — the whole scope: three new sections, their state wiring, `types.ts`, `api.ts`.

Frontend Present: yes

## Files to Create/Modify

- `apps/frontend/lib/types.ts` — add response/row types for the Scout ledger body (`families`,
  each family's trials with `family_id`/`family_root_id`/`variants_tried`/per-trial
  `decision`/`reason`/`notes`/`screen_result`, plus `chain_verification`), the Walk-Forward ledger
  body (`fold_specs`, `sequences` with `mode`/`fitting_rule`/`rule_id`/per-fold
  results/evidence-class label/decay view/sequence verdict/`voided`, plus `chain_verification`),
  the Vault body (see exact shape below — note the vault has TWO chain-verification fields, not
  one), and the Scout/Walk-Forward compute-snapshot + run-log-list shapes. Transcribe from the
  actual backend source (`micro_routes.py`, `vault.py`), never invent or drop a field.
- `apps/frontend/lib/api.ts` — `fetchDeskScout`, `triggerDeskScoutCompute`,
  `fetchDeskScoutCompute`, `cancelDeskScoutCompute`, `fetchDeskScoutRuns`; the same five-function
  quintet for Walk-Forward; `fetchDeskVault` (GET-only — the vault has no compute route this
  iteration). Follow `fetchMicroReadiness`'s exact shape verbatim (`apps/frontend/lib/api.ts`,
  found via `grep -n "export async function fetchMicroReadiness"` — same `API_BASE` usage, same
  `{ok, data, error?}` envelope, same "Backend unreachable — is the API running?" fallback
  string). `triggerDeskScoutCompute`/`triggerDeskWalkforwardCompute` take **no body/params** —
  both POST routes are parameterless triggers (verified in `micro_routes.py`), unlike
  `triggerDeskScreenCompute(screenDate)` or the recorder's symbol/date body — do not invent an
  argument they don't take.
- `apps/frontend/app/desk/page.tsx` — locate every anchor below by symbol name (`grep`), not line
  number; the file is ~11k lines and shifts between iterations:
  - Widen the `DeskCollapsibleSection` union (search `type DeskCollapsibleSection`) with
    `"scoutLedger" | "walkForward" | "validationVault"` — these exact three identifiers, per the
    phase spec's own IN SCOPE wording.
  - Add result state for each section (search `microReadinessResult` for the exact shape to
    copy) plus **one** `RefereeComputeControlState` instance each for Scout and Walk-Forward
    (search `REFEREE_COMPUTE_CONTROL_IDLE` / `RefereeComputeControlState` — reuse the type
    unchanged). Use a **single flat instance per section, not a `Record<string, ...>` keyed map**
    — Scout and Walk-Forward computes are page-level single triggers (no per-candidate/per-family
    selection, confirmed by the parameterless POST routes above), unlike the Referee's per-`
    null_spec_id`/per-`hypothesis_id` keyed pattern.
  - Extend `toggleSection`'s existing if/else chain (search `function toggleSection`) with three
    new branches issuing the deferred fetch-on-expand reads. **Do not add a `useEffect` for
    this** — `test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT` (currently 21) pins the
    page's exact effect count, and this page's own established convention is that expand-driven
    reads are plain event-handler logic inside `toggleSection`, never an effect.
  - Add `ScoutLedgerSection`, `WalkForwardSection`, `ValidationVaultSection` as inline function
    components in this same file (search `function MicroReadinessSection` for the placement/style
    precedent — every existing desk section component lives inline in `page.tsx`, not a separate
    component file).
  - Add three `CollapsibleSection` blocks directly after the existing `microReadiness` block
    (search `id="microReadiness"` — it is currently the LAST section on the page), in this exact
    order: Scout Ledger, Walk-Forward, Validation Vault (matches
    `runs/goal-session-rapid-microscope/state/blueprint.md`'s fixed Information Architecture
    order).
- `apps/backend/tests/test_desk_ui_guards.py` — widen `_PRICE_ARITHMETIC_FIELDS` (search
  `_PRICE_ARITHMETIC_FIELDS = (`) with a new alternation group per new local JSX binding name
  (mirror the existing `row.(?:...)`/`signal.(?:...)`/`plan.(?:...)` grouping style) covering
  every new numeric: `variants_tried`, fold/sequence counts, decay percentages, size buckets,
  progress counters, etc. Never loosen an existing group — only add.

## Backend contracts to render verbatim (already shipped — confirmed by reading source this pass; do not modify any of these files)

- `GET /research/desk/micro/scout` → `{families: [...], chain_verification: {...}}`.
  `POST /scout/compute` → `{state, run_id}` (or a refusal body if already running, no `run_id`).
  `GET /scout/compute` → `{state, progress, started_utc, finished_utc, error}` — read the actual
  `progress` sub-field names off the live response at build time (TC-7 names
  `candidates_done`/`candidates_total`; confirm before hard-coding). `POST /scout/compute/cancel`
  → `{state: "cancelled"}`, or HTTP 409 if idle. `GET /scout/runs` → `{runs: [...]}`.
- `GET /research/desk/micro/walkforward` → `{fold_specs: [...], sequences: [...],
  chain_verification: {...}}`. Compute triple is the same shape as Scout's, also parameterless.
  `GET /walkforward/runs` → `{runs: [...]}`.
- `GET /research/desk/micro/vault` → `{universes: [...], shards: [...],
  shard_ledger_chain_verification: {...}, universe_ledger_chain_verification: {...}}` — **two
  distinct chain-verification fields, not one `chain_verification` like Scout/Walk-Forward.**
  - Shard row, `sealed` stage — **exactly and only**: `shard_id`, `universe_id`, `size_bucket`,
    `checksum_commitment`, `sealed_at`, `exposure_state` (this is the literal
    `_OPAQUE_SHARD_KEYS` whitelist in `vault.py`). Add nothing else to this stage's rendering.
  - Shard row, `assigned`/`exposed` stage — the six fields above **plus** `dataset_id`,
    `family_root_id`, `symbol`, `session_date`, `assigned_at`, `exposed_at` (and
    `content_checksum` once `exposed`).
  - Universe row, committed stage (`rule_disclosure: "committed"`) — `universe_id`,
    `registered_at`, `rule_commitment`, `vault_secret_commitment`, `symbol_rule_size`,
    `date_rule_size`. No `symbol_rule`/`date_rule`/`commitment_nonce`.
  - Universe row, revealed stage (`rule_disclosure: "revealed"`, only after **whole-ORIGINAL-pool**
    release — never merely "every ledger-tracked shard exposed") — adds `symbol_rule`,
    `date_rule`, `commitment_nonce`.
  - Render `rule_disclosure` and `exposure_state` verbatim so the component branches on the
    server's own stage label, never on field-presence inference.

## Guardrails — read before writing the Vault section (the auditor's primary target this round)

Spec revisions r3–r8 (`docs/rapid-validation-spec.md` §7.1/§7.5, already read this pass) exist
because four prior audits (rounds 2, 4, 5, 7) found a subtraction attack against exactly this kind
of surface, each time *after* review and QA had already passed the same code. Do not reopen it:

- Render the shard/universe fields **exactly** as whitelisted above — no additional field, no
  derived/joined value, no raw `content_checksum` or `dataset_id` on a still-sealed row.
- The Validation Vault section issues **exactly one fetch** (`GET /research/desk/micro/vault`).
  Never call `/research/datasets`, never read the Microscope Readiness result to enrich or
  cross-reference a vault row — each section renders only its own endpoint's body (TC-6 is a grep
  check for this).
- Never compute or display an exact count derived from a coarse bucket field (`size_bucket`,
  any `*_bucket` progress field) — render the bucket label/range as served, nothing arithmetic on
  it.
- No compute/seal/assign/expose control anywhere in the Validation Vault section this iteration.
- Do not touch any MCP file or `EXPECTED_TOOLS` (stays at 22) — iteration 15's scope.
- Do not touch `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`, `walkforward_ledger.py`,
  `micro_routes.py`, or `docs/rapid-validation-spec.md`.

## UI Evolution

- New user-facing capability: an operator can SEE, not just query via curl/pytest, the Scout's
  every candidate trial and kill reason, the walk-forward engine's fold sequences and decay view,
  and the vault's shard/universe lifecycle states, on `/desk` — and can start/cancel a Scout
  screening run or a Walk-Forward run from the page.
- New information displayed: Scout family/trial rows; Walk-Forward fold-spec/sequence rows incl.
  evidence-class label and decay view; Vault shard rows (opaque-or-revealed per stage) and
  universe rows (committed-or-revealed per stage); three/two chain-verification verdicts.
- New user actions: "Run Screen" + Cancel; "Run Walk-Forward" + Cancel; expand/collapse for each
  of the three new sections (existing `CollapsibleSection` control, unchanged).
- UI surface changes: `/desk` gains three new below-the-fold sections directly below Microscope
  Readiness and below every shipped Referee section. No existing section's markup, `data-testid`,
  or heading changes (T-11).
- Navigation changes: none — `app/meta.py` `UI_ROUTES` untouched, no new route.

## Visual Requirements

- Component patterns: reuse `CollapsibleSection` (`components/CollapsibleSection.tsx`) for all
  three; reuse `EmptyState`/`LoadingPanel`/`UnavailablePanel` for empty/loading/error states
  (the `MicroReadinessSection` precedent); reuse the existing plain `<table>` +
  `PRIMARY_BUTTON_CLASS`/`CANCEL_BUTTON_CLASS` styling already used throughout this page — no new
  component-library primitive.
- Layout: continues the single-column, dense, terminal-grade `/desk` layout — a short intro `<p>`
  naming the source endpoint (the `MicroReadinessSection` precedent), then one or more `<table>`
  blocks.
- Key visual effects: none new — house style stays dark-only/dense/no-glow; a `chain_verification`
  verdict renders as plain text beside its data, never a colored trust badge (Design Direction:
  "no color implies advice").
- States to handle: loading, unavailable/typed-error (TC-14), honest empty (era copy convention,
  e.g. "No candidates ledgered." / "No universes registered."), and populated. The real `.data`
  store today has an empty Scout ledger and an empty Vault but a non-empty Walk-Forward ledger —
  so both the empty and populated code paths render against the REAL backend this iteration, not
  only fixtures.

## Key Test Scenarios

(Condensed from the phase spec's TC-1…TC-15 — see `docs/phases/goal-rapid-microscope-iter-14.md`
for full acceptance text.)

- TC-1/TC-3: zero scout families / zero vault universes on the real backend → honest empty-state
  copy, `chain_verification.ok: true`, zero fabricated rows.
- TC-2: the real, non-empty Walk-Forward ledger → rendered fold-sequence values byte-identical to
  `GET /walkforward`'s own JSON.
- TC-4/TC-5: a fixture vault state exercises BOTH stages — a sealed shard + a not-yet-released
  universe renders only the opaque/committed whitelist; the same universe at whole-pool release
  renders `symbol_rule`/`date_rule`/`commitment_nonce`. Both paths must be shown, not just one.
- TC-6: Validation Vault issues exactly one fetch, zero cross-references to `/research/datasets`
  or readiness (grep-verifiable in the component tree).
- TC-7/TC-8: Run Screen / Run Walk-Forward → running/disabled + progress readout + Cancel appears
  → Cancel hits the `/compute/cancel` route → reaches idle without hanging.
- TC-9: widened `_PRICE_ARITHMETIC_FIELDS` sweep reports zero client-side arithmetic on any new
  numeric.
- TC-10: full suite ≥ 3228 collected / 0 failed; `EXPECTED_TOOLS` still exactly 22.
- TC-11: fingerprint `08e471b10130e1e2`; six `referee_*.py` SHA-256 hashes unchanged from the
  iteration-0 baseline.
- TC-12: clean `rm -rf apps/frontend/.next` + rebuild; browser pass element-captures Microscope
  Readiness plus the three new sections, in that exact order, below the shipped Referee sections;
  no `data-testid`/heading collision (T-11 static sweep against stored replay scripts).
- TC-13: full regression of J-01–J-05 and J-07 — every cited evidence file genuinely exists on
  disk (closes iteration 13's `evidence_makeup` debt); J-07's `/research/desk/micro/graduation`
  genuinely re-checked live (not `DEFERRED-BUDGET` again).
- TC-14: backend unreachable/non-200 → typed "could not be loaded" message per section, never a
  blank panel or a stale table.
- **TC-15 — auditor-owned, this round's central mandate.** Sweep the RENDERED `/desk` page (DOM +
  every network response the page issues) with the same TR-2/TR-27/TR-28 inference-trap
  methodology the existing `test_vault.py` fixtures already apply to raw endpoints: no
  still-unexposed vault-eligible shard identifiable with certainty; no complete
  identity-labelled exploratory/sealed partition derivable by subtraction, through the new UI
  layer specifically — this is the fault class the independent auditor alone has caught, five
  times, always after review+QA had already passed.

## Notes

- J-08 is scored `partial` this iteration (panels only — the four MCP tools land in iteration 15).
  Do not report J-08 as fully `passing`.
- Required-still-passing this round (full regression, ESCALATE-widened per the era's own rule):
  J-01, J-02, J-03, J-04, J-05, J-07.
- If `runs/goal-session-rapid-microscope/state/golden-gaps`'s J-07 entry is missing, restore it
  verbatim rather than rewriting — a known harness durability gap, not a product gap for this
  iteration's developer (see the phase spec's own NOTES section).
