# goal-i_will_be_super_rich_with_my_loved_ones-iter-2 Execution Plan

Thesis declaration with honest validation (J-38 + J-39). First `/research/*` API namespace,
first persistence (journal-scoped SQLite), first research surface (cockpit thesis strip).
Depth: full. The verdict stays honestly `pending` this iteration — the verdict transition
engine (J-40–J-46) is NEXT iteration. Builds on the iter-1 observer seam
(`add_observer` / `observer_failed` / `on_event` / `on_status` on `TapeEngine`).

## What to Build

- **Research config + fingerprint** (`app/config.py`): env-configured journal DB path
  (temp-path injectable for tests via the existing dependency-override pattern) and a
  `config_fingerprint()` hashed over the ENTIRE frozen config (classifier + research values).
  No research literal outside config.
- **Taxonomy module + `GET /research/taxonomy`** — single backend owner of every research
  label: 4 setups (`absorption_reversal`, `trend_continuation`, `level_break`,
  `failed_move_fade`) with per-setup level requirements (REQUIRED for `level_break` +
  `failed_move_fade`'s level pair per spec — exactly: level REQUIRED for the two level
  setups, FORBIDDEN otherwise), expected-behaviour statement templates, direction + verdict
  enums with display copy. Frontend hardcodes none of it.
- **Journal store (SQLite, scoped)** — stdlib `sqlite3` only: WAL, `busy_timeout`,
  `BEGIN IMMEDIATE`, ONE writer queue (writes never happen on the event-processing or WS
  serialization path). Create the FULL versioned schema now (theses, verdict_events, hints,
  actions, studies, study_occurrences, schema_version); only `theses` + `verdict_events`
  are written this iteration. Repository exposes NO update/delete on `verdict_events`.
  No tape data persisted.
- **`POST /research/thesis`** — honest validation, never coercion: 404 not-watched; 409
  active thesis exists; 422 wrong-side invalidation (long ⇒ invalidation must be below
  current last; short ⇒ above), missing level for level setups, forbidden level for
  non-level setups, unknown enums. Nothing persisted on rejection. On success: freeze entry
  context (state, confidence, last, spread, primary-window features) + derived
  expected-behaviour statements; bind to SOURCE IDENTITY (the snapshot's scenario
  descriptor — sim scenario / exact historical window / live SYMBOL — never the bare
  ticker); stamp bound source + `data_feed` (`sim|sip|iex`) + `config_fingerprint`; record
  the initial `pending` verdict event (timeline starts here); return the full projection.
- **`GET /research/thesis/active?ticker=`** — canonical REST read; `thesis: null` is a
  normal state. MUST equal the WS frame's `thesis` key verbatim (data-contract row 15).
- **Research monitor** attached via the observer seam, exception-isolated: holds the active
  thesis per ticker, recomputes statement live statuses (met / not-yet / violated) per event
  from EXISTING engine states/features only, serves the projection (thesis fields, statement
  statuses, verdict fixed at `pending`, `monitor_status`). Read-only over the engine — zero
  engine/classifier/feature/threshold change. SQLite failure ⇒ `monitor_status: failed`,
  feed stays alive.
- **Additive WS `thesis` key** on `WS /tape/{ticker}/stream` — same projection, `null` when
  none. Merge the key at the WS send site (the stream handler in `main.py`), NOT inside the
  engine serializers, so `serialize_stream`/`serialize_history` stay byte-identical
  (equivalence anti-goal).
- **Minimal lifecycle honesty** (deadlock-prevention subset of capability 24): stop /
  stream end / feeder failure auto-resolves an active thesis `expired(reason)` with a final
  timeline event; a startup sweep resolves any DB row left `active` to `expired`. No entry
  marks exist yet, so the survives-with-entry-mark exception is NOT built. Full lifecycle /
  re-attach (J-47, J-50) is later.
- **Equivalence re-proof**: extend `test_observer_equivalence.py` with the REAL research
  monitor attached (no thesis declared) — engine projections byte-identical.
- **Frontend thesis strip** on `/` between the price chart and the panel grid: idle = one
  single-line declare affordance (J-68 strip-idle clause — nothing else moves); declare form
  fully taxonomy-driven from `GET /research/taxonomy`; invalidation price required; inline
  422/409/404 messages straight from the backend; active display = setup, direction,
  invalidation in mono, statements each with a live status, `pending` verdict badge (slate),
  bound source + `data_feed` stamp, `monitor_status: failed` surfaced honestly. All values
  read verbatim from the WS `thesis` key / REST projection — the frontend derives nothing.
