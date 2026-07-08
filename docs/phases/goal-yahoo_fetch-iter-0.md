# Goal Iteration 0 — Baseline: verify all Era-5 "The Library" journeys against current state

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** yahoo_fetch
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06
- **Required-still-passing journeys:** none (baseline — this iteration establishes the passing/failing/partial set that later iterations preserve)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**

  _Immutable rails — the identity of the project (copied verbatim from `docs/research-directions.md` §0.3; enforced by existing tests and audits; only ever grow more specific, never weaker):_
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

  _Era-5-specific anti-goals (added, not weakening any rail above):_
  - **The SQLite index is a derived cache, never a source of truth.** Canonical bars stay the append-only, checksummed JSON `BarStore`; every served candle is checksum-verified from it; the index holds metadata only, is rebuildable via `reindex()`, and its loss or corruption loses and fabricates nothing. A second authoritative bar store is a defect. *(critical)*
  - **Fetching is explicit and store-first.** Historical data is fetched only on an explicit user action; an already-stored window is served from storage without re-hitting Yahoo; there is no ambient or background polling. *(critical)*
  - **Yahoo data is fetched-and-stored only, never re-tagged or pooled across feeds.** A `feed="yahoo"` series is append-only and checksummed; it is never merged with, re-tagged to, or analytically pooled with `sip` or any other feed. *(critical)*
  - **`4h` is honestly derived.** It is a pure, deterministic resample of real `1h` bars, unit-tested for OHLC aggregation and bucket alignment, documented as derived; it is never presented as a vendor-native fetch and never fabricated. *(critical)*
  - **No fabricated bars, ever.** A symbol/window/timeframe Yahoo cannot serve (out of retention, unsupported interval, network failure) returns an explicit neutral error; the fetch never synthesizes, forward-fills across gaps, or pads a partial window to force a green journey. *(critical)*
  - **No new levels/PnL/strategy/champion computation.** This era feeds real bars to the existing era-4 owners and adds no second computation of levels, zones, PnL, aggregates, strategies, or the champion; the only new backend computation is the Yahoo fetch + `4h` resample confined to `adapters/yahoo.py` and the derived lookup index. *(critical)*
  - **The UI fetch stores bars only.** The `/structure` fetch control performs an explicit bar fetch/store; it computes no levels, PnL, or champion, and it never promotes. *(critical)*
  - **Yahoo default must not break the Alpaca path.** Making Yahoo the default bar vendor is additive: the Alpaca adapter, its credential gate, and its bar/tick/live paths stay byte-identical and selectable (opt-in). *(critical)*
  - **Dependency discipline.** `yfinance` is pinned in `requirements.txt` (confined to `adapters/yahoo.py`) and added to the install-security-policy allowlist; no unpinned/dynamic install, no other new runtime dependency. *(critical)*
  - **No vocabulary drift.** No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Establish the honest starting line for Era 5 "The Library": run every Must-have journey (J-01–J-06) against the current codebase and record which already pass, which fail, and which are partial — with **no** code changes.

## BACKGROUND

This is the **baseline assessment**, not a feature delivery — the developer step is a no-op; the value comes entirely from browser-qa + the backend/equivalence suite running every journey to snapshot reality. Era 5 (bars/structure side, keyless) layers a Yahoo Finance bar adapter, a store-first SQLite index, and a `/structure` fetch control on top of the frozen eras 1–4 + structure-UI foundation. Codebase inspection this iteration (evidence, to be confirmed by the executor, **not** scored here) shows: **no** `apps/backend/app/providers/adapters/yahoo.py`, **no** `apps/backend/app/research/bar_index.py`, and no `"yahoo"` entry in `research/taxonomy.py` `FEED_BASIS_LABELS` (only `sim`/`iex`/`sip`) — so the fetch/store/index/provenance capabilities (J-01, J-02, J-03, J-05) have no implementation and are expected to read as failing; J-04 (real levels on real Yahoo bars) is expected to fail as a *consequence* of J-01 (the `research/levels.py` machinery is present, but no `feed="yahoo"` bars exist for it to compute on); J-06 (foundation regression sentinel) is expected to pass since nothing has changed. Depth is **lean** per the baseline-mode rule (lean cycle is sufficient — no code is written; the browser-qa + suite steps carry the value); there is no prior evaluator verdict and no ESCALATE. Lessons ledger is empty (first iteration), so no prior pitfall applies.

