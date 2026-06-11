# Goal Iteration 12 — Journal list surface + restart honesty (J-51)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 12
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-51
- **Required-still-passing journeys:** J-01, J-02, J-08, J-38, J-42, J-47, J-49, J-50, J-52, J-68
- **Anti-goal reminders:**
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*"
  - "**Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis MUST never be evaluated against a different source than it was declared on; analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*"
  - "**No profitability or edge claims.** No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure. *(critical)*"

## GOAL

The user can open a persistent **Journal** page from the top-bar nav, see every journaled thesis as a filterable row read verbatim from the persisted store, and trust that a backend restart loses nothing and rewrites nothing — flipping **J-51** to passing in pixels.

## BACKGROUND

This is the iter-11 evaluator's mandated next step (depth **lean** — the FULL-pipeline harness defect at `qa_complete` remains open upstream; lean iterations 6–11 produced complete evidence). J-49 and J-50 are green; J-51 is the last open journey in the risk-and-lifecycle-honesty group (J-49–J-51) and its `/journal` page is the binding-build-order prerequisite for review/grading (J-54–J-57). Its hard parts are PRE-BUILT and unit-proven since iter-9: append-only `verdict_events`, `expire_stale_actives` on reopen, entry-marked survival (J-47), and v1→v4 migrations against committed fixtures. What is missing is the **`GET /research/journal` LIST endpoint**, the **top-bar nav**, and the **`/journal` page rows** — plus the browser-verifiable restart leg. The list endpoint is also J-55's groundwork (J-55 itself cannot pass yet: its acceptance requires execution checks, which are J-54, downstream).

Binding lessons applied (state/lessons.md): the journal list must read persisted rows verbatim via **ONE owner** (no recomputation, no second path); `/journal` is a new, below-the-fold page surface — browser-qa must use scroll-into-view/full-page captures and the evaluator opens the PNGs; mandatory pre-capture **server-freshness canary** (restart the QA backend after dev; server start mtime > newest patched file, or a content canary — `GET /research/journal` returning 200 with rows works); `store.py` schema changes need versioned migrations + a committed-fixture check (none expected here — this iteration is read-only over the schema); QA must **diff the executed browser test list against this spec's journey matrix**; never `npm run build` against the live dev server's shared `.next` (use `NEXT_DIST_DIR=.next-qa`).

## IN SCOPE

