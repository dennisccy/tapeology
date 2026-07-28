# Goal Iteration 11 — J-09: an append-only record of what every top-up run attempted

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 11
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
    tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk`
    BESIDE the kept two pages — the sanctioned kept-surface edits are J-05's additive `/structure`
    prefill and **R-1**'s price-less-row repair, which changes no output for finite data and leaves
    every recorded series on disk untouched.) *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
    labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
    feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
    MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - **Membership is never a signal.** Universe membership (and any constituents metadata) selects
    WHAT to screen; it never enters a computation, rank formula beyond selection, feature, or
    report as an input value. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed,
    append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint,
    bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or
    rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or
    market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no
    advice, imperative, prediction, or ranking language implying action ("buy", "watch this",
    "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk
    surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a
    future era). *(critical)*
  - **The demolition stays demolished.** No journal-era machinery returns; the desk ledger records
    machine output only — zero manual-input write paths on desk records this era (dispositions/
    annotations are Era C's design space). *(critical)*
  - **The ledger never holds orders.** No sizes, tickets, entries/exits, or account concepts in any
    desk record — rail 1 in desk terms. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test
    fetches the network; live fetch/top-up/screen runs are operator-run verifications reported
    honestly (run-or-not-run), never CI gates. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability
    test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged
    by the sentinel every iteration. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside
    the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this
    Anti-goals section, or any other part of this file; proposed journeys MUST carry a
    single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and
    `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value
    journey just to keep the loop alive is a failure. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are launched via `scripts/automation/host-guard-exec.sh claude`
    (the engine pauses `AWAITING_HOST_GUARD`, resumable, on an unconfined pump). Never disable,
    widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows
    the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Give every top-up run a durable, append-only record of exactly what it attempted — per-pair
reused/fetched/failed outcomes with vendor detail preserved verbatim, terminal state, and how many
pairs it never reached — surfaced as a new read-only "Top-up Runs" section on `/desk`, so a run's
outcome survives past the next run superseding its in-flight compute snapshot.

## BACKGROUND

Iteration 10 closed Era B `GOAL_ACHIEVED`, two-key confirmed (`runs/goal-session-desk/iter-10/eval.md`,
`iter-10/eval-confirm.md` = `CONFIRM_ACHIEVED`) — all eight journeys (J-01–J-08) `passing` with
opened evidence, `apps/` byte-identical to the proven iter-9 tree, suite 1346 passed / 8 skipped /
0 failed, fingerprint `08e471b10130e1e2`, HEAD `f664297`. The goal-proposer then ran its
post-achievement scan (`runs/goal-session-desk/state/proposer-result.json`,
`state/enhancement-proposals.jsonl`, 2026-07-28) and found one real, measured gap inside an
already-covered capability (Key Capability 2, top-up): `run_topup`'s per-pair outcomes
(`desk_topup_compute.py:158/184`, the `HTTPException` detail preserved verbatim at `:147`) are
process-scoped memory only — `GET /research/desk/topup/compute` already returns `null` once a job
is superseded, so a real ~100-symbol run's outcome is unrecoverable today (measured live against
the running backend: the frozen `BarStore` holds series for 65 symbols; 38 of
`universe-2026-07-25-49b33fa31680`'s 101 members hold none, exactly matching the latest screen's 38
`skipped: no_bars` rows — but whether each of those 38 (plus 5 more with a dark `1h` badge) was
attempted, refused, or never reached is unknowable from any store that exists today). The proposer
promoted exactly one journey, **J-09**, inside `docs/goal.md`'s `AUTO:journeys` marker block (the
only place it is allowed to write), and again declined to promote `bar-index-store-reconcile`
(re-measured and backlogged a second cycle — 369 store series vs 281 `bar_index` rows, the same 7
member×timeframe pairs still read `has_bars:false` against a store that holds them; the ranking is
unaffected and `/desk` already discloses that divergence honestly). Per the priority rubric and the
"do not manufacture more work" rule, this iteration builds only the promoted journey.

