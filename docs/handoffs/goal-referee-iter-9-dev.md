# goal-referee-iter-9 Dev Handoff

**Phase:** goal-referee-iter-9
**Date:** 2026-08-15
**Agent:** developer
**Status:** complete

## What Was Built

**J-08 — the promotion interlock (target journey), fail closed, no bypass:**
- `pnl_scan.py`'s `_promote`/`run_sweep` now consult `referee_adjudicate.authorize_promotion`
  BEFORE `append_validation_row` (ledger-row-first / pointer-second order unchanged after
  authorization). `run_sweep`/`_promote` gain one new **required** keyword param,
  `certificate_store: CertificateStore` — required, not optional, so the interlock cannot be
  silently skipped by omission; every caller (CLI `main()`, every test) must now supply one
  explicitly.
- `live_scan_context` — `{champion_identity, train_dataset, holdout_dataset, config_fingerprint,
  gate_version, referee_parameters_hash}` — is built fresh from the live run's own values every
  call, never cached, never caller-overridable. `train_dataset`/`holdout_dataset` are narrowed to
  exactly `{id, checksum, split}` via a new `_dataset_pin` helper.
- The scan report's `promotion` block gains three new fields on every path (structural-skip,
  certificate-refused, and promoted): `promotion_eligible: bool|None`, `refusal_class: str|None`,
  `reason: str|None`. Everything else in the report is byte-compatible.
- `authorize_promotion` itself already existed (built unwired at iter-7) with all six refusal
  classes fully implemented — this iteration's job was wiring it in, not building it.

