# goal-rapid-microscope-iter-2 Audit Report

**Date:** 2026-08-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-02's goal is genuinely achieved: the observer seam is additive and the engine is byte-untouched,
the three new modules ship real (not stubbed) machinery, and 18/18 real legacy datasets carry
identity-verified snapshots I re-verified myself against the operator's store — 3,815,933 rows,
row count matching `trades + 1` for every single dataset. J-01's last open half is closed with a
real screenshot whose every value matches the served API body. But the persisted corpus carried
**two honesty defects the review and QA both passed over** — a deferred construct the session cut
short was recorded as a *completed* observation, and a mid-stream observer exception would have
been persisted as a silently truncated snapshot that still identity-verified as complete. Both are
fixed, corpus rebuilt, and proven with before/after whole-corpus sweeps. Remaining gaps are
documented, not fixed: the J-10 sentinel did **not** literally pass its browser lane this iteration
(and the QA report claims it did), and two spec §3/§4 sub-clauses are unimplemented and
undisclosed.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): a depletion window the session cut short was recorded as a COMPLETED
observation, not `unavailable`**
`apps/backend/app/research/micro_observer.py:747` (the `finalize()` sweep) → `:657`
(`_resolve_depletion`).

Spec §0's availability law is explicit — a deferred construct "is `unavailable` (counted, never
guessed) when the session ends first" — and §3 says quote depletion "ends at a price change or the
bound". `finalize()` called `_resolve_depletion` unconditionally, which always stamped
`unavailable: False`, so a run that hit *neither* terminator was published as a closed window.

Verified by execution before the fix (a stream whose ask price never changes and never reaches
`DEPLETION_WINDOW_QUOTES`):

```
quote_size_unit="shares"      -> {'kind':'quote_depletion','value':400,'unavailable':False,'refused':False}
quote_size_unit="unverified"  -> {'kind':'quote_depletion','value':None,'unavailable':False,'refused':True}
```

Both are false claims about a window that never closed; under a verified unit it is worse — a
fabricated magnitude (400) for an unfinished observation. The sibling constructs
(`response_asymmetry`, `refill_consistent`) were already swept correctly in the very same
`finalize()`, so depletion was the lone outlier. The shipped 18-dataset corpus embedded exactly 36
of these (2 per dataset — the bid and ask runs open at session end). No test covered the case.

**Fix applied.** `finalize()` now sweeps an open run through
`_resolve_depletion(..., unavailable_at=ts)` → `value: None`, `unavailable: True`, `refused: False`
(a refusal asserts "the window closed and its magnitude is not reportable" — itself a false claim
here). Routed through the *same* emitter rather than a new one so the TR-18 streaming source scan
(`tests/test_micro_features.py:355`) keeps guarding it un-muzzled.

**Evidence after the fix** — corpus rebuilt through the shipped CLI, then every row of all 18 files
swept (42.7s):

