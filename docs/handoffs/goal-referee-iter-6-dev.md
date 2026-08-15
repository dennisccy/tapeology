# goal-referee-iter-6 Dev Handoff

**Phase:** goal-referee-iter-6
**Date:** 2026-08-15
**Agent:** developer
**Status:** complete

## What Was Built

**J-05 — the registry: pre-registration with an immutable boundary, full depth
(`docs/referee-statistical-spec.md` Sec5):**

- New `apps/backend/app/research/referee_registry.py` (the era's fourth `referee_*.py` module):
  - Four append-only stores -- `FamilyStore`, `HypothesisStore`, `WithdrawalStore`,
    `CertificateStore` -- all rooted at ONE shared resolved directory
    (`TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR` env var, else a `referee_registry` sibling of the
    universe dir; not a `Config` field), distinguished by filename prefix
    (`family-*.json`/`hypothesis-*.json`/`withdrawal-*.json`/`certificate-*.json`). No
    update/delete method exists on any of the four classes; a duplicate `family_id`/
    `hypothesis_id`/`certificate_id` raises (`FamilyAlreadyRecorded`/`HypothesisAlreadyRecorded`/
    `CertificateAlreadyRecorded`); a corrupted existing file at a key's own deterministic path
    raises `RegistryIntegrityError` rather than being silently overwritten.
  - **Family and hypothesis are registered through ONE act** (`register_hypothesis`), since the
    Data Contract names exactly one POST route and a family's `candidate_hypothesis_ids` must be
    "the COMPLETE planned list, forever" -- decided before any of its hypotheses individually
    register. The first call naming a given `family_id` creates it (from that call's own
    `family_q`/`family_candidate_hypothesis_ids`); every later call naming the SAME `family_id`
    must supply the identical q/candidate list (else refused -- a family's definition can never
    drift) and its own `hypothesis_id` must already be a member of that list ("no candidate joins
    a family retroactively", made structural). `hypothesis_id`/`family_id`/`certificate_id` are
    caller-supplied mnemonic strings (mirroring `family_id`'s own established shape), not derived
    hashes -- there is no "same content should dedupe" requirement anywhere in the spec, unlike
    `RefereeNullStore`'s identity.
  - **Validation, each refusal distinct, nothing written on any refusal**: missing/empty required
    field, out-of-vocabulary `evidence_family`/`estimand`/`side`/`sidedness`
    (`HypothesisMalformed`); `target_sessions < REFEREE_MIN_SESSIONS` (12) or
    `min_occurrences < REFEREE_MIN_OCCURRENCES` (12) -- both new module constants, first defined
    here per spec Sec1 (the `REFEREE_NULL_ANCHORS_PER_OCCURRENCE`-in-`referee_null.py` precedent:
    a constant lives in the first module that needs it); an Estimand-C (or B)
    `context_predicate` whose `backing_bucket` is not in the fixed vocabulary
    (`PLAYBOOK_CONTEXT_BACKING_BUCKETS`, read TRANSITIVELY through `referee_null.py` -- this
    module never imports `desk_playbook_context` directly, never calls `BandMapResolver`; the
    Build Notes' own ruling that this is a structural vocabulary check, not a live resolve,
    since a hypothesis registers against a setup+side abstractly with no concrete symbol/session
    yet to resolve against); an unrecognised `null_spec_id`/`test_spec_id` (`UnknownSpecId`) --
    `null_spec_id` is required (and validated) only for a playbook-family hypothesis whose
    estimand is A or C (Estimand B is a cell-vs-complement comparison with NO null population at
    all per spec Sec3.2 and spec Sec7's own S-4 table row, which names no null unlike
    S-1/S-2/S-3/S-5 -- a `null_spec_id` supplied for a B hypothesis is ignored, mirroring how
    `context_predicate` is scoped to B/C only); an explicit `confirmation_start_boundary` at or
    before the honest computed value (`RetroactiveBoundary`, TC-4 -- the boundary is ALWAYS
    exactly the ET calendar date of `registered_at`, spec Sec5's own definitional equality; the
    payload's override field exists only to catch a defensive/adversarial attempt to set it
    earlier-or-equal, never to let a caller actually choose it); a missing/unconfirmed act
    (`ConfirmationRequired` -- **no write of ANY kind, family or hypothesis, happens before
    `confirm is True`**, gating both writes together, not just the hypothesis one).
  - `detector_basis` (playbook family: `current_playbook_detector_basis()`, server-computed) and
    `context_algorithm_version` (B/C: `PLAYBOOK_CONTEXT_ALGORITHM_VERSION`) are server-determined,
    never caller-supplied. `origin` is always stamped `"historical-exploration"`.
  - **Withdrawal** (`withdraw_hypothesis`): refuses on an unknown `hypothesis_id`, on the injected
    `post_boundary_evaluation_exists=True` signal (no evaluation store exists until J-06 --
    default `False`, the honest answer for every real hypothesis today), or on an
    already-withdrawn hypothesis (`WithdrawalRefused` in all three cases); an accepted withdrawal
    appends exactly one WITHDRAWAL record, keyed by `hypothesis_id` (structurally one-per-hypothesis
    -- a second attempt collides on the same deterministic path).
  - **Accrual fold** (`registry_response` / `_hypothesis_accrual`): the disclosed readiness PROXY
    ratified in `state/assumptions.md` -- distinct post-boundary `session_date`s carrying >=1
    observation in the hypothesis's own `(setup_id, side)` cell, computed with the SAME shared
    pooling primitives `referee_evidence.playbook_occurrence_readiness()` is built from
    (`_newest_per_session_date`, `_is_stale_basis`, `current_playbook_detector_basis`, all
    imported, never reimplemented) -- ONE `PlaybookStore.list()` scan per `GET` call, shared
    across every hypothesis folded, never a second scan per hypothesis. Serves `is_proxy: true`
    and `basis_current: bool` (whether the hypothesis's own pinned `detector_basis` still matches
    the corpus's live value).
  - `registry_response()` serves the pinned four-key shape verbatim:
    `{families, hypotheses (each + status + accrual), withdrawals, certificates}` -- no 5th key,
    matching `state/blueprint.md`'s iter-6 note exactly.
  - CLI (`argparse` subparsers `register`/`withdraw`, `main()`) -- running the command IS the
    explicit act for `register` (`confirm=True` always; unlike the POST route, a CLI invocation
    has no automated/accidental-call surface to guard against).
- Extended `apps/backend/app/research/referee_routes.py`: `GET /research/desk/referee/registry`
  (dependency providers for all four stores + the existing playbook-store provider) and
  `POST /research/desk/referee/registry/hypotheses` (a fully-optional Pydantic body so
  `register_hypothesis` itself is the ONE place every validation class is decided -- 422 on
  `HypothesisMalformed`/`UnknownSpecId`/`RetroactiveBoundary`/`ConfirmationRequired`, 409 on
  `FamilyAlreadyRecorded`/`HypothesisAlreadyRecorded`). `GET /evidence` and every `/nulls*` route
  (J-01/J-04) are byte-unchanged except the one rider below.

**Rider 1 (`referee_null.py`, `build_null_record`):** `backing_bucket_eligibility_rate` now
serves `None` whenever `map_result is None` **or** `tod_eligible_count == 0` (previously only the
`map_result is None` half was special-cased; a resolved map with zero ToD-eligible candidates
wrongly served `0.0`, implying a measured 0% match over a real population when nothing was ever
checked at all). The genuine `len(matched) / tod_eligible_count == 0.0` case (real candidates
checked, zero matched) is unchanged. One-line fix inside the already-registered `float|None`
field.

**Rider 2 (`test_referee_null.py`):** a `>REFEREE_NULL_ANCHORS_PER_OCCURRENCE`-eligible (7
candidates, K=4) fixture that finally discriminates the seeded Fisher-Yates subset draw (every
prior fixture had `eligible_count <= 4`, where "draw all of them" is correct regardless of
whether the selector's randomization actually works) -- two builds over the identical observation
return the identical subset; an independent re-derivation (TC-1's own methodology) matches
byte-for-byte and is proven non-trivial (not merely "the first 4 in order"); a different
observation draws a different subset. Plus a hand-computed `window_overlap_fraction` assertion
(three cases: full mid-overlap, no overlap, left-edge partial overlap) and two tests proving
Rider 1's fix (the `None`-not-`0.0` case, plus a can-fail counter-test that a genuine zero-match
rate over a real checked population still correctly serves `0.0`).

**The import-topology guard extension (`tests/test_referee_guards.py`):** the existing glob-based
guards (`test_no_referee_module_imports_the_detect_module` /
`test_no_referee_module_other_than_referee_null_imports_the_context_module`) already cover
`referee_registry.py` automatically (they iterate every `referee_*.py` module on disk) -- no
existing assertion needed editing. Added one explicit, file-named test
(`test_referee_registry_module_imports_neither_the_detect_nor_the_context_module`) plus its
can-fail counter-test, making that coverage undeniable to a reviewer rather than leaving it
merely implicit in a glob. `referee_registry.py` reads `PLAYBOOK_CONTEXT_BACKING_BUCKETS` /
`PLAYBOOK_CONTEXT_ALGORITHM_VERSION` TRANSITIVELY through `referee_null.py` (the one module the
guard already exempts) -- it never imports `desk_playbook_context` itself and never touches
`BandMapResolver`.

## Files Changed

- `apps/backend/app/research/referee_registry.py` -- NEW. Four append-only stores, the
  registration act, the withdrawal act, the accrual fold, `registry_response()`, the CLI.
- `apps/backend/app/research/referee_routes.py` -- added `GET /registry` and
  `POST /registry/hypotheses`, their dependency providers, and the request Pydantic model.
  `GET /evidence` and every `/nulls*` route are byte-unchanged.
- `apps/backend/app/research/referee_null.py` -- Rider 1: the one-line
  `backing_bucket_eligibility_rate` fix in `build_null_record` (plus an explanatory comment). No
  other line changed.
- `apps/backend/tests/test_referee_registry.py` -- NEW. 32 tests: TC-1 through TC-14 (each with
  at least one refusal-class test verifying zero record written), store-discipline (no
  update/delete method on any of the four classes), the family/hypothesis coupling rules
  (consistency-on-reuse, "no candidate joins retroactively", duplicate refusal), the confirm gate
  (including that it blocks the FAMILY write too, not just the hypothesis one), route-level tests
  (`GET`/`POST`, 422/409 refusal shapes), and CLI tests (`register`/`withdraw` subcommands,
  argparse's own required-flag rejection).
- `apps/backend/tests/test_referee_null.py` -- Rider 2: 5 new tests (2 for Rider 1's fix, 2 for
  the discriminating seeded-draw fixture, 1 for the hand-computed `window_overlap_fraction`).
- `apps/backend/tests/test_referee_guards.py` -- 2 new tests (the explicit `referee_registry.py`
  import-ban check + its can-fail counter-test).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junit-xml=<path> -q`
(`pyproject.toml`'s `addopts = "-q"` means CLI `-q` becomes `-qq`, printing no "N passed" summary
line -- verified via the JUnit XML instead, this project's own established practice.)

Result: **2592 collected, 2584 passed, 8 skipped, 0 failed, 0 errors** (~249s). Exceeds the
iteration-5 floor (2553 collected / 2545 passed / 8 skipped) by exactly **+39** -- 32 new tests in
`test_referee_registry.py` + 5 new tests in `test_referee_null.py` + 2 new tests in
`test_referee_guards.py` = 39, confirming no stray/uncounted collection.

Targeted re-runs, all green:
- `tests/test_referee_registry.py` (32 tests, new) -- confirmed independently before the full run.
- `tests/test_referee_null.py` + `tests/test_referee_guards.py` + `tests/test_referee_evidence.py`
  + `tests/test_referee_stats.py` + `tests/test_referee_oracles.py` together (134 tests, 0
  failed) -- the J-01/J-02/J-03/J-04 required-still-passing regression check.

`Config().config_fingerprint()` verified live: still `08e471b10130e1e2`.
`tests.test_mcp_server.EXPECTED_TOOLS` verified live: still exactly 20 names, unchanged.

`git status --porcelain` confirms the diff is scoped to exactly the 6 files above (plus this
handoff and `status.json`) -- zero diff to `desk_forward.py`, `desk_playbook.py`,
`desk_playbook_context.py`, `levels.py`, `tradability.py`, `setups.py`, `edge_report*.py`,
`backtests.py`, `pnl_scan.py`, `referee_evidence.py`, `referee_stats.py`, `app/config.py`,
`app/main.py`, or `docs/referee-statistical-spec.md`. Zero new `Config` field (both new
constants -- `REFEREE_MIN_SESSIONS`/`REFEREE_MIN_OCCURRENCES` -- are plain module constants in
`referee_registry.py`, read at call time). No new MCP tool.

**Service startup verified** (`scripts/start-backend.sh`, deterministic port 8301 -- Frontend
Present: no this iteration, so only the backend was started, matching this iteration's own
scope): started cleanly; `GET /research/desk/referee/registry` against the REAL corpus served the
honest empty state (`{"families": [], "hypotheses": [], "withdrawals": [], "certificates": []}`);
`GET /research/desk/referee/evidence` (existing, unmodified) served the same real-corpus numbers
as every prior iteration (210 records / 156 sessions / 3222 signals, fingerprint
`08e471b10130e1e2`); `POST /research/desk/referee/registry/hypotheses` without `confirm` correctly
422'd. Stopped by exact PID (`lsof -ti :8301`, never a pattern-based
`pkill`, per the host protection rule -- an earlier iteration's `pkill` hit an unrelated project
sharing this host); restarted a second time with **no port conflicts** (ready in 2s, `GET
/registry` 200 immediately); stopped again by exact PID, port confirmed free both times. No real
registration was ever run against the production `.data/` store (deliberately -- a real
registration is an explicit J-07 operator act, out of scope this iteration; verified via
`find .data -iname "*referee_registry*"` returning nothing both before and after this dev pass).
No live external-integration test was needed (no adapter/scraper/API code added -- this module is
a pure read/write library over its own newly-created stores plus read-only imports).

## Known Issues

- **Hitting the pre-existing (byte-unchanged this iteration) `GET /research/desk/referee/evidence`
  route live touched `dataset_index.db-wal`/`dataset_index.db-shm`** (SQLite's own WAL-mode
  sidecar files, auto-created the moment any connection opens against the dataset accelerator
  index that route already depends on via `get_dataset_store`) -- both sidecars checkpointed to
  0 bytes (zero pending writes), and zero `.json` record file anywhere under `.data/` was created
  or modified (verified via `find -newer`). This is pre-existing behavior of an unmodified route
  (iter-5's own handoff hit this identical endpoint live too), not something this iteration's
  code introduced -- flagged here only for full transparency ahead of any byte-identity
  cross-check.
- **`null_spec_id` is required-and-validated only for Estimand A/C, forced to `None` for Estimand
  B** -- a genuine interpretation call (spec Sec3.2 describes B as a cell-vs-complement
  comparison with no null population, and spec Sec7's own S-4 table row names no null unlike
  S-1/S-2/S-3/S-5, unlike the more literal read of the Data Contract note "`null_spec_id: str|None`
  (None for `evidence_family='strategy'`)" taken in isolation, which would suggest playbook+B
  should still require one). I judged the spec's substantive estimand definitions (Sec3.2/Sec7)
  as the more authoritative source than the Data Contract summary's parenthetical, which only
  explains the strategy case and does not claim to be exhaustive. Reversible, zero downstream
  consumer yet (J-06 is the first real reader of this field). Not logged in
  `state/assumptions.md` (outside this dev pass's write scope) -- flagged here for reviewer/
  auditor visibility instead.
- **`confirmation_start_boundary`'s override field is a defensive/test hook, not a documented
  caller feature** -- a payload supplying a value strictly AFTER the honestly-computed boundary
  is silently ignored (the stored value is always exactly `et_date(registered_at)`), since spec
  Sec5 states a definitional equality with no "later boundary" feature named anywhere; only TC-4's
  own "at or before" refusal case is spec-mandated behavior, the "silently ignore a later value"
  half is my own conservative completion of an otherwise-unspecified corner.
- **The registration payload accepts (and a caller could in principle send) a raw
  `context_predicate` for Estimand A**, which is silently ignored (forced to `None`) rather than
  refused -- spec names no refusal for this case, and refusing would be inventing a validation
  rule the tests do not ask for.
- **J-10's browser regression sentinel (the full kept-product browser walk with fresh
  screenshots) was NOT performed in this dev pass** -- matching every prior
  `goal-referee-iter-*` dev handoff's own precedent; J-05 itself carries no browser acceptance
  ("Keyless; automated" per its own goal.md tag) and no frontend file changed this iteration (no
  frontend handoff written, matching `Frontend Present: no`).
- **The certificate store is genuinely unreachable from any route or CLI path this iteration**
  (by design -- J-08's job): `CertificateStore` exists and is append-only-tested (TC-12) via
  direct fixture seeding only, exactly as the iteration spec's own NOTES describe.
