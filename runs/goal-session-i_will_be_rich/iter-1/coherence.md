**Verdict:** COHERENCE-WARN

# Coherence Audit — goal-i_will_be_rich-iter-1

- **Session:** `i_will_be_rich` · **Iteration:** 1 (`goal-i_will_be_rich-iter-1`)
- **Auditor:** coherence-auditor · **Date:** 2026-06-02
- **Blueprint:** `runs/goal-session-i_will_be_rich/state/blueprint.md` (APPROVED, in force from iter 1)
- **Diff basis:** snapshot SHA `79193a33766b6d941560d3d89d78b9bb1e89a7cb`. The tracked diff contains only run/state artifacts; the iteration's source lives in the **untracked `apps/` tree** (`git status` shows `?? apps/`), so I audited the working tree directly (`apps/backend/app/**`, `apps/frontend/**`).

## Bottom line

The build is fundamentally coherent. There is **exactly one engine snapshot per tick** (`tape_engine.py:75-101`), every displayed value has a single producer, and the UI renders those values **verbatim** with no client-side recomputation. The app is **one `/` route in one shell** — no parallel nav, no duplicate home. **No objective Part A or Part B violation.** One advisory is recorded for a later iteration to tidy (stream-status dot), plus a trivial DRY note — neither blocks the goal.

---

## Part A — Data Contract (the "numbers don't match" gate)

Each registered value traces to **one** producer, serialized once into the snapshot and re-exposed read-only by `/summary` + `WS /stream`. The serializers are pure projections — verified no recompute (`serializers.py:1-108`, esp. the docstring + `_market`/`_headline_features` which only read snapshot fields).

| Registered value | Single producer (verified) | Snapshot field | UI reads verbatim |
|---|---|---|---|
| Tape state + confidence | `TapeStateClassifier.classify` (`tape_engine.py:77`) | `tape_state`, `confidence` | `TapeStatePanel.tsx:16,21` (`fmt(confidence,3)`; the `pct` is bar-width presentation only) |
| 14 features × 5 windows | `FeatureEngine.compute` (`tape_engine.py:76`) | `features` | `FeaturesPanel.tsx:52` (reads `active[key]`, `.toFixed` for display) |
| bid/ask/spread/last (spread = ask − bid) | `MarketState.spread` (`market_state.py:40`) | `spread` (`tape_engine.py:92`) | `QuotePanel.tsx:10` displays `market.spread` — **does not** compute `ask−bid` in the UI |
| Recent trades (price/size/side) | `classify_aggressor` once per trade (`tape_engine.py:58`) | `recent_trades` | `RecentTradesPanel.tsx:24` renders `t.side` verbatim — **does not** re-classify |
| Observations + event log | classifier / `ObservationEmitter` (`tape_engine.py:80,98`) | `observations`, `event_log` | `ObservationsPanel` / `EventLogPanel` render the strings |
| Scenario label + watch/stream status | `provider.scenario` via `WatchManager` (`watch_manager.py:47`) / engine `_stream_status` | `scenario`, `stream_status` | `TopBar.tsx:64` renders `snapshot.scenario` verbatim · status dot — see Advisory #1 |

**Frontend sourcing is canonical.** `fetchInitialSnapshot` reads only registered endpoints — `/summary`, `/features`, `/events` (`api.ts:40-44`) — and the WS hook stores frames verbatim (`useTapeStream.ts:39`, `setSnapshot(JSON.parse(...))`). Tape state + confidence are read from `/summary`, which the contract explicitly registers as a read-only **re-exposer** of `/state` from the same snapshot — not a non-canonical source. `lib/types.ts:1-2` documents the contract ("renders these values verbatim — never recomputes spread, ratios, impacts, or confidence"). `format.ts` is pure presentation (`fmt`, `*Color`); `impactColor` keys on the sign of an already-computed value — not a recomputation.

