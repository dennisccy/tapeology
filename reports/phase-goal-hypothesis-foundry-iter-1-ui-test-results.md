# Phase goal-hypothesis-foundry-iter-1 — UI Test Results

**Phase:** goal-hypothesis-foundry-iter-1
**Date:** 2026-08-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: J-01 (expected `passing` per the iteration spec's own scoring note) fails because the
     era-open baseline is not rendered on the live scoped QA rig; J-02's UI acceptance cannot be
     verified because no Sources/Compiler fixture view exists yet (explicitly out of scope this
     iteration per the spec, so this is a known/expected gap, not a regression). -->

**Overall:** 0/2 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Foundry opens as new finite era, old self-extension loop inactive | smoke | P1 | Panel identifies Rapid Microscope (closed) vs. Foundry (active) era separately; repo has archived Rapid Microscope goal + dated Foundry opening note; `runs/goal-session-rapid-microscope/` untouched; old proposer two-file condition no longer satisfied; era-open baseline (suite pass/skip/failed, `tsc` error count, config fingerprint, six Referee-module SHA-256 hashes) renders verbatim from `GET /research/desk/micro/foundry` | Steps 2-4 verified true via repo/filesystem checks. Step 5 fails: `GET http://localhost:8301/research/desk/micro/foundry` returns `"era_open_baseline": null`, and the expanded `Hypothesis Foundry` panel on `/desk` renders "The era-open baseline has not been recorded yet." instead of the suite/tsc/fingerprint/hash block | FAIL | `reports/qa/goal-hypothesis-foundry-iter-1-evidence/J-01-fail.png` |
| UT-J-02 | Ratified sources compile into auditable CandidateSpecs or typed blocks, inspectable in UI | smoke | P1 | A Foundry `Sources / Compiler` fixture view is reachable on `/desk`, showing 7 fixture source records (natural-boundary scalar, two frozen legal variants, unresolved magnitude word, proxy-only, unsupported statistic, alias/supersession, directionless mechanism) each with source refs/quoted span/formula refs/alternatives/threshold provenance/direction/alias/single disposition, plus an inspectable compiled `CandidateSpec` | No such view exists anywhere on `/desk`. DOM text search for "Sources / Compiler", "CandidateSpec", "fixture view" all return `false`; only the `Hypothesis Foundry` panel header (era identity + baseline block) is present. This matches the iteration spec's explicit OUT OF SCOPE line ("Any Sources/Compiler ... fixture UI subview beyond the panel header — deferred") — the UI surface for J-02 was not built this iteration by design | FAIL | `reports/qa/goal-hypothesis-foundry-iter-1-evidence/J-02-fail.png` |

---

## Passed Tests

None this iteration.

---

## Failed Tests

### UT-J-01 — Foundry opens as new finite era, old self-extension loop inactive
**Verdict:** FAIL
**Failure:** The `Hypothesis Foundry` panel on `/desk` renders correctly for era identity but does not render the era-open baseline block required by step 5 and by this iteration's own Definition of Done ("J-01 passes via browser-qa-agent ... panel header renders era identity + era-open baseline, every displayed value matches the `GET /research/desk/micro/foundry` response body verbatim"). Live `GET http://localhost:8301/research/desk/micro/foundry` on the running scoped QA rig returns:
```json
{"era":{"previous_era":"rapid-microscope","previous_era_status":"closed","current_era":"hypothesis-foundry","current_era_status":"active","foundry_spec_version":"v1"},"era_open_baseline":null,"source_registry_hash":null,"source_registry_status":"not_yet_generated"}
```
The expanded panel text reads "The era-open baseline has not been recorded yet." with no suite pass/skip/failed counts, no `tsc` error count, no config fingerprint, and no Referee-module hash table.

Root-cause detail (diagnostic only, not a fix): `apps/backend/app/research/foundry_source_registry.py::resolve_foundry_dir()` resolves the baseline storage directory as a `foundry` sibling of the caller's *resolved dataset directory*, honoring `TAPEOLOGY_FOUNDRY_DIR` only if explicitly set. The scoped QA rig backend process (uvicorn pid confirmed listening on :8301) has `TAPEOLOGY_DATASET_DIR` pointed at the scoped rig root (`.../tapeology-store-scope-qa/rig/datasets`) and no `TAPEOLOGY_FOUNDRY_DIR` override, so it resolves to `.../tapeology-store-scope-qa/rig/foundry`, which has no `era_open_baseline.json`. A populated `era_open_baseline.json` (matching the dev handoff's recorded numbers: `passed=3787, skipped=8, failed=0, tsc_error_count=0, config_fingerprint=08e471b10130e1e2`) does exist, but only under the real unscoped store at `apps/backend/.data/foundry/era_open_baseline.json` — the dev handoff records this was written via the developer's own manual `scripts/dev.sh` verification launch, not against this scoped QA rig's store. Whatever recording step (`scripts/record_foundry_era_open_baseline.py`) is meant to seed the scoped rig's own `foundry` directory before browser QA runs does not appear to have run for this rig instance.

