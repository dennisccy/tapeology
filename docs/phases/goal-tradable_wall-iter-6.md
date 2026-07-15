# Goal Iteration 6 — J-05: `/structure` decluttered (Tradable Map default + Case Studies + Edge Report)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03 (keyless substrate), J-04, J-07
- **Anti-goal reminders** (verbatim from `docs/goal.md`, the ones this iteration must respect):
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Descriptive, never imperative.** Chips, case studies, and reports state conditions and cite measured history — never "buy/sell/short now", no prediction or expected-return language, anywhere in UI copy. *(critical)*
  - **Morning-markup discipline.** Any session's map derives only from bars fully completed by the prior session's close; no forming-bar data enters a map, an event, or a chip. *(critical)*
  - **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid, publishable outcome. *(critical)*
  - **No vocabulary drift.** No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.

## GOAL

On `/structure`, make the **Tradable Map** (≤10 quality-scored bands) the default view with the raw 1,800-level rendering behind an off-by-default toggle, and add a **Case Studies** browser (registry + per-event drill-in) and an **Edge Report** section — every value read verbatim from `GET /research/tradability`, `GET /research/setups`(`/{id}`), and `GET /research/edge-report`, recomputing nothing in the browser.

## BACKGROUND

Iters 1–5 built and stabilized all three backend read surfaces J-05 renders (tradability, setups incl. the iter-5 recency-boundary fields, edge-report) plus the iter-5 shared scan cache — J-05 is the dependency-ordered next and the explicit next-step of both the iter-4 and iter-5 evaluators. No journey is `regressed` and iter-5 coherence was `COHERENCE-PASS`, so no consolidation is owed (priority rubric rules 1–2 clear); J-05 is the sole `failing` journey whose full backend substrate is ready (rule 3), and it is targeted alone — J-06 is a separate risky UI surface (cockpit) and stays queued for iter-7 (rule 5, no bundling). **Depth = full** per the "Picking depth" triggers: it adds new UI surfaces (three sections + a drill-in) → coherence-relevant (duplicate-home / parallel-shell / zero-recomputation checks across three endpoints), it is browser-verifiable, and it crosses the backend+frontend boundary via one scoped backend hardening touch — the iter-5 evaluator recommended full explicitly. This iteration is the FIRST caller to fire `/setups` + `/setups/{id}` + `/edge-report` concurrently from a browser page-load against a possibly-cold iter-5 scan cache; lesson iter-5 (Applies to: "iter-6's J-05 `/structure` render") requires closing that cache's torn-read window before the render, so a one-line atomic cache-write hardening is in scope.

## IN SCOPE

### Backend
- [ ] Harden the EXISTING iter-5 B3 scan cache write in `apps/backend/app/research/setups.py:377-378` so it is atomic against concurrent callers: replace the two non-atomic dict-key assignments (`_SCAN_CACHE["key"]=key` then `["result"]=result`) with a single atomic publish (an immutable `(key, result)` tuple rebind read once, or a `threading.Lock` around the check-and-set). The cached result stays **byte-identical** to a fresh `_run_full_panel_scan` — this is a rebuildable accelerator, not a second source (single-source-of-truth preserved). No change to `compute_setups`' signature, scan body, output, or the reaction/boundary logic. This is the ONLY backend change this iteration.

