# Goal Iteration 7 — Fresh-server re-capture of J-46/J-41 + user-facing thesis resolve (J-50)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 7
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-41, J-46, J-50
- **Required-still-passing journeys:** J-01, J-02, J-04, J-06, J-07, J-08, J-17, J-19, J-24, J-38, J-39, J-40, J-42, J-43, J-44, J-45
- **Anti-goal reminders:**
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*"
  - "**No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*" — "Played out" / "Abandon" are journaling record actions on the user's own declared thesis, never order actions.

## GOAL

The user can honestly close out their own thesis — **Played out** or **Abandon** — from the thesis strip (recorded with logical + wall timestamps, system-owned resolutions protected), and the two stale-server verdict captures (J-46 failed-move-fade confirming during absorption; J-41 statements reading violated on an adverse tape) are re-proven in real pixels against a verified-fresh backend.

## BACKGROUND

Iter-6 flipped J-40/J-42/J-43/J-45 to passing but its browser run executed against a STALE uvicorn (started 22:07, before the 23:15 on-disk fixes): J-46 confirmed at buyer_control instead of during bid_absorption, and J-41's progress statement read "met" on an adverse tape. The evaluator independently proved both are server-staleness, not code defects — the fixes are on disk, reviewed PASS, coherence PASS, and unit-proven (369 passed / 1 skipped). Its binding next step: re-capture both against a restarted, canary-verified backend, then advance one feature journey. Per goal.md build order and readiness, that feature is **J-50 (user-facing resolve)** — the journal store's terminal-status path, `invalidated` auto-resolve, and `expired(reason)` already work (proven in iter-6 pixels); only `POST /research/thesis/{id}/resolve` and the strip's two controls are missing. J-48 (chart geometry) was considered but deferred: its acceptance includes entry/confirmation marks that depend on action marks (J-52, unbuilt), so it cannot fully pass yet.

**Binding lessons applied (from session lessons.md):** mandatory pre-capture server-freshness canary; capture verdict states at the asserted moment BEFORE sim teardown; scroll-into-view/full-page on every below-the-fold capture; diff the executed browser test list against this spec's full matrix; `NEXT_DIST_DIR=.next-qa` — never `npm run build` against the live dev server's shared `.next`; `store.py` schema changes need versioned migrations (none are planned here — the `theses.status` column and resolution-event append path already exist).

## IN SCOPE

### Backend
- [ ] `POST /research/thesis/{id}/resolve` with body `{resolution: "played_out" | "abandoned"}` ONLY:
  - 404 unknown thesis id; 409 if the thesis is already resolved (any terminal status);
  - **422 if `invalidated` or `expired` is requested** — those resolutions are system-owned;
  - **`abandoned` is refused (409 or 422 with an explicit message) when the thesis carries an entry mark** (no entry-mark UI exists yet — enforce at the API/store level, proven by a unit test with a directly-inserted action row);
  - on success: sets the terminal status via the existing single-writer journal path, **appends** a final timeline event recording the resolution with logical + wall timestamps (append-only — never edits prior events), detaches/stops verdict evaluation for that thesis (no verdict events appended after resolution), and returns the resolved projection.
- [ ] After resolution, `GET /research/thesis/active?ticker=` returns `thesis: null` (and the WS `thesis` key matches verbatim — row 15 parity holds), so a new declaration on the same ticker succeeds (no 409).
- [ ] `GET /research/journal/{id}` (existing endpoint, row 16/19 owner) serves the resolved record: terminal status, resolution timestamps, full frozen timeline.
- [ ] NO grading/execution-check computation yet (J-54/J-56 scope) — but route the resolution through one function so grades can later be computed "once here" per Data Contract row 19 without a second path.

### Frontend (if applicable)
- [ ] `ThesisStrip.tsx`: on an ACTIVE thesis, two controls — **Played out** and **Abandon** — calling the resolve endpoint; on success the strip returns to the declare affordance (per goal.md J-50). System-owned terminal treatments (invalidated banner) are unchanged.
- [ ] Error handling: a 409/422 from resolve surfaces an explicit inline message (no swallowed failure, no dead click).
- [ ] Copy stays descriptive and thesis-attributed ("Resolved — played out", etc.); no imperative or predictive wording.

