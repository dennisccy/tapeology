# goal-rapid-microscope-iter-9 Execution Plan

Session: rapid-microscope. Target journeys: **J-06** (step 3 of 5 only), **J-10**.
Required-still-passing: **J-01, J-02, J-03, J-04, J-05**. Depth: **full** (mandatory — prior
verdict ESCALATE). Scope is deliberately narrow: this is `vault.py` alone, split off from J-06
steps 4-5 by an explicit operator ruling, precisely so the independent auditor's full-depth lane
survives the wall-clock budget this time. **Do not widen scope beyond what is listed below** —
that is the single biggest risk to this iteration succeeding.

Alignment check: this iteration advances `docs/goal.md` Success Criteria #5 ("the recorder and
the vault are real") and Key Capability 7 (`vault.py`) directly, and every anti-goal it touches
(sealed-shard refusal, single-shot exposure, denominator-never-shrinks, vault-secret secrecy) is
carried verbatim from goal.md's Rapid-Microscope anti-goals into the phase spec's own DEFINITION
OF DONE. No drift found; no scope creep to flag — the phase spec's OUT OF SCOPE section is
already self-policing (defers step 4/5, defers the registration CLI, defers MCP/UI wiring) and
is, if anything, more conservative than the umbrella goal.

## What to Build

1. **`vault.py`** — universe registration (rule-hash committed before any fetch) and the
   `sealed → assigned → exposed` one-way shard-lifecycle ledger, both hash-chained via the
   EXISTING `HashChainedLedger` primitive (no fourth chain implementation). HMAC-based seal
   assignment, independent of the existing published split axis. §7.5 opaque pre-exposure
   serving.
2. **`GET /research/desk/micro/vault`** — read-only proxy of vault.py's own state (no CLI/compute
   route this iteration — see Decomposer assumption below).
3. **The exposure-registry sealed filter** — closes the known latent hole: `TICK_LEGACY_CORPUS_ID`'s
   r2 seed in `walkforward.py` must never mark a currently-sealed shard's window "exposed."
4. **Spec §2.6 rule-text + verification-note fields** — two new optional, checksum-excluded
   manifest kwargs on `DatasetStore.record`/`record_from_source`, wired into
   `tick_recorder.py`'s existing `_finalize_day` call.
5. **Two named test-hygiene fixes** in `test_tick_recorder.py`, carried from iteration 8's review.

## Agents Required

- **backend-data: yes** — all five items above are backend-only (new module, one new GET route,
  a targeted fix in an existing module, two new optional dataclass/manifest fields, one existing
  call site updated, one test-file cleanup).
- **frontend-ux: no** — zero `.tsx`/`.ts` files change this iteration. The Validation Vault UI
  section is explicitly J-08 scope; this iteration's own J-06 acceptance requires an element
  capture PROVING that section still does not render (see Testing below), not building it.

## Frontend Present: yes

Read literally as a plain line for the browser-qa grep — do not let this look like a
contradiction of `frontend-ux: no` above. It is not: `Frontend Present: yes` is the standing
mechanical trigger (iter-5/6/7/8 precedent, restated in the dev handoffs each time) that keeps
`browser-qa-phase.sh`'s ENTIRE browser lane alive, including the required-still-passing
regression set (J-01-J-05) and the J-10 kept-product sentinel — none of which this iteration
touches in `.tsx`, but all of which must still be re-verified on-screen via the store-scoped rig
per the CARRIED CONTEXT instruction that dropping this lane has already cost two ESCALATE
verdicts. There is no new or changed UI surface in this diff.

## Files to Create/Modify

