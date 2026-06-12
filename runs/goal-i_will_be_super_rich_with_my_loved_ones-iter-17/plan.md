# goal-i_will_be_super_rich_with_my_loved_ones-iter-17 Execution Plan

Capability-34 engine performance gate — the session's first engine touch. Byte-identity-pinned,
backend-only, no journey flips by design (J-62 advances on its engine-gate clause only).

## What to Build

- **Truly incremental refresh-score maintenance** in `apps/backend/app/engine/features.py::_Window`:
  remove the permanent post-eviction degradation (`self._refresh_incremental = False` set in
  `_evict()` at ~lines 178 and 203, after which `compute()` line ~243 serves the O(window)
  `_refresh_fractions()` forward-merge on EVERY event — quadratic on any stream longer than a
  feature window). On the engine path (trades carrying `eff_bid`/`eff_ask`), maintain
  `bid_refresh_score`/`ask_refresh_score` with amortized O(1) (worst O(log n)) work per event
  INCLUDING across trade and quote evictions. Algorithm is the developer's choice (e.g. a
  two-stack / monotonic sliding-window-aggregation structure).
- **Byte-identity trap (non-negotiable, reviewer must verify):** the oracle is today's
  post-eviction semantics = `_refresh_fractions()` — in-effect quotes computed from **in-window
  quotes only**. An in-window trade older than the oldest surviving quote has NO in-effect quote
  and is SKIPPED (contributes no refresh evidence). This genuinely diverges from the append-time
  `eff_*` semantics once quotes evict — the new structure must reproduce the ORACLE, not the
  append-time values. If byte-identity proves unachievable incrementally: STOP and flag — the
  "re-pin as its own iteration" escape is explicitly NOT taken this iteration.
- **`_refresh_fractions()` is retained** as (a) the authoritative path for the standalone
  `FeatureEngine` API (no `eff_*` threaded — behavior unchanged, documented) and (b) the test oracle.
- **Committed ≈10-minute real SIP fixture** in `apps/backend/tests/fixtures/alpaca/` via the
  existing bounded/chunked adapter (SIP feed, NEVER IEX; credentials at dev time only — if
  genuinely unavailable, STOP and flag, never substitute synthetic data). Window comfortably
  > 300 s so all five feature windows evict; moderate density, target well under ~25 MB;
  provenance (symbol, exact UTC window, feed, fetch date) documented in the fixture/test
  docstring. This same fixture is capability 32's reference-study input next iteration.
- **CI timing gate:** unpaced replay of the fixture through a fresh full `TapeEngine` (the
  `test_real_data_classify.py` pattern — `HistoricalProvider` + `TapeEngine`, no credentials)
  asserting wall-time < a config-owned budget with documented headroom (≥5× measured dev-machine
  time).
- **Config key** `dense_replay_time_budget_seconds` in `app/config.py`, **excluded from
  `config_fingerprint`** with the full iter-12/iter-16 discipline: documented rationale comment
  (a CI gate value never enters persisted computation), a fingerprint-stability test, and the
  counter-test (a real classifier threshold still moves the fingerprint).
- **Additive iter-17 build-out note** appended to
  `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` (no skeleton
  change, no reapproval) registering the fixture + budget key as test/CI assets.
