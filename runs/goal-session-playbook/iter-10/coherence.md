# Iteration 10 — Coherence Audit

**Iteration:** goal-playbook-iter-10
**Date:** 2026-08-12
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Independence note

No prior coherence verdict exists for iteration 10 (`runs/goal-session-playbook/iter-10/` held
only `.steps/`, `depth-dispatched`, `goal-slice.md`, `snapshot-sha` before this file was written —
confirmed by directory listing). This verdict was produced fresh against the blueprint, the
iteration diff, and the codebase; it does not inherit or cite any judgment the hard auditor made
by hand.

## Scope actually shipped this iteration

Read in full: `runs/goal-session-playbook/state/blueprint.md`, `.claude/skills/coherence-audit.md`,
`docs/phases/goal-playbook-iter-10.md`, `docs/goal.md`'s `### OWNER RATIFICATION` R-3 block
(R-3.1/R-3.2(a)-(e)/R-3.3), `reports/phase-goal-playbook-iter-10-ui-surface-map.md`.

Diffed every changed path against snapshot `0e3b38be401ca18a0e44d1ac6be1e67b2b17e876` (the exact
noise-excluded command from the dispatch prompt) and cross-checked the result against `git status`
so nothing was missed, including the one untracked new file `git diff <sha>` cannot show on its
own:

- `apps/backend/app/research/desk_playbook_detect.py` (+13/-0, inside `_range_trade_side`)
- `apps/backend/scripts/seed_playbook_iter8_replay_rig.py` (+29/-4, fixture-rig index repair)
- `apps/backend/tests/test_desk_playbook_detect.py` (+87/-0)
- `apps/backend/tests/test_desk_playbook.py` (+69/-0)
- `apps/backend/tests/test_seed_playbook_iter8_replay_rig.py` (new, untracked, read directly)
- `apps/frontend/app/desk/page.tsx` (+3/-1, one new conditional chip)
- `apps/frontend/lib/types.ts` (+5/-0, one new optional field)
- `docs/playbook-detector-spec.md` (+~47/-~13, R-3.2(a)/(b)/(c)/(d)/(e) transcription)
- `runs/goal-session-playbook/journey-scripts/J-10.json` (test asset — harness scope, reviewed for
  context only)

`docs/goal.md` shows in `git status` (vs `HEAD`) but a zero-line diff against the snapshot SHA —
the R-3 ratification was already present in the snapshot the iteration was dispatched from, so it
is background/context here, not this iteration's own edit.

## Data Contract check

