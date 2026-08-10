# goal-playbook-iter-1 Dev Handoff

**Phase:** goal-playbook-iter-1
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

Target journey **J-01** ("The signal contract — opening-range breaks, lookahead-clean and
pre-registered") — the first link of Era B2 "The Playbook". Detection only; no measurement, no
compute manager/CLI/trigger route, no UI (all per the plan's explicit scope split).

- **`app/research/desk_playbook_features.py`** — the spec §2 eight shared primitives, constant-free
  by design (every threshold arrives as a parameter, so the module never imports from
  `desk_playbook.py` and the import graph stays acyclic): `rth_session_slice` (imports
  `desk_forward._session_slice` for the day-narrowing bisect, then filters to ET 09:30–16:00 via
  `zoneinfo.ZoneInfo("America/New_York")` — DST-correct, verified against both a June/EDT and a
  January/EST fixture), `opening_range` (1m basis when ≥10 of the first 15 one-minute bars are on
  file, else an honest 1m→5m degrade to the first `or_minutes // 5` five-minute bars **inside the
  09:30–09:45 window**, else `None`) — *amended by the audit pass (finding B1): the fallback
  originally sliced `session_5m[:3]` positionally, which handed a session whose early 5m bars are
  missing an "opening range" built from its 09:40/09:45/09:50 bars, disclosed as `basis: "5m"`
  exactly like a genuine one. Both bases now read the same epoch window; a gapped session is an
  honest absence,*
  `baselines` (MBR + per-slot volume-median vector over the prior 20 RTH sessions — the ONE
  baseline builder), `swing_pivots` (mirrors `levels._swing_pivots`'s strict-extreme/ties-are-not-
  pivots rule but returns high/low separately, since `levels.py` folds both into one level type),
  `consolidation_range`, `vertical_move` (with an optional, caller-supplied `require_volume`
  clause for J-05's later use), `zone_touches` (full-exit re-arm, attributed to
  `desk_forward._touch_scan`), `market_context` (index-only mechanical facts; direction/alignment
  is left to the detector, which has MBR access this primitive deliberately does not).
- **`app/research/desk_playbook_detect.py`** — `detect_opening_range_breaks`, one shared
  implementation of spec §3.1 (`open_high_break`) and §3.2 (`open_low_break`) since the two are an
  exact mirror and mutually exclusive (at most one fires per symbol-session). Also constant-free
  (reads every threshold from a `params` dict — the caller's already-built `playbook_parameters()`
  — so "the parameters blob matches what the detector used" holds by construction). Emits the full
  signal shape: `entry`/`entry_kind` (spec §0's stop-through-fill convention),
  `invalidation_price` (structural pad), the narrow-OR gate, the ambiguous-both-sides-break
  diagnostic, and the shared disclosure block (RVOL/volume-into-trigger verdict, spiky-approach,
  market context + relative-strength, attempt_count, principles). Never imports `setups.py`/
  `backtests.py`; no field is named `stop_loss`.
- **`app/research/desk_playbook.py`** — the spec §1 constants transcribed verbatim (all ~40, tagged
  BOOK/ADAPTATION in comments — including a `PLAYBOOK_OR_MIN_1M_BARS = 10` I named myself; see
  Known Issues), `PLAYBOOK_REGISTER`, `playbook_parameters()` (call-time reads + the rail's own
  horizon/seed/measure-shape constants embedded verbatim, per the "applied at birth" instruction —
  J-01 measures nothing, but a future rail change will still re-key playbook records),
  `compute_playbook_input_signature()` (mirrors `compute_forward_input_signature` exactly:
  sha256[:16] over sorted `(symbol, timeframe, series_id, checksum)` tuples for members ∪ {SPY} ×
  {1m, 5m} + config fingerprint + parameters blob), `PlaybookStore` (2-pin append-only, mirrors
  `ForwardStore`; no update/delete method exists — structurally, by never being written), and
  `compute_playbook(universe_store, bar_store, config_fingerprint, session_date)` — checks
  `desk_sessions.refuse_if_not_a_session` first (raising `PlaybookSessionRefused`, since no
  separate compute-manager layer exists yet to do this check upstream), then walks every universe
  member recording a signal, a disclosed absence (no 5m bars / thin-or-zero baseline / no buildable
  opening range), or neither (a legitimate "the setup did not form" outcome, never an absence).
- **`desk_routes.py`**: `GET /research/desk/playbook` (`?date=`/`?id=`, honest-empty
  `{"playbooks": [], "latest": null, "integrity_errors": []}`, mirrors `GET /forward`'s "latest
  recording" semantics since a playbook — like a forward measurement and unlike a screen — can
  carry multiple versions per date) plus `get_playbook_store` mirroring `get_forward_store`. This
  is the ONLY change to this shared file (one import line + one dependency function + one route).
- Generic lookahead property test (`test_desk_playbook_detect.py`): a module-level
  `_LOOKAHEAD_FIXTURES` list, parametrized, asserting (a) `detect(bars[:trigger_index+1])`
  reproduces the same `trigger_price`/`invalidation_price`/`geometry` and (b) mutating any bar
  strictly after the trigger index leaves the WHOLE signal byte-identical. J-04/J-05/J-06 extend
  this by appending their own fixture tuples, never touching the two assertion bodies.

## Files Changed

- `apps/backend/app/research/desk_playbook_features.py` — new; the 8 primitives.
- `apps/backend/app/research/desk_playbook_detect.py` — new; the opening-range-break detector pair.
- `apps/backend/app/research/desk_playbook.py` — new; constants, parameters/signature, `PlaybookStore`,
  `compute_playbook`.
- `apps/backend/app/research/desk_routes.py` — added the `GET /research/desk/playbook` route +
  `get_playbook_store` dependency + one import line. No other change.
- `apps/backend/tests/test_desk_playbook_features.py` — new; 21 tests (22 after the audit pass added
  the finding-B1 regression test), all 8 primitives incl. the
  1m/5m opening-range degrade + null case, MBR=0/thin-baseline case, `swing_pivots` parity with
  `levels._swing_pivots`, and `market_context`'s no-SPY/insufficient-lookback null cases.
- `apps/backend/tests/test_desk_playbook_detect.py` — new; 8 tests, the canonical/near-miss/
  degraded-basis/ambiguous-outside-bar fixture goldens (TC-2..TC-5) plus the generic lookahead
  property test (TC-6, both the truncation and mutation variants).
- `apps/backend/tests/test_desk_playbook.py` — new; 13 tests covering TC-1, TC-7..TC-12, TC-15,
  TC-16: session refusal, per-symbol absences beside a real firing signal, `PlaybookStore`
  duplicate-key/corrupt-file/no-update-or-delete discipline, the monkeypatch parameters/signature
  liveness counter-test, the `GET` route's three shapes, the `setups`/`backtests` import ban plus
  the live no-`stop_loss`-field check, and the `PLAYBOOK_REGISTER` copy-discipline lint.

Nothing else touched — `git diff` is empty against `desk_forward.py`, `desk_screen.py`,
`desk_screen_diff.py`, `desk_screen_pins.py`, `setups.py`, `bars.py`, `app/config.py`,
`app/mcp/__init__.py`, and everything under `apps/frontend/` (verified via `git status`/`git diff
--stat` before writing this handoff).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1968 passed, 8 skipped, 0 failed** (era-open floor was 1926 pass / 8 skip; this
iteration's 42 new tests account for the entire increase — 1926 + 42 = 1968 exactly).

Also verified directly:
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged; zero new `Config` fields — `git
  diff` against `app/config.py` is empty).
- MCP stays at 18 tools (`app/mcp/__init__.py` untouched).
- Real HTTP smoke test: started a scratch `uvicorn` instance, confirmed `GET
  /research/desk/playbook` returns `200 {"playbooks": [], "latest": null, "integrity_errors": []}`
  over a real socket (not just `TestClient`), then stopped the process (confirmed no uvicorn left
  running on that port afterward).

TC-13 (suite ≥ 1926/8, fingerprint, frozen-file diffs) and TC-14 (J-10 golden-script replay) are
both satisfied by the above — TC-14 specifically because this iteration touches zero files under
`apps/frontend/` and makes no change to any already-shipped route's behavior, so nothing the J-10
script exercises (cockpit, `/structure`, every shipped `/desk` section) could have changed. Per the
plan, the actual browser replay of `journey-scripts/J-10.json` is the browser-qa-agent's job, not
this agent's — Frontend Present is `no` for J-01 itself.

## Known Issues

- **`PLAYBOOK_OR_MIN_1M_BARS = 10` is not in the spec's own §1 constants table.** Spec §2
  primitive 2's prose states "fewer than 10 of the 15 one-minute bars on file ⇒ fall back to the
  5m basis" but §1's table (which calls itself "the COMPLETE tunable surface — nothing else
  exists") never lists this `10` as a named constant. I named it explicitly in
  `desk_playbook.py` (so it still flows through `playbook_parameters()`/the signature like every
  other threshold, rather than sitting as an inline magic number) and used the value the spec's
  own prose states, but I did not invent or adjust it — this is a spec-completeness gap worth an
  owner ruling on whether §1 should gain this row, not a threshold judgment call on my part.
- **The market-context/relative-strength/volume-into-trigger disclosure sub-fields are exercised
  correctly but only against fixtures where SPY has no bars planted** (the canonical/near-miss/
  degraded-basis/ambiguous fixtures all assert `market.reason == "no SPY bars recorded for the
  session"`). `market_context`'s "has enough SPY bars" path IS unit-tested directly in
  `test_desk_playbook_features.py`, and the detector's MBR-normalization/alignment logic that
  consumes it is implemented per spec §0, but there is no end-to-end detector-level fixture with a
  populated SPY series proving `direction`/`book_would_skip_market`/`relative_strength_strong`
  together on a real signal. Low risk (the primitive and the arithmetic are each independently
  tested) but flagged for the reviewer/auditor to weigh.
- **No live/manual verification of the real desk universe or real recorded bars** — J-01's own
  acceptance is `(Keyless; automated.)` per `docs/goal.md`, and the spec's Hermetic Tests
  constraint requires the default suite to stay keyless on committed fixtures, so this was not
  attempted. The real back-scan over the operator's actual recorded sessions is explicitly J-07's
  concern, operator-run.
- `.claude/project-template.md` is the unfilled generic template (a pre-existing condition, not
  introduced by this iteration — README.md:270 already flags it with a TODO pointing at the real
  source of truth: `scripts/dev.sh`/`start-backend.sh`/`start-frontend.sh`). Test/start commands
  used above came from README.md and `pyproject.toml`, not from `project-template.md`.
