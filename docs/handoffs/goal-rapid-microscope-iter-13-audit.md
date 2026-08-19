# goal-rapid-microscope-iter-13 Audit Report

**Date:** 2026-08-19
**Auditor:** Hard audit pass — skeptical, evidence-based
**Judged against:** `docs/rapid-validation-spec.md` **r8** (owner ruling of 2026-08-19) and
`runs/goal-session-rapid-microscope/state/assumptions.md`'s `2026-08-19 — OWNER RULING` entry —
NOT the iteration-13 phase spec, which still describes the graded/union-marking resume branch r8
deletes. Where they conflict, r8 wins.

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's must-close item is genuinely closed, and closed harder than its own phase spec
asked: `recover_shard_ledger` is halt-only, and I could not find any input shape that makes a
genuinely-lost sealed shard reachable, sealable, or invisible again *through the halt side of the
door* — I re-ran the review's `d-fake` attack and five further shapes of my own directly against the
patched module and every one refused. But the dev's own self-attack pass on the *proven-complete*
side found two laundering paths and stopped one short: **a third exists, I reproduced it end to end,
and it produced exactly the r8-forbidden outcome — a genuinely sealed shard deleted from the ledger,
`verify_chain()` reporting clean, the shard re-sealable fresh under another universe, and a
permanent `recovery_completed` attestation certifying the loss.** It is fixed in this audit (B1),
regression-tested, and the full suite is green at 3228/3220/8/0. The remaining residuals are
r8-sanctioned deferrals plus documentation-honesty gaps, none of which compromise the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): a "proven-complete" recovery DELETES genuinely sealed rows whenever the
tail anchor lags the ledger file — the shard then reads as never-sealed and is re-sealable**

`apps/backend/app/research/vault.py:1605-1610` (pre-fix `proven_complete`). The proof tested the
candidate against the ANCHOR only — non-empty, `row_count` equal, `head_hash` equal, chain
internally consistent — and then `rewrite_from_recovery(candidate_rows)` (`vault.py:1616`) makes the
candidate the ledger's *entire new content*. `micro_chain_ledger.append_row:156-157` writes the row
FIRST and the anchor SECOND, and its own comment calls the window "a crash between the two leaves
the ledger LONGER than the anchor -- benign -- never falsely short." In that state a byte-GENUINE
reconstruction of the anchor-length history satisfies all four conjuncts, and the surplus rows —
real, sealed shards — are truncated away and certified.

Reproduced end to end against the patched module (script now removed; every line below is copied
from its output):

```
1. four shards genuinely sealed; anchor lags by one row (append_row's documented window)
   verify_chain     : {'ok': True, 'failed_at_row': None, 'reason': None}
   currently sealed : ['d-1', 'd-2', 'd-3', 'd-4']
2. an interior row is corrupted -> recovery required: {'ok': False, 'failed_at_row': 0,
                                                       'reason': 'content_hash_mismatch'}
3. recovery outcome : {'ok': True, 'resumed': True}  recorded as: ['recovery_completed']
   verify_chain     : {'ok': True, 'failed_at_row': None, 'reason': None}
   currently sealed : ['d-1', 'd-2', 'd-3']
   d-4 rows on disk : ['d-1', 'd-2', 'd-3']
4. RE-SEAL OF d-4 SUCCEEDED -- a genuinely sealed shard is fresh again
```

