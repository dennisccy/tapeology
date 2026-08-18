# Goal Iteration 10 — Graduation: provenance in, nothing laundered out (J-07)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 10
- **Mode:** next
- **Depth:** lean
- Frontend Present: yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-10
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Sealed exposure is family-level and single-shot — never a second draw.** No more than one evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels in every later export bundle; no perturbed re-submission resets it. *(critical)*
  - **Evidence classes never mix.** No `historical_exposed_diagnostic` output feeds a gate, a graduation transition, a certificate, a promotion, or a pooled statistic with `historical_oos` rows; nothing in this era emits `live_confirmatory`. *(critical)*
  - **The denominator never shrinks.** Every evaluated variant lands in the hash-chained ledger with a closed-vocabulary decision; kills are never deleted; the union-N across grid versions is served beside every family. *(critical)*
  - **Referee modules are byte-untouched this era** — `referee_handoff_ready` never implies current-Referee registrability of a flow predicate; that awaits a future named revision of the referee spec. *(critical)*
  - **No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed` shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure; the refusal is typed, tested, and fail-closed. *(critical)*

## GOAL

Implement Graduation (`micro_graduation.py`, spec §8) so a fixture candidate's complete evidence
trail — every kill, every fold, every shard, every failure — can walk
`exploratory → walkforward_survivor → sealed_survivor → referee_handoff_ready` with nothing
laundered out, closing J-07 while J-06 step 4 waits on the owner.

## BACKGROUND

J-06 step 4 (the credentialed tranche) is hard-gated on two unresolved owner rulings (audit B2:
sealed membership recoverable via cartesian-closure of `GET /research/datasets`; audit B3: the
recorder-compute route leaking per-chunk symbol/date/raw id) — per the iter-9 evaluator's binding
recommendation and `iteration-state.md`'s "Do not redo" block, this iteration targets **J-07**
instead: fixture-only, needs no ruling, and next in dependency order (rubric rule 6: do not plan
human-blocked work). **Depth is LEAN, not the evaluator's recommended full: no full trigger
holds.** None of the four escape conditions is met — iter-9's verdict was CONTINUE, not
ESCALATE/REGRESSION; iter-9's `coherence.md` verdict was COHERENCE-PASS, not FAIL; the
hardening-cadence counter is 0/6, not due; and J-07 is backend/fixture-only with zero new frontend
surface, not a brand-new full-stack journey. A declared full would only be demoted by the
deterministic arbiter — as already happened twice this era (iters 3 and 8) — dropping the auditor
lane for real cost and no benefit, which is exactly the budget pattern the operator flagged as
tight. Two lessons apply directly and are binding on the build regardless of depth: the graduation
ledger MUST reuse `micro_chain_ledger.HashChainedLedger` (never a hand-rolled chain-only ledger —
iter-4's tail-truncation-blindness lesson) and its state-transition writes MUST be identity-keyed
and replay-safe, disclosing `appended` vs `replayed` (iter-5's lesson, which names "J-07's
graduation bundle" by name). Folding in the cheap iter-9 coherence WARN at zero developer cost:
`blueprint.md`'s Data Contract now carries rows for the three already-shipped disclosure
sub-fields (`withheld_excluded`, `sealed_withheld`, `sealed_tranche`), edited directly this turn.

## IN SCOPE

### Backend
- [ ] New `apps/backend/app/research/micro_graduation.py` implementing the four graduation states
      (`exploratory` → `walkforward_survivor` → `sealed_survivor` → `referee_handoff_ready`) per
      spec §8, backed by a NEW graduation ledger built on the shared
      `micro_chain_ledger.HashChainedLedger` primitive — reuse, never a hand-rolled chain; the
      ledger carries the same tail-anchor discipline as `scout_ledger.py`'s `_read_head_anchor`.
- [ ] Class-2-only advancement: `walkforward_survivor` reads fold rows via `walkforward.py`'s
      existing `fold_results_for_sequence`/`sequence_ids_for_corpus` (only `historical_oos` +
      `rule_process` folds satisfying `WF_SURVIVOR_RULE_V1` count); `sealed_survivor` reads the
      single-shot sealed-shard verdict via `vault.py`'s existing shard-state functions. No new
      query function is added to `scout_ledger.py`, `walkforward.py`, or `vault.py` — read-only
      via what they already expose (single source of truth; no second ledger-reading path).
- [ ] Idempotent, identity-keyed transition recording (`family_root_id` + target state): a
      repeated advancement check for an already-recorded transition is answered `replayed`, never
      appended as a second row (iter-5 lesson, named for this exact journey).
- [ ] Voiding semantics: consult (never reimplement) `walkforward.py`'s existing
      `voiding_events_for_corpus`/`is_corpus_era_voided` — no second voiding mechanism.
- [ ] The `referee_handoff_ready` export bundle: frozen spec hash; `family_root_id` lineage; every
      ledgered trial for the family including kills (union-N via
      `scout_ledger.distinct_variant_count`); every fold with its `evidence_class` and
      `process_label`; every shard touched; the proposed confirmation boundary;
      family/multiplicity metadata (sibling candidates, prior sealed verdicts of the root family);
      plus the bundle's own copy stating verbatim that current-Referee registration of a flow
      predicate awaits a future named referee-spec revision.
- [ ] Read-only `GET /research/desk/micro/graduation` on the existing `micro_routes.py` router
      (`/research/desk/micro` prefix — that file's own docstring already reserves this exact route
      for "a later iteration"). Serves the recorded graduation state per family; never 404/500 on
      an empty ledger — an honest empty state ("No candidates ledgered.") when the real ledger has
      no rows (no operator has run graduation yet).
- [ ] Fixture proof end to end (spec §8's acceptance): a fixture candidate with synthetic class-2
      evidence walks all four states; a diagnostic-only twin is refused at the first transition; a
      failed-sealed twin's permanent failed verdict is carried into its own bundle.
- [ ] Record the Era-15 evidence line in `docs/research-directions.md`'s Era-15 section (goal.md
      J-07 step 3) — a documentation-only amendment on what L1 liquidity-family survivor evidence
      would raise/lower the Depth-purchase prior; no code change.
- [ ] Extend the existing micro guard-test pattern (accessor import-ban, the `micro_*`/`scout*`/
      `walkforward*` threshold-sweep ban, `test_copy_discipline.py`) to `micro_graduation.py`.

### Frontend
(none this iteration — J-07 is keyless/automated per goal.md; its states get an operator-visible
home when J-08 renders the Scout Ledger / Walk-Forward / Vault sections. `Frontend Present: yes`
above is set solely to keep the required-still-passing browser regression sweep running, per the
standing iter-4/iter-5 lesson about `Frontend Present: no` silently skipping that sweep.)

### New user-facing capability
None this iteration.

### New information displayed
None — no UI change. The new `GET /research/desk/micro/graduation` route is a backend-only read
surface with no page consuming it yet.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible to the operator. The product's backend surface grows by one module and one read-only
route, both inert until J-08 wires them into `/desk`.

### Blueprint conformance
No new page. `micro_graduation.py` and `GET /research/desk/micro/graduation` fill the
ALREADY-RESERVED owner in `blueprint.md`'s Data Contract ("Graduation states + export bundles")
and Information Architecture ("Graduation states (J-07) | keyless/automated; states surface via
the Scout Ledger / Walk-Forward / Vault rows they attach to | Desk") — no IA edit needed for this
row. This iteration's only blueprint edit is additive housekeeping: registering the three
already-shipped disclosure sub-fields flagged WARN by iter-9's coherence audit, under their
existing owners (done this turn — see Data-contract additions below and `blueprint.md`).

### Data-contract additions
None NEW — the graduation endpoint row already exists in `blueprint.md` (registered at era
baseline); this iteration builds its reserved owner verbatim. Housekeeping only (decomposer-applied
this turn, zero developer cost): `blueprint.md`'s Data Contract gains three rows for already-shipped
sub-fields flagged WARN by iter-9's coherence audit —
`withheld_excluded: int >= 0` (count only, never ids; owner = each already-registered parent
module — `scout.py`/`walkforward.py`/`micro_join.py`/`edge_report.py`/`edge_report_cache.py`/
`pnl_scan.py`/`desk_screen.py`/`micro_snapshots.py` — via the single shared predicate
`vault.withheld_dataset_ids()` → `micro_snapshots.exclude_withheld()`);
`sealed_withheld: int >= 0` (owner `datasets.py`, served by `GET /research/datasets`);
`sealed_tranche: object` (aggregate block — shard count, total symbol-days, per-universe totals,
never a per-shard row; owner `micro_readiness.py`, served by `GET /research/desk/micro/readiness`).

## OUT OF SCOPE

- **J-06 step 4** (the credentialed tranche: universe registration, real Alpaca recording, real
  sealing) — HARD-GATED on unresolved owner rulings for audit B2 (sealed-membership
  cartesian-closure leak) and B3 (recorder-compute per-chunk leak). No real tape is recorded or
  sealed this iteration.
- The recorder-progress-page fix (hides a withheld recording's name/date) — gated on the same
  pending owner decision; deferred alongside J-06 step 4.
- **TR-3** (accessor fence), **TR-17** (future-event availability), **TR-22** (exposure registry)
  — the three still-missing traps live in already-stable `micro_accessor.py` /
  `micro_observer.py` / `walkforward.py` (J-02/J-03/J-05 territory), not `micro_graduation.py`;
  bundling them here would touch modules outside J-07's surface for no shared benefit. Deferred to
  a dedicated J-10 hardening iteration.
- Audit **B4** (withholding predicates fail open on ledger corruption) and **B5**
  (`referee_evidence.py` counting withheld shards, a frozen-hash collision) — both owner-owed per
  `iteration-state.md`'s active blockers, inert today (zero sealed shards exist anywhere).
- The one-quote-early depletion timing stamp (`micro_observer.py`) — owner-owed since iteration 2.
- **J-08** (surface + MCP v6 bump, `/desk` UI sections) and **J-09** (pilot studies) — natural next
  journeys after J-07, not this iteration.
- Any change to `referee_*` modules, the `v1` strategy, or the `default` profile — byte-identical,
  forbidden.
- Any change to `scout_ledger.py`'s, `walkforward.py`'s, or `vault.py`'s own persisted row shapes
  or public function signatures — J-07 reads them via their existing read-only functions only.
- A `desk_micro_graduation` MCP tool — not part of this era's v6 four-tool delta
  (readiness/scout/walkforward/vault only). MCP surface stays at 22 tools this iteration.
- Any new `/desk` UI section or nav change for graduation.

## DEFINITION OF DONE

- [ ] J-07's fixture pipeline (all four states, the diagnostic-only refusal, the failed-sealed
      permanent verdict) is proven by `test_micro_graduation.py` and verified directly by the
      developer and reviewer — no browser surface for J-07 itself this iteration.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06, J-10 remain green via
      deterministic replay (goldens on file for all seven).
- [ ] No anti-goal violation introduced: the denominator never shrinks; sealed exposure stays
      single-shot; all six `referee_*.py` modules stay byte-identical; the MCP surface stays at 22
      tools; nothing emits `live_confirmatory`.
- [ ] Full backend suite passes at a count ≥ 3,158 pass / 8 skip (iter-9's count) and ≥ the
      era-open baseline (2,691 pass / 8 skip), 0 regressions; `Config().config_fingerprint()`
      prints `08e471b10130e1e2` unchanged.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-10-dev.md`.