**Depth — full, triggers 1 and 2 (Structural/cross-cutting AND Data model).** J-09 adds a wholly
NEW persisted, checksummed, append-only store (mirroring `UniverseStore`/`ScreenStore`'s
discipline) — a brand-new blueprint Data-Contract row, not an additive field on an existing one
(unlike J-08's two fields folded into the already-registered screen row). That alone is trigger 2's
"adds persisted schema." It is also cross-cutting (trigger 1): the ONE shared writer this journey
requires must be invoked identically from TWO independent call sites that today have no shared
terminal-state hook at all — `DeskTopupComputeManager`'s background-thread worker (`_work`/
`_resolve`, `desk_topup_compute.py` ~:262/:282) and the CLI's synchronous `main` (~:329) — plus a
new route (`desk_routes.py`) and a new `/desk` UI section. The failure modes here (the two callers
silently diverging in shape, or a crash mid-walk fabricating a record for a run that never reached
its terminal state) are not covered by any single existing module's test file. This session's own
precedent agrees: iteration 9 — a comparably store-touching, single-promoted-journey iteration —
was also dispatched full.

**Lessons applied** (from `lessons.md`): iter-9's second entry applies directly — a fixture-scoped
rig existing in the DEV lane does not protect the BROWSER-QA lane; the scoped backend/data root
must be named explicitly in the browser-QA dispatch (not only the dev spec), and the results report
must state which data root produced the evidence, because J-09's required "failed pair" screenshot
means actually running a fixture-scoped top-up that includes at least one induced failure. iter-10's
entry is a live warning for whoever names the new run record's identifying key: check the target
store for a pre-existing record before assuming a fresh recording is collision-free, and disclose
any collision in the golden script's own `notes` rather than silently. The iter-4/iter-5 lessons on
write-triggering goldens apply to the new `journey-scripts/J-09.json`: scope its backend, never the
ambient `.data/`, and add a post-match liveness assertion (assert the page is still alive AFTER the
first matching string, not only at the match). The iter-8 lesson on undisclosed golden edits applies
to any FUTURE iteration that touches this newly-recorded script.

## IN SCOPE

### Backend
- [ ] New module `app/research/desk_topup_log.py` (name at build discretion) — the sole owner of
      top-up run records: one frozen, checksummed, append-only JSON file per run (mirrors
      `desk_screen.py`'s `ScreenStore` / `desk_universe.py`'s `UniverseStore` discipline —
      checksum-verified load, `record()` the only mutation, no update/delete function anywhere).
- [ ] A SINGLE shared writer function in that module, called exactly once, at a run's terminal
      state, by BOTH existing entry points: `DeskTopupComputeManager`'s worker resolve path
      (`desk_topup_compute.py` `_work`/`_resolve`, ~:262/:282) and the CLI's `main` (~:329) — never
      a second write path, never a second outcome shape. `run_topup` (`:158`) and `_run_one_pair`
      (`:123-155`) stay byte-unchanged; the writer only ever reads their already-produced outcomes.
- [ ] New route `GET /research/desk/topup/runs` in `desk_routes.py` — lightweight run-meta list +
      the latest full record; honest-empty `{"runs": [], "latest": null}`, HTTP 200, before any
      run. Storage dir mirrors `desk_screen.resolve_desk_screen_dir`'s bare
      env-var-or-sibling-of-`desk_universe_dir_resolved()` default (NOT a new `Config` field).
- [ ] Interrupted-run honesty: a run whose process ends before the writer's terminal call leaves
      NO record for it (asserted by a test that simulates the terminal write never happening and
      confirms the store gains zero new file).
- [ ] Confirm (no code change expected) `app/mcp/__init__.py`'s existing `/research/`
      `get_endpoint` allowlist (`ALLOWED_GET_PREFIXES`) reaches the new path with zero new
      `_STATIC_PATHS` entry — J-06's 17-tool contract stays green.
- [ ] Zero diff to `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`; zero new
      `Config` field; `Config().config_fingerprint()` stays `08e471b10130e1e2`.

