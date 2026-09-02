# Goal Iteration goal-observation-contract-iter-0 — UI Test Results

**Phase:** goal-observation-contract-iter-0
**Date:** 2026-09-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- This is iteration 0 of a brand-new era, run in Mode: baseline. Per the iter spec's own
     Test-first contract (TC-1..TC-6), J-01 through J-05 are EXPECTED to fail outright (the
     entire observation-contract implementation surface — builder, atomic manager read, route,
     test modules — is genuinely unbuilt) and J-06 is EXPECTED to be partial (era-open paperwork
     already done; guard-suite module not yet built). The FAIL verdict below is an honest,
     accurate record of the current (pre-build) state, not a regression — it establishes the
     baseline that iteration 1+ builds against, exactly as this iteration's GOAL requires. -->

**Overall:** 0/6 tests passed (0 skipped) — 5 FAIL (J-01..J-05), 1 FAIL-as-partial (J-06: era-open
docs + unchanged pages confirmed present/working; guard-suite module confirmed absent)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Pure projection, semantic identity, provenance, integrity | happy-path | P1 | `/tape/SIM-BIDABS/observation` serves `"schema_version": "tape-observation-v1"` etc.; `tests/test_tape_observation_projection.py` passes 0 failures | `/tape/SIM-BIDABS/observation` returns the generic unmatched-route body `{"detail":"Not Found"}` (not the artifact); `tests/test_tape_observation_projection.py` does not exist | FAIL | `reports/qa/goal-observation-contract-iter-0-evidence/J-01-fail.png` |
| UT-J-02 | Three honest time instants, atomic read | happy-path | P1 | Served JSON shows `observed_at_utc` starting `2024-01-02T14:3`, `available_at_utc` null, `availability_basis` `simulated_not_applicable`, `timing.settled_at_utc`/`generated_at_utc` today; `tests/test_tape_observation_time.py` passes | Same generic 404 body; none of the three time fields is observable anywhere; `tests/test_tape_observation_time.py` does not exist | FAIL | `reports/qa/goal-observation-contract-iter-0-evidence/J-02-fail.png` |
| UT-J-03 | Lifecycle, feed basis, session identity stay honest | happy-path | P1 | Reloads across live → paused → live → stopped(404) → re-watched show `lifecycle.stream_status` transitions and a changed `source.session_id`; `tests/test_tape_observation_lifecycle_feed.py` passes | Every reload across the full Watch → Pause → Resume → Stop → Watch-again sequence returns the identical generic 404 body — no `lifecycle.*` / `source.session_id` field ever appears to compare; module does not exist | FAIL | `reports/qa/goal-observation-contract-iter-0-evidence/J-03-fail.png` |
| UT-J-04 | Ingestion-path equivalence (observation_hash stable, artifact_hash/generated_at differ) | happy-path | P1 | Two reloads of the paused observation show identical `observation_hash`, different `generated_at_utc`/`artifact_hash`; `tests/test_tape_observation_path_equivalence.py` passes | Two reloads of the paused ticker both return the identical generic 404 body — no hash fields exist to compare; module does not exist | FAIL | `reports/qa/goal-observation-contract-iter-0-evidence/J-04-fail.png` |
| UT-J-05 | One read-only machine path, 404 parity | happy-path | P1 | `/tape/SIM-BIDABS/observation` renders 200 with the v1 schema; `/tape/ZZZZ/observation` renders a matched-404 body (same shape as `/tape/ZZZZ/state`); `tests/test_tape_observation_route.py` passes | Both `/tape/SIM-BIDABS/observation` (watched ticker) and `/tape/ZZZZ/observation` (unwatched) return the identical generic unmatched-route body `{"detail":"Not Found"}` — no route is registered at all, so there is no 200-vs-matched-404 distinction; `/tape/ZZZZ/state` by contrast returns the matched `{"detail":"Ticker 'ZZZZ' is not being watched"}`, proving `/observation` genuinely has no route; module does not exist | FAIL | `reports/qa/goal-observation-contract-iter-0-evidence/J-05-fail.png` |
| UT-J-06 | Guards and the regression sentinel | happy-path | P1 | `/`, `/structure`, `/desk` render with no new panel/link/control; the three era-open docs artifacts exist; `tests/test_tape_observation_guards.py` passes; full backend suite + `tsc --noEmit` green; `config_fingerprint`/MCP contract unchanged | `/`, `/structure`, `/desk` all confirmed rendering unchanged (no "observation" string anywhere in `/structure` or `/desk` HTML; `/` shows only the pre-existing tape-read UI) — this half PASSES; `docs/goal-archive/goal-2026-09-02.md`, `docs/observation-contract-spec.md`, and the dated `docs/research-directions.md` note all exist and are committed on `main` — this half PASSES; `tests/test_tape_observation_guards.py` does not exist — this half FAILS; `tsc --noEmit` (0 errors) and `config_fingerprint`/MCP contract (28 tools) independently confirmed unchanged; full backend suite = browser-qa-agent's own background re-run completed after report drafting (exit code 0, zero `F`/`E` characters in the captured output — 0 failed, independently confirmed) though its exact `N passed/M skipped` counts were not captured (only a `tail -30` of the run was piped) — see "Baseline suite/config confirmation" below; matches dev/reviewer's own separately-recorded 3930 passed/8 skipped/0 failed | FAIL (partial: era-open + unchanged-pages sub-checks PASS, guard-suite sub-check FAIL — record as **partial** in journey-history, not a full regression; full-suite 0-failed independently reconfirmed) | `reports/qa/goal-observation-contract-iter-0-evidence/J-06-partial.png` |