## IN SCOPE

### Backend
- [ ] None — verify-only baseline. No source files are modified this iteration.

### Frontend (if applicable)
- [ ] None — verify-only baseline. No source files are modified this iteration.

### Verification tasks (no code)
- [ ] Run J-01 (Yahoo fetch, keyless): attempt to fetch a daily window keyless and read it back via `GET /research/bars`, `GET /research/bars/{id}`, and the MCP `bars` tool; check for a `feed="yahoo"`-stamping adapter path and append-only/`409`-on-duplicate store behaviour. Record the result and observed absence/presence.
- [ ] Run J-02 (full timeframe set incl. derived 4h): probe whether `1w/1d/4h/1h/5m/1m` fetch is supported and whether a deterministic `1h`→`4h` resampler exists; record.
- [ ] Run J-03 (store-first SQLite index): probe for a derived `bar_index.py`, store-first idempotence (no second Yahoo call on a repeat window), and the additive `GET /research/bars?symbol=&timeframe=` filter; record.
- [ ] Run J-04 (real S/R levels + A/B/C zones on real Yahoo bars): call `GET /research/levels?symbol=&as_of=` and confirm whether real, non-empty levels/zones from `feed="yahoo"` bars can be produced (expected: not yet, pending J-01); confirm REST/MCP `levels` agreement on whatever exists; record.
- [ ] Run J-05 via browser-qa-agent: on `/structure`, attempt to locate a fetch control (symbol + timeframe + date range + "Fetch from Yahoo Finance" button) and a "Yahoo Finance" provenance badge; record the honest observation (expected absent at baseline).
- [ ] Run J-06 (foundation sentinel): execute the full backend suite + engine equivalence test, confirm `config_fingerprint` is `4d665603569b9dbf`, confirm the no-param `GET /research/bars` shape is unchanged, and spot-check `/`, `/journal`, `/studies`, `/performance`, and the existing `/structure` read behaviours in the browser; record the result.

### New user-facing capability
None — this iteration delivers no capability. It records the baseline pass/fail/partial state of the six journeys.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product is unchanged after this iteration. Its only output is a recorded baseline of journey states.

### Blueprint conformance
No new surfaces this iteration. The blueprint (`runs/goal-session-yahoo_fetch/state/blueprint.md`) is drafted alongside this spec: the nav skeleton is **unchanged** (Cockpit · Journal · Studies · Performance · Structure, data-driven via `GET /meta/ui-routes`); the future fetch control lives as a section of the existing `/structure` page. No page is created this iteration.

### Data-contract additions
None this iteration (verify-only). The blueprint registers the **one** new owned value Era 5 will introduce — bar-series provenance `feed="yahoo"`, owned by the canonical `BarStore` + the Yahoo adapter (the adapter is the sole source of the `feed` stamp), its human label owned by `research/taxonomy.py` `FEED_BASIS_LABELS`, read via `GET /research/bars*` + `GET /research/taxonomy`. The derived SQLite bar index **owns nothing**. Every other displayed value stays owned by its existing era-1–4 canonical source and read verbatim. No value is introduced by this baseline iteration.

## OUT OF SCOPE

- Any code change whatsoever (no `yahoo.py`, no `bar_index.py`, no `taxonomy` label, no `/structure` fetch control, no `requirements.txt`/allowlist edit — those begin in iteration 1).
- Any edit to `config.py` (fingerprint `4d665603569b9dbf`), `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, the JSON `BarStore`, the Alpaca adapter, or any existing surface.
- Any **live network** call to Yahoo Finance — the baseline records current state only; the live keyless fetch is exercised later under the `integration` marker (`TAPEOLOGY_LIVE_INTEGRATION=1`), never in the default suite.
- Marking journeys as passing/failing — that is the goal-evaluator's job; this spec only requests they be exercised and recorded.
- The `/datasets` library-management UI and the tick-tape backfill recorder — both explicitly out of scope for this chapter (roadmap Cards 5.2 tick-side / 5.9).

## DEFINITION OF DONE

- [ ] All six Must-have journeys (J-01, J-02, J-03, J-04, J-05, J-06) are exercised against the current HEAD and each has a recorded outcome (pass / fail / partial) with evidence.
- [ ] The full backend suite and the engine equivalence test are run and their current result recorded, with `config_fingerprint` observed and noted (baseline for the J-06 sentinel).
- [ ] The no-param `GET /research/bars` response shape is captured as the baseline the later `symbol`/`timeframe` filter must stay byte-compatible with.
- [ ] No source files changed — `git diff` over `apps/` is empty (only run/report artifacts written).
- [ ] No anti-goal violation introduced (trivially satisfied — no code changes).
- [ ] Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-0-dev.md` noting this was a verify-only baseline (developer no-op).

