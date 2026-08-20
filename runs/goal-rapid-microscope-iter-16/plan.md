# goal-rapid-microscope-iter-16 Execution Plan

## What to Build

Land three leakage traps as explicitly-labeled, non-vacuity-proven trap-suite entries, plus three
small carried passengers. J-10 moves 24/29 → 27/29 traps and is EXPECTED to stay `partial` (TR-23/
TR-24 are round 17's) — that is the correct outcome, not a shortfall.

- **TR-3** (accessor origin-fence): explicitly-labeled entry covering (a) single-read fence
  [fold in existing `test_tc1_*`], (b) NEW multi-session aggregate-boundary proof, (c) import-ban
  [fold in existing `test_tc3_*`] — plus a non-vacuity mutation-proof on the fence comparison.
- **TR-22** (exposure-registry auto-classification): explicitly-labeled entry covering both
  classification directions [fold in existing `test_tc13_*` pair] + r2 initialization
  [fold in existing `test_tc14_*`] — plus a non-vacuity mutation-proof on `is_exposed_before`.
- **TR-26** (depletion revealing-quote timing): a genuine production bug fix in
  `micro_observer.py`, its previously-wrong test assertion corrected, two new tests added, plus a
  non-vacuity mutation-proof.
- **Passenger 1**: `MicroReadinessSection` DOM testid present in all three render states (closes
  iteration 15's COHERENCE-WARN).
- **Passenger 2**: Scout Ledger table survives a malformed/tampered trial row (row-level
  defensive read, not a page-wide error boundary).
- **Passenger 3**: seeded-violation counter-test for the two iter-15 `_PRICE_ARITHMETIC_FIELDS`
  clauses.

**Every one of the three traps' acceptance additionally requires proving the test FAILS when its
defect is deliberately reintroduced, then passes again restored** — the binding design rule this
round (iteration 15's own opaque-pool regression test sealed an unregistered universe and could
not have caught the leak it was written for; only the auditor's mutation-proof found this). A
trap that only shows green today, without that reintroduction step recorded, is not done.

## Agents Required

- **backend-data: yes** — TR-3/TR-22 trap-suite entries + non-vacuity proofs
  (`test_micro_accessor.py`, `test_walkforward.py`); TR-26 depletion-timing fix
  (`micro_observer.py`) + corrected/added tests (`test_micro_observer.py`);
  `_PRICE_ARITHMETIC_FIELDS` seeded counter-test (`test_desk_ui_guards.py`).
- **frontend-ux: yes** — `MicroReadinessSection` testid wrapper + Scout Ledger table defensive
  reads (`apps/frontend/app/desk/page.tsx`).

## Frontend Present

Frontend Present: yes

(J-10's kept-product sentinel is a full browser pass over the store-scoped rig; the two frontend
passengers are DOM/resilience-only — no new surface, no new served value.)

## Files to Create/Modify

Backend:
- `apps/backend/tests/test_micro_accessor.py` — TR-3 labeled entry: reference existing
  `test_tc1_*` (single-read fence) and `test_tc3_*` (import-ban); add the non-vacuity
  mutation-proof for the fence.
- `apps/backend/tests/test_walkforward.py` — TR-3's NEW multi-session aggregate-boundary test
  (see note below); TR-22 labeled entry referencing existing `test_tc13_*` pair + `test_tc14_*`;
  add the non-vacuity mutation-proof for `is_exposed_before`.
- `apps/backend/app/research/micro_observer.py` — **production fix**: `_advance_depletion_run`'s
  price-change branch (`if run is None or run["price"] != price: if run is not None:
  self._resolve_depletion(side, run)`) currently resolves using the OLD run's own
  `observed_through` (the last same-price quote). Thread the NEW quote's own `ts` through so
  `_resolve_depletion` stamps `observed_through`/`available_at` at the REVEALING quote's instant.
  The depletion MAGNITUDE (`start_size - current_size`) is computed from the pre-change run data
  and must stay unaffected. The bound-termination branch (hits `DEPLETION_WINDOW_QUOTES`) is
  already correct — leave it untouched.
- `apps/backend/tests/test_micro_observer.py` — correct
  `test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_the_next_trade_row`'s
  assertion (`observed_through`/`available_at` `2.0` → `3.0`; `value` stays `200.0` — this
  assertion change IS the specified behaviour fix, not a regression); add a bound-termination
  fixture test (20 same-price updates, no price change); add a truncation-boundary test
  (truncate strictly before the revealing quote ⇒ unresolved/absent, never guessed; at/after ⇒
  deterministic); add the TR-26 non-vacuity mutation-proof (revert the fix, corrected test fails).
- `apps/backend/tests/test_desk_ui_guards.py` — seeded-violation counter-test for the two
  iter-15 clauses (`readiness.sealed_tranche.*`, `universeCounts.*`,
  `readiness.joinable_corpus.withheld_excluded`), mirroring
  `test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic` exactly.

Frontend:
- `apps/frontend/app/desk/page.tsx` `MicroReadinessSection` (~5886-5904) — wrap the
  `LoadingPanel`/`UnavailablePanel` early returns in `data-testid="micro-readiness-section"`,
  copying `ValidationVaultSection`'s already-fixed pattern verbatim (page.tsx:6684-6699).
- `apps/frontend/app/desk/page.tsx` Scout Ledger table (~6315/6317) — defend
  `trial.feature.name`/`.transform` and `trial.outcome.horizon_key` with optional chaining + a
  fallback glyph (e.g. `"—"`) so a malformed row degrades only its own cell(s). Row-level only —
  no page-wide `ErrorBoundary`.

Docs:
- `docs/handoffs/goal-rapid-microscope-iter-16-dev.md` — dev handoff (required deliverable).

**Do NOT touch** (frozen this round): `vault.py`, `tick_recorder.py`, `micro_readiness.py`'s
served computation, `scout.py`, `scout_ledger.py`, `walkforward_ledger.py`, `micro_routes.py`'s
route shape, `micro_chain_ledger.py`, any `referee_*.py`, any Playbook detector, any `Config`
field. `micro_accessor.py` and `walkforward.py` themselves get **test-file-only** changes this
round (no production edits to either) — the ONE production edit anywhere is `micro_observer.py`'s
depletion-timing fix.

## Note on TR-3's aggregate-boundary test (resolving a spec ambiguity)

The phase spec describes TC-2 as exercising "the walk-forward origin-window/session-enumeration
path, its one existing `origin=` consumer." Direct code inspection found no production call site
that actually constructs `MicroAccessor(..., origin=...)` — the only two production callers
(`micro_join.py:434`, `scout.py:353`) both use the disclosed unfenced mode (`origin` defaults to
`None`); `walkforward.py`'s `build_folds` is a pure function over `session_dates: list[str]` and
never touches the accessor. Since production changes to `micro_accessor.py`/`walkforward.py` are
out of scope this round, treat this as descriptive framing, not a pointer to existing code: write
TC-2 as a NEW TEST ONLY. Plant several fixture datasets+snapshots spanning consecutive session
dates (the existing `_plant_dataset_and_snapshot` helper in `test_micro_accessor.py`, or an
equivalent in `test_walkforward.py`, mirroring `build_folds`'s window shape), construct one
`MicroAccessor(origin=T)`, and loop `read_snapshot_rows` per dataset to assert the returned/refused
set is exactly `{s : s <= T}`, boundary-exact at T and T+1. No new production helper is needed or
wanted.

## UI Evolution

- New user-facing capability: none — this round hardens the trap suite and fixes an internal
  availability-timing bug.
- New information displayed: none — the testid is a DOM/test-tooling attribute; nothing served
  changes shape.
- New user actions: none.
- UI surface changes: none structurally — the Scout table's malformed-row cells degrade
  gracefully instead of throwing (resilience, not a new surface); `MicroReadinessSection` gains
  the same `data-testid` its three sibling sections already always carry.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `LoadingPanel`/`UnavailablePanel` wrapper pattern exactly
  as already shipped on `ValidationVaultSection` — no new components, no new styling.
- Layout: unchanged — no new section, no layout change.
- Key visual effects: none new. The only frontend edits are a DOM testid attribute and a
  fallback-glyph defensive read.
- States to handle: `MicroReadinessSection`'s three states (loading / unavailable / loaded) must
  ALL carry the wrapper testid — verify "unavailable" and "loaded" live (the proven iter-15
  technique: stop the backend genuinely for "unavailable", normal run for "loaded"); "loading" is
  transient and may be confirmed by code symmetry with its now-identical siblings if it cannot be
  screenshotted deterministically. The Scout table's malformed-row state must render a fallback
  without throwing, with the rest of `/desk` unaffected.

## Key Test Scenarios

**TR-3 (accessor origin-fence)** — non-vacuity required:
- Single-read: dates ≤ origin succeed; > origin raises `MicroAccessorOriginFenceError` (typed,
  never empty/truncated) — existing `test_tc1_*` coverage.
- NEW: aggregate view over sessions S1 < T=S2 < S3 — at `origin=S2` returns exactly `{S1, S2}`;
  at `origin=S3` returns exactly `{S1, S2, S3}` — boundary-exact both directions (iter-11 lesson:
  prove both sides, not just the refusal side).
- Import-ban: only `micro_accessor.py` opens `read_snapshot_rows` — existing `test_tc3_*` coverage
  (its own non-vacuity proof, `test_tc3_import_ban_guard_can_fail_on_a_seeded_violation`, already
  exists — reference it, don't re-derive).
- Non-vacuity: temporarily weaken the fence comparison to never refuse → the new suite must FAIL;
  restore → passes again.

**TR-22 (exposure registry)** — non-vacuity required:
- registered-after-exposure → `historical_exposed_diagnostic`; registered-before-any-exposure →
  `historical_oos` — existing `test_tc13_*` pair (`test_walkforward.py:282,298`) already proves
  both directions; fold in / reference, don't re-derive.
- r2 initialization pre-marks every playbook-corpus and legacy-tick window exposed — existing
  `test_tc14_*` coverage.
- Non-vacuity: mutate `is_exposed_before`'s strict `<` to always return `False` → the suite must
  FAIL at the auto-classification assertion; restore → passes again.

**TR-26 (depletion revealing quote)** — non-vacuity required, production fix:
- Corrected: `observed_through`/`available_at` == `3.0` (the revealing quote), `value` stays
  `200.0` (unaffected).
- New: bound-terminated run (20 same-price updates, no price change) resolves at the 20th quote's
  own instant.
- New: truncation boundary — truncate strictly before the revealing quote ⇒ the run does not
  appear as resolved (absent/`unavailable`, never guessed); at/after ⇒ deterministic resolution.
- Non-vacuity: revert the fix (price-change branch stamps the pre-change run's own
  `observed_through` again) → the corrected assertion must FAIL; restore → passes.
- Guard against a NEW lookahead in the other direction: the fix must not stamp `available_at`
  earlier than the revealing quote either — only correct the "one quote early" direction.

**Frontend passengers:**
- `MicroReadinessSection`: `data-testid="micro-readiness-section"` present in all three states.
- Scout table: seed a sparse/malformed trial row via `ScoutLedger.append_row` into an ISOLATED
  fixture store (the iter-15 audit's own reproduction recipe — the same sparse field set as
  `test_desk_scout_tool_byte_identical_on_a_populated_state` uses) and confirm only that
  row/cell degrades; the rest of `/desk` renders normally; `chain_verification` still shows a
  tampered-ledger verdict rather than crashing before it can render.
- `_PRICE_ARITHMETIC_FIELDS`: all six seeded violations across the two new clauses are caught;
  zero false positives on the real `page.tsx`.

**Regression / kept-product sentinel:**
- Full backend suite: 0 failures, passed count ≥ 3229 (iteration-15 baseline: 3237 collected /
  3229 passed / 8 skipped).
- `Config().config_fingerprint()` == `08e471b10130e1e2`.
- SHA-256 of the six `referee_*.py` files (`referee_adjudicate.py`, `referee_evidence.py`,
  `referee_null.py`, `referee_registry.py`, `referee_routes.py`, `referee_stats.py`) +
  `micro_chain_ledger.py` match the iteration-0 baseline byte-for-byte.
- `tsc --noEmit` clean.
- Required-still-passing J-01, J-02, J-03, J-04, J-05, J-08 via stored golden replay scripts;
  J-07 via direct-endpoint LLM navigation to `GET /research/desk/micro/graduation` (no golden
  script exists for it by design); J-06 explicitly excluded (no file under its module changes).
- Target J-10: browser-verify the kept-product sentinel — cockpit `/` live tape + chart,
  `/structure` load + Tradable Map, every shipped `/desk` section including the three Referee
  sections and all four Rapid-Microscope sections — via the store-scoped rig (`:8301`/`:3301`).
  `rm -rf apps/frontend/.next` + rebuild first (T-9); element-capture below-the-fold sections; no
  screenshot ⇒ `unknown`, never `passing` (T-10).
- J-10 stays `partial` at 27/29 traps at the end of this round — planned, not a shortfall.

**Environment constraints to respect (do not fight these):**
- No acceptance criterion may depend on a live Scout compute finishing — one ran past 25 minutes
  against the real corpus without producing a single candidate.
- The shared QA fixture rig has never been seeded with a Scout family, Walk-Forward sequence, or
  Vault shard. Any test needing that shape of data (e.g. the Scout-table defensive-read
  verification) must seed its OWN isolated, hermetic fixture store (`tmp_path`-scoped) — never
  assume the shared rig already carries it.
- Do NOT record real tape this round (J-06 is out of scope).
