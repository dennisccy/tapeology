# goal-rapid-microscope-iter-11 Audit Report

**Date:** 2026-08-19
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's central claim is true and I verified it independently rather than accepting it:
a dataset produced by the **real** `run_tick_recording` write path under a registered universe is
withheld by the new predicate and absent from `GET /research/datasets`, and a sweep of all 78
registered GET paths finds no surface serving an unresolved pool member's symbol, window, id or
checksum. The recorder-progress body is aggregate-only with no bypass, `routes.py`'s beyond-plan
edit was load-bearing (without it the most public listing surface still leaked), and every frozen
rail holds — suite 3192/3184/8/0 on my own run, fingerprint `08e471b10130e1e2`, all six
`referee_*.py` SHA-256 hashes byte-identical, MCP at 22 tools, zero `.tsx`/`.ts` diffs, real
`.data` store untouched.

Three IMPORTANT findings remain UNFIXED, deliberately. Each one is a place where this diff's
widening collides with a rule the spec already fixed elsewhere, and resolving each requires
choosing between two stated invariants — the T-1 situation this era escalated over in iteration 10.
I did not improvise a ruling. All three are named below with reproductions, the mechanical fix, and
the specific question the owner must answer.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap, carried forward): the vault route publishes a universe's COMPLETE rule while pool members are still withheld — restoring the exact subtraction attack iter-9's audit closed**

`vault._fully_exposed_universe_ids` (`apps/backend/app/research/vault.py:926-938`) gates the
`symbol_rule`/`date_rule` reveal on **shard-ledger rows only**: a universe is "revealed" once it
owns ≥1 row and no row is short of `exposed`. Iteration 11 widened *withholding* to universe-RULE
membership (`vault.py:809-881`) but left this twin gate narrow. The two now disagree about whether
a universe is fully resolved.

Reproduced (auditor probe, since removed): register universe U over `{ZQXPRC, ZQXPRD} × {2031-06-05}`,
record both, seal→assign→expose ZQXPRC, leave ZQXPRD untracked. `micro_snapshots.withheld_dataset_ids_for_store`
correctly still withholds ZQXPRD — and `GET /research/desk/micro/vault` returns
`"rule_disclosure": "revealed"` with the full `symbol_rule` and `date_rule` lists.

That is verbatim the attack `build_vault_state`'s own docstring (`vault.py:972-982`) says the gate
exists to prevent: *"the rule is read beside `GET /research/datasets` … `expected - served` is
exactly the sealed set — a full de-anonymisation from two public GETs"* (iter-9 audit finding B1).
It is also the phase spec's critical anti-goal wording — a complete list of one side is now
derivable by subtraction from two public GETs, with no operator knowledge required.

Not CRITICAL, and the reason matters: r5's own governing test **hands the attacker the registered
universe** ("public by construction", §7.2/§7.5), so the modelled adversary gains nothing. The loss
is defence-in-depth against a reader who does not already know the rule, plus the inconsistency
itself.

