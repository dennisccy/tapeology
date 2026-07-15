# goal-tradable_wall-iter-7 Dev Handoff

**Phase:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

**J-06: Cockpit confluence — tradable-band overlay + descriptive confluence chip on the cockpit
`PriceChart`.** Pure-frontend iteration per the plan: no backend endpoint, config, or computation
change; `config_fingerprint` stays `4d665603569b9dbf`.

- **Tradable-band overlay.** `PriceChart.tsx` now fetches the watched symbol's bands from
  `GET /research/tradability` and draws one solid price line per band edge (rose = resistance,
  emerald = support; title = side/class/quality_score/round_number), reusing
  `StructureChart.tsx`'s L97-120 pattern byte-for-byte. Solid lines are visually distinct from this
  component's own pre-existing dashed thesis price-lines.
- **Descriptive confluence chip.** Visible only when the latest served candle close is inside a
  served band AND the current served tape state (`tapeState`, a new required prop reading the WS
  snapshot's own `tape_state` field verbatim) matches that band's side in the served
  `structure_tape_map` `rejection_states`/`breakthrough_states` mapping (`GET /research/strategies`).
  Chip copy states the condition (side/range/class, tape state, whether the match is a rejection or
  a breakthrough) and cites the edge report as measured history — no imperative/prediction language.
- **Honest "no tradable map" empty state** for SIM-*/no-bar-series symbols — chart + tape markers
  keep rendering; no fabricated band, no chip.
- **Zero client recomputation.** Band ranges/class/score, the confirmation mapping, and the tape
  state are all read verbatim from their owning endpoints; the component only does a display
  conjunction (is-price-in-range? does-state-match-served-mapping?). The four tape-state names
  (`bid_absorption`/`ask_absorption`/`buyer_control`/`seller_control`) appear nowhere in the new
  matching logic — only in the pre-existing `MARKER_COLORS`/`STATE_LABELS` cosmetic dicts (verified
  by a source-inspection test scoped to exclude those two blocks).
- **Live mode untouched.** `page.tsx`'s existing `(mode === "sim" || mode === "historical")` gate is
  unchanged — the only edit to `page.tsx` is passing the new `tapeState` prop into the existing
  `<PriceChart>` call.

**One correction to the plan's own documented assumption, found and fixed during pre-handoff
verification (see "Deviation from plan" below): the tradable-bands fetch's `as_of` argument uses the
WATCHED SESSION's own `epoch_anchor` (already-fetched, real market epoch for a historical replay)
instead of the browser's wall-clock time.** The plan's Assumption 1 said to pass `new
Date().toISOString()` verbatim; I initially implemented that literally, then discovered via a real
credentialed browser test (see below) that it makes the band overlay show TODAY's tradable map
during a HISTORICAL replay of a past session — unrelated to whatever price is being replayed. Fixed
by sourcing `as_of` from `history.epoch_anchor` (already fetched by the existing `…/history` poll,
no new fetch) instead, falling back to wall-clock time only before the first `history` response
lands. This is still zero client "which session" math (`_resolve_basis` in `tradability.py` still
owns the decision entirely server-side) — it only supplies a different, more contextually correct
moment to resolve from. Verified live: this correctly resolves the pinned 2026-06-22 replay to the
2026-06-18 basis and renders the exact "round"-flagged ~300 resistance band goal.md's pinned case
describes (see the Live Verification section).

## Files Changed

- `apps/frontend/components/PriceChart.tsx` -- main change (+204/-4 lines):
  - New required prop `tapeState: string | null`.
  - New constant `STRATEGY_TAPE_MAP_ID = "structure_tape_map"` (mirrors `structure/page.tsx`'s own
    `STRATEGY_TAPE_ID` registry-lookup-key precedent).
  - New state: `tradabilityState` (`{phase, data: TradabilityResponse | null}`), `strategies`
    (`StrategiesPayload | null`).
  - New ref: `bandPriceLinesRef` (tracked separately from the existing thesis-geometry
    `priceLinesRef` so redrawing one family never clobbers the other).
  - New effect: fetches `GET /research/tradability`, keyed on `[ticker, history?.epoch_anchor]` (not
    polled — `epoch_anchor` is a stable per-watch value, so this fetches at most once or twice per
    watch, not every second).
  - New effect: fetches `GET /research/strategies` once on mount (`[]` deps).
  - New effect: draws the band overlay (`series.createPriceLine`), keyed on
    `[tradabilityState, history]` — the same self-healing dependency the pre-existing thesis-geometry
    effect already relies on for the "series not yet created" race.
  - New derived values (render body, not hooks): `lastPrice`, `matchedBand`, `direction`,
    `mapEntry`, `rejectionState`/`breakthroughState`, `matchKind`, `confluence`, `tradabilityEmpty`.
  - New JSX: the confluence chip (`data-testid="confluence-chip"`) and the "no tradable map"
    `EmptyHint` (`data-testid="no-tradable-map"`), both rendered below the existing chart canvas —
    additive, never blocking the pre-existing chart/markers rendering.
- `apps/frontend/app/page.tsx` -- one additive line: `tapeState={snapshot?.tape_state ?? null}`
  passed into the existing `<PriceChart>` call. The surrounding
  `(mode === "sim" || mode === "historical")` gate is byte-identical to before.
- `apps/frontend/lib/types.ts` -- new `StrategyEntries` interface (`rule` plus the optional
  `proximity_band_bps`/`rejection_states`/`breakthrough_states`/`arm_cooldown_seconds`/
  `concurrency` fields structure_tape/structure_tape_map's grammar carries); `Strategy.entries`
  widened from `{ rule: string }` to `StrategyEntries` (purely additive — `v1`'s narrower shape
  still satisfies it).
- `apps/backend/tests/test_price_chart_confluence.py` -- NEW file, 9 Python source-inspection
  tests (this repo's established keyless-frontend-testing precedent — see
  `test_profile_equivalence.py::test_performance_page_offers_no_profile_selection_control` and
  `test_strategies_api.py::test_strategies_module_carries_no_second_copy_of_the_id_strings`):
  1. `test_confluence_matching_has_no_hardcoded_tape_state_literal` -- no tape-state-name literal
     outside the pre-existing `MARKER_COLORS`/`STATE_LABELS` dicts.
  2. `test_confluence_matching_reads_rejection_and_breakthrough_off_the_served_entry` -- the mapping
     is read (`.rejection_states`/`.breakthrough_states`), never restated as a local object literal.
  3. `test_confluence_selects_structure_tape_map_strategy_entry` -- looks up the right registry
     entry.
  4. `test_tradability_bands_fetch_is_keyed_on_ticker_and_stable_session_anchor_not_polled` -- the
     bands effect's dependency array is exactly `[ticker, history?.epoch_anchor]`.
  5. `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math`
     -- `as_of` reads `history.epoch_anchor` (converted the same way this file already converts
     candle timestamps), falls back to wall-clock only before `history` loads, and no local
     "prior session" date arithmetic exists anywhere in the file.
  6. `test_strategies_fetched_once_on_mount_not_per_ticker` -- the strategies effect's dependency
     array is `[]`.
  7. `test_band_overlay_reads_only_served_band_fields` -- the overlay reads
     `band.side`/`price_low`/`price_high`/`class`/`quality_score`/`round_number` verbatim.
  8. `test_no_tradable_map_empty_state_present` -- the honest empty state exists and reuses
     `EmptyHint`.
  9. `test_page_threads_tape_state_prop_and_preserves_live_mode_gate` -- `page.tsx` passes
     `tapeState` and the live-mode gate is unchanged.

  Copy-discipline coverage (no imperative/predictive/claim language in the new chip text) is
  intentionally NOT duplicated in this new file: the existing
  `test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` already walks every
  `.tsx`/`.ts` file under `apps/frontend/components`/`apps/frontend/app`, so it automatically covers
  the new chip copy (reconfirmed green below).

No backend file was created or modified beyond this one new test file. `config.py`, `strategies.py`,
`tradability.py`, `levels.py`, `backtests.py`, `edge_report.py`, `setups.py`, `datasets.py`, the
engine, and the adapters are all absent from `git diff --name-only -- apps/backend/` (empty diff —
confirmed) and absent from `git status --porcelain -- apps/backend/` beyond the one new test file.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1348 passed, 7 skipped, 0 failed, 0 errors** — identical pass/skip count to before this
iteration's own new tests are subtracted (this run includes the 9 new tests above; the pre-existing
suite carries the same 7 `@pytest.mark.integration` credentialed skips, unaffected). Zero
regressions.

Targeted re-runs during development:
- `tests/test_price_chart_confluence.py` -- 9/9 passed, both before implementation (TDD red — 8/9
  failed with clear "expected X" assertion messages) and after (green).
- `tests/test_copy_discipline.py tests/test_price_chart_confluence.py
  tests/test_profile_equivalence.py tests/test_strategies_api.py` -- 63/63 passed, re-run AFTER the
  `as_of` fix described above (confirms the fix didn't disturb copy discipline, config-fingerprint
  stability, or the strategies-endpoint contract).
- `config_fingerprint()` reconfirmed `4d665603569b9dbf` via direct invocation.
- `git diff --name-only -- apps/backend/` -- empty. `git status --porcelain -- apps/backend/` shows
  only the one new test file.

**Frontend type-check.** `npx tsc --noEmit -p tsconfig.json` -- exit 0, zero type errors, re-run
after the `as_of` fix too.

**Frontend "tests"**: no frontend test runner exists in this repo (unchanged from every prior
iteration — no `test` script, no `.test.ts(x)` files). Verified via the source-inspection tests
above, `tsc`, and extensive live browser verification (below) — well beyond a typical dev-agent
smoke check, because this iteration's own live testing is what surfaced the `as_of` bug.

## Live Verification (real browser, both keyless and credentialed)

Started the real stack via `scripts/dev.sh` (ports 8301/3301 for this checkout). Used Chrome MCP
throughout; console logging enabled for every check.

**SIM ticker (keyless).** Watched `SIM-BUYER` in Simulated mode: chart + tape-state markers render
normally; "No tradable map for SIM-BUYER." renders as a small, non-blocking hint below the chart
(never covering the canvas, never a fabricated band, no chip). Zero console errors/warnings.

**Live mode (real market-clock check).** Switched to Live mode, watched AAPL: the real market was
closed at test time, so the honest "Market is closed" panel rendered — and, critically, no "Price
Chart — Tape-State Markers" section appeared anywhere in the DOM, confirming the whole component
(overlay + chip included) stays fully absent in live mode. Zero console errors/warnings.

**Credentialed historical replay (Alpaca credentials ARE configured in this environment — confirmed
via `GET /market/clock` returning `available: true`, without reading the `.env` file itself).**
Watched AAPL in Historical mode over 2026-06-22 09:30-16:00 ET (the pinned test window, `feed: "sip
(consolidated)"`):
- **Before the fix**, the band overlay fetched `as_of = new Date().toISOString()` (today,
  2026-07-15) and resolved bands from TODAY's basis (2026-07-13): a resistance band at 317.40 and
  support bands at 254-277 — nowhere near the replayed price action (~297-300). No line was visible
  anywhere in the chart's price range.
- **After the fix**, the SAME replay's overlay correctly resolved to the 2026-06-18 basis and showed
  a resistance band explicitly labeled `R class A · score 153 · round` at ~300.17 and a second
  `R class A · score 77 · round` band nearby — the exact "round-number 300 flagged" pinned rejection
  cluster goal.md describes. As the replay's price climbed from ~297.85 through ~299.86, the band
  lines were correctly visible and correctly positioned relative to the candles.
- I did not personally observe the confluence chip fire during this session (the tape state cycled
  through `unclear`/`buyer_control` while price approached the band; catching the exact moment it
  reads `ask_absorption` or `seller_control` while price is inside the band is a real-data timing
  question, not a code-path I can force deterministically). This is the credentialed, operator-gated
  portion of J-06 the plan explicitly separates from the "keyless core" — see Known Issues.
- Zero console errors/warnings throughout, including one Fast-Refresh-only React warning ("changed
  size between renders") that appeared exactly once, immediately after I hot-edited the effect's
  dependency-array length while a component instance from the PRE-edit code was still mounted; a
  full page reload + fresh watch afterward showed a completely clean console, confirming this was a
  dev-server hot-reload artifact, not a real bug.

**Service startup + shutdown verification.** Stopped the stack, confirmed both ports (8301/3301)
released via `ss`/`lsof`, restarted via the same `scripts/dev.sh` — clean second start (backend 200,
frontend 200, both compiled with no errors), no port-conflict errors. Stopped again afterward and
verified via `lsof -i :PORT` (not just `ps`, since `next dev`'s reloader/worker processes don't
always show a matching string to a plain `ps`/`pkill -f` pattern) that both ports are genuinely free
and no lingering tapeology process remains.

## Deviation from Plan

The plan's Assumption 1 (`as_of` = current wall-clock time, `new Date().toISOString()`) was
implemented literally first, exactly as specified, and all my own tests + the DoD's stated keyless
requirements passed with that implementation. Only through live credentialed browser verification
(not required at dev-time per the plan's own "the keyless … portions … constitute J-06's passing
core" carve-out) did I discover that this choice makes the flagship credentialed scenario
(goal.md's own named acceptance line: "during the credentialed AAPL 06-22 replay the band overlay
is visible and the chip appears at the 300-test") structurally unable to work — the overlay would
show whatever is TODAY's tradable map, unrelated to the session actually being replayed. I fixed
this using data already available inside the component (`history.epoch_anchor`, already fetched by
the existing history poll) rather than escalating, because: (a) it requires no new prop, no backend
change, and stays within the same "zero client session-math" constraint the plan itself set; (b) I
had direct, reproducible empirical proof of the failure and the fix; and (c) the fix is a strict
improvement for the historical-replay case and behaviorally identical for the sim/live cases (SIM
tickers resolve `no_bar_series_for_symbol` regardless of `as_of`, so the choice is moot there; live
mode never renders this component at all). Updated the corresponding tests to match. Flagging this
prominently here for the reviewer/auditor to independently assess the judgment call.

## Known Issues

1. **The confluence chip's live firing was not directly observed in this session's browser
   verification.** I confirmed the mechanism end-to-end (correct band data fetched and rendered at
   the correct moment; the matching logic is unit-verified via source inspection to read the served
   mapping verbatim) and confirmed price approached the relevant band during the pinned replay, but
   I did not personally witness the exact price-in-band + state-matches-mapping moment during my
   observation window. The goal's own Testing Requirements explicitly name the full credentialed
   "AAPL 2026-06-22 300-test replay screenshot" as the QA/operator-gated verification step, run with
   a dedicated time budget (potentially re-running the replay, or targeting the exact pinned
   touch timestamp) — not a dev-time requirement. The keyless core (overlay renders, chip logic is
   sound, SIM empty state, live-mode-unchanged) is fully verified and passing.
2. **No frontend test runner exists in this repo** (unchanged from every prior iteration). Frontend
   correctness relies on `tsc --noEmit`, the Python source-inspection precedent, and live browser
   verification (this iteration's was unusually thorough, prompted by the `as_of` bug discovery).
3. **The chip's "rejection" vs. "breakthrough" qualifier in its copy** (e.g. "tape: ask_absorption
   (rejection)") is an addition beyond the plan's own illustrative example string (which showed
   "tape: ask_absorption" without the qualifier). It is derived structurally from which of the two
   SERVED mapping keys matched (never a client-invented rule), and both words are the SAME
   vocabulary the served JSON keys themselves use (`rejection_states`/`breakthrough_states`) — not a
   new hardcoded concept. Flagged for the reviewer in case a stricter reading of "matches the
   example verbatim" is wanted; the DoD's actual acceptance wording ("descriptive copy citing the
   edge report") does not require an exact string match.
