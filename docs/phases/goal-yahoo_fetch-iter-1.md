# Goal Iteration 1 — Keyless Yahoo Finance bar adapter + default bar-vendor selector (J-01)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** yahoo_fetch
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes  <!-- no NEW UI this iteration; the browser lane runs a J-06 foundation regression spot-check only (closes the iter-0 no-evidence gap) -->
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-06
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **Fetching is explicit and store-first.** Historical data is fetched only on an explicit user action; an already-stored window is served from storage without re-hitting Yahoo; there is no ambient or background polling. *(critical)*
  - **Yahoo data is fetched-and-stored only, never re-tagged or pooled across feeds.** A `feed="yahoo"` series is append-only and checksummed; it is never merged with, re-tagged to, or analytically pooled with `sip` or any other feed. *(critical)*
  - **No fabricated bars, ever.** A symbol/window/timeframe Yahoo cannot serve (out of retention, unsupported interval, network failure) returns an explicit neutral error; the fetch never synthesizes, forward-fills across gaps, or pads a partial window to force a green journey. *(critical)*
  - **No new levels/PnL/strategy/champion computation.** This era feeds real bars to the existing era-4 owners and adds no second computation of levels, zones, PnL, aggregates, strategies, or the champion; the only new backend computation is the Yahoo fetch + `4h` resample confined to `adapters/yahoo.py` and the derived lookup index. *(critical)*
  - **Yahoo default must not break the Alpaca path.** Making Yahoo the default bar vendor is additive: the Alpaca adapter, its credential gate, and its bar/tick/live paths stay byte-identical and selectable (opt-in). *(critical)*
  - **Dependency discipline.** `yfinance` is pinned in `requirements.txt` (confined to `adapters/yahoo.py`) and added to the install-security-policy allowlist; no unpinned/dynamic install, no other new runtime dependency. *(critical)*

## GOAL

With **no credentials configured**, fetching a daily window for a symbol stores a real Yahoo Finance OHLCV series stamped `feed="yahoo"` (append-only, checksum-verified) through the canonical `BarStore`, and it reads back byte-for-byte via `GET /research/bars`, `GET /research/bars/{id}`, and the MCP `bars` tool.

## BACKGROUND