- **Copy discipline** (J-66 register): thesis-attributed, present-tense, descriptive; no
  buy/sell/enter/exit imperatives, no prediction/certainty language; "Descriptive only —
  not trading advice" discipline extends to the strip.

## Agents Required

- developer: yes -- backend (config fingerprint, taxonomy, SQLite store + writer queue,
  `/research/*` endpoints, research monitor on the observer seam, WS thesis key, lifecycle
  expiry + startup sweep, full unit-test matrix) AND frontend (ThesisStrip component,
  cockpit mount, API/types/WS wiring). Single developer, both halves in this iteration.
- backend-data: yes -- as above (research namespace, persistence, monitor).
- frontend-ux: yes -- as above (thesis strip idle/declare/active states).

## Frontend Present
yes

## Files to Create/Modify

Backend:
- `apps/backend/app/config.py` -- research config block (journal DB path env, research
  defaults) + `config_fingerprint()` over the entire frozen config.
- `apps/backend/app/research/__init__.py` -- NEW research package.
- `apps/backend/app/research/taxonomy.py` -- NEW: setup catalog, param requirements,
  statement templates, direction/verdict enums + display copy.
- `apps/backend/app/research/store.py` -- NEW: SQLite journal store (WAL, busy_timeout,
  BEGIN IMMEDIATE, single writer queue, versioned full schema, append-only verdict_events
  repository).
- `apps/backend/app/research/monitor.py` -- NEW: research monitor observer (active thesis,
  statement-status evaluation, projection builder, exception isolation, expiry on
  stop/end/failure).
- `apps/backend/app/research/routes.py` -- NEW: `POST /research/thesis`,
  `GET /research/thesis/active`, `GET /research/taxonomy` (router mounted in main.py).
- `apps/backend/app/main.py` -- mount research router; wire store DI + startup sweep in
  lifespan; merge additive `thesis` key into the WS frame at the stream send site.
- `apps/backend/app/watch_manager.py` -- attach the monitor observer on watch creation;
  notify monitor for `expired` resolution on stop / stream end / failure.
- `apps/backend/tests/test_research_api.py` -- NEW: full validation matrix (404/409/each
  422 case both directions), nothing persisted on rejection, taxonomy endpoint, REST==WS
  thesis projection verbatim.
- `apps/backend/tests/test_research_store.py` -- NEW: WAL + writer-queue discipline,
  temp-path injection, schema_version, no update/delete on verdict_events.
- `apps/backend/tests/test_research_monitor.py` -- NEW: frozen entry context + statements
  (config change never rewrites), source binding (scenario descriptor), data_feed +
  fingerprint stamps (stable across runs, changes with any config value), statement
  statuses, observer exception ⇒ `monitor_status: failed` with feed alive, initial
  `pending` event, expired-on-stop + startup sweep.
- `apps/backend/tests/test_observer_equivalence.py` -- extend: real monitor attached
  (benign + throwing), byte-identical projections.

Frontend:
- `apps/frontend/components/ThesisStrip.tsx` -- NEW: idle affordance / taxonomy-driven
  declare form with inline backend errors / active-thesis display.
- `apps/frontend/components/Cockpit.tsx` -- mount the strip between PriceChart and the
  panel grid.
- `apps/frontend/lib/api.ts` -- research calls (taxonomy, declare, active) with error-body
  passthrough for inline messages.
- `apps/frontend/lib/types.ts` -- thesis projection + taxonomy types.
- `apps/frontend/lib/useTapeStream.ts` -- surface the WS `thesis` key.

## UI Evolution

- New user-facing capability: declare a thesis (setup × direction × invalidation) on the
  watched ticker and watch it judged live (starting `pending`); incoherent declarations are
  rejected on-screen with explicit reasons.
- New information displayed: active thesis (setup, direction, invalidation), frozen
  expected-behaviour statements with live met/not-yet/violated statuses, `pending` verdict,
  bound source + data-feed stamp, monitor status.
