# Iteration diff (bounded)

Files changed: 2. Shown in full: 0.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `docs/goal-archive/goal-2026-07-17.md` (159 lines not shown)
- `docs/goal.md` (780 lines not shown)

```diff
diff --git a/docs/goal-archive/goal-2026-07-17.md b/docs/goal-archive/goal-2026-07-17.md
new file mode 100644
index 0000000..39ce222
--- /dev/null
+++ b/docs/goal-archive/goal-2026-07-17.md
@@ -0,0 +1,553 @@
+# Tapeology — Project Goal (Interlude: The Fast Wall — /structure at interactive speed & the operator-run edge report)
+
+> Eras 1–5B are the **foundation** of this goal and MUST NOT regress. Eras 1–2 (tape reading + the research
+> evolution, J-01 – J-68, GOAL_ACHIEVED) are archived at
+> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md); the structure-UI interlude at
+> [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md); **Era 5 "The Library"** at
+> [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md). Era 3 (the profit-research
+> measurement machine), Era 4 (the structure-and-tape evolution), and **Era 5B "The Tradable Wall"
+> (GOAL_ACHIEVED 2026-07-16, session `tradable_wall`, J-01 – J-08)** are frozen foundation; their records live
+> in git history and in `reports/goal-session-tape_to_profit-delivered.md`,
+> `reports/goal-session-tape_to_profit_support_resistence-delivered.md`, and
+> `reports/goal-session-tradable_wall-delivered.md`.
+>
+> **This chapter is an operator-directed performance interlude, not one of the numbered research eras** (the
+> [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md) UI interlude is the precedent). It
+> adds **no research finding and changes no research value** — every number the product serves stays
+> byte-identical. It is *enabling work* for the router
+> ([`docs/research-directions.md`](research-directions.md) Part 5.1): era 6 "Referee" needs the three-way edge
+> report as its input, and that report has **never once completed** on the real corpus — the compute cost
+> era 5B honestly documented is, measured, ~99% redundant recomputation. This interlude removes the waste,
+> makes the sweep an explicit resumable operator act, and makes `/structure` load at interactive speed.
+
+## Vision
+
+Era 5B filled `.data/` with real ticks (18 registered datasets, 882MB) and shipped the three-way edge report —
+and exposed the next honest problem: **the product cannot serve its own evidence**. Measured on the real
+corpus (2026-07-16, 16-core operator machine):
+
+- Opening `/structure` fires `GET /research/edge-report`; with the result cache empty (0 rows — the real
+  compute has never finished) the route **synchronously starts the full backtest sweep inside the page's own
+  request**, with no single-flight guard — every page load piles on another sweep. Observed: the backend
+  worker pinned at 98% CPU for hours after a single page visit, degrading every other endpoint through the
+  GIL, while the Edge Report section spins forever.
+- `GET /research/datasets` takes **31.4s to return 8.6KB of metadata**, because `DatasetStore.list()`
+  re-reads, re-parses, and double-sha256s all 882MB on every call (~30MB/s measured).
+- `GET /research/setups` takes **minutes** when cold: ~456 `compute_tradability` calls, each re-reading and
+  re-hashing all 47 bar files — **~17GB of cumulative re-read observed** for one request — plus O(n²) pivot
+  math; its only cache is one in-process slot wiped by every dev-server reload.
+- The sweep's documented "~10+h" is not real work. Raw engine replay runs at **12,829 events/s** (the whole
+  ~9.1M-event corpus ≈ 12 min per strategy); a `v1` backtest of a 14,241-event dataset takes **1.37s** — but
+  `structure_tape` on the SAME dataset could not finish in 9.3 minutes (**≥400×**), because the arming check
+  re-runs the FULL levels pipeline (including a whole-bar-store re-read + re-hash) **per confirming tick**.
+  Yet levels are a pure function of the as-of bar prefix, which changes only when a bar closes (~100 distinct
+  states per session), and the tradable map's basis is constant per UTC session date.
+
+This interlude makes the wall fast without moving a single brick:
+
+1. **`/structure` never computes** — `GET /research/edge-report` answers instantly from the durable cache or
+   with an honest "not computed" state; the sweep runs only as an explicit operator act.
+2. **The stores stop re-reading** — verified-content caches (stat-keyed, tamper-safe, rebuildable) end the
+   882MB-per-call and 17GB-per-scan festivals; restarts stop re-paying minutes.
+3. **The sweep stops wasting** — a per-run memo serves the arming checks from the ~100 real level states per
+   session instead of recomputing per tick, byte-identically.
+4. **The compute becomes an operator act** — a single-flight, cancellable, progress-reporting background job
+   (UI button + CLI warmer), **resumable** (durable per-dataset×strategy sub-results) and **parallel**
+   (process pool), so the first-ever completed real edge report costs minutes, not "never" — and a future
+   dataset costs only its own three backtests.
+
+Every accelerator is a **rebuildable derived value, never a source of truth**: deleting any of them loses
+nothing and fabricates nothing, and equivalence tests prove the accelerated outputs byte-identical to fresh
+computes. The measured baselines above are this interlude's ground truth; the deliverable is the same product,
+served at the speed its own honesty deserves.
+
+## Target Users
+
+- The project owner (a discretionary intraday trader) whose `/structure` page currently hangs for minutes and
+  whose machine burns hours of CPU per page visit — and who has never yet been able to SEE the real-corpus
+  edge report era 5B built.
+- AI dev-chain agents (the goal-mode chain) building and browser-verifying the fast path, the honest
+  not-computed state, and the operator-run compute.
+
+## Foundation invariants (still law — eras 1–5B)
+
+The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md)), the
+era-3 measurement machine, the era-4 structure stack, the era-5 keyless bar library, and the era-5B tradable
+wall remain binding verbatim on ALL new code: price-impact-over-aggression; honest uncertainty; **no
+fabricated data**; single source of truth; no magic numbers; provider-agnostic engine; deterministic &
+reproducible; no secrets in source; research read-only over the engine; journal/record integrity;
+source/feed/`config_fingerprint` honesty; the existing surfaces (`/`, `/journal`, `/journal/[id]`, `/studies`,
+`/performance`, `/structure`) stay intact.
+
+In addition, these stay **frozen foundation**:
+
+1. The **tape engine** emits its five states byte-identically under `default`; `config_fingerprint` stays
+   `4d665603569b9dbf` (equivalence-tested). **This interlude adds ZERO `Config` fields** — every new
+   operational knob is an env var + derived sibling path (the `bar_index` / `TAPEOLOGY_BAR_INDEX_DB`
+   precedent), so the fingerprint cannot move.
+2. The **research computations** — `levels.py` (raw levels + A/B/C zones and its parameters),
+   `tradability.py` (the ≤10-band map), `setups.py` (the scan + reactions + forward returns),
+   `edge_report.py` (the three-way cells, gates, null baseline, register), the strategy registry
+   (`v1` + `structure_tape` + `structure_tape_map`), the class-scaled math, and the backtest runner's
+   simulated trades — stay **behaviorally byte-identical: identical inputs keep producing identical
+   outputs.** This interlude changes only *when and how often* they are computed, never *what* they compute.
+3. The **stores** — the JSON `BarStore` and `DatasetStore` file formats, checksums, append-only immutability,
+   and split freezing — are untouched on disk; the verification discipline (a corrupt or tampered file is an
+   explicit error, never silently served) is preserved at every read that loads content.
+4. **`v1`, `default`, `structure_tape`, `structure_tape_map`, and the champion pointer are frozen.** The
+   champion moves only through the existing sweep gate on hold-out data; nothing here promotes.
+5. The **era-5B UI surfaces** — `/structure`'s Tradable Map / Case Studies / Edge Report sections, the raw
+   toggle, the era-5 fetch control + provenance badge, and the cockpit band overlay + confluence chip — keep
+   working exactly as shipped, including the frozen warm-cache texts ("No edge-report cells yet.", the
+   "simulated — assumed fees/slippage — not indicative of live results" register).
+6. The **existing rebuildable accelerators** — the derived `bar_index`, the J-08 `EdgeReportCache`, and the
+   setups `_SCAN_CACHE` discipline — keep their contracts (rebuildable, never a source of truth, loss loses
+   nothing); this interlude extends the same discipline, it never weakens it.
+
+## Success Criteria
+
+In priority order — honesty and non-regression outrank speed:
+
+1. **Nothing existing regresses.** Full backend suite green (no test deleted or weakened), engine equivalence
+   proves byte-identical `default` outputs, `config_fingerprint` stays `4d665603569b9dbf`, every era-1–5B
+   surface behaves exactly as shipped, and the warm-cache Edge Report render (cells or the honest
+   "No edge-report cells yet." empty state, register visible) is byte-equal to before.
+2. **`/structure` never triggers compute.** `GET /research/edge-report` answers within an interactive budget
+   in every state — a warm cache serves the report verbatim; a cold cache returns an honest, explicit
+   "not computed" payload and **starts nothing**. Opening the page never costs the machine hours (or even
+   seconds) of sweep CPU.
+3. **The heavy reads answer at interactive speed when content is unchanged.** With stores unchanged since the
+   last verified read, `GET /research/datasets` and `GET /research/setups` serve from verified-content caches
+   without re-reading the corpus (proven by zero-re-read spy tests keyless; observed sub-second on the real
+   corpus by the operator), and a backend restart no longer re-pays the 31.4s / minutes cold costs (durable
+   accelerators).
+4. **The first full real edge report completes — as one resumable operator act.** The sweep runs only via the
+   explicit trigger (UI button or CLI warmer): single-flight, cancellable, progress-visible, **resumable**
+   (a killed run re-computes only missing dataset×strategy pairs) and **parallel** (process pool; expected
+   ~10–20 min on the operator's 16-core machine vs never-completing today). Once computed it serves instantly
+   from the durable cache, and the completed three-way comparison is appended to
+   `reports/pnl/pnl-history.md` — closing era-5B J-08's still-outstanding step 3.
+5. **Every accelerator is rebuildable and proven byte-identical.** Deleting any cache/index DB loses nothing
+   (the next read re-verifies/recomputes); determinism and equivalence tests prove cached/memoized/parallel
+   outputs byte-identical to fresh sequential computes; a tampered store file is still detected on every
+   content change.
+
+## Key Capabilities
+
+Layered strictly on top of the era-1–5B capabilities, which remain unchanged.
+
+1. **Cache-or-honest-absence GET** — `EdgeReportCache` gains `lookup(records, config)` (serve the current
+   key's row, hot-slot then durable, never computing) and `compute_and_publish(...)` (the always-recompute
+   operator path); `edge_report.py` gains `peek_strategy_comparison_report(...)`: store-integrity errors keep
+   raising `EdgeReportError` (the route's explicit 500); a warm key serves the report **verbatim**; an
+   **empty dataset registry still computes inline** (O(1) — zero backtests — preserving the existing
+   empty-registry response shape and MCP byte-identity); a cold key returns the honest not-computed payload.
+   The route swaps one call; the payload's `register` field is read from `backtests.REGISTER`, never a
+   restated literal. Path policy for the cache DB is extracted to one shared resolver
+   (`TAPEOLOGY_EDGE_REPORT_CACHE_DB` env else sibling of the dataset dir — exactly today's rule).
+2. **Verified-content store caches** — `bars.py` and `datasets.py` gain module-level stat-keyed caches of
+   VERIFIED loads: key `(absolute path, st_size, st_mtime_ns)`; a stat match serves the already-verified
+   record with zero I/O; ANY mismatch re-runs the full existing verifier (both checksums); integrity errors
+   are never cached; a ~2s "racy write" guard refuses to cache freshly-written files (same-granularity
+   rewrites can never be served stale); atomic single-slot publish (the `_SCAN_CACHE` read-local-ref
+   discipline). `BarStore` caches meta + rows (6.5MB total; `get`/`list` serve per-row copies so a caller
+   mutation can never poison the cache; `load_bars` builds fresh `RawBar`s). `DatasetStore` caches
+   **metadata ONLY** (882MB of rows never live in RAM) and only for `get()`/`list()` — **`load_events()` and
+   `replay()` keep full verification on every load** (the trust boundary, pinned by tests). A durable sibling
+   **dataset metadata index** (`dataset_index.db`; env `TAPEOLOGY_DATASET_INDEX_DB`; `bar_index.py`'s
+   "derived, rebuildable, owns nothing" shape; meta JSON stored WITHOUT `sort_keys`) makes restarts stop
+   re-paying the 882MB parse.
+3. **The arm memo** — `levels.py` gains `level_change_points(store, symbol)` (the sorted union of every
+   healthy series' bar epochs for the symbol plus each prior-period bar's `epoch + period_seconds` close
+   instant — a conservative superset; between two consecutive change points `compute_levels` is a constant
+   function of `as_of`); `tradability.py` gains `basis_day_key(as_of_epoch)` (its basis resolution is
+   constant per UTC session date). `backtests.py` gains a small per-run `_StructureArmMemo` with
+   `levels_at(as_of)` / `tradability_at(as_of)` (keyed by change-point interval / day key; a miss calls the
+   one canonical owner), built once per `structure_tape` / `structure_tape_map` run and threaded into the
+   arming checks as an optional keyword — collapsing thousands of per-tick recomputes into the ~100 real
+   level states per session, byte-identically.
+4. **The operator-run compute** — new `edge_report_compute.py`: `EdgeReportComputeManager` (registry-scoped
+   like the existing job managers; single-flight; cooperative cancel; an atomic progress snapshot:
+   `{id, state, force, started_utc, finished_utc, error, progress: {phase, backtests_total, backtests_done,
+   backtests_from_cache, current}}`), driving the ONE computer `run_strategy_comparison_report` with new
+   additive keyword-only hooks (`progress=`, `should_abort=`, `sub_cache=`, `workers=`, `force=` — all
+   defaulting to today's exact behavior). Routes: `POST /research/edge-report/compute` (idempotent
+   single-flight: a second POST returns the running snapshot with `started: false`),
+   `GET /research/edge-report/compute` (snapshot or `null`), `POST /research/edge-report/compute/cancel`
+   (409 when idle; a cancelled sweep caches no report). A CLI warmer — `python -m
+   app.research.edge_report_compute --workers N [--force] [--out report.json]` — resolves the same seams the
+   backend reads, prints per-backtest progress, is nohup-able, and survives backend restarts because it
+   writes the same durable SQLite caches the GET serves. **No new MCP tool** (MCP stays a read-only proxy
+   surface; the new GET status route is additive REST only).
+5. **The resumable + parallel sweep** — `EdgeReportBacktestCache`: one durable row per (dataset × strategy)
+   result block, keyed by `{dataset_id, dataset_checksum, strategy_id, profile, config_fingerprint,
+   config_content_hash, strategy_registry, bar_store_signature}` — the bar-store term (the sorted
+   `(symbol, timeframe, id, checksum)` tuples `setups._store_signature` already computes) is load-bearing:
+   the structure strategies read bar content per event, and the EXISTING persisted backtest journal rows are
+   NOT a safe resume source precisely because their `config_fingerprint` excludes the
+   `sr_*`/`tradability_*`/`setups_*` families and records no bar content. Values are the runner's `result`
+   blocks verbatim (stored WITHOUT `sort_keys`; the null-baseline seed is the config-owned constant, so a
+   cached block is byte-identical to a re-run by the runner's own documented contract). `_split_cells` gains
+   a `run_pair(dataset_meta, strategy_id)` provider seam (default = today's inline call; pooling and ordering
+   code untouched, so reassembly from cached blocks is byte-identical **by construction**). Each pair
+   publishes durably the moment it completes → a killed sweep resumes with only the missing pairs; a newly
+   recorded dataset costs exactly its own three backtests + reassembly. Parallel mode (CLI `--workers` / env
+   `TAPEOLOGY_EDGE_SWEEP_WORKERS`, default 4, ceiling documented ~6): `ProcessPoolExecutor` with the `spawn`
+   context; **task = one dataset (all three strategies)** so peak memory is bounded to ~one parsed dataset
+   per worker; largest-first (LPT) scheduling by event count; each worker uses a throwaway temp journal DB
+   for job bookkeeping (the report never references backtest ids) and hands results back through the durable
+   sub-cache. Parallelism runs ONLY in the CLI/background job — never inside a request thread.
+6. **The setups durable scan cache** — new `setups_scan_cache.py` (same SQLite shape, env
+   `TAPEOLOGY_SETUPS_CACHE_DB` else a sibling of the bar dir); `compute_setups`' cache key becomes
+   `(config content hash, store signature)` — the content hash reused from `edge_report_cache.py`, replacing
+   the fragile `id(config)` — checked hot-slot → durable → real scan; publish failures never block serving.
+   With capability 2, the remaining cold cost is the O(n²) scan math, paid once per (store, config) content
+   ever instead of on every backend restart.
+7. **The honest not-computed UI state** — `/structure`'s Edge Report section renders the not-computed payload
+   as a distinct panel ("**Edge report not computed yet.**" — deliberately NOT the frozen
+   "No edge-report cells yet." empty-report text, which remains the warm all-empty-cache render) with a
+   **"Compute edge report" button**: POST the trigger, poll the status route with the existing
+   poll-while-active pattern, render `backtests_done / backtests_total` (+ `backtests_from_cache`) verbatim,
+   and on `done` re-fetch the report into the existing `EdgeReportBody`; a `failed` snapshot surfaces its
+   `error` verbatim. Zero client recomputation anywhere.
+
+## Non-Goals
+
+- **No research-value change of any kind** — no level/band/reaction/cell/PnL number moves; no parameter
+  re-tuning; no gate, minimum-n, split, or register change. This interlude is pure serving-cost work.
+- **No auto-compute on page load** — visiting `/structure` (or any GET) never starts the sweep; compute is
+  operator-run only (button or CLI). No scheduled/ambient compute either.
+- **No engine hot-loop rewrites** — the TapeEngine replay path and its throughput are untouched; the win
+  comes from removing redundant recomputation, not from micro-optimizing frozen code.
+- **No new Config fields** (the fingerprint is frozen) and **no new runtime dependencies** — stdlib only
+  (`sqlite3`, `concurrent.futures`, `multiprocessing`).
+- **No new nav entries or pages** — the interlude lives inside the existing `/structure` Edge Report section.
+- **No MCP write surface** — MCP tools stay byte-identical read-only GET proxies; the compute trigger is
+  REST-only.
+- **No recording, no new data, no credential work** — the corpus is what era 5B recorded; W1 top-ups remain a
+  separate workstream.
+- **No editing of archived eras' artifacts** — `docs/goal-archive/`, the era-5B journey scripts under
+  `runs/goal-session-tradable_wall/`, and `reports/goal-session-*-delivered.md` are read-only history.
+
+## Constraints
+
+- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm), `lightweight-charts`,
+  dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`, frontend
+  `http://localhost:3000`. No new runtime dependency.
+- **Fingerprint discipline:** `config_fingerprint` stays `4d665603569b9dbf`; all new knobs/paths are env vars
+  with derived sibling defaults (`TAPEOLOGY_DATASET_INDEX_DB`, `TAPEOLOGY_SETUPS_CACHE_DB`,
+  `TAPEOLOGY_EDGE_SWEEP_CACHE_DB`, `TAPEOLOGY_EDGE_SWEEP_WORKERS`) — the `get_bar_index` /
+  `get_edge_report_cache` resolution pattern, dependency-injectable and hermetic in tests.
+- **Byte-identity discipline:** every persisted cache value (edge report, sub-results, dataset metadata, scan
+  results) is stored `json.dumps` **WITHOUT `sort_keys`** so a durable-cache-served response is byte-identical
+  to a fresh compute's response (the existing `EdgeReportCache._insert` rule; REST↔MCP raw-byte proxy tests
+  enforce it). Determinism/equivalence tests accompany every accelerator.
+- **Verification trust boundary:** stat-keyed caches serve only content that WAS fully verified, keyed by
+  `(path, size, mtime_ns)`, with the ~2s racy-write guard and integrity-errors-never-cached; any stat change
+  re-verifies fully; `DatasetStore.load_events()`/`replay()` (the paths that feed research values) verify
+  fully on EVERY load, cache or no cache. Store docstrings are updated to state exactly this ("re-verified on
+  every content change"), and tests pin both sides of the boundary.
+- **Source-introspection guard tests (existing; the dev agent MUST respect them, never edit them):**
+  `tests/test_backtests.py:1500-1508` forbids the level-internal substrings (`_swing_pivots`,
+  `_prior_period_extremes`, `_cluster_levels`, `_grade_zone`) anywhere in `backtests.py` — hence the
+  change-point helper lives in `levels.py` and the memo methods are named `levels_at`/`tradability_at`;
+  `tests/test_backtests.py:932-943` requires `compute_tradability(` present and `compute_levels(` absent in
+  the map-arm source; `tests/test_setups.py:995-1017` requires exactly ONE `_SCAN_CACHE = (key, result)`
+  rebind; `tests/test_setups.py:758-771` forbids the substring "dataset" inside the scan functions;
+  `tests/test_edge_report_api.py:114-141` pins the route's `Depends` set and the literal `cache=cache` kwarg.
+- **Concurrency discipline:** in-process caches publish complete immutable tuples atomically
+  (read-local-reference-before-inspect — the iter-6 `_SCAN_CACHE` hardening); durable writes are single
+  atomic transactions over short-lived connections (WAL + busy_timeout — the `JournalStore._read_conn`
+  precedent); the compute manager is single-flight; a concurrent miss only ever costs a redundant,
+  harmless, byte-identical recompute.
+- **Test discipline:** the default suite stays hermetic and keyless — committed fixtures only; no test
+  deleted or weakened; counting-spy tests prove zero re-reads; tamper tests prove detection survives the
+  caches; the real-corpus timings and the full real compute are operator-run verifications, never CI gates.
+- **UI read discipline:** `/structure` renders endpoint values verbatim — the not-computed `detail`, the
+  progress counts, the report cells, and the register string are all server-owned; zero client recomputation.
+
+## Design Direction
+
+Unchanged from eras 4–5B: dark-only, dense, professional, terminal-grade; honest empty/degraded states are
+first-class UI. The not-computed panel and compute progress reuse the existing panel/empty-state/poll
+patterns — no new visual language.
+
+## Product Shape
+
+Nav (top bar) is unchanged: **Cockpit `/` · Journal `/journal` (+ `/journal/[id]`) · Studies `/studies` ·
+Performance `/performance` · Structure `/structure`**. Inside `/structure`, the existing **Tradable Map ·
+Case Studies · Edge Report** sections are unchanged except the Edge Report section, which gains the honest
+not-computed state, the "Compute edge report" button, and the progress line.
+
+**Data Contract (canonical values):** additions, each with exactly one owner:
+
+- **The not-computed edge-report payload** (`status: "not_computed"`, `detail`, `dataset_count`, `register`
+  read from the backtests register constant, embedded `compute` snapshot or `null`) — owned by
+  `research/edge_report.py` (`peek_strategy_comparison_report`); read via the EXISTING
+  `GET /research/edge-report` (the `status` key is the discriminator; a real report never carries one). The
+  MCP `edge_report` proxy mirrors whichever payload the route serves, byte-identically, unchanged.
+- **The compute-job snapshot** (state, progress counts, error) — owned by `research/edge_report_compute.py`;
+  read via `GET /research/edge-report/compute`; started/cancelled via the two POST routes. Job state is
+  process-scoped bookkeeping (honestly lost on restart, like the existing job managers) — never a research
+  value.
+- **Rebuildable accelerators (explicitly NOT canonical values; deleting any loses nothing):** the two
+  in-process verified-content store caches; `dataset_index.db`; `setups_scan_cache.db`;
+  `edge_report_backtests.db` (the per-pair sub-results); and the existing `edge_report_cache.db`. Owners
+  remain the stores/computers they accelerate; every one recomputes byte-identically on loss.
+- Everything else — bands, events, cells, ledger, registries, datasets, bars, levels — unchanged existing
+  owners.
+
+## Must-have user journeys
+
+Journeys **J-01 – J-07** open the interlude. **Frontend is present** (J-01, J-04, J-06 are
+browser-verifiable). The default suite and CI stay keyless on committed fixtures; the real-corpus timings and
+the first full real compute are operator-run verifications tagged *(operator-verified on the real corpus)* —
+honestly reported blocked/absent when the corpus isn't present, never simulated. Natural dependency order:
+J-01 → J-02 → J-03 → J-04 → J-05, with J-06 riding on J-02's durable index and **J-07 guarding
+continuously.** The foundation (eras 1–5B) MUST NOT regress.
+
+- **J-01: Stop the bleeding — `GET /research/edge-report` never computes**
+  - Steps:
+    1. Add `EdgeReportCache.lookup(records, config)` (derive the existing key; check the hot slot then the
+       durable row; NEVER compute) and `EdgeReportCache.compute_and_publish(dataset_store, config,
+       compute_fn)` (always recompute + republish — the operator/`force` path) beside the untouched
+       `get_or_compute`; extract the DB-path policy (`TAPEOLOGY_EDGE_REPORT_CACHE_DB` env else
+       dataset-dir sibling) into one shared resolver used by the route and (later) the CLI.
+    2. Add `edge_report.peek_strategy_comparison_report(store, dataset_store, bar_store, config, *, cache)`:
+       store-integrity errors raise `EdgeReportError` exactly as today (the route keeps its explicit 500);
+       a warm key returns the cached report **verbatim**; an **empty dataset registry computes inline**
+       (O(1), zero backtests — the existing empty-registry response shape and its MCP byte-identity stay
+       untouched); a cold key returns the honest not-computed payload — `status: "not_computed"`, a
+       `detail` naming the trigger, `dataset_count`, the register string read from the backtests register
+       constant, and the current compute snapshot (or `null`). Rewire `GET /research/edge-report` to call it
+       (same dependency seams, the literal `cache=cache` kwarg preserved).
+    3. On `/structure`, render the not-computed payload as a distinct panel — headline
+       "**Edge report not computed yet.**", the server `detail` verbatim — leaving the frozen warm-cache
+       texts ("No edge-report cells yet.", the register line) byte-identical and reachable.
+  - Acceptance: on a cold cache with a non-empty registry, `GET /research/edge-report` returns the
+    not-computed payload within an interactive budget and a compute-spy proves **zero** sweep/backtest
+    invocations from the GET path; on a warm cache the response is **byte-identical** to a fresh
+    cache-cleared compute of the same store (determinism test); on an empty registry the response keeps
+    today's full report shape; REST and the MCP `edge_report` proxy agree byte-for-byte in every state; the
+    warm scoped-fixture cache still renders "No edge-report cells yet." verbatim in the browser; no journey
+    or test is served by computing inside a GET. *(Keyless; browser-verifiable.)*
+
+- **J-02: The stores stop re-reading — verified-content caches + the durable dataset index**
+  - Steps:
+    1. `bars.py`: add the module-level stat-keyed verified-record cache (key `(path, st_size, st_mtime_ns)`;
+       hit = zero I/O; miss = the full existing `_load` verifier; integrity errors never cached; the ~2s
+       racy-write guard; atomic tuple publish) and route `get`/`list`/`load_bars` through it — `get`/`list`
+       serving per-row copies, `load_bars` building fresh `RawBar`s from cached rows. Add a public
+       `BarStore.root` property and a test-only cache-reset helper (+ autouse conftest reset).
+    2. `datasets.py`: the same cache for **metadata only**, used ONLY by `get()`/`list()`;
+       `load_events()`/`replay()` keep full verification on every load. Update both stores' docstrings to
+       the honest new contract: "re-verified on every content change (stat-keyed)".
+    3. Add `dataset_index.py` — a durable sibling SQLite metadata index (`dataset_index(path PRIMARY KEY,
+       size, mtime_ns, meta_json, created_utc)`, meta JSON stored without `sort_keys`, `bar_index.py`'s
+       rebuildable-derived-value shape); `DatasetStore` gains keyword-only `index_db_path=None` (default =
+       today's behavior); the route dependency injects `TAPEOLOGY_DATASET_INDEX_DB` else the
+       `.data/dataset_index.db` sibling.
+  - Acceptance: counting-spy tests prove a second `list()` performs **zero file reads** on both stores while
+    content is unchanged, and that a tampered file is still detected (explicit integrity error) after a warm
+    read once its stat changes; a freshly-written file inside the racy window is never served from cache;
+    served bar rows are copies (a caller mutation never leaks back); cache-hit responses are byte-identical
+    to cleared-cache responses (REST and MCP); `load_events`/`replay` fully verify even when the metadata
+    cache is warm (spy test pins the trust boundary); a fresh `DatasetStore` (simulated restart) serves
+    `list()` metadata from the durable index with zero content re-reads, and deleting the index DB merely
+    costs one re-verify pass; `GET /research/datasets` on the real corpus drops from the measured 31.4s to
+    sub-second warm *(operator-verified on the real corpus)*. *(Keyless; automated.)*
+
+- **J-03: The arm memo — per-tick levels recompute becomes ~100 memo hits per session**
+  - Steps:
+    1. `levels.py`: add `level_change_points(store, symbol) -> tuple[float, ...]` — the sorted, deduped
+       union of every healthy series' bar epochs for the symbol plus, for each prior-period-timeframe bar,
+       its `epoch + period_seconds` close instant; document the contract: between two consecutive change
+       points, `compute_levels` is a constant function of `as_of` (a SUPERSET of change points is always
+       safe; a subset never is).
+    2. `tradability.py`: add `basis_day_key(as_of_epoch) -> str` — the UTC session date key, citing the
+       basis resolution's per-date constancy.
+    3. `backtests.py`: add the small per-run `_StructureArmMemo` (`levels_at(as_of)` keyed by
+       `bisect_right(change_points, as_of)`; `tradability_at(as_of)` keyed by the day key; a miss calls the
+       one canonical owner function); build one memo per `structure_tape` / `structure_tape_map` run and
+       thread it into the arming checks as an optional keyword (`memo=None` preserves today's direct-call
+       behavior for existing tests), keeping the literal `compute_tradability(` / `compute_levels(` owner
+       calls in the fallback branch and introducing NO forbidden level-internal names (the guard tests pin
+       both).
+  - Acceptance: memoized `structure_tape` and `structure_tape_map` backtests are **byte-identical** to
+    fresh unmemoized runs on the committed fixtures (sorted-dump equality — the J-08 determinism-test
+    discipline), including a fixture where a daily period closes between bar epochs and one spanning a UTC
+    date boundary (both memo-bust legs proven); a counting spy proves `compute_levels` is called once per
+    change interval instead of per confirming tick; the committed tick-fixture structure backtests complete
+    within an interactive test budget; every existing pinned-value backtest test passes unmodified; the
+    source-introspection guard tests pass unmodified. *(Keyless; automated.)*
+
+- **J-04: The operator-run compute — button, background job, CLI warmer**
+  - Steps:
+    1. Add `edge_report_compute.py`: `EdgeReportComputeManager` — registry-scoped (the existing job-manager
+       home), **single-flight** (a trigger while one is in flight returns the running snapshot,
+       `started: false`), cooperative cancel between backtests, and an atomically-republished progress
+       snapshot (`state`, `backtests_total/done/from_cache`, `current`, `error`). Thread additive
+       keyword-only hooks through the ONE computer (`run_strategy_comparison_report(..., force=, progress=,
+       should_abort=, sub_cache=, workers=)` — every default reproduces today's byte-identical behavior); a
+       cancelled or failed sweep caches nothing (publish only after the compute function returns).
+    2. Add the routes: `POST /research/edge-report/compute` (body `{"force": bool=false}`),
+       `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel` (409 when idle) —
... [diff_bound] docs/goal-archive/goal-2026-07-17.md: 159 more diff lines omitted — Read the file for full detail
diff --git a/docs/goal.md b/docs/goal.md
index 39ce222..2069595 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1,492 +1,655 @@
-# Tapeology — Project Goal (Interlude: The Fast Wall — /structure at interactive speed & the operator-run edge report)
-
-> Eras 1–5B are the **foundation** of this goal and MUST NOT regress. Eras 1–2 (tape reading + the research
-> evolution, J-01 – J-68, GOAL_ACHIEVED) are archived at
-> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md); the structure-UI interlude at
-> [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md); **Era 5 "The Library"** at
-> [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md). Era 3 (the profit-research
-> measurement machine), Era 4 (the structure-and-tape evolution), and **Era 5B "The Tradable Wall"
-> (GOAL_ACHIEVED 2026-07-16, session `tradable_wall`, J-01 – J-08)** are frozen foundation; their records live
-> in git history and in `reports/goal-session-tape_to_profit-delivered.md`,
-> `reports/goal-session-tape_to_profit_support_resistence-delivered.md`, and
-> `reports/goal-session-tradable_wall-delivered.md`.
+# Tapeology — Project Goal (Interlude: The Clean Slate — demolishing the journal-era surfaces)
+
+> Eras 1–5C are the **foundation** of this goal. Eras 1–2 (tape reading + the research evolution, J-01 – J-68,
+> GOAL_ACHIEVED) are archived at [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md);
+> the structure-UI interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
+> **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
+> **the "Fast Wall" performance interlude (GOAL_ACHIEVED 2026-07-17, session `fast_wall`, J-01 – J-07)** at
+> [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md). Era 3 (the profit-research
+> measurement machine), Era 4 (the structure-and-tape evolution), and Era 5B "The Tradable Wall" are frozen
+> foundation; their records live in git history and in `reports/goal-session-*-delivered.md`
+> (`tape_to_profit`, `tape_to_profit_support_resistence`, `tradable_wall`, `yahoo_fetch`, `fast_wall`).
 >
-> **This chapter is an operator-directed performance interlude, not one of the numbered research eras** (the
-> [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md) UI interlude is the precedent). It
-> adds **no research finding and changes no research value** — every number the product serves stays
-> byte-identical. It is *enabling work* for the router
-> ([`docs/research-directions.md`](research-directions.md) Part 5.1): era 6 "Referee" needs the three-way edge
-> report as its input, and that report has **never once completed** on the real corpus — the compute cost
-> era 5B honestly documented is, measured, ~99% redundant recomputation. This interlude removes the waste,
-> makes the sweep an explicit resumable operator act, and makes `/structure` load at interactive speed.
+> **This chapter is an operator-directed DEMOLITION interlude, not one of the numbered research eras** (the
+> 2026-07-07 UI interlude and the 2026-07-17 performance interlude are the precedents). On 2026-07-23 the
+> operator judged the era-1/2 journal-era product surfaces — the manual thesis journal, the replay studies,
+> and the performance/analytics page, with their hints/stance/verdict/grades machinery — **not useful for
+> digging the edge**, and directed their FULL REMOVAL (not hiding) ahead of the next chapters (an automated
+> screening/decision "Desk" era and an AI pattern-annotation era, designed separately). This interlude adds
+> **no research finding and no new capability**: it deletes product surfaces wholesale, keeps every retained
+> research value byte-identical, and carries exactly ONE sanctioned side effect — the `config_fingerprint`
+> **Path B epoch bump** ([`docs/research-directions.md`](research-directions.md) §0.4) that deleting the
+> journal-era `Config` fields forces.
+>
+> **This goal.md is deliberately over-specified.** It was authored with the strongest available model
+> against the repo at `main @ fa76460` (2026-07-23), with every deletion-boundary claim verified by grep
+> before being written down. The **Demolition inventory** (I-1 … I-9) and **Weak-model traps** (T-1 … T-14)
+> sections below are the executable ground truth for every iteration. When ANY in-era finding contradicts
+> an inventory row, STOP and surface it in the iteration report — never improvise a bigger deletion.
 
 ## Vision
 
-Era 5B filled `.data/` with real ticks (18 registered datasets, 882MB) and shipped the three-way edge report —
-and exposed the next honest problem: **the product cannot serve its own evidence**. Measured on the real
-corpus (2026-07-16, 16-core operator machine):
-
-- Opening `/structure` fires `GET /research/edge-report`; with the result cache empty (0 rows — the real
-  compute has never finished) the route **synchronously starts the full backtest sweep inside the page's own
-  request**, with no single-flight guard — every page load piles on another sweep. Observed: the backend
-  worker pinned at 98% CPU for hours after a single page visit, degrading every other endpoint through the
-  GIL, while the Edge Report section spins forever.
-- `GET /research/datasets` takes **31.4s to return 8.6KB of metadata**, because `DatasetStore.list()`
-  re-reads, re-parses, and double-sha256s all 882MB on every call (~30MB/s measured).
-- `GET /research/setups` takes **minutes** when cold: ~456 `compute_tradability` calls, each re-reading and
-  re-hashing all 47 bar files — **~17GB of cumulative re-read observed** for one request — plus O(n²) pivot
-  math; its only cache is one in-process slot wiped by every dev-server reload.
-- The sweep's documented "~10+h" is not real work. Raw engine replay runs at **12,829 events/s** (the whole
-  ~9.1M-event corpus ≈ 12 min per strategy); a `v1` backtest of a 14,241-event dataset takes **1.37s** — but
-  `structure_tape` on the SAME dataset could not finish in 9.3 minutes (**≥400×**), because the arming check
-  re-runs the FULL levels pipeline (including a whole-bar-store re-read + re-hash) **per confirming tick**.
-  Yet levels are a pure function of the as-of bar prefix, which changes only when a bar closes (~100 distinct
-  states per session), and the tradable map's basis is constant per UTC session date.
-
-This interlude makes the wall fast without moving a single brick:
-
-1. **`/structure` never computes** — `GET /research/edge-report` answers instantly from the durable cache or
-   with an honest "not computed" state; the sweep runs only as an explicit operator act.
-2. **The stores stop re-reading** — verified-content caches (stat-keyed, tamper-safe, rebuildable) end the
-   882MB-per-call and 17GB-per-scan festivals; restarts stop re-paying minutes.
-3. **The sweep stops wasting** — a per-run memo serves the arming checks from the ~100 real level states per
-   session instead of recomputing per tick, byte-identically.
-4. **The compute becomes an operator act** — a single-flight, cancellable, progress-reporting background job
-   (UI button + CLI warmer), **resumable** (durable per-dataset×strategy sub-results) and **parallel**
-   (process pool), so the first-ever completed real edge report costs minutes, not "never" — and a future
-   dataset costs only its own three backtests.
-
-Every accelerator is a **rebuildable derived value, never a source of truth**: deleting any of them loses
-nothing and fabricates nothing, and equivalence tests prove the accelerated outputs byte-identical to fresh
-computes. The measured baselines above are this interlude's ground truth; the deliverable is the same product,
-served at the speed its own honesty deserves.
+The product today carries five pages; the operator uses two. `/journal` (271 lines), `/studies` (171), and
+`/performance` (334) — plus their backend: 15 journal-era routes (`/research/journal*`, `/research/thesis*`,
+`/research/hints*`, `/research/studies*`, `/research/analytics`), eleven research modules (`journal_rows`,
+`monitor`, `hints`, `stance`, `verdict`, `grades`, `marks`, `excursions`, `execution_checks`, `analytics`,
+`studies`), three MCP tools (`journal`, `analytics`, `studies`) plus the thesis/study half of a fourth
+(`taxonomy` — SLIMMED, not deleted: its feed-basis labels feed the KEPT provenance badge), two WebSocket
+frame keys (`thesis`, `hint`), and the cockpit's thesis strip / hint dock / sound cue — all exist to serve
+a manual journaling workflow the operator has concluded does not help find the edge. Dead weight is not
+neutral: every era pays to keep these surfaces green (sentinels, goldens, regression passes), every new
+agent reads them, and the coming Desk era would have to route around them.
+
+This interlude removes them **completely and honestly**:
+
+1. **Deletion, not hiding.** Pages, routes, modules, components, WS keys, MCP tools, nav rows, types, and
+   their tests are gone from the codebase — grep-provably, with no orphaned imports or dead links.
+2. **The kept product is untouched in value.** Cockpit (`/`) and Structure (`/structure`) — the live/sim/
+   historical tape, **both charts** (`StructureChart` + the cockpit `PriceChart` container — kept in full
+   by explicit operator directive), the bar library, levels/zones, the tradable map, case studies, the
+   edge report, the strategy registry, the champion pointer, and the PnL promotion ledger — keep serving
+   **byte-identical numbers on identical inputs**. (`pnl_ledger.py` is the promotion honesty ledger, NOT
+   the performance page — it stays, MCP tool and all.)
+3. **Shared code moves before its home is demolished.** `marks.r_basis` (the R-multiple basis the backtest
+   runner reads) and `studies.py`'s dataset-source constants + reference-window loader (which `datasets.py`,
+   `backtests.py`, and `pnl_baseline.py` import) are relocated byte-identically into kept modules FIRST.
+4. **The fingerprint moves once, lawfully.** Deleting the journal-era `Config` fields (verdict classifier
+   thresholds among them — fingerprint-included by design) moves `config_fingerprint` off the founding
+   `4d665603569b9dbf`. That bump is executed as its own journey, exactly per §0.4 Path B: documented here,
+   pinned literal updated at all **13 verified pin sites** (I-9), founding baseline re-seeded under the new
+   epoch, ledger row appended, sentinel asserting the new pin. Cross-epoch pooling is forbidden forever.
+
+The deliverable is a leaner instrument — **Cockpit + Structure, nothing else** — with the honesty machinery
+(stores, gates, registry, ledger, read-only MCP) fully intact, ready for the Desk chapter to build on
+cleared ground.
 
 ## Target Users
 
