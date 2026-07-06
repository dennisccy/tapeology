# Iteration 3 — Coherence Audit

**Iteration:** goal-tape_to_profit_support_resistence-iter-3
**Date:** 2026-07-06
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Support/resistance levels + A/B/C confluence classes (Data Contract row 39, both halves) | OK | Computed ONCE in the already-registered owner `apps/backend/app/research/levels.py` — new `compute_confluence_zones`/`_cluster_levels`/`_grade_zone`/`_confluence_zone`/`_zone_sort_key` (levels.py:162-244) are added inside this SAME module, not a new one; `compute_levels` (levels.py:247-296) folds the zones in as an additive `confluence_zones` key. Served verbatim by the existing single route `apps/backend/app/research/routes.py:1637-1655` (`return {"symbol": normalized_symbol, "as_of": as_of, **result}` — confirmed by direct read, no field is dropped/repicked) and the existing MCP `levels` tool (`apps/backend/app/mcp/__init__.py:190-199`, description text updated only, no handler change). Byte-identity between REST and MCP is asserted end-to-end by `apps/backend/tests/test_mcp_server.py:290-832` (`test_levels_tool_byte_identical_on_a_non_empty_live_result`, extended this iteration to require a non-empty `confluence_zones` in the compared body). Grepped the rest of the backend (`analytics.py`, `pnl_scan.py`, `edge_report.py`) and `apps/frontend/` for `confluence`/`cluster`/`CLASS_A` — zero hits outside `research/levels.py` and its own tests: no second computation path anywhere. |
| Confluence config inputs (`sr_confluence_band_bps`, `sr_confluence_class_a_min_timeframes`, `sr_confluence_class_b_min_timeframes`) | OK | Computation inputs, not displayed values, per row 39's own "every parameter config-sourced" note — correctly take no Data-Contract row. Declared with rationale at `apps/backend/app/config.py:1130,1139,1146`; added to the `config_fingerprint()` `excluded` list at `config.py:1366-1368`, same pattern/placement as the three pre-existing `sr_*` fields immediately above them (`config.py:1356-1358`) — preserves the pinned `default` fingerprint (`test_sr_config_fields_are_excluded_from_config_fingerprint` in `test_levels.py:688-703` asserts this directly). |
| New value not yet in the Data Contract | N/A | `confluence_zones` is not a new concept — Row 39 already named "A/B/C confluence classes" explicitly; this iteration ships the previously-deferred classes half of an already-registered row (the iter spec's own "Data-contract additions: None" is correct, matches the blueprint text verbatim). No A5 "unregistered value" note warranted. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/levels` `confluence_zones` field (J-03) | OK | Blueprint IA lists J-03's canonical home as "API `GET /research/levels` (same endpoint) + MCP `levels`" with Nav section "machine" (no nav home required). No new route, file, or MCP tool was added — `git diff <snapshot>..HEAD --diff-filter=A` shows zero new source files. `git diff <snapshot>..HEAD -- apps/frontend/` is empty, confirming the spec's "Frontend Present: no" / "apps/frontend/ MUST NOT change" constraint held. No nav/sidebar/router file exists to check reachability against because none was meant to change — consistent with the blueprint. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **README capability bullet undersells this iteration's actual shipped capability.** `README.md`'s `<!-- AUTO:capabilities -->` block gained its first-ever bullet for the levels endpoint this iteration — `"**Support/resistance level detection (research API)**..."` (README.md, `AUTO:capabilities` block, new bullet before the REST-API-routes bullet) — but its prose describes only the J-02 half (swing pivots, prior-period extremes, no-lookahead, byte-identical determinism, the two honest "nothing to show" states) and never mentions confluence zones, timeframe-weighted scoring, or the A/B/C conviction classes that are this exact iteration's (J-03's) entire deliverable on the same endpoint. (Confirmed via `git show <snapshot>:README.md` that no prior S/R-levels bullet existed before this iteration, so this is a fresh miss, not stale carry-over text.) Not a Data Contract or IA violation — there is one computation, one endpoint, and no nav change — so this does not block. Recommend the next README pass extend this bullet (or the adjacent "Machine-readable access for AI tools" bullet, which does now list "support/resistance levels" but likewise omits confluence/classes) to describe the confluence-zone/A-B-C-class shape so the doc matches the response the code and tests actually assert.
