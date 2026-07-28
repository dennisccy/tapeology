# Goal Iteration 13 — J-09's demo-narrator walkthrough, correctly ordered (full depth)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 13
- **Mode:** next
- **Depth:** full
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

Produce the one artifact `docs/goal.md`'s J-09 acceptance text still requires — a `[NEW]`-flagged
demo-narrator walkthrough that shows the honest "No top-up runs recorded yet." state and a
populated Top-up Runs state (attempted-of-total, per-outcome counts, a failed pair's own recorded
detail) in ONE artifact, in sequence — by dispatching at **full** depth (so the walkthrough lane
runs BEFORE the evaluator scores this iteration, not after) and by fixing the capture-order defect
that made iteration 12's own attempt structurally impossible (boot a live, hydrated `/desk` BEFORE
any run is recorded into the rig, never after), with **zero product-code change**.

## BACKGROUND

Iteration 11 built and independently re-verified every behavioral clause of J-09 in full — the
append-only per-run ledger, `GET /research/desk/topup/runs`, the `/desk` "Top-up Runs" section, the
byte-identical-outcomes proof, the cancelled-run and interrupted-run honesty guarantees, the
second-run append-only proof, the full suite, the fingerprint, the 17-tool MCP contract, and
`coherence.md` = COHERENCE-PASS. Only one clause was ever left unmet: `docs/goal.md`'s own text
requires "a `[NEW]`-flagged demo-narrator walkthrough covers the top-up-run disclosure end to end."
Two iterations have now tried and failed to close it, for two different, now-understood reasons:

1. **Iteration 11's walkthrough** narrated only the honest-empty panel, because the ambient store it
   recorded against genuinely had zero top-up runs — a feature whose whole point is accumulating
   state cannot be demonstrated on a store deliberately kept empty (`lessons.md` iter-11, third
   entry). Evaluator verdict: `CONTINUE`.
