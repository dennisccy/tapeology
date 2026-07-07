# Goal Iteration 2 — Strategy registry & champion on `/structure` (J-02) + close J-01

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** structure_ui
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02
- **Required-still-passing journeys:** J-04
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
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

On the existing `/structure` page, the user can see the strategy registry (`v1` and `structure_tape` with their config-owned parameters) and the badged founding champion — every value read verbatim from `GET /research/strategies` / `GET /research/profiles` — and J-01's levels/zones surface is independently re-verified and closed to `passing`.

## BACKGROUND

Iteration 1 built J-01 (`/structure` levels/zones); the evaluator left it **`partial`**, not `passing`: the levels-but-no-zones state rendered a silent blank chart (critical honest-state violation), the auditor fixed it in-tree (`StructureChart.tsx:99` `z-10`, present now), but the independent browser-QA lane never re-ran and phase-closure was CLOSURE-FAIL over three contradictory records. Per lessons.md iter-1(b), **an auditor's in-place fix is not "done" until browser-QA re-runs independently and the records reconcile** — so this iteration re-verifies J-01's levels-but-no-zones state on the current fixed code and drives it to a CLOSURE-PASS, then builds J-02 (the next journey in the goal's J-01→J-02→J-03 order) as a new Registry section of the same page. Depth is **full** for two rubric-anchored reasons: (1) closing J-01 requires the **phase-closure + ux-regression** steps, which exist only in the full 11-step pipeline and not in the lean cycle (developer→reviewer→browser-qa) — a lean iteration structurally cannot produce a CLOSURE-PASS; and (2) J-02 surfaces the **champion pointer**, a critical frozen-foundation value that must be read verbatim and moved never, so the verbatim/single-source-of-truth check needs the **coherence + audit** lanes (tests beyond browser smoke) — and iter-1 proved those lanes catch honest-state defects the dev/review/offline-QA lanes miss. The prior evaluator's next-step recommendation was exactly this (full; close J-01, then build J-02).

## IN SCOPE

### Backend
- [ ] **None.** `GET /research/strategies` (`apps/backend/app/research/strategies.py` → `{"strategies": config.strategy_registry(), "champion": store.get_champion_pointer()}`) and `GET /research/profiles` (`apps/backend/app/research/profiles.py` → `{"profiles": config.profile_registry(), "champion": store.get_champion_pointer()}`) already serve the registry and the champion verbatim from their single owners. This iteration adds **zero** backend code — no new endpoint, no new computation, no champion write.

### Frontend
- [ ] Add a `Strategy` + `StrategiesPayload` type to `apps/frontend/lib/types.ts` mirroring the served `GET /research/strategies` shape (`strategies: Strategy[]` with each strategy's config-owned fields — entry rule, exit precedence, and `structure_tape`'s `stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class`; `champion: { strategy_id, profile }`). Reuse the existing `ProfilesPayload.champion` shape (`{ strategy_id: string; profile: string }`) — do not define a second champion shape.
- [ ] Add `fetchStrategies()` to `apps/frontend/lib/api.ts`, mirroring the existing `fetchProfiles()` pattern (verbatim read of `GET /research/strategies`; on any non-200/unreachable, return an explicit unavailable state — `strategies: null` — never a fabricated registry).
- [ ] Add a **Registry** section to `apps/frontend/app/structure/page.tsx` (below the existing Levels & Zones section): render `v1` and `structure_tape` as two cards showing each entry rule, the exit precedence (`r_stop → reward_target → state_flip → horizon`), and `structure_tape`'s class-scaled `stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class` — every field printed verbatim from the payload (via `String(value)`, the page's established precedent), no client-side reconstruction.
- [ ] Badge the champion from `champion.strategy_id` / `champion.profile` (founding `v1`/`default`), cross-read against `GET /research/profiles` (`fetchProfiles()` already exists); the two views must agree because both read the same store pointer — surface an honest state if either endpoint is unavailable rather than hardcoding `v1`/`default`.
- [ ] J-01 close: **no new code expected** — the `StructureChart.tsx:99` `z-10` overlay fix is already in the tree. If browser-QA re-verification of the levels-but-no-zones state surfaces any residual occlusion, fix it in `apps/frontend/components/StructureChart.tsx` (give the empty-state overlay an explicit z-index above the `lightweight-charts` canvases, per lessons.md iter-1(a)).

