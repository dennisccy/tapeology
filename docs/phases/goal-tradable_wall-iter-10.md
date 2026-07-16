# Goal Iteration 10 — Observe the warm-cache Edge Report render (close J-08's last DoD element)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 10
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid, publishable outcome. *(critical)*
  - **The champion moves only through the existing sweep gate on hold-out data.** This era may feed the gate; it never hand-promotes `structure_tape_map` or anything else. *(critical)*
  - **Feed honesty — never pool across feeds.** The `feed` stamp comes verbatim from the adapter/key tier; `iex`, `sip`, and Yahoo-bar lineages are never pooled in any analysis cell, report row, or claim; `iex` is never presented as the consolidated tape. *(critical)*
  - **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)*
  - **No new nav entry** — the era lives inside `/structure` and the cockpit; no new page.
  - **No vocabulary drift.** No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.

## GOAL

On a warm cache, `/structure`'s Edge Report section renders its RESOLVED state — the three-way register cells or the honest all-`insufficient_sample`/empty state — within an interactive budget, browser-observed and opened, closing J-08's last DoD element and making all eight journeys passing.

## BACKGROUND

J-08's rebuildable, checksum-keyed edge-report result cache was built and independently evaluator-verified in iter-9 (warm==fresh byte-identity, second-call-never-recomputes, restart durability, route warm-serve, no train/hold-out & no feed pooling, concurrency/torn-read guard). But J-08 landed **partial, not passing** because its DoD item 1 — a *browser-observed warm-cache render* — was never delivered: the iter-9 browser-QA ran against the shared pipeline backend pointed at the **real corpus** (11 credentialed `sip` datasets), where `GET /research/edge-report` triggers a genuine cold ~10h compute, so the cache stayed empty all session and the only Edge Report screenshot (UT-01) showed the pulsing loading skeleton; UT-02/03/06 were SKIPPED. This warm render has now gone un-observed for three consecutive iterations (6/8/9), and J-08 exists precisely to close that gap.

This iteration follows the iter-9 evaluator's explicit recommendation and the iter-9 lesson verbatim: point the browser-QA backend at a **SCOPED, KEYLESS dataset dir** (`TAPEOLOGY_DATASET_DIR` + a scoped `TAPEOLOGY_EDGE_REPORT_CACHE_DB`) so the endpoint warms in seconds, pre-warm the durable cache once, then browser-QA opens the RESOLVED render. Depth is **lean** (evaluator-recommended; prior verdict CONTINUE not ESCALATE; **no product-computation change** — the render path is unchanged, already-verified J-05 code; the lean cycle's browser-qa step is exactly the missing evidence). Two iter-9 coherence-WARN advisories are folded in while here (blueprint pnl_ledger registration — already done in `blueprint.md`; the `band side` column rename in `pnl_ledger.py`).

## IN SCOPE

### Backend
- [ ] **(Verification harness — not product computation.)** Provision the browser-QA backend against a SCOPED KEYLESS dataset dir: start it with `TAPEOLOGY_DATASET_DIR` pointed at a small committed keyless dataset set (the committed `datasets_j03/` fixture and/or a committed keyless reference dataset) and a scoped/throwaway `TAPEOLOGY_EDGE_REPORT_CACHE_DB`, so `GET /research/edge-report` computes in **seconds** instead of the real-corpus ~10h path. **Pre-warm** the durable cache once (a single compute over the scoped store) BEFORE the browser pass so the observed render is the *warm-cache* path. Document the exact backend-start command + env + pre-warm step in the dev handoff so browser-QA reproduces it deterministically.
- [ ] **Cosmetic labeling fix (iter-9 coherence-WARN advisory b), `apps/backend/app/research/pnl_ledger.py`:** in `_render_strategy_comparison_row_lines`, rename the 3-way `strategy_comparison` table's column header from `side` to `band side` (the column holds `cell["band_side"]` = `support`/`resistance`, colliding with the pre-existing two-way row's role `side` = `baseline`/`candidate`), and correct the same function's docstring which claims the table is built "WITHOUT a `side` column" — contradicting the header it emits. Update the matching `test_pnl_ledger.py` assertion(s) to expect `band side`. Existing two-way rows must render **byte-identical**; committed `reports/pnl/pnl-history.md` is untouched.

### Frontend (if applicable)
- [ ] **No product code change expected.** The `/structure` Edge Report render path is unchanged, already-verified J-05 code (plain `fetch` + verbatim render — the same code path handles both the slow and the fast case, confirmed by the iter-9 frontend handoff + coherence audit). Do NOT touch it unless the RESOLVED state genuinely fails to render once the endpoint returns fast; any such fix stays minimal, read-only, and recomputes nothing client-side. Expected: a no-op.

