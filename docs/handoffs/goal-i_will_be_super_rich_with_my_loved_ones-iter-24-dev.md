# goal-i_will_be_super_rich_with_my_loved_ones-iter-24 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-24
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## Resume Context

This iteration was ABORTED mid-dispatch and resumed. The working tree carried an uncommitted
partial implementation (baseline snapshot-sha `6ea9018`). Per the spec's RESUME CONTEXT note, I
treated that work as WIP to **verify and complete** against the spec — I did not restart from
scratch, did not `git checkout`/discard the unstaged files, and did not trust it untested. The
partial work proved substantially complete and correct; my contribution this session was to
**verify** every IN-SCOPE item end-to-end (full backend suite, frontend type-check, live ASGI
probes of the new endpoints + the WS==summary single-source clause) and confirm the carry-along
`hint_log_max` test pair the config comment claims actually exists in the suite. No code changes
were required — the partial implementation already satisfied the spec; this handoff memorializes
the verification.

## What Was Built

J-67 — the feed basis is always labeled (cockpit feed badge + stamp display, one config-owned mapping):

- **ONE consolidated scenario→`data_feed` mapping.** A new leaf module
  `app/research/feed_basis.py` owns the single `data_feed_for_scenario(scenario, config)`
  function. The iter-23 `hints.py` LOCAL duplicate is REMOVED (re-exported from the leaf module,
  not paralleled); `monitor.py`, `hints.py`, `studies.py`, `routes.py`, and `serializers.py` all
  import the one function. No monitor↔hints import cycle (both import the leaf).
- **The mapping is config-aligned.** `live …` → `config.live_feed`, `historical …` →
  `config.historical_feed`, everything else → `"sim"` — replacing the hardcoded `"iex"`/`"sip"`
  literals. Defaults unchanged (`live_feed="iex"`, `historical_feed="sip"`) so every existing
  stamp/pinned test/persisted record is byte-identical. A SIP-entitled operator upgrading live is
  ONE config value with zero relabeling code (J-67's final acceptance clause, now provable by
  `test_flipping_live_feed_relabels_new_stamps_with_no_code_change`).
- **Current-watch feed basis served (Data Contract row 29).** An additive `data_feed` metadata
  field on the row-6 snapshot projection (`serialize_summary`), re-exposed VERBATIM by the WS
  frame (`serialize_stream`) — computed once server-side by the one mapping from the snapshot's
  scenario. Follows the `end_reason`/`delivery_lag_seconds` precedent: projection metadata only,
  never read by classification, observer signature unchanged.
- **Taxonomy feed-basis copy (row 24).** `GET /research/taxonomy` carries an additive `feed_basis`
  block: per-feed badge labels (sim → "Simulated", iex → "IEX (live)", sip → "SIP (consolidated)")
  + the live disclosure line VERBATIM from goal.md. The frontend hardcodes none of it. Doubles as
  the iter-24 code-identity canary.
- **Carry-along `hint_log_max` test pair.** `test_hint_log_max_is_serving_only_excluded_from_fingerprint`
  (stability) + `test_a_real_threshold_still_changes_fingerprint` (counter) in
  `tests/test_research_hints.py` — the assurance pair the `config.py` comment already claims is now
  real (lesson iter-23: comments claiming test coverage must be cross-checked against the suite).

### Frontend

- **Cockpit feed-basis badge** (`FeedBasisBadge.tsx`, wired into `TopBar.tsx`): renders the served
  `snapshot.data_feed` VERBATIM with taxonomy labels, beside the watched-source indicator / lag
  readout. On the live IEX basis the taxonomy disclosure line renders beside it. Honest absence —
  when no watch is active the badge renders nothing (self-guards on `data_feed`; never a fabricated
  "live"/"iex" guess). Neutral slate chip (a factual stamp, not the side/impact palette).
- **Hint-log feed stamp** (`HintLog.tsx`): a new "Feed" column displays each stored row's
  `data_feed` stamp (persisted value verbatim, label from taxonomy).
- **Display-gap sweep:** thesis rows, journal detail, analytics partitions, and study rows already
  display the stored `data_feed` (greps confirmed); the one confirmed gap was the hint-log column,
  now filled. No change to anything that already displayed it.

## Files Changed

