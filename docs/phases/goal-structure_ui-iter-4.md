# Goal Iteration 4 — Capture populated J-03 evidence; close the goal

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** structure_ui
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-04
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **The Structure UI recomputes nothing.** Every displayed value — level price/timeframe/type, zone class, net R, net $, n, `insufficient_sample`, the champion — is read verbatim from its canonical endpoint. No client-side grading, PnL math, aggregation, or champion resolution. A number that diverges from its API/MCP payload is a defect (trap T10). *(critical)*
  - **No new backend computation or endpoint.** This interlude consumes the existing canonical endpoints; the only backend edit is the additive `/structure` entry in the `meta.py` route registry (the nav owner). It creates no second implementation of any value. *(critical)*
  - **Honest UI states only.** No fabricated chart, level, zone, trade, fill, or PnL to force a green journey; every failure mode (no bar series, no levels, no zones, insufficient n, missing credentials, backend unreachable) surfaces an explicit, distinct state. *(critical)*
  - **The UI never promotes.** The comparison view runs backtests and diffs their reports; it MUST NOT move the champion pointer or write the PnL ledger — promotion remains the sweep's hold-out act. *(critical)*
  - **No vocabulary drift** (trap T9). No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.

## GOAL

Capture independent, populated-state browser evidence that the `/structure` Comparison section renders the `structure_tape`-vs-`v1` comparison honestly, flipping J-03 from `unknown` to `passing` and clearing iter-3's standing CLOSURE-FAIL — so all four Must-have journeys are green.

## BACKGROUND

J-03's Comparison section was fully built in iter-3 (frontend-only; COHERENCE-PASS, review-PASS, and the auditor ran both backtests to `done` live, confirming byte-match + champion-unmoved + ledger-unwritten), but browser-qa recorded **SKIPPED 0/26** and demo-narrator SKIPPED because the frontend was **down** (`http://localhost:3301` unreachable) by the time they ran — so the only screenshots on disk show the pre-run **idle** state and J-03 is `unknown`, not `passing`. This iteration is therefore an evidence-capture / hardening pass with **no code change expected**: bring both services up, curl-confirm them BEFORE dispatching QA, re-run browser-qa to photograph the populated J-03 render, and re-run the closure/ux-regression/audit lanes. Depth is **full** because (a) the evaluator explicitly recommended full and (b) iter-3's standing **CLOSURE-FAIL**, ux-regression-**WARN**, and audit-**PASS_WITH_GAPS** — all opened over the missing populated evidence — can only be cleared by the full pipeline's phase-closure / ux-regression / audit lanes, which a lean cycle (developer → reviewer → browser-qa) omits; this is the goal-closing journey (J-03 passing ⇒ all four green ⇒ GOAL_ACHIEVED candidate). Lessons applied: **iter-3** (confirm `curl :3301` + `:8301/health` respond BEFORE dispatching browser-qa/demo, or the populated render is never photographed and the whole full pass burns for nothing); **iter-0** (a journey with no populated evidence screenshot is `unknown`, never `passing`); **iter-1(b)** (an audit-verified-**live** fix still requires an *independent* browser-QA re-run before `passing`); **iter-1(a)** (lightweight-charts paints canvases at explicit z-index — empty/loading overlays must sit above them).

## IN SCOPE

### Backend
- [ ] No backend code change (frozen foundation). Confirm the `apps/backend/` diff stays byte-empty and `config_fingerprint` recomputes to `4d665603569b9dbf`.

