# Goal Iteration 23 — Close J-06: independently verify the real recorder+vault tranche the owner just ran

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 23
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: the real J-06 recording landed via commits
  `08534e8`/`76e7a70` OUTSIDE the goal-mode pipeline (an interactive session; never touched by
  developer/reviewer/QA/audit), adding four hash-chained ledgers, a typed TR-4 verifier, and a new
  `j06_operator.py` sequencer whose only witness so far is its own self-authored
  `reports/j06-tranche/acceptance.json`. It also crosses into `micro_readiness.py`'s
  `sealed_tranche` aggregate (J-01), the `/desk` Readiness+Vault UI (J-08), and the MCP 26-tool
  proxy contract — no single journey's existing tests cover that interaction, and this is the
  FIRST time any of it renders a non-empty registered universe.
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07, J-08, J-09, J-10 (full
  regression widening — see BACKGROUND)
- **Anti-goal reminders:**
  - **No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed`
    shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded
    exposure; the refusal is typed, tested, and fail-closed. *(critical)*
  - **Sealed exposure is family-level and single-shot — never a second draw.** No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and
    travels in every later export bundle; no perturbed re-submission resets it. *(critical)*
  - **A recorded tranche is one opaque research pool until its shards are exposed.** No served
    surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
    graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory"
    versus "sealed", nor a complete per-shard list of EITHER side while any pool member is
    unexposed; the registered universe is public by construction, so a complete list of one side
    identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable;
    identity becomes public only at real exposure or assignment. The governing test is the TR-2
    inference trap: given the registered universe plus every public artifact, no still-unexposed
    vault-eligible shard is identifiable with certainty. *(critical — spec r5)*
  - **The vault secret never enters the repo, a log, a payload, or a screenshot** — only its
    sha256 commitment is ever recorded. *(critical)*
  - **The accessor is the only data door.** No module but `micro_accessor.py` opens snapshot or
    vault event data; origin fences fail closed; import-ban and source-scan guards enforce it.
    *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **The 12 pre-existing tick symbol-days are permanently exploratory** — never sealed, never
    `historical_oos`, never relabeled. *(critical)*
  - **Referee modules are byte-untouched this era** — `referee_handoff_ready` never implies
    current-Referee registrability of a flow predicate. *(critical)*
  - **No fingerprint epoch movement.** Zero new Config fields expected; the pin
    `08e471b10130e1e2` does not move. *(critical)*

## GOAL

Independently verify — through the full goal-mode pipeline, not on the operator's own say-so —
that the real 80-pair Alpaca J-06 tranche the owner recorded and repaired (commits `08534e8`,
`76e7a70`) meets every J-06 acceptance clause against the live store, and capture the first-ever
browser evidence of the Microscope Readiness and Validation Vault sections rendering a genuinely
non-empty registered universe, so J-06 — the era's last non-passing journey — can be scored on
proof rather than on the operator's own report.

## BACKGROUND

Iteration 22 ended `STALLED`: J-06's only remaining step was the real tape recording, an act the
goal itself calls operator-only (paid feed, owner attendance, one-way seal). Between iter-22 and
this dispatch the owner did exactly that, OUTSIDE goal-mode, in an interactive session: commit
`08534e8` built the canonical operator bridge (`j06_operator.py`) and recorded 79/80 pairs;
`76e7a70` found and fixed two structural defects the first pass missed (TR-4 was laundering its
own failure provenance by deriving "disclosed" purely from "missing"; a legacy dataset could
silently swallow a registered pair) and completed 80/80. `reports/j06-tranche/acceptance.json`
self-reports every J-06 acceptance number: 8 symbols × 10 dates = 80 pairs, PG present, 3
Tier-B symbols resolved (AG/LYFT/WULF), 1 ETF (SPY), 100% full-session, concentration caps held
(≤0.125), 21/21 HMAC-selected sealed with zero unsealed, all four ledger chains verify, one
disclosed non-selected pool position refused (not glossed) by a new TR-33 typed check, and the
research-readiness gate still honestly reads unmet (80 < 150) — exactly as the acceptance clause
requires. I confirmed by hand: imports are clean, `Config().config_fingerprint()` still prints
`08e471b10130e1e2`, `docs/goal.md` is untouched since iter-17 (no goal-text drift), and
`micro_readiness.py`'s `sealed_tranche` aggregate machinery (built iter-9, widened iter-11 on
fixtures with zero registered universes) is the SAME code path that will now, for the first time,
serve a real non-empty pool — the frontend's `sealed_tranche.by_universe` map (already generic,
`apps/frontend/app/desk/page.tsx:6048`) has literally never rendered a non-empty branch before.

This is exactly the shape this era's independent-checker discipline exists for: ten prior findings
this era (iter-15 through iter-22 lessons) all share the pattern "a claim passed review and QA on
the strength of a report nobody but its own author checked." Nothing in `08534e8`/`76e7a70` has
been reviewed, tested-by-a-different-lane, or browser-verified by the chain — it was built and
self-certified in one sitting. Per rule 6 (don't perpetuate a stale human-blocked label) and the
iter-20 lesson on the same point, J-06 is no longer human-blocked: the human act is DONE and
committed; what's missing is the chain's own independent proof, which is exactly machine work.

Per priority rubric rule 1/3: J-06 is the sole remaining non-passing journey and unblocks nothing
else, but per rule 6 it is no longer human-blocked, so it is squarely this iteration's target — no
other journey is failing or partial. Depth: the evaluator's recommendation for this iteration is
`full` (BINDING) and independently justified (trigger 1, above) by the never-reviewed, cross-cutting
shape of the new code. Given the size of the underlying change (4 new ledgers, a widened trap, a new
trap, a repaired sequencer) and the fact this is likely the closing move of the era, I widen
Required-still-passing to ALL 9 currently-passing journeys rather than a smaller rotating set —
`sealed_tranche`/vault data now genuinely populated for the first time is exactly the kind of
blast-radius change the "widen regression periodically" guidance calls for.

**Lessons applied:** (iter-18, rig rule) the QA fixture rig (`start_scoped_qa_backend.sh` /
`qa_playbook_iter7_fixture_scoped_backend.sh`) points `TAPEOLOGY_DATASET_DIR` at a FIXTURE
directory, not the real `.data/datasets` store the tranche was recorded into — it cannot show this
evidence, and must NOT be repurposed to try; see NOTES for the resolution (logged to
`assumptions.md`). (iter-21/22, non-self-verification) do not accept `acceptance.json`,
`tr2-disclosure-analysis.json`, or `pool-position-disclosure.json` as proof by themselves — the
audit lane must independently re-derive at least the TR-2 "no identity is certain" claim and the
TR-4 batch-verification claim against the live store, the same way this era's auditor has caught
something after review+QA passed the same code nine times previously. (iter-22, vacuous test)
`test_scout.py:1676` still cannot fail — carried as a trivial, zero-risk passenger fix this round
per two consecutive evaluators' explicit request, never a round of its own. (iter-21 second/third,
rig sequencing) this iteration's browser evidence gathering must not touch the shared QA fixture
rig's ledger state at all (it uses a separate real-store-pointed instance), so the "run replay
before any rig-mutating lane" rule is moot here, but is restated for whichever future iteration
next touches the fixture rig.

## IN SCOPE

### Backend

- [ ] Independently review `apps/backend/app/research/vault.py`'s additions (
  `VaultScreenProvenanceLedger`, `VaultDisclosureIncidentLedger`, the typed J-06 TR-4 verifier,
  `record_screen_provenance`/`record_disclosure_incident`/`disclosed_pool_positions`), the r11
  `micro_tier_b_screen.py` changes, and `apps/backend/scripts/j06_operator.py` against
  `docs/rapid-validation-spec.md` r12 + new §7.2.2 — confirm the accessor-only-door rule,
  store-immutability discipline, and the closed-vocabulary/typed-refusal pattern are honored.
- [ ] Run the full backend suite; confirm pass count ≥ 3,322 (iter-22 baseline), 0 fail, 0 error,
  and that TR-2 (composed disclosure), TR-4 (widened), TR-12, TR-19, TR-20, and the new TR-33 are
  each individually green.
- [ ] Confirm `Config().config_fingerprint()` == `08e471b10130e1e2` and every `referee_*` module's
  SHA-256 still matches the era-open listing (byte-identical; no diff in this iteration's own
  changed-files list either).
- [ ] Stand up a backend instance pointed at the REAL `apps/backend/.data/datasets` store
  (`TAPEOLOGY_DATASET_DIR="$ROOT/.data/datasets"`, the `goal-desk-iter9-scoped-backend.sh`
  precedent; read-only GETs only) and confirm `GET /research/desk/micro/readiness` serves
  `sealed_tranche.by_universe["rapid-microscope-j06-starter"]` with the real aggregate counts
  (21 sealed, 80 shard pool, `quote_size_unit`/preservation-field presence), and that
  `joinable_corpus.withheld_excluded` reflects the withheld pool WITHOUT listing any individual
  pair.
- [ ] Against the same real-store instance, confirm `GET /research/desk/micro/vault` serves the
  registered universe (rule hash / commitment, never the raw symbol/date rule contents where
  unexposed) and the 21 sealed shard rows by surrogate id only — no `symbol` or `session_date`
  field for any still-sealed shard, on the route OR the `desk_vault` MCP proxy.
- [ ] Confirm the MCP 26-tool contract is unchanged (`EXPECTED_TOOLS` untouched) and that
  `desk_micro_readiness`/`desk_vault` return byte-identical JSON to their REST routes against the
  real-store instance.
- [ ] Independently re-run (not re-read) at least the TR-2 inference-certainty check and the TR-4
  batch-verification check against the live store, rather than trusting
  `reports/j06-tranche/tr2-disclosure-analysis.json` / `acceptance.json`'s own numbers at face
  value — reproduce `any_identity_certain: false` and `tr4_batch_verification.ok: true`
  independently.
- [ ] Passenger, trivial (≤1 line, zero product risk): add the missing non-vacuity assertion
  `screen_result["n_candidate"] + screen_result["n_comparator"] > 0` to
  `test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor`
  (`apps/backend/tests/test_scout.py:1676`), mirroring its Study-1 twin at `:1664` — carried two
  rounds per the iter-21/iter-22 evaluators' explicit ask.

### Frontend

- [ ] No code changes expected — `apps/frontend/app/desk/page.tsx`'s Microscope Readiness and
  Validation Vault sections already render `sealed_tranche`/vault data generically. If the real,
  non-empty `by_universe` map surfaces a genuine rendering bug (not previously exercisable against
  an all-zero fixture), fix it as the smallest possible change and record the fix in the dev
  handoff.

### New user-facing capability

None beyond what's already shipped — the owner (or an MCP-connected Claude session) can now, for
the first time, actually SEE a real registered recording universe and its sealed-shard aggregate
on `/desk`, instead of the all-zero empty state every prior browser pass has shown.

### New information displayed

The same already-registered `sealed_tranche` aggregate fields, now genuinely populated: shard
count, symbol-days, per-universe totals, `quote_size_unit` distribution, preservation-field
presence — no new field.

### New user actions

None — this era's rule holds (page-load GETs never compute; no new button, no new POST).

### UI surface changes

None structural — same sections (Microscope Readiness, Validation Vault) under the same `/desk`
Rapid Microscope block, now exercising their real-data code path for the first time.

### Product surface delta

Cosmetic-only, in substance: the empty-state placeholder ("no universes registered") on
Readiness/Vault is replaced by the real aggregate for anyone who loads `/desk` against the
production store. Nav, routes, and page count are unchanged.

### Blueprint conformance

Validation Vault (J-06) and Microscope Readiness (J-01) are already registered under
`Desk → Rapid Microscope` in `blueprint.md`'s Information Architecture (iter-14/iter-9). No new
page, no nav-skeleton change — no blueprint edit this iteration.

### Data-contract additions

None. This iteration populates already-registered Data Contract rows (`sealed_tranche` sub-fields
owned by `micro_readiness.py`; vault shard/universe rows owned by `vault.py`, both served from
their already-registered endpoints) with real data for the first time. No new field, module, or
endpoint is introduced; nothing here creates a second computation or serving path for any existing
value.

## OUT OF SCOPE

- Running the J-09 pilot studies against the real corpus (still forbidden — irreversible
  permanent rows, breaks J-10's "No candidates ledgered." golden, quadratic search uncancellable).
  Do NOT re-screen J-09; it stays `passing` from iter-22.
- The 22.3-second Desk-readiness latency fix (iter-22's item 4) — explicitly the lowest-priority
  carried item and not required for J-06 closure; deferred again.
- The duplicated selector→kind table dedupe (`micro_routes.py` vs `scout.py`) — cosmetic, deferred.
- Exposing (assigning/revealing) any sealed shard — J-06's acceptance only requires `sealed`
  state, not `exposed`; do not call `assign_shard`/`expose_shard` on any real shard this
  iteration.
- Recording any further tranche beyond the 80/80 already on disk — the research-readiness gate
  (~150 symbol-days) is honestly, correctly, still unmet; that is a passing state per the goal
  text, not a gap to close now.
- The sealed judge's economic-floor ruling (`micro_sealed_evaluation.py:316`) — remains an open
  owner ruling that blocks no journey; untouched this iteration.
- Any engine, detector, or `referee_*` change.
- Widening the recorder panel, changing the Card-5.2 universe rule, or any new vendor/data
  purchase.

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent: Microscope Readiness and Validation Vault sections on
  `/desk`, captured against the real-store-pointed backend instance, show the registered universe
  `rapid-microscope-j06-starter` with its 21-sealed-shard aggregate, no per-shard symbol/date
  visible anywhere in the DOM or screenshot.
- [ ] TR-2, TR-4, TR-12, TR-19, TR-20, TR-33 all green; full suite pass count ≥ 3,322, 0 fail, 0
  error.
- [ ] `Config().config_fingerprint()` == `08e471b10130e1e2`; every `referee_*` module
  SHA-256-identical to the era-open listing.
- [ ] MCP 26-tool contract unchanged; `desk_micro_readiness`/`desk_vault` byte-identical to their
  REST routes against the real store.
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-07, J-08, J-09, J-10) remain
  green (deterministic replay + LLM fallback).
- [ ] No anti-goal violation introduced: vault secret never appears in any log/payload/screenshot;
  TR-2 opaque-pool rule holds against the real 80-shard pool; sealed shards refuse exploratory
  reads.
- [ ] Study-3 non-vacuity assertion added and passing (`test_scout.py:1676`).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-23-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-06 (via the Microscope Readiness + Validation Vault sections on `/desk`), captured
  against a backend instance pointed at the real `.data/datasets` store per the resolution logged
  in `assumptions.md` (iter-23). Regression smoke of J-01, J-08, J-09, J-10 runs on the standard
  fixture-scoped QA rig as usual — the two rigs are never mixed in one capture.
- Unit/integration: full backend suite; TR-2/TR-4/TR-12/TR-19/TR-20/TR-33; fingerprint pin test;
  referee byte-freeze test; `test_mcp_server.py` `EXPECTED_TOOLS`; accessor import-ban guard;
  `test_scout.py:1676` non-vacuity fix.
- Error cases: reading a still-sealed shard's symbol/date via any route, MCP tool, or the
  accessor directly must raise the typed `SealedShardWithheldError` (or equivalent refusal),
  never an empty/degraded 200; attempting to open vault event data outside `micro_accessor.py`
  must fail the import-ban guard.

Test-first contract:

- TC-1: given the real universe `rapid-microscope-j06-starter` (80 recorded shards, 21 HMAC-selected,
  all sealed) and a backend instance pointed at the real `.data/datasets` store, when `/desk` is
  loaded with the Microscope Readiness section expanded, then `sealed_tranche.by_universe` shows
  exactly one row for `rapid-microscope-j06-starter` with `shard_count == 21`, and no per-shard
  symbol or date string appears anywhere on the rendered page.
- TC-2: given the same real-store-backed instance, when the Validation Vault section is expanded on
  `/desk`, then it renders the registered universe (rule hash/commitment) and reports 21 sealed
  shard rows keyed by surrogate id — the rendered DOM and its underlying JSON contain no `symbol`
  or `session_date` field for any still-sealed shard.
- TC-3: given the real store, when `GET /research/desk/micro/readiness` is called directly, then
  the response's `sealed_tranche.by_universe["rapid-microscope-j06-starter"].shard_count == 21`
  and `joinable_corpus.withheld_excluded` is a positive integer that never itemizes the withheld
  pairs.
- TC-4: given the MCP server pointed at the same real-store instance, when `desk_vault` and
  `desk_micro_readiness` are invoked, then their JSON payloads are byte-identical to the
  corresponding `GET` route responses, and `EXPECTED_TOOLS` still lists exactly 26 tools.
- TC-5: given the full backend suite, when run to completion, then it reports pass count >= 3,322,
  0 failures, 0 errors, and TR-2/TR-4/TR-12/TR-19/TR-20/TR-33 each show as individually passed in
  the run output.
- TC-6: given `Config().config_fingerprint()`, when computed against the working tree, then it
  prints exactly `08e471b10130e1e2`, and every `referee_*` module's SHA-256 matches the era-open
  listing with zero diffs.
- TC-7: given the live store's registered universe plus every public artifact (readiness, vault,
  dataset list, MCP), when the TR-2 inference-certainty check is re-run independently (not read
  from `tr2-disclosure-analysis.json`), then it reports `any_identity_certain: false` reproducibly.
- TC-8: given `test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor`
  (`test_scout.py:1676`) with `_plant_capitulation_signal`'s `trigger_ts` moved 5e9 seconds outside
  the dataset window, when the test is re-run AFTER adding
  `screen_result["n_candidate"] + screen_result["n_comparator"] > 0`, then the test FAILS; with the
  signal restored in-window, the test PASSES.
- TC-9: given the vault secret file (`TAPEOLOGY_VAULT_SECRET_FILE`), when every screenshot, log,
  and served payload captured this iteration is inspected, then none contain the raw secret bytes
  — only its sha256 commitment (`68f2bbb3...`) ever appears.
- TC-10: given the Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-07, J-08, J-09,
  J-10), when their stored golden replay scripts are run against the standard fixture-scoped QA
  rig (falling back to the LLM browser-qa lane for any journey without a golden on file), then
  every one reports its prior passing verdict with no regression.

## NOTES

- This iteration's ONLY new-code deliverable is the trivial Study-3 test fix; the rest is
  independent verification of already-committed, already-self-certified work. That is a
  deliberate, legitimate full-depth shape for this era (see iter-21/iter-22 for precedent) —
  not an evidence-only iteration under rule 7, because it requires the audit lane to independently
  RE-DERIVE claims (TR-2, TR-4) rather than merely re-photograph them.
- If the independent review in IN SCOPE's first bullet finds a genuine defect in the owner's
  interactive-session work (mirroring this era's established pattern of the auditor catching
  something nine times running), fix it as the smallest possible correction, document it plainly
  in the dev handoff, and do NOT treat finding-and-fixing a real bug as scope creep — it is
  exactly this iteration's purpose.
- If J-06 passes cleanly, all ten Must-have journeys are passing and the next evaluator should
  weigh GOAL_ACHIEVED against the two still-open owner rulings named in `iteration-state.md`
  (sealed judge's money-floor source) — neither blocks any journey's acceptance text, per the
  iter-20 lesson on not perpetuating a stale blocker label without re-testing it.
- Host-guard caps remain law for the full suite run and any backend instance stood up this
  iteration (CPU mask `4-7,12-15`, per `project-extensions/host-guard/host-guard.env`).