### New user-facing capability
On a warm cache the operator can actually READ the Edge Report on `/structure` — the section RESOLVES (three-way register cells, or the honest all-`insufficient_sample`/empty state) within an interactive budget instead of sitting on an indefinite loading skeleton. (The cache that makes this possible shipped in iter-9; iter-10 makes it observably true in the browser.)

### New information displayed
None new. The same edge-report cells (`v1` / `structure_tape` / `structure_tape_map`, per class × side × reaction, n / R / $ with the full register + null baseline + "simulated — not indicative of live results") served verbatim by `GET /research/edge-report`, now rendered RESOLVED rather than perpetually loading.

### New user actions
None.

### UI surface changes
None. No new page, panel, or section — the existing `/structure` Edge Report section renders its resolved state.

### Product surface delta
`/structure`'s Edge Report moves from "perpetually loading against the real corpus" to "resolves fast on a warm cache" — the report becomes usable. Cosmetically, the operator-facing `pnl-history.md` 3-way table's band-level column is disambiguated to `band side`.

### Blueprint conformance
All work lives under the existing **Structure** nav home → `/structure` → **Edge Report** section (`blueprint.md` IA, unchanged). Nav stays frozen (anti-goal "No new nav entry"). Additive blueprint edit already made this iteration: the pre-existing `pnl_ledger.py` owner is now registered in the "Existing owners Era 5B reads verbatim" Data Contract table (closes iter-9 coherence-WARN advisory a).