### Frontend
- [ ] `/desk` page: new read-only "Top-up Runs" section beside the existing "Screen History" panel
      (`apps/frontend/app/desk/page.tsx`, the `section aria-label="Screen history"` block ~:827) —
      per run: date + id, universe snapshot id, terminal state, attempted-of-total pairs, counts by
      outcome, and for the latest run every `failed` pair's detail rendered verbatim plus the
      honest count of pairs the run never reached; an honest empty state when no run is recorded;
      copy stays descriptive-measurement only (`tests/test_copy_discipline.py` must stay green
      unmodified).

### Golden script / regression asset
- [ ] Record `runs/goal-session-desk/journey-scripts/J-09.json` as this era's newest deterministic-
      replay golden, scoped to a throw-away backend per the iter-4/iter-5 lessons (never the
      ambient `.data/`); include a post-match liveness assertion.

### New user-facing capability
The operator can now see, on `/desk`, a durable record of every top-up run's outcome — which
symbol×timeframe pairs were reused, freshly fetched, or failed (with the vendor detail), and how
many pairs a cancelled or interrupted run never reached — instead of that information vanishing the
moment the in-flight compute snapshot is superseded by the next run.

### New information displayed
Top-up run history on `/desk`: run date + id, universe snapshot id, terminal state
(done/cancelled/failed), attempted-of-total pair counts, counts by outcome (reused/fetched/failed),
and — for the latest run — every failed pair's recorded detail plus the honest unreached-pairs
count.

### New user actions
None. No new button or control ships this iteration — the existing Top-up button and its live
progress/cancel controls are unchanged; this journey is a pure read-only disclosure of outcomes the
Top-up compute already produces.

### UI surface changes
One new read-only panel/section on `/desk`, placed beside the existing Screen History panel.

### Product surface delta
`/desk` gains a persistent, browsable record of top-up attempts that previously existed only for
the duration of one in-flight (or last-terminal) compute poll and was lost the moment a newer run
started.

### Blueprint conformance
This iteration's only surface change is a new read-only section on the ALREADY-REGISTERED `/desk`
canonical home (Desk nav section, the same page J-04/J-05/J-08 already use) — no new page, no
nav-skeleton change. `blueprint.md` has been updated additively (this iteration, before dispatch):
a new "Top-up run records" Data-Contract row, a new J-09 row in the Feature/journey-homes table
(home = `/desk`, same as J-04), and a "RESOLVED at iter-11" trailer note. No
`blueprint.reapproval-requested` file was written — nothing about the nav skeleton changed.

### Data-contract additions
- **Top-up run records (per-run outcome ledger)** — computed by new `app/research/desk_topup_log.py`
  (name at build discretion), served by `GET /research/desk/topup/runs`. Response shape:
  `{"runs": [<lightweight meta only>, ...], "latest": <full record> | null}`, honest-empty
  `{"runs": [], "latest": null}` (HTTP 200) before any run. Full record fields: `id: str`,
  `universe_snapshot_id: str | null`, `requested_window: {"start": str, "end": str}`,
  `config_fingerprint: str`, `started_utc: str (ISO 8601 UTC)`, `finished_utc: str (ISO 8601 UTC)`,
  `state: "done" | "cancelled" | "failed"` (terminal only — never `"running"`; a record is written
  once, at terminal state), `pairs_total: int >= 0`, `pairs_attempted: int >= 0` (`<= pairs_total`;
  `len(outcomes)` at terminal time — the pairs never reached by a cancelled/interrupted run are
  `pairs_total - pairs_attempted`, never conflated with an attempted-and-failed pair), `outcomes:
  [{"symbol": str, "timeframe": str, "outcome": "reused" | "fetched" | "failed", "detail": str |
  null}, ...]` byte-identical to `run_topup`'s own return for that walk. Lightweight run-meta
  (the `runs` list entries) carries every field above EXCEPT `outcomes` (mirrors
  `GET /research/desk/screen`'s meta-only `screens` list convention — never the full per-pair array
  for every historical run in one list call).
- One frozen, checksummed, append-only JSON file per run; written EXACTLY ONCE by the single shared
  writer, at terminal state only; never rewritten, backfilled, or recomputed — a second run appends
  a new file.
