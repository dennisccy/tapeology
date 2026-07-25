# Iteration diff (bounded)

Files changed: 2. Shown in full: 0.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `docs/goal-archive/goal-2026-07-25.md` (326 lines not shown)
- `docs/goal.md` (810 lines not shown)

```diff
diff --git a/docs/goal-archive/goal-2026-07-25.md b/docs/goal-archive/goal-2026-07-25.md
new file mode 100644
index 0000000..2069595
--- /dev/null
+++ b/docs/goal-archive/goal-2026-07-25.md
@@ -0,0 +1,720 @@
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
+>
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
+
+## Vision
+
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
+
+## Target Users
+
+- The project owner (a discretionary intraday trader) who wants the product reduced to the surfaces that
+  actually serve edge-digging, ahead of an automated screening/decision Desk operated through Claude + MCP.
+- AI dev-chain agents (the goal-mode chain) executing and browser-verifying a large, precise deletion
+  without touching a single research value.
+
+## Foundation invariants (still law — eras 1–5C, minus the demolished surfaces)
+
+The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md)) remains
+binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no fabricated data**; single
+source of truth; no magic numbers; provider-agnostic engine; deterministic & reproducible; no secrets in
+source; research read-only over the engine; record integrity; source/feed/`config_fingerprint` honesty —
+**except its surface inventory**: this interlude, by explicit operator direction, removes `/journal`,
+`/journal/[id]`, `/studies`, and `/performance` from that inventory. The KEPT surfaces (`/`, `/structure`)
+stay intact.
+
+In addition, these stay **frozen foundation**:
+
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
+
+## Success Criteria
+
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
+
+## Key Capabilities
+
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
+
+## Non-Goals
+
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
+- **No editing of archived history** — `docs/goal-archive/`, `runs/goal-session-*`,
+  `reports/goal-session-*-delivered.md`, `reports/phase-goal-*` artifacts, `reports/pnl/pnl-history.md`'s
+  existing rows, and journal.db's existing rows are read-only records. (Deleting CODE is this era's
+  mandate; deleting RECORDS is forbidden.)
+- **No schema surgery.** No v9 migration, no table drops, no rewriting migration history — dormant tables
+  are the honest, cheap choice.
+
+## Constraints
+
+- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm), `lightweight-charts`,
+  dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`, frontend
+  `http://localhost:3000`. No new runtime dependency.
+- **The deletion boundary is exactly the Demolition inventory (I-1 … I-9).** Anything discovered in-era
+  outside those lists is surfaced in the iteration report BEFORE being touched (trap T-14).
+- **Ordering discipline:** relocations land and prove green BEFORE their source modules are deleted
+  (J-01); the fingerprint pins are untouched until J-04; J-04 touches the pins and NOTHING else touches
+  them.
+- **Guard tests (kept, never edited):** `tests/test_no_execution_path.py`;
+  `tests/test_no_credential_in_artifacts.py`; the fast_wall source-introspection guards
+  (`tests/test_backtests.py:1500-1508` forbidden level-internal substrings,
+  `tests/test_backtests.py:932-943` map-arm source pins, `tests/test_setups.py:995-1017` single
+  `_SCAN_CACHE` rebind, `tests/test_setups.py:758-771` forbidden substring, the edge-report route
+  `Depends` pin). The ONLY sanctioned pin edit is J-04's Path B literal update at the 13 sites (I-9) —
+  the fingerprint ASSERTION LINES inside otherwise-kept test files are updated, the tests around them are
+  not weakened.
+- **WS contract change is explicit and typed:** the frame loses exactly the `thesis` and `hint` keys;
+  `lib/types.ts` + `lib/useTapeStream.ts` are updated in the same journey (J-02); no `undefined`-field
+  ghosts remain in the frontend types.
+- **Honest wording:** deleted surfaces 404 — no redirects, no "coming soon" placeholders, no tombstone
+  pages. The 404 is the app's existing not-found rendering.
+- **Test discipline:** the suite stays hermetic and keyless on committed fixtures; no kept test deleted or
+  weakened; the real-corpus behaviors (edge-report warm render, tradable map on real bars) are operator-run
+  verifications, never CI gates.
+- **Framework hygiene:** if any goal-mode framework asset (demo scripts, proposer guidance, eval fixtures)
+  references deleted surfaces, the reference is updated in the neutral source per
+  `.claude/maintenance-protocol.md` — never by editing generated mirrors.
+
+## Design Direction
+
+Unchanged: dark-only, dense, professional, terminal-grade; honest empty/degraded states are first-class.
+The demolition leaves no dead links, no empty nav slots, no unstyled 404s — the kept two-page product looks
+deliberate, not amputated.
+
+## Product Shape
+
+Nav (top bar) after this interlude: **Cockpit `/` · Structure `/structure`** — nothing else. `/journal`,
+`/journal/[id]`, `/studies`, `/performance` are gone (404). The nav is data-driven from `app/meta.py`
+ROUTES (the single owner); `GET /meta/ui-routes` and the MCP `ui_route_map` tool reflect it verbatim.
+
+**Data Contract:** every KEPT canonical value keeps its existing single owner unchanged (bands →
+`tradability.py`; touch events → `setups.py`; edge cells + not-computed payload → `edge_report.py`; compute
+snapshot → `edge_report_compute.py`; ledger rows → `pnl_ledger.py`; bars/candles → `bars.py`; levels/zones →
+`levels.py`; registry + champion → `strategies.py`/store; routes → `meta.py`). The **taxonomy labels** row
+SLIMS: `taxonomy.py` remains the single owner of research labels, but serves ONLY the families kept
+surfaces read (the `feed_basis` block the provenance badge renders, plus source labels); the
+thesis/verdict/stance/study families are removed with their owners. These rows are REMOVED entirely with
+their owners: active thesis, thesis journal + detail, verdict timeline, management stance, entry checks,
+grades, excursions, hints (active + log), study jobs/results, analytics aggregates. The WS frame = the
+engine projection ONLY (no additive research keys).
+
+## Demolition inventory — verified ground truth (2026-07-23, `main @ fa76460`)
+
+Every row below was verified by grep/read against `fa76460` before being written. **Line numbers are dated
+to that commit — always re-locate by symbol/route/decorator NAME (grep), never by line arithmetic**, since
+earlier journeys shift lines. Notation: **DELETE** = remove entirely; **SLIM** = file stays, listed parts
+removed; **RELOCATE** = move byte-identically, then delete the source; **KEEP-DANGER** = looks deletable,
+is not.
+
+### I-1 · Backend routes (`app/research/routes.py`)
+
+DELETE these 15 route handlers (decorator anchors at `fa76460`):
+
+| Route | Anchor |
+|---|---|
+| `GET /research/analytics` | `routes.py:457` |
+| `GET /research/thesis/active` | `routes.py:469` |
+| `GET /research/hints/active` | `routes.py:480` |
+| `GET /research/hints` | `routes.py:493` |
+| `GET /research/journal` | `routes.py:531` (+ helper `build_journal_detail` at 598) |
+| `GET /research/journal/{thesis_id}` | `routes.py:710` |
+| `POST /research/thesis` | `routes.py:728` |
+| `POST /research/thesis/{thesis_id}/resolve` | `routes.py:901` |
+| `POST /research/thesis/{thesis_id}/action` | `routes.py:1061` |
+| `POST /research/thesis/{thesis_id}/review` | `routes.py:1186` |
+| `POST /research/studies` | `routes.py:1300` (+ `get_study_market_adapter` at 1274) |
+| `GET /research/studies` | `routes.py:1405` |
+| `GET /research/studies/{study_id}` | `routes.py:1413` |
+| `POST /research/studies/{study_id}/cancel` | `routes.py:1424` |
+
+`GET /research/taxonomy` (`routes.py:446`) is **SLIM**: the route STAYS; its served payload shrinks to the
+kept label families (I-2 taxonomy row). Every OTHER route in the file is **KEEP**, explicitly: datasets
+(1470/1565/1574), bars (1692/1874/1934/1957), candles (2017), levels (2078), tradability (2108), setups
+(2168/2209), backtests (2240/2290/2299/2310), pnl ledger (2339), profiles (2355), strategies (2373),
+edge-report GET + compute POST/GET/cancel (2396/2441/2466/2475).
+
+### I-2 · Backend module dispositions (with reverse-import proof)
+
+**DELETE** (verified importers, all delete-side or import-lines being removed in the same journey):
+
+| Module | Verified importers at `fa76460` |
+|---|---|
+| `journal_rows.py` | `routes.py:91` |
+| `monitor.py` | `routes.py:81-87` block, `main.py` lifespan wiring (I-5) |
+| `hints.py` | `monitor.py` |
+| `stance.py` | `monitor.py`, `routes.py` |
+| `verdict.py` | `monitor.py` |
+| `grades.py` | `monitor.py`, `routes.py:79` |
+| `marks.py` (after RELOCATE) | `backtests.py:102` (moves), `excursions.py:44` (dies), `routes.py:80` |
+| `excursions.py` | `monitor.py`, `routes.py:77` |
+| `execution_checks.py` | `excursions.py`, `grades.py`, `monitor.py`, `routes.py:78`, `config.py`, `store.py` — ALL delete-side (**correction: an earlier draft wrongly listed this module as KEEP**) |
+| `analytics.py` | `routes.py:38` |
+| `studies.py` (after RELOCATE) | `datasets.py:69-70` (moves), `backtests.py:110` (moves), `pnl_baseline.py:41-43` (moves), `routes.py:93-101` |
+
+**RELOCATE** (land + prove green BEFORE deleting the source — J-01 step 1):
+
+| Symbol(s) | From | To | Importers to update |
+|---|---|---|---|
+| `r_basis` | `marks.py` | `backtests.py` (private helper, same math) | `backtests.py:102`; `excursions.py:44` dies with its module |
+| `SOURCE_REFERENCE`, `SOURCE_HISTORICAL`, `REFERENCE_SOURCE_ID`, `_load_reference_window` | `studies.py:101-217` | `datasets.py` | `datasets.py:69-70`, `backtests.py:110`, `pnl_baseline.py:41-43`; comment at `edge_report.py:72` |
+
+**SLIM**:
+
+- `taxonomy.py` — KEEP: the module, `GET /research/taxonomy`, the MCP `taxonomy` tool, and the label
+  families KEPT surfaces read — the `feed_basis` block (`FeedBasisBadge.tsx:46-60` reads
+  `taxonomy.feed_basis.feeds[].{id,name}` + the disclosure line) and the source labels
+  (`sim`/`iex`/`sip`/`yahoo`, taxonomy.py:42-45). DELETE: the verdict labels (56-61), thesis status labels
+  (71-75), `NOT_EVALUATED_NOTICE`/`not_evaluated_notice`/`mismatched_source_notice` (94-110), stance
+  labels + map + evidence copy (130-170+), `STUDY_COPY` incl. the "Replay studies" title (~646), the
+  setup-grammar/study families, and every other thesis/hint/study block. In-era rule: a label family
+  stays ONLY if a kept surface provably reads it (grep the frontend + kept routes).
+- `routes.py` — strip the delete-side imports: `from .analytics import compute_analytics` (38),
+  `excursions` (77), `execution_checks` (78), `grades` (79), `marks` (80), the `monitor` block (81-87),
+  `journal_rows` (91), the record types from `store` (92 — `ThesisRecord`/`ActionRecord`/
+  `VerdictEventRecord`; the `JournalStore` import itself STAYS), the `studies` block (93-101), the
+  taxonomy thesis-copy imports (101-103). KEEP imports right beside them: `datasets` block (65),
+  `pnl_ledger:87`, `profiles:88`, `strategies:89`, `feed_basis:90`. `ResearchRegistry` (267+) KEEPS store
+  access + the backtest/edge-compute job managers; LOSES `study_jobs` (294), `hint_projection_for` (375),
+  `on_engine_created`, `startup_sweep`.
+- `store.py`, `config.py`, `main.py` — per I-3, I-4, I-5.
+
+**KEEP-DANGER** (name-similarity traps — see T-1):
+
+- `pnl_ledger.py`, `pnl_history.py`, `pnl_scan.py`, `pnl_baseline.py` — the PROMOTION machinery, not the
+  performance page. All four stay; `pnl_baseline` is J-04's re-seeding tool.
+- `JournalStore` (class), `journal.db` / `tapeology_journal.db`, `Config.journal_db_path`,
+  `journal_busy_timeout_ms`, the schema-version constant — the store IS the kept research store
+  (datasets/backtests/champion/pnl live in it). The NAME is legacy; renaming is out of scope.
+- `feed_basis.py`, `profiles.py`, `algorithm_version.py` — kept research modules.
+- `history_marker_states` (config) — ENGINE history markers, not journal marks.
+- `watch_manager.py` — the research-agnostic engine-created hook seam (94-119) STAYS (unwired after
+  J-01); the file is untouched.
+- `serializers.py` — verified ZERO thesis/hint content; untouched.
+
+### I-3 · `JournalStore` method dispositions (`app/research/store.py`)
+
+**DELETE** these methods (anchors at `fa76460`): `insert_thesis` (738), `insert_thesis_with_event` (778),
+`append_verdict_event` (849), `_prune_timeline` (884), `resolve_thesis` (907), `set_execution_checks`
+(922), `set_statement_final_statuses` (942), `set_grades` (962), `set_excursions` (980), `save_review`
+(1000), `resolve_thesis_with_event` (1019), `insert_action` (1061), `insert_study` (1087),
+`update_study_payload` (1103), `set_study_result` (1118), `get_study` (1148), `list_studies` (1165),
+`latest_done_study_for` (1185), `study_occurrence_rows` (1222), `insert_hint` (1423), `get_hint` (1440),
+`list_hints` (1459), `mark_hint_declared_from` (1487), `expire_stale_actives` (1510), `get_thesis` (1562),
+`get_active_thesis` (1572), `list_theses` (1584), `list_row_context` (1651), `get_actions` (1709),
+`has_entry_mark` (1737), `verdict_events` (1749), `_row_to_thesis` (1791), `_encode_risk_flags` (710),
+`_encode_execution_checks` (719) — plus the journal-era record dataclasses (`ThesisRecord`,
+`VerdictEventRecord`, `ActionRecord`, `StudyRecord`, `HintRecord`) and their imports elsewhere.
+
+**KEEP** (do not touch): `__init__` (364), `_apply_pragmas` (383), `_create_schema` (391),
+`_ensure_champion_pointer_seeded` (410), `_column_exists` (431), `_migrate` (436) — **the whole migration
+history stays byte-identical (dormant tables; schema stays v8; no v9; no drops)** — `_read_conn` (667),
+`_writer_loop` (674), `_do_write` (692), `_encode_json_or_none` (729 — keep if any kept method uses it,
+else it may go with the pack), `insert_backtest` (1237), `update_backtest_payload` (1251),
+`set_backtest_result` (1264), `get_backtest` (1278), `list_backtests` (1295), `append_pnl_ledger_row`
+(1317), `get_pnl_ledger_row` (1342), `list_pnl_ledger` (1359), `get_champion_pointer` (1387),
+`set_champion_pointer` (1407), `schema_version` (1774), `journal_mode` (1782), `close` (1851).
+
+### I-4 · `Config` field dispositions (`app/config.py`)
+
+**Confirmed DELETE list** (anchors at `fa76460`): `verdict_dwell_seconds` (508), the invalidation-ε
+spread-multiple field (~516 — locate by the "INVALIDATION ε" comment), `verdict_timeline_cap` (534),
+`management_stance_dwell_seconds` (557), `checklist_stance_dwell_seconds` (580), the entry-checklist
+delivery-lag threshold field (~584+ — locate by the J-63 comment), `excursion_horizons_seconds` (728),
+`excursion_target_r` (734), `study_null_arm_count` (780), `study_arm_sustain_seconds` (789),
+`study_arm_cooldown_seconds` (795), `study_occurrence_r_spread_multiple` (808),
+`study_occurrence_r_floor` (816), `study_null_baseline_seed` (822), `study_list_max` (830),
+`hint_sustain_dwell_seconds` (843), `hint_cooldown_seconds` (851), `hint_log_max` (861).
+
+**Closure rule** (J-04 step 1): beyond the confirmed list, a field is deleted ONLY when a grep proves its
+only readers are deleted modules/tests. **In the same commit, prune the fingerprint EXCLUSION set** inside
+`config_fingerprint()` of now-deleted names (several dwells above are exclusion-listed today).
+
+**KEEP-DANGER fields** (deleting any of these is a defect): `journal_db_path` (410),
+`journal_busy_timeout_ms` (414), the journal schema-version constant, `history_marker_states` (241),
+`recent_trades_limit` (228), `event_log_limit` (229), `market_closed_status_code` (308),
+`vendor_call_timeout_seconds`, every engine/feature/classifier threshold (the graded-region families in
+the 100-300 range), and every `sr_*` / `tradability_*` / `setups_*` / edge-report field.
+
+### I-5 · `app/main.py` + WebSocket anchors
+
+- **Lifespan block (~152-161)**: `store = JournalStore(...)`, `registry = ResearchRegistry(store,
+  CONFIG)`, `set_registry(registry)` all STAY; DELETE `manager.set_on_engine_created(
+  registry.on_engine_created)` (157) and the `registry.startup_sweep()` try/except (159-162); DELETE the
+  shutdown `manager.set_on_engine_created(None)` (~191). The startup-sweep comment block (147-151) goes
+  with it.
+- **WS merge (586-635)**: DELETE `frame["thesis"] = _thesis_projection(ticker)` (602),
+  `frame["hint"] = _hint_projection(ticker)` (607), and both helper functions `_thesis_projection` (614)
+  and `_hint_projection` (626). The frame becomes the engine projection ONLY.
+- **Imports (42-57)**: `ResearchRegistry`, `get_registry_or_none`, `research_router`, `set_registry`, and
... [diff_bound] docs/goal-archive/goal-2026-07-25.md: 326 more diff lines omitted — Read the file for full detail
diff --git a/docs/goal.md b/docs/goal.md
index 2069595..27ac0fc 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1,655 +1,462 @@
-# Tapeology — Project Goal (Interlude: The Clean Slate — demolishing the journal-era surfaces)
+# Tapeology — Project Goal (Era B: The Desk — a daily screening desk over a fetched universe)
 
