# goal-rapid-microscope-iter-15 Dev Handoff

**Phase:** goal-rapid-microscope-iter-15
**Date:** 2026-08-19
**Agent:** developer
**Status:** complete

## What Was Built

Five pieces, all inside J-08/J-07's already-shipped homes (the evaluator-mandated second half of
iteration 14's split ESCALATE):

- **Four new read-only MCP tools** (`apps/backend/app/mcp/__init__.py`) — `desk_micro_readiness` →
  `GET /research/desk/micro/readiness`, `desk_scout` → `GET /research/desk/micro/scout`,
  `desk_walkforward` → `GET /research/desk/micro/walkforward`, `desk_vault` →
  `GET /research/desk/micro/vault` — inserted into both `_STATIC_PATHS` and the `TOOLS` tuple
  immediately after `desk_referee_registry` and before `pnl_ledger`, mirroring the existing
  no-required-param proxy shape exactly (`inputSchema=_object_schema({})`). Zero new HTTP verb,
  zero new dependency, zero change to `_request_path`'s dispatch shape. Module docstring's
  shipped-endpoint list updated in the same commit. MCP contract moves **v5 (22 tools) → v6 (26
  tools)**.
- **`EXPECTED_TOOLS` 22→26** (`apps/backend/tests/test_mcp_server.py`) — the ordered tuple, four
  names inserted at the correct position, in the same commit as the tool additions. Added
  honest-empty-state AND directly-seeded-populated-state byte-identity tests for each of the four
  new tools (mirroring the `desk_referee`/`desk_referee_registry` precedent), seeded via each
  ledger's own public write function (`ScoutLedger.append_row`, `walkforward_ledger.
  append_fold_result`, `vault.register_universe`/`vault.seal_shard`) — never a live compute run.
  Placed BEFORE `test_datasets_tool_byte_identical_on_a_non_empty_live_list` (the module's first
  dataset-writing test) so every honest-empty assertion is genuinely observed on a corpus with zero
  datasets and zero vault universes.
- **The MCP-surface TR-2 inference sweep** (new test,
  `test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard`) — reuses `test_vault.py`'s own
  TR-2 fixture rig (`_combined_fixture_store`, `_record_distinctive_dataset`, `_scope_everything_to`,
  `_scalars`, imported directly rather than reimplemented, matching this codebase's established
  cross-test-file-import precedent). Seals one globally-distinctive shard under an unregistered
  universe id (the `test_vault.py` precedent for "not yet whole-pool released"), spawns a
  DEDICATED, freshly-hermetic backend subprocess over that exact store (never the shared
  module-scoped `backend` fixture, whose dataset dir accumulates many other tests' recordings), and
  calls all 26 MCP tools against it. Asserts the sealed shard's raw dataset id, raw checksum,
  symbol, window bounds, and exact trade/quote counts appear in ZERO tool response bodies, then
  counter-tests that the sweep is non-vacuous (the sealed shard genuinely IS withheld; the two
  public PG siblings are still fully served).
- **Microscope Readiness coherence fix** — `apps/frontend/lib/types.ts` `MicroReadinessResponse`
  gains `joinable_corpus` and `sealed_tranche` (both already served by unchanged
  `micro_readiness.py`, transcribed verbatim from `build_readiness`'s own return statement).
  `MicroReadinessSection` (`page.tsx`) renders a new "Sealed Tranche (Aggregate Only)" block —
  `sealed_tranche.shard_count`/`.symbol_days`, a per-universe breakdown
  (`universe_id → {shard_count, symbol_days}`), and `joinable_corpus.withheld_excluded` — all
  AGGREGATE-ONLY, no symbol/date/dataset-id/checksum/per-shard `exposure_state` anywhere in the new
  markup. `joinable_corpus.total`/`playbook_signal_count`/`band_touch_count`/`by_setup_id` stay
  typed/fetched but unrendered this iteration (matches `state/assumptions.md`'s iter-15 entry).
- **Three minor fixes**: Scout family header now renders `family.family_root_id` beside
  `family.family_id`; Walk-Forward's empty-sequences title changed from the reused Scout copy "No
  candidates ledgered." to "No walk-forward sequences run."; `ValidationVaultSection`'s two early
  returns (loading, unavailable) now wrap their content in `data-testid="validation-vault-section"`,
  matching the success path (previously only the success path carried the testid).
- **The Walk-Forward HTML-nesting fix** — the sequence-verdict block's outer element changed from
  `<p>` to `<div>` so the `<details>`/`<pre>` block-level pair it wraps is legally nested (a `<p>`
  may only contain phrasing/inline content; both `<details>` and `<pre>` are block-level). A
  whole-file scan (Python regex over every `<p ...>...</p>` span) confirms this was the only site in
  the 12,000-line page containing `<details`, `<pre`, `<table`, or `<div` inside a `<p>`.
- **`_PRICE_ARITHMETIC_FIELDS` extension** (`apps/backend/tests/test_desk_ui_guards.py`) — added
  the two newly-rendered readiness numerics (`readiness.sealed_tranche.(shard_count|symbol_days)`,
  `universeCounts.(shard_count|symbol_days)` for the per-universe breakdown's destructured binding,
  `readiness.joinable_corpus.withheld_excluded`) to the client-side-arithmetic-ban allow-list.
- **J-07 genuine re-verification**: `tests/test_micro_graduation.py` re-ran fresh this iteration
  (19 tests, all pass — see Tests Run). Live-navigated the browser directly to
  `http://localhost:8301/research/desk/micro/graduation` (the backend port, store-scoped rig) and
  captured a screenshot showing HTTP 200 with the honest-empty stage-vocabulary body:
  `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,
  "failed_at_row":null,"reason":null}}`. This route deliberately has no golden replay script
  (`micro_routes.py`'s own docstring: `demo_runner.normalize_url()` forcibly rewrites any localhost
  URL onto the frontend base, so a backend-origin navigation cannot be expressed in the replay
  schema) — this direct-navigation check is the correct, permanent verification path, disclosed at
  `runs/goal-session-rapid-microscope/state/golden-gaps`. Screenshot on disk at
  `/home/dennis-chan/.cache/superpowers/browser/2026-08-14/session-1786713900809/727-navigate.png`
  (also `727-navigate.md` for the raw JSON text). This is a genuine re-verification, not a third
  `DEFERRED-BUDGET`.

