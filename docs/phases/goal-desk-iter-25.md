# Goal Iteration 25 — Close the three evidence gaps iter-24 left open (film, re-verify, replay)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 25
- **Mode:** next
- **Depth:** evidence
- **Target journeys:** J-06, J-15, J-16
- **Required-still-passing journeys:** J-01, J-03, J-04, J-07, J-08, J-11, J-12, J-13, J-14
- **Frontend Present:** no
- **Anti-goal reminders:**
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*

## GOAL

Close the three purely-evidentiary gaps iteration 24 left open, with zero code change: record J-16's
`[NEW]`-flagged demo-narrator walkthrough (with the `opposite` and `levels` columns visible in the
film's own frames, and every click locator naming exactly one row), re-verify J-06's 17-tool MCP
contract and J-15's current wall-composition column text against live state, and produce the
`J-16-verify.png` golden-replay screenshot that iteration 24's own report claimed but never wrote to
disk.

## BACKGROUND

Iteration 24 shipped J-16's layout fix (table `scrollWidth` 1214===1214, rows 57 px) and it is
already recorded `passing`, but the run went over its time budget: J-06 and J-15 were dropped from
re-verification (`DEFERRED-BUDGET`, prior status kept), no film was recorded because `Depth: lean`
never dispatches the demo-narrator, and browser-qa's own claimed `J-16-verify.png` is not on disk.
`journey-history.json` shows zero FAILING journeys — all 16 are `passing` — so per the target-journey
rubric this run is capture-and-check only, targeting exactly the three journeys iter-24's own
next-step recommendation named. The evaluator's binding depth recommendation for this iteration is
`evidence`, which matches rule 7's exception (next-step asks only for evidence on already-passing
journeys) — no escape condition (prior ESCALATE/REGRESSION, prior coherence-audit FAIL, hardening
cadence, or a brand-new full-stack journey) holds, so lean/full are both out of scope; the engine's
arbiter would demote a full spec here regardless. Last coherence verdict was `COHERENCE-PASS`
(iter-24), so no consolidation pass is owed.

Two lessons apply directly. iter-24's lesson: a `[NEW]`-flagged walkthrough clause needs `full` or
`evidence` depth — never `lean` — which is exactly why this run exists. iter-23's lesson (repeated at
iter-20): a demo script's click `target` resolving to a `data-testid` shared by all 100 rows produces
an ambiguous multi-match soft note (`RECORDED_WITH_NOTES`), and a script with JS-regex literals
instead of JSON strings fails OPEN and silently (`SKIPPED`) — this run's script must be parse-checked
before recording and every click must scope to one row via the row's own `data-symbol` attribute
(`apps/frontend/app/desk/page.tsx:403`, `<tr data-testid="desk-screen-row" data-symbol={row.symbol}>`),
e.g. `tr[data-symbol="<SYM>"] [data-testid="desk-row-levels"]` — never the bare testid alone. Also
carry forward the standing "Do not redo" rail from iteration-state: evidence capture must stay
READ-ONLY (no Run Screen / top-up / reconcile trigger); iter-24 already proved `.data` can stay
byte-identical across a capture-only run except for rebuildable `bar_index.db-wal`/`-shm` sidecars.

## IN SCOPE

### Backend
- (none — zero code change this iteration; see NOTES)

### Frontend
- (none — zero code change this iteration; see NOTES)

### Evidence capture (developer/reviewer skipped at this depth)
- [ ] Author (or repair) a `[NEW]`-flagged demo-narrator script for J-16 covering the briefing end to
  end, with the `opposite` and `levels` column cells visible inside its OWN recorded frames. Every
  click `target` must resolve to exactly one row: scope via `tr[data-symbol="<SYM>"] ...`, never the
  bare `[data-testid='desk-row-levels']`/`[data-testid='desk-row-opposite']` alone (both match all
  100 rows). Pick one ranked row with a small `band_member_count` (≤5) and one with a large count
  (≥100) so both extremes are legible, per iter-23's own precedent content.
- [ ] Parse-check the script (`demo_runner.py --mode lint` or equivalent) BEFORE the record run —
  iter-20's lesson: a script with JS-regex literals instead of JSON strings fails OPEN to `SKIPPED`
  with no visible error elsewhere in the pipeline.
- [ ] Record the walkthrough against the live rig (`:8301`/`:3301`), read-only (no Run Screen /
  top-up / reconcile trigger — capture the ALREADY-recorded latest screen
  `screen-2026-07-30-bad6387963ef` verbatim).
