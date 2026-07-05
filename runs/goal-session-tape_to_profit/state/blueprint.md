# App Blueprint — tape_to_profit

> **Tapeology — profit-research era (era 3).** Drafted at baseline (iter-0) from
> `docs/goal.md` (Product Shape, Key Capabilities 1–9, journeys J-01–J-08).
> The archived eras' approved contract — Data Contract rows 1–29 in
> `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` — remains
> **in force, unchanged** (foundation invariant 13). This blueprint registers the era-3
> additions (rows 30–37) and one nav change. (Rows 30–36 and the nav change were registered
> at baseline; row 37 + the J-09 machine-surface home were added additively at iter-8, when the
> human-authored J-09 entered `docs/goal.md` — no nav-skeleton change, purely additive.)
>
> **Governing principles:** every value computed once and read verbatim by REST / WS / UI /
> markdown reports / MCP; the `default` profile is frozen (byte-equivalence-tested) and the
> live cockpit uses it exclusively; train and hold-out data are never pooled; promotion only
> on hold-out survival (net R AND net $, n ≥ configured minimum); no broker / order /
> execution code anywhere; every $ figure appears beside its R figure, its n, and the
> "simulated — assumed fees/slippage — not indicative of live results" register; the MCP
> server is a read-only thin HTTP proxy over the canonical REST API — byte-identical JSON,
> never a second computation or serialization path.

## Information Architecture

**Layout shell:** unchanged dark instrument-panel with persistent top bar. The nav gains
exactly ONE new entry this era: **Cockpit · Journal · Studies · Performance**. The rendered
nav reads `GET /meta/ui-routes` (row 35) once J-01 lands — the hardcoded list in
`apps/frontend/components/NavBar.tsx` is replaced by that single source, never duplicated.
The **Performance** entry ships together with the `/performance` page (J-05) so the skeleton
never carries a dead link; until then `/meta/ui-routes` honestly lists only the live routes.

```
Tapeology (top bar: Cockpit · Journal · Studies · Performance)
├── Cockpit  /                        — live tape cockpit (archived eras; UNCHANGED; default profile only)
├── Journal  /journal (+ /journal/[id]) — thesis journal + review detail (archived; UNCHANGED)
├── Studies  /studies                 — replay studies (archived; UNCHANGED)
└── Performance  /performance         — NEW: PnL-ledger table + current champion (strategy +
                                        profile), rendered verbatim from canonical endpoints
```

**Machine surface** (no nav home — read-only, spawned on demand):
- `python -m app.mcp` (stdio) — MCP tools proxying the canonical REST API over HTTP
  (`TAPEOLOGY_API_BASE`); registered via `project-extensions/mcp-servers.yaml`
- `python -m app.research.pnl_scan --out <path>` — candidate sweep CLI
- `python -m app.research.edge_report --out <path>` — baseline-edge report (J-09): ranks the
  frozen champion's hold-out simulated edge per registered dataset; a pure render of stored
  row-31 backtest aggregates — strictly read-only (promotes / appends / moves NOTHING)
- `reports/pnl/pnl-history.md` — pure render of the stored PnL-ledger rows

**Feature / journey homes** (≤2 clicks from nav where UI-facing):

| Feature / journey | Canonical home | Nav section |
|---|---|---|
| J-01 MCP server + UI route map | machine surface; nav renders `GET /meta/ui-routes` | (nav itself) |
| J-02 dataset store, train/hold-out registry | API `/research/datasets*` + MCP `datasets` | machine |
| J-03 strategy grammar + backtest engine | API `/research/backtests*` + MCP `backtests` | machine |
| J-04 PnL ledger (append-only) | API `/research/pnl/ledger` + `reports/pnl/pnl-history.md` + MCP `pnl_ledger` | machine |
| J-05 performance page | `/performance` | Performance |
| J-06 indicator profiles (frozen default) | API `/research/profiles` (MCP via `get_endpoint`) | machine |
| J-07 candidate sweep (hold-out gate) | CLI `python -m app.research.pnl_scan` → scan report + ledger | machine |
| J-08 regression sentinel | `/`, `/journal`, `/studies` unchanged + full backend suite | Cockpit/Journal/Studies |
| J-09 champion edge across a diverse library | CLI `python -m app.research.edge_report` → ranked baseline-edge report over stored champion backtests | machine |

No watchlist, no multi-symbol view, no order/execution affordance anywhere — unchanged.

## Data Contract

Rows 1–29 (engine snapshot, tape state/features/history, thesis/journal/analytics/studies,
taxonomy, stamps…) are **in force as approved** in the prior-session blueprint — owners and
endpoints unchanged; the live cockpit keeps reading them under the `default` profile only.
Era-3 additions:

