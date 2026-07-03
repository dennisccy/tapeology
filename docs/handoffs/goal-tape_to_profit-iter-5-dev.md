# goal-tape_to_profit-iter-5 Dev Handoff

**Phase:** goal-tape_to_profit-iter-5
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## Re-verification (verify-and-complete resume dispatch, 2026-07-03)

This dispatch re-ran every claim below independently against the existing uncommitted working
tree per the iter spec's resume protocol. **All checks re-verified green; zero code changes were
made** — the implementation stands exactly as the interrupted dispatch left it. Results of THIS
dispatch's runs:

- Full backend suite: **988 passed, 1 skipped** (989 collected; exit 0) — matches the claim.
- Engine equivalence suite (`tests/test_observer_equivalence.py`): **7 passed** — matches.
- Frontend `npm run build`: **compiled successfully**; `/performance` in the route table at
  2.52 kB — matches.
- Golden replay `demo_runner.py --mode verify --journeys J-01,J-05` against a freshly seeded
  uvicorn(:8301) + `next dev`(:3301) stack: **2/2 PASS** (J-01 with its new 4th destination and
  the honest not-found step still final; J-05 all 11 steps including the exact full-precision
  value expects). No golden script was re-recorded — the existing scripts replayed green.
- Page-equals-API: live `GET /research/pnl/ledger` on a fresh seeded DB reproduced the pinned
  founding values exactly (train net R `-0.16000000000001136` / net $ `-16.000000000001137` /
  n 1; hold-out net R `0.3334000000001356` / net $ `33.34000000001356` / n 1; both splits
  `insufficient_sample: true`; `baseline: null`; register verbatim; `min_sample_size` 5), and
  the J-05 replay asserts those exact strings as rendered page text. `GET /research/profiles`
  served `{profiles: [{id: default, frozen: true, is_default: true}], champion: {strategy_id:
  v1, profile: default}}`; POST → 405.
- Honest failure states (headless-browser checks): empty ledger (fresh unseeded DB) → explicit
  `ledger-empty` state with the API-served register still visible, zero ledger rows, champion
  panel still served — PASS; backend down → BOTH panels show their explicit unavailable states
  ("Backend unreachable — is the API running?" + "Nothing cached and nothing fabricated is
  shown in its place."), no cached values leaked, no champion or ledger row fabricated — PASS.
- Seeding CLI idempotency: first run appended the founding row, second run reported the honest
  no-op ("already present … nothing was appended").
- Conformance re-checks: `app/mcp/__init__.py` diff is docstring-only (re-confirmed via
  `git diff`); zero diff on `pnl_ledger.py` / `pnl_baseline.py` / `pnl_history.py` /
  `backtests.py` / `datasets.py` / `app/engine/` / `app/serializers.py` /
  `reports/pnl/pnl-history.md` / `NavBar.tsx` / Cockpit/Journal/Studies pages; `profiles.py`
  imports `PROFILE_DEFAULT` + `STRATEGY_V1_ID` with no duplicated id literals (source-scan test
  green); tmpfs pre-flight /tmp 48%, pytest dir 2.3G — headroom OK.
- All verification server processes were killed before finishing (ports 8301/3301 verified
  free, no uvicorn/next processes remain).

Everything below this section is the interrupted dispatch's original handoff, left intact —
its substance is now independently confirmed.

## What Was Built

- **`/performance` entered the canonical route map (Data Contract row 35).** One entry added to
  `UI_ROUTES` in `app/meta.py`: `{"path": "/performance", "label": "Performance", "nav": True}` —
  the map now has 5 entries, 4 nav-true. This is the ONLY route-list edit anywhere; the NavBar
  picked up the fourth link with zero frontend nav changes (verified in the browser: 4 links on
  every page, Performance active on `/performance`).
- **Minimal `GET /research/profiles` (Data Contract row 33, serving side only).** New module
  `app/research/profiles.py` + one GET route on the existing research router. Serves the
  config-owned initial state: exactly one profile (`{"id": "default", "frozen": true,
  "is_default": true}`) and the founding champion pointer (`{"strategy_id": "v1", "profile":
  "default"}`), built from the existing single-copy constants `PROFILE_DEFAULT`
  (`backtests.py`) and `STRATEGY_V1_ID` (`config.py`) — a test asserts the new module's source
  carries NO literal copy of either id string. Non-GET verbs are FastAPI's automatic 405 (no
  write handler exists). No candidate registration, no promotion mechanics (J-06/J-07 untouched).
  Note: the "is this the default profile" flag key is `is_default` (not `default`) precisely so
  the module contains no copy of the id literal.
