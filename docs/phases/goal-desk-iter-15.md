# Goal Iteration 15 — J-11: history-depth disclosure on every ranked briefing row

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 15
- **Mode:** next
- **Depth:** full
- **Full trigger:** 2 — adds `history_sessions`/`history_start` to the PERSISTED screen-snapshot
  row schema (append-only JSON, one new pair of fields on every future ranked row); separately, the
  binding iter-12/13 lesson requires `full` depth for ANY journey whose acceptance names a
  `[NEW]`-flagged demo-narrator walkthrough, since at `lean` depth the demo-narrator lane runs AFTER
  the goal-evaluator and the clause is structurally unscoreable.
- **Frontend Present:** yes
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10
- **Anti-goal reminders:**
  - No lookahead — every value computed as-of T uses only events/bars fully completed at T.
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint,
    and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations.
  - Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
  - Snapshots are append-only and pinned. Universe and screen snapshots are dated, checksummed,
    append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint,
    bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or
    rewritten — a new run is a new snapshot.
  - The briefing describes, never advises. Desk copy is descriptive measurement only — no advice,
    imperative, prediction, or ranking language implying action ("buy", "watch this",
    "opportunity"); the copy-discipline lint stays green unmodified.
  - The fingerprint pin does not move. All new Config fields take Path A (exclusion + stability
    test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted
    unchanged by the sentinel every iteration.
  - The enhancement loop stays inside its box. The goal-proposer may append journeys ONLY inside
    the `AUTO:journeys` marker block — it MUST NOT edit human-authored journeys, this Anti-goals
    section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth
    (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and
    include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop
    alive is a failure.

## GOAL

Every ranked row on the `/desk` briefing discloses how many completed daily sessions (and from
what start date) its wall was measured over, so the operator can tell a 27-session listing apart
from a 500-session name without leaving the page.

## BACKGROUND

Era B closed `GOAL_ACHIEVED` at iter-13 and again at iter-14 (J-10); the goal-proposer's own
`AUTO:journeys` addition, J-11, reopened it for exactly one more disclosure journey, structurally
identical to J-08's iter-9 build: two new fields added to the ALREADY-registered "Screen snapshots,
rank rows, skip rows" Data-Contract row, derived inside the one ascending
`BarStore.merged_bars(symbol, "1d")` walk `_resolve_reference_close` (`desk_screen.py:239`) already
performs, with zero new store read, zero new `Config` field, and no rank-key change. This iteration
is dispatched at `full` depth for two independent reasons, either alone sufficient: (1) it changes
the persisted schema of the append-only screen-snapshot rows (Full trigger 2); (2) J-11's acceptance
names a `[NEW]`-flagged demo-narrator walkthrough, and the session's own binding lesson (iter-12
`ESCALATE`, corrected at iter-13) proved that clause is unscoreable at `lean` depth because the
demo-narrator lane runs after the evaluator there. Two more lessons apply directly: iter-9's lesson
that a live-measured acceptance number decays with real time — goal.md's own J-11 rationale cites a
specific screen (`screen-2026-07-29-ce0d82b8e9bf`, HONA #8 on 27 sessions, several names on 500) as
the WORKED EXAMPLE proving the split exists, not as a literal number this iteration must reproduce
byte-for-byte; the dev/QA lanes should independently confirm a genuine short/long split exists in
whatever rig they use rather than trusting the cited numbers verbatim. And iter-14's lesson that a
fixture-scoped rig lives under the pipeline's PID-scoped scratch dir and does not survive
re-dispatch — every lane (dev, browser-QA, demo-narrator) must state its own rig path and re-derive
it if re-dispatched, never fall back to the ambient `apps/backend/.data` store.

## IN SCOPE

### Backend
- [ ] Extend the existing ascending walk in `_resolve_reference_close` (`desk_screen.py:239`,
  which already iterates `BarStore.merged_bars(symbol, "1d")` to find the bar matching
  `basis_as_of`) to also derive, in that SAME walk, `history_sessions` (the count of bars at or
  before `basis_as_of`) and `history_start` (the earliest such bar's own timestamp, formatted
  through the same `_iso` helper `basis_as_of` uses) — no second store read, no new accessor on
  `bars.py`/`bar_index.py`.
- [ ] Attach `history_sessions`/`history_start` to each RANKED row in `compute_screen`
  (`desk_screen.py`, the `elif` branch building rows ~lines 342-359), alongside the existing
  `basis_as_of`/`basis_age_days` fields. Skip rows (`no_bars`/`no_basis`) carry neither, matching
  the J-08 precedent.
- [ ] Extend `desk_screen.py`'s module docstring with a "History disclosure" section documenting
  the new fields, mirroring the existing "Basis disclosure" section's structure and honesty
  contract (legacy rows omit the keys entirely, never present as `null`).
- [ ] Fixture-scoped tests in `test_desk_screen.py` mirroring the J-08 test block: golden per-row
  `history_sessions`/`history_start` including one short-history member and one long-history
  member; byte-identical re-run under identical pins; a legacy-row-absence test (old snapshot rows
  never backfilled, keys absent not null); a zero-extra-`BarStore`-read guard test (assert
  `merged_bars` call count is unchanged by this addition); an MCP `desk_screen` proxy pass-through
  check; `tests/test_copy_discipline.py` stays green unmodified.

### Frontend
- [ ] `apps/frontend/lib/types.ts` `DeskScreenRow` (~:801): add `history_sessions: number | null`
  and `history_start: string | null`, mirroring the existing `basis_as_of`/`basis_age_days`
  optional-field pattern (loose `== null` check for the legacy-absence case, per the pattern at
  `types.ts:812`).
- [ ] `apps/frontend/app/desk/page.tsx`: a descriptive `history` column beside the existing `basis`
  column on the ranked table (e.g. `history 500 sessions · from 2024-07-25`), with the honest
  `"history not recorded in this snapshot"` fallback for legacy rows (mirrors the existing
  basis-column pattern at ~lines 236/318), and full-precision `history_start` folded into the row
  anchor's existing composite hover tooltip (the iter-7 F2 consolidation pattern) — zero change to
  click geometry, zero change to any other column or section.

### New user-facing capability
The operator can see, per ranked row on `/desk`, how many completed daily sessions (and from what
start date) the row's wall was measured over, without leaving the page or opening `/structure`.

### New information displayed
`history_sessions` (int >= 0) and `history_start` (ISO 8601 date-time string or absent) per ranked
row, rendered as a new `history` column plus two additional lines in the row's existing composite
hover tooltip.

### New user actions
None — disclosure only, no new button, control, or interactive element.

### UI surface changes
`/desk` ranked table gains one column (`history`); the row drill-in anchor's composite hover
tooltip gains the `history_start` detail. No other page, section, or button changes.

### Product surface delta
`/desk`'s briefing table now discloses history depth alongside band/basis/coverage/tick-evidence —
no new page, no new nav entry, no new endpoint, no new MCP tool.

### Blueprint conformance
Desk nav section, `/desk` canonical home — the SAME page J-04/J-05/J-08/J-09/J-10 already
registered in `blueprint.md`'s Information Architecture. No new Information-Architecture entry;
this iteration's Feature/journey-homes and Data-Contract edits are additive-only (see the
blueprint edits made alongside this spec).

### Data-contract additions
`history_sessions: int >= 0` and `history_start: str | null` (ISO 8601) — NEW fields on the
ALREADY-registered "Screen snapshots, rank rows, skip rows" Data-Contract row. Owner: 
`app/research/desk_screen.py` (unchanged module). Serving endpoint: `GET /research/desk/screen`
(unchanged — no new endpoint, no new MCP tool; `desk_screen`'s existing byte-identical GET-proxy
contract covers the new fields automatically). Registered in `blueprint.md` alongside this spec,
per the J-08 iter-9 precedent (an "iter-15 addition" note on the same row, plus a new
"RESOLVED at iter-15" scope note and a J-11 Feature/journey-homes entry).

## OUT OF SCOPE

- No change to rank order/key — `_row_rank_key` and the `(band_class, distance_bps, band_score,
  symbol)` tuple stay byte-unchanged; this journey discloses, it never ranks, filters, gates,
  weights, or scores (per goal.md's own explicit Non-Goals text for J-11).
- No new `Config` field, no fingerprint move — `08e471b10130e1e2` stays pinned.
- No new page, no new nav entry, no new MCP tool (17-tool contract unchanged).
- No backfill of legacy screen snapshots — history fields are ABSENT (never `null`) on rows
  recorded before this iteration, matching the basis-field convention exactly.
- No change to `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`,
  `PriceChart.tsx`, or any frozen research computation.
- No click-through or new interactive control tied to history (disclosure only, matching J-08's
  non-interactive column precedent — no threshold, quality score, or "enough history" judgement
  anywhere).
- No touch of the Top-up Runs / Index Reconciliation sections' own content — only their SHARED
  page layout may shift vertically if the new column widens the ranked table.

## DEFINITION OF DONE

- [ ] J-11 passes via browser-qa-agent — `/desk` shows the `history` column with a
  `history_sessions <= 60` row and a `history_sessions >= 400` row legible in one screenshot after
  a T-9 clean rebuild.
- [ ] Required-still-passing journeys (J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10) remain green
  — deterministic replay + LLM fallback.
- [ ] No anti-goal violation introduced (no lookahead, single source of truth, append-only rail,
  fingerprint pin, copy discipline all hold, enhancement-loop box respected).
- [ ] Full backend suite green, `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new
  `Config` fields, MCP tool count still exactly 17, `tests/test_copy_discipline.py` green
  unmodified; no regressions.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough covers the briefing's history disclosure end to
  end (dispatched at `full` depth, so the lane runs before the evaluator scores it).
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-15-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-11 (new journey — golden replay script to be recorded this iteration), regression
  smoke over J-04/J-05/J-08/J-10's existing `/desk` replay scripts.
- Unit/integration: `desk_screen.py` new-field derivation inside the existing walk, byte-identical
  re-run under identical pins, legacy-row absence, zero-extra-store-read guard, MCP proxy
  pass-through, copy-discipline lint.
- Error cases: skip rows (`no_bars`/`no_basis`) must never carry the new fields; a member whose
  basis resolves to the very first bar in its own series (`history_sessions == 1`) must not
  off-by-one.

Test-first contract:

- TC-1: given a fixture-scoped screen with a member whose merged `1d` bars include N bars at or
  before its own `basis_as_of`, when the screen is computed, then that member's ranked row carries
  `history_sessions == N` and `history_start` equal to the earliest of those N bars' own timestamp
  (formatted via the same `_iso` helper `basis_as_of` uses).
- TC-2: given the same fixture, when the screen is computed for a short-history member (e.g. <= 5
  recorded daily bars) and a long-history member (e.g. >= 400 recorded daily bars) in the same run,
  then the two rows carry visibly different `history_sessions` values reflecting each member's own
  recorded series length.
- TC-3: given a screen already recorded once, when the identical pins (screen_date, as_of,
  universe_snapshot_id, config_fingerprint, bar_store_signature) trigger a second compute, then the
  endpoint returns the existing snapshot unchanged (no duplicate file written) and every ranked
  row's `history_sessions`/`history_start` are byte-identical to the first recording.
- TC-4: given a screen snapshot recorded BEFORE this iteration (no `history_sessions`/
  `history_start` keys on its rows), when `GET /research/desk/screen?date=<that date>` is called,
  then each ranked row in the response omits both keys entirely (never present as `null`), and
  `/desk` renders that row's history cell as `"history not recorded in this snapshot"`.
- TC-5: given a skip row (`reason: "no_bars"` or `"no_basis"`), when a screen is computed, then
  that skip row carries neither `history_sessions` nor `history_start`.
- TC-6: given `compute_screen`'s row-builder instrumented to count `BarStore.merged_bars` calls per
  symbol, when a screen is computed, then each ranked symbol shows exactly ONE
  `merged_bars(symbol, "1d")` call (no additional store read was added to derive the new fields).
- TC-7: given a ranked row's `history_sessions`/`history_start`, when compared against
  `GET /research/candles?symbol=<sym>&timeframe=1d`'s own merged, price-less-row-excluded response
  filtered to bars at or before that row's own `basis_as_of`, then the row's `history_sessions`
  equals that filtered count and `history_start` equals that filtered response's earliest bar
  timestamp (single-source-of-truth proof).
- TC-8: given a real browser session against a T-9 clean rebuild with a computed screen, when
  `/desk` is loaded, then the ranked table's `history` column shows at least one row with
  `history_sessions <= 60` and at least one row with `history_sessions >= 400` legible in the SAME
  screenshot.
- TC-9: given the same browser session, when the operator hovers a ranked row's drill-in anchor,
  then the composite tooltip includes that row's own `history_start` date alongside the existing
  basis/distance/score details, with zero change to click geometry.
- TC-10: given the full backend suite and fingerprint sentinel, when re-run after this change, then
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`, zero new `Config` fields exist,
  the MCP tool count is still exactly 17, and `tests/test_copy_discipline.py` passes unmodified.
- TC-11: given a `[NEW]`-flagged demo-narrator walkthrough dispatched at `full` depth, when it is
  recorded against a fixture-scoped rig carrying a computed screen, then it narrates and
  screenshots the briefing's history disclosure (at least one short-history and one long-history
  row visible) in one artifact.

## NOTES

- **Rig discipline (iter-14 lesson):** every lane (dev, browser-QA, demo-narrator) must state its
  own fixture-scoped rig path and re-derive it fresh if re-dispatched — a rig from a prior pass does
  not survive a re-dispatch's new PID-scoped scratch dir. None of this journey's evidence is a
  one-way-door capture (unlike J-09/J-10's honest-empty panels) — a screen can be recomputed freely
  on the same rig without breaching the append-only rail, since re-filming does not require
  deleting any record, only computing a fresh screen if the existing one lacks a wide session
  split.
- **Golden-collision discipline (iter-10 lesson):** if this iteration's evidence lane computes a
  NEW screen into a scoped rig that an existing golden script (`J-04.json`, `J-05.json`,
  `J-08.json`) also replays against (e.g. via "the latest screen" lookups), check for a collision
  before recording and disclose it in the results report if unavoidable.
- **Live-measured-number discipline (iter-9 lesson):** goal.md's own J-11 rationale cites a specific
  real screen (`screen-2026-07-29-ce0d82b8e9bf`) as a WORKED EXAMPLE that a wide session-count split
  genuinely exists (HONA #8 at 27 sessions beside several names at 500) — this is evidence the
  acceptance is reachable, not a literal number this iteration's fixture-scoped tests must
  reproduce byte-for-byte. The dev/QA lanes should independently confirm a genuine short/long split
  exists in whatever rig they use (fixture-scoped for tests; a scoped copy of the real `.data/` or
  an equivalent fixture for the TC-8 browser screenshot) rather than assuming the cited numbers are
  still current.
- **Copy discipline reminder:** the `history` column and its tooltip text must stay pure
  descriptive measurement (a count and a date) — no "enough history", "reliable", "confidence", or
  similar judgement language anywhere; `tests/test_copy_discipline.py`'s frontend-literal lint
  covers the new copy automatically.
- **Do not redo:** everything the iteration-state's "Do not redo" list names for J-01–J-10 stays
  binding — this iteration touches only `desk_screen.py`'s row-builder and `/desk`'s ranked-table
  rendering; the Top-up Runs and Index Reconciliation sections, the universe/coverage subsystem,
  and every kept `/`/`/structure` surface are untouched.
