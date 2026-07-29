# Goal Iteration 18 — Every ranked row discloses the nearest wall on the OTHER side of price

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 18
- **Mode:** next
- **Depth:** full
- **Full trigger:** 2 — Data model: this adds two new fields (`opposite_band`, `bands_by_class`) to
  the persisted, already-registered "Screen snapshots, rank rows, skip rows" Data-Contract row
  (`desk_screen.py`, `GET /research/desk/screen`) — every future recorded screen snapshot carries
  them forever. J-14's acceptance also names a `[NEW]`-flagged demo-narrator walkthrough narrated
  over POPULATED ranked rows, which goal.md's own text ties to closing iter-17's carried
  `RECORDED_WITH_NOTES` capture gap; the iter-12/iter-13 lessons proved a `lean`-dispatched iteration
  cannot score a brand-new walkthrough clause within its own run (the demo-narrator lane runs after
  the goal-evaluator at `lean` depth), reinforcing `full`.
- **Frontend Present:** yes
- **Target journeys:** J-14
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13
- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a future era). *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*

## GOAL

Every ranked row on `/desk` shows the nearest wall on the side of price it did NOT select
(`opposite_band`) plus how many bands of each class the row's own displayed wall was chosen from
(`bands_by_class`), so the 10,000×-wide spread between "0.6 bps away on the other side" and
"6,067.7 bps away on the other side" — currently invisible because every row keeps exactly one band
— becomes a legible fact instead of a number nobody can see without re-querying `tradability.py`
themselves.

## BACKGROUND

