# Goal Session rapid-microscope — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-16T23:11:10Z

**Verdict:** CONTINUE
**Lesson:** `apps/backend/pyproject.toml` already sets `addopts = "-q"`, so running
`pytest tests/ -q` stacks to verbosity -2 and pytest swallows even the final
"N passed, M skipped" summary line — iteration 0 had to reconstruct 2691/8 by counting
dot-grid characters. Invoke `pytest tests/` (no extra `-q`), or add `-v`, to get the count
directly. Separately: `runs/goal-rapid-microscope-iter-0/status.json` still reads
`browser_checks_run: false` after a completed browser pass (it is written at `dev_complete`
and never refreshed) — trust `reports/phase-*-ui-test-results.md` and the evidence directory,
not that flag.
**Applies to:** every iteration that records the backend suite count for J-10, and any agent
reading status.json to decide whether browser QA ran.

## iter-1 — 2026-08-17T02:20:00Z

**Verdict:** ESCALATE
**Lesson:** The mandated store-scoped browser rig (`:8301`, forced on by
`project-extensions/store-scope/store-scope.env` + `apps/backend/scripts/start_scoped_qa_backend.sh`)
sets `TAPEOLOGY_DATASET_DIR` to a fixture dir its seeder never populates with tick datasets — so a
tick-corpus panel renders an honest but empty 0/0/[] and any acceptance naming real-corpus values
(J-01's `distinct_symbol_days: 12`) is structurally unprovable through the browser lane, no matter
how correct the code is. The repo already ships usable tick fixtures at
`apps/backend/tests/fixtures/datasets/`; seed them (or scope the readiness cache and let the rig
read the real corpus read-only) BEFORE a browser acceptance depends on non-empty tick data.
**Applies to:** any iteration whose browser acceptance reads the tick corpus — J-06's vault
states, J-08's four `/desk` micro sections, and J-09's study results all hit this same wall.
