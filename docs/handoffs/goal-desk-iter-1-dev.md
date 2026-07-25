# goal-desk-iter-1 Dev Handoff

**Phase:** goal-desk-iter-1
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

- **Universe vendor seam** (`app/research/desk_universe.py::fetch_constituents_html`) — a plain,
  keyless HTTP GET (via the already-pinned `httpx` client) against the documented Wikipedia S&P
  100 constituents page. Raises the explicit `UniverseFetchError` for any transport failure or
  non-200 response — never a cached or fabricated fallback page.
- **Stdlib-only HTML parser + validation contract** (`desk_universe.py::parse_constituents`) —
  `html.parser.HTMLParser` (no `lxml`/`html5lib`/`beautifulsoup4`/`pandas.read_html`, none of
  which are declared dependencies). Locates the constituents table by header text ("Symbol" or
  "Ticker" — never a hardcoded column index), validates ticker charset `[A-Z.-]{1,6}`, normalizes
  Yahoo-style dual-class tickers (`BRK.B → BRK-B`), retains the raw form per normalized ticker,
  dedupes, sorts, and validates the final member count against `[min_members, max_members]`. Any
  failure (no recognizable table, zero tickers, a charset violation, an out-of-bounds count)
  raises a specific, honest `UniverseValidationError` naming the exact problem — the whole fetch
  is refused, never a partial or guessed list.
- **Three Path-A Config fields** on `Config` (`app/config.py`): `desk_universe_source_url`
  (default the live Wikipedia S&P 100 URL), `desk_universe_min_members` (90),
  `desk_universe_max_members` (110), plus a fourth operational storage-location field
  `desk_universe_dir` (mirrors `bar_dir`/`dataset_dir`) with a `desk_universe_dir_resolved()`
  method honoring a `TAPEOLOGY_DESK_UNIVERSE_DIR` env override. All four are in the
  `config_fingerprint()` exclusion set with a rationale comment, a stability test, and a
  counter-test (`tests/test_desk_universe.py`); the fetched/registered snapshot embeds the three
  semantic field values used at registration (provenance duty).
- **Universe store** (`desk_universe.py::UniverseStore`) — one frozen, whole-record-checksummed
  JSON file per snapshot at `.data/universe/universe-<YYYY-MM-DD>-<checksum12>.json` (mirrors
  `BarStore`/`DatasetStore`: verified on every load, `record` as the only mutation, structurally
  immutable — no update/delete function exists). Re-registering byte-identical membership content
  is refused with a 409-style `UniverseAlreadyRegistered` naming the existing snapshot; the
  on-disk file is left byte-unchanged.
- **Two new routes** under `/research/desk` (`app/research/desk_routes.py`, a new module, mounted
  in `app/main.py` alongside `research_router`): `POST /research/desk/universe/fetch` (fetch →
  parse → validate → register, with a distinct 503/422/409 for each honest failure state) and
  `GET /research/desk/universe` (snapshot list + latest membership; an explicit HTTP 200 empty
  payload before any registration — never 404).
- **Fixtures** under `apps/backend/tests/fixtures/universe/`: a realistic 103-ticker constituents
  HTML table (`sp100_constituents.html`, includes the real dual-class `BRK.B`), a deliberately
  charset-corrupted variant (`sp100_constituents_corrupted.html`), and the frozen, already-
  registered snapshot JSON produced by running the real registration path against the valid
  fixture once (`universe-2026-07-25-817cc184bbb3.json`) — this is "the fixture universe" future
  iterations (J-02–J-05) will reuse by that name.
- **42 new tests** across three files: parser contract, store immutability/integrity, T-3
  store-separation guard, Path-A stability/counter-tests, all four route states, provenance, and
  one live-Wikipedia integration test (see below).
- **Kept-route regression evidence** (`runs/goal-desk-iter-1/kept-route-baseline.txt` /
  `kept-route-after.txt`) — a sha256 byte-comparison of 14 existing `/research`, `/tape`, `/meta`
  GET responses, captured against a hermetic temp-dir server both before and after this
  iteration's diff (via a scoped `git stash`/`pop` bracket on only `config.py`/`main.py`). Zero
  deltas.

## Files Changed