Iteration 17 closed GOAL_ACHIEVED and CONFIRM_ACHIEVED (13/13 journeys passing, 0 regressed,
COHERENCE-PASS). The goal-proposer then appended J-14 inside the `AUTO:journeys` marker (its seventh
post-GOAL_ACHIEVED addition this era, after J-08/09/10/11/12/13), reopening the era for one more
disclosure journey — the same pattern as iterations 9, 11, 14, 15, 16, 17. J-14's own rationale,
measured live 2026-07-29 against the canonical `compute_tradability` owner itself for all 63 ranked
members of a real recorded snapshot: every one of the 63 carries bands on BOTH sides of price
(typically 5+5 of the ≤10-band map, 52 of 63 hold the full 10), yet each recorded row keeps exactly
one — the nine top-ranked rows all read `support · class A · 0.00 bps`, while their own nearest
opposite wall sits anywhere from 0.6 bps (BRK-B #1) to 6,067.7 bps (CRM #6) away, and two rows
(ISRG #63, CMCSA #62) invert it entirely, ranking on a wall thousands of bps out while an
unclassified band sits 0.0 bps from close on the other side. Nothing on the page today says a nearer
band on the other side exists.

**Target selection.** No journey is regressed; the last coherence audit was PASS, so no consolidation
pass is owed; J-14 is the only failing/unbuilt journey in the digest, so it is the natural, sole
target (priority rubric step 4 — smallest concrete change wins, and there is no competing journey to
weigh against). It does not unblock any other journey; it is a pure disclosure addition, the same
shape as J-08/J-11/J-13 before it.

**Depth and lessons applied.** Full trigger 2 applies (two new fields on a persisted, registered
Data-Contract row); the acceptance also names a `[NEW]`-flagged demo-narrator walkthrough over
POPULATED rows, and lessons iter-12/iter-13 established that `lean` cannot score a brand-new
walkthrough clause in the same run (demo-narrator runs after the goal-evaluator at `lean` depth) —
`full` is required so the walkthrough is produced BEFORE scoring. Scoped-rig discipline
(iter-9/11/14/15/16 lessons) binds every lane this iteration: any NEW screen compute for a
not-already-recorded pin set must run on a fixture-scoped rig (never `apps/backend/.data`), the rig
path must be stated in every lane's own dispatch and re-derived after any re-dispatch (iter-14
lesson — the scratch dir is PID-scoped), and isolation must be independently verified (e.g.
`/proc/<pid>/environ` for `TAPEOLOGY_*` overrides — iter-15 lesson: scoped PORTS are not a scoped
STORE). The iter-10 lesson applies to any new screen compute this iteration triggers: check the
target store for an existing snapshot under the same five pins BEFORE computing, and disclose any
collision in the script's `notes`/results report if one is unavoidable. The iter-16 lesson applies to
the browser-QA lane: verify no other project's dev server shares the Chrome instance (a capture-time
page-origin assertion against the rig's own base URL), and never mark a "in a real browser" test case
PASS on a source-code read alone. The iter-17 lessons apply directly: keep the
`Required-still-passing journeys:` line above on ONE physical line (the wrapped-line parser only
reads the first line — this cost two journeys their regression check last iteration), and never start
a second `next dev` from `apps/frontend` while an ambient one is running (they share `.next` and the
ambient page silently starts serving the scoped backend's API base — copy the whole `apps/frontend`
tree to an isolated directory, or stop the ambient one first).

## IN SCOPE

### Backend
- [ ] `apps/backend/app/research/desk_screen.py` `compute_screen` (~:385, immediately after
      `best = _select_best_band(result["bands"], close)`): select `opposite_band` — the nearest band
      on the side `best["side"]` is NOT on, filtered from the SAME `result["bands"]` list, ranked by
      the identical `(class rank DESCENDING, distance_bps ascending, quality_score descending)` key
      `_select_best_band` already uses (`_CLASS_RANK`, `_distance_bps`), resolved by `min`'s
      first-of-tie stability over `compute_tradability`'s own served order. `None` when no band
      exists on the other side. Copy its `side`/`class`/`price_low`/`price_high`/`quality_score`
      verbatim into the row's `opposite_band` dict (renaming `class`→`band_class`,
      `quality_score`→`band_score` to match the row's own existing field names) plus its own
      `distance_bps` computed via the SAME `_distance_bps(opposite, close)` call. Zero new
      `BarStore` read, zero second `compute_tradability` call — everything is drawn from the SAME
      `result` this function already holds.
- [ ] Same function, same pass: bind `bands_by_class` — a plain count of `result["bands"]` under the
      four fixed keys `"A"`, `"B"`, `"C"`, `"unclassified"` (a band with `class: None` counts under
      `"unclassified"`), all four always present even at zero. No grade, threshold, weight, or
      quality number — a count only.
- [ ] Add both fields to the ranked-row dict literal (~:386-403), beside the existing
      `reference_close` field. Skip rows (`no_bars`/`no_basis`) never carry either field.
- [ ] Update the module's own row-shape docstring/comment documenting both new fields and the
      legacy-row (entirely-absent-key, never `null` for the row itself — `opposite_band` alone may
      be `null` when the canonical return holds no band on the other side) fallback contract,
      following the J-08/J-11/J-13 precedent immediately above it in the same function.
- [ ] Tests in `apps/backend/tests/test_desk_screen.py`: fixture-scoped golden asserting the exact
      `opposite_band` + `bands_by_class` per ranked row — including one row whose nearest opposite
      wall is within 25 bps, one whose nearest opposite wall is beyond 1,000 bps, and one whose
      nearest opposite band carries a `null` class — byte-identical row content on a re-run under
      identical pins; a unit test of the selector proving the honest `null` when the canonical
      return holds no band on the other side; a unit test proving the tie-break is stable across
      repeated calls on a tied fixture; a guard test asserting the row builder issues NO additional
      `BarStore` read and NO second `compute_tradability` call beyond the ones it already makes
      (call-count assertions, the J-11/J-13 precedent); a golden comparison proving the recorded
      rank order is byte-identical to what the same pins produced before this change
      (`_row_rank_key` untouched, appears only as unchanged CONTEXT in `git diff`).
- [ ] Confirm (test) the MCP `desk_screen` tool and `get_endpoint`'s `/research/` allowlist proxy
      both new fields with zero code change (byte-identity of the GET response; the 17-tool contract
      unaffected).

### Frontend
- [ ] `apps/frontend/lib/types.ts` `DeskScreenRow`: add `opposite_band?: {side: "support" |
      "resistance"; band_class: "A" | "B" | "C" | null; price_low: number; price_high: number;
      band_score: number; distance_bps: number} | null` and `bands_by_class?: {A: number; B: number;
      C: number; unclassified: number}` beside the already-typed `reference_close` field (the same
      optional-field, legacy-absent-key pattern `basis_as_of`/`history_sessions`/`reference_close`
      already use).
- [ ] `apps/frontend/app/desk/page.tsx` `DeskRow`: add one new `opposite` column cell rendering the
      row's own recorded `opposite_band` (e.g. `opposite resistance A 490.88–494.22 · 0.6 bps`), with
      an honest `"no band on the other side"` for a recorded `null` and the established legacy-absent
      copy `"opposite wall not recorded in this snapshot"` for a pre-iteration row — following the
      SAME rounded-display split the distance/score/basis/history/band cells already use. Add the
      matching `<th>opposite</th>` header cell to `DeskRowsTable`.
- [ ] `deskRowDrillInTitle`: extend the row's existing composite hover tooltip with one more line
      carrying the row's full-precision `bands_by_class` (e.g. `10 bands · A 10 · B 0 · C 0 ·
      unclassified 0`) — never a new per-cell `title` under the stretched drill-in anchor (the
      iter-6/iter-7 audit F2 lesson, applied proactively the same way basis/history/band already
      did).
- [ ] Confirm `apps/backend/tests/test_copy_discipline.py` passes unmodified against the new
      `opposite`/`bands_by_class` copy strings (no advice/imperative/prediction language).

### New user-facing capability
The operator (and any Claude/MCP reader of `desk_screen`) can see, for every ranked row, where the
nearest wall on the OTHER side of price sits — how close it is, what class it carries — and how many
walls of each class the row's own displayed wall was chosen from, instead of a page where nine
top-ranked rows read identically (`support · class A · 0.00 bps`) while their true opposite-side
spreads range from 0.6 to 6,067.7 bps.

### New information displayed
`opposite_band` (side, class, price range, band score, distance in bps of the nearest band on the
side NOT selected) and `bands_by_class` (a per-class count of how many bands `compute_tradability`
returned for that symbol), rendered in a new `opposite` column and in the row's composite hover
tooltip.

### New user actions
None — read-only render; no new button or control.

### UI surface changes
One new `opposite` column on the existing `/desk` ranked-rows table (`DeskRowsTable`/`DeskRow`); one
new line in the row's existing composite drill-in tooltip. No new page, no new section, no new nav
row.

### Product surface delta
`/desk`'s ranked table grows from ten to eleven columns; the row's existing hover tooltip gains one
more disclosed value. No other surface changes.

### Blueprint conformance
Desk section of the Information Architecture (`runs/goal-session-desk/state/blueprint.md`) — no new
home; this iteration extends the already-registered `/desk` canonical home's ranked table. A J-14 row
was added to the blueprint's Feature/journey homes table, the Navigation-skeleton Desk description
gained an iter-18 sentence, and the "Screen snapshots, rank rows, skip rows" Data-Contract row gained
an iter-18 addition note plus a matching `RESOLVED at iter-18` build-time-scope note (documentation
only, no new build scope beyond what is in this spec).

### Data-contract additions
`opposite_band: {side: "support"|"resistance", band_class: "A"|"B"|"C"|null, price_low: float,
price_high: float, band_score: float, distance_bps: float>=0} | null` and `bands_by_class: {A:
int>=0, B: int>=0, C: int>=0, unclassified: int>=0}` — both present on every ranked row of every NEW
screen snapshot from this iteration forward; entirely absent (not present as keys, not `null`) on
every ranked row recorded before this iteration and on all skip rows. Owner: `app/research/
desk_screen.py` (the already-registered owner of "Screen snapshots, rank rows, skip rows"). Serving
endpoint: `GET /research/desk/screen` (the already-registered endpoint — no new route, no new query
param, no new `Config` field, no new MCP tool; the `desk_screen` tool's byte-identical no-arg proxy
contract covers both fields automatically, and J-06's exactly-17-tool contract is unaffected). This
is an ADDITIVE extension of an already-registered row, never a second owner or a second endpoint for
either value.

## OUT OF SCOPE

- Any new Data-Contract row, new endpoint, new route, or new `Config` field.
- Any diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
  `desk_coverage.py` — both new values are selected out of the one `result["bands"]` list
  `desk_screen.py` already holds.
- Any change to the rank key (`band_class`, `distance_bps`, `band_score`, `symbol`) or the 5-pin
  snapshot key — this journey discloses, it never ranks, filters, gates, weights, or scores.
- Any threshold, "room"/"corridor width", proximity flag, or quality number computed anywhere — the
  disclosure is the nearest opposite band's own recorded values plus a plain count, nothing derived
  or graded further.
- Backfilling, rewriting, or recomputing any already-recorded screen snapshot — legacy rows keep
  their honest absent-field state forever; `/desk` renders it as `"opposite wall not recorded in this
  snapshot"`, never a value computed at read time.
- A CLI warmer for these fields (none of J-08/J-11/J-13 needed one either; the existing screen
  compute POST/CLI already serves the fields automatically once they land in `compute_screen`).
- Any WRITE to `apps/backend/.data` for evidence capture — a new screen compute for a
  not-already-recorded pin set, if needed for evidence, runs on a fixture-scoped rig only
  (iter-9/11/14/15/16 scoped-rig discipline), and any collision with an existing golden's target
  store is checked and disclosed first (iter-10 lesson).
- Re-recording J-09/J-10/J-11/J-12's already-CORRECT `[NEW]` demo walkthroughs — do not redo.
- Building a `/desk` "Universe ledger" section (rejected at iter-16, still out of scope).

## DEFINITION OF DONE

- [ ] J-14 passes via browser-qa-agent
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10,
      J-11, J-12, J-13) remain green (deterministic replay + LLM fallback — mechanically verified)
