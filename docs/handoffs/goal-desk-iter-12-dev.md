# goal-desk-iter-12 Dev Handoff

**Phase:** goal-desk-iter-12
**Date:** 2026-07-28
**Agent:** developer
**Status:** complete

## What Was Built

**Nothing — zero product/application code change**, exactly as this iteration's spec requires. This
is a pure evidence-capture/showcase dispatch closing J-09's one remaining acceptance clause (a
`[NEW]`-flagged demo-narrator walkthrough that shows BOTH the honest-empty AND a populated Top-up
Runs state). J-09's actual implementation (`desk_topup_log.py`, `GET /research/desk/topup/runs`,
the `/desk` Top-up Runs section) shipped in iteration 11 and is untouched here — confirmed via
`git diff --stat` on every named product file, empty (see "Verification" below).

This dispatch's own job was the backend/ops half of the iteration's IN SCOPE checklist: seed a
fresh scoped rig, record three checkpoint top-up runs into it via the real production code paths,
boot a live scoped backend+frontend pair for the downstream browser-qa-agent/demo-narrator stages,
replay the regression set against that same rig, and prove the ambient store was never touched.

## Scoped root — absolute path (cite this, not a summary)

```
/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/desk-iter12-scoped-qa
```

Fresh this iteration — distinct from `desk-iter9-scoped-qa` / `desk-iter10-scoped-qa` /
`desk-iter11-scoped-qa` (the NOTES-section lesson). Seeded via the existing, reusable
`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301` — a full `cp -a` of
the ambient `apps/backend/.data/` tree taken at this iteration's start. **This is the path every
downstream stage (browser-qa-agent, demo-narrator) should point at** for J-09's remaining evidence.

## Evidence capture — what was done and verified

### 1. Ambient baseline captured before any work (TC-6 setup)

File listing + SHA-256 checksums of `apps/backend/.data/` (400 files) and
`apps/backend/tapeology_journal.db`, saved under
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/iter12-evidence/ambient-before-*`.
Confirmed at that point: `apps/backend/.data/topup_runs/` does not exist (no top-up has ever run
against the ambient store — consistent with iteration 11's own finding).

### 2. Scoped rig seeded; BEFORE state verified honest-empty (TC-1); collision-checked (TC-11)

Booted the scoped backend (uvicorn, `:8301`) against the freshly-copied root. Live checks:

- `GET http://localhost:8301/research/desk/topup/runs` → `{"runs":[],"latest":null}` — genuine,
  unforced honest-empty state.
- `ls .../desk-iter12-scoped-qa/.data/topup_runs` → does not exist. **No collision**: the scoped
  copy never received any pre-existing top-up-run record (the store's own append-only, no-dedup
  design means there is no key a new run could even collide against — disclosed per the iter-10
  lesson regardless).
- Universe snapshot present and correct: `universe-2026-07-25-49b33fa31680`, 101 members.

### 3. Three checkpoint top-up runs recorded (TC-2)

Recorded via a throwaway ops script
(`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/record_checkpoints.py`, NOT part of the
repo — lives only in the pipeline scratchpad) that points `TAPEOLOGY_BAR_DIR` /
`TAPEOLOGY_DESK_UNIVERSE_DIR` / `TAPEOLOGY_JOURNAL_DB` at the scoped root and calls
`DeskTopupComputeManager.trigger()` **in-process, three times**, against the REAL production code
path — the exact technique `tests/test_desk_topup_compute.py`'s own manager-mechanics tests use
(`manager_env` fixture), and the same recipe iteration 11's own browser-QA lane used for its
checkpoints 1/2. Zero live vendor calls at any point.

- **Checkpoint 1 (ordinary):** monkeypatched `_run_one_pair` (always `"fetched"`) →
  `topup-2026-07-28-52e271eacc44`, `state: done`, `404/404` attempted.