- `apps/backend/app/research/desk_universe.py` (new) — vendor seam, stdlib HTML parser +
  validation/normalization, `UniverseStore`.
- `apps/backend/app/research/desk_routes.py` (new) — `POST /research/desk/universe/fetch` +
  `GET /research/desk/universe` route handlers and their FastAPI dependencies.
- `apps/backend/app/config.py` — added `desk_universe_source_url`, `desk_universe_min_members`,
  `desk_universe_max_members`, `desk_universe_dir` (+ `desk_universe_dir_resolved()`), each in the
  `config_fingerprint()` exclusion set with a rationale comment.
- `apps/backend/app/main.py` — imports and mounts the new `desk_router` alongside
  `research_router`.
- `apps/backend/pyproject.toml` — broadened the `integration` pytest marker's one-line description
  (it previously named only Alpaca; a third vendor, Wikipedia, now shares the same marker and gate
  — no behavior change, a documentation-accuracy fix).
- `apps/backend/tests/fixtures/universe/` (new dir) — `sp100_constituents.html`,
  `sp100_constituents_corrupted.html`, `universe-2026-07-25-817cc184bbb3.json`.
- `apps/backend/tests/test_desk_universe.py` (new) — parser contract, store discipline, T-3 guard,
  Path-A tests, committed-fixture-snapshot tests (28 tests).
- `apps/backend/tests/test_desk_universe_api.py` (new) — both routes' four states, provenance,
  the route-level Path-A counter-test, dependency-resolver proofs (13 tests).
- `apps/backend/tests/test_desk_universe_live_integration.py` (new) — the gated live-Wikipedia
  integration test (1 test).
- `runs/goal-desk-iter-1/kept-route-baseline.txt`, `runs/goal-desk-iter-1/kept-route-after.txt`
  (new) — the TC-11 byte-comparison capture.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result: **1210 passed, 8 skipped, 0 failed, 0 errors** (1218 collected). Baseline at HEAD (before
this iteration) was 1169 passed / 7 skipped / 1176 collected — this diff adds exactly 42 new
tests, of which 41 pass and 1 (the live-Wikipedia check) self-skips by default, matching the
identical `TAPEOLOGY_LIVE_INTEGRATION` gate `test_yahoo_live_integration.py` already uses.

- `Config().config_fingerprint()` == `08e471b10130e1e2` — confirmed unchanged, both via the
  dedicated stability test and via the live `python -c` print.
- Default (non-`integration`) run performs zero network calls (confirmed by construction — the
  skip guard is the first statement in the one new integration test — and by the suite completing
  at normal speed with no network-timeout stalls).
- Kept-route TC-11 byte-comparison: 14/14 routes byte-identical (status + sha256 + body_len)
  before vs. after, captured against a hermetic server via a scoped `git stash`/`pop` bracket.

### Skip-count note (7 → 8, an intentional, documented deviation from the phase spec's literal TC-12 text)

The phase spec and plan both say "exactly 7 skipped." This iteration's own explicit requirement
(TC-14 / the `@pytest.mark.integration` live-Wikipedia test) adds a new gated test, which — by
the SAME established convention as the other three integration files
(`test_live_integration.py`, `test_event_recording_integration.py`,
`test_yahoo_live_integration.py`, all gated on the identical `TAPEOLOGY_LIVE_INTEGRATION=1` env
var) — self-skips in the default run. There is direct precedent for this exact growth: when Yahoo
Finance was introduced in era-5, `test_yahoo_live_integration.py` added 5 new permanent skips to
the suite the same way, and `docs/goal.md`'s own framing ("1169 pass / 7 skip at era open —
grows, never shrinks") describes exactly this kind of era-over-era growth. I judged the intent of
TC-12 (full suite green, 0 failures, hermetic default run) to matter more than its literal stale
number, rather than either hiding the new test from collection to preserve the literal count, or
silently ignoring the spec's stated number without comment. Flagging this explicitly per honesty
policy — no silent scope decisions.

### Live Wikipedia fetch (TC-14) — SUCCEEDED

Run for real, twice, against the live vendor:

1. `TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_desk_universe_live_integration.py -v -s`
   → **1 passed**.
