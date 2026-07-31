# Goal Iteration 28 — UI Test Results

**Phase:** goal-desk-iter-28
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->

**Overall:** 1/1 tests passed (0 skipped)

Scope note: this run tested EXACTLY J-17, on the ambient `:3301`/`:8301` pair (the only rig
running — no fixture-scoped `:3391`/`:8391` rig exists at test time). J-04, J-07, J-09, J-16 were
explicitly excluded from this browser-qa pass per dispatch instructions (verified separately by
deterministic replay; their evidence PNGs already present in the evidence directory from that
replay are untouched by this run).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | regression | P1 | `/desk` Top-up Runs section renders the four-outcome counts line, a window-basis disclosure line, and a "Failed pairs (N)" list with each pair's own detail; ranked briefing table (J-16) renders unaffected, no horizontal scroll at 1440×900 | On the ambient rig (`:3301`/`:8301`), `desk-topup-run-latest-counts` reads "0 reused · 390 fetched · 0 unchanged · 14 failed", `desk-topup-run-latest-window-basis` reads "window basis not recorded in this run" (honest legacy-absence disclosure — this run predates the per-pair window fields), `desk-topup-run-latest-failed` lists "Failed pairs (14)" with each pair's own detail text and its own "window basis not recorded in this run" per-pair note; ranked table present (115 rows), `scrollWidth` (1425px) == `clientWidth` (1425px) at 1440×900 — no horizontal scroll | PASS | `reports/qa/goal-desk-iter-28-evidence/J-17-result.png` |

---

## Passed Tests

### UT-J-17 — A top-up asks the vendor only for the bars the frozen store cannot already prove
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-28-evidence/J-17-result.png`

- Navigated to `http://localhost:3301/desk` at a 1440×900 viewport.
- Page loaded with heading "Desk"; Top-up Runs section rendered without error.
- `[data-testid="desk-topup-run-latest-counts"]` textContent = `"0 reused · 390 fetched · 0 unchanged · 14 failed"` — the four-outcome counts line renders (this iteration's added `unchanged` category is present in the line's shape, reading 0 on this particular recorded run, which is the honest real count for the one recorded real top-up per the goal file's own note).
- `[data-testid="desk-topup-run-latest-window-basis"]` textContent = `"window basis not recorded in this run"` — the honest legacy-absence disclosure for a run recorded before the per-pair `window_basis` field existed, matching the goal file's specified legacy pattern.
- `[data-testid="desk-topup-run-latest-failed"]` textContent begins `"Failed pairs (14)AAPL 1h — no data for AAPL 1h in the requested window 2024-07-29T00:00:00+00:00..2026-07-30T00:00:00+00:00 — Yahoo Finance serves 1h bars only for the last 730 days..."` followed by 13 more failed pairs, each with its own detail string and its own honest "window basis not recorded in this run" (no per-pair `requested_window` on this legacy run — expected, since that field also postdates this recorded run).
- Ranked briefing table (J-16) present with 115 rows, unaffected by the Top-up Runs section.
- `document.documentElement.scrollWidth` (1425) equals `clientWidth` (1425) — no horizontal scroll at the 1440×900 viewport.
- Existing golden replay script `runs/goal-session-desk/journey-scripts/J-17.json` was re-checked against this live state: its three `expect` assertions (counts line, window-basis line, "Failed pairs (14)") match verbatim what was just observed live, and it passes `demo_runner.py --mode lint`. No edit was needed — left in place unchanged.

**Scope boundary (not a failure, an honest limitation of this rig):** the full goal-file Acceptance
line for J-17 additionally calls for "at least one `unchanged`" outcome and "one failed pair with
its own recorded `requested_window`" — both of these require a **fixture-scoped rig** with an
injected fake adapter (per `docs/phases/goal-desk-iter-28.md`'s own Background section: the one
real recorded top-up run on the ambient store has never produced an `unchanged` outcome, and
predates the per-pair `requested_window` field). No such scoped rig (`:3391`/`:8391`) was running
at test time, and standing one up (fresh `.data` copy, a second backend/frontend build, seeding a
fixture top-up run) is explicitly a rig-provisioning + demo-narrator deliverable per the iteration
spec's own Testing Requirements section ("Browser: J-17 (demo-narrator walkthrough over a
populated, fixture-scoped Top-up Runs section...)") — not a browser-qa-agent task, and out of this
agent's remit (no app rebuilding/restarting, no new infrastructure). What WAS verified is that the
already-shipped J-17 UI continues to render correctly and honestly against the only rig available,
with zero regression to J-16's table layout — this is the portion of J-17 that is properly a
browser-qa-agent regression check. The scoped-rig walkthrough capture remains the separate,
already-identified deliverable of this iteration's demo-narrator step.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-04, J-07, J-09, J-16 were not tested by this agent per explicit dispatch instruction
("Do NOT test these — a deterministic replay verifies them separately") — not skips, exclusions by
design.

---

## Golden Replay Scripts

- `runs/goal-session-desk/journey-scripts/J-17.json` — re-verified against the live ambient rig
  this run; all three assertions matched verbatim; lints clean via
  `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-desk/journey-scripts --journeys J-17`
  (`J-17 ok`). Left unchanged — no drift found.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, CDP port 9222)
- **Test Date:** 2026-07-30
- **Evidence directory:** `reports/qa/goal-desk-iter-28-evidence/`
