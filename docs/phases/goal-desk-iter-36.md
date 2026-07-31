# Goal Iteration 36 — Screen-pin disclosure (J-21)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 36
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: a brand-new, never-before-built full-stack
  journey (new backend module + new endpoint + edits to two already-shipped `/desk` render
  surfaces — the Provenance panel and the Run Screen control's sibling line), whose first-ever
  `[NEW]`-flagged demo-narrator walkthrough clause a `lean`/`evidence` dispatch cannot deliver (no
  demo-narrator step) — the binding depth recommendation's own "brand-new full-stack journey"
  escape condition, since the evaluator's `evidence` recommendation for this iteration predates
  the goal-proposer's promotion of J-21 this cycle. See `assumptions.md` iter-36 for the full
  evidence trail.
- **Frontend Present:** yes
- **Target journeys:** J-21
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-07, J-12, J-16, J-18, J-20
- **Anti-goal reminders:**
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint,
    and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - No lookahead — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - Deterministic and seeded — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
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
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*

## GOAL

The operator opens `/desk` and, before clicking anything, sees whether a screen run right now
would reuse an already-recorded snapshot or walk the universe fresh — for both the currently
displayed screen's own date (in the Provenance panel) and for today's date (beside the Run Screen
control) — with an honest empty state when no universe snapshot is registered.

## BACKGROUND

The goal-proposer promoted **J-21** this cycle (`state/proposer-result.json`, `n_new_journeys: 1`,
`n_proposals: 3`), measured 2026-07-31 read-only over the frozen artifacts: the index currently
resolves `bar_store_signature 2ce14e8f252966f7`, a value **none** of the 12 recorded screen
snapshots carries, so the identical Run Screen click has been recorded both as a 1m41s 101-member
walk and, elsewhere, as a 14ms/16ms `reused` short-circuit — with nothing on the page today telling
the operator in advance which one a fresh click will get. Two sibling vision-gap proposals (the
coverage view and the universe surface, each with zero frontend clients) were measured and scored
lower, and are backlogged, not promoted.

Per the priority rubric: no journey is regressed, the last `coherence.md` was PASS (no
consolidation owed), and J-21 is the only failing/new journey this cycle, so it is targeted alone
(rubric rules 4/5 — smallest concrete change set, never bundled with a second risky change). The
evaluator's own recommendation for this iteration is `evidence` (all 20 prior journeys are
`passing`, with only J-20's demo-narrator film owed as evidence), but J-21 is a brand-new
full-stack journey — a new backend module, a new endpoint, edits to two already-shipped `/desk`
surfaces, and a first-ever `[NEW]`-flagged demo-narrator walkthrough clause — which neither `lean`
nor `evidence` can deliver (no developer at `evidence`, no demo-narrator at `lean`; the iter-12/13
lesson). This overrides the binding recommendation per the depth-binding rule's fourth escape
condition, the same pattern iterations 15/17/23/24/26/29/32/35 used for their own brand-new
journeys; see `assumptions.md` iter-36 for the full evidence trail and two logged interpretation
calls.

Applicable lessons from `lessons.md`: (iter-32) triggering a real ambient run against a "latest
wins" panel invalidates sibling golden scripts pinned to the current one — this iteration's match
and empty states are therefore captured on a **fixture-scoped rig**, never by an ambient Run
Screen click (see `assumptions.md` iter-36). (iter-26/27/31) the differ-state screenshot and the
`[NEW]` demo-narrator walkthrough should still record against the **ambient** `:3301`/`:8301` pair
where the state already exists — no scoped rig needed for those. (iter-30(b)) if a scoped rig is
provisioned, restore `apps/frontend/next-env.d.ts`/`tsconfig.json` in its own teardown. (iter-29)
capture any NEW empty state's screenshot BEFORE any populating action in that same rig session.
(iter-33/34) narrate the walkthrough from the actually-rendered page, after the code lands, never
before. (iter-34) open screenshot citations before trusting them — `md5sum` across a lane's
captures is the cheap tell for blank/duplicate frames. (iter-18/19/32 J-19 precedent)
`journey-scripts/*.json` must assert stable substrings, never a specific run's exact ids/counts —
`journey-scripts/J-21.json` must follow this from the start.

Non-blocking passenger note (rule 7 — never an iteration goal on its own): since this iteration's
full pipeline already dispatches a demo-narrator step, it should also re-record J-20's own
`[NEW]`-flagged walkthrough (currently missing per `iteration-state.md`'s `evidence_makeup: true`)
while it is already running, at zero extra scope. See NOTES below.

## IN SCOPE

### Backend
- [ ] New desk module owning the pin-resolution read (e.g. `app/research/desk_screen_pins.py`,
      name at build discretion), resolving the five pins for a caller-supplied `screen_date`
      through the SAME accessors `run_screen_and_record` already uses (`screen_as_of`,
      `UniverseStore.list()`'s latest record id, `Config.config_fingerprint()`,
      `compute_bar_store_signature` over `desk_coverage.get_desk_coverage`'s index-only read) —
      zero new derivation, zero `BarStore` read of any kind (T-4)
- [ ] Recorded-or-not lookup via `ScreenStore.find_by_key` on exactly those five pins (the same
      lookup J-18's pre-check already makes); `members_total` read the way
      `DeskScreenComputeManager.trigger` already reads it
- [ ] New GET endpoint (e.g. `GET /research/desk/screen/pins`, exact path at build discretion),
      `screen_date` REQUIRED query param (422 if absent, mirrors
      `POST /research/desk/screen/compute`'s own required-param convention); honest empty payload
      at HTTP 200 when no universe snapshot is registered — see Data-contract addition below for
      the exact shape; writes nothing, triggers nothing, recomputes nothing (assert
      `compute_tradability` and `BarStore` read call counts == 0 in tests)
- [ ] Backend tests over planted, scoped stores (goal.md step 6): a snapshot already recorded
      under the exact resolvable pins is named byte-identically; after one row is planted into the
      scoped bar index, the resolved signature differs and `recorded` becomes `null`; a trigger
      for the same date still reuses the pre-existing snapshot in the first case and records a NEW
      one (earlier file untouched) in the second; a fresh store with no universe snapshot returns
      the honest empty payload at HTTP 200; the same `screen_date` requested twice produces a
      byte-identical body; zero-call-count assertions

### Frontend
- [ ] `DeskProvenance` (`apps/frontend/app/desk/page.tsx:1702`) gains the resolved pins for the
      DISPLAYED snapshot's own `screen_date`, rendered beside its already-shown recorded pins — the
      served `recorded`-or-`null` answer IS the match/differ statement (the page derives no
      equality of its own, the J-20 rule)
- [ ] One new descriptive line beside the Run Screen control, querying the pins endpoint for
      `todayUtcDate()` (the SAME value the trigger already submits, `page.tsx:228`/`:2350`),
      naming the snapshot a run today would reuse (its own recorded id + created-at) or stating
      that none is recorded and a run would walk `members_total` members
- [ ] Honest empty state when no universe snapshot is registered
- [ ] Copy stays purely descriptive — no fresh/stale/current/behind/up-to-date/outdated judgement,
      no advice, prediction, or urgency language (T-copy discipline); no threshold, score, or
      confidence number computed anywhere
- [ ] No new ranked-table column, no attribute/selector any existing golden's click target can
      match; `test_desk_ui_guards.py`/`test_desk_hover_tooltip_guard.py`/
      `test_copy_discipline.py` stay green unmodified

### New user-facing capability
Before clicking Run Screen (or before reading a past screen's own provenance), the operator can
see whether a run under the pins that would resolve right now would reuse an already-recorded
snapshot or walk the universe fresh.

### New information displayed
The five resolved pins (`screen_date`, `as_of`, `universe_snapshot_id`, `config_fingerprint`,
`bar_store_signature`) for a given date; whether a snapshot is already recorded under them (its own
`id`, `created_utc`, ranked/skipped counts) or an honest none; `members_total` a fresh walk would
attempt.

### New user actions
None — this is a view-only disclosure that renders automatically on mount beside the already-shown
Provenance panel and Run Screen control (no new button, no polling loop, no auto-refresh).

### UI surface changes
No new section and no new page — an extension of the existing Provenance panel plus one new line
beside the existing Run Screen control.

### Product surface delta
`/desk` moves from "the operator discovers reuse-vs-walk only after clicking" to "the operator sees
it in advance, every time the page is open."

### Blueprint conformance
Desk (existing Information-Architecture home — the disclosure lives inside the ALREADY-REGISTERED
`/desk` canonical home, per the Feature/journey homes table's new J-21 row). No nav-skeleton
change.

### Data-contract additions
**Screen-pin resolution** — new value, one owner, one endpoint (registered in `blueprint.md` this
iteration, before the code lands):
- Computed by: new `app/research/desk_screen_pins.py` (name at build discretion)
- Served by: `GET /research/desk/screen/pins` (exact path at build discretion; `screen_date`
  REQUIRED query param)
- Shape:
  ```
  {
    "screen_date": str,
    "as_of": str,
    "universe_snapshot_id": str | null,
    "config_fingerprint": str,
    "bar_store_signature": str | null,
    "members_total": int >= 0,
    "recorded": {
      "id": str, "screen_date": str, "created_utc": str, "bar_store_signature": str,
      "ranked_count": int >= 0, "skipped_count": int >= 0
    } | null
  }
  ```
- Every pin is resolved through the accessor that already owns it (no second derivation); the
  recorded-or-not answer comes from `ScreenStore.find_by_key`, the same lookup J-18's pre-check
  already makes. Persists nothing (no store, no file, no cache, no index, no new `Config` field,
  no new MCP tool).

## OUT OF SCOPE

- No new ranked-table column and no change to the ranked table's own rendering — J-16's measured
  width contract stays untouched
- No new MCP tool (the existing `/research/` allowlist already reaches the new GET path)
- No threshold/staleness/confidence number, no fresh-vs-stale judgement language, no advice or
  prediction language (Non-Goals; goal.md J-21 step 4)
- No change to `desk_screen.py`'s recorded row/snapshot shapes, five-pin key, or rank key; zero
  diff to `desk_screen_compute.py`/`desk_coverage.py`/`tradability.py`/`levels.py`/`bars.py`/
  `bar_index.py`/`StructureChart.tsx`
- No new `Config` field
- No real ambient Top-up or Run Screen click — the match and empty states are captured on a
  fixture-scoped rig; only the differ state (already naturally present) is captured on the
  ambient `:3301`/`:8301` pair, read-only (the iter-32 lesson: an ambient "latest wins" write
  invalidates sibling golden scripts)
- No touching J-19's or J-20's already-DONE work or their golden scripts (binding "Do not redo"
  per iteration-state), except riding J-20's own missing demo-narrator film as a zero-scope
  passenger on this iteration's already-dispatched demo-narrator step (see NOTES)

## DEFINITION OF DONE

- [ ] J-21 passes via browser-qa-agent (match state on a fixture-scoped rig, differ state on the
      ambient rig, empty state on a fixture-scoped rig — all legible at 1440×900 with no
      horizontal scroll, ranked table rendering exactly as J-16 shipped it)
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-06, J-07, J-12, J-16, J-18, J-20) remain
      green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (SSOT, append-only, explicit-operator-act, no-advice,
      no-new-statistics, no-lookahead, deterministic/no-wall-clock rails all hold)
- [ ] Unit tests pass; no regressions (full backend suite green, fingerprint `08e471b10130e1e2`
      unchanged, MCP tool count still exactly 17)
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-36-dev.md`
- [ ] A `[NEW]`-flagged demo-narrator walkthrough covers the pin disclosure end to end, narrated
      over both the match and differ states, recorded AFTER the code lands (never before) and
      captioned from the actually-rendered page
- [ ] All 20 existing stored golden replay scripts (J-01..J-20) replay green with zero script edits
- [ ] `journey-scripts/J-21.json` is written using stable substrings/testid-existence checks, never
      a specific run's exact snapshot ids/counts (the J-18/J-19/J-20 hardening precedent)

## TESTING REQUIREMENTS

- Browser: J-21 (three states: match [fixture-scoped rig], differ [ambient rig], empty
  [fixture-scoped rig, captured before any registration in that rig session]); regression smoke on
  J-01, J-03, J-04, J-06, J-07, J-12, J-16, J-18, J-20
- Unit/integration: `desk_screen_pins.py`'s resolution logic over planted scoped stores (see
  TC-1..TC-7); call-count assertions proving zero recompute
- Error cases: missing `screen_date` query param (422), no universe snapshot registered (honest
  empty at HTTP 200, never 4xx/5xx)

Test-first contract:

- TC-1: given a fixture-scoped store where a screen snapshot is already recorded under exactly the
  five pins `run_screen_and_record` would resolve for date D, when
  `GET /research/desk/screen/pins?screen_date=D` is called, then the response's `recorded.id`,
  `created_utc`, `bar_store_signature`, `ranked_count` and `skipped_count` are byte-identical to
  that record's own file on disk, and `members_total` equals the pinned universe record's own
  member count.
- TC-2: given the same fixture-scoped store and date D, when a screen-run trigger is issued for
  date D, then it reuses exactly the snapshot named by TC-1's `recorded.id` (J-18's shipped reuse
  behaviour, unchanged).
- TC-3: given the fixture-scoped store from TC-1, when one new row is planted into the scoped bar
  index (changing a member's frozen coverage), then `GET /research/desk/screen/pins?screen_date=D`
  resolves a different `bar_store_signature` than before and reports `recorded: null`.
- TC-4: given the state from TC-3, when a screen-run trigger is issued for date D, then it walks
  every member and records a NEW snapshot while the earlier file from TC-1 remains byte-identical
  on disk.
- TC-5: given a fresh scoped store with no universe snapshot registered, when
  `GET /research/desk/screen/pins?screen_date=D` is called, then the response is HTTP 200 with an
  honest empty payload (`universe_snapshot_id: null`, `bar_store_signature: null`,
  `members_total: 0`, `recorded: null`), never a 4xx/5xx.
- TC-6: given any pins request under test instrumentation, when the request completes, then the
  recorded `compute_tradability` call count is exactly `0` and zero `BarStore` reads occur.
- TC-7: given the same `screen_date` requested twice in succession, when the pins endpoint is
  called both times, then the two response bodies are byte-identical (no wall-clock field, T-6).
- TC-8: given the `screen_date` query param omitted, when
  `GET /research/desk/screen/pins` is called, then the response is HTTP 422, never a silent
  default to today.
- TC-9: given `/desk` rebuilt clean (T-9) and opened on a fixture-scoped rig at a 1440×900
  viewport with no horizontal scroll, when the displayed screen's own recorded pins match the
  pins resolved right now (a freshly-recorded snapshot queried before anything else changes),
  then the Provenance panel names the snapshot a run would reuse, in one screenshot with the
  ranked briefing table rendering exactly as J-16 shipped it.
- TC-10: given `/desk` opened on the ambient `:3301`/`:8301` rig at the same viewport, when the
  displayed screen's own recorded pins differ from the pins resolved right now (the ambient case
  today: the index resolves `2ce14e8f252966f7`, which none of the 12 recorded snapshots carries),
  then the page states that no screen is recorded under the resolved pins and that a run would
  walk `members_total` members, in a second screenshot.
- TC-11: given a fixture-scoped rig with no universe snapshot registered, when `/desk` is opened
  (before any registration happens in that rig session), then the page renders the honest empty
  state for the pin disclosure, captured in a third screenshot.
- TC-12: given the fully rebuilt suite, when `test_copy_discipline.py`,
  `test_desk_ui_guards.py` and `test_desk_hover_tooltip_guard.py` run, then all pass unmodified,
  and the ranked table gains no new column/control (J-16's width contract holds).
- TC-13: given all 20 existing stored golden replay scripts (J-01..J-20), when replayed against
  the built `/desk`, then all pass green with zero script edits.
- TC-14: given a `[NEW]`-flagged demo-narrator walkthrough recorded AFTER the code lands, when
  played back, then it narrates the pin disclosure end to end over both the match and differ
  states, captioned from the actually-rendered page (iter-33 lesson).

## NOTES

- Non-blocking passenger, never this iteration's own goal: this iteration's full pipeline already
  dispatches a demo-narrator step for J-21's own `[NEW]` walkthrough; while it is running, it
  should also re-record J-20's still-missing `[NEW]`-flagged walkthrough (`evidence_makeup: true`
  in `iteration-state.md`) against the ambient ledger, at zero extra scope. If the demo-narrator
  step cannot fit both in this run without risk to J-21's own evidence, J-21 takes priority and
  J-20's film keeps riding as a passenger on a future run — do not let this become a reason to
  widen this iteration's scope.
- Two vision-gap proposals were measured and NOT promoted this cycle (coverage view, universe
  surface — both have zero frontend clients but scored lower than J-21); no action needed.
- Owner-optional follow-ups already on file (iteration-state.md) — none of these becomes a new
  iteration goal on their own: the "ranked rows are identical" sentence's field-subset scope, the
  unknown-id `base_resolution` fourth value, and the 10-of-19 golden-replay coverage note.
