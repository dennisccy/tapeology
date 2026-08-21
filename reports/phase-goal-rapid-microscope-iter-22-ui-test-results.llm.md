# Phase goal-rapid-microscope-iter-22 — UI Test Results

**Phase:** goal-rapid-microscope-iter-22
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads with Scout Ledger + Walk-Forward present | smoke | P1 | Page renders, both section headers visible, no console errors | Page rendered fully; `desk-section-expand-scoutLedger` and `desk-section-expand-walkForward` both present via selector query and visible in screenshot directly below "MICROSCOPE READINESS"; no console errors captured | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-01-result.png` |
| UT-02 | Study 1 screens and appears on `/desk` | happy-path | P1 | Family `failed_aggression_score__band_touch__trades_20` visible with trial row Feature `failed_aggression_score / threshold (band_touch)` and non-blank Decision | POST triggered run reached `state:"done"`; `GET /scout` showed the family; browser confirmed family block + trial row text `failed_aggression_score / threshold(band_touch)`, Decision `killed_insufficient_n` (non-blank) | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-02-result.png` |
| UT-03 | Study 3 screens and appears on `/desk` | happy-path | P1 | Family `failed_aggression_score__playbook_signal__trades_20` visible, Study 1 family still present (additive) | POST triggered run reached `state:"done"`; browser confirmed new family block, trial row Feature `failed_aggression_score / threshold(playbook_signal)`, non-blank Decision; Study 1's family block still visible in same ledger | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-03-result.png` |
| UT-04 | Both new studies record an honest floor-check row | validation | P1 | In both families, second row Feature/Horizon = `—`, Decision = `killed_insufficient_n` exactly; `screen_result` detail shows `null` | Both families' second rows confirmed: Feature/Horizon `— / —`, Decision `killed_insufficient_n`; opened the `<details>` for the floor-check row (band_touch family) and confirmed body text `null` | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-04-result.png` |
| UT-05 | Unrecognized `grid` value still 500s | error | P2 | HTTP 500; `/desk` unaffected on refresh | `curl` returned `500`; compute-manager state remained `done` (not stuck); `/desk` reloaded cleanly with no error banner | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-05-result.png` |
| UT-06 | "Run Screen" button still only runs the default grid | regression | P1 | Request body carries no `grid` field; new rows have no `(band_touch)`/`(playbook_signal)` suffix; no new `killed_insufficient_n`/`—` floor-check row | `fetch` monkey-patch showed the POST call's `opts.body` was `undefined` (no body/no grid field at all); run produced 3 new families (`cumulative_delta__none`, `failed_aggression_score__none`, `quote_imbalance__none`), all `structure_context.kind == "none"`, no `stage=="walkforward_floor_check"` row among them (confirmed via API + on-screen) | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-06-result.png` |
| UT-07 | Study 2's floor-check row still renders, freshly confirmed | regression | P1 | `divergence_at_level_bearish__band_touch__trades_20` family's second row shows `—`/`—`, Decision `killed_insufficient_n`, dated this iteration | Triggered a fresh `delta_divergence_pilot` run this session (registered timestamp `2026-08-20 18:47 ET`); family + floor-check row confirmed on screen, screenshot dated today | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-07-result.png` |
| UT-08 | J-07 Graduation surface unaffected, freshly confirmed | regression | P1 | HTTP 200; `families` non-empty with `family`/sealed reading (`verdict`,`rule_hash`)/`n`; unchanged shape | Browser navigated directly to `GET /research/desk/micro/graduation`; body rendered in Chrome's JSON viewer showing `family_root_id`, `sealed_evaluations[0].verdict:"pass"`, `rule_hash`, `n:30` | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-08-result.png` |
| UT-09 | Neither new study has an on-screen control | ux | P2 | Zero matches for both grid-selector strings anywhere on page; no dropdown/radio near "Run Screen" | Full-DOM text search: 0 hits for `range_wall_failed_aggression_pilot` and `capitulation_exhaustion_pilot`; 0 `<select>`/`input[type=radio]` elements anywhere on the whole page | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-09-result.png` |
| UT-10 | CLI path independently produces the same rows | smoke | P2 | stdout `1 candidate(s) processed`; on-disk ledger has screen row (closed-vocab decision, `structure_context.kind=="band_touch"`) + `walkforward_floor_check` row (`decision=="killed_insufficient_n"`) | Ran `.venv/bin/python -m app.research.scout --grid range_wall_failed_aggression_pilot` against fixture-pointed env-var dirs (scratchpad, never `.data/`); stdout matched exactly; on-disk `ledger.jsonl` held exactly 2 rows matching spec | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-10-ledger.jsonl` (terminal-only test; no browser surface) |

