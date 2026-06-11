# Goal Iteration 9 — A thesis survives interruption only with a position (J-47), plus the mandatory favorable-dominant unit pins

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 9
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-47
- **Required-still-passing journeys:** J-01, J-02, J-08, J-19, J-38, J-39, J-40, J-41, J-42, J-43, J-44, J-45, J-46, J-50, J-52
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*
  - **Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis MUST never be evaluated against a different source than it was declared on; analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label. *(critical)*
  - **The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*
  - **Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*
  - **No profitability or edge claims.** No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure. *(critical)*

## GOAL

A user who has marked a real entry on a thesis can stop (or lose) the watch without the system orphaning their position: the thesis survives as honestly **active-but-not-evaluated**, re-attaches with an explicit `watch_restarted` gap event when the matching source is re-watched, while an unmarked thesis auto-expires `expired(watch_stopped)` — and a watch of a different source is never evaluated against it.

## BACKGROUND

The iter-8 evaluator's primary recommendation is J-47, now fully unblocked by J-52 (entry marks exist end-to-end: `POST /research/thesis/{id}/action`, persisted `spread_at_mark`, `marks_projection`). Today the lifecycle is dishonest to a position-holder: `ResearchMonitor.on_status('closed'|'failed')` → `_expire_active()` expires **every** active thesis (entry-marked included), `ResearchRegistry.startup_sweep()` expires all stale actives on boot, and a re-watch builds a fresh monitor that knows nothing of a surviving thesis. goal.md capability 24 demands the opposite: "Stream end / stop / failure auto-resolves an active thesis `expired(reason)` — UNLESS it carries an entry mark (a real position must never be orphaned)". This iteration is lean (the evaluator mandates lean while the FULL-pipeline harness defect — engine halts at `qa_complete` — remains open) and additionally carries the iter-8 reviewer's MINOR-but-mandatory test-completeness task: unit-pin the both-material **favorable-dominant** `directional_impact` quadrant in both directions, which iter-8 proved only in pixels.

**Binding lesson (numeric truth anchors):** when this spec names numeric values for `apps/backend/app/research/` rule tests, the test parameters MUST actually use those values — the reviewer/evaluator will diff them.

## IN SCOPE

### Backend