- New user actions: declare-thesis affordance + form (setup select, direction select,
  invalidation price input, level price input only when the taxonomy requires it, submit).
- UI surface changes: one new strip on the cockpit (`/`) between the chart and the panel
  grid. No new pages.
- Navigation changes: none (Journal/Studies nav arrives with their pages in later
  iterations).

## Visual Requirements

- Component patterns: hand-built panels per the design system (no component library) —
  reuse the existing `Panel` styling conventions for the strip; mono (`font-mono`) for
  invalidation/level/price values; verdict badge as a small slate pill.
- Layout: full-width one-line strip when idle; when declaring/active it expands in place —
  the panel grid below must not reflow when idle (J-68 strip-idle clause).
- Key visual effects: slate-900/60 surface + slate-800 border matching existing panels;
  verdict semantics per design direction (`pending` = slate; green/amber/red reserved for
  later verdicts); statement statuses use the existing side/impact palette (met = emerald,
  not-yet = slate/amber, violated = rose) without repurposing.
- States to handle: idle (single declare line), form open (taxonomy loading + loaded),
  submit rejection (inline 422/409/404 message, form values preserved, nothing created),
  active thesis, `monitor_status: failed` (explicit honest notice), thesis expired on
  stop/stream-end.

## Key Test Scenarios

- **J-38 (browser):** watch `SIM-BIDABS` (persistent absorption state — safe for
  screenshots), declare absorption_reversal / long / invalidation below last via the strip;
  assert ACTIVE thesis with setup/direction/invalidation in mono, statements each with a
  live status, verdict `pending`, no page reload; REST-probe
  `GET /research/thesis/active?ticker=SIM-BIDABS` equals the WS frame's `thesis` key
  verbatim with the server demonstrably up.
- **J-39 (browser):** unwatched ticker ⇒ 404; wrong-side invalidation ⇒ inline message +
  422, nothing created; `level_break` without level ⇒ 422; `absorption_reversal` with
  level ⇒ 422; valid declare then second declare ⇒ 409 with explicit message. Capture
  response evidence (status codes + bodies), not only screenshots.
- **J-68 strip-idle leg:** with no thesis, the cockpit renders identically except the
  one-line declare affordance; spot-check J-17 (chart) and J-19 (pause/resume).
- **Required-still-passing:** J-01–J-09, J-17, J-19, J-21, J-24 spot checks.
- **Unit:** full POST validation matrix; frozen context/statements survive config change;
  source binding + data_feed + fingerprint stamps; store discipline (WAL, writer queue,
  temp path, schema_version, append-only repo); initial `pending` event; stop/stream-end ⇒
  `expired(reason)`; startup sweep; WS thesis key == REST projection; extended equivalence
  test byte-identical (benign + real monitor + throwing observer). Backend suite must stay
  ≥ iter-1's 292 passed / 1 skipped plus the new tests.

## Assumptions (documented, not asked)

- The WS `thesis` key is composed in `main.py`'s stream handler from the monitor projection
  and merged into the dict returned by `serialize_stream` — engine serializers untouched, so
  the existing byte-identity equivalence tests remain valid as written.
- One shared projection function in `monitor.py` feeds both REST and WS, guaranteeing
  verbatim equality by construction.
- The writer queue is a small background worker (thread + queue) owned by the store; the
  monitor enqueues thesis/event writes from observer callbacks and never blocks the feeder.
- Source identity comes from the snapshot's existing `scenario` descriptor field.
- `risk_flags` is omitted from the projection ENTIRELY (no empty list) per the spec's
  honesty rationale.

## Scope Notes

- No scope creep detected: everything maps to goal.md capabilities 23 + 28 (store
  foundation) + the taxonomy endpoint, with the lifecycle-honesty subset of 24 explicitly
  justified by the spec (QA/user deadlock prevention).
- Explicitly OUT: verdict transitions/dwell/`rule_first_true`, entry risk flags (J-49),
  resolve/abandon/action marks/stance (J-50/52/53), chart thesis geometry (J-48),
  `/journal` + `/studies` pages and nav, restart re-attach (J-47/J-51), any
  engine/classifier/feature/threshold change.
- QA harness notes: budget SIM-BIDABS warm-up before declaring; kill the dev frontend by
  port (`fuser -k`), never `pkill -f "next dev"` (iter-0 lesson).
