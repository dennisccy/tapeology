# Iteration 16 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-16
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `quote_depletion.observed_through` / `.available_at` (TR-26 timing fix) | OK — in-place correction inside the already-registered canonical owner, `micro_observer.py`; no second computation path created; value stays unserved by any endpoint/MCP tool | `apps/backend/app/research/micro_observer.py:646` (fix); confirmed via `grep -rln quote_depletion apps/backend/app/` → only `micro_features.py` and `micro_observer.py`, no route/MCP file |
| Corpus readiness truth / `sealed_tranche` / `joinable_corpus` (`MicroReadinessSection`) | OK — component still fetches only the registered `GET /research/desk/micro/readiness` response; this round's diff is a DOM wrapper only, no new fetch, no recompute | `apps/frontend/app/desk/page.tsx:5889-5910` |
| Scout trials (`trial.feature.name`/`.transform`, `trial.outcome.horizon_key`) | OK — already-registered sub-fields of the "Scout trials..." row (`scout_ledger.py`/`scout.py`, `GET /research/desk/micro/scout`); this round only adds a defensive optional-chain + established page-wide `"—"` fallback glyph (60+ existing uses in the same file, e.g. `page.tsx:1532,1996,2671,3295,3511`) for a missing value — not a new value, not a re-fetch, not a recompute | `apps/frontend/app/desk/page.tsx:6321,6323` |
| Accessor origin-fence / `ExposureRegistry` (TR-3, TR-22 mechanisms) | OK — no production edit to `micro_accessor.py` or `walkforward.py` this round (both files absent from the diff stat); this iteration adds only test-file coverage. Both mechanisms remain internal/unserved, matching blueprint.md's own iter-16 note | `git diff --stat` confirms only test files touched; `blueprint.md:219-233` |

