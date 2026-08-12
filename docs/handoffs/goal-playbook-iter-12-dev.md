# goal-playbook-iter-12 Dev Handoff

**Phase:** goal-playbook-iter-12
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

## What Was Built

**J-11 — "Every evidence cell states the basis of its own n."** Seven new served fields on the
ALREADY-registered "Evidence aggregates" row (`app/research/desk_playbook_evidence.py`, same owner,
same endpoint `GET /research/desk/playbook/evidence`) — no new row, no new owner, no new endpoint,
no cache-schema change, no bar read, no re-measurement, no call into `desk_forward._measure_from`:

- `cells[].signal.n_unmeasured` / `cells[].signal.n_sessions`
- `cells[].baseline.n_truncated` / `cells[].baseline.n_unmeasured` / `cells[].baseline.n_sessions`
- `other_signatures[].n_records`
- a new payload-level `basis: {dates, n_records, created_span}` block for the pooled/default
  signature

**Backend (`desk_playbook_evidence.py`):**
- Two new helpers, `_measure_horizon_label(measure)` and `_n_unmeasured_by_label(events)`, count
  `return_pct is None` directly off each event's own `horizons[label]` leaf — per the phase spec's
  own NOTES caution, this is NOT a `len(events) - len(values) - n_truncated` subtraction (an MDD
  sibling's own value list could in principle be shorter than its return sibling's for a reason
  unrelated to unmeasurability). `_n_unmeasured_for(measure, ...)` shares ONE count per horizon
  label across a return key and its two `mdd_long_{label}`/`mdd_short_{label}` siblings, and reads
  `0` for the session-level trio (`to_close`/`mdd_long`/`mdd_short`), which is never unmeasurable.
- `_fold_cells` now also tracks, per `(setup_id, side)` pool (not per measure), the set of
  `session_date`s that contributed >= 1 raw signal/baseline event — `n_sessions` is computed ONCE
  per pool and applied identically to every one of that pool's 15 measure cells.
- `_signature_basis(projections)` is a NEW shared helper extracted from `_fold_other_signatures`'s
  own pre-existing dates/created-span logic (now also returning `n_records`), called once per
  `other_signatures[]` entry and once more over `default_projections` to build the payload-level
  `basis` block — one implementation, two call sites, never a second one.
- `EVIDENCE_REGISTER` extended (not replaced): the existing "the exclusion counted, never silently
  dropped" sentence now also names the unmeasurable class, the baseline's own
  `n_truncated`/`n_unmeasured`, `n_sessions`, and the new `basis` block. Verified clean of
  probability/expectancy/edge/significance/advice/prediction language (both `find_violations` and
  the file's own stricter literal-substring check).
- `desk_forward.py`, `desk_playbook.py`, `desk_playbook_detect.py`, `desk_playbook_features.py`,
  `PlaybookEvidenceCache`'s SQL schema, `_file_projection`'s shape, `config.py`,
  `app/mcp/__init__.py`, and `docs/playbook-detector-spec.md` all confirmed **zero diff**
  (`git diff --stat` empty for every one of them).
- `desk_routes.py`: docstring-only accuracy fix (the route's own comment enumerating the served
  keys now lists `basis`) — zero code/behavior change to the route itself, which already returns
  `fold_evidence(...)`'s plain `dict` verbatim with no `response_model`.

**Passenger 1 — `TAPEOLOGY_BAR_INDEX_DB` scoping gap (`desk_playbook_backscan.py`):**
`_SCOPING_ENV_VARS` extended from four to five entries; docstrings and the raised
`PlaybookNotScopedError` message updated from "four" to "five" accordingly. `_assert_scoped` stays
test/browser-QA-rig-only (confirmed by a new source-scan test: zero occurrences of `_assert_scoped`
in `desk_routes.py`). Every REAL scoped-rig launcher
(`qa_playbook_iter7_fixture_scoped_backend.sh` and its siblings) already exports
`TAPEOLOGY_BAR_INDEX_DB`, so this closes a gap between what those scripts already DO and what the
guard actually CHECKED — it does not require touching any launcher script.

**Passenger 2 — Playbook Signals date input amber border (`page.tsx` line ~5628):**
`ASOF_INPUT_CLASS`'s own `border-slate-700` and a plain, conditionally-appended `border-amber-500`
are an equal-CSS-specificity Tailwind collision (both single-class border-color utilities) — the
compiled stylesheet's own utility order silently decides the tie regardless of the JSX class list's
order, and `border-slate-700` wins, leaving the input grey on an invalid value. Fixed by switching
`desk-playbook-date-input`'s own conditional class to Tailwind's `!` important modifier
(`"!border-amber-500"`), scoped to that ONE input's own `className` expression only.
`ASOF_INPUT_CLASS` itself and the other four call sites (Refresh Data From/To at lines ~4411/4427 —
the SAME collision, deliberately carried; Backscan/Deep-backfill From/To — never had the affordance)
are confirmed byte-unchanged in source by a dedicated test.

**Frontend UI (`page.tsx`, `types.ts`):**
- `types.ts`: `DeskPlaybookEvidenceCellStats` gains `n_unmeasured`/`n_sessions`;
  `DeskPlaybookEvidenceBaselineStats` gains `n_truncated`/`n_unmeasured`/`n_sessions`;
  `DeskPlaybookEvidenceOtherSignature` gains `n_records`; new `DeskPlaybookEvidenceBasis` interface;
  `DeskPlaybookEvidence` gains `basis: DeskPlaybookEvidenceBasis`.
- New `PlaybookEvidenceBasisLine` component (own `basis` prop, matching the `plan.*`/`compute.*`/
  `outcomes.*` top-level-binding naming convention the price-arithmetic guard already uses), rendered
  as a new `data-testid="desk-evidence-basis"` line immediately beside the existing "Built from
  signature:" line — that line's own text is byte-unchanged (confirmed: `J-09.json`'s golden script
  matches it by substring).
