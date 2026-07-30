# Goal Iteration 23 — Wall-composition disclosure on ranked /desk rows (J-15)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 23
- **Mode:** next
- **Depth:** full
- **Full trigger:** 4 — brand-new full-stack journey: backend `desk_screen.py` row-builder work AND frontend `/desk` column work, with three real Data-Contract additions, for J-15, a never-before-implemented journey the proposer just appended
- **Frontend Present:** yes
- **Target journeys:** J-15
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14
- **Anti-goal reminders:**
  - Single source of truth: each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - Snapshots are append-only and pinned. Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - The briefing describes, never advises. Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - No new statistics, gates, or strategies. No probability/expectancy/edge claims on any desk surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a future era). *(critical)*
  - The fingerprint pin does not move. All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*
  - Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - The enhancement loop stays inside its box. The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Every ranked `/desk` row honestly discloses what its selected wall is actually made of — how many
levels built it, whether it is a round-number band, and their per-timeframe split — by copying three
new fields verbatim from the same `_select_best_band` band `compute_tradability` already returns.

## BACKGROUND

Iteration 22 was `GOAL_ACHIEVED` and CONFIRMED (two-key), closing the era's last open item (J-14's
tooltip photograph). The session opted into continuous improvement: the goal-proposer surveyed the
product (`state/proposer-result.json`) and, measuring live against the canonical
`compute_tradability` owner for all 100 ranked rows of `screen-2026-07-29-2a57de4e7415`, found that
`member_count` (1 to 4,014, quartiles 19/45.5/87) and `round_number` (true on 16/100) are recorded on
every selected band inside `tradability.py` but never copied onto a screen row nor rendered anywhere
on `/desk` — while `/structure`'s own band table already renders both for the identical band. It
promoted this as **J-15**, appended inside goal.md's `AUTO:journeys` block (journey-history.json does
not yet contain J-15 — this is its first build). This is a genuinely new, never-implemented,
full-stack journey (backend row-builder + frontend column + three real Data-Contract additions), so
it satisfies full-depth escape condition 4 even though the evaluator's own last recommendation
(`evidence`) predates the proposer's extension and does not apply to code work. Journey-history shows
zero other FAILING/PARTIAL journeys, so this is the only target this iteration needs.

Lessons applied: (1) iter-9/11/14/15/17/19/20/21/22 — never write a screen/universe snapshot into
`apps/backend/.data`; the new screen this journey computes for evidence MUST land in a fixture-scoped
copy. (2) iter-12 — a `lean`-dispatched iteration cannot close a brand-new `[NEW]`-flagged
demo-narrator walkthrough within its own run (the demo lane runs after the evaluator at lean depth);
this iteration is `full` partly for that reason. (3) iter-17 — keep `Target journeys:` and
`Required-still-passing journeys:` each on ONE physical line (the replay-lane parser reads only the
first line). (4) iter-18 — when a spec bullet paraphrases a goal.md rule, it must not silently
override the literal text; the IN SCOPE bullets below quote goal.md's own field names and sources
rather than re-deriving them.

## IN SCOPE

