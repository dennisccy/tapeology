# Phase goal-hypothesis-foundry-iter-6 — UI Test Results

**Phase:** goal-hypothesis-foundry-iter-6
**Date:** 2026-08-27
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 tests passed (0 skipped)

---

## Environment note (read before the table)

The backend on `:8301` (the scoped QA rig) was down (connection refused) when this run started,
despite the frontend on `:3301` being up and Chrome CDP (`:9222`) responding. The orchestrating
wrapper's own seed/reseed attempt against the default fixture root failed
(`BarSeriesAlreadyRegistered` — the default root
`playbook-iter8-replay-fixture-qa` already held a fully-seeded, previously-verified state from
earlier in this iteration, and the seeder is not idempotent against a non-empty root). Recovery:
started `apps/backend/.venv/bin/uvicorn` directly (via `scripts/start-backend.sh`) against that
**already-seeded, already-verified** root's exact `TAPEOLOGY_*` store-scope env vars (same values
the rig's own manifest/log had printed earlier), binding `:8301` — no reseed, no touch of the
operator's real `apps/backend/.data/` store. Confirmed immediately after start that
`GET /research/desk/micro/foundry`'s `exhaust_progress` block was byte-identical to the values this
test plan asserts (`first_read_lock_at: 2026-08-27T06:55:51.071173Z`,
`eligible_corpus_manifest_hash: da7488f8609c801f7a6f7c27c736e8a2a713e98f53b2d7006956c355df5c3260`,
`checkpoint_ordinal: 0`, `protected_read_count: 0`, `single_flight_status: "idle"`,
`freeze_integrity_verdict: "green"`, `exhaust_complete: true`) before any browser interaction began.
All 7 test cases below were then executed live against this backend.

