# goal-playbook-iter-4 Audit Report

**Date:** 2026-08-11
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-04's goal is genuinely achieved: `jbe`, `dbi` and `cup_handle` are implemented against
`docs/playbook-detector-spec.md` §3.3/§3.4/§3.6 (traced line by line, not read from the handoff),
wired into the one existing compute walk, measured on the imported rail with zero diff to it, and
legible in the already-shipped `/desk` Playbook Signals section with browser screenshots for all
three. Two IMPORTANT defects the review and QA passes both missed were found and fixed here: the
`dbi` geometry line described a short setup's base as "ascending" when the detector measured the
opposite, and the pre-registered TC-4/TC-5 near-miss tests never reached the jump gate they claim
to prove (they still passed with BOTH jump gates zeroed out). The remaining findings are documented
gaps, not blockers — the largest is a constants-level fact the owner should see before J-07 reads
firing frequency: spec §3.3's BOOK ratio gate can never reject on its own under the pre-registered
constants.

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation, not fixed): `cup_handle`'s rim gate reads `NEAR_EXTREME_MBR` where the spec names `RIM_MATCH_MBR`**
`apps/backend/app/research/desk_playbook_detect.py:654` and `:657` gate both rims' "near the
session high so far" test on `params["near_extreme_mbr"]`. Spec §3.6's formation text names
`PLAYBOOK_RIM_MATCH_MBR · MBR` for the left rim ("Left rim = confirmed swing-high pivot within
`PLAYBOOK_RIM_MATCH_MBR · MBR` of session-high-so-far"); only the right rim's "itself near the
session high" is left unquantified. Both constants are `1.0` today
(`desk_playbook.py:112`, `:118`), so there is **zero behavioural difference on any input** — which
is exactly why it is a latent trap: a spec revision moving `RIM_MATCH_MBR` would silently not reach
this gate, and the divergence would surface as a mystery in the back-scan. Not fixed: an inert
rename inside detection code is scope creep this iteration; the right closure is one line in the
spec (or the code) at J-06/J-07 time, decided by the owner.

**B2 — GAP (not fixed): the base is the MAXIMAL consolidation window, so it widens toward the 2.0-MBR cap and reshapes what fires**
`_find_one_continuation` recomputes the base at every candidate trigger via
`consolidation_range(session_bars, t - 1, ...)` (`desk_playbook_detect.py:403`), and that primitive
returns the **longest** qualifying window (`desk_playbook_features.py:199-213`). The base therefore
extends backward into the pullback/jump leg until the `2.0·MBR` cap bites. Evidence from the
operator's own real record (`apps/backend/.data/playbook/playbook-2026-06-22-b698c3871e62.json`,
the first real-universe compute under the new tuple): every fired base sits near the cap —
`base_range_mbr` 1.8445 (ABT), 1.588 (BA), 1.9345 (CAT), 1.2421 (JPM), 1.4722 (PM) — with
`base_bars` up to 9. This follows the spec (§3.3 defines the base AS `consolidation_range`), so it
is not a defect; it is a sensitivity the back-scan (J-07) must characterise before firing counts
are interpreted. One inaccuracy rides along: that function's docstring claims "any window wide
enough to swallow part of the jump leg fails `consolidation_range`'s own `max_range` gate" — false
in general; only a window swallowing **more than 2.0 MBR** of it fails, which is precisely why the
base widens as observed.

**B3 — GAP (constants-level, owner ruling, not fixed): spec §3.3's BOOK ratio gate is inert as pre-registered**
`desk_playbook_detect.py:416` implements both jump gates exactly as specified:
`jump < jump_min_mult * base_range or jump < jump_min_move_mbr * mbr`. But with
`PLAYBOOK_BASE_MAX_RANGE_MBR = 2.0` and `PLAYBOOK_JUMP_MIN_MOVE_MBR = 3.0`
(`desk_playbook.py:111`, `:107`), any base range is ≤ 2.0·MBR, so `1.5 × base_range ≤ 3.0·MBR ≤`
any jump that clears the ADAPTATION floor. **The BOOK's own 1.5× jump-to-base ratio can therefore
never reject a formation on its own** — the floor always rejects first. This is not a code defect
(both gates are implemented verbatim) and not something an auditor may fix: a constant change is a
spec revision plus a new signature by this era's own anti-goal. It is recorded because TC-4's
literal wording ("jump < `PLAYBOOK_JUMP_MIN_MULT`× base range") describes a condition that cannot
occur in isolation, and because J-07 will otherwise attribute firing frequency to a gate that never
bound.

