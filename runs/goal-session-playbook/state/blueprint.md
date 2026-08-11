# App Blueprint — playbook

<!--
This is the coherence contract for the whole app. The goal-decomposer drafts it at baseline; you
approve it once (edit anything, then `--resume`); the coherence-auditor enforces it every iteration.

Era B2 ("The Playbook") builds ADDITIVELY on the three-page product left by Era B "The Desk"
(Cockpit `/` + Structure `/structure` + Desk `/desk`, GOAL_ACHIEVED 2026-07-31, 21 journeys,
`config_fingerprint` `08e471b10130e1e2` confirmed live against the current tree, 18 read-only MCP
tools confirmed via `EXPECTED_TOOLS` in `apps/backend/tests/test_mcp_server.py`, plus the R-2
forward-test interlude folded into this era's foundation). The Cockpit/Structure/kept-Desk
inventory is carried forward UNCHANGED and is NOT re-derived here — see
`runs/goal-session-desk/state/blueprint.md` for the exhaustive prior listing (nav skeleton +
every desk-owned Data Contract row through Era B's 21 journeys). This file registers only what
Era B2 adds: three new `/desk` sections and six new desk-owned values, all taken near-verbatim
from `docs/goal.md`'s own `## Product Shape` section plus the J-01..J-10 Must-have journeys.

STATUS AS OF ITERATION 7 (freshened from the iteration-0 baseline below — additive status-label
update only, no IA/Data-Contract change): J-01 (signal contract), J-02 (measurement), J-03
(Playbook Signals section), J-04 (continuation family), J-05 (climax family), J-06 (range family)
are SHIPPED and passing (session `playbook`, iterations 1-6). J-07 (back-scan) is the TARGET of
iteration 7. J-08/J-09 remain not yet built. The six-row Data Contract table below was drafted
whole at iteration 0 as the TARGET shape every journey ships into — it already anticipated J-07
landing on the "Back-scan plan" and "Back-scan progress + ledger" rows, so no Data-Contract
structural edit is needed for iteration 7, only the "Ships at" column below.

BASELINE STATE (iteration 0, kept verbatim for history): none of the six new rows below existed
in the codebase yet — confirmed by grep (no `desk_playbook*.py` module anywhere under
`apps/backend/app/research/`, no `playbook` string in `desk_routes.py` or `app/mcp/__init__.py`,
no `playbook` string in `apps/frontend/app/desk/page.tsx`/`apps/frontend/lib/api.ts`, no
`*playbook*` fixture under `apps/backend/tests/fixtures/`). This file registers them as the
TARGET contract each journey ships INTO, per the era's natural dependency order (J-01 → J-02 →
J-03, then J-04/J-05/J-06, then J-07 → J-08 → J-09, with J-10 guarding continuously).
-->

## Information Architecture

**Layout shell:** unchanged — persistent top nav bar + main content area, dark-only, dense,
terminal-grade. Nav is data-driven from `app/meta.py` `UI_ROUTES` (3 rows, confirmed live) —
never hand-edit `NavBar.tsx`.

**Navigation skeleton** (current state + this-era target):

```
Tapeology
├── Cockpit      /             live/sim/historical tape watch, engine panels, PriceChart —
│                               UNCHANGED this era (full inventory:
│                               runs/goal-session-desk/state/blueprint.md)
├── Structure    /structure    bar library, levels/zones, tradable map, case studies, edge
│                               report, strategy registry — UNCHANGED this era
└── Desk         /desk         every shipped Era-B section (universe + coverage, screen
                                briefing + history calendar, forward returns, refresh chain +
                                compute controls, runs/pins/compare/provenance) — UNCHANGED
                                this era, kept byte-for-byte (R-1/R-2 in inventory). THIS ERA
                                adds three NEW sections rendered BELOW all shipped ones:
                                  • Playbook Signals — per-session signal table + Run Playbook
                                    button + live progress/cancel + provenance line (J-03,
                                    SHIPPED; extended visibly by J-04/J-05/J-06, all SHIPPED)
                                  • Backscan — plan preview (From/To range) + trigger + live
                                    progress + cancel + runs table (J-07, TARGETED iteration 7)
                                  • Playbook Evidence — the per-(setup, side) distribution
                                    table beside the pooled baseline, min-n tags (J-08, not
                                    yet built)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 Signal contract (opening-range detectors, pre-registered, lookahead-clean) — SHIPPED | *(backend module + store; `GET /research/desk/playbook` — no standalone UI until J-03)* | Desk |
| J-02 Trigger-anchored measurement (rail conventions, seeded baseline anchors) — SHIPPED | *(backend extension, same module/endpoint as J-01, plus the compute-manager trio + run ledger)* | Desk |
| J-03 Playbook Signals section — SHIPPED | `/desk` (new section) | Desk |
| J-04 Continuation family (JBE, DBI, cup-and-handle) — SHIPPED | lands on J-03's section, `/desk` | Desk |
| J-05 Climax family (capitulation entry, euphoria marker) — SHIPPED | lands on J-03's section, `/desk` | Desk |
| J-06 Range family (range trades, double top/bottom) — SHIPPED | lands on J-03's section, `/desk` | Desk |
| J-07 Back-scan (resumable, append-only, host-guard-confined) — TARGETED iteration 7 | `/desk` (new Backscan panel) | Desk |
| J-08 Evidence view (distributions beside the null, min-n honest) — not yet built | `/desk` (new Playbook Evidence section) | Desk |
| J-09 MCP contract v4 (20 read-only tools) — not yet built | *(MCP tool surface only; no page — `desk_playbook`/`desk_playbook_evidence` proxy the rows below)* | — |
| J-10 Kept-product regression sentinel — continuous, every iteration (currently `partial`: text asks for 20 MCP tools, 18 exist until J-09) | `/`, `/structure`, `/desk` (every shipped section) | Cockpit, Structure, Desk |

## Data Contract

Every value that appears in the UI and should read the same everywhere is registered here with
**one** canonical computing source and **one** serving endpoint. No page may recompute or
re-fetch these from anywhere else; UI may only re-format what the canonical endpoint returns.

**Unchanged owners (the playbook reads them verbatim — never re-implemented, re-tuned, or served
a second way; per `docs/goal.md`'s Product Shape section):** bars/candles → `bars.py`
(`merged_bars`, `apps/backend/app/research/bars.py:883`) + `bar_index`; session honesty →
`desk_sessions.py` (`recorded_session_dates` :129, `refuse_if_not_a_session` :180); measurement
helpers → `desk_forward.py` (imported, zero diff — `_session_slice` :295, `_draw_anchor_indices`
:428, `_measure_from` :451, `forward_parameters()` :225, `compute_forward_input_signature` :362);
universe membership → `desk_universe.py`; pivot-rule reference → `levels.py` `_swing_pivots`
(:325 — mirrored by the playbook's own pivot primitive, never called directly, since the
playbook's series is the desk's own 5m/1m bars, not `levels.py`'s multi-timeframe input); the
`desk_playbook` walk performs ZERO `compute_tradability`/`compute_levels` calls (J-06's own
guard) — the book's intraday ranges and the desk's structural walls stay different owners.
Everything else (tradability, the levels endpoint itself, datasets, setups, edge_report, the PnL
ledger, the strategy registry, profiles, taxonomy, the route/nav inventory, `config_fingerprint`,
and every shipped `desk_screen*`/`desk_forward*`/`desk_topup*`/`desk_index_reconcile*`/
`desk_meta_cache` row) stays exactly as `runs/goal-session-desk/state/blueprint.md` lists — this
file does not re-derive that inventory.

**New rows this era (six new desk-owned values, exactly one owner each, taken verbatim from
`docs/goal.md`'s Product Shape table; "Ships at" tracks actual delivery, not just the original
target):**

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Ships at |
|---|---|---|---|
| Playbook records (signals + measurements + baseline + summary) | new `app/research/desk_playbook.py` (+ primitives `desk_playbook_features.py` and detectors `desk_playbook_detect.py`) | `GET /research/desk/playbook` (`?date=`, `?id=`) | J-01 (detection-only records, SHIPPED) → J-02 (adds the measurement block, same owner/endpoint, SHIPPED) → J-04/J-05/J-06 (continuation + climax + range families, same owner/endpoint, all SHIPPED) |
| Playbook compute progress | new playbook compute manager, `desk_playbook_compute.py` (single-flight, mirrors `DeskScreenComputeManager`) | `POST/GET/POST-cancel /research/desk/playbook/compute` | J-02 (SHIPPED) |
| Playbook run ledger | new `app/research/desk_playbook_log.py` (terminal-state-only, mirrors `desk_topup_log.py`) | `GET /research/desk/playbook/runs` | J-02 (SHIPPED) |
| Back-scan plan | new `app/research/desk_playbook_backscan.py` (pure, metadata-only) | `GET /research/desk/playbook/backscan/plan` | J-07 (TARGETED iteration 7) |
| Back-scan progress + ledger | same back-scan module (mirrors `desk_deep_backfill.py`'s plan/walker/ledger/manager quartet, re-chunked to one session-date) | `POST/GET/POST-cancel .../backscan/compute`, `GET .../backscan/runs` | J-07 (TARGETED iteration 7) |
| Evidence aggregates | new `app/research/desk_playbook_evidence.py` (stat-keyed derived projection cache, the `desk_meta_cache` contract — rebuildable, owns nothing) | `GET /research/desk/playbook/evidence` | J-08 (not yet built) |

No shared value from the unchanged-owners list above is recomputed a second way by any of these
six rows — each reads bars/sessions/measurement-helpers/universe-membership verbatim from its
single existing owner (the "no second implementation of the measurement rail" anti-goal). J-07's
back-scan rows read the ALREADY-registered "Playbook records" row's own store/signature verbatim,
via the ONE shared `run_playbook_and_record` entry point (`desk_playbook_compute.py:90`) — no new
detection or measurement path, no second store. MCP exposure (`desk_playbook`,
`desk_playbook_evidence`) is a byte-identical GET proxy of the first and last rows above, added at
J-09 — it introduces no new value and no new owner.
