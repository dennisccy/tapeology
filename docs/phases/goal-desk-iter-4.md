# Goal Iteration 4 — The `/desk` briefing page ships (J-04)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-07
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
    BESIDE the kept two pages — the one sanctioned kept-surface edit is J-05's additive
    `/structure` prefill.) *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
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
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability
    test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged
    by the sentinel every iteration. *(critical)*

## GOAL

The operator can open a new third page, `/desk`, click one "Run Screen" button, watch it compute
live, and read a dense, honest, provenance-carrying briefing of today's ranked tradable walls
across the registered universe — the nav becomes Cockpit · Structure · Desk.

## BACKGROUND

J-01/J-02/J-03 are `passing` (iter-1/2/3, each independently re-verified live by the evaluator);
J-04, J-05, J-06 are `failing`; J-07 is `partial` (kept-product half fully evidenced, its two
era-completion clauses — nav = 3 routes, MCP = 17 tools — structurally unmet at 2 routes / 15
tools). Per the priority rubric: no journey regressed (rule 1 n/a), the last `coherence.md` was
`COHERENCE-PASS` (rule 2 n/a), and J-04 is the clear unblocker (rule 3) — it is the FIRST frontend
surface this era, the only journey with zero upstream dependency left unmet (J-01/J-02/J-03 already
ship everything J-04 reads), and it is what J-05's drill-in and half of J-07's era-completion clause
both need to exist first. iter-3's `eval.md` recommends targeting J-04 alone at full depth; this
spec follows that recommendation and its five numbered MUST-carry items in full (chip-copy honesty,
an honest reuse signal, freshness labelling, browser-pass prerequisites, three hygiene items).

**Depth: full, trigger 1 (structural/cross-cutting).** This is the era's first frontend iteration —
a brand-new page, the FIRST `UI_ROUTES` nav-skeleton change of the era (2 → 3, a blueprint
Information-Architecture change the coherence gate must re-audit), touching `app/meta.py`,
`desk_routes.py`, `desk_screen_compute.py`, `desk_universe.py`, and the entire new frontend surface
— none of it covered by any single existing journey's tests. No trigger-2/3/4 applies (no persisted
schema change; last verdict was `CONTINUE` not `ESCALATE`; 0 consecutive lean iterations dispatched
so the hardening cadence is not met) — trigger 1 alone is sufficient and is why `full` is not
optional here (audit + ux-regression + closure + browser QA all apply, per iter-3's own framing).

**Lessons applied (see `lessons.md` — do not repeat these mistakes):**
- iter-0: `journey-scripts/J-07.json` step 8's assertion is cache-warmth-dependent and has never
  actually been replayed yet (browser QA never ran through iter-0..3, all backend-only) — THIS is
  the first iteration that will replay it. Fixed below (backend scope + NOTES).
- iter-0/iter-1: the scoped QA backend's FIRST real `/research/setups` and `/structure` Load calls
  are cold (minutes, not seconds) after iter-1's `edge_report_cache._config_content_hash` move —
  warm before dispatching browser QA, budget for the first call regardless.
- iter-2: coverage is per-`(symbol, timeframe)`, not per-member — MSFT has `1h`/`1d` but no
  `1w`/`4h` at era open. `/desk`'s coverage badges must render this honestly (per-timeframe
  true/false), never assume a symbol with SOME bars has ALL pinned timeframes.
- iter-3: two sibling append-only stores diverged on the same corrupt-file-overwrite failure mode.
  Ported below (backend scope item).
- iter-3: never carry a measured number from a QA/dev report into a golden or spec without
  re-deriving it against the ACTUAL data basis used (fixture vs. ambient store) — applies to any
  numeric value this iteration's dev/QA reports quote from `/desk`'s rendered rows.

## IN SCOPE

### Backend

- [ ] Append `{"path": "/desk", "label": "Desk", "nav": True}` as the THIRD entry of `UI_ROUTES`
      in `app/meta.py` (after Structure) — nav and the MCP `ui_route_map` tool follow automatically
      via the existing `GET /meta/ui-routes` proxy; never hand-edit `NavBar.tsx`.