### Backend
- [ ] In `apps/backend/app/research/desk_screen.py`'s ranked-row builder, copy `band_member_count`
      (int) and `band_round_number` (bool) VERBATIM from the SAME band dict `_select_best_band`
      already returns (that band's own `member_count`/`round_number` keys, `tradability.py:343`) —
      zero second `compute_tradability` call, zero second `BarStore` read
- [ ] Add `band_member_timeframes` (dict[str, int]): a plain tally of that SAME band's own `members`
      list by each member's own `timeframe`, mirroring the `_bands_by_class` precedent
      (`desk_screen.py:298`) — keys are exactly the timeframes present among those members in a
      deterministic order (developer's choice; keep it stable across runs and match it in the golden
      test), values sum to `band_member_count`, a timeframe with no member in this band is simply
      absent (never a fabricated zero)
- [ ] The band's own `members` list itself is never copied onto the row; no member price /
      `touch_count` / `strength` is copied
- [ ] Skip rows carry none of the three new fields (the J-08/J-11/J-13/J-14 shape)
- [ ] Legacy (pre-iteration) snapshots keep their stored shape and checksum unchanged; `GET
      /research/desk/screen` serves them exactly as recorded — never backfilled, never computed at
      read time
- [ ] Rank key (`band_class`, `distance_bps`, `band_score`, `symbol`) and `_row_rank_key` take zero
      diff — this journey discloses only
- [ ] Fixture-scoped tests: exact per-row assertions for `band_member_count`/`band_round_number`/
      `band_member_timeframes`, including one row whose band holds a single member (zero-width
      `price_low == price_high`) and one row whose band is dominated by intraday (`1m`/`5m`) members;
      the `sum(band_member_timeframes.values()) == band_member_count` invariant on every ranked row;
      byte-identical row content on a same-pins re-run; a call-count guard proving no additional
      `BarStore` read and no second `compute_tradability` call; a golden comparison proving the
      recorded rank order is byte-identical to what the same pins produced before this change
- [ ] Confirm the MCP `desk_screen` tool stays a byte-identical no-arg GET proxy (no code change
      expected) and the tool count stays exactly 17

### Frontend
- [ ] Add one new `levels` column to the `/desk` ranked table (`apps/frontend/app/desk/page.tsx`),
      beside the existing `band`/`opposite` columns, rendering each row's own recorded
      `band_member_count` + `band_member_timeframes` (e.g. `155 levels · 1d 68 · 1h 57 · 4h 19 · 1w
      11`) plus the same "round number" badge `/structure`'s own band table already renders for the
      identical field (`apps/frontend/app/structure/page.tsx:612/619`) — reuse that badge's existing
      style/component, do not build a new one
- [ ] Render rows from a legacy snapshot (missing the three new fields) with the honest
      `"composition not recorded in this snapshot"` state — the established J-08/J-11/J-13/J-14
      pattern (`page.tsx:383/392/407/420`)
- [ ] No new row `title` tooltip: every new value is an exact integer or boolean (no rounding), so no
      full-precision-on-hover need exists for this journey
- [ ] `tests/test_copy_discipline.py` stays green unmodified

### New user-facing capability
The operator (and Claude via MCP) can see, per ranked `/desk` row, how many levels its wall is built
of, whether it is a round-number band, and the per-timeframe split of those levels — the same
composition detail `/structure`'s own band table already shows for the identical band.

### New information displayed
`band_member_count`, `band_round_number`, `band_member_timeframes` per ranked row, rendered as a new
`levels` column plus a reused "round number" badge.

### New user actions
None — pure disclosure, no new button or control.

### UI surface changes
`/desk` ranked table gains one column (`levels`); no new page, no new section, no new control.

### Product surface delta
`/desk`'s ranked rows now describe wall composition the way `/structure`'s band table already does,
closing the disclosure gap the goal-proposer measured (top-ranked rows reading identically at
"support · Class A · 0.00 bps" while their walls range from 2 to 609+ levels).

### Blueprint conformance
Desk canonical home (`/desk`), the ALREADY-REGISTERED "Screen snapshots, rank rows, skip rows" Data
Contract row in `runs/goal-session-desk/state/blueprint.md` — additive extension only. No new page, no
nav-skeleton change. The blueprint's Feature/journey-homes table and that Data-Contract row's notes
were updated this iteration (RESOLVED-at-iter-23 note) BEFORE this spec was written.

### Data-contract additions
- `band_member_count: int >= 1` — computed by `apps/backend/app/research/desk_screen.py` (copied
  verbatim from the selected band's own `member_count`, `tradability.py:343`), served by `GET
  /research/desk/screen` (existing endpoint, no new route)
- `band_round_number: bool` — same owner/endpoint, copied verbatim from the selected band's own
  `round_number`
- `band_member_timeframes: dict[str, int]` — same owner/endpoint; a plain per-timeframe tally of that
  SAME band's own `members` list; keys are the timeframes present among those members in a
  deterministic order; values sum to `band_member_count`; a timeframe absent among the band's own
  members is simply absent, never a fabricated zero

No second computation, no second store read, no new endpoint, no new `Config` field, no new MCP tool.

## OUT OF SCOPE

- Any change to `_select_best_band`, `_select_opposite_band`, `_row_rank_key`, `tradability.py`,
  `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `StructureChart.tsx`,
  `PriceChart.tsx`, `config.py`, `engine/` — zero diff, per "Do not redo"
- Any new statistic, gate, threshold, or judgement about band quality ("confluence quality",
  "evidence depth", intraday-share ratio) — this journey discloses, it never scores
- Copying the band's own `members` list, or any member price/`touch_count`/`strength`, onto the row
- A new row `title` tooltip (not needed — all three new values are exact, unrounded)
- Backfilling any pre-iteration snapshot with the new fields
- A new MCP tool, a new `Config` field, or any change to the 17-tool contract
- `desk-live-coverage-view-on-page` and `desk-briefing-rank-position-column` (backlogged proposals
  the proposer explicitly did NOT promote this cycle)
- The still-running qa-rig housekeeping item (`project-extensions/qa-rig/xrig.sh down`) — operator's
  own task, not this iteration's

## DEFINITION OF DONE

- [ ] J-15 passes via browser-qa-agent
- [ ] Required-still-passing journeys (J-01..J-14) remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-23-dev.md`
- [ ] `band_member_count`/`band_round_number`/`band_member_timeframes` recorded on every ranked row
      of a NEW fixture-scoped screen snapshot, byte-identical to the canonical `compute_tradability`
      band's own fields
- [ ] Legacy screens render `"composition not recorded in this snapshot"` with their checksums
      unchanged on disk
- [ ] Rank order proven byte-identical to the pre-change baseline (golden comparison)
- [ ] MCP surface stays exactly 17 tools; `Config().config_fingerprint()` stays `08e471b10130e1e2`;
      zero new `Config` fields
- [ ] A `[NEW]`-flagged demo-narrator walkthrough covers the wall-composition disclosure end to end,
      narrated over POPULATED ranked rows

## TESTING REQUIREMENTS

- Browser: J-15 (screenshot of the populated `/desk` `levels` column + round-number badge); smoke
  replay across J-01..J-14
- Unit/integration: `desk_screen.py` row-builder golden tests (exact field values, sum invariant,
  single-member and intraday-dominated rows), call-count guard test, rank-order golden comparison,
  same-pins re-run byte-identity, `test_copy_discipline.py`, MCP tool-count assertion,
  `config_fingerprint` sentinel
- Error cases: an unknown/legacy snapshot must render the honest absent-composition state rather than
  a computed or fabricated value; a band with zero `members` entries for some timeframe must simply
  omit that key rather than emit a zero

Test-first contract:

- TC-1: given a fixture-scoped backend with a universe snapshot and bar store already frozen, when a
  screen compute is triggered for a screen_date not already recorded under the same 5 pins, then the
  persisted snapshot's every ranked row carries `band_member_count` (int), `band_round_number`
  (bool), and `band_member_timeframes` (dict[str,int]).
- TC-2: given that same new snapshot, when each ranked row's `band_member_count`/`band_round_number`
  is compared against `GET /research/tradability?symbol=<sym>&as_of=<that snapshot's own as_of>`'s
  own selected band's `member_count`/`round_number`, then they are byte-identical for every ranked
  row.
- TC-3: given that same new snapshot, when `band_member_timeframes` values are summed per row, then
  the sum equals that row's own `band_member_count` for every ranked row.
- TC-4: given a ranked row whose band holds a single member (zero-width `price_low == price_high`),
  when its `band_member_count` is read, then it equals 1 and `band_member_timeframes` sums to 1.
- TC-5: given a ranked row whose band is dominated by intraday (`1m`/`5m`) members, when
  `band_member_timeframes` is read, then it contains `1m`/`5m` keys whose counts, together with any
  other timeframe present, sum to `band_member_count`.
- TC-6: given the row builder under a spy/mock on `BarStore` reads and `compute_tradability` calls,
  when it constructs a ranked row, then the call counts are unchanged from before this iteration
  (zero additional reads or calls).
- TC-7: given the new snapshot's rank order, when compared against a golden capture of the same 5
  pins taken before this change, then the row order is byte-identical.
- TC-8: given a re-run triggered under identical pins, when the compute runs again, then it returns
  the existing snapshot honestly (no new file written) and every row stays byte-identical.
- TC-9: given a screen snapshot recorded BEFORE this change, when `/desk` renders its ranked rows,
  then the `levels` column shows the literal string "composition not recorded in this snapshot" for
  every row, and that snapshot's own stored `file_checksum` recomputes unchanged.
- TC-10: given `/desk` after a clean frontend rebuild, when the operator views the ranked table over
  the NEW populated screen, then the `levels` column is visible beside `band`/`opposite`, rendering
  each row's own recorded counts (e.g. "155 levels · 1d 68 · 1h 57 · 4h 19 · 1w 11") plus the "round
  number" badge on rows where `band_round_number` is true.
- TC-11: given a browser screenshot of the populated `/desk` table, when captured, then one frame
  shows at least one ranked row with `band_member_count` <= 5 and one ranked row with
  `band_member_count` >= 100 legible together, and a "round number" badge legible in that same frame
  or in one further screenshot of the SAME rendered screen.
- TC-12: given the `[NEW]`-flagged demo-narrator walkthrough, when recorded over the populated
  screen, then `Demo Verdict: RECORDED` with a non-empty gallery, narrating the `levels` column and
  the round-number badge.
- TC-13: given the full backend test suite, when it runs after this change, then it is green,
  `Config().config_fingerprint()` returns `08e471b10130e1e2`, zero new `Config` fields exist, and
  `tests/test_copy_discipline.py` passes unmodified.
- TC-14: given the MCP tool list, when counted after this change, then it has exactly 17 entries, and
  the `desk_screen` tool's response is byte-identical to a direct `GET /research/desk/screen` call.
- TC-15: given `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, and
  `StructureChart.tsx`, when diffed against their pre-iteration state, then each shows zero diff.

## NOTES

- Scoped rig required: compute the new screen snapshot, capture the browser screenshot, and record
  the demo-narrator walkthrough against a fixture-scoped copy of `apps/backend/.data` (never the
  ambient store) — name the scoped rig explicitly in every lane's dispatch (dev, browser-qa,
  demo-narrator), per the iter-9/11/14/15/17/19/20/21/22 lesson. Prove the serving process actually
  points at the copy (e.g. a direct `curl` against the scoped backend), not just the origin, per the
  iter-17 `.next`-cache-sharing lesson (never run two `next dev` from `apps/frontend` at once).
- `band_member_timeframes`'s key order is left to build discretion by goal.md itself ("a deterministic
  order", no further specification) — the blueprint's iter-23 RESOLVED note asks the developer to
  mirror the `_bands_by_class` precedent's own key style and keep it stable across the golden test's
  own assertions; this is a routine build-time degree of freedom, not a scoring ambiguity, so no
  assumption-ledger entry was logged for it.
- Housekeeping, not blocking: the T-10a qa-rig from iteration 22 is still running
  (`project-extensions/qa-rig/xrig.sh down` when convenient) — J-15 needs no native-tooltip
  screenshot, so this iteration does not depend on that rig.
- Do not re-open, re-test, or re-film J-01..J-14 beyond the required-still-passing regression check —
  they are all "Do not redo" per `iteration-state.md`.
