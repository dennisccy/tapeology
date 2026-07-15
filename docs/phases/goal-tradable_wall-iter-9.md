# Goal Iteration 9 — Edge report becomes observable: a rebuildable, checksum-keyed result cache

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes (the warm-cache `/structure` Edge Report render is browser-verifiable; **no frontend code change is expected** — the section already reads `GET /research/edge-report` verbatim from J-05, so frontend work is verify-only unless the warm render needs a minor observable-state/timeout tweak)
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid, publishable outcome. *(critical)*
  - **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Make the era's central "what actually profits" deliverable observable: wrap `edge_report.py`'s ~10+h backtest sweep in a rebuildable, dataset-checksum-keyed result cache so `GET /research/edge-report` (and its MCP proxy) return the full 3-way register within an interactive time budget on a warm cache — byte-identical to a fresh compute, never a second source of truth, champion untouched.

## BACKGROUND

Era 5B reached GOAL_ACHIEVED at iter-8 (deterministic gate PASS + two-key CONFIRM_ACHIEVED); the enhancement loop's goal-proposer then appended **J-08** inside the `AUTO:journeys` block to close the single real usability limitation the iter-8 evaluator, the auditor (audit B2), and the iter-8 lesson all independently named: `GET /research/edge-report` is a documented ~10+h uncached compute over ~9.1M ticks, so the populated Edge Report cells were never observed end-to-end — UT-13/14/15 resolved only to the sanctioned "still loading, backend at 98% CPU" carve-out. J-08 adds a rebuildable result cache around `run_strategy_comparison_report` (`edge_report.py:426`) mirroring the two established rebuildable-accelerator precedents — the in-process atomic `_SCAN_CACHE` (`setups.py:369-408`) and the persisted derived `bar_index` (`bar_index.py`) — so the first (operator-run) full compute is not repeated on every request or backend restart, making the report and every future proposer survivor-screen observable for the first time. **Depth is full** because multiple independent triggers fire: (1) it requires new tests beyond browser smoke (a determinism/byte-identity test and a concurrency/torn-read test); (2) it modifies the serving path of a canonical single-source-of-truth value (edge-report cells) — coherence-critical, the auditor must confirm the cache is an accelerator and not a second source; (3) concurrency correctness is subtle — this is the exact iter-5 torn-read hazard, now on the edge-report endpoint; (4) it adds a durable/persisted cache artifact (structural). This is the natural post-goal hardening pass, not a manufactured journey.

## IN SCOPE

### Backend
- [ ] Add a **rebuildable result cache** around `run_strategy_comparison_report` in `apps/backend/app/research/edge_report.py` (the sweep at `edge_report.py:426`). The cost being cached is the `BacktestJobManager` runs over the recorded event-window datasets for all three strategies (`v1` / `structure_tape` / `structure_tape_map`) — **NOT** the already-memoized `compute_setups` scan (`setups.py` `_SCAN_CACHE`), which stays as-is.
- [ ] Key the cache on the **`DatasetStore` per-dataset checksums** (append-only / immutable) **+ the strategy registry + `config_fingerprint` (`4d665603569b9dbf`)**. Any change to the dataset set, the registry, or the config busts the key and forces a byte-identical recompute.
- [ ] Make the cache **durable across backend restart** — a persisted, rebuildable derived artifact mirroring the `bar_index` precedent (so the first operator-run full compute is not re-triggered on restart or on every request), with an **atomic publish / torn-read guard** mirroring the iter-6-hardened `_SCAN_CACHE` single `(key, result)` tuple rebind + read-local-reference-before-inspect pattern (`setups.py:357-408`). `edge_report.py` stays the **SOLE computer**; the cache is a rebuildable accelerator, **never a source of truth**; a miss recomputes byte-identically.
- [ ] `GET /research/edge-report` and its read-only MCP proxy `edge_report` keep serving `run_strategy_comparison_report`'s output **verbatim through the cache** — one owner, one endpoint, no second computation path, zero client recomputation.
- [ ] Wire the **PnL-history append path** through the existing owner `apps/backend/app/research/pnl_history.py` → `reports/pnl/pnl-history.md`: build + unit-test (keyless) the code that, given a completed 3-way comparison, appends `v1` (null/baseline) vs `structure_tape` vs `structure_tape_map` per split with **train and hold-out never pooled** and **feeds never pooled**, each cell carrying net R, net $, n, fee/slippage assumptions, basis, null baseline, and the visible "simulated — not indicative of live results" register; n<5 cells labelled `insufficient_sample` (an all-`insufficient_sample` outcome is valid and still recorded). *(The append MACHINERY is agent-buildable and tested keyless; the actual append of the first **real** ~10+h compute is the operator-gated carry — see OUT OF SCOPE.)*
- [ ] New tests (see TESTING REQUIREMENTS): a **determinism/byte-identity** test (warm-cache report == fresh cache-cleared compute over the same store) and a **concurrency** test (a cold-cache concurrent read never observes a torn / half-written result). No existing test deleted or weakened.

