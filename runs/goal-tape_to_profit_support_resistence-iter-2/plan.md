# goal-tape_to_profit_support_resistence-iter-2 Execution Plan

Frontend Present: no

## What to Build

Target journey **J-02** (deterministic, lookahead-free support/resistance levels), the natural
successor to iter-1's J-01 bar store. Required-still-passing: J-01, J-07 (both currently
`passing`/`already_passing` per `runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json`
— confirmed, not assumed).

- A new config-owned S/R detection module (`apps/backend/app/research/levels.py`) that, from a
  symbol's stored bar series (read via the existing `BarStore`), derives horizontal level
  candidates per timeframe:
  - **swing pivots** — a bar's high/low that is the extreme over its ±N neighbours (N config-owned)
  - **prior-period extremes** — prior day/week/month high/low/close, derived from whichever stored
    series matches that timeframe
  - each level carries **price, timeframe, type** (`swing-pivot`|`prior-period-extreme`),
    **touch_count**, and **strength = timeframe_weight × touch_count** — every parameter
    config-sourced, no magic numbers, no fitting, no ML
- **Lookahead-free as-of computation**: levels at time T use ONLY bars timestamped ≤ T; a level at
  T must be provably unchanged by any bar after T (the headline correctness property this
  iteration exists to prove).
- **Deterministic**: byte-identical output across independent re-runs on the same inputs.
- New route `GET /research/levels?symbol=<S>&as_of=<ISO-T>` in `research/routes.py`, serving the
  module's output verbatim (single source of truth; no second computation path).
- New read-only MCP `levels` tool in `mcp/__init__.py` — byte-identical proxy of the REST endpoint.
- New `sr_*`-namespaced config fields (pivot lookback N, touch tolerance, per-timeframe weights),
  ALL added to `config_fingerprint()`'s `excluded` set so `Config().config_fingerprint()` stays
  pinned at `4d665603569b9dbf`.
- Full test coverage per Key Test Scenarios below.
- Dev handoff at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-2-dev.md`.

**Out of scope this iteration** (per phase spec OUT OF SCOPE — flag and exclude if attempted):
confluence zones / A-B-C classification (J-03), the `structure_tape` strategy / backtest wiring /
PnL / promotion (J-04–J-06), any levels/bars UI view, recording NEW real bars (fixture is read-only
this iteration), a symbol-tradability distinction (add ONLY if genuinely needed to explain an empty
level set — the honest "no levels found" state is the spec's stated default), and any change to
the tape engine, `default` profile, `v1`, or the live cockpit.

## Agents Required

- developer: yes -- implements the S/R levels module, the `/research/levels` route, the MCP
  `levels` tool, and the new `sr_*` config fields (backend only). This repo's pipeline dispatches
  all implementation through the single `developer` agent role (see the 19-agent catalog) — there
  is no separate backend-data/frontend-ux agent split here. Mapped: backend-data: yes, frontend-ux: no.
- frontend-ux: no -- no frontend work; the phase spec explicitly forbids any `apps/frontend/`
  change this iteration (verify via empty `git diff -- apps/frontend/`, per DoD).

## Files to Create/Modify

- `apps/backend/app/research/levels.py` -- NEW. Mirrors `research/bars.py`'s module discipline
  (docstring-first ownership statement, no fabrication, honest failure taxonomy). Sole owner of
  level computation.
- `apps/backend/app/config.py` -- new `sr_*` fields (pivot lookback N, touch tolerance,
  per-timeframe weights). Give them a namespace distinct from the EXISTING intraday tape setups
  `level_break`/`failed_move_fade` (config lines ~487, ~1133) — a different "level" concept
  entirely; do not let the two collide in naming. Add every new field to the `config_fingerprint()`
  `excluded` set (mirror the `bar_dir`/`bar_timeframes`/... block at ~line 1256, same
  rationale-comment style) so the pinned `default` hash does not move.
- `apps/backend/app/research/routes.py` -- `GET /research/levels` (query params `symbol`, `as_of`),
  using the existing `get_bar_store()` dependency. No existing `?symbol=&as_of=` query-param GET
  precedent exists in this file (checked) — this is a new shape; use FastAPI's standard
  function-parameter query args with explicit 422 on missing/malformed `as_of`.
- `apps/backend/app/mcp/__init__.py` -- new `levels` tool. **Needs a new dispatch shape**: the
  existing `_STATIC_PATHS` (no args) and `_TAPE_PATHS` (single `{ticker}` path substitution, one
  optional query param special-cased for `tape_history`) don't fit — `levels` needs TWO REQUIRED
  query params (`symbol`, `as_of`), not a path substitution. Add a small parallel mapping/branch in
  `_request_path` that builds `/research/levels?symbol=<quoted>&as_of=<quoted>`, raising
  `ToolArgumentError` if either is missing (mirroring the ticker-argument validation style), plus a
  `types.Tool` entry with a 2-field required input schema.
- `apps/backend/tests/test_levels.py` -- NEW (mirrors `test_bars.py`): swing-pivot + prior-period
  unit tests on the committed PG fixtures, strength calc, lookahead-free proof, byte-identical
  determinism, a no-magic-numbers test (mirror `test_chunk_bounds_are_config_sourced_no_magic_numbers`),
  and the fingerprint-stability + real-threshold counter-test pair for the new `sr_*` fields
  (mirror `test_bars.py`'s equivalent pair — this is a NEW test pair, not an edit to
  `test_profile_equivalence.py::test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field`,
  which needs no change at all if exclusion is done correctly).
- `apps/backend/tests/test_levels_api.py` -- NEW (mirrors `test_bars_api.py`): route happy path
  with exact expected values, the honest empty/error states, 422s.
- `apps/backend/tests/test_mcp_server.py` -- extend `EXPECTED_TOOLS` with `levels`; add a
  byte-identity test against a seeded non-empty result (mirror
  `test_bars_tool_byte_identical_on_a_non_empty_live_list`).
- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-2-dev.md` -- NEW dev handoff.

