# Goal Iteration 3 — J-03: confluence zones + A/B/C conviction classes

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit_support_resistence
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`; most load-bearing for J-03: No lookahead · No ML/no online tuning · No fabricated data · Single source of truth · frozen `default`/`v1` · MCP read-only):**
  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets. The ONLY permitted "fill" is the offline backtester's simulated fill against recorded historical tape, clearly labelled simulated and sent nowhere; "position size" is a simulated notional, never a real order. *(critical)*
  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — never presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
  - **The tape engine, `default` profile, and `v1` strategy are frozen.** Structure work is additive and versioned only: new bars/levels/classes and the `structure_tape` strategy may be added, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, `v1` stays byte-identical, and no enhancement may mutate an archived-era behaviour to pass. *(critical)*
  - **No train-only promotion.** Nothing becomes the champion on train data alone: hold-out survival (net R AND net $, at the configured minimum n) is the only promotion gate; overfit results are labelled overfit. *(critical)*
  - **No lookahead.** Levels and classes computed "as of" time T use only bars at or before T; a backtest may never see a level derived from data after the moment it is used. *(critical)*
  - **No ML, no online tuning.** S/R detection, confluence scoring, class thresholds, and class-based risk are bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops in the engine, no thresholds that move at runtime.
  - **No fabricated data — honest failure states.** No synthesized bars, levels, trades, fills, or PnL to force a green journey; every failure mode (backend down, corrupt file, empty window, missing credentials, rate-limited, no levels found, insufficient n) surfaces an explicit, distinct state. *(critical)*
  - **Single source of truth.** Every canonical value — bar series, levels, confluence classes, backtest aggregates, PnL rows — is computed once and read verbatim by every surface (REST, WebSocket, UI, MCP, reports). A second computation path or a diverging number across surfaces is a defect. *(critical)*
  - **No capital or portfolio management.** Class "position size" is a per-trade simulated notional only — no account, no equity curve, no compounding projection, no real position tracking. *(critical)*
  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
  - **Persistence stays scoped.** SQLite holds research records; the bar and dataset stores hold explicitly recorded historical bars and tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

A researcher calling `GET /research/levels` (and the read-only MCP `levels` tool) receives, beside the raw support/resistance levels, the **confluence zones** that cluster those levels across timeframes — each zone carrying its member levels (with timeframes), a timeframe-weighted score, and an honest **A / B / C** conviction class.

## BACKGROUND

J-01 (bar store) and J-02 (deterministic, lookahead-free S/R levels) are passing; iter-2's evaluator returned CONTINUE with a `full` recommendation and named J-03 as the natural next step, iter-2's coherence was COHERENCE-PASS (no consolidation owed). Following the priority rubric: no journey is regressed (rule 1 n/a), no coherence FAIL to consolidate (rule 2 n/a), and **J-03 is the unblocker** — it produces the A/B/C classified zones that J-04's `structure_tape` entries arm at and that J-05's class-scaled risk consumes, and it shares blueprint Data-Contract Row 39 with J-02 (rule 3). It is also the smallest change set — a single additive field on the *existing* `GET /research/levels` response, computed in the *existing* `research/levels.py` owner (rule 4) — and it is the only risky journey carried this iteration (rule 5). Depth is **full** by the "Picking depth" triggers (cited, not because of ESCALATE — prior verdict was CONTINUE): it (a) introduces a new canonical computation (confluence clustering + timeframe-weighted scoring + A/B/C grading), (b) requires new correctness tests beyond browser smoke (deterministic clustering, byte-identical re-runs, config-owned thresholds, honest labelling), and (c) extends the **critical no-lookahead** property to classes — and, being a machine surface with no browser smoke to catch a wiring slip, the test suite IS the acceptance, which warrants the fuller audit/QA/coherence pass.

## IN SCOPE

### Backend
- [ ] Add config-owned confluence parameters to `apps/backend/app/config.py`, `sr_`-namespaced and each documented with rationale (no magic numbers): a **clustering tolerance / confluence band** (e.g. `sr_confluence_band_bps`) and the **A/B/C class thresholds** (e.g. score cutoffs and/or the confluence criteria such as minimum distinct timeframes / required long-term member). **Add every new field to the `config_fingerprint()` `excluded` set** (the same rationale as the three existing `sr_*` level fields at `config.py:1320-1322`) — they are a separate research computation input, never a tape/backtest/PnL value; the pinned `default` fingerprint MUST stay `4d665603569b9dbf` (iter-1 lesson: any non-excluded new field silently breaks J-07).
- [ ] Add deterministic, lookahead-free confluence clustering + A/B/C classification **inside the existing `apps/backend/app/research/levels.py`** (the registered Row-39 owner — NO new module, endpoint, or owner): cluster the levels already computed by `compute_levels` across timeframes whose prices fall within the config band into confluence zones; score each zone = timeframe-weighted sum of its member levels' strengths; grade it A/B/C by the config thresholds/criteria. Each zone records its **member levels (with timeframes)**, its **score**, and its **class**. Sort zones by an explicit total order so the served JSON is byte-identical.
- [ ] Return the zones as an **additive** field on `compute_levels`' existing return dict (e.g. `confluence_zones` / `classes`, beside `levels` and `no_bar_series_for_symbol`) — served verbatim by the existing `GET /research/levels` route and the existing read-only MCP `levels` proxy. No second computation path; MCP JSON stays byte-identical to REST.
- [ ] Honest labelling: a zone is class **A only when the config confluence criteria are met** (e.g. several timeframes including a long-term level within tolerance), honestly graded B/C otherwise; a symbol with no series keeps `no_bar_series_for_symbol: true` with an empty zones list; a symbol with levels but no qualifying cluster returns an explicit empty zones list — never a fabricated zone or class.
- [ ] Decide + document the corrupt-sole-series seam (iter-2 B1 lesson): confirm the confluence layer introduces **no new fabricated or aliased state** — it reads only the healthy levels `compute_levels` already produces; the *distinct* corrupt-series honest state remains owned by `GET /research/bars`. Record this decision in the dev handoff.

### Frontend
- N/A — J-03 is a machine surface (REST + MCP) only. The nav skeleton (Cockpit · Journal · Studies · Performance) is unchanged this era; `apps/frontend/` MUST NOT change.

### New user-facing capability
Through `GET /research/levels` (+ MCP `levels`), a researcher can now read the confluence structure of a symbol's S/R levels — which levels cluster across timeframes and how much conviction (A/B/C) each cluster carries — the structural conviction layer J-04's tape-confirmed entries will later arm at.

### New information displayed
Confluence zones on the `GET /research/levels` response: per zone, its member levels (each with timeframe), its timeframe-weighted score, and its A/B/C class.

### New user actions
None — read-only GET; machine surface, no new controls.

### UI surface changes
None — no page, panel, or nav change.

### Product surface delta
The levels endpoint graduates from a flat list of levels to "levels + their confluence conviction structure (A/B/C)". No visual/UI change.

### Blueprint conformance
J-03's output lives on the **already-registered Row-39 canonical home** — `GET /research/levels` + MCP `levels` (machine surface, no nav home) — exactly as the baseline blueprint's Information Architecture places it (feature-home table, "J-03 confluence zones + A/B/C classes | API `GET /research/levels` (same endpoint) + MCP `levels`"). No nav-skeleton change; no `blueprint.reapproval-requested` written.

### Data-contract additions
**None.** Blueprint Data-Contract **Row 39** ("Support/resistance levels + A/B/C confluence classes") already registers the confluence zones + A/B/C classes with a single owner (the S/R + confluence module in `research/levels.py`) and a single serving endpoint (`GET /research/levels` + MCP `levels`); its notes already name "confluence band, class thresholds" as config-sourced. J-03 ships the previously-out-of-scope **classes half** of that already-registered row — it adds no new canonical value and no new endpoint/owner, so the blueprint needs no edit. The new confluence config params (band, class thresholds) are computation **inputs**, not displayed values, so they take no Data-Contract row (config-owned + fingerprint-excluded, per Row 39's "every parameter config-sourced" note).

## OUT OF SCOPE

- **J-04** (`structure_tape` strategy / strategy registry / `GET /research/strategies`), **J-05** (class-scaled stop/reward/simulated size), **J-06** (named-strategy comparison vs `v1`) — later iterations.
- Any **new endpoint, MCP tool, or module** — the zones ride the existing `GET /research/levels` route, the existing MCP `levels` proxy, and the existing `research/levels.py` owner.
- Any **support-vs-resistance "kind" labelling** of a zone — a zone is a horizontal price cluster; whether it acts as support or resistance depends on the tape at approach time and is **J-04's** tape-confirmation concern (goal.md's J-03 acceptance requires only clustering, scoring, and A/B/C grading — not direction).
- Any **new distinct honest state for a corrupt SOLE bar series** at the levels endpoint — that honesty is owned by `GET /research/bars` (decide-and-document only; do not add a new state here).
- Any change to the **raw levels computation**, the bar store, the `default` profile, `v1`, or any archived-era surface.
- Any **frontend/UI/nav change**, any levels view, and any cross-timeframe bar aggregation.

## DEFINITION OF DONE

- [ ] **J-03 passes** — `GET /research/levels` (and MCP `levels`) returns confluence zones, each with its member levels (+ timeframes), a timeframe-weighted score, and an A/B/C class; verified by the backend acceptance suite (machine surface — the test suite IS the acceptance; browser-qa correctly N/A, documented).
- [ ] Clustering tolerance (confluence band) and A/B/C class thresholds/criteria are **config-owned** — a no-magic-numbers introspection test (extending `tests/test_levels.py`'s existing pattern) asserts no literal thresholds in `levels.py`.
- [ ] A zone is graded **class A only when the config confluence criteria are met**; a non-qualifying cluster is honestly graded B/C or absent — asserted with exact expected classes on the committed bar fixture.
- [ ] **Byte-identical** deterministic re-runs of the zones/classes (explicit total order) — asserted.
- [ ] **No-lookahead extended to classes** — zones/classes at as-of T derive only from bars ≤ T; a bar after T cannot change any zone or class — asserted in the same physical-truncation style as J-02.
- [ ] **MCP `levels` remains byte-identical** to the REST response including the new zones field (single source of truth) — asserted.
- [ ] **Required-still-passing J-01, J-02, J-07 remain green:** full backend suite passes; `Config().config_fingerprint() == '4d665603569b9dbf'` unchanged (new confluence fields in the `excluded` set); engine observer + profile equivalence byte-identical (`default`/`v1` frozen); `git diff <iter-3 base snapshot>..HEAD -- apps/frontend/` is empty.
- [ ] No anti-goal violation introduced (no ML/fitting, no lookahead, no fabricated zone, single source of truth, no second computation path, MCP read-only) — grep/scan CLEAN.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md` (including the corrupt-sole-series seam decision).