### Frontend (if applicable)
- [ ] `apps/frontend/lib/api.ts` + `apps/frontend/lib/types.ts`: add `{ok,data,error}`-shaped client fns + types for the three endpoints (none are wired yet): `fetchTradability(symbol, as_of)` → bands map; `fetchSetups(filters?)` → case registry list; `fetchSetupDetail(id)` → drill-in incl. `tape_timeline`; `fetchEdgeReport()` → cells + register. Types mirror the endpoint payloads verbatim.
- [ ] `apps/frontend/app/structure/page.tsx` — **Tradable Map is the new default view.** On Load (the existing symbol + as-of form, which also drives the map), render the price chart candles + ≤10 band overlays (price areas/lines) + a map table with each band's range (`price_low`–`price_high`), `side`, `quality_score`, inherited `class`, member count, and `round_number` flag, plus the map's `basis_as_of` (the morning-markup basis) — all read verbatim from `GET /research/tradability`. Honest distinct states for `no_bar_series_for_symbol`, empty `bands`, and unreachable/422.
- [ ] Move the **prior raw levels + confluence-zones rendering** (the current "Price chart — S/R levels" and "Confluence zones" panels) behind an explicit **"raw levels" toggle**, OFF by default. When toggled on it renders byte-identically to today (era-5 behavior preserved unchanged).
- [ ] Add a **Case Studies** section: the registry table from `GET /research/setups` (columns: symbol, session date, band range/side/class, reaction, forward returns) with symbol + reaction filters (the endpoint's optional filter params, or a display-filter of served rows — never a client recomputation); clicking a row opens the drill-in from `GET /research/setups/{id}` (event band, reaction, forward returns, and the `tape_timeline` five-state list when the event was recorded — empty-state when not). Recency-boundary events render honestly using `reaction_boundary_truncated` + `effective_reaction_horizon_bars` (a "reaction read at a truncated {N}-bar horizon" note) — never hidden, never presented as a full-horizon reaction.
- [ ] Add an **Edge Report** section rendering `GET /research/edge-report` verbatim: per strategy × class × side × reaction (× feed) cells with n, R stats, $ + the full register, null baseline, and each cell's `insufficient_sample` shown inline. An empty / all-`insufficient_sample` report renders as an honest, first-class state (it is a valid outcome) — never blank, never a fabricated survivor.
- [ ] Preserve the era-5 **Fetch from Yahoo Finance** control, the **provenance badge** (`FeedBasisBadge`), and the era-5 **Registry** and **Comparison** sections intact, positioned below the new sections (see NOTES / assumptions.md iter-6 — declutter = raw levels behind a toggle, not removal of existing surfaces).

### New user-facing capability
The operator loads a symbol as-of a session and sees at most ~10 quality-scored tradable bands (not 1,800 level lines), browses/filters every historical band-touch case with its reaction and (when recorded) tape timeline, and reads the honest 3-way edge report — all on `/structure`, with the raw levels one toggle away.

### New information displayed
Tradable bands (range, side, quality score, inherited A/B/C class, member count, round-number flag, morning-markup basis); the touch-event case registry with reactions + forward returns + recency-boundary honesty; per-event tape timelines (recorded events); the 3-way edge-report cells + full register. All rendered verbatim from their owning endpoints.

### New user actions
A "raw levels" toggle (off by default); Case Studies symbol + reaction filters; a Case Studies row → drill-in open. (The existing Load form now also drives the map.)

### UI surface changes
`/structure` gains three sections — Tradable Map (default), Case Studies (+ drill-in), Edge Report — and a raw-levels toggle. No new page, no nav entry.

### Product surface delta
`/structure` flips from "1,800 raw levels first" to "the handful of tradable bands + the case evidence + the edge report first"; the raw view remains reachable and unchanged behind a toggle.

### Blueprint conformance
No new surfaces or nav change. All three sections live under the **already-registered** `/structure` homes in `blueprint.md`'s Information Architecture (J-01 Tradable Map → `/structure` default view; J-02 Case Studies table + drill-in; J-03 tape timeline inside the drill-in; J-04 Edge Report section; J-05 the declutter itself). Nav skeleton is frozen (anti-goal "No new nav entry"). No `blueprint.reapproval-requested` needed.

### Data-contract additions
**None.** J-05 is a pure verbatim render of values already owned and registered in `blueprint.md`: tradability bands (`research/tradability.py` → `GET /research/tradability`), touch events + reactions + forward returns + the iter-5 boundary fields + `tape_timeline` (`research/setups.py` → `GET /research/setups`,`/{id}`), and edge-report cells (`research/edge_report.py` → `GET /research/edge-report`). The frontend introduces no new computed value and MUST read each from its single registered endpoint — never a second computation or a re-derivation.

## OUT OF SCOPE

- **J-06 cockpit confluence** (band overlay + descriptive chip on `PriceChart`) — separate risky UI surface, queued for iter-7.
- Any change to the raw levels/zones rendering itself — it must stay byte-identical when the toggle is on.
- Removing or restructuring the era-5 Fetch control, provenance badge, Registry, or Comparison sections.
- The credentialed J-03 ≥10-window recording headline + pinned-AAPL 06-22 tape recording — operator-gated, parallel carry; the drill-in shows `tape_timeline` when a recorded dataset exists and an honest empty-state when it does not.
- Any backend change beyond the single `setups.py` cache-write atomicity hardening (no `tradability.py`/`edge_report.py`/`levels.py`/`strategies.py`/`backtests.py`/`config.py`/`datasets.py`/engine/adapters edits; `config_fingerprint` stays `4d665603569b9dbf`).
- The iter-5 coherence advisory that `_SCAN_CACHE` is keyed on `id(config)` — a test-only flakiness concern, not a production correctness issue; do not re-key unless it falls out of the atomic-write fix for free.

## DEFINITION OF DONE

- [ ] **J-05 passes via browser-qa-agent**: loading AAPL as of 2026-06-22 shows the Tradable Map as the default view with ≤10 bands total, including a resistance band covering the ~300–302 rejection cluster (round-number 300 flagged) — NOT 1,800 level lines (screenshot).
- [ ] The **"raw levels" toggle** is off by default; toggling it on restores the era-5 raw levels + confluence-zones view rendered byte-identically to before (screenshot of both states).
- [ ] The **Case Studies** section renders `GET /research/setups`; the pinned **AAPL 2026-06-22 ~300** case drill-in shows `reaction = rejected` with its forward returns; at least one recency-boundary event renders its `effective_reaction_horizon_bars` + truncated flag honestly (not as a full-horizon reaction).
- [ ] The **Edge Report** section renders `GET /research/edge-report` verbatim with the register visible; an empty / all-`insufficient_sample` report renders as an honest first-class state, and populated cells (if any) render verbatim.
- [ ] **Zero client recomputation**: every displayed band score/class/range, reaction, forward return, tape state, and edge-report cell is byte-equal to its owning endpoint — confirmed by the coherence-auditor (COHERENCE-PASS) and browser spot-checks.
- [ ] The era-5 **Fetch from Yahoo Finance** control + **provenance badge** still work (screenshot).
- [ ] **Required-still-passing** journeys J-01, J-02, J-04, J-07 remain green and the J-03 keyless substrate stays unbroken; `config_fingerprint` stays `4d665603569b9dbf`; every frozen backend file is absent from the diff EXCEPT the scoped `setups.py` cache hardening.
- [ ] The `setups.py` B3 cache write is atomic: the existing B3 byte-identity / determinism / checksum-bust tests pass, plus a NEW test proving two concurrent cold-cache callers never observe a new key paired with a stale/`None` result (no torn read, no 500).
- [ ] No anti-goal violation introduced (descriptive-only UI copy; no execution path; no recomputation; no vocabulary drift) — scan-report CLEAN; frontend copy-discipline lint green.
- [ ] Unit + integration tests pass; no regressions (full backend suite green).
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-6-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-05):** Load AAPL as-of `2026-06-22` against the populated 12-symbol panel store (the same store J-01/J-02/J-04 verified against): (1) default view = Tradable Map, ≤10 bands incl. the ~300–302 resistance band; (2) toggle raw levels on → era-5 view unchanged, off by default; (3) Case Studies renders + filters, pinned AAPL 06-22 drill-in = `rejected` + forward returns + honest `tape_timeline` empty/present state + a boundary event shown as truncated-horizon; (4) Edge Report renders verbatim incl. the honest empty/all-`insufficient_sample` state; (5) era-5 fetch control + provenance badge still function. Re-verify the J-01/J-02/J-04 read surfaces on `/structure` are intact.
- **Unit/integration (backend):** the `setups.py` atomic cache write — existing B3 tests (`test_cache_hit_is_byte_identical_to_a_fresh_uncached_scan`, computed-once spy, checksum-bust, enriched-read-never-leaks) still green; a NEW concurrency test asserting no torn read / no `None` result under concurrent cold-cache access. Pinned AAPL 2026-06-22 setups event stays byte-identical (J-02/J-04 non-regression).
- **Unit/integration (frontend):** the four new API client fns return `{ok,data,error}` shapes and surface backend `detail` verbatim on non-200; types match payloads; raw-levels toggle defaults off; boundary-event rendering keys off `reaction_boundary_truncated`; each new section has loading / honest-empty / degraded states.
- **Error cases that must be rejected/handled honestly:** malformed `as_of` → 422 surfaced verbatim (never a silent "now" default); tradability/setups/edge-report unreachable or non-200 → honest degraded panel (nothing cached or fabricated); a recency-boundary event → truncated-horizon disclosure (never a silent full-horizon claim); an all-`insufficient_sample` / empty edge report → honest render (never hidden, never a manufactured survivor).