### New user-facing capability
The user can close their own thesis honestly from the strip: mark it played out or abandon it; the record is journaled with timestamps and the strip frees up for the next declaration. System-owned outcomes (`invalidated`, `expired`) remain untouchable by the user.

### New information displayed
Resolution status + resolution timestamps on the resolved thesis record (read back via `GET /research/journal/{id}`); inline confirmation/error feedback on the strip when resolving.

### New user actions
"Played out" and "Abandon" buttons on the active thesis strip.

### UI surface changes
Thesis strip only (cockpit `/`): two resolve controls while a thesis is active; strip returns to the declare affordance after a user resolution. No new pages, no nav changes.

### Product surface delta
The thesis lifecycle is now closed end-to-end in the UI: declare → verdicts → (auto: invalidated/expired | user: played out/abandoned) → redeclare. This unblocks review/journal work (J-55–J-57) which needs resolved theses to exist.

### Blueprint conformance
No new surfaces. The resolve controls live on the `/` thesis strip — the registered canonical home for J-50 in the blueprint's Information Architecture ("J-38–J-46, J-49, J-50, J-52, J-53 … `/` thesis strip / Cockpit"). Nav untouched.

### Data-contract additions
None (no new computed value). The resolution is recorded by the already-registered row 19 owner (`POST /research/thesis/{id}/resolve`), its timeline entry is an appended row-16 event, and it is served by the registered endpoints (`GET /research/journal/{id}`, row 15 projection). A clarifying note has been added to row 19 in `blueprint.md` (additive; no reapproval needed): user resolutions are `played_out | abandoned` only; system owns `invalidated`/`expired` (422); 409 on already-resolved; entry-marked refuses abandon.

## OUT OF SCOPE

- Grading (outcome × process), execution checks, mistake tags — J-54/J-56/J-57; only keep the resolve path shaped so they can be computed there later.
- `GET /research/journal` LIST endpoint and the `/journal` page — J-55 scope; J-50's "journal row appears" clause is verified via the existing `GET /research/journal/{id}`.
- Action marks (entry/exit) — J-52; the entry-marked-refuses-abandon guard is unit-proven only.
- Thesis geometry on the chart — J-48 (next candidate, after action marks or with the entry-mark clause explicitly split).
- Excursions, analytics, studies, hints, checklist/stance — later layers; cues (J-63–J-67) remain gated on evidence (J-58–J-62).
- Any engine/classifier/provider/store-schema change. No schema migration is expected; if one becomes unavoidable, STOP and surface it (versioned-migration lesson).

## DEFINITION OF DONE

