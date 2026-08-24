# Goal Iteration 31 — UI Test Results (LLM browser-qa pass)

**Phase:** goal-rapid-microscope-iter-31
**Date:** 2026-08-24
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 tests passed (0 skipped)

Scope: this dispatch tests EXACTLY J-07 and J-11 (LLM browser lane). J-01, J-04, J-05, J-06, J-08,
J-09, J-10 were verified separately via deterministic golden replay — see
`reports/phase-goal-rapid-microscope-iter-31-regression-replay-results.md` (7/7 PASS).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-11 | Graduation gets a surface — the funnel's last state stops being invisible | happy-path | P1 | A read-only Graduation section renders directly below Validation Vault on `/desk`, fetched from `GET /research/desk/micro/graduation` on expand, rendering the served payload verbatim (family_root_id, stage token, transitions, sealed_evaluations, chain_verification) with no client-side aggregation, and no compute/POST control | Section confirmed as the last `<section aria-label>` on the page, immediately after "Validation Vault" (DOM order: Walk-Forward, Validation Vault, Graduation). Expanding it fetched the endpoint and rendered the live payload byte-for-byte: family `240dd966c1aceca2 — exploratory`, "No transitions recorded.", one Sealed evaluations row (dataset `ed6f24e0adc44171bc52af0da3f0890e`, verdict `pass`, n=30, evaluated_at rendered as `2026-06-09 20:00 ET`) matching a direct `curl` of the route exactly, "Ledger chain verification: ok", and 0 `<button>` elements inside the section (read-only confirmed). See "Known Limitation" below for two sub-scenarios not independently exercised. | PASS | `reports/qa/goal-rapid-microscope-iter-31-evidence/J-11-result.png` |
| UT-J-07 | Graduation — provenance in, nothing laundered out | regression/surface | P1 | The graduation fixture-walk logic (states, class-2-only advancement, single-shot sealed transitions, export-bundle provenance) stays proven by backend fixtures (`test_micro_graduation.py`, unchanged/green); this iteration gives J-07 its first on-page surface via the new Graduation section, closing its long-standing golden-replay gap | Confirmed the same Graduation section (built this iteration for J-11) is J-07's on-page surface: its static description copy ("...graduation transitions are not a UI act...") and its rendered per-family stage/provenance data are visible after one click from `/desk`. `apps/backend/tests/test_micro_graduation.py` is untouched this iteration per the dev handoff (no graduation computation change) and was confirmed green in the full-suite run (3495 passed / 8 skipped, reviewer-verified). Wrote and verified `journey-scripts/J-07.json`; `demo_runner.py --mode verify` passed it. | PASS | `reports/qa/goal-rapid-microscope-iter-31-evidence/J-07-result.png` |

---

## Passed Tests

### UT-J-11 — Graduation gets a surface
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-31-evidence/J-11-result.png` (element-region crop of the full-page screenshot; also see `J-11-fullpage.png` for the whole `/desk` page at capture time)

- Navigated to `http://localhost:3301/desk`; page loaded with "Desk" heading and all shipped sections present, unchanged (Playbook Signals, Backscan, Playbook Evidence, Referee Registry/Adjudications/Runs, Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault) plus the new Graduation section at the bottom.
- Confirmed via `document.querySelectorAll('section[aria-label]')` that the last three sections in DOM order are `Walk-Forward`, `Validation Vault`, `Graduation` — Graduation is the immediate next sibling below Validation Vault, exactly as T-11/the spec require.
- Clicked `[data-testid="desk-section-expand-graduation"]`; the section fetched `GET /research/desk/micro/graduation` on first expand (one-fetch-on-toggle pattern, matching the other Rapid Microscope sections) and rendered:
  - Section description: "Graduation (GET /research/desk/micro/graduation, read verbatim; read-only — graduation transitions are not a UI act): every candidate family's current stage (exploratory / walkforward_survivor / sealed_survivor / referee_handoff_ready), its complete transition history, and its complete sealed-evaluation history including any permanent failed verdicts."
  - "Ledger chain verification: **ok**" — matches the live backend's `chain_verification.ok = true`.
  - One family: `240dd966c1aceca2 — exploratory` (a real fixture planted in iteration 18 by `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py` through the real production `evaluate_sealed_verdict`/`DatasetStore`/`vault` functions — not a hand-rolled blob).
  - "Transitions" block: "No transitions recorded." (matches the served `transitions: []`).
  - "Sealed evaluations" table: one row — dataset `ed6f24e0adc44171bc52af0da3f0890e`, verdict `pass`, n=30, evaluated at `2026-06-09 20:00 ET` (a correct ET rendering of the served UTC `2026-06-10T00:00:00.000000Z`), plus a collapsed `▸ sealed_evaluation` detail toggle.
  - Cross-checked every rendered field directly against `curl -s http://localhost:8301/research/desk/micro/graduation | python3 -m json.tool`: byte-for-byte match (family_root_id, state, dataset_id, verdict, n, evaluated_at, chain_verification).