### New user-facing capability
On `/structure`, the user can read both registered strategies and their config-owned parameters and see which is the current champion — inside the app, not only via `curl`/MCP.

### New information displayed
The strategy registry (`v1`, `structure_tape`) with entry rule, exit precedence, and `structure_tape`'s class-scaled stop/reward/size maps; and the champion pointer (`champion.strategy_id` / `champion.profile`).

### New user actions
None — the Registry section is read-only and renders on page load (no new form, button, or input).

### UI surface changes
A new **Registry** section on the existing `/structure` page. No new route, no new nav entry. J-01's levels/zones section is unchanged except for the already-applied empty-state overlay fix, which this iteration re-verifies.

### Product surface delta
`/structure` grows from a levels/zones-only view to levels/zones + strategy-registry + champion — still one route under the one existing Structure nav tab.

### Blueprint conformance
J-02 lives at `/structure` (Registry section) — already the canonical home in `blueprint.md`'s Information Architecture table (row "J-02 … `/structure` (Registry section) … Structure"). No new surface, no nav-skeleton change; no `blueprint.reapproval-requested` written.

### Data-contract additions
**None.** Both displayed values are already registered in `blueprint.md`'s Data Contract, each with one computing module and one serving endpoint:
- "Registered strategies (`v1`, `structure_tape`) + class-scaled params" → `Config.strategy_definition` (config-owned) → `GET /research/strategies`.
- "Champion pointer (founding `v1`/`default`)" → `JournalStore.get_champion_pointer` (store-owned) → `GET /research/strategies` + `GET /research/profiles` (one pointer, two read views).

The Registry section reads both verbatim; no new owned value, no second computation, no second endpoint. `blueprint.md` is unchanged this iteration.

## OUT OF SCOPE

- **J-03** (`structure_tape`-vs-`v1` on-screen comparison) — the riskiest remaining journey (runs backtest jobs, poll loop, per-class A/B/C breakdown, PnL-ledger baseline). Deferred to iter-3 per the goal's J-01→J-02→J-03 dependency order and the "never bundle two risky journeys" rule. Do not build any comparison/backtest UI this iteration.
- **Any backend code change** — no new endpoint, no new computation, no edit to `strategies.py` / `profiles.py` / `config.py` / `store.py`; the champion-serving endpoints already exist.
- **Any champion-pointer mutation** — no `set_champion_pointer` call, no promotion path, no PnL-ledger write from the UI.
- **F2 (carry-forward, non-blocking)** — the same latent z-index empty-state occlusion in `apps/frontend/components/PriceChart.tsx` (Cockpit chart, serving J-04). It is pre-existing, byte-unchanged, and not on J-02's surface, so it is NOT a regression; defer to a future Cockpit-touching iteration (ideally a shared chart-empty-state wrapper for both charts).
- Any client-side reconstruction, grading, or aggregation of registry parameters or the champion (verbatim reads only).

## DEFINITION OF DONE

