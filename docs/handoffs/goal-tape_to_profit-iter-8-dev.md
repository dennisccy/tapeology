# goal-tape_to_profit-iter-8 Dev Handoff

**Phase:** goal-tape_to_profit-iter-8
**Date:** 05-07-2026
**Agent:** developer
**Status:** complete

## What Was Built

J-09 — the baseline-edge report machinery, `python -m app.research.edge_report --out <path>`:

- **`app/research/edge_report.py` (new).** Measures the CURRENT champion (read verbatim via
  `store.get_champion_pointer()` — never hardcoded `v1`/`default`) across every registered
  dataset. For each dataset, runs ONE backtest through the EXISTING `BacktestJobManager.create` +
  `run_sync` (the same computation path `pnl_scan`/`pnl_baseline` use) and reads the persisted
  row-31 `aggregates` and the seeded null baseline's own `aggregates` VERBATIM — no second R/$/edge
  computation anywhere. Train and hold-out are two separate, never-pooled report sections, each
  ranked by the champion's own net R on that dataset (descending, `dataset_id` tie-break). A
  hold-out dataset is flagged `positive_edge` iff `net_r > 0 AND net_usd > 0 AND n >=
  Config.pnl_min_sample_size AND` it beats its own null baseline on both net R and net $; train
  rows never carry the `positive_edge` key at all (honest omission, not a fabricated `False` — the
  concept simply does not apply to a train-split measurement). Zero qualifying datasets —
  including a true-empty registry — emits the exact literal finding `"no positive-edge dataset"`
  at exit 0. Strictly read-only: no `_promote`, no PnL-ledger write, no champion-pointer move —
  there is nothing here to promote, which is what makes "no train-only promotion" satisfied by
  construction. The report never collects a backtest-report id or a wall-clock field in the first
  place (simpler than the `pnl_scan` precedent, which collects then strips one field), so two
  independent fresh-state runs of an identical scenario are byte-identical by construction. A
  dataset failing integrity verification, or a backtest ending non-`done`, raises the explicit
  `EdgeReportError` before anything is written.
- **`apps/backend/tests/test_edge_report.py` (new).** 15 tests — see Tests Run below.
- **`apps/backend/tests/test_no_execution_path.py`** — one additive line: added
  `"backend/app/research/edge_report.py"` to `test_scan_is_not_vacuous`'s explicit path-presence
  assertions (the optional consistency polish the plan named, mirroring the `pnl_scan.py`
  precedent). No other change to that file.

No frontend, no REST endpoint, no MCP tool, no `/performance` change — confirmed a pure
machine-surface CLI artifact (see Known Issues for the explicit zero-diff verification).

## Files Changed

- `apps/backend/app/research/edge_report.py` (new) — the report engine + `__main__` CLI entry (270 lines).
- `apps/backend/tests/test_edge_report.py` (new) — 15 tests, all empirically grounded in real
  measured backtest numbers (never hand-typed assumptions — see Known Issues).
- `apps/backend/tests/test_no_execution_path.py` — one additive assertion line (see above).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1040 passed, 1 skipped** (0 failed, 0 errors) — up from the iter-7 baseline of 1025
passed / 1 skipped (net +15 = exactly the 15 new tests in `test_edge_report.py`; no test deletions
anywhere). `tests/test_observer_equivalence.py`: 7/7 passed (re-confirmed as part of the full run).
`tests/test_no_execution_path.py`: 4/4 passed. Targeted required-still-passing journey modules
(`test_datasets.py`, `test_datasets_api.py`, `test_backtests.py`, `test_pnl_ledger.py`,
`test_pnl_ledger_api.py`, `test_profile_equivalence.py`, `test_profiles_api.py`,
`test_pnl_scan.py`, `test_real_data_gate.py`) re-run standalone: all green.

`test_edge_report.py`'s 15 tests, by discipline:
1. Champion read verbatim, never hardcoded (moves the pointer to the one other registered
   profile, confirms the report AND every backtest it actually ran used it).
