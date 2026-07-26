# goal-desk-iter-5 Dev Handoff

**Phase:** goal-desk-iter-5
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete (evidence-only iteration — see "What Was Built" for scope)

## What Was Built

This iteration is **verification-only** per the iter spec (`docs/phases/goal-desk-iter-5.md`):
zero product code changes. `/desk` (J-04) was fully built in iter-4; iter-5 owes ONLY the
browser-evidence gap (Run Screen running + a second click refused, plus fresh empty/populated
shots + the first `/desk` golden replay script). That browser pass itself is
`browser-qa-agent`'s deliverable (the spec's own "QA / Evidence" section says "Dispatch
browser-qa-agent" — not a developer action). My scope was the "Backend" section's prep work:

- **Confirmed zero production diff** on every named module (`desk_universe.py`,
  `desk_coverage.py`, `desk_topup_compute.py`, `desk_screen.py`, `desk_screen_compute.py`,
  `desk_routes.py`, `bars.py`, `meta.py`) and on `apps/frontend/` as a whole — see "Zero-diff
  verification" below. I made no edits to any of these files.
- **Built and TWICE end-to-end verified** a fixture-scoped backend setup script:
  `apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh`. This is the one new file this
  iteration adds. It seeds a fresh temp root (never `apps/backend/.data/`) with the committed
  103-member universe fixture + the two committed PG bar fixtures, rebuilds the derived
  `bar_index.db` from them (coverage/screen reads ONLY the index, never the store — T-4), exports
  the 6 spec-named `TAPEOLOGY_*` env vars (+1 bonus, see below), and execs
  `scripts/start-backend.sh` on the given port.
- **Ran the full backend suite** and confirmed the floor + pin (see "Suite" below).
- **Did NOT** touch any browser, write `reports/phase-goal-desk-iter-5-ui-test-results.md`, or
  record `runs/goal-session-desk/journey-scripts/J-04.json` — those are `browser-qa-agent`'s job
  (TC-1..TC-6). Writing a golden script or a "screenshot" claim without a live browser pass would
  repeat exactly the iter-3/iter-4 fabrication pattern the lessons warn against.

## Files Changed

- `apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh` — NEW. Fixture-scoped backend
  setup/launch script for the browser-QA pass (see "How to use this script for the actual pass"
  below). Lives under `apps/backend/scripts/` — the project's OWN script tree — deliberately NOT
  under `scripts/` (a symlink into the vendored `incredible_auto_dev/` framework tree that gets
  content-synced from upstream and must never carry project-specific QA tooling; I initially wrote
  it there by mistake and relocated it before finishing).

No other file was touched.

## Zero-diff verification

```
$ git diff --stat HEAD -- apps/backend/app/research/desk_universe.py \
    apps/backend/app/research/desk_coverage.py apps/backend/app/research/desk_topup_compute.py \
    apps/backend/app/research/desk_screen.py apps/backend/app/research/desk_screen_compute.py \
    apps/backend/app/research/desk_routes.py apps/backend/app/research/bars.py \
    apps/backend/app/meta.py
(empty — zero changed lines)

$ git diff --stat HEAD -- apps/frontend/
(empty — zero changed lines)
```

## Suite

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1328 passed, 8 skipped, 0 failed** (matches the DoD floor exactly; no regressions).

`Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged pin, confirmed live).

`GET /meta/ui-routes` served verbatim from `UI_ROUTES` (`app/meta.py:31-35`) → exactly
`/` (Cockpit), `/structure` (Structure), `/desk` (Desk) — 3 entries, confirmed by reading the
module (byte-unchanged) and by live curl against the scoped backend (see below).

I did not re-run the Playwright deterministic-replay lane for J-07 myself (that lane boots the
real frontend+backend and is normally forked by `goal-iter-lean.sh`/dispatched to
`browser-qa-agent`, not the developer step). Since `apps/frontend/` has zero diff this iteration
and J-07's golden asserts against `/`, `/structure`'s AAPL 2026-06-22 Load, and post-match
liveness — none of which any file this iteration touches affects — J-07 should replay exactly as
before. TC-9 remains the replay lane's own job to execute and report.

## The fixture-scoped setup script — verified twice, live

I ran the script end-to-end TWICE against two different fresh roots (ports 8301 and 8302), each
time bracketing the run with a full `apps/backend/.data/` listing (`path|mtime|size`, 389 entries
both times) taken immediately before launch and immediately after teardown. **Both diffs were
empty — zero new or modified files anywhere under `apps/backend/.data/`.** I also confirmed the
two ambient journal DBs outside `.data/` (`apps/backend/journal.db`,
`apps/backend/tapeology_journal.db`) were untouched (identical mtime+size before/after), because
`main.py`'s `lifespan` opens a `JournalStore` at `TAPEOLOGY_JOURNAL_DB`/`journal_db_path_resolved()`
on every startup regardless of whether any desk route is ever hit — a bonus scoping the spec
doesn't literally require (TC-7 only measures `.data/`) but the "never touch the ambient store"
lesson (iter-4 entry 2) clearly intends.

**Exact env vars the script exports** (all six the spec names, plus one bonus):

```
TAPEOLOGY_DESK_UNIVERSE_DIR=<root>/universe
TAPEOLOGY_BAR_DIR=<root>/bars
TAPEOLOGY_DESK_SCREEN_DIR=<root>/screen
TAPEOLOGY_DATASET_DIR=<root>/datasets
TAPEOLOGY_BAR_INDEX_DB=<root>/bar_index.db
TAPEOLOGY_DATASET_INDEX_DB=<root>/dataset_index.db
TAPEOLOGY_JOURNAL_DB=<root>/journal.db          # bonus, not spec-named, see above
```

**Live behavior confirmed against the scoped backend** (both verification runs, ports 8301/8302):

- `GET /research/desk/universe` → the 103-member fixture snapshot, `universe-2026-07-25-817cc184bbb3`.
- `GET /research/desk/screen` on a FRESH (never-triggered) root → `{"screens":[],"latest":null,"integrity_errors":[]}`
  — the exact honest empty payload TC-1 needs.
- `GET /research/desk/coverage` → 200 OK for all 103 members; PG alone shows
  `has_bars:true` for `1h` (latest `2026-06-09T21:00:00Z`) and `1d` (latest `2026-06-06T00:00:00Z`);
  every other member shows `has_bars:false` on all 4 timeframes (`1h`/`4h`/`1d`/`1w`) — the two
  committed bar fixtures are BOTH for symbol **PG** (not AAPL/MSFT as `iteration-state.md`'s
  "active blockers" note loosely implied), so PG is the only member with any coverage at all.
- `POST /research/desk/screen/compute {"screen_date":"2026-07-26"}` → `started:true`, a job that
  reaches `state:"done"` in **single-digit milliseconds** (mostly-`no_bars` universe, tiny fixture
  set) with `members_total:103`.
- The resulting screen: **1 ranked row** (PG — `band_class:"C"`, `distance_bps:322.10`,
  `band_score:35.0`, `side:"support"`) and **102 skipped rows** (`reason:"no_bars"`), provenance
  `universe_snapshot_id:"universe-2026-07-25-817cc184bbb3"`, `config_fingerprint:"08e471b10130e1e2"`,
  `bar_store_signature` present. I derived this number myself, live, against the exact fixture
  basis named above — per the iter-3 lesson, do not carry it forward without re-deriving; PG's
  fixture bars end `2026-06-09`, so any `screen_date` on/after `2026-06-10` should reproduce the
  SAME row (no-lookahead means the reference price is PG's last completed bar regardless of which
  later date is requested), but re-verify this against whatever `screen_date` the browser actually
  submits (the UI submits the client's own "today" — see the timing note below for why this
  matters more than it looks).

## CRITICAL for browser-qa-agent: the "running" state is real but SHORT — plan the click sequence around it

The backend compute above finishes in ~6-10ms against this fixture set (only PG has bars; the
other 102 members resolve to `no_bars` almost instantly). A naive assumption would be "too fast to
screenshot" — **that is not the risk.** I read `apps/frontend/app/desk/page.tsx`: the Run Screen
button's `disabled`/`"Computing…"` state is driven by React state (`screenCompute`) that is set
IMMEDIATELY from the `POST` response itself (which synchronously returns `state:"running"` before
the background job even starts), and is only ever corrected by the poll `useEffect` at
`page.tsx:667-687`, which polls every **700ms** (`setInterval(..., 700)`). So regardless of how
fast the backend actually finishes:

- The button reliably shows `"Computing…"` / disabled / `data-testid="desk-screen-compute-running"`
  for close to the full 700ms after the click, because nothing corrects the client's belief until
  the next poll tick lands.
- **TC-2's screenshot** (running + disabled) and **TC-3's second-click-refused screenshot** are
  both comfortably capturable in that window — click, screenshot immediately, attempt the second
  click immediately (no artificial wait needed, and no risk of the window closing before you act).
- Do NOT add a `wait_for` before the TC-2/TC-3 screenshots that's long enough to cross 700ms, or
  you will screenshot the already-`"done"` state and reproduce iter-4's original gap. Assert the
  running state RIGHT after the click action, then re-check liveness (lesson (d)), then proceed.

## How to use this script for the actual browser-QA pass

```
# 1. Pick a FRESH root — NOT either of the two I used for verification (both now have 2 and 1
#    recorded screen snapshots respectively, so TC-1's empty state would not render on them):
ROOT=/var/tmp/<something-new>/desk-iter5-browser-qa
PORT=8301

