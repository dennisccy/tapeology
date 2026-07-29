# Goal Iteration 17 — Every ranked row discloses the price its wall sits at, beside the close it was measured from

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 17
- **Mode:** next
- **Depth:** full
- **Full trigger:** 2 — Data model: this adds a new field (`reference_close`) to the persisted,
  already-registered "Screen snapshots, rank rows, skip rows" Data-Contract row (`desk_screen.py`,
  `GET /research/desk/screen`) — every future recorded screen snapshot carries it forever. J-13's
  acceptance also names a first-ever `[NEW]`-flagged demo-narrator walkthrough for this specific
  disclosure; the iter-12/iter-13 lesson proved a `lean`-dispatched iteration cannot score a
  brand-new walkthrough clause within its own run (the demo-narrator lane runs after the
  goal-evaluator at `lean` depth), reinforcing `full`.
- **Frontend Present:** yes
- **Target journeys:** J-13
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12
  <!-- Reflowed onto ONE physical line by the goal-desk-iter-17 audit (finding P1). Content
       unchanged. `replay_lane_spec_journeys` (scripts/automation/lib/replay-lane.sh:70) parses this
       line with `head -1`, so the wrapped continuation silently dropped J-11/J-12 from
       REQUIRED_JOURNEYS and both journeys reached neither the replay nor the LLM lane. Keep this
       list on a single line until the parser handles continuations. -->

- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a future era). *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*

## GOAL

Every ranked row on `/desk` shows the exact price its wall sits at (`reference_close`) beside the
`price_low`–`price_high` band range it was measured against, so "the price is inside the wall" is a
fact visible on screen instead of arithmetic the operator (or an agent) would otherwise have to
invert out of `distance_bps` — exactly the client-side recomputation the Data Contract forbids.

## BACKGROUND

Iteration 16 closed GOAL_ACHIEVED (12/12 journeys passing, 0 regressed, COHERENCE-PASS). The
goal-proposer then appended J-13 inside the `AUTO:journeys` marker (its sixth post-GOAL_ACHIEVED
addition this era, after J-08/09/10/11/12), reopening the era for one more disclosure journey — the
same pattern as iterations 9, 11, 14, 15, 16. J-13's own rationale, measured live 2026-07-29 against
the running product's own artifacts: the string `price` occurs zero times in the 1,779-line
`apps/frontend/app/desk/page.tsx`, so `price_low`/`price_high` — already recorded on every ranked row
of every snapshot on disk since iter-3 and already typed at `lib/types.ts` — are rendered NOWHERE,
and the reference close is not even recorded, though `compute_screen` (`desk_screen.py:370`) already
binds it locally as `close` before feeding it to `_select_best_band`/`_distance_bps` and then drops
it. The close is recoverable from a recorded row ONLY by inverting `distance_bps` against a band edge
under the row's own `side` — the client-side recomputation the single-source-of-truth rail forbids —
which is exactly why goal.md requires it be recorded at its one owner instead.

**Target selection.** No journey is regressed; the last coherence audit was PASS, so no consolidation
pass is owed; J-13 is the only failing/unbuilt journey in the digest, so it is the natural, sole
target (priority rubric step 4 — smallest concrete change wins, and there is no competing journey to
weigh against). It does not unblock any other journey; it is a pure disclosure addition, the same
shape as J-08 and J-11 before it.

