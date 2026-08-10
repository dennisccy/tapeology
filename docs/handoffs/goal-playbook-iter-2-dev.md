# goal-playbook-iter-2 Dev Handoff

**Phase:** goal-playbook-iter-2
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

Target journey **J-02** ("Every signal measured — the rail's own conventions, anchored at the
trigger bar") plus the three carried items the evaluator folded into this same cycle: the J-10
golden-replay evidence gap, the three audit test gaps (T1×2, T3), and the two spec-doc catch-ups
(B3, B4).

- **`app/research/desk_playbook.py`** — `compute_playbook` now measures every detected signal in
  the SAME walk:
  - `_measurement_anchor(session_5m, session_1m, trigger_idx_5m, trigger_price)` — spec §0's
    5m→1m mapping (first 1m bar of the trigger's own `[epoch, epoch+300)` window whose
    `[low, high]` contains `T`, falling back to the window's first 1m bar); a window with ZERO 1m
    bars degrades that ONE signal to the 5m basis rather than borrowing a bar from a neighboring
    window (TC-19) — `_measure_from`'s own per-horizon `reason` field discloses the coarser basis
    for free (no new served field needed).
  - `_measure_signal` calls `_measure_from` (imported from `desk_forward.py`, zero diff to that
    file) with the signal's own already-detected `entry`/`entry_kind`/`trigger_price` reused
    verbatim, `sign = +1`/`-1` from `side`, and attaches the result as `signal["forward"]`.
  - `_invalidation_breached` computes the per-horizon breach block OUTSIDE `_measure_from` (its
    served shape never changes): ONE session-wide `first_breach_minutes` fact, with each horizon
    key `True` when that fact falls at-or-before that horizon's OWN already-measured
    `effective_minutes` (reusing the rail's truncation-honest window, never a second walk).
  - Baseline anchors: one seeded draw per in-cap firing symbol
    (`f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}"`, imported
    `_draw_anchor_indices`), pooled across ALL symbols sharing a `(setup_id, side)` key into the
    record's `baseline_anchors`/`summary`. The cross-symbol pool is capped at the rail's OWN
    `DESK_FORWARD_MAX_TOUCHES_PER_ROW` (imported, not a new invented threshold — see Known Issues)
    with the excess disclosed via a new `signals_beyond_cap` record field.
  - `summary` built with the rail's own `_avg_cell`/`_collect_measures` (imported, not copied).
  - `compute_playbook` gained `progress`/`should_abort` params (mirrors `compute_forward`'s
    contract), checked/called once per member regardless of outcome.
  - `playbook_parameters()` gained `rail_max_touches_per_row` (the new dependency, echoed per the
    established rail-constant-echo pattern) — this is also what re-keys a J-01-era (unmeasured)
    record: the parameters blob's shape genuinely changed, so a fresh J-02 compute over identical
    bar content mints a NEW version rather than matching the old, unmeasured one.
  - `PLAYBOOK_REGISTER` rewritten to describe the measurement now made (still passes copy
    discipline); `payload_version` 1 → 2 (describes the shape; the signature move is what actually
    re-keys).
  - `PlaybookStore.record`/`_registered` extended with `baseline_anchors`/`summary`/
    `signals_beyond_cap`, defaulting to empty for J-01-era records read back (TC-11).
- **`app/research/desk_playbook_compute.py`** (new) — `DeskPlaybookComputeManager` (single-flight,
  process-wide, mirrors `DeskForwardComputeManager`) + `run_playbook_and_record` (resolves the
  2-pin key before any walk, reuses honestly on a match) + a CLI (`--session-date`, required). Two
  deliberate divergences from the forward precedent, both explained in the module docstring: (1)
  session-refusal is checked BOTH at the HTTP route (before a job/ledger row exists) AND inside
  `run_playbook_and_record` itself (for the CLI path and the race) — the route's pre-check is why a
  bad date via the trigger route writes no ledger row; (2) a completed cancel reverts the snapshot
  to the SAME idle shape it started from (`status` enum has no distinct "cancelled" terminal value)
  and is never logged — a cancelled playbook run leaves no trace anywhere, not just off the durable
  store.
- **`app/research/desk_playbook_log.py`** (new) — `PlaybookRunStore`, terminal-state-only
  (`"recorded"|"reused"|"refused_non_session"|"failed"` — no `"cancelled"` value exists on this
  store at all, matching the compute manager's own choice), mirrors `desk_forward_log.py`'s
  checksum/append-only discipline exactly.
- **`desk_routes.py`**: `POST/GET/POST-cancel /research/desk/playbook/compute` +
  `GET /research/desk/playbook/runs`, wired the same way the forward-returns trio already is. The
  trigger route pre-checks `refuse_if_not_a_session` before calling `manager.trigger` (the
  `trigger_desk_screen_compute` precedent). This is the ONLY other file touched — one import block,
  one manager singleton, one dependency function, four routes; the existing `GET /playbook` route
  is untouched.
- **`docs/playbook-detector-spec.md`** — two documentation-only edits (B3, B4): `PLAYBOOK_OR_MIN_1M_BARS`
  now a row in §1's table; §3.1's Disclosures prose states the P4-on-`constructive` rule
  mechanically. Zero code/value change — verified by a source-diff assertion (TC-20).

## Files Changed

- `apps/backend/app/research/desk_playbook.py` — measurement pass, parameters/register updates,
  store extension (+257/-13 lines).
- `apps/backend/app/research/desk_playbook_compute.py` — new; manager + `run_playbook_and_record` + CLI.
- `apps/backend/app/research/desk_playbook_log.py` — new; the run ledger.
- `apps/backend/app/research/desk_routes.py` — added the playbook compute/runs routes (+135 lines);
  no existing route touched.
- `apps/backend/tests/test_desk_playbook.py` — +19 tests (32 total): convention identity,
  truncation, gap_open reuse, invalidation breach (boundary/anchor-bar/never/short-mirror),
  baseline determinism + cross-symbol independence, the beyond-cap pool, the embedded rail-seed
  counter-test, the J-01-era verbatim-serve test, the T1 compute_playbook-level fixtures (5m-basis
  degrade, ambiguous outside bar), the TC-19 gapped-window degrade + its genuine-1m-match sibling,
  progress/should_abort wiring, and the B3/B4 doc-consistency test.
- `apps/backend/tests/test_desk_playbook_detect.py` — +2 tests (10 total): the T3 populated-SPY
  fixtures (a supportive `market.direction`, and `relative_strength_strong: true`).
- `apps/backend/tests/test_desk_playbook_compute.py` — new; 13 tests: reuse/cancel/session-refusal/
  ledger-write behavior of `run_playbook_and_record`, manager single-flight + cancel-reverts-to-idle,
  the four compute/runs routes, the CLI.
- `apps/backend/tests/test_desk_playbook_log.py` — new; 22 tests, mirrors
  `test_desk_forward_log.py`'s store-discipline coverage (including the deliberate
  "cancelled" rejection test).
- `reports/phase-goal-playbook-iter-2-regression-replay-results.md` + `reports/qa/goal-playbook-iter-2-evidence/J-10-verify.png` — the explicit J-10 golden-script replay (see below).

Nothing else touched — `git status --porcelain` is empty on `desk_forward.py`, `desk_screen.py`,
`desk_screen_diff.py`, `desk_screen_pins.py`, `setups.py`, `bars.py`, `levels.py`, `app/config.py`,
`app/mcp/__init__.py`, and everything under `apps/frontend/` (verified directly before writing this
handoff, not just inferred).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **2025 passed, 8 skipped, 0 failed** (era-open floor after iter-1's audit fix was 1969
pass/8 skip; this iteration's 56 new tests account for the entire increase — 1969 + 56 = 2025
exactly).

Playbook suite alone (`test_desk_playbook.py` 32, `test_desk_playbook_detect.py` 10,
`test_desk_playbook_features.py` 22, `test_desk_playbook_compute.py` 13,
`test_desk_playbook_log.py` 22 = **99 passed**).

Also verified directly:
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged; zero new `Config` fields — I
  never touched `app/config.py`).
- MCP `_STATIC_PATHS` still has 12 entries (zero diff to `app/mcp/__init__.py`) — 18 tools total,
  unchanged.
- Real HTTP smoke test against a scratch `uvicorn` (real socket, not `TestClient`): `GET
  /research/desk/playbook` still returns the honest-empty payload against the REAL (non-fixture)
  desk universe/bar stores; the new `GET/POST /playbook/compute` and `GET /playbook/runs` routes
  respond correctly (idle snapshot, honest-empty runs list).

**TC-21 (the J-10 golden-script replay) was explicitly executed this iteration** — the exact gap
iter-1's audit (T2) and this iteration's own TESTING REQUIREMENTS demanded, rather than deferred to
"the browser-qa-agent" again.

> **This section was rewritten in fix mode (see Fix Notes) to describe the FINAL, authoritative
> replay pass — the one whose report + screenshot are the artifacts actually on disk.** An earlier
> replay attempt in this iteration was superseded by a later run that FAILed on step 5; that FAIL
> was root-caused to dead backend infrastructure (not a product regression) and the replay was then
> re-run clean four times. Full history in Fix Notes.

Authoritative pass (2026-08-10 18:48:05 UTC-local, artifact mtimes):

1. Killed a stuck orphan backend, then `rm -rf apps/frontend/.next` (T-9 clean rebuild).
2. Started a real backend (`scripts/start-backend.sh` → port **8301**) and frontend
   (`scripts/start-frontend.sh` → port **3301**) — the project's own deterministic port offset
   (`3000/8000 + 301`), which is what the pipeline's `replay-lane.sh` derives — against the REAL
   recorded desk universe/bar stores (not a fixture-scoped env). Backend `/health` → 200; cold
   `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T23:59:59Z` → 200 in 6.98 s containing
   `300.11`, warm 1.34 s.
3. Ran `python3 incredible_auto_dev/scripts/automation/lib/demo_runner.py --mode verify
   --scripts-dir runs/goal-session-playbook/journey-scripts --journeys J-10 --base-url
   http://localhost:3301 --results reports/phase-goal-playbook-iter-2-regression-replay-results.md
   --evidence-dir reports/qa/goal-playbook-iter-2-evidence --phase-id goal-playbook-iter-2 ...` —
   the SAME deterministic Playwright replay the pipeline's own `replay-lane.sh` invokes, with the
   same `--results`/`--evidence-dir` paths the lane uses.
4. **Result: PASS, 1/1 journeys, exit code 0.** All six steps held (cockpit "Try: SIM-BUYER" +
   Watch → "Watching"; `/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z` Load → "300.11"; `/desk`
   → "Forward Returns"). Evidence screenshot at
   `reports/qa/goal-playbook-iter-2-evidence/J-10-verify.png`; report at
   `reports/phase-goal-playbook-iter-2-regression-replay-results.md`. **Both files carry the
   identical mtime `18:48:05` — they are the same run**, so the artifact matches its own claim.
5. Reproducibility: the replay was run **four consecutive times** against the same live services
   (one into the authoritative path, two into scratch paths, one final authoritative re-run) —
   `rc=0` / `PASS` every time. `runs/goal-session-playbook/journey-scripts/J-10.json` was **not
   edited** (`git status --porcelain` on that directory is empty): the sentinel was made to pass by
   fixing the environment, never by relaxing an assertion.
6. Killed both dev servers afterward — see Fix Notes for the confirmed-clean check.

J-10 is honestly `passing` for this iteration, not `unknown-by-replay`.

## Known Issues

- **Two interpretive design calls, both reusing EXISTING constants rather than inventing new
  ones (T-1 compliance), flagged for the reviewer/auditor's own judgment:**
  1. The cross-symbol pooling cap on `baseline_anchors`/`summary` (TC-9's "per-(setup,side) cap")
     reuses the rail's own `DESK_FORWARD_MAX_TOUCHES_PER_ROW` (imported, echoed in
     `playbook_parameters()` as `rail_max_touches_per_row`) rather than a new playbook-specific
     constant — no such cap is named anywhere in `docs/playbook-detector-spec.md`'s own §1 table,
     and the OR-break family structurally fires at most one signal per symbol-session, so this cap
     only becomes reachable with 9+ DIFFERENT symbols firing the same `(setup_id, side)` in one
     session (tested directly, TC-9).
  2. `signals_beyond_cap` (a new top-level record field disclosing the excess) is not named
     verbatim in the iter spec's Data-contract shape section, which enumerates `baseline_anchors`/
     `summary` but not a beyond-cap field explicitly — TC-9 requires SOME explicit disclosure
     ("the record discloses the beyond-cap count"), so I added the minimal field this implies
     rather than leaving it only inferable by comparing pool sizes against the full `signals` list.
- **The compute-progress snapshot's exact field names/shape** (`{status, session_date,
  signals_done, signals_total, error}`, `status` idle/running/cancelling/done/error) are taken
  literally from the iter spec's Data-contract section, which states it "mirrors
  `DeskForwardComputeManager`'s snapshot shape" in general SPIRIT (single-flight, snapshot-pollable,
  cancel) while declaring a materially LEANER, differently-named shape than forward's own (no `id`/
  `reused`/nested `progress`). Implemented literally as declared; flagged since it is a real,
  visible divergence from the sibling manager's shape.
- **No live/manual verification of a real (non-fixture) compute run over the operator's actual
  recorded universe.** Every test in this iteration is fixture-scoped and keyless, per J-02's own
  acceptance tag `(Keyless; automated.)` and the OUT OF SCOPE line naming this explicitly. I did
  confirm the new routes respond correctly (idle/honest-empty) against the REAL backend during the
  J-10 replay session, but never triggered `POST /research/desk/playbook/compute` against it.
- **NEW (found during the fix pass, deliberately NOT fixed — out of this iteration's scope):** the
  replay lane is fragile against a half-dead backend. A uvicorn that has been SIGTERMed but has not
  finished shutting down keeps its PID while its listening socket is already closed, so every
  service *probe by process* says "backend running" while every *request* gets connection-refused —
  which is exactly how this iteration's replay recorded a product-looking FAIL (`step 05 expected
  "300.11" did not appear`) with a perfectly healthy product behind it. A liveness probe that curls
  `/health` rather than trusting a PID would have turned that into an honest infra-skip instead of a
  false regression. Filed here for the reviewer/auditor to triage; it is framework/infra behavior,
  not J-02 code, and touching it uninvited would be scope creep.
- `.claude/project-template.md` is still the unfilled generic template (a pre-existing condition
  from before this iteration, already flagged in iter-1's handoff). Test/start commands above came
  from `README.md`, matching what iter-1 used.

## Fix Notes (fix mode — review FAIL, 2026-08-10)

Input: `reports/reviews/goal-playbook-iter-2-review.md` — **one CRITICAL issue**, evidence integrity,
not implementation. Fixed exactly that; **zero product-code changes** in this pass.

### The issue as filed

The handoff narrated a PASS 1/1 J-10 golden replay while
`reports/phase-goal-playbook-iter-2-regression-replay-results.md` on disk said
`**Browser QA Verdict:** FAIL`, `0/1 journeys passed`, `step 05 expected "300.11" did not appear`,
dated ~6.5 h AFTER the handoff. TC-21 demands an explicitly-executed replay with zero new failures,
so a stale PASS claim standing beside a later, uncontradicted FAIL artifact is a DEFINITION OF DONE
violation regardless of which one was "right".

### What I found on disk when fix mode started

The FAIL report was **already gone** — `replay_lane_partition_and_verify`
(`incredible_auto_dev/scripts/automation/lib/replay-lane.sh:243`) does
`rm -f "$REGRESSION_RESULTS"` as stale-artifact hygiene at the start of every lane run, so a third
lane attempt (`runs/goal-session-playbook/iter-2/.bqa-replay-pid` = 338951) deleted it and then
died without writing a replacement. Net state entering this fix: **no TC-21 artifact at all**, plus
an orphaned `J-10-verify.png`. That is strictly worse than the contradiction the reviewer filed, so
producing one truthful current artifact was the only correct move.

### Root cause of the FAIL (it was infrastructure, not the product)

A stuck orphan backend, started at the same minute (18:30) as the failing replay:

- `ps -ef` → pid **339014**, `.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8301`, started 18:30,
  **99 % CPU** sustained (13 min 50 s CPU over ~14 min wall).
- `/proc/339014/status` → `VmRSS: 5352480 kB` (5.3 GB), `Threads: 25`.
- `ss -ltnp` → **nothing listening on 8301** (nor 3301); the only LISTEN rows were 631/53/42487.
- `curl --max-time 10 http://localhost:8301/health` → **HTTP `000`** (connection refused).

So at replay time the frontend's `/structure` Load had no backend to answer it: step 5 could not
have produced `300.11` within its 15 000 ms budget under any product behaviour. This matches the
reviewer's own independent finding that the backend data still contains `300.11` — the data never
drifted. Not a regression in the kept product, and consistent with the earlier attempt in this
iteration having genuinely passed against healthy services.

The shape of the failure — process alive, listening socket gone, CPU burning — is what a uvicorn
looks like **after a SIGTERM it never finished acting on**: graceful shutdown closes the listener
first, so the port stops answering while the process lives on. I could not reproduce the hang on
demand, so I stop short of naming the exact non-cooperative task; what is established is that no
backend was reachable, which is sufficient to explain step 5.

I did chase and **rule out** two tempting explanations, so nobody re-chases them:

| Hypothesis | Measurement on a fresh backend | Verdict |
|---|---|---|
| Idle background spin at startup | 0 CPU ticks over 20 s with zero traffic | ruled out |
| The J-10 `SIM-BUYER` watch (the golden starts a sim tape and never tears it down) leaves a feeder burning a core | 19 ticks over 20 s with the watch active (~1 % of one core) | ruled out |
| Replay page loads leave sustained load | 35 ticks over 30 s after `tradability` + all four `/research/desk/*` endpoints returned (~1 %) | ruled out |

The one real cost those requests do leave is memory, not CPU: RSS went 162 MB → **2.46 GB** after a
single cold `tradability` compute, which makes the dead process's 5.3 GB plausible as "a backend
that had served several of these", nothing more.

### What I did

1. Killed the stuck orphan (`kill -9 339014`) and `rm -rf apps/frontend/.next`.
2. Started clean services on the project's own deterministic ports: backend **8301**
   (`/health` → 200 in ~15 s), frontend **3301** (`✓ Ready in 1711ms`).
3. Proved the data path independently before touching the browser:
   `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T23:59:59Z` → 200, **cold 6.98 s / warm
   1.34 s**, body contains `300.11` (so 15 000 ms is ~2× margin on the cold path, and the golden's
   timeout did not need touching).
4. Re-ran the deterministic replay **4×**, all `rc=0` / `PASS` — the last one writing the
   authoritative pair. Report and screenshot now share mtime **18:48:05**: one run, one claim, no
   contradiction.
5. Killed both dev servers; verified nothing listens on 3301/8301 and no stray `uvicorn`/`next`
   processes remain.

### What I deliberately did NOT do

- **Did not touch `runs/goal-session-playbook/journey-scripts/J-10.json`** — not its assertions, not
  its `default_timeout_ms`. `git status --porcelain` on that directory is empty. The reviewer's fix
  text allowed adjusting the golden's wait condition, but the failure was dead infrastructure, so
  relaxing the sentinel would have hidden the real cause and weakened J-10's whole purpose.
- **Did not hand-edit the replay report.** It is byte-as-written by `demo_runner.py`, which is what
  makes it trustworthy; the supersession history lives here in the handoff instead.
- **Did not touch any product code, test, or spec file** — fix mode, one listed issue.
- Found no new problems to record beyond the port discrepancy noted below.

### Honest note on the earlier attempt

The original TC-21 narrative cited ports 8000/3000. This project's deterministic offset is **+301**,
so the pipeline lane and both `scripts/start-*.sh` resolve to 8301/3301. I cannot now reconstruct
which services that first run actually reached, so I am not defending its PASS — I am replacing it.
Everything claimed in the rewritten TC-21 section above comes from the run whose artifacts are on
disk right now.

### Verification re-run after the fix

- Full backend suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -q -p no:warnings` →
  exit code **0**, **2025 passed / 8 skipped / 0 failed** — unchanged from the pre-fix run and from
  the reviewer's own independent reproduction, as expected (no source file was modified in this
  pass). Counted from the progress census (`2025` × `.`, `8` × `s`, zero `F`/`E`): this project's
  pytest run does not emit a terminal summary line, so the census is the honest count.
- `Config().config_fingerprint()` → `08e471b10130e1e2` (pin held). `app.mcp._STATIC_PATHS` → 12
  entries (MCP still 18 tools, zero diff).
- `git diff` still empty for `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`,
  `levels.py`, `app/config.py`, `app/mcp/__init__.py`, `apps/frontend/`, and the journey-scripts dir.
- Services stopped: `ps -ef` shows no `uvicorn`/`next dev`/`next-server`, and nothing listens on
  3301/8301 (nor the 3399/8399 scratch pair used for the CPU measurements above).
