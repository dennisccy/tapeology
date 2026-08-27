# Goal Iteration 9 (hypothesis-foundry) — UI Test Results

**Phase:** goal-hypothesis-foundry-iter-9
**Date:** 2026-08-27
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped) — J-01 and J-08 live-browser-verified this run (Chrome
MCP); J-02..J-07 verified by the deterministic golden replay that ran separately this iteration
(see `reports/phase-goal-hypothesis-foundry-iter-9-regression-replay-results.md`), per the dispatch
instruction not to re-drive those via a browser-driving model this pass.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The Foundry opens as a new finite era and the old self-extension loop is inactive | regression | P1 | Panel identifies Rapid Microscope as closed foundation and the Foundry era/session separately; archived RM goal + dated opening note exist and `runs/goal-session-rapid-microscope/` is untouched; the two-file proposer-dispatch condition no longer holds; era-open baseline shows full-suite pass/skip, config fingerprint, and Referee-module SHA-256s | Live Chrome MCP: `/desk` → expanded "HYPOTHESIS FOUNDRY" shows "Previous era: rapid-microscope (closed)" / "Current era: hypothesis-foundry (active)", Era-Open Baseline block shows "Backend suite: 3787 passed · 8 skipped · 0 failed", "tsc --noEmit errors: 0", "Config fingerprint: 08e471b10130e1e2", and a 6-row Referee Module SHA-256 table. Filesystem checks: `docs/goal-archive/goal-2026-08-26.md` exists (archived RM predecessor goal); `docs/research-directions.md` §"HYPOTHESIS-FOUNDRY OPENING NOTE (2026-08-26, operator pivot...)" exists; `runs/goal-session-rapid-microscope/` last-modified Aug 26 15:34, untouched by this iteration; `project-extensions/proposer-guidance.md` no longer exists (archived to `docs/goal-archive/proposer-guidance-2026-08-26.md`), so `run-goal.sh`'s two-file dispatch condition (`--proposer` flag AND that file's presence, `scripts/automation/run-goal.sh:3369`) no longer holds | PASS | reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-01-result.png |
| UT-J-02 | Ratified sources compile into auditable CandidateSpecs or typed blocks without outcome input | regression | P1 | journey replays end-to-end; all expects hold | Deterministic golden replay (demo_runner.py, this iteration) reported PASS — journey replayed end-to-end, all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-02-verify.png |
| UT-J-03 | Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions | regression | P1 | journey replays end-to-end; all expects hold | Deterministic golden replay (demo_runner.py, this iteration) reported PASS — journey replayed end-to-end, all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-03-verify.png |
| UT-J-04 | Foundry owns the denominator, append-only state, freeze barrier, and integrity lock | regression | P1 | journey replays end-to-end; all expects hold | Deterministic golden replay (demo_runner.py, this iteration) reported PASS — journey replayed end-to-end, all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-04-verify.png |
| UT-J-05 | The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles | regression | P1 | journey replays end-to-end; all expects hold | Deterministic golden replay (demo_runner.py, this iteration) reported PASS — journey replayed end-to-end, all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-05-verify.png |
| UT-J-06 | One complete real epoch is generated and committed with zero Foundry outcome reads | regression | P1 | journey replays end-to-end; all expects hold | Deterministic golden replay (demo_runner.py, this iteration) reported PASS — journey replayed end-to-end, all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-06-verify.png |
| UT-J-07 | Goal Mode deterministically exhausts the frozen real epoch without changing science | regression | P1 | journey replays end-to-end; all expects hold | Deterministic golden replay (demo_runner.py, this iteration) reported PASS — journey replayed end-to-end, all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-07-verify.png |
| UT-J-08 | The operator sees the final Foundry truth and all foundation rails still hold | regression | P1 | `/desk` → Hypothesis Foundry final summary shows source/family/variant/integrity/multiplicity/evidence/runner state; a blocked source's canonical-provenance detail renders verbatim (no advisory copy); honest zero-survivor state is explicit if no survivor exists; REST body matches UI values; suite/tsc/leakage/opacity guards remain green | Live Chrome MCP: expanded "FINAL SUMMARY" shows source counts by disposition (7 distinct dispositions across 11 required objects, 0 `COMPILED`), "Family count: 0", "Variant count: 0", "Frozen-ready total: 0", "Evidence class: historical_exposed_diagnostic", "Protected/withheld/sealed reads: 0", "Freeze integrity: green", "Epoch status: committed", and the explicit "Zero diagnostic survivors exist for this epoch (diagnostic_survivor_count = 0)" / "Exhaust complete ... an honest, vacuous completion" copy — no `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` claimed since none exist. Opened the `card-9.3-top-of-book-imbalance` (`BLOCKED_DIRECTION`) source's "Canonical provenance" `<details>` — rendered its quoted mechanism statement, source hash, and an audit note explaining the block under §2.2 without result-dependent rationale (no evaluated variants exist to open, since variant count = 0, satisfying the journey's "if any exist" clause). `curl GET /research/desk/micro/foundry` byte-contains the same `source_registry_hash`, `config_fingerprint`, and every final-summary field value seen in the UI. No `desk_micro_foundry` MCP tool exists in `apps/backend/app/mcp/` (grep empty) — consistent with the goal's "deferrable, non-blocking" status for the optional MCP proxy. Suite/tsc/leakage-trap re-run is corroborated by `docs/handoffs/goal-hypothesis-foundry-iter-9-dev.md` (3930 passed / 8 skipped / 0 failed backend suite, 0 tsc errors, this iteration) — outside direct browser-QA scope but consistent and cross-checked. Zero browser console errors (only the standard React DevTools info line). | PASS | reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-08-result.png |

---

## Passed Tests

### UT-J-01 — The Foundry opens as a new finite era and the old self-extension loop is inactive
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-01-result.png`
- Navigated to `http://localhost:3301/desk`, confirmed "Hypothesis Foundry" section present (collapsed, at bottom of Desk sections), clicked `[data-testid="desk-section-expand-hypothesisFoundry"]` to expand.
- Panel text: "Previous era: rapid-microscope (closed)" and "Current era: hypothesis-foundry (active)" — era boundary explicit and separate.
- Era-Open Baseline block: "Backend suite: 3787 passed · 8 skipped · 0 failed", "tsc --noEmit errors: 0", "Config fingerprint: 08e471b10130e1e2", and a Referee Module SHA-256 table (6 modules: `referee_adjudicate.py`, `referee_evidence.py`, `referee_null.py`, `referee_registry.py`, `referee_routes.py`, `referee_stats.py`).
- Filesystem corroboration: `docs/goal-archive/goal-2026-08-26.md` present (archived Rapid Microscope predecessor goal, matches the goal file's own "Predecessor archived at" pointer); `docs/research-directions.md` contains the dated "HYPOTHESIS-FOUNDRY OPENING NOTE (2026-08-26, operator pivot, under §5.6 'goal.md wins')"; `runs/goal-session-rapid-microscope/` last-modified Aug 26 15:34 (before this iteration's work, i.e. untouched); `project-extensions/proposer-guidance.md` no longer exists (moved to `docs/goal-archive/proposer-guidance-2026-08-26.md`, preserving history rather than rewriting it), and `scripts/automation/run-goal.sh` line ~3369 shows the dispatch condition requires both `--proposer` and that now-absent file, so the old proposer no longer dispatches for this era.
- Zero console errors.

### UT-J-08 — The operator sees the final Foundry truth and all foundation rails still hold
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-08-result.png`
- From the expanded "HYPOTHESIS FOUNDRY" panel, clicked `[data-testid="desk-section-expand-foundry-final-summary-section"]` to expand "FINAL SUMMARY".
- Source counts by disposition (7 distinct dispositions, 11/11 required objects): `ALIASED_PROXY_ONLY: 2`, `BLOCKED_DIRECTION: 4`, `BLOCKED_SPEC_GAP: 1`, `ALIASED_VARIANT_VOCABULARY: 1`, `EXCLUDED_PREVIOUSLY_KILLED: 1`, `EXCLUDED_PREREQUISITE_UNMET: 1`, `EXCLUDED_GATE_CLOSED: 1`. No source is `COMPILED`, so Family count / Variant count / Frozen-ready total are all `0`.
- Evidence class `historical_exposed_diagnostic`, Protected/withheld/sealed reads `0`, Freeze integrity `green`, Epoch status `committed`.
- Explicit honest zero-survivor copy: "Zero diagnostic survivors exist for this epoch (diagnostic_survivor_count = 0) -- no candidate reached DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN this era." and "Exhaust complete -- every frozen candidate reached a terminal state (zero FROZEN_READY variants this epoch — an honest, vacuous completion)." No survivor label is shown (none exist), and no OOS/Referee-readiness claim appears anywhere.
- Opened the blocked source `card-9.3-top-of-book-imbalance` (`BLOCKED_DIRECTION`) via its "Canonical provenance" `<summary>` toggle: rendered a quoted mechanism statement, source hash, and an audit note citing §2.2 ("inventing a direction not mechanically implied by the ratified statement... would be exactly that") — canonical provenance/status/audit copy, not advisory trading language, and no result-dependent rationale. Since variant count = 0, there is no evaluated-variant detail view to open this epoch (journey's "if any exist" clause is honestly satisfied by absence).
- REST parity: `curl -s http://localhost:8301/research/desk/micro/foundry` contains the exact `source_registry_hash` (`ed40dbc25e8fdb961258512dc01ccbaa4633e0ddb6f374288c6c78d681bd098d`) and `config_fingerprint` (`08e471b10130e1e2`) shown in the UI, plus `family_count`, `variant_count`, `frozen_ready_total`, `evidence_class`, `freeze_integrity`, `epoch_status`, and `diagnostic_survivor_count` keys with the same values rendered on screen — one canonical backend owner, no client recomputation observed.
- MCP: `grep -rn "foundry" apps/backend/app/mcp/*.py` returns nothing — no `desk_micro_foundry` tool exists. Per `docs/goal.md`, this optional read-only proxy is deferrable and does not block `GOAL_ACHIEVED` as long as REST + `/desk` are complete, which they are.
- Backend suite / TypeScript compile / leakage-trap re-run is not directly browser-drivable; corroborated via `docs/handoffs/goal-hypothesis-foundry-iter-9-dev.md` (this iteration): backend suite 3930 passed / 8 skipped / 0 failed (matches iter-8 exactly, the one first-run flake in `test_tick_recorder.py` was investigated by the developer and confirmed to be a pre-existing wall-clock-dependent flake unrelated to this era, reproduced clean on 2 immediate re-runs), `npx tsc --noEmit` 0 errors.
- Zero console errors (only the standard React DevTools info line).

### UT-J-02 through UT-J-07 — stable, digested journeys
**Verdict:** PASS (all six)
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-9-evidence/J-0{2..7}-verify.png`
Per this dispatch's explicit instruction ("Do NOT test these — a deterministic replay verifies them
separately"), these six journeys were not re-driven with a browser-driving model this run. They were
verified this same iteration by the deterministic golden-script replay (`demo_runner.py`, verify
mode) against the checked-in scripts in
`runs/goal-session-hypothesis-foundry/journey-scripts/J-0{2..7}.json`, which reported 8/8 PASS with
0 skips in `reports/phase-goal-hypothesis-foundry-iter-9-regression-replay-results.md` (timestamped
minutes before this browser-qa pass began). No code changed this iteration (confirmed via dev
handoff `git diff --stat`), so there is no plausible drift between that replay and a fresh live
pass for these six.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden Replay Scripts

`J-01.json` and `J-08.json` in `runs/goal-session-hypothesis-foundry/journey-scripts/` were
confirmed valid against this run's live DOM (both selectors used —
`[data-testid="desk-section-expand-hypothesisFoundry"]` and
`[data-testid="desk-section-expand-foundry-final-summary-section"]` — matched and produced the
expected text on the first try) and are left as-is (no change needed; still accurate for this
iteration's zero-diff state). `J-02.json`..`J-07.json` were not touched by this dispatch (out of
scope per "Do NOT test").

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (CDP attach on pinned port 9222, headless)
- **Test Date:** 2026-08-27
- **Evidence directory:** `reports/qa/goal-hypothesis-foundry-iter-9-evidence/`
- **Commit under test:** `2599cb0a` (owner dispositions applied; zero code changes this iteration)