- [ ] Re-verify J-06 live: enumerate the running MCP tool registry and confirm it is exactly the same
  17 tools as `EXPECTED_TOOLS` in `apps/backend/tests/test_mcp_server.py`.
- [ ] Re-verify J-15 live: capture a fresh full-page `/desk` screenshot and read the `levels` column's
  CURRENT text form (iter-24 dropped the word "levels" from the in-cell tally: `"155 · 1d 68 · …"`,
  not `"155 levels · 1d 68 · …"` — the column heading alone now carries the word) directly off the
  picture, cross-checked against the stored snapshot JSON's `band_member_count` /
  `band_round_number` / `band_member_timeframes` fields for the same rows.
- [ ] Replay `runs/goal-session-desk/journey-scripts/J-16.json` against the live rig and confirm a
  real `J-16-verify.png` is written to the evidence directory (iter-24 claimed one that is not on
  disk anywhere under `reports/qa/goal-desk-iter-24-evidence/`).
- [ ] Replay the required-still-passing set's stored golden scripts (J-01, J-03, J-04, J-07, J-08,
  J-11, J-12, J-13, J-14) — zero script edits expected.

### New user-facing capability
None — this iteration ships no new product behavior. It records evidence for capability J-16 already
shipped (iter-24) and re-confirms two already-shipped capabilities (J-06, J-15).

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — `/desk` is read exactly as iter-24 left it.

### Product surface delta
None. The only deliverables are: one demo recording, two re-verification checks, and one missing
screenshot artifact.

### Blueprint conformance
No new page, no new column, no nav-skeleton change — `blueprint.md`'s J-16 "RESOLVED at iter-24" note
already covers the current `/desk` layout and needs no edit this iteration.

### Data-contract additions
None — zero new displayed value, zero new endpoint, zero new `Config` field.

## OUT OF SCOPE

