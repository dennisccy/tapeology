# Goal Iteration 14 — Coverage-index reconciliation (J-10)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 14
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - "**Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*"
  - "**Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*"
  - "**Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*"
  - "**Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
    MCP surface can change state. *(critical)*"
  - "**Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed,
    append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint,
    bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or
    rewritten — a new run is a new snapshot. *(critical)*"
  - "**Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or
    market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*"
  - "**The briefing describes, never advises.** Desk copy is descriptive measurement only — no
    advice, imperative, prediction, or ranking language implying action (\"buy\", \"watch this\",
    \"opportunity\"); the copy-discipline lint stays green unmodified. *(critical)*"
  - "**No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk
    surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a
    future era). *(critical)*"
  - "**The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability
    test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged
    by the sentinel every iteration. *(critical)*"
  - "**The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside
    the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this
    Anti-goals section, or any other part of this file; proposed journeys MUST carry a
    single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and
    `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value
    journey just to keep the loop alive is a failure. *(critical)*"
  - "**Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are launched via `scripts/automation/host-guard-exec.sh claude`
    (the engine pauses `AWAITING_HOST_GUARD`, resumable, on an unconfined pump). Never disable,
    widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows
    the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*"

## GOAL

The operator can trigger a reconciliation of the derived bar-coverage index against the frozen bar
store from `/desk`, watch it repair itself through the existing `BarIndex.reindex()`, and see — both
in a durable, append-only run record and in the briefing's own coverage badges on the next screen —
exactly what was wrong before and what is right after, so the coverage badges the briefing already
shows become independently checkable instead of silently trusted.

## BACKGROUND

Era B closed `GOAL_ACHIEVED` + `CONFIRM_ACHIEVED` at iteration 13 (all 9 journeys passing). The
goal-proposer then measured the running system directly and appended J-10 inside the `AUTO:journeys`
marker block (`state/proposer-result.json`, `state/enhancement-proposals.jsonl`, 2026-07-28):
`apps/backend/.data/bars` holds 369 series files while `.data/bar_index.db` holds only 281 rows — 88
recorded series carry no index row at all, and 7 of those land on screened member×timeframe pairs
that the briefing already renders with a dark (`has_bars: false`) or silently-false coverage badge
(NFLX/META/NVDA read as fully uncovered on `screen-2026-07-27-936543601e75`; MSFT's `4h` badge is
dark while the store genuinely holds that series). The only existing repair, `BarIndex.reindex()`, is
called by nothing outside its own test — no operator can reach it. J-10 is the only failing/target
journey this iteration; the two other backlogged proposer candidates (top-up-runs `integrity_errors`
disclosure; coverage-freshness date-format consistency) were explicitly NOT promoted this cycle and
stay out of scope here.

**Depth = full, citing trigger #2 (Data model).** This iteration adds a new persisted schema — an
append-only reconciliation run-record store mirroring `desk_topup_log.TopupRunStore`'s discipline —
plus a new compute-manager class serving a new transient-progress contract (both registered in
`blueprint.md` by this spec, before any code lands). Full depth is also what makes J-10's own
acceptance closeable in this single pass: its `[NEW]`-flagged demo-narrator walkthrough clause can
only be produced by a lane that runs BEFORE the evaluator scores, which this session proved (iter-12,
`ESCALATE`) is true only at `full` depth — a `lean` dispatch on this journey would repeat that exact
dead end.

**Lessons this iteration must apply (from this session's own evaluator log):**
- **iter-12 (first entry) — one-way-door capture order.** An append-only store's honest-EMPTY state
  can never be re-created once real records exist. Sequence on ONE scoped rig: seed → boot BOTH
  backend and frontend → capture the empty Reconciliation-section screenshot FIRST → only then
  trigger any reconciliation run.
- **iter-12 (second entry) / iter-13 — lane ordering by depth.** The demo-narrator lane runs BEFORE
  the goal-evaluator only at `full` depth (this iteration). Do not let a later iteration retry this
  journey at `lean`.
- **iter-9 (second entry) / iter-11 — scoped rig must be named to EVERY lane.** State the exact
  scoped root in the dev handoff, the browser-QA dispatch, AND the demo-narrator dispatch — a lane
  that silently reverts to the ambient store (or to a second, disconnected rig) breaks the single
  coherent walkthrough this journey needs.
- **iter-4 (lessons.md) — a golden replay script can be a write path.** If a `journey-scripts/J-10.json`
  golden is recorded, prefer asserting the ALREADY-POPULATED, read-only Reconciliation section over
  clicking "Reconcile Index" (or "Run Screen") during replay — a click-driven step would record a
  real reconciliation/screen into whatever store the replay lane targets on every future run.
- **iter-10 — an evidence compute can collide with an existing golden's replay target.** Any screen
  computed for this iteration's evidence must run on a FRESH scoped copy of `.data/`, never the
  target the J-01–J-09 goldens replay against.

## IN SCOPE

### Backend
- [ ] A new desk module (name at build discretion — goal.md's own example:
      `app/research/desk_index_reconcile.py`) that classifies drift between `BarStore.list(include_bars=False)`'s
      healthy records + its own `errors`, and `BarIndex.list()`'s indexed rows, into the three honest
      buckets goal.md's J-10 step 1 names: (a) a series on disk with no index row (attributed to that
      record's own `symbol`/`timeframe`), (b) an index row whose `series_id` is not on disk (reported
      by `series_id` alone), (c) an index row under a checksum the store no longer reports. Pure
      composition of `bar_index.py`'s and `bars.py`'s EXISTING public reads — zero diff to either file
      (no new accessor, no schema change, no new index).
- [ ] The same module repairs ONLY through the existing `BarIndex.reindex(store)` (`bar_index.py:198`)
      and nothing else — never a second index-building path — then re-runs the identical drift
      comparison post-repair and records the result together with `BarStore.list()`'s own `errors`
      verbatim (a corrupt file the rebuilt index cannot carry is disclosed on the record, never
      silently dropped).
- [ ] A single-flight, pollable, cancellable compute-manager class for the reconcile run, mirroring
      `DeskTopupComputeManager`'s shape (trigger/snapshot/cancel/`join_all`, atomic snapshot publish
      under a lock). An explicit `POST` starts it; page-load `GET`s never trigger it (T-4/5C lesson).
- [ ] A durable, checksummed, append-only run-record store mirroring `desk_topup_log.TopupRunStore`'s
      discipline exactly (checksum-verified load, `record()` the only mutation, no update/delete
      method anywhere), written EXACTLY ONCE at the run's terminal state by a SINGLE shared writer the
      compute manager's worker-resolve path calls.
- [ ] New routes under the existing `/research/desk` router (`desk_routes.py`): a durable-list read
      (goal.md's own suggested path: `GET /research/desk/coverage/reconcile/runs`) plus a
      trigger/poll/cancel trio mirroring `/research/desk/topup/compute*` (exact subpaths at build
      discretion). Honest-empty `{"runs": [], "latest": null}` HTTP 200 before any run. NO MCP tool
      added — `get_endpoint`'s existing `/research/` allowlist already reaches the new GET path.
- [ ] Storage dir: a bare env-var-or-sibling-of-`desk_universe_dir_resolved()` default (the
      `resolve_desk_topup_log_dir` pattern) — deliberately NOT a new `Config` field.
- [ ] Zero diff to `bar_index.py`, `bars.py`, `tradability.py`, `levels.py`, `desk_coverage.py` —
      reconciliation changes only the derived index; `desk_coverage.get_desk_coverage` keeps its
      single existing ownership of coverage/freshness and needs no code change to reflect the repair.

### Frontend
- [ ] A "Reconcile Index" trigger on `/desk`, wired like the existing Top-up button (live progress +
      cancel, mirrors the `TopupComputeControl` pattern).
- [ ] A read-only "Index Reconciliation" `<section aria-label="...">`, placed at the page's top level
      beside Top-up Runs (the same "always visible, never gated on screen state" placement precedent
      iter-11 established for Top-up Runs — reconciliation state is likewise independent of whether a
      screen has ever been computed). Shows the latest run's counts (series on disk, rows indexed
      before/after, affected pairs, store errors) with an honest no-run-recorded empty state.
- [ ] Copy is descriptive measurement only (no advice/imperative/urgency/prediction language) —
      covered by the existing `tests/test_copy_discipline.py` lint, which must stay green unmodified
      with zero edits to the lint itself.

### New user-facing capability
The operator can trigger, from `/desk`, a reconciliation of the derived bar-coverage index against
the frozen bar store, watch live progress with a cancel option, and read the latest reconciliation's
before/after drift counts and affected pairs — turning the coverage badges the briefing already shows
into something the operator can independently check and correct, not just trust.

### New information displayed
The Index Reconciliation section's run history and latest-run detail: series on disk, rows indexed
before/after, the affected symbol×timeframe pairs before and after repair, and any store errors
(corrupt files) surfaced verbatim; an honest "no reconciliation run recorded yet" empty state before
the first run.

### New user actions
"Reconcile Index" button (trigger); a cancel control while a reconciliation is running (mirrors
Top-up's cancel, including its 409-when-idle behavior).

### UI surface changes
One new read-only section on the existing `/desk` page. No new page, no nav change.

### Product surface delta
`/desk` gains a third operator-triggered action (alongside Run Screen and Top-up) and a third durable,
browsable run-history panel, sitting beside Top-up Runs.

### Blueprint conformance
Lives under the already-registered **Desk** canonical home (`/desk`), the same home as
J-01/J-02/J-03/J-04/J-05/J-08/J-09. No nav-skeleton change — `blueprint.md`'s Navigation skeleton and
Feature/journey-homes table have already been updated additively by this spec to register J-10's
"Index Reconciliation" section there.

### Data-contract additions
Both rows below are already registered in `runs/goal-session-desk/state/blueprint.md`'s Data Contract
table (see its "RESOLVED at iter-14" trailer note for the full build-time scope rationale; also see
`assumptions.md` iter-14 for why two rows, and why no CLI):

1. **Coverage-index reconciliation run records (durable ledger).** Owner: new
   `app/research/desk_index_reconcile.py` (name at build discretion). Endpoint:
   `GET /research/desk/coverage/reconcile/runs` (exact path at build discretion). Shape:
   `{"runs": [<meta-only: id, config_fingerprint, started_utc, finished_utc, state:
   "done"|"cancelled"|"failed", series_on_disk: int>=0, rows_indexed_before: int>=0,
   rows_indexed_after: int>=0>, ...], "latest": <same fields PLUS drift_before: {"unindexed_series":
   [{"series_id","symbol","timeframe"}], "orphan_index_rows": [{"series_id"}], "stale_checksum_rows":
   [{"series_id"}]}, drift_after: <same shape>, store_errors: [{"file","error"}]> | null}`. Honest-empty
   `{"runs": [], "latest": null}`, HTTP 200, before any run.
2. **Coverage-index reconciliation compute progress (transient).** Owner: the same new module's
   compute-manager class. Endpoints: `POST /research/desk/coverage/reconcile/compute` (trigger),
   `GET /research/desk/coverage/reconcile/compute` (poll), `POST
   /research/desk/coverage/reconcile/compute/cancel` (cancel) — exact subpaths at build discretion.
   Shape: `{"id": str, "state": "running"|"done"|"cancelled"|"failed", "started_utc": str,
   "finished_utc": str | null, "error": str | null, "progress": {...phase/counters at build
   discretion}}`. Process-scoped, honestly lost on restart, never a research value.

Neither row duplicates any existing Data-Contract value: coverage/freshness keeps its single existing
owner (`desk_coverage.get_desk_coverage` over `bar_index`), and both new rows describe attempts/repairs
only.

## OUT OF SCOPE

- A CLI warmer for the reconcile action — goal.md's own J-10 text never names one (unlike J-02/J-03);
  logged as a build-time scope call in `assumptions.md` iter-14.
- Any new MCP tool — goal.md step 4's explicit non-goal; `get_endpoint`'s existing `/research/`
  allowlist already reaches the new GET route with zero code change.
- Any change to `bar_index.py`'s or `bars.py`'s public API beyond their existing reads — no new
  accessor, no schema change, no new index (goal.md step 1's own rail).
- Any change to `desk_coverage.py`, `tradability.py`, `levels.py`, `StructureChart.tsx` — all take a
  zero diff this iteration.
- Repairing or rewriting a corrupt bar-series FILE itself — reconciliation only rebuilds the derived
  index; a corrupt file stays on disk untouched, disclosed as a store error (goal.md step 2's rail).
- A PnL-ledger append for this journey — goal.md's acceptance text explicitly substitutes the SSOT
  criterion "in place of a PnL-ledger append, which this era's Non-Goals forbid."
- Any scheduler/auto-run/cron trigger for reconciliation — every run stays an explicit operator act.
- Running the real ~88-pair AMBIENT-store reconciliation as part of this iteration's automated gates —
  fixture-scoped coverage (a small, planted drift case per goal.md step 6) is the required, keyless
  gate; the real run is an operator-later act, reported honestly if and when it happens, never a CI
  gate (goal.md's own parenthetical).
- The two other backlogged proposer candidates (top-up-runs `integrity_errors` disclosure;
  coverage-freshness date-format consistency) — explicitly not promoted this cycle
  (`state/proposer-result.json`).
- Any nav-skeleton structural change — the new section lives on the already-registered `/desk` home.

## DEFINITION OF DONE

- [ ] J-10 passes via browser-qa-agent: the honest no-run-recorded screenshot (with a dark-badged
      ranked row already computed) and the populated-Reconciliation-section screenshot (drift counts
      + the same row's badge lit on a NEW screen run) are both captured, legible, on ONE fixture-scoped
      rig, in that order (TC-17, TC-18).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09 remain green
      (deterministic replay + LLM fallback).
- [ ] No anti-goal violation introduced: SSOT (zero diff to `bar_index.py`/`bars.py`/`tradability.py`/
      `levels.py`/`desk_coverage.py`/`StructureChart.tsx`), append-only ledger discipline, explicit-
      operator-act only (no scheduler/auto-trigger), no new MCP tool, copy-discipline lint green.
- [ ] Unit/integration tests pass per TC-1 through TC-16 and TC-20; full backend suite green, no
      regressions.
- [ ] `Config().config_fingerprint()` still prints `08e471b10130e1e2`; zero new `Config` field.
- [ ] `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` still names exactly 17 tools.
- [ ] Both new Data-Contract rows registered in `blueprint.md` (already done by this spec) are matched
      byte-for-byte by the shipped code's served shape.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough covers the reconciliation end to end (empty state,
      then populated state, in that order, on the same rig) — TC-19.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-14-dev.md`, naming the exact scoped rig
      path used for all evidence.