**Why I did not fix it.** The mechanical fix is small — pass the store's
`(dataset_id, symbol, session_date, created_utc)` tuples into `build_vault_state`, run the same
`unresolved_pool_universe_by_dataset_id` predicate, and subtract universes with any unresolved pool
member from `revealed`; I confirmed it would **not** break the existing iter-9 reveal test
(`apps/backend/tests/test_vault.py:1178-1192`), because that fixture records its four datasets
*before* registering the universe, so the `created_utc >= registered_at` guard keeps them out of
the pool. But the fix has a real cost the spec has not priced: under the mandated §7.2 order
(register first, record after) **every** pool member is a rule match, and the exploratory-release
mechanism is unbuilt (the phase spec's own named open gap), so a universe holding any
never-sealed member would keep its rule committed **forever** — converting §7.2's audit trail from
"a delay" (the docstring's and test's stated intent) into a permanent withholding. Choosing between
"close the subtraction channel" and "keep the §7.2 audit trail eventually auditable" is an owner
call, not an auditor's. Surfaced, not improvised (T-1).

**B2 — IMPORTANT (gap, carried forward): `progress.trades_total`/`quotes_total` become a withheld shard's EXACT event counts on a single-symbol-day run**

`tick_recorder._progress_view` (`tick_recorder.py:665-691`) serves run-scoped running totals
accumulated by `_publish` (`tick_recorder.py:800-801`) from each fetched chunk's own
`HistoricalWindow`. The recorder's scope is whatever the operator POSTs
(`micro_routes.py:441-448`, `symbols` × `dates`), so a job scoped to **one** symbol-day — an
ordinary act (recording one pair, resuming one failed pair) — makes those totals identical to that
single dataset's exact `event_counts`.

Reproduced (auditor probe): a 1-symbol-day run over `ZQXPRF/2031-06-09` under a registered universe
produced `trades_total=3, quotes_total=3`, exactly the recorded dataset's
`event_counts {'trades': 3, 'quotes': 3}` — while that same dataset was simultaneously withheld
from every other surface (`withheld=True`).

This contradicts §7.5 ("Exact event counts, bytes, and any feature/outcome aggregate are withheld
until exposure") and the r3 TR-2 forbidden-scalar list — and it is also *exactly what §7.1 and this
phase spec's own Data-contract additions mandate* ("total trades and quotes";
`progress.trades_total: int >= 0`). Two spec clauses conflict: an aggregate over a one-element set
is not an aggregate.

Mitigation that keeps this below CRITICAL: the value is unattributed. A reader polling the route
learns "some pool member has N trades", not which one, unless they already know the run's scope.

**Why I did not fix it.** Every available fix — dropping the fields, bucketing them to orders of
magnitude, or refusing to publish them below a symbol-day threshold — deletes or degrades a field
both the methodology spec and the phase spec explicitly order. That is a spec change, not a bug
fix (T-1). Owner question: *should recorder-progress event totals be suppressed or coarsened when
the in-flight run covers fewer than N symbol-days?*

**B3 — IMPORTANT (gap, carried forward): the new predicate does not honour r6 §7.8's settled fail-closed ruling, and it widens that gap's blast radius**

`unresolved_pool_universe_by_dataset_id` (`vault.py:809-881`) reads `all_rows()` on both ledgers
with **no** `verify_chain()` call. `docs/rapid-validation-spec.md` §7.8 (r6, added in this same
working tree, dated 2026-08-18, and recorded as owner ruling 3 in
`runs/goal-session-rapid-microscope/state/assumptions.md`) states: *"Every vault/exposure predicate
calls `verify_chain()` FIRST. Any verification failure raises a typed refusal"*, under the
governing invariant *"unknown exposure history may NEVER be interpreted as 'never exposed.'"*

Concretely, `micro_chain_ledger.HashChainedLedger.all_rows` (`micro_chain_ledger.py:94-96`) returns
`[]` for a missing file. So deleting `micro_vault/`, or repointing `TAPEOLOGY_MICRO_VAULT_DIR`,
empties the pair index and **silently republishes the entire pool** — the fail-open direction, on
the one rail whose failures are irreversible. Before this iteration the universe ledger was not a
withholding input at all; iteration 11 makes it one, so the unimplemented §7.8's blast radius grew
from "already-sealed shards" to "every pool member".

**Why I did not fix it.** The phase spec explicitly freezes this path ("a corrupted or missing
vault ledger at withhold-check time fails the SAME way `withheld_dataset_ids()` already does today
— no behavior change to that path this iteration"), and §7.8/TR-25 specify a full halt-and-
evidence-backed-recovery protocol that cannot be partially improvised without inventing the typed
refusal contract. Fixing it here would violate an explicit OUT OF SCOPE instruction.

**Process note that let this pass unflagged:** the phase spec's OUT OF SCOPE still lists "whether a
corrupted vault ledger fails closed or open" among "the two remaining owner questions … human-owned,
not this iteration's job to resolve". That is **stale** — the owner ruled on both on 2026-08-18, and
r6 §7.8/§8.1 landed in the same working tree this iteration builds against. Nobody (decomposer,
developer, reviewer, QA) flagged the contradiction. Under T-1 that contradiction should have been
surfaced rather than inherited.

**B4 — GAP: the rule predicate matches by exact string, with no normalization, and fails OPEN on a mismatch**

`unresolved_pool_universe_by_dataset_id` matches `(symbol, session_date)` verbatim against
`expected_recording_pairs()` (`vault.py:461-464`). `POST /research/desk/micro/recorder/compute`
does **not** normalize `body.symbols` (`micro_routes.py:441-448`; only the CLI upper-cases, at
`tick_recorder.py` `main()`), and `register_universe` stores `symbol_rule` verbatim. A universe
registered as `["AAPL"]` with a recording POSTed as `["aapl"]` (or the reverse) yields pool members
that are never withheld — a silent fail-open on the critical rail, with no control to catch it:
TR-4's `verify_recording_batch` would refuse the mismatched batch but has zero production call
sites. Related: `register_universe` types `date_rule: list[str]`, narrowing §7.2's "an explicit
date range **or rule**" to an explicit list, so a range-encoded rule would match nothing and
withhold nothing. Both are pre-existing narrowings whose *consequence* this iteration escalates
from "TR-4 verification is wrong" to "pool members are published".

**B5 — OBSERVATION: two store enumerations per request on the dataset routes**

`micro_snapshots.withheld_dataset_ids_for_store` now performs its own `dataset_store.list()`
(`micro_snapshots.py:166`), so `GET /research/datasets`, `GET /research/datasets/{id}` and
`POST /research/backtests` each enumerate the store twice. Cheap today — `DatasetStore._cached_meta`
is a stat-keyed cache over a durable `dataset_index.db`, so a warm call is stat-only, and the dev's
live curl against the real 18-dataset corpus returned normally. Noted so it is not mistaken for
free if the corpus grows. `exclude_withheld` correctly avoids this by consuming the caller's own
records.

**B6 — OBSERVATION: the 403 refusal now says "sealed" for datasets that are not sealed**

`routes.py:445-449` serves `vault.SealedShardWithheldError`'s wording ("this dataset is sealed in
the validation vault") for untracked pool members that carry no ledger row at all. Verified live
(403, no symbol/date in the body). Spec-consistent (§7.5 point 3: the refusal states only that the
id is sealed) and *good* for opacity — an exploratory member and a sealed one are indistinguishable
— but literally inaccurate. Worth a wording review when the exploratory-release mechanism lands.

### Frontend Findings

**F1 — none.** `git diff --stat HEAD -- '*.tsx' '*.ts'` is empty. No frontend file references the
tick recorder's progress at all — every `outcomes` hit in `apps/frontend/lib/types.ts` and
`apps/frontend/app/desk/page.tsx` belongs to DeskTopup / DeepBackfill / Playbook — so removing
`progress.outcomes` cannot break a rendered surface. The readiness shapes (`shards`,
`sealed_tranche`) are unchanged.

### Test Findings

**T1 — GAP: the rewritten TR-2 trap checks the wrong forbidden substrings for the r5 identity**

`tests/test_vault.py`'s new TC-8/TC-9 asserts only that each unresolved member's **dataset id** and
**raw checksum** are absent from the swept union; the actual r5 identity — symbol + session date —
is checked only against two named surfaces (`/research/datasets` and readiness), reconstructed from
the fixture's own known pairs. A leak of the symbol/date through a third surface would pass. I ran
the widened sweep myself (all 78 registered GET paths, symbol and window-start substrings, against
untracked pool members): **clean**. So this is trap strength, not a product hole — but the older r3
test (`test_tr2_no_registered_get_route_serves_or_derives_a_sealed_shards_identity`) does check
symbol/window and the new one should match it.

**T2 — GAP: required-still-passing journey J-07 was not run, and the record of why it has no golden was deleted**

`reports/phase-goal-rapid-microscope-iter-11-ui-test-results.md:49` records
`UT-J-07 … not run this iteration … DEFERRED-BUDGET`. The DoD requires J-07 to remain green. Risk
is low — the diff touches no J-07 (graduation) surface and the graduation tests pass — but the
claim is unevidenced this iteration. Compounding it, `runs/goal-session-rapid-microscope/state/golden-gaps`
(whose entire content was the single line `J-07`) was **deleted** during this run while no
`journey-scripts/J-07.json` was created, so the record explaining J-07's missing golden is gone.

**T3 — GAP: TC-12's "against the real store" evidence was produced against the fixture rig**

The QA browser lane ran against the pipeline's scoped rig (QA report UT-05: "Real store has 2
datasets"), not the operator's 18-dataset `.data` corpus, so the DoD's "element capture of the
shipped `/desk` Microscope Readiness shards table proving it is byte-identical **against the real
store**" was not literally produced. The substantive claim nevertheless holds by construction and I
verified it directly: `apps/backend/.data` contains **no `micro_vault` directory at all**, so both
halves of the predicate are provably empty against production; `.data/datasets`'s newest file
mtime predates this iteration by a month; and `reports/qa/goal-rapid-microscope-iter-11-store-scope-guard.md`
independently reports CLEAN over 11,275 protected files.

**T4 — OBSERVATION: the QA report is wrong about the single most load-bearing edit**

`reports/qa/goal-rapid-microscope-iter-11-qa.md:107` states *"`routes.py` — no changes needed;
choke point is in `micro_snapshots.py`"*, and line 110 states *"All 9 changes match the execution
plan exactly."* Both are false: `routes.py` **was** changed, that change was **beyond the plan's
file list**, and it is load-bearing — I reproduced the dependency (probe 1: without the delegation,
an untracked pool member is served on `/research/datasets`). QA therefore did not verify the one
edit most worth verifying. The reviewer did, correctly.

---

## 3. Domain Assessment

The central design call — a **universe-RULE-driven** withhold predicate instead of a
ledger-row-driven one — is the right call, and it is the strongest thing in this diff. The gap it
closes is real, not hypothetical: `seal_shard`/`assign_shard`/`expose_shard` have zero production
call sites, so every dataset a real recorder finalizes today carries no ledger row and, pre-fix,
was fully identifiable the instant it landed. I verified the fix end-to-end through the real write
path rather than a hand-built fixture (`run_tick_recording` → `_finalize_day` →
`DatasetStore.record` → withheld → absent from `GET /research/datasets`), which is the check the
dev's own tests approximate with `store.record` fixtures.

The choke-point discipline holds under grep and under test. All eight `exclude_withheld` consumers
plus `routes.py` and `micro_readiness` route through the one predicate; no module outside them
enumerates `DatasetStore`; `vault.py` remains store-agnostic (its only `DatasetStore` mentions are
docstrings). The `ledger_tracked_ids` guard (`vault.py:873`) is correct and cannot be abused: the
only way to acquire a ledger row is the one-way, audited `seal_shard → assign_shard → expose_shard`
path, an unrecognized `exposure_state` still withholds (fail-closed), and the
`created_utc >= registered_at` guard genuinely protects the 12 permanently-exploratory legacy
symbol-days (TC-4 asserts it at both the readiness and the predicate boundary).

The recorder-progress rewrite is the right shape: an explicit whitelist projection
(`_progress_view`) rather than a spread, applied to **both** the GET and the POST echo, with the
internal `outcomes` list retained only for the terminal-run-log fallback and never reachable from a
response. TC-7 proves no bypass exists two ways (empty OpenAPI `parameters`, plus a live probe of
plausible query/header overrides). I found no leak through the `error` field either: the realistic
raise sites carry no symbol (dataset paths are hex ids, checkpoint paths are sha256 keys,
`record_from_source`'s messages name no symbol).

The four new `micro_readiness` tests are the best in the diff — exact assertions, and TC-10's
`load_events` spy proves the load-order guard *directly* with a legitimately-exposed fourth member
so it cannot pass vacuously.

Where the domain reasoning stops short is uniform: **this iteration widened one side of several
paired mechanisms and left the twin narrow.** B1 (withhold widened, reveal gate not), B3 (a new
vault predicate added without the fail-closed rule that now governs vault predicates), B2 (a field
mandated as an aggregate that stops being one at n=1). None defeats the phase goal; all three sit
on the same fault line and belong in one focused follow-up round.

---

## 4. Fixes Applied During This Audit

**None.** No production or test file was modified by this audit — the working tree is byte-identical
to the state I received (`git status --porcelain` unchanged; the temporary probe file
`apps/backend/tests/test_zz_audit_probe.py` was created, run, and deleted).

Every finding above is either (a) an owner-level ruling I must not improvise (B1, B2, B3 — T-1,
the discipline iteration 10 was ESCALATEd for breaching), or (b) below the fix threshold (B4-B6,
T1-T4). Per the DoD's own clause, all are carried forward **by name** here rather than silently
dropped.

**Independent verification performed (all re-run, never accepted from a handoff):**

| Claim | Method | Result |
|---|---|---|
| Full suite | `.venv/bin/python -m pytest tests/ -q -p no:randomly`, own run, exit 0 | **3192 collected / 3184 passed / 8 skipped / 0 failed / 0 errors** — exact match to dev + reviewer; baseline 3185/3177/8 ⇒ +7 tests, 0 regressions |
| Config fingerprint | `Config().config_fingerprint()` | `08e471b10130e1e2` — unchanged |
| Six `referee_*.py` | `sha256sum` on each | all six byte-identical to the dev handoff's recorded hashes |
| MCP surface | `tests/test_mcp_server.py:60` | 22-tuple, unchanged |
| Frontend / config / MCP code | `git diff --stat HEAD -- '*.tsx' '*.ts' app/config.py app/mcp/` | empty |
| Real-store inertness | no `micro_vault` dir under `.data`; `.data/datasets` newest mtime 2026-07-16; store-scope guard CLEAN over 11,275 files | verified three independent ways |
| Predicate fires for a REAL recording | probe: `run_tick_recording` under a registered universe → `withheld_dataset_ids_for_store` ⊇ recorded ids; `/research/datasets` serves none of them | PASS |
| No route leaks an unresolved member's identity | probe: all 78 registered GET paths swept for symbol + window-start substrings | PASS (zero leaks) |
| Parameterized surfaces refuse | probe: `GET /research/datasets/{id}` and `POST /research/backtests` aimed at an untracked pool member | both 403, refusal body carries no symbol/date |
| Single-flight/POST echo | code read: both `trigger()` paths project through `_copy_recorder_snapshot` | aggregate-only on both |
| Choke-point completeness | repo-wide grep for `DatasetStore.list()` and for `vault.withheld_*` callers | zero enumerators and zero direct callers outside the choke point |
| Beyond-plan `routes.py` edit | probe 1 with/without reasoning + reviewer's grep | justified, load-bearing, no second predicate |
| Rule-reveal gate | probe: expose the only tracked shard, leave one untracked pool member | `rule_disclosure` flips to `revealed` ⇒ finding B1 |
| Single-symbol-day event counts | probe: 1-symbol-day run under a registered universe | `trades_total/quotes_total` == the withheld shard's exact `event_counts` ⇒ finding B2 |

---

## 5. Recommended Next Step

**Proceed.** The phase goal is achieved and the diff is materially safer than what it replaced —
this is the first iteration in which a real recorder run under a registered universe is opaque by
construction rather than by bookkeeping that nothing performs.

Before J-06 step 4 (the credentialed starter tranche) is ever attempted against real tape, one
focused hardening round should close the fault line all three IMPORTANT findings sit on, in this
order:

1. **Ask the owner B1's question** — should a universe's `symbol_rule`/`date_rule` stay committed
   while *any* pool member is unresolved (closing the two-GET subtraction channel at the cost of a
   permanently-withheld §7.2 audit trail while the exploratory-release mechanism is unbuilt), or
   does the "public by construction" threat model make the reveal harmless? The mechanical change
   is ~15 lines and does not break the existing iter-9 reveal test.
2. **Ask the owner B2's question** — suppress or coarsen recorder-progress event totals below an
   N-symbol-day run scope, or accept an unattributed exact count pre-exposure?
3. **Implement r6 §7.8 / TR-25** (B3) — `verify_chain()` first in every vault predicate, typed
   refusal, and the evidence-backed recovery protocol. This is now the largest single fail-open
   surface, and the phase spec's claim that it is "still an open owner question" is stale; the
   ruling already exists.
4. **Cheap and unambiguous, no ruling needed** — normalize symbol/date at the universe-registration
   and recorder-request boundaries (B4); widen TC-8's forbidden substrings to symbol + session date
   to match the r3 trap (T1); restore `state/golden-gaps` and run J-07 (T2).

Nothing above blocks the next iteration; all of it blocks real credentialed recording.
