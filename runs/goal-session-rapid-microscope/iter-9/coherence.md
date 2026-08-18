# Iteration 9 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-9
**Date:** 2026-08-18
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration's diff is far larger than the iter-9 spec file's own IN SCOPE list describes
(vault.py + 4 files), because it carries three in-iteration fix rounds under two owner rulings
(spec revisions r3 and r4, `docs/rapid-validation-spec.md` §7.5) on top of the original build —
confirmed against `docs/handoffs/goal-rapid-microscope-iter-9-dev.md`'s "Fix Notes" sections and
`git status` (17 backend source files + 13 test files + 2 docs modified, plus `vault.py`/
`test_vault.py` untracked-new). r4 §7.5 point 6 requires every corpus-wide enumerator to exclude
withheld (non-`exposed`) vault shards through ONE shared predicate. I verified this single-source
property by direct code read of every call site, not by trusting the dev handoff's claim.

**The one predicate, traced end to end:**
`vault.withheld_dataset_ids()` (`apps/backend/app/research/vault.py:735`, itself
`frozenset(withheld_universe_by_dataset_id(ledger))` at line 738) is the sole computation of "which
dataset ids are withheld." `micro_snapshots.py:721` wraps it once as
`withheld_dataset_ids_for_store`, and `micro_snapshots.py:740` wraps that once more as
`exclude_withheld(records, dataset_store) -> (kept, withheld_excluded)` — the ONE
exclusion-and-disclosure primitive. Every enumerator r4 names imports and calls it, never
re-derives its own filter:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Withheld-shard predicate (`exclude_withheld`) | OK — single definition, reused verbatim | defined `micro_snapshots.py:740`; called from `desk_screen.py:108`, `edge_report.py:232` (via `_verified_corpus`), `edge_report_cache.py:422,433`, `micro_join.py:464,482`, `pnl_scan.py:974` (via `_verified_corpus`), `scout.py:1214`, `setups.py:1250`, `walkforward.py:1433` |
| Vault shards/universes/exposure ledger (blueprint-registered row) | OK — served verbatim from the pre-registered owner | `vault.py` (new) → `GET /research/desk/micro/vault`; `build_vault_state` (vault.py:812) composes only from its own two ledgers, no re-derivation of another module's value |
| `HashChainedLedger` primitive | OK — reused, not reimplemented | `vault.py:120` imports `micro_chain_ledger.HashChainedLedger`; `VaultUniverseLedger`/`VaultShardLedger` (vault.py:325,344) are thin wrappers, matching the `WalkForwardLedger` shape |
| `family_root_id` identity function | OK — reused, not reimplemented | `vault.py:121` imports `scout_ledger.compute_family_root_id` verbatim (TR-20 depends on exactly one identity function) |
| Split axis (`recorder_split_for`) | OK — untouched, not duplicated | `vault.py`'s `compute_seal` (line 506) is a new, independently-named function for the seal axis; no split-rule logic appears in vault.py |
| Corpus readiness truth / `distinct_datasets` (already-registered row, owner `micro_readiness.py`) | OK — same owner, extended not duplicated | `micro_readiness.py:535` reads `vault.withheld_universe_by_dataset_id` directly (not `exclude_withheld`) because it needs the per-universe mapping for its new `sealed_tranche.by_universe` aggregate — a differently-shaped read of the identical vault-owned set, not a second predicate |
| Route-level sealed refusal (spec §7.5 point 3, r3 — a different rule from r4 point 6) | OK — same vault primitive, different call shape | `routes.py:1075` `get_withheld_dataset_ids()` calls `vault.withheld_dataset_ids(vault.shard_ledger_for_dataset_dir(CONFIG.dataset_dir_resolved()))` directly; this is a single-id-membership check for a 403 refusal, not a corpus-wide list filter, so it legitimately doesn't route through `exclude_withheld` — but it still traces to the same canonical vault function, not a hand-rolled second implementation |
| `withheld_excluded` / `sealed_withheld` / `sealed_tranche` (new disclosure sub-fields, ~9 endpoints) | UNREGISTERED (WARN, not FAIL) | additive counts owned by each parent endpoint's already-registered module; not displayed by any UI this iteration (0 `.tsx` files changed) |

