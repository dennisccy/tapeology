# goal-playbook-iter-10 Audit Report

**Date:** 2026-08-12
**Auditor:** Hard audit pass — skeptical, evidence-based (era-closing; first auditor dispatch in five iterations)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Era B2's closing work is genuinely done: R-3.2(a)/(c)/(d)/(e) landed as doc-only edits with
git-diff-proved zero detector change, R-3.2(b)'s `turned_at_midrange` shipped inside every one of
its binding constraints (spec-first, disclosure-only, reuses `PLAYBOOK_RANGE_HOLD_TOL_MBR`,
optional and never backfilled), and both carried defects — `J-10.json`'s vacuous step 6 and the
scoped rig's blank `/structure` chart — are fixed and independently verified, not merely claimed.
Two evidence-class gaps remain and are the reason this is not a clean PASS: the DEFINITION OF DONE's
"the new disclosure visible in at least one fresh screenshot" was **unmet at hand-off** (I closed it
myself during this audit — evidence below), and the **coherence-auditor never ran for this
iteration** (the first miss in ten), so no COHERENCE-PASS exists for the one iteration in the era
that adds a Data-Contract field; I discharged its substantive check by hand instead.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): the new `run_reconcile` call writes to a destination no scoping guard covers.**
`apps/backend/scripts/seed_playbook_iter8_replay_rig.py:311` calls
`_reindex_copied_series(bar_store, get_bar_index())`. `get_bar_index()`
(`apps/backend/app/research/routes.py:449-460`) resolves `TAPEOLOGY_BAR_INDEX_DB` first and only
falls back to a sibling of `bar_dir_resolved()`. The rig's own `_assert_scoped(root)` checks only
four env vars (`desk_playbook_backscan.py:111-116` — playbook dir, playbook log dir, backscan log
dir, universe dir); `TAPEOLOGY_BAR_INDEX_DB` is not among them. The store-scope guard's protected
manifest is 12 **directories** (`reports/qa/goal-playbook-iter-10-store-scope-guard.md:5`) and
`apps/backend/.data/bar_index.db` is a file at the `.data/` root, inside none of them. Since
`BarIndex.reindex()` is `DELETE FROM bar_index` + repopulate (`bar_index.py:238-256`), a run of this
seed script with the four scoping vars set but `TAPEOLOGY_BAR_INDEX_DB` pointing at the real index
would wipe and re-key the operator's index from 172 fixture series.
**Verified NOT breached this run:** `apps/backend/.data/bar_index.db` md5 `a93c24dd1ecbdd8e…`,
mtime `2026-08-10 07:58:08` — untouched across the whole iteration (started 2026-08-11 22:40), and
the sanctioned launcher chain does export the var correctly
(`start_scoped_qa_backend.sh:73` → `qa_playbook_iter7_fixture_scoped_backend.sh:86`). Latent, not
live. Not fixed here: hardening `_assert_scoped` changes a shared guard's contract used by other
rigs — outside this iteration's IN SCOPE.

**B2 — GAP (gap): `turned_at_midrange: true` has never been observed on any recorded data.**
I read every playbook record in both stores rather than trusting the QA row. Real store
(`apps/backend/.data/playbook`): 87 `range_trade` signals across four records
(31 + 20 + 26 + 10), **all** with the key absent — which independently confirms the no-backfill
claim and R-3.1's own count. Scoped rig: exactly 2 `range_trade` signals (the same RTAAA session
under two signatures), both `false`. So 0 of 89 recorded signals exercise the `true` branch; its
only proof is the synthetic fixture at `test_desk_playbook_detect.py:1215-1251`. I checked whether
the branch is structurally dead and it is not: for a long, `true` requires both high-zone touches to
fall strictly before the first low-zone touch (otherwise the window's own max high sits ≥ 1.0·MBR
from the midpoint, beyond the 0.5·MBR tolerance) — a real "morning high, then double-bottom test"
shape, which is exactly what the fixture builds. Reachable, but its real-world frequency is
genuinely unknown and should be reported as unknown, not assumed.

