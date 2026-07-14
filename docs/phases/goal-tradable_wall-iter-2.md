# Goal Iteration 2 — The wide scan: touch-event scanner + case registry (J-02)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-02
- **Required-still-passing journeys:** J-01, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - 3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - 5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - 6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - 7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - 8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **The tradable map is a lens, never a second levels engine.** `research/tradability.py` consumes `compute_levels` output verbatim (plus bars for scale context); it never re-detects pivots/extremes and never alters the frozen raw computation or its parameters. *(critical)*
  - **Morning-markup discipline.** Any session's map derives only from bars fully completed by the prior session's close; no forming-bar data enters a map, an event, or a chip. *(critical)*
  - **Descriptive, never imperative.** Chips, case studies, and reports state conditions and cite measured history — never "buy/sell/short now", no prediction or expected-return language, anywhere in UI copy. *(critical)*
  - **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid, publishable outcome. *(critical)*

## GOAL

Deliver the touch-event scanner and case-study registry: for each of the 12 panel symbols, walk its stored 5m bars session by session against that session's morning tradable map (J-01), emit deterministic band-touch events with `rejected`/`broke`/`chopped` reaction labels and forward returns, and serve them at `GET /research/setups` + `GET /research/setups/{id}` (+ a byte-identical read-only MCP `setups` proxy) — with the pinned AAPL 2026-06-22 ~300 event surfacing as `rejected` with negative forward reaction.

## BACKGROUND

J-01 (the tradable level map) is passing; J-02 is the next dependency-order unblocker — J-03 records real tape at J-02's top-ranked events, J-04 arms `structure_tape_map` on its band-touches, and J-05 renders its case browser. Both the iter-0 and iter-1 evaluators explicitly recommended building J-02 next at **full** depth, because it introduces a new canonical value + owner (`setups.py`) across the backend+MCP boundary and its central risk is the critical no-lookahead rail — each event's morning map must derive only from data before its session (the exact `_PriorSessionBarView` consecutive-session hazard J-01 surfaced). This iteration carries **one risky journey only** (rubric rule 5); J-03/J-06 stay operator-Alpaca-credential-gated and are excluded (rubric rule 6). The iter-1 lesson governs the fixture design (see NOTES).

## IN SCOPE

### Backend
- [ ] Add `apps/backend/app/research/setups.py` — the sole owner of the touch-event / case-registry value. For each panel symbol and each session in the stored 5m window: compute that session's morning tradable map by reusing J-01's owner (`compute_tradability` / its `_resolve_basis` morning-markup as-of resolution) — **read the bands verbatim, never recompute the map or the levels**; detect band-touch events in the session's 5m bars (first touch per band per session, config-owned re-arm rule); classify each reaction deterministically (`rejected` / `broke` / `chopped`, config-owned pre-registered definitions); record forward returns at config-owned horizons, measured strictly after the touch (event-relative).
- [ ] Add the config-owned constants (all namespaced, all in the `config_fingerprint` exclusion set — `config_fingerprint` MUST stay `4d665603569b9dbf`): the **12-symbol panel** (`AAPL MSFT NVDA TSLA AMZN GOOGL META AMD NFLX SPY QQQ JPM`), the reaction definitions/thresholds, the forward-return horizons, the first-touch re-arm rule, and the 5m retention window — each documented in `config.py` with its rationale, no literal in `setups.py` (the `sr_*`/`tradability_*` discipline).
- [ ] Expose `GET /research/setups` (registry: filterable by symbol / reaction / band class) and `GET /research/setups/{id}` (per-event drill-in: band, reaction, forward returns, and a tape-timeline field that is present-but-empty until J-03 records). Both return `setups.py` output verbatim (single source of truth).
- [ ] Add the read-only MCP `setups` proxy (byte-identical mirror of `GET /research/setups`), following the existing `datasets` proxy pattern in `apps/backend/app/mcp/__init__.py`.
- [ ] Commit ONE small multi-session, multi-symbol 5m scan fixture under `apps/backend/tests/fixtures/` so the scan path, no-lookahead, and reaction-classification tests run keyless in CI.

### Frontend (if applicable)
- None. J-02 is backend + MCP only; the Case Studies browser UI is J-05.

