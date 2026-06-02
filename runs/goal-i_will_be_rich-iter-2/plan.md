# goal-i_will_be_rich-iter-2 Execution Plan

> **Iteration type: verification-closure + two surgical cleanups — NOT a feature delivery.**
> The single most important output is *real browser evidence (screenshots)* that **J-01 / J-02 / J-08**
> work end-to-end on `SIM-BUYER`, with the UI's tape state / confidence / features matching the REST
> endpoints exactly. iter-1's backend is already proven (24/24 tests; live `buyer_control @ 0.863`,
> positive `buy_price_impact`), but browser QA **SKIPPED all 18 UI tests** because the managed Next.js
> dev server returned HTTP 500 from a corrupted `.next` devtools cache. This pass closes that gap.

## What to Build
- **Backend cleanup #1 (behavior-preserving):** `apps/backend/app/engine/tape_engine.py:54` — replace the inline `event.ask - event.bid` passed to `self._features.add_quote(...)` with `self._market.spread` (already updated by `self._market.update_quote(event)` on line 53). Keeps the `ask − bid` subtraction in exactly one place (`MarketState.spread`); the value fed to `average_spread` is identical. **No behavior change.**
- **Backend cleanup #2 (dead import):** `apps/backend/app/config.py:11` — `from dataclasses import dataclass, field` → `from dataclasses import dataclass`. Confirmed: `field` appears only on the import line (zero uses).
- **Re-run the full backend suite (24 tests) — all must stay green.** Determinism (run-twice-identical), SIM-BUYER scenario → `buyer_control`, and the price-impact guard test (buyer_control requires positive `buy_price_impact`) must all still pass. No new magic numbers introduced.
- **Browser-prove J-01 / J-02 / J-08 on `SIM-BUYER` with screenshots** — the heart of this iteration. Browser QA must actually **RUN**, not SKIP.
- **Frontend = reactive-only.** No new features, panels, controls, endpoints, config keys, or dependencies. Expectation is **zero frontend code change** (iter-1 production build was clean and `lib/config.ts` already resolves `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_BASE` correctly). **Only if** browser QA surfaces a *genuine* client→backend defect — WS URL derivation, CORS, env-var resolution, or hydration/SSR mismatch — fix the **minimal root cause** and let the full review/audit loop cover it; capture before/after in the handoff.

## ⚠️ Precondition (the iter-1 trap — must be satisfied or the run is INVALID)
Before driving the browser, the QA/browser stage MUST:
1. `rm -rf apps/frontend/.next`
2. (Re)start the managed frontend dev server with `NEXT_PUBLIC_API_URL` pointed at the **running backend** (QA-harness offset port, e.g. backend `:8650` → frontend `:3650`).
3. **Confirm the frontend serves HTTP 200 (not 500)** before running any UI test.

In iter-1 the QA agent was *not permitted* to restart the shared managed service, so every UI test SKIPPED on the cached HTTP 500. **A backend PASS + clean build is NOT a substitute for a real browser pass** (lessons.md, iter-1). If the frontend cannot be made to serve HTTP 200, the iteration is **not** done — do not record SKIP as success.