**B4 — OBSERVATION (not fixed): `handle_retrace_frac` can go negative**
`desk_playbook_detect.py:767` computes `(right_rim_price − handle_bottom) / depth`. When every
handle bar trades above the right rim (possible when the LEFT rim is the higher one, so
`T = max(left, right)` is not yet broken), the value is negative while the data contract advertises
`0..PLAYBOOK_HANDLE_MAX_RETRACE_FRAC`. Harmless direction — the gate is a `≤` and a negative
retrace is a genuinely shallower handle — and the rendered line shows the served number verbatim.

**B5 — OBSERVATION (accepted design, already disclosed): the three new detectors ride the OR-break absence gate**
`desk_playbook.py:566-578` — a member with 5m bars but no buildable opening range is skipped for
`jbe`/`dbi`/`cup_handle` too, though spec §3.1 scopes that absence to the OR-break family. Dev
flagged it for an owner ruling and the reviewer logged it; the audit adds the missing quantity: on
the real 2026-06-22 record only **2 absences across the whole universe walk**, so the conservative
coupling costs almost nothing today. Revisit with J-07, as dev proposed.

### Frontend Findings

**F1 — IMPORTANT (fixed): a `dbi` signal's base shape was labelled "ascending" when the detector measured the opposite**
`_base_lows_ascending` (`desk_playbook_detect.py:355-364`) deliberately carries **two different
measurements under one served field name** (the goal's own data-contract name): non-decreasing
LOWS for `jbe` (ascending-triangle base) and non-increasing HIGHS for `dbi` (the mirrored
descending-triangle base). The UI rendered one unconditional string for both
(`apps/frontend/app/desk/page.tsx:4604`, pre-fix: `{geometry.base_lows_ascending && " · ascending
base"}`), so a **short** setup's row read "· ascending base". This is not hypothetical: the QA
screenshot `reports/qa/goal-playbook-iter-4-evidence/UT-03-result.png` shows the DBI1 row reading
"base 0.80 MBR wide (3 bars) · jump 6.00 MBR · broke at slot 9 · flatline base · ascending base",
and the operator's real store already holds a `dbi` signal with `base_lows_ascending: true` (PM,
2026-06-22) that would render the same way. An operator reading a Drop-Base Implosion would be told
the opposite of the measured geometry — a misleading-UI defect on the exact surface this iteration
exists to make legible.
*Fix applied:* the label now branches on `setup_id` — `jbe` reads "ascending base", `dbi` reads
"descending base" — a label selection only, no client-side arithmetic, no served-field change
(`page.tsx:4603-4612`). Guarded by a new source-scan test plus its seeded counter-test in
`apps/backend/tests/test_desk_ui_guards.py` (`test_desk_page_labels_the_dbi_base_shape_as_
descending_not_ascending`, `test_dbi_base_shape_label_guard_can_fail_on_a_seeded_violation`).
*Verification:* `pytest tests/test_desk_ui_guards.py tests/test_copy_discipline.py -q` → 64 passed
(the counter-test proves the pre-fix shape is caught); `npx tsc --noEmit` → exit 0.

### Test Findings

**T1 — IMPORTANT (fixed): the TC-4 / TC-5 near-miss tests passed for the wrong reason — the jump gate was never reached**
`test_jbe_near_miss_jump_too_small_fires_no_signal` / `test_dbi_near_miss_mirrors_the_jbe_near_miss`
(`apps/backend/tests/test_desk_playbook_detect.py`, pre-fix :473 and :496) asserted `results == []`
and documented the cause as "the jump fails BOTH the `jump_min_mult` and `jump_min_move_mbr`
gates". It did not. Because the fixtures' lookback leg sat within `base_max_range_mbr` of the base,
`consolidation_range`'s maximal window swallowed the whole leg back to bar 0, so **every** candidate
trigger was rejected earlier, at `start_idx - jump_lookback_bars < 0`. Proof (audit probe, gate
isolation): re-running the ORIGINAL fixtures with `jump_min_mult` and `jump_min_move_mbr` both set
to `0.0` still produced **0 signals** for jbe and 0 for dbi — a test that cannot distinguish a
working jump gate from a deleted one. The goal's own J-04 acceptance says near-misses must be
*provably* silent; they were silent, but not provably so.
*Fix applied:* both fixtures rebuilt so the lookback leg sits far enough below/above the base that
the maximal window stops at the base's own first bar, the formation reaches the jump gate with a
hand-computed 2.4-MBR jump (under the 3.0-MBR floor), and every other gate passes. Each test now
also runs the identical bars with **only** the two jump gates relaxed and asserts exactly one
signal fires at slot 9 with `jump_mbr == 2.4 < jump_min_move_mbr` — so the gate is provably the
decisive rejecter and a future regression cannot re-hide behind an earlier one.
*Verification:* `pytest tests/test_desk_playbook_detect.py -q` → 23 passed; the pre-fix
gate-isolation probe now returns 0 signals as-is and 1 signal (slot 9, `jump_mbr` 2.4) with the
gates relaxed, for both jbe and dbi.

