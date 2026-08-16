# goal-referee-iter-12 — UI Test Results

**Phase:** goal-referee-iter-12 (Era 6 "The Referee", J-11 — the accrual projection states its own basis)
**Date:** 2026-08-16
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->

**Overall:** 2/2 tests passed (0 skipped)

Scope note: per dispatch (GOAL-MODE LEAN MODE), this run tests exactly J-05 and J-11 via
Chrome MCP. J-07, J-09, and J-10 are intentionally NOT tested here — they are covered by a
separate deterministic golden-script replay (evidence already present in the evidence dir as
`J-07-verify.png` / `J-09-verify.png` / `J-10-verify.png` from that separate step).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | The shipped Referee Registry section's "Registered Hypotheses" table renders a real append-only hypothesis record with its immutable boundary date, origin label, status, and accrual — the UI-observable face of J-05's registry (full backend acceptance — append-only proof, duplicate/retroactive-boundary refusal, ET-midnight boundary case — is covered by the automated backend suite per J-05's own "(Keyless; automated.)" tag) | Expanded "Referee Registry" on `/desk`; "Registered Hypotheses" table showed one row: S-1 \| capitulation:long \| 2026-08-15 \| historical-exploration \| active \| 0 / 12 \| 1 / 1 discovery (exploratory). Shortlist row for S-1 shows Action="Registered" (disabled), distinct from "Select" on S-2..S-6 — consistent with single-registration, append-only behavior | PASS | `reports/qa/goal-referee-iter-12-evidence/UT-J-05-result.png` |
| UT-J-11 | The accrual projection states its own basis — the wait, measured in recorded sessions | feature | P1 | On `/desk`'s Referee Registry section: one descriptive basis line (recorded sessions, pooled sessions, span days, first→last date, longest zero-session stretch) renders above the shortlist table, and one new right-aligned column renders beside the shipped "Projected days" column — both read verbatim from the API (zero client arithmetic) — while the shipped `accrual_rate_sessions_per_day`/`projected_days_to_target` and every other shipped `/desk` section render exactly as shipped in the same pass | Basis line (`referee-accrual-basis-line`) rendered "Recorded sessions 3 · pooled at the current detector basis 3 · corpus span 47d (2026-06-22 → 2026-08-07) · longest zero-session stretch 42d (2026-06-25 → 2026-08-07)" — byte-identical to a direct `GET /research/desk/referee/registry/shortlist` cross-check. New "Projected sessions" column sits immediately right of "Projected days"; S-1/S-2/S-3 show "36" (== target_sessions 12 / rate 0.333 exactly, matching the live API's `projected_pooled_sessions_to_target`); S-4/S-5/S-6 show "—" (API `null`, zero-rate divide-by-zero discipline). Shipped "Accrual / day" (0.02) / "Projected days" (564) unchanged. Every other shipped section visible in the same pass (Desk screen, Playbook Signals, Backscan, collapsed Top-up/Index/Screen Runs, Playbook Evidence, Referee Adjudications header) rendered with no corruption | PASS | `reports/qa/goal-referee-iter-12-evidence/UT-J-11-result.png` |

---

## Passed Tests

### UT-J-05 — The registry — pre-registration with an immutable boundary
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-12-evidence/UT-J-05-result.png`

Steps executed (Chrome MCP against `http://localhost:3301`):
1. Navigated to `/desk`; confirmed "Referee Registry" section header present (collapsed).
2. Clicked `[data-testid="desk-section-expand-refereeRegistry"]` to expand it.
3. Extracted the section's text and confirmed the "Registered Hypotheses" sub-table renders
   a real, persisted hypothesis record:
   `S-1 | capitulation:long | 2026-08-15 | historical-exploration | active | 0 / 12 | 1 / 1 discovery (exploratory)`
   — i.e. `hypothesis_id`, `setup_id`/`side`, `confirmation_start_boundary`, `origin`,
   status, and per-hypothesis accrual are all rendering, which is the browser-observable
   surface of J-05's append-only registry.
4. Confirmed the shortlist row for S-1 shows Action = "Registered" (a disabled control),
   while S-2..S-6 (not yet registered) show "Select" — the UI correctly distinguishes an
   already-registered candidate.

Notes: J-05's own Acceptance line in goal.md is tagged `(Keyless; automated.)` — its detailed
rules (append-only proof via no update/delete method, duplicate-registration refusal,
retroactive-boundary refusal, the ET-midnight boundary edge case) are unit-tested in the
backend suite, not re-derived here. This browser pass verifies the regression-relevant,
user-visible half: that the registry's data keeps rendering correctly on `/desk` after this
iteration's changes to the same section (J-11 lands new fields in the same
`RefereeRegistrySection` component). No shipped registry text, column, or `data-testid` was
altered.

### UT-J-11 — The accrual projection states its own basis — the wait, measured in recorded sessions
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-12-evidence/UT-J-11-result.png`

Steps executed (Chrome MCP against `http://localhost:3301`; backend fixture rig confirmed
SCOPED via `assert_scoped_qa_backend.py` before starting — `source_url='fixture-rig-iter8-replay'`):
1. Confirmed the frontend dev server was rebuilt after the last edit to `page.tsx`
   (`.next` mtime 00:32:18 > `page.tsx` mtime 00:20:10; dev handoff records a clean
   `start-frontend.sh` / T-9 pass) — no stale-bundle risk.
1. Navigated to `/desk`; "Referee Registry" header present.
2. Clicked `[data-testid="desk-section-expand-refereeRegistry"]`.
3. Read `[data-testid="referee-accrual-basis-line"]`'s text via `eval`:
   `"Recorded sessions 3 · pooled at the current detector basis 3 · corpus span 47d (2026-06-22 → 2026-08-07) · longest zero-session stretch 42d (2026-06-25 → 2026-08-07)"`.
