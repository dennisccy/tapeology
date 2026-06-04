**Verdict:** COHERENCE-PASS

# Coherence Audit — goal-i_will_be_super_rich-iter-3

- **Session:** i_will_be_super_rich · **Iteration:** 3
- **Audited diff:** `git diff 1c05ebb…` (+ uncommitted working tree)
- **Blueprint:** `runs/goal-session-i_will_be_super_rich/state/blueprint.md`
- **Scope of change:** Market clock (Data Contract **row 8**) built; honest **`market_closed`** state (row 9) completed; Live market-status indicator turned real. Still exactly one screen (`/`).

This iteration is a textbook additive build into the approved blueprint. No objective Data-Contract or Information-Architecture violation found. Advisory notes are nil-to-trivial.

---

## Step 1 — Data Contract check (the "numbers don't match" gate) → PASS

**Row 8 (Market clock — open/closed + next open/close).** Built exactly as registered, with a single computing owner and a single serving endpoint:

- **One computing owner.** `AlpacaAdapter.get_market_clock()` (`apps/backend/app/providers/adapters/alpaca.py:176`) is the only place the session status is sourced, returning the vendor-neutral `MarketClock` record (`apps/backend/app/providers/adapters/base.py:68`). Declared on the `MarketDataAdapter` Protocol (`base.py:117`). The `alpaca` SDK import stays lazy + confined (`alpaca.py:182` `from alpaca.trading.client import TradingClient`). No vendor type leaks into the record.
- **One serving endpoint.** `GET /market/clock` (`apps/backend/app/main.py:256`) is the only endpoint that serves the clock. It reads the adapter via the existing `Depends(get_market_adapter)` seam and re-exposes the value read-only — no recomputation.
- **Pre-flight gate reads the SAME owner, not a second source.** The market-closed gate in `POST /watch` (`apps/backend/app/main.py:160`) calls `adapter.get_market_clock()` **directly** — the same computing owner the endpoint uses — exactly as the spec's "Data-contract additions" demanded ("not a second endpoint, not a recomputation"). The in-code comment states this explicitly. This mirrors how the row-9 availability gate already reads `adapter.is_available()`. **No second clock, no second endpoint.**
- **Frontend reads row 8 verbatim — no client-side derivation.** `getMarketClock()` (`apps/frontend/lib/api.ts:60`) fetches `GET /market/clock` and passes the fields through. `MarketStatusIndicator.indicatorSpec()` (`apps/frontend/components/MarketStatusIndicator.tsx:24`) maps `clock.is_open` / `clock.available` / `clock.next_open` onto color/label only — open/closed is never recomputed (the comment says so, and the code confirms it). The `next_open` shown on the `market_closed` panel comes from the `POST /watch` refusal body, which the gate populated from the same `get_market_clock()` call — same owner, not a parallel lookup.

**Re-format is fine.** `formatMarketTime()` (`apps/frontend/lib/datetime.ts:5`) only renders the canonical UTC instant in the operator's local zone — a display re-format of a canonical value, explicitly permitted. It is shared by both the indicator and the panel, so the next-open time is formatted **identically** across surfaces (active drift-prevention).

**No new unregistered value.** `next_open` is part of row 8 ("next open/close") and the registered row-9 "market is closed (with next open)" state. Nothing conceptually-duplicate of an existing value was introduced. No duplicate `is_open`/session computation anywhere in the diff.

**Rows 1–6 untouched.** The engine snapshot path (state/features/quote/trades/observations) shows an empty diff: no change to `engine`, classifier, serializers, `providers/base.py`, `providers/simulated.py`, or `providers/historical.py`. (The change to `providers/adapters/base.py` is the *adapter* seam — the row-7/8 owner — a different file from the engine's `providers/base.py`.) The SSOT singularity for rows 1–6 is preserved; real data adds no parallel state/feature path.

## Step 2 — Information Architecture check (the "where do I find it" gate) → PASS

New surfaces this iteration: the **`MarketStatusIndicator`** and the **`market_closed`** variant of `ProviderUnavailable`. Both land in their registered canonical homes.

- **Canonical home + navigation path (indicator).** Placed inside the persistent **TopBar** (`apps/frontend/components/TopBar.tsx:157`), rendered when `mode === "live"`. The blueprint IA explicitly registers this surface: *"Live → symbol search + market-status indicator (open/closed, from `GET /market/clock`)."* Reachable in ≤1 click (select **Live** in the data-source selector) — well within ≤2 clicks. Verified statically in `TopBar.tsx`.
- **Canonical home (closed panel).** The `market_closed` copy is added to `ProviderUnavailable.copyFor` (`apps/frontend/components/ProviderUnavailable.tsx:14`) and rendered through the existing mutually-exclusive `Cockpit | ProviderUnavailable | IdleState` ternary on `/` (`apps/frontend/app/page.tsx:101`) — **in place of** the cockpit, never alongside fabricated panels. Blueprint IA registers "J-14 → the honest non-cockpit states" as living on `/`, ≤1 click after Watch. Reason wired through `HONEST_REASONS` (`page.tsx:19`) and `FailureReason` (`apps/frontend/lib/types.ts:64`).
- **No new route / no parallel shell.** Still exactly one screen (`/`). The ui-surface-map confirms 0 new pages/routes and no navigation changes. The indicator is inside the existing shell; the panel inside the existing ternary. No parallel layout or nav introduced.
- **No duplicate home.** The prior hardcoded "market unavailable" stub was **removed in place** from `TopBar.tsx` and replaced by the real indicator — there is no second market-status surface and no second closed-market panel. The three existing honest reasons are untouched.

## Step 3 — Subjective observations (advisory) → none material

- Color semantics are consistent with the blueprint palette (emerald = open/positive, amber = closed/unclear/unavailable, slate = pre-fetch placeholder). No formatting or label drift: a single `getMarketClock()` reader and a single shared `formatMarketTime()` helper structurally prevent divergent copies of the value or its rendering.
- The compact pill uses the short label "closed" while the full panel uses "market is closed"; this is appropriate pill-vs-panel phrasing, not an inconsistency worth a WARN.

---

## Conclusion

**COHERENCE-PASS.** Row 8 was built with exactly one computing owner and one serving endpoint; the live pre-flight gate reuses that same owner rather than introducing a second clock; the UI reads the value verbatim with no client-side recomputation; and every new surface sits in its registered canonical home on the single `/` screen with a ≤2-click nav path and no duplicate home or parallel shell. No objective Step-1 or Step-2 violation. Nothing for the next iteration to consolidate.
