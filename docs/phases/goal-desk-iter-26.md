# Goal Iteration 26 — A top-up asks the vendor only for the bars the frozen store cannot already prove

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 26
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: J-17 is a brand-new, never-before-built full-stack journey whose interaction spans three modules with no existing single journey's own test coverage (`desk_topup_compute.py`'s new per-pair window-selection branch, `desk_topup_log.py`'s new fields/outcome value written by its one shared writer, and `/desk`'s Top-up Runs section render) — also satisfying the binding depth recommendation's own "brand-new full-stack journey" escape condition, since the evaluator's `evidence` recommendation for this iteration was computed from iteration 25's "Halt, confirm the finish" verdict, before the goal-proposer promoted J-17 this cycle (see `assumptions.md` iter-26 for the full override reasoning).
- **Frontend Present:** yes
- **Target journeys:** J-17
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16
- **Anti-goal reminders:**
  - No profit claims and no advice — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - Snapshots are append-only and pinned. Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - Every run is an explicit operator act. No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - The briefing describes, never advises. Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - The fingerprint pin does not move. All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*
  - The suite stays keyless and hermetic. Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*
  - The enhancement loop stays inside its box. The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Make the desk's top-up honest about what it actually asked the vendor for: derive each pair's
fetch window from the frozen `BarStore`'s own content instead of a wall-clock horizon, add an
honest `unchanged` outcome for a vendor call that returns nothing new, and surface both on
`/desk`'s existing Top-up Runs section — closing the one measured, uncovered Vision claim
("store-first ... never re-fetched") without adding any new page, column, or endpoint.

## BACKGROUND

Iteration 25 closed the session's 16-journey scope `GOAL_ACHIEVED` and was awaiting the
second-key confirm; the goal-proposer then promoted a tenth post-achievement journey, **J-17**
(`state/proposer-result.json`, score 0.86 vs. a 0.41 sibling not promoted), measured live against
the desk's own recorded ledger: the one real top-up run on file
(`topup-2026-07-29-5de907c83fc4`, 404 pairs) reports `0 reused / 390 fetched / 14 failed` —
`reused` has never once fired on a real run — because `_fetch_window_now()`'s window end is
wall-clock ("today") while `record_bar_series`'s store-first path is an exact-key
`(symbol, timeframe, window_start, window_end)` hit, so a daily-moving window can structurally
never land a reuse. For the 235 pairs the store already held before that run, it downloaded
276,714 bars to gain 13,533 (4.9%), and 174 of those 235 pairs gained ≤5 bars each. This
iteration's dispatch prompt inlines a binding `evidence` depth recommendation, computed from
iteration 25's own "Halt, confirm the finish" verdict — before J-17 existed. Since J-17 is a
brand-new, never-implemented full-stack journey (real backend logic + real frontend disclosure +
real Data-Contract additions), the depth-binding rule's own escape condition applies and this
iteration is dispatched `full` instead (see `assumptions.md` iter-26 for the full chain of
evidence behind that override, and the blueprint's new "RESOLVED at iter-26" note for the
build-time Data-Contract scope). Two applicable lessons: the iter-12/13 lesson (`lessons.md`) —
a `lean`-dispatched iteration cannot score a brand-new `[NEW]`-flagged walkthrough clause within
its own run — is why this cannot be lean even setting the structural trigger aside; and the
iter-23 lesson — the scoped-rig recipe lives in the DEVELOPER's `plan.md` (inherited from this
spec's NOTES) but NOT in the browser-qa lane's own slice unless explicitly checked — is restated
below because this iteration again needs a populated top-up run captured on a scoped rig, never
the operator's ambient `.data/` store.

## IN SCOPE