**B3 — OBSERVATION (observation): the field's name says "prior swing", its mechanics read the whole
approach window.** `desk_playbook_detect.py:1198-1202` takes `max(high)`/`min(low)` over
`session_bars[armed_touches[0] : b+1]`. When the armed zone has ≥ 3 touches that window spans
several swings, so the disclosure answers "did the approach's *overall* extreme sit at midrange",
not "did the swing immediately before `b`". The divergence is always fail-closed (never invents a
`true`), and §3.7's rewritten Disclosures clause states the mechanical reading verbatim, so spec and
code agree — only the English label ("the prior swing turned at midrange") and the chip text are
looser than the arithmetic. No action; recorded so a future revision does not mistake the label for
the definition.

**Verified clean (no finding):** the field never gates — it is computed after the degenerate-trigger
void and the trigger scan, and is written only into `geometry` (`:1259`). It is lookahead-clean:
the window ends at `b`, and `b = t-1 < trigger_idx`. It cannot crash on a short window:
`armed_touches` always holds ≥ 2 ascending indices (`zone_touches`, `desk_playbook_features.py:259`)
so the slice is never empty — the spec's "no confirmable prior swing" error case resolves to a
disclosed boolean, never a `ValueError`. Exactly one computation site exists repo-wide (grep:
`desk_playbook_detect.py:1202` only) and zero in the frontend.

### Frontend Findings

**F1 — IMPORTANT (closed by audit evidence): the DoD's "disclosure visible in at least one fresh
screenshot" was unmet.** The escape hatch was NOT taken (the field shipped), so the DoD required the
screenshot. UT-03 is `SKIPPED` (`reports/phase-goal-playbook-iter-10-ui-test-results.md:27`) because
no `true` example exists anywhere in the rig — which I confirmed independently (B2). The only chip
evidence filed, `UT-02-range-trade-geometry.png`, shows the *absence* of the chip. I opened it: the
line reads `… broke at slot 7 · crossed midrange`, nothing more. So the single user-visible pixel
this iteration adds had never been seen rendering.
**Closed during this audit, without changing any source file or touching any store:** a throwaway
Playwright probe intercepted the browser's own `GET /research/desk/playbook` response and flipped
`turned_at_midrange` to `true` on one real 2026-06-24 signal (BLK) before React saw it. Result:
`range 4.69 MBR wide · low zone touches 2 · high zone touches 3 · broke at slot 26 · crossed
midrange · turned at midrange`. Screenshot opened and read, then filed at
`reports/qa/goal-playbook-iter-10-evidence/AUDIT-turned-at-midrange-true-chip.png`. Store proof:
a 9841-file manifest over the 12 protected paths was identical before and after (`diff` → zero
lines), and `bar_index.db`'s md5 was unchanged.

**F2 — GAP (gap, pre-existing): the invalid-date input's amber border never renders.** UT-05's FAIL
is real and its diagnosis holds up: `ASOF_INPUT_CLASS` already carries `border-slate-700`, and
`page.tsx:5591` appends `border-amber-500` — two equal-specificity single-class rules, so Tailwind's
generated order decides and slate wins. I confirmed it is **not** a regression from this iteration:
`apps/frontend/app/desk/page.tsx` has exactly one diff hunk this pass, at 5094-5107; the date input
lives at 5583-5592. The semantic contract (`aria-invalid="true"` + the verbatim error message + an
honest empty state) is intact, so this is cosmetic only. Out of scope to fix here.

### Test Findings

