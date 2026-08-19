# Iteration 12 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-12
**Date:** 2026-08-19
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Backend-only iteration (7 files: `main.py`, `micro_chain_ledger.py`, `micro_routes.py`,
`tick_recorder.py`, `vault.py`, `tests/test_vault.py`, `tests/test_tick_recorder.py`). No
`.tsx`/`.ts` files touched (verified: `git diff --stat -- '*.tsx' '*.ts'` empty). The blueprint
registers three additive sub-field tables this iteration, all sub-fields of already-registered
rows, no new owner, no new endpoint. Each was traced to the actual serving code, not just the
docstrings.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `rule_commitment` (replaces `rule_hash` at committed stage) | OK | `apps/backend/app/research/vault.py` `_serialize_universe` (~line 613-651): `base` dict serves `rule_commitment`; `rule_hash` is never placed in any served dict — confirmed by `grep '"rule_hash"' apps/backend/app/` returning only internal uses inside `register_universe`'s own re-registration check (vault.py:685,689,696). Single owner (`vault.py`), single endpoint (`GET /research/desk/micro/vault` via `build_vault_state`, which `micro_routes.py:538 get_vault` forwards verbatim, "no second computation in this handler"). |
| `commitment_nonce` (revealed-stage only) | OK | `vault.py` `_serialize_universe`: included only in the `released_universe_ids` branch, alongside `symbol_rule`/`date_rule`. Same owner/endpoint as above. |
| `exposure_state` value-space extension (`exposure_unknown`) | OK | `vault.py`: `STATE_EXPOSURE_UNKNOWN` (line ~309) flows through the existing `_serialize_shard` (line ~902) and `build_vault_state`, same `GET /vault`. Test `test_tc5_an_unprovable_reconstruction_marks_affected_shards_exposure_unknown_permanently` confirms `entry["exposure_state"] == vault.STATE_EXPOSURE_UNKNOWN` is read back through the normal `build_vault_state` path, not a second accessor. |
| `progress.trades_total_bucket` / `progress.quotes_total_bucket` | OK | `tick_recorder.py` `_progress_view` (line ~709-748) replaces the exact `trades_total`/`quotes_total` keys with `_volume_bucket(...)` output. Traced both servers of this value: `GET /recorder/compute` (`micro_routes.py:482`) and `POST /recorder/compute`'s immediate return both call the SAME `_copy_recorder_snapshot()` → `_progress_view()` pipeline (`tick_recorder.py:752-762`, docstring: "used by BOTH ... so neither surface can diverge from the other") — one computation, two callers. Also checked the third surface under this Data Contract row, `GET /recorder/runs`: `_run_log_entry` (`tick_recorder.py:765-786`) serves `chunks_total`/`chunks_done`/outcome-type counts/`datasets_recorded`/`bars_recorded`/`error` only — no `trade_count`/`quote_count` field anywhere, and its own docstring notes this shape is "already aggregate-only ... out of this iteration's scope." No leak through the sibling endpoint. |
| Raw `trades_total`/`quotes_total` (internal running totals) | OK — not served | `_IDLE_PROGRESS`/`_publish` (tick_recorder.py:636, 859-860) keep exact internal accumulators, by design (so a future surface needing the exact value doesn't have to re-derive it) — but `_progress_view` builds an explicit whitelist dict that never spreads or includes the raw keys. `micro_routes.py:491`'s docstring still lists the old field names in prose (already flagged MINOR by the reviewer as a stale comment) — verified this is cosmetic only: the actual code path is the same single `_progress_view` traced above, so the served JSON is correct; nothing computes or serves the exact value through a second path. |
| New `VaultRecoveryLedger` (TR-25 lawful-recovery incident ledger) | OK — no Data Contract row needed yet | `vault.py` adds a third `HashChainedLedger` wrapper (`recovery_ledger_for_dataset_dir`, ~line 470) that `recover_shard_ledger` appends to. Grepped `micro_routes.py` (shown in full in the bounded diff — only two docstring edits, no new route) and `build_vault_state`'s return shape: neither exposes any `VaultRecoveryLedger` content via any endpoint. Since nothing displays/serves it yet, there is no "value" for the Data Contract to register (matches the existing precedent that `seal_shard`/`assign_shard`/`expose_shard` — also zero production call sites, also `vault.py`-owned — need no separate registration). Does not duplicate an existing entity's home; it is a genuinely new, currently-unserved audit trail. Register it if/when a route or CLI ever surfaces its content. |
| `verify_chain()`-first fail-closed refusal (TR-25) | OK — not a displayed value | Confirmed it is a refusal behavior (HTTP 503 via the new `main.py` global exception handler), not a served field — matches the phase spec's own Data-contract-additions text and needs no row. |

No duplicate computation of any registered value was found anywhere in the diff. No new UI
surface exists this iteration to fetch any value from a non-canonical source (there is no new UI
surface, period).

## Information Architecture check

No new page, route, or nav entry. `app/meta.py` (`UI_ROUTES`) is untouched (confirmed via `git
diff --stat`), no `apps/frontend/` file changed, and no `blueprint.reapproval-requested` file
exists on disk. The three sub-field additions are all served through already-registered
endpoints under the already-registered Desk → Rapid Microscope home — there is nothing new to
place in the nav.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new feature/page/route this iteration) | OK | `apps/backend/app/meta.py` unchanged; `apps/frontend/` unchanged (verified by `git diff --stat` against both) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The new `VaultLedgerCorruptionError` global exception handler in `apps/backend/app/main.py`
  (added right after the existing `_real_data_error_handler` for `RealDataError`) reuses that
  exact established pattern rather than inventing a new cross-cutting mechanism — this is
  consistent with, not a drift from, the project's existing architecture. No action needed.
- Two items already surfaced by the reviewer (`reports/reviews/goal-rapid-microscope-iter-12-review.md`)
  were re-checked here specifically for Data Contract impact and confirmed to have none: (1)
  `seal_shard`/`assign_shard`/`expose_shard` gating `verify_chain()` on their own shard ledger
  only — this affects when a refusal fires, not what any endpoint serves, and the phase spec's
  Data-contract-additions text already says the fail-closed behavior itself has no Data Contract
  row; (2) `micro_routes.py:491`'s stale docstring field list — cosmetic, the actual served shape
  is correct and single-sourced (traced above). Not re-flagging either as coherence findings, per
  the carried-context instruction.
- Also re-checked the reviewer's NOTE-severity item: `_whole_pool_released_universe_ids`'s
  pair-coverage test (`vault.py` ~line 608) stays byte-exact on symbol case, while the sibling
  `unresolved_pool_universe_by_dataset_id` normalizes case this same diff. This is an internal
  state-transition-timing asymmetry (a non-canonical-case-registered universe can never reach
  `REVEALED`), not a Data Contract violation — it does not cause any served value to differ
  between two surfaces, and it fails safe (conservative under-disclosure, never an early leak).
  Carried forward as the reviewer already logged it; no new action from this audit.
- If/when `recover_shard_ledger`'s output (the `VaultRecoveryLedger` incident trail) is ever
  exposed through a route, CLI, or UI, register it as a new Data Contract row at that time (owner
  `vault.py`, per the pattern this iteration already used for its sibling ledgers).