-> Eras 1–5C are the **foundation** of this goal. Eras 1–2 (tape reading + the research evolution, J-01 – J-68,
+> Eras 1–5D are the **foundation** of this goal. Eras 1–2 (tape reading + the research evolution,
 > GOAL_ACHIEVED) are archived at [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md);
 > the structure-UI interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
 > **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
-> **the "Fast Wall" performance interlude (GOAL_ACHIEVED 2026-07-17, session `fast_wall`, J-01 – J-07)** at
-> [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md). Era 3 (the profit-research
-> measurement machine), Era 4 (the structure-and-tape evolution), and Era 5B "The Tradable Wall" are frozen
-> foundation; their records live in git history and in `reports/goal-session-*-delivered.md`
-> (`tape_to_profit`, `tape_to_profit_support_resistence`, `tradable_wall`, `yahoo_fetch`, `fast_wall`).
+> the **"Fast Wall" performance interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
+> and the **"Clean Slate" demolition interlude (GOAL_ACHIEVED 2026-07-24, session `clean_slate`)** at
+> [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md). Eras 3, 4, 5B "The Tradable
+> Wall", and 5C "The Fast Wall" are frozen foundation; their records live in git history and in
+> `reports/goal-session-*-delivered.md`.
 >
-> **This chapter is an operator-directed DEMOLITION interlude, not one of the numbered research eras** (the
-> 2026-07-07 UI interlude and the 2026-07-17 performance interlude are the precedents). On 2026-07-23 the
-> operator judged the era-1/2 journal-era product surfaces — the manual thesis journal, the replay studies,
-> and the performance/analytics page, with their hints/stance/verdict/grades machinery — **not useful for
-> digging the edge**, and directed their FULL REMOVAL (not hiding) ahead of the next chapters (an automated
-> screening/decision "Desk" era and an AI pattern-annotation era, designed separately). This interlude adds
-> **no research finding and no new capability**: it deletes product surfaces wholesale, keeps every retained
-> research value byte-identical, and carries exactly ONE sanctioned side effect — the `config_fingerprint`
-> **Path B epoch bump** ([`docs/research-directions.md`](research-directions.md) §0.4) that deleting the
-> journal-era `Config` fields forces.
+> **This chapter is Era B of the operator's three-era pivot (A Demolition → B Desk → C Annotator,
+> decided 2026-07-23).** Era A demolished the journal-era surfaces: the product today is exactly
+> **Cockpit (`/`) + Structure (`/structure`)**, the fingerprint epoch is `08e471b10130e1e2`, the MCP
+> surface is 15 read-only tools, and the honesty machinery (stores, gates, registry, PnL promotion
+> ledger) is fully intact. The Desk is the first BUILDING era on that cleared ground: an automated
+> **universe screener + screen ledger + daily briefing**, operated through the UI and through
+> Claude + MCP. It is an operator-directed product era OUTSIDE the research catalog
+> ([`docs/research-directions.md`](research-directions.md) has no Desk card; per its §5.6 this file
+> wins for the running era). The statistics program (era-6 "The Referee") and the AI annotation
+> corpus (Era C) remain SEPARATE future chapters — nothing of them lands here.
 >
