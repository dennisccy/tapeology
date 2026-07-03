# Tapeology — Project Goal (Era 3: the profit-research evolution)

> Eras 1–2 (tape reading + the research evolution, journeys J-01 – J-68, GOAL_ACHIEVED across
> three goal-mode sessions) are archived at [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md).
> Everything they shipped is the **foundation** of this goal and MUST NOT regress.

## Vision

Tapeology already reads the tape: one US-stock ticker in, live order flow watched, and the
current tape state classified into one of five states — `buyer_control`, `seller_control`,
`bid_absorption`, `ask_absorption`, `unclear` — on the defining principle of **price impact,
not raw aggression**. On top of that read sits a decision-support research layer: declared
theses, tape-confirmation verdicts, an append-only journal, and replay studies with null
baselines. Data comes from a deterministic seedable simulator (default, keyless) or from real
US-equity vendors behind a provider-agnostic seam (Alpaca today: SIP historical, IEX live).

The **profit-research era** answers the question the first two eras deliberately refused to
ask: **does the tape read convert to simulated profit — and does each enhancement to the read
improve it?**

To answer it honestly, the product gains:

- **Persisted historical tape datasets** — recorded trade/quote streams that replay
  byte-identically, split into **frozen train and hold-out sets**, so every measurement is
  reproducible and nothing is ever judged on the data it was tuned on.
- **A config-owned strategy grammar and a deterministic backtest engine** — simulated entries
  and exits driven by the existing tape states and indicators, producing PnL in **R-multiples
  AND dollars**, gross and net of an explicit fee/slippage model, always beside a seeded
  random-entry null baseline.
- **Versioned indicator profiles** — candidate indicator adjustments and additions live beside
  the frozen `default` profile; the live cockpit never changes, and only the backtest layer may
  opt into candidates.
- **A read-only MCP server** — the whole product becomes machine-readable for the AI dev-chain
  (the goal-mode MCP loop): every MCP tool is a thin proxy over the same canonical REST API a
  human uses.
- **An autonomous enhancement loop** — after every must-have journey passes, a proposer surveys
  the product, screens candidate improvements against the hold-out data, promotes only
  **hold-out survivors** as new journeys, and every promoted enhancement appends **one honest
  row to the PnL ledger** so the operator can watch the PnL improve (or honestly not improve)
  enhancement by enhancement.

Absolutes, unchanged from day one: **no broker, no order placement (real or paper), no ML, no
advice**. Every PnL figure is a measurement of the past under disclosed assumptions — never a
forecast, never a promise.

## Target Users

- The discretionary intraday trader (the project owner) using the tape read to support
  decisions — now also as a **systematic researcher** measuring whether that read carries
  simulated edge and which refinements improve it.
- AI dev-chain agents (the goal-mode loop) surveying the product through its read-only MCP
  tools and judging every enhancement by its hold-out simulated-PnL delta.

## Foundation invariants (imported from the archived constitution — still law)

The archived goal's critical rules remain binding on ALL new code:

1. **Price impact over raw aggression** — high one-sided aggression with no price progress is
   absorption, never control.
2. **Honest uncertainty** — weak/mixed evidence reads `unclear`; spread and impact are judged
   relative to price, feed-aware and halt-aware; never manufacture a directional call.
3. **No fabricated data** — every failure mode surfaces an explicit state (`stale`, error,
   no-data, closed, unavailable); nothing is synthesized to force a green journey.
4. **Single source of truth** — every value is computed exactly once and read identically by
   REST, WebSocket, UI, MCP, and reports; nothing downstream recomputes it.
5. **No magic numbers** — every threshold, window, fee, slippage, minimum-n, and cutoff comes
   from config.
6. **Provider-agnostic engine** — vendor SDKs live in one adapter behind the neutral seam.
7. **Deterministic & reproducible** — same inputs, same seeds, same outputs, byte-identical.
8. **No secrets in source** — keys only from environment; keyless runs are simulator-only with
   explicit "unavailable" real modes.
9. **Research stays read-only over the engine** — observers never mutate engine outputs
   (byte-identical equivalence, exception-isolated).
10. **Journal integrity** — research records are append-only, never backfilled, never inferred.
11. **Source, feed, and config honesty** — every record stamps its source, `data_feed`, and
    `config_fingerprint`; nothing pools across feeds or fingerprints.
