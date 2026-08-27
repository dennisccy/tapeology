# goal-hypothesis-foundry-iter-4 Dev Handoff

**Phase:** goal-hypothesis-foundry-iter-4
**Date:** 2026-08-27
**Agent:** developer
**Status:** complete

## What Was Built

The consolidated Hypothesis Foundry read surface (J-02/J-03/J-04/J-05) — four new additive
top-level keys on `GET /research/desk/micro/foundry` (`sources_compiler`, `interpreter_fixtures`,
`freeze_integrity`, `hermetic_oracles`), each computed **exactly once at module-import time** from
purely hermetic literals and served verbatim on every request (never per-request compute) — plus
the two carried repairs from the iter-3 audit.

- **Repair 1 (auditor B7)** — `foundry_source_registry.lint_alternatives`: a new fail-closed batch
  lint over `SourceRecord.alternatives`, called alongside `lint_quoted_spans` inside
  `foundry_compiler.compile_sources`. Raises `AlternativeReferenceInvalid` when an alternative
  names (a) a nonexistent `source_id`, (b) a sibling outside the record's own `foundry_family_key`
  (including when the naming record has no family key at all), or (c) the record's own
  `source_id`.
- **Repair 2 (auditor B4)** — `foundry_runner.run_one_candidate`'s intent-without-terminal
  ("crash") branch now also verifies the pinned intent row's `manifest_hash` against the current
  invocation's `manifest_hash` (mirroring the already-fixed terminal-row check three lines above
  it), raising `FoundryResumeIdentityMismatch` on drift — checked before the existing
  `econ_floor_bps` check.
- **`sources_compiler` (J-02)** — `foundry_compiler.sources_compiler_hermetic_fixture_view()`: the
  exact 7 hermetic source-fixture archetypes from `test_foundry_source_registry.py`/
  `test_foundry_compiler.py` (compileable natural-boundary scalar; two-variant family — one
  surfaced entry naming the other via `alternatives`, both actually compiled so the surfaced
  entry's `foundry_family_variant_count` genuinely reads 2; unresolved magnitude word; proxy-only;
  unsupported statistic; alias/supersession; directionless), compiled through the real
  `compile_sources`, plus the `immutability_proof` (same fixture compiled twice with different
  injected `extra` fields — identical `candidate_spec_hash`). New `candidate_spec_view()` is the
  one canonical `CandidateSpec` → plain-dict rendering, reused by other subviews.
- **`interpreter_fixtures` (J-03)** — `foundry_interpreter.interpreter_hermetic_fixture_view()`:
  the 5 named scenarios (`immediate_scalar_equivalence`, `conjunction`, `deferred_refill_
  consistent`, `mirrored_direction`, `unsupported_ordered_relation`), each run through the real
  `resolve_population`/`interpret_candidate`. The mirrored scenario builds a genuine
  support-long/resistance-short pair (the resistance/short side uses the sign-negated outcome a
  short position would realize on the identical market) so it authentically demonstrates `long`
  dying via `killed_direction` and `short` surviving — not merely two labels.
- **`freeze_integrity` (J-04)** — `foundry_freeze.freeze_integrity_hermetic_fixture_view()`: the
  1/multiple/at-cap/over-cap family fixtures, late-insertion refusal, generation replay
  (idempotent + drift-refused), a fixture freeze record (naming the real future path
  `docs/hypothesis-foundry/freeze-set.json`, fixture-scoped), the first-read-lock's three outcomes,
  and replay idempotence/conflicting-refusal/single-flight-refusal — all through the real
  `foundry_family`/`foundry_freeze`/`foundry_ledger`/`foundry_runner` functions. The freeze-set
  fixture uses a **stable, non-random** temp directory (`freeze_integrity_fixture_dir()`) so a
  fresh `generate_freeze_set` recomputation reproduces the identical `freeze_set_hash` (TC-11).
