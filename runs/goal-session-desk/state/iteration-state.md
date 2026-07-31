# Iteration State — desk

**After iteration:** 29 · **Date:** 2026-07-31 · **Verdict:** GOAL_ACHIEVED

## Journeys

18 passing (J-01..J-18) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` · 0 `pending_infra` · 1 `evidence_makeup` (J-18) — 18 total (merged results 17/18 PASS, 1 SKIP; all 18 `spec_hash` values match current `docs/goal.md`).

## Active blockers

- **none blocking the goal.** THREE disclosed, non-blocking items, all harness/asset-side, none a product defect:
- (1) `runs/goal-session-desk/journey-scripts/J-18.json` steps 2-3 assert TODAY's ambient ids (`screenrun-…-0662273df270` / `screen-2026-07-31-c169546856c7`). The next real screen run on a new UTC date makes it report a FALSE regression. Repoint at `desk-screen-runs-table` + the stable substrings `no walk was performed` / `101 / 101`, then replay-verify with the rig up.
- (2) `reports/phase-goal-desk-iter-29-demo.json` step 5 CLICKS "Run Screen" against the ambient `:3301` rig — on a pin-miss day that starts a real ~1m41s 101-member walk and writes a real snapshot into the owner's `.data`. Demo scripts must stay read-only over the ambient store.
- (3) J-18's honest empty-state screenshot does not exist (blank-frame tool bug, then the lane's own click populated the append-only ledger for good). Needs a fixture-scoped rig; behaviour already proven by TC-1 + a live 200 `{"runs": [], "latest": null}` + a live DOM read.
- Coupling to watch: `test_desk_ui_guards.py` reads `journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 29: GOAL_ACHIEVED — J-18 built and verified on artefacts the evaluator opened: the run record is byte-identical to its snapshot (101/101, 100 ranked, 1 `no_basis`, same five pins), the reuse short-circuit measured 1m41s → 14ms with the same `screen_id` and NO second snapshot file, and the `[NEW]` film's own frames show the populated ledger (a first for a new journey this session). Suite 1500 pass/8 skip/0 fail, `08e471b10130e1e2`, 17 MCP tools, 16/16 record checksums verify, scan CLEAN, coherence COHERENCE-WARN (no blocking violation).
- iter 28: GOAL_ACHIEVED — zero product diff; 17/17 passing; J-17's `[NEW]` film cleared to the owner's OPTIONAL track after 3 harness-caused failures, disclosed rather than treated as met.

## Do not redo

- **J-18 is BUILT and verified** — `app/research/desk_screen_log.py` (sole owner), the five-pin pre-check + reuse short-circuit inside `run_screen_and_record` (`desk_screen_compute.py`), `GET /research/desk/screen/runs` (`desk_routes.py:498`), the fourth `/desk` "Screen Runs" section (`app/desk/page.tsx:2255`). Do not re-implement or re-photograph the populated/reused states.
- **The auditor's B1 fix is IN and counter-tested** — one-shot `logged` latch at `desk_screen_compute.py:170-186` + `test_a_terminal_log_write_that_raises_is_never_re_logged_as_a_second_failed_record` (:998). Do not revert.
- **The optional `screen_run_store=` kwarg is a DISCLOSED, ratified departure** from J-09/J-10's required parameter — it exists so the three protected tests pass unmodified. Do not "fix" it to required; add T2's CLI assertion instead.
- Do NOT run a capture-only iteration; the J-18 empty-state picture rides the make-up lane. Do NOT re-verify J-01..J-17 as an iteration goal (10 replayed green, 7 spot-checked this run).
- J-16 layout is DONE and measured (`table-fixed` + 13-col `<colgroup>`). No 14th column, no width re-tuning; `band `/`opposite ` in-cell prefixes MUST stay. Never script a `click` inside a `/desk` ranked/skipped row — the stretched `absolute inset-0` anchor blocks it; use `expect`-only.
- Zero diff stays law: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `meta.py`, `mcp/__init__.py`, both charts, the guard test files; pin `08e471b10130e1e2`; 17 MCP tools; zero new `Config` fields. Accepted non-defects: replay/demo frame duplication, 2/100 rows at 63 px, the reused-run amber "N not reached" chip (F1, cosmetic).