12. **Dates are dd-MM-yyyy everywhere**; times in the user's local timezone with US-session
    quick-picks.
13. **The existing surfaces stay intact** — cockpit `/`, `/journal`, `/journal/[id]`,
    `/studies` keep working exactly as shipped.

## Success Criteria

In priority order — honesty and non-regression outrank any profit number:

1. **Nothing existing regresses.** The full backend suite stays green, the engine equivalence
   test keeps proving byte-identical default outputs, and the archived-era surfaces keep
   working (J-08).
2. **Datasets are trustworthy.** A recorded dataset replays byte-identically to its source
   stream, re-runs are identical, checksums verify, and train/hold-out tags are frozen at
   registration.
3. **Backtests are deterministic and honest.** PnL is reported in R AND $, gross and net of
   the configured fee/slippage model, with trade count n, beside a seeded random-entry null
   baseline, stamped with full provenance (dataset id + checksum, strategy config, profile id,
   `config_fingerprint`).
4. **Nothing is promoted on train performance alone.** A candidate becomes the champion only
   by beating the incumbent on the frozen hold-out set with at least the configured minimum
   trade count; train-only winners are labeled overfit and rejected.
5. **The default read is frozen.** Indicator evolution is additive and versioned; the live
   cockpit and every archived-era journey run on the byte-identical `default` profile.
6. **Every enhancement reports its PnL delta.** One append-only PnL-ledger row per
   enhancement (baseline vs candidate, train AND hold-out, R and $), surfaced at
   `/performance`, in `reports/pnl/pnl-history.md`, and over REST/MCP.
7. **The product is machine-readable.** Every MCP tool returns byte-identical JSON to its
   canonical REST endpoint; everything an agent can do over MCP has a curl-equivalent.

## Key Capabilities

Layered strictly on top of the archived eras' capabilities 1–34, which remain unchanged.

1. **Historical tape dataset store.** Recorded trade/quote event streams per
   symbol + window + feed, stored under `TAPEOLOGY_DATASET_DIR` (default
   `apps/backend/.data/datasets/`, gitignored), each with metadata (symbol, UTC window, feed,
   event counts, checksum) and an immutable `train | holdout` split tag assigned at
   registration. A committed miniature train + hold-out fixture pair proves the whole pipeline
   keyless in CI. The live cockpit's tape is never persisted — recording is an explicit
   research action.
2. **Versioned indicator profiles.** Named engine-feature/classifier configurations. `default`
   is the frozen legacy configuration, guarded by a byte-equivalence test against pinned
   outputs. Candidate profiles may only add new feature keys or alternate threshold values;
   they are selectable solely by backtest/study runs (never by the live cockpit) and the
   profile id folds into `config_fingerprint`.
3. **Strategy grammar v1.** Config-owned, human-readable rules: entries armed by the existing
   setup/tape-state rules (setup type × direction), exits by invalidation R-stop, time horizon,
   or state-flip; an explicit fee model (per-share + minimum) and slippage model (spread
   fraction); a fixed $-per-R notional for dollar conversion. No ML anywhere.
4. **Deterministic backtest engine.** Replays a dataset unpaced through a fresh engine (the
   existing replay-study runner pattern), simulates fills at recorded prices adjusted by the
   slippage model, and produces a persisted report: per-trade list and aggregates — net/gross
   R and $, win rate, max drawdown (R), n — beside a seeded random-entry null baseline on the
   same dataset. Runs as a cancellable job like studies.
5. **The PnL ledger.** An append-only SQLite table (journal DB) + `GET /research/pnl/ledger` +
   a pure-rendered `reports/pnl/pnl-history.md`. One row per enhancement: enhancement id and
   title, baseline vs candidate net R and net $ on train AND hold-out, n per split, full
   provenance, timestamp. No update or delete paths exist.
6. **Read-only MCP server.** `python -m app.mcp` (stdio), spawned on demand by the AI CLI.
   Tools are thin HTTP clients against the running backend (`TAPEOLOGY_API_BASE`, default
   `http://localhost:8000`) — never a second app instance, never direct engine imports:
   `tape_state`, `tape_features`, `tape_history`, `journal`, `analytics`, `studies`,
   `datasets`, `backtests`, `pnl_ledger`, `taxonomy`, `ui_route_map`, plus a generic
   `get_endpoint(path)` allowlisted to GET `/tape/*`, `/research/*`, `/meta/*`. Backend down →
   explicit tool error. Registered for the dev-chain via `project-extensions/mcp-servers.yaml`.
