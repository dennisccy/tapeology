# Goal Iteration 7 — The back-scan (J-07): resumable, append-only, host-guard-confined

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Full trigger:** 4 — brand-new full-stack journey: J-07 needs a new backend module
  (`desk_playbook_backscan.py`, three new routes) AND a new `/desk` frontend panel, with three
  real Data-Contract additions for a target journey that has never been implemented before
  (matches the evaluator's own binding `full` recommendation for this iteration; iter-6's
  `budget-breached` marker exists, but the escape condition here does not rely on the prior
  verdict being `ESCALATE` — trigger 4 stands on its own).
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-10
- **Anti-goal reminders:**
  - No execution path, ever — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. *(critical)*
  - No profit claims and no advice — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them,
    never a mutation of them. *(critical)*
  - Hold-out-only promotion — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins
    are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
    feeds/fingerprints to manufacture a survivor. *(critical)*
  - No lookahead — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint,
    and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations.
    *(critical)*
  - Deterministic and seeded — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP
    surface can change state. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - Persistence stays scoped — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - No threshold exists outside the spec, and no code path sweeps one. Every detector rule and
    threshold exists in `docs/playbook-detector-spec.md` BEFORE the code that uses it; no code
    path iterates thresholds against outcomes (source-scan guard-tested); a threshold change is a
    spec revision + new signature, never an edit of recorded signals and never a sweep.
    *(critical)*
  - A signal is an observation, not a call. No signal, chip, or evidence cell uses advice,
    imperative, prediction, probability, expectancy, edge, or significance language; the served
    registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
    `invalidation_price` is geometry, never an order concept. *(critical)*
  - No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1. New
    signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*
  - No second implementation of the measurement rail. Measurement helpers are imported from
    `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
    MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*
  - Host-guard caps are law. Never disable, widen, or bypass the host confinement to make a run
    faster or a pause go away. *(critical)*

## GOAL

The operator can preview, over a From/To date range, which recorded trading sessions already
carry a playbook record at the current signature versus which are missing, trigger one resumable,
cancel-safe back-scan compute that walks every planned date through the existing playbook pipeline
and writes one append-only record per date, and review a runs table of what every scan attempt
actually did.

## BACKGROUND

The iter-6 evaluator named J-07 as the explicit next build and required the auditor on it — "the
first piece of work that writes many records into the owner's own store at once", after the same
iteration's test lane accidentally wrote an unscoped real-universe compute into the operator's
store. Trigger 4 (brand-new full-stack journey) independently justifies `full` depth here: J-07
needs a new backend module, three new routes, and a new `/desk` panel with real Data-Contract
additions, and this matches the evaluator's own binding recommendation for this iteration
(dispatch line: "Evaluator depth recommendation … full — BINDING by default"). Two cheap
passenger items ride along per the same evaluator's explicit request: the missing short-side
mirror test for `range_trade`'s degenerate-trigger fail-closed clause (iter-6 shipped only the
long-side test), and a re-take of the Range Trade row screenshot on a freshly rebuilt page.

Lessons applied from this session's ledger: scope ALL FOUR playbook env vars
(`TAPEOLOGY_DESK_PLAYBOOK_DIR`, `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`,
`TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR`, `TAPEOLOGY_DESK_UNIVERSE_DIR`) for every test/browser
run this iteration — the iter-6 lesson showed that reading `config.*_dir` directly instead of the
`*_resolved()` accessor, or scoping the store dir without its log-dir sibling, silently orphans
writes into the real store (iter-6 lesson, "Store scoping fails in two silent ways"). The
`/desk` page is now too tall for a full-page headless capture; the working technique
(`display:none` sibling `<section>`s for the capture only) applies again to the new Backscan
panel. New golden-replay assertions must target the new section's own static shell strings, never
reuse a shipped `data-testid`/heading (T-11).

## IN SCOPE

### Backend

- [ ] Build `app/research/desk_playbook_backscan.py`: `plan_backscan(from_day, to_day, ...)` —
  pure, metadata-only (one `playbook_input_signature` resolution per call, zero bar reads),
  classifying every recorded session date in range as `recorded_at_current_signature` or
  `missing_at_current_signature`.
- [ ] Same module: the compute trio (`DeskPlaybookBackscanComputeManager`, single-flight, mirrors
  `DeskPlaybookComputeManager`/`DeskDeepBackfillComputeManager`) + `run_backscan`, walking every
  planned date through the ONE existing shared `run_playbook_and_record`
  (`desk_playbook_compute.py:90`) — never a second implementation of that entry point. Per-date
  outcome is one of `reused` / `recorded` / `refused_non_session` / `failed`; cancel is
  cooperative, observed on a date boundary.
- [ ] `resolve_desk_playbook_backscan_log_dir` + a terminal-state-only `BackscanRunStore` (mirrors
  `PlaybookRunStore`/`desk_topup_log.py`), rooted at the `TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR`
  env var (already anticipated by `qa_playbook_iter6_fixture_scoped_backend.sh`) — zero new
  `Config` field.
- [ ] Wire three routes in `desk_routes.py`: `GET /research/desk/playbook/backscan/plan`,
  `POST` / `GET` / `POST .../cancel` on `/research/desk/playbook/backscan/compute`, and
  `GET /research/desk/playbook/backscan/runs`. Page-load GETs trigger nothing (T-7).
- [ ] Host-guard-confine the back-scan walker exactly as every other heavy desk path (T-12).
- [ ] Add the short-side mirror of
  `test_range_trade_degenerate_trigger_reference_below_the_range_low_fails_closed`
  (`apps/backend/tests/test_desk_playbook_detect.py:1249`) — the `T >= SH` short-side case, with
  its own relaxed-gate control. Test-only; zero detector code change expected (the fail-closed
  clause already ships symmetrically per the iter-6 audit).
- [ ] Add a positive scoping guard: a `_assert_scoped()`-style helper (or equivalent test-lane
  check) that refuses to let a playbook or back-scan compute proceed when any of the four
  scoping env vars is unset or points at the ambient default, exercised by a dedicated test.
  Extend (or supersede with an iter-7 variant of) `qa_playbook_iter6_fixture_scoped_backend.sh`
  so it seeds **two or more** additional recorded session dates (on top of the existing
  2026-06-22 fixture) and becomes the ONLY backend entry point for every test/browser run this
  iteration.

### Frontend

- [ ] Add a new `<section aria-label="Backscan">` panel to `/desk`, rendered directly below the
  existing "Playbook Signals" section (`apps/frontend/app/desk/page.tsx:6714`, before `</main>`):
  From/To date inputs + a plan preview (per-date status + totals), a Run Backscan control with
  live progress (current date, running per-outcome counts) + Cancel, and a runs table (one row
  per completed/cancelled/errored run with its per-outcome counts). No client-side arithmetic on
  served numerics — reuse the existing `fmt()` pattern and extend `_PRICE_ARITHMETIC_FIELDS`
  (`apps/backend/tests/test_desk_ui_guards.py:186`) for any new served numeric the panel renders.
- [ ] Re-take the Range Trade row screenshot (owed from iter-6) on the freshly rebuilt scoped rig,
  captured in the SAME clean-rebuilt browser pass as the new Backscan evidence (T-9).

### New user-facing capability

The operator can bulk-check and bulk-populate the playbook ledger across many recorded sessions in
one resumable act, instead of computing one date at a time via the existing Run Playbook control.

### New information displayed

Back-scan plan preview (per-date status, total planned, count missing); live back-scan progress
(current date being walked, running counts per outcome); a back-scan runs table (date range,
terminal status, per-outcome counts, timestamps) — all served verbatim, no client computation.

### New user actions

Enter a From/To date range and preview the plan; click "Run Backscan" to trigger the resumable
compute; click "Cancel" to cooperatively stop mid-scan; scroll the runs table to review past scans.

### UI surface changes

One new panel (`<section aria-label="Backscan">`) added to the existing `/desk` route, directly
below the shipped "Playbook Signals" section. No new route, no nav change.

### Product surface delta

`/desk` gains its second Era B2 panel below the shipped sections; the operator moves from
per-date manual computes to a single bulk, resumable back-scan over a date range.

### Blueprint conformance

Lands under the existing **Desk** home in `runs/goal-session-playbook/state/blueprint.md`'s
Information Architecture, in the pre-planned "Backscan" slot ("plan preview + trigger + live
progress + cancel + runs table (J-07, not yet built)") — no nav-skeleton change.

### Data-contract additions

Two new desk-owned values (both already pre-registered as target rows in
`runs/goal-session-playbook/state/blueprint.md`'s Data Contract; this iteration ships them and the
blueprint's "Ships at" column is updated accordingly):

- `backscan_plan`: `{from: str (yyyy-MM-dd), to: str (yyyy-MM-dd), playbook_input_signature: str,
  dates: [{session_date: str, status: "recorded_at_current_signature" |
  "missing_at_current_signature"}], total: int >= 0, missing: int >= 0}`. Owner:
  `app/research/desk_playbook_backscan.py::plan_backscan` (pure, metadata-only). Endpoint:
  `GET /research/desk/playbook/backscan/plan`.
- `backscan_compute` (progress) + `backscan_runs` (ledger), same owner module
  (`desk_playbook_backscan.py`, single-flight manager + `BackscanRunStore`). Progress snapshot:
  `{status: "idle"|"running"|"done"|"cancelled"|"error", from: str|null, to: str|null,
  planned_total: int, completed: int, outcomes: {reused: int, recorded: int,
  refused_non_session: int, failed: int}, current_date: str|null, error: str|null}`. Ledger row:
  `{run_id: str, from: str, to: str, started_at: str, finished_at: str, status:
  "done"|"cancelled"|"error", outcomes: {reused: int, recorded: int, refused_non_session: int,
  failed: int}}`, honest-empty `{runs: []}` before any run. Endpoints:
  `POST/GET/POST-cancel /research/desk/playbook/backscan/compute`,
  `GET /research/desk/playbook/backscan/runs`.

Both rows read the ALREADY-registered "Playbook records" row's own store/signature verbatim
(via `run_playbook_and_record`) — no second implementation of playbook detection, measurement, or
storage.

## OUT OF SCOPE

- J-08 (evidence view) and J-09 (MCP contract v4) — not targeted this iteration.
- The REAL back-scan over the operator's full recorded-session store. Per J-07's own acceptance
  text this is "an operator-run act … reported run-or-not-run", not a mechanically-gated
  passing condition — this iteration's passing bar is the fixture-scoped keyless core plus one
  fixture-scoped browser-verified scan.
- Any change to `range_trade` / `double_top` / `double_bottom` detection logic, or the four open
  owner rulings carried in iteration-state (the §3.7 degenerate-trigger clarification,
  `crossed_midrange`'s partial disclosure, `double_top`'s first-pair-vs-first-break choice, the
  1.5x jump-to-base gate, the cup rim constant) — untouched this iteration, awaiting the owner.
- Any diff to `desk_forward.py`, `desk_playbook_features.py`, `desk_playbook_detect.py` (beyond
  the one new short-side test), `mcp/__init__.py`, `config.py`, `levels.py`, `bars.py`,
  `setups.py` — zero diff maintained (session "Do not redo" list); MCP stays 18 tools; pin stays
  `08e471b10130e1e2`.
- J-10's "20 Claude tools" wording gap — stays `partial` until J-09 ships; not addressed here.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa-agent (fixture-scoped plan preview + a completed run row with
  per-outcome counts, screenshot)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06, J-10 remain green
  (deterministic replay + LLM fallback — mechanically verified)
- [ ] No anti-goal violation introduced — no test/browser/QA run writes into the operator's real
  `.data/playbook*` store; every run uses the scoped-only backend entry point
- [ ] Unit tests pass; no regressions (suite count at or above the iter-6 floor: 2105 passed / 8
  skipped; `Config().config_fingerprint()` still prints `08e471b10130e1e2`)
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-7-dev.md`
- [ ] Short-side degenerate mirror test for `range_trade`'s fail-closed clause added and green
- [ ] Range Trade row re-capture screenshot delivered on a freshly rebuilt page (evidence make-up
  owed from iter-6)
