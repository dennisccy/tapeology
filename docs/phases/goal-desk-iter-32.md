# Goal Iteration 32 — Top-up runs disclose the library reach each pair actually holds after the walk

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 32
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: a brand-new, never-before-built full-stack journey
  (compute-layer field + `/desk` UI disclosure + a first-ever `[NEW]`-flagged demo-narrator
  walkthrough) spanning `desk_topup_compute.py`'s shared walker, the Top-up Runs render, and a new
  Data-Contract field, with no existing single journey's own test coverage spanning that blast
  radius; invoked via the binding depth recommendation's own "brand-new full-stack journey" escape
  condition, since the evaluator's `lean` recommendation for this iteration predates the
  goal-proposer's promotion of J-19 this cycle (see `state/assumptions.md` iter-32).
- **Frontend Present:** yes
- **Target journeys:** J-19
- **Required-still-passing journeys:** J-01, J-02, J-04, J-06, J-07, J-09, J-16, J-17, J-18
- **Anti-goal reminders:**
  1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
     trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
     tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
     fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
     imperative trading cues. *(critical)*
  3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
     states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
     surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
     a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk`
     BESIDE the kept two pages — the sanctioned kept-surface edits are J-05's additive `/structure`
     prefill and **R-1**'s price-less-row repair, which changes no output for finite data and leaves
     every recorded series on disk untouched.) *(critical)*
  5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
     *(critical)*
  6. **Single source of truth** — each shared value is computed once, owned by one canonical
     endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
     violations. *(critical)*
  8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
     MCP surface can change state. *(critical)*
  9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never
     re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
     *(critical)*
  10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
      explicit, logged act. *(critical)*
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
    interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
    `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
    engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
    Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening the
    mask follows the verification ladder in `trendora/project-extensions/host-guard/README.md`.
    *(critical)*

## GOAL

After a top-up run, the operator can see — right inside the existing `/desk` Top-up Runs panel —
the actual date each pair's frozen bar history now reaches, not just the window the run asked for.

## BACKGROUND

Iteration 31's GOAL_ACHIEVED verdict was CONFIRM_ACHIEVED by the second key
(`runs/goal-session-desk/iter-31/eval-confirm.md`) with all 18 journeys passing and zero
regressions. The goal-proposer then ran its post-confirm enhancement pass and promoted one new
journey, **J-19** (score 0.86; `state/proposer-result.json`), measured read-only against the desk's
own artifacts: the one recorded real top-up run (`topup-2026-07-29-5de907c83fc4`, 404 pairs)
records each pair's provenance only as it stood BEFORE its own fetch — no artifact anywhere states
what a pair's frozen history reaches once the run ENDS, and the pinned pairs' newest bars in fact
span 2026-07-21..07-28 across timeframes while `bar_index`'s only freshness signal (the window a
run ASKED for) postdates the newest bar actually held on 394 of 395 member×timeframe pairs. Two
sibling proposals (coverage-freshness semantics 0.44; consecutive-screens-identical 0.46) were
correctly left backlogged, not promoted — this iteration builds the one promoted journey only,
following the priority rubric's tie-break (smallest, single, non-bundled scope).

This iteration overrides the engine's binding `lean` depth recommendation to `full`, because that
recommendation predates the promotion and J-19 is a genuinely brand-new full-stack journey
(backend field + frontend disclosure + a first-ever `[NEW]`-flagged walkthrough) — the same
override pattern iterations 15, 17, 23, 24, 26 and 29 used for their own brand-new journeys; full
reasoning logged in `state/assumptions.md` iter-32.

