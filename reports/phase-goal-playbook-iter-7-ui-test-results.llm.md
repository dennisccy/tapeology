# Goal Iteration 7 (playbook) — UI Test Results

**Phase:** goal-playbook-iter-7
**Date:** 2026-08-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 tests passed (0 skipped)

Lean-mode dispatch: tested exactly J-05 and J-07 with a live browser this run. J-01, J-02, J-03,
J-04, J-06, J-10 are covered by deterministic golden-replay elsewhere and were NOT re-driven here.

**Process note (critical, non-functional):** the ambient backend already running at `:8301` when
this dispatch started carried NO `TAPEOLOGY_*` scoping env vars (verified via
`/proc/<pid>/environ`) — i.e. it was pointed at the operator's real `.data/` store, the exact
hazard the dispatch's critical instruction warned about. Before any test action it was stopped and
replaced with `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` (root under the
provided `$TMPDIR`, port 8301) — the ONLY backend used for this run's browser/API calls. Verified
the real store (`apps/backend/.data/playbook*`) has no file modified during this session's window
(latest ambient mtime 2026-08-11 10:59:58, well before testing began ~13:00). No compute/backscan
was ever pointed at the real store.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | The climax family — capitulation entry, euphoria marker | happy-path | P1 | A capitulation signal and a marker-decorated signal legible on the fixture rig | `/desk` Playbook Signals for date `2026-06-22` shows `capitulation:long` (DECOR) row; expanded detail reads "1 approach attempt(s) · 0 bar(s) to close · **euphoria recent**" — the capitulation signal is itself the marker-decorated row (euphoria fired earlier in the same session, decorates the later capitulation per spec §3.5) | PASS | `reports/qa/goal-playbook-iter-7-evidence/UT-J-05-result.png` |
| UT-J-07 | The back-scan — every recorded session, resumable and append-only | happy-path | P1 | Plan preview over a From/To range + a completed fixture scan's run row with per-outcome counts legible | Typed From=`2026-06-22`, To=`2026-06-24` into the Backscan panel → plan preview read "3 dates planned · 3 missing at the current signature" listing all 3 dates; clicked "Run Backscan" → run completed and the runs table shows row `2026-06-22 → 2026-06-24 · done · 0 reused · 3 recorded · 0 refused · 0 failed` — all four per-outcome counts legible | PASS | `reports/qa/goal-playbook-iter-7-evidence/UT-J-07-result.png` |

---

## Passed Tests

### UT-J-05 — The climax family — capitulation entry, euphoria marker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-7-evidence/UT-J-05-result.png`
- Navigated to `/desk`, confirmed "Playbook Signals" section present.
- Typed `2026-06-22` into `[data-testid="desk-playbook-date-input"]`; the record loaded
  (`playbook-2026-06-22-605c13a37aa2`, `playbook_input_signature d7e4e63edf56a9d0`,
  `config_fingerprint 08e471b10130e1e2`) with 4 signals, including `capitulation:long` on symbol
  DECOR.
- Clicked the DECOR row to expand it. Detail line read: "decline 6.10 MBR over 3 bar(s) · climax
  RVOL 2.60 · reversal 1 bar(s) after climax · broke at slot 8", disclosures line read "1 approach
  attempt(s) · 0 bar(s) to close · **euphoria recent**" — confirming the euphoria marker (fired
  earlier in the DECOR session, per the fixture's own docstring: "euphoria marker (trigger slot 4)
  then an independent capitulation (trigger slot 8)") decorates this later capitulation signal via
  `disclosures.euphoria_recent`, exactly as spec'd — the marker itself never appears as its own
  measurable signal row (confirmed via the served payload: only 4 signals total, all with
  `setup_id` in {capitulation, range_trade, open_high_break, double_top} — no `euphoria` setup_id
  anywhere).
