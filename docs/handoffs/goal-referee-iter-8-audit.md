# goal-referee-iter-8 Audit Report

**Date:** 2026-08-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-07 is genuinely achieved: the Referee Registry section renders the five spec-pinned candidates
with live readiness and rationale, and a real select → confirm → write registration completed in a
browser against the fixture-scoped rig, producing a boundary-stamped hypothesis row with its
`discovery (exploratory)` numbers rendered distinctly from `accrual`
(`reports/qa/goal-referee-iter-8-evidence/UT-06-result.png`, read directly — not taken on report).
Two IMPORTANT findings were found by tracing the unhappy paths behind the handoff's claims and were
fixed during this audit, each with a regression test and a can-fail companion: Rider 1 gated only
one of the **two** sites that write a hypothesis's one permanent snapshot (B1), and the shortlist's
`projected_days_to_target` counted pre-boundary history toward a post-boundary target, serving
"0 days — ready now" for all three estimand-A candidates against the operator's real corpus where
the honest waits are ~74 / ~119 / ~50 days (B2). Remaining items are gaps, not defects: the starter
family's BH `q` lives as a browser literal, and J-01–J-06's browser re-checks were shed by the
wall-clock trim.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): Rider 1 gated only one of the two snapshot-write sites**
`apps/backend/app/research/referee_adjudicate.py:1016-1027` (the dedup / self-heal branch) is the
**second** site that writes a hypothesis's ONE permanent adjudication snapshot. Rider 1 (the
iteration's own deliverable) added its gate only at the fresh-compute site (line ~1160), and the
dev handoff's claim — "so the hypothesis's one permanent adjudication snapshot is never minted from
an unattested evaluation" — was therefore false for this branch, which called
`_build_and_record_snapshot(existing, ...)` with **no attestation check of any kind**.