Applicable lessons: (iter-24) do not alter any `expect.text` substring the stored golden replay
scripts `J-09.json`/`J-17.json` assert (`desk-topup-run-latest-counts`,
`desk-topup-run-latest-window-basis`, `desk-topup-run-latest-failed`) — this iteration only ADDS a
new sibling block, it must not touch those three. (iter-27/28) a `[NEW]`-flagged walkthrough must
run against the ambient `:3301`/`:8301` pair whenever the ambient store already carries (or can be
made to carry, by a sanctioned operator act) the state to be narrated — a scoped-rig teardown race
or a dead `base_url` override are the two failure modes already burned. (iter-29) an append-only
ledger destroys its own irreplaceable empty state the first time it is exercised — J-19 carries NO
honest-empty-state acceptance clause of its own (unlike J-18), so triggering a fresh, real top-up
run on the ambient store this iteration is safe and does not repeat that mistake; it is also the
most direct way to produce a run with genuinely varied per-pair `store_frozen_through_after` values
(some pairs already caught up, others lagging), which is exactly what TC-10 below needs.
(iter-31(b)) when a field's absence must be distinguished from its legitimate `null` value, verify
which cases actually collapse to the same discriminator before trusting it — TC-2/TC-3/TC-4/TC-5
below cover each outcome branch (`reused`/`unchanged`/`failed`/`fetched`) explicitly so the
`null`-only-when-empty case is not conflated with the equal-to-pre-fetch case.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/research/desk_topup_compute.py` — inside `run_topup` (the per-pair loop,
      currently building the `entry` dict at `:304-313`): immediately AFTER `_run_one_pair` returns
      for a pair, call `_pair_window(bar_store, symbol, timeframe)` a second time (the SAME pure,
      repeat-call-sanctioned accessor J-17 already calls once, pre-fetch, at `:302`) and add
      `entry["store_frozen_through_after"] = window_after["store_frozen_through"]` to that pair's
      outcome dict. Never a new accessor, never a second fetch, never `bar_index`'s
      `window_end_utc`, never a change to `_run_one_pair`'s two-value return signature.
- [ ] Update `run_topup`'s own docstring (and the module docstring's outcome-shape list) to name
      the new field, mirroring how the J-17 addition was documented.
- [ ] Explicitly zero diff: `apps/backend/app/research/desk_topup_log.py` (a pure, generic
      per-entry-dict persister — needs no change to carry one more key), `routes.py`'s
      `record_bar_series`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`,
      `tradability.py`, `levels.py`. No new route, no new `Config` field, no new store, no new MCP
      tool.

### Frontend
- [ ] `apps/frontend/lib/types.ts` — `DeskTopupOutcome` gains `store_frozen_through_after?: string
      | null` (optional/additive, mirrors the existing `store_frozen_through?` field's legacy-run
      absence contract).
