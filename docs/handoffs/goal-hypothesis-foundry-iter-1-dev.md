# goal-hypothesis-foundry-iter-1 Dev Handoff

**Phase:** goal-hypothesis-foundry-iter-1
**Date:** 2026-08-26
**Agent:** developer
**Status:** complete

## What Was Built

1. **Fixed the QA-rig-crashing fixture bug** (IN SCOPE bullet 1, TC-1/TC-2). `apps/backend/
   scripts/seed_micro_graduation_iter18_fixture.py::_observation()` now declares
   `value_unit=wf.WF_OBSERVATION_UNIT` (`"return_bps"`) on all 30 seeded observations. The values
   themselves were already basis points (`_ECON_FLOOR` compares them against a `floor_bps` in the
   same `long` direction) — the bug was a missing declaration, never a wrong unit.
   `walkforward.require_canonical_observation_units` (the guard that caught this) was **not**
   touched.
2. **Confirmed the scoped `:8301` QA rig starts healthy after the fix.** Ran
   `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` against a fresh throwaway
   root under `$TMPDIR`, port 8301. The `seed-micro-graduation-iter18` step now completes
   (`transition=appended verdict=pass n=30`, no `UnitMismatchError`), every subsequent seed step
   runs, and the backend reaches `Application startup complete`; `GET /research/desk/micro/
   readiness` returned 200 and `GET /research/desk/micro/foundry` returned 200 with the expected
   body. The rig's own `reports/qa-scoped-backend-store-manifest.md` was reverted to its committed
   state afterward (my verification launch's root path is not the pipeline's own QA launch — the
   browser-qa-agent's own launch will overwrite it with its own manifest).
3. **`docs/hypothesis-foundry-spec.md`** — the Foundry Methodology Spec (Key Capability 1).
   Candidate-construction/freeze/exhaustion semantics only, section-numbered to match `docs/
   goal.md`'s Foundry Constitution exactly (§1–§12) so a citation names the same rule in both
   files. References `scout.screen_candidate`/`docs/rapid-validation-spec.md` by name for the
   statistical rail; never restates or forks it. §12 states plainly what this revision proves
   (hermetically, over the 7 fixture archetypes) and what it deliberately does not build yet.
4. **`app/research/foundry_source_registry.py`** — new module:
   - the closed §7.1 disposition vocabulary (14 members, `SOURCE_DISPOSITIONS` frozenset);
   - `SourceRecord`, the §1.4 per-source-record schema (frozen dataclass; an `extra` field the
     compiler never reads, proving TC-11);
   - `compile_source_disposition()` — the §2 owner meta-policy as one fixed precedence: explicit
     exclusion → proxy → supersession → unresolved magnitude word (`BLOCKED_SPEC_GAP`) →
     `BLOCKED_DIRECTION` sentinel → `BLOCKED_UNSUPPORTED_STUDY_FORM` sentinel → `COMPILED`;
   - the §2.3 natural-boundary law as three named threshold-provenance constants, enforced at
     `SourceRecord` construction (an illegal fourth value raises `ValueError` immediately);
   - `lint_quoted_spans()` — the §1.4 exact-quote lint: every `QuotedSpan` must match its own
     record's `source_excerpt` at the recorded character offset exactly, or `QuoteMismatch` (fails
     closed; no keyword/fuzzy fallback);
   - `source_registry_hash()` — content-sensitive, field-order-invariant, ignores `extra`;
   - `record_era_open_baseline()` / `read_era_open_baseline()` — the static, one-time era-open
     snapshot (backend suite pass/skip/failed, `tsc` error count, `config_fingerprint`, six
     `referee_*.py` SHA-256 hashes), persisted to a `foundry` sibling dir
     (`resolve_foundry_dir`, `TAPEOLOGY_FOUNDRY_DIR` override), read verbatim by the GET route —
     never recomputed on read;
   - `foundry_era_identity()` — static era/session identity dict (Rapid Microscope closed /
     Foundry active) plus `FOUNDRY_SPEC_VERSION = "v1"`.
