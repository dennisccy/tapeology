# Goal Iteration 0 — Baseline assessment (Era 5B "The Tradable Wall")

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Required-still-passing journeys:** None yet — baseline establishes the passing/failing set. J-07 (regression sentinel) captures the eras-1–5 foundation floor that all later iterations must hold.
- **Anti-goal reminders (verbatim from `docs/goal.md`):**

  *Immutable rails — the identity of the project:*
  1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*

  *Era-5B-specific anti-goals (added, not weakening any rail above):*
  - **The tradable map is a lens, never a second levels engine.** `research/tradability.py` consumes `compute_levels` output verbatim (plus bars for scale context); it never re-detects pivots/extremes and never alters the frozen raw computation or its parameters. *(critical)*
  - **Morning-markup discipline.** Any session's map derives only from bars fully completed by the prior session's close; no forming-bar data enters a map, an event, or a chip. *(critical)*
  - **Descriptive, never imperative.** Chips, case studies, and reports state conditions and cite measured history — never "buy/sell/short now", no prediction or expected-return language, anywhere in UI copy. *(critical)*
  - **Recording stays explicit, windowed, and logged** — only around registered scan events with config-owned padding; no ambient, scheduled, or full-day bulk recording; every dataset append-only, checksummed, split-frozen at registration. *(critical)*
  - **Feed honesty — never pool across feeds.** The `feed` stamp comes verbatim from the adapter/key tier; `iex`, `sip`, and Yahoo-bar lineages are never pooled in any analysis cell, report row, or claim; `iex` is never presented as the consolidated tape. *(critical)*
  - **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid, publishable outcome. *(critical)*
  - **The champion moves only through the existing sweep gate on hold-out data.** This era may feed the gate; it never hand-promotes `structure_tape_map` or anything else. *(critical)*
  - **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)*
  - **Keys never committed, never logged.** Alpaca credentials live only in the operator's environment; no secret in source, fixtures, logs, artifacts, or reports. *(critical)*
  - **Live mode stays untouched.** The cockpit price chart remains hidden in live mode; no execution path, ever. *(critical)*
  - **No vocabulary drift.** No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.

## GOAL

Establish an honest baseline: run all seven Era 5B Must-have journeys (J-01 – J-07) against the current codebase to record which already pass, which fail, and which are partial/blocked — **without changing any code**.

## BACKGROUND