2. Empty registry → honest empty report, exit 0.
3. Committed fixture pair → `"no positive-edge dataset"`, with the train dataset failing on sign
   alone and the hold-out dataset failing on TWO independent gates at once (n<5 AND fails to beat
   its own null) — real measured numbers, not assumed.
4. Split separation (train/hold-out never pooled, no merged key exists).
5. Ranking descending by net R + exactly one hold-out dataset flagged (winner beats a real loser
   in the same split, test-local lowered minimum).
6. The `dataset_id` tie-break itself, proven as a pure-function check (see Known Issues).
7. The n-gate isolated (a real qualifying-except-for-n dataset, unflagged for that reason alone).
8. The beats-null gate isolated (fixture hold-out at a lowered minimum — net-positive but still
   unflagged because it fails to beat its own null).
9. Pure-render equality: every displayed value matches a FRESH, independently-run backtest over
   the identical (dataset, strategy, profile) byte-for-byte.
10. Determinism: two independent fresh-state runs via the real CLI produce byte-identical bytes.
11. Corrupt dataset → explicit `EdgeReportError`, no backtests even attempted.
12. CLI-level: corrupt dataset → exit 1, `--out` never created.
13. A backtest ending non-`done` (forced via the REAL cooperative-cancellation mechanism, never a
    hand-crafted fake payload) → explicit `EdgeReportError`.
14. The no-promotion-API grep guard (see Known Issues for why it's narrower than the plan's
    literal wording).
15. CLI smoke test on the fixture pair.

Live verification (not just tests) — mirrors the iter-7 `pnl_scan` precedent:
- `python -m app.research.edge_report --out <path>` run directly against the REAL
  `TAPEOLOGY_JOURNAL_DB` / dataset store (7 already-registered datasets — 5 train, 2 hold-out —
  from prior iterations' own work, plus the existing founding PnL-ledger row and champion
  pointer). Produced a well-formed, correctly-ranked, honest `"no positive-edge dataset"` report.
  Confirmed the champion pointer (`{v1, default}`), the PnL-ledger row count (1), and the dataset
  count (7) were all UNCHANGED afterward — the only new writes were the standard row-31 backtest
  rows the existing runner persists (the allowed side effect). Re-ran a second time: byte-identical
  `--out` output against the now-larger backtest history.
- Backend started via `scripts/start-backend.sh`, `GET /health` and `GET /research/profiles`
  verified over real HTTP, stopped, restarted on the same port — no conflicts, clean second stop.
  (No frontend files changed, so no frontend-build check beyond the full existing test suite.)

## Known Issues

