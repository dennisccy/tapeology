# Goal Iteration 10 — J-08 evidence: the literal fresh-vs-stale basis screenshot

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 10
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Anti-goal reminders:**

  **Immutable rails — the identity of the project (from
  [`docs/research-directions.md`](research-directions.md) §0.3; enforced by existing tests and
  audits; only ever grow more specific, never weaker):**

  1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
     trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
     tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
     fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
     imperative trading cues. *(critical)*
  3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
     states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
     surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
     a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk`
     BESIDE the kept two pages — the sanctioned kept-surface edits are J-05's additive `/structure`
     prefill and **R-1**'s price-less-row repair, which changes no output for finite data and leaves
     every recorded series on disk untouched.) *(critical)*
  4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
     through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
     labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
     feeds/fingerprints to manufacture a survivor. *(critical)*
  5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
     *(critical)*
  6. **Single source of truth** — each shared value is computed once, owned by one canonical
     endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
     violations. *(critical)*
  7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
     requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
     research artifact.
  8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
     MCP surface can change state. *(critical)*
  9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never
     re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
     *(critical)*
  10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
      explicit, logged act. *(critical)*

  **Desk-era anti-goals (added, not weakening any rail above):**

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

Close J-08's one remaining acceptance clause — one `/desk` screenshot legibly showing a
reading-age-≤2-day-old row beside a reading-age-≥10-day-old row, in the same image — by computing
the desk screen for `screen_date=2026-07-25` inside a scoped, throwaway copy of the data folder and
capturing that screenshot there, with zero change to any product code.

## BACKGROUND

Iteration 9 shipped J-08 completely and honestly: `basis_as_of`/`basis_age_days` are byte-identical
to `compute_tradability`'s own values, legacy snapshots fall back to an honest "basis not recorded
in this snapshot", the guard test proves zero extra reads, the suite is green, and the pin holds.
Its one required screenshot, though, was captured at `as_of` = the run's own wall-clock "today"
(2026-07-27), whose freshest recorded daily bar is 3 days old — missing goal.md's literal "≤ 2 d
fresh row" half by one day. Iteration 9's own test plan wrote itself an undisclosed-to-`goal.md`
allowance to accept a 3 d/14 d spread instead of the literal thresholds; the evaluator
refused it (`CONTINUE`, not `GOAL_ACHIEVED`) — a downstream test plan cannot amend `docs/goal.md`'s
own acceptance text, this session's own iter-7 precedent. The evaluator then proved a
zero-code-change remedy exists: computing the SAME screen for `screen_date=2026-07-25` inside a
throwaway copy of `.data/` measures AAPL at 1 day and NFLX/META/NVDA at 12 days — both thresholds
reachable today, with no write to the real data folder. This iteration is therefore
evidence-and-tidy-up only: reproduce that exact measurement inside a scoped rig, capture the
literal screenshot, disclose which data root served it, and land two one-line documentation
corrections the iter-9 audit flagged (finding T2's stale evidence citation, finding T3's
undocumented golden-script dependency).

**Target selection.** Per the priority rubric, J-08 is the only journey not already `passing`
(journey-history digest: 7 passing, 1 partial, 0 failing, 0 regressed) and it is not human-blocked
— iter-9's own evaluator scored it "CLOSEABLE BY THE CHAIN, no code change and no ambient write" —
so it is this iteration's sole, trivial target: the smallest possible spec, carrying zero risk (no
production code touched at all).

**Depth — lean, no full trigger holds.** This iteration changes no persisted schema, no
Data-Contract owner or endpoint, and no shared module — J-08's implementation is complete and a
binding "do not redo" item; the only changes are evidence artifacts and two documentation notes.
The prior verdict was `CONTINUE`, not `ESCALATE`; the consecutive-lean counter is 0/4 (hardening
cadence not met — iteration 9 itself dispatched `full`, which reset the counter). None of the four
full-depth triggers (structural/cross-cutting, data-model, prior ESCALATE, hardening cadence)
applies.

**Lessons applied** (from `lessons.md`): (i) *iter-9, first* — a goal-authored number measured live
at authoring time decays with wall-clock time; reproduce the goal's own cited measurement
conditions (`screen_date=2026-07-25` in a scoped copy) rather than granting a downstream allowance
— this iteration's TESTING REQUIREMENTS below use the literal `≤ 2 d` / `≥ 10 d` thresholds only,
with no softened variant anywhere. (ii) *iter-9, second* — the scoped-rig discipline must cover
EVERY lane including browser-QA, not only the dev lane, and the results report must name the data
root used. (iii) *iter-4/iter-5* — a golden replay or a UI click that reaches a compute/fetch/Run
button is a WRITE path; the desk-screen compute this iteration goes through the CLI/POST path
against a SCOPED copy only, never a UI click (the `/desk` Run Screen button always submits the
client's own `today` per the Product Shape's own build-time decision, so it cannot even target
`2026-07-25`) and never the ambient store.

## IN SCOPE

### Backend
- [ ] None — zero product/application code change. `desk_screen.py`, `desk_screen_compute.py`,
      `tradability.py`, `levels.py`, `bars.py`, `app/mcp/__init__.py`, `config.py`, `meta.py` all
      stay byte-unmodified.

### Frontend
- [ ] None — zero product/application code change. `apps/frontend/app/desk/page.tsx`,
      `lib/types.ts`, `StructureChart.tsx`, `PriceChart.tsx` all stay byte-unmodified.

### Evidence capture (ops/QA only — no source change)
- [ ] Seed ONE fresh throwaway root from the CURRENT `apps/backend/.data/` tree using the existing,
      reusable `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` (pass a new/distinct
      `root_dir` so the copy reflects today's ambient state, including every top-up and screen
      recorded since it was written) — never point any step this iteration at the ambient store.
- [ ] Inside that scoped root, compute one desk screen for `--date 2026-07-25` via the existing CLI
      (`python -m app.research.desk_screen_compute --date 2026-07-25`) or the equivalent
      `POST /research/desk/screen/compute` call against the scoped backend — never via the `/desk`
      UI's Run Screen button (it always submits the client's own `today`, so it cannot target this
      date). Contingency: if that compute reports `reused: true` against a snapshot that lacks
      basis fields (a pre-J-08 recording whose 5-pin key happens to coincide), pick the nearest
      NOT-yet-recorded `screen_date` that still yields a `≤ 2 d` row and a `≥ 10 d` row — re-derive
      the correct date live via `GET /research/tradability` on the SAME scoped copy first, the same
      check the evaluator already ran — rather than deviating from the append-only rail or accepting
      a non-literal spread.
- [ ] `rm -rf apps/frontend/.next` and rebuild before any browser capture (T-9).
- [ ] Browser-qa: load `/desk` against the scoped backend/frontend pair and capture one screenshot
      legibly showing a row's basis cell reading a day-count `≤ 2` together with a row's basis cell
      reading a day-count `≥ 10`, both inside that single image.
- [ ] Replay the smoke set (`journey-scripts/J-01.json` through `J-05.json`, `J-07.json` — all
      read-only, verified no mutating click in any of them) and `J-08.json` against the SAME scoped
      backend; record results.
- [ ] The evidence/results report states, in plain text, the absolute scoped-root path used for
      every capture and replay this iteration — no silent default to the real data folder (the
      iter-9 audit T3 deviation must not recur).

### Documentation tidy-ups (no behavior change)
- [ ] Append a non-destructive corrective note to `docs/handoffs/goal-desk-iter-9-dev.md` (do not
      delete or rewrite the original stale sentence — it is a historical record) naming where the
      real J-08 replay evidence actually lives
      (`reports/phase-goal-desk-iter-9-ui-test-results.llm.md`'s J-08 rows plus
      `reports/qa/goal-desk-iter-9-evidence/J-08-verify.png`) — the file the original sentence cited
      (`reports/phase-goal-desk-iter-9-regression-replay-results.md`) was overwritten by the
      iter-9 smoke-set replay and now carries no J-08 row (audit finding T2).
- [ ] Document, co-located with `runs/goal-session-desk/journey-scripts/J-08.json` (e.g. an
      additional non-functional field such as `"notes"` — confirmed tolerated by `demo_runner.py`'s
      script validator, which ignores unknown top-level keys), that steps 3 and 6 assume the replay
      target's LATEST recorded screen snapshot already carries `basis_as_of`/`basis_age_days`
      (i.e. was computed after the J-08 change landed) — audit finding T3's carried consequence.

### New user-facing capability
None — J-08's basis column, tooltip, and honest fallback already shipped in iteration 9 and are
already visible in production. This iteration only captures the specific evidence `docs/goal.md`'s
acceptance text still requires.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — this is a verification pass. The operator sees nothing new; the automation proves what
iteration 9 already built meets the literal acceptance text.

### Blueprint conformance
No new page, no nav-skeleton change. `/desk` remains the ALREADY-REGISTERED canonical home for J-08
(Feature/journey homes table, Desk nav section). `runs/goal-session-desk/state/blueprint.md` is
updated additively this iteration (before dispatch): the J-08 row's annotation is refreshed from
"IN BUILD at iter-9" to reflect that its implementation shipped iteration 9 and only evidence
capture remains, plus a "NOTED at iter-10" trailer paragraph recording that this iteration adds no
new Data-Contract row and no nav change. No `blueprint.reapproval-requested` file is written.

### Data-contract additions
None. `basis_as_of` and `basis_age_days` were already registered on the existing "Screen snapshots,
rank rows, skip rows" Data-Contract row at iteration 9's dispatch (`blueprint.md`'s "iter-9
addition" note). This iteration reads/serves that already-registered shape, introduces no new
value, and reuses the already-registered `desk_screen.py` owner / `GET /research/desk/screen`
endpoint verbatim.

## OUT OF SCOPE

- Any edit to `desk_screen.py`, `desk_screen_compute.py`, `tradability.py`, `levels.py`, `bars.py`,
  `desk/page.tsx`, `types.ts`, `StructureChart.tsx`, `PriceChart.tsx`, `config.py`, `meta.py`, or
  `app/mcp/__init__.py` — J-08's implementation is DONE and a binding "do not redo" item; zero diff
  is the expectation, not merely the default.
- Any new `Config` field, route, page, MCP tool, or nav-skeleton change.
- Computing a screen, or clicking "Run Screen"/"Top-up", against the ambient
  `apps/backend/.data/` store — the scoped copy is the only permitted target this iteration;
  repeating the iter-9 audit-T3 deviation is explicitly forbidden, not merely discouraged.
- Backfilling `basis_as_of`/`basis_age_days` onto the pre-existing legacy snapshots
  (`screen-2026-06-22-3ecd45c062c7`, `screen-2026-07-25-e184a7dc2f86`,
  `screen-2026-07-27-936543601e75`) — the append-only rail is absolute.
- Widening TC-8's guard-test coverage to the full `BarStore`/`bar_index` family, or adding a
  route-layer legacy-field-absence regression test (audit findings B2/B3) — genuine but
  non-blocking GAPs from iter-9's audit; leave for a future iteration if ever prioritized.
- The backlogged `bar-index-store-reconcile` proposal — not promoted by the goal-proposer this
  cycle; do not build it.
- Any test plan or lane granting itself an "allowance" to soften the literal `≤ 2 d` / `≥ 10 d`
  thresholds — forbidden outright this iteration (see Lessons applied above).
- Re-verifying J-01–J-07's own deep acceptance clauses beyond the smoke-set deterministic replay —
  "Do not redo" per `iteration-state.md`.
- Re-opening R-1, the same-date screen ambiguity, keyboard access for history rows, or the three
  older one-line hardening items — carried, unrelated to this journey.

## DEFINITION OF DONE

- [ ] Target journey J-08 passes via browser-qa-agent: one screenshot, captured against a scoped
      throwaway copy of `.data/` computed for `screen_date=2026-07-25`, legibly shows a row with
      `basis_age_days <= 2` and a row with `basis_age_days >= 10` together in the same image.
- [ ] Required-still-passing journeys remain green: J-01, J-02, J-03, J-04, J-05, J-07 via
      deterministic replay against the same scoped backend; J-06 re-confirmed via its existing MCP
      contract test suite (it has no browser surface).
- [ ] No anti-goal violation introduced: zero write to the ambient `apps/backend/.data/` store this
      iteration — its file listing and every file's checksum are identical before and after.
- [ ] Unit tests pass; no regressions — full backend suite reports at or above 1346 passed / 8
      skipped / 0 failed; `Config().config_fingerprint()` still prints `08e471b10130e1e2`; zero diff
      on every product source file.
- [ ] The evidence/results report states, in plain text, the absolute scoped-root path used for
      every capture this iteration.
- [ ] Both documentation tidy-ups land: a corrective, non-destructive note on the stale iter-9
      evidence citation; a documented note on `J-08.json` steps 3/6's latest-screen dependency.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-10-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-08 (the literal `≤2 d`/`≥10 d` screenshot, against the scoped `screen_date=2026-07-25`
  compute); smoke replay of J-01, J-02, J-03, J-04, J-05, J-07 (deterministic golden replay,
  read-only, against the same scoped backend). J-06 has no browser surface — re-confirmed via
  `test_mcp_server.py`, not a replay.
- Unit/integration: full backend suite re-run (`cd apps/backend && .venv/bin/python -m pytest
  tests/ -q`) to confirm the floor and pin hold; no new tests are expected since no product code
  changes.
- Error cases: none newly introduced — no new code path this iteration. Contingency only: if
  computing `screen_date=2026-07-25` inside the scoped copy returns `reused: true` against a
  snapshot lacking basis fields, the executor must re-derive the correct not-yet-recorded date live
  (via `GET /research/tradability` on the SAME scoped copy) rather than deviate from the
  append-only rail or accept a non-literal spread.

Test-first contract — TC- scenarios:

- TC-1: given a fresh throwaway copy of `apps/backend/.data/` seeded from the current ambient tree
  via the existing scoped-backend script pointed at a new root, when the desk screen is computed
  for `--date 2026-07-25` against that scoped copy (CLI or POST, never the ambient store, never the
  `/desk` UI button), then `GET /research/desk/screen?date=2026-07-25` on that scoped backend
  returns a snapshot whose ranked rows include at least one row with `basis_age_days <= 2` and at
  least one row with `basis_age_days >= 10`.
- TC-2: given that scoped snapshot from TC-1 and a clean rebuild (`rm -rf apps/frontend/.next` then
  rebuild) of the frontend pointed at the scoped backend, when `/desk` is loaded in a browser and
  its ranked rows render, then one screenshot legibly shows a `basis` cell reading a day-count
  `<= 2` and a `basis` cell reading a day-count `>= 10`, both inside that single image.
- TC-3: given TC-2's screenshot, when the accompanying evidence/results report is read, then it
  states the absolute filesystem path of the scoped throwaway data root used to serve that page
  load.
- TC-4: given the ambient `apps/backend/.data/screen/` directory's file listing and each file's
  SHA-256 checksum captured at the start of this iteration, when the same listing and checksums are
  captured again after all of this iteration's work completes, then both are byte-identical (zero
  new file, zero modified file, zero deleted file).
- TC-5: given `runs/goal-session-desk/journey-scripts/J-01.json` through `J-05.json` and
  `J-07.json`, when each is replayed deterministically against the scoped backend from TC-1, then
  every replay reports PASS with 0 failed steps.
- TC-6: given `test_mcp_server.py`'s existing tool-contract assertions, when the suite is run after
  this iteration, then `EXPECTED_TOOLS` still has exactly 17 entries including
  `desk_universe`/`desk_screen`, re-confirming J-06 without a browser pass.
- TC-7: given `docs/handoffs/goal-desk-iter-9-dev.md`'s existing citation of
  `reports/phase-goal-desk-iter-9-regression-replay-results.md` as J-08 replay proof (a file the
  iter-9 smoke-set replay subsequently overwrote, leaving no J-08 row), when a corrective note is
  appended to that handoff, then the note names the file that actually carries the J-08 replay
  evidence (`reports/phase-goal-desk-iter-9-ui-test-results.llm.md`'s J-08 rows plus
  `reports/qa/goal-desk-iter-9-evidence/J-08-verify.png`) without deleting or rewriting the
  original sentence.
- TC-8: given `runs/goal-session-desk/journey-scripts/J-08.json`'s steps 3 and 6 (both asserting
  text on the LATEST screen's basis cell), when a documentation note is added recording this
  dependency, then the note states plainly that both steps require the replay target's latest
  recorded screen snapshot to already carry `basis_as_of`/`basis_age_days`, so a replay against a
  store whose latest screen predates the J-08 change fails those two steps for an environmental
  reason, not a product regression.
- TC-9: given the full backend test suite, when it is run via `cd apps/backend &&
  .venv/bin/python -m pytest tests/ -q`, then it reports at least 1346 passed, 8 skipped, 0 failed,
  and a separate `python -c "from app.config import Config; print(Config().config_fingerprint())"`
  still prints `08e471b10130e1e2`.
- TC-10: given the cumulative repository diff produced by this iteration, when it is compared
  against this iteration's own start-of-run snapshot, then it touches only documentation/evidence
  artifacts (the corrective handoff note, the `J-08.json` dependency note, new QA/evidence reports
  and screenshots, this iteration's own dev handoff) and shows zero diff on
  `apps/backend/app/research/desk_screen.py`, `tradability.py`, `levels.py`, `bars.py`,
  `apps/frontend/app/desk/page.tsx`, `lib/types.ts`, `StructureChart.tsx`, `PriceChart.tsx`,
  `config.py`, `meta.py`, and `app/mcp/__init__.py`.
- TC-11: given this iteration's own TESTING REQUIREMENTS state the literal `<= 2 d` / `>= 10 d`
  thresholds, when the evidence/results report for J-08 is read, then it contains no self-granted
  "allowance", exception, or reinterpretation of those numbers — either the literal thresholds are
  met exactly as TC-1/TC-2 specify, or the iteration reports the gap honestly without softening the
  acceptance text.

## NOTES

- Carried, not blocking: four narrower-than-specified or spec-text-vs-shipped items from iter-9's
  audit (B2 — TC-8's guard test instruments only `compute_tradability` call counts, not the full
  `BarStore`/`bar_index` family named in the spec text; B3 — legacy-field-absence is pinned at the
  store layer only, not by a committed route-layer test; B4 — the identical-pins endpoint-reuse
  path is pre-existing/untouched, not newly tested; F1 — the basis column shipped as the 8th/last
  column rather than literally "beside distance", though no acceptance clause requires a specific
  position). None of these block J-08; none is this iteration's job.
- Carried, not forced: the same-date screen ambiguity (two screens recorded on one calendar day
  cannot be told apart by a date-only lookup), keyboard access for the history rows, and the three
  older one-line hardening items from earlier iterations.
- The backlogged `bar-index-store-reconcile` proposal (goal-proposer, not promoted this cycle)
  remains available for a future cycle once J-08 closes.
- If the desk-screen compute in this iteration's Evidence capture step needs a data root distinct
  from any root a prior iteration already seeded, say so explicitly in the results report — do not
  silently reuse a stale scoped root whose bar coverage may no longer match the ambient store's
  current state.
- If any lane edits `journey-scripts/J-08.json` (or any other golden) after this iteration's
  documentation note is added, say so explicitly in that lane's results report — the iter-8 lesson
  on undisclosed golden edits.
- Scoring J-08 `passing` or otherwise, and any consequence for the era's overall verdict, is the
  evaluator's call after real evidence lands — this spec does not presume an outcome.