-- The project owner (a discretionary intraday trader) whose `/structure` page currently hangs for minutes and
-  whose machine burns hours of CPU per page visit — and who has never yet been able to SEE the real-corpus
-  edge report era 5B built.
-- AI dev-chain agents (the goal-mode chain) building and browser-verifying the fast path, the honest
-  not-computed state, and the operator-run compute.
+- The project owner (a discretionary intraday trader) who wants the product reduced to the surfaces that
+  actually serve edge-digging, ahead of an automated screening/decision Desk operated through Claude + MCP.
+- AI dev-chain agents (the goal-mode chain) executing and browser-verifying a large, precise deletion
+  without touching a single research value.
 
-## Foundation invariants (still law — eras 1–5B)
+## Foundation invariants (still law — eras 1–5C, minus the demolished surfaces)
 
-The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md)), the
-era-3 measurement machine, the era-4 structure stack, the era-5 keyless bar library, and the era-5B tradable
-wall remain binding verbatim on ALL new code: price-impact-over-aggression; honest uncertainty; **no
-fabricated data**; single source of truth; no magic numbers; provider-agnostic engine; deterministic &
-reproducible; no secrets in source; research read-only over the engine; journal/record integrity;
-source/feed/`config_fingerprint` honesty; the existing surfaces (`/`, `/journal`, `/journal/[id]`, `/studies`,
-`/performance`, `/structure`) stay intact.
+The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md)) remains
+binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no fabricated data**; single
+source of truth; no magic numbers; provider-agnostic engine; deterministic & reproducible; no secrets in
+source; research read-only over the engine; record integrity; source/feed/`config_fingerprint` honesty —
+**except its surface inventory**: this interlude, by explicit operator direction, removes `/journal`,
+`/journal/[id]`, `/studies`, and `/performance` from that inventory. The KEPT surfaces (`/`, `/structure`)
+stay intact.
 
 In addition, these stay **frozen foundation**:
 
