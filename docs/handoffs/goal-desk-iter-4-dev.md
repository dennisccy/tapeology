# goal-desk-iter-4 Dev Handoff

**Phase:** goal-desk-iter-4
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

Journey **J-04** (the `/desk` briefing page), full depth, plus the five backend hygiene/hardening
items iter-3's `eval.md` Next-Step Recommendation named. `Frontend Present: yes` — this is the
era's first frontend iteration, a brand-new `/desk` page and the `UI_ROUTES` nav-skeleton's second
row (2 → 3).

### Backend

- **`UI_ROUTES` gains its third row** (`app/meta.py`): `{"path": "/desk", "label": "Desk", "nav":
  True}`, appended after Structure. Nav and MCP `ui_route_map` follow automatically via the
  existing `GET /meta/ui-routes` proxy — `NavBar.tsx` was not touched (it already renders whatever
  the endpoint serves). Live-verified: `GET /meta/ui-routes` now returns exactly three entries in
  order (Cockpit, Structure, Desk).
- **`DeskScreenComputeManager` gains `reused: bool` + `screen_id: str | None`** on its job snapshot
  (closes audit B2). `run_screen_and_record` (`desk_screen_compute.py`) now returns `(record,
  reused)` instead of a bare record: `(None, False)` on cancel, `(record, False)` when this call's
  own walk created the persisted snapshot, `(record, True)` when an identical-pin snapshot already
  existed and this call is a pure re-read. `trigger()`'s initial/running snapshot carries
  `reused: false, screen_id: null`; `_work()`/`_resolve()` thread the terminal values through. Zero
  change to `compute_screen`'s row/skip computation or `ScreenStore`'s persisted snapshot shape —
  only the process-scoped compute-manager snapshot gained the two fields. The three existing tests
  that call `run_screen_and_record` directly (and the CLI's `main()`) were updated for the new
  tuple return — the ONLY call sites of that function in the codebase.
- **`POST /research/desk/screen/compute` refuses when no universe snapshot is registered**
  (`desk_routes.py`, closes audit B4): a pre-flight `universe_store.list()` check before calling
  `manager.trigger(...)`; on empty, raises `HTTPException(422, ...)` naming the missing universe,
  mirroring the top-up CLI's own no-universe wording (`desk_topup_compute.py:352-356`, "top up" →
  "screen"). No job starts, nothing is persisted — `ScreenStore.list()` is unchanged before/after.
- **`UniverseStore.record` gains the same corrupt-file `.exists()` guard `ScreenStore.record`
  already has** (`desk_universe.py`, closes iter-1 audit B3 / iter-3's lesson): if a file already
  sits at the snapshot id's deterministic path (content-checksum collision after the duplicate scan
  found no valid match — meaning that file failed its own integrity check), `record` now raises
  `UniverseIntegrityError` instead of silently overwriting it. Mirrors `desk_screen.py:467-473`'s
  guard and message style exactly.
- **`test_desk_screen_compute.py`'s `route_ctx` fixture now scopes `TAPEOLOGY_DATASET_DIR`**
  (closes audit T3) — it was the one `route_ctx` among this file's siblings reading the ambient
  `.data/datasets` tree instead of a temp dir (the route calls `get_dataset_store()` for the
  tick-evidence badge).