-> **This goal.md is deliberately over-specified.** It was authored with the strongest available model
-> against the repo at `main @ fa76460` (2026-07-23), with every deletion-boundary claim verified by grep
-> before being written down. The **Demolition inventory** (I-1 … I-9) and **Weak-model traps** (T-1 … T-14)
-> sections below are the executable ground truth for every iteration. When ANY in-era finding contradicts
-> an inventory row, STOP and surface it in the iteration report — never improvise a bigger deletion.
+> **The Desk adds ZERO new research math.** It orchestrates, persists, and surfaces the frozen
+> 5B/5C computations (tradable-map bands, level classes, bar coverage) across many symbols. Every
+> new number it serves is either read verbatim from an existing canonical owner or is a new
+> desk-owned value (rank rows, coverage rows, snapshot metadata) with exactly one new owner.
 
 ## Vision
 
-The product today carries five pages; the operator uses two. `/journal` (271 lines), `/studies` (171), and
-`/performance` (334) — plus their backend: 15 journal-era routes (`/research/journal*`, `/research/thesis*`,
-`/research/hints*`, `/research/studies*`, `/research/analytics`), eleven research modules (`journal_rows`,
-`monitor`, `hints`, `stance`, `verdict`, `grades`, `marks`, `excursions`, `execution_checks`, `analytics`,
-`studies`), three MCP tools (`journal`, `analytics`, `studies`) plus the thesis/study half of a fourth
-(`taxonomy` — SLIMMED, not deleted: its feed-basis labels feed the KEPT provenance badge), two WebSocket
-frame keys (`thesis`, `hint`), and the cockpit's thesis strip / hint dock / sound cue — all exist to serve
-a manual journaling workflow the operator has concluded does not help find the edge. Dead weight is not
-neutral: every era pays to keep these surfaces green (sentinels, goldens, regression passes), every new
-agent reads them, and the coming Desk era would have to route around them.
-
-This interlude removes them **completely and honestly**:
-
-1. **Deletion, not hiding.** Pages, routes, modules, components, WS keys, MCP tools, nav rows, types, and
-   their tests are gone from the codebase — grep-provably, with no orphaned imports or dead links.
-2. **The kept product is untouched in value.** Cockpit (`/`) and Structure (`/structure`) — the live/sim/
-   historical tape, **both charts** (`StructureChart` + the cockpit `PriceChart` container — kept in full
-   by explicit operator directive), the bar library, levels/zones, the tradable map, case studies, the
-   edge report, the strategy registry, the champion pointer, and the PnL promotion ledger — keep serving
-   **byte-identical numbers on identical inputs**. (`pnl_ledger.py` is the promotion honesty ledger, NOT
-   the performance page — it stays, MCP tool and all.)
-3. **Shared code moves before its home is demolished.** `marks.r_basis` (the R-multiple basis the backtest
-   runner reads) and `studies.py`'s dataset-source constants + reference-window loader (which `datasets.py`,
-   `backtests.py`, and `pnl_baseline.py` import) are relocated byte-identically into kept modules FIRST.
-4. **The fingerprint moves once, lawfully.** Deleting the journal-era `Config` fields (verdict classifier
-   thresholds among them — fingerprint-included by design) moves `config_fingerprint` off the founding
-   `4d665603569b9dbf`. That bump is executed as its own journey, exactly per §0.4 Path B: documented here,
-   pinned literal updated at all **13 verified pin sites** (I-9), founding baseline re-seeded under the new
-   epoch, ledger row appended, sentinel asserting the new pin. Cross-epoch pooling is forbidden forever.
-
-The deliverable is a leaner instrument — **Cockpit + Structure, nothing else** — with the honesty machinery
-(stores, gates, registry, ledger, read-only MCP) fully intact, ready for the Desk chapter to build on
-cleared ground.
+The instrument can read one symbol deeply — levels, zones, tradable bands, case studies, edge
+report — but the operator starts every day with the OPPOSITE problem: *which of the ~100 liquid
+names deserves the instrument today?* Era B builds that answer as a product:
+
+1. **A fetched, registered universe.** S&P 100 constituent membership is fetched from a documented
+   public source on explicit operator command and registered as a dated, checksummed, append-only
+   **universe snapshot** — never silently refetched, never edited, never a signal input. The suite
+   and the UI run keyless on a committed fixture snapshot; live fetch is an operator act.
+2. **An honest bar library over that universe.** A coverage view says, per member, which
+   timeframes have bars and how fresh they are — read from the durable `bar_index`, never by
+   re-hashing stores. An explicit, resumable **top-up** run fetches missing/stale series through
+   the existing keyless Yahoo seam, store-first (a symbol×timeframe already frozen in the store is
+   reused, never re-fetched).
+3. **An operator-run screen with an append-only ledger.** One button (and one CLI, and one POST)
+   walks the pinned universe snapshot as-of a screen date and summarizes, per symbol, what the
+   FROZEN tradable-map computation says: best band, band class, distance from the last daily close
+   in bps, band score, coverage and tick-evidence badges. The ranked result persists as an
+   append-only **screen snapshot** keyed by its inputs (screen date, as-of, universe snapshot,
+   `config_fingerprint`, bar-store state) — identical inputs reproduce byte-identical rows, and
+   a member with no bars appears as an honest `skipped: no bars` row, never a guess. Because every
+   row is as-of-stamped and lookahead-free, a FUTURE era can measure whether the desk's top-ranked
+   walls produced reactions — the ledger is tomorrow's evidence, not today's advice.
+4. **A briefing the operator (and Claude) actually opens.** A third page — **`/desk`** — renders
+   the latest screen as a dense, descriptive briefing with full provenance, an honest
+   "Desk screen not computed yet." empty state, a Run Screen button with live progress, browsable
+   screen history, and per-row drill-in that preloads `/structure` for that symbol and as-of.
+   Two new read-only MCP tools expose the same payloads byte-identically, so the desk can be
+   operated from a Claude conversation end to end.
+
+The deliverable: the two-page instrument becomes a three-page **desk** — universe in, briefing
+out, every number owned once, every run explicit, every record append-only and evaluable later.
 
 ## Target Users
 
