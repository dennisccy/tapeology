# goal-desk-iter-13 Dev Handoff

**Phase:** goal-desk-iter-13
**Date:** 2026-07-28
**Agent:** developer
**Status:** complete

## What Was Built

**Nothing — zero product/application code change**, exactly as this iteration's spec requires. This
is a pure ops/evidence-capture dispatch closing J-09's one remaining acceptance clause: a
`[NEW]`-flagged demo-narrator walkthrough that shows, in ONE artifact and in sequence, the honest
"No top-up runs recorded yet." state and a populated Top-up Runs state. J-09's actual implementation
(`desk_topup_log.py`, `GET /research/desk/topup/runs`, the `/desk` Top-up Runs section) shipped in
iteration 11 and is untouched here — confirmed via `git diff --stat` on every named product file,
empty (see "Verification" below).

Two prior attempts (iteration 11, iteration 12) each failed to close this same clause for two
different, now-diagnosed reasons (lane ordering at lean depth; recording runs before the frontend
ever booted, closing the honest-empty window before any browser existed). This dispatch fixes both
by doing the ENTIRE sequence — boot, capture empty, record, capture populated — myself, in one
continuous pass, on one rig that is never restarted or swapped, matching the plan's explicit
attribution of steps 1–7 and 10–13 to the developer dispatch. Per the plan's own "Downstream
pipeline note," assembling the `[NEW]`-flagged walkthrough JSON from these two captures is the
demo-narrator lane's job, not this dispatch's — see "Known Issues" below.

## Scoped root — absolute path (cite this, not a summary)

```
/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/desk-iter13-scoped-qa
```

Fresh this iteration — distinct from `desk-iter9-scoped-qa` / `desk-iter10-scoped-qa` /
`desk-iter11-scoped-qa` / `desk-iter12-scoped-qa` / `desk-iter12-scoped-qa-empty`. Seeded via the
existing, reusable `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301` — a
full `cp -a` of the ambient `apps/backend/.data/` tree taken at this iteration's start, AFTER the
ambient baseline checksum (§6 below) was already captured. This is the path every downstream stage
(browser-qa-agent, demo-narrator, QA) should point at for J-09's remaining evidence, and the ONLY
data root this iteration's captures/recordings/replays ever touched.

## 1. Environment hygiene (TC-11) — done first, before anything was seeded

Inventoried `:8301`/`:3301`/`:8302`/`:3302` independently at execution time (the spec's own NOTES
section explicitly warned the plan-writing-time observation might be stale):

```
curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://127.0.0.1:<port>/   ->  000 (all four ports)
ss -ltnp | grep -E ':830[12]|:330[12]'                                        ->  no output
pgrep -af uvicorn / "next dev" / "goal-desk-iter9-scoped"                     ->  no matches
```

**Finding: all four ports were already free; nothing was found bound to them, so nothing needed to
be stopped.** Iteration 12's specific leftover PID (`1180202`) and the DIFFERENT idling pair the spec
author observed at plan-writing time (`1298449`/`1298605`+`1298616`) were both already gone by
execution time. No `taskset -pc` check was needed since no process was found.

## 2. Ambient baseline checksum (TC-6 setup) — captured BEFORE any seeding

