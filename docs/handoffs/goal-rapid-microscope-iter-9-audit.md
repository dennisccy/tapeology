# goal-rapid-microscope-iter-9 Audit Report (THIRD pass — re-audit of the r4 fix round)

**Date:** 2026-08-18
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

OWNER RULING #2 (spec r4) is genuinely implemented: `micro_snapshots.exclude_withheld` is one real
shared predicate used at every corpus-wide enumerator's single `DatasetStore.list()` choke point,
the disclosure reaches report bodies and append-only rows, and the compute-first TR-2 trap really
does run the operator acts before sweeping — I re-verified all of it in the code, not from the
handoff. The previous CRITICAL (B2) is closed, and every DEFINITION OF DONE item is met.

**But the trap is still vacuous on one axis, and three CRITICALs were hiding behind it — one now
fixed, two carried.** No TR-2
sweep registers a universe, so the surfaces that publish a sealed tranche's **complement** were
never exercised. (B1, fixed) `GET /research/desk/micro/vault` served each universe's full
`symbol_rule`/`date_rule`, and subtracting `GET /research/datasets` — which omits exactly the
withheld rows — yields the sealed symbol-days exactly; reproduced, fixed, and pinned with a trap
whose bite I verified. Then I attacked my own fix and found worse: **(B2, carried)** the attacker
never needed the rule. Because a universe is a symbol list × a date list and TR-4 forces the batch
to be its complete output, closing the *public dataset listing* under cartesian product and
subtracting recovers the sealed set on its own — **5 of 5, exactly, in a realistic 4 × 5 probe
sealed by the real §7.3 HMAC rule, with my B1 fix in place.** So §7.3's headline guarantee
("sealed membership cannot be inferred from public information before exposure") is **not achieved
by the system as it stands**, and nothing inside `vault.py` can achieve it. A third complement
surface (the recorder's live progress) is B3.

*I weighed FAIL and chose against it, so the reasoning is on the record rather than implied.* This
iteration's declared goal is step 3 **alone, on fixtures**, with step 4 explicitly OUT OF SCOPE; the
module it asked for is built correctly and I verified it directly. B2 is not a defect in this diff —
`GET /research/datasets` long predates it — and every carried item is unreachable while `seal_shard`
has no production caller, which the suite pins as a checked assertion rather than a claim. So the
iteration passes. **What must not happen is J-06 step 4.** B2 in particular needs an owner ruling of
the same family as the last two, and it is the one that decides whether this vault is a vault at
all. Read §5 before scheduling anything.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): the universe rule de-anonymises the whole sealed tranche by set subtraction**

`apps/backend/app/research/vault.py` — `build_vault_state` (now line 812) — served every universe
row through `_row_content`, i.e. the complete `symbol_rule` and `date_rule` lists, on the public
`GET /research/desk/micro/vault`. Three facts turn that into a total break of the vault:

1. `expected_recording_pairs` (`vault.py:427`) defines the universe's expected set as the cartesian
   product `symbol_rule × date_rule`, and TR-4 (`verify_recording_batch`, `vault.py:433`) *refuses*
   any batch that is not exactly that set net of disclosed failures — so after step 4 every
   symbol-day in the rule has a dataset.
2. `GET /research/datasets` (`routes.py:425-431`) serves each surviving dataset's `symbol` and
   `window_start_utc`, and omits precisely the withheld ones.
3. Therefore `sealed = (symbol_rule × date_rule) − served` — computable by anyone, from two public
   GETs, with no secret and no vault internals.

This defeats §7.3's stated guarantee ("sealed membership **cannot be inferred from public
information** before exposure") and §7.5's core purpose ("Symbol and date range are NOT served
pre-exposure — they would let bar-level public outcomes … be looked up against sealed membership").
It is the same *class* the owner ruled on twice (join resistance), reached by a path neither ruling
covered: not a per-shard join, but the tranche's complement.

**Why no trap caught it:** none of the four TR-2 sweeps
(`tests/test_vault.py:638`, `:726`, `:962`, `:1047`) calls `register_universe`. All four run with
`universes: []`, so the symbol under test could not appear on that surface no matter what the code
did — the *exact* "green only because the rig had nothing to leak" shape the second audit paid for.

