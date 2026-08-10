# Goal Iteration 0 — Baseline verification of Era B2 "The Playbook" journeys (J-01–J-10)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10
- **Required-still-passing journeys:** None yet — baseline establishes the passing/failing set
  for every journey of this era. J-10 (kept-product regression sentinel) itself DEFINES the
  regression floor every later iteration must protect: `config_fingerprint`
  `08e471b10130e1e2`, the three kept routes/every shipped `/desk` section as shipped, and the
  full backend suite green — future iterations should list J-10 (or the specific kept surfaces
  they touch) under Required-still-passing, not this one.
- **Anti-goal reminders** (verbatim from `docs/goal.md` — Immutable rails, Era-B desk anti-goals,
  Playbook-era anti-goals, Host protection):

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
     never a mutation of them. *(critical)*
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

  *Era-B desk anti-goals that remain binding:* membership is never a signal; snapshots are
  append-only and pinned; every run is an explicit operator act; the briefing describes, never
  advises; no new statistics, gates, or strategies; the demolition stays demolished; the ledger
  never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move.
  *(all critical)*

  *Playbook-era anti-goals (added, not weakening any rail above):*
  - **No threshold exists outside the spec, and no code path sweeps one.** Every detector rule
    and threshold exists in `docs/playbook-detector-spec.md` BEFORE the code that uses it; no
    code path iterates thresholds against outcomes (source-scan guard-tested); a threshold
    change is a spec revision + new signature, never an edit of recorded signals and never a
    sweep. *(critical)*
  - **A signal is an observation, not a call.** No signal, chip, or evidence cell uses advice,
    imperative, prediction, probability, expectancy, edge, or significance language; the served
    registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
    `invalidation_price` is geometry, never an order concept. *(critical)*
  - **The evidence pools one signature.** Distributions never mix parameter regimes; other
    signatures are listed, not merged; the min-n floor tags, it never filters; truncated values
    never enter a pool undisclosed. *(critical)*
  - **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.**
    New signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*
  - **No second implementation of the measurement rail.** Measurement helpers are imported from
    `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
    MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
    inside the `AUTO:journeys` marker block in `docs/goal.md` — it MUST NOT edit human-authored
    journeys, the Anti-goals section, or any other part of that file; proposed journeys MUST
    carry a single-source-of-truth acceptance criterion, keep the `default` profile and `v1`
    byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey
    just to keep the loop alive is a failure. *(critical)*

  *Host protection (carried verbatim — a physical constraint of the host, not product scope):*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
    `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
    engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
    Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening
    the mask follows the verification ladder in
    `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Establish, with zero code changes, exactly which of J-01–J-10 (Era B2 "The Playbook" journeys)
already pass, fail, or partially pass against the current codebase — so iteration 1 plans only
the remaining work, starting from the natural dependency order's first link (J-01).

## BACKGROUND

This is iteration 0 (`Mode: baseline`) — a verify-only assessment, not feature delivery, per the
goal-decomposer's baseline-mode rules. Depth is `lean` (matching the evaluator's own binding
recommendation) because the developer step is a no-op for code; all the value comes from the
browser-QA step exercising every journey against the current tree. Era B2 opens ADDITIVELY on
top of Era B "The Desk" (GOAL_ACHIEVED 2026-07-31, 21 journeys) plus the ratified R-2 forward-test
interlude — the product today is exactly Cockpit (`/`) + Structure (`/structure`) + Desk
(`/desk`), all shipped and, per Era B's own closure, previously verified GOAL_ACHIEVED.

Direct inspection of the current tree (HEAD `ed87dcac4a76f801b3d2d31c382e7e6d667f4057`, commit
message "docs(goal): open Era B2 'The Playbook'" — the era-open SHA this iteration records)
confirms the playbook has **not started**: a case-insensitive grep for `playbook` under
`apps/backend/app/research/` finds no `desk_playbook*.py` module of any kind (no
`desk_playbook.py`, `desk_playbook_features.py`, `desk_playbook_detect.py`,
`desk_playbook_compute.py`, `desk_playbook_log.py`, `desk_playbook_backscan.py`, or
`desk_playbook_evidence.py`); the same grep against `apps/backend/app/research/desk_routes.py`
and `apps/backend/app/mcp/__init__.py` returns zero matches (no `/research/desk/playbook*`
route, no `desk_playbook`/`desk_playbook_evidence` MCP tool); `apps/frontend/app/desk/page.tsx`
and `apps/frontend/lib/api.ts` contain no `playbook` string anywhere (no Playbook Signals
section, no Backscan panel, no Playbook Evidence table, no fetch/trigger/poll/cancel helpers for
any of them); and no `*playbook*` fixture exists under `apps/backend/tests/fixtures/`.
`docs/playbook-detector-spec.md` (the canonical detector spec) DOES exist (361 lines, §0 shared
conventions / §1 constants table / §3 the nine detectors) — it is design documentation, not code,
and is confirmed present and substantive. Three live checks confirm no drift on the invariants
every journey depends on: `python -c "from app.config import Config;
print(Config().config_fingerprint())"` (run from `apps/backend`) prints `08e471b10130e1e2`,
matching the pin exactly; `app/meta.py`'s `UI_ROUTES` tuple lists exactly 3 entries (Cockpit,
Structure, Desk); and `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple has
exactly 18 entries, ending in `get_endpoint`, with no `desk_playbook`/`desk_playbook_evidence`.
A further spot-check of `docs/goal.md`'s own "Build anchors" line-number citations against the
live tree (`DESK_FORWARD_HORIZONS_MINUTES` :112, `DESK_FORWARD_BASELINE_SEED = 1729` :138,
`forward_parameters()` :225, `_session_slice` :295, `compute_forward_input_signature` :362,
`_draw_anchor_indices` :428, `_measure_from` :451 in `desk_forward.py`;
`recorded_session_dates` :129 and `refuse_if_not_a_session` :180 in `desk_sessions.py`;
`merged_bars` :883 in `bars.py`; `_swing_pivots` :325 in `levels.py`) found every citation
byte-exact — the goal's anchors are current, not stale. `reports/goal-lint.md` (run 2026-08-10,
same day as the goal-open commit) confirms the authored goal itself lints CLEAN — deterministic
exit 0, zero semantic findings — and explicitly states the cited "1926 pass / 8 skip" suite count
is "the verified authoring-time suite count," recorded on this same commit.

So **J-01 through J-09 are expected to be recorded FAILING** this iteration — this is the
honest, expected baseline for a not-yet-started era, not a defect (J-04/J-05/J-06 in particular
are trivially blocked: each adds a detector family into the SAME `desk_playbook_detect.py`
module J-01 creates, which does not exist yet). **J-10's KEPT-product behaviors** (cockpit sim
tape + chart, `/structure` pinned-AAPL Load, every shipped `/desk` section, the full suite under
the current pin) are expected to already hold, since Cockpit/Structure/Desk were built and
verified GOAL_ACHIEVED across Era B (plus the R-2 interlude), and this baseline performs no
action that could regress them — but J-10's own acceptance text in `docs/goal.md` also requires
"MCP = exactly 20 tools," which cannot be satisfied until J-09 ships (today's count is 18). The
evaluator, not this spec, decides whether to record J-10 as passing-on-today's-kept-evidence or
partial-pending-the-later-journeys; this iteration only supplies the evidence (see TESTING
REQUIREMENTS and NOTES) — the exact treatment Era B's own baseline (`docs/phases/goal-desk-iter-0.md`)
gave its analogous J-07.

Per the natural dependency order `docs/goal.md` states ("J-01 → J-02 → J-03, then the detector
families J-04/J-05/J-06 ..., then J-07 → J-08 → J-09, with J-10 guarding continuously"),
iteration 1 should target **J-01 alone** next — it is both first in dependency order and the
unblocker for every other playbook journey (nothing else — measurement, the `/desk` section, any
detector family, the back-scan, the evidence view, the MCP tools — can exist until the shared
primitives + detect + store modules do). This session's own `lessons.md` and assumption ledger
are both empty (first iteration of a new session, nothing to apply yet). One operational,
cross-session note directly relevant to executing THIS iteration's browser checks: Chrome MCP's
`use_browser` has previously failed to attach on port 9222 mid-session in this project; if that
recurs, the browser-qa-agent should self-launch an isolated `--headless=new
--remote-debugging-port=9222 --no-sandbox --user-data-dir=<fresh>` Chrome and attach to it,
keeping it alive across the dispatch. A second reminder, already named in `docs/goal.md` as trap
T-9: browser verification must follow a clean rebuild (`rm -rf apps/frontend/.next`) before any
screenshot is trusted — a stale build can bake a wrong API base or ghost state into false results
in either direction.

## IN SCOPE

### Backend
None — this is a verify-only baseline iteration; no source files are modified.

### Frontend
None — this is a verify-only baseline iteration; no source files are modified.

### Verification scope (read-only — what gets checked, not changed)
- [ ] J-01: confirm `desk_playbook_features.py`, `desk_playbook_detect.py`, `desk_playbook.py`,
      the `PlaybookStore`, and `GET /research/desk/playbook` do not exist yet (expected: no —
      confirmed absent by grep at decompose time).
- [ ] J-02: confirm the measurement extension, `desk_playbook_compute.py`, `desk_playbook_log.py`,
      and `GET /research/desk/playbook/runs` do not exist yet (expected: no).
- [ ] J-03: confirm `/desk` has no "Playbook Signals" section, no Run Playbook control, and no
      playbook-prefixed `data-testid`s, while every shipped `/desk` section still renders exactly
      as before (expected: no new section; shipped sections unchanged).
- [ ] J-04: confirm no JBE/DBI/cup-and-handle detector implementation exists anywhere (expected:
      no — trivially blocked on J-01's absent shared detect module).
- [ ] J-05: confirm no capitulation-entry/euphoria-marker detector implementation exists anywhere
      (expected: no — same block).
- [ ] J-06: confirm no range-trade/double-top/double-bottom detector implementation exists
      anywhere (expected: no — same block).
- [ ] J-07: confirm `desk_playbook_backscan.py` and `GET .../playbook/backscan/plan` do not exist
      yet (expected: no).
- [ ] J-08: confirm `desk_playbook_evidence.py` and `GET /research/desk/playbook/evidence` do not
      exist yet (expected: no).
- [ ] J-09: confirm the MCP tool list is still exactly the 18-tool contract (no `desk_playbook`,
      no `desk_playbook_evidence`) (expected: yes — still 18).
- [ ] J-10: confirm every kept behavior still renders/passes unchanged (cockpit sim tape + chart,
      `/structure` Load for the pinned AAPL `2026-06-22` as-of date, every shipped `/desk`
      section, the full backend suite, `config_fingerprint` `08e471b10130e1e2`, nav = exactly 3
      routes) (expected: yes for the kept behaviors; the MCP-count clause of J-10's acceptance —
      20 tools — is not yet satisfiable and should be noted as such, not scored as a failure of
      the KEPT product).

### New user-facing capability
None — verify-only; the product is byte-for-byte what it was before this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None this iteration. (The eventual target delta — three new `/desk` sections and two new MCP
tools — is documented in `docs/goal.md` and in `blueprint.md`'s Information Architecture, but is
NOT executed here.)

### Blueprint conformance
No new surfaces. `blueprint.md` was freshly drafted this iteration at
`runs/goal-session-playbook/state/blueprint.md`, directly from `docs/goal.md`'s `## Product
Shape` section (carrying the unchanged Cockpit/Structure/kept-Desk inventory forward by
reference to `runs/goal-session-desk/state/blueprint.md`, never re-deriving it); this baseline
run only checks the CURRENT app (nav = Cockpit + Structure + Desk, all shipped; zero playbook
sections) against that future-state contract — it does not build toward it yet.

### Data-contract additions
None. No new displayed value is introduced this iteration. The six playbook-owned rows the era
will eventually add (playbook records, playbook compute progress, playbook run ledger, back-scan
plan, back-scan progress + ledger, evidence aggregates) are registered in `blueprint.md`'s Data
Contract as the FUTURE target, each with its proposed single owner and endpoint — none of them
are computed or served today.

## OUT OF SCOPE

- Any code change (the primitives/detect/store modules, the compute-manager trio, the run
  ledger, the three new `/desk` sections, the back-scan, the evidence view, the two new MCP
  tools, any playbook `Config` field) — begins with whichever iteration targets J-01 next, per
  the natural dependency order.
- Fixing or explaining away any journey found FAILING — recording the honest state is this
  iteration's entire job; planning the fix is iteration 1's job.
- Editing `docs/goal.md` or `docs/playbook-detector-spec.md` (the goal-proposer may append only
  inside the `AUTO:journeys` marker, and only once journeys exist to react to — not relevant at
  iteration 0; the spec is human-authored and canonical, implemented from verbatim, never
  revised here).
- Authoring detector fixtures (canonical firing / near-miss sessions) for any of J-01/J-04/J-05/
  J-06 — that is iteration 1+ build work, once the shared primitives/detect modules exist.
- Performing the REAL back-scan over recorded sessions — an operator-run act that only becomes
  exercisable once J-01/J-02/J-07 exist.
- Running the full 10h+ real-corpus edge-report sweep or any mutating recompute — read-only
  probes and the existing suite only.

## DEFINITION OF DONE

- [ ] J-01 verified against current codebase; result (failing, expected) recorded with grep/route
      evidence
- [ ] J-02 verified against current codebase; result (failing, expected) recorded with grep/route
      evidence
- [ ] J-03 verified against current codebase via a real browser; result (failing, expected)
      recorded with a screenshot showing every shipped `/desk` section unchanged and no playbook
      UI present
- [ ] J-04 verified against current codebase; result (failing, expected) recorded citing J-01's
      shared-detect-module absence
- [ ] J-05 verified against current codebase; result (failing, expected) recorded citing J-01's
      shared-detect-module absence
- [ ] J-06 verified against current codebase; result (failing, expected) recorded citing J-01's
      shared-detect-module absence
- [ ] J-07 verified against current codebase; result (failing, expected) recorded with route
      evidence
- [ ] J-08 verified against current codebase; result (failing, expected) recorded with route
      evidence
- [ ] J-09 verified against current codebase; result (failing, expected) recorded citing the
      18-entry `EXPECTED_TOOLS` tuple
- [ ] J-10 verified against current codebase via a real browser plus the full backend suite;
      result recorded with screenshots, distinguishing the KEPT-behavior evidence (expected
      passing) from the MCP-count clause (not yet satisfiable — 18 tools today, not 20)
- [ ] No anti-goal violation introduced (trivially satisfiable this iteration — verify by diff
      scope)
- [ ] `blueprint.md` is drafted at `runs/goal-session-playbook/state/blueprint.md` and reflects
      `docs/goal.md`'s Product Shape (3-route nav unchanged, the six new playbook-owned Data
      Contract rows each with exactly one proposed owner + endpoint)
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-0-dev.md`, explicitly stating no
      source files were changed

