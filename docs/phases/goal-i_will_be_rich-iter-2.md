# Goal Iteration 2 — Verification-closure: browser-prove the SIM-BUYER cockpit (J-01 / J-02 / J-08)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_rich
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-08
- **Required-still-passing journeys:** none (no journey is green yet — this iteration aims to make J-01/J-02/J-08 the *first* `passing` journeys; the iter-1 backend reads below must not regress)
- **Anti-goal reminders** (verbatim from `docs/goal.md`, the ones this iteration most directly exercises):
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical — J-08 verifies this in the browser)*
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state, never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical — J-02 must show buyer_control gated on positive buy_price_impact, not aggression alone)*
  - **No fabricated data.** On a provider gap/failure the system MUST surface an explicit stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical — screenshots must show real engine values, never placeholder/mocked numbers)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code. *(the two cleanups below MUST NOT introduce or relocate any literal)*
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence. *(the spread cleanup MUST be behavior-preserving — the run-twice-identical test must still pass)*

## GOAL

A user visits `/`, watches `SIM-BUYER`, and sees the full live tape cockpit resolve to **buyer_control** — and this is **proven in a real browser with screenshots**, with the UI's tape state / confidence / features matching the REST endpoints exactly.

## BACKGROUND

Iteration 1 built the complete walking skeleton (provider → engine → price-impact classifier → REST/WS → `/` Next.js cockpit) and **the backend is solidly proven**: 24/24 backend tests pass, live reads show `SIM-BUYER → buyer_control @ 0.863` with positive `buy_price_impact`, and all twelve anti-goals were verified independently. **But the browser half was never verified** — `browser-qa-agent` SKIPPED all 18 UI tests because the managed Next.js dev server returned HTTP 500 from a corrupted `.next` devtools cache (environmental, not an app defect). The only screenshot on disk is the failure shot. So J-01/J-02/J-08 are recorded `partial` (backend half live-verified; in-browser half unproven), **not** `passing`.

Per the iter-1 evaluator and the session lessons ledger, the correct next move is a **verification-closure pass**, **not** advancing to a new scenario (J-03). Everything downstream builds on this UI; it must be browser-green before more scenarios land. This iteration also folds in the two cheap, behavior-preserving cleanups the reviewer + coherence-auditor flagged, while the diff is small.

**Lesson applied (lessons.md, iter-1):** "backend PASS + clean build" is NOT evidence that the UI journeys work; an all-skipped browser run is a hard signal to do a verification-closure iteration. **Precondition for Next.js browser QA:** `rm -rf apps/frontend/.next` and restart the dev server with `NEXT_PUBLIC_API_URL` set **before** driving the browser. Do not let a backend-PASS stand in for browser verification of UI journeys again.

**Why full depth:** the UI has never been rendered through the QA pipeline — the only "live browser" claim so far is the developer's self-report. Browser QA may surface real client→backend defects (WS wiring, CORS, `NEXT_PUBLIC_API_URL` resolution, hydration). Full depth gives any such fix the review/audit loop, on the foundational slice everything else depends on.

## IN SCOPE

### Backend
- [ ] **Cleanup (behavior-preserving):** `apps/backend/app/engine/tape_engine.py:54` — replace the inline `event.ask - event.bid` passed to `self._features.add_quote(...)` with `self._market.spread` (the canonical `MarketState.spread`, already updated by `update_quote(event)` on the preceding line). Keeps the `ask − bid` subtraction in exactly one place. **No behavior change** — `average_spread`'s input value is identical.
- [ ] **Cleanup (dead import):** `apps/backend/app/config.py:11` — drop the unused `field` symbol (`from dataclasses import dataclass, field` → `from dataclasses import dataclass`). Verified unused (`field(` count = 0 in the file).
- [ ] Re-run the full backend suite; all existing tests must remain green (no behavior drift from either cleanup).

