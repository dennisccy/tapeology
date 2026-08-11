# Iteration 8 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The Playbook Evidence table is real and honest. I opened the pictures myself: one screen shows a
thin cell (3 signals, marked "low n") sitting right beside a full cell (14 signals, no mark), both
with real numbers, and a second screen shows the whole new section with its heading, its plain-English
disclosure paragraph and the signal-versus-random-chance columns side by side. All eight older
journeys were re-run automatically on a clean test copy and all eight passed. Two things stop this
being the end: the Claude tool list still has 18 entries where the goal asks for 20, so J-09
"MCP contract v4" is not built and J-10 "The kept product stands" cannot close.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The signal contract | passing | passing (re-run on the scoped test copy) | reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-J-01.png; reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-results.md |
| J-02 Every signal measured | passing | passing (re-run) | reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-J-02.png |
| J-03 The Playbook lands on /desk | passing | passing (re-run) | reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-J-03.png |
| J-04 The continuation family | passing | passing (re-run) | reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-J-04.png |
| J-05 The climax family | passing | passing (spot-checked by evaluator; new row-scoped assertion) | reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-J-05.png |
| J-06 The range family | passing (evidence_makeup) | passing — owed re-capture delivered, flag cleared; its own replay script now exists | reports/qa/goal-playbook-iter-8-evidence/audit-TC-14-range-trade-geometry-preseed-rig.png; .../fix-scoped-replay-J-06.png |
| J-07 The back-scan | passing | passing (re-run) | reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-J-07.png |
| J-08 The evidence view | failing | **passing** | reports/qa/goal-playbook-iter-8-evidence/UT-02-result.png (low-n cell beside full cell); .../fix-scoped-rig-J-08-evidence-cells.png (section + register); results rows UT-01/02/03/08/10 in reports/phase-goal-playbook-iter-8-ui-test-results.md |
| J-09 MCP contract v4 | failing | failing (not targeted; evaluator counted 18 tools directly) | evaluator ran `app.mcp.list_tools()` → 18 names, no `desk_playbook` / `desk_playbook_evidence` |
| J-10 The kept product stands | partial | partial (walk + replay green, but 18 tools ≠ the 20 its own acceptance names) | reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-J-10.png |