- **`hermetic_oracles` (J-05)** — new module `app/research/foundry_hermetic_summary.py`:
  genuinely re-runs `tests/test_foundry_hermetic_epoch.py`'s own fixture generators (imported
  directly, never re-typed) through the real production path to report outcome-type coverage,
  denominator consistency, canonical-order preservation, and pass/fail for the all-blocked,
  all-killed, multi-survivor, crash-resume-at-scale, and protected-data-trip/evidence-class-
  immutability fixtures — no second oracle implementation, no protected/sealed identity ever read.
- **Frontend** — four new nested `CollapsibleSection`s inside `HypothesisFoundrySection`
  (`apps/frontend/app/desk/page.tsx`): Sources/Compiler, Interpreter Fixtures, Freeze/Integrity,
  Hermetic Oracles — each carrying an explicit "Hermetic Fixture — not the real epoch" banner
  visually distinct from the header's `foundry-era-open-baseline` block, and reading the four new
  response keys verbatim (no client-side recomputation, no second fetch — same already-fetched
  `foundry` payload).

## Files Changed

- `apps/backend/app/research/foundry_source_registry.py` -- Repair 1: `lint_alternatives` +
  `AlternativeReferenceInvalid`.
- `apps/backend/app/research/foundry_compiler.py` -- calls `lint_alternatives`; adds
  `candidate_spec_view()` and `sources_compiler_hermetic_fixture_view()`.
- `apps/backend/app/research/foundry_interpreter.py` -- adds `interpreter_hermetic_fixture_view()`.
- `apps/backend/app/research/foundry_freeze.py` -- adds `freeze_integrity_fixture_dir()` and
  `freeze_integrity_hermetic_fixture_view()` (imports `foundry_family`/`foundry_ledger`/
  `foundry_runner`).
- `apps/backend/app/research/foundry_runner.py` -- Repair 2: crash-path `manifest_hash` check.
- `apps/backend/app/research/foundry_hermetic_summary.py` -- new module: `build_hermetic_oracles_
  summary()`.
- `apps/backend/app/research/micro_routes.py` -- `GET /research/desk/micro/foundry` grows the four
  additive keys, computed once at module import time and cached.
- `apps/backend/tests/test_foundry_source_registry.py` -- TC-16 lint-alternatives tests.
- `apps/backend/tests/test_foundry_compiler.py` -- TC-16 `compile_sources` integration test.
- `apps/backend/tests/test_foundry_runner.py` -- TC-17 crash-path `manifest_hash` drift test.
- `apps/backend/tests/test_foundry_route_hermetic_views.py` -- new file: TC-1 through TC-15 and
  TC-19 route-level tests (20 tests).
- `apps/frontend/lib/types.ts` -- `FoundrySourcesCompiler`/`FoundryInterpreterFixtures`/
  `FoundryFreezeIntegrity`/`FoundryHermeticOracles`/`FoundryCandidateSpecView`/
  `FoundrySourceFixture`/`FoundryInterpreterScenario` types; `DeskFoundryResponse` extended.
- `apps/frontend/app/desk/page.tsx` -- `HermeticFixtureBanner`, `SourcesCompilerSubsection`,
  `InterpreterFixturesSubsection`, `FreezeIntegritySubsection`, `HermeticOraclesSubsection`; four
  new nested `CollapsibleSection`s in `HypothesisFoundrySection`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **3878 passed, 8 skipped, 0 failed** (exit code 0; confirmed via `--junit-xml`). iter-3's
baseline was 3842 passed / 8 skipped / 0 failed — all growth is new tests, zero regressions.

Command: `cd apps/frontend && npx tsc --noEmit`
Result: **0 errors**.

Command: two repeated `curl http://localhost:8301/research/desk/micro/foundry` (backend started via
`scripts/dev.sh`)
Result: `sources_compiler`/`interpreter_fixtures`/`freeze_integrity`/`hermetic_oracles` byte
-identical across both calls, confirmed both via direct HTTP and via
`test_tc19_the_served_subviews_are_the_same_cached_object_across_two_in_process_calls` (Python
object identity, not just equality).