The operator here is entirely honest — every row they supplied is byte-genuine. No attacker
capability is required: a power loss or process kill inside `append_row` produces the precondition,
and the codebase already labels that state benign. This is verbatim r8 §7.8's forbidden outcome
("no affected shard becomes fresh, sealable, assignable, or `historical_oos` merely because the
reconstructed ledger now verifies internally"), reached through the PROVEN side of the door rather
than the graded one the owner deleted — i.e. the same failure class the iteration-12 evaluator and
the iteration-13 reviewer each found in a different branch, surviving into this pass.

Scored CRITICAL rather than IMPORTANT for consistency with the reviewer's own severity for the
identical class this iteration, and because it destroys data (a genuine ledger row) under a
permanent attestation. Honest mitigation, stated so the record is not overdrawn: `recover_shard_ledger`
has **zero production call sites** (grep across `apps/backend/app/` returns only comments in
`main.py:241` and `micro_chain_ledger.py:96`), no route, CLI or MCP tool reaches it, zero shards are
sealed and no `.data/micro_vault` directory exists — so this was never triggerable in the shipped
product today.

**Fix applied.** A fifth conjunct, `len(candidate_rows) >= preserved_row_count`
(`vault.py:1605-1631`), plus `preserved_row_count = len(shard_ledger.all_rows())` and one forensic
field of the same name on the halted incident row. It is a pure additional REFUSAL — it can only
turn a proof into a halt, never the reverse — so it does not resurrect count equality as evidence of
anything (r8's own lesson holds: it is a floor against destroying preserved evidence, never an
authorization). When it fires the vault stays BLOCKED, which is r8's explicit trade. Verification in
§4.

**B2 — GAP (disclosed residual, r8-deferred): deleting the ledger file AND its anchor together
leaves `verify_chain()` reporting `ok: True` over an empty ledger**

`micro_chain_ledger.py:186-189` — `_verify_tail` treats "no anchor and no rows" as trivially clean,
which is correct for a pristine ledger and indistinguishable from a deleted one. Executed: seal
`d-1`/`d-2`, `rm` both files ⇒ `verify_chain() == {'ok': True, ...}`, `currently_sealed_dataset_ids`
returns the empty set, and re-sealing `d-1` succeeds. Deleting the anchor *alone* correctly fails
closed (`head_anchor_missing`, verified), so the hole is specifically the both-files case.

This is the class the dev discloses as "an attacker able to rewrite the anchor sidecar can still
make a tampered ledger verify — e.g. replace both the file and its anchor with a self-consistent
forgery," and r8 explicitly defers its closure ("that migration is not designed ad hoc inside a
fix"). §7.8's own trap wording concedes the dependency: the last-known-good-prefix case fails closed
only "when a later committed checkpoint proves history should exist," and no such external
checkpoint exists yet. Left unfixed deliberately — fixing it here would be the identity-commitment
migration r8 defers. **The disclosure is honest but understated**: two `rm`s require no forgery
skill at all, which the phrase "self-consistent forgery" does not convey. Worth wording precisely in
the next revision's residuals.

**B3 — OBSERVATION: the canonical spec's TR-25 row still cites the state r8 deleted**

`docs/rapid-validation-spec.md:901` still reads "an unverifiable recovery never makes an affected
shard fresh again (`exposure_unknown`, permanently sealed-OOS-ineligible)". r8 deleted
`exposure_unknown`; TR-29 (line 902) now carries the live assertion. Not mine to edit — the spec is
the owner's document and the r8 revision is an owner ruling. Flagged for the owner's next pass.
Confirmed there is no *code* dangling reference: `vault.__all__` is 45 entries with zero dangling,
`hasattr(vault, "STATE_EXPOSURE_UNKNOWN")` is `False`, and a repo-wide grep finds the string only in
point-in-time records (phase specs, handoffs, reports, review packets) — never in `app/`, tests, or
the frontend.

**B4 — OBSERVATION: "zero on-disk format change anywhere" is imprecise**

`status.json`'s note and the handoff's Fix Notes item 4 claim no on-disk format change. The
load-bearing part is true and I verified it: `micro_chain_ledger.py` is byte-untouched
(`git diff --stat HEAD` empty), so the shard-ledger row format and the tail-anchor sidecar are
genuinely unchanged, and no identity-commitment migration was designed — the ruling's stop sign is
respected. But the RECOVERY ledger's halted-row schema did change (`recovery_incomplete` →
`recovery_halted`, `exposure_unknown_dataset_ids` dropped, four forensic fields added, plus my
`preserved_row_count`). Inconsequential — zero rows exist in any store, no Data Contract row, no
serving endpoint — but the blanket claim overstates.

### Frontend Findings