### Backend
- [ ] `desk_topup_compute.py`: derive each pair's fetch window from that pair's OWN frozen content
      via the canonical `BarStore.merged_bars(symbol, timeframe)` read (the same accessor
      `desk_screen.py`'s reference-close/history walk already uses) — three cases decided inside
      `_run_one_pair`: nothing frozen → the byte-identical full `_TOPUP_LOOKBACK_DAYS` window asked
      for today; frozen history shorter than the lookback start → the same full window; frozen
      history reaching the lookback start → a tail window `[pair's own newest frozen bar's UTC
      date, today]`. The end bound stays `_fetch_window_now()`'s wall-clock today, unchanged.
- [ ] Add exactly one new outcome value, `"unchanged"` (a vendor call ran and returned only bars
      already frozen), beside the existing `"reused"`, `"fetched"`, `"failed"` — a vendor's
      already-registered 409 answer (`BarSeriesAlreadyRegistered`, `routes.py:681`) on a tail-window
      request records `"unchanged"`, never `"failed"`.
- [ ] `desk_topup_log.py`: extend each per-pair outcome entry with `requested_window`,
      `store_frozen_from`, `store_frozen_through`, `window_basis` (`"tail"` | `"full_lookback"`),
      written once at a run's terminal state by the SAME single shared writer
      (`desk_topup_log.record_topup_run`) both the compute manager's resolve path and the CLI's
      `main` already call. Every run recorded before this iteration keeps its shape exactly as
      recorded (no backfill) — `GET /research/desk/topup/runs` serves legacy runs verbatim.
- [ ] Zero diff to `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`,
      `tradability.py`, `levels.py` — no new store, no new accessor, no second read of
      `bar_index`'s `window_end_utc`. No new `Config` field (`_TOPUP_LOOKBACK_DAYS` stays the
      module constant it is).

### Frontend
- [ ] `/desk`'s SHIPPED Top-up Runs section (no new section, no new control, no new ranked-table
      column — J-16's measured width contract stays untouched): extend the latest-run counts line
      to `N reused · N fetched · N unchanged · N failed`; add one descriptive line stating how many
      pairs asked for a tail window vs. the full lookback window; extend each already-rendered
      failed pair's row with its own recorded `requested_window`.
- [ ] Render the pre-iteration-26 legacy-run honest absence: `"window basis not recorded in this
      run"` wherever a run lacks the four new fields — never computed or backfilled at read time.
- [ ] Copy stays descriptive measurement only (counts and windows, never a saving/efficiency/speed
      or recommendation claim) — `tests/test_copy_discipline.py` stays green unmodified.

### New user-facing capability
The operator can see, per top-up run, whether each pair's fetch used a tail window or the full
lookback, an honest `unchanged` count when the vendor returned nothing new, and each failed
pair's own exact requested window — replacing what today reads as near-total "fetched"/"failed"
noise on every real run with an accurate account of what was actually asked for.

### New information displayed
Per-run outcome counts including `unchanged`; a tail-vs-full-lookback pair-count line; a
`requested_window` line on each already-rendered failed pair.

### New user actions
None — the existing Top-up button and its trigger/poll/cancel flow are unchanged; this is a
disclosure enhancement on an already-shipped section.

### UI surface changes
Top-up Runs section content only (no new page, no new nav row, no new control, no new
ranked-table column).

### Product surface delta
`/desk`'s Top-up Runs section becomes materially more informative about what a top-up actually
did, without adding surface area.

### Blueprint conformance
Desk nav home (already registered, `blueprint.md` Information Architecture). This iteration
extends the ALREADY-REGISTERED "Top-up run records (per-run outcome ledger)" Data-Contract row
(owner `desk_topup_log.py`, endpoint `GET /research/desk/topup/runs`) — see that row's new
"iter-26 addition (J-17)" note and the file's new "RESOLVED at iter-26" tail note, both already
written into `runs/goal-session-desk/state/blueprint.md`.

### Data-contract additions
All four fields below are additive to each **per-pair outcome entry** of the ALREADY-REGISTERED
"Top-up run records" row — same owner (`desk_topup_log.py`), same endpoint
(`GET /research/desk/topup/runs`), no new row, no new endpoint:
- `requested_window: {start: str, end: str}` — the exact window that pair's fetch call sent this run.
- `store_frozen_from: str | null` — that pair's own earliest frozen bar BEFORE this run's fetch (`null` if nothing was frozen).
- `store_frozen_through: str | null` — that pair's own newest frozen bar BEFORE this run's fetch (`null` if nothing was frozen).
- `window_basis: "tail" | "full_lookback"` — which of the two window-selection branches this pair's request used.
- `outcome` enum gains one new value: `"unchanged"` (alongside the existing `"reused"` | `"fetched"` | `"failed"`).