- **MCP: zero proxy/handler logic changes.** `/research/profiles` became reachable through the
  existing `get_endpoint` allowlist by construction. The only `app/mcp/__init__.py` diff is the
  module docstring whose honest-404 example named `/research/profiles` before this iteration
  (verified: `git diff` on that file shows docstring lines only).
- **MCP tests:** the honest-404 passthrough legs (direct dispatcher test AND the stdio
  end-to-end leg) were RELOCATED from `/research/profiles` to a permanently-unknown
  `/research/nonexistent-path-canary` (the honest-error behavior stays covered — nothing
  deleted), and a new byte-identity test proves `get_endpoint` on `/research/profiles` returns
  the live 200 byte-identical to REST.
- **New frontend page `apps/frontend/app/performance/page.tsx`** — see the frontend handoff
  (`goal-tape_to_profit-iter-5-frontend.md`) for detail. Renders the ledger and champion
  verbatim from the two canonical endpoints; computes nothing.
- **Golden replay scripts:** `J-01.json` evolved from 3 to 4 destinations (added
  `goto /performance` expecting `Performance`; the honest not-found step remains the final end
  state), and a new `J-05.json` was recorded (nav-click to `/performance`, then hard expects on
  the register string, the founding row title, the exact full-precision train/hold-out values,
  the insufficient-sample label, the founding marker, and the champion summary testids). Both
  replay end-to-end PASS via `demo_runner.py --mode verify` against a seeded dev stack.

## Files Changed

- `apps/backend/app/meta.py` -- added the `/performance` route-map entry (row 35); docstring tense fix
- `apps/backend/app/research/profiles.py` -- NEW: row-33 serving-side projection (registry + champion) from existing constants
- `apps/backend/app/research/routes.py` -- import + one `GET /research/profiles` route serving the projection
- `apps/backend/app/mcp/__init__.py` -- stale docstring only (honest-404 example no longer names `/research/profiles`)
- `apps/backend/tests/test_meta_routes.py` -- pinned expectations updated: 5 entries, 4 nav-true, `/performance` present (the old "excludes performance" test replaced by the positive assertion)
- `apps/backend/tests/test_profiles_api.py` -- NEW: exact payload pin vs constants, single-profile registry, non-GET 405, no-duplicated-id-literal source check
- `apps/backend/tests/test_mcp_server.py` -- honest-404 legs relocated to a permanently-unknown `/research/*` path; new live-200 byte-identity test for `/research/profiles`
- `apps/frontend/app/performance/page.tsx` -- NEW: the /performance page (see frontend handoff)
- `apps/frontend/lib/types.ts` -- NEW types: `PnlLedger`/`PnlLedgerRow`/`PnlSplitMeasurement`/`PnlSplitProvenance`, `IndicatorProfile`/`ProfilesPayload`
- `apps/frontend/lib/api.ts` -- NEW fetch helpers `fetchPnlLedger` / `fetchProfiles` (existing `fetchStudies` pattern; explicit unavailable results, never cached data)
- `runs/goal-session-tape_to_profit/journey-scripts/J-01.json` -- 3→4 destinations (added `/performance`); honest not-found still final
- `runs/goal-session-tape_to_profit/journey-scripts/J-05.json` -- NEW golden script for the J-05 journey