**No duplicate computation found.** The classifier **consumes** the `average_spread` feature (`classifier.py:53`), it does not recompute spread. No new endpoint or function recomputes any registered value. **Data-contract additions: none** — confirmed against the spec; every displayed value is a first implementation of an already-registered row read from its canonical/registered source.

## Part B — Information Architecture (the "where do I find it" gate)

- **Single home, single shell.** The only routes are `app/page.tsx` and `app/layout.tsx` (verified via `find apps/frontend/app`). No second `page.tsx`, no `route.ts`, no parallel shell. All six panels are composed inside `/` via `Cockpit.tsx:13-26`.
- **No new IA home / no duplicate home / no new nav section** — matches the blueprint ("Phase 1 is exactly one screen `/`… No second page, no watchlist grid, no dashboard") and the spec's "Blueprint conformance: …no reapproval requested." Confirmed.
- **Reachability:** every Must-have surface is on `/` in ≤1 click (enter ticker → Watch). Well within the ≤2-click rule.

→ **Part B: PASS, no findings.**

---

## Advisory notes (WARN — does not block; recorded for the next iteration to tidy)

**1. Stream-status dot is driven by client `connStatus`, not the engine's canonical `stream_status`.**
The persistent top-bar dot displays the browser's WebSocket lifecycle — `connStatus` ∈ {idle, connecting, live, closed} (`TopBar.tsx:69-70`, fed by `useTapeStream.ts:33-49`) — rather than the engine's registered `snapshot.stream_status` ∈ {connecting, live, **stale**, closed} (`tape_engine.py:40,47,67-89`, served by `/state`, `/summary`, `WS`). The blueprint app-shell text specifies the dot shows "connected / **stale** / closed," and the engine already produces a canonical `stream_status` that uniquely carries the no-fabrication **stale** (provider-gap) state; the client `connStatus` has no `stale` and cannot surface it.
- *Why WARN, not FAIL:* (a) only one surface shows stream status, so no two views display a divergent number — the dangerous "numbers don't match across views" failure is not present; (b) client transport liveness ("is my socket open?") is legitimately a client-only signal, arguably distinct from server-side provider-feed health; (c) `stale`/`closed` are not exercised this iteration (SIM-BUYER never gaps; Stop/teardown is deferred to J-09).
- *Forward risk this records:* once the stale-handling and J-09 teardown iterations land, the dot could read `live` while the snapshot says `stale`/`closed` — the exact two-sources-for-one-concept drift this gate exists to catch early.
- *Concrete tidy (next status/teardown iteration):* drive the dot from `snapshot.stream_status` (e.g. `TopBar.tsx:69` reads `snapshot?.stream_status`), optionally overlaid with a client "disconnected" indicator when the socket itself drops — so the engine's canonical status, including `stale`, is what users see. The decomposer should fold this into the J-04/J-05 (stale/no-data) or J-09 iteration.

**2. Trivial DRY note (not a contract violation — no verdict impact).**
`tape_engine.py:54` computes `event.ask - event.bid` inline to feed `FeatureEngine.add_quote` (the `average_spread` feature's input). This duplicates the `ask − bid` arithmetic owned by `MarketState.spread`, but it does **not** create a divergent producer of the displayed `spread` (that value comes solely from `MarketState.spread` at `tape_engine.py:92`), so it is not a coherence violation. Since `update_quote(event)` already ran on line 53, line 54 could pass `self._market.spread` to keep the subtraction in exactly one place. Optional cleanup only.

---

## Conclusion

Single source of truth and single information-architecture home are both satisfied: one immutable snapshot per tick, every displayed value with exactly one producer read verbatim by REST/WS/UI, and one `/` cockpit in one shell with no parallel structure. No objective FAIL. **COHERENCE-WARN** for the stream-status-dot advisory — flagged now so the upcoming stale/teardown iterations consolidate the status indicator onto the canonical engine field rather than the client socket state.
