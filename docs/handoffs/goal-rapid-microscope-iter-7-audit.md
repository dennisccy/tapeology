# goal-rapid-microscope-iter-7 Audit Report

**Date:** 2026-08-18
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's two deliverables are real and, after one fix, sound: the Card-5.1 preservation
fields thread the whole event pipeline additively, and J-05's "tick-family fold request naming
`11 < 105`" now genuinely reaches a production entry point (I re-ran it myself against the real
store). The byte-compatibility claim survives a harder test than the one the dev/review lanes ran
— I proved full round-trip row identity for all **9,145,900** rows in all 18 real datasets, not
just that they load. But the change silently defeated a *(critical)*-tagged anti-goal that no lane
checked: the preservation fields entered the dataset **content checksum**, which is the sole
enforcement of "split tags are frozen at registration", so one tape re-fetched after this change
could be registered a second time under a *different* split (train/holdout contamination). That is
fixed at the single choke point, with a regression test and byte-compat re-proven on all 18 real
datasets. Remaining items are documented gaps, chiefly that goal.md's own J-06 step 1 sentence is
only half-delivered (the dated vendor rule is deferred by design).

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): the Card-5.1 preservation fields entered the dataset CONTENT checksum, silently disabling the frozen-split re-tag refusal**

`apps/backend/app/research/datasets.py:256` (`_content_checksum`) hashes the stored event rows;
`record()` enforces immutability with exactly one check — `if meta["checksum"] == checksum: raise
DatasetAlreadyRegistered` (`:526`/`:532`). This module's own docstring (`:31-34`) states the
promise that check exists to keep:

> "it REFUSES content that is already registered: re-recording the same tape under a different
> split (the re-tag attempt) — or the same split — raises the 409-style `DatasetAlreadyRegistered`"

Once `_event_to_row` began emitting `conditions`/`exchange`/`tape`/`trade_id` (and the quote
equivalents) into the hashed rows, **the same tape hashed to two different identities depending
only on when it was fetched.** All 18 real on-disk datasets were recorded before the preservation
fields existed; the Alpaca adapter now populates them at both historical construction sites
(`app/providers/adapters/alpaca.py:395-401`, `:511-517`), and `POST /datasets` with
`source_kind=historical` (`app/research/routes.py:366`) runs that exact path. So any of those 18
windows could be re-requested and registered a *second* time under a *different* split — one tape
in both `train` and `holdout`, which is train/holdout contamination, not a duplicate. That breaches
the spec's *(critical)* "Immutable data — registered datasets ... never re-tagged ... Splits are
frozen at registration" anti-goal and fails the DEFINITION OF DONE line "No anti-goal violation
introduced".

Reproduced before the fix (same tape, identical timestamps/prices/sizes/sides; second list merely
preserves the vendor identifiers Alpaca always returned):

```
CONTROL  1st legacy record   : RECORDED  split=train   checksum=c23b348302f2350c
CONTROL  2nd identical record: REFUSED (DatasetAlreadyRegistered) — split tags are frozen ...
SCENARIO pre-change record   : RECORDED  split=train   checksum=c23b348302f2350c
SCENARIO post-change re-fetch: RECORDED  split=holdout checksum=792d3dad11cd7250   <-- LEAK
  datasets now registered: 2   train + holdout, same window 2026-06-22T17:00:00Z
```

I weighed CRITICAL against IMPORTANT and chose CRITICAL: the guard is the *only* enforcement of a
*(critical)* anti-goal, it is reachable from a normal production request, and the resulting state
is precisely the research-data corruption the guard exists to prevent, in an era whose subject is
not fooling yourself with contaminated evidence.

**Fix applied** (`datasets.py:88-96`, `:233-254`, `:256-271`): a `_tape_identity_rows` projection
strips the six preservation keys before hashing, so the content checksum is over *the tape itself*
again — the semantics `_content_checksum`'s own docstring already claimed. Symmetric by
construction: both the write side (`:526`) and the on-load verify side (`:361`) call the same
function. Legacy rows carry none of those keys, so the projection is the identity function for
them (it returns the same list object — zero allocation) and every stored checksum still verifies
verbatim. Tamper detection of the preservation values themselves is unaffected: `_load` verifies
the whole record against `file_checksum` (which covers every row key) at `:349` **before** the
content checksum is ever recomputed.