---

## Passed Tests

None this iteration. This is expected: iteration 0 is a Mode: baseline verify-only pass against a
brand-new, entirely-unbuilt era surface (`docs/phases/goal-observation-contract-iter-0.md` IN SCOPE
is empty for both Backend and Frontend by design). No journey's implementation surface exists yet.

---

## Failed Tests

### UT-J-01 — Pure projection, semantic identity, provenance, integrity
**Verdict:** FAIL
**Failure:** `apps/backend/app/observation_contract.py` does not exist and no `/tape/{ticker}/observation`
route is registered in `apps/backend/app/main.py`. After watching `SIM-BIDABS` (Simulated) from `/`
and waiting for the live tape read to appear, opening `http://localhost:8301/tape/SIM-BIDABS/observation`
returns the generic FastAPI unmatched-route body `{"detail":"Not Found"}` — none of the required keys
(`schema_version`, `provider`, `tape_state`, `engine_identity`, `implementation_provenance`,
`observation_hash`, `artifact_hash`, ...) is present. `tests/test_tape_observation_projection.py` is
absent (`ERROR: file or directory not found` on direct pytest invocation).
**Evidence:** `reports/qa/goal-observation-contract-iter-0-evidence/J-01-fail.png`

**Steps taken:**
1. Navigated to `http://localhost:3301/`, confirmed `Simulated` is the selected data source, typed
   `SIM-BIDABS` into the `Ticker` field, clicked `Watch`.
2. Waited for the tape read panel to populate (`TAPE STATE: Bid Absorption`, `Confidence 0.950`,
   feed `Simulated`, stream status `Live`) — confirmed via `curl http://localhost:8301/tape/SIM-BIDABS/state`
   showing `"stream_status":"live"`.