## OUT OF SCOPE

- The backlogged sibling proposal from this cycle, `desk-screen-run-ledger-and-member-failure-isolation` (score 0.41 vs. J-17's 0.86) — not promoted, not built this iteration.
- Any diff to `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `StructureChart.tsx`, `PriceChart.tsx` — zero diff stays law.
- Any new ranked-table column or any change to J-16's measured `scrollWidth`/row-height contract.
- Any new `Config` field — the window derivation reads only the existing canonical `BarStore` accessor and the existing `_TOPUP_LOOKBACK_DAYS` constant.
- A real ~100-symbol live Yahoo top-up run — stays an operator-run act reported honestly, never a CI gate; all tests are fixture-scoped with the suite's own injected fake adapter.
- Editing any EXISTING test's assertions in `test_desk_topup_compute.py` (including TC-7 "second run is all-reused with zero vendor calls" and TC-8 resumability) — they must pass unmodified; if any genuinely pins the shipped window for a pair whose frozen history already reaches the lookback start, disclose it in the iteration record rather than edit the test.
- Writing to the operator's ambient `apps/backend/.data/` store during evidence capture — the populated top-up run needed for the browser screenshot and demo walkthrough is recorded on a fresh, fixture-scoped copy of `.data/` (the iter-9/11/14/15/17/19/20/21/22/23 scoped-rig precedent), never the ambient store.

## DEFINITION OF DONE

- [ ] J-17 passes via browser-qa-agent
- [ ] Required-still-passing journeys (J-01..J-16) remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced
- [ ] Full backend suite green with zero regressions; `test_desk_topup_compute.py`'s existing TC-7/TC-8 and every other existing test pass unmodified
- [ ] `Config().config_fingerprint()` still reads `08e471b10130e1e2`; zero new `Config` fields; MCP tool count still exactly 17
- [ ] Every previously recorded universe/screen/top-up/reconciliation record file proven byte-identical before/after (SHA-256 listing) — append-only proof
- [ ] A `[NEW]`-flagged demo-narrator walkthrough covers J-17's window disclosure end to end, narrated over a populated run
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-26-dev.md`

## TESTING REQUIREMENTS

- Browser: J-17 (Top-up Runs section on `/desk`, 1440×900 viewport, no horizontal scroll); regression smoke over J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16 via stored golden replay
- Unit/integration: `test_desk_topup_compute.py` — window-selection branch (tail vs. full lookback vs. nothing-frozen), the new `unchanged` outcome, and byte-identity of every pre-existing test; `test_desk_topup_log.py` (or equivalent) — new field shapes + legacy-run honest-absence rendering; a source-introspection guard proving the window derivation reads `BarStore.merged_bars` and never `bar_index.window_end_utc`
- Error cases: a pair whose vendor call raises `BarSeriesAlreadyRegistered` (409) on a tail-window request must record `"unchanged"`, never `"failed"`; a run interrupted before its terminal write must leave NO record (the append-only rail); an unknown/missing `window_basis`/`requested_window` on a legacy run must render the honest fallback text, never a computed guess or a crash

Test-first contract:

- TC-1: given a fixture-scoped fake adapter with a pair whose planted frozen bars reach back past `_TOPUP_LOOKBACK_DAYS`, when a top-up run walks that pair, then the fake adapter receives a window `[that pair's own newest frozen bar's UTC date, today]` and the recorded outcome entry's `window_basis` reads `"tail"`.
- TC-2: given a fixture-scoped fake adapter with a pair holding NO frozen bars, when a top-up run walks that pair, then the fake adapter receives the byte-identical full `_TOPUP_LOOKBACK_DAYS` window it receives today, and the recorded entry's `window_basis` reads `"full_lookback"`.
- TC-3: given a fixture-scoped fake adapter with a pair whose frozen history is shorter than the lookback window, when a top-up run walks that pair, then the fake adapter receives the same full `_TOPUP_LOOKBACK_DAYS` window as TC-2, and the recorded entry's `window_basis` reads `"full_lookback"`.
- TC-4: given a fixture-scoped fake adapter whose vendor answer for a pair returns only bars already frozen in the store, when the run resolves that pair, then the recorded outcome reads `"unchanged"` (not `"failed"`), no second bar-series file is written, and `requested_window` + `store_frozen_through` are both present on the recorded entry.
- TC-5: given every EXISTING test in `test_desk_topup_compute.py` (including TC-7 "a second run is all-reused with zero vendor calls" and TC-8 resumability), when the suite runs after this iteration's change, then every one passes unmodified with zero edits.
- TC-6: given a fixture-scoped rig with a populated real-shaped top-up run recorded via this iteration's code (never the ambient `.data/` store), when the browser loads `/desk`'s Top-up Runs section at a 1440×900 viewport, then the latest-run counts line reads `N reused · N fetched · N unchanged · N failed` with at least one `unchanged` count > 0, a descriptive line states how many pairs asked for a tail window vs. a full lookback window, and at least one failed pair's row shows its own recorded `requested_window` — all legible in one screenshot with no horizontal scroll.
- TC-7: given a top-up run recorded BEFORE this iteration's code shipped (lacking the four new fields), when `/desk` renders its Top-up Runs entry, then it shows the literal text `"window basis not recorded in this run"` rather than a computed or backfilled value.
- TC-8: given the backend suite after this change, when `Config().config_fingerprint()` is printed, then it reads exactly `08e471b10130e1e2`, zero new `Config` fields exist, and the MCP tool count is exactly 17.
- TC-9: given SHA-256 checksums of every recorded universe/screen/top-up/reconciliation file captured before this iteration's fixture-scoped tests run, when compared to checksums captured after, then every one is byte-identical (append-only proof; the real store is never touched by tests or by evidence capture).
- TC-10: given a `[NEW]`-flagged demo-narrator walkthrough recorded over the TC-6 populated fixture-scoped rig, when its frames are opened directly, then the four-outcome counts line and the tail-vs-full-lookback line are both visible inside the frame, and every click target names exactly one row/element (never a locator matching a hundred cells at once, per the iter-20/23/25 lessons).

## NOTES

- **Scoped-rig recipe (repeat in the browser-qa dispatch, per the iter-23 lesson):** the populated
  top-up run needed for TC-6/TC-10 must be recorded on a FRESH, fixture-scoped copy of
  `apps/backend/.data` (the iter-9/11/14/15/17/19/20/21/22/23 precedent) — never trigger a real
  top-up against the operator's ambient store. Verify the serving process actually points at the
  scoped copy (a direct `curl` cross-check, not `location.origin` alone) before capturing.
- **Window-basis key naming and outcome enum placement are build discretion** (goal.md only
  specifies the two `window_basis` string values and the one new outcome value); mirror the
  existing `_bands_by_class`/`topupOutcomeCounts` naming style for consistency.
- **Do not redo** (binding, from iteration-state): J-16's layout (`table-fixed` + 13-col
  `<colgroup>`, `flex-nowrap` coverage badges) is DONE and measured — do not re-tune widths or add
  a column; `band `/`opposite ` in-cell prefixes MUST stay (golden-script guard); never script a
  `click` on a cell inside a `/desk` ranked or skipped row (stretched `absolute inset-0` anchor —
  use `expect`-only text assertions); the accepted non-defects list (2/100 rows at 63px, 8 stacked
  `/desk` sections, `.mcp.json` pointing at `:8000`, goal.md's stale host-mask paragraph) stays as
  is.
- **Second-key confirm carryover:** iteration 25's three non-blocking follow-ups (J-16 film
  `RECORDED_WITH_NOTES` → `RECORDED` via `expect`-only assertions; narration wording pass; the
  replay tool's same-frame duplication) remain open, optional, and non-blocking — they are NOT
  in scope this iteration and do not gate J-17's own DoD. If the evaluator has capacity, note their
  status; otherwise carry them forward again.
