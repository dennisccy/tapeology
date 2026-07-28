# Goal Iteration 12 — J-09 evidence: the demo-narrator walkthrough shows both halves

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 12
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
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

  **Host protection (added 2026-07-28 — a physical constraint of the host, not product scope):**

  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are launched via `scripts/automation/host-guard-exec.sh claude`
    (the engine pauses `AWAITING_HOST_GUARD`, resumable, on an unconfined pump). Never disable,
    widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows
    the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Close J-09's one remaining acceptance clause — a `[NEW]`-flagged demo-narrator walkthrough that
covers the top-up-run disclosure "end to end" — by re-recording it against a freshly-seeded,
scoped throwaway copy of the data folder that actually holds saved runs, so the walkthrough shows
both the honest empty state AND a populated run with a failed pair's own words, in one artifact,
with zero change to any product code.

## BACKGROUND

Iteration 11 built and independently re-verified J-09 in full: the append-only per-run ledger
(`desk_topup_log.py`), `GET /research/desk/topup/runs`, the `/desk` "Top-up Runs" section, and
every behavioral clause docs/goal.md's acceptance text names — byte-identical persisted outcomes
proven by a live spy over the real `run_topup`, a cancelled run's honest unreached-pairs count, a
run interrupted before its terminal write leaving zero fabricated record, a second run appending
without touching the first file's checksum, the MCP surface still exactly 17 tools, the
copy-discipline lint green unmodified, the full suite green (1369 passed / 8 skipped / 0 failed),
the pin still `08e471b10130e1e2`, and `coherence.md` = COHERENCE-PASS. Only one clause is unmet:
docs/goal.md's own text requires "a `[NEW]`-flagged demo-narrator walkthrough covers the
top-up-run disclosure end to end," and the recorded walkthrough
(`reports/phase-goal-desk-iter-11-demo.json` step 2, `reports/demo/goal-desk-iter-11/step-02.png`)
narrates only the honest empty panel — it never shows a single saved run. That happened because
the demo lane recorded against the ambient `apps/backend/.data/` store, which genuinely has zero
top-up runs (`reports/phase-goal-desk-iter-11-closure-verdict.md`'s audit finding T3: rated
PASS_WITH_GAPS/non-blocking for the pipeline gate, but the evaluator scored the *journey* `partial`
because the walkthrough's own narration — "every top-up run is saved for good. Its result can
never be lost." — sits over a picture that shows nothing saved). The evaluator's iter-11 verdict
was `CONTINUE`, not `GOAL_ACHIEVED`, for exactly this reason, and its next-step recommendation
names the precise, zero-code-change fix this spec implements: rebuild the same fixture-scoped rig
this era's `goal-desk-iter9-scoped-backend.sh` already provides, record three checkpoint top-up
runs into it (one ordinary, one stopped early, one with an induced failed pair — the identical
recipe iter-11's own browser-QA lane already executed for UT-03 through UT-08), and re-record the
walkthrough against that populated rig so it captures both halves in sequence.

**Target selection.** Per the priority rubric: journey-history shows 8 passing (J-01–J-08), 1
partial (J-09), 0 failing, 0 regressed. J-09 is the only journey not `passing`, it is not
human-blocked (the evaluator's own words: "nobody has to decide anything first" — this is "a
picture the automation can take by itself with no program change"), and it is the smallest
possible spec (zero source lines, one re-recorded artifact). It is this iteration's sole target.

**Depth — lean, no full trigger holds.** (1) Structural/cross-cutting — no, this iteration touches
zero application modules. (2) Data model — no, nothing new is persisted, no Data-Contract owner or
endpoint changes; the already-registered `desk_topup_log.py` / `GET /research/desk/topup/runs` row
is read verbatim. (3) Prior verdict was `CONTINUE`, not `ESCALATE`. (4) Hardening cadence —
"Consecutive lean iterations dispatched: 0" (iteration 11 dispatched `full`, which reset the
counter), cadence 4 not met. This matches the evaluator's own explicit
"**Depth Recommendation For Next Iteration:** lean" and its own words: "It is a picture-taking run
only — do not change any program code."

**Lessons applied** (from `lessons.md`): (i) *iter-11, third* — a feature whose whole point is
state that accumulates cannot be demonstrated on a store deliberately kept empty; name the scoped
rig (and the records it must already hold) in the SHOWCASE/demo dispatch itself, not only the dev
and browser-QA ones — this iteration's IN SCOPE below states the scoped root explicitly as a
showcase-lane requirement, not merely a dev-lane one. (ii) *iter-9, second* — the scoped-rig
discipline must cover EVERY lane; the results report (and the demo report) must each state which
data root produced the evidence. (iii) *iter-10* — an evidence-only compute can silently collide
with an existing record under the same key inside a store a golden script replays against; check
the scoped rig for a pre-existing top-up-run record before assuming a fresh recording is
collision-free, and disclose any collision found. (iv) *iter-4/iter-5* — a golden replay script or
a UI click that reaches a compute/fetch/Run button is a WRITE path; every replay and every
recording this iteration targets the scoped copy only, never the ambient store, and any script
whose own steps reach a mutating control gets a post-match liveness assertion. (v) *iter-8* — any
lane that edits a golden (`journey-scripts/J-09.json` or any other) after this iteration's baseline
must say so explicitly in its own results report.

## IN SCOPE

### Backend
- [ ] None — zero product/application code change. `desk_topup_log.py`, `desk_topup_compute.py`,
      `desk_routes.py`, `desk_screen.py`, `desk_coverage.py`, `tradability.py`, `levels.py`,
      `bars.py`, `app/mcp/__init__.py`, `config.py`, `meta.py` all stay byte-unmodified.

### Frontend
- [ ] None — zero product/application code change. `apps/frontend/app/desk/page.tsx`,
      `lib/types.ts`, `lib/api.ts`, `StructureChart.tsx`, `PriceChart.tsx` all stay
      byte-unmodified.

### Evidence capture (ops/showcase only — no source change)
- [ ] Seed ONE fresh throwaway root from the CURRENT `apps/backend/.data/` tree using the existing,
      reusable `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` (pass a new/distinct
      `root_dir`) — never point any step this iteration at the ambient store. Capture that root's
      "before" state (its `topup_runs`-equivalent directory is absent or empty) so the walkthrough's
      first capture is a genuine, unforced honest-empty state, not one manufactured by deleting
      existing records.
- [ ] Before recording anything into the scoped rig, check it for any pre-existing top-up-run
      record under the same identifying key a new run might collide with (the iter-10 lesson); if a
      collision is unavoidable, disclose it explicitly in this iteration's results/demo reports
      rather than silently proceeding.
- [ ] Against that scoped backend, record three checkpoint top-up runs — the same recipe iter-11's
      own browser-QA lane already used (`reports/phase-goal-desk-iter-11-ui-test-results.llm.md`
      "Test rigs used"): one ordinary run (`state: done`, `pairs_attempted == pairs_total`), one run
      cancelled mid-walk (`state: cancelled`, `pairs_attempted < pairs_total`), and one run
      containing at least one induced `failed` pair with its vendor detail preserved verbatim
      (e.g. an `AAPL 4h — no data for that window`-style message) via a monkeypatched adapter or the
      existing `_NthCallFailsAdapter`-style double `test_desk_topup_compute.py` already uses — never
      a live vendor call (the suite's keyless/hermetic rail).
- [ ] `rm -rf apps/frontend/.next` and rebuild before any browser/demo capture (T-9).
- [ ] Re-record the `[NEW]`-flagged demo-narrator walkthrough for J-09 against that populated scoped
      rig so it captures BOTH halves in one artifact, in sequence: (a) the honest "No top-up runs
      recorded yet." panel on the freshly-seeded, still-empty rig, and (b) after the three
      checkpoint runs, the populated Top-up Runs section showing the latest run's
      attempted-of-total count, its per-outcome (reused/fetched/failed) counts, and the failed
      pair's own recorded detail, all legible. Name the scoped rig's absolute path explicitly in
      the demo/showcase dispatch itself, not only the dev/QA one (the iter-11 lesson). Any other,
      already-`verified` step the walkthrough re-captures along the way must still narrate content
      that is actually true of whichever rig serves it — this iteration's job is closing J-09's own
      gap, not revising the rest of the tour's narration.
- [ ] Capture standalone browser-qa-agent screenshots for the same two states (empty, then
      populated-with-a-failed-pair) on the same scoped rig, so J-09's evidence includes both the
      narrated walkthrough artifact and independent screenshots.
- [ ] Replay the full regression set (`journey-scripts/J-01.json` through `J-08.json`) against the
      same scoped backend; any script whose own steps reach a compute/fetch/Run control runs that
      step against the SAME scoped backend, never the ambient store, per the iter-4/iter-5 lessons.
      Record results.
- [ ] The evidence/results report AND the demo/showcase report each state, in plain text, the
      absolute scoped-root path used for every capture and replay this iteration — no silent
      default to the real data folder (the iter-9 audit T3 deviation, and the iter-11 demo-lane
      deviation, must not recur).
- [ ] After all capture completes, diff the ambient `apps/backend/.data/` tree's file listing and
      per-file checksums against this iteration's own start-of-run snapshot to prove zero write
      landed there.
- [ ] If `journey-scripts/J-09.json` (or any other golden) is edited by any lane this iteration, say
      so explicitly in that lane's own results report (the iter-8 lesson).

### New user-facing capability
None — J-09's Top-up Runs section, store, and endpoint already shipped in iteration 11 and are
already visible in production. This iteration only captures the narrated-walkthrough evidence
docs/goal.md's acceptance text still requires.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — this is a verification/showcase pass. The operator sees nothing new; the automation proves
the already-shipped Top-up Runs disclosure narrates end to end, not only its empty half.

### Blueprint conformance
No new page, no nav-skeleton change. `/desk` remains the ALREADY-REGISTERED canonical home for
J-09 (Feature/journey homes table, Desk nav section). `runs/goal-session-desk/state/blueprint.md`
has been updated additively (before this dispatch): the J-09 Feature/journey-homes row's annotation
now reads "implementation shipped iter-11; iter-12 closes the remaining narrated-walkthrough
evidence" (mirroring the J-08 row's own iter-9/iter-10 pattern), plus a "NOTED at iter-12" trailer
paragraph recording that this iteration adds no new Data-Contract row and no nav change. No
`blueprint.reapproval-requested` file was written — nothing about the nav skeleton changed.

### Data-contract additions
None. "Top-up run records (per-run outcome ledger)" was already registered on
`app/research/desk_topup_log.py` / `GET /research/desk/topup/runs` at iteration 11's dispatch
(`blueprint.md`'s "NEW at iter-11" row). This iteration reads/serves that already-registered shape,
introduces no new value, and reuses the already-registered owner/endpoint verbatim.

## OUT OF SCOPE

- Any edit to `desk_topup_log.py`, `desk_topup_compute.py`, `desk_routes.py`, `desk_screen.py`,
  `desk_coverage.py`, `tradability.py`, `levels.py`, `bars.py`, `desk/page.tsx`, `lib/types.ts`,
  `lib/api.ts`, `StructureChart.tsx`, `PriceChart.tsx`, `config.py`, `meta.py`, or
  `app/mcp/__init__.py` — J-09's implementation is DONE and a binding "do not redo" item; zero diff
  is the expectation, not merely the default.
- Any new `Config` field, route, page, MCP tool, or nav-skeleton change.
- Triggering a top-up, screen, or fetch against the ambient `apps/backend/.data/` store — the
  scoped copy is the only permitted target this iteration; repeating the iter-9/iter-11 audit
  deviations is explicitly forbidden, not merely discouraged.
- A real ~100-symbol operator top-up run — this iteration proves the walkthrough on a
  fixture-scoped rig only; the real run stays a separate, explicit, honestly-reported operator act.
- Backfilling, rewriting, or recomputing any already-recorded universe, screen, or top-up-run
  record — the append-only rail is absolute.
- Re-verifying J-01–J-08's own deep acceptance clauses beyond the smoke-set deterministic replay —
  "Do not redo" per `iteration-state.md`.
- The backlogged `bar-index-store-reconcile` proposal — not promoted by the goal-proposer this
  cycle; do not build it.
- The carried, non-blocking hardening items: the run list dropping `integrity_errors`
  (`desk_routes.py:258`), the narrow auto-refresh race (`app/desk/page.tsx:1116-1121`), the missing
  run-table cap, the six-stacked-sections page length, the same-date-screen ambiguity, and keyboard
  access for the history rows — all unrelated to this journey, none of this iteration's job.

## DEFINITION OF DONE

- [ ] Target journey J-09 passes with a re-recorded `[NEW]`-flagged demo-narrator walkthrough that
      shows, in one artifact and in sequence, (a) the honest empty "No top-up runs recorded yet."
      state and (b) a populated Top-up Runs section (attempted-of-total, per-outcome counts, a
      failed pair's own detail legible) — both captured against the SAME scoped throwaway rig.
- [ ] Standalone browser-qa-agent screenshots exist for both states, on the same scoped rig.
- [ ] Required-still-passing journeys J-01–J-08 remain green: J-01–J-05, J-07, J-08 via
      deterministic replay against the same scoped backend; J-06 re-confirmed via its existing MCP
      contract test (`test_mcp_server.py`) — it has no browser surface.
- [ ] No anti-goal violation introduced: zero write to the ambient `apps/backend/.data/` store this
      iteration — its file listing and every file's checksum are identical before and after.
- [ ] Unit tests pass; no regressions — full backend suite reports at or above 1369 passed / 8
      skipped / 0 failed; `Config().config_fingerprint()` still prints `08e471b10130e1e2`; zero diff
      on every product source file.
- [ ] The evidence/results report AND the demo/showcase report each state, in plain text, the
      absolute scoped-root path used for every capture this iteration.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-12-dev.md`.

## TESTING REQUIREMENTS

- Browser: smoke replay of J-01 through J-08 (deterministic golden replay against the same scoped
  backend; any step reaching a compute/fetch/Run control stays scoped, never ambient). J-09 is
  verified via the re-recorded demo-narrator walkthrough plus the standalone supporting screenshots
  — no new golden script is required by this spec (an executor may choose to refresh
  `journey-scripts/J-09.json` too, disclosing it per the iter-8 lesson if so).
- Unit/integration: full backend suite re-run (`cd apps/backend && .venv/bin/python -m pytest
  tests/ -q`) to confirm the floor and pin hold; no new tests are expected since no product code
  changes.
- Error cases: none newly introduced — no new code path this iteration. The one already-required
  error case (a failed pair's detail preserved verbatim while the walk continues) is exercised
  again while recording the three checkpoint runs, not newly tested.

Test-first contract — TC- scenarios:

- TC-1: given a fresh throwaway copy of `apps/backend/.data/` seeded from the current ambient tree
  via the existing scoped-backend script pointed at a new root, when `GET
  /research/desk/topup/runs` is called against that scoped backend before any run, then the
  response is HTTP 200 `{"runs": [], "latest": null}`, and a screenshot of `/desk` on that same
  scoped backend legibly shows "No top-up runs recorded yet." with zero run rows.
- TC-2: given that same scoped rig, when three checkpoint top-up runs are recorded into it (one
  ordinary with `pairs_attempted == pairs_total`, one cancelled with `pairs_attempted <
  pairs_total`, one containing at least one induced `failed` pair), then `GET
  /research/desk/topup/runs` on that backend returns a `runs` list with 3 entries and a `latest`
  record whose `outcomes` include an entry with `outcome: "failed"` and a non-null `detail`.
- TC-3: given TC-2's populated rig and a clean rebuild (`rm -rf apps/frontend/.next` then rebuild)
  of the frontend pointed at it, when `/desk` is loaded and the Top-up Runs section renders, then
  one screenshot legibly shows the latest run's attempted-of-total pair count, its per-outcome
  (reused/fetched/failed) counts, and the failed pair's own recorded detail text, all in the same
  image.
- TC-4: given TC-1's empty-state capture and TC-3's populated-state capture, when the `[NEW]`-
  flagged demo-narrator walkthrough for J-09 is assembled, then it contains both captures in
  sequence (empty state first, populated state second) inside one walkthrough artifact, each step
  legible, and each step's narration matches what its own paired screenshot actually shows (no
  claim unsupported by the image next to it).
- TC-5: given the demo/showcase report and the browser-QA results report produced this iteration,
  when each is read, then both state the absolute filesystem path of the scoped throwaway data
  root used to serve every capture.
- TC-6: given the ambient `apps/backend/.data/` tree's full file listing and each file's SHA-256
  checksum captured at the start of this iteration, when the same listing and checksums are
  captured again after all of this iteration's work completes, then both are byte-identical (zero
  new file, zero modified file, zero deleted file) — including no new `topup_runs`-equivalent
  directory anywhere in the ambient tree.
- TC-7: given `runs/goal-session-desk/journey-scripts/J-01.json` through `J-05.json` and
  `J-08.json` (plus `J-07.json`), when each is replayed deterministically against the scoped
  backend from TC-1/TC-2, then every replay reports PASS with 0 failed steps.
- TC-8: given `test_mcp_server.py`'s existing tool-contract assertions, when the suite is run after
  this iteration, then `EXPECTED_TOOLS` still has exactly 17 entries, re-confirming J-06 without a
  browser pass.
- TC-9: given the full backend test suite, when it is run via `cd apps/backend &&
  .venv/bin/python -m pytest tests/ -q`, then it reports at least 1369 passed, 8 skipped, 0 failed,
  and a separate `python -c "from app.config import Config; print(Config().config_fingerprint())"`
  still prints `08e471b10130e1e2`.
- TC-10: given the cumulative repository diff produced by this iteration, when it is compared
  against this iteration's own start-of-run snapshot, then it touches only documentation/evidence/
  showcase artifacts (this iteration's dev handoff, QA/evidence reports and screenshots, the
  re-recorded demo walkthrough artifact) and shows zero diff on `desk_topup_log.py`,
  `desk_topup_compute.py`, `desk_routes.py`, `desk_screen.py`, `desk_coverage.py`, `tradability.py`,
  `levels.py`, `bars.py`, `apps/frontend/app/desk/page.tsx`, `lib/types.ts`, `lib/api.ts`,
  `StructureChart.tsx`, `PriceChart.tsx`, `config.py`, `meta.py`, and `app/mcp/__init__.py`.
- TC-11: given the scoped rig's own state before this iteration's three checkpoint runs are
  recorded, when the store is checked for any existing top-up-run record under the same
  identifying key, then either no collision exists, or, if one is found, the results report
  discloses it explicitly (the iter-10 lesson) rather than silently proceeding.

## NOTES

- Scoring J-09 `passing` or otherwise, and any consequence for the era's overall verdict, is the
  evaluator's call after real evidence lands — this spec does not presume an outcome. If every
  clause holds, this returns the era to 9/9 journeys `passing`; the evaluator, not this spec,
  decides whether that means `GOAL_ACHIEVED`.
- Carried, not forced (all optional, none blocking, unrelated to this journey): the run list does
  not yet report a damaged file the way the two sibling lists do (`desk_routes.py:258`); a
  just-finished run can stay hidden until a manual refresh in a narrow timing window
  (`apps/frontend/app/desk/page.tsx:1116-1121`); the run table has no limit yet; the Desk page is
  six stacked sections and long; two screens recorded for the same calendar day cannot be told
  apart by a date-only lookup; keyboard access for the history rows.
- If the three checkpoint top-up runs need a scoped root distinct from any prior iteration's
  already-seeded one, say so explicitly in the results report — do not silently reuse a stale root
  whose bar/universe coverage may no longer match the current ambient store's state (the iter-10
  lesson, restated).
- `runs/goal-desk-iter-11/status.json` reportedly still says browser checks did not run when they
  did (per iter-11's own next-step recommendation) — a bookkeeping artifact from iteration 11, not
  this iteration's job to fix; leave it unless it blocks this iteration's own tooling.
- Whether to extend `reports/phase-goal-desk-iter-11-demo.json`'s existing J-09 step in place, add a
  second J-09 step immediately after it, or author a fresh iter-12 demo script that reuses the same
  highlight steps against the scoped rig, is a build-time choice — any of the three satisfies TC-4
  as long as the resulting artifact carries both halves in one coherent walkthrough.