## TESTING REQUIREMENTS

- Browser: no NEW browser surface for J-07 itself (keyless/automated, no UI this iteration).
  Required-still-passing regression sweep: J-01, J-02, J-03, J-04, J-05, J-06, J-10 — each via its
  stored golden replay script (`runs/goal-session-rapid-microscope/journey-scripts/J-01.json`
  through `J-06.json`, `J-10.json`), LLM fallback only on a replay miss.
- Unit/integration: `test_micro_graduation.py` covering all four states end to end on synthetic
  fixtures, the diagnostic-only refusal, the failed-sealed permanent-verdict carry-through, ledger
  replay-idempotency (`appended` vs `replayed`), tail-anchor truncation detection, and the
  `GET /research/desk/micro/graduation` route's honest-empty-state response against the real
  (currently empty) ledger. Full backend suite re-run after every edit.
- Error cases: a diagnostic-only candidate submitted for `walkforward_survivor` advancement is
  refused with a typed error, never silently advanced; a second identical advancement attempt for
  an already-recorded transition is a replay, never a duplicate append; a request against a
  `family_root_id` with no ledgered scout/walkforward/vault history serves an honest refusal,
  never a fabricated bundle.

Test-first contract — TC- scenarios:

- TC-1: given a fixture candidate whose ledgered walk-forward folds are all `historical_oos` +
  `rule_process` and jointly satisfy every `WF_SURVIVOR_RULE_V1` clause (sufficient folds, the
  sign-agreement floor, the economic floor in the registered direction, no opposite-direction
  pass) with no voiding event on its corpus-era, when graduation evaluates it, then its state
  advances to `walkforward_survivor` with a new append-only ledger row recording the rule name and
  the satisfied clauses.