No new displayed value was introduced this iteration (confirmed against the diff: the only frontend changes are a `data-testid` DOM attribute and a rendering fallback for an already-fetched field). No duplicate computation, no non-canonical source.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` → Microscope Readiness (`MicroReadinessSection`) | OK — pre-existing component in its already-registered home (blueprint.md IA table row "Corpus readiness truth (J-01)"); no new route | `git diff --stat` b6ddb02..HEAD shows `app/meta.py` (`UI_ROUTES`) untouched; `apps/frontend/app/desk/page.tsx` is the only frontend file changed |
| `/desk` → Scout Ledger (`ScoutLedgerSection`) | OK — pre-existing component in its already-registered home (blueprint.md IA table row "Scout + candidate ledger (J-04)"); no new route | same as above |

No new page, route, nav-skeleton change, duplicate home, or parallel shell this iteration.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None — no Part C product-facing drift (label inconsistency, formatting drift, unregistered-but-new value) was introduced this round. The `"—"` fallback glyph added to the Scout table matches the page's own pre-existing convention (60+ prior uses across `page.tsx`), so it reinforces consistency rather than drifting from it.

---

## Judgment calls carried into this audit (from the dispatch prompt)

**1. Iteration-15 COHERENCE-WARN closure — VERIFIED CLOSED.** Read `MicroReadinessSection` directly: `data-testid="micro-readiness-section"` now wraps all three render paths — loading (`page.tsx:5893`), unavailable (`page.tsx:5900`), and loaded (`page.tsx:5910`) — mirroring `ValidationVaultSection`'s pattern (`page.tsx:6682-6699`, `data-testid="validation-vault-section"` in all three states) exactly. The WARN is closed; no residual gap.

**2. `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` as a 7th changed tracked file, absent from `status.json`'s `changed_files`, with `unknown` replay status — judged NOT a coherence concern; plainly out of this gate's jurisdiction.** I read the file's own diff directly. The change: `default_timeout_ms` 10000→20000, the `structure-as-of-input` value corrected 17:00:00→16:00:00, and — the substantive part — steps 9-10 (expand Playbook Evidence + fill the playbook date input) were replaced with four new steps expanding Microscope Readiness / Scout Ledger / Walk-Forward / Validation Vault and asserting each section's real empty-state text, with the two pre-existing Referee-section steps renumbered but otherwise unchanged. This is a legitimate widening of J-10's own coverage to match this iteration's explicit testing requirement ("every shipped `/desk` section including the three Referee sections and all four Rapid-Microscope sections") — the prior script never exercised the four Rapid-Microscope sections at all. It is not a Data Contract violation (touches no served value/endpoint) and not an Information Architecture violation (touches no nav path or route) — it is a test-asset bookkeeping-accuracy gap (the reviewer and QA lanes both undercounted "6 files changed" when a 7th tracked file changed, and the asset's own recorded execution status is `unknown` rather than `passing` because it was rewritten but not re-run through the deterministic replay harness this round). That is squarely QA/release bookkeeping territory, not product coherence — nothing about app structure or a displayed value's source of truth is at stake, and the dispatch prompt itself notes the auditor already confirmed every new `expect`/testid resolves in source and that the LLM browser lane live-confirmed the sentinel. Recommendation (non-blocking, does not affect this verdict): correct `status.json`'s `changed_files` count and run J-10 through the deterministic replay harness next time the store-scoped rig is up, so its stored status reads `passing` rather than `unknown`.

**3. `micro_accessor.py:34-37`'s module docstring describing a `walkforward.py` origin-fenced/exposure-logging read path that does not exist — confirmed as a real defect, judged OUT OF this gate's scope.** I verified directly: `grep -rn "MicroAccessor(" apps/backend/app/research/*.py` finds exactly two production construction sites (`micro_join.py:434`, `scout.py:353`), both passing `origin=None`; `grep -n "MicroAccessor\|origin=" apps/backend/app/research/walkforward.py` returns nothing — `walkforward.py` never imports or constructs `MicroAccessor` at all; `grep -n "log_exposure" apps/backend/app/research/*.py` shows every call site lives inside `micro_accessor.py` itself. So the docstring's claim ("Only `walkforward.py`'s OWN origin-fenced reads... participate in exposure logging") describes a call site that does not exist in production. This is independently confirmed in-code by this round's own developer: both `test_walkforward.py` and `test_micro_accessor.py`'s new TR-3 section headers state the identical finding ("direct code inspection found no production call site that actually constructs `MicroAccessor(origin=...)` today ... this file's own `build_folds` is a pure function over session-date strings that never touches the accessor"), which is why TC-2/the TR-3 aggregate-boundary proof was built as a new direct test on `MicroAccessor` rather than routed through `walkforward.py`. This is a genuine, already-acknowledged (if not yet cleaned up) documentation defect — but it does not fall under Part A or Part B: it names no displayed/served value in conflict (the blueprint itself already correctly documents this mechanism as "pre-existing and equally unserved directly," `blueprint.md:229-233`, so no registered Data Contract row is duplicated or mis-sourced) and touches no nav/route surface. It is an internal module's stale self-description — reviewer/code-quality territory, not product-structure coherence. Recommendation (non-blocking, does not affect this verdict): a future round should correct `micro_accessor.py:34-37` to state plainly that neither current production caller constructs an origin-fenced read yet, and that the aggregate-boundary behavior is proven today only by direct unit test (`test_walkforward.py::test_tr3_an_origin_fenced_loop_over_several_sessions_returns_exactly_the_set_le_origin`).

**4. Decomposer's iter-16 blueprint note ("documentation-only, no Data Contract or IA change") — VERIFIED TRUE against the actual diff.** Checked each of its claims against code: no new endpoint (`micro_routes.py` untouched — absent from `git diff --stat`), no new route/nav (`app/meta.py` untouched), `quote_depletion` remains unserved by any route or MCP tool (grep above), and TR-3/TR-22's mechanisms received no production edit this round (`micro_accessor.py` and `walkforward.py` both absent from the diff stat — only their test files changed). The note holds up exactly as written; the blueprint.md edit itself (+16 lines, the iter-16 `<!-- -->` note) required no Data Contract or IA table change, correctly.

## Files/commands consulted

- `runs/goal-session-rapid-microscope/state/blueprint.md`
- `docs/phases/goal-rapid-microscope-iter-16.md`
- `reports/phase-goal-rapid-microscope-iter-16-ui-surface-map.md`
- `git diff b6ddb02a89a2e8d7c8efcb900b49c668bdc51877 --stat -- . (noise-excluded)` and the matching full diff, plus the excluded-paths `--stat` (surfaced `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` as the 7th changed tracked file)
- Direct reads: `apps/backend/app/research/micro_observer.py`, `apps/frontend/app/desk/page.tsx` (`MicroReadinessSection`, `ValidationVaultSection`, `ScoutLedgerSection`), `apps/backend/app/research/micro_accessor.py` (module docstring), `apps/backend/tests/test_walkforward.py`, `apps/backend/tests/test_micro_accessor.py`, `apps/backend/tests/test_desk_ui_guards.py`
- `grep` sweeps: `MicroAccessor(` and `log_exposure` production call sites; `quote_depletion` route/MCP exposure; `"—"` fallback-glyph convention in `page.tsx`