Iteration 0 recorded the honest baseline: every Era-5 capability is absent (J-01–J-05 `failing`, J-06 `already_passing`). Per the priority rubric this iteration takes **J-01 alone** — the keyless Yahoo adapter is the unblocker whose completion feeds J-02 (timeframes), J-03 (store-first index), J-04 (levels on real bars), and J-05 (the `/structure` fetch control); it is a single risky change and must not be bundled with any other risky journey. **Depth is `full`** per the "risky provider integration + new runtime dependency, requires new backend tests beyond browser smoke" trigger (and the iter-0 evaluator's explicit `full` recommendation): a new `yfinance` runtime dependency plus a bar-vendor selector that flips the default fetch vendor is the highest-regression-risk change of the era. The primary regression vector — confirmed in the codebase — is that `get_adapter()` (`apps/backend/app/main.py:129`) feeds the live cockpit / tick / live / search / clock, while `get_study_market_adapter()` (`apps/backend/app/research/routes.py:1220`) feeds the bar-fetch path; Yahoo is **bars-only** (its tick/live/search honestly raise or return empty), so the Yahoo default must land on the **fetch** seam only and must NOT change the global live accessor — that is the exact "Yahoo default must not break the Alpaca path" anti-goal and the crux of J-06 protection.

**Lesson applied (iter-0):** the lean baseline's browser-qa lane did NOT run (`browser_checks_run:false`, empty evidence dir, no `ui-test-results.md`) and no `coherence.md` was produced. This iteration is `full` and marks **Frontend Present: yes** specifically so the browser lane runs a **J-06 foundation regression spot-check** (existing surfaces still render after the vendor-selector/backend change) and so the **coherence audit runs and clears** the new `feed="yahoo"` owned value — the two process requirements the iter-0 evaluator named for iteration 1.

## IN SCOPE

### Backend
- [ ] Add `apps/backend/app/providers/adapters/yahoo.py` implementing the `MarketDataAdapter` protocol (`apps/backend/app/providers/adapters/base.py:166`): `name = "yahoo"`, keyless `is_available()` (returns `True` with no credentials), and `fetch_bars(symbol, start, end, timeframe)` mapping the neutral timeframe(s) to `yfinance` intervals. Its tick / live / search methods **honestly raise or return empty** (Yahoo is bars-only). `volume` is coerced to `int`. New module confined to this file.
- [ ] Add a **bar-vendor selector** so the bar-**fetch** path defaults to Yahoo while Alpaca stays selectable (opt-in). Extend the fetch-path adapter accessor(s) — `get_study_market_adapter()` (`research/routes.py:1220`) and the `POST /research/bars` handler (`research/routes.py:191`) — **only**. Do NOT change the global live accessor `get_adapter()` (`main.py:129`): the cockpit / tick / live / search / clock paths must keep resolving to their existing (Alpaca / simulated) adapter unchanged.
- [ ] Source the `feed="yahoo"` stamp from the **adapter** (single owner) when storing a Yahoo fetch — not from `config.historical_feed` (`config.py:269`, still `"sip"` and unchanged) and never a route- or client-hardcoded literal. Store the series through the canonical `BarStore.record(...)` (`research/bars.py:220`): append-only, double-sha256 content checksum, `409`-style `BarSeriesAlreadyRegistered` on duplicate content.
- [ ] Pin `yfinance==<version>` in `apps/backend/requirements.txt` with the existing confined-to-adapter comment convention (mirror the `alpaca-py` / `mcp` comment block: "Confined to app/providers/adapters/yahoo.py"). Developer selects a current stable release cleared through the supply-chain install gate.
- [ ] Add `"yfinance"` to the `python.allowlist` array in `config/install-security-policy.json`.

### Frontend (if applicable)
- [ ] **No new UI this iteration.** J-01's capability is REST/MCP-only; the `/structure` fetch control + provenance badge are J-05. The browser lane's job this iteration is a **regression spot-check** of existing surfaces (see TESTING REQUIREMENTS) — not new UI.

### New user-facing capability
Backend/operator capability only: an operator (or agent) can POST a Yahoo bar fetch for a symbol/daily window with no credentials and read the stored `feed="yahoo"` series back through the existing REST + MCP read surface. No new on-screen control yet (that is J-05).

### New information displayed
None on-screen this iteration. The `feed="yahoo"` value becomes a real, readable field on `GET /research/bars*` and via the MCP `bars` proxy (its human-readable "Yahoo Finance" badge label is J-05).

### New user actions
None in the UI this iteration (the explicit `/structure` "Fetch from Yahoo Finance" button is J-05).

### UI surface changes
None. Existing surfaces (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`, `/structure`) stay intact and must be spot-checked as unbroken.

### Product surface delta
The app gains a keyless, default bar-fetch vendor under the hood: Yahoo becomes the default vendor for the bar-fetch path while the Alpaca credentialed path stays byte-identical and opt-in. Visible product change to the operator arrives in J-04/J-05; this iteration lands the honest data path beneath it.

### Blueprint conformance
No new surfaces and **no nav-skeleton change** — the nav is unchanged (data-driven from `GET /meta/ui-routes`). J-01 lives under the **Structure** section's data path per the blueprint's Feature/journey-homes table (row J-01: `/structure` fetch → `GET /research/bars` (+`/{id}`), MCP `bars`), though no `/structure` UI element is added this iteration.

### Data-contract additions
**None requiring a blueprint edit.** The `feed="yahoo"` value this iteration makes real is **already registered** in `blueprint.md`'s Data Contract (row 1: owned by the canonical `BarStore` stamped from the Yahoo adapter — the adapter is the sole source of the `feed` stamp — served via `GET /research/bars*`). This iteration introduces no second computation or second endpoint for it and no other new displayed value, so no additive Data-Contract row is needed. The "Yahoo Finance" human label (Data-Contract row 2) is deferred to J-05.

## OUT OF SCOPE

- The multi-timeframe set (`1w 1d 4h 1h 5m 1m`) and the deterministic `4h` resampler — **J-02**. This iteration validates the adapter on a **daily** window only; the full interval mapping + retention/unsupported-timeframe error taxonomy is J-02.
- The derived SQLite index (`research/bar_index.py`), the store-first coordinator, and the additive `symbol`/`timeframe` filter on `GET /research/bars` — **J-03**. (`GET /research/bars` and `/{id}` are read back **unchanged** this iteration.)
- Computing or rendering S/R levels + A/B/C zones on Yahoo bars; no change to `research/levels.py` — **J-04**.
- The `/structure` fetch control UI, the provenance badge, and the `"yahoo" → "Yahoo Finance"` entry in `taxonomy.FEED_BASIS_LABELS` — **J-05**.
- Any change to `config.py` / `config_fingerprint` (stays `4d665603569b9dbf`), `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the tape engine, the JSON `BarStore` internals, or the Alpaca adapter (frozen foundation).
- Any champion move, strategy mutation, or profile change.

## DEFINITION OF DONE

- [ ] **J-01 passes** its acceptance, verified deterministically (keyless, no network in the default suite): with no credentials, a Yahoo **daily** fetch stores a series stamped `feed="yahoo"` through `BarStore` (append-only, checksum-verified); `GET /research/bars/{id}` and the MCP `bars` proxy return it **byte-for-byte**; a duplicate-content fetch is refused with the `409`-style `BarSeriesAlreadyRegistered`; an unservable symbol/window returns a **clean neutral error** (never empty-but-present, never fabricated bars). Verified via a `FakeAdapter`-injected route test (`dependency_overrides`) plus a committed Yahoo fixture under `apps/backend/tests/fixtures/bars/`.
- [ ] The live Yahoo daily fetch is exercised under the `integration` marker (`TAPEOLOGY_LIVE_INTEGRATION=1`), and the dev handoff explicitly states whether the live fetch succeeded or failed (per `.claude/core.md` External Integration Testing).
- [ ] `feed="yahoo"` has **exactly one owner** (the Yahoo adapter); grep/coherence confirms no route- or client-hardcoded `feed` literal was introduced. Coherence audit runs and clears (single source of truth; no second bar store).
- [ ] `yfinance==<version>` is pinned in `requirements.txt` (confined-to-adapter comment) and present in the `python.allowlist` of `config/install-security-policy.json`; the supply-chain install gate passed.
- [ ] Yahoo is the default vendor on the **bar-fetch** path; Alpaca stays selectable (opt-in); `get_adapter()` (live/tick/live/search/clock) is unchanged; the Alpaca adapter + its credentialed bar/tick/live paths stay byte-identical.
- [ ] **J-06 remains green:** the full backend suite passes, the engine equivalence test proves byte-identical `default` output, `config_fingerprint` stays `4d665603569b9dbf`, and the JSON `BarStore` + Alpaca path stay byte-identical.
- [ ] **Browser-qa lane RUNS and emits evidence** (`ui-test-results.md` + screenshots): existing surfaces render unbroken after the vendor-selector/backend change — J-06 foundation spot-check, closing the iter-0 no-evidence gap.
- [ ] No anti-goal violation introduced (verified against the reminders above).
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-06 regression spot-check — must run and emit `ui-test-results.md` + screenshots):** confirm the existing surfaces still render and are unbroken by the vendor-selector/backend change — at minimum the Cockpit `/` (the live path that uses `get_adapter()`, most at risk if the wrong accessor were flipped) and Structure `/structure`. This is a render/no-regression check for J-06, not a J-01 test (J-01 has no UI).
- **Unit/integration (J-01):**
  - `yahoo.py`: asserts `name == "yahoo"`, keyless `is_available() is True`, the neutral→`yfinance` interval mapping for the daily timeframe, `volume` coerced to `int`, and that tick/live/search honestly raise or return empty.
  - Route/store test via `FakeAdapter` injected through `dependency_overrides`: a keyless fetch stores through `BarStore` with `feed="yahoo"`, and `GET /research/bars/{id}` + the MCP `bars` proxy return the stored series byte-for-byte.
  - A **committed Yahoo fixture** (`tests/fixtures/bars/`) proves the store/read path with **no network** in the default suite.
  - The `feed` stamp originates from the adapter (assert it is `"yahoo"`, sourced from the adapter and not `config.historical_feed`/`"sip"` and not a hardcoded route literal).
  - Vendor-selector test: the bar-fetch path resolves to Yahoo by default; Alpaca remains selectable (opt-in); `get_adapter()` (live/tick/search) resolution is unchanged.
  - Live fetch: an `integration`-marked test (gated on `TAPEOLOGY_LIVE_INTEGRATION=1`, `pytestmark = pytest.mark.integration`) performs a real keyless Yahoo daily fetch.
- **Error cases:** duplicate-content fetch → `409`-style `BarSeriesAlreadyRegistered`; a genuinely unservable symbol/window → a clean neutral error object (not empty-but-present, not fabricated/padded bars). (Out-of-retention and unsupported-timeframe taxonomy is J-02, out of scope here.)

## NOTES

- **Crux risk — accessor discipline.** `get_adapter()` (`main.py:129`) is the neutral accessor the general/live API uses (cockpit, tick, live, search, clock); `get_study_market_adapter()` (`research/routes.py:1220`, called at 1317/1463/1568) is the bar-fetch/study path. Yahoo is bars-only. The Yahoo default MUST land on the fetch path only. Flipping the global `get_adapter()` to a bars-only Yahoo default would break live/tick/search and regress J-06 — this is the single most likely regression and the reason for `full` depth and the browser spot-check.
- **`feed` single-owner subtlety.** The historical/Alpaca replay path currently sources `feed` from `config.historical_feed="sip"` (`config.py:269`, threaded via `research/feed_basis.py` and `research/routes.py:~1296–1329`). For a Yahoo fetch the `feed` must come from the **adapter**, additively — do not mutate the `config.historical_feed` default and do not add a parallel hardcoded `"yahoo"` literal in the route or client. This is the coherence-audited single-source-of-truth surface for the era's one new owned value.
- **Process requirements carried from the iter-0 evaluator (both must be satisfied this iteration):** (1) the browser-qa lane must actually run and emit evidence — it was skipped in the lean baseline; (2) the coherence audit must run and produce `coherence.md` clearing the new `feed="yahoo"` owned value (no second bar store, no second `feed` source).
- **Regression set rationale.** J-06 is the only currently-green journey and is itself the composite foundation sentinel (full backend suite + engine equivalence + `config_fingerprint` + all era-1–4 surfaces), so it functions as the full smoke set; J-02–J-05 are `failing` and carry no passing state to regress.
- **References:** iter-0 eval `runs/goal-session-yahoo_fetch/iter-0/eval.md`; blueprint `runs/goal-session-yahoo_fetch/state/blueprint.md` (Data-Contract row 1 already registers `feed="yahoo"`); goal `docs/goal.md` (J-01, Key Capability 1, Product Shape Data Contract).