- [ ] Update `apps/backend/tests/test_meta_routes.py`'s route-count assertions
      (`test_ui_routes_lists_exactly_the_live_routes`, `test_ui_routes_top_bar_entries_match_the_rendered_nav_set`,
      and any other hardcoded 2-route literal in that file) to the new 3-route list, in the SAME
      commit as the `UI_ROUTES` change — the file's own documented "a route ships here in the same
      iteration its page ships" precedent, applied to its test coverage too.
- [ ] `desk_screen_compute.py`'s `DeskScreenComputeManager`: thread an honest `reused: bool` +
      `screen_id: str | None` onto the job snapshot, distinguishing "this job's walk is what
      created the persisted snapshot" from "this job's walk found an already-recorded snapshot
      under the same 5-pin key and changed nothing" (audit B2). Zero change to `compute_screen`'s
      row/skip computation and zero change to `ScreenStore`'s PERSISTED snapshot shape — only the
      process-scoped compute-manager snapshot (`POST`/`GET /research/desk/screen/compute`) gains
      the two fields.
- [ ] Refuse — never persist — a `POST /research/desk/screen/compute` trigger when no universe
      snapshot is registered: an honest 4xx error naming the missing universe, mirroring the
      top-up CLI's own no-universe message (`desk_topup_compute.py:352-356`); `ScreenStore.list()`
      must show zero new records for this case, both before and after the call (closes audit B4).