Note on the merged results file: `reports/phase-goal-playbook-iter-8-ui-test-results.md` was written
at 15:28, before the fix pass. Its J-05/J-06 rows say "substituted evidence; golden not re-verified"
because the first replay run (14:45) failed those two on a rig that had not been seeded. The fix pass
re-ran all eight goldens at 16:40 on the correctly seeded scoped rig — 8/8 PASS
(`reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-results.md`), independently repeated by
the auditor. I scored J-05 and J-06 from the post-fix pictures, which I opened.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `scan-report.md`: CLEAN. New files are one research module, four scripts, one env file of paths and commands — I read `project-extensions/store-scope/store-scope.env` in full; no key material. |
| Paid / external SaaS | OK | `git diff` on every `package.json` / `requirements*.txt` / `pyproject.toml` since the snapshot is empty. No new runtime dependency. |
| License changes | OK | No LICENSE or license-field change in the diff; scan-report reports no license findings. |
| Fabricated / substituted data | OK | Every number in the new table is a straight pass-through of the served JSON (UT-10 checked on-screen `n=14` against the raw endpoint). The browser lane swapped which symbols it looked at because it ran against the operator's real backend rather than the fixture copy — substituted *test subjects*, not substituted numbers. |
| No execution path / no profit claims / no advice | OK | `EVIDENCE_REGISTER` read live from the running module: descriptive only, states no fills and no costs are modelled and that it "describes measurements of what already happened and nothing about what happens next". Copy lint in the suite (46 tests) passes. |
| Frozen foundations / no fingerprint bump | OK | Zero diff since the snapshot for `desk_forward.py`, `desk_playbook.py`, `desk_playbook_detect.py`, `config.py`, `meta.py`, `app/engine`, `levels.py`, `setups.py`, `apps/frontend/components`. `Config().config_fingerprint()` → `08e471b10130e1e2`. |
| No lookahead | OK | No detector or measurement code changed; the new module only folds already-recorded values. |
| Single source of truth | OK | `coherence.md` verdict is **COHERENCE-PASS**; the new module imports the rail's helpers and reads records through `PlaybookStore.get`, never a second reader. |
| Deterministic and seeded | OK | Cache is stat-keyed and derived; cold-vs-warm byte-identity and cache-deleted rebuild are covered by TC-2 / TC-6 in the suite I re-ran. |
| Read-only MCP | OK | `app/mcp/__init__.py` zero diff; 18 read-only proxies, no writes added. |
| Immutable data | OK | No recorded file was rewritten or pruned; existing records keep their old timestamps. The evidence cache exposes only `lookup`/`insert`. |
| **Persistence stays scoped** | **VIOLATED (minor) — remedied inside the iteration** | At 14:45 the automatic replay lane pressed Run Backscan against the operator's real backend and permanently wrote three real records (2026-06-22/23/24) plus one run row. I verified all four files on disk. They are genuine, correctly ledgered, append-only output — nothing invented — so this is the same minor/process shape the iteration-6 precedent already settled. The fix pass then built the guard that closes the lane, and re-ran clean with all 9,841 protected files unchanged. |
| Persistence stays scoped — residual | **OPEN (minor)** | The guard is wired into the two goal-mode browser lanes only; the QA agent's own browser pass is still ungated (it ran against the real backend this iteration, read-only). A detected breach discloses but does not stop the run. The guard's prepare step is hardcoded to the playbook fixtures for the whole repository. |
| A signal is an observation, not a call | Found and fixed this iteration (minor) | The served disclosure claimed the random-chance column covered every signal; on the real corpus one cell has 90 signals against 32 anchors. The auditor rewrote the sentence to name the cap; I read the corrected sentence live. |
| No threshold outside the spec / no sweeps | OK | `docs/playbook-detector-spec.md` and `desk_playbook_detect.py` both have a zero diff since the snapshot. |
| The evidence pools one signature | OK | Coherence audit traced the partition; UT-08 shows two other signatures listed with 5 and 1 dates while the main cell holds n=14, unrelated. |
| No recorded file rewritten / no second rail | OK | Store untouched; `desk_forward.py` zero diff. |
| Enhancement loop stays in its box | OK | `docs/goal.md` has a zero diff since the snapshot. |
| Host-guard caps | OK | No change to the host-guard configuration in the diff. |
| Two owner rulings from iteration 6 | OPEN (unchanged) | Deliberately out of scope again; the spec file was not touched. |

## Next-Step Recommendation

Build **J-09 "MCP contract v4"** next: add the two read-only Claude tools for the playbook and its
evidence table so the tool count goes from 18 to 20, then close **J-10 "The kept product stands"** —
walk the whole product in a real browser with a picture of every shipped Desk section, the Cockpit
and the Structure page, and prove no kept page changed except the two allowed additions. This is the
last piece of the era, so run it as a deep iteration with the auditor; the auditor was again the only
reader who found real problems this time.

Carry four cheap items in the same cycle: make the store-scope guard also cover the QA agent's own
browser pass, and decide whether a detected write into the operator's store should stop the run
instead of only reporting it; stop the guard from forcing the playbook fixture data onto a future,
unrelated project run; and show the signature the evidence table is built from on screen, since the
page currently names every *other* signature but not that one. Two questions still wait for the
owner, unchanged since iteration 6: say yes or no to the one sentence a developer added to the rule
book about range trades, and settle the three places where the shipped code reads the rule book more
narrowly than it is written.

One thing to know for next time: the picture the QA write-up offers as proof of the new table
(`reports/qa/goal-playbook-iter-8-evidence/TC-08-playbook-evidence-table.png`) does not show the new
table at all — it shows the calendar and forward-returns part of the page. The real proof exists in
two other pictures, which I opened, so the journey is genuinely passing; but the QA write-up should
not be trusted on which picture shows what.