**Known capture artifact (confirmed, not a product defect):** screenshots taken at a deep
`scrollY` (roughly beyond ~2500px) reliably come back **entirely blank** — reproduced twice
independently with this Chrome MCP tool during this run. Screenshots taken at `scrollY: 0` with an
enlarged viewport (per the test plan's own environment note) render correctly in most cases, but on
a very tall, fully-expanded page (all Hypothesis Foundry subsections open, ~6900px document height)
the tool's viewport cap (4320px max) still forces a partial scroll and the capture pipeline shows
some blank banding above/below the real content even at that shallower scroll. Every test below was
independently corroborated with DOM-text assertions (`document.body.textContent.includes(...)` /
`querySelector(...).textContent`) captured via `eval`, in addition to the screenshot — the report
says explicitly, per test, whether the saved screenshot is a clean full capture or a partial/best-
effort one backed by the DOM-text evidence.

**Regression lane note:** per the goal-mode dispatch, journeys J-01..J-06 already had deterministic
golden-replay coverage from before this run. Because the backend had to be restarted mid-dispatch, I
independently re-verified all six journeys' assertions live in-browser as part of UT-02/UT-05/UT-06
below (their content overlaps completely with the Hypothesis Foundry panel this iteration's change
lives in) rather than skipping them, so my rows supersede the replay's per this dispatch's own
instructions. I also wrote a new golden replay script for the new journey, **J-07**, at
`runs/goal-session-hypothesis-foundry/journey-scripts/J-07.json` (lint-checked clean via
`demo_runner.py --mode lint`).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads, Hypothesis Foundry panel present | smoke | P1 | Page renders, "Hypothesis Foundry" heading present (collapsed), no console errors, no `foundry-panel-unavailable` element | Page rendered fully; `[data-testid="desk-section-expand-hypothesisFoundry"]` found with text "▸Hypothesis Foundry"; `foundry-panel-unavailable` absent; console showed only the benign React DevTools info line | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-01-result.png` |
| UT-02 | Runner / Checkpoint shows the real exhaust state | happy-path | P1 | All 9 `foundry-runner-*` fields show the exact real values from `exhaust_progress`; empty/incomplete states absent | Every field matched verbatim (see detail below); `foundry-runner-checkpoint-empty` and `foundry-runner-exhaust-incomplete` both absent | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-02-result.png` (clean full capture, scrollY 0, enlarged viewport) |
| UT-03 | Every field is a real value, no placeholder leakage | validation | P2 | On-screen text is a byte-identical, unformatted echo of the API JSON; protected-read-count and freeze-integrity-verdict render `text-emerald-400`, not `text-rose-400` | `curl` of `GET /research/desk/micro/foundry` compared field-by-field against on-screen `eval` text — identical; `outerHTML` confirmed both lines use `class="font-mono text-emerald-400"`; hash shown full-length (64 hex chars), not truncated | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-03-result.png` |
| UT-04 | Backend outage shows honest error, not a crash | error | P2 | `foundry-panel-unavailable` appears with honest error text; rest of `/desk` stays functional; no fabricated `exhaust_progress` values | Simulated via a `window.fetch` override scoped to `*/research/desk/micro/foundry*` (see note below on tooling) + SPA remount: showed `foundry-panel-unavailable` = "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place."; no "Era-Open Baseline" / "0 of 0" anywhere; Desk Screen, Playbook, Backscan sections above it stayed fully visible and interactive | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-04-result.png` (clean full capture) |
| UT-05 | Sibling subsections unchanged | regression | P2 | Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic Oracles show their pre-existing text unchanged; no new `exhaust_progress`-related field leaks into them | All 4 confirmed present via DOM text; grep of every `[data-testid]` on the page for `foundry-runner` found only the legitimate `desk-section-expand-foundry-runner-checkpoint-section` header button — no leakage | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-05-result.png` (partial/best-effort capture — see note) |
| UT-06 | J-01..J-06 golden journeys replay clean | regression | P1 | All six journeys' exact assertions still hold | `08e471b10130e1e2` (J-01) present; "Era-Open Baseline" + "Hashes match — outcome-blind compilation proven." (J-02) present; "BLOCKED_UNSUPPORTED_RELATION" (J-03) present; "docs/hypothesis-foundry/freeze-set.json" (J-04) present; "Protected-data trip fails closed / evidence class immutable" (J-05) present; `epoch:afd19e9c11a6534f` (J-06) present | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-06-result.png` (partial/best-effort capture — see note) |
| UT-07 | Runner / Checkpoint discoverable in 2 clicks | ux | P3 | Reached in exactly 2 clicks; label unambiguous, sits below Epoch/Manifest; no duplicate rendering elsewhere | Fresh navigation → click `hypothesisFoundry` (1) → click `foundry-runner-checkpoint-section` (2) → target visible and populated; DOM order confirms `...epoch-manifest-section, runner-checkpoint-section` (Runner/Checkpoint immediately follows Epoch/Manifest); zero other occurrences of "Checkpoint: 0 of 0" text anywhere on the page | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-07-result.png` (clean full-page capture) |

---

## Passed Tests

### UT-01 — `/desk` loads and the Hypothesis Foundry panel is present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`; page rendered its full content (Desk Screen,
  Playbook Signals, Backscan, and every collapsed section list including "HYPOTHESIS FOUNDRY").
- `document.querySelector('[data-testid="desk-section-expand-hypothesisFoundry"]')` found, text
  `"▸Hypothesis Foundry"` (collapsed marker present).
- `document.querySelector('[data-testid="foundry-panel-unavailable"]')` → `null`.
- Console messages: only `info: Download the React DevTools...` — no errors.

### UT-02 — Operator can expand Runner / Checkpoint and see the real exhaust state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-02-result.png`
- Step 2 (click `desk-section-expand-hypothesisFoundry`): body text now includes "Era-Open
  Baseline". ✓
- Step 3 (click `desk-section-expand-foundry-epoch-manifest-section`): body text includes
  `epoch:afd19e9c11a6534f`. ✓
- Step 4 (click `desk-section-expand-foundry-runner-checkpoint-section`): `eval` read every field
  off `[data-testid="foundry-runner-checkpoint"]` and its children:
  - `foundry-runner-checkpoint-real-banner` = "Real Epoch — not a fixture"
  - `foundry-runner-first-read-lock` = "First-read lock recorded at: 2026-08-27T06:55:51.071173Z"
  - `foundry-runner-eligible-corpus-hash` = "Eligible-corpus manifest hash: da7488f8609c801f7a6f7c27c736e8a2a713e98f53b2d7006956c355df5c3260"
  - `foundry-runner-checkpoint-ordinal` = "Checkpoint: 0 of 0"
  - `foundry-runner-protected-read-count` = "Protected/withheld/sealed reads: 0"
  - `foundry-runner-single-flight-status` = "Runner lock: Idle — lock free"
  - `foundry-runner-freeze-integrity-verdict` = "Freeze integrity: green"
  - `foundry-runner-exhaust-complete` = "Exhaust complete — every frozen candidate reached a
    terminal state (zero FROZEN_READY variants this epoch — an honest, vacuous completion)."
  - All 9 values are an exact match to this iteration's spec/test-plan.
  - `foundry-runner-checkpoint-empty` and `foundry-runner-exhaust-incomplete` both absent (`null`).
- Screenshot is a **clean, fully-rendered capture** (viewport enlarged to 1400×4050, `scrollY: 0`,
  taken after collapsing the sibling Epoch/Manifest subsection so the target container's bottom
  edge fit inside the viewport cap) — cropping the saved PNG to the container's own bounding box
  confirms every line of text listed above is legible and correctly colored in the image itself,
  not just in the DOM.

### UT-03 — Runner / Checkpoint renders every field with a real value, no placeholder leakage
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-03-result.png`
- `curl -s http://localhost:8301/research/desk/micro/foundry` was compared field-by-field against
  the on-screen text captured in UT-02 — every value (`first_read_lock_recorded`,
  `first_read_lock_at`, `eligible_corpus_manifest_hash`, `frozen_ready_total`, `terminal_count`,
  `checkpoint_ordinal`, `protected_read_count`, `single_flight_status`,
  `freeze_integrity_verdict`, `exhaust_complete`) is echoed verbatim with no reformatting,
  truncation, or client-side recomputation.
- `outerHTML` of the two color-sensitive lines:
  - `<p data-testid="foundry-runner-protected-read-count">Protected/withheld/sealed reads: <span class="font-mono text-emerald-400">0</span></p>`
  - `<p data-testid="foundry-runner-freeze-integrity-verdict">Freeze integrity: <span class="font-mono text-emerald-400">green</span></p>`
  - Both use `text-emerald-400`; neither uses `text-rose-400`.
- Eligible-corpus hash rendered as the full 64-character hex string, not truncated.
- No occurrence of `undefined`, `NaN`, `[object Object]`, or an unexplained empty string anywhere
  in the subsection's text.

### UT-04 — Backend unavailability shows an honest error, not a blank/crashed panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-04-result.png`
- **Tooling note:** the Chrome MCP tool available in this environment
  (`mcp__plugin_superpowers-chrome_chrome__use_browser`) does not expose a DevTools-Network-tab-
  style request-blocking primitive (no CDP `Network.setBlockedURLs`/`Fetch` passthrough action).
  The test's intent (make requests to `*/research/desk/micro/foundry*` fail while leaving the
  shared `:8301` rig itself running for other tests) was reproduced functionally instead: a
  `window.fetch` override was installed via `eval` that rejects only requests whose URL contains
  `/research/desk/micro/foundry`, passing every other request through unmodified. Because this
  override lives on `window` and the app uses Next.js client-side routing (no full document
  reload), it was carried across an SPA navigation to `/` and back to `/desk` to force the Foundry
  panel's data-fetching component to remount and re-fetch — reproducing a genuine failed-fetch
  condition without ever taking the shared backend down for the rest of the plan.