**T2 — OBSERVATION (not fixed): the cup-and-handle fixture carries impossible bars**
`_canonical_cup_handle_bars` (`test_desk_playbook_detect.py`) contains bars whose `high` is below
their `open` (e.g. slots 4-9 and every handle bar: `(109.6, 109.3, 108.0, 108.5)`), which no real
OHLC bar can be. Re-deriving the rim/depth/handle gates with realistic highs does not change any
assertion (the rims and the trigger threshold dominate), so the goldens stand — but fixture realism
is weaker evidence than it looks, and the same shortcut in a future detector could mask a real gate.

**T3 — OBSERVATION (not fixed): one new guard test is scheduled to fail by construction**
`test_desk_playbook_evidence_module_does_not_exist_yet`
(`apps/backend/tests/test_desk_playbook_guards.py:198`) asserts `desk_playbook_evidence.py` does
not exist. That is true and useful today, but J-08 creates that module — this test will fail on the
iteration that ships the evidence view and must be flipped there. The import-graph guard itself
(TC-13) is correctly written to survive.

### Process / Definition-of-Done Findings

**P1 — GAP (not fixed): TC-17's clean-rebuild half was skipped**
The browser lane records (`reports/phase-goal-playbook-iter-4-ui-test-results.md`, UT-08) that
`rm -rf .next` + rebuild + restart "was intentionally skipped (would corrupt the pinned dev
server)". The rest of TC-17 was done properly — every shipped `/desk` section walked, lower
sections captured via the sibling-collapse technique
(`reports/qa/goal-playbook-iter-4-evidence/UT-08-lower-sections.png`), zero testid/heading
collisions against the stored `goal-session-desk` golden scripts. The discipline's *purpose* is met by other
evidence: UT-02/03/04 show this iteration's brand-new render branches served live, so the bundle
was not stale. Recorded as a gap, not a blocker.

**P2 — OBSERVATION: a golden regression script was edited in the same cycle it flagged a failure**
`runs/goal-session-playbook/journey-scripts/J-10.json` moved `default_timeout_ms` 15000 → 20000.
The diff is timeout-only — every step and every `expect` is byte-identical (verified by `git diff`)
— and the deterministic replay's J-10 step-5 failure ("300.11" did not appear,
`reports/phase-goal-playbook-iter-4-regression-replay-results.md`) did not reproduce in either the
live Chrome MCP walk (`UT-J-10-result.png`) or an independent `demo_runner.py --mode verify`. So the
bump is flake mitigation, not goalpost-moving. Flagged for the same visibility the era-5D inert
timeout bump got.

**P3 — OBSERVATION: a real (non-fixture) record was appended to the operator's store during the browser lane**
`apps/backend/.data/playbook/playbook-2026-06-22-b698c3871e62.json` (recorded_at
`2026-08-11T00:27:33Z`) holds a genuine real-universe compute under the new 5-setup signature — 5
signals across ABT/BA/CAT/JPM/PM, 2 absences, 0 diagnostics. The phase spec listed real computes as
out of scope, but this one is honest and harmless (append-only, correctly re-keyed, real symbols)
and it is in fact the strongest available evidence that the new detectors behave sanely outside
their fixtures. It also **supersedes two claims on file** — the dev handoff's "this iteration never
computed over the real recorded universe" and the browser lane's "the three new families have not
fired on any real recorded session yet": they had, within the same hour, and the result looks sane.
TC-18's own target is clean: `playbook-2026-08-04-e0f249f57785.json` is gone and **no
fixture-symbol record (LADDER/DBI1/CUP1) exists anywhere in the real store** — the fixture rig ran
against a second uvicorn with `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DESK_UNIVERSE_DIR`/
`TAPEOLOGY_DESK_PLAYBOOK_DIR`/`_LOG_DIR`/`_BACKSCAN_LOG_DIR` all pointed at
`$TMPDIR/playbook-fixture-rig/` (`reports/phase-goal-playbook-iter-4-ui-test-results.llm.md:20-43`),
exactly the scoping the carried item demanded.

