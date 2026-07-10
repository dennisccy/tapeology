# goal-yahoo_fetch-iter-5 Dev Handoff

**Phase:** goal-yahoo_fetch-iter-5
**Date:** 2026-07-10
**Agent:** developer
**Status:** complete

## Context: this iteration's work was found already drafted, uncommitted

Before touching anything, `git status` showed all eight of this iteration's target files already
modified in the working tree (uncommitted): `apps/backend/app/research/taxonomy.py`, `routes.py`,
`tests/test_research_api.py`, `tests/test_bars_api.py`, and the four frontend files
(`lib/api.ts`, `lib/types.ts`, `components/FeedBasisBadge.tsx`, `app/structure/page.tsx`). HEAD
(`d8190dd`, iter-4) has no trace of these changes, and `runs/goal-yahoo_fetch-iter-5/status.json`
was stuck at `current_step: "test_plan_generated"` with no dev handoff on disk — so this is the
same pattern iter-4's own handoff documented (an interrupted prior attempt at this exact iteration,
this session having hit interactive-quota throttling before; see the project's own memory notes).
Per the developer agent's initial-build mode, I did not blindly trust the draft: I independently
verified every claim below (read every diff line-by-line against the plan, ran the full test
suite, re-ran engine equivalence, checked the config fingerprint, type-checked the frontend, and
drove the real running app through a live browser session) before treating it as complete. I did
not need to write new production or test code — the existing draft matched the plan precisely and
needed no fixes.

## What Was Built

**Backend (small, additive, exactly per plan):**
- `apps/backend/app/research/taxonomy.py` — added `"yahoo": "Yahoo Finance"` to
  `FEED_BASIS_LABELS`. `taxonomy_payload()` already builds `feed_basis.feeds` from this dict, so
  `GET /research/taxonomy` serves `{"id": "yahoo", "name": "Yahoo Finance"}` with no route change.
  `config.py` untouched.
- `apps/backend/app/research/routes.py::list_bar_series` — closed audit carry-forward **B2**: the
  blank-string normalization (`symbol.strip().upper() if symbol else None` /
  `timeframe.strip() if timeframe else None`) now runs **before** the
  `normalized_symbol is None and normalized_timeframe is None` short-circuit, instead of after it.
  Previously a blank `?symbol=` (present but empty) fell through to `index.list(None, None)`
  (index-only), silently missing any series the index never learned of. Now it takes the exact
  same byte-identical `store.list()` path as a true no-param call. The real-filter path
  (`?symbol=PG&timeframe=1d` etc.) is unchanged — this is a 3-line reorder, not new logic.

**Frontend (`/structure` gains its one new explicit write action):**
- `apps/frontend/lib/api.ts` — new `recordBarSeries()` POST helper (`POST /research/bars`),
  modeled on the existing `createStudy` pattern: returns `{ok:true, bar_series}` or
  `{ok:false, status, error}` with the backend's own detail string surfaced verbatim.
- `apps/frontend/lib/types.ts` — new `RecordBarSeriesResult` interface for the helper's return
  shape.
- `apps/frontend/components/FeedBasisBadge.tsx` — widened the `dataFeed` prop from the narrow
  union `"sim"|"iex"|"sip"|null|undefined` to `string|null|undefined`, so the SAME component
  renders any registered feed id (including `"yahoo"`) via its existing taxonomy-lookup logic —
  no new component, no new fetch, no per-feed branch added.
