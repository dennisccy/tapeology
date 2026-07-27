# Goal Iteration 9 — J-08: basis disclosure on every ranked briefing row

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
    tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk`
    BESIDE the kept two pages — the sanctioned kept-surface edits are J-05's additive `/structure`
    prefill and **R-1**'s price-less-row repair, which changes no output for finite data and leaves
    every recorded series on disk untouched.) *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
    labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
    feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
    MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - **Membership is never a signal.** Universe membership (and any constituents metadata) selects
    WHAT to screen; it never enters a computation, rank formula beyond selection, feature, or
    report as an input value. *(critical)*
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
  - **The demolition stays demolished.** No journal-era machinery returns; the desk ledger records
    machine output only — zero manual-input write paths on desk records this era (dispositions/
    annotations are Era C's design space). *(critical)*
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

## GOAL

Give every ranked `/desk` briefing row an honest, self-describing measurement age — a `basis`
column and tooltip detail naming the exact daily bar `compute_tradability` actually measured that
row's distance/class from, and how many days old that reading is — so a same-day wall and an
11-day-old one are no longer indistinguishable on the ranked table's one sort key.

## BACKGROUND

Iteration 8 closed Era B: all seven Must-have journeys (J-01–J-07) reached `passing`,
`GOAL_ACHIEVED`, two-key confirmed (`runs/goal-session-desk/iter-8/eval.md`,
`iter-8/eval-confirm.md`). The goal-proposer then ran its post-achievement scan
(`runs/goal-session-desk/state/proposer-result.json`, `state/enhancement-proposals.jsonl`) and found
one real, measured gap: `compute_tradability`'s own `basis_as_of` spans an 11-day range across the
universe (AAPL 1 day old, TSLA/JPM/AMZN/GOOGL/AMD 2 days, MSFT 4 days, META/NFLX/NVDA 12 days —
measured live 2026-07-25) but never appears on a screen row, so the ranked table's one sort key
(`distance_bps`) silently mixes fresh and stale readings — the recorded snapshot
`screen-2026-07-25-e184a7dc2f86` ranks NFLX #2 on `distance_bps 0.0` with no basis field anywhere in
the row. The proposer promoted exactly one journey, **J-08**, inside `docs/goal.md`'s
`AUTO:journeys` marker block (the only place it is allowed to write — confirmed: the diff touches
nothing else in the file), and explicitly declined to promote a second candidate
(`bar-index-store-reconcile` — backlogged; `/desk` already discloses that divergence honestly and
the ranking is unaffected). Per the priority rubric and the "do not manufacture more work" rule,
this iteration builds only the promoted journey.

**Depth — full, trigger 2 (Data model).** `desk_screen.py`'s row-building loop (`compute_screen`,
`desk_screen.py:251`) writes an append-only, checksummed, frozen-JSON snapshot per screen run
(`ScreenStore.record`) whose Ranked-row shape has been stable since iter-3. J-08 adds two new
fields to that **persisted** shape (`basis_as_of`, `basis_age_days`) for every row of every NEW
snapshot, while every snapshot already on disk (2 real recordings today, plus fixtures) must keep
serving byte-identically and render the fields' absence honestly — never backfilled. This is
exactly the class of change trigger 2 names (an addition to a blueprint Data-Contract value's
persisted schema), and this era's own history is a direct warning against doing schema-touching
work at lean depth: iter-4's NaN-bar poisoning hit the same append-only store family, and iter-7
STALLED for four iterations over an under-scrutinized change to a frozen file. Full depth also
matches this session's own precedent — iter-6 (J-05, a comparably-scoped addition to the SAME
already-shipped `/desk` page, though it reused existing values with zero new field) was itself
dispatched full.

**Lessons applied** (from `lessons.md`): the iter-6 stretched-link lesson applies directly —
`/desk`'s row is a `position: relative` `<tr>` with an `absolute inset-0` drill-in anchor
(`page.tsx:220-235`) painted over every cell, so the new `basis` column's full-precision detail
must join the anchor's existing consolidated tooltip (`deskRowDrillInTitle`, `page.tsx:189-194`,
the iter-7 fix) instead of a new per-cell `title`, which is already proven pointer-unreachable
there. The iter-4/iter-5 lessons on scoped stores and golden-script write-paths apply to this
iteration's browser evidence and its new `journey-scripts/J-08.json`: never point a browser pass or
a replay at the ambient `.data/`, and if the recorded steps trigger a NEW screen compute, scope
that replay's backend or avoid the compute-triggering click. The iter-7/iter-8 lessons on
unfalsifiable append-only sentinels apply here too — this iteration must prove, not assert, that
the two pre-existing real screen snapshots are untouched.

## IN SCOPE

### Backend
- [ ] `desk_screen.py`'s `compute_screen` row-building loop (the ranked-row branch only,
      `desk_screen.py:310-325`): add `basis_as_of`, copied verbatim from `result["basis_as_of"]`
      (already read at `:311`, the same `compute_tradability` return value
      `_resolve_reference_close` already consumes), and `basis_age_days`, a plain calendar-date
      difference between that value and the snapshot's own `as_of` (`:275`). Skip rows are
      structurally excluded — a skip row's `reason: "no_basis"` already means no basis resolved at
      all, so it never enters the ranked-row branch.
- [ ] Confirm the two new fields flow through `ScreenStore.record`'s existing `_canonical`/checksum/
      append-only write path with zero change to that mechanism, and that reading a snapshot file
      recorded BEFORE this iteration (missing the fields) round-trips through
      `GET /research/desk/screen` (both no-param and `?date=` forms) with the fields absent — never
      defaulted to a computed value, never backfilled.
- [ ] A guard test (new, or extending `test_desk_screen.py`) proving the two fields are read/derived
      ONLY from the already-fetched `compute_tradability` result for that member — zero additional
      `BarStore`/`bar_index`/`compute_tradability` call — mirroring the existing
      `test_bar_store_signature_issues_zero_bar_store_calls` monkeypatch-call-count pattern
      (`test_desk_screen.py:125`).

### Frontend
- [ ] `apps/frontend/lib/types.ts` (`DeskScreenRow`, `:792`): add `basis_as_of: string | null` and
      `basis_age_days: number | null`.
- [ ] `apps/frontend/app/desk/page.tsx`: add one descriptive "basis" column to `DeskRowsTable`'s
      header (`:281-290`) and `DeskRow` (`:220-265`) — descriptive measurement copy only, e.g.
      "basis 2026-07-13 · 12 d before as-of" (goal.md's own example) — rendering the honest
      "basis not recorded in this snapshot" text when either field is absent. Extend
      `deskRowDrillInTitle` (`:189-194`) with the full-precision basis detail (never a new per-cell
      `title` — iter-6/iter-7 lesson); verify the row's drill-in anchor (`absolute inset-0`, `:234`)
      stays topmost at the new cell's center (hit-test assertion, per the iter-6 lesson's own
      remedy).
- [ ] Confirm the SAME `DeskRow`/`DeskRowsTable` components render the honest fallback correctly
      when reached via J-05's history drill-through (a past snapshot recorded before this
      iteration) — no separate render path for historical vs. latest.

### Golden script / regression asset
- [ ] Record `runs/goal-session-desk/journey-scripts/J-08.json` as this era's newest deterministic-
      replay golden (matching the J-04/J-05/J-07 precedent), scoped to a throw-away backend per the
      iter-4/iter-5 lessons (never the ambient `.data/`); include a post-match liveness assertion
      (the iter-4 lesson: assert the page is still alive AFTER the first matching string).

### New user-facing capability
Every ranked row on `/desk` now discloses how old the price reading behind its distance
measurement is — a `basis` column naming the date `compute_tradability` measured from and how many
days before the screen's as-of that date is.

### New information displayed
`basis_as_of` (the daily-bar date the row's distance/class was measured against) and
`basis_age_days` (days between that date and the screen's own as-of) on every ranked row of NEW
screens; an honest "basis not recorded in this snapshot" state on every ranked row of a screen
recorded before this iteration (both on the latest view and via J-05's history drill-through).

### New user actions
None — no new button/control. The existing Run Screen button now produces rows that carry two
additional descriptive fields.

### UI surface changes
`/desk`'s ranked-rows table gains one new "basis" column; the row anchor's existing consolidated
hover tooltip gains the full-precision basis detail alongside the already-present distance/score/
coverage text.

### Product surface delta
The `/desk` briefing becomes self-describing about measurement freshness — an operator can tell a
same-day reading from an 11-day-old one without leaving the ranked table.

### Blueprint conformance
This iteration's only surface change is a new column + tooltip content on the ALREADY-REGISTERED
`/desk` canonical home (Desk nav section, the same page J-04 shipped) — no new page, no
nav-skeleton change. `blueprint.md` has been updated additively (this iteration, before dispatch):
a new J-08 row in the Feature/journey homes table (home = `/desk`, same as J-04), an "iter-9
addition" note appended to the existing "Screen snapshots, rank rows, skip rows" Data Contract row,
and a "RESOLVED at iter-9" trailer note. No `blueprint.reapproval-requested` file was written —
nothing about the nav skeleton changed.

### Data-contract additions
- `basis_as_of: str (ISO datetime) | null` — read verbatim from `compute_tradability`'s own
  `basis_as_of` return field (already consumed internally by `desk_screen._resolve_reference_close`,
  `desk_screen.py:227`); computed by `desk_screen.py`, served by `GET /research/desk/screen` (both
  no-param and `?date=` forms) — registered as an ADDITIVE field on the EXISTING "Screen snapshots,
  rank rows, skip rows" Data-Contract row (not a new row, not a new owner, not a new endpoint).
  `null`/absent on every screen snapshot recorded before this iteration (never backfilled).
- `basis_age_days: int >= 0 | null` — a calendar-date difference between the row's own
  `basis_as_of` and the snapshot's own `as_of`, computed by the SAME `desk_screen.py`, served by
  the SAME endpoint, same additive-row registration. `null`/absent on legacy snapshots, same rule
  as above.
- Both fields apply to RANKED rows only — a skip row's existing `reason: "no_basis"` already means
  no basis resolved, so skip rows structurally never carry these fields.
- Zero diff to `tradability.py`/`levels.py`/`bars.py`'s own return shapes; zero new `Config` field.

## OUT OF SCOPE

- Any edit to `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, the
  engine, or any of **R-1**'s eight named files — Frozen foundations; J-08's own acceptance text
  requires zero diff to the first three plus the chart.