**P4 — OBSERVATION: the QA report's PASS was issued with browser checks skipped**
`reports/qa/goal-playbook-iter-4-qa.md` records "Browser Checks: SKIPPED" after its own
`npm run build` broke the running dev server (`Cannot find module './885.js'`). The DoD's browser
requirement is nonetheless met — by the separate browser-qa lane (15/15 with screenshots), not by
the QA report. Worth noting because a reader of the QA report alone would conclude J-04's
TC-1/TC-2/TC-3 were unverified.

---

## 3. Domain Assessment

**Detection logic vs. the pre-registered spec — traced, not trusted.** Every gate in
`_find_one_continuation` maps to spec §3.3 in order: base via `consolidation_range` ending at
`t−1`; `jump = U − min low of the PLAYBOOK_JUMP_LOOKBACK_BARS bars before base start`; both jump
gates; near-the-high at `t−1` (`session_bars[:t]`, not the whole session); jump-bar RVOL median
≥ 1.0 with max ≥ `RVOL_ELEVATED`; base-bar RVOL median ≤ `VOL_CONTRAST_RATIO` × jump median;
trigger `high > U`; invalidation `L − 0.30·(U − L)`; ladder cap 2 with the second base forced to
start after the first trigger bar (`min_base_start = slots_to_break + 1`). `dbi` is the same walk
with `side="short"`, not a hand-flipped copy — the right call, and the one that makes the mirror
claim checkable. `detect_cup_handle` matches §3.6 including the subtle part: the trigger scan
starts at `max(handle_start + 1, right["confirmed_at"] + 1)`, so a rim is never used before its own
pivot is knowable. That was a genuine lookahead bug the developer found and fixed mid-build; the
audit re-derived the boundary independently and it holds.

**Lookahead discipline** survives the reuse of shared primitives: every gating read is bounded by
the trigger bar, the only post-trigger fact served is `bars_to_close` (a disclosure, exactly as
J-01 shipped), and the truncate/mutate property harness now covers all three new detectors.

**Measurement, seeding, and the store** are untouched rails: `_measure_signal` anchors on
`geometry.slots_to_break` (which is why `types.ts` keeps that one field required), the
seed-collision discriminator genuinely increments across ladder firings, and TC-8's real
`BarStore`-backed two-firing test asserts two distinct anchors plus byte-identical re-compute.
`git diff` is empty against `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`,
`levels.py`, `config.py`, `mcp/__init__.py` and `desk_playbook_features.py`;
`Config().config_fingerprint()` prints `08e471b10130e1e2`.

**Honesty of the served surface.** No advice, probability or expectancy language enters the new
lines (copy-discipline scan green), the new numerics are rendered verbatim (the arithmetic guard
was extended and its counter-test genuinely catches each new binding), absence and refusal states
are unchanged, and — after F1 — every geometry word now names the measurement actually taken.

**Where the confidence stops.** The detectors are proven on fixtures plus one real session. Whether
their firing frequency and geometry distribution hold up on the recorded universe is unknown until
J-07, and findings B2/B3 are the two things that back-scan should be pointed at first.

### Definition-of-Done verification (risk-ranked)