- [ ] **Entry-marked theses survive stop/failure** (`apps/backend/app/research/monitor.py`): in the `on_status` → `_expire_active` path, an active thesis that carries an entry mark (the store already exposes the `actions WHERE kind='entry'` check) is NOT expired on `closed`/`failed`. It detaches as **active-but-not-evaluated**: it stays `active` in the store, NO verdict events are appended while unwatched, and the projection says so explicitly. An unmarked active thesis keeps auto-expiring, with the reason distinguishing user stop (**`watch_stopped`**) from stream exhaustion (**`stream_closed`** — J-50's already-verified leg MUST NOT regress) and feed failure (existing failure reason).
- [ ] **Projection survives the watch** (`apps/backend/app/research/routes.py` / `monitor.py`): `GET /research/thesis/active?ticker=` for an unwatched ticker with a surviving entry-marked thesis returns the thesis projection from the persisted record via the **same projection path** (one builder — extract/reuse, never a second computation), flagged with an explicit not-evaluated `monitor_status` and the plain-language notice ("not currently evaluated — re-watch this source to resume", taxonomy/display copy backend-owned per Data Contract row 24). `thesis: null` remains the answer when nothing survives.
- [ ] **Re-attach on matching source** (`apps/backend/app/research/routes.py::ResearchRegistry.on_engine_created` + `monitor.py`): when a new watch's source identity (the snapshot's scenario descriptor — known at/after the first snapshot, NOT assumed at engine construction) **equals the thesis's `bound_source`**, the fresh monitor adopts the surviving thesis, appends exactly one **`watch_restarted` gap event** to the append-only timeline (an appended row via the existing single writer; the timeline is never edited or backfilled), and resumes evaluation from post-restart evidence only.
- [ ] **Mismatched source is never evaluated** : if the new watch's source identity differs from `bound_source` (e.g. a different sim scenario, or live vs historical of the same symbol), the monitor does NOT adopt the thesis; no verdicts are appended; the active-thesis projection carries an explicit bound-source notice naming the declared source. Proven by unit test (the cross-source leg is unit-proven per goal.md J-47).
- [ ] **Startup sweep exempts entry-marked theses** (`apps/backend/app/research/store.py::expire_stale_actives`): a backend restart no longer expires a surviving entry-marked active thesis (this is also J-51's "entry-marked survives restart" leg, pre-built here; J-51 itself stays untargeted until `/journal` exists). Unmarked stale actives keep expiring with an explicit interruption reason.
- [ ] **Mandatory regression-hardening (iter-8 carry):** in `tests/test_research_monitor.py`, pin the both-material **favorable-dominant** dominance quadrant in BOTH directions with EXACTLY these parameters: **long — `buy_price_impact = +0.40` AND `sell_price_impact = -0.14` → `met`**; **short — `sell_price_impact = -0.40` AND `buy_price_impact = +0.14` → `met`**. The test parameters must literally be these values (binding lesson). No production-code change is expected for this task; if any statement-semantics production change turns out to be required, STOP and flag it — that would trigger the four-quadrant pixel-proof obligation and belongs in its own iteration.

### Frontend (if applicable)

- [ ] **Thesis strip honest not-evaluated state** (`apps/frontend/components/ThesisStrip.tsx` + `apps/frontend/app/page.tsx`): after Stop, the strip area for the stopped ticker remains rendered (within the existing `/` cockpit surface) showing the surviving entry-marked thesis: setup/direction/invalidation, recorded marks, and the backend-served notice "not currently evaluated — re-watch this source to resume" with the bound source. Rendered verbatim from the row-15 projection — no client-side lifecycle inference.
- [ ] **Re-attach renders live again**: on re-watching the matching source, the strip returns to normal live evaluation (verdict chip + evidence resume); the gap event is visible in the journal timeline (REST).
- [ ] **Mismatched-source notice** rendered verbatim when the projection carries it.

### New user-facing capability
A trader holding a marked position can stop the watch (or suffer a restart) without losing the thesis: the system honestly shows it as not-currently-evaluated and resumes judging it — with an explicit, recorded gap — only when the same source is watched again.

### New information displayed
The "active-but-not-evaluated" thesis state with its plain-language notice and bound source; the `watch_restarted` gap event in the journal timeline; the explicit `expired(watch_stopped)` reason on unmarked interrupted theses; the mismatched-source notice.

### New user actions
None (no new buttons/forms — this iteration is lifecycle honesty for existing flows; Stop/Watch/declare/mark are unchanged controls).

### UI surface changes
Thesis strip only (existing `/` cockpit surface): a not-evaluated presentation variant + notice line. No new pages, no nav change.

### Product surface delta
The thesis lifecycle becomes safe for real positions across interruptions — the precondition for honest holding-period support (J-53) and restart-proof journaling (J-51).

### Blueprint conformance
No new surfaces. J-47's registered home is already `/` thesis strip + `/journal` row (Cockpit / Journal) in `blueprint.md`; the journal-row leg is verified via REST `GET /research/journal/{id}` per the session's established convention (the `/journal` page is J-55's scope).

### Data-contract additions
No new contract rows. Two **additive notes** registered in `blueprint.md` (done by the decomposer alongside this spec): row 15 — the surviving entry-marked thesis is served by the SAME projection path/endpoint with a not-evaluated `monitor_status` + bound-source notice (never a second computation path); row 16 — `watch_restarted` gap events are appended timeline rows from the same single writer. Never compute lifecycle state client-side; never serve the surviving thesis from a second endpoint.

## OUT OF SCOPE

- The `/journal` page, journal list endpoint, review flow, grades, mistake tags (J-55–J-57) — J-51's full verification waits for them.
- Thesis geometry on the chart (J-48) — next candidate; its deferred J-45/J-52 chart clauses stay tracked there.
- Entry risk flags (J-49), management stance / distance-to-invalidation / open R (J-53), execution checks (J-54), excursions (J-58+), studies, and the entire cue layer (J-63–J-67 — binding build order: cues strictly after evidence J-58–J-62).
- New control behavior while not-evaluated (e.g. mark-exit prefill rules with no live last): existing controls must not crash, but no new unwatched-state interactions are required or to be invented. Resolution stays store-owned and unchanged.
- Any engine/classifier/feature/provider file change (research layer is read-only over the engine).
- Schema changes are NOT expected (gap events are appended `verdict_events` rows; entry-mark presence is already queryable). IF the developer finds a schema change unavoidable, it MUST ship as a versioned v3→v4 migration proven against a committed old-schema fixture + persistent-DB reopen test (iter-4 lesson, re-proven iter-8) — otherwise stop and flag.

## DEFINITION OF DONE

- [ ] Target journey J-47 passes via browser-qa-agent (sim legs in pixels; cross-source leg unit-proven per goal.md)
- [ ] Required-still-passing journeys remain green — in particular J-50's `expired(stream_closed)` leg and abandon flows, J-52's marks display, and J-42/J-41 verdict semantics (monitor.py is touched again)
- [ ] The favorable-dominant dominance pins exist with the exact named parameters (long +0.40/−0.14 → met; short −0.40/+0.14 → met), both passing
- [ ] No anti-goal violation introduced (journal integrity: timeline append-only, gap events explicit, no backfill; source honesty: never evaluated against a mismatched source)
- [ ] Unit tests pass; no regressions (full backend suite green; observer-equivalence suite green)
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-9-dev.md`

## TESTING REQUIREMENTS

- Browser (QA harness; sim only, no credentials):
  - **UT-J-47-A (survive stop):** watch `SIM-BUYER`, declare trend_continuation/long (invalidation far below), **mark an entry** while confirming, then Stop. The strip shows the surviving thesis with the not-evaluated notice + bound source; REST `GET /research/thesis/active?ticker=SIM-BUYER` returns it with the not-evaluated `monitor_status`; REST journal detail shows NO verdict events appended after the stop.
  - **UT-J-47-B (re-attach + gap event):** re-watch `SIM-BUYER`; the strip resumes live evaluation; REST `GET /research/journal/{id}` timeline shows exactly one `watch_restarted` gap event at the re-attach, then post-restart verdicts only (never interpolated history).
  - **UT-J-47-C (unmarked expires watch_stopped):** declare a thesis WITHOUT an entry mark, Stop the watch; the thesis auto-resolves `expired` with the explicit `watch_stopped` reason (REST journal readback; strip returns to the declare affordance on re-watch).
  - **Non-regression re-checks:** J-50's stream-end leg (`expired(stream_closed)` unchanged when a bounded sim stream ends on an unmarked thesis) via REST; one J-42 confirming strip capture as the monitor-touched canary; J-52's recorded-marks + realized-R line still rendered in the UT-J-47-A/B captures.
  - QA discipline (binding lessons): restart the QA backend after dev and verify the server-freshness canary (server start time > newest patched-file mtime) BEFORE any capture; capture verdict/lifecycle states at the asserted moment using Pause before sim teardown; scroll-into-view/full-page every below-the-fold capture; diff the executed browser-test list against this spec's matrix (all items above, none omitted); never `npm run build` against the live dev server's shared `.next` (use `NEXT_DIST_DIR=.next-qa`).
- Unit/integration (`apps/backend/tests/`):
  - Entry-marked active thesis survives `on_status('closed')` and `on_status('failed')`: stays `active`, zero verdict events appended afterwards.
  - Unmarked active thesis expires with reason `watch_stopped` on user stop vs `stream_closed` on stream exhaustion (both reasons asserted distinctly; existing J-50 expiry tests stay green).
  - Re-attach on matching `bound_source`: monitor adopts, appends exactly ONE `watch_restarted` gap event (append-only — no edits/backfill), evaluation resumes; idempotence (a second snapshot does not append a second gap event).
  - **Cross-source leg (REQUIRED unit test per goal.md):** a watch whose source identity ≠ `bound_source` does NOT adopt the thesis, appends NO verdicts, and the projection carries the explicit bound-source notice.
  - `expire_stale_actives` (startup sweep) exempts entry-marked actives and still expires unmarked ones with an explicit reason.
  - Active-thesis projection for an unwatched ticker is served by the same projection builder (one code path) with the not-evaluated status; `thesis: null` when nothing survives.
  - **Mandatory dominance pins (exact parameters, both directions):** long `buy_price_impact=+0.40`, `sell_price_impact=-0.14` → `met`; short `sell_price_impact=-0.40`, `buy_price_impact=+0.14` → `met`.
  - Observer-equivalence suite still green (research layer read-only over the engine).
- Error cases:
  - Re-attach never fires on a mismatched source (no silent adoption); no verdict event ever carries a timestamp inside the unwatched gap; resolution endpoints' existing 404/409/422 guard matrix unchanged; an entry-marked thesis still refuses `abandoned` (409) including while not-evaluated.

## NOTES

- **Depth is lean and mandatory-lean:** the engine halts at `qa_complete` for FULL iterations (carry-forward harness defect) — audit/closure would not run; lean produced complete evidence in iters 6–8.
- Evaluator basis: iter-8 eval `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/iter-8/eval.md` — primary recommendation J-47 + the mandatory favorable-dominant unit-pin task; coherence verdict iter-8 was COHERENCE-PASS (no consolidation debt).
- Copy register: every new string (not-evaluated notice, mismatched-source notice, `watch_restarted` display copy) is present-tense, descriptive, thesis-attributed; backend-owned via the taxonomy/display-copy seam (Data Contract row 24); never imperative or predictive. "Descriptive only — not trading advice" stays in frame.
- The sim browser environment cannot produce a mismatched source for the same ticker (a sim ticker is bound to its scenario), which is exactly why goal.md makes the cross-source leg unit-proven; do not fake it browser-side.
- J-51 benefit is incidental (sweep exemption + reason honesty); do NOT claim J-51 — it stays failing until the `/journal` page journeys land.