- Any new `Config` field, new route, new page, new MCP tool, or nav-skeleton change — the existing
  `desk_screen` MCP proxy already carries the new fields with zero code change (it is a byte-
  identical GET proxy).
- Backfilling, rewriting, or recomputing any already-recorded universe or screen snapshot — the
  append-only rail is absolute.
- The backlogged `bar-index-store-reconcile` proposal — explicitly NOT promoted by the
  goal-proposer this cycle; do not build it.
- A PnL-ledger append — this era's Non-Goals forbid it; J-08's acceptance uses the single-source-
  of-truth criterion in its place (goal.md's own text).
- The same-date screen ambiguity, keyboard access for history rows, and the three older one-line
  hardening items — carried, not forced, unrelated to this journey.
- Re-verifying J-01–J-07's own acceptance clauses beyond the smoke-set regression replay — they are
  "Do not redo" per `iteration-state.md`.

## DEFINITION OF DONE

- [ ] `desk_screen.py`'s row builder records `basis_as_of` and `basis_age_days` on every ranked row
      of a NEWLY computed screen, both read/derived from `compute_tradability`'s already-consumed
      return value (zero new `BarStore`/tradability call).
- [ ] A same-pins re-run of an existing screen reproduces byte-identical rows (including the two
      new fields where present) and writes no second file.
- [ ] Every screen snapshot recorded before this iteration is proven byte-identical on disk
      (checksum comparison before/after) and its rows are served with the two fields absent — never
      backfilled, never computed at read time.
- [ ] `/desk` renders a descriptive `basis` column on the ranked table (both for the latest screen
      and for any historical screen opened via J-05's drill-through) and shows the honest
      "basis not recorded in this snapshot" text for legacy rows lacking the field.
- [ ] The row anchor's existing consolidated hover tooltip includes the full-precision basis detail,
      and a hit-test confirms the anchor stays topmost at the new cell's center.
- [ ] A guard test proves the basis fields are never independently re-derived (no extra bar-store or
      tradability call beyond the existing one-call-per-member pattern).
- [ ] `journey-scripts/J-08.json` is recorded as this era's newest golden replay script and proven
      with a `--mode verify --journeys J-08` run against a fixture-scoped backend.
- [ ] J-08 passes via browser-qa-agent, including a screenshot with at least one fresh row (basis
      age ≤ 2 d) and one stale row (basis age ≥ 10 d) legible together.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough covers the briefing's basis disclosure end to end
      (goal.md's explicit acceptance clause).
- [ ] Required-still-passing journeys J-01–J-07 remain green (deterministic replay + LLM fallback).
- [ ] No anti-goal violation introduced: zero diff to `tradability.py`/`levels.py`/`bars.py`/
      `StructureChart.tsx`, zero new `Config` field, fingerprint pin `08e471b10130e1e2` unchanged,
      `tests/test_copy_discipline.py` green unmodified, MCP tool count stays 17 with `desk_screen`'s
      proxy still byte-identical.
- [ ] Full backend suite passes at or above the 1341 passing / 8 skipped floor; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-9-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-08 full walk (ranked table with the new column, hover tooltip, honest legacy fallback
  via J-05's history drill-through, fresh+stale rows legible in one screenshot); smoke replay of
  J-01–J-07.
- Unit/integration: `test_desk_screen.py` (new/extended golden assertions, the no-re-derivation
  guard test, the legacy-fallback test, the byte-identical-rerun test), `test_mcp_server.py`
  (re-run — no code change expected), `test_copy_discipline.py` (re-run green unmodified), the full
  backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`).
- Error cases: a screen snapshot recorded before this iteration (fields absent) must not raise or
  crash on read or render — it must degrade to the honest fallback text, never a `KeyError`/
  `undefined` render or a fabricated value.

Test-first contract — TC- scenarios:

- TC-1: given a fixture-scoped rig where `compute_tradability` returns a resolved `basis_as_of` for
  a ranked symbol, when a NEW screen is computed for a screen_date, then that row's persisted
  `basis_as_of` is byte-identical to `GET /research/tradability?symbol=<sym>&as_of=<snapshot
  as_of>`'s own `basis_as_of`.
- TC-2: given the same fixture, when the row's `basis_as_of` and the snapshot's own `as_of` are
  read, then `basis_age_days` equals the exact calendar-date difference between the two (e.g., a
  basis 12 calendar days before as_of yields `basis_age_days == 12`).
- TC-3: given a screen already recorded under a specific 5-pin key, when a screen compute is
  re-triggered under the IDENTICAL pins, then the endpoint returns the same already-recorded
  snapshot (`id` unchanged) with `rows` byte-identical including `basis_as_of`/`basis_age_days`,
  and no new file is written under `.data/screen/`.
- TC-4: given the two real screen snapshot files recorded before this iteration, when their
  SHA-256 checksums are compared before and after this iteration's full change set, then both are
  unchanged, and `GET /research/desk/screen?date=<either date>` serves their rows with
  `basis_as_of`/`basis_age_days` absent.
- TC-5: given `/desk` rendering a ranked row that HAS basis data, when the page is viewed, then the
  basis column shows descriptive text naming the date and day-count (e.g., "basis 2026-07-13 · 12 d
  before as-of").
- TC-6: given `/desk` rendering a ranked row from a screen recorded before this iteration (no basis
  data), when the page is viewed, then the basis column shows the honest
  "basis not recorded in this snapshot" text — not blank, not a dash, not a computed value.
- TC-7: given a ranked row with basis data, when the operator hovers anywhere in the row, then the
  composite tooltip (the row anchor's `title`) includes the full-precision `basis_as_of` alongside
  the already-present distance/score/coverage detail.
- TC-8: given `desk_screen.py`'s row-building function with `BarStore`/`bar_index`/
  `compute_tradability` call-counting instrumented (mirroring
  `test_bar_store_signature_issues_zero_bar_store_calls`), when a screen is computed, then the
  number of `compute_tradability` calls equals exactly the member count — zero additional calls
  attributable to the basis fields.
- TC-9: given the full backend test suite after this iteration, when it is run, then it reports 0
  failures at or above the 1341 passing / 8 skipped floor, and `Config().config_fingerprint()`
  still prints `08e471b10130e1e2`.
- TC-10: given `test_mcp_server.py`'s existing `desk_screen` tool contract test, when run after this
  iteration, then the tool's JSON output for a screen containing basis fields is byte-identical to
  the equivalent `GET /research/desk/screen` REST call, and the tool count is still exactly 17.
- TC-11: given `tests/test_copy_discipline.py`'s frontend-literal lint, when run after the new
  `/desk` basis column and tooltip copy are added, then it passes unmodified — no advice/imperative/
  prediction language detected in the new strings.
- TC-12: given a real browser after the T-9 clean rebuild (`rm -rf apps/frontend/.next` + restart
  both processes) against a scoped throw-away copy of real data with a natural basis-age spread,
  when `/desk` is loaded with its latest screen, then a screenshot shows at least one row with basis
  age ≤ 2 days and at least one row with basis age ≥ 10 days, both legible in the same image.
- TC-13: given `runs/goal-session-desk/journey-scripts/J-01.json` through `J-07.json`, when the
  deterministic replay lane runs them against a fixture-scoped backend, then every one reports PASS
  with no write-path side effect on the ambient `.data/` store.
- TC-14: given `runs/goal-session-desk/journey-scripts/J-08.json` recorded this iteration, when
  `--mode verify --journeys J-08` is run against a fixture-scoped backend, then it reports 0 failed
  and the results file is saved (not discarded).
- TC-15: given the `[NEW]`-flagged demo-narrator walkthrough requirement, when this iteration's
  showcase artifacts are generated, then a walkthrough entry flagged `[NEW]` describing the
  briefing's basis disclosure (both the fresh and the stale case) exists.
- TC-16: given `git diff` of this iteration's full change set, when `tradability.py`, `levels.py`,
  `bars.py`, and `StructureChart.tsx` are checked, then each shows zero diff.

## NOTES

- No open blockers carry into this iteration — the era's last one (owner ratification of R-1) is
  resolved (`docs/goal.md`'s "OWNER RATIFICATION — 2026-07-27 — R-1"); the one still-open item
  (`iteration-state.md`) is an operator cache-warm note, unrelated to this journey.
- Recommended recipe for TC-12's fresh/stale spread: use a throw-away COPY of the real ambient
  `.data/` (which already has exactly this spread per the proposer's own live measurement — AAPL
  1 d, MSFT 4 d, META/NFLX/NVDA 12 d), never the ambient store directly, per the iter-4 lesson and
  this era's established fixture-scoped-rig discipline (the iter-8 baseline-diff script is the most
  recent worked example of copying `.data/` into a throw-away root before booting a backend against
  it).
- If the recorded `J-08.json` golden's steps need to trigger a NEW screen compute to exhibit basis
  data, scope that replay's backend explicitly (own data dir) rather than pointing it at the
  ambient store — the iter-5 lesson (`J-04.json` step 5) is the cautionary precedent: a golden
  script is a WRITE path every time it replays.
- If any lane edits `journey-scripts/J-08.json` (or any other golden) after recording it, say so
  explicitly in that lane's results report — the iter-8 lesson on undisclosed golden edits.
- This is expected to reopen the era's `GOAL_ACHIEVED` state to `CONTINUE` only for the duration of
  this one promoted journey — but the goal-decomposer does not declare verdicts; that is the
  evaluator's call after real evidence lands.