7. **Candidate sweep harness.** `python -m app.research.pnl_scan --out <path>` evaluates every
   registered candidate (profile or strategy variant) against the champion over all train
   datasets, validates survivors on the hold-out set, appends promotions to the PnL ledger,
   and writes a machine-readable scan report. Zero candidates or zero survivors is an honest,
   exit-0 outcome.
8. **The `/performance` page.** A fourth top-level page rendering the PnL ledger and the
   current champion (strategy + profile) verbatim from the canonical endpoints, in the
   existing dark cockpit design language.
9. **A canonical UI route map.** `GET /meta/ui-routes` owns the list of user-facing routes;
   the rendered navigation and the MCP `ui_route_map` tool read it, never a hand-maintained
   duplicate.

## Non-Goals

- No brokerage integration, order placement, routing, or execution of any kind — **neither
  real-money nor paper-trading APIs**. Simulated fills exist only inside the offline
  backtester, computed against recorded historical tape and sent nowhere.
- No machine learning, no online/in-engine tuning, no fitted thresholds — candidate search is
  bounded, config-enumerated, offline, and hold-out-validated.
- No trading advice, no imperative cues ("buy", "sell", "enter now"), no prediction language,
  no expected-return claims. Simulated PnL describes the past under stated assumptions.
- No account, capital, portfolio, or position management; no compounding equity projections.
- No stock scanning/screening, multi-symbol dashboards, news/sentiment, fundamentals, or
  general-purpose charting — unchanged from the archived eras.
- No auto-modification of the `default` profile or any live-cockpit behavior by the
  enhancement loop.

## Constraints

- **Stack (carried over):** Backend Python 3.12 + FastAPI (uvicorn, REST + WebSocket), tests
  via pytest (venv at `apps/backend/.venv/`, package manager `uv`). Frontend Next.js 15 App
  Router + TypeScript + Tailwind v3 (npm), charts via `lightweight-charts`. Research
  persistence in the journal-scoped SQLite (`TAPEOLOGY_JOURNAL_DB`). Backend
  `http://localhost:8000`, frontend `http://localhost:3000`. Reserved sim tickers
  (`SIM-BUYER`, `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`) still work keyless.
- **Dataset discipline:** datasets live under `TAPEOLOGY_DATASET_DIR` (gitignored except the
  committed CI fixture pair), are immutable once registered (content checksum verified on
  load), stamp their feed, and carry a split tag that can never be changed afterwards.
- **Profile discipline:** the `default` profile is frozen and equivalence-tested; candidates
  are additive-only; every artifact touching a non-default profile is stamped with the profile
  id; profile id is part of `config_fingerprint`.
- **Backtest determinism:** seeded, unpaced, single-threaded per run; identical inputs and
  seeds reproduce byte-identical reports; the null baseline uses a seeded RNG recorded in the
  report.
- **PnL honesty register:** a dollar figure never appears without its R figure, its n, and the
  visible register "simulated — assumed fees/slippage — not indicative of live results";
  results with n below the configured minimum are labeled "insufficient sample"; train and
  hold-out numbers are never pooled or averaged together.
- **MCP read-only discipline:** the MCP server exposes no mutating tools, proxies the
  canonical REST API over HTTP, adds no second computation path, and fails explicitly when the
  backend is unreachable.
- **Design direction:** the `/performance` page follows the existing dark tape-cockpit design
  tokens; density and honesty over decoration.

### Glossary (new terms; archived glossary still applies)

- **Dataset** — an immutable recorded trade/quote event stream (symbol + window + feed) with
  checksum and split tag.
- **Train / hold-out** — the two frozen dataset splits; tuning may only ever see train;
  promotion is decided only on hold-out.
- **Profile** — a named, versioned engine indicator/classifier configuration; `default` is the
  frozen legacy one.
- **Strategy** — a config-owned rule set mapping tape states/features to simulated entries and
  exits.
