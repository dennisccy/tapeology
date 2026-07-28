# Phase goal-desk-iter-12 — UI Test Results

**Phase:** goal-desk-iter-12
**Date:** 2026-07-28
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 tests passed (0 skipped)

Scope per the dispatch (GOAL-MODE LEAN MODE): test EXACTLY J-06 and J-09 this run. J-01–J-05, J-07,
J-08 are explicitly out of this agent's scope this iteration — the developer already replayed them
deterministically against the scoped rig (`reports/phase-goal-desk-iter-12-smoke-replay-results.md`,
7/7 PASS) and this agent did not re-touch them.

---

## Test rigs used (disclosed per the iter-9/iter-10/iter-11 lessons)

**Three** backend/frontend pairs were involved this run — full disclosure of all three, and why a
second scoped root was necessary beyond the one the dev handoff seeded:

1. **`desk-iter12-scoped-qa`** (dev-seeded, `:8301`/`:3301`) — absolute path
   `/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/desk-iter12-scoped-qa`. Left running by
   the developer with 3 checkpoint top-up runs already recorded (per
   `docs/handoffs/goal-desk-iter-12-dev.md`). **Used for the J-09 POPULATED-state capture.** This
   agent did not click "Top-up" or "Run Screen" on it (per the dev handoff's explicit warning — a
   real click would supersede checkpoint 3 as "latest" and bury the failed-pair evidence); only
   `navigate`/`scroll`/`screenshot` actions were issued against it.