- Any code change to `desk_screen.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
  `desk_coverage.py`, either chart, or `/desk`'s own layout/testids — all frozen this iteration.
- Widening the `levels`/`opposite` column past its current width, or any further row-height tuning
  (the 2-of-100-rows-at-63px residual is an accepted non-defect per iteration-state's "Do not redo").
- Any Run Screen / top-up / index-reconcile trigger — capture reads the already-recorded latest
  screen only.
- A 13th ranked-table column, a grouped layout, or a per-row detail panel (iter-23's open UX-debt
  note) — not this iteration's job.
- Re-tuning `closure_gate.py`'s `backend-only` substring guard or `goal_gate.py results`' bold-FAIL
  regex miss (iter-23's lesson) — both are framework hygiene items, not product work, and out of a
  goal-decomposer's remit.
- Archiving `runs/goal-session-desk/journey-scripts/` (would break `test_desk_ui_guards.py`'s two
  golden-script reads) — leave it in place.

## DEFINITION OF DONE

- [ ] J-16's `[NEW]`-flagged demo-narrator walkthrough reads `Demo Verdict: RECORDED` (not
  `RECORDED_WITH_NOTES` or `SKIPPED`), with `opposite` and `levels` legible in its own frames and
  every click locator naming exactly one row.
- [ ] J-06 re-verified live: exactly 17 MCP tools, matching `EXPECTED_TOOLS`.
- [ ] J-15 re-verified live: the current `levels` column text form matches the stored snapshot's
  `band_member_count`/`band_round_number`/`band_member_timeframes` fields on a fresh full-page
  capture.
- [ ] `J-16-verify.png` exists on disk after replaying `journey-scripts/J-16.json`, and all 7 of its
  steps pass.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-07, J-08, J-11, J-12, J-13, J-14) replay
  green via deterministic golden-script replay, zero script edits.
- [ ] No anti-goal violation introduced — evidence capture stays read-only; zero append-only store
  write beyond the golden script's own single non-mutating history-row read.
- [ ] Zero diff under `apps/`, `scripts/`, `config/`; `config_fingerprint` stays `08e471b10130e1e2`;
  backend suite result unchanged from iter-24.

## TESTING REQUIREMENTS

- Browser: J-06 (tool-count re-check), J-15 (levels-column re-check), J-16 (demo walkthrough +
  golden replay) — plus deterministic replay of J-01, J-03, J-04, J-07, J-08, J-11, J-12, J-13, J-14.
- Unit/integration: none new (zero code change); the existing `test_mcp_server.py::EXPECTED_TOOLS`
  assertion and the backend suite as a whole are re-run to confirm no drift.
- Error cases: N/A — no new code path.

Test-first contract:

- TC-1: given the desk rig is live at `:8301`/`:3301` with the already-recorded latest screen
  `screen-2026-07-30-bad6387963ef` (100 ranked rows), when the demo-narrator records a `[NEW]`-flagged
  J-16 walkthrough using per-row-scoped click locators (`tr[data-symbol="<SYM>"]
  [data-testid="desk-row-opposite"]` and `...desk-row-levels`), then
  `reports/phase-goal-desk-iter-25-demo-results.md` reads `Demo Verdict: RECORDED` and the frame(s)
  under `reports/demo/goal-desk-iter-25/` show both the `opposite` and `levels` column text for at
  least one row each, with no ambiguous-multi-match soft note.
- TC-2: given the demo script is authored before capture, when it is parse-checked
  (`demo_runner.py --mode lint` or equivalent JSON/schema validation), then the lint step reports zero
  parse errors before the record run is dispatched.
- TC-3: given `app/mcp/__init__.py`'s tool registry is unchanged this iteration, when the live tool
  list is enumerated and compared against `EXPECTED_TOOLS` in `apps/backend/tests/test_mcp_server.py`,
  then the count is exactly 17 and every name matches.
- TC-4: given the latest recorded screen's `levels` column renders in its current (iter-24) text form,
  when a fresh full-page screenshot of `/desk` is captured and read directly, then one row with
  `band_member_count <= 5` and one row with `band_member_count >= 100` are both legible in the same
  frame together with a `round number` badge on at least one row, and every on-screen tally matches
  that row's `band_member_count`/`band_member_timeframes` read from the stored snapshot JSON on disk.
- TC-5: given `runs/goal-session-desk/journey-scripts/J-16.json` is a pure read (no mutating step),
  when it is replayed against the live rig, then a `J-16-verify.png` file is written to the evidence
  directory and all 7 of its `expect` assertions pass.
- TC-6: given the required-still-passing set (J-01, J-03, J-04, J-07, J-08, J-11, J-12, J-13, J-14),
  when their stored golden scripts are replayed, then all 9 report PASS with zero script edits.
- TC-7: given capture performs no mutating action beyond the golden script's own single read-only
  history-row click, when a file listing of `apps/backend/.data/` is diffed before and after the run,
  then the only files that differ are rebuildable index sidecars (e.g. `bar_index.db-wal`/`-shm`) — no
  new screen, universe, top-up, or reconcile record is written.
- TC-8: given zero code changes are made this iteration, when the backend suite and
  `Config().config_fingerprint()` are checked, then the suite result and the fingerprint
  (`08e471b10130e1e2`) are unchanged from iteration 24's own recorded values, and the working-tree
  diff under `apps/`, `scripts/`, `config/` is empty.

## NOTES

- This is a capture-only run (no developer, no reviewer dispatched at `Depth: evidence`) — there is
  no `docs/handoffs/goal-desk-iter-25-dev.md` to write; the deliverables are the demo recording, the
  two re-verification checks, and the replay artifact.
- Iteration-state's "Do not redo" list is binding: J-16's layout (`table-fixed` + 13-col `<colgroup>`,
  `flex-nowrap` coverage badges, `rank` cell) is DONE — do not re-tune widths; the `band `/`opposite `
  label prefixes must stay (guarded by `test_desk_row_cells_keep_the_label_prefix_their_golden_script_asserts`);
  the 2-of-100-rows-at-63px residual and the reused `round number` badge height are accepted
  non-defects — do not restyle.
- Do not delete or mutate `apps/backend/.data/screen/screen-2026-07-30-bad6387963ef.json` or any
  other stored record; the golden script's only click (a Screen History row) is a plain
  `GET /research/desk/screen?id=...` read.
- If the demo-narrator's action vocabulary genuinely cannot scope a click to one row (no CSS/testid
  combination resolves uniquely), fall back to `expect`-only text assertions over the populated frame
  rather than a click — per the iter-21 assumption-ledger precedent (narration accuracy over a
  populated recording satisfies "covers ... end to end" even without every disclosure being a click
  target), but prefer the `data-symbol`-scoped click since `data-symbol` already exists on every row
  (`apps/frontend/app/desk/page.tsx:403`) and iter-24's own next-step explicitly asked for it.
- No blueprint edit accompanies this iteration — no new displayed value, no nav-skeleton change.