### Data-contract additions
**None** — no new displayed value, no new endpoint, no new computation path. The `pnl_ledger.py` registration is a completeness backfill of a PRE-EXISTING owner (era-3 Data Contract row 32) that iter-9 began additively extending — an existing owner, now registered in `blueprint.md`, not a new value. The `band side` header is a cosmetic re-label of the existing `band_side` cell field (owned by `edge_report.py`'s cells, composed verbatim by `pnl_ledger.py`) — no new value, no second computation, no second source.

## OUT OF SCOPE

- The first REAL ~10h corpus warm over the 11 credentialed `sip` datasets and its real append to `reports/pnl/pnl-history.md` (via `python -m app.research.pnl_history --append-report …`) — operator-gated carry; does NOT block J-08 passing.
- Adding a `/structure` render path for the new `strategy_comparison` ledger row kind (audit §5) — deferred; `pnl-history.md` is an operator-run report, not a page.
- Any credentialed Alpaca call, any live Yahoo fetch, any real-corpus edge-report warm.
- Any change to `edge_report.py`'s computation, the cache key/logic (`edge_report_cache.py`), `levels.py`, `setups.py`, `tradability.py`, `backtests.py`, `strategies.py`, `config.py`, the tape engine, the champion pointer, or `config_fingerprint 4d665603569b9dbf`.
- Scoping/shrinking the BAR store or the Case Studies (`setups`) scan — only the recorded-tick `DatasetStore` (the edge-report's input) is scoped for the browser pass; the Case Studies table renders from the real bar store as before.
- Any new statistical / era-6 "Referee" machinery; any execution path of any kind.

## DEFINITION OF DONE

- [ ] **J-08 passes via browser-qa-agent:** on a WARM cache, `/structure`'s Edge Report section renders the RESOLVED state (the three-way register cells OR the honest all-`insufficient_sample`/empty state) within an interactive budget — NOT the loading skeleton — and the screenshot (or DOM-text capture for the deep-scroll section) is OPENED and confirms the resolved state, read verbatim from `GET /research/edge-report` with zero client recomputation.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06, J-07 remain green (re-verified: frozen-file diff-absence + `config_fingerprint 4d665603569b9dbf` + browser read-surface checks).
- [ ] No anti-goal violation introduced (scan-report CLEAN; no credential in the diff; `edge_report.py` computation byte-identical; champion pointer untouched; empty/all-`insufficient_sample` report served honestly, never fabricated).
- [ ] Existing two-way `pnl-history` rows render byte-identical after the `band side` rename; committed `reports/pnl/pnl-history.md` untouched; updated `test_pnl_ledger.py` green.
- [ ] `blueprint.md` registers the `pnl_ledger.py` owner (iter-9 coherence-WARN advisory a — done).
- [ ] Unit tests pass; no regressions — full backend suite green; no test deleted or weakened.
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-10-dev.md`, documenting the exact scoped-keyless browser-QA backend start command + env (`TAPEOLOGY_DATASET_DIR`, `TAPEOLOGY_EDGE_REPORT_CACHE_DB`) + pre-warm step.

## TESTING REQUIREMENTS

- **Browser (primary):** **J-08** — `/structure` Edge Report section resolves on a warm cache within an interactive budget (the crux — this is what iters 6/8/9 missed). Re-verify **J-05** (Tradable Map default + raw-levels toggle off-by-default), **J-02** (Case Studies registry + drill-in), **J-01** (pinned resistance band 300.x in the Tradable Map, top-2 by score, `06-18` basis), **J-06** (cockpit band overlay + descriptive confluence chip; SIM honest "no tradable map" empty state; live mode hides the PriceChart). Run against the scoped-keyless backend so the edge-report resolves fast. For the **deep-scroll** Edge Report section (the `/structure` page is 8,000–33,000px tall — Case Studies renders all rows), fall back to DOM-text (`innerText`) extraction if the screenshot is blank/double-exposed (iter-6 lesson) — that is a legitimate pass, NOT a SKIP.
- **Unit/integration:** the `band side` rename — existing two-way rows byte-identical, the new 3-way row emits `band side`, docstring corrected; the existing edge-report determinism (warm==fresh byte-identical) + concurrency (no torn read) + no-train/hold-out-pool + no-feed-pool + champion-untouched tests stay green; `config_fingerprint 4d665603569b9dbf` equivalence green.
- **Error cases:** a cold-cache page-load renders an honest loading state then resolves (no crash / no torn read); an empty/all-`insufficient_sample` edge report renders the honest empty state (not an error); the MCP `edge_report` proxy stays byte-identical to `GET /research/edge-report`.

## NOTES

- **Depth = lean** justified: evaluator-recommended (iter-9 eval); prior verdict CONTINUE (not ESCALATE); no product-computation change; narrow scope. The lean cycle (developer → reviewer → browser-qa-agent) includes exactly the browser-qa step that delivers the missing warm-render evidence.
- **LESSON (iter-9 — directly applicable, the reason this iteration exists):** "A proposer-created 'make X observable' journey is not met until X is actually OBSERVED — route-level warm-serve tests + unchanged render code do NOT substitute for the browser warm-RENDER the DoD names… An 'observability' iteration MUST provision a SCOPED, keyless dataset dir (`TAPEOLOGY_DATASET_DIR` + `TAPEOLOGY_EDGE_REPORT_CACHE_DB`) for the browser pass to warm-up in seconds — relying on the real-corpus backend guarantees the loading carve-out recurs." Do NOT accept unit/route proof as the browser render evidence; the screenshot/DOM-capture of the resolved state is the evidence.
- **LESSON (iter-6):** `/structure` renders all Case Studies rows (page 8,000–33,000px); Chrome MCP screenshots can go blank/double-exposed at deep scroll — browser-QA falls back to DOM-text (`innerText`) extraction for the deep Edge Report section (a legitimate pass). Anchor acceptance on the goal's structural criterion (resolved state, verbatim cells), not a numeric snapshot.
- **LESSON (iter-8) — this is a GOAL_ACHIEVED-candidate iteration:** if the QA lane reports Chrome/browser infra failure, the evaluator must open the separately-dispatched browser-qa-agent's own results file (`reports/phase-goal-tradable_wall-iter-10-ui-test-results.md`) before down-scoring J-08; and the honest all-`insufficient_sample`/empty resolved render is an EXPLICITLY VALID pass (goal Success Criterion 5 + anti-goal "No gate bending for a headline") — do NOT require populated real-corpus cells.
- The empty/all-`insufficient_sample` resolved render is a valid J-08 pass; the populated real-corpus cells remain the operator-gated carry (OUT OF SCOPE). This executes the already-established keyless-core-with-observed-warm-render reading (assumptions.md iter-8/iter-9) — **no new assumption logged**.
- On success, all eight journeys are passing → the evaluator can score **GOAL_ACHIEVED** (subject to the deterministic achievement gate + fresh-context two-key confirm). This is the first key; the outer loop re-verifies.
- **coherence:** iter-9 was COHERENCE-WARN (advisory, not FAIL — no consolidation owed). This iteration RESOLVES both WARN advisories (blueprint pnl_ledger registration + the `band side` rename), improving the coherence posture toward COHERENCE-PASS for the GOAL_ACHIEVED gate.
