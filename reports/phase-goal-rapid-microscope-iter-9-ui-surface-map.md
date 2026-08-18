# Phase goal-rapid-microscope-iter-9 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-9
**Date:** 2026-08-18
**Written by:** ui-impact-analyst

---

**Reading this map:** this iteration's diff touches zero frontend files (`git status --porcelain`
confirms exactly 9 changed backend files: 5 source including the new `vault.py` + 4 test files
including the new `test_vault.py` — 0 `.tsx`/`.ts`/`.css`). Every row below is either (a) a
**pre-existing, unmodified surface** the browser-QA lane must re-verify only because
`Frontend Present: yes` forces the browser lane to dispatch, or (b) a **negative check** — proving
a surface this iteration's own target journey (J-06) requires to still be absent. There is no new
UI surface to map; inventing one would misrepresent the diff. Three groups of rows exist for three
different reasons:

1. **J-06's own absence proof** — the phase spec's Testing Requirements state this iteration's
   browser evidence for J-06 is "an element capture of `/desk` confirming the Validation Vault
   section is genuinely ABSENT" (there is no on-screen pass to check yet — step 3 ships no UI). This
   is the one row this iteration adds that no prior iteration's map needed, because no prior
   iteration had a Vault to prove absent.
2. **J-01's Microscope Readiness section** — this iteration's diff touches
   `apps/backend/app/research/datasets.py` and `apps/backend/app/research/walkforward.py` again
   (the same two modules iteration 7 touched, for unrelated reasons this time — two new optional,
   checksum-excluded manifest kwargs, and a sealed-shard exclusion inside a diagnostic walk-forward
   seed path). Neither change is read by `micro_readiness.py` (independently confirmed: it imports
   neither `walkforward.py` nor `vault.py`, and its `exposure_state` value for legacy shards is a
   hardcoded constant, not a computed one), so the section must render byte-identically to before —
   this is the narrowest, highest-stakes regression check in this iteration's browser pass.