| | before (dev's sweep) | after |
|---|---:|---:|
| `quote_depletion` completions | 1,824,729 | 1,824,729 |
| …refused (window closed, magnitude withheld) | 1,824,729 | 1,824,693 |
| …`unavailable: True` / `value: None` (session cut short) | 0 | **36** (2 × 18 datasets) |
| …serving a raw magnitude | 0 | 0 |
| rows / bytes on disk | 3,815,933 / 6,378.8 MB | 3,815,933 / 6,378.8 MB (unchanged) |

Regression tests added: `test_quote_depletion_is_unavailable_when_the_session_ends_before_the_
window_closes` (parametrized over `shares`/`round_lots`/`unverified`) plus the counter-test
`test_quote_depletion_that_genuinely_closes_is_still_a_completed_observation`, and both real-fixture
TR-18 sweeps now separate "refused" from "unavailable" instead of conflating them.

---

**B2 — IMPORTANT (fixed): a mid-stream observer exception produced a silently TRUNCATED snapshot
that then identity-verified as complete**
`apps/backend/app/research/micro_snapshots.py:173` (`build_snapshot_rows`), against
`apps/backend/app/engine/tape_engine.py:144` (`_notify_event`).

The engine isolates observer exceptions **by design** (correct — a research observer must never
perturb engine output). The snapshot builder never asked whether the observer had failed, so a
raise anywhere mid-stream silently dropped that row *and every state update after it*, and the
short row set was written and served as a valid snapshot. Demonstrated on the pre-fix path
(observer raises on the last of 3 events):

```
engine snapshots yielded: 3 | observer rows: 1 | observer.failure: RuntimeError
PRE-FIX persisted row_count: 2 (dataset has 2 trades) -> identity-valid: True
```

Nothing raised, nothing was logged into the artifact, nothing refused. This is the silent-failure
class the era exists to eliminate, sitting under every downstream research claim.

**Fix applied.** `MicroObserver.on_event` (`micro_observer.py:360`) records `self.failure` and stops
consuming; `build_snapshot_rows` raises the typed `MicroObserverFailure` (`micro_observer.py:79`)
and writes nothing; the compute manager surfaces it as `state: "failed"` with the error verbatim and
appends a `failed` run to the durable log. The engine's own isolation is untouched — the new test
asserts all 3 snapshots still yield.

Regression tests added:
`test_a_mid_stream_observer_failure_refuses_the_build_instead_of_truncating_silently` (proves both
halves — the silent truncation *and* the refusal) and
`test_a_failed_build_surfaces_as_a_failed_run_never_a_silent_success`.

---

**B3 — IMPORTANT (fixed; I was unsure between GAP and IMPORTANT and chose the higher level):
`feature_source_hash` covered `micro_features.py` only, so an observer-only edit changed persisted
values while every stored identity still verified**
`apps/backend/app/research/micro_snapshots.py:98`.

The reviewer filed this as a NOTE (it matches §2.3's literal "sha256 over the feature-module
bytes") and the dev deferred it as latent. It is not latent: **this audit realized it.** B1's fix
changed 36 persisted completions across all 18 datasets, and every one of those 18 identities would
still have verified as valid — the corpus served as truth against code that no longer produces it.
The dev handoff's own Known Issues names the correct fix ("hash both module sources").

**Fix applied.** `feature_source_hash()` now digests the source bytes of both modules in a fixed
order (`_IDENTITY_SOURCE_MODULES`, `micro_snapshots.py:95`). Strictly more conservative than the
spec's literal wording — it can only ever convert a would-be HIT into an honest MISS, never the
reverse, which is the fail-closed direction §2.3 exists to guarantee. All 18 identities then missed
honestly and rebuilt through the shipped CLI (`python -m app.research.micro_snapshots --all`,
18/18, exit 0). Regression test:
`test_feature_source_hash_covers_the_observer_module_not_only_the_feature_module` (pins the module
tuple, proves the features-only digest is the *old* value, and that the two differ).

---

**B4 — GAP (not fixed — scope): two spec §3/§4 sub-clauses are unimplemented and undisclosed**

- §3 requires quote imbalance and microprice "both instantaneous at the in-effect NBBO **and as
  feature-window means**". Only the instantaneous forms exist (`micro_features.py:300`/`:307`,
  emitted per row at `micro_observer.py` `quote_imbalance`/`microprice`); no window-mean form.
- §4 requires "Quoted spread at the outcome start (bps) … served beside every outcome as the
  cost-proxy column — never netted into the outcome silently". `mid_outcome`
  (`micro_features.py:353`) and `last_trade_outcome` (`:382`) carry no spread column at all.

Neither is observable today — nothing serves outcomes this iteration, and the iteration's own IN
SCOPE lists the primitives without those qualifiers — so this is a gap, not a failure. But J-05's
walk-forward will inherit both omissions at the moment it starts serving outcomes, and the Known
Issues section does not mention them.

---

**B5 — GAP (not fixed — the spec is genuinely ambiguous; this needs an owner ruling, not an
invention): a price-change-terminated depletion stamps availability one quote earlier than the
evidence that ended it**
`apps/backend/app/research/micro_observer.py:636` → `:657`; locked in by
`tests/test_micro_observer.py:291` (`assert d["observed_through"] == 2.0  # the LAST update still at
the old price`).

§3 says depletion's "`available_at` = window end", and the window *ends at the price change* — i.e.
at the terminating quote's instant. §0 defines `observed_through` as "the last event consumed to
compute it", and the price-changing quote **is** consumed (it is what proves the run ended), even
though the magnitude itself needs only same-price quotes. The implementation takes the second,
narrower reading. The direction matters: it stamps availability *earlier* than the moment the
completion could be known, so a §4 consumer using the conditioning set's max `available_at` as an
outcome start would begin measuring marginally before the information existed. Sub-second in
magnitude, but it points the wrong way on the era's central no-lookahead rail. I did not change it:
the code's reading is defensible, the spec does not settle it, and inventing a ruling is exactly
what the execution plan forbids.

---

**B6 — OBSERVATION: `current_dataset_id` reports the last COMPLETED dataset, not the in-flight one**
`apps/backend/app/research/micro_snapshots.py:400` (`_publish` runs *after* each dataset finishes).
Harmless today (nothing renders it); J-08's progress UI will show a finished id under a
"current" label.

**B7 — OBSERVATION: the meta sidecar write is not atomic**
`apps/backend/app/research/micro_snapshots.py:198` (`Path.write_text`). A
`GET /research/desk/micro/snapshots` landing inside the sub-millisecond rewrite window could read a
partial file and surface `MicroSnapshotIntegrityError` as a 500 rather than an honest miss.
Fail-loud rather than fail-silent, and vanishingly narrow — but J-08 will poll this route *during*
builds, which is exactly when the window is open.

### Frontend Findings

**F1 — IMPORTANT (gap, not fixed): the QA report asserts a J-10 sentinel PASS that its own primary
evidence contradicts**

`reports/qa/goal-rapid-microscope-iter-2-qa.md` records "Browser QA Checks — **Status: PASSED**" and
a ten-row J-10 table with every surface "PASS … byte-identical to iter-1". The browser lane says
otherwise:

- `reports/phase-goal-rapid-microscope-iter-2-ui-test-results.md` — **Browser QA Verdict: FAIL,
  6/9**, with UT-06 (`/structure` Tradable Map), UT-07 (`/desk` Playbook Signals filters) and the
  UT-J-10 rollup all FAIL.
- `reports/phase-goal-rapid-microscope-iter-2-regression-replay-results.md` — **0/1 journeys
  passed** (golden step 9).

The QA report cites `TC-18-structure-map.png` for a claim ("Tradable Map page loads") that a page
load cannot support, and never mentions the failing lane. Under this project's own rubric (§5: a
"no regressions" claim needs the replay lane green *or* an explicit list of what was not
re-verified; §6: when the artifact contradicts the claim, the artifact wins) that row is `unknown`,
not `PASS`.