- Records ATTEMPTS only. Bar coverage/freshness keeps its existing single owner (`desk_coverage.py`
  over `bar_index`, the already-registered "Per-member bar coverage + freshness" row) — this
  journey creates no second coverage path anywhere.
- Storage dir: bare env-var-or-sibling-of-`desk_universe_dir_resolved()` default (the
  `resolve_desk_screen_dir` pattern) — NOT a new `Config` field; zero change to the
  `config_fingerprint()` exclusion set.
- No new MCP tool — `get_endpoint`'s existing `/research/` allowlist already reaches the new path
  with zero code change to `app/mcp/__init__.py`.

## OUT OF SCOPE

- Any edit to `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, the
  engine, or any of R-1's eight named files — Frozen foundations.
- Any change to what `run_topup`/`_run_one_pair` compute or return — the outcome-classification
  logic (`desk_topup_compute.py:123-188`) stays byte-unchanged; the writer only reads its output.
- Any change to `desk_coverage.py`'s coverage/freshness computation or its single owner — J-09
  records attempts only, never a second coverage path.
- Any new `Config` field, new MCP tool, new page, or nav-skeleton change.
- A PnL-ledger append — this era's Non-Goals forbid it; J-09's acceptance uses the single-source-
  of-truth criterion in its place (goal.md's own text, the J-08 precedent).
- Backfilling, rewriting, or recomputing any already-recorded universe, screen, or top-up-run
  record — the append-only rail is absolute.
- The backlogged `bar-index-store-reconcile` proposal — explicitly NOT promoted by the
  goal-proposer this cycle; do not build it.
- A real ~100-symbol operator top-up run — this iteration proves the mechanism on a fixture-scoped
  rig (per T-9/T-10 and this era's hermetic-suite discipline); the real run stays a separate,
  explicit, honestly-reported operator act.
- A date picker, a retry-only-failed-pairs control, or any new interactive control on the Top-up
  Runs section — read-only disclosure only, per goal.md's own step 4.
- Re-verifying J-01–J-08's own acceptance clauses beyond the smoke-set regression replay — they are
  "Do not redo" per `iteration-state.md`.
- The same-date screen ambiguity, keyboard access for history rows, and the other carried one-line
  hardening items — unrelated to this journey.

## DEFINITION OF DONE

- [ ] `app/research/desk_topup_log.py` persists exactly one frozen, checksummed, append-only run
      record per completed top-up run, written once at terminal state by a single shared writer
      called from both `DeskTopupComputeManager`'s worker resolve path and the CLI's `main`.
- [ ] `GET /research/desk/topup/runs` serves the honest-empty `{"runs": [], "latest": null}`
      (HTTP 200) before any run, and after a run, a `latest` record whose `outcomes` are
      byte-identical to `run_topup`'s own return for that walk.
- [ ] A cancelled run's persisted record has `state: "cancelled"` and `pairs_attempted <
      pairs_total`.
- [ ] A run interrupted before its terminal write leaves zero new record — never a fabricated
      entry.
- [ ] A second run appends a new record while every previously recorded file's checksum stays
      unchanged on disk.
- [ ] `/desk` shows a read-only "Top-up Runs" section beside Screen History: an honest empty state
      before any run; after a run, attempted-of-total pairs, per-outcome counts, and (for the
      latest run) every failed pair's detail verbatim plus the honest unreached-pairs count.
- [ ] Zero diff to `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`; zero new
      `Config` field; `Config().config_fingerprint()` stays `08e471b10130e1e2`.
- [ ] MCP surface stays exactly 17 tools; `get_endpoint` reaches the new path with zero
      `_STATIC_PATHS` addition.
- [ ] `tests/test_copy_discipline.py` passes unmodified against the new panel's copy.
- [ ] `journey-scripts/J-09.json` recorded as this era's newest golden replay script, scoped to a
      throw-away backend, and proven with a verify-mode replay.
- [ ] J-09 passes via browser-qa-agent, including both required screenshots (honest no-run-recorded
      state; populated Top-up Runs section with a failed pair's detail legible).
- [ ] A `[NEW]`-flagged demo-narrator walkthrough covers the top-up-run disclosure end to end.
- [ ] Required-still-passing journeys J-01–J-08 remain green (deterministic replay + LLM fallback).
- [ ] No anti-goal violation introduced.
- [ ] Full backend suite passes at or above the 1346 passing / 8 skipped floor; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-11-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-09's full walk on a fixture-scoped rig (honest empty Top-up Runs state; a
  fixture-scoped top-up run containing at least one induced failure; the populated section with
  attempted-of-total, per-outcome counts, and the failed pair's detail legible); smoke replay of
  J-01–J-08 against the same scoped rig, named explicitly in the browser-QA dispatch.
- Unit/integration: the new `desk_topup_log.py` store (checksum/append-only/no-update-or-delete),
  the single-shared-writer contract exercised from BOTH the manager and the CLI, the
  interrupted-run-leaves-no-record test, the cancelled-run test, the second-run-appends test,
  `test_mcp_server.py` (re-run — no code change expected), `test_copy_discipline.py` (re-run green
  unmodified), the full backend suite
  (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`).
