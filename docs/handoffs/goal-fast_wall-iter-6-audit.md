# goal-fast_wall-iter-6 Audit Report

**Date:** 2026-07-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-06 — the durable, restart-surviving, content-keyed `compute_setups` scan cache — is genuinely and
completely implemented. Every claim in the dev handoff was traced to source and independently
re-run: the three-tier lookup (hot slot → `SetupsScanCache` → `_run_full_panel_scan`) is correct,
the eight keyless test cases are non-vacuous (TC-6's mutation probe over a `_seed_full` store that
produces real events genuinely proves the durable-hit branch is read, not dead code), the two
source-introspection guards + the MCP 18-tool count + `config_fingerprint` `4d665603569b9dbf` all
pass byte-unmodified under my own run, and the diff is surgically scoped (only `setups.py` +
new `setups_scan_cache.py` as product code; every named out-of-scope file and the entire frontend
tree are zero-diff). No anti-goal is violated. The single open item is an OBSERVATION-level stale
comment the reviewer already flagged and deferred — no fix warranted.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no fix): "No compute on page load" was correctly NOT applied to the setups scan.**
I specifically checked whether `compute_setups` running its full-panel scan on `GET /research/setups`
(cold cache) violates the critical anti-goal "No compute on page load — operator-run only"
(`docs/goal.md:532-533`). It does not. That anti-goal is explicitly scoped to *"the backtest sweep"*
(J-04/J-05's edge-report PnL sweep), and J-06's own acceptance (`docs/goal.md:461-467`) frames the
setups scan as legitimately running on `/structure` page load — "a backend restart followed by
`/structure` no longer re-pays the multi-minute scan … within 10 seconds of navigation." Capability 6
(`docs/goal.md:200-205`) confirms the intended design: "the remaining cold cost is the O(n²) scan
math, paid once per (store, config) content ever instead of on every backend restart." The setups
scan is a different, lighter computation than the sweep and has always run on this GET since era-5B
iter-5's B3 memoization. No violation. Recorded here only because it is the single place a reader
could mistake this for a critical breach.

**B2 — OBSERVATION (no fix): durable DB accumulates one row per distinct key ever published.**
`compute_setups` publishes under `(config_content_hash, store_signature)`; a config or store change
mints a new key and leaves the old row in `setups_scan_cache.db` forever (no eviction/`reindex`). This
is the spec's own documented behavior (`setups.py:363-367`: "the DURABLE tier … can and does hold more
than one row, one per distinct key ever published") and matches the sibling caches. In a
one-store-per-process deployment the row count is bounded by the number of config revisions, which is
tiny. Not a defect; no bounded-growth requirement in scope.

### Frontend Findings

**F1 — none.** `git diff HEAD -- apps/frontend/` is empty (independently confirmed). `Frontend
Present: yes` existed only to force the UI-impact / UI-test / browser-QA / UX-regression lanes to
re-verify the unchanged `/structure` page — which they did (see Test Findings). Zero new frontend
code, exactly as the spec's "Frontend: None planned" section requires.

### Test Findings

**T1 — OBSERVATION (no fix; already flagged by reviewer): stale docstring aside at
`tests/test_setups.py:1027`.** The pre-existing `test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair`
docstring still says its isolation holds "per the module's own `id(config)` keying." That mechanism
was retired this iteration (the key is now a content hash), so a fresh default `Config()` no longer
self-isolates by identity — isolation now comes from the new `conftest.py` autouse
`_reset_scan_cache_for_tests()`. The test itself still passes and is genuinely isolated (verified: the
autouse fixture resets the hot slot before every test, and the durable tier is `tmp_path`-scoped). This
is pure comment staleness inside a test this iteration did not otherwise touch; the reviewer flagged it
MINOR and correctly deferred it. Fixing it would be scope creep per the audit rubric — documented, not
fixed.

---

## 3. Domain Assessment

The core domain logic is correct and honest.

**Three-tier lookup (`setups.py:419-459`).** Hot-slot hit returns immediately (`cached[0] == key`);
on a miss the durable `SetupsScanCache` is resolved from `store.root` and consulted; a durable hit
serves the persisted payload, a full miss runs `_run_full_panel_scan` once and publishes to the
durable tier before the hot slot. Both the durable-hit and full-miss paths funnel through the SAME
single `_SCAN_CACHE = (key, result)` rebind (line 458) — the guard test's exact requirement, which I
re-ran green. `cached` is read once into a local before inspection, preserving the era-5B iter-6
torn-read fix.

**Keying is genuinely content-based.** `_config_content_hash` (`edge_report_cache.py:150-156`) is
`sha256(canonical(dataclasses.asdict(config)))` — a pure function of every field's content with no
exclusion set, so two distinct-identity content-equal `Config` objects hash identically (TC-2) and a
`setups_*`-family change (excluded from `config_fingerprint()`) still busts the key (TC-3, which
explicitly asserts the fingerprint is unchanged first, then that the scan re-runs). `_store_signature`
contributes the sorted per-series `(symbol, timeframe, id, checksum)` tuples, so a new series busts the
key (TC-4). Collision across distinct inputs would require an sha256 collision or an identical
series-and-config set (which by definition yields the identical scan) — so there is no divergent-output
path.

**No divergent accelerator output.** The durable tier stores `json.dumps(result)` and returns
`json.loads(...)`. A JSON round-trip of the result dict (string keys, floats via `repr`, ints, `None`,
bools, nested lists/dicts) is faithful; TC-1/TC-5 assert `json.dumps(sort_keys=True)` equality across a
restart simulation and a DB deletion, and the standalone
`test_result_round_trips_byte_identically_through_json_persistence` covers floats/`None`/nesting
directly. `_run_full_panel_scan` remains the sole computer of a scan result; a miss always recomputes
byte-identically through it. The "Accelerators are never sources of truth" rail holds: deleting the DB
loses nothing (TC-5) and the mutation probe (TC-6) proves the cache is a genuine read path, not a
silent no-op.

**Failure handling is explicit and honest.** Every `SetupsScanCache` method guards `sqlite3.Error`:
`lookup` → `None` (a miss), `publish` → swallowed, `__init__` → swallowed and self-healing. TC-8 (unit)
and the API-level `test_corrupted_cache_db_never_blocks_get_setups` both prove a corrupted DB never
blocks serving; the browser leg's UT-05 additionally drove a real read-only cache dir end-to-end and
confirmed the publish was swallowed (`ro_cache/` stayed empty) with no error surfaced to the user.

**Ambiguous/empty data surfaced honestly.** On the mandated keyless fixture the scan resolves zero
events and Case Studies renders `case-studies-empty` "No band-touch events scanned yet." — the correct,
expected outcome, not a masked failure (the spec is emphatic that a populated-table demonstration is
the pytest suite's job, not the browser's). The browser QA confirmed this exact state.

---

## 4. Fixes Applied During This Audit

None. The implementation was already correct; all CRITICAL/IMPORTANT criteria were met on first
inspection. The two OBSERVATION items and one test-comment OBSERVATION do not warrant fixes (fixing
them is scope creep per the audit rubric; the docstring was already flagged and deferred by the
reviewer).

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied — nothing at CRITICAL/IMPORTANT severity found. |

**Independent verification performed during this audit:**
- `pytest tests/test_setups.py tests/test_setups_scan_cache.py tests/test_setups_api.py` → all passed
  (100%, no failures/errors).
- `pytest` on the two source-introspection guards, `test_advertised_tool_set_is_exactly_capability_6`,
  TC-1, TC-3, TC-6 → **6 passed**.
- `Config().config_fingerprint()` → **`4d665603569b9dbf`** (direct computation).
- `git status` / `git diff --stat HEAD` on all named out-of-scope files (`levels.py`,
  `tradability.py`, `backtests.py`, `bars.py`, `datasets.py`, `dataset_index.py`, `edge_report*.py`,
  `routes.py`, `config.py`, `app/mcp/__init__.py`, `apps/frontend/`) → **zero diff** confirmed.
- Traced `compute_setups` and `_run_full_panel_scan` source for the forbidden `"dataset"` substring →
  absent in both (guard passes for real).
- Read the browser-QA results (`reports/phase-goal-fast_wall-iter-6-ui-test-results.md`): real Chrome
  MCP run, 12/13 PASS + 1 documented SKIP, `loadingCount:0` after 10s, UT-05 broken-cache end-to-end
  proof.

---

## 5. Recommended Next Step

Proceed. J-06 is delivered cleanly and is the seventh and final Must-have journey of "The Fast Wall"
interlude; with J-01–J-05 and J-07 already `passing`, all seven Must-have journeys should now be
green. Whether that constitutes `GOAL_ACHIEVED` is the goal-evaluator's call (the auditor does not mark
journeys), but no product work remains for this iteration and no blocker stands in the way of that
determination.

Optional, non-blocking follow-ups for a future touch (do NOT reopen this iteration for them):
- Correct the stale `id(config)` aside in `tests/test_setups.py:1027` (T1) whenever that file is next
  edited for a substantive reason.
- The operator-only real-corpus "restart → `/structure` ready within 10s" figure remains
  operator-verified per goal.md's own tag — gather it as bonus evidence if/when a credentialed
  real-corpus run happens; it was correctly excluded from this iteration's Definition of Done.