**My own read of the product — which is what the verdict turns on — is that nothing regressed**, and
the browser agent's in-run corroboration is genuinely strong: on the same live page it loaded
`AAPL` as-of `2026-06-22` and got the identical `resistance 300.11–302.2, Class A` band iteration 1
recorded, and it drove the playbook filters to "showing 0 of 5 recorded signals" once a session with
recorded signals was selected. The iteration's diff touches **zero** `.tsx` files and no `/structure`
or playbook module (`git status` on `apps/frontend` and `app/engine`: clean). UT-06 fails because
symbol PG has no *bar* series in the rig (this iteration seeded *tick* datasets — different store);
UT-07 fails because the rig's default session never had `Run Playbook` executed; the replay's step-9
complaint is a stale golden assertion on `b06e0bc289c54d77`, a per-instance signature hash the
browser agent correctly identified as unsafe to hardcode.

Consequence for the record: **DoD item 3 is not literally met** and J-10's browser sentinel should
be carried forward as `partial`, not `passing`. Not auditor-fixable — closing it needs either a bar
fixture for PG in the rig or a test plan parameterized to the rig's actual data state, both beyond
this iteration's fence.

**F2 — OBSERVATION (evidentiary, not a defect): the rig seeding legitimately moved a sentinel
number.** Referee Registry's Evidence Readiness now reads "Datasets 2, Train/Holdout 1/1 … 148 short
of the gate" where iteration 1 read 0/150 — the direct, honest consequence of seeding two tick
fixtures. UT-08 recorded it as PASS; worth naming so a future sentinel diff does not read it as
drift.

### Test Findings