- `apps/backend/app/research/vault.py` **(NEW)**. Build on:
  - `micro_chain_ledger.HashChainedLedger` (`micro_chain_ledger.py:56`) — `.append_row(fields)`,
    `.all_rows()`, `.verify_chain()`. The phase spec names TWO distinct ledgers: the universe
    registration ledger and the shard-lifecycle exposure ledger (mirror
    `walkforward_ledger.WalkForwardLedger`'s "thin domain wrapper over ONE `HashChainedLedger`"
    shape, `walkforward_ledger.py:89-94`, once per ledger).
  - `scout_ledger.compute_family_root_id` (`scout_ledger.py:127`) for `family_root_id` — import,
    never reimplement (TR-20 depends on this being the one identity function).
  - `tick_recorder.recorder_split_for` (`tick_recorder.py:190`) for the PUBLISHED split axis —
    vault.py adds ONLY the new, independent seal axis; it must not reimplement split.
  - Seal assignment: `HMAC-SHA256(vault_secret, f"{symbol}:{YYYY-MM-DD}")`, sealed iff the last
    hex digit < `VAULT_SEAL_HEX_BELOW` (spec §1, =4). Secret read once from the path named by
    `TAPEOLOGY_VAULT_SECRET_FILE` (a NEW env var — no existing "_SECRET_FILE" precedent in this
    codebase, so this is genuinely new small code). A missing/unreadable file is a typed
    configuration-refusal exception — never a crash, never a fabricated default. Only
    `sha256(vault_secret)` is ever recorded (on the universe registration row) or logged — the
    raw secret must not appear in any row, log line, or the ledger file itself (TC-5).
  - §7.5 opaque serving while `sealed`: `shard_id`, `universe_id`, a coarse size bucket
    (order-of-magnitude, never an exact count), the checksum commitment, `sealed_at`,
    `exposure_state` — nothing else. Symbol/date/exact counts appear only from `assigned` onward,
    recorded in the SAME exposure ledger row (TC-6/TC-7).
  - Storage dirs: follow the established `TAPEOLOGY_MICRO_*` env-var-or-sibling-default family
    (`scout_ledger.py:99`'s `TAPEOLOGY_MICRO_SCOUT_DIR` is the direct naming precedent) — e.g.
    `TAPEOLOGY_MICRO_VAULT_DIR`. Zero new `Config` field.
- `apps/backend/app/research/micro_routes.py` — add the `GET /vault` route mirroring the
  existing GET-only shape of `get_scout()` (`micro_routes.py:197-218`, including surfacing
  `verify_chain()` beside the served state, the same pattern scout's own route already uses).
  Add a `Depends()`-injected ledger-dir provider mirroring `get_scout_ledger_dir`
  (`micro_routes.py:178`). GET-only this iteration — no `/vault/compute` route, no CLI (see
  Decomposer assumption below); TR-2's route sweep needs a real route, which this provides.
- `apps/backend/app/research/walkforward.py` — the sealed filter, at the r2 seed call site
  inside `run_diagnostic_walkforward` (`walkforward.py:1111`, the guarded block at
  `:1194-1201`) and/or `_tick_dataset_session_dates` (`:985-1010`): exclude any dataset id
  vault.py currently reports `sealed` from the date list before it reaches
  `initialize_r2_exposure_registry`. Naming precedent to reuse for consistency:
  `micro_accessor.py:213`'s existing `sealed_dataset_ids: frozenset[str] = frozenset()`
  constructor parameter is the same concept already named once in this codebase. **T-2
  reminder**: this is the WALKFORWARD exposure registry — a different ledger, file, and identity
  key from vault.py's OWN shard-lifecycle ledger above. Bridge them (vault.py answers "which
  dataset ids are sealed"); never merge their storage or vocabulary.
- `apps/backend/app/research/datasets.py` — two new optional kwargs, siblings of the existing
  `schema_basis`/`quote_size_unit` pair, on `record()` (`datasets.py:486`, params at `:499-500`,
  `meta[...]` stamps at `:557-560`) and `record_from_source()` (`:619`, params at `:629-630`):
  `quote_size_unit_rule_text: str | None = None`, `quote_size_unit_verification_note: str | None
  = None`. Stamp into `meta` only when supplied. Critical: do **not** add them as parameters to
  `_content_checksum` (`datasets.py:256`) — that omission is exactly what keeps them out of the
  content hash, proven by TC-13's byte-identical-checksum counter-test, matching
  `schema_basis`/`quote_size_unit`'s own already-proven exclusion.
- `apps/backend/app/research/tick_recorder.py` — the existing `_finalize_day`
  (`tick_recorder.py:408-445`) `record_from_source(...)` call (`:431-442`) gains the two new
  kwargs: `quote_size_unit_rule_text` = the frozen §2.6 vendor-rule sentence verbatim;
  `quote_size_unit_verification_note` = a note naming the comparison and
  `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` (`tick_recorder.py:166`) that produced THIS dataset's stamp.
- `apps/backend/tests/test_tick_recorder.py` — two named hygiene fixes (both located and
  confirmed during planning, not left for the developer to re-find):
  1. Delete the unused stand-in class `_StrippedTradeEventMissingConditions` (lines 282-289).
     Confirmed dead: it appears exactly once in the file (its own definition) and
     `test_tc8_the_recorder_refuses_to_record_anything_when_the_preservation_capability_is_absent`
     (starting line 292) builds its own `IncompleteTrade` via `dataclasses.make_dataclass`
     instead, with an inline comment explaining why that approach was chosen over hand-rolling
     `__dataclass_fields__`. Delete the class; the test needs no other change.
  2. Fix the stale file-path reference in the docstring at line 547
     (`test_tc7_cancel_on_an_idle_manager_is_rejected_by_the_route_layers_own_409_contract`): it
     says "tested at the route layer in `test_micro_routes_recorder.py`" — that file does not
     exist. The route-layer tests actually live in THIS SAME file (the iter-8 handoff's own
     "routes 9" count, part of its 36 tests). Reword to name the actual location.
- `apps/backend/tests/test_vault.py` **(NEW)** — TR-2/4/12/20 plus TC-1 through TC-9, on
  fixtures. Reuse the two already-committed tick fixtures at
  `apps/backend/tests/fixtures/datasets/` (1 symbol, 1 date, 2 shards — the same ones iter-2/3
  already used for rig seeding) rather than inventing new fixture data where these suffice.
- `apps/backend/tests/test_walkforward.py` — extended for TC-10/TC-11 (the sealed filter).
- `apps/backend/tests/test_datasets.py` — extended for TC-12/TC-13 (the two new fields + their
  checksum exclusion).
- `docs/handoffs/goal-rapid-microscope-iter-9-dev.md` — dev handoff (required deliverable).

### Decomposer assumptions carried into this plan (already logged, not to be re-litigated)

- Ship the read-only `GET /vault` route only — no universe-registration CLI/route. No operator
  act in this iteration or the next calls registration standalone; that lands with step 4.
- The sealed filter excludes vault-sealed dataset ids from `TICK_LEGACY_CORPUS_ID`'s r2 seed
  windows, at the seed call site named above — the minimal fix restoring the invariant without
  inventing a second exposure concept.

## UI Evolution

None. No new user-facing capability, no new information displayed, no new user actions, no UI
surface change. `GET /research/desk/micro/vault` is a new endpoint with no UI consumer yet (that
is J-08). This iteration's own J-06 acceptance is partly proven by a browser capture showing the
Validation Vault section's continued, correct ABSENCE from `/desk` (see Testing below) — the
opposite of a UI addition.

## Visual Requirements

None — no rendering work this iteration.

## Key Test Scenarios

Full TC-1..TC-18 detail lives in the phase spec (`docs/phases/goal-rapid-microscope-iter-9.md`)
— read it directly rather than re-deriving from this summary:

- **Vault mechanics (TC-1..TC-9, new `test_vault.py`)**: unregistered `universe_id` refuses
  (never validates silently); `rule_hash` round-trips exactly; cherry-picked batches refuse
  naming the specific gap (TR-4), disclosed-failure batches pass; HMAC seal decision is
  deterministic and the raw secret never appears in any row or log (TC-5); a `sealed` shard's
  served entry carries ONLY the §7.5 fields (TC-6/TR-2); `assigned` reveals symbol/date and
  `verify_chain()` stays `{"ok": true}` (TC-7); a second (family, shard) evaluation is refused
  with no new ledger row (TC-8/TR-12); `compute_family_root_id` reuse proves a rename cannot
  evade that refusal (TC-9/TR-20).
- **Sealed filter (TC-10/TC-11, extended `test_walkforward.py`)**: a sealed fixture dataset's
  session-date window carries no r2 exposure entry while an unsealed sibling's does; once later
  exposed through the vault's own lifecycle, the window still never double-appears in the
  legacy-corpus r2 seed.
- **§2.6 fields (TC-12/TC-13, extended `test_datasets.py`)**: `tick_recorder._finalize_day`'s
  recorded manifest carries both new fields verbatim; `_content_checksum` is byte-identical with
  and without them supplied.
- **Test hygiene (TC-14)**: the dead class is gone; the docstring names the correct file.
- **Regression + frozen foundations (TC-15/TC-16)**: full backend suite ≥ 3,092 pass / 0 fail;
  `config_fingerprint()` → `08e471b10130e1e2`; all six `referee_*.py` SHA-256 hashes unchanged;
  `EXPECTED_TOOLS` still the 22-tuple; a byte-for-byte hash of the real `.data/datasets` store
  taken before and after this iteration's dev/test work is identical (all work happens against a
  scoped throwaway copy, never the operator's real store).
- **Browser (TC-17, store-scoped rig `:8301`/`:3301`, `rm -rf apps/frontend/.next` rebuild
  first)**: J-06's browser proof this iteration is an element capture of `/desk` confirming the
  Validation Vault section is genuinely ABSENT (proving OUT OF SCOPE held — there is no on-screen
  pass to check yet, since step 3 ships no UI); J-01-J-05 re-verified green (deterministic replay
  where a golden script exists, LLM fallback otherwise — read the LLM lane's own
  `...-ui-test-results.llm.md` verdict directly per the iter-6 lesson, never a merged headline);
  J-10 sentinel: cockpit `/` live-tape+chart, `/structure` load + Tradable Map, every shipped
  `/desk` section (including the three Referee sections), all screenshotted on record.
- **Independent auditor (TC-18)**: full-depth lane MUST run against this diff (this is the
  entire reason this iteration was split down to step 3 alone — do not let it be trimmed). Its
  findings are fixed in-iteration or explicitly carried forward by name in the dev handoff —
  never silently dropped. Prior full audits caught a real integrity fault in 4 of the last 4 runs
  where they were allowed to execute; this diff's highest-risk surface for exactly that kind of
  fault is the seal/exposure state machine (TR-12/TR-20 single-shot discipline) and the vault
  secret's non-leakage (TC-5) — the auditor should weight those first.

## Error Cases (from the spec, do not skip)

An unregistered `universe_id` refuses; a cherry-picked batch names the missing entry; a second
(family, shard) evaluation attempt refuses; a sealed shard's route/accessor read surfaces only
§7.5 metadata, never rows; a missing/unreadable `TAPEOLOGY_VAULT_SECRET_FILE` at seal-assignment
time is a typed configuration refusal, never a crash and never a fabricated default secret.