- After the remount: `document.querySelector('[data-testid="foundry-panel-unavailable"]')` was
  present with text "Backend unreachable — is the API running?Nothing cached and nothing
  fabricated is shown in its place." — the panel's own served error text (one of the two accepted
  forms per the test plan).
- Body text confirmed to contain neither "Era-Open Baseline" nor "0 of 0" while the fetch was
  failing — no fabricated `exhaust_progress` values appeared.
- The rest of `/desk` (Desk Screen "not computed yet" panel, Playbook Signals, Backscan, and every
  other collapsed section) remained fully visible in the same screenshot — the panel failure did
  not crash the page.
- Cleanup: the override was disabled (`window.__foundryBlocked = false`) and then a full
  `navigate()` to `/desk` was issued, restoring the real, unblocked state for the remaining tests —
  the shared `:8301` rig was never actually stopped, satisfying the test's own cleanup step.

### UT-05 — Sibling Foundry subsections render unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-05-result.png`
- All four confirmed via `document.body.textContent.includes(...)`:
  - Sources / Compiler → "Hashes match — outcome-blind compilation proven." ✓
  - Interpreter Fixtures → "BLOCKED_UNSUPPORTED_RELATION" ✓
  - Freeze / Integrity → "docs/hypothesis-foundry/freeze-set.json" ✓
  - Hermetic Oracles → "Protected-data trip fails closed / evidence class immutable" ✓
- Grepped every `[data-testid]` on the page for the substring `foundry-runner`: the only match was
  the legitimate `desk-section-expand-foundry-runner-checkpoint-section` header button — no
  `exhaust_progress`-shaped field leaked into any of the four sibling subsections.
- **Screenshot note:** with all four siblings plus the era-open baseline expanded, the page's
  document height reached ~6900px, beyond this tool's 4320px viewport cap. The saved screenshot is
  a **partial/best-effort capture** (scrolled to bring "Sources / Compiler" into frame) — it does
  show real, legible content (the green "Hashes match — outcome-blind compilation proven." line is
  visible), but does not visually cover all four subsections in one image. The PASS verdict rests
  on the DOM-text assertions above, which cover all four independently and completely.

