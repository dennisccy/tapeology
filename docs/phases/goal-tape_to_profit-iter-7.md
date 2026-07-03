# Goal Iteration 7 — J-07 candidate sweep harness (hold-out promotion gate)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-08
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets, no recommendation to execute. The ONLY permitted "fill" is the offline backtester's simulated fill computed against recorded historical tape, clearly labeled simulated and sent nowhere. *(critical)*
  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — and MUST never be presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
  - **Default engine outputs are frozen.** Indicator evolution is additive and versioned only: candidate profiles may add feature keys or alternate thresholds, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, and no enhancement may mutate an archived-era behavior to pass. *(critical)*
  - **No train-only promotion.** Nothing becomes the champion, a proposed journey, or a claimed improvement on the strength of train data alone: hold-out survival (net R AND net $, with the configured minimum n) is the only promotion gate; overfit results are labeled overfit. *(critical)*
  - **No ML, no online tuning.** Candidate search is bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops inside the engine, no thresholds that move at runtime.
  - **No fabricated data — honest failure states.** No synthesized trades, quotes, fills, datasets, or PnL to force a green journey; every failure mode (backend down, corrupt dataset, empty window, missing credentials, insufficient n) surfaces an explicit, distinct state. *(critical)*
  - **Single source of truth.** Every canonical value in the Data Contract is computed once and read verbatim by every surface — REST, WebSocket, UI, markdown reports, and MCP. A second computation path or a diverging number across surfaces is a defect. *(critical)*
  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
  - **Persistence stays scoped.** SQLite holds research records (now including backtests and the PnL ledger); the dataset store holds explicitly recorded historical tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the default profile byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Ship the candidate-sweep harness `python -m app.research.pnl_scan --out <path>` so a researcher (human or the AI dev-chain) can evaluate every registered candidate against the champion over the train datasets, validate apparent winners on the frozen hold-out set, and — only for a genuine hold-out survivor — promote it by appending one honest PnL-ledger row and moving the champion pointer, while zero survivors is an explicit, honest, exit-0 outcome.

## BACKGROUND

J-07 is the last remaining Must-have journey (J-01–J-06 and J-08 all pass as of iter-6); passing it makes the next evaluation a GOAL_ACHIEVED candidate. It is planned **alone** per the priority rubric — it is the only failing journey, nothing regressed, and iter-6 coherence was COHERENCE-PASS (no consolidation owed). **Depth is `full`** (not reflexive escalation — the prior verdict was CONTINUE, not ESCALATE): J-07 is the single riskiest journey and triggers three of the "pick full" criteria at once — it (a) touches the data model (moves the champion pointer + appends a PnL-ledger row), (b) requires new tests well beyond browser smoke (min-n gate both ways, determinism, robustness, overfit labeling), and (c) is the only journey performing an **anti-goal-gated state mutation**, so the full pipeline's independent auditor + QA verdict on the promotion mechanics is proportionate insurance before the two-key GOAL_ACHIEVED confirm. The iter-6 evaluator explicitly recommended `full` for exactly this journey.

Codebase facts verified before planning: `app/research/pnl_scan.py` does not exist (J-07 creates it); the champion is currently a **hardcoded constant** in `app/research/profiles.py` (`{STRATEGY_V1_ID, PROFILE_DEFAULT}`, "no promotion exists yet, J-07") — J-07 must turn it into a single persisted movable pointer; the PnL-ledger single writer is `pnl_ledger.append_validation_row`; `pnl_min_sample_size = 5` exists and config.py flags the promotion minimum as a J-07 config decision; the fixture pair arms n=1 per split and the one registered candidate `candidate-faster-warmup` is a non-survivor (hold-out net R negative).

## IN SCOPE