### Backend
- [ ] `JournalStore` read-only list query (e.g. `list_theses`): filters `ticker`, `setup_type`, `direction`, `resolution`, `status`, plus `limit`/`offset`, ordered newest-declared-first; reads persisted rows verbatim — **no schema change** (`journal_schema_version` stays 4).
- [ ] **ONE** journal-row projection function (single owner, mirroring `build_projection`'s discipline) producing the compact row from the persisted record only: id, ticker, **bound source**, **`data_feed`**, **`config_fingerprint`** stamp, setup, direction, declared logical + wall timestamps, status, resolution **including the verbatim persisted expired/interruption reason**, entry/exit-mark presence. Nothing recomputed at read; grade/reviewed fields are NOT fabricated — they land as additive keys with J-56/J-57 (honest omission, the established absent-vs-empty discipline).
- [ ] `GET /research/journal?ticker=&setup_type=&direction=&resolution=&status=&limit=&offset=` (goal.md API surface) serving those rows — the ONLY serving path for journal rows (Data Contract row 21, journal-rows half). Unknown enum filter values → **422, never silent coercion**; default/max page size is **config-owned** (a serving-only value — exclude it from `config_fingerprint` alongside `journal_db_path` etc., with the rationale documented in `config.py`: it cannot affect any persisted research value, and including it would dishonestly fragment analytics pools).
- [ ] Verify (don't rebuild) the restart path: on store reopen, previously-active **unmarked** theses expire with an explicit interruption reason (iter-9's `expire_stale_actives`); entry-marked actives survive as active-but-not-evaluated (J-47). Fix only if a gap is found.
- [ ] Unit tests: list filtering/pagination/ordering with exact values; empty store → empty list; invalid filter → 422; **byte-identical timeline + row readback across a store close/reopen** (restart simulation) for a resolved thesis; unmarked-active → expired-with-reason on reopen; entry-marked-active survives.

### Frontend
- [ ] Persistent **top-bar nav** (layout-level, per the approved IA skeleton): **Cockpit (`/`) · Journal (`/journal`)**. The **Studies** entry lands together with the `/studies` page (J-60) — the approved skeleton must never carry a dead link.
- [ ] **`/journal` page**: a filterable table rendering `GET /research/journal` rows **verbatim** — columns: declared date (**dd-MM-yyyy via the one shared formatter** in `lib/datetime.ts`), ticker, bound source, data feed, setup, direction, status/resolution (expired rows show the verbatim interruption reason; terminal resolutions get the established terminal treatment). Filter controls (ticker, setup, direction, resolution/status) drive server-side re-fetch — no client-side filtering/derivation; **setup/direction/resolution display labels come from `GET /research/taxonomy` (row 24) — the frontend hardcodes none of them**. Honest empty state ("no theses journaled yet"). Dark instrument-panel style, mono numerics, consistent with the cockpit.
- [ ] Rows are **not yet links** — `/journal/[id]` (the review detail page) ships with J-54/J-55 next; do not render a dead link.
- [ ] Coherence advisory cleanup (evaluator-recommended fold-in): replace the `⚠` emoji prefix in `ThesisStrip.tsx` risk-flag chip labels with a class-based indicator consistent with the cockpit's text/class-based design system. No other strip change.

### New user-facing capability
The first multi-page surface: a persistent Journal page listing every thesis ever declared — resolved, expired, abandoned, and active alike — that survives a backend restart with history intact and honestly labeled.

### New information displayed
Journal rows: declared date (dd-MM-yyyy), ticker, bound source, data feed, setup, direction, status/resolution with verbatim expired/interruption reasons.

### New user actions
Top-bar navigation (Cockpit · Journal); journal filter controls (ticker, setup, direction, resolution/status).

### UI surface changes
New persistent top bar on every page; new `/journal` page (table + filters + empty state); risk-flag chip prefix changed from emoji to class-based indicator.

### Product surface delta
Tapeology stops being a single-screen cockpit and becomes the cockpit + its research record: the journal is now visible, navigable, and restart-proof — the review/grading surfaces (J-54–J-57) and analytics (J-59) will build on this exact page.

### Blueprint conformance
`/journal` and the top-bar **Cockpit · Journal · Studies** nav are ALREADY registered in the approved IA (Journal section; J-51's canonical home is `/journal` → `/journal/[id]`). This iteration builds the registered skeleton — additive build-out, **no nav-skeleton change, no reapproval needed**. The Studies entry is deferred to its page (documented as an additive build-out note in `blueprint.md`).

### Data-contract additions
No new row. The journal-rows half of **existing row 21** ships: ONE row-projection function over persisted theses rows, served ONLY by `GET /research/journal` (an iter-12 additive note is registered on row 21 in `blueprint.md`). All displayed values (resolution, reasons, stamps, dates) are reads of already-registered persisted values — never a second computation or serving path for anything in rows 15–19.

## OUT OF SCOPE

- `/journal/[id]` review detail **page** and a full J-55 pass — J-55's acceptance requires execution checks (J-54), which are downstream; the detail REST endpoint already exists and is used here only for byte-identity probes.
- Execution checks, mistake tags, review flow, grading (J-54, J-56, J-57).
- Analytics view + `GET /research/analytics` (J-59); hint log (J-65).
- `/studies`, the Studies nav entry, study runner, CI timing gate (J-60–J-62).
- Cue layer — entry checklist, stance, hints, feed badge (J-53, J-63–J-67): **binding build order, strictly after J-58–J-62**.
- Any engine / classifier / provider / chart change; any `store.py` schema change.
- Hint-log table writes, reviewed/grade columns, row links — all land with their own journeys.

## DEFINITION OF DONE

- [ ] Target journey J-51 passes via browser-qa-agent, including a harness-performed backend restart mid-journey
- [ ] Required-still-passing journeys remain green (J-01, J-02, J-08, J-38, J-42, J-47, J-49, J-50, J-52, J-68)
- [ ] No anti-goal violation introduced (journal integrity, single source of truth, honesty stamps; no grades/cues/analytics snuck in)
- [ ] Unit tests pass; full backend suite green; no regressions; `journal_schema_version` still 4
- [ ] `blueprint.md` row-21 additive note + IA build-out note registered (done by decomposer, verified in place)
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-12-dev.md`

## TESTING REQUIREMENTS

- Browser (J-51, all legs, with full-page/scroll-into-view captures — `/journal` is below the fold of nothing: it is a NEW page, capture it whole):
  1. Watch `SIM-BUYER`, declare trend_continuation/long, let verdict transitions publish (pending → confirming), resolve **Played out**; capture `GET /research/journal/{id}` (timeline JSON) as the pre-restart baseline.
  2. Declare a second thesis, leave it active, **no entry mark**.
  3. Declare a third thesis and **mark an entry**, leave it active (J-47 leg).
  4. **Restart the backend** (harness-performed — this also satisfies the server-freshness canary; additionally verify server start > newest patched-file mtime or use the `GET /research/journal` 200-with-rows content canary before any capture).
  5. Reload the UI, navigate **via the top-bar Journal link** to `/journal`: the resolved thesis's row shows `played_out`; the unmarked thesis's row reads **expired with its explicit interruption reason**; the entry-marked thesis reads active/not-evaluated honestly — all in opened pixels.
  6. Re-fetch `GET /research/journal/{id}` for the resolved thesis: **byte-identical** to the pre-restart baseline (nothing recomputed at read).
  7. Filters round-trip server-side (e.g. filter by setup or resolution and see the row set change); labels match the taxonomy payload.
  8. One fresh declaration with a firing risk flag to confirm the chip's class-based (non-emoji) indicator (J-49 still green; iter-11 frames may be cited for unchanged legs per lessons — re-stage only what this iteration touches).
  9. Cockpit spot-checks for the required-still-passing set (J-01/J-02/J-08/J-38/J-42 in one cockpit pass; J-68 no-thesis sentinel frame — the new top bar must not disturb the one-screen cockpit).
  10. QA report MUST include a diff of the executed browser test list against this journey matrix.
- Unit/integration: list endpoint filters/pagination/ordering with exact values; invalid enum filter → 422; empty store → empty list; byte-identical readback across store close/reopen; expired-with-reason on reopen for unmarked actives; entry-marked survival; full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`).
- Error cases: unknown enum filter values → 422 (never coerced); limit above the config cap → clamped-or-422 per the documented config choice; `GET /research/journal/{unknown-id}` → 404 (existing behavior unchanged).
- Frontend build: `NEXT_DIST_DIR=.next-qa npm run build` — never against the live dev server's shared `.next`.

## NOTES

- Evaluator mandate (iter-11 eval.md): journal review surface, lean depth; this completes the risk-and-lifecycle group and unblocks J-54/J-56/J-57 per the binding build order. J-55 is deliberately NOT a target: its acceptance clause "execution checks are visible" cannot be satisfied before J-54.
- Single-owner discipline is the audit focus: journal rows must come from ONE projection function over persisted rows and be served ONLY by `GET /research/journal`. Do not re-derive resolution, reasons, stamps, dates, or status anywhere client-side; do not add a second endpoint or reuse `build_projection` for rows in a way that recomputes anything.
- No schema change is expected. If the developer finds one unavoidable, the iter-4 lesson applies in full: bump `journal_schema_version`, in-place `ALTER` in one writer transaction, never backfill append-only rows, prove against a committed old-schema fixture — and flag it in the handoff.
- The FULL-pipeline engine halt at `qa_complete` remains open upstream — depth stays lean.
- Page-size config default is a serving-only value: document its `config_fingerprint` exclusion rationale in `config.py` next to the existing exclusions so the evaluator sees it was deliberate, not forgotten.