File listing + SHA-256 of `apps/backend/.data/` (400 files) and `apps/backend/tapeology_journal.db`,
saved under `/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/iter13-evidence/`. Confirmed
at that point: `apps/backend/.data/topup_runs/` does not exist (consistent with every prior
iteration's own finding — no top-up has ever run against the ambient store).

## 3. Scoped rig seeded and booted — collision-checked (TC-11 continued)

Booted the scoped backend (uvicorn, `:8301`) against the freshly-copied root immediately after the
baseline checksum. Live checks:

- `GET http://localhost:8301/research/desk/topup/runs` → `{"runs":[],"latest":null}` — genuine,
  unforced honest-empty state.
- `ls "$SCOPED_ROOT/.data/topup_runs"` → does not exist. **No collision.**
- Universe snapshot present and correct: `universe-2026-07-25-49b33fa31680`, 101 members.

## 4. Clean rebuild + scoped frontend booted BEFORE any run recorded (T-9, the load-bearing fix)

`rm -rf apps/frontend/.next`, then started the scoped frontend (`CHAIN_BACKEND_PORT=8301
CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`) pointed at the scoped backend — **before
recording a single top-up run.** Both confirmed healthy (`GET /health` → 200, `GET /` → 200,
`GET /desk` → 200) with `GET /research/desk/topup/runs` re-confirmed `{"runs":[],"latest":null}` at
that exact live moment (both processes up, zero runs recorded — this is iteration 12's closed window,
reopened correctly this time).

## 5. FIRST capture — the honest empty state, on the live, already-booted rig

Navigated Chrome (attached to the pre-launched headless instance on CDP `:9222`) to
`http://localhost:3301/desk`. The page rendered fully hydrated with a real populated Briefing/Screen
History (from the copied ambient screen snapshots — unrelated to J-09), and the Top-up Runs section
at the bottom legibly read "No top-up runs recorded yet." with the honest circle-slash empty-state
icon.

**Screenshot-capture note (disclosed, not hidden):** a plain post-scroll viewport screenshot came
back solid blank at this page's scroll depth (~4300px) — a known Chrome/CDP paint-timing issue on
this rig (previously documented for a different page in this project's own memory as "deep-scroll
screenshot blank"), reproduced here on THIS page for the first time and confirmed via three
independent attempts (auto-captured post-`eval` screenshot, explicit viewport screenshot, and an
element-scoped `selector` screenshot — all three blank at that scroll position). Worked around by
using the browser tool's native `fullpage: true` capture (which uses a different CDP path,
`captureBeyondViewport`, and rendered correctly), then cropping+2x-upscaling the bottom section with
Pillow for a legible close-up. Both the full-page image and the cropped close-up are saved evidence
— see "Files Changed" below.

Confirmed live at the moment of capture: `GET /research/desk/topup/runs` → `{"runs":[],"latest":null}`.

## 6. Three checkpoint top-up runs recorded (TC-2)

Recorded via a throwaway ops script
(`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/record_checkpoints.py`, NOT part of the
repo — lives only in the pipeline scratchpad) that points `TAPEOLOGY_BAR_DIR` /
`TAPEOLOGY_DESK_UNIVERSE_DIR` / `TAPEOLOGY_DESK_SCREEN_DIR` / `TAPEOLOGY_JOURNAL_DB` at the scoped
root and calls `DeskTopupComputeManager.trigger()` **in-process, three times, sequentially on one
manager instance**, against the REAL production code path — the exact technique
`tests/test_desk_topup_compute.py`'s own `manager_env` fixture uses, and the identical recipe
iteration 11 (browser-QA lane) and iteration 12 (dev lane) already used successfully twice. Zero live
vendor calls at any point.

- **Checkpoint 1 (ordinary):** monkeypatched `_run_one_pair` (always `"fetched"`) →
  `topup-2026-07-28-bad54d19fb21`, `state: done`, `404/404` attempted.
- **Checkpoint 2 (cancelled):** same monkeypatch technique + a `threading.Event` handshake, cancelled
  after 3 pairs → `topup-2026-07-28-a45eb8397844`, `state: cancelled`, `3/404` attempted.
- **Checkpoint 3 (one induced failure):** restored the REAL (unpatched) `_run_one_pair` and overrode
  `get_market_adapter` with a small double copied verbatim from
  `test_desk_topup_compute.py`'s own `_NthCallFailsAdapter` (fails on the first real, non-store-first
  call with `NoDataForWindow("no data for that window")`, synthetic bars otherwise) →
  `topup-2026-07-28-c4de94d71e04`, `state: done`, `404/404` attempted, `0 reused · 403 fetched · 1
  failed` — the failed pair is `AAPL 1h`, detail `"no data for that window"` (verbatim, confirmed live
  via `GET /research/desk/topup/runs` against the still-running scoped backend process — a SEPARATE
  process from the recording script — proving the file-based store's fresh-per-request read works as
  designed, with zero restart).