- [ ] Port `ScreenStore.record`'s corrupt-file `.exists()` guard (`desk_screen.py:467-473`) into
      `UniverseStore.record` (`desk_universe.py:418`) — raise an integrity error instead of
      silently overwriting a damaged file sitting at the same content-checksum path (closes iter-1
      audit B3 / iter-3's lesson).
- [ ] Scope `TAPEOLOGY_DATASET_DIR` inside `test_desk_screen_compute.py`'s `route_ctx` fixture
      (`apps/backend/tests/test_desk_screen_compute.py:405-423`) — it currently reads the ambient
      `.data/datasets` tree instead of a temp dir, the ONE `route_ctx` in this file's siblings that
      doesn't scope it. Test hygiene only, zero production code change (closes audit T3).
- [ ] Browser-QA / replay prerequisite (test-infra, not application code — do this BEFORE
      dispatching browser QA or the replay lane): warm the `tradability_cache` for AAPL as-of
      `2026-06-22T21:00:00Z` (one `/structure` Load, or an equivalent direct
      `GET /research/tradability` call) on the SAME backend instance that will serve both browser
      QA and the deterministic replay lane — closes the `edge_report_cache._config_content_hash`-
      stranded-cache latency carried since iter-1 (cold `/structure` Load measured ~21.6s).
- [ ] `journey-scripts/J-07.json` step 8 (test-infra, not application code): set this step's own
      `"timeout_ms": 20000` (the replay engine's hard-clamped maximum — `demo_runner.py`'s
      `min(int(step.get("timeout_ms", default_tmo)), 20000)`) instead of inheriting the file's
      `15000` default. Keep the assertion itself on the rendered AAPL band-boundary text — confirmed
      this iteration to be a plain HTML `<td data-testid="tradable-band-range">` cell
      (`structure/page.tsx`'s `BandRow`/`BandsTable`), never chart/SVG-embedded, so the ONLY risk
      factor is fetch latency, not a text-matching mismatch. Paired with the cache warm-up above,
      this closes the golden false-negative risk carried since iter-0 (see NOTES).

### Frontend

- [ ] New page `apps/frontend/app/desk/page.tsx` (`/desk`), matching the established dark/dense/
      terminal-grade style (`Panel`, local `EmptyState`/`LoadingPanel`/`UnavailablePanel`-style
      helpers, the `structure/page.tsx` visual conventions):
  - Honest empty state showing the exact text `"Desk screen not computed yet."` plus an enabled
    "Run Screen" button, rendered if-and-only-if `GET /research/desk/screen`'s `latest === null`
    (distinct from a screen that ran and found nothing tradable — see the next bullet).
  - Latest-screen briefing table: in the snapshot's OWN served row order — symbol, side, band-class
    chip, distance-bps chip, band score, per-timeframe coverage badge (each timeframe's `has_bars`
    rendered honestly true/false per iter-2's lesson — never assumed), tick-evidence badge — all
    read verbatim from `latest.rows`. The headline-band chip copy reads "nearest same-class band"
    (assumptions.md iter-4 entry 1 — `_select_best_band` itself stays byte-unchanged).
  - Skipped-members section grouped under an honest heading, distinguishing `no_bars` from
    `no_basis` reasons verbatim from `latest.skipped` — renders even when `rows` is empty but
    `skipped` is not (a real screen that skipped every member is NOT the same state as no screen
    ever existing).
  - Provenance line: universe snapshot id + date, `as_of`, `config_fingerprint`, and
    `bar_store_signature` labeled **"Bar-store signature"** with a caption stating it is a checksum
    over every member's window-last-requested timestamp — verbatim from the rendered snapshot.
    **AMENDED during the iter-4 fix pass (audit F1):** this line originally required the label
    "window last requested" for `bar_store_signature`. That value is
    `sha256(sorted (symbol, timeframe, latest_window_end_utc) tuples)[:16]` (`desk_screen.py:172-182`)
    — a checksum, not a timestamp — so honouring the label rendered
    `Window last requested   d7bc8f8127904d0a`, a false claim about what the value is. The
    freshness label stays where it is true: each per-timeframe coverage badge's
    `latest_window_end_utc` tooltip (never "last bar" — audit B9/iter-2 B2). `blueprint.md`'s
    registered wording is amended in the same commit.
  - Read-only screen-history list: each entry's date + `rows`/`skipped` counts + provenance
    summary, from `GET /research/desk/screen`'s meta-only `screens` list — no click/select
    interaction and no per-entry full-row fetch (J-05 scope, deferred).
  - "Run Screen" button: `POST /research/desk/screen/compute` with `screen_date` set to the
    client's own today (the SAME `todayUtcDate()`-style helper `/structure`'s "Today" shortcut
    already uses — assumptions.md iter-4 entry 2); poll `GET /research/desk/screen/compute` while
    `state === "running"`; on a terminal state, refetch `GET /research/desk/screen`; an in-flight
    second click observes the SAME job (`started: false`), never starts a second one; a Cancel
    control while running posts `/research/desk/screen/compute/cancel`. Mirrors the Edge Report
    Compute button's UX pattern (`NotComputedPanel`/poll-loop in `structure/page.tsx`).
  - "Top-up" button: `POST /research/desk/topup/compute`, poll `GET /research/desk/topup/compute`,
    cancel via `POST /research/desk/topup/compute/cancel`; live `pairs_done`/`pairs_total`
    progress. Same UX pattern; this is the FIRST-EVER UI surface for the J-02 top-up compute
    manager (previously CLI/POST-only).
  - Page-load GETs (`/research/desk/screen`, `/research/desk/screen/compute`,
    `/research/desk/topup/compute`) never trigger a compute as a side effect — mount issues GETs
    only, zero POST without an explicit button click.
- [ ] `apps/frontend/lib/api.ts`: add `fetchDeskScreen`, `triggerDeskScreenCompute`,
      `fetchDeskScreenCompute`, `cancelDeskScreenCompute`, `triggerDeskTopupCompute`,
      `fetchDeskTopupCompute`, `cancelDeskTopupCompute` — mirror
      `triggerEdgeReportCompute`/`fetchEdgeReportCompute`/`cancelEdgeReportCompute`'s exact
      `{ok, data, error}` shape and 422/unreachable-fold behavior byte-for-byte.
- [ ] `apps/frontend/lib/types.ts`: add the desk screen snapshot/row/skip TS interfaces and the two
      compute-snapshot interfaces (`DeskScreenComputeSnapshot` including `reused`/`screen_id`,
      `DeskTopupComputeSnapshot`), matching `blueprint.md`'s registered shapes field-for-field.

### New user-facing capability

The operator can open a third page, `/desk`, click "Run Screen," watch it compute live, and read a
dense ranked briefing (with full provenance) of which of the registered universe's symbols have the
closest tradable walls today — without visiting `/structure` symbol-by-symbol.

### New information displayed

The latest screen's ranked rows (symbol/side/class/distance/score/coverage/tick-evidence),
honestly-grouped skipped members, the screen's full provenance line, a read-only screen-history
list, and live Run-Screen/Top-up progress.

### New user actions

"Run Screen" (single-flight trigger, live progress, cancel) and "Top-up" (single-flight trigger,
live progress, cancel) — both new buttons on `/desk`.

### UI surface changes

One new page, `/desk`, added as the third persistent top-nav entry (after Structure).

### Product surface delta

The product becomes a three-page desk (Cockpit / Structure / Desk) instead of two; the operator's
day can now start on `/desk` instead of picking a symbol blind on `/structure`.

### Blueprint conformance

`/desk` lives under the "Desk" nav section — the EXISTING Information Architecture home already
registered in `blueprint.md` (`Feature/journey homes`: "J-04 `/desk` briefing page | `/desk` |
Desk") and the Navigation skeleton's pre-planned third row. This iteration REALIZES a planned home;
it does not invent a new one, so no nav-skeleton reapproval is needed.

### Data-contract additions

`reused: bool` + `screen_id: str | None` — additive fields on the ALREADY-registered "Screen
compute progress" Data-Contract row (computed by the SAME `app/research/desk_screen_compute.py`
`DeskScreenComputeManager`, served by the SAME `POST/GET /research/desk/screen/compute`) —
registered in `blueprint.md` this iteration (see the "RESOLVED at iter-4" note there). No wholly
new value/row is introduced; every other value `/desk` displays is read verbatim from an
already-registered Data Contract row.

## OUT OF SCOPE

- J-05 (screen-history click-through rendering a PAST snapshot's own rows verbatim;
  `/structure?symbol=&asof=` query-param prefill + auto-Load; per-row drill-in links) — next
  iteration; the screen-history list this iteration is read-only display.
- J-06 (MCP contract v3, 17 tools; `desk_universe`/`desk_screen` MCP proxies) — `_STATIC_PATHS` and
  `EXPECTED_TOOLS` (still 15) stay untouched this iteration.
- Any change to `_select_best_band`'s ranking tuple, `compute_screen`'s row/skip computation,
  `compute_tradability`, `levels.py`, `bar_index.py`, or `config.py` — all zero-diff
  this iteration (assumptions.md iter-4 entry 1; TC-17 below).
- **`bars.py`'s zero-diff constraint is LIFTED for the priceless-bar rail only** (amended during the
  iter-4 fix pass, per audit B1's own remediation §5 item 1: "Requires lifting `bars.py`'s zero-diff
  constraint explicitly in that iteration's spec"). The lift is scoped to: a write-path refusal of a
  bar carrying a non-finite OHLC price, and the read-side exclusion of an already-recorded priceless
  ROW from the merged fold (reported through the existing `integrity_errors` channel). No candle
  arithmetic, no checksum definition, no cursor semantics, and no `Config` field changes — the pin
  stays `08e471b10130e1e2` (`bars.py` contributes nothing to it). Same lift for
  `components/StructureChart.tsx`: a finite-value guard before `setData` so one unusable row degrades
  the chart instead of unmounting the page (audit B1 §5 item 2, "Requires sanctioning a kept-surface
  edit"); identical output for all-finite data, which is every existing test and every fixture.
- A date-picker or any alternate-screen-date UI control on `/desk` — Run Screen always targets the
  client's own today this iteration (assumptions.md iter-4 entry 2); the CLI's `--date` remains the
  path for an arbitrary historical re-screen.
- Any change to `/structure`, `PriceChart.tsx`, `StructureChart.tsx`, or the Cockpit (`/`) — kept
  byte-identical this iteration (J-07's own regression clause).
- A live 100-symbol universe fetch, top-up, or screen run as a test/CI gate — stays keyless/
  fixture-based; any real run is operator-verified and reported as such, never a suite requirement.
- Any new `Config` field — zero this iteration, continuing the iter-1/2/3 precedent.

## DEFINITION OF DONE

- [ ] J-04 passes via browser-qa-agent — the three screenshots named in `docs/goal.md`'s J-04
      acceptance (empty state + enabled Run Screen; populated ranked rows + provenance + honest
      skipped grouping; live progress + single-flight refusal), each also showing the top nav
      reading Cockpit · Structure · Desk
- [ ] `GET /meta/ui-routes` lists exactly three routes (`/`, `/structure`, `/desk`) in nav order —
      mechanically verified
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-07 remain green (deterministic replay +
      LLM fallback where no golden exists on file)
- [ ] No anti-goal violation introduced (membership never a signal; snapshots append-only; every
      run an explicit operator act; briefing copy descriptive-only; single source of truth; zero
      new `Config` field; pin unchanged)
- [ ] Unit tests pass; suite pass count non-decreasing off the 1299-passed/8-skipped floor; zero
      new failures
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-4-dev.md`

## TESTING REQUIREMENTS

- Browser: J-04 (three screenshots per `docs/goal.md`'s acceptance — empty state, populated
  briefing, live-progress/single-flight; nav bar visible in each). J-07's kept-product regression
  walk (sim cockpit `SIM-BUYER` settling Buyer Control; `/structure` Load for pinned AAPL as-of
  2026-06-22 rendering the 300–302.4 wall; Case Studies drill-in; Edge Report honest state) —
  re-verified with the golden-script timeout fix and cache warm-up in place (TC-16).
- Unit/integration: `test_meta_routes.py`'s widened route-count assertions; a new/extended test
  proving `reused`/`screen_id` distinguish a fresh compute from a pure reuse; a new test proving
  the no-universe refusal persists zero records; a new test proving `UniverseStore.record`'s
  corrupt-file guard (mirrors the existing `ScreenStore` one); `route_ctx`'s `TAPEOLOGY_DATASET_DIR`
  scoping fix; the existing (unmodified) `test_lint_frontend_source_literals_are_clean` walk
  covering the new `/desk` page automatically.
- Error cases: `POST /research/desk/screen/compute` with no universe registered (4xx, zero records
  persisted); a second `POST` while one is running (single-flight, `started: false`); a corrupt
  universe-snapshot file at a re-registered checksum (integrity error, no overwrite, no second
  file); backend-unreachable while polling either compute endpoint (UI keeps the last known state,
  never fabricates a snapshot).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one of the following scenarios.

- TC-1: given the fixture-scoped backend has a registered universe but no screen has ever been
  computed, when the operator opens `/desk`, then the page shows the text
  "Desk screen not computed yet." and an enabled "Run Screen" button (screenshot).
- TC-2: given `/desk` is open with no screen computed, when the operator clicks Run Screen, then
  `POST /research/desk/screen/compute` fires with `screen_date` set to the client's today, the
  button reflects a running/progress state, and a same-session second click while running is
  refused — the UI shows the SAME in-flight job, no second POST starts a second job (screenshot).
- TC-3: given a screen compute reaches `state: "done"`, when `/desk`'s poll observes the terminal
  state, then the page renders a briefing table with ranked rows (symbol, side, band-class chip
  reading "nearest same-class band" where applicable, distance-bps chip, band score, per-timeframe
  coverage badge, tick-evidence badge) read verbatim from the snapshot's `rows`, and skipped
  members render grouped under an honest heading distinguishing `no_bars` from `no_basis` reasons
  (screenshot).
- TC-4: given a completed screen snapshot, when `/desk` renders its provenance line, then it shows
  the universe snapshot id + date, `as_of`, `config_fingerprint`, and `bar_store_signature`
  verbatim from the snapshot. **AMENDED (audit pass, consistency with the IN SCOPE bullet above):**
  this case originally required `bar_store_signature` to be labeled "window last requested"; the
  fix-pass amendment at lines 165-172 replaced that label with **"Bar-store signature"** (plus the
  checksum caption) precisely because the value is a digest, not a timestamp, and TC-4 was left
  un-amended — a contradiction the iter-4 QA pass then reported as a PASS against the retired
  wording. The freshness label ("window last requested", never "last bar" — audit B9/iter-2 B2)
  belongs to each per-timeframe coverage badge's `latest_window_end_utc` tooltip, which is the
  value that really is a window end; that half of the case stands unchanged.
- TC-5: given `/desk`'s screen-history list, when it renders, then each entry shows the screen's
  date and its `rows`/`skipped` counts read verbatim from `GET /research/desk/screen`'s meta-only
  `screens` list, with no click/select interaction and no per-entry full-row fetch.
- TC-6: given this iteration's `UI_ROUTES` change, when `GET /meta/ui-routes` is called, then it
  returns exactly three entries in order `[{"/","Cockpit"}, {"/structure","Structure"},
  {"/desk","Desk"}]`, and the rendered top nav shows Cockpit · Structure · Desk (screenshot).
- TC-7: given a desk-screen compute job whose 5-pin key already has a recorded snapshot, when
  `GET /research/desk/screen/compute` is polled after it resolves, then the snapshot carries
  `reused: true` and `screen_id` equal to the EXISTING snapshot's id, and `ScreenStore.list()`
  shows no new file was written.
- TC-8: given a desk-screen compute job that persists a brand-new snapshot, when
  `GET /research/desk/screen/compute` is polled after it resolves, then the snapshot carries
  `reused: false` and `screen_id` equal to the newly-created snapshot's own id.
- TC-9: given no universe snapshot is registered, when `POST /research/desk/screen/compute` is
  triggered, then it returns an HTTP 4xx response naming the missing universe, no background job
  starts, and `ScreenStore.list()` returns zero records both before and after the call.
- TC-10: given a universe snapshot file already on disk at a content-checksum path that fails its
  integrity check, when `UniverseStore.record` is called with content hashing to that same
  checksum, then it raises an integrity error (mirroring `ScreenStore.record`'s guard), the damaged
  file's bytes stay byte-unchanged, and no second file is written.
- TC-11: given the desk-screen compute manager has an in-flight job, when a second
  `POST /research/desk/screen/compute` arrives, then it returns `started: false` and the SAME job
  snapshot (same `id`) — never a second concurrent job.
- TC-12: given the Top-up button on `/desk`, when clicked, then `POST /research/desk/topup/compute`
  fires, live progress (`pairs_done`/`pairs_total`) renders while `state === "running"`, and
  clicking Cancel issues `POST /research/desk/topup/compute/cancel` and the button reflects a
  cancelling/cancelled state.
- TC-13: given all frontend source under `apps/frontend/app/desk`, when
  `tests/test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` runs, then it
  reports zero imperative/predictive/certainty-claim violations — the existing lint, unmodified.
- TC-14: given AAPL's headline screen row is not its highest-scoring same-class band, when `/desk`
  renders that row's chip, then the chip text reads "nearest same-class band" and `desk_screen.py`'s
  `_select_best_band` function shows zero diff from before this iteration.
- TC-15: given `apps/backend/tests/test_meta_routes.py`, when the suite runs after `/desk` ships,
  then its route-count assertions expect exactly three routes (Cockpit, Structure, Desk) in nav
  order, updated in the same commit as the `UI_ROUTES` change.
- TC-16: given `journey-scripts/J-07.json` step 8 and a fixture-scoped backend with the
  `tradability_cache` pre-warmed for AAPL as-of `2026-06-22T21:00:00Z`, when the deterministic
  replay lane runs J-07, then step 8's expected band-boundary text is observed within its own
  `timeout_ms: 20000` budget — no golden false-negative.
- TC-17: given the frozen research modules (`config.py`, `tradability.py`, `levels.py`,
  `bar_index.py`), when this iteration's diff is inspected, then all four show zero changed lines
  and `Config().config_fingerprint()` still prints `08e471b10130e1e2`. **AMENDED (fix pass):**
  `bars.py` is no longer in this set — see the OUT OF SCOPE lift above; its diff must contain
  nothing beyond the priceless-bar rail.
- TC-22 (fix pass, audit B1): given a vendor row whose OHLC are all `NaN`, when `YahooAdapter.
  fetch_bars` maps the response, then that row is dropped as an absent bar (the surrounding real
  bars byte-identical), an all-priceless window raises `NoDataForWindow`, and `BarStore.record`
  independently refuses any bar carrying a non-finite price — nothing reaches disk.
- TC-23 (fix pass, audit B1): given the 60 series already on disk holding one priceless row each,
  when `GET /research/candles` serves that pair, then no served candle carries a `null` price, the
  exclusion is reported in `integrity_errors` naming the file, every real bar is byte-identical to
  before, and the file's bytes are unchanged (append-only). `/structure`'s Tradable-Map chart for the
  pinned AAPL as-of 2026-06-22 renders `300.11–302.2` and survives with zero page errors.
- TC-24 (fix pass, audit T1): given `journey-scripts/J-07.json`, when the replay lane runs it, then
  after the Load assertion it also asserts the chart caption is still visible and a chart canvas
  exists — so a runtime error arriving after the first matching string can no longer replay as PASS.
- TC-18: given a completed screen where every member was skipped (`rows: []`, `skipped`
  non-empty), when `/desk` renders it, then it shows the (empty) ranked-rows section and the
  skipped-members grouping — never the "Desk screen not computed yet." message, which renders only
  when `latest === null`.
- TC-19: given `/desk` on initial mount, when the page loads, then only GET requests reach
  `/research/desk/screen`, `/research/desk/screen/compute`, and `/research/desk/topup/compute` —
  zero POST fires without an explicit Run Screen/Top-up click.
- TC-20: given the full backend suite, when it runs after this iteration's changes land, then it
  reports a non-decreasing pass count off the 1299-passed/8-skipped floor with zero new failures,
  and `desk_universe.py`/`desk_coverage.py`/`desk_topup_compute.py`/`desk_screen.py`'s existing
  (pre-iter-4) tests all still pass unmodified except the two named additions (the corrupt-file
  guard test, the no-universe-refusal test).
- TC-21: given the backend is unreachable while `/desk` polls either compute endpoint, when a poll
  tick fails, then the UI keeps the last known snapshot state (never fabricates one) — mirrors
  `fetchEdgeReportCompute`'s `{ok:false, data:null}` fold.

## NOTES

- **Primary driver:** iter-3's `eval.md` "Next-Step Recommendation" (target J-04 alone, full
  depth) — its five numbered MUST-carry items are items 1-5 under Backend/Frontend IN SCOPE above
  (chip-copy honesty = item 1 → assumptions.md entry 1; honest reuse signal = item 2 →
  `reused`/`screen_id`; freshness labelling = item 3; browser-pass prerequisites = item 4 → the two
  test-infra Backend bullets + fixture-scoped-backend note below; the three hygiene items = item 5).
- **Browser-QA environment:** dispatch against a FIXTURE-SCOPED backend (per J-04's own acceptance,
  "keyless via the fixture-scoped backend") — scope `TAPEOLOGY_DESK_UNIVERSE_DIR`/
  `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR` at a temp dir seeded with the committed
  103-member universe fixture and the committed AAPL/MSFT bar fixtures already used by
  `test_desk_screen.py`/`test_desk_screen_compute.py` (the `real_ctx`/`route_ctx` test-fixture
  pattern, materialized as real files for the browser-qa process). A screen run against the REAL
  ambient `.data/` store instead would render ~100 honest `skipped: no_bars` rows against only 2-3
  real ones — technically honest, but not what J-04's acceptance asks the screenshots to show, and
  `desk_screen.py` deliberately bypasses `TradabilityCache` so the first real symbol's compute is
  several seconds cold regardless.
- **`journey-scripts/J-07.json` step 8** has never actually been replayed before this iteration
  (browser QA was `SKIPPED` every iteration through iter-3, `Frontend Present: no`) — this is the
  FIRST iteration where its false-negative risk is live. Do the cache warm-up AND the timeout bump
  before dispatch; if replay still fails step 8 while the LLM lane passes, treat it as a golden
  false-negative (not a J-07 regression) and re-open the golden fix rather than scoring J-07 down.
- **T-9 clean rebuild:** `rm -rf apps/frontend/.next` and rebuild, restart both processes, before
  any browser verification this iteration (the stale-build trap — first frontend build of the era).
- **Do not re-verify J-01/J-02/J-03's internals** — `journey-history.json` carries their
  clause-by-clause evidence already. Their Required-still-passing check this iteration is the
  suite + pin + the targeted diffs named above (zero diff elsewhere in `desk_universe.py`,
  `desk_coverage.py`, `desk_topup_compute.py`, and `desk_screen.py`'s row/skip computation).