- [ ] **Server-freshness canary passed BEFORE any capture** (see Testing Requirements) — captures from an unverified server are invalid evidence.
- [ ] J-46 passes via browser-qa-agent: CONFIRMING **during** the SIM-REVERSAL bid_absorption phase, and still confirming through the buyer_control reclaim.
- [ ] J-41 passes via browser-qa-agent: REJECTING with evidence on SIM-SELLER, and the "making progress in your direction" statement reads **violated/not-met** on the adverse tape.
- [ ] J-50 passes via browser-qa-agent: played_out + abandoned recorded with logical + wall timestamps; expired(stream_closed) leg re-shown; strip returns to declare affordance; redeclare succeeds.
- [ ] Required-still-passing journeys remain green (verdict suite J-38–J-40/J-42–J-45 and core cockpit J-01/J-02/J-04/J-06/J-07/J-08/J-17/J-19/J-24).
- [ ] No anti-goal violation introduced (journal integrity: resolution is an APPENDED event + status flip — no edit/delete of prior rows; repository still exposes no update/delete of verdict events).
- [ ] Unit tests pass; no regressions (observer-equivalence suite stays green).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-7-dev.md`.

## TESTING REQUIREMENTS

- **BINDING precondition (applies to EVERY browser capture in this iteration):**
  1. The QA backend MUST be (re)started AFTER dev completes — never reuse a uvicorn started earlier.
  2. BEFORE any capture, verify the running server's code identity with a cheap canary: `GET /research/taxonomy` MUST show `failed_move_fade` statement 1 with `states_long=["bid_absorption"]` (the iter-6 patched template). Record the canary response in the QA report. If the canary fails, restart and re-verify — do not capture.
  3. Frontend QA build uses `NEXT_DIST_DIR=.next-qa`; never `npm run build` against the live dev server's shared `.next`.
  4. Capture verdict states at the asserted moment (use Pause to freeze) BEFORE sim scenario teardown, with the thesis strip visibly in-frame (scroll-into-view or full-page screenshot).
  5. Diff the executed browser test list against this matrix before writing the report — every row below must appear.
- Browser (full matrix):
  - **UT-J-46-A** — watch `SIM-REVERSAL`; during its absorption phase declare **failed_move_fade / long** (level just above the absorbed price, invalidation below); capture CONFIRMING **while the tape state panel reads Bid Absorption**, evidence citing the absorbed downside break.
  - **UT-J-46-B** — same thesis: capture still-CONFIRMING during the buyer_control reclaim phase (never rejecting; rejecting would require seller_control follow-through, which this scenario never produces).
  - **UT-J-41** — watch `SIM-SELLER`; declare **trend_continuation / long**, invalidation far below; capture REJECTING with plain-language evidence (seller control / downward impact) AND the expected-behaviour statements reading violated/not-met (the direction-aware statement fix); thesis stays active (rejecting is a judgement, not a resolution).
  - **UT-J-50-A** — on a confirming `SIM-BUYER` trend_continuation/long thesis, click **Played out**: strip returns to the declare affordance; `GET /research/journal/{id}` shows status `played_out` with logical + wall resolution timestamps and the resolution event appended to the timeline.
  - **UT-J-50-B** — declare again on the same watch; click **Abandon**: resolves `abandoned`, same record checks; redeclare then succeeds (no 409).
  - **UT-J-50-C** — declare again (no entry mark) and let the bounded sim stream end: auto-resolves `expired(stream_closed)` with the final verdict frozen — never deleted, never upgraded to a user resolution.
  - **UT-J-50-D (API sub-cases, REST probes recorded in the report)** — `{resolution: "invalidated"}` → 422 explicit message; `{resolution: "expired"}` → 422; resolve an already-resolved thesis → 409; unknown id → 404.
- Unit/integration:
  - Resolve happy paths (`played_out`, `abandoned`): status flip + appended timeline event with both timestamps; prior verdict events byte-identical.
  - 422 system-owned resolutions; 409 already-resolved; 404 unknown id.
  - Entry-marked thesis refuses `abandoned` (inject an action row directly via the store; no UI exists yet).
  - No verdict events are appended after resolution (monitor detach), and `thesis/active` returns null / WS `thesis` key parity after resolution.
  - Redeclare after resolution succeeds (active-thesis uniqueness frees up).
  - Existing observer-equivalence and verdict-engine suites stay green (369/1 baseline).
- Error cases: malformed/unknown `resolution` enum → 422 with explicit message; resolve race (double-click) yields one resolution + one 409, never a duplicated timeline event.

## NOTES

- Evaluator (iter-6) verdict CONTINUE, depth lean — this spec follows its mandated step 1 (fresh-server re-capture with the taxonomy canary) and step 2 (advance J-50, chosen over J-48 for readiness: J-48's entry-mark clause depends on J-52).
- J-46/J-41 need NO code changes — the fixes are already on disk and unit-proven; their target status flips on clean pixels alone. If the re-capture again shows the pre-fix behaviour against a canary-verified fresh server, that is a REAL code defect — report it honestly, do not retry into a green.
- The "journal row appearing immediately" clause of J-50 is verified via `GET /research/journal/{id}` REST reads recorded in the QA report; the `/journal` page itself is J-55 scope. The entry-marked-no-Abandon UI clause is likewise deferred to J-52 (API guard unit-proven now).
- Carry-forward for the harness operator (not this iteration's scope): the engine halts at `qa_complete` for FULL iterations (audit/closure don't run) — open since iter-4/5. This lean cycle sidesteps it; it must be fixed before the next FULL iteration is dispatched.
- Blueprint: row 19 note clarified (additive); no nav change; no reapproval requested.