## Files Changed

- `apps/backend/app/mcp/__init__.py` — 4 new `_STATIC_PATHS` entries + 4 new `types.Tool` entries
  (desk_micro_readiness/desk_scout/desk_walkforward/desk_vault), inserted after
  `desk_referee_registry` and before `pnl_ledger`; module docstring's shipped-endpoint list updated.
- `apps/backend/tests/test_mcp_server.py` — `EXPECTED_TOOLS` 22→26; `backend_paths` fixture gains
  3 new env-scoped temp dirs (`TAPEOLOGY_MICRO_SCOUT_DIR`/`_WALKFORWARD_DIR`/`_VAULT_DIR`); new
  imports (`scout_ledger.ScoutLedger`, `vault`, `walkforward as wf`, `walkforward_ledger as wl`,
  plus `test_vault`'s TR-2 rig helpers); 9 new tests (4 tools × empty+populated, minus one — 8
  empty/populated pairs + 1 TR-2 sweep = 9); two pre-existing `len(TOOL_NAMES) == 22` assertions
  updated to `== 26`.
- `apps/backend/tests/test_desk_ui_guards.py` — `_PRICE_ARITHMETIC_FIELDS` widened for the two new
  readiness numerics.
- `apps/frontend/lib/types.ts` — `MicroReadinessResponse` gains `joinable_corpus`
  (`MicroReadinessJoinableCorpus`) and `sealed_tranche` (`MicroReadinessSealedTranche`), both new
  named interfaces, shapes transcribed verbatim from the backend.
- `apps/frontend/app/desk/page.tsx` — `MicroReadinessSection` renders the new Sealed Tranche
  aggregate block; Scout family header renders `family_root_id`; Walk-Forward empty-state copy
  fixed; Walk-Forward sequence-verdict block's outer `<p>` changed to `<div>`; `ValidationVaultSection`'s
  loading/unavailable early returns wrapped in the `validation-vault-section` testid.

