# Goal Iteration 16 — Snapshots are addressable by id, and ledgers disclose their own integrity errors

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 16
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: one coordinated change touches `desk_screen.py` (new `?id=` read branch + `id`+`date` refusal path), `desk_routes.py` (two sibling ledger routes — `get_topup_runs` :270-281, `get_desk_index_reconcile_runs` :495-509 — each gain an `integrity_errors` key), and `page.tsx` (history-select-by-id, id-based row highlighting, Provenance `id`/`created_utc`, four-ledger integrity-error disclosure). The acceptance also requires a `[NEW]`-flagged demo-narrator walkthrough over a same-date recorded-snapshot pair — the exact acceptance shape that ESCALATEd this session twice at lean depth (iter-11, iter-12) because lean's demo-narrator lane runs after scoring; full ensures the pipeline's audit/closure lanes catch a capture-order defect (iter-12/iter-13 lesson) before the verdict is cast.
- **Frontend Present:** yes
- **Target journeys:** J-12
- **Required-still-passing journeys:** J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11
- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Every screen snapshot the history list already names becomes individually readable by its own id
(closing the "two same-date recordings, only the newer one reachable" gap J-10's own repair
exposed), and the two run ledgers that today silently drop their own store's verification errors
start disclosing them the same way the screen and universe ledgers already do.

## BACKGROUND

Iteration 15 closed GOAL_ACHIEVED (11/11 journeys passing); the evaluator's last-recommendation
list named nothing blocking. The goal-proposer then appended J-12 inside the `AUTO:journeys`
marker (its fifth post-GOAL_ACHIEVED addition this era, after J-08/09/10/11), reopening the era for
one more disclosure journey — the same pattern as iterations 9, 11, 14, 15. J-12's own rationale is
measured live against the running backend and the frozen `.data/screen` store (2026-07-29): the
store already holds a same-`screen_date` pair from J-10's own reconciliation
(`screen-2026-07-27-936543601e75` pre-repair, `screen-2026-07-27-3ad3c57aa6ba` post-repair) that
`GET /research/desk/screen?date=` can only ever resolve to the later one — the earlier record is
listed by the history endpoint and permanently unreadable by any existing path — and both
`GET /research/desk/topup/runs` and `GET /research/desk/coverage/reconcile/runs` already unpack an
`errors` tuple from `store.list()` and discard it (`desk_routes.py:277`, `:505`) while their two
sibling GETs (`screen` :330, `universe` :171) already serve it as `integrity_errors`.