-1. The **tape engine** emits its five states byte-identically under `default`; `config_fingerprint` stays
-   `4d665603569b9dbf` (equivalence-tested). **This interlude adds ZERO `Config` fields** — every new
-   operational knob is an env var + derived sibling path (the `bar_index` / `TAPEOLOGY_BAR_INDEX_DB`
-   precedent), so the fingerprint cannot move.
-2. The **research computations** — `levels.py` (raw levels + A/B/C zones and its parameters),
-   `tradability.py` (the ≤10-band map), `setups.py` (the scan + reactions + forward returns),
-   `edge_report.py` (the three-way cells, gates, null baseline, register), the strategy registry
-   (`v1` + `structure_tape` + `structure_tape_map`), the class-scaled math, and the backtest runner's
-   simulated trades — stay **behaviorally byte-identical: identical inputs keep producing identical
-   outputs.** This interlude changes only *when and how often* they are computed, never *what* they compute.
-3. The **stores** — the JSON `BarStore` and `DatasetStore` file formats, checksums, append-only immutability,
-   and split freezing — are untouched on disk; the verification discipline (a corrupt or tampered file is an
-   explicit error, never silently served) is preserved at every read that loads content.
-4. **`v1`, `default`, `structure_tape`, `structure_tape_map`, and the champion pointer are frozen.** The
-   champion moves only through the existing sweep gate on hold-out data; nothing here promotes.
-5. The **era-5B UI surfaces** — `/structure`'s Tradable Map / Case Studies / Edge Report sections, the raw
-   toggle, the era-5 fetch control + provenance badge, and the cockpit band overlay + confluence chip — keep
-   working exactly as shipped, including the frozen warm-cache texts ("No edge-report cells yet.", the
-   "simulated — assumed fees/slippage — not indicative of live results" register).
-6. The **existing rebuildable accelerators** — the derived `bar_index`, the J-08 `EdgeReportCache`, and the
-   setups `_SCAN_CACHE` discipline — keep their contracts (rebuildable, never a source of truth, loss loses
-   nothing); this interlude extends the same discipline, it never weakens it.
+1. The **tape engine** (`app/engine/` — five states, thresholds, features, history, observations) emits
+   byte-identical output under `default` on identical inputs. `config_fingerprint` stays `4d665603569b9dbf`
+   through J-01 – J-03 and moves EXACTLY ONCE, in J-04, via the §0.4 Path B protocol — never any other way.
+2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan cache),
+   `edge_report*.py` (report, caches, compute manager, CLI), `backtests.py`, the strategy registry
+   (`v1` + `structure_tape` + `structure_tape_map`), `profiles.py` (`default`), and the champion pointer —
+   stay behaviorally byte-identical: identical inputs keep producing identical outputs (only the
+   `config_fingerprint` STAMP inside newly-computed payloads changes after J-04).
+3. The **stores** — the JSON `BarStore` + `DatasetStore` formats, checksums, append-only immutability, split
+   freezing, the durable accelerator DBs (`bar_index`, `dataset_index`, edge-report caches, setups scan
+   cache, tradability cache) — are untouched in format and discipline. Registered datasets and bar series
+   are never deleted, re-tagged, or content-perturbed.
+4. The **PnL promotion ledger** (`pnl_ledger.py`, `reports/pnl/pnl-history.md`, the MCP `pnl_ledger` tool)
+   stays append-only and intact — existing rows keep their original fingerprint stamps forever.
+5. The **era-5B/5C `/structure` surfaces** — Tradable Map / Case Studies / Edge Report sections, the raw
+   toggle, the fetch control + provenance badge, the Compute button + progress poll, the frozen warm-cache
+   texts — and **both charts** — `StructureChart.tsx` (the ONE shared renderer for `/structure` and the
+   cockpit) and `PriceChart.tsx` (the cockpit chart container: historical candles, timeframe switching,
+   viewport paging, S/R band overlay, live tape moving bars) — keep working exactly as shipped. **The
+   charts are kept in full (explicit operator directive, 2026-07-23); a chart regression is veto-class.**
+6. The **read-only MCP server** (`app/mcp/`) keeps its byte-identical GET-proxy contract; this interlude
+   removes three tools and slims one payload (`taxonomy`), never adds writes.
 
 ## Success Criteria
 