- [ ] `_assert_scoped`-style guard test added, positively proving an unscoped compute attempt is
  refused before it reaches the real store

## TESTING REQUIREMENTS

- Browser: J-07 (Backscan panel — plan preview + triggered fixture scan + runs table,
  screenshot); required-still-passing replay for J-01, J-02, J-03, J-04, J-05, J-06, J-10.
- Unit/integration: plan purity (stub-store-that-raises test proving zero bar reads), resumability
  (zero detector-call-count on a re-run of already-recorded dates), cancel-then-resume, a
  threshold monkeypatch flipping every planned date to `missing_at_current_signature`, honest
  `refused_non_session` classification, terminal-state-only ledger writes, SHA-256 byte-identity
  of every previously recorded file across a re-run, the short-side degenerate mirror test, the
  `_assert_scoped` guard.
- Error cases: an inverted `from > to` range; a session date with zero recorded 5m bars for any
  member inside the requested range; a corrupt existing playbook file sitting at a planned date's
  store key.

Test-first contract:

- TC-1: given a fixture-scoped backend with 3 recorded session dates and none yet recorded in the
  playbook store, when `GET /research/desk/playbook/backscan/plan?from=<d0>&to=<d2>` is called,
  then the response lists exactly 3 entries all with `status: "missing_at_current_signature"` and
  `missing == 3`.
