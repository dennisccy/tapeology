# goal-playbook-iter-9 Dev Handoff

**Phase:** goal-playbook-iter-9
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

**J-09 — MCP contract v4 (18 → 20 read-only tools).** `desk_playbook` and `desk_playbook_evidence`
added to `app/mcp/__init__.py`'s `_STATIC_PATHS` (both no-required-param shapes, mirroring
`desk_forward`/`desk_screen`) plus matching `types.Tool` entries. `get_endpoint`'s existing
`/research/` allowlist already reaches the parameterized `?date=`/`?id=`/`?signature=` reads — zero
new route code. `tests/test_mcp_server.py`'s `EXPECTED_TOOLS` updated to the 20-tool contract, both
`len(TOOL_NAMES) == 18` assertions bumped to 20, and full byte-identity coverage added for both new
tools in EMPTY and POPULATED fixture states (`test_desk_playbook_tool_byte_identical_on_the_honest_
empty_state`, `..._on_a_populated_state`, `test_get_endpoint_desk_playbook_date_query_proxies_
verbatim` for TC-6, `test_desk_playbook_evidence_tool_byte_identical_on_the_honest_empty_state`,
`..._on_a_populated_state`) — the honest-error/dead-backend coverage
(`test_backend_down_every_tool_raises_an_explicit_error`) already iterates `EXPECTED_TOOLS`, so both
new tools are automatically covered with zero test-loop changes. Verified live against BOTH the
scoped fixture rig and the operator's real backend: `list_tools()` returns exactly 20 names,
`desk_playbook`/`desk_playbook_evidence` calls succeed non-error on the real store too.

**J-09 frontend — Playbook Evidence signature display.** `PlaybookEvidenceSection`
(`apps/frontend/app/desk/page.tsx`) now renders `data.signature` as a visible line ("Built from
signature: `<value>`") above the existing `data.register` disclosure paragraph
(`data-testid="desk-evidence-signature"`). No new API call, no new type field — `DeskPlaybookEvidence.
signature` was already served and already typed (`lib/types.ts:1789`); this iteration only renders it.
Verified live (screenshot) and via a fresh golden replay script.

**J-08 golden — `runs/goal-session-playbook/journey-scripts/J-08.json`.** Closes the "no stored
script exists yet" gap the iter-8 dev handoff flagged. Three steps: goto `/desk` → expect the static
"Playbook Evidence" panel title (never data-dependent, per the T-11 lesson); wait for
`desk-evidence-section` → expect a well-populated cell row (`open_high_break`/`long`/`to_close`,
scoped via chained `:has-text()` on `[data-testid="desk-evidence-cell-row"]` — legible n/median/p25/
p75/mean, `to_close` chosen because it is the ONE measure key with no substring collision against any
other measure name); wait for the section again → expect a genuinely tagged low-n row
(`open_high_break`/`long`/`1h`, additionally requiring `:has([data-testid="desk-evidence-below-min-n"])`
as a descendant so the check cannot pass on an untagged row). `--mode lint` clean; `--mode verify`
against the scoped rig — PASS. **Proven to discriminate, not just pass**: a deliberately
logic-impossible mutation of step 2's selector (requiring a row whose measure column contains both
`"to_close"` and `"1h"` — mutually exclusive) was run through the SAME verify path and FAILED (rc 5),
confirming the runner does not vacuously pass regardless of selector content.

### Store-scope guard hardening (all three items landed; none dropped)

1. **Abort-on-breach at both existing call sites.** `browser-qa-phase.sh` and `goal-iter-lean.sh`:
   a `store_scope_verify` BREACH now writes its disclosure artifact/telemetry FIRST (unchanged), then
   `exit 1`s the script — previously it disclosed and fell through unconditionally. In
   `goal-iter-lean.sh` the abort deliberately sits BEFORE the `step_mark_done browser-qa` checkpoint
   call, so a breached run is never checkpointed done (a later resume genuinely re-runs the lane
   rather than reusing a stamp over an untrustworthy result). `run-goal.sh` does not special-case this
   script's non-zero exit beyond the existing `DISPATCH_UNAVAILABLE_EXIT_CODE` (70) check, so the outer
   loop falls through to the coherence-auditor/evaluator as usual — they read the merged results file
   (which now carries the loud disclosure section) and score accordingly. `browser-qa-phase.sh`'s
   non-zero exit is caught by its own existing callers in `run-phase.sh` (`|| { ...; return $rc; }` in
   the parallel branch, a warning-and-continue in the sequential branch) — both already-supported
   failure paths, nothing new to wire.
