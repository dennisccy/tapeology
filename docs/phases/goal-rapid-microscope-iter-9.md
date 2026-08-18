# Goal Iteration 9 — The sealed-evidence vault (J-06 step 3), alone

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory, no exceptions). Iteration 8's spec
  asked for full but the engine's budget arbiter demoted it to lean, so the independent auditor
  never ran on the diff — the same lane that caught a real integrity fault in 4 of the last 4 full
  iterations. This iteration is the vault: the era's most dangerous remaining change.
- **Frontend Present:** yes
- **Target journeys:** J-06, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05
- **Anti-goal reminders:**
  - No exploratory read of a sealed shard. Event data and outcome aggregates of a `sealed` shard
    are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure; the
    refusal is typed, tested, and fail-closed. *(critical)*
  - Sealed exposure is family-level and single-shot — never a second draw. No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels
    in every later export bundle; no perturbed re-submission resets it. *(critical)*
  - The vault secret never enters the repo, a log, a payload, or a screenshot — only its sha256
    commitment is ever recorded. *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - Deterministic and seeded — every random draw uses a recorded named seed via per-row streams;
    identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in
    any research artifact. *(critical)*
  - The 12 pre-existing tick symbol-days are permanently exploratory — never sealed, never
    `historical_oos`, never relabeled. *(critical)*
  - The denominator never shrinks. Every evaluated variant lands in the hash-chained ledger with
    a closed-vocabulary decision; kills are never deleted; the union-N across grid versions is
    served beside every family. *(critical)*
  - Persistence stays scoped — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP
    surface can change state. *(critical)*

## GOAL

Ship `vault.py` (J-06 step 3): universe registration, the split/seal dual assignment, the
one-way `sealed → assigned → exposed` shard lifecycle, and TR-2/4/12/20 — proven on fixtures,
alone, so the full pipeline (independent auditor included) can finish this dangerous change
inside budget instead of being demoted a third time.

## BACKGROUND

Iteration 8 (ESCALATE) built the tape recorder and closed two prior minor items, but the round
ran short twice for time: the auditor lane never ran (engine.log: "budget-breach"), and 4 of 6
required-still-passing re-checks were deferred. That auditor is the only step this whole session
has caught a dishonesty fault in, and the evaluator named the vault as exactly where the next one
would matter most — it is where a recording becomes un-lookable-at before anyone may read it, and
a wrong one-way state poisons every later export bundle. The evaluator's own next-step
recommendation named step 3 (the vault) as the target and asked for a full, unhurried round; the
operator has since ruled on HOW to protect that round: split step 3 away from step 4 (the
credentialed Alpaca tranche, an operator-attended act) rather than raise the wall-clock budget.
This spec is that split — step 3 only. Step 4 (fetch real tape) and step 5 (refresh readiness with
the new shards) are explicitly deferred to a later iteration; nothing here touches a real vendor
call or the operator's real `.data/datasets` store.

Two small items are folded in because they sit on the exact same manifest/ledger surface this
iteration already opens, and one of them is fixed by the SAME module this iteration builds:

