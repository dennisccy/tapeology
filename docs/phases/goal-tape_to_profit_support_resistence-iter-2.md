# Goal Iteration 2 — Deterministic, lookahead-free support/resistance levels (J-02)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit_support_resistence
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-02
- **Required-still-passing journeys:** J-01, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
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

Given a symbol and an as-of time, the machine surface `GET /research/levels` (and its read-only MCP proxy) returns deterministic, **lookahead-free** support/resistance levels — each carrying price, timeframe, type, touch count, and strength — computed once from the committed multi-timeframe bar store, keyless-verifiable on the PG fixture.

## BACKGROUND

J-01 (the multi-timeframe bar store) passed in iter-1; J-02 is the natural dependency successor and the first consumer of that store — it unblocks the entire downstream chain (J-03 confluence clusters these levels; J-04–J-06 arm/size/measure against classified levels). Per the priority rubric this is the correct single target: no journey regressed (skip rule 1), coherence was **COHERENCE-PASS** so no consolidation is owed (skip rule 2), and J-02 is the unblocker (rule 3) with the smallest self-contained change set (rule 4). Depth is **full** — chosen for three "Picking depth" triggers plus the prior evaluator's explicit recommendation: (a) it introduces a **new canonical data-model computation** (levels — blueprint Data-Contract Row 39) with a new serving endpoint; (b) it requires **new correctness tests beyond browser smoke** (a lookahead-free proof and a byte-identical determinism proof); and (c) it introduces the **critical no-lookahead anti-goal**, a subtle property whose silent violation would invalidate every downstream journey J-03–J-06 — it warrants the skeptical audit a full pass provides. This is a **backend-only, machine-surface** iteration (blueprint IA: J-02's home is `GET /research/levels` + MCP `levels`, no nav home); no frontend changes, so J-07's archived surfaces are guarded by an empty frontend diff plus engine equivalence.

**Lessons applied (from `lessons.md`, iter-1 — directly matches this iteration):** J-02 adds config-owned S/R fields (pivot lookback N, touch tolerance, timeframe weights, etc.). Two traps: (1) **the `config_fingerprint()` pinned-hash trap** — `Config().config_fingerprint()` hashes every non-excluded field against the literal pinned `4d665603569b9dbf`; these new S/R fields do NOT shape the `default` tape-engine output (levels are a separate research computation), so each MUST be added to the `excluded` set in `config.py` or the `default` fingerprint silently moves and J-07 equivalence breaks. (2) **vendor-name-forbidden modules** — the new S/R module is a canonical/engine module: `tests/test_real_data_gate.py::test_engine_and_canonical_modules_reference_no_vendor` fails if a vendor name (e.g. "Alpaca") appears anywhere in it, even in comments; keep vendor specifics confined to `providers/adapters/alpaca.py`.

## IN SCOPE

### Backend
- [ ] A new config-owned S/R detection module (its own file under `apps/backend/app/research/`, e.g. `levels.py`) that, from a stored bar series, derives horizontal level candidates per timeframe:
  - **swing pivots** — a bar's high/low that is the extreme over its ±N neighbours (N config-owned);
  - **prior-period extremes** — prior day/week/month high/low/close;
  - each level carries **price, timeframe, type** (`swing-pivot` | `prior-period-extreme`), **touch count**, and **strength = timeframe-weight × touch count**; every parameter (pivot lookback N, touch tolerance, per-timeframe weights) sourced from config — **no magic numbers, no fitting, no ML**.
- [ ] **Lookahead-free** as-of computation: levels "as of" time T use ONLY bars with timestamp ≤ T; a level at T is provably unchanged by any bar after T.
- [ ] Levels are **computed once**, owned by the one canonical module, and read verbatim by REST + MCP (single source of truth — no second computation path).
- [ ] New endpoint `GET /research/levels?symbol=<S>&as_of=<ISO-T>` in `apps/backend/app/research/routes.py` (mirroring the bars/datasets route discipline) returning the level list; an empty result surfaces an explicit honest **"no levels found"** state (never fabricated, never a silently-empty success masking an error).
- [ ] Read-only MCP `levels` tool in `apps/backend/app/mcp/__init__.py` that proxies `GET /research/levels` **byte-identically** (adds no computation). Note: unlike no-arg static tools (`bars`/`datasets`), `levels` requires `symbol` + `as_of` arguments — follow the parametrized `_TAPE_PATHS`-style pattern (or the allowlisted `get_endpoint`), not the no-arg `_STATIC_PATHS` copy.
- [ ] Add every new S/R config field to the `config_fingerprint()` **`excluded`** set in `apps/backend/app/config.py` (with a one-line rationale comment matching the existing exclusion style), keeping `Config().config_fingerprint() == '4d665603569b9dbf'`.