- `apps/frontend/app/structure/page.tsx` — new "Fetch from Yahoo Finance" section above the
  existing read-only Load form: symbol (`SymbolSearch`, reused), a timeframe `<select>` offering
  exactly the six era-5 Yahoo-supported values (`1w 1d 4h 1h 5m 1m` — `15m`/`8h`/`1mo` deliberately
  excluded, a display choice, not a second validation authority), start/end ISO datetime inputs,
  and the "Fetch from Yahoo Finance" button (disabled until all four fields are set). On submit:
  POST via the new helper, then — on success — seed `symbolInput`/`asOfInput` from the response
  and call the EXISTING `handleLoad()`, so the already-built Levels & Zones section (chart +
  `ZoneRow` table) renders the real Yahoo data with zero new rendering code and zero client
  recomputation. The provenance badge (`FeedBasisBadge`, keyed off the charted series' own `feed`
  field) renders beside the chart. A POST failure surfaces the backend's own 422/503/504/409
  `detail` string verbatim via the existing `UnavailablePanel` treatment; a fetched symbol with no
  bars falls through to the pre-existing `structure-no-bar-series` empty state — no new empty-state
  component was needed because the fetch simply feeds the already-tested J-04 state machine.

## Files Changed

- `apps/backend/app/research/taxonomy.py` -- `+6/-0` lines: `"yahoo": "Yahoo Finance"` entry +
  doc comment.
- `apps/backend/app/research/routes.py` -- `+12/-4` lines: B2 reorder in `list_bar_series`
  (~line 1712-1732), doc comment expanded. No other route logic touched.
- `apps/backend/tests/test_research_api.py` -- `+4/-1` lines: `test_taxonomy_serves_feed_basis_copy_canary`
  now expects `{"sim","iex","sip","yahoo"}` + asserts `labels["yahoo"] == "Yahoo Finance"`.
- `apps/backend/tests/test_bars_api.py` -- `+37` lines: new test
  `test_blank_symbol_param_is_byte_identical_to_no_param_even_with_an_unindexed_series` — seeds an
  **un-indexed** record directly via `BarStore.record()` (bypassing `index.insert()`), then proves
  `?symbol=`, `?timeframe=`, and both-blank all return byte-identical JSON to the no-param call,
  including that un-indexed record. This is the proof B2 is actually closed, not just reordered
  without effect.
- `apps/frontend/lib/api.ts` -- `+41` lines: `recordBarSeries()`.
- `apps/frontend/lib/types.ts` -- `+12` lines: `RecordBarSeriesResult`.
- `apps/frontend/components/FeedBasisBadge.tsx` -- `+11/-3` lines: widened prop type + doc comment.
- `apps/frontend/app/structure/page.tsx` -- `+181/-9` lines: fetch-control section, state, submit
  handler, badge wiring, updated page-level doc comments.
- `docs/handoffs/goal-yahoo_fetch-iter-5-dev.md` -- new (this file).
- `docs/handoffs/goal-yahoo_fetch-iter-5-frontend.md` -- new.
- `reports/phase-goal-yahoo_fetch-iter-5-implementation-summary.md` -- new.