Backend:
- `apps/backend/app/research/feed_basis.py` -- NEW: the single owner of the config-aligned scenario→`data_feed` mapping.
- `apps/backend/app/research/hints.py` -- removed the local mapping copy; re-exports from `feed_basis`; fire path passes `config`.
- `apps/backend/app/research/monitor.py` -- imports + re-exports the one mapping; `data_feed` declaration call passes `config`.
- `apps/backend/app/research/studies.py` -- imports the one mapping; passes `config` at both stamp sites.
- `apps/backend/app/research/routes.py` -- imports the mapping from `feed_basis`; `declare_thesis` passes `config`.
- `apps/backend/app/research/taxonomy.py` -- additive `FEED_BASIS_LABELS` + `FEED_BASIS_LIVE_DISCLOSURE` + `feed_basis` taxonomy block + hint-log `feed` column.
- `apps/backend/app/serializers.py` -- additive `data_feed` field on `serialize_summary` + `serialize_stream` (same single mapping).
- `apps/backend/app/config.py` -- `hint_log_max` comment now references the real test pair (no value change; both feed keys already present + in fingerprint).

Backend tests:
- `apps/backend/tests/test_feed_basis.py` -- NEW: pins the one mapping (defaults byte-identical, config-relabel, prefix-always-via-config, fingerprint inclusion, exactly-one-definition AST check).
- `apps/backend/tests/test_research_hints.py` -- two-arg call update + the carry-along `hint_log_max` stability/counter pair.
- `apps/backend/tests/test_api.py` -- summary+stream `data_feed` single-source + scenario-prefix-via-config tests.
- `apps/backend/tests/test_research_api.py` -- taxonomy `feed_basis` copy + canary + J-66 copy-discipline test.
- `apps/backend/tests/test_observer_equivalence.py`, `test_research_geometry.py`, `test_research_monitor.py` -- two-arg call-signature updates.

Frontend:
- `apps/frontend/components/FeedBasisBadge.tsx` -- NEW: the cockpit feed-basis badge.
- `apps/frontend/components/TopBar.tsx` -- wires the badge into the `/` status area (gated on `watched`).
- `apps/frontend/components/HintLog.tsx` -- additive "Feed" column rendering the stored stamp.
- `apps/frontend/lib/api.ts` -- `fetchInitialSnapshot` reads `summary.data_feed` verbatim.
- `apps/frontend/lib/types.ts` -- `data_feed` on `TapeSnapshot`; `FeedBasisTaxonomy` + `feed_basis` on `ResearchTaxonomy`; `feed` hint-log column.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **812 passed, 1 skipped, 0 failed** (full backend suite, exit 0, ~9m57s). The 1 skip is
the pre-existing credentialed live-integration test. Observer-equivalence suite green with ZERO
re-pins — no file under `app/engine/` or `app/providers/` is in the diff (the vendor adapter is
untouched). `test_feed_basis.py::test_exactly_one_mapping_function_in_the_codebase` (an AST scan)
proves exactly ONE `data_feed_for_scenario` definition remains.

Frontend type-check: `node_modules/.bin/tsc --noEmit` exit 0 (zero type errors across all changed
files). I deliberately used `tsc --noEmit` rather than `npm run build` to avoid any interaction
with a shared `.next` (memorialized QA caution) — although no tapeology dev server was running (the
only live `next dev`/`uvicorn` belong to the unrelated trendora project on ports 3835/8835).

## Live Verification (ASGI / uvicorn smoke)

Started the backend on an isolated port with a file-based temp DB and confirmed:
- `GET /research/taxonomy` carries the `feed_basis` block (3 labels + the exact goal.md disclosure
  line) — the iter-24 code-identity canary, proving the new server code is live.
- `GET /tape/SIM-BUYER/summary` returns `data_feed: "sim"` for a sim watch (computed by the one
  config-aligned mapping); a not-watched ticker stays **404** (honest absence — no fabricated basis).
- The **WS frame** `data_feed` equals the `/summary` value VERBATIM (`"sim" == "sim"`) — the
  REST==WS single-source clause confirmed live, matching the passing
  `test_data_feed_basis_served_on_summary_and_stream_single_source` unit test.

All test processes were torn down; ports 8765/8766 are free; temp DB files removed. The trendora
dev servers (a different project) were untouched.

## Known Issues

- **None functional.** All IN-SCOPE items implemented and verified; all required-still-passing
  journeys' backend legs green (byte-identity preserved via unchanged defaults).
