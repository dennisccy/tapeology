# goal-rapid-microscope-iter-13 Execution Plan

Alignment check: on-goal, no drift. Closes a genuine hole in TR-25/spec §7.8 (vault-ledger
integrity) that iteration 12's own auditor found: `recover_shard_ledger`'s "not proven complete"
branch only names dataset ids visible in the surviving verified PREFIX, so a shard whose only row
lived entirely in the destroyed suffix escapes `exposure_unknown` marking altogether — while
`rewrite_from_recovery` still re-heals the tail anchor, so `verify_chain()` reports clean
afterward. This directly serves Success Criterion #2 ("No leakage trap fails, ever") and the
Anti-goal "Sealed exposure is family-level and single-shot — never a second draw." Everything
ruled out-of-scope in the phase spec (the seal/assign/expose gate-widening pair, J-08/J-09,
TR-23/24/26, the case-sensitivity asymmetry, any frontend file) is a deliberate owner ruling
already logged in `state/assumptions.md`, not an omission — excluded here accordingly.

## What to Build

- **`recover_shard_ledger`'s three-way split** (`vault.py:1447-1558`), replacing today's two-way
  (proven-complete / mark-prefix-only) logic:
  1. **Proven-complete** — unchanged: reconstructed prefix+suffix hash-matches the tail anchor
     exactly; ledger rewritten, service resumes with the exact prior exposure state.
  2. **Named-but-unverified** — anchor-attested row COUNT matches (every row is at least named by
     a dataset_id) but the hash-attested completeness check fails on content: mark the UNION of
     prefix-named AND suffix-named dataset_ids `exposure_unknown` (today: prefix only — the bug).
     Resumes (`ok: False`, `resumed: True`).
  3. **Row-count deficit or unreadable/missing anchor** — the true row count cannot be bounded:
     refuse to resume at all. Never call `rewrite_from_recovery`; the corrupted file stays
     untouched; `verify_chain()` keeps reporting `ok: False`; every dependent predicate
     (`currently_sealed_dataset_ids`, `withheld_dataset_ids`,
     `unresolved_pool_universe_by_dataset_id`, `build_vault_state` — all gated through
     `verified_rows()`) keeps raising `VaultLedgerCorruptionError`. Still append an immutable
     `recovery_incomplete`-style incident row to `recovery_ledger` (spec §7.8's "or the whole
     tranche halts" disjunct). This is the exact hole iteration 12 found — closes it.
  Both halt-widening and union-widening ship in the SAME diff (the session's own pairing lesson:
  widening one side of the fix while leaving the other narrow reopens an equivalent leak).
- **Docstring-only pin**: `seal_shard`/`assign_shard`/`expose_shard` (`vault.py:880/941/971`)
  document that their corruption gating is deliberately scoped to their own shard ledger only —
  resolves iteration-12's open reviewer question as a recorded decision, zero behavior change. A
  pinning test proves a truncated universe ledger does not change what these three write.
- **Docstring-only fix**: `micro_routes.py`'s `get_tick_recorder_compute` (~:482-505) — correct
  the stale `trades_total`/`quotes_total` field names to the actual served
  `trades_total_bucket`/`quotes_total_bucket` (iteration 12 already shipped the bucket fields;
  only the prose is stale).
- **Test-first correction, not a guard-test edit**: `test_vault.py`'s three existing TC-5-named
  tests (`test_tc5_an_unprovable_reconstruction_marks_affected_shards_exposure_unknown_permanently`
  :1662, `test_tc5_a_wrong_nonempty_reconstruction_is_also_refused_never_treated_as_proven` :1704,
  `test_tc5_a_shard_recovery_could_not_name_stays_protected_by_the_universe_rule_predicate` :1751)
  currently assert the OLD buggy outcome (two shards sealed, d-2's row truncated, empty/wrong
  suffix supplied → today wrongly resumes and marks only d-1). Verified directly: under the new
  logic, tests 1 and 3 (empty suffix, row-count 1 vs anchor 2 → shortfall) become halt-path
  scenarios (`resumed: False`); test 2 (wrong but same-row-count suffix) becomes a union-marking
  scenario (`exposure_unknown_dataset_ids` must include BOTH d-1 and d-2, not d-1 alone). Revise
  all three plus add: an anchor-missing/unreadable variant, a re-recovery-after-halt test proving
  a later fuller reconstruction against the same untouched corrupted file still succeeds, and the
  seal/assign/expose own-ledger-only pinning test.
- Full backend regression + frozen-rails re-check (fingerprint, 6 `referee_*.py` SHA-256 hashes,
  22-tool MCP count, real `.data` store byte-unchanged) + J-10 kept-product browser sentinel +
  J-01 Microscope Readiness re-check (its `sealed_tranche` aggregate transitively reads `vault.py`).

## Agents Required

- backend-data: yes -- implements the three-way `recover_shard_ledger` split, the two
  docstring-only clarifications, and the test revisions/additions above, TDD (tests first per
  each TC).
- frontend-ux: no -- zero `.tsx`/`.ts`/frontend files touched; no served field, shape, or endpoint
  changes (only docstrings, and internal logic with zero production call sites today).

Frontend Present: yes

Declared `yes` solely so the mechanical browser-QA regression lane runs this iteration — this
iteration ships **zero frontend code**. The lane's job is regression verification only: J-10's
kept-product sentinel (`/`, `/structure`, `/desk` including all shipped sections and the four
already-shipped Rapid-Microscope sections, via the store-scoped rig) and J-01's Microscope
Readiness re-check. No new UI evidence, no new click paths, no evidence retakes pending.

## Files to Create/Modify

- `apps/backend/app/research/vault.py` -- three-way split in `recover_shard_ledger` (:1447-1558);
  docstring-only clarification on `seal_shard`/`assign_shard`/`expose_shard` (:880/941/971).
- `apps/backend/app/research/micro_routes.py` -- docstring fix on `get_tick_recorder_compute`
  (~:482-505); no behavior change.
- `apps/backend/tests/test_vault.py` -- revise the 3 named TC-5 tests (:1662/:1704/:1751) to
  assert the corrected halt/union behavior; add the halt-path tests (TC-1-TC-4), the
  anchor-missing/unreadable variant, the re-recovery-after-halt test, and the seal/assign/expose
  pinning test (TC-7).
- `docs/handoffs/goal-rapid-microscope-iter-13-dev.md` -- new dev handoff (required, TC-12).
- `runs/goal-session-rapid-microscope/state/blueprint.md` -- one documentation-only note
  confirming no new Data Contract row is needed (0 production call sites; matches iteration-12's
  own precedent for `VaultRecoveryLedger`'s content).

No files under `apps/frontend/` change. No `referee_*.py`, `micro_observer.py`,
`micro_features.py`, `micro_graduation.py`, Playbook detector, or `Config` field changes.

## UI Evolution

None — this iteration is backend-only (a recovery-path correctness fix with zero production call
sites). `Frontend Present: yes` is declared purely to trigger the regression/sentinel browser
lane described above, not because any user-facing capability, information, action, or surface
changed. New user-facing capability: none. New information displayed: none (the corrected
`recover_shard_ledger` return shape is consumed by no route, CLI, or UI). New user actions: none.
UI surface changes: none. Navigation changes: none.

## Visual Requirements

N/A — no visual or component changes this iteration.

## Key Test Scenarios

- TC-1/TC-2: a 3-shard ledger (d-1, d-2, d-3) with a valid tail anchor (`row_count=3`); d-3's row
  destroyed; recovery invoked with an empty `reconstructed_suffix` (TC-1) or with the ledger's own
  tail-anchor file itself missing/unreadable (TC-2) -> `resumed: False`, `rewrite_from_recovery`
  never called, `verify_chain()` still `ok: False` immediately after, d-3 appears in no row
  anywhere (not even `exposure_unknown`).
- TC-3: after TC-1's halt, `currently_sealed_dataset_ids`/`withheld_dataset_ids`/
  `unresolved_pool_universe_by_dataset_id`/`build_vault_state` each raise
  `VaultLedgerCorruptionError` rather than returning a result that silently omits d-3.
- TC-4: a second `recover_shard_ledger` call against the still-corrupted ledger from TC-1, this
  time with a byte-correct reconstruction of d-3's row, proves complete; all three shards report
  `sealed` exactly as before corruption; `recovery_ledger.all_rows()` shows both the halted and
  the completed attempts permanently.
- TC-5: a 2-shard ledger (d-1, d-2), tail truncated, `reconstructed_suffix` names d-2 with a
  row count matching the anchor but content that fails the hash-attested completeness check ->
  resumes (`resumed: True, ok: False`) marking BOTH d-1 and d-2 `exposure_unknown` (today's bug:
  d-1 alone).
- TC-6: a fully correct byte-exact reconstruction still resumes exactly as before this iteration's
  changes -- explicit regression pin on the unchanged proven-complete path.
- TC-7: `seal_shard`/`assign_shard`/`expose_shard` docstrings state own-ledger-only scope by
  design; with the universe ledger truncated and the shard ledger intact, all three still succeed
  exactly as before this iteration.
- TC-8: `get_tick_recorder_compute`'s docstring names `trades_total_bucket`/`quotes_total_bucket`,
  never the stale unconditional `trades_total`/`quotes_total`.
- TC-9: full backend suite >= 3212 collected / 3204 passed / 8 skipped / 0 failed, 0 regressions;
  `Config().config_fingerprint()` == `08e471b10130e1e2`; all six `referee_*.py` SHA-256 hashes
  unchanged from iteration 0; MCP `EXPECTED_TOOLS` still the 22-tuple; real `.data` store
  byte-unchanged (18 datasets, no `micro_vault` directory).
- TC-10 (regression): J-01 through J-05 and J-07's stored golden replay scripts (or J-07's
  disclosed LLM browser-qa fallback) all remain `passing`, zero regressions.
- TC-11 (browser, store-scoped rig): J-10 kept-product sentinel -- cockpit `/` live tape+chart,
  `/structure` load + Tradable Map, every shipped `/desk` section (Playbook/Band Context/Cohorts,
  Referee Registry/Adjudications/Runs, and the four already-shipped Rapid-Microscope sections) --
  screenshots match established shipped appearance; trap-suite count reconfirmed at 23 of 28
  (unchanged count; the TR-25 entry is now sound, not merely counted). J-01's Microscope Readiness
  section re-verified.
- TC-12: `docs/handoffs/goal-rapid-microscope-iter-13-dev.md` exists on disk after the iteration.

Error-case coverage (from the spec, do not skip): a recovery attempt that cannot NAME every
anchor-attested row must refuse to resume rather than silently omitting the unnamed shard; a
recovery attempt whose named rows fail the hash check must mark every named dataset (prefix AND
suffix), never a subset; a corrupted universe ledger must not change what
`seal_shard`/`assign_shard`/`expose_shard` write.
