# Goal Iteration 0 — Baseline assessment (Interlude: "The Fast Wall")

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** fast_wall
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Required-still-passing journeys:** None yet — baseline establishes the passing/failing set. J-07 (regression sentinel) captures the eras 1–5B foundation floor (`config_fingerprint` `4d665603569b9dbf`, the frozen surfaces `/`, `/journal`, `/studies`, `/performance`, `/structure`) that every later iteration must hold.
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

  *Interlude-specific anti-goals (added, not weakening any rail above):*
  - **Accelerators are never sources of truth.** Every cache/index/memo this interlude adds is a rebuildable derived value: deleting it loses nothing and fabricates nothing; a miss recomputes byte-identically through the one canonical owner; no research value is ever read FROM a cache that could not be re-derived identically without it. *(critical)*
  - **No compute on page load — operator-run only.** No GET (page, REST, or MCP proxy) ever starts, resumes, or extends the backtest sweep; the only compute entry points are the explicit POST trigger and the CLI warmer. No scheduled, ambient, or retry-driven compute either. *(critical)*
  - **The verification trust boundary never weakens.** Stat-keyed serving applies only to content already fully verified in this process's lifetime, keyed by `(path, size, mtime_ns)` with the racy-write guard; ANY stat change re-verifies fully; integrity failures are never cached; `DatasetStore.load_events()`/`replay()` — the paths that feed research values — verify fully on every load, forever. *(critical)*
  - **No divergent accelerator output.** An accelerated read (cached, memoized, resumed, or parallel) whose bytes differ from the fresh sequential compute of the same inputs is a veto-class defect, never a tolerable approximation; no accelerator ships without a passing determinism/equivalence test proving that byte-identity. *(critical)*
  - **No gate, register, or vocabulary drift.** The PnL register, `insufficient_sample` labeling, train/hold-out separation, feed separation, and the "simulated — not indicative of live results" language are untouched; the not-computed state introduces no prediction/advice/imperative phrasing. *(critical)*
  - **No source-guard weakening.** The existing source-introspection tests (forbidden substrings, single rebind, pinned dependency wiring) are respected as written — never edited, renamed, or loosened to make a change fit. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block in `docs/goal.md` — it MUST NOT edit human-authored journeys, the Anti-goals section, or any other part of that file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Establish an honest baseline for the Fast Wall interlude: run all seven Must-have journeys (J-01–J-07) against the current codebase to record which already pass, fail, or are partial — without changing any code.

## BACKGROUND

This is the **baseline assessment** for session `fast_wall`, not a feature delivery — it is iteration 0 of a brand-new session (no prior evaluator verdict, empty `journey-history.json`, empty `lessons.md`). Per baseline-mode rules, depth is **lean** because `Mode: baseline` mandates it outright: the developer step is a no-op, and the value comes entirely from the browser-QA + suite sweep that exercises every journey. A codebase probe run during decomposition confirms the pre-interlude state matches `docs/goal.md`'s diagnosis exactly: `GET /research/edge-report` (`routes.py:2093`) still calls `run_strategy_comparison_report` **directly**, through the only existing cache method `EdgeReportCache.get_or_compute` (no `lookup`/`compute_and_publish` split exists) — i.e. a cold cache genuinely computes inline inside the GET request, confirming J-01's target defect is live today. None of the interlude's six new modules/functions exist yet (`edge_report_compute.py`, `dataset_index.py`, `setups_scan_cache.py`, `EdgeReportBacktestCache`, `level_change_points`, `basis_day_key`, `_StructureArmMemo`, or any stat-keyed cache in `bars.py`/`datasets.py`), and the frontend `/structure` page has no not-computed panel or "Compute edge report" button — so J-01 through J-06 are expected to **fail** at baseline. J-07 (foundation regression sentinel) is expected to **pass**, since it only re-confirms unchanged era-1–5B behavior; `config_fingerprint()` was live-confirmed as `4d665603569b9dbf` against the current tree during this probe. One favorable finding for downstream iterations: the real corpus (`.data/datasets`, measured 882MB — matching the exact figure `docs/goal.md` cites) is **already present locally**, persisted from the prior `tradable_wall` session — so, unlike that session's baseline (where two journeys were genuinely Alpaca-credential-blocked), no journey here is human-blocked; the "operator-verified on the real corpus" acceptance sub-clauses just aren't buildable/exercisable until their journeys ship.