Zero diff (verified by `git diff --stat`): `pnl_ledger.py`, `pnl_baseline.py`, `pnl_history.py`,
`backtests.py`, `datasets.py`, `app/engine/`, `app/serializers.py`, `reports/pnl/pnl-history.md`,
`NavBar.tsx`, and the Cockpit/Journal/Studies pages.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **988 passed, 1 skipped** (iter-4 baseline was 983 passed / 1 skipped; +5 net new tests,
none deleted or weakened — the meta "excludes performance" pin was replaced by the positive
"includes performance" pin, and the MCP honest-404 leg was moved, not removed)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py`
Result: **7 passed** (engine equivalence 7/7 — zero engine/compute-module diffs by construction)

Command: `cd apps/frontend && npm run build`
Result: **compiled successfully**; `/performance` present in the route table (2.52 kB)

Deterministic replay (dev-stack proof; QA re-runs it in the harness):
`python3 scripts/automation/lib/demo_runner.py --mode verify --journeys J-01,J-05 ...`
Result: **2/2 PASS** (J-01 with the new 4th destination; J-05 end-to-end including exact
full-precision value expects)

Browser dev verification (Chrome, against a live seeded backend + `next dev`):
- Page-equals-API: 19/19 in-page `fetch()` comparisons true — train net R `-0.16000000000001136`,
  net $ `-16.000000000001137`, n `1`; hold-out net R `0.3334000000001356`, net $
  `33.34000000001356`, n `1`; register string verbatim; founding marker (no fabricated zeros);
  provenance (strategy/profile/fingerprint/backtest/dataset/checksum) visible; date dd-MM-yyyy;
  champion equals `GET /research/profiles`.
- Empty ledger (unseeded DB): honest explicit empty state; register still shown from the API.
- Backend down: both panels show explicit unavailable states ("Backend unreachable — is the API
  running?" / "Nothing cached and nothing fabricated is shown in its place."); the nav shows its
  existing degraded state. No fabricated or cached rows anywhere.
- Nav: 4 links (Cockpit / Journal / Studies / Performance) rendered from the route map on `/`,
  `/journal`, `/studies`, `/performance`.

Service startup (pre-handoff checklist): `bash scripts/dev.sh` started backend (:8301) and
frontend (:3301) healthy; stopped; started again — the script's port-kill preamble cleared the
lingering child and both came up healthy again (no port conflict). All server processes were
killed before finishing (ports verified dead).

## Known Issues

- **`scripts/dev.sh` child-process nuance (pre-existing, not introduced here):** killing the
  dev.sh parent leaves the `next dev` node child alive; the script's own next start kills port
  occupants (lsof+fuser preamble), so restarts recover cleanly — observed exactly that behavior.
  dev.sh is untouched this iteration.
- **QA pre-flight reminder (from the iter spec):** the browser lane must run the idempotent
  seeding CLI (`python -m app.research.pnl_baseline`) against the HARNESS backend's journal DB
  before testing `/performance`, and must assert VALUES, not backtest/dataset UUIDs (a fresh
  harness DB reproduces values deterministically but mints new record ids).
- **J-05 golden script pins `insufficient sample (n < 5)`** — the `5` is the served
  `min_sample_size` (config `pnl_min_sample_size`). If that config value ever changes, the
  script needs re-recording (golden scripts pin verified behavior by design).
- No new dependencies, no native binaries, no external/credentialed integrations this iteration
  (everything is keyless-local); live-integration checklist item satisfied by the real
  uvicorn+next+seeding-CLI dev stack used for verification.

## Suggested Next Phase

J-06 at lean depth: register one candidate indicator profile (additive feature key or alternate
threshold set) in the config-owned registry, refactor the backtest route's profile refusal to
consult the registry, pin the pre-profile equivalence outputs, and let `/research/profiles`
honestly list the candidate beside the frozen default — its fresh-failing evidence naturally
evolves from "404" to "registry lists no candidate yet", exactly as the iter-5 spec anticipated.
Then J-07 (sweep harness), whose promotion-gate tests must control the configured minimum-n in
both directions since the fixture pair arms only n=1 per split.