- **`journey-scripts/J-07.json` step 8** now sets its own `"timeout_ms": 20000` (the replay
  engine's hard-clamped maximum) instead of inheriting the file's `15000` default. The assertion
  itself (`{"text": "300.11"}`, a plain `<td data-testid="tradable-band-range">` cell) is
  unchanged — live-verified via browser that the text renders correctly for pinned AAPL as-of
  2026-06-22 (see "Live external verification" below).
- **Cache warm-up prerequisite verified live** (test-infra, no code change) — see "Live external
  verification."

### Frontend (all new this iteration — `Frontend Present: no` on J-01/J-02/J-03)

- **`apps/frontend/app/desk/page.tsx`** (new) — the `/desk` briefing page:
  - Honest empty state (`data-testid="desk-screen-not-computed"`): exact text "Desk screen not
    computed yet." + enabled "Run Screen" button, rendered iff `GET /research/desk/screen`'s
    `latest === null`.
  - Provenance panel (universe snapshot id, screen date, `as_of`, `config_fingerprint`, and the
    bar-store freshness value labeled "Window last requested" — never "last bar", per audit
    B9/iter-2 B2) using the existing `Metric` component (`components/Panel.tsx`).
  - Briefing table: symbol, side, band-class chip (with a "nearest same-class band" caption per
    assumptions.md iter-4 entry 1 — `_select_best_band` itself is byte-unchanged), distance-bps,
    band score, per-timeframe coverage badges (rendered from the row's OWN served `coverage` keys —
    never a hardcoded timeframe list, so a symbol with partial coverage, e.g. MSFT's `1h`/`1d` but
    no `4h`/`1w`, renders honestly), tick-evidence badge.
  - Skipped-members section grouped under "Skipped — no bars (N)" / "Skipped — no basis session
    (N)" headings, each rendered only when non-empty; renders even when `rows` is empty (never
    conflated with the not-computed state).
  - Read-only screen-history list (date, rows/skipped counts, provenance summary) — no
    click-through this iteration (J-05 scope).
  - "Run Screen" and "Top-up" buttons, each with its own live progress (pulsing-dot pattern,
    mirrors `/structure`'s `NotComputedPanel`), Cancel control, and single-flight disable
    (`disabled={triggering || isRunning}`) so a second click cannot fire a second POST. Both
    buttons live in the empty-state panel (first-ever run) and in a footer "Run Screen / Top-up"
    panel once a screen exists (so a later day's re-run stays reachable).
  - Mount issues exactly three GETs (`/research/desk/screen`, `/research/desk/screen/compute`,
    `/research/desk/topup/compute`) and zero POSTs — verified by code inspection (the mount
    `useEffect` calls only the three `fetch*` functions) and live browser check (no unexpected
    network activity on load).
- **`apps/frontend/lib/api.ts`** — added `fetchDeskScreen`, `triggerDeskScreenCompute`,
  `fetchDeskScreenCompute`, `cancelDeskScreenCompute`, `triggerDeskTopupCompute`,
  `fetchDeskTopupCompute`, `cancelDeskTopupCompute`, mirroring
  `fetchEdgeReport`/`triggerEdgeReportCompute`/`fetchEdgeReportCompute`/`cancelEdgeReportCompute`'s
  exact `{ok, data, error}` shape and 422/unreachable-fold behavior byte-for-byte.
- **`apps/frontend/lib/types.ts`** — added `DeskScreenRow`, `DeskScreenSkip`, `DeskScreenSnapshot`,
  `DeskScreenMeta`, `DeskScreenListResult`, `DeskScreenComputeProgress`,
  `DeskScreenComputeSnapshot` (including the new `reused`/`screen_id`), `DeskTopupOutcome`,
  `DeskTopupComputeProgress`, `DeskTopupComputeSnapshot` — matching `blueprint.md`'s registered
  shapes field-for-field.

## Files Changed

Backend:
- `apps/backend/app/meta.py` — appended the `/desk` `UI_ROUTES` entry.
- `apps/backend/app/research/desk_screen_compute.py` — `run_screen_and_record` returns
  `(record, reused)`; `trigger()`/`_work()`/`_resolve()` thread `reused`/`screen_id`; CLI `main()`
  updated for the new return tuple.
- `apps/backend/app/research/desk_routes.py` — `trigger_desk_screen_compute` refuses (422) with no
  universe registered.
- `apps/backend/app/research/desk_universe.py` — `UniverseStore.record` gains the corrupt-file
  `.exists()` guard.
- `apps/backend/tests/test_meta_routes.py` — widened the 2-route assertions to 3; added
  `test_ui_routes_includes_desk_now_its_page_ships` (symmetry with the existing Structure test).
- `apps/backend/tests/test_desk_screen_compute.py` — updated the 3 direct `run_screen_and_record`
  callers for the new tuple return; `route_ctx` now scopes `TAPEOLOGY_DATASET_DIR`; added
  `test_trigger_resolves_reused_false_and_its_own_screen_id_on_a_fresh_compute` (TC-8),
  `test_trigger_resolves_reused_true_and_the_existing_screen_id_on_a_repeat_compute` (TC-7),
  `test_initial_and_running_snapshot_carry_the_honest_reused_false_screen_id_null_defaults`, and
  `test_post_trigger_with_no_universe_registered_refuses_and_persists_nothing` (TC-9).
- `apps/backend/tests/test_desk_universe.py` — added
  `test_recording_over_a_corrupted_file_at_the_same_key_is_refused_never_a_silent_overwrite`
  (TC-10), mirroring the existing `test_desk_screen.py` test.
- `runs/goal-session-desk/journey-scripts/J-07.json` — step 8 `"timeout_ms": 20000`.

Frontend:
- `apps/frontend/app/desk/page.tsx` (new) — the `/desk` page.
- `apps/frontend/lib/api.ts` — 7 new fetch/trigger/cancel functions.
- `apps/frontend/lib/types.ts` — 10 new type declarations.

**Not touched, deliberately** (verified via `git diff --stat`, all empty): `apps/backend/app/config.py`,
`apps/backend/app/research/tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
`desk_screen.py` (row/skip computation), `desk_coverage.py`, `desk_topup_compute.py`, `routes.py`,
`apps/frontend/app/structure/page.tsx`, `apps/frontend/components/PriceChart.tsx`,
`apps/frontend/components/StructureChart.tsx`, `apps/frontend/components/NavBar.tsx`,
`apps/frontend/app/page.tsx`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`

Result: **1305 passed, 8 skipped, 0 failed** (floor was 1299 passed / 8 skipped — this diff adds
exactly 6 new passing tests: 1 in `test_meta_routes.py`, 1 in `test_desk_universe.py`, 4 in
`test_desk_screen_compute.py`; zero new skips, zero regressions). Note: this pytest install's `-q`
mode does not print the final one-line summary in this environment when run over the full `tests/`
directory (a pre-existing environment quirk also noted in iter-3's handoff) — ran WITHOUT `-q` to
get the explicit `"1305 passed, 8 skipped, 2 warnings in 128.75s"` line.

Frontend: `cd apps/frontend && rm -rf .next && npm run build` — compiles successfully, TypeScript
strict-mode typecheck passes with zero errors, `/desk` registers as a static route alongside `/`
and `/structure` (no test script exists in `package.json`; `next build`'s typecheck + production
build is this project's frontend verification step, per prior iterations' handoffs and the
README's own documented command set).

- `Config().config_fingerprint()` == `08e471b10130e1e2` for both the live `CONFIG` singleton and a
  fresh `Config()` — confirmed live via `python -c`, unchanged. Zero new `Config` fields.
- **Frozen modules zero-diff (TC-17):** `git diff --stat` on `config.py`, `tradability.py`,
  `levels.py`, `bars.py`, `bar_index.py`, `desk_screen.py`, `desk_coverage.py`,
  `desk_topup_compute.py` is completely empty.
- **Kept-surface zero-diff (J-07):** `git diff --stat` on `apps/frontend/app/structure/`,
  `PriceChart.tsx`, `StructureChart.tsx`, `NavBar.tsx`, `apps/frontend/app/page.tsx` is completely
  empty — the sanctioned `/structure` J-05 prefill is explicitly OUT OF SCOPE this iteration and
  was not touched.
- `test_lint_frontend_source_literals_are_clean` (unmodified) passes — the new `/desk` source is
  automatically covered (it scans `apps/frontend/app/**/*.tsx`) and reports zero
  imperative/predictive/certainty-claim violations.

### Live external verification (real ambient backend, zero mocks)

Per the pre-handoff checklist, ran `scripts/dev.sh` (backend `:8301`, frontend `:3301`) against the
REAL `apps/backend/.data/` tree — which, from prior operator/dev-session activity, already holds a
real recorded screen (`screen-2026-06-22-3ecd45c062c7`, 10 ranked rows / 91 skipped, over the real
101-member universe) — and exercised the whole stack live, including a real browser pass:

- `GET /meta/ui-routes` → exactly three entries, `Cockpit`/`Structure`/`Desk`, in order.
- `GET /research/desk/screen` → served the real populated snapshot (not the empty state).
- **Browser-verified `/desk`** (Chrome, 1440×1000, full-page screenshot): nav shows Cockpit ·
  Structure · Desk with Desk active (emerald); Provenance panel shows all 5 fields; Briefing table
  renders all 10 real ranked rows with correct chips ("Class A" + "nearest same-class band"
  caption), monospace distance/score, and per-timeframe coverage badges — verified via DOM query
  that EVERY row carries exactly 4 badges with the row's own true/false `has_bars` values (e.g.
  AAPL all-true, MSFT `1h`/`1d` true and `4h`/`1w` false — matching the exact iter-2-documented
  partial-coverage example), never a hardcoded/assumed set; Skipped Members section renders all 91
  `no_bars` rows grouped under the correct heading, including one row (`PG`) carrying a tick-evidence
  badge, confirming the independent-read discipline; Screen History shows the one real entry with
  correct counts and provenance summary; the footer "Run Screen / Top-up" panel renders both
  buttons enabled (`disabled: false`) with the correct labels ("Run Screen", "Top-up") verified via
  DOM query. Did NOT click either button against the real ambient store (a real ~100-member
  screen/top-up run is an explicit operator act, out of scope for a dev sanity check, and would
  leave a real side effect in the append-only store that isn't mine to create).
- **Browser-verified the J-07 kept-surface regression clause live**: `/structure`, symbol `AAPL`,
  as-of `2026-06-22T21:00:00Z`, Load → the pinned wall renders (`resistance 300.11–302.2 Class A
  score 171`), confirming the exact text (`"300.11"`) the newly-timeout-adjusted J-07.json step 8
  asserts. Nav on `/structure` also correctly shows exactly 3 routes with Structure active.
- **Cache warm-up mechanism verified** (isolated scratch script, scoped temp dirs + the committed
  AAPL daily fixture, mirroring `test_desk_screen_compute.py`'s `real_ctx` pattern): first
  `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T21:00:00Z` call 72.1ms (cold), second
  call same process 7.3ms (warm), a FRESH process against the SAME durable
  `TAPEOLOGY_TRADABILITY_CACHE_DB` path 18.4ms — confirms the cache genuinely survives process
  restarts, the property the browser-QA/replay warm-up step depends on. This scratch verification
  used a small isolated fixture, not the full real store, so the absolute cold-call magnitude here
  (72ms) is not representative of the ~21.6s figure prior iterations measured against the full
  ambient store — only the MECHANISM (warm reads are 10×+ faster and durable across restarts) was
  the thing to confirm.
- Service restart verified clean: killed both processes (by PID, not just `pkill -f` — see Known
  Issues), confirmed both ports free, restarted `scripts/dev.sh`, backend came up in 2s with no
  port conflict. Cleaned up fully afterward; confirmed both ports free and no stray
  uvicorn/next-server processes belonging to this project remained.

## Known Issues

- **`pkill -f "uvicorn"` / `pkill -f "next dev"` did not reliably kill this project's dev
  processes** in this environment — the first cleanup attempt left the actual server PIDs running
  (confirmed via `ps aux` immediately after). Killing by explicit PID (found via `lsof
  -tiTCP:<port> -sTCP:LISTEN`) worked reliably. Whoever next needs to stop `scripts/dev.sh`'s
  children should use the port-based PID lookup, not a bare `pkill -f` pattern match — this is the
  SAME gotcha iter-3's dev handoff flagged for `next dev`'s process tree; this iteration also saw
  it on the `uvicorn` side.
- **The "Browser-QA / replay prerequisite" warm-up is inherently a QA-dispatch-time action, not a
  durable code artifact.** `resolve_tradability_cache_db_path` resolves the cache DB as a SIBLING
  of whatever `TAPEOLOGY_BAR_DIR` currently points at — so a FIXTURE-SCOPED backend (a fresh temp
  dir, per the plan's NOTES on the browser-QA environment) gets a brand-new, cold cache every time,
  regardless of anything warmed against the ambient store in this handoff. The exact recipe for
  whoever dispatches browser QA / the replay lane: after starting the fixture-scoped backend (env
  vars `TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR` at a shared
  temp dir seeded with the committed 103-member universe fixture + committed AAPL/MSFT bar
  fixtures), issue ONE `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T21:00:00Z` call (or
  one `/structure` Load) against that SAME running instance BEFORE dispatching browser QA or the
  deterministic replay lane — this pays the cold-cache cost once, up front, rather than risking
  J-07 step 8's 20000ms budget on a cold first call.
- **Did not exercise the real ~101-member Run Screen / Top-up compute against the ambient store.**
  Confirmed live that both buttons render correctly, are enabled, and are wired to the correct
  endpoints (via code review + the passing backend route/manager tests), but did not click either
  against real data — that would be a genuine, slow, side-effecting operator act (a new permanent
  screen snapshot for today's date, or up to 404 real Yahoo fetch attempts), not something to
  trigger casually during a dev sanity pass. The backend compute-manager mechanics (single-flight,
  cancel, progress, `reused`/`screen_id`) are fully covered by the passing unit/integration tests
  instead.
- Everything else is in scope and complete: J-04's three required screenshots' worth of content
  (empty-state text + button, populated briefing + provenance + skipped grouping, nav = 3 routes)
  is confirmed renderable and correct via the live browser pass above; the actual browser-qa-agent
  dispatch (fixture-scoped, with its own screenshot capture discipline) is the next pipeline step,
  not part of this handoff.

---

## Fix Notes — audit fix pass (2026-07-26)

Input: `docs/handoffs/goal-desk-iter-4-audit.md` (verdict FAIL). Every listed finding is addressed
below; nothing else was touched. Suite after the pass: **1328 passed / 8 skipped / 0 failed**
(floor 1299/8; the audit's own re-run measured 1305/8). `Config().config_fingerprint()` ==
`08e471b10130e1e2` for both a fresh `Config()` and the singleton.

### B1 — CRITICAL, the priceless-bar rail (fixed, live-verified)

The audit's chain was reproduced and closed at three points. Root cause first: **the LIVE Yahoo
vendor is still serving that exact row today** — a direct `yfinance` call on 2026-07-26 for AAPL
`1d` returns 8 rows, one of which is
`2026-07-24 00:00:00-04:00  open=nan … volume=47402209.0`, byte-identical to the poisoned bar the
audit found. So this was never a one-off.

1. **`providers/adapters/yahoo.py` — drop a priceless vendor row at the seam.** New `_is_priced_row`
   predicate; a row without four finite prices (and a finite volume) is an ABSENT bar and is skipped,
   exactly as an empty chunk is. An all-priceless window still raises the existing honest
   `NoDataForWindow` (`rows_by_epoch` stays empty). Live proof after the fix: the same call returns
   **7 bars, zero non-finite** — the real bars byte-identical.
2. **`research/bars.py::BarStore.record` — refuse the write.** New `NonFiniteBarPriceError`, raised
   before any checksum work, naming the offending timestamp and its four values. Nothing reaches
   disk: no file, no registry row, no integrity error. This makes "a priceless bar can never reach
   disk" structural for every write path, present and future, not a per-caller convention.
   `POST /research/bars` maps it to the same honest 422 the empty-window refusal uses
   (`research/routes.py`), so no caller gets an opaque 500.
3. **`research/bars.py::_merged_rows` — exclude any already-recorded priceless ROW** from the fold
   and report it in the EXISTING `integrity_errors` channel ("N recorded row(s) carry a non-finite
   price … the file itself is unchanged"). Files are never touched. The report rides along in the
   memoized cache value, so affected pairs stay memoized and the cache-HIT path reports the exclusion
   identically to the cache-MISS path (asserted).
4. **`components/StructureChart.tsx` — a finite guard before `setData`** (defence in depth, not the
   fix). Non-finite rows are filtered out of both the store series and the live series; the viewport
   anchor, the as-of index and the "any candles" hint all index the filtered array so a dropped row
   can never shift the operator's scroll onto the wrong candle. A `structure-chart-undrawable-rows`
   note states the count when it is non-zero (it is zero now, because the backend already excluded
   the row) — one bad row degrades the chart, it can never delete the page again.

**Fate of the 60 already-recorded series** (audit §5 item 3 — the decision it declined to make):
row-level exclusion, nothing deleted, nothing re-fetched, nothing perturbed. Recorded in
`runs/goal-session-desk/state/assumptions.md` as `iter-4 (fix pass) — developer` with the
measurements behind it. The two alternatives were rejected on evidence, not preference:

- **File-level quarantine was measured and rejected.** Excluding the whole 501-bar AAPL `1d` series
  (the only recording covering 2024-07..2024-12) moves the tradable map's entire support side
  as-of 2026-06-22: `support A 222.68–224.23 score 688.6` → `support A 274.60–276.51 score 471.7`.
  Deleting one bad row must not silently move every band 500 good bars support.
- **A superseding revision series cannot work** — the vendor has no prices for that timestamp at all
  (verified live), so a clean re-fetch omits it and the merged union keeps the old priceless row.
- **Tolerate-on-read was rejected because the damage was not cosmetic.** Measured on the ambient
  store: `compute_tradability("AAPL", as_of=2026-07-25)` returned **`bands: []`** with the NaN row as
  its basis; with the row excluded it returns 10 honest bands off basis 2026-07-23. The priceless
  rows were silently deleting the tradable map for recent as-of dates, not only crashing the chart.

**Zero-diff constraints lifted, explicitly** (the audit named both as prerequisites): `bars.py` and
`components/StructureChart.tsx`, scoped to the priceless-bar rail only. `docs/phases/goal-desk-iter-4.md`
OUT OF SCOPE and TC-17 are amended in this same commit. Still zero-diff and verified as such:
`config.py`, `tradability.py`, `levels.py`, `bar_index.py`, `desk_screen.py` (so `_select_best_band`
and `compute_screen` are untouched), `desk_coverage.py`, `desk_topup_compute.py`,
`apps/frontend/app/structure/`, `apps/frontend/app/page.tsx`, `components/PriceChart.tsx`.

**Live re-verification of J-07's exact steps** (`reports/qa/goal-desk-iter-4-evidence/FIX-J-07-structure-alive.png`),
backend `:8301` + `next dev :3301` after `rm -rf .next` and a full rebuild:

| Check | Before (audit) | After |
|---|---|---|
| `GET /research/candles?symbol=AAPL&timeframe=1d…` null prices | `"open": null` present | **0 rows with a null price**; `integrity_errors` names `55bb757e….json` |
| `/structure` page errors after Load | `Assertion failed: Candlestick series item data value of open must be a number, got=object, value=null` | **`[]`** (also zero console errors) |
| page body after settle | collapsed to **127 chars** | **57,265 chars**, held for 8s |
| pinned wall | rendered then vanished | `tradable-band-range` = **`300.11–302.2`**, still on screen |
| chart drew | destroyed | caption visible, **7 canvases** |

New/changed tests: `test_yahoo_adapter.py` (+5: drops an all-NaN row, leaves neighbours byte-identical,
all-priceless window raises `NoDataForWindow`, NaN volume dropped), `test_bars.py` (+17 incl. 12
parametrized: `record` refuses nan/inf/-inf on each of the four price fields; a per-series read still
serves the stored truth; the merged read excludes and reports; the file's bytes are unchanged after
four different reads; the memo still serves and still reports), `test_bars_api.py` (+1: the exact
endpoint the chart pages never serves a null-priced candle).

### B2 — refusal wording when a universe exists but is corrupt (fixed)

`desk_routes.py::trigger_desk_screen_compute` now reads BOTH halves of `universe_store.list()`. With
records empty and errors present it refuses with "no READABLE universe snapshot is registered …
N snapshot file(s) failed their integrity check", naming each file — and deliberately does NOT
suggest `POST /research/desk/universe/fetch`, which is the wrong action for a damaged file. The
absent-universe wording is unchanged. New test asserts both wordings and that nothing is persisted
or started in either case.

### B3 — `_work`'s cancelled-state comment overstated its invariant (fixed)

The comment now states the real, honest behaviour: `record is None` means the cancel was observed
before any write, but a cancel landing between `run_screen_and_record`'s `should_abort()` check and
`_resolve` resolves `state: "cancelled"` WITH a non-null `screen_id` (and `reused: true` if that pin
was already on file). Behaviour unchanged — reporting the snapshot that really was written is more
honest than reporting null for one the operator can go and read. Comment only, no code change.

### F1 — the provenance line labelled a checksum as a freshness value (fixed)

`Window last requested  d7bc8f8127904d0a` → **`Bar-store signature`** plus a caption
(`desk-provenance-signature-note`) stating it is a checksum over every member's
window-last-requested timestamp — a pin, never a time — and that each coverage badge's tooltip
carries that member's own window-end value. The freshness LABEL now lives only where it is true.
`blueprint.md` (nav skeleton row + registered-decision 3) and the phase spec's own bullet are
amended in the same commit, as the audit required. Live-verified on `/desk`.

### F2 — an all-false coverage badge set had no on-screen explanation (fixed)

`desk-coverage-divergence-note` renders above the briefing table when at least one ranked row has
every timeframe dark, stating that rank comes from the bar store the screen read directly while
coverage comes from the derived bar index — two independent reads, each rendered as served. Live on
the ambient screen it reads "7 ranked row(s) below show every timeframe badge dark", matching the
audit's own count of 7 of 10.

### F3 — raw float precision in the dense briefing (fixed)

`0.33523150389608725 bps` → `0.34 bps` via the existing `lib/format.ts` `fmt` helper (the project's
one number-formatting convention), with the SERVED value in full on each cell's `title`. Nothing is
lost, only formatted. Live-verified: cell text `0.00 bps` / `217.00`, titles `0` / `217`.

### F4 — a failed post-compute refetch discarded the last known briefing (fixed)

The terminal-state refetch now uses a functional update: a failed GET keeps the last known GOOD
state (TC-21's discipline, previously applied only to the poll); when nothing good was ever loaded
the honest failure IS adopted, so the operator still sees the unavailable panel rather than a
permanent skeleton.

### F5 — `reused` / `screen_id` were threaded but never surfaced (fixed)

`desk-screen-compute-outcome` renders on a `done` terminal state: "Reused the snapshot already
recorded for this key — `<id>`" vs "Recorded a new snapshot — `<id>`". This is the point of the two
fields the iter-3 audit asked for; without it, a reuse looked identical to a fresh compute.

### T1 — the J-07 golden could not catch this class of breakage (fixed)

`runs/goal-session-desk/journey-scripts/J-07.json` gains three steps after the Load assertion:
step 9 `wait_for {ms: 4000}` (the crash fired ~0.1s past step 8's expect), step 10 an `expect` on
`tradable-map-chart-caption` re-asserting `300.11` is STILL on the page, step 11 an `expect` on
`[data-testid="structure-chart-canvas"] canvas`. Script re-validated with the runner's own
`validate_script` (zero errors) and both assertions confirmed against a live page. **Honest gap:**
the audit also asked for a zero-page-error assertion; the replay vocabulary
(`goto`/`click`/`fill`/`expect`/`wait_for`) has no page-error primitive, and `demo_runner.py` is
vendored framework code that must not be edited from a project iteration. My own live harness DOES
assert zero page errors (evidence above) and the caption+text-after-settle pair catches this exact
failure mode (the audit's repro collapsed the body to 127 chars), but a framework change is needed
for a first-class page-error gate — carried below as a Known Issue.

### T2 / T3 — QA evidence and the missing browser-qa-agent dispatch (NOT developer-fixable)

Both are pipeline-step defects, not product defects, and are left for the re-run: `TC-01-empty-state.png`
shows a populated briefing, `TC-12-topup-progress.png` and `TC-12-topup-cancelled.png` are the same
blank image (md5 `63e1402e50e2f1b17323b30c83b11483`), TC-02's Actual text contradicts itself, and no
browser-qa-agent step appears in the trace. The plan's fixture-scoped browser-QA recipe (repeated in
this handoff's Known Issues above) is what stops a QA pass from writing into append-only stores again
— which is how B1's damage and a permanent QA-authored `2026-07-25` screen snapshot got there.
The audit's `AUDIT-*.png` files plus my `FIX-*.png` files are the reference for what these states
look like.

### Known Issues added by this fix pass

- **The 60 poisoned series are still on disk** (58 symbols incl. AAPL `1d`), by decision. They are
  excluded from every merged read and permanently reported in that pair's `integrity_errors` until an
  operator chooses to act. `/research/candles?symbol=AAPL&timeframe=1d` therefore now returns
  `bar_count: 500` (was 501) and one integrity-error entry — both honest, and the pinned
  2026-06-22 tradable map is byte-identical field-for-field to before.
- **No page-error gate exists in the deterministic replay lane** (T1 above). Any runtime error that
  arrives after a journey's last matching string is still invisible to that lane. This needs a
  `demo_runner.py` change in the framework, not a project iteration.
- **The Top-up button was not clicked against the real vendor in this pass** — deliberately, since
  that writes to the append-only store, and doing it is precisely what caused B1. The two halves of
  the rail are instead verified independently: the adapter against the LIVE vendor (8 raw rows → 7
  bars, the priceless row confirmed still being served), and `record`'s refusal by unit test.
