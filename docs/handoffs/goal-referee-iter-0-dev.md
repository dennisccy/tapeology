# goal-referee-iter-0 Dev Handoff

**Phase:** goal-referee-iter-0
**Date:** 2026-08-14
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is Era 6 "The Referee"'s **verify-only baseline** (Mode: baseline,
Depth: lean). Per the iter spec's IN SCOPE section, Backend and Frontend are both explicitly
"(none — baseline verification only; no code changes this iteration)"; the iteration's real
scope is the checklist of read-only "Verification tasks." My part of that checklist was the
non-browser half: live route/config/MCP/test-suite checks against the current codebase plus a
scratch backend/frontend, recording evidence for J-01–J-02, J-04–J-06, J-08–J-09, and J-10's
non-browser (KEPT-behavior) half, plus confirming the decomposer-authored `blueprint.md`
already satisfies its DoD item. Browser-dependent evidence for J-07, J-09's rendered sections,
and J-10's visual walkthrough is explicitly deferred to the browser-qa-agent step (T-10: no
screenshot ⇒ `unknown`, never `passing`).

**No source file was created, modified, or deleted this iteration.**

```
$ git diff --stat -- apps/          (from repo root)
(empty)
$ git status --short -- apps/       (from repo root)
(empty)
$ git status --short
?? docs/phases/goal-referee-iter-0.md
?? reports/goal-session-referee-index.html
?? runs/goal-session-referee/
```

All three untracked entries are pipeline/session artifacts written by the goal-decomposer
before this developer step ran (the iter spec itself, the session state directory including
the already-drafted `blueprint.md`, and a rendered session index) — not product source. This
confirms TC-10 and the DoD's "no anti-goal violation introduced" item directly.

## Journey-by-journey verification evidence

