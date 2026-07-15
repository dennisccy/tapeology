# goal-tradable_wall-iter-7 Audit Report

**Date:** 2026-07-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-06's keyless core is genuinely done and verified against the real source, not the handoff summary: the cockpit `PriceChart` overlays tradable bands read verbatim from `/research/tradability`, and the confluence chip's match decision reads the served `structure_tape_map` `rejection_states`/`breakthrough_states` mapping off `/research/strategies` with **no** hardcoded tape-state literal in the matching branch. The backend diff is empty and `config_fingerprint` is confirmed `4d665603569b9dbf`. One real, borderline-IMPORTANT limitation remains (a transient wall-clock `as_of` fallback that briefly draws today's-basis bands on every historical-replay open before self-correcting) plus the spec's own operator-gated carry (the credentialed chip-fire was never runtime-observed) — both documented below, neither compromises the steady-state decision surface. Very close to a clean PASS.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no_change_needed): backend genuinely untouched.**
`git diff --name-only -- apps/backend/` is empty; the only backend change is the additive new test file `apps/backend/tests/test_price_chart_confluence.py` (untracked). `CONFIG.config_fingerprint()` invoked directly returns `4d665603569b9dbf` (spec DoD item met). No frozen backend file (`config.py`, `strategies.py`, `tradability.py`, `levels.py`, `backtests.py`, `edge_report.py`, `setups.py`, `datasets.py`, engine, adapters) appears in the diff. This DoD line is fully satisfied.

### Frontend Findings

**F1 — IMPORTANT-boundary (gap, documented — not fixed): transient wall-clock `as_of` fallback re-introduces the same lookahead-display class the dev's own fix targeted.**
`apps/frontend/components/PriceChart.tsx:203-206` — the tradability fetch computes
```
const asOf = history?.epoch_anchor != null
  ? new Date(history.epoch_anchor * 1000).toISOString()
  : new Date().toISOString();
```
On **every** historical/sim replay open, and again transiently on every bar-size change (the history poll at L161 sets `history=null` synchronously), `history?.epoch_anchor` is null for the sub-second window before the first `…/history` response lands. During that window `as_of` falls back to wall-clock **today**, so the backend `_resolve_basis` resolves **today's** basis and the overlay briefly fetches/draws today's-basis bands (future-derived relative to the replayed past session) before self-correcting within ~1s.
- *Failure scenario:* open AAPL in historical mode over 2026-06-22 → for ~1s the overlay draws today's (2026-07-15-basis) bands (e.g. resistance ~317, support ~254–277) on a chart whose candles are ~297–300, then snaps to the correct 2026-06-18-basis ~300 band. For the pinned AAPL case no spurious chip fires (297–300 is outside today's bands), but a symbol whose replay price coincidentally sits inside a today's-basis band **could** flash a confluence chip citing a band that does not belong to the replayed session.
- This is the residual **transient** form of the exact bug the dev's documented deviation eliminated in its **persistent** form; the reviewer flagged it as MINOR #1 with the correct fix.
- **Why documented, not fixed during audit:** (a) it is transient/self-correcting and never reaches the steady-state decision surface the operator actually reads; (b) the flagship pinned case is unaffected; (c) the fix is a frontend **runtime-behavior** change whose only sound verification is a live browser, and the backend was down at audit time / full-stack + Chrome-MCP verification is out of audit scope — shipping it on `tsc` + source-inspection evidence alone would repeat the precise verification gap the dev's own process warns about (only live testing caught the original `as_of` bug).
- **Recommended, verified-safe follow-up:** drop the wall-clock fallback and guard the fetch on `history?.epoch_anchor != null` (stay `loading`, no request, until the anchor resolves). Verified safe by source: simulated providers **always** set a non-null anchor (`apps/backend/app/providers/simulated.py:137` → `CONFIG.sim_session_anchor_epoch`) and historical sets `None` only when there are no bars (`historical.py:58`, nothing to overlay anyway), so deferring never suppresses a legitimate overlay **or** the SIM honest-empty-state. The follow-up must also update `test_price_chart_confluence.py` test #5's `assert "new Date().toISOString()" in as_of_computation` and correct the stale module docstring (see T1).