- **Backtest** — a deterministic replay of one dataset under one strategy + profile, producing
  a PnL report beside a null baseline.
- **PnL ledger** — the append-only record of per-enhancement baseline-vs-candidate PnL deltas.
- **Champion** — the currently promoted strategy + profile pair; only a hold-out survivor may
  replace it.

## Product Shape

Nav (top bar): **Cockpit `/` · Journal `/journal` (+ `/journal/[id]`) · Studies `/studies` ·
Performance `/performance`** — the first three exactly as shipped in the archived eras.

**API surface.** The archived canonical endpoints are unchanged: `/health`,
`POST/DELETE /watch/{ticker}` (+ `/pause`, `/resume`, `/speed`), `/symbols/search`,
`/market/clock`, `GET /tape/{ticker}/state|features|events|summary|history`,
`WS /tape/{ticker}/stream`, and `/research/*` (taxonomy, analytics, thesis, hints, journal,
studies). The profit-research era adds, every projection computed once server-side:

- `POST /research/datasets` (record/register) · `GET /research/datasets` · `GET /research/datasets/{id}`
- `POST /research/backtests` · `GET /research/backtests` · `GET /research/backtests/{id}` (+ cancel, mirroring studies)
- `GET /research/pnl/ledger`
- `GET /research/profiles`
- `GET /meta/ui-routes`

MCP tools are thin proxies over exactly these — no new computation, no divergent serialization.

**Data Contract (canonical values — each computed once, owned by one place):**

- Tape state, confidence, features, history — computed in the engine (unchanged owner).
- Dataset records and checksums — owned by the dataset store; served only via
  `/research/datasets*`.
- Backtest results (trades, R/$ aggregates, null baseline) — computed once by the backtest
  runner and persisted; `/performance`, reports, and MCP read the stored rows verbatim.
- PnL-ledger rows — appended once at validation time; every surface (REST, page, markdown,
  MCP) renders the same stored rows.
- Indicator profiles and the champion pointer — config-owned; served via `/research/profiles`.
- The UI route map — owned by `/meta/ui-routes`; the nav renders it, never a second list.

## Must-have user journeys

Journeys **J-01 – J-08** are the profit-research era. Each is sized for one lean iteration.
All are verifiable **keyless** via the simulator and the committed fixture dataset pair;
real-scale datasets are an operator action requiring Alpaca credentials and only enlarge the
data — they change no behavior. Natural dependency order: J-02 → J-03 → J-04 → J-05 and
J-06 → J-07; J-01 is independent; J-08 guards continuously. The foundation (archived
J-01 – J-68 behavior) MUST NOT regress.

- **J-01: A read-only MCP server exposes the product over the canonical API**
  - Steps:
    1. With the backend running, start a stdio MCP client session against `python -m app.mcp`
       (as the AI CLI would) and list the tools
    2. Watch `SIM-BUYER`, then call `tape_state`, `tape_features`, and `ui_route_map`
    3. `curl` the corresponding REST endpoints and diff the payloads
    4. Fill the real server entry into `project-extensions/mcp-servers.yaml`, run
       `./scripts/automation/sync-cli-assets.sh`, then
       `python3 scripts/automation/lib/mcp_sync_selftest.py self-test`
    5. Stop the backend and call any tool again
  - Acceptance: the advertised tool set matches capability 6 and every tool's JSON is
    **byte-identical** to its canonical REST endpoint (an automated test asserts this per
    tool); no tool mutates anything (tool list contains no write verbs; server code performs
    only GETs); `get_endpoint` refuses paths outside `/tape/*`, `/research/*`, `/meta/*`;
    with the backend down every tool returns an explicit error, never cached or fabricated
    data; the MCP sync self-test passes, `.mcp.json` is generated at the repo root **and**
    is gitignored; `GET /meta/ui-routes` lists exactly the live routes and the rendered
    top-bar links match it (browser-verified). *(Keyless; automated + browser-verifiable.)*
    [NEW] walkthrough: one MCP tool call narrated beside its curl equivalent.

