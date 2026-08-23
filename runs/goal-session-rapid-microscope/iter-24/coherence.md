# Iteration 24 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-24
**Date:** 2026-08-23
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Backend-only functional change (frontend touched only for a display-formatter swap, no new
component/route): `vault.py`'s `_serialize_shard` now coarsens the served `sealed_at` field from a
full-precision ISO timestamp to date-only precision, uniformly across `sealed`/`assigned`/`exposed`
states; `j06_operator.py`'s `stage_tr2()` gained a third, run-aware check that joins the committed
`reports/j06-tranche/recording-runs.json` against the (now-coarsened) served `sealed_at` values.
`journey-scripts/J-09.json` (new golden), `J-08.json`/`J-10.json` (assertion-string swap), a new
QA-fixture seeder, and new/extended unit tests round out the diff. No new page, route, nav entry, or
Data Contract row — matches the blueprint's own iter-24 note (blueprint.md:344-350) and the iter
spec's "Blueprint conformance" / "Data-contract additions: None" fields.

Note: the post-QA auditor (a separate pipeline gate, `docs/handoffs/goal-rapid-microscope-iter-24-
audit.md`) already found and fixed a real frontend regression this iteration introduced — the
Validation Vault "Sealed at" cell briefly rendered the new date-only value through the wrong
formatter (`formatDateTimeET`, an instant formatter) and showed the previous calendar day plus a
fabricated time. That fix (`apps/frontend/app/desk/page.tsx:6801`, swap to the pre-existing
`formatDayMarker`) is already committed in the working tree and is what this audit evaluates below.
That defect was a functional/rendering bug (browser-qa's and the auditor's domain), not itself a
coherence-contract violation — see Data Contract check.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `sealed_at` (sub-field of "Vault shards, universes, exposure ledger", owner `vault.py`, endpoint `GET /research/desk/micro/vault`) | OK | Coarsening happens at exactly one serve-time point: `apps/backend/app/research/vault.py:1486-1497` (`_coarsen_sealed_at_to_date`, called once from `_serialize_shard`'s `opaque["sealed_at"]` assignment, inherited by `assigned`/`exposed` rows via `revealed = {**opaque, ...}`). The underlying ledger row is proven untouched (`test_vault.py::test_tc2_...`). Frontend reads the same canonical endpoint and reformats the (unchanged-shape) string with `formatDayMarker` (`apps/frontend/app/desk/page.tsx:6804`, a pre-existing formatter — not new) — this is display-layer reformatting of a canonically-sourced value, which Part A rule 3 explicitly permits, not a violation. |
| "Scout trials, kills, denominators, screens" (Study 3 pilot-study row, surfaced via J-09) | OK | The new J-09 QA fixture seeder (`apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py`) plants its row through `scout.register_screen_and_walkforward_check` — the same production entry point the `POST /research/desk/micro/scout/compute` route and the CLI's `--grid` path both call (dev handoff, "J-09 Golden" section). No second computation path introduced; the new golden asserts a `family_id` string rendered from the already-registered endpoint's own served data. |
| `stage_tr2()`'s run-aware check output (`j06_operator.py`) | OK — not a Data Contract item | Confirmed via `git diff` on `apps/backend/app/meta.py` (empty) and the ui-surface-map's "Backend-Only Changes" list: this is an operator CLI computation with no route and no UI surface, consulted only by `j06_operator.py verify`/`tr2`. It reads the canonical `vault.build_vault_state(...)` for the served side of its join rather than recomputing shard state independently, so even as an internal tool it stays single-sourced. |

No new displayed value/entity was introduced this iteration outside the above (the J-09 golden
displays only already-registered Scout Ledger fields).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` → Validation Vault (`sealed_at` display change) | OK | `apps/backend/app/meta.py` — zero diff against the snapshot SHA (`UI_ROUTES` untouched). No new page/route/component; same `ValidationVaultSection`, same position in the section order (Microscope Readiness → Scout Ledger → Walk-Forward → Validation Vault), confirmed unchanged by both the ui-surface-map and live browser evidence (UT-09, `reports/phase-goal-rapid-microscope-iter-24-ui-test-results.md`). |
| `/desk` → Scout Ledger (J-09 pilot-study row) | OK | Same pre-existing `ScoutLedgerSection`, already registered in the blueprint IA table as J-09's canonical home ("Pilot studies (J-09) ... `/desk` → Scout Ledger / Walk-Forward"). No parallel page or shell introduced. |

`git diff` on `apps/frontend/` is a single 8-line hunk in one existing file (`app/desk/page.tsx`,
one call-site formatter swap) — confirmed via `git diff --stat`. No new frontend component, no new
route, no nav-skeleton edit.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The post-QA auditor's T4 finding is worth carrying forward, though it is a test-rigor concern, not
  a coherence-contract violation: `journey-scripts/J-08.json` step 3 and `J-10.json` step 12 now both
  assert the string `"Ledger chain verification:"`, which appears twice in `page.tsx` (Scout Ledger
  at `:6282` and Walk-Forward at `:6518`). It currently discriminates only because both scripts
  happen to expand Walk-Forward in a later step than the assertion in question; reordering either
  script would make the assertion satisfiable without the Scout Ledger ever opening. Not a Data
  Contract or IA rule (it is a replay-harness assertion choice, not a served value or a nav path),
  so it does not affect this verdict, but the next iteration touching either script should pick a
  section-unique string instead.
- `stage_tr2()`'s two halves (combinatorial vs. run-aware) reuse the field name
  `candidate_identities_per_unexposed_selected_shard` for two related-but-distinct quantities
  (audit report B2). This is entirely internal to an un-served operator CLI tool (confirmed no
  route/UI surface), so it carries no Data Contract implication — noted only for completeness.