## TESTING REQUIREMENTS

- **Browser:** J-05 (attempt to locate and drive a `/structure` Yahoo fetch control + provenance badge — expected absent at baseline; record the honest "not present" observation) and J-06 (spot-check the existing `/`, `/journal`, `/studies`, `/performance`, `/structure` surfaces still work).
- **API/MCP:** J-01/J-02/J-03/J-04 exercised against the running backend — `GET /research/bars` (+ `/{id}`, `?symbol=&timeframe=`), `GET /research/levels`, `GET /research/taxonomy`, and the MCP `bars`/`levels` proxies — recording current behaviour and the absence of a Yahoo-stamped path.
- **Unit/integration:** run the full backend test suite and the engine equivalence test as the J-06 baseline; record pass counts and the observed `config_fingerprint` (expected `4d665603569b9dbf`). Default suite stays hermetic — **no network**.
- **Error cases:** none introduced this iteration — no new inputs exist yet; honest-empty/degraded states (out-of-retention, unsupported timeframe, no-bars-for-symbol, network failure) are only *observed as not-yet-implemented*, not exercised.

## NOTES

- **Baseline framing:** the goal-evaluator will classify already-passing journeys as `already_passing` so later iterations skip them. Expected baseline read (evidence-based, evaluator to confirm — **not** the verdict): J-01/J-02/J-03/J-05 fail (no Yahoo adapter, no SQLite index, no fetch control), J-04 fails as a consequence of J-01 (levels machinery present but no `feed="yahoo"` bars to compute on), J-06 passes (foundation untouched; `config_fingerprint` `4d665603569b9dbf`). Do not treat these expectations as the verdict.
- **Dependency order for later iterations** (from `docs/goal.md`): J-01 → J-02 → J-03 → J-04 → J-05, with **J-06 guarding continuously**. Iteration 1 will likely target **J-01 alone** — the Yahoo adapter is a provider integration (a *risky* iteration by the rubric: new runtime dependency `yfinance` + vendor selector + `feed`-stamp sourcing) and unblocks every downstream journey, so it should not be bundled with any other risky change. Expect iteration 1 to be **full** depth (backend + data-path + new tests + dependency/allowlist gate).
- **Blueprint drafted this iteration:** `runs/goal-session-yahoo_fetch/state/blueprint.md` — Information Architecture (nav **unchanged**; the fetch control is a section of the existing `/structure` page) + a Data Contract that adds exactly one new owned value (`feed="yahoo"` provenance) and marks the derived SQLite index as owning nothing. Auto-approved by default; the loop proceeds to iteration 1 unless `--require-blueprint-approval` was passed. No nav-skeleton change ⇒ no `blueprint.reapproval-requested`.
- **Foundation-freeze reminder for the executor:** the additive changes this era permits are exactly the Yahoo adapter, the bar-vendor selector, the `feed`-stamp sourcing, the SQLite index + store-first coordinator, the additive `symbol`/`timeframe` filter, the `"yahoo"` taxonomy label, the `/structure` fetch control + provenance badge, and the pinned `yfinance` + allowlist entry. Everything else — `config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, the JSON `BarStore`, and the Alpaca path — stays byte-identical.
- The canonical endpoints the fetch control will read (`/research/bars`, `/research/levels`, `/research/strategies`, `/research/profiles`, `/research/datasets`, `/research/backtests` + `/{id}`, `/research/pnl/ledger`, `/research/taxonomy`, `/meta/ui-routes`) and the frozen owners (`research/bars.py` `BarStore`, `research/levels.py`, `research/taxonomy.py` `FEED_BASIS_LABELS`, `providers/adapters/` with Alpaca present) were confirmed present in the codebase this iteration; only the Yahoo adapter and the derived index are net-new.
