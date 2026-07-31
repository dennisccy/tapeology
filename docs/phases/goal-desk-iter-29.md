# Goal Iteration 29 — Screen runs get a durable, honest ledger (J-18)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 29
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: a brand-new, never-before-built full-stack
  journey whose interaction spans the shared entry point both callers of `run_screen_and_record`
  use, a new durable store/module, a new route, and a new `/desk` section, with no existing single
  journey's own test coverage spanning that blast radius.
- **Target journeys:** J-18
- **Required-still-passing journeys:** J-03, J-04, J-05, J-06, J-07, J-09, J-10, J-12, J-16, J-17
- **Frontend Present:** yes
- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
    MCP surface can change state. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed,
    append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint,
    bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or
    rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or
    market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no
    advice, imperative, prediction, or ranking language implying action ("buy", "watch this",
    "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
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

## GOAL

Every screen run — reused, cancelled, failed, or freshly computed — leaves a durable, honest
record on `/desk`'s new "Screen Runs" section, and a duplicate Run Screen click on unchanged inputs
short-circuits to that already-recorded answer instead of paying for a ~101-symbol recompute.

## BACKGROUND

The prior iteration (28) reached `GOAL_ACHIEVED` on all 17 existing journeys and awaited the
second-key confirm; before that confirm landed, the goal-proposer promoted a genuinely new journey,
**J-18**, into `docs/goal.md`'s `AUTO:journeys` block (score 0.86; `state/proposer-result.json`).
Per the priority rubric, J-18 is the only failing/new journey in the session, so it is this
iteration's sole target (rule 3/4 — it is also the smallest available unit of new scope, since
every other journey is already `passing`).

The dispatch prompt's binding depth recommendation for this iteration is `evidence`, computed from
iteration 28's own "halt, confirm the finish" verdict — before the proposer's promotion. This is
the exact situation iteration 26 faced for J-17: a brand-new, never-implemented, full-stack journey
with real Data-Contract additions is the depth-binding rule's own fourth escape condition, so this
spec overrides `evidence` to `full` (metadata trigger 1, cited above). An `evidence`-depth run
dispatches no developer, and per the iter-28 lesson, `Depth: evidence` also cannot provision the
fixture-scoped rig a populated-ledger walkthrough needs — both are additional reasons `full` is
required here, on top of the escape condition itself.

Proposer rationale (verbatim measurement, `state/proposer-result.json`): `.data/screen` holds 11
recorded snapshots and every one carries only `{id, screen_date, as_of, universe_snapshot_id,
config_fingerprint, bar_store_signature, created_utc, rows, skipped}` — no start time, duration,
members-attempted count, or terminal state — while its two lesser siblings (`.data/topup_runs`,
`.data/index_reconcile_runs`) each keep a durable ledger with exactly that kind of detail. The
desk's central compute (the screen) is the only one whose runs vanish. Separately, `/desk`'s Run
Screen always submits today's UTC date, and `trigger` ALWAYS runs the full member walk rather than
pre-checking the store first — `desk_screen_compute.py`'s own docstring already names the fix
("a future iteration can add a cheap pre-check ... the same way `members_total` already does"), and
`compute_bar_store_signature` / `find_by_key` (the exact accessors needed) already exist.

**Lessons applied (per `lessons.md`, directly relevant to this iteration's depth and evidence
plan):**
- iter-24/26: a `[NEW]`-flagged walkthrough conjunct is structurally unreachable at `lean` — this
  spec is `full`, so the demo-narrator lane runs inside this iteration, before scoring.
- iter-27: the browser-qa lane's fixture-scoped rig tears itself down when it finishes, and a
  demo-narrator run against a torn-down rig records the ambient page's empty state instead. This
  iteration's rig MUST stay alive until the demo-narrator step has finished.
- iter-28: `demo-phase.sh:316` always passes `--base-url "$FRONTEND_URL"` to `demo_runner.py`,
  which beats the script's own authored `base_url` field (`demo_runner.py:1292`). A script-level
  `base_url` cannot be relied on to point the film at a scoped rig — the iteration's evidence plan
  must instead point `$FRONTEND_URL` itself at the scoped rig for the whole evidence phase (dev
  through demo-narrator), never at the ambient `:3301` pair, and must not tear that rig down until
  the demo step completes.