### New user-facing capability
Via API/MCP: query a case-study registry of historical band-touch events across the panel and drill into any one event (band, reaction, forward returns). No UI surface this iteration (rendered on `/structure` at J-05).

### New information displayed
The `setups` registry (per-event: symbol, session, band ref, reaction label, forward-return fields) served at `/research/setups` and `/research/setups/{id}` — consumed by agents/API/MCP now, rendered in the UI at J-05.

### New user actions
None (no UI). API/MCP consumers gain the `setups` list + drill-in reads and the MCP `setups` tool.

### UI surface changes
None.

### Product surface delta
The product gains its evidence layer: the tradable map (J-01) now has a companion registry of *what actually happened* at those bands historically — the "more examples exist" success criterion — ready for the tape join (J-03), the edge report (J-04), and the case browser (J-05).

### Blueprint conformance
No new surface. The value this iteration realizes is already pre-registered in `blueprint.md` Data Contract row "Touch events + reaction labels (`rejected`/`broke`/`chopped`) + forward returns + case registry → `app/research/setups.py` → `GET /research/setups`, `GET /research/setups/{id}`". Nav is frozen (backend+MCP only). No blueprint edit, no reapproval request.

### Data-contract additions
None — the setups/case-registry value is already registered in `blueprint.md` (this iteration realizes its owner + endpoints, adding no unregistered displayed value). The new config constants (panel, reaction defs, horizons, re-arm rule, retention window) are pre-registered config inputs to that one value, not new served values. The tradable map is read verbatim from its existing canonical owner (`GET /research/tradability`) — no second computation.

## OUT OF SCOPE

- `structure_tape_map` strategy registration and the edge report (J-04) — no `backtests.py` / `edge_report.py` / strategy-registry change.
- Credentialed Alpaca tick recording and `DatasetStore` writes (J-03) — the drill-in tape-timeline field is present-but-empty until J-03 runs; no recorder invocation.
- Any `/structure` or cockpit UI change (J-05 / J-06) — Frontend Present: no.
- Any mutation of `tradability.py`, `levels.py`, the tape engine, `backtests.py`, or the `config_fingerprint` — J-02 only *reads* the map and levels.
- Champion-pointer movement (frozen; moves only through the existing sweep gate).
- No new nav entry.

## DEFINITION OF DONE

- [ ] J-02 verified via API + MCP (evaluator-reproducible): `GET /research/setups` returns a registry with **≥15 band-touch events across ≥8 of the 12 panel symbols** within the stored 5m window (after the store is populated per NOTES prerequisite).
- [ ] The pinned **AAPL 2026-06-22** event on the ~300–302 resistance band appears with reaction **`rejected`** and **negative** forward-return field(s).
- [ ] **No-lookahead** holds: shifting a scan's `as_of` earlier never changes an already-emitted event (consecutive-session test — the `_PriorSessionBarView` hazard).
- [ ] **Determinism**: identical scans produce byte-identical output.
- [ ] **REST == MCP**: `GET /research/setups` and the MCP `setups` proxy return byte-identical bodies.
- [ ] `GET /research/setups/{id}` returns the event's band + reaction + forward returns; unknown id → 404; malformed filter params → 422.
- [ ] `config_fingerprint` stays `4d665603569b9dbf` (new constants in the exclusion set; stability + real-threshold counter-test).
- [ ] Frozen foundations byte-identical: `levels.py` / `tradability.py` / `backtests.py` / tape engine / `BarStore` / Alpaca paths absent from the diff; engine equivalence green (22/22).
- [ ] Required-still-passing journeys **J-01, J-07** remain green (deterministic replay).
- [ ] No anti-goal violation introduced; coherence-auditor COHERENCE-PASS (one owner `setups.py`, one endpoint, byte-identical MCP proxy).
- [ ] Full backend unit/integration suite passes; the new scan-path / no-lookahead / reaction / determinism tests run keyless on the committed fixture.
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** N/A — backend + MCP only; the case-browser UI is deferred to J-05. J-02 is verified by API/MCP reproduction (evaluator re-runs the registry query, drill-in, REST==MCP byte-identity, no-lookahead, and determinism), mirroring how backend-only J-01 was verified in iter-1.
- **Unit/integration** (all keyless on the committed multi-session, multi-symbol 5m fixture):
  - Scan over the fixture emits deterministic events with `rejected`/`broke`/`chopped` labels + forward returns; exact-value assertions (not "something returned").
  - **No-lookahead consecutive-session** test: shifting `as_of` earlier never mutates an already-emitted event; each session's map derives only from bars completed before that session (the `_PriorSessionBarView` consecutive-session subtlety).
  - **Reaction-classification regression under intraday density** (per the iter-1 lesson): a realistic multi-timeframe/5m slice — never daily-only — with a guard that bites (e.g. a shallow high-volume intraday touch must not be misclassified as the pinned daily rejection).
  - Determinism: repeat scan is byte-identical.
  - `REST == MCP` byte-identity for `setups`.
  - `config_fingerprint` stability + exclusion-set counter-test (mirror the tradability pattern in `tests/test_tradability.py`).
  - Frozen-foundation guards re-run: `levels.py`/`tradability.py` byte-identical output; tape engine equivalence.