2. **Iteration 12** (dispatched `lean`) rebuilt a scoped, populated rig exactly as recommended and
   captured two genuine, correct standalone screenshots (`reports/qa/goal-desk-iter-12-evidence/
   UT-J-09-empty-topup-section.png` and `UT-J-09-populated-topup-section.png`) — but produced **no**
   demo-narrator artifact at all: `runs/goal-session-desk/trace/trace.jsonl` shows the demo-narrator
   lane runs AFTER the goal-evaluator at `lean` depth (iteration 10: evaluator 09:44 → demo-narrator
   09:59) but BEFORE it at `full` depth (iteration 11: demo-narrator 13:18 → evaluator 14:17). A lean
   iteration whose only outstanding acceptance clause is a showcase artifact is therefore structurally
   unscoreable — it cannot possibly close in the same pass it is produced. Iteration 12 also surfaced
   a second, independent defect: its dev lane's own capture order was seed → record three checkpoint
   runs → **then** boot the frontend (`docs/handoffs/goal-desk-iter-12-dev.md` §§2–4), which closed
   the honest "nothing saved yet" window before any browser existed at all — the append-only rail
   forbids re-opening it by deleting real records, so the browser-QA lane had to seed and boot a
   SECOND, disconnected scoped root (`desk-iter12-scoped-qa-empty`, `:8302`/`:3302`) just to
   photograph the empty half. The evaluator accepted that split for the two *standalone* screenshots
   (both roots are `cp -a` copies of the identical ambient tree — see `assumptions.md` iter-12,
   first entry) but a single coherent demo-narrator walkthrough cannot be assembled from two
   different, disconnected browser sessions on two different rigs. Evaluator verdict: `ESCALATE`
   (the session's first) — this session's first-ever escalation, with an explicit, ordered
   next-step recommendation (`runs/goal-session-desk/iter-12/eval.md` "Next-Step Recommendation").

**This iteration fixes both root causes, together, in one pass:**

- **Depth = full** puts the demo-narrator lane BEFORE the evaluator, so the walkthrough this
  iteration produces can actually be scored this same iteration.
- **Capture order is corrected**: seed ONE fresh scoped root → `rm -rf apps/frontend/.next` and boot
  BOTH the scoped backend AND the scoped frontend against it → **while the rig is still genuinely
  empty and the frontend is already live**, capture the honest-empty state → **only then** record
  the same three-checkpoint recipe that already worked twice (iteration 11's browser-QA lane,
  iteration 12's dev lane) → capture the populated state on that SAME still-live rig → assemble both
  captures, in sequence, into one `[NEW]`-flagged demo-narrator walkthrough artifact.

**Target selection.** Per the priority rubric: journey-history shows 8 passing (J-01–J-08), 1
partial (J-09), 0 failing, 0 regressed. J-09 is the only journey not `passing`; it is not
human-blocked (nobody has to decide anything — this is a picture the automation can take by itself
with the ordering fixed); and it remains the smallest possible spec (zero source lines, one
re-recorded artifact). It is this iteration's sole target, exactly as it was for iterations 11 and
12.

**Depth — full, trigger (3) "Prior ESCALATE" — mandatory, no exceptions.** Iteration 12's verdict
was `ESCALATE`; per the depth rubric this alone forces `full` with no discretion. It is also, quite
concretely, the only depth that can work here: J-09's sole remaining gap is a showcase artifact
whose owning lane runs post-evaluation at `lean` depth (see BACKGROUND above) — dispatching `lean`
again would repeat iteration 12's exact dead end. ("Consecutive lean iterations dispatched: 1" —
irrelevant; the mandatory ESCALATE trigger already applies and this dispatch resets that counter.)

**Lessons applied** (from `lessons.md`, most directly relevant first): (i) *iter-12, second entry* —
an append-only store's honest-empty state is a one-way door; photograph it BEFORE the first record
is written, and sequence frontend-boot before any write, on one root — this iteration's IN SCOPE
below states that exact order as the load-bearing fix. (ii) *iter-12, first entry* — the lane that
owns a showcase-artifact acceptance clause must be checked against dispatched depth; `full` is
mandatory here, not merely preferred. (iii) *iter-11, third entry* — name the scoped rig (and the
records it must already hold) in the demo/showcase dispatch itself, not only dev/QA. (iv) *iter-10*
— an evidence-only compute can silently collide with an existing record under the same key inside a
store a golden replays against; this iteration seeds a brand-new root, so no collision is expected,
but the collision check is still performed and disclosed. (v) *iter-9, second entry* — the
scoped-rig discipline must hold in EVERY lane, and every results/demo report must name the data
root used. (vi) *iter-8* — any lane that edits a golden (`journey-scripts/J-09.json` or any other)
must say so explicitly. (vii) *iter-4/iter-5* — a golden replay step or a UI click reaching a
compute/fetch/Run control is a WRITE path; scope every replay and every recording to this
iteration's own fresh copy, never the ambient store, and give any script whose steps reach a
mutating control a post-match liveness assertion.

## IN SCOPE

### Backend
- [ ] None — zero product/application code change. `desk_topup_log.py`, `desk_topup_compute.py`,
      `desk_routes.py`, `desk_screen.py`, `desk_coverage.py`, `tradability.py`, `levels.py`,
      `bars.py`, `app/mcp/__init__.py`, `config.py`, `meta.py` all stay byte-unmodified.

### Frontend
- [ ] None — zero product/application code change. `apps/frontend/app/desk/page.tsx`,
      `lib/types.ts`, `lib/api.ts`, `StructureChart.tsx`, `PriceChart.tsx` all stay
      byte-unmodified.

### Evidence capture (ops/showcase only — no source change; ORDER IS THE FIX, do not reorder)
- [ ] **First, environment hygiene.** Before seeding anything, inventory and stop whatever is
      currently bound to this era's scoped-rig ports (`:8301`/`:3301`, and `:8302`/`:3302` if
      occupied) — including any successor of iteration 12's leftover backend (PID `1180202`, last
      observed by the iter-12 evaluator at ~78% CPU with no page attached; that specific PID is
      already gone, but do not assume the ports are clear — verify independently). For any process
      found and stopped, confirm via `taskset -pc <pid>` (or equivalent) that it never ran outside
      the host-guard CPU mask `4-7,12-15` before stopping it, and record the finding.
- [ ] Seed ONE fresh throwaway root, distinctly named from every prior iteration's
      (`desk-iter9-scoped-qa`, `desk-iter10-scoped-qa`, `desk-iter11-scoped-qa`,
      `desk-iter12-scoped-qa` / `desk-iter12-scoped-qa-empty`), via the existing, reusable
      `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` (pass a new `root_dir`) — a `cp -a`
      of the CURRENT ambient `apps/backend/.data/` tree. Nothing in this list ever targets the
      ambient store.