- `PlaybookEvidenceCellRow`/`PlaybookEvidenceCellsTable`: five new `<td>`s (each with its own new
  `data-testid`) and two new header columns for the signal side / three for the baseline side. The
  existing `desk-evidence-cell-row`/`desk-evidence-signal-n`/`desk-evidence-baseline-n`/
  `desk-evidence-below-min-n` testids and their surrounding structure are unchanged (confirmed:
  `J-08.json`'s golden script's two `:has-text(...)`/`:has(...)` CSS selectors still resolve against
  the new markup, since they check row CONTENTS, not column position). Table `min-w` widened from
  900px to 1180px to accommodate the five new columns.
- No client-side arithmetic anywhere: every new field is a straight pass-through of the fetched
  JSON. `lib/api.ts`'s `fetchDeskPlaybookEvidence` needed zero changes (pure pass-through fetch).

## Files Changed

- `apps/backend/app/research/desk_playbook_evidence.py` -- the seven new fields, `_signature_basis`,
  `_n_unmeasured_by_label`/`_measure_horizon_label`/`_n_unmeasured_for`, `EVIDENCE_REGISTER` update
- `apps/backend/app/research/desk_playbook_backscan.py` -- `_SCOPING_ENV_VARS` five vars
- `apps/backend/app/research/desk_routes.py` -- docstring-only accuracy fix (lists `basis`)
- `apps/backend/tests/test_desk_playbook_evidence.py` -- 8 new test functions (this iteration's own
  TC-1..TC-6, TC-8, TC-9 numbering), the empty-store test extended (TC-7), the route empty-body test
  extended, the copy-discipline test extended (TC-11), a new `_unmeasurable_at_1h_forward` fixture
  helper
- `apps/backend/tests/test_desk_playbook_backscan.py` -- the three existing TC-13 tests widened to
  five vars, plus two new tests (TC-15: the fifth-var-alone negative counter-test, and the
  no-caller-under-desk_routes source-scan)
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended (the five new
  `cell.signal.*`/`cell.baseline.*` fields plus `basis.n_records`) with its own counter-test; three
  new tests for the TC-14 amber-border fix (positive + seeded-violation + a counter-test for the new
  extraction helper itself)
- `apps/backend/tests/test_mcp_server.py` -- the two `desk_playbook_evidence` byte-identical-proxy
  tests' hardcoded expected-key sets extended to include `basis`