## IN SCOPE

### Backend
- [ ] None — verify-only. No source files are created or modified this iteration.

### Frontend (if applicable)
- [ ] None — verify-only. No source files are created or modified this iteration.

### Verification actions (no code)
- [ ] Run the full backend test suite and record pass/skip counts as the green baseline (`docs/goal.md` Success Criterion 1).
- [ ] Confirm `config_fingerprint` is `4d665603569b9dbf` (J-07 anchor; already spot-confirmed live at decompose time).
- [ ] Probe `GET /research/edge-report` on a cold cache and record whether it currently computes inline (confirms J-01's defect) — a compute-spy is not required at baseline; an observed hang/timeout or a direct code citation (`routes.py:2093-2115` calling `run_strategy_comparison_report` unconditionally) is sufficient evidence.
- [ ] Probe `GET /research/datasets` and `GET /research/setups` latency against the local real corpus (`.data/datasets`, already present) and record the observed timings as the pre-interlude baseline (`docs/goal.md` cites 31.4s and multi-minute respectively) — read-only probes only, never a mutating recompute.
- [ ] Browser-verify the current `/structure` page's Edge Report section and record its actual render (spinner, error, hang, or the frozen "No edge-report cells yet." text) — never assume.
- [ ] Browser spot-check the eras-1–5B surfaces named by J-07 (`/`, `/journal`, `/studies`, `/performance`, `/structure` tradable map + case studies + raw toggle + era-5 fetch control/provenance badge; sim cockpit `SIM-BUYER`→`buyer_control`, `SIM-SELLER`→`seller_control`).

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
No new surfaces. This iteration only verifies against the Information Architecture drafted this same iteration in `runs/goal-session-fast_wall/state/blueprint.md` (nav frozen; this interlude's homes = `/structure`'s Edge Report section plus backend-only accelerators with no dedicated panel).

### Data-contract additions
None. The session's Data Contract is drafted in `blueprint.md`; no value is introduced or computed this iteration.

## OUT OF SCOPE

- Any code change (no `edge_report_compute.py`, `dataset_index.py`, `setups_scan_cache.py`, `EdgeReportBacktestCache`, stat-keyed store caches, the arm memo, or the frontend not-computed panel/Compute button — those are later iterations).
- Marking journeys as passing/failing — only the goal-evaluator does that; this spec only requests they be exercised and results recorded.
- Running the real ~10h+ sweep to completion or performing any mutating recompute against the real 882MB corpus — read-only latency probes only.
- Editing `docs/goal.md`, the Anti-goals, or any frozen foundation.

## DEFINITION OF DONE

- [ ] All seven journeys (J-01–J-07) are exercised against the current codebase and each result (pass / fail / partial / blocked) is recorded for the evaluator.
- [ ] The full backend test suite is run and its pass/skip counts recorded; `config_fingerprint` `4d665603569b9dbf` confirmed.
- [ ] No source file under `apps/` was modified (verify-only; `git diff --stat apps/` is empty).
- [ ] Dev handoff (no-op, stating "baseline verify-only, no code changes") written at `docs/handoffs/goal-fast_wall-iter-0-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-01 (`/structure` Edge Report section current render), J-04 (presence/absence of a "Compute edge report" button), J-06 (page-load-to-ready timing / any stuck loading panel on `/structure`), and the J-07 spot-checks (`/`, `/journal`, `/studies`, `/performance`, `/structure` tradable map + case studies + raw toggle + fetch control/provenance badge; `SIM-BUYER`/`SIM-SELLER` cockpit settlement).
- **Unit/integration:** run the full backend suite (establish the green baseline; assert `config_fingerprint == 4d665603569b9dbf`). No new tests are written this iteration.
- **Endpoint probes:** `GET /research/edge-report` (cold-cache latency/behavior), `GET /research/datasets`, `GET /research/setups` (record latency against the local real corpus; if it were ever absent, record `blocked`/`no local corpus` honestly rather than fabricating a number).
- **Error cases:** N/A — no code is added this iteration, so there are no new inputs to reject.

Test-first contract:

- TC-1: given the current codebase state, when browser-qa-agent or an automated probe issues `GET /research/edge-report` on a cold cache, then `journey-history.json` records a J-01 result (pass/fail/partial) citing the observed cold-cache behavior (inline compute vs. an honest not-computed payload) as evidence.
- TC-2: given the current codebase state, when an automated probe calls `DatasetStore.list()` and `BarStore.list()` and inspects `bars.py`/`datasets.py` for a stat-keyed cache, then `journey-history.json` records a J-02 result citing the presence or absence of any caching layer in the read source, plus the observed `GET /research/datasets` latency against the local corpus.
- TC-3: given the current codebase state, when the evaluator inspects `levels.py`, `tradability.py`, and `backtests.py` for `level_change_points`, `basis_day_key`, and `_StructureArmMemo`, then `journey-history.json` records a J-03 result citing whether the structure-strategy arming path uses a memo.
- TC-4: given the current codebase state, when browser-qa-agent inspects `/structure`'s Edge Report section for a "Compute edge report" button and the evaluator checks for `/research/edge-report/compute` routes, then `journey-history.json` records a J-04 result citing the presence or absence of the button and routes.
- TC-5: given the current codebase state, when the evaluator inspects `edge_report.py`/`_split_cells` for a per-pair durable cache (`EdgeReportBacktestCache`) and a `run_pair` provider seam, then `journey-history.json` records a J-05 result citing the presence or absence of the resumable/parallel provider.
- TC-6: given the current codebase state, when the evaluator inspects `setups.py`'s cache path (the existing in-process `_SCAN_CACHE` global) for a durable sibling (`setups_scan_cache.py`), then `journey-history.json` records a J-06 result citing the presence or absence of a durable scan cache surviving a simulated restart.
- TC-7: given the current codebase's era-1–5B surfaces (`/`, `/journal`, `/studies`, `/performance`, `/structure`) and the frozen `config_fingerprint`, when the full backend suite runs and browser-qa-agent spot-checks each surface plus the sim cockpit settlement, then `journey-history.json` records a J-07 result citing the suite's pass/skip counts and the confirmed fingerprint value as evidence.
- TC-8: given the iteration completes, when `git diff --stat apps/` is run, then its output is empty (zero files changed under `apps/`).
- TC-9: given the iteration completes, when the developer step finishes, then `docs/handoffs/goal-fast_wall-iter-0-dev.md` exists and states no code changes were made this iteration.

## NOTES

- **Codebase probe evidence (iter-0 decompose time):** `apps/backend/app/research/routes.py:2093-2115` (`get_edge_report`) calls `run_strategy_comparison_report(...)` unconditionally through `EdgeReportCache.get_or_compute` — the only cache method that exists (no `lookup`/`compute_and_publish`). `grep` for `edge_report_compute.py`, `dataset_index.py`, `setups_scan_cache.py`, `EdgeReportBacktestCache`, `level_change_points`, `basis_day_key`, `_StructureArmMemo`, and stat-keyed caches in `bars.py`/`datasets.py` all returned no matches. `apps/frontend/app/structure/page.tsx` has no "not_computed"/"Compute edge report" text. `setups.py`'s only cache is the existing in-process `_SCAN_CACHE` module global (era 5B), which is wiped on every restart — matches `docs/goal.md`'s claim precisely. `config_fingerprint()` was imported and called live: `4d665603569b9dbf`, matching the frozen value.
- **Real corpus already present:** `.data/datasets` measures 882MB locally (matches `docs/goal.md`'s cited figure exactly), persisted from the `tradable_wall` session. `.data/edge_report_cache.db` exists but is small (12KB) — consistent with holding only keyless-fixture rows, not a completed real-corpus report (the real compute "has never finished," per the goal). This means J-02/J-04/J-05/J-06's "operator-verified on the real corpus" acceptance sub-clauses are exercisable as soon as their journeys ship — no new credentials or recording needed this chapter.
- **No lessons or assumptions to surface:** `lessons.md` and the assumption ledger are both empty (first iteration of a new session); no `Applies to:` pattern to check against.
- **Likely next-iteration target (informational only — not committing scope here):** `docs/goal.md`'s stated build order is J-01 → J-02 → J-03 → J-04 → J-05, with J-06 riding on J-02's durable index and J-07 guarding continuously. J-01 is the smallest, most self-contained change (rewires one existing route + adds one cache-lookup method + one frontend panel) and is explicitly framed as "stop the bleeding" — the priority rubric's "unblockers next" and "smallest spec wins ties" both point here once baseline results are in.
