# goal-playbook-iter-10 Dev Handoff

**Phase:** goal-playbook-iter-10
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

## What Was Built

**A. Spec catch-up, doc-only, zero code diff (R-3.2(a)/(c)/(d)/(e)).** `docs/playbook-detector-spec.md`
rewritten in four places to match the shipped code, per the owner's R-3 ruling (`docs/goal.md`):
- §3.8 Caps line (mirrors §3.9 by the file's own convention): now states the shipped
  `_find_double_extreme` reading verbatim — every confirmed-pivot pair `(p1, p2)` is searched in
  chronological order and the FIRST pair whose full formation validates AND triggers wins.
- §3.3 body + the `PLAYBOOK_JUMP_MIN_MULT` constants-table row: annotated that the BOOK 1.5x
  jump-to-base ratio gate is mathematically dominated by `PLAYBOOK_JUMP_MIN_MOVE_MBR`/
  `PLAYBOOK_BASE_MAX_RANGE_MBR` (1.5 x 2.0 = 3.0 = the floor) and has never independently rejected
  a formation (min observed ratio across the 32 recorded `jbe`/`dbi` signals: 1.735).
- §3.6: the left-rim "near session-high-so-far" test now names `PLAYBOOK_NEAR_EXTREME_MBR`
  (matching `desk_playbook_detect.py:677`), not `PLAYBOOK_RIM_MATCH_MBR`; the rim-to-rim test
  keeps `RIM_MATCH_MBR` unchanged.
- §3.7 Trigger clause: narrowed to name `b` as the arming-completing touch specifically (the LAST
  of the `>= 2` touches the Arming clause requires), matching `_range_trade_side`'s own
  `b = armed_touches[-1]` anchor.

Every one of these four edits is confirmed doc-text-only: `git diff` on `desk_playbook_detect.py`
shows ZERO lines touched by any of them (verified below, TC-1..TC-4). R-3.1 (the degenerate-trigger
clause) needed no action — already ratified and shipped.

**B. The one new disclosure, spec-first (R-3.2(b)).** `docs/playbook-detector-spec.md` §3.7's
Disclosures clause was split BEFORE any code change into two named fields: `crossed_midrange`
("did price cross the range midpoint on the approach") and a new `turned_at_midrange` ("whether
the prior swing turned at midrange, the BOOK midrange rule"), with `turned_at_midrange`'s own
mechanical bar-by-bar definition written into the spec first (TC-5).

Implemented in `_range_trade_side` (`apps/backend/app/research/desk_playbook_detect.py:1068`):
`geometry.turned_at_midrange` is computed over the SAME approach window `crossed_midrange` already
reads (`session_bars[armed_touches[0] : b+1]`) — the swing's own extreme in that window (`max(high)`
long / `min(low)` short: the furthest point price reached before returning to complete the arming
touch `b`) is compared against the range midpoint, and the field is `True` when that distance is
`<= PLAYBOOK_RANGE_HOLD_TOL_MBR * MBR` (this detector's own existing "held" tolerance, reused
verbatim — no new constant, matching R-3.2(b)'s binding constraint). It is disclosure-only (never
gates/suppresses/creates a signal), lookahead-clean (reads only bars at-or-before `b`, the same
discipline `crossed_midrange` already uses), computed for both long and short sides, and optional
in the payload (absent, never `null`, on every record recorded before this field shipped). The
escape hatch was NOT needed — the definition above ships without minting any new constant.

**C. Two carried test/fixture defects, zero product-code diff.**
- `runs/goal-session-playbook/journey-scripts/J-10.json` step 6: the fixture-rebuild-dependent
  hash `9597251432bd9e75` (introduced by an iter-9 edit; `git log -p` confirms the value was
  `"Forward Returns"` from iteration 0 through iteration 4) is reverted to `"Forward Returns"` —
  a static string on the ALREADY-shipped `/desk` Forward Returns panel title.
- `apps/backend/scripts/seed_playbook_iter8_replay_rig.py`: `_copy_kept_symbol_series` copies
  AAPL's real bar files but never updated the scoped rig's `bar_index.db`, so
  `GET /research/bars?symbol=AAPL` (what `/structure`'s chart fetches) resolved through
  `BarIndex.list()` and saw nothing even though the file was physically present. Fixed by calling
  the existing `desk_index_reconcile.run_reconcile` (the sole `BarIndex.reindex()` repair path)
  right after the copy step, via a new `_reindex_copied_series` helper. Verified live against a
  freshly-seeded scratch rig (bypassing any live port): the AAPL copy went from 151 series copied /
  0 indexed to 151/151 indexed (`rows_indexed_before=0`, `rows_indexed_after=171` across the whole
  rig — the one non-AAPL gap is a PRE-EXISTING, out-of-scope `BSCAN` same-window double-record in
  `seed_playbook_iter7_backscan_fixture.py`, unrelated to this fix and unrelated to J-10's own
  AAPL/`/structure` requirement).

## Files Changed

- `docs/playbook-detector-spec.md` — §3.3, §3.6, §3.7 (Trigger + Disclosures), §3.8 Caps line, §1
  constants table (`PLAYBOOK_JUMP_MIN_MULT` and `PLAYBOOK_RANGE_HOLD_TOL_MBR` rows) — R-3.2(a)-(e)
- `apps/backend/app/research/desk_playbook_detect.py` — `_range_trade_side`: adds
  `geometry.turned_at_midrange` (13 lines; zero other lines in this 1526-line file touched)
- `apps/backend/tests/test_desk_playbook_detect.py` — a `turned_at_midrange` True fixture + its
  near-miss control (single-variable-controlled, the file's own convention), plus one new
  assertion each on the two pre-existing canonical long/short fixtures
- `apps/backend/tests/test_desk_playbook.py` — extends the signature-liveness counter-test (TC-9,
  both directions: the reused constant moves params+signature; untouched reproduces the
  byte-identical pre-monkeypatch value) and adds TC-8 (a pre-iteration-10-style record serves
  geometry with the key absent, HTTP 200)
- `apps/backend/scripts/seed_playbook_iter8_replay_rig.py` — indexes the copied AAPL series via
  `desk_index_reconcile.run_reconcile` (new `_reindex_copied_series` helper + two new imports)
- `apps/backend/tests/test_seed_playbook_iter8_replay_rig.py` (new file) — smoke check proving the
  index gap and its repair, isolated from the rest of the seed script's heavy fixture chain
- `apps/frontend/lib/types.ts` — `DeskPlaybookGeometry` gains `turned_at_midrange?: boolean`
  beside `crossed_midrange?: boolean`
- `apps/frontend/app/desk/page.tsx` — one new conditional chip in the existing `range_trade`
  geometry line (`desk-playbook-signal-range-trade-geometry`), same idiom as the existing chips
- `runs/goal-session-playbook/journey-scripts/J-10.json` — step 6 expect text reverted to the
  static `"Forward Returns"` string

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest -p no:warnings`
Result: **2168 passed, 8 skipped, 0 failed, exit 0** (199.83s). Clears the 2163-test floor; skip
count stays 8. Five new tests added (one in `test_desk_playbook_detect.py`, one in
`test_desk_playbook.py`, three in the new `test_seed_playbook_iter8_replay_rig.py`), plus two new
assertion lines added to two already-passing tests.

`Config().config_fingerprint()` → `08e471b10130e1e2`, unchanged.

`git diff` confirmed EMPTY (zero lines) for every file this iteration must not touch:
`desk_forward.py`, `desk_playbook_evidence.py`, `app/mcp/__init__.py`, `desk_playbook.py` (no
constant or `playbook_parameters()` change), `config.py`, `meta.py`.

Frontend: `npx tsc --noEmit` → zero errors.

`tests/test_copy_discipline.py` → 30/30 pass (the new " · turned at midrange" chip text is clean:
no advice/imperative/prediction/probability/edge/significance language).

## Live verification (dev-level; browser-qa-agent still owns the formal J-06/J-10 browser pass)

- **Seed-script fix, standalone (no live port touched):** ran
  `seed_playbook_iter8_replay_rig.py` directly against a fresh scratch root (env vars pointed at
  a scratchpad directory, matching `qa_playbook_iter7_fixture_scoped_backend.sh`'s own env-var
  wiring, minus the final `start-backend.sh` line) — `"copied 151 kept-symbol series verbatim...
  AAPL"` immediately followed by `"reconciled bar_index.db: 0 -> 171 rows indexed (172 series on
  disk)"`. Direct inspection: `BarIndex(...).list(symbol="AAPL")` returns all 151 AAPL series;
  `BarStore(...).list()` reports 0 errors and byte-identical checksums before/after reindexing.
- **Real backend, read-only:** started the operator's real backend/frontend
  (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/dev.sh`) — both healthy
  (`GET /health` 200, `GET /` 200), restarted once more to confirm clean port-conflict handling
  (new PIDs took over cleanly, no duplicate listeners). `GET /research/desk/playbook?id=` on the
  REAL record carrying signature `16a2734d10c91ea7` (the exact signature `docs/goal.md`'s R-3.1
  names for the 87 real `range_trade` signals) confirms live: `turned_at_midrange` key absent,
  `crossed_midrange` present, HTTP 200 — the honest-absence design proven against real data, not
  only a synthetic fixture. `GET /desk` on the real frontend returns 200 with no error banner.
  Only read-only GETs were issued against the real backend; `.data/` has zero files modified in the
  last 30 minutes (`find .data -newermt "-30 minutes"` empty), confirming the store-scope
  discipline held throughout.
- **Not run by this agent:** the Chrome-MCP/`demo_runner.py` golden-replay lane against the
  scoped rig, and the fresh `/structure`/`/desk` screenshots the phase spec's DEFINITION OF DONE
  requires for J-06/J-10. That is explicitly the browser-qa-agent's own pipeline stage per this
  phase's own division of labor ("J-06 passes via browser-qa-agent", "J-10 passes via
  browser-qa-agent"); this handoff's dev-level evidence (above) is offered as a head start, not a
  substitute.

## Known Issues

- **The seed-script fix indexes 171 of 172 on-disk series, not 172.** The one gap is `BSCAN`,
  which `seed_playbook_iter7_backscan_fixture.py` (unmodified by this iteration, out of scope)
  records twice under the IDENTICAL `(symbol, timeframe, window_start_utc, window_end_utc, feed)`
  key — `BarIndex`'s own primary key collapses two `series_id`s sharing that key down to whichever
  `insert()` ran last (`INSERT OR REPLACE`, documented as the index's own self-heal semantics).
  This predates this iteration (it was simply invisible before, since nothing was indexed at all)
  and does not affect AAPL or J-10's own `/structure` requirement; not fixed here as it is outside
  this iteration's IN SCOPE list and outside `_copy_kept_symbol_series`'s own code path.
- **No fresh browser screenshot accompanies this handoff.** Per the "Live verification" section
  above — deferred to browser-qa-agent by design, not an oversight. Per this iteration's own NOTES,
  any browser evidence captured before both B (the field's code) and C (the seed-script fix) landed
  must be treated as voided; since both landed together in this same dev pass, the NEXT capture
  will already be fresh against both fixes at once.
- **Depth-arbiter outcome is unknown to this agent.** The phase spec's own NOTES section discloses
  that the engine's `CHAIN_FULL_CADENCE_CAP` may demote this iteration's requested `full` depth to
  `lean` regardless of the spec's `Full trigger: 1`; this developer dispatch does not control or
  observe that decision, and every DEFINITION OF DONE item above is written (and was implemented)
  to hold under either depth.

## Environment

**State at handoff: real backend (`:8301`) and real frontend (`:3301`) both healthy**, matching
the dispatch note's "already prepared, keep it that way" instruction. Restarted once during this
session (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/dev.sh`, twice in
succession to prove clean port takeover) — both confirmed healthy after each restart. Chrome CDP
`:9222` was left untouched (still the pre-existing isolated headless instance). The operator's real
`apps/backend/.data/` store was never written to by this session — only read-only GETs were issued
against `:8301`, and the seed-script verification ran against a scratch root, never a live port.

To stand the scoped rig up for the browser-qa-agent's own pass:

```bash
bash apps/backend/scripts/start_scoped_qa_backend.sh   # swaps :8301 to the scoped fixture rig
# ... browser/replay work (this now includes indexed AAPL bars for /structure) ...
CHAIN_BACKEND_PORT=8301 bash scripts/start-backend.sh   # restore the operator's real backend after
```

---

## Fix Notes (fix pass 1 — `reports/reviews/goal-playbook-iter-10-review.md`, verdict FAIL)

**Scope: the review's ONE issue.** `runs/goal-session-playbook/journey-scripts/J-10.json` step 6.
No other file was touched in this pass — the review confirmed every other item (the four doc-only
spec edits with git-diff-proved zero code change, the `turned_at_midrange` disclosure, the
seed-script `bar_index` repair, the suite at 2168/8/0, the fingerprint, `tsc --noEmit`) as correct.

### What the review said, and what the live rig actually does

The review's CRITICAL finding was that step 6's `"Forward Returns"` renders only inside
`DeskPopulatedScreen` (gated on `latest !== null`), that no fixture in the scoped rig ever records
a desk screen, and that the assertion would therefore **time out deterministically**.

The gating half is exactly right, and I re-confirmed it live rather than taking it on trust — but
**the predicted failure mode is wrong, and the truth is worse.** Verified against a freshly-seeded
scoped rig (`start_scoped_qa_backend.sh` → `assert_scoped_qa_backend.py` reports
`SCOPED … source_url='fixture-rig-iter8-replay'`; `GET :8301/research/desk/screen` returns
`{"screens":[],"latest":null,…}`, so `DeskNotComputedPanel` renders and the Forward Returns
`Panel` never mounts — the served `/desk` HTML contains zero occurrences of the exact panel title
`Forward Returns`, against 2 for `Index Reconciliation` and 2 for `Screen Runs`):

`page.get_by_text("Forward Returns")` **matches, and is visible — 1 match, on a `<p>`, not the
panel.** Playwright's `get_by_text` does *case-insensitive substring* matching, and the
refresh-chain explainer inside `DeskNotComputedPanel` contains the prose
"…that day's screen followed by its own **forward returns**." (`page.tsx:4446-4455`). So step 6 as
written does not time out; it **passes vacuously against unrelated body copy**, while appearing to
guard a panel that is not on the page at all. It would keep passing if the Forward Returns section
were deleted outright — a silent sentinel, which is precisely the iter-9 lesson this fix exists to
close. (This also explains the history the earlier dev pass found: the string genuinely asserted
the panel in iterations 0-4, when the replay lane still ran against the operator's real backend,
where a screen exists. The store-scope guard landed at iteration 9 and force-swapped the lane onto
the fixture rig; the assertion silently stopped meaning anything then, rather than failing.)

### The fix

Step 6's expect now targets a section that is rendered **outside** the screen-state ternary, and
two sibling assertions were added so the sentinel covers all three of the always-rendered kept
Era-B ledger sections rather than one (TC-12 asks for "a kept Era-B heading"; each is a `Panel`
`<h2>` title in static JSX, present in the server-rendered HTML, independent of every fetch result):

| step | action | expect |
|---|---|---|
| 6 | `goto /desk` | `"Top-up Runs"` |
| 7 | `wait_for` text | `"Index Reconciliation"` |
| 8 | `wait_for` text | `"Screen Runs"` |

Steps 7-8 use the `wait_for`-target + step-level `expect` idiom already used by `J-08.json` step 2.
`"Playbook Signals"` (the review's own suggestion) was rejected on purpose: it is an Era-B2 section
this era itself added, and J-10 is the *kept-product* sentinel — J-01/J-03/J-06 already assert it.

### Why the replacement is not vacuous (negative control, run live)

Loaded `/desk` on the rig, removed the three shipped sections from the DOM
(`section[aria-label="Top-up runs" | "Index Reconciliation" | "Screen Runs"]`, 1 node each), and
re-ran the same locator each assertion uses:

```
before removal   'Top-up Runs' 2 matches · 'Index Reconciliation' 1 · 'Screen Runs' 2 · 'Forward Returns' 1
after  removal   'Top-up Runs' 0 matches · 'Index Reconciliation' 0 · 'Screen Runs' 0 · 'Forward Returns' 1 (still matching the refresh-chain prose)
```

Every match of the three chosen strings lives inside the section it names (the `<h2>` title plus,
for two of them, that section's own "No … runs recorded yet." empty-state copy), so deleting the
section drops the assertion to zero matches and step 6/7/8 fail. The old string does not — the
control is the direct proof of the vacuousness above.

### Verification

- `demo_runner.py --mode lint` over all nine goldens (J-01…J-08, J-10): **9 ok, rc 0**.
- `demo_runner.py --mode verify --journeys J-10 --base-url http://localhost:3301` against the
  freshly-seeded scoped rig: **PASS, rc 0** — "journey replayed end-to-end; all expects held", all
  eight steps including the cockpit SIM-BUYER watch, the `/structure` pinned-AAPL Load asserting
  `300.11`, and the three new `/desk` assertions. End-state screenshot opened and read (not just
  filed): the `/desk` not-computed state, with the refresh-chain paragraph carrying the "forward
  returns" prose visible in-frame.
- Store-scope guard around the whole browser pass: baseline 9841 files over the 12 protected
  paths → **verified CLEAN, zero delta**; `find apps/backend/.data -newermt "-90 minutes"` empty.
- **State-independence check (the property the old assertion lacked).** After restoring the
  operator's real backend on `:8301` (`assert_scoped_qa_backend.py` → `NOT SCOPED …
  source_url='https://en.wikipedia.org/wiki/S%26P_100' (member_count=101)`, i.e. the genuine
  store), a **read-only page load of `/desk` — zero clicks, zero fills, no compute control
  touched** — re-ran the same three locators against the fully POPULATED desk state
  (`latest !== null`, so `DeskPopulatedScreen` renders):

  ```
  'Top-up Runs' 1 match (H2, VISIBLE) · 'Index Reconciliation' 1 (H2, VISIBLE) · 'Screen Runs' 1 (H2, VISIBLE)
  'Forward Returns' 2 matches here (H2 panel + the same refresh-chain prose)   ← renders only in this state
  'Screen Comparison' 1 · 'Provenance' 1 · 'Desk screen not computed yet' 0    ← the state really is the other one
  ```

  So the three chosen strings hold in BOTH desk states — computed and not-computed — while
  `"Forward Returns"` is exactly the string whose match SOURCE flips with fixture state. A second
  store-scope snapshot/verify wrapped this probe: **CLEAN, zero delta**, `.data` untouched.
- Full backend suite re-run after the fix (this pass changes no Python/TypeScript, so it is a
  no-regression confirmation): `.venv/bin/python -m pytest -p no:warnings -q` → **exit 0, 2168
  passed / 8 skipped / 0 failed**, unchanged from the pre-fix run. (Counted directly from the
  progress markers — 2168 `.` + 8 `s` — because pytest's one-line summary does not land in the
  redirected non-tty log; same counting method the reviewer used.) `Config().config_fingerprint()`
  → `08e471b10130e1e2`, unchanged.

### Files changed in this pass

- `runs/goal-session-playbook/journey-scripts/J-10.json` — step 6's expect text; steps 7-8 added.

### Environment state at the end of this fix pass

Both services were **already down** when this pass started (`curl` on `:8301` and `:3301` both
returned `000`, no `uvicorn`/`next` process alive) — the previous pass's servers did not survive
its dispatch. Restored and left healthy:

| Port | What is on it now | Check |
|---|---|---|
| `:8301` | the operator's **REAL** backend (`CHAIN_BACKEND_PORT=8301 bash scripts/start-backend.sh`, detached) | `GET /health` **200**; `assert_scoped_qa_backend.py` reports NOT SCOPED / 101 real members, as it should |
| `:3301` | frontend dev server (`next dev`, `NEXT_PUBLIC_API_URL=http://localhost:8301`) | `GET /` **200**, `GET /desk` **200** |
| `:9222` | untouched — the pre-existing isolated headless Chrome | not used by this pass (the replay lane launches its own Playwright chromium) |

The scoped fixture rig was stood up on `:8301` for the browser verification above and then taken
back down; `no npm run build` was run (the dev server's `.next` was never rebuilt or deleted). The
browser-qa lane does not need the rig pre-started — `store_scope_require` stands up a fresh one
itself, which is also what this iteration's NOTES want (a rig seeded AFTER both of this
iteration's fixes). To do it by hand: `bash apps/backend/scripts/start_scoped_qa_backend.sh`, then
`CHAIN_BACKEND_PORT=8301 bash scripts/start-backend.sh` to put the real backend back.

### Known issues from this pass

- None new. The three assertions cover the always-rendered kept sections only; **Screen History,
  Forward Returns, the ranked briefing, Skipped Members, Screen Comparison and Provenance
  structurally cannot be asserted by a deterministic replay on this rig**, because no fixture
  records a desk screen and they are all gated on `latest !== null`. J-10's acceptance line for
  those sections stays with the browser-qa-agent's own walk. If the era ever wants them under
  deterministic replay too, the honest fix is a fixture that records a screen — not a string that
  happens to match something else on the page.