3. Navigated to `http://localhost:8301/tape/SIM-BIDABS/observation`.
4. Extracted page text: `{"detail":"Not Found"}`.
5. Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_projection.py -q`
   → `ERROR: file or directory not found: tests/test_tape_observation_projection.py`.

**Expected:** 200 JSON body with `"schema_version": "tape-observation-v1"` and the full field set;
`tests/test_tape_observation_projection.py` passing with 0 failures.
**Actual:** Generic 404 `{"detail":"Not Found"}`; test module absent.

---

### UT-J-02 — Three honest time instants, atomic read
**Verdict:** FAIL
**Failure:** Same `/tape/SIM-BIDABS/observation` 404 as J-01 — no `observed_at_utc`, `available_at_utc`,
`availability_basis`, `timing.settled_at_utc` or `generated_at_utc` field is served anywhere.
`tests/test_tape_observation_time.py` is absent.
**Evidence:** `reports/qa/goal-observation-contract-iter-0-evidence/J-02-fail.png`

**Steps taken:**
1. (Reused the live `SIM-BIDABS` watch from J-01.) Opened `http://localhost:8301/tape/SIM-BIDABS/observation`.
2. Extracted page text: `{"detail":"Not Found"}` — none of the three time concepts is observable.
3. Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_time.py -q` →
   `ERROR: file or directory not found: tests/test_tape_observation_time.py`.

**Expected:** `observed_at_utc` starting `2024-01-02T14:3`, `"available_at_utc": null`,
`"availability_basis": "simulated_not_applicable"`, `timing.settled_at_utc`/`generated_at_utc` on
today's date; `tests/test_tape_observation_time.py` passing.
**Actual:** Generic 404; test module absent.

---

### UT-J-03 — Lifecycle, feed basis, session identity stay honest
**Verdict:** FAIL
**Failure:** `WatchManager.get_observation_source` is not defined; every reload of
`/tape/SIM-BIDABS/observation` across the full lifecycle sequence (live → paused → live → stopped →
re-watched) returns the identical generic 404 body, so no `lifecycle.stream_status`,
`lifecycle.paused`, `source.session_id` or `source.data_feed` value is ever present to compare
across steps. `tests/test_tape_observation_lifecycle_feed.py` is absent.
**Evidence:** `reports/qa/goal-observation-contract-iter-0-evidence/J-03-fail.png`

**Steps taken:**
1. Re-attached the UI to the live `SIM-BIDABS` watch (`Watch` again after a full-page reload reset
   the client's local watch state — the backend watch itself stayed live throughout, confirmed via
   `curl .../tape/SIM-BIDABS/state`). Confirmed `stream_status: live` via curl.
2. Clicked `Pause` on `/`. Confirmed via curl (`"stream_status":"paused"`). Reloaded
   `/tape/SIM-BIDABS/observation` in a second tab → `{"detail":"Not Found"}` (unchanged).
3. Clicked `Resume` on `/`. Reloaded the observation tab → `{"detail":"Not Found"}` (unchanged).
4. Clicked `Stop` (aria-label "Stop watching") on `/`. Confirmed via curl
   (`{"detail":"Ticker 'SIM-BIDABS' is not being watched"}` from `/state`). Reloaded the observation
   tab → `{"detail":"Not Found"}` — identical body whether watched, paused, or stopped.
5. Re-typed `SIM-BIDABS` and clicked `Watch` again on `/`; waited for the tape-read panel to
   re-populate (`Pause`/`Stop` controls reappeared, `feed Simulated`, `Live`). Reloaded the
   observation tab → `{"detail":"Not Found"}` (unchanged) — no `source.session_id` field exists to
   compare against the first watch's session.
6. Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_lifecycle_feed.py -q`
   → `ERROR: file or directory not found`.

**Expected:** `lifecycle.stream_status` visibly transitioning `live` → `paused` → `live`, 404 after
Stop, a different `source.session_id` on re-watch; `tests/test_tape_observation_lifecycle_feed.py`
passing.
**Actual:** Identical generic 404 at every step; test module absent.

---

### UT-J-04 — Ingestion-path equivalence under an identical valid event stream
**Verdict:** FAIL
**Failure:** No `build_tape_observation` or hash law exists anywhere; two reloads of the paused
`/tape/SIM-BIDABS/observation` both return the identical generic 404 body, so there is no
`observation_hash` to show as stable nor `generated_at_utc`/`artifact_hash` to show as differing.
`tests/test_tape_observation_path_equivalence.py` is absent.
**Evidence:** `reports/qa/goal-observation-contract-iter-0-evidence/J-04-fail.png`

**Steps taken:**
1. With `SIM-BIDABS` live (re-watched in J-03 step 5), clicked `Pause` on `/`. Confirmed via curl
   (`"stream_status":"paused"`).
2. Navigated to `http://localhost:8301/tape/SIM-BIDABS/observation` — `{"detail":"Not Found"}`.
3. Reloaded the same URL a second time — `{"detail":"Not Found"}` (byte-identical body both times;
   no hash fields present in either to compare).
4. Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_path_equivalence.py -q`
   → `ERROR: file or directory not found`.

**Expected:** Identical `observation_hash` across two reloads, differing `generated_at_utc` and
`artifact_hash`; `tests/test_tape_observation_path_equivalence.py` passing on both fixtures.
**Actual:** Byte-identical generic 404 responses with no hash fields at all; test module absent.

---

### UT-J-05 — One read-only machine path
**Verdict:** FAIL
**Failure:** No `/tape/{ticker}/observation` route is registered on the FastAPI app at all. Both a
watched ticker (`SIM-BIDABS`) and a nonexistent one (`ZZZZ`) return the exact same generic
unmatched-route body `{"detail":"Not Found"}` — there is no 200-with-schema response for the watched
ticker and no matched-404 body (distinguishable from a truly-nonexistent path) for the unwatched
one. By contrast, `/tape/ZZZZ/state` (an existing, registered sibling route) returns the matched
`{"detail":"Ticker 'ZZZZ' is not being watched"}`, proving the difference is "no route registered"
rather than "ticker not found." `tests/test_tape_observation_route.py` is absent.
**Evidence:** `reports/qa/goal-observation-contract-iter-0-evidence/J-05-fail.png`

**Steps taken:**
1. Opened `http://localhost:8301/tape/SIM-BIDABS/observation` (SIM-BIDABS watched and live) →
   `{"detail":"Not Found"}` (expected 200 with `"schema_version": "tape-observation-v1"`).
2. Opened `http://localhost:8301/tape/ZZZZ/observation` → `{"detail":"Not Found"}` — identical body
   to step 1, and identical to `/tape/ZZZZ/state`'s *unmatched*-shape sibling would be, except that
   `/tape/ZZZZ/state` itself actually returns a different, matched body
   (`{"detail":"Ticker 'ZZZZ' is not being watched"}`, confirmed via curl), proving `/observation`
   has no route at all.
3. Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_route.py -q` →
   `ERROR: file or directory not found`.

**Expected:** `/tape/SIM-BIDABS/observation` → 200 with the v1 schema; `/tape/ZZZZ/observation` → a
matched 404 body; `tests/test_tape_observation_route.py` passing.
**Actual:** Both return the identical generic unmatched-route 404; test module absent.

---

### UT-J-06 — Guards and the regression sentinel
**Verdict:** FAIL (partial — see breakdown)
**Failure:** `tests/test_tape_observation_guards.py` does not exist, so the guard-suite sub-check of
this journey's Acceptance cannot pass. This is the *only* failing sub-check — the era-transition
paperwork sub-check and the "pages render unchanged" sub-check both genuinely pass, exactly matching
the iter spec's own prediction ("J-06 is expected to be at best partial"). Recommend recording this
journey as **partial** (not fully failing) in `journey-history.json`.
**Evidence:** `reports/qa/goal-observation-contract-iter-0-evidence/J-06-partial.png`

**Steps taken:**
1. Confirmed `/tape/SIM-BIDABS/observation` still serves the generic 404 (no JSON schema — same
   finding as J-01/J-05, not re-litigated here).
2. Navigated to `http://localhost:3301/structure` — page loads (`Structure` heading, existing forms/
   controls only); `grep -oi "observation"` over the captured HTML found zero matches — **no new
   panel, link, or control**.
3. Navigated to `http://localhost:3301/desk` — page loads (`Desk` heading, existing controls only);
   `grep -oi "observation"` over the captured HTML found zero matches — **no new panel, link, or
   control**.
4. Confirmed on disk: `docs/goal-archive/goal-2026-09-02.md` exists, `docs/observation-contract-spec.md`
   exists, and `docs/research-directions.md` contains the dated "Observation Contract v1" opening
   note (`grep -n "Observation Contract v1" docs/research-directions.md` → line 1255). `git log
   --oneline -1` on the first two files shows they are committed at `2f3d2b32
   docs(observation-contract): open Observation Contract v1 era` with **zero uncommitted changes**
   (`git status --porcelain` clean on all three paths).
5. Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_guards.py -q` →
   `ERROR: file or directory not found: tests/test_tape_observation_guards.py`.
6. Launched the full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`) in
   the background and ran frontend compile (`cd apps/frontend && npx tsc --noEmit`) — see "Baseline
   suite/config confirmation" below. The backend suite's background run completed after this
   report's initial draft (exit code 0, zero `F`/`E` characters in its captured tail output — 0
   failed independently confirmed by browser-qa-agent; exact `N passed/M skipped` counts not
   captured since only a `tail -30` of the run was piped).