No change to `micro_readiness.py`, `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`,
`walkforward_ledger.py`, `micro_routes.py`, any `referee_*.py`, `micro_chain_ledger.py`,
`micro_observer.py`, `micro_features.py`, `micro_graduation.py`, Playbook detectors, `Config`, or
`docs/rapid-validation-spec.md` — confirmed via `git status`/`git diff` (only the 5 files above show
as modified) and via SHA-256 re-check (below).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junitxml=<path>`

- `tests/test_mcp_server.py` (targeted): **61 passed**, 0 failed, 8.79s.
- Related-module targeted batch (`test_vault.py`, `test_desk_ui_guards.py`, `test_scout.py`,
  `test_scout_ledger.py`, `test_walkforward.py`, `test_walkforward_oracles.py`,
  `test_micro_readiness.py`, `test_micro_graduation.py`, `test_micro_join.py`,
  `test_micro_accessor.py`): **410 passed**, 0 failed, 201.47s.
- **Full backend suite (authoritative, read from `--junitxml`, not the redirected stdout stream
  per this session's own known pytest-version gotcha)**: `<testsuite tests="3237" errors="0"
  failures="0" skipped="8" .../>` → **3237 collected / 3229 passed / 8 skipped / 0 failed**,
  623.6s. Baseline (era-open, iteration 0): 2691 pass / 8 skip. Carried-context baseline for this
  round: 3228 collected / 3220 passed / 8 skipped / 0 failed. Delta: **+9 collected / +9 passed /
  same skip count / 0 failed** — exactly the 9 tests this iteration adds to
  `test_mcp_server.py` (4 empty-state + 4 populated-state + 1 TR-2 sweep), nothing removed,
  nothing newly failing. Meets TC-14's `≥ 3228 collected, 0 failures` floor.
- **Fresh, direct, live byte-identity re-proof (independent of the pytest suite, executed as part
  of this handoff's own verification, not merely cited)**: spun up an isolated, throwaway backend
  on a scratch port with fresh empty stores, then called `app.mcp.call_tool` for each of the four
  new tools and diffed the raw response bytes against a direct `httpx.get` on the same path:
  - `TOOL_NAMES` length = 26; order at the insertion point = `('desk_referee', 'desk_referee_registry',
    'desk_micro_readiness', 'desk_scout', 'desk_walkforward', 'desk_vault', 'pnl_ledger')` —
    confirms the four new tools sit immediately after `desk_referee_registry` and immediately
    before `pnl_ledger`, in both `_STATIC_PATHS` and `TOOLS`.
  - `desk_micro_readiness`: REST 200, tool `isError=False`, **byte_identical=True** (882 bytes,
    honest-empty shape).
  - `desk_scout`: REST 200, tool `isError=False`, **byte_identical=True** (83 bytes,
    `{"families":[],"chain_verification":{"ok":true,...}}`).
  - `desk_walkforward`: REST 200, tool `isError=False`, **byte_identical=True** (100 bytes).
  - `desk_vault`: REST 200, tool `isError=False`, **byte_identical=True** (193 bytes).
  - Re-ran `desk_micro_readiness` after recording one real dataset through the live backend's own
    `POST /research/datasets` (populated state, `shards` now non-empty, 1 row) — still
    **byte_identical=True**.
  - Scratch backend and its throwaway stores torn down immediately after (process killed, temp
    dir removed) — nothing touched the real `.data` store.
- Frontend: `npx tsc --noEmit` (apps/frontend) — **0 errors**, including every
  `MicroReadinessResponse` construction/read site.
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged, matches the era pin).
- SHA-256 re-check, six `referee_*.py` + `micro_chain_ledger.py`, all byte-identical to the
  iteration-0 baseline (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md`) and to `git diff`
  (zero changes reported for all seven files):
  ```
  6dd807b5ab69af033686a395484b1b10515d0f453a79c0943e534a578259786c  referee_adjudicate.py
  482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5  referee_evidence.py
  34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603  referee_null.py
  03840c863b1e1f382ad2588d3bb6d8dc0e36a70582c3cb7a716638dabef32d99  referee_registry.py
  0cc3a06f7b382c63d544886ec74a47f2414612fc77dd3dac444b00cc35216140  referee_routes.py
  fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c  referee_stats.py
  c8e86991ba229dadad4b76342bd97c5ead1fe62d6373e5db94fdf053ccaebaff  micro_chain_ledger.py
  ```
  `git diff --stat` re-run a second time (after all other verification steps, to catch any
  accidental late edit) over these 7 files PLUS `vault.py`/`scout.py`/`walkforward.py`/
  `micro_routes.py`/`config.py` (the carried-context "should stay untouched" list) reports **zero
  changes across all 12 files**.

## Pre-handoff verification

- **Service startup**: `scripts/dev.sh` (backend `:8301`, frontend `:3301`) — clean start, both
  ports came up, `GET /health` → 200. Ran the browser pass against this rig (below), then killed
  both server processes via `lsof`/`fuser` on both ports and confirmed both fully released.
- **External integrations**: none added this iteration — the four new tools are thin GET proxies
  over already-shipped, already-tested internal endpoints; no new adapter/vendor call.