- [ ] Before recording anything into the fresh rig, check it for any pre-existing top-up-run
      record under the same identifying key a new run might collide with (the iter-10 lesson); a
      brand-new root makes a collision unlikely, but disclose the check's result either way.
- [ ] `rm -rf apps/frontend/.next` (T-9), then boot BOTH the scoped backend AND the scoped
      frontend against the fresh root — **BEFORE recording a single run into it.** This is the
      load-bearing fix: iteration 12 recorded all three checkpoint runs before the frontend ever
      started, which meant no browser existed while the store was genuinely empty, forcing a
      second, disconnected root just to photograph the empty half. This time a live, hydrated
      `/desk` page must be reachable while the rig is still empty.
- [ ] **With the rig live and still empty**, capture the honest "No top-up runs recorded yet."
      state as this iteration's FIRST capture — confirm live via `GET /research/desk/topup/runs`
      returning `{"runs": [], "latest": null}` at the same moment, and use this as the opening
      state for the `[NEW]`-flagged demo-narrator walkthrough's J-09 step(s).
- [ ] **Only after** that first capture is on disk, record the three checkpoint top-up runs into
      the SAME rig — the recipe already proved correct twice (iteration 11's browser-QA lane,
      iteration 12's dev lane): one ordinary run (`state: done`, `pairs_attempted == pairs_total`),
      one run cancelled mid-walk (`state: cancelled`, `pairs_attempted < pairs_total`), one run
      with at least one induced `failed` pair whose vendor detail is preserved verbatim (a
      monkeypatched `_run_one_pair` / an `_NthCallFailsAdapter`-style double, the same technique
      `test_desk_topup_compute.py` already uses) — never a live vendor call.
- [ ] **With the rig now populated (same root, same still-live frontend — never restarted or
      swapped in between)**, capture the populated Top-up Runs section as this iteration's SECOND
      capture: the latest run's attempted-of-total count, its per-outcome (reused/fetched/failed)
      counts, and the failed pair's own recorded detail, all legible in one image.
- [ ] Assemble the `[NEW]`-flagged demo-narrator walkthrough for J-09 so it contains BOTH captures,
      in sequence (empty first, populated second), inside ONE artifact — whether by extending
      `reports/phase-goal-desk-iter-11-demo.json`'s existing J-09 step in place, adding a second
      J-09 step immediately after it, or authoring a fresh `reports/phase-goal-desk-iter-13-demo.json`
      that reuses the same highlight steps against this iteration's rig, is a build-time choice; any
      of the three is acceptable as long as the resulting artifact carries both halves in one
      coherent walkthrough with narration matching what each paired screenshot actually shows.
- [ ] Name the scoped rig's absolute path explicitly in the demo/showcase dispatch itself, not only
      the dev/QA one (the iter-11 lesson), and in every results report produced this iteration.
- [ ] Replay the regression set (`journey-scripts/J-01.json` through `J-05.json`, `J-07.json`,
      `J-08.json`) against the same scoped backend; any step reaching a compute/fetch/Run control
      stays scoped, never ambient (the iter-4/iter-5 lesson). J-06 is re-confirmed via
      `test_mcp_server.py`'s existing 17-tool contract — it has no browser surface. Record results.
- [ ] Capture the ambient `apps/backend/.data/` tree's full file listing + per-file SHA-256
      checksum BEFORE any of the above begins, and again AFTER all of it completes; diff the two
      and prove zero write landed there.
- [ ] If `journey-scripts/J-09.json` (already edited once, 2026-07-28) or any other golden is
      edited again by any lane this iteration, say so explicitly in that lane's own results report
      (the iter-8 lesson).
- [ ] Standalone browser-qa-agent screenshots for J-09's two states are already DONE and
      evaluator-opened (`reports/qa/goal-desk-iter-12-evidence/UT-J-09-empty-topup-section.png`,
      `UT-J-09-populated-topup-section.png`) — not required to be redone this iteration (binding
      "Do not redo"). If this iteration's correctly-ordered single-rig setup incidentally yields an
      equivalent same-rig pair as a costless side effect of the walkthrough capture, recording it is
      fine, but it is never a requirement.

### New user-facing capability
None — J-09's Top-up Runs section, store, and endpoint already shipped in iteration 11 and are
already visible in production. This iteration only captures the narrated-walkthrough evidence
`docs/goal.md`'s acceptance text still requires.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — this is a verification/showcase pass. The operator sees nothing new; the automation proves
the already-shipped Top-up Runs disclosure narrates end to end, not only its empty half, and does
so in one continuous, correctly-ordered artifact instead of two disconnected ones.

### Blueprint conformance
No new page, no nav-skeleton change. `/desk` remains the ALREADY-REGISTERED canonical home for
J-09 (Feature/journey homes table, Desk nav section). `runs/goal-session-desk/state/blueprint.md`
has been updated additively (before this dispatch): the J-09 Feature/journey-homes row's annotation
now records that iteration 12 (lean) could not close the walkthrough clause for a structural,
lane-ordering reason and also surfaced a capture-order defect, and that iteration 13 (full depth,
corrected order) re-attempts it — plus a "NOTED at iter-13" trailer paragraph recording that this
iteration adds no new Data-Contract row and no nav change. No `blueprint.reapproval-requested` file
was written — nothing about the nav skeleton changed.

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
- Triggering a top-up, screen, or fetch against the ambient `apps/backend/.data/` store — every
  capture and every recorded run this iteration targets its own fresh scoped copy only.
- A real ~100-symbol operator top-up run — this iteration proves the walkthrough on a
  fixture-scoped rig only; the real run stays a separate, explicit, honestly-reported operator act.
- Backfilling, rewriting, or recomputing any already-recorded universe, screen, or top-up-run
  record — the append-only rail is absolute, including on this iteration's own fresh rig (a
  mistaken empty-window loss is fixed by re-seeding a NEW root, never by deleting a recorded run).