**J-08 — the strategy-family evaluation branch (spec §3.7) + the certificate's real mint site:**
- `referee_adjudicate.py` gains `_pool_strategy_trades(journal_store)`: pools
  `referee_evidence.strategy_observations()`'s primary/null trade lists by `cluster_key` = dataset
  id (never `session_date`), shaped identically to `_pool_against_null`'s own return dict so
  `run_evaluation_and_record` reuses every downstream step (coverage, permutation test, both
  bootstrap CIs, BH, snapshot) with zero new code in `referee_stats.py`.
  `occurrence_diffs` is honestly `None` (no natural per-occurrence pairing exists for this family
  — mirrors estimand B's own precedent).
- `run_evaluation_and_record` gains two new optional kwargs: `journal_store` (strategy-family pool
  source; every existing playbook-only caller unaffected) and `certificate_mint` (the caller's own
  live scan identity — see below). A strategy-family evaluation's `provenance.basis_caveats` now
  carries the Card-6.4 forming-bar caveat plus a new `REFEREE_STRATEGY_NULL_DESIGN_CAVEAT`
  disclosing the recorded null is 100 uniform-random entries, not count/ToD-matched.
- `_mint_strategy_certificate(...)` — the certificate's real mint call site (spec §8) — fires ONLY
  from `run_evaluation_and_record`'s own fresh-checkpoint path, only for
  `evidence_family == "strategy"`, only when the caller explicitly supplies `certificate_mint`
  (`{candidate, champion_identity_at_scan_time, train_dataset, holdout_dataset,
  certificate_store}`), and only after re-verifying the attestation. A Playbook checkpoint never
  reaches it.
- New `referee_parameters()` / `referee_parameters_hash()` aggregator (spec §1): combines
  `referee_stats_parameters()`, `null_tod_spec_parameters()`, `null_context_spec_parameters()`,
  `test_perm_spec_parameters()`, and `REFEREE_GATE_VERSION` into one dict, hashed once, read at
  call time — a monkeypatched constant anywhere in that chain moves both the dict and the hash.

**Riders:**
- `referee_registry.py`: new `_signal_matches_hypothesis_cell` shared helper applies the SAME
  `context_predicate`/backing-bucket check `_starter_context_readiness` already uses to BOTH
  `_hypothesis_accrual` and `_hypothesis_discovery`. `registry_response()` gains two new OPTIONAL
  params (`bar_store`, `config`) to build a `context_resolver` — omitted, every existing caller is
  unaffected (every hypothesis registered this era is Estimand A, `context_predicate is None`,
  which short-circuits before ever touching the resolver). `referee_routes.py`'s
  `get_referee_registry` now supplies `bar_store`/`config` for real.
- `REFEREE_STARTER_FAMILY_SHORTLIST` gains a sixth candidate, `S-6` (`range_trade:short at_wall`,
  estimand B — the S-4 short-side sibling spec §7 names but iter-8 dropped), reusing
  `_starter_context_readiness` verbatim.
- New `REFEREE_DEFAULT_Q = 0.10` and `REFEREE_STARTER_FAMILY_ID = "referee-starter-family"` module
  constants in `referee_registry.py`; `shortlist_response()` now serves `family_id`/`family_q` as
  new top-level fields. `apps/frontend/app/desk/page.tsx` reads both from the fetched shortlist
  response instead of its own two local literals (`REFEREE_STARTER_FAMILY_ID`/
  `REFEREE_STARTER_FAMILY_Q`, now deleted); `lib/types.ts`'s `RefereeShortlistResponse` gains the
  two fields.
- `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` extended to
  `hyp.accrual.(?:informative_post_boundary_sessions|target_sessions)`, mirroring the existing
  `hyp.discovery.*` entry, with its own seeded counter-test.
- `tests/test_pnl_scan.py`'s promotion-path assertions inverted per goal.md J-08 Step 4: every
  test that previously asserted an unconditional promotion on a genuine hold-out survivor now
  either asserts refusal (`no_certificate`) or supplies a certificate minted through the real
  evaluation rail. A new no-bypass source-scan guard test
  (`test_no_bypass_path_exists_for_authorize_promotion`) scans `pnl_scan.py` and
  `referee_adjudicate.py` for any `--force`/skip-flag/env-override/default-allow identifier.

## Files Changed

- `apps/backend/app/research/referee_registry.py` -- `REFEREE_DEFAULT_Q`, `REFEREE_STARTER_FAMILY_ID`, S-6 shortlist candidate, `shortlist_response()` family_id/family_q, shared `_signal_matches_hypothesis_cell` helper, `registry_response()`'s optional `bar_store`/`config` params
- `apps/backend/app/research/referee_adjudicate.py` -- `referee_parameters()`/`referee_parameters_hash()`, `_pool_strategy_trades`, `REFEREE_STRATEGY_NULL_DESIGN_CAVEAT`, `run_evaluation_and_record`'s strategy branch + `journal_store`/`certificate_mint` params, `_mint_strategy_certificate`
- `apps/backend/app/research/referee_routes.py` -- `get_referee_registry` now supplies `bar_store`/`config` to `registry_response()`
- `apps/backend/app/research/pnl_scan.py` -- `_dataset_pin`, `_promote`'s `authorize_promotion` wiring + `certificate_store` param, `run_sweep`'s `certificate_store` param, `main()`'s `CertificateStore` construction, promotion block's 3 new fields
- `apps/backend/tests/test_pnl_scan.py` -- certificate/live-scan-context fixture helpers, inverted promotion-path assertions (TC-1), TC-2 (real-rail mint), TC-3..TC-7 (refusal classes), TC-8 (no-bypass guard + counter-test)
- `apps/backend/tests/test_referee_registry.py` -- S-6 shortlist assertions (TC-16), family_id/family_q assertions (TC-17), TC-15 (accrual/discovery context-predicate fix) + a backward-compatibility test for callers omitting `bar_store`/`config`
- `apps/backend/tests/test_referee_adjudicate.py` -- TC-9 (strategy pooling groups by dataset), TC-10 (insufficient_sample + caveats at today's real-corpus shape), TC-11 (playbook checkpoint mints nothing), TC-12 (strategy checkpoint mints exactly one certificate through the real rail), TC-13 (failed attestation gate), TC-14 (referee_parameters stability + monkeypatch counter-test)
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended to `hyp.accrual.*` + its seeded counter-test (TC-18)
- `apps/frontend/lib/types.ts` -- `RefereeShortlistResponse` gains `family_id`/`family_q`
- `apps/frontend/app/desk/page.tsx` -- `handleRegisterRefereeCandidate` reads `family_id`/`family_q` from the fetched shortlist response; the two now-dead local constants (`REFEREE_STARTER_FAMILY_ID`/`REFEREE_STARTER_FAMILY_Q`) removed
- `runs/goal-session-referee/state/assumptions.md` -- two new iter-9 developer entries (the strategy-family hypothesis identity design; the TC-10 "insufficient_sample" interpretation)
- `runs/goal-referee-iter-9/status.json` -- pipeline status

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junit-xml=<path>` (foreground; `pyproject.toml`'s `addopts = "-q"` suppresses the summary line, so verified via junit-xml + exit code per this iteration's own pump note)

Result: **2678 collected, 0 failed, 8 skipped**, exit code 0 (>= the 2,657 floor named in DEFINITION OF DONE).

Per-file breakdown of touched suites (all green):
- `tests/test_pnl_scan.py`: 30 tests, 0 failed (was 21 before this iteration; net +9 — the promotion-path inversion split one test into two [refusal + real-rail-mint promotion] and added TC-3..TC-8's five refusal-class tests plus the zero-certificate honest-completion test plus the no-bypass guard and its counter-test)
- `tests/test_referee_registry.py`: 47 tests, 0 failed
- `tests/test_referee_adjudicate.py`: 54 tests, 0 failed
- `tests/test_desk_ui_guards.py`: 76 tests, 0 failed

`Config().config_fingerprint()` prints `08e471b10130e1e2` (verified both via a direct Python check and as part of the full suite's own fingerprint-pin assertions). MCP tool count unaffected (verified: I did not touch `mcp_server.py` or `test_mcp_server.py`, and the full suite — which includes `test_mcp_server.py`'s own `EXPECTED_TOOLS` assertion — passed).

Frontend: `npx tsc --noEmit -p tsconfig.json` -- clean, exit 0. No frontend test runner exists in this project (`package.json` has no `test` script — matches this project's established convention of TypeScript + backend-side guard-test scans of `.tsx` source + browser QA, never a jest/vitest suite).

**Live verification against the real operator corpus** (not just fixtures): booted a real `uvicorn` instance on an isolated port, curled `GET /research/desk/referee/registry/shortlist` and `GET /research/desk/referee/registry`. The shortlist correctly served all 6 candidates against the real playbook store — `S-6` (`range_trade:short at_wall`) read `n=273, n_sessions=67`, a genuine non-zero, non-vacuous reading — plus `family_id: "referee-starter-family"` and `family_q: 0.1`. The registry route served the honest empty state (`{families: [], hypotheses: [], ...}`). Stopped the verification server by its exact PID afterward (no pattern-based kill, per this iteration's pump note).

## Known Issues

- **Strategy-family hypothesis identity is a T-1 interpretation, not a spec-literal design.** The
  hypothesis record schema requires `setup_id`/`side` uniformly across both evidence families, but
  spec §3.7's strategy-family pooling is dataset-clustered with no natural use for either field,
  and no field on the hypothesis record names which `(strategy_id, profile)` candidate a
  strategy-family hypothesis is about. I chose to pool ALL recorded trades unconditionally
  (ignoring `setup_id`/`side` for this branch) and to have the certificate mint call site accept
  the candidate/champion/dataset identity as an explicit, caller-supplied `certificate_mint` dict
  rather than invent a new hypothesis-record field. Logged in full, with reasoning, to
  `runs/goal-session-referee/state/assumptions.md` (two new "iter-9 — developer" entries). This is
  reversible and touches nothing stored (no real strategy hypothesis exists this era).
- **TC-10's "insufficient_sample" is read as the evaluation record's own `ci_cluster` sentinel
  field**, not a full `adjudications_response()` verdict-vocabulary token — because at today's
  real (tiny) corpus shape, a strategy-family hypothesis's `role` never reaches `"checkpoint"`
  (too few dataset clusters), so the existing `insufficient_sample`-producing branches in the
  read-side fold (both gated on a snapshot existing) are never reached. Wiring a NEW
  strategy-family-specific branch into `_live_fold`/`adjudications_response` was judged out of
  this iteration's IN SCOPE list (which names `referee_adjudicate.py`'s evaluation branch and the
  certificate mint, not the adjudications read-side fold) and was not attempted. Also logged to
  `state/assumptions.md`.
- **`referee_routes.py`'s `/evaluate` route and `RefereeEvaluationComputeManager.trigger()` are
  NOT wired for `journal_store`/`certificate_mint`.** The strategy-family branch is reachable via
  direct `run_evaluation_and_record()` calls (proven by the new tests) and would need this
  additional route-layer wiring before a REAL strategy-family hypothesis could ever be evaluated
  through the `/desk` UI or the `POST /evaluate` route. This is consistent with goal.md's own "no
  strategy certificate can honestly exist this era" and was not in this iteration's IN SCOPE list;
  flagging it explicitly so it is not mistaken for an oversight in a future era that DOES need it.
- **No browser/QA verification performed by this agent** (per the developer role — that is the
  QA/browser-qa-agent's job next). The frontend change is small and low-risk (reads two
  already-typed fields off an already-fetched response instead of two local literals; zero
  rendered-value change per the iter spec's own "no rendered value changes" acceptance), verified
  via `tsc --noEmit` and the backend's own `_PRICE_ARITHMETIC_FIELDS`/copy-discipline scans of the
  live `.tsx` source, plus the live curl verification above confirming the S-6 row and
  family_id/family_q are genuinely served — but no screenshot exists yet. T-9/T-10 (clean rebuild,
  screenshot-or-`unknown`) apply to the QA pass, not this handoff.
- Did not start the Next.js dev server for a full runtime boot (only `tsc --noEmit`) — the change
  is two lines (a type addition, an object-literal-to-field-read swap) with no new component, no
  new render branch, and no UI surface change per the iter spec itself ("UI surface changes: None.
  ... does not change any rendered class, element, or copy"), so a full dev-server boot was judged
  unnecessary beyond the typecheck; QA's own T-9 clean-rebuild pass will exercise it for real.