- Error cases: a pair's fetch failure is recorded with its detail preserved verbatim, and the run
  continues to the remaining pairs rather than aborting; a run whose process ends before the
  terminal write never produces a fabricated or partial record; a GET against the new endpoint
  before any run returns the honest-empty payload rather than a 404 or 500.

Test-first contract — TC- scenarios:

- TC-1: given a fixture-scoped rig with no top-up run ever executed, when `GET
  /research/desk/topup/runs` is called, then the response is HTTP 200 with body
  `{"runs": [], "latest": null}`.
- TC-2: given a fixture-scoped rig with a registered universe snapshot, when a top-up is triggered
  via `DeskTopupComputeManager.trigger()` and runs to completion, then `GET
  /research/desk/topup/runs`'s `latest.outcomes` list is byte-identical (same `symbol`/`timeframe`/
  `outcome`/`detail` values, same order) to the list `run_topup()` returned for that same walk.
- TC-3: given the same fixture-scoped rig, when the CLI entry point
  (`python -m app.research.desk_topup_compute`) is run to completion instead of the HTTP trigger,
  then the resulting run record's `outcomes` list has the identical shape (same field names and
  types) as a manager-triggered record's `outcomes` list — one shared writer, one schema.
- TC-4: given an in-flight top-up job, when its cancel is signaled mid-walk, then the persisted run
  record's `state` is `"cancelled"` and `pairs_attempted` is strictly less than `pairs_total`.
- TC-5: given a walk where one pair's fetch raises an error, when the run reaches its terminal
  state, then that pair's entry in the persisted record's `outcomes` list has `outcome: "failed"`
  and a `detail` string matching the raised error verbatim, and the remaining pairs after it are
  still present in `outcomes`.
- TC-6: given one already-persisted run record on disk with a known sha256 checksum, when a second
  top-up run completes, then `GET /research/desk/topup/runs`'s `runs` list has 2 entries, the first
  record's file on disk still has its original sha256 checksum, and `latest` reflects the second
  (newer) run.
- TC-7: given a top-up run whose terminal writer call is never invoked (simulating a process that
  ends mid-walk), when `GET /research/desk/topup/runs` is called afterward, then the `runs` list
  has zero entries for that run.
- TC-8: given no top-up run has ever been triggered, when `GET /research/desk/topup/runs` is called
  any number of times, then no top-up compute starts as a side effect — `GET
  /research/desk/topup/compute`'s own snapshot stays `null`.
- TC-9: given the current MCP tool registry, when `tests/test_mcp_server.py`'s `EXPECTED_TOOLS`
  contract test runs, then the tool count is exactly 17 (unchanged), and `get_endpoint` called with
  `path="/research/desk/topup/runs"` returns the identical JSON body a direct
  `GET /research/desk/topup/runs` call returns.
- TC-10: given the full backend suite, when it runs after this iteration's changes, then it reports
  0 failures at or above the 1346 passing / 8 skipped floor, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and `git diff --stat` for `tradability.py`, `levels.py`, `bars.py`, and
  `StructureChart.tsx` is empty.