- Reusing or continuing any prior iteration's scoped root (`desk-iter9-scoped-qa`,
  `desk-iter10-scoped-qa`, `desk-iter11-scoped-qa`, `desk-iter12-scoped-qa` /
  `desk-iter12-scoped-qa-empty`) — this iteration seeds its own fresh, distinctly-named root.
- Re-capturing separate, standalone browser-qa-agent evidence screenshots for J-09 — already DONE
  and evaluator-opened (binding "do not redo"); this iteration's job is the still-missing
  demo-narrator walkthrough artifact, not a re-shoot of already-accepted standalone frames.
- Re-verifying J-01–J-08's own deep acceptance clauses beyond the smoke-set deterministic replay —
  "Do not redo" per `iteration-state.md`.
- The backlogged `bar-index-store-reconcile` proposal — not promoted by the goal-proposer this
  cycle; do not build it.
- The carried, non-blocking hardening items: the run list dropping `integrity_errors`
  (`desk_routes.py:258`), the narrow auto-refresh race (`app/desk/page.tsx:1116-1121`), the missing
  run-table cap, the six-stacked-sections page length, the same-date-screen ambiguity, and keyboard
  access for the history rows — all unrelated to this journey, none of this iteration's job.
- Widening, disabling, or bypassing the host-guard CPU caps (`4-7,12-15`) for any process this
  iteration starts, including to make setup or cleanup faster — that anti-goal is `critical`.

## DEFINITION OF DONE