- iter-25: never script a `click` on a cell inside a `/desk` ranked or skipped row (the stretched
  `absolute inset-0` drill-in anchor intercepts it) — irrelevant to the new Screen Runs section
  itself (which carries no such anchor), but any script step that also touches the ranked table
  must stay `expect`-only.
- iter-26 (framework, `test_desk_topup_compute.py:1092`): if a genuine existing-assertion conflict
  surfaces the way J-17's build hit one, disclose it in the dev handoff rather than silently edit
  it — do not repeat that pattern without disclosure.

## IN SCOPE

### Backend

- [ ] New module `app/research/desk_screen_log.py` (name at build discretion) mirroring
      `desk_topup_log.py`'s discipline verbatim: checksum-verified append-only run records, a
      single writer function (e.g. `record_screen_run`), no update/delete path anywhere, storage
      dir a bare env-var-or-sibling-of-`desk_universe_dir_resolved()` default (the
      `resolve_desk_topup_log_dir` pattern) — deliberately NOT a new `Config` field.
- [ ] Inside the ONE shared entry point both callers already use
      (`run_screen_and_record`, `desk_screen_compute.py:73`): resolve the five pins BEFORE the
      walk using ONLY existing accessors (`desk_screen.screen_as_of`, `UniverseStore.list()`'s
      latest record id, `Config.config_fingerprint()`, `desk_screen.compute_bar_store_signature`
      over `desk_coverage`) — no new derivation of any pin. On a `ScreenStore.find_by_key` hit,
      short-circuit to the existing snapshot with `reused=True` immediately (zero
      `compute_tradability` calls, no `BarStore` read beyond the index-only coverage read the pin
      resolution already makes). On a miss, run the full walk exactly as today.
- [ ] Write ONE run record per run, EXACTLY ONCE at terminal state, from a SINGLE shared writer
      both `DeskScreenComputeManager`'s resolve path (`desk_screen_compute.py`) and the CLI's
      `main()` call — never two write paths. Recorded fields: run id, `screen_date`, the five pins
      as resolved (each honestly `null` when the run failed before resolving it), started/finished
      UTC, terminal state (`done`/`cancelled`/`failed`), `reused`, `members_total`,
      `members_attempted`, ranked/skip-by-reason counts, the resulting `screen_id` (or `null`), and
      — on `failed` — the exception detail verbatim plus the member the walk was on when it raised.
      A process that ends before the terminal write leaves NO record.
- [ ] New route `GET /research/desk/screen/runs` in `desk_routes.py`: honest-empty
      `{"runs": [], "latest": null}` at HTTP 200 before any run; a lightweight `runs` meta list plus
      a full `latest` record; `integrity_errors` in the same key/shape its three sibling desk GETs
      already use (the J-12 convention).
- [ ] Confirm `get_endpoint`'s existing `/research/` allowlist already reaches the new path with
      zero code change; add no MCP tool — the suite still proves exactly 17 tools.
- [ ] Zero diff to `desk_screen.py`'s recorded snapshot/row/skip shapes, rank order, or five-pin
      key, and zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
      `desk_coverage.py`/`desk_topup_log.py`/`StructureChart.tsx`.
- [ ] Zero new `Config` field; `Config().config_fingerprint()` stays `08e471b10130e1e2`.

### Frontend

- [ ] New read-only "Screen Runs" section on `/desk`, beside the shipped Screen History, Top-up
      Runs and Index Reconciliation sections (the same table-plus-latest-detail pattern, no
      recompute, NO new control): each run's date + id, terminal state, members
      attempted-of-total, ranked/skipped counts, its own recorded start→finish elapsed, and the
      produced snapshot id — or the honest "reused `<id>` — no walk was performed" and "nothing
      recorded" states — with the latest run's failure detail rendered verbatim when it failed, and
      the section's own `integrity_errors` line.