1. **The known latent hole** (carried since iteration 6, restated by iteration 8's eval): the
   WALKFORWARD exposure registry's r2 seed for `TICK_LEGACY_CORPUS_ID` currently derives its
   window list from "every currently-registered tick dataset" (`_tick_dataset_session_dates`
   reads the whole store), with no filter for a dataset that is currently `sealed`. Harmless
   today (nothing is sealed), but the moment vault.py exists this becomes live risk: a freshly
   sealed shard could be marked "already exposed" by a code path that has never heard of sealing.
   Since only vault.py can answer "which dataset ids are sealed right now," this fix is naturally
   sequenced with vault.py's own build, not before or after it.
2. **Spec §2.6's rule-text + verification-note gap** (new finding, operator-flagged): the recorder
   stamps `schema_basis`/`quote_size_unit` but never records the vendor rule text or the
   verification note beside them, though §2.6 requires both ("the recorder records the rule text
   and the verification note beside the stamp"). Dataset manifests are immutable, so this must
   close before any real tape is recorded (J-06 step 4, deliberately not this iteration) — and
   it's a two-field, checksum-excluded addition to the exact manifest machinery this iteration is
   already touching for the vault's own fixture proofs.

Applicable lessons (full text in the session's lessons file, not restated here): iter-7's lesson
on optional manifest fields silently entering an identity/checksum function — the two NEW §2.6
fields here must follow `_content_checksum`'s existing "manifest metadata, not tape content"
exclusion exactly like `schema_basis`/`quote_size_unit` already do, proven by a counter-test, not
assumed. Iter-4(second)/iter-5(second)'s lessons on hash-chained ledgers — tail-truncation
blindness and idempotency-everywhere-except-one-path — apply directly to vault.py's NEW exposure
ledger: reuse `micro_chain_ledger.HashChainedLedger` (the tail-anchored primitive already proven
by `scout_ledger.py`/`walkforward_ledger.py`/`ExposureRegistry`), never a fourth hash-chain
implementation, and TR-12's single-shot check must key on identity (`family_root_id` + shard id),
never on row count. Iter-6's lesson on the J-10 sentinel needing rig-real data, and iter-6(second)'s
lesson on trusting the LLM lane's own verdict file over a merged headline, both apply to how this
iteration's browser evidence should be read.

## IN SCOPE

### Backend

- [ ] New `apps/backend/app/research/vault.py`: universe registration (`{universe_id,
      symbol_rule, date_rule, registered_at, rule_hash}` appended to a NEW vault ledger BEFORE
      any fetch is possible); a batch verifier that refuses a recording batch whose (symbol,
      date) set differs from the universe rule's own computed set net of disclosed failures
      (TR-4); the seal-assignment function (`HMAC-SHA256(vault_secret, f"{symbol}:{date}")` per
      spec §7.3/§1's `VAULT_SEAL_HEX_BELOW`, secret sourced from `TAPEOLOGY_VAULT_SECRET_FILE`,
      never a Config field, never logged — only `sha256(vault_secret)` recorded); the split axis
      is REUSED unchanged from `tick_recorder.recorder_split_for` (no second split implementation).
- [ ] The shard lifecycle: a NEW hash-chained append-only ledger (built on the EXISTING
      `micro_chain_ledger.HashChainedLedger` primitive, same as `scout_ledger.py`/
      `walkforward_ledger.py`/`ExposureRegistry` — no fourth chain implementation) recording
      one-way `sealed → assigned → exposed` transitions keyed on the computed `family_root_id`
      (imported from `scout_ledger.compute_family_root_id`, never reimplemented) plus a shard id;
      TR-12 single-shot refusal (a second assignment/exposure attempt for the same
      (family_root_id, shard) pair is refused, never a new row); TR-20 root-lineage stability
      (proven by reusing the unchanged `compute_family_root_id`, never a second identity
      function). Every ledger row embeds `micro_parameters()` verbatim and keys on its hash,
      matching every other module's discipline this era.
- [ ] Section 7.5 opaque pre-exposure serving: while `sealed`, a shard's served entry carries
      ONLY `shard_id`, `universe_id`, a coarse size bucket (order of magnitude, never an exact
      count), the checksum commitment, `sealed_at`, and `exposure_state` — symbol/date/exact
      counts appear only from `assigned` onward, recorded in the SAME exposure ledger row.
- [ ] `GET /research/desk/micro/vault` in `apps/backend/app/research/micro_routes.py` (the
      Data-Contract-committed serving endpoint, already reserved in `blueprint.md`): serves
      vault.py's own state verbatim (no second computation in the route handler), swept for TR-2
      against a fixture carrying at least one `sealed` and one `assigned`/`exposed` shard.
- [ ] The exposure-registry sealed filter (closes the known latent hole): the caller that seeds
      `TICK_LEGACY_CORPUS_ID`'s r2 window list in `apps/backend/app/research/walkforward.py`
      (`_tick_dataset_session_dates`'s call site around the `TICK_LEGACY_CORPUS_ID` seeding
      block) excludes any dataset id vault.py currently reports `sealed` before the list reaches
      `initialize_r2_exposure_registry` — a sealed shard's window carries no exposure entry from
      the WALKFORWARD registry (a DIFFERENT ledger from vault's own shard-lifecycle ledger above
      — keep the two "exposure" vocabularies distinct, T-2) until the vault's own lifecycle
      exposes it.
- [ ] Spec §2.6 rule-text + verification-note fields: two new optional kwargs on
      `DatasetStore.record`/`record_from_source` in `apps/backend/app/research/datasets.py`
      (`quote_size_unit_rule_text`, `quote_size_unit_verification_note`), stamped into `meta`
      only when supplied, excluded from `_content_checksum` exactly like the existing
      `schema_basis`/`quote_size_unit` fields (manifest metadata, never tape content) — proven
      by a checksum-identity counter-test, not assumed.
- [ ] `apps/backend/app/research/tick_recorder.py`'s `_finalize_day` passes the two new kwargs
      at its existing `record_from_source` call, alongside the existing `schema_basis`/
      `quote_size_unit` stamps: the rule text is the frozen §2.6 vendor-rule sentence verbatim;
      the verification note names the comparison and constant (`ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`)
      that produced THIS dataset's specific stamp.
- [ ] Test-hygiene cleanup carried from iteration 8's review (both named there): delete the
      unused stand-in class and fix the stale file-path reference in
      `apps/backend/tests/test_tick_recorder.py`.

### Frontend

- None. `Frontend Present: yes` is declared solely to keep the browser-qa regression lane
  running for J-01–J-05 and the J-10 sentinel (per the standing iter-4/iter-5 lesson) — zero
  `.tsx` files change this iteration.

### New user-facing capability

None this iteration (backend-only; the Validation Vault UI section is J-08 scope).

### New information displayed

None. `GET /research/desk/micro/vault` is a new endpoint but nothing renders it yet.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible to a user this iteration. The change is entirely inside the research backend: a
new module, a new read-only endpoint with no UI consumer yet, and two small fixes to existing
manifest/registry machinery.

### Blueprint conformance

No new surfaces. `vault.py`'s Data Contract row ("Vault shards, universes, exposure ledger" →
`GET /research/desk/micro/vault`) and its Information Architecture home (`/desk` → Validation
Vault, under Rapid Microscope) are already registered in `blueprint.md` from baseline authoring,
ahead of implementation — the same early-registration pattern the blueprint's own iter-3 footnote
documents and iter-8's coherence audit reused for `tick_recorder.py`. No edit to `blueprint.md`
is needed this iteration.

### Data-contract additions

None. `vault.py`'s row is already registered (see Blueprint conformance above); the two new
`DatasetStore` manifest kwargs are sub-fields of the ALREADY-registered "Corpus readiness truth"
row (owned by `micro_readiness.py`) and are not served by any endpoint yet — they will surface
through readiness reporting in J-06 step 5 (deferred), not this iteration.

## OUT OF SCOPE

- J-06 step 4 (the credentialed Alpaca starter tranche — an operator-attended act) and step 5
  (refresh readiness with new-shard completeness reporting). Both deferred by the operator's own
  ruling to protect this round's budget; nothing in this diff makes a real vendor call or writes
  to the operator's real `.data/datasets` store.
- A CLI or route for universe REGISTRATION (as opposed to the read-only `GET .../vault` route
  above). No operator act in this iteration or the next calls it standalone — it becomes
  operator-facing only when step 4 actually runs (logged as an assumption-ledger entry).
- Wiring `micro_accessor.MicroAccessor`'s existing `sealed_dataset_ids=` parameter into a live
  production call site. No production caller reads tick-corpus snapshot ROWS yet (walkforward's
  tick-family path only checks session counts); inventing a call site with nothing to exercise it
  would violate T-1.
- Any `/desk` UI section or MCP tool for the vault (J-08 scope; MCP stays exactly 22 tools).
- J-07 (Graduation), J-08 (surface + MCP v6), J-09 (pilot studies) — natural dependency order
  keeps them after J-06 completes.
- Any change to the PUBLISHED split rule (`recorder_split_for`), the recorder's walk/checkpoint/
  throttle logic, or anything else already marked DONE in iteration-state's "Do not redo" list.
- The two owner rulings still waiting (the one-quote-early depletion timing stamp;
  whether J-01's readiness photo must show the real 12-day corpus). Carried, not resolved here —
  human-owned, per this agent's own target-selection rubric.
- Writing golden replay scripts for J-01–J-05 as a code deliverable — that is the browser-qa
  lane's own artifact of a passing run, not a developer task; flagged in NOTES so this run
  prioritizes capturing them while it re-verifies those journeys anyway.

## DEFINITION OF DONE

- [ ] `vault.py` exists implementing universe registration (rule-hash committed before fetch),
      the split/seal dual assignment, and the one-way `sealed → assigned → exposed` hash-chained
      shard-lifecycle ledger keyed on `family_root_id`.
- [ ] TR-2 (sealed route sweep), TR-4 (cherry-pick refusal), TR-12 (single-shot sealed exposure),
      TR-20 (root-lineage refusal) are implemented and green on fixtures.
- [ ] `GET /research/desk/micro/vault` serves vault.py's state verbatim; opaque-only for sealed
      shards, full provenance from `assigned` onward.
- [ ] The exposure-registry sealed filter closes the known latent hole: a sealed dataset's window
      is provably absent from `TICK_LEGACY_CORPUS_ID`'s r2-seeded exposure entries.
- [ ] Spec §2.6's rule text + verification note are recorded beside every `quote_size_unit` stamp
      the recorder writes, excluded from `_content_checksum` (byte-identical checksum proven with
      and without the fields supplied).
- [ ] The two named test-hygiene items in `test_tick_recorder.py` are cleared.
- [ ] Target journeys J-06 (advanced, evidenced by the specific traps now green — status is the
      evaluator's call, not asserted here) and J-10 (trap count increases by exactly TR-2/4/12/20)
      verified via browser-qa-agent and the backend test suite together.
- [ ] Required-still-passing journeys J-01–J-05 remain green (deterministic replay + LLM
      fallback, mechanically verified).
- [ ] No anti-goal violation introduced: the vault secret never appears in a log/payload/
      screenshot; sealed metadata minimization holds; `family_root_id`, the split rule, and the
      hash-chain primitive are all reused, never reimplemented (coherence-auditor confirms).
- [ ] Full backend suite passes at a count ≥ iteration 8's 3,092 (0 failures); frozen foundations
      re-verified (`config_fingerprint()` → `08e471b10130e1e2`; six `referee_*.py` hashes
      unchanged; `EXPECTED_TOOLS` still the 22-tuple).
- [ ] The independent auditor (full-depth lane) runs against this diff; its findings are fixed
      within this iteration or explicitly carried forward by name in the dev handoff.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-9-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-06 (element capture of `/desk` confirming the Validation Vault section is still
  genuinely absent — proving OUT OF SCOPE held, not a UI pass); J-10 sentinel (cockpit `/`
  live-tape+chart, `/structure` load + Tradable Map, every shipped `/desk` section, screenshots
  on record). J-06's primary proof this iteration is the backend suite + fixture runs below, not
  an on-screen pass — there is no UI to check yet.
- Unit/integration: `apps/backend/tests/test_vault.py` (new — TR-2/4/12/20 + universe
  registration + seal assignment on fixtures); `test_walkforward.py` (extended — the sealed
  filter); `test_datasets.py` and `test_tick_recorder.py` (extended — the two new §2.6 fields
  and their checksum exclusion); full suite re-run for regressions.
- Error cases: an unregistered `universe_id` refuses (never validates silently); a cherry-picked
  batch refuses naming the delta; a second (family, shard) evaluation attempt refuses (TR-12); a
  sealed shard's route/accessor read surfaces only §7.5 metadata, never rows; a missing or
  unreadable `TAPEOLOGY_VAULT_SECRET_FILE` at seal-assignment time is a typed configuration
  refusal, never a crash and never a fabricated default secret.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above
maps to at least one concrete scenario line below.

- TC-1: given no universe is registered for a `universe_id`, when vault.py's batch verifier is
  asked to validate a recording batch against it, then it raises a typed refusal, never a silent
  pass.
- TC-2: given a universe registered with an explicit `symbol_rule`/`date_rule` and a `rule_hash`,
  when the vault ledger is read back, then the registration row's `registered_at` is present and
  the `rule_hash` recomputed from the identical inputs matches the stored one exactly.
- TC-3: given a recording batch whose (symbol, date) set is short one entry the universe rule
  computes, with no disclosed failure for it, when the cherry-pick verifier runs, then it refuses
  and names the specific missing entry (TR-4).
- TC-4: given a recording batch whose (symbol, date) set matches the universe rule's computed set
  exactly minus one DISCLOSED per-symbol failure, when the same verifier runs, then it returns OK.
- TC-5: given a `TAPEOLOGY_VAULT_SECRET_FILE`-sourced secret and a fixture (symbol, date), when
  the seal-assignment function computes the HMAC-based seal decision twice with the same secret,
  then both calls return the identical boolean, and the universe registration row and every log
  line contain zero occurrences of the raw secret string — only `sha256(vault_secret)`.
- TC-6: given a shard in `sealed` state, when `GET /research/desk/micro/vault` is called, then
  that shard's entry contains only `shard_id`, `universe_id`, a coarse size bucket, the checksum
  commitment, `sealed_at`, and `exposure_state: "sealed"` — no symbol key, no date key, no exact
  event count anywhere in the entry (TR-2/§7.5).
- TC-7: given that same shard transitions to `assigned` under a real `family_root_id`, when
  `GET /research/desk/micro/vault` is called again, then its entry includes symbol/date-range
  fields, and the shard-lifecycle ledger's `verify_chain()` returns `{"ok": true}`.
- TC-8: given shard S already carries an `assigned`/`exposed` row for `family_root_id` F, when a
  second assignment/exposure attempt for the identical (F, S) pair is requested, then it is
  refused (TR-12) and the ledger gains no new row for that pair.
- TC-9: given two registrations sharing the same (feature family, context kind, outcome family)
  triple but differing in name/parameterization, when each computes `family_root_id` via the
  reused `scout_ledger.compute_family_root_id`, then both produce the identical root; a third
  registration with a genuinely different triple produces a different root (TR-20) — proving a
  rename cannot evade TC-8's refusal.
- TC-10: given a fresh WALKFORWARD exposure registry and two tick fixture datasets D (currently
  `sealed` per vault.py) and E (not sealed), when `TICK_LEGACY_CORPUS_ID`'s r2 seed runs, then
  E's session-date window carries an exposure entry timestamped at the r2 instant while D's
  window carries none.
- TC-11: given D from TC-10 is later exposed through the vault's own lifecycle, when
  `TICK_LEGACY_CORPUS_ID`'s seed (still guarded by its existing once-only rule) is inspected
  again, then D's window is still absent from that seed's rows — D's exposure lives only in the
  vault's own ledger (per TC-7), never double-recorded into the legacy corpus's r2 seed.
- TC-12: given a freshly recorded fixture day, when `tick_recorder._finalize_day` calls
  `record_from_source` with the existing `schema_basis`/`quote_size_unit` stamps, then the
  persisted manifest also carries `quote_size_unit_rule_text` (the frozen §2.6 sentence,
  verbatim) and `quote_size_unit_verification_note` (naming the comparison and
  `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`) as sibling fields.
- TC-13: given the same fixture day recorded with and without the two new fields supplied, when
  `_content_checksum` is computed for both, then the two checksums are byte-identical.
- TC-14: given the two named test-hygiene items in `test_tick_recorder.py`, when the test file is
  inspected after this iteration, then the unused stand-in class is gone and the docstring
  reference names the correct file.
- TC-15: given the full backend test suite, when it runs after this iteration's changes, then it
  passes at a count ≥ 3,092 with 0 failures, `Config().config_fingerprint()` still prints
  `08e471b10130e1e2`, all six `referee_*.py` files hash identical to the iteration-0 listing, and
  `test_mcp_server.py`'s `EXPECTED_TOOLS` is still the unchanged 22-tuple.
- TC-16: given the operator's real `.data/datasets` store, when this iteration's dev/test work is
  exercised against a scoped throwaway copy, then a byte-for-byte hash of the real store taken
  before and after this iteration is identical.
- TC-17: given required-still-passing journeys J-01–J-05, when the browser-qa regression lane
  runs (deterministic replay, LLM fallback for any journey without a golden script), then all
  five remain green with cited evidence, and the J-10 sentinel's full kept-product walk is
  browser-verified with screenshots on record.
- TC-18: given this iteration's diff, when the independent auditor (full-depth lane) reviews it,
  then its findings are either fixed within this same iteration or explicitly carried forward by
  name in the dev handoff — never silently dropped.

## NOTES

- Scope-protection is deliberate: this spec is step 3 of J-06's five steps, alone. Step 4
  (credentialed tranche) and step 5 (readiness refresh) are the next iteration's material, per
  the operator's explicit ruling to split rather than raise the wall-clock budget. Do not let
  this iteration grow to absorb them.
- Vocabulary trap (T-2): this iteration has TWO things named "exposure" — the WALKFORWARD
  exposure registry (§6.7, `ExposureRegistry`/`micro_accessor.py`, existing, tracks whether a
  (corpus, session-window) has ever been served) and the vault's OWN shard exposure ledger (§7.4,
  NEW this iteration, tracks a shard's `sealed → assigned → exposed` lifecycle keyed on
  `family_root_id`). They interact (the sealed filter bridges them) but are not the same ledger,
  the same file, or the same identity key. Keep them named distinctly in code and in the dev
  handoff.
- Carried, unresolved, human-owned (not this iteration's job to resolve): (1) whether the
  `micro_observer.py` depletion timing stamp that is one quote early should be corrected; (2)
  whether J-01's readiness photograph must show the real 12-symbol-day corpus when the
  store-scoped browser rig can only ever seed fixture data (session lesson: "any iteration whose
  browser acceptance reads the tick corpus" hits this wall — applies here too if J-06's own
  browser evidence is read as needing real corpus numbers; it should not be, since step 3 ships
  no UI).
- When reading this iteration's browser evidence, read the LLM lane's own
  `...-ui-test-results.llm.md` verdict directly rather than trusting a merged headline (iter-6
  lesson: a bare `**FAIL**` markdown cell has previously parsed as no-verdict-at-all and produced
  a false-green merged headline).
- This iteration's diff touches `datasets.py` and `walkforward.py`, both read by J-01/J-02/J-03
  (datasets/snapshots) and J-05 (walkforward) directly — hence those four plus J-04 (shares the
  `HashChainedLedger`/`compute_family_root_id` primitives vault.py reuses) are the
  required-still-passing set, not an arbitrary smoke sample.
- Two assumption-ledger entries were logged for this iteration's scoping calls (route-without-CLI
  for vault.py; the sealed-filter fix's design) — see
  `runs/goal-session-rapid-microscope/state/assumptions.md`.