## TESTING REQUIREMENTS

- Browser: J-10 (TC-17, TC-18, TC-19 — this iteration's target). Regression replay + LLM fallback for
  J-01, J-02, J-03, J-04, J-05, J-07, J-08, J-09 (browser-verifiable); J-06 by its 17-tool contract
  test (no browser surface).
- Unit/integration: the three drift-classification buckets (TC-1–TC-3); repair-and-reverify through
  `BarIndex.reindex()` only, including the corrupt-file case (TC-4, TC-5); the durable run-record
  store's honest-empty/append-only/checksum discipline including a corrupted run-record file (TC-6,
  TC-7, TC-20); byte-identical bar-store/universe/screen/top-up files before and after a run (TC-8);
  the compute manager's idle-poll/single-flight/cancel contract (TC-9, TC-10, TC-11); the SSOT proof
  that a post-repair screen is a new snapshot under a new `bar_store_signature` (TC-12); sentinel
  checks — fingerprint, Config exclusion set, MCP tool count, zero-diff files, copy-discipline lint
  (TC-13–TC-16).
- Error cases: a corrupted run-record file surfaces as an explicit, named error rather than being
  silently dropped or fabricated (TC-20); a cancel request while idle returns 409 rather than
  silently no-op-ing (TC-11); a GET on any new reconcile endpoint before any run/job exists returns
  an honest empty/`null` payload rather than a 404 or an exception (TC-6, TC-9).