**T1 — GAP: the TR-1 and TR-17b traps are scoped to `_non_close_out(rows)`**
`apps/backend/tests/test_micro_observer.py:41`, used at `:444` and `:519`. The close-out row is
excluded from both the prefix-identity and the truncation-reproduction comparisons. The exclusion is
defensible — a truncated stream genuinely ends earlier, so its `finalize()` sweep legitimately
differs — but it is nowhere disclosed, and it means the *persisted file* of a truncated build is not
a byte-prefix of the full build's file, only its trade rows are. J-05's accessor will read these
files; the distinction should be written down before it does.

**T2 — OBSERVATION: one vacuous assertion.** `tests/test_micro_observer.py:161` asserts a list
comprehension (`assert [r[...] == pytest.approx(e) for r, e in zip(...)]`), which is truthy
whenever the list is non-empty. Harmless — the loop directly below performs the real per-element
assertion — but it is exactly the shape that hides a dead check.

**T3 — OBSERVATION: `test_tc13_progress_increases_monotonically_to_done`
(`tests/test_micro_snapshots.py:298`) joins the worker thread *before* sampling progress**, so it
observes only terminal state; the monotonicity it claims to prove is guaranteed by the manager's
locked increment, not by this test.

**T4 — OBSERVATION: TC-11's benchmark carries one cell rather than measuring it.** Rep B's NVDA
build time is a separate dev run's "~116 s" (the script reuses an already-valid snapshot and reports
`build_seconds: None` — `scripts/micro_snapshot_granularity_benchmark.py:162`); the handoff
discloses this. Separately, `_query_latency_seconds` probes with `event_counts["total"]` used as a
*timestamp*, so the latency column times a bisect over each representation's array rather than a
true anchor lookup. The handoff already calls that axis a weak tie-breaker and the decision rests on
bytes/build-time/capability, all genuinely measured on both real datasets — TC-11 is met in
substance.

---

## 3. Domain Assessment

The core domain logic is sound, and unusually disciplined for a first landing of this much
machinery.

**The prefix law holds structurally, not just by test.** Rows are append-only and never mutated;
deferred completions attach to the row being built when they resolve, never retroactively to an
earlier one. That is why TR-1's three-cut-point trap and the tail-perturbation trap pass on a real
committed tick fixture rather than a toy sequence — the property is a consequence of the data
structure, not of a lucky test.

**The reuse table (§2.5) is genuinely honored.** The aggressor side is read verbatim from
`snapshot.recent_trades[0].side`; `absorption_score` comes straight off `primary_features`. The one
thing the engine does not expose — *which stage* decided the side — is mirrored from
`classify_aggressor`'s documented stage-1 precondition, and I checked it line by line against
`app/engine/aggressor.py:42-59` and the engine's `_last_tick_dir` update at
`tape_engine.py:309-313`: the mirror is faithful, and it never re-decides the side itself.

**The §2.6 unit gate is real and now provably complete.** 1,824,729 depletion completions across the
real corpus, zero serving a raw share-denominated magnitude, verified by my own whole-corpus sweep
rather than by trusting the handoff's table. The AST source scan over the *observer* (not just the
feature module) is the right shape of guard: scoped to emitters, non-vacuous by its own assertion,
and it genuinely fails when the gate is removed.

**Where the honesty discipline slipped, it slipped in the same place twice**: at the boundary
between "this observation completed and I am withholding it" and "this observation never
completed". B1 was exactly that conflation in the data; B2 was the same conflation at the file level
(a truncated build indistinguishable from a complete one). Both are now explicit states with typed
vocabulary, which is the standard the rest of the module already met.