### Frontend (verify-only — no code change expected)
- [ ] Confirm `/structure`'s **Edge Report** section renders the now-observable cells (or the honest all-`insufficient_sample`/empty state) **verbatim** from `GET /research/edge-report` within the interactive budget on a warm cache, with zero client recomputation. Add a frontend change ONLY if browser-QA finds the warm render needs an observable-state/timeout adjustment; do not touch J-05's other surfaces.

### New user-facing capability
The operator (and any UI/MCP reader) can retrieve the full 3-way edge report in interactive time on a warm cache instead of waiting ~10+h — the era's headline "what actually profits" answer becomes observable, and the honest PnL register can be recorded to history.

### New information displayed
None new in kind. The **same** edge-report cells (already owned by `edge_report.py`, served by `GET /research/edge-report`) simply become observable within an interactive budget. The first real 3-way comparison is recorded to the existing `reports/pnl/pnl-history.md` ledger (existing owner).

### New user actions
None. No new button, form, or control — the existing `/structure` Edge Report section and the existing endpoint/MCP proxy are unchanged in surface; only response latency (warm cache) changes.

### UI surface changes
None. No new page, panel, or nav entry (nav frozen for Era 5B). The existing Edge Report section on `/structure` is unchanged in structure.

### Product surface delta
The Edge Report goes from "honest-but-perpetually-loading" (a ~10+h carve-out) to observable within seconds on a warm cache — the one product experience gap flagged at GOAL_ACHIEVED closes, and future proposer runs can finally screen a completed survivor report.

### Blueprint conformance
No new surface. J-08 lives inside the existing `/structure` → **Edge Report** home (Structure nav section) and the existing `GET /research/edge-report` owner — both already registered in `blueprint.md`. No nav-skeleton change; no re-approval requested.