**Confirmed zero diff** (`git diff --stat` on each, independently re-checked): `research/levels.py`,
`research/backtests.py`, `research/strategies.py`, `config.py`, `research/bars.py`,
`research/bar_index.py`, `providers/adapters/` (both Yahoo and Alpaca), the tape engine,
`app/mcp/__init__.py`, `requirements.txt`, `config/install-security-policy.json`. No file outside
the plan's list was touched.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=<path>`
Result: **1207 tests, 0 failures, 0 errors, 6 skipped** (junit-xml is authoritative — same
sandbox quirk iter-4 noted where the plain-text `-q` summary line doesn't print to stdout). This is
the iter-4 baseline (1206) plus this iteration's one net-new test (the B2 byte-identity proof) —
**zero regressions**.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_bars_api.py tests/test_research_api.py -v`
Result: **54 passed** — includes the new B2 test and the updated taxonomy canary, and confirms the
two tests the plan required to "stay green unmodified"
(`test_symbol_and_timeframe_filter_returns_only_the_matching_series`,
`test_no_param_get_is_byte_identical_to_a_direct_store_list_call`) both still pass.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`
Result: **22 passed** (J-06's engine-equivalence guard).

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `4d665603569b9dbf` (unchanged, as expected — `config.py` has a zero diff).

Command: `cd apps/frontend && npx tsc --noEmit -p tsconfig.json`
Result: **exit 0, zero errors** — the new `recordBarSeries` wiring, the widened `FeedBasisBadge`
prop, and the new fetch-control section (including its `React.FormEvent` handler, which follows
the exact same no-explicit-import precedent already used by `handleSubmit`/`handleComparisonSubmit`
on this same page and by `ThesisStrip.tsx`/`TopBar.tsx`) all type-check cleanly.

Command: `grep -rn "Yahoo Finance" apps/frontend --include="*.ts" --include="*.tsx"` (excl. `.next`)
Result: 9 hits, all either code comments or the fetch-control's own UI copy (panel title, section
`aria-label`, button label, descriptive prose) — **zero** hits inside `FeedBasisBadge.tsx` itself.
See "A note on the 'no hardcoded Yahoo Finance' check" below for why this is the correct outcome.

### Live verification against the real running app (not just tests)

Started the real app (`bash scripts/dev.sh`; backend `:8301`, frontend `:3301`). Both came up
cleanly (`Application startup complete`, Next.js `Ready in ~1.2s`), health-checked `200` on both.

- `curl http://localhost:8301/research/taxonomy` — `feed_basis.feeds` includes
  `{"id":"yahoo","name":"Yahoo Finance"}` live, alongside `sim`/`iex`/`sip`.
- `curl http://localhost:8301/research/bars` vs `curl "http://localhost:8301/research/bars?symbol="`
  — byte-identical live (diffed the two response bodies directly), confirming B2 against the real
  server, real `.data/bars/` directory (8 pre-existing real `feed="yahoo"` series from prior
  iterations), not just the test client.
- **Browser walkthrough** (Chrome MCP): navigated to `/structure`, confirmed the new "Fetch from
  Yahoo Finance" panel renders above the Load form with the correct fields (Symbol / Timeframe
  select / Start / End) and a disabled button until all four are filled — visually consistent with
  the page's existing dark instrument-panel style (same `Panel`, same `INPUT_CLASS`, same button
  classes as the Load/Run-comparison controls). Filled `symbol=AAPL, timeframe=1d,
  start=2026-06-01T00:00:00Z, end=2026-07-09T23:59:59Z` (a window already stored + indexed from a
  prior iteration) and clicked **Fetch from Yahoo Finance**: backend log showed
  `POST /research/bars HTTP/1.1" 200 OK` (not `409`) immediately followed by the existing
  `GET /research/bars` / `GET /research/levels` / `GET /research/taxonomy` reads — the Levels &
  Zones section populated with real candles (a 2028-bar 5m series), real level lines, a real
  confluence-zones table (Class A, score 32, cross-timeframe members at `273.75` across
  `1d/1h/1w/4h/5m`), and the provenance badge read **"feed Yahoo Finance"** above the chart —
  sourced from `GET /research/taxonomy`, not a literal. This is the exact end-to-end J-05 flow,
  observed live, not only inferred from unit tests.