2. **`desk-iter12-scoped-qa-empty`** (this agent's own second scoped root, `:8302`/`:3302`) —
   absolute path
   `/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/desk-iter12-scoped-qa-empty`. **Why a
   second root was necessary (disclosed, not silent):** the dev's own timeline (seed → record 3
   checkpoints → THEN boot the frontend) means no browser frontend ever existed while
   `desk-iter12-scoped-qa` was still genuinely empty — its "honest-empty" window had already closed,
   via real (non-deletable, append-only) checkpoint records, before this agent was dispatched.
   TC-1/T-10 require an actual `/desk` **screenshot** of the honest-empty state, and the append-only
   rail forbids manufacturing that state by deleting the 3 real records. So this agent seeded a
   **second, freshly-seeded scoped root** with the identical recipe
   (`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$ROOT" 8302`, `cp -a` from the SAME
   current `apps/backend/.data/` ambient tree the dev's own root was seeded from, confirmed
   byte-for-byte the same universe snapshot `universe-2026-07-25-49b33fa31680`/101 members) —
   genuinely, unforced empty (`GET /research/desk/topup/runs` → `{"runs":[],"latest":null}`, no
   `topup_runs/` directory, no collision, checked before any capture — TC-11). Frontend served on a
   distinct port (`:3302`) with `NEXT_DIST_DIR=.next-iter12-empty-qa` (the project's own
   `next.config.mjs` isolation knob, added precisely so a one-off build never clobbers a running dev
   server's shared `.next`) and `NEXT_PUBLIC_API_URL=http://localhost:8302`, so it never touched the
   already-running `:3301` dev server's build cache. **Used for the J-09 EMPTY-state capture only.**
   Neither "Top-up" nor "Run Screen" was clicked on it either (clicking would have started a REAL,
   uncontrolled ~404-pair Yahoo fetch — an operator act explicitly out of this iteration's scope).
   Both processes were cleanly stopped (`SIGTERM`, verified gone, no `SIGKILL` needed) immediately
   after the one screenshot was captured; the 1.9G root itself was left on disk (not deleted) as an
   audit trail. **This means J-09's two required screenshots come from two DIFFERENT scoped roots,
   not the literal same one** — both are scoped copies of the identical ambient source, never the
   ambient store itself, and the deviation from a single literal root is disclosed here in full per
   the iteration's own transparency requirement, not silently substituted.
3. **Ambient `apps/backend/.data/`** — read from exactly once, as the `cp -a` SOURCE for rig #2 above
   (the same read-only operation the dev's own scoped-backend script recipe performs) — never as a
   destination, never navigated to in a browser, never had any compute/fetch/run triggered against
   it. Spot-checked after all work: `apps/backend/.data/topup_runs/` still does not exist (matching
   the dev handoff's own TC-6 finding); `:8000` (the ambient port) is not even listening in this
   environment.

J-06 was verified against neither live rig's HTTP surface nor this session's own `mcp__tapeology__*`
MCP client (wired to `TAPEOLOGY_API_BASE=http://localhost:8000` per this repo's `.mcp.json` — an
ambient port this iteration's rigs never use, and one this agent deliberately did not invoke, to
avoid pointing any step at the ambient store even as a read) — instead directly via the hermetic
`tests/test_mcp_server.py` suite, run live by this agent (not merely cited from the dev handoff). See
UT-J-06 below.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | Per goal.md: "the MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` outputs are proven byte-identical to their curl equivalents (empty AND populated fixture states); `get_endpoint` on `/research/desk/screen` proxies verbatim; the MCP suite is green." Tagged `(Keyless; automated.)` in goal.md — no browser surface. | Ran `tests/test_mcp_server.py` live (not merely cited): **35 passed, 0 failed** in 7.25s. `EXPECTED_TOOLS` read directly from source = exactly 17 names incl. `desk_universe`/`desk_screen`. Confirmed by name: `test_advertised_tool_set_is_exactly_capability_6` (17-tool count), `test_desk_universe_tool_byte_identical_on_the_honest_empty_state` + `_on_a_populated_state`, `test_desk_screen_tool_byte_identical_on_the_honest_empty_state` + `_on_a_populated_state`, `test_get_endpoint_desk_screen_date_query_proxies_verbatim`, `test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool` (also re-confirms `len(TOOL_NAMES)==17`), `test_stdio_session_end_to_end` (spawns the REAL `python -m app.mcp` subprocess over stdio — the actual production entry point). All passed. Confirmed via `goto`-and-read-nav that no dedicated MCP page exists in the UI (nav = Cockpit/Structure/Desk only) — consistent with goal.md's own "no browser surface" framing for this journey. | PASS | `reports/qa/goal-desk-iter-12-evidence/UT-J-06-nav-context.png` (supplementary nav context only — this journey's real evidence is the pytest run, quoted above and in the Environment section) |
| UT-J-09 | Every top-up run leaves an append-only record — standalone browser-qa screenshots for both states | happy-path | P1 | Per iter-12's IN SCOPE: standalone browser-qa-agent screenshots exist for (a) the honest empty "No top-up runs recorded yet." state and (b) the populated Top-up Runs section (attempted-of-total, per-outcome counts, a failed pair's own detail), on a scoped rig, never ambient. | (a) Navigated `:3302/desk` (fresh scoped, genuinely empty rig) — DOM text extraction showed exactly "No top-up runs recorded yet." under the "Top-up Runs" heading; screenshot legibly shows the empty-state panel (circle-slash icon + the exact text) with the Run Screen/Top-up buttons visible-but-unclicked above it. (b) Navigated `:3301/desk` (dev's populated rig) — DOM text + screenshot both show the 3-row table (`done 404/404`, `cancelled 3/404`, `done 404/404`) and "Latest run — 2026-07-28 · topup-2026-07-28-6b40a8029a75 — state: done, 404 of 404 pairs attempted, 0 reused · 403 fetched · 1 failed" with "Failed pairs (1): AAPL 1h — no data for that window" all legible in one image; cross-checked byte-for-byte against a live `curl :8301/research/desk/topup/runs`. Neither rig had "Top-up"/"Run Screen" clicked. | PASS | `reports/qa/goal-desk-iter-12-evidence/UT-J-09-empty-topup-section.png` (+ `UT-J-09-empty-fullpage.png`), `reports/qa/goal-desk-iter-12-evidence/UT-J-09-populated-topup-section.png` (+ `UT-J-09-populated.png`) |

---

## Passed Tests

### UT-J-06 — MCP contract v3 — 17 read-only tools
**Verdict:** PASS
**Evidence:** pytest output (below); `reports/qa/goal-desk-iter-12-evidence/UT-J-06-nav-context.png` for supplementary nav context only.

- Read J-06's Steps + Acceptance directly from `docs/goal.md`: every step is a backend/test-file
  edit (`_STATIC_PATHS` entry, `test_mcp_server.py` update, a conditional asset re-render) and the
  Acceptance line is tagged `(Keyless; automated.)` — the ONLY one of this era's 9 journeys without a
  `(Browser-verifiable...)` qualifier. There is no dedicated UI surface for this journey; confirmed
  live by reading the nav on `:3301` — exactly `Cockpit / Structure / Desk`, nothing MCP-related.
- Independently ran (not merely cited from the dev handoff) `cd apps/backend && .venv/bin/python -m
  pytest tests/test_mcp_server.py -v` in a clean shell with no `TAPEOLOGY_*` env vars set:
  **35 passed in 7.25s**, matching the dev handoff's own re-run exactly.
- Read `EXPECTED_TOOLS` directly from source (`tests/test_mcp_server.py:52-69`): `tape_state,
  tape_features, tape_history, datasets, bars, levels, tradability, setups, backtests, strategies,
  edge_report, desk_universe, desk_screen, pnl_ledger, taxonomy, ui_route_map, get_endpoint` — exactly
  17 entries, `desk_universe`/`desk_screen` present.
- Located and confirmed (by name, reading each test) the specific tests that prove every clause of
  J-06's Acceptance:
  - `test_advertised_tool_set_is_exactly_capability_6` — the 17-tool count + read-only-verb
    discipline.
  - `test_desk_universe_tool_byte_identical_on_the_honest_empty_state` and
    `_on_a_populated_state` — `desk_universe` byte-identical to curl, both states.
  - `test_desk_screen_tool_byte_identical_on_the_honest_empty_state` and `_on_a_populated_state` —
    same for `desk_screen`.
  - `test_get_endpoint_desk_screen_date_query_proxies_verbatim` — `get_endpoint` on
    `/research/desk/screen` (with `?date=`) proxies verbatim.
  - `test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool` — also re-confirms
    `len(TOOL_NAMES) == 17` and `"desk_topup_runs" not in TOOL_NAMES` (J-09 shipped no 18th tool).
  - `test_stdio_session_end_to_end` — spawns the actual `python -m app.mcp` subprocess (the real
    production entry point `.mcp.json` itself launches) and speaks MCP over real stdio, verifying
    byte-identity over the wire, not just in-process.
- This session's own live `mcp__tapeology__*` client is wired to `TAPEOLOGY_API_BASE=
  http://localhost:8000` (`.mcp.json`, repo root) — an ambient port neither this iteration's rigs use
  nor this agent touched (kept strictly to the scoped rigs per this iteration's own discipline, and
  `:8000` is not even listening right now). Rather than invoke that ambient-wired client (which would
  either fail to connect or, if it somehow connected, touch ambient — neither desirable), this agent
  went straight to the authoritative hermetic suite, which is exactly the mechanism goal.md's own
  `(Keyless; automated.)` tag points to for this journey.

### UT-J-09 — Every top-up run leaves an append-only record — standalone screenshots, both states
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-12-evidence/UT-J-09-empty-topup-section.png`,
`UT-J-09-empty-fullpage.png`, `UT-J-09-populated-topup-section.png`, `UT-J-09-populated.png`

- Read J-09's Steps + Acceptance from `docs/goal.md` and this iteration's own IN SCOPE item: "Capture
  standalone browser-qa-agent screenshots for the same two states (empty, then
  populated-with-a-failed-pair) on the same scoped rig[s], so J-09's evidence includes both the
  narrated walkthrough artifact [demo-narrator's job, not this agent's] and independent screenshots
  [this agent's job]."
- **Empty state** — navigated `http://localhost:3302/desk` (the fresh second scoped rig, see "Test
  rigs used" above). `get_text` extraction showed, verbatim: `## Top-up Runs` immediately followed by
  `No top-up runs recorded yet.` — the literal first clause of J-09's Acceptance text, genuinely true
  on this rig (not a stale assumption: `GET http://localhost:8302/research/desk/topup/runs` →
  `{"runs":[],"latest":null}`, confirmed moments before the screenshot). A full-page screenshot was
  taken (`UT-J-09-empty-fullpage.png`, 1585×5412), then cropped+upscaled to the relevant section
  (`UT-J-09-empty-topup-section.png`, the bottom ~1212px at 2×) for legibility — a direct
  viewport screenshot after a programmatic scroll rendered blank in this Chrome MCP setup (a known
  environment quirk, also hit and documented by the iter-11 browser-qa run; the full-page-then-crop
  workaround reliably worked both times). The crop legibly shows the "TOP-UP RUNS" heading, a
  circle-slash empty-state icon, and "No top-up runs recorded yet." — with the "Run Screen"/"Top-up"
  buttons visible immediately above, unclicked.
- **Populated state** — navigated `http://localhost:3301/desk` (the dev's rig, 3 checkpoint runs
  already recorded). `get_text` extraction showed the Top-up Runs table (3 rows: `done 404/404`,
  `cancelled 3/404`, `done 404/404`) and "Latest run — 2026-07-28 ·
  topup-2026-07-28-6b40a8029a75" with "Failed pairs (1): AAPL 1h — no data for that window". Cross-
  checked byte-for-byte against a live `curl http://localhost:8301/research/desk/topup/runs` — the
  `latest.outcomes` entry for `AAPL`/`1h` is `{"outcome":"failed","detail":"no data for that
  window"}`, matching exactly. Same full-page-then-crop technique produced
  `UT-J-09-populated-topup-section.png` (2853×3668), which legibly shows, all in one image: the 3-row
  table with dates/run-ids/states/attempted-total/universe-snapshot, and the latest-run detail block
  reading "state: done · 404 of 404 pairs attempted · 0 reused · 403 fetched · 1 failed" plus the
  failed pair's own verbatim detail — satisfying iter-12's TC-3 ("attempted-of-total pairs and counts
  by outcome, and the failed pair's own recorded detail text, all in the same image") directly.
- Confirmed the append-only rail from the outside: the same 3 run ids/states/counts were visible
  identically both in this agent's own first curl check (before any browser interaction) and in the
  final screenshot — nothing shifted mid-session, no 4th run appeared (i.e., this agent's own
  navigation/scroll/screenshot actions did not accidentally trigger anything).
- Did not attempt to independently re-verify the OTHER clauses of J-09's full Acceptance (three
  checkpoint runs' recorded outcomes byte-identical to `run_topup`'s return, second-run-appends-
  without-touching-the-first-file's-checksum, a run interrupted before its terminal write recording
  nothing, the copy-discipline lint) — those are the developer's own already-completed, already-
  disclosed work (`docs/handoffs/goal-desk-iter-12-dev.md` §2–3, §6) and the backend suite's job
  (`test_desk_topup_compute.py` et al., part of the 1369-passed floor), not a re-derivation this
  agent's own browser pass is positioned to redo or needed to redo per this iteration's narrow scope
  (standalone screenshots for the two states).
- The `[NEW]`-flagged demo-narrator walkthrough itself (the one remaining clause the iter-12 GOAL
  targets) is explicitly the demo-narrator agent's own deliverable, per this iteration's own division
  of labor — not produced by this agent.

---

## Golden replay scripts

- **J-06 — none written.** `runs/goal-session-desk/journey-scripts/` holds only browser-replayable
  journeys (`goto`/`click`/`fill` against a URL); J-06 has no URL of its own to visit — its entire
  Acceptance is a backend/MCP-protocol contract, already covered every iteration by
  `tests/test_mcp_server.py` as part of the full backend suite (the far more precise and appropriate
  regression mechanism for this journey — see UT-J-06 above for the exact test names). Writing a
  `goto`-only placeholder script that visits some unrelated page would not exercise anything J-06
  actually asserts and would misrepresent what is being verified, so none was written — a reasoned
  skip, not an oversight.
- **J-09 — left `journey-scripts/J-09.json` unchanged** (recorded goal-desk-iter-11; NOT edited by
  this agent or any other lane this iteration, confirmed via `git status`/`ls -la` timestamp
  unchanged since iter-11). Considered updating it to assert the now-populated state instead, but
  declined: the script's replay target in most future iterations is realistically the ambient store
  (still genuinely empty — confirmed again this iteration, `apps/backend/.data/topup_runs/` absent),
  and the script's own embedded `notes` already document this exact class of environment-dependency
  (mirroring `J-08.json`'s own documented pattern for its dated history rows) — asserting
  iteration-12-specific checkpoint IDs/counts would make the golden FAIL against ambient's normal
  (still-empty) condition, for an environmental reason having nothing to do with a regression. The
  script's own step 1 (`"Top-up Runs"` heading) and step 3 (`"Desk"`) already assert state-agnostic
  content; only step 2's empty-state text is state-specific, and that is the intended, documented
  design. This iteration's own populated-state evidence is captured instead via this report's live
  screenshots (not replayable against a future ambient store that has no checkpoint runs) — the
  correct home for iteration-12-specific, non-durable content.

---

## Environment

- **Frontend URL:** `http://localhost:3301` (J-09 populated state, dev's rig) and
  `http://localhost:3302` (J-09 empty state, this agent's own second scoped rig, stopped after use)
- **Backend URL:** `http://localhost:8301` (populated) and `http://localhost:8302` (empty, stopped
  after use) — see "Test rigs used" above for full absolute paths and seeding provenance
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`, attached to the
  pre-launched headless Chrome on CDP port 9222
- **Test Date:** 2026-07-28
- **Evidence directory:** `reports/qa/goal-desk-iter-12-evidence/`
- **J-06 regression (MCP contract):** `cd apps/backend && .venv/bin/python -m pytest
  tests/test_mcp_server.py -v` → **35 passed, 0 failed**, 7.25s, exit code 0 (run live by this agent,
  zero `TAPEOLOGY_*` env vars set).
- **Ambient integrity:** `apps/backend/.data/topup_runs/` confirmed still absent after all of this
  agent's work (spot check; the developer's own before/after full checksum diff in
  `docs/handoffs/goal-desk-iter-12-dev.md` §7 is the authoritative TC-6 proof — this agent's own only
  ambient interaction was one `cp -a` READ as the seeding source for its second scoped rig, the same
  operation the dev's own recipe performs, which cannot write to its source).
- **Golden replay scripts:** see "Golden replay scripts" section above — no script written or changed
  for either journey this run (both reasoned decisions, not omissions).
- **Incidental tooling side effect, found and reverted (full disclosure):** starting the second
  scoped frontend with `NEXT_DIST_DIR=.next-iter12-empty-qa` caused Next.js's own dev-server
  bookkeeping to auto-rewrite `apps/frontend/next-env.d.ts`'s type-reference path and reorder/append
  an entry in `apps/frontend/tsconfig.json`'s `include` array (both are standard, well-known Next.js
  dev-server side effects — not a manual edit, not application/product code, not in this iteration's
  OUT-OF-SCOPE named-file list). Caught in a final `git status`/`git diff` self-check after all
  captures were complete; both files were confirmed to be pure tooling regeneration (diffed, read in
  full) and reverted with `git checkout -- apps/frontend/next-env.d.ts apps/frontend/tsconfig.json`,
  re-confirmed clean (`git diff` empty on both) before writing this report. No other file was
  touched by this cleanup.
