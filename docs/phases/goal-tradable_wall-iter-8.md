# Goal Iteration 8 — J-03 credentialed tape verified: the wall now shows its real tape

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-04, J-05, J-06, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Descriptive, never imperative.** Chips, case studies, and reports state conditions and cite measured history — never "buy/sell/short now", no prediction or expected-return language, anywhere in UI copy. *(critical)*
  - **Feed honesty — never pool across feeds.** The `feed` stamp comes verbatim from the adapter/key tier; `iex`, `sip`, and Yahoo-bar lineages are never pooled in any analysis cell, report row, or claim; `iex` is never presented as the consolidated tape. *(critical)*
  - **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid, publishable outcome. *(critical)*
  - **Keys never committed, never logged.** Alpaca credentials live only in the operator's environment; no secret in source, fixtures, logs, artifacts, or reports. *(critical)*
  - **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)*
  - **Live mode stays untouched.** The cockpit price chart remains hidden in live mode; no execution path, ever. *(critical)*

## GOAL

Make the last open journey visible and honest: the pinned AAPL 2026-06-22 case-study drill-in shows its **real recorded five-state tape timeline** at the ~300 wall, and the Edge Report shows **populated cells** (real n / honest `insufficient_sample`) over the operator's now-persisted credentialed recordings — closing J-03 without a single new credentialed act at QA time.

## BACKGROUND

Iter-7 halted **STALLED**: J-06 was the last agent-buildable journey and it passed, leaving only J-03's credentialed **≥10-window recording**, whose every unblock path was operator-owned. The operator has now taken unblock-path #1/#2: `apps/backend/.data/datasets/` holds **11 durable historical tick recordings created today** across **10 distinct panel symbols** (AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, SPY, TSLA), both `train` and `holdout` splits, feed-stamped `sip` verbatim — **including the pinned AAPL 2026-06-22 window** (`5c7f1a44…`, window 12:30→15:00 UTC = touch −60/+90 min, 555,382 real trades+quotes, checksummed). That exceeds Success-Criterion-4's headline (≥10 windows / ≥5 symbols / pinned AAPL included). `docs/goal.md` J-03 text is unchanged (no goal amendment), so the credentialed acceptance stands and is now satisfiable.