**Depth and lessons applied.** Full trigger 2 applies (new field on a persisted, registered
Data-Contract row); the acceptance also names a first-run `[NEW]`-flagged demo-narrator walkthrough,
and lessons iter-12/iter-13 established that `lean` cannot score a brand-new walkthrough clause in
the same run (demo-narrator runs after the goal-evaluator at `lean` depth) — `full` is required so
the walkthrough is produced BEFORE scoring. Scoped-rig discipline (iter-9/11/14/15/16 lessons) binds
every lane this iteration: any NEW screen compute for a not-already-recorded pin set must run on a
fixture-scoped rig (never `apps/backend/.data`), the rig path must be stated in every lane's own
dispatch and re-derived after any re-dispatch (iter-14 lesson — the scratch dir is PID-scoped), and
isolation must be independently verified (e.g. `/proc/<pid>/environ` for `TAPEOLOGY_*` overrides —
iter-15 lesson: scoped PORTS are not a scoped STORE). The iter-10 lesson applies to any new screen
compute this iteration triggers: check the target store for an existing snapshot under the same five
pins BEFORE computing, and disclose any collision in the script's `notes`/results report if one is
unavoidable. The iter-16 lesson applies to the browser-QA lane: verify no other project's dev server
shares the Chrome instance (a capture-time page-origin assertion against the rig's own base URL), and
never mark a "in a real browser" test case PASS on a source-code read alone.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/research/desk_screen.py` `compute_screen` (~:370): bind `reference_close` on
      every ranked row dict, copied verbatim from the SAME `close` local
      `_resolve_reference_close_and_history` already returns and this function already uses to call
      `_select_best_band`/`_distance_bps` — zero new `BarStore` read, zero new accessor, zero
      re-derivation of which bar is the basis (that stays `compute_tradability`'s and
      `_resolve_reference_close_and_history`'s exclusive decision, unchanged).
- [ ] Update the module's own row-shape docstring/comment documenting the new field and the
      legacy-row (entirely-absent-key, never `null`) fallback contract, following the J-08/J-11
      precedent immediately above it in the same function.
- [ ] Tests in `apps/backend/tests/test_desk_screen.py`: fixture-scoped golden asserting the exact
      `reference_close` per ranked row (including one row whose close lies INSIDE its own recorded
      band, `distance_bps` 0.0, and one whose close lies outside it), byte-identical row content on a
      re-run under identical pins, a legacy-row absence check, a `merged_bars` call-count guard (no
      additional `BarStore` read beyond the one existing walk), and a rank-order-unchanged check
      against the pre-change golden (`_row_rank_key` untouched).
- [ ] Confirm (test) the MCP `desk_screen` tool and `get_endpoint`'s `/research/` allowlist proxy the
      new field with zero code change (byte-identity of the GET response; the 17-tool contract
      unaffected).

### Frontend
- [ ] `apps/frontend/lib/types.ts` `DeskScreenRow`: add `reference_close?: number | null` beside the
      already-typed `price_low`/`price_high` fields (the same optional-field pattern `basis_as_of`/
      `history_sessions` already use for a legacy-row-absent value).
- [ ] `apps/frontend/app/desk/page.tsx` `DeskRow`: add one new `band` column cell rendering the row's
      own `price_low`–`price_high` range beside `reference_close` (e.g. `band 488.50–490.85 · close
      490.85`), with the honest `"close not recorded in this snapshot"` fallback for legacy rows —
      following the SAME rounded-display split the distance/score/basis/history cells already use.
      Add the matching `<th>band</th>` header cell to `DeskRowsTable`.
- [ ] `deskRowDrillInTitle`: extend the row's existing composite hover tooltip with the row's
      full-precision `reference_close` (never a new per-cell `title` under the stretched drill-in
      anchor — the iter-6/iter-7 audit F2 lesson, applied proactively the same way the basis/history
      additions already did).
- [ ] Confirm `tests/test_copy_discipline.py` passes unmodified against the new `band`/`close` copy
      strings (no advice/imperative/prediction language).

### New user-facing capability
The operator (and any Claude/MCP reader of `desk_screen`) can see, for every ranked row, the exact
price the wall was measured from beside the band range it sits in or short of — "price is inside the
wall" becomes a legible fact instead of unrecoverable arithmetic.

### New information displayed
`reference_close` (the daily close the row's band selection and distance were computed from) and the
row's own already-recorded `price_low`–`price_high` band range, rendered together in a new `band`
column and in the row's composite hover tooltip.

### New user actions
None — read-only render; no new button or control.

### UI surface changes
One new `band` column on the existing `/desk` ranked-rows table (`DeskRowsTable`/`DeskRow`); one new
line in the row's existing composite drill-in tooltip. No new page, no new section, no new nav row.

### Product surface delta
`/desk`'s ranked table grows from nine to ten columns; the row's existing hover tooltip gains one
more disclosed value. No other surface changes.

### Blueprint conformance
Desk section of the Information Architecture (`runs/goal-session-desk/state/blueprint.md`) — no new
home; this iteration extends the already-registered `/desk` canonical home's ranked table. A J-13 row
was added to the blueprint's Feature/journey homes table, the Navigation-skeleton Desk description
gained an iter-17 sentence, and the "Screen snapshots, rank rows, skip rows" Data-Contract row gained
an iter-17 addition note plus a matching `RESOLVED at iter-17` build-time-scope note (documentation
only, no new build scope beyond what is in this spec).

### Data-contract additions
`reference_close: float` — present on every ranked row of every NEW screen snapshot from this
iteration forward; entirely absent (not `null`) on every ranked row recorded before this iteration
and on all skip rows. Owner: `app/research/desk_screen.py` (the already-registered owner of "Screen
snapshots, rank rows, skip rows"). Serving endpoint: `GET /research/desk/screen` (the already-
registered endpoint — no new route, no new query param, no new `Config` field, no new MCP tool; the
`desk_screen` tool's byte-identical no-arg proxy contract covers the field automatically, and J-06's
exactly-17-tool contract is unaffected). This is an ADDITIVE extension of an already-registered row,
never a second owner or a second endpoint for the value.

## OUT OF SCOPE

- Any new Data-Contract row, new endpoint, new route, or new `Config` field.
- Any diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
  `desk_coverage.py` — the new value is copied out of the one walk `desk_screen.py` already makes.
- Any change to the rank key (`band_class`, `distance_bps`, `band_score`, `symbol`) or the 5-pin
  snapshot key — this journey discloses, it never ranks, filters, gates, weights, or scores.
- Any threshold, proximity/quality number, or "price is inside the band" boolean flag computed
  anywhere — the disclosure is the two raw numbers, side by side, nothing derived from them.
- Backfilling, rewriting, or recomputing any already-recorded screen snapshot — legacy rows keep
  their honest absent-field state forever; `/desk` renders it as `"close not recorded in this
  snapshot"`, never a value computed at read time.
- A CLI warmer for this field (none of J-08/J-11 needed one either; the existing screen compute
  POST/CLI already serves the field automatically once it lands in `compute_screen`).
- Any WRITE to `apps/backend/.data` for evidence capture — a new screen compute for a not-already-
  recorded pin set, if needed for evidence, runs on a fixture-scoped rig only (iter-9/11/14/15/16
  scoped-rig discipline), and any collision with an existing golden's target store is checked and
  disclosed first (iter-10 lesson).

## DEFINITION OF DONE

- [ ] J-13 passes via browser-qa-agent
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10,
      J-11, J-12) remain green (deterministic replay + LLM fallback — mechanically verified)