-In priority order — honesty and non-regression outrank speed:
-
-1. **Nothing existing regresses.** Full backend suite green (no test deleted or weakened), engine equivalence
-   proves byte-identical `default` outputs, `config_fingerprint` stays `4d665603569b9dbf`, every era-1–5B
-   surface behaves exactly as shipped, and the warm-cache Edge Report render (cells or the honest
-   "No edge-report cells yet." empty state, register visible) is byte-equal to before.
-2. **`/structure` never triggers compute.** `GET /research/edge-report` answers within an interactive budget
-   in every state — a warm cache serves the report verbatim; a cold cache returns an honest, explicit
-   "not computed" payload and **starts nothing**. Opening the page never costs the machine hours (or even
-   seconds) of sweep CPU.
-3. **The heavy reads answer at interactive speed when content is unchanged.** With stores unchanged since the
-   last verified read, `GET /research/datasets` and `GET /research/setups` serve from verified-content caches
-   without re-reading the corpus (proven by zero-re-read spy tests keyless; observed sub-second on the real
-   corpus by the operator), and a backend restart no longer re-pays the 31.4s / minutes cold costs (durable
-   accelerators).
-4. **The first full real edge report completes — as one resumable operator act.** The sweep runs only via the
-   explicit trigger (UI button or CLI warmer): single-flight, cancellable, progress-visible, **resumable**
-   (a killed run re-computes only missing dataset×strategy pairs) and **parallel** (process pool; expected
-   ~10–20 min on the operator's 16-core machine vs never-completing today). Once computed it serves instantly
-   from the durable cache, and the completed three-way comparison is appended to
-   `reports/pnl/pnl-history.md` — closing era-5B J-08's still-outstanding step 3.
-5. **Every accelerator is rebuildable and proven byte-identical.** Deleting any cache/index DB loses nothing
-   (the next read re-verifies/recomputes); determinism and equivalence tests prove cached/memoized/parallel
-   outputs byte-identical to fresh sequential computes; a tampered store file is still detected on every
-   content change.
+In priority order — kept-value integrity outranks deletion completeness outranks speed of execution:
+
+1. **Nothing kept regresses.** Full backend suite green; engine equivalence proves byte-identical `default`
+   outputs; every kept `/` and `/structure` behavior works exactly as shipped (browser-verified, both
+   charts included); kept research values (levels, bands, touch events, edge cells, ledger rows)
+   byte-identical on identical inputs; `test_no_execution_path.py` and every kept guard test pass
+   unmodified.
+2. **The demolition is total.** `/journal`, `/journal/[id]`, `/studies`, `/performance` render the app's
+   404; the 15 journal-era routes return 404; nav shows exactly **Cockpit · Structure**; the WS frame
+   carries no `thesis`/`hint` keys; the MCP tool list is exactly the **15 kept tools** (I-6); a repo-wide
+   grep finds no live import of, reference to, or dead test for any deleted module/component (historical
+   `reports/**`, `runs/**`, and `docs/goal-archive/**` excepted — they are read-only history).
+3. **The epoch bump is lawful and complete.** Executed only in J-04, exactly per §0.4 Path B: the new pin
+   literal asserted at all 13 verified pin sites (I-9); the founding baseline re-seeded (`python -m
+   app.research.pnl_baseline`) appending the new-epoch founding row beside the old rows; the epoch change
+   documented on the ledger; no cross-epoch numbers pooled anywhere; no OTHER commit ever touches a pin.
+4. **Relocations are proven moves.** `r_basis` and the dataset-source constants/loader behave byte-
+   identically from their new homes; every kept caller's outputs are unchanged (existing kept tests pass
+   unmodified).
+5. **History stays readable.** journal.db's existing rows and tables remain (dormant — writers/readers
+   deleted, migrations untouched), the PnL ledger keeps all rows, and archived-era artifacts are not
+   edited.
 
 ## Key Capabilities
 