- TC-11: given `tests/test_copy_discipline.py`'s frontend-literal lint, when it runs against the new
  "Top-up Runs" panel's copy, then it passes unmodified — zero advice/imperative/prediction-language
  literal flagged.
- TC-12 (browser): given `/desk` loaded on a fixture-scoped rig with a registered universe snapshot
  and zero top-up runs recorded, when the page finishes loading, then a screenshot shows the Top-up
  Runs section's honest empty-state text and zero run rows.
- TC-13 (browser): given the same rig after one fixture-scoped top-up run containing at least one
  `failed` pair, when `/desk` is reloaded, then a screenshot shows the Top-up Runs section with that
  run's attempted-of-total count, its per-outcome counts, and the failed pair's `detail` text all
  legible in one image.
- TC-14: given the new run-record store's directory resolution with no env-var override set, when
  it resolves, then it is a sibling directory of `desk_universe_dir_resolved()` (mirroring
  `resolve_desk_screen_dir`'s pattern), and `app/config.py`'s `config_fingerprint()` exclusion set
  gains zero new entry.
- TC-15: given `runs/goal-session-desk/journey-scripts/J-09.json` recorded this iteration, when
  `--mode verify --journeys J-09` is run against a fixture-scoped backend, then it reports 0 failed
  and the results file is saved.
- TC-16: given the `[NEW]`-flagged demo-narrator walkthrough requirement, when this iteration's
  showcase artifacts are generated, then a walkthrough entry flagged `[NEW]` describing the
  top-up-run disclosure (an empty run history, then a populated one with a failed pair) exists.
- TC-17: given `runs/goal-session-desk/journey-scripts/J-01.json` through `J-08.json`, when the
  deterministic replay lane runs them against the same fixture-scoped backend named in the
  browser-QA dispatch, then every one reports PASS (or, where no golden exists for a journey, the
  LLM fallback reports PASS) with no write-path side effect on the ambient `.data/` store.

## NOTES

- No open blockers carry into this iteration — the era's last one (owner ratification of R-1) has
  been resolved since iteration 8; nothing in `iteration-state.md`'s carried-by-choice list touches
  this journey.
- The "requested fetch window" field's exact capture point (once per run vs. reading the existing
  per-pair `_fetch_window_now()` call an extra time for record-keeping) is a build-time choice, not
  prescribed here — whichever is chosen must leave `run_topup`/`_run_one_pair`'s own computation
  byte-unchanged (OUT OF SCOPE). If the choice is genuinely ambiguous at build time, log it as an
  interpretation call the way `assumptions.md` iter-2/iter-3 already do for this era's other
  storage-location and derivation decisions.
- Recommended recipe for TC-12/TC-13's fixture-scoped rig: reuse this era's established
  scoped-backend pattern (`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` is the most
  recent worked example) rather than inventing a new one, and name the exact data root used in both
  the dev handoff and the browser-QA results report — the iter-9 lesson (second entry) exists
  because a prior iteration's browser-QA lane silently used the ambient store instead.
- To induce at least one `failed` outcome for TC-5/TC-13 without any network dependency (the suite
  stays keyless and hermetic), use the existing fixture-scoped Yahoo adapter's known failure
  taxonomy (`NoDataForWindow`/`UnsupportedTimeframe`) or a monkeypatched fetch — the same technique
  `test_desk_topup_compute.py`'s existing
  `test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_continues_(manager_env)`
  test already uses — rather than any live vendor call.
- If `journey-scripts/J-09.json`'s replay steps trigger a NEW top-up run to exhibit outcome data,
  scope that replay's backend explicitly (its own data dir) rather than pointing it at the ambient
  store, and check the target store for a pre-existing run record before assuming the recording is
  collision-free — the iter-5 and iter-10 lessons respectively.
- If any lane edits `journey-scripts/J-09.json` after recording it, say so explicitly in that lane's
  results report — the iter-8 lesson on undisclosed golden edits.
- This is expected to reopen the era's `GOAL_ACHIEVED` state to `CONTINUE` only for the duration of
  this one promoted journey — but the goal-decomposer does not declare verdicts; that is the
  evaluator's call after real evidence lands.