I also grepped the whole diff for raw `exposure_state`/`"exposed"` comparisons outside
`vault.py`/`micro_snapshots.py` to rule out a hand-rolled second filter hiding behind different
variable names — zero hits (the only two matches are docstring prose, not code). I additionally
read `pnl_ledger.py`, `pnl_scan.py`, `scout.py`, `setups.py`, `walkforward.py`, `edge_report.py`,
`edge_report_cache.py`, `desk_screen.py`/`desk_screen_compute.py`, and `datasets.py` in full diff
form: `edge_report.py`/`pnl_scan.py` were both refactored so `_split_datasets` now takes an
already-filtered in-memory record list instead of re-reading the store per split — closing exactly
the "disclosed count and measured rows come from two different reads" divergence risk their own
docstrings name. `walkforward.py` deliberately uses two *different* predicates
(`vault.currently_sealed_dataset_ids` for the r2 seed vs. `exclude_withheld`'s wider set for the
fold-request inventory) — disclosed and justified in `_tick_dataset_session_dates`'s docstring
(spec §7.5's `sealed` vs. `!= exposed` distinction), not an accidental divergence. `tick_recorder.py`
is deliberately *not* filtered, with the reason written into its docstring (it is the recorder's own
idempotency check, not a corpus report). This matches the independent code reviewer's own
independent verification (`reports/reviews/goal-rapid-microscope-iter-9-review.md`: "edge_report/
pnl_scan's `_verified_corpus` is a single list-and-verify-and-filter read so the disclosed
`withheld_excluded` count can never diverge from the measured rows").

**Not a coherence-auditor finding (out of my mandate, correctly triaged elsewhere):** the third
independent audit (`docs/handoffs/goal-rapid-microscope-iter-9-audit.md`, verdict PASS_WITH_GAPS)
and the code reviewer both carry forward, by name, CRITICAL/MINOR findings that the vault's
join-resistance guarantee is not fully achieved (B2: a universe's sealed membership is still
inferable via `expected − served` set subtraction between `GET /vault`'s committed rule and
`GET /datasets`; B3: the recorder-compute route leaks the same complement; B4: the withheld
predicates read `HashChainedLedger.all_rows()` without `verify_chain()`, fail-open on ledger
corruption; B5/NEW-2: `referee_evidence.py` — one of the six frozen-hash-pinned files — is not
seal-filtered, a genuine r4-vs-freeze collision). These are security/completeness gaps in whether
the *sealing* guarantee holds, not a Data Contract violation: no value is computed twice, no UI
reads a value from a non-canonical source (all four are explicitly owner-ruling-gated and provably
inert today, since `seal_shard` has zero production callers this iteration — confirmed by both the
dev handoff and the reviewer via grep). They are the independent auditor's and evaluator's territory,
already correctly disclosed and carried by name rather than silently dropped.

## Information Architecture check

Zero frontend files changed this iteration (`git status`: 0 `.tsx`/`.ts`/`.css` files; independently
confirmed by `reports/phase-goal-rapid-microscope-iter-9-ui-surface-map.md`'s own grep for "vault"
under `apps/frontend/` → zero matches). `GET /research/desk/micro/vault` is a new backend route
only; no new page, no new nav entry, no new shell.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/desk/micro/vault` | OK — no UI this iteration, route lives beside its siblings | `micro_routes.py` (same router as every other rapid-microscope route, no parallel router); `blueprint.md`'s IA already reserves "Validation Vault" under `/desk` → Rapid Microscope as J-06's canonical home, matching the same early-registration-ahead-of-UI pattern the blueprint's own iter-3 footnote documents (reused here in the mirror direction: implemented-but-not-yet-surfaced rather than registered-but-not-yet-built) |
| `/desk` Validation Vault section | OK — confirmed absent, matching OUT OF SCOPE | `apps/frontend/app/desk/page.tsx`'s `DeskCollapsibleSection` type (per the ui-surface-map, line 358) lists no `vault` section; the ui-surface-map's own negative-check row requires an element capture proving "Validation Vault" text does not appear anywhere on `/desk` |

No duplicate home, no undiscoverable route, no parallel shell — there is nothing new to reach.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Unregistered-but-new disclosure sub-fields.** `withheld_excluded` (edge_report, edge_report_cache,
  pnl_scan, scout, walkforward, micro_join, desk_screen, micro_snapshots), `sealed_withheld`
  (`GET /research/datasets`), and `sealed_tranche` (`micro_readiness.build_readiness`) are now served
  across roughly nine endpoints but are not yet rows in `blueprint.md`'s Data Contract table. They are
  additive sub-fields owned entirely by each parent endpoint's already-registered module (no competing
  owner, no UI consumer yet, byte-identical/all-zero while nothing is sealed), so this is not a
  duplication risk today — but the decomposer should add a line for them next time the blueprint is
  touched, most naturally when J-08 wires the Validation Vault section into `/desk` and these counts
  first reach a screen.
- **`routes.py`'s `get_withheld_dataset_ids()` re-derives from `CONFIG.dataset_dir_resolved()`
  directly rather than composing through `micro_snapshots.withheld_dataset_ids_for_store(store)`
  via its own `store: DatasetStore = Depends(get_dataset_store)` dependency.** Both resolve to the
  same directory in production (`get_dataset_store` at `routes.py:293` also reads
  `CONFIG.dataset_dir_resolved()`), so this is not a live divergence, and both ultimately call the
  same `vault.withheld_dataset_ids`/`vault.shard_ledger_for_dataset_dir` pair — but composing through
  the store dependency instead would remove even the theoretical risk of the two ever being resolved
  differently (e.g. under a future per-request store override) and would match the "one resolver, one
  path" discipline the rest of this diff otherwise holds to consistently. Cosmetic; not a fix this
  gate requires.
- The four owner-ruling-gated join-resistance gaps (B2/B3/B4/B5-NEW-2, listed above) are not this
  gate's concern, but they are the load-bearing reason `docs/handoffs/goal-rapid-microscope-iter-9-dev.md`
  explicitly states J-06 step 4 (the credentialed real-tape recording) remains blocked. Flagging here
  only so the evaluator does not read this coherence PASS as implying the vault's security property is
  fully closed — it is not; it is coherent (one source of truth, one home) but not yet safe to seal
  real data under.