## NOTES

- **Central rail — zero recomputation (single source of truth, critical):** this is the make-or-break of J-05 and what the coherence-auditor hard-fails. Render every value with the page's established `String(value)`-verbatim precedent; never recompute a band score/class/membership, a reaction, a forward return, a tape state, or a PnL/register figure in the browser. Band membership and "price-in-band" are display reads of served values, not recomputations.
- **Lesson iter-5 (Applies to: iter-6's J-05 `/structure` render):** iter-6 is the FIRST caller to fire `/setups` + `/setups/{id}` + `/edge-report` concurrently from one page-load against a possibly-cold iter-5 scan cache; the two-key non-atomic write at `setups.py:377-378` has a torn-read window (new key paired with a `None` cold result → possible 500). Close it with the in-scope atomic rebind/Lock BEFORE relying on the render, and lock it with the new concurrency test.
- **Lesson iter-2 (Applies to: the J-05 iter — first render of setups events):** the recency-boundary case (a most-recent-session touch whose reaction was read from a truncated sub-horizon beside `None` horizon-0 returns) was resolved in iter-5 by the additive `reaction_boundary_truncated` / `effective_reaction_horizon_bars` fields — the drill-in MUST render these honestly rather than presenting the label as a full-horizon reaction.
- **Lesson iter-4 (Applies to: J-05 rendering the edge report):** do NOT assume the edge report is populated — on the keyless store it may legitimately be empty / all-`insufficient_sample` (the committed `datasets_j03` fixture is symbol PG, not a panel symbol). Render whatever the endpoint returns as an honest first-class state; the populated-cell view is exercised only when a credentialed/panel-symbol recording exists (operator-gated, parallel to J-03).
- **Interpretation call logged** (`runs/goal-session-tradable_wall/state/assumptions.md`, iter-6): "declutter" = raw levels behind an off-by-default toggle; the era-5 Fetch control, provenance badge, Registry, and Comparison sections are preserved intact below the new sections (Foundation invariant + J-07). Reversible.
- **Descriptive copy discipline (critical):** Case Studies and Edge Report copy states conditions and cites measured history only — no imperative/prediction/expected-return language; the frontend copy-discipline lint (bans "win rate", "expected profit", "paper/shadow trading", "annualized", etc.) must stay green. Simulated $ figures carry the "simulated — not indicative of live results" register.
- **Morning-markup / no-lookahead:** the map's `basis_as_of` (prior completed session's close, e.g. 2026-06-18 for the 2026-06-22 session) is enforced server-side; the UI displays it and never feeds forming-bar data into any view.
- Reference: iter-5 `eval.md` next-step recommendation (build J-05 at full depth) and iter-5 `coherence.md` (the `setups.py` cache is a rebuildable accelerator, not a second source — keep it so).