---

## Passed Tests

### UT-01 — `/desk` loads with Scout Ledger and Walk-Forward sections present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`; page rendered with no blank screen, no error banner.
- `document.querySelector('[data-testid="desk-section-expand-scoutLedger"]')` and `...walkForward` both resolved (`textContent`: "▸Scout Ledger", "▸Walk-Forward"), directly adjacent in DOM order below "Microscope Readiness".
- No console errors observed.

### UT-02 — Operator can screen Study 1 (range-wall failed aggression) and see it on `/desk`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-02-result.png`
- `POST /research/desk/micro/scout/compute {"grid":"range_wall_failed_aggression_pilot"}` against a freshly-launched scoped backend (verified `GET /scout` showed zero families beforehand) returned `{"state":"running","run_id":...}`, polled to `"state":"done"` (1 candidate).
- `GET /research/desk/micro/scout` confirmed the family `failed_aggression_score__band_touch__trades_20` with a screen row (`decision:"killed_insufficient_n"`, `structure_context.kind:"band_touch"`).
- Browser: expanded Scout Ledger, confirmed `[data-testid="scout-family-failed_aggression_score__band_touch__trades_20"]` present with trial-row text `failed_aggression_score / threshold(band_touch)` / `trades_20` / Decision `killed_insufficient_n` (non-blank).