- [ ] No anti-goal violation introduced — single source of truth holds (one owner, one endpoint, zero
      duplicated computation), snapshots stay append-only and unedited, the briefing stays
      descriptive-only, no new statistic/gate/threshold is computed
- [ ] A `[NEW]`-flagged demo-narrator walkthrough (`Demo Verdict: RECORDED` + a non-empty gallery
      directory, never a same-named replay script) covers the briefing's opposite-wall disclosure end
      to end, narrated over POPULATED ranked rows on a fixture-scoped rig with a freshly computed
      screen (this same populated capture also closes iter-17's carried `evidence_makeup` gap for
      J-13, whose own walkthrough narrated only the legacy pre-fix state — not a separate DoD item,
      but note in the demo/results report if the same frames legibly show `reference_close`/`band`
      populated too)
- [ ] Full backend suite green; `Config().config_fingerprint()` prints `08e471b10130e1e2`; zero new
      `Config` fields; the `default`/`v1` engine-equivalence test passes byte-identical; MCP tool
      count is exactly 17; zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
      `StructureChart.tsx`; `tests/test_copy_discipline.py` green unmodified
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-18-dev.md`

## TESTING REQUIREMENTS

- Browser: J-14 (`/desk` ranked table shows the new `opposite` column with, in ONE screenshot, at
  least one row whose nearest opposite wall is within 25 bps and one whose nearest opposite wall is
  more than 1,000 bps away, both legible; a separate screenshot of a row tooltip carrying its
  `bands_by_class` line; a legacy snapshot's row shows the honest fallback; demo-narrator walkthrough
  over populated rows). Regression smoke: J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10,
  J-11, J-12, J-13.
- Unit/integration: `desk_screen.py` `opposite_band` selector (exact-value golden, near/far/null-class
  rows, byte-identical re-run under identical pins, honest null when no opposite band exists,
  tie-break stability, `merged_bars`/`compute_tradability` call-count guard, rank-order-unchanged),
  `bands_by_class` count correctness, MCP `desk_screen`/`get_endpoint` proxy byte-identity.
- Error cases: a pre-existing (legacy) screen snapshot's ranked rows carry no `opposite_band`/
  `bands_by_class` keys and the served response, the on-disk file, and its checksum are all
  byte-unchanged; a re-run under identical pins returns the existing already-recorded response rather
  than writing a new file.

Test-first contract:

- TC-1: given a fixture-scoped rig with a registered universe snapshot and bar store, when a NEW
  screen is computed for a screen_date not already recorded under the same five pins, then every
  ranked row's response carries an `opposite_band` field (or `null`) and a `bands_by_class` field
  with keys `A`/`B`/`C`/`unclassified`.
- TC-2: given that same new screen snapshot, when each ranked row's non-null `opposite_band`
  `side`/`band_class`/`price_low`/`price_high`/`band_score` are compared to the corresponding band in
  `GET /research/tradability?symbol=<sym>&as_of=<that snapshot's own as_of>`'s own `bands` list, then
  the values are byte-identical.