4. Cross-checked this against a direct `curl http://localhost:8301/research/desk/referee/registry/shortlist`:
   `accrual_basis` = `{corpus_first_session_date: "2026-06-22", corpus_last_session_date:
   "2026-08-07", corpus_span_days: 47, recorded_sessions_in_span: 3,
   pooled_sessions_at_current_basis: 3, longest_zero_session_stretch_days: 42,
   longest_zero_session_stretch_start: "2026-06-25", longest_zero_session_stretch_end:
   "2026-08-07"}` — the on-screen basis line is a verbatim, zero-arithmetic render of this
   block (single source of truth honored).
5. Read the shortlist table's `<thead>` cell texts:
   `["Candidate","Estimand","Setup / Side","Primary","Rationale","n","Sessions","Accrual / day","Projected days","Projected sessions","Action"]`
   — exactly one new column, "Projected sessions", immediately beside the shipped
   "Projected days", nothing shipped removed or reordered.
6. Read `[data-testid="referee-shortlist-projected-pooled-S-1"]` = `"36"` and
   `[data-testid="referee-shortlist-projected-pooled-S-4"]` = `"—"`; cross-checked against the
   same API payload: S-1 `projected_pooled_sessions_to_target = 36.0`, S-4 `= null` (S-1
   `n_sessions=1`, `informative_sessions_per_pooled_session = 1/3 = 0.333...`, `36.0 == 12 /
   0.333...` where `target_sessions=12`, matching the registered hypothesis's own "0 / 12"
   accrual figure) — hand-computed and byte-matched, not merely visually similar.
7. Confirmed the shipped `accrual_rate_sessions_per_day`/`projected_days_to_target` columns
   render unchanged (`0.02` / `564` for S-1..S-3) beside the new ones — "beside, never
   replacing" honored.
8. Took one full-page screenshot (after a one-time viewport resize to fit the whole page,
   see Methodology Note below) capturing the basis line, the full shortlist table with the
   new column, the Registered Hypotheses table, and every other shipped `/desk` section from
   the screen controls down through the collapsed "Referee Adjudications" header — all
   rendering with no missing headers, no error banners, no altered shipped text.

Methodology note (not a product defect): the first screenshot attempt, taken at the section's
natural scroll depth (`scrollY≈1460` in a 1316px-tall viewport), came back a solid blank
background with no content — both the explicit `screenshot` action and the auto-captured
per-action PNG at that same scroll position were blank, while `getBoundingClientRect()`/
`visibilityState` via `eval` confirmed the target elements WERE genuinely laid out and
"visible" in the DOM at that scroll offset. This matches a previously-documented headless
capture quirk in this project (deep-scroll screenshots occasionally render blank in this
Chrome MCP setup). Worked around by resizing the viewport to the page's full
`scrollHeight` (2900px) so the whole page fits without scrolling, then re-capturing — the
resulting screenshot renders correctly and is the one saved as evidence. DOM-text extraction
(`extract`/`eval`) throughout matched the visual screenshot exactly, so this was a capture
presentation issue, not a data or rendering gap in the product itself.

Scope note on TC-14 (every OTHER shipped `/desk` section unchanged): this pass's single
full-page screenshot visually covers the screen-control panel, Playbook Signals, Backscan,
and the collapsed Top-up Runs / Index Reconciliation / Screen Runs / Playbook Evidence /
Referee Adjudications headers — all intact. It does not include an individual
screenshot/checksum of the Cockpit (`/`) or Structure (`/structure`) pages, nor of the
collapsed "Referee Runs" section's expanded contents or the page's very top nav — an
exhaustive section-by-section sweep of the whole product is outside browser-qa-agent's
per-test screenshot budget and is the auditor's remit; nothing observed in this pass
suggests any shipped section was touched, and the dev handoff records a `git diff` scoped to
`desk_playbook*.py`/`desk_forward.py`/`levels.py`/`tradability.py`/`pnl_scan.py` as empty.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden Replay Scripts Written

- `runs/goal-session-referee/journey-scripts/J-05.json` — **required deliverable** (J-05 had no
  golden yet per dispatch). 2 steps: `goto /desk` → expect "Referee Registry"; click
  `desk-section-expand-refereeRegistry` → expect "historical-exploration" (a live, data-driven
  string from the registered S-1 hypothesis's `origin` field — a stronger regression tripwire
  than asserting the static "Registered Hypotheses" heading alone, since it only renders if a
  real hypothesis record loaded). Linted clean (`--mode lint`).
- `runs/goal-session-referee/journey-scripts/J-11.json` — 2 steps: `goto /desk` → expect
  "Referee Registry"; click `desk-section-expand-refereeRegistry` → expect "Projected sessions"
  (the new column heading — unique substring, does not collide with the shipped "Projected
  days"). Linted clean (`--mode lint`).

Both scripts were hand-verified against this session's live DOM (exact `data-testid`s and exact
visible text pulled via `eval`, not guessed) before being written; not additionally replayed
through `demo_runner.py --mode verify` (i.e. its own separate Playwright-launched browser) in
this session, per this agent's mandate — lint plus this session's own live Chrome MCP
verification of the same click path and text stand in for that.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (fixture-scoped QA rig confirmed via
  `assert_scoped_qa_backend.py` — `source_url='fixture-rig-iter8-replay'`, exit 0)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless,
  pinned CDP profile/port per environment (pump-launched, attached — not relaunched)
- **Test Date:** 2026-08-16
- **Evidence directory:** `reports/qa/goal-referee-iter-12-evidence/`
- No Referee action buttons ("Confirm Registration", "Build Null", "Evaluate") were clicked in
  this session — both tested journeys are read-only verifications of already-recorded fixture
  state.