- [ ] No new ranked-table column and no change to the ranked table — J-16's measured width
      contract and every stored golden replay script must stay untouched.
- [ ] Copy discipline: descriptive measurement only (what a run attempted and produced) — no
      advice, imperative, urgency, prediction, or saving/waste/efficiency/speed claim;
      `tests/test_copy_discipline.py` stays green unmodified.

### New user-facing capability

The operator can see, for every screen run that was ever attempted — including ones that reused an
already-recorded snapshot, were cancelled, or failed — a durable record of what happened and how
long it took. A duplicate Run Screen click on unchanged inputs no longer pays for a full member
walk before being told "already recorded".

### New information displayed

Per screen run: date + id, terminal state (done/cancelled/failed), members attempted-of-total,
ranked/skipped-by-reason counts, elapsed time, produced snapshot id (or the honest reused/no-walk/
nothing-recorded states), verbatim failure detail on failure, and an `integrity_errors` line.

### New user actions

None new — this is a read-only section. The existing Run Screen button's behavior on a duplicate
trigger becomes cheaper (reuse short-circuit) but is not a new control.

### UI surface changes

`/desk` gains a fourth ledger section, "Screen Runs", beside Screen History / Top-up Runs / Index
Reconciliation. No new page, no nav-skeleton change.

### Product surface delta

The desk's honesty machinery now covers all three desk compute types (top-up, index-reconcile,
screen) instead of two; the screen's central compute is no longer the one whose runs vanish on
restart or supersession.

### Blueprint conformance

Lives under the existing **Desk** Information-Architecture home (`/desk`), beside the
already-registered Screen History / Top-up Runs / Index Reconciliation sections. No nav-skeleton
change. `runs/goal-session-desk/state/blueprint.md` has been updated additively: a new J-18 row in
"Feature / journey homes", a new "Screen run records (per-run outcome ledger)" row in the Data
Contract's "New rows this era" table, and a "RESOLVED at iter-29" build-time-scope note.

### Data-contract additions

**Screen run records (per-run outcome ledger)** — NEW.
- Owner (single module): new `app/research/desk_screen_log.py` (name at build discretion).
- Serving endpoint (single, single-home): `GET /research/desk/screen/runs`.
- Fields per record: `id: str`, `screen_date: str`, `universe_snapshot_id: str | null`,
  `config_fingerprint: str`, `bar_store_signature: str | null` (each pin honestly `null` if the run
  failed before resolving it), `started_utc: str`, `finished_utc: str`, `state: "done" |
  "cancelled" | "failed"`, `reused: bool`, `members_total: int >= 0`, `members_attempted: int >=
  0`, `ranked_count: int >= 0`, `skipped_by_reason: {"no_bars": int >= 0, "no_basis": int >= 0}`,
  `screen_id: str | null`, `error: str | null` (verbatim exception detail, `failed` only),
  `failed_member: str | null` (the member the walk was on when it raised, `failed` only).
- List/latest shape: `{"runs": [<lightweight meta only — no ranked/skipped breakdown>, ...],
  "latest": <same fields PLUS ranked_count/skipped_by_reason/error/failed_member> | null}` —
  honest-empty `{"runs": [], "latest": null}` at HTTP 200 before any run; `integrity_errors` in the
  same key/shape its three sibling desk GETs already use.