- [ ] No anti-goal violation introduced — single source of truth holds (one owner, one endpoint, zero
      duplicated computation), snapshots stay append-only and unedited, the briefing stays
      descriptive-only, no new statistic/gate/threshold is computed
- [ ] A `[NEW]`-flagged demo-narrator walkthrough (`Demo Verdict: RECORDED` + a non-empty gallery
      directory, never a same-named replay script) covers the briefing's price disclosure end to end
- [ ] Full backend suite green; `Config().config_fingerprint()` prints `08e471b10130e1e2`; zero new
      `Config` fields; the `default`/`v1` engine-equivalence test passes byte-identical; MCP tool
      count is exactly 17; zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
      `StructureChart.tsx`; `tests/test_copy_discipline.py` green unmodified
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-17-dev.md`

## TESTING REQUIREMENTS

- Browser: J-13 (`/desk` ranked table shows the new `band` column with `reference_close` legible
  beside `price_low`–`price_high`, at least one row inside its band and one row outside it, both in
  one screenshot; a legacy snapshot's row shows the honest fallback; demo-narrator walkthrough).
  Regression smoke: J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12.
- Unit/integration: `desk_screen.py` `reference_close` binding (exact-value golden, in-band vs
  out-of-band rows, byte-identical re-run under identical pins, legacy-row absence, `merged_bars`
  call-count guard, rank-order-unchanged), MCP `desk_screen`/`get_endpoint` proxy byte-identity.
- Error cases: a pre-existing (legacy) screen snapshot's ranked rows carry no `reference_close` key
  and the served response, the on-disk file, and its checksum are all byte-unchanged; a re-run under
  identical pins returns the existing already-recorded response rather than writing a new file.

Test-first contract:

- TC-1: given a fixture-scoped rig with a registered universe snapshot and bar store, when a NEW
  screen is computed for a screen_date not already recorded under the same five pins, then every
  ranked row's response carries a `reference_close` field equal to the `close` value
  `_resolve_reference_close_and_history` returns for that row's own `basis_as_of`.
- TC-2: given that same new screen snapshot, when each ranked row's `reference_close` is compared to
  the `close` field of the `1d` bar dated at that row's own `basis_as_of` from
  `GET /research/candles?symbol=<sym>&timeframe=1d`, then the two values are byte-identical for every
  ranked row.
- TC-3: given the same new screen snapshot, when its ranked-row symbol sequence is compared to the
  sequence the same five pins produced before this change (a golden fixture recorded pre-change,
  replayed post-change, plus `_row_rank_key`'s own source appearing only as unchanged CONTEXT in
  `git diff`), then the two sequences are byte-identical.
- TC-4: given the new screen snapshot, when the same compute is re-triggered under identical pins,
  then the store returns the already-recorded response byte-identical to the first, and no new file
  is written to disk.
- TC-5: given a screen snapshot recorded before this iteration's code landed, when
  `GET /research/desk/screen?date=<that date>` is called, then its ranked rows carry no
  `reference_close` key (not `null` — the key is absent), the file's on-disk checksum is unchanged
  from before this iteration, and `/desk` renders the honest `"close not recorded in this snapshot"`
  string for each of its rows.
- TC-6: given the `/desk` page after a T-9 clean rebuild, when a screen carrying `reference_close`
  data is loaded in a real browser, then the ranked table's `band` column shows, in ONE screenshot,
  at least one ranked row whose `reference_close` lies INSIDE its own recorded `price_low`–
  `price_high` range and at least one ranked row whose `reference_close` lies outside it, both
  legible.
- TC-7: given `desk_screen.py`'s row builder, when a screen is computed for N symbols with bars, then
  a call-count guard test asserts `BarStore.merged_bars(symbol, "1d")` is invoked exactly once per
  symbol — no additional store read beyond the one existing walk.
- TC-8: given `apps/frontend/app/desk/page.tsx`'s source, when scanned for arithmetic on
  `distance_bps`, `price_low`, or `price_high` outside the existing band-range display, then no
  expression derives a price value on the page — the frontend renders only what the endpoint serves.
- TC-9: given the full backend suite runs after this change, when `Config().config_fingerprint()` is
  read, then it prints `08e471b10130e1e2`; a diff of `tradability.py`/`levels.py`/`bars.py`/
  `bar_index.py`/`StructureChart.tsx` against the pre-iteration tree is empty; and zero new `Config`
  fields exist.
- TC-10: given `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` contract and a live call to
  the MCP `desk_screen` tool, when the suite runs, then the tool count is exactly 17 and the tool's
  JSON is byte-identical to the direct `GET /research/desk/screen` response for the same snapshot.
- TC-11: given `tests/test_copy_discipline.py`, when run after the `band`/`close` column and tooltip
  line land, then it passes unmodified (zero edits to the lint file itself, and the new copy strings
  contain no advice/imperative/prediction language).
- TC-12: given the demo-narrator lane runs at `full` depth (before scoring), when it records the
  `[NEW]`-flagged J-13 walkthrough, then the resulting artifact shows `Demo Verdict: RECORDED` with a
  non-empty screenshot gallery narrating: the ranked table's new `band` column, a row whose close
  sits inside its band, a row whose close sits outside its band, and a legacy row's honest
  `"close not recorded in this snapshot"` state.

## NOTES

- Applied lessons: iter-12/iter-13 (a `[NEW]`-flagged demo-narrator walkthrough clause forces `full`
  depth — the demo-narrator lane runs after scoring at `lean`); iter-9/iter-11/iter-14/iter-15/iter-16
  (state, in EVERY lane's own dispatch, which store root it serves against, and re-derive the rig
  path after any re-dispatch — never let a report's prose be the only evidence of isolation; scoped
  PORTS are not a scoped STORE); iter-10 (an evidence-only compute can silently collide with a stored
  golden — check the target store for an existing record under the same key first, and disclose any
  unavoidable collision); iter-16 (a shared Chrome instance can silently capture an unrelated app's
  page — assert the captured page's origin matches the rig's own base URL; a source-code read never
  satisfies a "in a real browser" test case, no matter how confident the report's prose is).
- No assumption-ledger entry this iteration: J-13's steps and acceptance text are fully prescriptive
  (exact field name, exact source variable, exact rendering pattern, exact test scenarios) and leave
  no genuine interpretation gap for the decomposer to log.
- Carry-only, not this iteration's concern (do not redo, per iteration-state.md): J-12's
  `evidence_makeup: true` one-page re-capture of the earlier same-date view — ride it on whichever
  lane next touches `/desk`'s Screen History section, never as a standalone goal; the `[NEW]`
  walkthroughs already recorded for J-09/J-10/J-11/J-12 are CORRECT and must not be re-recorded.
