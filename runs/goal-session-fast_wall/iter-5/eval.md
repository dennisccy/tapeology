# Iteration 5 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-05 (the resumable + parallel sweep) is delivered and verified passing on strong, non-vacuous,
triangulated evidence, and J-04's browser gap is closed — it flips `partial → passing` on real,
personally-opened screenshots. Six of seven Must-have journeys now pass; only J-06 (the durable
setups scan cache, deliberately out of scope this iteration) remains. Scan CLEAN, coherence
COHERENCE-PASS, review PASS, full suite 1517/7/0, `config_fingerprint` frozen, all frozen-foundation
files git-confirmed zero-diff — no regression and no anti-goal violation, so the loop continues to J-06.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | `reports/qa/goal-fast_wall-iter-5-evidence/UT-01-not-computed-panel.png` (opened — not-computed panel + button); backend log shows 2 GETs before any POST (never computes) |
| J-02 | passing | passing | `bars.py`/`datasets.py`/`dataset_index.py` git zero-diff; suite 1517/7/0; supplementary `UT-05-top-tradable-case-studies.png` (live read path intact) |
| J-03 | passing | passing | `levels.py`/`tradability.py`/`backtests.py` git zero-diff; suite 1517/7/0 incl. source-introspection guards |
| J-04 | partial | **passing** | `UT-02-after-empty-state.png` (opened — click → terminal honest empty state, no button/no reload), `UT-06-failed-compute-error.png` (opened — verbatim `EdgeReportError` + "Retry compute"), `UT-04-reload-warm-result.png`; audit independently confirmed |
| J-05 | failing | **passing** | `reports/qa/goal-fast_wall-iter-5-qa.md` (TC-4..TC-14, suite 1517/7/0); non-vacuous tests read in `iter-diff.md` (kill-and-resume spy `backtests_from_cache==1`, key-busting matrix, distinct-PID parallel, delete-DB byte-identity); audit PASS_WITH_GAPS |
| J-06 | failing | failing | not built (explicitly OUT OF SCOPE); `EdgeReportBacktestCache`≠`setups_scan_cache.py` — module still absent; carried forward from iter-0 |
| J-07 | passing | passing | `J-07-studies.png` (opened — "Replay studies" + DONE study), `UT-05` (`/structure` sections intact); engine files zero-diff, fingerprint frozen; replay false-negative overturned by 9/9 manual golden re-run |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials committed | OK | `scan-report.md` CLEAN; no new config/env files in the 7-file product diff |
| Paid/external SaaS dependency | OK | scan CLEAN; `pyproject.toml`/`requirements.txt`/`package.json` git-confirmed unchanged; new code uses only stdlib `sqlite3`/`multiprocessing`/`concurrent.futures`/`hashlib`/`json`/`os`/`tempfile` |
| License changes | OK | scan CLEAN; no LICENSE/license-field diff |
| Fabricated/substituted data | OK | accelerators byte-identical (TC-4/9/13/8, `sort_keys=True` on a non-degenerate 3-cell shape); delete/corrupt-DB force full byte-identical recompute — cache never a source of truth |
| Rail 3 Frozen foundations | OK | `levels`/`tradability`/`backtests`/`bars`/`datasets`/`dataset_index`/`config`/`mcp/__init__`/`setups`/`edge_report_cache` + entire `apps/frontend/` git zero-diff vs working tree; `config_fingerprint()`=`4d665603569b9dbf` (recomputed); no new `Config` field (config.py 0 added lines) |
| Rail 6 Single source of truth | OK | coherence COHERENCE-PASS; sole pair computer stays `_run_backtest`; sub-cache injected only into the POST trigger, never a GET/wire surface |
| Rail 8 Read-only MCP / no MCP write surface | OK | `mcp/__init__.py` zero-diff; `test_advertised_tool_set_is_exactly_capability_6` = exactly 18 tools (re-run); compute trigger is REST/CLI only |
| No compute on page load — operator-run only | OK | GET `/research/edge-report` path zero-diff; backend log shows 2 GETs served before any POST; `multiprocessing`/`ProcessPoolExecutor` confined to `edge_report.py`'s CLI-only `_parallel_prewarm_sub_cache`, `routes.py` has none (no parallelism in a request thread) |
| No divergent accelerator output | OK | byte-identity equivalence tests (non-vacuous, 3-cell shape); parallel path only pre-warms then reassembles through the untouched sequential path — byte-identical by construction |
| Verification trust boundary never weakens | OK | J-02 store files zero-diff; UT-06 exercises the integrity-verification-on-every-read path (the corrupt-file error still fires) |
| No source-guard weakening | OK | `test_backtests.py:1500-1508`/`:932-943` + `test_setups.py:995-1017`/`:758-771` pass byte-unmodified (setups.py/backtests.py zero-diff) |
| No gate/register/vocabulary drift | OK | frozen "simulated — … — not indicative of live results" register + "No edge-report cells yet." rendered verbatim in UT-02/UT-05 screenshots; not-computed copy carries no prediction/advice phrasing |

## Next-Step Recommendation

Build **J-06** ("Restarts stop hurting — the durable setups scan cache", new `setups_scan_cache.py`)
— the LAST of this interlude's seven journeys, per goal.md's dependency order (rides on J-02's
durable-index precedent; independent of J-05). It replaces `setups.compute_setups`' fragile
`id(config)` cache leg with the config CONTENT hash (reused verbatim from `edge_report_cache.py`)
beside the store signature, checked hot-slot → durable → real scan. Depth **full**: J-06 modifies
the frozen-foundation `setups.py` under the critical "Frozen foundations" + "No source-guard
weakening" anti-goals (the `test_setups.py:995-1017` single-`_SCAN_CACHE`-rebind and `:758-771`
forbidden-"dataset"-substring guards must pass byte-unmodified), adds a new durable accelerator
needing byte-identity + zero-rescan-spy + tamper tests, and is `Frontend Present: yes` (a
browser-verifiable `/structure` leg). As the final journey, a clean J-06 makes GOAL_ACHIEVED
reachable, so the audit + coherence + ux-regression + closure lanes are the warranted backstop.

## Halt Justification (if halting)

N/A — not halting. Verdict is CONTINUE: two journeys advanced this iteration (J-04 `partial →
passing`, J-05 `failing → passing`), no journey regressed, no critical anti-goal was violated, and
coherence is COHERENCE-PASS. GOAL_ACHIEVED is withheld only because J-06 remains `failing` (not
built — out of scope this iteration); it is tractable keyless dev work, so this is not STALLED, and
the review passed with no fail-open, so this is not ESCALATE.