- **Checkpoint 2 (cancelled):** same monkeypatch technique + a `threading.Event` handshake,
  cancelled after 3 pairs (matching iteration 11's own "cancel after 3" shape) →
  `topup-2026-07-28-ab37e4005b08`, `state: cancelled`, `3/404` attempted.
- **Checkpoint 3 (one induced failure):** restored the REAL (unpatched) `_run_one_pair` and
  overrode `get_market_adapter` with a small double mirroring
  `test_desk_topup_compute.py`'s own `_NthCallFailsAdapter` (fails on the first real, non-store-first
  call with `NoDataForWindow("no data for that window")`, synthetic bars otherwise) →
  `topup-2026-07-28-6b40a8029a75`, `state: done`, `404/404` attempted, `0 reused · 403 fetched ·
  1 failed` — the failed pair is `AAPL 1h`, detail `"no data for that window"` (verbatim, confirmed
  live via `GET /research/desk/topup/runs` after the fact, not just the script's own stdout).

Full structured result saved at
`.../desk-iter12-scoped-qa/checkpoint-recording-result.json`. `topup_run_store.list()` confirmed
`errors == []` (no integrity error) and exactly 3 records, both immediately after the script ran and
again independently via a live `curl` after restarting the scoped backend (see §6 below).

**Side-effect disclosure (honesty, not a defect):** checkpoint 3's REAL `_run_one_pair` walk wrote
403 new synthetic bar series (from the fake adapter's placeholder OHLC) into the SCOPED copy's bar
store for whichever `(symbol, timeframe)` pairs were not already store-first-satisfied under
*today's* fetch window (the store-first key is the exact `[start, end]` window string, which shifts
daily — so even AAPL/AMD/MSFT's real bars were NOT store-first hits today, matching iteration 11's
own identical `"0 reused"` observation on a different day). **Verified this does NOT corrupt
anything the regression set depends on**: the desk top-up's four timeframes (`1h`/`4h`/`1d`/`1w`)
are disjoint from the `1m` microscope timeframe the pinned-AAPL-2026-06-22 wall (J-07) and the
J-05 drill-in actually read — confirmed live, `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T21:00:00Z`
on the scoped rig still returns `resistance 300.11–302.2 class A score 171`, byte-identical to
`docs/goal.md`'s own cited value. This is entirely confined to the scoped copy; never touches
ambient (see §7).

### 4. Clean rebuild + scoped frontend (T-9)

`rm -rf apps/frontend/.next`, then started the scoped frontend (`CHAIN_BACKEND_PORT=8301
CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`) pointed at the scoped backend. Both
confirmed healthy (`GET /` → 200, `GET /desk` → 200, `Top-up Runs` + `desk-topup-runs-*` testids
present in the server-rendered HTML — the pre-hydration loading skeleton, since curl doesn't
execute the client fetch; expected, not a defect, matching iteration 10's own identical note).

### 5. Regression replay — J-01 through J-08 against the scoped rig (TC-7)

`python3 incredible_auto_dev/scripts/automation/lib/demo_runner.py --mode verify --scripts-dir
runs/goal-session-desk/journey-scripts --journeys J-01,J-02,J-03,J-04,J-05,J-07,J-08 --base-url
http://localhost:3301 ...` (J-06 excluded — no browser surface, re-confirmed separately via
`test_mcp_server.py`, see §6). Report:
[`reports/phase-goal-desk-iter-12-smoke-replay-results.md`](../../reports/phase-goal-desk-iter-12-smoke-replay-results.md).

**Result: 7/7 PASS, 0 failed, at `--timeout-ms 30000`.** First pass at the runner's 15000ms default
reported `UT-J-07` FAIL (step 04, "Watch" click → expect "Buyer Control" timed out with the tape
state still `Unclear`/`"Warming up..."`, `lag 10.5s` visible on the chart) — a warm-up timing flake,
not a regression (zero product diff this iteration; SIM-BUYER classification is unrelated to any
desk/top-up code). A same-journey retry at 30000ms passed immediately, then the full 7-journey set
was re-run together at 30000ms end to end with 0 failed — that clean run is the reported verdict.
Disclosed in full, with the transient failure's own screenshot state, inside the report itself
(§"Note — UT-J-07 transient timing flake").

None of J-01–J-08's own golden steps click a Run Screen/Top-up/Compute control (verified by reading
every script before replaying) — J-05/J-07 click navigation/watch/load controls that are existing
KEPT-surface behavior, so replaying them against the scoped rig carries no anti-goal risk in either
direction.

### 6. Full backend suite + fingerprint + MCP contract (TC-8, TC-9)

`cd apps/backend && .venv/bin/python -m pytest tests/ -v` (a fresh shell, zero `TAPEOLOGY_*` env
vars leaked in — confirmed explicitly before running):

```
1369 passed, 8 skipped, 2 warnings in 131.53s (0:02:11)
```

Meets the floor exactly (no product/test files changed, so no growth expected). **Environment note
worth recording for future dispatches:** this pytest/plugin setup (pytest 9.1.1) does not print its
final summary line under plain `-q` mode in this environment — only `-v` reliably showed it
(`collected 1377 items` ... `1369 passed, 8 skipped`). A dot-counting workaround on the `-q` log is
unreliable (letters inside test file names like `tests/...` false-match a naive `[.sFxXE]` grep) —
use `-v` and read the literal summary line, not a character count, if this environment quirk recurs.

`Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged). `git diff --stat` empty on every
named product file (see "Verification" below).

`tests/test_mcp_server.py` re-run in isolation: **35 passed**, including
`assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 17` — the 17-tool contract holds
unmodified (TC-8, closes J-06 without a browser pass).

### 7. Ambient store — zero write, proven byte-for-byte (TC-6)

Re-captured `apps/backend/.data/`'s file listing + SHA-256 checksums (plus
`tapeology_journal.db`) after all work completed and diffed against the pre-work baseline:

```
LISTING: IDENTICAL (zero new/deleted files)
CHECKSUMS: IDENTICAL (zero modified file) -- including tapeology_journal.db
```

`apps/backend/.data/topup_runs/` still does not exist in the ambient tree. Nothing this iteration
touched the ambient store at any point.

## Live scoped processes left running for the browser-qa-agent / demo-narrator

| Process | PID | Port | Command |
|---|---|---|---|
| Backend (uvicorn) | **1180202** | 8301 | `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/desk-iter12-scoped-qa" 8301` |
| Frontend (next dev) | 1125327 (npm wrapper) / 1125351 (node) | 3301 | `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh` |

Both confirmed healthy in a final check (`GET :8301/health` → 200, `GET :3301/desk` → 200) with the
3 checkpoint runs still correctly persisted and readable from disk.

**Fallback restart recipe**, if either process is gone by the time you need it (data is all on disk
— a restart loses nothing):

```bash
cd /home/dennis-chan/Git/tapeology
SCOPED_ROOT="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/desk-iter12-scoped-qa"
nohup bash apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301 > /tmp/backend.log 2>&1 &
nohup env CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh > /tmp/frontend.log 2>&1 &
```
(The script reuses the existing `.data/` copy at that root — it does NOT re-copy or lose the 3
checkpoint runs.)

**CRITICAL — do not click "Top-up" (or "Run Screen") on this scoped instance.** The Top-up Runs
demo depends on checkpoint 3 (`topup-2026-07-28-6b40a8029a75`, the induced-failure run) being the
*latest* recorded run — the `/desk` page's detail panel only shows the LATEST run's per-outcome
breakdown and failed-pair detail. A real click would start a 4th, uncontrolled top-up walk (against
the REAL keyless Yahoo adapter this time — no override on the live server) that would supersede
checkpoint 3 as "latest" and bury the failed-pair evidence this dispatch spent effort producing.
This scoped instance is for **reading** (GETs, page loads, screenshots) only — the same discipline
iteration 10's handoff established for its own scoped rig.

## An operational finding worth recording (non-blocking, no product-code implication)

The FIRST scoped backend instance (PID 1122385, launched in §2 above) accumulated sustained ~95–100%
CPU over the ~20 minutes I used it for the regression replay, and did not respond to `SIGTERM`
(required `SIGKILL`). Root-caused empirically, not left as a mystery: a FRESH restart of the same
rig (§ new PID 1180202) idled at ~2% CPU decaying to ~1% with zero requests sent, ruling out the
server's own startup warm-task (`_warm_symbol_universe_bg` → `AlpacaAdapter.warm_symbol_universe()`,
confirmed a one-shot, exception-suppressed, no-op-without-credentials call — not a loop) as the
cause. The most likely explanation: `demo_runner.py --mode verify` was invoked **three times**
against the SAME live server while diagnosing the J-07 timing flake (§5), and each run's J-07 step
clicks "Watch" on `SIM-BUYER`, starting a continuous simulated tick feeder; `DELETE
/watch/SIM-BUYER` (which I called once, successfully) only reaches the LATEST engine instance
tracked in the server's registry — if an earlier invocation's feeder task was left running
independent of that registry entry (e.g. because Playwright closed its page/WS connection abruptly
between runs rather than clicking "Stop"), it would keep generating ticks, un-reachable via the
normal stop path, indefinitely. **Not a regression** (zero product code touched this iteration) and
**not ambient-store-related** (confined to the scoped backend process only), but worth a note for
whoever next drives `demo_runner.py --mode verify` repeatedly against one long-lived server for a
journey that starts a continuous feed: expect to restart the server if you do this more than once,
or add an explicit `DELETE /watch/<ticker>` after every such replay, not just the last one.

