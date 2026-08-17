# goal-rapid-microscope-iter-1 Dev Handoff

**Phase:** goal-rapid-microscope-iter-1
**Date:** 2026-08-17
**Agent:** developer
**Status:** complete

## What Was Built

J-01's remaining deliverable, alone (per the iter spec's BACKGROUND and the iter-0 handoff's own
"Suggested Next Phase"): the era's first served value, a read-only corpus-truth surface.

- **`apps/backend/app/research/micro_readiness.py`** (new) — aggregates the 18 registered legacy
  tick datasets into a served-from-disk inventory:
  - `build_readiness(store, cache, *, dataset_dir)` — the whole response, reading
    `DatasetStore.list()` verbatim (checksum/trade_count/quote_count/data_feed/window bounds/
    split — never re-parsed, never re-derived) and `referee_evidence.REFEREE_TICK_GATE_SYMBOL_DAYS`
    verbatim (150, imported, never a second literal).
  - Per-shard `session_date` (ET calendar date) and `coverage_gaps` (overlap of the shard's window
    against the fixed 09:30–16:00 ET RTH session) — cheap arithmetic, no event replay.
  - Per-shard `fallback_frac` — the one genuinely expensive computation (a linear scan mirroring
    `aggressor.classify_aggressor`'s documented Stage-1 precondition), cached in a new
    checksum-keyed SQLite table (`MicroReadinessCache`, mirrors `tradability_cache.py`'s
    "rebuildable result only, owns nothing" discipline) so a repeat request never re-replays the
    ~0.92 GB corpus.
  - Every shard tagged `split_provenance: "hand_assigned"`, `exposure_state: "exploratory"`
    (constants, spec §7.7).
  - Corpus totals: `distinct_symbol_days`, `distinct_datasets`, `rth_minutes_covered`,
    `session_equivalents` (`rth_minutes_covered / 390`), `referee_tick_gate_symbol_days`.
  - `study_floors`: the three J-09-predeclared pilot studies, each compared against the frozen
    `WF_TRAIN_MIN_SESSIONS` (40) + `WF_TEST_MIN_SESSIONS` (20) = 60-session geometry floor —
    transcribed here as this iteration's first code representation of those two spec constants
    (see Known Issues).
  - `DatasetStore.list()`'s own `errors` half served verbatim as `integrity_errors` — never
    dropped, never a crash.
- **`apps/backend/app/research/micro_routes.py`** (new) — `GET /research/desk/micro/readiness`,
  a fresh router mounted separately in `main.py` (mirrors `referee_routes.py`'s precedent),
  depending on the existing `routes.get_dataset_store` provider.
- **`apps/backend/app/main.py`** — mounts the new router (8 lines: one import, one
  `include_router`, matching comments).
- **`apps/backend/tests/test_desk_ui_guards.py`** — extended `_PRICE_ARITHMETIC_FIELDS` with
  every served Microscope Readiness numeric (`readiness.totals.*`, `shard.*`, `floor.*`) plus a
  seeded counter-test proving the guard can fail (TC-9).
- **`apps/frontend/app/desk/page.tsx`** — a new "Microscope Readiness" section, appended directly
  below the shipped "Referee Runs" section (the prior last section): `MicroReadinessSection`
  component, `microReadinessResult` state, a `"microReadiness"` `DeskCollapsibleSection` variant,
  and one new `toggleSection` branch. Collapsed by default; the GET fires only on first expand
  (the shipped `CollapsibleSection` + deferred-read pattern, zero new `useEffect` —
  `test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT` is unaffected). Renders the totals
  line, the 18-row shard table, the 3-row floors table, and honest empty-state copy for
  `integrity_errors`/`shards` — every numeric read verbatim (`.toFixed()`/`.toLocaleString()` are
  formatting calls, never arithmetic). No existing line in the file was edited except the single
  mechanical union-type continuation (`| "refereeRuns"` → `| "refereeRuns" | "microReadiness"`).
- **`apps/frontend/lib/api.ts`** / **`apps/frontend/lib/types.ts`** — `fetchMicroReadiness()` and
  the `MicroReadinessResponse`/`Totals`/`Shard`/`StudyFloor` types, mirroring the established
  `fetchRefereeEvidence`/`RefereeEvidenceResponse` shape exactly.
- **`apps/backend/tests/test_micro_readiness.py`** (new) — TC-1 through TC-7 plus supporting unit
  coverage (31 tests): real-corpus checks (TC-1/2/3/4/5, module-scoped fixture so the expensive
  real-corpus classification runs once for the file), a hand-corrupted-file fixture (TC-6, both at
  the module level and through the route), a cache-hit call-count spy at both levels (TC-7), an
  RTH-overlap/coverage-gap table locking in five hand-computed window shapes, and a cross-validated
  proof that `_quote_rule_decides` agrees with `classify_aggressor`'s own observable behavior
  (never merely a second copy of the same formula — see the module docstring).

## Files Changed

- `apps/backend/app/research/micro_readiness.py` -- new: the corpus-truth aggregation + cache
- `apps/backend/app/research/micro_routes.py` -- new: `GET /research/desk/micro/readiness`
- `apps/backend/app/main.py` -- mounts the new router
- `apps/backend/tests/test_micro_readiness.py` -- new: TC-1..TC-7 + unit coverage (31 tests)
- `apps/backend/tests/test_desk_ui_guards.py` -- extended `_PRICE_ARITHMETIC_FIELDS` + counter-test
- `apps/frontend/app/desk/page.tsx` -- new Microscope Readiness section (strictly additive)
- `apps/frontend/lib/api.ts` -- `fetchMicroReadiness()`
- `apps/frontend/lib/types.ts` -- `MicroReadinessResponse` + nested types

## Real-corpus values (recorded here per TC-12; also the exact response served live)

```
totals: {
  distinct_symbol_days: 12, distinct_datasets: 18,
  rth_minutes_covered: 1173.49, session_equivalents: 3.0089,
  referee_tick_gate_symbol_days: 150
}
study_floors: 3 rows, all {floor_name: "wf_fold_geometry", required_sessions: 60,
  available_sessions: 11, status: "floor_unmet"}
fallback_frac spread across the 18 shards: [0.2931, 0.8252]
integrity_errors: []
```

Verified three independent ways: (1) a hand computation against the real dataset metadata before
any code was written, (2) the unit test suite's real-corpus fixture (`test_tc1`..`test_tc5` in
`test_micro_readiness.py`), (3) a live browser pass against `scripts/dev.sh`'s running backend —
the served totals, all 18 shard rows (including exact byte counts, e.g. 1,490,506 for the first PG
shard), and all 3 floor rows matched the API response and my hand computation exactly (element
`extract` used instead of a screenshot — see Known Issues).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/` (no added `-q`, per lessons.md)

Result: **2723 passed, 8 skipped, 0 failed** in 348.70s. Exit code 0.

- Baseline (iteration 0): 2691 passed / 8 skipped.
- This iteration adds exactly 32 new tests (31 in `test_micro_readiness.py` + 1 in
  `test_desk_ui_guards.py`) — 2691 + 32 = **2723**, matching exactly. Skip count unchanged (the
  same 5 credential/live-market-gated files). Zero regressions.

`config_fingerprint`: `08e471b10130e1e2` — unchanged, matches the era pin exactly (re-run after
every edit; no `Config` field was touched).

Referee-module SHA-256 listing — all 6 byte-identical to the iteration-0 baseline:

```
6dd807b5ab69af033686a395484b1b10515d0f453a79c0943e534a578259786c  referee_adjudicate.py
482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5  referee_evidence.py
34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603  referee_null.py
03840c863b1e1f382ad2588d3bb6d8dc0e36a70582c3cb7a716638dabef32d99  referee_registry.py
0cc3a06f7b382c63d544886ec74a47f2414612fc77dd3dac444b00cc35216140  referee_routes.py
fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c  referee_stats.py
```

`apps/frontend`: `node_modules/.bin/tsc --noEmit` — zero errors, whole project.

## Pre-handoff verification (service startup)

- `scripts/dev.sh` started both services cleanly on this repo's deterministic ports (`:8301`
  backend / `:3301` frontend — confirmed to be the SAME "store-scoped rig" ports the testing
  requirements name, simply this repo's own hash-derived offset). Backend served
  `GET /research/desk/micro/readiness` with the real corpus shape immediately; frontend `/desk`
  returned 200 with both "Referee Runs" and "Microscope Readiness" headings present.
  `Application startup complete` logged with zero errors.
- Live browser pass (Chrome DevTools, attached to an already-listening `:9222` instance — not
  started by this session, so not torn down by it): navigated to `/desk`, clicked "Microscope
  Readiness" to expand it, `await_text` confirmed the fetch resolved, and an element `extract`
  (text) of `[data-testid="micro-readiness-section"]` showed every totals/shard/floor value
  matching the live API response byte-for-byte (see the real-corpus values section above).
- Stopped both dev.sh processes via a port-scoped kill (`lsof -ti :8301` / `:3301`, never a
  pattern-based `pkill`/`killall`, per the standing pump note) — both ports released cleanly.
  Re-verified free before finishing.
- External integrations / native dependency binaries: not applicable — no new adapter, no new
  runtime dependency. `micro_readiness.py` reads only the already-recorded local `DatasetStore`.

## Known Issues

- **The measured `fallback_frac` spread (0.2931–0.8252) is slightly wider than goal.md's Build
  anchors' descriptive "29–76% per dataset" sentence.** Investigated directly: the one shard
  driving the high end (`309845c6…`, a 30-second, 103-trade slice of the committed PG reference
  fixture) has a normal bid-ask spread (avg ~$0.056, comparable to AAPL's ~$0.050 in the same
  corpus) — there is no bug; a very short, thin window genuinely has more mid-spread prints than a
  multi-hour one. `_quote_rule_decides` is cross-validated against `classify_aggressor`'s own
  observable behavior in the test suite (not merely against a second copy of the same formula), so
  I'm confident this is the correct, honestly-measured value rather than the goal.md prose's
  approximation. `test_tc3…` locks in the real measured min/max explicitly rather than the
  descriptive range. Flagging for the reviewer/auditor to weigh in on whether goal.md's own Build
  anchors sentence should be corrected in a later documentation pass (out of this iteration's
  scope to edit goal.md).
- **`WF_TRAIN_MIN_SESSIONS`/`WF_TEST_MIN_SESSIONS` are transcribed into `micro_readiness.py`
  as this iteration's first code representation of two `docs/rapid-validation-spec.md` §1
  constants** — no module owns them yet (`walkforward.py` is J-05, eight iterations away). Named
  clearly and exported so a future J-05 developer can import these two names from here or
  supersede them; never a second, independently-valued copy. Reversible per
  `runs/goal-session-rapid-microscope/state/assumptions.md`'s iter-1 entry, which already
  pre-approved this exact reading.
- **`session_date`'s ET conversion is a private module-level `ZoneInfo` constant in
  `micro_readiness.py`, not reused from `desk_sessions.py`** — despite the iter spec's own text
  suggesting "reuse its ET-date conversion." I read `desk_sessions.py` in full: it has no ET
  conversion at all (its own `_session_date` is UTC-calendar, and `referee_evidence.py`'s own
  comment explicitly draws this same distinction). `desk_sessions.py` IS the arbiter of which
  dates are known trading sessions (spec §0), a different question this module doesn't need to
  ask (every legacy shard is already a known-real recorded window). I followed the established
  codebase idiom instead — `referee_evidence.py`'s own module docstring: "each module that needs
  ET wall-clock resolution owns a private ZoneInfo constant" — and mirrored its exact
  `_et_session_date` formula. Flagging this interpretation explicitly since the spec text implied
  a reuse path that does not exist in the named module.
- **The `unknown_frac` half of the era anti-goal ("every aggressor-derived quantity is served
  beside its `fallback_frac` and `unknown_frac`") is not served this iteration.** The iter-1
  Data-contract JSON shape lists only `fallback_frac` per shard, and this endpoint serves no
  per-window aggressor-derived FEATURE value (that is J-02's `micro_features.py`, explicitly OUT
  OF SCOPE here) — `fallback_frac` here is itself the corpus-level diagnostic, not a feature that
  would need its own disclosure beside it. I believe the anti-goal targets J-02's future
  per-window features, not this iteration's corpus inventory, but flagging the reasoning
  explicitly for the reviewer/auditor to confirm.
- **An element screenshot of the new section came back blank** in my own quick manual browser
  check (via the already-running, not-self-started `:9222` Chrome instance) — `extract` (text)
  against the same selector worked perfectly and showed fully correct content matching the API
  exactly, and `document.visibilityState` was `"visible"` (ruling out the known
  hidden-tab-freezes-rendering issue this project has hit before). This looks like a tooling quirk
  specific to that Chrome instance/session rather than a product defect — text-level verification
  gives strong functional confidence, but the authoritative T-9/T-10 screenshot evidence (clean
  `.next` rebuild, the store-scoped rig, proper element capture) is browser-qa-agent's job next,
  not reproduced here.
- Full click-through sentinel verification of `/`, `/structure`, and every other shipped `/desk`
  section (J-10's Testing Requirements) is browser-qa-agent's step, per the established division
  of labor this project's prior iteration handoffs also follow. This developer's own check was
  limited to: `/desk` returns 200, both "Referee Runs" and "Microscope Readiness" headings render,
  and the new section's content is exactly correct on expand.
- No new MCP tool was added (the surface stays at 22 tools, confirmed unmodified — `desk_micro_
  readiness` lands in J-08 per the iter spec's OUT OF SCOPE list); `GET /research/desk/micro/
  readiness` is already reachable through the existing `get_endpoint` tool's `/research/*`
  allowlist with zero MCP-side change.

## Suggested Next Phase

Per goal.md's dependency order (J-01 → J-02 → ... → J-09, J-10 guarding continuously) and the
Constraints' Iteration hygiene note, iteration 2 should build **J-02 alone**: the additive
`observer=` kwarg on `DatasetStore.replay` (default `None`, counter-tested byte-identical),
`micro_observer.py`/`micro_snapshots.py` (streaming snapshot rows, flush-before-next-event,
identity + load-time verification), the Wave-1 `micro_features.py` primitives with their
hand-derived oracle fixtures, the spec §2.4 granularity benchmark, and snapshots built for all 18
legacy datasets. This is the era's next unblocker (every later journey through J-09 reads
snapshots this journey creates) and is explicitly the next journey in the goal's stated dependency
order.
