**Verdict:** COHERENCE-PASS

# Coherence Audit — goal-i_will_be_super_rich-iter-1

- **Session:** i_will_be_super_rich · **Iteration:** 1 · **Depth:** full
- **Audited against:** `runs/goal-session-i_will_be_super_rich/state/blueprint.md`
- **Diff base:** `git diff 09d1b1c012a411713bb12ab167dbc0a643350b91` (snapshot SHA matches `iter-1/snapshot-sha`) + working tree
- **Scope of change:** backend `main.py`, new `providers/adapters/{base,alpaca,__init__}.py`, `.env.example`, `test_real_data_gate.py`; frontend `page.tsx`, `TopBar.tsx`, new `DataSourceSelector.tsx` + `ProviderUnavailable.tsx`, `lib/{api,types}.ts`. No new route — all surfaces under the single home `/`.

## Step 1 — Data Contract (objective → FAIL gate): PASS

No duplicate computation and no non-canonical source. The iteration implements existing **rows 6 + 9** and creates the already-named vendor-agnostic adapter (canonical owner for rows 7–9); it registers no new displayed value.

- **Row 9 — real-data availability state.** Single canonical source `real_data_available()` defined **exactly once** (`apps/backend/app/providers/adapters/alpaca.py:50`), imported and read by the watch gate (`apps/backend/app/main.py:98–108`), and surfaced via the contract-specified **explicit 503 from `POST /watch/{ticker}`** (`reason: "provider_unavailable"`). The UI learns availability **only** from that API response — `page.tsx` sets `unavailableMode` from `result.providerUnavailable`, which `lib/api.ts` derives solely from the 503 `reason`. The frontend never re-derives credential presence. No second computation, no second endpoint. ✓
- **Row 6 — watched-source descriptor + stream status.** The stream-status dot reads the engine's canonical `snapshot.stream_status` (`TopBar.tsx:59–61`); the sim source descriptor reads canonical `snapshot.scenario` (`TopBar.tsx:165–168`). No client recomputation. The optional `{mode,start,end,speed}` watch body assembles **user inputs** into the request (`TopBar.tsx:handleSubmit`) — input packaging, not recomputation of a served value. ✓
- **Rows 1–5 — engine snapshot (single source of truth).** Untouched. The real-mode branch raises `RealDataUnavailableError` **before** `manager.watch` (`main.py:98–108`), so no engine/snapshot/trade/quote/state is created on refusal (no fabrication, no sim fall-back); the sim path is byte-for-byte unchanged (Simulated sends no body). No parallel state/feature path, no engine or canonical-read change. ✓
- **Vendor-seam singularity (architectural).** Verified no Alpaca SDK import anywhere outside `adapters/alpaca.py`; vendor name confined to that one module; `main.py` imports the neutral `real_data_available` function, not a vendor SDK. Credentials read from env only; `.env.example` holds names with empty values; not in engine `Config`. ✓

## Step 2 — Information Architecture (objective → FAIL gate): PASS

- **Canonical home / no new route.** Every new surface lives under the single existing home `/` (ui-surface-map confirms: 0 new routes, "still exactly one screen `/`"). ✓
- **Blueprint-specified placement.** `DataSourceSelector` + the mode-specific controls sit in the persistent **TopBar** — exactly the blueprint app-shell slot ("Top bar: … data-source selector (Live / Historical / Simulated) · mode-specific controls"). `ProviderUnavailable` renders **in place of** the cockpit inside the existing `<main>` (`page.tsx`: `Cockpit | ProviderUnavailable | IdleState` are mutually exclusive) — the blueprint's specified "honest non-cockpit state (provider unavailable, no credentials)". ✓
- **Reachability ≤2 clicks.** Selector and per-mode controls are 0–1 clicks (always-visible app shell); the provider-unavailable state is reached by selecting Live/Historical + Watch (≤2). ✓
- **No parallel shell / no duplicate home.** No second layout or nav introduced; no second cockpit or results page. ✓

## Step 3 — Advisory observations (non-blocking; not WARN-triggering)

Both items are **spec-sanctioned scoping for this iteration**, not drift it introduced — recorded as forward notes for J-11/J-12, not current defects.

1. **Market-status indicator is a static literal** "market unavailable" (`TopBar.tsx`, `mode === "live"`), not yet sourced from a canonical endpoint. This is intended: Data Contract **row 8** (`GET /market/clock`) is explicitly deferred (OUT OF SCOPE → J-12), and the indicator stays honest (never claims open/closed). *Forward note:* when J-12 wires the market clock, this indicator must **read `GET /market/clock`** and must not remain a second hardcoded source for market status.
2. **The `provider_not_implemented` 503 branch** (credentials-present, `main.py:106–108`) has **no dedicated honest non-cockpit UI** this iteration — the frontend special-cases only `provider_unavailable`, so a creds-present refusal would fall through to the generic error line. Acceptable here (verification is credentials-absent by design). *Forward note:* J-11/J-12 should give the creds-present "not yet serving" case its own honest non-cockpit state rather than a generic red error.

## Conclusion

No objective Data-Contract or Information-Architecture violation. The single-source-of-truth and provider-agnostic-seam guardrails are upheld: one canonical `real_data_available()`, one adapter module for the vendor, untouched engine and canonical REST/WS reads, and every new surface in its blueprint-specified home under `/`. Remaining notes are minor, honest, and explicitly deferred to later real-data slices. → **COHERENCE-PASS**