### Backend
- [ ] Create `apps/backend/app/research/pnl_scan.py` with a `__main__` entry so `python -m app.research.pnl_scan --out <path>` runs the candidate sweep (Data Contract row 36 owner — computed once per run, written to `--out`).
- [ ] **Candidate enumeration:** iterate every registered candidate from the existing single registry `Config.profile_registry()` / `profile_definition` (currently `candidate-faster-warmup`) — read that ONE registry, never a second enumeration or id-literal copy.
- [ ] **Sweep evaluation:** for each candidate, backtest it against the current champion over **all train** datasets using the existing J-03 backtest runner (reuse `app/research/backtests.py` — no second backtest/PnL computation path), then validate apparent winners on the **hold-out** set. Read dataset splits from the existing dataset store (row 30); read fee/slippage/notional from the config-owned strategy grammar (row 34).
- [ ] **Scan report (row 36):** per candidate, record train + hold-out **net R AND net $** deltas (champion baseline vs candidate), **n per split**, **per-dataset breakdown**, `survivor` (true iff it beats the champion on hold-out net R AND net $ with n ≥ the configured promotion minimum), and `robustness: robust|speculative` (robust iff positive on every train dataset individually). Train-only winners (positive train, failing the hold-out gate) are explicitly labeled **overfit** and never promoted. Include the honest simulated-PnL register on every $ figure.
- [ ] **Config-owned promotion minimum-n gate:** the minimum trade count for promotion comes from config (reuse `pnl_min_sample_size` or add a dedicated `promotion_min_sample_size` — developer's call, but it MUST be a config field, no magic number; if a new field, exclude/fold it into `config_fingerprint` per the config.py:920 note). Enforce it both ways.
- [ ] **Champion pointer → single persisted movable source (row 33):** replace the hardcoded `{STRATEGY_V1_ID, PROFILE_DEFAULT}` literal in `app/research/profiles.py` with a read from ONE persisted champion pointer (journal-scoped SQLite, existing single-writer discipline) that **defaults to the founding `v1/default`**. `GET /research/profiles` reads this single source so `/performance` (J-05) and MCP reflect a real promotion. No surface may infer the champion from the ledger or a second path.
- [ ] **Promotion mechanics (only when a hold-out survivor exists):** append exactly ONE PnL-ledger row via the EXISTING single writer `pnl_ledger.append_validation_row` (row 32 — no second append path), provenance-stamped (dataset ids + checksums, strategy config, profile id, `config_fingerprint`), AND move the persisted champion pointer. Promotion MUST NOT modify the `default` profile or any engine default (the pinned default fingerprint `4d665603569b9dbf` stays unchanged).
- [ ] **Determinism:** fixed seeds throughout (null-baseline RNG seed recorded in the report); identical re-runs produce byte-identical scan reports.
- [ ] **Honest empty/failure outcomes:** zero registered candidates OR zero survivors → explicit honest report + **exit code 0** (champion unmoved, no ledger row). Corrupt/unreadable dataset or unavailable store → explicit, distinct error, no partial write, no fabricated result.
- [ ] Extend `apps/backend/tests/test_no_execution_path.py` so its no-broker/order/paper-trading/execution scan also covers `app/research/pnl_scan.py` (keep the gate green with the sweep in coverage).

### Frontend (if applicable)
- None. J-07 is a machine-surface CLI journey. The champion pointer already renders on `/performance` via `GET /research/profiles` (J-05, unchanged). On the committed fixtures the sweep yields zero survivors, so the champion stays `v1/default` and `/performance` is visually unchanged; the profiles.py refactor keeps the endpoint response byte-identical for the shipped state.

### New user-facing capability
A researcher can run one deterministic command to learn whether any registered candidate carries edge that survives the frozen hold-out set — and trust that nothing is promoted on train performance alone. (Machine/CLI surface; no new page.)

### New information displayed
The scan report file (row 36): per-candidate train + hold-out net R/$ deltas, n per split, per-dataset breakdown, `survivor`, `robustness`, and overfit labels. A promotion additionally makes the moved champion visible on the already-shipped `/performance` page and a new honest PnL-ledger row visible at `GET /research/pnl/ledger`, `reports/pnl/pnl-history.md`, and MCP `pnl_ledger`.

### New user actions
`python -m app.research.pnl_scan --out <path>` (CLI). No UI controls.

### UI surface changes
None. No new pages, panels, or nav entries.

### Product surface delta
The product gains its promotion gate: the enhancement loop can now honestly convert a hold-out survivor into a champion move + a ledger row, or honestly report "no survivor" — closing the profit-research era's measurement story end to end.

### Blueprint conformance
No new surfaces. J-07 lives at its pre-registered machine home (IA table: "J-07 candidate sweep (hold-out gate) → CLI `python -m app.research.pnl_scan` → scan report + ledger; machine"). No Information-Architecture or nav-skeleton change.

### Data-contract additions
None (no new displayed value). Row 36 (scan reports) was registered at baseline (iter-0); promotion appends to the already-registered row 32 (PnL ledger, via the existing single writer) and moves the already-registered row 33 (champion pointer, served by the existing `GET /research/profiles`). Row 33's Notes were clarified **additively** in `blueprint.md` to record the owner-model change (champion pointer: hardcoded constant → single persisted movable pointer, same serving endpoint) — this keeps the single-source discipline current for the coherence auditor; it introduces no new value and no second computation or serving path.

## OUT OF SCOPE

- Any broker / order / execution / routing / paper-trading integration or order ticket of any kind (anti-goal: No live execution path). The only "fill" is the offline backtester's simulated fill, sent nowhere.
- Weakening, bypassing, or dialing-down the **shipped** min-n promotion gate to force a survivor on the committed fixtures (anti-goal: No train-only promotion). The fixtures MUST still yield zero survivors.
- Any change to the `default` profile, engine defaults, classifier, or any archived-era behavior (anti-goal: Default engine outputs frozen).
- Any new MCP tool or MCP mutation; `app/mcp/` stays zero-diff (anti-goal: MCP is read-only). The sweep is a CLI, not an MCP tool.
- Live-cockpit tape persistence or ambient recording; any new persistence scope beyond the journal SQLite champion-pointer + the existing ledger (anti-goal: Persistence stays scoped).
- ML, optimizer loops, or runtime-moving thresholds (anti-goal: No ML, no online tuning).
- Editing `docs/goal.md` or any human-authored journey/anti-goal (J-07 is human-authored; the proposer does not run this iteration).
- Real-vendor / Alpaca datasets — the sweep is verified keyless on the committed fixture pair only.
- New frontend pages, panels, or nav entries.

## DEFINITION OF DONE

- [ ] `python -m app.research.pnl_scan --out <path>` on the committed fixture datasets **exits 0** and writes a scan report that evaluates `candidate-faster-warmup` against the champion over all train datasets and records, per candidate: train + hold-out net R/$ deltas, n per split, per-dataset breakdown, `survivor`, and `robustness`.
- [ ] On the fixtures the report shows **zero survivors** with `candidate-faster-warmup` labeled non-survivor/overfit (hold-out net R negative and/or n < the configured minimum); and afterward the champion pointer is STILL `v1/default` (via `GET /research/profiles`), the PnL ledger STILL has row_count 1 (founding row only), and the default fingerprint is STILL `4d665603569b9dbf`.
- [ ] A controlled **n ≥ minimum survivor scenario** is exercised by an automated test (enlarged fixture windows that legitimately arm n ≥ min, or the config minimum dialed inside the test — never by weakening the shipped gate): it moves the persisted champion pointer AND appends **exactly one** provenance-stamped PnL-ledger row via `append_validation_row`, WITHOUT modifying `default` or any engine default.
- [ ] The **min-n gate is enforced both ways** by tests: a below-min candidate is rejected even with positive hold-out net R/$; an at-or-above-min candidate with positive hold-out net R AND net $ is promoted.
- [ ] Re-running the identical scan produces a **byte-identical** scan report (determinism under fixed seeds).
- [ ] `robustness` is `robust` iff positive on every train dataset individually, else `speculative`; a train-positive/hold-out-negative candidate is labeled **overfit** and never promoted — both asserted by tests.
- [ ] Target journey J-07 passes via the goal-evaluator's verification (backend suite + a live/in-page `python -m app.research.pnl_scan` run — no golden replay script exists for this machine-surface journey, per the iter-2 lesson).
- [ ] Required-still-passing journeys remain green: J-01 / J-05 / J-08 via golden replay; J-02 / J-03 / J-04 / J-06 via the backend suite + in-page fetch.
- [ ] `apps/backend/tests/test_no_execution_path.py` remains green and now also scans `app/research/pnl_scan.py`.
- [ ] No anti-goal violation introduced (all ten restated above).
- [ ] Full backend suite passes with no regressions (≥ iter-6 baseline of 1004 passed / 1 skipped; no tests deleted) and observer-equivalence stays 7/7.
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit-iter-7-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none new — J-07 is a machine surface with no frontend page, and no golden replay script exists or is created for it (iter-2 lesson: `demo_runner.py` supports only goto/click/fill and rewrites backend URLs onto the frontend base). Required-still-passing browser coverage rides J-01 / J-05 / J-08 golden replays; verify a result row exists per replayed journey rather than trusting the merge header (iter-1 lesson).
- **Unit/integration (backend, `app/research/pnl_scan.py` + `profiles.py` + store):**
  - Fixture sweep → zero survivors, exit 0, champion unmoved (`v1/default`), no ledger row appended, `candidate-faster-warmup` labeled non-survivor.
  - Controlled n ≥ min survivor scenario → champion pointer moves, exactly one ledger row appended via `append_validation_row`, provenance-stamped; `default` profile + engine defaults untouched.
  - Determinism → two identical scans produce byte-identical `--out` reports.
  - Min-n gate both ways (below-min rejected despite positive R/$; at-or-above-min positive-both promotes).
  - `robustness` robust vs speculative; overfit (train-positive/hold-out-negative) labeled and never promoted.
  - Champion single-source: `GET /research/profiles` reflects the persisted pointer; default fingerprint `4d665603569b9dbf` unchanged after any promotion (cross-check against the J-04 founding-ledger provenance fingerprint per the iter-6 lesson).
  - `test_no_execution_path.py` extended to cover `pnl_scan.py`.
- **Error cases (explicit, distinct states — no fabrication):** zero registered candidates → honest report + exit 0; corrupt/unreadable dataset → explicit error, no partial write; store unavailable during a promotion → explicit failure, no half-applied champion move or orphan ledger row.

## NOTES

- **Depth = full** justification is in BACKGROUND: data-model mutation (champion pointer + ledger append) + tests beyond browser smoke + the only anti-goal-gated state mutation on the goal-closing journey; the iter-6 evaluator recommended full for exactly this. Prior verdict was CONTINUE (no ESCALATE), so this is a deliberate risk-budget call, not a forced escalation.
- **Lessons applied:**
  - *iter-4:* the committed fixture pair arms only n=1 per split (train net_r ≈ −0.16, hold-out ≈ +0.3334, both < min 5). The fixture sweep therefore MUST report zero survivors + exit 0; a real promotion requires a distinct n ≥ min scenario. Do not "make it fire" by weakening the shipped gate.
  - *iter-2:* machine-surface journeys get no golden replay script (`demo_runner.py` has no POST and rewrites localhost URLs onto the frontend). Route J-07's durable regression coverage through the backend suite; drive the CLI/API legs via a live run or in-page `fetch()` from a backend-origin page.
  - *iter-6:* the strongest "default frozen" cross-check is the founding PnL-ledger row's stored `config_fingerprint` (`4d665603569b9dbf`) — assert it still equals the default backtest fingerprint after any promotion, since promotion machinery perturbing the default engine path would silently drift it. Also: J-05/J-08 golden-replay `*-verify.png` final frames land on the Studies page, not each journey's own surface — not a regression.
  - *iter-3:* before diagnosing a "flaky browser" or unexplained sqlite `Disk quota exceeded` during the full suite / replay lane, check `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota (root cause of prior instability; may still be outstanding) and route pytest basetemp off tmpfs if needed.
- **Champion-pointer coherence:** the single riskiest coherence point is that `GET /research/profiles` must read the champion from ONE persisted source (retiring the `profiles.py` constant), so there is never a constant-vs-persisted divergence. The coherence-auditor should confirm exactly one champion source and one ledger-append writer.
- This is the **goal-closing** iteration: a passing J-07 with all required-still-passing journeys green and no anti-goal violation makes the next evaluation a GOAL_ACHIEVED candidate (subject to the deterministic gates + two-key confirm).