Crucially, **verification is now keyless**: the recordings are persisted in the canonical store, so browser-QA reads them without any Alpaca credentials at QA time — this iteration is fully agent-verifiable. Depth is **full** because (a) the iter-7 evaluator explicitly recommended full; (b) it verifies a credentialed **external-integration** deliverable (`core.md` External Integration Testing) across **three UI surfaces**; (c) it crosses backend(verify/test) + frontend(F1) boundaries; and (d) it is the **GOAL_ACHIEVED-candidate** iteration and must run the full pipeline (audit + coherence + closure) to support the two-key confirm. Applied lessons: **iter-3** (a credentialed headline is durable only with persisted re-openable artifacts + native PASS + the named pinned-case demonstration — the datasets are persisted; this iter demonstrates the pinned drill-in), **iter-4** (verify populated edge-report cells on a *real panel-symbol* dataset, not just the empty/synthetic shape), **iter-6** (browser-QA on `/structure` deep-scroll frames go blank — fall back to DOM-text capture; anchor acceptance on the goal's structural criterion, not a numeric snapshot), **iter-7** (require a persisted store, not `/tmp`).

## IN SCOPE

### Backend
- [ ] **No production backend change.** The setups tape-join (`setups.py`, iter-3) and the 3-way edge report (`edge_report.py`, iter-4) already read the frozen `DatasetStore`; the newly-persisted datasets populate their existing read paths with no code change. Verify the running backend serves the new datasets (fresh read of the persistent store).
- [ ] **Cleanup B (test-only, iter-7 audit T1):** correct the stale docstring + QA description in `apps/backend/tests/test_price_chart_confluence.py` so it matches the shipped confluence-chip behavior. No production logic, no fingerprint impact.

### Frontend
- [ ] **Cleanup A (iter-7 audit F1):** gate the cockpit `PriceChart.tsx` tradability fetch on `history?.epoch_anchor != null` (early-return in the effect at `PriceChart.tsx:203-207`), **dropping the wall-clock `asOf` fallback**. Bands are then only ever requested/drawn with the correct anchor-derived morning-markup basis (e.g. 2026-06-18 for the 06-22 replay) — never today's date for the sub-second window before the anchor resolves. Keep the effect keyed on `[ticker, history?.epoch_anchor]`. SIM-*/no-bars symbols keep their honest "no tradable map" empty state (they never fetch until an anchor exists, or resolve `no_bar_series_for_symbol`).

### New user-facing capability
The pinned AAPL 2026-06-22 case study now tells its full story: the drill-in replays the recorded window through the frozen `TapeEngine` and shows the five-state timeline at the ~300 test; the Edge Report is no longer vacuously empty — it shows real per-cell counts under the existing gates.

### New information displayed
- Case Studies → AAPL 2026-06-22 drill-in: a **populated `tape_timeline`** (five states + transition times around the touch) replacing the prior "No recorded tape for this event." empty-state.
- Edge Report: **populated cells** (`v1` / `structure_tape` / `structure_tape_map` × class × side × reaction) with real `n`, R stats, the full PnL register, null baseline, and honest `insufficient_sample` labels where n<5.

### New user actions
None — the map/toggle/registry/filters/drill-in and the cockpit overlay/chip already exist (J-05/J-06). This iteration surfaces real data through them.

### UI surface changes
No new page, no new nav entry. `/structure` Case Studies drill-in and Edge Report section, and the `/` cockpit `PriceChart`, render real values that were empty/degraded before.

### Product surface delta
The product goes from "the wall is distilled and the machinery is proven on keyless/empty fixtures" to "the wall shows its **real recorded tape** and an **honest measured edge report** on credentialed data" — the operator's headline question is now answered end-to-end.

### Blueprint conformance
No new surfaces. All pages already have canonical homes: J-03's timeline renders inside `/structure` → **Case Studies** drill-in; the Edge Report inside `/structure` → **Edge Report**; the cockpit chip on `/` → `PriceChart`. Nav is frozen (Era 5B). No blueprint nav-skeleton change; no `blueprint.reapproval-requested`.

### Data-contract additions
**None.** This iteration introduces no new displayed value — it populates existing registered owners with real data: `tape_timeline` (owned by `setups.py`, served by `GET /research/setups/{id}`; states owned by the frozen `TapeEngine` replayed over the recorded `DatasetStore` window) and edge-report cells (owned by `edge_report.py`, served by `GET /research/edge-report`). The recorded datasets are owned by the existing `DatasetStore` (`GET /research/datasets`). All rows already exist in `blueprint.md`; no edit required.

## OUT OF SCOPE

- **Committing the recorded datasets.** The ~900 MB of `sip` tick data in `apps/backend/.data/datasets/` is gitignored (0 tracked, verified) and MUST stay local — CI stays keyless via the committed fixture slice. Do not stage, commit, or upload any recorded dataset.
- **Any new credentialed act.** The operator already recorded durably; no re-recording, no Alpaca calls at QA time. Verification is a keyless read of the persistent store.
- **Any change to a frozen file** — `levels.py`, `tradability.py`, `engine/`, `config.py`, `strategies.py`, `backtests.py`, `adapters/` (incl. Alpaca), `bars.py`, `datasets.py` (store) — stay byte-identical; `config_fingerprint` stays `4d665603569b9dbf`.
- **Surfacing a numeric edge-report figure in the cockpit chip** (iter-7 coherence advisory) — deferred; the static "measured history: edge report" citation stays. Adding a live edge figure would be new scope + a gate-register obligation.
- **Manufacturing a survivor.** An empty or all-`insufficient_sample` edge report is a valid, publishable pass — never lower n, widen a gate, or pool feeds/splits to produce a "profitable" cell.
- Era-6 statistical gates, `/datasets` UI, bulk recording, any nav/page addition.

## DEFINITION OF DONE

- [ ] **J-03 passes via browser-qa:** the pinned **AAPL 2026-06-22** Case Studies drill-in renders a populated five-state `tape_timeline` at the ~300 touch (not the empty-state), and `GET /research/datasets` (or store enumeration) shows **≥10 event-window datasets across ≥5 symbols including the pinned AAPL 06-22 window**, each append-only, checksum-verified, `feed` stamped verbatim (`sip`), split-frozen at registration.
- [ ] **Edge Report renders populated cells** on the recorded windows: real per-cell `n`, honest `insufficient_sample` where n<5, train/hold-out never pooled, feeds never pooled, full PnL register + null baseline visible — no vacuously-empty report (closes the iter-4 synthetic-only gap).
- [ ] **No credential** appears in any file, log, or artifact: `apps/backend/tests/test_no_credential_in_artifacts.py` green and scan-report CLEAN.
- [ ] **Default suite passes keyless** via the committed fixture (recorded datasets not required for CI); full backend suite green.
- [ ] **F1:** cockpit tradability fetch gated on `epoch_anchor`; no wall-clock-basis transient; SIM empty state + a historical-replay band overlay re-verified in the browser; J-06 chip/overlay not regressed.
- [ ] **T1:** `test_price_chart_confluence.py` docstring/QA description corrected; test green.
- [ ] **Required-still-passing** J-01, J-02, J-04, J-05, J-06, J-07 remain green (full regression; refreshes golden-replay scripts).
- [ ] **No frozen file in the diff**; `config_fingerprint == 4d665603569b9dbf` independently recomputed; coherence verdict is **COHERENCE-PASS**.
- [ ] No anti-goal violation introduced.
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-8-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by journey ID):**
  - **J-03** — Case Studies → pinned **AAPL 2026-06-22** drill-in shows the populated five-state tape timeline (states + transition times around the ~300 touch); Edge Report shows populated cells with honest `insufficient_sample` labels. Use DOM-text extraction for deep-scroll sections (iter-6 lesson — screenshots blank out at depth); anchor acceptance on "populated timeline / populated cells exist and read verbatim from the endpoint", not a specific numeric rank.
  - **J-06** — cockpit chip + band overlay re-verified after F1 on the AAPL historical replay (correct 2026-06-18 basis, no wall-clock transient); descriptive-only copy; live mode still hides the chart.
  - **J-05** — `/structure` still defaults to the Tradable Map (≤10 bands, pinned resistance band present), raw-levels toggle off by default.
  - **J-07** — nav unchanged (Cockpit · Journal · Studies · Performance · Structure).