| # | Value / entity | Computed by (single owner) | Served by (single endpoint) | Notes |
|---|---|---|---|---|
| 30 | **Dataset records** (symbol, UTC window, feed, event counts, checksum, immutable `train \| holdout` split tag) | dataset store module (single writer; checksum computed at registration, verified on every load) | `POST /research/datasets` (record/register), `GET /research/datasets`, `GET /research/datasets/{id}` | files under gitignored `TAPEOLOGY_DATASET_DIR` + committed miniature train/hold-out CI fixture pair; split tag frozen at registration (re-tag → 409); live/sim watching writes NO dataset rows |
| 31 | **Backtest reports** (per-trade list; net/gross R AND $; win rate; max drawdown (R); n; seeded random-entry null baseline; provenance: dataset id + checksum, strategy config, profile id, `config_fingerprint`) | backtest runner (deterministic, seeded, cancellable job — computed once, persisted) | `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}` (+ cancel, mirroring studies) | `/performance`, markdown, MCP read stored rows verbatim; identical re-runs byte-identical; simulated-fills register mandatory |
| 32 | **PnL-ledger rows** (enhancement id + title; baseline-vs-candidate net R AND net $ on train AND hold-out separately; n per split; provenance; timestamp) | appended ONCE at validation time by the validation/sweep path — append-only, no update/delete anywhere | `GET /research/pnl/ledger` | `/performance`, `reports/pnl/pnl-history.md` (pure render; unchanged rows ⇒ byte-level no-op regen), and MCP `pnl_ledger` show identical numbers; under-min-n splits labeled "insufficient sample" |
| 33 | **Indicator profiles + champion pointer** (`default` frozen + additive-only candidates; current champion strategy+profile) | config-owned profile registry; profile id folds into `config_fingerprint` | `GET /research/profiles` | live cockpit locked to `default` (no UI path selects a candidate); `default` guarded by byte-equivalence test vs pinned outputs; only hold-out survivors move the champion pointer. **J-07 makes the current-champion value a single persisted pointer (journal SQLite, single writer) defaulting to the founding `v1/default`, read ONLY via `GET /research/profiles` (retiring the hardcoded `profiles.py` constant) and moved ONLY by a hold-out-survivor promotion — the profile registry and the `default` freeze are unchanged.** |
| 34 | **Strategy definition v1** (entries from existing setup/state arming rules; exits: invalidation R-stop, horizon, state-flip; fee + slippage model; $-per-R notional) | config-owned strategy grammar (no ML, no runtime mutation) | read by the backtest runner; echoed verbatim in every report's provenance | all thresholds/fees/minimums from config — no magic numbers |
| 35 | **UI route map** (the list of user-facing routes) | route-map owner module behind `GET /meta/ui-routes` | `GET /meta/ui-routes` | rendered nav AND MCP `ui_route_map` read it; the hand-maintained `NavBar.tsx` list is retired at J-01; lists exactly the live routes at all times |
| 36 | **Scan reports** (per candidate: train + hold-out net R/$ deltas, n per split, per-dataset breakdown, `survivor`, `robustness: robust \| speculative`, overfit labels) | `app.research.pnl_scan` — computed once per run, written to the `--out` path (promotion additionally appends row 32 + moves the row-33 champion pointer) | scan report file (machine-readable) | deterministic under fixed seeds; zero candidates / zero survivors = honest report, exit 0; never modifies `default` or any engine default |
| 37 | **Baseline-edge report** (per registered dataset: the CURRENT champion's `v1/default` net R AND $ AND n, its seeded null baseline; datasets ranked by hold-out edge; each flagged positive-edge ONLY when hold-out net R > 0 AND net $ > 0 AND n ≥ the configured minimum AND it beats its own null baseline; explicit "no positive-edge dataset" when none qualify) | `app.research.edge_report` — computed ONCE per run from the row-31 `aggregates` read VERBATIM (never a second R/$/edge computation; reuses the ONE `BacktestJobManager` runner exactly as `pnl_scan`/`pnl_baseline` do) | `--out` report file (machine-readable) | **strictly read-only: promotes / appends to the PnL ledger / moves the champion pointer NOTHING** (the only writes are the standard row-31 backtest rows the existing runner persists + the `--out` file); train and hold-out never pooled; every $ beside its R, its n, its null baseline, and the ONE `REGISTER` string; deterministic under fixed seeds — identical re-runs byte-identical (per-run-random report ids / wall-clock stripped, `pnl_scan` precedent); honest empty finding at exit 0; missing Alpaca credentials surface the EXISTING explicit unavailable state (503), never synthesized data; `default` engine stays byte-identical (equivalence-tested) |

**Persistence (scoped, unchanged discipline).** Backtests + PnL ledger live in the
journal-scoped SQLite (`TAPEOLOGY_JOURNAL_DB`) via the existing single writer queue and
versioned-migration rules (proven against a committed old-schema fixture). Datasets live
under `TAPEOLOGY_DATASET_DIR` (gitignored; committed CI fixture pair excepted). The live
cockpit's tape is never persisted — recording is an explicit research action.

**MCP tool set** (capability 6 — proxies, not owners): `tape_state`, `tape_features`,
`tape_history`, `journal`, `analytics`, `studies`, `datasets`, `backtests`, `pnl_ledger`,
`taxonomy`, `ui_route_map`, `get_endpoint` (GET-only, allowlisted to `/tape/*`,
`/research/*`, `/meta/*`). Every tool's JSON byte-identical to its REST endpoint; backend
down ⇒ explicit tool error, never cached/fabricated data. (J-09 adds NO MCP tool — its edge
report is a machine-surface CLI artifact, not a REST endpoint; MCP stays zero-diff.)