- Every pin is resolved through the accessor that already owns it (`desk_screen.screen_as_of`,
  `UniverseStore.list()`, `Config.config_fingerprint()`, `compute_bar_store_signature` over
  `desk_coverage`) — never a second derivation; this is the SSOT criterion the acceptance stands on
  in place of a PnL-ledger append (which this era's Non-Goals forbid).

## OUT OF SCOPE

- No change to `desk_screen.py`'s recorded snapshot/row/skip shapes, rank order, or five-pin key.
- No new ranked-table column, no `/structure` change, no engine/chart change.
- No new MCP tool, no scheduler/cron/auto-refresh, no fingerprint epoch bump, no new Config field.
- No PnL-ledger append — the SSOT criterion above stands in its place, per goal.md's own J-18
  acceptance text.
- Do not edit the existing assertions in `test_desk_screen_compute.py` or `test_desk_screen.py` —
  in particular `test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`,
  `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot`, and
  `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite` must
  pass unmodified. If a genuine conflict surfaces (the J-17 precedent at
  `test_desk_topup_compute.py:1092`), disclose it verbatim in the dev handoff rather than edit
  silently.
- No per-member error-skip-row invention — `compute_screen`'s member loop keeps its shipped
  semantics; this journey makes the outcome legible, it does not alter it.

## DEFINITION OF DONE

- [ ] J-18 passes via browser-qa-agent (TC-10, TC-11, TC-12) at a 1440x900 viewport, no horizontal
      scroll, after a `rm -rf apps/frontend/.next` clean rebuild (T-9).
- [ ] Required-still-passing journeys (J-03, J-04, J-05, J-06, J-07, J-09, J-10, J-12, J-16, J-17)
      remain green via deterministic replay + LLM fallback.
- [ ] No anti-goal violation introduced — SSOT, append-only/pinned snapshots, explicit-operator-act,
      copy-discipline, keyless/hermetic suite, fingerprint-pin, and enhancement-loop-box rails all
      hold.
- [ ] Unit tests pass; zero regressions; the three named existing tests
      (`test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`,
      `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot`,
      `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`)
      pass unmodified.
- [ ] `Config().config_fingerprint()` still prints `08e471b10130e1e2`; zero new `Config` fields;
      MCP tool count exactly 17.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough is attempted over a populated fixture-scoped
      ledger (TC-13), with the scoped rig kept alive and `$FRONTEND_URL` pointed at it through the
      demo step — if it still fails for reasons outside product code, disclose that honestly per
      methodology A.7 rather than block the verdict on it (this is J-18's FIRST capture attempt,
      not a repeat of J-17's three-strikes history).
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-29-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-18 (TC-10, TC-11, TC-12, TC-13). Regression smoke via deterministic replay: J-03,
  J-04, J-05, J-06, J-07, J-09, J-10, J-12, J-16, J-17.
- Unit/integration: TC-1 through TC-9, TC-14, TC-15.
- Error cases: TC-5 (cancelled run), TC-6 (raising member), TC-7 (process death before terminal
  write) — none of these may write a snapshot or fabricate a ledger entry.

- TC-1: given no screen run has ever been recorded in a fixture-scoped store, when
  `GET /research/desk/screen/runs` is requested, then it returns HTTP 200 with body
  `{"runs": [], "latest": null}`.
- TC-2: given a fixture-scoped universe + bar store with no prior screen snapshot for a pin set
  (screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature), when a
  screen is triggered via `POST /research/desk/screen/compute` and runs to completion, then
  `GET /research/desk/screen/runs` returns exactly one record whose `members_total`/
  `members_attempted`, ranked count, skip-by-reason counts, five pins and `screen_id` are
  byte-identical to the snapshot recorded at `GET /research/desk/screen?date=<that date>`.
- TC-3: given that same run's five pins are already recorded, when the screen is re-triggered
  under identical pins, then the run record shows `reused: true`, `members_attempted: 0`, the test
  asserts zero `compute_tradability` calls were made, the returned `screen_id` equals the prior
  run's `screen_id`, and no second file is written under `.data/screen`.
- TC-4: given a trigger whose pins MISS (a different `screen_date`), when the screen compute walks
  every member, then the recorded snapshot's rows and rank order are byte-identical to what those
  same pins produce today (golden comparison), and the new run record shows `reused: false` with
  `members_attempted == members_total`.
- TC-5: given a running screen compute job, when the operator cancels it before the walk
  completes, then the run record shows terminal state `"cancelled"`, `members_attempted <
  members_total`, `screen_id: null`, and no snapshot file is written.
- TC-6: given a member whose `_resolve_reference_close_and_history` raises during the walk, when
  the screen compute encounters that raise, then the run record shows terminal state `"failed"`
  with the exception detail verbatim and the raising member's own name recorded, and no snapshot
  file is written.
- TC-7: given a process that ends before the run's terminal write (simulated by never invoking the
  writer in a unit test), when `GET /research/desk/screen/runs` is queried, then the ledger
  contains no entry for that run.
- TC-8: given two completed runs recorded in sequence, when the second run is recorded, then the
  first run's record file remains byte-identical on disk (checksum unchanged) and
  `GET /research/desk/screen/runs`'s `runs` list carries both runs' lightweight meta.
- TC-9: given the three named pre-existing tests
  (`test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`,
  `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot`,
  `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`), when
  the pre-check + run-log changes land, then all three pass with zero edits to their assertions.
- TC-10: given a fixture-scoped rig with zero screen runs recorded, when `/desk` is loaded at
  1440x900 after the T-9 clean rebuild, then the Screen Runs section renders the honest "nothing
  recorded" empty state in one screenshot, with no horizontal scroll and the ranked table unchanged
  from J-16's shipped layout.
- TC-11: given a fixture-scoped rig with one completed screen run recorded, when `/desk` is loaded,
  then the Screen Runs section shows that run's date + id, terminal state, members
  attempted-of-total, ranked/skipped counts, elapsed time, and produced snapshot id, all legible in
  one screenshot at 1440x900 with no horizontal scroll.
- TC-12: given a fixture-scoped rig with a `reused` run recorded (an identical-pin re-trigger),
  when `/desk` is loaded, then that run's own row states honestly that no walk was performed,
  legible in a dedicated screenshot.
- TC-13: given the fixture-scoped rig stays running through the demo-narrator step (`$FRONTEND_URL`
  pointed at the scoped rig's own frontend port for the whole evidence phase, not torn down until
  after this step), when the `[NEW]`-flagged walkthrough is recorded, then its frames show the
  Screen Runs section's populated state (attempted-of-total, ranked/skipped counts, elapsed,
  produced snapshot id) with distinct (non-duplicate) frame checksums — verified via `md5sum
  reports/demo/goal-desk-iter-29/*.png`.
