# Iteration 6 — Coherence Audit

**Iteration:** goal-hypothesis-foundry-iter-6
**Date:** 2026-08-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-FAIL

---

## Scope reviewed

Both the four committed commits on `goal/hypothesis-foundry` (`1573f457`..`873b4ed7`, snapshot
`ead194e6`..`HEAD`) and the later uncommitted working-tree edits (FIX pass + this iteration's own
hard-auditor pass: `qa_playbook_iter7_fixture_scoped_backend.sh`, `test_foundry_real_epoch_artifacts.py`,
`test_run_hypothesis_foundry_real_exhaust.py`, `reports/qa-scoped-backend-store-manifest.md`). The
uncommitted changes are test-only strengthenings (new guard tests for B1/TC-7/TC-4) plus a QA-rig
provisioning addition that mirrors the already-established `cp`-guarded pattern — none of them alter
the Data Contract or IA finding below.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `exhaust_progress.first_read_lock_recorded` / `.first_read_lock_at` / `.eligible_corpus_manifest_hash` | OK | `apps/backend/app/research/foundry_runner.py:229-283` (`read_exhaust_progress`), served via `apps/backend/app/research/micro_routes.py:938-941` — single canonical path, read verbatim by `apps/frontend/app/desk/page.tsx:7826-7901` (`RunnerCheckpointSubsection`), no client-side computation |
| `exhaust_progress.terminal_count` / `.checkpoint_ordinal` | OK (advisory — see notes) | `foundry_runner.py:266` computes `len([r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL])`; `run_hypothesis_foundry_real_exhaust.py:260` computes the byte-identical formula for its own console report only — same logic, same field, cannot diverge, so not a FAIL, but flagged below |
| **`exhaust_progress.frozen_ready_total`** | **DUPLICATE-COMPUTATION** | `apps/backend/app/research/micro_routes.py:901` vs `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225` — see Blocking violation 1 |
| `exhaust_progress.protected_read_count` | OK | Hardcoded `0` in both `read_exhaust_progress` branches (`foundry_runner.py:250, 262`); this is one asserted structural fact reused by the single serving path, not an independent computation |
| `exhaust_progress.single_flight_status` | OK | `foundry_runner.py:246-254`, a live probe against `EXHAUST_LOCK_FILENAME`; `run_hypothesis_foundry_real_exhaust.py:91` imports the SAME constant (`LOCK_FILENAME = fr.EXHAUST_LOCK_FILENAME`) rather than redefining it |
| `exhaust_progress.freeze_integrity_verdict` | OK | Derived once in `foundry_runner.py:267,281` from the presence of the epoch-open row (a historical fact, not re-verified per request, matching the router's GET-never-computes convention); frontend renders verbatim (`page.tsx:7852-7857`) |
| `exhaust_progress.exhaust_complete` | OK (downstream of the FAIL above) | `foundry_runner.py:274`: `terminal_count >= frozen_ready_total` — correct formula, but consumes the duplicated `frozen_ready_total` input; fixing that input closes this row too |
| `epoch_manifest`, `hermetic_oracles`, `freeze_integrity`, `interpreter_fixtures`, `sources_compiler`, `era`/`era_open_baseline` (rows 1-8, pre-existing) | OK, unchanged | `micro_routes.py:938-941` — every pre-existing key is untouched by this iteration's diff; `docs/hypothesis-foundry/{source-registry,epoch-manifest}.json` confirmed byte-identical (not in the file diff at all — only `freeze-set.json`/`freeze-record.json` changed, per spec) |

### Detail — Blocking violation 1

`exhaust_progress.frozen_ready_total` is registered in `state/blueprint.md`'s Data Contract (row
`exhaust_progress`, this iteration's own new row) as computed by `app/research/foundry_runner.py` +
`app/research/foundry_ledger.py`. Two independent implementations compute it this iteration:

- **Canonical / served path:** `apps/backend/app/research/micro_routes.py:901`
  ```python
  _FOUNDRY_FROZEN_READY_TOTAL = sum(f["variant_count"] for f in _EPOCH_MANIFEST_VIEW.get("families", []))
  ```
  passed into `foundry_runner.read_exhaust_progress(foundry_dir, frozen_ready_total=_FOUNDRY_FROZEN_READY_TOTAL)`
  at `micro_routes.py:941` — this is what `GET /research/desk/micro/foundry` actually serves and what
  `/desk` → Hypothesis Foundry → Runner / Checkpoint displays.

- **Duplicate:** `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225`
  ```python
  frozen_ready_total = sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))
  ```
  a brand-new script this iteration, reading the SAME `epoch-manifest.json` but keyed on a
  **different field** (`variants` list length vs. the route's `variant_count` field). This local
  value feeds the CLI's own `exhaust_complete` decision (`run_hypothesis_foundry_real_exhaust.py:274`)
  and its console report (`:297-301`) — a second, independent owner of the identical registered
  concept, living outside the registered `foundry_runner.py`/`foundry_ledger.py` modules.

Both currently evaluate to `0` because the frozen manifest's `families` list is `[]` (§8.1 pins this
epoch forever at zero candidates), so there is no live user-visible discrepancy today. That is exactly
the pattern this gate exists to catch before it compounds: two formulas reading two different fields
of the same file for "the same number," with no shared code path — a landmine for any future code
that copies this script forward. This iteration's own hard-auditor report independently found the
identical fact (`docs/handoffs/goal-hypothesis-foundry-iter-6-audit.md`, finding B6: "`frozen_ready_total`
has two independent derivations, keyed on two different manifest fields... a second owner for a shared
value (the 'single source of truth' anti-goal)"), rated there as a non-blocking OBSERVATION under that
report's own review rubric; under this gate's narrower, mechanical Data Contract rule it is an
objective duplicate-computation FAIL regardless of current numeric agreement.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` → Hypothesis Foundry → Runner / Checkpoint (new subsection, J-07) | OK | `apps/frontend/app/desk/page.tsx:8149-8158` — new `CollapsibleSection id="foundry-runner-checkpoint-section"` appended inside the already-registered `HypothesisFoundrySection` (blueprint IA home registered at baseline, "Runner / Checkpoint" row already listed as `[PLANNED, not yet built]" pending this iteration). No new route, no new nav entry, no parallel shell — reuses the exact `CollapsibleSection`/testid-family pattern the four iter-4 subsections already established. `apps/frontend/components/*Nav*` unchanged (confirmed no nav file appears in the diff) |
| No other new page/route this iteration | OK | `reports/phase-goal-hypothesis-foundry-iter-6-ui-surface-map.md` confirms 0 new pages/routes, 0 navigation changes |

No IA violation. The subsection is reachable via the same click path every prior Foundry subsection
already uses (Desk nav → expand Hypothesis Foundry → expand Runner/Checkpoint), an established,
previously-accepted pattern this iteration only extends, not a new decision.

## Blocking violations (FAIL only)

1. **Data Contract — duplicate computation of `exhaust_progress.frozen_ready_total`** — a second,
   independent implementation at `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225`
   computes the same registered value the canonical serving path already computes at
   `apps/backend/app/research/micro_routes.py:901`, keyed on a different manifest field
   (`variants` list length vs. `variant_count`).
   **Fix:** add one shared helper — e.g. `foundry_family.total_frozen_ready_variants(manifest: dict) -> int`
   (or a `foundry_runner.py` function alongside `read_exhaust_progress`) that sums `variant_count`
   per family, matching the currently-canonical `micro_routes.py:901` formula. Change
   `micro_routes.py:901` to call it, delete the independent
   `sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))` at
   `run_hypothesis_foundry_real_exhaust.py:225`, and have the CLI call the same helper instead. This
   is a small, finite, test-covered change (both existing call sites already have committed unit
   coverage over the zero-family manifest) and closes finding B6 from this iteration's own audit
   report for real, rather than leaving it as a disclosed-but-unfixed observation.

## Advisory notes (non-blocking)

- `exhaust_progress.terminal_count` / `checkpoint_ordinal` are computed by the byte-identical
  formula in two places (`foundry_runner.py:266` and `run_hypothesis_foundry_real_exhaust.py:260`,
  both `len([r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL])`). Because the
  formula and the field it reads are identical, this cannot diverge — not a FAIL — but it is the same
  "two owners" shape as the blocking finding above and should be folded into the same consolidation
  helper (e.g. `foundry_ledger.py` gaining a `terminal_count()` convenience method) when the fix for
  finding 1 lands, so `run_hypothesis_foundry_real_exhaust.py` stops reading ledger internals directly
  in two independent spots.
- `exhaust_progress.freeze_integrity_verdict`'s two-value contract in the blueprint/spec
  (`"green" | <typed halt code>`) does not name the real third state the code honestly emits,
  `"not_yet_verified"` (pre-lock). `apps/frontend/lib/types.ts:3183` already widens the field to
  `string` and documents this in a comment. Cosmetic contract-text drift only — the decomposer should
  update the Data-contract table's literal enum in the next iteration touching this row; not a
  coherence violation since there is exactly one owner and no fabrication involved.
- This iteration's own hard-auditor report (`docs/handoffs/goal-hypothesis-foundry-iter-6-audit.md`)
  independently surfaced two additional non-UI-facing gaps (B3: no chain-integrity re-verification on
  the read path; B5: the GET route now performs a filesystem write/lock-acquire on every page load)
  that sit outside this gate's Data Contract / IA charter — recorded here only for traceability, not
  adjudicated by this audit.
