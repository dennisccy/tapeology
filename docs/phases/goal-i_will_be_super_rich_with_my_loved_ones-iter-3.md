# Goal Iteration 3 — Clear the browser-verification debt: prove J-38/J-39 in the browser (QA harness repaired)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 3
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-38, J-39
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-17, J-19, J-21, J-24
- **Anti-goal reminders:**
  - "**Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*"
  - "**No silent dead-clicks.** Pressing Watch MUST always produce a visible UI change within ~1 second — a pending/\"connecting\" state, streaming data, an empty-state, an explicit error, or an inline validation message. The UI MUST NOT silently remain on the idle/previous screen, MUST NOT leave \"Connecting…\" running with no resolution, and MUST NOT swallow a failure (no empty `catch`, no unawaited promise that drops an error, no unbounded external wait). A reproducible silent no-op, an infinite connecting spinner, or a swallowed Watch error is a veto on GOAL_ACHIEVED. *(critical)*" (the same discipline applies to the thesis-declare submit this iteration verifies)
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*"

## GOAL

The user-facing half of thesis declaration — the cockpit thesis strip with its taxonomy-driven declare form, inline honest validation, and live ACTIVE display — is demonstrated working in a real browser with screenshot evidence, flipping J-38 and J-39 from partial to passing, on a QA harness repaired so browser evidence can never silently vanish again.

## BACKGROUND

Iter-2 delivered the entire J-38/J-39 backend (independently re-verified by the evaluator: 45 research + equivalence tests pass, full suite green, the 404/409/422 matrix proven live, REST == WS projection) — but **zero browser evidence**: the frontend dev server 500'd on a stale/corrupt `.next` (a `next build` ran against the live dev server's shared dist dir — the exact documented MEMORY/lessons failure mode), all 17 browser tests and the demo were silently SKIPPED, and the QA report still read PASS. The evaluator's iter-2 mandate is explicit: iter-3 is a **LEAN, verification-first** iteration — repair the harness, re-run the browser legs, flip J-38/J-39 on green, and do NOT start the verdict-transition engine (J-40–J-46) on top of unverified UI surface.

Lessons applied (from `lessons.md`, all three entries match this iteration):
- **iter-2:** never run `npm run build` against the live dev server's shared `.next` — `next.config.mjs` already honors `NEXT_DIST_DIR`, so any mid-pipeline type-check build MUST use `NEXT_DIST_DIR=.next-qa` (or be deferred until after browser tests), and the dev server MUST be re-probed for HTTP 200 **after** any build. An all-SKIP browser report counts as "frontend unverified" — target UI journeys cannot flip on it; browser-qa MUST hard-flag (FAIL, not soft-SKIP) a dead frontend because this iteration's targets are UI journeys.
- **iter-0:** kill the frontend dev server by port (`fuser -k <port>/tcp`), never `pkill -f "next dev"` (the reloader child survives); REST absence/error probes need the server demonstrably up; recount results from the table, not the summary line.
- **iter-1:** prefer event-log / REST-probe assertions over single state-panel screenshots for sequence claims in the spot checks; SIM-BIDABS's absorption state is persistent (not a transient phase), so the J-38 screenshots are safe.

## IN SCOPE

### Backend

- [ ] **None.** The backend is untouched this iteration. Any backend diff beyond zero is out of scope (the iter-2 backend is the verified foundation being surfaced).

### Frontend

- [ ] **Repair the dev-server environment (not a committed diff):** remove the stale/corrupt `apps/frontend/.next` and restart the dev server via the standard harness (`scripts/start-frontend.sh` / browser-qa harness ports); verify the cockpit serves HTTP 200 before any browser test runs.
- [ ] **Gitignore hardening:** extend `.gitignore` so isolated build dirs (`.next-qa`, i.e. a `.next*` pattern alongside the existing `.next` entry) can never be staged — today only `.next` exactly is ignored.
- [ ] **Coherence advisory cleanup (iter-2 coherence.md):** remove the unused `fetchActiveThesis` export from `apps/frontend/lib/api.ts` (the strip reads the WS `thesis` key only; the canonical REST read `GET /research/thesis/active` is probed by QA directly against the endpoint, per J-38 step 3). One read path per contract value — no parallel UI-layer REST fetch is to be added.
- [ ] **Defect fixes only if browser QA exposes one** in the J-38/J-39 UI legs (strip rendering, declare form, inline 422/409 messages, live statement statuses, no-reload behavior): fix within the lean retry loop, scoped to `ThesisStrip.tsx` / `app/page.tsx` / `lib/api.ts`. No restyling, no refactors, no new surface.

### New user-facing capability
None new — this iteration **proves** the iter-2 capability (declare a thesis and see it judged live, with honest rejection of incoherent input) in a real browser. That capability is only now considered delivered to users.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None (hygiene-only diffs: `.gitignore`, removal of one unused export).

### Product surface delta
Confidence, not surface: the thesis strip — the product's first decision-support surface — goes from "built but never seen rendering" to "demonstrated working with screenshot evidence", unblocking the verdict-transition engine next iteration.

### Blueprint conformance
No new surfaces. All verified surfaces live at their registered home — **Cockpit (`/`) thesis strip** (blueprint IA row "J-38–J-46, J-49, J-50, J-52, J-53 → `/` thesis strip"). No nav-skeleton change; no reapproval needed.

