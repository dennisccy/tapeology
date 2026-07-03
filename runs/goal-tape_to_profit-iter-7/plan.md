# goal-tape_to_profit-iter-7 Execution Plan

## What to Build

J-07 — the candidate-sweep harness, the goal-closing journey (J-01–J-06, J-08 already pass; a
clean pass here makes the next evaluation a GOAL_ACHIEVED candidate). `python -m
app.research.pnl_scan --out <path>` must:

- Enumerate every registered **candidate profile** (today: `candidate-faster-warmup` — profiles
  with `is_default: False`; `default` is never itself a candidate, per the goal glossary).
- For each candidate, backtest it against the **current champion** (strategy held constant at the
  champion's `strategy_id`; only `profile` varies) over **every train dataset**, then validate on
  the **hold-out** dataset(s) — reusing `BacktestJobManager`/`BacktestRunner`
  (`app/research/backtests.py`) as the ONE computation path, exactly as `pnl_baseline.py` already
  does (`jobs.create(...)` + `jobs.run_sync(...)`).
- Write a scan report to `--out`: per candidate — train + hold-out net R/$ deltas (candidate minus
  champion), n per split, per-dataset breakdown, `survivor` (hold-out net R AND net $ both beat
  the champion, n ≥ the configured promotion minimum), `robustness` (`robust` iff positive on
  every individual train dataset, else `speculative`), and `overfit` for train-positive/
  hold-out-negative candidates. Every candidate gets full train+holdout figures regardless of
  outcome — "validates apparent winners on hold-out" explains *why* the hold-out check exists, not
  a conditional skip that would leave gaps in the report.
- On a genuine survivor: append exactly one PnL-ledger row via the existing single writer
  (`pnl_ledger.append_validation_row`, passing the champion's own measured splits as `baseline` —
  already documented as this function's intended second caller) AND move a **newly persisted,
  single-source champion pointer** (today a hardcoded constant in `profiles.py`) — so
  `GET /research/profiles` (hence `/performance` and MCP) automatically reflects a real promotion
  with zero frontend changes.
- Zero candidates / zero survivors → honest report, **exit 0**, champion unmoved, no ledger row.
  Corrupt dataset / unavailable store → explicit distinct error, no partial write.
- Deterministic: fixed seeds, byte-identical `--out` across two independent fresh-state runs of
  the same non-promoting scenario (see Design Notes — a promotion mutates persisted state, so
  "identical re-run" can't mean two sequential runs against the same store).

No new UI: `/performance` already renders whatever `GET /research/profiles` returns; on the
shipped fixtures the sweep yields zero survivors, so the page stays visually unchanged (only its
data source moves from a constant to a persisted read).

## Agents Required

- backend-data: yes -- all of the above: `pnl_scan.py`, the config-owned promotion gate, the
  persisted champion pointer (store migration + accessors), `profiles.py`/`routes.py` wiring, and
  the full test matrix below.
- frontend-ux: no -- zero frontend files change (confirmed: OUT OF SCOPE explicitly bars new
  pages/panels/nav; `/performance` (J-05) already generically renders the profiles/champion
  payload with no hardcoded shape).

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/research/pnl_scan.py` (new) -- the sweep engine + `__main__` CLI entry.
- `apps/backend/tests/test_pnl_scan.py` (new) -- sweep test matrix (see Key Test Scenarios).
- `apps/backend/app/config.py` -- add the config-owned promotion minimum-n field (reuse
  `pnl_min_sample_size` or add `promotion_min_sample_size`; see Design Notes on fingerprint
  exclusion — this is the single riskiest small decision in the iteration).
- `apps/backend/app/research/store.py` -- schema migration v9→v10: a single persisted
  champion-pointer table/row (seeded to the founding `{strategy_id: v1, profile: default}` on
  both fresh-create and migrate-from-v9), plus `JournalStore` get/set accessors (set goes through
  the existing single-writer queue, mirroring `append_pnl_ledger_row`'s pattern but as the one
  intentionally-mutable pointer rather than an append-only row).
- `apps/backend/app/research/profiles.py` -- `profiles_projection()` reads the champion from the
  new persisted pointer instead of the hardcoded `STRATEGY_V1_ID`/`PROFILE_DEFAULT` literal pair
  (those constants remain the seed/founding values, just no longer read directly at serve time).
- `apps/backend/app/research/routes.py` -- `GET /research/profiles` gains
  `registry: ResearchRegistry = Depends(get_registry)` (it currently takes no dependency) and
  passes `registry.store` into `profiles_projection`.
- `apps/backend/tests/test_profiles_api.py` -- **breaking change to flag for the reviewer**: this
  file currently uses a bare lifespan-less `TestClient(app)` specifically because "the projection
  is config-owned with no registry/engine/store dependency, so no injection is needed" — that
  premise no longer holds once the route reads a persisted pointer. Migrate to the store-backed
  `ctx` fixture pattern already proven in `test_pnl_ledger_api.py`
  (`JournalStore` + `ResearchRegistry` + `set_registry` + `TestClient(app)` inside a `with` block).
  Add a case asserting the served champion reflects a moved pointer.
- `apps/backend/tests/test_no_execution_path.py` -- add `"backend/app/research/pnl_scan.py"` to
  `test_scan_is_not_vacuous`'s explicit path assertions (the glob-based scan already covers new
  files automatically; this is the belt-and-suspenders explicit check the spec calls for).
- `docs/handoffs/goal-tape_to_profit-iter-7-dev.md` (new) -- required dev handoff.

No changes expected to `app/research/backtests.py`, `app/research/pnl_ledger.py`,
`app/research/datasets.py`, or `app/mcp/` — all are reused verbatim as the single existing
computation/writer paths (`app/mcp/` must stay zero-diff per OUT OF SCOPE).

## Design Notes (read before implementing — resolves two non-obvious traps)

1. **Fingerprint exclusion for the promotion-min-n field.** The DoD requires the **pinned literal**
   default fingerprint `4d665603569b9dbf` to survive this iteration unchanged. `config_fingerprint()`
   hashes every non-excluded field; adding ANY new Config field without excluding it changes that
   hash for every profile, including `default` — breaking the pinned value regardless of which of
   the two field options is chosen. Recommendation: **exclude** the field (same discipline as
   `pnl_min_sample_size`), matching the precedent that a threshold gating *which rows get labeled
   or promoted* — never a trade, fill, or aggregate — is presentation/decision-only. The
   config.py:920 note's "will be fingerprinted there" most plausibly refers to the promotion
   record's *existing* provenance stamp (every backtest report already carries its own
   `config_fingerprint`), not a mandate to un-exclude this specific field — but the note explicitly
   calls itself a "separate, future decision," so treat this as a flagged judgment call, not settled
   law; verify against the pinned-fingerprint test before considering it closed.
2. **Promotion is two writes, not one.** A survivor promotion both appends a ledger row AND moves
   the champion pointer — two separate SQLite writes (no cross-table transaction exists elsewhere in
   this codebase). Decide and test an explicit failure-ordering discipline so a mid-promotion crash
   never leaves an "orphan" (e.g., verify/attempt the pointer move first and only append the ledger
   row once it is confirmed persisted, or vice versa — either is acceptable as long as the failure
   mode is one explicit, honestly-surfaced error with no silently-inconsistent state, per the
   "explicit failure, no half-applied champion move or orphan ledger row" DoD bullet).
3. **Single-mover discipline.** Since this is the iteration's only anti-goal-gated state mutation
   (flagged as the reason for `full` depth), add a source-scan test asserting only
   `app/research/pnl_scan.py` calls the champion-pointer setter — the same style as this codebase's
   existing "no engine path outside the backtest runner resolves a profile" guard.

## Key Test Scenarios

1. **Fixture sweep (non-regression baseline).** Committed train+holdout fixtures, default champion
   vs `candidate-faster-warmup` → exit 0; report shows zero survivors, candidate labeled
   non-survivor/overfit; **afterward**: champion pointer still `v1/default` via
   `GET /research/profiles`, PnL ledger still has row_count 1 (founding row only), default
   fingerprint still `4d665603569b9dbf`.
2. **Controlled survivor scenario** (isolated test fixtures or a test-local lower threshold via
   `dataclasses.replace` — never by weakening the shipped default): champion pointer moves,
   exactly one new provenance-stamped ledger row is appended via `append_validation_row`, `default`
   profile and engine defaults stay untouched.
3. **Min-n gate both ways**: below-minimum candidate rejected despite positive hold-out net R/$;
   at-or-above-minimum candidate with positive hold-out net R AND net $ is promoted.
4. **Determinism**: two independent fresh-state runs of the identical non-promoting scenario
   produce byte-identical `--out` file bytes (no wall-clock field in the report itself, mirroring
   the `render_history_markdown` pure-render precedent).
5. **Robustness/overfit labeling**: `robust` iff positive on every individual train dataset;
   `speculative` otherwise; a train-positive/hold-out-negative candidate is labeled `overfit` and
   never promoted.
6. **Single-source champion**: `GET /research/profiles` reflects the persisted pointer (not the
   retired constant); a source-scan confirms exactly one setter call-site.
7. **Honest empty/failure states**: zero registered candidates → honest report + exit 0; corrupt/
   unreadable dataset → explicit error, no partial write; store unavailable mid-promotion →
   explicit failure, no orphaned row or half-moved pointer.
8. **`test_no_execution_path.py`** stays green with `pnl_scan.py` explicitly covered.
9. **Full backend suite**: ≥ iter-6 baseline (1004 passed / 1 skipped), no test deletions,
   observer-equivalence 7/7.
10. **Required-still-passing journeys**: J-01/J-05/J-08 via golden replay (J-05 specifically
    re-proves `/performance` still renders correctly given `/research/profiles`'s new store
    dependency); J-02/J-03/J-04/J-06 via backend suite + in-page fetch. No golden replay exists for
    J-07 itself (machine/CLI surface, per the iter-2 lesson) — verify it via a live
    `python -m app.research.pnl_scan` run plus the backend suite.

## Out of Scope (per spec — do not implement)

Any broker/order/execution code; weakening the shipped min-n gate to force a fixture survivor;
any change to the `default` profile, engine defaults, or classifier; new MCP tools or `app/mcp/`
changes; new persistence scope beyond the journal SQLite champion pointer + existing ledger; ML/
optimizer/runtime-moving thresholds; edits to `docs/goal.md`; real-vendor/Alpaca datasets; any new
frontend page, panel, or nav entry.
