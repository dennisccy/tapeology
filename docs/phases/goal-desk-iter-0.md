# Goal Iteration 0 — Baseline verification of Era B "The Desk" journeys (J-01–J-07)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Required-still-passing journeys:** None yet — baseline establishes the passing/failing set for
  every journey. J-07 (kept-product regression sentinel) captures the floor every later iteration
  must protect: `config_fingerprint` `08e471b10130e1e2` (confirmed live against the current tree),
  the two KEPT surfaces `/` and `/structure` as shipped, and the full backend suite green. Note
  that J-07's own acceptance text also asserts "nav = exactly three routes" and "MCP = exactly 17
  tools" — those clauses cannot be satisfied until J-04 and J-06 ship, so this iteration can only
  supply the KEPT-behavior half of J-07's evidence (see BACKGROUND).
- **Anti-goal reminders** (verbatim from `docs/goal.md` — Immutable rails, then desk-era
  anti-goals):

  *Immutable rails — the identity of the project (from `docs/research-directions.md` §0.3;
  enforced by existing tests and audits; only ever grow more specific, never weaker):*
  1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
     trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
     tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
     fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
     imperative trading cues. *(critical)*
  3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
     states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
     surface's behaviour stay byte-identical. New work is additive and versioned beside them,
     never a mutation of them. (The 5D demolition's removals are final history; this era builds
     `/desk` BESIDE the kept two pages — the one sanctioned kept-surface edit is J-05's additive
     `/structure` prefill.) *(critical)*
  4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
     through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins
     are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
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
  10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is
      an explicit, logged act. *(critical)*

  *Desk-era anti-goals (added, not weakening any rail above):*
  - **Membership is never a signal.** Universe membership (and any constituents metadata) selects
    WHAT to screen; it never enters a computation, rank formula beyond selection, feature, or
    report as an input value. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated,
    checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of,
    fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in
    place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or
    market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no
    advice, imperative, prediction, or ranking language implying action ("buy", "watch this",
    "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk
    surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a
    future era). *(critical)*
  - **The demolition stays demolished.** No journal-era machinery returns; the desk ledger records
    machine output only — zero manual-input write paths on desk records this era
    (dispositions/annotations are Era C's design space). *(critical)*
  - **The ledger never holds orders.** No sizes, tickets, entries/exits, or account concepts in
    any desk record — rail 1 in desk terms. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test
    fetches the network; live fetch/top-up/screen runs are operator-run verifications reported
    honestly (run-or-not-run), never CI gates. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion +
    stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is
    asserted unchanged by the sentinel every iteration. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
    inside the `AUTO:journeys` marker block in `docs/goal.md` — it MUST NOT edit human-authored
    journeys, the Anti-goals section, or any other part of that file; proposed journeys MUST carry
    a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and
    `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value
    journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Establish, with zero code changes, exactly which of J-01–J-07 (Era B "The Desk" journeys) already
pass, fail, or partially pass against the current codebase — so iteration 1 plans only the
remaining work.

## BACKGROUND

This is iteration 0 (`Mode: baseline`) — a verify-only assessment, not feature delivery, per the
goal-decomposer's baseline-mode rules. Depth is `lean` because the developer step is a no-op for
code; all the value comes from the browser-QA step exercising every journey and a static probe of
the current tree. Direct inspection of the current branch (`main` @ `047c38e`, the commit that
opened this era's `docs/goal.md`) confirms the desk has **not started**: no `apps/frontend/app/desk/`
directory exists (the frontend `app/` tree has only `page.tsx` (Cockpit), `structure/`, `layout.tsx`,
`globals.css`); a repo-wide case-insensitive grep for `desk` under `apps/backend/app` and
`apps/frontend/app` returns zero matches (no `desk_universe.py`, `desk_screen.py`, no
`/research/desk/*` route, no desk `Config` field); `app/meta.py`'s `UI_ROUTES` tuple lists exactly
2 entries (Cockpit, Structure — confirmed by direct read); `apps/backend/tests/test_mcp_server.py`'s
`EXPECTED_TOOLS` tuple has exactly 15 entries with no `desk_universe`/`desk_screen`; no
`.data/universe/` directory or universe fixture exists under `apps/backend/tests/fixtures/`; and
`apps/frontend/app/structure/page.tsx` has no `useSearchParams`/query-param prefill logic for its
Load form. One live check confirms no drift on the invariant every journey depends on:
`python -c "from app.config import Config; print(Config().config_fingerprint())"` (run from
`apps/backend`) prints `08e471b10130e1e2`, matching `docs/goal.md`'s stated pin exactly — the same
value `reports/goal-lint.md` recorded when the goal was authored (lint result: CLEAN). So
**J-01 through J-06 are expected to be recorded FAILING** this iteration — this is the honest,
expected baseline for a not-yet-started era, not a defect. **J-07's kept-product behaviors**
(sim cockpit incl. both charts, `/structure` Load for the pinned AAPL `2026-06-22` as-of date, Case
Studies, the Edge Report's honest state, the full suite under the current pin) are expected to
already hold, since Cockpit + Structure were built and verified GOAL_ACHIEVED across eras 1–5C,
`yahoo_fetch`, `tradable_wall`, `fast_wall`, and `clean_slate`, and this baseline performs no action
that could regress them — but J-07's own acceptance text in `docs/goal.md` also requires "nav =
exactly three routes" and "MCP = exactly 17 tools," which are desk-completion clauses that cannot
be satisfied until J-04/J-06 ship. The evaluator, not this spec, decides whether to record J-07 as
passing-on-today's-kept-evidence or partial-pending-the-later-journeys; this iteration only
supplies the evidence (see TESTING REQUIREMENTS and NOTES). Per the natural dependency order stated
in `docs/goal.md` ("J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding continuously"),
iteration 1 should target **J-01 alone** next — it is both first in dependency order and the
unblocker for every other desk journey (nothing else can exist until a registered universe does).
This session's own `lessons.md` and assumption ledger are both empty (first iteration of a new
session, nothing to apply yet). One cross-session lesson is directly relevant to executing THIS
iteration's browser checks: Chrome MCP's `use_browser` has previously failed to attach on port 9222
mid-session in this project; if that recurs, the browser-qa-agent should self-launch an isolated
`--headless=new --remote-debugging-port=9222 --no-sandbox --user-data-dir=<fresh>` Chrome and attach
to it, keeping it alive across the dispatch. A second lesson: browser verification must follow a
clean rebuild (`rm -rf apps/frontend/.next`) before any screenshot is trusted, per this era's own
T-9 trap — a stale build can bake a wrong API base or ghost pages into false results in either
direction.

## IN SCOPE

### Backend
None — this is a verify-only baseline iteration; no source files are modified.

### Frontend
None — this is a verify-only baseline iteration; no source files are modified.

### Verification scope (read-only — what gets checked, not changed)
- [ ] J-01: confirm the universe vendor seam, parser, store, fixture, and
      `GET/POST /research/desk/universe*` routes do not exist yet (expected: no — confirmed absent
      by grep at decompose time).
- [ ] J-02: confirm the coverage read and the operator-run top-up (POST + CLI) do not exist yet
      (expected: no).
- [ ] J-03: confirm the screen compute (POST + CLI), the append-only screen-snapshot store, and
      `GET /research/desk/screen` do not exist yet (expected: no).
- [ ] J-04: confirm `/desk` does not render as a page (404 or absent nav entry) and `UI_ROUTES`
      still lists only 2 rows (expected: no page, 2 nav entries).
- [ ] J-05: confirm `/structure` has no `?symbol=&asof=` prefill and no screen-history UI exists
      anywhere (expected: no).
- [ ] J-06: confirm the MCP tool list is still exactly the 15-tool contract (no `desk_universe`,
      no `desk_screen`) (expected: yes — still 15).
- [ ] J-07: confirm each kept-product behavior still renders/passes unchanged (sim cockpit incl.
      both charts, `/structure` Load for the pinned AAPL `2026-06-22` as-of date, Case Studies,
      Edge Report honest state, full backend suite, `config_fingerprint` `08e471b10130e1e2`)
      (expected: yes for the kept behaviors; the desk-completion clauses of J-07's acceptance —
      3-route nav, 17-tool MCP — are not yet satisfiable and should be noted as such, not scored
      as a failure of the KEPT product).

### New user-facing capability
None — verify-only; the product is byte-for-byte what it was before this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None this iteration. (The eventual target delta — a third `/desk` nav entry, a briefing page, two
new MCP tools — is documented in `docs/goal.md` and in `blueprint.md`'s Information Architecture,
but is NOT executed here.)

### Blueprint conformance
No new surfaces. `blueprint.md` was freshly drafted this iteration at
`runs/goal-session-desk/state/blueprint.md`, directly from `docs/goal.md`'s `## Product Shape`
section; this baseline run only checks the CURRENT app (nav = Cockpit + Structure, confirmed live)
against that future-state contract — it does not build toward it yet.

### Data-contract additions
None. No new displayed value is introduced this iteration. The five desk-owned rows the era will
eventually add (universe snapshots/membership, coverage, screen snapshots/rank/skip rows, compute
progress, the 3-row route list) are registered in `blueprint.md`'s Data Contract as the FUTURE
target, each with its proposed single owner — none of them are computed or served today.

## OUT OF SCOPE

- Any code change (the universe vendor seam/parser/store, coverage read, top-up, screen compute,
  the `/desk` page, the `/structure` prefill, the two new MCP tools, any desk `Config` field) —
  begins with whichever iteration targets J-01 next, per the natural dependency order.
- Fixing or explaining away any journey found FAILING — recording the honest state is this
  iteration's entire job; planning the fix is iteration 1's job.
- Editing `docs/goal.md` itself (only the goal-proposer may append inside the `AUTO:journeys`
  marker, and only once journeys exist to react to — not relevant at iteration 0).
- Performing the LIVE Wikipedia/constituents fetch, a real ~100-symbol top-up, or a real screen
  run — those are operator-run acts that only become exercisable once J-01/J-02/J-03 exist; this
  iteration verifies only the keyless/fixture-scoped and kept-product paths.
- Running the full 10h+ real-corpus edge-report sweep or any mutating recompute — read-only
  probes and the existing suite only.

## DEFINITION OF DONE

- [ ] J-01 verified against current codebase; result (failing, expected) recorded with grep/route
      evidence
- [ ] J-02 verified against current codebase; result (failing, expected) recorded with grep/route
      evidence
- [ ] J-03 verified against current codebase; result (failing, expected) recorded with grep/route
      evidence
- [ ] J-04 verified against current codebase via a real browser; result (failing, expected)
      recorded with a screenshot of `/desk`'s absence and the current 2-entry nav
- [ ] J-05 verified against current codebase via a real browser; result (failing, expected)
      recorded with a screenshot of `/structure?symbol=AAPL&asof=2026-06-22` rendering with an
      EMPTY Load form (no prefill, no auto-Load)
- [ ] J-06 verified against current codebase; result (failing, expected) recorded citing the
      15-entry `EXPECTED_TOOLS`/`TOOL_NAMES` tuple
- [ ] J-07 verified against current codebase via a real browser plus the full backend suite;
      result recorded with screenshots, distinguishing the KEPT-behavior evidence (expected
      passing) from the desk-completion clauses (not yet satisfiable — 2 nav routes / 15 MCP
      tools today, not 3/17)
- [ ] No anti-goal violation introduced (trivially satisfiable this iteration — verify by diff
      scope)
- [ ] `blueprint.md` is drafted at `runs/goal-session-desk/state/blueprint.md` and reflects
      `docs/goal.md`'s Product Shape (3-route target nav with Desk marked not-yet-built, the
      unchanged-owner rows carried forward, the five new desk-owned Data Contract rows each with
      exactly one proposed owner + endpoint)
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-0-dev.md`, explicitly stating no source
      files were changed

## TESTING REQUIREMENTS

- Browser: J-04 (confirm `/desk` renders the app's honest 404/absent-route behavior; confirm the
  top nav shows exactly Cockpit + Structure), J-05 (confirm `/structure?symbol=AAPL&asof=...`
  renders with the Load form unprefilled), J-07 (kept-product walkthrough: `SIM-BUYER` cockpit
  scenario settling `buyer_control` with the `PriceChart` rendering candles + timeframe switch +
  S/R band overlay + a live tape bar; `/structure` Load for the pinned AAPL `2026-06-22` as-of
  date rendering the 300–302.4 wall band on `StructureChart`; a Case Study drill-in; the Edge
  Report section showing warm cells or the honest "Edge report not computed yet." panel) — every
  step needs a screenshot; no screenshot means `unknown`, never `passing` (T-10).
- Unit/integration: run the full backend suite (`cd apps/backend && .venv/bin/python -m pytest
  tests/ -v`) and record the pass/skip counts as the desk-era baseline (`docs/goal.md` cites 1169
  pass / 7 skip at era open — reconfirm live, do not assume the cited number still holds);
  reconfirm `Config().config_fingerprint() == "08e471b10130e1e2"`; reconfirm
  `EXPECTED_TOOLS`/`TOOL_NAMES` in `test_mcp_server.py` both still list exactly the 15 pre-desk
  tool names. No new tests are written this iteration.
- Error cases: N/A this iteration — no new code path exists yet. The CURRENT absence of every
  `/research/desk/*` route (each returns HTTP 404, unregistered) is itself the baseline evidence
  for J-01/J-02/J-03; it becomes a populated-vs-honest-empty-state assertion once those routes
  ship.

Test-first contract:

- TC-1: given the backend running on committed fixtures at the current branch tip, when `GET` is
  issued to `/research/desk/universe`, then the request returns HTTP 404 (route not registered) —
  recorded as J-01 = failing; supporting evidence: a grep for `desk` under
  `apps/backend/app/research/` and `apps/backend/tests/fixtures/` returns no matches (no
  `desk_universe.py`, no universe fixture).
- TC-2: given the current backend source tree, when `apps/backend/app/config.py` is grepped for
  `desk_universe_source_url`, `desk_universe_min_members`, and `desk_universe_max_members`, then
  none are found — recorded as supporting evidence that J-01's Path-A Config fields do not exist
  yet.
- TC-3: given the backend running, when `GET` is issued to `/research/desk/coverage` (or any
  desk-scoped coverage path) and to a top-up POST route, then both return HTTP 404 — recorded as
  J-02 = failing.
- TC-4: given the backend running, when `GET` is issued to `/research/desk/screen`, then the
  request returns HTTP 404 — recorded as J-03 = failing; supporting evidence: no
  `desk_screen.py` module exists under `apps/backend/app/research/`.
- TC-5: given a real browser at the frontend's base URL, when the operator navigates to `/desk`,
  then the app renders its honest not-found behavior (no briefing table, no Run Screen button, no
  provenance line) — screenshot captured; AND `GET /meta/ui-routes` returns exactly 2 route
  objects (`/` and `/structure`) — recorded as J-04 = failing.
- TC-6: given `apps/frontend/app/structure/page.tsx`, when the file is inspected for
  `useSearchParams`/query-param prefill logic, then none is found; AND when a real browser
  navigates to `/structure?symbol=AAPL&asof=2026-06-22`, then the Load form renders EMPTY (no
  prefill, no auto-Load triggered) — screenshot captured — recorded as J-05 = failing.
- TC-7: given `apps/backend/tests/test_mcp_server.py`, when its `EXPECTED_TOOLS` tuple is
  inspected, then it contains exactly 15 entries and neither `desk_universe` nor `desk_screen`
  appears — recorded as J-06 = failing.
- TC-8: given a real browser at the running frontend, when the operator drives a `SIM-BUYER`
  cockpit scenario to settle `buyer_control`, then the sim settles into `buyer_control` AND the
  cockpit `PriceChart` renders candles, allows a timeframe switch, overlays an S/R band, and shows
  a live tape bar moving — screenshot captured; when the operator loads `/structure` for the
  pinned AAPL `2026-06-22` as-of date, then the 300–302.4 wall band renders on `StructureChart`, a
  Case Study drill-in opens, and the Edge Report section shows either warm cells or the honest
  "Edge report not computed yet." panel — screenshot captured for each — recorded as J-07's
  KEPT-behavior evidence.
- TC-9: given the committed test fixtures, when the full backend test suite is run, then it
  reports 0 failures, and its pass/skip counts plus a live
  `Config().config_fingerprint()` print of `08e471b10130e1e2` are recorded — recorded as J-07's
  suite-and-pin evidence.
- TC-10: given this iteration's git diff against its parent commit, when the changed-file list is
  inspected (`git diff --stat apps/`), then its output is empty — zero files under
  `apps/backend/app/` or `apps/frontend/` are touched — confirming no anti-goal violation is
  possible this iteration.
- TC-11: given the iteration completes, when `runs/goal-session-desk/state/blueprint.md` is read,
  then its Information Architecture lists a three-entry TARGET nav skeleton (Cockpit, Structure,
  Desk — Desk marked not-yet-built) and its Data Contract table includes the five new desk-owned
  rows (universe snapshots/membership, coverage, screen snapshots/rank/skip rows, compute
  progress, the 3-row route list), each with exactly one named owner module and one serving
  endpoint.
- TC-12: given the iteration completes, when `docs/handoffs/goal-desk-iter-0-dev.md` is read, then
  it exists and explicitly states that no source files were modified this iteration.

## NOTES

- **Codebase probe evidence (iter-0 decompose time).** `apps/frontend/app/` contains only
  `page.tsx`, `structure/`, `layout.tsx`, `globals.css` (no `desk/`). A case-insensitive grep for
  `desk` under `apps/backend/app` and `apps/frontend/app`/`apps/frontend/components` returns zero
  matches. `apps/backend/app/meta.py`'s `UI_ROUTES` tuple: `({"path": "/", "label": "Cockpit",
  "nav": True}, {"path": "/structure", "label": "Structure", "nav": True})` — exactly 2 entries.
  `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple has exactly 15 entries ending in
  `get_endpoint`, none named `desk_universe`/`desk_screen`. `apps/backend/app/research/` has no
  `desk_universe.py`/`desk_screen.py` (confirmed module listing). `apps/backend/.data/` has
  `bars`, `datasets`, and the existing accelerator DBs — no `universe/` directory. `bar_index.py`
  is used only as an internal FastAPI dependency (`get_bar_index`) inside existing bars routes,
  confirming it has no dedicated REST route to reuse for coverage. A live
  `python -c "from app.config import Config; print(Config().config_fingerprint())"` (run from
  `apps/backend`) printed `08e471b10130e1e2`, matching `docs/goal.md` exactly — no drift.
  `reports/goal-lint.md` confirms the authored goal itself lints CLEAN.
- **No journey is human-blocked.** Unlike some prior sessions' baselines, nothing here needs
  credentials or network access to verify at baseline: the fixture/keyless paths are what J-01–J-06
  will build and test against, and the KEPT-product J-07 walkthrough runs entirely against the
  existing local backend/frontend.
- **Likely next-iteration target (informational only — not committing scope here).**
  `docs/goal.md`'s stated build order is J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07
  guarding continuously. J-01 (the universe vendor seam + parser + store + fixture +
  `GET/POST /research/desk/universe*`) is both first in dependency order and the unblocker for
  every other desk journey — nothing else (coverage, screen, briefing, MCP tools) can exist until
  a registered universe snapshot does. Per "Picking depth," J-01 touches a new store format, a new
  Config field (Path A), and a new vendor/parser seam — the iteration that plans it should weigh
  the "data model" full-depth trigger against its own evidence at that time, not inherit this
  baseline's `lean`.
- **Evidence honesty (T-10).** For J-04, J-05, and J-07, a missing screenshot means `unknown`,
  never `passing` — this applies to the browser-qa-agent's evaluation this iteration exactly as it
  will in every later iteration. Per T-9, a clean `rm -rf apps/frontend/.next` rebuild must precede
  any browser evidence capture.
- **J-07's literal acceptance spans the whole era, not just today.** `docs/goal.md`'s J-07
  acceptance line requires "nav = exactly three routes" and "MCP = exactly 17 tools," both of
  which are meaningful only once J-04/J-06 have shipped. At baseline, only J-07's
  KEPT-PRODUCT-BEHAVIOR half (the browser walk + suite-green-under-the-current-pin) is checkable;
  the evaluator should weigh that distinction rather than infer a full PASS or FAIL from partial
  (today-only) evidence.
- No assumption-ledger entry was needed this iteration — every scoping decision above follows
  directly from the goal-decomposer's baseline-mode rules and `docs/goal.md`'s own explicit
  Product Shape / dependency-ordering text; nothing here required resolving a genuine goal
  ambiguity. (The one deferred decision — coverage's exact REST sub-path — is `docs/goal.md`'s own
  explicit build-time choice, not a decomposer interpretation, and is flagged as such in
  `blueprint.md`.)
