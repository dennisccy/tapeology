# Iteration 2 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-2
**Date:** 2026-07-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Backend + MCP only (`Frontend Present: no`). Delivers the pre-registered Data Contract row "Touch
events + reaction labels (`rejected`/`broke`/`chopped`) + forward returns + case registry" via its
designated owner `app/research/setups.py` and its designated endpoints `GET /research/setups`,
`GET /research/setups/{id}`, plus the read-only MCP `setups` proxy. No UI surface changes (confirmed
by `reports/phase-goal-tradable_wall-iter-2-ui-surface-map.md`: "N/A — Backend-only phase"). Diffed
tracked files: `README.md`, `apps/backend/app/config.py`, `apps/backend/app/mcp/__init__.py`,
`apps/backend/app/research/routes.py`, `apps/backend/tests/test_mcp_server.py`; new untracked files:
`apps/backend/app/research/setups.py`, `apps/backend/scripts/populate_panel_bars.py`,
`apps/backend/tests/test_setups.py`, `apps/backend/tests/test_setups_api.py`, a committed fixture,
and the iter spec itself.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Touch events / reaction labels / forward returns / case registry | OK | Sole owner `apps/backend/app/research/setups.py:256` (`compute_setups`); served verbatim by `apps/backend/app/research/routes.py:217` (`list_setups`) and `:232` (`get_setup`) — both call `compute_setups(store, CONFIG)["events"]` and only filter/lookup, never recompute a field. |
| Tradable level map / bands (read by setups.py) | OK — read verbatim, not recomputed | `apps/backend/app/research/setups.py:270` calls `compute_tradability(store, symbol, as_of_epoch, config)` per session and reads `tradability["bands"]` directly; no pivot/zone/level detection logic exists in `setups.py`. Confirmed by the diff's own new static-analysis test `apps/backend/tests/test_setups.py:430` (`test_setups_module_reuses_compute_tradability_verbatim_never_a_second_map_engine`), which asserts `setups.py` never calls `compute_levels(` and imports nothing from `levels.py`. |
| `setups` MCP proxy | OK — genuine HTTP proxy, no second computation | `apps/backend/app/mcp/__init__.py:131` adds `"setups": "/research/setups"` to `_STATIC_PATHS`; dispatch goes through the existing `_proxy_get` (`mcp/__init__.py:377`), a real `httpx` GET against the running backend — the identical mechanism every other MCP tool (`bars`, `levels`, `tradability`) already uses. No per-tool reimplementation. |
| Bar series (consumed by the new `populate_panel_bars.py` script) | OK — uses the canonical write path | `apps/backend/scripts/populate_panel_bars.py:78-87` drives the **existing** `POST /research/bars` route via `TestClient(app)`, not a new fetch/write path or a direct `BarStore.record()` call. Store-first coordination and `BarIndex` update happen through the one existing route. |
| `config_fingerprint` (must stay `4d665603569b9dbf`) | OK | The 5 new `setups_*` constants (`apps/backend/app/config.py:41-79`) are added to the fingerprint **exclusion set** (`config.py:99-103`), mirroring the `tradability_*` precedent exactly — no fingerprinted field touched. |
| Frozen foundations (`levels.py`, `tradability.py`, `backtests.py`, tape engine, `BarStore`) | OK — absent from the diff | Tracked-file diff is exactly `README.md`, `config.py`, `mcp/__init__.py`, `research/routes.py`, `tests/test_mcp_server.py`; none of `levels.py` / `tradability.py` / `backtests.py` / the tape engine / `bars.py` appear. |

No new displayed value is introduced outside the Data Contract — the iteration spec's own
"Data-contract additions: None" is accurate; this iteration *realizes* an already-registered row
rather than adding an unregistered one. The pre-existing, unrelated "setup" vocabulary in
`studies.py`/`taxonomy.py`/`hints.py`/`store.py` (tape-arming occurrences: `level_break`,
`absorption_reversal`, etc.) is a different, pre-existing concept explicitly disambiguated in
`setups.py`'s own module docstring (lines 14-22) — not a duplicate of the new value, confirmed by
grep showing no cross-references between the two vocabularies' code.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no UI surface shipped this iteration) | OK | `reports/phase-goal-tradable_wall-iter-2-ui-surface-map.md` confirms backend-only; no frontend files appear in `git status` or the tracked/untracked diff. Nav stays frozen per blueprint (no top-level entry added), consistent with the blueprint's IA table listing J-02's canonical home as `/structure` → Case Studies, explicitly deferred to J-05 (out of scope this iteration, per the iter spec's own "OUT OF SCOPE" list). |

No new page/route was introduced this iteration, so there is nothing to check for nav reachability,
duplicate homes, or a parallel shell. This mirrors the precedent set by iter-1 (J-01 tradability),
which also shipped backend/MCP-only with its browser page deferred.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The `README.md` diff in this window documents J-01's `GET /research/tradability` endpoint and adds
  a "Tradable level map" capabilities bullet, but does not yet mention `GET /research/setups` or the
  case-study registry (J-02's actual deliverable this iteration). This reads as the readme-maintainer
  showcase step catching up on J-01 (which apparently hadn't landed its README update before this
  diff's snapshot boundary — iter-1's own `iteration-summary.md`/`summary.html` are also being
  modified in the excluded-paths stat, confirming lagged showcase-artifact commits), not something
  iter-2's dev work skipped. Not a Data Contract or IA violation — README prose isn't a served value
  or a nav surface. Expect the next readme-maintainer pass to add the `/research/setups` bullet;
  no action needed from the decomposer.