5. **`app/research/foundry_compiler.py`** — new module:
   - the canonical `CandidateSpec` dataclass implementing every §3 required field
     (`CandidatePopulation`/`CandidateCoordinate`/`CandidateRelation`/`CandidateOutcome`/
     `EconomicFloorRule` sub-dataclasses);
   - `candidate_spec_hash` — sha256 over every field except the four hash/pointer fields
     themselves (`manifest_hash` is excluded because it is computed from the whole manifest,
     circularity; `source_registry_hash`/`compiler_hash` are kept as separate provenance
     pointers); field-serialization order never moves it, any other field always can (TC-10);
   - `CandidateOutcome.__post_init__` verifies `horizon_key` against the real `scout.HORIZON_KEYS`
     (never a second hard-coded set) and `sidedness ∈ {long, short}`;
   - `compile_sources()` — batch compiler: lints first (fails closed before any spec is built),
     derives every disposition, groups `COMPILED` records sharing a `foundry_family_key` into one
     family (shared `foundry_family_id`/`foundry_family_variant_count`, distinct
     `variant_ordinal`s — refuses on a duplicate ordinal via `FamilyOrdinalCollision`), and builds
     a `CandidateSpec` for every `COMPILED` record whose caller-supplied `CandidateBlueprint` is
     fully immediate (no deferred coordinate — `foundry_interpreter.py` is explicitly future
     work/out of scope; a compiled-but-not-yet-spec'd record is simply `FROZEN_READY`-incomplete
     this revision, never approximated). `CandidateBlueprint` is passed as a separate
     `blueprints: Mapping[str, CandidateBlueprint]` argument, not a `SourceRecord` field — keeps
     the §1.4 and §3 schemas in their own modules with no import cycle.
6. **New route `GET /research/desk/micro/foundry`** added to the existing `micro_routes.py`
   router (GET-only, page-load-never-computes). Serves era/session identity, `foundry_spec_version`,
   the era-open baseline block read verbatim, and `source_registry_hash: null` +
   `source_registry_status: "not_yet_generated"` (never fabricated — the real registry does not
   exist until J-06).
7. **`apps/frontend/app/desk/page.tsx`** — appended `<section aria-label="Hypothesis Foundry">`
   below every existing shipped section, `data-testid="foundry-panel"` family
   (`foundry-era-identity`, `foundry-era-open-baseline`, `foundry-baseline-*`,
   `foundry-referee-module-hashes-table`, ...). Renders the `GET /research/desk/micro/foundry`
   body verbatim — era identity, baseline suite counts, `tsc` error count, config fingerprint, the
   six Referee-module hashes in a table — with no client-side recomputation. Read-only; the fetch
   is issued once on first expand (`toggleSection`'s existing plain-handler pattern — no new
   `useEffect`, so `test_desk_refresh_chain_guard.py`'s pinned effect census is unaffected).
8. **`apps/backend/scripts/record_foundry_era_open_baseline.py`** — the small operator CLI that
   performs the one-time recording act (takes `--passed/--skipped/--failed/--tsc-errors` as
   already-measured inputs; never shells out to pytest/tsc itself). Run once this iteration against
   the real store with the final counts below.

## Files Changed

- `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py` -- `_observation()` now declares
  `value_unit` (the fixture bug fix)
- `apps/backend/app/research/foundry_source_registry.py` -- new: disposition vocabulary, source
  schema, owner meta-policy, exact-quote lint, era-open baseline, era identity
- `apps/backend/app/research/foundry_compiler.py` -- new: `CandidateSpec` schema + hash, batch
  compiler
- `apps/backend/app/research/micro_routes.py` -- new `GET /research/desk/micro/foundry` route
- `apps/backend/scripts/record_foundry_era_open_baseline.py` -- new: era-open baseline recording
  CLI
- `apps/backend/tests/test_foundry_source_registry.py` -- new: TC-5..TC-9, TC-12, disposition
  vocabulary, registry hash, era-open baseline round-trip
- `apps/backend/tests/test_foundry_compiler.py` -- new: TC-3, TC-4, TC-10, TC-11, blueprint/family
  edge cases
- `apps/backend/tests/test_foundry_route.py` -- new: TC-13, TC-15, GET-only route shape
- `apps/backend/tests/test_foundry_fixture_unit_regression.py` -- new: TC-2 (seed script unit fix)
- `apps/frontend/app/desk/page.tsx` -- new `HypothesisFoundrySection`, panel wiring
  (`hypothesisFoundry` collapsible id, `foundryResult` state, fetch branch)
- `apps/frontend/lib/api.ts` -- new `fetchDeskFoundry()`
- `apps/frontend/lib/types.ts` -- new `FoundryEraIdentity`/`FoundryEraOpenBaseline`/
  `DeskFoundryResponse`
- `docs/hypothesis-foundry-spec.md` -- new: the Foundry Methodology Spec

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junitxml=...` (pytest 9.1.1 in
this environment prints no final terminal summary line even on a clean run — counts below are from
`--junitxml`, cross-checked against the dot/`s` marker count in the captured log, the same
workaround iter-0's handoff used)

Result: **3787 passed, 8 skipped, 0 failed** (3795 collected, 0 errors) — full suite, including the
40 new Foundry tests. No regressions.

Frontend: `cd apps/frontend && ./node_modules/.bin/tsc --noEmit` → **0 errors**.

Targeted re-checks after the full run (isolation from the long full-suite run):
- `test_foundry_source_registry.py` + `test_foundry_compiler.py` + `test_foundry_route.py` +
  `test_foundry_fixture_unit_regression.py`: 40/40 passed.
- `test_copy_discipline.py`: 30/30 passed (the new Foundry panel copy is clean).
- `test_desk_refresh_chain_guard.py` + `test_desk_ui_guards.py`: 113/113 passed (no `useEffect`
  census drift, no other desk-page structural guard broken).

Era-open baseline actually recorded against the real store (`apps/backend/.data/foundry/
era_open_baseline.json`, gitignored) with these final numbers:
`.venv/bin/python scripts/record_foundry_era_open_baseline.py --passed 3787 --skipped 8 --failed 0
--tsc-errors 0`. `config_fingerprint` live-read as `08e471b10130e1e2` (matches the pinned era
value — unmoved).

Service startup verified (pre-handoff checklist): `scripts/dev.sh` — both backend (:8301) and
frontend (:3301) started clean, stopped, restarted clean, no port conflicts. One gotcha
reconfirmed from prior eras: `pkill -f "next dev"` does not always reach the actual
`next-server` child process; `next-server`'s own PID needed a direct `kill -9` both times before
port 3301 was truly free — noted here for the next agent, not new this iteration.

Live verification of `GET /research/desk/micro/foundry` and the `/desk` panel against the real
recorded baseline (both via `scripts/dev.sh`, real `.data` store):
- `GET /research/desk/micro/foundry` → 200, body matches the recorded snapshot exactly (era
  identity, `backend_suite: {passed: 3787, skipped: 8, failed: 0}`, `tsc_error_count: 0`,
  `config_fingerprint`, all six Referee module hashes).
- `curl http://localhost:3301/desk` → contains `aria-label="Hypothesis Foundry"` and
  `data-testid="desk-section-expand-hypothesisFoundry"` (the collapsed header renders; per
  `CollapsibleSection`'s own documented contract the body — `data-testid="foundry-panel"` — is not
  server-rendered until the operator clicks to expand, exactly like every sibling section). The
  interactive expand + on-screen value verification (TC-14) is the browser-qa-agent's job next;
  every value it will see is confirmed correct at the API layer above.
- Confirmed the GET route never writes: `apps/backend/.data/foundry/` did not exist before the
  first real curl and the route call did not create it (only the explicit CLI recording act did).

## Known Issues

- **TC-14's interactive browser click was not performed by this developer step** (no Chrome MCP
  session was driven here) — only the API-level and collapsed-DOM-level checks above. The
  browser-qa-agent still needs to run the actual expand-and-screenshot pass; every value it will
  see is already verified correct against the live route.