The only Data-Contract-relevant change this iteration is `geometry.turned_at_midrange: boolean`,
a new optional field on the already-registered "Playbook records" row (blueprint.md line 129),
authorized by `docs/goal.md` R-3.2(b) with three binding constraints: disclosure-only, reuse an
already-registered constant (mint nothing new), and ride the existing owner/endpoint/MCP proxy
unchanged.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `geometry.turned_at_midrange` (new field, "Playbook records" row) | OK | Computed only inside the row's existing owner function `_range_trade_side`, `apps/backend/app/research/desk_playbook_detect.py:1180-1200` (immediately beside, and reusing the same `hold_tol = params["range_hold_tol_mbr"] * mbr` already computed at `:1097` for the pre-existing `crossed_midrange`/`absorption_bar_present` fields in the same function). No new function, no second module. |
| — reused constant, not a new one | OK | `grep -n "^PLAYBOOK_[A-Z_]* ="` across `apps/backend/app/research/*.py` finds `PLAYBOOK_RANGE_HOLD_TOL_MBR` defined only in `apps/backend/app/research/desk_playbook.py`, which has a **zero-line diff** against the snapshot (`git diff <sha> -- apps/backend/app/research/desk_playbook.py` = 0 lines) — no new `PLAYBOOK_*` constant was added anywhere in the diff (confirmed by grepping the diff's added lines for a `PLAYBOOK_[A-Z_]* =` pattern: zero matches). |
| — served endpoint unchanged | OK | `apps/backend/app/research/routes.py` and `apps/backend/app/research/desk_routes.py` both show a zero-line diff against the snapshot — `GET /research/desk/playbook` is untouched; the field rides the response verbatim via the existing `geometry` dict literal at `desk_playbook_detect.py:1263` (`"turned_at_midrange": turned_at_midrange,` inserted next to `"crossed_midrange": crossed_midrange,`). |
| — MCP proxy unchanged | OK | `apps/backend/app/mcp/__init__.py` shows a zero-line diff against the snapshot; `desk_playbook` (`:123`, `:344`) is already a byte-identical proxy of the same endpoint, so it forwards the new key automatically with no MCP code change — matches TC-16. |
| — UI reads it from the canonical source, not a new fetch | OK | `apps/frontend/app/desk/page.tsx` diff (`:5094-5106`) adds one conditional JSX line, `{geometry.turned_at_midrange && " · turned at midrange"}`, reading the SAME `geometry` object the pre-existing `crossed_midrange`/`absorption_bar_present` chips already read from the same `PlaybookSignalDetail` render — no new `fetch`/`useEffect`/API call anywhere in the hunk. `apps/frontend/lib/types.ts:1523-1527` adds only the matching optional type field beside `crossed_midrange?: boolean`. |
| — not a duplicate/synonym of an existing value | OK | `turned_at_midrange` and `crossed_midrange` are proven independent facts, not a re-derivation: `test_canonical_range_trade_short_mirrors_the_long_fixture` (`test_desk_playbook_detect.py`) asserts `crossed_midrange is False` and `turned_at_midrange is True` on the same fixture; the new near-miss-pair test `test_range_trade_turned_at_midrange_true_and_its_near_miss_control` isolates the one input (`peak_high`) that flips only `turned_at_midrange` while every other field — including `crossed_midrange` — stays byte-identical between the True and False runs. |
| — old records stay honest (no backfill) | OK | New test `test_a_pre_iteration_10_style_range_trade_record_serves_geometry_without_the_new_key` (`test_desk_playbook.py`) writes a record with the key stripped, reloads it through `PlaybookStore`, and asserts `GET /research/desk/playbook` still serves HTTP 200 with the key absent (never `null`) — confirms the append-only/no-backfill anti-goal holds through the SAME canonical endpoint, not a second one. |
| — signature/fingerprint pinned | OK | Extended `test_monkeypatched_constant_moves_parameters_and_signature_and_mints_a_new_version` proves both directions: monkeypatching `PLAYBOOK_RANGE_HOLD_TOL_MBR` moves `playbook_parameters()`/the signature; reverting it reproduces the exact pre-monkeypatch signature and `CONFIG.config_fingerprint() == "08e471b10130e1e2"`. Independently re-ran `Config().config_fingerprint()` against the current tree: prints `08e471b10130e1e2`, matching the pin. Ran all three touched test files directly (`test_desk_playbook_detect.py`, `test_desk_playbook.py`, `test_seed_playbook_iter8_replay_rig.py`): 104 passed, 0 failed. |
| Doc-only spec transcriptions (R-3.2(a)/(c)/(d)/(e), `docs/playbook-detector-spec.md`) | OK | Not a Data-Contract row (documentation, not a served value), but checked for a hidden code change since a silent spec/code divergence would be a "numbers don't match" risk: the `desk_playbook_detect.py` diff contains ONLY the 13-line `turned_at_midrange` addition inside `_range_trade_side` — zero lines touched in `_find_double_extreme` (double_top/double_bottom, R-3.2(a)), the JBE/DBI gate code (R-3.2(c)), `cup_handle` (R-3.2(d)), or `_range_trade_side`'s own trigger-scan block (R-3.2(e)) — matches TC-1/TC-2/TC-3/TC-4's zero-code-diff claim. |

No shared value from the blueprint's "Unchanged owners" list (bars, sessions, measurement helpers,
universe membership, tradability, levels, evidence aggregation) was touched by this iteration's
diff — `desk_playbook_evidence.py`, `desk_forward.py`, and `desk_playbook_features.py` all show a
zero-line diff against the snapshot, matching the spec's OUT OF SCOPE list.

## Information Architecture check

This iteration introduces no new page, route, section, or nav entry. The sole frontend change is
one additional conditional text fragment (`{geometry.turned_at_midrange && " · turned at midrange"}`)
inside the element `data-testid="desk-playbook-signal-range-trade-geometry"`, which already existed
(shipped goal-playbook-iter-6) inside the blueprint's already-registered "Playbook Signals" section
under `/desk` → Desk nav (blueprint.md Navigation-skeleton block + Feature/journey-homes table, J-06
row). There is no new feature/route to evaluate for reachability, duplicate-home, or parallel-shell
— confirmed by the ui-surface-map ("Only one production UI surface is affected... the change is a
single new conditional text fragment inside an element that already existed") and by the page.tsx
diff itself.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `range_trade` geometry chip, `/desk` Playbook Signals section | OK — not a new surface | `apps/frontend/app/desk/page.tsx:5094-5106` (existing `data-testid="desk-playbook-signal-range-trade-geometry"` element, unchanged parent section); nav skeleton confirmed unchanged in `runs/goal-session-playbook/state/blueprint.md`'s Navigation-skeleton block (no nav-file edit — `NavBar.tsx`/`app/meta.py` `UI_ROUTES` not present in the diff). |

The blueprint itself was freshened additively (status banner + the Data-Contract "Ships at" note),
not restructured — no nav-skeleton edit, consistent with the iteration spec's own "Blueprint
conformance" section ("no `blueprint.reapproval-requested` file was written").

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The scoped QA-fixture-rig index repair (`apps/backend/scripts/seed_playbook_iter8_replay_rig.py`,
  `_reindex_copied_series` calling `desk_index_reconcile.run_reconcile`) and the `J-10.json`
  golden-replay reassertion (step 6 now checks the pre-existing, unchanged `"Top-up Runs"` heading
  plus two new steps for `"Index Reconciliation"`/`"Screen Runs"`, all confirmed still rendered via
  `<Panel title="...">` at `page.tsx:7230/7238-7239/7248-7249`, unchanged by this iteration) are
  test/fixture infrastructure, not product surface or a Data-Contract row — out of this gate's
  scope by the blueprint's own iteration-10 status note, and not flagged.
- No unregistered-value, mislabeled-entity, or cross-page formatting-drift issue was found. The new
  chip follows the exact existing sibling pattern (`crossed_midrange`, `absorption_bar_present`) in
  wording, punctuation (` · <label>`), and conditional-render style.
