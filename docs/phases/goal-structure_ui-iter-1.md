# Goal Iteration 1 — J-01: the Structure tab renders S/R levels and A/B/C confluence zones

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** structure_ui
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-04
- **Anti-goal reminders:** (verbatim from `docs/goal.md`; all 10 rails + all interlude anti-goals remain binding — those most directly exercised by this iteration are restated here)
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **The Structure UI recomputes nothing.** Every displayed value — level price/timeframe/type, zone class, net R, net $, n, `insufficient_sample`, the champion — is read verbatim from its canonical endpoint. No client-side grading, PnL math, aggregation, or champion resolution. A number that diverges from its API/MCP payload is a defect (trap T10). *(critical)*
  - **No new backend computation or endpoint.** This interlude consumes the existing canonical endpoints; the only backend edit is the additive `/structure` entry in the `meta.py` route registry (the nav owner). It creates no second implementation of any value. *(critical)*
  - **Honest UI states only.** No fabricated chart, level, zone, trade, fill, or PnL to force a green journey; every failure mode (no bar series, no levels, no zones, insufficient n, missing credentials, backend unreachable) surfaces an explicit, distinct state. *(critical)*
  - **No vocabulary drift** (trap T9). No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.

## GOAL

Ship the read-only `/structure` page — reachable from the data-driven nav — that renders, for a chosen symbol and as-of time, a `lightweight-charts` price chart with one price line per support/resistance level and a confluence-zones table badged A/B/C, every value read verbatim from `GET /research/levels`, with three distinct honest empty states.

## BACKGROUND

J-01 is the dependency-order and blueprint unblocker: it lands the single `/structure` page and the additive `meta.py` nav entry that J-02 (registry) and J-03 (comparison) later attach to as sections of the same page. The prior evaluator (iter-0, CONTINUE) recommended targeting **J-01 alone at full depth**. Full is chosen per the depth rubric because this iteration crosses the backend↔frontend boundary (a `meta.py` `UI_ROUTES` edit plus a new Next.js page) and is the first real surface introducing the interlude's central critical anti-goals — single-source-of-truth / "the UI recomputes nothing" (T10) and honest-state discipline — plus a nav-registry edit that touches the data-driven-nav single source of truth; the auditor and coherence lanes that verify "no second source of truth, no client recompute, honest distinct states" run only in the full pipeline, and browser-qa evidence is load-bearing for the first time.

**Lesson carried forward (iter-0):** the lean baseline advanced to evaluation with an **empty** `reports/qa/…-evidence/` directory and no `ui-test-results.md`. That was harmless for a purely negative "surface absent" finding; it is **not** harmless now — a rendered Structure tab, the chart, verbatim level/zone values, and each honest empty state cannot be confirmed by code inspection. The browser-qa lane MUST run and populate the evidence directory with screenshots; a "surface renders" claim on prose alone is `unknown`, not `passing`.

## IN SCOPE