# 2. Launch (backgrounds itself via your own job control; the script's last line execs uvicorn
#    in the foreground, so run it with your shell's background/job tooling, not inline):
bash apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh "$ROOT" "$PORT"   # (in background)

# 3. Wait for "Application startup complete." in its log, THEN warm up before opening the browser
#    (lessons iter-0 entry 2's precedent — avoids a cold-first-call surprise):
curl --max-time 30 http://localhost:8301/research/desk/coverage >/dev/null

# 4. Start the frontend pointed at this backend (the established :8301/:3301 QA-rig convention):
CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh   # (in background)

# 5. Take the "before" apps/backend/.data/ listing NOW (immediately before opening the browser):
find apps/backend/.data -exec sh -c 'stat -c "%n|%Y|%s" "$1"' _ {} \; | sort > before.txt

# 6. Open Chrome at http://localhost:3301, drive TC-1..TC-5, capture screenshots + record
#    runs/goal-session-desk/journey-scripts/J-04.json with post-match liveness steps.

# 7. Take the "after" listing and diff against before.txt — MUST be identical (TC-7). Escalate
#    per the spec's NOTES ("second attempt... a pattern, not a fluke") if it is not.

# 8. Tear down both processes cleanly (kill the uvicorn/next PIDs) before finishing.
```

## Known Issues

- **The `iteration-state.md` "AAPL/MSFT bars" phrasing is imprecise.** The two committed bar
  fixtures are both for symbol PG, not AAPL/MSFT. This does not block anything — it just means the
  populated-briefing screenshot (TC-4) will show exactly ONE ranked row (PG) and 102 skipped rows,
  not a multi-symbol ranked table. That is the honest, correct rendering of this fixture basis; do
  not treat a single-row table as a bug.
- **I did not personally execute the browser pass, write `ui-test-results.md`, or record
  `J-04.json`.** These remain fully outstanding and are the explicit next step
  (`browser-qa-agent`), not a gap in this handoff.
- **The human-call item is unchanged and unresolved by this iteration** (as the spec's NOTES
  say it should be): `docs/goal.md` still lists `bars.py` + `StructureChart.tsx` as untouched for
  the era; both were changed under iter-4's developer-written spec amendment. I did not touch
  either file this iteration and did not attempt to resolve the ratification question — that
  decision belongs to the project owner.
- **`reports/qa/goal-desk-iter-4-qa.md` remains discredited and untouched**, per the spec's
  explicit instruction not to cite or "fix" it.