- `apps/frontend/lib/types.ts` -- the five new stats fields, `n_records`, `DeskPlaybookEvidenceBasis`
- `apps/frontend/app/desk/page.tsx` -- `PlaybookEvidenceBasisLine`, five new cell columns, the
  scoped amber-border fix

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest -p no:warnings`
Result: **2182 passed, 8 skipped, 0 failed, exit 0** (up from the iter-11 floor of 2168 passed / 8
skipped -- 14 net-new tests, all accounted for: 8 in `test_desk_playbook_evidence.py`, 2 in
`test_desk_playbook_backscan.py`, 4 in `test_desk_ui_guards.py`, 0 net-new in `test_mcp_server.py`
(two existing tests' assertions widened in place)). Skip count unchanged at 8. (Counted directly
from the progress markers -- this environment's pytest summary line does not land in the redirected
non-tty log, the iter-10 handoff's own established counting method.)

`Config().config_fingerprint()` -> `08e471b10130e1e2`, unchanged.

`app.mcp.list_tools()` -> exactly 20 tools (confirmed by direct call, not just the suite), including
`desk_playbook_evidence`; both of its byte-identical-proxy tests (empty-state and populated-state)
pass against the enriched body after their hardcoded expected-key sets were widened to include
`basis`.

`git diff --stat` confirmed EMPTY (zero lines) for every file this iteration must not touch:
`desk_forward.py`, `desk_playbook.py`, `desk_playbook_detect.py`, `desk_playbook_features.py`,
`PlaybookEvidenceCache`'s SQL schema / `_file_projection`'s shape (both inside
`desk_playbook_evidence.py`, verified by reading the diff directly -- neither changed), `config.py`,
`app/mcp/__init__.py`, `docs/playbook-detector-spec.md`.

Frontend: `npx tsc --noEmit` -> zero errors, exit 0.

**Every previously-recorded playbook JSON file's SHA-256 is unchanged.** Hashed all 10 files under
`apps/backend/.data/playbook/*.json` before this dev pass began and again at the end (`sha256sum
*.json | sort`); `diff` between the two listings is empty. `find apps/backend/.data -newermt "-2
hours" -type f` also returned zero files -- nothing under the operator's real store was touched at
any point (no compute/backscan/Run Playbook/Run Screen was ever triggered; every test uses an
isolated `tmp_path` store, and the only live requests against the real backend below are read-only
GETs).

## Live verification against the REAL corpus (dev-level, read-only)

Started the operator's real backend/frontend (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301
nohup bash scripts/dev.sh &`, confirmed NOT the scoped fixture rig -- the served `basis.dates`
lists exactly the four real dates the phase spec's own Background section cites:
`["2026-06-22", "2026-06-23", "2026-06-24", "2026-08-07"]`, `n_records: 4`). Both healthy: `GET
/health` on `:8301` -> 200; `GET /` and `GET /desk` on `:3301` -> 200, no error banner.

`GET /research/desk/playbook/evidence` against the REAL store reproduces the phase spec's own two
cited real-corpus numbers EXACTLY:

- `double_top:short` at `1m`: `n: 31, n_truncated: 0, n_unmeasured: 59` (`31 + 0 + 59 == 90`,
  matching the spec's "59 of its 90 signals were never measurable there" verbatim).
- `capitulation:long` at `4h`: `n: 25, n_truncated: 4` beside `n_baseline: 8`, matching the spec's
  own cited numbers verbatim.

Not run by this agent (explicitly the browser-qa-agent's own pipeline stage per this session's
established division of labor -- see iter-10's dev handoff for the same precedent): a real Chrome
screenshot of the basis line / `n_unmeasured > 0` cell after a T-9 clean rebuild (TC-12), and the
deterministic replay of J-01/J-02/J-03/J-07/J-08/J-09/J-10. This handoff's live REST verification
above (byte-exact match against the spec's own cited real-corpus numbers) is offered as a strong
head start, not a substitute -- no screenshot exists yet, so J-11's browser acceptance line is
`unknown`, never `passing`, until that pass runs.

I directly inspected (not just re-derived) both `J-08.json` and `J-09.json`, the two existing golden
scripts touching this section: `J-09.json` asserts only the literal text `"Built from signature:"`
(untouched, byte-identical in source); `J-08.json` asserts two `[data-testid="desk-evidence-cell-row"]
:has-text(...)` / `:has(...)` CSS selectors that check row CONTENTS, not column position or count --
both still resolve against the widened row (five new sibling `<td>`s, nothing removed or renamed).

## Known Issues

- **No browser screenshot in this handoff.** Per "Live verification" above -- by this session's own
  established division of labor, deferred to browser-qa-agent, not an oversight.
- **Demo-narrator walkthrough not run by this agent.** TC-17's own `[NEW]`-flagged,
  `verified: true`-only-if-actually-rendered walkthrough of the enriched Evidence section is that
  agent's own pipeline stage.
- **`n_records == len(dates)` is always true for a fixed signature** (the store's own 2-pin key
  discipline: at most one record per `(session_date, signature)` pair), so the two served numbers
  are mathematically redundant -- served as separate fields anyway per the Data-contract addition's
  own explicit shape, so a reader is never asked to derive one from the other.

## Environment

**State at handoff: real backend (`:8301`) and real frontend (`:3301`) both healthy, matching the
dispatch note's "leave both servers healthy when you finish" instruction** -- left running
deliberately (NOT killed), per this session's own established iter-10 precedent, since the next
pipeline stage (browser-qa-agent) needs them alive. Both were DOWN when this dev pass began (neither
port answered); started fresh via `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash
scripts/dev.sh`. Chrome CDP `:9222` was left untouched (the pre-existing isolated headless
instance). The operator's real `apps/backend/.data/` store was never written to by this session --
verified by SHA-256 diff on every playbook record file and by a store-wide 2-hour mtime sweep, both
empty.

To stand the scoped rig up for the browser-qa-agent's own pass (the framework's own store-scope
guard normally does this automatically before a browser lane runs; documented here only for a
manual repeat of this session's own verification):

```bash
bash apps/backend/scripts/start_scoped_qa_backend.sh   # swaps :8301 to the scoped fixture rig
# ... browser/replay work ...
CHAIN_BACKEND_PORT=8301 bash scripts/start-backend.sh   # restore the operator's real backend after
```