### Backend
- [ ] Add exactly ONE additive entry `{"path": "/structure", "label": "Structure", "nav": True}` to the `UI_ROUTES` tuple in `apps/backend/app/meta.py` (extend the owning tuple — the nav owner — never a client-side list). This is the ONLY backend edit in this iteration.
- [ ] Add/extend a backend test asserting `GET /meta/ui-routes` now returns the `/structure` entry (`nav: true`) AND that the five pre-interlude entries (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`) are unchanged in value and order.

### Frontend
- [ ] Create `apps/frontend/app/structure/page.tsx` following the `/performance` page pattern (`apps/frontend/app/performance/page.tsx`) — client component, dark-only, Tailwind, reads canonical endpoints only, no business logic.
- [ ] Symbol + as-of controls: reuse `apps/frontend/components/SymbolSearch.tsx` for symbol selection and an as-of time input; on selection, fetch `GET /research/levels?symbol=<S>&as_of=<ISO-T>`.
- [ ] Price chart: render candles from that symbol's recorded series via `GET /research/bars` using `lightweight-charts` — reuse/follow the existing `apps/frontend/components/PriceChart.tsx` pattern; overlay one dashed price line per level, each labelled by its `timeframe`, with `price`/`timeframe`/`type` taken verbatim from `GET /research/levels`.
- [ ] Confluence-zones table: one row per entry in `confluence_zones`, badged **A/B/C** read verbatim from `zone.class` (never recomputed from breadth or score), listing each member level (price + timeframe) and the served `score` verbatim.
- [ ] Three distinct honest empty states plus a degraded state:
  - `no_bar_series_for_symbol: true` → explicit "no bar series recorded — recording historical bars needs provider credentials" state
  - series present but `levels: []` → a distinct "no levels found" honest state (not the same copy as above)
  - levels present but `confluence_zones: []` → a distinct "no qualifying confluence zone" honest state
  - backend unreachable / non-200 → an explicit degraded state consistent with `NavBar.tsx`'s existing pattern (never a fabricated chart/level/zone)

### New user-facing capability
The user can open a **Structure** tab in the app, pick a symbol and as-of time, and see that symbol's computed S/R levels drawn on a price chart plus its A/B/C confluence zones in a table — read-only, straight from the canonical research endpoints, instead of via `curl`/MCP.

### New information displayed
Per-symbol S/R level lines (price + timeframe + type) on a candle chart, and a confluence-zones table with each zone's A/B/C class, member levels, and score — all verbatim from `GET /research/levels`. The **Structure** nav link itself, served from `GET /meta/ui-routes`.

### New user actions
Select a symbol (`SymbolSearch`), set an as-of time, and navigate to the Structure tab from the top-bar nav. Read-only — no mutation, no job, no submission.

### UI surface changes
One new page at `/structure` with a Levels & Zones section (chart + zones table + honest empty/degraded states). One new top-bar nav link, rendered by the existing data-driven `NavBar` with no client edit.

### Product surface delta
The app grows from four visible tabs to five; the era-4 structure computation becomes inspectable in the browser for the first time (levels + zones only this iteration — registry and comparison arrive in J-02/J-03).

### Blueprint conformance
`/structure` is the canonical home of J-01 (Levels & Zones section) under the **Structure** nav section — already present in `blueprint.md`'s Information Architecture (nav skeleton lists `Structure /structure [NEW]`; the J-01 row maps to `/structure` Levels & Zones). This iteration realizes the already-approved IA; it is NOT a nav-skeleton change, so no `blueprint.reapproval-requested` is written.

### Data-contract additions
**None.** Every value J-01 displays is already registered in `blueprint.md`'s Data Contract and is read verbatim from its single existing owner:
- Bar-series candles → `GET /research/bars` (bar store)
- S/R levels (price/timeframe/type) → `GET /research/levels` (`research/levels.py`)
- A/B/C confluence-zone class + score → `GET /research/levels` `zone.class` (`research/levels.py:_grade_zone`/`_confluence_zone`)
- The Structure nav entry → `GET /meta/ui-routes` (`apps/backend/app/meta.py` `UI_ROUTES`)

No new owned value, no second computation, no second endpoint. `blueprint.md` requires no edit for this iteration.

## OUT OF SCOPE

- **J-02** (strategy registry + champion cards) — a later section of this same page; not this iteration.
- **J-03** (`structure_tape`-vs-`v1` backtest comparison + per-class breakdown) — a later section; not this iteration.
- Any backend computation, aggregation, or endpoint beyond the single additive `/structure` entry in `meta.py` `UI_ROUTES`.
- Any edit to `config.py` (fingerprint `4d665603569b9dbf`), `research/levels.py`, `research/bars.py`, `research/backtests.py`, `research/strategies.py`, the engine, or any existing surface's behavior.
- Any client-side recomputation of levels, zone classes, or zone scores (badge/label/line come verbatim from the payload).
- Any champion mutation or promotion; any PnL rendering (there is none in J-01).
- A `/datasets` library-inventory page (roadmap Card 5.9 — explicitly out of this interlude).

## DEFINITION OF DONE

- [ ] **J-01 passes via browser-qa-agent**, with screenshots written to `reports/qa/goal-structure_ui-iter-1-evidence/` for each of: (a) the Structure tab reachable from the top-bar nav; (b) a symbol with a recorded bar series showing level lines on the chart AND a populated A/B/C zones table; (c) the `no_bar_series_for_symbol` honest state; (d) the series-but-no-levels honest state; (e) the levels-but-no-zones honest state.
- [ ] Browser QA confirms the Structure nav link is served by `GET /meta/ui-routes` (data-driven), not a hardcoded client link.
- [ ] Browser QA confirms the rendered level lines and zone table match `GET /research/levels` byte-for-byte for the tested symbol (A/B/C taken from `zone.class`; no client recompute).
- [ ] **J-04 (foundation regression sentinel) stays green:** full backend suite passes, the engine equivalence test proves byte-identical `default` output, `config_fingerprint` remains `4d665603569b9dbf`, and the existing surfaces `/`, `/journal`, `/studies`, `/performance` remain reachable and unchanged.
- [ ] The coherence-auditor returns a clean verdict (no second computation/endpoint, no client-side recompute of levels/classes/scores, honest distinct states).
- [ ] No anti-goal violation introduced (see Goal Mode Metadata reminders).
- [ ] Unit tests pass, including the new `meta.py` route-map assertion (new `/structure` entry present + five prior entries unchanged) and the existing `config_fingerprint` test still green; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-structure_ui-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-01):** exercise all five acceptance states listed in DEFINITION OF DONE, each with a screenshot in `reports/qa/goal-structure_ui-iter-1-evidence/`. Verify the nav link comes from `/meta/ui-routes` and that the on-screen level lines + zone rows equal the `GET /research/levels` payload byte-for-byte (class from `zone.class`).
- **Unit/integration:** `apps/backend/app/meta.py` — assert `GET /meta/ui-routes` includes `{"path": "/structure", "label": "Structure", "nav": true}` and that the five pre-existing entries are byte-identical and in order. Confirm the `config_fingerprint` test still yields `4d665603569b9dbf` (the additive nav entry must not perturb it).
- **Error cases:** `no_bar_series_for_symbol` renders the explicit credentials state (not a blank/fabricated chart); an empty symbol or malformed `as_of` (the endpoint returns 422) surfaces an honest UI state, never a crash or a fabricated chart; a backend-unreachable/non-200 response renders the explicit degraded state.

## NOTES

- **Full depth is mandatory here** (depth-rubric triggers cited in BACKGROUND: backend+frontend boundary crossing; first real surface introducing the critical single-source-of-truth (T10) and honest-state anti-goals; nav-registry / data-driven-nav SSOT edit). The prior evaluator recommended full. The lean pipeline runs neither the auditor nor the coherence lane, and both are load-bearing for a newly introduced read surface.
- **Episodic-memory guard (iter-0 lesson, `Applies to: J-01/J-02/J-03`):** treat any J-01 acceptance state with no populated screenshot in `reports/qa/goal-structure_ui-iter-1-evidence/` as `unknown`, not `passing`. Do NOT accept a "surface renders" claim on prose alone. The iter-0 browser lane produced zero artifacts — that must not recur now that a real surface exists.
- **Single-source-of-truth discipline (T10):** read candles from `/research/bars`, levels + zones from `/research/levels` (`zone.class` for the A/B/C badge), and the nav from `/meta/ui-routes`. Do not add a second computation, a second endpoint, or any client-side grading/aggregation for values already owned by these endpoints.
- **Blueprint:** no edit required — the Structure nav entry and all J-01 values are already registered in `runs/goal-session-structure_ui/state/blueprint.md` (drafted at baseline to cover the whole interlude). No `blueprint.reapproval-requested` is written because the nav skeleton is unchanged from its approved form.
- **Reference implementations to follow (reduce risk, don't reinvent):** `apps/frontend/app/performance/page.tsx` (page pattern), `apps/frontend/components/PriceChart.tsx` (existing `lightweight-charts` usage), `apps/frontend/components/SymbolSearch.tsx` (symbol picker), `apps/frontend/components/NavBar.tsx` (data-driven nav + existing degraded-state copy).