**F1 — none.** `git status --porcelain apps/frontend/` is empty (verified fresh). The QA lane's 9
regression cases and the 5/5 golden replay of J-01…J-05 all pass, and J-10's 13-step golden was
re-driven live. Nothing in this diff changes a served field, shape or endpoint;
`_serialize_shard`'s change is strictly *more* conservative (see T-adjacent note in §3).

### Test Findings

**T1 — OBSERVATION: 5 of the 6 TR-29 traps assert the count equality, not 6**

The handoff claims "**Every** TR-29 case asserts the count equality explicitly
(`attempted_row_count == anchor_row_count`), so none of these refusals can be passing for the
trivial reason of a short suffix." Five do
(`test_vault.py:2059, 2108, 2146, 2204, 2256`). The sixth,
`test_tr29_operator_attestation_alone_never_certifies_missing_identity_evidence`
(`test_vault.py:2262-2301`), asserts outcomes, operator identities and sources but **not** the
count. I verified by execution that its input does satisfy the equality by construction (identical
shape to trap 1: 2-row verified prefix + 1 fabricated row against a 3-row anchor ⇒ attempted 3 ==
anchor 3), so the trap is not passing vacuously *today* — but a future edit that shortened its
fabricated suffix would make it pass for exactly the trivial reason the claim disclaims. Left
unfixed (observation-level; fixing it is scope creep) and recorded in the handoff addendum.

Otherwise test quality is high and I could not find a trap passing by accident: assertions are exact
(`outcome == {"ok": False, "resumed": False}`, exact dataset-id lists, byte-untouched file checks via
`shard_ledger.verify_chain() == verify_result`), three TR-29 cases carry an explicit **non-vacuity**
half that runs the TRUE reconstruction against the same untouched file and proves it completes, and
`test_r8_a_prefix_the_file_no_longer_authenticates...` asserts that both original conjuncts still
matched so the refusal is demonstrably the new one. Function-name diff against HEAD: 59 → 74, two
removals (the two disclosed renames), 17 additions (16 dev + 1 mine) — **no test deleted, no
assertion weakened**, and no frozen-guard file touched (`test_mcp_server.py`, `test_meta_routes.py`,
`test_desk_ui_guards.py`, `test_copy_discipline.py`, `test_no_execution_path.py`, referee guards,
golden traces all absent from `git status`).

**T2 — GAP: `state/golden-gaps` was deleted again during this iteration; J-07's missing golden is
once more silently absent**

`runs/goal-session-rapid-microscope/state/golden-gaps` (content `J-07` / `J-08`) is deleted in this
working tree. It is not the dev's doing and is absent from `status.json`'s `changed_files`: the
framework's own `scripts/automation/lib/replay-lane.sh:522-537` rebuilds the file from *this
iteration's PASSing journeys that lack a golden*, and since only J-01…J-05 ran (all of which have
goldens), it `rm -f`'d the file. J-07 still has no `journey-scripts/J-07.json` (verified: the
directory holds J-01…J-06 and J-10 only), so the on-disk disclosure of that gap is gone. This is the
**third** occurrence in this project (playbook iter-10 audit, rapid-microscope iter-11 audit, now),
and iteration 12 explicitly restored it. Not fixed by hand: under the file's own defined semantics
J-07 did not PASS this iteration, so re-adding the line would itself be inaccurate, and the lane
would re-derive it away next run. Recorded here so the next decomposer/evaluator does not read the
absence as coverage.

**T3 — OBSERVATION: the trap-suite count must now be reported as 24 of 29, not 23 of 28**

The iteration's DoD says "the trap-suite count is reconfirmed at 23 of 28 (unchanged count)". That
line predates r8. `docs/rapid-validation-spec.md` §9 now carries 29 TR rows (counted), TR-29 is
implemented and green, and `docs/goal.md` was updated to "TR-1…TR-29". The honest inventory is
therefore **24 of 29** (still missing: TR-3, TR-22, TR-23, TR-24, TR-26).
`runs/goal-session-rapid-microscope/state/iteration-state.md:7` still carries the pre-r8 "23/28",
written before this iteration's fix pass — for the evaluator to update, not a defect of the diff.

---

## 3. Domain Assessment