## Files Changed

- `reports/phase-goal-desk-iter-12-smoke-replay-results.md` -- regression replay report (7/7 PASS),
  with the scoped-root disclosure and the J-07 timing-flake note.
- `reports/qa/goal-desk-iter-12-evidence/J-01-verify.png` through `J-08-verify.png` (7 screenshots)
  -- deterministic-replay evidence, scoped rig.
- `docs/handoffs/goal-desk-iter-12-dev.md` -- this handoff.

**Not touched** (verified via `git diff --stat`, empty): `desk_topup_log.py`,
`desk_topup_compute.py`, `desk_routes.py`, `desk_screen.py`, `desk_coverage.py`, `tradability.py`,
`levels.py`, `bars.py`, `apps/frontend/app/desk/page.tsx`, `lib/types.ts`, `lib/api.ts`,
`StructureChart.tsx`, `PriceChart.tsx`, `config.py`, `meta.py`, `app/mcp/__init__.py` — the complete
OUT OF SCOPE list, all sixteen files, zero diff.

**Not part of the repo** (throwaway ops tooling, lives only in the pipeline scratchpad, never
committed): `/home/dennis-chan/.cache/iad/iad.goal-desk-iter-12.154299/record_checkpoints.py`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1369 passed, 8 skipped, 0 failed** (meets the required floor exactly; see §6 for the `-v`
vs `-q` environment note).

