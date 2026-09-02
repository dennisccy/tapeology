# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This was the baseline check of a brand-new era. No code was written on purpose, and none was
written: the change scan and my own check both show zero changes under the product folders. The
browser check confirmed what the plan predicted — the new machine-readable page
`/tape/SIM-BIDABS/observation` does not exist yet (the server answers "Not Found"), so the first
five journeys fail, and the sixth is half done: the era's paperwork and the three existing pages
are fine, but its guard test file has not been written. Nothing went wrong; we now have an honest
starting line.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 "Artifact is a pure projection with identity, provenance, integrity" | (none — first record) | failing | `reports/phase-goal-observation-contract-iter-0-ui-test-results.md` row UT-J-01; `reports/qa/goal-observation-contract-iter-0-evidence/J-01-fail.png` (shows `{"detail":"Not Found"}`) |
| J-02 "Three honest time instants, read atomically" | (none — first record) | failing | row UT-J-02; `reports/qa/goal-observation-contract-iter-0-evidence/J-02-fail.png` (same 404 body) |
| J-03 "Lifecycle, feed basis and session identity stay honest" | (none — first record) | failing | row UT-J-03; `reports/qa/goal-observation-contract-iter-0-evidence/J-03-fail.png` (404 at every lifecycle step) |
| J-04 "Ingestion-path equivalence" | (none — first record) | failing | row UT-J-04; `reports/qa/goal-observation-contract-iter-0-evidence/J-04-fail.png` (no hashes exist to compare) |
| J-05 "One read-only machine path" | (none — first record) | failing | row UT-J-05; `reports/qa/goal-observation-contract-iter-0-evidence/J-05-fail.png`; contrast proof in the row: `/tape/ZZZZ/state` returns the matched body `{"detail":"Ticker 'ZZZZ' is not being watched"}`, so `/observation` genuinely has no route |
| J-06 "Guards and the regression sentinel" | (none — first record) | partial | row UT-J-06; `reports/qa/goal-observation-contract-iter-0-evidence/J-06-partial.png` (the `/desk` page renders with its existing panels only, no observation panel). Era-open documents present and `/`, `/structure`, `/desk` unchanged = pass; `tests/test_tape_observation_guards.py` absent = fail |

Verified by me directly, not taken from prose: `apps/backend/app/observation_contract.py` does not
exist, `grep -n "observation" apps/backend/app/main.py` returns nothing, and no
`tests/test_tape_observation_*.py` file exists. Backend test collection independently re-run by me:
**3938 tests collected**, matching the developer and reviewer figures exactly (they both recorded
3930 passed / 8 skipped / 0 failed from full runs; browser QA's own re-run of the full suite did not
finish inside its time budget and is honestly recorded as unknown there — it is not load-bearing for
any journey status, since every status above rests on a file/route being present or absent).

Note on evidence images: J-01 and J-02 share one screenshot file (identical bytes) and J-03, J-04 and
J-05 share another. That is expected here — every one of those steps returns the same "Not Found"
body — and each row's written steps record the distinct navigation that produced it.

Coherence audit: `runs/goal-session-observation-contract/iter-0/coherence.md` was not produced this
iteration. Under the decision rules a missing coherence file counts as "not clean", which only bars a
success verdict; it does not affect this CONTINUE. No coherence violation is claimed or implied here.

## Anti-goal Check

Basis: `runs/goal-session-observation-contract/iter-0/scan-report.md` (**CLEAN — no secret,
dependency or license findings**), `runs/goal-session-observation-contract/iter-0/iter-diff.md`
(its four files are the already-committed era-open documents from commit `2f3d2b32`, not this
iteration's work), and my own `git diff --stat -- apps/ docs/ project-extensions/ scripts/`, which
is **empty**. Anti-goal ledger classified by `scripts/automation/lib/anti_goal_disposition.py
summary`: total=0, resolved=0, unresolved_blocking=0, unresolved_non_blocking=0, unresolved_critical=0.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | scan-report CLEAN; no config or env file appears in the diff file list; the only modified tracked file is `reports/qa-scoped-backend-store-manifest.md`, whose diff is purely local scratch-store paths written by a pytest fixture (inspected line by line) |
| Paid / external SaaS dependency | OK | no manifest changed (`package.json`, `requirements*.txt`, `pyproject.toml` all absent from the diff); scan-report reports no dependency findings |
| License change | OK | no LICENSE file or license field in the diff; scan-report reports no license findings |
| Fabricated / substituted data presented as real | OK | browser evidence is Sim mode (`SIM-BIDABS`) on the local backend, and the failures are recorded as literal served bodies; no fixture is dressed up as real data |
| Rail 1 no execution path / Rail 2 no profit claims | OK | zero product code changed, so no execution or claim surface was added |
| Rail 3 frozen foundations | OK | `config_fingerprint` live-computed `08e471b10130e1e2` (dev + browser QA), MCP contract 28 tools, backend collection 3938 tests — identical to the previous era's closing baseline |
| Rail 6 single source of truth / Rail 7 deterministic / Rail 8 read-only MCP / Rail 9 immutable data / Rail 10 scoped persistence | OK | no code, no route, no MCP tool, no dataset touched this iteration |
| Source-authoring laws 1-4, 6 | OK | not engaged — no research source, formula, threshold or proxy was authored or changed |
| Era-specific: no trading/verdict token, no second engine, no route snapshotting an engine, no invented git provenance, no `content_hash`, no new UI file, no new `Config` field, no new MCP tool | OK | all vacuously satisfied — the observation module, route and tests do not exist yet and nothing was added; `git diff -- apps/frontend` empty |
| Era-specific: no weakening of the nine named existing guards | OK | none of the guard test files was edited (empty `git diff -- apps/`); collection count unchanged at 3938 |
| Era-specific: no mandatory journey needs Alpaca / network / credentials | OK | every step ran in Sim mode against the local backend; the 8 skips are the pre-existing environment-gated integration tests |
| Goal-Mode: no guard edited/skipped/xfailed to pass a journey; no fabricated browser proof; host-guard intact; no proposer self-extension | OK | no test file changed; failures reported honestly as failures; `project-extensions/` diff empty; no proposer ran |

No violation observed, minor or critical. Nothing was recorded in the violation ledger.

## Next-Step Recommendation

Build the first block of the era's required order: the constants, the builder that assembles the
observation, and the two hash rules, together with the test file
`apps/backend/tests/test_tape_observation_projection.py` — this is journey J-01 "the artifact is a
pure projection with identity, provenance and integrity". Do not start the web address
`/tape/{ticker}/observation` yet; the goal's binding order puts the route fifth, after time,
lifecycle and path-equivalence work. Because there is no route yet, the browser step for the next
iteration can only show the same "Not Found" page, so J-01 will stay failing until the route lands —
that is expected and is not a reason to reorder the work. Next iteration should run at lean depth
(the goal's own default while no frontend changes), and the person approving this only needs to
agree with one thing: the next iteration writes backend code and tests only, and changes nothing a
user can see.
