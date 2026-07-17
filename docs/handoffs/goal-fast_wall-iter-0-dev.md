# goal-fast_wall-iter-0 Dev Handoff

**Phase:** goal-fast_wall-iter-0
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is the "Fast Wall" interlude's **verify-only baseline** (Mode: baseline,
Depth: lean). The spec's BACKGROUND section states the developer step is an explicit no-op; the
entire scope was executing the spec's verification checklist against the current codebase and a
live backend/frontend, and recording the evidence below so the goal-evaluator can mark
`already_passing` vs. to-build for each of J-01–J-07.

```
$ git status --short -- apps/
(empty)
$ git diff --stat -- apps/
(empty)
$ git status --short
?? docs/phases/goal-fast_wall-iter-0.md
?? runs/goal-session-fast_wall/
```

Both untracked entries are pipeline artifacts (the iter spec itself and the goal-mode session state
directory), not product source. No file under `apps/` was created, modified, or deleted this
iteration.

## Baseline test counts (the J-07 sentinel anchor)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

- **1392 passed, 7 skipped, 0 failed, 0 errors in 435.16s (7m15.160s). Exit 0.** (1399 collected.)
- This pytest install does not print its usual final summary line on the full 1399-test run in this
  environment (a known, previously-documented quirk — see `docs/handoffs/goal-tradable_wall-iter-8-dev.md`)
  — exit code 0 corroborates zero failures. The count above is **cross-validated two independent
  ways**, not eyeballed:
  1. Manual tally of the dot/`s`/`F`/`E` progress characters captured from the run (1392 `.` + 7 `s`,
     zero `F`/`E` — 1399 total).
  2. An independent `--collect-only -q` pass, summed across this project's per-file collection report
     (`grep -oE '^tests/.*: ([0-9]+)$' | awk -F': ' '{s+=$2} END {print s}'`) → **1399**, an exact
     match to the manual tally.
- Skip breakdown (confirmed via a dedicated isolated run of the three skip-gated files —
  `.venv/bin/python -m pytest tests/test_live_integration.py tests/test_yahoo_live_integration.py
  tests/test_event_recording_integration.py -v` → **"7 skipped, 1 warning in 0.22s"**, an exact match
  to the full-run tally):
  - `tests/test_live_integration.py` (1) — gated on `TAPEOLOGY_LIVE_INTEGRATION=1` (then Alpaca
    credentials, then market hours).
  - `tests/test_yahoo_live_integration.py` (5) — gated on `TAPEOLOGY_LIVE_INTEGRATION=1` (the real
    Yahoo fetch check).
  - `tests/test_event_recording_integration.py` (1) — gated on "Alpaca credentials not configured in
    the environment".
  - All three are explicit two-stage opt-in gates, not credentials-missing failures — expected and
    honest for an autonomous, keyless run. **This is the Fast Wall opening baseline: 1392 passing /
    1399 collected / 7 skipped / 0 failed / 0 errors.**

Equivalence tests (byte-identical-output guard), confirmed via an isolated targeted run (fast, 1.08s,
unambiguous — avoids relying on the full run's summary-line quirk):

```
$ .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v
tests/test_observer_equivalence.py .......                               [ 31%]
tests/test_profile_equivalence.py ...............                        [100%]
============================== 22 passed in 1.08s ==============================
```

**22/22 passed, 0 skipped.** Both equivalence suites are green; the frozen `default` behavior is
intact.

`config_fingerprint` (live-computed, not just grepped):

```
cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"
-> 4d665603569b9dbf
```

Matches the goal.md-pinned value **exactly**. (Backend venv: Python 3.14.4, pytest 9.1.1.)

## J-01 — Stop the bleeding (expected FAIL) — CONFIRMED: the defect is live today

Read the actual call chain, not just grepped for absence — three files, one continuous path from the
GET handler down to the synchronous compute:

1. `apps/backend/app/research/routes.py:2093-2117` (`get_edge_report`) — the route's entire body:
   ```python
   try:
       return run_strategy_comparison_report(
           registry.store, dataset_store, bar_store, registry.config, cache=cache
       )
   except EdgeReportError as exc:
       raise HTTPException(status_code=500, detail=f"edge report could not complete: {exc}")
   ```
   No cache-lookup-first branch, no not-computed short-circuit — every GET calls the computer.
2. `apps/backend/app/research/edge_report.py:427-456` (`run_strategy_comparison_report`) — when a
   cache is supplied (the route's DI-wired path), it calls `cache.get_or_compute(dataset_store,
   config, compute)` where `compute` closes over `_compute_strategy_comparison_report`.
3. `apps/backend/app/research/edge_report_cache.py:228-266` (`get_or_compute`, the **only** cache
   method on `EdgeReportCache` — confirmed via `grep -n "def get_or_compute\|def lookup\|def
   compute_and_publish" edge_report_cache.py` → exactly one match, `get_or_compute`) — on a durable
   miss, line 263 is `result = compute_fn()`: called **directly and synchronously inside the current
   call stack**, i.e., inside the GET request. This is J-01's target defect, live and unmodified.

Live confirmation the real corpus's cache is genuinely cold (not just structurally missing a
lookup path): `.data/edge_report_cache.db` is **12,288 bytes**, mtime **2026-07-15 20:44** — small,
consistent with holding only keyless-fixture rows from the test suite, not a completed real-corpus
report. I did **not** call `GET /research/edge-report` against the real corpus live (see SAFETY NOTE
below) — this file's size/mtime were checked again after every other live probe this iteration and
never changed, confirming no compute was ever triggered by my own actions.

