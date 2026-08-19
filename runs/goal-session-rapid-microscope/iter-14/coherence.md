# Iteration 14 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-14
**Date:** 2026-08-19
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Summary

This is the first iteration in four that genuinely changes the frontend, and it holds up under
both Data Contract and Information Architecture review. Three new `/desk` sections — Scout Ledger,
Walk-Forward, Validation Vault — each read exactly one already-registered canonical endpoint
verbatim, land in their already-registered IA homes in the exact specified DOM order, and introduce
no new route, no new nav, no duplicate home, and no client-side arithmetic (confirmed both by
static read and by re-running the widened guard test). Zero backend product files were touched
(`git diff --stat` against the four authorized files only), which is the strongest possible
structural evidence against a duplicate-computation FAIL: there is no second implementation
anywhere for any of the three sections' values to diverge from.

The one substantive issue is pre-existing, not introduced by this diff, and does not rise to a
Part A/B FAIL under this gate's objective rules — see "Microscope Readiness's incomplete surface"
below. It is recorded as a WARN so it stays tracked into iteration 15, where the independent
auditor has already queued it as the top item.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Scout family/trial rows, `variants_tried`, `withheld_excluded`, `screen_result` | OK | `apps/frontend/lib/api.ts` `fetchDeskScout` → `GET /research/desk/micro/scout` only; rendered verbatim `apps/frontend/app/desk/page.tsx:6123-6281` (section `scout-ledger-section`); `trial.withheld_excluded` read directly, never summed (`page.tsx:6249`) |
| Scout run log (`.../scout/runs`) | OK | `apps/frontend/lib/api.ts` `fetchDeskScoutRuns` → `GET /research/desk/micro/scout/runs`; rendered `page.tsx:6272-6299` (`scout-ledger-runs-block`/`-table`/`-run-rows`) |
| Scout compute progress/trigger/cancel | OK | `apps/frontend/lib/api.ts` `triggerDeskScoutCompute` / `fetchDeskScoutCompute` / `cancelDeskScoutCompute` → the registered `POST/GET/POST-cancel /research/desk/micro/scout/compute` triple; polling re-fetches only `fetchDeskScoutCompute`, and on terminal state re-fetches only `fetchDeskScout`/`fetchDeskScoutRuns` (`page.tsx:9959-10026` — `pollScoutComputeUntilTerminal`/`handleTriggerScout`/`handleCancelScout` — mirrors the poll-then-refresh pattern already used elsewhere on this page) |
| Walk-Forward fold specs, sequences, decay view, sequence verdict | OK | `apps/frontend/lib/api.ts` `fetchDeskWalkforward` → `GET /research/desk/micro/walkforward` only; rendered verbatim `page.tsx:6334-6602` (function `WalkForwardSection`, testid `walk-forward-section`); `decay_view.fold_rows`/`recency` read directly, no client recompute of a decay statistic |
| Walk-Forward run log + compute progress/trigger/cancel | OK | mirrors the Scout triple exactly, own endpoints only (`page.tsx:10028-10094` — `pollWalkforwardComputeUntilTerminal`/`handleTriggerWalkforward`/`handleCancelWalkforward`) |
| Vault shard rows (opaque pre-exposure vs. revealed) | OK | `apps/frontend/lib/api.ts` `fetchDeskVault` → `GET /research/desk/micro/vault`, the section's **only** fetch (confirmed by grep: no `/research/datasets` or `microReadinessResult` reference inside `ValidationVaultSection`, `page.tsx:6603-6763`, testid `validation-vault-section` at `:6621`); branches strictly on server-stamped `shard.exposure_state`/`universe.rule_disclosure`, never on field presence |
| Vault universe rows (`rule_commitment`/`commitment_nonce` two-stage reveal) | OK | same section; `rule_commitment`/`commitment_nonce` are the already-registered iter-12 sub-fields (blueprint.md "Universe rule-reveal sub-fields"), rendered verbatim, gated on `rule_disclosure` |
| `shard_ledger_chain_verification` / `universe_ledger_chain_verification` (two distinct fields, per blueprint's own note) | OK | `page.tsx:6634-6644`; both rendered from the one `DeskVaultResponse`, never merged into one |
| Zero client-side arithmetic on any newly-rendered numeric | OK (executed, not just read) | `apps/backend/tests/test_desk_ui_guards.py` widened `_PRICE_ARITHMETIC_FIELDS` (+18 lines) re-run live: `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_ui_guards.py -q` → 80 passed, 0 failed |
| `EXPECTED_TOOLS` / MCP surface | OK (unchanged) | `git diff --stat` shows no `apps/backend/app/mcp*` file touched; parsed `tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple live → still 22 entries |
| Readiness `sealed_tranche` / `joinable_corpus.withheld_excluded` (`micro_readiness.py`, `GET /research/desk/micro/readiness`) | REGISTERED-NOT-RENDERED (pre-existing; WARN, not FAIL) | see "Microscope Readiness's incomplete surface" below |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Scout Ledger (`/desk`, below Microscope Readiness) | OK | `apps/frontend/app/desk/page.tsx:12034-12050` (`<section aria-label="Scout Ledger">`, `CollapsibleSection id="scoutLedger"`) — placed immediately after `<MicroReadinessSection>`'s closing tag; matches blueprint IA row "Scout + candidate ledger (J-04) \| `/desk` → Scout Ledger \| Desk" |
| Walk-Forward (`/desk`, below Scout Ledger) | OK | `page.tsx:12054-12070` (`CollapsibleSection id="walkForward"`) — matches blueprint IA row "Walk-forward engine + diagnostic run (J-05) \| `/desk` → Walk-Forward \| Desk" |
| Validation Vault (`/desk`, below Walk-Forward) | OK | `page.tsx:12075-12084` (`CollapsibleSection id="validationVault"`) — matches blueprint IA row "Recorder + Validation Vault (J-06) \| `/desk` → Validation Vault \| Desk" |
| No new route / no nav change | OK | `git diff --stat` shows no `app/meta.py` (`UI_ROUTES`) or `NavBar` component touched; the three sections live inside the existing `/desk` page, reachable via the unchanged top-nav "Desk" link (1 click) + expanding a `CollapsibleSection` (1 click) — within the blueprint's own ≤2-click benchmark |
| No parallel shell | OK | all three sections reuse the existing `CollapsibleSection`/`toggleSection` machinery already used by Microscope Readiness and the Referee sections (`page.tsx` `toggleSection`, extended not replaced at `page.tsx:9771-9786`) |
| No duplicate testid/heading | OK | grep-confirmed exactly one definition site each for `scout-ledger-section` / `walk-forward-section` / `validation-vault-section` and for `CollapsibleSection` ids `scoutLedger`/`walkForward`/`validationVault` |
| Blueprint IA rows themselves | OK (pre-existing, correctly unchanged) | blueprint.md's IA table already names all three homes "present since era baseline" (confirmed against the table's own text, not just the iter-14 note's claim); the iter-14 note appended to blueprint.md is a correct no-table-change confirmation, not an omission — the code faithfully implements the pre-registered homes rather than inventing new ones |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Microscope Readiness's incomplete surface (the item this dispatch asked for explicit
  judgment on).** `apps/frontend/lib/types.ts:2514-2519`'s `MicroReadinessResponse` declares only
  `totals`/`shards`/`study_floors`/`integrity_errors` — independently confirmed by grep that
  `sealed_tranche` and `withheld_excluded` appear nowhere in that type or in
  `MicroReadinessSection`'s rendering, while `apps/backend/app/research/micro_readiness.py:472,477,495`
  independently confirmed to serve both (`sealed_tranche` as its own object; `withheld_excluded`
  nested under `joinable_corpus`). **This is not a Part A/B FAIL**: the value is not computed twice
  (no second implementation exists anywhere — the frontend simply never destructures two of the
  fields its one canonical fetch already returns), it is not served from a non-canonical source,
  and Microscope Readiness is not a new page/feature this iteration — the diff does not touch
  `MicroReadinessSection` or its render call at all (confirmed: the only diff hunk near it is an
  insertion immediately after its closing tag). It also does not fit the "no home" or "duplicate
  home" IA violations — the value's canonical home (`/desk` → Microscope Readiness) already exists,
  is singular, and is correctly the ONLY place this value is rendered; it is just incompletely
  rendered there. That combination — one canonical source, one canonical home, simply not fully
  drawn from yet — sits outside this gate's objective FAIL rules, which are about scattering and
  divergence, not completeness. It is real and worth tracking, though: it is functionally the same
  shape of gap iteration 9's coherence WARN caught and iteration 10's decomposer closed by adding
  the Data Contract rows (`blueprint.md`'s "Disclosure sub-fields" table) — those rows now exist,
  but this iteration's independent auditor found (finding F3, `docs/handoffs/goal-rapid-microscope-
  iter-14-audit.md`) that the *registration* closed the WARN without the *rendering* ever following
  it into Microscope Readiness. This iteration's spec correctly forbade touching that section ("No
  existing section's markup, `data-testid`, or heading changes"), so leaving it alone was the right
  call here, not a defect of this round. Recorded as WARN so it is not lost: the fix is a one-section,
  no-new-endpoint addition (render the two already-fetched fields in the existing Microscope
  Readiness section), already correctly queued as iteration 15's top carried item by the independent
  auditor.
- Scout's family header never renders `family_root_id` even though this iteration's own spec names
  it under "New information displayed" (`page.tsx` family header interpolates only `family.family_id`
  and `family.variants_tried`). Not a Data Contract or IA violation — the field is read off the one
  canonical endpoint and simply not displayed in this one spot; it correctly IS displayed elsewhere
  in this same iteration's diff (Vault shard rows' `family_root_id` column). A one-line completeness
  gap, already filed by the independent auditor as a MINOR for iteration 15.
- Walk-Forward's empty-sequences state (`walk-forward-sequences-empty`) reuses Scout's copy, "No
  candidates ledgered.", instead of sequence-appropriate wording — a labelling/copy inconsistency
  across two sibling sections for two different entities (folds/sequences vs. candidates). Textbook
  Part C advisory (inconsistent labels for the same kind of empty state), not a structural issue —
  both sections still read their own correct canonical endpoint.
- Minor, low-priority: the Vault's committed-stage universe fields `symbol_rule_size`/
  `date_rule_size` (`apps/frontend/lib/types.ts` `VaultCommittedUniverse`) are not individually named
  in blueprint.md's "Universe rule-reveal sub-fields" table the way their sibling gated fields
  `rule_commitment`/`commitment_nonce` are. They are read verbatim from the same already-registered
  `GET /research/desk/micro/vault` endpoint under the same already-registered `vault.py` owner, so
  this is not a sourcing violation — just an unnamed companion field of an already-documented
  disclosure mechanism (the coarse-size-only pre-release view), the same category `symbol_rule`/
  `date_rule` (the post-release counterparts) were also left unnamed as. Not worth its own blocking
  action; noted only for completeness in case a future decomposer wants blueprint.md to enumerate it
  alongside its siblings.

## Verification performed this audit (for the record)

- `git diff 5fdf619ec124b9bfb566801172ece5e320679880 --stat` (noise-excluded): confirms only the four
  authorized files changed (`apps/backend/tests/test_desk_ui_guards.py`,
  `apps/frontend/app/desk/page.tsx`, `apps/frontend/lib/api.ts`, `apps/frontend/lib/types.ts`) — zero
  backend product modules touched.
- `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_ui_guards.py -q` → 80 passed, 0
  failed (re-run live, not merely cited from the dev/audit handoffs).
- Live count of `tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple → 22 (unchanged); zero MCP files
  in the diff.
- Grep-verified DOM insertion order (`page.tsx:12034-12084`): Microscope Readiness → Scout Ledger →
  Walk-Forward → Validation Vault, matching blueprint.md's nav-skeleton block exactly.
- Grep-verified single fetch inside `ValidationVaultSection` (no `/research/datasets`, no
  `microReadinessResult` reference within the component body).
- Grep-verified no duplicate `data-testid` or `CollapsibleSection` id across the three new sections
  and the rest of the file.
- Cross-read `docs/handoffs/goal-rapid-microscope-iter-14-audit.md` (independent auditor,
  PASS_WITH_GAPS) and independently re-derived its F1 (poll-leak fix present via
  `microComputePollStopRef` — declared `page.tsx:9711`, checked `:9962-9964`/`:10031-10033`, reset
  `:9986`/`:10052`, raised at `:10189-10196` inside the page's pre-existing unmount cleanup effect,
  not a second effect) and F2 (Scout trial rows keyed
  `` `${trial.candidate_id}-${trialIndex}` `` at `page.tsx:6232`, not the spec hash alone) fixes
  directly from the diff rather than taking the report's word for it.