- [ ] Target journey J-09 passes with a newly-produced, `[NEW]`-flagged demo-narrator walkthrough
      that shows, in ONE artifact and in sequence, (a) the honest "No top-up runs recorded yet."
      state, captured on a live, already-booted `/desk` page BEFORE any run was recorded into the
      rig, and (b) a populated Top-up Runs section (attempted-of-total, per-outcome counts, a
      failed pair's own detail, all legible) captured afterward on the SAME scoped rig — with each
      step's narration matching what its own paired screenshot actually shows.
- [ ] Required-still-passing journeys J-01–J-08 remain green: J-01–J-05, J-07, J-08 via
      deterministic replay against this iteration's scoped backend; J-06 re-confirmed via its
      existing MCP contract test (`test_mcp_server.py`) — it has no browser surface.
- [ ] No anti-goal violation introduced: zero write to the ambient `apps/backend/.data/` store this
      iteration (its file listing and every file's checksum are identical before and after), and
      any scoped-rig process left running from a prior iteration is confirmed stopped before this
      iteration's own rig is seeded.
- [ ] Unit tests pass; no regressions — full backend suite reports at or above 1369 passed / 8
      skipped / 0 failed; `Config().config_fingerprint()` still prints `08e471b10130e1e2`; zero
      diff on every named product source file.
- [ ] The demo/showcase report AND any browser-QA/evidence report produced this iteration each
      state, in plain text, the absolute scoped-root path used for every capture this iteration.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-13-dev.md`.

## TESTING REQUIREMENTS

- Browser: smoke replay of J-01 through J-05, J-07, J-08 (deterministic golden replay against this
  iteration's scoped backend; any step reaching a compute/fetch/Run control stays scoped, never
  ambient). J-09 is verified via the newly-recorded, correctly-ordered `[NEW]`-flagged
  demo-narrator walkthrough — standalone browser-qa-agent screenshots for J-09 are already DONE
  from iteration 12 and are not required to be redone (binding do-not-redo). No new golden script
  is required by this spec (an executor may choose to refresh `journey-scripts/J-09.json` too,
  disclosing it per the iter-8 lesson if so).
- Unit/integration: full backend suite re-run (`cd apps/backend && .venv/bin/python -m pytest
  tests/ -v` — the `-v` flag is required in this environment to reliably see the final summary
  line, per iteration 12's own disclosed environment note) to confirm the floor and pin hold; no
  new tests are expected since no product code changes.
- Error cases: none newly introduced — no new code path this iteration. The one already-required
  error case (a failed pair's detail preserved verbatim while the walk continues) is exercised
  again while recording the three checkpoint runs, not newly tested.

Test-first contract — TC- scenarios:

- TC-1: given a fresh scoped root seeded from the current ambient `apps/backend/.data/` tree via
  the existing scoped-backend script at a NEW root_dir distinct from every prior iteration's, when
  both the scoped backend AND scoped frontend are booted against it and no top-up run has yet been
  recorded, then `GET /research/desk/topup/runs` on that backend returns HTTP 200
  `{"runs": [], "latest": null}` AND a live-browser screenshot of `/desk` on that same rig legibly
  shows "No top-up runs recorded yet." with zero run rows — captured with the frontend already
  live, never before it existed.
- TC-2: given TC-1's still-empty, still-live rig, when three checkpoint top-up runs are recorded
  into it in this order (one ordinary with `pairs_attempted == pairs_total`, one cancelled with
  `pairs_attempted < pairs_total`, one with at least one induced `failed` pair carrying a non-null
  verbatim detail), then `GET /research/desk/topup/runs` on that same backend returns a `runs` list
  with 3 entries and a `latest` record whose `outcomes` include an entry with `outcome: "failed"`
  and non-null `detail`, and the same rig — not a second one — is still serving the frontend.
- TC-3: given TC-2's now-populated rig with its frontend still live from TC-1 (never restarted or
  swapped in between), when `/desk` is reloaded, then one screenshot legibly shows the latest run's
  attempted-of-total pair count, its per-outcome (reused/fetched/failed) counts, and the failed
  pair's own recorded detail text, all in the same image.
- TC-4: given TC-1's empty-state capture and TC-3's populated-state capture, when the `[NEW]`-
  flagged demo-narrator walkthrough for J-09 is assembled, then it contains both captures in
  sequence (empty state first, populated state second) inside one walkthrough artifact, both drawn
  from the SAME scoped root, each step legible, and each step's narration matching what its own
  paired screenshot actually shows (no claim unsupported by the image next to it).
- TC-5: given the demo/showcase report and any browser-QA/evidence report produced this iteration,
  when each is read, then both state the absolute filesystem path of the scoped throwaway data
  root used to serve every capture.
- TC-6: given the ambient `apps/backend/.data/` tree's full file listing and each file's SHA-256
  checksum captured at the very start of this iteration (before any leftover process is stopped or
  any new rig is seeded), when the same listing and checksums are captured again after all of this
  iteration's work completes, then both are byte-identical (zero new file, zero modified file, zero
  deleted file) — including no new `topup_runs`-equivalent directory anywhere in the ambient tree.
- TC-7: given `runs/goal-session-desk/journey-scripts/J-01.json` through `J-05.json`, `J-07.json`,
  and `J-08.json`, when each is replayed deterministically against this iteration's scoped backend,
  then every replay reports PASS with 0 failed steps.
- TC-8: given `test_mcp_server.py`'s existing tool-contract assertions, when the suite is run after
  this iteration, then `EXPECTED_TOOLS` still has exactly 17 entries, re-confirming J-06 without a
  browser pass.
- TC-9: given the full backend test suite, when it is run via `cd apps/backend &&
  .venv/bin/python -m pytest tests/ -v`, then it reports at least 1369 passed, 8 skipped, 0 failed,
  and a separate `python -c "from app.config import Config; print(Config().config_fingerprint())"`
  still prints `08e471b10130e1e2`.
- TC-10: given the cumulative repository diff produced by this iteration, when it is compared
  against this iteration's own start-of-run snapshot, then it touches only documentation/evidence/
  showcase artifacts (this iteration's dev handoff, QA/evidence reports and screenshots, the demo
  walkthrough artifact) and shows zero diff on `desk_topup_log.py`, `desk_topup_compute.py`,
  `desk_routes.py`, `desk_screen.py`, `desk_coverage.py`, `tradability.py`, `levels.py`, `bars.py`,
  `apps/frontend/app/desk/page.tsx`, `lib/types.ts`, `lib/api.ts`, `StructureChart.tsx`,
  `PriceChart.tsx`, `config.py`, `meta.py`, and `app/mcp/__init__.py`.
- TC-11: given any scoped-rig process left running from a prior iteration and bound to a port this
  iteration intends to reuse (e.g., iteration 12's own leftover backend, last observed by its
  evaluator at ~78% CPU with no page attached), when this iteration's own environment setup begins,
  then that process (or whatever currently occupies the same port) is confirmed stopped BEFORE this
  iteration's fresh rig is seeded or booted, and this fact is stated in the dev handoff.

## NOTES

- Scoring J-09 `passing` or otherwise, and any consequence for the era's overall verdict, is the
  evaluator's call after real evidence lands — this spec does not presume an outcome. If every
  clause holds, this returns the era to 9/9 journeys `passing`; the evaluator, not this spec,
  decides whether that means `GOAL_ACHIEVED`.
- **Observed at spec-authoring time only (2026-07-28, ~17:13 BST) — do not treat as durable
  state, verify independently:** iteration 12's specific leftover backend (PID `1180202`, the
  ~78%-CPU process its evaluator flagged) was already gone. A DIFFERENT, idling scoped
  backend+frontend pair was live on the same `:8301`/`:3301` ports (PIDs then `1298449` /
  `1298605`+`1298616`, tagged to iteration 12's own dispatch tmpdir), and `GET
  /research/desk/topup/runs` against it returned a genuinely empty `{"runs":[],"latest":null}` —
  i.e. NOT iteration 12's own populated rig. Whatever is actually occupying those ports by the time
  this spec is executed may differ again; per IN SCOPE's first bullet, inventory and stop it, then
  seed this iteration's own fresh, distinctly-named root regardless of what you find.
- Carried, not forced (all optional, none blocking, unrelated to this journey): the run list does
  not yet report a damaged file the way the two sibling lists do (`desk_routes.py:258`); a
  just-finished run can stay hidden until a manual refresh in a narrow timing window
  (`apps/frontend/app/desk/page.tsx:1116-1121`); the run table has no limit yet; the Desk page is
  six stacked sections and long; two screens recorded for the same calendar day cannot be told
  apart by a date-only lookup; keyboard access for the history rows.
- Optional polish, not required to close J-09: the three-checkpoint recording technique has now
  been reproduced ad hoc, from scratch, in both iteration 11's and iteration 12's dispatches (a
  throwaway, uncommitted script each time). If convenient, committing it as a reusable script
  (mirroring `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`'s own precedent) would remove
  that repetition for any future era that needs the same recipe — but this is not this iteration's
  job and must not expand its scope.
- `runs/goal-session-desk/journey-scripts/J-09.json` already exists (recorded 2026-07-28,
  deliberately read-only/goto-only) and asserts whichever backend it replays against is currently
  in the honest-empty state — it is independent of this iteration's own scoped-rig work and is not
  part of the required regression set (J-09 is this iteration's target, not yet `passing`). If any
  lane touches it, disclose per the iter-8 lesson.