Also run individually: `tests/test_mcp_server.py` (35/35, 17-tool contract confirmed).

Regression replay (`demo_runner.py --mode verify`, scoped rig): **7/7 PASS** (J-01–J-05, J-07, J-08)
at `--timeout-ms 30000` — see §5 for the one disclosed transient retry.

Fingerprint: `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).

## Pre-handoff verification

- **Service startup works:** scoped backend + frontend both confirmed starting cleanly on `:8301`/
  `:3301` with no port conflicts (nothing was listening on either port before either start). The
  backend was restarted once mid-dispatch (see the CPU finding above) — confirmed clean stop
  (eventually, via SIGKILL after SIGTERM did not respond) and clean fresh start, with the 3
  checkpoint records still correctly readable afterward (file-based store, unaffected by a process
  restart). Per this iteration's own established precedent (iteration 10's dev handoff), these
  processes are **deliberately left running** for the browser-qa-agent/demo-narrator stages — see
  the table and restart recipe above. No ambient-facing server was started or touched.
- **External integrations:** none — this iteration made zero live vendor calls anywhere (checkpoint
  3's failure and its 403 "fetched" pairs both came from an in-process fake adapter, never the
  network).
- **Native dependencies:** none added. (`demo_runner.py --mode verify` needed system `python3` with
  a user-level Playwright install already present in this environment — NOT `apps/backend/.venv`,
  which has no Playwright; noted here only because it tripped the first invocation attempt with a
  clear, self-explanatory error, not because anything needed installing.)

## Known Issues

- The `[NEW]`-flagged demo-narrator walkthrough and the standalone browser-qa-agent screenshots for
  J-09's two states (empty + populated-with-a-failed-pair) are **not part of this dev dispatch** —
  per this repo's established pipeline division of labor (confirmed again this iteration: iteration
  11's own dev handoff logged the identical division), those are the browser-qa-agent's and
  demo-narrator's own steps. What this dispatch guarantees is that the environment those stages need
  is live, correct, and populated right now — see the "Live scoped processes" section above.
- The J-07 timing flake (§5) is disclosed, not silently retried away — the FIRST attempt's own FAIL
  is on record inside the replay report's own text, not hidden.
- Checkpoint 3's real bar-store side effect (§3) is disclosed for transparency even though it is
  confirmed harmless to every existing regression check.
- The operational CPU finding above is disclosed for whoever runs `demo_runner.py --mode verify`
  next against a long-lived scoped server — not a product defect, not this iteration's job to fix
  (would require touching `main.py`'s `manager.stop()`/engine-registry code, explicitly out of
  scope).
- I did not attempt to trigger a top-up or screen run against the ambient store at any point (out of
  scope, and the anti-goal this whole iteration is built around avoiding).