### UT-03 — Operator can screen Study 3 (capitulation exhaustion) and see it on `/desk`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-03-result.png`
- `POST .../scout/compute {"grid":"capitulation_exhaustion_pilot"}` (same backend, UT-02's run already `done`) reached `"state":"done"`.
- Browser confirmed family `failed_aggression_score__playbook_signal__trades_20` with trial-row Feature `failed_aggression_score / threshold(playbook_signal)`, Decision `killed_insufficient_n` (non-blank).
- Study 1's family block (`...band_touch__trades_20`) was still present in the same Scout Ledger view — confirms additive behavior, not a replace.

### UT-04 — Both new studies record an honest walk-forward floor-check row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-04-result.png`
- Both families' second trial row (sharing the same Candidate ID as their screen row) show Feature/Horizon `— / —` and Decision `killed_insufficient_n` exactly.
- Opened the `<details>` element for the band_touch family's floor-check row via its `summary.click()`; the disclosed body read `null` — the floor-check row carries no `screen_result` payload of its own, as specified.

### UT-05 — An unrecognized `grid` value still surfaces a raw server error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-05-result.png`
- `curl -X POST .../scout/compute -d '{"grid":"not_a_real_selector"}'` returned HTTP `500` — unchanged pre-existing, disclosed limitation (iter-21 audit finding B5), not a new regression.
- Compute-manager state was unaffected (remained `"done"` from the prior run, not stuck).
- `/desk` reloaded normally afterward with no error banner, heading "Desk" present.

### UT-06 — The shipped "Run Screen" button still triggers only the unchanged default grid
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-06-result.png`
- Patched `window.fetch` before clicking `[data-testid="scout-ledger-trigger"]` ("Run Screen"); the captured POST call to `/scout/compute` had `opts.body === undefined` — no `grid` field of any kind is sent by the button (stronger than the "or `grid: null`" allowance).
- Run completed (6 candidates, default grid); resulting API state showed 3 new families (`cumulative_delta__none__trades_20`, `failed_aggression_score__none__trades_20`, `quote_imbalance__none__trades_20`), every trial's `structure_context.kind == "none"` (no `(band_touch)`/`(playbook_signal)` suffix anywhere), and no `stage == "walkforward_floor_check"` row among any of them.
- Confirmed the same on screen after refresh + re-expand: button label reverted to "Run Screen", all three new family blocks visible with plain "threshold" Feature labels only.

### UT-07 — Study 2's walk-forward floor-check row is still visible, freshly confirmed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-07-result.png`
- Triggered `{"grid":"delta_divergence_pilot"}` fresh this session (registered `2026-08-20 18:47 ET`, not a reused iter-21 timestamp).
- Family `divergence_at_level_bearish__band_touch__trades_20` visible; its second row shows `— / —` and Decision `killed_insufficient_n` exactly, matching iter-21's fixed behavior.
- Screenshot captured this iteration (dated 2026-08-20), showing all six families accumulated over the session (both new pilot studies, the default-grid families, and Study 2), confirming no cross-family interference.

### UT-08 — J-07 Graduation surface is unaffected and freshly re-confirmed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-08-result.png`
- Browser navigated directly to `http://localhost:8301/research/desk/micro/graduation`; HTTP 200, body rendered in Chrome's built-in JSON viewer.
- `families` array non-empty (1 entry): `family_root_id: "240dd966c1aceca2"`, `sealed_evaluations[0]` carries `verdict: "pass"`, `rule_hash: "8aaea80b..."`, `n: 30` — matches the shape description exactly (family identifier + sealed reading + observation count).
- Fresh, iter-22-dated capture (2026-08-20), not a reused iter-20 asset.

### UT-09 — Neither new study is discoverable as an on-screen control
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-09-result.png`
- Full-DOM text search (`document.body.textContent`) for `range_wall_failed_aggression_pilot` and `capitulation_exhaustion_pilot`: 0 matches for both (a stronger check than Ctrl+F since it also covers any hidden/rendered-but-offscreen text).
- `document.querySelectorAll('select, input[type=radio]')`: 0 elements anywhere on the whole page — confirms no dropdown/radio group exists near "Run Screen" or anywhere else. The trigger surface is a single unadorned button.

### UT-10 — The CLI path independently produces the same ledger rows as the route
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-10-ledger.jsonl` (raw on-disk ledger captured as evidence; terminal-only test, no browser surface per the test plan's own note)
- Replicated the dev handoff's own CLI fixture recipe: copied `tests/fixtures/datasets/*.json` + `tests/fixtures/datasets_j03/*.json` into a scratch dataset dir, pointed `TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_MICRO_SCOUT_DIR`/`TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR` env vars at fresh scratchpad directories (never `.data/`).
- Ran `.venv/bin/python -m app.research.scout --grid range_wall_failed_aggression_pilot` from `apps/backend`; stdout: `scout screen complete: 1 candidate(s) processed; ledger=...`.
- On-disk `ledger.jsonl` contained exactly 2 rows under the same `candidate_id`: one screen-stage row (`structure_context.kind: "band_touch"`, `decision: "killed_insufficient_n"`), one `stage: "walkforward_floor_check"` row (`decision: "killed_insufficient_n"`) — proving the CLI path independently, not only the HTTP route.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden Replay Scripts

**Not written this iteration for J-09 or J-07 — structural incompatibility with the replay format, not a test failure.**

- **J-09**: its acceptance requires `POST /research/desk/micro/scout/compute` calls (UT-02/UT-03)
  that have no on-screen control (UT-09 confirms this by design) — the demo_runner replay format
  only supports `goto`/`click`/`fill` actions, none of which can issue a raw POST. A pure-browser
  replay script cannot reproduce the required ledger mutation.
- **J-07**: its acceptance surface is `GET http://localhost:8301/research/desk/micro/graduation` —
  the backend's own port, not the frontend's. `demo_runner.py`'s `normalize_url` forcibly rewrites
  any absolute `localhost`/`127.0.0.1` URL onto the replay's single `base_url` host:port (by
  design, to fix the offset-dev-port problem for the frontend), and relative `goto` paths always
  resolve against that same single base_url. There is no frontend route or Next.js proxy serving
  this backend JSON, so the endpoint is unreachable from a single-base-url replay script.

Both are genuinely re-verified this iteration via live Chrome MCP interaction (see UT-02/03/04/06/07
for J-09, UT-08 for J-07) — only the fast-path deterministic-replay shortcut is unavailable for
these two journeys. Per the "best-effort" rule, they fall back to a full browser-qa pass next time.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (scoped QA fixture store, never `.data/`)
- **Browser:** Chrome via MCP (headless, CDP `127.0.0.1:9222`)
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-22-evidence/`

## Sequencing Note (honored)

Per the phase spec's binding "Do not redo" rig rule, the deterministic golden-replay lane
(J-01…J-05, J-08, J-10) had already been run against a clean backend before this browser-qa pass
began (per the dispatch note: "Deterministic replay has ALREADY re-verified these... Do NOT
re-test them"). All of this test plan's mutating steps (UT-02, UT-03, UT-06, UT-07) were run only
after that, on the freshly-launched scoped QA backend instance confirmed empty at UT-02's
precondition check (`GET /scout` returned zero families, compute state `idle` before the first
POST).