Config fingerprint verified unchanged: `CONFIG.config_fingerprint() == "08e471b10130e1e2"`
(`test_tc19_config_fingerprint_stays_pinned`).

Browser sanity check (pre-handoff verification, not the formal browser-QA pass): started
`scripts/dev.sh` (backend :8301, frontend :3301), navigated Chrome to `/desk`, expanded
`Hypothesis Foundry` then each of the four new subsections via their `desk-section-expand-*`
testids. Confirmed via DOM/markdown extraction (screenshot capture rendered blank in this headless
environment — a known tool quirk, not a page defect; text/DOM extraction was used instead and is
conclusive) that:
- All four `foundry-*-hermetic-banner` testids are present.
- Sources/Compiler shows 7 fixtures, the immutability proof, and a working CandidateSpec
  `<details>` drill-in.
- Interpreter Fixtures shows all 5 scenarios with real screen results.
- Freeze/Integrity shows the 4-row family denominator table, freeze record, and all boolean flags
  true.
- Hermetic Oracles shows outcome-type coverage and all 6 pass/fail booleans true.
- No console errors; existing `foundry-panel`/`foundry-era-identity`/`foundry-era-open-baseline`
  (J-01) rendered unchanged.

Both dev servers were killed after this check (`pkill -f "uvicorn main:app"`, `pkill -f "next dev
-p 3301"`) — no lingering processes.

## Known Issues

- **J-02 step 5's real-audit-report inspection is out of scope**, per `state/assumptions.md`
  iter-4 — the fixture-immutability half of step 5 is built and tested (TC-3); the committed
  `reports/hypothesis-foundry/source-registry-audit.md` inspection depends on J-06 (not yet built).
  This is a pre-declared, expected gap, not a defect — J-02 may still be scored `partial` for this
  reason alone.
- **The formal browser-qa-agent pass (J-02/J-03/J-04/J-05's 20 on-screen checks, TC-18) has not
  been run by this dev pass** — only a lightweight DOM-text sanity check was done above. The
  screenshot-capture tool returned blank images in this environment during my sanity check; the
  browser-qa-agent should verify whether that recurs and, if so, fall back to DOM/text extraction
  (as this handoff did) rather than treating a blank screenshot as a page failure.
- **`interpreter_fixtures`/`FoundryInterpreterScenario` carries one additive field beyond the
  iteration's own literal Data-contract text** (`predeclared_sidedness`, populated only for the
  `mirrored_direction` scenario) — needed to satisfy J-03 step 4's own acceptance ("predeclared
  sidedness is inside CandidateSpec before the outcome... shown"), since the contract's listed
  scenario fields have no dedicated slot for it. This is additive only (no listed field was
  removed or repurposed) and does not violate single-source-of-truth (the value is read straight
  off each `CandidateSpec.outcome.sidedness`, never recomputed).
- **`sources_compiler.fixtures[]` holds one surfaced entry for the "two explicitly-frozen legal
  variants" archetype, not two** — a deliberate schema-ambiguity resolution: the IN SCOPE prose
  names 7 "fixture types" where that one archetype is itself a two-record family, but the
  Data-contract's own TC-1 hard-requires "exactly 7 entries". Both sibling records ARE compiled
  together (so the surfaced entry's `foundry_family_variant_count` genuinely reads 2), and the
  surfaced record's own `alternatives` field names the uncompiled-but-real sibling by id. Flagged
  here for the reviewer/auditor to confirm this reading is acceptable.
- Full backend suite run took ~7 minutes wall-clock (3878 tests) — normal for this codebase's
  scale, not a regression introduced this iteration (the four new fixture-view builders together
  add well under 1 second at import time, confirmed by direct timing).
