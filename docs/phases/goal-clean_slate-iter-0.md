# Goal Iteration 0 — Baseline verification of The Clean Slate demolition journeys (J-01–J-05)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** clean_slate
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05
- **Required-still-passing journeys:** None (baseline iteration — no journey has an established
  passing/failing state yet; this run creates that state for every journey). J-05's kept-product
  behaviors are *expected* to already be green per prior eras' close-out (eras 1–5C, `yahoo_fetch`,
  `tradable_wall`, `fast_wall` all ended GOAL_ACHIEVED), but that determination belongs to this
  iteration's own verification, not a pre-declared requirement.
- **Anti-goal reminders** (verbatim from `docs/goal.md` — Immutable rails, then interlude-specific):
  1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no
     "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new
     research code adds matching guard tests, never weakens them.) *(critical)*
  2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
     fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative
     trading cues. *(critical)*
  3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and
     thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour
     stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(This
     era's one sanctioned exception, operator-approved 2026-07-23: the journal/studies/performance product
     surfaces are REMOVED outright — never mutated-in-place — and their historical records stay readable;
     nothing else moves.)* *(critical)*
  4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the
     sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never
     lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor.
     *(critical)*
  5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and
     read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests
     reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface
     can change state. *(critical)*
  9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged,
     never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit,
      logged act. *(critical)*
  - **No research-value change beyond the documented epoch bump.** Every number a KEPT surface serves
    (levels, bands, touch events, edge cells, pnl rows) stays byte-identical on identical inputs; the ONLY
    sanctioned change is the `config_fingerprint` value itself, moved once via the J-04 Path B journey;
    cross-epoch pooling is forbidden forever. *(critical)*
  - **Deletion is complete, never cosmetic.** No orphaned imports, dead components, unreachable routes,
    dangling MCP tools, or skipped tests survive; a deleted surface is gone from code, routes, nav, MCP,
    types, and tests alike — grep-provably. *(critical)*
  - **No new features.** This era ships zero new product capabilities, pages, endpoints, strategies, or
    Config fields; anything new belongs to the next eras. *(critical)*
  - **Relocations are moves, not rewrites.** `r_basis` and the dataset-source constants keep byte-identical
    behaviour at their new homes; every kept caller's output is proven unchanged. *(critical)*
  - **Never modify the charts beyond the one named edit.** No commit in this era may edit
    `StructureChart.tsx` at all, or edit `PriceChart.tsx` beyond removing its thesis-geometry overlay
    build (I-7 chart clause); the three chart guard suites must pass byte-unmodified; any other chart
    diff — visual or behavioral — is a veto-class defect. *(critical)*
  - **Never touch a historical record.** No commit in this era may delete, rewrite, truncate, or re-stamp
    journal.db's existing rows or tables, any PnL-ledger row, anything under `docs/goal-archive/` or
    `runs/goal-session-*`, or any `reports/goal-session-*-delivered.md` — a diff touching any of these is a
    veto-class defect (deleting CODE is the mandate; deleting RECORDS is forbidden). *(critical)*
  - **No guard weakening.** `test_no_execution_path.py`, the source-introspection guards, and every kept test
    stay as written; the fingerprint pins change ONLY inside J-04 per Path B, never to make a red test green.
    *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the
    `AUTO:journeys` marker block in `docs/goal.md` — it MUST NOT edit human-authored journeys, the Anti-goals
    section, or any other part of that file; proposed journeys MUST carry a single-source-of-truth (or
    PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a
    `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure.
    *(critical)*

## GOAL

Establish, with zero code changes, exactly which of J-01 – J-05 (the Clean Slate demolition journeys)
already pass, fail, or partially pass against the current codebase — so subsequent iterations plan
only the remaining work.

## BACKGROUND

This is iteration 0 (`Mode: baseline`) — a verify-only assessment, not feature delivery, per the
goal-decomposer's baseline-mode rules. Depth is `lean` because the developer step is a no-op here;
all the value comes from the browser-qa step exercising every Must-have journey. Direct inspection of
the current branch (`goal/clean_slate_build` @ `e7865b4`, one commit past the `fa76460` the goal was
authored against) confirms the demolition has **not started**: `apps/frontend/app/{journal,studies,performance}/`
all still exist, `python -c "from app.config import Config; print(Config().config_fingerprint())"`
still prints the OLD pin `4d665603569b9dbf`, and `app/mcp/__init__.py`'s `_TOOL_PATHS` still registers
`journal`/`analytics`/`studies`. So **J-01 through J-04 are expected to be recorded FAILING** this
iteration (their acceptance criteria require deletions/relocations/a fingerprint move that have not
happened) — this is the expected, honest baseline for a not-yet-started demolition, not a defect.
**J-05's kept-product behaviors** (sim cockpit incl. both charts, `/structure` Load, case studies, the
Edge Report's honest state, the full suite under the CURRENT pin) are expected to already hold, since
Cockpit + Structure were built and verified GOAL_ACHIEVED across eras 1–5C, `yahoo_fetch`,
`tradable_wall`, and `fast_wall`, and this baseline performs no action that could regress them. Note,
though, that J-05's own acceptance text in `docs/goal.md` ties its FULL closure to running after J-04
("full suite green under **the new pin**," plus a cumulative diff-vs-inventory cross-check that only
means something once J-01–J-04 have executed) — the evaluator, not this spec, decides whether to
record J-05 as passing-on-today's-evidence or partial-pending-the-later-journeys; this iteration only
supplies the evidence (see NOTES). Per the priority rubric's natural dependency order stated in
`docs/goal.md` (J-01 → J-02 → J-03 → J-04 → J-05, "with J-05 guarding continuously"), iteration 1
should target **J-01 alone** next — it is both the first in dependency order and the unblocker for
every other journey (nothing else can be verified as truly done until the backend surface is gone).
This session's own `lessons.md` is empty (first iteration, nothing to apply yet). One cross-session
lesson is relevant to executing THIS iteration's browser checks: Chrome MCP's `use_browser` has
previously failed to attach on port 9222 mid-session; if that recurs, the browser-qa-agent should
self-launch an isolated `--headless=new --remote-debugging-port=9222 --no-sandbox --user-data-dir=<fresh>`
Chrome and attach to it, keeping it alive across the dispatch.

## IN SCOPE

### Backend
None — this is a verify-only baseline iteration; no source files are modified.

### Frontend
None — this is a verify-only baseline iteration; no source files are modified.

### Verification scope (read-only — what gets checked, not changed)
- [ ] J-01: confirm whether the 15-journal-era-route deletion, the two byte-identical relocations
      (`r_basis` → `backtests.py`; the four dataset-source symbols → `datasets.py`), the eleven-module
      deletion, and the `JournalStore` method deletions have already happened (expected: no).
- [ ] J-02: confirm whether `/journal`, `/journal/[id]`, `/studies`, `/performance` already 404, whether
      the WS frame already drops `thesis`/`hint`, and whether the cockpit/`Cockpit.tsx` already lost
      their thesis/hint/sound integration (expected: no — all still present).
- [ ] J-03: confirm whether the MCP tool list already matches the 15-tool I-6 contract (expected: no —
      `journal`/`analytics`/`studies` still registered).
- [ ] J-04: confirm whether `config_fingerprint()` already returns a new pin and the I-4 confirmed-delete
      `Config` fields are already gone (expected: no — old pin `4d665603569b9dbf`, old fields present).
- [ ] J-05: confirm each kept-product behavior in TC-6/TC-7/TC-8 below still renders/passes unchanged
      (sim cockpit incl. both charts, `/structure` Load for the pinned AAPL 2026-06-22 as-of date, Case
      Studies, Edge Report honest state, full backend suite) (expected: yes).

### New user-facing capability
None — verify-only; the product is byte-for-byte what it was before this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None this iteration. (The eventual target delta — nav shrinks to Cockpit + Structure, three pages and
15+ routes disappear — is documented in `docs/goal.md` and in `blueprint.md`'s Information Architecture,
but is NOT executed here.)

### Blueprint conformance
No new surfaces. `blueprint.md` was freshly drafted this iteration (see below) directly from
`docs/goal.md`'s `## Product Shape` section; this baseline run only checks the CURRENT app against that
future-state contract, it does not build toward it yet.

### Data-contract additions
None. No new displayed value is introduced this iteration.

## OUT OF SCOPE

- Any code change (relocations, deletions, fingerprint bump, test edits) — begins with whichever
  iteration targets J-01 next, per the natural dependency order.
- Capturing the I-9 step-1 byte-comparison baseline (`kept-route-baseline.txt`) — that capture is J-01's
  own first action (per J-01 Step 1 in `docs/goal.md`) and belongs immediately before J-01's own
  deletions start, not to this baseline pass where nothing is about to change.
- Fixing or explaining away any journey found FAILING — recording the honest state is this iteration's
  entire job; planning the fix is iteration 1's job.
- Editing `docs/goal.md` itself (only the goal-proposer may append inside the `AUTO:journeys` marker,
  and only once journeys exist to react to — not relevant at iteration 0).
- Re-running or second-guessing the Demolition inventory (I-1 … I-9) — it is treated as verified ground
  truth per `docs/goal.md`'s own framing, with one flagged reconciliation note below (NOTES section).

## DEFINITION OF DONE

- [ ] J-01 verified against current codebase; result (passing/failing/partial) recorded with evidence
- [ ] J-02 verified against current codebase via a real browser; result recorded with screenshots
- [ ] J-03 verified against current codebase; result recorded with evidence
- [ ] J-04 verified against current codebase; result recorded with evidence
- [ ] J-05 verified against current codebase via a real browser plus the full backend suite; result
      recorded with screenshots
- [ ] No anti-goal violation introduced (trivially satisfiable this iteration — verify by diff scope)
- [ ] `blueprint.md` is drafted at `runs/goal-session-clean_slate/state/blueprint.md` and reflects
      `docs/goal.md`'s Product Shape (Cockpit + Structure nav, KEPT Data Contract rows)
- [ ] Dev handoff written at `docs/handoffs/goal-clean_slate-iter-0-dev.md`, explicitly stating no
      source files were changed

## TESTING REQUIREMENTS

- Browser: J-02, J-05 (both require real-browser evidence per `docs/goal.md`; screenshot or it is
  `unknown`, never `passing` — T-13)
- Unit/integration: J-01, J-03, J-04 are keyless/automated (no browser needed) — verified via HTTP
  calls to the running backend, a repo grep, an MCP tool-list request, and a one-line `python -c` print
- Error cases: N/A this iteration (no new code path). The CURRENT (pre-deletion) 200-OK responses on the
  soon-to-be-deleted routes are themselves the baseline evidence that J-01/J-02 have not happened yet —
  they become 404 assertions once deletion executes in a later iteration.

Test-first contract:

- TC-1: given the backend running on committed fixtures at the current branch tip, when `GET` is issued
  to `/research/analytics`, `/research/journal`, `/research/studies`, and `/research/hints`, then each
  returns HTTP 200 (not 404) — recorded as J-01 = failing (the I-1 route deletions have not happened).
- TC-2: given the current backend source tree, when a grep is run for
  `from .journal_rows import|from .monitor import|from .hints import|from .stance import|from .verdict import|from .grades import|from .marks import|from .excursions import|from .execution_checks import|from .analytics import|from .studies import`
  under `apps/backend/app/research/routes.py`, then all eleven I-2 DELETE-list modules are still found
  imported — recorded as supporting evidence that J-01's module deletions have not started.
- TC-3: given a real browser at `http://localhost:3000` with the backend at `http://localhost:8000`,
  when the operator navigates to `/journal`, `/studies`, and `/performance`, then each renders its
  existing page content (the journal table / study list / analytics view) — NOT the app's 404 — with a
  screenshot captured for each — recorded as J-02 = failing.
- TC-4: given the MCP server started against the running backend, when its tool list (`_TOOL_PATHS` /
  `list_tools`) is requested, then the response still includes `journal`, `analytics`, and `studies`
  tool entries (more than the 15-tool I-6 contract) — recorded as J-03 = failing.
- TC-5: given the backend running, when `python -c "from app.config import Config;
  print(Config().config_fingerprint())"` is run from `apps/backend`, then it prints the OLD pin
  `4d665603569b9dbf`, and a grep for `verdict_dwell_seconds` and `hint_sustain_dwell_seconds` in
  `apps/backend/app/config.py` finds both still present — recorded as J-04 = failing.
- TC-6: given a real browser at `http://localhost:3000`, when the operator drives a `SIM-BUYER` cockpit
  scenario to settle `buyer_control`, then the sim settles into the `buyer_control` state AND the cockpit `PriceChart`
  renders candles, allows a timeframe switch, overlays an S/R band, and shows a live tape bar moving —
  screenshot captured — recorded as supporting evidence for J-05.
- TC-7: given a real browser at `http://localhost:3000/structure`, when the operator loads the pinned
  AAPL `2026-06-22` as-of date, then the 300–302.4 wall band renders on the `StructureChart`, a Case
  Study drill-in opens, and the Edge Report section shows either warm cells or the honest
  "Edge report not computed yet." panel with a Compute button — screenshot captured for each — recorded
  as J-05 = passing (or the specific gap found, documented, if any).
- TC-8: given the committed test fixtures, when the full backend test suite is run
  (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`), then it reports 0 failures (matching the
  fast_wall close-out's 1544-pass/7-skip baseline plus any tests added since) — recorded as supporting
  evidence for J-05.
- TC-9: given this iteration's git diff against its parent commit, when the changed-file list is
  inspected, then it contains only paths under `docs/phases/`, `docs/handoffs/`,
  `runs/goal-session-clean_slate/`, and `reports/` — zero files under `apps/backend/app/` or
  `apps/frontend/` are touched — confirming no anti-goal violation is possible this iteration.
- TC-10: given the iteration completes, when `runs/goal-session-clean_slate/state/blueprint.md` is
  read, then it contains an "Information Architecture" section whose navigation skeleton lists exactly
  Cockpit (`/`) and Structure (`/structure`), and a "Data Contract" table with one row per KEPT
  canonical value named in `docs/goal.md`'s Product Shape section (bands, touch events, edge cells,
  ledger rows, bars, levels, registry/champion, taxonomy, routes, `config_fingerprint`).
- TC-11: given the iteration completes, when `docs/handoffs/goal-clean_slate-iter-0-dev.md` is read,
  then it exists and explicitly states that no source files were modified this iteration.

## NOTES

- **Route-count reconciliation (flag, not a blocker).** `docs/goal.md`'s Vision and Success Criteria
  prose says "15 journal-era routes," but the I-1 DELETE table enumerates exactly 14 route decorators,
  and a direct grep of `app/research/routes.py` at the current HEAD (`@router.get/post` matching
  journal/thesis/hint/studies/analytics) also returns exactly 14 hits. `GET /research/taxonomy`
  (`routes.py:446`) is explicitly SLIM, not DELETE, per I-1/I-2, so it is not a hidden 15th. Treat the
  I-1 table (14 rows) as ground truth, consistent with `docs/goal.md`'s own instruction to
  "always re-locate by symbol/route/decorator NAME (grep), never by line arithmetic." Whichever
  iteration executes J-01 should re-grep at execution time rather than trust either count blindly, and
  surface it (per T-14) only if a genuine 15th route turns up.
- **Depth expectation for iteration 1.** J-01 alone (relocations + 15/14-route deletion + 11-module
  deletion + `JournalStore` method deletion + `Config`/`main.py` edits + test-file deletions) is large,
  structural, and crosses many files with an explicit two-phase ordering constraint (relocate-and-prove-
  green BEFORE deleting). Per "Picking depth," this strongly suggests `full` depth for iteration 1 (the
  decomposer planning that iteration should make the call explicitly against that iteration's own
  evidence, not inherit this baseline's `lean`).
- **Evidence honesty (T-13).** For J-02 and J-05, a missing screenshot means `unknown`, never `passing`
  — this applies to the browser-qa-agent's evaluation this iteration exactly as it will in every later
  iteration.
- **J-05's literal acceptance spans the whole interlude, not just today.** `docs/goal.md`'s J-05
  acceptance line requires "full suite green under the new pin" and a diff-vs-inventory cross-check of
  the cumulative era diff — both only meaningful once J-04 has executed. At baseline, only J-05's
  KEPT-PRODUCT-BEHAVIOR half (the browser walk + suite-green-under-the-CURRENT-pin) is checkable; the
  evaluator should weigh that distinction rather than infer a full PASS from partial (today-only)
  evidence.
- No assumption-ledger entry was needed this iteration — every scoping decision above follows directly
  and unambiguously from the goal-decomposer's baseline-mode rules and `docs/goal.md`'s own explicit
  Product Shape / ordering-discipline text; nothing here required resolving a genuine goal ambiguity.