**Depth and lessons applied.** This journey's acceptance explicitly names a
`[NEW]`-flagged demo-narrator walkthrough (lessons iter-12/iter-13: that clause structurally
requires `full` depth, since at `lean` the demo-narrator lane runs after the goal-evaluator scores
the iteration). Evidence capture must follow the scoped-rig discipline restated at iter-9/iter-14/
iter-15: the corrupt-record-integrity test plants its file in a SCOPED store dir, **never**
`apps/backend/.data` (goal.md's own step 6 wording); the same-date-pair screenshots may read the
real ambient pair directly OR a `cp -a` read-only copy of it — goal.md's own acceptance text
anticipates the ambient rig here because this journey triggers no compute and writes nothing
(unlike J-09/J-10/J-11's WRITE-triggering buttons). One-way-door capture ordering (iter-12/13
lesson) does not apply this iteration — nothing here is append-only-and-empty-once; both same-date
records already exist and reading them is repeatable.

## IN SCOPE

### Backend
- [ ] `desk_screen.py` / `desk_routes.py` `get_screen` (`desk_routes.py:314`): add an `id: str | None`
      query param. When `id` is given (and `date` is not), return `{"screen": <that exact persisted
      snapshot, verbatim>}` if found, else the existing honest `{"screen": null}` at HTTP 200 (the
      `?date=` convention, unchanged). `?date=` alone keeps its documented, byte-unchanged meaning.
      `id` and `date` supplied together return an honest 4xx refusal (never a silent precedence
      rule). The read recomputes nothing and writes nothing; `ScreenStore` stays the only owner.
- [ ] `desk_routes.py` `get_topup_runs` (`:270-281`): stop discarding `store.list()`'s `errors`
      return — add `"integrity_errors": errors` to the response, in the identical key/shape
      `get_screen`/`get_universe` already use.
- [ ] `desk_routes.py` `get_desk_index_reconcile_runs` (`:495-509`): same change — add
      `"integrity_errors": errors` sourced from `store.list()`'s own return, identical shape.
- [ ] Tests: fixture-scoped coverage for `?id=` byte-identity against the on-disk record, unknown-id
      honest-null, `id`+`date` refusal, `integrity_errors` on both run-ledger GETs (planted corrupt
      record file in a scoped dir — never `apps/backend/.data`), a SHA-256 before/after listing of
      every universe/screen/topup-run/reconcile-run file proving nothing was backfilled or rewritten,
      MCP `desk_screen` no-arg proxy unaffected, `get_endpoint` proxies `?id=` verbatim, the 17-tool
      contract unaffected.

### Frontend
- [ ] `/desk` Screen History rows (`page.tsx` history render + `handleSelectHistoryScreen` ~:1553):
      select by the row's own `meta.id` (not `screen_date`) and fetch
      `GET /research/desk/screen?id=`; each history entry displays its own `created_utc` beside its
      `screen_date` so two same-date entries read distinctly.
- [ ] `/desk` Screen History highlighting (`page.tsx` ~:537, currently
      `selected={meta.screen_date === selectedDate}`): highlight by the displayed snapshot's own
      `id`, so two same-date entries are each independently, distinctly highlighted.
- [ ] `/desk` Provenance panel (`DeskProvenance`, `page.tsx:890`): render the displayed snapshot's
      own `id` and `created_utc` (both already carried by `DeskScreenSnapshot`, `lib/types.ts:838` —
      a straight re-format, nothing derived); default-view copy describes itself as the most
      recently RECORDED screen (`created_utc`-sorted `latest`), never "the latest screen date".
      Copy stays descriptive measurement only (no advice/imperative/urgency/prediction language).
- [ ] `/desk`: render an honest count-plus-filename `integrity_errors` line for each of the four
      ledger sections (Universe, Screen History, Top-up Runs, Index Reconciliation) whenever that
      ledger's own payload carries any — today rendered for none of the four.
- [ ] `lib/api.ts` / `lib/types.ts`: thread the `?id=` query param and the new
      `integrity_errors: {file: string; error: string}[]` field through the typed client for all
      four ledger reads.

### New user-facing capability
The operator can open ANY individually-recorded screen snapshot from the history list — including
an earlier same-date recording superseded by a later one — and see exactly which snapshot (by id
and recorded-at time) is on screen; any ledger's own file-integrity problem is now visibly disclosed
instead of silently dropped.

### New information displayed
Displayed-snapshot `id` and `created_utc` in the Provenance panel; per-history-row `created_utc`;
a count-plus-filename integrity-error line for each of the four ledgers when present.

### New user actions
Click any history row (now keyed by id, not date) to view that exact recording, including a
same-date sibling that was previously unreachable through the UI.

### UI surface changes
Screen History list (id-based select + highlight + `created_utc`), Provenance panel (+`id`,
+`created_utc`), all four ledger sections (+integrity-error line). No new page, no new nav row.

### Product surface delta
`/desk`'s existing sections become fully addressable and self-auditing — nothing new is computed,
but every already-recorded record becomes reachable and every ledger's own honesty channel becomes
visible on screen.

### Blueprint conformance
Desk section of the Information Architecture (`runs/goal-session-desk/state/blueprint.md`) — no new
home; this iteration extends the already-registered `/desk` canonical home's Screen History list,
Provenance panel, and all four ledger sections. A J-12 row was added to the blueprint's Feature/
journey homes table, and the "Screen snapshots, rank rows, skip rows" / "Top-up run records" /
"Coverage-index reconciliation run records" Data-Contract rows each gained an iter-16 addition note
(this is documentation, not new build scope). No nav-skeleton change; no reapproval file needed.

### Data-contract additions
None — every change here is an ADDITIVE extension of an already-registered Data-Contract row,
already recorded in `blueprint.md`:
- `GET /research/desk/screen?id=<snapshot id>` — a new READ PARAM on the already-registered "Screen
  snapshots, rank rows, skip rows" row (`desk_screen.ScreenStore` stays the only owner,
  `GET /research/desk/screen` the only serving endpoint); response shape identical to the existing
  `latest`/`?date=` full-snapshot shape.
