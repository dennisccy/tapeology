# Goal Iteration goal-observation-contract-iter-2 — UI Test Results

**Phase:** goal-observation-contract-iter-2
**Date:** 2026-09-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

**Scope note:** This is a lean, backend-only iteration (`Frontend Present: no`; iter spec
`docs/phases/goal-observation-contract-iter-2.md`). Zero frontend files are touched this
iteration — the work is a `WatchManager` atomic settled-pair (`get_observation_source`) plus a
new pytest module. The iter spec's own TESTING REQUIREMENTS and the goal-mode metadata block
narrow the browser check for J-02 THIS iteration to exactly what the spec names: confirm
`/tape/SIM-BIDABS/observation` still answers "Not Found" after a live Sim watch (route lands
iteration 5 — the full J-02 Acceptance, which requires the served JSON body with
`observed_at_utc`/`available_at_utc`/`availability_basis`/`timing.*` values, is not reachable
this iteration by design); confirm `/structure` and `/desk` render unchanged; and confirm
Watch → Pause → Resume → Stop on `/` still transition the status dot correctly as a regression
smoke test on the touched `watch_manager.py` feeder/pause/resume code paths (Definition of Done:
"status dot transitions `live` → `paused` → `live`, then stops"). This report certifies that
narrower, iteration-scoped browser check, per the same convention iter-1 applied to J-01 ("Note
on J-02's overall journey status: this iteration cannot make J-02 fully pass ... this is
correct, not a regression").

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Iteration-scoped Sim-mode check (watch live; observation route still 404; /structure and /desk unchanged; Watch/Pause/Resume/Stop regression) | smoke | P1 | Status dot reads `live` after watching `SIM-BIDABS` (Simulated); `/tape/SIM-BIDABS/observation` answers `{"detail":"Not Found"}` (route not yet wired — expected this iteration); `/structure` and `/desk` load with no new panel/link/control; Pause → status `paused` (settled state retained, buttons show Resume/Stop); Resume → status `live` again (buttons show Pause/Stop); Stop → returns to `No ticker watched` idle state and the backend 404s the ticker | Watched `SIM-BIDABS` (Simulated); status showed `lag 1.2s` + `live`, scenario `bid_absorption`, tape state `Bid Absorption` confidence `0.950`; `/tape/SIM-BIDABS/observation` (backend :8301) returned `{"detail":"Not Found"}`; `/structure` loaded normally (heading "Structure", 5 buttons/7 inputs/3 links/2 forms — byte-identical interactive-element counts to iter-1's baseline); `/desk` loaded normally (heading "Desk", existing screen/backfill/playbook panels, no observation-contract-related text anywhere on the page); re-watched `SIM-BIDABS`, clicked Pause → status became `paused`, buttons `[Live,Historical,Simulated,Watch,Resume,Stop]`; clicked Resume → status became `live` again, buttons `[Live,Historical,Simulated,Watch,Pause,Stop]`; clicked Stop → page returned to "No ticker watched" / Idle, and `curl http://localhost:8301/tape/SIM-BIDABS/state` confirmed 404 `{"detail":"Ticker 'SIM-BIDABS' is not being watched"}` | PASS | `reports/qa/goal-observation-contract-iter-2-evidence/UT-J-02-watch-live.png`, `reports/qa/goal-observation-contract-iter-2-evidence/UT-J-02-observation-404.png`, `reports/qa/goal-observation-contract-iter-2-evidence/UT-J-02-desk-unchanged.png`, `reports/qa/goal-observation-contract-iter-2-evidence/UT-J-02-pause-resume.png`, `reports/qa/goal-observation-contract-iter-2-evidence/UT-J-02-stop-idle.png` |

---

## Passed Tests

### UT-J-02 — Iteration-scoped Sim-mode check (J-02, lean-mode browser rail)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-2-evidence/UT-J-02-watch-live.png` (acceptance
state), plus supporting `UT-J-02-observation-404.png`, `UT-J-02-desk-unchanged.png`,
`UT-J-02-pause-resume.png`, `UT-J-02-stop-idle.png`

Steps executed (per J-02's goal-file steps as narrowed by the iter spec's TESTING REQUIREMENTS
and Definition of Done, not full J-02 goal-acceptance):
1. Navigated to `http://localhost:3301/`. Clicked the `Simulated` data-source button, typed
   `SIM-BIDABS` into the Ticker field, clicked `Watch`. Confirmed via DOM eval: input value
   `SIM-BIDABS`, `Simulated` button `aria-pressed=true`, Watch button enabled before clicking.
2. Waited for the status indicator; confirmed via eval it read `live` (rendered "lag 1.2s" +
   "live"). Page text showed `Watching / SIM-BIDABS / Pause / Stop / scenario: bid_absorption /
   feed Simulated`, tape state panel `Bid Absorption` confidence `0.950`, quote/trades/features/
   observations/event-log panels populated — a fully live Sim watch, matching iter-1 baseline
   behavior (no product change from the `watch_manager.py` edits).
3. Opened `http://localhost:8301/tape/SIM-BIDABS/observation` directly (the backend origin, since
   this is a REST-only route with no frontend page counterpart). Response body:
   `{"detail":"Not Found"}` — identical in shape to the pre-existing `/tape/{ticker}/*` 404
   convention and to the iter-1 baseline. This is the EXPECTED result per the iter spec ("route
   not yet built — expected, correct, not a defect"), also confirmed via direct `curl` (HTTP 404)
   before driving the browser.
4. Navigated to `http://localhost:3301/structure`. Page loaded with heading "Structure", 5
   buttons / 7 inputs / 3 links / 2 forms — identical interactive-surface counts to iter-1's
   recorded baseline. No new panel, link or control observed.
5. Navigated to `http://localhost:3301/desk`. Page loaded with heading "Desk", the existing
   screen-not-computed panel, Refresh Data / Run Screen / Deep Backfill / Run Playbook / Run
   Backscan controls and the Playbook Signals / Referee / Vault / Graduation collapsible
   sections. Full page text scanned — no mention of "observation", "artifact_hash",
   `tape-observation-v1` or any other observation-contract surface anywhere.
6. Returned to `/` (a fresh navigation resets client-side watch state to idle — pre-existing
   behavior, confirmed as the same "No ticker watched" idle screen, not a regression). Re-watched
   `SIM-BIDABS` (Simulated) and confirmed `live` again via eval.
7. Clicked `Pause`. Confirmed via eval: status text became `paused`, button row became
   `[Live, Historical, Simulated, Watch, Resume, Stop]` (the Pause button relabels to Resume).
   This exercises the iteration's new `pause()` code path that must carry the previous settled
   time forward unchanged.
8. Clicked `Resume`. Confirmed via eval: status text became `live` again, button row reverted to
   `[Live, Historical, Simulated, Watch, Pause, Stop]`. This exercises `resume()`.
9. Clicked `Stop`. Page returned to the "No ticker watched" / Idle screen (same screen as before
   any watch was started). Confirmed via `curl http://localhost:8301/tape/SIM-BIDABS/state` that
   the backend independently 404s the ticker (`"Ticker 'SIM-BIDABS' is not being watched"`),
   proving `stop()` removed the engine as expected — no dangling settled-pair state left the
   ticker in a half-watched condition.

No console errors observed that prevented test completion. No anti-goal or unexpected UI change
detected. The status-dot transition `live → paused → live → (stopped)` matches the Definition of
Done's explicit regression requirement exactly.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-09-03
- **Evidence directory:** `reports/qa/goal-observation-contract-iter-2-evidence/`

## Golden replay scripts written

- `runs/goal-session-observation-contract/journey-scripts/J-02.json` — captures the reliably
  deterministic-replayable portion of this iteration's verified state: watch `SIM-BIDABS`
  (Simulated) to `Watching`, Pause to `Resume`-labeled controls, Resume back to `Pause`-labeled
  controls, Stop back to `No ticker watched`. Deliberately OMITS a `goto` step to
  `/tape/SIM-BIDABS/observation`: `scripts/automation/lib/replay-lane.sh` always invokes
  `demo_runner.py` with `--base-url "$FRONTEND_URL"`, and `demo_runner.py`'s `normalize_url`
  rewrites every `goto` URL (including an explicit backend-origin one) onto that same
  frontend host:port — so a step targeting the backend-only JSON route would silently be
  redirected to Next.js's own client-side 404 page (`heading "404"`, text "This page could not
  be found.") rather than the real backend response, at every replay, regardless of whether the
  observation route actually exists on the backend by then. Including it would make the golden
  either always-trivially-pass (asserting only "404" — true both before and after the real
  route ships) or non-representative. The backend-JSON 404 check above was verified directly by
  this run via real Chrome MCP navigation to the backend origin and is documented with evidence
  in this report; a future browser-qa pass, once the route exists (iteration ~5) and full J-02
  acceptance (the served JSON with `observed_at_utc`/`available_at_utc`/`availability_basis`/
  timing fields) becomes reachable, should overwrite this golden and account for the same
  base_url constraint when deciding how (or whether) to encode that assertion.
- Linted clean: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
  runs/goal-session-observation-contract/journey-scripts --journeys J-02` → `J-02 ok`.