## TESTING REQUIREMENTS

- **Browser:** none — J-03 is a backend/machine surface (REST + MCP); browser-qa is correctly N/A. Documented reason: no frontend/UI/nav change (`apps/frontend/` untouched — the executor must confirm the empty frontend diff, per the iter-0/iter-2 lesson that zero-frontend-diff iterations need no screenshot evidence).
- **Unit/integration:** extend `apps/backend/tests/test_levels.py` + `tests/test_levels_api.py` — deterministic clustering into zones; timeframe-weighted score exactness; A/B/C grading on the committed fixture with **exact expected classes**; config-owned thresholds (no-magic-numbers introspection); byte-identical re-runs; no-lookahead-for-classes (physical truncation); honest empty-zones state and `no_bar_series_for_symbol` state. Extend the MCP byte-identity test to cover the new zones field. Extend/confirm the fingerprint-stability test so the new confluence config fields are excluded and the `default` fingerprint is unmoved.
- **Error cases:** symbol with no series → `no_bar_series_for_symbol: true`, empty zones (not fabricated); symbol with levels but no qualifying cluster → explicit empty zones list; invalid / out-of-set `as_of` handled by the existing route validation (unchanged — assert no regression); an unknown timeframe weight still raises rather than fabricating.

## NOTES

- **Lessons applied** (session `lessons.md`):
  - *iter-1 (config fingerprint + vendor names):* any new `Config` field silently moves the pinned `default` fingerprint (`4d665603569b9dbf`) and breaks J-07 unless added to the `config_fingerprint()` `excluded` set — the new confluence band + class-threshold fields (a separate research computation, never a tape/backtest value) MUST be excluded, exactly as the three `sr_*` level fields were. (Vendor-name-in-config is not a risk here — the confluence code touches no vendor SDK.)
  - *iter-2 (corrupt sole series):* `compute_levels` reads only the healthy half of `BarStore.list()`, so a corrupt SOLE series currently aliases to `no_bar_series_for_symbol: true`; the distinct corrupt-series state is owned by `GET /research/bars`. J-03 makes this a conscious decision — keep that ownership (confluence adds no new fabricated/aliased state) and document it; do not add a new corrupt state at the levels endpoint.
- **Single-source-of-truth discipline** (the coherence-auditor's central check): confluence zones are computed ONCE in `research/levels.py` (the Row-39 owner) and served verbatim by the one route + the one MCP proxy — no second computation path, no divergent serialization.
- The codebase already anticipates this additive field: `apps/backend/app/research/levels.py:2` and `apps/backend/app/research/routes.py:1631` both mark `classes` (J-03 confluence) as deliberately absent pending this iteration.
- References: iter-2 `eval.md` next-step recommendation (advance to J-03, full, additive `classes` field on the existing endpoint); iter-2 `coherence.md` COHERENCE-PASS (Row 39 canonical home confirmed).