- `integrity_errors: [{"file": str, "error": str}]` — an additive field on the already-registered
  "Top-up run records" row (`GET /research/desk/topup/runs`) and "Coverage-index reconciliation run
  records" row (`GET /research/desk/coverage/reconcile/runs`), verbatim from each store's own
  `.list()` `errors` return — same key/shape the screen/universe rows already expose.
No new module, no new route, no new `Config` field, no new MCP tool.

## OUT OF SCOPE

- Any new page or nav row.
- Any change to the rank key, the 5-pin snapshot key, or any recorded row's stored content.
- Repairing, rewriting, or deleting a record that fails verification — a corrupt file is only ever
  NAMED via `integrity_errors`, never fixed, never removed.
- A CLI warmer for the `?id=` read (it is a GET; no compute is involved, unlike J-02/J-03).
- Non-blocking backlog items from iterations 13-15 not named in J-12's own steps (badge overlapping
  "AAPL" letters in demo frames, unbounded run-table length, keyboard access for history rows) —
  these stay backlogged, except the "same-day screens indistinguishable by date-only lookup" item,
  which J-12 IS the fix for.
- Any WRITE to `apps/backend/.data` for evidence capture — this journey triggers no compute and
  persists nothing; browser evidence for the same-date pair may read the ambient store directly or
  a read-only `cp -a` copy of it, and the corrupt-record test plants its file in a SEPARATE scoped
  store dir, never in `apps/backend/.data`.

## DEFINITION OF DONE

- [ ] J-12 passes via browser-qa-agent
- [ ] Required-still-passing journeys (J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11) remain
      green (deterministic replay + LLM fallback — mechanically verified)
- [ ] No anti-goal violation introduced — single source of truth holds (zero new value/owner/
      endpoint), snapshots stay append-only and unedited, every run stays an explicit operator act
      (this iteration triggers none), the briefing stays descriptive-only
- [ ] A `[NEW]`-flagged demo-narrator walkthrough (`Demo Verdict: RECORDED` + a non-empty gallery
      directory, never a same-named replay script) covers reaching a same-date recorded snapshot
      end to end