### Frontend (if applicable)
- [ ] No frontend code change expected — the committed 3-section `/structure` page (`apps/frontend/app/structure/page.tsx`) already implements J-03. Make a **minimal, single-file** fix ONLY if browser-qa surfaces a genuine render defect (e.g., a residual lightweight-charts z-index empty-state occlusion like iter-1's), then re-run coherence + audit; otherwise the frontend diff stays empty.

### Evidence capture (the primary work this iteration)
- [ ] Start both services (`bash scripts/dev.sh`) and confirm frontend `http://localhost:3301` **and** backend `http://localhost:8301/health` both return HTTP 200 **before** any browser-qa/demo dispatch. (Ports are the deterministic `dev.sh` sha1 offset = 301 → 3301/8301; read the actual values from `dev.sh`'s startup output and curl-confirm both.)
- [ ] Dispatch browser-qa-agent with services confirmed up; execute the J-03 populated-state cases and write screenshots into `reports/qa/goal-structure_ui-iter-4-evidence/`.
- [ ] Re-run phase-closure-auditor, ux-regression-reviewer, and demo-narrator on the refreshed, populated `ui-test-results.md` to flip iter-3's standing CLOSURE-FAIL → CLOSURE-PASS.

### New user-facing capability
None new. This iteration photographs (independently verifies) the J-03 Comparison capability already delivered in iter-3.

### New information displayed
None new. The populated render shows values already served by `GET /research/backtests/{id}` and `GET /research/pnl/ledger` — all already in the Data Contract.

### New user actions
None new. The dataset selector and "Run comparison" control shipped in iter-3.

### UI surface changes
None. Same 3-section `/structure` page; no new route, no nav change.

### Product surface delta
The already-built J-03 Comparison becomes independently browser-verified and demonstrable end-to-end (dataset chosen → both backtests to `done` → side-by-side aggregates + per-class A/B/C breakdown → honest keyless non-survivor outcome), and the session's closure verdict returns to CLOSURE-PASS.

### Blueprint conformance
`/structure` (Comparison section), under the **Structure** nav home — matches the existing Information Architecture home in `blueprint.md`. No new surface.

### Data-contract additions
None. Every J-03 value (backtest aggregates; per-class `aggregates_by_class` + `insufficient_sample`; the `register` string; the founding-baseline row; the champion pointer; datasets) is already registered to its single canonical owner in `blueprint.md` — the `register` string was registered in iter-3. No new value; `blueprint.md` is unchanged this iteration.

## OUT OF SCOPE

- Any backend computation, endpoint, or edit beyond the already-present additive `/structure` nav-registry entry — frozen foundation.
- Any change that moves the champion pointer or writes the PnL ledger from the UI.
- Fixing `apps/frontend/components/PriceChart.tsx`'s latent z-index empty-state occlusion (carry-forward **F2**, Cockpit/J-04) — pre-existing, non-blocking; this iteration touches neither the Cockpit nor PriceChart, so it is deferred to a future Cockpit-touching iteration.
- Building a `/datasets` library-inventory page (Card 5.9 scope; explicit Non-Goal).
- Any new journey or scope beyond J-03 verification; the goal-proposer must not append work here.
- README/showcase copy expansion beyond what demo-narrator/readme-maintainer regenerate (the stale "Structure page" README bullet is an advisory note, not a blocker).

## DEFINITION OF DONE

- [ ] **J-03 passes via browser-qa-agent** — independent, populated-state screenshots in `reports/qa/goal-structure_ui-iter-4-evidence/` show: a dataset chosen; both `v1` and `structure_tape` backtests polled to `done`; side-by-side aggregates (n, net R, net $, `win_rate`, `max_drawdown_r`) byte-matching a live `GET /research/backtests/{id}`; the per-class A/B/C `insufficient_sample` chips; the verbatim `register` string; the champion unchanged at `v1`/`default`; and the keyless `structure_tape` non-survivor outcome (`n=0` → "no trades (n=0)").
- [ ] Required-still-passing **J-01** (populated chart + A/B/C zones, chart un-occluded), **J-02** (registry + champion badge), **J-04** (5-link nav, `/performance` intact) each re-verified green with iter-4 evidence.
- [ ] `apps/backend/` diff byte-empty; `config_fingerprint` recomputes to `4d665603569b9dbf`.
- [ ] No anti-goal violation introduced (scan CLEAN; champion unmoved; ledger unwritten; register read verbatim from payload; no vocabulary drift; no fabricated chart/level/zone/trade/PnL).
- [ ] Coherence returns COHERENCE-PASS; audit returns PASS or PASS_WITH_GAPS; ux-regression returns UX-REGRESSION-PASS (iter-3's WARN was raised over the then-missing populated evidence, now supplied); **phase-closure returns CLOSURE-PASS**, clearing iter-3's standing CLOSURE-FAIL.
- [ ] Backend unit suite green (≈1146 passed / 1 skipped); frontend copy-discipline lint green; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-structure_ui-iter-4-dev.md`.

## TESTING REQUIREMENTS

- **Precondition (mandatory — this is exactly why iter-3 burned):** confirm `curl -sf http://localhost:3301` (frontend) **and** `curl -sf http://localhost:8301/health` (backend) BOTH return 200 immediately BEFORE dispatching browser-qa-agent and demo-narrator. If either is down, bring it up (`bash scripts/dev.sh`) and re-confirm. Do NOT run browser-qa against a down frontend — that produced the iter-3 SKIPPED 0/26.
- **Browser:**
  - **J-03** (populated Comparison): dataset chosen → both backtests polled to `done` → side-by-side aggregates byte-matching `GET /research/backtests/{id}` → per-class A/B/C `insufficient_sample` chips → verbatim `register` string → champion unchanged `v1`/`default` → keyless `structure_tape` non-survivor (`n=0` → "no trades (n=0)").
  - **J-01** re-verify: populated chart + A/B/C confluence zones, chart overlay un-occluded (z-index above the lightweight-charts canvases).
  - **J-02** re-verify: `v1` + `structure_tape` cards with class-scaled maps; champion `v1`/`default` badged.
  - **J-04** re-verify: 5-link data-driven nav; `/performance` intact.
  - If practical while services are up, exercise ≥1 honest degraded state (backtest `failed` / `cancelled` / comparison poll-error / no-datasets) — non-blocking.
- **Unit/integration:** backend suite must stay green (≈1146 passed / 1 skipped) as a regression guard; no code-path change expected. Frontend copy-discipline lint must stay green.
- **Error cases:** the honest degraded states (no bar series, no levels/zones, insufficient n, backend unreachable, poll error) must each render an explicit, distinct state; verify at minimum the insufficient-n keyless non-survivor path (the committed reference dataset's `structure_tape` `n=0` → all per-class rows `insufficient_sample=true`).

## NOTES

- **Depth = full** (prior verdict CONTINUE, prior depth full). Justified by the evaluator's explicit `full` recommendation plus the standing CLOSURE-FAIL / ux-regression-WARN / audit-PASS_WITH_GAPS from iter-3, which only the full-pipeline closure/ux-regression/audit lanes can clear; this is the goal-closing journey.
- **#1 risk (root cause of iter-3):** browser-qa/demo ran while the frontend was down. Mitigation is the hard curl precondition above. The orchestrator/developer MUST bring services up and confirm both respond before QA dispatch.
- **Second attempt at populated J-03 evidence.** The first (iter-3) SKIPPED for services-down. If — and only if — the services genuinely cannot be started (a real environment blocker), surface it explicitly as a STALLED-class human-owned blocker rather than advancing on another SKIP. Do NOT accept a developer self-run or an idle-state `qa`-captured screenshot as the DoD's populated evidence (iter-0 / iter-3 lessons).
- **Lessons applied (episodic memory):** iter-3 (services-up + curl-confirm before QA); iter-0 (no populated screenshot ⇒ `unknown`); iter-1(b) (audit-verified-live ≠ `passing`; independent browser-QA re-run required); iter-1(a) (lightweight-charts overlays need explicit z-index above the canvases — watch the populated J-03/J-01 chart overlays for residual occlusion); iter-2 (diff-scope: evaluate with `git diff <snapshot>` / `git status --short`, never a two-dot `snapshot..HEAD` range — iter-4's own changes, if any, are uncommitted at eval time).
- **Carry-forward F2 (non-blocking, out of scope):** `apps/frontend/components/PriceChart.tsx` (Cockpit/J-04) shares the latent z-index empty-state occlusion fixed on StructureChart in iter-1 — defer to a future Cockpit-touching iteration.
- **Advisory (non-blocking):** the README "Structure page" bullet documents only J-01 levels/zones and is stale re: the shipped Registry (J-02) + Comparison (J-03); demo-narrator/readme-maintainer may refresh it, but it does not block J-03.
- **Blueprint:** unchanged this iteration — no new displayed value, no nav change (Data-contract additions = none).