**What is *not* yet exercised**, and should not be mistaken for working: `divergence_at_level` and
`execution_vs_replenishment_ratio` are oracle-tested pure functions with no live caller (correctly
disclosed), the outcome set has no consumer, and no event-level read path exists (J-05's door).
J-02 built the substrate; nothing has yet asked it a research question.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/micro_observer.py` | `finalize()` sweeps a still-open depletion run as `unavailable: True` / `value: None` / `refused: False` (spec §0) instead of resolving it as a completed window; `_resolve_depletion` gained the `unavailable_at` path, routed through the same gated emitter so the TR-18 source scan keeps covering it |
| 2 | Important | `apps/backend/app/research/micro_observer.py` | `on_event` records `self.failure` and stops consuming (body split to `_consume`); new typed `MicroObserverFailure` |
| 3 | Important | `apps/backend/app/research/micro_snapshots.py` | `build_snapshot_rows` refuses (raises `MicroObserverFailure`) instead of persisting a silently truncated snapshot |
| 4 | Important | `apps/backend/app/research/micro_snapshots.py` | `feature_source_hash()` digests both `micro_features.py` and `micro_observer.py` (`_IDENTITY_SOURCE_MODULES`), so an observer-only edit re-keys the corpus |
| 5 | — (test) | `apps/backend/tests/test_micro_observer.py` | 4 new regression tests (the unavailable sweep across all three unit bases + the closed-window counter-test); both real-fixture TR-18 sweeps now separate `refused` from `unavailable` |
| 6 | — (test) | `apps/backend/tests/test_micro_snapshots.py` | 3 new regression tests (observer-failure refusal at builder and manager level; identity hash covers the observer) |
| 7 | — (data) | `apps/backend/.data/micro_snapshots/` | all 18 real-corpus snapshots rebuilt through the shipped CLI after the identity re-key |
| 8 | — (doc) | `docs/handoffs/goal-rapid-microscope-iter-2-dev.md` | "Audit amendments" section recording the three handoff claims these fixes invalidated |

**Verification of the fixes (commands and results, not claims):**

- `cd apps/backend && .venv/bin/python -m pytest tests/` → **2,835 passed, 8 skipped, 0 failed**
  (468.30s, exit 0). Exactly +7 over the dev's 2,828 — the 7 tests added here; no pre-existing test
  changed behaviour, none lost.
- `python -m app.research.micro_snapshots --all` → `snapshot build complete: 18 dataset(s)
  processed`, exit 0.
- Whole-corpus sweep of every row of all 18 files (post-rebuild): 18/18 identities re-verify, all
  `quote_size_unit: "unverified"`, per-file line count == stored `row_count` for all 18, total
  3,815,933 rows / 6,378.8 MB, 1,824,693 refused + 36 unavailable depletion completions, **0**
  serving a magnitude.
- Counter-checks recorded before each fix: B1's pre-fix output (`value: 400, unavailable: False`)
  and B2's pre-fix output (`observer rows: 1` for a 2-trade dataset, persisted `row_count: 2`,
  `identity-valid: True`).
- Era invariants re-verified **after** the fixes: `Config().config_fingerprint()` →
  `08e471b10130e1e2` (unchanged); all 6 `referee_*.py` SHA-256 hashes byte-identical to the
  iteration-0 listing; `git status` clean on `apps/backend/app/engine`, `apps/frontend`,
  `tests/test_observer_equivalence.py`, `tests/test_dense_replay_gate.py` (rail 3 intact, zero
  `.tsx` touched, both golden files unmodified).
- My own diff re-read: the changes are confined to the four code sites above plus their tests —
  no refactor, no unrelated edit, nothing else touched.

---

## 5. Recommended Next Step

**Proceed to J-03**, carrying three things forward explicitly:

1. **Record J-10 as `partial`, not `passing`, for this iteration** (F1). The kept product is
   corroborated unregressed, but the sentinel's literal browser acceptance did not pass and the QA
   report's PASS is unsupported. Before the next iteration whose acceptance rides on that sentinel,
   fix the *test plan* (parameterize `/structure` to a symbol the rig actually has bars for, and the
   Playbook step to a session with recorded signals) and repair `journey-scripts/J-10.json` step 9
   to assert the static label `"Built from signature:"` rather than the volatile hash — the browser
   agent already left exactly this guidance and correctly declined to overwrite the golden.
2. **B4's two §3/§4 omissions are J-05's inheritance** — the window-mean quote imbalance/microprice
   and the outcome-start spread cost-proxy column must land before any outcome is *served*, or the
   first served outcome breaches §4 on arrival.
3. **B5 needs an owner ruling, not a developer's guess**: is a price-change-terminated depletion's
   `available_at` the last in-window quote (today's behaviour) or the terminating quote? It is a
   one-line change either way; leaving it unruled means every downstream `available_at` consumer
   inherits an unexamined sub-second lookahead.

No blocking work remains for J-02 itself.