Full structured result saved at `.../desk-iter13-scoped-qa/checkpoint-recording-result.json`.
`topup_run_store.list()` confirmed `errors == []` and exactly 3 records, both immediately after the
script ran and independently via a live `curl` against the unrestarted scoped backend afterward.

**Side-effect disclosure (honesty, not a defect — the iteration-12 precedent):** checkpoint 3's REAL
`_run_one_pair` walk wrote 403 new synthetic bar series into the SCOPED copy's bar store (every pair
was a fresh call, `0 reused`, because the store-first key is the exact `[start, end]` fetch window,
which shifts daily — even AAPL/AMD/MSFT's real bars were not store-first hits today, matching
iterations 11 and 12's own identical `"0 reused"` observation on their own days). **Verified this does
NOT corrupt anything the regression set depends on**: the desk top-up's four timeframes
(`1h`/`4h`/`1d`/`1w`) are disjoint from the `1m` microscope timeframe the pinned-AAPL-2026-06-22 wall
(J-07/J-05) actually reads — confirmed live on this rig,
`GET /research/tradability?symbol=AAPL&as_of=2026-06-22T21:00:00Z` still returns
`resistance 300.11–302.2 class A quality_score 171.0`, byte-identical to `docs/goal.md`'s own cited
value. Entirely confined to the scoped copy; the ambient store took zero writes (§8).

## 7. SECOND capture — the populated Top-up Runs state, same still-live rig

Reloaded `http://localhost:3301/desk` on the SAME backend and frontend processes (never restarted or
swapped) and captured the populated Top-up Runs section via the same full-page-then-crop technique
(§5). The image legibly shows, in one frame: the 3-row run table (`done 404/404`, `cancelled 3/404`,
`done 404/404`), the line "state: done   404 of 404 pairs attempted   0 reused · 403 fetched ·
1 failed", and "Failed pairs (1): AAPL 1h — no data for that window".

## 8. Regression replay — J-01 through J-08 against the scoped rig (TC-7)

`demo_runner.py --mode verify --scripts-dir runs/goal-session-desk/journey-scripts --journeys
J-01,J-02,J-03,J-04,J-05,J-07,J-08 --base-url http://localhost:3301 --timeout-ms 30000` (J-06 excluded
— no browser surface, re-confirmed separately, see §9). Report:
[`reports/phase-goal-desk-iter-13-smoke-replay-results.md`](../../reports/phase-goal-desk-iter-13-smoke-replay-results.md).

**Result: 7/7 PASS, 0 failed, on the reported clean run.** A first pass reported `UT-J-07` FAIL (step
04, "Watch" click → expect "Buyer Control" timed out) — J-07.json's own embedded
`default_timeout_ms: 15000` governs that step regardless of my `--timeout-ms 30000` CLI flag (a
different mechanism than iteration 12 assumed; disclosed precisely in the replay report). Stopped the
SIM-BUYER watch the failed attempt left running (`DELETE /watch/SIM-BUYER` → `{"status":"stopped"}`,
the iteration-12 leftover-feeder lesson applied proactively), retried J-07 alone (passed immediately),
then re-ran the full 7-journey set together end to end with 0 failed — that clean run is the reported
verdict, fully disclosed in the replay report's own "Note" section, not hidden.