Live checks ran against a scratch dev-stack instance (`scripts/dev.sh`, this checkout's
deterministic port-hash offset: backend `:8301`, frontend `:3301` — confirmed by direct offset
computation and by the script's own startup banner) plus direct source-tree grep. Every spec
baseline prediction (J-01–J-09 failing/not-started, J-10's kept product intact) was **confirmed
on every point checked**.

### J-01: Reconciliation made testable — CONFIRMED FAILING (not started)

- `find apps/backend/app/research -iname "*referee*"` → zero results. Case-insensitive grep for
  `referee` across `apps/backend/app/` (all `.py`) and `apps/backend/tests/` (all `.py`) → **zero
  matches in either tree** — `app/research/referee_evidence.py` does not exist, and no file
  anywhere in the backend even contains the word.
- `find apps/backend/tests -iname "*referee*"` → zero results — `tests/test_referee_guards.py`
  does not exist yet, so neither the doc-drift guard nor the catalog-reconciliation guard is
  built.
- Live: `GET /research/desk/referee/evidence` → **HTTP 404** `{"detail":"Not Found"}` (fresh
  boot, confirmed twice across two independent dev-stack boot cycles).
- `docs/referee-statistical-spec.md` confirmed present and unmodified this iteration: **371
  lines** (exact line count matches the number `docs/goal.md`'s BACKGROUND cites).

### J-02: The evidence contract — CONFIRMED FAILING (not started)

- Same absence as J-01 covers this journey directly: `referee_evidence.py` does not exist, so
  neither adapter (Playbook nor strategy) nor the derived observation cache can exist, and no
  fixture goldens can be located (`find` for any `*referee*` fixture path returns nothing).

### J-03: The statistics core — CONFIRMED FAILING (not started)

- `find apps/backend -iname "referee_stats.py"` → zero results.
- `find apps/backend -iname "test_referee_oracles.py"` → zero results.
- No oracle suite exists to run; `REFEREE_ORACLE_BUDGET_SECONDS` is not defined anywhere
  (covered by the same whole-tree `referee` grep returning zero matches).

### J-04: Matched nulls — CONFIRMED FAILING (not started)

- `find apps/backend -iname "referee_null.py"` → zero results (same whole-tree absence).
- Live: `GET /research/desk/referee/nulls` → **HTTP 404**; `GET
  /research/desk/referee/nulls/compute` → **HTTP 404**.

### J-05: The registry — CONFIRMED FAILING (not started)

- `find apps/backend -iname "referee_registry.py"` → zero results.
- Live: `GET /research/desk/referee/registry` → **HTTP 404**; `POST
  /research/desk/referee/registry/hypotheses` (with an empty JSON body) → **HTTP 404** — the
  route is not registered at any sub-path, let alone reachable enough to validate a payload.

### J-06: Estimand engines + adjudication — CONFIRMED FAILING (not started)

- `find apps/backend -iname "referee_adjudicate.py"` → zero results.
- Live: `GET /research/desk/referee/adjudications` → **HTTP 404**.

### J-07: The starter family / registration flow — CONFIRMED FAILING (not started); browser evidence deferred

- Case-insensitive grep for `referee` in `apps/frontend/app/`, `apps/frontend/components/`, and
  `apps/frontend/lib/` → **zero matches anywhere** — no shortlist table, no registration
  confirmation step, no referee-prefixed fetch helper or type.
- Fetched the live rendered `/desk` page's raw HTML (`curl http://localhost:3301/desk`, 20,610
  bytes) and grepped it case-insensitively for `referee` → **zero matches** (corroborating,
  non-authoritative for client-hydrated content — the source grep above is the authoritative
  absence check).
- Live: `GET /desk` (frontend, both scratch boot cycles) → **200** — the page still loads (kept
  behavior intact); this is a status-code + raw-HTML check only, not a rendered/hydrated-content
  screenshot.
- **Not verified by me this iteration** (browser-qa-agent's step, T-10): the screenshot proving
  no shortlist/registration UI renders anywhere on the page after a T-9 clean `.next` rebuild.

### J-08: The strategy family + promotion interlock — CONFIRMED FAILING (not started; pre-Era-6 gate runs unchanged)

- `grep -rn "authorize_promotion" apps/backend/app/research/` → **zero matches** — the function
  named in the spec does not exist anywhere in the codebase yet.
- Read `apps/backend/app/research/pnl_scan.py`'s `_promote` function directly (lines 267–327,
  matching the goal doc's own build anchor). Its current logic: require exactly one train and
  one hold-out dataset (else skip promotion with an honest note) → unconditionally call
  `append_validation_row` (the ledger write) → **only then** call
  `store.set_champion_pointer(...)`. There is no certificate lookup, no
  `authorize_promotion` call, no gate of any kind beyond the dataset-count check — confirming
  TC-4's expected pre-Era-6-gate-only behavior by direct source inspection, not inference.
- Isolated re-run of the promotion-focused tests: `cd apps/backend && .venv/bin/python -m
  pytest tests/test_pnl_scan.py -k promot -q` → **7 passed**, 0 failed (the 7 test functions:
  `test_min_n_gate_promotes_at_or_above_minimum`,
  `test_overfit_is_positive_train_failing_holdout_and_is_never_promoted`,
  `test_mid_promotion_crash_leaves_no_orphan_and_no_silent_double_append`,
  `test_strategy_axis_mid_promotion_crash_leaves_no_orphan_and_no_silent_double_append`,
  `test_strategy_axis_min_n_gate_promotes_at_or_above_minimum`,
  `test_strategy_axis_overfit_is_positive_train_failing_holdout_and_is_never_promoted`,
  `test_strategy_axis_more_than_one_dataset_per_split_skips_promotion_with_honest_note`).
  Together with the source read, this confirms a fixture candidate promotes today strictly
  under the pre-Era-6 gate — exactly the baseline TC-4 predicts.

### J-09: The Referee on `/desk` + MCP contract v5 — CONFIRMED FAILING (still the 20-tool contract)

- `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple (lines 56–77) has **exactly
  20 entries** ending in `get_endpoint`: `tape_state, tape_features, tape_history, datasets,
  bars, levels, tradability, setups, backtests, strategies, edge_report, desk_universe,
  desk_screen, desk_forward, desk_playbook, desk_playbook_evidence, pnl_ledger, taxonomy,
  ui_route_map, get_endpoint`. Neither `desk_referee` nor `desk_referee_registry` appears.
- Independent live corroboration (not just a source grep): this session's own connected
  `tapeology` MCP server exposes exactly the same 20 `mcp__tapeology__*` tool names — matched
  one-for-one against `EXPECTED_TOOLS` above with zero extras and zero omissions.
- Attempted a live MCP proxy call through that same connection (`ui_route_map`, which proxies
  `GET /meta/ui-routes`): it **honestly errored** — `"tapeology backend unreachable at
  http://localhost:8000 (GET /meta/ui-routes): ConnectError: All connection attempts failed —
  no cached or fabricated data is served"`. Confirmed via `ss -ltnp | grep :8000` that nothing
  is bound to that port; I deliberately did not stand up a `:8000` instance myself (leaving it
  free for the operator's own manual use — the same reasoning every prior baseline iteration
  used the deterministic scratch offset for). This demonstrates the honest-no-fabrication MCP
  contract live; the 20-tool count itself is already independently confirmed two other ways
  above.
- Frontend: same zero-match grep as J-07 covers the absence of all three new sections (Referee
  Registry / Referee Adjudications / Referee Runs) — no referee-prefixed `data-testid` or
  heading string exists anywhere in `apps/frontend/`.
- **Not verified by me this iteration** (browser-qa-agent's step, T-10): the screenshot proving
  every shipped `/desk` section still renders exactly as before AND none of the three new
  sections appear, after the T-9 clean rebuild.

### J-10: The kept product stands — KEPT-BEHAVIOR HALF CONFIRMED; browser walkthrough deferred

Non-browser evidence (dev-level):

- **Full backend suite: exactly 2,418 passed / 8 skipped / 0 failed / 0 errors.** This
  project's pytest configuration emits no final summary line (a known, already-documented
  quirk — confirmed again this run), so the count was taken by a character-exact "progress
  census" over the `-q` dot-stream (`.`=passed, `s`=skipped, and zero `F`/`E`/`x`/`X`
  characters anywhere in the log): 2,418 `.` + 8 `s`, nothing else. Zero occurrences of
  `FAILED` or `ERROR` anywhere in the log. This **matches `docs/goal.md`'s stated era-open
  floor "2,418 pass / 8 skip" exactly** — zero drift, confirming the live figure the DoD asks
  for.
- Skip breakdown (all eight are the standard two-stage `TAPEOLOGY_LIVE_INTEGRATION=1` opt-in
  gates, confirmed by reading each file's `pytest.skip(...)` call site directly — not
  credential failures, expected and honest for an autonomous, keyless run): `
  tests/test_live_integration.py` (1), `tests/test_event_recording_integration.py` (1),
  `tests/test_desk_universe_live_integration.py` (1), `tests/test_yahoo_live_integration.py`
  (5, one per test function, each gated behind the same env-var check) — `1+1+1+5 = 8`,
  matching the census exactly.
- Engine equivalence: `tests/test_profile_equivalence.py` and `tests/test_observer_equivalence.py`
  both exist and ran clean as part of the full suite above (0 failures in the whole run covers
  them).
- `config_fingerprint` (direct python invocation, not grepped): `cd apps/backend &&
  .venv/bin/python -c "from app.config import Config; print(Config().config_fingerprint())"` →
  `08e471b10130e1e2` — matches the pinned value exactly.
- `GET /meta/ui-routes` (live) →
  `{"routes":[{"path":"/","label":"Cockpit","nav":true},{"path":"/structure","label":"Structure","nav":true},{"path":"/desk","label":"Desk","nav":true}]}`
  — exactly 3 entries, matching `app/meta.py`'s `UI_ROUTES` source exactly.
- `GET /health` → **200**; `GET /research/taxonomy` → **200** (kept surfaces unaffected).
- `GET /`, `GET /desk`, `GET /structure` (live frontend, both scratch boot cycles) → all
  **200**.
- **Not verified by me this iteration** (browser-qa-agent's step, T-10): the cockpit sim tape +
  chart walkthrough, `/structure` pinned-AAPL Load, and every shipped `/desk` section's actual
  visual rendering (universe/coverage, screen briefing + history calendar, forward returns,
  refresh chain + compute controls, briefing, skipped members, runs/pins/compare/provenance,
  every Playbook section with context columns/filters/cohort views) — all require visual
  confirmation via screenshot after a clean `.next` rebuild (T-9), not a GET probe.

## `blueprint.md` (DoD item — already drafted, not by me)

`runs/goal-session-referee/state/blueprint.md` already existed when this developer step
started (goal-decomposer-authored, same iteration-0 dispatch). Verified it satisfies TC-11: the
"Information Architecture" section lists the unchanged 3-route nav skeleton (Cockpit `/`,
Structure `/structure`, Desk `/desk`) with Desk explicitly mapped to the three NOT-YET-BUILT
sections (Referee Registry / Referee Adjudications / Referee Runs) plus a feature/journey-home
table covering all ten journeys; the "Data Contract" section lists **exactly 7** Era-6 rows
(referee evidence, matched-null records, null compute progress/runs, registry, evaluation
records/runs, adjudications, promotion-authorization verdict), each with one named owner module
and one serving endpoint, verbatim from `docs/goal.md` § Product Shape, plus a baseline note
confirming the same zero-`referee_*.py`/20-tool findings independently reached above. Not
edited — already correct on inspection.

## Files Changed

- (none — verify-only baseline; zero source modifications under `apps/`)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **2,418 passed, 8 skipped, 0 failed, 0 errors** (progress-census method — see J-10
above for the exact methodology and skip breakdown). Matches `docs/goal.md`'s cited era-open
floor exactly.

Targeted re-run for J-08 evidence: `cd apps/backend && .venv/bin/python -m pytest
tests/test_pnl_scan.py -k promot -q` → **7 passed, 0 failed**.

`config_fingerprint` (direct python, not from the suite): `08e471b10130e1e2` — matches the
pinned value exactly.

`EXPECTED_TOOLS` (direct source read, `apps/backend/tests/test_mcp_server.py` lines 56–77):
**20 entries**, cross-checked against this session's own live MCP tool manifest — exact match,
no referee tools present.

## Service startup verification

- `bash scripts/dev.sh` (deterministic scratch ports 8301/3301, confirmed by direct offset
  computation matching the script's own printed banner) started both services clean on a
  **first boot**: backend `Application startup complete` + `/health` → 200 immediately;
  frontend `Ready in 1414ms`. Stopped via port-based kill (`fuser -k -9 8301/tcp` and
  `3301/tcp` — the documented `next dev`/`uvicorn --reload` child-process gotcha means a
  parent-PID-only kill can miss grandchild workers; port-based kill reliably reached every
  bound-socket process both times). Verified fully free via `ss -ltnH`/`lsof` after each stop.
- **Restarted** `scripts/dev.sh` on the same ports (second boot) — both services came up clean
  again: `Application startup complete`, frontend `Ready in 1205ms`, zero `error`/`EADDRINUSE`/
  "address already in use" strings in either boot log. Re-ran the referee-route and kept-route
  sanity probes on this fresh second instance (still 404/200 exactly as before), then did a
  final stop the same way; confirmed clean (`ss -ltnH`/`lsof`/`ps aux` — no residual
  `uvicorn`/`next-server`/`next dev` process tied to this project's PIDs; the only matching
  processes found belong to an unrelated sibling project on this host, `trendora`, on its own
  ports `8255`/`3255` — untouched by me).

## No side effects (baseline hygiene)

- Every live probe this iteration was a **read-only GET or a 404-only POST against a
  non-existent route** (`/health`, `/research/desk/referee/evidence`,
  `/research/desk/referee/nulls` [+ `/compute`], `/research/desk/referee/registry` [+ `POST
  .../hypotheses`], `/research/desk/referee/adjudications`, `/meta/ui-routes`,
  `/research/taxonomy`, `/`, `/desk`, `/structure`) — no write ever reached a real handler
  (every POST attempted 404'd before any handler ran), so no journal/dataset/bar-series/
  universe/screen/forward/playbook record was created or mutated.
- The one live MCP proxy call (`ui_route_map`) errored before reaching any backend (nothing
  bound on the MCP server's configured `:8000` target) — confirmed read-only by construction
  (a GET-only proxy tool) and by the honest-error outcome itself.
- No Alpaca, Yahoo Finance, or Wikipedia network call was made or attempted.
- The scratch dev-stack used this project's real local `.data/`/DB files; safe given the
  read-only constraint above.

## Known Issues

- **Environment drift (carried over from every prior era baseline):** `.claude/project-template.md`
  is still the generic, unfilled vendored template (placeholder text like `<e.g., Python 3.12>`,
  `<your project name>`) — never customized for this project, confirmed again this iteration.
  `README.md`'s own `<!-- TODO -->` comment above its "How to run" section documents this gap
  explicitly and points to the verified commands used instead (`scripts/dev.sh`,
  `scripts/start-backend.sh`, `apps/backend/pyproject.toml`, `apps/backend/tests/`). The iter
  spec itself also gave the exact test command directly, which I used verbatim. Not this
  iteration's scope to fix.
- Full click-through browser verification of J-07 (shortlist/registration — expect absent),
  J-09 (three Referee sections + MCP tool count — expect absent/20), and J-10's kept-behavior
  walkthrough (cockpit sim tape + chart, `/structure` pinned-AAPL Load, every shipped `/desk`
  section) is the browser-qa-agent's step per the spec's TESTING REQUIREMENTS; the evidence
  above is the dev-level route/config/MCP/suite inspection leg only, per T-10 ("no screenshot ⇒
  `unknown`, never `passing`"). That step must precede its screenshots with the T-9 clean `rm
  -rf apps/frontend/.next` rebuild.
- No credential blockers this iteration — none of J-01–J-09's baseline checks need Alpaca/
  Yahoo/Wikipedia network access; the 8 suite skips are the standard two-stage
  `TAPEOLOGY_LIVE_INTEGRATION=1` opt-in gates, not missing-credential failures.
- A live MCP proxy confirmation of the 20-tool contract against a running `:8000` backend was
  not performed (see J-09 above) — the MCP server targets the default `:8000` port, which I
  deliberately left unbound rather than occupy with a scratch instance; the tool-count claim is
  independently confirmed two other ways (source `EXPECTED_TOOLS` + this session's own live MCP
  tool manifest) instead.
- **`journey-history.json` was intentionally NOT written by me.** Per `.claude/workflow.md`'s
  artifact table, that file is the goal-evaluator's output (it reads this handoff plus the
  upcoming browser-qa report and records the actual verdicts + evidence pointers); writing to
  it here would risk conflicting with the evaluator's own read/write pass. This handoff
  supplies the non-browser half of the evidence the evaluator needs per journey; the
  browser-qa-agent supplies the rest.

## Suggested Next Phase

Confirms the iter spec's own NOTES and `docs/goal.md`'s dependency order (J-01 → J-02 → J-03 →
… → J-09, with J-10 guarding continuously): iteration 1 should build **J-01 alone** — the first
slice of `app/research/referee_evidence.py` (the per-family readiness fold: playbook family
records/distinct-sessions/signals-at-current-`detector_basis`/per-(setup,side) n/n_sessions;
strategy family dataset/split/trade counts plus the honest "tick gate unmet" statement and the
Card-6.4 `basis_caveats` disclosure text) behind `GET /research/desk/referee/evidence`, plus the
two guards `tests/test_referee_guards.py` needs (the `playbook-band-context-v3` doc/code-match
pin + zero-diff-to-`desk_playbook_context.py` pin, and the `docs/research-directions.md`
catalog-reconciliation string-presence pin). It is both first in the natural dependency order
and the unblocker for every later Referee journey — nothing else (the evidence contract's
adapters, the stats core, matched nulls, the registry, adjudication, the starter family, the
promotion interlock, or the `/desk` sections) can exist until this readiness fold and its
guards do.
