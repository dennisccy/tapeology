# Iteration 1 — Coherence Audit

**Iteration:** goal-desk-iter-1
**Date:** 2026-07-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Backend-only (`Frontend Present: no`). Full production diff against snapshot
`def522b4278cf65ff38490460d71711eb1f63db2`:

- Modified (tracked): `apps/backend/app/config.py` (+4 Path-A `desk_universe_*` Config fields +
  exclusion-set entries), `apps/backend/app/main.py` (mounts new `desk_router`),
  `apps/backend/pyproject.toml` (doc-only: broadened the `integration` marker's description text
  to name Wikipedia alongside Alpaca — no behavioral change).
- New (untracked, production): `apps/backend/app/research/desk_universe.py` (vendor seam + stdlib
  parser + `UniverseStore`), `apps/backend/app/research/desk_routes.py` (`POST
  /research/desk/universe/fetch`, `GET /research/desk/universe`).
- New (untracked, tests/fixtures): `tests/test_desk_universe.py`, `tests/test_desk_universe_api.py`,
  `tests/test_desk_universe_live_integration.py`, `tests/fixtures/universe/*`.
- Zero frontend files touched (confirmed: `git diff ... --stat -- apps/frontend/` is empty).
- `apps/backend/app/meta.py` diff is empty — `UI_ROUTES` stays exactly the 2 pre-existing rows
  (`Cockpit`, `Structure`); no Desk nav row this iteration (correct — that is J-04's job).
- `bar_index.py`, `tradability.py`, `levels.py`, `routes.py`, `datasets.py` all zero-diff.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Universe snapshots + membership | OK | Computed by `apps/backend/app/research/desk_universe.py` (fetch: `:147` `fetch_constituents_html`; parse: `:249` `parse_constituents`; store: `:312` `UniverseStore`). Served by `GET /research/desk/universe` (`apps/backend/app/research/desk_routes.py:95-103`) and `POST /research/desk/universe/fetch` (`desk_routes.py:53-92`) — exact module name and exact endpoint paths match `blueprint.md`'s "New rows this era" table row 1 verbatim. |
| All other registered rows (bars/candles, levels/zones, tradability, datasets, setups, edge report, pnl ledger, strategies, profiles, taxonomy, `UI_ROUTES`, `config_fingerprint`) | OK — untouched | Confirmed zero diff on their owning modules (`bar_index.py`, `tradability.py`, `levels.py`, `routes.py`, `datasets.py`, `meta.py`); `config_fingerprint()` gains only an additive exclusion-set entry (`config.py:1551-1568`), the function body/logic is otherwise unchanged. |

Checks performed beyond the diff itself:

- **T-3 store-separation guard held structurally**: grepped `desk_universe.py` and `desk_routes.py`
  for any import of `research/datasets.py` or `DatasetStore` — zero hits (the only match was the
  guard's own docstring describing the discipline, `desk_universe.py:28`).
- **No pre-existing duplicate concept**: grepped the whole backend + frontend tree for
  `universe`/`wikipedia`/`constituents`/`sp100` outside the two new files. The only pre-existing
  `universe` hits are `_ASSET_UNIVERSE` / `warm_symbol_universe` in
  `apps/backend/app/providers/adapters/{alpaca,yahoo,base}.py` and `main.py:134-167` — a
  long-standing, unrelated concept (the vendor's tradable-symbol *search-box autocomplete* cache),
  untouched by this diff, living in a different module family, serving a different purpose (search
  candidates, not S&P-100 index membership). Not a Data Contract collision — different registered
  entity, no shared endpoint, no shared computation. Noted below as a naming-proximity FYI only.
- **No new unregistered value**: the sole new displayed/servable concept this iteration (universe
  snapshot metadata + membership) was already pre-registered in `blueprint.md`'s Data Contract
  before this iteration ran (per the iter spec's own "Data-contract additions" field: "None
  requiring a blueprint edit"). Confirmed the shipped shape (checksum, member count, normalized +
  raw ticker forms, embedded Path-A provenance) matches that pre-registration.
- **"Membership is never a signal"**: confirmed structurally — `desk_universe.py` contains no
  ranking, scoring, or feature computation; `UniverseStore.record`/`.list` only carry membership
  data through unchanged.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new page/route/feature shipped in the UI this iteration)* | OK / N/A | `apps/backend/app/meta.py` diff against the snapshot SHA is empty; `UI_ROUTES` (`meta.py:27-30`) still lists exactly `/` (Cockpit) and `/structure` (Structure). `git diff ... --stat -- apps/frontend/` is empty — zero frontend files changed. |

The two new REST endpoints (`POST /research/desk/universe/fetch`, `GET /research/desk/universe`)
are backend/operator/MCP-callable only this iteration, which is exactly what `blueprint.md`'s
Feature/journey-homes table already specifies for this journey: *"J-01 Universe ingestion ... —
surfaced as the provenance line + universe metadata on `/desk` — no standalone page"* (Desk
section). There is no UI surface to check reachability for, so the "no navigation path" /
"undiscoverable" / "duplicate home" / "parallel shell" rules do not apply — none of them can fire
against a REST-only change with a pre-planned no-page-yet home. This matches the iteration spec's
own "Blueprint conformance" field ("No new page ships this iteration... no nav-skeleton change") and
"UI surface changes: None."

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Naming proximity, not a coherence violation.** The new `desk_universe.py`/`UniverseStore`
  ("S&P 100 index membership snapshot") and the pre-existing, unrelated
  `_ASSET_UNIVERSE`/`warm_symbol_universe` in `providers/adapters/{alpaca,yahoo,base}.py`
  ("vendor tradable-symbol search-box cache") both use the English word "universe" for genuinely
  different concepts. They do not share an endpoint, a computation, or a Data Contract row, and
  `desk_universe.py`'s module docstring already scopes itself precisely, so this is unlikely to
  cause real confusion — flagged only for awareness if a later iteration ever needs to grep for
  "universe" in this codebase.
