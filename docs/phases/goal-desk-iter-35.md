# Goal Iteration 35 — Screen comparison disclosure (J-20)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 35
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: a brand-new, never-before-built full-stack
  journey (new backend module + new endpoint + new `/desk` section rendered beside nine
  already-shipped sections' testids/tooltip/copy contracts), whose first-ever `[NEW]`-flagged
  demo-narrator walkthrough clause a `lean` dispatch cannot deliver (no demo-narrator step) — the
  binding depth recommendation's own "brand-new full-stack journey" escape condition, since the
  evaluator's `lean` recommendation for this iteration predates the goal-proposer's promotion of
  J-20 this cycle. See `assumptions.md` iter-35 for the full evidence trail.
- **Frontend Present:** yes
- **Target journeys:** J-20
- **Required-still-passing journeys:** J-03, J-04, J-05, J-06, J-07, J-12, J-13, J-14, J-16, J-18
- **Anti-goal reminders:**
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint,
    and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - Snapshots are append-only and pinned. Universe and screen snapshots are dated, checksummed,
    append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint,
    bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or
    rewritten — a new run is a new snapshot. *(critical)*
  - Every run is an explicit operator act. No scheduler, cron, daemon, auto-refresh, or
    market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - The briefing describes, never advises. Desk copy is descriptive measurement only — no advice,
    imperative, prediction, or ranking language implying action ("buy", "watch this",
    "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - No new statistics, gates, or strategies. No probability/expectancy/edge claims on any desk
    surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a
    future era). *(critical)*
  - The enhancement loop stays inside its box. The goal-proposer may append journeys ONLY inside
    the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this
    Anti-goals section, or any other part of this file; proposed journeys MUST carry a
    single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and
    `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value
    journey just to keep the loop alive is a failure. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - Persistence stays scoped — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay
    byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*

## GOAL

The operator opens `/desk` and, for the screen currently displayed, sees a new read-only "Screen
Comparison" section stating exactly how it differs from the screen recorded immediately before it —
rank/side/band-class/distance/basis changes per symbol, plus symbols that entered or left the
ranked set — or an honest "no earlier recorded screen" state on the ledger's oldest snapshot.

## BACKGROUND

The goal-proposer promoted **J-20** this cycle (`state/proposer-result.json`, `n_new_journeys: 1`),
measured live over the 12 recorded screen snapshots: four consecutive pairs change nothing but
`basis_age_days` while seven others churn heavily (up to 95 of 100 rows moving rank, 12 flipping
side), yet `/desk` renders both extremes identically because no module and no page line ever
compares two snapshots. Per the priority rubric, J-20 is the only failing/new item (no regressed
journeys, no coherence-FAIL, nothing to consolidate) and is targeted alone (rubric rule 4/5: one
journey, smallest concrete change set, never bundled with a second risky change). The prior
verdict was GOAL_ACHIEVED (iter-34) and the evaluator's own recommendation for this iteration is
`lean`, but J-20 is a brand-new full-stack journey — new backend module, new endpoint, new UI
section, and a first-ever `[NEW]`-flagged demo-narrator walkthrough clause — which a lean dispatch
structurally cannot deliver (the iter-12/13 lesson: the demo-narrator lane does not run at lean
depth). This overrides the binding recommendation per the depth-binding rule's fourth escape
condition, the same pattern iterations 15/17/23/24/26/29/32 used for their own brand-new journeys;
see `assumptions.md` iter-35 for the full evidence trail.

Applicable lessons from `lessons.md`: (iter-26/27/31) record the demo-narrator walkthrough against
the **ambient** `:3301`/`:8301` pair, never a scoped rig that tears down before the narrator runs —
this journey's acceptance is fully satisfiable over the already-recorded ambient ledger, so no
scoped rig is needed or wanted. (iter-31) anchor each walkthrough step on its own `data-testid`,
never a scroll position. (iter-33) narration must be written from the actually-rendered page, never
from the spec's intent — do not record the film before the code lands. (iter-34) a screenshot
citation is only evidence once opened, and `md5sum` across a lane's captures is the cheap tell for
blank/duplicate frames — open the artifacts, don't just cite them. (iter-32/33 J-19 precedent)
`journey-scripts/*.json` must assert stable substrings, never a specific run's exact counts/dates —
J-20's own golden script must follow this from the start.

## IN SCOPE

### Backend
- [ ] New desk module owning the screen-comparison computation (e.g.
      `app/research/desk_screen_diff.py`, name at build discretion), reading exactly two recorded
      snapshots via the existing `ScreenStore.list()` accessor (`desk_screen.py:581`) — zero new
      store, zero new file, zero recompute of any kind
- [ ] Base-snapshot resolution logic: default = the recorded snapshot with the greatest
      `screen_date` strictly earlier than the compare snapshot's own `screen_date` (ties broken by
      later `created_utc`, matching what `?date=` already serves); an explicit `base=<id>`
      overrides it; no earlier snapshot ⇒ honest `base: null` state; an unknown id ⇒ honest `null`
      at HTTP 200; a snapshot compared with itself ⇒ an honest refusal
- [ ] New GET endpoint (e.g. `GET /research/desk/screen/compare`, path/params at build discretion)
      returning the comparison payload — see Data-contract addition below for the exact shape;
      writes nothing, triggers nothing, recomputes nothing (assert `compute_tradability` call
      count == 0 in tests)
- [ ] Backend tests over planted, scoped snapshots (goal.md step 6): two identical-ranked
      snapshots report zero changes; a pair with a moved rank, a flipped side, an entered symbol
      and a left symbol each report exactly once with both recorded values verbatim; the oldest
      recorded snapshot reports the honest no-earlier-screen state; an unknown id is an honest
      null; the same two ids twice produce a byte-identical body; the GET writes nothing; a legacy
      base row missing `basis_as_of` is reported absent, never derived

### Frontend
- [ ] New read-only "Screen Comparison" section on `/desk`, rendered AFTER the ranked briefing
      table (beside Screen History / Top-up Runs / Index Reconciliation / Screen Runs) — both
      snapshots' own ids/screen dates/created-at/bar-store signatures, one descriptive counts line,
      the honest "ranked rows are identical" line, the honest no-earlier-screen state, and a capped
      table of the compare snapshot's first N rows using the shipped `EARLIER_PAIRS_DISPLAY_CAP`
      pattern (`apps/frontend/app/desk/page.tsx:882`/`:1032`) with its honest "showing N of M" line
- [ ] Wire the section to the new compare endpoint for whichever screen the page is currently
      DISPLAYING (the shipped `?id=` history selection) — no new control, no recompute trigger on
      page load
- [ ] New section introduces no attribute/selector any existing golden's click target can match
      (never reuses `data-screen-id`, `desk-history-row`, `desk-screen-row`, or any `desk-row-*`
      testid) and renders after the ranked table so the replay tool's first-visible-match text
      search cannot resolve into it

### New user-facing capability
The operator can see, for the currently-displayed screen, how it differs from the screen recorded
immediately before it — without leaving `/desk` or running any new compute.

### New information displayed
Both compared snapshots' own ids, screen dates, recorded-at timestamps and bar-store signatures;
per-symbol rank/side/band_class/distance_bps/basis_as_of for the compare snapshot beside the base
snapshot's own recorded values for the same symbol, plus a plain rank-change integer; the
entered/left symbol sets with the other snapshot's own recorded skip reason where it has one; a
descriptive counts line (rows compared, rank changed, side changed, entered, left).

### New user actions
None — this is a view-only disclosure that renders automatically for whichever screen is already
selected on the page (no new button, no new form).

### UI surface changes
One new section on `/desk`, positioned after the ranked briefing table.

### Product surface delta
`/desk` moves from showing each screen in total isolation to also disclosing screen-to-screen
change — the operator no longer has to eyeball two separately-opened screens to know whether "today
looks like yesterday" or "today churned."

### Blueprint conformance
Desk (existing Information-Architecture home — same canonical `/desk` page every prior desk
journey uses, per the Feature/journey homes table's J-20 row). No nav-skeleton change.

### Data-contract additions
**Screen comparison** — new value, one owner, one endpoint (registered in `blueprint.md` this
iteration, before the code lands):
- Computed by: new `app/research/desk_screen_diff.py` (name at build discretion)
- Served by: `GET /research/desk/screen/compare` (exact path/params at build discretion, e.g.
  `?id=<compare id>&base=<base id>`)
- Shape:
  ```
  {
    "compare": {"id": str, "screen_date": str, "as_of": str, "created_utc": str,
                "bar_store_signature": str, "universe_snapshot_id": str|null,
                "ranked_count": int>=0, "skipped_count": int>=0},
    "base": <same shape as compare> | null,
    "base_resolution": "explicit" | "default_prior_date" | "none_earlier",
    "rows": [
      {"symbol": str, "status": "compared"|"entered"|"left",
       "compare_rank": int|null, "base_rank": int|null, "rank_change": int|null,
       "compare_side": "support"|"resistance"|null, "base_side": "support"|"resistance"|null,
       "compare_band_class": "A"|"B"|"C"|null, "base_band_class": "A"|"B"|"C"|null,
       "compare_distance_bps": float|null, "base_distance_bps": float|null,
       "compare_basis_as_of": str|null, "base_basis_as_of": str|null,
       "skip_reason": "no_bars"|"no_basis"|null}
    ],
    "identical": bool,
    "counts": {"compared": int>=0, "rank_changed": int>=0, "side_changed": int>=0,
               "entered": int>=0, "left": int>=0}
  }
  ```
- Every field is copied verbatim from the two snapshots' own recorded rows via `ScreenStore.list()`
  — no field is derived from a fresh `compute_tradability`/`levels`/`bar_index` call. Persists
  nothing (no store, no file, no cache, no index).

## OUT OF SCOPE

- No new ranked-table column and no change to the ranked table's own rendering — J-16's measured
  width contract stays untouched
- No new MCP tool (the existing `/research/` allowlist already reaches the new GET path)
- No churn/significance/volatility/stability metric, no highlighting or ordering by size of change,
  no "notable"/"biggest mover" framing, no arrow/colour giving a direction a valence, no advice or
  prediction language (Non-Goals; goal.md step 4)
- No change to `desk_screen.py`'s recorded row/snapshot shapes, five-pin key, or rank key; zero
  diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`desk_coverage.py`/
  `StructureChart.tsx`
- No new `Config` field
- No real screen run triggered this iteration — the ambient ledger's 12 recorded snapshots already
  carry the identical-state, churned-state, and oldest/no-earlier examples the acceptance names
- No touching J-19's already-DONE record/display halves or their golden scripts (binding "Do not
  redo" per iteration-state)

## DEFINITION OF DONE

- [ ] J-20 passes via browser-qa-agent (identical state, churned state, no-earlier-screen state,
      all legible at 1440×900 with no horizontal scroll, ranked table rendering exactly as J-16
      shipped it)
- [ ] Required-still-passing journeys (J-03, J-04, J-05, J-06, J-07, J-12, J-13, J-14, J-16, J-18)
      remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (SSOT, append-only, explicit-operator-act, no-advice,
      no-new-statistics rails all hold)
- [ ] Unit tests pass; no regressions (full backend suite green, fingerprint `08e471b10130e1e2`
      unchanged, MCP tool count still exactly 17)
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-35-dev.md`
- [ ] A `[NEW]`-flagged demo-narrator walkthrough covers the screen-comparison disclosure end to
      end, narrated over the populated ambient ledger and over both the identical and churned pair,
      recorded AFTER the code lands (never before) and captioned from the actually-rendered page
- [ ] All 19 existing stored golden replay scripts (J-01..J-19) replay green with zero script edits
- [ ] `journey-scripts/J-20.json` is written using stable substrings/testid-existence checks, never
      today's exact snapshot ids/counts (the J-18/J-19 hardening precedent)

## TESTING REQUIREMENTS

- Browser: J-20 (three states: identical, churned, no-earlier-screen); regression smoke on J-03,
  J-04, J-05, J-06, J-07, J-12, J-13, J-14, J-16, J-18
- Unit/integration: `desk_screen_diff.py`'s comparison logic over planted scoped snapshots (see
  TC-1..TC-10); call-count assertions proving zero recompute
- Error cases: unknown snapshot id, self-compare, missing `basis_as_of` on a legacy base row

Test-first contract:

- TC-1: given two recorded screen snapshots whose ranked rows are identical (e.g.
  `screen-2026-07-31-c169546856c7` vs `screen-2026-07-30-bad6387963ef`), when
  `GET /research/desk/screen/compare` is called for the later snapshot, then the response's
  `identical` field is `true` and `counts.rank_changed`/`side_changed`/`entered`/`left` are all `0`.
- TC-2: given two recorded screen snapshots with churned rank order (e.g.
  `screen-2026-07-25-bd0b37ebc426` vs `screen-2026-07-20-ca185294a384`), when the compare endpoint
  is called, then at least one row's `rank_change` is non-null and non-zero, at least one row's
  `compare_side` differs from its `base_side`, and every `compare_*` field in `rows` is
  byte-identical to what `GET /research/desk/screen?id=<compare id>` serves for that same symbol.
- TC-3: given the ledger's oldest recorded snapshot (e.g. `screen-2026-06-22-3ecd45c062c7`), when
  the compare endpoint is called for it, then the response's `base` field is `null` and
  `base_resolution` is `"none_earlier"`.
- TC-4: given a symbol ranked in the compare snapshot but absent from the base snapshot's ranked
  rows, when the compare endpoint is called, then that symbol's row reports `status: "entered"`
  carrying the base snapshot's own recorded skip reason when its skip list names it, and `null`
  when the base does not mention the symbol at all.
- TC-5: given a symbol ranked in the base snapshot but absent from the compare snapshot's ranked
  rows, when the compare endpoint is called, then that symbol's row reports `status: "left"` the
  same way.
- TC-6: given the same two snapshot ids requested twice in succession, when the compare endpoint is
  called both times, then the two response bodies are byte-identical.
- TC-7: given an unknown snapshot id passed as `?id=`, when the compare endpoint is called, then it
  returns HTTP 200 with an honest null/not-found comparison, never a 500 or a fabricated body.
- TC-8: given a snapshot compared against itself (`?id=X&base=X`), when the compare endpoint is
  called, then the response is an honest refusal (non-2xx or an explicit "cannot compare a snapshot
  with itself" body), never a silent zero-diff no-op.
- TC-9: given any compare request under test instrumentation, when the request completes, then the
  recorded `compute_tradability` call count is exactly `0` and no `BarStore`/`bar_index`/dataset
  read occurs.
- TC-10: given a legacy base row that predates the `basis_as_of` field, when the compare endpoint is
  called, then `base_basis_as_of` for that row is reported as an honest `null`, never derived or
  backfilled.
- TC-11: given `/desk` rebuilt clean (T-9) and opened at a 1440×900 viewport with no horizontal
  scroll, when the currently-displayed screen's Screen Comparison section renders, then one
  screenshot shows both compared snapshots' ids/screen dates/created_utc/bar_store_signature, the
  descriptive counts line, and the capped rows table with an honest "showing N of M" line whenever
  the compare snapshot's row count exceeds the cap.
- TC-12: given the identical-state pair on the ambient ledger, when the corresponding `/desk` view
  is captured, then the screenshot shows the "the compared snapshots' ranked rows are identical"
  line and zero counts for rank/side/entered/left changes.
- TC-13: given the churned-state pair on the ambient ledger, when the corresponding `/desk` view is
  captured, then the screenshot shows at least one row whose rank moved by at least 20 places and
  at least one row whose side differs between the two recordings.
- TC-14: given the ledger's oldest snapshot, when its `/desk` view is captured, then the screenshot
  shows the honest no-earlier-recorded-screen state.
- TC-15: given a `[NEW]`-flagged demo-narrator walkthrough recorded over the populated ambient
  ledger after the code lands, when it is played back, then its steps narrate the Screen Comparison
  section end to end across both the identical-state and churned-state pair, with each caption
  matching its own captured frame.
- TC-16: given the full backend suite run after this iteration's change, when it completes, then it
  reports 0 failures, `Config().config_fingerprint()` still prints `08e471b10130e1e2`, and the MCP
  tool list read from the running program contains exactly 17 names.
- TC-17: given a SHA-256 listing of every recorded universe/screen/top-up/reconciliation/screen-run
  file taken before and after this iteration, when compared, then every file is byte-identical
  (zero new/altered/deleted record).
- TC-18: given all 19 stored golden replay scripts (`journey-scripts/J-01.json`..`J-19.json`), when
  replayed after this iteration's change, then all 19 pass green with zero script edits.
- TC-19: given `tests/test_copy_discipline.py`, `tests/test_desk_ui_guards.py`, and
  `tests/test_desk_hover_tooltip_guard.py` run after this iteration's change, then all three pass
  unmodified.

## NOTES

- This is the goal-proposer's thirteenth post-GOAL_ACHIEVED journey this session; the sibling
  proposal from this cycle (the displayed screen's own `bar_store_signature` vs the store's CURRENT
  signature) is explicitly NOT promoted — out of scope for this iteration, per
  `proposer-result.json`'s own summary.
- Depth escalation to `full` overrides the evaluator's binding `lean` recommendation under the
  depth-binding rule's fourth escape condition (brand-new full-stack journey); see `assumptions.md`
  iter-35 for the full evidence trail and reversibility note.
- `blueprint.md` has been updated this iteration (additive only): the J-20 Feature/journey-home row,
  the new "Screen comparison" Data Contract row, and an "IN BUILD at iter-35" build-time-scope note
  — no nav-skeleton change, so no `blueprint.reapproval-requested` file was written.
- Binding "Do not redo" items from `iteration-state.md` remain in force: do not touch J-19's
  record/display halves or their golden scripts; do not click Top-up or Run Screen; do not stand up
  a scoped rig — this journey's evidence is fully obtainable over the already-populated ambient
  ledger.