### UT-06 — J-01 through J-06 golden journeys replay clean
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-06-result.png`
- All six confirmed present via a single consolidated `eval` over `document.body.textContent`
  after re-expanding every subsection (including re-opening Epoch/Manifest, which a prior
  screenshot-troubleshooting step had toggled closed):
  - J-01: `08e471b10130e1e2` (product fingerprint) ✓
  - J-02: "Era-Open Baseline" + "Hashes match — outcome-blind compilation proven." ✓
  - J-03: "BLOCKED_UNSUPPORTED_RELATION" ✓
  - J-04: "docs/hypothesis-foundry/freeze-set.json" ✓
  - J-05: "Protected-data trip fails closed / evidence class immutable" ✓
  - J-06: `epoch:afd19e9c11a6534f` ✓
- None of J-01..J-06's assertions reference `exhaust`, `foundry-runner`, or "Runner / Checkpoint" —
  grep-confirmed against the existing golden scripts
  `runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json` through `J-06.json`, so this
  iteration's additive change cannot have altered their assertions; this run reconfirms that live.
- **Screenshot note:** same tall-page constraint as UT-05 — the saved image is a partial/best-
  effort capture (shows real, legible "Hashes match..." content, not blank) rather than a single
  frame covering all six confirmations. PASS rests on the DOM-text evidence above.
- No golden-script changes were needed for J-01..J-06 (pre-existing scripts already lint clean and
  their assertions were reconfirmed live). A new golden was written for the new journey this
  iteration introduces — see J-07 below.

### UT-07 — Runner / Checkpoint is discoverable in 2 clicks with an unambiguous label
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-07-result.png`
- Fresh navigation to `/desk`, then exactly 2 clicks — `desk-section-expand-hypothesisFoundry`
  (click 1) then `desk-section-expand-foundry-runner-checkpoint-section` (click 2), skipping every
  sibling subsection — landed directly on the populated `foundry-runner-checkpoint` element (text
  confirmed to include "Idle — lock free").
- DOM order of every `[data-testid^="desk-section-expand-foundry-"]` element confirms Runner /
  Checkpoint is the last subsection and immediately follows Epoch / Manifest:
  `sources-compiler, interpreter-fixtures, freeze-integrity, hermetic-oracles, epoch-manifest,
  runner-checkpoint` — matching the spec's placement.
- Zero other occurrences of the string "Checkpoint: 0 of 0" anywhere on the page — no duplicate or
  conflicting rendering of the same data.
- Screenshot is a **clean, full-page capture** (viewport 1400×4320, scrollY 0) showing the entire
  page from the top nav down through the fully-expanded, fully-populated Runner / Checkpoint
  subsection at the bottom in one image.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Journey coverage note (goal-mode)

- **J-01..J-06:** independently re-verified live in-browser this run (see UT-02/UT-05/UT-06 above);
  all six still pass. Existing golden scripts at
  `runs/goal-session-hypothesis-foundry/journey-scripts/J-0{1..6}.json` were not modified — their
  assertions were reconfirmed, not changed.
- **J-07 (new this iteration):** verified PASS via UT-02/UT-06's flow. New golden replay script
  written to `runs/goal-session-hypothesis-foundry/journey-scripts/J-07.json`:
  ```
  {"schema_version":1,"journey":"J-07","name":"Goal Mode deterministically exhausts the frozen real epoch without changing science", ...}
  ```
  4 steps: goto `/desk` → expand Hypothesis Foundry (expect "Era-Open Baseline") → expand
  Epoch/Manifest (expect `epoch:afd19e9c11a6534f`) → expand Runner/Checkpoint (expect "Runner
  lock: Idle — lock free"). Lint-checked clean:
  `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
  runs/goal-session-hypothesis-foundry/journey-scripts --journeys J-07` → `J-07 ok`.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL (scoped QA rig):** http://localhost:8301 (restarted mid-dispatch — see
  Environment note above; served the exact real, previously-verified `exhaust_progress` state
  throughout all 7 tests)
- **Browser:** Chrome (headless) via `mcp__plugin_superpowers-chrome_chrome__use_browser`,
  attached to the pre-existing CDP endpoint at `http://127.0.0.1:9222`
- **Test Date:** 2026-08-27
- **Evidence directory:** `reports/qa/goal-hypothesis-foundry-iter-6-evidence/`
- **Console errors observed across the entire session:** none (only the benign React DevTools
  info-level message)