-- The project owner (a discretionary intraday trader) who wants the product reduced to the surfaces that
-  actually serve edge-digging, ahead of an automated screening/decision Desk operated through Claude + MCP.
-- AI dev-chain agents (the goal-mode chain) executing and browser-verifying a large, precise deletion
-  without touching a single research value.
-
-## Foundation invariants (still law — eras 1–5C, minus the demolished surfaces)
-
-The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md)) remains
-binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no fabricated data**; single
-source of truth; no magic numbers; provider-agnostic engine; deterministic & reproducible; no secrets in
-source; research read-only over the engine; record integrity; source/feed/`config_fingerprint` honesty —
-**except its surface inventory**: this interlude, by explicit operator direction, removes `/journal`,
-`/journal/[id]`, `/studies`, and `/performance` from that inventory. The KEPT surfaces (`/`, `/structure`)
-stay intact.
-
-In addition, these stay **frozen foundation**:
-
-1. The **tape engine** (`app/engine/` — five states, thresholds, features, history, observations) emits
-   byte-identical output under `default` on identical inputs. `config_fingerprint` stays `4d665603569b9dbf`
-   through J-01 – J-03 and moves EXACTLY ONCE, in J-04, via the §0.4 Path B protocol — never any other way.
-2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan cache),
-   `edge_report*.py` (report, caches, compute manager, CLI), `backtests.py`, the strategy registry
-   (`v1` + `structure_tape` + `structure_tape_map`), `profiles.py` (`default`), and the champion pointer —
-   stay behaviorally byte-identical: identical inputs keep producing identical outputs (only the
-   `config_fingerprint` STAMP inside newly-computed payloads changes after J-04).
-3. The **stores** — the JSON `BarStore` + `DatasetStore` formats, checksums, append-only immutability, split
-   freezing, the durable accelerator DBs (`bar_index`, `dataset_index`, edge-report caches, setups scan
-   cache, tradability cache) — are untouched in format and discipline. Registered datasets and bar series
-   are never deleted, re-tagged, or content-perturbed.
-4. The **PnL promotion ledger** (`pnl_ledger.py`, `reports/pnl/pnl-history.md`, the MCP `pnl_ledger` tool)
-   stays append-only and intact — existing rows keep their original fingerprint stamps forever.
-5. The **era-5B/5C `/structure` surfaces** — Tradable Map / Case Studies / Edge Report sections, the raw
-   toggle, the fetch control + provenance badge, the Compute button + progress poll, the frozen warm-cache
-   texts — and **both charts** — `StructureChart.tsx` (the ONE shared renderer for `/structure` and the
-   cockpit) and `PriceChart.tsx` (the cockpit chart container: historical candles, timeframe switching,
-   viewport paging, S/R band overlay, live tape moving bars) — keep working exactly as shipped. **The
-   charts are kept in full (explicit operator directive, 2026-07-23); a chart regression is veto-class.**
-6. The **read-only MCP server** (`app/mcp/`) keeps its byte-identical GET-proxy contract; this interlude
-   removes three tools and slims one payload (`taxonomy`), never adds writes.
+- The project owner (a discretionary intraday trader) who starts the day on `/desk`: run the
+  screen, read the briefing, drill into `/structure` for the names whose walls are close.
+- The same owner operating through **Claude + MCP**: `desk_universe` / `desk_screen` (plus the
+  existing 15 tools) make the whole desk readable from a conversation.
+- AI dev-chain agents (the goal-mode chain) building and browser-verifying the era.
+
+## Foundation invariants (still law — eras 1–5D)
+
+The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md))
+remains binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no
+fabricated data**; single source of truth; no magic numbers; provider-agnostic engine;
+deterministic & reproducible; no secrets in source; research read-only over the engine; record
+integrity; source/feed/`config_fingerprint` honesty. Its surface inventory is the POST-demolition
+one: `/` and `/structure` (this era adds `/desk`).
+
+1. The **tape engine** (`app/engine/`) emits byte-identical output under `default` on identical
+   inputs. `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era — every new
+   `desk_*` Config field takes §0.4 **Path A** (exclusion + stability test + counter-test); a pin
+   movement is a defect, full stop.
+2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan
+   cache), `edge_report*.py`, `backtests.py`, the strategy registry (`v1` + `structure_tape` +
+   `structure_tape_map`), `profiles.py` (`default`), the champion pointer — stay behaviorally
+   byte-identical. The desk READS them; it never re-implements, re-tunes, or re-grades.
+3. The **stores** — the JSON `BarStore` + `DatasetStore` formats, checksums, append-only
+   immutability, split freezing, the durable accelerator DBs (`bar_index`, `dataset_index`,
+   edge-report caches, setups scan cache, tradability cache) — are untouched in format and
+   discipline. Registered datasets and bar series are never deleted, re-tagged, or
+   content-perturbed. The era ADDS a universe store and a screen store under the same discipline.
+4. The **PnL promotion ledger** (`pnl_ledger.py`, `reports/pnl/pnl-history.md`, MCP `pnl_ledger`)
+   stays append-only and intact; the champion pointer does not move this era.
+5. The **kept surfaces as shipped**: the cockpit (live/sim/historical tape, `PriceChart.tsx`
+   container behaviors, panels) and `/structure` (Load flow, Tradable Map, Case Studies, Edge
+   Report + Compute button, fetch control + provenance badge) — including **both charts**
+   (`StructureChart.tsx`, `PriceChart.tsx`) — keep working exactly as shipped. The ONLY sanctioned
+   `/structure` edit is J-05's additive query-param prefill of the existing Load form.
+6. The **read-only MCP server** (`app/mcp/`) keeps its byte-identical GET-proxy contract; this era
+   adds two GET-proxy tools (15 → 17) and never adds writes.
 
 ## Success Criteria
 
-In priority order — kept-value integrity outranks deletion completeness outranks speed of execution:
-
-1. **Nothing kept regresses.** Full backend suite green; engine equivalence proves byte-identical `default`
-   outputs; every kept `/` and `/structure` behavior works exactly as shipped (browser-verified, both
-   charts included); kept research values (levels, bands, touch events, edge cells, ledger rows)
-   byte-identical on identical inputs; `test_no_execution_path.py` and every kept guard test pass
-   unmodified.
-2. **The demolition is total.** `/journal`, `/journal/[id]`, `/studies`, `/performance` render the app's
-   404; the 15 journal-era routes return 404; nav shows exactly **Cockpit · Structure**; the WS frame
-   carries no `thesis`/`hint` keys; the MCP tool list is exactly the **15 kept tools** (I-6); a repo-wide
-   grep finds no live import of, reference to, or dead test for any deleted module/component (historical
-   `reports/**`, `runs/**`, and `docs/goal-archive/**` excepted — they are read-only history).
-3. **The epoch bump is lawful and complete.** Executed only in J-04, exactly per §0.4 Path B: the new pin
-   literal asserted at all 13 verified pin sites (I-9); the founding baseline re-seeded (`python -m
-   app.research.pnl_baseline`) appending the new-epoch founding row beside the old rows; the epoch change
-   documented on the ledger; no cross-epoch numbers pooled anywhere; no OTHER commit ever touches a pin.
-4. **Relocations are proven moves.** `r_basis` and the dataset-source constants/loader behave byte-
-   identically from their new homes; every kept caller's outputs are unchanged (existing kept tests pass
-   unmodified).
-5. **History stays readable.** journal.db's existing rows and tables remain (dormant — writers/readers
-   deleted, migrations untouched), the PnL ledger keeps all rows, and archived-era artifacts are not
-   edited.
+In priority order — kept-value integrity outranks new-surface completeness outranks convenience:
+
+1. **Nothing kept regresses.** Full backend suite green (1169 pass / 7 skip at era open — grows,
+   never shrinks); engine equivalence proves byte-identical `default` outputs;
+   `Config().config_fingerprint()` prints `08e471b10130e1e2` in every iteration; every kept `/`
+   and `/structure` behavior browser-verified as shipped; every guard test passes unmodified.
+2. **The universe is honest.** Membership comes only from registered, dated, checksummed,
+   append-only snapshots; the parser validates (charset, count bounds, normalization) or fails
+   with an honest error — it NEVER emits a guessed or partial list; the committed fixture keeps
+   every test and default UI state keyless; live fetch happens only on explicit operator command.
+3. **The screen is deterministic and evaluable.** A screen run pins (universe snapshot id, screen
+   date, as-of, `config_fingerprint`, bar-store signature); identical pins reproduce byte-identical
+   rows; members without bars are honest `skipped` rows; snapshots are append-only and never
+   backfilled or recomputed in place; every row's structure numbers match the canonical owners
+   byte-for-byte for the same inputs.
+4. **The briefing is a real product surface.** `/desk` is the third nav row (data-driven from
+   `app/meta.py`); it renders ranked rows with descriptive chips + provenance, honest empty/
+   partial states, a Run Screen button with progress + cancel, browsable history, and drill-in
+   that lands on `/structure` preloaded — all browser-verified with screenshots.
+5. **The desk is Claude-operable.** `desk_universe` and `desk_screen` are byte-identical GET
+   proxies; `ui_route_map` lists the three routes; the MCP suite proves the 17-tool contract.
 
 ## Key Capabilities
 
-This interlude REMOVES capabilities; the "capabilities" below are the demolition's own work packages. The
-exact per-file ground truth for every package lives in the **Demolition inventory** (I-1 … I-9).
-
-1. **Byte-identical relocations (before any deletion — I-2 RELOCATE table).** Move `r_basis` from
-   `marks.py` into `backtests.py` (its sole surviving consumer; `excursions.py`, the other importer, is
-   being deleted). Move `SOURCE_REFERENCE` / `SOURCE_HISTORICAL` / `REFERENCE_SOURCE_ID` /
-   `_load_reference_window` from `studies.py` (lines 101–217) into `datasets.py`, updating the importers
-   (`datasets.py:69-70`, `backtests.py:110`, `pnl_baseline.py:41-43`) and the `edge_report.py:72` comment.
-   Pure moves — no behavior change, no renamed semantics.
-2. **Backend surface deletion (I-1, I-2, I-3).** Delete the 15 journal-era routes; delete modules
-   `journal_rows.py`, `monitor.py`, `hints.py`, `stance.py`, `verdict.py`, `grades.py`, `marks.py`,
-   `excursions.py`, `execution_checks.py`, `analytics.py`, `studies.py`; **SLIM `taxonomy.py`** (the route,
-   module, and MCP tool stay — the KEPT `FeedBasisBadge` reads its `feed_basis` block — but every
-   thesis/verdict/stance/study label family and copy block is deleted); strip `ResearchRegistry` to its
-   kept duties (store access + the backtest/edge-compute job managers) — `study_jobs`,
-   `hint_projection_for`, `on_engine_created`, and `startup_sweep` go; remove the WS `thesis`/`hint` merge
-   and the lifespan monitor wiring from `app/main.py` (I-5); delete `JournalStore`'s journal-era methods
-   and record dataclasses (I-3; tables stay dormant; the append-only migration history is NOT edited;
-   schema version stays v8).
-3. **Frontend + WS deletion (I-7).** Delete pages `apps/frontend/app/{journal,studies,performance}/`; the
-   eleven journal-era components; the 14 journal-era `lib/api.ts` functions (**`fetchTaxonomy` is NOT one
-   of them** — the badge keeps it); the thesis/hint types and WS-frame fields; the cockpit page's thesis
-   stop-flow and thesis/hint/sound rendering; the four nav rows from `app/meta.py` ROUTES. **Both chart
-   components are kept** (I-7 chart clause): `StructureChart.tsx` untouched; `PriceChart.tsx` keeps every
-   behavior except building thesis-geometry overlays from the now-deleted thesis data.
-4. **MCP contract v2 — 15 tools (I-6).** Remove tools `journal`, `analytics`, `studies` from
-   `app/mcp/__init__.py`; `taxonomy` STAYS (its payload slims because the route's payload slims — the
-   byte-identical proxy discipline is unchanged). Update `tests/test_mcp_server.py` to the 15-tool
-   contract; `get_endpoint` allowlist unchanged (deleted paths now surface the backend's honest 404 — the
-   existing unshipped-path contract).
-5. **The §0.4 Path B epoch bump (its own journey — I-4, I-9).** Delete the journal-era `Config` fields
-   (confirmed list in I-4, closure rule by grep), prune the fingerprint EXCLUSION set of deleted names in
-   the same commit, then execute Path B verbatim: update the pinned literal at all 13 verified pin sites;
-   re-seed the founding baseline; document the epoch change on the ledger; the J-05 sentinel asserts the
-   new pin. Registered dataset/bar fixtures are untouched (rail 9).
-6. **Test-suite demolition + sentinel re-baseline (I-8).** Delete the ~24 journal-era test files; UPDATE
-   the six mixed/contract files per I-8's explicit keep/drop notes (`test_copy_discipline` is a KEEPER —
-   the rail-2 language lint); keep every kept-side test unmodified (the fast_wall source-introspection
-   guards included); browser-verify the kept product end to end (both charts included).
+1. **Universe subsystem (new data kind, honest by construction).** A universe vendor seam (the
+   bars-vendor pattern) fetching S&P 100 membership from ONE documented public source; a parser
+   contract (ticker charset `[A-Z.-]{1,6}`, count sanity 90–110, **Yahoo normalization
+   `BRK.B → BRK-B`**, dedupe, sorted output); registration as
+   `apps/backend/.data/universe/universe-<YYYY-MM-DD>-<checksum12>.json` (frozen JSON = source of
+   truth; any index over it is derived/rebuildable); a committed fixture snapshot under
+   `apps/backend/tests/fixtures/` for hermetic tests + default keyless UI;
+   `GET /research/desk/universe` serving snapshot list + latest membership with honest emptiness.
+2. **Coverage + top-up.** `GET /research/desk/coverage` (or a `universe` payload block): per-member
+   × per-timeframe bar presence + freshness read from `bar_index` (NEVER re-hashing the store);
+   an explicit operator-run top-up (POST + CLI) that walks members store-first through the
+   existing `POST /research/bars` fetch path, resumable, worker-capped, logging per-symbol
+   outcomes; the timeframe set = exactly what `compute_levels`/`compute_tradability` read for a
+   daily-close screen (verify at build time; era-5 contract: `4h` is resampled from `1h`, never
+   fetched; intraday microscope tfs stay per-symbol on `/structure`).
+3. **Screen compute + append-only ledger.** An operator-run screen (POST + CLI + `/desk` button)
+   over the pinned latest universe snapshot: per member, call the CANONICAL owners
+   (`compute_tradability` / levels / `bar_index`) as-of the screen date's session close and
+   summarize best band, class, distance-from-close (bps), band score, coverage + tick-evidence
+   badges; deterministic rank order = (band class A>B>C, then distance asc, then band score desc,
+   then symbol asc); single-flight + progress + cancel via the 5C compute-manager pattern;
+   persistence as append-only screen snapshots (frozen JSON + derived index) with full input pins;
+   `GET /research/desk/screen` (latest / `?date=`) + honest `"Desk screen not computed yet."`.
+4. **The `/desk` briefing page.** Third nav row; latest-screen briefing table (rank, symbol,
+   band class chip, distance chip, score, coverage/evidence badges, skipped rows grouped
+   honestly); provenance line (universe snapshot id + date, as-of, fingerprint, bar-store
+   signature); Run Screen + top-up buttons with live progress + cancel; screen history list;
+   dark/dense/terminal-grade per house style.
+5. **Drill-in + `/structure` prefill.** Clicking a briefing row navigates to
+   `/structure?symbol=<sym>&asof=<iso>`; `/structure` gains query-param PREFILL of its existing
+   Load form (prefill + auto-Load; `apps/frontend/app/structure/page.tsx` inputs at ~:2057/:2070)
+   — no other `/structure` behavior changes; the desk never recomputes structure values.
+6. **MCP contract v3 — 17 read-only tools.** Add `desk_universe` → `/research/desk/universe` and
+   `desk_screen` → `/research/desk/screen` to `_STATIC_PATHS` (`app/mcp/__init__.py:85`);
+   `get_endpoint` allowlist (`/tape/`, `/research/`, `/meta/`) already covers the new paths
+   unchanged; `tests/test_mcp_server.py` proves the 17-tool contract with byte-identity and
+   honest-error clauses.
 
 ## Non-Goals
 
-- **No new features, pages, endpoints, strategies, or Config fields.** The Desk (universe screener,
-  decision ledger, briefing) and the AI annotation corpus are the NEXT chapters — designed separately,
-  built only after this interlude closes. Nothing of them lands here.
-- **No research-value change beyond the documented epoch bump.** No level/band/reaction/cell/PnL number
-  moves; no parameter re-tuning; no gate, minimum-n, split, or register change.
-- **No engine work.** `app/engine/` is untouched; its five states, thresholds, and outputs are frozen.
-- **No chart work.** `StructureChart.tsx` and `PriceChart.tsx` are kept as shipped (minus the sourceless
-  thesis-overlay inputs) — no rewrites, no "cleanups", no renderer consolidation.
-- **No MCP write surface.** MCP stays read-only GET proxies; this interlude only removes/slims tools.
-- **No recording, no new data, no credential work, no Yahoo/universe fetching.**
-- **No editing of archived history** — `docs/goal-archive/`, `runs/goal-session-*`,
-  `reports/goal-session-*-delivered.md`, `reports/phase-goal-*` artifacts, `reports/pnl/pnl-history.md`'s
-  existing rows, and journal.db's existing rows are read-only records. (Deleting CODE is this era's
-  mandate; deleting RECORDS is forbidden.)
-- **No schema surgery.** No v9 migration, no table drops, no rewriting migration history — dormant tables
-  are the honest, cheap choice.
+- **No statistics program.** No new gates, CIs, nulls, multiple-testing control, or promotion
+  logic — that is era-6 "The Referee" (future). The screen RANKS by existing descriptive
+  structure metrics; it never claims edge, probability, or expectancy.
+- **No annotation layer.** Human/AI pattern annotation, dispositions, notes, or any manual input
+  path on desk records is Era C "The Annotator" (designed separately). This era's ledger records
+  MACHINE output only.
+- **No strategy/champion work.** No new strategies/profiles, no backtest changes, no champion
+  movement, no PnL-ledger rows beyond what existing machinery already writes.
+- **No scheduling.** No cron, daemon, auto-refresh, or market-hours trigger — every fetch,
+  top-up, and screen run is an explicit operator act (UI button / CLI / POST).
+- **No tick-data expansion.** No new dataset recording, no credential work; tick evidence badges
+  reflect the 11 recorded dataset symbols as they stand.
+- **No engine, chart, or kept-surface work.** `app/engine/` untouched; `StructureChart.tsx`
+  untouched; `PriceChart.tsx` untouched; `/structure` untouched beyond the J-05 prefill.
+- **No fingerprint epoch bump.** Path A only; the pin `08e471b10130e1e2` does not move.
+- **No second market, no options/sentiment/news data, no paid services.** The one new external
+  read is the documented constituents source; membership is universe METADATA, never a signal
+  input (the roadmap's earnings-calendar exclusion-only precedent).
 
 ## Constraints
 
-- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm), `lightweight-charts`,
-  dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`, frontend
-  `http://localhost:3000`. No new runtime dependency.
-- **The deletion boundary is exactly the Demolition inventory (I-1 … I-9).** Anything discovered in-era
-  outside those lists is surfaced in the iteration report BEFORE being touched (trap T-14).
-- **Ordering discipline:** relocations land and prove green BEFORE their source modules are deleted
-  (J-01); the fingerprint pins are untouched until J-04; J-04 touches the pins and NOTHING else touches
-  them.
-- **Guard tests (kept, never edited):** `tests/test_no_execution_path.py`;
-  `tests/test_no_credential_in_artifacts.py`; the fast_wall source-introspection guards
-  (`tests/test_backtests.py:1500-1508` forbidden level-internal substrings,
-  `tests/test_backtests.py:932-943` map-arm source pins, `tests/test_setups.py:995-1017` single
-  `_SCAN_CACHE` rebind, `tests/test_setups.py:758-771` forbidden substring, the edge-report route
-  `Depends` pin). The ONLY sanctioned pin edit is J-04's Path B literal update at the 13 sites (I-9) —
-  the fingerprint ASSERTION LINES inside otherwise-kept test files are updated, the tests around them are
-  not weakened.
-- **WS contract change is explicit and typed:** the frame loses exactly the `thesis` and `hint` keys;
-  `lib/types.ts` + `lib/useTapeStream.ts` are updated in the same journey (J-02); no `undefined`-field
-  ghosts remain in the frontend types.
-- **Honest wording:** deleted surfaces 404 — no redirects, no "coming soon" placeholders, no tombstone
-  pages. The 404 is the app's existing not-found rendering.
-- **Test discipline:** the suite stays hermetic and keyless on committed fixtures; no kept test deleted or
-  weakened; the real-corpus behaviors (edge-report warm render, tradable map on real bars) are operator-run
-  verifications, never CI gates.
-- **Framework hygiene:** if any goal-mode framework asset (demo scripts, proposer guidance, eval fixtures)
-  references deleted surfaces, the reference is updated in the neutral source per
-  `.claude/maintenance-protocol.md` — never by editing generated mirrors.
+- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm),
+  `lightweight-charts`, dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`,
+  frontend `http://localhost:3000` (browser-QA rig on `:8301`/`:3301`). No new runtime dependency
+  (the universe fetch uses the stdlib/HTTP client patterns the Yahoo adapter already uses).
+- **Config discipline (§0.4 Path A, every time):** every new SEMANTIC knob is a `Config` field
+  (`desk_universe_source_url`, `desk_universe_min_members`, `desk_universe_max_members`, plus any
+  the build genuinely needs) added to the `config_fingerprint()` exclusion set
+  (`app/config.py:1312`) **in the same commit**, with (i) a stability test proving the pin is
... [diff_bound] docs/goal.md: 810 more diff lines omitted — Read the file for full detail
```