### Data-contract additions
None — no new displayed value and no second computation. The edge-report cells value keeps its single owner (`edge_report.py`) and single endpoint (`GET /research/edge-report`). This iteration adds only an **additive cache annotation** to that existing Data-Contract row in `blueprint.md` (mirroring the setups row's `_SCAN_CACHE` note): the sweep is memoized behind a rebuildable, checksum+registry+fingerprint-keyed durable cache that is byte-identical to a fresh compute and is an accelerator, never a source of truth. The PnL-history append targets the existing `pnl_history.py` → `reports/pnl/pnl-history.md` ledger (existing owner) — not a new value.

## OUT OF SCOPE

- **The first full REAL ~10+h compute over the credentialed corpus and its append to `reports/pnl/pnl-history.md`** — this is the operator-gated carry (parallel to J-03/J-04's credentialed carve-outs). The cache MACHINERY, its determinism/concurrency/equivalence tests, and the append CODE are all agent-buildable and verified keyless this iteration; the operator warms the cache once (running the real compute over the 11 durable `sip` datasets already on disk) and that append lands the real register. Do not simulate the real compute; do not score the real pnl-history append "met" from a handoff narration (iter-3 lesson).
- **Any change to `edge_report.py`'s computation, `levels.py`, `setups.py`, `tradability.py`, `v1`, `structure_tape`, `structure_tape_map`, the `default` profile, or `config_fingerprint`** — the cache is additive only; every one stays byte-identical (equivalence test green).
- **Any champion promotion / sweep-gate change** — the champion pointer is untouched; making the report observable never promotes.
- **Recording new datasets / enlarging the window library** — explicitly backlogged by the proposer (premature + operator-gated); not this iteration.
- **Any era-6 statistical machinery** (bootstrap CIs, multiple-testing control), any `/datasets` UI, any new nav entry, any execution/live-mode change.

## DEFINITION OF DONE

- [ ] Target journey **J-08 passes via browser-qa-agent**: on a warm cache, `/structure`'s Edge Report section renders the 3-way register (populated cells if warmed over the real corpus, or the honest all-`insufficient_sample`/empty state) verbatim from `GET /research/edge-report`, within an interactive time budget, with zero client recomputation (screenshot opened, or DOM-text extraction for deep-scroll sections per the iter-6 lesson).
- [ ] **Determinism test green:** the warm-cache report is **byte-identical** to a fresh cache-cleared compute over the same store (verified on a store that produces a NON-degenerate report shape — a populated all-`insufficient_sample` cell structure via the real datasets or the `test_synthetic_scan_join_...` panel-override pattern, per the iter-4 lesson — not merely an empty `cells: []`).
- [ ] **Concurrency test green:** a cold-cache concurrent read never observes a torn / half-written result (mirrors `setups.py`'s atomic-publish guard; bites under the exact concurrent cold-cache scenario, per the iter-5 lesson).
- [ ] **Cache correctness:** keyed on dataset checksums + strategy registry + `config_fingerprint`; rebuildable and durable across a backend restart; any dataset/registry/config change busts the key; a miss recomputes byte-identically; the cache is never read as a source of truth.
- [ ] **Single source of truth intact:** `edge_report.py` remains the sole computer and `GET /research/edge-report` the single endpoint; the MCP `edge_report` proxy stays **byte-identical**; coherence-auditor returns COHERENCE-PASS (cache is an accelerator, not a second source).
- [ ] **Frozen foundations byte-identical:** `edge_report.py`'s computation, `levels.py`, `setups.py`, `tradability.py`, `v1`, `structure_tape`, `structure_tape_map`, the `default` profile, and `config_fingerprint` `4d665603569b9dbf` all unchanged (equivalence test green; independently recompute the fingerprint); the **champion pointer is untouched**.
- [ ] **PnL-history append path** built and unit-tested keyless: given a completed comparison it appends the per-split register (net R, net $, n, assumptions, basis, null baseline, "simulated — not indicative of live results", `insufficient_sample` for n<5, train/hold-out and feeds never pooled). *(The real-corpus append itself is the operator-gated carry.)*
- [ ] Required-still-passing journeys **J-01, J-02, J-03, J-04, J-05, J-06, J-07 remain green** (deterministic golden replay; refresh golden scripts on this full-regression pass).
- [ ] No anti-goal violation introduced (scan-report CLEAN; no credential/paid-SaaS/vocabulary drift; descriptive-only).
- [ ] Full backend unit/integration suite passes (new determinism + concurrency tests added; **no test deleted or weakened**); no regressions.
- [ ] A **`[NEW]`-flagged demo-narrator walkthrough** shows `/structure`'s Edge Report section rendering the now-observable cells (or the honest all-`insufficient_sample` state) verbatim from the endpoint.
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-9-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):** verify **J-08** — `/structure` Edge Report section renders the warm-cache report verbatim within the interactive budget (open the screenshot; fall back to `innerText`/DOM-text extraction for deep-scroll Edge Report / registry sections, which the iter-6 lesson documented go blank at deep scroll offsets). Re-verify the **J-05** page shell (Tradable Map default + off-by-default raw toggle + Case Studies) and **J-06** cockpit chip/overlay are unregressed. Use the real state vocabulary `{buyer_control, seller_control, bid_absorption, ask_absorption, unclear}` and the pinned event id `13e24a2f185b1299` (not the 32-hex dataset id, which 404s) per the iter-8 QA-plan T3 correction.
- **Unit/integration (must have tests):** the new cache module/path in `edge_report.py` — determinism/byte-identity (warm == fresh cache-cleared), key-busting (dataset checksum change, registry change, config change each force recompute), durability across a simulated restart, and the concurrency/torn-read guard; the `pnl_history.py` append format (full register, no pooling, `insufficient_sample` gating); the MCP `edge_report` byte-identity proxy test; the `config_fingerprint == 4d665603569b9dbf` equivalence test and the frozen-strategy/`default`-profile byte-identity tests must stay green.
- **Error cases:** a stale/mismatched cache key (dataset added/removed, registry or config changed) MUST recompute rather than serve a stale result; a torn/half-written cache entry MUST NOT be served; a cold cache with no completed compute MUST surface the honest loading/empty state, never a fabricated or partial report; n<5 cells MUST be labelled `insufficient_sample` (never rolled into a pooled headline).

## NOTES

- **Lessons applied (from `lessons.md`):**
  - *iter-5 (torn-read):* an in-process memoization proven only by single-threaded byte-identity tests can hide a torn-read that appears under the concurrency the next caller introduces. The cache's publish MUST be the atomic `(key, result)` tuple rebind + read-local-reference-before-inspect pattern already shipped for `_SCAN_CACHE` (`setups.py:357-408`), and the concurrency test must bite under a genuinely concurrent cold-cache read.
  - *iter-4 (fixture predates feature):* the committed `datasets_j03/` fixture (symbol `PG`, not a panel symbol) yields `cells: []` under the real panel, so prove byte-identity/determinism on a store that actually produces a NON-degenerate report shape (real datasets, or the `test_synthetic_scan_join_produces_real_cells_all_insufficient_sample` panel-override), not just the empty shape.
  - *iter-3 (credentialed durability):* do not score the operator-gated real-corpus pnl-history append "met" from a handoff narration or a "documents the outcome" QA check — require the persisted append + a clean native test.
  - *iter-8 (stale audit vs browser-QA; long endpoint):* J-08 exists precisely to eliminate the ~10+h "still computing" carve-out for the warm path — the warm-cache render must be observed in a real browser (open the screenshot), not left to a loading carve-out; and check the separately-dispatched browser-qa-agent result directly before down-scoring.
  - *iter-6 (deep-scroll screenshots):* `/structure` renders tall; browser-QA should expect blank deep-scroll frames and fall back to DOM-text extraction, and anchor acceptance on the structural criterion (register present + verbatim) not a mutable numeric snapshot.
- **Interpretation call (logged to `assumptions.md` iter-9):** J-08's passing bar is its **keyless core** (cache machinery + determinism + concurrency + byte-identity/equivalence + the warm-cache render + the append machinery), with the first **real** ~10+h compute and its pnl-history append treated as the operator-gated carry — mirroring the iter-4 J-04 reading. A human who requires the real compute + real pnl-history append before J-08 passes could reverse this to `partial`.
- **Proposer provenance:** J-08 was promoted by the goal-proposer (`enhancement-proposals.jsonl` id `edge-report-result-cache`, score 0.75) as a structural/pipeline-enabling enhancement — permitted because no hold-out survivor is currently observable (the ~10+h report has never completed). The companion `enlarge-recorded-window-library` proposal was correctly NOT promoted (premature + operator-gated). J-08 was appended only inside the `AUTO:journeys` marker block; the human-authored journeys and Anti-goals section are untouched.
- **Coherence focus for the auditor:** confirm the cache is a rebuildable accelerator keyed on immutable inputs — one computer (`edge_report.py`), one endpoint, byte-identical served output — and NOT a second source of truth or a parallel computation path (anti-goal #6, which the coherence-auditor hard-fails).