This is the **baseline assessment** for session `tradable_wall`, not a feature delivery. Per baseline-mode rules the developer step is a no-op; the value is the browser-QA + suite sweep that verifies every journey against the current state so the goal-evaluator can mark `already_passing` vs. to-build. Depth is **lean** because baseline mandates it (the lean cycle's browser-QA runs every journey; no code path needs the full 11-step pipeline). Codebase probe confirms the starting reality: the Era 5B endpoints `/research/tradability`, `/research/setups`, and `/research/edge-report` are **not registered** and modules `tradability.py` / `setups.py` are **absent**, so J-01, J-02, J-04, J-05, J-06 are expected to fail at baseline; J-07 (foundation sentinel) is expected to pass on the frozen eras-1–5 stack. J-03 and J-06 are credential-gated (Alpaca env) and must report **blocked** — never simulated — when keys are absent.

## IN SCOPE

### Backend
- [ ] None — verify-only. No source files are created or modified this iteration.

### Frontend (if applicable)
- [ ] None — verify-only. No source files are created or modified this iteration.

### Verification actions (no code)
- [ ] Run the full backend test suite and record pass/skip counts as the green baseline.
- [ ] Confirm `config_fingerprint` is `4d665603569b9dbf` (J-07 anchor).
- [ ] Probe each Era 5B endpoint (`/research/tradability`, `/research/setups`, `/research/setups/{id}`, `/research/edge-report`) and record present/absent.
- [ ] Browser-verify the current `/structure` page and cockpit `/` `PriceChart` against J-05 / J-06 expectations (record what is present vs. missing).
- [ ] Browser spot-check the eras-1–5 surfaces named by J-07 (`/journal`, `/studies`, `/performance`, `/structure` era-5 fetch control + provenance badge; sim cockpit `SIM-BUYER`→`buyer_control`, `SIM-SELLER`→`seller_control`).

### New user-facing capability
None — baseline changes nothing the user sees. It only measures the current state.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — this iteration produces a baseline record, not a product change.

### Blueprint conformance
No new surfaces. This iteration only verifies against the Information Architecture just drafted in `runs/goal-session-tradable_wall/state/blueprint.md` (nav frozen; Era 5B homes = `/structure` sections + cockpit `PriceChart`).

### Data-contract additions
None. The Data Contract for the whole session is drafted in `blueprint.md`; no value is introduced or computed this iteration.

## OUT OF SCOPE

- Any code change (no `tradability.py`, `setups.py`, `/research/edge-report` endpoint, `structure_tape_map` registry entry, `/structure` sections, or cockpit overlay/chip work — those are later iterations).
- Marking journeys as passing/failing — only the goal-evaluator does that; this spec only requests they be exercised and results recorded.
- Recording any real tape / touching Alpaca beyond a read-only presence check for credentials (no dataset is created at baseline).
- Editing `docs/goal.md`, the Anti-goals, or the frozen foundation in any way.

## DEFINITION OF DONE

- [ ] All seven journeys (J-01 – J-07) are exercised against the current codebase and each result (pass / fail / partial / blocked) is recorded for the evaluator.
- [ ] The full backend test suite is run and its pass/skip counts recorded; `config_fingerprint` `4d665603569b9dbf` confirmed.
- [ ] Credential-gated J-03 and J-06 are recorded as `blocked` (not simulated) if Alpaca keys are absent from the environment, else exercised.
- [ ] No source file under `apps/` was modified (verify-only; `git diff --stat apps/` is empty).
- [ ] Dev handoff (no-op, stating "baseline verify-only, no code changes") written at `docs/handoffs/goal-tradable_wall-iter-0-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-05 (`/structure` current state vs. tradable-map-default expectation), J-06 (cockpit `PriceChart` band overlay + chip — credential-gated), and the J-07 spot-checks (`/journal`, `/studies`, `/performance`, era-5 `/structure` fetch control + provenance badge; `SIM-BUYER`/`SIM-SELLER` cockpit settlement).
- **Unit/integration:** run the full backend suite (establish the green baseline; assert `config_fingerprint` `4d665603569b9dbf`). No new tests are written this iteration.
- **Endpoint probes:** GET `/research/tradability`, `/research/setups`, `/research/edge-report` and record HTTP status (expected 404/absent at baseline).
- **Error cases:** N/A — no code is added, so there are no new inputs to reject.

## NOTES

- **Credential gating (J-03, J-06):** these carry `*(Verified with Alpaca credentials configured)*`. Alpaca keys live ONLY in the operator's environment (anti-goal "Keys never committed, never logged"). If keys are absent at baseline, record these journeys as `blocked` — do NOT simulate a tape recording or fabricate a result.
- **`edge_report.py` name collision (heads-up for the future J-04 iteration, not a baseline action):** `apps/backend/app/research/edge_report.py` already exists as the **era-3 champion-ONLY CLI** (`python -m app.research.edge_report`). Era 5B's J-04 needs a **3-way** (`v1` / `structure_tape` / `structure_tape_map`) strategy × class × side × reaction report served via `GET /research/edge-report`. The blueprint registers `research/edge_report.py` as the canonical owner (per the goal's Data Contract) — the J-04 builder must **extend this file additively** (reusing the single `BacktestJobManager` path it already uses) and register the new endpoint in `routes.py`, never fork a second edge computation.
- **Codebase probe results informing this baseline:** `tradability.py` and `setups.py` are absent; `/research/tradability`, `/research/setups`, `/research/edge-report` are not registered in `apps/backend/app/research/routes.py`. Frontend `/structure` exists as a single `page.tsx`; cockpit chart is `apps/frontend/components/PriceChart.tsx`. These confirm J-01/J-02/J-04/J-05/J-06 are expected to fail at baseline and J-07 to pass.
- **Natural build order after baseline** (from `docs/goal.md`): J-01 → J-02 → J-03 → J-04, then J-05/J-06 surface them; J-07 guards continuously. J-01 (`tradability.py` + `GET /research/tradability`) is the likely next target — it is the unblocker whose bands J-02 scans, J-04 arms `structure_tape_map` on, and J-05/J-06 render.
- **Blueprint drafted this iteration:** `runs/goal-session-tradable_wall/state/blueprint.md` (auto-approved by `run-goal.sh` unless `--require-blueprint-approval`).