- TC-2: given that same candidate additionally has a single-shot sealed-shard evaluation (fixture)
  that passes under a spec frozen before assignment, when graduation evaluates it, then its state
  advances to `sealed_survivor`.
- TC-3: given a `sealed_survivor` candidate, when graduation builds its export bundle, then the
  bundle contains the frozen spec hash, the `family_root_id` lineage, every ledgered trial for
  that family including kills (union-N via `scout_ledger.distinct_variant_count`), every fold with
  its `evidence_class` and `process_label`, every shard touched, the proposed confirmation
  boundary, and family/multiplicity metadata, and the candidate's state becomes
  `referee_handoff_ready`.
- TC-4: given that `referee_handoff_ready` bundle, when its copy field is read, then it contains
  the sentence that current-Referee registration of a flow predicate awaits a future named
  referee-spec revision.
- TC-5: given a diagnostic-only twin fixture candidate whose only ledgered folds are
  `historical_exposed_diagnostic`, when graduation evaluates it, then it is refused at the first
  transition (state stays `exploratory`) with a typed refusal.
- TC-6: given a failed-sealed twin fixture candidate whose sealed-shard evaluation returns a
  failing verdict, when graduation evaluates it, then its permanent failed verdict is recorded and
  appears in that family's export bundle output.
- TC-7: given a candidate already recorded as `walkforward_survivor` for a specific
  `family_root_id`, when the same advancement check is run a second time with no new ledgered
  evidence, then the ledger records the second call as `replayed` (not a duplicate `appended`
  row) and the ledger's row count for that family/state is unchanged.
