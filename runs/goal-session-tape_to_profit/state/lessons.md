# Goal Session tape_to_profit — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-1 — 2026-07-03T04:14:31+01:00

**Verdict:** CONTINUE
**Lesson:** The deterministic replay of required-still-passing journeys silently no-ops when Playwright is missing: engine.log shows "Playwright (Python) is not available" at the J-08 replay step, yet the merged UI report still claims "LLM browser-qa + deterministic replay" and reports "1/1 passed (0 skipped)" with no replay row and no failure. Only engine.log reveals the gap — a real J-08 regression could have passed unnoticed if the automated suite had not covered it.
**Applies to:** every future iteration (all carry J-08 as required-still-passing) — until `python3 -m pip install --user playwright && python3 -m playwright install chromium` is done, browser QA must explicitly execute required-still-passing browser legs, and the evaluator must demand a result row per required journey rather than trusting the merge header.

## iter-2 — 2026-07-03T06:00:19+01:00

**Verdict:** CONTINUE
**Lesson:** Machine-surface journeys (no frontend page) structurally cannot get golden replay scripts: `demo_runner.py` supports only goto/click/fill (no POST) and its `normalize_url` rewrites ANY localhost URL onto the single frontend base_url, so a `goto` aimed at the backend port silently hits the frontend instead. Their durable regression lane is the backend test suite; for browser-originated verification, Chrome MCP's `eval` issuing in-page `fetch()` from a backend-origin page works well (iter-2 drove POST/409/422 flows that way).
**Applies to:** J-03, J-04, J-06, J-07 (all machine-surface per the blueprint IA table) — dispatch browser-qa knowing no replay script will exist for them, and route their required-still-passing coverage through the automated suite, not the replay lane.

## iter-3 — 2026-07-03T08:34:58+01:00

**Verdict:** CONTINUE
**Lesson:** Three seemingly unrelated failures this iteration — the replay lane's Playwright Chromium killed at launch (SIGTRAP, engine.log 07:29:19), browser-qa's Chrome `net::ERR_INSUFFICIENT_RESOURCES` + hydration stalls, and sqlite `Disk quota exceeded` errors under pytest — share ONE root cause: `/tmp` is a tmpfs with a per-user quota (~5.2G = 80%), pinned at the limit by ~4.5G of accumulated pytest basetemp dirs in `/tmp/pytest-of-dennis-chan` (~4-5MB per suite run x hundreds of framework runs; pytest's keep-3 cleanup has not kept up). Symptom looks like flaky browsers or a broken product; it is neither. Workaround proven this iteration: run pytest with `TMPDIR` + `--basetemp` pointed at a root-filesystem dir; real fix is clearing the pytest dir (this evaluator's delete was permission-denied — operator action).
**Applies to:** every future iteration's browser-qa / replay / large-suite lane — before diagnosing "flaky browser" or unexplained sqlite I/O errors, check `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota first.
