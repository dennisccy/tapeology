# Goal Iteration 1 — Backend demolition with byte-identical relocations (J-01)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** clean_slate
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-05 (backend/keyless subset only — see NOTES)
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(This era's one sanctioned exception, operator-approved 2026-07-23: the journal/studies/performance product surfaces are REMOVED outright — never mutated-in-place — and their historical records stay readable; nothing else moves.)* *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **No research-value change beyond the documented epoch bump.** Every number a KEPT surface serves (levels, bands, touch events, edge cells, pnl rows) stays byte-identical on identical inputs; the ONLY sanctioned change is the `config_fingerprint` value itself, moved once via the J-04 Path B journey; cross-epoch pooling is forbidden forever. *(critical)*
  - **Deletion is complete, never cosmetic.** No orphaned imports, dead components, unreachable routes, dangling MCP tools, or skipped tests survive; a deleted surface is gone from code, routes, nav, MCP, types, and tests alike — grep-provably. *(critical)*
  - **No new features.** This era ships zero new product capabilities, pages, endpoints, strategies, or Config fields; anything new belongs to the next eras. *(critical)*
  - **Relocations are moves, not rewrites.** `r_basis` and the dataset-source constants keep byte-identical behaviour at their new homes; every kept caller's output is proven unchanged. *(critical)*
  - **Never modify the charts beyond the one named edit.** No commit in this era may edit `StructureChart.tsx` at all, or edit `PriceChart.tsx` beyond removing its thesis-geometry overlay build (I-7 chart clause); the three chart guard suites must pass byte-unmodified; any other chart diff — visual or behavioral — is a veto-class defect. *(critical)*
  - **Never touch a historical record.** No commit in this era may delete, rewrite, truncate, or re-stamp journal.db's existing rows or tables, any PnL-ledger row, anything under `docs/goal-archive/` or `runs/goal-session-*`, or any `reports/goal-session-*-delivered.md` — a diff touching any of these is a veto-class defect (deleting CODE is the mandate; deleting RECORDS is forbidden). *(critical)*
  - **No guard weakening.** `test_no_execution_path.py`, the source-introspection guards, and every kept test stay as written; the fingerprint pins change ONLY inside J-04 per Path B, never to make a red test green. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block of goal.md — it MUST NOT edit human-authored journeys, the Anti-goals section, or any other part of that file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Delete the backend half of the journal/studies/performance surfaces — 14 routes, 11 modules, `JournalStore`'s journal-era methods, and their ~24 tests — after relocating two shared helpers byte-identically first, so every kept backend endpoint (bars, levels, tradability, setups, backtests, pnl ledger, profiles, strategies, edge-report, the slimmed taxonomy) keeps serving byte-identical data and the deleted routes honestly 404; there is no user-visible change yet — the frontend still shows all 5 pages until J-02 lands.

## BACKGROUND

Iteration 0 (baseline, zero code diff) recorded J-01–J-04 `failing` and J-05 `partial`. The evaluator's Next-Step Recommendation explicitly targets **J-01 alone at full depth**, honoring goal.md's own dependency order (J-01 → J-02 → J-03 → J-04 → J-05) and the hard two-phase ordering constraint: relocations must land and prove green BEFORE any deletion. Per the target-selection rubric this also satisfies rule 3 (J-01 is the natural unblocker — J-02's frontend deletion and J-03's MCP contract both assume the backend routes/modules are already gone) and rule 5 (J-01 alone is already a large, structural, risky change — eleven modules, ~24 test files, `JournalStore`'s schema-adjacent method surface — so no second risky journey may be bundled with it this iteration). Depth is **full** because this crosses the "touches data model" and "large/structural" triggers in the Picking-depth rubric (JournalStore method + dataclass deletion, multi-file backend refactor with an ordering constraint), independently confirming the evaluator's own recommendation.

Two lessons carried forward from iter-0 (see NOTES for detail): (1) goal.md's I-1 header text says "15 route handlers" but the table + taxonomy-SLIM note reconcile to 14 DELETE + 1 SLIM — verified against the live `routes.py` decorator anchors during this iteration's planning, so this is settled, not a contradiction to re-litigate; (2) `/structure`'s Case Studies section is currently code-suppressed (pre-existing, unrelated to this backend-only iteration) and will block J-05's literal acceptance later — out of scope here, flagged again for J-02/J-05 planning.

## IN SCOPE

### Backend
- [ ] Capture the byte-comparison baseline (I-9 step 1): with the backend running on committed fixtures, sha256 every KEPT `/research`, `/tape`, `/meta` GET response into the session run dir as `kept-route-baseline.txt`, captured BEFORE any deletion below.
- [ ] Relocate `r_basis` from `app/research/marks.py` into `app/research/backtests.py` (I-2 RELOCATE row 1) — private helper, same math; update the one surviving importer.
- [ ] Relocate `SOURCE_REFERENCE`, `SOURCE_HISTORICAL`, `REFERENCE_SOURCE_ID`, `_load_reference_window` from `app/research/studies.py` into `app/research/datasets.py` (I-2 RELOCATE row 2); update the `datasets.py`, `backtests.py`, `pnl_baseline.py` importers and the `edge_report.py` comment.
- [ ] Run the full backend suite after the two relocations land, BEFORE any deletion below — every kept test must pass unmodified (ordering discipline).
- [ ] Delete the 14 I-1 DELETE route handlers from `app/research/routes.py`: `GET /research/analytics`, `GET /research/thesis/active`, `GET /research/hints/active`, `GET /research/hints`, `GET /research/journal`, `GET /research/journal/{thesis_id}`, `POST /research/thesis`, `POST /research/thesis/{thesis_id}/resolve`, `POST /research/thesis/{thesis_id}/action`, `POST /research/thesis/{thesis_id}/review`, `POST /research/studies`, `GET /research/studies`, `GET /research/studies/{study_id}`, `POST /research/studies/{study_id}/cancel` — plus their now-dead helpers (`build_journal_detail`, `get_study_market_adapter`).
- [ ] SLIM `GET /research/taxonomy` in `app/research/taxonomy.py` to the kept label families only (`feed_basis` block + `sim`/`iex`/`sip`/`yahoo` source labels) — the route and MCP tool stay; every other label family (verdict, thesis-status, stance, `STUDY_COPY`, etc.) is deleted per I-2's taxonomy SLIM row.
- [ ] Strip `routes.py`'s delete-side imports (I-2 SLIM row) and `ResearchRegistry`'s `study_jobs`, `hint_projection_for`, `on_engine_created`, `startup_sweep` — keep store access and the backtest/edge-compute job managers.
- [ ] Remove the lifespan monitor wiring from `app/main.py` — `manager.set_on_engine_created(registry.on_engine_created)`, `registry.startup_sweep()`, and the matching shutdown call (I-5 lifespan half ONLY — the WS `thesis`/`hint` merge is J-02's job, not this iteration's).
- [ ] Delete the eleven journal-era modules — `journal_rows.py`, `monitor.py`, `hints.py`, `stance.py`, `verdict.py`, `grades.py`, `marks.py`, `excursions.py`, `execution_checks.py`, `analytics.py`, `studies.py` — running T-12's grep-before-delete (`grep -rn "from .M import\|from app.research.M import\|import M" apps/`) on each before removing it.
- [ ] Delete `JournalStore`'s journal-era methods and record dataclasses (`ThesisRecord`, `VerdictEventRecord`, `ActionRecord`, `StudyRecord`, `HintRecord`) from `app/research/store.py` per I-3's DELETE list; every I-3 KEEP method (migrations, backtest/pnl/champion methods) stays untouched.
- [ ] Delete the ~24 journal-era test files (I-8 DELETE list): `test_analytics.py`, `test_analytics_api.py`, `test_excursions.py`, `test_execution_checks.py`, `test_grades.py`, `test_journal_list.py`, `test_journal_migration.py`, `test_research_action.py`, `test_research_checklist.py`, `test_research_excursions_integration.py`, `test_research_execution_checks_api.py`, `test_research_freshness_integration.py`, `test_research_geometry.py`, `test_research_hints.py`, `test_research_hints_api.py`, `test_research_lifecycle.py`, `test_research_marks.py`, `test_research_monitor.py`, `test_research_resolve.py`, `test_research_review.py`, `test_research_risk_flags.py`, `test_research_stance.py`, `test_studies.py`, `test_studies_api.py`, `test_verdict_engine.py`.
- [ ] Apply the I-8 UPDATE edits belonging to this iteration's surfaces: `test_research_api.py` (drop thesis/stance/checklist seeded checks, keep feed-basis), `test_research_store.py` (drop thesis/hint/study method coverage, keep backtest/pnl/champion), `test_studies_reference.py` (re-point at the relocated loader/constants in `datasets.py`), `conftest.py` (import-line cleanups only), and `test_copy_discipline.py`'s served-copy walk (drop the verdict/checklist/hint/analytics/studies served-copy checks — those backend surfaces are deleted this iteration; its frontend-literal walk is untouched here, that shrinks in J-02).
- [ ] Leave `test_mcp_server.py` and `test_meta_routes.py` untouched this iteration — their contract updates belong to J-03 and J-02 respectively.
- [ ] Leave all 13 fingerprint pin assertion sites (I-9) and every `Config` field byte-unmodified — J-04's job only (T-3).
- [ ] Re-capture the byte-comparison hashes for every KEPT route (I-9 step 2) and diff against `kept-route-baseline.txt` — zero deltas except `/research/taxonomy`'s expected payload shrink.
- [ ] Run T-12's grep for all eleven deleted module names across `apps/` — zero live hits outside `reports/**`, `runs/**`, `docs/goal-archive/**`.

### New user-facing capability
None. This iteration is backend-only and keyless/automated per goal.md's own J-01 acceptance tag.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None. The frontend still renders `/journal`, `/studies`, `/performance` and shows the 5-item nav until J-02 — that is expected, not a regression, since J-01's scope is backend routes/modules/tests only.

### Product surface delta
None visible in the browser. The deleted routes now 404 at the HTTP layer only (curl/pytest-verifiable); no page a human would click has changed.

### Blueprint conformance
No new surfaces — this iteration touches zero pages/nav. The two relocations it performs (`r_basis` → `backtests.py`; dataset-source symbols → `datasets.py`) are already documented verbatim in `blueprint.md`'s existing Data Contract rows (Backtests, Datasets) from baseline drafting — no blueprint edit is required this iteration.

### Data-contract additions
None. No new displayed value is introduced. The two relocated helpers move into their already-registered canonical owners; every value a KEPT surface serves must stay byte-identical (verified via the I-9 byte-comparison protocol — TC-1/TC-5 below).

## OUT OF SCOPE

- Frontend/WS demolition (J-02) — pages, components, `lib/api.ts` functions, types, the cockpit's thesis/hint/sound integration, `PriceChart.tsx`'s thesis-geometry overlay removal, `app/meta.py` ROUTES trim, and the WS `thesis`/`hint` frame-merge removal in `app/main.py` — all deferred to iteration 2.
- MCP tool removal (J-03) — `_TOOL_PATHS`/`types.Tool` deletions for `journal`/`analytics`/`studies`, `test_mcp_server.py`'s 15-tool contract update — deferred to iteration 3. Transiently those three MCP tools will proxy to now-404 routes via `get_endpoint`'s existing honest-404 contract; this is expected per I-6's own wording, not a defect.
- Config field deletion + the `config_fingerprint` epoch bump (J-04), including any of the 13 pinned assertion sites — strictly deferred to iteration 4 (T-3 pin discipline: this iteration's diff must show zero change on those 13 lines).
- `test_meta_routes.py`'s route-inventory update — belongs to J-02 (changes only when `app/meta.py` ROUTES actually loses rows).
- `test_copy_discipline.py`'s frontend-literal walk — belongs to J-02 (changes only when the frontend components/pages are actually deleted).
- Restoring `SHOW_CASE_STUDIES` on `/structure` — a pre-existing, unrelated frontend flag flagged by iter-0's evaluator as blocking J-05's literal acceptance; not required by J-01, not touched here. Must be resolved (restore vs. operator rescopes J-05) before J-05 closes.
- Any browser/UI verification — J-01's acceptance is keyless/automated per goal.md; no Chrome MCP dispatch is expected for this iteration's target.
- Schema migrations, `journal.db` table drops, or any edit to `_migrate`/`_create_schema` — dormant tables are the correct end state (T-4).

## DEFINITION OF DONE

- [ ] J-01 passes: the 14 I-1 DELETE routes return HTTP 404; `GET /research/taxonomy` returns 200 with the slimmed `feed_basis`+source-label payload; every other kept `/research`, `/tape`, `/meta` GET route is byte-identical (sha256) to the I-9 baseline capture
- [ ] The two I-2 RELOCATE moves (`r_basis`, dataset-source symbols) land and the full suite passes BEFORE any deletion (ordering discipline)
- [ ] Eleven journal-era modules deleted; T-12 grep returns zero live hits per module outside `reports/**`, `runs/**`, `docs/goal-archive/**`
- [ ] `JournalStore`'s journal-era methods + record dataclasses deleted per I-3; every I-3 KEEP method untouched
- [ ] ~24 journal-era test files deleted; the five backend-relevant I-8 UPDATE files edited to their reduced scope; every other kept test passes unmodified
- [ ] `python -c "from app.config import Config; print(Config().config_fingerprint())"` still prints `4d665603569b9dbf`; none of the 13 fingerprint pin assertion sites touched
- [ ] Full backend suite passes (0 failed, 0 errors)
- [ ] No anti-goal violation introduced (rails 1, 3, 5, 6, 8, 9, plus the interlude-specific "deletion complete never cosmetic," "relocations are moves not rewrites," "no guard weakening")
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-clean_slate-iter-1-dev.md`

## TESTING REQUIREMENTS

- Browser: none — J-01 is keyless/automated; no journeys require Chrome MCP this iteration.
- Unit/integration: full `apps/backend` pytest suite (1665 passed / 7 skipped per iter-0's baseline capture) must stay passing after the deletions/relocations, with the ~24 files removed and the five I-8 backend UPDATE files reduced; T-12 grep-before-delete run for each of the eleven deleted modules; I-9 byte-comparison capture-and-diff run before and after the deletions.
- Error cases: each of the 14 deleted routes must return exactly 404 (not 200, not 500, not a redirect) when curled with its correct verb; a `get_endpoint`-style probe of a deleted path must not raise an unhandled exception.

Test-first contract:

- TC-1: given the backend running on committed fixtures BEFORE any deletion in this iteration, when every KEPT `/research`, `/tape`, `/meta` GET route is curled, then its response is sha256-captured into `kept-route-baseline.txt` in the session run dir (I-9 step 1).
- TC-2: given `r_basis` is relocated from `marks.py` into `backtests.py` and the four dataset-source symbols are relocated from `studies.py` into `datasets.py`, when `pytest apps/backend/tests/` runs immediately after (before any deletion below), then it reports 0 failed and 0 errors.
- TC-3: given the 14 I-1 DELETE routes are removed from `routes.py`, when each of the 14 routes is curled on the running backend (its correct GET/POST verb), then each returns HTTP status 404.
- TC-4: given `GET /research/taxonomy` is SLIMMED per I-2, when it is curled, then the response body contains the `feed_basis.feeds[]` block and the `sim`/`iex`/`sip`/`yahoo` source labels, and contains none of the verdict-label, thesis-status-label, stance-label, or `STUDY_COPY` strings named in I-2's taxonomy SLIM row.
- TC-5: given the 14-route deletion and the taxonomy slim are applied, when every OTHER kept `/research`, `/tape`, `/meta` GET route is curled and sha256-compared against `kept-route-baseline.txt`, then every hash is identical to its baseline entry.
- TC-6: given the eleven journal-era modules are deleted, when `grep -rn "from .M import\|from app.research.M import\|import M" apps/` is run for each module name M in {journal_rows, monitor, hints, stance, verdict, grades, marks, excursions, execution_checks, analytics, studies}, then the only hits (if any) are inside `reports/**`, `runs/**`, or `docs/goal-archive/**`.
- TC-7: given `JournalStore`'s journal-era methods and dataclasses are deleted per I-3, when the backend suite exercises the I-3 KEEP methods (`insert_backtest`, `append_pnl_ledger_row`, `get_champion_pointer`, `list_pnl_ledger`), then each returns the same shape/values it did in the pre-iteration suite run.
- TC-8: given the ~24 journal-era test files are deleted and the five backend I-8 UPDATE files are edited to their reduced scope, when `pytest apps/backend/tests/` runs, then it reports 0 failed, 0 errors, and a collected-test count no higher than 1665 minus the deleted files' test counts (no new tests silently added).
- TC-9: given no `Config` field is touched this iteration, when `python -c "from app.config import Config; print(Config().config_fingerprint())"` runs, then it prints `4d665603569b9dbf`.
- TC-10: given the full iteration diff, when the 13 fingerprint pin assertion sites listed in I-9 (`test_timeframe_history_api.py:194`, `test_levels.py:718`, `test_tradability.py:370`, `test_backtests.py:416`, `test_backtests.py:1485`, `test_profile_equivalence.py:114`, `test_pnl_scan.py:193/266/569/646`, `test_edge_report.py:213`, `test_setups.py:409/779`) are diffed against `fa76460`, then none of those 13 lines differ.
- TC-11: given the full iteration diff, when it is checked against the "never touch a historical record" anti-goal, then zero lines under `docs/goal-archive/`, `runs/goal-session-*`, `reports/goal-session-*-delivered.md`, or `journal.db`'s existing rows are touched.

## NOTES

- **Route-count reconciliation (carried from iter-0 lesson).** goal.md's I-1 header sentence says "DELETE these 15 route handlers" but the table lists 14 rows, and `GET /research/taxonomy` is called out immediately after as SLIM (not DELETE). Verified during this iteration's planning against the live `routes.py` decorator anchors — all 14 DELETE anchors and the taxonomy anchor at line 446 match exactly. Treat "14 DELETE + 1 SLIM = 15 journal-era routes touched" as settled; do not re-litigate the count.
- **Case Studies flag (carried from iter-0 lesson, applies to J-05, not this iteration).** `/structure`'s Case Studies section is currently suppressed (`SHOW_CASE_STUDIES = false`, `apps/frontend/app/structure/page.tsx:335`, commit `e60f6a7`, pre-dates goal.md and is unrelated to this era). This backend-only iteration does not touch it. It must be resolved — restore the flag (reversible per its own commit message) vs. the operator rescopes J-05's acceptance line — before J-05 can close. Surface again when J-02 (frontend) is planned.
- **`test_copy_discipline.py` split (discovered during this iteration's planning).** Read in full: it walks three surfaces — (a) the entire `GET /research/taxonomy` payload, (b) served copy from verdict/checklist/hint/analytics/studies (ALL deleted this iteration), and (c) frontend source literals. Only (a) and (b) belong to this iteration; (c) belongs to J-02. Developer should update only (a)/(b) here.
- **Required-still-passing scoping.** `journey-history.json` currently has no `passing` journeys (J-01–J-04 `failing`, J-05 `partial`), so there is no stable-passing regression set to protect via replay this iteration. J-05 is listed as Required-still-passing in its backend/keyless subset only — the I-9 byte-comparison protocol above (TC-1/TC-5) IS the mechanism that catches "kept routes regressed," which is J-01's own acceptance criterion. J-05's browser-walked portion (cockpit screenshots, `/structure` Load, Case Studies, Edge Report state) is not re-verified this iteration since zero frontend files change in this diff; it will be re-confirmed once frontend work resumes in J-02 and finally closed in J-05's own iteration. `Frontend Present: no` is set accordingly — no Chrome MCP dispatch is expected or required this iteration.
- No new assumption-ledger entry was logged this iteration: target/depth selection followed the rubric mechanically against the evaluator's own explicit recommendation, and every relocation/deletion traces to an already grep-verified goal.md inventory row — no goal-text ambiguity required interpretation.