- Screenshot captured with the shipped sections above "Playbook Signals" hidden via `display:none`
  (iter-3/iter-7-spec capture technique) so the full section renders in one viewport-height
  screenshot without a scroll — headless Chrome on this rig returned a blank capture for any
  scrolled viewport position (verified: content renders correctly at `scrollY=0` regardless of
  `scroll`/`eval scrollTo`/`scrollIntoView`, but a scrolled capture at the same content position
  returned solid background with no DOM — a headless CDP screenshot quirk, not a product defect).
  The underlying DOM was fully rendered and interactive throughout; only the screenshot capture
  needed the hide-and-reset-scroll workaround the phase spec already names.

### UT-J-07 — The back-scan — every recorded session, resumable and append-only
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-7-evidence/UT-J-07-result.png`
- Navigated to `/desk`, confirmed the new `<section aria-label="Backscan">` panel renders below
  the shipped "Playbook Signals" section with no page-load compute triggered (page-load GET to
  `/research/desk/playbook/backscan/runs` only, honest-empty before any run).
- Typed `2026-06-22` / `2026-06-24` into
  `[data-testid="desk-backscan-from-input"]` / `[data-testid="desk-backscan-to-input"]`. The plan
  preview (`[data-testid="desk-backscan-plan"]`) auto-loaded and read "3 dates planned · 3 missing
  at the current signature", listing `2026-06-22`, `2026-06-23`, `2026-06-24` — matches the
  fixture's own design: registering the 4th universe member (BSCAN) re-keys
  `playbook_input_signature`, so even 2026-06-22's already-recorded 3-member record shows missing
  at the current 4-member signature. Confirmed via direct `GET .../backscan/plan` on the scoped
  backend before the browser pass: `{"total": 3, "missing": 3, "dates": [...all 3 "missing_at_current_signature"...]}`.
  (A single transient debounce-triggered backend traceback was observed mid-typing, for an
  incomplete partial date string `"2026-06-2"` fired by the plan-preview auto-refetch on every
  keystroke; the final committed `2026-06-24` value re-fetched cleanly to 200 OK immediately after
  — noted as a WARN, not a functional failure, since the test's actual end state was correct and
  the panel never surfaced an error to the user.)
- Clicked `[data-testid="desk-backscan-button"]` ("Run Backscan"). The compute completed and a new
  row appeared in `[data-testid="desk-backscan-runs-table"]`:
  `2026-06-22 → 2026-06-24 · done · 0 reused · 3 recorded · 0 refused · 0 failed · 2026-08-11
  08:04:56 ET` — all four per-outcome counts (`reused`, `recorded`, `refused_non_session`,
  `failed`) legible in one row, matching TC-11/TC-2 (`outcomes.recorded == 3`).
- Screenshot captured with the same hide-siblings-above/reset-scroll technique, isolating the
  Backscan panel (plan preview + Run Backscan control + the completed runs table) in one
  viewport-height capture.

---

## Failed Tests

None.

---

## Skipped Tests

None — both target journeys (J-05, J-07) were tested live per the lean-mode dispatch.

---

## Golden Replay Scripts

Both journeys PASSED, so deterministic replay scripts were written/refreshed and lint-verified
(`demo_runner.py --mode lint`, both `ok`):

- `runs/goal-session-playbook/journey-scripts/J-05.json` — re-verified unchanged (goto `/desk` →
  fill session date `2026-06-22` expecting "Capitulation" → click "DECOR" expecting "euphoria
  recent").
- `runs/goal-session-playbook/journey-scripts/J-07.json` — new: goto `/desk` expecting "Backscan"
  → fill From=`2026-06-22` → fill To=`2026-06-24` expecting "3 missing at the current signature" →
  click the Backscan button (`testid: desk-backscan-button`) expecting "3 recorded". Targets the
  new section's own static shell strings and testids only, per T-11 (no shipped `data-testid` or
  heading string reused).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (restarted mid-dispatch onto the iter-7 fixture-scoped
  rig — see process note above; both servers verified healthy, 200, at end of run)
- **Browser:** Chrome via MCP (headless, pinned CDP `127.0.0.1:9222`)
- **Test Date:** 2026-08-11
- **Evidence directory:** `reports/qa/goal-playbook-iter-7-evidence/`