- [ ] Full backend suite green; `Config().config_fingerprint()` prints `08e471b10130e1e2`; MCP tool
      count is exactly 17; zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
      `StructureChart.tsx`/`desk_coverage.py`; `tests/test_copy_discipline.py` green unmodified
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-16-dev.md`

## TESTING REQUIREMENTS

- Browser: J-12 (screen-history two same-date entries individually reachable/highlighted with a
  legible coverage-badge difference; Provenance panel shows displayed snapshot's own `id` +
  `created_utc`; corrupt-record integrity-error line visible on screen; demo-narrator walkthrough).
  Regression smoke: J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11.
- Unit/integration: `desk_screen.py` `?id=` branch (byte-identity, unknown-id, `id`+`date` refusal),
  `desk_routes.py` `integrity_errors` on both run-ledger GETs, MCP `desk_screen`/`get_endpoint`
  proxy behavior, SHA-256 before/after listing of every universe/screen/topup-run/reconcile-run file
  on disk.
- Error cases: unknown `id` → honest `{"screen": null}` HTTP 200 (never 404); `id` and `date`
  together → honest 4xx refusal; a corrupt run-record file → named in `integrity_errors`, excluded
  from `runs`/`latest`, never repaired or deleted.

Test-first contract:

- TC-1: given two screen snapshots already recorded for the same `screen_date` under different
  `bar_store_signature`s (the real `screen-2026-07-27-936543601e75` / `screen-2026-07-27-3ad3c57aa6ba`
  pair, read against the ambient store or a read-only copy of it), when a client calls
  `GET /research/desk/screen?id=<the earlier id>`, then the response body is byte-identical to that
  id's own file on disk (same `id`, `screen_date`, `as_of`, `rows`, `skipped`).
- TC-2: given the same store, when a client calls `GET /research/desk/screen?date=2026-07-27` (no
  `id`), then the response still serves only the later recording (`matching[-1]`) — unchanged from
  before this iteration.
- TC-3: given no snapshot recorded under a given id, when a client calls
  `GET /research/desk/screen?id=does-not-exist`, then the response is `{"screen": null}` at HTTP 200.
- TC-4: given a request supplying both `?id=` and `?date=`, when the request is made, then the
  server returns an HTTP 4xx response naming that only one of the two may be supplied.
- TC-5: given a `TopupRunStore` whose `.list()` returns one or more `errors` (a planted corrupt
  record file in a scoped store dir, never `apps/backend/.data`), when a client calls
  `GET /research/desk/topup/runs`, then the response body carries
  `integrity_errors: [{"file": <filename>, "error": <message>}, ...]` naming that file, and the
  corrupt record is absent from both `runs` and `latest`.
- TC-6: given the same setup for the coverage-index reconciliation store, when a client calls
  `GET /research/desk/coverage/reconcile/runs`, then the response carries the equivalent
  `integrity_errors` entry and the corrupt record is absent from `runs`/`latest`.
- TC-7: given the running backend, when the MCP `desk_screen` tool is called with no arguments, then
  its JSON is byte-identical to `GET /research/desk/screen`'s no-param response, and when
  `get_endpoint` is called with path `/research/desk/screen?id=<id>`, then its JSON is byte-identical
  to the direct curl equivalent.
- TC-8: given `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` contract, when the full
  backend suite runs, then the tool count is exactly 17.
- TC-9: given a real browser on the T-9 clean-rebuilt `/desk` page pointed at a store carrying the
  same-date pair, when the operator opens the Screen History list, then both same-date entries are
  shown with distinct `created_utc` values and are each independently selectable, not both
  highlighted together for the same date.
- TC-10: given the operator selects the earlier of the two same-date entries, when the page renders,
  then the ranked table shows its own rows (NFLX's `1d` coverage badge dark) and the Provenance
  panel names that entry's own `id` and `created_utc`.
- TC-11: given the operator then selects the later of the two same-date entries, when the page
  renders, then the ranked table shows that snapshot's own rows (NFLX's `1d` coverage badge lit) and
  the Provenance panel updates to that entry's own `id` and `created_utc`.
- TC-12: given the default `/desk` load with no history selection, when the Provenance panel
  renders, then its description reads as the most recently recorded screen, never "the latest screen
  date".
- TC-13: given a planted corrupt run-record file in a scoped Top-up Runs store dir, when the operator
  opens `/desk`'s Top-up Runs section, then a count-plus-filename integrity-error line is visible on
  screen and captured in a screenshot.
- TC-14: given the full backend suite runs after this iteration's changes, when
  `Config().config_fingerprint()` is read, then it prints `08e471b10130e1e2`, and a diff of
  `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/`desk_coverage.py`
  against the pre-iteration tree is empty.
- TC-15: given a SHA-256 checksum listing of every universe/screen/topup-run/reconcile-run file on
  disk taken before this iteration's changes land, when the same listing is taken after the
  iteration completes, then every checksum is identical.
- TC-16: given the demo-narrator lane runs at full depth (before scoring), when it records the
  `[NEW]`-flagged J-12 walkthrough, then the resulting artifact shows `Demo Verdict: RECORDED` with
  a non-empty screenshot gallery narrating: opening the history list, selecting the earlier same-date
  entry, selecting the later same-date entry, and reading the integrity-error line.

## NOTES

- Applied lessons: iter-12/iter-13 (a `[NEW]`-flagged demo-narrator walkthrough clause forces `full`
  depth — the demo-narrator lane runs after scoring at `lean`); iter-9/iter-14/iter-15 (state, in the
  browser-QA dispatch itself, which store root each lane serves against — never let the report's
  prose be the only evidence of isolation; the corrupt-record test's scoped dir must be independently
  confirmed, not merely claimed); iter-13 second entry (a screenshot's bytes prove the STATE, not
  which lane captured it — attribute captures by report narrative plus an independent check).
- Assumption ledger entry logged separately by this run (see
  `runs/goal-session-desk/state/assumptions.md`, `## iter-16 — goal-decomposer`): goal.md names an
  `?id=` refusal for `id`+`date` together but does not specify the HTTP status; any honest 4xx is
  acceptable (422 to match FastAPI's own validation-refusal convention elsewhere in this router is
  the natural choice, but the acceptance text does not pin the exact code).
- The five owner-facing, non-blocking follow-ups from iteration 15's eval.md remain open by choice
  and are not this iteration's concern: two same-day screens indistinguishable by date-only lookup
  is EXACTLY what this iteration fixes; keyboard access for history rows and the eight-stacked-
  section page length stay backlogged.