- TC-8: given the graduation ledger's persisted tail anchor (row_count/head_hash) plus N committed
  rows, when the underlying ledger file is truncated to remove its newest row, then the
  chain-verification call returns a mismatch against the persisted anchor instead of returning ok
  on the shortened chain.
- TC-9: given the real, currently-empty graduation ledger on disk (no operator has ever run
  graduation), when `GET /research/desk/micro/graduation` is called, then it returns HTTP 200 with
  an explicit empty-state body ("No candidates ledgered.") — never a 500 and never a fabricated
  row.
- TC-10: given the full backend suite and the six `referee_*.py` SHA-256 hashes recorded at
  iteration 0, when they are re-run/re-hashed after this iteration's diff, then all six hashes are
  byte-identical to the iteration-0 listing and the suite count is ≥ 3,158 pass / 8 skip with 0
  failures.
- TC-11: given the stored golden replay scripts for J-01 through J-06 and J-10, when the
  browser-qa lane runs this iteration, then each replays deterministically green (or the LLM
  fallback reports its own result honestly on a replay miss), and
  `Config().config_fingerprint()` prints `08e471b10130e1e2`.

## NOTES

- **Depth deviation is intentional, not an oversight.** The evaluator recommended full; this spec
  plans lean because no escape condition independently holds (see BACKGROUND). Per iter-3/iter-8
  lessons, only the evaluator's own verdict (ESCALATE) or a met hardening cadence grants full
  unconditionally — a decomposer's `Full trigger:` line cannot manufacture it, and writing one here
  would just be demoted at real cost.
- **Process note (standing, from the operator):** never use pattern-based process kills
  (`pkill -f` / `killall`) for uvicorn, next, node, chrome, or python — other projects share this
  host. Kill only exact PIDs you started and recorded.
- The vault secret (`TAPEOLOGY_VAULT_SECRET_FILE` at `~/.config/tapeology/vault-secret`) is not
  touched this iteration (no sealing act occurs), but the standing rule stands regardless: never
  read, log, print, or serve it — only its sha256 commitment may ever be recorded.
- Spec revisions r3 and r4 (`docs/rapid-validation-spec.md` §7.5) are SETTLED owner rulings — do
  not re-litigate; build against the current spec text as read this iteration.
- Escalation flag: none required. If the developer finds graduation genuinely needs a new
  read-only function on `scout_ledger.py`/`walkforward.py`/`vault.py` beyond what already exists,
  that stays in-scope (additive, read-only, no schema change) — but flag it for extra reviewer
  scrutiny given this era's pattern (iter-4/iter-5 lessons): every prior ledger-writer path the
  auditor has examined has hidden an identity or idempotency bug on first inspection.