- TC-2: given the same fixture, when `POST /research/desk/playbook/backscan/compute` runs to
  completion, then the playbook store contains one recorded record for each of the 3 dates and
  the compute snapshot shows `outcomes.recorded == 3`.
- TC-3: given the 3 dates already recorded by TC-2, when the plan is requested again for the same
  range, then every entry's status is `"recorded_at_current_signature"` and `missing == 0`.
- TC-4: given the same 3 already-recorded dates, when a second back-scan run walks the same range,
  then the compute snapshot shows `outcomes.reused == 3` and a call-counting stub on the
  detector/measurement layer records zero calls for those 3 dates.
- TC-5: given a back-scan run cancelled after 1 of 3 planned dates completes, when
  `GET /research/desk/playbook/backscan/runs` is queried, then the ledger row for that run shows
  `status == "cancelled"` and `outcomes.recorded == 1`, and a fresh plan GET shows that 1 date as
  `"recorded_at_current_signature"` and the other 2 as `"missing_at_current_signature"`.
- TC-6: given the cancelled run of TC-5, when the back-scan is re-triggered over the same range,
  then the previously-recorded date is reported `reused` and the run completes with
  `outcomes.recorded == 2` and `outcomes.reused == 1`.
- TC-7: given a `PLAYBOOK_*` threshold constant monkeypatched to a different value inside a test,
  when the plan is requested again for the same 3 already-recorded dates, then every entry's
  status flips to `"missing_at_current_signature"`.