- **Error cases:** symbol with no bar series → honest empty (no events, no crash — the `no_bar_series_for_symbol` analog); a session whose morning map has zero bands → no events for that session (never a fabricated event); unknown `setup_id` → 404; malformed filter (bad reaction/class/symbol) → 422.

## NOTES

- **Execution prerequisite (keyless, but a live act):** the live store currently holds 5m bars for **AAPL only** (MSFT has 4h; the other 10 panel symbols have none). The "≥15 events across ≥8 symbols" headline is therefore **not** reachable against the current store. J-02 step 1 (per `docs/goal.md`) is an explicit fetch: populate the store for the 12-symbol panel via the existing **era-5 Yahoo store-first flow** — `1d` (long window), `1h`, `5m` (retention window). This is **keyless (Yahoo, no Alpaca)** but is a live-network act that runs under the `integration` marker (`TAPEOLOGY_LIVE_INTEGRATION=1`) / as an explicit executor step, not part of the hermetic default suite. The committed fixture covers the scan *logic* keyless; the ≥8-symbol *headline* is verified after this fetch. Yahoo 5m retention (~60 days) comfortably covers the pinned 06-22 window. If the panel fetch cannot complete (network), the executor must report that honestly — the scan logic still passes on the fixture, but the ≥15/≥8 headline stays unverified rather than simulated.
- **Depth = full, justified:** J-02 requires new tests well beyond browser smoke (no-lookahead consecutive-session, determinism, REST==MCP byte-identity, reaction-classification-under-intraday-density) AND introduces a new canonical value + owner (`setups.py`) across the backend+MCP boundary — both `full` triggers; the prior evaluator also recommended `full`. Not ESCALATE-forced (iter-1 verdict was CONTINUE), but clearly a `full` iteration.
- **Lesson applied (iter-1 — CONTINUE):** a daily-only fixture could not surface J-01's cross-timeframe scoring CRITICAL; it only appeared under realistic multi-timeframe/intraday density. J-02's reaction classification + forward returns aggregate across the 5m session, so the committed fixture MUST be a realistic multi-session/5m slice (never daily-only) with a guard that bites under intraday density, and the per-session map reuse MUST add its own consecutive-session no-lookahead test.
- **No magic numbers / pre-registration (Constraint — "Config-owned everything"):** the reaction definitions, forward-return horizons, re-arm rule, and retention window are config-owned constants **pre-registered before measurement** — never post-hoc tuned to manufacture the ≥15/≥8 count or to force the pinned AAPL 06-22 event to read `rejected`. The 06-22 `rejected`/negative-forward result must fall out of pre-registered definitions applied to real bars, not the reverse.
- **Descriptive labels only:** `rejected`/`broke`/`chopped` are descriptive reaction classifications of measured history — no imperative or predictive language enters any field.
- **Coherence watch:** `setups.py` must be the *sole* owner; the two GETs and the MCP `setups` proxy serve its output verbatim; the tradable map is read from `GET /research/tradability` (or its owner `compute_tradability`) — never a second map/levels computation (the exact drift the coherence-auditor hard-fails).
- **Watch-item carried for J-04:** the edge report must EXTEND the existing `apps/backend/app/research/edge_report.py` (currently the era-3 champion-only CLI) additively — never fork it (per the blueprint Data Contract note).
