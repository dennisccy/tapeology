# Iteration 7 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-7
**Date:** 2026-08-18
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration's own diff is backend-only (8 files: 6 source + 2 test, 0 `.tsx`/`.ts`; confirmed
via `git diff f3f6691f --stat` and matching the ui-surface-map's claim). No endpoint (`routes.py` /
`micro_routes.py`) was touched, and every other registered owner
(`micro_readiness.py`/`micro_join.py`, `micro_snapshots.py`, `scout_ledger.py`/`scout.py`,
`vault.py`, `tick_recorder.py`, `micro_graduation.py`) is untouched — confirmed by
`git diff --stat` against each. "Data-contract additions: None" (iter spec) checks out: nothing new
is served or displayed.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Card-5.1 preservation fields (`conditions`/`exchange`/`tape`/`trade_id`/`bid_exchange`/`ask_exchange`) — new, storage-only | OK (not yet a contract value — genuinely new but nothing displays or serves it, so A4/A5's trigger condition ("a value the iteration displays") never fires) | `apps/backend/app/research/datasets.py:159-247` (`_event_to_row`/`_row_to_event`, present-only) — no route reads them |
| Dataset manifest `schema_basis`/`quote_size_unit` — new, storage-only | OK, same reasoning as above | `apps/backend/app/research/datasets.py:496-560` (`DatasetStore.record`) — no route reads them |
| Quote-size unit vocabulary (`micro_features.QUOTE_SIZE_UNITS`) | OK — datasets.py *imports* the existing tuple, does not redefine it | `apps/backend/app/research/datasets.py:63` (`from .micro_features import QUOTE_SIZE_UNITS`) vs. sole definition at `apps/backend/app/research/micro_features.py:100`; grep confirms one definition repo-wide; the iteration's own new AST-structural guard test (`test_tc9_no_second_quote_size_unit_vocabulary_or_early_dated_rule_constant_exists`, `apps/backend/tests/test_datasets.py:608-630`) makes this self-enforcing going forward |
| `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` (assumption-ledger-reserved constant) | OK — not defined this iteration | grep repo-wide: only referenced inside the guard test asserting its absence (`test_datasets.py:626,630`) |
| Fold specs / folds / walkforward ledger | OK — new `run_tick_family_fold_request()` is a new **caller**, not a new computation path: it reuses the existing `_tick_dataset_session_dates`, `register_fold_spec`, and `require_sufficient_sessions_for_folds` from the SAME canonical owner module/ledger, writing through the one existing write path `GET /research/desk/micro/walkforward` already serves | `apps/backend/app/research/walkforward.py:1005-1049` |
| Dataset content-checksum / split-freeze identity (existing invariant, not a new contract row) | OK — `_tape_identity_rows()` projects preservation keys out of the hashed payload so one tape keeps one identity regardless of which vendor identifiers happen to be preserved; verified byte-identical for legacy rows (no-op projection) and covered by a new regression test proving the re-tag guard still fires with preservation fields present on one side | `apps/backend/app/research/datasets.py:216-238` (`_tape_identity_rows`, `_content_checksum`); test: `apps/backend/tests/test_datasets.py` `test_the_frozen_split_guard_still_refuses_one_tape_re_fetched_with_preservation_fields` |

## Information Architecture check

No new page/route/feature this iteration (0 frontend files touched, 0 new endpoints). The new CLI
flag (`--family tick_legacy` on `python -m app.research.walkforward`) is an operator/CLI entry
point, not a UI surface, so Part B's nav-reachability rule does not apply to it — the iter spec
explicitly defers `POST /walkforward/compute`'s route-level family parameter (assumption ledger,
iter-7 second entry) until a UI/MCP consumer needs it, which is the honest, non-premature call.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new UI surface this iteration) | OK | `apps/frontend/app/desk/page.tsx` unchanged this iteration (confirmed via `git diff --stat`); ui-surface-map confirms `DeskCollapsibleSection` still lists exactly the same 10 sections, no new one added |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Forward-looking, not a defect: `run_tick_family_fold_request()` now writes a fold-spec row for
  `TICK_LEGACY_CORPUS_ID` into the same ledger `GET /research/desk/micro/walkforward` serves,
  alongside the existing playbook-corpus rows. When J-08 eventually builds the Walk-Forward `/desk`
  section, it should render/label fold specs by `corpus_id` so a future multi-corpus ledger reads
  unambiguously (which row is "playbook" vs. "tick_legacy") rather than assuming a single corpus.
  Nothing to fix now — no UI reads this ledger yet.
- The iteration's own audit caught and fixed a genuine identity-checksum risk (finding B1: Card-5.1
  fields would otherwise have entered the content checksum, letting a legacy tape be re-registered
  under a second split once the Alpaca adapter started populating them) before it could become a
  cross-page "the numbers don't match" bug in a future iteration. Correctly scoped inside this
  iteration's own diff — noted here for the record, not an open item.