- **J-02: Historical tape datasets persist and replay byte-identically (train/hold-out registry)**
  - Steps:
    1. Record a dataset from a historical fetch (the committed fixture window works keyless)
       via `POST /research/datasets`
    2. Register its split tag (`train` or `holdout`), then attempt to re-tag it
    3. Replay the dataset unpaced through a fresh engine twice; separately replay the original
       source stream
    4. List datasets via REST and the MCP `datasets` tool
  - Acceptance: the dataset stores symbol, UTC window, feed, event counts, and checksum;
    replaying it yields tape snapshots **byte-identical** to replaying the source stream, and
    re-runs are identical; the checksum is verified on load and a corrupted file surfaces an
    explicit error; re-tagging a registered split returns a 409-style refusal; a committed
    miniature train + hold-out fixture pair proves record→register→replay in CI without
    credentials; watching a live or sim ticker writes **no** dataset rows. *(Keyless;
    automated.)*

- **J-03: Strategy grammar v1 backtests a dataset into a deterministic PnL report**
  - Steps:
    1. Read the v1 strategy definition from config (entries from the existing setup/state
       arming rules; exits: invalidation R-stop, horizon, state-flip; fee + slippage model;
       $-per-R notional)
    2. `POST /research/backtests` with dataset id + strategy + profile `default`; poll the job
       to completion
    3. Open the result via `GET /research/backtests/{id}`, the MCP `backtests` tool, and re-run
       the identical request
  - Acceptance: the report lists per-trade entries/exits with simulated fills at recorded
    prices adjusted by the configured slippage model, and aggregates — **net and gross R AND
    $**, win rate, max drawdown (R), n — beside a seeded random-entry null baseline on the
    same dataset; it is stamped with dataset id + checksum, strategy config, profile id, and
    `config_fingerprint`; an identical re-run reproduces a byte-identical report; the rendered
    copy carries "simulated — assumed fees/slippage — not indicative of live results"; no
    broker, order, or account code exists anywhere in the repo (asserted by a grep-style
    test). *(Keyless on the fixture datasets; automated.)*

- **J-04: Every enhancement lands one honest row in the PnL ledger**
  - Steps:
    1. Append the founding baseline row (strategy v1 on profile `default`, evaluated on the
       fixture train AND hold-out datasets) via the validation path
    2. Read `GET /research/pnl/ledger`, the MCP `pnl_ledger` tool, and regenerate
       `reports/pnl/pnl-history.md`
  - Acceptance: a ledger row records enhancement id + title, baseline-vs-candidate net R and
    net $ on train AND hold-out separately, n per split, dataset/profile/fingerprint
    provenance, and timestamp; the store exposes **no update or delete** path (same standard
    as verdict events); the markdown is a pure render of the stored rows (regenerating with
    unchanged rows is a byte-level no-op); REST, markdown, and MCP show identical numbers;
    under-minimum-n splits are labeled "insufficient sample". *(Keyless; automated.)*

- **J-05: The /performance page reports PnL per enhancement honestly**
  - Steps:
    1. Visit `/performance` from the top-bar Performance link with the founding ledger row
       present
    2. Read the ledger table and the champion summary (current strategy + profile)
    3. Check `GET /meta/ui-routes`
  - Acceptance: the page renders `GET /research/pnl/ledger` verbatim (no client-side
    recomputation — a value shown on the page equals the API value exactly); every $ figure
    sits beside its R figure, its n, and the visible "simulated — assumed fees/slippage — not
    indicative of live results" register; train and hold-out columns are separate and never
    pooled; under-minimum-n rows read "insufficient sample"; the nav reads
    Cockpit / Journal / Studies / Performance on every page and `/meta/ui-routes` includes
    `/performance`; the page follows the existing dark cockpit design language.
    *(Keyless; browser-verifiable.)* [NEW] walkthrough: narrate one enhancement's before/after
    hold-out PnL delta.

- **J-06: Indicator profiles are versioned; the default stays byte-identical**
  - Steps:
    1. List profiles via `GET /research/profiles` (and the MCP tool): `default` plus at least
       one registered candidate (a new additive feature key or an alternate threshold set)
    2. Run the same fixture-dataset backtest under `default` and under the candidate
    3. Run the engine equivalence suite and the full backend suite
  - Acceptance: an automated equivalence test replays fixed event streams under `default` and
    asserts **byte-identical** state/confidence/features/history against pinned pre-profile
    outputs; the live cockpit and every archived-era surface use `default` only (no UI path
    selects a candidate); candidate outputs appear only in backtest/study artifacts stamped
    with their profile id; the two backtests differ only where the candidate legitimately
    changes behavior and both remain individually deterministic. *(Keyless; automated.)*