**F2 — GAP (operator-gated, accepted by spec): confluence chip firing was never runtime-observed.**
Only the chip *logic* is source-verified (`PriceChart.tsx:480-501` — a correct `price-in-band × side→direction × served-state-match` conjunction). Neither the dev nor QA observed the chip actually render at a real in-band + mapped-state moment (dev handoff "Known Issues" #1; QA TC-17 BLOCKED). The spec explicitly carves this out as the operator-gated credentialed AAPL 2026-06-22 replay portion, honest-blocked, never simulated — so this is an accepted carry, **not** a failure. Note: per project memory, Alpaca creds do live in `apps/backend/.env`; the backend simply was not running at audit time. Closing recommendation: run the credentialed replay and capture the real chip screenshot to close TC-17 (also closes the parallel J-03 carry).

**F3 — OBSERVATION (no_change_needed): live-mode gate genuinely untouched.**
`apps/frontend/app/page.tsx:251` keeps `(mode === "sim" || mode === "historical")` byte-identical; the only edit is the additive `tapeState={snapshot?.tape_state ?? null}` prop at L255. `PriceChart` stays fully unmounted in live mode → overlay + chip cannot appear there. Confirmed by code and by test #9; dev browser-verified AAPL-live shows no chart section.

### Test Findings

**T1 — OBSERVATION (gap): the QA report and the test module docstring describe stale, pre-fix code.**
The QA report's TC-08 and TC-13 both assert *"`PriceChart.tsx L203–205`: `fetchTradability(ticker, new Date().toISOString())` — passes current time verbatim"* and mark them PASS. That is the **pre-fix** implementation; the shipped code (L203-206) resolves `as_of` from `history.epoch_anchor`. The QA agent evidently echoed the plan text and the test file's own stale module docstring (`test_price_chart_confluence.py:14-16`, which still says "keyed on `ticker` alone" and "passes the CURRENT wall-clock time as `as_of`") rather than reading the final source. The underlying code is nonetheless correct, and the file's actual tests #4/#5 (`:111-164`) correctly assert the `[ticker, history?.epoch_anchor]` keying and epoch_anchor-derived `as_of` — only the docstring is stale (reviewer MINOR #2). Documentation-honesty issue with no product impact; correct the docstring + QA description in the F1 follow-up.

**T2 — OBSERVATION: source-inspection tests cannot catch runtime regressions.**
The 9 new tests are grep-style structural guards (dependency arrays, served-field reads, no-hardcoded-literal scan, gate-present). They are reasonably tight for that style (exact-string dep-array assertions, scoped literal exclusion of `MARKER_COLORS`/`STATE_LABELS`) and match this repo's established keyless-frontend precedent, but by construction they cannot verify runtime behavior — including the F1 transient or whether the chip actually renders. This is the repo's standing constraint, not a new defect; noted for context.

**T3 — OBSERVATION (no_change_needed): the 9 J-06 tests pass and the suite is intact.**
`pytest tests/test_price_chart_confluence.py -q` → 9 passed (verified). Dev + QA both report the full suite at 1348 passed / 7 skipped; with the backend source untouched (empty diff) the regression risk to the pre-existing 1339 tests is nil, so the count is credible without a full re-run.

---

## 3. Domain Assessment

The core domain logic — a pure *display conjunction* over already-served values — is correct and faithful to the spec:
- **Band overlay** (`PriceChart.tsx:432-467`) draws one solid price line per served band edge, colored by `side`, titled from `side`/`class`/`quality_score`/`round_number` — served fields verbatim, no client scoring, clustering, or re-detection. Solid (`lineStyle:0`) is deliberately distinct from the component's own dashed thesis lines.
- **Chip match** (`:480-501`): `lastPrice` = last served candle close; `matchedBand` = first served band containing it; `direction` = resistance→short / support→long (the structural side→direction reading named in the spec's Notes, correctly inlined — not tape-state vocabulary); `matchKind` compares `tapeState` against the served entry's `rejection_states[direction]`/`breakthrough_states[direction]` **only**. The four tape-state names appear nowhere in the matching branch (test #1 enforces this, scoped to exclude the pre-existing cosmetic dicts). Chip correctly absent when price is outside all bands, when `tapeState` is null/`unclear`/unmapped, or before strategies load — each traced through the code.
- **Single source of truth / no-lookahead (steady state):** the dev's deviation (sourcing `as_of` from the watched session's `epoch_anchor` instead of wall-clock) is a genuine improvement — it makes the 2026-06-22 replay resolve the correct 2026-06-18 prior-close basis and render the pinned ~300 round-number resistance band, which the dev empirically confirmed live. `_resolve_basis` still owns "which session" server-side; the frontend does zero date arithmetic (test #5 guards against it). The only blemish is the F1 transient before the anchor first resolves.
- Frontend types (`StrategyEntries`, `Strategy.entries`, `StrategiesPayload.strategies`, `TradabilityBand`, `TradabilityResponse`, `TapeHistory.epoch_anchor`) all line up exactly with the component's reads, corroborating the clean `tsc --noEmit` exit. The `Strategy.entries` widening is purely additive; `v1`'s narrower shape still satisfies it.

Scope discipline is clean: exactly `page.tsx` (one additive prop + comment), `PriceChart.tsx` (+204/-4), `types.ts` (additive widening), and one new additive test file. No backend source, no `/structure` change, no new nav/page, no new `api.ts` function (existing `fetchTradability`/`fetchStrategies` reused). No drift from the IN-SCOPE list.

---

## 4. Fixes Applied During This Audit

None.

The single substantive issue (F1) sits on the GAP/IMPORTANT boundary; I chose to document it with a verified-safe follow-up rather than apply an un-browser-verifiable frontend runtime change at the audit stage (rationale in F1). All other findings are OBSERVATION-level (documentation staleness) or spec-sanctioned operator-gated carries, which the auditor policy says to document, not fix. No regression was introduced by this audit.

---

## 5. Recommended Next Step

Proceed — hand to the goal-evaluator. J-06's keyless core is achieved and evidence-verified; the remaining items are an accepted operator-gated carry (F2) and a borderline transient (F1) that does not reach the steady-state decision surface.

Two concrete, low-risk follow-ups (ideally as a lean patch before or alongside era closure):
1. **Close F1**: guard the tradability fetch on `history?.epoch_anchor != null` (drop the wall-clock fallback), then update `test_price_chart_confluence.py` test #5 + module docstring, run `tsc` + the 9 tests, and — because it is a runtime change — re-verify the SIM honest-empty-state and a historical-replay overlay in a live browser.
2. **Close F2/TC-17**: with the backend up and Alpaca creds loaded, run the credentialed AAPL 2026-06-22 replay and capture the real chip-at-confluence screenshot (also closes the J-03 parallel carry).

The evaluator's `GOAL_ACHIEVED`-vs-`CONTINUE` call may reasonably treat J-03's credentialed remainder + F1/F2 as honest operator-gated/transient carries.