**B2 — GAP: the tick-family "request" permanently freezes the tick corpus's fold geometry and pins a `corpus_manifest_hash` that can never update**

`run_tick_family_fold_request` (`app/research/walkforward.py:1005`) calls `register_fold_spec`
(`:1039`) *before* the floor check (`:1043`), so the CLI whose entire documented purpose is
"print the typed below-floor refusal" also writes a permanent ledger row. Two consequences, both
delayed rather than present-day:

1. `register_fold_spec`'s idempotency is keyed on `geometry_hash` **only**
   (`walkforward_ledger.py:176-177`) — `corpus_manifest_hash` is not part of the key. So once the
   tick corpus grows (J-06's whole purpose), re-running the CLI replays the existing row and the
   ledger keeps reporting the hash of *today's 11 dates* forever.
2. `DIAGNOSTIC_GEOMETRY` becomes the tick family's frozen geometry from the first invocation. A
   later tick-appropriate geometry then hits `FoldGeometryFrozenError` (`:179`) and needs a
   recorded voiding event — which, per `WF_SURVIVOR_RULE_V1` condition 5, is fatal to every
   survivor state of that corpus-era.

Not a defect of this iteration: the phase spec explicitly authorised this ordering ("Consider
mirroring the existing playbook path's ordering ... developer's call, not mandated"), and the
playbook path (`:1183`) has the same shape. Documented, not fixed — reversing it would contradict
an authorised choice and the test that asserts the fold spec *is* registered.

**B3 — GAP: the tick-family CLI's success path reports "fold request complete" without building any folds**

`walkforward.py:1046` returns `{"corpus_id", "session_count"}` with no `build_folds` call, and
`main()` prints `"tick-family fold request complete ({family}): {N} session(s) clear the
WF_MIN_SUFFICIENT_FOLDS floor"` and exits 0 (`:1285`). Unreachable today (11 < 105 always raises
first — I verified) and deliberately so per the developer's own T-1 reasoning, but it becomes
reachable *exactly* when J-06 succeeds in growing the corpus, and at that moment an operator gets
a success message and exit 0 for a fold build that never happened. Worth wording honestly ("no
fold build was performed") when J-06 lands; not fixed here (GAP-level, fixing it is scope creep).

**B4 — GAP: goal.md's J-06 step 1 is delivered in part, not in full**

`docs/goal.md:551-558` defines step 1 as the optional preservation fields **"plus the §2.6
`schema_basis` + `quote_size_unit` stamping from the dated vendor rule (Alpaca CTA/UTP shares from
`2025-11-03`, round lots before)"**. This iteration ships the storage *capability* only — the
dated rule is explicitly reserved (assumption ledger iter-7, first entry), and no caller anywhere
supplies either kwarg, so nothing is stamped on any recording today. The phase spec authorised
this deferral and the dev handoff does not claim J-06 complete, but it does read as "step 1
ships"; the evaluator should treat step 1 as **partially** delivered when deciding J-06's status.

**B5 — OBSERVATION: events become unhashable once `conditions` is populated**

`TradeEvent`/`QuoteEvent` (`app/providers/base.py:25`/`:52`) and `RawTrade`/`RawQuote`
(`app/providers/adapters/base.py:65`/`:87`) are `frozen=True` dataclasses, so Python generates
`__hash__` over the field tuple. With `conditions` a `list`, `hash(event)` raises
`TypeError: unhashable type: 'list'` (verified). No current call site hashes an event, so nothing
breaks today — but it is a trap that will fire only on *preserved* data, i.e. exactly what J-06
steps 2-5 will produce. A `field(hash=False, compare=...)` or a tuple instead of a list would
close it.

**B6 — OBSERVATION: an empty vendor value still emits a key, at the margin of the present-only discipline**

`_conditions_list([])` returns `[]` and `_venue_str("")` returns `""`
(`app/providers/adapters/alpaca.py:169`/`:182`, both verified), and `_event_to_row` tests
`is not None`, so an empty SDK value writes `"conditions": []` / `"exchange": ""` — a present key
carrying no information. Harmless post-B1-fix (it no longer perturbs dataset identity), but it
makes the stored shape depend on a vendor's empty-vs-absent choice.

**B7 — OBSERVATION: `--family` silently overrides `--diagnostic`**

`walkforward.py:1276` returns from the family branch before the diagnostic branch is reached.
Verified: `--diagnostic --family tick_legacy` runs only the family path, with no warning. Argparse
mutual exclusion would make the precedence explicit.

### Frontend Findings

None. Verified independently: `git status --short` shows zero `.tsx`/`.ts` files in this
iteration's diff, and no route, serialized field, or served value changed. The `Frontend Present:
yes` declaration is the documented mechanical trigger for the browser lane, not a UI claim.

### Test Findings

**T1 — IMPORTANT (fixed): nothing pinned dataset content identity against the new row keys**

The four new tests are otherwise good (tight equality assertions, an on-disk key-absence check, an
AST-based vocabulary guard) — but every one of them exercises a *single* record. None asserted
what the row-shape widening did to the checksum that carries the split guarantee, which is why B1
passed both review and QA. Closed by
`tests/test_datasets.py:526` —
`test_the_frozen_split_guard_still_refuses_one_tape_re_fetched_with_preservation_fields`, which
asserts the refusal in **both** record orders (legacy-then-preserved and preserved-then-legacy) and
re-asserts that the preservation values still survive the round trip verbatim, so a future "just
strip them everywhere" shortcut cannot pass it.

**T2 — GAP: browser evidence cited by two lanes is not on disk**

`reports/phase-goal-rapid-microscope-iter-7-regression-replay-results.md` (written 00:14:39) cites
`reports/qa/.../J-10-verify.png`, and the QA report (00:30:25) cites nine descriptive screenshot
names (`UT-01-cockpit-home.png` …). None of the ten exist; the evidence directory holds only the
browser-qa lane's eight `UT-0N-result.png` (00:34–00:37). `demo_runner.py:1176-1181` only records a
path after `page.screenshot()` succeeds, so the replay screenshot did exist at capture time and was
removed later — I could not establish by what, and I make no fabrication claim. Effect: TC-11's
"every step produces a screenshot" is not independently re-checkable for those two lanes. It does
not change the verdict, because the browser-qa lane's own verdict file (which I read directly, per
the standing iter-6 mitigation) reads PASS 8/8 with eight genuine screenshots covering cockpit `/`,
`/structure` Tradable Map, and every shipped `/desk` section including the three Referee sections.
Flagged for the operator as an artifact-lifecycle issue.

**T3 — OBSERVATION: the J-10 sentinel was covered two ways, neither of them the literal 13 steps in the LLM lane**

The LLM lane self-declares that "UT-03 through UT-07 collectively re-run all 13 steps ... by
surface" — a mapping, not the script. The deterministic replay lane *did* run
`journey-scripts/J-10.json` end to end and reports PASS. Both together are adequate; the mapping
should be named as such rather than read as a 13-step execution.

**T4 — OBSERVATION: the iter-6 framework bug did not bite this iteration**

I checked directly rather than trusting the merged headline: the only `FAIL` token in either UI
results file is a template comment (`llm.md:12`), and both files' verdict lines read PASS.

---

## 3. Domain Assessment

### DEFINITION OF DONE — verification trace

Risk-class items (schema mutation, data persistence, ledger writes) were fully re-traced through
the code and re-executed by this audit. Mechanical items already executed live against the running
system are accepted on the reviewer's PASS **plus** the cited executed row.

| # | DoD item | How verified | Result |
|---|---|---|---|
| 1 | J-06 step 1 ships, proven via TC-1/2/3/9 | **Full trace** (risk class: shared schema + persistence). Read `_event_to_row`/`_row_to_event` line by line; re-ran TC-1 harder than the handoff (full row round-trip, not load-only) over all 18 real datasets + both committed fixtures; read TC-2/TC-3/TC-9 sources | **Met** — 9,145,900/9,145,900 rows byte-identical, 0 new keys, 20/20 checksums verify. Partial vs. goal.md's own step-1 sentence — see B4 |
| 2 | Engine byte-compat: TC-4/TC-5 green; fingerprint `08e471b10130e1e2` | **Full trace.** `git status` proves `test_observer_equivalence.py`, `test_dense_replay_gate.py`, `test_real_data_gate.py`, `app/engine/` all unmodified; I ran the fingerprint and a same-tape-with/without-fields `replay()` comparison myself | **Met** — fingerprint `08e471b10130e1e2`; snapshot sequences byte-identical |
| 3 | J-05 clause met via a genuine production entry point: TC-6/7/8 | **Full trace.** Re-ran TC-7 myself against the real store with a scoped ledger; read TC-6's source; `git diff -U0` proves TC-8's test untouched (zero removed lines) | **Met** — `11 < 105`, `TR-15`, exit 1, real ledger untouched |
| 4 | J-10 sentinel + TR-19's schema-provable half re-proved: TC-10/TC-11 | TC-10 **full trace** (suite count, 6 referee hashes, double-replay — all re-run by me). TC-11 accepted on reviewer PASS + the browser-qa lane's own verdict file read directly (8/8 PASS, 8 screenshots on disk) + the replay lane's `UT-J-10` PASS row | **Met**, with T2/T3 noted |
| 5 | J-01–J-04 remain green: TC-12 | Accepted on reviewer PASS + executed rows UT-02 (J-01 Microscope Readiness: 1 symbol-day / 2 datasets / exactly 12 columns, no preservation column) and UT-01 (J-02/03/04 have no dedicated UI). Independently confirmed the diff cannot reach their served values: no route, no serializer, no served field changed | **Met** |
| 6 | No anti-goal violation introduced | **Full trace** — this is where B1 was found | **Failed as shipped; met after the audit fix** |
| 7 | Full suite ≥ iteration-6 baseline, 0 failures, 0 regressions | Re-run by me after my fix | **Met** — 3045 passed / 8 skipped / **0 failed** (dev: 3044; baseline: 3038) |
| 8 | Dev handoff written | Read in full | **Met** |

### What the code actually shows

The domain reasoning behind this change is sound and, unusually, its riskiest property holds up
under a harder test than anyone ran. The absent-key discipline is implemented at the only two
places that matter — `_event_to_row` adds a key only for a non-`None` value, `_row_to_event` uses
`row.get(...)` throughout — and I proved the consequence directly rather than inferring it:

| Independent check (run by this audit) | Result |
|---|---|
| Full round-trip `_event_to_row(_row_to_event(row))` over all 18 real datasets | **9,145,900 / 9,145,900 rows byte-identical**, 0 mismatches |
| New keys on any real row or manifest | **0** (rows) / **0** (manifests) |
| `file_checksum` verified per dataset | 18 / 18 |
| Content checksum recomputed **from the round-tripped rows** vs. stored | 18 / 18 (this is the property the dev's load-only check did not test) |
| Committed fixtures (`tests/fixtures/datasets/*.json`) verify + load with all fields `None` | 2 / 2 |
| Engine blindness: same tape with all 8 fields populated vs. absent, full `replay()` | **snapshot sequences byte-identical** (5,334 events) |
| Two consecutive `replay()` calls over one unchanged real dataset | byte-identical |
| `Config().config_fingerprint()` | `08e471b10130e1e2` |
| Six `referee_*.py` SHA-256 vs. the iteration-0 listing | 6 / 6 identical |
| Real installed Alpaca SDK field names/types vs. the code's assumptions | all 8 correct (`Trade.id: int\|None`, `exchange: str\|Exchange\|None`, `conditions: List[str]\|str\|None`, `tape: str\|None`; `Quote.bid_exchange`/`ask_exchange` likewise); `_venue_str(Exchange.Q)` → `'Q'`, not `'Exchange.Q'` |

The J-05 half is genuinely closed. I re-ran the production CLI against the operator's real store
with a scoped ledger directory:

```
$ TAPEOLOGY_MICRO_WALKFORWARD_DIR=<scoped> python -m app.research.walkforward --family tick_legacy
tick-family fold request refused (tick_legacy): 11 < 105 -- refused (TR-15): this corpus cannot
produce WF_MIN_SUFFICIENT_FOLDS(3) folds under this geometry
$ echo $?   ->  1
```

with `.data/micro_walkforward` provably untouched (identical directory listing hash before and
after). The three error paths the spec names all produce the typed refusal, never a traceback:
missing dataset directory → `0 < 105`, empty directory → `0 < 105`, both flags together →
`0 < 105`, each exit 1. `test_tc20_...` is untouched — `git diff -U0` on `test_walkforward.py`
shows **zero removed lines**; the single `tc20` occurrence in the diff is inside an added
docstring.

Where the domain reasoning fell short was one level up from the row: nobody asked what the widened
row shape does to *dataset identity*. The checksum is not just an integrity device in this system
— it is the enforcement mechanism for the split freeze, and therefore for train/holdout
separation. That coupling is documented in the module's own docstring and was still missed by the
diff, the review, and QA. B1's fix restores "same tape ⇒ same identity" and makes the coupling
explicit in the code.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/backend/app/research/datasets.py` | Added `_PRESERVATION_ROW_KEYS` (`:88`) and `_tape_identity_rows` (`:233`); `_content_checksum` (`:256`) now hashes the tape-only projection, so the Card-5.1 vendor identifiers no longer change a dataset's content identity. Restores the `DatasetAlreadyRegistered` re-tag refusal for a window re-fetched after this iteration. Byte-compatible: the projection is the identity function for every row already on disk. |
| 2 | Critical | `apps/backend/tests/test_datasets.py` | New regression guard `test_the_frozen_split_guard_still_refuses_one_tape_re_fetched_with_preservation_fields` (`:526`) — asserts the refusal in both record orders, asserts only one split tag survives, and re-asserts that the preservation values still round-trip verbatim. |

**Post-fix verification (each command run, each result cited):**

- `.venv/bin/python -m pytest tests/test_datasets.py` → **23 passed** (was 22; +1 new guard).
- B1 reproduction re-run → `SAME TAPE re-registered under a SECOND split: False`; the second
  attempt now raises the documented refusal and `store.list()` returns **1** dataset, not 2.
- Byte-compat proof re-run over all 18 real datasets **after** the fix → 18/18 file checksums,
  18/18 content checksums from round-tripped rows, 9,145,900 rows, **0** mismatches, **0** new keys.
- Engine-blindness + determinism proof re-run → snapshot sequences byte-identical; same tape in
  both shapes now yields the **same checksum** (`same tape identity across both shapes: True`).
- Cost on the heaviest real path (199 MB / 1,973,556-row NVDA dataset): the projection scan adds
  **0.231 s**, 9.6 % of the checksum step and ~2 % of a full `_load` — and returns the same list
  object for legacy shapes, so no allocation.
- Full backend suite re-run after the fix (`cd apps/backend && .venv/bin/python -m pytest tests/`)
  → **3045 passed, 8 skipped, 0 failed in 538.77s**. Exactly +1 on the dev's 3044 (my new guard),
  **0 regressions**; still above the iteration-6 baseline of 3038.
- Diff re-read: the change touches only the constant, the new helper, one line inside
  `_content_checksum`, their docstrings, and one new test. No scope creep, no new escape hatch —
  the fix *adds* a refusal, it does not silence one, and `file_checksum` still guards every stored
  byte before the projection is reached.

**Dev handoff claims invalidated by this fix:** the handoff's statement that
"`_content_checksum` hashes `symbol`/`data_feed`/`epoch_anchor`/`events` only" is now
"…`events` projected to tape-only". Its byte-compat numbers all remain accurate and are
independently confirmed above.

---

## 5. Recommended Next Step

Proceed to the evaluator, with three things carried explicitly:

1. **J-06 step 1 is half of goal.md's step 1.** The storage capability ships and is proven; the
   dated vendor rule (`2025-11-03` CTA/UTP shares vs. round lots) and any actual stamping do not.
   Do not credit step 1 as complete — the next J-06 iteration owns the rule plus `tick_recorder.py`.
2. **J-05's remaining clause is genuinely met** — `11 < 105`, TR-15, exit 1, from a real production
   entry point against the real corpus, independently reproduced by this audit.
3. **Carry B2 into the J-06 iteration that grows the tick corpus.** Before recording new tick
   tranches, decide whether `DIAGNOSTIC_GEOMETRY` is really the geometry the tick family should be
   frozen at, because the first `--family tick_legacy` run freezes it and the ledger's
   `corpus_manifest_hash` for that corpus will never update afterwards.

Also worth an operator note outside this loop: T2's artifact-lifecycle problem (two lanes citing
screenshots that are no longer on disk) sits alongside the still-unfixed
`merge_ui_test_results.py:64` `**FAIL**`-parsing bug — both weaken the audit trail the browser lane
is supposed to leave behind.