7. Confirmed `config_fingerprint` live-computed (`CONFIG.config_fingerprint()`) = `08e471b10130e1e2`
   (matches the goal's pinned value) and the MCP contract stays at 28 registered tools (`grep -c
   'name="' apps/backend/app/mcp/__init__.py`-style module count, cross-checked against
   `tests/test_mcp_server.py`'s own `len(TOOL_NAMES) == 28` assertion).

**Expected:** All four sub-checks (served route, unchanged pages, era-open docs, guard suite +
green full suite) pass.
**Actual:** Unchanged pages ✓, era-open docs ✓, served route ✗ (still absent, already covered by
J-01/J-05), guard suite ✗ (module absent).

---

## Baseline suite/config confirmation (supports J-06, and DoD's baseline-reference requirement)

- **Backend full suite** (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`): launched in
  the background early in this dispatch; it had not finished when this report was first drafted
  (recorded at that point as `unknown`, per instruction, rather than assumed) and **completed
  afterward with exit code 0**. Its captured output was only the final `tail -30` of the run
  (per the original command), so the exact `N passed / M skipped` counts were not captured by
  browser-qa-agent directly — but that captured tail contains **zero `F` or `E` characters**
  anywhere (only pass-dots and skip-`s` markers), and pytest's exit code is 0 only when there are
  no test failures. This **independently confirms 0 failed** for browser-qa-agent's own re-run,
  consistent with (not merely trusting) the developer handoff
  (`docs/handoffs/goal-observation-contract-iter-0-dev.md`) and reviewer report
  (`reports/reviews/goal-observation-contract-iter-0-review.md`), which each separately recorded
  from their own earlier full-output runs this same iteration: **3930 passed, 8 skipped, 0 failed,
  0 errors (3938 collected)**. This suite result is **not** load-bearing for any of the six journey
  verdicts above (J-01..J-05 are FAIL and J-06 is partial purely on the presence/absence of files
  and routes, independently confirmed by direct filesystem/route inspection); it supports only the
  DoD's baseline-reference and UT-J-06's "full backend suite green" sub-claim, both now
  independently reconfirmed (0 failed) by browser-qa-agent, with the exact pass/skip totals sourced
  from dev/reviewer's matching, independently-obtained figures.
- **Frontend compile** (`cd apps/frontend && npx tsc --noEmit`): independently run by
  browser-qa-agent this dispatch — **0 errors**, exit code 0 (confirmed, not from a background
  process).
- **`config_fingerprint`**: live-computed via `CONFIG.config_fingerprint()` = `08e471b10130e1e2` —
  matches the goal's pinned foundation value, unchanged.
- **MCP contract**: 28 registered tools (v8), matching `tests/test_mcp_server.py`'s
  `len(TOOL_NAMES) == 28` pin — no new tool exists (the route itself is unbuilt, so nothing new
  could be proxied yet).
- No `apps/`, `docs/` (outside this spec + the pre-existing `blueprint.md`), or `project-extensions/`
  file shows any diff (`git status --porcelain` at session end shows only pipeline/report artifacts
  — this iteration's spec doc, this QA report, the goal-session state dir, the dev handoff, the
  review report, and the pre-existing `reports/qa-scoped-backend-store-manifest.md` fixture-rewrite
  file — zero product source changed).

---

## Skipped Tests

None. Frontend and Chrome MCP were both available; all six journeys were exercised.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (the served-JSON surface for all six journeys — the
  frontend has no page for `/tape/{ticker}/observation`; it was opened directly)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless,
  pinned profile/CDP port
- **Test Date:** 2026-09-02
- **Evidence directory:** `reports/qa/goal-observation-contract-iter-0-evidence/`
- **Sim ticker used:** `SIM-BIDABS` (per the goal's Must-have journey steps) plus `ZZZZ` (J-05's
  nonexistent-ticker case)

---

## Golden replay scripts

None written this iteration. No journey verified PASS (all six are correctly FAIL/partial against
the genuinely-unbuilt implementation surface), and per the browser-qa-agent contract goldens are
only produced for journeys that PASS.