**T1 — IMPORTANT (gap): the coherence-auditor did not run for iteration 10.** The DEFINITION OF DONE
names it explicitly ("Coherence-auditor (runs at every depth) confirms single-source-of-truth for
the new field via its Data Contract check"). There is no `runs/goal-session-playbook/iter-10/
coherence.md` (iterations 1-9 all have one), no `coherence_audit` telemetry event for iter 10 (nine
exist, one per prior iteration, all COHERENCE-PASS), and — unlike `ux-regression` and
`ui-test-design` — no `step_skipped` record either, so the omission is silent. The trace confirms
it: iteration 9 ran it at `0096-coherence-auditor.log`, between reviewer and browser-qa; iteration
10 goes `0106-reviewer → 0107-ui-impact-analyst → 0108-qa → 0109-browser-qa-agent →
0110-demo-narrator` with no coherence step, and the pipeline is now past that slot.
**Substance discharged by hand during this audit** (so the risk it guards is retired, but no
COHERENCE-PASS exists and none should be cited): exactly one computation site repo-wide
(`desk_playbook_detect.py:1202`); served by the already-registered `GET /research/desk/playbook`
with no new route; `git diff --stat` on `apps/backend/app/mcp/` is **empty**, so the existing
`desk_playbook` proxy forwards the field with zero MCP diff; `blueprint.md`'s "Playbook records" row
was extended in place with no new row, no new owner, no new endpoint; the frontend recomputes
nothing (one type declaration, one render site).

**T2 — GAP (gap): J-09 was re-verified by no lane this iteration, and the file that tracked its
missing golden was auto-deleted.** The merged results carry J-09 as `DEFERRED-BUDGET`
(`…ui-test-results.md:65`); the deterministic replay ran 7 journeys (J-01..J-05, J-07, J-08) and
J-09 has no golden script at all (lint covers nine: J-01..J-08, J-10). As a side effect,
`runs/goal-session-playbook/state/golden-gaps` — whose entire content was `J-09` — was **deleted**:
`replay-lane.sh:530-537` rebuilds the file from PASSing journeys only, and a deferred journey is not
a PASS, so the gap list came out empty and the file was removed. The next iteration's SPEED-23
golden nudge can therefore no longer see J-09.
Mitigation that keeps this a GAP rather than worse: J-09's own acceptance is automated, not
browser-borne — `tests/test_mcp_server.py:198-199` pins the exact tool tuple and `:1363`/`:1382`
assert `len(TOOL_NAMES) == 20` with byte-identity — and that suite is inside the green run.

**T3 — OBSERVATION (observation): one of the three new J-10 assertions has a state-conditional
escape.** Steps 6 and 8 are airtight — `Top-up Runs`/`Screen Runs` occur only as the `Panel` title
and that section's own empty-state copy, both inside the section
(`page.tsx:7229-7230`, `:7248-7249`, `:1334`, `:1769`). Step 7's `Index Reconciliation` is also
matched case-insensitively by `ReconcileIndexControl`'s "Index reconciliation cancelled…"
(`page.tsx:3980`), which renders outside the section. Because all three must pass, the sentinel as a
whole still cannot go vacuous. I independently confirmed the substantive property the fix exists to
restore: all three titles are `<section>`/`<Panel>` siblings placed *after* the `latest !== null`
ternary (`page.tsx:7215-7252`), so they are state-independent by construction — the exact property
`"Forward Returns"` lacked.

**T4 — OBSERVATION (observation): a new assertion sits exactly on the tolerance boundary.**
`test_desk_playbook_detect.py`'s pre-existing canonical short fixture now asserts
`turned_at_midrange is True` at |202.0 − 201.5| = 0.50 == `hold_tol`, i.e. it tests the `<=`
inclusivity. Deliberate and documented in the test's own comment, and exact in binary floating
point here — but it means any future re-tuning of that fixture's prices flips the assertion for a
reason unrelated to the mechanism under test.

**Verified clean (no finding):** the True/near-miss pair changes exactly one input value
(`peak_high` 105.2 vs 106.0) and asserts every other field identical between the two runs — a
genuine single-variable control, not a bare outcome flip. TC-8's test proves absence-not-`null`
through a real `PlaybookStore` round trip **and** a live `GET /research/desk/playbook`; I confirmed
its real-data counterpart directly (B2).

---

## 3. Domain Assessment

The domain work here is small and correct, and the spec-vs-code reconciliation is the real content.
All four doc-only items are genuinely doc-only: `desk_playbook_detect.py`'s entire diff is the
13-line additive `turned_at_midrange` block in `_range_trade_side` plus one geometry key —
`_find_double_extreme` (R-3.2(a)), the JBE/DBI gates (R-3.2(c)), `cup_handle` (R-3.2(d)) and the
trigger scan (R-3.2(e)) are byte-untouched, satisfying TC-1..TC-4 mechanically. §3.9 needed no
separate edit: the file's own heading is the combined `### 3.8 double_top / 3.9 double_bottom
(mirror; double_top described)`, so the "mirrored by convention" claim is literally true.

The signature-stability requirement is met by construction, more strongly than by the new test:
`apps/backend/app/research/desk_playbook.py` — which owns every `PLAYBOOK_*` constant and
`playbook_parameters()` — has a **zero-line diff**, as do `config.py`, `meta.py`, `desk_forward.py`,
`desk_playbook_evidence.py` and `app/mcp/`. A signature keyed on those cannot move. I reproduced
`Config().config_fingerprint()` → `08e471b10130e1e2` and the two spec table rows show annotations
only, values still 1.5 and 0.5, with no new row added (TC-5).

The `/structure` diagnosis was correct and the repair is real, not aspirational: the rig's own
`bar_index.db` holds 171 rows of which **151 are AAPL**, and the filed screenshot — which I opened —
shows a fully drawn daily candlestick chart Nov 2025 → Aug 2026 with volume bars and the pinned
300.10/302.20 resistance band overlay. The one documented shortfall (171 of 172 series, `BSCAN`
double-recorded under an identical index key by an unmodified iter-7 fixture) is honestly disclosed
and does not touch AAPL.

The one thing worth the era's attention is B2/B3 together: `turned_at_midrange` is an honest,
non-gating, fail-closed disclosure, but it is a rule the corpus has never once satisfied. The
right register for it in any era-closing narrative is "shipped and unit-proven, never yet observed",
not "measured".

---

## 4. Fixes Applied During This Audit

No source file was modified. One missing DEFINITION OF DONE artifact was produced.

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/qa/goal-playbook-iter-10-evidence/AUDIT-turned-at-midrange-true-chip.png` | **Added** the missing F1 evidence: a fresh screenshot of the `· turned at midrange` chip rendering on a real `range_trade` signal, captured via an in-browser response interception (no source change, no store write). Verification: probe printed `CHIP PRESENT: True` and the geometry line `… · crossed midrange · turned at midrange`; image opened and read; protected-path manifest identical before/after (9841 files, zero-line `diff`), `bar_index.db` md5 unchanged. |

Independent re-verification run by this audit (not taken from any handoff):

- Full backend suite: `.venv/bin/python -m pytest -p no:warnings` → **exit 0**; collection sums to
  **2176** = 2168 passed + 8 skipped, clearing the 2163 floor.
- `tests/test_copy_discipline.py` + `test_desk_playbook_detect.py` +
  `test_seed_playbook_iter8_replay_rig.py` → 83 passed, exit 0 (the new chip copy is clean).
- `Config().config_fingerprint()` → `08e471b10130e1e2`.
- `git diff --stat` empty for `app/mcp/`, `desk_playbook.py`, `desk_forward.py`,
  `desk_playbook_evidence.py`, `config.py`, `meta.py`; `docs/goal.md`'s diff is a single
  +78/-0 insertion containing exactly the R-3 block (no self-widened authorization);
  `journey-scripts/J-06.json` untouched, as its NOTES require.
- Scoped rig read directly: 171 index rows / 151 AAPL; 2 `range_trade` signals, both `false`.
- Real store read directly: 87 `range_trade` signals, key absent on all 87.

---

## 5. Recommended Next Step

Proceed to the era evaluation, with three things stated honestly in it rather than papered over:

1. **Do not cite a coherence PASS for iteration 10** — none exists (T1). The Data-Contract check it
   would have performed is discharged in §2 above with citations; reuse that, or dispatch the
   coherence-auditor once before declaring the era closed.
2. **Record J-09 as "verified by suite, not re-driven" and restore its golden-gap** (T2). J-09's
   acceptance is automated and green, but `state/golden-gaps` no longer names it, so the next
   session will not notice it lacks a replay script. Re-adding the one line `J-09` to that file is a
   one-token repair.
3. **Report `turned_at_midrange` as shipped-and-unobserved** (B2). Zero of the 89 recorded
   `range_trade` signals exercise its `true` branch; the chip is now proven to render (F1), and the
   detector is proven to compute both branches on a fixture, but no real session has produced one.

The two GAPs left open (B1's uncovered `bar_index.db` write destination, F2's cosmetic amber border)
are correctly outside this iteration's scope; both are worth a line in the next iteration's or era's
backlog rather than a fix now.
