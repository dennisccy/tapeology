# Goal Session hypothesis-foundry — Iteration 2 — UI Test Results

**Phase:** goal-hypothesis-foundry-iter-2
**Date:** 2026-08-26
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 browser-testable tests passed (2 skipped by design — no UI surface this iteration)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Foundry opens as new finite era; old proposer loop inactive | smoke | P1 | `/desk` → Hypothesis Foundry panel shows real recorded era-open baseline (backend suite pass/skip/fail, config fingerprint, 6 Referee module SHA-256 hashes) matching `GET /research/desk/micro/foundry` verbatim; panel identifies Rapid Microscope as closed foundation and Foundry as a separate active era; repo has archived Rapid Microscope goal + dated opening note; old proposer two-file condition no longer satisfied; `runs/goal-session-rapid-microscope/` untouched | Panel expanded and rendered "Previous era: rapid-microscope (closed)" / "Current era: hypothesis-foundry (active)"; Era-Open Baseline block showed "Backend suite: 3787 passed · 8 skipped · 0 failed", "tsc --noEmit errors: 0", "Config fingerprint: 08e471b10130e1e2", and all 6 Referee module SHA-256 hashes — byte-identical to `curl http://localhost:8301/research/desk/micro/foundry`. Repo checks (Bash): `docs/goal-archive/goal-2026-08-26.md` is the archived Rapid Microscope goal; `docs/research-directions.md:1126` carries the dated "HYPOTHESIS-FOUNDRY OPENING NOTE (2026-08-26...)"; `git status --porcelain -- runs/goal-session-rapid-microscope/` is empty (untouched); `project-extensions/proposer-guidance.md` does not exist at the active path (only the archived copy at `docs/goal-archive/proposer-guidance-2026-08-26.md` and the unrelated template under `incredible_auto_dev/templates/`), so the old two-file proposer-dispatch condition is no longer satisfied | PASS | `reports/qa/goal-hypothesis-foundry-iter-2-evidence/J-01-result.png` |
| UT-J-03 | Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions | smoke | P1 | Acceptance steps require inspecting hermetic fixture views (immediate-scalar equivalence, conjunction boolean-projection, deferred `refill_consistent` timing, mirrored direction, unsupported ordered-relation block) inside the Hypothesis Foundry panel | No such fixture subsection exists in the shipped UI this iteration. Iteration spec (`docs/phases/goal-hypothesis-foundry-iter-2.md`) explicitly states: "Browser: J-01 only ... J-03/J-04 have no browser surface this iteration by design — their evidence is the hermetic test suite" and "both journeys are expected to remain/move to `partial` this iteration". Confirmed live: expanding Hypothesis Foundry on `/desk` renders only the era boundary + era-open baseline block (see UT-J-01 evidence); no Interpreter/Sources-Compiler subview is present to inspect | SKIP | none |
| UT-J-04 | Foundry owns the denominator, append-only state, freeze barrier, and integrity lock | smoke | P1 | Acceptance steps require inspecting family-cap/late-insertion/freeze-record/first-read-lock fixture views inside the Hypothesis Foundry panel | No such fixture subsection exists in the shipped UI this iteration — same by-design deferral as J-03 (all Foundry fixture UI, including Freeze/Integrity, is deferred to the Binding Execution Order step-5 consolidated read-surface iteration per the iteration spec's NOTES and IN SCOPE/OUT OF SCOPE sections). Confirmed live via the same panel expansion as UT-J-01/UT-J-03 — no Freeze/Integrity subview present | SKIP | none |

---

## Passed Tests

### UT-J-01 — Foundry opens as a new finite era and the old self-extension loop is inactive
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-2-evidence/J-01-result.png`

- Navigated to `http://localhost:3301/desk`, located the collapsed `▸ HYPOTHESIS FOUNDRY` section at the bottom of the Desk page, and clicked it to expand.
- Verified panel copy: "The Hypothesis Foundry (GET /research/desk/micro/foundry, read verbatim; read-only this era)... Foundry methodology spec version v1." followed by "Previous era: rapid-microscope (closed)" and "Current era: hypothesis-foundry (active)" — satisfies step 2 (identifies Rapid Microscope as closed foundation, Foundry era separately).
- Verified the "Era-Open Baseline" block now renders real values instead of "The era-open baseline has not been recorded yet.": `Backend suite: 3787 passed · 8 skipped · 0 failed`, `tsc --noEmit errors: 0`, `Config fingerprint: 08e471b10130e1e2`, and a 6-row Referee Module SHA-256 table (`referee_adjudicate.py`, `referee_evidence.py`, `referee_null.py`, `referee_registry.py`, `referee_routes.py`, `referee_stats.py`).
- Cross-checked against `curl -s http://localhost:8301/research/desk/micro/foundry`: `era_open_baseline` is non-null with `backend_suite.passed=3787`, `.skipped=8`, `.failed=0`, `config_fingerprint="08e471b10130e1e2"`, `tsc_error_count=0`, and all 6 referee_module_sha256 entries — every UI value is byte-identical to the backend response. This closes the QA-rig visibility gap named in the iteration BACKGROUND (TC-1, TC-2) — the scoped `:8301` rig now serves the genuine recorded artifact, not `null`.
- Repo-level checks (step 3): `docs/goal-archive/goal-2026-08-26.md` exists (archived Rapid Microscope goal, matches the current goal.md's "Predecessor archived at docs/goal-archive/goal-2026-08-26.md" header); `docs/research-directions.md` line 1126 carries the dated "HYPOTHESIS-FOUNDRY OPENING NOTE (2026-08-26, operator pivot..." entry, and a corresponding catalog row was appended 2026-08-26; `git status --porcelain -- runs/goal-session-rapid-microscope/` returned empty (no uncommitted changes — untouched).
- Repo-level check (step 4): `project-extensions/proposer-guidance.md` does not exist at the active path — only an archived copy (`docs/goal-archive/proposer-guidance-2026-08-26.md`, preserved for history, not rewritten) and an unrelated framework template (`incredible_auto_dev/templates/proposer-guidance.md`) exist. This confirms the old two-file condition that would dispatch the post-`GOAL_ACHIEVED` proposer is no longer satisfied for this era.
- All five journey steps and the Acceptance line (finite fixed journey set, no active continuous-improvement proposer, auditable era transition, no mutation of prior research records) are satisfied.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-J-03 — Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions
**Verdict:** SKIPPED
**Reason:** No UI surface shipped this iteration, by explicit design. The iteration spec states J-03's acceptance is proved only by the hermetic test suite this iteration ("J-03/J-04 have no browser surface this iteration by design"), with all Foundry fixture UI (Sources/Compiler, Interpreter, Freeze/Integrity) deferred to the Binding Execution Order step-5 consolidated read-surface iteration. Live-verified: the only content under the expanded Hypothesis Foundry panel is the era boundary + era-open baseline block (see UT-J-01) — no Interpreter fixture subview exists to click into for immediate-scalar equivalence, conjunction boolean-projection, deferred `refill_consistent` timing symmetry, mirrored-direction, or unsupported-ordered-relation-block inspection. This is an expected `partial` state per the iteration's DEFINITION OF DONE, not a defect.

### UT-J-04 — Foundry owns the denominator, append-only state, freeze barrier, and integrity lock
**Verdict:** SKIPPED
**Reason:** Same by-design deferral as UT-J-03. No Freeze/Integrity or family-denominator fixture subview exists under the Hypothesis Foundry panel this iteration; the iteration spec's IN SCOPE section builds only the hermetic backend modules (`foundry_interpreter.py`, `foundry_family.py`, `foundry_freeze.py`, `foundry_ledger.py`, `foundry_runner.py`) with "None" listed under Frontend, and DEFINITION OF DONE explicitly expects J-04 to remain/move to `partial` this iteration. Live-verified via the same panel expansion — no such subview present.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Headless Chrome via MCP (CDP attached at 127.0.0.1:9222)
- **Test Date:** 2026-08-26
- **Evidence directory:** `reports/qa/goal-hypothesis-foundry-iter-2-evidence/`

## Golden Replay Scripts

- `runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json` — written and lint-passed
  (`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-hypothesis-foundry/journey-scripts --journeys J-01` → `J-01 ok`). Asserts the real `config_fingerprint`
  value `08e471b10130e1e2` post-expansion as the final acceptance check.
- No golden written for J-03/J-04 (SKIPPED — no UI surface to script this iteration).