Confirmed by direct probe, not by reading: plant the attested checkpoint fixture; delete the
snapshot file (this branch's own documented "the snapshot write did not complete" scenario); bump
`referee_stats.STATS_CORE_VERSION` so the recorded attestation is version-stale — the exact state
the era's anti-goal names ("missing, mismatched, or version-stale"). Re-running the evaluation
printed:

```
PROBE role: checkpoint
PROBE snapshot minted: True
PROBE snapshot verdict: corroborated
PROBE snapshot attestation re-verifies: False
PROBE read-side fold verdict: insufficient_sample refused: True
```

No confirmatory output leaks (the read fold refuses, as designed), but the hypothesis's single,
immutable checkpoint is permanently spent on a `corroborated` record that can never be served — and
no later, genuinely attested evaluation can replace it, because `checkpoint_exists` is then true and
every subsequent role folds to `monitoring`.

*Fix applied:* the branch now writes only when the existing record's attestation both carries
`passed is True` **and** re-derives through `verify_oracle_attestation` (the read side's own gate,
never the stored flag, T-8). When it does not verify, nothing is written and the fold serves its
honest live pre-checkpoint state. The `elif` read-back of an already-existing snapshot is untouched.

**B2 — IMPORTANT (fixed): `projected_days_to_target` counted pre-boundary history toward a
post-boundary target**
`apps/backend/app/research/referee_registry.py:1118` served
`max(0.0, (target_sessions - n_sessions) / accrual_rate)`. But `target_sessions` is a POST-boundary
count everywhere else it is used (`_hypothesis_accrual`'s `informative_post_boundary_sessions`;
`run_evaluation_and_record`'s `confirmatory_eligible`, `referee_adjudicate.py:1034-1037`), and
registration stamps the boundary at that instant — so not one of the historical sessions in
`n_sessions` can ever count toward it. Measured against the operator's own corpus (210 records,
span 2025-06-03 → 2026-08-13 = 437 days), the served value was:

| candidate | n | n_sessions | rate/day | served `projected_days` | honest post-boundary |
|---|---|---|---|---|---|
| S-1 capitulation:long | 473 | 71 | 0.1625 | **0.0** → UI "0" | 73.9 |
| S-2 jbe:long | 164 | 44 | 0.1007 | **0.0** → UI "0" | 119.2 |
| S-3 double_top:short | 771 | 105 | 0.2403 | **0.0** → UI "0" | 49.9 |

Every estimand-A candidate read "ready now" on the very screen whose purpose is to help the
operator choose which question to register (goal.md J-07 Step 3), for a wait of 50–119 days — and
it counted historical observations as progress toward a confirmatory target, which the era's
critical anti-goal ("the historical atlas is exploratory forever") forbids. The fixture rig hid it
(a one-session corpus renders 517, `UT-06-result.png`); only the real corpus exposes it.

*Fix applied:* `projected_days_to_target = target_sessions / accrual_rate`, measured from zero; the
`None`-on-zero-rate divide-by-zero guard (TC-2) is unchanged and the `max(0.0, …)` floor is gone
with the subtraction. Post-fix real-corpus serving: S-1 → 74, S-2 → 119, S-3 → 50, S-4/S-5 → `—`.
The interpretation call is re-logged in `runs/goal-session-referee/state/assumptions.md` (iter-8
auditor entry) and the stale sentence in the dev handoff is corrected in place.

**B3 — GAP: the shortlist is the module's most expensive GET, and breaks its own single-scan
discipline**
`shortlist_response` (`referee_registry.py:1084-1090`) calls `playbook_occurrence_readiness()`
(which lists the store) and then `playbook_store.list()` again — two full scans, 0.44 s each
measured on the operator's real 210-record store — and constructs a `BandMapResolver`
unconditionally (its `__init__` runs `bar_store.list()`), even when no `range_trade:long` signal
exists. On the real corpus S-4/S-5 then resolve 469 distinct `(symbol, session_date)` band-map
lookups (measured). It stays honest and never computes (`compute=False`, T-8) and it is paid once
per page load (`sectionReadIssuedRef`, `page.tsx:7745`), so no loop or repeated cost is exposed —
but the module docstring's own claim that it "scans the store exactly ONCE per call" is not true of
the new fold. Not fixed: reworking the scan structure is beyond a surgical audit fix.

**B4 — OBSERVATION: the fresh-path Rider-1 gate trusts the stored `passed` flag**
`referee_adjudicate.py:1160` reads `fields["attestation"]["passed"]` while the read side pointedly
"never trusts a stored `passed` flag". At the fresh-compute site the two are equivalent by
construction (`run_oracle_attestation` computes `passed` via `verify_oracle_attestation` on the same
record), and the shipped Rider-1 test deliberately depends on the stored flag (its fixture flips
`passed` on an otherwise genuine attestation, which `verify_oracle_attestation` would re-derive as
True). Left as-is deliberately; noted so a future hardening pass does not "fix" it and silently
break that test's intent.

**B5 — OBSERVATION: two timestamp choices for one conceptual band-map lookup**
`_starter_context_readiness` resolves at `signal["trigger_ts"]` (`referee_registry.py:1046`);
`referee_adjudicate._pool_cell_vs_complement` resolves the same concept at the observation's
`anchor_ts` (`referee_adjudicate.py:407-409`). I verified `BandMapResolver` keys on
`(symbol, basis_day)` (`desk_playbook_context.py:603-617`), so both land on the same map for a
same-session anchor and the readiness number cannot disagree with the evaluation's pooling today.
Recorded only because the equivalence is incidental, not enforced.

### Frontend Findings

**F1 — GAP: the starter family's BH `q` — immutable once registered — is a browser literal**
`apps/frontend/app/desk/page.tsx:361` pins `REFEREE_STARTER_FAMILY_Q = 0.1` (and
`REFEREE_STARTER_FAMILY_ID`) and `handleRegisterRefereeCandidate` sends it in the registration
payload. `REFEREE_DEFAULT_Q` exists **only** in prose (`docs/referee-statistical-spec.md:50`) —
there is no backend module constant, the shortlist response carries no family framing, the
blueprint's iter-8 contract note does not register one, and no test ties the browser value to the
spec value. Server-side validation is only `0 < q <= 1` (`referee_registry.py:640`).

Nothing is wrong today: `0.1 == 0.10`, `family_candidate_hypothesis_ids` is read live off the
fetched shortlist so the BH denominator is the full `m = 5` (verified in code and in UT-06's real
write), and `_validate_family_consistency` freezes `q` against the recorded family from the second
registration onward. The gap is ownership: the single value that fixes a family's error rate
forever now lives in the file least likely to be reviewed as a statistics change. Remedy for a
later iteration (it would be a data-contract addition, outside this iteration's registered shape):
pin `REFEREE_DEFAULT_Q` in `referee_registry.py`, serve `family_id`/`family_q` on the shortlist, and
have the client read them verbatim.

**F2 — OBSERVATION: readiness numbers render without their basis**
"Accrual / day" and "Projected days" render bare (`page.tsx:4780-4789`); their formula (a
whole-corpus calendar-span denominator) is disclosed only in `state/assumptions.md`, and the
registry fold's own `accrual.is_proxy: true` flag is served but never rendered. Honest, but the
operator cannot see that these are proxies.

### Test Findings

**T1 — GAP: J-01–J-06 were not re-verified, though DoD asked for them "mechanically verified"**
`reports/phase-goal-referee-iter-8-ui-test-results.md:43-51` carries six `DEFERRED-BUDGET` rows
(SPEED-15 trim rung 2). Compensating evidence, which I checked rather than assumed: those journeys
are keyless backend machinery whose regression surface is the unit suite (2,657 collected, 0 failed,
re-run by me post-fix), and J-10 — the kept-product sentinel, the one journey with a golden — did
replay green (`reports/phase-goal-referee-iter-8-regression-replay-results.md`, evidence
`J-10-verify.png`). Real but low-risk; re-queue rather than block.

**T2 — OBSERVATION: the guard extension misses the newly-rendered `hyp.accrual.*` pair**
The reviewer's own MINOR (`reports/reviews/goal-referee-iter-8-review.md:20-34`): the registered
table renders `hyp.accrual.informative_post_boundary_sessions / hyp.accrual.target_sessions` in the
identical "X / Y" idiom as the now-guarded discovery pair, but only `candidate.*` and
`hyp.discovery.*` were added to `_PRICE_ARITHMETIC_FIELDS`. Accepted as-is (no client-side
arithmetic exists today); not fixed here — it is the reviewer's already-filed fix task.

**T3 — OBSERVATION: the QA report understates its own iteration's evidence**
`reports/qa/goal-referee-iter-8-qa.md:115-125` describes the registration flow as select → confirm
→ **cancel** and lists "Submit registration" without evidence; its shortlist table is garbled
("Projected 25/17"). Had that been the authoritative artifact, DoD's TC-4/TC-5 would be unproven.
The real evidence is the merged browser-QA file plus the screenshots (UT-06/UT-07), which I opened
directly. Flagged so the evaluator reads the merged file, not the QA summary, for J-07.

---

## 3. Domain Assessment

The statistical machinery this iteration touches is, apart from B2, sound and defended in the right
places:

- **Boundary integrity.** `POST /registry/hypotheses`'s request model deliberately omits
  `registered_at` (`referee_routes.py:299-307`), so the registration instant — and therefore the
  boundary — is always server-stamped, and `_resolve_boundary` refuses an explicit boundary at or
  before the honest one. The new UI cannot reach either seam: it sends only candidate fields plus
  family framing. The iter-6 hardening this iteration depends on is real, not assumed.
- **Discovery vs accrual is an exact partition.** `_hypothesis_discovery` keeps
  `session_date <= boundary`; `_hypothesis_accrual` keeps `session_date > boundary`; both walk the
  same single `newest_by_date` scan with the same stale-basis exclusion, and both key on
  `session_date`, never `recorded_at` — so a deep-backfilled pre-boundary record lands in discovery
  forever (TC-10 asserts both sides of the split, including the on-boundary edge). Discovery never
  feeds accrual, and the label ships from the backend.
- **The write path stayed generic.** TC-9 registers `dbi:short` — outside S-1..S-5 — through the
  real route; the five candidates are read-side constants only. No special-casing entered the POST.
- **BH denominator untouched.** `m` comes from the full served candidate list; nothing in this
  iteration touches the family fold.
- **The one leak of history into a confirmatory quantity was B2**, and it was in exactly the place
  the era's lesson set predicts: not in the guarded field (`accrual`), but in a sibling number that
  reached the same target another way.

Test quality is genuinely good and above this repo's average: tight equality assertions (not
range checks), can-fail companions beside each new gate, a non-vacuous discrimination test for the
`at_wall` resolve (3 at_wall / 1 off_wall, sessions deduped), and seeded counter-tests proving the
extended UI guard fires on each new field without over-matching the real "X / Y" idiom. The one
test that encoded a wrong semantic (`…projected_days_to_target_is_zero_when_already_at_or_above_target`)
was replaced rather than deleted.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/referee_adjudicate.py` | Gate the dedup/self-heal snapshot write on `verify_oracle_attestation` (+ the stored `passed` flag) — the second write site Rider 1 missed (B1) |
| 2 | Important | `apps/backend/tests/test_referee_adjudicate.py` | New `…audit_b1_the_self_heal_branch_never_mints_a_snapshot_from_a_stale_attestation` (version-stale attestation → nothing written, read fold stays honest) plus its can-fail companion proving an *attested* interrupted write still self-heals; imports `verify_oracle_attestation`/`referee_stats_module` |
| 3 | Important | `apps/backend/app/research/referee_registry.py` | `projected_days_to_target = target_sessions / accrual_rate` — measured from zero, never net of pre-boundary history (B2); docstring states why |
| 4 | Important | `apps/backend/tests/test_referee_registry.py` | Replaced the test that pinned the old net-of-history semantic with one asserting the projection is measured from zero and is never `0.0` on historical evidence alone |
| 5 | — | `runs/goal-session-referee/state/assumptions.md` | New iter-8 **auditor** entry superseding the developer's `projected_days_to_target` call, with the measured real-corpus numbers |
| 6 | — | `docs/handoffs/goal-referee-iter-8-dev.md` | Corrected the now-false "floors at `0.0`" claim in place, pointing at B2 |

**Verification of the fixes (commands run, results cited):**

- `cd apps/backend && .venv/bin/python -m pytest tests/test_referee_adjudicate.py -p no:cacheprovider --junit-xml=…`
  → **46 passed, 0 failed, 0 errors**; both new B1 tests named and passing in the JUnit XML.
- `… -m pytest tests/test_referee_registry.py …` → **44 passed, 0 failed, 0 errors**.
- Full suite, post-fix: `… -m pytest tests/ -p no:cacheprovider --junit-xml=…` → exit 0,
  **collected 2657, failures 0, errors 0, skipped 8**, 256.6 s (≥ the 2,642 DoD floor; +2 over the
  handoff's 2,655 = my two new tests).
- `Config().config_fingerprint()` → **`08e471b10130e1e2`** (unchanged, run by me).
- `test_mcp_server.py::EXPECTED_TOOLS` → **20 entries** (unchanged, counted by me).
- Real-corpus re-serve of `shortlist_response` after fix 3 (band resolver stubbed so nothing touched
  the operator's protected `.data/bars`): S-1 74 / S-2 119 / S-3 50 / S-4 `—` / S-5 `—`.
- `git diff` re-read: the changes touch only the two findings' code paths, their tests, and the two
  documentation records — no incidental edits.
- Nothing was written to the operator's real registry store: the shortlist/registry probes were
  read-only and the temporary probe test ran against pytest `tmp_path` stores only (probe file
  deleted).

**DoD trace.** Risk-class items (the permanent write path, the boundary, the attestation gate, the
discovery/accrual split) were traced in full through the code — B1 and B2 came out of that trace.
Mechanical items are accepted on the reviewer's PASS plus an executed browser row, cited: shortlist
renders with readiness + rationale → review `spec_alignment: complete` + UT-02/UT-03; registration
flows to a recorded row with boundary/target/origin → UT-06 (+ screenshot read directly); discovery
label distinct from accrual → UT-07 (+ same screenshot); kept product intact → UT-10 + the J-10
golden replay; suite/fingerprint/MCP-count → re-run by me above. The DoD line "no anti-goal
violation introduced" was **partially breached at handoff** (B2 counted historical observations
toward a confirmatory target) and is satisfied after fix 3.

---

## 5. Recommended Next Step

Proceed to J-08. J-07's goal is met and the two write-side riders are now genuinely complete on both
of their write sites. Carry forward, in priority order:

1. **F1** — give `REFEREE_DEFAULT_Q` a backend home and serve the starter family's `family_id`/`q`
   on the shortlist, so the browser stops owning an irreversible statistical parameter. Natural to
   fold into J-08, which is where family/promotion mechanics get their next real work.
2. **T2** — the reviewer's `hyp.accrual.*` guard extension (one regex clause + a seeded
   counter-test).
3. **T1** — re-queue the J-01–J-06 browser re-checks in the next iteration that has budget.
4. **B3/F2** — if the shortlist's first-expand latency is ever felt on the real corpus, collapse the
   double store scan and defer the `BandMapResolver` construction to the first context candidate;
   and consider rendering the served `is_proxy` flag beside the readiness columns.

Before the operator performs the real J-07 Step 3 registration against the production store, note
that the shortlist's `Projected days` column now reads 74 / 119 / 50 rather than 0 — that is the
honest post-boundary wait, and it is the number the choice of 2–3 hypotheses should be made on.