Test-first contract:

- TC-1: given a scoped `BarStore` holding a recorded series for one (symbol, timeframe) and a scoped
  `bar_index.db` with no row for that pair, when the drift classifier runs, then it reports exactly
  one "on disk, no index row" entry naming that symbol and timeframe, and zero entries in the other
  two buckets for that pair.
- TC-2: given a scoped `bar_index.db` row whose `series_id` matches no file in the scoped `BarStore`,
  when the drift classifier runs, then it reports exactly one "orphan index row" entry naming that
  `series_id` alone, with no symbol or timeframe attached.
- TC-3: given a scoped `BarStore` series file that is corrupted so `BarStore.list()` reports it in
  `errors` while a `bar_index.db` row still points at its `series_id`, when the drift classifier
  runs, then it reports exactly one "stale-checksum" entry for that `series_id`.
- TC-4: given the drift state of TC-1, when `POST` triggers a reconciliation run, then the run
  resolves state `"done"`, `GET /research/desk/coverage` reports `has_bars: false` for that pair
  before the run and `has_bars: true` after it, and the recorded run's `drift_before` names that
  exact pair while `drift_after` no longer does.
- TC-5: given the planted corrupt file of TC-3, when a reconciliation run executes
  `BarIndex.reindex()`, then the rebuilt index carries no row for that file's `series_id`, and the
  run record's `store_errors` field lists that file's name and error message verbatim, matching
  `BarStore.list()`'s own `errors` entry byte-for-byte.