### Frontend (if applicable)
- None. Machine-only surface (REST + MCP). The frontend MUST NOT change this iteration (a future levels view is explicitly out of the data-foundation scope).

### New user-facing capability
None in the browser UI. A new **machine/research** capability: given a symbol + as-of time, an agent or researcher reads deterministic, lookahead-free S/R levels via `GET /research/levels` or the MCP `levels` tool.

### New information displayed
No browser-UI change. Newly served (machine surface): per-level **price, timeframe, type, touch count, strength**, keyed by symbol + as-of time.

### New user actions
None (no UI controls; read-only machine surface).

### UI surface changes
None.

### Product surface delta
The first **structural read** on top of the era-4 bar store: the product can now answer "where are the deterministic support/resistance levels for symbol S, as of time T?" — computed once, lookahead-free, and identical across REST and MCP. This is the substrate J-03 (confluence classes) and J-04 (tape-confirmed entries) build on.

### Blueprint conformance
Machine surface only — J-02's canonical home `GET /research/levels` + MCP `levels` is **already listed** in the blueprint Information Architecture machine-surfaces table (and the MCP tool set already anticipates `levels`). No nav-skeleton change; no `blueprint.reapproval-requested` needed.

### Data-contract additions
**None.** J-02 delivers the **levels half** of the already-registered blueprint **Row 39** ("Support/resistance levels + A/B/C confluence classes" — single owner: the NEW S/R + confluence module; single endpoint: `GET /research/levels` + MCP `levels`). Every value J-02 introduces (price, timeframe, type, touch count, strength) is exactly the per-level fields Row 39 already names. The confluence/class half of Row 39 is J-03 and is out of scope here. No new row, no second owner, no second endpoint — read levels only from the one canonical module.

## OUT OF SCOPE

- **Confluence zones and A/B/C classification (J-03).** Row 39 bundles levels + classes, but J-02 ships levels only; the endpoint may reserve an absent/empty classes field for J-03. No clustering, scoring, or grading logic this iteration.
- **The `structure_tape` strategy, class-scaled stop/reward/size, and the named-strategy comparison (J-04, J-05, J-06).** No strategy registry, no backtest wiring, no PnL, no champion/promotion code.
- **Any levels/bars UI view** — explicitly out of the data-foundation scope per Product Shape.
- **Recording NEW real bars (credentialed).** J-02 reads the committed keyless PG fixture (`1h` + `1d`); it does not fetch from the vendor. (Extending the committed fixture with MORE real bars, if needed for a meaningful pivot test, is a credentialed action via `apps/backend/scripts/generate_bar_fixtures.py` using REAL captured data only — never synthesized bars.)
- **A symbol-tradability / "why is this empty" distinction** — carried-forward iter-1 probe finding: an unknown symbol and an empty window currently both surface the same 422 on the bars path. Add a tradability distinction ONLY if J-02 genuinely needs to explain why a level set is empty; otherwise the honest "no levels found" state is sufficient.
- **Any change to the tape engine, `default` profile, `v1`, or the live cockpit.**

## DEFINITION OF DONE