### SAFETY NOTE — do not casually hit `/research/edge-report` against the real corpus

`.data/datasets` (882MB, matches goal.md's cited figure exactly) is the backend's **default** dataset
directory — `scripts/dev.sh` / `start-backend.sh` boot against it with no override needed. Given the
cache is confirmed cold (above), a live `GET /research/edge-report` call **or a browser visit to
`/structure` with its Edge Report section rendering** against this default-booted backend will
synchronously enter `_compute_strategy_comparison_report` inside that one request/page-load, exactly
as goal.md's Vision section documents ("the backend worker pinned at 98% CPU for hours"). I
deliberately avoided this (relying on the code citation above, which the spec's own NOTES
explicitly permits: "a compute-spy is not required at baseline... a direct code citation... is
sufficient evidence"). **Flagging for whoever runs the browser-qa step next:** the spec's TESTING
REQUIREMENTS do ask for a live `/structure` Edge Report render check, and the spec's BACKGROUND
anticipates "spinner, error, hang" as valid observed states — so triggering this is expected/
intentional for this baseline. But the **backend process itself will keep computing in the
background** after any bounded UI-wait timeout returns (Python's GIL-bound synchronous work isn't
cancelled by a client giving up), degrading every other endpoint on that same process for as long as
the sweep runs. If this gets triggered, the resulting backend process should be identified and killed
(`fuser -k -9 <port>/tcp`, not just a parent-PID kill — see Service startup verification below) before
any further journey checks lean on that same backend instance, so a false regression isn't recorded
against an unrelated endpoint that's merely GIL-starved.

## J-02 — The stores stop re-reading (expected FAIL) — CONFIRMED ABSENT; live cost measured

- `grep -n "st_mtime_ns|st_size|_STAT_CACHE|stat_cache" app/research/bars.py app/research/datasets.py`
  → no matches — no stat-keyed cache in either store.
- `ls app/research/ | grep -i index` → only `bar_index.py` (the pre-existing era-5 bar-index
  accelerator — unrelated; `dataset_index.py` does not exist).
- Live probe against the real corpus (backend on scratch port `:8301`):

  ```
  GET /research/datasets -> HTTP 200, 8588 bytes, 29.181288s, 18 datasets registered
  ```

  Close to goal.md's cited 31.4s (same order of magnitude; local machine variance). Confirms
  `DatasetStore.list()` re-reads/re-hashes the full corpus on every call today.

## J-03 — The arm memo (expected FAIL) — CONFIRMED ABSENT

`grep -rn "level_change_points|basis_day_key|_StructureArmMemo" app/research/levels.py
app/research/tradability.py app/research/backtests.py` → no matches anywhere. No memo exists; the
structure-strategy arming path has no per-run cache to test.

## J-04 — The operator-run compute (expected FAIL) — CONFIRMED ABSENT

- `find app/research -iname "edge_report_compute.py"` → no match.
- `grep -n 'compute/cancel\|"/compute"' app/research/routes.py` → no match.
- Live probe: `GET /research/edge-report/compute` → **404**; `POST /research/edge-report/compute` →
  **404** (both safe to call — they hit FastAPI's default 404 for an unregistered subpath, no
  existing logic engaged).
- Frontend: `grep -n "not_computed|Compute edge report|not computed yet"
  apps/frontend/app/structure/page.tsx` → no matches — no button, no not-computed panel.

## J-05 — Resumable and parallel sweep (expected FAIL) — CONFIRMED ABSENT

`grep -rn "EdgeReportBacktestCache|run_pair" app/research/*.py` → no matches. No per-pair durable
cache, no provider seam.

## J-06 — Durable setups scan cache (expected FAIL) — CONFIRMED ABSENT; live cost measured

- `apps/backend/app/research/setups.py` has exactly one cache: the in-process `_SCAN_CACHE` module
  global (era-5B, `_SCAN_CACHE: tuple[tuple, dict] | None = None`) — wiped on every restart.
  `find app/research -iname "setups_scan_cache.py"` → no match.
- Live probe against the real corpus (cold — this backend instance had never called `/research/setups`
  before):

  ```
  GET /research/setups -> HTTP 200, 4,497,772 bytes, 269.820641s (4m29.8s), 801 events
  ```

  A real, measured cold-cache cost — consistent with goal.md's "minutes when cold" citation. This
  confirms `compute_setups` re-scans and re-hashes the full bar corpus on every call today with no
  durable fallback.

## J-07 — The foundation is unchanged (regression sentinel) — CONFIRMED INTACT

- Full suite green (1392/1399 above); equivalence suite green (22/22 above); `config_fingerprint`
  confirmed **live-computed** as `4d665603569b9dbf`, matching the pinned value.
- Champion pointer confirmed untouched: live probe `GET /research/profiles` →
  `"champion":{"strategy_id":"v1","profile":"default"}`, profiles list unchanged (`default` frozen,
  `candidate-faster-warmup` non-default).
- `GET /research/strategies` → exactly **`["v1", "structure_tape", "structure_tape_map"]`** — the
  full era-5B registry, unchanged, full config intact.
- `GET /meta/ui-routes` → exactly the same **6** entries as the blueprint's frozen nav (Cockpit `/`,
  Journal `/journal`, Journal detail `/journal/[id]` non-nav, Studies `/studies`, Performance
  `/performance`, Structure `/structure`) — unchanged, no new entry.
- Live backend (`scripts/dev.sh`, scratch ports 8301/3301): `GET /health` → `{"status":"ok"}`.
- Live frontend SSR probes (curl only — no client JS executes on a plain GET, so this **cannot**
  trigger the edge-report sweep): `GET /` → 200, `GET /journal` → 200, `GET /studies` → 200,
  `GET /performance` → 200, `GET /structure` → 200.
- `/structure`'s raw SSR HTML (25,233 bytes) contains all era-5/5B markers: "Tradable Map", "Case
  Studies", "Edge Report", "Yahoo Finance", `structure-load-button` — all present and intact; contains
  **none** of "not_computed", "Compute edge report", "not computed yet" — confirms the additive UI
  from this interlude does not exist yet without disturbing anything that does.
- `git diff --stat -- apps/` confirmed **empty** — not merely "additive" — this iteration makes no
  backend or frontend edit at all.
- **Not verified by me this iteration** (browser-qa-agent's step per TESTING REQUIREMENTS, not a
  dev-level code/API check): the sim cockpit click-through (`SIM-BUYER` settles `buyer_control`,
  `SIM-SELLER` settles `seller_control`) requires an active WebSocket-driven watch session, which is
  a browser interaction, not a GET probe — recorded as deferred, not as pass or fail.

## Files Changed

- (none — verify-only baseline; zero source modifications under `apps/`)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1392 passed, 7 skipped** (1399 collected), 0 failed, 0 errors, 435.16s, exit 0

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`
Result: **22 passed** in 1.08s (0 skipped) — both engine/profile equivalence guards green.

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `4d665603569b9dbf` — matches the pinned fingerprint exactly.

## Service startup verification

- `bash scripts/dev.sh` (deterministic scratch ports `8301`/`3301` from the script's own
  project-path hash offset) started both services clean: backend `/health` → 200 within 1-2s,
  frontend root → 200 within 1-2s. No `error`/`EADDRINUSE`/`address already in use` in either log,
  on either boot (fresh start and restart both checked).
- Stopped, verified both ports free, **restarted `scripts/dev.sh` on the same ports** — backend and
  frontend both healthy again within seconds, no port-conflict errors in the restart log — then
  stopped again and verified fully clean.
- **Gotcha confirmed (matches the precedent noted in `docs/handoffs/goal-tradable_wall-iter-0-dev.md`
  and `-yahoo_fetch-iter-0-dev.md`):** killing only the top-level `bash scripts/dev.sh` PID and the
  `uvicorn`/`next dev` parent PIDs is **not sufficient** — `uvicorn --reload` spawns a separate
  `multiprocessing.spawn` worker child that actually binds the port, and `next dev` similarly spawns a
  child `next-server` process; a PID-only kill left both orphaned and still listening. Port-based
  kill (`fuser -k -9 <port>/tcp`) reliably reaches the actual bound-socket process regardless of
  process-tree shape and is what actually achieved a clean stop both times. Final state confirmed:
  no tapeology `uvicorn`/`next`/`dev.sh` process remains, ports 8301/3301 fully free.

## No side effects (baseline hygiene)

- Every live probe this iteration was a **read-only GET** (`/health`, `/research/datasets`,
  `/research/setups`, `/research/strategies`, `/research/profiles`, `/meta/ui-routes`,
  `/research/edge-report/compute` GET+POST — both hit FastAPI's default 404 for an unregistered
  route, no application logic engaged — plus frontend page GETs) — no mutating call was made, so no
  journal/dataset/bar-series record was created or mutated.
- `GET /research/edge-report` was deliberately **never called** against the real corpus this
  iteration (see SAFETY NOTE under J-01) — `.data/edge_report_cache.db` confirmed byte-identical
  (12,288 bytes, mtime unchanged at 2026-07-15 20:44) before and after every other probe, proving no
  compute was triggered by my actions.
- No live Alpaca or Yahoo Finance network call was made or attempted.
- The dev-stack smoke test used the real `.data/` corpus (needed for the J-02/J-06 latency probes
  the spec explicitly requests); safe given the read-only-GET constraint above, consistent with
  prior baseline practice.

## Known Issues

- **Environment drift (carried over from every prior era baseline):** the backend venv runs Python
  **3.14.4**; `.claude/project-template.md`'s placeholder text says 3.12. The full suite is green on
  3.14.4 — a documentation/environment drift observation, not a failure. No action taken (out of
  scope for a verify-only iteration).
- **`.claude/project-template.md` is still the generic unfilled vendored template** (confirmed again
  this iteration — same finding as every prior baseline; `.claude` is a symlink into
  `incredible_auto_dev/`, never customized for this project). This developer used goal.md's
  Constraints section, prior dev handoffs (`docs/handoffs/goal-tradable_wall-iter-0-dev.md` and
  `goal-yahoo_fetch-iter-0-dev.md` especially), and direct codebase inspection (`pyproject.toml`,
  `apps/backend/tests/`, `scripts/dev.sh`) as the real stack-configuration source of truth. Not this
  iteration's scope to fix.
- **The J-01 CPU hazard (see SAFETY NOTE above) is a real operational risk for the next browser-qa
  step**, not a code defect to fix this iteration (fixing it *is* J-01's future scope). Flagged here
  so it's on record before a live browser check against the real corpus is attempted.
- **The full-suite pytest run does not print its own final summary line in this environment** (known,
  pre-existing quirk, first documented in `docs/handoffs/goal-tradable_wall-iter-8-dev.md` and
  `goal-yahoo_fetch-iter-4-dev.md`). Worked around this iteration via two independent cross-checks
  (manual dot-tally + collect-only per-file sum, both = 1399) plus a small isolated re-run of the
  skip-gated files (which *does* print its summary cleanly) — not a test-content problem, exit code 0
  corroborates zero failures throughout.
- Full click-through browser verification of J-01 (`/structure` Edge Report section's actual render),
  J-04 (button absence), J-06 (page-load timing / stuck loading panel), and J-07's sim-cockpit
  spot-checks (`SIM-BUYER`→`buyer_control`, `SIM-SELLER`→`seller_control`) is the browser-qa-agent's
  step per the spec's TESTING REQUIREMENTS; the evidence above is the dev-level code/API/SSR
  inspection leg only.
- No credential blockers this iteration — the real corpus (`.data/datasets`, 882MB) is already
  present locally (persisted from the prior `tradable_wall` session), so unlike that session's own
  baseline, no journey here is human-blocked on missing data or credentials.

## Suggested Next Phase

Confirms the spec's own NOTES and goal.md's dependency order (J-01 → J-02 → J-03 → J-04 → J-05, with
J-06 riding on J-02's durable index and J-07 guarding continuously): iteration 1 should build **J-01
alone** — `EdgeReportCache.lookup`/`compute_and_publish` beside the untouched `get_or_compute`,
`edge_report.peek_strategy_comparison_report`, the shared cache-DB-path resolver, and the
`/structure` not-computed panel. It is the smallest, most self-contained change (rewires one existing
route + two new cache methods + one frontend panel), is explicitly framed as "stop the bleeding," and
is the direct fix for the exact live defect confirmed above (J-01 section) — it also removes the
SAFETY NOTE's hazard for every later iteration's own browser-qa step, since a cold cache would then
return the honest not-computed payload instead of computing inline.