- TC-6: given no reconciliation run has ever been recorded on a fresh scoped store, when
  `GET /research/desk/coverage/reconcile/runs` is called, then it returns HTTP 200 with
  `{"runs": [], "latest": null}`.
- TC-7: given one recorded reconciliation run, when a second reconciliation run is triggered and
  completes, then the store directory contains two run-record files, the first file's SHA-256
  checksum is unchanged from before the second run, and the runs endpoint lists both with the newest
  as `latest`.
- TC-8: given a scoped rig with recorded universe, screen, and top-up run files present before a
  reconciliation run, when the reconciliation run completes, then every `.data/bars/*.json` series
  file's SHA-256 is unchanged, and every previously recorded universe/screen/top-up-run file's
  checksum is unchanged (nothing backfilled or rewritten).
- TC-9: given no reconciliation job has ever run in the process, when `GET` is called on the reconcile
  compute-progress poll endpoint, then it returns `null` and no reconciliation run is started as a
  side effect.
- TC-10: given a reconciliation job is already `"running"`, when a second `POST` trigger is issued,
  then it returns `started: false` with the existing job's unchanged snapshot, never starting a
  second concurrent job.
- TC-11: given no reconciliation job has ever run, or the last one is terminal, when
  `POST .../reconcile/compute/cancel` is called, then it responds HTTP 409 naming that no
  reconciliation compute is running.