- TC-8: given a session date in range with zero recorded 5m bars for any member, when the
  back-scan walks that date, then its outcome is `refused_non_session` and no playbook file is
  written for it.
- TC-9: given `GET /research/desk/playbook/backscan/plan` is called against a stub `BarStore` that
  raises `AssertionError` on every bar-read method, when the request is made, then it returns
  HTTP 200 with a populated `dates` list, proving the plan performs zero bar reads.
- TC-10: given a back-scan run cancelled before any date completes, when
  `GET /research/desk/playbook/backscan/runs` is queried, then no row exists for that run (the
  ledger stays honestly empty — terminal-state-only write).
- TC-11: given the fixture-scoped rig (started via the iter-7 scoped backend script, seeded with
  2 or more recorded session dates), when the browser opens `/desk`'s Backscan panel, previews a
  From/To range, and triggers the scan to completion, then a screenshot shows the plan preview
  counts and the completed run's row with all four per-outcome counts (`reused`, `recorded`,
  `refused_non_session`, `failed`) legible.
- TC-12: given `detect_range_trade`'s SHORT-side degenerate trigger reference (`T >= SH`, mirroring
  the existing long-side fixture at `test_desk_playbook_detect.py:1249`), when detection runs on
  the degenerate fixture, then it returns an empty list; when the same bars are run with the
  reference low raised above `SH` (the control), then exactly one short signal is returned.
- TC-13: given all four playbook scoping env vars unset (or pointing at the ambient default), when
  `_assert_scoped()` is called before a playbook or back-scan compute is triggered, then it raises
  before any compute reaches the real store.
- TC-14 (evidence make-up, passenger, non-blocking): given the post-fix range-trade detector on a
  freshly rebuilt `/desk` page, when the Range Trade signal row is expanded, then the screenshot
  shows its full geometry line ("range … MBR wide · low zone touches … · high zone touches … ·
  broke at slot … · crossed midrange") legible in the same image as at least one other setup row.
- TC-15: given the full backend suite, when it is run to completion, then it exits 0 with a pass
  count at or above 2105 (8 skipped), and `Config().config_fingerprint()` prints
  `08e471b10130e1e2`.
- TC-16: given `tests/test_mcp_server.py` runs this iteration, when it executes, then it still
  asserts exactly 18 tools (unchanged — J-09 is not targeted).
- TC-17: given an inverted range (`from > to`), when
  `GET /research/desk/playbook/backscan/plan?from=<to>&to=<from>` is called, then the response is
  HTTP 200 with `dates: []` and `total == 0` (honest empty, no error — matching the existing
  `GET /research/desk/sessions` fail-open range-filter convention).

## NOTES

- Iter-6's `budget-breached` marker means the engine's own arbiter may still demote this spec to
  `lean` regardless of the `Full trigger: 4` justification recorded here (the session's iter-5
  lesson: the SPEED-20 arbiter reliably grants `full` only after a prior `ESCALATE`, not merely a
  registered trigger) — that is an engine-level guardrail outside this spec's control; if demoted,
  the auditor's absence should be flagged again in the resulting eval.
- Owner rulings (a)-(d) carried in iteration-state remain open and are explicitly untouched by
  this iteration — J-07 orchestrates the EXISTING `run_playbook_and_record` entry point and never
  re-derives detector logic.
- The zero-structural-calls guard (`compute_playbook` never calls `compute_tradability`/
  `compute_levels`) and the no-threshold-sweep guard already cover the back-scan's own call path
  transitively (it calls `run_playbook_and_record`, which calls `compute_playbook`) — no new
  source-scan guard is needed for those two properties, only the new scoping guard (TC-13) and the
  short-side mirror (TC-12).
- Capture technique: hide sibling `<section>`s above the Backscan panel via `eval` for the
  duration of the screenshot only (iter-3 lesson) — the underlying DOM is fully rendered either
  way, so every functional assertion still runs against the complete page.