- **J-07: The candidate sweep survives hold-out or says so honestly**
  - Steps:
    1. Run `python -m app.research.pnl_scan --out <path>` with at least one registered
       candidate and the fixture datasets
    2. Read the scan report and the PnL ledger afterwards; re-run the identical scan
  - Acceptance: the scan evaluates every registered candidate against the champion over all
    **train** datasets and validates apparent winners on the **hold-out** set; the report
    records, per candidate: train and hold-out net R/$ deltas, n per split, per-dataset
    breakdown, `survivor` (true iff it beats the champion on hold-out net R AND net $ with
    n ≥ the configured minimum), and `robustness: robust|speculative` (robust iff positive on
    every train dataset individually); train-only winners are explicitly labeled overfit and
    never promoted; a promotion appends a PnL-ledger row and moves the champion pointer
    **without modifying the `default` profile or any engine default**; the scan is
    deterministic under fixed seeds and identical re-runs produce identical reports; zero
    candidates or zero survivors produces an explicit honest report and **exit code 0**.
    *(Keyless; automated.)*

- **J-08: The existing product is unchanged (regression sentinel)**
  - Steps:
    1. With the profit-research layer deployed, run the sim cockpit flows (`SIM-BUYER` settles
       `buyer_control`, `SIM-SELLER` settles `seller_control`) and spot-check `/journal` and
       `/studies` in the browser
    2. Run the full backend suite and the engine equivalence test
  - Acceptance: the archived-era surfaces behave exactly as shipped (cockpit panels populate
    and classify; journal and studies pages render their data); the full backend suite passes
    (848+ tests and growing — no archived-era test is deleted or weakened to make new work
    pass); the equivalence test proves a fixed event stream still yields **byte-identical**
    state/confidence/features/history under the default configuration. The per-journey detail
    lives in the archived goal; this sentinel makes "don't break the foundation" an enforced
    must-have of this era. *(Keyless; browser-verifiable + automated.)*

<!-- AUTO:journeys -->
<!-- /AUTO:journeys -->

## Anti-goals

- **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere —
  no brokerage integration, no trading API, **no paper-trading API**, no order tickets, no
  recommendation to execute. The ONLY permitted "fill" is the offline backtester's simulated
  fill computed against recorded historical tape, clearly labeled simulated and sent nowhere.
  *(critical)*
- **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always
  appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out
  basis, and its null baseline — and MUST never be presented as expected live results, an edge
  claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
- **Default engine outputs are frozen.** Indicator evolution is additive and versioned only:
  candidate profiles may add feature keys or alternate thresholds, but the `default` profile's
  outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, and
  no enhancement may mutate an archived-era behavior to pass. *(critical)*
- **No train-only promotion.** Nothing becomes the champion, a proposed journey, or a claimed
  improvement on the strength of train data alone: hold-out survival (net R AND net $, with
  the configured minimum n) is the only promotion gate; overfit results are labeled overfit.
  *(critical)*
- **No ML, no online tuning.** Candidate search is bounded, config-enumerated, offline, and
  deterministic; no fitted models, no optimizer loops inside the engine, no thresholds that
  move at runtime.
- **No fabricated data — honest failure states.** No synthesized trades, quotes, fills,
  datasets, or PnL to force a green journey; every failure mode (backend down, corrupt
  dataset, empty window, missing credentials, insufficient n) surfaces an explicit, distinct
  state. *(critical)*
- **Single source of truth.** Every canonical value in the Data Contract is computed once and
  read verbatim by every surface — REST, WebSocket, UI, markdown reports, and MCP. A second
  computation path or a diverging number across surfaces is a defect. *(critical)*
- **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical
  GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second
  implementation of any computation. *(critical)*
- **Persistence stays scoped.** SQLite holds research records (now including backtests and the
  PnL ledger); the dataset store holds explicitly recorded historical tape for research
  replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
- **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
  inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this
  Anti-goals section, or any other part of this file; proposed journeys MUST carry a
  PnL-ledger acceptance criterion, keep the default profile byte-identical, and include a
  [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is
  a failure. *(critical)*