- **Dev handoff** at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-17-dev.md`.

## Agents Required

- developer: yes -- backend-only: the incremental `_Window` refresh structure, the SIP fixture
  fetch + commit, the new test matrix (timing gate, structural no-rescan counter, oracle
  equivalence, pinned anchors, fingerprint stability/counter pair), the config key, the blueprint
  note, the handoff.
- backend-data: yes (the above — all work is backend/engine/tests).
- frontend-ux: no -- ZERO frontend file changes permitted (reviewer verifies the diff file list:
  no store.py, no schema, no classifier.py, no providers, no frontend files).

## Frontend Present

Frontend Present: yes

(Per the spec: "yes" exists SOLELY to force browser QA to run the J-68 byte-identity regression
sentinel + J-08 REST==UI spot check after the engine change. No frontend code changes.)

## Files to Create/Modify

- `apps/backend/app/engine/features.py` -- replace the permanent post-eviction merge fallback in
  `_Window` with incremental maintenance byte-identical to the `_refresh_fractions()` oracle;
  keep `_refresh_fractions()` for the standalone-API path and as oracle.
- `apps/backend/app/config.py` -- add `dense_replay_time_budget_seconds` + fingerprint-exclusion
  rationale comment + exclusion-set entry (iter-16 pattern).
- `apps/backend/tests/fixtures/alpaca/<SYMBOL>_<window>_sip.json` -- NEW committed ≈10-min real
  SIP trades+quotes fixture with documented provenance (<~25 MB).
- `apps/backend/tests/test_dense_replay_gate.py` (or similarly named NEW file) -- CI timing gate,
  structural no-rescan counter (with evictions-actually-occurred guard), pinned final-value
  anchors from the dense replay.
- `apps/backend/tests/test_features.py` (or a NEW oracle test file) -- oracle-equivalence test
  (dense fixture + ≥1 seeded sim scenario, exact `==`, provably covering post-eviction ticks) +
  the error-case matrix below.
- existing fingerprint test file (follow the iter-16 placement, e.g. `test_analytics_api.py` /
  config tests) -- stability test + counter-test for the new key.
- `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` -- additive
  iter-17 note only.
- `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-17-dev.md` -- dev handoff.

## UI Evolution (required if Frontend Present: yes)

- New user-facing capability: **None — by design.** The user-facing acceptance is the negative
  assertion: nothing visible changes. (UI-audit note from the spec: a performance gate is not a
  capability the UI could expose — do NOT flag UI-FAIL for "backend changed but UI did not".)
- New information displayed: None.
- New user actions: None.
- UI surface changes: None. The disabled Studies nav entry stays disabled (its page lands with
  J-60 next iteration).
- Navigation changes: none.

## Visual Requirements (required if Frontend Present: yes)

- Component patterns: no new components — existing cockpit panels only, verified unchanged.
- Layout: unchanged; browser QA verifies the existing cockpit renders identically.
- Key visual effects: none added. Sentinel captures must be full-page, scrolled-into-view,
  non-blank, with byte-size sanity checks (iter-2/3/14 capture discipline).
- States to handle: the J-68 no-thesis SIM-BUYER cockpit (panels, chart + Control marker,
  observations, event log, confidence) must behave identically pre/post engine change. The
  backend serving the captures MUST be started AFTER dev completes, with a canary check
  (iter-6 lesson).

## Key Test Scenarios

- **Structural no-rescan:** during the dense-fixture replay on the engine path, the count of
  `_refresh_fractions()` invocations after evictions begin is zero (or a strictly bounded,
  justified, documented constant) — AND the test asserts evictions actually occurred (guard
  against a silently too-short fixture).
- **Oracle equivalence:** over the dense fixture AND ≥1 seeded sim scenario, incremental
  `bid_refresh_score`/`ask_refresh_score` exactly equal (`==`, never approx) the
  `_refresh_fractions()` oracle on identical window contents, at every compute or a dense
  sampled subset provably including many post-eviction ticks.
- **CI timing gate:** unpaced fresh-`TapeEngine` replay of the committed fixture completes
  within `dense_replay_time_budget_seconds`, in CI, without credentials.
- **Pinned regression anchors:** exact final feature values (refresh scores, impacts, ratios at
  minimum) from the dense replay committed as equality-pinned assertions.
- **Fingerprint pair:** changing `dense_replay_time_budget_seconds` does NOT move
  `config_fingerprint`; changing a real classifier threshold still DOES.
- **Error cases, each byte-identical to the oracle:** empty window; trades before the first
  quote (no in-effect quote ⇒ no refresh evidence, never fabricated); quote-only window;
  single-trade window; the eviction boundary (oldest trade's `impact_delta` removal unchanged);
  a quote eviction that strips an early in-window trade of its in-effect quote (the trade STOPS
  contributing refresh evidence, exactly as the merge oracle does).
- **Whole existing suite green (607+ tests):** notably `test_features.py`, the
  progressive-vs-single-shot determinism test, `test_observer_equivalence.py` (7/7),
  `test_real_data_classify.py` (5 pinned), `test_real_data_gate.py` (35), `test_scenario.py`.
  No re-pinning of any feature value — a semantics change is a stop-and-flag, never a silent re-pin.
- **Browser (post-dev server + canary):** J-68 regression sentinel (SIM-BUYER, no thesis:
  panels, chart + Control marker, observations, event log, confidence all identical) and a
  J-08 REST==UI agreement spot check; full-page, non-blank captures.

## Notes / Assumptions

- **No scope creep detected** — the spec maps 1:1 to goal.md capability 34 and stays inside
  CORE RULES; the committed fixture is allowed by the persistence anti-goal's "committed test
  fixtures excepted" clause.
- **Credential assumption:** Alpaca credentials are available at dev time for the one-time SIP
  fixture fetch (use the bounded/chunked paths — the unbounded fetch is a known hang). If not
  available, the developer STOPS and flags rather than substituting synthetic data.
- **Harness-defect fallback (spec NOTES, mandatory):** the open `qa_complete` defect may halt
  the pipeline after QA; this iteration's done-ness must NOT depend on audit/closure artifacts.
  The goal-evaluator independently re-runs the full backend suite, the new gate/oracle/no-rescan
  tests, the fingerprint pair, and opens the J-68/J-08 sentinel pixels. If the harness
  hard-blocks before QA, complete lean-style (developer → reviewer → browser-qa) with the same
  evaluator re-runs.
- **Stall-risk note for the evaluator:** no journey can flip this iteration by design (J-62's
  reference-study clause needs the J-60 runner, next iteration). One deliberate no-flip
  iteration, not a stall.
- Required-still-passing: J-01–J-09, J-17, J-19, J-31, J-36, J-37, J-42, J-58, J-59 plus every
  journey currently passing in journey-history.json.