**The core mechanism is sound, and I verified it rather than reasoning about it.** The proof that
authorizes a resume is now: non-empty candidate ∧ count == anchor ∧ final row hash == anchor head
hash ∧ whole chain re-derived from its own contents byte-identically ∧ (my addition) accounts for at
least as many rows as the preserved corrupt file. Because each `row_hash` commits to its own content
*and* the previous row's hash, matching the anchor's `head_hash` under a re-derived chain pins the
entire history — the count conjunct is redundant to it, which is exactly why r8 is right that count
equality can never be the dividing line and why the halt-only shape is the correct call on this
ledger. Attacks executed directly against the patched module, all REFUSED: the review's `d-fake`
same-length suffix (and `d-3` stays un-re-sealable); a `verify_result` understating the damage over
an in-place-edited interior row; a `verify_result` **over**stating `failed_at_row` so the whole
tampered file becomes the trusted prefix (a shape I did not find in the dev's or reviewer's list); a
suffix row smuggling `row_hash`/`prev_hash`/`row_index` back in as content; deleting the anchor alone.

**The halt path is genuinely fail-closed at the choke point, not route-by-route.** Every predicate
and every lifecycle transition reaches the ledger through `_latest_rows_by_dataset_id` →
`verified_rows()` → `verify_chain()` (`vault.py:894-903`), and the only `all_rows()` callers inside
the module are the recovery tooling itself. Outside `vault.py`, every consumer
(`micro_snapshots.py`, `micro_readiness.py`, `walkforward.py`, `micro_graduation.py`, `routes.py`,
`micro_routes.py`) goes through the gated public predicates — I checked each call site, not the
handoff's summary.

**The `_serialize_shard` whitelist genuinely fails closed.** I served five state values through
`build_vault_state` — `"exposure_unknown"`, `"EXPOSED"`, `" exposed"`, `"sealed"`, `"totally_new"` —
and every one returned exactly the six opaque keys with no `symbol`, `session_date`, `dataset_id`,
`content_checksum` or `family_root_id`. Case-variant and whitespace-variant near-misses of the real
states are covered by the same whitelist, which the previous blacklist form would have leaked.
`_whole_pool_released_universe_ids` also treats any non-`exposed` state as withholding, so an
unrecognised state keeps a universe's rule hidden rather than releasing it.

**Scope discipline holds.** The identity-commitment migration r8 defers was NOT attempted:
`micro_chain_ledger.py` is byte-untouched, so the anchor's on-disk shape is unchanged. Zero new
`Config` fields (`config.py` diff empty; fingerprint `08e471b10130e1e2` printed fresh from a live
import). Six `referee_*.py` byte-untouched. MCP `EXPECTED_TOOLS` parsed from the literal: 22. Zero
frontend files. Real `.data/datasets`: 18 files, no `micro_vault` directory. No invented rule (T-1):
every behavior in the diff traces to r8's own bullets or to `_rehash_suffix`'s pre-existing
"internally consistent" step, and the one place the dev overrode the phase spec's prose (the
`micro_routes.py` docstring's bucketing condition) was resolved against the verified code, disclosed,
and is strictly more conservative than r7 §7.1's ceiling.

