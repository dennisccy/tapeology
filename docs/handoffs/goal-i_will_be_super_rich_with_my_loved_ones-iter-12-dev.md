# goal-i_will_be_super_rich_with_my_loved_ones-iter-12 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-12
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

Target journey **J-51** — the persistent Journal list surface + restart honesty. Lean iteration,
read-only over the existing v4 schema (no schema change; `journal_schema_version` stays **4**).

### Backend
- **`JournalStore.list_theses(...)`** — a read-only LIST query over the persisted `theses` rows:
  filters `ticker` / `setup_type` / `direction` / `resolution` / `status`, plus `limit`/`offset`,
  ordered **newest-declared-first** (`created_wall_ts DESC, id DESC`). Returns the SAME
  `ThesisRecord` shape `get_thesis` returns — ONE owner over persisted rows, nothing recomputed.
  `resolution` and `status` both filter the same persisted terminal-status column (a resolution IS
  the terminal status); supplying both ANDs them.
- **`JournalStore.list_row_context(ids)`** — the per-row context the row projection needs, in TWO
  bulk reads (no N+1): the VERBATIM `evidence` of each thesis's last appended verdict event (the
  persisted expired/interruption/resolution reason) + entry/exit mark presence. Pure read.
- **`app/research/journal_rows.py` → `journal_row(...)`** — the SINGLE journal-row projection
  function (mirrors `marks.py`'s single-owner discipline). Builds the compact row from a persisted
  record only: id, ticker, bound source, `data_feed`, `config_fingerprint`, setup, direction,
  declared logical + wall ts, status, resolution (null while active), verbatim resolution reason,
  `has_entry`/`has_exit`. Grade/reviewed fields are **absent** (honest omission — they land with
  J-56/J-57).
- **`GET /research/journal`** — the ONLY serving path for journal rows. Filters server-side; unknown
  ENUM filter values (`setup_type`/`direction`/`resolution`/`status`) → **422** (never coerced);
  `ticker` is free-form (unknown ticker matches nothing, never an error). Page size is
  **config-owned, serving-only**: omitted `limit` → `journal_list_default_limit`; `limit` above
  `journal_list_max_limit` → **clamped** (a safety bound, never a 422).
- **`config.py`** — added `journal_list_default_limit` (50) and `journal_list_max_limit` (200), both
  **excluded from `config_fingerprint`** with the documented rationale next to the existing
  exclusions (a serving page size touches no persisted research value; including it would dishonestly
  fragment the analytics pools).
- **`taxonomy.py`** — added `statuses` (active + the four resolutions) and the `resolutions` subset,
  with display copy, to `GET /research/taxonomy`, so the journal table + filters are
  taxonomy-driven (the frontend hardcodes no status/resolution label).
- **Restart path verified (not rebuilt)** — iter-9's `expire_stale_actives` + the registry startup
  sweep: an UNMARKED previously-active thesis expires with its explicit interruption reason on
  reopen; an ENTRY-MARKED active survives as active-but-not-evaluated (J-47). No gap found, no fix
  needed.

### Frontend
- **`components/NavBar.tsx`** — the persistent app-level nav (layout-mounted): **Cockpit (`/`) ·
  Journal (`/journal`)** as active links + **Studies** as a DISABLED, non-navigable item (its page
  lands with J-60 — the approved skeleton carries no dead link). Active-link highlight via
  `usePathname`. Dark instrument-panel style.
- **`app/layout.tsx`** — mounts `<NavBar/>` above every page (the first multi-page surface). The
  cockpit stays one screen below it.
- **`app/journal/page.tsx`** — the `/journal` page: fetches taxonomy (labels) + `GET /research/journal`
  rows, handles **loading / error / empty** states, re-fetches server-side on filter change (no
  client-side filtering).
- **`components/JournalTable.tsx`** — renders rows VERBATIM: declared date (**dd-MM-yyyy** via the one
  shared `formatDateDMY`), ticker, bound source, data feed, setup, direction, status/resolution chip
  (terminal-red treatment for invalidated/expired), the verbatim expired/interruption reason, and an
  entry-marked indicator. Honest empty state ("No theses journaled yet"). Rows are NOT links
  (`/journal/[id]` ships with J-54/J-55).
- **`components/JournalFilterBar.tsx`** — ticker / setup / direction / status-resolution controls
  driving server-side re-fetch; all option labels from the taxonomy.
- **`components/ThesisStrip.tsx`** — coherence cleanup: replaced the `⚠` emoji prefix on the
  risk-flag chip label with a **class-based amber left-accent rule** (consistent with the cockpit's
  text/class-based design system). No other strip change (the J-47 `⏸` not-evaluated chip is out of
  scope and untouched).
- **`lib/types.ts`**, **`lib/api.ts`** — `JournalRow` / `JournalFilters` types, taxonomy
  `statuses`/`resolutions`, and `fetchJournal(filters)` (the single read path; surfaces the backend
  422 detail verbatim).

## Files Changed
- `apps/backend/app/config.py` -- journal-list page-size config + fingerprint exclusion
- `apps/backend/app/research/store.py` -- `list_theses` + `list_row_context` read queries
- `apps/backend/app/research/journal_rows.py` -- NEW: the single journal-row projection
- `apps/backend/app/research/routes.py` -- `GET /research/journal` list endpoint
- `apps/backend/app/research/taxonomy.py` -- status/resolution display-label enums in the payload
- `apps/backend/tests/test_research_store.py` -- list query + restart-simulation tests
- `apps/backend/tests/test_journal_list.py` -- NEW: list endpoint (filters/pagination/422/clamp/reason)
- `apps/frontend/components/NavBar.tsx` -- NEW: persistent nav top bar
- `apps/frontend/app/layout.tsx` -- mount the NavBar
- `apps/frontend/app/journal/page.tsx` -- NEW: the /journal page
- `apps/frontend/components/JournalTable.tsx` -- NEW: the journal table
- `apps/frontend/components/JournalFilterBar.tsx` -- NEW: the filter controls
- `apps/frontend/components/ThesisStrip.tsx` -- emoji → class-based risk-flag indicator
- `apps/frontend/lib/types.ts` -- JournalRow / JournalFilters / taxonomy statuses+resolutions
- `apps/frontend/lib/api.ts` -- `fetchJournal`

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **494 passed, 1 skipped** (the skip is the pre-existing credentialed live-integration test;
no failures). `journal_schema_version` confirmed still 4.

New tests:
- `test_research_store.py`: `list_theses` empty/ordering/filters(all)/combined-AND/pagination/verbatim;
  `test_resolved_thesis_timeline_byte_identical_across_reopen`;
  `test_unmarked_active_expires_with_reason_on_reopen_then_sweep`.
- `test_journal_list.py`: empty rows; newest-first + verbatim shape + grade/reviewed absent;
  played_out + verbatim reason; expired + verbatim interruption reason; entry-marked presence;
  filters (ticker/setup/direction/status/resolution); 422 on unknown enum (parametrized);
  unknown-ticker-is-not-an-error; pagination; default-page-size; limit-above-max-clamped; taxonomy
  owns status/resolution labels.

Frontend build: `cd apps/frontend && NEXT_DIST_DIR=.next-qa npm run build` →
**Compiled successfully + type-checks clean**; routes `/` (12.3 kB), `/journal` (2.46 kB) emitted.

## Live verification (content canary + restart leg, REST)
Ran a real backend (uvicorn) against a temp journal DB on a test port:
1. Watched `SIM-BUYER`, declared trend_continuation/long, let the verdict publish
   (`pending → confirming`), resolved **played_out** — captured `GET /research/journal/{id}` baseline.
2. Declared a second active thesis (no mark).
3. `GET /research/journal` → newest-first; resolved row `played_out` with its verbatim reason; active
   row `resolution: null`. Both rows share an **identical `config_fingerprint`** (proves the new
   page-size fields are correctly excluded).
4. **Restarted the backend against the same DB** (server-freshness content canary:
   `GET /research/journal` → 200 with rows). After restart: the unmarked thesis reads **`expired`**
   with the verbatim "expired on restart" interruption reason; the resolved thesis still reads
   **`played_out`**; `GET /research/journal/{id}` is **byte-identical** to the pre-restart baseline
   (`before == after` → True; timeline `['pending','confirming','played_out']`).
5. Filters round-trip server-side (resolution=played_out / expired return the matching row;
   setup=absorption_reversal → empty); `status=zombie` → **422**; `ticker=NOPE` → **200** empty.
6. Frontend started against this backend: `/journal` and `/` both serve **200** with the persistent
   nav (Cockpit · Journal · Studies); no errors in the dev log.

All test servers (uvicorn + next dev and their children) were killed afterward; temp journal DB removed.

## Known Issues
- The full-page browser render of `/journal` rows (data fetched client-side at runtime) is the
  browser-QA step's job — dev verified the data path end-to-end via the live REST content canary and
  confirmed both pages serve with the nav. No blocker.
- `/journal/[id]` review-detail page and row links are deliberately out of scope (J-54/J-55) — rows
  are intentionally not links (no dead link). The detail REST endpoint already exists and was used
  here only for the byte-identity probe.
- The upstream FULL-pipeline harness halt at `qa_complete` remains open — depth stays lean per the
  iter spec; this iteration adds no engine/classifier/provider/chart/schema change.