## Agents Required
- **developer: yes** — apply the two backend cleanups; run the backend suite; clear `apps/frontend/.next` and re-verify the production build; fix a genuine UI defect **only if** browser QA surfaces one. No new product code.
- **backend-data: yes (minor only)** — two behavior-preserving cleanups; no new data, no schema/contract change.
- **frontend-ux: reactive-only** — no new UI; corrective fix only on a real browser-surfaced defect.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/tape_engine.py` — line 54: `event.ask - event.bid` → `self._market.spread` (single producer for spread; behavior-preserving).
- `apps/backend/app/config.py` — line 11: drop the unused `field` from the `dataclasses` import.
- `docs/handoffs/goal-i_will_be_rich-iter-2-dev.md` — **new** dev handoff (records both cleanups, the browser-QA precondition steps taken, and any defect fix with before/after).
- _(conditional, only if browser QA finds a real defect)_ a single minimal frontend fix, most likely in `apps/frontend/lib/config.ts` (API/WS base resolution) or `apps/frontend/lib/useTapeStream.ts` (WS wiring) — minimal root cause only, preserving existing surfaces.

## UI Evolution (Frontend Present: yes)
- **New user-facing capability:** none. This iteration makes the **already-built** J-01/J-02/J-08 capability *trustworthy* — actually verified in a real browser with screenshot evidence — rather than self-reported.
- **New information displayed:** none.
- **New user actions:** none (no Stop control / `DELETE /watch` this iteration — that is J-09).
- **UI surface changes:** none expected. Only a correction to an *existing* surface if a real defect is found — never a new surface.
- **Navigation changes:** none. Everything stays on the single `/` (Watch / tape cockpit) **HOME** — the only route in the approved blueprint. **No nav-skeleton change; no blueprint re-approval requested.**

## Visual Requirements (Frontend Present: yes)
- **Component patterns:** none added — the existing hand-built panels (`QuotePanel`, `RecentTradesPanel`, `FeaturesPanel`, `TapeStatePanel`, `ObservationsPanel`, `EventLogPanel`, `TopBar`, `IdleState`) must render correctly in-browser. No new components.
- **Layout:** unchanged — responsive panel grid (1-col → 2-col `md` → 3-col `lg`) on the calm dark surface (slate-950). Verify it renders, not redesign it.
- **Key visual effects (verify, don't invent):** load-bearing color semantics — **emerald = buy-side / positive impact, rose = sell-side / negative impact, amber = absorption / unclear**; monospaced numerics for all prices/sizes/ratios; confidence bar + stream-status dot.
- **States to handle:** confirm the existing idle/empty, connecting/warm-up, live, and watch-error states render in-browser (no new states). No "Descriptive only — not trading advice" disclaimer regression.

## Key Test Scenarios
**Browser (the heart of this iteration — each needs ≥1 screenshot of the claimed END state, not a failure shot):**
- **J-01** — visit `/`, watch `SIM-BUYER`, wait for stream connect; assert all six panels render live numeric values (bid/ask/spread/last with **spread = ask − bid**; recent-trades with price/size/side; the feature readouts; tape-state + confidence; observations; event log) and that values **update over WebSocket without a page reload**. Screenshot the populated cockpit.
- **J-02** — let it stabilize; assert tape state settles on **buyer_control** at confidence ≥ the configured threshold, `aggressive_buy_ratio` reads high, `buy_price_impact` reads **positive**, and the event log contains **"Tape state changed to buyer_control"**. Screenshot the tape-state panel + event log.
- **J-08** — compare the UI's tape state / confidence / feature readouts against `GET /tape/SIM-BUYER/state` and `GET /tape/SIM-BUYER/features` for the same ticker; assert **exact agreement** (one engine value per metric; no divergence between views). Screenshot the UI panel and the REST JSON.

**Regression guard (must remain green — cleanups must not drift behavior):**
- Full backend suite `cd apps/backend && .venv/bin/python -m pytest tests/ -v` → 24 passed.
- Determinism run-twice-identical test still passes (proves the `tape_engine.py:54` change is behavior-preserving).
- SIM-BUYER scenario test still resolves to `buyer_control` with reasonable confidence.
- Price-impact guard test still passes — **do not relax it.**
- Error cases unchanged: unknown-ticker `POST /watch/{ticker}` → 400; read of a not-watched ticker → 404; on a provider gap the snapshot still surfaces an explicit stale/no-data state (no fabrication).
- No new magic numbers; frontend production build (`npm run build`) clean.

## Goal Alignment & Scope Flags
- **Advances the goal directly.** The iter-2 GOAL is exactly "browser-prove the SIM-BUYER cockpit (J-01/J-02/J-08) with screenshots, UI matching REST." This plan targets precisely that and applies the iter-1 lesson (never let a backend PASS stand in for browser verification).
- **Builds on existing architecture, no duplication.** Two surgical cleanups only; cleanup #1 *removes* a duplicate inline `ask − bid`, reinforcing the Data Contract's single producer for `spread` (`MarketState.spread`). No new data-contract row; `blueprint.md` unchanged.
- **No drift / no scope creep.** Explicitly **out of scope** and excluded: any new scenario/journey (J-03 seller_control, J-04/J-05 absorption pair, J-06 unclear-chop, J-07 transitions, J-09 stop/re-watch); the stream-status-dot → `snapshot.stream_status` consolidation (deferred to the J-04/J-05 or J-09 iteration — recorded so it is not lost); any new panels, endpoints, features, config keys, or dependencies; any refactor beyond the two named cleanups. Do **not** advance to J-03 regardless of any dev-handoff suggestion.

## Definition of Done
- J-01 / J-02 / J-08 **pass via browser-qa-agent** on `SIM-BUYER`, each with ≥1 end-state screenshot; browser QA RAN (frontend served HTTP 200), did not SKIP.
- Both cleanups applied; full backend suite still passes (determinism / SIM-BUYER scenario / price-impact-guard green); frontend production build clean.
- No anti-goal violation introduced; coherence remains WARN-or-better (no new duplicate producer, no new IA home).
- Dev handoff written at `docs/handoffs/goal-i_will_be_rich-iter-2-dev.md`.