- **Credential-gated browser leg (documented, not faked):** the J-67 live-declared-row leg (declare
  a live thesis and confirm the stored `iex` stamp on its journal row) needs market hours +
  credentials. Per the spec's TESTING REQUIREMENTS, the live badge + the exact disclosure line are
  browser-verifiable WITHOUT a feed (the cockpit can render the live-mode controls); the
  stored-`iex`-stamp confirmation is the credential-gated leg for browser-qa to document, never
  fabricate. The historical SIP leg is REST-verifiable on a credentialed historical watch
  (`serialize_summary(historical_snap)["data_feed"] == "sip"` is unit-proven via
  `test_data_feed_basis_reflects_scenario_prefix_via_config`).
- **First ASGI probe gotcha (resolved):** an initial smoke test using `TAPEOLOGY_JOURNAL_DB=":memory:"`
  surfaced a `no such table: theses` on the WS path — this is a SQLite `:memory:` per-connection
  isolation artifact of the probe config, NOT a code defect. Re-running with a file-based temp DB
  passed cleanly. Documented so QA does not mistake it for a backend bug if they reuse `:memory:`.
- **Depth stays lean:** the full-pipeline `qa_complete` harness halt remains open (iter-23 eval,
  open item 3); restore full depth once it is fixed.

## Re-verification Notes (second resume, 2026-06-13)

The session paused mid-iter-24 again (AWAITING_PUMP) and re-dispatched. Per the spec RESUME
CONTEXT, I treated the uncommitted working tree as the developer's already-complete WIP to
**verify, not restart** — I did not `git checkout`/discard the unstaged files and did not trust
them untested. I re-confirmed the tree is internally consistent against the spec and re-ran the
full gate fresh:

- **Full backend suite re-run (fresh):** `cd apps/backend && .venv/bin/python -m pytest tests/`
  → **812 passed, 1 skipped, 0 failed, exit 0** (393.53s). Byte-for-byte the same pass/skip count
  as the prior run — no flake, no drift. The 1 skip is the pre-existing credentialed
  live-integration test.
- **Frontend type-check re-run:** `node_modules/.bin/tsc --noEmit` → exit 0 across all changed
  files. (Used `tsc --noEmit`, not `npm run build`, per the memorialized shared-`.next` caution;
  no tapeology dev server was running.)
- **DoD spot-checks confirmed in the tree:**
  - Exactly ONE `data_feed_for_scenario` definition (`research/feed_basis.py`); `monitor.py` and
    `hints.py` re-export it (`__all__`/comment), and `studies.py`, `routes.py`, `serializers.py`
    all import the one function — verified by grep across `app/` + the passing AST test
    `test_exactly_one_mapping_function_in_the_codebase`.
  - The mapping reads `config.live_feed`/`config.historical_feed` (no hardcoded `"iex"`/`"sip"`);
    defaults unchanged so all pinned stamp tests stay green.
  - No file under `app/engine/` or `app/providers/` is in the diff (`git diff --name-only HEAD`
    → empty for those paths) — the vendor adapter is untouched; observer-equivalence suite green
    with zero re-pins.
  - The carry-along `hint_log_max` pair genuinely exists in the suite
    (`test_hint_log_max_is_serving_only_excluded_from_fingerprint` +
    `test_a_real_threshold_still_changes_fingerprint` in `tests/test_research_hints.py`) — the
    `config.py` comment's claim is now true (iter-23 lesson applied and re-checked).
  - Summary==WS single source proven by `test_data_feed_basis_served_on_summary_and_stream_single_source`;
    `live`→`iex` / `historical`→`sip` projection by `test_data_feed_basis_reflects_scenario_prefix_via_config`;
    taxonomy `feed_basis` copy + verbatim goal.md disclosure by `test_taxonomy_serves_feed_basis_copy_canary`.
- **No code changes were required this session** — the WIP already satisfied every IN-SCOPE item;
  this re-verification memorializes the fresh green gate. Servers clean (no tapeology
  uvicorn/next-dev processes left running).
- **Downstream still pending (unchanged):** reviewer, QA, and browser-qa have not run; the
  J-67 evidence dir is empty. J-67 cannot flip to passing without browser evidence — the remaining
  pipeline evaluates the finished diff as usual.