- [ ] `apps/frontend/app/desk/page.tsx` — `LatestTopupRunDetail` (`:918-986`) gains one new
      descriptive block, placed beside the existing `desk-topup-run-latest-window-basis` line: a
      plain tally/extreme helper (mirrors `topupWindowBasisCounts`'s shape) that, over
      `run.outcomes`, finds the newest `store_frozen_through_after` date and how many pairs reach
      it, plus a short list of the pairs whose own `store_frozen_through_after` is earlier (or
      `null`) — each list row rendering that pair's `symbol`, `timeframe`, and recorded date
      verbatim. When ANY outcome in the run lacks `store_frozen_through_after` (a legacy run), the
      whole block renders the honest fallback text `"library reach not recorded in this run"`
      instead (the `WINDOW_BASIS_NOT_RECORDED`-pattern precedent) — never computed or backfilled.
- [ ] No new section, no new control, no new column on the ranked briefing table, and no new column
      on the Top-up Runs summary table (`TopupRunsTable`/`TopupRunRow`) — the new content lives
      ONLY inside the already-shipped `desk-topup-run-latest-detail` block. J-16's measured
      `table-fixed` + `<colgroup>` width contract on the ranked table is untouched.

### New user-facing capability
On `/desk`'s existing Top-up Runs panel, after a run, the operator can read the actual date each
pair's frozen history now reaches — not merely the window the run requested.

### New information displayed
One new descriptive line (newest reach date across the run's pairs + how many pairs reach it) and
a short list of pairs whose own recorded reach date is earlier than that newest date (or `null`),
each with symbol, timeframe, and date.

### New user actions
None. Read-only disclosure inside an already-shipped panel — no new button, control, or click
target (matches the J-09/J-17 precedent's explicit "no new control" scope).

### UI surface changes
`/desk`'s existing "Top-up Runs" panel → `LatestTopupRunDetail` gains one new line + one new short
list. No new page, no new section, no nav-skeleton change.

### Product surface delta
An existing panel becomes more honest about what a top-up run actually accomplished, without adding
any new page, control, or navigation.

### Blueprint conformance
Desk nav section, `/desk` canonical home (already registered) — see `state/blueprint.md`'s Feature/
journey-homes table (new J-19 row, "IN BUILD at iter-32") and the "Top-up run records" Data Contract
row's iter-32 addition note (both edited this iteration, purely additive, zero nav-skeleton change
— no `blueprint.reapproval-requested` file needed).

### Data-contract additions
`store_frozen_through_after: string (ISO-8601 UTC, microsecond precision, "Z" suffix) | null` — one
new field, additive to each per-pair outcome entry of the ALREADY-REGISTERED "Top-up run records"
row. Computing module: `desk_topup_compute.run_topup` (via the existing pure `_pair_window`
accessor, called a second time after `_run_one_pair`). Serving endpoint: `GET
/research/desk/topup/runs` (owner `desk_topup_log.py`, unchanged, zero diff). No new Data-Contract
row, no new endpoint. Registered in `state/blueprint.md` BEFORE this build (per the iter-30 lesson:
never write a blueprint entry in the past tense before the code lands — this note is written as
"IN BUILD", not "RESOLVED").

## OUT OF SCOPE

- Coverage-freshness semantics (the backlogged sibling proposal, score 0.44) — not promoted this
  cycle, do not build it.
- Any change to `bar_index`'s `window_end_utc` semantics, or a second coverage path anywhere —
  coverage/freshness keeps its single existing owner, `desk_coverage.py` over `bar_index`.
- A new ranked-table column, a new Top-up Runs summary-table column, a new page, a new nav row, a
  new `Config` field, a new route, a new MCP tool, or a new store.
- Re-verifying J-01..J-18 as an iteration goal beyond the Required-still-passing regression set —
  do not run a capture-only iteration.
- The four owner-optional notes from iter-31 (`B1`/`F1`/`T3`/the demo scroll-anchor gap) — binding
  "Do not redo", explicitly out of scope again this iteration.
- Any diff to `desk_topup_log.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`,
  `tradability.py`, `levels.py`, `StructureChart.tsx`, `mcp/__init__.py`, `config.py`, `engine/` —
  zero diff stays law per the standing iteration-state constraint.

## DEFINITION OF DONE

- [ ] J-19 passes via browser-qa-agent, with a real-browser screenshot at a 1440×900 viewport
      showing both the new reach line and the earlier-pairs list in one frame, no horizontal
      scroll, and the ranked briefing table rendering exactly as J-16 shipped it.
- [ ] Required-still-passing journeys (J-01, J-02, J-04, J-06, J-07, J-09, J-16, J-17, J-18) remain
      green via deterministic golden-script replay where a script exists, LLM browser-qa fallback
      otherwise.
- [ ] No anti-goal violation introduced; the scan report is CLEAN.
- [ ] Full backend suite green, zero regressions; `Config().config_fingerprint()` still prints
      `08e471b10130e1e2`; zero new `Config` fields; the MCP tool list still reads exactly 17 names.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough of the library-reach disclosure is recorded, with
      genuinely distinct frames (unique md5 each) that show their subject in frame.
- [ ] `tests/test_copy_discipline.py` and `tests/test_desk_ui_guards.py` and
      `tests/test_desk_hover_tooltip_guard.py` pass unmodified.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-32-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-19 (target); regression replay for J-01, J-02, J-04, J-06, J-07, J-09, J-16, J-17,
  J-18.
- Unit/integration: `desk_topup_compute.py`'s `run_topup` per-pair `store_frozen_through_after`
  derivation across all four outcome branches (`reused`/`unchanged`/`failed`/`fetched`) plus the
  holds-nothing/`null` case; every EXISTING test in `test_desk_topup_compute.py` and
  `test_desk_topup_log.py` (including the manager-mechanics tests that substitute a fake
  `_run_one_pair`, and `test_desk_topup_compute_reads_merged_bars_and_never_reads_bar_index_window_
  end_utc`) passes unmodified.
- Error cases: no new input surface is added (read-only, derived-value disclosure) — the existing
  error paths (`TopupRunIntegrityError` on a corrupted run-record file, the honest-empty
  `{"runs": [], "latest": null}` payload before any run) must keep behaving unchanged.

Test-first contract:

- TC-1: given a fixture-scoped rig with an injected fake adapter whose fetch genuinely appends new
  bars for pair `(SYM, TF)`, when a NEW top-up run walks that pair, then its outcome entry's
  `store_frozen_through_after` equals the newest bar `BarStore.merged_bars(SYM, TF)` reports for
  that pair AFTER the walk, in the same ISO format `store_frozen_through` already uses.
- TC-2: given a pair whose fetch is classified `unchanged` (a real vendor call returned only
  already-frozen content), when its outcome entry is recorded, then `store_frozen_through_after`
  equals that pair's own pre-fetch `store_frozen_through` value exactly.
- TC-3: given a pair whose fetch is classified `failed`, when its outcome entry is recorded, then
  `store_frozen_through_after` equals that pair's own pre-fetch `store_frozen_through` value
  exactly.
- TC-4: given a pair whose fetch is classified `reused` (a store-first exact-key hit, zero vendor
  calls), when its outcome entry is recorded, then `store_frozen_through_after` equals that pair's
  own pre-fetch `store_frozen_through` value exactly.
- TC-5: given a pair that holds no frozen bars before the run and whose fetch does not result in any
  bars being recorded (e.g. `failed`), when its outcome entry is recorded, then
  `store_frozen_through_after` is `null`.
- TC-6: given a fresh, empty top-up run store, when `GET /research/desk/topup/runs` is called before
  any run, then the response is HTTP 200 with `{"runs": [], "latest": null}` and triggers no
  compute (the unchanged honest-empty contract).
- TC-7: given two consecutive top-up runs recorded on the same fixture-scoped rig, when the second
  run's outcomes are compared against the first run's own persisted file on disk, then the first
  run's JSON file is byte-identical before and after the second run (append-only proof).
- TC-8: given the full backend suite runs after this iteration's change, when every EXISTING test in
  `test_desk_topup_compute.py` and `test_desk_topup_log.py` executes (including
  `test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls`,
  `test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_resumability_
  guarantee`, and every manager-mechanics test using a fake `_run_one_pair`), then all of them pass
  unmodified.
- TC-9: given a run recorded BEFORE this iteration's code shipped (a legacy run lacking
  `store_frozen_through_after` on any outcome entry), when `/desk`'s Top-up Runs latest-run detail
  renders that run, then it shows the honest `"library reach not recorded in this run"` fallback
  text rather than a computed or backfilled value.
- TC-10: given a NEW top-up run recorded with at least one pair whose fetch genuinely appended bars
  and at least one pair whose recorded reach is earlier than the run's own newest reach date, when
  `/desk`'s Top-up Runs latest-run detail renders that run in a real browser at a 1440×900 viewport,
  then a screenshot shows one descriptive line naming the newest reach date and the count of pairs
  reaching it, AND a list of the pairs recorded earlier (each with its own symbol/timeframe/date),
  both legible in one frame with no horizontal scroll, and the ranked briefing table renders
  unchanged from J-16's shipped layout.
- TC-11: given the same populated run, when `tests/test_copy_discipline.py` runs against the page's
  rendered copy including the new line, then it passes unmodified (no fresh/stale/current/behind/
  recommendation language anywhere in the new text).
- TC-12: given the backend suite runs after this iteration's change, when
  `Config().config_fingerprint()` is printed, then it prints `08e471b10130e1e2` unchanged, and zero
  new `Config` fields exist (`git diff` on `config.py` is empty).
- TC-13: given the MCP tool list is read from the running server after this iteration's change, then
  it still lists exactly 17 tool names (no new tool added).
- TC-14: given a `[NEW]`-flagged demo-narrator walkthrough is recorded over a populated run showing
  the library-reach disclosure, when its saved frames are opened, then each frame is a genuinely
  distinct image (unique md5 per frame) and legibly shows the new reach line and the earlier-pairs
  list in frame, at a normal window size with nothing cut off at the right.

## NOTES

- Recommended evidence route for TC-1/TC-10/TC-14: trigger ONE new, real top-up run against the
  AMBIENT `:3301`/`:8301` pair (via the shipped Top-up button, an explicit sanctioned operator act
  per Vision Key Capability 2) rather than standing up a scoped rig — this avoids the scoped-rig
  teardown race (iter-27) and the dead `base_url` override (iter-28) that broke prior `[NEW]`
  walkthroughs, and J-19 carries no honest-empty-state acceptance clause a real ambient run would
  destroy (unlike J-18 — iter-29's lesson does not apply here). The pinned pairs' currently-recorded
  spread (newest bars 2026-07-21..07-28 across timeframes, per the proposer's own measurement) means
  a fresh full run is very likely to naturally produce both a "just advanced" pair and an
  "already-was-fresher" or "still lags" pair without needing a contrived fixture. If the ambient
  route is used, still keep TC-1 through TC-9's fixture-scoped, network-free unit coverage as the
  suite's own hermetic proof — the ambient run is evidence-capture only, never a test.
- Do not touch the `expect.text` substrings `journey-scripts/J-09.json` and `journey-scripts/J-17.json`
  assert (`desk-topup-run-latest-counts`, `desk-topup-run-latest-window-basis`,
  `desk-topup-run-latest-failed`) — this iteration only ADDS a new sibling block; grep both scripts'
  asserted strings against the rendered page before considering the frontend change done (iter-24
  lesson).
- The prior evaluator's four owner-optional notes (iter-31: `B1` first-member-crash naming, `F1`
  counts-line suppression on the rare reuse race, `T3` a stale comment inside `J-18.json`, the demo
  `step-02.png` scroll-anchor gap) are binding "Do not redo" — none of them is this iteration's
  concern.
- Full-depth rationale is logged in `state/assumptions.md` iter-32, alongside the blueprint edits
  (additive only — no nav-skeleton change, so no `blueprint.reapproval-requested` file was written).