- **Flagged judgment call: the "beats its own null baseline" comparator.** Per the plan's Design
  Note #1, I required BOTH the champion's hold-out `net_r > null net_r` AND `net_usd > null
  net_usd` — the codebase's established "gate on both R and $ jointly" convention (see
  `pnl_scan._is_positive`). Given the current strategy grammar's fixed `$-per-R` notional, `net_usd`
  and `net_r` are always exactly proportional for any trade population (`net_r = net_usd /
  dollars_per_r`, a positive constant), so checking both is currently redundant in practice — but
  matches the codebase's own convention and its documented "a dollar figure never appears without
  its R counterpart" philosophy, so I kept it rather than simplify it away.
- **Flagged judgment call: the ranking key.** "Rank each split's datasets by hold-out edge" (spec
  text) is applied per the plan's Design Note #3: within EACH section (train and hold-out
  independently), order that section's own datasets by the champion's OWN net R on that dataset
  (descending), tie-break `dataset_id` ascending. Train sections are ranked the same way (net R
  descending) even though they never carry a `positive_edge` flag — verified live against 5 real
  train datasets (see Tests Run).
- **`test_edge_report_source_calls_no_promotion_api` is narrower than the plan's literal
  wording.** The plan asked for one dedicated test proving BOTH "no broker/order/account/execution
  pattern" AND "never calls `set_champion_pointer`/`append_validation_row`". I initially wrote
  both checks into one test, but the broker-pattern literals (e.g. `"TradingClient"`,
  `"paper_trading"`) as DATA in my own test's forbidden-pattern tuple tripped the REPO-WIDE
  `test_no_execution_path.py` scanner — which flags any file merely *naming* those patterns as
  guard/policing data, exactly the reason it already self-allowlists its own file and
  `test_real_data_gate.py`. Rather than expand that scanner's allowlist (touching a shared,
  security-relevant file more than necessary), I narrowed my dedicated test to the two
  promotion-API calls only (the part NOT covered elsewhere), and rely on the pre-existing
  repo-wide scanner for the broker/order/account/execution-pattern clause — which I confirmed
  covers `edge_report.py` by adding it to `test_scan_is_not_vacuous`'s explicit path-presence
  assertions. Net effect is identical DoD coverage, split across two files instead of duplicated
  in one; flagging since it's a deviation from the plan's literal "one dedicated test" phrasing.
- **The `dataset_id` tie-break is tested as a pure function, not through a real backtest.**
  Engineering a genuine float tie in `net_r` between two DIFFERENT real recorded datasets is
  impractical to arrange deterministically. `test_rank_orders_by_net_r_descending_with_dataset_id_tiebreak`
  calls the module's own `_rank()` helper directly with representative (not fabricated-as-if-real)
  measurement dicts — this is testing a pure JSON-shaping/sorting function, not asserting on
  invented tape/PnL data, and every OTHER test in the suite uses real recorded datasets exclusively.
  All 15 tests (plus this design) were verified to have real teeth via targeted mutation testing
  during development (each of the sign gate, n-gate, beats-null gate, ranking order/tie-break, and
  the train-rows-never-flagged omission was independently broken and confirmed caught by at least
  one test) before finalizing.
- No other gaps against the phase spec's Definition of Done — pure-render equality, split
  separation, both-ways positive-edge proof (isolated per gate, stronger than the DoD's literal
  minimum), determinism, honest failure states, the no-execution/no-promotion guard, and the
  default-frozen cross-check (`config_fingerprint` still `4d665603569b9dbf`, no new `Config` field
  added) are all covered by passing, exact-value-asserting tests.
- **Three places where the independently-authored QA test plan
  (`reports/qa/goal-tape_to_profit-iter-8-test-plan.md`, written before this implementation
  existed) frames a scenario slightly differently than what I built — noting these explicitly so
  QA/review doesn't mistake a framing difference for a gap:**
  - **TC-08** describes the `REGISTER` string as attached "adjacent to" every individual `net_usd`
    field. I attached it ONCE at the report's top level (`report["register"]`), matching the
    EXISTING, twice-precedented codebase convention (`pnl_scan.py` and `pnl_baseline.py` both do
    exactly this) and the DoD's own "never re-declare it" instruction — repeating the identical
    string next to every dollar figure would itself be a form of re-declaration.
  - **TC-06** frames the positive-edge proof as "with minimum-n=5 [the shipped default] the
    qualifying dataset is flagged naturally, then re-confirm at minimum-n=1." The phase spec's own
    Key Test Scenario 6 text explicitly offers the technique I used instead: "a controlled scenario
    (test-local `dataclasses.replace`-lowered minimum ... never by weakening the shipped default)."
    Constructing a dataset that naturally reaches n≥5 total trades (rather than the n=1 single-trade
    datasets used throughout this suite and its two `pnl_scan.py` /`pnl_baseline.py` precedents) adds
    real engineering cost for a proof the DoD text itself says is unnecessary.
  - **TC-10**'s literal grep (`set_champion_pointer|append_validation_row|broker|order|account`) run
    directly against `edge_report.py`'s prose docstrings will surface one benign hit — the word
    "ordered" in "datasets are **ordered** by the champion's own net R" (describing sort order, not
    a trade order). TC-10's own pass criteria already anticipates this ("zero matches, or only in
    comments/strings that are safe").