- TC-14: given the full backend suite after this iteration's changes, when it runs, then
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`, zero new `Config` fields exist,
  the MCP tool count is exactly 17, and the suite passes with zero regressions (baseline: 1,474
  passed / 8 skipped, exit 0, or higher).
- TC-15: given the owner's real `apps/backend/.data` directory, when this iteration's build and
  tests run, then no file under it is created, changed, or removed except new rebuildable
  index/log files this journey's own new storage dir explicitly adds — verified by a before/after
  file listing (759 price files / 1 universe record / 11 screens / 1 top-up record, or whatever
  the current live counts are, unchanged).

## NOTES

- This is J-18's FIRST attempt at its `[NEW]`-flagged walkthrough — unlike J-17 (which reached a
  disclosed, evaluator-accepted "clear as owner-optional" outcome after three tries), there is no
  standing bound against retrying this one if the first attempt fails for a fixable reason. Do
  apply the harness lessons proactively rather than repeating them: keep the fixture-scoped rig's
  backend AND frontend both up through the demo-narrator step, and set `$FRONTEND_URL` itself
  (not just the demo script's own `base_url` field, which the CLI silently overrides per the
  iter-28 lesson) to the scoped rig's frontend address for the whole evidence phase.
  `scripts/automation/demo-phase.sh:316` / `scripts/automation/lib/demo_runner.py:1292` are
  framework files, not in scope for this product iteration to edit — work around the bug at the
  environment-variable level instead.
  - No native-browser-UI screenshot is required by J-18 (no `title` tooltip acceptance clause), so
    the T-10a headed rig is not needed this iteration.
  - The recorded reused/cancelled/failed states for TC-11/12/13 should be planted into a fresh
    fixture-scoped copy of `.data/` (never the ambient store) via the existing
    `desk_screen_compute` CLI/POST path — the iter-9/11/14/15/17/19/20/21 scoped-rig lesson.
  - Building the fixture states in a deterministic order matters (iter-12's capture-order lesson):
    boot both backend and frontend against the scoped root BEFORE recording any run, so the honest
    "nothing recorded" empty state can be captured live, then record the checkpoint runs, then
    capture the populated states — all on the same still-live rig.