3. **J-10's kept-product sentinel** — `journey-scripts/J-10.json`'s 13-step walk (cockpit →
   `/structure` → several `/desk` sections), reused byte-unmodified this iteration. The rows below
   decompose its 13 steps by surface. None of the code these steps exercise (cockpit tape rendering,
   `/structure`'s bar/level engine, the Playbook/Referee sections) is anywhere in this iteration's
   diff — the vault/walk-forward/dataset changes are entirely inside the tick-recording and
   diagnostic-walk-forward pipelines, a different code path from what these steps read.

J-02, J-03, J-04, and J-05 (the other required-still-passing journeys) have **no dedicated UI
element of their own** — independently confirmed by reading `apps/frontend/app/desk/page.tsx`
directly: the page's `DeskCollapsibleSection` type (line 358) lists exactly 10 possible sections
(`topupRuns`, `indexReconciliation`, `screenRuns`, `screenComparison`, `provenance`,
`playbookEvidence`, `refereeRegistry`, `refereeAdjudications`, `refereeRuns`, `microReadiness`) — no
`scoutLedger`, `walkforward`, or `vault` section exists in the current build. That UI is J-08 scope
(`docs/goal.md` J-08 step 1 names all three — Scout Ledger, Walk-Forward, Validation Vault — as the
sections landing there). Row 2 below (whole-page load) is the correct substitute for all four,
matching how iteration 7's map handled the same absence for J-02/J-03/J-04.

Of the 10 possible sections, two (`screenComparison`, `provenance`) render only once a screen has
been computed in the running rig instance (`{latest !== null && (...)}` guards at
`apps/frontend/app/desk/page.tsx:10888` and `:10907`); the other eight always render. This is a
pre-existing, unmodified conditional — not something this iteration changed — but it means "exactly
10 sections" is not a safe assertion regardless of rig state; the rows below phrase it correctly.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Whole-page section list — confirms no "Validation Vault" section exists (`data-testid="desk-section-expand-vault"` absent) | Negative check (this iteration's own J-06 acceptance proof) | The phase spec requires an element capture proving the Validation Vault section is genuinely absent this iteration — `vault.py` and `GET /research/desk/micro/vault` are built, but no `/desk` section renders them (J-08 scope) | Navigate to `/desk`, wait for the page to load, and scroll from the "Playbook Signals" heading at the top all the way to the bottom of the page. Verify the text "Validation Vault" does **not** appear anywhere on the page, and that no element with `data-testid="desk-section-expand-vault"` exists. Verify the last section on the page is still "Microscope Readiness" (`data-testid="desk-section-expand-microReadiness"`) — nothing renders below it |
| `/desk` | Microscope Readiness section (`data-testid="micro-readiness-section"`, collapsible id `microReadiness`) | Regression check (unmodified this iteration) | This iteration's diff touches `datasets.py`'s manifest-stamping code and `walkforward.py`'s diagnostic-run seed path — but adds no new served field to the readiness endpoint (the two new §2.6 kwargs are additive/optional and no caller supplies them this iteration) and the sealed filter only fires inside a code path `micro_readiness.py` never reads — so the endpoint and section must render byte-identically to before | Navigate to `/desk`, click the section header `data-testid="desk-section-expand-microReadiness"` to expand it, and verify: (1) the "Corpus Totals" table (`data-testid="micro-readiness-totals-table"`) shows "Distinct symbol-days" = **1** and "Distinct datasets" = **2** — this store-scoped QA rig seeds exactly 2 committed fixture datasets (`tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json`, `.../d9f9dbe04fb24a7caccc53f0c6805412.json`, both independently re-opened for this report and confirmed symbol `PG`, session date 2026-06-09), never the real store's 12/18; (2) the "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"`) lists exactly **2** rows (`data-testid="micro-readiness-shard-rows"`), both Symbol = `PG`, Session date = `2026-06-09`, Split provenance = `hand_assigned`, Exposure state = `exploratory`; (3) the shard table still has exactly 12 columns (Symbol, Session date, Feed, Window (ET), Trades, Quotes, Bytes, Coverage gaps, Fallback frac, Checksum, Split provenance, Exposure state) — no new column for `quote_size_unit_rule_text` or `quote_size_unit_verification_note`, confirming this iteration's two new manifest fields are not surfaced in the UI |
| `/desk` | Whole-page load across the 8 always-rendered sections (confirms no "Scout Ledger" or "Walk-Forward" section exists) | Regression check (unmodified this iteration) | J-02 ("micro observer"), J-03 ("structure × flow join"), J-04 ("Scout and the ledger"), and J-05 ("walk-forward engine") remain backend/CLI/endpoint-only journeys with no browser element of their own; the current build has no section named `scoutLedger` or `walkforward` (confirmed via source) — that UI lands with J-08 | Navigate to `/desk`, verify the "Playbook Signals" heading renders, and confirm these 8 section headers are all present somewhere on the page (in any screen state): "Top-up Runs", "Index Reconciliation", "Screen Runs", "Playbook Evidence", "Referee Registry", "Referee Adjudications", "Referee Runs", "Microscope Readiness" — plus "Screen Comparison" and "Provenance" if a screen has already been computed in this rig session. No error banner appears anywhere, and the browser console shows no unhandled exception |
| `/` (cockpit) | Ticker watch panel | Regression check (unmodified this iteration; J-10 steps 1–3) | Part of J-10's 13-step kept-product sentinel (`journey-scripts/J-10.json`, byte-unmodified); this iteration's vault/recorder-adjacent changes touch only the tick-recording and diagnostic-walk-forward pipelines, entirely separate from the cockpit's live-tape rendering | Navigate to `/`, verify the text "No ticker watched" appears, type `SIM-BUYER` into the field labeled "Ticker", click the "Watch" button, and verify the text "Buyer Control" appears |
| `/structure` | Tradable Map load | Regression check (unmodified this iteration; J-10 steps 4–7) | Same J-10 sentinel; `/structure` reads the Yahoo/BarStore bar pipeline, entirely separate from this iteration's tick-dataset/vault diff | Navigate to `/structure`, verify the text "Tradable Map" appears, type `AAPL` into the field labeled "Structure symbol", type `2026-06-22 17:00:00` into the field with `data-testid="structure-as-of-input"`, click the element with `data-testid="structure-load-button"`, and verify the text "300.11–302.2" appears |
| `/desk` | Playbook Evidence section | Regression check (unmodified this iteration; J-10 steps 8–10) | Same J-10 sentinel; reads already-recorded playbook signal data, unrelated to this iteration's tick/vault diff | Navigate to `/desk`, verify the "Playbook Signals" heading appears, click `data-testid="desk-section-expand-playbookEvidence"`, verify the text "Built from signature:" appears, type `2026-06-22` into the field with `data-testid="desk-playbook-date-input"`, and verify the text "recorded signals, none hidden" appears |
| `/desk` | Referee Registry section | Regression check (unmodified this iteration; J-10 step 11) | Same J-10 sentinel | Click `data-testid="desk-section-expand-refereeRegistry"` and verify the text "config fingerprint 08e471b10130e1e2" appears — the same frozen fingerprint this iteration's own backend check independently re-verifies (dev handoff: `Config().config_fingerprint()` → `08e471b10130e1e2`, zero new `Config` fields added) |
| `/desk` | Referee Adjudications section + Referee Runs section | Regression check (unmodified this iteration; J-10 steps 12–13) | Same J-10 sentinel | Click `data-testid="desk-section-expand-refereeAdjudications"` and verify the text "No hypotheses registered" appears; click `data-testid="desk-section-expand-refereeRuns"` and verify the text "No evaluation runs recorded yet." appears |

<!-- Change Type is "Regression check" or "Negative check" throughout — no row above reflects a code change to a rendered surface; the first row exists because this iteration's own J-06 acceptance requires proving absence, and every other row exists because Frontend Present: yes forces the browser lane to genuinely exercise the kept product. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/vault.py` **(NEW, 528 lines)** — universe registration
  (`register_universe`/`find_universe`), the batch verifier (TR-4 cherry-pick refusal), HMAC seal
  assignment (`compute_seal`, secret sourced from `TAPEOLOGY_VAULT_SECRET_FILE`, never logged), and
  the one-way `sealed → assigned → exposed` shard-lifecycle ledger (`seal_shard`/`assign_shard`/
  `expose_shard`, TR-12 single-shot refusal) — no UI surface affected; nothing in the frontend
  imports or references this module (confirmed by grep: zero matches for "vault" under
  `apps/frontend/`).
- `apps/backend/app/research/micro_routes.py` — adds `GET /research/desk/micro/vault`, a read-only
  proxy of `vault.build_vault_state()` — no UI surface affected; no frontend code calls this path.
- `apps/backend/app/research/walkforward.py` — `_tick_dataset_session_dates` gains an additive
  `sealed_dataset_ids` kwarg (default-empty, byte-identical for the existing call site that omits
  it); `run_diagnostic_walkforward`'s r2 seed for `TICK_LEGACY_CORPUS_ID` now excludes
  currently-sealed dataset ids before seeding exposure entries — no UI surface affected; this
  function is reachable only from the diagnostic-walk-forward code path, which has no `/desk`
  section (J-08 scope, per the map's own preamble above).
- `apps/backend/app/research/datasets.py` — `DatasetStore.record`/`record_from_source` gain two new
  optional, checksum-excluded kwargs (`quote_size_unit_rule_text`, `quote_size_unit_verification_note`)
  — no UI surface affected; the Microscope Readiness shard table has no column for either (see the
  regression row above), and no existing caller other than `tick_recorder.py` supplies them.
- `apps/backend/app/research/tick_recorder.py` — new `QUOTE_SIZE_UNIT_RULE_TEXT` constant and
  `quote_size_unit_verification_note()` helper; `_finalize_day` now supplies both new fields on every
  call — no UI surface affected; `_finalize_day` only runs during a live, credentialed recording
  (J-06 step 4), which did not happen this iteration, so no dataset on disk is affected by this
  change yet either.
- `apps/backend/tests/test_vault.py` **(NEW, 24 tests)**, `apps/backend/tests/test_walkforward.py`
  (+2 tests), `apps/backend/tests/test_datasets.py` (+3 tests), `apps/backend/tests/test_tick_recorder.py`
  (+1 test, plus the two named hygiene fixes: a dead stand-in class deleted, a stale docstring file
  reference corrected) — test files, no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 9 (5 source files, 1 of them new, + 4 test files, 1 of them new)
- **Pre-existing/negative-check surfaces requiring re-verification this iteration:** 8 rows above
  (Validation Vault absence proof, Microscope Readiness section, `/desk` whole-page section-list
  check, cockpit ticker watch, `/structure` Tradable Map, Playbook Evidence section, Referee
  Registry section, Referee Adjudications + Referee Runs sections)