| DoD item | How verified | Result |
|---|---|---|
| J-04 passes via browser-qa — one JBE, one DBI, one cup-and-handle legible with geometry (TC-1/2/3) | **Full trace** (new detection math): spec §3.3/3.4/3.6 walked against `desk_playbook_detect.py:367-793`; screenshots opened directly — `UT-04-result.png` (all 5 setup chips in one table + the cup detail line), `UT-03-result.png` (DBI chip/side/geometry) | MET (and F1 raised from reading them) |
| J-01/J-02/J-03 unchanged, recorded files byte-identical (TC-9/TC-11) | **Full trace** (data persistence): `compute_playbook` pooling/seeding diff read line by line — new setups use disjoint pool keys, OR-break path untouched; `test_j04_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file` asserts SHA-256 of the pre-J-04 file unchanged and OR-signal content equal | MET |
| J-10 still ≥ partial, browser-verified, lower sections re-taken | Reviewer PASS + browser row UT-J-10 (live walk, screenshot) + UT-08 lower-section capture; the replay lane's contradicting FAIL was chased down (P2) rather than accepted | MET, with P1/P2 gaps |
| No anti-goal violation (TC-7/8/10/12/13/14/15) | **Full trace** of the lookahead and seed paths (§3 above); guards read in full (`test_desk_playbook_guards.py`) — both carry counter-tests; TC-14's duplicate-key test is untouched and the store write path has zero diff | MET |
| Suite ≥ 2036/8, fingerprint `08e471b10130e1e2`, zero new `Config` fields, zero diff to the protected modules (TC-16) | Re-run by the audit, not accepted from the handoff: `git diff` on the eight protected paths → empty; fingerprint printed → `08e471b10130e1e2`; full suite re-run post-fix (§4) | MET |
| Three carried items closed (TC-17/18/19) | Store listing inspected directly (stray file gone, no fixture-symbol record); spec §0 provenance paragraph read in the diff; screenshots present | TC-18/TC-19 MET, TC-17 partial (P1) |
| Dev handoff written | Present at `docs/handoffs/goal-playbook-iter-4-dev.md`, and honest about its own limits (no browser pass, fixture-scope only) | MET |

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/desk/page.tsx` | Base-shape label now branches on `setup_id`: `jbe` → "ascending base" (its lows), `dbi` → "descending base" (its highs). Label selection only — no arithmetic, no served-field change. |
| 2 | Important | `apps/backend/tests/test_desk_ui_guards.py` | New source-scan guard + seeded counter-test locking that both direction labels exist and are selected by `setup_id`. |
| 3 | Important | `apps/backend/tests/test_desk_playbook_detect.py` | TC-4/TC-5 near-miss fixtures rebuilt so the jump gate is genuinely reached and is the decisive rejecter; each test now carries a gate-relaxed control asserting exactly one signal fires at slot 9 with `jump_mbr` 2.4 < the 3.0-MBR floor. |

Post-fix verification (commands run, results cited):
- `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_ui_guards.py tests/test_copy_discipline.py -q` → **64 passed**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_playbook_detect.py -q` → **23 passed**
- `cd apps/frontend && npx tsc --noEmit` → **exit 0, no errors**
- Full suite re-run by the audit after the fixes:
  `cd apps/backend && .venv/bin/python -m pytest tests/ -o addopts="" -q` →
  **2061 passed, 8 skipped in 155.42s** (pre-audit was 2059/8; +2 = the new label guard and its
  counter-test — the rebuilt near-miss fixtures replaced tests in place. Floor was ≥ 2036 / 8.)
- `git diff` on the three touched files re-read: the audit's own changes are confined to the label
  branch + its comment, the two new guard tests, and the two rebuilt fixtures — nothing else.
- Dev-handoff claims invalidated by these fixes: none of substance, but the handoff's frontend
  description ("an 'ascending base' note") and the browser lane's UT-03 transcript now describe the
  pre-fix string; the `dbi` row reads "· descending base" from this commit on.

---

## 5. Recommended Next Step

Proceed to the next journey (J-05, the climax family) — J-04 is delivered end to end and the two
IMPORTANT defects are closed with tests. Carry three items forward rather than fixing them
speculatively:

1. **Owner ruling on B3** (spec §3.3's 1.5× BOOK ratio gate can never reject alone under
   `BASE_MAX_RANGE_MBR = 2.0` / `JUMP_MIN_MOVE_MBR = 3.0`) and on **B1** (the rim gate's constant).
   Both are spec-side decisions, both are cheap now and expensive after J-07 has interpreted firing
   counts.
2. **Point J-07's back-scan at B2 first** — characterise how often the maximal-window base widens
   into the jump leg and what that does to jbe/dbi frequency, before any conclusion is drawn from
   the counts. The one real record already on disk (5 signals, all bases near the 2.0-MBR cap) is
   the seed observation.
3. **Restore the clean-rebuild half of T-9 (P1)** in the next browser pass, and flip T3's
   "evidence module does not exist" test when J-08 lands.