- [ ] **J-02 passes via browser-qa-agent:** on `/structure`, the Registry section shows `v1` and `structure_tape` as two cards whose entry rule, exit precedence (`r_stop → reward_target → state_flip → horizon`), and (for `structure_tape`) `stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class` match `GET /research/strategies` **byte-for-byte**, with a screenshot in `reports/qa/goal-structure_ui-iter-2-evidence/`.
- [ ] **J-02 champion badge verbatim:** the champion badge shows `champion.strategy_id` / `champion.profile` (founding `v1`/`default`) read verbatim from `GET /research/strategies`, and it equals `GET /research/profiles`'s `champion` byte-for-byte (coherence-auditor confirms single-source-of-truth; browser screenshot captured).
- [ ] **J-02 honest state:** with the registry endpoint unreachable/non-200, the Registry section renders an explicit, distinct "registry unavailable" state (no fabricated strategy, no hardcoded champion) — browser-verified with a screenshot.
- [ ] **J-01 independently re-verified:** browser-qa-agent produces a fresh PASS on the levels-but-no-zones state against the current `StructureChart.tsx` (the empty-state hint renders, not a blank box), plus the populated levels/zones state, with evidence in `reports/qa/goal-structure_ui-iter-2-evidence/`.
- [ ] **J-01 closed:** iteration-2's `ui-test-results` / `ux-regression` / `status.json` are internally consistent and the phase-closure verdict is **CLOSURE-PASS** (no contradiction across records like iter-1's CLOSURE-FAIL).
- [ ] **Required-still-passing J-04 remains green:** backend suite green, engine equivalence proves byte-identical `default` output, `config_fingerprint` stays `4d665603569b9dbf`, and the four prior surfaces (`/`, `/journal`, `/studies`, `/performance`) + the data-driven 5-link nav are intact.
- [ ] **No anti-goal violation:** champion read verbatim and moved never (`get_champion_pointer` unmodified, no `set_champion_pointer` added); no new backend endpoint/computation (diff is frontend-only: `types.ts` / `api.ts` / `page.tsx` additive, plus `StructureChart.tsx` only if re-verify demands it); no vocabulary drift in Registry copy.
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-structure_ui-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by journey ID):**
  - **J-02** — Registry cards render `v1` + `structure_tape` with config-owned params verbatim; champion badge shows `v1`/`default` matching both `/research/strategies` and `/research/profiles`; registry-unavailable honest state renders when the endpoint is down. Screenshots into `reports/qa/goal-structure_ui-iter-2-evidence/`.
  - **J-01** — re-verify the levels-but-no-zones honest state (the iter-1 UT-10 equivalent) shows the empty-state hint, not a blank chart box, on the current fixed component; plus the populated levels/zones state still renders byte-for-byte. Screenshots into the same evidence directory. (Per lessons.md iter-0: a journey with no populated evidence screenshot is `unknown`, not `passing` — prose is not sufficient.)
- **Unit/integration:**
  - Frontend `fetchStrategies()` unavailable-state path (non-200 / unreachable → `strategies: null`), mirroring the existing `fetchProfiles()` coverage.
  - The champion single-source-of-truth (identical `champion` from `/research/strategies` and `/research/profiles`) is the coherence-auditor's verbatim check.
  - The J-04 foundation suite (backend 1146-class run, `test_profile_equivalence.py`, `test_levels.py`, `config_fingerprint`) must stay green.
- **Error cases:** registry endpoint non-200 or unreachable → explicit unavailable state (no fabricated strategy); missing/partial champion field → honest state, never a hardcoded `v1`/`default` fallback.

## NOTES

- **Lessons applied (from `runs/goal-session-structure_ui/state/lessons.md`):**
  - iter-1(b): an auditor's in-place fix of a browser-QA FAIL is not "done" until browser-QA re-runs independently and the records reconcile — this is exactly why J-01 is a target this iteration and why depth is full (only the full pipeline runs phase-closure/ux-regression).
  - iter-1(a): `lightweight-charts` paints its canvases at `z-index:1/2`; any empty/loading overlay needs an explicit z-index above them. The J-01 fix (`StructureChart.tsx:99` `z-10`) is in-tree — re-verify it holds; if a residual occlusion appears, apply the same explicit-z-index remedy.
  - iter-0: treat any journey lacking a populated `reports/qa/<iter>-evidence/` screenshot as `unknown`, not `passing`; J-02's new Registry section and J-01's re-verify both require browser evidence.
- **Champion immutability is the critical rail here.** J-02 only *reads* `store.get_champion_pointer()`; both serving endpoints already share that one source. The developer must not add a second champion shape, a client-side champion inference, or any `set_champion_pointer` call — the coherence-auditor hard-fails single-source-of-truth violations and the audit lane guards frozen-foundation immutability.
- **Data reality (keyless fixture):** the registry (`v1`, `structure_tape`) and the champion are fully populated even keyless (config-owned + seeded pointer), so J-02 is demoable without recorded bars — unlike J-01's levels/zones, which stay honestly empty where no bars are recorded.
- Reference: prior evaluator verdict `runs/goal-session-structure_ui/iter-1/eval.md` (CONTINUE, next-step = full: close J-01 then build J-02) and coherence `runs/goal-session-structure_ui/iter-1/coherence.md` (COHERENCE-PASS).