### Data-contract additions
None. This iteration *verifies* registered rows browser-side: **15** (thesis projection — strip + WS `thesis` key + REST `…/thesis/active` verbatim-equal), **24** (taxonomy-driven form labels), **26** (source + `data_feed` stamp shown on the strip). Removing the unused `fetchActiveThesis` export *enforces* row 15's single read path at the UI layer. Never introduce a second way to compute or fetch any registered value.

## OUT OF SCOPE

- The verdict-transition engine (`confirming / weakening / rejecting / invalidated`, per-setup dwell, `rule_first_true`) — J-40–J-46, planned next iteration at FULL depth once this browser debt is cleared. The verdict stays honestly `pending` everywhere this iteration.
- `/journal` and `/studies` pages, top-bar nav links (Journal · Studies).
- Entry risk flags (J-49), resolve endpoint/controls (J-50), action marks (J-52), management stance (J-53), thesis chart geometry (J-48).
- Cue layer (J-63–J-67) — gated behind the evidence layer per the binding build order.
- Any backend, engine, classifier, config, or journal-store change.
- Any framework/harness script edits outside this repo's app + `.gitignore` (the build-isolation mechanism already exists in `next.config.mjs`; the fix here is procedural discipline plus environment repair).

## DEFINITION OF DONE

- [ ] The frontend dev server serves the cockpit with HTTP 200 at browser-QA start **and is re-verified 200 after any build step run during the pipeline** (a dead frontend is a FAIL, never a SKIP, for this iteration).
- [ ] Target journeys **J-38** and **J-39** pass via browser-qa-agent with per-journey screenshot evidence in a **non-empty** evidence directory.
- [ ] J-68's strip-idle clause is browser-verified (no thesis ⇒ the strip idles as a single declare affordance and the cockpit is otherwise unchanged) — recorded as J-68 progress; J-68 itself stays partial until its "J-01–J-37 all green" clause is met.
- [ ] Required-still-passing journeys re-verified green: J-01–J-09, J-17, J-19, J-21, J-24.
- [ ] Backend suite still green (iter-2 baseline: 332 passed / 1 skipped; zero regressions).
- [ ] No anti-goal violation introduced.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-3-dev.md` (states exactly what environment repair was performed, the post-build 200 re-probe result, and the committed diff — expected to be tiny).

## TESTING REQUIREMENTS

- Browser (the substance of this iteration — all on the harness ports, frontend probed 200 first):
  - **J-38 (full journey):** watch `SIM-BIDABS` (Simulated); in the thesis strip declare **absorption_reversal / long** with an invalidation below the current last; assert the strip shows the ACTIVE thesis — setup, direction, invalidation in mono — with the frozen expected-behaviour statements each rendering a live status (met / not-yet / violated), the verdict badge honestly **pending** (slate), and the bound source + `data_feed: sim` stamp; in a new tab open `GET /research/thesis/active?ticker=SIM-BIDABS` and assert the REST projection equals the WS frame's `thesis` key verbatim; assert declaration required **no page reload**.
  - **J-39 (full journey):** wrong-side invalidation (long with invalidation above last) ⇒ inline validation message from the 422, form values preserved, **nothing created** (active projection still `null` via REST probe); `level_break` without a level ⇒ 422 inline message; `absorption_reversal` with a level ⇒ 422 inline message; a second declare on the same ticker ⇒ 409 with an explicit message; unwatched ticker ⇒ explicit 404 (REST probe with the server demonstrably up). Input is never silently coerced, auto-corrected, or partially saved.
  - **J-68 strip-idle clause:** with no thesis declared, the strip is a single one-line declare affordance and every pre-existing cockpit panel behaves identically.
  - **Required-still-passing spot checks:** J-01–J-09 sim flows, J-17 (chart + markers + bar-size selector), J-19 (pause/resume), J-21 (Watch acknowledged ≤ ~1 s), J-24 (invalid Watch input inline feedback). Prefer event-log / REST assertions for sequence claims (iter-1 lesson).
  - **Harness rules (binding):** any `npm run build` during the pipeline uses `NEXT_DIST_DIR=.next-qa` or is deferred until after browser tests; the dev server is killed by port (`fuser -k`), never by process-name pkill; the dev server is re-probed 200 after any build.
- Unit/integration: re-run the full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`) — must match the iter-2 green baseline; no new backend tests required (no backend change). Frontend type-check build runs only under `NEXT_DIST_DIR=.next-qa`.
- Error cases: the J-39 matrix above is the error-case coverage; additionally assert nothing was persisted after each rejected declare (active projection unchanged).

## NOTES

- **Evaluator mandate (iter-2 eval):** "Do not build the verdict engine on top of unverified UI surface." This iteration exists to clear that debt; on green, the evaluator can flip J-38/J-39 and the recommended iter-4 is the verdict-transition engine (J-40–J-46) at FULL depth (prerequisites — SIM-SHIFT/SIM-REVERSAL, thesis layer, monitor seam — are all in place).
- **Escalation flag:** if browser QA again produces no evidence (harness failure repeats), the evaluator should ESCALATE so iter-4 runs FULL with harness reliability as primary scope — a second consecutive evidence-free iteration must not be absorbed silently.
- The expected committed diff is tiny (`.gitignore` + one removed unused export + any QA-found strip defect fix). The value of this iteration is evidence, not code; the developer step is near-no-op by design.
- SIM-BIDABS warm-up resolves within seconds (accelerated sim clock); its absorption state persists, so screenshots are stable. Budget extra time only for the spot-check scenarios, not J-38/J-39.