- **Unit/integration:**
  - `test_no_credential_in_artifacts.py` green; `test_price_chart_confluence.py` green after the T1 docstring fix.
  - The setups tape-join and `edge_report` read-path tests green; MCP `setups` / `edge_report` proxies byte-identical to their REST GETs.
  - Full backend suite green (report pass/skip/fail counts); `config_fingerprint` equivalence test green at `4d665603569b9dbf`.
- **Error cases (must be rejected/handled honestly):**
  - SIM-*/no-bars symbols show the honest "no tradable map" empty state after F1 (no chip, no band, no wall-clock fetch).
  - Edge-report cells with n<5 are labelled `insufficient_sample` (never manufactured into a survivor); an all-`insufficient_sample` report is accepted as a valid pass.
  - `sip` recordings are never pooled with `iex` or Yahoo-bar lineages in any cell/row/claim; `feed` stamped verbatim.

## NOTES

- **Feed = `sip` (interpretation logged):** the goal uses `iex` as the *free-tier example* ("iex on free keys — honestly thinner than SIP"); the operator's Alpaca tier returns `sip`, which all 11 recordings stamp verbatim. J-03's binding rail is "feed stamped verbatim from the adapter tier" + "never pool / never equate iex with sip" — not "must be iex." `sip` is honest (the actual consolidated tier), richer than the goal's worst case, and there is no `iex` lineage to pool with. Recorded to `runs/goal-session-tradable_wall/state/assumptions.md` (iter-8, reversible).
- **GOAL_ACHIEVED-candidate:** if J-03 flips `partial → passing` and the regression set stays green with no critical anti-goal violation and COHERENCE-PASS, the evaluator should evaluate toward **GOAL_ACHIEVED** (subject to the deterministic gate + two-key confirm). Do not self-declare — the evaluator owns that verdict.
- **Verification checkpoint (iter-4 pattern):** confirm the drill-in and Edge Report actually *populate* on the real panel-symbol datasets after a fresh backend read. If they unexpectedly render empty/degraded on real data, that is a **finding to surface** (not a pass) — the join/read path may have a real-config dependency that only credentialed panel-symbol data exposes.
- **iter-7 halt is resolved** by operator action, not by a goal edit: `docs/goal.md` J-03 acceptance is unchanged; the datasets are durably in `apps/backend/.data/datasets/` (not `/tmp`), directly answering the iter-3/iter-7 durability lesson.