**Reproduced before fixing** (throwaway rig, `ZQXAAA`/`ZQXBBB` × `2031-03-17`/`2031-03-18`, one
shard sealed):

```
GET /research/desk/micro/vault  → 'symbol_rule': ['ZQXAAA','ZQXBBB'], 'date_rule': ['2031-03-17','2031-03-18']
GET /research/datasets          → sealed_withheld = 1
DERIVED sealed symbol-days (public info only): [('ZQXBBB', '2031-03-17')]   ← exact
```

**Fix applied** — the same commit-then-reveal discipline r3 point 2 already applies to
`content_checksum`, at one serving choke point:

* `vault.py` — new `_fully_exposed_universe_ids()` and `_serialize_universe()`; `build_vault_state`
  now projects universe rows through the latter. While **any** shard of a universe is short of
  `exposed`, the row serves `rule_hash` (already computed at registration) plus
  `symbol_rule_size`/`date_rule_size` and `rule_disclosure: "committed"` — never the lists. Once
  every shard of that universe is `exposed`, the full row returns with
  `rule_disclosure: "revealed"`. A universe owning **zero** shards stays committed (fail-closed:
  §7.2's mandated order registers the universe before any fetch, so there is a real window in which
  a reader could otherwise harvest the rule and keep it for the tranche's whole life).
* No spec meaning is changed: §7.2 requires the rule to be **RECORDED in the vault ledger** before
  any fetch — unchanged — and `find_universe`/the TR-4 verifier still read it verbatim from that
  ledger, so batch verification and post-hoc auditability are untouched. This was a bug against an
  invariant §7.3 already states, not a policy choice, which is why I closed it rather than
  escalating (the rubric's §3 "two legitimate readings conflict" test does not fire — §7.2 never
  said *served*).
* `micro_routes.py`'s `/vault` docstring corrected; `vault.py`'s module docstring gained
  join-resistance part 4 and the old, wrong justification ("knowing that a tranche covers S symbols
  × D dates says nothing about WHICH …") is now marked wrong with the reason.

**B2 — CRITICAL (carried, HARD GATE on J-06 step 4; owner ruling required): the public dataset
listing alone still de-anonymises the sealed tranche, by cartesian closure**

**I found this by attacking my own B1 fix, and it is the more important of the two.** Removing the
published rule takes away one oracle, not the attack. The tranche's *shape* is public by design
(§7.2: a resolved symbol list × a resolved date list; TR-4 forces the batch to be its complete
output), so an attacker does not need the rule — they can reconstruct it from
`GET /research/datasets` itself: take the served (symbol, session_date) pairs, close them under
cartesian product, and subtract. Whatever is missing is sealed.

Probed on a realistic 4 × 5 grid, sealing by the **real §7.3 HMAC rule** rather than a hand-picked
member, with the B1 fix in place:

```
truly sealed (5): [(ZQXAAA,03-20), (ZQXBBB,03-17), (ZQXBBB,03-19), (ZQXDDD,03-18), (ZQXDDD,03-21)]
attack input:     GET /research/datasets ONLY  (the vault row now carries no rule)
derived sealed:   [(ZQXAAA,03-20), (ZQXBBB,03-17), (ZQXBBB,03-19), (ZQXDDD,03-18), (ZQXDDD,03-21)]
EXACT MATCH: True                                                                   ← 5 of 5
```

It works whenever no symbol and no date is *entirely* sealed — which, at ~25% sealing
(`VAULT_SEAL_HEX_BELOW = 4`) over §7.6's ≥8 symbols × ≥10 dates, is effectively always.

**So §7.3's headline guarantee — "sealed membership cannot be inferred from public information
before exposure" — is NOT achieved by the system as it stands**, and no change inside `vault.py`
can achieve it: the leak is a property of a pre-existing published route (`GET /research/datasets`
serves every non-withheld dataset's `symbol` and `window_start_utc`) meeting a cartesian universe.
Closing it means deciding something an agent must not decide alone — e.g. withholding symbol/date
for *every* dataset of a universe until the whole tranche is exposed, or seeding the universe with
decoy symbol-days, or accepting the residual with a written caveat and relying on the read refusals
alone. Each changes what the vault promises. **This is the third ruling of the same family and it
should be taken before any real tape is sealed.**

*Not introduced by this iteration* — `GET /research/datasets` long predates it — but iteration 9 is
what creates "sealed" as a concept, so this is the first moment the gap is meaningful, and it is
inert until step 4 seals something.

**B3 — CRITICAL (carried, HARD GATE on J-06 step 4): the recorder's live progress serves every
sealed shard's symbol, date and raw `dataset_id`**

Same class as B1/B2, a third instance, and the trap is blind to it for the same reason.
`GET /research/desk/micro/recorder/compute` (`micro_routes.py:475`) returns
`manager.snapshot()["progress"]` verbatim. That progress carries `outcomes`, and each outcome is
`_chunk_entry` (`tick_recorder.py:492`) = `{**chunk, "outcome", "detail", "dataset_id",
"dataset_outcome"}` where `chunk` is `{"symbol", "date", "start", "end"}`
(`plan_recorder_chunks`). So after step 4's recording run, and until the backend process restarts,
that route serves the complete recorded (symbol, date, dataset_id) list — **including the shards
sealed immediately afterwards**. That hands out the raw `dataset_id` r3 §7.5 point 1 exists to
replace with a surrogate, and hands over the recorded set outright — B2's subtraction with no
inference step at all.

Not reachable today (`seal_shard` has no production caller; nothing is sealed). Every TR-2 sweep
leaves the recorder manager idle, so `outcomes` is `[]` and the sweep cannot bite.

**Left unfixed deliberately, per the rubric's stop-and-ask test:** the redaction shape is a genuine
product choice on a surface this iteration's spec puts OUT OF SCOPE (the recorder is iteration-8
material; step 4 is deferred) — redact retroactively once withheld, clear the snapshot at seal
time, or refuse the route while any shard is withheld all differ in what an operator sees mid-run.
Recommended closure: filter the served `outcomes` through the existing
`micro_snapshots.withheld_dataset_ids_for_store` predicate at that one route, dropping
`symbol`/`date`/`start`/`end`/`dataset_id` for any outcome whose dataset is withheld, and add a
TR-2 variant that runs a recorder job before sweeping.

*Residual to weigh in the same ruling (not a separate finding — materially weaker).*
`pair_bar_backfill_for_recorded_days` (`tick_recorder.py`) backfills 1m/5m bars for every symbol
that finalized a dataset, over that symbol's own `min(dates)..max(dates)`, and `GET /research/bars`
serves each series' `symbol`, `timeframe` and `created_utc`. That narrows the recorded **symbol set
and date span** — not symbol-days, and the deep-backfill path appends to series that often already
exist from earlier eras, so it is circumstantial rather than exact. It is worth a look when B2 is
ruled, because it is one more way the tranche's shape stays inferable after the obvious surfaces
are shut.

**B4 — IMPORTANT (carried, correctly named by dev; needs the owner): the withholding predicates
fail OPEN on a corrupted ledger**

`vault._latest_rows_by_dataset_id` (`vault.py:568`) reads `HashChainedLedger.all_rows()`, which
parses but never verifies. Truncating `vault_shard_ledger.jsonl` silently un-withholds every sealed
shard, now across **eleven** consumers. I confirmed the asymmetry that makes this sharper than the
handoff states: `micro_chain_ledger.verify_chain()` **would** catch it
(`_verify_tail` → `{"ok": false, …, "reason": "tail_truncated"}`, `micro_chain_ledger.py:141-151`),
and `build_vault_state` already surfaces that verdict on `/vault` — so the alarm rings on one page
while every refusal quietly opens. Fail-closed changes availability semantics on published routes
(a corrupted vault would 5xx the dataset list, the edge report, the desk screen), which is an owner
call. **Decide before the first real shard is sealed.**

**B5 — IMPORTANT (carried; owner call, genuine r4-vs-freeze collision): `referee_evidence`
counts withheld shards**

`referee_evidence.strategy_trade_readiness` (`referee_evidence.py:333`) enumerates
`dataset_store.list()` with no seal filter and serves `dataset_count`, `per_split_counts` and
`tick_gate_met`/`tick_gate_statement` off it. Verified by direct read. The harm is not identity
(the count is already public as `sealed_withheld`) — it is that a **research gate can report its
floor met on the strength of evidence no analysis is permitted to read**. Fixing it edits one of
the six frozen-hash `referee_*.py` files, a standing DoD pin for this era. Dev's NEW-2, correctly
disclosed; take it with B4 to the same ruling before step 4.

**B6 — GAP (not fixed, reviewer also flagged it): `micro_snapshots.main()` discloses an unscoped
count**

`micro_snapshots.py:616-621` re-lists the WHOLE store to compute `withheld_excluded` after a
possibly `--dataset-id`-scoped run, so a scoped CLI run prints the store-wide count rather than what
this run excluded. Honest in the conservative direction (it can only over-state an exclusion, never
hide one) and it is a stdout line, not a report body or an append-only row, so r4's binding clause
is not breached. Fix when convenient: return the count from `run_snapshot_build_and_record`, which
already computes the filter internally.

**B7 — OBSERVATION: `peek_strategy_comparison_report` reads the corpus twice**

`edge_report.py:911` calls `_verified_corpus`, and on the empty-records branch (`:912-913`) delegates
to `_compute_strategy_comparison_report`, which calls it again (`:970`) — so the module docstring's
"the ONE `DatasetStore.list` read this module makes" is not literally true on that path. No
correctness impact (same predicate, same store; the fully-withheld branch still reports honestly via
`FULLY_WITHHELD_FINDING`).

### Frontend Findings

None. Zero `.tsx`/`.ts` files changed this iteration (confirmed against `git status`), and my own fix
touches only `GET /research/desk/micro/vault`, which has no UI consumer (the Validation Vault
section is J-08 scope and is verified ABSENT from `/desk`).

### Test Findings

**T1 — IMPORTANT (fixed): the TR-2 sweeps had a structural blind spot**

None of the four sweeps registered a universe, so the surface that publishes a tranche's complement
was untested — which is how B1 shipped green. Closed by two new tests in `tests/test_vault.py`:

* `test_audit_b1_the_universe_rule_cannot_de_anonymise_the_sealed_tranche_by_subtraction` — registers
  a universe, records its full 2×2 set, seals one member, then asserts the served universe row
  carries `rule_hash`/sizes and *no* `symbol_rule`/`date_rule`, that no symbol or date token appears
  anywhere in it, and that the sealed pair is absent from the served dataset pairs. It leads with a
  **counter-test** (1 universe registered, `sealed_withheld == 1`, 3 siblings still served) so it
  cannot pass on an idle rig — the failure mode it exists to prevent. It also proves the reveal half:
  `assigned` still withholds, `exposed` restores the full rule.
* `test_audit_b1_a_universe_with_no_shards_yet_keeps_its_rule_committed` — the fail-closed window.

**What these two do NOT cover, stated so nobody reads them as more than they are:** they close the
*universe-rule* axis only. No test in the suite performs B2's cartesian-closure attack, and none
seals by the real §7.3 HMAC rule over a full grid — deliberately, since such a test would fail
today and B2 is unruled. That case is named in §5 as part of B2's closure.

**T2 — GAP (carried): the browser and suite evidence certifying this iteration predates the r4 fix
round**

Dev flagged this itself. The QA report cites 3,130 tests (stale — the r4 round is 3,164) and its
browser screenshots are timestamped 09:34, while round 3's source edits landed at 14:14–14:34
(`edge_report.py` 14:14, `pnl_scan.py` 14:16, `desk_screen.py` 14:18, `micro_snapshots.py` 14:34 —
checked by mtime, not inferred); `reports/…-ui-test-
results.llm.md` (read directly per the spec's NOTES — it is a genuine `PASS` with 8 `PASS` rows, not
a merged headline) and `…-regression-replay-results.md` (1/1 journeys, `J-01-verify.png`) are from
the same pre-r4 window. Low risk — r4 added only optional keys, the frontend does no runtime schema
validation, and no `.tsx` changed — but it is unverified for the post-r4 state, so it is `unknown`
rather than `passing` at the browser layer. My own B1 fix cannot affect it (the only route whose
payload changed has no UI consumer).

**T3 — OBSERVATION: three duplicate `withheld_excluded` keys in test stubs**

`tests/test_desk_screen_compute.py:133/136`, `192/195`, `484/487` — the first of each pair is fully
overridden. Reviewer flagged it; harmless patch-merge residue, not fixed (cosmetic).

---

## 3. Domain Assessment

The vault's core logic is sound and I verified it directly rather than from the handoff.

* **Lifecycle.** `seal_shard` refuses if any row exists; `assign_shard` requires the latest row to be
  `sealed`; `expose_shard` requires `assigned` **and** the same `family_root_id` — so "never
  assigned", "already exposed" and "assigned to a different family" all refuse through one guard
  (`vault.py:587`/`:648`/`:678`). One-way by construction; state is decided server-side only (there is no
  client). TR-12's guard keys on identity via `_latest_shard_row`, never on row count.
* **TR-20 / no reimplementation.** `vault.compute_family_root_id is scout_ledger.compute_family_root_id`
  is asserted by object identity (`test_vault.py:52-55`), not by matching output. The split axis is
  reused from `tick_recorder.recorder_split_for`; both ledgers are thin wrappers over the existing
  `HashChainedLedger`. No fourth chain, no second identity function.
* **The r4 predicate is genuinely single.** `exclude_withheld` (`micro_snapshots.py:118`) is called
  by `edge_report`, `edge_report_cache` (both read and write halves — which is what prevents the
  permanent cache miss), `pnl_scan`, `scout`, `micro_join` (both `joinable_corpus_counts` and
  `find_covering_dataset`), `desk_screen`, `setups`, `walkforward` and `micro_snapshots` itself. I
  enumerated every `DatasetStore.list()` site in `app/research/` and found exactly two unfiltered
  enumerators: `tick_recorder.py:422` (deliberate and documented — it is the recorder's own
  idempotency check; hiding a sealed shard would make it re-fetch a day it already holds) and
  `referee_evidence.py:333` (B4). A third, `datasets.py:552`, is `DatasetStore.record`'s own
  duplicate-content scan — not a corpus enumerator, and filtering it would *weaken* immutability by
  letting a sealed shard's content be re-registered under a second id, so leaving it is right.
  `walkforward.py:1034` reads unfiltered inside `_tick_dataset_session_dates`, but both callers pass
  an explicit `excluded_dataset_ids` predicate — the deliberate two-boundary design (r2 seed =
  strictly `sealed`; corpus inventory = the wider withheld set). `micro_readiness` correctly uses the vault's own `withheld_universe_by_dataset_id` because it
  needs the universe grouping, and it `continue`s **before** `store.load_events` — so readiness can
  no longer load a sealed shard's events at all.
* **Disclosure really travels.** `withheld_excluded` reaches the edge report body (both the computed
  and the `not_computed` payloads), the PnL sweep body, `pnl_ledger.append_validation_row`'s
  `provenance` (omitted entirely for `pnl_baseline`'s founding seed, so pre-r4 rows stay
  byte-identical), the snapshot compute snapshot **and** its append-only run-log row, every scout
  ledger row (outside `spec_fields`, so nothing re-keys), the desk screen payload and recorded
  snapshot, and the walkforward body — including, thoughtfully, the
  `InsufficientSessionsForFoldsError` message, but only when something was actually withheld, so
  today's refusal text is unchanged. The decision *not* to stamp it into `register_fold_spec`'s
  idempotent row (a per-run count frozen and replayed as fact forever) is correct reasoning.
* **The secret.** `commit_vault_secret` (`sha256`) is the only form persisted; the raw secret is used
  solely as an HMAC key in `compute_seal`/`compute_surrogate_shard_id`/`commit_content_checksum`, all
  domain-separated with versioned labels, and never written, returned, logged, or served. B7's
  empty-secret refusal is in place before any row is written. No test in the repo reads the
  operator's real `TAPEOLOGY_VAULT_SECRET_FILE`. I did not read it either.
* **§2.6 manifest fields.** `_content_checksum` (`datasets.py`) hashes only
  `{symbol, data_feed, epoch_anchor, events}`; the two new fields are stamped into `meta` afterwards
  (`datasets.py:580-583`), so exclusion is structural, not merely tested.

The compute-first trap is real work, not theatre: `test_tr2_holds_after_the_corpus_wide_report_acts`
runs `run_edge_report` and `run_sweep` before sweeping, and its counter-test half (`measured ==
public_ids`, `backtested` non-empty, `GET /research/backtests` non-empty) is exactly what stops an
idle rig from passing. Its blind spot is scope, not rigor — it covers r4's four enumerated compute
acts and misses every surface that publishes a *complement* (B1, B2, B3).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/backend/app/research/vault.py` | B1: `_fully_exposed_universe_ids` + `_serialize_universe`; `build_vault_state` serves a universe's `symbol_rule`/`date_rule` only once every shard of that universe is `exposed`, else `rule_hash` + sizes + `rule_disclosure: "committed"`. Added `RULE_DISCLOSURE_COMMITTED`/`_REVEALED`; module docstring gains join-resistance part 4 and retracts the old (wrong) justification. |
| 2 | Critical | `apps/backend/tests/test_vault.py` | B1/T1 regression: `test_audit_b1_the_universe_rule_cannot_de_anonymise_the_sealed_tranche_by_subtraction` (with its own anti-vacuity counter-test and the reveal half) and `test_audit_b1_a_universe_with_no_shards_yet_keeps_its_rule_committed`. |
| 3 | Critical | `apps/backend/app/research/micro_routes.py` | Docstring only: the `/vault` route now states the universe rule's two-stage disclosure. |

**Post-fix verification (evidence, not assertion).**

* `tests/test_vault.py` — 42 passed, 0 failed
  (`.venv/bin/python -m pytest tests/test_vault.py -q -p no:randomly`).
* **Reproduction inverted:** the standalone repro that asserted the leak *exists* now fails with
  `KeyError: 'symbol_rule'` — the payload no longer contains the field the attack needs. (Scratch
  file deleted; `ls` confirms it is gone.)
* **Trap-bites check:** I neutralised `_serialize_universe`'s predicate to always reveal (the pre-fix
  behaviour) and re-ran — **both** new tests FAILED. File restored from backup and the restore
  verified (`grep -c NEUTRALISED` → `0`; the real predicate re-read at `vault.py:799`).
* **Adversarial re-test of my own fix (this is what produced B2):** a second scratch probe on a
  4 × 5 grid, sealed by `vault.compute_seal` itself rather than by hand, showed the sealed set is
  still recoverable — 5 of 5 — from `GET /research/datasets` alone. Both scratch files were deleted
  (`ls tests/test_zzz*` → no such file); neither is part of the suite.
* **Full backend suite:** see §4a below.
* **Diff discipline:** my changes touch three files and only what B1 required — one serving
  projection, its two constants, its tests, and two docstrings. No behaviour outside
  `build_vault_state`'s universe projection moved.
* **Handoff correction owed:** the dev handoff's final line ("**J-06 step 4 is unblocked by the
  ruling's own terms once TR-2 passes in its compute-first form — which it now does**") is
  **invalidated** by B1 (which was live in the code that sentence describes) and by B2/B3/B4, which
  remain open. §5 states the real gate.

### 4a. Frozen foundations — re-verified by me, after my fix

| Pin | Result |
|---|---|
| `Config().config_fingerprint()` | `08e471b10130e1e2` ✓ (zero new `Config` fields; the two new vault constants are plain module constants) |
| Six `referee_*.py` SHA-256 | byte-identical to the iteration-0 listing (`goal-rapid-microscope-iter-0-dev.md:76-81`) — compared line by line, not inferred from `git status` ✓ |
| `EXPECTED_TOOLS` (extracted by AST) | 22-tuple ending `get_endpoint` ✓ |
| Operator's real `.data/datasets` | `f7bbcf28d074d51a126e7cf5d4724ca9a8f2758a0453c6801331c88111e2c26c`, 18 files ✓ — identical to the value both prior rounds recorded; every store I touched was `tmp_path`-scoped |
| Full backend suite | **3,166 / 0 failures / 0 errors / 8 skipped** ✓ — run **twice**, independently agreeing (JUnit roots `errors="0" failures="0" skipped="8" tests="3166"`, 582.5s and 587.2s; exit code 0 both times). 3,166 = the r4 round's 3,164 plus my two new traps, so the DoD floor of 3,092 is cleared and every prior test still runs. |

**Why the suite was run twice, stated rather than glossed.** The first run's window overlapped the
mtimes of the files I had edited, and I could not prove from the timestamps alone that no edit
landed mid-run — the exact trap the dev handoff documents from its own round 2. So I pinned
`sha256sum` of all three touched files, re-ran the whole suite against those pinned bytes, and
verified the hashes afterwards: `vault.py` and `test_vault.py` **OK**, unchanged across the run.
One file did change afterwards — a docstring re-wrap in `micro_routes.py` — so rather than claim it
was harmless I re-ran the seven test files covering that route family with the final bytes:
**258 passed, 0 failed**. No claim in this report rests on a run that predates the code it
describes.

### 4b. DEFINITION OF DONE

Risk-class items (state transitions, persistence, serving of held-out evidence) were traced through
the code by me. Mechanical items already executed against the running system cite the reviewer's
`definition_of_done: complete` plus the specific QA row.

| DoD item | Status | Basis |
|---|---|---|
| `vault.py`: universe registration, split/seal, one-way `family_root_id`-keyed ledger | met | **traced** — `vault.py:366` (idempotent-or-refuse registration), `:587`/`:648`/`:678` (the three guards), object-identity test for `compute_family_root_id` |
| TR-2/4/12/20 green on fixtures | met **after B1** | **traced** — TR-4 refuses in both directions naming the gap (`vault.py:433`); TR-12/20 as above; TR-2 was defeated by B1 and now carries the new universe trap |
| `GET .../vault` serves state verbatim, opaque while sealed | met **after B1** | **traced** — `_serialize_shard`'s per-stage whitelist was already correct; the universe half was not |
| Exposure-registry sealed filter closes the latent hole | met | **traced** — `walkforward.py:1267` passes `currently_sealed_dataset_ids`; `_tick_dataset_session_dates(excluded_dataset_ids=)`; TC-10/TC-11 + T3's shared-date pin |
| §2.6 rule text + note recorded, checksum-excluded | met | **traced** — structural exclusion in `_content_checksum`; `tick_recorder.py:484-485` supplies both |
| Two test-hygiene items cleared | met | **traced** (no QA row exists) — `grep -c _StrippedTradeEventMissingConditions` → 0; docstring now names `test_cancelling_an_idle_recorder_is_a_409` in the same file (`:571`), which exists at `:754` |
| J-06 / J-10 verified via browser-qa + suite | met (with T2) | QA report "Validation Vault section is ABSENT ✅ PASS" + `…-ui-test-results.llm.md` `**Browser QA Verdict:** PASS` (8 PASS rows) + 4 screenshots on record |
| J-01–J-05 remain green | met (with T2) | QA "All regression sections present ✅ PASS" + replay `1/1 journeys passed` (`J-01-verify.png`); reviewer `definition_of_done: complete` |
| No anti-goal violation introduced | met **after B1** | B1 was a sealed-metadata-minimization violation introduced by this iteration's own new endpoint; fixed. Reuse-not-reimplementation verified directly. |
| Suite ≥ 3,092 / 0 failures + frozen pins | met | §4a, re-run by me after every edit |
| Independent auditor runs; findings fixed or carried by name | met | this report; B2/B3/B4/B5/B6/T2/T3 carried by name, plus the pre-existing `disclosed_failures`, O1 and `register_fold_spec` items |
| Dev handoff written | met | `docs/handoffs/goal-rapid-microscope-iter-9-dev.md`, amended by this audit (its "step 4 is unblocked" line retracted in place, not silently left standing) |

---

## 5. Recommended Next Step

**Do not proceed to J-06 step 4.** The dev handoff declares it unblocked; it is not. Four things
must be ruled on or closed first, and every one of them is inert *only* because `seal_shard` still
has no production caller — step 4 is precisely the act that makes them live.

1. **B2 (CRITICAL) — owner ruling, and take it first.** Decide what §7.3's "sealed membership cannot
   be inferred from public information" actually promises, now that it is demonstrably false as
   built. The cartesian closure of `GET /research/datasets` recovers the sealed set exactly (5/5 in
   my probe) with no vault involvement at all. The options are genuinely different products, which
   is why an agent must not pick one:
   * **(a) Withhold the whole tranche's symbol/date** — every dataset of a universe stays opaque on
     `/research/datasets` until the tranche is fully exposed. Strongest; costs the most (a large
     slice of the public listing disappears for the tranche's whole life, and readiness/desk
     surfaces thin out with it).
   * **(b) Break the cartesian shape** — record decoy/extra symbol-days so "missing" no longer means
     "sealed". Preserves the public listing; adds real fetch cost and a new honesty question about
     what the decoys are.
   * **(c) Accept the residual, in writing** — rely on the read/compute refusals (which genuinely
     hold: no sealed shard's events or aggregates can be read anywhere) and state plainly that
     sealed *membership* is inferable. Cheapest; materially weakens what the vault claims, and the
     era's own goal text would need amending rather than quietly outliving the gap.
   Whatever is chosen becomes a named spec revision, and TR-2 needs a case that seals by the real
   §7.3 rule over a full grid and then runs the closure attack — the shape of my probe.
2. **B3 (CRITICAL) — close it.** `GET /research/desk/micro/recorder/compute` must stop serving a
   withheld shard's `symbol`/`date`/`dataset_id`. A one-route filter through the existing
   `withheld_dataset_ids_for_store` predicate, plus a TR-2 variant that runs a recorder job before
   sweeping. Cheap and unambiguous once B2's direction is set.
3. **B4 (IMPORTANT) — owner ruling.** Fail-open vs fail-closed withholding on a corrupted vault
   ledger, across eleven consumers. Note that `verify_chain()` already detects the truncation and
   `/vault` already surfaces it — only the predicates ignore it, so a fail-closed variant is cheap
   once the availability question is answered.
4. **B5 (IMPORTANT) — owner ruling, same sitting.** r4 vs the frozen `referee_*.py` hash pin. Until
   ruled, `tick_gate_met` can report a floor met on evidence no analysis may read, the moment a
   shard is sealed.

**One thing that is genuinely solid, and worth saying so plainly:** the *read* side of the vault
holds. No sealed shard's events, snapshots, backtests, screens, drill-ins, scout trials or ledger
rows can be produced anywhere — I traced every `DatasetStore.list()` site to confirm it, and the
r4 disclosure is honest throughout. The gap is entirely about **membership inference**, not about
anyone being able to look at held-out tape.

Also worth ruling with them: O1 (shard-global vs pair-scoped TR-12 — currently pinned by a test in
the stricter direction, which is the safe interim), and `disclosed_failures`, which is still bound
to nothing and must bind to `tick_recorder`'s real per-chunk `failed` outcomes when step 4 runs.

**Before the next iteration's evaluator reads this:** re-run the browser lane and re-cite the suite
against the *current* tree (T2) — the existing browser evidence and the QA report's 3,130 both
predate the r4 round. Treat the browser layer as `unknown` for the post-r4 state, not `passing`.

Two lessons worth carrying into the session's lessons file, because this is now the **third**
consecutive pass where the same shape produced a real defect:

* *A join-resistance sweep is only as good as the state its rig has created.* Twice the trap was
  blind because nothing had been computed; this time because nothing had been **registered**. Before
  trusting any "value X appears nowhere" assertion, list what the rig did **not** create, and treat
  each as an untested surface.
* *Per-record minimization does not imply set-level minimization, and removing one oracle is not
  closing the leak.* Every individual field can be opaque while the **complement** hands over the
  whole secret — and here the complement did not even need a published rule, because the set's
  SHAPE was inferable from the surviving members. After any fix of this class, attack your own fix
  before writing it up. Any surface that publishes an expected
  set beside a surface that publishes an actual set needs the commit-then-reveal treatment.