### Frontend (reactive only — no new features)
- [ ] Ensure the cockpit renders and updates **in a real browser** against the running backend. The expectation is no code change is needed (iter-1's production build was clean), but **if browser QA surfaces a genuine defect** — client→backend WS URL derivation, CORS, `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_API_BASE` resolution, hydration/SSR mismatch, or an env-wiring bug — fix the minimal root cause. Do **not** add panels, controls, endpoints, or features.

### Environment / QA precondition (not product code)
- [ ] Before driving the browser: `rm -rf apps/frontend/.next`, then start the managed frontend dev server with `NEXT_PUBLIC_API_URL` pointed at the running backend (QA-harness offset port). Confirm the frontend serves HTTP 200 (not 500) before running any UI test.

### New user-facing capability
None new. This iteration makes the **already-built** J-01/J-02/J-08 capability *trustworthy* — actually verified in the browser with evidence — rather than self-reported.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None expected. (Only a minimal fix if a real defect is found — and that would be a correction to existing surfaces, not a new one.)

### Product surface delta
No visible change for the end user beyond any defect fix. The cockpit becomes browser-proven on `SIM-BUYER`: panels render live values and update over WebSocket without a reload, captured in screenshots.

### Blueprint conformance
No new surfaces — everything is on the existing `/` (Watch / tape cockpit) **HOME**, which is the only route in the blueprint. No nav-skeleton change; **no re-approval requested.** The `tape_engine.py:54` cleanup *removes* a duplicate inline `ask − bid`, reinforcing the Data Contract's single producer for `spread` (`MarketState.spread`) — it does not add or move a canonical home.

### Data-contract additions
**None.** No new displayed value is introduced. `spread` keeps its single canonical producer (`MarketState.spread`); the cleanup deletes a redundant inline computation rather than creating a second one. `blueprint.md` is unchanged this iteration (no additive row needed).

## OUT OF SCOPE

- **No new scenarios / journeys.** J-03 (seller_control), J-04/J-05 (absorption pair), J-06 (unclear-chop), J-07 (transition taxonomy), J-09 (stop/re-watch) are **not** built this iteration. Do not drive `SIM-SELLER` / `SIM-BIDABS` / `SIM-ASKABS` / `SIM-CHOP` to their states; do not add `DELETE /watch` UI.
- **Stream-status dot consolidation is deferred.** The coherence WARN advisory (drive the top-bar status dot from the engine's canonical `snapshot.stream_status` instead of the client `connStatus`) belongs to the J-04/J-05 (stale/no-data) or J-09 (teardown) iteration, where `stale`/`closed` are actually exercised. It is **not forgotten** — it MUST be consolidated before those iterations land — but touching it now would be scope creep with no journey to verify it against.
- No new panels, endpoints, features, config keys, or dependencies.
- No refactors beyond the two named cleanups.

## DEFINITION OF DONE

- [ ] **J-01, J-02, J-08 pass via `browser-qa-agent`** on `SIM-BUYER`, each with **≥1 screenshot of the claimed end state** (not a failure shot). Browser QA must actually **RUN**, not SKIP — the frontend serves HTTP 200 and the panels populate.
- [ ] J-01 evidence: every panel renders live numeric values (bid/ask/spread/last with spread = ask − bid; recent-trades with price/size/side; the feature readouts; tape-state + confidence; observations; event log) and values update over WebSocket **without a page reload**.
- [ ] J-02 evidence: tape state settles on **buyer_control** at confidence ≥ the configured threshold; `aggressive_buy_ratio` reads high and `buy_price_impact` reads positive; the event log contains "Tape state changed to buyer_control".
- [ ] J-08 evidence: the UI's tape state, confidence, and feature readouts **match** `GET /tape/SIM-BUYER/state` and `GET /tape/SIM-BUYER/features` for the same ticker (one engine value per metric; no divergence between views).
- [ ] Both cleanups applied; the **full backend suite still passes** (no regression; determinism / SIM-BUYER scenario / price-impact-guard tests green); frontend production build clean.
- [ ] No anti-goal violation introduced; coherence remains WARN-or-better (no new duplicate producer, no new IA home).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_rich-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Browser (the heart of this iteration):**
  - **J-01** — visit `/`, watch `SIM-BUYER`, wait for stream connect; assert all six panels render live values and update over WS without reload. Screenshot the populated cockpit.
  - **J-02** — let it stabilize; assert `buyer_control` + confidence ≥ threshold, `aggressive_buy_ratio` high, `buy_price_impact` positive, and "Tape state changed to buyer_control" in the event log. Screenshot the tape-state panel + event log.
  - **J-08** — compare the UI's state/confidence/features against `GET /tape/SIM-BUYER/state` and `/features` (open in another tab or via the harness); assert exact agreement. Screenshot the UI panel and the REST JSON.
  - Precondition (must be satisfied or the run is invalid): `rm -rf apps/frontend/.next`; dev server up with `NEXT_PUBLIC_API_URL` set; frontend returns HTTP 200.
- **Unit / integration (regression guard for the two cleanups):**
  - Full existing backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`) stays green.
  - Determinism: the run-twice-identical test must still pass after the `tape_engine.py:54` change (proves the spread cleanup is behavior-preserving).
  - SIM-BUYER scenario test still resolves to `buyer_control` with reasonable confidence.
  - Price-impact-guard test (buyer_control requires positive `buy_price_impact`) still passes — do not relax it.
  - No new magic numbers introduced by either cleanup (config remains the single source of tunables).
- **Error cases (must still hold — regression guard):**
  - Unknown-ticker `POST /watch/{ticker}` → 400; read of a not-watched ticker → 404. Neither cleanup may change these.
  - On any provider gap, the snapshot still surfaces an explicit stale/no-data state — never a fabricated read.

## NOTES

- **This is a verification + hardening pass, not a feature delivery.** Its single most important output is real browser evidence (screenshots) that J-01/J-02/J-08 work end-to-end on `SIM-BUYER`. If browser QA passes cleanly with no code change beyond the two cleanups, that is a complete and successful iteration.
- **Treat the never-QA'd UI skeptically.** If browser QA surfaces a real client/WS/env-wiring/hydration defect, that is the *point* of this pass — fix the minimal root cause and let the full review/audit loop cover it. Capture the before/after in the dev handoff.
- **Do not advance to J-03** regardless of any dev-handoff suggestion to do so; the scenario sequence resumes only after J-01/J-02/J-08 are browser-green. After that: J-03 (seller_control) → the price-impact-critical absorption pair J-04/J-05 → J-06/J-07/J-09 (those can likely run lean).
- The deferred coherence advisory (stream-status dot → `snapshot.stream_status`) is recorded in OUT OF SCOPE and must be folded into the J-04/J-05 or J-09 iteration; flagging here so it is not lost.
- Blueprint unchanged this iteration; no `blueprint.reapproval-requested` written (no nav-skeleton change, no new displayed value).
