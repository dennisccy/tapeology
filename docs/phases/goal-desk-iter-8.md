# Goal Iteration 8 — Close J-07: era-open baseline, golden restore, missing picture, two hygiene fixes

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 8
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06
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

Close the last open journey of Era B: prove J-07's two still-unverified acceptance clauses
(kept-route byte-identity vs. an era-open baseline; zero out-of-inventory diff, now read subject to
the owner's **R-1** ratification) with real evidence, restore the sentinel's own golden script to
its correct target, take the one browser screenshot J-07 has been missing since iteration 4
(Cockpit Historical mode on a real symbol), and clear two one-line hygiene items — so J-07 can move
from `partial` to `passing` with nothing left carried.

## BACKGROUND

Iteration 7 shipped J-06 (17 MCP tools) and left J-07 `partial` for exactly three reasons, all
documented live in `runs/goal-session-desk/iter-7/eval.md` and the iter-7 audit
(`docs/handoffs/goal-desk-iter-7-audit.md`, findings T1/T3/T4): (1) the owner had not ratified
iteration 4's frozen-file repair; (2) no era-open response baseline was ever captured, so "kept-route
byte-identity" was unverifiable as written; (3) the sentinel's own golden script
(`journey-scripts/J-07.json` step 10) was edited out-of-scope in iteration 7 on a premise the audit
disproved (`demo_runner._check_expect` matches `expect.text` page-wide, so the original
`tradable-map-chart-caption` target was never actually broken). The evaluator STALLED rather than
CONTINUE a fifth time, and asked the owner one question with three options (ratify / revert /
narrow). **The owner has now ratified**: `docs/goal.md` carries a new dated section
`### OWNER RATIFICATION — 2026-07-27 (price-less-bar repair) — R-1` naming the exact eight files and
scoping the exception precisely — reason (1) above is resolved by that edit alone, no code change
needed. This iteration does the remaining, already-fully-specified work for reasons (2) and (3), plus
the one still-missing screenshot the assumptions ledger flagged (iter-7 — goal-evaluator: Cockpit
Historical mode on a real symbol was never photographed; SIM-BUYER honestly cannot show it) and two
one-line cleanups the iter-7 audit found (B1: an order-dependent MCP test; F1: a now-untrue comment).

**Lessons applied:** iter-7's lesson is the direct cause of this iteration's #1 task — a
byte-identical-vs-baseline sentinel clause is unfalsifiable unless the baseline is actually captured;
this iteration captures it from `047c38e` rather than deferring again. The iter-4/iter-5 screenshot
lessons (disclose any capture aid used to photograph a state) apply to the Cockpit Historical
screenshot task below. Per the priority rubric, this is a single, non-risky (pure verification +
two one-line hygiene edits + one golden-script restore), smallest-remaining-scope journey — no
deviation from the rubric was needed.

## IN SCOPE

### Backend
- [ ] Write a one-off, disposable comparison script (not a permanent CLI/route — a scratch script
      under e.g. `scripts/goal-desk-iter8-baseline-diff.py` or an ad-hoc shell recipe documented in
      the handoff) that: (a) creates a scratch `git worktree` at commit `047c38e`; (b) boots that
      worktree's backend against a THROW-AWAY copy of the current `.data/` directory (never the
      ambient store — same discipline as every prior iteration's fixture-scoped rigs); (c) boots the
      current tree's backend against an identical throw-away copy of the same data snapshot; (d)
      curls, with `--max-time`, the same concrete inputs against both backends for every kept GET
      route: `/research/taxonomy`, `/research/datasets`, `/research/datasets/{id}` (one real id),
      `/research/bars`, `/research/bars/{id}`, `/research/bars/{id}/candles`, `/research/candles`
      (AAPL, as-of 2026-06-22 and 2026-07-25), `/research/levels` (AAPL, same as-ofs),
      `/research/tradability` (AAPL, same as-ofs), `/research/setups` (AAPL), `/research/setups/{id}`,
      `/research/pnl/ledger`, `/research/profiles`, `/research/strategies`, `/research/edge-report`
      (AAPL); (e) diffs every pair of response bodies and writes the result — every match, every
      difference, and the named reason for each difference — to a durable report (see TESTING
      REQUIREMENTS). Per `assumptions.md` iter-8, this bounded route/input set is the one this
      iteration commits to; `/meta/ui-routes` is compared too but is EXPECTED to differ (2→3, named
      exempt by goal.md) and the MCP tool-count delta (15→17) is cited from iteration 7's own
      already-proven evidence, not re-diffed against a second MCP server.
- [ ] Run `git diff --name-only 047c38e -- apps/` on the current tree and confirm every listed file
      is accounted for by `docs/goal.md`'s Key Capability file list plus **R-1**'s eight named
      files; record the full file list and the accounting in the same report.
- [ ] Fix `apps/backend/tests/test_mcp_server.py::test_get_endpoint_desk_screen_date_query_proxies_verbatim`
      (iter-7 audit B1) to seed its own screen snapshot (a distinct date from any other test's
      fixture) instead of relying on `test_desk_screen_tool_byte_identical_on_a_populated_state`'s
      side effect, so it passes when run in isolation. No other test in the file is modified.

### Frontend
- [ ] Correct the now-untrue comment at `apps/frontend/app/desk/page.tsx:207` (iter-7 audit F1) —
      it currently claims "each cell's `title` carries the served value in full"; iteration 7's F2
      fix moved that detail onto the row's own drill-in anchor. Comment-only change; zero change to
      any anchor `href`, `absolute inset-0`, `data-testid`, or click geometry.

### Golden script / regression asset
- [ ] Restore `runs/goal-session-desk/journey-scripts/J-07.json` step 10's target from
      `{"testid": "tradable-map-table"}` back to `{"testid": "tradable-map-chart-caption"}` (the
      iter-7 audit's T1: the edit was based on a disproven premise). Prove it with one
      `--mode verify --journeys J-07` deterministic-replay run against a fixture-scoped backend,
      and keep the results file (see TESTING REQUIREMENTS) — the iter-7 audit's exact complaint was
      an unproven claim with no artifact; this iteration must not repeat that.

### Browser evidence
- [ ] Capture the still-missing J-07 screenshot: the Cockpit (`/`) in **Historical** mode on a REAL
      symbol with a recorded bar series (e.g. AAPL) — candles rendered, the timeframe switch visible,
      and the S/R band overlay drawn on the chart. Disclose any capture aid used (per the iter-5
      lesson on disclosing display tricks), though none should be needed for a page-load state.

### New user-facing capability
None — this iteration adds no new page, button, or served value. It closes verification and
hygiene gaps on the already-shipped product.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — Cockpit and Structure render exactly as already shipped; only a code comment changes on
`/desk` (no visible effect).

### Product surface delta
None visible to the user. The delta is evidentiary: J-07's own acceptance clauses gain real proof
where they previously had none or had a disproven substitute.

### Blueprint conformance
No new pages or nav entries. All work targets journeys already homed under Cockpit (`/`) and
Structure (`/structure`) in `blueprint.md`'s Information Architecture; `blueprint.md` has been
updated additively (a "NOTED at iter-8" documentation-currency entry, no Data-Contract row change,
no nav-skeleton change — no reapproval file needed).

### Data-contract additions
None. No new displayed value, computing module, or serving endpoint. The comparison script and its
report are diagnostic artifacts, not product surfaces, and must not be wired into any route the app
serves.

## OUT OF SCOPE

- Any further edit to `apps/backend/app/research/bars.py`, `apps/frontend/components/StructureChart.tsx`,
  `apps/frontend/components/PriceChart.tsx`, or any guard test — **R-1** ratifies the iteration-4
  changes as-is and explicitly does NOT reopen any of these files to further edits.
- The same-date screen ambiguity, keyboard access for history rows, and the three older one-line
  hardening items (guard `run_screen_and_record`, finite-price filter on the per-series bar read,
  re-tighten the relaxed chart guard test) — carried, not forced, per iteration 7's own
  recommendation. None of them block J-07's written acceptance text.
- Any new `Config` field, new route, new page, or new MCP tool.
- Re-verifying J-06 (17 tools, byte-identical proxies) — already DONE and live-proven per
  `iteration-state.md`'s "Do not redo" list; cite iteration 7's evidence instead of re-running it.
- Re-verifying J-01–J-05's own acceptance clauses beyond the smoke-set regression replay — they are
  "Do not redo" per `iteration-state.md`.
- Widening the comparison script into a permanent tool, CLI command, or CI gate — it is a one-off
  diagnostic for this iteration's evidence requirement only.

## DEFINITION OF DONE

- [ ] J-07's kept-route byte-identity clause is verified against a real era-open (`047c38e`)
      baseline, with every difference (if any, beyond the two named exemptions) explained and
      attributed to **R-1** or flagged as a defect.
- [ ] J-07's "zero out-of-inventory changes" clause is verified: the full `git diff --name-only
      047c38e -- apps/` file list is accounted for by goal.md's Key Capability inventory plus R-1's
      eight files, with the accounting written down.
- [ ] `runs/goal-session-desk/journey-scripts/J-07.json` step 10 is restored to
      `tradable-map-chart-caption` and proven via a kept `--mode verify --journeys J-07` results
      file.
- [ ] A screenshot of the Cockpit in Historical mode on a real symbol (candles + timeframe switch +
      band overlay) exists and is opened by browser-qa-agent.
- [ ] `test_get_endpoint_desk_screen_date_query_proxies_verbatim` passes both in the full suite and
      when run in isolation (`pytest -k`).
- [ ] `apps/frontend/app/desk/page.tsx:207`'s comment matches the F2-fixed reality (tooltip detail
      lives on the row's drill-in anchor, not per-cell).
- [ ] J-07 passes via browser-qa-agent (full kept-product walk: sim cockpit, historical cockpit on a
      real symbol, Structure AAPL wall, Case Studies drill-in, Edge Report honest state).
- [ ] Required-still-passing journeys J-01–J-06 remain green (deterministic replay + LLM fallback).
- [ ] No anti-goal violation introduced; the one previously-carried "Frozen foundations" item is
      resolved by the owner's R-1 ratification landing in `docs/goal.md` before this iteration
      started (verify it is present and byte-matches what was ratified — do not re-word it).
- [ ] Full backend suite passes at or above the 1341 passing / 8 skipped floor; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-8-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (full kept-product walk, including the new Historical-cockpit screenshot); smoke
  replay of J-01, J-02, J-03, J-04, J-05, J-06 (deterministic golden scripts where present, LLM
  fallback otherwise).
- Unit/integration: `apps/backend/tests/test_mcp_server.py` (the fixed date-lookup test, in isolation
  and in the full suite); full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/
  -q`).
- Diagnostic (not a pytest gate, but a required artifact): the era-open vs. current kept-route diff,
  written to `reports/goal-desk-iter-8-kept-route-baseline.md` (route-by-route table: route, inputs,
  match/differ, reason if differing) — this is the evidence backing DoD items 1 and 2.
- Error cases: the comparison script must handle a route that 404s or errors identically on BOTH
  backends (still a "match", recorded as such) versus one that errors on only one side (a real
  difference, must be explained, never silently dropped from the report).

Test-first contract — TC- scenarios:

- TC-1: given a scratch worktree at commit `047c38e` booted against a throw-away copy of `.data/`,
  and the current tree booted against an identical throw-away copy, when the same concrete inputs
  (AAPL as-of 2026-06-22 and 2026-07-25, the fixture universe, one real dataset id) are curled
  against every kept GET route listed in IN SCOPE, then every response body matches byte-for-byte
  except the bar/candle-backed reads for the 60 series R-1 names, and `reports/goal-desk-iter-8-kept-route-baseline.md`
  records each route's match/differ status with the reason for every difference.
- TC-2: given the same two-backend setup, when `/meta/ui-routes` is compared, then it shows exactly
  2 rows on the era-open backend and exactly 3 rows on the current backend, and the report states
  this is the expected, goal.md-named exemption, not a defect.
- TC-3: given the current tree, when `git diff --name-only 047c38e -- apps/` is run, then the
  resulting file list is fully accounted for by `docs/goal.md`'s Key Capability inventory plus
  R-1's eight named files, and the report states this explicitly with the full file list shown.
- TC-4: given `runs/goal-session-desk/journey-scripts/J-07.json` step 10's target restored to
  `{"testid": "tradable-map-chart-caption"}`, when the deterministic replay runner is invoked with
  `--mode verify --journeys J-07` against a fixture-scoped backend, then the run reports 0 failed
  and a results file is saved (not discarded) recording step 10 as PASS.
- TC-5: given a fixture-scoped or the throw-away real-data backend with AAPL bars recorded, when the
  Cockpit is opened, "Historical" mode is selected, AAPL is watched, and a timeframe is switched,
  then a screenshot shows rendered candles, the active timeframe control, and the S/R band overlay
  drawn on the chart.
- TC-6: given `apps/backend/tests/test_mcp_server.py`, when
  `pytest -k test_get_endpoint_desk_screen_date_query_proxies_verbatim` is run alone (no other test
  in the file executed first), then it passes with exit code 0 because the test now seeds its own
  screen snapshot under a date no other test uses.
- TC-7: given `apps/frontend/app/desk/page.tsx` after the comment fix, when the text around line 207
  is read, then it states the full-precision tooltip detail is reachable via the row's drill-in
  anchor's composite `title`, and makes no claim that each cell carries its own `title`.
- TC-8: given the fixture-scoped backend, when the full backend suite is run
  (`.venv/bin/python -m pytest tests/ -q`), then it reports 0 failures at or above 1341 passing / 8
  skipped, and `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-9: given the current tree after all fixes above, when browser-qa-agent replays J-07's full
  acceptance walk (sim cockpit `SIM-BUYER`, historical cockpit on AAPL, Structure AAPL wall at
  as-of 2026-06-22, Case Studies drill-in, Edge Report honest "not computed yet" panel), then every
  step is screenshot-evidenced and none shows a broken or crashed page.
- TC-10: given J-01–J-06's golden scripts under `runs/goal-session-desk/journey-scripts/`, when the
  deterministic replay lane runs them against a fixture-scoped backend, then every one reports PASS
  with no write-path side effect on the ambient `.data/` store.

## NOTES

- `docs/goal.md` already carries the owner's ratification (`### OWNER RATIFICATION — 2026-07-27
  (price-less-bar repair) — R-1`, option 1 of the three the iter-7 evaluator offered). This
  iteration must NOT re-word, shorten, or move that section — only read it and confirm it resolves
  the previously-carried anti-goal item.
- The comparison script's throw-away data copies MUST be scoped (own `TMPDIR`/dataset-dir env vars
  per the era's fixture-scoped-rig recipe) — never point either backend at the ambient
  `apps/backend/.data/`. Remember `export TMPDIR TMP TEMP` per the environment note before running
  any command that writes temp files.
- If the era-open (`047c38e`) worktree's backend cannot start against the throw-away data copy for
  any environment reason (missing dependency pin, etc.), do not silently skip the clause — report
  the exact failure and fall back to the iter-7 audit's static-proof method (diff the route-handler
  source between `047c38e` and current tree) as an explicitly-labeled substitute, same discipline
  the iter-7 audit already used for T3.
- This is expected to be the era's closing iteration if J-07 passes cleanly — but the goal-decomposer
  does not declare GOAL_ACHIEVED; that is the evaluator's call after real evidence lands.