None of J-01–J-08's own golden steps click a Run Screen/Top-up/Compute control (verified by reading
every script before replaying) — J-05/J-07 click navigation/watch/load controls that are existing
KEPT-surface behavior, so replaying them against the scoped rig carries no anti-goal risk in either
direction. `journey-scripts/J-09.json` was NOT touched by this dispatch (it is independently
read-only/goto-only per its own notes and is not part of the required regression set — J-09 is this
iteration's target, not yet `passing`).

## 9. Full backend suite + fingerprint + MCP contract (TC-8, TC-9)

`cd apps/backend && .venv/bin/python -m pytest tests/ -v` (a fresh shell, confirmed zero `TAPEOLOGY_*`
env vars leaked in before running):

```
1369 passed, 8 skipped, 2 warnings in 135.84s (0:02:15)
```

Meets the required floor exactly (≥1369 passed / 8 skipped / 0 failed) — no product/test files
changed, so no growth expected, none occurred.

`Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).

`tests/test_mcp_server.py` re-run in isolation: **35 passed**, `EXPECTED_TOOLS` confirmed to hold
exactly 17 entries (verbatim: `tape_state`, `tape_features`, `tape_history`, `datasets`, `bars`,
`levels`, `tradability`, `setups`, `backtests`, `strategies`, `edge_report`, `desk_universe`,
`desk_screen`, `pnl_ledger`, `taxonomy`, `ui_route_map`, `get_endpoint`) — the 17-tool contract holds
unmodified (TC-8, closes J-06 without a browser pass).

## 10. Ambient store — zero write, proven byte-for-byte (TC-6)

Re-captured `apps/backend/.data/`'s file listing + SHA-256 checksums (plus `tapeology_journal.db`)
after all work completed and diffed against the pre-work baseline:

```
LISTING: IDENTICAL (400 files before, 400 after -- zero new/deleted files)
CHECKSUMS: IDENTICAL (zero modified file) -- including tapeology_journal.db
```

`apps/backend/.data/topup_runs/` still does not exist in the ambient tree. Nothing this iteration
touched the ambient store at any point.

## Live scoped processes left running for downstream lanes

| Process | PID | Port | Command |
|---|---|---|---|
| Backend (uvicorn) | **1419904** | 8301 | `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/desk-iter13-scoped-qa" 8301` |
| Frontend (next dev) | 1421592 (npm wrapper) / 1421611 (node) | 3301 | `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh` |

Both confirmed healthy in a final check, with the 3 checkpoint runs still correctly persisted and
readable from disk. Left running (matching the established iteration-10/11/12 precedent for this
era's scoped browser-QA rig on its own dedicated, non-default ports) so any downstream lane that wants
to independently reload the live page can do so without re-seeding — though note "Known Issues" below:
neither this iteration's demo-narrator lane nor QA is required to redo any capture this dispatch
already produced.

**Fallback restart recipe**, if either process is gone by the time you need it (data is all on disk —
a restart loses nothing):

```bash
cd /home/dennis-chan/Git/tapeology
SCOPED_ROOT="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/desk-iter13-scoped-qa"
nohup bash apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301 > /tmp/backend.log 2>&1 &
nohup env CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh > /tmp/frontend.log 2>&1 &
```

**CRITICAL — do not click "Top-up" (or "Run Screen") on this scoped instance.** The Top-up Runs
demo depends on checkpoint 3 (`topup-2026-07-28-c4de94d71e04`, the induced-failure run) being the
*latest* recorded run — the `/desk` page's detail panel only shows the LATEST run's per-outcome
breakdown and failed-pair detail. A real click would start a 4th, uncontrolled top-up walk (against
the REAL keyless Yahoo adapter this time — no override on the live server) that would supersede
checkpoint 3 as "latest" and bury the failed-pair evidence this dispatch produced. This scoped
instance is for **reading** (GETs, page loads, screenshots) only.

## Files Changed

- `reports/phase-goal-desk-iter-13-smoke-replay-results.md` — regression replay report (7/7 PASS),
  with the scoped-root disclosure and the J-07 timing-flake note.
- `reports/qa/goal-desk-iter-13-evidence/J-01-verify.png` through `J-08-verify.png` (7 screenshots)
  — deterministic-replay evidence, scoped rig.
- `reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-fullpage.png` — full-page capture, honest-empty
  state, live rig, before any run recorded.
- `reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-topup-section.png` — cropped/upscaled close-up
  of the same capture, legible.
- `reports/qa/goal-desk-iter-13-evidence/UT-J-09-populated-fullpage.png` — full-page capture, populated
  state, same still-live rig, after the 3 checkpoint runs.
- `reports/qa/goal-desk-iter-13-evidence/UT-J-09-populated-topup-section.png` — cropped/upscaled
  close-up of the same capture, legible.
- `docs/handoffs/goal-desk-iter-13-dev.md` — this handoff.

**Not touched** (verified via `git diff --stat`, empty): `desk_topup_log.py`, `desk_topup_compute.py`,
`desk_routes.py`, `desk_screen.py`, `desk_coverage.py`, `tradability.py`, `levels.py`, `bars.py`,
`apps/frontend/app/desk/page.tsx`, `lib/types.ts`, `lib/api.ts`, `StructureChart.tsx`,
`PriceChart.tsx`, `config.py`, `meta.py`, `app/mcp/__init__.py` — the complete OUT OF SCOPE list, all
sixteen files, zero diff. `journey-scripts/J-09.json` also not touched (disclosed per the iter-8
lesson even though not required).

**Not part of the repo** (throwaway ops tooling, lives only in the pipeline scratchpad, never
committed): `/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/record_checkpoints.py`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1369 passed, 8 skipped, 0 failed** (meets the required floor exactly).

Also run individually: `tests/test_mcp_server.py` (35/35, 17-tool contract confirmed).

Regression replay (`demo_runner.py --mode verify`, scoped rig): **7/7 PASS** (J-01–J-05, J-07, J-08)
at `--timeout-ms 30000` — see §8 for the one disclosed transient retry.

Fingerprint: `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).

## Pre-handoff verification

- **Service startup works:** scoped backend + frontend both confirmed starting cleanly on `:8301`/
  `:3301` with no port conflicts (§1 confirmed nothing was listening on either port beforehand). Per
  this era's own established precedent (iterations 10/11/12), these processes are **deliberately left
  running** on their own dedicated, non-default, non-ambient-conflicting ports for downstream lanes —
  see the table and restart recipe above. No ambient-facing server (`:8000`/`:3000`) was started or
  touched by this dispatch.
- **External integrations:** none — zero live vendor calls anywhere this iteration (checkpoint 3's
  failure and its 403 "fetched" pairs both came from an in-process fake adapter, never the network).
- **Native dependencies:** none added. `demo_runner.py --mode verify` needed system `python3` with a
  user-level Playwright install (not `apps/backend/.venv`), matching iteration 12's own disclosed
  environment note — nothing needed installing.

## Known Issues

- **Assembling the `[NEW]`-flagged demo-narrator walkthrough JSON is explicitly NOT this dispatch's
  job** — per the plan's own "Downstream pipeline note": "the demo-narrator lane owns assembling the
  `[NEW]`-flagged walkthrough JSON from the developer's two same-rig captures." What this dispatch
  guarantees is that both captures exist, are legible, are drawn from the SAME never-restarted rig, in
  the correct sequence (empty first, populated second), and that the scoped-root path is stated in
  this handoff and in the smoke-replay-results report (TC-5). The demo-narrator lane still needs to
  run and produce that artifact for J-09's acceptance text to be fully closed.
- **Deep-scroll viewport screenshots on `/desk` came back blank on this Chrome/CDP setup** (§5) —
  worked around with `fullpage: true` capture + a Pillow crop/upscale, both saved. This is a capture
  tooling quirk, not a product defect (the page itself rendered and hydrated correctly at every check,
  confirmed via DOM/markdown extraction and via `eval` element-rect queries at the exact same scroll
  position that produced a blank plain-viewport screenshot).
- The J-07 timing flake (§8) is disclosed, not silently retried away — the first attempt's own FAIL is
  on record inside the replay report's own text, not hidden.
- Checkpoint 3's real bar-store side effect (§6) is disclosed for transparency even though it is
  confirmed harmless to every existing regression check.
- Standalone browser-qa-agent screenshots for J-09's two states are NOT part of this dispatch — already
  DONE and evaluator-opened from iteration 12
  (`reports/qa/goal-desk-iter-12-evidence/UT-J-09-empty-topup-section.png`,
  `UT-J-09-populated-topup-section.png`) — binding "do not redo" per the plan.
- I did not attempt to trigger a top-up or screen run against the ambient store at any point (out of
  scope, and the anti-goal this whole iteration is built around avoiding).