- TC-12: given the drift state of TC-1 repaired by one reconciliation run, when a NEW screen is
  computed for the same scoped universe and as-of, then the resulting snapshot is a new append-only
  file under a new `bar_store_signature`, and the previously recorded (pre-repair) screen snapshot
  file's checksum is unchanged on disk.
- TC-13: given the full backend suite, when it is run after this iteration's changes, then it passes
  with zero failures, `Config().config_fingerprint()` still prints `08e471b10130e1e2`, and
  `apps/backend/app/config.py`'s exclusion set carries no new field.
- TC-14: given `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS`, when it is parsed after
  this iteration's changes, then it still names exactly 17 tools, with no reconcile-named tool added.
- TC-15: given `git diff` scoped to `bar_index.py`, `bars.py`, `tradability.py`, `levels.py`,
  `StructureChart.tsx`, when compared against the iter-13 snapshot, then it reports zero changes to
  all five files.
- TC-16: given `tests/test_copy_discipline.py`'s frontend-literal lint, when it runs against the new
  Reconciliation section's copy, then it passes unmodified with zero banned advice/imperative/
  prediction terms found.
- TC-17 (browser, before-state — capture FIRST on a fresh scoped rig, before any reconciliation run
  is ever recorded there): given a fixture-scoped `/desk` after the T-9 clean rebuild, with one screen
  already computed showing the TC-1 pair's ranked row, when the operator opens `/desk`, then the Index
  Reconciliation section reads an honest "no reconciliation run recorded yet" state and that ranked
  row's coverage badge for the drifted timeframe renders dark, both legible.