**What the vault can honestly claim after this iteration**: an unproven reconstruction can never
resume service, and no shard becomes fresh through the recovery primitive — including, after B1's
fix, through a recovery that would have *deleted* it. What it still cannot claim: that an actor with
write access to the vault directory (or a filesystem that loses both files) cannot make history
disappear. That bound is real, is r8's explicit deferral, and should stay on the record until the
identity commitment lands.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/backend/app/research/vault.py` | `recover_shard_ledger`: added `preserved_row_count = len(shard_ledger.all_rows())` and a fifth proof conjunct `len(candidate_rows) >= preserved_row_count` — a recovery may never DELETE rows the preserved corrupt file still carries. Added `preserved_row_count` to the `recovery_halted` forensic row; updated the docstring's "FOUR conjuncts" to five and its guard count to three. |
| 2 | Critical | `apps/backend/tests/test_vault.py` | Added `test_audit_a_recovery_can_never_delete_rows_the_corrupt_file_itself_still_carries` — the anchor-lag reproduction, asserting the refusal AND (non-vacuity) that every other conjunct was satisfied: `attempted_row_count == anchor_row_count == 3`, `attempted_final_row_hash == anchor_head_hash`, `attempted_chain_internally_consistent is True`, `preserved_row_count == 4`; plus d-4's row still on disk, `build_vault_state` still raising, and `seal_shard("d-4")` refused. |
| 3 | — | `docs/handoffs/goal-rapid-microscope-iter-13-dev.md` | Appended an "Audit addendum" correcting the six handoff claims this fix invalidated or overstated (conjunct count, "resumes exactly as before", new forensic field, suite counts, the TR-29 5-of-6 assertion claim, the on-disk-format claim). |

**Post-fix verification (commands and results, not restatements):**

1. `cd apps/backend && .venv/bin/python -m pytest tests/test_vault.py tests/test_tick_recorder.py -q --junitxml=…` →
   `{'tests': '118', 'failures': '0', 'errors': '0', 'skipped': '0'}`, exit 0.
2. Full suite, **pre-fix**, run independently by me to verify the dev's own figure before changing
   anything: `pytest tests/ -q --junitxml=…` → `tests=3227, failures=0, errors=0, skipped=8`,
   587.5s, `REAL_EXIT_CODE=0`. The handoff's 3227/3219/8/0 is confirmed.
3. Full suite, **post-fix**: `tests=3228, failures=0, errors=0, skipped=8`, 587.2s,
   `REAL_EXIT_CODE=0` ⇒ **3228 collected / 3220 passed / 8 skipped / 0 failed**. Exactly +1
   collected and +1 passed — the single regression test — **zero regressions**.
4. The B1 reproduction script re-run against the patched module: outcome flips from
   `{'ok': True, 'resumed': True}` / `recovery_completed` to `{'ok': False, 'resumed': False}` /
   `recovery_halted`; `verify_chain()` still reports the identical `content_hash_mismatch`; every
   predicate raises `VaultLedgerCorruptionError`; d-4's row is still on disk.
5. Self-review of my own diff (`git diff` on both files): one local variable, one conjunct, one
   forensic field, one docstring sentence, one comment block, one test. No new import, no config
   field, no format change, nothing outside `recover_shard_ledger`'s proof. Both probe scripts I
   dropped into `apps/backend/` during the attack were deleted — `git status --porcelain
   apps/backend/` shows only the four intended files.
6. Frozen rails re-confirmed after my change: fingerprint `08e471b10130e1e2` (live import),
   `config.py` / `referee_*.py` / `micro_chain_ledger.py` diffs empty, `EXPECTED_TOOLS` = 22,
   `apps/frontend/` clean, `.data/datasets` = 18 files with no `micro_vault` directory.

---

## 5. Recommended Next Step

**Proceed.** The iteration's goal is achieved and the vault is materially stronger than it was when
this audit started. Carry these into the next iteration's inputs rather than treating them as
blockers:

1. **B2 is the honest ceiling on "the vault is safe" and should be restated more bluntly** in the
   next residuals list: deleting the ledger and its anchor together — no forgery, two `rm`s —
   silently erases every sealed shard, because nothing external commits to the ledger's existence.
   It is the single strongest argument for scheduling r8's deferred identity commitment (an ordered
   row/event identity or a canonical checkpoint/manifest tied to the chain) *before* any real sealed
   tape is recorded, i.e. before J-06 step 4. Recovery availability under B1's fix is also now
   narrower still (an anchor-lag crash window can strand a tranche outright) — a second argument for
   the same migration.
2. **Report the trap inventory as 24 of 29** (T3) and update `iteration-state.md` accordingly.
3. **Note in the journey history that J-07 has no golden replay script** (T2), since the on-disk
   `state/golden-gaps` disclosure has been auto-deleted again.
4. **J-08 remains the next build target**, unchanged — nothing in this audit moves that sequencing,
   and J-06 steps 4-5 stayed untouched by design, as the phase spec required.