Steps 2-4 (verified independently, not requiring the missing baseline):
- Panel correctly shows "Previous era: rapid-microscope (closed)" and "Current era: hypothesis-foundry (active)".
- `docs/goal-archive/goal-2026-08-26.md` (archived Rapid Microscope goal) and a dated Foundry opening note at `docs/research-directions.md:1126` ("HYPOTHESIS-FOUNDRY OPENING NOTE (2026-08-26...)") both exist.
- `runs/goal-session-rapid-microscope/` shows no uncommitted changes (`git status --porcelain` empty) and its last touching commit is the prior era's own finalization (`adb25d13 chore(goal): rapid-microscope finalization artifacts — GOAL_ACHIEVED`).
- No active `project-extensions/proposer-guidance.md` exists (only an archived copy at `docs/goal-archive/proposer-guidance-2026-08-26.md` and the generic template under `incredible_auto_dev/templates/`), so the old two-file proposer-dispatch condition is not satisfied.

**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-1-evidence/J-01-fail.png`

**Steps taken:**
1. Navigated to `http://localhost:3301/desk`.
2. Confirmed the collapsed `▸Hypothesis Foundry` section exists at the bottom of the page (below all other shipped Desk sections).
3. Clicked to expand it; extracted panel text — era identity present, era-open baseline block reads "has not been recorded yet."
4. Cross-checked against `GET http://localhost:8301/research/desk/micro/foundry` (`era_open_baseline: null`) — panel matches the live (empty) response verbatim, so rendering itself is correct; the underlying data is simply absent for this environment.
5. Verified steps 2-4 via filesystem/git checks (see above).

**Expected:** Era-open baseline block shows real suite pass/skip/failed counts, `tsc` error count, config fingerprint, and six Referee-module SHA-256 hashes.
**Actual:** Era-open baseline block shows only "The era-open baseline has not been recorded yet."; backing GET response field is `null`.

---

### UT-J-02 — Ratified sources compile into auditable CandidateSpecs or typed blocks, inspectable in UI
**Verdict:** FAIL
**Failure:** No `Sources / Compiler` fixture view exists anywhere on `/desk` (or elsewhere in the frontend). A full-page DOM text search for "Sources / Compiler", "Sources/Compiler", "CandidateSpec", "fixture view", and "Compiler fixture" all returned `false`. The only Foundry-related UI is the panel header (era identity + era-open baseline), which is all this iteration's IN SCOPE list built for the frontend. This is consistent with the iteration spec's own OUT OF SCOPE section: "Any Sources/Compiler (or other) fixture UI subview beyond the panel header — deferred to the consolidated read-surface iteration (Binding Execution Order step 5)." The J-02 backend machinery (compiler, schema, hash, lint) may be real and unit-tested per the dev handoff, but none of it is reachable through the browser this iteration, so J-02's steps 1-5 (all UI inspection steps) cannot be executed or verified via Chrome MCP.

**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-1-evidence/J-02-fail.png`

**Steps taken:**
1. Navigated to `http://localhost:3301/desk`, expanded every collapsible section via prior extraction pass — no "Sources", "Compiler", or "CandidateSpec" heading appears among the ~20 existing Desk sections plus the new Hypothesis Foundry section.
2. Ran `document.body.innerText.includes(...)` checks in-page for the exact terms named in the journey's steps — all `false`.
3. Confirmed the only rendered Foundry content is era identity + era-open baseline (already covered by UT-J-01).

**Expected:** A reachable Sources/Compiler fixture view showing the 7 named fixture source records with full per-record provenance fields, plus an inspectable compiled `CandidateSpec`.
**Actual:** No such view exists in the UI; zero DOM matches for any of the expected view's identifying text.

---

## Skipped Tests

None — both journeys were executed against a live frontend/backend and Chrome MCP.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (scoped QA rig)
- **Browser:** Chrome via MCP (attached to existing CDP endpoint at 127.0.0.1:9222, headless)
- **Test Date:** 2026-08-26
- **Evidence directory:** `reports/qa/goal-hypothesis-foundry-iter-1-evidence/`
