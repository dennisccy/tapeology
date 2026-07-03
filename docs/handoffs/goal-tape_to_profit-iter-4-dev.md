# goal-tape_to_profit-iter-4 Dev Handoff

**Phase:** goal-tape_to_profit-iter-4
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## What Was Built

- **PnL-ledger store (Data Contract row 32):** new `pnl_ledger` table in the journal-scoped
  SQLite, payload-blob shape keyed by the ENHANCEMENT id (uniqueness structural — one honest row
  per enhancement). Added by the versioned on-open **v8→v9 migration** (`journal_schema_version`
  8→9), proven against the NEW committed old-schema fixture
  `tests/fixtures/journal_v8_schema.sql` (the exact v7→v8 precedent). **Append-only at the
  repository level** (the `verdict_events` standard): `JournalStore` exposes
  `append_pnl_ledger_row` / `get_pnl_ledger_row` / `list_pnl_ledger` and NO update/delete; a
  duplicate enhancement id raises the explicit `DuplicateEnhancementError` refusal; no
  UPDATE/DELETE SQL targets the table anywhere (source-scanned by a test).
- **Validation append path (`app/research/pnl_ledger.py` — row 32's ONE writer):**
  `append_validation_row` composes a row from two COMPLETED persisted backtest reports (one per
  frozen split), copying `net_r` / `net_usd` / `n` **verbatim** from the row-31 aggregates (never
  recomputing; equality asserted in tests). It validates report existence/terminal-status/shape,
  per-report split honesty (train report backs the train side only), and cross-report agreement
  on strategy/profile/`config_fingerprint` (never pool across fingerprints) — any failure is an
  explicit `LedgerCompositionError` with NOTHING appended. Founding rows store `baseline: null`
  explicitly (`founding: true`) — never fabricated zeros. `baseline` param exists for J-07's
  sweep (the second caller); today's only caller passes `None`.
- **Founding-baseline seeding CLI (`python -m app.research.pnl_baseline`):** keyless +
  deterministic. Obtains the fixture train/hold-out datasets through the real
  `record_from_source` reference path sliced to the NEW config-owned founding windows
  (content-identical to the committed fixture pair — checksum equality asserted); reuses an
  already-registered dataset (409 refusal carries the id); refuses a frozen-split conflict. Runs
  one backtest per split via the EXISTING `BacktestJobManager.create` + `run_sync` (zero runner
  changes), appends the row via the one writer. **Idempotent:** re-run prints the explicit
  "already present" no-op and exits 0 (no datasets recorded, no backtests run, ledger
  byte-identical — tested).
- **`GET /research/pnl/ledger`** on the existing research router — exactly ONE new route, GET
  only. Serves stored rows verbatim (insertion order) through the ONE `ledger_projection` read,
  wrapped with the existing `REGISTER` constant (imported, never a second copy) and the NEW
  config-owned `pnl_min_sample_size`: each split carries an `insufficient_sample` bool marker
  with `n` still present (the `analytics_min_sample_size` presentation-only precedent). Empty
  ledger → honest 200 empty list; non-GET verbs → FastAPI default 405 (no write handler exists).
- **`reports/pnl/pnl-history.md`** — pure render via the SAME `ledger_projection` read, written
  by `python -m app.research.pnl_history` to the config-owned path. Byte-level no-op on unchanged
  rows (render-twice test + verified live via identical md5 across regenerations); dd-MM-yyyy
  dates from the stored UTC timestamp; register verbatim; every $ beside its R and its n; train
  and hold-out separate rows (never pooled); explicit founding "no prior incumbent" prose;
  explicit empty state. **Committed** with the founding row rendered.
- **Config (no magic numbers):** `pnl_min_sample_size` (labeling-only → EXCLUDED from
  `config_fingerprint` with the documented analytics precedent + pinning tests),
  `pnl_history_md_path` (operational path → EXCLUDED, `dataset_dir` discipline),
  `pnl_founding_enhancement_id` / `pnl_founding_enhancement_title` / the two founding windows
  (row-shaping, DELIBERATELY NOT excluded — counter-test pins that they move the fingerprint).
- **MCP:** `app/mcp/__init__.py` diff is exactly the two stale documentation strings (module
  docstring honest-404 sentence + the `pnl_ledger` tool description) — zero
  proxy/transport/handler logic changes; the tool flipped from honest 404 to live data by
  construction. `tests/test_mcp_server.py`: `pnl_ledger` moved into live byte-identity coverage
  with a non-empty-200 test that seeds via the REAL CLI subprocess against the live test backend
  (the datasets/backtests pattern) and proves the idempotent re-run; the now-empty
  `NOT_YET_SHIPPED` dict and its vacuous premise loop retired (the one sanctioned removal); the
  stdio honest-404 wire-form leg now uses the allowlisted-but-missing `/research/profiles`.
- **Dev environment seeded:** the founding row is live in the dev journal DB
  (`apps/backend/tapeology_journal.db`, migrated v8→v9 on open) and
  `reports/pnl/pnl-history.md` is rendered from it.

## Files Changed

- `apps/backend/app/config.py` — `journal_schema_version` 9; PnL-ledger config block (min-n
  label threshold, founding id/title/windows, markdown path); fingerprint exclusions + commentary
- `apps/backend/app/research/store.py` — `pnl_ledger` table in schema; v8→v9 migration step;
  `PnlLedgerRecord`; `DuplicateEnhancementError`; append/get/list (append-only repository)
- `apps/backend/app/research/pnl_ledger.py` — NEW: row-32 writer, `ledger_projection` (the one
  serving read), markdown render/write
- `apps/backend/app/research/pnl_baseline.py` — NEW: founding-baseline seeding CLI
- `apps/backend/app/research/pnl_history.py` — NEW: markdown regeneration CLI
- `apps/backend/app/research/routes.py` — NEW `GET /research/pnl/ledger` route + one import
- `apps/backend/app/mcp/__init__.py` — the two stale documentation strings ONLY
- `apps/backend/tests/fixtures/journal_v8_schema.sql` — NEW committed v8 old-schema fixture
- `apps/backend/tests/test_journal_migration.py` — v8→v9 migration block (8 tests); two stale
  `== 8` version literals updated to the current-version assertion
- `apps/backend/tests/test_pnl_ledger.py` — NEW (21 tests): append-only surface + SQL scan,
  verbatim-copy equality, composition refusals, founding honesty, seeding determinism +
  idempotence, insufficient-sample both ways, markdown byte-no-op/format/empty-state, render
  purity scan, module source-scans, fingerprint pinning both ways
- `apps/backend/tests/test_pnl_ledger_api.py` — NEW (4 tests): 200 list shape, empty list, 405
  non-GET verbs, founding row served verbatim with cross-surface equality vs
  `GET /research/backtests/{id}`, REST-vs-markdown identical numbers + labels
- `apps/backend/tests/test_mcp_server.py` — `backend_paths` fixture split; pnl_ledger non-empty
  byte-identity + CLI idempotence test; NOT_YET_SHIPPED dict + vacuous loop retired; stdio 404
  leg → `/research/profiles`
- `reports/pnl/pnl-history.md` — NEW committed pure render carrying the founding row

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **983 passed, 1 skipped (984 collected)** — up from the iter-3 baseline of 952 collected
(951 passed / 1 skipped): +33 new tests, −1 sanctioned removal (the vacuous NOT_YET_SHIPPED
loop, replaced by the stronger live byte-identity test). Engine equivalence suite
(`tests/test_observer_equivalence.py`): **7/7 passed**. `test_no_execution_path.py` green over
the new modules. Frontend: `cd apps/frontend && npm run build` — **passes** (code unchanged).

## Pre-handoff Verification

- **Service startup:** `scripts/start-backend.sh` (port 8301) + `scripts/start-frontend.sh`
  (port 3301) both start clean; stop→start again verified with no port conflict; ledger row
  survives the restart (persisted, served verbatim). Both servers KILLED after verification.
- **Live (not mocked) machine-surface checks against the dev backend:**
  `GET /research/pnl/ledger` → **200** with the founding row (register verbatim, `baseline:
  null`, both splits `insufficient_sample: true` with n shown, full provenance) — the iter-0 404
  is flipped; `POST`/`DELETE` → **405**; MCP `pnl_ledger` tool response **byte-identical** to
  the REST body (1039 bytes) via a real `call_tool` against the live backend;
  `GET /meta/ui-routes` unchanged (3 nav links, no `/performance` — blueprint no-dead-link rule).
- **Founding-row honesty (measured, not fabricated):** train net_r −0.16 / net_usd −$16.00 /
  n=1; holdout net_r +0.3334 / net_usd +$33.34 / n=1 — the 60s/45s fixture windows arm exactly
  one trade per split, so BOTH splits are labeled "insufficient sample (n < 5)" with n shown.
  An honest small-n founding row is a good founding row (spec's founding-row framing).
  Dataset checksums in the row equal the committed fixture pair's checksums exactly.

## Known Issues

- The iter spec's NOTES recall "iter-3's fixture backtest produced net_r −1.239 on n=5" — the
  actual fixture-pair measurement is n=1 per split (one armed trade per 60s/45s window under the
  v1 sustain/cooldown rules; the −1.239/n=5 figure came from a different iter-3 substrate). The
  verbatim-copy tests assert equality against the persisted reports rather than any pinned n, and
  the insufficient-sample label covers the thin pool honestly. No action needed.
- `python -m app.research.pnl_baseline` / `pnl_history` resolve the journal DB via
  `TAPEOLOGY_JOURNAL_DB` or the cwd-relative default — run them from `apps/backend/` (as the
  backend does) or set the env var; documented in both module docstrings.
- Browser-visible evidence of the 404→200 flip (vs the iter-0 screenshot) is the browser-qa
  lane's leg (machine-surface journey — in-page `fetch()` from a backend-origin page, lessons
  iter-2): the dev DB is already seeded so the flip is immediately observable at
  `GET /research/pnl/ledger` on the QA backend port once services start. J-01/J-08 replay rows
  come from the stored golden scripts (untouched).

## Suggested Next Phase

J-05 — the `/performance` page: the first frontend iteration of the era. Add the fourth
top-level page rendering exactly this iteration's `GET /research/pnl/ledger` rows verbatim (R
beside $ beside n, register visible, train/hold-out separate, insufficient-sample labels), a
Performance entry in the nav rendered from `/meta/ui-routes` (adding `/performance` to the route
map), and the champion summary placeholder per the blueprint — in the existing dark cockpit
design language. All data it needs is now live.