## TESTING REQUIREMENTS

- Browser (after a clean `rm -rf apps/frontend/.next` rebuild — T-9): J-03 (confirm `/desk`
  renders every shipped section unchanged and NO Playbook Signals section, Run Playbook control,
  or playbook `data-testid` anywhere), J-10 (kept-product walkthrough: a cockpit sim scenario
  rendering the `PriceChart` with candles + timeframe switch + S/R band overlay + a live tape
  bar; `/structure` Load for the pinned AAPL `2026-06-22` as-of date rendering the 300–302.4 wall
  band on `StructureChart`; every shipped `/desk` section — universe/coverage, screen briefing +
  history calendar, forward returns, refresh chain + compute controls, runs/pins/compare/
  provenance) — every step needs a screenshot; no screenshot means `unknown`, never `passing`
  (T-10).
- Unit/integration: run the full backend suite (per `.claude/project-template.md`'s test command)
  and record the pass/skip counts as the Era-B2 baseline (`docs/goal.md` cites 1926 pass / 8 skip
  at authoring, confirmed by `reports/goal-lint.md` as the verified authoring-time count on this
  same commit — reconfirm live, do not assume the cited number still holds); reconfirm
  `Config().config_fingerprint() == "08e471b10130e1e2"`; reconfirm `EXPECTED_TOOLS` in
  `test_mcp_server.py` still lists exactly the 18 pre-playbook tool names. No new tests are
  written this iteration.
- Error cases: N/A this iteration — no new code path exists yet. The CURRENT absence of every
  `/research/desk/playbook*` route (each returns HTTP 404, unregistered) is itself the baseline
  evidence for J-01/J-02/J-07/J-08; it becomes a populated-vs-honest-empty-state assertion once
  those routes ship.

Test-first contract:

- TC-1: given the backend running on committed fixtures at the current branch tip (era-open SHA
  `ed87dca`), when GET is issued to `/research/desk/playbook`, then the request returns HTTP 404
  (route not registered) — recorded as J-01 = failing; supporting evidence: a grep for
  `playbook` under `apps/backend/app/research/` returns no `desk_playbook*.py` module and no
  fixture under `apps/backend/tests/fixtures/` matches `*playbook*`.
- TC-2: given the current backend source tree, when `apps/backend/app/research/` is searched for
  `desk_playbook_compute.py` and `desk_playbook_log.py`, then neither file exists, and when GET
  is issued to `/research/desk/playbook/runs`, then the request returns HTTP 404 — recorded as
  J-02 = failing (measurement and the compute-manager trio are not yet built; trivially
  dependent on J-01, which is itself absent).
- TC-3: given a real browser at the frontend's `/desk` route after the T-9 clean rebuild, when
  the operator loads the page, then every shipped section (universe/coverage, screen briefing +
  history calendar, forward returns, refresh chain + compute controls, runs/pins/compare/
  provenance) renders exactly as before AND no "Playbook Signals" heading, Run Playbook control,
  or playbook-prefixed `data-testid` exists anywhere on the page — screenshot captured — recorded
  as J-03 = failing; supporting evidence: a case-insensitive grep for `playbook` in
  `apps/frontend/app/desk/page.tsx` and `apps/frontend/lib/api.ts` returns no matches.
- TC-4: given `apps/backend/app/research/desk_playbook_detect.py` does not exist (TC-1's own
  evidence), when the codebase is searched for a JBE/DBI/cup-and-handle detector implementation,
  then none is found anywhere — recorded as J-04 = failing.
- TC-5: given the same absence, when the codebase is searched for a capitulation-entry or
  euphoria-marker detector implementation, then none is found anywhere — recorded as J-05 =
  failing.
- TC-6: given the same absence, when the codebase is searched for a range-trade or double-top/
  double-bottom detector implementation, then none is found anywhere — recorded as J-06 =
  failing.
- TC-7: given the backend running, when GET is issued to
  `/research/desk/playbook/backscan/plan`, then the request returns HTTP 404 — recorded as
  J-07 = failing; supporting evidence: no `desk_playbook_backscan.py` module exists.
- TC-8: given the backend running, when GET is issued to `/research/desk/playbook/evidence`,
  then the request returns HTTP 404 — recorded as J-08 = failing; supporting evidence: no
  `desk_playbook_evidence.py` module exists.
- TC-9: given `apps/backend/tests/test_mcp_server.py`, when its `EXPECTED_TOOLS` tuple is
  inspected, then it contains exactly 18 entries and neither `desk_playbook` nor
  `desk_playbook_evidence` appears — recorded as J-09 = failing; a live MCP tool-list call
  independently confirming the same 18-tool count is deferred to the test-execution step.
- TC-10: given a real browser at the running frontend after the T-9 clean rebuild, when the
  operator walks a cockpit sim scenario, `/structure`'s pinned-AAPL `2026-06-22` Load, and every
  shipped `/desk` section, then each renders exactly as shipped — screenshot captured for each;
  AND when the full backend suite is run, then it reports the era-open baseline count with 0
  failures; AND `Config().config_fingerprint()` prints `08e471b10130e1e2`; AND
  `GET /meta/ui-routes` returns exactly 3 route objects — recorded as J-10's KEPT-behavior
  evidence (passing); J-10's own acceptance text also requires "MCP = exactly 20 tools," which is
  not yet satisfiable (today's count is 18) and must be recorded as a not-yet-satisfiable clause,
  never scored as a KEPT-product failure.
- TC-11: given this iteration's git diff against its parent commit, when the changed-file list is
  inspected (`git diff --stat -- apps/`), then its output is empty — zero files under
  `apps/backend/app/` or `apps/frontend/` are touched — confirming no anti-goal violation is
  possible this iteration.
- TC-12: given the iteration completes, when `runs/goal-session-playbook/state/blueprint.md` is
  read, then its Information Architecture lists the unchanged 3-route nav (Desk annotated with
  the three new not-yet-built sections) and its Data Contract table includes all six new
  playbook-owned rows (playbook records, playbook compute progress, playbook run ledger,
  back-scan plan, back-scan progress + ledger, evidence aggregates), each with exactly one named
  owner module and one serving endpoint.
- TC-13: given the iteration completes, when `docs/handoffs/goal-playbook-iter-0-dev.md` is read,
  then it exists and explicitly states that no source files were modified this iteration.

## NOTES

- **Codebase probe evidence (iter-0 decompose time).** Case-insensitive grep for `playbook`
  under `apps/backend/app/research/`, `apps/backend/app/mcp/__init__.py`,
  `apps/backend/app/research/desk_routes.py`, `apps/frontend/app/desk/page.tsx`, and
  `apps/frontend/lib/api.ts` returns zero matches in every location. No `*playbook*` fixture
  exists under `apps/backend/tests/fixtures/`. `docs/playbook-detector-spec.md` exists (361
  lines) and is substantive. `app/meta.py`'s `UI_ROUTES` tuple: 3 entries (Cockpit, Structure,
  Desk — unchanged since Era B). `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS`
  tuple has exactly 18 entries ending in `get_endpoint`. A live
  `python -c "from app.config import Config; print(Config().config_fingerprint())"` (run from
  `apps/backend`) printed `08e471b10130e1e2` — no drift. `docs/goal.md`'s own "Build anchors"
  line-number citations (`desk_forward.py`, `desk_sessions.py`, `bars.py`, `levels.py`) were all
  spot-checked byte-exact against the live tree. `reports/goal-lint.md` (2026-08-10) confirms the
  authored goal lints CLEAN (deterministic exit 0, zero semantic findings) and independently
  verified the "1926 pass / 8 skip" suite count at authoring time on this same commit.
- **No journey is human-blocked.** Nothing here needs credentials or network access to verify at
  baseline: the fixture/keyless paths are what J-01–J-08 will build and test against, SPY 5m/1m
  bars needed for market context are already frozen in the store, and the KEPT-product J-10
  walkthrough runs entirely against the existing local backend/frontend.
- **Likely next-iteration target (informational only — not committing scope here).**
  `docs/goal.md`'s stated build order is J-01 → J-02 → J-03, then J-04/J-05/J-06, then J-07 →
  J-08 → J-09, with J-10 guarding continuously. J-01 (the primitives + detect modules, the
  opening-range detector pair, the store, and the honest-empty GET) is both first in dependency
  order and the unblocker for every other playbook journey. Per "Picking depth," J-01 adds a new
  store format (though NOT a new `Config` field — the module docstring/constants pattern follows
  the `desk_forward` precedent per goal.md's own framing) — the iteration that plans it should
  weigh the "data-model" full-depth trigger against its own evidence at that time, not inherit
  this baseline's `lean`.
- **Evidence honesty (T-10) and clean-rebuild (T-9).** For J-03 and J-10, a missing screenshot
  means `unknown`, never `passing` — this applies to the browser-qa-agent's evaluation this
  iteration exactly as it will in every later iteration. A clean `rm -rf apps/frontend/.next`
  rebuild must precede any browser evidence capture. Chrome MCP's `use_browser` has previously
  failed to attach on port 9222 mid-session in this project; if that recurs, self-launch an
  isolated `--headless=new --remote-debugging-port=9222 --no-sandbox --user-data-dir=<fresh>`
  Chrome and attach to it, keeping it alive across the dispatch.
- **J-10's literal acceptance spans the whole era, not just today.** `docs/goal.md`'s J-10
  acceptance line requires "MCP = exactly 20 tools," meaningful only once J-09 has shipped. At
  baseline, only J-10's KEPT-PRODUCT-BEHAVIOR half (the browser walk + suite-green-under-the-
  current-pin + 3-route nav) is checkable; the evaluator should weigh that distinction rather
  than infer a full PASS or FAIL from partial (today-only) evidence — the exact treatment Era
  B's own baseline gave its analogous J-07.
- No assumption-ledger entry was needed this iteration — every scoping decision above follows
  directly from the goal-decomposer's baseline-mode rules and `docs/goal.md`'s own explicit
  Product Shape / dependency-ordering text; nothing here required resolving a genuine goal
  ambiguity.