- TC-18 (browser, after-state — captured on the SAME rig after TC-17, never a second/disconnected
  rig): given the same rig after one reconciliation run and one NEW screen run, when the operator
  opens `/desk`, then the Index Reconciliation section shows the run's series-on-disk count,
  rows-indexed count, and the affected symbol×timeframe pair, and the same ranked row's coverage
  badge for that timeframe renders lit, both legible.
- TC-19: given the demo-narrator lane dispatched at full depth (runs before evaluator scoring), when
  it records the `[NEW]`-flagged J-10 walkthrough against the SAME scoped rig used for TC-17/TC-18,
  then the walkthrough's steps narrate the empty state before the populated state, in that order,
  with each step's frame matching the state its narration describes.
- TC-20: given one genuine reconciliation run record on disk plus a second, deliberately corrupted
  run-record file in the same directory, when the runs endpoint is called, then the genuine record
  still appears in `runs`/`latest` and the corrupted file's verification failure is surfaced as an
  explicit, named error, never silently dropped and never served as data.

## NOTES

- **Evidence sequencing is binding (see BACKGROUND's lesson list).** On ONE fresh scoped copy of
  `.data/` (never the ambient store, never a second/disconnected rig): (1) plant the TC-1 drift case
  (a bar series recorded with no matching `bar_index.db` row) plus, if convenient, the TC-3 corrupt-file
  case; (2) register a small scoped universe snapshot covering the affected symbol; (3) boot BOTH
  backend and frontend against that rig; (4) compute a screen (screen run #1) so the affected row
  exists with a dark badge; (5) capture TC-17 NOW, before any reconciliation run is ever recorded —
  this is a one-way door; (6) trigger one reconciliation run; (7) compute a second, NEW screen (screen
  run #2, same universe/as-of) so the SAME row now shows a lit badge; (8) capture TC-18; (9) record the
  `[NEW]`-flagged demo-narrator walkthrough (TC-19) against this same still-live rig, narrating steps
  5 and 8's states in order.
- **Name the scoped rig to every lane.** State the exact rig path in the dev handoff, the browser-QA
  dispatch, and the demo-narrator dispatch — not just one of them (iter-9's lesson).
- Use the pipeline's own isolated scratch directory for the scoped rig (this session's own
  `/home/dennis-chan/.cache/iad/iad.<iter-name>.<pid>/` convention) — never write large scoped copies
  directly under `/tmp` (this session has hit `/tmp` quota exhaustion before).
- **T-9 clean rebuild is mandatory before any browser evidence**: `rm -rf apps/frontend/.next` and
  restart both processes before TC-17/TC-18.
- If a `journey-scripts/J-10.json` golden replay script is recorded, prefer steps that assert the
  ALREADY-POPULATED Reconciliation section's read-only text over a step that clicks "Reconcile Index"
  or "Run Screen" — a mutating step would record a real reconciliation/screen into whatever backend
  future replay runs target (iter-4's lessons.md entry).
- Host-guard caps are law (critical anti-goal, added 2026-07-28): any background reconciliation job or
  test run must inherit the existing CPU-mask/thread-cap wrapping — never widen or bypass it to make
  this iteration's evidence capture faster.
- The real ~88-pair ambient-store reconciliation (the number goal.md's own rationale cites) is NOT a
  gate for this iteration — the fixture-scoped, small planted-drift case (TC-1–TC-20) is what's
  required. The operator may run the real reconciliation later, reported honestly as an operator act.
- `runs/goal-session-desk/state/blueprint.md` has already been updated additively by this spec
  (Navigation skeleton sentence, Feature/journey-homes row, two new Data-Contract rows, and a
  "RESOLVED at iter-14" trailer note) — no nav-skeleton structural change, so no
  `blueprint.reapproval-requested` file was written.