2. A full end-to-end proof through the actual production route (`POST
   /research/desk/universe/fetch`, zero test doubles, a hermetic temp `.data/` dir, real network):
   `200 OK`, **101 real members parsed** (well inside `[90, 110]`), dual-class `BRK.B → BRK-B`
   confirmed against real data (`raw_members["BRK-B"] == "BRK.B"`), registered as snapshot
   `universe-2026-07-25-49b33fa31680`, then read back correctly via `GET
   /research/desk/universe`.

**One real finding, fixed in the shipped code (not just the test):** the FIRST live attempt got
an honest `HTTP 403` from the Wikimedia edge ("Please respect our robot policy") — I had used a
generic `User-Agent` string. Isolated empirically (curl with the identical UA succeeded; httpx
with the same UA failed; the deciding factor, confirmed by three isolated variants, was the
presence of a URL-shaped token in the UA — matching Wikimedia's documented User-Agent policy,
which requires bots to self-identify with a project reference). Fixed by giving
`fetch_constituents_html` a descriptive default User-Agent
(`TapeologyDeskBot/1.0 (+http://example.invalid/tapeology; ...)`, using the IANA-reserved
`.invalid` TLD since this project has no public home page, rather than fabricate a real-looking
one). Confirmed fixed against the live vendor after the change (both runs above are POST-fix).
This is a real operational fact about the vendor a future top-up/screen-run operator should know:
Wikipedia's edge actively bot-detects on User-Agent shape, not just presence/absence.

Measured live-fetch latency: 0.15s for the full page (180KB), comfortably inside the
`CONFIG.vendor_http_timeout_seconds` (6.0s) production budget used by the real route path (the
live integration test itself uses an explicit 15s timeout for extra headroom under test
conditions, but the production route path was independently verified at the real 6.0s budget).

### Service startup

`scripts/dev.sh` started both backend (`:8301`) and frontend (`:3301`) cleanly with no errors;
stopped (killed by port, verifying the actual child `uvicorn`/`next dev` processes, not just the
wrapper script's own PID — the wrapper's `$!` is not the same PID as the processes actually
bound to the ports); restarted cleanly a second time with no port conflicts. Both server
processes were killed before finishing this task (verified via `ss -ltn` — ports free, no
lingering `uvicorn`/`next dev` processes).

## Known Issues

- **Skip count is 8, not the spec's literal "exactly 7."** See the dedicated note above — this is
  an intentional, honestly-documented deviation, not an oversight. Every OTHER quantitative
  acceptance line (≥1169 passed, 0 failed, hermetic default run, fingerprint pin unchanged) holds
  exactly as specified.
- **Wikimedia's User-Agent policy is now a hard operational dependency for the LIVE fetch path.**
  The current UA string works today (verified live). If Wikimedia's bot-detection policy changes
  further in the future, the honest failure mode is unchanged (`UniverseFetchError`, a clean 503
  at the route, nothing fabricated) — but a future operator debugging a fetch failure should know
  to check for this class of issue first, not just credentials/connectivity.
- **No SQLite index over the universe store this iteration** — by design, per the plan
  (`docs/goal.md`'s own text: "any index over it is derived/rebuildable" describes a property an
  index must have IF one exists, not a mandate that J-01 ship one). A directory-scan `list()` is
  sufficient at J-01's snapshot volume; J-02's own coverage-speed requirement is the one that
  actually needs an index, and it reads `bar_index`, not a universe index.
- **No CLI wrapper for the universe fetch** — not named in J-01's steps (only J-02/J-03 explicitly
  require "POST + CLI"); the route is fully usable via curl/MCP `get_endpoint` today.
- **The universe subsystem is entirely backend/REST-only this iteration** — zero frontend files
  touched, `UI_ROUTES` unchanged (still exactly `Cockpit`, `Structure`), no on-screen control
  exists yet. This is explicitly correct per the plan (`Frontend Present: no`; `/desk` ships in
  J-04) — noted here only so it isn't mistaken for an oversight.
- **The real `.data/universe/` directory now holds one real, live-fetched snapshot** (from the
  end-to-end production-route proof above, run against a temp `.data/` dir, NOT the repo's real
  `apps/backend/.data/`). No production data directory was touched by this work — every
  verification used either the hermetic test suite or an explicitly temp-dir-scoped manual run.