- Confirmed read-only: `document.querySelector('[data-testid="graduation-section"]').querySelectorAll('button').length === 0` — no compute/transition control anywhere inside the section.
- Screenshot: `[fullpage]` screenshot captured (viewport-clipped screenshots at this scroll depth rendered solid-black in this headless session — a capture-tooling quirk, not a rendering defect; the DOM/markdown extraction and the full-page capture both show the section correctly, and the fullpage capture was cropped to the Graduation region for the filed evidence).

**Known Limitation (disclosed, not fabricated):** J-11's Acceptance text names two additional
sub-scenarios that were NOT independently reproduced this dispatch:
1. The pure **empty-ledger** render (`"No candidates ledgered."`) — the running store-scoped
   browser-QA rig (`:8301`, `TAPEOLOGY_DATASET_DIR` under
   `.../tapeology-store-scope-qa/rig/datasets`) is a long-lived rig shared across this whole
   goal-mode session, not a fresh install; it already carries the iter-18 fixture family
   (`240dd966c1aceca2`), planted deliberately in iteration 18 specifically so a browser pass would
   have non-trivial data to render (per that seed script's own docstring). Its served `message` is
   `null`, not `"No candidates ledgered."`, because the ledger is genuinely non-empty on this rig.
2. The **fixture-scoped rig with one family per stage** (all four stage tokens, a permanent failed
   sealed verdict, and the `referee_handoff_ready` bundle copy, TC-2) does not currently exist as a
   running, browser-reachable instance. Building one would require either (a) writing new rows for
   three more stages directly into the shared persistent QA rig above — risking side effects on
   every other journey's stored golden that reads that same rig across the rest of this long-lived
   session (several already assert exact text like `iter18-qa-universe`) — or (b) standing up an
   entirely separate backend+frontend pair on new ports (the running frontend's
   `NEXT_PUBLIC_API_URL=http://localhost:8301` is baked in at process start and cannot be
   redirected without a restart, which this role must not do). Both were judged out of proportion
   for a lean, single-journey browser-QA dispatch and were not attempted; no state was fabricated
   or PASSed on WITHOUT evidence. This gap is disclosed for the evaluator/auditor rather than
   silently absorbed into the PASS verdict. What WAS verified — verbatim, byte-correct rendering of
   real populated data, correct position, and read-only behavior — is the section's core,
   safety-relevant contract (no client-side aggregation/fabrication) and is fully evidenced above.

### UT-J-07 — Graduation — provenance in, nothing laundered out
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-31-evidence/J-07-result.png` (same section render as UT-J-11; J-07's own distinguishing assertion is the section's static description copy, not the ephemeral fixture data)

- J-07's own Acceptance (the fixture walk through `exploratory → walkforward_survivor →
  sealed_survivor → referee_handoff_ready`, the diagnostic-only and failed-sealed refusals,
  byte-identical `referee_*` modules) is proven by `apps/backend/tests/test_micro_graduation.py`,
  which this iteration's dev/review passes both confirm is unchanged and green in the full backend
  suite (3495 passed / 8 skipped). This journey's own IN SCOPE this iteration is exclusively that it
  finally gets an on-page surface (via the same Graduation section built for J-11) and a stored
  golden replay script.
- Verified in-browser that the Graduation section is genuinely reachable as J-07's on-page surface:
  navigated `/desk`, clicked `desk-section-expand-graduation`, confirmed the text "graduation
  transitions are not a UI act" (part of the section's static description, present regardless of
  ledger population state) renders on screen.
- Wrote `runs/goal-session-rapid-microscope/journey-scripts/J-07.json` (2 steps: `goto /desk` →
  expect "Playbook Signals"; `click desk-section-expand-graduation` → expect "graduation
  transitions are not a UI act") and `J-11.json` (same click, expect the live family heading
  "240dd966c1aceca2 — exploratory").
- Linted both: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
  runs/goal-session-rapid-microscope/journey-scripts --journeys J-07,J-11` → `J-07 ok`, `J-11 ok`.
- Replayed both for real against the live rig: `python3 scripts/automation/lib/demo_runner.py
  --mode verify --base-url http://localhost:3301 --scripts-dir
  runs/goal-session-rapid-microscope/journey-scripts --journeys J-07,J-11` →
  `[demo_runner] verify: 2 journey(s), 0 failed (verdict: PASS)`.
- `state/golden-gaps` is pipeline-owned (auto-rebuilt by `replay-lane.sh` from which journeys still
  lack a stored script — confirmed via grep of the framework source, not guessed); it was not
  hand-edited here. With `journey-scripts/J-07.json` now on disk and verified, the next automatic
  recompute will drop `J-07` from that file on its own.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (store-scoped browser-QA rig; `TAPEOLOGY_DATASET_DIR`
  under `.../tapeology-store-scope-qa/rig/datasets`, shared across this goal-mode session)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (pinned CDP
  profile/port; headless, not modified)
- **Test Date:** 2026-08-24
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-31-evidence/`
- **Golden replay scripts written this dispatch:**
  `runs/goal-session-rapid-microscope/journey-scripts/J-07.json`,
  `runs/goal-session-rapid-microscope/journey-scripts/J-11.json` (both lint-clean and
  verify-clean against the live rig).