2. **The `qa` agent's own direct browser-driving path is gated (audit B3).** `qa-phase.sh` now
   sources `lib/replay-lane.sh` and calls `store_scope_require` (gated on `FRONTEND_PRESENT == "yes"`)
   before dispatching the `qa` agent. A refusal downgrades `FRONTEND_PRESENT` to `"no"` honestly (the
   agent is told browser checks are SKIPPED with the reason, and to mark browser-dependent test cases
   SKIPPED) rather than blocking the whole `qa-phase.sh` dispatch — the non-browser functional QA
   checks still run. This closes the third ungated lane the iter-8 audit found (`qa-phase.sh`'s own
   Chrome MCP pass drove the operator's real backend during iter-8 itself, read-only that time).
3. **Fixture-forcing scoped to this project only (TC-17).** `project-extensions/store-scope/
   store-scope.env` now opens with a project-identity guard: it declares nothing (leaves
   `STORE_SCOPE_ENABLED` unset, so `store-scope.sh`'s own no-config no-op applies) unless the resolved
   project root's git remote names `tapeology`, or — when there is no remote at all —
   `apps/backend/app/research/desk_playbook.py` exists. `STORE_SCOPE_PROTECTED_PATHS`,
   `STORE_SCOPE_ASSERT_CMD`, and `STORE_SCOPE_PREPARE_CMD` are byte-unmodified (confirmed by `git
   diff` — the guard is a pure prepended block). Verified directly: sourcing the real file with
   `ROOT=<tapeology repo>` sets `STORE_SCOPE_ENABLED=1`; sourcing it with `ROOT=<a fresh dir with no
   git remote and no desk_playbook.py>` leaves it unset.

All three items landed inside budget — none needed the escape hatch.

### Tests added for the hardening (framework side)

`incredible_auto_dev/tests/automation/test-store-scope-guard.sh` grew three new sections (structural
source-scan + functional sandbox checks, the same style the existing suite already uses for these two
orchestration scripts, which dispatch a real `claude` CLI this suite cannot mock):
- §9: both callers' verify-BREACH branch now contains `exit 1`; in `goal-iter-lean.sh` that exit line
  precedes the real `step_mark_done browser-qa --dir` checkpoint call in file order.
- §10: `qa-phase.sh` sources `lib/replay-lane.sh`, calls `store_scope_require` gated on
  `FRONTEND_PRESENT`, and that gate runs before `record_agent_invocation_start qa`; a functional
  sandbox re-run of the gate's own logic confirms an unscoped backend flips `FRONTEND_PRESENT` to
  `"no"`.
- §11: tapeology's REAL `project-extensions/store-scope/store-scope.env` enables scope for its own
  project root and no-ops for a synthetic unrelated-project root.

## Files Changed

- `apps/backend/app/mcp/__init__.py` -- `desk_playbook`/`desk_playbook_evidence` added to
  `_STATIC_PATHS` + `TOOLS` (MCP contract v4, 18 → 20 tools)
- `apps/backend/tests/test_mcp_server.py` -- 20-tool `EXPECTED_TOOLS`, both tool-count assertions
  bumped, 5 new byte-identity tests (empty/populated × 2 tools + the `?date=` proxy)
- `apps/frontend/app/desk/page.tsx` -- `PlaybookEvidenceSection` renders `data.signature`
- `runs/goal-session-playbook/journey-scripts/J-08.json` -- new golden replay script
- `incredible_auto_dev/scripts/automation/browser-qa-phase.sh` -- verify-BREACH now aborts
- `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` -- verify-BREACH now aborts (before the
  browser-qa checkpoint)
- `incredible_auto_dev/scripts/automation/qa-phase.sh` -- sources `lib/replay-lane.sh`, gates its own
  Chrome MCP dispatch on `store_scope_require`
- `incredible_auto_dev/tests/automation/test-store-scope-guard.sh` -- 6 new assertions (§9/§10/§11)
- `project-extensions/store-scope/store-scope.env` -- project-identity guard (pure prepend; no
  protected-path/assert/prepare change)
- `project-extensions/store-scope/README.md` -- documents the identity guard

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest -p no:warnings`
Result: **2163 passed, 8 skipped, 0 failed, exit 0** (196.67s). Clears both floors (iter-8's 2158,
the era-open 1926); skip count = 8 exactly.

`Config().config_fingerprint()` → `08e471b10130e1e2`, unchanged. `git diff` confirms
`desk_forward.py`, `desk_playbook_detect.py`, `desk_playbook.py`, `docs/playbook-detector-spec.md`,
`docs/goal.md`, `config.py`, `meta.py` are ALL byte-unmodified (empty diffs against each, individually
confirmed).

Framework: `bash incredible_auto_dev/scripts/automation/run-evals.sh` → **152 pass, 0 fail** (includes
`test-store-scope-guard.sh`'s now-34 assertions).

Frontend: `npx tsc --noEmit` → zero errors.

Live browser / golden-replay verification (scoped rig, `apps/backend/scripts/
start_scoped_qa_backend.sh` on `:8301`, frontend rebuilt at `:3301`, Chrome CDP `:9222`):
- `demo_runner.py --mode lint` — J-01..J-08: all clean.
- `demo_runner.py --mode verify --journeys J-08` — 1/1 PASS.
- J-08's deliberately logic-impossible counter-mutation (step 2 requiring `"to_close"` AND `"1h"` on
  the same row) — 1/1 FAIL, confirming the assertion genuinely discriminates.
- **Full Required-still-passing regression replay: `demo_runner.py --mode verify --journeys
  J-01,J-02,J-03,J-04,J-05,J-06,J-07,J-08` on the SAME scoped rig — 8/8 PASS** (verdict PASS,
  0 failed). This clears the DoD's "Required-still-passing J-01–J-08 remain green" line via
  deterministic replay for every one of them, including J-08 itself (better than the DoD's own
  stated minimum of an LLM fallback for J-08, since its golden landed this iteration).
- `GET /research/desk/playbook/evidence` and the MCP `desk_playbook`/`desk_playbook_evidence` tools —
  verified live over HTTP on the scoped rig AND (after restoring services) on the operator's real
  backend: `list_tools()` = 20 names, both new tools call non-error.
- Screenshot: `reports/qa/goal-playbook-iter-9-evidence/desk-evidence-signature-crop.png` — the
  Playbook Evidence section showing "Built from signature: `9803f6881e8f86b3`" above the register
  paragraph, with a well-populated `5m`/`to_close`/`mdd_*` row set beside `below_min_n`-tagged `1h`/
  `4h` rows.

## Kept-route byte-identity / cumulative-diff inventory check (static, developer-level)

Full static confirmation, complementing (not replacing) the browser-qa-agent/auditor's own live
route-diff for J-10:

- `git diff ed87dca..HEAD --stat -- apps/backend/app/` (era-open commit → before this iteration's
  uncommitted work) touches ONLY the `desk_playbook*` module family plus one additive extension to
  `desk_routes.py` (+404/-1, the single removed line being an import statement replaced by a longer
  import list — no kept-route handler touched). `bars.py`, `levels.py`, `tradability.py`, `setups.py`,
  `edge_report*.py`, `backtests.py`, `profiles.py`, `desk_universe.py`, `desk_screen.py`,
  `desk_forward.py`, `desk_sessions.py`, `desk_meta_cache.py`, `desk_topup*.py`, `config.py`,
  `meta.py`, `main.py` are ALL absent from the diff — their serving code never changed, so their
  served responses cannot have changed either.
- `git diff HEAD -- apps/backend/app/` (this iteration's own uncommitted work on top) touches ONLY
  `app/mcp/__init__.py` — confirmed via `git status --short` and `git diff --stat`.
- `git diff ed87dca..HEAD --stat -- apps/backend/app/mcp/` returns EMPTY for the committed history —
  this iteration is the FIRST time `app/mcp/__init__.py` has been touched anywhere in the era, exactly
  matching the plan (only J-09 touches MCP).
- Frontend: `git diff ed87dca..HEAD --stat -- apps/frontend/` touches only `app/desk/page.tsx`,
  `lib/api.ts`, `lib/types.ts` — no other page/route.
- Non-playbook backend TEST files touched across the whole era:
  `test_desk_refresh_chain_guard.py`, `test_desk_ui_guards.py`, `test_qa_scoped_backend_guard.py` —
  exactly the "named guard-test extensions" the inventory declares.
- The two named MCP-tool-list exemptions (18 → 20) and the new playbook routes are the only additions;
  everything else in the diff is either the `desk_playbook*` family itself, its own tests, or the
  store-scope guard/fixture-rig infrastructure supporting it (assert/prepare scripts, seeders,
  launchers) — all named in the goal's own declared inventory.

This is a static, code-diff-level proof (unchanged code ⇒ unchanged served output under identical
inputs); it does not replace the browser-qa-agent's own live HTTP route capture for J-10, which this
handoff defers to that step as planned.

## Known Issues

- **The store-scope abort does not (and by design cannot) undo a breach that already happened.** If
  `store_scope_verify` reports BREACH, the data was already written before the abort fires — the
  mechanism prevents the run's verdicts from being silently trusted afterward, it does not roll back
  the write (the project's own append-only rail forbids that anyway). This is the same limitation the
  iter-8 audit already noted for the disclose-only version; the abort makes the failure loud and
  un-checkpointable rather than fixing the underlying append.
- **`qa-phase.sh`'s new gate only covers ITS OWN dispatch.** It does not retroactively harden anything
  about how `run-phase.sh` sequences `qa-phase.sh` relative to `browser-qa-phase.sh`; each script's
  gate is independent (matches the existing "PROJECT-NEUTRAL BY CONSTRUCTION" no-op-per-project
  design — no shared state was introduced).
- **The identity guard in `store-scope.env` cannot detect a literal `git clone` of tapeology
  (history and remote intact) repurposed as a different project without repointing its remote.** This
  is inherent to a remote-URL-based check; TC-17's own scenario ("copied wholesale as a starting
  template" without carrying the `.git` history/remote) is the one this guards against, and does.
- **No live route-diff harness exists yet for J-10's own kept-route byte-identity acceptance** (a
  before/after HTTP capture of every kept route). This iteration's own contribution is the static
  code-diff proof above; building a dedicated live-capture tool was not in this iteration's IN SCOPE
  list and is left to the browser-qa-agent/auditor's own J-10 pass, as the phase spec's own division
  of labor implies (J-10 explicitly names "browser-qa-agent... and deterministic replay" as its own
  verifiers).

## Environment

**State at handoff: BOTH real services healthy, exactly as the dispatch note asked.**

- `:8301` — the OPERATOR'S REAL backend (`CHAIN_BACKEND_PORT=8301 bash scripts/start-backend.sh`, no
  `TAPEOLOGY_*` overrides). Confirmed serving the real 101-member S&P-100 universe
  (`source_url=https://en.wikipedia.org/wiki/S%26P_100`). `assert_scoped_qa_backend.py` correctly
  reports **NOT SCOPED** against it (the honest, expected state).
- `:3301` — the real frontend (`npx next dev -p 3301`, `NEXT_PUBLIC_API_URL=http://localhost:8301`),
  healthy, rebuilt fresh (no stale `.next` from the scoped-rig session — a plain `next dev` restart,
  not a `next build`, per the "never `npm run build` against the live dev server's `.next`"
  instruction).
- `:9222` — the pre-existing isolated headless Chrome, still holding CDP (untouched by this session).
- The operator's real `apps/backend/.data/` store: untouched by any of this session's dev-verification
  work — `:8301` was temporarily swapped to the scoped fixture rig TWICE (once for the J-08 golden's
  own development/verification, once for the 8-journey regression replay above), each time via
  `start_scoped_qa_backend.sh` with no prior listener to disclose/restore (nothing was running when
  this session began), and restored to the real backend both times afterward. The final MCP sanity
  check ran read-only GETs against the now-restored real backend
  (`desk_playbook`/`desk_playbook_evidence` GETs never write).

To stand the scoped rig up again for further browser/replay work:

```bash
bash apps/backend/scripts/start_scoped_qa_backend.sh   # ~15-25s: seed + health on :8301
bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh require   # proves it
# ... browser/replay work ...
CHAIN_BACKEND_PORT=8301 bash scripts/start-backend.sh   # restore the operator's real backend after
```