-Layered strictly on top of the era-1–5B capabilities, which remain unchanged.
-
-1. **Cache-or-honest-absence GET** — `EdgeReportCache` gains `lookup(records, config)` (serve the current
-   key's row, hot-slot then durable, never computing) and `compute_and_publish(...)` (the always-recompute
-   operator path); `edge_report.py` gains `peek_strategy_comparison_report(...)`: store-integrity errors keep
-   raising `EdgeReportError` (the route's explicit 500); a warm key serves the report **verbatim**; an
-   **empty dataset registry still computes inline** (O(1) — zero backtests — preserving the existing
-   empty-registry response shape and MCP byte-identity); a cold key returns the honest not-computed payload.
-   The route swaps one call; the payload's `register` field is read from `backtests.REGISTER`, never a
-   restated literal. Path policy for the cache DB is extracted to one shared resolver
-   (`TAPEOLOGY_EDGE_REPORT_CACHE_DB` env else sibling of the dataset dir — exactly today's rule).
-2. **Verified-content store caches** — `bars.py` and `datasets.py` gain module-level stat-keyed caches of
-   VERIFIED loads: key `(absolute path, st_size, st_mtime_ns)`; a stat match serves the already-verified
-   record with zero I/O; ANY mismatch re-runs the full existing verifier (both checksums); integrity errors
-   are never cached; a ~2s "racy write" guard refuses to cache freshly-written files (same-granularity
-   rewrites can never be served stale); atomic single-slot publish (the `_SCAN_CACHE` read-local-ref
-   discipline). `BarStore` caches meta + rows (6.5MB total; `get`/`list` serve per-row copies so a caller
-   mutation can never poison the cache; `load_bars` builds fresh `RawBar`s). `DatasetStore` caches
-   **metadata ONLY** (882MB of rows never live in RAM) and only for `get()`/`list()` — **`load_events()` and
-   `replay()` keep full verification on every load** (the trust boundary, pinned by tests). A durable sibling
-   **dataset metadata index** (`dataset_index.db`; env `TAPEOLOGY_DATASET_INDEX_DB`; `bar_index.py`'s
-   "derived, rebuildable, owns nothing" shape; meta JSON stored WITHOUT `sort_keys`) makes restarts stop
-   re-paying the 882MB parse.
-3. **The arm memo** — `levels.py` gains `level_change_points(store, symbol)` (the sorted union of every
-   healthy series' bar epochs for the symbol plus each prior-period bar's `epoch + period_seconds` close
-   instant — a conservative superset; between two consecutive change points `compute_levels` is a constant
-   function of `as_of`); `tradability.py` gains `basis_day_key(as_of_epoch)` (its basis resolution is
-   constant per UTC session date). `backtests.py` gains a small per-run `_StructureArmMemo` with
-   `levels_at(as_of)` / `tradability_at(as_of)` (keyed by change-point interval / day key; a miss calls the
-   one canonical owner), built once per `structure_tape` / `structure_tape_map` run and threaded into the
-   arming checks as an optional keyword — collapsing thousands of per-tick recomputes into the ~100 real
-   level states per session, byte-identically.
-4. **The operator-run compute** — new `edge_report_compute.py`: `EdgeReportComputeManager` (registry-scoped
-   like the existing job managers; single-flight; cooperative cancel; an atomic progress snapshot:
-   `{id, state, force, started_utc, finished_utc, error, progress: {phase, backtests_total, backtests_done,
-   backtests_from_cache, current}}`), driving the ONE computer `run_strategy_comparison_report` with new
-   additive keyword-only hooks (`progress=`, `should_abort=`, `sub_cache=`, `workers=`, `force=` — all
-   defaulting to today's exact behavior). Routes: `POST /research/edge-report/compute` (idempotent
-   single-flight: a second POST returns the running snapshot with `started: false`),
-   `GET /research/edge-report/compute` (snapshot or `null`), `POST /research/edge-report/compute/cancel`
-   (409 when idle; a cancelled sweep caches no report). A CLI warmer — `python -m
-   app.research.edge_report_compute --workers N [--force] [--out report.json]` — resolves the same seams the
-   backend reads, prints per-backtest progress, is nohup-able, and survives backend restarts because it
-   writes the same durable SQLite caches the GET serves. **No new MCP tool** (MCP stays a read-only proxy
-   surface; the new GET status route is additive REST only).
-5. **The resumable + parallel sweep** — `EdgeReportBacktestCache`: one durable row per (dataset × strategy)
-   result block, keyed by `{dataset_id, dataset_checksum, strategy_id, profile, config_fingerprint,
-   config_content_hash, strategy_registry, bar_store_signature}` — the bar-store term (the sorted
-   `(symbol, timeframe, id, checksum)` tuples `setups._store_signature` already computes) is load-bearing:
-   the structure strategies read bar content per event, and the EXISTING persisted backtest journal rows are
-   NOT a safe resume source precisely because their `config_fingerprint` excludes the
-   `sr_*`/`tradability_*`/`setups_*` families and records no bar content. Values are the runner's `result`
-   blocks verbatim (stored WITHOUT `sort_keys`; the null-baseline seed is the config-owned constant, so a
-   cached block is byte-identical to a re-run by the runner's own documented contract). `_split_cells` gains
-   a `run_pair(dataset_meta, strategy_id)` provider seam (default = today's inline call; pooling and ordering
-   code untouched, so reassembly from cached blocks is byte-identical **by construction**). Each pair
-   publishes durably the moment it completes → a killed sweep resumes with only the missing pairs; a newly
-   recorded dataset costs exactly its own three backtests + reassembly. Parallel mode (CLI `--workers` / env
-   `TAPEOLOGY_EDGE_SWEEP_WORKERS`, default 4, ceiling documented ~6): `ProcessPoolExecutor` with the `spawn`
-   context; **task = one dataset (all three strategies)** so peak memory is bounded to ~one parsed dataset
-   per worker; largest-first (LPT) scheduling by event count; each worker uses a throwaway temp journal DB
-   for job bookkeeping (the report never references backtest ids) and hands results back through the durable
-   sub-cache. Parallelism runs ONLY in the CLI/background job — never inside a request thread.
-6. **The setups durable scan cache** — new `setups_scan_cache.py` (same SQLite shape, env
-   `TAPEOLOGY_SETUPS_CACHE_DB` else a sibling of the bar dir); `compute_setups`' cache key becomes
-   `(config content hash, store signature)` — the content hash reused from `edge_report_cache.py`, replacing
-   the fragile `id(config)` — checked hot-slot → durable → real scan; publish failures never block serving.
-   With capability 2, the remaining cold cost is the O(n²) scan math, paid once per (store, config) content
-   ever instead of on every backend restart.
-7. **The honest not-computed UI state** — `/structure`'s Edge Report section renders the not-computed payload
-   as a distinct panel ("**Edge report not computed yet.**" — deliberately NOT the frozen
-   "No edge-report cells yet." empty-report text, which remains the warm all-empty-cache render) with a
-   **"Compute edge report" button**: POST the trigger, poll the status route with the existing
-   poll-while-active pattern, render `backtests_done / backtests_total` (+ `backtests_from_cache`) verbatim,
-   and on `done` re-fetch the report into the existing `EdgeReportBody`; a `failed` snapshot surfaces its
-   `error` verbatim. Zero client recomputation anywhere.
+This interlude REMOVES capabilities; the "capabilities" below are the demolition's own work packages. The
+exact per-file ground truth for every package lives in the **Demolition inventory** (I-1 … I-9).
+
+1. **Byte-identical relocations (before any deletion — I-2 RELOCATE table).** Move `r_basis` from
+   `marks.py` into `backtests.py` (its sole surviving consumer; `excursions.py`, the other importer, is
+   being deleted). Move `SOURCE_REFERENCE` / `SOURCE_HISTORICAL` / `REFERENCE_SOURCE_ID` /
+   `_load_reference_window` from `studies.py` (lines 101–217) into `datasets.py`, updating the importers
+   (`datasets.py:69-70`, `backtests.py:110`, `pnl_baseline.py:41-43`) and the `edge_report.py:72` comment.
+   Pure moves — no behavior change, no renamed semantics.
+2. **Backend surface deletion (I-1, I-2, I-3).** Delete the 15 journal-era routes; delete modules
+   `journal_rows.py`, `monitor.py`, `hints.py`, `stance.py`, `verdict.py`, `grades.py`, `marks.py`,
+   `excursions.py`, `execution_checks.py`, `analytics.py`, `studies.py`; **SLIM `taxonomy.py`** (the route,
+   module, and MCP tool stay — the KEPT `FeedBasisBadge` reads its `feed_basis` block — but every
+   thesis/verdict/stance/study label family and copy block is deleted); strip `ResearchRegistry` to its
+   kept duties (store access + the backtest/edge-compute job managers) — `study_jobs`,
+   `hint_projection_for`, `on_engine_created`, and `startup_sweep` go; remove the WS `thesis`/`hint` merge
+   and the lifespan monitor wiring from `app/main.py` (I-5); delete `JournalStore`'s journal-era methods
+   and record dataclasses (I-3; tables stay dormant; the append-only migration history is NOT edited;
+   schema version stays v8).
+3. **Frontend + WS deletion (I-7).** Delete pages `apps/frontend/app/{journal,studies,performance}/`; the
+   eleven journal-era components; the 14 journal-era `lib/api.ts` functions (**`fetchTaxonomy` is NOT one
+   of them** — the badge keeps it); the thesis/hint types and WS-frame fields; the cockpit page's thesis
+   stop-flow and thesis/hint/sound rendering; the four nav rows from `app/meta.py` ROUTES. **Both chart
+   components are kept** (I-7 chart clause): `StructureChart.tsx` untouched; `PriceChart.tsx` keeps every
+   behavior except building thesis-geometry overlays from the now-deleted thesis data.
+4. **MCP contract v2 — 15 tools (I-6).** Remove tools `journal`, `analytics`, `studies` from
+   `app/mcp/__init__.py`; `taxonomy` STAYS (its payload slims because the route's payload slims — the
+   byte-identical proxy discipline is unchanged). Update `tests/test_mcp_server.py` to the 15-tool
+   contract; `get_endpoint` allowlist unchanged (deleted paths now surface the backend's honest 404 — the
+   existing unshipped-path contract).
+5. **The §0.4 Path B epoch bump (its own journey — I-4, I-9).** Delete the journal-era `Config` fields
+   (confirmed list in I-4, closure rule by grep), prune the fingerprint EXCLUSION set of deleted names in
+   the same commit, then execute Path B verbatim: update the pinned literal at all 13 verified pin sites;
+   re-seed the founding baseline; document the epoch change on the ledger; the J-05 sentinel asserts the
+   new pin. Registered dataset/bar fixtures are untouched (rail 9).
+6. **Test-suite demolition + sentinel re-baseline (I-8).** Delete the ~24 journal-era test files; UPDATE
+   the six mixed/contract files per I-8's explicit keep/drop notes (`test_copy_discipline` is a KEEPER —
+   the rail-2 language lint); keep every kept-side test unmodified (the fast_wall source-introspection
+   guards included); browser-verify the kept product end to end (both charts included).
 
 ## Non-Goals
 
-- **No research-value change of any kind** — no level/band/reaction/cell/PnL number moves; no parameter
-  re-tuning; no gate, minimum-n, split, or register change. This interlude is pure serving-cost work.
-- **No auto-compute on page load** — visiting `/structure` (or any GET) never starts the sweep; compute is
-  operator-run only (button or CLI). No scheduled/ambient compute either.
-- **No engine hot-loop rewrites** — the TapeEngine replay path and its throughput are untouched; the win
-  comes from removing redundant recomputation, not from micro-optimizing frozen code.
-- **No new Config fields** (the fingerprint is frozen) and **no new runtime dependencies** — stdlib only
-  (`sqlite3`, `concurrent.futures`, `multiprocessing`).
-- **No new nav entries or pages** — the interlude lives inside the existing `/structure` Edge Report section.
-- **No MCP write surface** — MCP tools stay byte-identical read-only GET proxies; the compute trigger is
-  REST-only.
-- **No recording, no new data, no credential work** — the corpus is what era 5B recorded; W1 top-ups remain a
-  separate workstream.
-- **No editing of archived eras' artifacts** — `docs/goal-archive/`, the era-5B journey scripts under
-  `runs/goal-session-tradable_wall/`, and `reports/goal-session-*-delivered.md` are read-only history.
+- **No new features, pages, endpoints, strategies, or Config fields.** The Desk (universe screener,
+  decision ledger, briefing) and the AI annotation corpus are the NEXT chapters — designed separately,
+  built only after this interlude closes. Nothing of them lands here.
+- **No research-value change beyond the documented epoch bump.** No level/band/reaction/cell/PnL number
+  moves; no parameter re-tuning; no gate, minimum-n, split, or register change.
+- **No engine work.** `app/engine/` is untouched; its five states, thresholds, and outputs are frozen.
+- **No chart work.** `StructureChart.tsx` and `PriceChart.tsx` are kept as shipped (minus the sourceless
+  thesis-overlay inputs) — no rewrites, no "cleanups", no renderer consolidation.
+- **No MCP write surface.** MCP stays read-only GET proxies; this interlude only removes/slims tools.
+- **No recording, no new data, no credential work, no Yahoo/universe fetching.**
... [diff_bound] docs/goal.md: 780 more diff lines omitted — Read the file for full detail
```