- **`docs/hypothesis-foundry-spec.md` is a new, first-revision document** — it is deliberately
  scoped to what this iteration implements plus fixed-meaning-for-later-iterations text for §4–§11
  (interpreter/family/freeze/exhaust/evidence/survivor semantics remain unbuilt). A future
  iteration that builds `foundry_interpreter.py`/`foundry_family.py`/`foundry_freeze.py`/etc. should
  extend this spec in place (append a named revision) rather than fork a second spec document.
- **`CandidateBlueprint` (the §3 population/coordinates/outcome content) is currently an explicit,
  hand-authored input to `foundry_compiler.compile_sources()`, not derived from a source record's
  `mechanism_statement` text.** This is by design this iteration (see the module's own docstring
  and spec §12) — deriving it generically is `foundry_interpreter.py`'s job (J-03). A real source
  record authored at J-06 will need its own hand-authored blueprint alongside its §1.4 fields until
  that interpreter exists, OR J-03 lands first and supersedes this path for multi-coordinate/
  deferred cases. Flagging this now so the J-06 author doesn't rediscover it mid-task.
- **The natural-boundary-law precedence collapses `BLOCKED_UNIT_CONTRACT` into
  `BLOCKED_SPEC_GAP`'s branch** (see `foundry_source_registry.compile_source_disposition`'s §2 step
  6 comment): no fixture this iteration exercises a genuine cross-unit-arithmetic gap distinct from
  an unresolved magnitude word, so `BLOCKED_UNIT_CONTRACT` is reachable only via
  `explicit_exclusion`-style direct construction today, never derived from declared fields. A real
  source needing this disposition (goal.md's "unverified trade-share ↔ displayed-size arithmetic"
  example) will need either a dedicated declared field or a documented owner ruling on how to
  distinguish it mechanically from `unresolved_magnitude_words` — left for whichever iteration
  first needs it, since no required source this era is known to need it yet.
- Two interpretive scoping calls (what "first source records" means; deferring the Sources/Compiler
  UI) were made by the goal-decomposer and are logged in `runs/goal-session-hypothesis-foundry/
  state/assumptions.md` under `## iter-1 — goal-decomposer` — not this agent's calls, but restated
  here since they bound this iteration's scope.