- [ ] Target journey **J-02 passes** (verified by browser-qa-agent against the machine surface: `GET /research/levels` + MCP `levels`, since this is a backend-only journey).
- [ ] `GET /research/levels?symbol=PG&as_of=<T>` returns levels each carrying **price, timeframe, type** (`swing-pivot`|`prior-period-extreme`), **touch_count**, and **strength** — asserted by a new acceptance test with exact expected values on the committed PG fixture.
- [ ] **Lookahead-free test**: a level computed as-of T is **byte-identical** whether or not bars after T are present in the store (proves a level at T is unchanged by any later bar).
- [ ] **Byte-identical determinism test**: two independent runs on the committed PG fixture produce identical levels JSON.
- [ ] **MCP `levels` byte-identity test**: the `levels` tool output equals `GET /research/levels` byte-for-byte on a non-empty live result (mirroring iter-1's `test_bars_tool_byte_identical_on_a_non_empty_live_list`).
- [ ] **No magic numbers**: a grep/test proves every S/R parameter in the levels module is read from config.
- [ ] **J-07 sentinel intact**: `Config().config_fingerprint() == '4d665603569b9dbf'` (new S/R fields excluded), and the engine equivalence suites (`tests/test_observer_equivalence.py` + `tests/test_profile_equivalence.py`) stay green (byte-identical `default`).
- [ ] `git diff <pre-iteration snapshot>..HEAD -- apps/frontend/` is empty (backend-only; J-07 archived surfaces untouched).
- [ ] **Honest empty state**: a symbol/as-of with no derivable levels returns an explicit "no levels found" state — no fabricated levels, no silent empty-as-error.
- [ ] Required-still-passing journeys **J-01, J-07 remain green**.
- [ ] No anti-goal violation introduced (verified against the verbatim list above).
- [ ] Full backend unit/integration suite passes; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** N/A — machine-only surface (REST + MCP). J-02 is verified via the API + MCP acceptance suite; J-07's archived browser surfaces are verified unchanged by the empty frontend diff + engine equivalence (backend-only phase; UI steps write N/A stubs).
- **Unit/integration (must have real assertions, exact values, not just "runs"):**
  - swing-pivot detection over ±N neighbours (config-driven N) and prior-period-extreme extraction, on the committed PG `1h` + `1d` fixture;
  - strength = timeframe-weight × touch-count computed with config-owned weights;
  - the as-of **lookahead-free** filter (bars ≤ T only) — the headline correctness test;
  - byte-identical determinism across re-runs;
  - `GET /research/levels` route (happy path + honest empty state);
  - MCP `levels` proxy byte-identity vs the REST endpoint;
  - `config_fingerprint` stability at `4d665603569b9dbf` (new fields excluded) + a real-threshold counter-test proving a *computational* config change would still move it.
- **Error cases (must be rejected / surfaced explicitly, never fabricated):**
  - unknown symbol or no derivable levels → explicit "no levels found" state (not a fabricated/empty-masked success);
  - out-of-set timeframe in any bar series → the existing explicit 422 discipline;
  - malformed / missing `as_of` → 422 (never a silent "now" default that would leak lookahead);
  - no recorded bar series for the requested symbol → explicit distinct state (not an empty-levels success).

## NOTES

- **Naming disambiguation (carry the iter-1 coherence advisory forward):** the engine already has intraday **tape** setups named `level_break` / `failed_move_fade` (config:487, config:1133) — a DIFFERENT concept from era-4 **structural** S/R levels. Give the new structural-level config a distinct namespace (e.g. `sr_*` / `structure_level_*`) and distinct serialized field names so the two "level" concepts do not collide in config or JSON — the same discipline the iter-1 diff used to separate the two "bar" concepts.
- **Keyless substrate is real and multi-timeframe:** committed fixtures cover symbol **PG** at `1h` (9 bars, 2026-06-09) and `1d` (5 bars, early June 2026), feed `sip`. Prior-period extremes are computable on the `1d` series; swing pivots need 2N+1 bars, so choose a small config N (or record MORE real PG bars via `scripts/generate_bar_fixtures.py`) so the acceptance suite has ≥1 swing pivot AND ≥1 prior-period extreme to assert — do NOT synthesize bars to pad the fixture (no-fabricated-data anti-goal).
- **Endpoint shape reserves room for J-03:** `GET /research/levels` returns levels now; keep the response shape such that J-03 can add confluence zones/classes additively (absent or empty classes field this iteration) without a breaking change.
- **Carried-forward iter-1 probe findings:** (1) monthly-bar vendor depth on the free plan stops at 2016-01-01 — context for future real-data level computation, not exercised by the keyless fixture; (2) unknown-symbol vs empty-window both surface the same 422 today — see the OUT OF SCOPE tradability note.
- **Depth = full** is justified by three "Picking depth" triggers (new canonical data-model computation + new endpoint; new correctness tests beyond browser smoke; the critical no-lookahead property needing skeptical audit) and matches the iter-1 evaluator's explicit `Depth Recommendation For Next Iteration: full`.
- No blueprint edit was required this iteration (Row 39 + the IA machine-surface home for `GET /research/levels`/MCP `levels` were registered at baseline); `blueprint.md` is already current for J-02.