- TC-3: given the same new snapshot, when each ranked row's `opposite_band.distance_bps` is compared
  to the value the SAME `_distance_bps` formula produces against that row's own `reference_close`,
  then the two values match.
- TC-4: given the same new snapshot, when each ranked row's `bands_by_class` four values are summed,
  then the sum equals the length of that symbol's `GET /research/tradability` `bands` list.
- TC-5: given the same new snapshot, when its ranked-row symbol sequence is compared to the sequence
  the same five pins produced before this change (a golden fixture recorded pre-change, replayed
  post-change, plus `_row_rank_key`'s own source appearing only as unchanged CONTEXT in `git diff`),
  then the two sequences are byte-identical.
- TC-6: given the new screen snapshot, when the same compute is re-triggered under identical pins,
  then the store returns the already-recorded response byte-identical to the first, and no new file
  is written to disk.
- TC-7: given a screen snapshot recorded before this iteration's code landed, when
  `GET /research/desk/screen?date=<that date>` is called, then its ranked rows carry no
  `opposite_band`/`bands_by_class` keys (absent, not `null`), the file's on-disk checksum is
  unchanged from before this iteration, and `/desk` renders the honest `"opposite wall not recorded
  in this snapshot"` string for each of its rows.
- TC-8: given a symbol whose `compute_tradability` return holds bands on only ONE side of price, when
  that symbol's row is built, then `opposite_band` is `null` — never an invented or wrong-side band.
- TC-9: given a bands list containing two bands tied on `(class, distance_bps, quality_score)` on the
  opposite side, when the selector runs twice on the identical input, then it returns the same band
  both times (tie-break stability via `min`'s first-of-tie order).
- TC-10: given `desk_screen.py`'s row builder, when a screen is computed for N symbols with bars, then
  a call-count guard test asserts `compute_tradability` is invoked exactly once per symbol and
  `BarStore.merged_bars(symbol, "1d")` is invoked exactly once per symbol — no additional read beyond
  the ones iteration 17 already established.
- TC-11: given `apps/frontend/app/desk/page.tsx`'s source, when scanned for arithmetic deriving a
  distance, price, or band value outside the existing rendered fields, then no expression computes an
  opposite-band or bands-by-class value on the page — the frontend renders only what the endpoint
  serves.
- TC-12: given `/desk` after a T-9 clean rebuild, when a screen carrying `opposite_band` data is
  loaded in a real browser, then the ranked table's `opposite` column shows, in ONE screenshot, at
  least one ranked row whose nearest opposite wall is within 25 bps and one ranked row whose nearest
  opposite wall is more than 1,000 bps away, both legible; and a second screenshot shows a row's
  tooltip carrying its `bands_by_class` line.
- TC-13: given the full backend suite runs after this change, when `Config().config_fingerprint()` is
  read, then it prints `08e471b10130e1e2`; a diff of `tradability.py`/`levels.py`/`bars.py`/
  `bar_index.py`/`StructureChart.tsx` against the pre-iteration tree is empty; and zero new `Config`
  fields exist.
- TC-14: given `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` contract and a live call to
  the MCP `desk_screen` tool, when the suite runs, then the tool count is exactly 17 and the tool's
  JSON is byte-identical to the direct `GET /research/desk/screen` response for the same snapshot.
- TC-15: given `apps/backend/tests/test_copy_discipline.py`, when run after the `opposite` column and
  `bands_by_class` tooltip line land, then it passes unmodified (zero edits to the lint file itself,
  and the new copy strings contain no advice/imperative/prediction language).
- TC-16: given the demo-narrator lane runs at `full` depth (before scoring), when it records the
  `[NEW]`-flagged J-14 walkthrough on a fixture-scoped rig against a freshly computed, populated
  screen, then the resulting artifact shows `Demo Verdict: RECORDED` with a non-empty screenshot
  gallery narrating: the ranked table's new `opposite` column, a row whose nearest opposite wall is
  within 25 bps, a row whose nearest opposite wall is beyond 1,000 bps, a row tooltip's
  `bands_by_class` line, and a legacy row's honest `"opposite wall not recorded in this snapshot"`
  state.

## NOTES

- Applied lessons: iter-12/iter-13 (a `[NEW]`-flagged demo-narrator walkthrough clause forces `full`
  depth — the demo-narrator lane runs after scoring at `lean`); iter-9/iter-11/iter-14/iter-15/iter-16
  (state, in EVERY lane's own dispatch, which store root it serves against, and re-derive the rig
  path after any re-dispatch — never let a report's prose be the only evidence of isolation; scoped
  PORTS are not a scoped STORE); iter-10 (an evidence-only compute can silently collide with a stored
  golden — check the target store for an existing record under the same key first, and disclose any
  unavoidable collision); iter-16 (a shared Chrome instance can silently capture an unrelated app's
  page — assert the captured page's origin matches the rig's own base URL; a source-code read never
  satisfies a "in a real browser" test case); iter-17 (keep `Required-still-passing journeys:` on ONE
  physical line — the replay-lane parser truncates a wrapped continuation and silently drops
  journeys from BOTH the replay and the LLM-fallback check; never start a second `next dev` from
  `apps/frontend` while an ambient one is running — they share `.next` and the ambient page silently
  starts serving the scoped backend's API base).
- No assumption-ledger entry this iteration: J-14's steps and acceptance text are fully prescriptive
  (exact field names, exact source list/helper reuse, exact tie-break rule inherited from
  `_select_best_band`, exact rendering pattern, exact test scenarios) and leave no genuine
  interpretation gap for the decomposer to log.
- Carry-only, not this iteration's concern (do not redo, per iteration-state.md): J-12's
  `evidence_makeup: true` one-page re-capture of the earlier same-date view — ride it on whichever
  lane next touches `/desk`'s Screen History section, never as a standalone goal. J-13's
  `evidence_makeup: true` re-film is EXPECTED to close naturally as a side effect of this iteration's
  own required populated demo capture (see DEFINITION OF DONE) — but if the demo lane's frames happen
  not to legibly show `reference_close`/`band`, that remains a carry, not a new iteration's goal. The
  `[NEW]` walkthroughs already recorded for J-09/J-10/J-11/J-12 are CORRECT and must not be
  re-recorded.