No `apps/frontend/` file may change.

## Key Test Scenarios

- **Swing pivot on the committed fixture**: PG `1h` (9 bars, 2026-06-09T13:00–21:00Z, feed `sip`).
  Manual check of the committed highs/lows shows a config N=1 (2N+1=3 bars) already yields a clear
  swing-high (bar index 3, high 149.4796, both neighbours lower) and a clear swing-low (index 4,
  low 148.06, both neighbours higher) — i.e. the existing fixture likely already supports ≥1 swing
  pivot without extending it. Assert exact price/index values, not just "a pivot exists."
- **Prior-period extreme on the committed fixture**: PG `1d` (5 bars, early June 2026) — each day's
  high/low/close becomes a prior-period level referenceable by the following day's `as_of`.
- **Strength** = timeframe_weight × touch_count using config-owned weights — assert exact numbers.
- **Lookahead-free** (headline test): a level computed as-of T is byte-identical whether or not
  bars timestamped after T are present in the store.
- **Byte-identical determinism**: two independent runs on the same fixture produce identical JSON.
- **`GET /research/levels?symbol=PG&as_of=<T>` happy path**: exact price/timeframe/type/touch_count/strength.
- **Honest distinct failure states** (three, not one bare empty array): (a) a symbol with ZERO
  recorded bar series → an explicit state distinct from (b); (b) a symbol with bar series but no
  derivable levels at that `as_of` → explicit "no levels found" (never a silent empty-success that
  reads the same as a bug); (c) malformed/missing `as_of` → 422. (d) An out-of-set timeframe
  surfacing in a stored bar series still hits the existing 422 discipline.
- **MCP `levels` byte-identity**: tool output == REST response verbatim on a non-empty result;
  missing `symbol`/`as_of` raises `ToolArgumentError` before any HTTP call.
- **`config_fingerprint` stays pinned** at `4d665603569b9dbf` with the new `sr_*` fields present but
  excluded, PLUS the real-threshold counter-test proving a genuinely tape-computational config
  change still moves it.
- **No-magic-numbers** grep/introspection test over every S/R parameter in `levels.py`.
- **Regression sentinel (J-01, J-07)**: full backend suite green (iter-1 baseline: 1069 passed / 1
  skipped), `test_observer_equivalence.py` + `test_profile_equivalence.py` green, `git diff --
  apps/frontend/` empty, no `/research/strategies` or backtest/PnL code leaked in (J-04–J-06 stay
  unbuilt — a scope check, mirroring the iter-1 audit's route-count check).

## Assumptions & Notes

- **Grouping multiple bar series per (symbol, timeframe)**: `BarStore` has no "get by
  symbol+timeframe" accessor — only `list()` (all series) and `get`/`load_bars` (by id). The
  committed fixture has exactly one series per (symbol, timeframe), so this doesn't block
  acceptance, but if the store ever holds more than one series for the same pair, picking the
  most-recently-created one is a reasonable default the developer should document (DoD doesn't
  specify this); flag for reviewer if handled differently.
- **Vendor-confinement test doesn't currently scan `research/`**: `test_real_data_gate.py::test_engine_and_canonical_modules_reference_no_vendor`'s
  `targets` list is `["engine", "config.py", "serializers.py", "providers/base.py",
  "providers/simulated.py"]` — it does not include `research/`, so `levels.py` isn't mechanically
  gated on this today (neither was `research/bars.py` in iter-1). Keep `levels.py` vendor-neutral by
  construction anyway (it only ever touches `RawBar`/stored bar rows, never a vendor SDK) — cheap
  discipline, not a hard requirement this iteration.
- **Fixture extension is a last resort**: only touch `scripts/generate_bar_fixtures.py` /
  `tests/fixtures/bars/*.json` if the swing-pivot check above doesn't actually hold once
  implemented — never synthesize bars to pad a fixture (no-fabricated-data anti-goal).
- **Naming**: keep the new config namespace (`sr_*` or `structure_level_*`) and JSON field names
  distinct from the existing `level_break`/`failed_move_fade` tape setups — same concept-collision
  discipline iter-1 used to separate the two "bar" concepts.
- No upfront questions were needed: the phase spec is unusually prescriptive (exact endpoint shape,
  exact module mirroring target, exact fixture data, exact naming pitfalls carried forward from
  iter-1's lessons.md) and iter-1's foundation was independently verified healthy
  (`journey-history.json`: J-01 `passing`, J-07 `already_passing`; iter-1 audit verdict PASS;
  pinned fingerprint confirmed). Remaining decisions above are ordinary implementation judgment
  calls, documented rather than escalated, per the questioning policy.