- **Native dependency binaries**: none added.
- **Live browser verification** (Chrome attached at `127.0.0.1:9222`, per this session's carried
  context — not self-launched): navigated to `/desk`, enabled console logging, and expanded each of
  the four Rapid-Microscope sections in turn, checking console messages after each expansion
  (CARRIED CONTEXT's own directive — "verify by execution rather than inspection"):
  - **Microscope Readiness**: expanded cleanly, zero console errors. The new "Sealed Tranche
    (Aggregate Only)" block renders against the REAL `.data` store's genuinely all-zero state —
    `Sealed shard count: 0`, `Sealed symbol-days: 0`, `Joinable corpus — withheld (excluded): 0`,
    and the per-universe breakdown correctly shows "No sealed shards recorded." (confirmed via raw
    HTML inspection of the rendered `data-testid` values, not merely "something rendered").
  - **Scout Ledger**: expanded cleanly, zero console errors. Real store is genuinely empty
    ("No candidates ledgered."), so `family_root_id` rendering was NOT visually exercised live
    (see Known Issues) — but is type-checked (`tsc --noEmit` clean against `ScoutFamily.
    family_root_id: string`) and covered by the backend contract test proving the field is served.
  - **Walk-Forward**: expanded cleanly, zero console errors. The REAL `.data` store already carries
    one genuine diagnostic walk-forward sequence (`seq-d39d20e47af24671`, from the era's own
    155-session diagnostic run, spec `playbook_setups_diagnostic_v1`) — so this section rendered
    NON-TRIVIAL real data, not an empty stub. Clicked the sequence's own "detail" `<details>`
    toggle (the EXACT TC-7 interaction) and re-checked the console: **zero new messages** — only
    the unrelated, harmless React DevTools notice persisted from page load. This is a direct, live
    proof of the HTML-nesting fix on real data, not merely a static source-scan.
  - **Validation Vault**: expanded cleanly, zero console errors. Directly observed
    `data-testid="validation-vault-section"` wrapping BOTH the `validation-vault-loading` state
    (captured mid-fetch) AND the settled, populated (but honestly empty — "No shards recorded." /
    "No universes registered.") state — confirming TC-10 live, in both states, not merely by source
    inspection.
  - **J-07** (`GET /research/desk/micro/graduation`, backend port `:8301`): navigated directly,
    confirmed HTTP 200 with the honest-empty stage-vocabulary body; screenshot on disk (path above).
  - Full backend/frontend test suites (above) are the authoritative regression evidence; this
    browser pass is a targeted, execution-based spot-check of exactly the fault class this round's
    auditor mandate names (hydration errors only visible after interaction, opaque-pool disclosure
    surfaces), not a substitute for the QA/browser-qa lane's own full J-01–J-05/J-10 regression
    sweep and TC-5/TC-6 non-zero-fixture pass (still pending downstream — see Known Issues).
- **Real-store hygiene**: no write path was exercised against the real `.data` store at any point —
  every populated-state proof in this iteration's tests runs against a `tmp_path`-scoped fixture
  store or the module-scoped MCP test backend's own env-scoped temp dirs (`backend_paths`), never
  the operator's real dataset/vault/scout/walkforward directories. The live browser pass above was
  read-only (section expansions + one `<details>` click); no "Run Screen"/"Run Walk-Forward" button
  was ever clicked, per the era's own performance trap.

## Known Issues

- **TC-5's non-zero fixture-rendering pass and TC-8's live `family_root_id` render are not
  independently browser-verified this dev pass.** The real `.data` store's Microscope Readiness
  state is genuinely all-zero (verified live, see above) and its Scout ledger is genuinely empty —
  so this pass could only browser-confirm the ALL-ZERO/EMPTY rendering paths, never the non-zero
  ones. Both non-zero shapes ARE proven correct by other means: `tsc --noEmit` type-checks every
  field access against the real backend-transcribed interfaces with zero errors, and the backend
  contract tests (`test_desk_micro_readiness_tool_byte_identical_on_a_populated_state`,
  `test_desk_scout_tool_byte_identical_on_a_populated_state`) prove the SERVED JSON shape is
  correct and non-empty. What remains unexercised is specifically the REACT RENDER of a non-zero
  `sealed_tranche`/`by_universe` and a `family_root_id` differing from `family_id`, over a live DOM.
  Per the phase spec's own Testing Requirements ("TC-5 must also be exercised against a non-zero
  fixture state... so the rendering path is proven, not merely inert"), this is squarely the
  QA/browser-qa lane's job against a seeded fixture-scoped rig, not reproduced here.
- **J-01–J-05 and J-10's full replay/browser-QA regression sweep (TC-13) was not independently
  re-run this dev pass.** My changes are narrowly scoped (5 files, all inside the already-shipped
  J-08 sections/MCP module) and the full backend suite (which those journeys' backend contracts
  depend on) passes at the reported count with 0 failures — but the PHASE SPEC's own Testing
  Requirements name this as the QA/browser-qa lane's explicit job ("full regression sweep of
  J-01–J-05 and J-10 via the store-scoped rig, with every cited evidence path confirmed to exist on
  disk"), which is the next pipeline step, not this one.
- **The Walk-Forward "Run Walk-Forward"/Scout "Run Screen" compute buttons were never clicked**
  (the era's own performance trap: a live Scout screen against the real corpus has previously run
  past 25 minutes without completing one candidate). All populated-state proof in this iteration
  seeds directly through each ledger's own public write function, exactly as the phase spec
  requires.
- Everything else in the phase spec's IN SCOPE / DEFINITION OF DONE list is implemented as
  specified, with backend contract tests and (where the real store's own current state permitted)
  live browser confirmation for each item.
