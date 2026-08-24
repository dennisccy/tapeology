# Goal Iteration 32 — UI Test Results

**Phase:** goal-rapid-microscope-iter-32
**Date:** 2026-08-24
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped) — lean-mode dispatch scoped to J-11 only; J-01, J-04, J-05,
J-06, J-07, J-08, J-10 are verified separately by deterministic golden replay per the dispatch
instructions and were NOT re-tested here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-11 | Graduation gets a surface — the funnel's last state stops being invisible | happy-path | P1 | Capture 1: empty ledger shows "No candidates ledgered." + chain verification "ok". Capture 2: fixture rig shows all 4 stage tokens, Family B's permanent `fail` sealed verdict, and Family D's referee-handoff-ready note verbatim. | Both captures produced and verified against live DOM text; all TC-1..TC-4 assertions confirmed via `extract` before screenshotting. | PASS | `reports/qa/goal-rapid-microscope-iter-32-evidence/J-11-capture1-empty.png`, `reports/qa/goal-rapid-microscope-iter-32-evidence/J-11-capture2-fourstage.png` |

---

## Passed Tests

### UT-J-11 — Graduation gets a surface — the funnel's last state stops being invisible

**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-rapid-microscope-iter-32-evidence/J-11-capture1-empty.png`
- `reports/qa/goal-rapid-microscope-iter-32-evidence/J-11-capture2-fourstage.png`

**Setup performed (per iter-32 spec's Browser evidence section):**
1. Ran the dev-built seed script (`apps/backend/scripts/seed_micro_graduation_iter32_fourstage_fixture.py`)
   against a fresh scoped root `apps/backend/.data/qa-fixtures/goal-rapid-microscope-iter32-fourstage`
   — exit 0, all four families landed `[ok]` (A `exploratory`/`insufficient`, B
   `walkforward_survivor`/`fail`, C `sealed_survivor`/`pass`, D `referee_handoff_ready`/`pass`).
2. Captured the full running :8301 backend environment (174 vars, including every
   `TAPEOLOGY_*` rig path) before making any change, so each restart below preserves the rest of
   the store-scoped rig untouched and can be restored exactly.

**Capture 1 ("empty"):**
- Restarted :8301 with `TAPEOLOGY_MICRO_GRADUATION_DIR` pointed at a fresh, never-seeded root
  (`apps/backend/.data/qa-fixtures/goal-rapid-microscope-iter32-empty/graduation`). Confirmed via
  `GET /research/desk/micro/graduation` → `{"families":[],"message":"No candidates ledgered.",
  "chain_verification":{"ok":true,...}}`.
- Opened `/desk` (:3301), clicked `[data-testid="desk-section-expand-graduation"]`, awaited
  `[data-testid="graduation-families-block"]`, and extracted its text: confirmed
  `Ledger chain verification: ok` and the empty-state title `"No candidates ledgered."` are both
  on screen (TC-1 satisfied).
- Screenshot: full-page capture then cropped in place to the Graduation section (element-only
  screenshot capture hit a headless-Chrome rendering artifact on this run — see Known Issue below
  — full-page capture was the reliable path); saved to `J-11-capture1-empty.png`. Visually confirms
  the "GRADUATION" heading, "Ledger chain verification: ok", and the empty state "No candidates
  ledgered." in one frame.

**Capture 2 ("four-stage"):**
- Restarted :8301 with `TAPEOLOGY_MICRO_GRADUATION_DIR` pointed at the seeded fixture root's
  `micro_graduation` subdirectory. Confirmed via `GET /research/desk/micro/graduation` that all
  four families are present with the correct `family_root_id`/`state` pairs.
- Reloaded `/desk`, expanded Graduation, and extracted the section's full text — verified live:
  - `14ecf3e4610456cf — exploratory` (Family A), zero transitions, one sealed evaluation
    `verdict: insufficient`, `n: 29`.
  - `f9fb7652ae6c68ea — walkforward_survivor` (Family B), one transition
    (`exploratory → walkforward_survivor`), one sealed evaluation `verdict: fail`, `n: 30`,
    `failure_reason: below_economic_floor` — the state stayed `walkforward_survivor`, never
    advanced (TC-3 satisfied).
  - `0c46668c9c828643 — sealed_survivor` (Family C), two transitions, one sealed evaluation
    `verdict: pass`, `n: 30`.
  - `45cb3a975c062bc4 — referee_handoff_ready` (Family D), three transitions, one sealed
    evaluation `verdict: pass`, `n: 30`, and the referee-note block reading verbatim: "This
    referee_handoff_ready state does not imply the current Referee can register or adjudicate
    this candidate: a flow-context predicate requires a future named revision of
    docs/referee-statistical-spec.md. Where a candidate maps onto the existing referee vocabulary
    (setup, side, existing context predicates, existing measures), the bundle is registrable
    through the existing operator act unchanged." — byte-identical to the backend's
    `REFEREE_FUTURE_REVISION_SENTENCE` (TC-4 satisfied).
  - All four stage tokens (TC-2), the chain verification `ok`, and no client-side aggregation
    observed — every value traces to the served payload.
- Screenshot: full-page capture (after resetting scroll to 0, which fixed a rendering artifact —
  see Known Issue) cropped to the Graduation section's bounding box; saved to
  `J-11-capture2-fourstage.png`. Visually confirms all four family header lines with their stage
  tokens, Family B's `fail` row, and Family D's referee-note text in one frame.

**Restore:**
- Restarted :8301 back onto the captured original environment (no `TAPEOLOGY_MICRO_GRADUATION_DIR`
  override). `GET /research/desk/micro/graduation` reproduced byte-identical output to the
  pre-test baseline (`family_root_id: 240dd966c1aceca2`, `state: exploratory`, one `pass`
  sealed evaluation, `chain_verification.ok: true`) — the persistent rig's default graduation
  directory was left untouched by both scoped-root passes (TC-9 satisfied).
- Re-verified live at the restored state: `/desk` → expand Graduation → text still reads
  `240dd966c1aceca2 — exploratory` and the intro copy "graduation transitions are not a UI act"
  is present (the string J-07's existing stored golden asserts), and J-11's own existing/updated
  golden assertion (`240dd966c1aceca2 — exploratory`) still matches.

**Known Issue (tooling, not a product defect):** Chrome MCP's `screenshot` action with a CSS
`selector` (element-clip screenshot) produced fully black images on this run once the page had
been programmatically scrolled (via `eval`-driven `scrollIntoView` or the tool's own `scroll`
action) — a headless-Chrome compositor artifact tied to the page's sticky nav header, not a
frontend defect (confirmed: `extract`/`get_text` against the same DOM state returned fully
correct content throughout; only the screenshot pixel buffer was affected). Worked around by
resetting `window.scrollTo(0,0)` before every `fullpage:true` capture, then cropping the saved
PNG to the Graduation section's `getBoundingClientRect()` in a follow-up Python/PIL step — the
resulting crops are pixel-accurate captures of the live rendered section, not synthetic images.
This is the same class of headless-rendering flakiness the project has hit before (see memory:
"Headless Chrome throttles the live chart"); it did not block evidence collection here.

---

## Not Tested This Run (per dispatch scope)

J-01, J-04, J-05, J-06, J-07, J-08, J-10 — explicitly excluded from this browser-qa-agent
dispatch; verified separately by deterministic golden replay against the persistent rig's
default (unscoped) state. Evidence screenshots for these already exist at
`reports/qa/goal-rapid-microscope-iter-32-evidence/{J-01,J-04,J-05,J-06,J-07,J-08,J-10}-verify.png`
(timestamped prior to this dispatch). This browser-qa-agent run did not disturb that evidence —
the two backend restarts performed for J-11's captures both targeted only
`TAPEOLOGY_MICRO_GRADUATION_DIR` on a scoped root and were fully reverted (see Restore above)
before this report was written.

---

## Skipped Tests

None.

---

## Golden Replay Script

Wrote `runs/goal-session-rapid-microscope/journey-scripts/J-11.json` (overwritten), asserting
against the persistent rig's restored default state: navigate to `/desk`, click
`[data-testid="desk-section-expand-graduation"]`, expect text `"240dd966c1aceca2 — exploratory"`
(the default rig's one iter-18 fixture family, unaffected by this iteration's scoped-root
captures). Linted clean:
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-rapid-microscope/journey-scripts --journeys J-11` → `J-11 ok`.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, pinned profile/CDP port)
- **Test Date:** 2026-08-24
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-32-evidence/`
