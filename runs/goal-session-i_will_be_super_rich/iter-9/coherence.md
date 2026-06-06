# Iteration 9 — Coherence Audit

**Iteration:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 6 — watch/stream status (`connecting`) | OK | `apps/frontend/app/page.tsx`: `effectiveConnStatus = pending && !ticker ? "connecting" : connStatus` — reads the existing row-6 status concept; `ConnectingState` is a display-only component, no recomputation |
| Row 9 — real-data failure state (`provider_timeout`) | OK | `apps/backend/app/main.py`: `asyncio.wait_for(..., timeout=CONFIG.vendor_call_timeout_seconds)` raises `RealDataError("provider_timeout", ...)` on the **same** `POST /watch/{ticker}` failure path — additive sibling reason, not a new endpoint or new producer |
| `WATCH_REQUEST_TIMEOUT_MS` (frontend config constant) | OK | `apps/frontend/lib/config.ts`: registered in the blueprint as a config constant, not a displayed value; no coherence obligation |
| `vendor_call_timeout_seconds` (backend config constant) | OK | `apps/backend/app/config.py`: registered in the blueprint as a config constant, not a displayed value; no coherence obligation |
| `connError` in `useTapeStream` | OK | `apps/frontend/lib/useTapeStream.ts`: UI-layer connection lifecycle message (not an engine-computed tape value); does not recompute any row 1–6 value; `gotFrame` guard ensures it fires only pre-snapshot |
| Rows 1–6 (tape state / features / quote / trades / observations / stream status) | OK | Diff touches none of the canonical computing modules (`TapeStateClassifier`, `FeatureEngine`, `MarketState`, aggressor classifier, `WatchManager`); `Cockpit` still reads the engine snapshot verbatim once data arrives |
| `StreamFailedState` display component | OK | `apps/frontend/components/IdleState.tsx`: pure presentation state (rose warning + static message); renders when `connStatus === "failed"`, which is set by the WS/snapshot failure lifecycle — no engine value recomputed |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `ConnectingState` (pending cockpit treatment on `/`) | OK | `apps/frontend/app/page.tsx`: rendered in the cockpit area of `/` when `pending && !ticker`; no new route, no parallel shell; all journeys J-21–J-24 live on `/` per IA |
| `StreamFailedState` (connect-failure cockpit treatment on `/`) | OK | `apps/frontend/app/page.tsx`: rendered in the cockpit area of `/` when `streamFailed`; replaces the cockpit in-place per the IA's "Honest non-cockpit states" clause; no new route |
| `CONN_DOT.failed` dot in TopBar | OK | `apps/frontend/components/TopBar.tsx`: additive entry in the existing `CONN_DOT` record; no new nav section |
| Inline validation (Watch button + message in TopBar) | OK | `apps/frontend/components/TopBar.tsx`: the Watch button and its validation message live inside the existing `TopBar` form; no new route, no new nav section |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. The iteration is tightly scoped to presentation-lifecycle hardening on the existing `/` cockpit screen. No new routes, no new canonical values, no nav-skeleton change. Blueprint rows 6 and 9 were updated additively by the decomposer before the iteration ran. All new UI states (`ConnectingState`, `StreamFailedState`, inline validation) are transient presentation states that add no client-side recomputation of engine values — rows 1–6 remain single-source-of-truth.