- Stopped both services (`scripts/dev.sh`'s known cleanup gap reproduced again — see Known Issues),
  confirmed both ports fully free (`lsof`/`ss`), restarted from clean, re-confirmed both healthy
  with no port conflicts, then did a final thorough stop (verified `lsof`/`ss`/`ps` all empty for
  both ports before finishing).
- Did not exercise a live cache-miss Yahoo network fetch through the new control (out of scope per
  the plan/spec — that path is `integration`-marker-gated on `TAPEOLOGY_LIVE_INTEGRATION=1`, and
  the browser leg is specified to verify the store-first/no-network path only).

All server processes were killed before finishing this handoff.

## A note on the "no hardcoded Yahoo Finance" check

The plan and phase spec both include a `grep -r "Yahoo Finance" apps/frontend` check. Two different
things are being asked for by the surrounding documents, and they point in opposite directions if
read too literally:

- `docs/goal.md`'s Vision and Key Capability 5, and the phase spec's own IN SCOPE section, **name
  the button text verbatim**: "clicks **Fetch from Yahoo Finance**" / a "**'Fetch from Yahoo
  Finance'** button" — this is human-authored, mandated UI copy for the button/section, not a
  data-contract value.
- The DoD's anti-hardcode bullet is specifically about the **provenance badge** — the label that
  stamps a *bar series' feed* — which must come from `GET /research/taxonomy`, never be typed by
  the frontend.

I kept the implementation as found: the button label, the panel title ("Fetch from Yahoo
Finance"), the section `aria-label`, and the descriptive prose all say "Yahoo Finance" as static
product copy (matching goal.md's own mandated wording verbatim), while the actual provenance
**badge** (`FeedBasisBadge`, rendered beside the chart) has **zero** hardcoded occurrences of the
string anywhere in its source — it reads the label from `taxonomy.feed_basis.feeds` keyed by the
served `feed` value, confirmed both by reading the component and by the live browser check above
(the badge rendered "Yahoo Finance" for a `feed:"yahoo"` series pulled off a real API response).
Rewording the button to avoid the literal string would contradict goal.md's own explicit copy
mandate, which I treated as the higher-priority, human-authored constraint. Flagging this
explicitly so the reviewer/auditor can independently confirm the distinction rather than being
surprised by the grep's raw hit count.

## Known Issues

- **`scripts/dev.sh`'s `pkill`/PID-based stop does not reliably kill the full `next dev` child
  process tree** — the same finding iter-3 and iter-4 flagged, reproduced a third time here: after
  `pkill -f "next dev -p 3301"`, the `npm exec` → `sh -c` → `node next-server` descendants
  (multiple generations deep) stayed bound to port 3301 until I killed each surviving PID
  explicitly and re-verified via `lsof`/`ss`. Pre-existing gap in `scripts/dev.sh` itself, not
  touched this iteration (out of scope) — flagged again since it will keep surprising future
  dev/QA cycles that rely on the script's own Ctrl+C handler or a simple `pkill`.
- **The browser lane's exact pre-seed fixtures are narrower than the real dev data I used.** The
  plan names two specific committed fixtures (`AAPL_1d_20260601_20260604.json`,
  `AAPL_1h_20260601_20260603.json`, proven in iter-4 to yield 14 levels / 4 class-B zones) for the
  browser-qa-agent to seed via the store-first POST path or `reindex()`. My own live verification
  above used the broader, already-indexed real `AAPL 1d 2026-06-01..2026-07-09` series already
  present in `.data/bars/` from earlier iterations (also a genuine store-first `200`, also real
  levels/zones/badge) rather than the two narrow fixtures — a valid proof of the same mechanism,
  but not a substitute for the browser-qa-agent seeding the exact fixture tuple the spec names if
  it wants the exact "14 levels / 4 zones / score 12.0" result reproduced.
- **B1 (mixed-feed pooling avoided by scoping, not enforced) is unchanged** — carried forward from
  iter-4, explicitly out of scope this iteration (would require mutating frozen, fingerprint-locked
  `research/levels.py`). Still true: a symbol that accumulates both a `feed="yahoo"` and a
  `feed="sip"` series over overlapping timeframes would have them pooled into one confluence
  cluster by the feed-blind `compute_levels`. J-05's "honestly segregated" acceptance is met at the
  fetch/store/display layer (a distinct, separately badged, never-re-tagged append-only record) on
  a single-feed (Yahoo-only) path, per the iter-5 assumption-ledger entry already logged in
  `runs/goal-session-yahoo_fetch/state/assumptions.md`.
- No frontend test runner exists in this repo (confirmed again: no `test` script in
  `apps/frontend/package.json`, no `.test.ts(x)` files) — consistent with every prior iteration,
  frontend behavior is verified via TypeScript compilation (clean) plus the live/browser checks
  above and the downstream browser-qa-agent's own pass.
